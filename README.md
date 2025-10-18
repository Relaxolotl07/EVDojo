# Expert-in-the-Loop Comparative Coaching Platform (MVP)

This repo contains a FastAPI backend implementing the core MVP described in the build spec:
- Modality adapter (Text MVP)
- Variant generator (3 small interpretable edits)
- Comparative judging pipeline and BT ranking
- Dueling bandit (Thompson sampling-style) for next duel
- Simple reward model (linear pairwise) with reason-tag head
- Judge orchestration (RM → LLM stub → expert escalation)
- Safety guardrails and PII redaction (basic)
- Expert console endpoints (queue/label) and abuse reporting
- Streaming scorer endpoint with calibration, hysteresis, and metrics

## Structure
- `backend/app/main.py` FastAPI app and router wiring
- `backend/app/routers/*.py` REST endpoints
- `backend/app/bt.py` Rater-aware Bradley–Terry (online SGD)
- `backend/app/bandit.py` Next duel selection
- `backend/app/rm.py` Simple text RM with pairwise training
- `backend/app/variants.py` Text variants
- `backend/app/adapters/text_adapter.py` Normalization + features + redaction
- `backend/app/moderation.py` Safety checks
- `backend/app/storage.py` In-memory store (swap for Postgres later)
- `tests/` Unit tests for BT, bandit, RM

## Quick Start
1. Create a virtualenv and install deps:
   - `pip install fastapi uvicorn pydantic`
2. Run the server:
   - `uvicorn backend.app.main:app --reload`
3. Open docs at `/docs`.
4. Local frontend is served at `/` (static HTML/JS).

## Minimal Flow
1. Create item
   - `POST /items` with `{ user_id, modality: "text", content: { text }, context: { goal, ... } }`
2. Generate variants
   - `POST /variants` with `{ item_id }`
3. Rank
   - `GET /rank?item_id=...`
4. Next duel
   - `GET /next_duel?item_id=...`
5. Compare
   - `POST /compare` with `{ item_id, a_id, b_id, winner_id|null, judge_type, rater_id? }`
6. Judge orchestration (RM first)
   - `POST /judge` with `{ a: {features|compact_features}, b: {...}, context: {...} }`
7. Streaming scorer (text MVP)
   - `POST /rm/stream/score` with `{ modality, context, snippet, cursor?, rm_version?, user_id?, item_id?, mode? }`
   - Returns `{ p_win, confidence, state, tags, spans, suggestion, rm_version }`
   - Metrics: `GET /rm/metrics/stream`; Calibration meta: `GET /rm/calibration?rm_version=v1`
   - Apply suggestion to create a Variant: `POST /variants/apply_suggestion?item_id=...&diff_type=...&content_text=...`

## Local Frontend
- Path: `/` serves `frontend/index.html`
- Features:
  - Start session (creates Item), type in editor
  - Continuous scoring (debounced) with meter chip and one suggestion at a time
  - Apply suggestion (creates a new Variant) and refresh rank
  - Generate variants and view ranking

## Deploying with Cloudflare (evdojo.com)

Recommended architecture
- Frontend (Next.js): Cloudflare Pages at `evdojo.com` (or `app.evdojo.com`).
- Backend (FastAPI): any container host (e.g., Fly.io, Railway, Render, VPS) exposed as `api.evdojo.com` and proxied by Cloudflare (orange cloud).
- Optional: Cloudflare Worker proxy to expose `/api/*` on the root domain.

Backend hardening in this repo
- Proxy headers trusted: real client IP via `CF-Connecting-IP` is honored.
- Request ID middleware adds `X-Request-ID` for tracing.
- CORS is env-driven via `CORS_ALLOW_ORIGINS` (defaults include `https://evdojo.com`).
- Health endpoint: `GET /healthz`.
- Dockerfile: `backend/Dockerfile` exposes port 8080.

Steps
1) Buy domain and add to Cloudflare
   - Add `evdojo.com` to Cloudflare, update registrar nameservers.
2) Backend origin
   - Build and run container: `docker build -t evdojo-backend ./backend && docker run -p 8080:8080 evdojo-backend` (or deploy to Fly/Railway/Render).
   - Ensure health: visit `http://<origin-host>:8080/healthz`.
   - Set environment:
     - `CORS_ALLOW_ORIGINS=https://evdojo.com,https://www.evdojo.com,https://app.evdojo.com`
     - Optional: `STREAMING_ENABLED=true`, `DEBUG_DEMO=false` for prod.
3) Cloudflare DNS
   - Create `A`/`AAAA` or `CNAME` for `api.evdojo.com` pointing to your origin host. Enable proxy (orange cloud).
   - SSL/TLS → Full (Strict). Install a valid cert on origin.
4) Frontend (Cloudflare Pages)
   - Push `frontend-next` to a repo. In Cloudflare Pages, “Create project” → connect repo → set build command `npm run build` and output directory `.next` will be auto-handled by Pages (or follow Next-on-Pages docs).
   - In Pages project Settings → Environment variables:
     - `NEXT_PUBLIC_API_BASE=https://api.evdojo.com` (or use Worker proxy below and leave unset to use `/api`).
5) Optional: Worker proxy `/api/*`
   - In `cloudflare/wrangler.toml`, set `ORIGIN` to your backend origin (`https://api.evdojo.com`).
   - Deploy: `cd cloudflare && npx wrangler deploy`.
   - Add a route: `evdojo.com/api/*` on your zone.
   - Now the Next.js app can use relative `/api` (default in this repo), and Cloudflare will forward to the backend.
6) WAF/Rate limiting
   - Add a Rate Limiting rule on `/rm/stream/score` (e.g., 60 req/min per IP) and bot protections.

Notes
- If you prefer, host the backend on Cloudflare Tunnel instead of public IP: run `cloudflared tunnel` from your origin and bind `api.evdojo.com`.
- Cloudflare D1/R2 are not used in this MVP; use Postgres/Supabase for DB and optionally R2 for file storage later.
- For Pages SSR, consider `@cloudflare/next-on-pages` for advanced Next.js features.


Notes:
- In-memory storage for MVP; replace with Postgres models per spec when ready.
- RM and LLM are stubs; RM is trainable online via `/rm/train`.
- Safety check blocks goal keywords: harassment, deception, impersonation, harm.

## Tests
- `pytest -q` (requires `pytest`)

## Next Steps
- Persist to Postgres/Supabase with schema in spec
- Add expert console UI (Next.js) and dashboards
- Integrate small sentence embedder for RM features
- Implement real LLM judging with strict prompts and safety filters
