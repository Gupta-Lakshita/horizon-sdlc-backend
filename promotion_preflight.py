"""Single promotion eligibility service consumed by PromotionEngine callers."""
from typing import Any, Dict

from policy_engine import BLOCK, PASS


class PromotionPreflightService:
    def evaluate(self, release: Dict[str, Any]) -> Dict[str, Any]:
        policy = release.get("policy_evaluation") or {}
        findings = (release.get("findings") or {}).get("summary", {})
        rules = policy.get("rules") or []
        reasons = [r["rule"] for r in rules if r.get("result") == BLOCK]
        evidence_ready = all((release.get(key) or {}).get("status", "").lower() not in {"missing", "failed", ""} for key in ("sbom", "signature", "provenance", "scan_evidence"))
        if not evidence_ready: reasons.append("Required evidence or scan is incomplete")
        if policy.get("overall_decision", "").upper() == BLOCK: reasons.append("Required policy did not pass")
        return {"eligible": not reasons, "status": PASS if not reasons else BLOCK, "blocking_reasons": list(dict.fromkeys(reasons)), "required_evidence_exists": evidence_ready, "required_policies_passed": policy.get("overall_decision", "").upper() != BLOCK, "required_scans_completed": (release.get("scan_evidence") or {}).get("status", "").lower() not in {"missing", "failed", ""}, "finding_summary": findings}


class TrustScoreCalculator:
    def calculate(self, release: Dict[str, Any], preflight: Dict[str, Any]) -> Dict[str, Any]:
        summary = (release.get("findings") or {}).get("summary", {})
        deductions = {"critical": 35 * summary.get("critical", 0), "high": 12 * summary.get("high", 0), "medium": 4 * summary.get("medium", 0), "low": summary.get("low", 0), "active_exceptions": 2 * summary.get("exception_count", 0)}
        evidence = 30 if preflight["required_evidence_exists"] else 0
        policy = 30 if preflight["required_policies_passed"] else 0
        scans = 20 if preflight["required_scans_completed"] else 0
        readiness = 20 if preflight["eligible"] else 0
        score = max(0, min(100, evidence + policy + scans + readiness - sum(deductions.values())))
        return {"score": score, "max_score": 100, "factors": {"evidence_completeness": evidence, "policy_compliance": policy, "scan_completeness": scans, "promotion_readiness": readiness, "deductions": deductions}, "explainable": "Deterministic base points minus severity and active-exception deductions."}
