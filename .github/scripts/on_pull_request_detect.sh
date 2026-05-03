#!/usr/bin/env bash
# Detects chart directories whose VERSION file changed relative to the PR base branch.
# Writes matrix and has_changes to $GITHUB_OUTPUT.
#
# Usage: on_pull_request_detect.sh <base_ref>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
matrix=$("$SCRIPT_DIR/changed-charts.sh" "${1}")

if [ "$(echo "$matrix" | jq '.include | length')" = "0" ]; then
  echo "Outcome: no changes detected, skipping build." >&2
  echo "has_changes=false" >> "$GITHUB_OUTPUT"
else
  echo "has_changes=true" >> "$GITHUB_OUTPUT"
fi
echo "matrix=$matrix" >> "$GITHUB_OUTPUT"
