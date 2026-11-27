# Spec: Dashboard, History, Practice Center & Analytics

Consolidated from the project's second planning conversation. The Dashboard is a
**major part of the system**, not an afterthought — it's what lets the user
practice, review mistakes, revisit old interviews, and track improvement over time.

## 1. Dashboard Architecture

```
DASHBOARD
├── Overview
├── Start Interview
├── Interview History
│      ├── All
│      ├── Completed
│      ├── Quit
│      ├── Expired
│      └── Failed
├── Interview Details
│      ├── Summary
│      ├── Transcript
│      ├── Feedback
│      ├── Practice Questions
│      └── Download
├── Practice Center
│      ├── Weak Answers
│      ├── Unanswered Questions
│      ├── Saved Questions
│      └── Practice Again
├── Analytics
│      ├── Performance
│      ├── Progress
│      ├── Roles
│      └── Interview Statistics
└── Settings
```

## 2. Main Dashboard (Overview)

Top-level stat cards: Total Interviews, Completed Interviews, Quit/Incomplete
Interviews. An "Average Performance" section with per-category bars
(Communication, Problem Solving, Technical Knowledge). A "Recent Interviews" list
(role, status, action link — View for completed, Resume for quit/in-progress).

## 3. Interview Categories

- **All Interviews** — everything (Completed, Quit, Expired, Failed, In Progress).
- **Completed Interviews** — view results, review conversation, download
  transcript, practice questions from it, compare results across interviews.
- **Quit / Incomplete Interviews** — important. Show progress made (e.g. "4 minutes
  / 10 minutes", "6 questions answered", date). Actions: View Transcript, Continue
  Practice, Download Transcript, Delete.

### Interview Status Enum
Internal: `CREATED, STARTING, ACTIVE, PAUSED, COMPLETED, QUIT, TIME_EXPIRED, FAILED`
Displayed simply as: `Completed, In Progress, Quit, Expired, Failed`

## 4. Download Transcript Feature

Offered right after an interview ends (`View Results` / `Download Transcript`), and
always available later via Dashboard → Interview History → select interview →
Download Transcript, in case the user forgets at the time.

**Formats**: Markdown (`.md`) and Text (`.txt`) are in scope now. PDF can be added
later (Phase 7+).

### Markdown transcript format
```
# AI Interview Transcript

## Interview Information
Role: Software Engineer
Interview Type: Technical
Duration: 10 Minutes
Date: <date>
Status: Completed

---

## Conversation

### AI Interviewer
<question>

### Candidate
<answer>

---
```

### TXT transcript format
```
AI INTERVIEW TRANSCRIPT

Role: Software Engineer
Interview Type: Technical
Duration: 10 Minutes
Date: <date>
Status: Completed

-----------------------------------

AI INTERVIEWER:
<question>

CANDIDATE:
<answer>
```

**TranscriptExportService** architecture:
```
Interview → Messages → Transcript Formatter → {Markdown, TXT} → File Generation → Download
```

## 5. Practice Forgotten Questions

If the candidate answered poorly or with "I don't know," the Dashboard surfaces it
under Interview Review → Questions to Practice → Practice Again. This starts a new
short voice session focused on that one question ("Previously, you had difficulty
answering this question. Let's practice it again...").

### Practice Question Categories
Unanswered Questions, Weak Answers, Technical Questions, Behavioral Questions,
Problem Solving Questions, Questions You Marked (bookmarked).

## 6. Bookmark Feature

During or after an interview, the user can mark any question with "☆ Practice
Later." These collect under Dashboard → Practice Center → Saved Questions.

## 7. Analytics

- **Progress over time** per category (e.g. Technical Knowledge / Communication /
  Problem Solving, month over month) — shown as simple bar comparisons so the user
  can see improvement.
- **Analytics categories**: Total Interviews, Completed Interviews, Quit
  Interviews, Average Duration, Average Topic Coverage, Technical Performance,
  Communication Structure, Problem Solving, Behavioral Answers, Practice Questions
  Completed.
- **Interviews by Role** — count + average score per job role practiced.
- **Recent Activity feed** — e.g. "Today: Completed Software Engineer Interview",
  "Yesterday: Practiced System Design Question", "Sept 5: Downloaded Frontend
  Interview Transcript."

## 8. Database Additions (on top of the core schema)

```
interviews
  id, user_id, job_role, interview_type, difficulty, duration, actual_duration,
  status, started_at, ended_at, created_at

interview_messages
  id, interview_id, speaker (AI|USER), content, timestamp, sequence_number

practice_questions
  id, user_id, interview_id, message_id, question, previous_answer, category,
  status (NEW|PRACTICING|COMPLETED|ARCHIVED), created_at

question_bookmarks
  id, user_id, question_id, created_at

analytics_snapshots
  id, user_id, period, total_interviews, completed_interviews, quit_interviews,
  average_score, created_at
```

## 9. Recommended API Endpoints

```
GET  /api/dashboard
GET  /api/interviews
GET  /api/interviews/:id
GET  /api/interviews/:id/transcript
GET  /api/interviews/:id/download?format=md
GET  /api/interviews/:id/download?format=txt
GET  /api/practice
POST /api/practice/:id/start
POST /api/questions/:id/bookmark
GET  /api/analytics
```

These map to the `dashboard`, `interviews`, `practice`, and `analytics` backend
modules in the master folder structure.
