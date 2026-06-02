from _core.llm import LLMResponse
from _core.tools import Tool, ToolRegistry
from agent import ReActAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def _echo_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="echo",
            description="echo the input",
            parameters={
                "type": "object",
                "properties": {"x": {"type": "string"}},
                "required": ["x"],
            },
            fn=lambda x: f"echoed {x}",
        )
    )
    return reg


def test_react_agent_uses_tool_then_finalizes():
    scripted = _ScriptedLLM([
        LLMResponse(
            content="I should echo",
            tool_calls=[{"id": "1", "name": "echo", "arguments": '{"x":"hi"}'}],
            prompt_tokens=10,
            completion_tokens=5,
        ),
        LLMResponse(content="Done: echoed hi", tool_calls=[], prompt_tokens=8, completion_tokens=4),
    ])
    agent = ReActAgent(llm=scripted, tools=_echo_registry(), max_steps=5)
    steps = list(agent.run("please echo hi"))
    kinds = [s.kind for s in steps]
    assert "action" in kinds
    assert "observation" in kinds
    assert steps[-1].kind == "final"
    assert "echoed hi" in steps[-1].content


def test_react_agent_stops_at_max_steps():
    loop = LLMResponse(
        content="thinking",
        tool_calls=[{"id": "1", "name": "echo", "arguments": '{"x":"again"}'}],
        prompt_tokens=1,
        completion_tokens=1,
    )
    scripted = _ScriptedLLM([loop] * 10)
    agent = ReActAgent(llm=scripted, tools=_echo_registry(), max_steps=3)
    steps = list(agent.run("loop forever"))
    assert steps[-1].kind == "final"
    assert "max steps" in steps[-1].content.lower()


def test_react_agent_recovers_from_bad_tool_json():
    scripted = _ScriptedLLM([
        LLMResponse(
            content="calling tool",
            tool_calls=[{"id": "1", "name": "echo", "arguments": "{not valid json"}],
            prompt_tokens=1,
            completion_tokens=1,
        ),
        LLMResponse(
            content="Recovered, final answer", tool_calls=[], prompt_tokens=1, completion_tokens=1
        ),
    ])
    agent = ReActAgent(llm=scripted, tools=_echo_registry(), max_steps=5)
    steps = list(agent.run("bad json"))
    observations = [s.content for s in steps if s.kind == "observation"]
    assert any("invalid tool arguments" in o.lower() for o in observations)
    assert steps[-1].kind == "final"
    assert "Recovered" in steps[-1].content
