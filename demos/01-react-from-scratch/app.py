from _core.llm import LLMClient
from _core.tools import ToolRegistry, make_calculator, make_web_search
from _core.ui import build_agent_app
from agent import ReActAgent


def run_fn(llm: LLMClient, user_input: str):
    tools = ToolRegistry()
    tools.register(make_calculator())
    tools.register(make_web_search())
    return ReActAgent(llm=llm, tools=tools).run(user_input)


demo = build_agent_app(
    title="ReAct from scratch",
    description=(
        "The Reasoning + Acting loop, built from first principles. The agent "
        "interleaves thinking, tool calls, and observations. Bring your own "
        "OpenRouter key — it stays in your browser session."
    ),
    input_label="Question",
    input_placeholder="What is 24 * 17? And who won the 2022 FIFA World Cup?",
    run_fn=run_fn,
    example="What is 24 * 17?",
)

if __name__ == "__main__":
    demo.launch()
