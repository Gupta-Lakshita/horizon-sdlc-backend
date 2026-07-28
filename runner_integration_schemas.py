"""Versioned, CI/CD-neutral contracts for Release Trust runner ingestion."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


RUNNER_CONTRACT_VERSION = "v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RepositoryContext(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    revision: Optional[str] = None


class ArtifactMetadata(BaseModel):
    name: str
    version: Optional[str] = None
    digest: Optional[str] = None
    uri: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceUpload(BaseModel):
    """An open evidence category and optional externally-hosted reference."""
    evidence_type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    reference: Optional[str] = None
    media_type: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionMetadata(BaseModel):
    pipeline_id: str = Field(min_length=1)
    pipeline_execution_id: str = Field(min_length=1)
    external_run_id: Optional[str] = None
    runner_name: Optional[str] = None
    runner_version: Optional[str] = None
    build_url: Optional[str] = None
    build_number: Optional[str] = None
    status: str = "pending"
    trigger_source: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunnerReleaseCreate(BaseModel):
    contract_version: str = RUNNER_CONTRACT_VERSION
    release_id: str = Field(min_length=1)
    application: str = Field(min_length=1)
    environment: str = "dev"
    repository: RepositoryContext = Field(default_factory=RepositoryContext)
    commit_sha: str = "unknown"
    branch: str = "unknown"
    tag: Optional[str] = None
    build: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[ArtifactMetadata] = Field(default_factory=list)
    execution: ExecutionMetadata
    evidence: List[EvidenceUpload] = Field(default_factory=list)


class RunnerStatusUpdate(BaseModel):
    status: str = Field(min_length=1)
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunnerPipelineEvent(BaseModel):
    event_type: str = Field(min_length=1, description="For example pipeline.started, build.completed, evidence.uploaded, policy.evaluation.requested, promotion.requested, or promotion.completed.")
    occurred_at: str = Field(default_factory=now_iso)
    payload: Dict[str, Any] = Field(default_factory=dict)


class RunnerAuthentication(Protocol):
    """Future adapter auth boundary; platform session/RBAC remains authoritative."""
    def authenticate(self, authorization: Optional[str], api_key: Optional[str] = None) -> Any: ...


class RunnerAdapter(Protocol):
    """Capabilities a future provider adapter may implement; no provider is embedded."""
    def authenticate(self, credentials: Any) -> Any: ...
    def publish_release(self, release: RunnerReleaseCreate) -> Any: ...
    def publish_evidence(self, release_id: str, evidence: EvidenceUpload) -> Any: ...
    def publish_metadata(self, release_id: str, execution: ExecutionMetadata) -> Any: ...
    def publish_event(self, release_id: str, event: RunnerPipelineEvent) -> Any: ...
    def synchronize_status(self, release_id: str, status: RunnerStatusUpdate) -> Any: ...
