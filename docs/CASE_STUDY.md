# Signal Ledger technical case study

Signal Ledger demonstrates a bounded research workflow: timeline → topology → precomputed research context → simulated human decision → browser-memory audit note. It is not a production system, compliance recommendation, or statement about a real entity.

The public fixture is a deterministic IBM AML-Data v8 HI-Small slice under
CDLA-Sharing-1.0. It is realistic synthetic banking data, not anonymized
customer data. The owner-approved artifact records IBM/Erik Altman attribution,
retrieval date, source checksum, schema, output checksum, and a deterministic
selection/pseudonymization rule. The full source is local-only and is not
delivered to browsers.

The FastAPI API limits case catalogue, timeline, and topology responses; it has
no local Elliptic route. Illustrative ordering and explanations are precomputed.
The versioned local Elliptic run uses provenance gating, a chronological split,
unknown-label exclusion, baseline/message-passing comparison, PR-AUC,
precision/recall, calibration, review-capacity analysis, and operational-error
analysis. Only its owner-approved aggregate summary is public; all raw and
derived research artifacts remain local-only.

With a verified local v8 input, record a source manifest with
`uv run python scripts/build_public_replay.py --source <local HI-Small_Trans.csv> --record-manifest <local-source.json> --retrieved-at <ISO-8601 timestamp>`.
After the owner records an approved decision for that exact source checksum,
materialize with `--source-manifest <local-source.json> --distribution-decision <approved-decision.json> --output data/fixtures/public_casefile.json`.
