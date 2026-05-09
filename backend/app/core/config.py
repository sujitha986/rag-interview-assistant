import os


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


class Settings:
    app_name = os.getenv("APP_NAME", "Role Screening RAG")
    database_path = os.getenv("DATABASE_PATH", "data/app.db")
    max_interview_questions = _int_env("MAX_INTERVIEW_QUESTIONS", 5)
    chunk_size = _int_env("CHUNK_SIZE", 900)
    chunk_overlap = _int_env("CHUNK_OVERLAP", 160)
    embedding_dimensions = _int_env("EMBEDDING_DIMENSIONS", 384)
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,https://sujichowdary24-rag-interview-assistant.hf.space").split(",")
        if origin.strip()
    ]
    openai_api_key = os.getenv("OPENAI_API_KEY") or None


settings = Settings()
