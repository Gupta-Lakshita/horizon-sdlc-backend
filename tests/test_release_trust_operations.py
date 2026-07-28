from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from release_trust_operations import ReleaseTrustMetrics, audit, health_report, list_audit_logs, validate_configuration
from storage.local_object_store import LocalObjectStore


def test_configuration_validation_preserves_non_strict_compatibility(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_DEV_AUTH", "true")
    assert validate_configuration(strict=False) == []
    assert "LOCAL_DEV_AUTH must be disabled in strict mode" in validate_configuration(strict=True)


def test_audit_records_are_structured_and_persisted():
    engine = create_engine("sqlite://")
    sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with patch("release_trust_operations.SessionLocal", sessions):
        audit("release.create", "rel-audit", "success", correlation_id="request-1", details={"safe": True})
        events = list_audit_logs()
    assert events[0]["operation"] == "release.create"
    assert events[0]["correlation_id"] == "request-1"
    assert events[0]["details"] == {"safe": True}


def test_metrics_and_health_are_provider_neutral(tmp_path):
    counters = ReleaseTrustMetrics()
    counters.increment("release_trust.releases_created")
    assert counters.snapshot()["release_trust.releases_created"] == 1
    report = health_report(LocalObjectStore(tmp_path))
    assert report["checks"]["object_store"]["status"] == "ok"
