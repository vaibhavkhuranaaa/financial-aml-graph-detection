# Signal Ledger delivery plan

## Delivery contract

**Current milestone:** B — Data provenance and deterministic fixture/replay pipeline (in progress)

Signal Ledger will be a deployable public research workbench for a deterministic,
synthetic banking-event replay. A visitor can replay a bounded case, inspect its
timeline, topology, evidence, and uncertainty, then create a browser-private,
simulated audit artifact. The product is not a live monitoring system, a
compliance product, or a conclusion about a person or entity.

### Goals

- Make analyst review tangible: case queue, replayable timeline, bounded topology,
  evidence, uncertainty, and a clearly human simulated disposition.
- Demonstrate reproducible data engineering: validated local source ingestion,
  deterministic case selection, precomputed replay artifacts, and visible lineage.
- Provide a polished, accessible React + TypeScript and FastAPI experience that
  is ready to be deployed to Render after owner approval.
- Keep the public surface safe: approved realistic synthetic banking data only;
  no request-time model training or inference.

### Non-goals

- Real transaction monitoring, real-person/entity allegations, compliance advice,
  or automated decision recommendations.
- Live blockchain/financial telemetry, paid data/services, or visitor-submitted
  server-side data.
- Authentication, multi-user collaboration, or server-side decision persistence.
- Public Elliptic data, derived graphs, model outputs, or metrics.
- Deployment, publication, push, merge, or release without explicit owner approval.

## Users and jobs

| User | Job to be done | Evidence of success |
| --- | --- | --- |
| AML analytics leader | Assess whether the workflow respects analyst capacity, evidence, uncertainty, and human review. | Can trace one case from queue through replay, evidence, and a simulated disposition. |
| ML hiring manager | Evaluate end-to-end engineering judgment beyond a model demo. | Can inspect deterministic data lineage, bounded APIs, reproducibility, evaluation boundaries, and delivery hardening. |
| Risk/compliance recruiter | Understand the project’s safety and governance posture quickly. | Sees synthetic-data labeling, limitations, audit semantics, and no-production-claim boundary in the product and docs. |

## Proposed architecture

```mermaid
flowchart LR
  A[Local IBM AML-Data source] --> B[Validate version, checksum, license, schema]
  B --> C[Deterministic selection and pseudonymization]
  C --> D[Precomputed replay and case artifacts]
  D --> E[Read-only FastAPI with bounded responses]
  E --> F[React investigation workbench]
  F --> G[Browser-local notes, simulated decision, local export]
```

- The full IBM input is processed offline/local by default. Public deployment
  serves only legally approved, bounded synthetic artifacts.
- The API is read-only and returns precomputed data. Browser actions never train,
  score, or call a model.
- Browser-local storage may retain a visitor’s simulated rationale/decision and
  a local export. The server stores neither visitor input nor identities.
- The local Elliptic research boundary remains separate and cannot be queried,
  serialized, or displayed by the public product.

## Data, legal, and owner gates

| Gate | Required evidence | Owner decision |
| --- | --- | --- |
| IBM public artifact | Exact source/version, retrieval date, source and output SHA-256, attribution, CDLA-Sharing-1.0 text/link, schema, and deterministic selection manifest. | Approve any public artifact only after distribution obligations are recorded. |
| Elliptic isolation | Local-only path, documented source/access terms/checksum, exclusion tests, and no public rows/graphs/models/metrics. | Separate written permission is required before any public use. |
| Claims | Versioned evidence for every evaluation or operational assertion. | Approve any aggregate research statement before publication. |
| External services | No telemetry or paid resource in v1. | Explicit approval is required before adding either. |
| Deployment | Render readiness evidence and approved account/project. | Explicit owner approval is required before creating a deployment. |

## Milestones and acceptance criteria

### A — Product discovery and delivery plan

- [x] Record product goals, non-goals, users, architecture, risks, gates, and
  owner decisions.
- [x] Define a single public mode: anonymous, read-only, synthetic replay;
  browser-private simulated notes/decisions with local export.
- [x] Define milestones B–I with acceptance and verification requirements.
- [x] Update authoritative handoff/state and record verification results.
- [x] Commit intentional documentation using the configured human identity.

**Complete when:** this plan, `docs/STATE.md`, and `docs/HANDOFF.md` agree on the
current milestone, deployment remains owner-gated, verification passes, and the
documentation commit exists.

**Verification:** `git diff --check`; documentation consistency searches;
`git status --short`; refreshed Graphify report; Ponytail audit outcome.

### B — Data provenance and deterministic fixture/replay pipeline

- [ ] Validate the IBM input checksum, schema, exact version, retrieval record,
  attribution, and CDLA-Sharing-1.0 access/distribution obligations.
- [ ] Create a deterministic selection manifest and generator that records
  inputs, selection rules, pseudonymization, output checksum, and pipeline run ID.
- [ ] Materialize bounded public replay/case artifacts offline; no request-time
  inference or full-dataset browser delivery.
- [ ] Add provenance, determinism, and public-boundary tests.

**Complete when:** rerunning against the verified local input produces the
recorded artifact/hash, the public-output decision is documented, and no
unapproved data can enter the public path.

**Verification:** generator reproduction command; checksum comparison; schema and
selection tests; source/output boundary scan; `git diff --check`.

**Current B status (2026-07-24):** independent metadata and license review is
recorded, and the API now rejects the legacy unverified fixture. The stdlib-only
offline builder and tests are in progress. Completion remains blocked on the
actual `HI-Small_Trans.csv` v8 input: it is not present in this workspace, so
the legacy source checksum cannot yet be independently reproduced and no public
distribution decision has been approved.

### C — API contract, validation, and data-boundary tests

- [ ] Define typed contracts for health/readiness, replay catalogue/detail,
  timeline, bounded topology, evidence, provenance, and methodology.
- [ ] Validate all path/query parameters; enforce response limits and stable
  secure error messages.
- [ ] Make API access read-only, prevent Elliptic/local-source routes, and test
  that visitor input cannot be persisted or trigger inference.

**Complete when:** contract and negative tests cover valid, invalid, boundary,
and forbidden access paths; API behavior matches public data governance.

**Verification:** FastAPI tests, schema/contract tests, public-route allowlist
test, forbidden-route tests, and static search for local data paths.

### D — Useful investigation UX redesign

- [ ] Build the replay workbench: searchable/filterable case queue, replay
  controls, time-filtered timeline, bounded interactive topology, evidence,
  uncertainty, provenance, and recovery states.
- [ ] Preserve one concrete flow: select case → replay/inspect → understand
  evidence/limits → proceed to simulated human record.
- [ ] Support keyboard use, semantic labels, focus visibility, reduced motion,
  responsive layout, and loading/empty/error states.

**Complete when:** the defined workflow works at desktop and mobile widths, every
screen supports a concrete analyst action, and no UI presents a score as a decision.

**Verification:** Impeccable context/review and detector; rendered browser
inspection; keyboard, responsive, loading/empty/error checks; frontend lint/build.

### E — Analyst decision and audit workflow

- [ ] Add browser-private rationale, simulated escalation/closure, local history,
  reset, and JSON export containing fixture/version, visible evidence, action,
  rationale, and timestamp.
- [ ] Include a seeded, read-only example history so visitors can understand the
  audit shape before writing anything.
- [ ] State clearly that decisions are simulated, local to the browser, and not
  compliance actions or server records.

**Complete when:** refresh/reset/export behavior is understandable, accessible,
and cannot send visitor notes to the API.

**Verification:** frontend behavior tests; browser storage/export/reset checks;
network inspection confirming no write requests; accessibility checks.

### F — Evaluation and reproducibility boundary

- [ ] Version a local-only evaluation procedure for Elliptic research with source
  gate, chronological split, explicit unknown-label treatment, baseline/GNN
  comparison, PR-AUC, precision/recall, calibration, review capacity, and
  operational-error analysis.
- [ ] Separate research evidence from public replay artifacts and prevent public
  metrics until independently verified and owner-approved.

**Complete when:** the procedure is reproducible with versioned evidence and the
claims/publication boundary is mechanically documented and tested.

**Verification:** evaluation command and manifest validation; report schema
checks; boundary tests; review of class-imbalance/operational-error reporting.

### G — Browser E2E, accessibility, responsive, and Docker verification

- [ ] Add repeatable browser E2E for replay, filters, topology, decision/export,
  error recovery, and public data boundary.
- [ ] Verify keyboard navigation, accessible names, contrast/focus, reduced
  motion, mobile/tablet/desktop layouts, API tests, production build, and Docker.

**Complete when:** all automated checks pass and browser inspection confirms the
critical journey without console errors.

**Verification:** E2E/accessibility/responsive commands; API suite; frontend
lint/build; Docker build/run/health; compose config; `git diff --check`.

### H — Render deployment readiness

- [ ] Pin reproducible dependencies/build commands and add CI coverage.
- [ ] Add Docker health/readiness checks, environment validation, production CORS
  allowlist, secure error handling, runtime documentation, and rollback runbook.
- [ ] Produce an owner-ready Render checklist without deploying.

**Complete when:** the container is reproducibly buildable, externally configurable
without secrets in source, and deployment/rollback instructions are tested locally.

**Verification:** clean dependency install/build, CI equivalent, Docker health
probe, configuration validation, production CORS tests, and deployment-doc review.

### I — Owner-approved live deployment and post-deploy verification

- [ ] Obtain explicit approval for the Render account/project and production
  deployment.
- [ ] Deploy only the approved public synthetic artifact and record the release.
- [ ] Verify public health, CORS, synthetic labels, no write routes, no local-only
  exposure, and rollback procedure.

**Complete when:** the owner-approved URL, release identifier, health result,
rollback path, and post-deploy checks are recorded.

**Verification:** owner-approved deploy command, deployed health check, smoke/E2E
test, headers/CORS review, data-boundary probe, and rollback dry-run or procedure.

## Risks and dependencies

| Risk/dependency | Control |
| --- | --- |
| IBM redistribution obligations are misunderstood. | Treat public artifact publication as blocked until terms and derivative-output decision are recorded. |
| “Live” presentation is mistaken for real monitoring. | Use “deterministic synthetic replay” wording in UI, API, docs, and deployment copy. |
| A large dataset leaks through API or build artifacts. | Offline materialization, explicit allowlist, response limits, Docker copy boundary, and negative tests. |
| Browser-local audit state is mistaken for durable case management. | Prominent local-only/reset/export language and seeded read-only example history. |
| UI scope turns into a generic dashboard. | Use the select → replay → inspect → record flow as the acceptance test for every surface. |
| Render configuration weakens the public boundary. | Readiness, CORS, health, environment, and deployed-boundary gates before owner approval. |

## Mandatory milestone handoff

Every completed milestone must update this document, `docs/STATE.md`, and
`docs/HANDOFF.md` with:

1. completed work and commit SHA(s);
2. exact verification commands and observed results;
3. remaining work and current blockers;
4. data, access, and deployment status;
5. Graphify status and source-commit freshness;
6. the exact next milestone.

No milestone advances on intended work alone. If context becomes constrained,
finish the current milestone handoff before stopping.

## Milestone A audit record

- **Graphify:** refreshed with `graphify update .`; the report is built from
  `925931e2`, the current source commit at audit time. The tool warned that the
  installed package (`0.9.25`) is newer than the bundled skill (`0.9.23`) and
  that JSON files have no structural nodes; neither warning blocks this milestone.
- **Ponytail audit:** no documentation-scope code simplification was applied.
  Stale graph-oriented CSS is a plausible deletion candidate, but it belongs to
  the visual redesign and requires rendered-browser verification in Milestone D.
  Dependency pinning and Docker install reproducibility belong to Milestone H.
- **Safe simplification decision:** preserve the existing implementation during
  documentation-only Milestone A; no unrelated code or UI changes are mixed into
  this commit.

## Milestone A handoff — 2026-07-24

- **Completed work:** created this delivery plan; established the anonymous,
  read-only replay product boundary; defined milestones B–I, acceptance criteria,
  risks, owner/data gates, and handoff requirements; synchronized
  `docs/STATE.md` and `docs/HANDOFF.md`.
- **Commit:** `docs: add Signal Ledger delivery plan` (configured human identity;
  SHA recorded in Git history).
- **Verification:**
  - `graphify update .` — passed; report refreshed from `925931e2`, matching the
    source commit at refresh time.
  - `git diff --check` — passed.
  - `test -f docs/DELIVERY_PLAN.md` — passed.
  - `rg -n "Current milestone|deterministic synthetic|no authentication|owner approval|B — Data provenance" docs/DELIVERY_PLAN.md docs/STATE.md docs/HANDOFF.md` — passed; all required delivery-boundary terms are present in the three authoritative documents.
  - `git status --short` — only the three intentional Milestone A documentation
    changes were present before commit.
- **Ponytail audit:** no safe simplification was applied in this documentation-only
  milestone. Stale graph-oriented CSS requires a rendered UI verification in
  Milestone D; dependency pinning and Docker reproducibility belong to Milestone H.
- **Data/access/deployment:** public surface remains approved-synthetic-fixture
  only; IBM public-artifact distribution remains gated in B; Elliptic remains
  local-only; no external data access, deployment, publication, push, or merge
  occurred.
- **Graphify:** refreshed before and after this milestone’s documentation commit;
  the final ignored `graphify-out/GRAPH_REPORT.md` was confirmed to match `HEAD`
  at handoff time. JSON structural-node and package/skill-version warnings are
  non-blocking.
- **Remaining work/blockers:** Milestone B cannot complete until the source
  provenance and public-distribution obligations are independently verified.
- **Exact next milestone:** B — Data provenance and deterministic fixture/replay
  pipeline.
