# Phase 12: Reference Runner Adapters

The adapters in `release_trust_adapters` are HTTP clients only. They call the stable `/release-trust/runner/v1` API and never import the service, repository, models, SQLite database, or object store.

## Authentication

Use the existing Secure SDLC signed-session bearer credential. Set `HORIZON_AUTHORIZATION="Bearer <platform-session-token>"`; the normal Runner API RBAC and environment authorization checks apply. No API-key, OAuth, or provider authentication is added by these references.

## CLI uploader

Run from the backend source directory:

```sh
export HORIZON_API_URL=https://horizon.example.com/pipeline/api
export HORIZON_AUTHORIZATION='Bearer <platform-session-token>'
python -m release_trust_adapters.cli create-release @examples/runner-api/create-release.json
python -m release_trust_adapters.cli upload-evidence payments-2026.07.28-101 @examples/runner-api/evidence.json
python -m release_trust_adapters.cli publish-event payments-2026.07.28-101 @examples/runner-api/event.json
python -m release_trust_adapters.cli update-status payments-2026.07.28-101 @examples/runner-api/status.json
python -m release_trust_adapters.cli get-status payments-2026.07.28-101
```

Each payload can be inline JSON or `@path.json`. The CLI prints JSON on success, writes a concise error to stderr, and returns 0 on success or 1 on invalid input, timeout, network failure, or final HTTP failure.

## REST examples

The JSON files in `examples/runner-api` are direct request bodies for `POST /releases`, `POST /releases/{release_id}/evidence`, `POST /releases/{release_id}/events`, and `PATCH /releases/{release_id}/status`. Query with `GET /release-trust/runner/v1/releases/{release_id}/status`.

## Jenkins reference

`JenkinsReferenceAdapter` maps standard Jenkins environment values (`JOB_NAME`, `BUILD_NUMBER`, `BUILD_URL`, `GIT_URL`, `GIT_COMMIT`, and `BRANCH_NAME`) to the v1 create-release payload. The executable [Jenkinsfile](../examples/jenkins/Jenkinsfile) demonstrates create, evidence, event, and completion-status calls. Store the existing Horizon session credential as a Jenkins secret exposed as `HORIZON_SESSION`; do not put it in the Jenkinsfile.

## Failure handling

`RunnerApiClient` uses a configurable timeout, retry count (default 3), and exponential backoff (1, 2, 4 seconds). It retries network errors and transient HTTP responses: 408, 429, 500, 502, 503, and 504. Other 4xx responses fail immediately, preserving useful server response detail. Configure `HORIZON_TIMEOUT_SECONDS` and `HORIZON_RETRIES` for the CLI.

## Enterprise flow

`Pipeline → create release → upload metadata/evidence → publish lifecycle events → update status → existing policy evaluation → existing promotion request`.

Policy and promotion remain Release Trust responsibilities; the adapters do not make database calls or alter policy/promotion semantics.
