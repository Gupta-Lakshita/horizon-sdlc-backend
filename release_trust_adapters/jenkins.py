"""Reference mapper from Jenkins environment variables to Runner API v1."""
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional

from .client import RunnerApiClient


class JenkinsReferenceAdapter:
    """HTTP-only example. It never imports Release Trust persistence modules."""
    def __init__(self, client: RunnerApiClient, environment: Optional[Dict[str, str]] = None):
        self.client, self.env = client, environment or os.environ

    def release_payload(self, application: str, environment: str, release_id: str, artifact: Optional[dict] = None) -> dict:
        env = self.env
        return {"contract_version": "v1", "release_id": release_id, "application": application, "environment": environment,
                "repository": {"url": env.get("GIT_URL"), "name": env.get("JOB_NAME"), "revision": env.get("GIT_COMMIT")},
                "commit_sha": env.get("GIT_COMMIT", "unknown"), "branch": env.get("BRANCH_NAME", "unknown"),
                "build": {"number": env.get("BUILD_NUMBER"), "timestamp": datetime.now(timezone.utc).isoformat()},
                "artifacts": [artifact] if artifact else [],
                "execution": {"pipeline_id": env.get("JOB_NAME", "jenkins-pipeline"), "pipeline_execution_id": f"{env.get('JOB_NAME', 'job')}#{env.get('BUILD_NUMBER', '0')}", "external_run_id": env.get("BUILD_TAG"), "runner_name": "jenkins", "runner_version": env.get("JENKINS_VERSION"), "build_url": env.get("BUILD_URL"), "build_number": env.get("BUILD_NUMBER"), "status": "running", "trigger_source": env.get("BUILD_CAUSE", "pipeline"), "started_at": datetime.now(timezone.utc).isoformat()}}

    def publish(self, payload: dict, evidence: Iterable[dict] = ()) -> dict:
        result = self.client.create_release(payload); release_id = payload["release_id"]
        self.client.publish_event(release_id, {"event_type": "pipeline.started", "occurred_at": datetime.now(timezone.utc).isoformat(), "payload": {"build_url": self.env.get("BUILD_URL")}})
        for item in evidence: self.client.upload_evidence(release_id, item)
        return result
