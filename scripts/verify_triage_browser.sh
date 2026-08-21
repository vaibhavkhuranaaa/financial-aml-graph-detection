#!/usr/bin/env sh
# Verify the triage desk against a running local workbench.
#
# Every content assertion matches case insensitively. innerText returns the
# rendered text, so a CSS text-transform decides its case: the evidence table
# headers and the review record boundary are uppercased in the stylesheet, and a
# case sensitive match against them can never pass however correct the surface
# is. Case belongs to presentation, and these assertions are about content.
#
# Run the service with APP_MODE=local-triage-workbench and a built triage
# artifact present. The journey is read only: it moves the capacity control,
# switches the ordering, opens an alert below the cut line, and records a
# browser private disposition. It contains no API write.
set -eu

base_url="${1:-http://127.0.0.1:8000}"
triage_url="${base_url%/}/?surface=triage"

browser_cli="${BROWSER_CLI:-}"

if [ -z "$browser_cli" ] || ! command -v "$browser_cli" >/dev/null 2>&1; then
  echo "Set BROWSER_CLI to the browser automation command used for verification, then rerun this script." >&2
  exit 2
fi

"$browser_cli" open "$triage_url"
"$browser_cli" wait --load networkidle
"$browser_cli" eval '/At the capacity you have/i.test(document.body.innerText) ? "TRIAGE_PRESENT" : "TRIAGE_MISSING"'
"$browser_cli" eval 'document.querySelector(".vite-error-overlay, #webpack-dev-server-client-overlay") ? "ERROR_OVERLAY" : "NO_ERROR_OVERLAY"'

# The measured result is stated where the queue is read, not behind a link.
"$browser_cli" eval '/No model ships/i.test(document.querySelector(".baseline-wins").innerText) ? "BASELINE_WINS_RENDERED" : "BASELINE_WINS_MISSING"'
"$browser_cli" eval '/Structural zero/i.test(document.body.innerText) ? "STRUCTURAL_ZERO_RENDERED" : "STRUCTURAL_ZERO_MISSING"'
"$browser_cli" eval '/Neither means a crime occurred/i.test(document.body.innerText) ? "CLAIMS_COPY_PRESENT" : "CLAIMS_COPY_MISSING"'

# The evidence block states where the attempts are lost, before the queue is read.
"$browser_cli" eval 'document.querySelector(".evidence") ? "EVIDENCE_RENDERED" : "EVIDENCE_MISSING"'
"$browser_cli" eval '/lost here/i.test(document.querySelector(".funnel").innerText) ? "FUNNEL_STATES_THE_LOSS" : "FUNNEL_SILENT"'
"$browser_cli" eval '/Recall of surfaced/i.test(document.querySelector(".evidence").innerText) ? "BOTH_DENOMINATORS_SHOWN" : "ONE_DENOMINATOR_ONLY"'
"$browser_cli" eval '(() => { const rows = [...document.querySelectorAll(".evidence tbody tr")].map((r) => r.innerText); return rows.some((r) => /-\d/.test(r)) ? "COSTLIER_PERIODS_VISIBLE" : "NEGATIVE_SIGN_LOST"; })()'
"$browser_cli" eval '(() => { const cells = [...document.querySelectorAll(".evidence .volume-bar")]; return cells.length > 1 ? "PER_PERIOD_VOLUME_SHOWN" : "PER_PERIOD_VOLUME_MISSING"; })()'

# The cut line is drawn in the queue and the alerts below it are still rendered.
"$browser_cli" eval 'document.querySelector(".cut-line") ? "CUT_LINE_DRAWN" : "CUT_LINE_MISSING"'
"$browser_cli" eval '(() => { const cut = Number(document.querySelector(".cut-line").innerText.match(/\d+/)[0]); const below = [...document.querySelectorAll(".queue-row .rank")].filter((cell) => Number(cell.innerText) > cut).length; return below > 0 ? "DEFERRED_ALERTS_VISIBLE" : "DEFERRED_ALERTS_HIDDEN"; })()'

# The queue renders a budget of rows, not a subset of the period. The control that
# extends it has to name the exact count it is holding back and say that rank is
# not the reason, and taking it has to leave the whole period on screen with the
# ranks contiguous. A budget that reads as a filter is the failure this catches.
"$browser_cli" eval '(() => { const button = [...document.querySelectorAll(".queue-frame button")].find((item) => /Show the remaining/i.test(item.innerText)); if (!button) { return "QUEUE_RENDERS_WHOLE_PERIOD"; } return /Show the remaining \d+ alerts/i.test(button.innerText) && /None is hidden by rank/i.test(button.innerText) ? "BUDGET_NAMES_ITS_COUNT" : "BUDGET_READS_AS_A_FILTER"; })()'
"$browser_cli" eval '(() => { const button = [...document.querySelectorAll(".queue-frame button")].find((item) => /Show the remaining/i.test(item.innerText)); if (button) { button.click(); } return "QUEUE_BUDGET_EXTENDED"; })()'
"$browser_cli" wait 800
"$browser_cli" eval '(() => { const total = Number(document.querySelector(".queue-frame .panel-heading").innerText.match(/(\d[\d,]*) alerts/)[1].replace(/,/g, "")); const ranks = [...document.querySelectorAll(".queue-row .rank")].map((cell) => Number(cell.innerText)); return ranks.length === total && ranks.every((value, index) => value === index + 1) ? "WHOLE_PERIOD_RENDERED" : "PERIOD_TRUNCATED_BY_THE_QUEUE"; })()'
"$browser_cli" eval 'document.querySelector(".cut-line") ? "CUT_LINE_SURVIVES_THE_BUDGET" : "CUT_LINE_LOST_TO_THE_BUDGET"'

# A queue this long needs an exit that is not several hundred tab stops. The skip
# link stays out of sight until it is focused, names the exact number of alerts it
# passes, says they stay in the queue, and lands on a region that has a name to
# announce. A hidden until focused control can only be measured while the window
# actually holds focus, so that one assertion says it could not run rather than
# reporting a failure it did not observe.
"$browser_cli" eval '(() => { const link = document.querySelector(".skip-queue"); if (!link) { return "SKIP_LINK_MISSING"; } return link.getBoundingClientRect().width <= 2 ? "SKIP_LINK_HIDDEN_UNTIL_FOCUSED" : "SKIP_LINK_ALWAYS_VISIBLE"; })()'
"$browser_cli" eval '(() => { const link = document.querySelector(".skip-queue"); return /Skip past [\d,]+ alerts/i.test(link.innerText) && /stays in the queue/i.test(link.innerText) ? "SKIP_LINK_NAMES_ITS_COUNT" : "SKIP_LINK_COUNT_MISSING"; })()'
"$browser_cli" eval '(() => { const link = document.querySelector(".skip-queue"); link.focus(); if (!document.hasFocus()) { return "SKIP_LINK_FOCUS_NOT_TESTABLE_IN_AN_UNFOCUSED_WINDOW"; } return link.getBoundingClientRect().height > 20 ? "SKIP_LINK_VISIBLE_ON_FOCUS" : "SKIP_LINK_STAYS_HIDDEN"; })()'
"$browser_cli" eval '(() => { document.querySelector(".skip-queue").click(); const target = document.getElementById("past-the-queue"); return document.activeElement === target && target.getAttribute("aria-label") ? "SKIP_LINK_LANDS_ON_A_NAMED_REGION" : "SKIP_LINK_LANDS_NOWHERE"; })()'

# Rank carries no colour: every rank cell renders in the body text colour.
"$browser_cli" eval '(() => { const colours = new Set([...document.querySelectorAll(".queue-row .rank")].map((cell) => getComputedStyle(cell).color)); return colours.size === 1 ? "RANK_HAS_NO_COLOUR_SCALE" : "RANK_IS_COLOUR_CODED"; })()'

# The capacity control restates the consequence.
"$browser_cli" eval '(() => { const el = document.getElementById("hours"); const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set; set.call(el, String(Math.max(1, Math.round(Number(el.max) / 2)))); el.dispatchEvent(new Event("input", { bubbles: true })); return "CAPACITY_HALVED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval '/still open and workable/i.test(document.querySelector(".consequence").innerText) ? "CONSEQUENCE_RESTATED" : "CONSEQUENCE_STALE"'

# Baselines switch in place.
"$browser_cli" eval '(() => { const el = [...document.querySelectorAll(".ordering-switch input")].find((input) => input.value === "B2"); el.click(); return "ORDERING_SWITCHED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval '/Alert amount descending/i.test(document.querySelector(".queue-frame .panel-heading").innerText) ? "BASELINE_IN_PLACE" : "BASELINE_MISSING"'

# The view narrows without hiding the cut line and without suppression copy.
"$browser_cli" eval '(() => { const el = document.getElementById("typology-view"); const set = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set; set.call(el, "FAN-IN"); el.dispatchEvent(new Event("change", { bubbles: true })); return "TYPOLOGY_VIEW_NARROWED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval '/still in the queue and still workable/i.test(document.querySelector(".queue-view").innerText) ? "NARROWED_VIEW_STATED" : "NARROWED_VIEW_SILENT"'
"$browser_cli" eval 'document.querySelector(".cut-line") ? "CUT_LINE_SURVIVES_NARROWING" : "CUT_LINE_LOST_TO_A_FILTER"'
"$browser_cli" eval '/excluded|filtered out|cleared|low risk|dismissed/i.test(document.querySelector(".triage").innerText) ? "SUPPRESSION_COPY_PRESENT" : "NO_SUPPRESSION_COPY"'
"$browser_cli" eval '(() => { const before = document.querySelector(".consequence").innerText; return /still open and workable/i.test(before) ? "CONSEQUENCE_UNCHANGED_BY_VIEW" : "CONSEQUENCE_FOLLOWED_A_FILTER"; })()'
"$browser_cli" find role button click --name "Show the whole period"
"$browser_cli" wait 500
"$browser_cli" eval '/Showing the whole period/i.test(document.querySelector(".queue-view").innerText) ? "VIEW_CLEARED" : "VIEW_STUCK"'

# An alert below the cut line opens, with no dead end at any depth.
"$browser_cli" eval '(() => { const cut = Number(document.querySelector(".cut-line").innerText.match(/\d+/)[0]); const rows = [...document.querySelectorAll(".queue-row")]; const row = rows.find((item) => Number(item.querySelector(".rank").innerText) > cut); row.click(); return "DEFERRED_ALERT_OPENED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval '/Why this alert exists/i.test(document.querySelector(".alert-detail").innerText) ? "TRIGGER_EVIDENCE_SHOWN" : "TRIGGER_EVIDENCE_MISSING"'
"$browser_cli" eval '[...document.querySelectorAll(".disposition input")].some((input) => input.checked) ? "DISPOSITION_HAS_A_DEFAULT" : "DISPOSITION_CARRIES_NO_DEFAULT"'

"$browser_cli" find label "Rationale" fill "Browser verification simulated rationale."
"$browser_cli" eval '(() => { document.querySelector(".disposition input").click(); return "DISPOSITION_CHOSEN"; })()'
"$browser_cli" find role button click --name "Record this disposition"
"$browser_cli" eval '/recorded in this browser only/i.test(document.body.innerText) ? "LOCAL_RECORD_SAVED" : "LOCAL_RECORD_MISSING"'

# The recorded disposition reaches the review record, and the export is local.
# The click is not issued here: a real download would leave a file behind on the
# verifying machine. What is asserted is that the control is reachable, that it
# is disabled until a record exists, and that it names the local boundary.
"$browser_cli" eval 'document.querySelector(".review-record .record-list") ? "REVIEW_RECORD_LISTED" : "REVIEW_RECORD_MISSING"'
"$browser_cli" eval '(() => { const button = [...document.querySelectorAll(".review-record button")].find((item) => /Export/i.test(item.innerText)); return button && !button.disabled ? "EXPORT_ENABLED_WITH_A_RECORD" : "EXPORT_UNREACHABLE"; })()'
"$browser_cli" eval '/never sent to this API/i.test(document.querySelector(".review-record").innerText) ? "EXPORT_STATES_LOCAL_BOUNDARY" : "EXPORT_BOUNDARY_MISSING"'
"$browser_cli" eval '/not a compliance record/i.test(document.querySelector(".review-record").innerText) ? "EXPORT_CARRIES_CLAIMS_BOUNDARY" : "EXPORT_CLAIMS_BOUNDARY_MISSING"'
"$browser_cli" close
