from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from backend.app.core.config import settings

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
_CONTENT_TYPE_SUFFIXES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@dataclass(frozen=True)
class FixtureImageRename:
    source_path: Path
    target_path: Path


def _validate_fixture_code(fixture_code: str) -> str:
    normalized = fixture_code.strip()
    if not normalized or normalized in {".", ".."} or "/" in normalized or "\\" in normalized:
        raise ValueError("Fixture code cannot be used as an image filename")
    return normalized


def _fixture_image_dir(customer_id: int) -> Path:
    if customer_id <= 0:
        raise ValueError("customer_id must be positive")
    return Path(settings.fixture_image_dir) / str(customer_id)


def _resolve_image_in_dir(image_dir: Path, fixture_code: str) -> Path | None:
    code = _validate_fixture_code(fixture_code)
    for suffix in _IMAGE_SUFFIXES:
        candidate = image_dir / f"{code}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def resolve_fixture_image_path(customer_id: int, fixture_code: str) -> Path | None:
    return _resolve_image_in_dir(_fixture_image_dir(customer_id), fixture_code)


def resolve_legacy_fixture_image_path(fixture_code: str) -> Path | None:
    """Resolve the pre-customer-scope flat path. The service decides whether it is safe to expose."""
    return _resolve_image_in_dir(Path(settings.fixture_image_dir), fixture_code)


def _list_image_codes(image_dir: Path) -> set[str]:
    if not image_dir.is_dir():
        return set()
    return {
        path.stem
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
    }


def list_fixture_image_codes(customer_id: int) -> set[str]:
    return _list_image_codes(_fixture_image_dir(customer_id))


def list_legacy_fixture_image_codes() -> set[str]:
    return _list_image_codes(Path(settings.fixture_image_dir))


def guess_fixture_image_media_type(image_path: Path) -> str:
    return _MEDIA_TYPES.get(image_path.suffix.lower(), "application/octet-stream")


def ensure_fixture_image_dir(customer_id: int) -> Path:
    image_dir = _fixture_image_dir(customer_id)
    image_dir.mkdir(parents=True, exist_ok=True)
    return image_dir


def resolve_fixture_image_suffix(content_type: str | None, filename: str | None = None) -> str | None:
    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type in _CONTENT_TYPE_SUFFIXES:
        return _CONTENT_TYPE_SUFFIXES[normalized_content_type]
    suffix = Path(filename or "").suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        return suffix
    return None


def delete_fixture_image(customer_id: int, fixture_code: str) -> None:
    image_path = resolve_fixture_image_path(customer_id, fixture_code)
    if image_path is not None:
        image_path.unlink(missing_ok=True)


def delete_legacy_fixture_image(fixture_code: str) -> None:
    image_path = resolve_legacy_fixture_image_path(fixture_code)
    if image_path is not None:
        image_path.unlink(missing_ok=True)


def save_fixture_image(
    customer_id: int,
    fixture_code: str,
    content: bytes,
    *,
    content_type: str | None = None,
    filename: str | None = None,
) -> Path:
    suffix = resolve_fixture_image_suffix(content_type, filename)
    if suffix is None:
        raise ValueError("Unsupported fixture image type")
    code = _validate_fixture_code(fixture_code)
    image_dir = ensure_fixture_image_dir(customer_id)
    target_path = image_dir / f"{code}{suffix}"
    with NamedTemporaryFile(dir=image_dir, prefix=f".{code}-", suffix=".tmp", delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        temporary_path.replace(target_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    for old_suffix in _IMAGE_SUFFIXES:
        old_path = image_dir / f"{code}{old_suffix}"
        if old_path != target_path:
            old_path.unlink(missing_ok=True)
    return target_path


def rename_fixture_image(
    before_customer_id: int,
    before_code: str,
    after_customer_id: int,
    after_code: str,
    *,
    allow_legacy_source: bool = False,
) -> FixtureImageRename | None:
    if before_customer_id == after_customer_id and before_code == after_code:
        return None
    source_path = resolve_fixture_image_path(before_customer_id, before_code)
    if source_path is None and allow_legacy_source:
        source_path = resolve_legacy_fixture_image_path(before_code)
    if source_path is None:
        return None

    target_dir = ensure_fixture_image_dir(after_customer_id)
    target_code = _validate_fixture_code(after_code)
    if _resolve_image_in_dir(target_dir, target_code) is not None:
        raise ValueError("Target fixture image already exists")
    target_path = target_dir / f"{target_code}{source_path.suffix.lower()}"
    source_path.replace(target_path)
    return FixtureImageRename(source_path=source_path, target_path=target_path)


def rollback_fixture_image_rename(rename: FixtureImageRename | None) -> None:
    if rename is None or not rename.target_path.is_file():
        return
    rename.source_path.parent.mkdir(parents=True, exist_ok=True)
    rename.target_path.replace(rename.source_path)
