"""Offline-only construction and admission checks for public replay artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = (
    "Timestamp", "From Bank", "Account", "To Bank", "Account",
    "Amount Received", "Receiving Currency", "Amount Paid", "Payment Currency",
    "Payment Format", "Is Laundering",
)
NORMALIZED_COLUMNS = (
    "Timestamp", "From Bank", "From Account", "To Bank", "To Account",
    "Amount Received", "Receiving Currency", "Amount Paid", "Payment Currency",
    "Payment Format", "Is Laundering",
)
LICENSE = "CDLA-Sharing-1.0"
LICENSE_URL = "https://cdla.dev/sharing-1-0/"
ARTIFACT_SCHEMA = "signal-ledger-public-replay/v1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_rows(source: Path):
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        if tuple(next(reader, [])) != REQUIRED_COLUMNS:
            raise ValueError("Source schema does not match the recorded HI-Small transaction schema.")
        for values in reader:
            if len(values) != len(NORMALIZED_COLUMNS):
                raise ValueError("Source contains a row outside the recorded HI-Small transaction schema.")
            yield dict(zip(NORMALIZED_COLUMNS, values, strict=True))


def validate_source(source: Path, manifest: dict[str, Any]) -> str:
    if manifest.get("verification_status") != "verified":
        raise ValueError("Source manifest is not verified.")
    if manifest.get("dataset_version") != 8 or manifest.get("source_file") != source.name:
        raise ValueError("Source manifest does not describe IBM AML-Data v8 input.")
    if manifest.get("license") != LICENSE or manifest.get("license_url") != LICENSE_URL:
        raise ValueError("Source manifest is missing the CDLA-Sharing-1.0 record.")
    actual = sha256_file(source)
    if manifest.get("source_sha256") != actual:
        raise ValueError("Source checksum does not match its verified manifest.")
    rows = source_rows(source)
    next(rows, None)
    return actual


def pseudonym(account: str) -> str:
    return f"Party-{hashlib.sha256(account.encode('utf-8')).hexdigest()[:10].upper()}"


def transaction(row: dict[str, str], index: int) -> dict[str, str | float]:
    return {
        "id": f"txn-{index:02d}",
        "timestamp": row["Timestamp"],
        "from": pseudonym(row["From Account"]),
        "to": pseudonym(row["To Account"]),
        "amount": float(row["Amount Paid"]),
        "currency": row["Payment Currency"],
        "rail": row["Payment Format"],
    }


def validate_distribution(decision: dict[str, Any], source_sha256: str) -> None:
    if decision.get("public_distribution_status") != "approved":
        raise ValueError("Distribution decision does not approve public materialization.")
    if decision.get("dataset_version") != 8 or decision.get("license") != LICENSE:
        raise ValueError("Distribution decision does not cover IBM AML-Data v8 under CDLA-Sharing-1.0.")
    if decision.get("approved_source_sha256") != source_sha256:
        raise ValueError("Distribution decision does not approve this verified source checksum.")


def build_artifact(source: Path, source_manifest: dict[str, Any], distribution: dict[str, Any]) -> dict[str, Any]:
    source_sha256 = validate_source(source, source_manifest)
    validate_distribution(distribution, source_sha256)
    ordering = lambda item: (item[1]["Timestamp"], item[0])
    laundering_by_party: dict[str, list[tuple[int, dict[str, str]]]] = {}
    closure: list[tuple[int, dict[str, str]]] = []
    cash_escalation: list[tuple[int, dict[str, str]]] = []
    mixed_rail_escalation: list[tuple[int, dict[str, str]]] = []
    card_closure: list[tuple[int, dict[str, str]]] = []

    def keep_first(bucket: list[tuple[int, dict[str, str]]], item: tuple[int, dict[str, str]], maximum: int) -> None:
        bucket.append(item)
        bucket.sort(key=ordering)
        del bucket[maximum:]

    for index, row in enumerate(source_rows(source)):
        item = (index, row)
        if row["Is Laundering"] == "1":
            laundering_by_party.setdefault(row["From Account"], []).append(item)
            if row["Payment Format"] == "Cash":
                keep_first(cash_escalation, item, 8)
            keep_first(mixed_rail_escalation, item, 18)
        if row["Is Laundering"] == "0" and row["Payment Format"] == "ACH":
            keep_first(closure, item, 8)
        if row["Is Laundering"] == "0" and row["Payment Format"] == "Credit Card":
            keep_first(card_closure, item, 8)
    candidates = [(party, sorted(items, key=ordering)) for party, items in laundering_by_party.items() if len(items) >= 16]
    if not candidates:
        raise ValueError("No source party has 16 laundering rows for the bounded escalation case.")
    escalation_party, escalation = min(candidates, key=lambda item: (ordering(item[1][0]), item[0]))
    if len(cash_escalation) != 8 or len(closure) != 8 or len(card_closure) != 8:
        raise ValueError("Expected enough ordered rows for the bounded synthetic sequence cases.")
    mixed_rails = {row["Payment Format"] for _, row in mixed_rail_escalation}
    if len(mixed_rail_escalation) < 10 or len(mixed_rails) < 3:
        raise ValueError("Expected an ordered laundering sequence spanning at least three payment rails.")
    selection = {
        "escalation": "earliest source account with at least 16 laundering rows; first 16 ordered by Timestamp then CSV row index",
        "cash_sequence": "first eight laundering Cash rows ordered by Timestamp then CSV row index",
        "mixed_rail_sequence": "first ten laundering rows from the earliest ordered sequence spanning at least three payment rails",
        "ach_sequence": "first eight non-laundering ACH rows ordered by Timestamp then CSV row index",
        "card_sequence": "first eight non-laundering Credit Card rows ordered by Timestamp then CSV row index",
        "pseudonymization": "SHA-256(account identifier), first 10 uppercase hexadecimal characters, prefixed Party-",
        "selected_source_account_sha256": hashlib.sha256(escalation_party.encode("utf-8")).hexdigest(),
    }
    run_material = {"artifact_schema": ARTIFACT_SCHEMA, "source_sha256": source_sha256, "selection": selection}
    payload: dict[str, Any] = {
        "artifact_schema": ARTIFACT_SCHEMA,
        "provenance": {
            "provider": "IBM / Erik Altman",
            "dataset": "IBM Transactions for Anti Money Laundering (AML)",
            "dataset_version": 8,
            "source_ref": source_manifest["source_ref"],
            "retrieved_at": source_manifest["retrieved_at"],
            "source_file": source.name,
            "source_sha256": source_sha256,
            "source_schema": list(REQUIRED_COLUMNS),
            "license": LICENSE,
            "license_url": LICENSE_URL,
            "distribution": {
                "classification": "Enhanced Data",
                "status": "approved",
                "notice": "Modified, selected, and pseudonymized from IBM AML-Data; published under CDLA-Sharing-1.0 with retained attribution.",
            },
            "selection": selection,
            "pipeline_run_id": hashlib.sha256(canonical_bytes(run_material)).hexdigest(),
        },
        "cases": [
            {"id": "sim-escalation-fanout", "outcome": "Simulated escalation", "transactions": [transaction(row, index) for index, (_, row) in enumerate(escalation[:16], 1)]},
            {"id": "sim-escalation-cash-sequence", "outcome": "Simulated escalation", "transactions": [transaction(row, index) for index, (_, row) in enumerate(cash_escalation, 1)]},
            {"id": "sim-escalation-mixed-rails", "outcome": "Simulated escalation", "transactions": [transaction(row, index) for index, (_, row) in enumerate(mixed_rail_escalation[:10], 1)]},
            {"id": "sim-closure-compare", "outcome": "Simulated closure", "transactions": [transaction(row, index) for index, (_, row) in enumerate(closure[:5], 1)]},
            {"id": "sim-closure-ach-sequence", "outcome": "Simulated closure", "transactions": [transaction(row, index) for index, (_, row) in enumerate(closure, 1)]},
            {"id": "sim-closure-card-sequence", "outcome": "Simulated closure", "transactions": [transaction(row, index) for index, (_, row) in enumerate(card_closure, 1)]},
        ],
    }
    payload["artifact_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def write_artifact(source: Path, source_manifest_path: Path, distribution_path: Path, output: Path) -> dict[str, Any]:
    artifact = build_artifact(source, load_json(source_manifest_path), load_json(distribution_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(artifact) + b"\n")
    return artifact


def record_source_manifest(source: Path, retrieved_at: str, source_ref: str) -> dict[str, Any]:
    datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    rows = source_rows(source)
    next(rows, None)
    return {"schema": "signal-ledger-source-manifest/v1", "verification_status": "verified", "provider": "IBM / Erik Altman", "dataset": "IBM Transactions for Anti Money Laundering (AML)", "dataset_version": 8, "source_ref": source_ref, "retrieved_at": retrieved_at, "source_file": source.name, "source_sha256": sha256_file(source), "source_schema": list(REQUIRED_COLUMNS), "license": LICENSE, "license_url": LICENSE_URL}


def approved_public_artifact(path: Path) -> dict[str, Any]:
    artifact = load_json(path)
    provenance = artifact.get("provenance", {})
    if artifact.get("artifact_schema") != ARTIFACT_SCHEMA or provenance.get("distribution", {}).get("status") != "approved":
        raise ValueError("Public fixture is not an approved Signal Ledger replay artifact.")
    unsigned = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if artifact.get("artifact_sha256") != hashlib.sha256(canonical_bytes(unsigned)).hexdigest():
        raise ValueError("Public fixture checksum does not match its content.")
    return artifact
