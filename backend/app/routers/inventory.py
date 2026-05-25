from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.inventory import StockAlertRead, StockSummaryRead, StockTransactionCreate
from backend.app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/receipts", status_code=status.HTTP_204_NO_CONTENT)
def create_receipt(payload: StockTransactionCreate, db: Session = Depends(get_db)):
    service = InventoryService(db)
    try:
        service.receipt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/returns", status_code=status.HTTP_204_NO_CONTENT)
def create_return(payload: StockTransactionCreate, db: Session = Depends(get_db)):
    service = InventoryService(db)
    try:
        service.return_material(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/stock", response_model=list[StockSummaryRead])
def list_stock(db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.list_stock_summary()


@router.get("/alerts", response_model=list[StockAlertRead])
def list_alerts(db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.list_alerts()
