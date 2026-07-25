"""Validation contract for local-only Elliptic evaluation evidence.

This module intentionally does not train, score, or serialize benchmark data.
It validates a local source manifest and an aggregate-only research report before
they can be treated as reproducible evidence.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

EVALUATION_SCHEMA = "signal-ledger-local-evaluation/v1"
REQUIRED_METRICS = {
    "pr_auc",
    "precision",
    "recall",
    "calibration",
    "review_capacity",
    "operational_errors",
}
REQUIRED_MODEL_FAMILIES = {"baseline", "gnn"}
FORBIDDEN_IDENTIFIER_KEYS = {
    "account",
    "address",
    "transaction_id",
    "node_id",
    "edge_id",
    "raw_rows",
    "predictions",
}
PUBLIC_PATH_SEGMENTS = {"data/fixtures", "data/provenance", "docs", "frontend"}
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("Evaluation evidence must be a JSON object.")
    return value


def _required(value: dict[str, Any], key: str) -> Any:
    if key not in value:
        raise ValueError(f"Evaluation evidence is missing required field: {key}.")
    return value[key]


def _timestamp(value: str, name: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 timestamp.") from error


def validate_local_path(path: Path, repository_root: Path) -> None:
    resolved = path.resolve()
    root = repository_root.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return
    if any(
        relative == segment or relative.startswith(f"{segment}/")
        for segment in PUBLIC_PATH_SEGMENTS
    ):
        raise ValueError(
            "Local evaluation evidence cannot be read from a public delivery path."
        )


def validate_source_manifest(manifest: dict[str, Any]) -> None:
    if _required(manifest, "schema") != EVALUATION_SCHEMA:
        raise ValueError("Source manifest does not use the local evaluation schema.")
    if _required(manifest, "scope") != "local-only":
        raise ValueError("Elliptic evaluation must remain local-only.")
    source = _required(manifest, "source")
    if not isinstance(source, dict):
        raise TypeError("Source manifest must include a source object.")
    for key in ("dataset", "path", "access_terms_ref", "retrieved_at", "source_sha256"):
        _required(source, key)
    if source["dataset"] != "Elliptic":
        raise ValueError(
            "Local evaluation contract is reserved for the Elliptic benchmark."
        )
    if not isinstance(source["path"], str) or not Path(source["path"]).is_absolute():
        raise ValueError(
            "Local source path must be absolute and must not be published."
        )
    if (
        not isinstance(source["access_terms_ref"], str)
        or not source["access_terms_ref"]
    ):
        raise ValueError("Source access terms reference is required.")
    if not isinstance(source["source_sha256"], str) or not SHA256.fullmatch(
        source["source_sha256"]
    ):
        raise ValueError("Source manifest must contain a SHA-256 checksum.")
    _timestamp(source["retrieved_at"], "Source retrieval time")

    split = _required(manifest, "split")
    if not isinstance(split, dict) or split.get("strategy") != "chronological":
        raise ValueError("Evaluation requires a chronological split.")
    for key in ("time_field", "train_max_timestep", "holdout_min_timestep"):
        _required(split, key)
    if split["train_max_timestep"] >= split["holdout_min_timestep"]:
        raise ValueError("Chronological holdout must begin after the training window.")
    if _required(manifest, "unknown_label_policy") not in {
        "excluded-from-supervised-metrics",
        "reported-separately",
    }:
        raise ValueError("Unknown-label treatment must be explicit.")

    models = _required(manifest, "models")
    if (
        not isinstance(models, list)
        or {item.get("family") for item in models if isinstance(item, dict)}
        != REQUIRED_MODEL_FAMILIES
    ):
        raise ValueError(
            "Evaluation manifest must declare one baseline and one GNN comparison."
        )
    if any(
        not item.get("model_id") or not item.get("code_version")
        for item in models
        if isinstance(item, dict)
    ):
        raise ValueError(
            "Each declared model needs a versioned identifier and code version."
        )
    publication = _required(manifest, "publication")
    if publication != {"status": "local-only", "public_approval": False}:
        raise ValueError("Evaluation evidence has not been approved for public use.")


def _contains_forbidden_identifier(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_IDENTIFIER_KEYS or _contains_forbidden_identifier(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_identifier(item) for item in value)
    return False


def validate_report(report: dict[str, Any], manifest: dict[str, Any]) -> None:
    validate_source_manifest(manifest)
    if (
        _required(report, "schema") != EVALUATION_SCHEMA
        or _required(report, "scope") != "local-only"
    ):
        raise ValueError(
            "Evaluation report must remain local-only under the versioned schema."
        )
    if _required(report, "source_sha256") != manifest["source"]["source_sha256"]:
        raise ValueError(
            "Evaluation report source checksum does not match the local source manifest."
        )
    if _required(report, "publication") != {
        "status": "local-only",
        "public_approval": False,
    }:
        raise ValueError("Evaluation report has not been approved for public use.")
    _timestamp(_required(report, "generated_at"), "Report generation time")
    if _contains_forbidden_identifier(report):
        raise ValueError(
            "Evaluation report contains raw or derived identifiers that cannot leave local research."
        )

    results = _required(report, "model_results")
    if (
        not isinstance(results, list)
        or {item.get("family") for item in results if isinstance(item, dict)}
        != REQUIRED_MODEL_FAMILIES
    ):
        raise ValueError("Evaluation report must compare one baseline and one GNN.")
    for result in results:
        if not isinstance(result, dict):
            raise TypeError("Model results must be objects.")
        metrics = _required(result, "metrics")
        if not isinstance(metrics, dict) or set(metrics) != REQUIRED_METRICS:
            raise ValueError(
                "Model results must include PR-AUC, precision, recall, calibration, review capacity, and operational errors."
            )
        if not all(
            isinstance(metrics[key], (int, float, dict, list))
            for key in REQUIRED_METRICS
        ):
            raise ValueError("Evaluation metrics must be aggregate values only.")
    if _required(report, "unknown_label_treatment") != manifest["unknown_label_policy"]:
        raise ValueError(
            "Report unknown-label treatment must match the local source manifest."
        )


def validate_evaluation_files(
    manifest_path: Path, report_path: Path, repository_root: Path
) -> None:
    validate_local_path(manifest_path, repository_root)
    validate_local_path(report_path, repository_root)
    validate_report(load_json(report_path), load_json(manifest_path))
