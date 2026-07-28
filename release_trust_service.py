"""Release Trust ingestion orchestration and request validation."""
from typing import Dict, Any

from fastapi import HTTPException

from release_trust_repository import add_pipeline_event, add_runner_evidence, add_runner_execution, create_promotion_decision, create_release, get_release_by_id, get_release_runs, get_runner_ingestion_status, release_is_visible_to_principal, resolve_platform_application, update_runner_execution_status
from policy_engine import PolicyEngine
from promotion_engine import PromotionEngine
from findings_correlation import correlate_findings
from promotion_preflight import PromotionPreflightService, TrustScoreCalculator
from storage import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore, ObjectStoreError


policy_engine = PolicyEngine()
promotion_engine = PromotionEngine()
preflight_service = PromotionPreflightService()
trust_score_calculator = TrustScoreCalculator()
_object_store: ObjectStore | None = None


def configure_object_store(object_store: ObjectStore) -> None:
    """Inject the startup-selected provider into Release Trust business logic."""
    global _object_store
    _object_store = object_store


def _store() -> ObjectStore:
    if _object_store is None:
        raise RuntimeError("Release Trust ObjectStore dependency has not been configured")
    return _object_store


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
    try:
        application = resolve_platform_application(release)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if application:
        # Use the catalog's canonical name and persist its foreign-key link.
        release["application_id"] = application["id"]
        release["application"] = application["name"]
    store = object_store or _store()
    try:
        store.build_reference(release_id, "sbom")
    except ObjectStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if get_release_by_id(release_id, store) is not None:
        raise HTTPException(status_code=409, detail="release_id already exists")

    # Build a distinct persistence payload so a caller-supplied legacy policy
    # section can never reach the repository.
    payload["findings"] = correlate_findings(payload)
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


def get_release_trust_detail(release_id: str, object_store: ObjectStore | None = None, principal=None) -> Dict[str, Any]:
    """Return a detail record with structured policy rules for old and new rows."""
    try:
        release = get_release_by_id(release_id, object_store or _store())
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Release Trust evidence not found") from exc
    except (ObjectStoreError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Release Trust evidence unavailable: {exc}") from exc
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")

    if principal is not None and not release_is_visible_to_principal(release_id, principal):
        raise HTTPException(status_code=403, detail="You do not have access to this application's release.")
    policy = release.setdefault("policy_evaluation", {})
    if not policy.get("rules"):
        # A process started before the migration can still encounter a legacy
        # row. Return one internally consistent computed object; normal app
        # startup persists this same value through the repository backfill.
        release["policy_evaluation"] = policy_engine.evaluate(release)
    release["findings"] = correlate_findings(release)
    # Evaluate findings-aware policy on the read model; old persisted policy
    # remains present and response fields are additive.
    release["policy_evaluation"] = policy_engine.evaluate(release)
    preflight = preflight_service.evaluate(release)
    release["promotion_preflight"] = preflight
    release["trust_score"] = trust_score_calculator.calculate(release, preflight)
    return release


def get_release_trust_runs(object_store: ObjectStore | None = None, principal=None):
    try:
        runs = get_release_runs(object_store or _store())
        return runs if principal is None else [run for run in runs if release_is_visible_to_principal(run["release_id"], principal)]
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Release Trust evidence not found") from exc
    except (ObjectStoreError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Release Trust evidence unavailable: {exc}") from exc


def request_promotion(release_id: str, actor: str = "system", object_store: ObjectStore | None = None, principal=None) -> Dict[str, Any]:
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
    if principal is not None and not release_is_visible_to_principal(release_id, principal):
        raise HTTPException(status_code=403, detail="You do not have access to this application's release.")
    try:
        release["findings"] = correlate_findings(release)
        release["policy_evaluation"] = policy_engine.evaluate(release)
        preflight = preflight_service.evaluate(release)
        decision = promotion_engine.evaluate(preflight["status"])
        decision["reason"] = "; ".join(preflight["blocking_reasons"]) if preflight["blocking_reasons"] else decision["reason"]
        persisted = create_promotion_decision(release_id, decision, actor or "system", store)
    except ValueError as exc:
        if str(exc) == "promotion already exists":
            raise HTTPException(status_code=409, detail="promotion already exists") from exc
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if persisted is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return persisted


def ingest_runner_release(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Adapt a v1 runner envelope to the canonical Release Trust service path."""
    build = contract.get("build", {})
    artifact = (contract.get("artifacts") or [{}])[0]
    try: build_number = int(build.get("number", 0))
    except (TypeError, ValueError): build_number = 0
    canonical = {"release": {"release_id": contract["release_id"], "application": contract["application"], "environment": contract.get("environment", "dev"), "build_number": build_number, "build_time": build.get("timestamp") or contract["execution"].get("started_at") or "runner", "commit_sha": contract.get("commit_sha", "unknown"), "branch": contract.get("branch", "unknown")},
                 "artifact": {"image_name": artifact.get("name") or "runner-artifact", "image_tag": artifact.get("version") or contract.get("tag") or "unknown", "image_digest": artifact.get("digest") or "unknown", "registry": artifact.get("uri") or "runner"},
                 "sbom": {"status": "missing"}, "signature": {"status": "missing"}, "provenance": {"status": "missing"}, "scan_evidence": {"status": "missing", "critical": 0, "high": 0}, "promotion": {"current_environment": contract.get("environment", "dev"), "promotion_eligibility": "pending", "promotion_history": []}}
    release = ingest_release_trust(canonical)
    add_runner_execution(contract["release_id"], contract["execution"], contract["contract_version"])
    for evidence in contract.get("evidence", []): add_runner_evidence(contract["release_id"], evidence)
    add_pipeline_event(contract["release_id"], {"event_type": "pipeline.started", "occurred_at": contract["execution"].get("started_at") or "runner", "payload": {"pipeline_id": contract["execution"]["pipeline_id"]}})
    return release


def publish_runner_evidence(release_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    result = add_runner_evidence(release_id, evidence)
    if result is None: raise HTTPException(status_code=404, detail="Release Trust run not found")
    add_pipeline_event(release_id, {"event_type": "evidence.uploaded", "occurred_at": evidence.get("occurred_at", "runner"), "payload": {"evidence_type": evidence["evidence_type"], "name": evidence["name"]}})
    return result


def update_runner_status(release_id: str, update: Dict[str, Any]) -> Dict[str, Any]:
    result = update_runner_execution_status(release_id, update)
    if result is None: raise HTTPException(status_code=404, detail="Runner ingestion not found")
    return result


def publish_runner_event(release_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    result = add_pipeline_event(release_id, event)
    if result is None: raise HTTPException(status_code=404, detail="Release Trust run not found")
    return result


def get_runner_status(release_id: str) -> Dict[str, Any]:
    result = get_runner_ingestion_status(release_id)
    if result is None: raise HTTPException(status_code=404, detail="Release Trust run not found")
    return result
