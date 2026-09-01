"""add super admin role and promote the bootstrap account

Revision ID: 0017_super_admin_role
Revises: 0016_user_model_shortcuts
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_super_admin_role"
down_revision = "0016_user_model_shortcuts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if "users" not in set(sa.inspect(connection).get_table_names()):
        return
    connection.execute(
        sa.text("UPDATE users SET role = 'super_admin' WHERE username = 'admin' AND role = 'admin'")
    )


def downgrade() -> None:
    connection = op.get_bind()
    if "users" not in set(sa.inspect(connection).get_table_names()):
        return
    connection.execute(
        sa.text("UPDATE users SET role = 'admin' WHERE username = 'admin' AND role = 'super_admin'")
    )
