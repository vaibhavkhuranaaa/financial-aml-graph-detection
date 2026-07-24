# Data governance

## Public experience

The public workbench serves only `data/fixtures/public_casefile.json`: a deterministic, attributed IBM AML-Data v8 HI-Small slice. It is **realistic synthetic banking data**, not anonymized customer data. The fixture records retrieval date, CDLA-Sharing-1.0, IBM/Erik Altman attribution, source and slice SHA-256 values, and its selection method. Browser visits do not train, fit, or invoke a model. The API exposes two cases, a maximum of 18 timeline rows and 18 graph nodes.

## Local research boundary

The Elliptic benchmark is research-only and local-only. Before use, record the source, permitted use, file checksum, and retrieval date. Do not commit benchmark files, derived raw rows, identifiers, or API responses; do not serve or raw-display them. Local evaluation must preserve chronological splitting, explicitly handle unknown labels, and report precision/recall plus operational errors rather than accuracy alone.

## Claims boundary

This project is building. The synthetic workbench is neither a deployed compliance product nor evidence of illicit activity, real-world effectiveness, or benchmark performance. Versioned local evidence is required before publishing any research evaluation statement.
