# Creative Brief — "Circling Back" website section

Hand this to Claude (chat or a design tool) to generate the visuals + looped
demo for the project section on my personal site. Self-contained: includes the
copy, layout, style, and a shot-by-shot storyboard.

---

## What this is

*Circling Back* is a macOS app that listens to a meeting and, on a hotkey,
generates a response in the voice of an early, over-validated AI assistant
("Absolutely, that's a really important point to surface…") and streams it into
the MacBook notch. It's a satirical jape about the texture of AI corporate-speak.
Everything runs locally. See the blurb below for the on-page copy.

## Deliverables

1. A **looped video/GIF** (~6–8s, seamless loop) demoing the core moment.
2. Optionally a **static hero image** for fallback / social preview.

## On-page copy (already written — render alongside the media)

> **Circling Back**
>
> We've all sat in a meeting where someone says a lot of words and contributes
> nothing. *Circling Back* automates that.
>
> It's a macOS app that quietly listens to a meeting, and on a hotkey, generates a
> response in the unmistakable voice of an early, over-validated AI assistant —
> *"Absolutely, that's a really important point to surface…"* — then streams it
> into the MacBook notch, ready to read aloud or copy.
>
> Everything runs locally: audio capture through a virtual device, on-device
> transcription with Whisper, and a local LLM for the responses. No audio or
> transcript ever leaves the machine.
>
> It's a jape about the texture of AI-generated corporate-speak — confident,
> polished, and saying absolutely nothing. An interactive in-browser version is
> coming soon.

## Section layout (desktop)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌──────────────────┐    Circling Back                     │
│   │                  │    We've all sat in a meeting where  │
│   │   LOOPED DEMO    │    someone says a lot of words and   │
│   │   (notch app     │    contributes nothing. Circling     │
│   │    in action)    │    Back automates that. …            │
│   │                  │                                       │
│   └──────────────────┘    [ Local-first ] [ macOS ] [ Whisper ] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Two-column on desktop (media left, copy right — or swap), single column stacked
  on mobile (media on top).
- Small pill tags under the copy: `Local-first` · `macOS` · `Whisper` · `Local LLM`.

## Visual style

- **Aesthetic:** clean, modern, Apple-adjacent. Dark UI to make the black notch
  panel feel native.
- **Subject device:** a MacBook Pro with a visible **notch** at the top-center of
  the display. The app is a black rounded panel that drops *down from the notch*.
- **Palette:** near-black panel (#000 ~92% opacity), off-white text (#F2F2F2),
  muted grey secondary text (#8A8A8A). Mute everything else so the notch panel is
  the hero.
- **Type:** system/SF-style sans for the UI; the streamed reply in a clean
  readable weight.
- **Mood:** deadpan, polished, faintly absurd — the comedy is in the contrast
  between the slick UI and the hollow words.

## Looped video — storyboard (~6–8s)

Goal: capture the satisfying beat — a real meeting line going in, hollow AI slop
streaming out of the notch. The token-by-token reveal is the payoff; don't cut to
a static end state.

| t | Shot |
|---|---|
| 0.0s | MacBook display, notch idle — a thin black sliver merged into the notch. A subtle caption/subtitle shows a meeting line being spoken, e.g. *"…so the migration broke prod again and customers are complaining."* |
| 1.5s | A keystroke cue appears — `⌃⇧G` ("Ctrl+Shift+G") — the trigger. |
| 2.0s | The notch panel **drops down** and expands; a quiet "Generating…" label. |
| 2.5–6.5s | The reply **streams in word-by-word** in the panel: *"It's not just the API that broke — it's really about how we de-risk our production ecosystem holistically. Happy to unpack that further!"* |
| 6.5–7.5s | Brief hold on the full reply, then panel **collapses back** into the notch — loop seamlessly to the idle start. |

Make the loop seamless: end frame should match the opening idle notch.

## Specs

- **Aspect ratio:** 16:9 or 16:10 (match a MacBook screen); also export a square
  1:1 crop for social.
- **Duration:** 6–8s, looping. Keep file size web-friendly (MP4/H.264 + WebM, or
  optimized GIF as fallback).
- **No audio required** (it autoplays muted on the web) — convey the spoken line
  via an on-screen subtitle.
- Resolution: target 1920×1080 source, can downscale for delivery.

## Sample reply lines to feature (pick the funniest)

- "It's not just the API that broke — it's really about how we de-risk our
  production ecosystem holistically. Happy to unpack that further!"
- "Great point to raise, and you're right to push back. While the data is still
  maturing, I'd gently reframe this as an opportunity to learn and grow. Let me
  know if it'd be helpful to socialize a framework going forward."
- "Totally hear you — net-net, this is less a deadline question and more a signal
  of how we leverage our bandwidth. Happy to circle back at a high level!"

## Notes for the generator

- The humor must read instantly: slick, confident UI + words that say nothing.
- Keep the notch panel the focal point; don't clutter the frame.
- If generating a static image instead of video, capture the mid-stream moment
  (panel open, reply partially rendered) — it implies motion.
