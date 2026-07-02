from datetime import datetime

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    inspector = inspect(connection)
    if table_name not in inspector.get_table_names():
        return False
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    return column_name in columns


def _add_column_if_missing(connection: Connection, table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(connection)
    if table_name not in inspector.get_table_names():
        return
    if _column_exists(connection, table_name, column_name):
        return
    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def _drop_object_if_exists(connection: Connection, table_name: str, object_name: str, *, is_constraint: bool = False) -> None:
    dialect = connection.dialect.name
    try:
        if dialect == "sqlite":
            connection.execute(text(f"DROP INDEX {object_name}"))
        elif dialect in {"mysql", "mariadb"}:
            connection.execute(text(f"ALTER TABLE {table_name} DROP INDEX {object_name}"))
        elif dialect == "postgresql":
            if is_constraint:
                connection.execute(text(f'ALTER TABLE {table_name} DROP CONSTRAINT "{object_name}"'))
            else:
                connection.execute(text(f'DROP INDEX IF EXISTS "{object_name}"'))
        else:
            connection.execute(text(f"DROP INDEX {object_name}"))
    except Exception:
        pass


def _replace_single_code_unique_with_customer_code_unique(connection: Connection, table_name: str, constraint_name: str) -> None:
    inspector = inspect(connection)
    unique_constraints = inspector.get_unique_constraints(table_name) if table_name in inspector.get_table_names() else []
    unique_indexes = inspector.get_indexes(table_name) if table_name in inspector.get_table_names() else []

    for constraint in unique_constraints:
        columns = constraint.get("column_names") or []
        if columns == ["code"] and constraint.get("name"):
            _drop_object_if_exists(connection, table_name, constraint["name"], is_constraint=True)

    for index in unique_indexes:
        columns = index.get("column_names") or []
        if columns == ["code"] and index.get("unique") and index.get("name"):
            _drop_object_if_exists(connection, table_name, index["name"], is_constraint=False)

    try:
        connection.execute(text(f"CREATE UNIQUE INDEX {constraint_name} ON {table_name}(customer_id, code)"))
    except Exception:
        pass


def _ensure_default_customer_id(connection: Connection) -> int:
    row = connection.execute(text("SELECT id FROM customers ORDER BY id ASC LIMIT 1")).first()
    if row is not None:
        return int(row[0])
    connection.execute(
        text(
            "INSERT INTO customers(code, name, created_at, updated_at) VALUES ('DEFAULT', 'Default Customer', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    row = connection.execute(text("SELECT id FROM customers WHERE code='DEFAULT' LIMIT 1")).first()
    if row is None:
        raise RuntimeError("failed to bootstrap default customer")
    return int(row[0])


def _patch_fixture_customer(connection: Connection) -> None:
    if _column_exists(connection, "fixtures", "customer_id"):
        return
    default_customer_id = _ensure_default_customer_id(connection)
    connection.execute(text("ALTER TABLE fixtures ADD COLUMN customer_id INTEGER NULL"))
    connection.execute(text("UPDATE fixtures SET customer_id = :cid WHERE customer_id IS NULL"), {"cid": default_customer_id})
    # MySQL mode
    try:
        connection.execute(text("ALTER TABLE fixtures MODIFY COLUMN customer_id INTEGER NOT NULL"))
    except Exception:
        pass
    try:
        connection.execute(text("CREATE INDEX ix_fixtures_customer_id ON fixtures(customer_id)"))
    except Exception:
        pass


def _ensure_default_customer(connection: Connection) -> None:
    _ensure_default_customer_id(connection)


def _patch_fixture_master(connection: Connection) -> None:
    _add_column_if_missing(connection, "fixtures", "line_storage_location", "VARCHAR(120) NULL")
    _add_column_if_missing(connection, "fixtures", "department_storage_location", "VARCHAR(120) NULL")
    _add_column_if_missing(connection, "fixtures", "storage_location", "VARCHAR(120) NULL")
    _replace_single_code_unique_with_customer_code_unique(connection, "fixtures", "uq_fixtures_customer_code")


def _patch_machine_models(connection: Connection) -> None:
    default_customer_id = _ensure_default_customer_id(connection)
    _add_column_if_missing(connection, "machine_models", "customer_id", "INTEGER NULL")
    if _column_exists(connection, "machine_models", "customer_id"):
        connection.execute(
            text("UPDATE machine_models SET customer_id = :cid WHERE customer_id IS NULL"),
            {"cid": default_customer_id},
        )
        try:
            connection.execute(text("ALTER TABLE machine_models MODIFY COLUMN customer_id INTEGER NOT NULL"))
        except Exception:
            pass
        try:
            connection.execute(text("CREATE INDEX ix_machine_models_customer_id ON machine_models(customer_id)"))
        except Exception:
            pass
    _replace_single_code_unique_with_customer_code_unique(connection, "machine_models", "uq_machine_models_customer_code")


def _patch_stations(connection: Connection) -> None:
    default_customer_id = _ensure_default_customer_id(connection)
    _add_column_if_missing(connection, "stations", "customer_id", "INTEGER NULL")
    if _column_exists(connection, "stations", "customer_id"):
        connection.execute(text("UPDATE stations SET customer_id = :cid WHERE customer_id IS NULL"), {"cid": default_customer_id})
        try:
            connection.execute(text("ALTER TABLE stations MODIFY COLUMN customer_id INTEGER NOT NULL"))
        except Exception:
            pass
        try:
            connection.execute(text("CREATE INDEX ix_stations_customer_id ON stations(customer_id)"))
        except Exception:
            pass
    _replace_single_code_unique_with_customer_code_unique(connection, "stations", "uq_stations_customer_code")


def _patch_material_transactions(connection: Connection) -> None:
    default_customer_id = _ensure_default_customer_id(connection)
    _add_column_if_missing(connection, "material_transactions", "customer_id", "INTEGER NULL")
    _add_column_if_missing(connection, "material_transactions", "transaction_no", "VARCHAR(64) NULL")
    _add_column_if_missing(connection, "material_transactions", "occurred_at", "DATETIME NULL")
    _add_column_if_missing(connection, "material_transactions", "created_by", "VARCHAR(120) NULL")

    if _column_exists(connection, "material_transactions", "customer_id"):
        if connection.dialect.name == "sqlite":
            rows = connection.execute(
                text(
                    """
                    SELECT ti.transaction_id AS transaction_id, MIN(f.customer_id) AS customer_id
                    FROM material_transaction_items ti
                    JOIN fixtures f ON f.id = ti.fixture_id
                    GROUP BY ti.transaction_id
                    """
                )
            ).all()
            for row in rows:
                if row.customer_id is None:
                    continue
                connection.execute(
                    text("UPDATE material_transactions SET customer_id = :customer_id WHERE id = :id AND customer_id IS NULL"),
                    {"customer_id": int(row.customer_id), "id": int(row.transaction_id)},
                )
        else:
            connection.execute(
                text(
                    """
                    UPDATE material_transactions tx
                    JOIN (
                        SELECT ti.transaction_id AS transaction_id, MIN(f.customer_id) AS customer_id
                        FROM material_transaction_items ti
                        JOIN fixtures f ON f.id = ti.fixture_id
                        GROUP BY ti.transaction_id
                    ) mapped ON mapped.transaction_id = tx.id
                    SET tx.customer_id = mapped.customer_id
                    WHERE tx.customer_id IS NULL
                    """
                )
            )
        connection.execute(
            text("UPDATE material_transactions SET customer_id = :cid WHERE customer_id IS NULL"),
            {"cid": default_customer_id},
        )
        try:
            connection.execute(text("ALTER TABLE material_transactions MODIFY COLUMN customer_id INTEGER NOT NULL"))
        except Exception:
            pass

    if _column_exists(connection, "material_transactions", "occurred_at"):
        connection.execute(
            text("UPDATE material_transactions SET occurred_at = created_at WHERE occurred_at IS NULL")
        )
        try:
            connection.execute(text("ALTER TABLE material_transactions MODIFY COLUMN occurred_at DATETIME NOT NULL"))
        except Exception:
            pass

    if _column_exists(connection, "material_transactions", "created_by"):
        connection.execute(
            text("UPDATE material_transactions SET created_by = 'system' WHERE created_by IS NULL OR created_by = ''")
        )
        try:
            connection.execute(text("ALTER TABLE material_transactions MODIFY COLUMN created_by VARCHAR(120) NOT NULL"))
        except Exception:
            pass

    if _column_exists(connection, "material_transactions", "transaction_no"):
        if connection.dialect.name == "sqlite":
            rows = connection.execute(
                text(
                    "SELECT id, transaction_type, COALESCE(occurred_at, created_at) AS occurred_at FROM material_transactions WHERE transaction_no IS NULL OR transaction_no = ''"
                )
            ).all()
            for row in rows:
                occurred_at = row.occurred_at
                if isinstance(occurred_at, str):
                    occurred_dt = datetime.fromisoformat(occurred_at.replace(" ", "T"))
                elif isinstance(occurred_at, datetime):
                    occurred_dt = occurred_at
                else:
                    occurred_dt = datetime.utcnow()
                prefix = "RCV" if row.transaction_type == "receipt" else "RTN"
                transaction_no = f"{prefix}-{occurred_dt:%Y%m%d}-{int(row.id):06d}"
                connection.execute(
                    text("UPDATE material_transactions SET transaction_no = :transaction_no WHERE id = :id"),
                    {"transaction_no": transaction_no, "id": int(row.id)},
                )
        else:
            connection.execute(
                text(
                    """
                    UPDATE material_transactions
                    SET transaction_no = CONCAT(
                        CASE WHEN transaction_type = 'receipt' THEN 'RCV' ELSE 'RTN' END,
                        '-',
                        DATE_FORMAT(COALESCE(occurred_at, created_at), '%Y%m%d'),
                        '-',
                        LPAD(id, 6, '0')
                    )
                    WHERE transaction_no IS NULL OR transaction_no = ''
                    """
                )
            )
        try:
            connection.execute(text("ALTER TABLE material_transactions MODIFY COLUMN transaction_no VARCHAR(64) NOT NULL"))
        except Exception:
            pass
        try:
            connection.execute(text("CREATE UNIQUE INDEX uq_material_transactions_transaction_no ON material_transactions(transaction_no)"))
        except Exception:
            pass


def _patch_material_transaction_items(connection: Connection) -> None:
    _add_column_if_missing(
        connection,
        "material_transaction_items",
        "ownership_type",
        "VARCHAR(32) NOT NULL DEFAULT 'self_purchased'",
    )
    _add_column_if_missing(connection, "material_transaction_items", "identifier", "VARCHAR(120) NULL")
    _add_column_if_missing(connection, "material_transaction_items", "quantity", "INTEGER NULL")
    _add_column_if_missing(connection, "material_transaction_items", "note", "VARCHAR(255) NULL")

    if _column_exists(connection, "material_transaction_items", "identifier"):
        if _column_exists(connection, "material_transaction_items", "datecode"):
            connection.execute(
                text("UPDATE material_transaction_items SET identifier = datecode WHERE identifier IS NULL AND datecode IS NOT NULL")
            )
        if _column_exists(connection, "material_transaction_items", "serial_number"):
            connection.execute(
                text(
                    "UPDATE material_transaction_items SET identifier = serial_number "
                    "WHERE identifier IS NULL AND serial_number IS NOT NULL"
                )
            )

    if _column_exists(connection, "material_transaction_items", "quantity"):
        if _column_exists(connection, "material_transaction_items", "qty"):
            connection.execute(
                text("UPDATE material_transaction_items SET quantity = qty WHERE quantity IS NULL")
            )
        connection.execute(
            text("UPDATE material_transaction_items SET quantity = 1 WHERE quantity IS NULL")
        )
        try:
            connection.execute(text("ALTER TABLE material_transaction_items MODIFY COLUMN quantity INTEGER NOT NULL"))
        except Exception:
            pass

    if _column_exists(connection, "material_transaction_items", "qty"):
        try:
            connection.execute(text("UPDATE material_transaction_items SET qty = quantity WHERE qty IS NULL"))
        except Exception:
            pass
        try:
            connection.execute(text("ALTER TABLE material_transaction_items MODIFY COLUMN qty INTEGER NULL"))
        except Exception:
            pass


def _patch_fixture_requirements_model_scope(connection: Connection) -> None:
    inspector = inspect(connection)
    if "fixture_requirements" not in inspector.get_table_names():
        return

    if not _column_exists(connection, "fixture_requirements", "model_id"):
        connection.execute(text("ALTER TABLE fixture_requirements ADD COLUMN model_id INTEGER NULL"))

    if _column_exists(connection, "fixture_requirements", "model_id"):
        connection.execute(
            text(
                """
                UPDATE fixture_requirements
                SET model_id = (
                    SELECT MIN(model_stations.model_id)
                    FROM model_stations
                    WHERE model_stations.station_id = fixture_requirements.station_id
                )
                WHERE model_id IS NULL
                """
            )
        )
        try:
            connection.execute(text("CREATE INDEX ix_fixture_requirements_model_id ON fixture_requirements(model_id)"))
        except Exception:
            pass

    _drop_object_if_exists(connection, "fixture_requirements", "uq_station_fixture_requirement", is_constraint=True)
    try:
        connection.execute(
            text(
                "CREATE UNIQUE INDEX uq_model_station_fixture_requirement "
                "ON fixture_requirements(model_id, station_id, fixture_id)"
            )
        )
    except Exception:
        pass


def run_schema_patches(connection: Connection) -> None:
    # Backfill columns for environments that started before explicit migrations were added.
    _add_column_if_missing(connection, "machine_models", "is_active", "BOOLEAN NOT NULL DEFAULT 1")
    _add_column_if_missing(connection, "stations", "is_active", "BOOLEAN NOT NULL DEFAULT 1")
    _ensure_default_customer(connection)
    _patch_fixture_customer(connection)
    _patch_fixture_master(connection)
    _patch_machine_models(connection)
    _patch_stations(connection)
    _patch_material_transactions(connection)
    _patch_material_transaction_items(connection)
    _patch_fixture_requirements_model_scope(connection)
