from __future__ import annotations

import os
import threading
from queue import Queue
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import SessionContext
from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary, MaterialTransaction
from backend.app.models.master import Customer, Fixture, User, UserCustomer
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.services.inventory_service import InventoryService


MYSQL_STAGING_DATABASE_URL = os.getenv("MYSQL_STAGING_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not MYSQL_STAGING_DATABASE_URL,
    reason="MYSQL_STAGING_DATABASE_URL is required for the MySQL concurrency test",
)


def _run_concurrent_transactions(
    session_factory,
    *,
    actor: SessionContext,
    payloads: list[StockTransactionCreate],
    method_name: str,
) -> list[tuple[str, str]]:
    barrier = threading.Barrier(len(payloads))
    results: Queue[tuple[str, str]] = Queue()

    def worker(payload: StockTransactionCreate) -> None:
        db = session_factory()
        try:
            service = InventoryService(db, actor=actor)
            barrier.wait(timeout=15)
            getattr(service, method_name)(payload)
            results.put(("success", ""))
        except ValueError as exc:
            results.put(("rejected", str(exc)))
        except Exception as exc:  # pragma: no cover - surfaced with its concrete type below
            results.put(("unexpected", f"{type(exc).__name__}: {exc}"))
        finally:
            db.close()

    threads = [threading.Thread(target=worker, args=(payload,), daemon=True) for payload in payloads]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not any(thread.is_alive() for thread in threads), "concurrent inventory transaction timed out"
    return [results.get_nowait() for _ in threads]


def test_mysql_concurrent_receipts_do_not_lose_updates_and_returns_cannot_oversell() -> None:
    engine = create_engine(MYSQL_STAGING_DATABASE_URL, pool_pre_ping=True)
    if engine.dialect.name != "mysql":
        engine.dispose()
        pytest.skip("MYSQL_STAGING_DATABASE_URL must use the MySQL dialect")

    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    token = uuid4().hex[:12]
    customer_id: int | None = None
    fixture_id: int | None = None
    user_id: int | None = None
    try:
        with session_factory() as db:
            customer = Customer(code=f"RACE-{token}", name=f"Concurrency {token}")
            user = User(
                username=f"race-{token}",
                email=None,
                password_hash="staging-concurrency-test",
                display_name=f"Race {token}",
                role="user",
                is_active=True,
            )
            db.add_all([customer, user])
            db.flush()
            fixture = Fixture(
                customer_id=customer.id,
                responsible_user_id=None,
                code=f"FX-{token}",
                name="Concurrency Fixture",
                line_storage_location=None,
                department_storage_location=None,
                description=None,
                is_active=True,
            )
            db.add(fixture)
            db.flush()
            db.add_all(
                [
                    UserCustomer(user_id=user.id, customer_id=customer.id),
                    FixtureStockLevel(
                        fixture_id=fixture.id,
                        min_stock_qty=0,
                        warning_threshold=0,
                        alert_enabled=True,
                    ),
                    FixtureStockSummary(
                        fixture_id=fixture.id,
                        stock_qty=0,
                        returned_qty=0,
                        stock_status="out_of_stock",
                    ),
                ]
            )
            db.commit()
            customer_id = customer.id
            fixture_id = fixture.id
            user_id = user.id
            actor = SessionContext(
                mode="user",
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                role=user.role,
                issued_at=0,
                expires_at=9999999999,
            )

        receipt_payloads = [
            StockTransactionCreate(
                customer_id=customer_id,
                transaction_no=f"RACE-R-{token}-{index}",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "customer_supplied",
                        "identifier": "RACE-ID",
                        "quantity": 1,
                    }
                ],
            )
            for index in range(2)
        ]
        receipt_results = _run_concurrent_transactions(
            session_factory,
            actor=actor,
            payloads=receipt_payloads,
            method_name="receipt",
        )
        assert sorted(status for status, _ in receipt_results) == ["success", "success"]

        with session_factory() as db:
            summary = db.get(FixtureStockSummary, fixture_id)
            assert summary is not None
            assert summary.stock_qty == 2

        return_payloads = [
            StockTransactionCreate(
                customer_id=customer_id,
                transaction_no=f"RACE-T-{token}-{index}",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "customer_supplied",
                        "identifier": "RACE-ID",
                        "quantity": 2,
                    }
                ],
            )
            for index in range(2)
        ]
        return_results = _run_concurrent_transactions(
            session_factory,
            actor=actor,
            payloads=return_payloads,
            method_name="return_material",
        )
        assert sorted(status for status, _ in return_results) == ["rejected", "success"]
        assert not [message for status, message in return_results if status == "unexpected"]

        with session_factory() as db:
            summary = db.get(FixtureStockSummary, fixture_id)
            assert summary is not None
            assert summary.stock_qty == 0
            return_count = db.scalar(
                select(func.count())
                .select_from(MaterialTransaction)
                .where(
                    MaterialTransaction.customer_id == customer_id,
                    MaterialTransaction.transaction_type == "return",
                )
            )
            assert return_count == 1
            identifier_row = next(
                row
                for row in InventoryService(db).list_identifier_stock_summary(customer_id, fixture_id)
                if row["identifier"] == "RACE-ID"
            )
            assert identifier_row["customer_supplied_qty"] == 0
            assert identifier_row["stock_qty"] == 0
    finally:
        if customer_id is not None and fixture_id is not None and user_id is not None:
            with session_factory() as db:
                db.execute(delete(MaterialTransaction).where(MaterialTransaction.customer_id == customer_id))
                db.execute(delete(UserCustomer).where(UserCustomer.user_id == user_id))
                db.execute(delete(Fixture).where(Fixture.id == fixture_id))
                db.execute(delete(Customer).where(Customer.id == customer_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
        engine.dispose()
