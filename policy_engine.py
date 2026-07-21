"""Reusable policy evaluation for Release Trust evidence."""
from typing import Any, Dict, List


PASS = "PASS"
WARN = "WARN"
BLOCK = "BLOCK"


def _status(evidence: Dict[str, Any], section: str) -> str:
    return str(evidence.get(section, {}).get("status", "")).strip().lower()


class PolicyEngine:
    """Evaluate Release Trust evidence without persistence or API concerns."""

    def evaluate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        sbom_exists = _status(evidence, "sbom") not in {"", "missing", "absent", "none"}
        signature_verified = _status(evidence, "signature") == "verified"
        provenance_exists = _status(evidence, "provenance") not in {"", "missing", "absent", "none"}
        scan = evidence.get("scan_evidence") or {}
        critical = int(scan.get("critical", 0) or 0)
        high = int(scan.get("high", 0) or 0)
        promotion = evidence.get("promotion") or {}
        promotion_completed = len(promotion.get("promotion_history") or []) > 0

        rules: List[Dict[str, str]] = [
            {"rule": "SBOM exists", "result": PASS if sbom_exists else BLOCK},
            {"rule": "Signature verified", "result": PASS if signature_verified else BLOCK},
            {"rule": "Provenance exists", "result": PASS if provenance_exists else BLOCK},
            {"rule": "Critical vulnerabilities == 0", "result": PASS if critical == 0 else BLOCK},
            {"rule": "High vulnerabilities > 0", "result": WARN if high > 0 else PASS},
            {"rule": "Promotion completed", "result": PASS if promotion_completed else WARN},
        ]
        blocked = sum(rule["result"] == BLOCK for rule in rules)
        warnings = sum(rule["result"] == WARN for rule in rules)
        passed = sum(rule["result"] == PASS for rule in rules)
        overall = BLOCK if blocked else WARN if warnings else PASS
        summary = {
            PASS: "Release satisfies all policy rules.",
            WARN: "Release is compliant but has policy warnings.",
            BLOCK: "Release is blocked by one or more policy rules.",
        }[overall]
        return {"status": overall, "summary": summary, "rules": rules,
                "overall_decision": overall.lower(), "passed_rules": passed,
                "warning_rules": warnings, "blocked_rules": blocked}


default_policy_engine = PolicyEngine()
