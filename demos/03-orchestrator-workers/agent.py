import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tracer import Step

ORCH_PROMPT = (
    "You are an orchestrator. Decompose the task into 2-4 independent subtasks, "
    "each assigned to a named specialist. Output ONLY a JSON array of objects "
    '{"role": str, "subtask": str}.'
)
SYNTH_PROMPT = (
    "You are an orchestrator. Combine the workers' outputs into one coherent answer "
    "to the original task."
)


class OrchestratorAgent:
    def __init__(self, llm: LLMClient, max_workers: int = 4):
        self.llm = llm
        self.max_workers = max_workers

    def _ask(self, system: str, user: str):
        start = time.monotonic()
        resp = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        latency = int((time.monotonic() - start) * 1000)
        cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
        return resp, latency, cost

    def run(self, task: str) -> Iterator[Step]:
        resp, lat, cost = self._ask(ORCH_PROMPT, task)
        try:
            parsed = json.loads(resp.content or "[]")
        except json.JSONDecodeError:
            parsed = []
        # Coerce whatever the model returned into a list of {role, subtask} dicts —
        # small models often return a bare string array or a single object.
        if not isinstance(parsed, list):
            parsed = [parsed]
        subtasks = []
        for item in parsed[: self.max_workers]:
            if isinstance(item, dict):
                subtasks.append(
                    {"role": item.get("role", "specialist"), "subtask": item.get("subtask", task)}
                )
            else:
                subtasks.append({"role": "generalist", "subtask": str(item)})
        if not subtasks:
            subtasks = [{"role": "generalist", "subtask": task}]
        yield Step(
            kind="thought",
            content="Decomposition:\n"
            + "\n".join(f"- [{s['role']}] {s['subtask']}" for s in subtasks),
            tokens=resp.prompt_tokens + resp.completion_tokens,
            cost_usd=cost,
            latency_ms=lat,
        )

        outputs: list[str] = []
        for s in subtasks:
            yield Step(kind="action", content=f"Dispatch to {s['role']}: {s['subtask']}")
            wresp, wlat, wcost = self._ask(
                f"You are a {s['role']}. Answer concisely.", s["subtask"]
            )
            yield Step(
                kind="observation",
                content=wresp.content or "",
                tokens=wresp.prompt_tokens + wresp.completion_tokens,
                cost_usd=wcost,
                latency_ms=wlat,
            )
            outputs.append(f"[{s['role']}] {wresp.content}")

        fresp, flat, fcost = self._ask(
            SYNTH_PROMPT, f"Task: {task}\nWorker outputs:\n" + "\n".join(outputs)
        )
        yield Step(
            kind="final",
            content=fresp.content or "",
            tokens=fresp.prompt_tokens + fresp.completion_tokens,
            cost_usd=fcost,
            latency_ms=flat,
        )
