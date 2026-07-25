# Vercel readiness and owner gate

This document prepared Signal Ledger for Vercel. It did not itself authorize a
deployment, link a Vercel project, create a public URL, or change the project
status from `building`. The subsequent owner-approved deployment attempt and
its unresolved target/protection decision are recorded in `docs/STATE.md` and
`docs/HANDOFF.md`.

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

## Owner checklist before any deployment

1. Select and explicitly approve the Vercel account/team, project, plan, public
   URL, release branch, and whether the release is preview or production.
2. Install/login or provide a Vercel token outside source control, then link the
   exact project with `vercel link --yes --project <project> --scope <team>`.
   Never commit `.vercel/project.json`, `VERCEL_TOKEN`, org IDs, or project IDs.
3. Run `vercel build --prod`, then review the built static workbench and the
   single FastAPI Function before any `vercel deploy --prebuilt --prod` command.
4. After an owner-approved deployment, run the Milestone I health, CORS,
   synthetic-label, no-write, and local-only boundary probes before making any
   public claim.

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
