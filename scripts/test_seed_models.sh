#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${CLAUDE_ARK_HOST:-127.0.0.1}"
PORT="${CLAUDE_ARK_PORT:-8011}"
PRO_MODEL="${SEED_21_PRO_MODEL:-<your-ark-endpoint-id>}"
EVOLVING_MODEL="${SEED_21_EVOLVING_MODEL:-<your-ark-endpoint-id>}"

if [[ -z "${ARK_API_KEY:-${VOLCENGINE_API_KEY:-}}" ]]; then
  echo "Missing ARK_API_KEY or VOLCENGINE_API_KEY." >&2
  exit 1
fi

export ARK_PASSTHROUGH_MODEL=1

python3 "$ROOT_DIR/proxy/anthropic_ark_proxy.py" --host "$HOST" --port "$PORT" &
PROXY_PID=$!
trap 'kill "$PROXY_PID" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 50); do
  if curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

test_model() {
  local model="$1"
  echo "==> Testing $model"
  curl -fsS "http://$HOST:$PORT/v1/messages" \
    -H 'content-type: application/json' \
    -H 'anthropic-version: 2023-06-01' \
    -H 'x-api-key: <redacted-api-key>' \
    --data-binary @- <<JSON | python3 -m json.tool
{
  "model": "$model",
  "max_tokens": 256,
  "stream": false,
  "messages": [
    {
      "role": "user",
      "content": "用一句话说明你是什么模型，并输出 OK。"
    }
  ]
}
JSON
}

test_model "$PRO_MODEL"
test_model "$EVOLVING_MODEL"
