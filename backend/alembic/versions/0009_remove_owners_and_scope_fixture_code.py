"""remove owners and scope fixture code by customer

Revision ID: 0009_remove_owners_and_scope_fixture_code
Revises: 0008_fixture_responsible_user
Create Date: 2026-06-15 16:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0009_remove_owners_and_scope_fixture_code"
down_revision = "0008_fixture_responsible_user"
branch_labels = None
depends_on = None


def _drop_fixture_code_unique(batch_op, inspector: sa.Inspector) -> None:
    unique_constraints = inspector.get_unique_constraints("fixtures")
    indexes = inspector.get_indexes("fixtures")

    for constraint in unique_constraints:
        name = constraint.get("name")
        columns = constraint.get("column_names") or []
        if name and columns == ["code"]:
            try:
                batch_op.drop_constraint(name, type_="unique")
            except Exception:
                pass

    for index in indexes:
        name = index.get("name")
        columns = index.get("column_names") or []
        if name and columns == ["code"] and index.get("unique"):
            try:
                batch_op.drop_index(name)
            except Exception:
                pass


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    dialect = connection.dialect.name

    if "fixtures" in table_names:
        columns = {column["name"] for column in inspector.get_columns("fixtures")}
        foreign_keys = {fk.get("name") for fk in inspector.get_foreign_keys("fixtures") if fk.get("name")}
        indexes = {index.get("name") for index in inspector.get_indexes("fixtures") if index.get("name")}
        if dialect in {"mysql", "mariadb"}:
            if "owner_id" in columns:
                if "fk_fixtures_owner_id_owners" in foreign_keys:
                    try:
                        op.drop_constraint("fk_fixtures_owner_id_owners", "fixtures", type_="foreignkey")
                    except Exception:
                        pass
                if "ix_fixtures_owner_id" in indexes:
                    try:
                        op.drop_index("ix_fixtures_owner_id", table_name="fixtures")
                    except Exception:
                        pass
                op.drop_column("fixtures", "owner_id")

            if "ix_fixtures_code" in indexes:
                try:
                    op.drop_index("ix_fixtures_code", table_name="fixtures")
                except Exception:
                    pass
            try:
                op.create_unique_constraint("uq_fixtures_customer_code", "fixtures", ["customer_id", "code"])
            except Exception:
                pass
            try:
                op.create_index("ix_fixtures_code", "fixtures", ["code"], unique=False)
            except Exception:
                pass
        else:
            with op.batch_alter_table("fixtures") as batch_op:
                if "owner_id" in columns:
                    if "fk_fixtures_owner_id_owners" in foreign_keys:
                        try:
                            batch_op.drop_constraint("fk_fixtures_owner_id_owners", type_="foreignkey")
                        except Exception:
                            pass
                    if "ix_fixtures_owner_id" in indexes:
                        try:
                            batch_op.drop_index("ix_fixtures_owner_id")
                        except Exception:
                            pass
                    batch_op.drop_column("owner_id")

                _drop_fixture_code_unique(batch_op, inspector)

                try:
                    batch_op.create_unique_constraint("uq_fixtures_customer_code", ["customer_id", "code"])
                except Exception:
                    pass

            inspector = sa.inspect(connection)
            index_names = {index.get("name") for index in inspector.get_indexes("fixtures") if index.get("name")}
            if "ix_fixtures_code" not in index_names:
                try:
                    op.create_index("ix_fixtures_code", "fixtures", ["code"], unique=False)
                except Exception:
                    pass

    inspector = sa.inspect(connection)
    if "owners" in set(inspector.get_table_names()):
        op.drop_table("owners")


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    dialect = connection.dialect.name

    if "owners" not in table_names:
        op.create_table(
            "owners",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        )

    inspector = sa.inspect(connection)
    if "fixtures" in set(inspector.get_table_names()):
        columns = {column["name"] for column in inspector.get_columns("fixtures")}
        unique_names = {uc.get("name") for uc in inspector.get_unique_constraints("fixtures") if uc.get("name")}
        if dialect in {"mysql", "mariadb"}:
            if "uq_fixtures_customer_code" in unique_names:
                try:
                    op.drop_constraint("uq_fixtures_customer_code", "fixtures", type_="unique")
                except Exception:
                    pass
            try:
                op.drop_index("ix_fixtures_code", table_name="fixtures")
            except Exception:
                pass
            try:
                op.create_index("ix_fixtures_code", "fixtures", ["code"], unique=True)
            except Exception:
                pass
            if "owner_id" not in columns:
                op.add_column("fixtures", sa.Column("owner_id", sa.Integer(), nullable=True))
                try:
                    op.create_index("ix_fixtures_owner_id", "fixtures", ["owner_id"], unique=False)
                except Exception:
                    pass
                try:
                    op.create_foreign_key(
                        "fk_fixtures_owner_id_owners",
                        "fixtures",
                        "owners",
                        ["owner_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
                except Exception:
                    pass
        else:
            with op.batch_alter_table("fixtures") as batch_op:
                if "uq_fixtures_customer_code" in unique_names:
                    try:
                        batch_op.drop_constraint("uq_fixtures_customer_code", type_="unique")
                    except Exception:
                        pass
                if "owner_id" not in columns:
                    batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
                    try:
                        batch_op.create_index("ix_fixtures_owner_id", ["owner_id"], unique=False)
                    except Exception:
                        pass
                    try:
                        batch_op.create_foreign_key(
                            "fk_fixtures_owner_id_owners",
                            "owners",
                            ["owner_id"],
                            ["id"],
                            ondelete="SET NULL",
                        )
                    except Exception:
                        pass

            inspector = sa.inspect(connection)
            index_names = {index.get("name") for index in inspector.get_indexes("fixtures") if index.get("name")}
            if "ix_fixtures_code" in index_names:
                try:
                    op.drop_index("ix_fixtures_code", table_name="fixtures")
                except Exception:
                    pass
            try:
                op.create_index("ix_fixtures_code", "fixtures", ["code"], unique=True)
            except Exception:
                pass
