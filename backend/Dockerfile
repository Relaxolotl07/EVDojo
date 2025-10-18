# Simple production Dockerfile for FastAPI backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/ /app/backend/
COPY README.md /app/README.md

RUN pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8080

ENV PORT=8080

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]

