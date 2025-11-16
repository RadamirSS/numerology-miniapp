# Numerology Mini App — Deploy Guide (Vercel + Render)

This repository contains:
- `frontend/` — React + Vite app (Telegram mini-app UI)
- `backend/` — FastAPI app (numerology calculations and AI interpretation)

Both parts are already working locally. The steps below prepare the project for deployment without changing business logic.

## 1) Structure and basics

- Frontend directory: `frontend/` (Vite + React)
- Backend directory: `backend/` (FastAPI)

Frontend scripts (in `frontend/package.json`):
- `dev`: `vite`
- `build`: `tsc -b && vite build`
- `preview`: `vite preview`

Backend entry point: `backend/app/main.py` exposing `app = FastAPI(...)`.

## 2) Frontend (Vercel) configuration

- API base URL is provided via Vite env variable: `VITE_API_URL`.
- The shared HTTP helpers live at `frontend/src/api.ts` and use:

```ts
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
```

Usage in code: requests are built as `${API_URL}/...` (see `postJSON`/`getJSON` in `src/api.ts`).

Environment files (create locally as needed):

```env
# frontend/.env or .env.local
VITE_API_URL=http://127.0.0.1:8000
```

Production example (on Vercel, set in Project → Settings → Environment Variables, do not commit the file):

```
VITE_API_URL=https://<YOUR_RENDER_BACKEND_URL>
```

Vite config (`frontend/vite.config.ts`) uses standard settings suitable for Vercel (no custom `base`).

Build locally:

```bash
cd frontend
npm install
npm run build
```

## 3) Backend (Render) configuration

Entry point: `backend/app/main.py` (FastAPI). CORS is configured to allow:
- `FRONTEND_ORIGIN` (via env; defaults to `http://127.0.0.1:5173`),
- Telegram Web domains.

Set `FRONTEND_ORIGIN` in Render (Environment → Environment Variables) to your Vercel URL, e.g. `https://<your-vercel-app>.vercel.app`.

Requirements file: `backend/requirements.txt` (contains FastAPI, Uvicorn, etc.).

Start command on Render (Web Service):

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 4) Local development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
# create .env or .env.local with:
# VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

Local addresses:
- Backend: http://127.0.0.1:8000
- Frontend (Vite): http://127.0.0.1:5173

## 5) Deploy

Vercel (Frontend):
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables:
  - `VITE_API_URL=https://<YOUR_RENDER_BACKEND_URL>`

Render (Backend):
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:
  - `FRONTEND_ORIGIN=https://<YOUR_VERCEL_URL>`
  - (plus any existing keys used in `backend/.env`, e.g. `OPENAI_API_KEY`, DB settings, etc.)

This guide avoids any refactors and only prepares the project for deployment. Existing logic and routes remain unchanged. 
*** End Patch

