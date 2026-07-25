"""Bounded public IBM AML-Data v8 scenario API; no request-time inference."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.public_replay import approved_public_artifact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "fixtures" / "public_casefile.json"
DIST_PATH = ROOT / "frontend" / "dist"
MAX_TIMELINE = 18
MAX_GRAPH_NODES = 18


def fixture() -> dict:
    try:
        return approved_public_artifact(FIXTURE_PATH)
    except ValueError as error:
        raise HTTPException(503, "Public replay artifact is not approved for delivery.") from error


def selected(case_id: str) -> dict:
    case = next((item for item in fixture()["cases"] if item["id"] == case_id), None)
    if not case:
        raise HTTPException(404, "Public simulated case not found.")
    return case


app = FastAPI(title="Signal Ledger", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "public-ibm-synthetic-scenario", "request_inference": False}


@app.get("/api/cases")
def catalogue() -> dict:
    data = fixture()
    return {"items": [{"id": case["id"], "outcome": case["outcome"], "transaction_count": len(case["transactions"]), "research_rank": "precomputed illustrative ordering"} for case in data["cases"]], "maximum": 2}


@app.get("/api/cases/{case_id}")
def detail(case_id: str) -> dict:
    case = selected(case_id)
    return {"id": case["id"], "outcome": case["outcome"], "transaction_count": len(case["transactions"]), "uncertainty": "Illustrative research context only; not a compliance recommendation or accusation.", "rationale": "Simulated analyst rationale is stored only in this browser."}


@app.get("/api/cases/{case_id}/timeline")
def timeline(case_id: str, rail: str | None = None, limit: Annotated[int, Query(ge=1, le=MAX_TIMELINE)] = MAX_TIMELINE) -> dict:
    transactions = selected(case_id)["transactions"]
    if rail:
        transactions = [item for item in transactions if item["rail"] == rail]
    return {"case_id": case_id, "items": transactions[:limit], "limit": limit, "bounded": True}


@app.get("/api/cases/{case_id}/graph")
def graph(case_id: str, depth: Annotated[int, Query(ge=1, le=2)] = 1) -> dict:
    transactions = selected(case_id)["transactions"]
    parties = list(dict.fromkeys(party for item in transactions for party in (item["from"], item["to"])))[:MAX_GRAPH_NODES]
    ids = {party: f"n{index}" for index, party in enumerate(parties)}
    return {"case_id": case_id, "depth": depth, "bounded": True, "nodes": [{"id": ids[party], "label": party} for party in parties], "edges": [{"source": ids[item["from"]], "target": ids[item["to"]]} for item in transactions if item["from"] in ids and item["to"] in ids]}


@app.get("/api/provenance")
def provenance() -> dict:
    data = fixture()
    record = data["provenance"]
    return record | {
        "version": record["dataset_version"],
        "retrieved": record["retrieved_at"],
        "slice_sha256": data["artifact_sha256"],
        "label": "realistic synthetic banking data",
    }


@app.get("/api/methodology")
def methodology() -> dict:
    return {"public": "Scores and explanations are precomputed; visits never train or infer.", "elliptic": "Local-only: provenance gate, chronological split, unknown-label treatment, baseline/GNN comparison, PR-AUC, precision/recall, calibration, review-capacity and operational-error analysis. No rows, graphs, or metrics are public.", "limitations": ["Simulated outcomes", "No live feeds", "No production or compliance use", "Small bounded public slice"]}


if DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="workbench")
