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
    research_boundary: str
    limitations: list[str] = Field(min_length=1, max_length=4)


class SafeError(PublicContract):
    detail: str


# The triage surface. Every field below is read from a precomputed artifact. No
# route scores anything, and no visitor supplied value reaches a model or a rule.

ALERT_ID = r"^\d{20}$"
PARTY = r"^Party-[A-F0-9]{10}$"
RULE_ID = r"^R[1-8]$"
ORDERING_ID = r"^(B[0-3]|C1)$"

# The queue is one review period carried whole, because the capacity control has
# to divide by a real denominator. The bound is the largest period the artifact
# builder will publish, and it is enforced here as well as there.
MAX_QUEUE_ALERTS = 3000
MAX_FIRED_RULES = 8
# The evidence block's bounds. The walk forward is seven periods and the model
# holds 39 features; both lists are capped so a rebuilt artifact cannot quietly
# grow the response.
MAX_EVALUATION_PERIODS = 12
MAX_IMPORTANCE_FEATURES = 15


class TriageDelivery(PublicContract):
    """Whether this artifact is approved for publication, stated on every response."""

    status: Literal["approved", "local-only"]
    published: bool
    statement: str


class OrderingSummary(PublicContract):
    id: str = Field(pattern=ORDERING_ID)
    label: str
    kind: Literal["baseline", "challenger"]
    ordered_on: str


class MeasuredOrdering(PublicContract):
    ordering: str = Field(pattern=ORDERING_ID)
    periods: int = Field(ge=1)
    worked: int = Field(ge=1)
    true_positives: int = Field(ge=0)
    precision: float = Field(ge=0, le=1)
    interval: list[float] = Field(min_length=2, max_length=2)


class GateResult(PublicContract):
    metric: str
    threshold: float
    reference_rung: str = Field(pattern=ORDERING_ID)
    lift: float
    interval: list[float] = Field(min_length=2, max_length=2)
    met: bool
    promoted: bool
    statement: str


class MeasuredResult(PublicContract):
    gate: GateResult
    measured: list[MeasuredOrdering] = Field(max_length=6)
    evaluation_periods: int = Field(ge=1)
    k: int = Field(ge=1)


class RuleParameter(PublicContract):
    name: str
    unit: str
    effect: str


class RuleSummary(PublicContract):
    rule_id: str = Field(pattern=RULE_ID)
    name: str
    meaning: str
    parameters: list[RuleParameter] = Field(max_length=6)
    alerts_in_store: int = Field(ge=0)
    alerts_in_period: int = Field(ge=0)
    supported: bool
    typologies: list[str] = Field(max_length=8)
    attempts: int = Field(ge=0)


class TypologyCounts(PublicContract):
    attempts_live: int = Field(ge=0)
    attempts_surfaced: int = Field(ge=0)


class TypologySummary(PublicContract):
    typology: str
    in_period: TypologyCounts
    across_evaluation: TypologyCounts


class OperatingPoint(PublicContract):
    analysts: int = Field(ge=1)
    productive_hours_per_analyst: float = Field(gt=0)
    handling_minutes_per_alert: float = Field(gt=0)
    k_alerts_worked_per_period: int = Field(ge=1)
    assumption_note: str


class PeriodSummary(PublicContract):
    start: str
    alerts: int = Field(ge=1)
    true_positives: int = Field(ge=0)
    base_rate: float = Field(ge=0, le=1)
    label: Literal["realistic synthetic banking data"]


class PeriodAttempt(PublicContract):
    attempt_id: int = Field(ge=0)
    typology: str
    surfaced: bool


Reached = dict[str, int]


class Funnel(PublicContract):
    """Where the attempts are lost. Bounds every ranking number downstream."""

    attempts_live: int = Field(ge=0)
    attempts_surfaced: int = Field(ge=0)
    attempts_reached: Reached
    lost_before_ordering: int = Field(ge=0)
    statement: str


class TypologyDetail(PublicContract):
    """One typology, both denominators. Recall of live scores the rules; recall
    of surfaced scores the ordering, and conflating them blames the ranker for a
    population it never had."""

    typology: str
    attempts_live: int = Field(ge=0)
    attempts_surfaced: int = Field(ge=0)
    reached: Reached
    recall_of_live: float = Field(ge=0, le=1)
    recall_of_surfaced: float = Field(ge=0, le=1)
    interval: list[float] = Field(min_length=2, max_length=2)


class Unattributed(PublicContract):
    alerts_in_population: int = Field(ge=0)
    reached: Reached
    statement: str


class PeriodRow(PublicContract):
    period_start: str
    alerts: int = Field(ge=1)
    worked: int = Field(ge=0)
    coverage: float = Field(ge=0, le=1)
    true_positives: Reached
    precision: dict[str, float]


class VolumeRow(PublicContract):
    period_start: str
    alerts_target: int
    alerts_depth: int
    alerts_freed: int
    attempts_target: int
    attempts_depth: int
    # Signed on purpose. A negative figure means the challenger cost more volume
    # than the reference at equal coverage, which happens and must stay visible.
    attempts_freed: int
    target_was_zero: bool


class VolumeReduction(PublicContract):
    pooled: float
    reference_rung: str
    per_period: list[VolumeRow] = Field(max_length=MAX_EVALUATION_PERIODS)


class StabilityPair(PublicContract):
    period_start: str
    alerts: int = Field(ge=1)
    spearman: float = Field(ge=-1, le=1)


class RankStability(PublicContract):
    threshold: float
    pairs: list[StabilityPair] = Field(max_length=MAX_EVALUATION_PERIODS)


class FeatureGain(PublicContract):
    feature: str
    gain: float = Field(ge=0)


class FeatureImportance(PublicContract):
    features_in_model: int = Field(ge=0)
    carried: int = Field(ge=0)
    bound_note: str
    top: list[FeatureGain] = Field(max_length=MAX_IMPORTANCE_FEATURES)


class EvidenceBlock(PublicContract):
    funnel: Funnel
    typology_detail: list[TypologyDetail] = Field(max_length=8)
    unattributed: Unattributed
    per_period: list[PeriodRow] = Field(max_length=MAX_EVALUATION_PERIODS)
    volume_reduction: VolumeReduction
    rank_stability: RankStability
    feature_importance: FeatureImportance


class TriageEvidenceResponse(PublicContract):
    delivery: TriageDelivery
    claims: str
    reference_rung: str
    k: int = Field(ge=1)
    evidence: EvidenceBlock
    request_inference: Literal[False]


class TriagePeriodResponse(PublicContract):
    delivery: TriageDelivery
    claims: str
    period: PeriodSummary
    operating_point: OperatingPoint
    orderings: list[OrderingSummary] = Field(max_length=6)
    result: MeasuredResult
    rules: list[RuleSummary] = Field(max_length=8)
    typologies: list[TypologySummary] = Field(max_length=8)
    period_attempts: list[PeriodAttempt] = Field(max_length=MAX_QUEUE_ALERTS)
    request_inference: Literal[False]


class QueueRow(PublicContract):
    position: int = Field(ge=1)
    alert_id: str = Field(pattern=ALERT_ID)
    subject: str = Field(pattern=PARTY)
    fired_rules: list[str] = Field(max_length=MAX_FIRED_RULES)
    first_transaction_at: str | None
    alert_amount: float = Field(ge=0)
    contributing_transaction_count: int = Field(ge=0)
    is_true_positive: bool
    unattributed_only: bool
    typologies: list[str] = Field(max_length=8)
    attempt_ids: list[int] = Field(max_length=16)


class QueueResponse(PublicContract):
    delivery: TriageDelivery
    ordering: OrderingSummary
    period_start: str
    alerts: int = Field(ge=1)
    cut_line: int = Field(ge=1)
    cut_line_copy: Literal[
        "Alerts below this line are not reached at this capacity. They stay open and workable."
    ]
    items: list[QueueRow] = Field(max_length=MAX_QUEUE_ALERTS)
    bounded: Literal[True]


class TriggerQuantity(PublicContract):
    key: str
    label: str
    unit: str
    value: float


class TriggerEvidence(PublicContract):
    rule_id: str = Field(pattern=RULE_ID)
    quantities: list[TriggerQuantity] = Field(max_length=6)


class RankingContribution(PublicContract):
    feature: str
    value: float
    contribution: float


class TriageTransaction(PublicContract):
    id: str = Field(pattern=r"^txn-\d{2}$")
    timestamp: str
    from_party: str = Field(alias="from", pattern=PARTY)
    to_party: str = Field(alias="to", pattern=PARTY)
    amount: float = Field(ge=0)
    currency: str = Field(min_length=1, max_length=32)
    rail: str = Field(min_length=1, max_length=32)


class AlertDetailResponse(PublicContract):
    delivery: TriageDelivery
    alert_id: str = Field(pattern=ALERT_ID)
    subject: str = Field(pattern=PARTY)
    period_start: str
    fired_rules: list[str] = Field(max_length=MAX_FIRED_RULES)
    alert_amount: float = Field(ge=0)
    ranks: dict[str, int]
    trigger_evidence: list[TriggerEvidence] = Field(max_length=MAX_FIRED_RULES)
    ranking_explanation: str
    ranking_contributions: list[RankingContribution] = Field(max_length=8)
    contributing_transaction_count: int = Field(ge=0)
    contributing_transactions: list[TriageTransaction] = Field(max_length=8)
    transaction_bound_note: str
    is_true_positive: bool
    typologies: list[str] = Field(max_length=8)
    disposition: Literal["Not recorded. This control carries no default and no recommendation."]
    disposition_storage: Literal[
        "A disposition and its rationale stay in this browser and are never sent to this API."
    ]
