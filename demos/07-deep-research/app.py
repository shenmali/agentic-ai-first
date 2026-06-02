import gradio as gr
from _core.llm import LLMClient
from _core.tracer import Trace
from _core.ui import api_key_input, metrics_summary, model_selector, render_trace_markdown
from agent import DeepResearchAgent, make_search_fn


def run(api_key: str, model_id: str, topic: str, tavily_key: str):
    if not api_key:
        yield "⚠️ Please enter your OpenRouter API key.", ""
        return
    try:
        llm = LLMClient(api_key=api_key, model=model_id)
    except Exception as e:
        yield f"⚠️ {e}", ""
        return
    search_fn = make_search_fn(tavily_key or None)
    trace = Trace()
    try:
        for step in DeepResearchAgent(llm=llm, search_fn=search_fn).run(topic):
            trace.add(step)
            yield render_trace_markdown(trace), metrics_summary(trace)
    except Exception as e:
        yield render_trace_markdown(trace) + f"\n\n⚠️ **Error:** {e}", metrics_summary(trace)


with gr.Blocks(title="Deep Research Agent") as demo:
    gr.Markdown(
        "# Deep Research Agent\n\n"
        "Plans sub-questions, searches the web for each, tracks every source, and "
        "writes a cited brief. Uses DuckDuckGo by default; add a Tavily key for "
        "higher-quality search. Bring your own OpenRouter key."
    )
    with gr.Row():
        key = api_key_input()
        model = model_selector()
    tavily = gr.Textbox(
        label="Tavily API key (optional — better search)", type="password", placeholder="tvly-..."
    )
    topic = gr.Textbox(
        label="Research topic",
        placeholder="The current state of small language models for on-device inference",
    )
    btn = gr.Button("Research", variant="primary")
    out = gr.Markdown()
    metrics_out = gr.Markdown()
    btn.click(run, inputs=[key, model, topic, tavily], outputs=[out, metrics_out])

if __name__ == "__main__":
    demo.launch()
