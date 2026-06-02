from _core.tools import Tool, ToolRegistry


def _add_tool() -> Tool:
    return Tool(
        name="add",
        description="add two numbers",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
        fn=lambda a, b: str(a + b),
    )


def test_registry_executes_registered_tool():
    reg = ToolRegistry()
    reg.register(_add_tool())
    assert reg.execute("add", {"a": 2, "b": 3}) == "5"


def test_registry_unknown_tool_returns_error():
    reg = ToolRegistry()
    assert "unknown tool" in reg.execute("nope", {})


def test_to_openai_schema_shape():
    reg = ToolRegistry()
    reg.register(_add_tool())
    schema = reg.to_openai_schema()
    assert schema[0]["type"] == "function"
    assert schema[0]["function"]["name"] == "add"
    assert "parameters" in schema[0]["function"]
