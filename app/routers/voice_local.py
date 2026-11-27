import base64
import logging
import time
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview, InterviewStatus
from app.models.interview_message import InterviewMessage, Speaker
from app.services.llm import generate_ai_message
from app.services.tts import synthesize_speech
from app.services.stt import transcribe_audio

router = APIRouter()
log = logging.getLogger("uvicorn.error")

ENDED = (InterviewStatus.COMPLETED, InterviewStatus.QUIT, InterviewStatus.TIME_EXPIRED)


def _get_owned_interview(interview_id: str, user: User, db: Session) -> Interview:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status in ENDED:
        raise HTTPException(status_code=400, detail="This interview has already ended.")
    return interview


def _next_seq(interview_id: str, db: Session) -> int:
    return (
        db.query(func.coalesce(func.max(InterviewMessage.sequence_number), 0))
        .filter(InterviewMessage.interview_id == interview_id)
        .scalar() + 1
    )


@router.post("/api/interviews/{interview_id}/ai-turn")
async def ai_turn(
    interview_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI's next message (local Ollama) + its spoken audio (local Piper).
    Returns audio/wav as the body, transcript text base64-encoded in a header."""
    interview = _get_owned_interview(interview_id, user, db)
    history = (
        db.query(InterviewMessage)
        .filter(InterviewMessage.interview_id == interview.id)
        .order_by(InterviewMessage.sequence_number)
        .all()
    )

    t0 = time.perf_counter()
    text = await generate_ai_message(interview, history)
    t1 = time.perf_counter()
    audio_bytes = await run_in_threadpool(synthesize_speech, text)
    t2 = time.perf_counter()
    log.info(f"[ai-turn] LLM {t1 - t0:.1f}s | TTS {t2 - t1:.1f}s | {len(text.split())} words")

    db.add(InterviewMessage(
        interview_id=interview.id, speaker=Speaker.AI, content=text,
        sequence_number=_next_seq(interview.id, db),
    ))
    if interview.status == InterviewStatus.CREATED:
        interview.status = InterviewStatus.ACTIVE
        interview.started_at = datetime.utcnow()
    db.commit()

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"X-AI-Text-Base64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
                 "Access-Control-Expose-Headers": "X-AI-Text-Base64"},
    )


@router.post("/api/interviews/{interview_id}/user-turn")
async def user_turn(
    interview_id: str,
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Transcribes the candidate's recorded answer locally and saves it."""
    interview = _get_owned_interview(interview_id, user, db)

    suffix = Path(audio.filename or "answer.webm").suffix or ".webm"
    data = await audio.read()
    if len(data) < 1500:
        raise HTTPException(
            status_code=400,
            detail="The recording was empty or too short. Click Start answering, speak for a few seconds, then click Stop.",
        )
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        t0 = time.perf_counter()
        text = await run_in_threadpool(transcribe_audio, tmp_path)
        log.info(f"[user-turn] speech-to-text {time.perf_counter() - t0:.1f}s")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not text:
        text = "(no speech detected)"

    db.add(InterviewMessage(
        interview_id=interview.id, speaker=Speaker.USER, content=text,
        sequence_number=_next_seq(interview.id, db),
    ))
    db.commit()
    return {"text": text}
