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
    AlertDetailResponse,
    CaseDetailResponse,
    CatalogueResponse,
    EvidenceResponse,
    HealthResponse,
    MethodologyResponse,
    ProvenanceResponse,
    QueueResponse,
    ReadinessResponse,
    SafeError,
    TimelineResponse,
    TopologyResponse,
    TriageEvidenceResponse,
    TriagePeriodResponse,
)
from src.public_replay import approved_public_artifact
from src.triage_artifact import admitted_triage_artifact
from src.triage_artifact import delivery as artifact_delivery

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "fixtures" / "public_casefile.json"
TRIAGE_PATH = ROOT / "data" / "fixtures" / "public_triage.json"
DIST_PATH = (
    ROOT / "public" if (ROOT / "public").exists() else ROOT / "frontend" / "dist"
)
MAX_TIMELINE = 18
MAX_GRAPH_NODES = 18
CASE_ID = Annotated[str, ApiPath(pattern=r"^sim-[a-z0-9-]{3,64}$")]
ALERT_ID = Annotated[str, ApiPath(pattern=r"^\d{20}$")]
ORDERING = Annotated[str, Query(pattern=r"^(B[0-3]|C1)$")]

# The two modes the service runs in. `public-synthetic-fixture` is what the
# deployed surface runs and it serves the approved replay artifact alone. The
# triage artifact is a larger slice of the same source and carries no owner
# approved distribution decision, so in public mode every triage route refuses
# it. `local-triage-workbench` is the analyst desk an operator runs on their own
# machine, where the artifact is admitted on every check except the one that
# governs publication, and every response says so.
PUBLIC_MODE = "public-synthetic-fixture"
LOCAL_TRIAGE_MODE = "local-triage-workbench"
APP_MODES = (PUBLIC_MODE, LOCAL_TRIAGE_MODE)
APPROVED_PUBLIC_ARTIFACT_SHA256 = (
    "e78b20e8445a7e818c95af6216258487c46cf59ac061c6fcef531f45e10b0160"
)
APPROVED_PUBLIC_PIPELINE_RUN_ID = (
    "098fc76310d08f4263fb91e1ba772c7e976444e72eff18a9502f11e930f74140"
)
# The triage artifact's approved release. The distribution decision approves a
# source checksum and the artifact records that approval, but the artifact is
# built from a local pipeline the deployed function cannot see, so approval alone
# would admit any rebuild that carried the flag. Pinning the digest means the
# release that was reviewed is the release the public serves. The pin is public
# mode only: a local workbench exists to run an artifact an operator just built,
# and there it would refuse the very thing it is for.
APPROVED_TRIAGE_ARTIFACT_SHA256 = (
    "6a70f44fcce9962e320bb597ec5ce65abe64157aa912c1c10922c15163df4a5f"
)
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
    app_mode = values.get("APP_MODE", PUBLIC_MODE)
    if app_mode not in APP_MODES:
        raise RuntimeError(f"APP_MODE must be one of {', '.join(APP_MODES)}.")
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
        return approved_public_artifact(
            FIXTURE_PATH,
            expected_sha256=APPROVED_PUBLIC_ARTIFACT_SHA256,
            expected_pipeline_run_id=APPROVED_PUBLIC_PIPELINE_RUN_ID,
        )
    except ValueError as error:
        raise HTTPException(
            503, "Public replay artifact is not approved for delivery."
        ) from error


def selected(case_id: str) -> dict:
    case = next((item for item in fixture()["cases"] if item["id"] == case_id), None)
    if not case:
        raise HTTPException(404, "Public simulated case not found.")
    return case


def triage() -> dict:
    """The triage artifact, or a 503 stating why it is not being served.

    In public mode both the approval gate and the release pin are on, so an
    artifact carrying no owner approved distribution decision, or any rebuild
    other than the reviewed release, is refused here and the surface renders the
    honest state rather than a broken queue.
    """
    public = RUNTIME.app_mode == PUBLIC_MODE
    try:
        return admitted_triage_artifact(
            TRIAGE_PATH,
            require_approval=public,
            expected_sha256=APPROVED_TRIAGE_ARTIFACT_SHA256 if public else None,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            503, "No triage artifact is built. The triage surface is not available."
        ) from error
    except ValueError as error:
        raise HTTPException(
            503, "Triage artifact is not approved for delivery on this surface."
        ) from error


def triage_alert(alert_id: str) -> dict:
    artifact = triage()
    alert = next(
        (item for item in artifact["alerts"] if item["alert_id"] == alert_id), None
    )
    if not alert:
        raise HTTPException(404, "Alert not found in the published review period.")
    return alert


app = FastAPI(
    title="Signal Ledger",
    version="1.2.1",
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
        maximum=6,
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


@app.get(
    "/api/triage/period", response_model=TriagePeriodResponse, responses=ERROR_RESPONSES
)
def triage_period() -> TriagePeriodResponse:
    """The period, the operating point, the orderings and the measured result.

    The measured result travels with the surface so that the outcome can be
    stated where the queue is read. It is the same block the challenger run
    record holds, which is what keeps the interface and the write up from
    drifting apart.
    """
    artifact = triage()
    return TriagePeriodResponse(
        delivery=artifact_delivery(artifact),
        claims=artifact["claims"],
        period=artifact["period"],
        operating_point=artifact["operating_point"],
        orderings=artifact["orderings"],
        result=artifact["result"],
        rules=artifact["rules"],
        typologies=artifact["typologies"],
        period_attempts=artifact["period_attempts"],
        request_inference=False,
    )


@app.get(
    "/api/triage/evidence",
    response_model=TriageEvidenceResponse,
    responses=ERROR_RESPONSES,
)
def triage_evidence() -> TriageEvidenceResponse:
    """The measured run broken back into the units the work happens in.

    This is a separate route rather than a larger period payload because the two
    are read at different moments: the period block is what the queue needs to
    render, and this is what answers whether the queue is worth trusting. Both
    are precomputed and neither scores anything.
    """
    artifact = triage()
    return TriageEvidenceResponse(
        delivery=artifact_delivery(artifact),
        claims=artifact["claims"],
        reference_rung=artifact["result"]["gate"]["reference_rung"],
        k=artifact["result"]["k"],
        evidence=artifact["evidence"],
        request_inference=False,
    )


@app.get("/api/triage/queue", response_model=QueueResponse, responses=ERROR_RESPONSES)
def triage_queue(ordering: ORDERING = "C1") -> QueueResponse:
    """One review period in one ordering, carried whole.

    Every alert in the period is returned, including every alert below the cut
    line, because the cut line is a rule drawn in a queue that stays open rather
    than a filter that removes rows. An ordering that returned only the worked
    head would make the constraint unrenderable.
    """
    artifact = triage()
    summary = next(item for item in artifact["orderings"] if item["id"] == ordering)
    ordered = sorted(artifact["alerts"], key=lambda alert: alert["ranks"][ordering])
    return QueueResponse(
        delivery=artifact_delivery(artifact),
        ordering=summary,
        period_start=artifact["period"]["start"],
        alerts=artifact["period"]["alerts"],
        cut_line=artifact["operating_point"]["k_alerts_worked_per_period"],
        cut_line_copy="Alerts below this line are not reached at this capacity. They stay open and workable.",
        items=[
            {
                "position": alert["ranks"][ordering],
                "alert_id": alert["alert_id"],
                "subject": alert["subject"],
                "fired_rules": alert["fired_rules"],
                "first_transaction_at": alert["first_transaction_at"],
                "alert_amount": alert["alert_amount"],
                "contributing_transaction_count": alert[
                    "contributing_transaction_count"
                ],
                "is_true_positive": alert["is_true_positive"],
                "unattributed_only": alert["unattributed_only"],
                "typologies": alert["typologies"],
                "attempt_ids": alert["attempt_ids"],
            }
            for alert in ordered
        ],
        bounded=True,
    )


@app.get(
    "/api/triage/alerts/{alert_id}",
    response_model=AlertDetailResponse,
    responses=ERROR_RESPONSES,
)
def triage_alert_detail(
    alert_id: ALERT_ID, ordering: ORDERING = "C1"
) -> AlertDetailResponse:
    """Why the alert exists, and why it sits where it sits in the chosen ordering.

    On a baseline the explanation names the baseline and what it ordered on
    rather than disappearing, because the comparison is the point and a missing
    section reads as a missing feature.
    """
    artifact = triage()
    alert = triage_alert(alert_id)
    summary = next(item for item in artifact["orderings"] if item["id"] == ordering)
    return AlertDetailResponse(
        delivery=artifact_delivery(artifact),
        alert_id=alert["alert_id"],
        subject=alert["subject"],
        period_start=artifact["period"]["start"],
        fired_rules=alert["fired_rules"],
        alert_amount=alert["alert_amount"],
        ranks=alert["ranks"],
        trigger_evidence=alert["trigger_evidence"],
        ranking_explanation=(
            f"Position {alert['ranks'][ordering]} of {artifact['period']['alerts']} under {summary['label']}. {summary['ordered_on']}"
        ),
        ranking_contributions=alert["ranking_contributions"]
        if ordering == "C1"
        else [],
        contributing_transaction_count=alert["contributing_transaction_count"],
        contributing_transactions=alert["contributing_transactions"],
        transaction_bound_note=(
            f"Showing {len(alert['contributing_transactions'])} of "
            f"{alert['contributing_transaction_count']} contributing transactions. "
            "The artifact carries a bounded sample and states the true count."
        ),
        is_true_positive=alert["is_true_positive"],
        typologies=alert["typologies"],
        disposition="Not recorded. This control carries no default and no recommendation.",
        disposition_storage="A disposition and its rationale stay in this browser and are never sent to this API.",
    )


@app.get("/api/methodology", response_model=MethodologyResponse)
def methodology() -> MethodologyResponse:
    return MethodologyResponse(
        public="Scores and explanations are precomputed; visits never train or infer.",
        research_boundary="This API serves the approved six-case replay only. Raw source data, the alert store, tuned rule parameters, model execution, and the larger triage artifact stay local.",
        limitations=[
            "Simulated outcomes",
            "No live feeds",
            "No production or compliance use",
            "Small bounded public slice",
        ],
    )


if DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="workbench")
