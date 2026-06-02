from _core.tracer import Step, Trace
from _core.ui import metrics_summary, render_step_markdown, render_trace_markdown


def test_render_step_includes_kind_and_content():
    step = Step(kind="thought", content="thinking", tokens=5, cost_usd=0.001, latency_ms=120)
    md = render_step_markdown(step)
    assert "Thought" in md
    assert "thinking" in md
    assert "5 tok" in md


def test_render_trace_joins_steps():
    trace = Trace()
    trace.add(Step(kind="action", content="search(x)"))
    trace.add(Step(kind="observation", content="result"))
    md = render_trace_markdown(trace)
    assert "Action" in md and "Observation" in md


def test_metrics_summary_reports_totals():
    trace = Trace()
    trace.add(Step(kind="final", content="done", tokens=20, cost_usd=0.002))
    summary = metrics_summary(trace)
    assert "20" in summary
    assert "0.0020" in summary
