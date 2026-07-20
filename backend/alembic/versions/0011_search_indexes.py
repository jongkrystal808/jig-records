"""add search-oriented indexes

Revision ID: 0011_search_indexes
Revises: 0010_user_email
Create Date: 2026-07-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_search_indexes"
down_revision = "0010_user_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {
        "fixture_columns": {column["name"] for column in inspector.get_columns("fixtures")},
        "fixtures": {index["name"] for index in inspector.get_indexes("fixtures")},
        "machine_models": {index["name"] for index in inspector.get_indexes("machine_models")},
        "stations": {index["name"] for index in inspector.get_indexes("stations")},
        "material_transactions": {index["name"] for index in inspector.get_indexes("material_transactions")},
    }

    if "storage_location" in existing["fixture_columns"] and "ix_fixtures_storage_location" not in existing["fixtures"]:
        op.create_index("ix_fixtures_storage_location", "fixtures", ["storage_location"], unique=False)
    if "ix_machine_models_name" not in existing["machine_models"]:
        op.create_index("ix_machine_models_name", "machine_models", ["name"], unique=False)
    if "ix_stations_name" not in existing["stations"]:
        op.create_index("ix_stations_name", "stations", ["name"], unique=False)
    if "ix_material_transactions_occurred_at" not in existing["material_transactions"]:
        op.create_index("ix_material_transactions_occurred_at", "material_transactions", ["occurred_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {
        "fixture_columns": {column["name"] for column in inspector.get_columns("fixtures")},
        "fixtures": {index["name"] for index in inspector.get_indexes("fixtures")},
        "machine_models": {index["name"] for index in inspector.get_indexes("machine_models")},
        "stations": {index["name"] for index in inspector.get_indexes("stations")},
        "material_transactions": {index["name"] for index in inspector.get_indexes("material_transactions")},
    }

    if "ix_material_transactions_occurred_at" in existing["material_transactions"]:
        op.drop_index("ix_material_transactions_occurred_at", table_name="material_transactions")
    if "ix_stations_name" in existing["stations"]:
        op.drop_index("ix_stations_name", table_name="stations")
    if "ix_machine_models_name" in existing["machine_models"]:
        op.drop_index("ix_machine_models_name", table_name="machine_models")
    if "storage_location" in existing["fixture_columns"] and "ix_fixtures_storage_location" in existing["fixtures"]:
        op.drop_index("ix_fixtures_storage_location", table_name="fixtures")
