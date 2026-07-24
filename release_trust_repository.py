"""Persistence and serialization for the frozen Release Trust evidence contract."""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import Artifact, PolicyEvaluation, Promotion, PromotionDecision, Provenance, ReleaseRun, SBOM, ScanEvidence, Signature
from storage.object_store import ObjectStore


SEED_RELEASES = [
    {"release": {"release_id": "rel-2026-07-001", "application": "horizon-sdlc-platform", "environment": "dev", "build_number": 101, "build_time": "2026-07-16T10:15:00Z", "commit_sha": "8f14e45f", "branch": "main"}, "artifact": {"image_name": "horizon-sdlc-platform", "image_tag": "2026.07.16-101", "image_digest": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "registry": "local-dev"}, "sbom": {"status": "verified", "format": "spdx-json"}, "signature": {"status": "verified", "provider": "cosign"}, "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "pass", "critical": 0, "high": 0}, "policy_evaluation": {"overall_decision": "pass", "passed_rules": 8, "warning_rules": 0, "blocked_rules": 0}, "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "dev", "promoted_at": "2026-07-16T10:35:00Z"}]}},
    {"release": {"release_id": "rel-2026-07-002", "application": "horizon-runner", "environment": "dev", "build_number": 102, "build_time": "2026-07-16T11:05:00Z", "commit_sha": "c9f0f895", "branch": "main"}, "artifact": {"image_name": "horizon-runner", "image_tag": "2026.07.16-102", "image_digest": "sha256:3a6eb0790f39ac87c94f3856b2dd2c5d110e6811602261a9a923d3bb23adc8b7", "registry": "local-dev"}, "sbom": {"status": "generated", "format": "cyclonedx-json"}, "signature": {"status": "verified", "provider": "cosign"}, "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "warn", "critical": 0, "high": 1}, "policy_evaluation": {"overall_decision": "warn", "passed_rules": 7, "warning_rules": 1, "blocked_rules": 0}, "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible_with_warnings", "promotion_history": [{"environment": "dev", "promoted_at": "2026-07-16T11:25:00Z"}]}},
    {"release": {"release_id": "rel-2026-07-003", "application": "license-service", "environment": "dev", "build_number": 103, "build_time": "2026-07-16T11:45:00Z", "commit_sha": "45c48cce", "branch": "feature/release-trust"}, "artifact": {"image_name": "license-service", "image_tag": "2026.07.16-103", "image_digest": "sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", "registry": "local-dev"}, "sbom": {"status": "missing", "format": None}, "signature": {"status": "failed", "provider": "cosign"}, "provenance": {"status": "failed", "slsa_level": None}, "scan_evidence": {"status": "failed", "critical": 1, "high": 3}, "policy_evaluation": {"overall_decision": "block", "passed_rules": 4, "warning_rules": 2, "blocked_rules": 2}, "promotion": {"current_environment": "dev", "promotion_eligibility": "blocked", "promotion_history": []}},
]


_LOAD_OPTIONS = [joinedload(getattr(ReleaseRun, name)) for name in ("artifact", "sbom", "signature", "provenance", "scan_evidence", "policy_evaluation", "promotion", "promotion_decision")]


def _evidence(run: ReleaseRun, object_store: Optional[ObjectStore]) -> Dict[str, Dict[str, Any]]:
    """Hydrate Phase 9 references, while retaining reads of pre-Phase-9 rows."""
    references = {
        "sbom": run.sbom_reference,
        "signature": run.signature_reference,
        "provenance": run.provenance_reference,
        "scan_evidence": run.scan_reference,
    }
    if any(references.values()):
        if object_store is None:
            raise RuntimeError("an ObjectStore is required to hydrate evidence references")
        if not all(references.values()):
            raise RuntimeError("stored release has incomplete evidence references")
        return {name: object_store.download_json(reference) for name, reference in references.items()}
    return {
        "sbom": {key: getattr(run.sbom, key) for key in ("status", "format")},
        "signature": {key: getattr(run.signature, key) for key in ("status", "provider")},
        "provenance": {key: getattr(run.provenance, key) for key in ("status", "slsa_level")},
        "scan_evidence": {key: getattr(run.scan_evidence, key) for key in ("status", "critical", "high")},
    }


def _detail(run: ReleaseRun, object_store: Optional[ObjectStore] = None) -> Dict[str, Any]:
    policy = {key: getattr(run.policy_evaluation, key) for key in ("overall_decision", "passed_rules", "warning_rules", "blocked_rules")}
    if run.policy_evaluation.summary is not None:
        policy["status"] = run.policy_evaluation.overall_decision.upper()
        policy["summary"] = run.policy_evaluation.summary
        policy["rules"] = json.loads(run.policy_evaluation.rules or "[]")
    decision = None
    if run.promotion_decision:
        decision = {key: getattr(run.promotion_decision, key) for key in ("promotion_status", "policy_status", "reason", "timestamp", "actor")}
        decision["timestamp"] = decision["timestamp"].isoformat()
        decision["deployment_permitted"] = decision["promotion_status"] == "ALLOW"
    evidence = _evidence(run, object_store)
    return {"release": {key: getattr(run, key) for key in ("release_id", "application", "environment", "build_number", "build_time", "commit_sha", "branch")}, "artifact": {key: getattr(run.artifact, key) for key in ("image_name", "image_tag", "image_digest", "registry")}, **evidence, "policy_evaluation": policy, "promotion": {"current_environment": run.promotion.current_environment, "promotion_eligibility": run.promotion.promotion_eligibility, "promotion_history": json.loads(run.promotion.promotion_history)}, "promotion_decision": decision}


def _add_release(session, payload: Dict[str, Any]) -> ReleaseRun:
    references = payload.get("evidence_references")
    run = ReleaseRun(**payload["release"], **(references or {}))
    session.add(run); session.flush()
    policy = dict(payload["policy_evaluation"])
    policy["overall_decision"] = policy.get("overall_decision", policy.get("status", "pending")).lower()
    policy.pop("status", None)
    policy["rules"] = json.dumps(policy["rules"]) if policy.get("rules") is not None else None
    run.artifact = Artifact(**payload["artifact"])
    # Only legacy callers/seed data persist evidence payloads in SQLite.
    if not references:
        run.sbom = SBOM(**payload["sbom"]); run.signature = Signature(**payload["signature"])
        run.provenance = Provenance(**payload["provenance"]); run.scan_evidence = ScanEvidence(**payload["scan_evidence"])
    run.policy_evaluation = PolicyEvaluation(**policy)
    promotion = dict(payload["promotion"]); promotion["promotion_history"] = json.dumps(promotion["promotion_history"]); run.promotion = Promotion(**promotion)
    return run


def seed_release_trust_data() -> None:
    with SessionLocal() as session:
        if session.query(ReleaseRun.id).first() is None:
            for payload in SEED_RELEASES: _add_release(session, payload)
            session.commit()


def get_release_runs(object_store: Optional[ObjectStore] = None) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        runs = session.query(ReleaseRun).options(*_LOAD_OPTIONS).order_by(ReleaseRun.id).all()
        return [{"id": run.release_id, "release_id": run.release_id, "commit_sha": run.commit_sha, "image_digest": run.artifact.image_digest, "policy_status": run.policy_evaluation.overall_decision, "promotion_status": run.promotion_decision.promotion_status if run.promotion_decision else None, "sbom_status": _evidence(run, object_store)["sbom"]["status"]} for run in runs]


def backfill_policy_evaluations(policy_engine, object_store: Optional[ObjectStore] = None) -> None:
    """Replace legacy policy fields with the single current engine result.

    This runs after the additive schema migration. Re-evaluating every stored
    row also corrects values written by the pre-Phase-7 path. Normal reads do
    not re-evaluate a release; persisted decisions remain the source for both
    API views.
    """
    with SessionLocal() as session:
        runs = session.query(ReleaseRun).options(*_LOAD_OPTIONS).all()
        changed = False
        for run in runs:
            # New service-ingested rows already have the engine result. Avoid
            # reading external evidence during startup just to backfill them.
            if run.policy_evaluation.rules is not None:
                continue
            evaluation = policy_engine.evaluate(_detail(run, object_store))
            policy = run.policy_evaluation
            policy.overall_decision = evaluation["overall_decision"]
            policy.passed_rules = evaluation["passed_rules"]
            policy.warning_rules = evaluation["warning_rules"]
            policy.blocked_rules = evaluation["blocked_rules"]
            policy.summary = evaluation["summary"]
            policy.rules = json.dumps(evaluation["rules"])
            changed = True
        if changed:
            session.commit()


def get_release_by_id(release_id: str, object_store: Optional[ObjectStore] = None) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        run = session.query(ReleaseRun).options(*_LOAD_OPTIONS).filter(ReleaseRun.release_id == release_id).one_or_none()
        return _detail(run, object_store) if run else None


def create_release(payload: Dict[str, Any], object_store: Optional[ObjectStore] = None) -> Dict[str, Any]:
    with SessionLocal() as session:
        run = _add_release(session, payload); session.commit(); session.refresh(run)
        return _detail(run, object_store)


def create_promotion_decision(release_id: str, decision: Dict[str, Any], actor: str, object_store: Optional[ObjectStore] = None) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        run = session.query(ReleaseRun).options(*_LOAD_OPTIONS).filter(ReleaseRun.release_id == release_id).one_or_none()
        if run is None:
            return None
        if run.promotion_decision is not None:
            raise ValueError("promotion already exists")
        run.promotion_decision = PromotionDecision(
            promotion_status=decision["promotion_status"], policy_status=decision["policy_status"],
            reason=decision["reason"], actor=actor,
        )
        session.commit()
        session.refresh(run)
        return _detail(run, object_store)["promotion_decision"]


def get_promotion_decisions() -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        decisions = session.query(PromotionDecision).join(ReleaseRun).order_by(PromotionDecision.id).all()
        return [{"release_id": decision.release_run.release_id, "promotion_status": decision.promotion_status,
                 "policy_status": decision.policy_status, "reason": decision.reason,
                 "timestamp": decision.timestamp.isoformat(), "actor": decision.actor,
                 "deployment_permitted": decision.promotion_status == "ALLOW"} for decision in decisions]


def get_promotion_decision(release_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        decision = session.query(PromotionDecision).join(ReleaseRun).filter(ReleaseRun.release_id == release_id).one_or_none()
        if decision is None:
            return None
        return {"release_id": release_id, "promotion_status": decision.promotion_status,
                "policy_status": decision.policy_status, "reason": decision.reason,
                "timestamp": decision.timestamp.isoformat(), "actor": decision.actor,
                "deployment_permitted": decision.promotion_status == "ALLOW"}


def update_release(release_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        run = session.query(ReleaseRun).options(*_LOAD_OPTIONS).filter(ReleaseRun.release_id == release_id).one_or_none()
        if not run: return None
        for group, obj in (("release", run), ("artifact", run.artifact), ("sbom", run.sbom), ("signature", run.signature), ("provenance", run.provenance), ("scan_evidence", run.scan_evidence), ("policy_evaluation", run.policy_evaluation)):
            for key, value in payload.get(group, {}).items(): setattr(obj, key, value)
        for key, value in payload.get("promotion", {}).items(): setattr(run.promotion, key, json.dumps(value) if key == "promotion_history" else value)
        session.commit(); return _detail(run)
