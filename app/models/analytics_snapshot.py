import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class AnalyticsSnapshot(Base):
    """
    A periodic rollup (e.g. one row per user per month) so the Analytics
    dashboard can chart progress over time without recomputing from every
    interview on every page load.
    """
    __tablename__ = "analytics_snapshots"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    period = Column(String, nullable=False)  # e.g. "2026-09"
    total_interviews = Column(Integer, default=0)
    completed_interviews = Column(Integer, default=0)
    quit_interviews = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
