from datetime import date

import polars as pl
import pytest

from src.pipeline import backtest, ranker
from tests.test_backtest import moment, population


def built_features(prepared: pl.DataFrame) -> pl.DataFrame:
    """A feature table shaped like the real one, with one honest signal in it.

    `signal` is the outcome's own driver, so a model that trains at all will
    order by it. That is what makes the walk forward assertions testable without
    depending on the model finding something subtle.
    """
    return prepared.select(
        "alert_id",
        "subject_account",
        "period_start",
        pl.col("period_start").alias("feature_cutoff_ts"),
        pl.col("is_true_positive").cast(pl.Float64).alias("signal"),
        pl.col("alert_amount"),
        pl.col("laundering_transactions").cast(pl.Float64).alias("noise"),
        pl.lit("alert-features/1").alias("feature_version"),
    )


def test_training_reads_prior_periods_only():
    prepared = population()
    built = built_features(prepared)
    training = ranker.training_frame(built, prepared, date(2022, 9, 4))
    assert training["period_start"].max() < moment(4)
    assert training.height == 20
    # The period being scored contributes nothing to the model that scores it.
    assert not training.filter(pl.col("period_start") == moment(4)).height


def test_the_outcome_cannot_be_offered_as_a_feature():
    prepared = population()
    built = built_features(prepared)
    training = ranker.training_frame(built, prepared, date(2022, 9, 4))
    with pytest.raises(ValueError, match="outcome"):
        ranker.train(training, ["signal", "is_true_positive"], rounds=5)


def test_one_lambdarank_group_per_review_period():
    prepared = population()
    built = built_features(prepared)
    training = ranker.training_frame(built, prepared, date(2022, 9, 4))
    dataset = ranker._dataset(training, ["signal", "alert_amount"])
    dataset.construct()
    # Two training periods of ten alerts each.
    assert dataset.get_group().tolist() == [10, 10]


def test_the_walk_forward_scores_every_evaluation_alert_once_and_deterministically():
    prepared = population()
    built = built_features(prepared)
    first, boosters = ranker.walk_forward(built, prepared, date(2022, 9, 4), rounds=10)
    second, _ = ranker.walk_forward(built, prepared, date(2022, 9, 4), rounds=10)
    assert first.height == 4
    assert first["alert_id"].n_unique() == 4
    assert first["score"].to_list() == second["score"].to_list()
    assert list(boosters) == [moment(4)]


def test_a_scored_ordering_is_worked_like_any_other_rung():
    prepared = population()
    scores = pl.DataFrame(
        {"alert_id": ["eval-0", "eval-1", "eval-2", "eval-3"], "score": [0.1, 0.2, 0.9, 0.8]}
    )
    worked = backtest.worked_queue_from_scores(prepared, scores, "C1", k=2, start=date(2022, 9, 4))
    assert worked["alert_id"].to_list() == ["eval-2", "eval-3"]
    assert worked["rung"].unique().to_list() == ["C1"]
    assert worked["period_alerts"][0] == 4


def test_an_alert_without_a_score_is_an_error_and_not_a_silent_drop():
    prepared = population()
    scores = pl.DataFrame({"alert_id": ["eval-0"], "score": [1.0]})
    with pytest.raises(ValueError, match="no score"):
        backtest.worked_queue_from_scores(prepared, scores, "C1", k=2, start=date(2022, 9, 4))


def test_spearman_is_one_on_agreement_and_minus_one_on_reversal():
    assert ranker.spearman([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]) == pytest.approx(1.0)
    assert ranker.spearman([1.0, 2.0, 3.0], [30.0, 20.0, 10.0]) == pytest.approx(-1.0)


def test_rank_stability_needs_two_retrains_and_the_minimum_training_window():
    prepared = population()
    built = built_features(prepared)
    # One evaluation period, so there is no earlier retrain to compare against.
    assert ranker.rank_stability(built, prepared, date(2022, 9, 4), rounds=10).height == 0


def test_the_depth_to_match_a_target_is_the_position_it_is_reached_at():
    ordered = pl.DataFrame(
        {
            "attempt_ids": [[], [7], [], [7, 8]],
            "is_true_positive": [False, True, False, True],
        }
    )
    depths = backtest._depth_for(ordered, attempts_target=2, alerts_target=1)
    assert depths["alerts_depth"] == 2
    assert depths["attempts_depth"] == 4


def test_a_target_of_zero_is_matched_at_depth_zero_and_is_flagged_as_empty():
    ordered = pl.DataFrame({"attempt_ids": [[]], "is_true_positive": [False]})
    depths = backtest._depth_for(ordered, attempts_target=0, alerts_target=0)
    assert depths == {
        "attempts_depth": 0,
        "alerts_depth": 0,
        "attempts_target": 0,
        "alerts_target": 0,
    }


def test_an_unreachable_target_leaves_the_depth_unset():
    ordered = pl.DataFrame({"attempt_ids": [[], []], "is_true_positive": [False, False]})
    depths = backtest._depth_for(ordered, attempts_target=1, alerts_target=1)
    assert depths["attempts_depth"] is None
    assert depths["alerts_depth"] is None


def test_volume_reduction_measures_the_depth_the_challenger_needs():
    prepared = population()
    reference = backtest.worked_queue(prepared, "B1", k=4, start=date(2022, 9, 4))
    scores = pl.DataFrame(
        {"alert_id": ["eval-0", "eval-1", "eval-2", "eval-3"], "score": [0.1, 0.2, 0.9, 0.8]}
    )
    reduction = backtest.volume_reduction(
        prepared, scores, reference, k=4, start=date(2022, 9, 4)
    )
    assert reduction.height == 1
    row = reduction.to_dicts()[0]
    # The reference works all four alerts to find both positives. The scored
    # ordering puts both first, so it holds the same coverage at depth two.
    assert row["alerts_target"] == 2
    assert row["alerts_depth"] == 2
    assert row["alerts_freed"] == 2
