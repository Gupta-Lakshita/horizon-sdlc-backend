# Horizon Relevance release roadmap

## Completed phases

| Phase | Status | Outcome |
| --- | --- | --- |
| 1–5 | Complete | Release Trust dashboard and detail experience, canonical evidence model, SQLite persistence, repository layer, and containerization. |
| 6 – Runner Integration | Complete | Development-only simulated runner ingestion through `POST /pipeline/api/release-trust/runs`, including validation, repository persistence, Docker packaging, and dashboard-compatible GET data. |

## Phase 6 acceptance record

- The POST route is registered on the same `APIRouter` as the existing Release Trust GET routes.
- Ingestion follows router → service → repository → SQLite commit; the router does not use SQLAlchemy directly.
- A duplicate `release_id` returns `409`; missing or invalid request content returns `422`.
- The backend container includes the ingestion service, runner helper, and request schemas. Generated OpenAPI exposes both `GET` and `POST` for `/release-trust/runs`.
- The simulated runner creates representative evidence only. It does not invoke Jenkins, GitHub Actions, Kubernetes, or the supply-chain repository.

## Next: Phase 7

Phase 7 is blocked on product decisions and integration authority for real supply-chain evidence. Before starting it, define the source of real SBOMs, signatures, provenance, scan findings, and policy decisions; choose runner and CI integration boundaries; and add integration tests with a compatible HTTP test client. No schema redesign or frontend contract change is required by Phase 6.
