"""invalidate user sessions after password changes

Revision ID: 0021_user_auth_version
Revises: 0020_transaction_actor
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_user_auth_version"
down_revision = "0020_transaction_actor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "auth_version" in columns:
        return
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("auth_version", sa.Integer(), server_default="1", nullable=False)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "auth_version" not in columns:
        return
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("auth_version")
