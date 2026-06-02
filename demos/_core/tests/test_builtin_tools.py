from _core.tools import calculate, make_calculator, make_web_search


def test_calculator_evaluates_expression():
    assert calculate("2 * (3 + 4)") == "14"


def test_calculator_rejects_unsafe_input():
    assert calculate("__import__('os').system('ls')").startswith("Error")


def test_make_calculator_returns_named_tool():
    tool = make_calculator()
    assert tool.name == "calculator"
    assert "expression" in tool.parameters["properties"]


def test_make_web_search_returns_named_tool():
    tool = make_web_search()
    assert tool.name == "web_search"


def test_calculator_rejects_exponent_bomb():
    assert calculate("9**9**9").startswith("Error")


def test_calculator_allows_small_exponent():
    assert calculate("2**10") == "1024"
