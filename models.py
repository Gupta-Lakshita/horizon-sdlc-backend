from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

#Base = declarative_base()

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    repo_url = Column(String, unique=True)
    branch = Column(String)
    app_type = Column(String, default="unknown") 

    vulnerabilities = relationship("Vulnerability", back_populates="application")
    access_list = relationship("ApplicationUserAccess", back_populates="application")


class ApplicationUserAccess(Base):
    __tablename__ = "app_user_access"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"))

    application = relationship("Application", back_populates="access_list")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    target = Column(String, nullable=False)
    package_name = Column(String, nullable=True)
    installed_version = Column(String, nullable=True)
    vulnerability_id = Column(String, nullable=False)
    severity = Column(String, nullable=True)
    fixed_version = Column(String, nullable=True)
    risk_score = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    source = Column(String, default="Unknown")
    timestamp = Column(DateTime, default=datetime.utcnow)
    line = Column(Integer, nullable=True)
    rule = Column(String, nullable=True)
    status = Column(String, nullable=True)
    predicted_severity = Column(String, nullable=True)
    jenkins_job = Column(String)
    build_number = Column(Integer)
    jenkins_url = Column(String, nullable=True)
    policy_bundle = Column(String, nullable=True)
    policy_version = Column(String, nullable=True)
    policy_ref = Column(String, nullable=True)
    policy_decision = Column(String, nullable=True)
    waiver_status = Column(String, nullable=True)
    waiver_expiry = Column(String, nullable=True)
    waiver_reason = Column(Text, nullable=True)
    waiver_approved_by = Column(String, nullable=True)
    evidence_uri = Column(String, nullable=True)

    application = relationship("Application", back_populates="vulnerabilities")


class EnvironmentCatalog(Base):
    __tablename__ = "environment_catalog"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    account_tier = Column(String, nullable=True)
    aws_account_id = Column(String, nullable=True)
    aws_region = Column(String, default="us-east-1")
    ecr_registry = Column(String, nullable=True)
    ecr_repository_template = Column(String, nullable=True)
    artifact_bucket = Column(String, nullable=True)
    client_aws_role_arn = Column(String, nullable=True)
    nonprod_aws_role_arn = Column(String, nullable=True)
    source_aws_role_arn = Column(String, nullable=True)
    target_aws_role_arn = Column(String, nullable=True)
    cluster_name = Column(String, nullable=True)
    namespace_strategy = Column(String, default="auto")
    namespace_template = Column(String, default="{client_id}-{project_name}-{env}")
    iam_validation_mode = Column(String, default="validation-only")
    eks_access_mode = Column(String, default="namespace-scoped")
    sns_topic_arn = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReleaseRun(Base):
    __tablename__ = "release_runs"

    id = Column(Integer, primary_key=True)
    release_id = Column(String, unique=True, nullable=False, index=True)
    application = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    build_number = Column(Integer, nullable=False)
    build_time = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    branch = Column(String, nullable=False)

    artifact = relationship("Artifact", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    sbom = relationship("SBOM", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    signature = relationship("Signature", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    provenance = relationship("Provenance", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    scan_evidence = relationship("ScanEvidence", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    policy_evaluation = relationship("PolicyEvaluation", back_populates="release_run", uselist=False, cascade="all, delete-orphan")
    promotion = relationship("Promotion", back_populates="release_run", uselist=False, cascade="all, delete-orphan")


class ReleaseEvidenceBase:
    id = Column(Integer, primary_key=True)
    release_run_id = Column(Integer, ForeignKey("release_runs.id"), unique=True, nullable=False)


class Artifact(ReleaseEvidenceBase, Base):
    __tablename__ = "release_artifacts"
    image_name = Column(String, nullable=False)
    image_tag = Column(String, nullable=False)
    image_digest = Column(String, nullable=False)
    registry = Column(String, nullable=False)
    release_run = relationship("ReleaseRun", back_populates="artifact")


class SBOM(ReleaseEvidenceBase, Base):
    __tablename__ = "release_sboms"
    status = Column(String, nullable=False)
    format = Column(String, nullable=True)
    release_run = relationship("ReleaseRun", back_populates="sbom")


class Signature(ReleaseEvidenceBase, Base):
    __tablename__ = "release_signatures"
    status = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    release_run = relationship("ReleaseRun", back_populates="signature")


class Provenance(ReleaseEvidenceBase, Base):
    __tablename__ = "release_provenance"
    status = Column(String, nullable=False)
    slsa_level = Column(String, nullable=True)
    release_run = relationship("ReleaseRun", back_populates="provenance")


class ScanEvidence(ReleaseEvidenceBase, Base):
    __tablename__ = "release_scan_evidence"
    status = Column(String, nullable=False)
    critical = Column(Integer, nullable=False)
    high = Column(Integer, nullable=False)
    release_run = relationship("ReleaseRun", back_populates="scan_evidence")


class PolicyEvaluation(ReleaseEvidenceBase, Base):
    __tablename__ = "release_policy_evaluations"
    overall_decision = Column(String, nullable=False)
    passed_rules = Column(Integer, nullable=False)
    warning_rules = Column(Integer, nullable=False)
    blocked_rules = Column(Integer, nullable=False)
    summary = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    release_run = relationship("ReleaseRun", back_populates="policy_evaluation")


class Promotion(ReleaseEvidenceBase, Base):
    __tablename__ = "release_promotions"
    current_environment = Column(String, nullable=False)
    promotion_eligibility = Column(String, nullable=False)
    promotion_history = Column(Text, nullable=False)
    release_run = relationship("ReleaseRun", back_populates="promotion")
