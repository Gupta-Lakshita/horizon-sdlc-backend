"""Request schemas for the frozen Release Trust evidence contract."""
from typing import List, Optional

from pydantic import BaseModel, Field


class ReleaseMetadata(BaseModel):
    release_id: str = Field(min_length=1)
    application: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    build_number: int
    build_time: str = Field(min_length=1)
    commit_sha: str = Field(min_length=1)
    branch: str = Field(min_length=1)


class ArtifactEvidence(BaseModel):
    image_name: str = Field(min_length=1)
    image_tag: str = Field(min_length=1)
    image_digest: str = Field(min_length=1)
    registry: str = Field(min_length=1)


class SBOMEvidence(BaseModel):
    status: str = Field(min_length=1)
    format: Optional[str] = None


class SignatureEvidence(BaseModel):
    status: str = Field(min_length=1)
    provider: str = Field(min_length=1)


class ProvenanceEvidence(BaseModel):
    status: str = Field(min_length=1)
    slsa_level: Optional[str] = None


class ScanEvidence(BaseModel):
    status: str = Field(min_length=1)
    critical: int
    high: int


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
    current_environment: str = Field(min_length=1)
    promotion_eligibility: str = Field(min_length=1)
    promotion_history: List[dict]


class ReleaseTrustPayload(BaseModel):
    release: ReleaseMetadata
    artifact: ArtifactEvidence
    sbom: SBOMEvidence
    signature: SignatureEvidence
    provenance: ProvenanceEvidence
    scan_evidence: ScanEvidence
    policy_evaluation: Optional[PolicyEvaluation] = None
    promotion: Promotion
