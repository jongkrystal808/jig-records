from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class StorageLocation(Base, TimestampMixin):
    __tablename__ = "storage_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    area: Mapped[str] = mapped_column(String(8), nullable=False)
    rack: Mapped[str] = mapped_column(String(8), nullable=False)
    layer: Mapped[str] = mapped_column(String(8), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)


class FixtureLocationAssignment(Base, TimestampMixin):
    __tablename__ = "fixture_location_assignments"
    __table_args__ = (UniqueConstraint("fixture_id", name="uq_fixture_location_one"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("storage_locations.id", ondelete="CASCADE"), nullable=False)


class FixtureImage(Base, TimestampMixin):
    __tablename__ = "fixture_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
