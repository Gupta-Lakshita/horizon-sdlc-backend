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
        },
    },
    "rel-2026-07-002": {
        "release": {
            "release_id": "rel-2026-07-002",
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
        },
    },
}


def find_release_run(release_id: str):
    return RELEASE_TRUST_RUN_DETAILS.get(release_id)


@router.get("/runs")
def list_release_trust_runs():
    return RELEASE_TRUST_RUNS


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
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
