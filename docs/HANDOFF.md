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

## Milestone B status — in progress (2026-07-24)

Do not mark B complete yet. Kaggle metadata independently identifies the current
dataset as version 8 under CDLA-Sharing-1.0; the license requires a published
selected/pseudonymized subset to remain under the agreement with modification
notice, provider attribution, and agreement text/link. The precise local
`HI-Small_Trans.csv` input was independently retrieved and verified on
2026-07-25 UTC as
`b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`. The API
remains fail-closed until an owner-approved distribution decision admits a new
artifact. Exact next work remains **B — Data provenance and deterministic
fixture/replay pipeline**: record approval, rerun the manifest twice, compare
artifact hashes, and then complete the B handoff.
