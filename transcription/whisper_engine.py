"""Local speech-to-text with faster-whisper, plus a rolling transcript buffer.

Runs entirely on-device (no audio leaves the machine). The model loads lazily on
first use so importing this module stays cheap.
"""

from collections import deque

import numpy as np

# Rolling transcript — keeps the last N utterances (~2-3 min of conversation).
transcript_buffer: "deque[str]" = deque(maxlen=10)

# 'base.en' is fast and accurate enough; bump to 'small.en' for more accuracy.
_MODEL_NAME = "base.en"
_model = None


def _get_model():
    """Load the Whisper model once, on first transcription."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(_MODEL_NAME, device="cpu", compute_type="int8")
    return _model


def transcribe_chunk(audio_np: "np.ndarray") -> str:
    """Transcribe a mono float32 chunk at 16 kHz.

    Returns the transcribed text, or "" for silence. Non-empty results are
    appended to ``transcript_buffer``.
    """
    # faster-whisper wants a 1-D float32 array.
    audio_np = np.asarray(audio_np, dtype=np.float32).reshape(-1)

    segments, _ = _get_model().transcribe(
        audio_np,
        beam_size=1,                # fastest decode
        language="en",
        vad_filter=True,            # built-in silence suppression
        vad_parameters={"min_silence_duration_ms": 500},
    )
    text = " ".join(seg.text for seg in segments).strip()
    if text:
        transcript_buffer.append(text)
    return text


def get_context() -> str:
    """Return the rolling transcript as a single string for the prompt."""
    return " ".join(transcript_buffer)
