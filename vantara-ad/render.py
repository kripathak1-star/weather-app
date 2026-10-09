"""Vantara AI 30 s vertical ad — procedural motion-graphics renderer.

  python3 render.py --preview 0.5,5.6,12        # PNG stills (VSCALE=0.5 for fast drafts)
  python3 render.py --render                    # full 4K60 render -> build/video.mp4

Design space is 1080x1920; VSCALE (default 2) maps it to output pixels (2 -> 2160x3840).
Optional overrides: assets/logo.png (RGBA logo) and assets/screen_1.png (tall website
screenshot, scrolled inside the 3D browser in scene 3).
"""
import functools, json, math, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import timeline as T

cv2.setNumThreads(1)
S = float(os.environ.get("VSCALE", "2"))
W, H = int(1080 * S), int(1920 * S)
GW, GH = W // 2, H // 2          # glow layer resolution
GS = S / 2                        # design -> glow px
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
A = os.path.join(HERE, "assets")

FD = "/usr/share/fonts/opentype/inter/"
F_BLACK, F_XB, F_BOLD, F_SEMI, F_MED = (FD + f for f in (
    "InterDisplay-Black.otf", "Inter-ExtraBold.otf", "Inter-Bold.otf", "Inter-SemiBold.otf", "Inter-Medium.otf"))

CYAN = (0.13, 0.83, 1.0)
BLUE = (0.18, 0.42, 1.0)
VIOLET = (0.55, 0.36, 0.96)
WHITE = (1.0, 1.0, 1.0)
ICE = (0.82, 0.95, 1.0)
NAVY = (0.02, 0.04, 0.11)

WORDS = json.load(open(os.path.join(B, "words.json")))

# ------------------------------------------------------------------ easing (graph-editor curves)
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def prog(t, t0, d):
    return clamp((t - t0) / d)

def lerp(a, b, x):
    return a + (b - a) * x

def e_out_cubic(x): return 1 - (1 - x) ** 3
def e_in_cubic(x): return x ** 3
def e_in_out_cubic(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def e_out_expo(x): return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def e_in_expo(x): return 0.0 if x <= 0 else 2 ** (10 * x - 10)
def e_out_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2
def e_out_elastic(x, p=0.38):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return 2 ** (-10 * x) * math.sin((x - p / 4) * 2 * math.pi / p) + 1

def bump(t, t0, k=10.0):
    """1 at t0, exponential decay afterwards, 0 before."""
    return 0.0 if t < t0 else math.exp(-(t - t0) * k)

def noise1(t, seed=0.0):
    return (math.sin(t * 53.1 + seed) * 0.5 + math.sin(t * 91.7 + seed * 2.1) * 0.3
            + math.sin(t * 27.3 + seed * 3.7) * 0.2)

# ------------------------------------------------------------------ sprite construction
_cache = {}

def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]

@functools.lru_cache(None)
def font(path, px):
    return ImageFont.truetype(path, px)

def text_mask(text, fpath, size, tracking=0.0, crop=True, stroke=0):
    px = max(4, int(round(size * S)))
    f = font(fpath, px)
    tr = tracking * px
    ws = [f.getlength(c) for c in text]
    total = (sum(ws) + tr * (len(text) - 1)) if tracking else f.getlength(text)
    asc, desc = f.getmetrics()
    pad = int(px * 0.4) + stroke
    im = Image.new("L", (int(total) + 2 * pad + 2, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, cw in zip(text, ws):
            d.text((x, pad), c, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
            x += cw + tr
    else:
        d.text((pad, pad), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    m = np.asarray(im, np.float32) / 255
    if crop:
        ys, xs = np.nonzero(m > 0.01)
        m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        p = int(px * 0.35) + 2
        m = np.pad(m, p)
    return m

def colorize(mask, top, bottom=None):
    h = mask.shape[0]
    if bottom is None:
        col = np.array(top, np.float32)[None, None, :]
    else:
        rows = np.nonzero(mask.max(1) > 0.05)[0]
        r0, r1 = (rows.min(), rows.max()) if len(rows) else (0, h)
        g = np.clip((np.arange(h, dtype=np.float32) - r0) / max(1, r1 - r0), 0, 1)[:, None, None]
        col = np.array(top, np.float32) * (1 - g) + np.array(bottom, np.float32) * g
    return np.dstack([mask[..., None] * col, mask]).astype(np.float32)

def over(dst, src, ox=0, oy=0):
    h, w = src.shape[:2]
    reg = dst[oy:oy + h, ox:ox + w]
    reg *= 1 - src[..., 3:4]
    reg += src

def extrude(mask, top, bottom, side_far=(0.02, 0.05, 0.18), side_near=(0.10, 0.28, 0.75),
            depth=16, dx=0.55, dy=1.0):
    d = int(depth * S)
    h, w = mask.shape
    out = np.zeros((h + d + 2, w + d + 2, 4), np.float32)
    step = max(1, int(S))
    for i in range(d, 0, -step):
        c = np.array(side_far) * (i / d) + np.array(side_near) * (1 - i / d)
        over(out, colorize(mask, tuple(c)), int(i * dx), int(i * dy))
    face = colorize(mask, top, bottom)
    sh = int(2 * S) + 1
    edge = np.clip(mask - np.pad(mask, ((sh, 0), (0, 0)))[:h], 0, 1)
    face[..., :3] += edge[..., None] * 0.6 * face[..., 3:4]
    over(out, face, 0, 0)
    return out

def glow_of(spr, sigma=16):
    small = cv2.resize(spr, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(small, (0, 0), max(0.6, sigma * S * 0.25))
    b2 = cv2.GaussianBlur(small, (0, 0), max(1.0, sigma * S * 0.75))
    return cv2.resize(b * 0.6 + b2 * 0.6, (spr.shape[1], spr.shape[0]), interpolation=cv2.INTER_LINEAR)

def txt(key, text, fpath, size, top=WHITE, bottom=None, tracking=0.0, ext=False):
    def mk():
        m = text_mask(text, fpath, size, tracking)
        spr = extrude(m, top, bottom or top) if ext else colorize(m, top, bottom)
        return spr
    return cached(("txt", key), mk)

def glow(key, spr, sigma=16):
    return cached(("glow", key, sigma), lambda: glow_of(spr, sigma))

def emblem():
    """Brand mark: the user's logo if supplied, else a geometric V placeholder."""
    def mk():
        sz = int(420 * S)
        p = os.path.join(A, "logo.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            im.thumbnail((sz, sz), Image.LANCZOS)
            a = np.asarray(im, np.float32) / 255
            a[..., :3] *= a[..., 3:4]
            return np.pad(a, ((sz // 6,) * 2, (sz // 6,) * 2, (0, 0)))
        ss = 3
        big = sz * ss
        L = Image.new("L", (big, big), 0); R = Image.new("L", (big, big), 0); D = Image.new("L", (big, big), 0)
        dl, dr, dd = ImageDraw.Draw(L), ImageDraw.Draw(R), ImageDraw.Draw(D)
        u = big / 100
        dl.polygon([(14 * u, 18 * u), (31 * u, 18 * u), (54 * u, 74 * u), (46 * u, 90 * u)], fill=255)
        dr.polygon([(86 * u, 18 * u), (69 * u, 18 * u), (46 * u, 74 * u), (54 * u, 90 * u)], fill=255)
        dd.polygon([(50 * u, 22 * u), (57 * u, 33 * u), (50 * u, 44 * u), (43 * u, 33 * u)], fill=255)
        dd.ellipse([(5 * u, 5 * u), (95 * u, 95 * u)], outline=255, width=int(2.2 * u))
        dd.rectangle([(38 * u, 0), (62 * u, 12 * u)], fill=0)   # gap in the ring
        f = lambda im: np.asarray(im.resize((sz, sz), Image.LANCZOS), np.float32) / 255
        ml, mr, md = f(L), f(R), f(D)
        spr = np.zeros((sz, sz, 4), np.float32)
        over(spr, extrude(ml, CYAN, BLUE, depth=10)[:sz, :sz])
        over(spr, extrude(mr, BLUE, VIOLET, depth=10)[:sz, :sz])
        over(spr, colorize(md, WHITE, CYAN))
        return np.pad(spr, ((sz // 6,) * 2, (sz // 6,) * 2, (0, 0)))
    return cached("emblem", mk)

# ------------------------------------------------------------------ compositing
FOC = 1500 * S

def rot(rx, ry, rz):
    rx, ry, rz = (math.radians(a) for a in (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def place(cv, spr, x, y, sc=1.0, rx=0.0, ry=0.0, rz=0.0, alpha=1.0, add=False, z=0.0):
    """Composite premultiplied RGBA sprite centred at design (x, y) with 3D rotation.
    Returns a function mapping sprite pixel coords -> design coords (for tracking)."""
    if alpha <= 0.003 or sc <= 0.002:
        return None
    h, w = spr.shape[:2]
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]]) * sc
    P = pts @ rot(rx, ry, rz).T
    P[:, 2] += z * S
    den = FOC + P[:, 2]
    if np.any(den < 50):
        return None
    k = FOC / den
    dst = np.c_[x * S + P[:, 0] * k, y * S + P[:, 1] * k]
    area = 0.5 * abs(np.dot(dst[:, 0], np.roll(dst[:, 1], 1)) - np.dot(dst[:, 1], np.roll(dst[:, 0], 1)))
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))

    def mapper(u, v):
        p = M @ np.array([u, v, 1.0])
        return p[0] / p[2] / S, p[1] / p[2] / S

    if area < 4:
        return mapper
    x0, x1 = max(0, int(math.floor(dst[:, 0].min()))), min(W, int(math.ceil(dst[:, 0].max())))
    y0, y1 = max(0, int(math.floor(dst[:, 1].min()))), min(H, int(math.ceil(dst[:, 1].max())))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return mapper
    Mo = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ M
    wp = cv2.warpPerspective(spr, Mo, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    reg = cv[y0:y1, x0:x1]
    if add:
        reg += wp[..., :3] * alpha
    else:
        reg *= 1 - wp[..., 3:4] * alpha
        reg += wp[..., :3] * alpha
    return mapper

def mblur(spr, vx, vy):
    """Directional motion blur of a sprite (velocity in design px per frame-ish units)."""
    L = int(min(abs(vx) + abs(vy), 400) * S)
    if L < 3:
        return spr
    p = L // 2 + 1
    if abs(vx) >= abs(vy):
        s = cv2.copyMakeBorder(spr, 0, 0, p, p, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
        return cv2.blur(s, (L, 1))
    s = cv2.copyMakeBorder(spr, p, p, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
    return cv2.blur(s, (1, L))

def put(cv, key, spr, x, y, sc=1.0, rx=0, ry=0, rz=0, alpha=1.0, glow_amt=0.8, sigma=16, blur=(0, 0)):
    g = glow(key, spr, sigma)
    if blur != (0, 0):
        spr, g = mblur(spr, *blur), mblur(g, *blur)
    if glow_amt > 0:
        place(cv, g, x, y, sc, rx, ry, rz, alpha * glow_amt, add=True)
    return place(cv, spr, x, y, sc, rx, ry, rz, alpha)

# ------------------------------------------------------------------ glow layer primitives (design coords)
SH = 4
SF = 1 << SH

def gp(x, y):
    return int(round(x * GS * SF)), int(round(y * GS * SF))

def col255(c, a=1.0):
    return tuple(float(clamp(v * a) * 255) for v in c)

def gline(G, p1, p2, c, th=2.0, a=1.0):
    if a <= 0.01:
        return
    cv2.line(G, gp(*p1), gp(*p2), col255(c, a), max(1, int(round(th * GS))), cv2.LINE_AA, SH)

def gcircle(G, p, r, c, a=1.0, th=-1):
    if a <= 0.01:
        return
    cv2.circle(G, gp(*p), max(1, int(round(r * GS * SF))), col255(c, a),
               th if th < 0 else max(1, int(round(th * GS))), cv2.LINE_AA, SH)

def gpoly(G, pts, c, th=2.0, a=1.0, closed=False):
    if a <= 0.01:
        return
    arr = np.array([gp(*p) for p in pts], np.int32).reshape(-1, 1, 2)
    cv2.polylines(G, [arr], closed, col255(c, a), max(1, int(round(th * GS))), cv2.LINE_AA, SH)

def flush_glow(cv, G, core=1.0, bloom=1.0):
    g = G.astype(np.float32) * (1 / 255)
    b = cv2.GaussianBlur(cv2.resize(g, (GW // 4, GH // 4), interpolation=cv2.INTER_AREA), (0, 0), 3 * S)
    m = cv2.GaussianBlur(g, (0, 0), 2.5 * S)
    mix = g * core + m * 0.9 * bloom + cv2.resize(b, (GW, GH)) * 1.3 * bloom
    cv += cv2.resize(mix, (W, H), interpolation=cv2.INTER_LINEAR)

def new_glow():
    return np.zeros((GH, GW, 3), np.uint8)

# ------------------------------------------------------------------ backgrounds
def make_bg(center_col, edge_col, cy=0.42, rad=0.75, vign=0.55):
    def mk():
        yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32)
        d = np.sqrt(((xx / GW - 0.5) * 1.0) ** 2 + ((yy / GH - cy) * 0.75) ** 2) / rad
        g = np.clip(d, 0, 1)[..., None]
        img = np.array(center_col, np.float32) * (1 - g) + np.array(edge_col, np.float32) * g
        v = np.sqrt(((xx / GW - 0.5) * 1.6) ** 2 + ((yy / GH - 0.5) * 1.2) ** 2)
        img *= (1 - vign * np.clip(v - 0.35, 0, 1) ** 1.5)[..., None]
        img += np.random.default_rng(1).normal(0, 0.004, img.shape).astype(np.float32)  # dither vs banding
        return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
    return cached(("bg", center_col, edge_col, cy, rad), mk)

BG1 = ((0.05, 0.10, 0.28), (0.005, 0.01, 0.04))
BG2 = ((0.06, 0.12, 0.34), (0.01, 0.01, 0.05))
BG4 = ((0.07, 0.05, 0.25), (0.005, 0.005, 0.03))
BG5 = ((0.05, 0.13, 0.36), (0.004, 0.01, 0.04))

def blob_bg(t):
    """Soft moving colour blobs (behind glass panels)."""
    sw, sh = 135, 240
    img = np.zeros((sh, sw, 3), np.float32)
    img[:] = (0.01, 0.015, 0.05)
    blobs = [(BLUE, 0.3, 0.35, 0.33), (VIOLET, 0.75, 0.6, 0.30), (CYAN, 0.45, 0.85, 0.22), (BLUE, 0.85, 0.2, 0.22)]
    for i, (c, bx, by, r) in enumerate(blobs):
        x = (bx + 0.08 * math.sin(t * 0.5 + i * 1.7)) * sw
        y = (by + 0.05 * math.cos(t * 0.4 + i)) * sh
        cv2.circle(img, (int(x), int(y)), int(r * sw), tuple(v * 0.32 for v in c), -1, cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 22)
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)

# ------------------------------------------------------------------ shared FX
RNG = np.random.default_rng(42)
DUST = RNG.random((140, 4))

def dust(G, t, a=0.5, par=(0, 0)):
    for i, (x, y, s, ph) in enumerate(DUST):
        yy = ((y - t * (0.01 + 0.02 * s)) % 1.0) * 1920 + par[1] * (0.3 + s)
        xx = x * 1080 + 18 * math.sin(t * 0.7 + ph * 6) + par[0] * (0.3 + s)
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + 2 * s) + ph * 10)
        c = CYAN if i % 3 else VIOLET
        gcircle(G, (xx, yy), 1.0 + 2.2 * s, c, a * (0.25 + 0.75 * tw) * (0.4 + s))

def burst(G, t, t0, c, n=160, seed=1, speed=900, life=1.6, cols=(CYAN, BLUE, VIOLET, WHITE), drag=2.8, a=1.0):
    dt = t - t0
    if dt < 0 or dt > life:
        return
    r = np.random.default_rng(seed)
    ang = r.random(n) * 2 * math.pi
    sp = speed * (0.25 + r.random(n) ** 1.5)
    sz = 1.2 + r.random(n) * 3
    fall = (1 - dt / life) ** 1.4
    k = (1 - math.exp(-drag * dt)) / drag
    k2 = (1 - math.exp(-drag * max(0, dt - 0.035))) / drag
    for i in range(n):
        dx, dy = math.cos(ang[i]) * sp[i], math.sin(ang[i]) * sp[i] * 0.85
        p1 = (c[0] + dx * k, c[1] + dy * k + 60 * dt * dt)
        p0 = (c[0] + dx * k2, c[1] + dy * k2 + 60 * max(0, dt - 0.035) ** 2)
        gline(G, p0, p1, cols[i % len(cols)], sz[i] * fall + 0.6, a * fall)

def grid_floor(G, t, horizon=1060, speed=1.2, a=0.55, col=BLUE):
    vx = 540
    for i in range(-12, 13):
        gline(G, (vx + i * 14, horizon), (vx + i * 260, 1920 + 400), col, 1.6, a * 0.55)
    for j in range(14):
        z = ((j - t * speed) % 14) + 0.6
        y = horizon + 520 / z
        fade = clamp((y - horizon) / 160) * clamp(1.4 - z / 14)
        gline(G, (-50, y), (1130, y), col, 1.0 + 3 / z, a * fade)

def shake(t, events):
    x = y = r = 0.0
    for t0, amp in events:
        b = bump(t, t0, 9.0) * amp
        if b > 0.05:
            x += b * noise1(t, t0)
            y += b * noise1(t, t0 + 7)
            r += b * 0.025 * noise1(t, t0 + 3)
    return x, y, r

# ------------------------------------------------------------------ subtitles
def sub_groups():
    """Caption chunks: break after punctuation or every 3 words; each holds until the next chunk."""
    out = []
    for L in WORDS:
        gs, cur = [], []
        for w in L["words"]:
            cur.append(w)
            if w["w"][-1] in ".,!?" or len(cur) == 3:
                gs.append(cur); cur = []
        if cur:
            gs.append(cur)
        for i, g in enumerate(gs):
            end = gs[i + 1][0]["s"] if i + 1 < len(gs) else L["end"] + 0.35
            out.append((g[0]["s"] - 0.06, end, g, i + 1 == len(gs)))
    return out

GROUPS = sub_groups()
SUB_Y = 1395
SUB_SIZE = 66

def word_sprite(w):
    def mk():
        m = text_mask(w.upper(), F_XB, SUB_SIZE, crop=False)
        fill = colorize(m, WHITE)
        st = text_mask(w.upper(), F_XB, SUB_SIZE, crop=False, stroke=int(5 * S))
        # align stroke mask (it has extra pad) with fill mask
        dy = (st.shape[0] - m.shape[0]) // 2; dx = (st.shape[1] - m.shape[1]) // 2
        st = st[dy:dy + m.shape[0], dx:dx + m.shape[1]]
        out = colorize(st, (0.0, 0.01, 0.04))
        sh = cv2.GaussianBlur(out, (0, 0), 6 * S) * 0.7
        o = sh.copy(); over(o, out); over(o, fill)
        return o
    return cached(("word", w.upper()), mk)

def pill_sprite(wd, ht):
    key = ("pill", int(wd * S), int(ht * S))
    def mk():
        w, h = int(wd * S), int(ht * S)
        ss = 2
        m = Image.new("L", (w * ss, h * ss), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=h * ss // 3, fill=255)
        mk_ = np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255
        g = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
        col = np.array(BLUE) * (1 - g) + np.array(VIOLET) * g
        spr = np.dstack([mk_[..., None] * col, mk_]).astype(np.float32)
        return np.pad(spr, ((int(h * .3),) * 2, (int(h * .3),) * 2, (0, 0)))
    return cached(key, mk)

def draw_subs(cv, t):
    for gi, (g0, g1, g, last) in enumerate(GROUPS):
        nxt0 = GROUPS[gi + 1][0] if gi + 1 < len(GROUPS) else 1e9
        if not (g0 <= t < (g1 + 0.12 if last else min(g1, nxt0))):
            continue
        appear = e_out_back(prog(t, g0, 0.22), 2.2)
        fade = 1 - prog(t, g1, 0.12) if last else 1.0
        sprs = [word_sprite(w["w"]) for w in g]
        gap = 26
        pad_px = int(SUB_SIZE * S * 0.4)
        widths = [(s.shape[1] - 2 * pad_px) / S for s in sprs]
        total = sum(widths) + gap * (len(g) - 1)
        sc = min(1.0, 980 / total)
        x = 540 - total * sc / 2
        cur = None
        for i, w in enumerate(g):
            nxt = g[i + 1]["s"] if i + 1 < len(g) else g1
            if w["s"] <= t < nxt:
                cur = i
        centers = []
        xx = x
        for i, wd in enumerate(widths):
            centers.append(540 + (xx + wd * sc / 2 - 540) * appear); xx += (wd + gap) * sc
        if cur is not None:
            w = g[cur]
            k = e_out_cubic(prog(t, w["s"], 0.09))
            pi = max(0, cur - 1) if k < 1 else cur
            cx = lerp(centers[pi], centers[cur], k) if cur > 0 else centers[cur]
            pw = lerp(widths[pi], widths[cur], k) if cur > 0 else widths[cur]
            pill = pill_sprite(int(pw + 34), int(SUB_SIZE * 1.32))
            pop = 1 + 0.08 * bump(t, w["s"], 14)
            place(cv, pill, cx, SUB_Y + 2, sc * appear * pop, alpha=0.95 * fade)
        for i, (s, w) in enumerate(zip(sprs, g)):
            spoken = t >= w["s"]
            a = (1.0 if spoken else 0.55) * fade
            pop = 1 + (0.12 * bump(t, w["s"], 12) if spoken else 0)
            place(cv, s, centers[i], SUB_Y, sc * appear * pop, alpha=a)

# ------------------------------------------------------------------ scene 1: hook
def scene1(t):
    cv = make_bg(*BG1).copy()
    G = new_glow()
    grid_floor(G, t, speed=1.5 + 4 * e_in_cubic(prog(t, *T.S1_RAMP)))
    dust(G, t, 0.5)
    burst(G, t, T.S1_STOP + 0.05, (540, 640), n=120, seed=3, speed=1100)
    burst(G, t, T.S1_SCROLL + 0.05, (540, 880), n=80, seed=4, speed=900, cols=(CYAN, WHITE))
    # neon underline
    k = e_out_expo(prog(t, T.S1_SCROLL + 0.1, 0.5))
    gline(G, (540 - 380 * k, 990), (540 + 380 * k, 990), CYAN, 5, 0.9)
    gline(G, (540 - 260 * k, 1010), (540 + 260 * k, 1010), VIOLET, 3, 0.7)
    flush_glow(cv, G)
    # STOP: slams in, extruded 3D, idles with a slow 3D float
    if t >= T.S1_STOP:
        u = prog(t, T.S1_STOP, 0.5)
        sc = lerp(3.2, 1.0, e_out_elastic(u, 0.45))
        spr = txt("stop", "STOP", F_BLACK, 300, WHITE, ICE, ext=True)
        put(cv, "stop", spr, 540, 650, sc, rx=6 * math.sin(t * 1.1), ry=12 * math.sin(t * 1.4 + 0.5),
            rz=lerp(-14, -3, e_out_back(u)), alpha=clamp(u * 6), glow_amt=0.55, sigma=22)
    if t >= T.S1_SCROLL:
        u = prog(t, T.S1_SCROLL, 0.42)
        e = e_out_expo(u)
        x = lerp(1500, 540, e)
        v = (1 - e) * 160 if u < 1 else 0
        spr = txt("scroll", "SCROLLING!", F_BLACK, 148, CYAN, BLUE, ext=True)
        put(cv, "scroll", spr, x, 880, 1.0, rx=4 * math.sin(t * 1.3), ry=-10 * math.sin(t * 1.2),
            rz=-3, glow_amt=0.8, sigma=18, blur=(v, 0))
    return cv

# ------------------------------------------------------------------ scene 2: reveal
def trails_in(G, t):
    s_end = T.S2_BURST
    for k in range(7):
        th0 = k / 7 * 2 * math.pi
        pts = []
        for j in range(26):
            tt = t - j * 0.012
            s = clamp((tt - 5.0) / (s_end - 5.0))
            if tt < 5.0:
                break
            r = 720 * (1 - s) ** 1.3
            th = th0 + 3.2 * (1 - s)
            pts.append((540 + r * math.cos(th), 700 + r * math.sin(th) * 0.62))
        for j in range(len(pts) - 1):
            gline(G, pts[j], pts[j + 1], CYAN if k % 2 else VIOLET, 6 * (1 - j / 26) + 0.8, 1 - j / 26)
        if pts and t < s_end:
            gcircle(G, pts[0], 7, WHITE, 0.9)

def orbit(G, t, cx, cy, rx, ry, tilt, speed, c, phase=0.0, a=1.0, head=True):
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    pts = []
    for j in range(40):
        ang = t * speed + phase - j * 0.06
        x, y = rx * math.cos(ang), ry * math.sin(ang)
        pts.append((cx + x * ct - y * st, cy + x * st + y * ct))
    for j in range(len(pts) - 1):
        gline(G, pts[j], pts[j + 1], c, 4.5 * (1 - j / 40) + 0.6, a * (1 - j / 40))
    if head:
        gcircle(G, pts[0], 6, WHITE, a)

def scene2(t):
    cv = make_bg(*BG2).copy()
    G = new_glow()
    dust(G, t, 0.6)
    trails_in(G, t)
    burst(G, t, T.S2_BURST, (540, 700), n=260, seed=8, speed=1300, life=2.2)
    # shock ring at burst
    u = prog(t, T.S2_BURST, 0.8)
    if 0 < u < 1:
        gcircle(G, (540, 700), 40 + 900 * e_out_cubic(u), CYAN, (1 - u) * 0.9, th=10 * (1 - u) + 1)
    on = e_out_cubic(prog(t, T.S2_BURST, 0.6))
    if on > 0:
        orbit(G, t, 540, 700, 330, 95, -18, 2.6, CYAN, 0.0, on)
        orbit(G, t, 540, 700, 300, 80, 22, -2.1, VIOLET, 2.0, on * 0.9)
    # line under wordmark
    k = e_out_expo(prog(t, T.S2_WORDMARK + 0.4, 0.8))
    gline(G, (540 - 330 * k, 1110), (540 + 330 * k, 1110), CYAN, 3, 0.85)
    flush_glow(cv, G)
    # MEET
    u = prog(t, 5.28, 0.5)
    if u > 0:
        spr = txt("meet", "MEET", F_BLACK, 96, ICE, CYAN, tracking=0.32)
        put(cv, "meet", spr, 540, lerp(270, 330, e_out_expo(u)), lerp(0.6, 1.0, e_out_back(u)),
            alpha=clamp(u * 3), glow_amt=0.6)
    # emblem: 3D Y rotation from edge-on to front, then a slow wobble
    if t >= T.S2_BURST - 0.05:
        u = prog(t, T.S2_BURST - 0.05, T.S2_LOGO_FRONT - T.S2_BURST + 0.05)
        ry = lerp(88, 0, e_out_back(u, 1.4)) + 9 * math.sin((t - 5) * 1.6) * on
        sc = lerp(0.3, 1.0, e_out_elastic(prog(t, T.S2_BURST - 0.05, 0.9), 0.5))
        put(cv, "emblem", emblem(), 540, 700, sc, rx=5 * math.sin(t), ry=ry, glow_amt=0.9, sigma=26)
    # wordmark letters stagger in (elastic, rising, with glow)
    letters = "VANTARA AI"
    WM = 118
    f = font(F_BLACK, int(WM * S))
    trk = 0.04 * WM
    adv = [f.getlength(c) / S + trk for c in letters]
    total = sum(adv) - trk
    x = 540 - total / 2
    si = 0
    for i, c in enumerate(letters):
        cx = x + (adv[i] - trk) / 2
        x += adv[i]
        if c == " ":
            continue
        sprs_c = txt("wm_" + c + str(i >= 7), c, F_BLACK, WM, WHITE if i < 7 else CYAN, ICE if i < 7 else BLUE)
        u = prog(t, T.S2_WORDMARK + i * 0.045, 0.6)
        if u > 0:
            put(cv, "wm_" + c + str(i >= 7), sprs_c, cx, lerp(1080, 1010, e_out_back(u, 2.4)), lerp(1.6, 1.0, e_out_expo(u)),
                rx=lerp(70, 0, e_out_cubic(u)), alpha=clamp(u * 4), glow_amt=0.55)
        si += 1
    # url hint
    u = prog(t, 8.0, 0.6)
    if u > 0:
        spr = txt("url2", "vantaraai.dev", F_SEMI, 46, ICE, tracking=0.08)
        put(cv, "url2", spr, 540, lerp(1190, 1170, e_out_cubic(u)), alpha=u * 0.9, glow_amt=0.4)
    return cv

# ------------------------------------------------------------------ scene 3: website showcase
PW, PH, CH = 760, 1100, 66          # panel width/height, chrome bar height (design)
PAGE_H = 2300

def rrect(d, box, r, **kw):
    d.rounded_rectangle([int(v * S) for v in box], radius=int(r * S), **kw)

def page_sprite():
    def mk():
        p = os.path.join(A, "screen_1.png")
        w = int(PW * S)
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
            a = np.asarray(im, np.float32) / 255
            a[..., :3] *= a[..., 3:4]
            return a
        hgt = int(PAGE_H * S)
        im = Image.new("RGBA", (w, hgt), (8, 14, 34, 200))
        d = ImageDraw.Draw(im)
        # hero glow
        gl = Image.new("L", (w, int(700 * S)), 0)
        ImageDraw.Draw(gl).ellipse([int(80 * S), int(120 * S), int(680 * S), int(620 * S)], fill=120)
        glow_rgba = np.zeros((gl.height, w, 4), np.uint8)
        gm = cv2.GaussianBlur(np.asarray(gl, np.float32), (0, 0), 70 * S)
        glow_rgba[..., 0], glow_rgba[..., 1], glow_rgba[..., 2] = 47, 107, 255
        glow_rgba[..., 3] = np.clip(gm, 0, 255).astype(np.uint8)
        im.alpha_composite(Image.fromarray(glow_rgba, "RGBA"), (0, 0))
        # nav
        em = Image.fromarray((np.clip(emblem() / np.maximum(emblem()[..., 3:4], 1e-4), 0, 1) * 255).astype(np.uint8)[..., :3])
        ea = Image.fromarray((emblem()[..., 3] * 255).astype(np.uint8))
        em.putalpha(ea)
        em = em.resize((int(62 * S), int(62 * S)), Image.LANCZOS)
        im.alpha_composite(em, (int(28 * S), int(14 * S)))
        d.text((int(96 * S), int(26 * S)), "VANTARA AI", font=font(F_BLACK, int(30 * S)), fill=(235, 245, 255, 255))
        for i in range(3):
            rrect(d, (680, 30 + i * 12, 724, 34 + i * 12), 2, fill=(180, 200, 230, 220))
        # hero
        f = font(F_BLACK, int(66 * S))
        for i, line in enumerate(("YOUR AI JOURNEY", "STARTS HERE")):
            lw = f.getlength(line)
            d.text(((w - lw) / 2, int((230 + i * 80) * S)), line, font=f,
                   fill=(240, 248, 255, 255) if i == 0 else (60, 200, 255, 255))
        for i, bw in enumerate((520, 400)):
            rrect(d, (380 - bw / 2, 430 + i * 36, 380 + bw / 2, 446 + i * 36), 8, fill=(150, 170, 210, 90))
        rrect(d, (250, 540, 510, 620), 40, fill=(60, 110, 255, 255))
        d.text((int(362 * S), int(548 * S)), "→", font=font(F_BOLD, int(48 * S)), fill=(255, 255, 255, 255))
        # section header skeleton
        rrect(d, (230, 770, 530, 796), 13, fill=(200, 215, 240, 150))
        rrect(d, (170, 818, 590, 834), 8, fill=(150, 170, 210, 80))
        # cards 2x2
        icol = [(34, 211, 255), (139, 92, 246), (47, 107, 255), (34, 211, 255)]
        for k, (cx, cy) in enumerate([(35, 880), (395, 880), (35, 1210), (395, 1210)]):
            rrect(d, (cx, cy, cx + 330, cy + 300), 26, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=max(1, int(1.5 * S)))
            d.ellipse([int((cx + 30) * S), int((cy + 30) * S), int((cx + 100) * S), int((cy + 100) * S)], fill=icol[k] + (230,))
            rrect(d, (cx + 30, cy + 140, cx + 250, cy + 162), 11, fill=(220, 230, 250, 160))
            rrect(d, (cx + 30, cy + 190, cx + 290, cy + 204), 7, fill=(150, 170, 210, 80))
            rrect(d, (cx + 30, cy + 220, cx + 240, cy + 234), 7, fill=(150, 170, 210, 80))
        # banner
        ban = np.zeros((int(340 * S), int(690 * S), 4), np.uint8)
        g = np.linspace(0, 1, ban.shape[1])[None, :]
        ban[..., 0] = (47 * (1 - g) + 139 * g); ban[..., 1] = (107 * (1 - g) + 92 * g); ban[..., 2] = 255 * (1 - g) + 246 * g
        bm = Image.new("L", (ban.shape[1], ban.shape[0]), 0)
        ImageDraw.Draw(bm).rounded_rectangle([0, 0, ban.shape[1] - 1, ban.shape[0] - 1], radius=int(30 * S), fill=200)
        ban[..., 3] = np.asarray(bm)
        im.alpha_composite(Image.fromarray(ban, "RGBA"), (int(35 * S), int(1560 * S)))
        rrect(d, (80, 1640, 440, 1668), 14, fill=(255, 255, 255, 220))
        rrect(d, (80, 1700, 560, 1716), 8, fill=(255, 255, 255, 120))
        rrect(d, (80, 1734, 500, 1750), 8, fill=(255, 255, 255, 120))
        rrect(d, (80, 1790, 260, 1846), 28, fill=(255, 255, 255, 235))
        # footer
        for i in range(3):
            rrect(d, (60, 1990 + i * 40, 60 + (300 - i * 60), 2004 + i * 40), 7, fill=(150, 170, 210, 70))
        d.text((int(60 * S), int(2160 * S)), "vantaraai.dev", font=font(F_SEMI, int(28 * S)), fill=(120, 200, 255, 230))
        a = np.asarray(im, np.float32) / 255
        a[..., :3] *= a[..., 3:4]
        return a
    return cached("page", mk)

def chrome_sprite():
    def mk():
        w, h = int(PW * S), int(CH * S)
        im = Image.new("RGBA", (w, h), (14, 22, 48, 235))
        d = ImageDraw.Draw(im)
        for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
            x = int((28 + i * 26) * S); y = int(33 * S); r = int(8 * S)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (200,))
        rrect(d, (130, 14, 630, 52), 19, fill=(255, 255, 255, 30))
        # padlock glyph
        rrect(d, (152, 28, 168, 44), 3, fill=(140, 220, 255, 255))
        d.arc([int(154 * S), int(20 * S), int(166 * S), int(34 * S)], 180, 360, fill=(140, 220, 255, 255), width=max(1, int(2.5 * S)))
        d.text((int(180 * S), int(19 * S)), "vantaraai.dev", font=font(F_MED, int(24 * S)), fill=(225, 238, 255, 255))
        a = np.asarray(im, np.float32) / 255
        a[..., :3] *= a[..., 3:4]
        return a
    return cached("chrome", mk)

def frame_mask(w, h, r):
    def mk():
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
        return np.asarray(m, np.float32)[..., None] / 255
    return cached(("fmask", w, h, r), mk)

SCROLL_KEYS = [(10.0, 0), (11.8, 0), (12.65, 760), (13.9, 760), (15.05, 1250), (18.0, 1250)]
CURSOR_KEYS = [(10.0, (700, 900)), (11.35, (395, 590)), (11.9, (420, 640)), (13.35, (565, 1365)),
               (13.9, (600, 1400)), (15.85, (380, 1730)), (16.4, (430, 1780)), (18.0, (520, 1850))]
HILITES = [(T.S3_CLICKS[0], (250, 540, 510, 620)), (T.S3_CLICKS[1], (395, 1210, 725, 1510)),
           (T.S3_CLICKS[2], (35, 1560, 725, 1900))]

def keyed(keys, t):
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            e = e_in_out_cubic((t - t0) / (t1 - t0))
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, e) for a, b in zip(v0, v1))
            return lerp(v0, v1, e)
    return keys[-1][1]

def panel_frame(t, scroll, with_ui=True):
    page = page_sprite()
    w = int(PW * S)
    vh = int((PH - CH) * S)
    s0 = int(scroll * S)
    s0 = max(0, min(page.shape[0] - vh, s0))
    out = np.zeros((int(PH * S), w, 4), np.float32)
    out[:, :, :] = (0.03 * 0.6, 0.05 * 0.6, 0.12 * 0.6, 0.6)          # glass base
    view = page[s0:s0 + vh]
    reg = out[int(CH * S):int(CH * S) + view.shape[0]]
    reg *= 1 - view[..., 3:4]; reg += view
    out[:int(CH * S)] = chrome_sprite()
    if with_ui:
        for tc, (x0, y0, x1, y1) in HILITES:
            u = t - tc
            if -0.1 < u < 1.6:
                a = clamp((u + 0.1) * 8) * (1 - clamp((u - 1.1) * 2))
                grow = 8 * e_out_back(clamp(u * 3))
                yy0 = (y0 - scroll + CH - grow) * S; yy1 = (y1 - scroll + CH + grow) * S
                xx0 = (x0 - grow) * S; xx1 = (x1 + grow) * S
                for th, al in ((10, 0.25), (3, 1.0)):
                    cv2.rectangle(out, (int(xx0), int(yy0)), (int(xx1), int(yy1)),
                                  (CYAN[0] * a * al, CYAN[1] * a * al, CYAN[2] * a * al, a * al), int(th * S))
    # glass sheen + border
    g = np.linspace(0.10, 0.0, out.shape[0] // 3, dtype=np.float32)[:, None, None]
    out[:out.shape[0] // 3, :, :3] += g * out[:out.shape[0] // 3, :, 3:4]
    cv2.rectangle(out, (0, 0), (out.shape[1] - 1, out.shape[0] - 1), (0.35, 0.45, 0.6, 0.6), max(1, int(2 * S)))
    out *= frame_mask(out.shape[1], out.shape[0], int(28 * S))
    return out

def cursor_sprite():
    def mk():
        s = int(56 * S)
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        u = s / 56
        pts = [(4, 2), (4, 44), (15, 34), (23, 52), (31, 48), (23, 31), (38, 31)]
        d.polygon([(x * u, y * u) for x, y in pts], fill=(255, 255, 255, 255), outline=(10, 20, 40, 255), width=max(1, int(2.5 * u)))
        a = np.asarray(im, np.float32) / 255
        a[..., :3] *= a[..., 3:4]
        return np.pad(a, ((s, s), (s, s), (0, 0)))  # pad so the tip sits at sprite centre-ish
    return cached("cursor", mk)

def side_panel(scroll):
    def mk():
        p = panel_frame(-10, scroll, with_ui=False)
        return cv2.GaussianBlur(p, (0, 0), 2.5 * S)
    return cached(("side", scroll), mk)

def s3_headline(cv, t):
    items = [("discover", ["DISCOVER"], 10.39, 11.6), ("explore", ["EXPLORE"], 11.63, 13.25),
             ("seewhat", ["SEE WHAT", "AI CAN DO"], 13.31, 17.7)]
    for key, lines, t0, t1 in items:
        if not (t0 <= t < t1 + 0.25):
            continue
        u = prog(t, t0, 0.55)
        out = prog(t, t1, 0.25)
        for li, line in enumerate(lines):
            uu = prog(t, t0 + li * 0.12, 0.55)
            spr = txt(f"{key}{li}", line, F_BLACK, 112 if len(lines) > 1 else 128,
                      WHITE if li == 0 else CYAN, ICE if li == 0 else VIOLET, ext=True)
            y = (230 if len(lines) == 1 else 190 + li * 125) - 400 * e_in_expo(out)
            put(cv, f"{key}{li}", spr, 540, y + 40 * (1 - e_out_back(uu)), lerp(0.5, 1, e_out_elastic(uu, 0.5)),
                rx=lerp(-60, 0, e_out_cubic(uu)) + 4 * math.sin(t * 1.5), ry=5 * math.sin(t * 1.1),
                alpha=clamp(uu * 4) * (1 - out), glow_amt=0.5, blur=(0, 120 * out))

def scene3(t):
    cv = blob_bg(t)
    G = new_glow()
    drift = (math.sin(t * 0.5) * 20, math.cos(t * 0.4) * 14)
    dust(G, t, 0.45, par=drift)
    # whips: quick lateral pans that swap the panel's tilt
    wx, wblur = 0.0, 0.0
    flip = 0
    for i, wt in enumerate(T.S3_WHIPS):
        d = t - wt
        if -0.17 < d < 0.17:
            k = (d + 0.17) / 0.34
            wx = (-e_in_expo(k * 2) * 900 if k < 0.5 else (1 - e_out_expo((k - 0.5) * 2)) * 900) * (1 if i % 2 else -1)
            wblur = 220 * (1 - abs(k - 0.5) * 2)
        if t >= wt:
            flip += 1
    ry_base = [-15, 13, -9][flip]
    scroll = keyed(SCROLL_KEYS, t)
    # side panels (parallax: they move less)
    sp_in = e_out_expo(prog(t, 10.05, 0.8))
    place(cv, side_panel(900), 150 + drift[0] * 0.5 + wx * 0.6 - 300 * (1 - sp_in), 820 + drift[1] * 0.5,
          0.62, rx=6, ry=24, alpha=0.5 * sp_in, z=420)
    place(cv, side_panel(1250), 930 + drift[0] * 0.5 + wx * 0.6 + 300 * (1 - sp_in), 1000 + drift[1] * 0.5,
          0.62, rx=6, ry=-24, alpha=0.5 * sp_in, z=420)
    flush_glow(cv, G, bloom=0.7)
    # main panel
    p_in = prog(t, 10.0, 0.75)
    pf = panel_frame(t, scroll)
    if wblur > 1:
        pf = mblur(pf, wblur, 0)
    px = 540 + drift[0] + wx
    py = lerp(1500, 905, e_out_expo(p_in)) + 10 * math.sin(t * 1.4) + drift[1]
    sc = 0.80 * lerp(0.7, 1, e_out_back(p_in, 1.2))
    ry = ry_base + 3 * math.sin(t * 0.7)
    rx = lerp(40, 7, e_out_cubic(p_in)) + 2 * math.sin(t * 0.9)
    # soft drop glow behind the panel
    G2 = new_glow()
    sh = cached("pshadow", lambda: glow_of(np.dstack([np.ones((int(PH * S), int(PW * S), 3), np.float32) * np.array(BLUE, np.float32),
                                                       np.ones((int(PH * S), int(PW * S), 1), np.float32)]), 30))
    place(cv, sh, px, py + 30, sc * 1.05, rx, ry, alpha=0.35 * p_in, add=True)
    mp = place(cv, pf, px, py, sc, rx, ry)
    # cursor rides on the 3D panel (tracked through the same projection)
    if mp and t > 10.6:
        cx_, cy_ = keyed(CURSOR_KEYS, t)
        vy = (cy_ - scroll + CH)
        if -20 < vy < PH:
            dx, dy = mp(cx_ * S, vy * S)
            press = 1 - 0.18 * sum(bump(t, c, 14) for c in T.S3_CLICKS if t >= c)
            cs = cursor_sprite()
            place(cv, cs, dx + 28 * sc, dy + 28 * sc, sc * press, alpha=clamp((t - 10.6) * 4))
            for c in T.S3_CLICKS:
                u = prog(t, c, 0.55)
                if 0 < u < 1:
                    gcircle(G2, (dx, dy), 10 + 90 * e_out_cubic(u), CYAN, 1 - u, th=4)
    flush_glow(cv, G2)
    s3_headline(cv, t)
    return cv

# ------------------------------------------------------------------ scene 4: high-energy kinetic edit
def tunnel(G, t, pulse):
    for i in range(14):
        z = ((i - t * 3.2) % 14) + 0.35
        hw, hh = 300 * 1.4 / z, 533 * 1.4 / z
        a = clamp((14 - z) / 6) * clamp(z * 1.2) * (0.35 + 0.65 * pulse)
        c = (CYAN, VIOLET, BLUE)[i % 3]
        pts = [(540 - hw, 860 - hh), (540 + hw, 860 - hh), (540 + hw, 860 + hh), (540 - hw, 860 + hh)]
        gpoly(G, pts, c, 1.5 + 4 / z, a * 0.6, closed=True)
    r = np.random.default_rng(5)
    angs = r.random(46) * 2 * math.pi
    offs = r.random(46)
    for i in range(46):
        rr = ((offs[i] + t * 1.1) % 1.0) ** 2 * 1500
        ln = 30 + rr * 0.35
        c, s = math.cos(angs[i]), math.sin(angs[i])
        gline(G, (540 + c * rr, 860 + s * rr), (540 + c * (rr + ln), 860 + s * (rr + ln)),
              WHITE if i % 4 == 0 else CYAN, 2.0, 0.55 * clamp(rr / 200))

def wtime(word):
    for w in WORDS[3]["words"]:
        if w["w"].lower().startswith(word):
            return w["s"]
    raise KeyError(word)

def kinetic(cv, t):
    groups = [
        # (key, text, size, y, start, end, top, bottom, entry)
        ("k_smarter", "SMARTER", 190, 700, wtime("smarter"), 19.55, WHITE, ICE, "slam"),
        ("k_ideas", "IDEAS.", 170, 900, wtime("ideas"), 19.55, CYAN, VIOLET, "rise"),
        ("k_new", "NEW", 290, 650, wtime("new"), 20.62, WHITE, ICE, "flip"),
        ("k_poss", "POSSIBILITIES.", 104, 870, wtime("possibilities"), 20.62, CYAN, BLUE, "slide"),
        ("k_one", "ONE PLACE", 160, 660, wtime("one"), 22.42, WHITE, ICE, "slam"),
        ("k_start", "TO GET STARTED", 92, 920, wtime("to"), 22.42, CYAN, VIOLET, "rise"),
    ]
    for key, text, size, y, t0, t1, top, bot, entry in groups:
        if not (t0 - 0.02 <= t < t1 + 0.2):
            continue
        u = prog(t, t0, 0.45)
        o = prog(t, t1, 0.2)
        spr = txt(key, text, F_BLACK, size, top, bot, ext=True)
        x, sc, rx, ry, rz, blur = 540.0, 1.0, 0.0, 0.0, 0.0, (0, 0)
        if entry == "slam":
            sc = lerp(2.4, 1, e_out_elastic(u, 0.42)); rz = lerp(-8, -2, e_out_cubic(u))
        elif entry == "rise":
            y = y + 260 * (1 - e_out_back(u, 2.2)); blur = (0, (1 - e_out_expo(u)) * 90)
        elif entry == "flip":
            rx = lerp(-95, 0, e_out_back(u, 1.6)); sc = lerp(0.6, 1, e_out_back(u))
        elif entry == "slide":
            x = lerp(-700, 540, e_out_expo(u)); blur = ((1 - e_out_expo(u)) * 160, 0)
        ry += 8 * math.sin(t * 1.7 + size)
        # beat bounce
        sc *= 1 + 0.035 * math.exp(-((t % T.BEAT) * 12))
        # exits: whip left / zoom through
        if o > 0:
            if key in ("k_smarter", "k_ideas"):
                x -= 1400 * e_in_expo(o); blur = (180 * o, 0)
            elif key in ("k_new", "k_poss"):
                sc *= 1 + 5 * e_in_expo(o)
            else:
                y -= 900 * e_in_expo(o); blur = (0, 150 * o)
        put(cv, key, spr, x, y, sc, rx, ry, rz, alpha=clamp(u * 5) * (1 - o * 0.9), glow_amt=0.5, blur=blur)

def scene4(t):
    cv = make_bg(*BG4).copy()
    G = new_glow()
    pulse = math.exp(-((t % T.BEAT) * 7))
    tunnel(G, t, pulse)
    for sw in T.S4_SWEEPS:
        u = prog(t, sw, 0.45)
        if 0 < u < 1:
            x = lerp(-300, 1380, e_in_out_cubic(u))
            for k, c in enumerate((CYAN, VIOLET, WHITE)):
                gline(G, (x - 200 - k * 60, 1700), (x + 200 - k * 60, 120), c, 6 - k * 1.5, 0.9 * math.sin(math.pi * u))
    flush_glow(cv, G, bloom=1.0)
    kinetic(cv, t)
    # 22.4 -> 25: rotating 3D wordmark with beat pulses
    if t >= 22.38:
        u = prog(t, 22.38, 0.6)
        ry = lerp(-75, 0, e_out_back(u, 1.3)) + 22 * math.sin((t - 22.4) * 1.6)
        sc = lerp(0.4, 1, e_out_elastic(u, 0.5)) * (1 + 0.04 * pulse)
        spr = txt("big_wm", "VANTARA", F_BLACK, 168, WHITE, ICE, ext=True)
        spr2 = txt("big_ai", "AI", F_BLACK, 220, CYAN, VIOLET, ext=True)
        put(cv, "big_wm", spr, 540, 760, sc, rx=8 * math.sin(t * 1.3), ry=ry, alpha=clamp(u * 4), glow_amt=0.4 + 0.4 * pulse)
        put(cv, "big_ai", spr2, 540, 990, sc, rx=8 * math.sin(t * 1.3), ry=-ry * 0.7, alpha=clamp(u * 4), glow_amt=0.5 + 0.4 * pulse)
    return cv

# ------------------------------------------------------------------ scene 5: CTA
def scene5(t):
    cv = make_bg(*BG5).copy()
    G = new_glow()
    grid_floor(G, t, horizon=1250, speed=0.6, a=0.35, col=BLUE)
    dust(G, t, 0.7)
    for i, (c, a, w) in enumerate(((CYAN, 0.95, 2.5), (BLUE, 0.6, 7), (VIOLET, 0.35, 14))):
        u = e_out_cubic(prog(t, T.S5_SHOCK, 1.1 + i * 0.25))
        if 0 < u < 1:
            gcircle(G, (540, 560), 60 + 1200 * u, c, a * (1 - u), th=w * (1 - u) + 1)
    burst(G, t, T.S5_SHOCK, (540, 560), n=200, seed=11, speed=1400, life=2.0)
    # anamorphic streak through the emblem
    on = e_out_cubic(prog(t, T.S5_SHOCK, 0.5))
    fl = on * (0.75 + 0.25 * math.sin(t * 3))
    gline(G, (540 - 520 * on, 560), (540 + 520 * on, 560), ICE, 3, 0.7 * fl)
    gline(G, (540 - 360 * on, 560), (540 + 360 * on, 560), CYAN, 9, 0.35 * fl)
    k = e_out_expo(prog(t, T.S5_TAG + 0.2, 0.8))
    gline(G, (540 - 300 * k, 1062), (540 + 300 * k, 1062), CYAN, 2.5, 0.8)
    flush_glow(cv, G)
    u = prog(t, T.S5_SHOCK - 0.05, 0.9)
    put(cv, "emblem", emblem(), 540, 560, lerp(0.2, 0.85, e_out_elastic(u, 0.45)),
        rx=4 * math.sin(t * 1.2), ry=lerp(180, 0, e_out_expo(u)) + 6 * math.sin(t * 1.5), glow_amt=1.0, sigma=26)
    u = prog(t, T.S5_SHOCK + 0.2, 0.7)
    if u > 0:
        spr = txt("wm5", "VANTARA AI", F_BLACK, 150, WHITE, ICE, tracking=0.04, ext=True)
        put(cv, "wm5", spr, 540, 900, lerp(1.35, 1, e_out_expo(u)), rx=lerp(50, 0, e_out_cubic(u)),
            alpha=clamp(u * 3), glow_amt=0.6, sigma=20)
    # tagline letters fade/rise in sequence
    tag = "YOUR AI JOURNEY STARTS HERE"
    u = prog(t, T.S5_TAG, 0.9)
    if u > 0:
        spr = txt("tag", tag, F_BOLD, 44, ICE, CYAN, tracking=0.16)
        w = spr.shape[1]
        cut = spr.copy()
        cut[:, int(spr.shape[1] * e_out_cubic(u)):] = 0
        put(cv, "tag", cut, 540, 1010, 1.0, alpha=1, glow_amt=0.35)
    # URL pill
    u = prog(t, T.S5_URL, 0.6)
    if u > 0:
        pill = cached("urlpill", lambda: url_pill())
        sc = lerp(0.3, 1, e_out_elastic(u, 0.45))
        put(cv, "urlpill", pill, 540, 1170, sc, alpha=clamp(u * 4), glow_amt=0.9, sigma=20)
        # light sweep across the pill
        sw = ((t - T.S5_URL - 0.6) % 1.8) / 0.7
        if 0 < sw < 1:
            G3 = new_glow()
            x = lerp(300, 780, sw)
            gline(G3, (x - 20, 1215), (x + 20, 1125), WHITE, 10, 0.5 * math.sin(math.pi * sw))
            flush_glow(cv, G3, bloom=0.5)
    return cv

def url_pill():
    w, h = int(560 * S), int(118 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(20, 40, 90, 170), outline=(90, 210, 255, 255), width=int(3.5 * S))
    f = font(F_BOLD, int(56 * S))
    tw = f.getlength("vantaraai.dev")
    asc, desc = f.getmetrics()
    d.text(((w - tw) / 2, (h - asc - desc * 0.3) / 2), "vantaraai.dev", font=f, fill=(240, 250, 255, 255))
    a = np.asarray(im, np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    return np.pad(a, ((h // 2,) * 2, (h // 2,) * 2, (0, 0)))

# ------------------------------------------------------------------ camera & post
SHAKES = [(0.0, 16), (T.S1_STOP, 24), (T.S1_SCROLL, 14), (5.0, 16), (T.S2_BURST, 12), (10.0, 6),
          (18.0, 18), (T.S5_SHOCK, 22)]

def camera(t):
    """zoom, rotation (deg), dx, dy (design px), radial blur, dir blur (x,y), rgb split px, flash."""
    zoom, rot_, dx, dy, rad, dbl, rgb, flash = 1.0, 0.0, 0.0, 0.0, 0.0, (0, 0), 0.0, 0.0
    sh = list(SHAKES)
    try:
        sh += [(wtime(w), 7) for w in ("smarter", "new", "one")]
    except KeyError:
        pass
    x, y, r = shake(t, sh)
    dx += x; dy += y; rot_ += r
    for t0, amp in [(0.0, 14), (T.S1_STOP, 16), (T.S1_SCROLL, 10), (5.0, 8), (18.0, 10), (T.S5_SHOCK, 10)]:
        rgb += amp * bump(t, t0, 9)
    flash = max(0.45 * bump(t, 0.0, 14), 0.5 * bump(t, 5.0, 12), 0.45 * bump(t, 25.0, 11))
    if t < 5:
        u = prog(t, *T.S1_RAMP) if t >= T.S1_RAMP[0] else 0
        ramp = e_in_expo(u) if u > 0 else 0
        zoom = 1.0 + 0.05 * e_in_out_cubic(prog(t, 0.4, 3.4)) + 5.5 * ramp
        rad = 0.35 * ramp
        rgb += 18 * ramp
        zc = (540, 700)
    elif t < 10:
        u = prog(t, 5.0, 0.6)
        zoom = lerp(1.35, 1.0, e_out_expo(u)) * (1 + 0.06 * e_in_out_cubic(prog(t, 5.6, 4.3)))
        rad = 0.25 * (1 - e_out_expo(u))
        zc = (540, 760)
    elif t < 18:
        zc = (540, 900)
        zoom = 1.0 + 0.04 * e_in_out_cubic(prog(t, 10, 8))
        if t > 17.62:  # whip up into scene 4
            k = e_in_expo(prog(t, 17.62, 0.38))
            dy -= 1500 * k; dbl = (0, 140 * k)
    elif t < 25:
        zc = (540, 860)
        if t < 18.32:
            k = 1 - e_out_expo(prog(t, 18.0, 0.32))
            dy += 1500 * k; dbl = (0, 140 * k)
        zoom = 1.0 + 0.03 * math.exp(-((t % T.BEAT) * 8))
        u = prog(t, *T.S4_RISER)
        if u > 0:
            zoom *= 1 + 2.2 * e_in_expo(u)
            rad = 0.3 * e_in_expo(u)
            rgb += 14 * e_in_expo(u)
    else:
        zc = (540, 700)
        zoom = 1.0 + 0.09 * e_in_out_cubic(prog(t, 25.3, 4.6))
        u = prog(t, 25.0, 0.5)
        zoom *= lerp(1.3, 1.0, e_out_expo(u)); rad = max(rad, 0.2 * (1 - e_out_expo(u)))
    return dict(zoom=zoom, rot=rot_, dx=dx, dy=dy, zc=zc, rad=rad, dbl=dbl, rgb=rgb, flash=flash)

def apply_camera(cv, c):
    z, cx, cy = c["zoom"], c["zc"][0] * S, c["zc"][1] * S
    M = cv2.getRotationMatrix2D((cx, cy), c["rot"], z)
    M[0, 2] += c["dx"] * S; M[1, 2] += c["dy"] * S
    if abs(z - 1) > 1e-4 or abs(c["rot"]) > 1e-3 or abs(c["dx"]) + abs(c["dy"]) > 0.05:
        cv = cv2.warpAffine(cv, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if c["rad"] > 0.01:   # zoom blur: average of progressively scaled copies (half res)
        hw, hh = W // 2, H // 2
        small = cv2.resize(cv, (hw, hh), interpolation=cv2.INTER_AREA)
        acc = np.zeros_like(small)
        n = 8
        for i in range(n):
            s = 1 + c["rad"] * i / n
            Mi = cv2.getRotationMatrix2D((cx / 2, cy / 2), 0, s)
            acc += cv2.warpAffine(small, Mi, (hw, hh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        cv = cv2.resize(acc / n, (W, H), interpolation=cv2.INTER_LINEAR)
    bx, by = c["dbl"]
    if bx + by > 2:
        cv = cv2.blur(cv, (max(1, int(bx * S)), max(1, int(by * S))))
    return cv

def post(cv, c, t, fi):
    # bloom
    small = cv2.resize(cv, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    br = np.maximum(small - 0.55, 0)
    br = cv2.GaussianBlur(br, (0, 0), 4 * S)
    cv += cv2.resize(br, (W, H), interpolation=cv2.INTER_LINEAR) * 0.55
    if c["flash"] > 0.01:
        cv *= 1 - c["flash"]
        cv += np.array(ICE, np.float32) * c["flash"]
    d = int(c["rgb"] * S * 0.5)
    if d >= 1:
        out = cv.copy()
        out[:, d:, 0] = cv[:, :-d, 0]
        out[:, :-d, 2] = cv[:, d:, 2]
        cv = out
    # brief horizontal glitch bands on the hardest hits
    gl = max(bump(t, 0.0, 16), bump(t, T.S1_SCROLL, 18), prog(t, 24.55, 0.45) * (t < 25.0))
    if gl > 0.15:
        r = np.random.default_rng(fi)
        for _ in range(4):
            y0 = int(r.random() * H); hh = int((20 + r.random() * 90) * S)
            sh = int((r.random() - 0.5) * 120 * S * gl)
            cv[y0:y0 + hh] = np.roll(cv[y0:y0 + hh], sh, axis=1)
    fade = clamp((T.DUR - t) / 0.35)
    if fade < 1:
        cv *= fade
    return cv

# ------------------------------------------------------------------ transitions
@functools.lru_cache(1)
def grids():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return xx, yy

def liquid(cv, amt, t):
    if amt < 0.01:
        return cv
    xx, yy = grids()
    A_ = 70 * S * amt
    mx = xx + A_ * np.sin(yy / (210 * S) + t * 9).astype(np.float32)
    my = yy + A_ * 0.6 * np.sin(xx / (160 * S) + t * 7).astype(np.float32)
    return cv2.remap(cv, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def shockwave(cv, t):
    u = prog(t, T.S5_SHOCK, 0.9)
    if not (0 < u < 1):
        return cv
    xx, yy = grids()
    cx, cy = 540 * S, 560 * S
    dx, dy = xx - cx, yy - cy
    d = np.sqrt(dx * dx + dy * dy) + 1e-3
    R = (60 + 1200 * e_out_cubic(u)) * S
    wdt = 70 * S
    off = (40 * S * (1 - u)) * np.exp(-((d - R) / wdt) ** 2)
    return cv2.remap(cv, xx - dx / d * off, yy - dy / d * off, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

SCENE_FN = [scene1, scene2, scene3, scene4, scene5]

def frame(fi):
    t = fi / T.FPS
    m0, m1 = T.S2_MORPH
    if m0 <= t < m1:
        u = (t - m0) / (m1 - m0)
        mix = e_in_out_cubic(clamp((u - 0.35) / 0.3))
        a = scene2(t) if mix < 1 else None
        b = scene3(t) if mix > 0 else None
        cv = a if b is None else b if a is None else a * (1 - mix) + b * mix
        cv = liquid(cv, math.sin(math.pi * u), t)
    else:
        idx = max(i for i, (s0, _) in enumerate(T.SCENES) if t >= s0)
        cv = SCENE_FN[idx](t)
    c = camera(t)
    cv = apply_camera(cv, c)
    cv = shockwave(cv, t)
    draw_subs(cv, t)
    cv = post(cv, c, t, fi)
    return cv2.convertScaleAbs(cv, alpha=255)

# ------------------------------------------------------------------ drivers
def preview(times):
    os.makedirs(os.path.join(B, "preview"), exist_ok=True)
    for t in times:
        img = frame(int(round(t * T.FPS)))
        p = os.path.join(B, "preview", f"t{t:05.2f}.png")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print(p)

def render_range(args):
    k, f0, f1 = args
    out = os.path.join(B, f"seg_{k:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(T.FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-profile:v", "high", "-level", "5.2",
           "-x264-params", "threads=2", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-r", str(T.FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for fi in range(f0, f1):
        p.stdin.write(frame(fi).tobytes())
        if (fi - f0) % 30 == 0:
            print(f"seg {k}: frame {fi} ({fi - f0}/{f1 - f0}) {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    return out

def render(workers=4):
    from multiprocessing import Pool
    n = int(T.DUR * T.FPS)
    # interleave short chunks so heavy scenes are spread across workers
    chunk = 60
    jobs = [(k, f, min(n, f + chunk)) for k, f in enumerate(range(0, n, chunk))]
    with Pool(workers) as pool:
        segs = pool.map(render_range, jobs, chunksize=1)
    lst = os.path.join(B, "segs.txt")
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", os.path.join(B, "video.mp4")], check=True)
    print("video ok")

if __name__ == "__main__":
    if sys.argv[1] == "--preview":
        preview([float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "--render":
        render(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
