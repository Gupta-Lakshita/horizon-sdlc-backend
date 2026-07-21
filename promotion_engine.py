"""Promotion-gate decisions derived from persisted Release Trust policy."""
from typing import Dict


ALLOW = "ALLOW"
MANUAL_APPROVAL = "MANUAL_APPROVAL"
DENY = "DENY"

POLICY_TO_PROMOTION = {
    "PASS": ALLOW,
    "WARN": MANUAL_APPROVAL,
    "BLOCK": DENY,
}

_REASONS = {
    ALLOW: "Policy passed; deployment is permitted.",
    MANUAL_APPROVAL: "Policy has warnings; deployment is paused pending manual approval.",
    DENY: "Policy blocked this release; deployment is not permitted.",
}


class PromotionEngine:
    """Map a persisted policy decision to a reusable deployment-gate result."""

    def evaluate(self, policy_status: str) -> Dict[str, object]:
        normalized = str(policy_status or "").upper()
        try:
            promotion_status = POLICY_TO_PROMOTION[normalized]
        except KeyError as exc:
            raise ValueError("Release has no valid persisted policy decision") from exc
        return {
            "policy_status": normalized,
            "promotion_status": promotion_status,
            "reason": _REASONS[promotion_status],
            "deployment_permitted": promotion_status == ALLOW,
        }


default_promotion_engine = PromotionEngine()
