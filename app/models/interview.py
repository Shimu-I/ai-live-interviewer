import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class InterviewStatus(str, enum.Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    QUIT = "QUIT"
    TIME_EXPIRED = "TIME_EXPIRED"
    FAILED = "FAILED"


class InterviewType(str, enum.Enum):
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    BEHAVIORAL = "BEHAVIORAL"
    MIXED = "MIXED"
    CUSTOM = "CUSTOM"


class Difficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    ADAPTIVE = "ADAPTIVE"


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    job_role = Column(String, nullable=False)
    experience_level = Column(String, nullable=True)
    interview_type = Column(Enum(InterviewType), default=InterviewType.MIXED)
    difficulty = Column(Enum(Difficulty), default=Difficulty.ADAPTIVE)

    duration = Column(Integer, nullable=False)  # planned duration, seconds
    actual_duration = Column(Integer, nullable=True)  # seconds actually used
    status = Column(Enum(InterviewStatus), default=InterviewStatus.CREATED)

    # Optional inputs the orchestrator uses for context
    job_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)

    # Structured memory + evaluation, stored as JSON (see docs/spec-interview-architecture.md §6, §9)
    candidate_profile = Column(JSON, default=dict)
    conversation_summary = Column(Text, nullable=True)
    topics_completed = Column(JSON, default=list)
    topics_remaining = Column(JSON, default=list)

    overall_score = Column(Integer, nullable=True)
    category_scores = Column(JSON, default=dict)  # {"communication": 80, ...}
    strengths = Column(JSON, default=list)
    improvement_areas = Column(JSON, default=list)

    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interviews")
    messages = relationship(
        "InterviewMessage", back_populates="interview",
        cascade="all, delete-orphan", order_by="InterviewMessage.sequence_number",
    )
