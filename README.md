# Caption Studio

Turn any Urdu poetry audio into a styled caption video: the words are
transcribed with exact timings, then drawn as layered kinetic typography —
big Roman caps with gold Nastaliq calligraphy woven over them, building
word by word with the voice, on a dark maroon canvas with drifting dust
particles. The style replicates the Urdu poetry edits popular on Reels.

## What you need

- **Python 3.10+** — https://www.python.org/downloads/
  (Windows: tick **"Add python.exe to PATH"** while installing)
- **ffmpeg** — Windows: `winget install ffmpeg`, or download from
  https://www.gyan.dev/ffmpeg/builds/ · macOS: `brew install ffmpeg` ·
  Ubuntu: `sudo apt install ffmpeg`
- No internet needed for the **Large** speech model: it is bundled inside
  this package (`models/` folder, ≈1.6 GB) and loads locally. Only the
  optional **Small** model downloads once (~0.5 GB) if you select it.

## Install (one time)

- **Windows:** double-click `install.bat`
- **macOS / Linux:** `bash install.sh`

## Use

- **Windows:** double-click `run.bat`
- **macOS / Linux:** `./run.sh`

1. **Browse...** and pick an audio (mp3/wav/m4a) or video file.
2. Optional: type your **watermark handle** (shown top-left).
3. Pick a **style preset** (see below), a **background** (the preset's own,
   a flat color, or your own photo), **format** — 16:9, 9:16 vertical
   (Reels/Shorts/TikTok), 4:5 portrait, 1:1 square, or 4:3 — and
   **speech model** (Large = accurate, Small = fast).
4. Click **Create Video**. The finished MP4 appears in a new folder next
   to your file, named `<yourfile>-caption`, together with
   `transcript.json` and `plan.json`.

## Style presets

Each preset changes the caption-mode mix, the text colors and the
background together, so every video can look different:

- **Classic Herr** — the original: red + gold stacks and line pairs on maroon.
- **Mystic Gold** — gold-dominant, calmer, with Urdu-only breathing lines.
- **Crimson Stage** — loud and dramatic: bright red stacks, giant words.
- **Poet's Lines** — elegant: every phrase as a full poetic line pair.
- **Giant Words** — poster energy: short phrases explode into giant words.
- **Interlude Calm** — spacious gold Urdu-only lines on espresso brown.
- **Ivory & Gold** — ivory-white Roman type + gold calligraphy on charcoal.
- **Marquee Mix** — variety pack: artsy stacks mixed with clean subtitles.
- **Midnight Mono** — moody silver-gold and white on near-black.
- **Royal Maroon** — rich plum-maroon, brighter gold, deeper red.

Tip: keep "Background: Preset default" to use each preset's own canvas,
or override it with any color/photo — the preset's caption style stays.

## Fixing a word

Automatic transcription and Roman transliteration are very good but not
perfect. To correct anything:

1. Open `plan.json` in the output folder (any text editor).
2. Fix the Urdu (`ur`), Roman (`ro`) or the style (`mode`) of any phrase.
   Modes: `stack_gold`, `stack_red`, `line_pair`, `urdu_only`, `giant`, `plain`.
3. Re-render without re-transcribing:
   `python render.py plan.json <your-audio> <output.mp4>` from this folder.

## Command line (optional)

```
python caption_studio.py song.mp3 --brand yourhandle -o out.mp4
python caption_studio.py song.mp3 --preset "Crimson Stage" -o out.mp4
python caption_studio.py song.mp3 --format 9:16 -o out.mp4   # vertical reel
python caption_studio.py song.mp3 --plan-only        # stop after plan.json
```

## Notes

- Everything runs locally on your computer; audio never leaves the machine.
- Urdu text is shaped by the app itself (HarfBuzz), so it renders
  correctly on any system — the app does not depend on your Pillow build
  having the optional "raqm" component. The log line at the start of each
  run ("Text engine: ...") shows which engine was used.
- Speed: transcription runs at roughly real-time on CPU; rendering a
  1-minute video takes under a minute.
- Fonts bundled under the SIL Open Font License (Anton, Noto Nastaliq Urdu,
  Noto Sans). Speech recognition: OpenAI Whisper via faster-whisper (MIT).
