"""Run the rules engine and write the alert store.

Local only. Raw transaction files and the alert store never enter Git.
"""

import argparse
from pathlib import Path

import polars as pl

from src.pipeline import alert_store, rules


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--accounts", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/alerts"))
    parser.add_argument("--start", default=rules.Window().start)
    parser.add_argument("--end", default=rules.Window().end)
    args = parser.parse_args()

    params = rules.Parameters()
    window = rules.Window(start=args.start, end=args.end)

    everything = rules.load_transactions(args.transactions)
    txns = everything.filter(
        pl.col(rules.PERIOD).is_between(
            pl.lit(window.start).str.to_date(), pl.lit(window.end).str.to_date()
        )
    ).sort("ts", "txn_id")
    excluded = everything.height - txns.height

    jurisdictions = rules.load_bank_jurisdictions(args.accounts)
    rows = rules.run_rules(txns, jurisdictions, params)
    alerts = alert_store.build_alerts(rows, params)
    destination = alert_store.write_store(alerts, args.out, params)

    with pl.Config(tbl_rows=20, tbl_width_chars=200):
        print(f"store: {destination}")
        print(f"transactions in window: {txns.height}")
        print(f"transactions excluded by the window: {excluded}")
        print(f"rule rows: {rows.height}")
        print(f"alerts: {alerts.height}")
        print(alert_store.period_index(alerts))
        print(f"store digest: {alert_store.store_digest(destination)}")


if __name__ == "__main__":
    main()
