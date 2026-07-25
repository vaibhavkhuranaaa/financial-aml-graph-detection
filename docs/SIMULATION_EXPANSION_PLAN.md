# Simulation expansion plan

## Scope

Signal Ledger now serves six bounded deterministic cases from the approved IBM
AML-Data v8 source. Every outcome remains a simulated human exercise, not a
finding about a person, entity, or real transaction.

| Case | Outcome | Count | Deterministic selection rule |
| --- | --- | ---: | --- |
| Fan-out | Simulated escalation | 16 | Earliest source account with 16 labelled rows |
| Cash sequence | Simulated escalation | 8 | First eight labelled Cash rows |
| Mixed-rail sequence | Simulated escalation | 10 | First ten labelled rows in an ordered sequence spanning three rails |
| Comparison | Simulated closure | 5 | First five unlabelled ACH rows |
| ACH sequence | Simulated closure | 8 | First eight unlabelled ACH rows |
| Credit-card sequence | Simulated closure | 8 | First eight unlabelled Credit Card rows |

## Guardrails

- The builder reproduces each case from the approved checksum-bound source;
  there is no hand-authored transaction data.
- Public delivery stays capped at 18 transactions and 18 topology nodes/edges
  per request.
- Account values are pseudonymized. Full source data remains temporary and
  local-only.
- Case labels describe only the simulated exercise. The UI continues to show
  uncertainty and no compliance-action language.

## Future additions

Add a case only when its selection rule, count, rail coverage, deterministic
rebuild, provenance checksum, API-boundary tests, and rendered browser review
are recorded. Keep the catalogue at a small, comprehensible size; do not turn
the replay workbench into a raw-data browser.
