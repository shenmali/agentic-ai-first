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
