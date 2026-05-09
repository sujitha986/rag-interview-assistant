import re
from io import BytesIO

from pypdf import PdfReader

SKILL_KEYWORDS = {
    "python", "java", "typescript", "javascript", "fastapi", "flask", "react", "next.js",
    "sql", "postgresql", "sqlite", "mongodb", "docker", "kubernetes", "aws", "gcp",
    "machine learning", "deep learning", "nlp", "rag", "llm", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "api", "microservices", "redis", "celery",
}

DOMAIN_KEYWORDS = {
    "finance", "healthcare", "education", "ecommerce", "recommendation", "computer vision",
    "natural language", "analytics", "fraud", "search", "automation",
}


def parse_resume(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return content.decode("utf-8", errors="ignore").strip()


def extract_profile(text: str) -> dict:
    lowered = text.lower()
    skills = sorted(keyword for keyword in SKILL_KEYWORDS if keyword in lowered)
    domains = sorted(keyword for keyword in DOMAIN_KEYWORDS if keyword in lowered)
    technologies = [item for item in skills if item not in {"machine learning", "deep learning", "nlp", "rag", "llm"}]
    years = [int(value) for value in re.findall(r"(\d+)\+?\s+years?", lowered)]
    seniority = "project-ready"
    if years and max(years) >= 3:
        seniority = "experienced"
    elif len(skills) < 4:
        seniority = "early"
    return {
        "skills": skills[:12],
        "technologies": technologies[:10],
        "domains": domains[:8],
        "seniority_signal": seniority,
    }

