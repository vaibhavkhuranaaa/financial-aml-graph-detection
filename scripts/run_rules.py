"""Run the typology rules engine and print the base rate and volume report.

Local only. Raw transaction files never enter Git and nothing here is served.
"""

import argparse
from pathlib import Path

import polars as pl

from src.pipeline.rules import (
    Parameters,
    Window,
    alert_volume,
    load_bank_jurisdictions,
    load_transactions,
    overlap,
    rule_report,
    run_rules,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--accounts", type=Path, required=True)
    parser.add_argument("--start", default=Window().start)
    parser.add_argument("--end", default=Window().end)
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    args = parser.parse_args()

    params = Parameters()
    for override in args.set:
        name, _, value = override.partition("=")
        current = getattr(params, name)
        params = params.replace(**{name: type(current)(value)})

    window = Window(start=args.start, end=args.end)
    txns = load_transactions(args.transactions, window)
    jurisdictions = load_bank_jurisdictions(args.accounts)
    rows = run_rules(txns, jurisdictions, params)

    volume = alert_volume(rows)
    with pl.Config(tbl_rows=40, tbl_width_chars=200, fmt_str_lengths=60):
        print(f"transactions in window: {txns.height}")
        print(f"periods: {txns.select('period').n_unique()}")
        print(rule_report(rows, txns))
        print(volume)
        print(overlap(rows))
        print(f"mean alerts per period: {volume.select(pl.col('alerts').mean()).item():.1f}")


if __name__ == "__main__":
    main()
