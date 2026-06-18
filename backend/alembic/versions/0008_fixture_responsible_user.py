"""add fixture responsible user field

Revision ID: 0008_fixture_responsible_user
Revises: 0007_user_customer_scope
Create Date: 2026-06-15 05:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0008_fixture_responsible_user"
down_revision = "0007_user_customer_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "fixtures" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("fixtures")}
    if "responsible_user_id" not in columns:
        with op.batch_alter_table("fixtures") as batch_op:
            batch_op.add_column(sa.Column("responsible_user_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_fixtures_responsible_user_id_users",
                "users",
                ["responsible_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_fixtures_responsible_user_id", ["responsible_user_id"], unique=False)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "fixtures" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("fixtures")}
    if "responsible_user_id" in columns:
        with op.batch_alter_table("fixtures") as batch_op:
            batch_op.drop_index("ix_fixtures_responsible_user_id")
            batch_op.drop_constraint("fk_fixtures_responsible_user_id_users", type_="foreignkey")
            batch_op.drop_column("responsible_user_id")
