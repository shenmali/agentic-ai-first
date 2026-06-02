from _core.llm import LLMResponse
from agent import EvalHarness


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def test_eval_harness_scores_each_case_and_aggregates():
    dataset = [
        {"q": "Capital of France?", "ref": "Paris"},
        {"q": "2 + 2?", "ref": "4"},
    ]
    scripted = _ScriptedLLM([
        LLMResponse(content="Paris", prompt_tokens=3, completion_tokens=1),
        LLMResponse(
            content='{"score": 5, "pass": true, "reason": "correct"}',
            prompt_tokens=5,
            completion_tokens=3,
        ),
        LLMResponse(content="5", prompt_tokens=3, completion_tokens=1),
        LLMResponse(
            content='{"score": 1, "pass": false, "reason": "wrong"}',
            prompt_tokens=5,
            completion_tokens=3,
        ),
    ])
    harness = EvalHarness(llm=scripted, dataset=dataset, pass_threshold=4)
    steps = list(harness.run())
    assert sum(1 for s in steps if s.kind == "action") == 2
    final = steps[-1]
    assert final.kind == "final"
    assert "Passed 1/2" in final.content


def test_app_builds():
    import app

    assert app.demo is not None
