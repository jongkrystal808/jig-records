from datetime import date, datetime, time, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.common import CsvImportPayload, ImportResultRead
from backend.app.schemas.inventory import (
    ConfigurationReportOptionsRead,
    ConfigurationReportPageRead,
    IdentifierStockSummaryRead,
    InventoryDashboardSummaryRead,
    InventoryRecalculateRead,
    StockAlertRead,
    StockSummaryRead,
    StockTransactionCreate,
    StockTransactionPageRead,
    StockTransactionRead,
    TransactionOverviewPageRead,
    TransactionReverseRead,
)
from backend.app.services.configuration_report_service import ConfigurationReportService
from backend.app.services.inventory_service import DuplicateTransactionError, InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(require_permission("read"))])


def _configuration_report_filters(
    *,
    keyword: str | None,
    fixture_status: str | list[str] | None,
    fixture_id: int | None,
    model_id: int | None,
    station_id: int | None,
    water_status: str | list[str] | None,
    storage: str | None,
    configuration_status: str | list[str] | None,
    transaction_type: str | list[str] | None,
    ownership_type: str | list[str] | None,
    date_from: date | None,
    date_to: date | None,
) -> dict:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be earlier than or equal to date_to",
        )
    if not transaction_type:
        ownership_type = None
        date_from = None
        date_to = None
    return {
        "keyword": keyword,
        "fixture_status": fixture_status or ["active"],
        "fixture_id": fixture_id,
        "model_id": model_id,
        "station_id": station_id,
        "water_status": water_status,
        "storage": storage,
        "configuration_status": configuration_status,
        "transaction_type": transaction_type,
        "ownership_type": ownership_type,
        "date_from": datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None,
        "date_to": datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None,
    }


@router.post("/receipts", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def create_receipt(
    payload: StockTransactionCreate,
    confirm_duplicate: bool = Query(default=False),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        service.receipt(payload, allow_duplicate=confirm_duplicate)
    except DuplicateTransactionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/returns", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def create_return(
    payload: StockTransactionCreate,
    confirm_duplicate: bool = Query(default=False),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        service.return_material(payload, allow_duplicate=confirm_duplicate)
    except DuplicateTransactionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/configuration-report", response_model=ConfigurationReportPageRead)
def get_configuration_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    customer_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    fixture_status: list[Literal["active", "inactive", "all"]] | None = Query(default=None),
    fixture_id: int | None = Query(default=None, ge=1),
    model_id: int | None = Query(default=None, ge=1),
    station_id: int | None = Query(default=None, ge=1),
    water_status: list[Literal["attention", "low", "empty", "normal"]] | None = Query(default=None),
    storage: str | None = Query(default=None),
    configuration_status: list[Literal["configured", "unconfigured", "unbound"]] | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sort_by: str = Query(
        "fixture_code",
        pattern="^(fixture_code|fixture_name|stock_qty|customer_supplied_qty|self_purchased_qty|model_code|station_code|water_status|configuration_status)$",
    ),
    sort_direction: str = Query("asc", pattern="^(asc|desc)$"),
    include_transaction_details: bool = Query(default=False),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    filters = _configuration_report_filters(
        keyword=keyword,
        fixture_status=fixture_status,
        fixture_id=fixture_id,
        model_id=model_id,
        station_id=station_id,
        water_status=water_status,
        storage=storage,
        configuration_status=configuration_status,
        transaction_type=transaction_type,
        ownership_type=ownership_type,
        date_from=date_from,
        date_to=date_to,
    )
    return ConfigurationReportService(db).get_page(
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
        include_transaction_details=include_transaction_details,
    )


@router.get("/configuration-report/options", response_model=ConfigurationReportOptionsRead)
def get_configuration_report_options(
    customer_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    fixture_status: list[Literal["active", "inactive", "all"]] | None = Query(default=None),
    fixture_id: int | None = Query(default=None, ge=1),
    model_id: int | None = Query(default=None, ge=1),
    station_id: int | None = Query(default=None, ge=1),
    water_status: list[Literal["attention", "low", "empty", "normal"]] | None = Query(default=None),
    storage: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    filters = _configuration_report_filters(
        keyword=keyword,
        fixture_status=fixture_status,
        fixture_id=fixture_id,
        model_id=model_id,
        station_id=station_id,
        water_status=water_status,
        storage=storage,
        configuration_status=None,
        transaction_type=None,
        ownership_type=None,
        date_from=None,
        date_to=None,
    )
    return ConfigurationReportService(db).get_options(
        customer_id=customer_id,
        filters=filters,
        priority=priority,
    )


@router.get("/configuration-report/export")
def export_configuration_report(
    customer_id: int | None = Query(default=None),
    file_format: str = Query("csv", pattern="^(csv|xlsx)$"),
    columns: str | None = Query(default=None),
    include_transaction_details: bool = Query(default=False),
    keyword: str | None = Query(default=None),
    fixture_status: list[Literal["active", "inactive", "all"]] | None = Query(default=None),
    fixture_id: int | None = Query(default=None, ge=1),
    model_id: int | None = Query(default=None, ge=1),
    station_id: int | None = Query(default=None, ge=1),
    water_status: list[Literal["attention", "low", "empty", "normal"]] | None = Query(default=None),
    storage: str | None = Query(default=None),
    configuration_status: list[Literal["configured", "unconfigured", "unbound"]] | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sort_by: str = Query(
        "fixture_code",
        pattern="^(fixture_code|fixture_name|stock_qty|customer_supplied_qty|self_purchased_qty|model_code|station_code|water_status|configuration_status)$",
    ),
    sort_direction: str = Query("asc", pattern="^(asc|desc)$"),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    filters = _configuration_report_filters(
        keyword=keyword,
        fixture_status=fixture_status,
        fixture_id=fixture_id,
        model_id=model_id,
        station_id=station_id,
        water_status=water_status,
        storage=storage,
        configuration_status=configuration_status,
        transaction_type=transaction_type,
        ownership_type=ownership_type,
        date_from=date_from,
        date_to=date_to,
    )
    service = ConfigurationReportService(db)
    headers, rows = service.build_export(
        customer_id=customer_id,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
        columns=[] if not columns else [column.strip() for column in columns.split(",")],
        include_transaction_details=include_transaction_details,
    )
    filename = f"fixture-inventory-report-{customer_id}.{file_format}"
    export_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Export-Row-Count": str(len(rows)),
        "X-Export-Column-Count": str(len(headers)),
    }
    if file_format == "xlsx":
        return Response(
            content=service.render_xlsx(headers, rows),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=export_headers,
        )
    return Response(
        content=service.render_csv(headers, rows),
        media_type="text/csv; charset=utf-8",
        headers=export_headers,
    )


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
    fixture_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.list_identifier_stock_summary(customer_id=customer_id, fixture_id=fixture_id)


@router.get("/dashboard-summary", response_model=InventoryDashboardSummaryRead)
def get_dashboard_summary(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.build_dashboard_summary(customer_id=customer_id)


@router.get("/transactions", response_model=list[StockTransactionRead])
def list_transactions(
    limit: int = Query(20, ge=1, le=2000),
    customer_id: int | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
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
        ownership_type=ownership_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )


@router.get("/transactions/overview", response_model=TransactionOverviewPageRead)
def list_transaction_overview(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    customer_id: int | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
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
    return service.list_transaction_overview_page(
        page,
        page_size,
        customer_id=customer_id,
        transaction_type=transaction_type,
        ownership_type=ownership_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        identifier=identifier,
        created_by=created_by,
    )


@router.get("/admin/transactions", response_model=StockTransactionPageRead, dependencies=[Depends(require_permission("manage"))])
def list_admin_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    customer_id: int | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    return service.list_transaction_page(
        page,
        page_size,
        customer_id=customer_id,
        transaction_type=transaction_type,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        created_by=created_by,
    )


@router.get("/transactions/export")
def export_transactions(
    customer_id: int | None = Query(default=None),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
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
    content = service.stream_transactions_csv(
        customer_id=customer_id,
        transaction_type=transaction_type,
        date_from=dt_from,
        date_to=dt_to,
        fixture_code=fixture_code,
        transaction_no=transaction_no,
        ownership_type=ownership_type,
        identifier=identifier,
        created_by=created_by,
    )
    return StreamingResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )


@router.get("/transactions/export-report")
def export_transaction_report(
    customer_id: int | None = Query(default=None),
    report_type: str = Query(..., pattern="^(summary|detail)$"),
    file_format: str = Query(..., pattern="^(xlsx|txt)$"),
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
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
        ownership_type=ownership_type,
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
    transaction_type: list[Literal["receipt", "return"]] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    fixture_code: str | None = Query(default=None),
    transaction_no: str | None = Query(default=None),
    ownership_type: list[Literal["customer_supplied", "self_purchased"]] | None = Query(default=None),
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
        ownership_type=ownership_type,
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


@router.delete(
    "/admin/transactions/{transaction_id}",
    response_model=TransactionReverseRead,
    dependencies=[Depends(require_permission("manage"))],
)
def reverse_transaction(
    transaction_id: int,
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    try:
        return service.reverse_transaction(transaction_id, customer_id=customer_id, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post(
    "/admin/recalculate",
    response_model=InventoryRecalculateRead,
    dependencies=[Depends(require_permission("manage"))],
)
def recalculate_inventory_state(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = InventoryService(db)
    result = service.recalculate_inventory_state(customer_id=customer_id)
    db.commit()
    return result

