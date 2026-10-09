"""Synthesize the electronic score + SFX, then mix with the voiceover (music ducks under speech).

Output: build/music.wav, build/sfx.wav, build/mix.wav (48 kHz stereo)
"""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
import timeline as T

SR = 48000
N = int(SR * T.DUR)
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
rng = np.random.default_rng(7)


def st():
    return np.zeros((N, 2), np.float32)


def add(buf, sig, t, gain=1.0, pan=0.0):
    """Add mono or stereo sig at time t (s) with equal-power pan."""
    n0 = int(round(t * SR))
    if n0 >= N:
        return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(a), sig * np.sin(a)], 1)
    n1 = min(N, n0 + len(sig))
    s0 = max(0, -n0)
    buf[max(0, n0):n1] += sig[s0:n1 - n0] * gain


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100), "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "band", fs=SR, output="sos"), x, axis=0)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, t, phase=0.0):
    p = (f * t + phase) % 1.0
    return 2 * p - 1


def sweep_filter(x, f0, f1, kind="low", blocks=64):
    """Crude time-varying filter: process in blocks with exponentially moving cutoff."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    zi = None
    for b in range(blocks):
        f = f0 * (f1 / f0) ** (b / max(1, blocks - 1))
        sos = butter(2, min(f, SR / 2 - 200), kind, fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[edges[b]:edges[b + 1]], zi = sosfilt(sos, x[edges[b]:edges[b + 1]], zi=zi)
    return out


def reverb(x, secs=2.2, wet=0.25, seed=1):
    r = np.random.default_rng(seed)
    t = tvec(secs)
    ir = np.stack([r.standard_normal(len(t)), r.standard_normal(len(t))], 1) * np.exp(-t * 6.5 / secs)[:, None]
    ir = lp(ir, 7000)
    ir /= np.sqrt((ir ** 2).sum(0))
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet * 3


# ---------------------------------------------------------------- instruments
def kick(d=0.45):
    t = tvec(d)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 300) * 0.25
    return np.tanh((body + click) * 1.6) * 0.9


def clap():
    t = tvec(0.35)
    n = bp(rng.standard_normal(len(t)), 900, 5000)
    env = np.zeros_like(t)
    for o in (0, 0.011, 0.022):
        env += (t >= o) * np.exp(-np.clip(t - o, 0, None) * 60)
    env += np.exp(-t * 14) * 0.5
    return n * env * 0.55


def hat(open_=False):
    t = tvec(0.25 if open_ else 0.06)
    return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t * (14 if open_ else 70)) * 0.22


def impact(big=1.0):
    t = tvec(2.5)
    f = 28 + 70 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crack = lp(rng.standard_normal(len(t)), 6000) * np.exp(-t * 18) * 0.6
    s = np.tanh((boom * 1.4 + crack) * 1.3) * big
    s = np.stack([s, s], 1)
    return reverb(s, 2.5, 0.3, seed=3)


def riser(d):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    n = sweep_filter(n, 300, 9000, "low")
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (t / d * 2.5)) / SR) * 0.25
    env = (t / d) ** 2.2
    return (n * 0.45 + tone) * env


def whoosh(d=0.6, f0=500, f1=6000):
    t = tvec(d)
    n = sweep_filter(rng.standard_normal(len(t)), f0, f1, "low", 32)
    n = hp(n, 250)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2.5
    s = n * env * 0.9
    pan = np.linspace(-0.8, 0.8, len(t))
    a = (pan + 1) * np.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)], 1)


def shimmer(d=2.0, base=76):
    t = tvec(d)
    s = np.zeros_like(t)
    for k, m in enumerate([base, base + 7, base + 12, base + 16, base + 19]):
        s += np.sin(2 * np.pi * note(m) * t + k) * np.exp(-t * (2.5 + k * 0.4)) * (t > k * 0.05)
    s *= 0.12
    return reverb(np.stack([s, s], 1), 2.5, 0.45, seed=5)


def tick():
    t = tvec(0.05)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120) * 0.35 + hp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 200) * 0.15


def glitch(d=0.18):
    t = tvec(d)
    sq = np.sign(np.sin(2 * np.pi * (300 + 900 * rng.random()) * t))
    crush = np.round(rng.standard_normal(len(t)) * 3) / 3
    gate = (np.floor(t * 70) % 2 == 0)
    return (sq * 0.15 + hp(crush, 1500) * 0.2) * gate * np.exp(-t * 8)


def thump():
    t = tvec(0.5)
    f = 50 + 90 * np.exp(-t * 20)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 2) * 0.7


# ---------------------------------------------------------------- score
PROG = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # Am F C G


def chord_at(t):
    return PROG[int(t // 2.0) % 4]  # one chord per bar (2 s)


def section(t):
    if t < 5: return "hook"
    if t < 10: return "reveal"
    if t < 18: return "groove"
    if t < 25: return "drop"
    return "outro"


def build_music():
    m = st()
    beats = np.arange(0, T.DUR, T.BEAT)
    k = kick()
    for b in beats:
        s = section(b)
        if s == "reveal" and b < 6.0: continue        # breathe after the hit
        if s == "outro" and b > 27.0 and b % 1.0: continue
        if s == "outro" and b > 29.0: continue
        if 4.5 <= b < 5.0 or 17.5 <= b < 18 or 24.5 <= b < 25: continue  # pre-drop gaps
        add(m, k, b, 0.85 if s in ("groove", "drop") else 0.7)
    # claps on 2 & 4, plus a roll into the drop
    for b in beats:
        if section(b) in ("groove", "drop") and int(round(b / T.BEAT)) % 2 == 1 and not (17.5 <= b < 18):
            add(m, clap(), b, 0.6, 0.05)
    for i, tt in enumerate(np.arange(16.5, 17.95, 0.125 / 1.0)):
        g = 0.15 + 0.5 * (tt - 16.5) / 1.5
        add(m, clap()[: int(0.12 * SR)], tt, g, 0.1 * (-1) ** i)
    # hats: off-beat 8ths, 16ths in the drop
    for tt in np.arange(0, T.DUR, T.BEAT / 4):
        s = section(tt)
        pos = round(tt / (T.BEAT / 4)) % 4
        if s == "hook" and pos == 2: add(m, hat(), tt, 0.8, 0.3)
        if s in ("reveal", "groove") and pos == 2: add(m, hat(pos == 2 and s == "groove"), tt, 0.7, 0.3)
        if s == "drop" and tt < 24.5: add(m, hat(), tt, 0.5 + 0.35 * (pos == 2), -0.3 + 0.6 * (pos % 2))
    # sub bass (8th notes, side-chained to the kick)
    for tt in np.arange(0, T.DUR, T.BEAT / 2):
        s = section(tt)
        if s == "reveal" and tt < 6 or 4.5 <= tt < 5 or 17.5 <= tt < 18 or 24.5 <= tt < 25 or tt > 29.2:
            continue
        root, _ = chord_at(tt)
        d = T.BEAT / 2
        t = tvec(d)
        f = note(root - 24)
        sub = np.sin(2 * np.pi * f * t)
        grit = lp(saw(f * 2, t), 900 if s == "drop" else 500) * (0.5 if s == "drop" else 0.3)
        env = np.minimum(1, t / 0.005) * np.exp(-t * 3)
        duck = 0.35 + 0.65 * np.clip((tt % T.BEAT) / 0.18, 0, 1) if (tt % T.BEAT) < 0.01 else 1.0
        sig = (sub + grit) * env * duck * 0.42
        if (tt % T.BEAT) < 0.01:
            sig *= np.clip(t / 0.12, 0.25, 1)  # pump
        add(m, sig, tt, 1.0)
    # pads: detuned supersaw chords per bar, stereo spread
    pad = st()
    for bar in np.arange(0, T.DUR, 2.0):
        _, notes = chord_at(bar)
        t = tvec(2.2)
        L = np.zeros_like(t); R = np.zeros_like(t)
        for n_ in notes:
            for dv, pn in ((-0.12, -0.7), (-0.05, -0.3), (0.0, 0), (0.06, 0.3), (0.11, 0.7)):
                f = note(n_ + 12) * 2 ** (dv / 12)
                v = saw(f, t, rng.random())
                L += v * (1 - pn) / 2; R += v * (1 + pn) / 2
        env = np.minimum(1, t / 0.25) * np.minimum(1, (2.2 - t) / 0.3)
        s = np.stack([L, R], 1) * env[:, None] * 0.035
        add(pad, s, bar, 1.0)
    pad = lp(pad, 2400)
    pad_gain = np.interp(np.arange(N) / SR, [0, 5, 5.01, 10, 18, 24.5, 25, 30], [0.5, 0.7, 1.0, 1.0, 1.0, 1.1, 1.3, 1.0])
    m += reverb(pad, 2.0, 0.35, seed=2) * pad_gain[:, None]
    # pluck arp (16ths) in reveal/groove/drop/outro
    arp = st()
    for i, tt in enumerate(np.arange(5.5, 29.5, T.BEAT / 4)):
        if 17.5 <= tt < 18 or 24.5 <= tt < 25.2:
            continue
        _, notes = chord_at(tt)
        pat = [0, 1, 2, 1, 2, 0, 2, 1]
        n_ = notes[pat[i % 8]] + 24 + (12 if (i // 8) % 4 == 3 else 0)
        t = tvec(0.22)
        f = note(n_)
        v = (saw(f, t) * 0.6 + np.sign(np.sin(2 * np.pi * f * 1.005 * t)) * 0.4) * np.exp(-t * 18)
        v = lp(v, 2200 + 2500 * (section(tt) == "drop"))
        add(arp, v, tt, 0.13 * (0.7 if section(tt) in ("reveal", "outro") else 1.0), 0.45 * np.sin(i * 0.7))
    m += reverb(arp, 1.2, 0.3, seed=4)
    # drop lead stabs on the bar
    for bar in np.arange(18, 24, 1.0):
        _, notes = chord_at(bar)
        t = tvec(0.35)
        s = sum(saw(note(n_ + 12), t) + saw(note(n_ + 12) * 1.008, t) for n_ in notes)
        s = lp(s * np.exp(-t * 7), 3500) * 0.05
        add(m, reverb(np.stack([s, s], 1), 1.0, 0.3, 6), bar + 0.25, 1.0)
    # master fade
    fade = np.clip((T.DUR - np.arange(N) / SR) / 1.2, 0, 1)
    return m * fade[:, None]


def build_sfx():
    s = st()
    add(s, impact(1.0), 0.0, 0.9)
    add(s, glitch(), 0.02, 0.6, -0.3)
    add(s, whoosh(0.25, 2000, 9000), T.S1_STOP - 0.12, 0.6)
    add(s, thump(), T.S1_STOP, 0.8)
    add(s, glitch(0.12), T.S1_SCROLL, 0.5, 0.4)
    add(s, thump(), T.S1_SCROLL, 0.8)
    add(s, riser(T.S1_RAMP[1] - 3.3), 3.3, 0.55)
    add(s, whoosh(0.9, 400, 8000), T.S1_RAMP[0], 0.5)
    add(s, impact(1.0), 5.0, 1.0)
    add(s, impact(0.6), T.S2_BURST, 0.7)
    add(s, shimmer(2.5, 76), T.S2_BURST + 0.05, 0.9)
    add(s, whoosh(0.7, 800, 5000), T.S2_LOGO_FRONT - 0.6, 0.35)
    add(s, shimmer(2.0, 81), T.S2_WORDMARK + 0.4, 0.5)
    add(s, whoosh(0.8, 300, 3000), T.S2_MORPH[0], 0.6)   # liquid swoosh
    add(s, impact(0.45), 10.0, 0.6)
    add(s, whoosh(0.5, 600, 7000), 10.05, 0.45)
    for c in T.S3_CLICKS:
        add(s, tick(), c, 0.9, 0.2)
    for w in T.S3_WHIPS:
        add(s, whoosh(0.35, 1500, 9000), w - 0.17, 0.6)
    add(s, riser(1.5), 16.5, 0.5)
    add(s, impact(1.0), 18.0, 1.0)
    words = json.load(open(os.path.join(B, "words.json")))
    for w in words[3]["words"]:
        if w["w"].lower() in ("smarter", "ideas.", "new", "possibilities.", "one", "started!"):
            add(s, whoosh(0.18, 2500, 9000), w["s"] - 0.1, 0.35)
    for w in T.S4_SWEEPS:
        add(s, whoosh(0.5, 900, 9000), w - 0.1, 0.45)
    add(s, riser(T.S4_RISER[1] - T.S4_RISER[0]), T.S4_RISER[0], 0.6)
    add(s, impact(1.2), T.S5_SHOCK, 1.0)
    add(s, shimmer(3.0, 76), T.S5_SHOCK + 0.1, 0.8)
    add(s, tick(), T.S5_URL, 0.6)
    add(s, shimmer(2.0, 88), T.S5_URL, 0.4)
    return s


def envelope(x, att=0.03, rel=0.35):
    """Attack/release follower on 10 ms RMS frames, interpolated back to audio rate."""
    hop = SR // 100
    fr = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same")[::hop])
    a, r = np.exp(-0.01 / att), np.exp(-0.01 / rel)
    out, v = np.zeros_like(fr), 0.0
    for i, e in enumerate(fr):
        c = a if e > v else r
        v = c * v + (1 - c) * e
        out[i] = v
    return np.interp(np.arange(len(x)), np.arange(len(fr)) * hop, out)


def main():
    music = build_music(); music /= np.abs(music).max() + 1e-9
    sfx = build_sfx(); sfx /= np.abs(sfx).max() + 1e-9
    sf.write(os.path.join(B, "music.wav"), music * 0.9, SR)
    sf.write(os.path.join(B, "sfx.wav"), sfx * 0.9, SR)
    vo, _ = sf.read(os.path.join(B, "vo.wav"), dtype="float32")
    # speech gate: hold the bed down for each whole line, ramping 150 ms either side
    gate = np.zeros(N, np.float32)
    for L in json.load(open(os.path.join(B, "words.json"))):
        gate[int((L["start"] - 0.1) * SR):int((L["end"] + 0.1) * SR)] = 1.0
    k = int(0.15 * SR)
    gate = np.convolve(gate, np.ones(k) / k, "same")
    duck_m = 1 - 0.80 * gate          # about -14 dB under speech
    duck_s = 1 - 0.55 * gate          # SFX stay audible between phrases
    mix = music * 0.55 * duck_m[:, None] + sfx * 0.42 * duck_s[:, None] + vo[:, None] * 0.95
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix /= np.abs(mix).max() / 0.95
    sf.write(os.path.join(B, "mix.wav"), mix.astype(np.float32), SR)
    print("mix ok", mix.shape)


if __name__ == "__main__":
    main()
