from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class FixtureRequirement(Base, TimestampMixin):
    __tablename__ = "fixture_requirements"
    __table_args__ = (
        UniqueConstraint("model_id", "station_id", "fixture_id", name="uq_model_station_fixture_requirement"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("machine_models.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False, index=True)
    required_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    designated_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    designated_identifier_rows: Mapped[list["FixtureRequirementIdentifier"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
        order_by="FixtureRequirementIdentifier.identifier",
    )

    @property
    def designated_identifiers(self) -> list[str]:
        return [row.identifier for row in self.designated_identifier_rows]


class FixtureRequirementIdentifier(Base):
    __tablename__ = "fixture_requirement_identifiers"

    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("fixture_requirements.id", ondelete="CASCADE"),
        primary_key=True,
    )
    identifier: Mapped[str] = mapped_column(String(120), primary_key=True)

    requirement: Mapped[FixtureRequirement] = relationship(back_populates="designated_identifier_rows")


class MachineCapacitySummary(Base, TimestampMixin):
    __tablename__ = "machine_capacity_summary"

    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), primary_key=True)
    max_open_station_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bottleneck_fixture_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
