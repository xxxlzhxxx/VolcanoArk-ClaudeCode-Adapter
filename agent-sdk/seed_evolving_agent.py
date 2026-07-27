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
CLAUDE_RUNNER = ROOT_DIR / "scripts" / "run_with_ark.sh"
SEED_EVOLVING_MODEL = "<your-ark-endpoint-id>"


class SeedEvolvingAgent:
    """Small adapter around Claude Code headless execution."""

    def __init__(self, model: str = SEED_EVOLVING_MODEL, cwd: Path | None = None) -> None:
        self.model = model
        self.cwd = cwd or ROOT_DIR

    def run(self, prompt: str, timeout_seconds: int = 900) -> dict[str, Any]:
        env = os.environ.copy()
        env["ARK_MODEL"] = self.model
        env["ANTHROPIC_MODEL"] = self.model
        env["ANTHROPIC_SMALL_FAST_MODEL"] = self.model
        env.setdefault("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1")

        if not (env.get("ARK_API_KEY") or env.get("VOLCENGINE_API_KEY")):
            return {
                "ok": False,
                "model": self.model,
                "error": "Missing ARK_API_KEY or VOLCENGINE_API_KEY.",
            }

        cmd = [
            "bash",
            str(CLAUDE_RUNNER),
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
                "model": self.model,
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
            "model": self.model,
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
