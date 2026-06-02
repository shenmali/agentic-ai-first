import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tools import ToolRegistry
from _core.tracer import Step

SYSTEM_PROMPT = (
    "You are a ReAct agent. Reason step by step about the user's question. "
    "Use a tool when you need external information or computation. "
    "When you can answer directly, respond with the final answer and do NOT call a tool."
)


class ReActAgent:
    def __init__(self, llm: LLMClient, tools: ToolRegistry, max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> Iterator[Step]:
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        for _ in range(self.max_steps):
            start = time.monotonic()
            resp = self.llm.chat(messages, tools=self.tools.to_openai_schema())
            latency = int((time.monotonic() - start) * 1000)
            cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
            step_tokens = resp.prompt_tokens + resp.completion_tokens

            if resp.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp.content or "",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": tc["arguments"]},
                            }
                            for tc in resp.tool_calls
                        ],
                    }
                )
                if resp.content:
                    yield Step(
                        kind="thought",
                        content=resp.content,
                        tokens=step_tokens,
                        cost_usd=cost,
                        latency_ms=latency,
                    )
                for tc in resp.tool_calls:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    yield Step(kind="action", content=f"{tc['name']}({tc['arguments']})")
                    result = self.tools.execute(tc["name"], args)
                    yield Step(kind="observation", content=result)
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                continue

            yield Step(
                kind="final",
                content=resp.content or "",
                tokens=step_tokens,
                cost_usd=cost,
                latency_ms=latency,
            )
            return

        yield Step(kind="final", content="Reached max steps without a final answer.")
