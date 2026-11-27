from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview, InterviewStatus
from app.services.realtime_session import exchange_sdp

router = APIRouter()


def _get_owned_interview(interview_id: str, user: User, db: Session) -> Interview:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.post("/api/interviews/{interview_id}/realtime-session")
async def create_realtime_session(
    interview_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Receives the browser's raw SDP offer (Content-Type: application/sdp),
    exchanges it with OpenAI using this interview's context as the system
    instructions, and returns OpenAI's SDP answer. This is the only place the
    OpenAI API key is used — it never reaches the browser.
    """
    interview = _get_owned_interview(interview_id, user, db)

    if interview.status in (InterviewStatus.COMPLETED, InterviewStatus.QUIT, InterviewStatus.TIME_EXPIRED):
        raise HTTPException(status_code=400, detail="This interview has already ended.")

    offer_sdp = (await request.body()).decode("utf-8")
    if not offer_sdp:
        raise HTTPException(status_code=400, detail="Missing SDP offer body.")

    answer_sdp = await exchange_sdp(interview, offer_sdp)

    if interview.status == InterviewStatus.CREATED:
        interview.status = InterviewStatus.ACTIVE
        interview.started_at = datetime.utcnow()
        db.commit()

    return PlainTextResponse(content=answer_sdp, media_type="application/sdp")
