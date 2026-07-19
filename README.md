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
| `POST` | `/release-trust/runs` | Ingest one complete simulated Release Trust evidence payload. |
| `GET` | `/release-trust/runs` | List dashboard-ready release summaries. |
| `GET` | `/release-trust/runs/{release_id}` | Retrieve the complete evidence record for a release. |

`POST /release-trust/runs` requires these top-level evidence sections: `release`, `artifact`, `sbom`, `signature`, `provenance`, `scan_evidence`, `policy_evaluation`, and `promotion`. The `release` section requires release ID, application, environment, build metadata, commit SHA, and branch. A duplicate `release_id` returns `409`; malformed or incomplete requests return FastAPI validation errors (`422`).

Use `simulated_release_trust_payload()` from `release_trust_runner.py` to produce development-only payloads. It does not execute CI/CD systems, generate real SBOMs or signatures, or verify policy.

## Release Trust architecture

The frozen evidence model and existing GET response contracts are preserved. Ingestion follows the established boundary:

```text
router POST /release-trust/runs
  -> service.ingest_release_trust(payload)
  -> repository.create_release(payload)
  -> SQLite transaction commit
```

The router validates the request shape through `ReleaseTrustPayload` and delegates ingestion to the service. The service rejects duplicate IDs and incomplete evidence, then calls the repository. Only `release_trust_repository.py` constructs SQLAlchemy `ReleaseRun`, `Artifact`, `SBOM`, `Signature`, `Provenance`, `ScanEvidence`, `PolicyEvaluation`, and `Promotion` records and commits the transaction. API routes do not access SQLAlchemy models directly.

## Simulated ingestion example

```powershell
@'
from release_trust_runner import simulated_release_trust_payload
import json
print(json.dumps(simulated_release_trust_payload("rel-local-001")))
'@ | .\.venv\Scripts\python.exe - | curl.exe -X POST http://localhost:8000/pipeline/api/release-trust/runs -H "Content-Type: application/json" --data-binary "@-"
```

The resulting release immediately appears in the list endpoint and is available to the existing dashboard and detail page without frontend changes.
