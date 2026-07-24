# Data governance

## Public experience

The public workbench serves only `data/fixtures/public_casefile.json`. It is authored synthetic data, has no real entities, and contains precomputed illustrative research scores. Browser visits do not train, fit, or invoke a model. The API exposes a maximum of 12 queue entries and 18 graph nodes.

## Local research boundary

The Elliptic benchmark is research-only and local-only. Before use, record the source, permitted use, file checksum, and retrieval date. Do not commit benchmark files, derived raw rows, identifiers, or API responses; do not serve or raw-display them. Local evaluation must preserve chronological splitting, explicitly handle unknown labels, and report precision/recall plus operational errors rather than accuracy alone.

## Claims boundary

This project is building. The synthetic workbench is neither a deployed compliance product nor evidence of illicit activity, real-world effectiveness, or benchmark performance. Versioned local evidence is required before publishing any research evaluation statement.
