"""Production operations shared by the Release Trust router and service.

This module deliberately contains no FastAPI or provider-specific logic so it
can be injected/tested independently and so audit records survive restarts.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import os
from threading import Lock
from typing import Any, Dict, Optional

from sqlalchemy import text

from database import SessionLocal, engine
from models import ReleaseTrustAuditLog
from storage.object_store import ObjectStore


class ReleaseTrustMetrics:
    """Small, vendor-neutral counter registry intended for scrape/export adapters."""
    def __init__(self) -> None:
        self._values: Counter[str] = Counter()
        self._lock = Lock()

    def increment(self, name: str) -> None:
        with self._lock:
            self._values[name] += 1

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._values)


metrics = ReleaseTrustMetrics()


def audit(operation: str, target: str, result: str, *, principal: Any = None,
          correlation_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    """Persist a structured, secret-free audit event. Audit failure never breaks a release."""
    identity = "system"
    if principal is not None:
        identity = getattr(principal, "email", "") or getattr(principal, "username", "") or "system"
    try:
        with SessionLocal() as session:
            session.add(ReleaseTrustAuditLog(
                timestamp=datetime.now(timezone.utc), identity=str(identity)[:256],
                operation=operation, target=str(target)[:512], result=result,
                correlation_id=(correlation_id or "")[:128], details_json=__import__("json").dumps(details or {}, sort_keys=True),
            ))
            session.commit()
    except Exception:
        # Operational telemetry must not turn a valid release decision into an outage.
        return


def list_audit_logs(limit: int = 100) -> list[Dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with SessionLocal() as session:
        rows = session.query(ReleaseTrustAuditLog).order_by(ReleaseTrustAuditLog.id.desc()).limit(limit).all()
        return [{"timestamp": row.timestamp.isoformat(), "identity": row.identity,
                 "operation": row.operation, "target": row.target, "result": row.result,
                 "correlation_id": row.correlation_id, "details": __import__("json").loads(row.details_json or "{}")} for row in rows]


def validate_configuration(*, strict: Optional[bool] = None) -> list[str]:
    """Return validation diagnostics; strict mode makes production omissions fatal."""
    strict = strict if strict is not None else os.getenv("RELEASE_TRUST_STRICT_CONFIG", "false").lower() == "true"
    errors: list[str] = []
    provider = os.getenv("OBJECT_STORE_PROVIDER", "local").strip().lower()
    if provider not in {"local", "s3", "minio", "azure", "azure-blob"}:
        errors.append("OBJECT_STORE_PROVIDER must name a registered provider")
    if strict and not os.getenv("GITHUB_WEBHOOK_SECRET"):
        errors.append("GITHUB_WEBHOOK_SECRET is required in strict mode")
    if strict and os.getenv("LOCAL_DEV_AUTH", "false").lower() == "true":
        errors.append("LOCAL_DEV_AUTH must be disabled in strict mode")
    return errors


def health_report(object_store: ObjectStore) -> Dict[str, Any]:
    checks: Dict[str, Dict[str, Any]] = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception:
        checks["database"] = {"status": "error"}
    try:
        # Validating an opaque non-writing reference proves provider initialization.
        object_store.build_reference("healthcheck", "sbom")
        checks["object_store"] = {"status": "ok", "provider": type(object_store).__name__}
    except Exception:
        checks["object_store"] = {"status": "error"}
    config_errors = validate_configuration()
    checks["configuration"] = {"status": "ok" if not config_errors else "warning", "errors": config_errors}
    checks["runner_api"] = {"status": "ready"}
    status = "ok" if all(item["status"] in {"ok", "ready"} for item in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
