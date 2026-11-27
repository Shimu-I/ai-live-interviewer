"""
Transcribes the candidate's spoken answers with faster-whisper — a local,
open-source Whisper implementation. CPU-only, no API key, no cost.

We decode the browser's recording to raw audio ourselves (instead of letting
faster-whisper do it) because faster-whisper's built-in decoder passes an
option to PyAV that some PyAV versions reject ("unexpected keyword argument
'metadata_errors'"). Handing Whisper a ready-made audio array sidesteps that.
"""
import logging
import shutil
import subprocess
from functools import lru_cache

from fastapi import HTTPException

from app.config import settings

log = logging.getLogger("uvicorn.error")

SAMPLE_RATE = 16000


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the rest of the site works even before this is installed.
    from faster_whisper import WhisperModel
    return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")


def _decode_with_pyav(path: str):
    """Decode any audio file to mono 16 kHz float32 using only basic PyAV calls."""
    import av
    import numpy as np

    container = av.open(path)
    try:
        stream = next(s for s in container.streams if s.type == "audio")
        resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
        chunks = []

        def collect(out):
            if out is None:
                return
            frames = out if isinstance(out, (list, tuple)) else [out]
            for f in frames:
                chunks.append(f.to_ndarray().reshape(-1))

        for frame in container.decode(stream):
            collect(resampler.resample(frame))
        collect(resampler.resample(None))  # flush
    finally:
        container.close()

    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def _decode_with_ffmpeg(path: str):
    """Fallback: use the system ffmpeg (sudo apt install ffmpeg) if PyAV fails."""
    import numpy as np

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed")
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
        capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="ignore")[-300:])
    return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def _decode_audio(path: str):
    try:
        return _decode_with_pyav(path)
    except Exception as e1:
        log.warning(f"PyAV decode failed ({type(e1).__name__}: {e1}); trying ffmpeg")
        try:
            return _decode_with_ffmpeg(path)
        except Exception as e2:
            raise RuntimeError(f"PyAV: {type(e1).__name__}: {e1} | ffmpeg: {e2}")


def transcribe_audio(file_path: str) -> str:
    try:
        model = _get_model()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Speech-to-text isn't available: {e}. Run: pip install -r requirements.txt",
        )

    try:
        audio = _decode_audio(file_path)
        if audio.size < SAMPLE_RATE * 0.3:  # under ~0.3 s of audio
            return ""
        segments, _info = model.transcribe(audio, beam_size=5)
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:
        log.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {type(e).__name__}: {e}")
