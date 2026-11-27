from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_optional, get_current_user
from app.models.user import User
from app.models.interview import Interview

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

JOB_ROLES = [
    "Software Engineer", "Frontend Developer", "Backend Developer",
    "Data Scientist", "Machine Learning Engineer", "UI/UX Designer",
    "Marketing Manager", "Customer Support", "Product Manager", "Custom Role",
]
EXPERIENCE_LEVELS = ["Intern", "Junior", "Mid-Level", "Senior", "Custom"]
INTERVIEW_TYPES = ["TECHNICAL", "HR", "BEHAVIORAL", "MIXED", "CUSTOM"]
DIFFICULTIES = ["EASY", "MEDIUM", "HARD", "ADAPTIVE"]
DURATIONS = [1, 5, 10, 20, 30, 45, 60]


@router.get("/")
def landing(request: Request, user: User | None = Depends(get_current_user_optional)):
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})


@router.get("/setup")
def setup_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "setup.html",
        {
            "request": request,
            "user": user,
            "job_roles": JOB_ROLES,
            "experience_levels": EXPERIENCE_LEVELS,
            "interview_types": INTERVIEW_TYPES,
            "difficulties": DIFFICULTIES,
            "durations": DURATIONS,
        },
    )


@router.get("/interviews/{interview_id}/live")
def interview_live(
    interview_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status.value in ("COMPLETED", "QUIT", "TIME_EXPIRED"):
        return templates.TemplateResponse(
            "interview_ready.html", {"request": request, "user": user, "interview": interview}
        )
    return templates.TemplateResponse(
        "interview_live.html", {"request": request, "user": user, "interview": interview}
    )
