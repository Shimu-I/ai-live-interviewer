# Changelog

All notable changes to this project are logged here, most recent first.

## [Fix] — Speech-to-text crash: "open() got an unexpected keyword argument 'metadata_errors'"
- faster-whisper's built-in audio decoder passes an option some PyAV versions reject. The app now
  decodes the recording itself (basic PyAV calls, ffmpeg as fallback) and gives Whisper the raw audio.

## [Fix] — Show real speech-to-text errors
- Transcription failures now return the actual error (and log a traceback) instead of a bare
  "Internal Server Error"; empty/too-short recordings get a clear message; the page shows the
  server's message text rather than raw JSON.

## [Fix] — 0.0.0.0 blocks the microphone
- The server now listens on 127.0.0.1 (uvicorn prints a working link), and any request
  arriving via 0.0.0.0 is automatically redirected to localhost. Log in again after the redirect
  (cookies are per-address).

## [Fix] — Ending an interview
- "End interview" now asks for confirmation, stops the mic/audio, and ignores any AI reply
  still in flight. An "Interview ended" panel shows time spent and answers given, with a
  "Start a new interview" button (also shown when time runs out). Added a Cancel link before beginning.

## [Fix] — Speed, custom duration, layout, mic diagnostics
- Faster replies: interviewer turns capped to 1-3 short sentences (`prompt_builder.py`,
  `num_predict`), model kept loaded (`keep_alive`), LLM + speech-to-text preloaded at
  startup, and per-turn timings (LLM / TTS / STT) logged in the terminal.
- Setup page: added 30/45/60 min presets and a custom-minutes field (1-120).
- Live interview page: transcript now sits to the right of the orb (stacks on narrow screens).
- Mic errors now say exactly why (wrong address, permission blocked, no mic, mic in use).

## [Step 2b] — Free local voice stack (replaces paid OpenAI Realtime as default)
- New default voice pipeline: Ollama (LLM) + faster-whisper (STT) + Piper (TTS),
  all local, no API keys, no cost.
- Added `app/services/{llm,stt,tts}.py` and `app/routers/voice_local.py`.
- Rewrote `voice.js` / `interview_live.html` to push-to-talk.
- Added `scripts/setup-local-ai.sh`; updated `.env.example`, `requirements.txt`,
  `app/config.py` (removed OpenAI settings, added Ollama/Whisper/Piper).
- OpenAI Realtime files kept but unused.

## [Fix] — Nav bar not sticky, mismatched pill spacing
- Nav bar now uses `position: sticky` so it stays visible while scrolling.
- Fixed a CSS bug where `label:first-of-type { margin-top: 0; }` — meant only
  to tighten spacing above the first field label in a form — was also
  matching the first pill in every button group (Technical / Easy / 1 min),
  giving those three a different margin than their siblings and making them
  look like a different shape. Scoped the rule to `.card > form >
  label:first-of-type` and gave `.pill` its own explicit `margin: 0`, spaced
  instead by `.button-group`'s `gap`.
- Note: the "can't access microphone" error is not a code bug — browsers only
  allow mic access on `localhost`/`127.0.0.1`, not on `0.0.0.0`. Always open
  the app at `http://localhost:8000`, never `http://0.0.0.0:8000`.

## [Fix] — Signup/login 500 error (passlib + bcrypt incompatibility)
- `passlib` (unmaintained) runs an internal self-test on its bcrypt backend
  that crashes with newer `bcrypt` versions (4.1+): `AttributeError: module
  'bcrypt' has no attribute '__about__'`, which then surfaces as `ValueError:
  password cannot be longer than 72 bytes` on the very first signup/login.
- Replaced `passlib` with direct calls to the `bcrypt` library in
  `app/security.py` (`bcrypt.hashpw` / `bcrypt.checkpw`) — simpler and avoids
  this entire class of bug. Removed `passlib` from `requirements.txt`, pinned
  `bcrypt==4.2.1`.

## [Step 2] — Live Voice Interview
- Added the actual live voice interview: mic capture, WebRTC connection proxied
  through the backend to OpenAI's Realtime API (`/v1/realtime/calls`), an
  animated voice orb (idle/connecting/listening/thinking/speaking/finished/
  error), a live transcript saved to the database as it streams in, and a
  countdown timer that auto-ends the interview at zero.
- Added `app/services/prompt_builder.py` (layered interviewer system prompt)
  and `app/services/realtime_session.py` (server-side SDP proxy — the OpenAI
  key never reaches the browser).
- Added `app/routers/realtime.py` and two new endpoints on the interviews
  router: `POST .../messages` and `POST .../end`.
- `interview_ready.html` now links straight into the live interview.
- Requires `OPENAI_API_KEY` (with Realtime API access) in `.env`.

## [Stack Pivot + Step 1] — Python-first rebuild, Landing/Auth/Setup
- **Pivoted the whole stack to Python**: FastAPI + SQLAlchemy (SQLite) + Jinja2,
  replacing the original Next.js/NestJS/Prisma plan. Removed `frontend/`,
  `backend/`, `docker/`; added `app/` (the FastAPI project) and `tests/`.
- Applied forest green, minimal UI theme.
- Added SQLAlchemy models: `User`, `Interview`, `InterviewMessage`,
  `PracticeQuestion`, `QuestionBookmark`, `AnalyticsSnapshot`.
- Added cookie/JWT auth (`security.py`, `deps.py`) — signup, login, logout.
- Added landing page, interview setup page (job role / experience / type /
  difficulty / duration / optional JD & resume), and interview creation
  (saves to DB, status `CREATED`).
- Added `scripts/setup.sh` and `scripts/run.sh` for local dev.
- Verified: all Python files pass `py_compile` (no runtime test possible in this
  sandbox — no network to install packages — so test it locally with the
  commands in the README).

## [Step 0] — Project Foundation
- Created master project folder structure (`frontend/`, `backend/`, `python/`,
  `scripts/`, `updates/`, `backups/`, `docs/`, `docker/`).
- Added `README.md` as the living architecture + roadmap + progress tracker.
- Added `docs/spec-interview-architecture.md`, `docs/spec-dashboard.md`,
  `docs/dev-workflow.md` consolidating both source planning conversations in full.
- Added the update tooling: `scripts/create-update.sh`, `scripts/install-update.sh`.
- Added `.env.example`, `.gitignore`.
- No application code yet — this is the foundation step only.
