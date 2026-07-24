# Handoff

Read `AGENTS.md`, `README.md`, `docs/STATE.md`, and fresh Graphify output before work.

Next action: verify dataset permission and provenance, then implement the smallest graph-construction and baseline-evaluation slice. Record precision/recall and failure modes only from a versioned run. Preserve all existing dirty work and do not invent public claims.

Rollback the contract migration only through a reviewed `git revert 3ffc5b4f068c5c917ce8a0f04f314782702f81b7`; do not reset to `e291ceb98bc347d776d7999fbb49b5374a566c1e`.
