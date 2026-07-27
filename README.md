# Claude Code on Volcengine Ark

This directory vendors Claude Code and runs it through a local Anthropic Messages API proxy backed by Volcengine Ark chat completions.

## What Is Included

- `vendor/package`: `@anthropic-ai/claude-code@2.1.216` wrapper package from npm.
- `vendor/native/darwin-arm64/package/claude`: native Claude Code binary for macOS arm64.
- `proxy/anthropic_ark_proxy.py`: local `/v1/messages` proxy that maps Anthropic Messages API requests to Ark `/chat/completions`.
- `scripts/run_with_ark.sh`: starts the proxy and then launches Claude Code with `ANTHROPIC_BASE_URL` pointed at the proxy.
- `scripts/test_seed_models.sh`: smoke-tests Seed 2.1 Pro and Seed 2.1 Evolving through the same Messages API compatibility layer.
- `runtime/`: validates Claude Code headless mode as the Seed Evolving runtime, including direct Ark Messages API access.
- `agent-sdk/`: wraps Claude Code headless execution as a programmable Agent SDK-style interface.
- `product-shell/`: exposes a local HTTP product shell that delegates work to the Agent SDK PoC.
- `context-api/`: calls Ark Context API directly to validate Seed Evolving context cache support.

## Requirements

- `python3`
- `curl`
- `ARK_API_KEY` or `VOLCENGINE_API_KEY`
- macOS arm64 for the vendored native binary

Claude Code itself requires Node `>=22` when installed through npm. The current environment did not have `node`/`npm`, so the wrapper tarball and macOS arm64 native package were downloaded directly from npm registry and extracted under `vendor`.

## Run Claude Code With Ark

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
export ARK_MODEL="<your-ark-endpoint-id>"
bash scripts/run_with_ark.sh
```

The launcher exports:

- `ANTHROPIC_BASE_URL=http://127.0.0.1:8011`
- `ANTHROPIC_MODEL=$ARK_MODEL`
- `ANTHROPIC_SMALL_FAST_MODEL=$ARK_MODEL`
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`

By default the proxy overrides Claude Code's requested Claude model with `ARK_MODEL`. Set `ARK_PASSTHROUGH_MODEL=1` only if the request body already contains a valid Ark model or endpoint id.

## Test Seed 2.1 Pro And Evolving

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash scripts/test_seed_models.sh
```

For the endpoints from `/Users/bytedance/WorkSpace/LLM_env.md`, use the second Ark API key in that file. The first key returns 403 for these text-model endpoints.

Defaults:

- `SEED_21_PRO_MODEL=<your-ark-endpoint-id>`
- `SEED_21_EVOLVING_MODEL=<your-ark-endpoint-id>`

## Seed Evolving PoC Directories

### 1. Runtime

Direct Ark Messages API path:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

Legacy local proxy path:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_headless.sh "用一句话说明你是什么模型，并输出 OK。"
```

Use the direct Ark Messages API path first when the target endpoint supports Anthropic Messages API. Keep the local proxy path only for compatibility experiments or request/response mapping debugging.

### 2. Agent SDK

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

Use this path when you want another Python process to own orchestration, retries, queueing, and result parsing.

### 3. Product Shell

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

Then call it from another terminal:

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

Use this path when you want a Web/backend/product surface in front of Claude Code.

### 4. Context API

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 context-api/context_api_client.py \
  --mode session \
  --system "你是一个极简助手。回答必须包含 SEED_EVOLVING_CONTEXT_OK。" \
  --prompt "用一句话说明你是否读取了缓存中的系统指令。"
```

Use this path when you want to test Ark native context cache independently from Claude Code. Context Chat currently does not support `tools`, so it is best for long system prompts, repository summaries, product context, or non-tool subflows.

If your Ark account uses different endpoint IDs or public model names, override the variables:

```bash
export SEED_21_PRO_MODEL="<your-seed-2.1-pro-endpoint-id>"
export SEED_21_EVOLVING_MODEL="<your-seed-2.1-evolving-endpoint-id>"
bash scripts/test_seed_models.sh
```

## Run Local Unit Tests

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
python3 -m unittest discover -s tests -p 'test_*.py'
```

The unit tests validate request/response conversion without calling Ark.

## API Mapping

The proxy supports these Anthropic Messages API features:

- `system` to OpenAI-compatible `system` message.
- `messages[].content` text blocks to chat message text.
- `tool_use` blocks to OpenAI-compatible `tool_calls`.
- `tool_result` blocks to OpenAI-compatible `tool` messages.
- `tools[].input_schema` to OpenAI-compatible function `parameters`.
- non-streaming Ark responses back to Anthropic `message` responses.
- streaming text chunks back to Anthropic SSE events.

Current limitations:

- Image blocks are not forwarded.
- Streaming tool-call deltas are not fully reconstructed; non-streaming tool calls are supported.
- Token usage in streaming responses is emitted as `0` unless Ark includes usage in a compatible stream chunk.
