#!/usr/bin/env bash
set -euo pipefail

PRO_MODEL="${SEED_21_PRO_MODEL:-<your-ark-endpoint-id>}"
EVOLVING_MODEL="${SEED_21_EVOLVING_MODEL:-<your-ark-endpoint-id>}"
ARK_MESSAGES_BASE_URL="${ANTHROPIC_BASE_URL:-https://ark.cn-beijing.volces.com/api/compatible}"

if [[ -z "${ARK_API_KEY:-${VOLCENGINE_API_KEY:-}}" ]]; then
  echo "Missing ARK_API_KEY or VOLCENGINE_API_KEY." >&2
  exit 1
fi

API_KEY="${ARK_API_KEY:-$VOLCENGINE_API_KEY}"

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

test_model "$PRO_MODEL"
test_model "$EVOLVING_MODEL"
