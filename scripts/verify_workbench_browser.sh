#!/usr/bin/env sh
# Verify the public synthetic replay journey against a running local workbench.
set -eu

base_url="${1:-http://127.0.0.1:8000}"

browser_cli="${BROWSER_CLI:-}"

if [ -z "$browser_cli" ] || ! command -v "$browser_cli" >/dev/null 2>&1; then
  echo "Set BROWSER_CLI to the browser automation command used for verification, then rerun this script." >&2
  exit 2
fi

"$browser_cli" open "$base_url"
"$browser_cli" wait --load networkidle
"$browser_cli" eval 'document.body.innerText.includes("Signal Ledger") ? "HAS_CONTENT" : "BLANK"'
"$browser_cli" eval 'document.querySelector("[data-nextjs-dialog], .vite-error-overlay, #webpack-dev-server-client-overlay") ? "ERROR_OVERLAY" : "NO_ERROR_OVERLAY"'
"$browser_cli" snapshot -i
"$browser_cli" find label "Simulated reviewer rationale" fill "Browser E2E simulated rationale."
"$browser_cli" find role button click --name "Simulate escalation"
"$browser_cli" eval 'document.body.innerText.includes("saved in this browser only") ? "LOCAL_RECORD_SAVED" : "LOCAL_RECORD_MISSING"'
"$browser_cli" find role button click --name "Reset my local records"
"$browser_cli" eval 'document.body.innerText.includes("read-only example remains") ? "LOCAL_RESET_COMPLETE" : "LOCAL_RESET_MISSING"'
"$browser_cli" eval 'document.querySelectorAll("button, input, select, textarea, [role=button]").length > 0 ? "INTERACTIVE_CONTROLS_PRESENT" : "MISSING_INTERACTIVE_CONTROLS"'
"$browser_cli" close
