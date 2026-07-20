"""split fixture storage location into line and department columns

Revision ID: 0012_split_fixture_storage_columns
Revises: 0011_search_indexes
Create Date: 2026-07-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_split_fixture_storage_columns"
down_revision = "0011_search_indexes"
branch_labels = None
depends_on = None


def _split_storage_location(value: str | None) -> tuple[str | None, str | None]:
    normalized = (value or "").strip()
    if not normalized:
        return None, None
    if " / " in normalized:
        left, right = normalized.split(" / ", 1)
        left = left.strip() or None
        right = right.strip() or None
        return left, right
    return normalized, None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
    fixture_indexes = {index["name"] for index in inspector.get_indexes("fixtures")}

    if "line_storage_location" not in fixture_columns:
        op.add_column("fixtures", sa.Column("line_storage_location", sa.String(length=120), nullable=True))
    if "department_storage_location" not in fixture_columns:
        op.add_column("fixtures", sa.Column("department_storage_location", sa.String(length=120), nullable=True))

    if "ix_fixtures_line_storage_location" not in fixture_indexes:
        op.create_index("ix_fixtures_line_storage_location", "fixtures", ["line_storage_location"], unique=False)
    if "ix_fixtures_department_storage_location" not in fixture_indexes:
        op.create_index("ix_fixtures_department_storage_location", "fixtures", ["department_storage_location"], unique=False)

    if "storage_location" in fixture_columns:
        rows = bind.execute(
            sa.text(
                """
                SELECT id, storage_location, line_storage_location, department_storage_location
                FROM fixtures
                """
            )
        ).mappings()
        for row in rows:
            if row["line_storage_location"] or row["department_storage_location"]:
                continue
            line_storage_location, department_storage_location = _split_storage_location(row["storage_location"])
            if line_storage_location is None and department_storage_location is None:
                continue
            bind.execute(
                sa.text(
                    """
                    UPDATE fixtures
                    SET line_storage_location = :line_storage_location,
                        department_storage_location = :department_storage_location
                    WHERE id = :fixture_id
                    """
                ),
                {
                    "fixture_id": row["id"],
                    "line_storage_location": line_storage_location,
                    "department_storage_location": department_storage_location,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
    fixture_indexes = {index["name"] for index in inspector.get_indexes("fixtures")}

    if "ix_fixtures_department_storage_location" in fixture_indexes:
        op.drop_index("ix_fixtures_department_storage_location", table_name="fixtures")
    if "ix_fixtures_line_storage_location" in fixture_indexes:
        op.drop_index("ix_fixtures_line_storage_location", table_name="fixtures")

    if "department_storage_location" in fixture_columns:
        op.drop_column("fixtures", "department_storage_location")
    if "line_storage_location" in fixture_columns:
        op.drop_column("fixtures", "line_storage_location")
