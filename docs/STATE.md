# State

- Lifecycle: `building`
- Deployment and publication: `public-review`
- Canonical URL: `https://signal-ledger-workbench.vercel.app`
- Release branch: `main`

## Current product

Signal Ledger is an anonymous, read-only deterministic replay workbench. It
serves six bounded cases (55 transactions) derived from approved realistic
synthetic IBM AML-Data v8 material. It has no authentication, telemetry,
server-side visitor storage, request-time inference, live feeds, or write API.

The public artifact SHA-256 is
`e78b20e8445a7e818c95af6216258487c46cf59ac061c6fcef531f45e10b0160`; its
pipeline run ID is
`098fc76310d08f4263fb91e1ba772c7e976444e72eff18a9502f11e930f74140`.

## Research and claims boundary

IBM material is realistic synthetic banking data, never anonymized customer
data. The public workbench is not a compliance product, real-time monitor, or
claim about any person or organization.

Elliptic rows, identifiers, graphs, predictions, model files, and full reports
remain local-only. The only public Elliptic material is the owner-approved
aggregate research summary in `docs/ELLIPTIC_EVALUATION_SUMMARY.md`; it is not
a model-selection, operational, or compliance recommendation.

## Verified release evidence

- Deterministic IBM fixture rebuild produced byte-identical output.
- Local Elliptic evaluation evidence passed `scripts/validate_local_evaluation.py`.
- API/configuration suite: 18 passed.
- Ruff and frontend lint/production build passed.
- Public browser verification found six rendered cases, no error overlay, and
  no console errors; readiness reported approved/no-inference/no-persistence,
  POST returned 405, and the Elliptic route returned 404.
- Graphify is fresh at `ca9eb685`.

## Next action

Owner review. Future simulations must follow
`docs/SIMULATION_EXPANSION_PLAN.md`; no new product scope is scheduled.
