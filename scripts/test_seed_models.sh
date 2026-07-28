#!/usr/bin/env bash
set -euo pipefail

PRO_MODEL="${SEED_21_PRO_MODEL:-}"
EVOLVING_MODEL="${SEED_21_EVOLVING_MODEL:-${ANTHROPIC_MODEL:-${ARK_MODEL:-}}}"
ARK_MESSAGES_BASE_URL="${ANTHROPIC_BASE_URL:-https://ark.cn-beijing.volces.com/api/compatible}"

if [[ -z "${ARK_API_KEY:-${VOLCENGINE_API_KEY:-}}" ]]; then
  echo "Missing ARK_API_KEY or VOLCENGINE_API_KEY." >&2
  exit 1
fi

API_KEY="${ARK_API_KEY:-$VOLCENGINE_API_KEY}"

if [[ -z "$PRO_MODEL" && -z "$EVOLVING_MODEL" ]]; then
  echo "Missing SEED_21_PRO_MODEL, SEED_21_EVOLVING_MODEL, ANTHROPIC_MODEL, or ARK_MODEL." >&2
  exit 1
fi

test_model() {
  local model="$1"
  echo "==> Testing $model"
  curl -fsS "$ARK_MESSAGES_BASE_URL/v1/messages" \
    -H 'content-type: application/json' \
    -H 'anthropic-version: 2023-06-01' \
    -H "x-api-key: $API_KEY" \
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

if [[ -n "$PRO_MODEL" ]]; then
  test_model "$PRO_MODEL"
fi

if [[ -n "$EVOLVING_MODEL" ]]; then
  test_model "$EVOLVING_MODEL"
fi
