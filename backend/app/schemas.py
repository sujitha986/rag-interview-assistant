from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


class RoleOut(BaseModel):
    id: str
    name: str
    description: str


class ResumeProfile(BaseModel):
    skills: list[str]
    technologies: list[str]
    domains: list[str]
    seniority_signal: str


class ContextChunk(BaseModel):
    id: int
    role: str
    source: str
    title: str
    text: str
    score: float


class InteractionOut(BaseModel):
    id: int
    question: str
    answer: str | None = None
    context: list[ContextChunk]
    feedback: dict | None = None


class SessionOut(BaseModel):
    id: str
    role: str
    profile: ResumeProfile
    status: str
    interactions: list[InteractionOut]


class AnswerIn(BaseModel):
    answer: str


class AnswerOut(BaseModel):
    session: SessionOut
    next_question: str | None
    completed: bool


class SummaryOut(BaseModel):
    session_id: str
    role: str
    profile: ResumeProfile
    total_questions: int
    strengths: list[str]
    gaps: list[str]
    source_coverage: list[str]
    interactions: list[InteractionOut]

