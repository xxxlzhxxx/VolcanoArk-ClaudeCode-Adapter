#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT="${1:-用一句话说明你是什么模型，并输出 OK。}"

export ARK_MODEL="${ARK_MODEL:-<your-ark-endpoint-id>}"
export ANTHROPIC_MODEL="$ARK_MODEL"
export ANTHROPIC_SMALL_FAST_MODEL="$ARK_MODEL"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"

exec bash "$ROOT_DIR/scripts/run_with_ark.sh" \
  -p "$PROMPT" \
  --output-format json
