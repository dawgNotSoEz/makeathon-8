# Regulatory Intelligence & Impact Forecasting System

A scalable, production-grade terminal-based system for tracking regulatory policies and analyzing their business impact.

##  System Overview

This AI-powered system:
- Stores regulatory policies in version-controlled folders
- Detects policy changes between versions
- Extracts only changed sections for processing
- Embeds new/changed sections in vector database
- Provides RAG-based regulatory context retrieval
- Generates structured business impact analysis

##  Architecture

```

## Production Runtime

- API entrypoint: `backend/main.py`
- Process model: Gunicorn + Uvicorn workers
- Shared dependencies: Redis (cache/rate limits), Chroma (vector retrieval)
- Health endpoints: `/api/health`, `/api/readiness`
- Metrics endpoint (optional): `/api/metrics` when `ENABLE_METRICS_ENDPOINT=true`

See deployment and scaling details in `DEPLOYMENT.md`.
project/
├── backend/
│   ├── main.py                # FastAPI app entrypoint
│   ├── routes/                # API routes
│   ├── services/              # Service layer
│   ├── core/                  # Core regulatory processing modules
│   └── data/
│       ├── policies/          # Version-controlled policy storage
│       ├── vector_store/      # ChromaDB persistent storage
│       └── org_data.json      # Organization profile
├── archive/
│   ├── generated/             # Generated/non-runtime outputs
│   └── cache/                 # Cached/temporary artifacts
├── requirements.txt           # Dependencies
└── .env                       # Environment variables
```
