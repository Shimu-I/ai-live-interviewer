import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class PracticeStatus(str, enum.Enum):
    NEW = "NEW"
    PRACTICING = "PRACTICING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class PracticeCategory(str, enum.Enum):
    UNANSWERED = "UNANSWERED"
    WEAK_ANSWER = "WEAK_ANSWER"
    TECHNICAL = "TECHNICAL"
    BEHAVIORAL = "BEHAVIORAL"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"
    BOOKMARKED = "BOOKMARKED"


class PracticeQuestion(Base):
    __tablename__ = "practice_questions"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=True)
    message_id = Column(String, ForeignKey("interview_messages.id"), nullable=True)

    question = Column(Text, nullable=False)
    previous_answer = Column(Text, nullable=True)
    category = Column(Enum(PracticeCategory), default=PracticeCategory.WEAK_ANSWER)
    status = Column(Enum(PracticeStatus), default=PracticeStatus.NEW)

    created_at = Column(DateTime, default=datetime.utcnow)
