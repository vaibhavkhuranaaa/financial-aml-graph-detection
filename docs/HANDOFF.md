# Handoff

Release automation is intentionally `planned` in `portfolio/release.json`. Do not deploy or publish until the project reaches release-candidate status with verified data provenance and evaluation evidence.

Read `AGENTS.md`, `README.md`, `docs/STATE.md`, and fresh Graphify output before work.

## Milestone A handoff — complete (2026-07-24)

Completed work: established `docs/DELIVERY_PLAN.md` as the delivery source of
truth and synchronized `docs/STATE.md`. The delivery model is an anonymous,
read-only deterministic synthetic event replay workbench: precomputed approved
synthetic artifacts only; no authentication, no server-side visitor
notes/decisions, no request-time inference, and no deployment without explicit
owner approval.

Read `docs/DELIVERY_PLAN.md` before beginning any milestone. It is the delivery
source of truth for product goals, non-goals, architecture, acceptance criteria,
risks, data/legal gates, owner decisions, and verification requirements.

Verification: `graphify update .` refreshed the report at source commit
`925931e2`; `git diff --check`, delivery-document consistency search, and
delivery-plan presence check passed. Ponytail found no documentation-scope
simplification safe to apply; stale UI CSS is deferred to D and dependency/Docker
reproducibility is deferred to H. The intentional documentation commit is
`docs: add Signal Ledger delivery plan` using the configured human identity.

Data/access/deployment status: public mode remains approved synthetic fixture
only; IBM distribution validation is still gated in B; Elliptic is local-only;
no deployment, publication, push, merge, or external access occurred. Graphify
was refreshed after the documentation commit and confirmed to match `HEAD` at
handoff time (JSON structural-node and package/skill-version warnings are
non-blocking). Current blocker: the IBM public-artifact provenance and
distribution decision must be independently verified. Exact next milestone:
**B — Data provenance and deterministic fixture/replay pipeline**.

Current public surface: Signal Ledger is a verified React + TypeScript / FastAPI synthetic-fixture workbench. It renders a bounded research queue and keyboard-operable graph investigation without serving local benchmark records or training on request. Tests, production frontend build, Docker Compose configuration, UI detector, and local browser interactions were verified on 2026-07-24; this is public-fixture verification, not release, deployment, or benchmark-evaluation evidence.

Owner-approved next action: retain Signal Ledger and build a recruiter-facing banking transaction-monitoring case study around a verified, attributed IBM AML-Data scenario slice. Provide one simulated escalation and one simulated closure with pseudonymous payment parties, rails, timestamps, amounts, counterparties, timeline playback, bounded graph context, evidence, uncertainty, and an audit-style rationale. IBM data must be labeled realistic synthetic banking data, not anonymized customers.

Before committing an IBM slice, verify its exact version, retrieval date, checksum, CDLA-Sharing-1.0 terms, attribution, and selection method. Exclude live telemetry from v1 and precompute all public scoring. In parallel, keep Elliptic local-only behind its provenance gate and evaluate chronological splits, unknown labels, baseline/GNN comparison, PR-AUC, precision/recall, calibration, review-capacity metrics, and operational errors. Never publish Elliptic raw/derived rows, graphs, or metrics without independently verified permission. Preserve local research artifacts and do not invent claims.

Rollback the contract migration only through a reviewed `git revert 3ffc5b4f068c5c917ce8a0f04f314782702f81b7`; do not reset to `e291ceb98bc347d776d7999fbb49b5374a566c1e`.

## Milestone B handoff — complete (2026-07-24)

Completed work: independently verified IBM AML-Data v8 source metadata,
attribution, CDLA-Sharing-1.0 obligations, exact checksum, and published schema;
corrected the duplicate positional `Account` header mapping; recorded source and
distribution manifests; materialized the approved 21-row bounded artifact;
retired the legacy bypass; and preserved a read-only, precomputed API boundary.

Commits: `65d8ed1 feat: gate public replay artifacts`, `7ee5446 docs: record
IBM source verification`, and `5a04424 feat: materialize approved replay fixture`.

Verification: the official `HI-Small_Trans.csv` v8 file reproduced source SHA-256
`b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`; two
`scripts/build_public_replay.py` runs produced byte-identical output (file
SHA-256 `79ab2c9350cedd3eac394e13e0c67bd595cfbc3e2e4cca137cd46e75d69c9409`),
artifact hash `62b1d7476466f5456f61ef0d019db52536cf13e46e584724d5346a9ad8b75db2`,
and run ID `d7bd5a14342256427d08604a6e7ce9d3f2ce60ff5e3b154298fffd8db6a31356`.
`uv tool run ruff check src scripts tests`, `uv run pytest -q` (5 passed),
`uv run python -m compileall -q src scripts`, `cd frontend && npm run build`,
and `git diff --check` all passed.

Data/access/deployment: the owner approved publication only for the bounded,
pseudonymized CDLA-Sharing-1.0 artifact tied to the exact source checksum. The
full IBM input and temporary outputs were removed; Elliptic remains local-only.
No deployment, external publication, push, or merge occurred.

Graphify: refreshed after the final handoff commit and confirmed to match `HEAD`.
The final map is code-only because documentation semantic extraction has no LLM
backend; JSON provenance files have no structural nodes, and the installed
package/skill version warning is non-blocking.
Exact next milestone: **C — API contract, validation, and data-boundary tests**.

## Milestone C handoff — complete (2026-07-24)

Completed work: added `src/contracts.py` with strict public response contracts
for health/readiness, catalogue/detail, timeline, bounded topology, evidence,
provenance, and methodology. `src/app.py` now validates the public case-ID
shape, permitted rails, timeline limit (1–18), and topology depth (1–2), has a
fixed GET-only API allowlist, disables docs/OpenAPI routes, and returns the
stable safe 422 body `{"detail": "Invalid request parameters."}`. New evidence
is derived only from the already approved bounded synthetic replay artifact.

Verification: `uv run pytest -q` passed (6 tests); `uv tool run ruff format
--check src/app.py src/contracts.py tests/test_app.py`, `uv tool run ruff check
src tests`, `uv run python -m compileall -q src tests`, static local-boundary
search, and `git diff --check` passed. The suite covers typed responses,
positive requests, invalid and limit-boundary requests, safe 404/422 errors,
route allowlisting, missing Elliptic/local-source/docs/OpenAPI routes, and 405
rejection of POSTed visitor data. The test client reports only a third-party
Starlette/httpx deprecation warning.

Data/access/deployment: public mode remains the exact approved, checksum-bound
IBM v8 artifact only, labeled realistic synthetic banking data. Elliptic and
the full IBM input remain local-only and unavailable by route or payload. No
visitor input reaches persistence, training, or inference. No deployment,
publication, push, merge, or external access occurred.

Ponytail audit: no verified-safe simplification was applied; the existing API
was already minimal and the typed contracts/validation/tests are required C
scope. Graphify was refreshed code-only and reclustered against implementation
commit `7ed3cef7`; documentation semantic extraction remains unavailable without
an LLM backend, and the installed package/skill version warning is non-blocking.
Exact next milestone: **D — Useful investigation UX redesign**; do not begin it
as part of this milestone handoff.

## Milestone D handoff — complete (2026-07-24)

Completed work: rebuilt `frontend/src/main.tsx` and `frontend/src/styles.css`
within the established Signal Ledger evidence-desk visual system. The public
workbench now supports filtering the approved case queue, selecting a case,
play/pause/reset replay, rail-filtered bounded timeline, keyboard-operable
bounded pseudonymous topology, evidence, uncertainty, provenance, and clear
loading/empty/error recovery. The visible flow is select → replay/inspect →
understand evidence and limits → proceed to the simulated-record workflow.

Scope boundary: D does not implement the browser-local rationale, decision,
history, reset, or JSON export planned for E. It explicitly states that the
later simulated record sends nothing to the API. The page continues to label
the fixture realistic synthetic banking data; it makes no real-person,
compliance, production, benchmark, or request-time inference claim.

Verification: Impeccable context and finish review completed; its mechanical
detector returned `[]`. `cd frontend && npm run lint && npm run build`, `uv run
pytest -q` (6 passed), and `git diff --check` passed. Local browser inspection
confirmed desktop and 390px mobile layouts, case selection, replay advancement,
filter empty state, keyboard topology selection, and zero browser-console
warnings/errors. Graphify was refreshed code-only and reclustered against
`09e50125` after the implementation commit; documentation
semantic extraction remains unavailable without an LLM backend, and the
installed package/skill version warning is non-blocking. No deployment,
publication, push, merge, or external access occurred. Exact next milestone:
**E — Analyst decision and audit workflow**; do not begin it as part of this
milestone handoff.

## Milestone E handoff — complete (2026-07-24)

Completed work: added an inline browser-private simulated audit workflow to the
existing workbench. Visitors may enter an optional rationale and choose a
simulated escalation or closure. Those records, plus resettable history, live
only under a single browser-local key. A seeded read-only example remains after
reset so the audit shape is understandable before a visitor writes anything.
The local JSON export includes fixture dataset version and replay checksum,
visible evidence statements, simulated action, rationale, and timestamp.

Data/access boundary: the UI prominently says records are simulated, browser
private, not compliance actions, and never sent to the API. Static inspection
confirms its only `fetch` has no write method and all visitor state is limited
to `localStorage`; the FastAPI allowlist and POST rejection tests remain intact.
No local IBM source or Elliptic content is added or exposed.

Verification: the Impeccable detector returned `[]` and the independent finish
review found no material issue. `cd frontend && npm run lint && npm run build`,
`uv run pytest -q` (6 passed), static request/storage scan, and `git diff
--check` passed. Local browser testing verified rationale entry, simulated
decision, persistence after refresh, local export confirmation, reset to the
read-only example, keyboard controls, and zero console warnings/errors. The
in-app browser did not emit a download event, but the export confirmation and
client-side Blob download path were verified. Graphify was refreshed code-only
and reclustered against `21427a4c` after the implementation commit;
documentation semantic extraction remains unavailable without an LLM backend,
and the installed package/skill version warning is non-blocking.

No deployment, publication, push, merge, or external access occurred. Exact
next milestone: **F — Evaluation and reproducibility boundary**; do not begin
it as part of this milestone handoff.

## Milestone F handoff — complete (2026-07-24)

Completed work: added `docs/ELLIPTIC_EVALUATION_PROTOCOL.md`, the versioned
`signal-ledger-local-evaluation/v1` validator contract, and
`scripts/validate_local_evaluation.py`. A future untracked local manifest must
record source/access terms, absolute local source path, retrieval time, SHA-256,
chronological boundaries, explicit unknown-label treatment, and versioned
baseline/GNN identifiers. An aggregate-only local report must include PR-AUC,
precision, recall, calibration, review capacity, and operational-error analysis
for both families.

Data/access boundary: the validator rejects public delivery paths, public or
unapproved reports, raw/derived identifiers, mismatched source checksums,
non-chronological splits, and incomplete metrics. It does not run training or
evaluation, and no Elliptic source, graph, model, prediction, metric, or claim
was created. Public API routes remain fixed and do not import local evaluation
evidence.

Verification: `uv run pytest -q` passed (12 tests); Ruff format/check,
`python -m compileall`, and `git diff --check` passed. Boundary tests cover
aggregate-only evidence, local-only publication status, chronological splitting,
baseline/GNN presence, raw-identifier rejection, missing metrics, and public
delivery-path rejection. Graphify was refreshed code-only and reclustered
against `420f82e7` after the implementation commit; documentation semantic
extraction remains unavailable without an LLM backend, and the installed
package/skill version warning is non-blocking.

No deployment, publication, push, merge, or external access occurred. Exact
next milestone: **G — Browser E2E, accessibility, responsive, and Docker
verification**; do not begin it as part of this milestone handoff.
