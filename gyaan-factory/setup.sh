#!/usr/bin/env bash
# One-time (per session) setup: node deps, python venv, offline fallback voice.
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules/three ] || npm install --no-audit --no-fund three@0.160.0 @fontsource/baloo-2@5 >/dev/null
[ -e engine/node_modules ] || ln -s ../node_modules engine/node_modules
[ -x .venv/bin/python ] || { python3 -m venv .venv && .venv/bin/pip install -q requests numpy soundfile "sherpa-onnx==1.13.8"; }
if [ ! -d models/vits-piper-hi_IN-pratham-medium ]; then mkdir -p models && curl -sSL https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-hi_IN-pratham-medium.tar.bz2 | tar xj -C models; fi
echo "setup ok"
