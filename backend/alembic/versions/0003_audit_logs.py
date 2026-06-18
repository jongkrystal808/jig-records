"""add audit logs

Revision ID: 0003_audit_logs
Revises: 0002_schema_backfill
Create Date: 2026-06-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_audit_logs"
down_revision = "0002_schema_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())

    if "audit_logs" not in table_names:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("entity_type", sa.String(length=40), nullable=False),
            sa.Column("entity_key", sa.String(length=120), nullable=False),
            sa.Column("action", sa.String(length=24), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("actor_username", sa.String(length=80), nullable=False),
            sa.Column("actor_display_name", sa.String(length=120), nullable=False),
            sa.Column("actor_role", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )

    index_names = {index.get("name") for index in sa.inspect(connection).get_indexes("audit_logs")}
    if "ix_audit_logs_customer_id" not in index_names:
        op.create_index("ix_audit_logs_customer_id", "audit_logs", ["customer_id"], unique=False)
    if "ix_audit_logs_entity_type" not in index_names:
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
    if "ix_audit_logs_entity_key" not in index_names:
        op.create_index("ix_audit_logs_entity_key", "audit_logs", ["entity_key"], unique=False)
    if "ix_audit_logs_action" not in index_names:
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    if "ix_audit_logs_actor_user_id" not in index_names:
        op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_key", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_customer_id", table_name="audit_logs")
    op.drop_table("audit_logs")
