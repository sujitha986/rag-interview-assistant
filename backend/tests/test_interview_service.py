import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db
from app.services.ingestion import ingest_seed_knowledge
from app.services.interview import InterviewService


class InterviewServiceTest(unittest.TestCase):
    def test_session_lifecycle(self) -> None:
        init_db()
        ingest_seed_knowledge()
        service = InterviewService()
        resume = (
            "AI ML engineer with Python, FastAPI, SQL, RAG, pandas, scikit-learn, "
            "model evaluation, analytics, and production API experience."
        ).encode("utf-8")

        session = service.create_session("ai_ml", "resume.txt", resume)
        self.assertEqual(session.status, "active")
        self.assertEqual(len(session.interactions), 1)
        self.assertTrue(session.interactions[0].context)

        result = service.submit_answer(
            session.id,
            "I would compare a baseline against validation metrics, check train-test drift, "
            "inspect errors by slice, and store the evidence, feature changes, and outcomes.",
        )
        self.assertFalse(result.completed)
        self.assertEqual(len(result.session.interactions), 2)


if __name__ == "__main__":
    unittest.main()

