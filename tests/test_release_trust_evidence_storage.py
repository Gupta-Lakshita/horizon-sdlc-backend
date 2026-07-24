"""Phase 9 coverage for provider-neutral Release Trust evidence storage."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import release_trust_repository as repository
from release_trust_service import get_release_trust_detail, ingest_release_trust
from storage.local_object_store import LocalObjectStore
from storage.object_store import ObjectAlreadyExistsError, ObjectNotFoundError


def _payload(release_id="evidence-test"):
    return {
        "release": {"release_id": release_id, "application": "app", "environment": "dev", "build_number": 1, "build_time": "2026-07-24T00:00:00Z", "commit_sha": "abc123", "branch": "main"},
        "artifact": {"image_name": "app", "image_tag": "1", "image_digest": "sha256:" + "a" * 64, "registry": "test"},
        "sbom": {"status": "verified", "format": "spdx-json"},
        "signature": {"status": "verified", "provider": "cosign"},
        "provenance": {"status": "verified", "slsa_level": "2"},
        "scan_evidence": {"status": "pass", "critical": 0, "high": 0},
        "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "dev"}]},
    }


def test_local_object_store_upload_download_and_delete(tmp_path):
    store = LocalObjectStore(tmp_path / "data" / "evidence")
    reference = store.upload_json("release-123", "sbom", {"status": "verified"})
    assert reference == "evidence/release-123/sbom.json"
    assert store.exists(reference)
    assert store.download_json(reference) == {"status": "verified"}
    with pytest.raises(ObjectAlreadyExistsError):
        store.upload_json("release-123", "sbom", {})
    store.delete(reference)
    assert not store.exists(reference)
    with pytest.raises(ObjectNotFoundError):
        store.download_json(reference)


def test_references_are_persisted_and_api_detail_hydrates_evidence(tmp_path):
    engine = create_engine("sqlite://")
    sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    store = LocalObjectStore(tmp_path / "data" / "evidence")
    with patch.object(repository, "SessionLocal", sessions):
        created = ingest_release_trust(_payload(), store)
        assert created["sbom"] == {"status": "verified", "format": "spdx-json"}
        with sessions() as session:
            run = session.query(repository.ReleaseRun).filter_by(release_id="evidence-test").one()
            assert run.sbom_reference == "evidence/evidence-test/sbom.json"
            assert run.signature_reference == "evidence/evidence-test/signature.json"
            assert run.sbom is None  # new records do not duplicate evidence in SQLite
        # The externally visible detail contract remains the embedded payload.
        assert get_release_trust_detail("evidence-test", store)["scan_evidence"] == {"status": "pass", "critical": 0, "high": 0}
        with pytest.raises(HTTPException) as duplicate:
            ingest_release_trust(_payload(), store)
        assert duplicate.value.status_code == 409
        store.delete("evidence/evidence-test/sbom.json")
        with pytest.raises(HTTPException) as missing:
            get_release_trust_detail("evidence-test", store)
        assert missing.value.status_code == 404
    engine.dispose()
