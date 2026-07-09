from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


transaction_type_enum = Enum("receipt", "return", name="transaction_type", native_enum=False, validate_strings=True)
stock_status_enum = Enum("normal", "low_stock", "out_of_stock", name="stock_status", native_enum=False, validate_strings=True)
ownership_type_enum = Enum(
    "customer_supplied",
    "self_purchased",
    name="ownership_type",
    native_enum=False,
    validate_strings=True,
)


class MaterialTransaction(Base, TimestampMixin):
    __tablename__ = "material_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(transaction_type_enum, nullable=False)
    transaction_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    items = relationship("MaterialTransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class MaterialTransactionItem(Base):
    __tablename__ = "material_transaction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("material_transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False, index=True)
    ownership_type: Mapped[str] = mapped_column(ownership_type_enum, nullable=False)
    identifier: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

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
