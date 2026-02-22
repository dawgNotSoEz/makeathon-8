# KIRA Workspace

KIRA is a full-stack regulatory intelligence platform:

- `kira-v2`: React + TypeScript frontend for dashboards, document views, analysis, and assistant workflows.
- `kira-backend`: FastAPI backend for policy retrieval, analysis, assistant responses, health, and metrics.

## What this project does

In simple professional terms, KIRA helps teams:

- collect and organize regulatory/policy content,
- analyze impact on an organization profile,
- query insights through an assistant-style interface,
- monitor platform health and operational readiness.

## Repository Structure

- `kira-v2/` – frontend application (Vite)
- `kira-backend/` – backend API and services
- `intro-page/` – additional UI assets/page work

## Core Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind
- Backend: FastAPI, Gunicorn/Uvicorn
- Infra dependencies: Redis (cache/rate limit), Chroma (vector store)
- LLM providers: OpenAI and/or Gemini and/or MegaLLM

---

## Run Locally (Recommended for development)

### 1) Start backend dependencies

Make sure Redis and Chroma are running and reachable.

Default backend expectations:

- `REDIS_URL` (example: `redis://localhost:6379/0`)
- `CHROMA_HOST` (example: `127.0.0.1`)
- `CHROMA_PORT` (default: `8001`)

### 2) Configure backend environment

Create/update `kira-backend/.env` with required values:

- `REDIS_URL`
- `CHROMA_HOST`
- `JWT_SECRET`
- one or more LLM keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, or `MEGA_LLM_API_KEY`)

Use your own API key if you want the project to be running.

Optional examples:

- `LLM_PROVIDER=auto`
- `ENVIRONMENT=dev`
- `PORT=8000`

### 3) Run backend

From workspace root:

```powershell
cd kira-backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Health check:

```powershell
curl http://127.0.0.1:8010/api/health
```

### 4) Configure and run frontend

Create/update `kira-v2/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
# Optional (only if backend auth is enabled for your flow)
# VITE_API_AUTH_TOKEN=<token>
```

Run frontend:

```powershell
cd kira-v2
npm install
npm run dev
```

Build frontend:

```powershell
npm run build
```

---

## Run Backend with Docker

From `kira-backend/`:

```powershell
docker build -t kira-backend:prod .
docker run --env-file .env -p 8000:8000 kira-backend:prod
```

Notes:

- Container still needs external Redis and Chroma endpoints from `.env`.
- API health endpoint remains available at `/api/health`.

---

## API Endpoints (High-level)

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/dashboard`
- `GET /api/policies`
- `GET /api/policies/{policy_id}`
- `GET /api/gazettes`
- `POST /api/analysis/run`
- `POST /api/assistant/chat`

---

## How to Update the Project Safely

Use this workflow whenever dependencies or code change.

### Backend update steps

```powershell
cd kira-backend
git pull
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Then verify:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
curl http://127.0.0.1:8010/api/health
```

If using Docker after updates:

```powershell
docker build -t kira-backend:prod .
docker run --env-file .env -p 8000:8000 kira-backend:prod
```

### Frontend update steps

```powershell
cd kira-v2
git pull
npm install
npm run build
npm run dev
```

### Environment update checklist

When new config is introduced, update:

- `kira-backend/.env` for backend variables
- `kira-v2/.env` for frontend runtime variables
- deployment/runtime secrets in your host environment

---

## Useful Commands

Backend production command:

```powershell
cd kira-backend
gunicorn backend.main:app -c gunicorn_conf.py -k uvicorn.workers.UvicornWorker
```

Frontend production build:

```powershell
cd kira-v2
npm run build
```