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

Graphify: refresh after the final commit is required; JSON files have no
structural nodes and the installed package/skill version warning is non-blocking.
Exact next milestone: **C — API contract, validation, and data-boundary tests**.
