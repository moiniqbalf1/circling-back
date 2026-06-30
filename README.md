# Circling Back

A workplace jape: listens to your meeting, transcribes it locally, and on a
hotkey generates an early-LLM-style corporate-jargon reply that streams into the
MacBook notch.

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

## Requirements

- macOS (MacBook with a notch recommended; falls back to a top-center pill otherwise)
- [Homebrew](https://brew.sh)
- ~5 GB free disk space

---

## One-time setup

### 1. Install system dependencies

```bash
brew install ffmpeg blackhole-2ch ollama
```

**Reboot after this step.** BlackHole won't appear as an audio device until you do.

### 2. Start Ollama and pull the model

```bash
brew services start ollama
ollama pull llama3.2:3b
```

First `pull` is ~2 GB, one-time only. Prefer wittier output? Use `qwen2.5:7b`
instead, then set `MODEL = "qwen2.5:7b"` in `llm/responder.py`.

### 3. Create a Python virtualenv and install deps

Homebrew Python is externally managed, so a virtualenv is required.

```bash
cd ~/Documents/circling-back
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first run will also download the Whisper `base.en` model (~150 MB).

### 4. Route meeting audio through BlackHole

The goal: meeting audio goes to your speakers (so you hear it) *and* BlackHole
(so the app captures it).

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`).
2. Click **+** → **Create Multi-Output Device**.
3. Tick **BlackHole 2ch** and your normal output (MacBook Pro Speakers or headphones).
4. Set your real speakers as the **clock master**; tick **Drift Correction** on BlackHole.
5. Rename the device (e.g. **Meeting Capture**).
6. Go to System Settings → Sound → Output → select your new Multi-Output Device.

Sanity check: play a YouTube video — you should still hear it. If not, your real
speakers aren't ticked or aren't the clock master.

### 5. Find the BlackHole device index

Device indices are machine-specific.

```bash
source .venv/bin/activate
python -m audio.capture
```

Find the line with `BlackHole 2ch` and note its number. Then open `main.py` and set:

```python
DEVICE_INDEX = <that number>
```

### 6. Grant Accessibility permission

System Settings → Privacy & Security → **Accessibility** → enable your terminal app.

This is required for the global hotkeys to fire while another app (the meeting) is focused.

**Fully quit (`Cmd+Q`) and reopen your terminal after granting** — the permission
only takes effect on a fresh launch.

---

## Running the app

Each time you want to use it:

```bash
cd ~/Documents/circling-back
source .venv/bin/activate
python main.py
```

Make sure your Multi-Output Device is set as system output, then play audio (a
call, YouTube, podcast — anything) so Whisper has speech to transcribe. After
~10 seconds, start pressing hotkeys.

### Hotkeys

| Key | Action |
|---|---|
| `Ctrl+Shift+G` | Generate a response for what's been said |
| `Ctrl+Shift+C` | Copy the current response to the clipboard |

The notch stays an invisible sliver until you press generate; it drops down,
streams the reply, and auto-collapses after a few seconds. Hover over it to keep
it open while you read.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `DEVICE_INDEX` error / segfault on launch | Re-run `python -m audio.capture` and update the index in `main.py` |
| Hotkeys do nothing | Re-check Accessibility permission; quit and reopen terminal after granting |
| `[generate] not enough transcript yet` | Let more audio play, or lower `MIN_TRANSCRIPT_WORDS` in `main.py` |
| No audio heard with Multi-Output Device selected | Real speakers not ticked or not clock master in Audio MIDI Setup |
| Overlay renders as a pill below the notch | AppKit fallback engaged — check terminal for `[overlay] ... fallback` |
| `ffmpeg not found` | `brew install ffmpeg`; make sure venv is activated |
| Ollama connection refused | `brew services start ollama` |

---

## Testing pieces in isolation

```bash
python -m audio.capture       # list audio devices
python -m llm.responder       # stream a sample response from the local model
python -m ui.overlay          # demo the notch overlay with dummy text
```

## Tuning

- **Persona / cringe level:** `SYSTEM_PROMPT` in `llm/prompt.py`
- **Model / wit:** `MODEL` in `llm/responder.py`
- **Trigger sensitivity:** `MIN_TRANSCRIPT_WORDS` in `main.py`
- **Transcript window:** `maxlen` of the deque in `transcription/whisper_engine.py`
- **Notch sizing / auto-collapse:** constants at the top of `ui/overlay.py`
