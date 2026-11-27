#!/bin/bash
# One-time setup for the free local AI stack (LLM + speech-to-text + text-to-speech).
# Run from the project root:  ./scripts/setup-local-ai.sh
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate

MODEL=$(grep -E '^OLLAMA_MODEL=' .env 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"')
MODEL="${MODEL:-llama3.2}"
VOICE=$(grep -E '^PIPER_VOICE=' .env 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"')
VOICE="${VOICE:-en_US-lessac-medium}"
WHISPER=$(grep -E '^WHISPER_MODEL=' .env 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"')
export WHISPER_MODEL="${WHISPER:-base.en}"

command -v ollama >/dev/null || { echo "Ollama not found. Install from https://ollama.com"; exit 1; }

echo "==> Pulling LLM: $MODEL (one-time download)"
ollama pull "$MODEL"

echo "==> Downloading Piper voice: $VOICE (one-time, ~60MB)"
python -m piper.download_voices "$VOICE"

echo "==> Downloading speech-to-text model: $WHISPER_MODEL (one-time)"
python -c "import os; from faster_whisper import WhisperModel; WhisperModel(os.environ['WHISPER_MODEL'], device='cpu', compute_type='int8'); print('Whisper ready.')"

echo "All set. Start the app with ./scripts/run.sh"
