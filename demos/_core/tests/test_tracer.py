from _core.tracer import Step, Trace


def test_trace_accumulates_tokens_and_cost():
    trace = Trace()
    trace.add(Step(kind="thought", content="hmm", tokens=10, cost_usd=0.001))
    trace.add(Step(kind="action", content="search", tokens=5, cost_usd=0.0005))
    assert trace.total_tokens() == 15
    assert abs(trace.total_cost() - 0.0015) < 1e-9
    assert len(trace.steps) == 2


def test_step_defaults_are_zero():
    step = Step(kind="final", content="done")
    assert step.tokens == 0
    assert step.cost_usd == 0.0
    assert step.latency_ms == 0
