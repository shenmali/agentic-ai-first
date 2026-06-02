from _core.llm import LLMClient
from _core.ui import build_agent_app
from agent import OrchestratorAgent


def run_fn(llm: LLMClient, user_input: str):
    return OrchestratorAgent(llm=llm).run(user_input)


demo = build_agent_app(
    title="Orchestrator-Workers",
    description=(
        "A boss agent decomposes the task, dispatches each subtask to a specialist "
        "worker, then synthesizes their outputs. Bring your own OpenRouter key."
    ),
    input_label="Task",
    input_placeholder="Write a launch plan for a new productivity app.",
    run_fn=run_fn,
    example="Compare electric vs. hydrogen cars across cost, range, and infrastructure.",
)

if __name__ == "__main__":
    demo.launch()
