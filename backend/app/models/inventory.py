from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


transaction_type_enum = Enum("receipt", "return", name="transaction_type")
stock_status_enum = Enum("normal", "low_stock", "out_of_stock", name="stock_status")


class MaterialTransaction(Base, TimestampMixin):
    __tablename__ = "material_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[str] = mapped_column(transaction_type_enum, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    items = relationship("MaterialTransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class MaterialTransactionItem(Base):
    __tablename__ = "material_transaction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("material_transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False, index=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)

    transaction = relationship("MaterialTransaction", back_populates="items")


class FixtureStockLevel(Base, TimestampMixin):
    __tablename__ = "fixture_stock_levels"

    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), primary_key=True)
    min_stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    fixture = relationship("Fixture", back_populates="stock_level")


class FixtureStockSummary(Base, TimestampMixin):
    __tablename__ = "fixture_stock_summary"

    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), primary_key=True)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    returned_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_transaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stock_status: Mapped[str] = mapped_column(stock_status_enum, nullable=False, default="normal")

    fixture = relationship("Fixture", back_populates="stock_summary")


class FixtureSerial(Base, TimestampMixin):
    __tablename__ = "fixture_serials"
    __table_args__ = (UniqueConstraint("fixture_id", "serial_no", name="uq_fixture_serial"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False)
    serial_no: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
