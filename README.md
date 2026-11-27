# AI Live Interviewer

A real-time, human-like AI voice interview platform. The AI interviewer conducts a
natural, adaptive conversation with a candidate — it does **not** behave like a fixed
questionnaire. It listens, remembers, analyzes each answer, and decides what to ask
next based on interview goals, topic coverage, and time remaining.

This README is the single source of truth for project status. **It is updated after
every step** so that any future Claude session (or you) can open this file and know
exactly what exists, what doesn't, and what's next. Do not delete history from the
"Progress Log" — append to it.

---

## 1. Source Specs

This project's requirements come from two prior ChatGPT planning conversations,
fully incorporated here:

- `docs/spec-interview-architecture.md` — core interview experience, AI orchestrator,
  memory system, question strategy, voice UX, evaluation (from convo-1).
- `docs/spec-dashboard.md` — dashboard, interview history, practice center, analytics,
  transcript export, database additions (from convo-2).
- `docs/dev-workflow.md` — how updates from Claude are packaged and applied on your
  Ubuntu machine (ZIP + manifest + install script).

All features from both conversations are accepted and in scope. Nothing is dropped;
things not yet built are listed in the roadmap below as "Not started."

---

## 2. Tech Stack (decided — revised to Python-first)

> **Revision note:** the project originally planned Next.js/NestJS/Prisma. Per your
> request to keep everything in Python (your language of choice) and avoid
> unnecessary complexity, it was rebuilt as below. Everything from both source
> specs is still fully in scope — only the implementation language/tooling changed.

| Layer | Technology | Notes |
|---|---|---|
| Backend + app logic | **FastAPI (Python)** | Auth, orchestrator, memory, question strategy, dashboard, analytics — all Python |
| Frontend | **Jinja2 server-rendered HTML + plain CSS** | No React/Next.js, no build step |
| Database | **SQLite via SQLAlchemy** | One file, zero setup; swap to Postgres later by changing one `.env` line |
| Auth | Simple cookie/JWT auth built into the app | No external auth provider needed |
| Voice (default, free) | **Ollama (LLM) + faster-whisper (speech-to-text) + Piper (text-to-speech)** | 100% local, open source, CPU-only friendly, no API keys. Turn-based push-to-talk. |
| Optional paid path | OpenAI Realtime API | Code kept in `app/routers/realtime.py` + `app/services/realtime_session.py`, **unused by default**. Not required. |
| Styling | Forest green, minimal, readable | See `app/static/css/style.css` |

This keeps ~95% of the project — everything that actually matters (the interview
intelligence, the dashboard, the data) — in Python, which you already know. See
`docs/dev-workflow.md` for setup.

---

## 3. Master Folder Structure

```
ai-live-interviewer/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py                # settings (env-driven)
│   ├── database.py              # SQLAlchemy engine/session
│   ├── security.py              # password hashing + JWT
│   ├── deps.py                  # auth dependencies (get_current_user)
│   ├── schemas.py               # Pydantic request/response models
│   ├── models/                  # SQLAlchemy tables: user, interview, interview_message,
│   │                             #   practice_question, question_bookmark, analytics_snapshot
│   ├── routers/                 # auth, pages, interviews, (dashboard/practice/analytics/realtime to come)
│   ├── services/                # orchestrator, memory, question_strategy, follow_up,
│   │                             #   timer, transcript_export, answer_analyzer (Phase 2+)
│   ├── templates/                # Jinja2 HTML (forest green theme)
│   └── static/
│       ├── css/style.css
│       └── js/                   # app.js (UI), voice.js added in Phase 2 (mic/WebRTC)
├── tests/
├── scripts/                     # dev + update tooling (see docs/dev-workflow.md)
│   ├── setup.sh                  # one-time: creates venv, installs deps
│   ├── run.sh                    # starts the dev server
│   ├── create-update.sh          # packages changed files into update-XXX.zip
│   └── install-update.sh         # applies an update ZIP to your local copy
├── updates/                     # generated update-XXX.zip staging area
├── backups/                     # backups created automatically before applying updates
├── docs/                        # full specs + architecture docs (this project's memory)
├── requirements.txt
├── .env.example
├── README.md                    # you are here
└── CHANGELOG.md
```

**Rule for all future updates:** new/changed files are only ever delivered as
`updates/update-XXX.zip` (manifest + files + install script), never as a full
folder replacement. See `docs/dev-workflow.md`.

---

## 4. Development Roadmap (phases, combining both source conversations)

Status legend: ✅ Done · 🚧 In progress · ⬜ Not started

| Phase | Contents | Status |
|---|---|---|
| **0** | Project foundation: folder structure, README, docs, update/ZIP tooling | ✅ Done |
| **1** | Landing page, interview setup UI, basic auth, DB schema, interview creation | ✅ Done (this step) |
| **2** | Voice MVP: mic, voice orb, live transcript, start/stop — rebuilt on a **free local stack** (Ollama + Whisper + Piper) | ✅ Done (this step) |
| **3** | Interview Orchestrator: memory manager, topic manager, question strategy engine, follow-up engine, timer/time intelligence | ⬜ Not started |
| **4** | Advanced interview: adaptive difficulty, resume analysis, job-description analysis, STAR detection, answer-length handling | ⬜ Not started |
| **5** | Evaluation: interview summary, strengths/weaknesses, scored feedback, transcript (MD/TXT/PDF later), interview history | ⬜ Not started |
| **6** | Dashboard: overview stats, interview history (all/completed/quit/expired/failed), interview details, practice center, bookmarks, analytics over time, role statistics, recent activity | ⬜ Not started |
| **7** | Advanced/production: interview replay, cost monitoring & rate limiting, security hardening, deployment | ⬜ Not started |

We execute **one phase/step at a time**, and this table (plus the Progress Log below)
gets updated at the end of every step.

---

## 5. Database Schema Summary (full detail in `docs/spec-dashboard.md` and `docs/spec-interview-architecture.md`)

Core tables:
- `users`
- `interviews` (id, user_id, job_role, interview_type, difficulty, duration,
  actual_duration, status, started_at, ended_at, created_at)
- `interview_messages` (id, interview_id, speaker [AI|USER], content, timestamp,
  sequence_number)
- `practice_questions` (id, user_id, interview_id, message_id, question,
  previous_answer, category, status [NEW|PRACTICING|COMPLETED|ARCHIVED], created_at)
- `question_bookmarks` (id, user_id, question_id, created_at)
- `analytics_snapshots` (id, user_id, period, total_interviews, completed_interviews,
  quit_interviews, average_score, created_at)
- `candidate_profiles` / structured memory (skills, projects, experience, strengths,
  weaknesses, topics completed/remaining)
- `interview_results` / evaluations
- `usage` (token/audio usage + cost tracking per interview)

Interview status enum: `CREATED, STARTING, ACTIVE, PAUSED, COMPLETED, QUIT,
TIME_EXPIRED, FAILED`.

Prisma schema will be created in Phase 1 (`backend/prisma/schema.prisma`).

---

## 6. Progress Log

### Step 0 — Project Foundation (done)
- Created master folder structure under `ai-live-interviewer/`.
- Wrote this README as the living tracker.
- Wrote `docs/spec-interview-architecture.md` and `docs/spec-dashboard.md`,
  consolidating everything from both source ChatGPT conversations so no feature
  is lost.
- Wrote `docs/dev-workflow.md` describing the Ubuntu dev setup, Python venv
  isolation, and the ZIP + manifest + Bash install-script update system.
- Built the update tooling itself: `scripts/create-update.sh` (packages changed
  files into `update-XXX.zip` with manifest) and `scripts/install-update.sh`
  (template shipped inside each update ZIP; backs up before overwriting, never
  deletes unrelated files).
- Created `CHANGELOG.md` and `.env.example` placeholders.
- **No application code yet.** Phase 1 starts next.

### Stack Pivot — Python-first
- Rebuilt the project on **FastAPI + SQLAlchemy (SQLite) + Jinja2**, replacing the
  original Next.js/NestJS/Prisma plan, per your request to keep everything in
  Python. See Section 2. All features from both source specs remain in scope —
  only the implementation stack changed.
- Applied the forest green, minimal UI theme (`app/static/css/style.css`).

### Step 1 — Landing, Auth, Interview Setup, Database (done)
- `app/models/` — SQLAlchemy tables for `users`, `interviews`, `interview_messages`,
  `practice_questions`, `question_bookmarks`, `analytics_snapshots`, matching
  Section 5 exactly. Auto-created in SQLite on first run.
- `app/security.py`, `app/deps.py` — password hashing + JWT cookie sessions.
- `app/routers/auth.py` — signup / login / logout.
- `app/routers/pages.py` — landing page, interview setup page.
- `app/routers/interviews.py` — creates an `Interview` row from the setup form
  (status `CREATED`), redirects to a confirmation page.
- Templates: `landing.html`, `signup.html`, `login.html`, `setup.html`,
  `interview_ready.html`, all extending `base.html`, forest green theme.
- `scripts/setup.sh` (creates venv + installs deps + copies `.env`) and
  `scripts/run.sh` (starts the dev server).
- **Not yet built**: the actual live voice interview — creating an interview just
  saves it and shows a confirmation page. That's Phase 2.

### Step 2 — Live Voice Interview (done)
- `app/services/prompt_builder.py` — builds the layered AI-interviewer system
  prompt (identity, behavior rules, goals, context) from the interview's job
  role, type, difficulty, duration, resume, and job description.
- `app/services/realtime_session.py` — server-side WebRTC handshake with
  OpenAI's Realtime API (`/v1/realtime/calls`, the "unified interface"). The
  OpenAI API key is used only here; it never reaches the browser.
- `app/routers/realtime.py` — `POST /api/interviews/{id}/realtime-session`
  proxies the browser's SDP offer, returns OpenAI's SDP answer, and marks the
  interview `ACTIVE` with a `started_at` timestamp.
- `app/routers/interviews.py` — added `POST /api/interviews/{id}/messages`
  (saves each transcript line as it's finalized, so nothing is lost if the
  tab closes) and `POST /api/interviews/{id}/end` (sets status COMPLETED /
  QUIT / TIME_EXPIRED + `actual_duration`).
- `app/templates/interview_live.html` + `app/static/js/voice.js` — mic
  capture, WebRTC connection, the AI is prompted to speak first, a voice orb
  that reflects `idle / connecting / listening / thinking / speaking /
  finished / error`, a live transcript, and a countdown timer that
  auto-ends the interview as `TIME_EXPIRED` at zero.
- `app/static/css/style.css` — orb animations (pulse for listening, spin for
  thinking, faster pulse for speaking) and transcript bubble styling, forest
  green theme.
- `app/templates/interview_ready.html` — now links to the live interview
  instead of showing a "not built yet" note.
- **Requires** `OPENAI_API_KEY` in `.env` with Realtime API access.
- **Not yet built**: the full Interview Orchestrator (topic tracking, explicit
  follow-up priority logic, adaptive difficulty engine, STAR detection) — for
  now the Realtime model follows the instructions prompt directly, which
  already produces natural follow-ups but doesn't yet track topic coverage
  structurally. That's Phase 3. Also not yet built: pause/resume, interview
  evaluation/scoring, and transcript downloads.

### Next Step (Phase 3, not yet started)
- `app/services/orchestrator.py` — structured topic tracking, follow-up
  priority engine, time-phase logic, injected back into the session via
  `session.update` mid-interview (rather than relying solely on the initial
  instructions).
- Answer analyzer (vague/short/long detection, STAR component detection).
- Adaptive difficulty manager.
- Package as `update-003.zip`.

### Step 2b — Switched to a 100% free local voice stack (done)
- Reason: the OpenAI Realtime API is paid; this project must cost nothing.
- `app/services/llm.py` — AI interviewer replies via your local **Ollama** model.
- `app/services/stt.py` — **faster-whisper** transcribes your spoken answers (CPU).
- `app/services/tts.py` — **Piper** speaks the AI's replies (CPU).
- `app/routers/voice_local.py` — `POST /api/interviews/{id}/ai-turn` (LLM + TTS,
  returns audio + transcript) and `POST /api/interviews/{id}/user-turn`
  (uploads your recorded answer, returns the transcript).
- `voice.js` / `interview_live.html` rewritten: **push-to-talk** ("Start
  answering" / "Stop & send answer") instead of always-on voice detection.
  Trade-off: turn-based, with a few seconds of pause per reply on CPU.
- `scripts/setup-local-ai.sh` — one-time: pulls the Ollama model, downloads the
  Piper voice, pre-downloads the Whisper model.
- OpenAI code is still in the repo but unused; `OPENAI_API_KEY` is no longer needed.

### How to Run This Right Now
```bash
cd ai-live-interviewer
./scripts/setup.sh              # one-time: venv + Python deps
./scripts/setup-local-ai.sh     # one-time: LLM + voice models (needs Ollama installed)
./scripts/run.sh                # start the app
# open http://localhost:8000   (NOT 0.0.0.0 — browsers block the mic there)
```
Tip: slow replies? Keep `OLLAMA_MODEL=llama3.2` (3B). Want smarter answers and
OK with waiting longer? Set `OLLAMA_MODEL=qwen2.5:7b` and run `ollama pull qwen2.5:7b`.

---

## 7. How to Resume Work With Claude

Paste this file's contents (or just say "continue from the README") at the start of
a new conversation, and ask Claude to proceed with the next unstarted phase in
Section 4. Claude should always update Section 4's status table and append to the
Progress Log at the end of a step.
