from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Response
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.common import CsvImportPayload, ImportResultRead
from backend.app.schemas.inventory import IdentifierStockSummaryRead, StockAlertRead, StockSummaryRead, StockTransactionCreate, StockTransactionRead
from backend.app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(require_permission("read"))])


@router.post("/receipts", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def create_receipt(
    payload: StockTransactionCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        service.receipt(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/returns", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def create_return(
    payload: StockTransactionCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        service.return_material(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/stock", response_model=list[StockSummaryRead])
def list_stock(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.list_stock_summary(customer_id=customer_id)


@router.get("/alerts", response_model=list[StockAlertRead])
def list_alerts(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.list_alerts(customer_id=customer_id)


@router.get("/identifier-stock-summary", response_model=list[IdentifierStockSummaryRead])
def list_identifier_stock_summary(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.list_identifier_stock_summary(customer_id=customer_id)


@router.get("/transactions", response_model=list[StockTransactionRead])
def list_transactions(
    limit: int = Query(20, ge=1, le=2000),
    customer_id: int | None = Query(default=None),
    transaction_type: str | None = Query(default=None, pattern="^(receipt|return)?$"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    dt_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    dt_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    return service.list_transactions(
        limit,
        customer_id=customer_id,
        transaction_type=transaction_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )


@router.get("/transactions/export")
def export_transactions(
    limit: int = Query(200, ge=1, le=2000),
    customer_id: int | None = Query(default=None),
    transaction_type: str | None = Query(default=None, pattern="^(receipt|return)?$"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    dt_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    dt_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    content = service.export_transactions_csv(
        limit,
        customer_id=customer_id,
        transaction_type=transaction_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )


@router.get("/transactions/export-report")
def export_transaction_report(
    customer_id: int | None = Query(default=None),
    report_type: str = Query(..., pattern="^(summary|detail)$"),
    file_format: str = Query(..., pattern="^(xlsx|txt)$"),
    transaction_type: str | None = Query(default=None, pattern="^(receipt|return)?$"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    dt_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    dt_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    columns, rows = service.build_transaction_export_report(
        customer_id=customer_id,
        report_type=report_type,
        transaction_type=transaction_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )
    report_label = "summary" if report_type == "summary" else "detail"
    if file_format == "xlsx":
        content = service.render_transaction_report_xlsx(f"transaction-{report_label}", columns, rows)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="transaction-{report_label}.xlsx"'},
        )
    content = service.render_transaction_report_txt(columns, rows)
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="transaction-{report_label}.txt"'},
    )


@router.get("/transactions/export-report/preview")
def preview_transaction_report_export(
    customer_id: int | None = Query(default=None),
    report_type: str = Query(..., pattern="^(summary|detail)$"),
    transaction_type: str | None = Query(default=None, pattern="^(receipt|return)?$"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    dt_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    dt_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    return service.get_transaction_export_preview(
        customer_id=customer_id,
        report_type=report_type,
        transaction_type=transaction_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )


@router.get("/transactions/template")
def transaction_template(db: Session = Depends(get_db)):
    content = InventoryService(db).transaction_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions-template.csv"'},
    )


@router.post("/transactions/import", response_model=ImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_transactions(
    customer_id: int = Query(...),
    operator_name: str = Query(..., min_length=1),
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        return {"imported_count": service.import_transactions_csv(customer_id, operator_name, payload)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

