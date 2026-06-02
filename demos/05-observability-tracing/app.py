import gradio as gr

from _core.llm import LLMClient
from _core.tools import ToolRegistry, make_web_search
from _core.tracer import Trace
from _core.ui import (
    api_key_input,
    cost_breakdown,
    metrics_summary,
    model_selector,
    render_trace_table,
)
from agent import PipelineAgent


def run(api_key: str, model_id: str, query: str):
    if not api_key:
        yield "⚠️ Please enter your OpenRouter API key.", "", ""
        return
    try:
        llm = LLMClient(api_key=api_key, model=model_id)
    except Exception as e:
        yield f"⚠️ {e}", "", ""
        return
    tools = ToolRegistry()
    tools.register(make_web_search())
    trace = Trace()
    try:
        for step in PipelineAgent(llm=llm, tools=tools).run(query):
            trace.add(step)
            yield render_trace_table(trace), cost_breakdown(trace), metrics_summary(trace)
    except Exception as e:
        yield (
            render_trace_table(trace) + f"\n\n⚠️ **Error:** {e}",
            cost_breakdown(trace),
            metrics_summary(trace),
        )


with gr.Blocks(title="Observability & tracing") as demo:
    gr.Markdown(
        "# Observability & tracing\n\n"
        "Every agent step is recorded with its tokens, cost, and latency. This demo "
        "renders the trace as a table plus a per-step cost breakdown — the kind of "
        "instrumentation you need to debug and budget an agent in production. "
        "Bring your own OpenRouter key."
    )
    with gr.Row():
        key = api_key_input()
        model = model_selector()
    query = gr.Textbox(
        label="Query",
        placeholder="What are the main approaches to retrieval-augmented generation?",
    )
    btn = gr.Button("Run pipeline", variant="primary")
    table_out = gr.Markdown()
    breakdown_out = gr.Markdown()
    metrics_out = gr.Markdown()
    btn.click(run, inputs=[key, model, query], outputs=[table_out, breakdown_out, metrics_out])

if __name__ == "__main__":
    demo.launch()
