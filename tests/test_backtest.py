from datetime import date, datetime

import polars as pl

from src.pipeline import alert_store, backtest, rules
from tests.test_rules import JURISDICTIONS, txn, txns

PATTERNS = """BEGIN LAUNDERING ATTEMPT - FAN-OUT:  Max 3-degree Fan-Out
2022/09/01 01:00,1,AAA,1,BBB,100.00,US Dollar,100.00,US Dollar,ACH,1
2022/09/01 02:00,1,AAA,1,CCC,200.00,US Dollar,200.00,US Dollar,ACH,1
END LAUNDERING ATTEMPT - FAN-OUT

BEGIN LAUNDERING ATTEMPT - CYCLE:  Max 2 hops
2022/09/12 03:00,1,DDD,1,EEE,300.00,US Dollar,300.00,US Dollar,ACH,1
END LAUNDERING ATTEMPT - CYCLE
"""

TRANSACTIONS = (
    "Timestamp,From Bank,Account,To Bank,Account,Amount Received,Receiving Currency,"
    "Amount Paid,Payment Currency,Payment Format,Is Laundering\n"
    "2022/09/01 01:00,1,AAA,1,BBB,100.00,US Dollar,100.00,US Dollar,ACH,1\n"
    "2022/09/01 02:00,1,AAA,1,CCC,200.00,US Dollar,200.00,US Dollar,ACH,1\n"
    "2022/09/01 03:00,1,AAA,1,DDD,400.00,US Dollar,400.00,US Dollar,ACH,1\n"
    "2022/09/01 04:00,1,FFF,1,GGG,500.00,US Dollar,500.00,US Dollar,ACH,1\n"
    "2022/09/01 05:00,1,HHH,1,III,600.00,US Dollar,600.00,US Dollar,ACH,0\n"
    # Dated after the study window. The label join still reads it.
    "2022/09/12 03:00,1,DDD,1,EEE,300.00,US Dollar,300.00,US Dollar,ACH,1\n"
)


def moment(day: int, hour: int = 0) -> datetime:
    """A naive timestamp, matching the alert store's own column type."""
    return datetime.fromisoformat(f"2022-09-{day:02d}T{hour:02d}:00:00")


def sources(tmp_path):
    transactions = tmp_path / "trans.csv"
    transactions.write_text(TRANSACTIONS, encoding="utf-8")
    patterns = tmp_path / "patterns.txt"
    patterns.write_text(PATTERNS, encoding="utf-8")
    return transactions, patterns


def test_patterns_parse_into_attempts_with_their_typology(tmp_path):
    _, patterns = sources(tmp_path)
    parsed = backtest.parse_patterns(patterns)
    assert parsed.height == 3
    assert parsed["attempt_id"].to_list() == [0, 0, 1]
    assert parsed["typology"].to_list() == ["FAN-OUT", "FAN-OUT", "CYCLE"]


def test_the_label_join_reads_days_after_the_study_window(tmp_path):
    """An outcome observed later is how a suspicious activity report works.

    Features stay bound by feature_cutoff_ts; the label deliberately is not.
    """
    transactions, patterns = sources(tmp_path)
    labels = backtest.load_labels(transactions, patterns)
    after_the_window = labels.filter(pl.col(rules.PERIOD) > date(2022, 9, 10))
    assert after_the_window.height == 1
    assert after_the_window["typology"].to_list() == ["CYCLE"]


def test_a_flagged_transaction_with_no_attempt_keeps_a_null_typology(tmp_path):
    transactions, patterns = sources(tmp_path)
    labels = backtest.load_labels(transactions, patterns)
    assert labels.height == 5
    assert labels["typology"].null_count() == 2


def test_an_alert_is_a_true_positive_when_a_contributing_transaction_is_flagged():
    alerts = pl.DataFrame(
        {
            "alert_id": ["one", "two"],
            "contributing_txn_ids": [[0, 9], [7]],
        }
    )
    labels = pl.DataFrame(
        {
            "txn_id": [0, 4],
            rules.PERIOD: [date(2022, 9, 1), date(2022, 9, 1)],
            "attempt_id": [None, 3],
            "typology": [None, "CYCLE"],
        },
        schema_overrides={"txn_id": pl.Int64, "attempt_id": pl.Int64},
    )
    labelled = backtest.label_alerts(alerts, labels).sort("alert_id")
    assert labelled["is_true_positive"].to_list() == [True, False]
    # The positive carries no attempt, so it is on the unattributed line and is
    # neither folded into a typology nor dropped.
    assert labelled["unattributed_only"].to_list() == [True, False]
    assert labelled["typologies"].to_list() == [[], []]


def population() -> pl.DataFrame:
    """Two training periods and one evaluation period, hand built.

    R_HIGH resolves as suspicious in the training periods and R_LOW does not, so
    a prior period hit rate has an ordering to express.
    """
    rows = []
    for day in (1, 2):
        for index in range(10):
            rows.append(
                {
                    "alert_id": f"train-{day}-{index}",
                    "subject_account": f"1|A{index}",
                    "period_start": moment(day),
                    "fired_rules": ["R3"] if index < 5 else ["R1"],
                    "first_txn_ts": moment(day),
                    "alert_amount": 10.0,
                    "laundering_transactions": 1 if index < 5 else 0,
                    "attempt_ids": [index] if index < 5 else [],
                    "typologies": ["FAN-IN"] if index < 5 else [],
                    "is_true_positive": index < 5,
                    "unattributed_only": False,
                }
            )
    for index in range(4):
        rows.append(
            {
                "alert_id": f"eval-{index}",
                "subject_account": f"1|B{index}",
                "period_start": moment(4),
                # The low hit rate rule fires first in the day and carries the
                # larger amount, so only B3 can put the R3 alerts on top.
                "fired_rules": ["R1"] if index < 2 else ["R3"],
                "first_txn_ts": moment(4, index),
                "alert_amount": 100.0 + index,
                "laundering_transactions": 0 if index < 2 else 1,
                "attempt_ids": [] if index < 2 else [100 + index],
                "typologies": [] if index < 2 else ["FAN-IN"],
                "is_true_positive": index >= 2,
                "unattributed_only": False,
            }
        )
    return pl.DataFrame(rows).with_columns(
        pl.col("period_start").cast(pl.Datetime("us")),
        pl.col("first_txn_ts").cast(pl.Datetime("us")),
    )


def test_b3_weights_rules_by_their_hit_rate_in_prior_periods_only():
    prepared = population()
    worked = backtest.worked_queue(prepared, "B3", k=2, start=date(2022, 9, 4), prior_weight=0)
    assert worked["alert_id"].to_list() == ["eval-2", "eval-3"]

    rates = backtest.rule_hit_rates(prepared, moment(4), 0)
    high = rates.filter(pl.col("rule_id") == "R3")
    assert high["prior_alerts"][0] == 10
    assert high["observed_rate"][0] == 1.0
    # The evaluation period's own outcomes are not in the denominator.
    assert rates["prior_alerts"].sum() == 20


def test_shrinkage_keeps_a_rule_with_three_observations_off_the_top_band():
    """R6 fires three times before 2022/09/09 and hits every time on the real run.

    An unsmoothed rate reads that as 1.0 and hands the rule the whole priority
    band. The estimator shrinks it toward the pooled rate instead.
    """
    prepared = population()
    thin = prepared.head(1).with_columns(
        pl.lit("thin").alias("alert_id"),
        pl.lit(["R6"]).alias("fired_rules"),
        pl.lit(True).alias("is_true_positive"),
    )
    rates = backtest.rule_hit_rates(
        pl.concat([prepared, thin]), moment(4), 126
    )
    r6 = rates.filter(pl.col("rule_id") == "R6")
    assert r6["observed_rate"][0] == 1.0
    assert r6["hit_rate"][0] < rates.filter(pl.col("rule_id") == "R3")["hit_rate"][0]


def test_every_catalogue_rule_appears_in_the_hit_rate_table():
    rates = backtest.rule_hit_rates(population(), moment(4))
    assert rates["rule_id"].to_list() == sorted(backtest.RULE_SUPPORT)
    unfired = rates.filter(pl.col("rule_id") == "R7")
    assert unfired["prior_alerts"][0] == 0
    assert unfired["observed_rate"][0] is None


def test_the_lower_rungs_order_by_time_and_by_amount():
    prepared = population()
    chronological = backtest.worked_queue(prepared, "B1", k=4, start=date(2022, 9, 4))
    assert chronological["alert_id"].to_list() == ["eval-0", "eval-1", "eval-2", "eval-3"]
    by_amount = backtest.worked_queue(prepared, "B2", k=4, start=date(2022, 9, 4))
    assert by_amount["alert_id"].to_list() == ["eval-3", "eval-2", "eval-1", "eval-0"]
    assert by_amount["queue_position"].to_list() == [1, 2, 3, 4]


def test_precision_is_counted_before_it_is_rated():
    prepared = population()
    worked = backtest.worked_queue(prepared, "B3", k=2, start=date(2022, 9, 4), prior_weight=0)
    pooled, per_period = backtest.precision_tables(worked)
    assert pooled["true_positives"][0] == 2
    assert pooled["worked"][0] == 2
    assert pooled["precision"][0] == 1.0
    assert per_period["period_alerts"][0] == 4


def test_a_period_smaller_than_k_is_worked_out_and_not_padded():
    prepared = population()
    worked = backtest.worked_queue(prepared, "B1", k=backtest.K_ALERTS, start=date(2022, 9, 4))
    assert worked.height == 4


def test_typology_recall_prints_the_attempt_count_behind_every_figure():
    prepared = population()
    labels = pl.DataFrame(
        {
            "txn_id": [1, 2, 3],
            rules.PERIOD: [date(2022, 9, 4)] * 3,
            "attempt_id": [102, 103, 200],
            "typology": ["FAN-IN", "FAN-IN", "CYCLE"],
        },
        schema_overrides={"txn_id": pl.Int64, "attempt_id": pl.Int64},
    )
    universe = backtest.attempt_universe(prepared, labels, date(2022, 9, 4))
    assert set(universe["attempt_id"].to_list()) == {102, 103, 200}
    # Attempt 200 is live in the period and no alert carries it, so the rules
    # never surfaced it and no ordering can recover it.
    assert universe.filter(pl.col("attempt_id") == 200)["surfaced"][0] is False

    worked = backtest.worked_queue(prepared, "B2", k=4, start=date(2022, 9, 4))
    recall, per_attempt = backtest.typology_recall(worked, universe)
    fan_in = recall.filter(pl.col("typology") == "FAN-IN")
    assert fan_in["attempts"][0] == 2
    assert fan_in["attempts_surfaced"][0] == 2
    assert fan_in["attempts_recovered"][0] == 2
    cycle = recall.filter(pl.col("typology") == "CYCLE")
    assert cycle["attempts"][0] == 1
    assert cycle["attempts_recovered"][0] == 0
    assert per_attempt.height == 3


def test_the_structural_zeros_carry_an_attempt_count_of_zero_and_not_a_recall():
    universe = pl.DataFrame(
        {
            "attempt_id": [1, 2],
            "typology": ["FAN-IN", "STACK"],
            "surfaced": [True, False],
        }
    )
    support = backtest.rule_support_table(universe)
    unsupported = support.filter(~pl.col("supported"))
    assert unsupported["rule_id"].to_list() == ["R1", "R5", "R6", "R7", "R8"]
    assert unsupported["attempts"].to_list() == [0, 0, 0, 0, 0]
    assert "recall" not in support.columns
    assert support.filter(pl.col("rule_id") == "R3")["attempts"][0] == 1


def test_the_unattributed_positives_are_reported_as_their_own_line():
    prepared = population().with_columns(
        pl.when(pl.col("alert_id") == "eval-2")
        .then(True)
        .otherwise(pl.col("unattributed_only"))
        .alias("unattributed_only")
    )
    worked = backtest.worked_queue(prepared, "B1", k=4, start=date(2022, 9, 4))
    line = backtest.unattributed_line(worked, prepared, date(2022, 9, 4))
    assert line["typology"].to_list() == [backtest.UNATTRIBUTED]
    assert line["alerts_in_population"][0] == 1
    assert line["alerts_recovered"][0] == 1


def test_the_bootstrap_interval_brackets_the_point_estimate():
    outcomes = [1] * 20 + [0] * 80
    low, high = backtest.bootstrap_mean(outcomes, samples=500, seed=1)
    assert low < 0.20 < high


def test_lift_is_reported_against_every_lower_rung():
    pooled = pl.DataFrame(
        {"rung": ["B0", "B1", "B2", "B3"], "precision": [0.05, 0.10, 0.20, 0.10]}
    )
    lift = backtest.lift_over_ladder(pooled)
    assert lift["against"].to_list() == ["B0", "B1", "B2"]
    assert lift.filter(pl.col("against") == "B2")["lift"][0] == 0.5


def test_the_ladder_runs_end_to_end_on_a_built_alert_store(tmp_path):
    """One pass through the real path: rules, store, label join, ordering."""
    frame = txns([txn(index, index, "A", f"B{index}", 1_000.0 + index) for index in range(14)])
    rows = rules.run_rules(frame, JURISDICTIONS)
    alerts = alert_store.build_alerts(rows)
    labels = pl.DataFrame(
        {
            "txn_id": [0],
            rules.PERIOD: [date(2022, 9, 1)],
            "attempt_id": [None],
            "typology": [None],
        },
        schema_overrides={"txn_id": pl.UInt32, "attempt_id": pl.Int64},
    )
    prepared = backtest.prepare(alerts, frame, labels)
    assert prepared.height == alerts.height
    assert prepared["is_true_positive"].sum() == 1
    assert prepared["alert_amount"][0] > 0
    worked = backtest.worked_queue(prepared, "B2", k=1, start=date(2022, 9, 1))
    assert worked.height == 1
