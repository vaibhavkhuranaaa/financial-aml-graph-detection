"""Train C1 across the walk forward and score it against the whole ladder.

Local only. The model never reaches the deployed runtime and LightGBM is pinned
in requirements-dev.txt alone.
"""

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from src.pipeline import alert_store, backtest, features, ranker, rules


def interval(bounds: tuple[float, float]) -> str:
    return f"[{bounds[0]:.4f}, {bounds[1]:.4f}]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/backtest"))
    parser.add_argument("--k", type=int, default=backtest.K_ALERTS)
    parser.add_argument("--start", default=rules.Window().start)
    parser.add_argument("--end", default=rules.Window().end)
    parser.add_argument("--evaluation-start", default=backtest.EVALUATION_START.isoformat())
    parser.add_argument("--bootstrap", type=int, default=backtest.BOOTSTRAP_SAMPLES)
    parser.add_argument("--rounds", type=int, default=ranker.ROUNDS)
    args = parser.parse_args()

    evaluation_start = date.fromisoformat(args.evaluation_start)
    window = rules.Window(start=args.start, end=args.end)
    txns = rules.load_transactions(args.transactions, window)
    alerts = alert_store.read_store(args.store)
    labels = backtest.load_labels(args.transactions, args.patterns)
    prepared = backtest.prepare(alerts, txns, labels)
    built = pl.read_parquet(args.features)
    columns = features.feature_columns(built)

    scores, boosters = ranker.walk_forward(built, prepared, evaluation_start, args.rounds)
    rungs = {
        rung: backtest.worked_queue(prepared, rung, k=args.k, start=evaluation_start)
        for rung in backtest.LADDER
    }
    rungs["C1"] = backtest.worked_queue_from_scores(
        prepared, scores, "C1", k=args.k, start=evaluation_start
    )
    worked = pl.concat(rungs.values())

    pooled, per_period = backtest.precision_tables(worked)
    universe = backtest.attempt_universe(prepared, labels, evaluation_start)
    recall, per_attempt = backtest.typology_recall(worked, universe)
    unattributed = backtest.unattributed_line(worked, prepared, evaluation_start)
    lift = backtest.lift_over_ladder(pooled, "C1")

    # The reference for the headline is the strongest rung, which M4 measured as
    # B2 and not B3. See decision record 0006.
    reference = max(
        backtest.LADDER,
        key=lambda rung: pooled.filter(pl.col("rung") == rung)["precision"][0],
    )
    reduction = backtest.volume_reduction(
        prepared, scores, rungs[reference], k=args.k, start=evaluation_start
    )
    stability = ranker.rank_stability(built, prepared, evaluation_start, args.rounds)

    precision_intervals = {
        rung: backtest.bootstrap_mean(
            worked.filter(pl.col("rung") == rung)["is_true_positive"].cast(pl.Int8).to_list(),
            samples=args.bootstrap,
        )
        for rung in rungs
    }
    lift_intervals = {
        row["against"]: backtest.bootstrap_lift(
            per_period, "C1", row["against"], samples=args.bootstrap
        )
        for row in lift.to_dicts()
    }
    recall_intervals = {
        (row["rung"], row["typology"]): backtest.bootstrap_mean(
            per_attempt.filter(
                (pl.col("rung") == row["rung"]) & (pl.col("typology") == row["typology"])
            )["recovered"]
            .cast(pl.Int8)
            .to_list(),
            samples=args.bootstrap,
        )
        for row in recall.to_dicts()
    }

    matched = reduction.filter(pl.col("alerts_depth").is_not_null())
    alerts_freed = matched["alerts_freed"].sum() if matched.height else 0
    reduction_rate = alerts_freed / (args.k * reduction.height)

    with pl.Config(tbl_rows=60, tbl_width_chars=220):
        print(f"model: {ranker.MODEL_VERSION}, {args.rounds} rounds, {len(columns)} features")
        print(f"reference rung for the headline: {reference}")
        print()
        print("LADDER AND CHALLENGER, pooled")
        print(pooled)
        for rung in pooled["rung"].to_list():
            row = pooled.filter(pl.col("rung") == rung).to_dicts()[0]
            print(
                f"  {rung}: {row['true_positives']} true positives in {row['worked']} worked "
                f"alerts, precision {row['precision']:.4f}, "
                f"95 percent interval {interval(precision_intervals[rung])}"
            )
        print()
        print("LIFT of C1 over every rung, paired bootstrap over the periods")
        for row in lift.to_dicts():
            print(
                f"  C1 over {row['against']}: {row['lift']:.4f}, "
                f"95 percent interval {interval(lift_intervals[row['against']])}"
            )
        print()
        print("PER PERIOD")
        print(per_period)
        print()
        print("PER TYPOLOGY RECALL at K, attempts live in the evaluation periods")
        print(recall)
        for row in recall.to_dicts():
            bounds = recall_intervals[(row["rung"], row["typology"])]
            print(
                f"  {row['rung']} {row['typology']}: {row['attempts_recovered']} of "
                f"{row['attempts']} attempts, {row['attempts_surfaced']} surfaced, "
                f"recall {row['recall']:.4f}, 95 percent interval {interval(bounds)}"
            )
        print()
        print("UNATTRIBUTED positives, in alerts rather than attempts")
        print(unattributed)
        print()
        print(f"FALSE POSITIVE REDUCTION at held coverage, against {reference} at K = {args.k}")
        print(reduction)
        print(
            f"  pooled, in true positive alerts held: {alerts_freed} of "
            f"{args.k * reduction.height} worked alerts freed, {reduction_rate:.4f}"
        )
        print(
            f"  periods where the attempt target was zero, so the attempt criterion is "
            f"empty: {reduction['target_was_zero'].sum()} of {reduction.height}"
        )
        print()
        print("RANK STABILITY between successive retrains on the same period")
        print(stability)
        print()
        print("FEATURE IMPORTANCE of the last model, by gain")
        print(ranker.importance(boosters[max(boosters)], columns))

    args.out.mkdir(parents=True, exist_ok=True)
    destination = args.out / "challenger-1.json"
    record = {
        "model_version": ranker.MODEL_VERSION,
        "rounds": args.rounds,
        "params": ranker.PARAMS,
        "features": columns,
        "k": args.k,
        "evaluation_start": args.evaluation_start,
        "reference_rung": reference,
        "engine_version": alerts["engine_version"][0],
        "param_set_hash": alerts["param_set_hash"][0],
        # Same reason as the ladder record: the parameter set does not move
        # between dataset variants, so it cannot identify the population.
        "source": {
            "transactions": args.transactions.name,
            "patterns": args.patterns.name,
            "features": args.features.name,
        },
        "store_digest": alert_store.store_digest(args.store),
        "pooled": pooled.to_dicts(),
        "precision_intervals": {rung: list(bounds) for rung, bounds in precision_intervals.items()},
        "per_period": [
            {**row, "period_start": row["period_start"].date().isoformat()}
            for row in per_period.to_dicts()
        ],
        "lift": lift.to_dicts(),
        "lift_intervals": {name: list(bounds) for name, bounds in lift_intervals.items()},
        "typology_recall": recall.to_dicts(),
        "recall_intervals": {
            f"{rung}|{typology}": list(bounds)
            for (rung, typology), bounds in recall_intervals.items()
        },
        "unattributed": unattributed.to_dicts(),
        "volume_reduction": [
            {**row, "period_start": row["period_start"].date().isoformat()}
            for row in reduction.to_dicts()
        ],
        "volume_reduction_pooled": reduction_rate,
        "rank_stability": [
            {**row, "period_start": row["period_start"].date().isoformat()}
            for row in stability.to_dicts()
        ],
        "importance": ranker.importance(boosters[max(boosters)], columns, len(columns)).to_dicts(),
    }
    destination.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    print(f"\nrun record: {destination}")


if __name__ == "__main__":
    main()
