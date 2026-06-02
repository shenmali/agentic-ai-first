from _core.models import DEFAULT_MODEL, estimate_cost, get_model, model_ids


def test_default_model_is_in_catalog():
    assert DEFAULT_MODEL in model_ids()


def test_estimate_cost_math():
    # a model priced 0.15 prompt / 0.60 completion per 1M tokens
    m = get_model(DEFAULT_MODEL)
    expected = (1_000_000 / 1_000_000) * m.prompt_cost + (1_000_000 / 1_000_000) * m.completion_cost
    assert abs(estimate_cost(DEFAULT_MODEL, 1_000_000, 1_000_000) - expected) < 1e-9


def test_estimate_cost_unknown_model_is_zero():
    assert estimate_cost("nonexistent/model", 100, 100) == 0.0
