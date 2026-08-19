"""Score the baseline ladder B0 to B3 and write the run record.

Local only. This is the one place the laundering flag is read, and it is read
after the ordering exists, never before it. Nothing here is served.
"""

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from src.pipeline import alert_store, backtest, rules


def interval(bounds: tuple[float, float]) -> str:
    return f"[{bounds[0]:.4f}, {bounds[1]:.4f}]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/backtest"))
    parser.add_argument("--k", type=int, default=backtest.K_ALERTS)
    parser.add_argument("--start", default=rules.Window().start)
    parser.add_argument("--end", default=rules.Window().end)
    parser.add_argument("--evaluation-start", default=backtest.EVALUATION_START.isoformat())
    parser.add_argument("--bootstrap", type=int, default=backtest.BOOTSTRAP_SAMPLES)
    parser.add_argument("--prior-weight", type=int, default=backtest.PRIOR_WEIGHT)
    args = parser.parse_args()

    evaluation_start = date.fromisoformat(args.evaluation_start)
    window = rules.Window(start=args.start, end=args.end)
    txns = rules.load_transactions(args.transactions, window)
    alerts = alert_store.read_store(args.store)
    labels = backtest.load_labels(args.transactions, args.patterns)
    prepared = backtest.prepare(alerts, txns, labels)

    worked = pl.concat(
        [
            backtest.worked_queue(
                prepared, rung, k=args.k, start=evaluation_start, prior_weight=args.prior_weight
            )
            for rung in backtest.LADDER
        ]
    )
    pooled, per_period = backtest.precision_tables(worked)

    # B3 with the shrinkage removed, published beside the reported ladder so the
    # estimator choice is visible rather than argued.
    unsmoothed = backtest.worked_queue(
        prepared, "B3", k=args.k, start=evaluation_start, prior_weight=0
    )
    unsmoothed_pooled, _ = backtest.precision_tables(unsmoothed)
    unsmoothed = unsmoothed.with_columns(pl.lit("B3 unsmoothed").alias("rung"))
    universe = backtest.attempt_universe(prepared, labels, evaluation_start)
    # Both B3 variants carry a per typology line, because shrinkage buys
    # precision and gives up attributed attempts, and reporting only the half
    # that improved is the aggregate that hides a typology.
    reported = pl.concat([worked, unsmoothed])
    recall, per_attempt = backtest.typology_recall(reported, universe)
    unattributed = backtest.unattributed_line(
        prepared=prepared, worked=reported, start=evaluation_start
    )
    support = backtest.rule_support_table(universe)
    lift = backtest.lift_over_ladder(pooled)

    population = prepared.filter(pl.col("period_start").dt.date() >= evaluation_start)
    base_rate = backtest.population_base_rate(prepared, evaluation_start)

    precision_intervals = {
        rung: backtest.bootstrap_mean(
            worked.filter(pl.col("rung") == rung)["is_true_positive"].cast(pl.Int8).to_list(),
            samples=args.bootstrap,
        )
        for rung in backtest.LADDER
    }
    lift_intervals = {
        row["against"]: backtest.bootstrap_lift(
            per_period, row["rung"], row["against"], samples=args.bootstrap
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

    with pl.Config(tbl_rows=60, tbl_width_chars=220):
        print(f"evaluation periods: {len(backtest.evaluation_periods(prepared, evaluation_start))}")
        print(f"alerts in the evaluation population: {population.height}")
        print(f"true positive alerts in the population: {population['is_true_positive'].sum()}")
        print(f"population base rate: {base_rate:.4f}")
        print(f"K: {args.k} alerts worked per period")
        print()
        print("LADDER, pooled over the evaluation periods")
        print(pooled)
        for rung in backtest.LADDER:
            row = pooled.filter(pl.col("rung") == rung).to_dicts()[0]
            print(
                f"  {rung}: {row['true_positives']} true positives in {row['worked']} worked alerts, "
                f"precision {row['precision']:.4f}, 95 percent interval {interval(precision_intervals[rung])}"
            )
        row = unsmoothed_pooled.to_dicts()[0]
        print(
            f"  B3 with no shrinkage, for comparison and not the reported rung: "
            f"{row['true_positives']} true positives in {row['worked']} worked alerts, "
            f"precision {row['precision']:.4f}"
        )
        print()
        print("LADDER, per period")
        print(per_period)
        print()
        print(f"B3 RULE HIT RATES, prior periods only, shrinkage weight {args.prior_weight} alerts")
        for period in backtest.evaluation_periods(prepared, evaluation_start):
            print(f"  period {period.date().isoformat()}")
            print(backtest.rule_hit_rates(prepared, period, args.prior_weight))
        print()
        print("LIFT of B3 over each lower rung, paired bootstrap over the seven periods")
        print(lift)
        for row in lift.to_dicts():
            print(
                f"  B3 over {row['against']}: {row['lift']:.4f}, "
                f"95 percent interval {interval(lift_intervals[row['against']])}"
            )
        print()
        print("PER TYPOLOGY RECALL at K, attempts live in the evaluation periods")
        print(recall)
        for row in recall.to_dicts():
            bounds = recall_intervals[(row["rung"], row["typology"])]
            print(
                f"  {row['rung']} {row['typology']}: {row['attempts_recovered']} of {row['attempts']} "
                f"attempts recovered, {row['attempts_surfaced']} surfaced by the rules, "
                f"recall {row['recall']:.4f}, 95 percent interval {interval(bounds)}"
            )
        print()
        print("UNATTRIBUTED positives, reported as their own line in alerts, not attempts")
        print(unattributed)
        print()
        print("RULE SUPPORT. An empty typology list is a structural zero, not a failed rule.")
        print(support)

    args.out.mkdir(parents=True, exist_ok=True)
    destination = args.out / "baseline-ladder-1.json"
    record = {
        "k": args.k,
        "study_window": [args.start, args.end],
        "evaluation_start": args.evaluation_start,
        "engine_version": alerts["engine_version"][0],
        "param_set_hash": alerts["param_set_hash"][0],
        # The parameter set is held fixed across dataset variants, so the engine
        # version and the parameter hash are identical on HI-Small and LI-Small
        # and cannot tell two run records apart. The source file names and the
        # store digest are what identify which population a number came from.
        "source": {
            "transactions": args.transactions.name,
            "patterns": args.patterns.name,
        },
        "store_digest": alert_store.store_digest(args.store),
        "alerts_in_population": population.height,
        "true_positive_alerts": int(population["is_true_positive"].sum()),
        "population_base_rate": base_rate,
        "bootstrap_samples": args.bootstrap,
        "prior_weight": args.prior_weight,
        "pooled": pooled.to_dicts(),
        "b3_unsmoothed": unsmoothed_pooled.to_dicts(),
        "b3_hit_rates": {
            period.date().isoformat(): backtest.rule_hit_rates(
                prepared, period, args.prior_weight
            ).to_dicts()
            for period in backtest.evaluation_periods(prepared, evaluation_start)
        },
        "per_period": [
            {**row, "period_start": row["period_start"].date().isoformat()}
            for row in per_period.to_dicts()
        ],
        "precision_intervals": {rung: list(bounds) for rung, bounds in precision_intervals.items()},
        "lift": lift.to_dicts(),
        "lift_intervals": {name: list(bounds) for name, bounds in lift_intervals.items()},
        "typology_recall": recall.to_dicts(),
        "recall_intervals": {
            f"{rung}|{typology}": list(bounds)
            for (rung, typology), bounds in recall_intervals.items()
        },
        "unattributed": unattributed.to_dicts(),
        "rule_support": support.to_dicts(),
    }
    destination.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    print(f"\nrun record: {destination}")


if __name__ == "__main__":
    main()
