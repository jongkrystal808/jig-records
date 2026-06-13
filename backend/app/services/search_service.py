from sqlalchemy.orm import Session

from backend.app.repositories.search_repository import SearchRepository


class SearchService:
    def __init__(self, db: Session) -> None:
        self.repo = SearchRepository(db)

    def global_search(self, q: str, customer_id: int | None = None) -> list[dict]:
        results: list[dict] = []

        for row in self.repo.search_fixtures(q, customer_id=customer_id):
            results.append(
                {
                    "entity_type": "fixture",
                    "title": f'{row["code"]} - {row["name"]}',
                    "subtitle": "Fixture",
                    "reference_id": row["id"],
                    "stock_qty": row["stock_qty"] if row["stock_qty"] is not None else 0,
                    "stock_status": row["stock_status"] or "normal",
                    "location_code": row["location_code"],
                }
            )

        for model in self.repo.search_models(q, customer_id=customer_id):
            results.append(
                {
                    "entity_type": "model",
                    "title": f"{model.code} - {model.name}",
                    "subtitle": "Machine Model",
                    "reference_id": model.id,
                }
            )

        for station in self.repo.search_stations(q, customer_id=customer_id):
            results.append(
                {
                    "entity_type": "station",
                    "title": f"{station.code} - {station.name}",
                    "subtitle": "Station",
                    "reference_id": station.id,
                }
            )

        return results
