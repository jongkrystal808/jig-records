from datetime import date, datetime, timezone

from collections.abc import Iterator

from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.orm import Session

from backend.app.models.inventory import (
    FixtureStockLevel,
    FixtureStockSummary,
    MaterialTransaction,
    MaterialTransactionItem,
)
from backend.app.models.master import Fixture


class InventoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _normalize_transaction_no(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _filter_values(value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(dict.fromkeys(value))

    @staticmethod
    def _serialize_transaction_item_row(row: dict) -> dict:
        return {
            "fixture_id": row["fixture_id"],
            "fixture_code": row["fixture_code"],
            "fixture_name": row["fixture_name"],
            "ownership_type": row["ownership_type"],
            "identifier": row["identifier"],
            "quantity": row["quantity"],
            "note": row["note"],
        }

    def _build_transaction_id_stmt(
        self,
        *,
        customer_id: int | None = None,
        fixture_id: int | None = None,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        ownership_type: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ):
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        stmt = (
            select(MaterialTransaction.id)
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .distinct()
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        if fixture_id is not None:
            stmt = stmt.where(MaterialTransactionItem.fixture_id == fixture_id)
        if transaction_type:
            stmt = stmt.where(MaterialTransaction.transaction_type.in_(self._filter_values(transaction_type)))
        if date_from is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at <= date_to)
        stmt = self._apply_fixture_code_filter(stmt, fixture_code_expr, fixture_code)
        if transaction_no:
            stmt = stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
        if ownership_type:
            stmt = stmt.where(MaterialTransactionItem.ownership_type.in_(self._filter_values(ownership_type)))
        stmt = self._apply_identifier_filter(
            stmt,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
        )
        if created_by:
            stmt = stmt.where(MaterialTransaction.created_by.ilike(f"%{created_by.strip()}%"))
        return stmt

    def _list_transaction_items(
        self,
        transaction_ids: list[int],
        *,
        fixture_id: int | None = None,
        ownership_type: str | None = None,
    ) -> dict[int, list[dict]]:
        if not transaction_ids:
            return {}
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        fixture_name_expr = func.coalesce(Fixture.name, MaterialTransactionItem.deleted_fixture_name)
        item_stmt = (
            select(
                MaterialTransactionItem.transaction_id,
                MaterialTransactionItem.fixture_id,
                MaterialTransactionItem.ownership_type,
                MaterialTransactionItem.identifier,
                MaterialTransactionItem.quantity,
                MaterialTransactionItem.note,
                fixture_code_expr.label("fixture_code"),
                fixture_name_expr.label("fixture_name"),
            )
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .where(MaterialTransactionItem.transaction_id.in_(transaction_ids))
            .order_by(MaterialTransactionItem.id.asc())
        )
        if fixture_id is not None:
            item_stmt = item_stmt.where(MaterialTransactionItem.fixture_id == fixture_id)
        if ownership_type:
            item_stmt = item_stmt.where(MaterialTransactionItem.ownership_type.in_(self._filter_values(ownership_type)))
        item_rows = [dict(row._mapping) for row in self.db.execute(item_stmt).all()]
        item_map: dict[int, list[dict]] = {}
        for row in item_rows:
            item_map.setdefault(row["transaction_id"], []).append(self._serialize_transaction_item_row(row))
        return item_map

    def _build_transaction_payloads(
        self,
        transaction_ids: list[int],
        *,
        fixture_id: int | None = None,
        ownership_type: str | None = None,
    ) -> list[dict]:
        if not transaction_ids:
            return []
        tx_stmt = select(MaterialTransaction).where(MaterialTransaction.id.in_(transaction_ids))
        transactions = list(self.db.scalars(tx_stmt))
        if not transactions:
            return []
        transaction_map = {row.id: row for row in transactions}
        item_map = self._list_transaction_items(
            transaction_ids,
            fixture_id=fixture_id,
            ownership_type=ownership_type,
        )
        result: list[dict] = []
        for transaction_id in transaction_ids:
            tx = transaction_map.get(transaction_id)
            if tx is None:
                continue
            result.append(
                {
                    "id": tx.id,
                    "customer_id": tx.customer_id,
                    "transaction_type": tx.transaction_type,
                    "transaction_no": self._normalize_transaction_no(tx.transaction_no),
                    "occurred_at": tx.occurred_at,
                    "actor_user_id": tx.actor_user_id,
                    "created_by": tx.created_by,
                    "note": tx.note,
                    "created_at": tx.created_at,
                    "items": item_map.get(tx.id, []),
                }
            )
        return result

    def create_transaction(
        self,
        *,
        customer_id: int,
        transaction_type: str,
        occurred_at: datetime,
        actor_user_id: int,
        created_by: str,
        transaction_no: str,
        note: str | None,
    ) -> MaterialTransaction:
        normalized_transaction_no = transaction_no.strip()
        transaction = MaterialTransaction(
            customer_id=customer_id,
            transaction_type=transaction_type,
            transaction_no=normalized_transaction_no,
            occurred_at=occurred_at,
            actor_user_id=actor_user_id,
            created_by=created_by,
            note=note,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def add_transaction_item(
        self,
        *,
        transaction_id: int,
        fixture_id: int,
        fixture_code: str | None = None,
        fixture_name: str | None = None,
        ownership_type: str,
        identifier: str | None,
        quantity: int,
        note: str | None,
    ) -> MaterialTransactionItem:
        item = MaterialTransactionItem(
            transaction_id=transaction_id,
            fixture_id=fixture_id,
            deleted_fixture_code=fixture_code,
            deleted_fixture_name=fixture_name,
            ownership_type=ownership_type,
            identifier=identifier,
            quantity=quantity,
            note=note,
        )
        self.db.add(item)
        return item

    def remove_fixture_transaction_items(self, fixture: Fixture, *, delete_records: bool) -> dict:
        transaction_ids = list(
            self.db.scalars(
                select(MaterialTransactionItem.transaction_id)
                .where(MaterialTransactionItem.fixture_id == fixture.id)
                .distinct()
            )
        )
        item_count = int(
            self.db.scalar(
                select(func.count(MaterialTransactionItem.id)).where(MaterialTransactionItem.fixture_id == fixture.id)
            )
            or 0
        )
        deleted_transaction_count = 0

        if delete_records:
            self.db.execute(delete(MaterialTransactionItem).where(MaterialTransactionItem.fixture_id == fixture.id))
            for transaction_id in transaction_ids:
                remaining_item_count = int(
                    self.db.scalar(
                        select(func.count(MaterialTransactionItem.id)).where(
                            MaterialTransactionItem.transaction_id == transaction_id
                        )
                    )
                    or 0
                )
                if remaining_item_count == 0:
                    self.db.execute(delete(MaterialTransaction).where(MaterialTransaction.id == transaction_id))
                    deleted_transaction_count += 1
        else:
            self.db.execute(
                update(MaterialTransactionItem)
                .where(MaterialTransactionItem.fixture_id == fixture.id)
                .values(
                    fixture_id=None,
                    deleted_fixture_code=fixture.code,
                    deleted_fixture_name=fixture.name,
                )
            )

        self.db.flush()
        return {
            "transaction_item_count": item_count,
            "affected_transaction_count": len(transaction_ids),
            "deleted_transaction_count": deleted_transaction_count,
        }

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_fixture_by_code(self, code: str, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.code == code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

    def list_fixtures(self, customer_id: int | None = None) -> list[Fixture]:
        stmt = select(Fixture).order_by(Fixture.code.asc())
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def get_transaction(self, transaction_id: int, customer_id: int | None = None) -> MaterialTransaction | None:
        stmt = select(MaterialTransaction).where(MaterialTransaction.id == transaction_id)
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        return self.db.scalar(stmt)

    def find_recent_transactions_by_signature(
        self,
        *,
        customer_id: int,
        transaction_type: str,
        actor_user_id: int,
        transaction_no: str | None,
        created_at_from: datetime,
    ) -> list[MaterialTransaction]:
        normalized_transaction_no = (transaction_no or "").strip()
        if not normalized_transaction_no:
            return []

        stmt = (
            select(MaterialTransaction)
            .where(
                MaterialTransaction.customer_id == customer_id,
                MaterialTransaction.transaction_type == transaction_type,
                MaterialTransaction.actor_user_id == actor_user_id,
                MaterialTransaction.transaction_no == normalized_transaction_no,
                MaterialTransaction.created_at >= created_at_from,
            )
            .order_by(MaterialTransaction.created_at.desc(), MaterialTransaction.id.desc())
        )
        return list(self.db.scalars(stmt))

    def delete_transaction(self, transaction: MaterialTransaction) -> None:
        self.db.delete(transaction)
        self.db.flush()

    def get_or_create_stock_level(self, fixture_id: int) -> FixtureStockLevel:
        level = self.db.get(FixtureStockLevel, fixture_id)
        if level:
            return level
        level = FixtureStockLevel(fixture_id=fixture_id, min_stock_qty=0, warning_threshold=0, alert_enabled=True)
        self.db.add(level)
        self.db.flush()
        return level

    def get_or_create_stock_summary(self, fixture_id: int) -> FixtureStockSummary:
        summary = self.db.get(FixtureStockSummary, fixture_id)
        if summary:
            return summary
        summary = FixtureStockSummary(fixture_id=fixture_id, stock_qty=0, returned_qty=0, stock_status="normal")
        self.db.add(summary)
        self.db.flush()
        return summary

    def set_stock_status(
        self,
        summary: FixtureStockSummary,
        min_stock_qty: int,
        *,
        touch_last_transaction: bool = True,
    ) -> None:
        if summary.stock_qty <= 0:
            summary.stock_status = "out_of_stock"
        elif summary.stock_qty < min_stock_qty:
            summary.stock_status = "low_stock"
        else:
            summary.stock_status = "normal"
        if touch_last_transaction:
            summary.last_transaction_at = datetime.now(tz=timezone.utc)

    @staticmethod
    def _signed_stock_qty_expr():
        return case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )

    def _stock_breakdown_subquery(self, customer_id: int | None = None):
        signed_qty_expr = self._signed_stock_qty_expr()
        stmt = (
            select(
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransactionItem.ownership_type == "customer_supplied", signed_qty_expr),
                            else_=0,
                        )
                    ),
                    0,
                ).label("customer_supplied_qty"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransactionItem.ownership_type == "self_purchased", signed_qty_expr),
                            else_=0,
                        )
                    ),
                    0,
                ).label("self_purchased_qty"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(MaterialTransactionItem.fixture_id.is_not(None))
            .group_by(MaterialTransactionItem.fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        return stmt.subquery()

    @staticmethod
    def _stock_summary_expressions(stock_breakdown):
        customer_supplied_qty_expr = func.coalesce(stock_breakdown.c.customer_supplied_qty, 0)
        self_purchased_qty_expr = func.coalesce(stock_breakdown.c.self_purchased_qty, 0)
        stock_qty_expr = func.coalesce(FixtureStockSummary.stock_qty, 0)
        min_stock_qty_expr = func.coalesce(FixtureStockLevel.min_stock_qty, 0)
        stock_status_expr = case(
            (Fixture.is_active.is_(False), "normal"),
            (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
            else_="normal",
        )
        return (
            customer_supplied_qty_expr,
            self_purchased_qty_expr,
            stock_qty_expr,
            min_stock_qty_expr,
            stock_status_expr,
        )

    def get_available_identifier_qty(self, *, fixture_id: int, identifier: str, ownership_type: str) -> int:
        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("receipt_qty"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransaction.transaction_type == "return", MaterialTransactionItem.quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("return_qty"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(
                MaterialTransactionItem.fixture_id == fixture_id,
                MaterialTransactionItem.identifier == identifier,
                MaterialTransactionItem.ownership_type == ownership_type,
            )
        )
        row = self.db.execute(stmt).one()
        return int(row.receipt_qty or 0) - int(row.return_qty or 0)

    def list_stock_summary_rows(self, customer_id: int | None = None) -> list[dict]:
        stock_breakdown = self._stock_breakdown_subquery(customer_id)
        (
            customer_supplied_qty_expr,
            self_purchased_qty_expr,
            stock_qty_expr,
            min_stock_qty_expr,
            stock_status_expr,
        ) = self._stock_summary_expressions(stock_breakdown)
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                stock_qty_expr.label("stock_qty"),
                customer_supplied_qty_expr.label("customer_supplied_qty"),
                self_purchased_qty_expr.label("self_purchased_qty"),
                min_stock_qty_expr.label("min_stock_qty"),
                stock_status_expr.label("stock_status"),
                FixtureStockSummary.last_transaction_at.label("last_transaction_at"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .outerjoin(stock_breakdown, stock_breakdown.c.fixture_id == Fixture.id)
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def get_stock_summary_row(self, fixture_id: int, customer_id: int | None = None) -> dict | None:
        stock_breakdown = self._stock_breakdown_subquery(customer_id)
        (
            customer_supplied_qty_expr,
            self_purchased_qty_expr,
            stock_qty_expr,
            min_stock_qty_expr,
            stock_status_expr,
        ) = self._stock_summary_expressions(stock_breakdown)
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                stock_qty_expr.label("stock_qty"),
                customer_supplied_qty_expr.label("customer_supplied_qty"),
                self_purchased_qty_expr.label("self_purchased_qty"),
                min_stock_qty_expr.label("min_stock_qty"),
                stock_status_expr.label("stock_status"),
                FixtureStockSummary.last_transaction_at.label("last_transaction_at"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .outerjoin(stock_breakdown, stock_breakdown.c.fixture_id == Fixture.id)
            .where(Fixture.id == fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        row = self.db.execute(stmt).first()
        return None if row is None else dict(row._mapping)

    def list_stock_alert_rows(self, customer_id: int | None = None) -> list[dict]:
        stock_breakdown = self._stock_breakdown_subquery(customer_id)
        (
            customer_supplied_qty_expr,
            self_purchased_qty_expr,
            stock_qty_expr,
            min_stock_qty_expr,
            stock_status_expr,
        ) = self._stock_summary_expressions(stock_breakdown)
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                stock_qty_expr.label("stock_qty"),
                customer_supplied_qty_expr.label("customer_supplied_qty"),
                self_purchased_qty_expr.label("self_purchased_qty"),
                min_stock_qty_expr.label("min_stock_qty"),
                stock_status_expr.label("stock_status"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .outerjoin(stock_breakdown, stock_breakdown.c.fixture_id == Fixture.id)
            .where(Fixture.is_active.is_(True), stock_status_expr.in_(["low_stock", "out_of_stock"]))
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def summarize_transaction_quantities_on_date(self, target_date: date, *, customer_id: int | None = None) -> dict[str, int]:
        stmt = (
            select(
                MaterialTransaction.transaction_type.label("transaction_type"),
                func.coalesce(func.sum(MaterialTransactionItem.quantity), 0).label("quantity"),
            )
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .where(func.date(MaterialTransaction.occurred_at) == target_date.isoformat())
            .group_by(MaterialTransaction.transaction_type)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        totals = {"receipt": 0, "return": 0}
        for row in self.db.execute(stmt).all():
            totals[str(row.transaction_type)] = int(row.quantity or 0)
        return totals

    def list_recent_transaction_item_entries(
        self,
        limit: int,
        *,
        customer_id: int | None = None,
        transaction_type: str,
    ) -> list[dict]:
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        stmt = (
            select(
                MaterialTransaction.id.label("transaction_id"),
                MaterialTransactionItem.id.label("transaction_item_id"),
                MaterialTransaction.transaction_no.label("transaction_no"),
                MaterialTransaction.occurred_at.label("occurred_at"),
                fixture_code_expr.label("fixture_code"),
                MaterialTransactionItem.identifier.label("identifier"),
                MaterialTransactionItem.quantity.label("quantity"),
            )
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .where(MaterialTransaction.transaction_type == transaction_type)
            .order_by(MaterialTransaction.occurred_at.desc(), MaterialTransaction.id.desc(), MaterialTransactionItem.id.desc())
            .limit(limit)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        rows = [dict(row._mapping) for row in self.db.execute(stmt).all()]
        for row in rows:
            row["transaction_no"] = self._normalize_transaction_no(row["transaction_no"])
        return rows

    def list_identifier_stock_summary_rows(self, customer_id: int | None = None, fixture_id: int | None = None) -> list[dict]:
        signed_qty_expr = self._signed_stock_qty_expr()
        customer_supplied_qty_expr = func.coalesce(
            func.sum(
                case(
                    (MaterialTransactionItem.ownership_type == "customer_supplied", signed_qty_expr),
                    else_=0,
                )
            ),
            0,
        )
        self_purchased_qty_expr = func.coalesce(
            func.sum(
                case(
                    (MaterialTransactionItem.ownership_type == "self_purchased", signed_qty_expr),
                    else_=0,
                )
            ),
            0,
        )
        stock_qty_expr = customer_supplied_qty_expr + self_purchased_qty_expr
        stmt = (
            select(
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                MaterialTransactionItem.identifier.label("identifier"),
                stock_qty_expr.label("stock_qty"),
                customer_supplied_qty_expr.label("customer_supplied_qty"),
                self_purchased_qty_expr.label("self_purchased_qty"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .join(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .where(
                MaterialTransactionItem.identifier.is_not(None),
                MaterialTransactionItem.identifier != "",
            )
            .group_by(MaterialTransactionItem.fixture_id, MaterialTransactionItem.identifier)
            .having(stock_qty_expr > 0)
            .order_by(MaterialTransactionItem.fixture_id.asc(), MaterialTransactionItem.identifier.asc())
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id, Fixture.customer_id == customer_id)
        if fixture_id is not None:
            stmt = stmt.where(MaterialTransactionItem.fixture_id == fixture_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_transactions(
        self,
        limit: int,
        customer_id: int | None = None,
        *,
        fixture_id: int | None = None,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ) -> list[dict]:
        tx_id_stmt = self._build_transaction_id_stmt(
            customer_id=customer_id,
            fixture_id=fixture_id,
            transaction_type=transaction_type,
            ownership_type=ownership_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )
        tx_id_stmt = tx_id_stmt.order_by(MaterialTransaction.id.desc()).limit(limit)
        tx_ids = list(self.db.scalars(tx_id_stmt))
        return self._build_transaction_payloads(
            tx_ids,
            fixture_id=fixture_id,
            ownership_type=ownership_type,
        )

    def iter_transactions(
        self,
        customer_id: int | None = None,
        *,
        batch_size: int = 500,
        fixture_id: int | None = None,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ) -> Iterator[dict]:
        """Yield every matching transaction without retaining the full result set."""
        last_transaction_id: int | None = None
        while True:
            tx_id_stmt = self._build_transaction_id_stmt(
                customer_id=customer_id,
                fixture_id=fixture_id,
                transaction_type=transaction_type,
                ownership_type=ownership_type,
                date_from=date_from,
                date_to=date_to,
                fixture_code=fixture_code,
                transaction_no=transaction_no,
                identifier_exact_matches=identifier_exact_matches,
                identifier_contains=identifier_contains,
                created_by=created_by,
            )
            if last_transaction_id is not None:
                tx_id_stmt = tx_id_stmt.where(MaterialTransaction.id < last_transaction_id)
            tx_ids = list(
                self.db.scalars(
                    tx_id_stmt.order_by(MaterialTransaction.id.desc()).limit(batch_size)
                )
            )
            if not tx_ids:
                return
            yield from self._build_transaction_payloads(
                tx_ids,
                fixture_id=fixture_id,
                ownership_type=ownership_type,
            )
            last_transaction_id = tx_ids[-1]

    def list_transaction_page(
        self,
        page: int,
        page_size: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        created_by: str | None = None,
    ) -> dict:
        tx_id_stmt = self._build_transaction_id_stmt(
            customer_id=customer_id,
            transaction_type=transaction_type,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            created_by=created_by,
        )
        total = int(self.db.scalar(select(func.count()).select_from(tx_id_stmt.order_by(None).subquery())) or 0)
        paged_tx_id_stmt = (
            tx_id_stmt.order_by(MaterialTransaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        tx_ids = list(self.db.scalars(paged_tx_id_stmt))
        return {
            "items": self._build_transaction_payloads(tx_ids),
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def list_transaction_overview_page(
        self,
        page: int,
        page_size: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ) -> dict:
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        fixture_name_expr = func.coalesce(Fixture.name, MaterialTransactionItem.deleted_fixture_name)
        note_expr = func.coalesce(MaterialTransactionItem.note, MaterialTransaction.note)
        stmt = (
            select(
                MaterialTransactionItem.id.label("id"),
                MaterialTransaction.transaction_type.label("transaction_type"),
                MaterialTransaction.transaction_no.label("transaction_no"),
                MaterialTransaction.occurred_at.label("occurred_at"),
                MaterialTransaction.actor_user_id.label("actor_user_id"),
                MaterialTransaction.created_by.label("created_by"),
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                fixture_code_expr.label("fixture_code"),
                fixture_name_expr.label("fixture_name"),
                MaterialTransactionItem.ownership_type.label("ownership_type"),
                MaterialTransactionItem.identifier.label("identifier"),
                MaterialTransactionItem.quantity.label("quantity"),
                note_expr.label("note"),
            )
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        if transaction_type:
            stmt = stmt.where(MaterialTransaction.transaction_type.in_(self._filter_values(transaction_type)))
        if ownership_type:
            stmt = stmt.where(MaterialTransactionItem.ownership_type.in_(self._filter_values(ownership_type)))
        if date_from is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at <= date_to)
        stmt = self._apply_fixture_code_filter(stmt, fixture_code_expr, fixture_code)
        if transaction_no:
            stmt = stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
        stmt = self._apply_identifier_filter(
            stmt,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
        )
        if created_by:
            stmt = stmt.where(MaterialTransaction.created_by.ilike(f"%{created_by.strip()}%"))

        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        paged_stmt = (
            stmt.order_by(
                MaterialTransaction.occurred_at.desc(),
                MaterialTransaction.id.desc(),
                MaterialTransactionItem.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = [dict(row._mapping) for row in self.db.execute(paged_stmt).all()]
        for row in rows:
            row["transaction_no"] = self._normalize_transaction_no(row["transaction_no"])
        return {
            "items": rows,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def list_transaction_item_rows(
        self,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        ownership_type: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ) -> list[dict]:
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        fixture_name_expr = func.coalesce(Fixture.name, MaterialTransactionItem.deleted_fixture_name)
        stmt = (
            select(
                MaterialTransaction.id.label("transaction_id"),
                MaterialTransaction.transaction_type.label("transaction_type"),
                MaterialTransaction.transaction_no.label("transaction_no"),
                MaterialTransaction.occurred_at.label("occurred_at"),
                MaterialTransaction.created_by.label("created_by"),
                MaterialTransactionItem.id.label("transaction_item_id"),
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                MaterialTransactionItem.identifier.label("identifier"),
                MaterialTransactionItem.quantity.label("quantity"),
                fixture_code_expr.label("fixture_code"),
                fixture_name_expr.label("fixture_name"),
            )
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        if transaction_type:
            stmt = stmt.where(MaterialTransaction.transaction_type.in_(self._filter_values(transaction_type)))
        if date_from is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at <= date_to)
        stmt = self._apply_fixture_code_filter(stmt, fixture_code_expr, fixture_code)
        if transaction_no:
            stmt = stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
        if ownership_type:
            stmt = stmt.where(MaterialTransactionItem.ownership_type.in_(self._filter_values(ownership_type)))
        stmt = self._apply_identifier_filter(
            stmt,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
        )
        if created_by:
            stmt = stmt.where(MaterialTransaction.created_by.ilike(f"%{created_by.strip()}%"))
        stmt = stmt.order_by(MaterialTransaction.occurred_at.asc(), MaterialTransaction.id.asc(), MaterialTransactionItem.id.asc())
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    @staticmethod
    def _apply_identifier_filter(
        stmt,
        *,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
    ):
        clauses = []
        if identifier_exact_matches:
            clauses.append(MaterialTransactionItem.identifier.in_(identifier_exact_matches))
        if identifier_contains:
            clauses.append(MaterialTransactionItem.identifier.ilike(f"%{identifier_contains.strip()}%"))
        if not clauses:
            return stmt
        return stmt.where(or_(*clauses))

    @staticmethod
    def _apply_fixture_code_filter(stmt, fixture_code_expr, fixture_code: str | None):
        if not fixture_code:
            return stmt
        keywords = [value.strip() for value in fixture_code.split(",") if value.strip()]
        if not keywords:
            return stmt
        if len(keywords) == 1:
            return stmt.where(fixture_code_expr.ilike(f"%{keywords[0]}%"))
        return stmt.where(or_(*[fixture_code_expr.ilike(f"%{keyword}%") for keyword in keywords]))

    def summarize_transactions_by_fixture(self, customer_id: int | None = None) -> dict[int, dict]:
        stock_qty_expr = func.coalesce(
            func.sum(
                case(
                    (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
                    else_=-MaterialTransactionItem.quantity,
                )
            ),
            0,
        )
        returned_qty_expr = func.coalesce(
            func.sum(
                case(
                    (MaterialTransaction.transaction_type == "return", MaterialTransactionItem.quantity),
                    else_=0,
                )
            ),
            0,
        )
        stmt = (
            select(
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                stock_qty_expr.label("stock_qty"),
                returned_qty_expr.label("returned_qty"),
                func.max(MaterialTransaction.occurred_at).label("last_transaction_at"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(MaterialTransactionItem.fixture_id.is_not(None))
            .group_by(MaterialTransactionItem.fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        return {
            int(row.fixture_id): {
                "stock_qty": int(row.stock_qty or 0),
                "returned_qty": int(row.returned_qty or 0),
                "last_transaction_at": row.last_transaction_at,
            }
            for row in self.db.execute(stmt).all()
        }

    def count_transactions(self, customer_id: int | None = None) -> int:
        stmt = select(func.count(MaterialTransaction.id))
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        return int(self.db.scalar(stmt) or 0)

    def count_transaction_items(self, customer_id: int | None = None) -> int:
        stmt = select(func.count(MaterialTransactionItem.id)).join(
            MaterialTransaction,
            MaterialTransaction.id == MaterialTransactionItem.transaction_id,
        )
        if customer_id is not None:
            stmt = stmt.where(MaterialTransaction.customer_id == customer_id)
        return int(self.db.scalar(stmt) or 0)
