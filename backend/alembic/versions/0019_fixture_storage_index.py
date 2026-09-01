"""add fixture storage index and placement allocation

Revision ID: 0019_fixture_storage
Revises: 0018_designated_ids
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_fixture_storage"
down_revision = "0018_designated_ids"
branch_labels = None
depends_on = None


def _tokens(*values: str | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for raw in (value or "").replace("，", ",").split(","):
            token = raw.strip().upper()
            if token and token not in seen:
                seen.add(token)
                result.append(token)
    return result


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())
    create_containers = "storage_containers" not in existing_tables
    create_codes = "storage_codes" not in existing_tables
    create_placements = "fixture_placements" not in existing_tables

    if create_containers:
        op.create_table(
        "storage_containers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("customer_id", "name", name="uq_storage_containers_customer_name"),
        )
        op.create_index("ix_storage_containers_customer_id", "storage_containers", ["customer_id"])

    if create_codes:
        op.create_table(
        "storage_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("container_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["container_id"], ["storage_containers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("customer_id", "code", name="uq_storage_codes_customer_code"),
        )
        op.create_index("ix_storage_codes_customer_id", "storage_codes", ["customer_id"])
        op.create_index("ix_storage_codes_container_id", "storage_codes", ["container_id"])
        op.create_index("ix_storage_codes_code", "storage_codes", ["code"])

    if create_placements:
        op.create_table(
        "fixture_placements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=24), nullable=False),
        sa.Column("storage_code_id", sa.Integer(), nullable=True),
        sa.Column("model_id", sa.Integer(), nullable=True),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=24), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_fixture_placement_quantity"),
        sa.CheckConstraint(
            "(target_type = 'storage_code' AND storage_code_id IS NOT NULL AND model_id IS NULL AND station_id IS NULL) OR "
            "(target_type = 'model_station' AND storage_code_id IS NULL AND model_id IS NOT NULL AND station_id IS NOT NULL)",
            name="ck_fixture_placement_target",
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["fixtures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["storage_code_id"], ["storage_codes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["model_id"], ["machine_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("fixture_id", "storage_code_id", name="uq_fixture_placement_storage_code"),
        sa.UniqueConstraint("fixture_id", "model_id", "station_id", name="uq_fixture_placement_model_station"),
        )
        op.create_index("ix_fixture_placements_fixture_id", "fixture_placements", ["fixture_id"])
        op.create_index("ix_fixture_placements_storage_code_id", "fixture_placements", ["storage_code_id"])
        op.create_index("ix_fixture_placements_model_id", "fixture_placements", ["model_id"])
        op.create_index("ix_fixture_placements_station_id", "fixture_placements", ["station_id"])

    connection = op.get_bind()
    fixtures = connection.execute(
        sa.text(
            "SELECT id, customer_id, line_storage_location, department_storage_location FROM fixtures"
        )
    ).mappings()
    code_cache: dict[tuple[int, str], int] = {}
    for fixture in fixtures:
        station_rows = connection.execute(
            sa.text(
                "SELECT fr.model_id, fr.station_id, s.code AS station_code "
                "FROM fixture_requirements fr JOIN stations s ON s.id = fr.station_id "
                "WHERE fr.fixture_id = :fixture_id"
            ),
            {"fixture_id": fixture["id"]},
        ).mappings().all()
        station_by_code: dict[str, list[dict]] = {}
        for row in station_rows:
            station_by_code.setdefault(str(row["station_code"]).strip().upper(), []).append(row)
        for token in _tokens(fixture["line_storage_location"], fixture["department_storage_location"]):
            candidates = station_by_code.get(token, [])
            if len(candidates) == 1:
                exists = connection.execute(
                    sa.text(
                        "SELECT id FROM fixture_placements WHERE fixture_id = :fixture_id "
                        "AND model_id = :model_id AND station_id = :station_id"
                    ),
                    {
                        "fixture_id": fixture["id"],
                        "model_id": candidates[0]["model_id"],
                        "station_id": candidates[0]["station_id"],
                    },
                ).scalar_one_or_none()
                if exists is not None:
                    continue
                connection.execute(
                    sa.text(
                        "INSERT INTO fixture_placements "
                        "(fixture_id, target_type, model_id, station_id, quantity, source) "
                        "VALUES (:fixture_id, 'model_station', :model_id, :station_id, NULL, 'fixture_field')"
                    ),
                    {
                        "fixture_id": fixture["id"],
                        "model_id": candidates[0]["model_id"],
                        "station_id": candidates[0]["station_id"],
                    },
                )
                continue
            cache_key = (int(fixture["customer_id"]), token)
            code_id = code_cache.get(cache_key)
            if code_id is None:
                code_id = connection.execute(
                    sa.text(
                        "SELECT id FROM storage_codes WHERE customer_id = :customer_id AND code = :code"
                    ),
                    {"customer_id": fixture["customer_id"], "code": token},
                ).scalar_one_or_none()
            if code_id is None:
                result = connection.execute(
                    sa.text(
                        "INSERT INTO storage_codes (customer_id, code, is_active) "
                        "VALUES (:customer_id, :code, 1)"
                    ),
                    {"customer_id": fixture["customer_id"], "code": token},
                )
                code_id = int(result.lastrowid)
            code_cache[cache_key] = int(code_id)
            exists = connection.execute(
                sa.text(
                    "SELECT id FROM fixture_placements WHERE fixture_id = :fixture_id "
                    "AND storage_code_id = :storage_code_id"
                ),
                {"fixture_id": fixture["id"], "storage_code_id": code_id},
            ).scalar_one_or_none()
            if exists is not None:
                continue
            connection.execute(
                sa.text(
                    "INSERT INTO fixture_placements "
                    "(fixture_id, target_type, storage_code_id, quantity, source) "
                    "VALUES (:fixture_id, 'storage_code', :storage_code_id, NULL, 'fixture_field')"
                ),
                {"fixture_id": fixture["id"], "storage_code_id": code_id},
            )


def downgrade() -> None:
    op.drop_index("ix_fixture_placements_station_id", table_name="fixture_placements")
    op.drop_index("ix_fixture_placements_model_id", table_name="fixture_placements")
    op.drop_index("ix_fixture_placements_storage_code_id", table_name="fixture_placements")
    op.drop_index("ix_fixture_placements_fixture_id", table_name="fixture_placements")
    op.drop_table("fixture_placements")
    op.drop_index("ix_storage_codes_code", table_name="storage_codes")
    op.drop_index("ix_storage_codes_container_id", table_name="storage_codes")
    op.drop_index("ix_storage_codes_customer_id", table_name="storage_codes")
    op.drop_table("storage_codes")
    op.drop_index("ix_storage_containers_customer_id", table_name="storage_containers")
    op.drop_table("storage_containers")
