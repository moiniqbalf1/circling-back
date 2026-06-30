# Circling Back App

A workplace jape: it listens to a meeting, transcribes it locally, and on a
hotkey generates an early-LLM-style corporate-jargon reply that streams into the
**MacBook notch**.

**Fully local.** Audio capture, Whisper transcription, and the LLM all run on
your Mac — no cloud, no API key, no per-use cost, nothing leaves the machine.

```
meeting audio → BlackHole → Whisper (local) → rolling transcript
                                                   │  Ctrl+Shift+G
                                                   ▼
                                       Ollama (local llama3.2:3b)
                                                   │
                                                   ▼
                                         notch overlay (streams text)
```

> ⚠️ Capturing meeting audio may be against your org's policy, and other
> participants haven't consented to being transcribed. Use responsibly.

---

## Setup

### 1. System dependencies
```bash
brew install ffmpeg blackhole-2ch ollama
```

### 2. Local model
```bash
ollama serve            # starts the local server on http://localhost:11434
ollama pull llama3.2:3b # ~2 GB, one-time download
```
Prefer wittier output? `ollama pull qwen2.5:7b` and set `MODEL = "qwen2.5:7b"`
in `llm/responder.py`.

### 3. Python deps
```bash
pip install -r requirements.txt
```

### 4. Route meeting audio through BlackHole
Open **Audio MIDI Setup** → create a **Multi-Output Device** combining
*BlackHole 2ch* + your speakers → set it as the system output (and as the
meeting app's speaker). Now you still hear the call while it's captured.

### 5. macOS permissions
System Settings → Privacy & Security → **Accessibility** → enable your terminal
(or Python). Required for the global hotkeys to work while another app is focused.

---

## Run

Find your BlackHole input index, set it, then launch:
```bash
python -m audio.capture          # note the "BlackHole 2ch" index
# edit DEVICE_INDEX in main.py to that number
python main.py
```

### Hotkeys
| Key | Action |
|---|---|
| `Ctrl+Shift+G` | Generate a response for what's been said |
| `Ctrl+Shift+C` | Copy the current response to the clipboard |

The notch stays an invisible black sliver until you press generate; it then
drops down, streams the reply, and auto-collapses after a few seconds.

---

## Testing pieces in isolation
```bash
python -m audio.capture          # list audio devices
python -m llm.responder          # stream a sample response from the local model
python -m ui.overlay             # demo the notch overlay with dummy text
```

## Tuning
- **Trigger sensitivity:** `MIN_TRANSCRIPT_WORDS` in `main.py`.
- **Transcript window:** `maxlen` of the deque in `transcription/whisper_engine.py`.
- **Model / wit:** `MODEL` in `llm/responder.py`.
- **Persona:** edit `SYSTEM_PROMPT` in `llm/prompt.py`.
- **Notch sizing / auto-collapse:** constants at the top of `ui/overlay.py`.

If the overlay can't position itself above the menu bar (rare), it automatically
falls back to a pill just below the notch.
