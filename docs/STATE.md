# State

- Lifecycle: `building`
- Deployment: `release-pending`
- Publication: `absent`
- Contract migration: v2 draft; no first-demo evidence has been approved

- First-demo evidence still required: dataset source/license/checksum, implemented graph construction, time-aware split, baseline comparison, minority-class evaluation, tests/CI results, safe graph visualization, and deployment observation.

No new deployment, metric, or production claim was introduced by this migration.

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
