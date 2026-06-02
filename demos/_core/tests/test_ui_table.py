from _core.tracer import Step, Trace
from _core.ui import cost_breakdown, render_trace_table


def _trace() -> Trace:
    t = Trace()
    t.add(Step(kind="action", content="web_search(x)", tokens=0, cost_usd=0.0, latency_ms=300))
    t.add(Step(kind="observation", content="some long observation text " * 5))
    t.add(Step(kind="final", content="answer", tokens=120, cost_usd=0.0030, latency_ms=900))
    return t


def test_render_trace_table_has_header_and_rows():
    md = render_trace_table(_trace())
    assert "| # | Step | Tokens | Cost | Latency |" in md
    assert "final" in md
    assert "120" in md


def test_render_trace_table_truncates_long_content():
    md = render_trace_table(_trace())
    assert "…" in md  # long observation is truncated


def test_cost_breakdown_groups_by_kind():
    md = cost_breakdown(_trace())
    assert "final" in md
    assert "0.0030" in md
