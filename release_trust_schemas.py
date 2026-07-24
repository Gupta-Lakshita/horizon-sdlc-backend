"""Request schemas for Release Trust CI and manual-demo ingestion."""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def _manual_build_time() -> str:
    """Generate an ISO timestamp when a manually created release has none."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ReleaseMetadata(BaseModel):
    release_id: str = Field(min_length=1)
    application: str = Field(default="manual-release", min_length=1)
    environment: str = Field(default="dev", min_length=1)
    build_number: int = 0
    build_time: str = Field(default_factory=_manual_build_time, min_length=1)
    commit_sha: str = Field(default="manual", min_length=1)
    branch: str = Field(default="manual", min_length=1)


class ArtifactEvidence(BaseModel):
    image_name: str = Field(default="manual-image", min_length=1)
    image_tag: str = Field(default="manual", min_length=1)
    image_digest: str = Field(default="sha256:manual", min_length=1)
    registry: str = Field(default="manual", min_length=1)


class SBOMEvidence(BaseModel):
    status: str = Field(default="verified", min_length=1)
    format: Optional[str] = None


class SignatureEvidence(BaseModel):
    status: str = Field(default="verified", min_length=1)
    provider: str = Field(default="manual", min_length=1)


class ProvenanceEvidence(BaseModel):
    status: str = Field(default="verified", min_length=1)
    slsa_level: Optional[str] = None


class ScanEvidence(BaseModel):
    status: str = Field(default="pass", min_length=1)
    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)


class PolicyEvaluation(BaseModel):
    # Legacy fields remain accepted for existing clients; the service replaces
    # them with the engine-generated evaluation before persistence.
    overall_decision: str = Field(default="pending", min_length=1)
    passed_rules: int = 0
    warning_rules: int = 0
    blocked_rules: int = 0
    status: Optional[str] = None
    summary: Optional[str] = None
    rules: Optional[List[dict]] = None


class Promotion(BaseModel):
    current_environment: str = Field(default="dev", min_length=1)
    promotion_eligibility: str = Field(default="eligible", min_length=1)
    promotion_history: List[dict] = Field(default_factory=list)


class ReleaseTrustPayload(BaseModel):
    """Complete CI metadata or minimal evidence for a manual test release.

    ``release.release_id`` is the only required field.  Optional sections and
    metadata receive persistence-safe defaults; explicitly supplied evidence is
    always what drives the Policy Engine result.
    """
    release: ReleaseMetadata
    artifact: ArtifactEvidence = Field(default_factory=ArtifactEvidence)
    sbom: SBOMEvidence = Field(default_factory=SBOMEvidence)
    signature: SignatureEvidence = Field(default_factory=SignatureEvidence)
    provenance: ProvenanceEvidence = Field(default_factory=ProvenanceEvidence)
    scan_evidence: ScanEvidence = Field(default_factory=ScanEvidence)
    policy_evaluation: Optional[PolicyEvaluation] = None
    promotion: Promotion = Field(default_factory=Promotion)


class PromotionRequest(BaseModel):
    release_id: str = Field(min_length=1)
    actor: str = Field(default="system", min_length=1)
    # Accepted only to demonstrate backward-compatible rejection of forged
    # decisions; the router and service intentionally never read it.
    promotion_status: Optional[str] = None
