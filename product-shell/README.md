# Product Shell PoC: Local HTTP Wrapper

This PoC adds a minimal product-facing shell around the Seed Evolving Claude Code runtime. It exposes a local HTTP API and delegates execution to the programmable agent PoC in `../agent-sdk/seed_evolving_agent.py`.

## Goal

- Simulate a product backend that treats Claude Code as the runtime.
- Keep orchestration outside the Claude Code binary.
- Provide a simple API surface for future Web UI, internal platform, or queue worker integration.

## Run

```bash
cd /Users/bytedance/WorkSpace/ModelPlayground/agent/claude-code
export ARK_API_KEY="..."
python3 product-shell/server.py
```

In another terminal:

```bash
curl -sS http://127.0.0.1:8021/health | python3 -m json.tool
curl -sS http://127.0.0.1:8021/run \
  -H 'content-type: application/json' \
  --data '{"prompt":"用一句话说明当前产品外壳如何接入 seed-evolving。"}' \
  | python3 -m json.tool
```

## API

- `GET /health`: returns shell health and configured model.
- `POST /run`: accepts `{"prompt": "..."}` and returns the agent result.

## What It Proves

- A product surface can call Claude Code through an internal service boundary.
- The product shell can own request validation, auth, queueing, logging, and usage metrics later.
- Model routing remains centralized through Claude Code's `ANTHROPIC_*` environment variables and Ark's Messages API compatibility endpoint.

## Security Notes

- This server binds to `127.0.0.1` by default.
- Do not expose it to a shared network without adding authentication, authorization, request quotas, audit logs, and command/tool policy controls.
