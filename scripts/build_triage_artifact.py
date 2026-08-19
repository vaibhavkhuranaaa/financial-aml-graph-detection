"""Build the bounded triage artifact for one review period.

Local only. Building an artifact does not approve it for publication: the
distribution decision passed in has to approve the exact source checksum, and the
API's admission check refuses anything that does not. Raw transaction files never
enter Git and nothing here runs on the serving path.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from src.pipeline import backtest, rules, triage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--backtest", type=Path, default=Path("data/backtest/challenger-1.json"))
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument(
        "--distribution",
        type=Path,
        default=Path("data/provenance/ibm_aml_data_v8_triage_distribution.json"),
    )
    parser.add_argument("--out", type=Path, default=Path("data/fixtures/public_triage.json"))
    parser.add_argument("--period", default="2022-09-07")
    parser.add_argument("--start", default=rules.Window().start)
    parser.add_argument("--end", default=rules.Window().end)
    parser.add_argument("--k", type=int, default=backtest.K_ALERTS)
    parser.add_argument("--analysts", type=int, default=6)
    parser.add_argument("--productive-hours", type=float, default=7.0)
    parser.add_argument("--handling-minutes", type=float, default=20.0)
    args = parser.parse_args()

    operating_point = {
        "analysts": args.analysts,
        "productive_hours_per_analyst": args.productive_hours,
        "handling_minutes_per_alert": args.handling_minutes,
        "k_alerts_worked_per_period": args.k,
        "assumption_note": (
            "Analyst count, productive hours and handling time are assumptions "
            "rather than measurements. Handling time is adjustable here and the "
            "alert count follows from it."
        ),
    }
    payload = triage.build_from_paths(
        transactions=args.transactions,
        patterns=args.patterns,
        store=args.store,
        feature_table=args.features,
        backtest_record=args.backtest,
        source_manifest=json.loads(args.source_manifest.read_text(encoding="utf-8")),
        distribution=json.loads(args.distribution.read_text(encoding="utf-8"))
        if args.distribution.exists()
        else {},
        period=date.fromisoformat(args.period),
        operating_point=operating_point,
        window=rules.Window(start=args.start, end=args.end),
    )
    destination = triage.write_artifact(payload, args.out)

    period = payload["period"]
    print(f"artifact: {destination}")
    print(f"bytes: {destination.stat().st_size}")
    print(f"period: {period['start']}")
    print(f"alerts: {period['alerts']}")
    print(f"true positive alerts: {period['true_positives']}")
    print(f"period base rate: {period['base_rate']:.4f}")
    print(f"K: {args.k}, coverage {args.k / period['alerts']:.4f} of the period")
    print(f"orderings: {', '.join(item['id'] for item in payload['orderings'])}")
    print(f"artifact digest: {payload['artifact_sha256']}")
    print(f"pipeline run id: {payload['provenance']['pipeline_run_id']}")
    print(f"distribution: {payload['provenance']['distribution']['status']}")
    structural = [rule["rule_id"] for rule in payload["rules"] if not rule["supported"]]
    print(f"structural zeros: {', '.join(structural)}")
    print(
        "gate: lift "
        f"{payload['result']['gate']['lift']:.4f} against "
        f"{payload['result']['gate']['threshold']}, met "
        f"{payload['result']['gate']['met']}"
    )


if __name__ == "__main__":
    main()
