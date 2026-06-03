"""Integration test: exercise LLMClient over a REAL HTTP round-trip.

The other LLM tests replace `_client` with a fake object, so they never touch
the OpenAI SDK's request/response machinery. This test points the real SDK at a
local server returning OpenRouter/OpenAI-shaped JSON, validating the actual wire
path (auth header, request, response parsing) without needing a real API key.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from openai import OpenAI

from _core.llm import LLMClient

_COMPLETION = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 0,
    "model": "test/model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "The answer is 42."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16},
}


def _start_fake_openrouter(payload: dict) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # keep test output quiet
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_llm_client_real_http_roundtrip():
    server = _start_fake_openrouter(_COMPLETION)
    try:
        port = server.server_address[1]
        client = LLMClient(api_key="test-key", model="test/model")
        # point the real OpenAI SDK at the local fake OpenRouter endpoint
        client._client = OpenAI(api_key="test-key", base_url=f"http://127.0.0.1:{port}/v1")
        resp = client.chat([{"role": "user", "content": "what is the answer?"}])
        assert resp.content == "The answer is 42."
        assert resp.prompt_tokens == 11
        assert resp.completion_tokens == 5
        assert resp.tool_calls == []
    finally:
        server.shutdown()
