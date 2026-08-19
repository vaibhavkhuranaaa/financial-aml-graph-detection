"""C1, the learned ranker over alerts.

LightGBM lambdarank, one group per review period, trained on prior periods only
and walked forward one period at a time. The product decision is an ordering
inside a period, which is what lambdarank optimises, so the model is never asked
for a probability and nothing surfaces one.

Two constraints the code enforces rather than documents. The label reaches this
module only as the training target for periods strictly before the period being
scored, and it arrives already joined by the backtest harness. B3's ordering
value is not a feature, because a challenger that consumes its own baseline is
not a comparison.
"""

from __future__ import annotations

from datetime import date

import lightgbm as lgb
import polars as pl

from src.pipeline import backtest, features

MODEL_VERSION = "lambdarank/1"

# Small data, so the model is kept small on purpose. 9,171 alerts across ten
# periods with a 3.9 percent positive rate cannot support a deep ensemble, and a
# tuned one would be fitted to the evaluation periods it is meant to be tested
# on. These are defaults chosen for the data size, not a search.
PARAMS = {
    "objective": "lambdarank",
    "metric": "ndcg",
    "ndcg_eval_at": [backtest.K_ALERTS],
    "label_gain": [0, 1],
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_data_in_leaf": 40,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambdarank_truncation_level": backtest.K_ALERTS,
    "seed": 0,
    "deterministic": True,
    "force_row_wise": True,
    "num_threads": 1,
    "verbosity": -1,
}

ROUNDS = 200


def training_frame(
    built: pl.DataFrame, prepared: pl.DataFrame, before: date
) -> pl.DataFrame:
    """Features and outcomes for every period strictly before `before`.

    The strict inequality is the whole walk forward guarantee, so it lives in one
    function and every caller goes through it.
    """
    outcomes = prepared.select("alert_id", "period_start", "is_true_positive")
    return (
        built.drop("period_start")
        .join(outcomes, on="alert_id", how="inner")
        .filter(pl.col("period_start").dt.date() < before)
        .sort("period_start", "alert_id")
    )


def _dataset(frame: pl.DataFrame, columns: list[str]) -> lgb.Dataset:
    """One lambdarank group per review period, which is the unit being ordered."""
    groups = frame.group_by("period_start", maintain_order=True).len()["len"].to_list()
    return lgb.Dataset(
        frame.select(columns).to_numpy(),
        label=frame["is_true_positive"].cast(pl.Int8).to_numpy(),
        group=groups,
        feature_name=columns,
        free_raw_data=False,
    )


def train(frame: pl.DataFrame, columns: list[str], rounds: int = ROUNDS) -> lgb.Booster:
    if any("aunder" in name or name == "is_true_positive" for name in columns):
        raise ValueError("the outcome must not be offered to the model as a feature")
    return lgb.train(PARAMS, _dataset(frame, columns), num_boost_round=rounds)


def score(booster: lgb.Booster, built: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """One score per alert. An ordering value, never a probability."""
    return built.select("alert_id", "period_start").with_columns(
        pl.Series("score", booster.predict(built.select(columns).to_numpy()))
    )


def walk_forward(
    built: pl.DataFrame,
    prepared: pl.DataFrame,
    start: date = backtest.EVALUATION_START,
    rounds: int = ROUNDS,
) -> tuple[pl.DataFrame, dict]:
    """Score every evaluation period with a model that has seen only its past.

    Returns the scores and the boosters, keyed by the period they were trained
    for, because rank stability needs two successive models over one period.
    """
    columns = features.feature_columns(built)
    scored = []
    boosters = {}
    for period in backtest.evaluation_periods(prepared, start):
        training = training_frame(built, prepared, period.date())
        booster = train(training, columns, rounds)
        boosters[period] = booster
        scored.append(score(booster, built.filter(pl.col("period_start") == period), columns))
    return pl.concat(scored), boosters


def spearman(left: list[float], right: list[float]) -> float:
    """Rank correlation, computed as Pearson over average ranks.

    Written here rather than pulled in, because it is six lines and the only
    thing the project would use SciPy for.
    """
    frame = pl.DataFrame({"left": left, "right": right}).with_columns(
        pl.col("left").rank("average").alias("left_rank"),
        pl.col("right").rank("average").alias("right_rank"),
    )
    return frame.select(pl.corr("left_rank", "right_rank")).item()


def rank_stability(
    built: pl.DataFrame,
    prepared: pl.DataFrame,
    start: date = backtest.EVALUATION_START,
    rounds: int = ROUNDS,
    minimum_training_periods: int = 3,
) -> pl.DataFrame:
    """Correlation between two successive retrains scoring the same period.

    A queue that reshuffles on every retrain cannot be operated, whatever the
    headline says. The comparison is the same period's alerts ordered by the
    model trained through the period before it and by the model trained one
    period earlier than that, so the only difference between them is one
    period of training data.

    The earlier model must still meet the minimum training window, which is why
    the first evaluation period has no pair.
    """
    columns = features.feature_columns(built)
    periods = backtest.evaluation_periods(prepared, start)
    rows = []
    for index, period in enumerate(periods):
        earlier = periods[index - 1] if index else None
        if earlier is None:
            continue
        older = training_frame(built, prepared, earlier.date())
        if older.select("period_start").n_unique() < minimum_training_periods:
            continue
        current = built.filter(pl.col("period_start") == period)
        recent_scores = score(
            train(training_frame(built, prepared, period.date()), columns, rounds),
            current,
            columns,
        )
        older_scores = score(train(older, columns, rounds), current, columns)
        rows.append(
            {
                "period_start": period,
                "alerts": current.height,
                "spearman": spearman(
                    recent_scores["score"].to_list(), older_scores["score"].to_list()
                ),
            }
        )
    return pl.DataFrame(rows)


def importance(booster: lgb.Booster, columns: list[str], top: int = 12) -> pl.DataFrame:
    """What the model split on. The explanation payload starts here."""
    return (
        pl.DataFrame(
            {"feature": columns, "gain": booster.feature_importance("gain").tolist()}
        )
        .sort("gain", descending=True)
        .head(top)
    )
