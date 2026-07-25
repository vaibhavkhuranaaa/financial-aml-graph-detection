"""Public, read-only response contracts for the Signal Ledger replay API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PublicContract(BaseModel):
    """Reject accidental fields when a public response contract changes."""

    model_config = ConfigDict(extra="forbid")


class HealthResponse(PublicContract):
    status: Literal["ok"]
    mode: Literal["public-ibm-synthetic-scenario"]
    request_inference: Literal[False]
    read_only: Literal[True]


class ReadinessResponse(PublicContract):
    status: Literal["ready"]
    artifact_delivery: Literal["approved"]
    request_inference: Literal[False]
    visitor_persistence: Literal[False]


class CaseCatalogueItem(PublicContract):
    id: str = Field(pattern=r"^sim-[a-z0-9-]{3,64}$")
    outcome: Literal["Simulated escalation", "Simulated closure"]
    transaction_count: int = Field(ge=1, le=18)
    research_rank: Literal["precomputed illustrative ordering"]


class CatalogueResponse(PublicContract):
    items: list[CaseCatalogueItem] = Field(max_length=6)
    maximum: Literal[6]


class CaseDetailResponse(PublicContract):
    id: str = Field(pattern=r"^sim-[a-z0-9-]{3,64}$")
    outcome: Literal["Simulated escalation", "Simulated closure"]
    transaction_count: int = Field(ge=1, le=18)
    uncertainty: str
    rationale: Literal["Simulated analyst rationale is stored only in this browser."]


class Transaction(PublicContract):
    id: str = Field(pattern=r"^txn-\d{2}$")
    timestamp: str
    from_party: str = Field(alias="from", pattern=r"^Party-[A-F0-9]{10}$")
    to_party: str = Field(alias="to", pattern=r"^Party-[A-F0-9]{10}$")
    amount: float = Field(ge=0)
    currency: str = Field(min_length=1, max_length=32)
    rail: Literal["ACH", "Cash", "Cheque", "Credit Card"]


class TimelineResponse(PublicContract):
    case_id: str = Field(pattern=r"^sim-[a-z0-9-]{3,64}$")
    items: list[Transaction] = Field(max_length=18)
    limit: int = Field(ge=1, le=18)
    bounded: Literal[True]


class TopologyNode(PublicContract):
    id: str = Field(pattern=r"^n\d{1,2}$")
    label: str = Field(pattern=r"^Party-[A-F0-9]{10}$")


class TopologyEdge(PublicContract):
    source: str = Field(pattern=r"^n\d{1,2}$")
    target: str = Field(pattern=r"^n\d{1,2}$")


class TopologyResponse(PublicContract):
    case_id: str = Field(pattern=r"^sim-[a-z0-9-]{3,64}$")
    depth: int = Field(ge=1, le=2)
    bounded: Literal[True]
    nodes: list[TopologyNode] = Field(max_length=18)
    edges: list[TopologyEdge] = Field(max_length=18)


class EvidenceItem(PublicContract):
    kind: Literal["replay", "boundary"]
    statement: str


class EvidenceResponse(PublicContract):
    case_id: str = Field(pattern=r"^sim-[a-z0-9-]{3,64}$")
    items: list[EvidenceItem] = Field(max_length=2)
    uncertainty: str


class Distribution(PublicContract):
    classification: Literal["Enhanced Data"]
    status: Literal["approved"]
    notice: str


class ProvenanceResponse(PublicContract):
    provider: str
    dataset: str
    dataset_version: Literal[8]
    version: Literal[8]
    source_ref: str
    retrieved_at: str
    retrieved: str
    source_file: Literal["HI-Small_Trans.csv"]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_schema: list[str] = Field(min_length=11, max_length=11)
    license: Literal["CDLA-Sharing-1.0"]
    license_url: str
    distribution: Distribution
    selection: dict[str, str]
    pipeline_run_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    slice_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    label: Literal["realistic synthetic banking data"]


class MethodologyResponse(PublicContract):
    public: str
    elliptic: str
    limitations: list[str] = Field(min_length=1, max_length=4)


class SafeError(PublicContract):
    detail: str
