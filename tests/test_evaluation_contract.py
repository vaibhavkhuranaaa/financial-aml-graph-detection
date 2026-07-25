from copy import deepcopy
from pathlib import Path

import pytest

from src.pipeline.evaluation_contract import (
    EVALUATION_SCHEMA,
    validate_evaluation_files,
    validate_report,
)


def manifest() -> dict:
    return {
        "schema": EVALUATION_SCHEMA,
        "scope": "local-only",
        "source": {
            "dataset": "Elliptic",
            "path": "/private/local-research/elliptic.csv",
            "access_terms_ref": "local-recorded-access-terms",
            "retrieved_at": "2026-07-24T00:00:00Z",
            "source_sha256": "a" * 64,
        },
        "split": {
            "strategy": "chronological",
            "time_field": "timestep",
            "train_max_timestep": 34,
            "holdout_min_timestep": 35,
        },
        "unknown_label_policy": "excluded-from-supervised-metrics",
        "models": [
            {
                "family": "baseline",
                "model_id": "local-baseline",
                "code_version": "abc1234",
            },
            {"family": "gnn", "model_id": "local-gnn", "code_version": "abc1234"},
        ],
        "publication": {"status": "local-only", "public_approval": False},
    }


def report() -> dict:
    metrics = {
        "pr_auc": 0.2,
        "precision": {"at_10": 0.1},
        "recall": {"at_10": 0.1},
        "calibration": {"ece": 0.1},
        "review_capacity": {"reviews": 10},
        "operational_errors": ["aggregate-only analysis"],
    }
    return {
        "schema": EVALUATION_SCHEMA,
        "scope": "local-only",
        "source_sha256": "a" * 64,
        "generated_at": "2026-07-24T01:00:00Z",
        "publication": {"status": "local-only", "public_approval": False},
        "unknown_label_treatment": "excluded-from-supervised-metrics",
        "model_results": [
            {"family": "baseline", "metrics": metrics},
            {"family": "gnn", "metrics": deepcopy(metrics)},
        ],
    }


def test_local_evaluation_contract_accepts_aggregate_evidence() -> None:
    validate_report(report(), manifest())


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["split"].update({"holdout_min_timestep": 34}),
            "Chronological",
        ),
        (
            lambda value: value.update(
                {"publication": {"status": "public", "public_approval": True}}
            ),
            "public",
        ),
        (lambda value: value["models"].pop(), "baseline and one GNN"),
    ],
)
def test_manifest_rejects_missing_local_only_controls(mutate, message: str) -> None:
    bad_manifest = manifest()
    mutate(bad_manifest)
    with pytest.raises(ValueError, match=message):
        validate_report(report(), bad_manifest)


def test_report_rejects_raw_identifiers_and_missing_metrics() -> None:
    bad_report = report()
    bad_report["transaction_id"] = "local-only-but-not-aggregate"
    with pytest.raises(ValueError, match="identifiers"):
        validate_report(bad_report, manifest())
    bad_report = report()
    del bad_report["model_results"][0]["metrics"]["calibration"]
    with pytest.raises(ValueError, match="PR-AUC"):
        validate_report(bad_report, manifest())


def test_validator_rejects_public_delivery_paths(tmp_path: Path) -> None:
    public_path = tmp_path / "docs"
    public_path.mkdir()
    manifest_path = public_path / "manifest.json"
    report_path = public_path / "report.json"
    manifest_path.write_text("{}", encoding="utf-8")
    report_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="public delivery path"):
        validate_evaluation_files(manifest_path, report_path, tmp_path)
