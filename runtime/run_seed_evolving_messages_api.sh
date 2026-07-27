#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_BIN="${CLAUDE_BIN:-$ROOT_DIR/vendor/native/darwin-arm64/package/claude}"
PROMPT="${1:-用一句话说明你是什么模型，并输出 OK。}"

if [[ -z "${ARK_API_KEY:-${VOLCENGINE_API_KEY:-}}" ]]; then
  echo "Missing ARK_API_KEY or VOLCENGINE_API_KEY." >&2
  exit 1
fi

if [[ ! -x "$CLAUDE_BIN" ]]; then
  echo "Claude binary is not executable: $CLAUDE_BIN" >&2
  echo "Run: chmod +x '$CLAUDE_BIN'" >&2
  exit 1
fi

export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://ark.cn-beijing.volces.com/api/compatible}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-${ARK_API_KEY:-$VOLCENGINE_API_KEY}}"
export ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-$ANTHROPIC_API_KEY}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-<your-ark-endpoint-id>}"
export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-$ANTHROPIC_MODEL}"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="${ANTHROPIC_DEFAULT_HAIKU_MODEL:-$ANTHROPIC_MODEL}"
export ANTHROPIC_DEFAULT_SONNET_MODEL="${ANTHROPIC_DEFAULT_SONNET_MODEL:-$ANTHROPIC_MODEL}"
export ANTHROPIC_DEFAULT_OPUS_MODEL="${ANTHROPIC_DEFAULT_OPUS_MODEL:-$ANTHROPIC_MODEL}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"

exec "$CLAUDE_BIN" \
  -p "$PROMPT" \
  --output-format json
