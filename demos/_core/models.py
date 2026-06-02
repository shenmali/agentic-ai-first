from dataclasses import dataclass

# NOTE: model ids and prices reflect OpenRouter's catalog. Verify/refresh against
# https://openrouter.ai/models before launch — ids change as providers release models.


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    prompt_cost: float       # USD per 1M prompt tokens
    completion_cost: float   # USD per 1M completion tokens


MODELS: list[ModelInfo] = [
    ModelInfo("openai/gpt-4o-mini", "GPT-4o mini (cheap)", 0.15, 0.60),
    ModelInfo("anthropic/claude-3.5-haiku", "Claude 3.5 Haiku (cheap)", 0.80, 4.00),
    ModelInfo("google/gemini-flash-1.5", "Gemini 1.5 Flash (cheap)", 0.075, 0.30),
    ModelInfo("deepseek/deepseek-chat", "DeepSeek Chat (cheap)", 0.14, 0.28),
    ModelInfo("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet (strong)", 3.00, 15.00),
    ModelInfo("openai/gpt-4o", "GPT-4o (strong)", 2.50, 10.00),
]

DEFAULT_MODEL = "openai/gpt-4o-mini"


def model_ids() -> list[str]:
    return [m.id for m in MODELS]


def get_model(model_id: str) -> ModelInfo | None:
    return next((m for m in MODELS if m.id == model_id), None)


def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    m = get_model(model_id)
    if m is None:
        return 0.0
    return (prompt_tokens / 1_000_000) * m.prompt_cost + (
        completion_tokens / 1_000_000
    ) * m.completion_cost
