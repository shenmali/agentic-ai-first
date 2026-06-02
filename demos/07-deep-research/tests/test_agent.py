from _core.llm import LLMResponse
from agent import DeepResearchAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def _fake_search(query):
    return [{"title": f"Title for {query}", "body": "snippet", "url": "https://example.com"}]


def test_deep_research_plans_searches_and_cites():
    scripted = _ScriptedLLM([
        LLMResponse(
            content='["sub-question one", "sub-question two"]',
            prompt_tokens=10,
            completion_tokens=5,
        ),
        LLMResponse(content="A brief citing [1] and [2].", prompt_tokens=30, completion_tokens=20),
    ])
    agent = DeepResearchAgent(llm=scripted, search_fn=_fake_search)
    steps = list(agent.run("small language models"))
    actions = [s for s in steps if s.kind == "action"]
    assert len(actions) == 2          # one search per sub-question
    final = steps[-1]
    assert final.kind == "final"
    assert "### Sources" in final.content
    assert "[1]" in final.content


def test_app_builds():
    import app

    assert app.demo is not None
