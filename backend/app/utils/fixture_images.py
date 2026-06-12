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


def resolve_fixture_image_path(fixture_code: str) -> Path | None:
    image_dir = Path(settings.fixture_image_dir)
    for suffix in _IMAGE_SUFFIXES:
        candidate = image_dir / f"{fixture_code}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def guess_fixture_image_media_type(image_path: Path) -> str:
    return _MEDIA_TYPES.get(image_path.suffix.lower(), "application/octet-stream")
