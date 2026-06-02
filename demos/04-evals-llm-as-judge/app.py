from _core.llm import LLMClient
from _core.ui import build_agent_app
from agent import EvalHarness


def run_fn(llm: LLMClient, _user_input: str):
    return EvalHarness(llm=llm).run()


demo = build_agent_app(
    title="Evals & LLM-as-judge",
    description=(
        "How do you know your agent is any good? This harness asks the model a fixed "
        "Q&A set, then uses an LLM judge to score each answer against a reference. "
        "Press Run (the input box is ignored). Bring your own OpenRouter key."
    ),
    input_label="(ignored) press Run to evaluate the built-in dataset",
    input_placeholder="",
    run_fn=run_fn,
)

if __name__ == "__main__":
    demo.launch()
