# Production Deployment

## Runtime Command

gunicorn backend.main:app -c gunicorn_conf.py -k uvicorn.workers.UvicornWorker

## Horizontal Scaling Strategy

- Run multiple identical stateless API replicas.
- Use a load balancer with sticky sessions disabled.
- Keep state in Redis and external Chroma only.
- Scale Redis and Chroma independently.
- Use shared JWT issuer/audience and common secrets via secret manager.

## Required Dependencies

- Redis (cache + rate limits)
- Chroma server (external vector store)
- Gemini API access

## Readiness and Health

- Health: `/api/health`
- Readiness: `/api/readiness` (checks Redis and vector collection)

## Container Notes

- Build: `docker build -t kira-backend:prod .`
- Run with env file: `docker run --env-file .env -p 8000:8000 kira-backend:prod`
