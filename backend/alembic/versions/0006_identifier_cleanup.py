"""move inventory items to identifier and drop legacy manage columns

Revision ID: 0006_identifier_cleanup
Revises: 0005_remove_warehouse_tables
Create Date: 2026-06-15 01:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_identifier_cleanup"
down_revision = "0005_remove_warehouse_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())

    if "material_transaction_items" in table_names:
        item_columns = {column["name"] for column in inspector.get_columns("material_transaction_items")}
        if "identifier" not in item_columns:
            with op.batch_alter_table("material_transaction_items") as batch_op:
                batch_op.add_column(sa.Column("identifier", sa.String(length=120), nullable=True))

        refreshed_columns = {column["name"] for column in sa.inspect(connection).get_columns("material_transaction_items")}
        if "identifier" in refreshed_columns:
            if "datecode" in refreshed_columns:
                connection.execute(
                    sa.text(
                        "UPDATE material_transaction_items "
                        "SET identifier = datecode "
                        "WHERE identifier IS NULL AND datecode IS NOT NULL"
                    )
                )
            if "serial_number" in refreshed_columns:
                connection.execute(
                    sa.text(
                        "UPDATE material_transaction_items "
                        "SET identifier = serial_number "
                        "WHERE identifier IS NULL AND serial_number IS NOT NULL"
                    )
                )
            try:
                connection.execute(
                    sa.text("CREATE INDEX ix_material_transaction_items_identifier ON material_transaction_items(identifier)")
                )
            except Exception:
                pass

        refreshed_columns = {column["name"] for column in sa.inspect(connection).get_columns("material_transaction_items")}
        with op.batch_alter_table("material_transaction_items") as batch_op:
            for column_name in ("manage_type", "datecode", "serial_number"):
                if column_name in refreshed_columns:
                    batch_op.drop_column(column_name)

    if "fixtures" in table_names:
        fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
        if "manage_type" in fixture_columns:
            with op.batch_alter_table("fixtures") as batch_op:
                batch_op.drop_column("manage_type")

    if "fixture_serials" in table_names:
        op.drop_table("fixture_serials")


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())

    if "fixtures" in table_names:
        fixture_columns = {column["name"] for column in inspector.get_columns("fixtures")}
        if "manage_type" not in fixture_columns:
            with op.batch_alter_table("fixtures") as batch_op:
                batch_op.add_column(sa.Column("manage_type", sa.String(length=32), nullable=False, server_default="datecode"))

    if "material_transaction_items" in table_names:
        item_columns = {column["name"] for column in inspector.get_columns("material_transaction_items")}
        with op.batch_alter_table("material_transaction_items") as batch_op:
            if "manage_type" not in item_columns:
                batch_op.add_column(sa.Column("manage_type", sa.String(length=32), nullable=False, server_default="datecode"))
            if "datecode" not in item_columns:
                batch_op.add_column(sa.Column("datecode", sa.String(length=80), nullable=True))
            if "serial_number" not in item_columns:
                batch_op.add_column(sa.Column("serial_number", sa.String(length=120), nullable=True))
        connection.execute(
            sa.text(
                "UPDATE material_transaction_items "
                "SET datecode = identifier "
                "WHERE identifier IS NOT NULL AND (datecode IS NULL OR datecode = '')"
            )
        )

        refreshed_columns = {column["name"] for column in sa.inspect(connection).get_columns("material_transaction_items")}
        if "identifier" in refreshed_columns:
            with op.batch_alter_table("material_transaction_items") as batch_op:
                batch_op.drop_column("identifier")

    op.create_table(
        "fixture_serials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("serial_no", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("fixture_id", "serial_no", name="uq_fixture_serial"),
    )
    op.create_index("ix_fixture_serials_serial_no", "fixture_serials", ["serial_no"], unique=False)
