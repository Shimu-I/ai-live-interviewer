"""
Handshakes a WebRTC session with OpenAI's Realtime API on behalf of the
browser, using the "unified interface" (POST /v1/realtime/calls) so the
standard OpenAI API key is only ever used server-side — the browser never
sees any OpenAI credential at all.

Reference: https://developers.openai.com/api/docs/guides/realtime-webrtc
"""
import json

import httpx
from fastapi import HTTPException

from app.config import settings
from app.models.interview import Interview
from app.services.prompt_builder import build_instructions

OPENAI_REALTIME_CALLS_URL = "https://api.openai.com/v1/realtime/calls"

# Voice options: alloy, ash, ballad, coral, echo, marin, sage, shimmer, verse.
# "marin" is a natural, professional-sounding default for an interviewer.
DEFAULT_VOICE = "marin"


def build_session_config(interview: Interview) -> dict:
    return {
        "type": "realtime",
        "model": settings.openai_realtime_model,
        "instructions": build_instructions(interview),
        "audio": {
            "input": {
                "transcription": {"model": "whisper-1"},
                "turn_detection": {"type": "semantic_vad", "eagerness": "medium"},
            },
            "output": {"voice": DEFAULT_VOICE},
        },
    }


async def exchange_sdp(interview: Interview, offer_sdp: str) -> str:
    """
    Sends the browser's SDP offer + our session config to OpenAI, returns the
    SDP answer (raw text) to relay back to the browser.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not set on the server. Add it to your .env "
            "file to enable live voice interviews.",
        )

    session_config = build_session_config(interview)

    files = {
        "sdp": (None, offer_sdp, "application/sdp"),
        "session": (None, json.dumps(session_config), "application/json"),
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENAI_REALTIME_CALLS_URL, headers=headers, files=files)

    if response.status_code >= 400:
        # Surface OpenAI's error text so it's actionable instead of a bare 500.
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI Realtime API error ({response.status_code}): {response.text}",
        )

    return response.text
