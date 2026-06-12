"""schema backfill for legacy databases

Revision ID: 0002_schema_backfill
Revises: 0001_initial
Create Date: 2026-06-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

from backend.app.core.schema_patch import run_schema_patches

# revision identifiers, used by Alembic.
revision = "0002_schema_backfill"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_schema_patches(op.get_bind())


def downgrade() -> None:
    # Legacy backfill is intentionally not reversed.
    pass
