#!/usr/bin/env bash
# Outputs a JSON matrix ({"include":[{"name":"...","version":"..."}]}) of charts
# whose VERSION file changed (or all charts when no diff reference is given).
#
# Usage:
#   changed-charts.sh                        # all charts in repo
#   changed-charts.sh <base_ref>             # diff against origin/<base_ref> (pull request)
#   changed-charts.sh <before_sha> <sha>     # diff between two commits (push); lists all on first push
set -euo pipefail

build_matrix() {
  local dirs="$1"
  if [ -z "$dirs" ]; then
    echo '{"include":[]}'
    return
  fi
  echo "$dirs" | while IFS= read -r dir; do
    version=$(tr -d '[:space:]' < "$dir/VERSION")
    echo "  ${dir} → ${version}" >&2
    printf '%s' "$dir" | jq -R --arg v "$version" '{"name": ., "version": $v}'
  done | jq -sc '{"include": .}'
}

case "$#" in
  0)
    echo "Listing all charts in repo..." >&2
    dirs=$(find . -mindepth 2 -maxdepth 2 -name 'VERSION' \
      | sed 's|^\./||;s|/VERSION$||' | sort -u)
    if [ -z "$dirs" ]; then
      echo "No charts found." >&2
    else
      echo "Charts found:" >&2
    fi
    build_matrix "$dirs"
    ;;
  1)
    BASE_REF="${1}"
    echo "Detecting changed charts relative to origin/${BASE_REF}..." >&2
    dirs=$(git diff --name-only "origin/${BASE_REF}...HEAD" \
      | grep -E '^[^/]+/VERSION$' \
      | sed 's|/VERSION$||' | sort -u || true)
    if [ -z "$dirs" ]; then
      echo "No chart VERSION files changed." >&2
    else
      echo "Changed charts:" >&2
    fi
    build_matrix "$dirs"
    ;;
  2)
    BEFORE="${1}"
    SHA="${2}"
    if [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
      echo "First push — listing all charts in repo..." >&2
      dirs=$(find . -mindepth 2 -maxdepth 2 -name 'VERSION' \
        | sed 's|^\./||;s|/VERSION$||' | sort -u)
      if [ -z "$dirs" ]; then
        echo "No charts found." >&2
      else
        echo "Charts found:" >&2
      fi
    else
      echo "Detecting changed charts between ${BEFORE} and ${SHA}..." >&2
      dirs=$(git diff --name-only "$BEFORE" "$SHA" \
        | grep -E '^[^/]+/VERSION$' \
        | sed 's|/VERSION$||' | sort -u || true)
      if [ -z "$dirs" ]; then
        echo "No chart VERSION files changed." >&2
      else
        echo "Changed charts:" >&2
      fi
    fi
    build_matrix "$dirs"
    ;;
  *)
    echo "Usage: changed-charts.sh [<base_ref> | <before_sha> <sha>]" >&2
    exit 1
    ;;
esac
