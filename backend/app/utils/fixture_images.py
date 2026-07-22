from pathlib import Path

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


def resolve_fixture_image_path(fixture_code: str) -> Path | None:
    image_dir = Path(settings.fixture_image_dir)
    for suffix in _IMAGE_SUFFIXES:
        candidate = image_dir / f"{fixture_code}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def guess_fixture_image_media_type(image_path: Path) -> str:
    return _MEDIA_TYPES.get(image_path.suffix.lower(), "application/octet-stream")


def ensure_fixture_image_dir() -> Path:
    image_dir = Path(settings.fixture_image_dir)
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


def delete_fixture_image(fixture_code: str) -> None:
    image_path = resolve_fixture_image_path(fixture_code)
    if image_path is not None:
        image_path.unlink(missing_ok=True)


def save_fixture_image(fixture_code: str, content: bytes, *, content_type: str | None = None, filename: str | None = None) -> Path:
    suffix = resolve_fixture_image_suffix(content_type, filename)
    if suffix is None:
        raise ValueError("Unsupported fixture image type")
    image_dir = ensure_fixture_image_dir()
    delete_fixture_image(fixture_code)
    target_path = image_dir / f"{fixture_code}{suffix}"
    target_path.write_bytes(content)
    return target_path


def rename_fixture_image(before_code: str, after_code: str) -> None:
    if before_code == after_code:
        return
    image_path = resolve_fixture_image_path(before_code)
    if image_path is None:
        return
    ensure_fixture_image_dir()
    delete_fixture_image(after_code)
    image_path.replace(image_path.with_name(f"{after_code}{image_path.suffix.lower()}"))
