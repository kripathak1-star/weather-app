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
