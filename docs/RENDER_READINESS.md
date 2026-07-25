# Render readiness and owner gate

This document prepares Signal Ledger for Render. It does not authorize a
deployment, create a Render resource, publish a URL, or change the project
status from `building`.

## Public service boundary

- Service: one Docker web service, serving the committed public frontend and
  approved bounded realistic synthetic banking replay artifact only.
- Health gate: `GET /api/readiness` must return `ready` and approved artifact
  delivery before the service is considered ready.
- Runtime: `APP_MODE=public-synthetic-fixture` is required; any other value
  prevents startup.
- CORS: `SIGNAL_LEDGER_CORS_ORIGINS` is a comma-separated explicit HTTP(S)
  allowlist. It is empty by default because the frontend and API share one
  origin. Do not use `*` or add a third-party origin without owner approval.
- No secret, token, analytics key, database, worker, cron job, telemetry, local
  IBM source, or Elliptic resource is required or configured.

## Owner checklist before any deployment

1. Confirm the target Render account, project, region, plan, public URL, and
   release branch. This repository does not grant that approval.
2. Confirm `render.yaml` is committed and pushed to the intended Git remote;
   `autoDeploy` remains `false` until the owner chooses to deploy.
3. Review the rendered Blueprint: one web service, Docker runtime,
   `/api/readiness` health check, and only the two non-secret environment values.
4. Keep `SIGNAL_LEDGER_CORS_ORIGINS` empty for same-origin serving; if a separate
   approved frontend origin is introduced, record the exact HTTPS origin first.
5. After an owner-approved deploy, run the Milestone I health, CORS, no-write,
   synthetic-label, and local-only boundary checks before any public claim.

## Local readiness verification

```sh
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.yml up --build -d
curl -fsS http://127.0.0.1:8000/api/readiness
docker inspect --format '{{.State.Health.Status}}' docker-workbench-1
docker compose -f docker/docker-compose.yml down
```

The container runs read-only with `/tmp` as a temporary filesystem. It binds
`0.0.0.0:$PORT`, defaulting to 8000 locally, so Render may provide its own port.

## Rollback procedure

Only an owner may carry out a Render rollback.

1. In Render, select the last known-good deploy for the approved service and
   use the dashboard rollback action; do not create a new service or expose a
   new artifact as a workaround.
2. Confirm `GET /api/readiness` returns `ready`, then check health, CORS, fixed
   GET-only routes, synthetic-data labeling, and absence of Elliptic/local-source
   routes.
3. Record the service, release identifier, time, health result, and reason in
   the owner-approved release record. If the approved artifact cannot be served,
   keep the service unavailable rather than substituting data.
