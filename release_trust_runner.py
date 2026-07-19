"""Development-only simulated runner output."""
from datetime import datetime, timezone
from typing import Dict, Any


def simulated_release_trust_payload(release_id: str = "rel-simulated-001") -> Dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "release": {"release_id": release_id, "application": "horizon-runner", "environment": "dev",
                    "build_number": 1, "build_time": now, "commit_sha": "a1b2c3d4e5f6",
                    "branch": "main"},
        "artifact": {"image_name": "horizon-runner", "image_tag": "simulated", "image_digest":
                     "sha256:" + "0" * 64, "registry": "local-dev"},
        "sbom": {"status": "generated", "format": "cyclonedx-json"},
        "signature": {"status": "verified", "provider": "cosign-simulated"},
        "provenance": {"status": "verified", "slsa_level": "2"},
        "scan_evidence": {"status": "pass", "critical": 0, "high": 0},
        "policy_evaluation": {"overall_decision": "pass", "passed_rules": 8,
                               "warning_rules": 0, "blocked_rules": 0},
        "promotion": {"current_environment": "dev", "promotion_eligibility": "eligible",
                       "promotion_history": [{"environment": "dev", "promoted_at": now}]},
    }
