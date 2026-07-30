from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.common import ORMModel
from backend.app.utils.identifier_rules import normalize_identifier_for_write


class StockTransactionItemInput(BaseModel):
    fixture_id: int
    ownership_type: Literal["customer_supplied", "self_purchased"]
    identifier: str | None = Field(default=None, max_length=120)
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_identifier(self):
        self.identifier = normalize_identifier_for_write(self.identifier)
        return self


class StockTransactionCreate(BaseModel):
    customer_id: int
    created_by: str = Field(min_length=1, max_length=120)
    occurred_at: datetime | None = None
    transaction_no: str = Field(min_length=1, max_length=64)
    note: str | None = None
    items: list[StockTransactionItemInput] = Field(min_length=1)


class StockSummaryRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    stock_qty: int
    customer_supplied_qty: int
    self_purchased_qty: int
    min_stock_qty: int
    stock_status: Literal["normal", "low_stock", "out_of_stock"]
    last_transaction_at: datetime | None


class StockAlertRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    stock_qty: int
    customer_supplied_qty: int
    self_purchased_qty: int
    min_stock_qty: int
    stock_status: Literal["low_stock", "out_of_stock"]


class DashboardRecentTransactionEntryRead(ORMModel):
    transaction_id: int
    transaction_item_id: int
    transaction_no: str | None
    occurred_at: datetime
    fixture_code: str
    identifier: str | None
    quantity: int


class InventoryDashboardSummaryRead(ORMModel):
    today_receipt_qty: int
    today_return_qty: int
    low_stock_count: int
    low_stock_preview_entries: list[StockAlertRead]
    has_more_low_stock_entries: bool
    recent_receipt_entries: list[DashboardRecentTransactionEntryRead]
    recent_return_entries: list[DashboardRecentTransactionEntryRead]


class IdentifierStockSummaryRead(ORMModel):
    fixture_id: int
    identifier: str
    stock_qty: int
    customer_supplied_qty: int
    self_purchased_qty: int


class StockTransactionItemRead(ORMModel):
    fixture_id: int | None
    fixture_code: str
    fixture_name: str
    ownership_type: Literal["customer_supplied", "self_purchased"]
    identifier: str | None
    quantity: int
    note: str | None


class StockTransactionRead(ORMModel):
    id: int
    customer_id: int
    transaction_type: Literal["receipt", "return"]
    transaction_no: str | None
    occurred_at: datetime
    created_by: str
    note: str | None
    created_at: datetime
    items: list[StockTransactionItemRead]


class StockTransactionPageRead(ORMModel):
    items: list[StockTransactionRead]
    page: int
    page_size: int
    total: int


class TransactionOverviewRowRead(ORMModel):
    id: int
    transaction_type: Literal["receipt", "return"]
    transaction_no: str | None
    occurred_at: datetime
    created_by: str
    fixture_id: int | None
    fixture_code: str
    fixture_name: str
    ownership_type: Literal["customer_supplied", "self_purchased"]
    identifier: str | None
    quantity: int
    note: str | None


class TransactionOverviewPageRead(ORMModel):
    items: list[TransactionOverviewRowRead]
    page: int
    page_size: int
    total: int


class InventoryRecalculateRead(ORMModel):
    customer_id: int | None
    fixture_count: int
    transaction_count: int
    item_count: int


class TransactionReverseRead(ORMModel):
    transaction_id: int
    transaction_no: str | None
    transaction_type: Literal["receipt", "return"]
    item_count: int
    total_quantity: int
