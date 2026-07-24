"""Release Trust ingestion orchestration and request validation."""
from typing import Dict, Any

from fastapi import HTTPException

from release_trust_repository import create_promotion_decision, create_release, get_release_by_id, get_release_runs
from policy_engine import PolicyEngine
from promotion_engine import PromotionEngine
from storage import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore, ObjectStoreError, get_default_object_store


policy_engine = PolicyEngine()
promotion_engine = PromotionEngine()


def _store() -> ObjectStore:
    return get_default_object_store()


def _store_evidence(payload: Dict[str, Any], object_store: ObjectStore) -> Dict[str, str]:
    release_id = payload["release"]["release_id"]
    stored = []
    names = (("sbom", "sbom_reference"), ("signature", "signature_reference"), ("provenance", "provenance_reference"), ("scan_evidence", "scan_reference"))
    try:
        references = {}
        for payload_key, reference_key in names:
            reference = object_store.upload_json(release_id, payload_key.replace("_evidence", ""), payload[payload_key])
            references[reference_key] = reference
            stored.append(reference)
        # Reserved for a future aggregated evidence document.
        references["bundle_reference"] = None
        return references
    except ObjectStoreError:
        for reference in stored:
            try:
                object_store.delete(reference)
            except ObjectStoreError:
                pass
        raise


def ingest_release_trust(payload: Dict[str, Any], object_store: ObjectStore | None = None) -> Dict[str, Any]:
    """Persist CI evidence or a normalized minimal manual-test payload."""
    release = payload.get("release", {})
    release_id = release.get("release_id")
    if not release_id or not str(release_id).strip():
        raise HTTPException(status_code=422, detail="release.release_id is required")
    store = object_store or _store()
    try:
        store.build_reference(release_id, "sbom")
    except ObjectStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if get_release_by_id(release_id, store) is not None:
        raise HTTPException(status_code=409, detail="release_id already exists")

    # Build a distinct persistence payload so a caller-supplied legacy policy
    # section can never reach the repository.
    computed_evaluation = policy_engine.evaluate(payload)
    payload_for_persistence = {
        **payload,
        "policy_evaluation": computed_evaluation,
    }

    references = {}
    try:
        references = _store_evidence(payload_for_persistence, store)
        payload_for_persistence["evidence_references"] = references
        return create_release(payload_for_persistence, store)
    except ObjectAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="evidence already exists for release_id") from exc
    except ObjectStoreError as exc:
        raise HTTPException(status_code=500, detail=f"evidence storage failure: {exc}") from exc
    except Exception as exc:
        for reference in references.values():
            if reference:
                try: store.delete(reference)
                except ObjectStoreError: pass
        # SQLite's unique constraint is the final protection against a race.
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="release_id already exists") from exc
        raise


def get_release_trust_detail(release_id: str, object_store: ObjectStore | None = None) -> Dict[str, Any]:
    """Return a detail record with structured policy rules for old and new rows."""
    try:
        release = get_release_by_id(release_id, object_store or _store())
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Release Trust evidence not found") from exc
    except (ObjectStoreError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Release Trust evidence unavailable: {exc}") from exc
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")

    policy = release.setdefault("policy_evaluation", {})
    if not policy.get("rules"):
        # A process started before the migration can still encounter a legacy
        # row. Return one internally consistent computed object; normal app
        # startup persists this same value through the repository backfill.
        release["policy_evaluation"] = policy_engine.evaluate(release)
    return release


def get_release_trust_runs(object_store: ObjectStore | None = None):
    try:
        return get_release_runs(object_store or _store())
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Release Trust evidence not found") from exc
    except (ObjectStoreError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Release Trust evidence unavailable: {exc}") from exc


def request_promotion(release_id: str, actor: str = "system", object_store: ObjectStore | None = None) -> Dict[str, Any]:
    """Apply the deployment gate to the persisted policy; never request policy input."""
    if not release_id or not release_id.strip():
        raise HTTPException(status_code=422, detail="release_id is required")
    store = object_store or _store()
    try:
        release = get_release_by_id(release_id, store)
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Release Trust evidence not found") from exc
    except (ObjectStoreError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Release Trust evidence unavailable: {exc}") from exc
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    try:
        decision = promotion_engine.evaluate(release["policy_evaluation"].get("overall_decision"))
        persisted = create_promotion_decision(release_id, decision, actor or "system", store)
    except ValueError as exc:
        if str(exc) == "promotion already exists":
            raise HTTPException(status_code=409, detail="promotion already exists") from exc
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if persisted is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return persisted
