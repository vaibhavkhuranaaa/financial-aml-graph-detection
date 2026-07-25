#!/usr/bin/env sh
# Verify the public synthetic replay journey against a running local workbench.
set -eu

base_url="${1:-http://127.0.0.1:8000}"

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "agent-browser is required for browser verification. Install or expose it, then rerun this script." >&2
  exit 2
fi

agent-browser open "$base_url"
agent-browser wait --load networkidle
agent-browser eval 'document.body.innerText.includes("Signal Ledger") ? "HAS_CONTENT" : "BLANK"'
agent-browser eval 'document.querySelector("[data-nextjs-dialog], .vite-error-overlay, #webpack-dev-server-client-overlay") ? "ERROR_OVERLAY" : "NO_ERROR_OVERLAY"'
agent-browser snapshot -i
agent-browser find label "Simulated reviewer rationale" fill "Browser E2E simulated rationale."
agent-browser find role button click --name "Simulate escalation"
agent-browser eval 'document.body.innerText.includes("saved in this browser only") ? "LOCAL_RECORD_SAVED" : "LOCAL_RECORD_MISSING"'
agent-browser find role button click --name "Reset my local records"
agent-browser eval 'document.body.innerText.includes("read-only example remains") ? "LOCAL_RESET_COMPLETE" : "LOCAL_RESET_MISSING"'
agent-browser eval 'document.querySelectorAll("button, input, select, textarea, [role=button]").length > 0 ? "INTERACTIVE_CONTROLS_PRESENT" : "MISSING_INTERACTIVE_CONTROLS"'
agent-browser close
