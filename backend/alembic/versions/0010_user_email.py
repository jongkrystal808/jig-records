"""add email column to users

Revision ID: 0010_user_email
Revises: 0009_remove_owners_and_scope_fixture_code
Create Date: 2026-07-02 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010_user_email"
down_revision = "0009_remove_owners_and_scope_fixture_code"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "users" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" in columns:
        return
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "users" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" not in columns:
        return
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("email")
