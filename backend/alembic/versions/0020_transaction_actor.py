"""bind inventory transactions to authenticated users

Revision ID: 0020_transaction_actor
Revises: 0019_fixture_storage
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_transaction_actor"
down_revision = "0019_fixture_storage"
branch_labels = None
depends_on = None


FK_NAME = "fk_material_transactions_actor_user_id_users"
INDEX_NAME = "ix_material_transactions_actor_user_id"
NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def _actor_foreign_key(inspector: sa.Inspector) -> dict | None:
    for foreign_key in inspector.get_foreign_keys("material_transactions"):
        if foreign_key.get("constrained_columns") == ["actor_user_id"]:
            return foreign_key
    return None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "material_transactions" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("material_transactions")}
    actor_foreign_key = _actor_foreign_key(inspector)
    if "actor_user_id" not in columns or actor_foreign_key is None:
        with op.batch_alter_table(
            "material_transactions",
            naming_convention=NAMING_CONVENTION,
        ) as batch_op:
            if "actor_user_id" not in columns:
                batch_op.add_column(sa.Column("actor_user_id", sa.Integer(), nullable=True))
            if actor_foreign_key is None:
                batch_op.create_foreign_key(
                    FK_NAME,
                    "users",
                    ["actor_user_id"],
                    ["id"],
                    ondelete="RESTRICT",
                )

    # Legacy created_by values were free text. Only bind them when exactly one
    # user matches, so historical rows are never attributed speculatively.
    bind.execute(
        sa.text(
            """
            UPDATE material_transactions
            SET actor_user_id = (
                SELECT CASE WHEN COUNT(*) = 1 THEN MIN(users.id) ELSE NULL END
                FROM users
                WHERE users.username = material_transactions.created_by
                   OR users.display_name = material_transactions.created_by
            )
            WHERE actor_user_id IS NULL
            """
        )
    )

    index_names = {index["name"] for index in sa.inspect(bind).get_indexes("material_transactions")}
    if INDEX_NAME not in index_names:
        op.create_index(INDEX_NAME, "material_transactions", ["actor_user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "material_transactions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("material_transactions")}
    if "actor_user_id" not in columns:
        return

    index_names = {index["name"] for index in inspector.get_indexes("material_transactions")}
    if INDEX_NAME in index_names:
        op.drop_index(INDEX_NAME, table_name="material_transactions")

    actor_foreign_key = _actor_foreign_key(sa.inspect(bind))
    with op.batch_alter_table(
        "material_transactions",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        if actor_foreign_key is not None:
            batch_op.drop_constraint(actor_foreign_key.get("name") or FK_NAME, type_="foreignkey")
        batch_op.drop_column("actor_user_id")
