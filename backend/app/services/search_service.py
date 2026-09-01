from sqlalchemy.orm import Session

from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.production_repository import ProductionRepository
from backend.app.repositories.search_repository import FixtureSearchMode, SearchEntityType, SearchRepository
from backend.app.services.inventory_service import InventoryService
from backend.app.services.master_service import MasterService
from backend.app.services.production_service import ProductionService
from backend.app.utils.identifier_rules import resolve_identifier_query


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SearchRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.production_repo = ProductionRepository(db)
        self.inventory_service = InventoryService(db)
        self.master_service = MasterService(db)
        self.production_service = ProductionService(db)

    @staticmethod
    def _serialize_result(entity_type: SearchEntityType, row: dict) -> dict:
        payload = {
            "entity_type": entity_type,
            "title": row["code"],
            "subtitle": row["name"],
            "reference_id": row["id"],
            "is_active": bool(row["is_active"]),
        }
        if entity_type == "fixture":
            payload["stock_qty"] = row["stock_qty"] if row["stock_qty"] is not None else 0
            payload["stock_status"] = row["stock_status"] or "normal"
            payload["location_code"] = row["location_code"]
            payload["matched_identifier"] = row.get("matched_identifier")
        return payload

    def global_search(
        self,
        q: str,
        *,
        customer_id: int | None = None,
        entity_type: SearchEntityType | None = None,
        fixture_search_mode: FixtureSearchMode = "fixture",
        page: int = 1,
        page_size: int = 12,
    ) -> dict:
        offset = (page - 1) * page_size
        if entity_type is not None:
            rows, total = self.repo.search_entities(
                entity_type,
                q,
                customer_id=customer_id,
                limit=page_size,
                offset=offset,
                fixture_search_mode=fixture_search_mode,
            )
            items = [self._serialize_result(entity_type, row) for row in rows]
            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": offset + len(items) < total,
            }

        combined_limit = page * page_size
        combined_rows: list[dict] = []
        total = 0
        for current_type in ("fixture", "model", "station"):
            rows, count = self.repo.search_entities(
                current_type,  # type: ignore[arg-type]
                q,
                customer_id=customer_id,
                limit=combined_limit,
                offset=0,
                fixture_search_mode="fixture",
            )
            total += count
            combined_rows.extend(
                {
                    **self._serialize_result(current_type, row),  # type: ignore[arg-type]
                    "_active_rank": row.get("active_rank", 0),
                    "_match_score": row.get("match_score", 0),
                }
                for row in rows
            )

        combined_rows.sort(
            key=lambda row: (
                int(row["_active_rank"]),
                int(row["_match_score"]),
                str(row["title"]),
            )
        )
        sliced = combined_rows[offset : offset + page_size]
        items = [{key: value for key, value in row.items() if not key.startswith("_")} for row in sliced]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": offset + len(items) < total,
        }

    def get_fixture_overview(
        self,
        *,
        customer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        offset = (page - 1) * page_size
        rows, total = self.repo.search_fixtures(
            "",
            customer_id=customer_id,
            limit=page_size,
            offset=offset,
        )
        items = [self._serialize_result("fixture", row) for row in rows]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": offset + len(items) < total,
        }

    def get_fixture_context(
        self,
        fixture_id: int,
        *,
        customer_id: int,
        recent_transaction_limit: int = 8,
        identifier: str | None = None,
    ) -> dict:
        fixture = self.master_service.get_fixture_detail(fixture_id, customer_id=customer_id)
        stock = self.inventory_repo.get_stock_summary_row(fixture_id, customer_id=customer_id)
        exact_identifier = identifier.strip() if identifier and identifier.strip() else None
        identifier_rows = [] if exact_identifier else self.inventory_repo.list_identifier_stock_summary_rows(
            customer_id=customer_id,
            fixture_id=fixture_id,
        )
        station_rows = [] if exact_identifier else self.production_repo.list_requirement_rows_by_fixture(
            fixture_id,
            customer_id=customer_id,
        )
        related_models = []
        seen_model_ids: set[int] = set()
        for row in station_rows:
            model_id = int(row["model_id"])
            if model_id in seen_model_ids:
                continue
            seen_model_ids.add(model_id)
            related_models.append(self.master_service.get_model_detail(model_id, customer_id=customer_id))
        transactions = self.inventory_service.list_transactions(
            recent_transaction_limit,
            customer_id=customer_id,
            fixture_id=fixture_id,
            identifier=exact_identifier,
        )
        if exact_identifier:
            identifier_candidates, _ = resolve_identifier_query(exact_identifier)
            normalized_candidates = {candidate.casefold() for candidate in identifier_candidates or []}
            filtered_transactions = []
            for transaction in transactions:
                matching_items = [
                    item
                    for item in transaction["items"]
                    if (item.get("identifier") or "").strip().casefold() in normalized_candidates
                ]
                if matching_items:
                    filtered_transactions.append({**transaction, "items": matching_items})
            transactions = filtered_transactions
        return {
            "fixture": fixture,
            "stock": stock,
            "identifier_rows": identifier_rows,
            "related_models": related_models,
            "station_rows": station_rows,
            "transactions": transactions,
        }

    def get_model_context(self, model_id: int, *, customer_id: int) -> dict:
        model = self.master_service.get_model_detail(model_id, customer_id=customer_id)
        query = self.production_service.get_model_query(model_id, customer_id=customer_id)
        return {
            "model": model,
            "query": query,
        }
