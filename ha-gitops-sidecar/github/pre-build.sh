#!/usr/bin/env bash
# Pre-build CI checks for ha-gitops-sidecar.
# Called by .github/workflows/docker-images.yaml before the Docker build step.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v task &>/dev/null; then
  sh -c "$(curl -fsSL https://taskfile.dev/install.sh)" -- -d -b "$HOME/.local/bin"
  export PATH="$HOME/.local/bin:$PATH"
fi

task check
