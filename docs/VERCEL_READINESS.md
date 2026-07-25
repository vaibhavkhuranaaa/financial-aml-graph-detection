# Vercel operations

Signal Ledger is live for public review at
`https://signal-ledger-workbench.vercel.app`. The active deployment is the
canonical Vercel production alias recorded in `portfolio/release.json`; it is
not a production or compliance claim.

## Public service boundary

- Vercel serves the built React workbench from `public/` and runs `src.app` as
  one FastAPI Python Function. The function contains only the approved bounded
  realistic synthetic banking replay artifact.
- `scripts/build_vercel.sh` runs `npm ci`, builds the frontend, and copies the
  resulting static files to `public/`. `vercel.json` excludes tests, docs,
  Docker files, local Elliptic paths, and IBM provenance records from the
  Python-function bundle while retaining `data/fixtures/public_casefile.json`.
- `GET /api/readiness` must return `ready` and approved artifact delivery before
  a deployment is considered usable.
- `APP_MODE=public-synthetic-fixture` is required. CORS remains empty for the
  same-origin frontend/API; never use `*` or add an origin without approval.
- No secret, token, database, worker, cron job, telemetry, local IBM source, or
  Elliptic resource is required by the application.

## Release checklist

1. Keep only the canonical verified production deployment plus any actively
   reviewed preview; remove superseded deployments after verification.
2. Never commit `.vercel/project.json`, `VERCEL_TOKEN`, organization IDs, or
   project IDs.
3. Before merging a release, run the repository verification suite and review
   the generated static workbench and FastAPI Function.
4. After deployment, verify readiness, CORS, synthetic labeling, GET-only
   behavior, and the exclusion of Elliptic/local-source routes.

## Local readiness verification

```sh
sh scripts/build_vercel.sh
uv run pytest -q
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/api/readiness
```

The Docker verification remains a separate portability check. Vercel Functions
manage request ports; the application does not depend on server-side visitor
state or a writable filesystem.

## Rollback procedure

Only an owner may carry out a Vercel rollback.

1. Identify the last known-good deployment and use `vercel rollback
   <deployment-url-or-id>` or the Vercel dashboard. Do not deploy a substitute
   artifact as a workaround.
2. Confirm `/api/readiness`, CORS, fixed GET-only routes, synthetic-data
   labeling, and the absence of Elliptic/local-source routes.
3. Record the project, deployment identifier, time, health result, and reason
   in the owner-approved release record. If the approved artifact cannot be
   served, keep the project unavailable.
