from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.warehouse import StorageLocation


class WarehouseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_location(
        self, *, code: str, area: str, rack: str, layer: str, description: str | None, image_path: str | None
    ) -> StorageLocation:
        location = StorageLocation(
            code=code, area=area, rack=rack, layer=layer, description=description, image_path=image_path
        )
        self.db.add(location)
        self.db.flush()
        return location

    def list_locations(self) -> list[StorageLocation]:
        return list(self.db.scalars(select(StorageLocation).order_by(StorageLocation.code)))
