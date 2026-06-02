from _core.llm import LLMClient
from _core.tools import ToolRegistry, make_calculator, make_web_search
from _core.ui import build_agent_app
from agent import PlanExecuteAgent

_EXAMPLE = "Estimate the cost of tiling a 12 m² floor at €25/m², then suggest a cheaper option."


def run_fn(llm: LLMClient, user_input: str):
    tools = ToolRegistry()
    tools.register(make_calculator())
    tools.register(make_web_search())
    return PlanExecuteAgent(llm=llm, tools=tools).run(user_input)


demo = build_agent_app(
    title="Plan-Execute-Reflect",
    description=(
        "The agent first drafts a plan, executes each step (using tools), then "
        "reflects on whether the goal is met — replanning if not. Bring your own "
        "OpenRouter key."
    ),
    input_label="Task",
    input_placeholder=_EXAMPLE,
    run_fn=run_fn,
    example=_EXAMPLE,
)

if __name__ == "__main__":
    demo.launch()
