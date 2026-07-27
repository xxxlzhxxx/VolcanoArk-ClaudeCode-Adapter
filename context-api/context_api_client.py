#!/usr/bin/env python3
"""Direct Volcengine Ark Context API smoke client for Seed Evolving."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
SEED_EVOLVING_MODEL = "<your-ark-endpoint-id>"


class ArkContextClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_ARK_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def create_context(
        self,
        *,
        model: str,
        mode: str,
        system: str,
        ttl: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "mode": mode,
            "ttl": ttl,
            "messages": [{"role": "system", "content": system}],
        }
        return self._post("/context/create", payload)

    def chat(
        self,
        *,
        model: str,
        context_id: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "context_id": context_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        return self._post("/context/chat/completions", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
                "accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ark Context API error {exc.code}: {body}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("ARK_MODEL", SEED_EVOLVING_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("ARK_BASE_URL", DEFAULT_ARK_BASE_URL))
    parser.add_argument("--mode", choices=["session", "common_prefix"], default="session")
    parser.add_argument("--ttl", type=int, default=3600)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--system", default="你是一个极简助手。回答必须包含 SEED_EVOLVING_CONTEXT_OK。")
    parser.add_argument("--prompt", default="用一句话说明你是否读取了缓存中的系统指令。")
    args = parser.parse_args()

    api_key = os.environ.get("ARK_API_KEY") or os.environ.get("VOLCENGINE_API_KEY")
    if not api_key:
        print("Missing ARK_API_KEY or VOLCENGINE_API_KEY.", file=sys.stderr)
        return 1

    client = ArkContextClient(api_key=api_key, base_url=args.base_url)
    created = client.create_context(
        model=args.model,
        mode=args.mode,
        system=args.system,
        ttl=args.ttl,
    )
    context_id = created.get("id")
    if not context_id:
        print(json.dumps({"ok": False, "create_response": created}, ensure_ascii=False, indent=2))
        return 1

    chatted = client.chat(
        model=args.model,
        context_id=context_id,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "model": args.model,
                "mode": args.mode,
                "context_id": context_id,
                "create_response": created,
                "chat_response": chatted,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
