# syntax=docker/dockerfile:1.7

FROM node:20-bullseye-slim AS frontend-builder
WORKDIR /app/code/frontend
COPY code/frontend/package*.json ./
RUN npm ci
COPY code/frontend/ ./
# 避免某些环境下 node_modules/.bin/vite 无执行权限导致 Permission denied
RUN chmod +x node_modules/.bin/vite && node ./node_modules/vite/bin/vite.js build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/code/backend

# System deps for pandas/openpyxl runtime compatibility
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY code/backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY code/backend/ ./
COPY --from=frontend-builder /app/code/frontend/dist /app/code/frontend/dist

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
