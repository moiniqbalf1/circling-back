"""Audio capture from a loopback device (BlackHole on macOS).

The meeting app's output is routed through a virtual audio device so we can read
it without touching the microphone. On macOS that device is BlackHole; create a
Multi-Output Device (BlackHole + speakers) in Audio MIDI Setup and set it as the
system output so you still hear the call while it's being captured.

Run ``list_devices()`` once to find the index of the BlackHole input, then pass
it to ``start_capture()``.
"""

import sounddevice as sd
from queue import Queue

SAMPLE_RATE = 16000   # Whisper expects 16 kHz
CHUNK_SECONDS = 5     # Size of each audio chunk handed to Whisper

# Background capture pushes numpy float32 chunks here; the pipeline consumes them.
audio_queue: "Queue" = Queue()


def list_devices() -> None:
    """Print available audio devices so you can identify the loopback device.

    Look for an input named like ``BlackHole 2ch`` and note its index.
    """
    print(sd.query_devices())


def start_capture(device_index: int) -> sd.InputStream:
    """Open a loopback input stream on ``device_index``.

    Pushes mono float32 chunks (CHUNK_SECONDS long, at SAMPLE_RATE) onto
    ``audio_queue``. Returns the running stream so the caller can stop it.
    """
    def callback(indata, frames, time, status):
        if status:
            # Overflows/underflows are non-fatal; keep capturing.
            print(f"[capture] stream status: {status}")
        audio_queue.put(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=device_index,
        blocksize=int(SAMPLE_RATE * CHUNK_SECONDS),
        callback=callback,
    )
    stream.start()
    return stream


if __name__ == "__main__":
    list_devices()
