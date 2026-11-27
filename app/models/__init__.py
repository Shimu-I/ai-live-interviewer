"""
All SQLAlchemy models, gathered here so `Base.metadata.create_all` (called in
app/main.py) sees every table. Keep one model per concept, matching
docs/spec-dashboard.md and docs/spec-interview-architecture.md exactly so the
database never drifts from the design docs.
"""
from app.models.user import User
from app.models.interview import Interview
from app.models.interview_message import InterviewMessage
from app.models.practice_question import PracticeQuestion
from app.models.question_bookmark import QuestionBookmark
from app.models.analytics_snapshot import AnalyticsSnapshot

__all__ = [
    "User",
    "Interview",
    "InterviewMessage",
    "PracticeQuestion",
    "QuestionBookmark",
    "AnalyticsSnapshot",
]
