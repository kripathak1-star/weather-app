# 3D Weather Planet video

12-second 1280x720 animation made entirely in code with Three.js (procedural shader planet, atmosphere glow, 3D city temperature towers, cloud swirl, rainstorm with lightning, title card).

- `scene.html`: the 3D scene. Each frame is rendered deterministically by `renderFrame(t)`.
- `render.mjs`: captures every frame in headless Chromium and encodes `weather-planet-3d.mp4` with ffmpeg.

```bash
npm install && node render.mjs 30   # needs Playwright + ffmpeg
```

## 10-minute version: "Every Sky"

`long.html` is a 10-minute, 7-chapter journey with retention hooks at the start (0:00), middle (5:00) and end (9:40):
city countdown, hurricane, aurora, thunderstorm at sea, blizzard, day/night time-lapse and the Super Storm.

```bash
node render-long.mjs --preview 16 305 585   # stills in build/
node render-long.mjs 30 3                   # full MP4 with soundtrack -> every-sky-10min.mp4
```

## Voice-over and soundtrack

- `narration.json`: the timed narration script (82 lines).
- `tts/speak.mjs`: offline Kokoro-82M text-to-speech (voice `af_heart`). It needs `kokoro-js`, `onnxruntime-node`,
  the Kokoro q8 ONNX model and its `config.json` vocab next to the script.
- `music.mjs`: procedural music (pads, arpeggio, drums, chapter impacts) plus thunder on every lightning strike.
- `mix.mjs`: places the voice lines, ducks the music under the voice, adds rain/wind and muxes the final MP4.

```bash
node music.mjs build/music.wav
node mix.mjs <voice-wav-dir> build/music.wav every-sky-10min.mp4 every-sky-10min-voice.mp4
```
