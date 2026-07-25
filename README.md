# Financial AML Graph Detection

Status: **building**. This is a pending research project, not a deployed compliance product and not evidence that any real entity is illicit.

The intended workflow turns the public Elliptic Bitcoin transaction graph into a reproducible graph-learning benchmark: construct the graph, train an explainable baseline and GraphSAGE/GAT candidate, evaluate the minority illicit class, then expose only a bounded research scoring interface.

## Data boundary

- Source: Elliptic transaction graph, obtained under its published access terms.
- Classification: public research data.
- Excluded: customer, bank, account, KYC, and confidential compliance data.
- Record the exact source, license/access terms, checksum, and permitted use before adding data.

## Planned architecture

```mermaid
flowchart LR
  A[Versioned Elliptic files] --> B[Validated graph builder]
  B --> C[Time-aware train and holdout split]
  C --> D[Baseline and GNN training]
  D --> E[Precision recall and error analysis]
  E --> F[Bounded research API and graph view]
```

## Current gate

The draft contract is structurally valid, but first-demo readiness is blocked on reproducible data provenance, implemented graph construction, versioned evaluation, safe examples, tests/CI evidence, and deployment evidence. See `docs/STATE.md`, `docs/HANDOFF.md`, and `portfolio/project.json`.

No metric, demo URL, production claim, or compliance outcome should be added before that evidence exists.

## Public workbench

`frontend/` contains the React + TypeScript Signal Ledger workbench. FastAPI will
serve only a checksum-validated, explicitly approved synthetic replay artifact.
The approved v8 artifact is a bounded, pseudonymized IBM AML-Data slice; it is
realistic synthetic banking data, not anonymized customer data. The full source
remains local-only and is not delivered by the API.

```bash
pip install -r requirements.txt
uvicorn src.app:app --reload
cd frontend && npm install && npm run dev
```

For a production-like local preview, build the frontend and start FastAPI, or use `docker compose -f docker/docker-compose.yml up --build`. The Docker context explicitly copies only the frontend build, FastAPI source, and synthetic fixture.

See [data governance](docs/DATA_GOVERNANCE.md) for the strict separation between the public fixture and local Elliptic research.
The [local-only Elliptic evaluation protocol](docs/ELLIPTIC_EVALUATION_PROTOCOL.md)
defines the required source gate and aggregate-report validation; it does not
publish a benchmark result.
