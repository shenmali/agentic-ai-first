from _core.llm import LLMClient
from _core.ui import build_agent_app
from agent import GuardedAgent


def run_fn(llm: LLMClient, user_input: str):
    return GuardedAgent(llm=llm).run(user_input)


demo = build_agent_app(
    title="Guardrails & retries",
    description=(
        "Reliability patterns: an input guardrail blocks disallowed prompts, and the "
        "agent validates its JSON output against a schema — retrying with the error "
        "fed back until it's valid. Bring your own OpenRouter key."
    ),
    input_label="Describe a person (name, age, skills)",
    input_placeholder="Ada Lovelace, 36, skilled in mathematics and programming.",
    run_fn=run_fn,
    example="Ada Lovelace, 36, skilled in mathematics and programming.",
)

if __name__ == "__main__":
    demo.launch()
