"""scope fixture requirements by model and station

Revision ID: 0004_model_station_scope
Revises: 0003_audit_logs
Create Date: 2026-06-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_model_station_scope"
down_revision = "0003_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    if "fixture_requirements" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("fixture_requirements")}
    if "model_id" not in columns:
        with op.batch_alter_table("fixture_requirements") as batch_op:
            batch_op.add_column(sa.Column("model_id", sa.Integer(), nullable=True))

    connection.execute(
        sa.text(
            """
            UPDATE fixture_requirements
            SET model_id = (
                SELECT MIN(model_stations.model_id)
                FROM model_stations
                WHERE model_stations.station_id = fixture_requirements.station_id
            )
            WHERE model_id IS NULL
            """
        )
    )

    refreshed_columns = {column["name"] for column in sa.inspect(connection).get_columns("fixture_requirements")}
    if "model_id" not in refreshed_columns:
        return

    unique_names = {constraint.get("name") for constraint in inspector.get_unique_constraints("fixture_requirements")}
    index_names = {index.get("name") for index in inspector.get_indexes("fixture_requirements")}

    with op.batch_alter_table("fixture_requirements") as batch_op:
        if "uq_station_fixture_requirement" in unique_names:
            batch_op.drop_constraint("uq_station_fixture_requirement", type_="unique")
        if "uq_model_station_fixture_requirement" not in unique_names:
            batch_op.create_unique_constraint(
                "uq_model_station_fixture_requirement",
                ["model_id", "station_id", "fixture_id"],
            )
        if "ix_fixture_requirements_model_id" not in index_names:
            batch_op.create_index("ix_fixture_requirements_model_id", ["model_id"], unique=False)
        if not any(fk.get("constrained_columns") == ["model_id"] for fk in inspector.get_foreign_keys("fixture_requirements")):
            batch_op.create_foreign_key(
                "fk_fixture_requirements_model_id_machine_models",
                "machine_models",
                ["model_id"],
                ["id"],
                ondelete="CASCADE",
            )
        batch_op.alter_column("model_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())
    if "fixture_requirements" not in table_names:
        return

    unique_names = {constraint.get("name") for constraint in inspector.get_unique_constraints("fixture_requirements")}
    index_names = {index.get("name") for index in inspector.get_indexes("fixture_requirements")}
    fk_names = {fk.get("name") for fk in inspector.get_foreign_keys("fixture_requirements")}
    columns = {column["name"] for column in inspector.get_columns("fixture_requirements")}

    with op.batch_alter_table("fixture_requirements") as batch_op:
        if "uq_model_station_fixture_requirement" in unique_names:
            batch_op.drop_constraint("uq_model_station_fixture_requirement", type_="unique")
        if "uq_station_fixture_requirement" not in unique_names:
            batch_op.create_unique_constraint("uq_station_fixture_requirement", ["station_id", "fixture_id"])
        if "fk_fixture_requirements_model_id_machine_models" in fk_names:
            batch_op.drop_constraint("fk_fixture_requirements_model_id_machine_models", type_="foreignkey")
        if "ix_fixture_requirements_model_id" in index_names:
            batch_op.drop_index("ix_fixture_requirements_model_id")
        if "model_id" in columns:
            batch_op.drop_column("model_id")
