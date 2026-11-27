"""
Reads the session cookie, validates the JWT, and loads the current user.
Used as a FastAPI dependency in every router that needs auth.
"""
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

COOKIE_NAME = "session_token"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Same as get_current_user but returns None instead of raising — used on
    public pages (landing page) that render differently when logged in."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()
