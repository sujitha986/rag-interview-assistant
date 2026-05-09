# Role-Based AI Candidate Screening System

An end-to-end AI/ML and backend intern assessment project. The system parses a candidate resume, selects a target role, retrieves role-specific knowledge from Section 9 resources, generates grounded interview questions, stores the full session, and returns a structured summary.

## Features

- Resume upload for PDF or text files
- Role selection for AI/ML, data science/applied ML, backend, and advanced ML
- RAG-style ingestion with chunking, local embeddings, vector search, and source traceability
- Interview session lifecycle with stored questions, answers, retrieved context, and analysis
- React frontend for upload, interview, and summary views
- SQLite persistence for sessions, chunks, and responses
- Optional LLM integration through environment variables, with a deterministic local fallback

## Architecture

```text
frontend React app
        |
        v
FastAPI backend
  - resume parser
  - profile extractor
  - query builder
  - retriever
  - question generator
  - evaluator
        |
        v
SQLite database
  - knowledge chunks + vectors
  - interview sessions
  - Q&A records
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python ..\scripts\ingest_seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

On Windows PowerShell, if `npm` is blocked by script policy, use:

```bash
"C:\Program Files\nodejs\npm.cmd" install --cache ..\.npm-cache
"C:\Program Files\nodejs\npm.cmd" run dev
```

Open the frontend URL shown by Vite, usually `http://localhost:5173`.

## Section 9 Knowledge Base

The assignment requires the RAG source to use the provided books. The source URLs recovered from the assignment PDF are stored in [scripts/download_section9_sources.py](scripts/download_section9_sources.py).

To download and ingest them:

```bash
python scripts/download_section9_sources.py
python scripts/ingest_sources.py
```

During local verification, 6 of the 7 linked PDFs downloaded and ingested successfully. The `Machine Learning for Absolute Beginners` host returned `406 Not Acceptable`; the downloader reports this and continues with the remaining sources.

The app also includes small seed excerpts in [data/seed/role_knowledge.md](data/seed/role_knowledge.md) so the demo works before downloading large PDFs.

## Verification

Commands run locally:

```bash
python -m compileall backend\app scripts
python scripts\ingest_seed.py
python scripts\ingest_sources.py
cd frontend && npm run build
python -m unittest backend.tests.test_interview_service
```

The populated local database contained 6,934 chunks after ingesting the available Section 9 PDFs and seed excerpts.

## Key Design Decisions

- **SQLite as persistence and vector store:** The assignment asks for a database. This project stores both interview records and chunk vectors in SQLite for a simple, inspectable submission.
- **Local embeddings by default:** The embedding service uses deterministic hashed vectors, avoiding external services during review. The interface is isolated so it can be replaced with sentence-transformers, OpenAI embeddings, or Chroma.
- **Grounded question traceability:** Each generated question stores retrieved chunk IDs, source names, and context snippets.
- **Optional LLM path:** If `OPENAI_API_KEY` is configured and an OpenAI client is installed, the generator can be extended without changing the API contract. The current fallback remains fully runnable offline.

## API Overview

- `GET /health`
- `GET /roles`
- `POST /ingest/seed`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/answers`
- `GET /sessions/{session_id}/summary`

## Demo Video Checklist

1. Start backend and frontend.
2. Run seed ingestion or Section 9 ingestion.
3. Upload a resume.
4. Select a role.
5. Answer several questions.
6. Show the summary and the cited knowledge sources.
