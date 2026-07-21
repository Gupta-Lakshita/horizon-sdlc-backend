from fastapi import APIRouter

from release_trust_repository import get_promotion_decision, get_promotion_decisions, get_release_runs
from release_trust_service import get_release_trust_detail, ingest_release_trust, request_promotion
from release_trust_schemas import PromotionRequest, ReleaseTrustPayload


router = APIRouter(prefix="/release-trust", tags=["Release Trust"])


@router.post("/runs", status_code=201)
def create_release_trust_run(payload: ReleaseTrustPayload):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return ingest_release_trust(data)


@router.get("/runs")
def list_release_trust_runs():
    return get_release_runs()


@router.post("/promotions", status_code=201)
def create_promotion(payload: PromotionRequest):
    return request_promotion(payload.release_id, payload.actor)


@router.get("/promotions")
def list_promotions():
    return get_promotion_decisions()


@router.get("/promotions/{release_id}")
def get_promotion(release_id: str):
    promotion = get_promotion_decision(release_id)
    if promotion is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Promotion decision not found")
    return promotion


@router.get("/runs/{release_id}")
def get_release_trust_run(release_id: str):
    return get_release_trust_detail(release_id)
