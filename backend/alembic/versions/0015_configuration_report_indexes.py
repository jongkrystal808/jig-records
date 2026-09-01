"""add configuration report query indexes

Revision ID: 0015_configuration_report_indexes
Revises: 0014_fixture_deletion
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_configuration_report_indexes"
down_revision = "0014_fixture_deletion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    transaction_indexes = {
        index["name"] for index in inspector.get_indexes("material_transactions")
    }
    item_indexes = {
        index["name"] for index in inspector.get_indexes("material_transaction_items")
    }
    if "ix_material_transactions_report_filter" not in transaction_indexes:
        op.create_index(
            "ix_material_transactions_report_filter",
            "material_transactions",
            ["customer_id", "transaction_type", "occurred_at"],
            unique=False,
        )
    if "ix_material_transaction_items_report_filter" not in item_indexes:
        op.create_index(
            "ix_material_transaction_items_report_filter",
            "material_transaction_items",
            ["fixture_id", "ownership_type", "transaction_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    transaction_indexes = {
        index["name"] for index in inspector.get_indexes("material_transactions")
    }
    item_indexes = {
        index["name"] for index in inspector.get_indexes("material_transaction_items")
    }
    if "ix_material_transaction_items_report_filter" in item_indexes:
        op.drop_index(
            "ix_material_transaction_items_report_filter",
            table_name="material_transaction_items",
        )
    if "ix_material_transactions_report_filter" in transaction_indexes:
        op.drop_index(
            "ix_material_transactions_report_filter",
            table_name="material_transactions",
        )
