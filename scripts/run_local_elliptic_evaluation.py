"""Run a local-only chronological Elliptic baseline/GNN comparison.

The command deliberately writes only aggregate manifest/report evidence to an
external local directory. It never writes raw rows, identifiers, embeddings,
predictions, or model checkpoints into this repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.evaluation_contract import EVALUATION_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "elliptic_txs_classes.csv",
    "elliptic_txs_edgelist.csv",
    "elliptic_txs_features.csv",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_only(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return resolved
    raise ValueError("Local evaluation inputs and outputs must be outside the repository.")


def combined_source_sha256(source_dir: Path) -> str:
    parts = [f"{name}:{sha256_file(source_dir / name)}" for name in REQUIRED_FILES]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def load_dataset(source_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    classes_path = source_dir / "elliptic_txs_classes.csv"
    features_path = source_dir / "elliptic_txs_features.csv"
    edges_path = source_dir / "elliptic_txs_edgelist.csv"
    labels: dict[str, str] = {}
    with classes_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            labels[row["txId"]] = row["class"]

    identifiers: list[str] = []
    times: list[int] = []
    feature_rows: list[list[float]] = []
    with features_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            identifiers.append(row[0])
            times.append(int(float(row[1])))
            feature_rows.append([float(value) for value in row[2:]])
    index = {identifier: position for position, identifier in enumerate(identifiers)}
    label_values = np.array(
        [-1 if labels.get(identifier) == "unknown" else int(labels[identifier] == "1") for identifier in identifiers],
        dtype=np.int64,
    )
    edge_pairs: list[tuple[int, int]] = []
    with edges_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source = index.get(row["txId1"])
            target = index.get(row["txId2"])
            if source is not None and target is not None:
                edge_pairs.extend(((source, target), (target, source)))
    edge_array = np.asarray(edge_pairs, dtype=np.int64).T
    return (
        np.asarray(feature_rows, dtype=np.float32),
        np.asarray(times, dtype=np.int64),
        label_values,
        edge_array,
    )


def fit_probabilities(features: torch.Tensor, labels: torch.Tensor, train_index: torch.Tensor) -> torch.Tensor:
    model = torch.nn.Linear(features.shape[1], 1)
    positives = labels[train_index].sum().item()
    negatives = train_index.numel() - positives
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(negatives / positives))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=1e-4)
    for _ in range(120):
        optimizer.zero_grad()
        logits = model(features[train_index]).squeeze(1)
        loss = loss_fn(logits, labels[train_index].float())
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        return torch.sigmoid(model(features).squeeze(1))


def one_hop_mean(features: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
    source, target = edge_index
    aggregate = torch.zeros_like(features)
    aggregate.index_add_(0, target, features[source])
    degree = torch.zeros(features.shape[0], dtype=features.dtype)
    degree.index_add_(0, target, torch.ones_like(target, dtype=features.dtype))
    return aggregate / degree.clamp_min(1).unsqueeze(1)


def pr_auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    ordering = np.argsort(-probabilities)
    ordered = labels[ordering]
    positives = max(int(ordered.sum()), 1)
    true_positive = np.cumsum(ordered)
    precision = true_positive / np.arange(1, len(ordered) + 1)
    recall = true_positive / positives
    return float(np.trapezoid(precision, recall))


def metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    predicted = probabilities >= 0.5
    true_positive = int(np.logical_and(predicted, labels == 1).sum())
    false_positive = int(np.logical_and(predicted, labels == 0).sum())
    false_negative = int(np.logical_and(~predicted, labels == 1).sum())
    true_negative = int(np.logical_and(~predicted, labels == 0).sum())
    top_k = min(100, len(labels))
    top_labels = labels[np.argsort(-probabilities)[:top_k]]
    return {
        "pr_auc": pr_auc(labels, probabilities),
        "precision": true_positive / max(true_positive + false_positive, 1),
        "recall": true_positive / max(true_positive + false_negative, 1),
        "calibration": {"brier_score": float(np.mean((probabilities - labels) ** 2))},
        "review_capacity": {
            "top_k": top_k,
            "precision_at_top_k": float(top_labels.mean()) if top_k else 0.0,
            "true_positives_at_top_k": int(top_labels.sum()),
        },
        "operational_errors": {
            "threshold": 0.5,
            "false_positives": false_positive,
            "false_negatives": false_negative,
            "true_positives": true_positive,
            "true_negatives": true_negative,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-max-timestep", type=int, default=34)
    parser.add_argument("--holdout-min-timestep", type=int, default=35)
    args = parser.parse_args()
    source_dir = local_only(args.source_dir)
    output_dir = local_only(args.output_dir)
    if args.train_max_timestep >= args.holdout_min_timestep:
        parser.error("The holdout timestep must begin after the training window.")
    if any(not (source_dir / name).is_file() for name in REQUIRED_FILES):
        parser.error("Source directory does not contain the required Elliptic CSV files.")

    features_np, timesteps, labels_np, edges_np = load_dataset(source_dir)
    known = labels_np >= 0
    train_mask = np.logical_and(known, timesteps <= args.train_max_timestep)
    holdout_mask = np.logical_and(known, timesteps >= args.holdout_min_timestep)
    if not train_mask.any() or not holdout_mask.any():
        parser.error("Chronological split has no known-label training or holdout examples.")
    torch.manual_seed(7)
    features = torch.from_numpy(features_np)
    train_index = torch.from_numpy(np.flatnonzero(train_mask))
    labels = torch.from_numpy(labels_np)
    mean = features[train_index].mean(dim=0)
    std = features[train_index].std(dim=0).clamp_min(1e-6)
    standardized = (features - mean) / std
    baseline = fit_probabilities(standardized, labels, train_index)
    graph_features = torch.cat((standardized, one_hop_mean(standardized, torch.from_numpy(edges_np))), dim=1)
    graph = fit_probabilities(graph_features, labels, train_index)
    holdout_index = np.flatnonzero(holdout_mask)
    holdout_labels = labels_np[holdout_index]
    source_sha256 = combined_source_sha256(source_dir)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema": EVALUATION_SCHEMA,
        "scope": "local-only",
        "source": {
            "dataset": "Elliptic",
            "path": str(source_dir),
            "access_terms_ref": "https://www.kaggle.com/datasets/ellipticco/elliptic-data-set (CC BY-NC-ND 4.0; local non-commercial research only)",
            "retrieved_at": now,
            "source_sha256": source_sha256,
        },
        "split": {
            "strategy": "chronological",
            "time_field": "time_step",
            "train_max_timestep": args.train_max_timestep,
            "holdout_min_timestep": args.holdout_min_timestep,
        },
        "unknown_label_policy": "excluded-from-supervised-metrics",
        "models": [
            {"family": "baseline", "model_id": "torch-logistic-regression/v1", "code_version": "local-runner/v1"},
            {"family": "gnn", "model_id": "one-hop-mean-message-passing-linear/v1", "code_version": "local-runner/v1"},
        ],
        "publication": {"status": "local-only", "public_approval": False},
    }
    report = {
        "schema": EVALUATION_SCHEMA,
        "scope": "local-only",
        "source_sha256": source_sha256,
        "generated_at": now,
        "publication": {"status": "local-only", "public_approval": False},
        "unknown_label_treatment": "excluded-from-supervised-metrics",
        "model_results": [
            {"family": "baseline", "model_id": "torch-logistic-regression/v1", "metrics": metrics(holdout_labels, baseline[holdout_index].detach().numpy())},
            {"family": "gnn", "model_id": "one-hop-mean-message-passing-linear/v1", "metrics": metrics(holdout_labels, graph[holdout_index].detach().numpy())},
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output_dir / "evaluation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote local-only aggregate evidence to {output_dir}")


if __name__ == "__main__":
    main()
