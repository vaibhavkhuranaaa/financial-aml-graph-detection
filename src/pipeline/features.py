"""Alert level feature build, with the leakage cutoff as its first constraint.

One row per alert. Every value is computed from transactions dated strictly
before the alert's `feature_cutoff_ts`, which is the contract the leakage gate
enforces in `leakage_report`.

Two things are deliberately not here. The laundering flag is not an input, so no
feature can read it even by accident. B3's ordering value is not a feature
either, because a challenger that consumes its own baseline is not a comparison.
"""

from __future__ import annotations

import polars as pl

from src.pipeline import rules

FEATURE_VERSION = "alert-features/1"

KEY_COLUMNS = ["alert_id", "subject_account", "period_start", "feature_cutoff_ts"]

RULE_IDS = [f"R{n}" for n in range(1, 9)]

CORRIDOR_FORMATS = ["Bitcoin", "Cash"]


def _subject_activity(txns: pl.DataFrame, side: str, prefix: str) -> pl.DataFrame:
    """Aggregate one side of the ledger for every account."""
    counterparty = "to_account" if side == "from_account" else "from_account"
    return txns.group_by(pl.col(side).alias("subject_account")).agg(
        pl.len().alias(f"{prefix}_count"),
        pl.col(counterparty).n_unique().alias(f"{prefix}_counterparties"),
        pl.col("amount").sum().alias(f"{prefix}_amount_total"),
        pl.col("amount").max().alias(f"{prefix}_amount_max"),
        pl.col("amount").mean().alias(f"{prefix}_amount_mean"),
    )


def _period_features(
    alerts: pl.DataFrame, txns: pl.DataFrame, cutoff, period_start
) -> pl.DataFrame:
    """Features for one period's alerts, from transactions before its cutoff.

    Two horizons. History is everything strictly before the period, which is what
    tells a busy account from a newly active one. The period itself is what the
    rules fired on, and it stops at the cutoff.
    """
    before_cutoff = txns.filter(pl.col("ts") < cutoff)
    history = before_cutoff.filter(pl.col("ts") < period_start)
    in_period = before_cutoff.filter(pl.col("ts") >= period_start)

    features = alerts.select(KEY_COLUMNS + ["fired_rules", "contributing_txn_ids"])
    for frame, side, prefix in (
        (history, "from_account", "history_out"),
        (history, "to_account", "history_in"),
        (in_period, "from_account", "period_out"),
        (in_period, "to_account", "period_in"),
    ):
        features = features.join(
            _subject_activity(frame, side, prefix), on="subject_account", how="left"
        )

    period_shape = in_period.group_by(pl.col("from_account").alias("subject_account")).agg(
        pl.col("ts").dt.hour().std().alias("period_hour_spread"),
        (pl.col("amount") % 1 == 0).mean().alias("period_whole_dollar_share"),
        pl.col("format").is_in(CORRIDOR_FORMATS).mean().alias("period_corridor_format_share"),
        (pl.col("from_bank") != pl.col("to_bank")).mean().alias("period_cross_bank_share"),
        pl.col("currency").n_unique().alias("period_currencies"),
    )
    features = features.join(period_shape, on="subject_account", how="left")

    active_periods = history.group_by(pl.col("from_account").alias("subject_account")).agg(
        pl.col(rules.PERIOD).n_unique().alias("history_active_periods")
    )
    features = features.join(active_periods, on="subject_account", how="left")

    return features.with_columns(
        pl.col("fired_rules").list.len().alias("fired_rule_count"),
        pl.col("contributing_txn_ids").list.len().alias("contributing_transactions"),
        *[
            pl.col("fired_rules").list.contains(rule).cast(pl.Int8).alias(f"fired_{rule.lower()}")
            for rule in RULE_IDS
        ],
    ).drop("fired_rules", "contributing_txn_ids")


def build_features(alerts: pl.DataFrame, txns: pl.DataFrame) -> pl.DataFrame:
    """One feature row per alert, computed strictly before each alert's cutoff.

    Alerts in one period share a cutoff, so the build runs once per period rather
    than once per alert.
    """
    if "Is Laundering" in txns.columns or any("aunder" in name for name in txns.columns):
        raise ValueError("the laundering flag must not reach the feature build")

    periods = alerts.select("period_start", "feature_cutoff_ts").unique().sort("period_start")
    frames = [
        _period_features(
            alerts.filter(pl.col("period_start") == period_start),
            txns,
            cutoff,
            period_start,
        )
        for period_start, cutoff in periods.iter_rows()
    ]
    return _finalise(pl.concat(frames))


def _finalise(built: pl.DataFrame) -> pl.DataFrame:
    """Fill the gaps a left join leaves, add the ratios, stamp the version.

    A null here means the account had no activity on that side, which is a zero
    and not a missing value.
    """
    return (
        built.sort("period_start", "alert_id")
        .with_columns(
            [pl.col(name).fill_null(0) for name in built.columns if built.schema[name].is_numeric()]
        )
        .with_columns(*_derived(), pl.lit(FEATURE_VERSION).alias("feature_version"))
    )


def _derived() -> list[pl.Expr]:
    """Ratios that say more than either side alone."""
    history_rate = pl.col("history_out_count") / pl.col("history_active_periods").clip(
        lower_bound=1
    )
    return [
        (pl.col("period_out_count") / history_rate.clip(lower_bound=0.001)).alias(
            "period_over_history_rate"
        ),
        (
            pl.col("period_out_counterparties") / pl.col("period_out_count").clip(lower_bound=1)
        ).alias("period_counterparty_ratio"),
        (
            pl.col("period_out_amount_total")
            / pl.col("history_out_amount_total").clip(lower_bound=1.0)
        ).alias("period_over_history_amount"),
    ]


def feature_columns(features: pl.DataFrame) -> list[str]:
    """The model facing columns, in a fixed order."""
    return [name for name in features.columns if name not in {*KEY_COLUMNS, "feature_version"}]


def leakage_report(
    alerts: pl.DataFrame, txns: pl.DataFrame, sample: int = 200, seed: int = 0
) -> pl.DataFrame:
    """The leakage gate.

    Rebuild a sample of alerts from an input with every transaction at or after
    the cutoff removed. A feature that reads the future changes value here, and
    the difference is the report. An empty frame is a pass.
    """
    sampled = alerts.sample(n=min(sample, alerts.height), seed=seed)
    full = build_features(sampled, txns)

    trimmed = []
    for period_start, cutoff in (
        sampled.select("period_start", "feature_cutoff_ts").unique().sort("period_start").iter_rows()
    ):
        trimmed.append(
            _period_features(
                sampled.filter(pl.col("period_start") == period_start),
                txns.filter(pl.col("ts") < cutoff),
                cutoff,
                period_start,
            )
        )
    rebuilt = _finalise(pl.concat(trimmed))

    differences = []
    for column in feature_columns(full):
        mismatched = (
            full.select("alert_id", column)
            .join(rebuilt.select("alert_id", column), on="alert_id", suffix="_trimmed")
            .filter(pl.col(column) != pl.col(f"{column}_trimmed"))
        )
        if mismatched.height:
            differences.append({"feature": column, "mismatched_alerts": mismatched.height})
    return pl.DataFrame(
        differences, schema={"feature": pl.String, "mismatched_alerts": pl.UInt32}
    )
