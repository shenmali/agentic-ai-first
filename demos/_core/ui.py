from collections.abc import Callable, Iterator

import gradio as gr

from _core.llm import LLMClient
from _core.models import DEFAULT_MODEL, model_ids
from _core.tracer import Step, Trace

_KIND_ICON = {"thought": "💭", "action": "🔧", "observation": "👁️", "final": "✅"}


def api_key_input() -> gr.Textbox:
    return gr.Textbox(
        label="OpenRouter API key",
        type="password",
        placeholder="sk-or-...",
        info=(
            "Get a key at https://openrouter.ai/keys — it stays in your browser"
            " session and is never stored."
        ),
    )


def model_selector() -> gr.Dropdown:
    return gr.Dropdown(choices=model_ids(), value=DEFAULT_MODEL, label="Model")


def render_step_markdown(step: Step) -> str:
    icon = _KIND_ICON.get(step.kind, "•")
    meta = ""
    if step.tokens or step.cost_usd or step.latency_ms:
        meta = f"  \n<sub>{step.tokens} tok · ${step.cost_usd:.4f} · {step.latency_ms} ms</sub>"
    return f"**{icon} {step.kind.title()}**  \n{step.content}{meta}"


def render_trace_markdown(trace: Trace) -> str:
    return "\n\n---\n\n".join(render_step_markdown(s) for s in trace.steps)


def metrics_summary(trace: Trace) -> str:
    return (
        f"**Total:** {trace.total_tokens()} tokens · "
        f"${trace.total_cost():.4f} · {len(trace.steps)} steps"
    )


def build_agent_app(
    *,
    title: str,
    description: str,
    input_label: str,
    input_placeholder: str,
    run_fn: Callable[[LLMClient, str], Iterator[Step]],
    example: str = "",
) -> gr.Blocks:
    """Build a standard single-input agent demo.

    run_fn(llm, user_input) yields Steps. Key validation, LLM construction,
    trace accumulation, rendering and error handling are handled here.
    """

    def _handler(api_key: str, model_id: str, user_input: str):
        if not api_key:
            yield "⚠️ Please enter your OpenRouter API key.", ""
            return
        try:
            llm = LLMClient(api_key=api_key, model=model_id)
        except Exception as e:
            yield f"⚠️ {e}", ""
            return
        trace = Trace()
        try:
            for step in run_fn(llm, user_input):
                trace.add(step)
                yield render_trace_markdown(trace), metrics_summary(trace)
        except Exception as e:
            yield render_trace_markdown(trace) + f"\n\n⚠️ **Error:** {e}", metrics_summary(trace)

    with gr.Blocks(title=title) as demo:
        gr.Markdown(f"# {title}\n\n{description}")
        with gr.Row():
            key = api_key_input()
            model = model_selector()
        inp = gr.Textbox(label=input_label, placeholder=input_placeholder, value=example)
        btn = gr.Button("Run agent", variant="primary")
        trace_out = gr.Markdown()
        metrics_out = gr.Markdown()
        btn.click(_handler, inputs=[key, model, inp], outputs=[trace_out, metrics_out])
    return demo


def _truncate(text: str, limit: int = 60) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_trace_table(trace: Trace) -> str:
    header = (
        "| # | Step | Tokens | Cost | Latency | Content |\n"
        "|---|------|-------|------|---------|---------|"
    )
    rows = [
        f"| {i + 1} | {s.kind} | {s.tokens} | ${s.cost_usd:.4f}"
        f" | {s.latency_ms} ms | {_truncate(s.content)} |"
        for i, s in enumerate(trace.steps)
    ]
    return "\n".join([header, *rows])


def cost_breakdown(trace: Trace) -> str:
    by_kind: dict[str, float] = {}
    for s in trace.steps:
        by_kind[s.kind] = by_kind.get(s.kind, 0.0) + s.cost_usd
    lines = [f"- **{kind}**: ${cost:.4f}" for kind, cost in by_kind.items()]
    lines.append(f"- **total**: ${trace.total_cost():.4f}")
    return "\n".join(lines)
