import csv
from collections.abc import Iterable, Iterator
from io import StringIO

_SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@")


def escape_spreadsheet_formula(value):
    """Keep user-controlled strings from being interpreted as spreadsheet formulas."""
    if isinstance(value, str) and value.startswith(_SPREADSHEET_FORMULA_PREFIXES):
        return "'" + value
    return value


def _safe_csv_row(fieldnames: list[str], row: dict) -> dict:
    return {name: escape_spreadsheet_formula(row.get(name, "")) for name in fieldnames}


def parse_csv_bytes(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    return [{key: (value or "").strip() for key, value in row.items() if key is not None} for row in reader]


def render_csv_text(fieldnames: list[str], rows: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writerow({name: escape_spreadsheet_formula(name) for name in fieldnames})
    for row in rows:
        writer.writerow(_safe_csv_row(fieldnames, row))
    return buffer.getvalue()


def stream_csv_text(
    fieldnames: list[str],
    rows: Iterable[dict],
    *,
    chunk_size: int = 64 * 1024,
) -> Iterator[str]:
    """Render CSV incrementally so large exports do not accumulate in memory."""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writerow({name: escape_spreadsheet_formula(name) for name in fieldnames})
    yield "\ufeff" + buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow(_safe_csv_row(fieldnames, row))
        if buffer.tell() >= chunk_size:
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
    if buffer.tell():
        yield buffer.getvalue()
