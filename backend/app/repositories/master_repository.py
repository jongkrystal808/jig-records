from collections.abc import Iterator

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary
from backend.app.models.master import (
    Customer,
    Fixture,
    MachineModel,
    ModelStation,
    Station,
    User,
    UserCustomer,
    UserModelShortcut,
)
from backend.app.models.production import FixtureRequirement, MachineCapacitySummary


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
        line_storage_location: str | None = None,
        department_storage_location: str | None = None,
        description: str | None,
    ) -> Fixture:
        fixture = Fixture(
            customer_id=customer_id,
            responsible_user_id=responsible_user_id,
            code=code,
            name=name,
            line_storage_location=line_storage_location,
            department_storage_location=department_storage_location,
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

    def list_fixtures_page(
        self,
        *,
        customer_id: int,
        page: int,
        page_size: int,
        keyword: str = "",
        is_active: bool | None = None,
        image_codes: set[str] | None = None,
        has_image: bool | None = None,
    ) -> tuple[list[Fixture], int]:
        stmt = select(Fixture).where(Fixture.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(Fixture.code.ilike(pattern), Fixture.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(Fixture.is_active == is_active)
        if has_image is not None:
            normalized_image_codes = {code.lower() for code in image_codes or set()}
            if has_image and not normalized_image_codes:
                return [], 0
            if normalized_image_codes:
                image_condition = func.lower(Fixture.code).in_(normalized_image_codes)
                stmt = stmt.where(image_condition if has_image else ~image_condition)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(self.db.scalars(stmt.order_by(Fixture.code).offset((page - 1) * page_size).limit(page_size)))
        return rows, total

    def iter_fixture_export_rows(
        self,
        *,
        customer_id: int,
        keyword: str = "",
        is_active: bool | None = None,
        image_codes: set[str] | None = None,
        has_image: bool | None = None,
    ) -> Iterator[dict]:
        stmt = (
            select(
                Fixture.code.label("code"),
                Fixture.name.label("name"),
                Fixture.line_storage_location.label("line_storage_location"),
                Fixture.department_storage_location.label("department_storage_location"),
                func.coalesce(FixtureStockLevel.min_stock_qty, 0).label("min_stock_qty"),
                Fixture.is_active.label("is_active"),
            )
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .where(Fixture.customer_id == customer_id)
        )
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(Fixture.code.ilike(pattern), Fixture.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(Fixture.is_active == is_active)
        if has_image is not None:
            normalized_image_codes = {code.lower() for code in image_codes or set()}
            if has_image and not normalized_image_codes:
                return
            if normalized_image_codes:
                image_condition = func.lower(Fixture.code).in_(normalized_image_codes)
                stmt = stmt.where(image_condition if has_image else ~image_condition)
        rows = self.db.execute(stmt.order_by(Fixture.code).execution_options(yield_per=500))
        for row in rows:
            yield dict(row._mapping)

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_fixture_by_code(self, code: str, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.code == code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

    def list_globally_unique_fixture_codes(self, codes: list[str]) -> set[str]:
        if not codes:
            return set()
        normalized_codes = {code.lower() for code in codes}
        stmt = (
            select(func.lower(Fixture.code).label("normalized_code"))
            .where(func.lower(Fixture.code).in_(normalized_codes))
            .group_by(func.lower(Fixture.code))
            .having(func.count(Fixture.id) == 1)
        )
        unique_normalized_codes = set(self.db.scalars(stmt))
        return {code for code in codes if code.lower() in unique_normalized_codes}

    def is_fixture_code_globally_unique(self, code: str) -> bool:
        stmt = select(func.count(Fixture.id)).where(func.lower(Fixture.code) == code.lower())
        return int(self.db.scalar(stmt) or 0) == 1

    def get_stock_level(self, fixture_id: int) -> FixtureStockLevel | None:
        return self.db.get(FixtureStockLevel, fixture_id)

    def list_stock_levels(self, fixture_ids: list[int]) -> dict[int, FixtureStockLevel]:
        if not fixture_ids:
            return {}
        stmt = select(FixtureStockLevel).where(FixtureStockLevel.fixture_id.in_(fixture_ids))
        levels = list(self.db.scalars(stmt))
        return {level.fixture_id: level for level in levels}

    def count_related_models_by_fixture(self, fixture_ids: list[int]) -> dict[int, int]:
        if not fixture_ids:
            return {}
        stmt = (
            select(
                FixtureRequirement.fixture_id.label("fixture_id"),
                func.count(func.distinct(FixtureRequirement.model_id)).label("related_model_count"),
            )
            .where(FixtureRequirement.fixture_id.in_(fixture_ids))
            .group_by(FixtureRequirement.fixture_id)
        )
        return {
            int(row.fixture_id): int(row.related_model_count or 0)
            for row in self.db.execute(stmt).all()
        }

    def update_fixture(
        self,
        fixture: Fixture,
        *,
        customer_id: int,
        responsible_user_id: int | None,
        code: str,
        name: str,
        line_storage_location: str | None = None,
        department_storage_location: str | None = None,
        description: str | None,
        is_active: bool,
    ) -> Fixture:
        fixture.customer_id = customer_id
        fixture.responsible_user_id = responsible_user_id
        fixture.code = code
        fixture.name = name
        fixture.line_storage_location = line_storage_location
        fixture.department_storage_location = department_storage_location
        fixture.description = description
        fixture.is_active = is_active
        self.db.flush()
        return fixture

    def delete_fixture(self, fixture: Fixture) -> int:
        affected_station_ids = list(
            self.db.scalars(
                select(FixtureRequirement.station_id)
                .where(FixtureRequirement.fixture_id == fixture.id)
                .distinct()
            )
        )
        requirement_count = int(
            self.db.scalar(
                select(func.count(FixtureRequirement.id)).where(FixtureRequirement.fixture_id == fixture.id)
            )
            or 0
        )
        self.db.execute(delete(FixtureRequirement).where(FixtureRequirement.fixture_id == fixture.id))
        if affected_station_ids:
            self.db.execute(
                delete(MachineCapacitySummary).where(MachineCapacitySummary.station_id.in_(affected_station_ids))
            )
        self.db.execute(delete(FixtureStockLevel).where(FixtureStockLevel.fixture_id == fixture.id))
        self.db.execute(delete(FixtureStockSummary).where(FixtureStockSummary.fixture_id == fixture.id))
        self.db.delete(fixture)
        self.db.flush()
        return requirement_count

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

    def list_models_page(self, *, customer_id: int, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> tuple[list[MachineModel], int]:
        stmt = select(MachineModel).where(MachineModel.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(MachineModel.code.ilike(pattern), MachineModel.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(MachineModel.is_active == is_active)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(self.db.scalars(stmt.order_by(MachineModel.code).offset((page - 1) * page_size).limit(page_size)))
        return rows, total

    def iter_models(self, *, customer_id: int, keyword: str = "", is_active: bool | None = None) -> Iterator[MachineModel]:
        stmt = select(MachineModel).where(MachineModel.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(MachineModel.code.ilike(pattern), MachineModel.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(MachineModel.is_active == is_active)
        yield from self.db.scalars(stmt.order_by(MachineModel.code).execution_options(yield_per=500))

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

    def delete_model(self, model: MachineModel) -> dict:
        affected_station_ids = list(
            {
                *self.db.scalars(
                    select(func.distinct(ModelStation.station_id)).where(ModelStation.model_id == model.id)
                ),
                *self.db.scalars(
                    select(func.distinct(FixtureRequirement.station_id)).where(FixtureRequirement.model_id == model.id)
                ),
            }
        )
        mapping_count = int(
            self.db.scalar(
                select(func.count(ModelStation.id)).where(ModelStation.model_id == model.id)
            )
            or 0
        )
        requirement_count = int(
            self.db.scalar(
                select(func.count(FixtureRequirement.id)).where(FixtureRequirement.model_id == model.id)
            )
            or 0
        )
        capacity_summary_count = int(
            self.db.scalar(
                select(func.count(MachineCapacitySummary.station_id)).where(
                    MachineCapacitySummary.station_id.in_(affected_station_ids)
                )
            )
            or 0
        ) if affected_station_ids else 0
        self.db.execute(delete(FixtureRequirement).where(FixtureRequirement.model_id == model.id))
        self.db.execute(delete(ModelStation).where(ModelStation.model_id == model.id))
        if affected_station_ids:
            self.db.execute(delete(MachineCapacitySummary).where(MachineCapacitySummary.station_id.in_(affected_station_ids)))
        self.db.delete(model)
        self.db.flush()
        return {
            "deleted_model_station_count": mapping_count,
            "deleted_requirement_count": requirement_count,
            "deleted_capacity_summary_count": capacity_summary_count,
        }

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

    def list_stations_page(self, *, customer_id: int, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> tuple[list[Station], int]:
        stmt = select(Station).where(Station.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(Station.code.ilike(pattern), Station.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(Station.is_active == is_active)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(self.db.scalars(stmt.order_by(Station.code).offset((page - 1) * page_size).limit(page_size)))
        return rows, total

    def iter_stations(self, *, customer_id: int, keyword: str = "", is_active: bool | None = None) -> Iterator[Station]:
        stmt = select(Station).where(Station.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(Station.code.ilike(pattern), Station.name.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(Station.is_active == is_active)
        yield from self.db.scalars(stmt.order_by(Station.code).execution_options(yield_per=500))

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

    def delete_station(self, station: Station) -> dict:
        mapping_count = int(
            self.db.scalar(select(func.count(ModelStation.id)).where(ModelStation.station_id == station.id))
            or 0
        )
        requirement_count = int(
            self.db.scalar(select(func.count(FixtureRequirement.id)).where(FixtureRequirement.station_id == station.id))
            or 0
        )
        capacity_summary_count = int(
            self.db.scalar(
                select(func.count(MachineCapacitySummary.station_id)).where(MachineCapacitySummary.station_id == station.id)
            )
            or 0
        )
        self.db.execute(delete(FixtureRequirement).where(FixtureRequirement.station_id == station.id))
        self.db.execute(delete(ModelStation).where(ModelStation.station_id == station.id))
        self.db.execute(delete(MachineCapacitySummary).where(MachineCapacitySummary.station_id == station.id))
        self.db.delete(station)
        self.db.flush()
        return {
            "deleted_model_station_count": mapping_count,
            "deleted_requirement_count": requirement_count,
            "deleted_capacity_summary_count": capacity_summary_count,
        }

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.username)))

    def list_users_page(self, *, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> tuple[list[User], int]:
        stmt = select(User)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(User.username.ilike(pattern), User.display_name.ilike(pattern), User.email.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(self.db.scalars(stmt.order_by(User.username).offset((page - 1) * page_size).limit(page_size)))
        return rows, total

    def iter_users(self, *, keyword: str = "", is_active: bool | None = None) -> Iterator[User]:
        stmt = select(User)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(User.username.ilike(pattern), User.display_name.ilike(pattern), User.email.ilike(pattern)))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        yield from self.db.scalars(stmt.order_by(User.username).execution_options(yield_per=500))

    def iter_customers(self, *, keyword: str = "", customer_ids: list[int] | None = None) -> Iterator[Customer]:
        if customer_ids == []:
            return
        stmt = select(Customer)
        if customer_ids is not None:
            stmt = stmt.where(Customer.id.in_(customer_ids))
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(Customer.code.ilike(pattern), Customer.name.ilike(pattern)))
        yield from self.db.scalars(stmt.order_by(Customer.code).execution_options(yield_per=500))

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

    def list_allowed_customer_ids_for_users(self, user_ids: list[int]) -> dict[int, list[int]]:
        result = {user_id: [] for user_id in user_ids}
        if not user_ids:
            return result
        rows = self.db.execute(
            select(UserCustomer.user_id, UserCustomer.customer_id)
            .where(UserCustomer.user_id.in_(user_ids))
            .order_by(UserCustomer.user_id, UserCustomer.customer_id)
        )
        for user_id, customer_id in rows:
            result[int(user_id)].append(int(customer_id))
        return result

    def list_allowed_user_ids_for_customer(self, customer_id: int) -> list[int]:
        stmt = select(UserCustomer.user_id).where(UserCustomer.customer_id == customer_id).order_by(UserCustomer.user_id)
        return list(self.db.scalars(stmt))

    def list_allowed_user_ids_for_customers(self, customer_ids: list[int]) -> dict[int, list[int]]:
        result = {customer_id: [] for customer_id in customer_ids}
        if not customer_ids:
            return result
        rows = self.db.execute(
            select(UserCustomer.customer_id, UserCustomer.user_id)
            .where(UserCustomer.customer_id.in_(customer_ids))
            .order_by(UserCustomer.customer_id, UserCustomer.user_id)
        )
        for customer_id, user_id in rows:
            result[int(customer_id)].append(int(user_id))
        return result

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

    def list_model_shortcut_preferences(self, *, user_id: int, customer_id: int):
        stmt = (
            select(UserModelShortcut, MachineModel.code)
            .join(MachineModel, MachineModel.id == UserModelShortcut.model_id)
            .where(
                UserModelShortcut.user_id == user_id,
                UserModelShortcut.customer_id == customer_id,
                MachineModel.customer_id == customer_id,
            )
            .order_by(
                UserModelShortcut.is_pinned.desc(),
                UserModelShortcut.last_queried_at.desc(),
                MachineModel.code,
            )
        )
        return list(self.db.execute(stmt))

    def get_model_shortcut_preference(
        self,
        *,
        user_id: int,
        customer_id: int,
        model_id: int,
    ) -> UserModelShortcut | None:
        stmt = select(UserModelShortcut).where(
            UserModelShortcut.user_id == user_id,
            UserModelShortcut.customer_id == customer_id,
            UserModelShortcut.model_id == model_id,
        )
        return self.db.scalar(stmt)

    def create_model_shortcut_preference(
        self,
        *,
        user_id: int,
        customer_id: int,
        model_id: int,
    ) -> UserModelShortcut:
        preference = UserModelShortcut(
            user_id=user_id,
            customer_id=customer_id,
            model_id=model_id,
            query_count=0,
            is_pinned=False,
        )
        self.db.add(preference)
        self.db.flush()
        return preference

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)

    def create_user(
        self,
        *,
        username: str,
        email: str | None,
        password_hash: str,
        display_name: str,
        role: str = "user",
        is_active: bool = True,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_user(self, user: User, *, email: str | None, display_name: str, role: str, is_active: bool) -> User:
        user.email = email
        user.display_name = display_name
        user.role = role
        user.is_active = is_active
        self.db.flush()
        return user

    def count_active_users_by_role(self, role: str) -> int:
        stmt = select(func.count()).select_from(User).where(User.role == role, User.is_active.is_(True))
        return int(self.db.scalar(stmt) or 0)
