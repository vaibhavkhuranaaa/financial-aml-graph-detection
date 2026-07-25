# Aggregate Elliptic evaluation summary

The owner approved publication of this aggregate-only portfolio summary on
2026-07-25. It is not a deployment claim, compliance claim, or conclusion about
real-world activity. Raw data, identifiers, rows, graph structures,
predictions, embeddings, model files, and the full local report remain outside
this repository.

## Local research run

- Source: checksum-verified Elliptic dataset under the recorded CC BY-NC-ND 4.0
  local-research terms.
- Split: chronological; timesteps 1–34 for training and 35–49 for holdout.
- Unknown labels: excluded from supervised metrics.
- Compared models: PyTorch logistic-regression baseline and a one-hop mean
  message-passing linear classifier. Both use the same feature input and split.

## Aggregate holdout findings

| Model | PR-AUC | Precision at 0.5 | Recall at 0.5 | Brier score | Precision at top 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic baseline | 0.345 | 0.139 | 0.953 | 0.277 | 0.570 |
| One-hop message passing | 0.381 | 0.151 | 0.847 | 0.220 | 0.430 |

The message-passing candidate has higher PR-AUC and a lower Brier score in this
single local run. At the fixed 0.5 threshold it trades recall for fewer false
positives; at the fixed top-100 review capacity it returns fewer positives than
the baseline. These are research observations, not a recommendation to deploy,
select a threshold, or make a compliance decision.

The machine-readable local manifest/report passed
`scripts/validate_local_evaluation.py`; it remains untracked in external local
storage. Reproduce only with the permitted local source, a local PyTorch runtime,
and `scripts/run_local_elliptic_evaluation.py`.
