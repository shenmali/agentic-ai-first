import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tools import ToolRegistry
from _core.tracer import Step

PLANNER_PROMPT = (
    "You are a planner. Given a task, output a JSON array of 2-5 short step "
    "strings that would accomplish it. Output ONLY the JSON array."
)
EXECUTOR_PROMPT = "You are an executor. Complete the given step concisely. Use a tool if it helps."
REFLECTOR_PROMPT = (
    "You are a reviewer. Given the task and the results so far, decide if the task "
    'is complete. Reply with JSON {"done": bool, "feedback": str}. Output ONLY JSON.'
)


class PlanExecuteAgent:
    def __init__(self, llm: LLMClient, tools: ToolRegistry, max_rounds: int = 2):
        self.llm = llm
        self.tools = tools
        self.max_rounds = max_rounds

    def _ask(self, system: str, user: str, use_tools: bool = False):
        start = time.monotonic()
        resp = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tools=self.tools.to_openai_schema() if use_tools else None,
        )
        latency = int((time.monotonic() - start) * 1000)
        cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
        return resp, latency, cost

    def run(self, task: str) -> Iterator[Step]:
        feedback = ""
        results: list[str] = []
        for _ in range(self.max_rounds):
            planner_input = f"Task: {task}" + (f"\nPrior feedback: {feedback}" if feedback else "")
            resp, lat, cost = self._ask(PLANNER_PROMPT, planner_input)
            try:
                plan = json.loads(resp.content or "[]")
            except json.JSONDecodeError:
                plan = [resp.content or ""]
            yield Step(
                kind="thought",
                content="Plan:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(plan)),
                tokens=resp.prompt_tokens + resp.completion_tokens,
                cost_usd=cost,
                latency_ms=lat,
            )

            results = []
            for s in plan:
                eresp, elat, ecost = self._ask(
                    EXECUTOR_PROMPT, f"Task: {task}\nStep: {s}", use_tools=True
                )
                if eresp.tool_calls:
                    for tc in eresp.tool_calls:
                        yield Step(kind="action", content=f"{tc['name']}({tc['arguments']})")
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError as e:
                            obs = f"Error: invalid tool arguments JSON: {e}"
                        else:
                            obs = self.tools.execute(tc["name"], args)
                        yield Step(kind="observation", content=obs)
                        results.append(f"{s}: {obs}")
                else:
                    yield Step(kind="action", content=f"Execute: {s}")
                    yield Step(
                        kind="observation",
                        content=eresp.content or "",
                        tokens=eresp.prompt_tokens + eresp.completion_tokens,
                        cost_usd=ecost,
                        latency_ms=elat,
                    )
                    results.append(f"{s}: {eresp.content}")

            rresp, rlat, rcost = self._ask(
                REFLECTOR_PROMPT, f"Task: {task}\nResults:\n" + "\n".join(results)
            )
            try:
                verdict = json.loads(rresp.content or "{}")
            except json.JSONDecodeError:
                verdict = {"done": True, "feedback": ""}
            yield Step(
                kind="thought",
                content=f"Reflection (done={verdict.get('done')}): {verdict.get('feedback', '')}",
                tokens=rresp.prompt_tokens + rresp.completion_tokens,
                cost_usd=rcost,
                latency_ms=rlat,
            )
            if verdict.get("done"):
                break
            feedback = verdict.get("feedback", "")

        yield Step(kind="final", content="\n".join(results))
