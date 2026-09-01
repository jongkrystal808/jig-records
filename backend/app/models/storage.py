from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class StorageContainer(Base, TimestampMixin):
    __tablename__ = "storage_containers"
    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_storage_containers_customer_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class StorageCode(Base, TimestampMixin):
    __tablename__ = "storage_codes"
    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_storage_codes_customer_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    container_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_containers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FixturePlacement(Base, TimestampMixin):
    __tablename__ = "fixture_placements"
    __table_args__ = (
        UniqueConstraint("fixture_id", "storage_code_id", name="uq_fixture_placement_storage_code"),
        UniqueConstraint(
            "fixture_id", "model_id", "station_id", name="uq_fixture_placement_model_station"
        ),
        CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_fixture_placement_quantity"),
        CheckConstraint(
            "(target_type = 'storage_code' AND storage_code_id IS NOT NULL "
            "AND model_id IS NULL AND station_id IS NULL) OR "
            "(target_type = 'model_station' AND storage_code_id IS NULL "
            "AND model_id IS NOT NULL AND station_id IS NOT NULL)",
            name="ck_fixture_placement_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    storage_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_codes.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("machine_models.id", ondelete="CASCADE"), nullable=True, index=True
    )
    station_id: Mapped[int | None] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False, default="manual")
