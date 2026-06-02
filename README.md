# Agentic AI — Engineering Showcase

Interview-grade agentic-AI problems, solved with modern techniques and runnable live (bring your own [OpenRouter](https://openrouter.ai/keys) key).

- **Site:** https://agentic.mashen.dev
- **Demos:** HuggingFace Spaces (see each case-study)

## Case studies

| # | Case study | Layer | Live demo |
|---|-----------|-------|-----------|
| 1 | [ReAct from scratch](https://agentic.mashen.dev/en/react-from-scratch) | Pattern | `demos/01-react-from-scratch` |
| 2 | [Plan-Execute-Reflect](https://agentic.mashen.dev/en/plan-execute-reflect) | Pattern | `demos/02-plan-execute` |
| 3 | [Orchestrator-Workers](https://agentic.mashen.dev/en/orchestrator-workers) | Pattern | `demos/03-orchestrator-workers` |
| 4 | [Evals & LLM-as-judge](https://agentic.mashen.dev/en/evals-llm-as-judge) | Production | `demos/04-evals-llm-as-judge` |
| 5 | [Observability & tracing](https://agentic.mashen.dev/en/observability-tracing) | Production | `demos/05-observability-tracing` |
| 6 | [Guardrails & retries](https://agentic.mashen.dev/en/guardrails-retries) | Production | `demos/06-guardrails-retries` |
| 7 | [Deep Research Agent](https://agentic.mashen.dev/en/deep-research) | Flagship | `demos/07-deep-research` |

Articles are available in English, Turkish, and Dutch.

## Repo layout
- `site/` — Astro static site (EN/TR/NL)
- `demos/` — Python Gradio demos, one HF Space each
- `demos/_core/` — shared LLM / tools / tracer / UI helpers

## Develop
```bash
pip install -r requirements-dev.txt
cd demos && PYTHONPATH=. pytest _core/tests -q
```

## Deployment

GitHub Actions secrets required:
- `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` — site → Cloudflare Pages (project `agentic-ai`)
- `HF_TOKEN` — demos → HuggingFace Spaces (user `mashen`)

DNS: point `agentic.mashen.dev` (CNAME) at the Cloudflare Pages project.
