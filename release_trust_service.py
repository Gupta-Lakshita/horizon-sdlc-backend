"""Release Trust ingestion orchestration and request validation."""
from typing import Dict, Any

from fastapi import HTTPException

from release_trust_repository import create_promotion_decision, create_release, get_release_by_id
from policy_engine import PolicyEngine
from promotion_engine import PromotionEngine


REQUIRED_SECTIONS = (
    "release", "artifact", "sbom", "signature", "provenance",
    "scan_evidence", "promotion",
)

policy_engine = PolicyEngine()
promotion_engine = PromotionEngine()


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

    # Build a distinct persistence payload so a caller-supplied legacy policy
    # section can never reach the repository.
    computed_evaluation = policy_engine.evaluate(payload)
    payload_for_persistence = {
        **payload,
        "policy_evaluation": computed_evaluation,
    }

    try:
        return create_release(payload_for_persistence)
    except Exception as exc:
        # SQLite's unique constraint is the final protection against a race.
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="release_id already exists") from exc
        raise


def get_release_trust_detail(release_id: str) -> Dict[str, Any]:
    """Return a detail record with structured policy rules for old and new rows."""
    release = get_release_by_id(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")

    policy = release.setdefault("policy_evaluation", {})
    if not policy.get("rules"):
        # A process started before the migration can still encounter a legacy
        # row. Return one internally consistent computed object; normal app
        # startup persists this same value through the repository backfill.
        release["policy_evaluation"] = policy_engine.evaluate(release)
    return release


def request_promotion(release_id: str, actor: str = "system") -> Dict[str, Any]:
    """Apply the deployment gate to the persisted policy; never request policy input."""
    if not release_id or not release_id.strip():
        raise HTTPException(status_code=422, detail="release_id is required")
    release = get_release_by_id(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    try:
        decision = promotion_engine.evaluate(release["policy_evaluation"].get("overall_decision"))
        persisted = create_promotion_decision(release_id, decision, actor or "system")
    except ValueError as exc:
        if str(exc) == "promotion already exists":
            raise HTTPException(status_code=409, detail="promotion already exists") from exc
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if persisted is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return persisted
