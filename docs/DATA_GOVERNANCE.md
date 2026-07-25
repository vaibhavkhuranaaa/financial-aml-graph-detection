# Data governance

## Public experience

The public workbench may serve only a checksum-validated, explicitly approved
replay artifact. It is **realistic synthetic banking data**, never anonymized
customer data. Browser visits do not train, fit, or invoke a model. The API
serves the approved bounded artifact only; the full source remains local-only.

## IBM AML-Data provenance and publication decision

- Independent source check on 2026-07-24: Kaggle dataset
  `ealtman2019/ibm-transactions-for-anti-money-laundering-aml`, version 8,
  names Erik Altman as creator, lists `HI-Small_Trans.csv`, and identifies
  `Community Data License Agreement - Sharing - Version 1.0`.
- IBM's [AML-Data repository](https://github.com/IBM/AML-Data) states that the
  data itself is CDLA-Sharing-1.0 and that the virtual-world people and
  companies are synthetic, not obfuscated or anonymized real individuals.
- The governing [CDLA-Sharing-1.0 text](https://cdla.dev/sharing-1-0/) treats a
  selected/pseudonymized subset as Enhanced Data. Publication must use the
  agreement, carry a prominent modification notice, retain available provider
  attribution, and provide the agreement text or a reliable hyperlink.
- The exact local v8 input was retrieved and verified on 2026-07-25 UTC. Its
  SHA-256 is `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`;
  its published header contains positional duplicate `Account` fields, which
  the pipeline records and maps internally to from/to accounts.
- The owner approved the exact verified source checksum on 2026-07-24 for the
  bounded Signal Ledger replay scope. The admitted artifact has content hash
  `62b1d7476466f5456f61ef0d019db52536cf13e46e584724d5346a9ad8b75db2` and
  pipeline run ID `d7bd5a14342256427d08604a6e7ce9d3f2ce60ff5e3b154298fffd8db6a31356`.

The offline builder records source metadata, retrieval timestamp, source
checksum, schema, deterministic selection rule, pseudonymization method,
pipeline run ID, and output checksum. The public admission check rejects a
missing or changed checksum, an unverified source manifest, an unapproved
distribution decision, or a tampered artifact.

## Local research boundary

The Elliptic benchmark is research-only and local-only. Before use, record the source, permitted use, file checksum, and retrieval date. Do not commit benchmark files, derived raw rows, identifiers, or API responses; do not serve or raw-display them. Local evaluation must preserve chronological splitting, explicitly handle unknown labels, and report precision/recall plus operational errors rather than accuracy alone.

## Claims boundary

This project is building. The synthetic workbench is neither a deployed compliance product nor evidence of illicit activity, real-world effectiveness, or benchmark performance. Versioned local evidence is required before publishing any research evaluation statement.
