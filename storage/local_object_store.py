"""Filesystem-backed ObjectStore used for local and container deployments."""
import json
import os
import re
from pathlib import Path
from typing import Any

from .object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore, ObjectStoreError


_RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_OBJECT_NAMES = {"sbom", "signature", "provenance", "scan", "bundle"}


class LocalObjectStore(ObjectStore):
    """Store immutable JSON evidence under ``<root>/<release_id>``."""

    def __init__(self, root: str | Path | None = None):
        configured_root = os.getenv("EVIDENCE_DATA_PATH")
        database_path = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH")
        default_root = Path(configured_root) if configured_root else (
            Path(database_path).parent / "evidence" if database_path else Path("data") / "evidence"
        )
        self.root = Path(root) if root is not None else default_root

    def _validate_release_id(self, release_id: str) -> str:
        value = str(release_id or "")
        if not _RELEASE_ID.fullmatch(value):
            raise ObjectStoreError("invalid release ID for evidence storage")
        return value

    def _validate_object_name(self, object_name: str) -> str:
        name = str(object_name or "").removesuffix(".json")
        if name not in _OBJECT_NAMES:
            raise ObjectStoreError("invalid evidence object name")
        return name

    def build_reference(self, release_id: str, object_name: str) -> str:
        return f"evidence/{self._validate_release_id(release_id)}/{self._validate_object_name(object_name)}.json"

    def _path(self, reference: str) -> Path:
        if not isinstance(reference, str) or not reference.startswith("evidence/"):
            raise ObjectStoreError("invalid evidence reference")
        parts = reference.split("/")
        if len(parts) != 3:
            raise ObjectStoreError("invalid evidence reference")
        expected = self.build_reference(parts[1], parts[2])
        if reference != expected:
            raise ObjectStoreError("invalid evidence reference")
        return self.root / parts[1] / parts[2]

    def upload_json(self, release_id: str, object_name: str, payload: Any) -> str:
        reference = self.build_reference(release_id, object_name)
        path = self._path(reference)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation makes evidence immutable and duplicate-safe.
            with path.open("x", encoding="utf-8") as output:
                json.dump(payload, output, ensure_ascii=False)
            return reference
        except FileExistsError as exc:
            raise ObjectAlreadyExistsError(f"evidence object already exists: {reference}") from exc
        except (OSError, TypeError, ValueError) as exc:
            raise ObjectStoreError(f"unable to store evidence: {exc}") from exc

    def download_json(self, reference: str) -> Any:
        path = self._path(reference)
        try:
            with path.open("r", encoding="utf-8") as source:
                return json.load(source)
        except FileNotFoundError as exc:
            raise ObjectNotFoundError(f"evidence object not found: {reference}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise ObjectStoreError(f"unable to read evidence: {exc}") from exc

    def exists(self, reference: str) -> bool:
        try:
            return self._path(reference).is_file()
        except ObjectStoreError:
            return False

    def delete(self, reference: str) -> None:
        path = self._path(reference)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise ObjectStoreError(f"unable to delete evidence: {exc}") from exc
