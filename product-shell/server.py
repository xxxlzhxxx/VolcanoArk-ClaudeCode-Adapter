#!/usr/bin/env python3
"""Minimal local product shell for invoking Seed Evolving through Claude Code."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
AGENT_SCRIPT = ROOT_DIR / "agent-sdk" / "seed_evolving_agent.py"
SEED_EVOLVING_MODEL = "<your-ark-endpoint-id>"


class ProductShellHandler(BaseHTTPRequestHandler):
    server_version = "SeedEvolvingProductShell/0.1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._write_json(
            {
                "ok": True,
                "shell": "seed-evolving-product-shell",
                "model": os.environ.get("ARK_MODEL", SEED_EVOLVING_MODEL),
            }
        )

    def do_POST(self) -> None:
        if self.path != "/run":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
        except ValueError as exc:
            self._write_json({"ok": False, "error": str(exc)}, status=400)
            return

        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            self._write_json({"ok": False, "error": "Missing non-empty prompt."}, status=400)
            return

        result = run_agent(prompt)
        self._write_json(result, status=200 if result.get("ok") else 502)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        return payload

    def _write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[product-shell] " + fmt % args + "\n")


def run_agent(prompt: str) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("ARK_MODEL", SEED_EVOLVING_MODEL)
    cmd = ["python3", str(AGENT_SCRIPT), prompt]
    completed = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
        timeout=int(env.get("PRODUCT_SHELL_TIMEOUT_SECONDS", "900")),
        check=False,
    )
    try:
        body = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        body = {"ok": False, "stdout": completed.stdout}

    if completed.returncode != 0:
        body.setdefault("ok", False)
        body.setdefault("exit_code", completed.returncode)
        body.setdefault("stderr", completed.stderr)
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("PRODUCT_SHELL_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PRODUCT_SHELL_PORT", "8021")))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ProductShellHandler)
    print(f"product shell listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
