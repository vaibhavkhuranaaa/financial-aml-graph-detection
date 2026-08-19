# 0009 The triage surface exists, and it is local until the owner approves it

## Decision

**The triage workbench is built and it is not published.** The queue view, the
capacity control, the cut line, the ordering switch, the alert detail and both
new honest states all exist and run against a real review period. They run on a
local analyst workbench. The deployed public surface continues to serve the
approved six case replay artifact and nothing else, and it refuses the triage
artifact outright.

The reason is governance, not readiness. `docs/DATA_GOVERNANCE.md` requires an
owner recorded distribution decision against an exact source checksum before a
row reaches a public URL, and the approval on file covers *bounded replay
artifacts*: 55 transactions across six cases. The triage artifact is a different
and much larger selection of the same source, and an approval granted for one
scope never carries over to another. There is no owner decision for the triage
scope, so there is no publication.

**The service gained one application mode and no bypass.** `APP_MODE` accepts
`local-triage-workbench` alongside `public-synthetic-fixture`. The local mode
changes exactly one thing: the triage artifact is admitted without an approved
distribution decision. Every other check still runs, including the schema check
and the content checksum, and the replay artifact's own admission check is
untouched. Every triage response carries a `delivery` block stating which mode
served it, and the surface renders that statement above the queue rather than in
a footnote.

**The publication request is recorded rather than assumed.**
`data/provenance/ibm_aml_data_v8_triage_distribution.json` states the scope
requested, why it needs its own decision, the conditions publication would carry,
and a `blocker` saying plainly that the owner has not approved it. Its
`public_distribution_status` is `pending_owner_approval`, so the artifact built
from it carries `not approved` and the public service refuses it. Approving the
triage surface is one edit to that file by its owner, followed by a rebuild and a
pinned release digest.

## Why

**The capacity control is the product, so it needs a real denominator.** The
artifact carries one review period whole, 749 alerts of 2022-09-07, rather than a
sample. A sampled queue would make every number on the consequence block a
fiction: the share of the period included, the count not reached, and the depth at
which a typology loses coverage are all statements about a denominator, and a
truncated denominator would flatter all three. The period is the bound; within it
nothing is removed.

**The cut line is drawn and nothing below it is hidden.** The queue endpoint
returns every alert in the period in the chosen ordering, and the interface draws
a ruled separator at the current depth. Alerts below it stay at full contrast,
keep their disposition control, and open to the same detail view as anything
above it. A queue endpoint that returned only the worked head would have made the
constraint unrenderable, which is why the bound lives in the artifact and not in
the response.

**Rank carries no colour and the test says so.** The rank cell is monospace,
right aligned and painted in the body text colour, with no bar, no heat scale and
no gradient anywhere in the queue. A colour scale invites rank to be read as a
probability or a severity and it is neither. There is a stylesheet test asserting
the rank rule paints no background and no gradient, and a browser check asserting
every rank cell computes to one colour, because this is the kind of rule that
gets undone by a well meaning later edit.

**Both honest states render at full weight.** The measured result sits above the
queue in the largest type on the surface: "The baseline holds. No model ships,"
with the lift, its interval, the reference rung and the gate beside it. The five
rules the simulator generates no counterpart for carry a structural zero with
their reason and their alert volume on the same row, because that volume is a
real analyst cost and it is the finding. Neither is behind a disclosure and
neither is in smaller type than a win would have been.

**A typology the rules missed is marked differently from a structural zero.**
Three typologies in the published period have live attempts and no surfaced ones.
That is the rules engine missing them, not the simulator failing to generate
them, and rendering both in the same treatment would have collapsed two different
statements into one. They are marked separately and the copy under the table says
which is which.

**The tuned trigger values do not leave the builder.** Every rule writes both the
quantities that met its trigger and the parameters that set it into one evidence
blob. The published quantity list is an allowlist per rule, so a parameter added
later is dropped by default rather than carried by default, and a test asserts
that no parameter name and none of the distinctive tuned values appear anywhere
in the payload. The catalogue describes each parameter by name, unit and
direction of effect instead, which is what `spec.md` section 5 permits and what
keeps the method view from reading as an evasion guide.

**The explanation is the model's own arithmetic.** Ranking contributions come
from LightGBM's exact per feature contributions rather than a story told about
the model afterwards. On a baseline ordering the section does not disappear: it
names the baseline and what it sorted on, because the comparison is the point of
the surface and a missing section reads as a missing feature.

**Nothing is computed at request time and the import graph enforces it.** Every
ordering, trigger quantity and contribution is written offline, once. The
admission check the service calls lives in `src/triage_artifact.py`, which imports
nothing from `src/pipeline/`, so the deployed function cannot gain Polars or
LightGBM by importing a checksum check. The browser does arithmetic over a fixed
table; it never asks for a score and it never writes.

## Alternatives rejected

**Publish the triage artifact under the existing distribution decision.** The
existing decision approves bounded replay artifacts derived from the verified
HI-Small checksum. Reading "bounded" as covering a 749 alert period with its
transactions would be stretching an approval to cover a scope its author did not
see, which is the failure mode the whole governance section exists to prevent.

**Ask for approval by building an approved artifact and letting the owner object.**
Building the artifact with `public_distribution_status: approved` would have made
the surface publishable by default and turned the owner's decision into a veto
they have to notice. The decision file is a request, and it says so.

**Serve a smaller triage slice that fits the existing approval.** A slice small
enough to be uncontroversial would be too small to carry the capacity argument,
because the argument is about what a fixed analyst budget does to a real period's
volume. A demonstration on 55 transactions would be a screenshot of the idea
rather than the thing.

**Keep one application mode and gate on the artifact alone.** Then either the
public service serves an unapproved artifact when one is present on disk, or the
local workbench cannot run at all. The mode makes the difference explicit,
auditable in one place, and testable: there is a test asserting the public mode
refuses the artifact and another asserting the local mode serves it and says it
is unpublished.

**Fold the triage surface into the replay workbench's existing sections.** The
replay workbench asks a visitor to understand a case. The triage workbench asks
them to make an allocation decision under a constraint and to see what it gives
up. They are different tasks and the second one is the product, so it sits above
the first with its own claims line rather than being threaded through it.

## Not done

No publication, no owner approval, and no change to the deployed artifact, its
pinned digest or its pipeline run identifier. The public deployment is unchanged
by this milestone.

No filters. Filtering the queue by typology, by period and by disposition status
is in the design language's product behaviour list and is not in this milestone's
acceptance line. The queue is one period, so the period filter has nothing to
select between until a second period is published.

No local export of the triage review record. The replay workbench's export is
untouched; the triage dispositions are browser private and are not exportable
yet.

No second review period, and no LI-Small triage artifact. The builder takes the
period as an argument and would produce either.

No change to the rules engine, the alert store, the feature build, the backtest
harness, the ranker or any measured number. The model retrained here uses the
same `training_frame` every measured number went through, on periods strictly
before the published one, so the queue on the surface is the queue that was
scored.

## Changed

`src/pipeline/triage.py` builds the artifact, `scripts/build_triage_artifact.py`
runs it, and `src/triage_artifact.py` holds the admission check on the serving
path. `src/contracts.py` gains the triage response contracts and `src/app.py`
gains three GET routes and the second application mode.
`frontend/src/triage.tsx` and `frontend/src/styles.css` carry the desk.
`tests/test_triage.py` is new, and `tests/test_app.py`,
`tests/test_runtime_config.py` and `tests/test_workbench_boundary.py` grew the
boundary assertions. `scripts/verify_triage_browser.sh` is the browser journey.
`data/provenance/ibm_aml_data_v8_triage_distribution.json` records the
publication request and its blocker. The artifact itself is written to
`data/fixtures/public_triage.json`, which is gitignored, because an unapproved
slice does not belong in the repository either.

## Superseded in part

The owner recorded a distribution decision for the triage slice on 2026-08-17 and
the surface is published. Decision record 0012 holds what the approval covers,
what it deliberately does not, and why an approved artifact is still refused
unless it is the pinned release.

This record stands as written. The withholding was the correct default and the
reasoning above is what made the approval a decision rather than a drift, so it
is amended rather than rewritten. Two statements in it are now out of date: the
artifact is tracked at `data/fixtures/public_triage.json` rather than gitignored,
and the public service serves the triage routes rather than returning 503 on them.
