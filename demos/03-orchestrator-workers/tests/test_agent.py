from _core.llm import LLMResponse
from agent import OrchestratorAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def test_orchestrator_dispatches_workers_then_synthesizes():
    scripted = _ScriptedLLM([
        LLMResponse(
            content=(
                '[{"role": "historian", "subtask": "history of X"}, '
                '{"role": "economist", "subtask": "economics of X"}]'
            ),
            prompt_tokens=10,
            completion_tokens=5,
        ),
        LLMResponse(content="History worker output", prompt_tokens=5, completion_tokens=5),
        LLMResponse(content="Economics worker output", prompt_tokens=5, completion_tokens=5),
        LLMResponse(content="Combined synthesis", prompt_tokens=5, completion_tokens=5),
    ])
    agent = OrchestratorAgent(llm=scripted)
    steps = list(agent.run("Explain X"))
    actions = [s for s in steps if s.kind == "action"]
    assert len(actions) == 2
    assert steps[-1].kind == "final"
    assert "Combined synthesis" in steps[-1].content


def test_app_builds():
    import app

    assert app.demo is not None
