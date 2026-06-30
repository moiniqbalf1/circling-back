# Circling Back App — Project Briefing

A fun side project: a desktop app that listens to a work meeting and, on a
hotkey, generates a response in the style of an early, overly-validated LLM —
think *"Absolutely, that's a really important point to surface..."* — and streams
it into the MacBook notch. Subtle enough to be plausible, obvious to anyone who
has used an LLM before.

> Side project / jape. Capturing meeting audio may be against an org's policy and
> other participants don't consent to transcription — use responsibly. Everything
> runs locally precisely so no audio or transcript ever leaves the machine.

---

## Current status (resume point)

The app is **built and nearly set up**. The reboot is done; BlackHole is live and
audio routing is configured. Only one setup step remains (Accessibility) before
the first end-to-end run.

| Piece | Status |
|---|---|
| Local LLM (Ollama + `llama3.2:3b`) | ✅ built + verified (`python -m llm.responder`) |
| Notch overlay UI | ✅ built + verified (`python -m ui.overlay`) |
| Whisper transcription | ✅ built, installed, untested (needs audio) |
| Audio capture (BlackHole) | ✅ reboot done — BlackHole 2ch is **device index 1**; `DEVICE_INDEX = 1` set in `main.py` |
| Multi-Output Device | ✅ created as **"Meeting Capture"** (BlackHole + speakers), set as system output |
| Global hotkeys (Accessibility) | ⏳ Terminal still needs Accessibility permission granted |
| Full wiring (`main.py`) | ⏳ built, not yet run end-to-end |

**Resume point — do this next:**
1. System Settings → Privacy & Security → **Accessibility** → enable **Terminal**,
   then **fully quit (`Cmd+Q`) and reopen Terminal** so it takes effect.
   (If hotkeys still don't fire, also enable Terminal under **Input Monitoring**.)
2. `cd ~/Documents/corporate-ai-responses && source .venv/bin/activate`
3. Play some audio (YouTube/podcast) so it routes through **Meeting Capture** → BlackHole.
4. `python main.py` → wait a few seconds for the transcript to fill (needs ≥8 words)
   → `Ctrl+Shift+G` to generate, `Ctrl+Shift+C` to copy.

Audio sanity check: with "Meeting Capture" selected you should still **hear** the
audio. If it's silent, make sure Mac mini Speakers is ticked in the Multi-Output
Device and is the clock master (BlackHole has drift correction on).

Dev machine is a **Mac mini** (no notch — overlay falls back to a top-center
panel). The real deployment target is a **work MacBook**, where the true notch
behavior should be verified before the UI is considered done.

A project writeup + screenshots for a personal website are planned for later.

---

## How it works

```
meeting audio
      │  routed via a macOS Multi-Output Device
      ▼
BlackHole (virtual audio device)
      │
      ▼
audio/capture.py ── 5s @ 16kHz mono chunks → audio_queue
      │
      ▼
transcription/whisper_engine.py ── faster-whisper (LOCAL), rolling transcript buffer
      │
      │   ⌨️  Ctrl+Shift+G  (manual trigger — nothing fires until pressed)
      ▼
llm/responder.py ── streams from local Ollama (llama3.2:3b)
      │
      ▼
ui/overlay.py ── notch overlay streams the text; Ctrl+Shift+C copies it
```

**Design decisions made:**
- **Fully local.** No cloud, no API key. Replaced the original Anthropic API plan
  with Ollama. Raw audio + transcript never leave the Mac.
- **Manual hotkey trigger** (not auto-fire). Transcription runs continuously; the
  model is only called when you press `Ctrl+Shift+G`. Controllable in a meeting,
  no constant work/calls.
- **Notch UI** via PyQt6 + pyobjc (raise the `NSWindow` level above the menu bar
  to overlap the notch), with an automatic fallback to a top-center pill if the
  AppKit positioning fails.
- **`pynput`** for global hotkeys instead of the `keyboard` lib (which needs sudo
  on macOS).

---

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Audio capture | `sounddevice` + **BlackHole** | Multi-Output Device so you still hear the call |
| STT | `faster-whisper` (`base.en`, int8, CPU) | Local; needs `ffmpeg` on PATH |
| LLM | **Ollama** `llama3.2:3b` | Local HTTP at `localhost:11434`; bump to `qwen2.5:7b` for wittier output |
| UI | `PyQt6` + `pyobjc-framework-Cocoa` | Frameless translucent notch overlay |
| Hotkeys | `pynput` | Needs macOS Accessibility permission |
| Clipboard | `pyperclip` | |

---

## Project structure

```
circling-back/
├── CLAUDE.md                  ← this file
├── README.md                  ← setup + run guide
├── requirements.txt
├── .gitignore
├── main.py                    ← wires capture → transcribe (bg) + hotkeys → LLM → overlay
├── audio/
│   └── capture.py             ← BlackHole loopback capture → audio_queue
├── transcription/
│   └── whisper_engine.py      ← faster-whisper wrapper + rolling transcript buffer
├── llm/
│   ├── prompt.py              ← persona system prompt (SYSTEM_PROMPT + build_prompt)
│   └── responder.py           ← streams from local Ollama (MODEL = "llama3.2:3b")
└── ui/
    └── overlay.py             ← PyQt6 notch overlay (Option B) + top-center fallback
```

(Note: the original spec had an `audio/vad.py` — dropped, since Whisper's built-in
`vad_filter=True` handles silence suppression.)

---

## Environment setup (already done on the Mac mini)

System tools (Homebrew):
```bash
brew install ffmpeg blackhole-2ch ollama
brew services start ollama
ollama pull llama3.2:3b
```

Python (a **virtualenv** is required — Homebrew Python is externally managed):
```bash
cd ~/Documents/corporate-ai-responses
python3 -m venv .venv
source .venv/bin/activate          # run this in every new terminal for this project
pip install -r requirements.txt
```
The `.venv/` is gitignored. All Python deps live there, not globally.

---

## Hotkeys

| Key | Action |
|---|---|
| `Ctrl+Shift+G` | Generate a response for the current transcript |
| `Ctrl+Shift+C` | Copy the current response to the clipboard |

---

## Tuning knobs

- **Persona / cringe level:** `SYSTEM_PROMPT` in `llm/prompt.py`
- **Model / wit:** `MODEL` in `llm/responder.py` (`llama3.2:3b` → `qwen2.5:7b`)
- **Trigger sensitivity:** `MIN_TRANSCRIPT_WORDS` in `main.py`
- **Transcript window length:** `maxlen` of the deque in `transcription/whisper_engine.py`
- **Notch sizing / auto-collapse:** constants at the top of `ui/overlay.py`
- **Response variety:** Ollama can be deterministic by default; add a random seed
  per call in `responder.py` if identical inputs should vary.

---

## Known friction points

- **Device index:** BlackHole 2ch is currently **index 1** and `DEVICE_INDEX = 1`
  is set in `main.py`. Re-check with `python -m audio.capture` if devices change.
- **Audio capture segfault (fixed) — two causes, both in `audio/capture.py`:**
  1. *No PortAudio callback under Qt.* A `sounddevice` callback fires on
     CoreAudio's realtime thread; running Python there while Qt drives the main
     thread segfaults (GIL / autorelease-pool clash — crash shows up in
     `ffi_closure_SYSV` → `AdaptingInputOnlyProcess`). We now drain the stream
     with blocking `stream.read()` in a normal background thread, so no Python
     runs on the audio thread. An `atexit` handler stops that thread before
     closing the stream (closing while a read is in flight also segfaults).
  2. *Native rate/channels, resample in Python.* BlackHole is **48 kHz / 2ch**
     but Whisper wants 16 kHz mono — we open at the native rate/channels and
     downmix + decimate ourselves rather than letting PortAudio convert.
  The MacBook's BlackHole is also 48 kHz, so keep both. Diagnose any recurrence
  from the crash `.ips` in `~/Library/Logs/DiagnosticReports/`.
- **BlackHole needs a reboot** after install before it appears as a device — done.
- **Accessibility permission** is required for the global hotkeys to fire while
  another app (the meeting) is focused — Terminal still needs this granted, then a
  full quit/reopen. May also need Terminal under **Input Monitoring**.
- **Mac mini has no notch** — the overlay renders as a top-center panel there;
  test true notch fit on the MacBook.
- **Testing without a real meeting:** play any audio (YouTube, podcast) through the
  Multi-Output Device so Whisper has something to transcribe.
