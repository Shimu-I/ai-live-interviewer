"""
Central app configuration. Reads from environment variables / .env file.
Keep every tunable (limits, secrets, model names) here — nothing hardcoded
elsewhere in the app.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Live Interviewer"
    environment: str = "development"

    # Database — SQLite by default (zero setup). Swap to a Postgres URL later
    # without changing any application code.
    database_url: str = "sqlite:///./ai_live_interviewer.db"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Local AI stack — no API keys, no cost. Requires Ollama running locally
    # (https://ollama.com) with a model pulled, e.g. `ollama pull llama3.2`.
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Speech-to-text: faster-whisper, runs locally on CPU. Downloads the model
    # automatically on first use (cached under ~/.cache/huggingface).
    whisper_model: str = "base.en"

    # Text-to-speech: Piper, runs locally on CPU. Voice is downloaded once by
    # scripts/setup-local-ai.sh (python -m piper.download_voices <voice>).
    piper_voice: str = "en_US-lessac-medium"

    # Cost / usage limits
    max_interview_duration_seconds: int = 1800
    max_daily_interviews_per_user: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"  # unrecognized .env vars (leftovers from old edits) are ignored, not fatal


settings = Settings()
