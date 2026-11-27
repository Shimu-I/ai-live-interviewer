from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import hash_password, verify_password, create_access_token
from app.deps import COOKIE_NAME

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 1 week, matches token expiry


@router.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@router.post("/signup")
def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "An account with that email already exists."},
            status_code=400,
        )

    user = User(email=email, hashed_password=hash_password(password), full_name=full_name or None)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    response = RedirectResponse(url="/setup", status_code=303)
    response.set_cookie(COOKIE_NAME, token, max_age=COOKIE_MAX_AGE, httponly=True)
    return response


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect email or password."},
            status_code=400,
        )

    token = create_access_token(user.id)
    response = RedirectResponse(url="/setup", status_code=303)
    response.set_cookie(COOKIE_NAME, token, max_age=COOKIE_MAX_AGE, httponly=True)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
