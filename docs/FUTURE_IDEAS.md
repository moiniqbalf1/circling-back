# Circling Back — Future Scalability & Ideas

Parking lot for larger directions beyond the working local app. Nothing here is
committed work — these are scoped notes for "if/when I pick this up."

---

## 1. Package as a downloadable macOS app

**Goal:** remove the "open Terminal, activate venv, `python main.py`" friction so
the app can be launched (and shared) like a normal `.app`.

**The catch — it's not self-contained.** Three hard external dependencies can't be
bundled inside an app:
- **BlackHole** — kernel-level audio driver; needs its own install **+ reboot**.
- **Ollama + a multi-GB model** — the local LLM runtime and weights.
- **ffmpeg** — `faster-whisper` shells out to it.

So even a packaged app realistically needs a setup wizard or a Homebrew bootstrap
for those pieces. The Python side itself bundles fine.

**Pragmatic ladder (likely stop at rung 2 for a side project):**
1. **`.app` via PyInstaller / py2app** — wrap Python + deps into
   `Circling Back.app`. Removes the Terminal/venv dance. Bonus: macOS permissions
   (Accessibility / Input Monitoring) then attach to *this app* instead of
   Terminal, which is cleaner. ~an afternoon.
2. **`.app` + `setup.sh`** that `brew install`s BlackHole/Ollama/ffmpeg and pulls
   the model. The realistic "shippable to a friend" tier.
3. **Signed + notarized `.dmg`** — needed only for distribution to others without
   Gatekeeper warnings. Requires a **paid Apple Developer account ($99/yr)** and
   codesigning. Skip unless actually distributing.

**Recommendation:** PyInstaller `.app` + `setup.sh`, unsigned, documented as "for
personal use — right-click → Open to bypass Gatekeeper." Matches the side-project
scope without the notarization tax.

**First steps when picked up:** add a PyInstaller spec (entry `main.py`, include
`audio/`, `transcription/`, `llm/`, `ui/`, and pyobjc/PyQt6 hidden imports), plus a
`setup.sh` for the system deps. Verify Accessibility/Input-Monitoring prompts fire
against the bundled app, not Terminal.

---

## 2. Interactive web demo (Next.js + Vercel)

**Goal:** let someone open the personal-site page, click "Enable audio," and try a
live version of the app in the browser. Pairs well with the planned project
writeup.

**Key constraint:** this must be a **reimplementation**, not the Python app running
in a browser. None of BlackHole / Ollama / faster-whisper / pynput run client-side.
The browser has native equivalents for a self-contained demo:

| Local app piece | Browser equivalent |
|---|---|
| BlackHole capture | `navigator.mediaDevices.getUserMedia` (mic) or `getDisplayMedia` (tab audio) — user grants permission via an "Enable audio" button |
| faster-whisper (STT) | **Web Speech API** (`SpeechRecognition`) for v1 (easiest); or `whisper.cpp` / Transformers.js via WASM for fully-local, heavier |
| Ollama (LLM) | A serverless **Vercel API route** streaming from a hosted model — natural fit for the **Claude API** (strong at the persona, nothing to ship). Stream tokens via SSE. |
| Notch overlay (PyQt6) | A CSS/React notch-styled component pinned top-center, rendering the streamed text |

**Architecture:** client captures mic → transcribes (Web Speech API for v1) → on a
"Circle Back" button, POST the transcript to a Vercel API route → route streams a
persona response from Claude (reuse the spirit of `llm/prompt.py`'s
`SYSTEM_PROMPT`) → React notch component renders the stream.

**Things to handle:**
- **Privacy disclaimer.** Unlike the local app, a serverless route means the demo
  transcript *leaves the browser*. Say so in one line on the page.
- **Rate limiting** on the API route so a public demo can't run up the API bill
  (per-IP cap / simple token bucket).
- **Browser support.** Web Speech API support varies (best in Chrome); have a
  graceful fallback message, or let the user type a sample transcript.

**First steps when picked up:** stub a Next.js API route (`/api/circle-back`) that
streams from Claude with the persona system prompt, plus a `Notch` React component
and a mic-capture hook. Build the typed-transcript path first (no audio), then add
speech capture.
