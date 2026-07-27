# Runtime PoC: Claude Code on Seed Evolving

This PoC treats the vendored Claude Code binary as the runtime and routes its Anthropic Messages API traffic to Volcengine Ark through `../proxy/anthropic_ark_proxy.py`.

## Goal

- Validate Claude Code headless mode against Seed Evolving.
- Keep the Claude Code runtime unchanged.
- Reuse the existing Anthropic-to-Ark compatibility proxy.

## Model

- Default Ark endpoint: `<your-ark-endpoint-id>`
- Source: `/Users/bytedance/WorkSpace/LLM_env.md`
- Secret handling: read `ARK_API_KEY` or `VOLCENGINE_API_KEY` from the shell environment.

## Run

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_headless.sh "用一句话说明你是什么模型，并输出 OK。"
```

## What It Proves

- Claude Code can be launched as the agent runtime.
- The local proxy can make Claude Code call Seed Evolving instead of Anthropic-hosted models.
- This path is suitable for CLI automation, CI jobs, and simple backend task runners.

## Limits

- This does not add a custom product UI.
- This does not use the official Python or TypeScript Agent SDK package directly.
- Claude Code tool-use compatibility depends on the proxy mapping in `../proxy/anthropic_ark_proxy.py`.
