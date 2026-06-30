"""Audio capture from a loopback device (BlackHole on macOS).

The meeting app's output is routed through a virtual audio device so we can read
it without touching the microphone. On macOS that device is BlackHole; create a
Multi-Output Device (BlackHole + speakers) in Audio MIDI Setup and set it as the
system output so you still hear the call while it's being captured.

Run ``list_devices()`` once to find the index of the BlackHole input, then pass
it to ``start_capture()``.
"""

import atexit
import threading

import numpy as np
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
    """Open a loopback input stream on ``device_index`` and drain it in a thread.

    Two macOS-specific choices here, both to avoid CoreAudio segfaults:

    * **No PortAudio callback.** A callback fires on CoreAudio's realtime thread;
      invoking Python there while Qt drives the main thread segfaults (GIL /
      autorelease-pool clash). Instead a normal Python thread drains the stream
      with blocking ``stream.read()`` — no Python ever runs on the audio thread.
    * **Native rate/channels, resample in Python.** We open at the device's own
      rate/channels (48 kHz/2ch for BlackHole) and downmix + decimate to
      ``SAMPLE_RATE`` ourselves, rather than letting PortAudio's adapter convert.

    Pushes mono float32 chunks (~CHUNK_SECONDS long, at SAMPLE_RATE) onto
    ``audio_queue``. Returns the running stream so the caller can stop it.
    """
    info = sd.query_devices(device_index)
    capture_rate = int(info["default_samplerate"])           # e.g. 48000 for BlackHole
    capture_channels = max(1, int(info["max_input_channels"]))
    decim = max(1, round(capture_rate / SAMPLE_RATE))         # 48000/16000 -> 3
    # Read in short blocks (~0.5s, a whole number of decimation groups) so a stop
    # signal is acted on promptly; accumulate until we have a full chunk.
    read_frames = max(decim, (capture_rate // 2 // decim) * decim)
    target = SAMPLE_RATE * CHUNK_SECONDS                     # output samples per chunk

    stream = sd.InputStream(
        samplerate=capture_rate,
        channels=capture_channels,
        dtype="float32",
        device=device_index,
        blocksize=0,                                          # native host buffer
    )
    stream.start()

    stop_event = threading.Event()

    def reader():
        pending: "list[np.ndarray]" = []
        have = 0
        while not stop_event.is_set():
            try:
                data, overflowed = stream.read(read_frames)
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                print(f"[capture] read error: {exc}")
                continue
            if overflowed:
                # Dropped frames are non-fatal; keep capturing.
                print("[capture] input overflow")
            mono = data.mean(axis=1)                          # downmix to mono
            # Averaging consecutive samples is a crude anti-alias low-pass before
            # decimating capture_rate -> SAMPLE_RATE; good enough for speech.
            down = mono.reshape(-1, decim).mean(axis=1).astype(np.float32)
            pending.append(down)
            have += len(down)
            while have >= target:
                combined = np.concatenate(pending)
                audio_queue.put(combined[:target].copy())
                rest = combined[target:]
                pending = [rest] if len(rest) else []
                have = len(rest)

    thread = threading.Thread(target=reader, daemon=True, name="audio-reader")
    thread.start()

    def _shutdown():
        # Stop the reader before closing the stream — calling read() on a
        # closing PortAudio stream segfaults on macOS.
        stop_event.set()
        thread.join(timeout=2)
        try:
            stream.stop()
            stream.close()
        except Exception:  # noqa: BLE001 - best effort during teardown
            pass

    atexit.register(_shutdown)
    return stream


if __name__ == "__main__":
    list_devices()
