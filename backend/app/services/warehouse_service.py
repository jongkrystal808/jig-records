from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.repositories.warehouse_repository import WarehouseRepository
from backend.app.schemas.warehouse import FixtureImageCreate, FixtureLocationAssignmentCreate, StorageLocationCreate


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

    def assign_fixture_location(self, payload: FixtureLocationAssignmentCreate):
        fixture = self.repo.get_fixture(payload.fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {payload.fixture_id} not found")

        location = self.repo.get_location(payload.location_id)
        if location is None:
            raise ValueError(f"location {payload.location_id} not found")

        assignment = self.repo.create_or_update_assignment(fixture_id=payload.fixture_id, location_id=payload.location_id)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def list_assignments(self):
        return self.repo.list_assignments()

    def create_fixture_image(self, payload: FixtureImageCreate):
        fixture = self.repo.get_fixture(payload.fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {payload.fixture_id} not found")

        image = self.repo.create_fixture_image(
            fixture_id=payload.fixture_id,
            image_path=payload.image_path,
            thumbnail_path=payload.thumbnail_path,
            is_main=payload.is_main,
        )
        self.db.commit()
        self.db.refresh(image)
        return image

    def list_fixture_images(self, fixture_id: int | None):
        return self.repo.list_fixture_images(fixture_id)
