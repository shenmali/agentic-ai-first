"""Headless live smoke test — run one agent end-to-end against real OpenRouter.

This is the single check that needs a real key (BYOK); everything else is
covered by the unit + HTTP-integration tests. It turns the manual "open the
Gradio app and paste a key" step into one command (also usable in CI with a
secret).

Usage:
    OPENROUTER_API_KEY=sk-or-... python scripts/smoke_live.py [model]

Exit codes: 0 = agent produced a final answer, 1 = no final answer, 2 = no key.
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "demos"))  # _core
sys.path.insert(0, str(_ROOT / "demos" / "01-react-from-scratch"))  # agent

from _core.llm import LLMClient  # noqa: E402
from _core.tools import ToolRegistry, make_calculator, make_web_search  # noqa: E402
from _core.ui import render_step_markdown  # noqa: E402
from agent import ReActAgent  # noqa: E402


def main() -> int:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Set OPENROUTER_API_KEY to run the live smoke test.")
        return 2

    model = sys.argv[1] if len(sys.argv) > 1 else "openai/gpt-4o-mini"
    tools = ToolRegistry()
    tools.register(make_calculator())
    tools.register(make_web_search())
    agent = ReActAgent(llm=LLMClient(api_key=key, model=model), tools=tools)

    final = None
    for step in agent.run("What is 24 * 17? Use the calculator tool."):
        print(render_step_markdown(step))
        print("---")
        if step.kind == "final":
            final = step

    if final and final.content:
        print(f"\n✅ Live run OK on {model}")
        return 0
    print("\n❌ No final answer produced")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
