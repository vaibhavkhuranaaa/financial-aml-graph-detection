# Local workbench verification

This runbook verifies the anonymous, read-only public synthetic replay
workbench. It does not deploy the application or authorize public use of the
larger local triage artifact.

## API and frontend

```bash
uv run pytest -q
cd frontend && npm run lint && npm run build
```

Start the locally built workbench in a separate terminal:

```bash
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Then run the browser journey. It drives a real browser through a command line
driver, which the script reads from `BROWSER_CLI` rather than hard coding, so
any driver exposing the same verbs can be used:

```bash
BROWSER_CLI=<your browser automation command> \
  sh scripts/verify_workbench_browser.sh http://127.0.0.1:8000
```

The journey confirms the page has content and no error overlay, exercises a
browser-private simulated rationale/action/reset, and confirms interactive
controls are present. It intentionally contains no API write.

At narrow and wide viewports, inspect the same journey for readable queue,
timeline, audit, topology, and provenance ordering; use keyboard Tab/Enter to
reach case, replay, simulated-record, and topology controls. Reduced-motion
behavior is supplied by the workbench stylesheet.

## The triage desk

The triage desk serves in both application modes now that the owner has recorded
a distribution decision for the triage slice. The public mode additionally
requires the artifact to be the pinned release named by
`APPROVED_TRIAGE_ARTIFACT_SHA256`, so a locally rebuilt artifact is refused there
and admitted under `APP_MODE=local-triage-workbench`. That is deliberate: the
local mode exists to run the artifact an operator just built.

Build the artifact from the local pipeline outputs:

```bash
uv run python -m scripts.build_triage_artifact \
  --transactions <local HI-Small_Trans.csv> \
  --patterns <local HI-Small_Patterns.txt> \
  --store data/alerts/rules-engine-1_<param set hash> \
  --features data/features/alert-features-1.parquet \
  --source-manifest data/provenance/ibm_aml_data_v8_source.json
```

Then serve it and run the journey:

```bash
APP_MODE=local-triage-workbench uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
BROWSER_CLI=<your browser automation command> \
  sh scripts/verify_triage_browser.sh http://127.0.0.1:8000
```

Open the local desk at
`http://127.0.0.1:8000/?surface=triage`. The default route remains the public
six-case replay in every application mode.

Every line the journey prints is an assertion. The ones that carry the design
language are `DEFERRED_ALERTS_VISIBLE`, which proves the alerts below the cut
line are rendered rather than filtered away; `RANK_HAS_NO_COLOUR_SCALE`, which
proves every rank cell computes to one colour; `DISPOSITION_CARRIES_NO_DEFAULT`;
and `BASELINE_WINS_RENDERED` with `STRUCTURAL_ZERO_RENDERED`, which prove the two
states this project most needs are on the surface rather than in a document.

The evidence block adds five: `EVIDENCE_RENDERED`, `FUNNEL_STATES_THE_LOSS`,
`BOTH_DENOMINATORS_SHOWN`, `COSTLIER_PERIODS_VISIBLE`, which proves a period that
cost volume keeps its negative sign on screen, and `PER_PERIOD_VOLUME_SHOWN`.

The view controls add four more. `CUT_LINE_SURVIVES_NARROWING` proves a narrowed
view still draws the cut line, `NARROWED_VIEW_STATED` proves it says how many
alerts it is not showing and that they remain workable,
`CONSEQUENCE_UNCHANGED_BY_VIEW` proves the capacity arithmetic is computed on the
whole period rather than on what is on screen, and `NO_SUPPRESSION_COPY` proves
no control on the surface reads as removing, clearing or dismissing an alert.
`EXPORT_ENABLED_WITH_A_RECORD`, `EXPORT_STATES_LOCAL_BOUNDARY` and
`EXPORT_CARRIES_CLAIMS_BOUNDARY` cover the review record export. The journey does
not click the export itself, because a real download would leave a file on the
verifying machine.

Confirm the public boundary in the same session. Against the committed artifact
the triage route serves; against any rebuild it refuses, and the replay workbench
is unaffected either way:

```bash
APP_MODE=public-synthetic-fixture uv run uvicorn src.app:app --host 127.0.0.1 --port 8001
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8001/api/triage/period   # 200 committed release, 503 any rebuild
curl -fsS http://127.0.0.1:8001/api/triage/period | head -c 400                      # delivery.status approved
curl -fsS http://127.0.0.1:8001/api/readiness                                        # still ready
```

At narrow and wide viewports, check that the capacity control, its consequence
block, the queue and the alert detail follow one linear reading order below the
breakpoint, and that Tab reaches the capacity sliders, every ordering radio, both
view controls, every queue row, the disposition control and the review record
export.

## Docker configuration and local run

```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.yml up --build
curl -fsS http://127.0.0.1:8000/api/health
docker compose -f docker/docker-compose.yml down
```

The compose command must be run only with a local Docker daemon available. The
container may serve the approved bounded synthetic artifact only; no local
source input, triage artifact, model, or metric is part of its build context.
