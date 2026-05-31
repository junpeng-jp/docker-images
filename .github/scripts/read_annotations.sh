#!/usr/bin/env bash
# Reads OCI annotations from an image's annotations directory and writes them to stdout
# in the <prefix>:<key>=<value> format expected by docker/build-push-action.
#
# Usage: read_annotations.sh <image_dir>
set -euo pipefail

annotations_dir="${1}/annotations"
[ -d "$annotations_dir" ] || exit 0

for prefix in index manifest manifest-descriptor index-descriptor default; do
  file="$annotations_dir/$prefix"
  [ -f "$file" ] || continue
  while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue
    [ "$prefix" = "default" ] && echo "$line" || echo "${prefix}:${line}"
  done < "$file"
done
