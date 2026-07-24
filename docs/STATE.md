# State

- Lifecycle: `building`
- Deployment: `release-pending`
- Publication: `absent`
- Contract migration: v2 draft; no first-demo evidence has been approved

- First-demo evidence still required: dataset source/license/checksum, implemented graph construction, time-aware split, baseline comparison, minority-class evaluation, tests/CI results, safe graph visualization, and deployment observation.

No new deployment, metric, or production claim was introduced by this migration.

## Workspace stabilization — 2026-07-23

- Stable source commit: `3ffc5b4f068c5c917ce8a0f04f314782702f81b7`
- Verification: manifest JSON parsed and `git diff --check` passed.
- Rollback baseline: `e291ceb98bc347d776d7999fbb49b5374a566c1e`
- Graphify: incrementally checked and stamped to the stable source commit; JSON coverage remains a direct-source review requirement.
