"""Release Trust lifecycle coverage for existing pipeline request hooks."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from database import Base
from models import Application
import release_trust_repository as repository
import release_trust_service as service
from storage.local_object_store import LocalObjectStore


def test_pipeline_events_share_one_application_release_run(tmp_path):
    engine = create_engine("sqlite://")
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    store = LocalObjectStore(tmp_path / "evidence")

    with patch.object(repository, "SessionLocal", test_session_local), patch.object(service, "_store", return_value=store):
        with test_session_local() as session:
            application = Application(name="payments", owner_email="dev@example.com", repo_url="https://example.test/payments", branch="main", app_type="Docker")
            session.add(application)
            session.commit()
            application_id = application.id

        release = service.start_build_pipeline_release(
            application_id=application_id,
            application="payments",
            environment="DEV",
            branch="main",
            actor="dev@example.com",
            repository_url="https://example.test/payments",
            image_name="payments",
            registry="registry.example.test",
            pipeline_job="payments",
        )
        release_id = release["release"]["release_id"]
        validation = service.record_validation_pipeline_start(
            application_id=application_id,
            actor="qa@example.com",
            pipeline_job="payments-test",
            enabled_gates=["trivy", "opa"],
        )
        promotion = service.record_promotion_pipeline_start(
            application_id=application_id,
            actor="release@example.com",
            pipeline_job="payments-qa-release",
            source_environment="DEV",
            target_environment="QA",
            image_tag="",
        )

        assert validation["release"]["release_id"] == release_id
        assert promotion["release"]["release_id"] == release_id
        events = repository.get_release_by_id(release_id, store)["pipeline_execution"]
        assert [event["stage"] for event in events] == ["build", "validation", "promotion"]
        assert events[1]["validation_evidence"]["enabled_gates"] == ["opa", "trivy"]

    engine.dispose()
