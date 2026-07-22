from datetime import datetime, timezone

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

    def create_transaction(
        self,
        *,
        customer_id: int,
        transaction_type: str,
        occurred_at: datetime,
        created_by: str,
        transaction_no: str | None,
        note: str | None,
    ) -> MaterialTransaction:
        normalized_transaction_no = (transaction_no or "").strip()
        temp_no = normalized_transaction_no or f"TMP-{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S%f}-{customer_id}"
        transaction = MaterialTransaction(
            customer_id=customer_id,
            transaction_type=transaction_type,
            transaction_no=temp_no,
            occurred_at=occurred_at,
            created_by=created_by,
            note=note,
        )
        self.db.add(transaction)
        self.db.flush()
        if not normalized_transaction_no:
            prefix = "RCV" if transaction_type == "receipt" else "RTN"
            transaction.transaction_no = f"{prefix}-{occurred_at:%Y%m%d}-{transaction.id:06d}"
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
        created_by: str,
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
                MaterialTransaction.created_by == created_by,
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

    def get_available_identifier_qty(self, *, fixture_id: int, identifier: str) -> int:
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
            )
        )
        row = self.db.execute(stmt).one()
        return int(row.receipt_qty or 0) - int(row.return_qty or 0)

    def list_stock_summary_rows(self, customer_id: int | None = None) -> list[dict]:
        stock_status_expr = case(
            (Fixture.is_active.is_(False), "normal"),
            (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
            else_="normal",
        )
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                case((FixtureStockSummary.stock_qty.is_not(None), FixtureStockSummary.stock_qty), else_=0).label("stock_qty"),
                case((FixtureStockLevel.min_stock_qty.is_not(None), FixtureStockLevel.min_stock_qty), else_=0).label(
                    "min_stock_qty"
                ),
                stock_status_expr.label("stock_status"),
                FixtureStockSummary.last_transaction_at.label("last_transaction_at"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def get_stock_summary_row(self, fixture_id: int, customer_id: int | None = None) -> dict | None:
        stock_status_expr = case(
            (Fixture.is_active.is_(False), "normal"),
            (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
            else_="normal",
        )
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                case((FixtureStockSummary.stock_qty.is_not(None), FixtureStockSummary.stock_qty), else_=0).label("stock_qty"),
                case((FixtureStockLevel.min_stock_qty.is_not(None), FixtureStockLevel.min_stock_qty), else_=0).label(
                    "min_stock_qty"
                ),
                stock_status_expr.label("stock_status"),
                FixtureStockSummary.last_transaction_at.label("last_transaction_at"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .where(Fixture.id == fixture_id)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        row = self.db.execute(stmt).first()
        return None if row is None else dict(row._mapping)

    def list_stock_alert_rows(self, customer_id: int | None = None) -> list[dict]:
        stock_status_expr = case(
            (Fixture.is_active.is_(False), "normal"),
            (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
            else_="normal",
        )
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                case((FixtureStockSummary.stock_qty.is_not(None), FixtureStockSummary.stock_qty), else_=0).label("stock_qty"),
                case((FixtureStockLevel.min_stock_qty.is_not(None), FixtureStockLevel.min_stock_qty), else_=0).label(
                    "min_stock_qty"
                ),
                stock_status_expr.label("stock_status"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .where(Fixture.is_active.is_(True), stock_status_expr.in_(["low_stock", "out_of_stock"]))
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_identifier_stock_summary_rows(self, customer_id: int | None = None, fixture_id: int | None = None) -> list[dict]:
        stock_qty_expr = (
            func.coalesce(
                func.sum(
                    case(
                        (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
                        else_=-MaterialTransactionItem.quantity,
                    )
                ),
                0,
            )
        )
        stmt = (
            select(
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                MaterialTransactionItem.identifier.label("identifier"),
                stock_qty_expr.label("stock_qty"),
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
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier_exact_matches: list[str] | None = None,
        identifier_contains: str | None = None,
        created_by: str | None = None,
    ) -> list[dict]:
        fixture_code_expr = func.coalesce(Fixture.code, MaterialTransactionItem.deleted_fixture_code)
        fixture_name_expr = func.coalesce(Fixture.name, MaterialTransactionItem.deleted_fixture_name)
        tx_id_stmt = (
            select(MaterialTransaction.id)
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .outerjoin(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .distinct()
        )
        if customer_id is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.customer_id == customer_id)
        if fixture_id is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransactionItem.fixture_id == fixture_id)
        if transaction_type:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.transaction_type == transaction_type)
        if date_from is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.occurred_at <= date_to)
        if fixture_code:
            tx_id_stmt = tx_id_stmt.where(fixture_code_expr.ilike(f"%{fixture_code.strip()}%"))
        if transaction_no:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
        tx_id_stmt = self._apply_identifier_filter(
            tx_id_stmt,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
        )
        if created_by:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.created_by.ilike(f"%{created_by.strip()}%"))
        tx_id_stmt = tx_id_stmt.order_by(MaterialTransaction.id.desc()).limit(limit)
        tx_ids = list(self.db.scalars(tx_id_stmt))
        if not tx_ids:
            return []

        tx_stmt = select(MaterialTransaction).where(MaterialTransaction.id.in_(tx_ids)).order_by(MaterialTransaction.id.desc())
        transactions = list(self.db.scalars(tx_stmt))
        if not transactions:
            return []

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
            .where(MaterialTransactionItem.transaction_id.in_(tx_ids))
            .order_by(MaterialTransactionItem.id.asc())
        )
        if fixture_id is not None:
            item_stmt = item_stmt.where(MaterialTransactionItem.fixture_id == fixture_id)
        item_rows = [dict(row._mapping) for row in self.db.execute(item_stmt).all()]
        item_map: dict[int, list[dict]] = {}
        for row in item_rows:
            item_map.setdefault(row["transaction_id"], []).append(
                {
                    "fixture_id": row["fixture_id"],
                    "fixture_code": row["fixture_code"],
                    "fixture_name": row["fixture_name"],
                    "ownership_type": row["ownership_type"],
                    "identifier": row["identifier"],
                    "quantity": row["quantity"],
                    "note": row["note"],
                }
            )

        result: list[dict] = []
        for tx in transactions:
            result.append(
                {
                    "id": tx.id,
                    "customer_id": tx.customer_id,
                    "transaction_type": tx.transaction_type,
                    "transaction_no": tx.transaction_no,
                    "occurred_at": tx.occurred_at,
                    "created_by": tx.created_by,
                    "note": tx.note,
                    "created_at": tx.created_at,
                    "items": item_map.get(tx.id, []),
                }
            )
        return result

    def list_transaction_item_rows(
        self,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
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
            stmt = stmt.where(MaterialTransaction.transaction_type == transaction_type)
        if date_from is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(MaterialTransaction.occurred_at <= date_to)
        if fixture_code:
            stmt = stmt.where(fixture_code_expr.ilike(f"%{fixture_code.strip()}%"))
        if transaction_no:
            stmt = stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
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
