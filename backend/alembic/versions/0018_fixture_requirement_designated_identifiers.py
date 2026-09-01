"""add designated identifiers to fixture requirements

Revision ID: 0018_designated_ids
Revises: 0017_super_admin_role
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_designated_ids"
down_revision = "0017_super_admin_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    fixture_requirement_columns = {
        column["name"] for column in inspector.get_columns("fixture_requirements")
    }
    if "designated_mode" not in fixture_requirement_columns:
        op.add_column(
            "fixture_requirements",
            sa.Column("designated_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "fixture_requirement_identifiers" not in set(inspector.get_table_names()):
        op.create_table(
            "fixture_requirement_identifiers",
            sa.Column("requirement_id", sa.Integer(), nullable=False),
            sa.Column("identifier", sa.String(length=120), nullable=False),
            sa.ForeignKeyConstraint(
                ["requirement_id"],
                ["fixture_requirements.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("requirement_id", "identifier"),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "fixture_requirement_identifiers" in set(inspector.get_table_names()):
        op.drop_table("fixture_requirement_identifiers")
    fixture_requirement_columns = {
        column["name"] for column in inspector.get_columns("fixture_requirements")
    }
    if "designated_mode" in fixture_requirement_columns:
        op.drop_column("fixture_requirements", "designated_mode")
