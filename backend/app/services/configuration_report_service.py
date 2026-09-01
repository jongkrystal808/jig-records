from __future__ import annotations

from datetime import datetime
from io import BytesIO, StringIO
import csv

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from backend.app.repositories.configuration_report_repository import (
    ConfigurationReportRepository,
    REPORT_FILTER_KEYS,
)
from backend.app.utils.csv_tools import escape_spreadsheet_formula


REPORT_COLUMN_LABELS = {
    "index": "序號",
    "customer": "客戶",
    "fixtureCode": "治具代碼",
    "fixtureName": "治具名稱",
    "stockQty": "總庫存",
    "customerSuppliedQty": "客供庫存",
    "selfPurchasedQty": "自購庫存",
    "minStockQty": "最低水位",
    "waterStatus": "水位狀態",
    "lineStorage": "產線儲位",
    "departmentStorage": "部門儲位",
    "modelCode": "機種",
    "station": "站點",
    "requiredQty": "需求數量",
    "maxOpenStationCount": "可開站",
    "configurationStatus": "配置狀態",
}
DEFAULT_REPORT_COLUMNS = list(REPORT_COLUMN_LABELS)
TRANSACTION_DETAIL_LABELS = [
    "收退料類型",
    "交易來源",
    "交易日期",
    "單號",
    "datecode/編號",
    "交易數量",
]


class ConfigurationReportService:
    def __init__(self, db: Session) -> None:
        self.repo = ConfigurationReportRepository(db)

    @staticmethod
    def _serialize_row(row: dict) -> dict:
        return {
            "key": f"{row['row_type']}-{row['row_id']}",
            "customer_code": row["customer_code"],
            "fixture_id": int(row["fixture_id"] or 0),
            "fixture_code": row["fixture_code"] or "",
            "fixture_name": row["fixture_name"] or "",
            "stock_qty": None if row["stock_qty"] is None else int(row["stock_qty"]),
            "customer_supplied_qty": (
                None
                if row["customer_supplied_qty"] is None
                else int(row["customer_supplied_qty"])
            ),
            "self_purchased_qty": (
                None
                if row["self_purchased_qty"] is None
                else int(row["self_purchased_qty"])
            ),
            "min_stock_qty": (
                None if row["min_stock_qty"] is None else int(row["min_stock_qty"])
            ),
            "water_status": row["water_status"],
            "line_storage": row["line_storage"] or "",
            "department_storage": row["department_storage"] or "",
            "model_id": int(row["model_id"] or 0),
            "model_code": row["model_code"] or "",
            "station_id": int(row["station_id"] or 0),
            "station_code": row["station_code"] or "",
            "station_name": row["station_name"] or "",
            "required_qty": (
                None if row["required_qty"] is None else int(row["required_qty"])
            ),
            "max_open_station_count": (
                None
                if row["max_open_station_count"] is None
                else int(row["max_open_station_count"])
            ),
            "configuration_status": row["configuration_status"],
        }

    @staticmethod
    def normalize_priority(priority: str | None) -> list[str]:
        if not priority:
            return []
        return list(
            dict.fromkeys(
                key.strip()
                for key in priority.split(",")
                if key.strip() in REPORT_FILTER_KEYS
            )
        )

    def get_page(
        self,
        *,
        customer_id: int,
        page: int,
        page_size: int,
        filters: dict,
        sort_by: str,
        sort_direction: str,
        include_transaction_details: bool,
    ) -> dict:
        raw_rows, _ = self.repo.list_rows(
            customer_id=customer_id,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        summary = self.repo.summarize(customer_id=customer_id, filters=filters)
        items = [self._serialize_row(row) for row in raw_rows]
        fixture_ids = list(
            dict.fromkeys(row["fixture_id"] for row in items if row["fixture_id"] > 0)
        )
        details = (
            self.repo.list_transaction_details(fixture_ids=fixture_ids, filters=filters)
            if include_transaction_details
            else []
        )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            **summary,
            "transaction_details": details,
            "transaction_detail_count": self.repo.count_transaction_details_for_filtered_fixtures(
                customer_id=customer_id,
                filters=filters,
            ),
        }

    def get_options(
        self,
        *,
        customer_id: int,
        filters: dict,
        priority: str | None,
    ) -> dict:
        return self.repo.list_options(
            customer_id=customer_id,
            filters=filters,
            priority=self.normalize_priority(priority),
        )

    @staticmethod
    def _water_status_label(value: str) -> str:
        return {"normal": "正常", "low": "低水位", "empty": "缺料", "na": "不適用"}.get(
            value,
            value,
        )

    @staticmethod
    def _configuration_status_label(value: str) -> str:
        return {
            "configured": "已配置",
            "unconfigured": "未配置",
            "unbound": "未綁定",
        }.get(value, value)

    @classmethod
    def _export_value(cls, key: str, row: dict, index: int):
        if key == "index":
            return index + 1
        if key == "customer":
            return row["customer_code"] or "—"
        if key == "fixtureCode":
            return row["fixture_code"] or "—"
        if key == "fixtureName":
            return row["fixture_name"] or "—"
        if key == "stockQty":
            return row["stock_qty"] if row["stock_qty"] is not None else "—"
        if key == "customerSuppliedQty":
            return (
                row["customer_supplied_qty"]
                if row["customer_supplied_qty"] is not None
                else "—"
            )
        if key == "selfPurchasedQty":
            return (
                row["self_purchased_qty"]
                if row["self_purchased_qty"] is not None
                else "—"
            )
        if key == "minStockQty":
            return row["min_stock_qty"] if row["min_stock_qty"] is not None else "—"
        if key == "waterStatus":
            return cls._water_status_label(row["water_status"])
        if key == "lineStorage":
            return row["line_storage"] or "—"
        if key == "departmentStorage":
            return row["department_storage"] or "—"
        if key == "modelCode":
            return row["model_code"] or "—"
        if key == "station":
            if not row["station_code"]:
                return "—"
            return (
                f"{row['station_code']}－{row['station_name']}"
                if row["station_name"]
                else row["station_code"]
            )
        if key == "requiredQty":
            return row["required_qty"] if row["required_qty"] is not None else "—"
        if key == "maxOpenStationCount":
            return (
                row["max_open_station_count"]
                if row["max_open_station_count"] is not None
                else "—"
            )
        return cls._configuration_status_label(row["configuration_status"])

    def build_export(
        self,
        *,
        customer_id: int,
        filters: dict,
        sort_by: str,
        sort_direction: str,
        columns: list[str],
        include_transaction_details: bool,
    ) -> tuple[list[str], list[list]]:
        selected_columns = [
            key for key in columns if key in REPORT_COLUMN_LABELS
        ] or DEFAULT_REPORT_COLUMNS
        raw_rows, _ = self.repo.list_rows(
            customer_id=customer_id,
            filters=filters,
            page=None,
            page_size=None,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        rows = [self._serialize_row(row) for row in raw_rows]
        detail_groups: dict[int, list[dict]] = {}
        if include_transaction_details:
            fixture_ids = list(
                dict.fromkeys(row["fixture_id"] for row in rows if row["fixture_id"] > 0)
            )
            for detail in self.repo.list_transaction_details(
                fixture_ids=fixture_ids,
                filters=filters,
            ):
                detail_groups.setdefault(int(detail["fixture_id"]), []).append(detail)

        headers = [REPORT_COLUMN_LABELS[key] for key in selected_columns]
        if include_transaction_details:
            headers.extend(TRANSACTION_DETAIL_LABELS)

        exported_rows: list[list] = []
        expanded_fixture_ids: set[int] = set()
        for index, row in enumerate(rows):
            base = [self._export_value(key, row, index) for key in selected_columns]
            fixture_id = row["fixture_id"]
            details = (
                detail_groups.get(fixture_id, [])
                if fixture_id > 0 and fixture_id not in expanded_fixture_ids
                else []
            )
            if fixture_id > 0:
                expanded_fixture_ids.add(fixture_id)
            if not include_transaction_details or not details:
                exported_rows.append(
                    base + (["", "", "", "", "", ""] if include_transaction_details else [])
                )
                continue
            for detail in details:
                exported_rows.append(
                    base
                    + [
                        "收料" if detail["transaction_type"] == "receipt" else "退料",
                        (
                            "客供"
                            if detail["ownership_type"] == "customer_supplied"
                            else "自購"
                        ),
                        detail["occurred_at"].date().isoformat(),
                        detail["transaction_no"] or "（無單號）",
                        detail["identifier"] or "",
                        int(detail["quantity"]),
                    ]
                )
        return headers, exported_rows

    @staticmethod
    def render_csv(headers: list[str], rows: list[list]) -> bytes:
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow([escape_spreadsheet_formula(value) for value in headers])
        writer.writerows(
            [escape_spreadsheet_formula(value) for value in row]
            for row in rows
        )
        return ("\ufeff" + output.getvalue()).encode("utf-8")

    @staticmethod
    def render_xlsx(headers: list[str], rows: list[list]) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "治具庫存配置報表"
        worksheet.append([escape_spreadsheet_formula(value) for value in headers])
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
        for row in rows:
            worksheet.append([escape_spreadsheet_formula(value) for value in row])
        worksheet.freeze_panes = "A2"
        for column_cells in worksheet.columns:
            width = min(
                42,
                max(10, max(len(str(cell.value or "")) for cell in column_cells) + 2),
            )
            worksheet.column_dimensions[column_cells[0].column_letter].width = width
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()
