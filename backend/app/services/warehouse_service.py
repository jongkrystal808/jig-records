from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.repositories.warehouse_repository import WarehouseRepository
from backend.app.schemas.warehouse import StorageLocationCreate


class WarehouseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WarehouseRepository(db)

    def create_location(self, payload: StorageLocationCreate):
        try:
            location = self.repo.create_location(
                code=payload.code,
                area=payload.area,
                rack=payload.rack,
                layer=payload.layer,
                description=payload.description,
                image_path=payload.image_path,
            )
            self.db.commit()
            self.db.refresh(location)
            return location
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("location code already exists") from exc

    def list_locations(self):
        return self.repo.list_locations()
