# 0012 The triage slice is approved for one period, and the release is pinned

## Decision

**The owner recorded a distribution decision for the triage slice, and the desk
is published.** Decision 0009 withheld it, correctly, because an approval granted
for the bounded replay scope never carried to a larger selection of the same
source. That is now decided rather than assumed:
`data/provenance/ibm_aml_data_v8_triage_distribution.json` carries
`public_distribution_status` of `approved`, the approved source checksum, and an
owner approval block naming the scope. The artifact was rebuilt from the same
source, the same parameter set and the same pipeline run, and it changed in
exactly one respect: it now records the approval it was built under.

**The approval covers one review period of HI-Small and nothing else.** Not
another period, not the LI-Small variant, not the alert store, not the feature
table, and not the tuned rule parameter values. The scope is written into the
approval block rather than left to be inferred from what happened to be built,
because the failure mode this project keeps guarding against is an approval
quietly widening to cover whatever came next.

**Approval alone does not admit a file, so the release is pinned.** The
distribution decision approves a source checksum. Any rebuild that reads that
source inherits the approval flag, and the deployed function cannot see the
pipeline that produced the file it is handed, so approval by itself would let an
unreviewed rebuild serve itself on the strength of a flag it did not earn.
`APPROVED_TRIAGE_ARTIFACT_SHA256` in `src/app.py` names the exact release that
was reviewed, alongside the pin the replay artifact has always carried. In public
mode an artifact that does not match is refused with a 503, whether or not it is
approved.

Approval is a statement about a source. The pin is a statement about a build.
Collapsing the two is the mistake this record exists to prevent.

**The pin is public mode only.** `APP_MODE=local-triage-workbench` keeps the
schema check, the content checksum and every other admission check, and drops the
pin alone. A local workbench exists to run the artifact an operator just built,
and applying the release pin there would refuse the one thing the mode is for.
The publication gate and the release pin are now the two things that separate the
modes, and both are named in the response and in the runbook.

## What the publication carries

The artifact is published under CDLA-Sharing-1.0 with the conditions the
distribution decision records: the modification, selection and pseudonymisation
notice, retained IBM and Erik Altman attribution with the source hyperlink, the
licence text by reliable hyperlink, and computed trigger quantities only. Account
identifiers are pseudonymised by the same function the replay artifact uses. The
tuned rule parameter values are not carried at all; each parameter is described by
name, unit and direction of effect, and a test asserts both the names and their
distinctive values are absent from the whole payload.

Nothing measured changed. The published period holds 749 alerts and 30 true
positive alerts, the pipeline run identifier is unchanged, and the gate still
reads a lift of 1.2333 against a threshold of 1.3, unmet. **No model ships**
remains the result, and the surface still states it above the queue in the largest
type on the page.

## Consequences

The deployed URL now serves two artifacts rather than one, and the triage routes
return 200 where they returned 503. Every claim in `README.md`, `docs/scope.md`,
`docs/architecture.md`, `docs/DATA_GOVERNANCE.md`, `docs/CASE_STUDY.md` and
`docs/DELIVERY_PLAN.md` that described the desk as unpublished was rewritten in
the same change, because a governance document that lags the surface it describes
is worse than no document.

Decision 0009 is not superseded. It records why the surface was withheld, which
is the part worth keeping: the withholding was the correct default, and this
record is the approval that lifted it rather than a discovery that the concern
was unfounded.

The rebuild changes the artifact digest, so any future rebuild must update the pin
in `src/app.py` in the same change. A rebuild that does not is refused in public
mode with the artifact sitting right there, which is the intended failure and is
covered by a test.
