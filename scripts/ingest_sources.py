import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db
from app.services.ingestion import ingest_all_sources

init_db()
print(f"inserted {ingest_all_sources()} source chunks")

