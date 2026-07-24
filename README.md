# Horizon SDLC Backend

The Horizon SDLC backend is a FastAPI application backed by SQLite for local development. It includes the Release Trust dashboard API and Phase 6's simulated runner ingestion flow.

## Local development

Create and activate a Python 3.11 virtual environment, install dependencies, then set the required webhook secret before starting Uvicorn.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GITHUB_WEBHOOK_SECRET = "local-dev-webhook-secret"
$env:DATABASE_PATH = "$PWD\.local-data\app.db"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is served below `/pipeline/api`; interactive documentation is available at `http://localhost:8000/pipeline/api/docs`.

## Docker workflow

Copy `.env.local.example` to `.env` and adjust values as needed, then build and start the local stack:

```powershell
Copy-Item .env.local.example .env
docker compose -f docker-compose.local.yaml up --build
```

The backend listens on `http://localhost:8000` by default. SQLite state is retained in the Compose `backend-data` volume. Stop services with `docker compose -f docker-compose.local.yaml down`; add `--volumes` only when intentionally discarding local database data.

## Release Trust API

All endpoints are relative to `/pipeline/api`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/release-trust/runs` | Ingest CI/CD evidence or a concise manual-test Release Trust payload. |
| `GET` | `/release-trust/runs` | List dashboard-ready release summaries. |
| `GET` | `/release-trust/runs/{release_id}` | Retrieve the complete evidence record for a release. |

`POST /release-trust/runs` supports both complete CI/CD evidence and manual testing. For manual use, only `release.release_id` is required; omitted metadata and evidence sections are filled with persistence-safe defaults. The Policy Engine still calculates the outcome from the resulting evidence, so a completed `promotion_history` produces PASS, an empty history produces WARN, and explicitly failed or missing evidence produces BLOCK. CI/CD clients can continue sending every metadata and evidence field unchanged. The legacy `policy_evaluation` section remains accepted when supplied, but is always replaced by the engine result. A duplicate `release_id` returns `409`.

Use `simulated_release_trust_payload()` from `release_trust_runner.py` to produce development-only payloads. It does not execute CI/CD systems, generate real SBOMs or signatures, or verify policy.

## Release Trust architecture

The frozen evidence model and existing GET response contracts are preserved. Ingestion follows the established boundary:

```text
router POST /release-trust/runs
  -> service.ingest_release_trust(payload)
  -> PolicyEngine.evaluate(evidence)
  -> repository.create_release(payload + evaluation)
  -> SQLite transaction commit
```

The router validates the request shape through `ReleaseTrustPayload` and delegates ingestion to the service. The service rejects duplicate IDs and incomplete evidence, evaluates the collected evidence through the reusable `PolicyEngine`, then calls the repository. Only `release_trust_repository.py` constructs SQLAlchemy `ReleaseRun`, `Artifact`, `SBOM`, `Signature`, `Provenance`, `ScanEvidence`, `PolicyEvaluation`, and `Promotion` records and commits the transaction. API routes do not access SQLAlchemy models directly. The submitted legacy policy counts are accepted for compatibility but are replaced by the engine result.

The engine returns `status`, `summary`, and per-rule results. The existing policy decision and rule-count fields remain available, and structured rules are persisted in the policy evaluation section for the detail endpoint.

## Simulated ingestion example

```powershell
@'
from release_trust_runner import simulated_release_trust_payload
import json
print(json.dumps(simulated_release_trust_payload("rel-local-001")))
'@ | .\.venv\Scripts\python.exe - | curl.exe -X POST http://localhost:8000/pipeline/api/release-trust/runs -H "Content-Type: application/json" --data-binary "@-"
```

The resulting release immediately appears in the list endpoint and is available to the existing dashboard and detail page without frontend changes.

## Release Trust evidence storage

Phase 9 stores SBOM, signature, provenance, and scan JSON independently in an
`ObjectStore`. New SQLite `release_runs` records keep only opaque
`*_reference` values; the detail API hydrates those references so its response
remains unchanged. The local provider writes to `data/evidence/<release_id>/`
in local development, or `/app/data/evidence/<release_id>/` in Compose. That
path is inside the existing `backend-data` volume and survives restarts.

`storage/object_store.py` is the provider contract. A future S3 provider only
needs to implement `upload_json`, `download_json`, `exists`, `delete`, and
`build_reference`, then replace the composition in `storage.get_default_object_store()`.
