import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tools import ToolRegistry
from _core.tracer import Step

SUMMARIZE_PROMPT = "Summarize the search results to answer the user's query in 2-3 sentences."


class PipelineAgent:
    """A fixed two-stage pipeline: web_search -> LLM summarize. Deterministic
    structure makes the trace ideal for demonstrating observability."""

    def __init__(self, llm: LLMClient, tools: ToolRegistry):
        self.llm = llm
        self.tools = tools

    def run(self, query: str) -> Iterator[Step]:
        yield Step(kind="action", content=f"web_search({query!r})")
        results = self.tools.execute("web_search", {"query": query})
        yield Step(kind="observation", content=results)

        start = time.monotonic()
        resp = self.llm.chat(
            [
                {"role": "system", "content": SUMMARIZE_PROMPT},
                {"role": "user", "content": f"Query: {query}\nResults:\n{results}"},
            ]
        )
        latency = int((time.monotonic() - start) * 1000)
        cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
        yield Step(
            kind="final",
            content=resp.content or "",
            tokens=resp.prompt_tokens + resp.completion_tokens,
            cost_usd=cost,
            latency_ms=latency,
        )
