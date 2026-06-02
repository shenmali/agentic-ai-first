import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tracer import Step

DEFAULT_DATASET = [
    {"q": "What is the capital of France?", "ref": "Paris"},
    {"q": "What is 2 + 2?", "ref": "4"},
    {"q": "Who wrote 'Romeo and Juliet'?", "ref": "William Shakespeare"},
    {"q": "What is the chemical symbol for water?", "ref": "H2O"},
    {"q": "How many continents are there?", "ref": "7"},
]

SUT_PROMPT = "Answer the question concisely."
JUDGE_PROMPT = (
    "You are a strict grader. Given a question, a reference answer, and a candidate "
    'answer, reply with JSON {"score": 1-5, "pass": bool, "reason": str}. '
    "Output ONLY JSON."
)


class EvalHarness:
    def __init__(
        self, llm: LLMClient, dataset: list[dict] | None = None, pass_threshold: int = 4
    ):
        self.llm = llm
        self.dataset = dataset if dataset is not None else DEFAULT_DATASET
        self.pass_threshold = pass_threshold

    def _ask(self, system: str, user: str):
        start = time.monotonic()
        resp = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        latency = int((time.monotonic() - start) * 1000)
        cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
        return resp, latency, cost

    def run(self, _user_input: str = "") -> Iterator[Step]:
        scores: list[int] = []
        for case in self.dataset:
            aresp, alat, acost = self._ask(SUT_PROMPT, case["q"])
            yield Step(kind="action", content=f"Q: {case['q']}")
            yield Step(
                kind="observation",
                content=f"Answer: {aresp.content}",
                tokens=aresp.prompt_tokens + aresp.completion_tokens,
                cost_usd=acost,
                latency_ms=alat,
            )
            jresp, jlat, jcost = self._ask(
                JUDGE_PROMPT,
                f"Question: {case['q']}\nReference: {case['ref']}\nCandidate: {aresp.content}",
            )
            try:
                verdict = json.loads(jresp.content or "{}")
            except json.JSONDecodeError:
                verdict = {"score": 0, "pass": False, "reason": "unparseable judge output"}
            scores.append(int(verdict.get("score", 0)))
            yield Step(
                kind="thought",
                content=(
                    f"Judge: score={verdict.get('score')} pass={verdict.get('pass')} "
                    f"— {verdict.get('reason', '')}"
                ),
                tokens=jresp.prompt_tokens + jresp.completion_tokens,
                cost_usd=jcost,
                latency_ms=jlat,
            )

        avg = sum(scores) / len(scores) if scores else 0.0
        passed = sum(1 for s in scores if s >= self.pass_threshold)
        yield Step(
            kind="final",
            content=(
                f"Avg score: {avg:.2f}/5 · Passed {passed}/{len(scores)} "
                f"(threshold {self.pass_threshold})"
            ),
        )
