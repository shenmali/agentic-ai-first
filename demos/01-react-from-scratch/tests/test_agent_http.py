"""Full ReAct loop over a REAL HTTP round-trip.

Validates the one path no other test covers: that the OpenAI SDK accepts our
tool-threaded messages (assistant-with-tool_calls + `tool` role replies) when
serialized over the wire on the second loop iteration. Uses a local fake
OpenRouter server returning a tool call, then a final answer — no real key.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from _core.llm import LLMClient
from _core.tools import Tool, ToolRegistry
from agent import ReActAgent
from openai import OpenAI


def _start_server(payloads):
    box = {"i": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            payload = payloads[min(box["i"], len(payloads) - 1)]
            box["i"] += 1
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _completion(content=None, tool_calls=None, finish="stop"):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }


def _echo_registry():
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="echo",
            description="echo",
            parameters={
                "type": "object",
                "properties": {"x": {"type": "string"}},
                "required": ["x"],
            },
            fn=lambda x: f"echoed {x}",
        )
    )
    return reg


def test_react_full_loop_over_real_http():
    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "echo", "arguments": '{"x": "hi"}'},
        }
    ]
    server = _start_server([
        _completion(content=None, tool_calls=tool_calls, finish="tool_calls"),
        _completion(content="Done: echoed hi", finish="stop"),
    ])
    try:
        port = server.server_address[1]
        llm = LLMClient(api_key="test-key", model="test/model")
        llm._client = OpenAI(api_key="test-key", base_url=f"http://127.0.0.1:{port}/v1")
        steps = list(ReActAgent(llm=llm, tools=_echo_registry(), max_steps=4).run("echo hi"))
        kinds = [s.kind for s in steps]
        assert "action" in kinds
        assert "observation" in kinds
        assert steps[-1].kind == "final"
        assert "echoed hi" in steps[-1].content
    finally:
        server.shutdown()
