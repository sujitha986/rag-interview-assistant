import json
from pathlib import Path

from pypdf import PdfReader

from app.core.config import settings
from app.db import connect
from app.services.chunking import chunk_text
from app.services.embeddings import HashingEmbeddingService

ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = ROOT / "data" / "seed" / "role_knowledge.md"
SOURCE_DIR = ROOT / "data" / "sources"


def _insert_document(role: str, source: str, title: str, text: str) -> int:
    embedder = HashingEmbeddingService()
    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    with connect() as conn:
        conn.execute(
            "delete from knowledge_chunks where role = ? and source = ? and title = ?",
            (role, source, title),
        )
        inserted = 0
        for chunk in chunks:
            embedding = embedder.embed(f"{title}\n{chunk}")
            conn.execute(
                """
                insert into knowledge_chunks(role, source, title, text, embedding)
                values (?, ?, ?, ?, ?)
                """,
                (role, source, title, chunk, json.dumps(embedding)),
            )
            inserted += 1
    return inserted


def ingest_seed_knowledge() -> int:
    text = SEED_FILE.read_text(encoding="utf-8").lstrip()
    if text.startswith("## "):
        text = text[3:]
    sections = [section.strip() for section in text.split("\n## ") if section.strip()]
    inserted = 0
    with connect() as conn:
        conn.execute("delete from knowledge_chunks where source = 'seed-role-knowledge'")
    for section in sections:
        header, body = section.split("\n", 1)
        if "|" in header:
            role, title = [part.strip() for part in header.split("|", 1)]
        else:
            role, title = "all", header.strip("# ")
        inserted += _insert_document(role, "seed-role-knowledge", title, body)
    return inserted


def ingest_pdf(path: Path, role: str, title: str | None = None) -> int:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return _insert_document(role, path.name, title or path.stem, text)


def ingest_all_sources() -> int:
    mapping = {
        "mitchell_machine_learning.pdf": ("ai_ml", "Machine Learning - Tom Mitchell"),
        "hundred_page_ml.pdf": ("ai_ml", "The Hundred-Page Machine Learning Book"),
        "ml_absolute_beginners.pdf": ("ai_ml", "Machine Learning for Absolute Beginners"),
        "intro_ml_python.pdf": ("data_science", "Introduction to Machine Learning with Python"),
        "master_ml_algorithms.pdf": ("data_science", "Master Machine Learning Algorithms"),
        "bishop_prml.pdf": ("advanced_ml", "Pattern Recognition and Machine Learning"),
        "ai_ml_deep_learning.pdf": ("advanced_ml", "Artificial Intelligence, Machine Learning, and Deep Learning"),
    }
    inserted = 0
    for filename, (role, title) in mapping.items():
        path = SOURCE_DIR / filename
        if path.exists():
            inserted += ingest_pdf(path, role, title)
    return inserted
