# Claude Code 二次开发与火山方舟接入指南

本文说明 Claude Code 二次开发的几种常见形式、模型与 Claude Code binary 的层级关系，以及如何使用本仓库通过火山方舟 Anthropic Messages API 兼容入口接入 Seed Evolving。

GitHub 仓库：

```text
git@github.com:xxxlzhxxx/VolcanoArk-ClaudeCode-Adapter.git
```

## 1. 核心结论

- Claude Code binary 是闭源/专有可执行程序，内部包含 agent loop、工具调度、上下文组织、权限交互、TUI/headless runtime 和 Anthropic Messages API client 行为。
- 常规二次开发不能修改 Claude Code 内部 agent loop，只能在 binary 外层做接入、封装、编排、产品化和工程化。
- 本仓库不推荐本地协议转换代理，只推荐直连火山方舟 Anthropic Messages API 兼容入口。
- 三个主要接入入口 `Interactive CLI`、`CLI/headless`、`Agent SDK-style` 都依赖同一个 Claude Code binary。
- 火山方舟模型以 endpoint id 形式传给 Claude Code，例如 Seed Evolving 默认是 `<your-ark-endpoint-id>`。

## 2. Claude Code 二次开发的几种形式

| 形式 | 是否改 Claude Code 内核 | 适用场景 | 本仓库示例 |
|---|---:|---|---|
| 原生 Claude Code | 否 | 直接运行官方 binary，人工 coding session | `vendor/native/darwin-arm64/package/claude` |
| Interactive CLI | 否 | 在终端里交互式使用 Claude Code，但模型流量走火山方舟 | `runtime/run_interactive_messages_api.sh` |
| CLI/headless | 否 | 自动化任务、smoke test、CI-like 调用、JSON 输出、缓存统计 | `runtime/run_seed_evolving_messages_api.sh` |
| Agent SDK-style wrapper | 否 | 用 Python 把 Claude Code headless 包装成可编程接口 | `agent-sdk/seed_evolving_agent.py` |
| Product shell | 否 | 在 Claude Code 前面套 HTTP/API/产品后端 | `product-shell/server.py` |
| Skills / MCP / Hooks | 否 | 扩展工具、上下文注入、外部系统集成、流程钩子 | 可在现有入口基础上继续扩展 |

## 3. 层级关系

```text
Product / Automation / Human Operator
  |
  |-- Interactive CLI script
  |     -> runtime/run_interactive_messages_api.sh
  |
  |-- CLI/headless script
  |     -> runtime/run_seed_evolving_messages_api.sh
  |
  |-- Agent SDK-style Python wrapper
  |     -> agent-sdk/seed_evolving_agent.py
  |
  |-- Product shell
        -> product-shell/server.py
        -> agent-sdk/seed_evolving_agent.py

All Claude Code paths above
  -> Claude Code binary
  -> Anthropic Messages API contract
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> Ark endpoint <your-ark-endpoint-id>
  -> Seed Evolving model
```

## 4. 模型、API 与 binary 的关系

Claude Code binary 原生按 Anthropic Messages API 的语义工作。接入火山方舟时，不需要改 binary，也不需要本地代理，只需要把 Claude Code 的 Anthropic 环境变量指向方舟兼容入口。

关键关系：

```text
Claude Code binary
  reads ANTHROPIC_BASE_URL
  reads ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN
  reads ANTHROPIC_MODEL and default model variables
  sends request to ${ANTHROPIC_BASE_URL}/v1/messages

Volcengine Ark
  receives Anthropic-compatible Messages API request
  maps model field to Ark endpoint id
  runs Seed Evolving endpoint
```

推荐环境变量：

```bash
export ARK_API_KEY="your-ark-api-key"

export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible"
export ANTHROPIC_API_KEY="$ARK_API_KEY"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"

export ANTHROPIC_MODEL="<your-ark-endpoint-id>"
export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL"

export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

注意：

- `ANTHROPIC_BASE_URL` 只写到 `/api/compatible`，不要带 `/v1/messages`。
- Claude Code 会自动请求 `${ANTHROPIC_BASE_URL}/v1/messages`。
- `ANTHROPIC_MODEL` 填火山方舟 endpoint id，不填 Claude 官方模型名。
- 不要把真实 API key 写入文档、代码、`.env.example` 或 commit。

## 5. 使用本 GitHub 仓库接入火山方舟

### 5.1 Clone 仓库

```bash
git clone git@github.com:xxxlzhxxx/VolcanoArk-ClaudeCode-Adapter.git
cd VolcanoArk-ClaudeCode-Adapter
```

如果是在当前工作区：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
```

### 5.2 安装 Claude Code binary

本仓库不提交 `vendor/` 和 Claude Code binary。首次使用先执行：

```bash
bash scripts/install_claude_code.sh
```

默认安装位置：

```text
vendor/native/darwin-arm64/package/claude
```

验证：

```bash
./vendor/native/darwin-arm64/package/claude --help
```

更完整安装说明见 `INSTALL_CLAUDE_CODE.zh-CN.md`。

### 5.3 配置火山方舟 API Key

```bash
export ARK_API_KEY="your-ark-api-key"
```

如果账号使用不同 endpoint，可以覆盖：

```bash
export ANTHROPIC_MODEL="<your-ark-endpoint-id>"
export SEED_21_EVOLVING_MODEL="<your-ark-endpoint-id>"
```

### 5.4 先测试方舟 Messages API

```bash
bash scripts/test_seed_models.sh
```

这个脚本直接请求：

```text
https://ark.cn-beijing.volces.com/api/compatible/v1/messages
```

用于确认 API key、endpoint id、Messages API 兼容入口可用。

## 6. 三种主要入口怎么用

### 6.1 Interactive CLI

适合人工在终端中使用 Claude Code。

```bash
export ARK_API_KEY="your-ark-api-key"
bash runtime/run_interactive_messages_api.sh
```

脚本会自动设置 `ANTHROPIC_BASE_URL`、`ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL` 等变量，然后启动 Claude Code TUI。

### 6.2 CLI/headless

适合自动化调用、脚本任务、JSON 输出和缓存统计。

```bash
export ARK_API_KEY="your-ark-api-key"
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

底层等价于：

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "用一句话说明你是什么模型，并输出 OK。" \
  --output-format json
```

### 6.3 Agent SDK-style

适合被 Python 工作流、队列任务或产品后端调用。

```bash
export ARK_API_KEY="your-ark-api-key"
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

核心代码在 `SeedEvolvingAgent.run(prompt)`：

```text
Python caller
  -> SeedEvolvingAgent.run(prompt)
  -> subprocess.run([claude, -p, prompt, --output-format, json])
  -> Claude Code binary
  -> Ark Messages API
```

## 7. Product Shell

Product shell 是在 Agent SDK-style 之上再封一层 HTTP 服务：

```bash
export ARK_API_KEY="your-ark-api-key"
python3 product-shell/server.py
```

调用：

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

Product shell 仍然复用 Claude Code binary，并通过 Ark Anthropic Messages API 兼容入口访问 Seed Evolving。它不是新的模型协议层，只是在 Messages API 接入路径外层增加 HTTP 服务边界。

## 8. 缓存命中率监控

Claude Code headless 支持 `stream-json`，但必须搭配 `--verbose`：

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "阅读 README.md，总结当前项目状态" \
  --output-format stream-json \
  --verbose \
  --exclude-dynamic-system-prompt-sections
```

关注字段：

```text
usage.input_tokens
usage.cache_creation_input_tokens
usage.cache_read_input_tokens
usage.output_tokens
```

命中率公式：

```text
cache_hit_rate =
  cache_read_input_tokens /
  (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)
```

## 9. 本地验证

不调用外部模型的静态检查：

```bash
python3 -m py_compile agent-sdk/seed_evolving_agent.py product-shell/server.py
bash -n runtime/run_seed_evolving_messages_api.sh runtime/run_interactive_messages_api.sh scripts/install_claude_code.sh scripts/test_seed_models.sh
```

调用火山方舟的 smoke test：

```bash
export ARK_API_KEY="your-ark-api-key"
bash runtime/run_seed_evolving_messages_api.sh "只输出 OK"
```

## 10. 安全与边界

- 不提交 `vendor/`、`.env`、真实 API key、运行日志和本地缓存。
- 不在聊天、终端总结、README 或 commit message 中暴露真实 API key。
- 不修改全局 Claude Code、Anthropic 或 shell 配置，除非用户明确要求。
- 不新增其他协议路径；普通 Claude Code 使用统一保持 Ark Anthropic Messages API only。
- 对 Claude Code 二次开发主要发生在外层入口、工具、MCP、Skills、Hooks、产品 shell 和调度系统中，不发生在闭源 binary 内部。
