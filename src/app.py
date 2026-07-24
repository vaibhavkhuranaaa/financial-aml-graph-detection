"""Bounded public fixture API for the visual research workbench."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "fixtures" / "public_casefile.json"
DIST_PATH = ROOT / "frontend" / "dist"
MAX_QUEUE = 12
MAX_GRAPH_NODES = 18


def fixture() -> dict:
    """Load precomputed synthetic content; never train or infer on requests."""
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


app = FastAPI(title="Signal Ledger", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "public-synthetic-fixture"}


@app.get("/api/brief")
def brief() -> dict:
    data = fixture()
    return {key: data[key] for key in ("brief", "governance", "evidence")}


@app.get("/api/queue")
def queue(limit: Annotated[int, Query(ge=1, le=MAX_QUEUE)] = 6) -> dict:
    data = fixture()
    return {"items": data["queue"][:limit], "limit": limit, "total": len(data["queue"])}


@app.get("/api/cases/{case_id}")
def case(case_id: str) -> dict:
    selected = next((item for item in fixture()["queue"] if item["id"] == case_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Synthetic case not found.")
    return selected


@app.get("/api/graph/{case_id}")
def graph(case_id: str, depth: Annotated[int, Query(ge=1, le=2)] = 1) -> dict:
    data = fixture()
    graph_data = data["graphs"].get(case_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail="No bounded graph available for this case.")
    nodes = graph_data["nodes"][:MAX_GRAPH_NODES]
    node_ids = {node["id"] for node in nodes}
    return {"case_id": case_id, "depth": depth, "bounded": True, "nodes": nodes, "edges": [edge for edge in graph_data["edges"] if edge["source"] in node_ids and edge["target"] in node_ids]}


if DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="workbench")
