# Signal Ledger

Signal Ledger is a read-only workbench for replaying a bounded, deterministic
realistic synthetic banking-event case file. It is a portfolio research
demonstration, not a compliance product, real-time monitor, or statement about
any real person or organization.

## Live workbench

The public-review URL is [signal-ledger-workbench.vercel.app](https://signal-ledger-workbench.vercel.app).
It serves only the approved 21-row replay fixture. It has no authentication,
telemetry, server-side visitor storage, request-time inference, or write API.

## What it demonstrates

- A bounded case queue, replayable timeline, and keyboard-operable topology.
- Precomputed research context, evidence, uncertainty, provenance, and
  methodology.
- Browser-private simulated escalation/closure notes with local-only export.
- Typed, validated FastAPI GET contracts with fixed limits and safe errors.

The workbench labels the data as realistic synthetic banking data. It never
describes it as anonymized customer data.

## Data boundary

The public artifact is a checksum-bound, pseudonymized slice derived from IBM
AML-Data v8 under the recorded CDLA-Sharing-1.0 distribution decision. The full
IBM source is not committed or served. Elliptic is strictly local-only: no
Elliptic rows, graphs, models, artifacts, metrics, or endpoints are public.

See [data governance](docs/DATA_GOVERNANCE.md) and the [delivery plan](docs/DELIVERY_PLAN.md)
for the source, disclosure, and release boundary.

## Local development

```bash
pip install -r requirements-dev.txt
uvicorn src.app:app --reload

cd frontend
npm ci
npm run dev
```

For a production-like local check:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Verification

```bash
uv run pytest -q
uv run ruff check src scripts tests
cd frontend && npm ci && npm run lint && npm run build
```

The local-only Elliptic evaluation protocol is implemented but does not contain
or publish an evaluation result. Do not make model-performance, operational, or
compliance claims without separately approved aggregate evaluation evidence.
