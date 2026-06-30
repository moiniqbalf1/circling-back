"""Entry point — wires capture -> transcription -> (hotkey) -> LLM -> overlay.

Transcription runs continuously in the background, keeping a rolling transcript.
Nothing is sent to the model until you press the generate hotkey.

Hotkeys (global, need Accessibility permission on macOS):
  Ctrl+Shift+G  generate a response for the current transcript
  Ctrl+Shift+C  copy the current response to the clipboard

Find DEVICE_INDEX first:  python -m audio.capture
"""

import sys
import threading

from PyQt6.QtWidgets import QApplication
from pynput import keyboard

from audio.capture import start_capture, audio_queue
from transcription.whisper_engine import transcribe_chunk, get_context
from llm.responder import stream_response
from ui.overlay import OverlayWindow

# Index of the BlackHole input. Run `python -m audio.capture` to find yours.
DEVICE_INDEX = 0

# Don't fire on tiny utterances like "yeah" / "right".
MIN_TRANSCRIPT_WORDS = 8

# Guards against overlapping generations while one is in flight.
_generating = threading.Lock()


def transcription_loop():
    """Continuously drain the audio queue into the rolling transcript."""
    while True:
        chunk = audio_queue.get()
        try:
            transcribe_chunk(chunk)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            print(f"[transcription] error: {exc}")


def generate(overlay: OverlayWindow):
    """Run one generation pass; called on the hotkey thread."""
    if not _generating.acquire(blocking=False):
        return  # a response is already streaming
    try:
        context = get_context()
        if len(context.split()) < MIN_TRANSCRIPT_WORDS:
            print("[generate] not enough transcript yet")
            return
        overlay.sig_start.emit()
        stream_response(context, on_token=overlay.token_received.emit)
        overlay.sig_finish.emit()
    except Exception as exc:  # noqa: BLE001
        print(f"[generate] error: {exc}")
        overlay.sig_finish.emit()
    finally:
        _generating.release()


def start_hotkeys(overlay: OverlayWindow):
    """Start the global hotkey listener (runs in its own thread)."""
    def on_generate():
        # Run generation off the hotkey thread so it isn't blocked.
        threading.Thread(target=generate, args=(overlay,), daemon=True).start()

    def on_copy():
        overlay.sig_copy.emit()

    listener = keyboard.GlobalHotKeys({
        "<ctrl>+<shift>+g": on_generate,
        "<ctrl>+<shift>+c": on_copy,
    })
    listener.start()
    return listener


def main():
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()

    try:
        start_capture(DEVICE_INDEX)
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] could not open device {DEVICE_INDEX}: {exc}")
        print("Run `python -m audio.capture` to list devices and set DEVICE_INDEX.")

    threading.Thread(target=transcription_loop, daemon=True).start()
    start_hotkeys(overlay)

    print("Ready. Ctrl+Shift+G to generate, Ctrl+Shift+C to copy.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
