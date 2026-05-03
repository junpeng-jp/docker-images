#!/usr/bin/env bash
# Detects all chart directories in the repo (used for manual dispatch builds).
# Writes matrix and has_changes to $GITHUB_OUTPUT.
#
# Usage: on_workflow_dispatch_detect.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
matrix=$("$SCRIPT_DIR/changed-charts.sh")

if [ "$(echo "$matrix" | jq '.include | length')" = "0" ]; then
  echo "Outcome: no charts found in repo, skipping build." >&2
  echo "has_changes=false" >> "$GITHUB_OUTPUT"
else
  echo "has_changes=true" >> "$GITHUB_OUTPUT"
fi
echo "matrix=$matrix" >> "$GITHUB_OUTPUT"
