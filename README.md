# EVDojo — Expert‑in‑the‑Loop Comparative Coaching (MVP)

EVDojo is a minimal, self‑contained demo that you can run locally. It includes:

- A FastAPI backend with A/B judging, a simple reward model, and utilities for items/variants.
- A dark‑mode static frontend with animated backgrounds, an expert labeling flow, a writing coach demo, and a webcam‑based interview analysis page.

The backend serves the static site from `frontend/` at the root path (`/`). No build step required.

## Repo Structure

Backend (FastAPI)
- `backend/app/main.py` — App factory, CORS, request ID, and static mount (`/` → `frontend/`).
- `backend/app/routers/*.py` — REST endpoints (items, variants, compare, rank, bandit, rm, judge, topics, etc.).
- `backend/app/bt.py` — Bradley–Terry online ranking.  `backend/app/bandit.py` — next duel selection.
- `backend/app/rm.py` — simple text reward model; `backend/app/variants.py` — variant generator.
- `backend/app/adapters/text_adapter.py` — normalization, features, redaction.
- `backend/app/moderation.py` — basic safety; `backend/app/storage.py` — in‑memory store.
- `tests/` — unit tests for BT, bandit, and RM.

Frontend (static)
- `frontend/index.html` — minimal landing with a large center logo, a short methodology blurb, and vertically stacked sections with dividers and image placeholders.
- `frontend/user.html` — continuous feedback writing demo (editor UI).  `frontend/user-feedback.html` — supporting feedback view.
- `frontend/expert.html` — expert entry; for testing it routes to `label.html` (scripts disabled).
- `frontend/label.html` — A/B email compare: two large, selectable cards, hover/selection styling, rationale input, Continue cycles through example pairs, and a small “Thanks” toast.
- `frontend/interview.html` — interview analysis: webcam video with an overlaid mask (MediaPipe Face Landmarker via CDN). Detects nod, smile, open mouth, frown, head shake, looking away, blink, brow, and posture with short coaching toasts.
- `frontend/styles.css` — global dark theme + animated radial gradient, shapes, and star “constellation”.
- `frontend/bg.js` — performant moving stars/lines (constellation) with adaptive throttling.
- `frontend/logo.svg`, `frontend/icon.svg` — branding and SVG favicon.

## Quick Start

1) Create a virtualenv and install minimal deps:

```
pip install fastapi uvicorn pydantic
```

2) Run the server (serves UI and API):

```
uvicorn backend.app.main:app --reload
```

3) Open the site at http://127.0.0.1:8000/

4) API docs at http://127.0.0.1:8000/docs

Notes
- Static site is mounted from `frontend/`. Favicon is `frontend/icon.svg`.
- For the interview page, your browser will prompt for camera access and needs WASM support.

## Frontend Pages

- Landing (`/`) — Large centered logo; “Algorithm & Methodology” placeholder; sections for “Start Coaching”, “Coach / Expert”, “Interview Analysis”, and “Admin” with dividers and image placeholders. Content is constrained to the middle third for readability.
- Writing Coach (`/user.html`) — Dark theme editor with a meter and suggestions.
- Expert Labeling (`/expert.html` → `/label.html`) — Two side‑by‑side email cards; click or keyboard (Enter/Space) to select; optional rationale input; Continue cycles through example pairs; toast thanks the user.
- Interview Analysis (`/interview.html`) — Video stream with absolute canvas overlay (mask) and a visible rounded frame border. Events trigger coaching toasts. Transparency and point size are configurable via `CONFIG.MASK_ALPHA` and `CONFIG.POINT_RADIUS`.

## Minimal API Flow (Text MVP)

1. Create item — `POST /items`
2. Generate variants — `POST /variants`
3. Rank — `GET /rank?item_id=...`
4. Next duel — `GET /next_duel?item_id=...`
5. Compare — `POST /compare`
6. Judge orchestration — `POST /judge`
7. Streaming scorer — `POST /rm/stream/score` (with calibration/metrics endpoints)

## Background & Performance

- Animated background uses CSS gradients + a canvas constellation. It throttles during scroll/low FPS and honors `prefers-reduced-motion`.
- Interview page uses MediaPipe Tasks from a CDN; all processing is in‑browser (no video leaves the device).

## Tests

```
pytest -q
```

## Implementation Notes

- In‑memory storage for the MVP; swap for Postgres/Supabase when ready.
- Reward model and judging are simple stubs for demonstration; improve prompts/models and safety when moving beyond local demos.

