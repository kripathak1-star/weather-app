"""Generate the temporary AI voiceover with Kokoro (local neural TTS, young US-English male).

Needs: pip install kokoro-onnx soundfile, plus models/kokoro-v1.0.onnx and models/voices-v1.0.bin from
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
Writes build/line_{0..4}.wav. Lines placed in assets/vo_{i}.wav override these in vo.py.
"""
import os, sys
import soundfile as sf
from kokoro_onnx import Kokoro
from vo import LINES

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("KOKORO_MODELS", os.path.join(HERE, "models"))
VOICE = os.environ.get("VOICE", "am_michael")
SPEED = float(os.environ.get("SPEED", "1.12"))

k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
for i, line in enumerate(LINES):
    a, sr = k.create(line, voice=VOICE, speed=SPEED, lang="en-us")
    sf.write(os.path.join(HERE, "build", f"line_{i}.wav"), a, sr)
    print(i, f"{len(a) / sr:.2f}s", line, file=sys.stderr)
