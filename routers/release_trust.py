from fastapi import APIRouter


router = APIRouter(prefix="/release-trust", tags=["release-trust"])


@router.get("/health")
def release_trust_health():
    return {
        "status": "not_implemented",
        "message": "Release Trust API skeleton is registered. Functionality is not implemented yet.",
    }
