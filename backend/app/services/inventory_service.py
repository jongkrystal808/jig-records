from sqlalchemy.orm import Session

from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.services.production_service import ProductionService


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InventoryRepository(db)
        self.capacity_service = ProductionService(db)

    def receipt(self, payload: StockTransactionCreate) -> None:
        self._apply_transaction(payload, "receipt")

    def return_material(self, payload: StockTransactionCreate) -> None:
        self._apply_transaction(payload, "return")

    def _apply_transaction(self, payload: StockTransactionCreate, transaction_type: str) -> None:
        transaction = self.repo.create_transaction(transaction_type=transaction_type, note=payload.note)
        changed_station_ids: set[int] = set()

        for item in payload.items:
            fixture = self.repo.get_fixture(item.fixture_id)
            if fixture is None:
                self.db.rollback()
                raise ValueError(f"fixture {item.fixture_id} not found")

            self.repo.add_transaction_item(transaction_id=transaction.id, fixture_id=item.fixture_id, qty=item.qty)
            level = self.repo.get_or_create_stock_level(item.fixture_id)
            summary = self.repo.get_or_create_stock_summary(item.fixture_id)

            if transaction_type == "receipt":
                summary.stock_qty += item.qty
            else:
                next_qty = summary.stock_qty - item.qty
                if next_qty < 0:
                    self.db.rollback()
                    raise ValueError(f"fixture {fixture.code} stock is not enough for return")
                summary.stock_qty = next_qty
                summary.returned_qty += item.qty

            self.repo.set_stock_status(summary, level.min_stock_qty)
            changed_station_ids.update(self.capacity_service.get_affected_station_ids_by_fixture(item.fixture_id))

        for station_id in changed_station_ids:
            self.capacity_service.recalculate_station_capacity(station_id)

        self.db.commit()

    def list_stock_summary(self):
        return self.repo.list_stock_summary_rows()

    def list_alerts(self):
        return self.repo.list_stock_alert_rows()

    def list_transactions(self, limit: int):
        return self.repo.list_transactions(limit)
