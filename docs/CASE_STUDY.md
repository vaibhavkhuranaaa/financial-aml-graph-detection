# Signal Ledger: an alert triage workbench, and the model that did not ship

**No model shipped.** A learned ranker was built, trained, measured against a
four rung baseline ladder, and not promoted. It beat every rung. Its lift over
the strongest one was 1.2444 with a 95 percent interval of 1.1460 to 1.3359,
against a ship gate of 1.3 that was written down before the model existed. The
improvement is real and it is not enough, so the deliverable is the rules engine,
the ladder, the measured negative, and the workbench the result is read on. This
document is the account of how that was measured and what it does not prove.

## The problem

Transaction monitoring in banks runs at a 90 to 98 percent false positive rate,
and roughly 1 to 5 percent of alerts become a suspicious activity report. The
cost is not detection. It is the analyst who opens, reads, dispositions and
documents every alert that turns out to be nothing.

The stakeholder is an anti money laundering investigation lead with a fixed
number of analyst hours per review period. The decision is which alerts get those
hours and in what order. The product reorders a queue. It never suppresses,
closes or disposes of an alert, and it never files anything.

## What was built

Six components, in dependency order. Everything below the workbench runs locally
and is imported by nothing that is served.

1. **A typology rules engine**, R1 through R8, written from Bank Secrecy Act
   typologies rather than borrowed. It generates the alert population, which is
   what makes the baseline real: an evaluation against someone else's alerts
   would be a comparison against an unknown. Parameters were tuned against
   measured alert volume and never against the laundering flag. The flag is
   absent from the loader's column selection, so no rule can read it even by
   accident, and a test asserts that.
2. **An alert store.** One row per subject account per review period, with the
   fired rules, their computed trigger evidence, the contributing transaction
   identifiers and a feature cutoff timestamp held separately from the period
   end. Parquet, partitioned by period, immutable. Two consecutive full runs
   produce the same digest, which is the acceptance condition.
3. **An alert level feature build with a leakage gate.** Thirty nine columns over
   two separated horizons: history strictly before the period, and the period
   itself up to the cutoff. The gate recomputes features with every transaction
   at or after the cutoff removed and fails the build on any difference.
4. **A backtest harness** holding the label join. It is the only module in the
   project that reads the laundering flag, and it reads it only to score an
   ordering that already exists.
5. **A learned ranker**, LightGBM lambdarank over the alert features, one group
   per review period, trained on prior periods only across an expanding walk
   forward.
6. **A triage workbench**: the queue, a capacity control in analyst hours, a cut
   line drawn inside the queue, the ordering switchable across every rung and the
   challenger, and alert detail down to the contributing transactions.

**The leakage gate is the part worth keeping.** A leakage check whose build
filters its own input and whose check re-filters the same way degenerates into
two identical code paths agreeing with each other, and it passes forever whether
or not it works. So the test suite substitutes a period builder that ignores the
cutoff and asserts the gate reports the offending column by name. The gate is
known to fail when it should, which is the only thing that makes its passing
worth anything.

## The operating point

Derived before any measurement, from six analysts at seven productive hours and
twenty minutes per alert: **42 analyst hours per period, so K = 126 alerts worked
per period.** Ten daily periods in the study window, the first three reserved as
the minimum training window, seven evaluation periods, 882 worked alerts in
total.

The rules engine emits 7,912 alerts over the ten periods, 791.2 per period,
inside the 640 to 960 band it was parameterised to. The seven evaluation periods
carry 4,961 alerts of which 204 are true positives, a population base rate of
**4.112 percent**. That base rate is the structural ceiling on everything below,
and it is lower than the 4.5 percent estimated before the data was profiled.

## What was measured

Every rung is scored on the same alert population, through the same metric code,
with absolute counts before rates and a 1,000 sample bootstrap interval on every
figure.

| Ordering | True positives | Precision at K | 95 percent interval |
| --- | --- | --- | --- |
| B0 random | 61 | 6.92 percent | 5.33 to 8.50 |
| B1 chronological, oldest first | 125 | 14.17 percent | 11.68 to 16.67 |
| B2 alert amount descending | 135 | 15.31 percent | 12.93 to 17.69 |
| B3 rules only priority | 133 | 15.08 percent | 12.81 to 17.46 |
| B3 with no shrinkage, published beside it | 121 | 13.72 percent | not a reported rung |
| C1 learned ranker | 168 | 19.05 percent | 16.33 to 21.54 |

**The first finding contradicted the plan, and the second engine did not rescue
it.** Rules only priority, the rung the project named as the number to beat, does
not beat sorting on a single feature. Under engine 1 it lost outright, 0.85 with
an interval whose upper bound was below one. Under engine 2 it draws: B3 over B2
is 0.9852 with a paired interval of 0.9231 to 1.0530, which spans one, so the two
are not distinguishable. B3 over B1 is 1.0640, interval 1.0236 to 1.1154. Only B0
is clearly beaten, at 2.1803. The rung a challenger has to beat was fixed as B2
before the challenger was built, it is still the strongest rung, and that decision
cost the model its promotion twice.

**Every headline number, with its interval.**

| Metric | Threshold | Result | Interval | Outcome |
| --- | --- | --- | --- | --- |
| Precision at K, as lift over B2 | 1.3 | 1.2444 | 1.1460 to 1.3359 | **Missed** |
| Lift over every rung | above 1.0 | 1.2444 over B2, 1.2632 over B3, 1.3440 over B1, 2.7541 over B0 | lower bounds 1.1460, 1.1884, 1.2462, 2.0238 | Passed |
| False positive reduction at held coverage | 20 percent | 59.07 percent | per period 42, 76, 83, 63, 105, 110 and 42 alerts freed of 126 | Passed |
| Per typology recall against B3 | no supported typology more than 5 points below | worst drop 0.0 points | see the table below | Passed |
| Rank stability across retrains | Spearman 0.70 | 0.9317 mean over six pairs | 0.8998 to 0.9514 | Passed |
| Rules and model contribution split | reported, not gated | plus 3.97 precision points | rules only accounts for 133 of C1's 168 | Reported |
| Leakage gate | binary | pass | proven to fail when it should | Passed |

## What failed, and why the gate was not moved

C1 finds 168 true positives in the 882 alerts a team of six can work across seven
periods, against 135 for sorting by amount. That is 33 more alerts worth opening,
and the paired interval against B2 excludes 1.0. The improvement is real.

It is also 1.2444 rather than 1.3. The threshold was written before any model
existed, precisely so that this call could not be argued afterwards. Three
flattering readings were available and all three were declined.

- **Report the lift against B3.** 1.2632 is the friendlier figure. B3 does not
  beat a single feature sort, so a challenger that clears a rung nothing should be
  measured against has cleared nothing.
- **Lower the threshold to 1.2.** Moving the ship gate after seeing 1.2444 is the
  failure mode the project was built to avoid.
- **Promote on the interval.** The interval reaches 1.3359, so the true lift
  might clear the gate. It might also be 1.1460. The gate is written on the point
  estimate with an interval condition attached, and both halves have to hold.

**What C1 actually learned, and why the edge is modest.** By gain the model
splits on contributing transaction count, in period payment count, currency
count and in period amount aggregates. Those are size and busyness, which is the
same family of signal B2 exploits through amount. The model adds discrimination
inside that family rather than finding a new one, which is consistent with a lift
near 1.2 and not near 2.

## The result held on a second dataset

The whole pipeline was rerun on LI-Small, the low prevalence release of the same
simulator, with the parameter set, the operating point and every metric
definition held fixed.

| Ordering | HI-Small precision at K | LI-Small precision at K |
| --- | --- | --- |
| B1 chronological | 14.17 percent | 16.10 percent |
| B2 alert amount descending | 15.31 percent | 14.06 percent |
| B3 rules only priority | 15.08 percent | 14.17 percent |
| C1 learned ranker | 19.05 percent | 17.23 percent |
| Strongest rung | B2 | **B1** |
| C1 lift over the strongest rung | 1.2444, interval 1.1460 to 1.3359 | 1.0704, interval 0.9139 to 1.2441 |

**The strongest rung is not the same one on both variants.** On HI-Small it is B2.
On LI-Small it is B1 chronological, which is what the queue already does before
anyone sorts it. Measured against it, C1's interval contains one: on the low
prevalence variant the learned ranker is not distinguishable from working the
queue in arrival order. Against B2 the same run reads 1.2258, which is the
flattering comparison and is not the one that counts. False positive reduction is
26.64 percent there and rank stability is 0.9014, both passing.

**On LI-Small it also fails a second criterion.** The per typology floor permits a
supported typology to sit at most 5 recall points below B3. There, B3 recovers one
GATHER-SCATTER attempt of ten and one SCATTER-GATHER attempt of twelve, and C1
recovers neither, a worst drop of 10.00 points. On that variant the model misses
two of the three ship criteria rather than one.

Two things about that comparison are recorded rather than smoothed over. The
perturbation attenuates: a 44 percent cut in transaction level prevalence, from
0.10061 to 0.05602 percent in the study window, becomes only a 22 percent cut in
the alert population base rate, 3.21 percent against 4.11 percent, because the
rules select for structure and structure survives the variant. And K stays at 126 because K is analyst hours, so
the same parameters produce a deeper queue on LI-Small and the run varies
prevalence and queue depth together.

## Per typology recall, including the structural zeros

Five of the eight catalogue rules have no counterpart in the simulated data. The
simulator generates BIPARTITE, CYCLE, FAN-IN, FAN-OUT, GATHER-SCATTER, RANDOM,
SCATTER-GATHER and STACK, and nothing that R1, R5, R6, R7 or R8 targets. Their
recall is zero **by construction and not by failure**, so it is reported as an
attempt count of zero rather than as a recall of zero, and their measured alert
volume stays on the same row, because that volume is a real analyst cost and it
is the finding.

| Rule | What it targets | Alerts raised, ten periods | Injected attempts available |
| --- | --- | --- | --- |
| R1 | Structuring below a reporting threshold | 1,378 | **0, structural zero** |
| R2 | Rapid movement of funds | 2,748 | 89, via STACK and CYCLE |
| R3 | Fan in | 1,431 | 122, via FAN-IN, GATHER-SCATTER and BIPARTITE |
| R4 | Fan out | 446 | 124, via FAN-OUT, SCATTER-GATHER and BIPARTITE |
| R5 | Round amount repetition | 395 | **0, structural zero** |
| R6 | Dormant then active | 223 | **0, structural zero** |
| R7 | High risk corridor | 836 | **0, structural zero** |
| R8 | Peer group velocity deviation | 725 | **0, structural zero** |

Attempt counts for R3 and R4 overlap through BIPARTITE and are never summed, and
neither are the alert counts, because one alert can fire several rules. Counted
without double counting, **3,328 of the 7,912 alerts, 42.1 percent of the queue,
are raised only by the five rules with no injected counterpart**, and 2,193 of
4,961, or 44.2 percent, inside the evaluation periods.

Those alerts are not empty. They carry **14 of the 204 true positives**, a base
rate of 0.64 percent against the population's 4.11 percent. So the five rules buy
6.9 percent of the findable positives for 44.2 percent of the analyst volume, and
switching them off would be a real trade rather than a free deletion. Every one of
those 14 is a coincidence of timing rather than a typology the rule was written
for: the rule targets a pattern the simulator never generates, and the alert
happened to contain a flagged transaction belonging to some other attempt.

That is not a model result. It is what a rule catalogue costs when the data does
not contain what it looks for, and it is the most transferable finding in this
project.

**Recall at K, per injected typology, with every denominator shown.**

| Typology | Attempts live | Surfaced by rules | B2 recovers | B3 recovers | C1 recovers | C1 recall, 95 percent interval |
| --- | --- | --- | --- | --- | --- | --- |
| BIPARTITE | 35 | 1 | 0 | 0 | 0 | 0.0000 to 0.0000 |
| CYCLE | 51 | 3 | 0 | 0 | 1 | 0.0000 to 0.0588 |
| FAN-IN | 39 | 1 | 0 | 0 | 0 | 0.0000 to 0.0000 |
| FAN-OUT | 45 | 3 | 0 | 0 | 2 | 0.0000 to 0.1111 |
| GATHER-SCATTER | 48 | 6 | 1 | 1 | 3 | 0.0000 to 0.1458 |
| RANDOM | 37 | 1 | 1 | 0 | 0 | 0.0000 to 0.0000 |
| SCATTER-GATHER | 44 | 6 | 2 | 0 | 2 | 0.0000 to 0.1136 |
| STACK | 38 | 4 | 1 | 0 | 0 | 0.0000 to 0.0000 |
| **Total** | **337** | **25** | **5** | **1** | **8** | |

Every interval on that table includes zero. On a denominator of one to six
surfaced attempts, per typology recall is directional and nothing more, and this
document says so rather than presenting eight decimal places as a result.

## The unattributed positives, on their own line

The patterns file names 3,209 of the 5,177 flagged transactions. The other
**1,968, which is 38.0 percent, carry the laundering flag and no typology
attribution at all.** They are positives, they count toward precision, and they
are reported as their own line rather than folded into a typology or dropped.

| Ordering | Unattributed true positive alerts reached, of 178 available |
| --- | --- |
| B0 random | 54 |
| B1 chronological | 121 |
| B2 amount descending | 126 |
| B3 rules only priority | 127 |
| C1 learned ranker | 154 |

**This is the line that explains the headline.** 178 of the 204 true positive
alerts in the evaluation population carry no attribution, and 154 of C1's 168 are
on this line. The ranker is mostly ordering the unattributed positives, because
that is what the alert population is made of. On LI-Small the effect is close to
complete: 150 of C1's 152 true positives are unattributed.

## What the evidence cannot carry

**The rules surface 7.4 percent of the attempts that are live.** 25 of 337 on
HI-Small, 8 of 108 on LI-Small: 7.42 and 7.41 percent, two independently injected
attempt sets, the same fraction to two decimal places.

The obvious explanation was that the fan in and fan out rules counted
counterparties inside a single day while the attempts spread their structure
across several. That explanation was tested rather than assumed. The rules were
rebuilt to count counterparties over a trailing three period window, the minima
were re-tuned on alert volume alone to hold the accepted band, and the whole
pipeline was rerun. **The engine still surfaces 25 of 337, the same 7.42
percent.** Widening the window while holding the old threshold does surface 49,
but at 1,188.5 alerts per period against a ceiling of 960, so that surfacing is
bought with analyst volume rather than found. The bound is not a property of the
window. It is a property of how small the injected attempts are against any
threshold that holds a workable queue. Decision record 0014 carries the full
sensitivity table, including two in band rows that surface more and were not
taken, because attempts surfaced is computed from the label and choosing
parameters by it would be choosing parameters against the label.
**No ordering can recover an attempt no rule raised an alert on**, so per typology
recall at K is between zero and eight attempts for every rung including the
ranker, and reparameterising to a multi day window would invalidate the alert
store, the feature build and every number above.

**Twenty nine percent of attempts are truncated by the study window.** 109 of the
370 injected attempts have a transaction dated after 2022-09-10, and an attempt
spans up to eight days. That is why the labelling rule separates from the feature
cutoff: the label join reads the full transaction file including days after the
window, because an outcome observed later is how a suspicious activity report
works, while features stay bound by the cutoff and the leakage gate enforces that
separately.

**The typology level evidence is thin even on the primary variant.** HI-Small
carries 35 to 51 injected attempts per typology and LI-Small carries 10 to 19.
That is enough to make per typology recall reportable and not enough to make it
precise. Every figure prints its attempt count and its interval.

**The attempt unit does not survive contact with the data.** The headline metric
was defined as false positive reduction at held typology recall, in attempts. At
25 surfaced attempts across seven periods, five periods carry a target of one
attempt, one carries zero, and in two the challenger must be worked deeper than K
to match a single attempt. The metric is therefore reported in **true positive
alerts**, with the threshold unchanged at 20 percent and the attempt depths
published beside the alert depths. Only the unit of the held coverage changed.

**The largest available gain in this project is a better alert population, not a
better ranker.** That conclusion is stable across both dataset variants and it is
the honest answer to the question the project set out to ask.

## The workbench

The surface an analyst would work in is deployed, against a real review period:
749 alerts, 30 of them true positives, with K reaching 16.8 percent of the
period.

- **The capacity control is the product.** It is expressed in analyst hours, with
  the alert count derived from it, and every move restates alerts included as a
  count and a share, hours implied at a stated and adjustable handling time, true
  positives reached, what is not reached, per typology attempts recovered with
  their live and surfaced counts, and which typology loses coverage first.
- **The cut line is drawn inside the queue.** Every alert below it stays visible,
  keeps its disposition control, and opens to the same detail view. The copy is
  "not reached at this capacity", never excluded, cleared, or low risk. The model
  reorders and never suppresses, and an interface that hid the deferred alerts
  would be contradicting its own product claim.
- **Rank carries no colour.** No bar, no heat scale, no gradient. A colour scale
  invites rank to be read as a probability or a severity and it is neither.
- **Both hard states render at full weight.** "The baseline holds. No model ships"
  sits above the queue in the largest type on the page, with the lift, its
  interval and the gate beside it. The five structural zeros carry their reason
  and their measured alert volume on the same row. Neither is behind a
  disclosure, and neither is in smaller type than a win would have been.
- **The disposition control carries no default** and there is no recommended
  action anywhere. Suggesting the disposition is the one change that would turn a
  ranking product into a deciding one.

**It was withheld until it was approved, and it is pinned now that it is.** The
slice a real queue needs is larger than the approved replay artifact's scope, and
an approval granted for one scope never carries to another, so the desk ran
locally until the owner recorded a distribution decision against the exact
verified source checksum. It is published under CDLA-Sharing-1.0 with its
modification and pseudonymisation notice, and the public service admits only the
pinned release: an approved but unreviewed rebuild is refused, because approval
is a statement about a source and the pin is a statement about a build.

## The claims boundary

This is a portfolio research demonstration. It is not a compliance product, a
production monitor, an accusation, or a statement about any real person or
organisation.

- **The data is realistic synthetic banking data** produced by a simulator, under
  the Community Data License Agreement, Sharing, Version 1.0. It is never
  described as anonymised customer data, because it is not.
- **Every measurement is a statement about a simulated population.** The
  laundering flag is generated by the simulator. Nothing here says anything about
  real world detection performance.
- **An alert means a rule fired.** A high rank means the alert resembles alerts
  that resolved as suspicious in the simulation. Neither means a crime occurred.
- **Nothing is scored at request time.** The public surface serves a precomputed
  artifact and accepts no visitor supplied input for scoring. Putting inference
  behind a public URL is a claims decision, not a capacity one, and the answer is
  no.
- **No compliance suitability, regulatory acceptance, or production readiness is
  claimed.** This is not a Bank Secrecy Act compliant system, it performs no
  sanctions screening and no customer risk rating, and it never files or drafts a
  suspicious activity report.
- **The typology rules are described, not disclosed.** The catalogue publishes
  what each rule means, its measured base rate and volume, and each parameter's
  name, unit and direction of effect. The tuned trigger values are held privately,
  because a precise trigger set published openly reads as an evasion guide.
- **The source is local only.** Raw transaction files are never committed and
  never served.

## Reproducing the public fixture

With a verified local v8 input, record a source manifest:

```sh
python3 scripts/build_public_replay.py \
  --source <local HI-Small_Trans.csv> \
  --record-manifest <local-source.json> \
  --retrieved-at <ISO-8601 timestamp>
```

After the owner records an approved decision for that exact source checksum,
materialise the artifact:

```sh
python3 scripts/build_public_replay.py \
  --source-manifest <local-source.json> \
  --distribution-decision <approved-decision.json> \
  --output data/fixtures/public_casefile.json
```

The admission check refuses a missing or changed checksum, an unverified source
manifest, an unapproved distribution decision, or a tampered artifact. The
pipeline, the ladder and the triage artifact are reproduced by the commands in
[WORKBENCH_VERIFICATION.md](WORKBENCH_VERIFICATION.md).

## What I would do next, and why it is not in this repository

**Widen the fan in and fan out rules to a multi day counterparty window.** That is
the change most likely to move the ceiling, because it targets the one
measurement that bounds everything else. It also invalidates the alert store, the
feature build and every number in this document, so it is a new evaluation rather
than an edit, and doing it quietly would have been the dishonest option.

**Not a better ranker.** Two dataset variants agree that the alert population and
not the ordering is the binding constraint, and there is no validation split in
ten periods that is not the evaluation set, so any hyperparameter search would be
fitted to the periods the result is reported on. The parameter set is stated,
chosen for the data size, and was not searched.

---

The full decision history is in [decisions/](decisions/). Every threshold, its
method and its limitation is in [metric-glossary.md](metric-glossary.md). What the
product deliberately does not do is in [scope.md](scope.md).
