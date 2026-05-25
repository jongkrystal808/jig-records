from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.common import ORMModel


class StockTransactionItemInput(BaseModel):
    fixture_id: int
    qty: int = Field(gt=0)


class StockTransactionCreate(BaseModel):
    note: str | None = None
    items: list[StockTransactionItemInput] = Field(min_length=1)


class StockSummaryRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    stock_qty: int
    min_stock_qty: int
    stock_status: Literal["normal", "low_stock", "out_of_stock"]
    last_transaction_at: datetime | None


class StockAlertRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    stock_qty: int
    min_stock_qty: int
    stock_status: Literal["low_stock", "out_of_stock"]
