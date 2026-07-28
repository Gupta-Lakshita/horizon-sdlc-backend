# Phase 15: Enterprise hardening and production readiness

## Deployment

Run the existing Docker Compose deployment with a persistent volume mounted at
`/app/data`. Set `DATABASE_URL` (or `DATABASE_PATH`), `EVIDENCE_DATA_PATH`,
`GITHUB_WEBHOOK_SECRET`, and `BACKEND_SESSION_SECRET` before startup. Set
`RELEASE_TRUST_STRICT_CONFIG=true` in production: it rejects local object
storage and `LOCAL_DEV_AUTH=true`. Place the backend behind a TLS-terminating
reverse proxy, forward `X-Request-ID`, and restrict `/pipeline/api` to trusted
origins with `BACKEND_CORS_ORIGINS`.

The service is request-stateless; its durable release, audit, and evidence
state is SQLite plus the configured ObjectStore. For multiple replicas, use a
shared production database and a shared provider implementation registered in
the existing ObjectStore factory; SQLite/local evidence are appropriate only
for a single-node deployment. No clustering or leader election is required.

## Storage, backup, and recovery

Use an immutable, versioned object store for evidence. Back up the database
and evidence together, verify a restore in an isolated environment, then
start the application normally: additive schema creation preserves existing
records. Keep audit records with the same retention policy as release
decisions. Never place credentials in release payloads or audit details.

## Operations

`GET /pipeline/api/release-trust/health` returns database, ObjectStore,
configuration, and runner readiness. It intentionally omits credential and
provider topology details. Platform administrators can use `GET
/pipeline/api/release-trust/metrics` and `/audit`; both are included in the
OpenAPI document. Metrics are vendor-neutral counters suitable for an export
adapter: release creation, evidence activity, runner traffic, promotion
attempt/failure, API requests/errors, and latency units.

Structured audit records are stored in `release_trust_audit_logs`. They record
timestamp, identity when supplied, operation, resource, result, correlation
ID field, and non-sensitive details. Current operations cover release
creation, evidence upload/retrieval, runner ingestion, and promotion.

## Access and licensing

Release Trust permissions are mapped onto the existing platform roles, rather
than creating new identities: view releases/evidence (all established roles),
create releases and upload evidence (developer, release manager, or platform
admin), execute promotion (release manager or platform admin), and policy or
storage administration (platform admin). Existing application ACL and
environment authorization continue to apply.

Release creation invokes the existing enterprise license validator for the
`release_trust` feature. It remains backward compatible when platform license
enforcement is disabled. With enforcement enabled, the normal signed license
and entitlement configuration controls the capability.

## Upgrade and troubleshooting

Deploy the new image, retain the existing `/app/data` volume, and check the
health endpoint after startup. The only schema addition is the append-only
`release_trust_audit_logs` table; no existing table or API field is changed.
If health is degraded, first confirm database access, evidence path/provider
configuration, and runner reachability. A strict-configuration startup error
names the invalid setting without exposing a secret.
