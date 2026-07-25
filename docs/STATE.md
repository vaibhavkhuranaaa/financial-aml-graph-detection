# State

- Lifecycle: `building`
- Deployment: `release-pending`
- Publication: `absent`
- Contract migration: v2 draft; no first-demo evidence has been approved

## Delivery ownership — 2026-07-24

- Current milestone: **I — Owner-approved live deployment and post-deploy verification** (blocked pending owner approval).
- Product direction: anonymous, read-only deterministic synthetic-event replay;
  browser-private simulated notes/decisions with local export; no authentication,
  server-side visitor data, or request-time inference.
- Deployment remains `release-pending`; publication remains absent. Vercel is a
  future owner-gated target, not an approved deployment.
- The authoritative acceptance criteria, legal/data gates, risks, milestones,
  and required handoff fields are recorded in `docs/DELIVERY_PLAN.md`.
- No deployment, publication, evaluation, or production/compliance claim has
  been advanced by this planning milestone.
- Milestone A verification passed: fresh Graphify at `925931e2`, Ponytail audit
  recorded with no documentation-scope change, delivery-document consistency
  search passed, and `git diff --check` passed. The exact next milestone is
  **B — Data provenance and deterministic fixture/replay pipeline**.

- First-demo evidence still required: dataset source/license/checksum, implemented graph construction, time-aware split, baseline comparison, minority-class evaluation, tests/CI results, safe graph visualization, and deployment observation.

No new deployment, metric, or production claim was introduced by this migration.

## Milestone B — complete (2026-07-24)

- Independent metadata review verified Kaggle dataset version 8, Erik Altman
  attribution, the HI-Small transaction schema listing, and CDLA-Sharing-1.0.
  The v8 source checksum was reproduced on 2026-07-25 UTC as
  `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`; the owner
  approved the bounded CDLA-Sharing-1.0 artifact for that exact checksum.
- The public API serves the approved bounded artifact. An offline,
  deterministic builder records local source metadata/schema/checksum, selection
  and pseudonymization rules, pipeline run ID, and artifact checksum; it also
  requires an owner-approved distribution decision for that exact source hash.
- Two local runs produced the same artifact hash
  `62b1d7476466f5456f61ef0d019db52536cf13e46e584724d5346a9ad8b75db2`; the full
  IBM input and temporary outputs were removed. Elliptic remains local-only; no
  deployment, publication, push, or merge occurred. Exact next milestone: **C**.

## Milestone C — complete (2026-07-24)

- Added strict typed FastAPI response contracts for health/readiness, replay
  catalogue/detail, timeline, bounded topology, evidence, provenance, and
  methodology. The API is a fixed GET-only public allowlist; malformed inputs
  receive stable safe errors, docs/OpenAPI routes are disabled, and all replay
  access remains bounded and precomputed.
- Added contract, positive, negative, limit-boundary, forbidden-route, and
  rejected-write tests. Verification passed: `uv run pytest -q` (6 passed),
  Ruff format/check, Python compilation, static local-boundary search, and
  `git diff --check`. The test client emits a third-party Starlette/httpx
  deprecation warning only.
- Elliptic and local source remain unavailable through the public API; no
  visitor data can be persisted or trigger inference. No UI work, deployment,
  publication, push, merge, or external access occurred. Exact next milestone:
  **D — Useful investigation UX redesign**.
- Graphify was refreshed code-only and reclustered against `7ed3cef7` after the
  implementation commit. Documentation semantic extraction has no LLM backend;
  the package/skill version warning is non-blocking.

## Milestone D — complete (2026-07-24)

- Rebuilt the public Signal Ledger workbench as an accessible operate-mode
  investigation desk: search/filter the two approved synthetic cases, replay
  their bounded timelines with rail filtering and controls, inspect a bounded
  keyboard-operable pseudonymous topology, read evidence/uncertainty and
  provenance, and recover from loading, empty, and API-error states.
- The screen preserves the concrete flow select → replay/inspect → understand
  limits → proceed to the later simulated human record. It deliberately does
  not add the browser-local decision, notes, persistence, history, or export
  work reserved for E.
- Verification passed: Impeccable detector returned no findings; frontend lint
  and production build, API tests (6 passed), and `git diff --check` passed.
  Local rendered desktop and 390px mobile inspection verified selection,
  replay, empty filtering, keyboard topology, and zero console warnings/errors.
  No deployment, publication, push, merge, or external access occurred. Exact
  next milestone: **E — Analyst decision and audit workflow**.
- Graphify was refreshed code-only and reclustered against `09e50125` after the
  implementation commit. Documentation semantic extraction has no LLM backend;
  the package/skill version warning is non-blocking.

## Milestone E — complete (2026-07-24)

- Added browser-private simulated audit records with optional rationale,
  simulated escalation/closure, resettable local history, seeded read-only
  example, and JSON export. The export captures the approved replay version and
  checksum, visible evidence, action, rationale, and timestamp.
- The page states that records are simulated, local to the browser, never sent
  to the API, and not compliance actions. Static inspection confirms the
  frontend retains one default GET `fetch`; visitor state is limited to one
  browser-local storage key.
- Verification passed: Impeccable detector and independent finish review found
  no issues; frontend lint/build, API tests (6 passed), and `git diff --check`
  passed. Browser testing confirmed persistence, local export confirmation,
  reset to the read-only example, keyboard controls, and zero console errors.
  No deployment, publication, push, merge, or external access occurred. Exact
  next milestone: **F — Evaluation and reproducibility boundary**.
- Graphify was refreshed code-only and reclustered against `21427a4c` after the
  implementation commit. Documentation semantic extraction has no LLM backend;
  the package/skill version warning is non-blocking.

## Milestone F — complete (2026-07-24)

- Added a versioned local-only Elliptic evaluation protocol, manifest/report
  validator, and command. It enforces source/access/checksum evidence,
  chronological splitting, explicit unknown-label treatment, baseline/GNN
  comparison, and aggregate PR-AUC, precision/recall, calibration,
  review-capacity, and operational-error reporting.
- The validator rejects public paths, public/unapproved reports, raw/derived
  identifiers, source-checksum mismatches, and incomplete evaluation evidence.
  The protocol does not produce or publish a dataset, graph, model, prediction,
  metric, or claim.
- Verification passed: 12 tests, Ruff format/check, compilation, and `git diff
  --check`. No deployment, publication, push, merge, external access, or
  evaluation run occurred. Exact next milestone: **G — Browser E2E,
  accessibility, responsive, and Docker verification**.
- Graphify was refreshed code-only and reclustered against `420f82e7` after the
  implementation commit. Documentation semantic extraction has no LLM backend;
  the package/skill version warning is non-blocking.

## Milestone G — complete (2026-07-24)

- Added a reusable, read-only browser-verification harness and public-boundary
  test. The harness exercises rendered content, error-overlay absence, the
  browser-private simulated rationale/action/reset flow, and interactive
  controls; it never sends a write request.
- Verification passed: API suite (14 passed), Ruff check and formatting check
  for the new G file, Python
  compilation, frontend lint/production build, Docker Compose configuration,
  `git diff --check`, and local desktop-browser inspection. The browser found
  labelled inputs, keyboard-operable topology nodes, focus and reduced-motion
  rules, no error overlay, and no warnings/errors.
- The repeatable `agent-browser` CLI journey passes, including local simulated
  rationale/action/reset and interactive-control checks. Docker Compose built
  the production image, started the read-only public service, and returned the
  expected `/api/health` response; the temporary container and network were
  then removed. No deployment, publication, push, merge, or external access
  occurred. Exact next milestone: **H — Vercel deployment readiness**.

## Milestone H — complete (2026-07-24)

- Added pinned runtime and frontend dependency inputs, deterministic Docker
  install/build commands, dynamic `$PORT` binding, a readiness health check,
  fail-closed configurable CORS validation, CI container-readiness coverage, a
  non-deploying Vercel Function/static-build configuration, and an owner-gated
  Vercel rollback runbook.
- Verification passed: 18 API/configuration tests, Ruff check, compilation,
  pinned `npm ci` lint/build, Compose configuration, Blueprint YAML parsing,
  and `git diff --check`. No hosting account resource, service, API token, deployment,
  publication, push, or merge was used.
- Final container verification passed: a no-cache Compose rebuild served
  `/api/readiness`, reported Docker `healthy`, rejected an unapproved CORS
  preflight with 400, and cleaned up its container/network. A separate
  read-only `PORT=8080` container also served readiness and reported healthy.
  The owner subsequently selected Vercel, so the Render-only configuration was
  replaced by a locally verified Vercel FastAPI Function/static-build setup.
  Vercel remains owner-gated: no project link, deployment, publication, push,
  or merge was used. Exact next milestone is **I**, which requires explicit
  owner approval before any deployment action.

## Signal Ledger public-fixture workbench — 2026-07-24

- A React + TypeScript visual analyst workbench is implemented behind a FastAPI API. Its public mode serves only the committed synthetic fixture; scores are precomputed, queue responses and graph neighborhoods are bounded, and benchmark rows are not committed, served, or raw-displayed.
- The interface exposes a research-ranked synthetic queue, keyboard-operable bounded graph nodes, investigation evidence, source/access terms, governance notes, limitations, loading/empty/error recovery, and a Docker/CI build boundary.
- Verification recorded for this source state: FastAPI contract tests (`2 passed`), TypeScript lint and production build, Docker Compose configuration, `git diff --check`, Impeccable detector (no findings), and local browser validation of rendered content, queue selection, bounded graph interaction, mobile graph visibility, and zero browser console errors.
- This verifies the public fixture experience only. It is not benchmark evaluation evidence, a production deployment, a compliance system, or a finding about real activity.

## Owner-requested next pivot

- Preserve Signal Ledger rather than changing its product direction in this revision.
- Public v1 uses a small deterministic IBM AML-Data scenario slice, subject to exact-version, checksum, CDLA-Sharing-1.0, attribution, and scenario-selection verification. Label it realistic synthetic banking data, never anonymized customer data.
- Build two guided, time-bound cases: one simulated escalation and one simulated closure. Show pseudonymous parties, rails, timestamps, amounts, counterparties, timeline playback, bounded topology, evidence, uncertainty, and audit-style rationale.
- Exclude live blockchain telemetry from v1. Precompute public scores and explanations; never train or infer on visitor requests.
- Keep Elliptic local-only under the recorded CC BY-NC-ND boundary. Verify provenance, chronological split, unknown-label treatment, baseline/GNN comparison, PR-AUC, precision/recall, calibration, review-capacity metrics, and operational errors before making any aggregate claim public.
- The narrative is: limited analyst capacity → bounded graph-learning research → timeline and topology → human escalate/close decision → audit record. It is not a production system, accusation, or compliance recommendation.

## Workspace stabilization — 2026-07-23

- Stable source commit: `3ffc5b4f068c5c917ce8a0f04f314782702f81b7`
- Verification: manifest JSON parsed and `git diff --check` passed.
- Rollback baseline: `e291ceb98bc347d776d7999fbb49b5374a566c1e`
- Graphify: incrementally checked and stamped to the stable source commit; JSON coverage remains a direct-source review requirement.
