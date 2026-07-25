# Handoff

Signal Ledger is a public-review, read-only deterministic replay workbench at
`https://signal-ledger-workbench.vercel.app`. Start with `AGENTS.md`,
`README.md`, `docs/STATE.md`, `docs/DATA_GOVERNANCE.md`, and fresh Graphify
output.

## Current release

- Release branch: `main`.
- Public artifact: six bounded IBM AML-Data v8 synthetic cases / 55
  transactions; SHA-256
  `e78b20e8445a7e818c95af6216258487c46cf59ac061c6fcef531f45e10b0160`.
- Artifact pipeline run ID:
  `098fc76310d08f4263fb91e1ba772c7e976444e72eff18a9502f11e930f74140`.
- Portfolio integration records: `portfolio/project.json` and
  `portfolio/release.json`.
- Hosting: one canonical Vercel production deployment; no preview deployment
  is retained.

## Boundaries

The workbench serves only approved realistic synthetic banking replay data. It
does not identify real-world activity, provide compliance advice, use
request-time inference, retain visitor data server-side, or expose local source
data.

Elliptic is local-only except for the owner-approved aggregate summary in
`docs/ELLIPTIC_EVALUATION_SUMMARY.md`. Never publish or route raw rows,
identifiers, graphs, predictions, model files, or full reports.

## Verification baseline

Run:

```bash
uv run pytest -q
uv run ruff check src scripts tests
cd frontend && npm ci && npm run lint && npm run build
docker compose -f docker/docker-compose.yml config
```

For deployment verification, check `/api/readiness`, rejection of POST and
local-only routes, and rendered browser content/no errors. Refresh Graphify
after any committed code change.

## Future work

Use `docs/SIMULATION_EXPANSION_PLAN.md` for additional deterministic cases.
Any new data, service, public claim, or deployment change requires explicit
owner approval and an updated governance record.
