# 0013 Show where the alerts go, in the units the work happens in

## Decision

**The triage artifact carries the measured run broken back into per period, per
typology and per attempt rows, and a fourth GET route serves it.** The desk was
answering its question well and answering it for one review period in pooled
totals. Pooled figures hid three facts, and each of them changes what an
investigation lead would do about the result.

**The loss is upstream of the ranking.** 337 laundering attempts are live in the
evaluation window, the rules surface 25, and the challenger reaches 8 of those
inside capacity against rules only priority's 1. So 92.6 percent of the loss
happens before any ordering exists. The ranking layer is competing for 25 attempts
out of 337, and no ranker can move that bound. This is the number that should
govern what gets built next, and it was not on the surface at all.

**Precision is carried by alerts no typology claims.** 198 of the 223 flagged
alerts carry no typology attribution, and 139 of the challenger's 148 true
positives sit on that line. Its advantage over the binding rung is 25 extra
unattributed alerts and 3 extra attributed ones. The headline metric is real and
it is overwhelmingly not a statement about catching named laundering structures.
That belongs in structure, not in a paragraph.

**The periods are not alike and capacity is fixed.** Volume swings from 304 to
2,127 alerts across the seven periods. At a constant K of 126 that is coverage of
5.9 percent in the worst period against 41.4 percent in the best. The capacity
control is the product, and it was reasoning about a single 749 alert period, so
the operational question of what happens in the 2,127 period could not be asked.

## Two denominators, kept apart

Recall against every live attempt scores the **rules**. Recall of the attempts the
rules surfaced scores the **ordering**. They are different questions and the
artifact now carries both on every typology.

FAN-OUT is the clearest case. Against all 45 live attempts the challenger recalls
4.4 percent, which reads as a ranking failure. Against the 3 the rules actually
surfaced it recalls 66.7 percent, which reads as the ranking working. Both are
true. Reporting only the first blames the ordering for a population it never had,
and reporting only the second would hide that the population is the real problem.

## What is deliberately excluded

The B3 per rule prior hit rates are not carried. They are what the rules only
priority ordering is built from and they sit closer to the tuned trigger set than
to a published result, so the disclosure rule in `docs/scope.md` governs them and
a test asserts they are absent.

Model feature names are carried, with gains, truncated to 15 of 39 with the true
count beside them. Feature names are not rule parameters. The existing leakage
test, which scans the whole payload for every tuned parameter name and value,
still runs over the larger payload and still passes.

That test caught two coincidental collisions in the new fixture while this was
built: a derived coverage ratio equal to `r1_band`, and a fixture feature gain
equal to `r5_min_amount`. Neither was a leak. Both were fixed by changing the
fixture rather than by loosening the assertion, and it is worth recording that a
blunt substring scan gets more collision prone as the payload grows. The right
response is a better fixture, not a narrower test.

## Colour, and a defect avoided rather than fixed

The evidence block is the first part of this surface to encode identity in a mark
rather than in text.

The existing surface carried no defect. Chartreuse and archive orange appear on it
as accent and status colours, and every element using them also carries the words:
a structural zero row says "Structural zero", a deferred row says "Not reached at
this capacity". Colour was never the only channel.

Used as two adjacent series marks, those same hues collapse under deuteranopia to
an OKLab delta E of 1.8, and a red-green colourblind analyst could not separate the
binding baseline from the challenger. So the charts do not use them that way. The
challenger takes a chartreuse stepped into the dark lightness band, the baseline
takes blue, and orange stays a labelled status colour for the capacity line. The
set passes the lightness band, chroma floor, colour vision separation, normal
vision floor and contrast checks on the adjacent pairlist.

Rank still carries no colour. That rule is untouched and the charts add none.

## The result is unchanged

**No model ships.** Lift over the binding rung is 1.2333 with an interval of
1.1045 to 1.3967 against a precommitted gate of 1.3. Nothing here reopens that.

The evidence does show that the challenger leads the binding rung in 7 of 7
periods. That is a consistency claim, and the gate is an effect size gate; the two
are different and the artifact states both rather than letting the stronger looking
one stand in for the weaker one. Making the miss more legible is the point.

## Consequences

A fourth typed GET route, `/api/triage/evidence`, on the allowlist and covered by
the boundary test. The artifact digest changes, so the pin in `src/app.py` moves
with it in the same change, as decision 0012 requires.

Response size is bounded by contract: 12 evaluation periods, 8 typologies, 15
features. A rebuilt artifact cannot quietly grow the response.

Three tests exist to stop the block degrading into the thing it replaced: the
funnel arithmetic has to hold, both recall denominators have to travel together,
and a period that cost volume has to keep its negative sign. The last one matters
most, because smoothing that sign would turn an honest number into a flattering
one and nothing else in the suite would notice.
