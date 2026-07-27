#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${CLAUDE_ARK_HOST:-127.0.0.1}"
PORT="${CLAUDE_ARK_PORT:-8011}"
CLAUDE_BIN="${CLAUDE_BIN:-$ROOT_DIR/vendor/native/darwin-arm64/package/claude}"

if [[ -z "${ARK_API_KEY:-${VOLCENGINE_API_KEY:-}}" ]]; then
  echo "Missing ARK_API_KEY or VOLCENGINE_API_KEY." >&2
  exit 1
fi

if [[ ! -x "$CLAUDE_BIN" ]]; then
  echo "Claude binary is not executable: $CLAUDE_BIN" >&2
  echo "Run: chmod +x '$CLAUDE_BIN'" >&2
  exit 1
fi

export ARK_MODEL="${ARK_MODEL:-doubao-seed-2-1-pro-260628}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-$ARK_MODEL}"
export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-$ARK_MODEL}"
export ANTHROPIC_BASE_URL="http://$HOST:$PORT"
export ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-local-ark-proxy-token}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-$ANTHROPIC_AUTH_TOKEN}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"

python3 "$ROOT_DIR/proxy/anthropic_ark_proxy.py" --host "$HOST" --port "$PORT" &
PROXY_PID=$!
trap 'kill "$PROXY_PID" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 50); do
  if curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

exec "$CLAUDE_BIN" "$@"
