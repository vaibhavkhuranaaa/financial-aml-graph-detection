# Local workbench verification

This runbook verifies the anonymous, read-only public synthetic replay
workbench. It does not deploy the application or authorize public use of local
Elliptic research.

## API and frontend

```bash
uv run pytest -q
cd frontend && npm run lint && npm run build
```

Start the locally built workbench in a separate terminal:

```bash
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Then run the browser journey (requires the `agent-browser` CLI):

```bash
sh scripts/verify_workbench_browser.sh http://127.0.0.1:8000
```

The journey confirms the page has content and no error overlay, exercises a
browser-private simulated rationale/action/reset, and confirms interactive
controls are present. It intentionally contains no API write.

At narrow and wide viewports, inspect the same journey for readable queue,
timeline, audit, topology, and provenance ordering; use keyboard Tab/Enter to
reach case, replay, simulated-record, and topology controls. Reduced-motion
behavior is supplied by the workbench stylesheet.

## Docker configuration and local run

```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.yml up --build
curl -fsS http://127.0.0.1:8000/api/health
docker compose -f docker/docker-compose.yml down
```

The compose command must be run only with a local Docker daemon available. The
container may serve the approved bounded synthetic artifact only; no local
Elliptic input, evaluation report, model, or metric is part of its build
context.
