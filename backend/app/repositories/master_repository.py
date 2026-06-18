from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockLevel
from backend.app.models.master import Customer, Fixture, MachineModel, Station, User, UserCustomer


class MasterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_customer(self, *, code: str, name: str) -> Customer:
        customer = Customer(code=code, name=name)
        self.db.add(customer)
        self.db.flush()
        return customer

    def list_customers(self) -> list[Customer]:
        return list(self.db.scalars(select(Customer).order_by(Customer.code)))

    def list_customers_by_ids(self, customer_ids: list[int]) -> list[Customer]:
        if not customer_ids:
            return []
        stmt = select(Customer).where(Customer.id.in_(customer_ids)).order_by(Customer.code)
        return list(self.db.scalars(stmt))

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def get_customer_by_code(self, code: str) -> Customer | None:
        stmt = select(Customer).where(Customer.code == code)
        return self.db.scalar(stmt)

    def update_customer(self, customer: Customer, *, code: str, name: str) -> Customer:
        customer.code = code
        customer.name = name
        self.db.flush()
        return customer

    def create_fixture(
        self,
        *,
        customer_id: int,
        responsible_user_id: int | None,
        code: str,
        name: str,
        storage_location: str | None,
        description: str | None,
    ) -> Fixture:
        fixture = Fixture(
            customer_id=customer_id,
            responsible_user_id=responsible_user_id,
            code=code,
            name=name,
            storage_location=storage_location,
            description=description,
        )
        self.db.add(fixture)
        self.db.flush()
        return fixture

    def list_fixtures(self, customer_id: int | None = None) -> list[Fixture]:
        stmt = select(Fixture).order_by(Fixture.code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_fixture_by_code(self, code: str, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.code == code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_stock_level(self, fixture_id: int) -> FixtureStockLevel | None:
        return self.db.get(FixtureStockLevel, fixture_id)

    def list_stock_levels(self, fixture_ids: list[int]) -> dict[int, FixtureStockLevel]:
        if not fixture_ids:
            return {}
        stmt = select(FixtureStockLevel).where(FixtureStockLevel.fixture_id.in_(fixture_ids))
        levels = list(self.db.scalars(stmt))
        return {level.fixture_id: level for level in levels}

    def update_fixture(
        self,
        fixture: Fixture,
        *,
        customer_id: int,
        responsible_user_id: int | None,
        code: str,
        name: str,
        storage_location: str | None,
        description: str | None,
        is_active: bool,
    ) -> Fixture:
        fixture.customer_id = customer_id
        fixture.responsible_user_id = responsible_user_id
        fixture.code = code
        fixture.name = name
        fixture.storage_location = storage_location
        fixture.description = description
        fixture.is_active = is_active
        self.db.flush()
        return fixture

    def get_or_create_stock_level(self, fixture_id: int) -> FixtureStockLevel:
        level = self.db.get(FixtureStockLevel, fixture_id)
        if level is not None:
            return level
        level = FixtureStockLevel(fixture_id=fixture_id, min_stock_qty=0, warning_threshold=0, alert_enabled=True)
        self.db.add(level)
        self.db.flush()
        return level

    def create_model(self, *, customer_id: int, code: str, name: str) -> MachineModel:
        model = MachineModel(customer_id=customer_id, code=code, name=name, is_active=True)
        self.db.add(model)
        self.db.flush()
        return model

    def list_models(self, customer_id: int | None = None) -> list[MachineModel]:
        stmt = select(MachineModel).order_by(MachineModel.code)
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def get_model(self, model_id: int, customer_id: int | None = None) -> MachineModel | None:
        stmt = select(MachineModel).where(MachineModel.id == model_id)
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_model_by_code(self, code: str, customer_id: int | None = None) -> MachineModel | None:
        stmt = select(MachineModel).where(MachineModel.code == code)
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        return self.db.scalar(stmt)

    def update_model(self, model: MachineModel, *, code: str, name: str, is_active: bool) -> MachineModel:
        model.code = code
        model.name = name
        model.is_active = is_active
        self.db.flush()
        return model

    def create_station(self, *, customer_id: int, code: str, name: str) -> Station:
        station = Station(customer_id=customer_id, code=code, name=name, is_active=True)
        self.db.add(station)
        self.db.flush()
        return station

    def list_stations(self, customer_id: int | None = None) -> list[Station]:
        stmt = select(Station).order_by(Station.code)
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def get_station(self, station_id: int, customer_id: int | None = None) -> Station | None:
        stmt = select(Station).where(Station.id == station_id)
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_station_by_code(self, code: str, customer_id: int | None = None) -> Station | None:
        stmt = select(Station).where(Station.code == code)
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return self.db.scalar(stmt)

    def update_station(self, station: Station, *, code: str, name: str, is_active: bool) -> Station:
        station.code = code
        station.name = name
        station.is_active = is_active
        self.db.flush()
        return station

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.username)))

    def list_users_by_ids(self, user_ids: list[int]) -> list[User]:
        if not user_ids:
            return []
        stmt = select(User).where(User.id.in_(user_ids)).order_by(User.username)
        return list(self.db.scalars(stmt))

    def list_users_by_customer(self, customer_id: int) -> list[User]:
        stmt = (
            select(User)
            .join(UserCustomer, UserCustomer.user_id == User.id)
            .where(UserCustomer.customer_id == customer_id)
            .order_by(User.display_name, User.username)
        )
        return list(self.db.scalars(stmt))

    def list_allowed_customer_ids_for_user(self, user_id: int) -> list[int]:
        stmt = select(UserCustomer.customer_id).where(UserCustomer.user_id == user_id).order_by(UserCustomer.customer_id)
        return list(self.db.scalars(stmt))

    def list_allowed_user_ids_for_customer(self, customer_id: int) -> list[int]:
        stmt = select(UserCustomer.user_id).where(UserCustomer.customer_id == customer_id).order_by(UserCustomer.user_id)
        return list(self.db.scalars(stmt))

    def replace_allowed_customers_for_user(self, user_id: int, customer_ids: list[int]) -> None:
        self.db.execute(delete(UserCustomer).where(UserCustomer.user_id == user_id))
        unique_customer_ids = sorted(set(customer_ids))
        if not unique_customer_ids:
            self.db.flush()
            return
        self.db.add_all([UserCustomer(user_id=user_id, customer_id=customer_id) for customer_id in unique_customer_ids])
        self.db.flush()

    def replace_allowed_users_for_customer(self, customer_id: int, user_ids: list[int]) -> None:
        self.db.execute(delete(UserCustomer).where(UserCustomer.customer_id == customer_id))
        unique_user_ids = sorted(set(user_ids))
        if not unique_user_ids:
            self.db.flush()
            return
        self.db.add_all([UserCustomer(user_id=user_id, customer_id=customer_id) for user_id in unique_user_ids])
        self.db.flush()

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)

    def create_user(
        self, *, username: str, password_hash: str, display_name: str, role: str = "user", is_active: bool = True
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_user(self, user: User, *, display_name: str, role: str, is_active: bool) -> User:
        user.display_name = display_name
        user.role = role
        user.is_active = is_active
        self.db.flush()
        return user
