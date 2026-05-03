#!/usr/bin/env bash
# Detects chart directories whose VERSION file changed between two commits.
# Writes matrix and has_changes to $GITHUB_OUTPUT.
#
# Usage: on_push_detect.sh <before_sha> <current_sha>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
matrix=$("$SCRIPT_DIR/changed-charts.sh" "${1}" "${2}")

if [ "$(echo "$matrix" | jq '.include | length')" = "0" ]; then
  echo "Outcome: no changes detected, skipping build." >&2
  echo "has_changes=false" >> "$GITHUB_OUTPUT"
else
  echo "has_changes=true" >> "$GITHUB_OUTPUT"
fi
echo "matrix=$matrix" >> "$GITHUB_OUTPUT"
