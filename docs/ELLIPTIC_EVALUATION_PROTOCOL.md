# Local-only Elliptic evaluation protocol

This protocol governs local Elliptic research runs, including the completed
aggregate-only run summarized in `docs/ELLIPTIC_EVALUATION_SUMMARY.md`. It is
not a deployed capability or evidence about real-world activity. Do not commit
the Elliptic source, graph, model files, predictions, node/edge identifiers, or
full report; all remain local-only.

## Source gate

Before any run, create an untracked local JSON manifest using
`signal-ledger-local-evaluation/v1`. It must record the absolute local source
path, access-terms reference, retrieval timestamp, SHA-256, chronological
split boundary, explicit unknown-label treatment, a versioned baseline and GNN
identifier, and the fixed publication object:

```json
{"status":"local-only","public_approval":false}
```

The source path must be outside public delivery paths such as `data/fixtures`,
`data/provenance`, `frontend`, and `docs`. The source gate is incomplete unless
the access terms and checksum are independently recorded for the exact local
input.

## Required procedure

1. Build the transaction graph locally from the approved local input; do not
   serialize raw rows, identifiers, nodes, edges, or model artifacts into this
   repository.
2. Split chronologically: every training timestep must precede every holdout
   timestep. Record the time field and both boundaries in the manifest.
3. Explicitly choose one unknown-label policy: exclude unknown labels from
   supervised metrics, or report them separately. Use the same policy in the
   aggregate report.
4. Train and evaluate one versioned baseline and one versioned GNN candidate
   against the same split and policy. This protocol does not authorize a claim
   that either model is effective.
5. Produce aggregate-only local results for each model: PR-AUC, precision,
   recall, calibration, review-capacity analysis, and operational-error
   analysis. Accuracy alone is insufficient for this imbalanced task.
6. Validate the local manifest and report before treating them as reproducible
   evidence:

```bash
uv run python scripts/validate_local_evaluation.py \
  --manifest /absolute/local/path/evaluation-manifest.json \
  --report /absolute/local/path/evaluation-report.json
```

The validator rejects public delivery paths, missing source/access evidence,
non-chronological splits, absent baseline/GNN comparison, missing aggregate
metrics, public-approval status, raw/derived identifiers, and mismatched source
checksums.

## Claims and publication boundary

The validator confirms structural completeness only; it does not verify a
metric, model quality, or permitted publication. Raw/derived Elliptic data,
graphs, predictions, model artifacts, and any research claim remain prohibited
until independently verified and explicitly owner-approved. The current approval
is limited to the aggregate summary; it does not authorize public API metrics or
research artifacts.
