# Going live — deployment checklist

The code is on GitHub and CI is green. Deployment needs three things only you can do
(account access + an API key). The deploy workflows **skip gracefully** until the
secrets below exist, so the Actions tab stays green in the meantime.

## 1. Site → Cloudflare Pages (agentic.mashen.dev)

1. Cloudflare dashboard → **Create an API token** with the *Cloudflare Pages: Edit*
   permission. Copy it, and copy your **Account ID** (right sidebar of any domain).
2. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `CLOUDFLARE_API_TOKEN` = the token
   - `CLOUDFLARE_ACCOUNT_ID` = the account id
3. Cloudflare → **Workers & Pages → Create → Pages** → name the project **`agentic-ai`**
   (must match `--project-name` in `.github/workflows/site-deploy.yml`; change one to match the other if you prefer a different name).
4. Re-run the **Deploy site** workflow (Actions tab → Deploy site → Re-run), or push any
   change under `site/`. It builds `site/` and deploys `site/dist`.
5. In the Pages project → **Custom domains** → add `agentic.mashen.dev`. Cloudflare gives
   you a CNAME target; add that CNAME in your `mashen.dev` DNS.

## 2. Demos → HuggingFace Spaces

1. **Confirm your HF username.** The demos currently assume `mashen`
   (`spaceUrl` in the 21 MDX files = `https://mashen-agentic-<demo>.hf.space`, and
   `HF_USER: mashen` in `.github/workflows/space-sync.yml`). If your HF username differs,
   update those references first (one find/replace of `mashen-agentic-` and the `HF_USER`
   value).
2. HF → **Settings → Access Tokens** → create a **write** token.
3. GitHub repo secret: `HF_TOKEN` = that token.
4. Re-run the **Sync demos to HF Spaces** workflow (or push under `demos/`). It creates
   one Space per demo (`<user>/agentic-<demo>`) and uploads the demo + `_core/`.

## 3. Live smoke test (BYOK)

Open any deployed Space (or run locally: `cd demos/01-react-from-scratch &&
PYTHONPATH="..:." python app.py`), paste a real **OpenRouter** key, pick a model, and run.
This is the one path that hasn't been exercised end-to-end yet.

---

Once 1–2 are done, the LinkedIn sequence in `linkedin-posts.md` can go out.
