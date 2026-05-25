from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.master import FixtureCreate, MachineModelCreate, StationCreate


class MasterService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MasterRepository(db)

    def create_fixture(self, payload: FixtureCreate):
        try:
            fixture = self.repo.create_fixture(code=payload.code, name=payload.name, description=payload.description)
            self.db.commit()
            self.db.refresh(fixture)
            return fixture
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("fixture code already exists") from exc

    def list_fixtures(self):
        return self.repo.list_fixtures()

    def create_model(self, payload: MachineModelCreate):
        try:
            model = self.repo.create_model(code=payload.code, name=payload.name)
            self.db.commit()
            self.db.refresh(model)
            return model
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model code already exists") from exc

    def list_models(self):
        return self.repo.list_models()

    def create_station(self, payload: StationCreate):
        try:
            station = self.repo.create_station(code=payload.code, name=payload.name)
            self.db.commit()
            self.db.refresh(station)
            return station
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("station code already exists") from exc

    def list_stations(self):
        return self.repo.list_stations()
