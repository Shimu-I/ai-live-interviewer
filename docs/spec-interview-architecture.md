# Spec: Core Interview Architecture

Consolidated from the project's first planning conversation. This is the "AI
interviewer brain" spec — everything about how the live interview itself behaves.

## 1. Core Principle

The interview must **not** be a fixed list of questions. It is a goal-driven
conversation:

```
AI asks a question → Candidate answers → AI understands the answer →
AI analyzes it → AI decides what's next → AI asks a natural follow-up →
... → Time check → Continue or conclude
```

The AI has **interview goals** (e.g. understand background, test main skill, test
problem solving, gather behavioral evidence) and decides *how* to reach them
naturally, rather than reading down a script.

## 2. Interviewer Personality

Be: professional, calm, natural, friendly, conversational, clear, confident,
respectful, experienced.

Avoid: robotic, overly enthusiastic, too formal/casual, too fast/slow, repetitive.
Do not constantly say "Great!" / "Excellent!" / "Amazing!" after every answer — use
natural acknowledgements ("I see." / "Could you tell me more about that?" / "What
happened next?").

## 3. Interview Setup (user-facing options)

- **Job Role**: Software Engineer, Frontend Developer, Backend Developer, Data
  Scientist, ML Engineer, UI/UX Designer, Marketing, Customer Support, Product
  Manager, Custom.
- **Experience Level**: Intern, Junior, Mid-Level, Senior, Custom.
- **Interview Type**: Technical, HR, Behavioral, Mixed, Custom.
- **Difficulty**: Easy, Medium, Hard, **Adaptive** (recommended default — AI raises
  difficulty when candidate is strong, changes approach when they struggle, without
  assuming anything about the candidate as a person).
- **Duration**: 1 / 5 / 10 / 20 minutes, plus Custom (30/45/60).
- **Optional Resume/CV upload** — parsed for education, experience, projects,
  skills, achievements; AI references it naturally during the interview.
- **Optional Job Description paste** — AI builds a coverage checklist from required
  skills and prioritizes covering them.

## 4. Interview Screen (voice UI)

Minimal, modern, premium, calm, not cluttered, responsive, accessible.

Shows: job role, remaining time, large animated voice orb, AI interviewer name,
current voice state, optional live transcript, mic status, connection status,
pause, end interview.

### Voice Orb States
`idle, connecting, listening, processing, thinking, speaking,
candidate_interrupted (interrupted), paused, finished, error`

Each state gets a distinct animation (e.g. listening = gentle pulse, speaking =
multi-dot waveform, thinking = orbiting dots). Smooth transitions, CSS/Framer Motion.

## 5. Voice Experience Requirements

- Live microphone input, natural AI voice output, low latency.
- Natural turn-taking: candidate can interrupt the AI mid-sentence; AI stops
  speaking and listens.
- Silence handling: don't interrupt immediately on pause; after a configurable
  delay, AI can gently prompt ("Take your time." / offer to start from an example).
- **"I don't know" handling**: don't just move on — ask how the candidate would
  approach finding the answer (tests problem solving / learning ability).
- Do not infer emotional/mental state from voice signals (e.g. "nervousness"); only
  react to observable conversational signals (long pauses, very short answers,
  repeated hesitation) with slightly more supportive phrasing — never assumptions
  about the person.

Recommended: **OpenAI Realtime API over WebRTC**. Never expose the OpenAI API key to
the frontend — the backend mints a short-lived/ephemeral realtime session and the
frontend connects with that.

Low-cost/dev mode: STT → text LLM → TTS pipeline as a swappable alternative to full
Realtime voice, since Realtime audio is metered and can get expensive during
development. The Interview Orchestrator must be agnostic to which voice pipeline is
active.

## 6. Interview Orchestrator (the main brain)

The voice model handles *conversation*, the Orchestrator handles *strategy*. Do not
let the voice model alone drive the whole interview.

```
Voice AI → Interview Orchestrator → {Memory Manager, Topic Manager, Time Manager,
Answer Analyzer, Question Strategy Engine, Follow-up Engine, Difficulty Manager,
Evaluation Manager} → Next Interview Strategy → AI Response (voice)
```

### Conversation Manager
Receives candidate answers → stores them → updates conversation context → sends to
orchestrator → receives next strategy → generates the AI's next utterance.

### Memory Manager — two levels
- **Short-term / live context**: current question, last answer, current topic, last
  ~10 messages.
- **Structured interview memory** (persisted, grows over the interview):
  ```json
  {
    "skills": [], "projects": [], "experience": [], "achievements": [],
    "strengths": [], "areasToExplore": [],
    "topicsCompleted": [], "topicsRemaining": []
  }
  ```

### Topic Manager
Tracks coverage per topic (Background, Experience, Technical Skills, Problem
Solving, Communication, Behavioral) as Not Started / Partial / Complete. Prevents
the AI from wandering forever or missing important areas.

### Question Strategy Engine
Every question has an explicit internal purpose, one of:
`OPEN_QUESTION, FOLLOW_UP, CLARIFICATION, DEEP_DIVE, TECHNICAL, BEHAVIORAL,
SCENARIO, PROBLEM_SOLVING, TRANSITION, FINAL_QUESTION`

### Follow-up Engine — priority order
1. Important unanswered information
2. Interesting candidate experience worth exploring
3. Weak or vague answer needing clarification
4. Job requirement not yet covered
5. Technical depth
6. Behavioral skills
7. New topic

### Decision Engine (pseudocode)
```
IF answer_is_vague               → CLARIFICATION
ELSE IF interesting_project      → DEEP_DIVE
ELSE IF important_topic_missing  → NEW_TOPIC
ELSE IF candidate_answer_strong  → INCREASE_DIFFICULTY
ELSE IF time_is_low              → FINAL_QUESTION
ELSE                             → FOLLOW_UP
```

### Time Manager / Time Intelligence
| Phase | % of duration | Goal |
|---|---|---|
| Beginning | 0–20% | Understand candidate |
| Middle | 20–75% | Deep exploration |
| Final | 75–100% | Finish important topics, ask final question, conclude |

Duration → depth mapping: 1 min = intro + 1 question; 5 min = background + one deep
follow-up; 10 min = background → experience → skills → project → problem solving;
20 min = full arc including behavioral + scenario questions.

Never end abruptly. Near the end: *"We're approaching the end of the interview, so
I'd like to ask one final question."* → then a professional close.

### Answer Analyzer
Classifies each answer: clear? specific? contains an interesting topic worth
exploring? needs more detail? Also detects: answer too short (ask to expand), answer
too long (acknowledge, then pivot to one specific part), and for behavioral
interviews, **STAR structure** (Situation/Task/Action/Result) — follow up on
whichever component is missing (commonly Result).

### Difficulty Manager
Adaptive mode: raise difficulty after strong answers, change approach (not
"simplify because the candidate must be struggling") after weak ones — react to the
answer, not to assumptions about the person.

## 7. Layered AI Prompt (not one giant prompt)

1. **Identity** — "You are a professional interviewer."
2. **Behavior rules** — natural conversation, one question at a time, no
   questionnaire behavior.
3. **Interview goals** — experience, skills, problem solving, communication,
   decision making.
4. **Context** — job role, job description, resume, interview type, difficulty,
   duration.
5. **Live state** — current topic, topics completed, time remaining, candidate
   info gathered so far, running conversation summary.

Only the context needed for the current decision is sent — use structured
summaries/memory rather than replaying the full transcript every turn once it gets
long.

## 8. Interview Modes
- **Practice Mode** — friendly, can give hints/feedback during the session.
- **Realistic Interview** — professional, no hints, natural recruiter behavior.
- **Strict Interview** — harder questions, less guidance, deeper follow-ups.
- **Stress Interview** (optional, clearly opt-in) — pressure scenarios, rapid
  follow-up; use carefully.

## 9. Evaluation & Report

After the interview: overall score + per-category scores (communication, technical
skill, problem solving, experience — never infer "confidence" from voice alone).

Detailed feedback: strengths, areas to improve, and a concrete "your answer →
better answer" example. Full transcript stored and downloadable. Interview replay
(scrub through timeline, click a Q/A pair to see feedback) is a later/advanced
feature.

## 10. System Architecture

```
Next.js/React Frontend
        │  HTTPS
        ▼
NestJS Backend ── Auth Service, File Service
        │
        ▼
Interview Orchestrator ── Memory, Timer, Analyzer ── Question Strategy
        │
        ▼
OpenAI Realtime API (WebRTC) ── AI Voice ── Candidate
        │
        ▼
PostgreSQL (users, interviews, messages, results, usage)
```

Frontend structure: `components/ (VoiceOrb, InterviewTimer, Transcript,
InterviewControls, InterviewSetup, Feedback)`, `pages/`, `hooks/
(useRealtimeVoice, useInterviewTimer, useInterviewState)`, `services/`, `store/`.

Backend structure (NestJS modules): `auth, users, interviews, realtime,
orchestrator, memory, analytics, reports, resumes`, plus services:
`InterviewService, InterviewOrchestrator, ConversationMemory, QuestionStrategy,
AnswerAnalyzer, TimeManager, ReportGenerator`.

## 11. Security & Cost Control

- Never put the OpenAI key in the frontend; backend mints ephemeral realtime
  sessions.
- Auth, rate limiting, session validation, encrypted secrets, input validation, DB
  access control.
- Track per-interview usage: input/output tokens, audio duration, estimated cost.
- Enforce max interview duration, max daily interviews, automatic disconnect,
  session timeout, rate limiting.
- Keep the orchestrator compatible with both Realtime Voice mode and the cheaper
  STT→LLM→TTS mode for development.

## 12. Interview State Shape (reference)

```json
{
  "interviewId": "",
  "status": "active",
  "jobRole": "",
  "interviewType": "",
  "difficulty": "adaptive",
  "duration": 600,
  "timeRemaining": 420,
  "currentTopic": "",
  "completedTopics": [],
  "remainingTopics": [],
  "candidateProfile": {},
  "conversationSummary": "",
  "questionHistory": [],
  "interviewGoals": []
}
```
