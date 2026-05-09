import json

from app.db import connect
from app.services.embeddings import HashingEmbeddingService, cosine


class Retriever:
    def __init__(self) -> None:
        self.embeddings = HashingEmbeddingService()

    def search(self, role: str, query: str, limit: int = 6) -> list[dict]:
        query_vector = self.embeddings.embed(query)
        with connect() as conn:
            rows = conn.execute(
                """
                select id, role, source, title, text, embedding
                from knowledge_chunks
                where source != 'seed-role-knowledge'
                """
            ).fetchall()
        scored = []
        for row in rows:
            vector = json.loads(row["embedding"])
            role_boost = 0.04 if row["role"] == role else 0.0
            scored.append(
                {
                    "id": row["id"],
                    "role": row["role"],
                    "source": row["source"],
                    "title": row["title"],
                    "text": row["text"],
                    "score": round(cosine(query_vector, vector) + role_boost, 4),
                }
            )
        ranked = sorted(scored, key=lambda item: item["score"], reverse=True)
        diversified = []
        used_sources = set()
        for item in ranked:
            if item["source"] in used_sources:
                continue
            diversified.append(item)
            used_sources.add(item["source"])
            if len(diversified) == limit:
                return diversified
        for item in ranked:
            if item["id"] not in {selected["id"] for selected in diversified}:
                diversified.append(item)
            if len(diversified) == limit:
                break
        return diversified
