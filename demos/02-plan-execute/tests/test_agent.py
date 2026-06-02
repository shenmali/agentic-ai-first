from _core.llm import LLMResponse
from _core.tools import ToolRegistry
from agent import PlanExecuteAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def test_plan_execute_reflect_completes_in_one_round():
    scripted = _ScriptedLLM([
        LLMResponse(
            content='["Estimate area", "Compute cost"]', prompt_tokens=10, completion_tokens=5
        ),
        LLMResponse(content="Area is 12 m².", prompt_tokens=8, completion_tokens=4),
        LLMResponse(content="Cost is 300 EUR.", prompt_tokens=8, completion_tokens=4),
        LLMResponse(content='{"done": true, "feedback": ""}', prompt_tokens=6, completion_tokens=3),
    ])
    agent = PlanExecuteAgent(llm=scripted, tools=ToolRegistry(), max_rounds=2)
    steps = list(agent.run("tile a 12 m2 floor"))
    kinds = [s.kind for s in steps]
    assert kinds[0] == "thought"          # the plan
    assert kinds.count("observation") == 2  # two executed steps
    assert steps[-1].kind == "final"


def test_plan_execute_reflect_replans_when_not_done():
    scripted = _ScriptedLLM([
        LLMResponse(content='["step one"]', prompt_tokens=1, completion_tokens=1),
        LLMResponse(content="did step one", prompt_tokens=1, completion_tokens=1),
        LLMResponse(
            content='{"done": false, "feedback": "need more detail"}',
            prompt_tokens=1,
            completion_tokens=1,
        ),
        LLMResponse(content='["step one improved"]', prompt_tokens=1, completion_tokens=1),
        LLMResponse(content="did it better", prompt_tokens=1, completion_tokens=1),
        LLMResponse(content='{"done": true, "feedback": ""}', prompt_tokens=1, completion_tokens=1),
    ])
    agent = PlanExecuteAgent(llm=scripted, tools=ToolRegistry(), max_rounds=2)
    steps = list(agent.run("task"))
    thoughts = [s.content for s in steps if s.kind == "thought"]
    assert any("need more detail" in t for t in thoughts)
    assert steps[-1].kind == "final"


def test_app_builds():
    import app
    assert app.demo is not None
