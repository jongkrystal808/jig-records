from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import Boolean, Integer, and_, case, cast, exists, func, literal, or_, select, true, union_all
from sqlalchemy.orm import Session

from backend.app.models.inventory import (
    FixtureStockLevel,
    FixtureStockSummary,
    MaterialTransaction,
    MaterialTransactionItem,
)
from backend.app.models.master import Customer, Fixture, MachineModel, ModelStation, Station
from backend.app.models.production import FixtureRequirement, FixtureRequirementIdentifier


REPORT_FILTER_KEYS = ("keyword", "fixture_id", "model_id", "station_id", "water_status", "storage")
REPORT_SORT_COLUMNS = {
    "fixture_code",
    "fixture_name",
    "stock_qty",
    "customer_supplied_qty",
    "self_purchased_qty",
    "model_code",
    "station_code",
    "water_status",
    "configuration_status",
}


class ConfigurationReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _stock_breakdown(customer_id: int):
        signed_quantity = case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )
        return (
            select(
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransactionItem.ownership_type == "customer_supplied", signed_quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("customer_supplied_qty"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransactionItem.ownership_type == "self_purchased", signed_quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("self_purchased_qty"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(
                MaterialTransaction.customer_id == customer_id,
                MaterialTransactionItem.fixture_id.is_not(None),
            )
            .group_by(MaterialTransactionItem.fixture_id)
            .subquery()
        )

    def report_rows_subquery(self, customer_id: int):
        stock_breakdown = self._stock_breakdown(customer_id)
        signed_quantity = case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )
        designated_stock = (
            select(
                FixtureRequirementIdentifier.requirement_id.label("requirement_id"),
                func.coalesce(func.sum(signed_quantity), 0).label("stock_qty"),
            )
            .join(
                FixtureRequirement,
                FixtureRequirement.id == FixtureRequirementIdentifier.requirement_id,
            )
            .join(
                MaterialTransactionItem,
                (MaterialTransactionItem.fixture_id == FixtureRequirement.fixture_id)
                & (MaterialTransactionItem.identifier == FixtureRequirementIdentifier.identifier),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(MaterialTransaction.customer_id == customer_id)
            .group_by(FixtureRequirementIdentifier.requirement_id)
            .subquery()
        )
        stock_qty = func.coalesce(FixtureStockSummary.stock_qty, 0)
        capacity_stock_qty = case(
            (FixtureRequirement.designated_mode.is_(True), func.coalesce(designated_stock.c.stock_qty, 0)),
            else_=stock_qty,
        )
        customer_supplied_qty = func.coalesce(stock_breakdown.c.customer_supplied_qty, 0)
        self_purchased_qty = func.coalesce(stock_breakdown.c.self_purchased_qty, 0)
        min_stock_qty = func.coalesce(FixtureStockLevel.min_stock_qty, 0)
        water_status = case(
            (stock_qty <= 0, "empty"),
            (stock_qty < min_stock_qty, "low"),
            else_="normal",
        )
        max_open_station_count = cast(
            func.min(
                func.floor(
                    capacity_stock_qty / func.nullif(FixtureRequirement.required_qty, 0)
                )
            ).over(
                partition_by=(
                    FixtureRequirement.model_id,
                    FixtureRequirement.station_id,
                )
            ),
            Integer,
        )
        blank_int = cast(literal(0), Integer)
        blank_nullable_int = cast(literal(None), Integer)
        blank_nullable_bool = cast(literal(None), Boolean)
        # Keep blank text as a coercible literal. Casting it to CHAR makes MySQL
        # assign the connection collation, which can conflict with legacy table
        # columns during UNION even though every value is valid UTF-8.
        blank_text = literal("")

        configured = (
            select(
                literal("requirement").label("row_type"),
                FixtureRequirement.id.label("row_id"),
                Customer.code.label("customer_code"),
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                Fixture.is_active.label("fixture_active"),
                stock_qty.label("stock_qty"),
                customer_supplied_qty.label("customer_supplied_qty"),
                self_purchased_qty.label("self_purchased_qty"),
                min_stock_qty.label("min_stock_qty"),
                water_status.label("water_status"),
                func.coalesce(Fixture.line_storage_location, "").label("line_storage"),
                func.coalesce(Fixture.department_storage_location, "").label("department_storage"),
                MachineModel.id.label("model_id"),
                MachineModel.code.label("model_code"),
                Station.id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
                FixtureRequirement.required_qty.label("required_qty"),
                max_open_station_count.label("max_open_station_count"),
                literal("configured").label("configuration_status"),
            )
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Customer, Customer.id == Fixture.customer_id)
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .outerjoin(stock_breakdown, stock_breakdown.c.fixture_id == Fixture.id)
            .outerjoin(designated_stock, designated_stock.c.requirement_id == FixtureRequirement.id)
            .where(
                Fixture.customer_id == customer_id,
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
            )
        )

        unbound_fixtures = (
            select(
                literal("fixture").label("row_type"),
                Fixture.id.label("row_id"),
                Customer.code.label("customer_code"),
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                Fixture.is_active.label("fixture_active"),
                stock_qty.label("stock_qty"),
                customer_supplied_qty.label("customer_supplied_qty"),
                self_purchased_qty.label("self_purchased_qty"),
                min_stock_qty.label("min_stock_qty"),
                water_status.label("water_status"),
                func.coalesce(Fixture.line_storage_location, "").label("line_storage"),
                func.coalesce(Fixture.department_storage_location, "").label("department_storage"),
                blank_int.label("model_id"),
                blank_text.label("model_code"),
                blank_int.label("station_id"),
                blank_text.label("station_code"),
                blank_text.label("station_name"),
                blank_nullable_int.label("required_qty"),
                blank_nullable_int.label("max_open_station_count"),
                literal("unbound").label("configuration_status"),
            )
            .join(Customer, Customer.id == Fixture.customer_id)
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .outerjoin(stock_breakdown, stock_breakdown.c.fixture_id == Fixture.id)
            .where(
                Fixture.customer_id == customer_id,
                ~exists(select(1).where(FixtureRequirement.fixture_id == Fixture.id)),
            )
        )

        unconfigured_mappings = (
            select(
                literal("mapping").label("row_type"),
                ModelStation.id.label("row_id"),
                Customer.code.label("customer_code"),
                blank_int.label("fixture_id"),
                blank_text.label("fixture_code"),
                blank_text.label("fixture_name"),
                blank_nullable_bool.label("fixture_active"),
                blank_nullable_int.label("stock_qty"),
                blank_nullable_int.label("customer_supplied_qty"),
                blank_nullable_int.label("self_purchased_qty"),
                blank_nullable_int.label("min_stock_qty"),
                literal("na").label("water_status"),
                blank_text.label("line_storage"),
                blank_text.label("department_storage"),
                MachineModel.id.label("model_id"),
                MachineModel.code.label("model_code"),
                Station.id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
                blank_nullable_int.label("required_qty"),
                blank_nullable_int.label("max_open_station_count"),
                literal("unconfigured").label("configuration_status"),
            )
            .join(MachineModel, MachineModel.id == ModelStation.model_id)
            .join(Station, Station.id == ModelStation.station_id)
            .join(Customer, Customer.id == MachineModel.customer_id)
            .where(
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
                ~exists(
                    select(1).where(
                        FixtureRequirement.model_id == ModelStation.model_id,
                        FixtureRequirement.station_id == ModelStation.station_id,
                    )
                ),
            )
        )

        unmapped_models = (
            select(
                literal("model").label("row_type"),
                MachineModel.id.label("row_id"),
                Customer.code.label("customer_code"),
                blank_int.label("fixture_id"),
                blank_text.label("fixture_code"),
                blank_text.label("fixture_name"),
                blank_nullable_bool.label("fixture_active"),
                blank_nullable_int.label("stock_qty"),
                blank_nullable_int.label("customer_supplied_qty"),
                blank_nullable_int.label("self_purchased_qty"),
                blank_nullable_int.label("min_stock_qty"),
                literal("na").label("water_status"),
                blank_text.label("line_storage"),
                blank_text.label("department_storage"),
                MachineModel.id.label("model_id"),
                MachineModel.code.label("model_code"),
                blank_int.label("station_id"),
                blank_text.label("station_code"),
                blank_text.label("station_name"),
                blank_nullable_int.label("required_qty"),
                blank_nullable_int.label("max_open_station_count"),
                literal("unconfigured").label("configuration_status"),
            )
            .join(Customer, Customer.id == MachineModel.customer_id)
            .where(
                MachineModel.customer_id == customer_id,
                ~exists(select(1).where(ModelStation.model_id == MachineModel.id)),
            )
        )

        unmapped_stations = (
            select(
                literal("station").label("row_type"),
                Station.id.label("row_id"),
                Customer.code.label("customer_code"),
                blank_int.label("fixture_id"),
                blank_text.label("fixture_code"),
                blank_text.label("fixture_name"),
                blank_nullable_bool.label("fixture_active"),
                blank_nullable_int.label("stock_qty"),
                blank_nullable_int.label("customer_supplied_qty"),
                blank_nullable_int.label("self_purchased_qty"),
                blank_nullable_int.label("min_stock_qty"),
                literal("na").label("water_status"),
                blank_text.label("line_storage"),
                blank_text.label("department_storage"),
                blank_int.label("model_id"),
                blank_text.label("model_code"),
                Station.id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
                blank_nullable_int.label("required_qty"),
                blank_nullable_int.label("max_open_station_count"),
                literal("unconfigured").label("configuration_status"),
            )
            .join(Customer, Customer.id == Station.customer_id)
            .where(
                Station.customer_id == customer_id,
                ~exists(select(1).where(ModelStation.station_id == Station.id)),
            )
        )

        return union_all(
            configured,
            unbound_fixtures,
            unconfigured_mappings,
            unmapped_models,
            unmapped_stations,
        ).subquery("configuration_report_rows")

    @staticmethod
    def _transaction_conditions(
        *,
        transaction_type: str | list[str] | None,
        ownership_type: str | list[str] | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list:
        conditions = []
        if transaction_type:
            values = [transaction_type] if isinstance(transaction_type, str) else transaction_type
            conditions.append(MaterialTransaction.transaction_type.in_(values))
        if ownership_type:
            values = [ownership_type] if isinstance(ownership_type, str) else ownership_type
            conditions.append(MaterialTransactionItem.ownership_type.in_(values))
        if date_from:
            conditions.append(MaterialTransaction.occurred_at >= date_from)
        if date_to:
            conditions.append(MaterialTransaction.occurred_at <= date_to)
        return conditions

    def apply_filters(
        self,
        stmt,
        rows,
        *,
        filters: dict,
        enabled_keys: Iterable[str] | None = None,
    ):
        enabled = set(REPORT_FILTER_KEYS if enabled_keys is None else enabled_keys)
        fixture_status_value = filters.get("fixture_status") or ["active"]
        fixture_statuses = {fixture_status_value} if isinstance(fixture_status_value, str) else set(fixture_status_value)
        if fixture_statuses == {"active"}:
            # Rows without a fixture represent configuration gaps. Keep them in
            # the default view so the active-fixture baseline does not hide
            # missing model/station configuration.
            stmt = stmt.where(
                or_(rows.c.fixture_id <= 0, rows.c.fixture_active.is_(True))
            )
        elif fixture_statuses == {"inactive"}:
            stmt = stmt.where(
                rows.c.fixture_id > 0,
                rows.c.fixture_active.is_(False),
            )
        keyword = str(filters.get("keyword") or "").strip().lower()
        if "keyword" in enabled and keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    func.lower(rows.c.customer_code).like(pattern),
                    func.lower(rows.c.fixture_code).like(pattern),
                    func.lower(rows.c.fixture_name).like(pattern),
                    func.lower(rows.c.model_code).like(pattern),
                    func.lower(rows.c.station_code).like(pattern),
                    func.lower(rows.c.station_name).like(pattern),
                    func.lower(rows.c.line_storage).like(pattern),
                    func.lower(rows.c.department_storage).like(pattern),
                )
            )
        for key, column_name in (
            ("fixture_id", "fixture_id"),
            ("model_id", "model_id"),
            ("station_id", "station_id"),
        ):
            value = filters.get(key)
            if key in enabled and value:
                stmt = stmt.where(getattr(rows.c, column_name) == int(value))
        water_status = filters.get("water_status")
        if "water_status" in enabled and water_status:
            water_values = [water_status] if isinstance(water_status, str) else list(water_status)
            expanded_water_values = set(water_values)
            if "attention" in expanded_water_values:
                expanded_water_values.remove("attention")
                expanded_water_values.update(("low", "empty"))
            stmt = stmt.where(rows.c.water_status.in_(expanded_water_values))
        storage = str(filters.get("storage") or "").strip().lower()
        if "storage" in enabled and storage:
            pattern = f"%{storage}%"
            stmt = stmt.where(
                or_(
                    func.lower(rows.c.line_storage).like(pattern),
                    func.lower(rows.c.department_storage).like(pattern),
                )
            )
        configuration_status = filters.get("configuration_status")
        if configuration_status:
            values = [configuration_status] if isinstance(configuration_status, str) else configuration_status
            stmt = stmt.where(rows.c.configuration_status.in_(values))

        transaction_type = filters.get("transaction_type")
        ownership_type = filters.get("ownership_type")
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        if transaction_type or ownership_type or date_from or date_to:
            transaction_exists = exists(
                select(1)
                .select_from(MaterialTransactionItem)
                .join(
                    MaterialTransaction,
                    MaterialTransaction.id == MaterialTransactionItem.transaction_id,
                )
                .where(
                    MaterialTransactionItem.fixture_id == rows.c.fixture_id,
                    *self._transaction_conditions(
                        transaction_type=transaction_type,
                        ownership_type=ownership_type,
                        date_from=date_from,
                        date_to=date_to,
                    ),
                )
            )
            stmt = stmt.where(rows.c.fixture_id > 0, transaction_exists)
        return stmt

    def list_rows(
        self,
        *,
        customer_id: int,
        filters: dict,
        page: int | None,
        page_size: int | None,
        sort_by: str,
        sort_direction: str,
        include_total: bool = True,
    ) -> tuple[list[dict], int | None]:
        rows = self.report_rows_subquery(customer_id)
        filtered = self.apply_filters(select(rows), rows, filters=filters)
        total = (
            int(self.db.scalar(select(func.count()).select_from(filtered.order_by(None).subquery())) or 0)
            if include_total
            else None
        )

        sort_key = sort_by if sort_by in REPORT_SORT_COLUMNS else "fixture_code"
        sort_column = getattr(rows.c, sort_key)
        direction = sort_column.desc() if sort_direction == "desc" else sort_column.asc()
        string_sort_keys = {
            "fixture_code",
            "fixture_name",
            "model_code",
            "station_code",
            "water_status",
            "configuration_status",
        }
        blank_condition = (
            or_(sort_column.is_(None), sort_column == "")
            if sort_key in string_sort_keys
            else sort_column.is_(None)
        )
        blank_last = case((blank_condition, 1), else_=0)
        stmt = filtered.order_by(
            blank_last,
            direction,
            rows.c.fixture_code.asc(),
            rows.c.model_code.asc(),
            rows.c.station_code.asc(),
            rows.c.row_type.asc(),
            rows.c.row_id.asc(),
        )
        if page is not None and page_size is not None:
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()], total

    def summarize(self, *, customer_id: int, filters: dict) -> dict:
        rows = self.report_rows_subquery(customer_id)
        filtered = self.apply_filters(select(rows), rows, filters=filters).cte(
            "filtered_configuration_report"
        )
        has_transaction_filters = any(
            filters.get(key)
            for key in ("transaction_type", "ownership_type", "date_from", "date_to")
        )
        transaction_detail_count = literal(0)
        if has_transaction_filters:
            filtered_fixture_ids = (
                select(filtered.c.fixture_id)
                .where(filtered.c.fixture_id > 0)
                .distinct()
            )
            transaction_detail_count = (
                select(func.count())
                .select_from(MaterialTransactionItem)
                .join(
                    MaterialTransaction,
                    MaterialTransaction.id == MaterialTransactionItem.transaction_id,
                )
                .where(
                    MaterialTransactionItem.fixture_id.in_(filtered_fixture_ids),
                    *self._transaction_conditions(
                        transaction_type=filters.get("transaction_type"),
                        ownership_type=filters.get("ownership_type"),
                        date_from=filters.get("date_from"),
                        date_to=filters.get("date_to"),
                    ),
                )
                .scalar_subquery()
            )
        scalar_summary_query = (
            select(
                func.count().label("total"),
                func.count(func.distinct(case((filtered.c.fixture_id > 0, filtered.c.fixture_id)))).label(
                    "fixture_count"
                ),
                func.count(
                    func.distinct(
                        case(
                            (
                                and_(
                                    filtered.c.fixture_id > 0,
                                    filtered.c.water_status.in_(["low", "empty"]),
                                ),
                                filtered.c.fixture_id,
                            )
                        )
                    )
                ).label("attention_fixture_count"),
                func.coalesce(
                    func.sum(case((filtered.c.configuration_status == "unconfigured", 1), else_=0)),
                    0,
                ).label("missing_configuration_count"),
                func.max(case((filtered.c.fixture_code != "", 1), else_=0)).label(
                    "has_fixture_code"
                ),
                func.max(case((filtered.c.fixture_name != "", 1), else_=0)).label(
                    "has_fixture_name"
                ),
                func.max(case((filtered.c.stock_qty.is_not(None), 1), else_=0)).label(
                    "has_stock_qty"
                ),
                func.max(
                    case((filtered.c.customer_supplied_qty.is_not(None), 1), else_=0)
                ).label("has_customer_supplied_qty"),
                func.max(
                    case((filtered.c.self_purchased_qty.is_not(None), 1), else_=0)
                ).label("has_self_purchased_qty"),
                func.max(case((filtered.c.min_stock_qty.is_not(None), 1), else_=0)).label(
                    "has_min_stock_qty"
                ),
                func.max(case((filtered.c.water_status != "na", 1), else_=0)).label(
                    "has_water_status"
                ),
                func.max(case((filtered.c.line_storage != "", 1), else_=0)).label(
                    "has_line_storage"
                ),
                func.max(case((filtered.c.department_storage != "", 1), else_=0)).label(
                    "has_department_storage"
                ),
                func.max(case((filtered.c.model_code != "", 1), else_=0)).label(
                    "has_model_code"
                ),
                func.max(case((filtered.c.station_code != "", 1), else_=0)).label(
                    "has_station"
                ),
                func.max(case((filtered.c.required_qty.is_not(None), 1), else_=0)).label(
                    "has_required_qty"
                ),
                func.max(
                    case((filtered.c.max_open_station_count.is_not(None), 1), else_=0)
                ).label("has_max_open_station_count"),
                transaction_detail_count.label("transaction_detail_count"),
            )
            .select_from(filtered)
            .cte("configuration_report_scalar_summary")
        )
        fixture_totals = (
            select(
                filtered.c.fixture_id,
                func.max(filtered.c.stock_qty).label("stock_qty"),
                func.max(filtered.c.customer_supplied_qty).label("customer_supplied_qty"),
                func.max(filtered.c.self_purchased_qty).label("self_purchased_qty"),
            )
            .where(filtered.c.fixture_id > 0)
            .group_by(filtered.c.fixture_id)
            .cte("configuration_report_fixture_totals")
        )
        stock_totals_query = (
            select(
                func.coalesce(func.sum(fixture_totals.c.stock_qty), 0).label("total_stock_qty"),
                func.coalesce(func.sum(fixture_totals.c.customer_supplied_qty), 0).label(
                    "customer_supplied_qty"
                ),
                func.coalesce(func.sum(fixture_totals.c.self_purchased_qty), 0).label(
                    "self_purchased_qty"
                ),
            )
            .select_from(fixture_totals)
            .cte("configuration_report_stock_totals")
        )
        scalar_summary = self.db.execute(
            select(*scalar_summary_query.c, *stock_totals_query.c).select_from(
                scalar_summary_query.join(stock_totals_query, true())
            )
        ).one()
        populated_columns = ["index", "customer", "configurationStatus"]
        populated_column_flags = [
            ("fixtureCode", scalar_summary.has_fixture_code),
            ("fixtureName", scalar_summary.has_fixture_name),
            ("stockQty", scalar_summary.has_stock_qty),
            ("customerSuppliedQty", scalar_summary.has_customer_supplied_qty),
            ("selfPurchasedQty", scalar_summary.has_self_purchased_qty),
            ("minStockQty", scalar_summary.has_min_stock_qty),
            ("waterStatus", scalar_summary.has_water_status),
            ("lineStorage", scalar_summary.has_line_storage),
            ("departmentStorage", scalar_summary.has_department_storage),
            ("modelCode", scalar_summary.has_model_code),
            ("station", scalar_summary.has_station),
            ("requiredQty", scalar_summary.has_required_qty),
            ("maxOpenStationCount", scalar_summary.has_max_open_station_count),
        ]
        populated_columns.extend(
            key for key, is_populated in populated_column_flags if bool(is_populated)
        )
        return {
            "total": int(scalar_summary.total or 0),
            "fixture_count": int(scalar_summary.fixture_count or 0),
            "attention_fixture_count": int(scalar_summary.attention_fixture_count or 0),
            "missing_configuration_count": int(scalar_summary.missing_configuration_count or 0),
            "total_stock_qty": int(scalar_summary.total_stock_qty or 0),
            "customer_supplied_qty": int(scalar_summary.customer_supplied_qty or 0),
            "self_purchased_qty": int(scalar_summary.self_purchased_qty or 0),
            "populated_columns": populated_columns if scalar_summary.total else [],
            "transaction_detail_count": int(scalar_summary.transaction_detail_count or 0),
        }

    def list_options(
        self,
        *,
        customer_id: int,
        filters: dict,
        priority: list[str],
    ) -> dict:
        report_rows = self.report_rows_subquery(customer_id)
        rows = select(report_rows).cte("configuration_report_option_rows")
        active_order = [key for key in priority if key in REPORT_FILTER_KEYS and filters.get(key)]
        active_order.extend(
            key for key in REPORT_FILTER_KEYS if filters.get(key) and key not in active_order
        )

        def enabled_before(target: str) -> list[str]:
            if target in active_order:
                return active_order[: active_order.index(target)]
            return active_order

        def option_query(target: str, id_column, code_column, name_column):
            return self.apply_filters(
                select(
                    literal(target).label("option_type"),
                    id_column.label("option_id"),
                    code_column.label("option_code"),
                    name_column.label("option_name"),
                ).distinct(),
                rows,
                filters=filters,
                enabled_keys=enabled_before(target),
            )

        water_query = self.apply_filters(
            select(
                literal("water_status").label("option_type"),
                literal(0).label("option_id"),
                rows.c.water_status.label("option_code"),
                rows.c.water_status.label("option_name"),
            ).distinct(),
            rows,
            filters=filters,
            enabled_keys=enabled_before("water_status"),
        )
        combined_options = union_all(
            option_query(
                "fixture_id",
                rows.c.fixture_id,
                rows.c.fixture_code,
                rows.c.fixture_name,
            ),
            option_query(
                "model_id",
                rows.c.model_id,
                rows.c.model_code,
                rows.c.model_code,
            ),
            option_query(
                "station_id",
                rows.c.station_id,
                rows.c.station_code,
                rows.c.station_name,
            ),
            water_query,
        ).subquery()
        option_rows = self.db.execute(
            select(combined_options).order_by(
                combined_options.c.option_type,
                combined_options.c.option_code,
            )
        ).all()
        grouped_options: dict[str, list] = {
            "fixture_id": [],
            "model_id": [],
            "station_id": [],
            "water_status": [],
        }
        for row in option_rows:
            grouped_options[str(row.option_type)].append(row)
        return {
            "fixtures": [
                {"id": int(row.option_id), "code": row.option_code, "name": row.option_name}
                for row in grouped_options["fixture_id"]
                if int(row.option_id or 0) > 0
            ],
            "models": [
                {"id": int(row.option_id), "code": row.option_code, "name": row.option_name}
                for row in grouped_options["model_id"]
                if int(row.option_id or 0) > 0
            ],
            "stations": [
                {"id": int(row.option_id), "code": row.option_code, "name": row.option_name}
                for row in grouped_options["station_id"]
                if int(row.option_id or 0) > 0
            ],
            "water_statuses": sorted(
                {
                    str(row.option_code)
                    for row in grouped_options["water_status"]
                    if str(row.option_code) != "na"
                }
            ),
        }

    def list_transaction_details(
        self,
        *,
        fixture_ids: list[int],
        filters: dict,
    ) -> list[dict]:
        if not fixture_ids:
            return []
        stmt = (
            select(
                MaterialTransaction.id.label("id"),
                MaterialTransaction.transaction_type.label("transaction_type"),
                MaterialTransaction.transaction_no.label("transaction_no"),
                MaterialTransaction.occurred_at.label("occurred_at"),
                MaterialTransaction.actor_user_id.label("actor_user_id"),
                MaterialTransaction.created_by.label("created_by"),
                MaterialTransactionItem.fixture_id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                MaterialTransactionItem.ownership_type.label("ownership_type"),
                MaterialTransactionItem.identifier.label("identifier"),
                MaterialTransactionItem.quantity.label("quantity"),
                MaterialTransactionItem.note.label("note"),
            )
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .join(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .where(
                MaterialTransactionItem.fixture_id.in_(fixture_ids),
                *self._transaction_conditions(
                    transaction_type=filters.get("transaction_type"),
                    ownership_type=filters.get("ownership_type"),
                    date_from=filters.get("date_from"),
                    date_to=filters.get("date_to"),
                ),
            )
            .order_by(MaterialTransaction.occurred_at.desc(), MaterialTransaction.id.desc())
        )
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def count_transaction_details_for_filtered_fixtures(
        self,
        *,
        customer_id: int,
        filters: dict,
    ) -> int:
        if not any(
            filters.get(key)
            for key in ("transaction_type", "ownership_type", "date_from", "date_to")
        ):
            return 0
        rows = self.report_rows_subquery(customer_id)
        filtered_fixture_ids = (
            self.apply_filters(
                select(rows.c.fixture_id).distinct(),
                rows,
                filters=filters,
            )
            .where(rows.c.fixture_id > 0)
            .subquery()
        )
        stmt = (
            select(func.count())
            .select_from(MaterialTransactionItem)
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(
                MaterialTransactionItem.fixture_id.in_(select(filtered_fixture_ids.c.fixture_id)),
                *self._transaction_conditions(
                    transaction_type=filters.get("transaction_type"),
                    ownership_type=filters.get("ownership_type"),
                    date_from=filters.get("date_from"),
                    date_to=filters.get("date_to"),
                ),
            )
        )
        return int(self.db.scalar(stmt) or 0)
