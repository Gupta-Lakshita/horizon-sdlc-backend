"""Release Trust ingestion orchestration and request validation."""
from typing import Dict, Any

from fastapi import HTTPException

from release_trust_repository import create_release, get_release_by_id


REQUIRED_SECTIONS = (
    "release", "artifact", "sbom", "signature", "provenance",
    "scan_evidence", "policy_evaluation", "promotion",
)


def ingest_release_trust(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Persist one complete evidence payload through the repository layer."""
    release = payload.get("release", {})
    release_id = release.get("release_id")
    if get_release_by_id(release_id) is not None:
        raise HTTPException(status_code=409, detail="release_id already exists")

    # This check also protects callers that use the service without FastAPI.
    missing = [section for section in REQUIRED_SECTIONS if not payload.get(section)]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_sections": missing})

    try:
        return create_release(payload)
    except Exception as exc:
        # SQLite's unique constraint is the final protection against a race.
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="release_id already exists") from exc
        raise
