from fastapi import APIRouter

from release_trust_repository import get_release_runs
from release_trust_service import get_release_trust_detail, ingest_release_trust
from release_trust_schemas import ReleaseTrustPayload


router = APIRouter(prefix="/release-trust", tags=["Release Trust"])


@router.post("/runs", status_code=201)
def create_release_trust_run(payload: ReleaseTrustPayload):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return ingest_release_trust(data)


@router.get("/runs")
def list_release_trust_runs():
    return get_release_runs()


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
    return get_release_trust_detail(release_id)
