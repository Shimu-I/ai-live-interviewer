// Live voice interview — free local pipeline. Push-to-talk audio is sent to the
// backend (faster-whisper transcribes), a local Ollama model replies, Piper
// speaks the reply. No cloud APIs.
document.addEventListener("DOMContentLoaded", () => {
  if (!document.getElementById("interview-root")) return;

  const interviewId = window.INTERVIEW_ID;
  let secondsRemaining = window.INTERVIEW_DURATION_SECONDS;
  let secondsElapsed = 0;

  const $ = (id) => document.getElementById(id);
  const orb = $("orb"), orbLabel = $("orb-label"), errorBox = $("error-box");
  const timerEl = $("timer"), transcriptEl = $("transcript"), aiAudio = $("ai-audio");
  const startBtn = $("start-btn"), recordBtn = $("record-btn"), endBtn = $("end-btn");
  const endedPanel = $("ended-panel"), endedTitle = $("ended-title"), endedSummary = $("ended-summary");
  const startControls = $("start-controls"), answerControls = $("answer-controls"), liveControls = $("live-controls");

  let timerInterval = null, ended = false, isRecording = false;
  let mediaRecorder = null, recordedChunks = [], activeStream = null;

  const LABELS = {
    idle: "Your turn \u2014 click \u201cStart answering\u201d",
    thinking: "Thinking...",
    speaking: "Speaking",
    listening: "Listening \u2014 click again when you're done",
    transcribing: "Working out what you said...",
    finished: "Interview finished",
    error: "Something went wrong",
  };

  const setOrb = (state) => { orb.dataset.state = state; orbLabel.textContent = LABELS[state] || state; };
  const showError = (msg) => { setOrb("error"); errorBox.textContent = msg; errorBox.style.display = "block"; };
  const clearError = () => { errorBox.style.display = "none"; };

  function addLine(speaker, content) {
    const line = document.createElement("div");
    line.className = "transcript-line " + (speaker === "AI" ? "ai" : "user");
    const label = document.createElement("span");
    label.className = "transcript-speaker";
    label.textContent = speaker === "AI" ? "Interviewer" : "You";
    const text = document.createElement("div");
    text.textContent = content;
    line.append(label, text);
    transcriptEl.appendChild(line);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }

  const fmt = (s) => { s = Math.max(0, s); return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`; };

  function startTimer() {
    timerInterval = setInterval(() => {
      secondsRemaining -= 1; secondsElapsed += 1;
      timerEl.textContent = fmt(secondsRemaining);
      timerEl.classList.toggle("timer-low", secondsRemaining <= 60);
      if (secondsRemaining <= 0) endInterview("TIME_EXPIRED");
    }, 1000);
  }

  async function endInterview(status) {
    if (ended) return;
    ended = true;
    clearInterval(timerInterval);
    if (isRecording && mediaRecorder) { try { mediaRecorder.stop(); } catch (e) {} }
    if (activeStream) activeStream.getTracks().forEach((t) => t.stop());
    aiAudio.pause();
    setOrb("finished");
    startControls.style.display = answerControls.style.display = liveControls.style.display = "none";

    const titles = { COMPLETED: "Interview complete", QUIT: "Interview ended early", TIME_EXPIRED: "Time's up" };
    const answers = transcriptEl.querySelectorAll(".transcript-line.user").length;
    endedTitle.textContent = titles[status] || "Interview ended";
    endedSummary.textContent = `You spoke for ${fmt(secondsElapsed)} and gave ${answers} answer${answers === 1 ? "" : "s"}.`;
    endedPanel.style.display = "block";
    try {
      await fetch(`/api/interviews/${interviewId}/end`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, actual_duration: secondsElapsed }),
      });
    } catch (e) { console.error(e); }
  }

  async function readError(res) {
    const text = await res.text();
    try { return JSON.parse(text).detail || text; } catch (e) { return text || `Server responded ${res.status}`; }
  }

  const b64ToUtf8 = (b64) => {
    const bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder("utf-8").decode(bytes);
  };

  async function requestAiTurn() {
    setOrb("thinking");
    answerControls.style.display = "none";
    try {
      const res = await fetch(`/api/interviews/${interviewId}/ai-turn`, { method: "POST" });
      if (ended) return;
      if (!res.ok) throw new Error(await readError(res));
      const enc = res.headers.get("X-AI-Text-Base64");
      addLine("AI", enc ? b64ToUtf8(enc) : "(no transcript)");

      const blob = await res.blob();
      if (ended) return;
      const url = URL.createObjectURL(blob);
      aiAudio.src = url;
      aiAudio.onended = () => {
        URL.revokeObjectURL(url);
        if (ended) return;
        setOrb("idle");
        answerControls.style.display = "flex";
      };
      setOrb("speaking");
      await aiAudio.play();
    } catch (e) {
      console.error(e);
      showError("Couldn't reach the AI interviewer. " + (e.message || ""));
      answerControls.style.display = "flex";
    }
  }

  async function toggleRecording() {
    if (!isRecording) {
      clearError();
      if (!window.isSecureContext || !navigator.mediaDevices) {
        showError(`The browser blocks the microphone because this page is open at "${location.host}". Open http://localhost:8000 instead (not 0.0.0.0 or an IP address).`);
        return;
      }
      try {
        activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (e) {
        const reasons = {
          NotAllowedError: "Microphone permission is blocked. Click the lock/site-settings icon in the address bar, set Microphone to Allow, then reload the page. Also check Ubuntu Settings > Privacy > Microphone.",
          NotFoundError: "No microphone was found on this computer. Check that one is plugged in and selected in Ubuntu Sound settings.",
          NotReadableError: "Your microphone is being used by another app. Close it and try again.",
        };
        showError(reasons[e.name] || `Couldn't access your microphone (${e.name}: ${e.message}).`);
        return;
      }
      recordedChunks = [];
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "audio/webm";
      mediaRecorder = new MediaRecorder(activeStream, { mimeType });
      mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) recordedChunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        activeStream.getTracks().forEach((t) => t.stop());
        activeStream = null;
        if (ended) return;
        setOrb("transcribing");
        const form = new FormData();
        form.append("audio", new Blob(recordedChunks, { type: mimeType }), "answer.webm");
        try {
          const res = await fetch(`/api/interviews/${interviewId}/user-turn`, { method: "POST", body: form });
          if (!res.ok) throw new Error(await readError(res));
          addLine("USER", (await res.json()).text);
          await requestAiTurn();
        } catch (e) {
          console.error(e);
          showError("Couldn't process your answer. " + (e.message || ""));
          answerControls.style.display = "flex";
        }
      };
      mediaRecorder.start();
      isRecording = true;
      recordBtn.textContent = "Stop & send answer";
      setOrb("listening");
    } else {
      isRecording = false;
      recordBtn.textContent = "Start answering";
      mediaRecorder.stop();
    }
  }

  startBtn.addEventListener("click", async () => {
    startBtn.disabled = true;
    clearError();
    startControls.style.display = "none";
    liveControls.style.display = "flex";
    startTimer();
    await requestAiTurn();
  });
  recordBtn.addEventListener("click", toggleRecording);
  endBtn.addEventListener("click", () => {
    if (!confirm("End this interview now?")) return;
    endInterview(secondsElapsed >= window.INTERVIEW_DURATION_SECONDS * 0.5 ? "COMPLETED" : "QUIT");
  });

  window.addEventListener("beforeunload", () => {
    if (!ended && secondsElapsed > 0) {
      navigator.sendBeacon(`/api/interviews/${interviewId}/end`,
        new Blob([JSON.stringify({ status: "QUIT", actual_duration: secondsElapsed })], { type: "application/json" }));
    }
  });
});
