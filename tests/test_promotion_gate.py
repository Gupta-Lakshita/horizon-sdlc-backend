"""Promotion gate unit and persistence/API-flow coverage."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from promotion_engine import ALLOW, DENY, MANUAL_APPROVAL, PromotionEngine
import release_trust_repository as repository
from routers.release_trust import create_promotion, get_promotion, list_promotions
from release_trust_schemas import PromotionRequest


@pytest.mark.parametrize("policy, expected", [
    ("PASS", ALLOW), ("WARN", MANUAL_APPROVAL), ("BLOCK", DENY),
])
def test_promotion_engine_uses_only_policy_status(policy, expected):
    result = PromotionEngine().evaluate(policy)
    assert result["promotion_status"] == expected
    assert result["deployment_permitted"] is (expected == ALLOW)


def payload(release_id, policy):
    return {
        "release": {"release_id": release_id, "application": "app", "environment": "dev", "build_number": 1, "build_time": "2026-07-21T00:00:00Z", "commit_sha": "a1b2c3d4", "branch": "main"},
        "artifact": {"image_name": "app", "image_tag": "1", "image_digest": "sha256:" + "2" * 64, "registry": "test"},
        "sbom": {"status": "generated", "format": "spdx-json"}, "signature": {"status": "verified", "provider": "cosign"},
        "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "pass", "critical": 0, "high": 0},
        "policy_evaluation": {"overall_decision": policy.lower(), "passed_rules": 6, "warning_rules": 0, "blocked_rules": 0, "summary": "stored", "rules": []},
        "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "dev"}]},
    }


def test_promotion_api_persists_stored_policy_mapping_and_rejects_duplicates():
    engine = create_engine("sqlite://")
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with patch.object(repository, "SessionLocal", test_session_local):
        for policy in ("PASS", "WARN", "BLOCK"):
            repository.create_release(payload(f"promotion-{policy.lower()}", policy))

        # Forged request status is intentionally absent from this direct router
        # call; the service only reads the release's persisted policy value.
        created = create_promotion(PromotionRequest(release_id="promotion-pass", actor="runner", promotion_status="DENY"))
        assert created["promotion_status"] == ALLOW
        assert created["policy_status"] == "PASS"
        assert get_promotion("promotion-pass") == {"release_id": "promotion-pass", **created}

        assert create_promotion(PromotionRequest(release_id="promotion-warn", actor="runner"))["promotion_status"] == MANUAL_APPROVAL
        assert create_promotion(PromotionRequest(release_id="promotion-block", actor="runner"))["promotion_status"] == DENY
        assert len(list_promotions()) == 3
        with pytest.raises(HTTPException) as duplicate:
            create_promotion(PromotionRequest(release_id="promotion-pass", actor="runner"))
        assert duplicate.value.status_code == 409
        with pytest.raises(HTTPException) as missing:
            create_promotion(PromotionRequest(release_id="unknown-release", actor="runner"))
        assert missing.value.status_code == 404
    engine.dispose()
