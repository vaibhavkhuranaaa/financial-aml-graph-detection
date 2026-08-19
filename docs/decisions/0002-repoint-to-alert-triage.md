# 0002 Repoint Signal Ledger at alert triage

## Decision

Signal Ledger becomes an anti money laundering alert triage workbench on IBM
AML-Data v8.

The stakeholder is an investigation lead with a fixed number of analyst review
hours per week. The decision the product supports is which alerts get worked this
week and in what order. The project writes its own Bank Secrecy Act typology
rules engine to generate the alert population, so rules only alert volume and per
typology recall is the baseline any ranker has to beat. The headline metric is
false positive reduction at held typology recall, reported in alerts and in
analyst hours.

The model reorders the queue. It never suppresses an alert.

## Why

Transaction monitoring runs at a 90 to 98 percent false positive rate, and
roughly 1 to 5 percent of alerts become a suspicious activity report. The cost
and the buying decision both sit in review capacity, not in novel detection. A
project that claims to find laundering answers a question the function does not
ask. A project that reports how much review volume can be dropped at held
typology recall answers the one that gets budget.

Writing the rules engine, rather than borrowing an alert population, does two
things. It makes the baseline a real baseline instead of a strawman, and it
removes the failure mode that ended the previous path, because the study
population is now a function of code the project controls and can always be
generated.

## Alternatives rejected

**Continue the UCI BitcoinHeist research path.** Tried and measured, not assumed.
Both evaluated candidates ranked below holdout prevalence on PR-AUC, so no
product existed on that data and no amount of tuning would create one. The
business framing was also wrong before the model was: the stated stakeholder was
a fiat anti money laundering investigation lead while the data was Bitcoin
ransomware address attribution. Release was NO GO. That work is complete,
archived privately, and closed.

**Continue the local Elliptic evaluation.** Same structural problem in a milder
form. It is a labelled benchmark exercise, not a product decision, and its
licence forbids redistribution, so nothing from it could reach a public surface
beyond an aggregate summary. Archived with the BitcoinHeist work.

**Fit a classifier to the IBM laundering flag directly.** This is what almost
every portfolio project in this domain does. It answers no question a financial
crime team asks, because the labels come from the same generator as the features,
and it produces an area under a curve that no stakeholder can act on.

**Rank raw transactions rather than alerts.** Rejected because the unit an
analyst opens is the alert. A transaction level score has to be re-aggregated
into an alert ordering anyway, which breaks the link between the score and the
thing a human acts on.

**Let the model suppress low ranked alerts.** This is where the savings look
biggest and it is rejected anyway. A model that closes alerts without human
review has to be defended to a regulator on the day it is wrong. Reordering under
a fixed hour budget carries the same capacity argument and loses nothing, because
an alert pushed into next week is still an alert.

**Claim the data engineer role alongside data scientist.** Rejected. The sibling
project `shell-company-network-risk` carries that role with a no streaming
deviation, and claiming the same role here with the same deviation would weaken
both. A Small variant of AML-Data is one file on one machine with no ingestion
contract surface. Revisited only if a Large variant is selected.

## Not done

The rules engine, the alert store, the feature build, the ranker and the backtest
harness are specified and not built. No dataset variant has been selected; that
decision belongs to phase P2. No metric in this repository has a result.

The deployed workbench was not rebuilt. It continues to serve the bounded replay
fixture it served before this decision, and the README marks the triage product
as in progress rather than claiming it.

The public history begins with the reviewed release. Delivery notes and local
workspace configuration stay outside the repository.

## Changed

Public source and private delivery records now have separate ownership boundaries.

The BitcoinHeist and Elliptic code, tests, documents, evidence and superseded
records were archived privately with no public trace. One gigabyte of raw data
was deleted after its source, DOI, checksums, row counts and exact re-acquisition
commands were recorded.

`README.md` was rewritten to the template shape and describes what exists today.
`docs/` was rebuilt: `architecture.md`, `scope.md`, `data-dictionary.md` and
`metric-glossary.md` now describe the triage product and mark every unmeasured
number as unmeasured.

Orphaned bytecode, stale build output, an outdated vendored copy of the delivery
kit, and empty placeholder directories were removed. `.vercelignore` now excludes
build artifacts and frontend dependencies so the deployment upload cannot
regress.
