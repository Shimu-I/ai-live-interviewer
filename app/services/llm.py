"""
Generates the AI interviewer's next message using a local Ollama model — no
API key, no per-token cost, runs entirely on your machine.
Requires Ollama running locally with a model pulled:  ollama pull llama3.2
"""
import httpx
from fastapi import HTTPException

from app.config import settings
from app.models.interview import Interview
from app.models.interview_message import InterviewMessage
from app.services.prompt_builder import build_instructions


def _history_to_messages(history: list[InterviewMessage]) -> list[dict]:
    role_map = {"AI": "assistant", "USER": "user"}
    return [{"role": role_map[m.speaker.value], "content": m.content} for m in history]


async def generate_ai_message(interview: Interview, history: list[InterviewMessage]) -> str:
    """history = the interview's messages so far, oldest first. Returns the AI's
    next message as plain text (spoken via TTS by the caller)."""
    messages = [{"role": "system", "content": build_instructions(interview)}]
    messages.extend(_history_to_messages(history))

    if not history:
        messages.append({
            "role": "user",
            "content": "(The interview is starting now. Greet the candidate briefly and ask your first question.)",
        })

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "keep_alive": "30m",  # keep the model loaded in RAM between turns
        "options": {"temperature": 0.7, "num_predict": 160},  # cap reply length = faster
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{settings.ollama_host}/api/chat", json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Couldn't reach Ollama at {settings.ollama_host}. Make sure Ollama is "
                f"running (`ollama serve`) and the model is pulled: `ollama pull {settings.ollama_model}`."
            ),
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Ollama error ({response.status_code}): {response.text}")

    content = response.json().get("message", {}).get("content", "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="Ollama returned an empty response.")
    return content


def warm_up() -> None:
    """Loads the model into memory ahead of time so the first interview turn
    doesn't pay the cold-start cost. Safe to fail (Ollama may not be running yet)."""
    httpx.post(
        f"{settings.ollama_host}/api/generate",
        json={"model": settings.ollama_model, "keep_alive": "30m"},
        timeout=180.0,
    )
