"""Build the tiny, reproducible public IBM AML-Data scenario fixture.

The full source stays local. This script publishes only the selected rows below
and replaces source account identifiers with deterministic pseudonyms.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUTPUT = Path("data/fixtures/public_casefile.json")
SOURCE_SHA256 = "b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040"


def pseudonym(account: str) -> str:
    return f"Party-{hashlib.sha256(account.encode()).hexdigest()[:6].upper()}"


def compact(row: dict[str, str], index: int) -> dict[str, str | float]:
    return {
        "id": f"txn-{index:02d}", "timestamp": row["Timestamp"],
        "from": pseudonym(row["From Account"]), "to": pseudonym(row["To Account"]),
        "amount": float(row["Amount Paid"]), "currency": row["Payment Currency"],
        "rail": row["Payment Format"],
    }


def main() -> None:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Source checksum does not match recorded IBM AML-Data v8 file.")
    # Fixed, documented selection: first 16-row FAN-OUT sequence (shown in the
    # provider's matching v8 pattern manifest), plus first three chronological
    # non-laundering ACH rows after 2022/09/01 00:20 for the closure comparison.
    escalation: list[dict[str, str]] = []
    closure: list[dict[str, str]] = []
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)
        for values in reader:
            row = dict(zip(("Timestamp", "From Bank", "From Account", "To Bank", "To Account", "Amount Received", "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering"), values, strict=True))
            if row["From Account"] == "800737690" and row["Is Laundering"] == "1" and len(escalation) < 16:
                escalation.append(row)
            if row["Is Laundering"] == "0" and row["Payment Format"] == "ACH" and len(closure) < 5:
                closure.append(row)
            if len(escalation) == 16 and len(closure) == 5:
                break
    if len(escalation) != 16 or len(closure) != 5:
        raise SystemExit("Expected deterministic v8 escalation and closure selections were not found.")
    payload = {"provenance": {"provider": "IBM / Erik Altman", "dataset": "IBM Transactions for Anti Money Laundering (AML)", "version": 8, "retrieved": "2026-07-24", "license": "CDLA-Sharing-1.0", "source_file": "HI-Small_Trans.csv", "source_sha256": SOURCE_SHA256, "selection": "first v8 HI-Small FAN-OUT manifest sequence; first five chronological non-laundering ACH comparison rows", "attribution_url": "https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml"}, "cases": [{"id": "sim-escalation-fanout", "outcome": "Simulated escalation", "transactions": [compact(row, index) for index, row in enumerate(escalation, 1)]}, {"id": "sim-closure-compare", "outcome": "Simulated closure", "transactions": [compact(row, index) for index, row in enumerate(closure, 1)]}]}
    payload["slice_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
