# Plan 3 — Content & i18n Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the site with all seven case-study articles in English, add Turkish and Dutch translations with a graceful fallback for missing languages, finish SEO (hreflang/sitemap/OG), and produce the LinkedIn launch materials — completing v1.

**Architecture:** Astro content collections, one folder per language (`en`/`tr`/`nl`), same `slug` across languages. Routing generates every `locale × slug` combination: a localized entry renders directly; a missing one falls back to the English entry with a banner. Prose verification is `astro check` + `astro build` (schema + route generation) plus a manual read — there are no unit tests for article text.

**Tech Stack:** Astro 4 + MDX (from Plan 1). No new dependencies.

**Prerequisite:** Plan 1 complete (site scaffold, layouts, routing, first EN post stub). Plan 2 complete (all 7 Spaces live, so `spaceUrl`s resolve).

**Spec:** `docs/superpowers/specs/2026-06-02-agentic-ai-showcase-design.md`

> **Execution corrections (learned during Plan 1 — apply these here):**
> - **Use `urlSlug`, not `slug`.** Astro reserves `slug` in content-collection schemas (build error). The schema already declares `urlSlug: z.string()`. Every post's frontmatter MUST include `urlSlug: "<slug>"`, and routing references `entry.data.urlSlug` (NOT `entry.data.slug` / `entry.slug`). In this plan's Task 1 `[slug].astro` rewrite, the `bySlug` grouping and `params` must key on `entry.data.urlSlug`.
> - **`@astrojs/sitemap` is currently disabled** in `astro.config.mjs` (3.7.3 crashes astro 4.16's `build:done` with `_routes` undefined). For Task 5, re-enable only with a version verified against astro 4.16 (test `npm run build` stays green) — or generate the sitemap manually. Don't assume the plan's snippet works as-is.
> - **i18n dict access must be typed** (`Record<string,string>`) or `astro check` fails under strict mode — already handled in `utils.ts`.
> - **Node 18+/20 required** (Astro 4 won't run on Node 16). Locally use homebrew node (`/opt/homebrew/bin`, node 24); CI uses node 20. Run `astro check`/`build` with that node on `PATH`.

> **Verification convention for this plan:** unless a step says otherwise, "verify" means run `cd site && npm run build` and expect `astro check` to report **0 errors** and the build to emit the expected routes. Article prose is additionally read in `npm run dev`.

---

### Task 1: Fallback routing (missing translations → EN + banner)

Replaces the EN-only routing from Plan 1 so every `locale × slug` resolves.

**Files:**
- Modify: `site/src/pages/[lang]/[slug].astro`
- Modify: `site/src/layouts/PostLayout.astro`
- Modify: `site/src/pages/[lang]/index.astro`

- [ ] **Step 1: Rewrite `site/src/pages/[lang]/[slug].astro`**

```astro
---
import { getCollection } from 'astro:content';
import PostLayout from '../../layouts/PostLayout.astro';
import { LOCALES } from '../../i18n/utils';

export async function getStaticPaths() {
  const all = await getCollection('posts');
  const bySlug = new Map<string, Map<string, (typeof all)[number]>>();
  for (const entry of all) {
    if (!bySlug.has(entry.data.slug)) bySlug.set(entry.data.slug, new Map());
    bySlug.get(entry.data.slug)!.set(entry.data.lang, entry);
  }
  const paths = [];
  for (const [slug, byLang] of bySlug) {
    const en = byLang.get('en');
    for (const lang of LOCALES) {
      const entry = byLang.get(lang) ?? en;
      if (!entry) continue; // require an EN canonical to fall back to
      paths.push({ params: { lang, slug }, props: { entry, lang, isFallback: !byLang.has(lang) } });
    }
  }
  return paths;
}

const { entry, lang, isFallback } = Astro.props;
const { Content } = await entry.render();
---
<PostLayout entry={entry} lang={lang} isFallback={isFallback}>
  <Content />
</PostLayout>
```

- [ ] **Step 2: Update `site/src/layouts/PostLayout.astro`** to use the requested `lang` for chrome/banner while keeping `entry` for content

```astro
---
import type { CollectionEntry } from 'astro:content';
import BaseLayout from './BaseLayout.astro';
import SpaceEmbed from '../components/SpaceEmbed.astro';
import { useTranslations } from '../i18n/utils';
interface Props { entry: CollectionEntry<'posts'>; lang: string; isFallback?: boolean }
const { entry, lang, isFallback = false } = Astro.props;
const { title, description, slug, spaceUrl, githubPath } = entry.data;
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

- [ ] **Step 3: Update `site/src/pages/[lang]/index.astro`** to list canonical (EN) posts with localized titles when available

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
const all = await getCollection('posts');
const canonical = all.filter((p) => p.data.lang === 'en').sort((a, b) => a.data.order - b.data.order);

function localized(slug: string) {
  return (
    all.find((p) => p.data.slug === slug && p.data.lang === lang) ??
    all.find((p) => p.data.slug === slug && p.data.lang === 'en')!
  );
}

const layers = ['pattern', 'production', 'flagship'] as const;
---
<BaseLayout lang={lang} title={t('site.title')} description={t('site.tagline')}>
  <h1>{t('site.title')}</h1>
  <p>{t('site.tagline')}</p>
  {layers.map((layer) => {
    const group = canonical.filter((p) => p.data.layer === layer);
    return group.length > 0 && (
      <section>
        <h2>{t(`layer.${layer}`)}</h2>
        <ul>
          {group.map((p) => {
            const loc = localized(p.data.slug);
            return (
              <li><a href={`/${lang}/${p.data.slug}`}>{loc.data.title}</a> — {loc.data.description}</li>
            );
          })}
        </ul>
      </section>
    );
  })}
</BaseLayout>
```

- [ ] **Step 4: Verify**

Run: `cd site && npm run build`
Expected: 0 errors. With only the EN ReAct post present, the build now also emits `/tr/react-from-scratch` and `/nl/react-from-scratch` as fallback pages. Confirm in `npm run dev` that `/tr/react-from-scratch` shows the "not translated" banner in Turkish.

- [ ] **Step 5: Commit**

```bash
git add site/src/pages/[lang]/[slug].astro site/src/layouts/PostLayout.astro site/src/pages/[lang]/index.astro
git commit -m "feat(site): fall back to English with a banner for missing translations"
```

---

### Task 2: Write the seven English articles

Each post follows the fixed 6-section template (problem → naïve → solution → tradeoffs → try it → read the code). Frontmatter must validate against the schema (`title, description, publishDate, lang, slug, spaceUrl, githubPath, order, layer`). The bodies below are complete and publishable; expand later if desired.

> Confirm each `spaceUrl` matches the actual deployed Space URL from Plan 2 (`https://mashen-agentic-<short>.hf.space`).

- [ ] **Step 1: Expand `site/src/content/posts/en/01-react-from-scratch.mdx`** (replace the Plan 1 stub body; keep frontmatter)

Body:
```mdx
## The interview problem

> "Implement an agent that answers questions needing both reasoning and external
> lookups — without hardcoding the steps."

## Why one prompt isn't enough

A single completion can't decide *mid-task* that it needs to search or compute.
It commits to an answer in one shot. ReAct breaks that open: the model thinks,
optionally acts (calls a tool), observes the result, and repeats.

## The loop

The whole pattern is a `while` loop over `chat()`: if the model returns tool
calls, execute them and append the results as `tool` messages; otherwise the
content is the final answer. Tools are described to the model as JSON schemas,
so it chooses *which* to call and *with what arguments*. The trace below makes
each thought/action/observation visible.

## Tradeoffs

- **Use it** when the tools needed vary per query and the path isn't known ahead.
- **Avoid it** when the workflow is fixed — a hardcoded pipeline is cheaper and
  more predictable (see the Observability case study for exactly that).
- **Watch** runaway loops: always cap `max_steps`.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 2: Create `site/src/content/posts/en/02-plan-execute.mdx`**

```mdx
---
title: "Plan-Execute-Reflect: agents that revise their own work"
description: "Draft a plan, execute it, then reflect and replan — for tasks a single loop drifts on."
publishDate: 2026-06-02
lang: en
slug: "plan-execute-reflect"
spaceUrl: "https://mashen-agentic-plan-execute.hf.space"
githubPath: "demos/02-plan-execute"
order: 2
layer: "pattern"
---

## The interview problem

> "Design an agent for multi-step tasks where the first attempt often misses
> requirements."

## Why a flat loop drifts

On long tasks a ReAct loop loses the thread — it optimizes the next step, not the
whole goal. Separating *planning* from *doing* keeps the objective explicit.

## The pattern

Three roles, one loop: a **planner** turns the task into ordered steps; an
**executor** runs each step (with tools); a **reflector** checks whether the goal
is met and, if not, emits feedback that seeds a fresh plan. Bounded by
`max_rounds`.

## Tradeoffs

- **Use it** for complex, requirement-heavy tasks where a first draft rarely suffices.
- **Avoid it** for simple lookups — the extra planner/reflector calls are wasted cost.
- **Watch** the round cap so reflection can't loop forever.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 3: Create `site/src/content/posts/en/03-orchestrator-workers.mdx`**

```mdx
---
title: "Orchestrator-Workers: dividing a task across specialists"
description: "A boss agent decomposes the task, dispatches specialist workers, and synthesizes their output."
publishDate: 2026-06-02
lang: en
slug: "orchestrator-workers"
spaceUrl: "https://mashen-agentic-orchestrator-workers.hf.space"
githubPath: "demos/03-orchestrator-workers"
order: 3
layer: "pattern"
---

## The interview problem

> "How would you split a broad task across specialized agents and recombine the
> results?"

## Why one generalist falls short

A single prompt asked to "cover everything" produces shallow, unfocused output.
Specialization — a historian, an economist, an engineer — yields depth.

## The pattern

An **orchestrator** decomposes the task into independent subtasks, each tagged
with a specialist role. Each **worker** is an LLM call under that role's system
prompt. The orchestrator then **synthesizes** the worker outputs into one answer.

## Tradeoffs

- **Use it** for broad tasks that decompose cleanly into independent parts.
- **Avoid it** for tightly coupled steps where workers would need to see each
  other's output mid-flight.
- **Watch** cost: it's `N + 2` model calls. Subtasks can run in parallel to cut latency.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 4: Create `site/src/content/posts/en/04-evals-llm-as-judge.mdx`**

```mdx
---
title: "Evals & LLM-as-judge: knowing your agent is actually good"
description: "Score answers against references with an LLM judge — the regression test for non-deterministic systems."
publishDate: 2026-06-02
lang: en
slug: "evals-llm-as-judge"
spaceUrl: "https://mashen-agentic-evals-llm-as-judge.hf.space"
githubPath: "demos/04-evals-llm-as-judge"
order: 4
layer: "production"
---

## The interview problem

> "Your agent's output isn't deterministic. How do you measure quality and catch
> regressions before users do?"

## Why eyeballing fails

Manual spot-checks don't scale and miss regressions. You need a repeatable score.

## The pattern

Hold a small **dataset** of inputs with reference answers. Run the system under
test, then have an **LLM judge** score each answer against its reference (1–5,
pass/fail), and **aggregate**. Run it in CI to gate changes.

## Tradeoffs

- **Use it** to track quality over time and block regressions automatically.
- **Be aware** judges have bias and variance — pin the judge model, use a strict
  rubric, and pair with exact-match checks where possible.
- **Cheap to run**: a handful of cases costs cents.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 5: Create `site/src/content/posts/en/05-observability-tracing.mdx`**

```mdx
---
title: "Observability & tracing: debugging agents in production"
description: "Capture tokens, cost, and latency per step — the instrumentation you need to debug and budget an agent."
publishDate: 2026-06-02
lang: en
slug: "observability-tracing"
spaceUrl: "https://mashen-agentic-observability-tracing.hf.space"
githubPath: "demos/05-observability-tracing"
order: 5
layer: "production"
---

## The interview problem

> "Your agent is slow and expensive in production. How do you find out why?"

## Why print statements aren't enough

Agents make many model and tool calls. Without structured per-step data you can't
see where the tokens, dollars, and milliseconds go.

## The pattern

Record a **Step** for every action with its tokens, estimated cost, and latency.
Render the **trace as a table** plus a **cost breakdown by step kind**. This demo
uses a fixed search→summarize pipeline so the trace is predictable — the point is
the instrumentation, not the agent.

## Tradeoffs

- **Always worth it**: the overhead is negligible and it's the foundation for
  cost control and evals.
- **Extend it** with persistent storage and dashboards when you go multi-user.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 6: Create `site/src/content/posts/en/06-guardrails-retries.mdx`**

```mdx
---
title: "Guardrails & retries: reliable output from an unreliable model"
description: "Validate structured output against a schema and retry with feedback; block disallowed input at the boundary."
publishDate: 2026-06-02
lang: en
slug: "guardrails-retries"
spaceUrl: "https://mashen-agentic-guardrails-retries.hf.space"
githubPath: "demos/06-guardrails-retries"
order: 6
layer: "production"
---

## The interview problem

> "Make an agent that returns reliable structured output and resists prompt
> injection."

## Why trusting the model fails

Models return *almost*-valid JSON, drift from schemas, and follow injected
instructions. You must verify at the boundary.

## The pattern

An **input guardrail** rejects over-long or disallowed prompts before any model
call. The agent then generates JSON, **validates** it against a schema, and on
failure **retries with the validation error fed back** — bounded by `max_retries`.

## Tradeoffs

- **Use it** whenever downstream code consumes the agent's output as data.
- **Watch** latency/cost: cap retries, and prefer the provider's structured-output
  mode when available as a first line of defense.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 7: Create `site/src/content/posts/en/07-deep-research.mdx`**

```mdx
---
title: "Deep Research Agent: from a topic to a cited brief"
description: "Plan sub-questions, search multiple sources, track citations, and synthesize a referenced report."
publishDate: 2026-06-02
lang: en
slug: "deep-research"
spaceUrl: "https://mashen-agentic-deep-research.hf.space"
githubPath: "demos/07-deep-research"
order: 7
layer: "flagship"
---

## The interview problem

> "Build an agent that researches a topic and produces a brief you can actually
> trust — with sources."

## Why search-then-summarize isn't enough

One query gives a shallow, uncited answer. Real research decomposes the topic and
keeps track of where each claim came from.

## The pattern

A **planner** splits the topic into sub-questions. The agent **searches** each
(DuckDuckGo by default, optional Tavily for quality), **tracks every source** with
a numbered id, and a **synthesizer** writes a brief that cites sources inline as
`[n]` with a sources list appended.

## Tradeoffs

- **Use it** when provenance matters and the topic spans several angles.
- **Watch** cost: it grows with the number of sub-questions and sources.
- **Swap** the search backend to trade cost for quality without touching the agent.

Run it live below with your own OpenRouter key.
```

- [ ] **Step 8: Verify all English content**

Run: `cd site && npm run build`
Expected: 0 errors; routes emitted for `/en/<slug>` for all 7 slugs, plus `/tr/<slug>` and `/nl/<slug>` fallback pages. Landing `/en/` groups posts under Patterns (3), Production (3), Flagship (1).

- [ ] **Step 9: Commit**

```bash
git add site/src/content/posts/en/
git commit -m "content: add all seven English case-study articles"
```

---

### Task 3: Turkish translations

Translate each EN article into Turkish. Frontmatter is identical except `lang: tr` and translated `title`/`description`; **`slug`, `spaceUrl`, `githubPath`, `order`, `layer`, `publishDate` stay the same**.

- [ ] **Step 1: Create `site/src/content/posts/tr/01-react-from-scratch.mdx`** (full worked example — translate the remaining six the same way)

```mdx
---
title: "Sıfırdan ReAct: akıl yürütme + eylem döngüsü"
description: "Agent'lar düşünmeyi ve araç kullanımını nasıl iç içe geçirir — ilk prensiplerden inşa edildi."
publishDate: 2026-06-02
lang: tr
slug: "react-from-scratch"
spaceUrl: "https://mashen-agentic-react-from-scratch.hf.space"
githubPath: "demos/01-react-from-scratch"
order: 1
layer: "pattern"
---

## Mülakat problemi

> "Hem akıl yürütme hem de dış kaynaklardan veri çekme gerektiren soruları —
> adımları sabit kodlamadan — yanıtlayan bir agent yaz."

## Neden tek bir prompt yetmez

Tek seferlik bir tamamlama, görev *ortasında* arama ya da hesap yapması
gerektiğine karar veremez; cevabı tek hamlede verir. ReAct bunu açar: model
düşünür, gerekirse bir araç çağırır, sonucu gözlemler ve tekrarlar.

## Döngü

Tüm desen `chat()` üzerinde dönen bir `while` döngüsüdür: model araç çağrısı
döndürürse onları çalıştırıp sonuçları `tool` mesajı olarak ekleriz; aksi halde
içerik nihai cevaptır. Araçlar modele JSON şeması olarak tanıtılır, böylece
*hangisini* ve *hangi argümanlarla* çağıracağını model seçer.

## Dengeler (tradeoff)

- **Kullan**: gereken araçlar sorgudan sorguya değişiyorsa ve yol önceden belli değilse.
- **Kullanma**: akış sabitse — sabit kodlanmış bir pipeline daha ucuz ve öngörülebilir.
- **Dikkat**: kontrolden çıkan döngülere karşı her zaman `max_steps` koy.

Aşağıda kendi OpenRouter anahtarınla canlı dene.
```

- [ ] **Step 2: Create the remaining six Turkish articles**

Create `tr/02-plan-execute.mdx` … `tr/07-deep-research.mdx`. For each, copy the matching EN frontmatter, change `lang` to `tr`, translate `title`/`description`, and translate the body using the same section structure (Mülakat problemi / Neden … yetmez / Desen / Dengeler / canlı dene). Keep technical terms (ReAct, tool, JSON, trace, eval) as-is where they're standard in Turkish technical writing.

- [ ] **Step 3: Verify**

Run: `cd site && npm run build`
Expected: 0 errors; `/tr/<slug>` for all 7 now render translated content (no fallback banner). Spot-check `/tr/` landing shows Turkish titles.

- [ ] **Step 4: Commit**

```bash
git add site/src/content/posts/tr/
git commit -m "content: add Turkish translations for all seven articles"
```

---

### Task 4: Dutch translations

Same procedure as Turkish, `lang: nl`. Per the spec, NL may ship incrementally — but with the fallback in place, any not-yet-translated post degrades gracefully to English. Complete all seven when possible.

- [ ] **Step 1: Create `site/src/content/posts/nl/01-react-from-scratch.mdx`** (full worked example)

```mdx
---
title: "ReAct vanaf nul: de redeneer- en actielus"
description: "Hoe agents redeneren en tools afwisselen — opgebouwd vanuit de basisprincipes."
publishDate: 2026-06-02
lang: nl
slug: "react-from-scratch"
spaceUrl: "https://mashen-agentic-react-from-scratch.hf.space"
githubPath: "demos/01-react-from-scratch"
order: 1
layer: "pattern"
---

## Het sollicitatieprobleem

> "Bouw een agent die vragen beantwoordt die zowel redeneren als externe
> opzoekingen vereisen — zonder de stappen hard te coderen."

## Waarom één prompt niet volstaat

Een enkele voltooiing kan niet *tijdens* de taak besluiten dat er gezocht of
gerekend moet worden; ze kiest in één keer een antwoord. ReAct doorbreekt dat: het
model denkt, roept eventueel een tool aan, observeert het resultaat en herhaalt.

## De lus

Het hele patroon is een `while`-lus over `chat()`: geeft het model tool-aanroepen
terug, voer ze uit en voeg de resultaten toe als `tool`-berichten; anders is de
inhoud het eindantwoord. Tools worden als JSON-schema's aan het model beschreven,
zodat het kiest *welke* het aanroept en *met welke argumenten*.

## Afwegingen

- **Gebruik het** wanneer de benodigde tools per vraag verschillen en het pad niet vooraf vaststaat.
- **Vermijd het** bij een vaste workflow — een hardgecodeerde pipeline is goedkoper en voorspelbaarder.
- **Let op** doorslaande lussen: begrens altijd `max_steps`.

Probeer het hieronder live met je eigen OpenRouter-sleutel.
```

- [ ] **Step 2: Create the remaining six Dutch articles**

Create `nl/02-plan-execute.mdx` … `nl/07-deep-research.mdx`, mirroring the EN frontmatter with `lang: nl` and Dutch `title`/`description`/body, same section structure (Het sollicitatieprobleem / Waarom … niet volstaat / Het patroon / Afwegingen / live).

- [ ] **Step 3: Verify**

Run: `cd site && npm run build`
Expected: 0 errors; `/nl/<slug>` render translated content for every post created; any not created still resolve via the EN fallback banner (no broken routes).

- [ ] **Step 4: Commit**

```bash
git add site/src/content/posts/nl/
git commit -m "content: add Dutch translations for all seven articles"
```

---

### Task 5: SEO finishing touches

**Files:**
- Create: `site/public/robots.txt`
- Modify: `site/src/layouts/BaseLayout.astro` (add OG/Twitter meta + canonical)

- [ ] **Step 1: Create `site/public/robots.txt`**

```
User-agent: *
Allow: /

Sitemap: https://agentic.mashen.dev/sitemap-index.xml
```

- [ ] **Step 2: Add Open Graph / Twitter / canonical meta to `BaseLayout.astro`** (inside `<head>`, after the existing `<meta name="description">` block)

```astro
    <link rel="canonical" href={`${site}${Astro.url.pathname}`} />
    <meta property="og:type" content="article" />
    <meta property="og:title" content={title} />
    {description && <meta property="og:description" content={description} />}
    <meta property="og:site_name" content="agentic.mashen.dev" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content={title} />
    {description && <meta name="twitter:description" content={description} />}
```

- [ ] **Step 3: Verify**

Run: `cd site && npm run build`
Expected: 0 errors; `npm run build` emits `sitemap-index.xml` (the `@astrojs/sitemap` integration was added in Plan 1). Confirm `dist/robots.txt` and `dist/sitemap-index.xml` exist.

Run: `ls site/dist/robots.txt site/dist/sitemap-index.xml`
Expected: both paths listed.

- [ ] **Step 4: Commit**

```bash
git add site/public/robots.txt site/src/layouts/BaseLayout.astro
git commit -m "feat(site): add robots.txt, sitemap reference, and OG/Twitter meta"
```

---

### Task 6: Landing polish + minimal global styles

**Files:**
- Create: `site/src/styles/global.css`
- Modify: `site/src/layouts/BaseLayout.astro` (import the stylesheet; basic header/footer layout)

- [ ] **Step 1: Create `site/src/styles/global.css`**

```css
:root {
  --max-width: 46rem;
  --fg: #1a1a2e;
  --muted: #5a5a72;
  --accent: #3b3bd6;
  --bg: #fafafe;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
  color: var(--fg);
  background: var(--bg);
  line-height: 1.65;
}
header, main, footer { max-width: var(--max-width); margin: 0 auto; padding: 1rem 1.25rem; }
header { display: flex; justify-content: space-between; align-items: center; }
header a { font-weight: 600; text-decoration: none; color: var(--fg); }
.lang-switcher a { margin-left: 0.5rem; color: var(--muted); text-decoration: none; }
.lang-switcher a[aria-current="page"] { color: var(--accent); font-weight: 700; }
a { color: var(--accent); }
.banner { background: #fff4d6; border: 1px solid #e6c200; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.9rem; }
article h1 { line-height: 1.2; }
iframe { border-radius: 10px; border: 1px solid #e2e2ee; }
section h2 { margin-top: 2rem; }
footer { color: var(--muted); border-top: 1px solid #e2e2ee; margin-top: 3rem; }
```

- [ ] **Step 2: Import the stylesheet in `BaseLayout.astro`** (add to frontmatter)

```astro
import '../styles/global.css';
```

- [ ] **Step 3: Verify (manual)**

Run: `cd site && npm run dev`
Expected: landing and a post render with readable typography, a centered column, a highlighted current language in the switcher, and the styled fallback banner on a `/tr/` or `/nl/` page that isn't translated yet.

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/global.css site/src/layouts/BaseLayout.astro
git commit -m "feat(site): add global styles and polish landing/header"
```

---

### Task 7: Launch materials (LinkedIn + README)

**Files:**
- Create: `docs/launch/linkedin-posts.md`
- Modify: `README.md` (complete the case-study table)

- [ ] **Step 1: Create `docs/launch/linkedin-posts.md`** — a serialized announcement plan (per the spec's launch sequence)

```markdown
# LinkedIn launch sequence

Strategy: ship landing + 2–3 case studies, then post 1–2 per week. Each post links
to one article (problem → solution → live demo). Mix EN and TR posts.

## Post 0 — Launch announcement
> I built an Agentic AI engineering showcase: interview-grade problems, solved with
> modern techniques, each runnable live in your browser (bring your own OpenRouter
> key — multi-model). First three case studies are up: ReAct from scratch,
> Plan-Execute-Reflect, and Evals with LLM-as-judge.
> 👉 https://agentic.mashen.dev
> Code (MIT): https://github.com/shenmali/agentic-ai-first

## Post 1 — ReAct from scratch
Hook: "Most 'agents' are one prompt in a trench coat. Here's the actual loop." +
link to /en/react-from-scratch.

## Post 2 — Evals & LLM-as-judge
Hook: "How do you unit-test something non-deterministic? You don't — you eval it." +
link to /en/evals-llm-as-judge.

## Post 3 — Deep Research Agent (flagship)
Hook: "A research agent that actually cites its sources." + short screen capture of
the live trace + link to /en/deep-research.

## Posts 4–7 — remaining case studies
Plan-Execute-Reflect, Orchestrator-Workers, Observability, Guardrails — one per week.

## Notes
- Post a Turkish variant of the launch + flagship for the TR network.
- Each post: 1 hook line, 2–3 value lines, 1 link, 3–5 hashtags
  (#AgenticAI #LLM #AIEngineering).
```

- [ ] **Step 2: Complete the case-study table in `README.md`** (replace the single-line "Case studies" section from Plan 1)

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add docs/launch/linkedin-posts.md README.md
git commit -m "docs: add LinkedIn launch sequence and complete case-study table"
```

---

### Task 8: Final v1 verification

- [ ] **Step 1: Build the whole site**

Run: `cd site && npm ci && npm run build`
Expected: 0 errors. Routes: `/`, `/en/`, `/tr/`, `/nl/`, and `/<lang>/<slug>` for all 7 slugs × 3 languages (21 post routes), plus `sitemap-index.xml` and `robots.txt`.

- [ ] **Step 2: Manual review (manual)**

In `npm run dev`: visit `/en/`, `/tr/`, `/nl/`; open one post per layer; switch languages on a post and confirm the switcher + (where applicable) the fallback banner behave; confirm each post embeds the correct Space iframe.

- [ ] **Step 3: Confirm v1 Definition of Done (spec §12)**

- [ ] 7 Spaces live via BYOK (verified in Plan 2)
- [ ] 7 posts EN complete + TR complete; NL complete-or-fallback
- [ ] Landing + language switcher + navigation to all 7
- [ ] CI green, auto-deploy working (Plan 1)
- [ ] README pitch + LinkedIn draft (this plan)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: v1 content and i18n complete"
```

---

## Self-Review

**Spec coverage:** §7 i18n (content collections per language, UI dict, hreflang, fallback) → Tasks 1–4; `hreflang` shipped in Plan 1 BaseLayout, fallback in Task 1. §7 SEO (`hreflang`, sitemap, NL emphasis) → Task 5. §5 article template (6 sections) → Task 2 bodies. §12 DoD (EN+TR complete, NL incremental, README + LinkedIn) → Tasks 2–4, 7, 8. ✓

**Placeholder scan:** EN articles (Task 2) are complete, publishable bodies — not placeholders. TR/NL tasks provide a full worked example (post #1) and an exact, mechanical procedure for the remaining six; translations are content the implementer generates, not undefined code. No TODO/TBD gating the build. ✓

**Type/route consistency:** Frontmatter fields match the Zod schema from Plan 1 (`title, description, publishDate, lang, slug, spaceUrl, githubPath, order, layer`). `slug` is shared across languages so routing and the language switcher line up. `PostLayout` now takes `{entry, lang, isFallback}` consistently between Task 1's route and layout edits. `spaceUrl`s follow `https://mashen-agentic-<short>.hf.space`, matching the Space ids produced by Plan 2's `_space_id` (`agentic-<short>`). ✓
