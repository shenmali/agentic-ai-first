import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tracer import Step

TARGET_SCHEMA = '{"name": string, "age": integer, "skills": [string]}'
GEN_PROMPT = (
    f"Extract the person's info as JSON matching this schema: {TARGET_SCHEMA}. "
    "Output ONLY the JSON object."
)
BANNED_PHRASES = ["ignore previous", "system prompt", "disregard instructions"]
MAX_INPUT_CHARS = 2000


def input_guardrail(text: str) -> str | None:
    if len(text) > MAX_INPUT_CHARS:
        return f"Input too long (max {MAX_INPUT_CHARS} characters)."
    low = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in low:
            return f"Input rejected: contains disallowed phrase '{phrase}'."
    return None


def validate(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        return ["output must be a JSON object"]
    errors: list[str] = []
    if not isinstance(payload.get("name"), str):
        errors.append("'name' must be a string")
    if not isinstance(payload.get("age"), int) or isinstance(payload.get("age"), bool):
        errors.append("'age' must be an integer")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        errors.append("'skills' must be a list of strings")
    return errors


class GuardedAgent:
    def __init__(self, llm: LLMClient, max_retries: int = 2):
        self.llm = llm
        self.max_retries = max_retries

    def run(self, user_input: str) -> Iterator[Step]:
        blocked = input_guardrail(user_input)
        if blocked:
            yield Step(kind="final", content=f"⛔ {blocked}")
            return

        messages: list[dict] = [
            {"role": "system", "content": GEN_PROMPT},
            {"role": "user", "content": user_input},
        ]
        for attempt in range(self.max_retries + 1):
            start = time.monotonic()
            resp = self.llm.chat(messages)
            latency = int((time.monotonic() - start) * 1000)
            cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
            yield Step(
                kind="thought",
                content=f"Attempt {attempt + 1}: {resp.content}",
                tokens=resp.prompt_tokens + resp.completion_tokens,
                cost_usd=cost,
                latency_ms=latency,
            )
            try:
                payload = json.loads(resp.content or "{}")
                errors = validate(payload)
            except json.JSONDecodeError as e:
                payload = None
                errors = [f"invalid JSON: {e}"]

            if not errors:
                yield Step(kind="observation", content="✅ Output passed validation.")
                yield Step(kind="final", content=json.dumps(payload, indent=2))
                return

            yield Step(kind="observation", content="❌ Validation failed: " + "; ".join(errors))
            messages.append({"role": "assistant", "content": resp.content or ""})
            messages.append(
                {
                    "role": "user",
                    "content": "Your output was invalid: "
                    + "; ".join(errors)
                    + ". Return corrected JSON only.",
                }
            )

        yield Step(kind="final", content="Failed validation after all retries.")
