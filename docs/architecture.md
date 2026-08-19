# Architecture

Two things are described here. What is deployed today, which is the replay
workbench, and what the alert triage product adds. Anything marked planned is not
built and is not claimed.

## Flow

Deployed today:

1. A local, checksum verified IBM AML-Data v8 transaction file, never committed
   and never served.
2. An offline builder, `scripts/build_public_replay.py`, which selects a bounded
   slice under a deterministic rule, pseudonymises it, and writes a replay
   artifact together with a source manifest and a distribution decision record.
3. An admission check that refuses to serve an artifact whose checksum is
   missing, changed, unverified, unapproved or tampered with.
4. A FastAPI function, `src/app.py`, serving typed GET contracts over that one
   artifact with fixed response and topology limits.
5. A React workbench, built by `scripts/build_vercel.sh`, serving the queue,
   timeline, bounded topology, provenance and methodology views.

Built, local only, and imported by nothing the demo serves:

6. `src/pipeline/rules.py`, a typology rules engine over the transaction file,
   emitting one row per fired rule per subject and period with its trigger
   evidence attached. The laundering flag is absent from its input schema.
7. `src/pipeline/alert_store.py`, which collapses those rows into the alert
   store, the unit of analysis for everything downstream. Parquet, partitioned by
   review period, rebuilding byte for byte from the same source and parameters.
8. `src/pipeline/features.py`, an alert level feature build with a strict pre
   decision cutoff and an automated leakage gate. The gate is tested by
   introducing a leak on purpose and asserting that it fails.

9. `src/pipeline/backtest.py`, the backtest harness. It holds the label join and
   is the only place in the project that reads the laundering flag, and it scores
   the baseline ladder B0 to B3 across the evaluation periods with absolute
   counts, per typology attempt counts and bootstrap intervals.

10. `src/pipeline/ranker.py`, the learned ranker. LightGBM lambdarank over the
    alert features, one group per review period, trained on prior periods only
    across the expanding walk forward. Built, measured, and not promoted: it
    beats every rung of the ladder and misses the ship gate. See decision record
    0007.

11. The prevalence sensitivity run. The same ten components run end to end on the
    low prevalence LI-Small variant with the parameter set and every metric
    definition held fixed. The ladder ordering, the missed ship gate and the
    rules engine's 7.4 percent attempt surfacing rate all reproduce. See decision
    record 0008.

12. `src/pipeline/triage.py` and `scripts/build_triage_artifact.py`, the offline
    triage artifact builder, and `src/triage_artifact.py`, its admission check.
    The check sits on the serving path and imports nothing from `src/pipeline/`,
    so the deployed function cannot gain Polars or LightGBM by importing it.
13. The triage desk in `frontend/src/triage.tsx`, served by three GET routes over
    the artifact. Built and running locally. Not published: the triage slice is
    larger than the approved replay scope and the public service refuses it. See
    decision record 0009.

Planned, in phase order:

14. Publication of the triage artifact, which is an owner decision and not an
    engineering one.

## Components

| Component | Technology | Responsibility | Why this over the alternative |
| --- | --- | --- | --- |
| Replay builder | Python, standard library plus the project dependencies | Deterministic bounded slice, pseudonymisation, checksums, manifest | An offline builder keeps every heavy step out of the request path, so the public surface has no inference and no source access |
| Admission check | Python, in `src/public_replay.py` | Refuses an unverified or tampered artifact | A checksum gate is enforceable in a test; a documented promise is not |
| Public API | FastAPI, one Vercel Python function | Typed GET contracts, fixed limits, safe errors | One function serving a precomputed artifact is the cheapest credible topology and removes the entire class of request time abuse |
| Workbench | React and TypeScript, static build | Queue, timeline, bounded topology, provenance, browser private notes | A static build needs no server side session, which is what lets the demo carry no visitor persistence at all |
| Rules engine | Python over Polars | Generates the alert population from written BSA typologies | Writing the detection layer is what makes the baseline real; borrowing someone else's alerts would make the comparison meaningless |
| Backtest harness | Python over Polars, standard library bootstrap | Holds the label join and scores the baseline ladder per period | The only component that reads the laundering flag, so the guarantee that no rule and no feature can reach it is structural rather than a promise |
| Ranker, measured and not promoted | LightGBM lambdarank | Orders alerts inside a stated analyst capacity | Ranking alerts, never raw transactions, because the unit an analyst opens is the alert. Lambdarank because the product decision is an ordering inside a period, not a probability |
| Triage artifact builder | Python over Polars and LightGBM, offline | One review period carried whole, pseudonymised, with every ordering, trigger quantity and per feature contribution precomputed | The capacity control divides by the period's alert count, so a sampled queue would make every consequence number a fiction. The period is the bound; nothing inside it is removed |
| Triage admission check | Python, standard library, in `src/triage_artifact.py` | Refuses an artifact with no approved distribution decision in public mode, and admits it on every other check locally | It imports nothing from `src/pipeline/`, so the serving runtime cannot gain Polars or LightGBM by importing a checksum check |
| Triage desk | React and TypeScript, in the same static build | Capacity control, cut line, ordering switch, alert detail, both honest states | The browser does arithmetic over a fixed table. Doing it client side is what lets the consequence restate live without a request, which is also what keeps request time inference impossible rather than merely absent |

## Contracts

The public API is GET only. There is no write route, no authentication, no
telemetry, and no server side visitor state. Response sizes and topology
expansion are bounded by fixed limits rather than by client request. Malformed
input receives a typed safe error, never a stack trace or a partial payload.

The replay artifact is content addressed. The service will not start serving an
artifact whose recorded checksum does not match its bytes. The triage artifact is
content addressed the same way and carries two further gates: publication
requires an owner recorded distribution decision against the exact source
checksum, and `APP_MODE=public-synthetic-fixture` additionally requires the
artifact to be the pinned release that decision was recorded against. Approval is
a statement about a source and the pin is a statement about a build, so an
unreviewed rebuild carrying the inherited approval flag is refused rather than
served. `APP_MODE=local-triage-workbench` drops the pin alone, because that mode
exists to run the artifact an operator just built, and every other check still
runs there.

An alert record carries a stable identifier, subject account, period, the set of
rules that fired, per rule trigger evidence, and the transaction identifiers that
raised it. Every feature declares the cutoff timestamp it was computed against,
which is what the leakage gate checks. What reaches the triage artifact is a
pseudonymised subset of that record: the computed trigger quantities are
published and the tuned parameter values are not, filtered by a per rule
allowlist so a parameter added later is dropped by default.

## Demo topology

Vercel free tier. A static React build in `public/`, produced at deploy time by
`scripts/build_vercel.sh`, plus one FastAPI Python function. `vercel.json`
excludes tests, docs, Docker files and provenance records from the function
bundle, and `.vercelignore` keeps build output, caches and dependencies out of
the upload. `APP_MODE=public-synthetic-fixture` is required on the deployment, which is what makes it refuse the triage artifact. CORS stays empty for
the same origin frontend. No database, no worker, no cron job, no secret.

`GET /api/readiness` must report ready and approved artifact delivery before a
deployment counts as usable.

## Scaled topology

Not built. If a larger IBM AML-Data v8 variant is selected, the rules engine and
feature build move to partitioned columnar storage and out of core processing,
run once for evidence, and are torn down inside the recorded cost ceiling. The
public demo does not change: it continues to serve a precomputed bounded
artifact, because putting inference behind a public URL is a claims decision, not
a capacity one.

The first component to break past the demo topology is the rules engine, which
holds counterparty windows in memory. Nothing about the serving path is on that
path.

## Operations

Health is `GET /api/health`. Readiness is `GET /api/readiness`, which reports
approved artifact delivery rather than process liveness alone. A deployment that
cannot serve the approved artifact is left unavailable rather than substituted.

Rollback is owner only: identify the last known good deployment, roll back to it,
then reverify readiness, CORS, GET only behaviour, synthetic data labelling and
the absence of any local research route. See `docs/VERCEL_READINESS.md`.
