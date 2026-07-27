#!/usr/bin/env python3
"""Anthropic Messages API proxy backed by Volcengine Ark chat completions."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "<your-ark-endpoint-id>"


class ProxyConfig:
    def __init__(self) -> None:
        self.ark_base_url = os.environ.get("ARK_BASE_URL", DEFAULT_ARK_BASE_URL).rstrip("/")
        self.ark_api_key = os.environ.get("ARK_API_KEY") or os.environ.get("VOLCENGINE_API_KEY")
        self.default_model = os.environ.get("ARK_MODEL") or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
        self.pass_through_model = os.environ.get("ARK_PASSTHROUGH_MODEL") == "1"
        self.timeout = float(os.environ.get("ARK_TIMEOUT_SECONDS", "600"))


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                parts.append(json.dumps(block, ensure_ascii=False))
                continue
            block_type = block.get("type")
            if block_type == "text":
                parts.append(str(block.get("text", "")))
            elif block_type == "tool_result":
                result = block.get("content", "")
                if isinstance(result, list):
                    parts.append(_content_to_text(result))
                else:
                    parts.append(str(result))
            elif block_type == "image":
                parts.append("[image omitted: Ark chat completions proxy does not forward Anthropic image blocks]")
            else:
                parts.append(json.dumps(block, ensure_ascii=False))
        return "\n".join(part for part in parts if part)
    return json.dumps(content, ensure_ascii=False)


def anthropic_to_openai_messages(request_body: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    system = request_body.get("system")
    if system:
        messages.append({"role": "system", "content": _content_to_text(system)})

    for message in request_body.get("messages", []):
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, list):
            text_blocks: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for block in content:
                if not isinstance(block, dict):
                    text_blocks.append(str(block))
                    continue
                block_type = block.get("type")
                if block_type == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id") or f"toolu_{uuid.uuid4().hex}",
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                            },
                        }
                    )
                elif block_type == "tool_result":
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id", ""),
                            "content": _content_to_text(block.get("content", "")),
                        }
                    )
                else:
                    text = _content_to_text([block])
                    if text:
                        text_blocks.append(text)
            if role == "assistant" and tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "\n".join(text_blocks) or None,
                        "tool_calls": tool_calls,
                    }
                )
            elif text_blocks:
                messages.append({"role": role, "content": "\n".join(text_blocks)})
        else:
            messages.append({"role": role, "content": _content_to_text(content)})
    return messages


def anthropic_tools_to_openai(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    converted = []
    for tool in tools:
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
        )
    return converted


def build_ark_request(request_body: dict[str, Any], config: ProxyConfig, stream: bool) -> dict[str, Any]:
    model = request_body.get("model") if config.pass_through_model else config.default_model
    payload: dict[str, Any] = {
        "model": model or config.default_model,
        "messages": anthropic_to_openai_messages(request_body),
        "stream": stream,
    }
    if request_body.get("max_tokens") is not None:
        payload["max_tokens"] = request_body["max_tokens"]
    if request_body.get("temperature") is not None:
        payload["temperature"] = request_body["temperature"]
    tools = anthropic_tools_to_openai(request_body.get("tools"))
    if tools:
        payload["tools"] = tools
        tool_choice = request_body.get("tool_choice")
        if isinstance(tool_choice, dict):
            choice_type = tool_choice.get("type")
            if choice_type == "auto":
                payload["tool_choice"] = "auto"
            elif choice_type == "any":
                payload["tool_choice"] = "required"
            elif choice_type == "tool" and tool_choice.get("name"):
                payload["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice["name"]},
                }
    return payload


def openai_to_anthropic_response(openai_body: dict[str, Any], model: str) -> dict[str, Any]:
    choice = (openai_body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content: list[dict[str, Any]] = []
    text = message.get("content")
    if text:
        content.append({"type": "text", "text": text})
    for tool_call in message.get("tool_calls") or []:
        function = tool_call.get("function") or {}
        arguments = function.get("arguments") or "{}"
        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError:
            parsed_arguments = {"_raw": arguments}
        content.append(
            {
                "type": "tool_use",
                "id": tool_call.get("id") or f"toolu_{uuid.uuid4().hex}",
                "name": function.get("name", ""),
                "input": parsed_arguments,
            }
        )

    finish_reason = choice.get("finish_reason")
    stop_reason = "tool_use" if message.get("tool_calls") else "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"

    usage = openai_body.get("usage") or {}
    return {
        "id": openai_body.get("id") or f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content or [{"type": "text", "text": ""}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


def sse(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


def anthropic_error(status_code: int, message: str) -> dict[str, Any]:
    return {
        "type": "error",
        "error": {
            "type": "api_error" if status_code >= 500 else "invalid_request_error",
            "message": message,
        },
    }


class AnthropicArkProxy(BaseHTTPRequestHandler):
    server_version = "AnthropicArkProxy/0.1"

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in {"/health", "/healthz"}:
            self._write_json({"ok": True, "proxy": "anthropic-ark"})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in {"/v1/messages/count_tokens", "/messages/count_tokens"}:
            self._count_tokens()
            return
        if path not in {"/v1/messages", "/messages"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            request_body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            self._write_json(anthropic_error(400, f"Invalid JSON: {exc}"), status=400)
            return

        config: ProxyConfig = self.server.config  # type: ignore[attr-defined]
        if not config.ark_api_key:
            self._write_json(anthropic_error(401, "Missing ARK_API_KEY or VOLCENGINE_API_KEY"), status=401)
            return

        stream = bool(request_body.get("stream"))
        ark_payload = build_ark_request(request_body, config, stream=stream)
        if stream:
            self._stream_ark(request_body, ark_payload, config)
        else:
            self._complete_ark(ark_payload, config)

    def _count_tokens(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            request_body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            self._write_json(anthropic_error(400, f"Invalid JSON: {exc}"), status=400)
            return
        text = _content_to_text(request_body.get("system", ""))
        for message in request_body.get("messages", []):
            text += "\n" + _content_to_text(message.get("content", ""))
        # Cheap local estimate to satisfy Claude Code preflight calls.
        self._write_json({"input_tokens": max(1, len(text) // 4)})

    def _complete_ark(self, ark_payload: dict[str, Any], config: ProxyConfig) -> None:
        try:
            openai_body = self._ark_post(ark_payload, config)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            self._write_json(anthropic_error(exc.code, body), status=exc.code)
            return
        except Exception as exc:  # noqa: BLE001 - surface proxy failures as API errors.
            self._write_json(anthropic_error(502, str(exc)), status=502)
            return
        self._write_json(openai_to_anthropic_response(openai_body, ark_payload["model"]))

    def _stream_ark(self, request_body: dict[str, Any], ark_payload: dict[str, Any], config: ProxyConfig) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-cache")
        self.end_headers()
        message_id = f"msg_{uuid.uuid4().hex}"
        self.wfile.write(
            sse(
                "message_start",
                {
                    "type": "message_start",
                    "message": {
                        "id": message_id,
                        "type": "message",
                        "role": "assistant",
                        "model": ark_payload["model"],
                        "content": [],
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                },
            )
        )
        self.wfile.write(sse("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}))
        try:
            req = self._build_request(ark_payload, config)
            with urllib.request.urlopen(req, timeout=config.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = ((chunk.get("choices") or [{}])[0].get("delta") or {}).get("content")
                    if delta:
                        self.wfile.write(sse("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": delta}}))
                        self.wfile.flush()
        except Exception as exc:  # noqa: BLE001
            self.wfile.write(sse("error", anthropic_error(502, str(exc))))
        self.wfile.write(sse("content_block_stop", {"type": "content_block_stop", "index": 0}))
        self.wfile.write(sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 0}}))
        self.wfile.write(sse("message_stop", {"type": "message_stop"}))
        self.wfile.flush()

    def _ark_post(self, payload: dict[str, Any], config: ProxyConfig) -> dict[str, Any]:
        req = self._build_request(payload, config)
        with urllib.request.urlopen(req, timeout=config.timeout) as response:
            return json.loads(response.read())

    def _build_request(self, payload: dict[str, Any], config: ProxyConfig) -> urllib.request.Request:
        return urllib.request.Request(
            f"{config.ark_base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "authorization": f"Bearer {config.ark_api_key}",
                "content-type": "application/json",
                "accept": "text/event-stream" if payload.get("stream") else "application/json",
            },
            method="POST",
        )

    def _write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), fmt % args))


def run(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), AnthropicArkProxy)
    server.config = ProxyConfig()  # type: ignore[attr-defined]
    print(f"anthropic-ark proxy listening on http://{host}:{port}", flush=True)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("CLAUDE_ARK_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CLAUDE_ARK_PORT", "8011")))
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
