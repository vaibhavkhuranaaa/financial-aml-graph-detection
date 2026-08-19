# Data governance

## Public experience

The public workbench may serve only a checksum validated, explicitly approved
replay artifact. It is **realistic synthetic banking data**, never anonymised
customer data. Browser visits do not train, fit, or invoke a model. The API
serves the approved bounded artifact only; the full source remains local only.

## IBM AML-Data provenance and publication decision

- Independent source check refreshed on 2026-08-17: the Kaggle dataset
  `ealtman2019/ibm-transactions-for-anti-money-laundering-aml`, version 8, names
  Erik Altman as creator, lists `HI-Small_Trans.csv`, and identifies the
  Community Data License Agreement, Sharing, Version 1.0.
- IBM's [AML-Data repository](https://github.com/IBM/AML-Data) states that the
  data itself is CDLA-Sharing-1.0 and that the virtual world people and companies
  are synthetic, not obfuscated or anonymised real individuals.
- The governing [CDLA-Sharing-1.0 text](https://cdla.dev/sharing-1-0/) treats a
  selected and pseudonymised subset as Enhanced Data. Publication must use the
  agreement, carry a prominent modification notice, retain available provider
  attribution, and provide the agreement text or a reliable hyperlink.
- The exact local v8 input was retrieved and verified on 2026-07-25 UTC. Its
  published header contains positional duplicate `Account` fields, which the
  pipeline records and maps internally to from and to accounts.
- The owner approved the exact verified source checksum for the bounded Signal
  Ledger replay scope. Public provenance manifests and the fixture carry the
  source and artifact identities needed for deterministic admission. Private
  delivery records retain the acquisition and re-verification evidence.

The offline builder records source metadata, retrieval timestamp, source
checksum, schema, deterministic selection rule, pseudonymisation method, pipeline
run identifier, and output checksum. The public admission check rejects a missing
or changed checksum, an unverified source manifest, an unapproved distribution
decision, or a tampered artifact.

## Selecting a different variant

IBM AML-Data v8 ships six variants. Any variant other than the currently approved
HI-Small requires its own verified source manifest and its own recorded
distribution decision before a single row of it reaches a public surface. An
approval granted for one source checksum never carries over to another file.

`LI-Small_Trans.csv` is retrieved and verified for local use. Its source manifest
is `data/provenance/ibm_aml_data_v8_li_small_source.json` and its checksum was
re-verified against that manifest immediately before the prevalence sensitivity
run. It carries **no distribution decision and requires none**, because no row of
it, and no artifact derived from it, reaches the public API, the deployed
fixture, or this repository. Its alert store, feature table and run records are
written under `data/li-small/`, which is gitignored. Publishing anything drawn
from LI-Small would require its own distribution decision first.

## The triage artifact, requested and not approved

The triage workbench needs a larger selection of HI-Small than the approved
replay artifact covers: one review period of the alert store carried whole, with
each alert's pseudonymised subject, its computed trigger quantities, a bounded
sample of its contributing transactions, its position under every ordering, and
its simulated outcome. The approved decision on file covers bounded replay
artifacts of 55 transactions across six cases, and an approval granted for one
scope never carries over to another.

`data/provenance/ibm_aml_data_v8_triage_distribution.json` records the decision:
the scope, why it needs its own decision, the conditions publication carries, and
the owner approval against the exact verified source checksum. Its
`public_distribution_status` is `approved`, so an artifact built from it carries
`approved` and the public service serves it, under CDLA-Sharing-1.0 with the
modification and pseudonymisation notice the conditions require.

Approval alone does not admit a file. The public mode also requires the artifact
to be the pinned release named by `APPROVED_TRIAGE_ARTIFACT_SHA256` in
`src/app.py`, because the approval is a statement about a source and any rebuild
reading that source would inherit the flag. `APP_MODE=local-triage-workbench`
drops the pin and keeps every other check, which is what lets an operator run an
artifact they just built.

The approval names one review period of the HI-Small variant. It does not extend
to another period, to the LI-Small variant, to the alert store, to the feature
table, or to the tuned rule parameter values.

Two disclosure rules apply to that artifact whether or not it is ever published.
Account identifiers are pseudonymised by the same function the replay artifact
uses, and the tuned rule parameter values are not carried at all: only the
computed quantities that met a trigger are published, filtered by a per rule
allowlist so a parameter added later is dropped by default rather than carried by
default. The catalogue describes each parameter by name, unit and direction of
effect instead.

## Local research boundary

Research data is local only. Before use, record the source, permitted use, file
checksum and retrieval date. Do not commit benchmark files, derived raw rows,
identifiers, or API responses, and do not serve or raw display them. Local
evaluation must preserve chronological splitting, handle unknown labels
explicitly, and report precision and recall plus operational errors rather than
accuracy alone.

Two earlier research paths, a UCI BitcoinHeist evaluation and a local Elliptic
evaluation, were closed and removed from this repository. Their raw inputs,
derived artifacts and reports were never public and are not part of this project.

## Claims boundary

The public replay is complete. It is neither a compliance product nor evidence
of illicit activity, real world effectiveness, or benchmark performance.
Versioned evidence and explicit owner approval remain required before expanding
the public data scope.
