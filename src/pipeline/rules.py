"""Typology rules engine for the Signal Ledger alert population.

Eight Bank Secrecy Act typology rules run over the transaction file and emit one
row per fired rule per subject account per review period. The alert store built
from these rows is the unit of everything downstream.

The laundering flag is never read here. `load_transactions` selects the columns
the rules need and the flag is not among them, so no rule can reach it even by
accident. Rules are parameterised against target alert volume only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

import polars as pl

SUBJECT = "subject_account"
PERIOD = "period"
RULE = "rule_id"
EVIDENCE = "evidence"
TXNS = "contributing_txn_ids"
ALERT_COLUMNS = [SUBJECT, PERIOD, RULE, EVIDENCE, TXNS]

# Money thresholds apply to US Dollar payments only. The file carries fourteen
# currencies and no exchange rates, so converting would mean inventing them.
THRESHOLD_CURRENCY = "US Dollar"


@dataclass(frozen=True)
class Parameters:
    """Rule parameters. Tuned against measured alert volume, never against the label."""

    # R1 structuring below a reporting threshold
    r1_threshold: float = 10_000.0
    r1_band: float = 0.15
    r1_min_count: int = 2
    # R2 rapid movement of funds
    r2_tolerance: float = 0.03
    r2_min_amount: float = 20_000.0
    r2_max_hours: float = 12.0
    # R3 fan in
    r3_min_originators: int = 12
    # R4 fan out
    r4_min_beneficiaries: int = 12
    # R5 round dollar repetition
    r5_multiple: float = 1.0
    r5_min_amount: float = 100.0
    r5_min_count: int = 2
    # R6 dormant then active
    r6_lookback_periods: int = 3
    r6_dormancy_ceiling: int = 0
    r6_activation_count: int = 6
    # R7 high risk corridor
    r7_formats: tuple[str, ...] = ("Bitcoin", "Cash")
    r7_min_amount: float = 1_000.0
    r7_min_count: int = 3
    # R8 peer group velocity deviation
    r8_min_prior_periods: int = 2
    r8_own_multiple: float = 2.0
    r8_peer_multiple: float = 2.0
    r8_min_count: int = 4

    def replace(self, **changes: object) -> Parameters:
        return replace(self, **changes)


@dataclass(frozen=True)
class Window:
    """The study window. Periods outside it are excluded from alert generation."""

    start: str = "2022-09-01"
    end: str = "2022-09-10"
    excluded_transactions: int = field(default=0, compare=False)


def load_transactions(path: str | Path, window: Window | None = None) -> pl.DataFrame:
    """Read the transaction file into the frame the rules operate on.

    The published header repeats `Account` positionally; Polars renames the
    second one. `Is Laundering` is not selected, which is the structural
    guarantee that no rule can read the label.

    Self transfers are dropped. 590,819 rows of HI-Small move value between one
    account and itself, mostly the `Reinvestment` format, and a payment to
    yourself has no counterparty, so it cannot evidence any typology in the
    catalogue. Leaving them in makes R2 fire on almost every account that
    reinvests twice in a day.
    """
    frame = (
        pl.scan_csv(path)
        .with_row_index("txn_id")
        .select(
            "txn_id",
            pl.col("Timestamp").str.to_datetime("%Y/%m/%d %H:%M").alias("ts"),
            pl.format("{}|{}", pl.col("From Bank"), pl.col("Account")).alias("from_account"),
            pl.format("{}|{}", pl.col("To Bank"), pl.col("Account_duplicated_0")).alias("to_account"),
            pl.col("From Bank").alias("from_bank"),
            pl.col("To Bank").alias("to_bank"),
            pl.col("Amount Paid").alias("amount"),
            pl.col("Payment Currency").alias("currency"),
            pl.col("Payment Format").alias("format"),
        )
        .filter(pl.col("from_account") != pl.col("to_account"))
        .with_columns(pl.col("ts").dt.date().alias(PERIOD))
        .collect()
    )
    if window is None:
        return frame.sort("ts", "txn_id")
    inside = frame.filter(
        pl.col(PERIOD).is_between(pl.lit(window.start).str.to_date(), pl.lit(window.end).str.to_date())
    )
    return inside.sort("ts", "txn_id")


def load_bank_jurisdictions(path: str | Path) -> pl.DataFrame:
    """Map bank identifier to jurisdiction from the accounts file.

    Bank names are either `<Country> Bank #n` for foreign banks or a domestic
    style name. Anything that does not match the first form is treated as one
    domestic jurisdiction, which is what the simulator's naming supports.
    """
    return (
        pl.scan_csv(path)
        .select(
            pl.col("Bank ID").alias("bank"),
            pl.col("Bank Name")
            .str.replace(r" #\d+$", "")
            .str.extract(r"^(\w+) Bank$", 1)
            .fill_null("domestic")
            .alias("jurisdiction"),
        )
        .unique(subset="bank")
        .collect()
    )


def _alerts(frame: pl.DataFrame, rule: str, evidence: list[str]) -> pl.DataFrame:
    """Shape a per rule aggregation into the common alert row schema."""
    return frame.select(
        pl.col(SUBJECT),
        pl.col(PERIOD),
        pl.lit(rule).alias(RULE),
        pl.struct(evidence).struct.json_encode().alias(EVIDENCE),
        pl.col(TXNS),
    )


def r1_structuring(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """Repeated payments sitting just below a reporting threshold in one period."""
    floor = params.r1_threshold * (1 - params.r1_band)
    near = txns.filter(
        (pl.col("currency") == THRESHOLD_CURRENCY)
        & (pl.col("amount") >= floor)
        & (pl.col("amount") < params.r1_threshold)
    )
    grouped = (
        near.group_by(pl.col("from_account").alias(SUBJECT), PERIOD)
        .agg(
            pl.len().alias("count"),
            pl.col("amount").sum().round(2).alias("total"),
            pl.col("txn_id").alias(TXNS),
        )
        .filter(pl.col("count") >= params.r1_min_count)
        .with_columns(
            pl.lit(params.r1_threshold).alias("threshold"),
            pl.lit(params.r1_band).alias("band"),
        )
    )
    return _alerts(grouped, "R1", ["count", "total", "threshold", "band"])


def r2_rapid_movement(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """A credit followed by a near equal debit from the same account."""
    big = txns.filter(pl.col("amount") >= params.r2_min_amount)
    incoming = big.select(
        pl.col("to_account").alias(SUBJECT),
        PERIOD,
        pl.col("ts").alias("in_ts"),
        pl.col("amount").alias("in_amount"),
        pl.col("txn_id").alias("in_id"),
    )
    outgoing = big.select(
        pl.col("from_account").alias(SUBJECT),
        PERIOD,
        pl.col("ts").alias("out_ts"),
        pl.col("amount").alias("out_amount"),
        pl.col("txn_id").alias("out_id"),
    )
    paired = (
        incoming.join(outgoing, on=[SUBJECT, PERIOD])
        .filter(
            (pl.col("out_ts") >= pl.col("in_ts"))
            & ((pl.col("out_ts") - pl.col("in_ts")).dt.total_hours() <= params.r2_max_hours)
            & (
                (pl.col("out_amount") - pl.col("in_amount")).abs()
                <= pl.col("in_amount") * params.r2_tolerance
            )
        )
    )
    grouped = (
        paired.group_by(SUBJECT, PERIOD)
        .agg(
            pl.len().alias("pairs"),
            pl.col("in_amount").max().round(2).alias("largest_pass_through"),
            pl.concat_list("in_id", "out_id")
            .list.explode(empty_as_null=False)
            .unique()
            .sort()
            .alias(TXNS),
        )
        .with_columns(pl.lit(params.r2_tolerance).alias("tolerance"))
    )
    return _alerts(grouped, "R2", ["pairs", "largest_pass_through", "tolerance"])


def _fan(txns: pl.DataFrame, subject: str, counterparty: str, minimum: int, rule: str) -> pl.DataFrame:
    grouped = (
        txns.group_by(pl.col(subject).alias(SUBJECT), PERIOD)
        .agg(
            pl.col(counterparty).n_unique().alias("counterparties"),
            pl.col("amount").sum().round(2).alias("total"),
            pl.col("txn_id").alias(TXNS),
        )
        .filter(pl.col("counterparties") >= minimum)
        .with_columns(pl.lit(minimum).alias("minimum_counterparties"))
    )
    return _alerts(grouped, rule, ["counterparties", "total", "minimum_counterparties"])


def r3_fan_in(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """Many distinct originators paying one beneficiary inside a period."""
    return _fan(txns, "to_account", "from_account", params.r3_min_originators, "R3")


def r4_fan_out(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """One originator paying many distinct beneficiaries inside a period."""
    return _fan(txns, "from_account", "to_account", params.r4_min_beneficiaries, "R4")


def r5_round_dollar(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """Repeated exactly round amounts, atypical of organic activity.

    Roundness is a whole dollar amount. The simulator draws amounts with cents,
    so only 1.26 percent of US Dollar payments are whole dollars and only 20 in
    the entire file are multiples of a thousand. A thousand dollar definition
    would make this rule unfireable, which is a property of the data rather than
    a parameter worth defending.
    """
    round_amounts = txns.filter(
        (pl.col("currency") == THRESHOLD_CURRENCY)
        & (pl.col("amount") >= params.r5_min_amount)
        & (pl.col("amount") % params.r5_multiple == 0)
    )
    grouped = (
        round_amounts.group_by(pl.col("from_account").alias(SUBJECT), PERIOD)
        .agg(
            pl.len().alias("count"),
            pl.col("amount").sum().round(2).alias("total"),
            pl.col("txn_id").alias(TXNS),
        )
        .filter(pl.col("count") >= params.r5_min_count)
        .with_columns(
            pl.lit(params.r5_multiple).alias("multiple"),
            pl.lit(params.r5_min_amount).alias("minimum_amount"),
        )
    )
    return _alerts(grouped, "R5", ["count", "total", "multiple", "minimum_amount"])


def r6_dormant_then_active(txns: pl.DataFrame, params: Parameters) -> pl.DataFrame:
    """An account with negligible recent history suddenly transacting at volume.

    The lookback is bounded by the study window, which is ten periods, so the
    dormancy period here is days rather than the months an institution would use.
    """
    activity = (
        txns.group_by(pl.col("from_account").alias(SUBJECT), PERIOD)
        .agg(pl.len().alias("count"), pl.col("txn_id").alias(TXNS))
        .sort(SUBJECT, PERIOD)
    )
    prior = (
        activity.rolling(index_column=PERIOD, period=f"{params.r6_lookback_periods}d", group_by=SUBJECT, closed="left")
        .agg(pl.col("count").sum().alias("prior_count"))
    )
    # The rule cannot fire until a full lookback exists behind the period.
    # Without this it fires on every busy account in the first period, where the
    # absence of history is an artefact of the window and not dormancy.
    earliest = txns.select(pl.col(PERIOD).min()).item()
    joined = (
        activity.join(prior, on=[SUBJECT, PERIOD])
        .with_columns(pl.col("prior_count").fill_null(0))
        .filter(
            (pl.col(PERIOD) >= pl.lit(earliest) + pl.duration(days=params.r6_lookback_periods))
            & (pl.col("prior_count") <= params.r6_dormancy_ceiling)
            & (pl.col("count") >= params.r6_activation_count)
        )
        .with_columns(pl.lit(params.r6_lookback_periods).alias("lookback_periods"))
    )
    return _alerts(joined, "R6", ["count", "prior_count", "lookback_periods"])


def r7_high_risk_corridor(
    txns: pl.DataFrame, jurisdictions: pl.DataFrame, params: Parameters
) -> pl.DataFrame:
    """Cross jurisdiction payments settled through an elevated risk instrument.

    The corridor is defined structurally, as a cross border payment in a cash or
    crypto instrument, rather than by naming jurisdictions as risky. Publishing a
    country risk list would be a claim about real jurisdictions that this project
    has no basis to make, and the structural definition captures the same red flag.
    """
    corridor = (
        txns.join(jurisdictions.rename({"bank": "from_bank", "jurisdiction": "from_jurisdiction"}), on="from_bank", how="left")
        .join(jurisdictions.rename({"bank": "to_bank", "jurisdiction": "to_jurisdiction"}), on="to_bank", how="left")
        .filter(
            (pl.col("from_jurisdiction") != pl.col("to_jurisdiction"))
            & pl.col("format").is_in(params.r7_formats)
            & (pl.col("amount") >= params.r7_min_amount)
        )
    )
    grouped = (
        corridor.group_by(pl.col("from_account").alias(SUBJECT), PERIOD)
        .agg(
            pl.len().alias("count"),
            pl.col("amount").sum().round(2).alias("total"),
            pl.col("to_jurisdiction").n_unique().alias("jurisdictions"),
            pl.col("txn_id").alias(TXNS),
        )
        .filter(pl.col("count") >= params.r7_min_count)
    )
    return _alerts(grouped, "R7", ["count", "total", "jurisdictions"])


def r8_peer_velocity(
    txns: pl.DataFrame, jurisdictions: pl.DataFrame, params: Parameters
) -> pl.DataFrame:
    """Activity far above the account's own history and above its peer group.

    The peer group is the originating bank. Prior periods only, so this rule
    cannot fire before an account has `r8_min_prior_periods` of history.
    """
    activity = (
        txns.group_by(pl.col("from_account").alias(SUBJECT), "from_bank", PERIOD)
        .agg(pl.len().alias("count"), pl.col("txn_id").alias(TXNS))
        .sort(SUBJECT, PERIOD)
    )
    own = activity.rolling(index_column=PERIOD, period="10d", group_by=SUBJECT, closed="left").agg(
        pl.col("count").mean().alias("own_mean"),
        pl.len().alias("prior_periods"),
    )
    peer = (
        activity.group_by("from_bank", PERIOD)
        .agg(pl.col("count").mean().alias("peer_mean"))
    )
    joined = (
        activity.join(own, on=[SUBJECT, PERIOD])
        .join(peer, on=["from_bank", PERIOD])
        .filter(
            (pl.col("prior_periods") >= params.r8_min_prior_periods)
            & (pl.col("count") >= params.r8_min_count)
            & (pl.col("count") >= pl.col("own_mean") * params.r8_own_multiple)
            & (pl.col("count") >= pl.col("peer_mean") * params.r8_peer_multiple)
        )
        .with_columns(
            pl.col("own_mean").round(3),
            pl.col("peer_mean").round(3),
        )
    )
    return _alerts(joined, "R8", ["count", "own_mean", "peer_mean", "prior_periods"])


def run_rules(
    txns: pl.DataFrame, jurisdictions: pl.DataFrame, params: Parameters | None = None
) -> pl.DataFrame:
    """Run the full catalogue and return one row per fired rule per subject period."""
    params = params or Parameters()
    fired = [
        r1_structuring(txns, params),
        r2_rapid_movement(txns, params),
        r3_fan_in(txns, params),
        r4_fan_out(txns, params),
        r5_round_dollar(txns, params),
        r6_dormant_then_active(txns, params),
        r7_high_risk_corridor(txns, jurisdictions, params),
        r8_peer_velocity(txns, jurisdictions, params),
    ]
    return pl.concat([frame.select(ALERT_COLUMNS) for frame in fired]).sort(PERIOD, SUBJECT, RULE)


def rule_report(rows: pl.DataFrame, txns: pl.DataFrame) -> pl.DataFrame:
    """Per rule base rate and alert volume, measured before any alert is ranked.

    Base rate is fired subject periods over evaluated subject periods, where an
    evaluated subject period is any account active in that period.
    """
    subject_periods = (
        pl.concat(
            [
                txns.select(pl.col("from_account").alias(SUBJECT), PERIOD),
                txns.select(pl.col("to_account").alias(SUBJECT), PERIOD),
            ]
        )
        .unique()
        .height
    )
    periods = txns.select(PERIOD).n_unique()
    return (
        rows.group_by(RULE)
        .agg(
            pl.len().alias("rows"),
            pl.col(SUBJECT).n_unique().alias("subjects"),
            pl.col(TXNS).list.len().sum().alias("contributing_transactions"),
        )
        .with_columns(
            (pl.col("rows") / periods).round(1).alias("rows_per_period"),
            (pl.col("rows") / subject_periods).alias("base_rate"),
        )
        .sort(RULE)
    )


def alert_volume(rows: pl.DataFrame) -> pl.DataFrame:
    """Alerts per period, where one alert is one subject in one period.

    Rules fire independently and an alert can carry several, so the alert count
    is the distinct subject period count and never the sum of the rule rows.
    """
    return (
        rows.group_by(PERIOD)
        .agg(pl.col(SUBJECT).n_unique().alias("alerts"), pl.len().alias("rule_rows"))
        .sort(PERIOD)
    )


def overlap(rows: pl.DataFrame) -> pl.DataFrame:
    """How many rules each alert carries. Heavy overlap inflates volume without coverage."""
    return (
        rows.group_by(SUBJECT, PERIOD)
        .agg(pl.col(RULE).n_unique().alias("rules"))
        .group_by("rules")
        .agg(pl.len().alias("alerts"))
        .sort("rules")
    )


def parameters_json(params: Parameters) -> str:
    """Stable serialisation of the parameter set, for the store version hash."""
    return json.dumps({k: v for k, v in sorted(vars(params).items())}, default=list, sort_keys=True)
