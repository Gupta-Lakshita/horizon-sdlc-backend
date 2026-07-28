# Phase 13: Findings Correlation & Promotion Preflight

Release Trust now reads the existing Secure SDLC `vulnerabilities` records as
the detailed finding source of truth. Findings correlate to a release through
the linked platform application and, when present, build number, commit SHA or
artifact digest in scan metadata. Project-only matching is retained for scan
providers that emit partial metadata and each returned finding declares whether
that match is `strong` or `project`.

The detail API adds `findings`, `promotion_preflight`, and `trust_score`; all
existing response fields and runner contracts are unchanged. Aggregation keeps
the detailed findings and reports severity counts, fixes, exploit indicators,
suppression, and exception totals. Existing waiver fields are interpreted as
active only when approved/active and unexpired; expired waivers remain visible.

`PromotionPreflightService` is the single readiness decision: it checks
required evidence, scan completion, the reused Policy Engine decision, and
blocking rule reasons. Promotion uses that result before calling the existing
Promotion Engine mapping. The policy engine evaluates active correlated
critical/high findings, excluding suppressed and active waived findings.

`TrustScoreCalculator` is modular and deterministic: evidence, policy, scans,
and readiness contribute 30/30/20/20 points; severity and active exceptions
deduct fixed published values. Its factors are returned with every score so it
is reproducible and explainable.

Swagger exposes these additive fields through the existing untyped detail
responses and documents `GET /release-trust/runs/{release_id}/preflight`.
