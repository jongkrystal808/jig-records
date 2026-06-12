from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.common import ORMModel


class StockTransactionItemInput(BaseModel):
    fixture_id: int
    manage_type: Literal["datecode", "serial"]
    ownership_type: Literal["customer_supplied", "self_purchased"]
    datecode: str | None = Field(default=None, max_length=80)
    serial_number: str | None = Field(default=None, max_length=120)
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_by_manage_type(self):
        if self.manage_type == "datecode":
            if not self.datecode:
                raise ValueError("datecode item requires datecode")
            if self.serial_number:
                raise ValueError("datecode item cannot include serial_number")
            return self

        if not self.serial_number:
            raise ValueError("serial item requires serial_number")
        if self.datecode:
            raise ValueError("serial item cannot include datecode")
        if self.quantity != 1:
            raise ValueError("serial item quantity must be 1")
        return self


class StockTransactionCreate(BaseModel):
    customer_id: int
    created_by: str = Field(min_length=1, max_length=120)
    occurred_at: datetime | None = None
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


class StockTransactionItemRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    manage_type: Literal["datecode", "serial"]
    ownership_type: Literal["customer_supplied", "self_purchased"]
    datecode: str | None
    serial_number: str | None
    quantity: int
    note: str | None


class StockTransactionRead(ORMModel):
    id: int
    customer_id: int
    transaction_type: Literal["receipt", "return"]
    transaction_no: str
    occurred_at: datetime
    created_by: str
    note: str | None
    created_at: datetime
    items: list[StockTransactionItemRead]
