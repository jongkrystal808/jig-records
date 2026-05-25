from sqlalchemy.orm import Session

from backend.app.repositories.search_repository import SearchRepository


class SearchService:
    def __init__(self, db: Session) -> None:
        self.repo = SearchRepository(db)

    def global_search(self, q: str) -> list[dict]:
        results: list[dict] = []

        for row in self.repo.search_fixtures(q):
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

        for model in self.repo.search_models(q):
            results.append(
                {
                    "entity_type": "model",
                    "title": f"{model.code} - {model.name}",
                    "subtitle": "Machine Model",
                    "reference_id": model.id,
                }
            )

        for station in self.repo.search_stations(q):
            results.append(
                {
                    "entity_type": "station",
                    "title": f"{station.code} - {station.name}",
                    "subtitle": "Station",
                    "reference_id": station.id,
                }
            )

        for location in self.repo.search_locations(q):
            results.append(
                {
                    "entity_type": "location",
                    "title": location.code,
                    "subtitle": "Storage Location",
                    "reference_id": location.id,
                    "location_code": location.code,
                }
            )

        for serial in self.repo.search_serials(q):
            results.append(
                {
                    "entity_type": "serial",
                    "title": serial["serial_no"],
                    "subtitle": f'{serial["code"]} - {serial["name"]}',
                    "reference_id": serial["id"],
                }
            )

        return results
