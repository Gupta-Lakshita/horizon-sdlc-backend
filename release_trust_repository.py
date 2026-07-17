"""Persistence and serialization for the frozen Release Trust evidence contract."""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import Artifact, PolicyEvaluation, Promotion, Provenance, ReleaseRun, SBOM, ScanEvidence, Signature


SEED_RELEASES = [
    {"release": {"release_id": "rel-2026-07-001", "application": "horizon-sdlc-platform", "environment": "dev", "build_number": 101, "build_time": "2026-07-16T10:15:00Z", "commit_sha": "8f14e45f", "branch": "main"}, "artifact": {"image_name": "horizon-sdlc-platform", "image_tag": "2026.07.16-101", "image_digest": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "registry": "local-dev"}, "sbom": {"status": "verified", "format": "spdx-json"}, "signature": {"status": "verified", "provider": "cosign"}, "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "pass", "critical": 0, "high": 0}, "policy_evaluation": {"overall_decision": "pass", "passed_rules": 8, "warning_rules": 0, "blocked_rules": 0}, "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "dev", "promoted_at": "2026-07-16T10:35:00Z"}]}},
    {"release": {"release_id": "rel-2026-07-002", "application": "horizon-runner", "environment": "dev", "build_number": 102, "build_time": "2026-07-16T11:05:00Z", "commit_sha": "c9f0f895", "branch": "main"}, "artifact": {"image_name": "horizon-runner", "image_tag": "2026.07.16-102", "image_digest": "sha256:3a6eb0790f39ac87c94f3856b2dd2c5d110e6811602261a9a923d3bb23adc8b7", "registry": "local-dev"}, "sbom": {"status": "generated", "format": "cyclonedx-json"}, "signature": {"status": "verified", "provider": "cosign"}, "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "warn", "critical": 0, "high": 1}, "policy_evaluation": {"overall_decision": "warn", "passed_rules": 7, "warning_rules": 1, "blocked_rules": 0}, "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible_with_warnings", "promotion_history": [{"environment": "dev", "promoted_at": "2026-07-16T11:25:00Z"}]}},
    {"release": {"release_id": "rel-2026-07-003", "application": "license-service", "environment": "dev", "build_number": 103, "build_time": "2026-07-16T11:45:00Z", "commit_sha": "45c48cce", "branch": "feature/release-trust"}, "artifact": {"image_name": "license-service", "image_tag": "2026.07.16-103", "image_digest": "sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", "registry": "local-dev"}, "sbom": {"status": "missing", "format": None}, "signature": {"status": "failed", "provider": "cosign"}, "provenance": {"status": "failed", "slsa_level": None}, "scan_evidence": {"status": "failed", "critical": 1, "high": 3}, "policy_evaluation": {"overall_decision": "block", "passed_rules": 4, "warning_rules": 2, "blocked_rules": 2}, "promotion": {"current_environment": "dev", "promotion_eligibility": "blocked", "promotion_history": []}},
]


_LOAD_OPTIONS = [joinedload(getattr(ReleaseRun, name)) for name in ("artifact", "sbom", "signature", "provenance", "scan_evidence", "policy_evaluation", "promotion")]


def _detail(run: ReleaseRun) -> Dict[str, Any]:
    return {"release": {key: getattr(run, key) for key in ("release_id", "application", "environment", "build_number", "build_time", "commit_sha", "branch")}, "artifact": {key: getattr(run.artifact, key) for key in ("image_name", "image_tag", "image_digest", "registry")}, "sbom": {key: getattr(run.sbom, key) for key in ("status", "format")}, "signature": {key: getattr(run.signature, key) for key in ("status", "provider")}, "provenance": {key: getattr(run.provenance, key) for key in ("status", "slsa_level")}, "scan_evidence": {key: getattr(run.scan_evidence, key) for key in ("status", "critical", "high")}, "policy_evaluation": {key: getattr(run.policy_evaluation, key) for key in ("overall_decision", "passed_rules", "warning_rules", "blocked_rules")}, "promotion": {"current_environment": run.promotion.current_environment, "promotion_eligibility": run.promotion.promotion_eligibility, "promotion_history": json.loads(run.promotion.promotion_history)}}


def _add_release(session, payload: Dict[str, Any]) -> ReleaseRun:
    run = ReleaseRun(**payload["release"])
    session.add(run); session.flush()
    run.artifact = Artifact(**payload["artifact"]); run.sbom = SBOM(**payload["sbom"]); run.signature = Signature(**payload["signature"]); run.provenance = Provenance(**payload["provenance"]); run.scan_evidence = ScanEvidence(**payload["scan_evidence"]); run.policy_evaluation = PolicyEvaluation(**payload["policy_evaluation"])
    promotion = dict(payload["promotion"]); promotion["promotion_history"] = json.dumps(promotion["promotion_history"]); run.promotion = Promotion(**promotion)
    return run


def seed_release_trust_data() -> None:
    with SessionLocal() as session:
        if session.query(ReleaseRun.id).first() is None:
            for payload in SEED_RELEASES: _add_release(session, payload)
            session.commit()


def get_release_runs() -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        runs = session.query(ReleaseRun).options(*_LOAD_OPTIONS).order_by(ReleaseRun.id).all()
        return [{"id": run.release_id, "release_id": run.release_id, "commit_sha": run.commit_sha, "image_digest": run.artifact.image_digest, "policy_status": run.policy_evaluation.overall_decision, "sbom_status": run.sbom.status} for run in runs]


def get_release_by_id(release_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        run = session.query(ReleaseRun).options(*_LOAD_OPTIONS).filter(ReleaseRun.release_id == release_id).one_or_none()
        return _detail(run) if run else None


def create_release(payload: Dict[str, Any]) -> Dict[str, Any]:
    with SessionLocal() as session:
        run = _add_release(session, payload); session.commit(); session.refresh(run)
        return _detail(run)


def update_release(release_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        run = session.query(ReleaseRun).options(*_LOAD_OPTIONS).filter(ReleaseRun.release_id == release_id).one_or_none()
        if not run: return None
        for group, obj in (("release", run), ("artifact", run.artifact), ("sbom", run.sbom), ("signature", run.signature), ("provenance", run.provenance), ("scan_evidence", run.scan_evidence), ("policy_evaluation", run.policy_evaluation)):
            for key, value in payload.get(group, {}).items(): setattr(obj, key, value)
        for key, value in payload.get("promotion", {}).items(): setattr(run.promotion, key, json.dumps(value) if key == "promotion_history" else value)
        session.commit(); return _detail(run)
