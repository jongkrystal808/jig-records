"""add per-user customer access scope

Revision ID: 0007_user_customer_scope
Revises: 0006_identifier_cleanup
Create Date: 2026-06-15 02:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_user_customer_scope"
down_revision = "0006_identifier_cleanup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    if "user_customers" not in table_names:
        op.create_table(
            "user_customers",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
            sa.PrimaryKeyConstraint("user_id", "customer_id"),
            sa.UniqueConstraint("user_id", "customer_id", name="uq_user_customers_user_customer"),
        )

    users = connection.execute(sa.text("SELECT id, role FROM users")).fetchall()
    customer_ids = [row[0] for row in connection.execute(sa.text("SELECT id FROM customers")).fetchall()]
    for user_id, role in users:
        if role == "admin":
            continue
        for customer_id in customer_ids:
            connection.execute(
                sa.text(
                    "INSERT INTO user_customers(user_id, customer_id) "
                    "SELECT :user_id, :customer_id "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM user_customers WHERE user_id = :user_id AND customer_id = :customer_id"
                    ")"
                ),
                {"user_id": user_id, "customer_id": customer_id},
            )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "user_customers" in set(inspector.get_table_names()):
        op.drop_table("user_customers")
