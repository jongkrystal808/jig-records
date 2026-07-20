"""drop legacy fixture storage_location column

Revision ID: 0013_drop_fixture_storage_location
Revises: 0012_split_fixture_storage_columns
Create Date: 2026-07-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_drop_fixture_storage_location"
down_revision = "0012_split_fixture_storage_columns"
branch_labels = None
depends_on = None


def _compose_storage_location(line_storage_location: str | None, department_storage_location: str | None) -> str | None:
    line = (line_storage_location or "").strip() or None
    department = (department_storage_location or "").strip() or None
    if line or department:
        return " / ".join(part for part in [line, department] if part)
    return None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
    fixture_indexes = {index["name"] for index in inspector.get_indexes("fixtures")}

    if "ix_fixtures_storage_location" in fixture_indexes:
        op.drop_index("ix_fixtures_storage_location", table_name="fixtures")

    if "storage_location" in fixture_columns:
        op.drop_column("fixtures", "storage_location")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
    fixture_indexes = {index["name"] for index in inspector.get_indexes("fixtures")}

    if "storage_location" not in fixture_columns:
        op.add_column("fixtures", sa.Column("storage_location", sa.String(length=120), nullable=True))

    rows = bind.execute(
        sa.text(
            """
            SELECT id, line_storage_location, department_storage_location
            FROM fixtures
            """
        )
    ).mappings()
    for row in rows:
        storage_location = _compose_storage_location(row["line_storage_location"], row["department_storage_location"])
        bind.execute(
            sa.text(
                """
                UPDATE fixtures
                SET storage_location = :storage_location
                WHERE id = :fixture_id
                """
            ),
            {
                "fixture_id": row["id"],
                "storage_location": storage_location,
            },
        )

    if "ix_fixtures_storage_location" not in fixture_indexes:
        op.create_index("ix_fixtures_storage_location", "fixtures", ["storage_location"], unique=False)
