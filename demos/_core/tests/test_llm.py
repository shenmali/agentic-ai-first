import pytest

from _core.llm import LLMClient, LLMResponse


class _FakeMessage:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message):
        self.message = message


class _FakeUsage:
    def __init__(self, p, c):
        self.prompt_tokens = p
        self.completion_tokens = c


class _FakeResponse:
    def __init__(self, content, tool_calls, p, c):
        self.choices = [_FakeChoice(_FakeMessage(content, tool_calls))]
        self.usage = _FakeUsage(p, c)


class _FakeCompletions:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeOpenAI:
    def __init__(self, response):
        self.chat = type("C", (), {"completions": _FakeCompletions(response)})()


def test_llm_client_requires_key():
    with pytest.raises(ValueError):
        LLMClient(api_key="", model="openai/gpt-4o-mini")


def test_llm_client_parses_content_and_usage():
    client = LLMClient(api_key="test-key", model="openai/gpt-4o-mini")
    client._client = _FakeOpenAI(_FakeResponse("hello", None, 12, 7))
    resp = client.chat([{"role": "user", "content": "hi"}])
    assert isinstance(resp, LLMResponse)
    assert resp.content == "hello"
    assert resp.prompt_tokens == 12
    assert resp.completion_tokens == 7
    assert resp.tool_calls == []


def test_llm_client_parses_tool_calls():
    tc = type("TC", (), {
        "id": "call_1",
        "function": type("F", (), {"name": "calculator", "arguments": '{"expression":"2+2"}'})(),
    })()
    client = LLMClient(api_key="test-key", model="openai/gpt-4o-mini")
    client._client = _FakeOpenAI(_FakeResponse(None, [tc], 5, 5))
    resp = client.chat([{"role": "user", "content": "calc"}], tools=[{"type": "function"}])
    assert resp.tool_calls[0]["name"] == "calculator"
    assert resp.tool_calls[0]["arguments"] == '{"expression":"2+2"}'
