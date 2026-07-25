"""Bounded public IBM AML-Data v8 scenario API; no request-time inference."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, NamedTuple
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi import Path as ApiPath
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.contracts import (
    CaseDetailResponse,
    CatalogueResponse,
    EvidenceResponse,
    HealthResponse,
    MethodologyResponse,
    ProvenanceResponse,
    ReadinessResponse,
    SafeError,
    TimelineResponse,
    TopologyResponse,
)
from src.public_replay import approved_public_artifact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "fixtures" / "public_casefile.json"
DIST_PATH = (
    ROOT / "public" if (ROOT / "public").exists() else ROOT / "frontend" / "dist"
)
MAX_TIMELINE = 18
MAX_GRAPH_NODES = 18
CASE_ID = Annotated[str, ApiPath(pattern=r"^sim-[a-z0-9-]{3,64}$")]
Rail = Literal["ACH", "Cash", "Cheque", "Credit Card"]
ERROR_RESPONSES = {
    404: {"model": SafeError},
    422: {"model": SafeError},
    503: {"model": SafeError},
}


class RuntimeConfig(NamedTuple):
    app_mode: str
    cors_origins: tuple[str, ...]


def runtime_config(values: Mapping[str, str]) -> RuntimeConfig:
    app_mode = values.get("APP_MODE", "public-synthetic-fixture")
    if app_mode != "public-synthetic-fixture":
        raise RuntimeError("APP_MODE must be public-synthetic-fixture.")
    origins = tuple(
        origin.strip()
        for origin in values.get("SIGNAL_LEDGER_CORS_ORIGINS", "").split(",")
        if origin.strip()
    )
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or origin == "*":
            raise RuntimeError(
                "SIGNAL_LEDGER_CORS_ORIGINS must be an explicit HTTP(S) allowlist."
            )
    return RuntimeConfig(app_mode=app_mode, cors_origins=origins)


RUNTIME = runtime_config(os.environ)


def fixture() -> dict:
    try:
        return approved_public_artifact(FIXTURE_PATH)
    except ValueError as error:
        raise HTTPException(
            503, "Public replay artifact is not approved for delivery."
        ) from error


def selected(case_id: str) -> dict:
    case = next((item for item in fixture()["cases"] if item["id"] == case_id), None)
    if not case:
        raise HTTPException(404, "Public simulated case not found.")
    return case


app = FastAPI(
    title="Signal Ledger",
    version="0.3.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(RUNTIME.cors_origins),
    allow_methods=["GET"],
    allow_headers=[],
    allow_credentials=False,
)


@app.exception_handler(RequestValidationError)
def invalid_request(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"detail": "Invalid request parameters."}
    )


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        mode="public-ibm-synthetic-scenario",
        request_inference=False,
        read_only=True,
    )


@app.get("/api/readiness", response_model=ReadinessResponse, responses=ERROR_RESPONSES)
def readiness() -> ReadinessResponse:
    fixture()
    return ReadinessResponse(
        status="ready",
        artifact_delivery="approved",
        request_inference=False,
        visitor_persistence=False,
    )


@app.get("/api/cases", response_model=CatalogueResponse, responses=ERROR_RESPONSES)
def catalogue() -> CatalogueResponse:
    data = fixture()
    return CatalogueResponse(
        items=[
            {
                "id": case["id"],
                "outcome": case["outcome"],
                "transaction_count": len(case["transactions"]),
                "research_rank": "precomputed illustrative ordering",
            }
            for case in data["cases"]
        ],
        maximum=2,
    )


@app.get(
    "/api/cases/{case_id}", response_model=CaseDetailResponse, responses=ERROR_RESPONSES
)
def detail(case_id: CASE_ID) -> CaseDetailResponse:
    case = selected(case_id)
    return CaseDetailResponse(
        id=case["id"],
        outcome=case["outcome"],
        transaction_count=len(case["transactions"]),
        uncertainty="Illustrative research context only; not a compliance recommendation or accusation.",
        rationale="Simulated analyst rationale is stored only in this browser.",
    )


@app.get(
    "/api/cases/{case_id}/timeline",
    response_model=TimelineResponse,
    responses=ERROR_RESPONSES,
)
def timeline(
    case_id: CASE_ID,
    rail: Rail | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_TIMELINE)] = MAX_TIMELINE,
) -> TimelineResponse:
    transactions = selected(case_id)["transactions"]
    if rail:
        transactions = [item for item in transactions if item["rail"] == rail]
    return TimelineResponse(
        case_id=case_id, items=transactions[:limit], limit=limit, bounded=True
    )


@app.get(
    "/api/cases/{case_id}/graph",
    response_model=TopologyResponse,
    responses=ERROR_RESPONSES,
)
def graph(
    case_id: CASE_ID, depth: Annotated[int, Query(ge=1, le=2)] = 1
) -> TopologyResponse:
    transactions = selected(case_id)["transactions"]
    parties = list(
        dict.fromkeys(
            party for item in transactions for party in (item["from"], item["to"])
        )
    )[:MAX_GRAPH_NODES]
    ids = {party: f"n{index}" for index, party in enumerate(parties)}
    return TopologyResponse(
        case_id=case_id,
        depth=depth,
        bounded=True,
        nodes=[{"id": ids[party], "label": party} for party in parties],
        edges=[
            {"source": ids[item["from"]], "target": ids[item["to"]]}
            for item in transactions
            if item["from"] in ids and item["to"] in ids
        ],
    )


@app.get(
    "/api/cases/{case_id}/evidence",
    response_model=EvidenceResponse,
    responses=ERROR_RESPONSES,
)
def evidence(case_id: CASE_ID) -> EvidenceResponse:
    case = selected(case_id)
    return EvidenceResponse(
        case_id=case_id,
        items=[
            {
                "kind": "replay",
                "statement": f"This deterministic replay contains {len(case['transactions'])} bounded synthetic transactions.",
            },
            {
                "kind": "boundary",
                "statement": "All scores and explanations are precomputed; visits cannot train, infer, or persist visitor input.",
            },
        ],
        uncertainty="Illustrative research context only; not a compliance recommendation or accusation.",
    )


@app.get(
    "/api/provenance", response_model=ProvenanceResponse, responses=ERROR_RESPONSES
)
def provenance() -> ProvenanceResponse:
    data = fixture()
    record = data["provenance"]
    return ProvenanceResponse.model_validate(
        record
        | {
            "version": record["dataset_version"],
            "retrieved": record["retrieved_at"],
            "slice_sha256": data["artifact_sha256"],
            "label": "realistic synthetic banking data",
        }
    )


@app.get("/api/methodology", response_model=MethodologyResponse)
def methodology() -> MethodologyResponse:
    return MethodologyResponse(
        public="Scores and explanations are precomputed; visits never train or infer.",
        elliptic="Local-only: provenance gate, chronological split, unknown-label treatment, baseline/GNN comparison, PR-AUC, precision/recall, calibration, review-capacity and operational-error analysis. No rows, graphs, or metrics are public.",
        limitations=[
            "Simulated outcomes",
            "No live feeds",
            "No production or compliance use",
            "Small bounded public slice",
        ],
    )


if DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="workbench")
