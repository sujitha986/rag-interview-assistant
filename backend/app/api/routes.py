from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.schemas import AnswerIn, AnswerOut, HealthOut, RoleOut, SessionOut, SummaryOut
from app.services.ingestion import ingest_seed_knowledge
from app.services.interview import InterviewService
from app.services.report import build_summary_pdf
from app.services.roles import ROLES

router = APIRouter()
service = InterviewService()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok")


@router.get("/roles", response_model=list[RoleOut])
def roles() -> list[RoleOut]:
    return [RoleOut(id=key, **value) for key, value in ROLES.items()]


@router.post("/ingest/seed")
def ingest_seed() -> dict:
    inserted = ingest_seed_knowledge()
    return {"inserted_chunks": inserted}


@router.post("/sessions", response_model=SessionOut)
async def create_session(role: str = Form(...), resume: UploadFile = File(...)) -> SessionOut:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail="Unsupported role")
    content = await resume.read()
    return service.create_session(role=role, filename=resume.filename or "resume.txt", content=content)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str) -> SessionOut:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/answers", response_model=AnswerOut)
def submit_answer(session_id: str, payload: AnswerIn) -> AnswerOut:
    result = service.submit_answer(session_id, payload.answer)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/sessions/{session_id}/summary", response_model=SummaryOut)
def summary(session_id: str) -> SummaryOut:
    result = service.summary(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/sessions/{session_id}/report.pdf")
def report_pdf(session_id: str) -> Response:
    result = service.summary(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    pdf = build_summary_pdf(result)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="interview-report-{session_id}.pdf"'},
    )
