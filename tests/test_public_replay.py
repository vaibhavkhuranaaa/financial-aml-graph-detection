import csv
import json
from pathlib import Path

import pytest

from src.public_replay import (
    REQUIRED_COLUMNS,
    approved_public_artifact,
    record_source_manifest,
    write_artifact,
)


def write_source(path: Path) -> None:
    rows = []
    for index in range(16):
        rail = ("ACH", "Cheque", "Credit Card")[index % 3]
        rows.append([f"2022/09/01 00:{index:02d}", "1", "fanout", "2", f"target-{index}", "10", "US Dollar", "10", "US Dollar", rail, "1"])
    for index in range(8):
        rows.append([f"2022/09/02 00:{index:02d}", "1", f"normal-{index}", "2", f"receiver-{index}", "10", "US Dollar", "10", "US Dollar", "ACH", "0"])
        rows.append([f"2022/09/03 00:{index:02d}", "1", f"card-{index}", "2", f"card-receiver-{index}", "10", "US Dollar", "10", "US Dollar", "Credit Card", "0"])
        rows.append([f"2022/09/04 00:{index:02d}", "1", f"cash-{index}", "2", f"cash-target-{index}", "10", "US Dollar", "10", "US Dollar", "Cash", "1"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(REQUIRED_COLUMNS)
        writer.writerows(reversed(rows))


def test_replay_is_deterministic_and_bounded(tmp_path: Path) -> None:
    source = tmp_path / "HI-Small_Trans.csv"
    write_source(source)
    manifest = record_source_manifest(source, "2026-07-24T00:00:00Z", "https://example.invalid/versions/8")
    manifest_path = tmp_path / "source.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    decision = {"public_distribution_status": "approved", "dataset_version": 8, "license": "CDLA-Sharing-1.0", "approved_source_sha256": manifest["source_sha256"]}
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision), encoding="utf-8")
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    first_artifact = write_artifact(source, manifest_path, decision_path, first)
    second_artifact = write_artifact(source, manifest_path, decision_path, second)
    assert first.read_bytes() == second.read_bytes()
    assert first_artifact["artifact_sha256"] == second_artifact["artifact_sha256"]
    assert first_artifact["provenance"]["pipeline_run_id"] == second_artifact["provenance"]["pipeline_run_id"]
    assert [len(case["transactions"]) for case in first_artifact["cases"]] == [16, 8, 10, 5, 8, 8]
    public_transactions = [transaction for case in first_artifact["cases"] for transaction in case["transactions"]]
    assert all("fanout" not in transaction["from"] and "target-" not in transaction["to"] for transaction in public_transactions)
    assert approved_public_artifact(first)["artifact_sha256"] == first_artifact["artifact_sha256"]


def test_unverified_or_tampered_input_cannot_enter_public_path(tmp_path: Path) -> None:
    source = tmp_path / "HI-Small_Trans.csv"
    write_source(source)
    manifest = record_source_manifest(source, "2026-07-24T00:00:00Z", "https://example.invalid/versions/8")
    manifest_path = tmp_path / "source.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps({"public_distribution_status": "blocked"}), encoding="utf-8")
    with pytest.raises(ValueError, match="does not approve"):
        write_artifact(source, manifest_path, decision_path, tmp_path / "artifact.json")
    manifest["verification_status"] = "blocked"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="not verified"):
        write_artifact(source, manifest_path, decision_path, tmp_path / "artifact.json")
    blocked_artifact = approved_public_artifact(Path("data/fixtures/public_casefile.json"))
    blocked_artifact["provenance"]["distribution"]["status"] = "blocked"
    blocked_path = tmp_path / "blocked.json"
    blocked_path.write_text(json.dumps(blocked_artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="not an approved"):
        approved_public_artifact(blocked_path)


def test_legacy_generator_cannot_bypass_public_admission() -> None:
    legacy_generator = Path("scripts/generate_public_fixture.py").read_text(encoding="utf-8")
    assert "SOURCE_SHA256" not in legacy_generator
    assert "write_artifact" not in legacy_generator
