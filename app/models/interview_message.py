import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class Speaker(str, enum.Enum):
    AI = "AI"
    USER = "USER"


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(String, primary_key=True, default=gen_id)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False, index=True)

    speaker = Column(Enum(Speaker), nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)

    # Set when this message (an AI question) is judged weak/unanswered/vague
    # so the Practice Center can surface it later.
    needs_practice = Column(Integer, default=0)  # 0/1 boolean flag (SQLite-friendly)

    timestamp = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="messages")
