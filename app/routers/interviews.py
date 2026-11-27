from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview, InterviewStatus, InterviewType, Difficulty
from app.models.interview_message import InterviewMessage, Speaker

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/interviews")
def create_interview(
    request: Request,
    job_role: str = Form(...),
    experience_level: str = Form(""),
    interview_type: str = Form("MIXED"),
    difficulty: str = Form("ADAPTIVE"),
    duration_minutes: int = Form(10),
    custom_duration_minutes: str = Form(""),
    job_description: str = Form(""),
    resume_text: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # A typed-in custom length overrides the preset pills (clamped to 1-120 min).
    if custom_duration_minutes.strip().isdigit():
        duration_minutes = int(custom_duration_minutes)
    duration_minutes = max(1, min(duration_minutes, 120))

    interview = Interview(
        user_id=user.id,
        job_role=job_role,
        experience_level=experience_level or None,
        interview_type=InterviewType(interview_type),
        difficulty=Difficulty(difficulty),
        duration=duration_minutes * 60,
        status=InterviewStatus.CREATED,
        job_description=job_description or None,
        resume_text=resume_text or None,
        candidate_profile={},
        topics_completed=[],
        topics_remaining=[],
        category_scores={},
        strengths=[],
        improvement_areas=[],
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return RedirectResponse(url=f"/interviews/{interview.id}/ready", status_code=303)


def _get_owned_interview(interview_id: str, user: User, db: Session) -> Interview:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.get("/interviews/{interview_id}/ready")
def interview_ready(
    interview_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _get_owned_interview(interview_id, user, db)
    return templates.TemplateResponse(
        "interview_ready.html", {"request": request, "user": user, "interview": interview}
    )


class MessageIn(BaseModel):
    speaker: str  # "AI" or "USER"
    content: str


@router.post("/api/interviews/{interview_id}/messages")
def add_message(
    interview_id: str,
    body: MessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Called by voice.js each time a transcript segment (question or answer)
    is finalized, so the full conversation is saved as it happens — not lost
    if the tab closes mid-interview."""
    interview = _get_owned_interview(interview_id, user, db)

    next_seq = (
        db.query(func.coalesce(func.max(InterviewMessage.sequence_number), 0))
        .filter(InterviewMessage.interview_id == interview.id)
        .scalar()
        + 1
    )

    message = InterviewMessage(
        interview_id=interview.id,
        speaker=Speaker(body.speaker),
        content=body.content,
        sequence_number=next_seq,
    )
    db.add(message)
    db.commit()
    return JSONResponse({"ok": True, "sequence_number": next_seq})


class EndIn(BaseModel):
    status: str  # "COMPLETED", "QUIT", or "TIME_EXPIRED"
    actual_duration: int | None = None


@router.post("/api/interviews/{interview_id}/end")
def end_interview(
    interview_id: str,
    body: EndIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _get_owned_interview(interview_id, user, db)

    interview.status = InterviewStatus(body.status)
    interview.ended_at = datetime.utcnow()
    if body.actual_duration is not None:
        interview.actual_duration = body.actual_duration
    db.commit()
    return JSONResponse({"ok": True})
