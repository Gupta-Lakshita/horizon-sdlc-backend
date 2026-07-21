"""Integration coverage for Release Trust policy evaluation on POST ingestion."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from database import Base
import release_trust_repository as repository
from release_trust_schemas import ReleaseTrustPayload
from routers.release_trust import (
    create_release_trust_run,
    get_release_trust_run,
    list_release_trust_runs,
)
from policy_engine import PolicyEngine
from release_trust_repository import backfill_policy_evaluations


def test_post_ignores_client_supplied_policy_evaluation_and_persists_engine_result():
    """Exercise router -> service -> engine -> repository -> SQLite end to end."""
    engine = create_engine("sqlite://")
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    payload = ReleaseTrustPayload(
        release={
            "release_id": "forged-policy-integration-test",
            "application": "policy-test-app",
            "environment": "dev",
            "build_number": 1,
            "build_time": "2026-07-20T00:00:00Z",
            "commit_sha": "a1b2c3d4",
            "branch": "main",
        },
        artifact={
            "image_name": "policy-test-app",
            "image_tag": "1.0.0",
            "image_digest": "sha256:" + "0" * 64,
            "registry": "local-test",
        },
        sbom={"status": "generated", "format": "spdx-json"},
        signature={"status": "verified", "provider": "cosign"},
        provenance={"status": "available", "slsa_level": "2"},
        scan_evidence={"status": "pass", "critical": 0, "high": 0},
        # This value must not affect the persisted result.
        policy_evaluation={
            "overall_decision": "block",
            "passed_rules": 0,
            "warning_rules": 0,
            "blocked_rules": 999,
        },
        promotion={
            "current_environment": "dev",
            "promotion_eligibility": "eligible",
            "promotion_history": [{"environment": "dev", "promoted_at": "2026-07-20T00:00:00Z"}],
        },
    )

    with patch.object(repository, "SessionLocal", test_session_local):
        created = create_release_trust_run(payload)
        policy = created["policy_evaluation"]
        assert policy["status"] == "PASS"
        assert policy["overall_decision"] == "pass"
        assert policy["passed_rules"] == 6
        assert policy["warning_rules"] == 0
        assert policy["blocked_rules"] == 0
        assert {"rule": "High vulnerabilities > 0", "result": "PASS"} in policy["rules"]

        persisted = get_release_trust_run("forged-policy-integration-test")
        assert persisted["policy_evaluation"] == policy
        assert list_release_trust_runs()[0]["policy_status"] == "pass"

    engine.dispose()


def test_legacy_rows_are_backfilled_with_the_full_computed_policy():
    engine = create_engine("sqlite://")
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    legacy = {
        "release": {"release_id": "legacy-policy-test", "application": "app", "environment": "dev", "build_number": 1, "build_time": "2026-07-20T00:00:00Z", "commit_sha": "a1b2c3d4", "branch": "main"},
        "artifact": {"image_name": "app", "image_tag": "1", "image_digest": "sha256:" + "1" * 64, "registry": "test"},
        "sbom": {"status": "generated", "format": "spdx-json"}, "signature": {"status": "verified", "provider": "cosign"},
        "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "pass", "critical": 0, "high": 0},
        "policy_evaluation": {"overall_decision": "warn", "passed_rules": 0, "warning_rules": 99, "blocked_rules": 0},
        "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "dev"}]},
    }
    with patch.object(repository, "SessionLocal", test_session_local):
        repository.create_release(legacy)
        backfill_policy_evaluations(PolicyEngine())
        stored = get_release_trust_run("legacy-policy-test")
        assert stored["policy_evaluation"] == PolicyEngine().evaluate(stored)
        assert list_release_trust_runs()[0]["policy_status"] == "pass"
    engine.dispose()
