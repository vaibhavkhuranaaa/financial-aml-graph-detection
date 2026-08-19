# 0011 A filter narrows a view, and never the queue

## Decision

**The triage desk gained two view controls and a review record export.** The
queue can be narrowed by typology and by disposition status, and the browser held
review record can be written to a local file. Both were the last two items of the
design language's product behaviour list that were still unbuilt.

**A filter changes what is on screen and nothing else.** This is the whole of the
decision. The alternative, which is what a filter normally does, would have been
to treat the narrowed set as the queue: renumber it, recompute the capacity
consequence against it, and draw the cut line inside it. Each of those is a small
and reasonable looking step, and together they turn a filter into a suppression
control, which is the one thing this product is not allowed to have.

So the invariants are stated rather than assumed:

- A position is always the alert's position in the whole period under the chosen
  ordering. A narrowed view shows a discontinuous run of positions on purpose,
  because the gaps are the evidence that nothing was renumbered.
- Every number in the consequence block, including the worked depth, the true
  positives reached and the per typology recovery table, is computed on the whole
  period. Moving a view control changes none of them.
- The cut line is drawn before the first row on screen that sits past the
  capacity depth, rather than at the row numbered depth plus one. Anchoring it to
  a specific position would let a narrowed view drop the separator, and the
  constraint it draws is not negotiable.
- A narrowed view states the count it is not showing and says those alerts are
  still in the queue and still workable, and it clears in one control.

**The copy carries the same rule as the arithmetic.** Nothing on the surface says
excluded, filtered out, cleared, dismissed or low risk. The browser journey
asserts this against the rendered text of the whole desk rather than against any
one string, so new copy cannot reintroduce a suppression word quietly.

**There is no filter across review periods, and no control pretending there is.**
The design language asks for one. The triage artifact carries exactly one review
period, so a period selector would be a control with a single entry, and a dead
control reads as a missing feature rather than as an honest absence. The view
control states the review period and says the artifact carries only that one. A
cross period filter needs a multi period artifact, which is a rebuild and a new
pinned digest, not an interface change.

**The export is a file this browser writes, not a request this surface makes.**
It carries the review period, the ordering that was on screen, the delivery
statement and the claims boundary alongside the records, because a file outlives
the page it came from and a bare list of dispositions would read as a compliance
record. The journey does not click it, because a real download would leave a file
on the verifying machine; it asserts that the control is reachable, that it is
disabled until a record exists, and that it names both boundaries.

## Consequences

The desk now covers every item in the product behaviour list except the cross
period filter, which is recorded above as blocked on the artifact rather than on
the interface.

Nothing measured changed. No API contract changed, no artifact was rebuilt, and
no digest moved. The two controls are arithmetic and presentation over data the
surface already held, and the deployed public service is unaffected because it
still refuses the triage artifact.

The risk this record exists to hold is drift: a later change that makes the
capacity block follow the filter, or that renumbers the narrowed set, would look
like a bug fix and would be a change of product meaning. The browser journey
asserts both invariants so that the change fails loudly.
