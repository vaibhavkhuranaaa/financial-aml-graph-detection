# CLAUDE.md — financial-aml-graph-detection

## Project Context
- **Industry:** Financial
- **Role focus:** Data Scientist / AI Engineer hybrid
- **Portfolio goal:** graph-based AML detection is what real compliance teams actually use (entities/transactions as a network, not isolated rows). Very few portfolios attempt graph ML — this is the differentiation project.

## Data
- **Dataset:** Elliptic Data Set — labeled Bitcoin transaction graph (licit/illicit), from real blockchain data, published alongside peer-reviewed AML research
- **Source:** Kaggle "Elliptic Data Set"; extended version "Elliptic++" on GitHub (adds wallet-level data)
- **Access constraints:** open, Kaggle account needed to download

## Required Stack
Python, PyTorch Geometric (GraphSAGE or GAT for the GNN), Flask API for scoring new transaction subgraphs, Docker, Azure Container Apps.

## Standard Repo Structure
```
src/
├── app.py                  # Flask scoring endpoint
├── pipeline/
│   ├── graph_build.py        # construct transaction graph from raw data
│   ├── train.py                # GNN training
│   └── evaluate.py             # precision/recall/AUROC on illicit class
notebooks/                   # EDA + graph visualization
data/                          # Elliptic CSVs (open dataset, fine to include or document download)
tests/
docker/
infra/
.github/workflows/ci.yml
```

## Subagent Ownership
1. **Architect subagent** — confirm structure, plan graph construction → GNN training → API flow
2. **Pipeline subagent** — owns `src/pipeline/` (graph construction, GNN training/eval)
3. **API subagent** — owns `src/app.py`, scores a submitted transaction subgraph
4. **Infra subagent** — owns `docker/` and `infra/`
5. **Docs/test subagent** — owns `tests/`, README must include a visualized transaction subgraph example (this is the single most differentiating visual in the whole portfolio)

## Hard Constraints
- Class imbalance is severe (illicit transactions are a small minority) — report precision/recall/AUROC, not accuracy alone
- Include a graph visualization in the README, not just metrics — this is what makes the project memorable in a screening

## Definition of Done (v1)
- [ ] Graph construction pipeline from Elliptic raw data
- [ ] GNN trained (GraphSAGE or GAT) with reported precision/recall/AUROC on illicit class
- [ ] Visualized example transaction subgraph in README
- [ ] Flask API scoring new subgraphs
- [ ] Dockerized, deployed to Azure
- [ ] README complete, tagged `v1.0`
