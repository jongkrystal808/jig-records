"""add cross-device user model shortcuts

Revision ID: 0016_user_model_shortcuts
Revises: 0015_configuration_report_indexes
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_user_model_shortcuts"
down_revision = "0015_configuration_report_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "user_model_shortcuts" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "user_model_shortcuts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("query_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_queried_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["machine_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "customer_id", "model_id", name="uq_user_model_shortcut_scope"),
    )
    op.create_index("ix_user_model_shortcuts_user_id", "user_model_shortcuts", ["user_id"], unique=False)
    op.create_index("ix_user_model_shortcuts_customer_id", "user_model_shortcuts", ["customer_id"], unique=False)
    op.create_index("ix_user_model_shortcuts_model_id", "user_model_shortcuts", ["model_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if "user_model_shortcuts" not in set(sa.inspect(bind).get_table_names()):
        return
    op.drop_index("ix_user_model_shortcuts_model_id", table_name="user_model_shortcuts")
    op.drop_index("ix_user_model_shortcuts_customer_id", table_name="user_model_shortcuts")
    op.drop_index("ix_user_model_shortcuts_user_id", table_name="user_model_shortcuts")
    op.drop_table("user_model_shortcuts")
