import polars as pl

from src.pipeline import alert_store, rules
from tests.test_rules import JURISDICTIONS, txn, txns


def sample_rows() -> pl.DataFrame:
    frame = txns(
        [
            txn(0, 1, "X", "A", 50_000.0),
            txn(1, 2, "A", "Y", 50_100.0),
            txn(2, 3, "A", "Z", 9_500.0),
            txn(3, 4, "A", "W", 9_600.0),
            txn(4, 5, "B", "Q", 9_500.0, day=2),
            txn(5, 6, "B", "R", 9_600.0, day=2),
        ]
    )
    return rules.run_rules(frame, JURISDICTIONS)


def test_alerts_collapse_rule_rows_to_one_row_per_subject_period():
    rows = sample_rows()
    alerts = alert_store.build_alerts(rows)
    assert alerts.columns == alert_store.ALERT_SCHEMA
    assert alerts.height < rows.height
    assert alerts.select("alert_id").n_unique() == alerts.height
    subject_periods = rows.select(rules.SUBJECT, rules.PERIOD).unique().height
    assert alerts.height == subject_periods


def test_the_label_is_absent_from_the_schema():
    alerts = alert_store.build_alerts(sample_rows())
    assert not [name for name in alerts.columns if "aunder" in name or "label" in name]
    # rules_priority is deliberately absent. See decision record 0004.
    assert "rules_priority" not in alerts.columns


def test_alert_id_is_deterministic_and_depends_on_the_fired_rule_set():
    rows = sample_rows()
    first = alert_store.build_alerts(rows)
    second = alert_store.build_alerts(rows.sample(fraction=1.0, shuffle=True, seed=7))
    assert first.equals(second)

    dropped = rows.filter(pl.col(rules.RULE) != "R1")
    changed = alert_store.build_alerts(dropped)
    shared = set(first["alert_id"]) & set(changed["alert_id"])
    assert len(shared) < first.height


def test_contributing_transactions_are_deduplicated_and_sorted():
    alerts = alert_store.build_alerts(sample_rows())
    for ids in alerts["contributing_txn_ids"].to_list():
        assert list(ids) == sorted(set(ids))


def test_rule_evidence_parses_back_to_one_entry_per_fired_rule():
    alerts = alert_store.build_alerts(sample_rows())
    row = alerts.row(0, named=True)
    parsed = alert_store.evidence_for(row)
    assert [item["rule_id"] for item in parsed] == sorted(row["fired_rules"])
    assert all(len(item) > 1 for item in parsed)


def test_feature_cutoff_is_its_own_field_and_never_precedes_the_period():
    alerts = alert_store.build_alerts(sample_rows())
    assert alerts["feature_cutoff_ts"].to_list() == alerts["period_end"].to_list()
    assert (alerts["period_end"] > alerts["period_start"]).all()


def test_store_rebuild_is_byte_identical_and_partitioned_by_period(tmp_path):
    alerts = alert_store.build_alerts(sample_rows())
    first = alert_store.write_store(alerts, tmp_path)
    digest = alert_store.store_digest(first)
    second = alert_store.write_store(alerts, tmp_path)
    assert alert_store.store_digest(second) == digest

    partitions = sorted(path.name for path in first.iterdir())
    assert partitions == ["period=2022-09-01", "period=2022-09-02"]
    assert alert_store.read_store(first).equals(alerts)


def test_a_changed_parameter_set_writes_a_different_store_version(tmp_path):
    params = rules.Parameters()
    other = params.replace(r1_band=0.25)
    assert alert_store.param_set_hash(params) != alert_store.param_set_hash(other)

    alerts = alert_store.build_alerts(sample_rows(), params)
    written = alert_store.write_store(alerts, tmp_path, params)
    assert written.name == alert_store.store_version(params)
    assert alert_store.read_store(written)["param_set_hash"].unique().to_list() == [
        alert_store.param_set_hash(params)
    ]
