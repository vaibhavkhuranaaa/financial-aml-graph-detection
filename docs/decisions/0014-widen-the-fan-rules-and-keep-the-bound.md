# 0014 Widen the fan rules to a three period window, and find the bound unmoved

## Status

Accepted, 2026-08-21. Supersedes the rules engine version, not the result.

## Context

Decision 0006 recorded a finding it did not act on. R3 fan in and R4 fan out
required a distinct counterparty count inside a single review period, and no
injected laundering attempt reaches that count on any single day, so the rules
surfaced 7.42 percent of the attempts live in the evaluation window on HI-Small
and 7.41 percent on LI-Small. Decision 0013 then measured what that costs: of 337
attempts live, the rules surface 25, and 92.6 percent of the loss happens before
any ordering exists. No ranker can move a bound like that.

The obvious suspicion was that the bound is an artifact of the single day window.
A fan spread over three days is still a fan; a rule that can only see one day
cannot see it. This decision tests that suspicion.

## Decision

The fan rules count distinct counterparties over a trailing window of review
periods. The window ends at the period the alert is raised in and never reaches
forward, so an alert is still evidenced only by transactions that had already
happened when it fired. This is rules engine version 2.

**The window is three periods.** The engine already treats three periods as its
lookback horizon: R6 dormant then active uses `r6_lookback_periods = 3`. Reusing
that horizon keeps one notion of recent history in the catalogue rather than two.
The window was fixed before anything was measured with it.

**The minima move from 12 to 18.** Widening the window at a fixed threshold
raises alert volume from 917.1 to 1,188.5 alerts per period, outside the accepted
band of 640 to 960 that decision 0003 set. Holding the volume target is what the
parameterisation rule requires, so the minima were swept against volume alone.
Eighteen produces 791.2 alerts per period, the closest of any candidate to the
800 target. That choice was made and fixed before any attempt or label was
counted.

## What it did to the bound

Nothing.

| | Engine 1 | Engine 2 |
| --- | --- | --- |
| Window | 1 period | 3 periods |
| Fan minima | 12 | 18 |
| Alerts per period | 917.1 | 791.2 |
| Attempts live | 337 | 337 |
| Attempts surfaced | 25 | 25 |
| Share surfaced | 7.42 percent | 7.42 percent |

The per typology composition moved a little. FAN-OUT goes from 3 surfaced to 4,
SCATTER-GATHER from 6 to 7, STACK from 4 to 2. The total does not move at all.

## The sensitivity table, and why it did not choose anything

Having fixed the parameter set on volume, the pair was then swept to measure what
else was available. This is reported as a measurement and was not used to select
anything.

| Window | Minimum | Alerts per period | Attempts surfaced | Share |
| --- | --- | --- | --- | --- |
| 1 | 12 | 917.1 | 25 | 7.42 percent |
| 3 | 12 | 1,188.5 | 49 | 14.54 percent |
| 3 | 15 | 897.8 | 31 | 9.20 percent |
| 3 | 18 | 791.2 | 25 | 7.42 percent |
| 5 | 18 | 837.7 | 32 | 9.50 percent |
| 5 | 24 | 715.5 | 24 | 7.12 percent |
| 5 | 30 | 685.7 | 23 | 6.82 percent |

Two rows in that table are inside the volume band and surface more than the
shipped parameter set does. Neither was taken, and the reason is the rule this
project is built on: attempts surfaced is computed from the patterns file, which
is the label. Choosing a parameter set because it surfaces more attempts is
choosing parameters against the label, which destroys the comparison the whole
project exists to make. Volume is the selection criterion because volume is what
an institution can actually observe when it sets a threshold. The table is
published because hiding an unflattering sensitivity is worse than reporting one
that a reader might have chosen differently.

What the table does show, and this is the finding worth carrying, is that the
window is not free. Surfacing more attempts costs alert volume roughly in
proportion, and at a fixed volume the window buys nothing at all. The bound is
not a property of the window. It is a property of how small the injected attempts
are against any threshold that holds the volume an analyst team can work.

## What else moved

The alert population is smaller and cleaner: 4,961 alerts carrying 204 true
positives, against 5,715 and 223 under engine 1. Every rung improves.

| Ordering | Engine 1 precision at K | Engine 2 precision at K |
| --- | --- | --- |
| B0 random | 0.0465 | 0.0692 |
| B1 chronological | 0.1134 | 0.1417 |
| B2 amount descending | 0.1361 | 0.1531 |
| B3 rules only priority | 0.1156 | 0.1508 |
| C1 learned ranker | 0.1678 | 0.1905 |

B2 remains the strongest rung on HI-Small and remains the rung to beat. C1's lift
over it is 1.2444 with an interval of 1.1460 to 1.3359, against the ship gate of
1.3 written before the model existed. **The gate is missed again and no model is
promoted.**

On LI-Small the negative is stronger than it was. The strongest rung there is now
B1 chronological at 0.1610, ahead of B2 at 0.1406, so B1 is the binding rung on
that variant. C1 reaches 0.1723, a lift of 1.0704 with an interval of 0.9139 to
1.2441. **That interval contains one.** Under engine 2 the learned ranker is not
distinguishable from ordering the queue by arrival time on the low prevalence
variant. Under engine 1 it at least cleared its baseline there.

## Consequences

Every number measured under engine 1 is invalidated and has been remeasured. The
alert store, the feature table, both backtest run records, the triage artifact and
its pinned digest are all rebuilt. The store digest moves to `ffddcfe6c21ca392`
on HI-Small and `bf4fd3cf6f46bd66` on LI-Small.

The triage artifact carries 623 alerts for the review period rather than 749, and
25 true positive alerts rather than 30. Its distribution decision was approved
again rather than carried across, because a slice drawn from a different alert
population is a different slice even when the source file, its checksum, the
variant and the period are all unchanged.

The roadmap note in decision 0006 is closed. Widening the fan window was the one
change that targeted the measurement bounding every other number, it was made,
and it did not move it. What would move it is a rule catalogue that fires on
smaller structures, which means accepting more alert volume and is a different
decision with a cost an institution has to agree to pay.
