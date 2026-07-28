# AGENTS.zh-CN.md

这是给 coding agent 使用的中文启动指南。任何 agent 在本仓库开始工作前，都应该先阅读本文件，确认用户想如何使用 Claude Code，再路由到对应接入方式。

本仓库用于验证 Claude Code 接入火山方舟 Seed Evolving。默认推荐路径是方舟的 Anthropic Messages API 兼容入口：

```text
Claude Code
  -> https://ark.cn-beijing.volces.com/api/compatible/v1/messages
  -> 方舟 Endpoint <your-ark-endpoint-id>
```

除非用户明确要做协议调试，否则优先使用直连 Messages API，不优先使用本地 proxy。

## 第一步：先问用户怎么用 Claude Code

在运行命令、修改文件或索要配置前，先问用户：

```text
你这次希望如何使用 Claude Code？

1. 直接交互式使用 Claude Code
2. CLI / headless 自动化使用
3. Agent SDK-style 可编程封装
4. Product shell / HTTP 服务封装
5. 方舟 Context API 缓存实验
6. 本地 proxy / 协议调试
7. 其他自定义流程
```

如果用户不确定，推荐：

- 日常手动写代码：选 `1. 直接交互式使用 Claude Code`
- 自动化测试、缓存命中率统计、脚本化任务：选 `2. CLI / headless 自动化使用`

不要一上来让用户把 API Key 明文贴到聊天里。应该让用户在 terminal 里通过环境变量配置。

## 需要用户确认的配置

| 配置 | 是否必需 | 默认值 | 说明 |
|---|---:|---|---|
| `ARK_API_KEY` 或 `VOLCENGINE_API_KEY` | 是 | 无 | 用户应在 shell 中导出。不要打印、记录或提交。 |
| 方舟 Endpoint ID | 是 | `<your-ark-endpoint-id>` | Seed Evolving endpoint。 |
| 使用方式 | 是 | CLI/headless | 根据用户选择路由到后续章节。 |
| 是否监控缓存命中率 | 可选 | 否 | 需要时使用 `stream-json --verbose`。 |
| 是否允许修改文件 | 可选 | 先询问 | 涉及代码修改前必须确认。 |
| 是否允许 commit / push | 可选 | 先询问 | 涉及 Git 操作前必须确认。 |

如果缺少 `ARK_API_KEY`，请让用户在 terminal 中执行：

```bash
export ARK_API_KEY="your-ark-api-key"
```

不要把真实 key 写入 `.env`、`.env.example`、README、日志或 commit。

## 通用环境变量

直连方舟 Anthropic Messages API 时使用：

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

注意：

- `ANTHROPIC_BASE_URL` 不要带 `/v1/messages`，Claude Code 会自己拼接路径。
- `ANTHROPIC_MODEL` 应该填写方舟 endpoint id，不要填写 Claude 官方模型名。
- 除非用户明确要做模型路由，否则把 Claude Code 的所有模型变量都指向同一个 endpoint。

## 路由 1：直接交互式 Claude Code

适用于用户想在 terminal 里手动使用 Claude Code。

配置：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."

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

启动：

```bash
./vendor/native/darwin-arm64/package/claude
```

适合：

- 手动 coding session
- 交互式阅读代码
- 用户监督下的文件修改

限制：

- 交互式 TUI 不适合直接实时解析缓存命中率。
- 如果用户要看缓存命中率，请路由到 CLI/headless。

## 路由 2：CLI / Headless Claude Code

适用于自动化、smoke test、脚本化任务和用量统计。

推荐脚本：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

等价直接命令：

```bash
./vendor/native/darwin-arm64/package/claude \
  -p "阅读 README.md，总结当前项目如何接入 seed-evolving" \
  --output-format json
```

适合：

- 一次性验证
- CI-like 自动化
- 脚本化代码任务
- 缓存与 token 使用量统计

## 路由 2A：实时监控缓存命中率

`stream-json` 必须和 `--verbose` 一起使用，否则 Claude Code 会报错。

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

缓存命中率公式：

```text
cache_hit_rate =
  cache_read_input_tokens /
  (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)
```

重点字段：

```text
usage.input_tokens
usage.cache_creation_input_tokens
usage.cache_read_input_tokens
usage.output_tokens
```

## 路由 3：Agent SDK-style 可编程封装

适用于由 Python 进程负责调度、重试、排队和结果解析。

运行：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

适合：

- 把 Claude Code 嵌入更大的 Python 工作流
- 批量任务
- 队列驱动任务
- 后续迁移到官方 Agent SDK

当前注意：

- 这里是对 Claude Code headless 的本地 SDK-style wrapper，不是完整官方 SDK 实现。

## 路由 4：Product Shell / HTTP 服务

适用于用户想在 Claude Code 前面套一层产品后端或 Web 服务。

启动服务：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

调用：

```bash
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

适合：

- Web UI 实验
- 内部服务封装
- 后续接认证、审计、限额和任务队列

## 路由 5：方舟 Context API 缓存实验

仅当用户明确要测试方舟原生 Context API 时使用。

运行：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 context-api/context_api_client.py \
  --mode session \
  --system "你是一个极简助手。回答必须包含 SEED_EVOLVING_CONTEXT_OK。" \
  --prompt "用一句话说明你是否读取了缓存中的系统指令。"
```

适合：

- 长 system prompt
- 仓库摘要
- 产品背景缓存
- 不需要工具调用的子流程

不要把 Context API 当作默认 Claude Code runtime。Context Chat 可能不支持完整 Claude Code tool loop。

## 路由 6：本地 Proxy / 协议调试

当直连 Ark Messages API 不可用，或用户要检查协议转换时使用。

运行：

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_headless.sh "用一句话说明你是什么模型，并输出 OK。"
```

链路：

```text
Claude Code
  -> local /v1/messages proxy
  -> Ark /chat/completions
  -> Seed Evolving
```

适合：

- request / response 映射调试
- mock Anthropic Messages API
- 协议兼容性测试
- 自定义日志和未来路由实验

普通 Claude Code runtime 不要优先走这条路。直连 Messages API 更能保留 Anthropic 原生语义。

## 验证清单

单测：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Runtime smoke test：

```bash
bash runtime/run_seed_evolving_messages_api.sh "只输出 OK"
```

预期：

- 命令成功退出。
- 输出包含成功结果。
- `modelUsage` 包含 `<your-ark-endpoint-id>`。
- usage 可能包含 `cacheReadInputTokens` 等缓存字段。

## 安全规则

- 不要打印 API Key。
- 不要把真实密钥写入 `.env`、`.env.example`、README、文档、日志、commit 或终端总结。
- 不要提交 `vendor/`、`.env`、生成日志、Python cache 或本地编辑器文件。
- 除非用户明确要求，不要修改全局 Claude Code、Anthropic 或 shell 配置。
- 优先使用项目内脚本和环境变量。
- 文件编辑、commit、push、可能暴露密钥的命令都要先询问用户。
- 普通 Claude Code 使用默认走直连 Ark Messages API。
- 本地 proxy 仅用于兼容性或调试任务。

## 仓库路径

| 路径 | 用途 |
|---|---|
| `runtime/run_seed_evolving_messages_api.sh` | 直连 Ark Messages API runtime |
| `runtime/run_seed_evolving_headless.sh` | legacy 本地 proxy runtime |
| `agent-sdk/seed_evolving_agent.py` | Python SDK-style wrapper |
| `product-shell/server.py` | HTTP product shell |
| `context-api/context_api_client.py` | Ark Context API client |
| `proxy/anthropic_ark_proxy.py` | Anthropic Messages 到 Ark Chat Completions 的转换 proxy |
| `tests/test_anthropic_ark_proxy.py` | Proxy 转换单测 |
| `.env.example` | 安全环境变量占位示例 |

## 什么时候再次询问用户

以下情况必须先问用户：

- 使用方式不清楚。
- 缺少 `ARK_API_KEY` 或 endpoint id。
- 用户要缓存命中率，但选择了交互式模式。
- 用户要 push，但没有 remote 或认证。
- 命令可能修改文件或调用外部服务。
- 任务需要本指南之外的接入路径。
