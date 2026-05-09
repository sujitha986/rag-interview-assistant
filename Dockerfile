FROM node:20-bookworm AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/backend
ENV DATABASE_PATH=/app/data/app.db
ENV MAX_INTERVIEW_QUESTIONS=5
ENV PORT=7860

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY scripts /app/scripts
COPY data /app/data
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

RUN python scripts/ingest_seed.py

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

