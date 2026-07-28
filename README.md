# Claude Code on Volcengine Ark

This directory validates Claude Code on Volcengine Ark through Ark's Anthropic Messages API compatibility endpoint.

For a Chinese architecture guide covering Claude Code secondary development forms, binary layering, integration entry points, and GitHub usage, see `CLAUDE_CODE_DEVELOPMENT.zh-CN.md`.

## What Is Included

- `vendor/package`: `@anthropic-ai/claude-code@2.1.216` wrapper package from npm.
- `vendor/native/darwin-arm64/package/claude`: native Claude Code binary for macOS arm64.
- `scripts/test_seed_models.sh`: smoke-tests Seed 2.1 Pro and Seed 2.1 Evolving through Ark's Anthropic Messages API compatibility endpoint.
- `runtime/`: validates Claude Code interactive and headless modes through direct Ark Messages API access.
- `agent-sdk/`: wraps Claude Code headless execution as a programmable Agent SDK-style interface.
- `product-shell/`: exposes a local HTTP product shell that delegates work to the Agent SDK PoC.
- `context-api/`: calls Ark Context API directly to validate Seed Evolving context cache support.

## Requirements

- `python3`
- `curl`
- `ARK_API_KEY` or `VOLCENGINE_API_KEY`
- macOS arm64 for the vendored native binary

Claude Code itself requires Node `>=22` when installed through npm. The current environment did not have `node`/`npm`, so the wrapper tarball and macOS arm64 native package were downloaded directly from npm registry and extracted under `vendor`.

For binary setup details, see `INSTALL_CLAUDE_CODE.zh-CN.md`.

## Run Interactive Claude Code With Ark Messages API

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

The script exports `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, and related Claude Code model variables before launching the native Claude Code binary.

Claude Code appends `/v1/messages` to `ANTHROPIC_BASE_URL`, so do not include that path in the base URL.

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

### 1. Interactive CLI

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

Use this path when a human wants to operate Claude Code in the terminal.

### 2. CLI / Headless

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

Use this path when you want Claude Code itself to be the runtime but need scriptable JSON output.

### 3. Agent SDK-Style

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

Use this path when you want another Python process to own orchestration, retries, queueing, and result parsing.

### 4. Product Shell

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

### 5. Context API

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
python3 -m py_compile agent-sdk/seed_evolving_agent.py product-shell/server.py context-api/context_api_client.py
```

The compile check validates local Python entry points without calling Ark.

## API Path

The repository only recommends the Anthropic Messages API compatibility path:

```text
Claude Code
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> Ark endpoint <your-ark-endpoint-id>
```

All Claude Code runtime traffic should use this Messages API path.
