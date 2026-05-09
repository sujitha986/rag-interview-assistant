import json
import uuid

from app.core.config import settings
from app.db import connect, row_to_dict
from app.schemas import AnswerOut, InteractionOut, ResumeProfile, SessionOut, SummaryOut
from app.services.generation import build_query, evaluate_answer, generate_question
from app.services.resume import extract_profile, parse_resume
from app.services.retrieval import Retriever


class InterviewService:
    def __init__(self) -> None:
        self.retriever = Retriever()

    def create_session(self, role: str, filename: str, content: bytes) -> SessionOut:
        resume_text = parse_resume(filename, content)
        profile = extract_profile(resume_text)
        session_id = str(uuid.uuid4())
        query = build_query(role, profile)
        contexts = self.retriever.search(role, query)
        question = generate_question(role, profile, contexts, 1)
        with connect() as conn:
            conn.execute(
                "insert into sessions(id, role, resume_text, profile_json, status) values (?, ?, ?, ?, ?)",
                (session_id, role, resume_text, json.dumps(profile), "active"),
            )
            conn.execute(
                "insert into interactions(session_id, question, context_json) values (?, ?, ?)",
                (session_id, question, json.dumps(contexts)),
            )
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> SessionOut | None:
        with connect() as conn:
            session = conn.execute("select * from sessions where id = ?", (session_id,)).fetchone()
            if not session:
                return None
            interactions = conn.execute(
                "select * from interactions where session_id = ? order by id", (session_id,)
            ).fetchall()
        session_data = row_to_dict(session)
        return SessionOut(
            id=session_data["id"],
            role=session_data["role"],
            profile=ResumeProfile(**session_data["profile"]),
            status=session_data["status"],
            interactions=[InteractionOut(**row_to_dict(row)) for row in interactions],
        )

    def submit_answer(self, session_id: str, answer: str) -> AnswerOut | None:
        session = self.get_session(session_id)
        if not session:
            return None
        unanswered = next((item for item in session.interactions if item.answer is None), None)
        if not unanswered:
            return AnswerOut(session=session, next_question=None, completed=session.status == "completed")
        contexts = [context.model_dump() for context in unanswered.context]
        feedback = evaluate_answer(answer, contexts)
        with connect() as conn:
            conn.execute(
                """
                update interactions
                set answer = ?, feedback_json = ?, answered_at = current_timestamp
                where id = ?
                """,
                (answer, json.dumps(feedback), unanswered.id),
            )
        answered_count = len([item for item in session.interactions if item.answer is not None]) + 1
        if answered_count >= settings.max_interview_questions:
            with connect() as conn:
                conn.execute(
                    "update sessions set status = 'completed', updated_at = current_timestamp where id = ?",
                    (session_id,),
                )
            updated = self.get_session(session_id)
            return AnswerOut(session=updated, next_question=None, completed=True)
        query = build_query(session.role, session.profile.model_dump(), answer)
        new_contexts = self.retriever.search(session.role, query)
        next_question = generate_question(session.role, session.profile.model_dump(), new_contexts, answered_count + 1)
        with connect() as conn:
            conn.execute(
                "insert into interactions(session_id, question, context_json) values (?, ?, ?)",
                (session_id, next_question, json.dumps(new_contexts)),
            )
        updated = self.get_session(session_id)
        return AnswerOut(session=updated, next_question=next_question, completed=False)

    def summary(self, session_id: str) -> SummaryOut | None:
        session = self.get_session(session_id)
        if not session:
            return None
        answered = [item for item in session.interactions if item.answer]
        grounded = []
        thin = 0
        sources = set()
        for item in answered:
            for context in item.context:
                sources.add(context.source)
            if item.feedback and item.feedback.get("grounded_terms"):
                grounded.extend(item.feedback["grounded_terms"])
            if item.feedback and item.feedback.get("depth") == "thin":
                thin += 1
        strengths = []
        if grounded:
            strengths.append("Connected answers to retrieved knowledge-base concepts.")
        if len(answered) >= 3:
            strengths.append("Completed a multi-turn technical interview flow.")
        gaps = []
        if thin:
            gaps.append("Some answers were brief; add concrete examples, metrics, and implementation details.")
        if not grounded:
            gaps.append("Tie responses more explicitly to the retrieved role knowledge.")
        return SummaryOut(
            session_id=session.id,
            role=session.role,
            profile=session.profile,
            total_questions=len(answered),
            strengths=strengths or ["Provided enough signal for initial screening."],
            gaps=gaps or ["No major gaps detected in this lightweight evaluation."],
            source_coverage=sorted(sources),
            interactions=session.interactions,
        )

