#!/usr/bin/env bash
# Full pipeline: voice -> word timings -> music/SFX/mix -> 4K60 picture -> final MP4s.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build out

[ "${SKIP_TTS:-0}" = 1 ] || python3 make_voice.py
python3 vo.py
python3 audio.py
python3 render.py --render "${WORKERS:-4}"

ffmpeg -y -loglevel error -i build/video.mp4 -i build/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart \
  out/VantaraAI_Ad_4K60_9x16.mp4

# lighter 1080p copy for quick sharing / review
ffmpeg -y -loglevel error -i out/VantaraAI_Ad_4K60_9x16.mp4 \
  -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a copy -movflags +faststart out/VantaraAI_Ad_1080p60_9x16.mp4

ls -la out
