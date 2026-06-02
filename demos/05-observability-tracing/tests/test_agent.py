from _core.llm import LLMResponse
from _core.tools import Tool, ToolRegistry
from agent import PipelineAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def _fake_search_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="web_search",
            description="fake",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            fn=lambda query: f"results for {query}",
        )
    )
    return reg


def test_pipeline_searches_then_summarizes():
    scripted = _ScriptedLLM([
        LLMResponse(content="A concise summary.", prompt_tokens=20, completion_tokens=10),
    ])
    agent = PipelineAgent(llm=scripted, tools=_fake_search_registry())
    steps = list(agent.run("quantum computing"))
    kinds = [s.kind for s in steps]
    assert kinds == ["action", "observation", "final"]
    assert "results for quantum computing" in steps[1].content
    assert steps[-1].tokens == 30


def test_app_builds():
    import app

    assert app.demo is not None
