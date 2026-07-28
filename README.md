# Claude Code on Volcengine Ark

Language: [中文](#中文) | [English](#english)

<a id="中文"></a>

## 中文

本仓库验证如何让 Claude Code 通过火山方舟的 Anthropic Messages API 兼容入口调用 Seed Evolving。当前只保留 Messages API 接入路径，不保留其他协议入口。

更完整的中文架构说明见 `CLAUDE_CODE_DEVELOPMENT.zh-CN.md`，Claude Code binary 安装说明见 `INSTALL_CLAUDE_CODE.zh-CN.md`。

### 包含内容

- `scripts/test_seed_models.sh`：通过 Ark Anthropic Messages API 兼容入口 smoke-test Seed 2.1 Pro 和 Seed 2.1 Evolving。
- `runtime/`：验证 Claude Code interactive 和 headless 两种运行模式。
- `agent-sdk/`：把 Claude Code headless 执行封装成可编程的 Agent SDK-style 接口。
- `product-shell/`：提供一个本地 HTTP product shell，并委托给 Agent SDK-style PoC。
- `AGENTS.md` / `AGENTS.zh-CN.md`：给 coding agent 读取的中英文接入指南。

### 前置要求

- `python3`
- `curl`
- `ARK_API_KEY` 或 `VOLCENGINE_API_KEY`
- Claude Code binary，默认路径为 `vendor/native/darwin-arm64/package/claude`

本仓库不会提交 `vendor/`、Claude Code binary 或真实 API key。首次使用请先安装 binary：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
bash scripts/install_claude_code.sh
```

### API 路径

Claude Code 原生按 Anthropic Messages API 语义工作。本仓库将 Claude Code 的 `ANTHROPIC_*` 环境变量指向火山方舟：

```text
Claude Code
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> Ark endpoint <your-seed-evolving-endpoint-id>
  -> Seed Evolving
```

关键配置：

```bash
export ARK_API_KEY="your-ark-api-key"
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible"
export ANTHROPIC_API_KEY="$ARK_API_KEY"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_MODEL="<your-seed-evolving-endpoint-id>"
export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

注意：`ANTHROPIC_BASE_URL` 不要包含 `/v1/messages`，Claude Code 会自动拼接该路径。

### 快速验证 Ark Messages API

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash scripts/test_seed_models.sh
```

默认 endpoint：

- `SEED_21_PRO_MODEL=<your-seed-pro-endpoint-id>`
- `SEED_21_EVOLVING_MODEL=<your-seed-evolving-endpoint-id>`

如需替换成自己的方舟 endpoint：

```bash
export SEED_21_PRO_MODEL="<your-seed-2.1-pro-endpoint-id>"
export SEED_21_EVOLVING_MODEL="<your-seed-2.1-evolving-endpoint-id>"
bash scripts/test_seed_models.sh
```

### 接入方式

#### 1. Interactive CLI

适合人工在终端中直接操作 Claude Code。

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

#### 2. CLI / Headless

适合自动化任务、smoke test、CI-like 调用和 JSON 输出。

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

#### 3. Agent SDK-Style

适合让 Python 进程负责调度、重试、排队和结果解析。

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

#### 4. Product Shell

适合在 Claude Code 前面套一层 Web/backend/product surface。

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

另开一个终端调用：

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

### 本地检查

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
python3 -m py_compile agent-sdk/seed_evolving_agent.py product-shell/server.py
bash -n runtime/run_seed_evolving_messages_api.sh runtime/run_interactive_messages_api.sh scripts/install_claude_code.sh scripts/test_seed_models.sh
```

### 安全规则

- 不提交 `vendor/`、`.env`、真实 API key、运行日志或本地缓存。
- 不在 README、脚本、commit message 或终端输出中暴露真实 API key。
- 不修改全局 Claude Code、Anthropic 或 shell 配置，除非用户明确要求。
- 普通 Claude Code 使用统一保持 Ark Anthropic Messages API only。

[Back to language switch](#claude-code-on-volcengine-ark)

<a id="english"></a>

## English

This repository validates running Claude Code against Volcengine Ark Seed Evolving through Ark's Anthropic Messages API compatibility endpoint. The repository keeps the Messages API path only and does not include alternate protocol entry points.

For a detailed Chinese architecture guide, see `CLAUDE_CODE_DEVELOPMENT.zh-CN.md`. For Claude Code binary installation, see `INSTALL_CLAUDE_CODE.zh-CN.md`.

### What Is Included

- `scripts/test_seed_models.sh`: smoke-tests Seed 2.1 Pro and Seed 2.1 Evolving through Ark's Anthropic Messages API compatibility endpoint.
- `runtime/`: validates Claude Code interactive and headless modes.
- `agent-sdk/`: wraps Claude Code headless execution as a programmable Agent SDK-style interface.
- `product-shell/`: exposes a local HTTP product shell that delegates work to the Agent SDK-style PoC.
- `AGENTS.md` / `AGENTS.zh-CN.md`: bilingual bootstrap guides for coding agents.

### Requirements

- `python3`
- `curl`
- `ARK_API_KEY` or `VOLCENGINE_API_KEY`
- Claude Code binary, default path: `vendor/native/darwin-arm64/package/claude`

This repository does not commit `vendor/`, the Claude Code binary, or real API keys. Install the binary before first use:

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
bash scripts/install_claude_code.sh
```

### API Path

Claude Code natively follows the Anthropic Messages API contract. This repository points Claude Code's `ANTHROPIC_*` environment variables to Volcengine Ark:

```text
Claude Code
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> Ark endpoint <your-seed-evolving-endpoint-id>
  -> Seed Evolving
```

Key environment variables:

```bash
export ARK_API_KEY="your-ark-api-key"
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible"
export ANTHROPIC_API_KEY="$ARK_API_KEY"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_MODEL="<your-seed-evolving-endpoint-id>"
export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

Important: do not include `/v1/messages` in `ANTHROPIC_BASE_URL`; Claude Code appends that path itself.

### Test Ark Messages API

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash scripts/test_seed_models.sh
```

Default endpoints:

- `SEED_21_PRO_MODEL=<your-seed-pro-endpoint-id>`
- `SEED_21_EVOLVING_MODEL=<your-seed-evolving-endpoint-id>`

Override the endpoints if your Ark account uses different endpoint IDs:

```bash
export SEED_21_PRO_MODEL="<your-seed-2.1-pro-endpoint-id>"
export SEED_21_EVOLVING_MODEL="<your-seed-2.1-evolving-endpoint-id>"
bash scripts/test_seed_models.sh
```

### Integration Modes

#### 1. Interactive CLI

Use this path when a human wants to operate Claude Code in a terminal.

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

#### 2. CLI / Headless

Use this path for automation, smoke tests, CI-like calls, and JSON output.

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "Explain what model you are in one sentence and output OK."
```

#### 3. Agent SDK-Style

Use this path when another Python process should own orchestration, retries, queueing, and result parsing.

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "Read README.md and summarize the current PoC integration modes."
```

#### 4. Product Shell

Use this path when you want a Web/backend/product surface in front of Claude Code.

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

Call it from another terminal:

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"Explain in one sentence how this product shell connects to seed-evolving."}' \
  | python3 -m json.tool
```

### Local Checks

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
python3 -m py_compile agent-sdk/seed_evolving_agent.py product-shell/server.py
bash -n runtime/run_seed_evolving_messages_api.sh runtime/run_interactive_messages_api.sh scripts/install_claude_code.sh scripts/test_seed_models.sh
```

### Safety Rules

- Do not commit `vendor/`, `.env`, real API keys, runtime logs, or local caches.
- Do not expose real API keys in README files, scripts, commit messages, or terminal output.
- Do not modify global Claude Code, Anthropic, or shell configuration unless explicitly requested.
- Keep normal Claude Code usage on Ark Anthropic Messages API only.

[Back to language switch](#claude-code-on-volcengine-ark)
