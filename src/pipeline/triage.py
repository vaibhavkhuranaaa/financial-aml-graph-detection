"""The triage artifact: one review period, bounded, pseudonymised, precomputed.

This is the offline builder behind the triage surface. It takes the alert store,
the feature table, the label join and the measured backtest, and writes a single
JSON artifact holding everything the workbench needs to answer the one question
the product exists for: at the capacity I actually have, what do I get and what
do I give up.

Three properties are structural rather than promised.

1. **Nothing is computed at request time.** Every ordering, every trigger
   quantity and every ranking contribution is written here, offline, once. The
   surface does arithmetic over a fixed table; it never scores anything, and no
   visitor supplied value reaches a model. The model does not exist on the
   serving path at all.
2. **The tuned parameter values do not leave this process.** Rule evidence
   carries both the computed quantities that met a trigger and the parameters
   that set it. Only the computed quantities are published. The parameter set is
   described by name, unit and direction of effect, which is what
   `design-language.md` and `spec.md` section 5 permit, because a precise trigger
   set published openly reads as an evasion guide.
3. **Accounts are pseudonymised on the way in**, with the same function the
   replay artifact uses, and the raw identifier never enters the payload.

The artifact is bounded twice: to one review period, and to a fixed number of
contributing transactions per alert. Both bounds are stated in the payload with
the true count beside them, because a truncated list that does not say it is
truncated is a lie about the evidence.

Building this artifact does not approve it for publication. `approved_artifact`
refuses anything without an approved distribution decision recorded against the
exact source checksum, exactly as the replay artifact's admission check does.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from src.pipeline import alert_store, backtest, features, ranker, rules
from src.public_replay import canonical_bytes, pseudonym
from src.triage_artifact import ARTIFACT_SCHEMA, admitted_triage_artifact

# Contributing transactions carried per alert. An alert can contribute hundreds
# through R3 and R4, and the surface needs a readable sample rather than the
# whole set, so the list is bounded and the true count travels beside it.
MAX_CONTRIBUTING_TRANSACTIONS = 8

# Ranking contributions carried per alert, by absolute contribution.
MAX_EXPLANATION_FEATURES = 5

# Model features carried in the evidence block, by gain. The full list is 39 and
# the tail is uninformative; the count of the whole list travels beside the
# bounded one so the truncation states itself.
MAX_IMPORTANCE_FEATURES = 15

LADDER_AND_CHALLENGER = [*backtest.LADDER, "C1"]

# What each ordering sorts on, in the analyst's language. The detail view shows
# this instead of a ranking explanation when the queue is on a baseline, because
# a baseline that renders no explanation reads as a missing feature rather than
# as the point of the comparison.
ORDERING_COPY: dict[str, dict[str, str]] = {
    "B0": {
        "label": "Random",
        "kind": "baseline",
        "ordered_on": "A seeded shuffle of the period's alerts. It is the floor, and its precision is the population base rate by construction.",
    },
    "B1": {
        "label": "Chronological, oldest first",
        "kind": "baseline",
        "ordered_on": "The timestamp of the alert's earliest contributing transaction. This is a queue worked in the order it arrived.",
    },
    "B2": {
        "label": "Alert amount descending",
        "kind": "baseline",
        "ordered_on": "The summed paid amount of the alert's contributing transactions, largest first. The sum mixes currencies, because the source carries fourteen of them and no exchange rates, which is also what an institution sorting without a rate table would get.",
    },
    "B3": {
        "label": "Rules only priority",
        "kind": "baseline",
        "ordered_on": "The highest prior hit rate among the rules that fired, computed over earlier periods only and shrunk toward the pooled rate, then oldest alert first inside a band.",
    },
    "C1": {
        "label": "Learned ranker",
        "kind": "challenger",
        "ordered_on": "A LightGBM lambdarank model over the alert features, trained on earlier periods only. It is measured and it is not promoted, so this ordering is shown for comparison and is not a shipped product.",
    },
}

# Rule catalogue copy. Capability and effect direction only: the tuned value, the
# exact window length and the proximity band are never published here.
RULE_COPY: dict[str, dict[str, Any]] = {
    "R1": {
        "name": "Structuring below a reporting threshold",
        "meaning": "Repeated payments from one account sitting just below a reporting threshold inside a single period.",
        "parameters": [
            {"name": "reporting threshold", "unit": "currency amount", "effect": "raising it moves the band the rule watches upward"},
            {"name": "proximity band", "unit": "share of the threshold", "effect": "tightening it lowers alert volume and lowers recall together"},
            {"name": "minimum count", "unit": "payments per period", "effect": "raising it lowers volume sharply"},
        ],
    },
    "R2": {
        "name": "Rapid movement of funds",
        "meaning": "A credit followed by a near equal debit from the same account within a short window, which is money passing through rather than resting.",
        "parameters": [
            {"name": "amount tolerance", "unit": "share of the credit", "effect": "widening it admits less exact pass throughs and raises volume"},
            {"name": "window length", "unit": "hours", "effect": "lengthening it raises volume"},
            {"name": "minimum amount", "unit": "currency amount", "effect": "raising it lowers volume"},
        ],
    },
    "R3": {
        "name": "Fan in",
        "meaning": "Many distinct originators paying one beneficiary inside a period.",
        "parameters": [
            {"name": "minimum originators", "unit": "distinct counterparties per period", "effect": "raising it lowers volume and is the parameter that decides whether a multi day attempt is ever seen"},
        ],
    },
    "R4": {
        "name": "Fan out",
        "meaning": "One originator paying many distinct beneficiaries inside a period.",
        "parameters": [
            {"name": "minimum beneficiaries", "unit": "distinct counterparties per period", "effect": "raising it lowers volume and is the parameter that decides whether a multi day attempt is ever seen"},
        ],
    },
    "R5": {
        "name": "Round amount repetition",
        "meaning": "Repeated exactly round payments, which are atypical of organic activity.",
        "parameters": [
            {"name": "roundness multiple", "unit": "currency amount", "effect": "raising it makes the rule unfireable on this source, because the simulator draws amounts with cents"},
            {"name": "minimum amount", "unit": "currency amount", "effect": "raising it lowers volume"},
            {"name": "minimum count", "unit": "payments per period", "effect": "raising it lowers volume"},
        ],
    },
    "R6": {
        "name": "Dormant then active",
        "meaning": "An account with negligible recent history suddenly transacting at volume. The rule cannot fire until a full lookback exists behind the period.",
        "parameters": [
            {"name": "lookback length", "unit": "periods", "effect": "lengthening it lowers volume and delays the earliest period the rule can fire in"},
            {"name": "dormancy ceiling", "unit": "payments in the lookback", "effect": "raising it admits accounts that were not truly dormant and raises volume"},
            {"name": "activation count", "unit": "payments in the period", "effect": "raising it lowers volume"},
        ],
    },
    "R7": {
        "name": "High risk corridor",
        "meaning": "A cross jurisdiction payment settled through an elevated risk instrument. The corridor is defined structurally rather than by naming jurisdictions, because publishing a country risk list would be a claim about real places this project has no basis to make.",
        "parameters": [
            {"name": "instrument set", "unit": "payment formats", "effect": "widening it raises volume"},
            {"name": "minimum amount", "unit": "currency amount", "effect": "raising it lowers volume"},
            {"name": "minimum count", "unit": "payments per period", "effect": "raising it lowers volume"},
        ],
    },
    "R8": {
        "name": "Peer group velocity deviation",
        "meaning": "Activity far above the account's own history and above its peer group, where the peer group is the originating bank. Prior periods only.",
        "parameters": [
            {"name": "minimum prior periods", "unit": "periods", "effect": "raising it delays the earliest period the rule can fire in"},
            {"name": "own history multiple", "unit": "ratio", "effect": "raising it lowers volume"},
            {"name": "peer group multiple", "unit": "ratio", "effect": "raising it lowers volume"},
            {"name": "minimum count", "unit": "payments in the period", "effect": "raising it lowers volume"},
        ],
    },
}

# Which evidence keys are computed trigger quantities and may be published. Every
# other key in a rule's evidence is a parameter value and is dropped. A key that
# is not listed here is dropped, so adding a parameter to a rule cannot leak it
# by default.
PUBLISHABLE_EVIDENCE: dict[str, tuple[str, ...]] = {
    "R1": ("count", "total"),
    "R2": ("pairs", "largest_pass_through"),
    "R3": ("counterparties", "total"),
    "R4": ("counterparties", "total"),
    "R5": ("count", "total"),
    "R6": ("count", "prior_count"),
    "R7": ("count", "total", "jurisdictions"),
    "R8": ("count", "own_mean", "peer_mean", "prior_periods"),
}

EVIDENCE_COPY: dict[str, dict[str, str]] = {
    "count": {"label": "Payments in the period", "unit": "payments"},
    "total": {"label": "Total paid", "unit": "mixed currency amount"},
    "pairs": {"label": "Matched credit and debit pairs", "unit": "pairs"},
    "largest_pass_through": {"label": "Largest pass through", "unit": "mixed currency amount"},
    "counterparties": {"label": "Distinct counterparties", "unit": "accounts"},
    "jurisdictions": {"label": "Distinct destination jurisdictions", "unit": "jurisdictions"},
    "prior_count": {"label": "Payments in the lookback", "unit": "payments"},
    "own_mean": {"label": "The account's own prior mean", "unit": "payments per period"},
    "peer_mean": {"label": "Peer group mean", "unit": "payments per period"},
    "prior_periods": {"label": "Prior periods observed", "unit": "periods"},
}

CLAIMS = (
    "An alert means a rule fired. A high rank means the alert resembles alerts "
    "that resolved as suspicious in the simulation. Neither means a crime "
    "occurred."
)


def publishable_evidence(alert: dict) -> list[dict[str, Any]]:
    """Trigger evidence with the parameter values removed.

    The engine writes both the quantities that met a trigger and the parameters
    that set it into one JSON blob. Only the quantities are published, and the
    filter is an allowlist so a new parameter cannot leak by being forgotten.
    """
    published = []
    for item in alert_store.evidence_for(alert):
        rule_id = item["rule_id"]
        allowed = PUBLISHABLE_EVIDENCE.get(rule_id, ())
        published.append(
            {
                "rule_id": rule_id,
                "quantities": [
                    {
                        "key": key,
                        "label": EVIDENCE_COPY[key]["label"],
                        "unit": EVIDENCE_COPY[key]["unit"],
                        "value": float(item[key]),
                    }
                    for key in allowed
                    if key in item
                ],
            }
        )
    return sorted(published, key=lambda item: item["rule_id"])


def contributions(
    booster, built: pl.DataFrame, columns: list[str], top: int = MAX_EXPLANATION_FEATURES
) -> dict[str, list[dict[str, Any]]]:
    """Per alert feature contributions to the model's score.

    LightGBM computes these exactly rather than approximating them, so the
    explanation is the model's own arithmetic and not a story told about it. The
    trailing column is the base value and is dropped: it is identical for every
    alert and explains nothing about why one sits above another.
    """
    matrix = booster.predict(built.select(columns).to_numpy(), pred_contrib=True)
    identifiers = built["alert_id"].to_list()
    explained: dict[str, list[dict[str, Any]]] = {}
    values = built.select(columns).to_numpy()
    for row, (alert_id, row_values) in enumerate(zip(identifiers, values, strict=True)):
        pairs = [
            {
                "feature": columns[index],
                "value": float(row_values[index]),
                "contribution": float(matrix[row][index]),
            }
            for index in range(len(columns))
        ]
        pairs.sort(key=lambda item: (-abs(item["contribution"]), item["feature"]))
        explained[alert_id] = pairs[:top]
    return explained


def _bounded_transactions(
    alerts: pl.DataFrame, txns: pl.DataFrame
) -> dict[str, dict[str, Any]]:
    """The first few contributing transactions per alert, with the true count."""
    exploded = (
        alerts.select("alert_id", "contributing_txn_ids")
        .explode("contributing_txn_ids", empty_as_null=True)
        .drop_nulls()
        .rename({"contributing_txn_ids": "txn_id"})
        .join(
            txns.select("txn_id", "ts", "from_account", "to_account", "amount", "currency", "format"),
            on="txn_id",
            how="inner",
        )
        .sort("alert_id", "ts", "txn_id")
    )
    carried: dict[str, dict[str, Any]] = {}
    for alert_id, frame in exploded.group_by("alert_id", maintain_order=True):
        identifier = alert_id[0]
        rows = frame.head(MAX_CONTRIBUTING_TRANSACTIONS).to_dicts()
        carried[identifier] = {
            "contributing_transaction_count": frame.height,
            "contributing_transactions": [
                {
                    "id": f"txn-{index:02d}",
                    "timestamp": row["ts"].isoformat(sep=" ", timespec="minutes"),
                    "from": pseudonym(row["from_account"]),
                    "to": pseudonym(row["to_account"]),
                    "amount": round(float(row["amount"]), 2),
                    "currency": row["currency"],
                    "rail": row["format"],
                }
                for index, row in enumerate(rows, 1)
            ],
        }
    return carried


def _orderings(
    period_alerts: pl.DataFrame,
    prepared: pl.DataFrame,
    period,
    scores: pl.DataFrame,
    prior_weight: int = backtest.PRIOR_WEIGHT,
    seed: int = 0,
) -> dict[str, list[str]]:
    """Every rung's ordering of this one period, as alert identifiers in order.

    The orderings come from `backtest.order_period` and `backtest.order_by_score`,
    which are the same functions that produced every measured number, so the
    queue an analyst reorders is the queue that was scored.
    """
    hit_rates = backtest.rule_hit_rates(prepared, period, prior_weight)
    ordered = {
        rung: backtest.order_period(period_alerts, rung, hit_rates, seed)["alert_id"].to_list()
        for rung in backtest.LADDER
    }
    scored = backtest.order_by_score(period_alerts, scores)
    if scored.height != period_alerts.height:
        raise ValueError(f"{period_alerts.height - scored.height} alerts in the period have no score")
    ordered["C1"] = scored["alert_id"].to_list()
    return ordered


def _typology_table(
    universe: pl.DataFrame, period_universe: pl.DataFrame
) -> list[dict[str, Any]]:
    """Attempt counts per injected typology, with both denominators and no gaps.

    Two scopes, because the surface needs one and the written result reports the
    other, and reading a single period's recall against a seven period
    denominator would be wrong in the direction that flatters.

    `in_period` is what the capacity control divides by: attempts with a
    transaction dated in the published period, and the subset of those the rules
    raised an alert on. `across_evaluation` is the seven period figure the
    backtest reports. A typology with no attempt in the period is carried at zero
    rather than dropped, so no row disappears between the two scopes.
    """

    def counts(frame: pl.DataFrame) -> dict[str, dict[str, int]]:
        return {
            row["typology"]: row
            for row in frame.group_by("typology")
            .agg(
                pl.len().alias("attempts_live"),
                pl.col("surfaced").sum().alias("attempts_surfaced"),
            )
            .to_dicts()
        }

    overall = counts(universe)
    scoped = counts(period_universe)
    return [
        {
            "typology": typology,
            "in_period": {
                "attempts_live": int(scoped.get(typology, {}).get("attempts_live", 0)),
                "attempts_surfaced": int(scoped.get(typology, {}).get("attempts_surfaced", 0)),
            },
            "across_evaluation": {
                "attempts_live": int(overall.get(typology, {}).get("attempts_live", 0)),
                "attempts_surfaced": int(overall.get(typology, {}).get("attempts_surfaced", 0)),
            },
        }
        for typology in backtest.INJECTED_TYPOLOGIES
    ]


def period_attempt_universe(
    period_alerts: pl.DataFrame, labels: pl.DataFrame, period: date
) -> pl.DataFrame:
    """Attempts live in one period, and whether the rules surfaced them there.

    The same two denominators `backtest.attempt_universe` produces, narrowed to a
    single period, because a queue covering one period can only be measured
    against the attempts that period could have reached.
    """
    active = (
        labels.filter(
            pl.col("attempt_id").is_not_null() & (pl.col(rules.PERIOD) == pl.lit(period))
        )
        .select("attempt_id", "typology")
        .unique()
    )
    surfaced = (
        period_alerts.select("attempt_ids")
        .explode("attempt_ids", empty_as_null=True)
        .drop_nulls()
        .unique()
        .rename({"attempt_ids": "attempt_id"})
        .with_columns(pl.lit(True).alias("surfaced"))
    )
    return active.join(surfaced, on="attempt_id", how="left").with_columns(
        pl.col("surfaced").fill_null(False)
    )


def _rule_table(
    alerts: pl.DataFrame, universe: pl.DataFrame, period_alerts: pl.DataFrame
) -> list[dict[str, Any]]:
    """The catalogue with its measured volume, its support and its structural zeros.

    A rule the simulator never generates a counterpart for carries an attempt
    count of zero and `supported` false. Its alert volume is on the same row,
    because that volume is a real analyst cost and it is the finding, not an
    omission.
    """
    support = {row["rule_id"]: row for row in backtest.rule_support_table(universe).to_dicts()}
    store_volume = dict(
        alerts.select("fired_rules")
        .explode("fired_rules", empty_as_null=True)
        .drop_nulls()
        .group_by("fired_rules")
        .len()
        .iter_rows()
    )
    period_volume = dict(
        period_alerts.select("fired_rules")
        .explode("fired_rules", empty_as_null=True)
        .drop_nulls()
        .group_by("fired_rules")
        .len()
        .iter_rows()
    )
    return [
        {
            "rule_id": rule_id,
            "name": RULE_COPY[rule_id]["name"],
            "meaning": RULE_COPY[rule_id]["meaning"],
            "parameters": RULE_COPY[rule_id]["parameters"],
            "alerts_in_store": int(store_volume.get(rule_id, 0)),
            "alerts_in_period": int(period_volume.get(rule_id, 0)),
            "supported": bool(support[rule_id]["supported"]),
            "typologies": [] if not support[rule_id]["supported"] else support[rule_id]["typologies"].split(", "),
            "attempts": int(support[rule_id]["attempts"]),
        }
        for rule_id in sorted(RULE_COPY)
    ]


def _result_block(record: dict[str, Any]) -> dict[str, Any]:
    """The measured comparison, carried so the surface can state the outcome.

    This is where the baseline wins state gets its numbers. It is read from the
    challenger run record rather than recomputed, so the interface and the
    written result cannot drift apart.
    """
    pooled = {row["rung"]: row for row in record["pooled"]}
    reference = record["reference_rung"]
    lift = {row["against"]: row for row in record["lift"]}
    return {
        "gate": {
            "metric": "Precision at K against the strongest rung",
            "threshold": 1.3,
            "reference_rung": reference,
            "lift": lift[reference]["lift"],
            "interval": record["lift_intervals"][reference],
            "met": lift[reference]["lift"] >= 1.3,
            "promoted": False,
            "statement": (
                "The learned ranker beats every rung of the ladder and does not "
                "clear the gate that was written before it existed, so no model "
                "is promoted. The ordering is shown for comparison."
            ),
        },
        "measured": [
            {
                "ordering": rung,
                "periods": pooled[rung]["periods"],
                "worked": pooled[rung]["worked"],
                "true_positives": pooled[rung]["true_positives"],
                "precision": pooled[rung]["precision"],
                "interval": record["precision_intervals"][rung],
            }
            for rung in LADDER_AND_CHALLENGER
            if rung in pooled
        ],
        "evaluation_periods": len({row["period_start"] for row in record["per_period"]}),
        "k": record["k"],
    }


def _evidence_block(record: dict[str, Any]) -> dict[str, Any]:
    """The measured run broken back into the units the work happens in.

    The surface used to carry one review period and a pooled ladder, and pooled
    figures hide three things that change what an investigation lead would do:
    where in the pipeline the attempts are actually lost, that the flagged alerts
    are overwhelmingly ones no typology claims, and that the periods are not
    alike. Every row here is read from the run record rather than recomputed, for
    the same reason `_result_block` is: the surface and the written result cannot
    then disagree.

    Nothing tuned enters this block. Model feature names are not rule parameters,
    and the per rule prior hit rates that B3 is built from are deliberately left
    out, because those are closer to the trigger set than to a published result.
    """
    reference = record["reference_rung"]
    recall = {(row["rung"], row["typology"]): row for row in record["typology_recall"]}
    typologies = sorted({row["typology"] for row in record["typology_recall"]})
    per_period: dict[str, dict[str, Any]] = {}
    for row in record["per_period"]:
        per_period.setdefault(row["period_start"], {})[row["rung"]] = row
    unattributed = {row["rung"]: row for row in record["unattributed"]}
    volume = {row["period_start"]: row for row in record["volume_reduction"]}

    attempts = sum(recall[("C1", t)]["attempts"] for t in typologies)
    surfaced = sum(recall[("C1", t)]["attempts_surfaced"] for t in typologies)
    return {
        # The spine. Attempts the rules never surfaced are unreachable by any
        # ordering, so this is the number that bounds every ranking result.
        "funnel": {
            "attempts_live": attempts,
            "attempts_surfaced": surfaced,
            "attempts_reached": {
                rung: sum(recall[(rung, t)]["attempts_recovered"] for t in typologies)
                for rung in LADDER_AND_CHALLENGER
                if (rung, typologies[0]) in recall
            },
            "lost_before_ordering": attempts - surfaced,
            "statement": (
                "Attempts the rules never surfaced cannot be recovered by any "
                "ordering. The ranking layer competes for the surfaced count "
                "alone, and that bound is a property of the alert population."
            ),
        },
        # Two denominators, side by side, because they answer different
        # questions. Recall against all attempts scores the rules. Recall of
        # surfaced attempts scores the ordering.
        "typology_detail": [
            {
                "typology": typology,
                "attempts_live": recall[("C1", typology)]["attempts"],
                "attempts_surfaced": recall[("C1", typology)]["attempts_surfaced"],
                "reached": {
                    rung: recall[(rung, typology)]["attempts_recovered"]
                    for rung in LADDER_AND_CHALLENGER
                    if (rung, typology) in recall
                },
                "recall_of_live": recall[("C1", typology)]["recall"],
                "recall_of_surfaced": recall[("C1", typology)]["recall_of_surfaced"],
                "interval": record["recall_intervals"].get(f"C1|{typology}", [0.0, 0.0]),
            }
            for typology in typologies
        ],
        # The dominant line. Reporting it inside the typology table would fold it
        # into a denominator it does not belong to, so it gets its own block.
        "unattributed": {
            "alerts_in_population": unattributed[reference]["alerts_in_population"],
            "reached": {
                rung: unattributed[rung]["alerts_recovered"]
                for rung in LADDER_AND_CHALLENGER
                if rung in unattributed
            },
            "statement": (
                "Flagged alerts that no injected attempt claims. They are true "
                "positives by the simulator's own label and they carry no "
                "typology, so per typology recall cannot see them at all."
            ),
        },
        "per_period": [
            {
                "period_start": period,
                "alerts": per_period[period][reference]["period_alerts"],
                "worked": per_period[period][reference]["worked"],
                "coverage": per_period[period][reference]["worked"]
                / per_period[period][reference]["period_alerts"],
                "true_positives": {
                    rung: per_period[period][rung]["true_positives"]
                    for rung in LADDER_AND_CHALLENGER
                    if rung in per_period[period]
                },
                "precision": {
                    rung: per_period[period][rung]["precision"]
                    for rung in LADDER_AND_CHALLENGER
                    if rung in per_period[period]
                },
            }
            for period in sorted(per_period)
        ],
        # The volume claim, unpooled and signed. A negative figure means the
        # challenger cost more volume than the reference at equal coverage, and
        # two periods do exactly that.
        "volume_reduction": {
            "pooled": record["volume_reduction_pooled"],
            "reference_rung": reference,
            "per_period": [
                {
                    "period_start": period,
                    "alerts_target": volume[period]["alerts_target"],
                    "alerts_depth": volume[period]["alerts_depth"],
                    "alerts_freed": volume[period]["alerts_freed"],
                    "attempts_target": volume[period]["attempts_target"],
                    "attempts_depth": volume[period]["attempts_depth"],
                    "attempts_freed": volume[period]["attempts_freed"],
                    "target_was_zero": volume[period]["target_was_zero"],
                }
                for period in sorted(volume)
            ],
        },
        "rank_stability": {
            "threshold": 0.70,
            "pairs": [
                {
                    "period_start": row["period_start"],
                    "alerts": row["alerts"],
                    "spearman": row["spearman"],
                }
                for row in record["rank_stability"]
            ],
        },
        "feature_importance": {
            "features_in_model": len(record["importance"]),
            "carried": min(MAX_IMPORTANCE_FEATURES, len(record["importance"])),
            "bound_note": (
                f"The {len(record['importance'])} model features ranked by gain, "
                f"truncated to {MAX_IMPORTANCE_FEATURES}. These are model feature "
                "names and not rule parameters; no tuned trigger value is carried."
            ),
            "top": [
                {"feature": row["feature"], "gain": row["gain"]}
                for row in record["importance"][:MAX_IMPORTANCE_FEATURES]
            ],
        },
    }


def build_artifact(
    *,
    alerts: pl.DataFrame,
    txns: pl.DataFrame,
    prepared: pl.DataFrame,
    built: pl.DataFrame,
    universe: pl.DataFrame,
    period_universe: pl.DataFrame,
    period: date,
    scores: pl.DataFrame,
    booster,
    backtest_record: dict[str, Any],
    source_manifest: dict[str, Any],
    distribution: dict[str, Any],
    operating_point: dict[str, Any],
) -> dict[str, Any]:
    """One period of the queue, everything it needs, and nothing raw.

    The caller supplies the frames rather than paths so that the test suite can
    build a complete artifact from a fixture without touching the source file.
    """
    stamp = pl.Series([period]).cast(pl.Datetime("us"))[0]
    period_alerts = prepared.filter(pl.col("period_start") == stamp)
    if not period_alerts.height:
        raise ValueError(f"no alerts in period {period.isoformat()}")
    period_store = alerts.filter(pl.col("period_start") == stamp)
    period_built = built.filter(pl.col("period_start") == stamp).sort("alert_id")

    ordered = _orderings(period_alerts, prepared, stamp, scores)
    ranks = {
        rung: {alert_id: position for position, alert_id in enumerate(identifiers, 1)}
        for rung, identifiers in ordered.items()
    }
    columns = features.feature_columns(period_built)
    explained = contributions(booster, period_built, columns)
    transactions = _bounded_transactions(period_store, txns)
    evidence = {row["alert_id"]: publishable_evidence(row) for row in period_store.to_dicts()}
    scored = dict(scores.select("alert_id", "score").iter_rows())

    rows = []
    for row in period_alerts.sort("alert_id").to_dicts():
        alert_id = row["alert_id"]
        carried = transactions.get(
            alert_id, {"contributing_transaction_count": 0, "contributing_transactions": []}
        )
        rows.append(
            {
                "alert_id": alert_id,
                "subject": pseudonym(row["subject_account"]),
                "fired_rules": list(row["fired_rules"]),
                "first_transaction_at": row["first_txn_ts"].isoformat(sep=" ", timespec="minutes")
                if row["first_txn_ts"] is not None
                else None,
                "alert_amount": round(float(row["alert_amount"] or 0.0), 2),
                "ranks": {rung: ranks[rung][alert_id] for rung in LADDER_AND_CHALLENGER},
                "score": round(float(scored[alert_id]), 6),
                "is_true_positive": bool(row["is_true_positive"]),
                "attempt_ids": [int(value) for value in row["attempt_ids"]],
                "typologies": list(row["typologies"]),
                "unattributed_only": bool(row["unattributed_only"]),
                "trigger_evidence": evidence[alert_id],
                "ranking_contributions": explained[alert_id],
                **carried,
            }
        )

    selection = {
        "period": period.isoformat(),
        "period_rule": "one evaluation period from the expanding walk forward, carried whole so the capacity control has a real denominator",
        "alert_bound": "every alert in the period, none removed",
        "transaction_bound": f"the first {MAX_CONTRIBUTING_TRANSACTIONS} contributing transactions of each alert ordered by timestamp, with the true count carried beside them",
        "parameter_disclosure": "computed trigger quantities only; tuned rule parameter values are described by name, unit and direction of effect and are not published",
        "pseudonymization": "SHA-256(account identifier), first 10 uppercase hexadecimal characters, prefixed Party-",
    }
    run_material = {
        "artifact_schema": ARTIFACT_SCHEMA,
        "source_sha256": source_manifest["source_sha256"],
        "engine_version": period_store["engine_version"][0],
        "param_set_hash": period_store["param_set_hash"][0],
        "feature_version": features.FEATURE_VERSION,
        "model_version": ranker.MODEL_VERSION,
        "selection": selection,
    }
    payload: dict[str, Any] = {
        "artifact_schema": ARTIFACT_SCHEMA,
        "provenance": {
            "provider": source_manifest["provider"],
            "dataset": source_manifest["dataset"],
            "dataset_version": source_manifest["dataset_version"],
            "source_ref": source_manifest["source_ref"],
            "retrieved_at": source_manifest["retrieved_at"],
            "source_file": source_manifest["source_file"],
            "source_sha256": source_manifest["source_sha256"],
            "license": source_manifest["license"],
            "license_url": source_manifest["license_url"],
            "engine_version": period_store["engine_version"][0],
            "param_set_hash": period_store["param_set_hash"][0],
            "feature_version": features.FEATURE_VERSION,
            "model_version": ranker.MODEL_VERSION,
            "distribution": {
                "classification": "Enhanced Data",
                "status": "approved"
                if distribution.get("public_distribution_status") == "approved"
                else "not approved",
                "notice": "Modified, selected, and pseudonymized from IBM AML-Data; published under CDLA-Sharing-1.0 with retained attribution.",
            },
            "selection": selection,
            "pipeline_run_id": hashlib.sha256(canonical_bytes(run_material)).hexdigest(),
        },
        "claims": CLAIMS,
        "period": {
            "start": period.isoformat(),
            "alerts": period_alerts.height,
            "true_positives": int(period_alerts["is_true_positive"].sum()),
            "base_rate": period_alerts["is_true_positive"].sum() / period_alerts.height,
            "label": "realistic synthetic banking data",
        },
        "operating_point": operating_point,
        "orderings": [
            {"id": rung, **ORDERING_COPY[rung]} for rung in LADDER_AND_CHALLENGER
        ],
        "result": _result_block(backtest_record),
        "evidence": _evidence_block(backtest_record),
        "rules": _rule_table(alerts, universe, period_alerts),
        "typologies": _typology_table(universe, period_universe),
        # The attempt to typology map for this period. Without it the surface can
        # count how many attempts a depth recovers but not which typology each
        # one belongs to, because an alert carrying two attempts of different
        # typologies collapses them into one unordered set on the row.
        "period_attempts": [
            {
                "attempt_id": int(row["attempt_id"]),
                "typology": row["typology"],
                "surfaced": bool(row["surfaced"]),
            }
            for row in period_universe.sort("attempt_id").to_dicts()
        ],
        "alerts": rows,
    }
    payload["artifact_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def write_artifact(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(payload) + b"\n")
    return output


def approved_artifact(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Publication level admission check, for use outside the serving path.

    The check itself lives in `src/triage_artifact.py`, which imports nothing
    from this package, because the deployed function must not gain Polars or
    LightGBM by importing an admission check. This is the builder's alias for it.
    """
    return admitted_triage_artifact(
        Path(path), require_approval=True, expected_sha256=expected_sha256
    )


def build_from_paths(
    *,
    transactions: Path,
    patterns: Path,
    store: Path,
    feature_table: Path,
    backtest_record: Path,
    source_manifest: dict[str, Any],
    distribution: dict[str, Any],
    period: date,
    operating_point: dict[str, Any],
    window: rules.Window | None = None,
    rounds: int = ranker.ROUNDS,
) -> dict[str, Any]:
    """Everything the artifact needs, assembled from the local pipeline outputs.

    The model is trained here on periods strictly before the published one, by
    the same `training_frame` every measured number went through, so the queue on
    the surface is the queue that was scored and not a re-fit of it.
    """
    window = window or rules.Window()
    txns = rules.load_transactions(transactions, window)
    alerts = alert_store.read_store(store)
    labels = backtest.load_labels(transactions, patterns)
    prepared = backtest.prepare(alerts, txns, labels)
    built = pl.read_parquet(feature_table)
    universe = backtest.attempt_universe(prepared, labels)
    columns = features.feature_columns(built)
    booster = ranker.train(ranker.training_frame(built, prepared, period), columns, rounds)
    stamp = pl.Series([period]).cast(pl.Datetime("us"))[0]
    scores = ranker.score(booster, built.filter(pl.col("period_start") == stamp), columns)
    period_universe = period_attempt_universe(
        prepared.filter(pl.col("period_start") == stamp), labels, period
    )
    return build_artifact(
        alerts=alerts,
        txns=txns,
        prepared=prepared,
        built=built,
        universe=universe,
        period_universe=period_universe,
        period=period,
        scores=scores,
        booster=booster,
        backtest_record=json.loads(Path(backtest_record).read_text(encoding="utf-8")),
        source_manifest=source_manifest,
        distribution=distribution,
        operating_point=operating_point,
    )
