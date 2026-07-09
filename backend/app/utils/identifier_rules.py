def is_strict_identifier(value: str) -> bool:
    return value.isdigit() and len(value) <= 4


def normalize_identifier_for_write(value: str | None) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError("identifier is required")
    if is_strict_identifier(normalized):
        return normalized.zfill(4)
    return normalized


def resolve_identifier_query(value: str | None) -> tuple[list[str] | None, str | None]:
    token = (value or "").strip()
    if not token:
        return None, None
    if is_strict_identifier(token):
        significant = token.lstrip("0") or "0"
        exact_matches = list(dict.fromkeys(significant.zfill(width) for width in range(len(significant), 5)))
        return exact_matches, None
    return [token], None
