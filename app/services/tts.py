"""
Synthesizes the AI interviewer's voice with Piper — fast, open-source, local
neural TTS. CPU-only, no API key, no cost.
Voice is downloaded once by scripts/setup-local-ai.sh.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.config import settings


def synthesize_speech(text: str) -> bytes:
    """Returns WAV audio bytes for the given text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "speech.wav"
        try:
            result = subprocess.run(
                [sys.executable, "-m", "piper", "-m", settings.piper_voice,
                 "-f", str(out_path), "--", text],
                capture_output=True, text=True, timeout=90,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Text-to-speech timed out.")

        if result.returncode != 0 or not out_path.exists():
            raise HTTPException(
                status_code=503,
                detail=("Piper TTS failed — usually the voice isn't downloaded yet. Run "
                        f"./scripts/setup-local-ai.sh\n\nDetails: {result.stderr.strip()[-500:]}"),
            )
        return out_path.read_bytes()
