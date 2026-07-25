# Data governance

## Public experience

The public workbench may serve only a checksum-validated, explicitly approved
replay artifact. It is **realistic synthetic banking data**, never anonymized
customer data. Browser visits do not train, fit, or invoke a model. The API is
currently fail-closed: the legacy fixture is not admitted because the local
IBM input required to independently reproduce its recorded checksum is absent.

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
- Therefore `data/provenance/ibm_aml_data_v8_distribution.json` records a
  **blocked** decision. It cannot be changed to approved until the exact local
  v8 file is available, its SHA-256 and schema are recorded by the pipeline,
  and the owner approves the corresponding public artifact.

The offline builder records source metadata, retrieval timestamp, source
checksum, schema, deterministic selection rule, pseudonymization method,
pipeline run ID, and output checksum. The public admission check rejects a
missing or changed checksum, an unverified source manifest, an unapproved
distribution decision, or a tampered artifact.

## Local research boundary

The Elliptic benchmark is research-only and local-only. Before use, record the source, permitted use, file checksum, and retrieval date. Do not commit benchmark files, derived raw rows, identifiers, or API responses; do not serve or raw-display them. Local evaluation must preserve chronological splitting, explicitly handle unknown labels, and report precision/recall plus operational errors rather than accuracy alone.

## Claims boundary

This project is building. The synthetic workbench is neither a deployed compliance product nor evidence of illicit activity, real-world effectiveness, or benchmark performance. Versioned local evidence is required before publishing any research evaluation statement.
