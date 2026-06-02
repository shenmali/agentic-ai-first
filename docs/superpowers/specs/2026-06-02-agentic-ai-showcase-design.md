# Agentic AI Showcase — Design Spec

**Date:** 2026-06-02
**Status:** Approved (brainstorming complete)
**Owner:** mashen.dev
**Topic:** Portfolio showcase project — a blog + live-demo hybrid that solves the kinds of agentic-AI problems companies ask in interviews, with modern technical solutions.

---

## 1. Goal & Context

Build a public, live-testable portfolio piece that demonstrates agentic-AI engineering depth across a beginner→advanced spectrum. It is the author's flagship "vitrin" (showcase) project, announced on LinkedIn with serialized posts, targeting the Dutch/international AI-engineering job market.

Each unit pairs a **technical blog post** (problem → naïve approach → solution → tradeoffs) with a **working live demo** the visitor can run with their own API key.

**Non-goals for v1:** a published framework package, user accounts, a backend that pays for inference, or fully localized demo UIs. See §10.

---

## 2. Key Decisions (from brainstorming)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project shape | Blog + live demos hybrid | Best fit for LinkedIn serialization + technical depth |
| Audience | Mixed (beginner → advanced) | Broad reach; layered content |
| Content theme | Hybrid: patterns + production + flagship | Covers the most ground for interview-style problems |
| Demo run model | **BYOK** (Bring Your Own Key) | Zero runtime cost to author; no backend needed |
| LLM access | **OpenRouter**, model selectable by visitor | Multi-provider for free; visitor picks model |
| Demo hosting | HuggingFace Spaces (Python, Gradio) | Python is the agentic-AI lingua franca; free CPU tier |
| Blog/site | `agentic.mashen.dev` (Astro, static) | Matches main portfolio (Astro); MDX-native |
| Site deploy | Cloudflare Pages (GitHub Pages fallback) | Free, fast CDN, PR previews, easy custom subdomain |
| Languages | EN (canonical) + TR + NL | Dutch job market target; EN for international reach |
| Architecture | **Pragmatic Monorepo (Approach A)** | Fast v1; shared `_core.py`; evolve to framework in v2 |
| v1 scope | 7 case-studies | Substantial but shippable |

---

## 3. System Architecture

```
Visitor (arrives from LinkedIn, holds an OpenRouter API key)
        │
        ├──────────────────────────┐
        ▼                           ▼
agentic.mashen.dev            huggingface.co/spaces/mashen/agentic-<demo>
(Astro static site)           (Python Gradio app)
 • Landing                     • BYOK key input
 • 7 case-study posts          • Model selector (OpenRouter catalog)
   (EN/TR/NL)         iframe   • Live agent run
 • Each post embeds  ───────▶  • Streaming trace viewer
   its matching Space          • Cost / latency / token metrics
        ▲                           │
        │                           ▼
        │                     OpenRouter (visitor's key)
        │
GitHub: github.com/mashen/agentic-ai  (public monorepo)
 • /site            Astro source
 • /demos           7 Python Space sources
 • /demos/_core     shared LLM / tool / trace / UI helpers
 • /.github/workflows  CI + deploy to Cloudflare Pages & HF Spaces
```

**Request flow:**
1. Visitor follows a LinkedIn link → `agentic.mashen.dev` → a case-study post.
2. Post presents problem + approach + code excerpts; ends with an embedded HF Space iframe.
3. Visitor pastes their OpenRouter API key, selects a model, runs the agent.
4. The Space calls OpenRouter directly (visitor's key) and streams the trace into the UI.
5. "Read the code" button → the matching folder in the GitHub repo.

**Isolation & dependencies:**
- The site emits static HTML only (no server). Deploy target: Cloudflare Pages.
- Each Space is an independent Python sandbox with its own `requirements.txt`.
- **The API key never passes through the author's infrastructure** — it lives in the Gradio session (client-supplied), used only to call OpenRouter. Never logged, never persisted.

---

## 4. Repository Layout

```
agentic-ai/
├── README.md                    # pitch + 7 case-study links + LinkedIn link
├── LICENSE                      # MIT
├── .github/workflows/
│   ├── site-deploy.yml          # Astro → Cloudflare Pages (on site/** change)
│   ├── space-sync.yml           # demo folder → its HF Space (on demos/** change)
│   └── ci.yml                   # ruff + pytest + astro check
├── site/                        # Astro static site
│   ├── astro.config.mjs
│   ├── package.json
│   ├── src/
│   │   ├── content/posts/
│   │   │   ├── en/01-react-from-scratch.mdx … (7 posts)
│   │   │   ├── tr/ … (same 7)
│   │   │   └── nl/ … (same 7)
│   │   ├── layouts/
│   │   ├── components/
│   │   │   ├── SpaceEmbed.astro
│   │   │   ├── LanguageSwitcher.astro
│   │   │   └── CodeBlock.astro
│   │   ├── i18n/ {en,tr,nl}.json    # UI strings
│   │   └── pages/
│   │       ├── index.astro
│   │       └── [lang]/[slug].astro
│   └── public/
└── demos/
    ├── _core/                   # SHARED — every Space imports this
    │   ├── __init__.py
    │   ├── llm.py               # OpenRouter client wrapper (BYOK)
    │   ├── tools.py             # Tool dataclass + ToolRegistry
    │   ├── tracer.py            # Step / Trace / cost & latency tracking
    │   ├── ui.py                # Gradio helpers (key input, model selector, trace panel)
    │   └── models.py            # curated OpenRouter model catalog
    ├── 01-react-from-scratch/
    │   ├── app.py               # Gradio entry (HF Space main file)
    │   ├── agent.py             # ReAct loop implementation
    │   ├── requirements.txt
    │   ├── README.md            # HF Space landing
    │   └── .space.yml           # HF Space config (sdk: gradio)
    ├── 02-plan-execute/
    ├── 03-orchestrator-workers/
    ├── 04-evals-llm-as-judge/
    ├── 05-observability-tracing/
    ├── 06-guardrails-retries/
    └── 07-deep-research/
```

**Decisions:**
- `demos/_core/` is a **shared local module, not a PyPI package** (Approach A). Demos use `from _core.llm import …`. At Space build time, the `_core/` folder is **copied** into each Space (CI step) — editable installs don't work across isolated Spaces, copying is the correct mechanism.
- **HF Space sync:** each demo folder is pushed as its own HF Space repo via `huggingface_hub`. The sync workflow copies `_core/` + the demo folder into the Space repo. The monorepo stays clean; Space repos hold their own git history.
- **Astro content collections:** one folder per language, same slug. Missing TR/NL → fall back to EN with a "not yet translated" banner (not a 404).
- **Versioning:** `main` is always live. New case-studies arrive via PR (author can self-review using the code-review skill). Merge → auto-deploy.

---

## 5. Case-Study Anatomy

Every case-study is a 3-layer unit following a fixed skeleton, so understanding one makes the rest fast to scan.

**Layer 1 — Blog post (Astro MDX, 3 languages).** Fixed template:
1. **Problem** — framed as an interview scenario.
2. **Naïve approach** — why it falls short (brief).
3. **Solution** — the pattern/technique, with a diagram + code excerpts.
4. **Tradeoffs** — when to use, when not to.
5. **Try it live** — embedded HF Space.
6. **Read the code** — GitHub folder link.

**Layer 2 — HF Space (Gradio app).** Fixed UI skeleton (from `_core/ui.py`):
- Top: OpenRouter API key input (password field) + "how to get a key" link + model selector dropdown.
- Middle: problem-specific input (e.g. a question for ReAct, a research topic for Deep Research).
- Trace viewer: each step (thought → action → observation → final) streams in as it happens.
- Bottom: run metrics — tokens, estimated cost, latency, step count.

**Layer 3 — Source code (GitHub, readable).**
- `agent.py` — the essence of the pattern; commented but clean (educational).
- `app.py` — thin Gradio glue.

**Consistency principle:** all 7 demos reuse the same key-input, model-selector, and trace-viewer components from `_core/ui.py`. Only the problem-specific middle changes. This speeds the build and gives a coherent "single product" feel.

**Trace viewer is the centerpiece.** Transparently showing the agent's reasoning is the most compelling part of the project. Each step records: kind (thought/action/observation/final), content, that step's tokens/cost, and latency. It streams (Gradio `yield`). This simultaneously proves "the agent really runs" and "the author understands observability."

---

## 6. Shared `_core/` Module

The core that demonstrates engineering depth and keeps the 7 demos consistent. Each file has one responsibility.

**`_core/llm.py` — OpenRouter client wrapper**
```python
class LLMClient:
    def __init__(self, api_key: str, model: str): ...
    def chat(self, messages, tools=None) -> LLMResponse: ...      # single turn
    def stream(self, messages, tools=None) -> Iterator[Delta]: ... # streaming
```
- Uses OpenRouter's OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`).
- BYOK: key passed to constructor, never logged or persisted.
- Normalizes tool calling to OpenRouter's function-calling format.
- `LLMResponse` carries: content, tool_calls, usage (prompt/completion tokens).

**`_core/tools.py` — Tool abstraction**
```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict        # JSON schema
    fn: Callable

class ToolRegistry:
    def register(self, tool: Tool): ...
    def to_openai_schema(self) -> list: ...
    def execute(self, name, args) -> str: ...
```
- Common tools live here: `web_search` (DuckDuckGo default — keyless, zero BYOK friction; optional Tavily key field for the Deep Research flagship where quality matters), `calculator`, `python_exec` (sandboxed). Each demo selects what it needs.

**`_core/tracer.py` — Observability primitive**
```python
@dataclass
class Step:
    kind: Literal["thought","action","observation","final"]
    content: str
    tokens: int
    cost_usd: float
    latency_ms: int

class Trace:
    steps: list[Step]
    def add(self, step: Step): ...
    def total_cost(self) -> float: ...
    def total_tokens(self) -> int: ...
```
- All demos produce a trace; case-study #5 (Observability) builds a *deep visualization* on top of it.

**`_core/ui.py` — Shared Gradio components**
- `api_key_input()` — password field + "how to get a key" link.
- `model_selector()` — dropdown from `models.py`.
- `trace_panel(trace)` — renders steps with color/icons by kind.
- `metrics_bar(trace)` — token/cost/latency summary.

**`_core/models.py` — Model catalog**
- Curated OpenRouter list: cheap (Haiku, GPT-4o-mini, Gemini Flash, DeepSeek) + strong (Opus, GPT-4o, Gemini Pro). Default = a cheap model (protects the visitor's wallet).

**Design principle:** `_core` contains **no agent patterns** — only infrastructure (LLM access, tools, trace, UI). The patterns themselves live in each demo's `agent.py`. This separation matters: visitors see real pattern code, not "framework magic." `_core` only removes repetition.

---

## 7. Internationalization (EN / TR / NL)

Two distinct translation layers; do not conflate them.

**1. Content translation (blog posts) — Astro Content Collections.**
- `site/src/content/posts/{en,tr,nl}/<slug>.mdx` — same slug, different folder.
- Routing: `/[lang]/[slug]` — SEO-friendly, shareable.
- `en` is canonical. Missing TR/NL → EN fallback + "not yet translated in [lang]" banner.
- Frontmatter: `lang`, `title`, `description`, `publishDate`, `spaceUrl`, `githubPath`.

**2. UI translation (interface strings) — simple JSON dictionaries.**
- `site/src/i18n/{en,tr,nl}.json` for nav, buttons, footer, banners.

**Language switcher:** EN/TR/NL in the header; goes to the same slug in the chosen language (else fallback). Preference stored in `localStorage`.

**Demo (Space) language: English only.** 7 Spaces × 3 languages = 21 UIs is unsustainable. Demo UI is minimal/universal (key, model, run, trace); the localized blog post supplies context. This is a deliberate YAGNI call.

**Translation workflow:** author writes EN; Claude produces TR/NL drafts (author reviews). Each case-study's DoD: all 3 languages present OR the fallback banner works correctly. v1 launch requires EN+TR complete; NL may arrive incrementally.

**SEO:** `hreflang` tags per language. NL `hreflang` matters for the Dutch job-market target.

---

## 8. Deployment & CI

Two deploy targets, two triggers.

**Site — `agentic.mashen.dev`**
- Target: Cloudflare Pages (GitHub Pages fallback if DNS isn't on Cloudflare).
- Trigger: push to `main` touching `site/**`.
- Flow: `astro build` → static output → Cloudflare Pages.
- DNS: `agentic` CNAME → Cloudflare Pages.
- Cloudflare gives free CDN + per-PR preview deployments (nice for a portfolio).

**Demos — HuggingFace Spaces**
- Target: `huggingface.co/spaces/mashen/agentic-<demo-name>`.
- Trigger: push to `main` touching `demos/<name>/**` or `demos/_core/**`.
- Flow (`space-sync.yml`):
  1. Detect changed demo(s) (`_core` change → all).
  2. For each: prepare a temp folder → copy `demos/<name>/*` + `demos/_core/`.
  3. Push to that Space repo via `huggingface_hub`.
  4. HF auto-builds (Gradio SDK).
- Secret: `HF_TOKEN` (GitHub Actions secret) — for deploy only. The agent never runs server-side; the visitor's BYOK key drives inference.

**When `_core` changes:** all 7 Spaces re-sync. Acceptable (rare once `_core` stabilizes). Path-filtering to only affected Spaces is a later optimization.

**CI quality gate (`ci.yml`):**
- `ruff` lint + `pytest` (`_core` unit tests + each agent's smoke test).
- Astro: `astro check` (type + content-schema validation).
- No deploy without green.

**Cost:** all free tier — Cloudflare Pages (free), HF Spaces (free CPU tier), GitHub Actions (unlimited on public repos). Runtime LLM cost is the visitor's (BYOK). **Author's monthly cost: $0.**

**HF free-tier note:** CPU-only; Spaces sleep when idle (~30s cold start on first request). Agents do no heavy compute (just LLM API calls), so CPU tier suffices. Cold start is managed with a "demo waking up" message in the blog.

---

## 9. v1 Scope — 7 Case-Studies

| # | Case-study | Layer | Headline technique |
|---|-----------|-------|--------------------|
| 1 | ReAct from scratch | Pattern | Reasoning+Acting loop, tool-calling basics |
| 2 | Plan-Execute-Reflect | Pattern | Planner + executor + reflection loop |
| 3 | Orchestrator-Workers | Pattern | Multi-agent dispatch, parallel subtasks |
| 4 | Evals & LLM-as-judge | Production | Ground-truth + judge, eval scoring |
| 5 | Observability & tracing | Production | Deep trace visualization, cost/latency analysis |
| 6 | Guardrails & retries | Production | Output validation, structured retry, failure recovery |
| 7 | Deep Research Agent | Flagship | Multi-source, citation tracking, parallel exploration |

---

## 10. Testing Strategy

Light but real:
- **`_core` unit tests:** `LLMClient` (mocked OpenRouter response), `ToolRegistry`, `Tracer` cost math.
- **Per-`agent.py` smoke test:** one full loop runs without error using a mock LLM (no real API calls, deterministic).
- **Astro:** `astro check` validates content schema (catches broken frontmatter / missing fields).

This guarantees **code health**, not agent quality (LLMs are non-deterministic). Agent quality is demonstrated in case-study #4 via evals — the project itself uses the eval pattern it teaches.

---

## 11. Out of Scope for v1 (Deliberate YAGNI)

- ❌ `agentic-core` PyPI package — v2 ("framework evolution" story).
- ❌ Pre-recorded trace replay — BYOK makes it unnecessary.
- ❌ Pre-funded / rate-limited backend — BYOK = zero backend.
- ❌ Demo UIs in 3 languages — only the blog localizes.
- ❌ User accounts, sign-up, database — fully static + client-side.
- ❌ Computer-use / browser-use demo — too fragile; a v2 flagship candidate.
- ❌ Model-comparison arena — nice but scope creep; v2.

---

## 12. Definition of Done (v1)

1. 7 Spaces live and working via BYOK.
2. 7 blog posts: EN complete + TR complete (NL incremental, fallback works).
3. Landing page + language switcher + navigation to all 7 posts.
4. CI green, auto-deploy working.
5. README pitch + LinkedIn announcement draft.

**Suggested launch sequence (for LinkedIn momentum):** ship landing + the first 2–3 case-studies, then add 1–2 per week to create a "series" feel. Each addition = a new LinkedIn post.

---

## 13. Future (v2+)

- Extract `_core` into a published `agentic-core` package — narrate the "from duplication to framework" evolution.
- Add a flashy flagship: computer-use / browser-use agent.
- Model-comparison arena (run the same pattern across models side-by-side).
- Path-filtered Space sync (only redeploy affected Spaces on `_core` change).
