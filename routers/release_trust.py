from fastapi import APIRouter, Body

from release_trust_repository import get_promotion_decision, get_promotion_decisions
from release_trust_service import get_release_trust_detail, get_release_trust_runs, ingest_release_trust, request_promotion
from release_trust_schemas import PromotionRequest, ReleaseTrustPayload


router = APIRouter(prefix="/release-trust", tags=["Release Trust"])


RUN_EXAMPLES = {
    "pass": {
        "summary": "PASS manual release",
        "description": "Supply a completed promotion to satisfy every policy rule.",
        "value": {"release": {"release_id": "demo-pass"}, "promotion": {"promotion_history": [{"environment": "dev"}]}},
    },
    "warn": {
        "summary": "WARN manual release",
        "description": "The default empty promotion history leaves a promotion warning.",
        "value": {"release": {"release_id": "demo-warn"}},
    },
    "block": {
        "summary": "BLOCK manual release",
        "description": "A failed signature is evaluated as a blocking policy violation.",
        "value": {"release": {"release_id": "demo-block"}, "signature": {"status": "failed"}},
    },
    "production": {
        "summary": "Full production CI/CD payload",
        "value": {"release": {"release_id": "ci-2026-07-24-101", "application": "payments", "environment": "staging", "build_number": 101, "build_time": "2026-07-24T10:15:00Z", "commit_sha": "8f14e45f", "branch": "main"}, "artifact": {"image_name": "payments", "image_tag": "2026.07.24-101", "image_digest": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "registry": "registry.example.com"}, "sbom": {"status": "verified", "format": "spdx-json"}, "signature": {"status": "verified", "provider": "cosign"}, "provenance": {"status": "verified", "slsa_level": "2"}, "scan_evidence": {"status": "pass", "critical": 0, "high": 0}, "promotion": {"current_environment": "staging", "promotion_eligibility": "eligible", "promotion_history": [{"environment": "staging", "promoted_at": "2026-07-24T10:30:00Z"}]}},
    },
}


@router.post("/runs", status_code=201)
def create_release_trust_run(payload: ReleaseTrustPayload = Body(..., openapi_examples=RUN_EXAMPLES)):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return ingest_release_trust(data)


@router.get("/runs")
def list_release_trust_runs():
    return get_release_trust_runs()


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
