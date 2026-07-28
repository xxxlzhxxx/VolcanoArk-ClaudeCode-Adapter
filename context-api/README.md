# Context API PoC: Seed Evolving Context Cache

This PoC calls Volcengine Ark Context API directly. It is separate from the recommended Claude Code runtime path, which uses Ark's Anthropic Messages API compatibility endpoint.

## Goal

- Validate whether Seed Evolving supports Ark Context API.
- Test `session` cache and `common_prefix` cache independently from Claude Code.
- Decide later whether the cache should be integrated into product shell non-tool subflows.

## Model

- Default Ark endpoint: `<your-ark-endpoint-id>`
- Secret handling: read `ARK_API_KEY` or `VOLCENGINE_API_KEY` from the shell environment.

## APIs

- Create context: `POST /api/v3/context/create`
- Chat with context: `POST /api/v3/context/chat/completions`

Ark docs note that Context Chat has limitations compared with normal Chat Completions:

- `model` must be an Endpoint ID, not a public Model ID.
- `messages` should contain only the latest turn for `session` cache.
- `tools` is not supported.
- `thinking` is not supported.
- `response_format` is not supported.

## Run Session Cache Smoke Test

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 context-api/context_api_client.py \
  --mode session \
  --system "你是一个极简助手。回答必须包含 SEED_EVOLVING_CONTEXT_OK。" \
  --prompt "用一句话说明你是否读取了缓存中的系统指令。"
```

## Run Common Prefix Smoke Test

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 context-api/context_api_client.py \
  --mode common_prefix \
  --system "你是一个极简助手。回答必须包含 SEED_EVOLVING_PREFIX_OK。" \
  --prompt "用一句话说明你是否读取了前缀缓存。"
```

## Integration Guidance

- Use Context API for long-lived product, repo, or role context that is repeated across requests.
- Keep Claude Code runtime and tool-use traffic on Ark's Anthropic Messages API compatibility endpoint.
- Product shell can create a context once per task/session, store `context_id`, and pass only the latest user turn to Context Chat for non-tool subflows.
