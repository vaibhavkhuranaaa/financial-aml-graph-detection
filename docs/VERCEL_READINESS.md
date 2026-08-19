# Vercel operations

Signal Ledger is live for public review at
`https://signal-ledger-workbench.vercel.app`. The active deployment is the
canonical Vercel production alias recorded in the private delivery records; it is
not a production or compliance claim.

## Public service boundary

- Vercel serves the built React workbench from `public/` and runs `src.app` as
  one FastAPI Python Function. The function contains two approved bounded
  realistic synthetic banking artifacts and nothing else: the six case replay
  artifact and one review period of the triage artifact.
- `scripts/build_vercel.sh` runs `npm ci`, builds the frontend, and copies the
  resulting static files to `public/`. `vercel.json` excludes tests, docs,
  Docker files and IBM provenance records from the
  Python-function bundle while retaining `data/fixtures/public_casefile.json`
  and `data/fixtures/public_triage.json`.
- Both artifacts are pinned by content digest in `src/app.py`. An artifact that
  does not match its pin is refused with a 503 even when it carries an approved
  distribution decision, so an unreviewed rebuild cannot reach the public URL on
  the strength of a flag it inherited.
- `GET /api/readiness` must return `ready` and approved artifact delivery before
  a deployment is considered usable. `GET /api/triage/period` must return 200
  with `delivery.status` of `approved`.
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
4. Run `python scripts/verify_release.py` before approval. After deployment, run
   it again with the production URL and public repository fixture URL to compare
   the deployed artifact identity, the case bound, and the triage artifact digest.
5. Verify CORS, synthetic labeling, GET-only behavior, and the exclusion of
   local-source routes. Confirm the triage routes serve the pinned release and
   that no tuned rule parameter value appears in any response.

## Local readiness verification

```sh
sh scripts/build_vercel.sh
uv run pytest -q
uv run python scripts/verify_release.py
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/api/readiness
```

The Docker verification remains a separate portability check. Vercel Functions
manage request ports; the application does not depend on server-side visitor
state or a writable filesystem.

The remote verifier proves that the deployed artifact contract matches the
fixture on the public repository. It does not claim full commit provenance,
which requires authenticated Vercel deployment metadata.

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
