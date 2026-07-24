"""Coverage for concise Swagger/manual Release Trust ingestion."""
from fastapi import FastAPI

from policy_engine import PolicyEngine
from release_trust_schemas import ReleaseTrustPayload
from routers.release_trust import RUN_EXAMPLES, router


def _payload(example_name):
    payload = ReleaseTrustPayload(**RUN_EXAMPLES[example_name]["value"])
    return payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()


def test_manual_examples_produce_their_documented_policy_outcomes():
    engine = PolicyEngine()
    assert engine.evaluate(_payload("pass"))["status"] == "PASS"
    assert engine.evaluate(_payload("warn"))["status"] == "WARN"
    assert engine.evaluate(_payload("block"))["status"] == "BLOCK"


def test_manual_defaults_are_persistence_safe_and_production_metadata_is_preserved():
    manual = _payload("warn")
    assert manual["release"]["application"] == "manual-release"
    assert manual["artifact"]["registry"] == "manual"
    assert manual["scan_evidence"] == {"status": "pass", "critical": 0, "high": 0}

    production = _payload("production")
    assert production["release"]["application"] == "payments"
    assert production["artifact"]["registry"] == "registry.example.com"


def test_openapi_exposes_all_manual_and_production_examples():
    app = FastAPI()
    app.include_router(router)
    examples = app.openapi()["paths"]["/release-trust/runs"]["post"]["requestBody"]["content"]["application/json"]["examples"]
    assert set(examples) == {"pass", "warn", "block", "production"}
