# AGENTS.md

This file is the bootstrap guide for coding agents working in this repository.

Chinese version: see `AGENTS.zh-CN.md`.

The repository validates Claude Code integration with Volcengine Ark Seed Evolving. The preferred path is direct Anthropic Messages API compatibility:

```text
Claude Code
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> Ark endpoint <your-ark-endpoint-id>
```

Use this guide before running commands, editing files, or asking the user for credentials.

## First Step: Ask How Claude Code Will Be Used

Before choosing an integration path, ask the user:

```text
How do you want to use Claude Code in this task?

1. Direct interactive Claude Code
2. CLI/headless Claude Code
3. Agent SDK-style programmable wrapper
4. Product shell / HTTP service
5. Ark Context API cache experiment
6. Other custom workflow
```

If the user does not know, recommend option 2 for automation tests and option 1 for manual coding sessions.

Do not start by asking for raw API keys in chat. Ask the user to export secrets in their terminal.

## Required User Configuration

Ask the user to provide or confirm:

| Config | Required | Default | Notes |
|---|---:|---|---|
| `ARK_API_KEY` or `VOLCENGINE_API_KEY` | Yes | none | User should export it in shell. Never print or commit it. |
| Ark endpoint id | Yes | `<your-ark-endpoint-id>` | Seed Evolving endpoint. |
| Usage mode | Yes | CLI/headless | Route to the correct section below. |
| Cache monitoring | Optional | off | Use `stream-json --verbose` when requested. |
| File modification permission | Optional | ask first | Required for coding tasks that edit files. |
| GitHub remote / push permission | Optional | ask first | Required before pushing commits. |

If `ARK_API_KEY` is missing, tell the user to run:

```bash
export ARK_API_KEY="your-ark-api-key"
```

Never echo, log, write, or commit the actual key.

If the Claude Code binary is missing, ask the user to install it with:

```bash
bash scripts/install_claude_code.sh
```

For details, read `INSTALL_CLAUDE_CODE.zh-CN.md`.

## Shared Environment Setup

Use these environment variables for direct Ark Messages API access:

```bash
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible"
export ANTHROPIC_API_KEY="${ARK_API_KEY:-$VOLCENGINE_API_KEY}"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"

export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-<your-ark-endpoint-id>}"
export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL"

export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

Important:

- `ANTHROPIC_BASE_URL` must not include `/v1/messages`; Claude Code appends the path itself.
- `ANTHROPIC_MODEL` should be an Ark endpoint id, not an Anthropic public model name.
- Set all Claude Code model variables to the same endpoint unless the user explicitly wants model routing.

## Route 1: Direct Interactive Claude Code

Use this route when the user wants to operate Claude Code manually in a terminal.

Run with the project script:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

Equivalent direct binary launch after the shared environment is already exported:

```bash
./vendor/native/darwin-arm64/package/claude
```

Use this for:

- Manual coding sessions.
- Interactive repo exploration.
- User-supervised edits.

Limitations:

- Interactive TUI output is not ideal for real-time cache parsing.
- For cache monitoring, route to CLI/headless mode.

## Route 2: CLI / Headless Claude Code

Use this route for automation, smoke tests, cache monitoring, and reproducible runs.

Preferred script:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

Equivalent direct command:

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "阅读 README.md，总结当前项目如何接入 seed-evolving" \
  --output-format json
```

Use this for:

- One-shot verification.
- CI-like automation.
- Scripted code tasks.
- Cache and usage measurement.

## Route 2A: CLI With Real-Time Cache Monitoring

Use `stream-json` and `--verbose` together. Claude Code requires `--verbose` when `--output-format stream-json` is used.

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "阅读 README.md，总结当前项目状态" \
  --output-format stream-json \
  --verbose \
  --exclude-dynamic-system-prompt-sections \
| python3 -u -c '
import json, sys

last_usage = None

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        obj = json.loads(line)
    except Exception:
        continue

    usage = obj.get("usage")
    msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    if not isinstance(usage, dict):
        usage = msg.get("usage")

    if isinstance(usage, dict):
        inp = usage.get("input_tokens", 0) or 0
        create = usage.get("cache_creation_input_tokens", 0) or 0
        read = usage.get("cache_read_input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0
        total = inp + create + read
        rate = read / total * 100 if total else 0
        last_usage = (inp, create, read, out, rate)
        print(
            f"[cache] input={inp} create={create} read={read} "
            f"output={out} hit_rate={rate:.2f}%",
            flush=True,
        )

if last_usage:
    inp, create, read, out, rate = last_usage
    print(
        f"[summary] input={inp} create={create} read={read} "
        f"output={out} hit_rate={rate:.2f}%",
        flush=True,
    )
else:
    print("[summary] no usage event observed", flush=True)
'
```

Cache hit rate formula:

```text
cache_hit_rate =
  cache_read_input_tokens /
  (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)
```

Fields to inspect:

```text
usage.input_tokens
usage.cache_creation_input_tokens
usage.cache_read_input_tokens
usage.output_tokens
```

## Route 3: Agent SDK-Style Programmable Wrapper

Use this route when another Python process should own orchestration, retries, queueing, or result parsing.

Run:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

Use this for:

- Embedding Claude Code into a larger Python workflow.
- Batch tasks.
- Queue-driven jobs.
- Future migration to an official Agent SDK integration.

Current note:

- This is a local SDK-style wrapper around Claude Code headless execution, not a full official SDK implementation.

## Route 4: Product Shell / HTTP Service

Use this route when the user wants a product/backend surface in front of Claude Code.

Start server:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

Call it:

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

Use this for:

- Web UI experiments.
- Internal service wrappers.
- Future auth, audit, quota, and task queue layers.

## Route 5: Ark Context API Cache Experiment

Use this route only when the user explicitly wants to test Ark native Context API.

Run:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 context-api/context_api_client.py \
  --mode session \
  --system "你是一个极简助手。回答必须包含 SEED_EVOLVING_CONTEXT_OK。" \
  --prompt "用一句话说明你是否读取了缓存中的系统指令。"
```

Use this for:

- Long system prompts.
- Repository summaries.
- Product background caching.
- Non-tool subflows.

Do not use this as the default Claude Code runtime path. Context Chat may not support full Claude Code tool loops.

## Validation Checklist

Before reporting success, run the relevant checks.

Unit tests:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Runtime smoke test:

```bash
bash runtime/run_seed_evolving_messages_api.sh "只输出 OK"
```

Expected:

- Command exits successfully.
- Output includes a successful result.
- `modelUsage` includes `<your-ark-endpoint-id>`.
- Usage may include cache fields such as `cacheReadInputTokens`.

## Safety Rules

- Never print API keys.
- Never write real secrets to `.env`, `.env.example`, README, docs, logs, commits, or terminal summaries.
- Never commit `vendor/`, `.env`, generated logs, Python caches, or local editor files.
- Never modify global Claude Code, Anthropic, or shell configuration unless the user explicitly asks.
- Prefer project-local scripts and environment variables.
- Ask before file edits, commits, remote pushes, or commands that may expose secrets.
- Prefer direct Ark Messages API for normal Claude Code usage.
- Do not add or use a Messages-to-Chat-Completions conversion layer unless the user explicitly starts a new experiment for it.

## Repository Map

| Path | Purpose |
|---|---|
| `runtime/run_interactive_messages_api.sh` | Direct Ark Messages API interactive CLI path |
| `runtime/run_seed_evolving_messages_api.sh` | Direct Ark Messages API runtime path |
| `agent-sdk/seed_evolving_agent.py` | Python SDK-style wrapper |
| `product-shell/server.py` | HTTP product shell |
| `context-api/context_api_client.py` | Ark Context API client |
| `.env.example` | Safe environment variable placeholders |

## When To Ask The User Again

Ask for clarification before continuing if:

- The usage mode is unclear.
- `ARK_API_KEY` or endpoint id is missing.
- The user asks for cache numbers but selected interactive mode.
- The user asks to push but no remote or auth is configured.
- The command may modify files or call external services.
- The task requires a route not listed in this guide.
