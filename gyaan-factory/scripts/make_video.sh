#!/usr/bin/env bash
# Usage: scripts/make_video.sh plans/<name>.json out/<name>
# Turns a plan into a finished video: voice -> captions -> 3D render -> music -> mix -> thumbnail.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; PLAN="$(realpath "$1")"; OUT="$(mkdir -p "$2" && realpath "$2")"
PY="${PY:-$ROOT/.venv/bin/python}"; WORKERS="${WORKERS:-4}"
cd "$ROOT"
echo "== voice"; "$PY" scripts/tts.py "$PLAN" "$OUT/voice"
echo "== captions"; "$PY" scripts/caps.py "$PLAN" "$OUT/voice" engine
echo "== events"; node scripts/render.js events "$OUT/events.json"
T=$(python3 -c "import json;print(json.load(open('$OUT/events.json'))['starts'][-1])"); N=$(python3 -c "print(round($T*30))")
echo "== render $N frames with $WORKERS workers"; pids=()
for k in $(seq 0 $((WORKERS-1))); do a=$((N*k/WORKERS)); z=$((N*(k+1)/WORKERS)); node scripts/render.js video $a $z "$OUT/seg$k.mp4" > "$OUT/seg$k.log" 2>&1 & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
grep -h ERR "$OUT"/seg*.log && { echo "render error"; exit 1; } || true
echo "== audio"; python3 scripts/music.py "$OUT/events.json" "$OUT/music.wav" "$(date +%j)$RANDOM"
"$PY" - "$OUT" <<'PYEOF'
import json,sys,numpy as np,soundfile as sf
O=sys.argv[1];R=json.load(open(f'{O}/events.json'))['starts'];durs=json.load(open(f'{O}/voice/durs.json'))
sr=sf.info(f'{O}/voice/l0.wav').samplerate;v=np.zeros(int(R[-1]*sr)+sr)
for i in range(len(durs)):
    a,_=sf.read(f'{O}/voice/l{i}.wav');s=int((R[i]+.45)*sr);v[s:s+len(a)]+=a[:len(v)-s]
sf.write(f'{O}/voice.wav',v/np.max(np.abs(v))*.95,sr)
PYEOF
ffmpeg -y -loglevel error -i "$OUT/music.wav" -i "$OUT/voice.wav" -filter_complex "[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];[0:a]volume=0.34[m];[m][v1]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=300[md];[md][v2]amix=inputs=2:normalize=0:weights=1 1.15,alimiter=limit=0.95[out]" -map "[out]" -t "$T" "$OUT/mix.wav"
echo "== mux"; ( for k in $(seq 0 $((WORKERS-1))); do echo "file '$OUT/seg$k.mp4'"; done ) > "$OUT/list.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$OUT/list.txt" -i "$OUT/mix.wav" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/video.mp4"
echo "== thumbnail"; python3 -c "import json;p=json.load(open('$PLAN'));json.dump(p.get('thumbnail',{'line1':p['title']}),open('$OUT/thumb.json','w'),ensure_ascii=False)"
node scripts/render.js thumb "$OUT/thumb.json" "$OUT/thumbnail.jpg"
rm -f "$OUT"/seg*.mp4
echo "== small copy (<29 MB, for sending)"
BR=$(python3 -c "print(max(500,int(28*8*1000/$T)-170))")
ffmpeg -y -loglevel error -i "$OUT/video.mp4" -c:v libx264 -preset slow -b:v ${BR}k -pass 1 -passlogfile "$OUT/p2" -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i "$OUT/video.mp4" -c:v libx264 -preset slow -b:v ${BR}k -pass 2 -passlogfile "$OUT/p2" -c:a aac -b:a 160k -movflags +faststart "$OUT/video_send.mp4"
rm -f "$OUT"/p2*
echo "DONE $OUT/video.mp4 ($(du -h "$OUT/video.mp4" | cut -f1))"
