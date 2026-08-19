"""Backtest harness and the baseline ladder B0 to B3.

**The label join lives here and nowhere else.** The rules engine, the alert store
and the feature build all refuse the laundering flag by construction. This module
is the one place it is read, and it reads it only to score an ordering that has
already been produced.

Three properties of the join are deliberate.

1. An alert is a true positive if any of its contributing transactions carries
   the laundering flag. Typology attribution is a second, narrower question,
   answered from the patterns file rather than inferred from the flag. 38 percent
   of flagged transactions carry no attribution, and those are reported as their
   own line rather than folded into a typology or dropped.
2. The join reads the full transaction file, including days after the study
   window. An outcome observed after the alert is how a suspicious activity
   report works. Features stay bound by `feature_cutoff_ts` and the leakage gate
   in `features.py` enforces that separately.
3. B3 weights each fired rule by its hit rate in **prior periods only**. A hit
   rate that reads the period it is scoring makes the baseline leak and the
   comparison worthless. Decision record 0004 is why the value is computed here
   rather than stored on the alert.
"""

from __future__ import annotations

import random
from datetime import date
from pathlib import Path

import polars as pl

from src.pipeline import rules

# The operating point, from scope.md. Six analysts at seven productive hours and
# twenty minutes per alert is 126 alerts worked per period.
K_ALERTS = 126

# Days one to three are the minimum training window and are never evaluated.
EVALUATION_START = date(2022, 9, 4)

BOOTSTRAP_SAMPLES = 1000
CONFIDENCE = 0.95

# Shrinkage weight for B3's hit rates, in alerts. See rule_hit_rates.
PRIOR_WEIGHT = K_ALERTS

LADDER = ["B0", "B1", "B2", "B3"]

# The eight patterns the simulator injects. Not the same eight as the rule
# catalogue, which is a first class finding rather than a mismatch to engineer
# around. See data.md.
INJECTED_TYPOLOGIES = [
    "BIPARTITE",
    "CYCLE",
    "FAN-IN",
    "FAN-OUT",
    "GATHER-SCATTER",
    "RANDOM",
    "SCATTER-GATHER",
    "STACK",
]

UNATTRIBUTED = "UNATTRIBUTED"

# Which catalogue rules the simulator gives a counterpart to. R3 and R4 map onto
# the compositions as well as the direct patterns, and BIPARTITE is many to many
# so it belongs to both. The counts in this table therefore overlap and are never
# summed. RANDOM is attributed to no rule. The five rules with an empty tuple are
# structural zeros: their recall is not a model result and is never reported as
# one.
RULE_SUPPORT: dict[str, tuple[str, ...]] = {
    "R1": (),
    "R2": ("STACK", "CYCLE"),
    "R3": ("FAN-IN", "GATHER-SCATTER", "BIPARTITE"),
    "R4": ("FAN-OUT", "SCATTER-GATHER", "BIPARTITE"),
    "R5": (),
    "R6": (),
    "R7": (),
    "R8": (),
}

# The published header positionally repeats `Account`; Polars renames the second.
# These ten fields are every column of a transaction except the flag, which is
# what a patterns file line reproduces.
_KEY_COLUMNS = [
    "Timestamp",
    "From Bank",
    "Account",
    "To Bank",
    "Account_duplicated_0",
    "Amount Received",
    "Receiving Currency",
    "Amount Paid",
    "Payment Currency",
    "Payment Format",
]


def parse_patterns(path: str | Path) -> pl.DataFrame:
    """Read the injected laundering attempts and their typologies.

    The file is blocks of transaction lines between BEGIN and END markers, and
    the marker names the typology. A line reproduces its transaction verbatim
    except for the trailing flag, so the line itself is the join key.
    """
    attempts: list[dict] = []
    attempt_id = -1
    typology: str | None = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("BEGIN LAUNDERING ATTEMPT"):
            attempt_id += 1
            typology = line.split(" - ", 1)[1].split(":")[0].strip()
        elif line.startswith("END LAUNDERING ATTEMPT"):
            typology = None
        elif line and typology is not None:
            attempts.append(
                {"attempt_id": attempt_id, "typology": typology, "key": line.rsplit(",", 1)[0]}
            )
    return pl.DataFrame(
        attempts, schema={"attempt_id": pl.Int64, "typology": pl.String, "key": pl.String}
    )


def load_labels(transactions: str | Path, patterns: str | Path) -> pl.DataFrame:
    """One row per flagged transaction, with its attempt and typology where known.

    The full file is read with no window filter and no self transfer filter, so
    the join can see an outcome that lands after the study window. That is the
    point: features are cut at `feature_cutoff_ts`, outcomes are not.

    A transaction that carries the flag but appears in no attempt keeps a null
    typology. There are 1,968 of those on HI-Small and they are positives, so
    they count toward precision and are reported as their own line in the
    typology table.
    """
    flagged = (
        pl.scan_csv(transactions, infer_schema=False)
        .with_row_index("txn_id")
        .filter(pl.col("Is Laundering") == "1")
        .select(
            "txn_id",
            pl.col("Timestamp").str.to_datetime("%Y/%m/%d %H:%M").dt.date().alias(rules.PERIOD),
            pl.concat_str([pl.col(name) for name in _KEY_COLUMNS], separator=",").alias("key"),
        )
        .collect()
    )
    injected = parse_patterns(patterns)
    attributed = flagged.join(injected, on="key", how="left")
    matched = attributed.filter(pl.col("attempt_id").is_not_null()).height
    if matched != injected.height:
        raise ValueError(
            f"{injected.height - matched} pattern lines did not match a flagged transaction"
        )
    return attributed.select("txn_id", rules.PERIOD, "attempt_id", "typology").sort("txn_id")


def alert_facts(alerts: pl.DataFrame, txns: pl.DataFrame) -> pl.DataFrame:
    """The label free ordering inputs: when an alert starts and what it is worth.

    `alert_amount` sums the paid amounts of the contributing transactions. The
    file carries fourteen currencies and no exchange rates, so this mixes
    currencies. That is a real distortion and it is also exactly what an
    institution sorting a mixed currency queue without a rate table would get,
    which is what B2 is meant to represent.
    """
    exploded = alerts.select("alert_id", "contributing_txn_ids").explode(
        "contributing_txn_ids", empty_as_null=True
    )
    return (
        exploded.rename({"contributing_txn_ids": "txn_id"})
        .join(txns.select("txn_id", "ts", "amount"), on="txn_id", how="left")
        .group_by("alert_id")
        .agg(
            pl.col("ts").min().alias("first_txn_ts"),
            pl.col("amount").sum().alias("alert_amount"),
        )
    )


def label_alerts(alerts: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    """Attach the outcome to every alert. One row per alert, nothing dropped."""
    exploded = (
        alerts.select("alert_id", "contributing_txn_ids")
        .explode("contributing_txn_ids", empty_as_null=True)
        .rename({"contributing_txn_ids": "txn_id"})
        .join(labels, on="txn_id", how="inner")
    )
    outcome = exploded.group_by("alert_id").agg(
        pl.len().alias("laundering_transactions"),
        pl.col("attempt_id").drop_nulls().unique().sort().alias("attempt_ids"),
        pl.col("typology").drop_nulls().unique().sort().alias("typologies"),
    )
    return (
        alerts.join(outcome, on="alert_id", how="left")
        .with_columns(
            pl.col("laundering_transactions").fill_null(0),
            pl.col("attempt_ids").fill_null([]),
            pl.col("typologies").fill_null([]),
        )
        .with_columns(
            (pl.col("laundering_transactions") > 0).alias("is_true_positive"),
            (
                (pl.col("laundering_transactions") > 0) & (pl.col("attempt_ids").list.len() == 0)
            ).alias("unattributed_only"),
        )
    )


def prepare(alerts: pl.DataFrame, txns: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    """The scored alert population: ordering inputs plus the joined outcome."""
    return (
        label_alerts(alerts, labels)
        .join(alert_facts(alerts, txns), on="alert_id", how="left")
        .select(
            "alert_id",
            "subject_account",
            "period_start",
            "fired_rules",
            "first_txn_ts",
            "alert_amount",
            "laundering_transactions",
            "attempt_ids",
            "typologies",
            "is_true_positive",
            "unattributed_only",
        )
        .sort("period_start", "alert_id")
    )


def evaluation_periods(prepared: pl.DataFrame, start: date = EVALUATION_START) -> list:
    """The periods that are scored. Everything before `start` is training only."""
    return (
        prepared.filter(pl.col("period_start").dt.date() >= start)
        .select("period_start")
        .unique()
        .sort("period_start")["period_start"]
        .to_list()
    )


def rule_hit_rates(
    prepared: pl.DataFrame, period, prior_weight: int = PRIOR_WEIGHT
) -> pl.DataFrame:
    """Each rule's hit rate over periods strictly before `period`, smoothed.

    The observed rate is the share of a rule's prior alerts that resolved as
    suspicious. Used raw it is unusable at the start of the window: R6 cannot
    fire until a full lookback exists behind the period, so by 2022/09/09 it had
    three prior alerts, all three of which were hits, and an unsmoothed estimator
    reads that as a hit rate of 1.0 and hands the rule the entire priority band.

    The estimator therefore shrinks each rule toward the pooled prior hit rate
    with a weight of `prior_weight` alerts, which is additive smoothing under a
    beta prior. The weight is set to K, one period of analyst capacity, because
    that is the smallest sample an institution could actually have worked before
    re-banding a rule. It is an operating point anchor, not a number chosen
    against the outcome, and the unsmoothed ladder is published beside the
    smoothed one so the choice is visible.

    A rule with no prior alerts inherits the pooled rate, which is what the
    shrinkage gives it at zero observations.
    """
    prior = prepared.filter(pl.col("period_start") < period)
    catalogue = pl.DataFrame({"rule_id": sorted(RULE_SUPPORT)})
    observed = (
        catalogue.join(
            prior.select("fired_rules", "is_true_positive")
            .explode("fired_rules", empty_as_null=True)
            .rename({"fired_rules": "rule_id"})
            .group_by("rule_id")
            .agg(
                pl.len().alias("prior_alerts"),
                pl.col("is_true_positive").sum().alias("prior_hits"),
            ),
            on="rule_id",
            how="left",
        )
        .with_columns(pl.col("prior_alerts").fill_null(0), pl.col("prior_hits").fill_null(0))
        .sort("rule_id")
    )
    total = observed["prior_alerts"].sum()
    pooled = observed["prior_hits"].sum() / total if total else 0.0
    return observed.with_columns(
        pl.when(pl.col("prior_alerts") > 0)
        .then(pl.col("prior_hits") / pl.col("prior_alerts"))
        .alias("observed_rate"),
        (
            (pl.col("prior_hits") + prior_weight * pooled)
            / (pl.col("prior_alerts") + prior_weight)
        )
        # A rule with no prior alerts and no smoothing has no rate at all, which
        # is a priority of zero rather than an undefined one.
        .fill_nan(0.0)
        .alias("hit_rate"),
    )


def b3_priority(period_alerts: pl.DataFrame, hit_rates: pl.DataFrame) -> pl.DataFrame:
    """B3's ordering value: the highest prior hit rate among the rules that fired.

    An institution works its queue by priority band and chronologically inside a
    band, per spec.md section 8, so the band is the strongest rule on the alert
    and the tie break is the oldest alert first.
    """
    weights = dict(zip(hit_rates["rule_id"].to_list(), hit_rates["hit_rate"].to_list()))
    if not weights:
        return period_alerts.with_columns(pl.lit(0.0).alias("priority"))
    return period_alerts.with_columns(
        pl.col("fired_rules")
        .list.eval(pl.element().replace_strict(weights, default=0.0))
        .list.max()
        .alias("priority")
    )


def order_period(period_alerts: pl.DataFrame, rung: str, hit_rates: pl.DataFrame, seed: int) -> pl.DataFrame:
    """One period's alerts in the order the given rung would work them."""
    if rung == "B0":
        return period_alerts.sample(fraction=1.0, shuffle=True, seed=seed)
    if rung == "B1":
        return period_alerts.sort("first_txn_ts", "alert_id")
    if rung == "B2":
        return period_alerts.sort("alert_amount", "alert_id", descending=[True, False])
    if rung == "B3":
        return b3_priority(period_alerts, hit_rates).sort(
            "priority", "first_txn_ts", "alert_id", descending=[True, False, False]
        )
    raise ValueError(f"unknown ladder rung {rung}")


def worked_queue(
    prepared: pl.DataFrame,
    rung: str,
    k: int = K_ALERTS,
    start: date = EVALUATION_START,
    seed: int = 0,
    prior_weight: int = PRIOR_WEIGHT,
) -> pl.DataFrame:
    """The alerts this rung reaches, across every evaluation period.

    A period with fewer than k alerts is worked out, and the worked count is
    carried so precision is never computed against a denominator the period
    could not supply.
    """
    frames = []
    for index, period in enumerate(evaluation_periods(prepared, start)):
        period_alerts = prepared.filter(pl.col("period_start") == period)
        hit_rates = (
            rule_hit_rates(prepared, period, prior_weight) if rung == "B3" else pl.DataFrame()
        )
        ordered = order_period(period_alerts, rung, hit_rates, seed + index)
        frames.append(_take(ordered, rung, k, period_alerts.height))
    return pl.concat(frames)


def _take(ordered: pl.DataFrame, rung: str, k: int, period_alerts: int) -> pl.DataFrame:
    """The head of one period's ordering, in the shape every metric reads."""
    return (
        ordered.head(k)
        .with_columns(
            pl.lit(rung).alias("rung"),
            pl.int_range(1, pl.len() + 1).alias("queue_position"),
            pl.lit(period_alerts).alias("period_alerts"),
        )
        .select(
            "rung",
            "period_start",
            "queue_position",
            "period_alerts",
            "alert_id",
            "attempt_ids",
            "typologies",
            "is_true_positive",
            "unattributed_only",
        )
    )


def order_by_score(period_alerts: pl.DataFrame, scores: pl.DataFrame) -> pl.DataFrame:
    """A scored ordering, highest score first, oldest alert first on a tie."""
    return (
        period_alerts.join(scores.select("alert_id", "score"), on="alert_id", how="inner")
        .sort("score", "first_txn_ts", "alert_id", descending=[True, False, False])
    )


def worked_queue_from_scores(
    prepared: pl.DataFrame,
    scores: pl.DataFrame,
    rung: str = "C1",
    k: int = K_ALERTS,
    start: date = EVALUATION_START,
) -> pl.DataFrame:
    """The alerts a scored ordering reaches, in the same shape as a ladder rung.

    Every metric in this module reads that shape, so the challenger is measured
    by exactly the code that measured the ladder.
    """
    frames = []
    for period in evaluation_periods(prepared, start):
        period_alerts = prepared.filter(pl.col("period_start") == period)
        ordered = order_by_score(period_alerts, scores)
        if ordered.height != period_alerts.height:
            raise ValueError(f"{period_alerts.height - ordered.height} alerts have no score")
        frames.append(_take(ordered, rung, k, period_alerts.height))
    return pl.concat(frames)


def precision_tables(worked: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Precision at K, counts first and rate second, pooled and per period.

    Pooling hides whether a result holds on more than one day, so both are
    returned and both are reported.
    """
    per_period = (
        worked.group_by("rung", "period_start")
        .agg(
            pl.len().alias("worked"),
            pl.col("is_true_positive").sum().alias("true_positives"),
            pl.col("period_alerts").first().alias("period_alerts"),
        )
        .with_columns((pl.col("true_positives") / pl.col("worked")).alias("precision"))
        .sort("rung", "period_start")
    )
    pooled = (
        per_period.group_by("rung")
        .agg(
            pl.len().alias("periods"),
            pl.col("worked").sum().alias("worked"),
            pl.col("true_positives").sum().alias("true_positives"),
            pl.col("period_alerts").sum().alias("alerts_in_population"),
        )
        .with_columns((pl.col("true_positives") / pl.col("worked")).alias("precision"))
        .sort("rung")
    )
    return pooled, per_period


def population_base_rate(prepared: pl.DataFrame, start: date = EVALUATION_START) -> float:
    """The share of the evaluation population that is a true positive.

    B0's expected precision is exactly this number, which is what makes it the
    floor rather than an arbitrary shuffle.
    """
    population = prepared.filter(pl.col("period_start").dt.date() >= start)
    return population["is_true_positive"].sum() / population.height


def attempt_universe(
    prepared: pl.DataFrame, labels: pl.DataFrame, start: date = EVALUATION_START
) -> pl.DataFrame:
    """Every attempt that is live in an evaluation period, and whether rules saw it.

    Two denominators, both reported, because they answer different questions.
    `active` is every attempt with a transaction dated in an evaluation period,
    which is what the team could in principle have found. `surfaced` is the
    subset the rules engine raised an alert on, which bounds what any ordering
    can recover.
    """
    periods = [period.date() for period in evaluation_periods(prepared, start)]
    active = (
        labels.filter(pl.col("attempt_id").is_not_null() & pl.col(rules.PERIOD).is_in(periods))
        .select("attempt_id", "typology")
        .unique()
    )
    surfaced = (
        prepared.filter(pl.col("period_start").dt.date() >= start)
        .select("attempt_ids")
        .explode("attempt_ids", empty_as_null=True)
        .drop_nulls()
        .unique()
        .rename({"attempt_ids": "attempt_id"})
        .with_columns(pl.lit(True).alias("surfaced"))
    )
    return active.join(surfaced, on="attempt_id", how="left").with_columns(
        pl.col("surfaced").fill_null(False)
    )


def typology_recall(
    worked: pl.DataFrame, universe: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Per typology recall at K, with the attempt count behind every figure.

    An attempt counts as recovered when any alert inside the worked queue carries
    one of its transactions, in any evaluation period. Recall is reported against
    both denominators: every live attempt, and the subset the rules surfaced.

    Returns the table and the per attempt outcomes the bootstrap resamples.
    """
    recovered = (
        worked.select("rung", "attempt_ids")
        .explode("attempt_ids", empty_as_null=True)
        .drop_nulls()
        .unique()
        .rename({"attempt_ids": "attempt_id"})
        .with_columns(pl.lit(True).alias("recovered"))
    )
    rungs = pl.DataFrame({"rung": sorted(worked["rung"].unique().to_list())})
    per_attempt = (
        universe.join(rungs, how="cross")
        .join(recovered, on=["rung", "attempt_id"], how="left")
        .with_columns(pl.col("recovered").fill_null(False))
    )
    return (
        per_attempt.group_by("rung", "typology")
        .agg(
            pl.len().alias("attempts"),
            pl.col("surfaced").sum().alias("attempts_surfaced"),
            pl.col("recovered").sum().alias("attempts_recovered"),
        )
        .with_columns(
            (pl.col("attempts_recovered") / pl.col("attempts")).alias("recall"),
            (pl.col("attempts_recovered") / pl.col("attempts_surfaced").clip(lower_bound=1)).alias(
                "recall_of_surfaced"
            ),
        )
        .sort("rung", "typology")
    ), per_attempt


def unattributed_line(worked: pl.DataFrame, prepared: pl.DataFrame, start: date = EVALUATION_START) -> pl.DataFrame:
    """The positives that carry no typology, reported rather than folded or dropped.

    They have no attempt to count, so the unit is alerts. An alert is on this
    line when it is a true positive and none of its laundering transactions
    appears in the patterns file.
    """
    population = prepared.filter(pl.col("period_start").dt.date() >= start)
    available = population["unattributed_only"].sum()
    return (
        worked.group_by("rung")
        .agg(pl.col("unattributed_only").sum().alias("alerts_recovered"))
        .with_columns(
            pl.lit(UNATTRIBUTED).alias("typology"),
            pl.lit(available).alias("alerts_in_population"),
        )
        .select("rung", "typology", "alerts_in_population", "alerts_recovered")
        .sort("rung")
    )


def rule_support_table(universe: pl.DataFrame) -> pl.DataFrame:
    """Which catalogue rules the simulator supports, and the attempts behind each.

    A structural zero is a rule the simulator never generates a counterpart for.
    It is reported with an attempt count of zero and never as a recall of zero,
    because those are different statements and only one of them is about the
    product.
    """
    counts = dict(universe.group_by("typology").len().iter_rows())
    return pl.DataFrame(
        [
            {
                "rule_id": rule,
                "supported": bool(typologies),
                "typologies": ", ".join(typologies) if typologies else "none",
                "attempts": sum(counts.get(name, 0) for name in typologies),
            }
            for rule, typologies in RULE_SUPPORT.items()
        ],
        schema={
            "rule_id": pl.String,
            "supported": pl.Boolean,
            "typologies": pl.String,
            "attempts": pl.Int64,
        },
    )


def bootstrap_mean(
    outcomes: list[int], samples: int = BOOTSTRAP_SAMPLES, seed: int = 0
) -> tuple[float, float]:
    """Percentile interval on the mean of a zero one vector.

    Resampling the worked alerts, or the attempts, is what evaluation.toml
    specifies. An empty vector has no interval.
    """
    if not outcomes:
        return (float("nan"), float("nan"))
    generator = random.Random(seed)
    size = len(outcomes)
    means = sorted(sum(generator.choices(outcomes, k=size)) / size for _ in range(samples))
    return _percentiles(means)


def bootstrap_lift(
    per_period: pl.DataFrame, numerator: str, denominator: str, samples: int = BOOTSTRAP_SAMPLES, seed: int = 0
) -> tuple[float, float]:
    """Paired interval on one rung's precision against another.

    The rungs work different alerts, so there is nothing to pair at the alert
    level. Periods are the pairing unit and there are seven of them, which makes
    this interval coarse. It is reported with that stated rather than omitted.
    """
    counts = {
        rung: {
            row["period_start"]: (row["true_positives"], row["worked"])
            for row in per_period.filter(pl.col("rung") == rung).to_dicts()
        }
        for rung in (numerator, denominator)
    }
    periods = sorted(counts[numerator])
    generator = random.Random(seed)
    ratios = []
    for _ in range(samples):
        drawn = generator.choices(periods, k=len(periods))
        top = sum(counts[numerator][period][0] for period in drawn)
        top_worked = sum(counts[numerator][period][1] for period in drawn)
        bottom = sum(counts[denominator][period][0] for period in drawn)
        bottom_worked = sum(counts[denominator][period][1] for period in drawn)
        if not bottom:
            continue
        ratios.append((top / top_worked) / (bottom / bottom_worked))
    if not ratios:
        return (float("nan"), float("nan"))
    return _percentiles(sorted(ratios))


def _percentiles(ordered: list[float], confidence: float = CONFIDENCE) -> tuple[float, float]:
    tail = (1 - confidence) / 2
    low = ordered[int(tail * (len(ordered) - 1))]
    high = ordered[int((1 - tail) * (len(ordered) - 1))]
    return (low, high)


def _depth_for(ordered: pl.DataFrame, attempts_target: int, alerts_target: int) -> dict:
    """How deep an ordering has to be worked to match a coverage target.

    Two criteria, because the metric as written and the metric as it can be
    measured here are not the same thing. Attempts is the definition in
    `evaluation.toml`. True positive alerts is the same question denominated in
    the unit that has enough evidence to answer it, since the rules surface 25
    attempts across seven periods and most periods recover none at all.

    A target of zero is matched at depth zero, which is arithmetically true and
    analytically empty, and the caller reports how often that happened rather
    than averaging it away.
    """
    depths = {"attempts": None, "alerts": None}
    seen: set[int] = set()
    positives = 0
    if not attempts_target:
        depths["attempts"] = 0
    if not alerts_target:
        depths["alerts"] = 0
    for position, row in enumerate(
        ordered.select("attempt_ids", "is_true_positive").iter_rows(), start=1
    ):
        seen.update(row[0])
        positives += bool(row[1])
        if depths["attempts"] is None and len(seen) >= attempts_target:
            depths["attempts"] = position
        if depths["alerts"] is None and positives >= alerts_target:
            depths["alerts"] = position
        if depths["attempts"] is not None and depths["alerts"] is not None:
            break
    return {
        "attempts_depth": depths["attempts"],
        "alerts_depth": depths["alerts"],
        "attempts_target": attempts_target,
        "alerts_target": alerts_target,
    }


def volume_reduction(
    prepared: pl.DataFrame,
    scores: pl.DataFrame,
    reference: pl.DataFrame,
    k: int = K_ALERTS,
    start: date = EVALUATION_START,
) -> pl.DataFrame:
    """False positive reduction at held coverage, per period.

    The reference rung works k alerts and recovers some attempts and some true
    positive alerts. This finds the depth the scored ordering needs to match that
    same coverage, and the freed volume is the difference. It is expressed
    against the worked volume, because that is the analyst hours the business
    case is denominated in, and the period's total alert count is carried
    alongside so the other denominator is available.

    A depth of None means the target was never matched at any depth.
    """
    rows = []
    for period in evaluation_periods(prepared, start):
        period_alerts = prepared.filter(pl.col("period_start") == period)
        worked = reference.filter(pl.col("period_start") == period)
        attempts_target = len(
            {attempt for row in worked["attempt_ids"].to_list() for attempt in row}
        )
        alerts_target = int(worked["is_true_positive"].sum())
        depths = _depth_for(order_by_score(period_alerts, scores), attempts_target, alerts_target)
        rows.append(
            {
                "period_start": period,
                "period_alerts": period_alerts.height,
                "worked": worked.height,
                **{key: depths[key] for key in depths},
                "attempts_freed": None
                if depths["attempts_depth"] is None
                else k - depths["attempts_depth"],
                "alerts_freed": None
                if depths["alerts_depth"] is None
                else k - depths["alerts_depth"],
                "target_was_zero": attempts_target == 0,
            }
        )
    return pl.DataFrame(rows)


def lift_over_ladder(pooled: pl.DataFrame, rung: str = "B3") -> pl.DataFrame:
    """Precision at K of one rung against every rung below it, at the same K."""
    precisions = dict(zip(pooled["rung"].to_list(), pooled["precision"].to_list()))
    against = [name for name in LADDER if name != rung and name in precisions]
    return pl.DataFrame(
        [
            {
                "rung": rung,
                "against": name,
                "precision": precisions[rung],
                "against_precision": precisions[name],
                "lift": precisions[rung] / precisions[name] if precisions[name] else float("inf"),
            }
            for name in against
        ]
    )
