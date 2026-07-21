from policy_engine import BLOCK, PASS, WARN, PolicyEngine


def evidence(**overrides):
    value = {
        "sbom": {"status": "verified"},
        "signature": {"status": "verified"},
        "provenance": {"status": "verified"},
        "scan_evidence": {"critical": 0, "high": 0},
        "promotion": {"promotion_history": [{"environment": "dev"}]},
    }
    value.update(overrides)
    return value


def test_policy_engine_passes_complete_evidence():
    result = PolicyEngine().evaluate(evidence())
    assert result["status"] == PASS
    assert all(rule["result"] == PASS for rule in result["rules"])
    assert {"rule": "High vulnerabilities > 0", "result": PASS} in result["rules"]


def test_policy_engine_warns_for_high_vulnerabilities_and_pending_promotion():
    result = PolicyEngine().evaluate(evidence(scan_evidence={"critical": 0, "high": 2}, promotion={"promotion_history": []}))
    assert result["status"] == WARN
    assert result["warning_rules"] == 2
    assert {"rule": "High vulnerabilities > 0", "result": WARN} in result["rules"]


def test_policy_engine_blocks_for_missing_evidence_and_critical_vulnerability():
    result = PolicyEngine().evaluate(evidence(
        sbom={"status": "missing"}, signature={"status": "failed"},
        provenance={"status": "missing"}, scan_evidence={"critical": 1, "high": 0},
    ))
    assert result["status"] == BLOCK
    assert result["blocked_rules"] == 4


def test_policy_engine_thresholds_and_failed_evidence_are_deterministic():
    engine = PolicyEngine()
    passing = engine.evaluate(evidence(scan_evidence={"critical": 0, "high": 0}))
    warning = engine.evaluate(evidence(scan_evidence={"critical": 0, "high": 1}))
    blocking = engine.evaluate(evidence(
        sbom={"status": "failed"}, provenance={"status": "failed"},
        scan_evidence={"critical": 1, "high": 0},
    ))

    assert passing["status"] == PASS
    assert warning["status"] == WARN
    assert blocking["status"] == BLOCK
    assert len(passing["rules"]) == 6
    assert passing == engine.evaluate(evidence(scan_evidence={"critical": 0, "high": 0}))
