#!/usr/bin/env bash
# Pre-build CI checks for ha-gitops-sidecar.
# Called by .github/workflows/docker-images.yaml before the Docker build step.
# Must be run from the ha-gitops-sidecar image root directory.
set -euo pipefail

if [ ! -f "Taskfile.yml" ]; then
  echo "Error: must be run from the image root directory (no Taskfile.yml found in $(pwd))"
  exit 1
fi

if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v task &>/dev/null; then
  sh -c "$(curl -fsSL https://taskfile.dev/install.sh)" -- -d -b "$HOME/.local/bin"
  export PATH="$HOME/.local/bin:$PATH"
fi

task check
