from pydantic import BaseModel, EmailStr


class SignupForm(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginForm(BaseModel):
    email: EmailStr
    password: str


class InterviewCreate(BaseModel):
    job_role: str
    experience_level: str | None = None
    interview_type: str = "MIXED"
    difficulty: str = "ADAPTIVE"
    duration_minutes: int = 10
    job_description: str | None = None
    resume_text: str | None = None
