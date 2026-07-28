#!/usr/bin/env python3
"""Programmable Claude Code agent wrapper routed to Seed Evolving."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
CLAUDE_BIN = ROOT_DIR / "vendor" / "native" / "darwin-arm64" / "package" / "claude"
ARK_MESSAGES_BASE_URL = "https://ark.cn-beijing.volces.com/api/compatible"


class SeedEvolvingAgent:
    """Small adapter around Claude Code headless execution."""

    def __init__(self, model: str | None = None, cwd: Path | None = None) -> None:
        self.model = model
        self.cwd = cwd or ROOT_DIR

    def run(self, prompt: str, timeout_seconds: int = 900) -> dict[str, Any]:
        env = os.environ.copy()
        api_key = env.get("ARK_API_KEY") or env.get("VOLCENGINE_API_KEY")
        if not api_key:
            return {
                "ok": False,
                "model": self.model,
                "error": "Missing ARK_API_KEY or VOLCENGINE_API_KEY.",
            }

        model = self.model or env.get("ANTHROPIC_MODEL") or env.get("ARK_MODEL") or env.get("SEED_21_EVOLVING_MODEL")
        if not model:
            return {
                "ok": False,
                "model": None,
                "error": "Missing ANTHROPIC_MODEL, ARK_MODEL, or SEED_21_EVOLVING_MODEL.",
            }

        claude_bin = Path(env.get("CLAUDE_BIN", CLAUDE_BIN))
        if not claude_bin.exists():
            return {
                "ok": False,
                "model": model,
                "error": f"Claude binary does not exist: {claude_bin}",
            }
        if not os.access(claude_bin, os.X_OK):
            return {
                "ok": False,
                "model": model,
                "error": f"Claude binary is not executable: {claude_bin}",
            }

        env.setdefault("ANTHROPIC_BASE_URL", ARK_MESSAGES_BASE_URL)
        env.setdefault("ANTHROPIC_API_KEY", api_key)
        env.setdefault("ANTHROPIC_AUTH_TOKEN", env["ANTHROPIC_API_KEY"])
        env["ANTHROPIC_MODEL"] = model
        env["ANTHROPIC_SMALL_FAST_MODEL"] = model
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = model
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model
        env.setdefault("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1")

        cmd = [
            str(claude_bin),
            "-p",
            prompt,
            "--output-format",
            "json",
        ]
        completed = subprocess.run(
            cmd,
            cwd=self.cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )

        if completed.returncode != 0:
            return {
                "ok": False,
                "model": model,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }

        try:
            raw: Any = json.loads(completed.stdout)
        except json.JSONDecodeError:
            raw = {"text": completed.stdout}

        return {
            "ok": True,
            "model": model,
            "raw": raw,
            "stderr": completed.stderr,
        }


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip() or "用一句话说明你是什么模型，并输出 OK。"
    result = SeedEvolvingAgent().run(prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
