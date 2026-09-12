FROM node:22-slim AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


FROM python:3.12-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --chown=app:app src/ ./src/
COPY --chown=app:app data/ ./data/
COPY --chown=app:app --from=frontend-builder \
    /build/frontend/dist/ ./frontend/dist/

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec python -m uvicorn api.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
