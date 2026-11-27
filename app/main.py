from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import Base, engine
from app import models  # noqa: F401 — ensures all models are registered before create_all
from app.routers import auth, pages, interviews, realtime, voice_local

app = FastAPI(title="AI Live Interviewer")

# Creates ai_live_interviewer.db and all tables on first run. Safe to call
# repeatedly — it only creates tables that don't exist yet.
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(interviews.router)
app.include_router(realtime.router)  # optional paid path (OpenAI) — unused by default
app.include_router(voice_local.router)  # default: free local voice pipeline


@app.middleware("http")
async def redirect_wildcard_host(request: Request, call_next):
    """Browsers block the microphone on http://0.0.0.0. If someone arrives that
    way (e.g. by clicking the link uvicorn prints), send them to localhost."""
    host = request.headers.get("host", "")
    if host.startswith("0.0.0.0"):
        target = request.url.replace(netloc=host.replace("0.0.0.0", "localhost", 1))
        return RedirectResponse(str(target), status_code=307)
    return await call_next(request)


@app.on_event("startup")
def warm_up_models():
    """Preload the LLM and speech-to-text model in the background so the first
    interview turn isn't slow. Failures are ignored (e.g. Ollama not running yet)."""
    import threading

    def work():
        try:
            from app.services.llm import warm_up
            warm_up()
        except Exception as e:
            print(f"[warm-up] LLM not preloaded: {e}")
        try:
            from app.services.stt import _get_model
            _get_model()
        except Exception as e:
            print(f"[warm-up] Speech-to-text not preloaded: {e}")

    threading.Thread(target=work, daemon=True).start()


@app.exception_handler(StarletteHTTPException)
async def auth_redirect_handler(request: Request, exc: StarletteHTTPException):
    """If a page route requires login and the user isn't authenticated,
    send them to /login instead of showing a raw 401 JSON error."""
    if exc.status_code == 401 and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/login", status_code=303)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
