<<<<<<< HEAD
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/release-trust", tags=["Release Trust"])

MOCK_RELEASE_TRUST_RUNS = [
    {
        "id": "rel-2026-07-001",
        "release_id": "rel-2026-07-001",
        "commit_sha": "8f14e45f",
        "image_digest": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "policy_status": "pass",
        "sbom_status": "verified",
    },
    {
        "id": "rel-2026-07-002",
        "release_id": "rel-2026-07-002",
        "commit_sha": "c9f0f895",
        "image_digest": "sha256:3a6eb0790f39ac87c94f3856b2dd2c5d110e6811602261a9a923d3bb23adc8b7",
        "policy_status": "warn",
        "sbom_status": "generated",
    },
    {
        "id": "rel-2026-07-003",
        "release_id": "rel-2026-07-003",
        "commit_sha": "45c48cce",
        "image_digest": "sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        "policy_status": "block",
        "sbom_status": "missing",
    },
]

MOCK_RELEASE_TRUST_DETAILS = {
    "rel-2026-07-001": {
        "release": {
            "release_id": "rel-2026-07-001",
            "application": "horizon-sdlc-platform",
            "environment": "dev",
            "build_number": 101,
            "build_time": "2026-07-16T10:15:00Z",
            "commit_sha": "8f14e45f",
            "branch": "main",
        },
        "artifact": {
            "image_name": "horizon-sdlc-platform",
            "image_tag": "2026.07.16-101",
            "image_digest": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            "registry": "local-dev",
        },
        "sbom": {"status": "verified", "format": "spdx-json"},
        "signature": {"status": "verified", "provider": "cosign"},
        "provenance": {"status": "verified", "slsa_level": "2"},
        "scan_evidence": {"status": "pass", "critical": 0, "high": 0},
        "policy_evaluation": {
            "overall_decision": "pass",
            "passed_rules": 8,
            "warning_rules": 0,
            "blocked_rules": 0,
        },
        "promotion": {
            "current_environment": "dev",
            "promotion_eligibility": "eligible",
            "promotion_history": [
                {"environment": "dev", "promoted_at": "2026-07-16T10:35:00Z"}
            ],
=======
from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/release-trust", tags=["release-trust"])


RELEASE_TRUST_RUNS = [
    {
        "release_id": "rel-2026-07-001",
        "application": "Payments",
        "commit_sha": "8f3a2c9",
        "image_digest": "sha256:abcd1234",
        "policy_status": "pass",
        "sbom_status": "generated",
    },
    {
        "release_id": "rel-2026-07-002",
        "application": "Claims",
        "commit_sha": "5d7b1a4",
        "image_digest": "sha256:efgh5678",
        "policy_status": "warn",
        "sbom_status": "generated",
    },
]


RELEASE_TRUST_RUN_DETAILS = {
    "rel-2026-07-001": {
        "release": {
            "release_id": "rel-2026-07-001",
            "application": "Payments",
            "environment": "staging",
            "build_number": "1842",
            "build_time": "2026-07-14T10:32:18Z",
            "commit_sha": "8f3a2c9",
            "branch": "main",
        },
        "artifact": {
            "image_name": "payments-api",
            "image_tag": "2026.07.14-1842",
            "image_digest": "sha256:abcd1234",
            "registry": "registry.horizonrelevance.com/platform",
        },
        "sbom": {
            "status": "generated",
            "format": "CycloneDX",
            "spec_version": "1.5",
            "generator": "Syft 1.5.0",
            "generated_at": "2026-07-14T10:33:05Z",
            "component_count": 146,
            "download_url": "https://evidence.horizonrelevance.com/releases/rel-2026-07-001/sbom.cdx.json",
            "hash": "sha256:9a35b2c41d7e",
        },
        "signature": {
            "status": "verified",
            "algorithm": "ECDSA-P256-SHA256",
            "issuer": "Horizon Release Signing CA",
            "certificate": "https://evidence.horizonrelevance.com/certificates/payments-release.pem",
            "signed_at": "2026-07-14T10:34:11Z",
            "verified_at": "2026-07-14T10:34:14Z",
        },
        "provenance": {
            "status": "verified",
            "predicate_type": "https://slsa.dev/provenance/v1",
            "builder": "horizon-runner",
            "repository": "https://github.com/horizonrelevance/payments-api",
            "workflow": "release.yml",
            "build_id": "payments-api-1842",
            "generated_at": "2026-07-14T10:33:48Z",
        },
        "scan_evidence": {
            "status": "passed",
            "scanner": "Trivy 0.53.0",
            "scan_time": "2026-07-14T10:35:22Z",
            "critical": 0,
            "high": 0,
            "medium": 2,
            "low": 5,
        },
        "policy_evaluation": {
            "overall_decision": "pass",
            "passed_rules": 12,
            "warning_rules": 0,
            "blocked_rules": 0,
            "evaluated_at": "2026-07-14T10:36:01Z",
        },
        "promotion": {
            "current_environment": "staging",
            "promotion_history": [
                {"environment": "development", "promoted_at": "2026-07-14T09:48:03Z"},
                {"environment": "staging", "promoted_at": "2026-07-14T10:41:12Z"},
            ],
            "promotion_eligibility": "eligible",
>>>>>>> 003d5a96fa1f374fc3981e86a6d8dc94d9e33a72
        },
    },
    "rel-2026-07-002": {
        "release": {
            "release_id": "rel-2026-07-002",
<<<<<<< HEAD
            "application": "horizon-runner",
            "environment": "dev",
            "build_number": 102,
            "build_time": "2026-07-16T11:05:00Z",
            "commit_sha": "c9f0f895",
            "branch": "main",
        },
        "artifact": {
            "image_name": "horizon-runner",
            "image_tag": "2026.07.16-102",
            "image_digest": "sha256:3a6eb0790f39ac87c94f3856b2dd2c5d110e6811602261a9a923d3bb23adc8b7",
            "registry": "local-dev",
        },
        "sbom": {"status": "generated", "format": "cyclonedx-json"},
        "signature": {"status": "verified", "provider": "cosign"},
        "provenance": {"status": "verified", "slsa_level": "2"},
        "scan_evidence": {"status": "warn", "critical": 0, "high": 1},
        "policy_evaluation": {
            "overall_decision": "warn",
            "passed_rules": 7,
            "warning_rules": 1,
            "blocked_rules": 0,
        },
        "promotion": {
            "current_environment": "dev",
            "promotion_eligibility": "eligible_with_warnings",
            "promotion_history": [
                {"environment": "dev", "promoted_at": "2026-07-16T11:25:00Z"}
            ],
        },
    },
    "rel-2026-07-003": {
        "release": {
            "release_id": "rel-2026-07-003",
            "application": "license-service",
            "environment": "dev",
            "build_number": 103,
            "build_time": "2026-07-16T11:45:00Z",
            "commit_sha": "45c48cce",
            "branch": "feature/release-trust",
        },
        "artifact": {
            "image_name": "license-service",
            "image_tag": "2026.07.16-103",
            "image_digest": "sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            "registry": "local-dev",
        },
        "sbom": {"status": "missing", "format": None},
        "signature": {"status": "failed", "provider": "cosign"},
        "provenance": {"status": "failed", "slsa_level": None},
        "scan_evidence": {"status": "failed", "critical": 1, "high": 3},
        "policy_evaluation": {
            "overall_decision": "block",
            "passed_rules": 4,
            "warning_rules": 2,
            "blocked_rules": 2,
        },
        "promotion": {
            "current_environment": "dev",
            "promotion_eligibility": "blocked",
            "promotion_history": [],
=======
            "application": "Claims",
            "environment": "development",
            "build_number": "993",
            "build_time": "2026-07-14T12:18:47Z",
            "commit_sha": "5d7b1a4",
            "branch": "release/2026.07",
        },
        "artifact": {
            "image_name": "claims-api",
            "image_tag": "2026.07.14-993",
            "image_digest": "sha256:efgh5678",
            "registry": "registry.horizonrelevance.com/platform",
        },
        "sbom": {
            "status": "generated",
            "format": "CycloneDX",
            "spec_version": "1.5",
            "generator": "Syft 1.5.0",
            "generated_at": "2026-07-14T12:19:25Z",
            "component_count": 98,
            "download_url": "https://evidence.horizonrelevance.com/releases/rel-2026-07-002/sbom.cdx.json",
            "hash": "sha256:4f81e1a803d9",
        },
        "signature": {
            "status": "verified",
            "algorithm": "ECDSA-P256-SHA256",
            "issuer": "Horizon Release Signing CA",
            "certificate": "https://evidence.horizonrelevance.com/certificates/claims-release.pem",
            "signed_at": "2026-07-14T12:20:04Z",
            "verified_at": "2026-07-14T12:20:07Z",
        },
        "provenance": {
            "status": "verified",
            "predicate_type": "https://slsa.dev/provenance/v1",
            "builder": "horizon-runner",
            "repository": "https://github.com/horizonrelevance/claims-api",
            "workflow": "release.yml",
            "build_id": "claims-api-993",
            "generated_at": "2026-07-14T12:19:51Z",
        },
        "scan_evidence": {
            "status": "passed",
            "scanner": "Trivy 0.53.0",
            "scan_time": "2026-07-14T12:21:19Z",
            "critical": 0,
            "high": 0,
            "medium": 4,
            "low": 9,
        },
        "policy_evaluation": {
            "overall_decision": "warn",
            "passed_rules": 10,
            "warning_rules": 2,
            "blocked_rules": 0,
            "evaluated_at": "2026-07-14T12:22:03Z",
        },
        "promotion": {
            "current_environment": "development",
            "promotion_history": [
                {"environment": "development", "promoted_at": "2026-07-14T12:25:19Z"},
            ],
            "promotion_eligibility": "eligible_with_warnings",
>>>>>>> 003d5a96fa1f374fc3981e86a6d8dc94d9e33a72
        },
    },
}


<<<<<<< HEAD
@router.get("/runs")
def list_release_trust_runs():
    return MOCK_RELEASE_TRUST_RUNS
=======
def find_release_run(release_id: str):
    return RELEASE_TRUST_RUN_DETAILS.get(release_id)


@router.get("/runs")
def list_release_trust_runs():
    return RELEASE_TRUST_RUNS
>>>>>>> 003d5a96fa1f374fc3981e86a6d8dc94d9e33a72


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
<<<<<<< HEAD
    release = MOCK_RELEASE_TRUST_DETAILS.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return release
=======
    release = find_release_run(release_id)
    if not release:
        return JSONResponse(
            status_code=404,
            content={"error": f"Release Trust run '{release_id}' was not found."},
        )
    return release


@router.get("/health")
def release_trust_health():
    return {
        "status": "not_implemented",
        "message": "Release Trust API skeleton is registered. Functionality is not implemented yet.",
    }
>>>>>>> 003d5a96fa1f374fc3981e86a6d8dc94d9e33a72
