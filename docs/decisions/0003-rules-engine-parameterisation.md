# 0003 Parameterise the typology rules against alert volume, and four choices the data forced

## Decision

The rules engine implementing R1 through R8 is parameterised against a target
alert volume of 800 alerts per review period, with an accepted band of 640 to
960. The catalogue lands at 917.1 alerts per period. Parameters are never set
against the laundering flag, and the flag is absent from the loader's column
selection so no rule can read it.

Four further choices were forced by what the data turned out to be.

**Self transfers are dropped at load.** 590,819 of the 5,077,237 in-window rows
move value between one account and itself, mostly under the `Reinvestment`
payment format. A payment to yourself has no counterparty, so it cannot evidence
any typology in the catalogue.

**R6 dormant then active cannot fire until a full lookback exists behind the
period.** The study window is ten periods, so an account transacting on the first
day has no history by construction rather than by dormancy.

**Roundness in R5 is a whole dollar amount, not a multiple of a thousand.** The
simulator draws amounts with cents. Twenty US Dollar payments in the entire file
are multiples of a thousand, against 21,010 that are whole dollars.

**R7's corridor is defined structurally, as a cross jurisdiction payment settled
in a cash or crypto instrument,** rather than by naming jurisdictions as high
risk.

## Why

Rules tuned to the label would destroy the comparison this project exists to
make. The baseline is what rules only achieve, and a baseline fitted to the
answer is not a baseline. Volume is also how an institution actually sets these
thresholds, because the queue has to be workable by the analysts who have to work
it.

Self transfers had to go because leaving them in made R2 rapid movement of funds
fire on almost any account that reinvested twice in a day, which is an artefact
of the simulator's payment mix and not a pass through pattern.

R6 without the lookback guard produced 216,568 alerts in the first period against
roughly 1,100 in a normal one. Every account was dormant on day one because there
was no day zero.

R5 at a thousand dollar definition was a dead rule with twenty candidate
transactions in five million. That is a property of the generator, and a rule
that cannot fire cannot have its false positive burden measured, which is the
only thing R5 can contribute on this data.

R7 by named jurisdiction would have meant publishing a country risk list. This
project studies simulated transactions and has no basis for a claim about any
real jurisdiction. The structural definition captures the same red flag, a cross
border movement through an instrument that breaks the audit trail, without making
one.

## Alternatives rejected

**Use the laundering flag to define the alert population.** Faster and wrong. It
deletes the baseline, gives the alert set perfect recall by construction, removes
the false positives that are the entire problem, and hides the typologies the
simulator never generates.

**Keep self transfers and raise R2's thresholds instead.** That would have hidden
a data property inside a parameter, and the parameter would then be carrying two
jobs at once.

**Drop R5 and R8 as unfireable.** Rejected. A rule whose base rate makes it
useless is reported as such rather than quietly dropped, and its alert volume is
a real cost to the analysts who work it.

**Convert currencies so money thresholds apply to all payments.** The file
carries fourteen currencies and no exchange rates. Converting would mean
inventing them, so threshold based rules are stated as applying to US Dollar
payments only.

## Not done

No tuning against per typology recall, and no measurement of recall at all yet.
That is a later milestone and it happens after the baseline ladder exists.

The rule parameter values are described in public documentation by name, unit and
direction of effect, never as the tuned trigger set. The values live in the
private delivery records.

## Changed

`src/pipeline/rules.py`, `scripts/run_rules.py`, `tests/test_rules.py`, and
`requirements-dev.txt`, which gains Polars and PyArrow. The deployed runtime is
unchanged; `requirements.txt` and the serving path are untouched.
