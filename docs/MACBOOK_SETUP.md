# Circling Back — MacBook Setup & Verification

Hand this file to Claude Code on the **work MacBook** to bring the app up from a
fresh clone and verify the real notch behavior. The app was developed on a Mac
mini (no notch); the MacBook is the true deployment target.

> ⚠️ Capturing meeting audio may violate org policy and other participants don't
> consent to transcription. Everything runs locally (no audio/transcript leaves
> the machine), but use responsibly.

---

## 0. Prerequisites to confirm first

- macOS with a notch (MacBook Pro/Air, 2021+).
- Admin rights (needed for Homebrew installs, audio device creation, and granting
  Accessibility/Input-Monitoring permissions).
- Roughly 5 GB free (Whisper model + Ollama model + Python deps).
- The clone lives somewhere like `~/Documents/corporate-ai-responses`. Adjust
  paths below if it's elsewhere.

---

## 1. System tools (Homebrew)

```bash
# Install Homebrew first if `brew` is missing: https://brew.sh
brew install ffmpeg blackhole-2ch ollama
brew services start ollama
ollama pull llama3.2:3b        # or qwen2.5:7b for wittier output (larger/slower)
```

- `ffmpeg` must be on PATH — `faster-whisper` shells out to it.
- **BlackHole requires a reboot** after install before it shows up as an audio
  device. Reboot now if it's a fresh install.

Verify after reboot:

```bash
ollama list                    # llama3.2:3b should be present
brew services list | grep ollama   # should say "started"
ffmpeg -version | head -1
```

---

## 2. Audio routing — the Multi-Output Device

The goal: the meeting app's output goes to **both** your speakers/headphones (so
you still hear it) **and** BlackHole (so the app can capture it).

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`).
2. Click **+** (bottom-left) → **Create Multi-Output Device**.
3. Tick **BlackHole 2ch** and your normal output (e.g. **MacBook Pro Speakers**
   or your headphones).
4. Set your real output device as the **clock master** (Primary), and tick
   **Drift Correction** on BlackHole.
5. Rename it to **Meeting Capture** (double-click the name).
6. Set it as the **system output**: System Settings → Sound → Output → **Meeting
   Capture**. (Or click the speaker menu-bar icon.)

**Sanity check:** play a YouTube video. With *Meeting Capture* selected you should
still **hear** it. If it's silent, your real speakers aren't ticked or aren't the
clock master in the Multi-Output Device.

> Note: in a real meeting (Zoom/Meet/Teams), this captures the **other people's
> audio** (the app's speaker output), not your mic. That's what you want — you're
> responding to what *they* say.

---

## 3. Python environment

Homebrew Python is externally managed, so a virtualenv is required.

```bash
cd ~/Documents/corporate-ai-responses
python3 -m venv .venv
source .venv/bin/activate        # run this in every new terminal for this project
pip install -r requirements.txt
```

`.venv/` is gitignored; all deps live there. First `python main.py` run will also
download the `faster-whisper` `base.en` model (~150 MB) on first transcription.

---

## 4. Find the BlackHole device index ⚠️ (will differ from the Mac mini)

Device indices are machine-specific. The Mac mini had BlackHole at index 1, but
the MacBook's order will likely differ.

```bash
source .venv/bin/activate
python -m audio.capture
```

Find the line like `N BlackHole 2ch, Core Audio (2 in, 2 out)` and note `N`.
Then set it in `main.py`:

```python
DEVICE_INDEX = N   # whatever index BlackHole 2ch printed as
```

(The capture code reads the device's native sample rate/channels automatically —
BlackHole is 48 kHz/2ch and the app downmixes + resamples to 16 kHz internally, so
only the *index* needs changing.)

---

## 5. macOS permissions (required for global hotkeys)

The hotkeys (`pynput`) fire while another app (the meeting) is focused, which
needs:

1. System Settings → Privacy & Security → **Accessibility** → enable **Terminal**
   (or iTerm / whatever you run the app from).
2. If hotkeys still don't fire, also enable that same app under **Input
   Monitoring**.
3. **Fully quit (`Cmd+Q`) and reopen** the terminal app after granting — the
   permission only takes effect on a fresh launch.

If you later package this as a real `.app` (see project notes), these permissions
must be granted to *that app*, not Terminal.

---

## 6. Run end-to-end

```bash
cd ~/Documents/corporate-ai-responses
source .venv/bin/activate
python main.py
```

Then:
1. Play some audio (YouTube/podcast) through **Meeting Capture** so Whisper has
   speech to transcribe.
2. Wait ~10 s for the rolling transcript to fill (needs ≥ `MIN_TRANSCRIPT_WORDS`,
   default 8).
3. Press **`Ctrl+Shift+G`** → a response streams into the notch overlay.
4. Press **`Ctrl+Shift+C`** → copies the current response to the clipboard.
5. The panel auto-collapses ~12 s after a response finishes. **Hover over it to
   keep it open**; it re-arms the countdown when you move the mouse away.

---

## 7. Notch verification (the whole point of testing on the MacBook)

This is what couldn't be tested on the Mac mini. Confirm:

- [ ] The collapsed sliver sits **flush against / merged into the physical notch**
      (not below it, not offset left/right).
- [ ] On `Ctrl+Shift+G` the panel **drops down from the notch** and is horizontally
      centered under it.
- [ ] The top edge is square and tucks under the notch; the bottom is rounded.
- [ ] It renders **above the menu bar** and stays visible over a fullscreen
      meeting window and across Spaces.
- [ ] Text is readable against the meeting content behind it.

If positioning is wrong, the relevant code is in `ui/overlay.py`:
- `COLLAPSED_W/H`, `EXPANDED_W/H` — sizing (tune notch width/height to this Mac).
- `_raise_to_notch_level()` — raises the native `NSWindow` above the menu bar via
  pyobjc. If this throws, the app falls back to a top-center pill *below* the notch
  and prints `[overlay] notch positioning unavailable, using fallback: ...`. Check
  the terminal for that line — if you see it, the AppKit path failed and that's the
  first thing to fix.
- `_top_y()` / `_reposition()` — vertical placement (0 = screen top in notch mode).

Measure your MacBook's actual notch width in points and set `COLLAPSED_W` to match
for a clean merge.

---

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `segmentation fault` on launch | Audio device mismatch — re-check `DEVICE_INDEX` (§4). The capture rewrite already avoids the PortAudio callback/adapter crashes; if it recurs, read the newest `.ips` in `~/Library/Logs/DiagnosticReports/`. |
| Hotkeys do nothing | Accessibility + Input Monitoring not granted, or terminal not relaunched after granting (§5). |
| `[generate] not enough transcript yet` | Let more audio play, or lower `MIN_TRANSCRIPT_WORDS` in `main.py`. |
| No audio heard with Meeting Capture selected | Real speakers not ticked / not clock master in the Multi-Output Device (§2). |
| Overlay renders below the notch as a pill | AppKit fallback engaged — see the `[overlay] ... fallback` line and §7. |
| `ffmpeg not found` | `brew install ffmpeg`; ensure PATH is picked up in the venv shell. |
| Ollama connection refused | `brew services start ollama`; it serves at `localhost:11434`. |

---

## Tuning knobs (all in code)

- **Persona / cringe level:** `SYSTEM_PROMPT` in `llm/prompt.py`
- **Model / wit:** `MODEL` in `llm/responder.py` (`llama3.2:3b` → `qwen2.5:7b`)
- **Trigger sensitivity:** `MIN_TRANSCRIPT_WORDS` in `main.py`
- **Transcript window length:** `maxlen` of the deque in `transcription/whisper_engine.py`
- **Notch sizing / auto-collapse:** constants at the top of `ui/overlay.py`
  (`COLLAPSED_*`, `EXPANDED_*`, `AUTO_COLLAPSE_MS`)
