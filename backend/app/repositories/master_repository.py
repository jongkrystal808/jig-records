from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.master import Fixture, MachineModel, Station


class MasterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_fixture(self, *, code: str, name: str, description: str | None) -> Fixture:
        fixture = Fixture(code=code, name=name, description=description)
        self.db.add(fixture)
        self.db.flush()
        return fixture

    def list_fixtures(self) -> list[Fixture]:
        return list(self.db.scalars(select(Fixture).order_by(Fixture.code)))

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def create_model(self, *, code: str, name: str) -> MachineModel:
        model = MachineModel(code=code, name=name)
        self.db.add(model)
        self.db.flush()
        return model

    def list_models(self) -> list[MachineModel]:
        return list(self.db.scalars(select(MachineModel).order_by(MachineModel.code)))

    def create_station(self, *, code: str, name: str) -> Station:
        station = Station(code=code, name=name)
        self.db.add(station)
        self.db.flush()
        return station

    def list_stations(self) -> list[Station]:
        return list(self.db.scalars(select(Station).order_by(Station.code)))

    def get_station(self, station_id: int) -> Station | None:
        return self.db.get(Station, station_id)
