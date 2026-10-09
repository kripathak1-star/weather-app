"""Place the five voiceover lines on the 30 s timeline and estimate per-word timings.

Input : build/line_{0..4}.wav (any sample rate, mono). If assets/vo_{i}.wav exists it
        replaces the generated line, so a real recorded/ElevenLabs voice can be dropped in.
Output: build/vo.wav (48 kHz mono, 30 s) and build/words.json
"""
import json, os, re
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
DUR = 30.0
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")

LINES = [
    "Wait! Still doing everything the hard way? Watch this!",
    "Meet Vantara AI. A new way to explore artificial intelligence!",
    "Discover the platform, explore its features, and see what AI can do for you!",
    "Smarter ideas. New possibilities. One place to get started!",
    "Your AI journey starts here. Visit Vantara AI today!",
]
STARTS = [0.30, 5.25, 10.35, 18.30, 25.35]  # scene-relative entry points


def load(i):
    p = os.path.join(HERE, "assets", f"vo_{i}.wav")
    if not os.path.exists(p):
        p = os.path.join(B, f"line_{i}.wav")
    a, sr = sf.read(p, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        a = resample_poly(a, SR // g, sr // g).astype(np.float32)
    return a


def syllables(w):
    w = w.lower()
    if w == "ai":
        return 2.0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n) + 0.35  # small constant for consonant onsets


def word_times(a, text, t0):
    hop = int(SR * 0.01)
    rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, "same"))[::hop]
    thr = max(rms.max() * 0.04, 1e-4)
    voiced = np.where(rms > thr)[0]
    v0, v1 = voiced[0], voiced[-1] + 1
    # silent gaps (>= 80 ms) inside the voiced span
    gaps, run = [], None
    for k in range(v0, v1):
        if rms[k] <= thr:
            run = k if run is None else run
        elif run is not None:
            if k - run >= 8:
                gaps.append((k - run, run, k))
            run = None
    words = text.split()
    # phrase segments end at punctuation
    segs, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?,]$", w):
            segs.append(cur); cur = []
    if cur:
        segs.append(cur)
    need = len(segs) - 1
    use = sorted(sorted(gaps, reverse=True)[:need], key=lambda g: g[1])
    bounds = [v0] + [x for g in use for x in (g[1], g[2])] + [v1]
    if len(use) < need:  # not enough pauses found: one proportional span
        segs, bounds = [words], [v0, v1]
    out = []
    for si, seg in enumerate(segs):
        s, e = bounds[2 * si], bounds[2 * si + 1]
        wts = np.array([syllables(re.sub(r"\W", "", w)) for w in seg])
        edges = s + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (e - s)
        for wi, w in enumerate(seg):
            out.append({"w": w, "s": round(t0 + edges[wi] * 0.01, 3),
                        "e": round(t0 + edges[wi + 1] * 0.01, 3)})
    return out


def main():
    track = np.zeros(int(SR * DUR), np.float32)
    lines = []
    for i, text in enumerate(LINES):
        a = load(i)
        a = a / (np.abs(a).max() + 1e-9) * 0.89
        n0 = int(STARTS[i] * SR)
        n1 = min(len(track), n0 + len(a))
        track[n0:n1] += a[: n1 - n0]
        ws = word_times(a, text, STARTS[i])
        lines.append({"line": i, "start": STARTS[i], "end": round(STARTS[i] + len(a) / SR, 3),
                      "words": ws})
        print(i, f"{STARTS[i]:.2f}-{STARTS[i] + len(a) / SR:.2f}", " ".join(f"{w['w']}@{w['s']:.2f}" for w in ws))
    sf.write(os.path.join(B, "vo.wav"), track, SR)
    json.dump(lines, open(os.path.join(B, "words.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
