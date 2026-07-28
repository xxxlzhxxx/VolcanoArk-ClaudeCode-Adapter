# Agent SDK PoC: Programmable Seed Evolving Agent

This PoC wraps Claude Code headless execution as a programmable agent interface. It uses the CLI surface of Claude Code's Agent SDK style flow and routes model traffic directly through Ark's Anthropic Messages API compatibility endpoint.

## Goal

- Provide a small programmatic API for invoking Claude Code with Seed Evolving.
- Keep the implementation independent from product UI concerns.
- Make it easy to swap the wrapper with the official Python or TypeScript Agent SDK package later.

## Model

- Default Ark endpoint: `<your-ark-endpoint-id>`
- Secret handling: read `ARK_API_KEY` or `VOLCENGINE_API_KEY` from the shell environment.

## Run

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 agent-sdk/seed_evolving_agent.py "阅读 README.md，总结当前 PoC 的接入方式。"
```

## API Shape

`SeedEvolvingAgent.run(prompt)` returns:

```python
{
    "ok": True,
    "model": "<your-ark-endpoint-id>",
    "raw": {...}
}
```

If Claude Code exits with an error, it returns `ok=False` with stderr and exit code.

## What It Proves

- The agent can be embedded in another Python process.
- The caller can own orchestration, retries, queueing, and result parsing.
- The model routing stays centralized in Claude Code's `ANTHROPIC_*` environment variables.
