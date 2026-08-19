"""Build alert level features and run the leakage gate.

Local only. Nothing here is served and the laundering flag is never an input.
"""

import argparse
import sys
from pathlib import Path

import polars as pl

from src.pipeline import alert_store, features, rules


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/features"))
    parser.add_argument("--start", default=rules.Window().start)
    parser.add_argument("--end", default=rules.Window().end)
    parser.add_argument("--sample", type=int, default=200)
    args = parser.parse_args()

    window = rules.Window(start=args.start, end=args.end)
    txns = rules.load_transactions(args.transactions, window)
    alerts = alert_store.read_store(args.store)

    gate = features.leakage_report(alerts, txns, sample=args.sample)
    built = features.build_features(alerts, txns)

    args.out.mkdir(parents=True, exist_ok=True)
    destination = args.out / f"{features.FEATURE_VERSION.replace('/', '-')}.parquet"
    built.write_parquet(destination, compression="uncompressed")

    columns = features.feature_columns(built)
    with pl.Config(tbl_rows=40, tbl_width_chars=200):
        print(f"features: {destination}")
        print(f"alerts: {built.height}")
        print(f"feature columns: {len(columns)}")
        for name in columns:
            print(f"  {name}")
        print(built.select(columns).describe())

    if gate.height:
        print("LEAKAGE GATE FAILED")
        print(gate)
        sys.exit(1)
    print(f"leakage gate: pass on a sample of {min(args.sample, alerts.height)} alerts")


if __name__ == "__main__":
    main()
