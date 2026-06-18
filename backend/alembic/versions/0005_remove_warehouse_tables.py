"""remove warehouse tables and deprecated qty column

Revision ID: 0005_remove_warehouse_tables
Revises: 0004_model_station_scope
Create Date: 2026-06-15 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_remove_warehouse_tables"
down_revision = "0004_model_station_scope"
branch_labels = None
depends_on = None


WAREHOUSE_TABLES = (
    "fixture_location_assignments",
    "fixture_images",
    "storage_locations",
    "warehouse_profiles",
)


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())

    if "material_transaction_items" in table_names:
        item_columns = {column["name"] for column in inspector.get_columns("material_transaction_items")}
        if "qty" in item_columns:
            with op.batch_alter_table("material_transaction_items") as batch_op:
                batch_op.drop_column("qty")

    for table_name in WAREHOUSE_TABLES:
        if table_name in table_names:
            op.drop_table(table_name)


def downgrade() -> None:
    op.create_table(
        "warehouse_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_table(
        "storage_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True, index=True),
        sa.Column("area", sa.String(length=8), nullable=False),
        sa.Column("rack", sa.String(length=8), nullable=False),
        sa.Column("layer", sa.String(length=8), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("image_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.create_table(
        "fixture_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("image_path", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_path", sa.String(length=255), nullable=True),
        sa.Column("is_main", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_table(
        "fixture_location_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("storage_locations.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("fixture_id", name="uq_fixture_location_one"),
    )

    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    if "material_transaction_items" in table_names:
        item_columns = {column["name"] for column in inspector.get_columns("material_transaction_items")}
        if "qty" not in item_columns:
            with op.batch_alter_table("material_transaction_items") as batch_op:
                batch_op.add_column(sa.Column("qty", sa.Integer(), nullable=True))
            connection.execute(sa.text("UPDATE material_transaction_items SET qty = quantity WHERE qty IS NULL"))
