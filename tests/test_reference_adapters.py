"""Dependency-free checks for the Phase 12 HTTP-only reference layer."""
import unittest

from release_trust_adapters.jenkins import JenkinsReferenceAdapter


class _Client:
    def __init__(self): self.calls = []
    def create_release(self, value): self.calls.append(("release", value)); return value
    def publish_event(self, release_id, value): self.calls.append(("event", release_id, value))
    def upload_evidence(self, release_id, value): self.calls.append(("evidence", release_id, value))


class ReferenceAdapterTests(unittest.TestCase):
    def test_jenkins_maps_environment_and_publishes_only_through_client(self):
        client = _Client()
        adapter = JenkinsReferenceAdapter(client, {"JOB_NAME": "payments", "BUILD_NUMBER": "10", "BUILD_URL": "https://ci/run/10", "GIT_COMMIT": "abc", "BRANCH_NAME": "main"})
        payload = adapter.release_payload("payments", "dev", "payments-10")
        adapter.publish(payload, [{"evidence_type": "scan", "name": "scan.json"}])
        self.assertEqual(payload["execution"]["pipeline_execution_id"], "payments#10")
        self.assertEqual([call[0] for call in client.calls], ["release", "event", "evidence"])
