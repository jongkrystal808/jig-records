"""support hard fixture deletion with optional transaction-history retention

Revision ID: 0014_fixture_deletion
Revises: 0013_drop_fixture_storage_location
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_fixture_deletion"
down_revision = "0013_drop_fixture_storage_location"
branch_labels = None
depends_on = None


FK_NAME = "fk_material_transaction_items_fixture_id_fixtures"
NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def _fixture_foreign_key(inspector: sa.Inspector) -> dict | None:
    for foreign_key in inspector.get_foreign_keys("material_transaction_items"):
        if foreign_key.get("constrained_columns") == ["fixture_id"]:
            return foreign_key
    return None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "material_transaction_items" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("material_transaction_items")}
    with op.batch_alter_table("material_transaction_items") as batch_op:
        if "deleted_fixture_code" not in columns:
            batch_op.add_column(sa.Column("deleted_fixture_code", sa.String(length=60), nullable=True))
        if "deleted_fixture_name" not in columns:
            batch_op.add_column(sa.Column("deleted_fixture_name", sa.String(length=160), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE material_transaction_items
            SET deleted_fixture_code = COALESCE(
                    deleted_fixture_code,
                    (SELECT fixtures.code FROM fixtures WHERE fixtures.id = material_transaction_items.fixture_id)
                ),
                deleted_fixture_name = COALESCE(
                    deleted_fixture_name,
                    (SELECT fixtures.name FROM fixtures WHERE fixtures.id = material_transaction_items.fixture_id)
                )
            WHERE fixture_id IS NOT NULL
            """
        )
    )

    inspector = sa.inspect(bind)
    columns_by_name = {
        column["name"]: column for column in inspector.get_columns("material_transaction_items")
    }
    fixture_fk = _fixture_foreign_key(inspector)
    current_ondelete = str((fixture_fk or {}).get("options", {}).get("ondelete", "")).upper()
    needs_fk_update = fixture_fk is None or current_ondelete != "SET NULL"
    needs_nullable_update = not bool(columns_by_name["fixture_id"].get("nullable"))

    if needs_fk_update or needs_nullable_update:
        with op.batch_alter_table(
            "material_transaction_items",
            naming_convention=NAMING_CONVENTION,
        ) as batch_op:
            if fixture_fk is not None:
                batch_op.drop_constraint(fixture_fk.get("name") or FK_NAME, type_="foreignkey")
            if needs_nullable_update:
                batch_op.alter_column("fixture_id", existing_type=sa.Integer(), nullable=True)
            batch_op.create_foreign_key(
                FK_NAME,
                "fixtures",
                ["fixture_id"],
                ["id"],
                ondelete="SET NULL",
            )

    index_names = {index["name"] for index in sa.inspect(bind).get_indexes("material_transaction_items")}
    if "ix_material_transaction_items_deleted_fixture_code" not in index_names:
        op.create_index(
            "ix_material_transaction_items_deleted_fixture_code",
            "material_transaction_items",
            ["deleted_fixture_code"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "material_transaction_items" not in inspector.get_table_names():
        return

    bind.execute(sa.text("DELETE FROM material_transaction_items WHERE fixture_id IS NULL"))
    fixture_fk = _fixture_foreign_key(inspector)
    with op.batch_alter_table(
        "material_transaction_items",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        if fixture_fk is not None:
            batch_op.drop_constraint(fixture_fk.get("name") or FK_NAME, type_="foreignkey")
        batch_op.alter_column("fixture_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(None, "fixtures", ["fixture_id"], ["id"])
        batch_op.drop_column("deleted_fixture_name")
        batch_op.drop_column("deleted_fixture_code")
