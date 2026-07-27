import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proxy"))

import anthropic_ark_proxy as proxy  # noqa: E402


class AnthropicArkProxyTests(unittest.TestCase):
    def test_converts_anthropic_messages_and_tools_to_openai_shape(self) -> None:
        request = {
            "system": "You are a coding agent.",
            "messages": [
                {"role": "user", "content": "List files"},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I will inspect the workspace."},
                        {"type": "tool_use", "id": "toolu_1", "name": "ls", "input": {"path": "."}},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": "toolu_1", "content": "README.md\nsrc"}
                    ],
                },
            ],
            "tools": [
                {
                    "name": "ls",
                    "description": "list files",
                    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
                }
            ],
        }

        messages = proxy.anthropic_to_openai_messages(request)
        tools = proxy.anthropic_tools_to_openai(request["tools"])

        self.assertEqual(messages[0], {"role": "system", "content": "You are a coding agent."})
        self.assertEqual(messages[1], {"role": "user", "content": "List files"})
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["tool_calls"][0]["id"], "toolu_1")
        self.assertEqual(json.loads(messages[2]["tool_calls"][0]["function"]["arguments"]), {"path": "."})
        self.assertEqual(messages[3], {"role": "tool", "tool_call_id": "toolu_1", "content": "README.md\nsrc"})
        self.assertEqual(tools[0]["function"]["name"], "ls")

    def test_converts_openai_text_response_to_anthropic_message(self) -> None:
        response = proxy.openai_to_anthropic_response(
            {
                "id": "chatcmpl_1",
                "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            },
            "doubao-seed-2-1-pro-260628",
        )

        self.assertEqual(response["id"], "chatcmpl_1")
        self.assertEqual(response["type"], "message")
        self.assertEqual(response["content"], [{"type": "text", "text": "hello"}])
        self.assertEqual(response["stop_reason"], "end_turn")
        self.assertEqual(response["usage"], {"input_tokens": 3, "output_tokens": 2})

    def test_converts_openai_tool_call_to_anthropic_tool_use(self) -> None:
        response = proxy.openai_to_anthropic_response(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {"name": "edit", "arguments": "{\"path\":\"a.py\"}"},
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
            "doubao-seed-2-1-pro-evolving",
        )

        self.assertEqual(response["stop_reason"], "tool_use")
        self.assertEqual(
            response["content"][0],
            {"type": "tool_use", "id": "call_1", "name": "edit", "input": {"path": "a.py"}},
        )

    def test_build_request_overrides_model_by_default(self) -> None:
        config = proxy.ProxyConfig()
        config.default_model = "doubao-seed-2-1-pro-260628"
        config.pass_through_model = False

        payload = proxy.build_ark_request(
            {"model": "claude-sonnet-4-5", "max_tokens": 16, "messages": [{"role": "user", "content": "hi"}]},
            config,
            stream=False,
        )

        self.assertEqual(payload["model"], "doubao-seed-2-1-pro-260628")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
