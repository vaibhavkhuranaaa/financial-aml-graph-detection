import polars as pl
import pytest

from src.pipeline import alert_store, features, rules
from tests.test_rules import JURISDICTIONS, txn, txns


def sample() -> tuple[pl.DataFrame, pl.DataFrame]:
    frame = txns(
        [
            txn(0, 1, "A", "H1", 30_000.0, day=1),
            txn(1, 2, "A", "H2", 30_000.0, day=1),
            txn(2, 3, "X", "A", 50_000.0, day=2),
            txn(3, 4, "A", "Y", 50_100.0, day=2),
            txn(4, 5, "A", "Z", 9_500.0, day=2),
            txn(5, 6, "A", "W", 9_600.0, day=2),
            # After the day two cutoff. No feature may see these.
            txn(6, 1, "A", "L1", 900_000.0, day=3),
            txn(7, 2, "A", "L2", 900_000.0, day=3),
            txn(8, 3, "A", "L3", 900_000.0, day=3),
        ]
    )
    rows = rules.run_rules(frame, JURISDICTIONS)
    return alert_store.build_alerts(rows), frame


def test_one_feature_row_per_alert_with_a_fixed_column_set():
    alerts, frame = sample()
    built = features.build_features(alerts, frame)
    assert built.height == alerts.height
    assert built.select("alert_id").n_unique() == built.height
    assert set(features.KEY_COLUMNS).issubset(built.columns)
    assert built["feature_version"].unique().to_list() == [features.FEATURE_VERSION]
    assert len(features.feature_columns(built)) > 20


def test_the_laundering_flag_cannot_reach_the_build():
    alerts, frame = sample()
    with_label = frame.with_columns(pl.lit(0).alias("Is Laundering"))
    with pytest.raises(ValueError, match="laundering flag"):
        features.build_features(alerts, with_label)


def test_no_feature_reads_a_transaction_at_or_after_the_cutoff():
    alerts, frame = sample()
    day_two = alerts.filter(pl.col("period_start").dt.day() == 2)
    before = frame.filter(pl.col("ts") < day_two["feature_cutoff_ts"][0])

    full = features.build_features(day_two, frame)
    trimmed = features.build_features(day_two, before)
    assert full.equals(trimmed)


def test_the_leakage_gate_passes_on_a_compliant_build():
    alerts, frame = sample()
    assert features.leakage_report(alerts, frame).height == 0


def test_the_leakage_gate_catches_a_feature_that_reads_the_future(monkeypatch):
    """The gate is only worth having if it fails when it should.

    This replaces the period builder with one that ignores the cutoff. The build
    then sees the whole file while the rebuild sees a pre trimmed input, which is
    exactly the shape of a leak.
    """
    alerts, frame = sample()
    original = features._period_features

    def leaking(alerts_frame, txns, cutoff, period_start):
        built = original(alerts_frame, txns, cutoff, period_start)
        future = txns.group_by(pl.col("from_account").alias("subject_account")).agg(
            pl.col("amount").max().alias("subject_amount_max_ever")
        )
        return built.join(future, on="subject_account", how="left")

    monkeypatch.setattr(features, "_period_features", leaking)
    report = features.leakage_report(alerts, frame)
    assert report.height > 0
    assert "subject_amount_max_ever" in report["feature"].to_list()


def test_history_and_period_horizons_are_separated():
    alerts, frame = sample()
    built = features.build_features(alerts, frame)
    day_one = built.filter(pl.col("period_start").dt.day() == 1)
    day_two = built.filter(pl.col("period_start").dt.day() == 2)

    # Nothing precedes the first period, so its history is empty by construction.
    assert day_one["history_out_count"].sum() == 0
    assert day_two.filter(pl.col("subject_account") == "1|A")["history_out_count"][0] == 2


def test_missing_activity_is_zero_and_not_null():
    alerts, frame = sample()
    built = features.build_features(alerts, frame)
    numeric = [
        name for name in features.feature_columns(built) if built.schema[name].is_numeric()
    ]
    assert built.select(numeric).null_count().sum_horizontal().item() == 0


def test_the_baseline_ordering_value_is_not_a_feature():
    alerts, frame = sample()
    built = features.build_features(alerts, frame)
    assert "rules_priority" not in built.columns
    assert not [name for name in built.columns if "label" in name or "aunder" in name]
