import json
import time
from collections.abc import Callable, Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tracer import Step

PLAN_PROMPT = (
    "Break the research topic into 2-4 specific sub-questions that together cover it. "
    "Output ONLY a JSON array of strings."
)
SYNTH_PROMPT = (
    "Write a concise research brief answering the topic. Cite sources inline as [n] "
    "using the provided numbered source list."
)

SearchFn = Callable[[str], list[dict]]


class DeepResearchAgent:
    def __init__(self, llm: LLMClient, search_fn: SearchFn, max_subquestions: int = 4):
        self.llm = llm
        self.search_fn = search_fn
        self.max_subquestions = max_subquestions

    def _ask(self, system: str, user: str):
        start = time.monotonic()
        resp = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        latency = int((time.monotonic() - start) * 1000)
        cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
        return resp, latency, cost

    def run(self, topic: str) -> Iterator[Step]:
        resp, lat, cost = self._ask(PLAN_PROMPT, topic)
        try:
            subqs = json.loads(resp.content or "[]")[: self.max_subquestions]
        except json.JSONDecodeError:
            subqs = [topic]
        yield Step(
            kind="thought",
            content="Sub-questions:\n" + "\n".join(f"- {q}" for q in subqs),
            tokens=resp.prompt_tokens + resp.completion_tokens,
            cost_usd=cost,
            latency_ms=lat,
        )

        sources: list[dict] = []
        for q in subqs:
            yield Step(kind="action", content=f"search: {q}")
            results = self.search_fn(q)
            ids = []
            for r in results:
                sources.append(r)
                ids.append(len(sources))
            yield Step(
                kind="observation",
                content="\n".join(
                    f"[{i}] {sources[i - 1]['title']}: {sources[i - 1].get('body', '')}"
                    for i in ids
                )
                or "No results.",
            )

        source_list = "\n".join(
            f"[{i + 1}] {s['title']} — {s.get('url', '')}" for i, s in enumerate(sources)
        )
        fresp, flat, fcost = self._ask(
            SYNTH_PROMPT, f"Topic: {topic}\nNumbered sources:\n{source_list}"
        )
        yield Step(
            kind="final",
            content=(fresp.content or "") + "\n\n### Sources\n" + source_list,
            tokens=fresp.prompt_tokens + fresp.completion_tokens,
            cost_usd=fcost,
            latency_ms=flat,
        )


def make_search_fn(tavily_key: str | None = None, max_results: int = 3) -> SearchFn:
    if tavily_key:
        import requests

        def search(query: str) -> list[dict]:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_key, "query": query, "max_results": max_results},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", ""), "body": r.get("content", ""), "url": r.get("url", "")}
                for r in data.get("results", [])
            ]

        return search

    def search(query: str) -> list[dict]:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore
        out: list[dict] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append(
                    {
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                )
        return out

    return search
