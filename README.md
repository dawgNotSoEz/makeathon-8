# KIRA Fullstack Workspace

KIRA includes a React frontend (`kira-v2`) and a FastAPI backend (`kira-backend`) for regulatory intelligence workflows.

## Project Structure

- [kira-v2](https://github.com/dawgNotSoEz/makeathon-8/tree/main/kira-v2)
- [kira-backend](https://github.com/dawgNotSoEz/makeathon-8/tree/main/kira-backend)

## Frontend (kira-v2)

- React + TypeScript + Vite + Tailwind
- Dashboard, policies list/detail, analysis workspace, assistant chat, profile

## Backend (kira-backend)

- FastAPI with strict schemas and JWT auth
- Routes: `/health`, `/api/dashboard`, `/api/policies`, `/api/analysis/run`, `/api/assistant/chat`
- Local policy fallback data available under `backend/data/policies`

## Quick Start (Local)

1. Frontend
   - `cd kira-v2`
   - `npm install`
   - `npm run dev`
2. Backend (new terminal)
   - `cd kira-backend`
   - `python -m venv .venv`
   - `.\.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `uvicorn backend.main:app --host 127.0.0.1 --port 8010`
3. Configure frontend env
   - Copy `kira-v2/.env.example` to `kira-v2/.env`
   - Set `VITE_API_BASE_URL=http://127.0.0.1:8010`

## Frontend Routes

- `/dashboard`
- `/documents`
- `/documents/analysis/:documentId`
- `/profile`