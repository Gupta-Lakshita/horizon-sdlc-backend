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


def find_release_run(release_id: str):
    for release in RELEASE_TRUST_RUNS:
        if release["release_id"] == release_id:
            return release
    return None


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
