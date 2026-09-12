"""Filesystem operations constrained to Batcave storage roots."""

from __future__ import annotations

import shutil
from io import BytesIO
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


PHOTO_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".webp": "WEBP",
}
Image.MAX_IMAGE_PIXELS = 30_000_000


class InvalidPathError(ValueError):
    pass


def resolve_path(root: Path, relative_path: str, *, allow_root: bool = True) -> Path:
    relative_path = relative_path.strip().strip("/")
    root_resolved = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as error:
        raise InvalidPathError("Invalid path.") from error
    if not allow_root and candidate == root_resolved:
        raise InvalidPathError("The Files root cannot be modified.")
    return candidate


def clean_name(raw_name: str) -> str:
    return secure_filename(raw_name.strip())


def save_new_upload(uploaded, target_dir: Path, filename: str) -> Path:
    """Create a new file exclusively; never replace an existing destination."""
    destination = target_dir / filename
    try:
        with destination.open("xb") as target:
            shutil.copyfileobj(uploaded.stream, target)
    except FileExistsError:
        raise FileExistsError(f"{filename} already exists. It was not overwritten.")
    except Exception:
        # A failed stream must not leave a partial file that looks valid.
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        raise
    return destination


def validate_photo(uploaded, filename: str) -> None:
    extension = Path(filename).suffix.lower()
    expected_format = PHOTO_FORMATS.get(extension)
    if expected_format is None:
        raise ValueError("That file type is not supported as a photo.")

    try:
        image_bytes = uploaded.stream.read()
        # Pillow owns this short-lived in-memory stream, so it cannot keep the
        # request's spooled upload file open on Windows after validation.
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            image.verify()
        if image_format != expected_format:
            raise ValueError("The image contents do not match its filename.")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("The uploaded file is not a valid supported image.") from error
    finally:
        uploaded.stream.seek(0)


def is_photo_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in PHOTO_FORMATS


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def file_info(path: Path, relative_to: Path) -> dict:
    stat = path.stat()
    return {
        "name": path.name,
        "path": path.relative_to(relative_to).as_posix(),
        "size": format_size(stat.st_size),
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).astimezone().strftime("%b %d, %Y %H:%M"),
        "modified_timestamp": stat.st_mtime,
        "type": f"{path.suffix[1:].upper()} file" if path.suffix else "File",
        "is_folder": False,
    }


def folder_info(path: Path, relative_to: Path) -> dict:
    """Return display metadata without recursively calculating directory size."""
    stat = path.stat()
    return {
        "name": path.name,
        "path": path.relative_to(relative_to).as_posix(),
        "size": "—",
        "size_bytes": 0,
        "modified": datetime.fromtimestamp(stat.st_mtime).astimezone().strftime("%b %d, %Y %H:%M"),
        "modified_timestamp": stat.st_mtime,
        "type": "Folder",
        "is_folder": True,
    }


def storage_usage(path: Path) -> dict:
    """Report the capacity of the filesystem holding path without walking files."""
    usage = shutil.disk_usage(path)
    return {
        "used": format_size(usage.used),
        "free": format_size(usage.free),
        "total": format_size(usage.total),
    }
