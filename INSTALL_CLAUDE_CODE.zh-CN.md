# Claude Code Binary 安装教程

本文说明如何在本仓库中准备 Claude Code binary，并让它通过火山方舟 Anthropic Messages API 兼容入口调用 Seed Evolving。

## 背景

Claude Code binary 是 Anthropic 提供的闭源/专有可执行程序。本仓库不会提交 binary 本体，也不会提交 npm tarball。

本仓库只维护：

- Claude Code 启动脚本
- 方舟 Messages API 接入配置
- CLI/headless wrapper
- Agent SDK-style wrapper
- Product shell
- 中英文 Agent 指南

因此 clone 仓库后，需要先在本地安装或准备 Claude Code binary。

## 推荐安装方式

本仓库提供了项目内安装脚本：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
bash scripts/install_claude_code.sh
```

默认安装：

```text
Claude Code version: 2.1.216
Platform: darwin-arm64
Binary path: vendor/native/darwin-arm64/package/claude
```

安装后验证：

```bash
./vendor/native/darwin-arm64/package/claude --version
```

如果版本命令不可用，也可以看帮助：

```bash
./vendor/native/darwin-arm64/package/claude --help
```

## 安装脚本做了什么

`scripts/install_claude_code.sh` 会从 npm registry 下载两个包：

```text
@anthropic-ai/claude-code
@anthropic-ai/claude-code-darwin-arm64
```

然后解压到：

```text
vendor/
vendor/native/darwin-arm64/package/claude
```

最后执行：

```bash
chmod +x vendor/native/darwin-arm64/package/claude
```

注意：`vendor/` 已被 `.gitignore` 排除，不会提交到 GitHub。

## 指定版本

默认版本在脚本中是 `2.1.216`。如需指定版本：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
CLAUDE_CODE_VERSION="2.1.216" bash scripts/install_claude_code.sh
```

## 指定平台

默认平台是 macOS arm64：

```bash
CLAUDE_CODE_PLATFORM="darwin-arm64"
```

如需为其他平台安装，需要确认 npm 上存在对应平台包，再设置：

```bash
CLAUDE_CODE_PLATFORM="<platform>" bash scripts/install_claude_code.sh
```

常见平台命名通常类似：

```text
darwin-arm64
darwin-x64
linux-x64
linux-arm64
```

实际可用平台以 npm registry 中的 `@anthropic-ai/claude-code-<platform>` 包为准。

## 配置方舟 Messages API

安装 binary 后，不要直接使用 Anthropic 官方模型配置。本仓库推荐统一设置到火山方舟 Messages API：

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

重要：

- `ANTHROPIC_BASE_URL` 不要带 `/v1/messages`。
- Claude Code 会自动请求 `${ANTHROPIC_BASE_URL}/v1/messages`。
- `ANTHROPIC_MODEL` 应该填写方舟 endpoint id，不要填写 Claude 官方模型名。
- 不要把真实 `ARK_API_KEY` 写入 README、脚本、`.env.example` 或 commit。

## 启动交互式 Claude Code

推荐使用仓库脚本，它会自动导出火山方舟 Messages API 所需的 `ANTHROPIC_*` 环境变量：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="your-ark-api-key"
bash runtime/run_interactive_messages_api.sh
```

这是普通交互式 CLI / TUI 模式，适合人工 coding session。

如果已经手工导出完整环境变量，也可以直接启动底层 binary：

```bash
./vendor/native/darwin-arm64/package/claude
```

## 启动 CLI/headless Claude Code

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

或直接运行：

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "用一句话说明你是什么模型，并输出 OK。" \
  --output-format json
```

## 实时监控缓存命中率

`stream-json` 必须搭配 `--verbose`：

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

## 常见问题

### 1. `Claude binary does not exist`

说明还没有安装 binary。执行：

```bash
bash scripts/install_claude_code.sh
```

### 2. `Claude binary is not executable`

执行：

```bash
chmod +x vendor/native/darwin-arm64/package/claude
```

### 3. `Missing ARK_API_KEY or VOLCENGINE_API_KEY`

说明没有配置方舟 key。执行：

```bash
export ARK_API_KEY="your-ark-api-key"
```

不要把真实 key 贴到聊天或提交到 Git。

### 4. `ANTHROPIC_BASE_URL` 路径错误

正确：

```bash
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible"
```

错误：

```bash
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/compatible/v1/messages"
```

### 5. clone GitHub 后没有 `vendor/`

这是预期行为。`vendor/` 被 `.gitignore` 排除，需要本地运行安装脚本。

## 安全规则

- 不提交 `vendor/`。
- 不提交 `.env`。
- 不打印真实 API Key。
- 不把真实 API Key 写进文档或代码。
- 不修改全局 Claude Code 配置，除非用户明确要求。
- 优先使用项目内环境变量和脚本。

## 快速检查清单

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code

bash scripts/install_claude_code.sh
./vendor/native/darwin-arm64/package/claude --help

export ARK_API_KEY="your-ark-api-key"
bash runtime/run_seed_evolving_messages_api.sh "只输出 OK"
```

如果命令成功返回，说明 Claude Code binary 已安装，并且已通过方舟 Messages API 接入 Seed Evolving。
