from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.models.master import Fixture
from backend.app.models.warehouse import FixtureImage, FixtureLocationAssignment, StorageLocation


class WarehouseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_location(self, location_id: int) -> StorageLocation | None:
        return self.db.get(StorageLocation, location_id)

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

    def create_or_update_assignment(self, *, fixture_id: int, location_id: int) -> FixtureLocationAssignment:
        stmt = select(FixtureLocationAssignment).where(FixtureLocationAssignment.fixture_id == fixture_id)
        assignment = self.db.scalar(stmt)
        if assignment:
            assignment.location_id = location_id
            self.db.flush()
            return assignment
        assignment = FixtureLocationAssignment(fixture_id=fixture_id, location_id=location_id)
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def list_assignments(self) -> list[FixtureLocationAssignment]:
        stmt = select(FixtureLocationAssignment).order_by(FixtureLocationAssignment.id.desc())
        return list(self.db.scalars(stmt))

    def create_fixture_image(
        self, *, fixture_id: int, image_path: str, thumbnail_path: str | None, is_main: bool
    ) -> FixtureImage:
        if is_main:
            self.db.execute(
                update(FixtureImage).where(FixtureImage.fixture_id == fixture_id).values(is_main=False)
            )
        image = FixtureImage(
            fixture_id=fixture_id, image_path=image_path, thumbnail_path=thumbnail_path, is_main=is_main
        )
        self.db.add(image)
        self.db.flush()
        return image

    def list_fixture_images(self, fixture_id: int | None = None) -> list[FixtureImage]:
        stmt = select(FixtureImage).order_by(FixtureImage.id.desc())
        if fixture_id is not None:
            stmt = stmt.where(FixtureImage.fixture_id == fixture_id)
        return list(self.db.scalars(stmt))
