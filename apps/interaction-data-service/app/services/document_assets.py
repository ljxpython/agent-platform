from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path


_SAFE_SEGMENT_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_segment(value: str | None, *, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    normalized = _SAFE_SEGMENT_PATTERN.sub("_", text)
    normalized = normalized.strip("._")
    return normalized or fallback


def _guess_extension(filename: str | None, content_type: str | None) -> str:
    suffix = Path((filename or "").strip()).suffix
    if suffix:
        return suffix.lower()
    guessed = mimetypes.guess_extension((content_type or "").strip() or "application/pdf")
    if guessed:
        return guessed.lower()
    return ".bin"


def build_document_asset_relative_path(
    *,
    project_id: str,
    batch_id: str | None,
    asset_key: str,
    filename: str | None,
    content_type: str | None,
) -> str:
    project_segment = _safe_segment(project_id, fallback="project")
    batch_segment = _safe_segment(batch_id, fallback="default")
    key_segment = _safe_segment(asset_key, fallback="asset")
    extension = _guess_extension(filename, content_type)
    return f"test-case-service/{project_segment}/{batch_segment}/{key_segment}{extension}"


def write_document_asset(
    *,
    root_dir: str,
    project_id: str,
    batch_id: str | None,
    asset_key: str,
    filename: str,
    content_type: str,
    payload: bytes,
) -> dict[str, object]:
    relative_path = build_document_asset_relative_path(
        project_id=project_id,
        batch_id=batch_id,
        asset_key=asset_key,
        filename=filename,
        content_type=content_type,
    )
    root_path = Path(root_dir).expanduser().resolve()
    target_path = (root_path / relative_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(payload)
    return {
        "storage_path": relative_path,
        "filename": filename,
        "content_type": content_type,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def resolve_document_asset_path(root_dir: str, storage_path: str) -> Path:
    root_path = Path(root_dir).expanduser().resolve()
    candidate = (root_path / storage_path).resolve()
    if not str(candidate).startswith(str(root_path)):
        raise FileNotFoundError("document_asset_outside_root")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError("document_asset_not_found")
    return candidate


__all__ = [
    "build_document_asset_relative_path",
    "resolve_document_asset_path",
    "write_document_asset",
]
