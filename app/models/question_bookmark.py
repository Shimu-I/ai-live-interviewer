import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class QuestionBookmark(Base):
    __tablename__ = "question_bookmarks"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    practice_question_id = Column(String, ForeignKey("practice_questions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
