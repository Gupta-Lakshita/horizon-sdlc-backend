from fastapi import APIRouter, HTTPException

from release_trust_repository import get_release_by_id, get_release_runs


router = APIRouter(prefix="/release-trust", tags=["Release Trust"])


@router.get("/runs")
def list_release_trust_runs():
    return get_release_runs()


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
    release = get_release_by_id(release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release Trust run not found")
    return release
