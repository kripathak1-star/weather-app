# Vantara AI — 30 s vertical ad

A procedurally generated 30-second, 9:16 commercial for **Vantara AI** (vantaraai.dev).
It renders at 2160×3840, 60 fps, with an AI voiceover, a synthesized electronic score,
synced sound effects and word-by-word animated subtitles.

## Output

`./build.sh` writes:

| File | Spec |
|---|---|
| `out/VantaraAI_Ad_4K60_9x16.mp4` | 2160×3840, 60 fps, H.264 High, BT.709, AAC 320 kbps |
| `out/VantaraAI_Ad_1080p60_9x16.mp4` | 1080×1920 review/share copy |

## Pipeline

| Step | File | What it does |
|---|---|---|
| 1 | `make_voice.py` | Kokoro neural TTS (`am_michael`, young US-English male, 1.12× speed) → `build/line_*.wav` |
| 2 | `vo.py` | Places each line on the timeline and estimates word timings from pauses and syllables → `build/words.json` |
| 3 | `audio.py` | 120 BPM A-minor score (kick, clap, hats, sub bass, supersaw pads, pluck arp), plus risers, impacts, whooshes, shimmer, clicks and glitches. Music is lowered ~14 dB under each spoken line. Mix measures ≈ −15 LUFS. |
| 4 | `render.py` | Frame-by-frame compositor (NumPy/OpenCV/Pillow) → `build/video.mp4` |
| 5 | `build.sh` | Muxes the picture and mix, and makes the 1080p copy |

`timeline.py` holds every shared cue time, so picture, music and SFX stay locked to the beat.

Preview stills quickly with `VSCALE=0.5 python3 render.py --preview 1.0,6.5,12,20,27`.

## Scenes

1. **0–5 s, hook.** "STOP SCROLLING!" slams in as elastic, extruded 3D text over a moving neon grid.
   Camera shake, RGB split, spark bursts, then an exponential velocity zoom with radial blur and a flash cut.
2. **5–10 s, reveal.** Neon energy trails spiral in, a particle explosion fires, and the emblem rotates in 3D.
   Orbiting light trails circle it, the "VANTARA AI" letters stagger in, and a liquid-morph transition follows.
3. **10–18 s, website.** A glassmorphism 3D browser shows `vantaraai.dev`, with parallax side windows.
   The page scrolls smoothly; a cursor tracked through the 3D projection clicks, with ripples and glowing highlights.
   Whip-pan velocity transitions separate the shots, with kinetic headlines DISCOVER / EXPLORE / SEE WHAT AI CAN DO.
4. **18–25 s, high-energy edit.** Kinetic typography locked to each spoken word: slam, rise, 3D flip,
   slide-in, whip-out and zoom-through. A beat-pulsing neon tunnel, warp streaks and neon line sweeps
   run behind it, then a rotating 3D wordmark and a riser speed ramp.
5. **25–30 s, CTA.** A blue energy shockwave with refractive distortion leads into the emblem and wordmark reveal.
   "YOUR AI JOURNEY STARTS HERE" wipes in, followed by a glowing `vantaraai.dev` pill with a light sweep and a slow push-in.

There are only three flashes, at 0 s, 5 s and 25 s. Each is capped at 50% intensity and lasts under 0.25 s.

## Swapping in real assets

Drop files into `assets/` and re-run `./build.sh` (use `SKIP_TTS=1` to keep the current voice):

- `assets/vo_0.wav` … `assets/vo_4.wav`: your own recorded or ElevenLabs voice, one file per line in `vo.py`.
  Subtitle timing and ducking follow the new audio automatically.
- `assets/logo.png`: the official logo (transparent PNG). It replaces the placeholder V emblem everywhere.
- `assets/screen_1.png`: a full-page screenshot of vantaraai.dev. It replaces the mock page inside the 3D browser.

## Known limitations

- **No human presenter.** No avatar or lip-sync model was available in the build environment.
  A presenter clip from a tool such as HeyGen or Synthesia can be composited in afterwards.
- **No real website content.** vantaraai.dev was unreachable from the build environment.
  Scene 3 uses an illustrative page with skeleton placeholders: brand name, URL and tagline only, with no feature claims.
  Supply `assets/screen_1.png` to show the real site.
- **Placeholder logo.** The emblem is a geometric "V" built for this ad, not the official Vantara AI logo.
- **Estimated subtitle timing.** Word timings come from pause detection and syllable weighting, not forced alignment,
  so individual words may land a few frames early or late.
