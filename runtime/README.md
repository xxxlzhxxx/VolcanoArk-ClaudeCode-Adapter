# Runtime PoC: Claude Code on Seed Evolving

This PoC treats the vendored Claude Code binary as the runtime and connects it directly to Volcengine Ark through Ark's Anthropic Messages API compatibility endpoint.

## Goal

- Validate Claude Code interactive and headless modes against Seed Evolving.
- Keep the Claude Code runtime unchanged.
- Use the native Anthropic Messages API contract instead of protocol conversion.

## Model

- Default Ark endpoint: `<your-seed-evolving-endpoint-id>`
- Source: `/Users/bytedance/WorkSpace/LLM_env.md`
- Secret handling: read `ARK_API_KEY` or `VOLCENGINE_API_KEY` from the shell environment.

## Run Interactive CLI

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_interactive_messages_api.sh
```

This launches the native Claude Code terminal UI after exporting the Ark Messages API environment variables.

## Run CLI / Headless

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
bash runtime/run_seed_evolving_messages_api.sh "用一句话说明你是什么模型，并输出 OK。"
```

## What It Proves

- Claude Code can be launched as the agent runtime in interactive and headless modes.
- Ark's Anthropic Messages API compatibility endpoint can make Claude Code call Seed Evolving instead of Anthropic-hosted models.
- This path is suitable for CLI automation, CI jobs, and simple backend task runners.

## Limits

- This does not add a custom product UI.
- This does not use the official Python or TypeScript Agent SDK package directly.
- Claude Code compatibility depends on Ark's `/api/compatible/v1/messages` support.
