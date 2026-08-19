"""Alert store: the unit of everything downstream of the rules engine.

The rules engine emits one row per fired rule per subject period. This collapses
those rows into one row per alert, attaches the trigger evidence, and writes the
store as Parquet partitioned by review period.

The laundering flag is not a field here and never becomes one. The join to it
happens once, in the backtest harness, at M4.

`rules_priority` is deliberately absent, which amends the record contract in
`system-design.md`. See decision record 0004: B3 weights each fired rule by its
historical hit rate, a hit rate is a function of the label, and the label must
not enter this store. The anti-leak property the contract wanted comes from
computing it over prior periods only, which the backtest does, and not from the
field's storage location.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import polars as pl

from src.pipeline import rules

ENGINE_VERSION = "rules-engine/1"

ALERT_SCHEMA = [
    "alert_id",
    "subject_account",
    "period_start",
    "period_end",
    "fired_rules",
    "rule_evidence",
    "contributing_txn_ids",
    "feature_cutoff_ts",
    "engine_version",
    "param_set_hash",
]


def param_set_hash(params: rules.Parameters) -> str:
    """Stable hash of the parameter set. Two stores compare only if this matches."""
    return hashlib.sha256(rules.parameters_json(params).encode()).hexdigest()[:16]


def store_version(params: rules.Parameters) -> str:
    return f"{ENGINE_VERSION.replace('/', '-')}_{param_set_hash(params)}"


def _alert_id(subject: pl.Expr, period: pl.Expr, fired: pl.Expr) -> pl.Expr:
    """Deterministic identifier from subject, period start and the fired rule set.

    Not a surrogate key. The backtest and the evidence records depend on the same
    source and parameter set producing the same identifiers on every run.
    """
    material = pl.concat_str(subject, period.cast(pl.String), fired.list.join(","), separator="|")
    return material.hash(seed=0).cast(pl.String).str.zfill(20)


def build_alerts(rows: pl.DataFrame, params: rules.Parameters | None = None) -> pl.DataFrame:
    """Collapse rule rows into one row per subject period, to the record contract."""
    params = params or rules.Parameters()
    collapsed = (
        rows.sort(rules.SUBJECT, rules.PERIOD, rules.RULE)
        .group_by(rules.SUBJECT, rules.PERIOD, maintain_order=True)
        .agg(
            pl.col(rules.RULE).unique().sort().alias("fired_rules"),
            pl.struct(rule_id=pl.col(rules.RULE), evidence=pl.col(rules.EVIDENCE)).alias(
                "rule_evidence"
            ),
            pl.col(rules.TXNS)
            .list.explode(empty_as_null=False)
            .unique()
            .sort()
            .alias("contributing_txn_ids"),
        )
    )
    period_start = pl.col(rules.PERIOD).cast(pl.Datetime("us"))
    return (
        collapsed.with_columns(
            period_start.alias("period_start"),
            (period_start + pl.duration(days=1)).alias("period_end"),
        )
        .with_columns(
            _alert_id(pl.col(rules.SUBJECT), pl.col("period_start"), pl.col("fired_rules")).alias(
                "alert_id"
            ),
            # Equal to period_end today. Held as its own field so that a design
            # with a reporting lag can move it without changing what a period means.
            pl.col("period_end").alias("feature_cutoff_ts"),
            pl.lit(ENGINE_VERSION).alias("engine_version"),
            pl.lit(param_set_hash(params)).alias("param_set_hash"),
        )
        .select(ALERT_SCHEMA)
        .sort("period_start", "alert_id")
    )


def write_store(alerts: pl.DataFrame, root: str | Path, params: rules.Parameters | None = None) -> Path:
    """Write the store partitioned by review period.

    The store directory is replaced rather than appended to. An alert is
    immutable once written, and a correction is a new store version, because the
    backtest compares stores and an edited store silently invalidates every prior
    result.
    """
    params = params or rules.Parameters()
    destination = Path(root) / store_version(params)
    if destination.exists():
        shutil.rmtree(destination)
    for (period,), partition in alerts.group_by("period_start", maintain_order=True):
        directory = destination / f"period={period.date().isoformat()}"
        directory.mkdir(parents=True)
        partition.write_parquet(directory / "alerts.parquet", compression="uncompressed")
    return destination


def read_store(path: str | Path) -> pl.DataFrame:
    return pl.read_parquet(Path(path) / "**/*.parquet").sort("period_start", "alert_id")


def store_digest(path: str | Path) -> str:
    """Digest over every partition file, for the byte identical rebuild check."""
    digest = hashlib.sha256()
    for file in sorted(Path(path).rglob("*.parquet")):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()[:16]


def evidence_for(alert: dict) -> list[dict]:
    """Parse the stored rule evidence back into structures.

    The engine emits evidence as JSON so that eight rules with eight different
    trigger quantities can share one column. Parsing is the reader's job.
    """
    return [
        {"rule_id": item["rule_id"], **json.loads(item["evidence"])}
        for item in alert["rule_evidence"]
    ]


def period_index(alerts: pl.DataFrame) -> pl.DataFrame:
    """Alerts and contributing transactions per period, with denominators."""
    return (
        alerts.group_by("period_start")
        .agg(
            pl.len().alias("alerts"),
            pl.col("fired_rules").list.len().sum().alias("rule_rows"),
            pl.col("contributing_txn_ids").list.len().sum().alias("contributing_transactions"),
        )
        .sort("period_start")
    )
