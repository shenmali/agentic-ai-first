# Plan 1 — Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one complete agentic-AI case-study (ReAct) end-to-end — shared `_core` module, a live HuggingFace Space running via BYOK OpenRouter, an Astro i18n site shell with the first post, and both deploy pipelines — proving the whole architecture before scaling to the other six demos.

**Architecture:** Pragmatic monorepo. `demos/_core/` is a shared local Python module (imported as `from _core.x import ...`) copied into each HF Space at deploy time. `demos/01-react-from-scratch/` is an isolated Gradio app. `site/` is a static Astro site with explicit `[lang]/[slug]` routing. CI runs Python tests per-demo (cwd = demo dir, `PYTHONPATH` includes `demos/` for `_core`) — this mirrors the Space runtime exactly.

**Tech Stack:** Python 3.11, OpenAI SDK (pointed at OpenRouter), Gradio, `ddgs` (DuckDuckGo search), pytest, ruff. Astro 4 + MDX. GitHub Actions → Cloudflare Pages (site) + HuggingFace Hub (demos).

**Spec:** `docs/superpowers/specs/2026-06-02-agentic-ai-showcase-design.md`

---

### Task 0: Repo scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Create: `README.md`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = ["site"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
addopts = "-q"
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest>=8.0
ruff>=0.6
gradio>=4.44
openai>=1.40
ddgs>=6.0
```

- [ ] **Step 3: Create `README.md`**

```markdown
# Agentic AI — Engineering Showcase

Interview-grade agentic-AI problems, solved with modern techniques and runnable live (bring your own [OpenRouter](https://openrouter.ai/keys) key).

- **Site:** https://agentic.mashen.dev
- **Demos:** HuggingFace Spaces (see each case-study)

## Case studies
1. ReAct from scratch — `demos/01-react-from-scratch`

## Repo layout
- `site/` — Astro static site (EN/TR/NL)
- `demos/` — Python Gradio demos, one HF Space each
- `demos/_core/` — shared LLM / tools / tracer / UI helpers

## Develop
```bash
pip install -r requirements-dev.txt
cd demos && PYTHONPATH=. pytest _core/tests -q
```
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml requirements-dev.txt README.md
git commit -m "chore: repo scaffolding (ruff, pytest, deps, readme)"
```

---

### Task 1: `_core/tracer.py` — observability primitive

**Files:**
- Create: `demos/_core/__init__.py` (empty)
- Create: `demos/_core/tracer.py`
- Test: `demos/_core/tests/__init__.py` (empty), `demos/_core/tests/test_tracer.py`

- [ ] **Step 1: Write the failing test**

`demos/_core/tests/test_tracer.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_tracer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_core.tracer'`

- [ ] **Step 3: Write minimal implementation**

`demos/_core/tracer.py`:
```python
from dataclasses import dataclass, field
from typing import Literal

StepKind = Literal["thought", "action", "observation", "final"]


@dataclass
class Step:
    kind: StepKind
    content: str
    tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


@dataclass
class Trace:
    steps: list[Step] = field(default_factory=list)

    def add(self, step: Step) -> None:
        self.steps.append(step)

    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.steps)

    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.steps)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_tracer.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add demos/_core/__init__.py demos/_core/tracer.py demos/_core/tests/__init__.py demos/_core/tests/test_tracer.py
git commit -m "feat(core): add Step/Trace observability primitive"
```

---

### Task 2: `_core/tools.py` — Tool abstraction + registry

**Files:**
- Create: `demos/_core/tools.py`
- Test: `demos/_core/tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

`demos/_core/tests/test_tools.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_core.tools'`

- [ ] **Step 3: Write minimal implementation**

`demos/_core/tools.py`:
```python
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def to_openai_schema(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, args: dict) -> str:
        if name not in self._tools:
            return f"Error: unknown tool '{name}'"
        try:
            return self._tools[name].fn(**args)
        except Exception as e:  # tool failures must not crash the agent loop
            return f"Error executing {name}: {e}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_tools.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add demos/_core/tools.py demos/_core/tests/test_tools.py
git commit -m "feat(core): add Tool dataclass and ToolRegistry"
```

---

### Task 3: Built-in tools — calculator + web_search

**Files:**
- Modify: `demos/_core/tools.py` (append factories)
- Test: `demos/_core/tests/test_builtin_tools.py`

- [ ] **Step 1: Write the failing test**

`demos/_core/tests/test_builtin_tools.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_builtin_tools.py -v`
Expected: FAIL with `ImportError: cannot import name 'calculate'`

- [ ] **Step 3: Write minimal implementation (append to `demos/_core/tools.py`)**

```python
import ast
import operator

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")  # prevent 9**9**9 DoS
        return _SAFE_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def calculate(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"Error: {e}"


def make_calculator() -> Tool:
    return Tool(
        name="calculator",
        description="Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4)'.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        fn=lambda expression: calculate(expression),
    )


def web_search(query: str, max_results: int = 3) -> str:
    try:
        from ddgs import DDGS
    except ImportError:  # package was renamed; support both
        from duckduckgo_search import DDGS  # type: ignore
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(f"- {r.get('title', '')}: {r.get('body', '')}")
    return "\n".join(results) if results else "No results found."


def make_web_search() -> Tool:
    return Tool(
        name="web_search",
        description="Search the web for current information. Returns the top results.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        fn=lambda query: web_search(query),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_builtin_tools.py -v`
Expected: PASS (6 passed). The web_search test only constructs the Tool — it does NOT hit the network.

- [ ] **Step 5: Commit**

```bash
git add demos/_core/tools.py demos/_core/tests/test_builtin_tools.py
git commit -m "feat(core): add safe calculator and web_search built-in tools"
```

---

### Task 4: `_core/models.py` — model catalog + cost estimate

**Files:**
- Create: `demos/_core/models.py`
- Test: `demos/_core/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`demos/_core/tests/test_models.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_core.models'`

- [ ] **Step 3: Write minimal implementation**

`demos/_core/models.py`:
```python
from dataclasses import dataclass

# NOTE: model ids and prices reflect OpenRouter's catalog. Verify/refresh against
# https://openrouter.ai/models before launch — ids change as providers release models.


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    prompt_cost: float       # USD per 1M prompt tokens
    completion_cost: float   # USD per 1M completion tokens


MODELS: list[ModelInfo] = [
    ModelInfo("openai/gpt-4o-mini", "GPT-4o mini (cheap)", 0.15, 0.60),
    ModelInfo("anthropic/claude-3.5-haiku", "Claude 3.5 Haiku (cheap)", 0.80, 4.00),
    ModelInfo("google/gemini-flash-1.5", "Gemini 1.5 Flash (cheap)", 0.075, 0.30),
    ModelInfo("deepseek/deepseek-chat", "DeepSeek Chat (cheap)", 0.14, 0.28),
    ModelInfo("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet (strong)", 3.00, 15.00),
    ModelInfo("openai/gpt-4o", "GPT-4o (strong)", 2.50, 10.00),
]

DEFAULT_MODEL = "openai/gpt-4o-mini"


def model_ids() -> list[str]:
    return [m.id for m in MODELS]


def get_model(model_id: str) -> ModelInfo | None:
    return next((m for m in MODELS if m.id == model_id), None)


def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    m = get_model(model_id)
    if m is None:
        return 0.0
    return (prompt_tokens / 1_000_000) * m.prompt_cost + (
        completion_tokens / 1_000_000
    ) * m.completion_cost
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add demos/_core/models.py demos/_core/tests/test_models.py
git commit -m "feat(core): add OpenRouter model catalog and cost estimator"
```

---

### Task 5: `_core/llm.py` — OpenRouter client (BYOK)

**Files:**
- Create: `demos/_core/llm.py`
- Test: `demos/_core/tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

`demos/_core/tests/test_llm.py`:
```python
import pytest

from _core.llm import LLMClient, LLMResponse


class _FakeMessage:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message):
        self.message = message


class _FakeUsage:
    def __init__(self, p, c):
        self.prompt_tokens = p
        self.completion_tokens = c


class _FakeResponse:
    def __init__(self, content, tool_calls, p, c):
        self.choices = [_FakeChoice(_FakeMessage(content, tool_calls))]
        self.usage = _FakeUsage(p, c)


class _FakeCompletions:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeOpenAI:
    def __init__(self, response):
        self.chat = type("C", (), {"completions": _FakeCompletions(response)})()


def test_llm_client_requires_key():
    with pytest.raises(ValueError):
        LLMClient(api_key="", model="openai/gpt-4o-mini")


def test_llm_client_parses_content_and_usage():
    client = LLMClient(api_key="test-key", model="openai/gpt-4o-mini")
    client._client = _FakeOpenAI(_FakeResponse("hello", None, 12, 7))
    resp = client.chat([{"role": "user", "content": "hi"}])
    assert isinstance(resp, LLMResponse)
    assert resp.content == "hello"
    assert resp.prompt_tokens == 12
    assert resp.completion_tokens == 7
    assert resp.tool_calls == []


def test_llm_client_parses_tool_calls():
    tc = type("TC", (), {
        "id": "call_1",
        "function": type("F", (), {"name": "calculator", "arguments": '{"expression":"2+2"}'})(),
    })()
    client = LLMClient(api_key="test-key", model="openai/gpt-4o-mini")
    client._client = _FakeOpenAI(_FakeResponse(None, [tc], 5, 5))
    resp = client.chat([{"role": "user", "content": "calc"}], tools=[{"type": "function"}])
    assert resp.tool_calls[0]["name"] == "calculator"
    assert resp.tool_calls[0]["arguments"] == '{"expression":"2+2"}'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_core.llm'`

- [ ] **Step 3: Write minimal implementation**

`demos/_core/llm.py`:
```python
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[dict] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMClient:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("An OpenRouter API key is required.")
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        tool_calls = []
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tool_calls.append(
                    {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                )
        usage = resp.usage
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_llm.py -v`
Expected: PASS (3 passed). No network calls — the OpenAI client is replaced with a fake.

- [ ] **Step 5: Commit**

```bash
git add demos/_core/llm.py demos/_core/tests/test_llm.py
git commit -m "feat(core): add OpenRouter LLMClient with BYOK and tool-call parsing"
```

---

### Task 6: `_core/ui.py` — render helpers + reusable app builder

**Files:**
- Create: `demos/_core/ui.py`
- Test: `demos/_core/tests/test_ui.py`

- [ ] **Step 1: Write the failing test** (only the pure render functions are unit-tested)

`demos/_core/tests/test_ui.py`:
```python
from _core.tracer import Step, Trace
from _core.ui import metrics_summary, render_step_markdown, render_trace_markdown


def test_render_step_includes_kind_and_content():
    md = render_step_markdown(Step(kind="thought", content="thinking", tokens=5, cost_usd=0.001, latency_ms=120))
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_ui.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_core.ui'`

- [ ] **Step 3: Write minimal implementation**

`demos/_core/ui.py`:
```python
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
        info="Get a key at https://openrouter.ai/keys — it stays in your browser session and is never stored.",
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos && PYTHONPATH=. pytest _core/tests/test_ui.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add demos/_core/ui.py demos/_core/tests/test_ui.py
git commit -m "feat(core): add trace render helpers and reusable Gradio app builder"
```

---

### Task 7: ReAct agent loop

**Files:**
- Create: `demos/01-react-from-scratch/agent.py`
- Test: `demos/01-react-from-scratch/tests/__init__.py` (empty), `demos/01-react-from-scratch/tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

`demos/01-react-from-scratch/tests/test_agent.py`:
```python
from _core.llm import LLMResponse
from _core.tools import Tool, ToolRegistry
from agent import ReActAgent


class _ScriptedLLM:
    def __init__(self, responses):
        self.model = "test/model"
        self._responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None):
        r = self._responses[self.calls]
        self.calls += 1
        return r


def _echo_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="echo",
            description="echo the input",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            fn=lambda x: f"echoed {x}",
        )
    )
    return reg


def test_react_agent_uses_tool_then_finalizes():
    scripted = _ScriptedLLM([
        LLMResponse(
            content="I should echo",
            tool_calls=[{"id": "1", "name": "echo", "arguments": '{"x":"hi"}'}],
            prompt_tokens=10,
            completion_tokens=5,
        ),
        LLMResponse(content="Done: echoed hi", tool_calls=[], prompt_tokens=8, completion_tokens=4),
    ])
    agent = ReActAgent(llm=scripted, tools=_echo_registry(), max_steps=5)
    steps = list(agent.run("please echo hi"))
    kinds = [s.kind for s in steps]
    assert "action" in kinds
    assert "observation" in kinds
    assert steps[-1].kind == "final"
    assert "echoed hi" in steps[-1].content


def test_react_agent_stops_at_max_steps():
    loop = LLMResponse(
        content="thinking",
        tool_calls=[{"id": "1", "name": "echo", "arguments": '{"x":"again"}'}],
        prompt_tokens=1,
        completion_tokens=1,
    )
    scripted = _ScriptedLLM([loop] * 10)
    agent = ReActAgent(llm=scripted, tools=_echo_registry(), max_steps=3)
    steps = list(agent.run("loop forever"))
    assert steps[-1].kind == "final"
    assert "max steps" in steps[-1].content.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos/01-react-from-scratch && PYTHONPATH="..:." pytest -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Write minimal implementation**

`demos/01-react-from-scratch/agent.py`:
```python
import json
import time
from collections.abc import Iterator

from _core.llm import LLMClient
from _core.models import estimate_cost
from _core.tools import ToolRegistry
from _core.tracer import Step

SYSTEM_PROMPT = (
    "You are a ReAct agent. Reason step by step about the user's question. "
    "Use a tool when you need external information or computation. "
    "When you can answer directly, respond with the final answer and do NOT call a tool."
)


class ReActAgent:
    def __init__(self, llm: LLMClient, tools: ToolRegistry, max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> Iterator[Step]:
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        for _ in range(self.max_steps):
            start = time.monotonic()
            resp = self.llm.chat(messages, tools=self.tools.to_openai_schema())
            latency = int((time.monotonic() - start) * 1000)
            cost = estimate_cost(self.llm.model, resp.prompt_tokens, resp.completion_tokens)
            step_tokens = resp.prompt_tokens + resp.completion_tokens

            if resp.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp.content or "",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": tc["arguments"]},
                            }
                            for tc in resp.tool_calls
                        ],
                    }
                )
                if resp.content:
                    yield Step(
                        kind="thought",
                        content=resp.content,
                        tokens=step_tokens,
                        cost_usd=cost,
                        latency_ms=latency,
                    )
                for tc in resp.tool_calls:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    yield Step(kind="action", content=f"{tc['name']}({tc['arguments']})")
                    result = self.tools.execute(tc["name"], args)
                    yield Step(kind="observation", content=result)
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                continue

            yield Step(
                kind="final",
                content=resp.content or "",
                tokens=step_tokens,
                cost_usd=cost,
                latency_ms=latency,
            )
            return

        yield Step(kind="final", content="Reached max steps without a final answer.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos/01-react-from-scratch && PYTHONPATH="..:." pytest -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add demos/01-react-from-scratch/agent.py demos/01-react-from-scratch/tests/
git commit -m "feat(demo): add ReAct agent loop with tests"
```

---

### Task 8: ReAct demo app + Space config

**Files:**
- Create: `demos/01-react-from-scratch/app.py`
- Create: `demos/01-react-from-scratch/requirements.txt`
- Create: `demos/01-react-from-scratch/README.md` (HF Space config via YAML frontmatter)
- Test: `demos/01-react-from-scratch/tests/test_app.py`

- [ ] **Step 1: Write the failing test**

`demos/01-react-from-scratch/tests/test_app.py`:
```python
def test_app_builds_demo_object():
    import app

    assert app.demo is not None
    assert callable(app.run_fn)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd demos/01-react-from-scratch && PYTHONPATH="..:." pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Write the implementation**

`demos/01-react-from-scratch/app.py`:
```python
from _core.llm import LLMClient
from _core.tools import ToolRegistry, make_calculator, make_web_search
from _core.ui import build_agent_app
from agent import ReActAgent


def run_fn(llm: LLMClient, user_input: str):
    tools = ToolRegistry()
    tools.register(make_calculator())
    tools.register(make_web_search())
    return ReActAgent(llm=llm, tools=tools).run(user_input)


demo = build_agent_app(
    title="ReAct from scratch",
    description=(
        "The Reasoning + Acting loop, built from first principles. The agent "
        "interleaves thinking, tool calls, and observations. Bring your own "
        "OpenRouter key — it stays in your browser session."
    ),
    input_label="Question",
    input_placeholder="What is 24 * 17? And who won the 2022 FIFA World Cup?",
    run_fn=run_fn,
    example="What is 24 * 17?",
)

if __name__ == "__main__":
    demo.launch()
```

`demos/01-react-from-scratch/requirements.txt`:
```
gradio>=4.44
openai>=1.40
ddgs>=6.0
```

`demos/01-react-from-scratch/README.md`:
```markdown
---
title: ReAct From Scratch
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# ReAct from scratch

A Reasoning + Acting agent built from first principles, with a transparent
step-by-step trace. Bring your own [OpenRouter](https://openrouter.ai/keys) key.

Source & write-up: https://github.com/shenmali/agentic-ai-first/tree/main/demos/01-react-from-scratch
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd demos/01-react-from-scratch && PYTHONPATH="..:." pytest tests/test_app.py -v`
Expected: PASS (1 passed). Building the Blocks object does not launch a server.

- [ ] **Step 5: Smoke-run locally (manual)**

Run: `cd demos/01-react-from-scratch && PYTHONPATH="..:." python app.py`
Expected: Gradio prints a local URL. Open it, paste a real OpenRouter key, run "What is 24 * 17?" and confirm the trace streams thought→action→observation→final. Ctrl-C to stop.

- [ ] **Step 6: Commit**

```bash
git add demos/01-react-from-scratch/app.py demos/01-react-from-scratch/requirements.txt demos/01-react-from-scratch/README.md demos/01-react-from-scratch/tests/test_app.py
git commit -m "feat(demo): add ReAct Gradio app and HF Space config"
```

---

### Task 9: Space-sync script

**Files:**
- Create: `scripts/sync_spaces.py`
- Test: `scripts/tests/__init__.py` (empty), `scripts/tests/test_sync_classify.py`

- [ ] **Step 1: Write the failing test** (only the pure path-classification logic is tested)

`scripts/tests/test_sync_classify.py`:
```python
from scripts.sync_spaces import classify_targets


def test_core_change_syncs_all_demos():
    changed = ["demos/_core/llm.py"]
    all_demos = ["01-react-from-scratch", "02-plan-execute"]
    assert classify_targets(changed, all_demos) == all_demos


def test_demo_change_syncs_only_that_demo():
    changed = ["demos/01-react-from-scratch/agent.py", "README.md"]
    all_demos = ["01-react-from-scratch", "02-plan-execute"]
    assert classify_targets(changed, all_demos) == ["01-react-from-scratch"]


def test_no_demo_change_syncs_nothing():
    changed = ["site/src/pages/index.astro"]
    all_demos = ["01-react-from-scratch"]
    assert classify_targets(changed, all_demos) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest scripts/tests/test_sync_classify.py -v` (from repo root)
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.sync_spaces'`

- [ ] **Step 3: Write the implementation**

`scripts/__init__.py`: (empty file)

`scripts/sync_spaces.py`:
```python
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
EXCLUDE = {"tests", "__pycache__"}


def all_demo_names() -> list[str]:
    return sorted(d.name for d in DEMOS.iterdir() if d.is_dir() and d.name[:1].isdigit())


def classify_targets(changed: list[str], all_demos: list[str]) -> list[str]:
    if any(c.startswith("demos/_core/") for c in changed):
        return list(all_demos)
    touched = []
    for name in all_demos:
        if any(c.startswith(f"demos/{name}/") for c in changed):
            touched.append(name)
    return touched


def _changed_paths() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def _copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE or item.suffix == ".pyc":
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*EXCLUDE, "*.pyc"))
        else:
            shutil.copy2(item, target)


def _space_id(hf_user: str, demo_name: str) -> str:
    short = demo_name.split("-", 1)[1] if "-" in demo_name else demo_name
    return f"{hf_user}/agentic-{short}"


def main() -> None:
    from huggingface_hub import HfApi

    hf_user = os.environ["HF_USER"]
    token = os.environ["HF_TOKEN"]
    api = HfApi()

    targets = classify_targets(_changed_paths(), all_demo_names())
    if not targets:
        print("No demo changes to sync.")
        return

    for name in targets:
        space_id = _space_id(hf_user, name)
        print(f"Syncing {name} -> {space_id}")
        api.create_repo(
            repo_id=space_id, repo_type="space", space_sdk="gradio", exist_ok=True, token=token
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _copy_tree(DEMOS / name, tmp_path)
            _copy_tree(DEMOS / "_core", tmp_path / "_core")
            api.upload_folder(
                repo_id=space_id, repo_type="space", folder_path=str(tmp_path), token=token
            )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest scripts/tests/test_sync_classify.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/sync_spaces.py scripts/tests/
git commit -m "feat(ci): add HF Space sync script with tested path classification"
```

---

### Task 10: CI workflow (Python + Astro check)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: ruff check demos scripts
      - name: Test _core
        working-directory: demos
        run: PYTHONPATH=. pytest _core/tests -q
      - name: Test scripts
        run: PYTHONPATH=. pytest scripts/tests -q
      - name: Test demos
        run: |
          set -e
          for d in demos/[0-9]*/; do
            echo "::group::Testing $d"
            (cd "$d" && PYTHONPATH="..:." pytest -q)
            echo "::endgroup::"
          done

  site:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - working-directory: site
        run: npm ci
      - working-directory: site
        run: npm run check
```

- [ ] **Step 2: Verify YAML locally**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('valid')"`
Expected: prints `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add Python + Astro check workflow"
```

> The `site` job will pass once Task 11 adds `site/package.json`. If committing before then, expect that job to fail until Task 11 lands — acceptable within this plan's sequence.

---

### Task 11: Astro site scaffold

**Files:**
- Create: `site/package.json`, `site/astro.config.mjs`, `site/tsconfig.json`
- Create: `site/src/content/config.ts`
- Create: `site/src/i18n/{en,tr,nl}.json`, `site/src/i18n/utils.ts`

- [ ] **Step 1: Create `site/package.json`**

```json
{
  "name": "agentic-ai-site",
  "type": "module",
  "version": "0.1.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro check && astro build",
    "preview": "astro preview",
    "check": "astro check"
  },
  "dependencies": {
    "astro": "^4.15.0",
    "@astrojs/mdx": "^3.1.0",
    "@astrojs/check": "^0.9.0",
    "@astrojs/sitemap": "^3.1.0",
    "typescript": "^5.5.0"
  }
}
```

- [ ] **Step 2: Create `site/astro.config.mjs`**

```js
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://agentic.mashen.dev',
  integrations: [mdx(), sitemap()],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'tr', 'nl'],
    routing: { prefixDefaultLocale: true },
  },
});
```

- [ ] **Step 3: Create `site/tsconfig.json`**

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist"]
}
```

- [ ] **Step 4: Create `site/src/content/config.ts`**

```ts
import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    lang: z.enum(['en', 'tr', 'nl']),
    slug: z.string(),
    spaceUrl: z.string().url(),
    githubPath: z.string(),
    order: z.number(),
    layer: z.enum(['pattern', 'production', 'flagship']),
  }),
});

export const collections = { posts };
```

- [ ] **Step 5: Create i18n dictionaries**

`site/src/i18n/en.json`:
```json
{
  "site.title": "Agentic AI — Engineering Showcase",
  "site.tagline": "Interview-grade agentic AI problems, solved with modern techniques. Bring your own key and run them live.",
  "nav.home": "Home",
  "cta.tryDemo": "Try the live demo",
  "cta.readCode": "Read the code",
  "post.notTranslated": "This article isn't available in your language yet — showing the English version.",
  "layer.pattern": "Patterns",
  "layer.production": "Production",
  "layer.flagship": "Flagship"
}
```

`site/src/i18n/tr.json`:
```json
{
  "site.title": "Agentic AI — Mühendislik Vitrini",
  "site.tagline": "Mülakat seviyesi agentic AI problemleri, güncel tekniklerle çözülmüş. Kendi anahtarını getir, canlı çalıştır.",
  "nav.home": "Ana Sayfa",
  "cta.tryDemo": "Canlı demoyu dene",
  "cta.readCode": "Kodu oku",
  "post.notTranslated": "Bu yazı henüz senin dilinde mevcut değil — İngilizce sürümü gösteriliyor.",
  "layer.pattern": "Desenler",
  "layer.production": "Production",
  "layer.flagship": "Vitrin"
}
```

`site/src/i18n/nl.json`:
```json
{
  "site.title": "Agentic AI — Engineering Showcase",
  "site.tagline": "Agentic AI-problemen op sollicitatieniveau, opgelost met moderne technieken. Gebruik je eigen sleutel en draai ze live.",
  "nav.home": "Home",
  "cta.tryDemo": "Probeer de live demo",
  "cta.readCode": "Lees de code",
  "post.notTranslated": "Dit artikel is nog niet beschikbaar in jouw taal — de Engelse versie wordt getoond.",
  "layer.pattern": "Patronen",
  "layer.production": "Productie",
  "layer.flagship": "Vlaggenschip"
}
```

- [ ] **Step 6: Create `site/src/i18n/utils.ts`**

```ts
import en from './en.json';
import tr from './tr.json';
import nl from './nl.json';

export const LOCALES = ['en', 'tr', 'nl'] as const;
export type Locale = (typeof LOCALES)[number];

const dicts: Record<Locale, Record<string, string>> = { en, tr, nl };

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

export function useTranslations(lang: string) {
  const dict = isLocale(lang) ? dicts[lang] : en;
  return (key: string): string => dict[key] ?? en[key] ?? key;
}
```

- [ ] **Step 7: Install and verify**

Run: `cd site && npm install && npm run check`
Expected: `npm install` succeeds; `astro check` reports 0 errors (it will warn there are no pages yet — that's fine; 0 errors is the gate).

- [ ] **Step 8: Commit**

```bash
git add site/package.json site/astro.config.mjs site/tsconfig.json site/src/content/config.ts site/src/i18n/
git commit -m "feat(site): scaffold Astro project with i18n config and content schema"
```

---

### Task 12: Layouts and components

**Files:**
- Create: `site/src/layouts/BaseLayout.astro`, `site/src/layouts/PostLayout.astro`
- Create: `site/src/components/LanguageSwitcher.astro`, `site/src/components/SpaceEmbed.astro`

- [ ] **Step 1: Create `site/src/components/LanguageSwitcher.astro`**

```astro
---
import { LOCALES } from '../i18n/utils';
interface Props { current: string }
const { current } = Astro.props;
const path = Astro.url.pathname;
const rest = path.replace(/^\/(en|tr|nl)/, '');
---
<nav class="lang-switcher">
  {LOCALES.map((l) => (
    <a href={`/${l}${rest || '/'}`} aria-current={l === current ? 'page' : undefined}>{l.toUpperCase()}</a>
  ))}
</nav>
```

- [ ] **Step 2: Create `site/src/components/SpaceEmbed.astro`**

```astro
---
interface Props { src: string }
const { src } = Astro.props;
---
<iframe
  src={src}
  title="Live demo"
  width="100%"
  height="760"
  frameborder="0"
  allow="clipboard-write"
  loading="lazy"
></iframe>
<p><small>The demo may take ~30s to wake from sleep on first load.</small></p>
```

- [ ] **Step 3: Create `site/src/layouts/BaseLayout.astro`**

```astro
---
import LanguageSwitcher from '../components/LanguageSwitcher.astro';
import { LOCALES } from '../i18n/utils';
interface Props { lang: string; title: string; description?: string; slug?: string }
const { lang, title, description = '', slug } = Astro.props;
const site = Astro.site?.toString().replace(/\/$/, '') ?? '';
---
<!doctype html>
<html lang={lang}>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    {description && <meta name="description" content={description} />}
    {slug && LOCALES.map((l) => (
      <link rel="alternate" hreflang={l} href={`${site}/${l}/${slug}`} />
    ))}
    {slug && <link rel="alternate" hreflang="x-default" href={`${site}/en/${slug}`} />}
  </head>
  <body>
    <header><a href={`/${lang}/`}>agentic.mashen.dev</a><LanguageSwitcher current={lang} /></header>
    <main><slot /></main>
    <footer><small>© mashen.dev · <a href="https://github.com/shenmali/agentic-ai-first">Source on GitHub</a></small></footer>
  </body>
</html>
```

- [ ] **Step 4: Create `site/src/layouts/PostLayout.astro`**

```astro
---
import type { CollectionEntry } from 'astro:content';
import BaseLayout from './BaseLayout.astro';
import SpaceEmbed from '../components/SpaceEmbed.astro';
import { useTranslations } from '../i18n/utils';
interface Props { entry: CollectionEntry<'posts'>; isFallback?: boolean }
const { entry, isFallback = false } = Astro.props;
const { title, description, lang, slug, spaceUrl, githubPath } = entry.data;
const t = useTranslations(lang);
---
<BaseLayout lang={lang} title={title} description={description} slug={slug}>
  <article>
    <h1>{title}</h1>
    {isFallback && <p class="banner">{t('post.notTranslated')}</p>}
    <slot />
    <h2>{t('cta.tryDemo')}</h2>
    <SpaceEmbed src={spaceUrl} />
    <p><a href={`https://github.com/shenmali/agentic-ai-first/tree/main/${githubPath}`}>{t('cta.readCode')} →</a></p>
  </article>
</BaseLayout>
```

- [ ] **Step 5: Verify**

Run: `cd site && npm run check`
Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add site/src/layouts/ site/src/components/
git commit -m "feat(site): add base/post layouts, language switcher, space embed"
```

---

### Task 13: Pages + first EN post

**Files:**
- Create: `site/src/pages/index.astro`
- Create: `site/src/pages/[lang]/index.astro`
- Create: `site/src/pages/[lang]/[slug].astro`
- Create: `site/src/content/posts/en/01-react-from-scratch.mdx`

- [ ] **Step 1: Create `site/src/pages/index.astro`** (root redirect to EN)

```astro
---
return Astro.redirect('/en/');
---
```

- [ ] **Step 2: Create `site/src/pages/[lang]/index.astro`** (landing per language, grouped by layer)

```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../../layouts/BaseLayout.astro';
import { LOCALES, useTranslations } from '../../i18n/utils';

export function getStaticPaths() {
  return LOCALES.map((lang) => ({ params: { lang } }));
}

const { lang } = Astro.params;
const t = useTranslations(lang);
const layers = ['pattern', 'production', 'flagship'] as const;
const posts = (await getCollection('posts', (p) => p.data.lang === lang)).sort(
  (a, b) => a.data.order - b.data.order,
);
---
<BaseLayout lang={lang} title={t('site.title')} description={t('site.tagline')}>
  <h1>{t('site.title')}</h1>
  <p>{t('site.tagline')}</p>
  {layers.map((layer) => {
    const group = posts.filter((p) => p.data.layer === layer);
    return group.length > 0 && (
      <section>
        <h2>{t(`layer.${layer}`)}</h2>
        <ul>
          {group.map((p) => (
            <li><a href={`/${lang}/${p.data.slug}`}>{p.data.title}</a> — {p.data.description}</li>
          ))}
        </ul>
      </section>
    );
  })}
</BaseLayout>
```

- [ ] **Step 3: Create `site/src/pages/[lang]/[slug].astro`** (post page; EN-only for now, fallback added in Plan 3)

```astro
---
import { getCollection } from 'astro:content';
import PostLayout from '../../layouts/PostLayout.astro';

export async function getStaticPaths() {
  const all = await getCollection('posts');
  return all.map((entry) => ({
    params: { lang: entry.data.lang, slug: entry.data.slug },
    props: { entry },
  }));
}

const { entry } = Astro.props;
const { Content } = await entry.render();
---
<PostLayout entry={entry}>
  <Content />
</PostLayout>
```

- [ ] **Step 4: Create the first EN post** `site/src/content/posts/en/01-react-from-scratch.mdx`

```mdx
---
title: "ReAct from scratch: the reasoning + acting loop"
description: "How agents interleave thinking and tool use — built from first principles."
publishDate: 2026-06-02
lang: en
slug: "react-from-scratch"
spaceUrl: "https://mashen-agentic-react-from-scratch.hf.space"
githubPath: "demos/01-react-from-scratch"
order: 1
layer: "pattern"
---

## The interview problem

> "Implement an agent that can answer questions requiring both reasoning and
> external lookups — without hardcoding the steps."

## Why a single prompt isn't enough

A one-shot completion can't decide *mid-task* that it needs to search or
calculate. ReAct fixes this by looping: the model emits a thought, optionally
calls a tool, reads the result, and repeats until it can answer.

## The loop

The whole pattern is a `while` loop over `chat()` calls: if the model returns
tool calls, execute them and feed results back; otherwise, that's the final
answer. See [`agent.py`](https://github.com/shenmali/agentic-ai-first/tree/main/demos/01-react-from-scratch/agent.py).

## Tradeoffs

- **Use it** for open-ended questions where the needed tools vary per query.
- **Avoid it** when the workflow is fixed — a hardcoded pipeline is cheaper and
  more predictable.

Run it live below with your own OpenRouter key.
```

> The prose above is a launch-ready stub. Full polish + TR/NL translations happen in Plan 3.

- [ ] **Step 5: Build and verify**

Run: `cd site && npm run build`
Expected: `astro check` 0 errors; build emits `/en/`, `/tr/`, `/nl/` index pages and `/en/react-from-scratch`. (TR/NL post routes don't exist yet — expected; fallback comes in Plan 3.)

- [ ] **Step 6: Dev-server eyeball (manual)**

Run: `cd site && npm run dev`
Expected: open `http://localhost:4321/en/` → landing lists the ReAct post under "Patterns"; clicking it shows the article + the embedded Space iframe; the EN/TR/NL switcher renders.

- [ ] **Step 7: Commit**

```bash
git add site/src/pages/ site/src/content/posts/en/01-react-from-scratch.mdx
git commit -m "feat(site): add routing, landing page, and first ReAct post"
```

---

### Task 14: Deploy workflows (Cloudflare Pages + HF Spaces)

**Files:**
- Create: `.github/workflows/site-deploy.yml`
- Create: `.github/workflows/space-sync.yml`

- [ ] **Step 1: Create `.github/workflows/site-deploy.yml`**

```yaml
name: Deploy site
on:
  push:
    branches: [main]
    paths: ['site/**', '.github/workflows/site-deploy.yml']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - working-directory: site
        run: npm ci && npm run build
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy site/dist --project-name=agentic-ai
```

- [ ] **Step 2: Create `.github/workflows/space-sync.yml`**

```yaml
name: Sync demos to HF Spaces
on:
  push:
    branches: [main]
    paths: ['demos/**', '.github/workflows/space-sync.yml', 'scripts/sync_spaces.py']

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install "huggingface_hub>=0.24"
      - name: Sync changed demos
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          HF_USER: mashen
        run: python -m scripts.sync_spaces
```

- [ ] **Step 3: Validate YAML**

Run: `python -c "import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/site-deploy.yml','.github/workflows/space-sync.yml']]; print('valid')"`
Expected: prints `valid`

- [ ] **Step 4: Document required secrets** (append to `README.md` under a new "## Deployment" section)

```markdown
## Deployment

GitHub Actions secrets required:
- `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` — site → Cloudflare Pages (project `agentic-ai`)
- `HF_TOKEN` — demos → HuggingFace Spaces (user `mashen`)

DNS: point `agentic.mashen.dev` (CNAME) at the Cloudflare Pages project.
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/site-deploy.yml .github/workflows/space-sync.yml README.md
git commit -m "ci: add Cloudflare Pages and HF Space deploy workflows"
```

---

### Task 15: Full local verification + final commit

- [ ] **Step 1: Run the entire Python suite the way CI does**

```bash
pip install -r requirements-dev.txt
ruff check demos scripts
(cd demos && PYTHONPATH=. pytest _core/tests -q)
PYTHONPATH=. pytest scripts/tests -q
for d in demos/[0-9]*/; do (cd "$d" && PYTHONPATH="..:." pytest -q); done
```
Expected: ruff clean; all suites pass.

- [ ] **Step 2: Build the site the way CI does**

```bash
cd site && npm ci && npm run build
```
Expected: 0 errors; `site/dist` produced.

- [ ] **Step 3: Manual end-to-end check (manual)**

- Run the ReAct Space locally (`cd demos/01-react-from-scratch && PYTHONPATH="..:." python app.py`), exercise it with a real key.
- Run the site (`cd site && npm run dev`), confirm the post embeds the Space and the layer grouping renders.

- [ ] **Step 4: Final commit (if anything was adjusted)**

```bash
git add -A
git commit -m "chore: walking skeleton verified end-to-end"
```

---

## Self-Review

**Spec coverage (§ refers to the design spec):**
- §3 architecture (site + Space + BYOK OpenRouter) → Tasks 5, 6, 8, 11–13. ✓
- §4 repo layout (`_core`, demo dir, copy-at-build) → Tasks 1–9, sync script copies `_core`. ✓
- §5 case-study anatomy (blog + Space + readable code) → Tasks 8, 13. ✓
- §6 `_core` modules (llm/tools/tracer/ui/models) → Tasks 1–6. ✓
- §6 web_search default DuckDuckGo → Task 3. (Tavily optional deferred to Plan 2 / demo #7.) ✓
- §7 i18n (content collections + UI dict + hreflang) → Tasks 11, 12. Fallback banner stubbed, completed in Plan 3. ✓
- §8 deploy (Cloudflare + HF, free tier, secrets) → Tasks 10, 14. ✓
- §10 testing (core unit tests + per-agent smoke + astro check) → Tasks 1–9, CI in 10. ✓

**Placeholder scan:** No TBD/TODO in code steps; every code step shows complete content. The MDX post is explicitly a launch-ready stub (full prose is Plan 3's scope), not a placeholder gap. ✓

**Type consistency:** `Step(kind, content, tokens, cost_usd, latency_ms)`, `Trace.add/total_tokens/total_cost`, `LLMResponse(content, tool_calls, prompt_tokens, completion_tokens)`, `LLMClient(api_key, model).chat(messages, tools)`, `ToolRegistry.register/to_openai_schema/execute`, `build_agent_app(...run_fn)` with `run_fn(llm, user_input) -> Iterator[Step]`, `ReActAgent(llm, tools, max_steps).run(question)` — all consistent across tasks and reused identically in app.py. ✓
