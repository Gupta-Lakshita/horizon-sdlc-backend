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
        },
    },
    "rel-2026-07-002": {
        "release": {
            "release_id": "rel-2026-07-002",
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
        },
    },
}


@router.get("/runs")
def list_release_trust_runs():
    return MOCK_RELEASE_TRUST_RUNS


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
    release = MOCK_RELEASE_TRUST_DETAILS.get(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return release
