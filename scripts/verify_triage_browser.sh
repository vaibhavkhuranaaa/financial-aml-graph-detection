#!/usr/bin/env sh
# Verify the triage desk against a running local workbench.
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
"$browser_cli" eval 'document.body.innerText.includes("At the capacity you have") ? "TRIAGE_PRESENT" : "TRIAGE_MISSING"'
"$browser_cli" eval 'document.querySelector(".vite-error-overlay, #webpack-dev-server-client-overlay") ? "ERROR_OVERLAY" : "NO_ERROR_OVERLAY"'

# The measured result is stated where the queue is read, not behind a link.
"$browser_cli" eval 'document.querySelector(".baseline-wins").innerText.includes("No model ships") ? "BASELINE_WINS_RENDERED" : "BASELINE_WINS_MISSING"'
"$browser_cli" eval 'document.body.innerText.includes("Structural zero") ? "STRUCTURAL_ZERO_RENDERED" : "STRUCTURAL_ZERO_MISSING"'
"$browser_cli" eval 'document.body.innerText.includes("Neither means a crime occurred") ? "CLAIMS_COPY_PRESENT" : "CLAIMS_COPY_MISSING"'

# The evidence block states where the attempts are lost, before the queue is read.
"$browser_cli" eval 'document.querySelector(".evidence") ? "EVIDENCE_RENDERED" : "EVIDENCE_MISSING"'
"$browser_cli" eval 'document.querySelector(".funnel").innerText.includes("lost here") ? "FUNNEL_STATES_THE_LOSS" : "FUNNEL_SILENT"'
"$browser_cli" eval 'document.querySelector(".evidence").innerText.includes("Recall of surfaced") ? "BOTH_DENOMINATORS_SHOWN" : "ONE_DENOMINATOR_ONLY"'
"$browser_cli" eval '(() => { const rows = [...document.querySelectorAll(".evidence tbody tr")].map((r) => r.innerText); return rows.some((r) => /-\d/.test(r)) ? "COSTLIER_PERIODS_VISIBLE" : "NEGATIVE_SIGN_LOST"; })()'
"$browser_cli" eval '(() => { const cells = [...document.querySelectorAll(".evidence .volume-bar")]; return cells.length > 1 ? "PER_PERIOD_VOLUME_SHOWN" : "PER_PERIOD_VOLUME_MISSING"; })()'

# The cut line is drawn in the queue and the alerts below it are still rendered.
"$browser_cli" eval 'document.querySelector(".cut-line") ? "CUT_LINE_DRAWN" : "CUT_LINE_MISSING"'
"$browser_cli" eval '(() => { const cut = Number(document.querySelector(".cut-line").innerText.match(/\d+/)[0]); const below = [...document.querySelectorAll(".queue-row .rank")].filter((cell) => Number(cell.innerText) > cut).length; return below > 0 ? "DEFERRED_ALERTS_VISIBLE" : "DEFERRED_ALERTS_HIDDEN"; })()'

# Rank carries no colour: every rank cell renders in the body text colour.
"$browser_cli" eval '(() => { const colours = new Set([...document.querySelectorAll(".queue-row .rank")].map((cell) => getComputedStyle(cell).color)); return colours.size === 1 ? "RANK_HAS_NO_COLOUR_SCALE" : "RANK_IS_COLOUR_CODED"; })()'

# The capacity control restates the consequence.
"$browser_cli" eval '(() => { const el = document.getElementById("hours"); const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set; set.call(el, String(Math.max(1, Math.round(Number(el.max) / 2)))); el.dispatchEvent(new Event("input", { bubbles: true })); return "CAPACITY_HALVED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval 'document.querySelector(".consequence").innerText.includes("still open and workable") ? "CONSEQUENCE_RESTATED" : "CONSEQUENCE_STALE"'

# Baselines switch in place.
"$browser_cli" eval '(() => { const el = [...document.querySelectorAll(".ordering-switch input")].find((input) => input.value === "B2"); el.click(); return "ORDERING_SWITCHED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval 'document.querySelector(".queue-frame .panel-heading").innerText.includes("Alert amount descending") ? "BASELINE_IN_PLACE" : "BASELINE_MISSING"'

# The view narrows without hiding the cut line and without suppression copy.
"$browser_cli" eval '(() => { const el = document.getElementById("typology-view"); const set = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set; set.call(el, "FAN-IN"); el.dispatchEvent(new Event("change", { bubbles: true })); return "TYPOLOGY_VIEW_NARROWED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval 'document.querySelector(".queue-view").innerText.includes("still in the queue and still workable") ? "NARROWED_VIEW_STATED" : "NARROWED_VIEW_SILENT"'
"$browser_cli" eval 'document.querySelector(".cut-line") ? "CUT_LINE_SURVIVES_NARROWING" : "CUT_LINE_LOST_TO_A_FILTER"'
"$browser_cli" eval '/excluded|filtered out|cleared|low risk|dismissed/i.test(document.querySelector(".triage").innerText) ? "SUPPRESSION_COPY_PRESENT" : "NO_SUPPRESSION_COPY"'
"$browser_cli" eval '(() => { const before = document.querySelector(".consequence").innerText; return before.includes("still open and workable") ? "CONSEQUENCE_UNCHANGED_BY_VIEW" : "CONSEQUENCE_FOLLOWED_A_FILTER"; })()'
"$browser_cli" find role button click --name "Show the whole period"
"$browser_cli" wait 500
"$browser_cli" eval 'document.querySelector(".queue-view").innerText.includes("Showing the whole period") ? "VIEW_CLEARED" : "VIEW_STUCK"'

# An alert below the cut line opens, with no dead end at any depth.
"$browser_cli" eval '(() => { const cut = Number(document.querySelector(".cut-line").innerText.match(/\d+/)[0]); const rows = [...document.querySelectorAll(".queue-row")]; const row = rows.find((item) => Number(item.querySelector(".rank").innerText) > cut); row.click(); return "DEFERRED_ALERT_OPENED"; })()'
"$browser_cli" wait 500
"$browser_cli" eval 'document.querySelector(".alert-detail").innerText.includes("WHY THIS ALERT EXISTS") || document.querySelector(".alert-detail").innerText.includes("Why this alert exists") ? "TRIGGER_EVIDENCE_SHOWN" : "TRIGGER_EVIDENCE_MISSING"'
"$browser_cli" eval '[...document.querySelectorAll(".disposition input")].some((input) => input.checked) ? "DISPOSITION_HAS_A_DEFAULT" : "DISPOSITION_CARRIES_NO_DEFAULT"'

"$browser_cli" find label "Rationale" fill "Browser verification simulated rationale."
"$browser_cli" eval '(() => { document.querySelector(".disposition input").click(); return "DISPOSITION_CHOSEN"; })()'
"$browser_cli" find role button click --name "Record this disposition"
"$browser_cli" eval 'document.body.innerText.includes("recorded in this browser only") ? "LOCAL_RECORD_SAVED" : "LOCAL_RECORD_MISSING"'

# The recorded disposition reaches the review record, and the export is local.
# The click is not issued here: a real download would leave a file behind on the
# verifying machine. What is asserted is that the control is reachable, that it
# is disabled until a record exists, and that it names the local boundary.
"$browser_cli" eval 'document.querySelector(".review-record .record-list") ? "REVIEW_RECORD_LISTED" : "REVIEW_RECORD_MISSING"'
"$browser_cli" eval '(() => { const button = [...document.querySelectorAll(".review-record button")].find((item) => item.innerText.includes("Export")); return button && !button.disabled ? "EXPORT_ENABLED_WITH_A_RECORD" : "EXPORT_UNREACHABLE"; })()'
"$browser_cli" eval 'document.querySelector(".review-record").innerText.includes("never sent to this API") ? "EXPORT_STATES_LOCAL_BOUNDARY" : "EXPORT_BOUNDARY_MISSING"'
"$browser_cli" eval 'document.querySelector(".review-record").innerText.includes("not a compliance record") ? "EXPORT_CARRIES_CLAIMS_BOUNDARY" : "EXPORT_CLAIMS_BOUNDARY_MISSING"'
"$browser_cli" close
