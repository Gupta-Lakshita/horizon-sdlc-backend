"""Correlate existing Secure SDLC findings to a Release Trust release."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from database import SessionLocal
from models import Vulnerability

SEVERITIES = ("critical", "high", "medium", "low", "informational")


def _active_exception(finding: Vulnerability) -> bool:
    if str(finding.waiver_status or "").lower() not in {"approved", "active", "waived"}:
        return False
    if not finding.waiver_expiry:
        return True
    try:
        return datetime.fromisoformat(finding.waiver_expiry.replace("Z", "+00:00")) > datetime.now(timezone.utc)
    except ValueError:
        return False


def correlate_findings(release: Dict[str, Any]) -> Dict[str, Any]:
    """Use strongest available shared metadata, gracefully falling back to project.

    The source findings table intentionally remains the system of record; no
    duplicate vulnerability rows are created by Release Trust.
    """
    metadata, artifact = release.get("release", {}), release.get("artifact", {})
    app_id = (release.get("context") or {}).get("application_id")
    with SessionLocal() as session:
        query = session.query(Vulnerability)
        if app_id:
            query = query.filter(Vulnerability.application_id == app_id)
        rows = query.all()
    digest, commit = artifact.get("image_digest", ""), metadata.get("commit_sha", "")
    build = metadata.get("build_number")
    matched = []
    for item in rows:
        text = " ".join(str(x or "") for x in (item.target, item.description, item.evidence_uri, item.jenkins_url))
        strong = (digest and digest in text) or (commit and commit in text) or (build is not None and item.build_number == build)
        # Application/project match is deliberately accepted when scan systems
        # omit release identifiers; detailed correlation metadata is returned.
        if app_id or strong:
            matched.append((item, "strong" if strong else "project"))
    summary = {"total_findings": len(matched), **{key: 0 for key in SEVERITIES}, "active_critical": 0, "active_high": 0, "fix_available_count": 0, "exploitable_count": 0, "exception_count": 0, "suppressed_count": 0}
    details: List[Dict[str, Any]] = []
    for item, match in matched:
        severity = str(item.severity or "informational").lower()
        severity = severity if severity in SEVERITIES else "informational"
        summary[severity] += 1
        active_exception = _active_exception(item)
        expired_exception = bool(item.waiver_status) and not active_exception
        suppressed = str(item.status or "").lower() in {"suppressed", "false_positive"}
        if item.fixed_version: summary["fix_available_count"] += 1
        if "exploit" in str(item.description or "").lower(): summary["exploitable_count"] += 1
        if active_exception: summary["exception_count"] += 1
        if suppressed: summary["suppressed_count"] += 1
        if not active_exception and not suppressed and severity in {"critical", "high"}:
            summary[f"active_{severity}"] += 1
        details.append({"id": item.id, "finding_id": item.vulnerability_id, "category": item.source or "Unknown", "severity": severity.upper(), "target": item.target, "package_name": item.package_name, "status": item.status, "fixed_version": item.fixed_version, "correlation": match, "exception": {"active": active_exception, "expired": expired_exception, "reason": item.waiver_reason, "owner": item.waiver_approved_by, "expires_at": item.waiver_expiry}})
    return {"summary": summary, "findings": details}
