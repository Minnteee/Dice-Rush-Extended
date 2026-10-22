"""Dice Shaker - 60 tarot cards (Area 3 of work/shaker_art_spec.md).

  art/tarot/<id>.png   30 fortune cards (deep purple, ornate gold frame, roman numeral I..XXX)
  art/black/<id>.png   30 black market cards (charcoal, rusty iron frame, red wax seal)
  art/tarot/back.png, art/black/back.png   card backs
  art/tarot/contact_sheet.png, art/black/contact_sheet.png   (x3, labelled with the ids)
  art/tarot/_preview_sizes.png, art/black/_preview_sizes.png (x1 / x2 / x5 checks)

Every card is 51x79 px, opaque RGBA (hard alpha) except the 3 rounded-off pixels in each corner.
Pure numpy + Pillow, deterministic (no randomness except a fixed integer hash).
Run:  tools\\venv\\Scripts\\python.exe tools\\shaker_art\\gen_tarot.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT_ROOT = os.path.join(REPO, 'build', 'generated', 'shaker', 'art')
OUT_T = os.path.join(OUT_ROOT, 'tarot')
OUT_B = os.path.join(OUT_ROOT, 'black')

W, H = 51, 79
YY, XX = np.mgrid[0:H, 0:W]
PX = XX + 0.5          # pixel centres
PY = YY + 0.5
B4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0
BAYER = B4[YY % 4, XX % 4]


# =====================================================================================  colours
def hexc(s, a=255):
    if isinstance(s, (tuple, list, np.ndarray)):
        s = tuple(int(v) for v in s)
        return s if len(s) == 4 else s + (a,)
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def mix(c1, c2, t):
    c1, c2 = hexc(c1), hexc(c2)
    return tuple(int(round(c1[i] * (1 - t) + c2[i] * t)) for i in range(3)) + (255,)


def hsh(x, y, seed=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + int(seed) * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFFFF) / float(0x1000000)


HASH = np.vectorize(hsh)(XX, YY, 7)


# =====================================================================================  masks
def nb(m, dx, dy):
    """r[y, x] = m[y+dy, x+dx]  (False outside)."""
    r = np.zeros_like(m)
    h, w = m.shape
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    r[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return r


def erode(m, diag=False):
    r = m & nb(m, 1, 0) & nb(m, -1, 0) & nb(m, 0, 1) & nb(m, 0, -1)
    if diag:
        r &= nb(m, 1, 1) & nb(m, -1, -1) & nb(m, 1, -1) & nb(m, -1, 1)
    return r


def dilate(m, diag=False):
    r = m | nb(m, 1, 0) | nb(m, -1, 0) | nb(m, 0, 1) | nb(m, 0, -1)
    if diag:
        r |= nb(m, 1, 1) | nb(m, -1, -1) | nb(m, 1, -1) | nb(m, -1, 1)
    return r


def border(m, diag=False):
    return m & ~erode(m, diag)


def E(cx, cy, rx, ry=None, k=0.0):
    """ellipse; (cx, cy) in pixel-edge coords, so cx=25.5 is the centre of pixel 25."""
    ry = rx if ry is None else ry
    return ((PX - cx) / rx) ** 2 + ((PY - cy) / ry) ** 2 <= 1.0 + k


def C(cx, cy, r, k=0.0):
    return E(cx, cy, r, r, k)


def RING(cx, cy, r0, r1, ry0=None, ry1=None):
    return E(cx, cy, r1, ry1 if ry1 else r1) & ~E(cx, cy, r0, ry0 if ry0 else r0)


def P(pts):
    """polygon (even-odd, pixel centre test)."""
    ins = np.zeros((H, W), bool)
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if y0 == y1:
            continue
        cond = ((y0 <= PY) & (PY < y1)) | ((y1 <= PY) & (PY < y0))
        xi = x0 + (PY - y0) * (x1 - x0) / (y1 - y0)
        ins ^= cond & (PX < xi)
    return ins


def R(x0, y0, x1, y1):
    """inclusive pixel rectangle."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    return (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)


def SEG(x0, y0, x1, y1):
    """1px Bresenham line between pixel coords."""
    m = np.zeros((H, W), bool)
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < W and 0 <= y0 < H:
            m[y0, x0] = True
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return m


def POLYL(pts, closed=False):
    m = np.zeros((H, W), bool)
    n = len(pts)
    for i in range(n - (0 if closed else 1)):
        m |= SEG(*pts[i], *pts[(i + 1) % n])
    return m


def TH(x0, y0, x1, y1, w):
    """thick line (capsule), endpoints in pixel-edge coords."""
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    if L2 == 0:
        t = 0
    else:
        t = np.clip(((PX - x0) * vx + (PY - y0) * vy) / L2, 0, 1)
    dx = PX - (x0 + t * vx)
    dy = PY - (y0 + t * vy)
    return dx * dx + dy * dy <= (w / 2.0) ** 2


def THP(pts, w):
    m = np.zeros((H, W), bool)
    for i in range(len(pts) - 1):
        m |= TH(*pts[i], *pts[i + 1], w)
    return m


def bez(p0, p1, p2, p3=None, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0]
                 + t ** 3 * p3[0])
            y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1]
                 + t ** 3 * p3[1])
        out.append((x, y))
    return out


def ARC(cx, cy, r, a0, a1, w=1.0, ry=None):
    """arc band between angles a0..a1 (degrees, 0 = right, 90 = down)."""
    ry = r if ry is None else ry
    ang = np.degrees(np.arctan2((PY - cy) / ry * r, PX - cx)) % 360
    a0 %= 360
    a1 %= 360
    inside = (ang >= a0) & (ang <= a1) if a0 <= a1 else (ang >= a0) | (ang <= a1)
    d = np.sqrt((PX - cx) ** 2 + ((PY - cy) * r / ry) ** 2)
    return inside & (np.abs(d - r) <= w / 2.0)


def pts_mask(pts):
    m = np.zeros((H, W), bool)
    for (x, y) in pts:
        if 0 <= x < W and 0 <= y < H:
            m[int(y), int(x)] = True
    return m


def ascii_mask(rows, x0, y0, ch='#'):
    m = np.zeros((H, W), bool)
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c in ch and 0 <= x0 + i < W and 0 <= y0 + j < H:
                m[y0 + j, x0 + i] = True
    return m


# =====================================================================================  fields
def f_sphere(cx, cy, rx, ry=None, lx=-0.55, ly=-0.7, lz=0.45, amb=0.12, spec=0.0):
    ry = rx if ry is None else ry
    nx = (PX - cx) / rx
    ny = (PY - cy) / ry
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    v = (nx * lx + ny * ly + nz * lz) / ln
    v = np.clip(v, 0, 1)
    return np.clip(amb + (1 - amb) * v, 0, 1)


def f_lin(x0, y0, x1, y1):
    """0 at (x0,y0) .. 1 at (x1,y1)."""
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    return np.clip(((PX - x0) * vx + (PY - y0) * vy) / L2, 0, 1)


def f_cyl(cx, r, hl=0.35):
    """vertical cylinder, light from the left: bright stripe at cx - hl*r."""
    t = (PX - cx) / r
    return np.clip(1 - np.abs(t + hl) * 0.95 - np.clip(t, 0, 1) * 0.25, 0, 1)


def f_rad(cx, cy, r, ry=None):
    ry = r if ry is None else ry
    return np.clip(1 - np.sqrt(((PX - cx) / r) ** 2 + ((PY - cy) / ry) ** 2), 0, 1)


def quant(field, n, dith=0.0):
    v = field * (n - 1) + 0.5
    if dith:
        v = v + (BAYER - 0.5) * dith
    return np.clip(np.floor(v), 0, n - 1).astype(int)


# =====================================================================================  layers
class Layer:
    """RGBA layer the size of the card; `occ` marks pixels that get the outline."""

    def __init__(self):
        self.c = np.zeros((H, W, 4), np.uint8)
        self.occ = np.zeros((H, W), bool)

    def put(self, m, col, occ=True):
        self.c[m] = hexc(col)
        if occ:
            self.occ |= m
        return self

    def ramp(self, m, ramp, lev, occ=True):
        """lev: int or int array; paints ramp[lev] inside m."""
        if np.isscalar(lev):
            return self.put(m, ramp[int(lev)], occ)
        lev = np.clip(lev, 0, len(ramp) - 1)
        for i, col in enumerate(ramp):
            mm = m & (lev == i)
            if mm.any():
                self.c[mm] = hexc(col)
        if occ:
            self.occ |= m
        return self

    def shade(self, m, ramp, field, dith=0.0, lo=0, hi=None, occ=True):
        hi = len(ramp) - 1 if hi is None else hi
        lev = lo + quant(field, hi - lo + 1, dith)
        return self.ramp(m, ramp, lev, occ)

    def bevel(self, m, ramp, base, up=1, dn=1, diag=False, occ=True):
        """flat fill with lighter top/left and darker bottom/right edge pixels."""
        self.put(m, ramp[base], occ)
        top = m & ~nb(m, 0, -1)
        left = m & ~nb(m, -1, 0)
        bot = m & ~nb(m, 0, 1)
        right = m & ~nb(m, 1, 0)
        if dn:
            self.c[(bot | right)] = hexc(ramp[max(0, base - dn)])
        if up:
            self.c[(top | left) & ~(bot | right)] = hexc(ramp[min(len(ramp) - 1, base + up)])
        return self

    def erase(self, m):
        self.c[m] = 0
        self.occ &= ~m
        return self

    def mask(self):
        return self.c[:, :, 3] > 0

    def outline(self, col, diag=False, inner=None):
        ring = dilate(self.occ, diag) & ~self.occ & ~self.mask()
        self.c[ring] = hexc(col)
        return self

    def under(self, other):
        """composite self over other (other is a Layer or ndarray), result in other."""
        dst = other.c if isinstance(other, Layer) else other
        m = self.c[:, :, 3] > 0
        dst[m] = self.c[m]
        return other


def comp(dst, layer, clip=None):
    m = layer.c[:, :, 3] > 0
    if clip is not None:
        m &= clip
    dst[m] = layer.c[m]


# =====================================================================================  palettes
# fortune set
FO = '#130920'                                                                  # outline
BGF = ['#140a22', '#190d2b', '#1f1035', '#25133f', '#2c1849', '#341d55', '#3d2462']
GOLD = ['#2e1607', '#5f350f', '#995b19', '#cc8b27', '#efbb48', '#ffe697']
GEMV = ['#3a1060', '#6a2aa8', '#a463e8', '#e0b8ff']                              # violet gem
STARC = ['#4a3878', '#7d68b8', '#c4b4f4', '#fffbe8']

# black market set
BO = '#070506'
BGB = ['#0c0a0c', '#110e10', '#151214', '#1a1618', '#201a1c', '#271e20', '#30211f']
RUST = ['#1f0907', '#3b120c', '#5a1d11', '#7c2b17', '#9e4020', '#bf5e2e', '#d98048']
IRON = ['#151316', '#2a272b', '#454147', '#686269', '#958d93']
WAX = ['#2a0306', '#540a0f', '#8a1218', '#bd2027', '#e8463f', '#ff8f7a']


def card_shape():
    m = np.ones((H, W), bool)
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (W - 1, 0, -1, 1), (0, H - 1, 1, -1), (W - 1, H - 1, -1, -1)):
        for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
            m[cy + sy * dy, cx + sx * dx] = False
    return m


SHAPE = card_shape()


def rings(m, n):
    """list of n successive 1px border rings of mask m (outermost first) + the rest."""
    out = []
    cur = m.copy()
    for _ in range(n):
        b = border(cur)
        out.append(b)
        cur = cur & ~b
    return out, cur


SIDE_TL = np.minimum(XX, YY) <= np.minimum(W - 1 - XX, H - 1 - YY)


# =====================================================================================  numerals
NUM = {
    'I': ['#', '#', '#', '#', '#'],
    'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
}


def roman(n):
    out = ''
    for v, s in ((10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')):
        while n >= v:
            out += s
            n -= v
    return out


def numeral_mask(text, cx, y):
    w = sum(len(NUM[c][0]) for c in text) + len(text) - 1
    x = cx - w // 2
    m = np.zeros((H, W), bool)
    for c in text:
        g = NUM[c]
        m |= ascii_mask(g, x, y)
        x += len(g[0]) + 1
    return m, cx - w // 2, w


# =====================================================================================  fortune frame
ART_F = R(5, 5, W - 6, H - 6)        # inside of the gold band


def fortune_background(seed=0):
    a = np.zeros((H, W, 4), np.uint8)
    f = f_rad(25.5, 40.0, 34, 44)
    lev = quant(f ** 0.9, len(BGF) - 1, dith=1.0)
    for i, col in enumerate(BGF[:-1]):
        a[lev == i] = hexc(col)
    return a


def halo_fortune(a, cx=25.5, cy=40.0, r=17.5):
    """quiet moon-disc behind the motif: slightly lighter disc + thin ring."""
    disc = C(cx, cy, r - 0.5)
    inner = f_rad(cx, cy, r)
    lev = quant(np.clip(inner * 1.6, 0, 1), 2, dith=1.0)
    a[disc & (lev == 0)] = hexc(BGF[4])
    a[disc & (lev == 1)] = hexc(BGF[5])
    ring = C(cx, cy, r + 0.5) & ~C(cx, cy, r - 0.5)
    a[ring] = hexc(BGF[6])
    for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        x = int(cx + dx * (r + 1.5))
        y = int(cy + dy * (r + 1.5))
        a[y, x] = hexc(STARC[1])


def fortune_frame(a, numeral=None):
    sh = SHAPE
    rg, inner = rings(sh, 5)
    a[~sh] = 0
    a[rg[0]] = hexc(FO)
    a[rg[1] & SIDE_TL] = hexc(GOLD[5])
    a[rg[1] & ~SIDE_TL] = hexc(GOLD[3])
    a[rg[2]] = hexc(GOLD[4])
    a[rg[2] & ~SIDE_TL] = hexc(GOLD[3])
    a[rg[3] & SIDE_TL] = hexc(GOLD[2])
    a[rg[3] & ~SIDE_TL] = hexc(GOLD[4])
    a[rg[4]] = hexc(FO)
    hl = border(R(6, 6, W - 7, H - 7))
    a[hl] = hexc(BGF[5])

    # --- corner bosses (diamond with violet gem)
    for (cx, cy) in ((4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)):
        man = np.abs(PX - cx) + np.abs(PY - cy)
        dia = man <= 3.6
        a[dilate(dia) & ~dia & (man <= 5)] = hexc(FO)
        a[dia] = hexc(GOLD[4])
        a[dia & ((PX - cx) + (PY - cy) > 1.5)] = hexc(GOLD[3])
        a[dia & ((PX - cx) + (PY - cy) < -1.5)] = hexc(GOLD[5])
        gem = man <= 1.6
        a[gem] = hexc(GEMV[1])
        a[int(cy), int(cx)] = hexc(GEMV[2])
        a[int(cy) - 1, int(cx)] = hexc(GEMV[3])

    # --- side studs
    for cx in (2.5, W - 2.5):
        st = (np.abs(PX - cx) * 1.6 + np.abs(PY - 40.0) <= 3.2)
        a[dilate(st) & ~st & (np.abs(PX - cx) <= 3)] = hexc(FO)
        a[st] = hexc(GOLD[4])
        a[st & (PY > 40.0)] = hexc(GOLD[3])
        a[39, int(cx)] = hexc(GOLD[5])

    # --- top cartouche with the numeral
    cart = P([(10.5, 6.5), (15.0, 0.0), (36.0, 0.0), (40.5, 6.5), (36.0, 13.0), (15.0, 13.0)])
    cart &= sh
    a[cart] = hexc(FO)
    c1 = erode(cart) & (YY >= 1)
    a[c1] = hexc(GOLD[4])
    a[c1 & (PY > 6.5)] = hexc(GOLD[3])
    a[c1 & ~nb(c1, 0, -1) & (PY < 3)] = hexc(GOLD[5])
    c2 = erode(c1) & (YY >= 2)
    a[c2] = hexc(GOLD[1])
    c3 = erode(c2) & (YY >= 3)
    a[c3] = hexc('#1a0c2b')
    if numeral:
        txt = roman(numeral)
        nm, x0, w = numeral_mask(txt, 25, 4)
        rule = R(x0 - 1, 2, x0 + w, 2) | R(x0 - 1, 10, x0 + w, 10)
        a[rule & c2] = hexc(GOLD[3])
        a[nm] = hexc(GOLD[5])
        a[nm & (YY >= 7)] = hexc(GOLD[4])
    else:
        moon = C(25.5, 6.5, 3.2) & ~C(27.0, 5.6, 2.8)
        a[moon] = hexc(GOLD[5])

    # --- bottom medallion with crescent moon
    med = C(25.5, 73.5, 5.6)
    med &= sh
    a[dilate(med) & sh & ~med] = hexc(FO)
    a[med] = hexc(GOLD[4])
    a[med & (PY > 73.5)] = hexc(GOLD[3])
    a[med & ~nb(med, 0, -1)] = hexc(GOLD[5])
    mi = C(25.5, 73.5, 4.0)
    a[mi] = hexc('#1a0c2b')
    moon = C(25.5, 73.5, 3.1) & ~C(26.9, 72.6, 2.6)
    a[moon] = hexc(GOLD[5])
    a[moon & (PY > 74.5)] = hexc(GOLD[4])
    return a


def place_stars(a, free, seed, n_small=9, n_spark=3, area=None):
    """scatter a few calm stars on free background pixels (deterministic)."""
    area = ART_F if area is None else area
    ok = free & area & erode(erode(free, True), True)
    cand = [(x, y) for y in range(H) for x in range(W) if ok[y, x]]
    if not cand:
        return
    cand.sort(key=lambda p: hsh(p[0], p[1], seed))
    used = []

    def far(p, d):
        return all(abs(p[0] - q[0]) + abs(p[1] - q[1]) >= d for q in used)
    k = 0
    for p in cand:
        if k >= n_spark:
            break
        if not far(p, 14):
            continue
        x, y = p
        a[y, x] = hexc(STARC[3])
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a[y + dy, x + dx] = hexc(STARC[1])
        used.append(p)
        k += 1
    k = 0
    for p in cand:
        if k >= n_small:
            break
        if not far(p, 9):
            continue
        x, y = p
        a[y, x] = hexc(STARC[2] if hsh(x, y, seed + 3) < 0.4 else STARC[1])
        used.append(p)
        k += 1


# =====================================================================================  black frame
def black_background(seed=0):
    a = np.zeros((H, W, 4), np.uint8)
    f = f_rad(25.5, 39.0, 30, 40)
    g = np.clip(f + (HASH - 0.5) * 0.10, 0, 1)
    lev = quant(g ** 1.1, len(BGB) - 1, dith=0.9)
    for i, col in enumerate(BGB[:-1]):
        a[lev == i] = hexc(col)
    return a


def glow_black(a, cx=25.5, cy=40.0, r=18.0, col=None):
    """dim red lamp glow behind the motif."""
    f = f_rad(cx, cy, r)
    lev = quant(np.clip(f * 1.5, 0, 1), 3, dith=1.0)
    cols = ['#211416', '#2b1517'] if col is None else col
    for i in (1, 2):
        m = (lev == i) & (f > 0)
        a[m] = hexc(cols[i - 1])


SKULL5 = ['.###.', '#####', '#.#.#', '#####', '.#.#.']


def wax_seal(a, cx, cy, r=5.6, emblem='skull'):
    """round red wax seal with two small drips, a pressed centre and an embossed skull.
    (cx, cy) = centre in edge coords (cx = k + 0.5 is the centre of pixel k)."""
    blob = C(cx, cy, r)
    for (ang, dr, rr) in ((128, 5.0, 1.7), (28, 5.3, 1.4), (250, 5.2, 1.2)):
        t = math.radians(ang)
        blob |= C(cx + dr * math.cos(t), cy + dr * math.sin(t), rr)
    a[dilate(blob, True) & ~blob & SHAPE] = hexc(BO)
    a[blob] = hexc(WAX[3])
    a[blob & ~nb(blob, 1, 1)] = hexc(WAX[2])
    a[blob & ~nb(blob, 0, 1)] = hexc(WAX[1])
    a[blob & ~nb(blob, -1, -1)] = hexc(WAX[4])
    a[blob & ~nb(blob, 0, -1) & (PX < cx)] = hexc(WAX[5])
    disc = C(cx, cy, r - 1.7)
    a[disc] = hexc(WAX[2])
    a[disc & ~nb(disc, -1, -1)] = hexc(WAX[1])
    a[disc & ~nb(disc, 1, 1)] = hexc(WAX[4])
    if emblem == 'skull':
        m = ascii_mask(SKULL5, int(cx) - 2, int(cy) - 2)
        a[m] = hexc(WAX[4])
        a[m & ~nb(m, 0, -1)] = hexc(WAX[5])
        a[m & ~nb(m, 0, 1)] = hexc(WAX[3])
    return blob


def black_frame(a, seal=True):
    sh = SHAPE
    rg, inner = rings(sh, 5)
    a[~sh] = 0
    a[rg[0]] = hexc(BO)
    band = rg[1] | rg[2] | rg[3]
    lev = np.zeros((H, W), int)
    lev[rg[1]] = np.where(SIDE_TL, 4, 3)[rg[1]]
    lev[rg[2]] = 3
    lev[rg[3]] = np.where(SIDE_TL, 2, 4)[rg[3]]
    pit = (HASH < 0.16) & band
    bright = (HASH > 0.90) & band
    lev[pit] -= 1
    lev[bright] += 1
    lev = np.clip(lev, 0, len(RUST) - 1)
    for i, col in enumerate(RUST):
        a[band & (lev == i)] = hexc(col)
    a[rg[4]] = hexc(BO)
    for (x, y) in ((3, 3), (W - 4, 3), (3, H - 4), (W - 4, H - 4), (3, 39), (W - 4, 39)):
        m = R(x - 1, y - 1, x + 1, y + 1)
        a[border(dilate(m, True), False) & band] = hexc(RUST[1])
        a[m] = hexc(IRON[2])
        a[y - 1, x - 1] = hexc(IRON[4])
        a[y - 1, x] = hexc(IRON[3])
        a[y, x - 1] = hexc(IRON[3])
        a[y + 1, x + 1] = hexc(IRON[1])
    if seal:
        # riveted iron lock plate at the top centre
        plate = R(18, 0, 32, 8) & SHAPE
        a[dilate(plate) & ~plate & SHAPE & (YY <= 9)] = hexc(BO)
        a[plate] = hexc(IRON[2])
        a[plate & (YY <= 1)] = hexc(IRON[3])
        a[plate & (YY == 0)] = hexc(BO)
        a[plate & (XX == 18)] = hexc(IRON[3])
        a[plate & ((YY == 8) | (XX == 32))] = hexc(IRON[1])
        for x in (20, 30):
            a[4, x] = hexc(IRON[4])
            a[5, x] = hexc(IRON[1])
        a[R(22, 4, 28, 4)] = hexc(BO)
        a[R(22, 5, 28, 5)] = hexc(IRON[3])
        a[R(22, 3, 28, 3)] = hexc(IRON[1])
        wax_seal(a, W - 7.5, H - 8.5)
    return a


EMBER = ['#3a1612', '#5a2018', '#8a3020']


def place_embers(a, free, seed, n=7):
    """a few dim red embers on free background pixels (black market counterpart of the stars)."""
    ok = free & INNER & erode(erode(free, True), True) & (YY > 12) & ~(C(W - 7.5, H - 8.5, 9.0))
    cand = [(x, y) for y in range(H) for x in range(W) if ok[y, x]]
    cand.sort(key=lambda p: hsh(p[0], p[1], seed))
    used = []
    for (x, y) in cand:
        if len(used) >= n:
            break
        if any(abs(x - u) + abs(y - v) < 10 for (u, v) in used):
            continue
        k = 2 if hsh(x, y, seed + 1) < 0.3 else (1 if hsh(x, y, seed + 2) < 0.6 else 0)
        a[y, x] = hexc(EMBER[k])
        if k == 2:
            a[y - 1, x] = hexc(EMBER[0])
        used.append((x, y))


# =====================================================================================  previews
def upscale(a, s):
    im = Image.fromarray(a, 'RGBA')
    return im.resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)


def sheet(items, scale=3, cols=6, bg=(34, 26, 40, 255), label=True):
    cw, ch = W * scale, H * scale
    pad = 8
    lh = 16 if label else 0
    rows = (len(items) + cols - 1) // cols
    im = Image.new('RGBA', (cols * (cw + pad) + pad, rows * (ch + lh + pad) + pad), bg)
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype('arial.ttf', 12)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (lab, a) in enumerate(items):
        r, c = divmod(i, cols)
        x = pad + c * (cw + pad)
        y = pad + r * (ch + lh + pad)
        im.alpha_composite(upscale(a, scale), (x, y))
        if label:
            d.text((x + cw // 2, y + ch + 2), lab, fill=(236, 228, 210, 255), font=fnt, anchor='ma')
    return im


def dev_path(name):
    d = os.environ.get('TAROT_DEV')
    if not d:
        return None
    return '\\\\?\\' + os.path.join(d, name) if os.name == 'nt' and not d.startswith('\\\\?\\') else os.path.join(d, name)


# =====================================================================================  motif helpers
def MIR(m):
    """mirror a mask around the card's vertical centre line (x -> 50 - x)."""
    return m[:, ::-1]


def SYM(m):
    return m | MIR(m)


def glow(a, cx, cy, r, cols, ry=None, power=1.0, dith=1.0, clip=None):
    """radial glow painted into the background array: cols = dim .. bright."""
    f = f_rad(cx, cy, r, ry) ** power
    lev = quant(f, len(cols) + 1, dith)
    for i, col in enumerate(cols):
        m = (lev == i + 1) & (f > 0)
        if clip is not None:
            m &= clip
        a[m] = hexc(col)


def lens(cx, cy, w, h):
    """almond / eye shape (intersection of two circles), w and h = full size."""
    hw, hh = w / 2.0, h / 2.0
    r = (hw * hw + hh * hh) / (2 * hh)
    return C(cx, cy - hh + r, r) & C(cx, cy + hh - r, r)


def star_mask(cx, cy, r_out, r_in, n=5, rot=-90.0):
    pts = []
    for i in range(n * 2):
        rr = r_out if i % 2 == 0 else r_in
        ang = math.radians(rot + i * 180.0 / n)
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return P(pts), pts


def sparkle(a, x, y, big=False, cols=None):
    cols = cols or STARC
    a[y, x] = hexc(cols[3])
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a[y + dy, x + dx] = hexc(cols[2] if big else cols[1])
    if big:
        for (dx, dy) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            a[y + dy, x + dx] = hexc(cols[1])


# fortune motif ramps (dark -> light)
SILV = ['#24223a', '#45466a', '#7279a0', '#a9b2d4', '#e4eaff']
CRYS = ['#1a1f52', '#283f8a', '#3672bd', '#56a8e0', '#8edcf6', '#e0fbff']
FLM = ['#7a1408', '#c43a10', '#f27618', '#ffb23a', '#ffe07a', '#fffbe0']
WAXC = ['#4a3456', '#86708e', '#bfa9b8', '#e6d6d4', '#fff7ee']
RAVN = ['#0b0812', '#17122a', '#251f40', '#383260', '#5a5690']
MOTH = ['#1d3f3a', '#2f6a55', '#56a476', '#94d494', '#d6f5c4']
SKN = ['#4a2032', '#874458', '#c27378', '#eaa89e', '#ffdcc8']
RED = ['#3a0818', '#6e1028', '#a81e38', '#e04050', '#ff8a8a']
GRN = ['#0f2a22', '#1d4a32', '#2f7a44', '#56b05a', '#a4e07a']
BLU = ['#141e4a', '#243a8a', '#3a64c8', '#6aa0f0', '#b8dcff']
PNK = ['#4a1438', '#8a2a66', '#c85496', '#f08cc0', '#ffd0e8']
BRN = ['#24120a', '#4a2614', '#76401e', '#a8642c', '#d89450']
ORG = ['#4a1a08', '#8a3410', '#c85a18', '#f08a2a', '#ffc070']
STN = ['#221c34', '#3a3252', '#585074', '#8780a2', '#bab2d0']
CRM = ['#5a4a3a', '#9a8670', '#d0c0a0', '#f0e6cc', '#fffaf0']
IRN = ['#14121c', '#262434', '#3e3c52', '#62607c', '#9694b0']
PUR = ['#2a0e4a', '#4e1c80', '#7a34b8', '#aa64e8', '#d8b0ff']
TEA = ['#0e2e36', '#1a5058', '#2a7e80', '#4ab0a8', '#90e0d0']
SND = ['#5a2e0c', '#9a5a18', '#d89434', '#f8c860', '#fff0b0']
MOON = ['#4e4280', '#7a6eae', '#a89cd6', '#d4ccf2', '#f4f0ff']


# =====================================================================================  fortune motifs
def fm_crystal_ball(L, a):
    cx, cy, r = 25.5, 34.5, 12.0
    glow(a, cx, cy, 21, ['#2a1a50', '#30205c', '#372768', '#3f3076'])
    ball = C(cx, cy, r)
    core = np.clip(f_rad(cx + 1, cy + 1.5, r * 1.15) ** 0.9, 0, 1)
    L.shade(ball, CRYS, 0.12 + 0.8 * core, dith=1.0, hi=4)
    # violet mist swirl
    sw = (ARC(cx - 2.5, cy + 1.5, 5.5, 180, 360, 2.0) | ARC(cx + 2.5, cy - 1.0, 5.0, 0, 180, 2.0)) & C(cx, cy, r - 2)
    L.put(sw, '#c9a8ff')
    L.put(sw & (PY > cy + 2), '#a58ae8')
    # rims
    L.put(ball & ~C(cx - 0.8, cy - 0.8, r) , CRYS[4])
    L.put(ball & ~C(cx + 0.8, cy + 0.8, r) & (PY < cy) & (PX < cx), CRYS[1])
    # highlight crescent + dot
    L.put(ARC(cx, cy, r - 2.6, 200, 255, 1.6) & ball, CRYS[5])
    L.put(R(16, 28, 17, 29), '#ffffff')
    L.put(pts_mask([(30, 30), (22, 39)]), CRYS[5])
    # stand: cup collar, neck, base
    cup = E(cx, 45.5, 9.0, 3.0) & ~E(cx, 43.6, 7.0, 2.0)
    L.shade(cup, GOLD, f_cyl(cx, 9.0), hi=5, lo=1)
    neck = P([(21.5, 47), (29.5, 47), (28, 51), (23, 51)])
    L.shade(neck, GOLD, f_cyl(cx, 4.5), lo=1, hi=4)
    knot = E(cx, 51.5, 5.0, 1.6)
    L.shade(knot, GOLD, f_cyl(cx, 5.0), lo=2, hi=5)
    base = P([(18.5, 53), (32.5, 53), (36.5, 58), (14.5, 58)])
    L.shade(base, GOLD, f_cyl(cx, 11.0), lo=1, hi=4)
    L.put(R(15, 58, 36, 59), GOLD[1])
    L.put(R(16, 55, 35, 55) & base, GOLD[2])
    for x in (19, 25, 31):
        L.put(R(x, 55, x + 1, 55), GEMV[2])
    return {'halo': (cx, cy, 16.5)}


def fm_candle(L, a):
    cx = 25.5
    glow(a, cx, 21, 15, ['#2f1a4a', '#3a2050', '#472656', '#552c58'])
    body = R(19, 27, 31, 53)
    L.shade(body, WAXC, f_cyl(cx, 7.0, 0.3), lo=1, hi=4)
    top = E(cx, 27.0, 6.5, 2.2)
    L.put(top, WAXC[3])
    L.put(E(cx, 27.2, 4.5, 1.2), WAXC[2])
    drips = (TH(21.0, 28, 21.0, 33, 2.2) | TH(28.5, 28, 28.5, 37, 2.4) | TH(24.5, 28, 24.5, 31, 2.0)
             | TH(30.6, 27, 30.6, 31, 1.6))
    L.put(drips & body, WAXC[4])
    L.put(drips & ~nb(drips, 0, 1) & body, WAXC[2])
    # wick + flame
    L.put(R(25, 22, 25, 25), '#2a1a1a')
    fl = P([(25.5, 10.5), (28.5, 17.0), (28.0, 21.0), (25.5, 23.0), (23.0, 21.0), (22.5, 17.0)])
    L.shade(fl, FLM, f_rad(25.5, 19.5, 5.5, 7.5), lo=2, hi=5)
    L.put(E(25.5, 20.0, 1.2, 2.0), FLM[5])
    L.put(R(24, 22, 24, 22) | R(26, 22, 26, 22), '#5aa0ff')
    # holder dish + handle
    dish = E(cx, 55.5, 13.0, 3.6)
    L.shade(dish, GOLD, f_cyl(cx, 13.0), lo=1, hi=5)
    L.put(E(cx, 54.4, 8.0, 1.6) & dish, GOLD[2])
    L.put(body & (YY >= 53) & (YY <= 54), WAXC[1])
    rim = E(cx, 54.5, 13.0, 3.0) & ~E(cx, 54.0, 12.0, 2.4) & (PY < 54.5)
    L.put(rim, GOLD[5])
    hd = RING(40.5, 51.5, 1.6, 3.4)
    L.shade(hd, GOLD, f_sphere(40.5, 51.5, 3.4), lo=1, hi=5)
    foot = E(cx, 59.6, 7.0, 1.8)
    L.shade(foot, GOLD, f_cyl(cx, 7.0), lo=1, hi=3)
    return {'halo': (cx, 38.0, 17.0)}


def fm_raven(L, a):
    # pale moon behind
    mx, my, mr = 21.0, 27.5, 11.5
    moon = C(mx, my, mr)
    lev = quant(f_sphere(mx, my, mr, lx=-0.3, ly=-0.5, lz=0.8, amb=0.35), 4, dith=1.0)
    for i in range(4):
        a[moon & (lev == i)] = hexc(MOON[i])
    for (x, y, rr) in ((14.5, 31.5, 2.0), (26.5, 21.0, 1.6), (12.5, 23.5, 1.3)):
        a[C(x, y, rr) & moon] = hexc(MOON[1])
    branch = TH(6.5, 56.5, 45.0, 52.5, 3.0) | TH(36.0, 53.5, 41.0, 49.5, 1.6)
    L.shade(branch, BRN, f_lin(0, 51, 0, 58) * -1 + 1, lo=1, hi=3)
    L.put(E(42.0, 48.5, 2.2, 1.2), GRN[3])
    L.put(E(12.0, 54.0, 2.0, 1.2), GRN[2])
    body = P([(18, 33), (22, 29.5), (29, 29.5), (33.5, 34), (35, 41), (33, 47), (28, 50.5), (22, 48.5), (18.5, 42)])
    tail = P([(29, 46), (36, 50), (42.5, 58.5), (36.5, 59.5), (30, 53)])
    head = C(20.5, 25.5, 5.0)
    neck = P([(16.5, 27), (16, 33), (19.5, 38), (24.5, 31)])
    beak = P([(17.5, 22.5), (12, 23.8), (8.0, 26.2), (12.0, 26.6), (17.0, 28.6)])
    legs = TH(23.5, 48, 23.0, 53.5, 1.4) | TH(27.0, 49, 27.5, 53.0, 1.4)
    L.put(legs, RAVN[3])
    L.bevel(tail, RAVN, 1, up=1, dn=1)
    L.bevel(body | neck | head, RAVN, 1, up=2, dn=1)
    wing = P([(21, 33), (28.5, 31), (33.5, 35.5), (37.5, 45), (39, 53.5), (34, 51.5), (29, 47), (23.5, 41.5)])
    L.bevel(wing, RAVN, 2, up=1, dn=2)
    for (x0, y0, x1, y1) in ((26, 37, 34, 46), (25, 40, 32, 48), (29, 35, 36, 45)):
        L.put(SEG(x0, y0, x1, y1) & wing, RAVN[1])
    L.bevel(beak, ['#1a1624', '#3a3450', '#5e5a7a', '#8c88a8'], 1, up=2, dn=1)
    L.put(SEG(9, 26, 16, 25), '#1a1624')
    L.put(pts_mask([(19, 24)]), '#ffffff')
    L.put(pts_mask([(20, 24), (19, 25)]), RAVN[0])
    # throat hackles
    L.put(pts_mask([(16, 31), (17, 33), (16, 29)]), RAVN[2])
    return {'halo': False}


def fm_moon_moth(L, a):
    glow(a, 25.5, 38, 20, ['#251540', '#2c1a4a'])
    fw = P([(24.0, 30.0), (19.0, 23.5), (12.0, 19.0), (8.0, 20.5), (7.0, 26.0), (9.0, 33.0), (14.0, 38.0),
            (20.0, 39.5), (24.5, 37.5)])
    hw = P([(24.5, 37.0), (18.5, 39.0), (13.5, 43.0), (13.0, 49.0), (16.5, 52.0), (21.0, 50.5), (24.5, 45.0)])
    tail = THP(bez((17.5, 50.0), (13.5, 55.0), (16.0, 60.0), n=10), 3.0) | THP(bez((16.0, 60.0), (17.0, 63.0), (18.5, 64.0), n=6), 2.0)
    for m, base in ((SYM(hw | tail), 3), (SYM(fw), 3)):
        L.bevel(m, MOTH, base, up=1, dn=1)
    # leading edge purple
    edge = SYM(THP([(23.5, 30.0), (16.0, 22.0), (11.5, 19.5), (8.5, 20.8)], 1.6))
    L.put(edge & SYM(fw), '#9a7ad0')
    # veins
    for (x0, y0, x1, y1) in ((23, 33, 11, 25), (23, 35, 12, 34), (23, 41, 15, 47)):
        L.put(SYM(SEG(x0, y0, x1, y1)) & SYM(fw | hw), MOTH[2])
    # eye spots (little moons)
    for (x, y, r) in ((14.5, 29.0, 3.0), (18.5, 45.5, 2.2)):
        ring = SYM(C(x, y, r))
        L.put(ring, GOLD[4])
        L.put(SYM(C(x, y, r - 1.0)), '#3a2050')
        L.put(SYM(C(x, y, r - 1.0) & ~C(x + 1.0, y - 0.6, r - 1.2)), MOON[3])
    # body + head + antennae
    body = E(25.5, 39.0, 2.6, 9.0)
    L.shade(body, CRM, f_cyl(25.5, 2.6), lo=2, hi=4)
    for y in (36, 40, 44):
        L.put(R(24, y, 26, y) & body, CRM[1])
    L.put(C(25.5, 29.0, 2.3), CRM[3])
    ant = SYM(THP(bez((24.5, 27.5), (22.0, 21.0), (17.5, 17.0), n=10), 1.0))
    L.put(ant, GOLD[3])
    for (x, y) in ((22, 22), (21, 20), (19, 18)):
        L.put(SYM(pts_mask([(x - 1, y), (x, y - 1)])), GOLD[2])
    L.put(SYM(pts_mask([(24, 28)])), RAVN[0])
    return {'halo': (25.5, 40.0, 18.5)}


def fm_open_hand(L, a):
    glow(a, 25.5, 38, 19, ['#2c1a4c', '#33205a'])
    fingers = [((19.0, 38.0), (18.0, 22.0), 5.0), ((24.8, 37.0), (25.0, 18.5), 5.2),
               ((30.5, 38.0), (31.5, 21.5), 5.0), ((35.5, 41.0), (38.0, 28.5), 4.2)]
    palm = P([(14.5, 38.0), (37.5, 38.0), (38.0, 48.0), (35.0, 56.0), (17.0, 56.0), (14.5, 49.0)])
    thumb = TH(17.0, 47.0, 9.5, 36.5, 5.4)
    L.shade(thumb, SKN, f_cyl(12.0, 4.0), lo=1, hi=4)
    L.put(border(thumb) & ~nb(thumb, 1, 0), SKN[1])
    for (p0, p1, w) in fingers:
        m = TH(p0[0], p0[1], p1[0], p1[1], w)
        L.shade(m, SKN, f_cyl((p0[0] + p1[0]) / 2.0, w / 2.0, 0.2), lo=1, hi=4)
        L.put(m & ~nb(m, 1, 0), SKN[1])
        # nail hint / knuckle crease
        L.put(R(int(p1[0]) - 1, int(p1[1]) + 6, int(p1[0]), int(p1[1]) + 6) & m, SKN[2])
    L.shade(palm, SKN, 0.8 - 0.45 * f_lin(0, 40, 0, 56), lo=2, hi=4)
    L.put(border(palm) & (PY > 50), SKN[1])
    # eye in the palm
    eye = lens(25.5, 47.0, 13.0, 6.0)
    L.put(dilate(eye) & palm, SKN[0])
    L.put(eye, CRM[4])
    iris = C(25.5, 47.0, 2.6)
    L.shade(iris & eye, PUR, f_sphere(25.5, 47.0, 2.6), lo=1, hi=4)
    L.put(R(25, 46, 25, 47), '#120a1e')
    L.put(pts_mask([(24, 46)]), '#ffffff')
    # wrist, cuff, sleeve
    wrist = R(18, 56, 33, 58)
    L.shade(wrist, SKN, f_cyl(25.5, 8.0), lo=1, hi=3)
    cuff = R(16, 59, 35, 60)
    L.bevel(cuff, GOLD, 4, up=1, dn=2)
    sleeve = P([(15.5, 61), (35.5, 61), (39, 66), (12, 66)])
    L.bevel(sleeve, PUR, 2, up=1, dn=1)
    for x in range(17, 36, 4):
        L.put(R(x, 62, x, 62), GOLD[4])
    return {'halo': (25.5, 40.0, 18.5)}


def fm_third_eye(L, a):
    cx = 25.5
    # rays behind the triangle
    rays = np.zeros((H, W), bool)
    for k in range(12):
        ang = math.radians(-90 + k * 30 + 15)
        x0, y0 = cx + 15 * math.cos(ang), 41 + 15 * math.sin(ang)
        x1, y1 = cx + 21 * math.cos(ang), 41 + 21 * math.sin(ang)
        if y1 < 52:
            rays |= TH(x0, y0, x1, y1, 1.3)
    a[rays & ART_F] = hexc(GOLD[2])
    tri = P([(cx, 15.0), (6.0, 55.0), (45.0, 55.0)])
    tri_in = P([(cx, 21.5), (11.5, 52.0), (39.5, 52.0)])
    L.put(tri & ~tri_in, GOLD[4])
    band = tri & ~tri_in
    L.put(band & (PY > 50.5), GOLD[3])
    L.put(band & (PX > cx) & (PY < 50.5) & ~nb(tri, 1, 0), GOLD[2])
    L.put(band & ~nb(tri, -1, 0) & (PX < cx), GOLD[5])
    L.put(border(tri_in), GOLD[1])
    inside = erode(tri_in)
    L.shade(inside, ['#1c0d30', '#24123e', '#2e184c', '#3a2060'], f_rad(cx, 42, 14), dith=1.0)
    eye = lens(cx, 42.0, 20.0, 10.0)
    L.put(dilate(eye) & inside, FO)
    L.put(eye, CRM[4])
    L.put(eye & (PY > 44.5), CRM[3])
    iris = C(cx, 42.0, 4.2) & eye
    L.shade(iris, BLU, f_sphere(cx, 42.0, 4.2), lo=1, hi=4)
    L.put(C(cx, 42.0, 1.9), '#0c0818')
    L.put(R(23, 40, 24, 40), '#ffffff')
    lid = ARC(cx, 47.5, 10.6, 205, 335, 1.2) & ~eye
    L.put(lid & inside, GOLD[3])
    for x in (18, 22, 29, 33):
        L.put(pts_mask([(x, 35 if x in (22, 29) else 36)]), GOLD[3])
    return {'halo': False}


def fm_key(L, a):
    glow(a, 25.5, 40, 18, ['#2a1848', '#311d54'])
    bx, by, ex, ey = 17.5, 25.5, 38.5, 56.0           # bow centre -> shaft tip (diagonal)
    Lk = math.hypot(ex - bx, ey - by)
    u, v = uv(bx, by, ex, ey)
    s = u * Lk
    lit = np.clip(0.55 + v / 4.0, 0, 1)               # v > 0 is the upper-left (lit) side
    shaft = (s >= 7.0) & (s <= Lk) & (np.abs(v) <= 1.8)
    L.shade(shaft, GOLD, lit, lo=1, hi=5)
    for sc in (10.0, 14.0):
        col = (np.abs(s - sc) <= 1.0) & (np.abs(v) <= 3.6)
        L.shade(col, GOLD, lit, lo=2, hi=5)
    L.shade((np.abs(s - Lk) <= 1.6) & (np.abs(v) <= 2.4), GOLD, lit, lo=1, hi=4)
    bit = (s >= Lk - 10.0) & (s <= Lk - 1.0) & (v <= -1.5) & (v >= -8.0)
    bit &= ~((s >= Lk - 7.6) & (s <= Lk - 5.6) & (v < -4.6))
    bit &= ~((s >= Lk - 3.6) & (s <= Lk - 1.0) & (v < -6.0))
    L.bevel(bit, GOLD, 3, up=2, dn=2)
    bow = (C(bx - 4.5, by, 4.2) | C(bx + 4.5, by, 4.2) | C(bx, by - 4.5, 4.2) | C(bx, by + 4.5, 4.2))
    hole = C(bx, by, 3.0)
    L.shade(bow & ~hole, GOLD, f_sphere(bx, by, 9.0), lo=1, hi=5)
    for (x, y) in ((bx - 4.5, by), (bx + 4.5, by), (bx, by - 4.5), (bx, by + 4.5)):
        L.put(C(x, y, 1.4) & ~hole, GOLD[2])
    L.erase(hole)
    L.put(C(bx, by, 1.6), GEMV[1])
    L.put(pts_mask([(int(bx) - 1, int(by) - 1)]), GEMV[3])
    return {'halo': (25.5, 40.0, 18.0)}


def fm_hourglass(L, a):
    cx = 25.5
    glow(a, cx, 40, 17, ['#2a1848', '#311d54'])
    glass = (P([(16.0, 23.0), (35.0, 23.0), (34.5, 30.0), (27.2, 39.0), (27.2, 41.0), (34.5, 50.0), (35.0, 57.0),
                (16.0, 57.0), (16.5, 50.0), (23.8, 41.0), (23.8, 39.0), (16.5, 30.0)]))
    L.put(glass, '#3a3070')
    L.put(glass & (PX < 22) , '#453a80')
    sand_top = P([(19.0, 31.5), (32.0, 31.5), (27.0, 38.5), (24.0, 38.5)]) & glass
    sand_bot = P([(25.5, 46.0), (33.0, 53.0), (34.0, 57.0), (17.0, 57.0), (18.0, 53.0)]) & glass
    L.shade(sand_top, SND, 1 - f_lin(0, 31, 0, 39), lo=1, hi=3)
    L.shade(sand_bot, SND, 1 - f_lin(0, 46, 0, 57) * 0.8, lo=1, hi=4)
    L.put(R(25, 39, 25, 48), SND[3])
    L.put(SEG(17, 24, 17, 29) | SEG(18, 51, 18, 55), '#c8d8ff')
    L.put(border(glass) & ~(PX < 20), '#5a4c98')
    # frame: plates + posts
    for y in (19, 57):
        pl = R(12, y, 39, y + 3)
        L.bevel(pl, BRN, 3, up=1, dn=2)
        L.put(R(13, y + 1, 38, y + 1) & pl, BRN[3])
        L.put(R(11, y + 1, 40, y + 2) & ~pl, BRN[2])
    for x in (13, 37):
        post = R(x, 23, x + 1, 56)
        L.shade(post, GOLD, f_cyl(x + 1.0, 1.0), lo=2, hi=5)
        for y in (30, 40, 50):
            L.put(R(x - 1, y, x + 2, y + 1), GOLD[3])
            L.put(R(x - 1, y, x + 2, y), GOLD[4])
    for x in (11, 40):
        for y in (21, 59):
            L.put(R(x, y, x, y), GOLD[4])
    return {'halo': (cx, 40.0, 18.0)}


def uv(x0, y0, x1, y1):
    """u: 0..1 along the axis (x0,y0)->(x1,y1); v: signed perpendicular distance in px."""
    vx, vy = x1 - x0, y1 - y0
    L_ = math.hypot(vx, vy)
    u = ((PX - x0) * vx + (PY - y0) * vy) / (L_ * L_)
    v = ((PX - x0) * (-vy) + (PY - y0) * vx) / L_
    return u, v


SNK = ['#0e2a1e', '#1b4a2c', '#2c7038', '#4c9e46', '#8acc5c', '#d0f08a']
BEL = ['#6a5a1e', '#a8923a', '#dccb6a', '#f8eeb0']


def fm_serpent(L, a):
    cx = 25.5
    glow(a, cx, 42, 19, ['#2a1848', '#311d54'])

    def coil(cy, rx, ry, th):
        outer = E(cx, cy, rx + th / 2, ry + th / 2)
        inner = E(cx, cy, rx - th / 2, max(0.5, ry - th / 2))
        band = outer & ~inner
        front = PY >= cy
        f = np.where(front, 0.25 + 0.75 * (1 - (PY - cy) / (ry + th / 2)), 0.35 + 0.5 * (cy - PY) / (ry + th / 2))
        L.shade(band, SNK, np.clip(f, 0, 1), lo=1, hi=4, dith=0.6)
        ang = np.degrees(np.arctan2((PY - cy) / ry, (PX - cx) / rx)) % 360
        pat = band & (((ang / 24.0) % 1.0) < 0.28) & front
        L.put(pat & ~border(band), SNK[1])
        bel = band & front & ~nb(band, 0, 1)
        L.put(bel, BEL[1])
        L.put(band & ~nb(band, 0, -1) & front, SNK[5])
        return band

    coil(57.0, 13.5, 4.2, 4.6)
    coil(51.0, 11.0, 3.6, 4.4)
    coil(45.5, 8.5, 3.0, 4.2)
    path = bez((31.5, 45.0), (37.0, 37.0), (22.0, 34.0), (26.0, 27.0), n=30)
    neck = THP(path, 4.4)
    L.shade(neck, SNK, f_cyl(28.0, 5.0, 0.4), lo=2, hi=4)
    for (x, y) in ((30, 39), (28, 36), (26, 33)):
        L.put(R(x - 1, y, x, y), BEL[2])
    head = E(23.0, 25.5, 5.6, 3.6) | E(26.0, 26.5, 3.4, 3.0)
    L.shade(head, SNK, f_sphere(23.0, 25.0, 6.0, 4.0), lo=2, hi=5)
    L.put(R(18, 27, 24, 27) & head, BEL[2])
    L.put(pts_mask([(21, 24), (22, 24)]), '#ffd23a')
    L.put(pts_mask([(22, 24)]), '#120a0a')
    L.put(pts_mask([(18, 25)]), SNK[0])
    tongue = SEG(17, 27, 14, 27) | pts_mask([(13, 26), (13, 28)])
    L.put(tongue, '#e8304a')
    return {'halo': (cx, 41.0, 18.5)}


def fm_mask(L, a):
    cx = 25.5
    glow(a, cx, 38, 19, ['#2a1848', '#311d54'])
    fcols = [(PUR, (33.0, 33.0), (40.5, 15.5), 4.4), (TEA, (31.0, 33.0), (33.0, 14.0), 4.0),
             (PNK, (35.0, 34.0), (44.0, 24.0), 3.8)]
    for (rmp, p0, p1, w) in fcols:
        u, v = uv(p0[0], p0[1], p1[0], p1[1])
        prof = (w / 2.0) * np.sin(np.clip(u, 0, 1) * math.pi) ** 0.7
        fm = (u >= 0) & (u <= 1) & (np.abs(v) <= prof)
        L.shade(fm, rmp, np.clip(0.3 + 0.7 * u, 0, 1), lo=1, hi=4, dith=0.6)
        L.put(fm & (np.abs(v) < 0.6) & (u > 0.1), rmp[1])
    half = P([(25.5, 33.0), (20.0, 32.5), (14.0, 31.5), (8.0, 27.0), (7.5, 31.0), (9.0, 37.0), (12.5, 42.0),
              (17.0, 45.0), (22.0, 45.0), (25.5, 41.5)])
    msk = SYM(half)
    L.shade(msk, ['#2a1a4a', '#d6c8e6', '#ebe2f4', '#f8f4ff', '#ffffff'], f_sphere(cx, 34.0, 18.0, 12.0),
            lo=1, hi=4, dith=0.6)
    L.put(border(msk), GOLD[3])
    L.put(border(msk) & (PY < 36), GOLD[4])
    eyes = SYM(lens(18.0, 37.5, 9.0, 4.4))
    L.put(dilate(eyes) & msk, GOLD[4])
    L.put(eyes, '#160a24')
    for s in (False, True):
        sw = ARC(14.0, 40.5, 2.2, 180, 450, 1.0) | ARC(12.0, 33.5, 1.6, 270, 540, 1.0)
        sw = MIR(sw) if s else sw
        L.put(sw & msk & ~dilate(eyes), PUR[2])
    gem = lens(cx, 33.5, 3.4, 5.0)
    L.put(dilate(gem) & msk, GOLD[3])
    L.put(gem, RED[3])
    L.put(pts_mask([(25, 32)]), RED[4])
    stick = TH(37.5, 41.5, 42.0, 63.0, 2.2)
    L.shade(stick, GOLD, f_cyl(40.0, 1.6), lo=1, hi=4)
    rib = TH(36.0, 46.0, 33.0, 52.0, 2.0) | TH(38.5, 46.0, 41.5, 52.5, 2.0)
    L.put(rib, PUR[3])
    L.put(rib & ~nb(rib, 0, 1), PUR[1])
    L.put(C(38.0, 45.5, 1.8), PUR[2])
    return {'halo': (cx, 38.0, 18.0)}


def fm_lantern(L, a):
    cx = 25.5
    glow(a, cx, 38, 20, ['#2d1a46', '#38204c', '#452750', '#532e52'])
    ring = RING(cx, 16.5, 1.3, 3.0)
    L.shade(ring, GOLD, f_sphere(cx, 16.0, 3.0), lo=1, hi=5)
    roof = P([(15.0, 27.5), (36.0, 27.5), (30.5, 21.0), (20.5, 21.0)])
    L.shade(roof, IRN, f_cyl(cx, 10.0), lo=1, hi=4)
    L.put(R(15, 26, 36, 27), GOLD[3])
    L.put(R(15, 26, 36, 26), GOLD[4])
    L.put(R(23, 19, 28, 20), IRN[3])
    body = R(17, 28, 34, 47)
    lit = f_rad(cx, 39.0, 11.0, 12.0)
    L.shade(body, FLM, 0.35 + 0.65 * lit, lo=2, hi=5, dith=0.8)
    L.put(R(24, 40, 27, 46), WAXC[3])
    L.put(R(24, 40, 24, 46), WAXC[4])
    fl = P([(25.5, 31.5), (27.5, 35.5), (27.0, 38.5), (25.5, 39.5), (24.0, 38.5), (23.5, 35.5)])
    L.put(fl, '#ffffff')
    L.put(fl & (PY > 37.5), FLM[4])
    for x in (17, 21, 30, 34):
        L.put(R(x, 28, x, 47), IRN[2] if x in (21, 30) else IRN[1])
    L.put(R(17, 28, 34, 28) | R(17, 47, 34, 47), IRN[2])
    L.put(R(18, 37, 20, 37) | R(31, 37, 33, 37), IRN[2])
    base = P([(15.0, 48.0), (36.0, 48.0), (33.5, 52.5), (17.5, 52.5)])
    L.shade(base, IRN, f_cyl(cx, 10.0), lo=1, hi=4)
    L.put(R(15, 48, 36, 48), GOLD[4])
    L.put(R(22, 53, 29, 54), IRN[2])
    L.put(R(24, 55, 27, 56), GOLD[3])
    return {'halo': (cx, 38.0, 18.0)}


def fm_crown(L, a):
    cx = 25.5
    glow(a, cx, 42, 19, ['#2a1848', '#311d54'])
    vel = E(cx, 44.0, 12.0, 11.0) & (PY < 45)
    L.shade(vel, RED, f_sphere(cx, 40.0, 13.0, 11.0), lo=1, hi=3, dith=0.6)
    spikes = [((10.0, 45.0), (9.5, 33.0), (16.0, 45.0)), ((14.0, 45.0), (17.0, 29.0), (21.5, 45.0)),
              ((20.5, 45.0), (25.5, 22.5), (30.5, 45.0))]
    sp = np.zeros((H, W), bool)
    for (p0, p1, p2) in spikes:
        sp |= SYM(P([p0, p1, p2]))
    L.shade(sp, GOLD, f_cyl(cx, 16.0, 0.25), lo=2, hi=5)
    for (p0, p1, p2) in spikes:
        L.put(SYM(SEG(p1[0], p1[1] + 2, p1[0], 44)), GOLD[3])
    band = R(10, 44, 41, 52) | E(cx, 52.0, 15.5, 2.5)
    L.shade(band, GOLD, f_cyl(cx, 16.0, 0.25), lo=1, hi=5)
    L.put(R(10, 44, 41, 44), GOLD[5])
    L.put(R(10, 46, 41, 46) & band, GOLD[2])
    L.put((R(10, 51, 41, 51) | (E(cx, 52.0, 15.5, 2.5) & ~E(cx, 51.5, 15.5, 2.5))) & band, GOLD[2])
    for (x, rmp, rr) in ((25.5, RED, 2.6), (17.0, BLU, 1.9), (34.0, BLU, 1.9), (11.8, GRN, 1.2), (39.2, GRN, 1.2)):
        g = E(x, 48.8, rr, rr * 0.95)
        L.put(dilate(g) & band, GOLD[1])
        L.shade(g, rmp, f_sphere(x, 48.8, rr), lo=1, hi=4)
    for (x, y) in ((9.5, 32.5), (17.0, 28.5), (25.5, 21.5), (34.0, 28.5), (41.5, 32.5)):
        p = C(x, y, 2.0)
        L.shade(p, CRM, f_sphere(x, y, 2.0), lo=1, hi=4)
    return {'halo': (cx, 40.0, 18.0)}


def fm_chalice(L, a):
    cx = 25.5
    glow(a, cx, 22, 15, ['#2c1a4c', '#34205a', '#3e2768'])
    bowl = (E(cx, 23.5, 11.0, 14.0) & (PY >= 23.5)) | E(cx, 23.5, 11.0, 3.0)
    L.shade(bowl, GOLD, f_cyl(cx, 11.0, 0.35), lo=1, hi=5, dith=0.5)
    L.put(E(cx, 23.5, 11.0, 3.0) & ~E(cx, 23.5, 9.6, 2.2), GOLD[4])
    liq = E(cx, 23.5, 9.6, 2.2)
    L.put(liq, PUR[2])
    L.put(liq & (PY < 23.5), PUR[3])
    L.put(pts_mask([(21, 23), (22, 23)]), PUR[4])
    L.put(R(15, 27, 36, 27) & bowl, GOLD[2])
    L.put(R(16, 28, 35, 28) & bowl, GOLD[4])
    for (x, rmp) in ((25.5, RED), (19.0, BLU), (32.0, BLU)):
        g = C(x, 32.0, 1.9 if x == 25.5 else 1.4)
        L.put(dilate(g) & bowl, GOLD[1])
        L.shade(g, rmp, f_sphere(x, 32.0, 2.0), lo=1, hi=4)
    stem = R(24, 37, 27, 49)
    L.shade(stem, GOLD, f_cyl(cx, 2.0), lo=1, hi=4)
    knot = E(cx, 42.5, 4.0, 2.3)
    L.shade(knot, GOLD, f_sphere(cx, 42.0, 4.0, 2.3), lo=1, hi=5)
    L.put(C(cx, 42.5, 1.1), RED[3])
    foot = P([(21.5, 49.0), (29.5, 49.0), (35.0, 54.0), (16.0, 54.0)]) | E(cx, 54.5, 9.5, 2.5)
    L.shade(foot, GOLD, f_cyl(cx, 9.5, 0.35), lo=1, hi=5)
    L.put(E(cx, 54.5, 9.5, 2.5) & ~E(cx, 54.0, 9.5, 2.5), GOLD[1])
    return {'halo': (cx, 37.0, 18.0), 'sparks': 4}


def fm_coin(L, a):
    cx, cy = 25.5, 40.0
    glow(a, cx, cy, 19, ['#2a1848', '#311d54'])
    edge = E(cx + 1.5, cy + 1.2, 14.0, 15.0)
    L.put(edge, GOLD[1])
    L.put(edge & (XX % 2 == 0), GOLD[2])
    face = E(cx, cy, 14.0, 15.0)
    L.put(face, GOLD[3])
    L.put(face & ((PX - cx) * 0.8 + (PY - cy) < -6), GOLD[4])
    rim = face & ~E(cx, cy, 12.0, 13.0)
    L.put(rim, GOLD[4])
    L.put(rim & ((PX - cx) + (PY - cy) > 4), GOLD[2])
    L.put(rim & ((PX - cx) + (PY - cy) < -8), GOLD[5])
    inner = E(cx, cy, 12.0, 13.0)
    L.put(border(inner) & ~nb(inner, -1, -1), GOLD[2])
    L.put(border(inner) & ~nb(inner, 1, 1), GOLD[5])
    st, _ = star_mask(cx, cy + 0.6, 10.0, 4.2)
    L.put(dilate(st) & inner & ~st, GOLD[2])
    L.put(st, GOLD[4])
    L.put(st & ~nb(st, 1, 1), GOLD[2])
    L.put(st & ~nb(st, -1, -1), GOLD[5])
    L.put(st & ~nb(st, 1, 0) & ~nb(st, 1, 1), GOLD[3])
    L.put(pts_mask([(15, 31), (16, 30), (17, 29), (18, 28)]), GOLD[5])
    return {'halo': False}


def fm_star(L, a):
    cx, cy = 25.5, 40.5
    glow(a, cx, cy, 21, ['#2a1a4e', '#31205a', '#392866', '#423072'])
    ST = ['#6a3a10', '#b8781e', '#e8b236', '#ffd968', '#fff2b4', '#ffffff']
    st, pts = star_mask(cx, cy, 17.5, 7.3)
    L.put(st, ST[2])
    lx, ly = -0.6, -0.8
    for i in range(5):
        o = pts[2 * i]
        ia = pts[(2 * i - 1) % 10]
        ib = pts[(2 * i + 1) % 10]
        for p in (ia, ib):
            tri = P([(cx, cy), o, p])
            mx = (o[0] + p[0]) / 2.0 - cx
            my = (o[1] + p[1]) / 2.0 - cy
            d = (mx * lx + my * ly) / math.hypot(mx, my)
            lv = 4 if d > 0.55 else 3 if d > 0.0 else 2 if d > -0.55 else 1
            L.put(tri & st, ST[lv])
    L.put(C(cx, cy, 1.6), ST[5])
    return {'halo': False, 'sparks': 5, 'stars': 10}


def fm_comet(L, a):
    hx, hy = 34.5, 23.5
    tx, ty = 8.0, 63.0
    u, v = uv(hx, hy, tx, ty)
    half = 4.6 + 4.0 * np.clip(u, 0, 1)
    tail = (u >= 0) & (u <= 1) & (np.abs(v) <= half)
    f = (1 - np.abs(v) / np.maximum(half, 0.1)) * (1 - np.clip(u, 0, 1)) ** 0.8
    TL = ['#2c1c58', '#3a2e7a', '#4a50a8', '#5e86cc', '#8ec8ec', '#d8f6ff']
    lev = quant(np.clip(f * 1.15, 0, 1), 6, dith=1.0)
    for i in range(1, 6):
        a[tail & (lev == i) & ART_F] = hexc(TL[i])
    for off in (-3.0, 3.5):
        s = (u > 0.05) & (u < 0.75) & (np.abs(v - off * (1 + u)) < 0.5)
        a[s & ART_F & (lev < 3)] = hexc(TL[3])
    head = C(hx, hy, 4.6)
    L.shade(head, ['#5e86cc', '#8ec8ec', '#c8f0ff', '#ffffff'], f_rad(hx - 0.5, hy - 0.5, 4.6), dith=0.5)
    return {'halo': False, 'sparks': 3, 'stars': 9}


def fm_tower(L, a):
    cx = 25.5
    glow(a, cx, 30, 18, ['#2a1848', '#311d54'])
    hill = P([(5.0, 68.0), (9.0, 61.0), (16.0, 58.0), (35.0, 58.0), (42.0, 61.0), (46.0, 68.0)])
    L.shade(hill, STN, 1 - f_lin(0, 58, 0, 68), lo=0, hi=2, dith=0.8)
    body = P([(18.5, 27.0), (32.5, 27.0), (34.0, 60.0), (17.0, 60.0)])
    L.shade(body, STN, f_cyl(cx, 9.0, 0.3), lo=1, hi=4, dith=0.5)
    for y in range(30, 60, 4):
        L.put(R(16, y, 35, y) & body, STN[1])
        off = 0 if (y // 4) % 2 else 3
        for x in range(17 + off, 35, 6):
            L.put(R(x, y + 1, x, y + 3) & body, STN[1])
    top = R(16, 23, 35, 27)
    L.shade(top, STN, f_cyl(cx, 11.0, 0.3), lo=1, hi=4)
    L.put(R(16, 27, 35, 27), STN[0])
    for x0 in (16, 21, 27, 32):
        m = R(x0, 19, x0 + 2, 22)
        L.shade(m, STN, f_cyl(x0 + 1.0, 1.5), lo=2, hi=4)
    for wy in (33, 43):
        win = R(24, wy, 27, wy + 5) | E(25.5, wy + 0.5, 2.0, 1.5)
        L.put(dilate(win) & body, STN[0])
        L.put(win, FLM[3])
        L.put(win & (PY > wy + 3), FLM[2])
        L.put(R(25, wy + 1, 26, wy + 2), FLM[4])
    door = R(23, 54, 28, 60) | E(25.5, 54.5, 2.6, 2.4)
    L.put(dilate(door) & body, STN[0])
    L.put(door, BRN[2])
    L.put(R(25, 53, 26, 60) & door, BRN[1])
    bolt = P([(7.0, 12.5), (14.0, 12.5), (12.0, 16.5), (17.5, 16.0), (14.5, 20.5), (20.5, 20.0), (12.0, 24.0),
              (13.5, 20.5), (9.0, 21.0), (11.0, 17.0), (6.5, 17.5)])
    L.put(bolt, FLM[4])
    L.put(bolt & ~nb(bolt, 0, -1), FLM[5])
    L.put(bolt & ~nb(bolt, 0, 1), FLM[3])
    for (x, y) in ((22, 16), (27, 15)):
        L.put(R(x, y, x + 1, y + 1), STN[3])
    return {'halo': False}


def fm_wheel(L, a):
    cx, cy = 25.5, 38.5
    glow(a, cx, cy, 20, ['#2a1848', '#311d54'])
    post = P([(23.5, 50.0), (27.5, 50.0), (29.0, 60.0), (22.0, 60.0)])
    L.shade(post, BRN, f_cyl(cx, 4.0), lo=1, hi=4)
    foot = R(17, 60, 34, 62)
    L.bevel(foot, BRN, 3, up=1, dn=2)
    disc = C(cx, cy, 12.5)
    cols = [RED, PUR, BLU, GRN]
    ang = (np.degrees(np.arctan2(PY - cy, PX - cx)) + 90 + 22.5) % 360
    seg = (ang // 45).astype(int)
    for k in range(8):
        m = disc & (seg == k)
        L.shade(m, cols[k % 4], f_sphere(cx, cy, 16.0, amb=0.4), lo=1, hi=3)
    for k in range(8):
        t = math.radians(k * 45 - 90)
        L.put(SEG(cx - 0.5, cy - 0.5, cx - 0.5 + 12 * math.cos(t), cy - 0.5 + 12 * math.sin(t)) & disc, GOLD[3])
    rim = RING(cx, cy, 12.5, 15.5)
    L.shade(rim, GOLD, f_sphere(cx, cy, 18.0), lo=2, hi=5)
    L.put(border(C(cx, cy, 12.5)) & ~C(cx, cy, 11.5), GOLD[1])
    for k in range(16):
        t = math.radians(k * 22.5 - 90)
        x = int(math.floor(cx + 14.0 * math.cos(t)))
        y = int(math.floor(cy + 14.0 * math.sin(t)))
        L.put(pts_mask([(x, y)]), '#fff6c8' if k % 2 == 0 else GOLD[2])
    hub = C(cx, cy, 3.2)
    L.shade(hub, GOLD, f_sphere(cx, cy, 3.2), lo=1, hi=5)
    L.put(C(cx, cy, 1.4), GEMV[2])
    ptr = P([(22.0, 19.0), (29.0, 19.0), (25.5, 26.0)])
    L.bevel(ptr, ['#2a0a14', RED[1], RED[2], RED[3], RED[4]], 3, up=1, dn=2)
    L.put(C(cx, 19.5, 1.0), GOLD[4])
    return {'halo': False}


def fm_feather(L, a):
    glow(a, 26, 39, 19, ['#2a1848', '#311d54'])
    x0, y0, x1, y1 = 13.0, 61.0, 38.5, 16.0
    u, v = uv(x0, y0, x1, y1)
    us = np.clip((u - 0.22) / 0.78, 0, 1)
    wl = 7.0 * np.sin(np.clip(us, 0, 1) * math.pi) ** 0.55 * (1 - 0.25 * us)
    wr = 5.5 * np.sin(np.clip(us, 0, 1) * math.pi) ** 0.6
    vane = (u > 0.22) & (u < 1.0) & (((v <= 0) & (-v <= wl)) | ((v > 0) & (v <= wr)))
    cut = (((np.abs((u * 40.0 + v * 0.35) - 25.0) < 0.45) & (v < -1.5))
           | ((np.abs((u * 40.0 - v * 0.35) - 31.0) < 0.45) & (v > 1.5)))
    vane &= ~cut
    FTH = ['#3a2860', '#7a6aa8', '#b8acd8', '#e4dcf6', '#fbf8ff']
    f = np.clip(0.95 - np.abs(v) / 9.0 - (u - 0.6) * 0.5, 0, 1)
    L.shade(vane, FTH, f, lo=1, hi=4, dith=0.5)
    L.put(vane & (u > 0.85), PUR[3])
    L.put(vane & (u > 0.92), PUR[2])
    barbs = vane & (((u * 46.0 - np.abs(v) * 0.7) % 3.0) < 0.6) & (np.abs(v) > 1.2)
    L.put(barbs & (u < 0.85), FTH[2])
    shaft = THP([(x0, y0), (x0 + (x1 - x0) * 0.98, y0 + (y1 - y0) * 0.98)], 1.3)
    L.put(shaft & (u > 0.14), FTH[4])
    nib = P([(12.0, 56.5), (16.0, 59.0), (13.5, 62.0), (9.5, 64.5), (11.5, 60.0)])
    L.bevel(nib, GOLD, 3, up=2, dn=2)
    L.put(SEG(10, 63, 12, 60), GOLD[1])
    drop = C(8.0, 66.0, 1.4)
    L.put(drop, '#2a1c5a')
    L.put(pts_mask([(7, 65)]), '#6a5aa8')
    return {'halo': (25.5, 40.0, 18.0)}


def fm_anchor(L, a):
    cx = 25.5
    glow(a, cx, 40, 19, ['#2a1848', '#311d54'])
    ring = RING(cx, 18.0, 1.6, 3.6)
    L.shade(ring, SILV, f_sphere(cx, 17.5, 3.6), lo=1, hi=4)
    shank = R(24, 21, 27, 55)
    L.shade(shank, SILV, f_cyl(cx, 2.0), lo=1, hi=4)
    stock = R(15, 24, 36, 26)
    L.shade(stock, SILV, 1 - f_lin(0, 24, 0, 27), lo=1, hi=4)
    for x in (14.0, 37.0):
        b = C(x, 25.0, 2.0)
        L.shade(b, SILV, f_sphere(x, 24.5, 2.0), lo=1, hi=4)
    arm = ARC(cx, 41.0, 14.5, 22, 158, 3.4)
    L.shade(arm, SILV, f_lin(0, 60, 0, 44), lo=1, hi=4, dith=0.4)
    for s in (False, True):
        fl = P([(11.5, 49.0), (7.5, 42.0), (15.5, 45.0)])
        fl = MIR(fl) if s else fl
        L.bevel(fl, SILV, 3, up=1, dn=2)
    crown = C(cx, 55.5, 2.6)
    L.shade(crown, SILV, f_sphere(cx, 55.0, 2.6), lo=1, hi=4)
    rope = (THP(bez((cx + 2.0, 19.5), (36.0, 30.0), (16.0, 36.0), (28.0, 44.0), n=30), 1.8)
            | THP(bez((28.0, 44.0), (34.0, 49.0), (19.0, 49.0), (21.0, 53.0), n=16), 1.8))
    L.put(rope, BRN[3])
    L.put(rope & (((XX + YY) % 3) == 0), BRN[2])
    L.put(rope & (((XX + YY) % 3) == 1) & ~nb(rope, 0, -1), BRN[4])
    return {'halo': (cx, 39.0, 18.0)}


def fm_mirror(L, a):
    cx, cy = 25.5, 31.0
    glow(a, cx, cy, 17, ['#2a1848', '#311d54'])
    frame = E(cx, cy, 11.5, 13.5)
    L.shade(frame, GOLD, f_sphere(cx, cy, 13.0, 15.0), lo=1, hi=5)
    crest = P([(22.5, 18.5), (25.5, 14.5), (28.5, 18.5)]) | C(cx, 15.5, 1.6)
    L.bevel(crest, GOLD, 4, up=1, dn=2)
    for (x, y) in ((14.5, 31.0), (36.5, 31.0)):
        L.shade(C(x, y, 1.6), GOLD, f_sphere(x, y, 1.6), lo=2, hi=5)
    glass = E(cx, cy, 8.6, 10.6)
    L.put(border(E(cx, cy, 9.6, 11.6)), GOLD[1])
    L.shade(glass, ['#2e2a6a', '#3e4a8c', '#5876b0', '#86b2d8', '#c6e6f6'], 1 - f_lin(18, 22, 33, 41) * 0.9, dith=1.0)
    for d in (0, 4):
        L.put(SEG(19 + d, 27, 23 + d, 23) & glass, '#e8f8ff')
    moon = C(29.0, 35.0, 2.8) & ~C(30.2, 34.0, 2.4)
    L.put(moon & glass, '#f6f0ff')
    L.bevel(R(23, 44, 28, 46), GOLD, 4, up=1, dn=2)
    handle = P([(23.5, 46.0), (27.5, 46.0), (28.5, 59.0), (22.5, 59.0)])
    L.shade(handle, GOLD, f_cyl(cx, 3.0), lo=1, hi=5)
    L.put(R(23, 50, 28, 50) & handle, GOLD[2])
    L.put(R(23, 54, 28, 54) & handle, GOLD[2])
    knob = E(cx, 61.0, 3.4, 2.4)
    L.shade(knob, GOLD, f_sphere(cx, 60.5, 3.4, 2.4), lo=1, hi=5)
    L.put(C(cx, 61.0, 1.0), GEMV[2])
    return {'halo': False}


def fm_bell(L, a):
    cx = 25.5
    glow(a, cx, 40, 19, ['#2a1848', '#311d54'])
    loop = RING(cx, 20.0, 1.4, 3.2)
    L.shade(loop, GOLD, f_sphere(cx, 19.5, 3.2), lo=1, hi=5)
    bell = (E(cx, 29.5, 8.0, 6.5)
            | P([(17.5, 29.5), (33.5, 29.5), (35.0, 40.0), (39.5, 48.0), (11.5, 48.0), (16.0, 40.0)])
            | E(cx, 48.5, 14.5, 2.6))
    L.shade(bell, GOLD, f_cyl(cx, 13.0, 0.4), lo=1, hi=5, dith=0.5)
    L.put(E(cx, 48.5, 14.5, 2.6) & ~E(cx, 47.5, 14.5, 2.6), GOLD[2])
    L.put(R(10, 42, 41, 42) & bell, GOLD[2])
    L.put(R(10, 44, 41, 44) & bell, GOLD[4])
    L.put(SEG(20, 27, 18, 38), GOLD[5])
    clap = C(cx, 52.5, 2.6)
    L.shade(clap, GOLD, f_sphere(cx, 52.0, 2.6), lo=1, hi=3)
    for s in (False, True):
        loopm = P([(25.0, 24.0), (18.5, 20.0), (17.0, 24.5), (19.0, 26.5)])
        tailm = P([(24.5, 25.0), (19.5, 31.0), (21.0, 32.0), (25.5, 26.0)])
        if s:
            loopm, tailm = MIR(loopm), MIR(tailm)
        L.bevel(tailm, RED, 2, up=1, dn=1)
        L.bevel(loopm, RED, 3, up=1, dn=2)
    L.bevel(R(24, 23, 27, 26), RED, 3, up=1, dn=1)
    return {'halo': (cx, 39.0, 18.0)}


def petal(base, tip, w, bend=0.0):
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2.0, (by + ty) / 2.0
    nx, ny = -(ty - by), (tx - bx)
    ln = math.hypot(nx, ny)
    nx, ny = nx / ln, ny / ln
    left = bez(base, (mx + nx * w + bend * nx, my + ny * w + bend * ny), tip, n=14)
    right = bez(tip, (mx - nx * w + bend * nx, my - ny * w + bend * ny), base, n=14)
    return P(left + right[1:])


def fm_lotus(L, a):
    cx = 25.5
    glow(a, cx, 42, 19, ['#2c1848', '#371d50', '#432356'])
    for (y, x0, x1) in ((59, 9, 20), (59, 31, 42), (62, 13, 38), (65, 18, 33)):
        a[R(x0, y, x1, y)] = hexc('#3a2e6e')
    pads = E(13.0, 56.0, 7.5, 2.6) | E(38.0, 56.5, 7.5, 2.6)
    L.shade(pads, GRN, 1 - f_lin(0, 53, 0, 59), lo=1, hi=3)
    L.put(SEG(13, 56, 9, 54) | SEG(38, 56, 42, 54), GRN[0])
    pet = [((cx, 54.0), (6.5, 43.0), 9.0), ((cx, 54.0), (44.5, 43.0), 9.0),
           ((cx, 54.0), (12.5, 29.0), 10.0), ((cx, 54.0), (38.5, 29.0), 10.0),
           ((cx, 55.0), (cx, 21.0), 11.0)]
    for i, (b, t, w) in enumerate(pet):
        m = petal(b, t, w)
        u, v = uv(b[0], b[1], t[0], t[1])
        L.shade(m, PNK, np.clip(0.2 + 0.8 * u, 0, 1), lo=1 if i < 2 else 2, hi=4, dith=0.5)
        L.put(m & ~nb(m, 1, 1) & ~nb(m, 0, 1), PNK[1])
        L.put(m & ~nb(m, -1, -1) & (u > 0.3), PNK[4])
        L.put(m & (np.abs(v) < 0.5) & (u > 0.2) & (u < 0.75), PNK[2])
    for (x, y) in ((22, 50), (24, 49), (27, 49), (29, 50), (25, 51)):
        L.put(pts_mask([(x, y)]), GOLD[4])
    base = E(cx, 53.5, 9.0, 2.5)
    L.shade(base, GRN, 1 - f_lin(0, 52, 0, 56), lo=2, hi=4)
    return {'halo': (cx, 40.0, 18.0)}


def fm_dagger(L, a):
    cx = 25.5
    glow(a, cx, 40, 19, ['#2a1848', '#311d54'])
    blade = P([(22.5, 35.0), (28.5, 35.0), (28.3, 55.0), (25.5, 64.5), (22.7, 55.0)])
    L.put(blade, SILV[3])
    L.put(blade & (PX > 25.5), SILV[2])
    L.put(blade & (PX > 27.5), SILV[1])
    L.put(blade & (PX < 23.5), SILV[4])
    L.put(R(25, 36, 25, 56), SILV[1])
    L.put(R(26, 36, 26, 56), SILV[4])
    grip = R(24, 21, 27, 30)
    L.shade(grip, BRN, f_cyl(cx, 2.0), lo=1, hi=3)
    for y in range(21, 31, 2):
        L.put(R(24, y, 27, y), PUR[1])
    guard = P([(14.0, 31.0), (37.0, 31.0), (35.0, 34.5), (16.0, 34.5)])
    L.shade(guard, GOLD, f_cyl(cx, 12.0, 0.3), lo=1, hi=5)
    for x in (12.5, 38.5):
        L.shade(C(x, 30.0, 2.2), GOLD, f_sphere(x, 29.5, 2.2), lo=1, hi=5)
    L.shade(C(cx, 32.8, 1.8), GEMV, f_sphere(cx, 32.4, 1.8), lo=0, hi=3)
    pom = C(cx, 18.0, 2.8)
    L.shade(pom, RED, f_sphere(cx, 17.5, 2.8), lo=1, hi=4)
    L.put(R(23, 20, 28, 20), GOLD[3])
    return {'halo': (cx, 40.0, 18.0)}


BRW = ['#14381c', '#1f6a2a', '#38a83a', '#7ae05a', '#c8ff9a']


def fm_cauldron(L, a):
    cx = 25.5
    glow(a, cx, 30, 16, ['#1e2a40', '#20363e', '#22423e'])
    for (x, h) in ((19.5, 5), (25.5, 6.5), (31.5, 5)):
        fl = P([(x - 2.5, 63.0), (x + 2.5, 63.0), (x + 1.5, 63 - h * 0.6), (x, 63 - h), (x - 1.5, 63 - h * 0.6)])
        L.put(fl, FLM[2])
        L.put(fl & (PY > 63 - h * 0.45) & (np.abs(PX - x) < 1.4), FLM[4])
    legs = R(14, 55, 16, 60) | R(35, 55, 37, 60) | R(24, 57, 27, 61)
    L.bevel(legs, IRN, 2, up=1, dn=1)
    pot = E(cx, 46.0, 15.0, 11.0) & (PY > 38)
    L.shade(pot, IRN, f_sphere(cx - 1, 44.0, 16.0, 12.0, amb=0.15), lo=0, hi=4, dith=0.8)
    for x in (9.5, 41.5):
        L.shade(RING(x, 41.0, 1.0, 2.4), IRN, f_sphere(x, 40.5, 2.4), lo=1, hi=4)
    lip = E(cx, 38.0, 15.0, 3.6)
    L.shade(lip, IRN, 1 - f_lin(0, 35, 0, 41), lo=1, hi=4)
    brew = E(cx, 38.0, 12.3, 2.4)
    L.shade(brew, BRW, f_rad(cx, 38.0, 12.0, 3.0), lo=1, hi=3, dith=0.6)
    drip = (TH(18.0, 40.0, 18.0, 44.0, 1.8) | TH(31.0, 40.0, 31.0, 46.0, 1.8))
    L.put(drip, BRW[2])
    L.put(drip & ~nb(drip, -1, 0), BRW[3])
    for (x, y, r) in ((20.5, 31.5, 2.6), (29.5, 26.5, 2.4), (24.5, 20.5, 1.6), (32.5, 33.5, 1.5)):
        b = C(x, y, r)
        L.put(b, BRW[2])
        L.put(border(b), BRW[3])
        L.put(b & ~nb(b, -1, -1) & ~nb(b, 0, -1), BRW[4])
        L.put(pts_mask([(int(x) - 1, int(y) - 1)]) & b, BRW[4])
    return {'halo': (cx, 41.0, 18.5)}


OWL = ['#24140c', '#4a2c1a', '#76492a', '#a6703e', '#d4a468', '#f2d6a2']


def fm_owl(L, a):
    cx = 25.5
    glow(a, cx, 40, 19, ['#2a1848', '#311d54'])
    br = TH(6.0, 58.5, 45.0, 57.0, 3.2)
    L.shade(br, BRN, 1 - f_lin(0, 56, 0, 60), lo=1, hi=3)
    body = E(cx, 44.0, 12.0, 13.5)
    L.shade(body, OWL, f_sphere(cx, 41.0, 14.0, 16.0, amb=0.3), lo=1, hi=4, dith=0.6)
    head = E(cx, 31.0, 12.5, 9.0)
    tufts = SYM(P([(14.0, 30.0), (14.5, 19.0), (21.0, 25.0)]))
    L.shade(head | tufts, OWL, f_sphere(cx, 28.0, 14.0, 10.0, amb=0.35), lo=1, hi=4, dith=0.6)
    belly = E(cx, 47.5, 7.5, 8.5)
    L.put(belly, OWL[5])
    for (y, xs) in ((42, (22, 28)), (46, (20, 25, 30)), (50, (22, 28)), (54, (25,))):
        for x in xs:
            L.put(pts_mask([(x, y), (x + 1, y + 1), (x + 2, y)]) & belly, OWL[3])
    wings = SYM(E(15.5, 46.0, 4.5, 9.5)) & body
    L.shade(wings, OWL, f_sphere(cx, 40.0, 16.0), lo=0, hi=2)
    for y in (44, 48, 52):
        L.put(SYM(R(13, y, 17, y)) & wings, OWL[1])
    L.put(SYM(C(20.5, 31.5, 5.0)), OWL[4])
    L.put(SYM(border(C(20.5, 31.5, 5.0))) & (PY > 31), OWL[2])
    L.put(SYM(C(20.5, 31.5, 3.2)), '#ffb028')
    L.put(SYM(C(20.5, 31.5, 3.2) & (PY < 30.5)), '#ffd868')
    L.put(SYM(C(20.5, 31.5, 1.6)), '#120808')
    L.put(SYM(pts_mask([(19, 30)])), '#ffffff')
    beak = P([(24.0, 34.0), (27.0, 34.0), (25.5, 38.5)])
    L.put(beak, GOLD[3])
    L.put(beak & (PX > 25.5), GOLD[2])
    L.put(SYM(R(20, 56, 22, 57) | R(19, 57, 19, 58) | R(21, 57, 21, 58)), GOLD[3])
    return {'halo': (cx, 40.0, 18.0)}


def fm_sun(L, a):
    cx, cy = 25.5, 40.0
    glow(a, cx, cy, 22, ['#2c1a4a', '#382050', '#462656', '#562e5a'])
    rays = np.zeros((H, W), bool)
    rays2 = np.zeros((H, W), bool)
    for k in range(16):
        t = math.radians(k * 22.5 - 90)
        if k % 2 == 0:
            r0, r1, w = 9.0, 19.5, 2.6
            px_, py_ = -math.sin(t), math.cos(t)
            tip = (cx + r1 * math.cos(t), cy + r1 * math.sin(t))
            b1 = (cx + r0 * math.cos(t) + px_ * w, cy + r0 * math.sin(t) + py_ * w)
            b2 = (cx + r0 * math.cos(t) - px_ * w, cy + r0 * math.sin(t) - py_ * w)
            rays |= P([b1, tip, b2])
        else:
            pts = []
            for i in range(9):
                rr = 10.0 + i * 0.85
                off = 1.0 * math.sin(i * 1.4)
                pts.append((cx + rr * math.cos(t) - math.sin(t) * off, cy + rr * math.sin(t) + math.cos(t) * off))
            rays2 |= THP(pts, 1.5)
    L.put(rays2, ORG[3])
    L.put(rays, GOLD[4])
    L.put(rays & ~nb(rays, 1, 1), GOLD[3])
    disc = C(cx, cy, 10.5)
    L.shade(disc, ['#a85a14', '#e0901e', '#f8bc34', '#ffdc6a', '#fff2b0'], f_sphere(cx, cy, 13.0, amb=0.45), dith=0.6)
    for x0 in (20, 28):
        L.put(pts_mask([(x0, 39), (x0 + 1, 40), (x0 + 2, 40), (x0 + 3, 39)]), '#a85a14')
    L.put(pts_mask([(23, 45), (24, 46), (25, 46), (26, 46), (27, 45)]), '#a85a14')
    L.put(R(18, 42, 19, 42) | R(31, 42, 32, 42), '#f08a5a')
    return {'halo': False}


def fm_spider(L, a):
    cx, cy = 25.5, 37.0
    web = np.zeros((H, W), bool)
    spokes = []
    for k in range(8):
        t = math.radians(k * 45 + 22.5)
        web |= SEG(cx, cy, cx + 40 * math.cos(t), cy + 40 * math.sin(t))
        spokes.append(t)
    for rr in (6.0, 11.0, 16.0, 21.0):
        for k in range(8):
            t0, t1 = spokes[k], spokes[(k + 1) % 8]
            p0 = (cx + rr * math.cos(t0), cy + rr * math.sin(t0))
            p2 = (cx + rr * math.cos(t1), cy + rr * math.sin(t1))
            tm = (t0 + t1) / 2 if k < 7 else (t0 + t1 + 2 * math.pi) / 2
            p1 = (cx + rr * 0.78 * math.cos(tm), cy + rr * 0.78 * math.sin(tm))
            web |= POLYL(bez(p0, p1, p2, n=8))
    a[web & ART_F & ~R(10, 0, 40, 13)] = hexc('#4e3f80')
    SPD = ['#0c0814', '#1c1430', '#2e2450', '#463a74', '#6a5ca0', '#9a8ccc']
    sp_y = 40.0
    a[R(25, 13, 25, int(sp_y) - 6) & ART_F] = hexc('#8a7ac0')
    abd = E(cx, sp_y + 5.0, 6.0, 7.0)
    ceph = E(cx, sp_y - 3.0, 3.8, 3.4)
    legs = np.zeros((H, W), bool)
    for s in (1, -1):
        for (sy, kx, ky, ex, ey) in ((-4.5, 7.5, -10.0, 13.0, -14.0), (-3.0, 10.0, -6.0, 16.5, -5.0),
                                     (-1.5, 10.0, -1.0, 16.0, 6.0), (0.0, 8.0, 3.0, 12.5, 14.0)):
            p0 = (cx + s * 2.0, sp_y + sy * 0.4 - 1.0)
            p1 = (cx + s * kx, sp_y + ky)
            p2 = (cx + s * ex, sp_y + ey)
            legs |= THP([p0, p1], 1.6) | THP([p1, p2], 1.2)
    L.put(legs, SPD[2])
    L.put(legs & ~nb(legs, 0, -1), SPD[4])
    L.shade(abd, SPD, f_sphere(cx - 1.5, sp_y + 2.5, 6.5, 7.5, amb=0.2), lo=1, hi=5, dith=0.4)
    L.shade(ceph, SPD, f_sphere(cx - 1, sp_y - 4.5, 4.0, 3.6, amb=0.2), lo=1, hi=5)
    hg = (P([(22.5, sp_y + 2.0), (28.5, sp_y + 2.0), (25.5, sp_y + 5.0)])
          | P([(22.5, sp_y + 8.0), (28.5, sp_y + 8.0), (25.5, sp_y + 5.0)]))
    L.put(hg, RED[3])
    L.put(hg & ~nb(hg, 0, -1), RED[4])
    L.put(pts_mask([(24, int(sp_y) - 3), (26, int(sp_y) - 3)]), '#ff5a6a')
    return {'halo': False, 'stars': 4, 'sparks': 1}


def fm_fox(L, a):
    cx = 25.5
    glow(a, cx, 40, 19, ['#2a1848', '#311d54'])
    tail = P([(31.0, 60.0), (38.0, 58.0), (43.0, 50.0), (43.5, 41.0), (40.5, 35.0), (38.0, 42.0), (37.5, 50.0),
              (33.0, 55.0)])
    L.shade(tail, ORG, f_sphere(40.0, 46.0, 6.0, 12.0), lo=1, hi=4, dith=0.5)
    tip = tail & (PY < 41.5)
    L.put(tip, CRM[4])
    L.put(tip & (PX > 41.5), CRM[3])
    body = E(cx, 50.5, 9.5, 10.5)
    L.shade(body, ORG, f_sphere(cx - 1, 47.0, 11.0, 12.0, amb=0.35), lo=1, hi=4, dith=0.5)
    bib = lens(cx, 47.0, 9.0, 15.0)
    L.shade(bib, CRM, f_sphere(cx, 44.0, 6.0, 9.0, amb=0.5), lo=2, hi=4)
    for x0 in (19, 28):
        leg = R(x0, 52, x0 + 3, 60)
        L.shade(leg, ORG, f_cyl(x0 + 1.5, 2.0), lo=1, hi=3)
        L.put(R(x0, 57, x0 + 3, 61), BRN[1])
        L.put(R(x0, 61, x0 + 3, 61), BRN[0])
    ears = SYM(P([(13.5, 30.0), (14.0, 15.5), (22.5, 24.0)]))
    L.shade(ears, ORG, f_sphere(cx, 24.0, 14.0, 10.0), lo=1, hi=4)
    L.put(SYM(P([(15.5, 27.0), (15.8, 19.5), (20.5, 24.5)])), BRN[1])
    head = E(cx, 31.5, 11.0, 8.0) | P([(17.0, 33.0), (34.0, 33.0), (25.5, 43.5)])
    L.shade(head, ORG, f_sphere(cx - 1, 27.0, 12.0, 11.0, amb=0.35), lo=1, hi=4, dith=0.5)
    cheek = SYM(P([(14.5, 32.0), (20.0, 33.5), (25.5, 43.5), (19.0, 39.0)]))
    L.put(cheek & head, CRM[4])
    L.put(cheek & head & (PY > 38), CRM[3])
    for s in (False, True):
        e = pts_mask([(19, 30), (20, 30), (21, 31), (20, 31)])
        L.put(MIR(e) if s else e, '#1c0e0a')
        L.put(MIR(pts_mask([(20, 30)])) if s else pts_mask([(20, 30)]), '#ffcc40')
    L.put(R(24, 41, 27, 42) | R(25, 43, 26, 43), '#160a0a')
    L.put(pts_mask([(24, 41)]), '#5a4a5a')
    return {'halo': (cx, 40.0, 18.0)}


PH = ['#5a0e0a', '#a4200e', '#e04a12', '#f88a1e', '#ffc23a', '#ffec88', '#fffbe0']


def fm_phoenix(L, a):
    cx = 25.5
    glow(a, cx, 38, 21, ['#2e1846', '#3c1e4a', '#4c244c', '#5c2a4c'])
    tails = np.zeros((H, W), bool)
    for (ex, ey, w) in ((cx, 65.0, 3.2), (17.0, 62.0, 2.8), (34.0, 62.0, 2.8)):
        tails |= THP(bez((cx, 46.0), ((cx + ex) / 2, 54.0), (ex, ey), n=12), w)
    L.shade(tails, PH, 1 - f_lin(0, 46, 0, 65), lo=1, hi=4, dith=0.6)
    wing = P([(24.0, 36.0), (18.0, 31.0), (12.0, 24.0), (7.5, 16.5), (9.5, 24.5), (7.0, 26.0), (10.5, 31.0),
              (8.0, 33.0), (13.0, 37.0), (11.0, 39.5), (17.0, 41.0), (16.0, 44.0), (23.0, 44.0)])
    wing = SYM(wing)
    L.shade(wing, PH, 0.25 + 0.7 * f_rad(cx, 38.0, 19.0, 17.0), lo=1, hi=5, dith=0.8)
    L.put(SYM(THP([(22.0, 37.0), (14.0, 30.0), (9.0, 20.0)], 1.0)) & wing, PH[4])
    body = E(cx, 40.0, 4.0, 7.5)
    L.shade(body, PH, f_sphere(cx, 38.0, 5.0, 8.0), lo=3, hi=6)
    head = C(cx, 29.5, 3.2)
    L.shade(head, PH, f_sphere(cx, 28.5, 3.2), lo=3, hi=6)
    crest = (THP([(cx, 27.0), (cx, 19.0)], 1.6) | THP([(24.5, 27.5), (21.0, 21.0)], 1.4)
             | THP([(26.5, 27.5), (30.0, 21.0)], 1.4))
    L.put(crest, PH[4])
    L.put(pts_mask([(25, 18), (20, 20), (30, 20)]), PH[5])
    beak = P([(24.5, 31.0), (26.5, 31.0), (25.5, 34.0)])
    L.put(beak, GOLD[2])
    L.put(pts_mask([(24, 29), (26, 29)]), '#2a0808')
    return {'halo': False}


# =====================================================================================  black market motifs
BONE = ['#3a3226', '#6a5e48', '#9c8e6e', '#c8bc98', '#ebe3c8']
IRB = ['#121114', '#232126', '#38353c', '#555058', '#7c7680', '#a8a2aa']
SLB = ['#222228', '#3e3e48', '#62626e', '#8e8e9a', '#c4c4cc', '#eeeef4']
BRS = ['#2a1e0a', '#4e3a14', '#7a5c22', '#a8843a', '#d0b060', '#efd890']
PAP = ['#3a3020', '#62563c', '#8e8060', '#b8aa84', '#d8ceaa']
LTH = ['#1a100c', '#2e1c14', '#4a2e1e', '#6a4428', '#8e6038']
BLD = ['#2a0508', '#560a10', '#8c1018', '#c41e26', '#f04a40', '#ff9a80']
TOX = ['#0c2010', '#16401c', '#22702a', '#3ea83a', '#86e05a', '#ccff9a']
MNY = ['#16261a', '#24402a', '#3a6040', '#5a8a5a', '#8ab884', '#c4e4b4']
GHO = ['#1a3a3a', '#2a6060', '#4a9a90', '#80d0c0', '#c8fff0']
SMK = ['#2a2630', '#3e3846', '#58505e', '#7a7280', '#a8a0aa']
IVO = ['#5a5040', '#968a70', '#cfc4a4', '#efe8d0', '#fffcf0']
SACK = ['#2e2214', '#4e3a22', '#705636', '#957650', '#b89a6c']
PRD = ['#1a0e1e', '#2e1a36', '#4a2a56', '#6a3e7a', '#9060a8']
JADE = ['#0e1e1a', '#18332a', '#264e3c', '#3a6e52', '#5a9270']

RIM = '#ff3a22'


def iso_cube(cx, y0, s, h):
    """isometric cube masks + face corner points (top rhombus 2:1.2)."""
    T = (cx, y0)
    Lv = (cx - s, y0 + s * 0.58)
    Rv = (cx + s, y0 + s * 0.58)
    B = (cx, y0 + s * 1.16)
    top = P([T, Rv, B, Lv])
    left = P([Lv, B, (B[0], B[1] + h), (Lv[0], Lv[1] + h)])
    right = P([B, Rv, (Rv[0], Rv[1] + h), (B[0], B[1] + h)])
    return top, left, right, (T, Lv, Rv, B)


PIPS = {1: [(0.5, 0.5)], 2: [(0.25, 0.25), (0.75, 0.75)], 3: [(0.22, 0.22), (0.5, 0.5), (0.78, 0.78)],
        4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
        5: [(0.22, 0.22), (0.78, 0.22), (0.5, 0.5), (0.22, 0.78), (0.78, 0.78)],
        6: [(0.25, 0.2), (0.75, 0.2), (0.25, 0.5), (0.75, 0.5), (0.25, 0.8), (0.75, 0.8)]}


def flame(cx, base, h, w, lean=0.0):
    """organic flame tongue: base centre (cx, base), height h, half width w, tip leaning by `lean` px."""
    tip = (cx + lean, base - h)
    left = bez((cx - w, base), (cx - w * 1.15, base - h * 0.45), (cx + lean * 0.3 - w * 0.2, base - h * 0.8), tip, n=12)
    right = bez(tip, (cx + lean * 0.2 + w * 0.5, base - h * 0.6), (cx + w * 1.1, base - h * 0.35), (cx + w, base), n=12)
    return P(left + right[1:] + [(cx, base + w * 0.5)])


def face_pips(o, eu, ev, n, top=False):
    """pips as crisp pixel blobs at the projected positions: 3x2 on the top face, 2x2 on the sides."""
    m = np.zeros((H, W), bool)
    for (u, v) in PIPS[n]:
        x = o[0] + u * eu[0] + v * ev[0]
        y = o[1] + u * eu[1] + v * ev[1]
        if top:
            m |= R(int(math.floor(x)) - 1, int(round(y)) - 1, int(math.floor(x)) + 1, int(round(y)))
        else:
            m |= R(int(round(x)) - 1, int(round(y)) - 1, int(round(x)), int(round(y)))
    return m


def draw_die(L, cx, y0, s, h, rt, rl, rr, pipcol, pips=(1, 2, 3), lev=(3, 2, 1), pipdark=None,
             psize=(0.2, 0.19)):
    top, left, right, (T, Lv, Rv, B) = iso_cube(cx, y0, s, h)
    L.put(top, rt[lev[0]])
    L.put(left, rl[lev[1]])
    L.put(right, rr[lev[2]])
    # bevelled edges
    L.put(border(top) & ~nb(top, 0, -1) & (PY < T[1] + 2), rt[min(len(rt) - 1, lev[0] + 1)])
    L.put(top & nb(left | right, 0, 1) & ~nb(top, 0, 1), rt[min(len(rt) - 1, lev[0] + 1)])
    L.put(left & ~nb(left, -1, 0), rl[min(len(rl) - 1, lev[1] + 1)])
    L.put(right & ~nb(right, 1, 0), rr[max(0, lev[2] - 1)])
    L.put(left & ~nb(left, 0, 1), rl[max(0, lev[1] - 1)])
    L.put(right & ~nb(right, 0, 1), rr[max(0, lev[2] - 1)])
    pt = face_pips(T, (Rv[0] - T[0], Rv[1] - T[1]), (Lv[0] - T[0], Lv[1] - T[1]), pips[0], top=True)
    pl = face_pips(Lv, (B[0] - Lv[0], B[1] - Lv[1]), (0, h), pips[1])
    pr = face_pips(B, (Rv[0] - B[0], Rv[1] - B[1]), (0, h), pips[2])
    L.put(pt & top, pipcol[2])
    L.put(pl & left, pipcol[1])
    L.put(pr & right, pipcol[0])
    if pipdark:
        L.put((pt & top) & ~nb(pt, 0, 1), pipdark)
    return top | left | right, (T, Lv, Rv, B)


def bm_loaded_dice(L, a):
    # lead ball + chain, then the die
    ball = C(36.0, 56.5, 6.0)
    L.shade(ball, IRB, f_sphere(36.0, 56.5, 6.0, amb=0.2), lo=1, hi=5, dith=0.6)
    chain = np.zeros((H, W), bool)
    for i, (x, y) in enumerate(((24.5, 47.0), (27.0, 49.5), (29.5, 51.0), (32.0, 52.0))):
        if i % 2 == 0:
            chain |= RING(x, y, 0.8, 2.0, 0.6, 1.6)
        else:
            chain |= E(x, y, 2.0, 1.0) & ~E(x, y, 1.0, 0.3)
    L.put(chain, IRB[3])
    L.put(chain & ~nb(chain, 0, -1), IRB[4])
    m, (T, Lv, Rv, B) = draw_die(L, 23.5, 18.0, 13.0, 14.0, IVO, IVO, IVO, ['#5a0a10', BLD[2], BLD[3]],
                                 pips=(5, 2, 3), lev=(4, 3, 2))
    # lead plug visible in the side face
    plug = E(17.5, 41.0, 2.2, 2.6)
    L.put(dilate(plug) & m, IVO[1])
    L.shade(plug, IRB, f_sphere(17.0, 40.5, 2.4), lo=2, hi=4)
    return {}


def bm_counterfeit(L, a):
    # stack of bills (side stripes), top bill with a skull portrait, red band
    top = P([(9.0, 33.0), (31.0, 24.0), (43.0, 33.0), (21.0, 42.0)])
    sides = P([(9.0, 33.0), (21.0, 42.0), (21.0, 54.0), (9.0, 45.0)]) | P([(21.0, 42.0), (43.0, 33.0), (43.0, 45.0), (21.0, 54.0)])
    L.put(sides, MNY[3])
    for y in range(0, 14, 2):
        L.put(sides & (np.abs(PY - (33 + y + (PX - 9) * (9 / 12.0) * (PX < 21) + (9 - (PX - 21) * 9 / 22.0) * (PX >= 21))) < 0.6), MNY[4])
    L.put(sides & (PX >= 21), MNY[1])
    for y in range(0, 14, 2):
        yy = 42 + y - (PX - 21) * 9.0 / 22.0
        L.put(sides & (PX >= 21) & (np.abs(PY - yy) < 0.55), MNY[2])
    L.shade(top, MNY, 0.7 - 0.3 * f_lin(9, 33, 43, 33), lo=2, hi=4)
    inner = P([(12.5, 33.0), (31.0, 25.5), (39.5, 33.0), (21.0, 40.5)])
    L.put(border(inner), MNY[2])
    port = E(29.0, 31.5, 5.0, 3.8)
    L.put(port, MNY[5])
    L.put(border(port), MNY[2])
    sk = ascii_mask(['.###.', '#####', '#.#.#', '.###.', '.#.#.'], 27, 29)
    L.put(sk, MNY[1])
    for (x, y) in ((15, 33), (35, 33)):
        L.put(C(x + 0.5, y + 0.5, 1.4), MNY[2])
    band = ((P([(10.5, 32.75), (16.5, 30.25), (28.5, 39.75), (22.5, 42.25)]) & top)
            | (P([(22.5, 42.25), (28.5, 39.75), (28.5, 51.75), (22.5, 54.25)]) & sides))
    L.put(band, BLD[3])
    L.put(band & sides, BLD[2])
    L.put(band & ~nb(band, 0, -1), BLD[4])
    # a loose bill sticking out, off-colour (the fake)
    loose = P([(5.5, 51.0), (21.0, 45.0), (29.0, 52.0), (13.5, 58.0)])
    L.shade(loose, ['#2a2236', '#463a52', '#6a5a6e', '#8e7e8a', '#b0a2a6'], 0.8 - 0.4 * f_lin(5, 51, 29, 52), lo=1, hi=3)
    L.put(border(P([(8.5, 51.0), (21.0, 46.5), (26.0, 52.0), (13.5, 56.5)])), '#463a52')
    L.put(C(17.0, 51.5, 1.6), TOX[3])
    return {}


def bm_rigged_shaker(L, a):
    cx, cy = 25.5, 31.0
    # wooden box base
    btop = P([(14.0, 48.0), (37.0, 48.0), (40.0, 51.5), (11.0, 51.5)])
    L.put(btop, LTH[4])
    front = R(11, 52, 40, 61)
    L.shade(front, LTH, f_cyl(cx, 16.0, 0.2), lo=1, hi=3)
    L.put(R(11, 52, 40, 52), BRS[4])
    L.put(R(11, 61, 40, 61), LTH[0])
    for x in (13, 38):
        L.put(R(x, 54, x, 54), BRS[3])
    collar = E(cx, 46.5, 9.0, 2.8)
    L.shade(collar, BRS, f_cyl(cx, 9.0), lo=1, hi=5)
    ball = C(cx, cy, 13.0)
    L.shade(ball, ['#0e1a1a', '#14282a', '#1c3a3a', '#2a5250', '#3e7068'], f_rad(cx + 1.5, cy + 2, 14.0), lo=0, hi=4, dith=0.8)
    # die inside
    draw_die(L, 25.5, 30.0, 6.0, 6.0, IVO, IVO, IVO, [BLD[2], BLD[2], BLD[3]], pips=(1, 2, 2), lev=(3, 2, 1))
    L.put(ARC(cx, cy, 10.5, 200, 250, 1.4) & ball, '#9ae8d8')
    L.put(R(17, 23, 18, 24), '#e8fff8')
    L.put(border(ball) & (PX > cx) & (PY > cy), '#4e8a80')
    # the hidden switch (front of the box) + wires
    sw_plate = R(16, 54, 23, 59)
    L.bevel(sw_plate, IRB, 3, up=1, dn=2)
    L.put(R(18, 56, 21, 57), IRB[0])
    lever = TH(19.5, 56.5, 15.0, 52.5, 1.4)
    L.put(lever, SLB[4])
    L.put(C(14.5, 52.0, 1.5), BLD[4])
    L.put(pts_mask([(14, 51)]), BLD[5])
    wire = THP(bez((22.5, 58.0), (27.0, 64.0), (31.0, 63.0), (36.0, 65.0), n=16), 1.0)
    L.put(wire, BLD[3])
    wire2 = THP(bez((21.0, 59.5), (22.0, 64.0), (16.0, 63.0), (10.0, 65.5), n=12), 1.0)
    L.put(wire2, TOX[3])
    return {}


GUM = [('#8a1818', '#c42a2a', '#ff7060'), ('#9a7a10', '#d8b020', '#fff070'), ('#1a3a90', '#2a5ad0', '#80b0ff'),
       ('#1a6a28', '#2a9a3a', '#80e070'), ('#902a6a', '#d04a9a', '#ff9ad8'), ('#8a8a90', '#c8c8c8', '#ffffff')]


def gumball(L, x, y, k, r=2.7):
    b = C(x, y, r)
    L.put(b, GUM[k][1])
    L.put(b & ~nb(b, 1, 1), GUM[k][0])
    L.put(pts_mask([(int(x) - 1, int(y) - 1)]), GUM[k][2])


def bm_smuggled_gumballs(L, a):
    cx = 25.5
    # open burlap sack, rim rolled down, full of gum balls
    sack = P([(11.0, 34.0), (40.0, 34.0), (42.5, 46.0), (41.0, 57.0), (36.0, 62.0), (15.0, 62.0), (10.0, 57.0),
              (8.5, 46.0)])
    L.shade(sack, SACK, f_sphere(cx - 4, 42.0, 19.0, 18.0, amb=0.25), lo=1, hi=4, dith=0.5)
    weave = sack & ((((XX + YY) % 4) == 0) | (((XX - YY) % 4) == 0)) & ~border(sack)
    L.put(weave & (YY > 38), SACK[2])
    # contraband stencil: a red skull stamp on the sack
    sk = ascii_mask(SKULL5, 23, 48)
    L.put(sk, BLD[2])
    L.put(border(R(21, 46, 29, 54)) & ~R(21, 46, 21, 46) & ~R(29, 54, 29, 54), BLD[2])
    # gum balls heaped in the opening (behind the rim)
    heap = [(15.0, 32.0, 0), (20.0, 30.0, 2), (25.5, 29.5, 4), (31.0, 30.0, 3), (36.0, 32.0, 1),
            (17.5, 27.0, 5), (23.0, 25.5, 1), (28.5, 25.5, 0), (33.5, 27.5, 2), (26.0, 21.5, 3)]
    for (x, y, k) in heap:
        gumball(L, x, y, k)
    # rolled-down rim
    rim = E(cx, 34.5, 16.0, 3.4)
    L.shade(rim, SACK, 1 - f_lin(0, 31, 0, 38), lo=2, hi=4)
    L.put(rim & ~nb(rim, 0, 1), SACK[1])
    L.put(rim & ((XX % 3) == 0) & ~border(rim), SACK[2])
    # spilled ones
    for (x, y, k) in ((8.0, 64.0, 2), (13.5, 65.5, 4), (34.5, 65.0, 0)):
        gumball(L, x, y, k)
    return {}


def bm_forged_diploma(L, a):
    paper = R(12, 22, 38, 54)
    L.shade(paper, PAP, 0.85 - 0.5 * f_lin(12, 22, 38, 54), lo=1, hi=4, dith=0.6)
    for (y, x0, x1) in ((27, 16, 34), (31, 15, 35), (34, 15, 31), (37, 15, 33), (40, 15, 27)):
        L.put(R(x0, y, x1, y) & ((XX * 7 + y) % 5 != 0), PAP[1])
    for y in (20.0, 55.5):
        roll = E(25.5, y, 15.0, 2.6)
        L.shade(roll, PAP, 1 - f_lin(0, y - 2.5, 0, y + 2.5), lo=1, hi=4)
        for x in (10.0, 41.0):
            L.shade(E(x, y, 1.5, 2.6), PAP, f_sphere(x, y, 1.6, 2.6), lo=0, hi=2)
    # fake seal: lopsided red wax with a smudged imprint, ribbon tails
    rib = P([(28.0, 48.0), (31.0, 49.0), (29.5, 61.0), (27.5, 59.0), (25.5, 61.0)])
    rib2 = P([(32.0, 48.0), (35.0, 48.0), (37.5, 60.0), (35.0, 58.5), (33.0, 60.5)])
    L.bevel(rib | rib2, BLD, 2, up=1, dn=1)
    seal = E(31.5, 46.0, 5.2, 4.8)
    L.shade(seal, BLD, f_sphere(31.0, 45.0, 5.5, 5.0), lo=1, hi=4)
    L.put(C(31.5, 46.0, 3.0) & ~C(31.0, 45.5, 2.0), BLD[2])
    L.put(pts_mask([(30, 45), (32, 46), (31, 47)]), BLD[1])
    # crude scribble signature
    sig = POLYL([(14, 47), (16, 44), (17, 48), (19, 45), (21, 48), (23, 46)])
    L.put(sig, '#2a1a40')
    return {}


PLUM = ['#1c1220', '#2c1c34', '#3e2848', '#54365e', '#6c4878']


def bm_pickpocket(L, a):
    # the coat (background fabric, no outline) with its front edge and a button
    coat = P([(5.0, 33.0), (46.0, 30.0), (46.0, 74.0), (5.0, 74.0)])
    a[coat & ART_F] = hexc('#1e1424')
    a[coat & ART_F & (((XX * 2 + YY) % 5) == 0)] = hexc('#24182c')
    a[SEG(5, 33, 46, 30) & ART_F] = hexc('#3a2846')
    # gaping opening of the patch pocket
    L.put(E(25.5, 42.0, 15.0, 3.2), '#08060a')
    # black leather glove coming from the upper right, fingers dipping into the pocket
    sleeve = P([(32.0, 11.0), (46.0, 11.0), (46.0, 24.0), (40.0, 28.5), (30.5, 20.0)])
    L.shade(sleeve, ['#1a0c10', '#2a1218', '#3e1a22', '#55242e', '#6e3440'], f_cyl(38.0, 8.0), lo=1, hi=4)
    cuff = THP([(30.0, 21.0), (40.5, 29.0)], 2.8)
    L.put(cuff, BLD[3])
    L.put(cuff & ~nb(cuff, 0, -1), BLD[4])
    for (p0, p1) in (((24.5, 34.0), (22.0, 46.0)), ((28.5, 35.0), (27.0, 47.0)), ((32.5, 34.0), (32.0, 46.0))):
        m = TH(p0[0], p0[1], p1[0], p1[1], 3.4)
        L.shade(m, IRB, f_cyl(p0[0] - 0.5, 1.8), lo=1, hi=4)
        L.put(m & ~nb(m, 1, 0), IRB[1])
    hand = P([(22.0, 27.0), (30.0, 21.5), (38.0, 28.0), (34.5, 35.5), (24.0, 36.5)])
    L.shade(hand, IRB, f_sphere(27.0, 25.0, 12.0, 11.0, amb=0.3), lo=1, hi=5, dith=0.4)
    for (x0, y0, x1, y1) in ((27, 26, 25, 33), (30, 26, 29, 34), (33, 28, 32, 33)):
        L.put(SEG(x0, y0, x1, y1), IRB[2])
    thumb = TH(23.5, 30.0, 17.5, 37.5, 3.2)
    L.shade(thumb, IRB, f_cyl(20.0, 1.8), lo=2, hi=5)
    L.put(thumb & ~nb(thumb, 0, 1), IRB[1])
    L.put(pts_mask([(25, 25), (24, 26), (26, 24)]), IRB[5])
    # pocket front covers the finger tips
    front = P([(10.0, 42.5), (41.0, 41.5), (41.0, 58.0), (38.0, 62.0), (13.0, 62.5), (10.0, 59.0)])
    L.c[front] = 0
    L.shade(front, PLUM, 1 - 0.6 * f_lin(0, 41, 0, 64), lo=1, hi=4, dith=0.5)
    L.put(front & ~nb(front, 0, -1), PLUM[4])
    stitch = border(P([(12.0, 44.5), (39.0, 43.5), (39.0, 57.0), (36.5, 60.5), (14.5, 61.0), (12.0, 58.0)])) & ((XX + YY) % 2 == 0)
    L.put(stitch & front, PLUM[1])
    # gold watch dangling out of the pocket on its chain
    chain = THP(bez((14.0, 42.0), (9.0, 46.0), (12.5, 50.5), n=10), 1.1)
    L.put(chain, BRS[4])
    L.put(chain & ((XX + YY) % 2 == 0), BRS[2])
    wx, wy = 14.5, 55.0
    L.put(RING(13.5, 50.5, 0.5, 1.6), BRS[4])
    L.shade(C(wx, wy, 4.4), BRS, f_sphere(wx - 1, wy - 1, 4.6), lo=1, hi=5)
    L.put(C(wx, wy, 3.0), IVO[3])
    L.put(C(wx, wy, 3.0) & ~nb(C(wx, wy, 3.0), -1, -1), IVO[1])
    L.put(SEG(14, 55, 14, 53) | SEG(14, 55, 16, 55), '#1a1416')
    return {'glow': (25.5, 38.0, 19.0)}


def bm_insider_tip(L, a):
    # folded note sticking out of the envelope (behind)
    note = P([(13.0, 19.0), (33.0, 16.0), (35.0, 36.0), (15.0, 38.0)])
    L.shade(note, PAP, 0.95 - 0.35 * f_lin(13, 16, 35, 38), lo=2, hi=4)
    fold = SEG(14, 28, 34, 25)
    L.put(fold & note, PAP[2])
    L.put(nb(fold, 0, -1) & note, PAP[4])
    for (y, x1) in ((22, 29), (25, 23)):
        L.put(SEG(17, y, x1, y - 1) & ((XX % 4) != 0) & note, '#3a2a40')
    L.put(SEG(17, 31, 27, 30) & ((XX % 3) != 0) & note, '#3a2a40')
    L.put(ARC(28.0, 30.5, 2.3, 0, 360, 1.0) & note, BLD[3])
    # envelope
    env = R(8, 33, 43, 58)
    L.shade(env, ['#3a3020', '#5a4c34', '#7e6e4e', '#9e8e68', '#b8aa84'], 0.85 - 0.45 * f_lin(8, 33, 43, 58), lo=1, hi=4)
    L.put(SEG(8, 58, 22, 47) | SEG(43, 58, 29, 47), '#5a4c34')
    flap = P([(8.0, 33.0), (43.0, 33.0), (25.5, 48.0)])
    L.shade(flap, ['#3a3020', '#5a4c34', '#7e6e4e', '#9e8e68', '#c4b690'], 0.9 - 0.4 * f_lin(0, 33, 0, 48), lo=2, hi=4)
    L.put(border(flap) & ~nb(flap, 0, -1), '#5a4c34')
    L.put(R(8, 33, 43, 33), '#c4b690')
    # red wax seal with an eye
    sx, sy = 25.5, 47.5
    seal = C(sx, sy, 5.0) | C(21.0, 50.5, 1.4) | C(30.5, 50.0, 1.2)
    L.put(seal, WAX[3])
    L.put(seal & ~nb(seal, 1, 1), WAX[2])
    L.put(seal & ~nb(seal, -1, -1), WAX[4])
    eye = lens(sx, sy, 7.0, 3.6)
    L.put(eye, WAX[5])
    L.put(C(sx, sy, 1.5), WAX[1])
    L.put(eye & ~nb(eye, 0, -1), WAX[2])
    return {}


BAG = ['#2a1a10', '#4a3020', '#6e4a2e', '#946a40', '#b88c58', '#d8b07a']
TIE = ['#060608', '#121016', '#221e2a', '#3a3446', '#5a5268']


def bm_bribed_croupier(L, a):
    cx = 25.5
    # coins peeking out of the bag
    for (x, y) in ((21.0, 22.5), (29.5, 21.5), (25.5, 19.5)):
        c = E(x, y, 3.4, 2.2)
        L.shade(c, BRS, f_sphere(x, y - 0.5, 3.4, 2.4), lo=2, hi=5)
        L.put(E(x, y + 1.0, 3.4, 1.4) & ~c, BRS[1])
    bag = P([(16.0, 37.0), (20.0, 33.0), (31.0, 33.0), (35.0, 37.0), (41.0, 47.0), (39.5, 58.0), (25.5, 62.0),
             (11.5, 58.0), (10.0, 47.0)])
    L.shade(bag, BAG, f_sphere(cx - 3, 43.0, 18.0, 17.0, amb=0.3), lo=1, hi=5, dith=0.5)
    neck = P([(19.0, 33.5), (32.0, 33.5), (35.5, 24.0), (30.0, 27.0), (25.5, 23.5), (21.0, 27.0), (15.5, 24.0)])
    L.shade(neck, BAG, f_cyl(cx, 9.0), lo=2, hi=4)
    L.put(SEG(20, 27, 21, 32) | SEG(30, 27, 30, 32), BAG[2])
    # coin emblem
    cm = C(cx, 48.5, 5.6)
    L.shade(cm, BRS, f_sphere(cx - 1, 47.0, 6.4), lo=2, hi=5)
    L.put(RING(cx, 48.5, 3.4, 4.4), BRS[2])
    L.put(R(25, 46, 26, 51), BRS[2])
    # the croupier's bow tie tied around the neck of the bag
    bt = P([(25.5, 33.0), (16.0, 28.5), (17.0, 33.0), (15.5, 38.0)]) | P([(25.5, 33.0), (35.0, 28.5), (34.0, 33.0), (35.5, 38.0)])
    L.shade(bt, BLD, 1 - f_lin(15, 28, 36, 38), lo=1, hi=4)
    L.put(bt & ~nb(bt, 0, -1), BLD[5])
    L.put(SEG(19, 31, 19, 35) | SEG(32, 31, 32, 35), BLD[1])
    knot = R(24, 31, 27, 35)
    L.put(knot, BLD[2])
    L.put(R(24, 31, 27, 31), BLD[4])
    # spilled coins
    for (x, y) in ((8.5, 61.0), (42.0, 60.5)):
        c = E(x, y, 3.4, 2.0)
        L.shade(c, BRS, f_sphere(x, y - 0.5, 3.4, 2.2), lo=1, hi=4)
        L.put(E(x, y + 1.2, 3.4, 1.2) & ~c, BRS[1])
    return {}


def bm_cursed_idol(L, a):
    cx = 25.5
    glow(a, cx, 33, 13, ['#2a1214', '#3a1416'])
    ped = R(14, 56, 37, 61)
    L.bevel(ped, IRB, 3, up=1, dn=2)
    L.put(R(16, 54, 35, 55), IRB[2])
    body = P([(17.0, 42.0), (34.0, 42.0), (36.0, 54.0), (15.0, 54.0)])
    L.shade(body, JADE, f_cyl(cx, 11.0), lo=1, hi=4)
    L.put(R(23, 47, 28, 47) & body, JADE[1])
    L.put(SEG(17, 46, 22, 49) | SEG(34, 46, 29, 49), JADE[1])
    legs = R(18, 52, 22, 55) | R(29, 52, 33, 55)
    L.put(R(23, 51, 28, 54), JADE[0])
    head = P([(13.0, 21.0), (38.0, 21.0), (36.0, 42.0), (15.0, 42.0)])
    L.shade(head, JADE, f_cyl(cx, 13.0), lo=1, hi=4)
    crest = P([(15.0, 21.0), (19.0, 13.5), (22.0, 19.0), (25.5, 12.5), (29.0, 19.0), (32.0, 13.5), (36.0, 21.0)])
    L.shade(crest, JADE, 1 - f_lin(0, 13, 0, 21), lo=1, hi=4)
    # brow, eyes (red glow), nose, mouth
    L.put(R(15, 26, 36, 27), JADE[0])
    for x in (17, 29):
        eye = R(x, 28, x + 4, 31)
        L.put(eye, '#1a0404')
        L.put(R(x + 1, 29, x + 3, 30), BLD[4])
        L.put(pts_mask([(x + 2, 29)]), '#ffd0a0')
    nose = P([(24.0, 29.0), (27.0, 29.0), (28.0, 35.0), (23.0, 35.0)])
    L.put(nose, JADE[3])
    L.put(nose & (PX > 25.5), JADE[2])
    mouth = R(18, 37, 33, 40)
    L.put(mouth, '#120808')
    for x in range(19, 33, 2):
        L.put(R(x, 37, x, 37) | R(x + 1, 40, x + 1, 40), BONE[3])
    for (x, y) in ((22, 33), (30, 24), (16, 47)):
        L.put(pts_mask([(x, y)]), JADE[0])
    return {'glow': (25.5, 33.0, 19.0)}


def bm_weighted_coin(L, a):
    cx, cy = 23.5, 36.5
    # coin standing slightly turned: thick reeded edge on the right
    edge = E(cx + 2.5, cy + 0.5, 11.0, 14.0)
    L.put(edge, BRS[1])
    L.put(edge & (YY % 2 == 0) & (PX > cx + 6), BRS[2])
    face = E(cx, cy, 11.0, 14.0)
    L.put(face, BRS[3])
    L.put(face & ((PX - cx) * 0.9 + (PY - cy) * 0.6 < -5), BRS[4])
    inner = E(cx, cy, 9.0, 12.0)
    L.put(border(inner) & ~nb(inner, -1, -1), BRS[2])
    L.put(border(inner) & ~nb(inner, 1, 1), BRS[5])
    for k in range(16):
        t = k * 2 * math.pi / 16
        L.put(pts_mask([(int(cx + 7.4 * math.cos(t)), int(cy + 10.2 * math.sin(t)))]), BRS[2])
    # the drilled-in lead plug
    plug = E(cx, cy, 4.0, 5.0)
    L.put(dilate(plug) & face, BRS[1])
    L.shade(plug, IRB, f_sphere(cx - 1.2, cy - 1.8, 4.5, 5.5, amb=0.25), lo=1, hi=5)
    for (x, y) in ((16, 29), (29, 44), (30, 27)):
        L.put(R(x, y, x + 1, y), BRS[2])
    # a cast-iron weight with a handle beside it
    wt = P([(31.5, 54.0), (41.5, 54.0), (43.5, 63.0), (29.5, 63.0)])
    L.shade(wt, IRB, f_cyl(36.5, 7.0, 0.3), lo=1, hi=4)
    L.put(R(30, 54, 43, 54) & wt, IRB[4])
    L.put(R(34, 51, 39, 53), IRB[2])
    L.put(R(34, 51, 39, 51), IRB[4])
    L.put(ARC(36.5, 51.0, 2.6, 180, 360, 1.3), IRB[3])
    return {}


def bm_black_cat_bone(L, a):
    cx = 25.5
    CAT = ['#08070a', '#121016', '#1c1922', '#2a2532', '#3c3546']
    tail = THP(bez((33.0, 58.0), (43.0, 57.0), (43.0, 44.0), (39.0, 38.0), n=20), 3.0)
    L.put(tail, CAT[2])
    body = E(cx, 50.0, 9.5, 11.0) | P([(18.0, 52.0), (33.0, 52.0), (35.0, 61.0), (16.0, 61.0)])
    L.shade(body, CAT, f_sphere(cx - 2, 46.0, 12.0, 13.0, amb=0.3), lo=1, hi=3)
    head = E(cx, 32.0, 9.0, 7.5)
    ears = SYM(P([(17.0, 30.0), (17.0, 20.0), (23.0, 26.0)]))
    L.shade(head | ears, CAT, f_sphere(cx - 2, 28.0, 10.0, 9.0, amb=0.3), lo=1, hi=3)
    L.put(SYM(P([(18.0, 27.0), (18.2, 22.5), (21.0, 25.5)])), BLD[1])
    # green eyes
    for x in (20.5, 30.5):
        e = lens(x, 31.5, 4.4, 3.2)
        L.put(e, TOX[4])
        L.put(e & (PY > 31.5), TOX[3])
        L.put(R(int(x), 30, int(x), 32), '#050806')
    L.put(pts_mask([(25, 35), (26, 35)]), '#3a2a34')
    # paws
    for x0 in (19, 28):
        L.put(R(x0, 59, x0 + 3, 61), CAT[3])
    # bone in front
    bone = TH(13.0, 63.0, 38.0, 57.0, 2.6)
    ends = C(12.0, 61.5, 1.8) | C(12.5, 64.5, 1.8) | C(38.5, 55.5, 1.8) | C(39.5, 58.5, 1.8)
    L.shade(bone | ends, BONE, 1 - f_lin(0, 55, 0, 66), lo=2, hi=4)
    L.put(bone & ~nb(bone, 0, 1) & ~ends, BONE[1])
    return {'glow': (25.5, 40.0, 19.0)}


def bm_snake_oil(L, a):
    cx = 25.5
    body = E(cx, 47.5, 10.5, 11.5) | R(15, 47, 36, 56)
    neck = R(22, 24, 29, 37)
    bottle = body | neck | E(cx, 37.0, 6.5, 3.0)
    L.shade(bottle, ['#0a1a10', '#12301c', '#1c4a2a', '#2a663a', '#3e8a4e'], f_cyl(cx, 11.0, 0.4), lo=1, hi=4)
    liq = (body & (PY > 43)) | (E(cx, 43.0, 10.0, 1.5) & body)
    L.shade(liq, TOX, f_cyl(cx, 10.0, 0.4), lo=1, hi=4, dith=0.6)
    L.put(E(cx, 43.0, 9.5, 1.2) & body, TOX[4])
    L.put(SEG(17, 46, 17, 53) | SEG(23, 27, 23, 34), '#b8f0c8')
    cork = R(22, 18, 29, 23)
    L.bevel(cork, LTH, 3, up=1, dn=2)
    L.put(R(21, 23, 30, 24), BRS[3])
    label = R(17, 48, 34, 56)
    L.shade(label, PAP, 0.8 - 0.4 * f_lin(17, 48, 34, 56), lo=2, hi=4)
    L.put(border(label), PAP[1])
    # snake wrapped around the bottle
    path = bez((9.0, 60.0), (24.0, 66.0), (40.0, 50.0), (30.0, 42.0), n=20) + bez((30.0, 42.0), (20.0, 36.0), (13.0, 40.0), (19.0, 32.0), n=14)[1:]
    sn = THP(path, 2.8)
    L.shade(sn, BLD, f_lin(0, 66, 0, 30), lo=2, hi=4)
    L.put(sn & ~nb(sn, 0, -1), BLD[4])
    head = E(19.5, 30.0, 2.8, 2.0)
    L.shade(head, BLD, f_sphere(19.0, 29.5, 3.0, 2.0), lo=2, hi=5)
    L.put(pts_mask([(18, 29)]), '#ffd040')
    L.put(SEG(16, 30, 14, 30) | pts_mask([(13, 29), (13, 31)]), TOX[4])
    return {}


def bm_fake_crown(L, a):
    cx = 25.5
    spikes = [((10.0, 45.0), (9.5, 32.0), (16.0, 45.0)), ((14.0, 45.0), (17.0, 28.0), (21.5, 45.0)),
              ((20.5, 45.0), (25.5, 22.0), (30.5, 45.0)), ((29.5, 45.0), (35.5, 29.5), (37.0, 45.0)),
              ((35.0, 45.0), (44.0, 36.0), (41.0, 45.0))]
    sp = np.zeros((H, W), bool)
    for (p0, p1, p2) in spikes:
        sp |= P([p0, p1, p2])
    band = R(10, 44, 41, 52) | E(cx, 52.0, 15.5, 2.5)
    crown = sp | band
    L.shade(crown, BRS, f_cyl(cx, 16.0, 0.25), lo=2, hi=5)
    L.put(R(10, 44, 41, 44) & crown, BRS[5])
    L.put(R(10, 46, 41, 46) & crown, BRS[2])
    # chipped paint: grey metal shows through in a few patches
    chips = crown & (value_field(2.0, 11) < 0.2) & ~border(crown)
    L.put(chips, IRB[3])
    L.put(chips & ~nb(chips, 0, -1), IRB[1])
    L.put(chips & ~nb(chips, 1, 0), IRB[4])
    # glass gems: one missing (empty socket)
    for (x, col, rr) in ((25.5, BLD, 2.6), (17.0, TOX, 1.9), (34.0, None, 1.9)):
        g = E(x, 48.8, rr, rr)
        L.put(dilate(g) & band, IRB[1])
        if col is None:
            L.put(g, '#0a0a0c')
            L.put(g & (PY > 49.5), IRB[2])
        else:
            L.shade(g, col, f_sphere(x, 48.5, rr), lo=1, hi=4)
    for (x, y) in ((9.5, 31.5), (17.0, 27.5), (25.5, 21.0), (44.5, 35.5)):
        L.shade(C(x, y, 1.8), BONE, f_sphere(x, y, 1.8), lo=1, hi=3)
    # paint flakes falling
    for (x, y) in ((40, 56), (42, 60), (37, 61)):
        L.put(R(x, y, x + 1, y), BRS[4])
    return {}


def value_field(scale, seed):
    out = np.zeros((H, W))
    for y in range(H):
        for x in range(W):
            fx, fy = x / scale, y / scale
            ix, iy = int(math.floor(fx)), int(math.floor(fy))
            tx, ty = fx - ix, fy - iy
            tx = tx * tx * (3 - 2 * tx)
            ty = ty * ty * (3 - 2 * ty)
            a_ = hsh(ix, iy, seed)
            b_ = hsh(ix + 1, iy, seed)
            c_ = hsh(ix, iy + 1, seed)
            d_ = hsh(ix + 1, iy + 1, seed)
            out[y, x] = (a_ * (1 - tx) + b_ * tx) * (1 - ty) + (c_ * (1 - tx) + d_ * tx) * ty
    return out


def bm_stolen_lantern(L, a):
    cx = 25.5
    glow(a, cx, 41, 16, ['#14221a', '#18301e', '#1c3e22'])
    # broken chain at the top
    for (x, y, vert) in ((25.5, 14.5, True), (25.5, 18.5, False)):
        m = (RING(x, y, 0.8, 2.0, 1.4, 2.6) if vert else (E(x, y, 2.4, 1.6) & ~E(x, y, 1.2, 0.5)))
        L.put(m, IRB[3])
        L.put(m & ~nb(m, 0, -1), IRB[4])
    L.put(pts_mask([(27, 12), (28, 11)]), IRB[4])
    handle = ARC(cx, 27.0, 7.5, 180, 360, 1.4)
    L.put(handle, IRB[3])
    cap = P([(17.0, 30.0), (34.0, 30.0), (31.0, 25.0), (20.0, 25.0)])
    L.shade(cap, SLB, f_cyl(cx, 9.0), lo=1, hi=3)
    L.put(R(23, 21, 28, 24), SLB[2])
    globe = E(cx, 40.0, 9.0, 9.5)
    L.shade(globe, ['#122218', '#1c3824', '#2c5432', '#4a7c46', '#86b070'], f_rad(cx, 41.0, 9.0, 9.5), lo=1, hi=4, dith=0.8)
    fl = P([(25.5, 34.5), (27.3, 38.5), (26.8, 41.5), (25.5, 42.5), (24.2, 41.5), (23.7, 38.5)])
    L.put(fl, TOX[5])
    L.put(fl & (PY > 40.5), TOX[3])
    for x in (19, 25, 32):
        L.put(R(x, 31, x, 49) & globe, IRB[2])
    L.put(ARC(cx, 40.0, 7.0, 200, 245, 1.2) & globe, '#c8f0c0')
    base = P([(16.0, 49.0), (35.0, 49.0), (36.0, 56.0), (15.0, 56.0)])
    L.shade(base, SLB, f_cyl(cx, 10.0), lo=1, hi=3)
    L.put(R(15, 52, 36, 52), SLB[1])
    # a price tag hanging off the handle (red string)
    L.put(SEG(32, 24, 38, 31), BLD[3])
    tag = P([(36.0, 31.0), (41.0, 30.0), (43.0, 37.0), (38.0, 38.0)])
    L.shade(tag, PAP, 0.8, lo=2, hi=3)
    L.put(pts_mask([(38, 32)]), '#120808')
    L.put(SEG(39, 34, 41, 34) | SEG(39, 36, 41, 35), BLD[3])
    return {}


def bm_marked_cards(L, a):
    cards = [(-24.0, 13.0, 30.0), (-8.0, 22.5, 27.5), (8.0, 31.5, 27.5), (24.0, 38.0, 30.0)]
    for i, (ang, x, y) in enumerate(cards):
        t = math.radians(ang)
        w_, h_ = 7.5, 12.0
        cxp, cyp = x, y + 10
        pts = []
        for (dx, dy) in ((-w_, -h_), (w_, -h_), (w_, h_), (-w_, h_)):
            pts.append((cxp + dx * math.cos(t) - dy * math.sin(t), cyp + dx * math.sin(t) + dy * math.cos(t)))
        m = P(pts)
        if i < 3:
            L.put(m, BLD[2])
            inner = P([((p[0] - cxp) * 0.78 + cxp, (p[1] - cyp) * 0.84 + cyp) for p in pts])
            L.put(inner, BLD[1])
            L.put(inner & (((XX + YY) % 4) == 0), BLD[3])
            L.put(border(m), BONE[3])
        else:
            L.put(m, BONE[4])
            L.put(border(m), BONE[2])
            spade =(C(cxp - 2.0, cyp + 0.5, 2.6) | C(cxp + 2.6, cyp + 1.5, 2.6)
                     | P([(cxp - 4.4, cyp + 0.0), (cxp + 4.8, cyp + 1.6), (cxp - 0.6, cyp - 6.0)]))
            L.put(spade & m, '#14101a')
            L.put(P([(cxp, cyp + 2.0), (cxp - 1.5, cyp + 7.0), (cxp + 2.5, cyp + 7.4)]) & m, '#14101a')
    # the hidden mark: a tiny bent corner with a green glint on card 2
    L.put(pts_mask([(33, 22), (34, 22), (34, 23)]), TOX[4])
    L.put(pts_mask([(34, 21)]), TOX[5])
    # magnifier glass
    lens_ = C(36.0, 52.0, 5.5)
    L.put(RING(36.0, 52.0, 4.2, 5.6), BRS[3])
    L.put(C(36.0, 52.0, 4.2), '#2a3a3a')
    L.put(ARC(36.0, 52.0, 2.6, 200, 250, 1.0), '#a0d0c8')
    L.put(TH(40.0, 56.5, 44.0, 63.0, 2.4), LTH[3])
    return {}


def bm_hot_dice(L, a):
    glow(a, 25.5, 38, 18, ['#2a1410', '#381a10', '#4a2010'])
    flames = np.zeros((H, W), bool)
    for (x, y, h, w, ln) in ((14.5, 33.0, 11.0, 3.4, -2.0), (20.5, 26.0, 13.0, 3.6, -1.0),
                             (27.5, 24.0, 15.0, 4.0, 1.5), (34.5, 29.0, 12.0, 3.4, 2.0),
                             (39.5, 38.0, 9.0, 2.8, 2.5), (10.5, 43.0, 8.0, 2.6, -2.5)):
        flames |= flame(x, y, h, w, ln)
    L.put(flames, FLM[1])
    L.put(flames & erode(flames, True), FLM[2])
    L.put(erode(erode(flames, True), True), FLM[3])
    L.put(erode(erode(erode(flames, True), True)), FLM[4])
    m, _ = draw_die(L, 25.5, 26.0, 13.0, 14.0, BLD, BLD, BLD, ['#f0e0d0', '#ffffff', '#ffffff'], pips=(6, 4, 5),
                    lev=(4, 3, 2))
    L.put(pts_mask([(14, 46), (13, 45), (37, 46)]), FLM[3])
    for (x, y) in ((19, 16), (33, 14), (40, 23)):
        L.put(pts_mask([(x, y)]), FLM[4])
    return {}


def bm_ghost_hand(L, a):
    fingers = [((19.5, 37.0), (17.5, 22.0), 4.4), ((24.8, 36.0), (25.0, 19.0), 4.6),
               ((30.0, 37.0), (32.0, 22.0), 4.4), ((34.5, 40.0), (38.0, 29.0), 3.8)]
    palm = P([(15.0, 37.0), (37.0, 37.0), (38.0, 46.0), (34.0, 52.0), (17.0, 52.0), (14.5, 45.0)])
    thumb = TH(17.0, 45.0, 9.5, 35.0, 4.6)
    hand = palm | thumb
    for (p0, p1, w) in fingers:
        hand |= TH(p0[0], p0[1], p1[0], p1[1], w)
    wrist = P([(18.0, 51.0), (33.0, 51.0), (35.0, 58.0), (31.0, 63.0), (27.0, 59.0), (23.0, 65.0), (19.0, 59.0), (15.0, 62.0), (16.0, 56.0)])
    f = f_sphere(25.5, 38.0, 16.0, 22.0, amb=0.35)
    L.shade(hand, GHO, f, lo=1, hi=4, dith=0.8)
    for (p0, p1, w) in fingers:
        mm = TH(p0[0], p0[1], p1[0], p1[1], w)
        L.put(mm & ~nb(mm, 1, 0) & hand, GHO[1])
    fade = wrist & ~hand
    L.shade(fade, GHO, 0.8 - f_lin(0, 51, 0, 65), lo=0, hi=3, dith=1.0)
    # translucency: let the background through in a checker on the lower part
    holes = fade & (((XX + YY) % 2) == 0) & (PY > 56)
    L.erase(holes)
    L.put(C(25.5, 45.0, 1.0) | C(21.0, 44.0, 0.8), GHO[4])
    return {'glow': (25.5, 40.0, 19.0), 'glowcol': ['#121e1e', '#14282a']}


def bm_mirror_trick(L, a):
    cx, cy = 25.5, 38.0
    fr = R(11, 17, 40, 61)
    L.shade(fr, RUST, f_cyl(cx, 16.0), lo=1, hi=4)
    L.put(border(fr), RUST[1])
    for (x, y) in ((12, 18), (38, 18), (12, 59), (38, 59)):
        L.put(R(x, y, x + 1, y + 1), BRS[4])
    glass = R(15, 21, 36, 57)
    L.shade(glass, ['#141a24', '#1e2836', '#2c3a4c', '#405268', '#5e7488'], 1 - f_lin(15, 21, 36, 57), dith=1.0)
    # reflection of a red glint / eye
    # cracks from an impact point
    ix, iy = 29.0, 31.0
    cracks = np.zeros((H, W), bool)
    for (ex, ey) in ((15, 22), (36, 24), (16, 45), (30, 57), (36, 50), (22, 21), (15, 34)):
        mx, my = (ix + ex) / 2 + (ey - iy) * 0.12, (iy + ey) / 2 - (ex - ix) * 0.12
        cracks |= POLYL([(ix, iy), (mx, my), (ex, ey)])
    ring = POLYL([(26, 28), (31, 27), (33, 31), (31, 35), (26, 34), (25, 31)], closed=True)
    L.put((cracks | ring) & glass, '#b8d0e0')
    L.put(C(ix + 0.5, iy + 0.5, 1.4), '#e8f8ff')
    L.put(pts_mask([(20, 26), (21, 25)]) & glass, '#8aa4bc')
    # a red reflection (eye) in one shard
    L.put(R(19, 41, 21, 41), BLD[4])
    L.put(pts_mask([(20, 41)]), '#ffd0c0')
    # shards on the floor
    for pts in (((14, 64), (18, 62), (19, 65)), ((33, 63), (37, 61), (36, 65))):
        L.put(P(list(pts)), '#5e7488')
    return {}


def bm_shadow_ledger(L, a):
    pages = P([(15.0, 21.0), (39.0, 18.0), (41.0, 56.0), (17.0, 60.0)])
    L.put(pages, BONE[3])
    for y in range(20, 58, 2):
        L.put(SEG(36, y, 40, y - 0.4) & pages, BONE[1])
    cover = P([(10.0, 20.0), (35.0, 17.0), (37.0, 56.0), (12.0, 60.0)])
    L.shade(cover, ['#08070a', '#121016', '#1c1a22', '#2a2632', '#3c3846'], 1 - f_lin(10, 20, 37, 60), lo=1, hi=3, dith=0.6)
    L.put(border(cover) & ~nb(cover, -1, 0), '#4a4456')
    L.put(SEG(12, 21, 14, 59), '#2a2632')
    # metal corners
    for pts in (((10, 20), (16, 19.3), (10.5, 26)), ((35, 17), (35.5, 23), (29.5, 17.7)),
                ((12, 60), (11.6, 54), (18, 59.3)), ((37, 56), (31, 56.8), (36.6, 50))):
        L.bevel(P(list(pts)), BRS, 3, up=1, dn=1)
    # strap + padlock
    strap = P([(30.0, 35.0), (41.0, 34.0), (41.5, 40.0), (30.5, 41.0)])
    L.shade(strap, LTH, 1 - f_lin(0, 34, 0, 41), lo=2, hi=4)
    shackle = ARC(36.5, 41.0, 3.2, 180, 360, 1.5)
    L.put(shackle, SLB[4])
    lock = R(32, 41, 41, 49)
    L.shade(lock, BRS, f_cyl(36.5, 5.0), lo=1, hi=5)
    L.put(R(36, 43, 37, 45), '#0a0806')
    L.put(R(36, 46, 37, 46), BRS[2])
    # emblem: small red skull
    sk = ascii_mask(['.###.', '#####', '#.#.#', '.###.', '.#.#.'], 18, 30)
    L.put(sk, BLD[3])
    L.put(sk & ~nb(sk, 0, -1), BLD[4])
    # red bookmark ribbon
    rib = P([(24.0, 58.0), (27.0, 57.6), (27.2, 65.0), (25.6, 63.4), (24.2, 65.2)])
    L.put(rib, BLD[3])
    L.put(rib & (PX > 26), BLD[2])
    return {}


HONEY = ['#5a2a06', '#9a5410', '#d88a1c', '#f8b834', '#ffe27a']


def bm_silver_tongue(L, a):
    # ornate silver spoon (bowl up-left) with honey dripping from it: honeyed words
    bx, by = 19.5, 25.0
    u, v = uv(36.0, 60.0, bx, by)
    handle = (u > 0.0) & (u < 0.8) & (np.abs(v) <= 1.2 + 1.3 * np.clip(1 - u / 0.22, 0, 1))
    knob = E(36.5, 60.5, 3.2, 3.4)
    L.shade(handle | knob, SLB, f_cyl(28.0, 7.0, 0.3), lo=1, hi=5)
    L.put(handle & (np.abs(v) < 0.5) & (u > 0.25) & (u < 0.7), SLB[2])
    bowl = E(bx, by, 7.0, 9.0)
    L.shade(bowl, SLB, f_sphere(bx - 2, by - 3, 9.0, 11.0, amb=0.3), lo=1, hi=5, dith=0.5)
    # honey filling the bowl and running over the lip
    hon = E(bx + 0.5, by + 1.5, 5.0, 6.2)
    L.shade(hon, HONEY, f_sphere(bx - 1, by - 1, 6.0, 7.0, amb=0.35), lo=1, hi=4)
    L.put(pts_mask([(17, 22), (18, 21)]), HONEY[4])
    drip = THP(bez((bx - 2.0, by + 7.0), (bx - 5.5, by + 12.0), (bx - 3.5, by + 17.0), n=10), 2.2)
    bulb = C(bx - 3.5, by + 18.5, 2.3)
    L.put(drip | bulb, HONEY[3])
    L.put((drip | bulb) & ~nb(drip | bulb, 1, 0), HONEY[2])
    L.put(pts_mask([(int(bx - 5), int(by + 17))]), HONEY[4])
    gem = C(36.5, 60.5, 1.6)
    L.put(gem, BLD[3])
    L.put(pts_mask([(35, 59)]), BLD[5])
    L.put(ARC(bx, by, 6.0, 195, 250, 1.2, ry=8.0) & bowl, SLB[5])
    return {}


def bm_crooked_scale(L, a):
    cx = 25.5
    base = P([(17.0, 58.0), (34.0, 58.0), (36.0, 62.0), (15.0, 62.0)])
    L.shade(base, BRS, f_cyl(cx, 10.0), lo=1, hi=4)
    post = R(24, 22, 27, 58)
    L.shade(post, BRS, f_cyl(cx, 2.0), lo=1, hi=4)
    L.shade(C(cx, 20.0, 2.2), BRS, f_sphere(cx, 19.5, 2.2), lo=1, hi=5)
    # tilted beam (left side down)
    bx0, by0, bx1, by1 = 8.0, 31.0, 43.0, 20.0
    beam = TH(bx0, by0, bx1, by1, 2.2)
    L.shade(beam, BRS, 1 - f_lin(0, 18, 0, 33), lo=2, hi=5)
    L.shade(C(cx, 25.5, 2.0), RUST, f_sphere(cx, 25.0, 2.0), lo=2, hi=5)
    # chains + pans
    for (px_, py_, drop) in ((9.0, 31.0, 18.0), (42.0, 20.5, 11.0)):
        pan_y = py_ + drop
        ch = SEG(px_, py_ + 1, px_ - 5, pan_y) | SEG(px_, py_ + 1, px_ + 5, pan_y)
        L.put(ch, IRB[4])
        pan = E(px_, pan_y + 1.0, 6.5, 2.4) & (PY > pan_y)
        L.shade(pan, BRS, f_cyl(px_, 6.5), lo=1, hi=4)
        L.put(R(int(px_) - 6, int(pan_y), int(px_) + 6, int(pan_y)), BRS[4])
    # heavy pan: coins, light pan: one feather-light coin
    for (x, y) in ((6.5, 47.0), (10.5, 46.5), (8.5, 45.0)):
        L.shade(E(x, y, 2.4, 1.4), BRS, f_sphere(x, y - 0.4, 2.4, 1.6), lo=2, hi=5)
    L.put(R(40, 30, 43, 30), BLD[3])
    L.put(R(41, 29, 42, 29), BLD[4])
    # crooked: a red weight hidden under the left pan
    hid = R(6, 50, 11, 52)
    L.put(hid, BLD[3])
    L.put(R(6, 50, 11, 50), BLD[4])
    return {}


def bm_smoke_lamp(L, a):
    # smoke first (behind)
    smoke = np.zeros((H, W), bool)
    for (r_, ox, oy) in ((3.2, 37.0, 33.0), (3.8, 34.0, 26.5), (3.4, 38.5, 20.5), (2.8, 34.5, 15.5)):
        smoke |= C(ox, oy, r_) & ~C(ox + 1.6, oy + 1.2, r_ - 1.4)
    smoke |= THP(bez((40.5, 41.0), (42.0, 37.0), (38.0, 35.0), n=8), 1.6)
    L.shade(smoke, SMK, f_rad(36.0, 22.0, 18.0), lo=1, hi=4, dith=0.8)
    body = E(23.0, 47.0, 12.0, 6.5)
    spout = P([(33.0, 44.0), (40.0, 41.0), (43.0, 40.0), (42.0, 42.5), (35.0, 50.0)])
    lid = E(22.5, 40.0, 6.0, 2.6) | P([(20.0, 37.0), (25.0, 37.0), (23.5, 33.5), (21.5, 33.5)])
    handle = ARC(10.5, 46.0, 4.6, 90, 270, 1.8)
    foot = E(23.0, 56.0, 7.0, 2.0) | R(19, 52, 27, 55)
    L.put(handle, BRS[2])
    L.shade(foot, BRS, f_cyl(23.0, 7.0), lo=1, hi=3)
    L.shade(body | spout, BRS, f_sphere(20.0, 43.0, 15.0, 9.0, amb=0.25), lo=1, hi=5, dith=0.6)
    L.shade(lid, BRS, f_sphere(21.5, 38.0, 6.0, 4.0), lo=1, hi=5)
    L.put(C(22.5, 33.0, 1.2), BRS[4])
    L.put(R(13, 48, 33, 48) & body, BRS[2])
    for x in (16, 23, 30):
        L.put(pts_mask([(x, 46)]) & body, BLD[3])
    # tarnish
    for (x, y) in ((18, 50), (27, 44), (31, 49)):
        L.put(pts_mask([(x, y)]), TOX[1])
    # tiny green flame at the spout
    fl = P([(42.0, 40.0), (44.0, 40.0), (43.0, 36.0)])
    L.put(fl, TOX[4])
    return {}


def bm_grave_dust(L, a):
    cx = 25.5
    jar = R(13, 27, 38, 59) | E(cx, 59.0, 12.5, 2.5)
    L.put(jar, '#1c2226')
    dust = (R(14, 38, 37, 58) | E(cx, 58.5, 11.5, 2.0)) & jar
    L.shade(dust, SMK, value_field(3.0, 21) * 0.6 + 0.2, lo=1, hi=3, dith=1.0)
    L.put(E(cx, 38.0, 11.5, 1.6) & jar, SMK[3])
    L.put(border(jar), '#3a4448')
    L.put(SEG(15, 29, 15, 56), '#8aa0a8')
    L.put(SEG(16, 30, 16, 36), '#5a6c74')
    neck = R(15, 22, 36, 27)
    L.shade(neck, ['#1c2226', '#2a3236', '#3a4448', '#56666c', '#7a8c92'], f_cyl(cx, 11.0), lo=1, hi=3)
    cork = R(16, 15, 35, 22)
    L.bevel(cork, SACK, 3, up=1, dn=2)
    L.put(cork & (((XX * 3 + YY * 5) % 7) == 0), SACK[2])
    L.put(R(14, 21, 37, 22), BLD[2])
    L.put(R(14, 21, 37, 21), BLD[3])
    # label with skull
    label = R(17, 41, 34, 55)
    L.shade(label, PAP, 0.85 - 0.4 * f_lin(17, 41, 34, 55), lo=2, hi=4)
    L.put(border(label), PAP[1])
    sk = ascii_mask(['.#####.', '#######', '#..#..#', '#######', '.##.##.', '.#.#.#.'], 22, 44)
    L.put(sk, '#1a1214')
    L.put(SEG(20, 52, 31, 52), '#1a1214')
    return {}


def bm_voodoo_doll(L, a):
    cx = 25.5
    head = C(cx, 26.0, 8.5)
    body = P([(19.0, 32.0), (32.0, 32.0), (34.0, 50.0), (17.0, 50.0)])
    arms = TH(19.0, 37.0, 9.0, 44.0, 6.0) | TH(32.0, 37.0, 42.0, 44.0, 6.0)
    legs = TH(21.5, 48.0, 17.0, 61.0, 6.4) | TH(29.5, 48.0, 34.0, 61.0, 6.4)
    doll = head | body | arms | legs
    L.shade(doll, SACK, f_sphere(cx - 2, 34.0, 18.0, 26.0, amb=0.35), lo=1, hi=4, dith=0.6)
    L.put(doll & (((XX + YY * 3) % 5) == 0), SACK[2])
    # stitched seams
    seam = (SEG(cx, 18, cx, 34) | SEG(cx, 34, cx, 47)) & doll & ((YY % 2) == 0)
    L.put(seam, SACK[0])
    # button eye + X eye
    L.put(C(21.5, 25.0, 2.3), '#1a1418')
    L.put(pts_mask([(21, 24), (22, 25)]), '#4a3a44')
    L.put(pts_mask([(28, 23), (30, 23), (29, 24), (28, 25), (30, 25)]), '#1a1418')
    # stitched mouth
    L.put(R(21, 30, 30, 30), '#1a1418')
    for x in (22, 25, 28):
        L.put(R(x, 29, x, 31), '#1a1418')
    # red heart patch
    heart = C(27.0, 39.0, 1.8) | C(30.0, 39.0, 1.8) | P([(25.0, 39.5), (32.0, 39.5), (28.5, 43.5)])
    L.put(heart, BLD[3])
    L.put(heart & ~nb(heart, 0, -1), BLD[4])
    # pins with coloured heads
    for (x0, y0, x1, y1, col) in ((28.5, 40.0, 37.0, 30.0, BLD[4]), (21.0, 26.0, 13.0, 16.0, TOX[4]),
                                  (22.0, 44.0, 12.0, 52.0, BONE[4]), (31.0, 22.0, 38.0, 15.0, BLD[4])):
        L.put(SEG(x0, y0, x1, y1), SLB[4])
        L.put(C(x1 + 0.5, y1 + 0.5, 1.6), col)
    return {}


def bm_smugglers_map(L, a):
    mp = P([(8.0, 22.0), (14.0, 20.0), (22.0, 23.0), (30.0, 20.0), (38.0, 22.0), (43.0, 21.0), (42.0, 40.0),
            (44.0, 58.0), (36.0, 60.0), (28.0, 57.0), (18.0, 61.0), (9.0, 58.0), (10.0, 40.0)])
    L.shade(mp, PAP, 0.8 - 0.5 * value_field(6.0, 5), lo=1, hi=4, dith=0.8)
    # land masses
    land = (E(17.0, 33.0, 6.0, 5.0) | E(21.0, 37.0, 4.0, 3.5) | E(33.0, 47.0, 6.5, 5.5) | E(36.5, 43.0, 3.0, 3.0))
    L.put(land & mp, '#7a6a48')
    L.put(border(land) & mp, '#4a3e2a')
    # dotted route
    route = bez((14.0, 30.0), (26.0, 30.0), (22.0, 50.0), (33.0, 46.0), n=24)
    for i, (x, y) in enumerate(route):
        if i % 3 == 0:
            L.put(pts_mask([(int(x), int(y))]) & mp, BLD[3])
    # big red X
    xm = TH(30.0, 43.0, 36.0, 49.0, 1.8) | TH(36.0, 43.0, 30.0, 49.0, 1.8)
    L.put(xm, BLD[3])
    L.put(xm & ~nb(xm, 0, -1), BLD[4])
    # sea waves
    for (x0, y0) in ((12, 50), (17, 54), (12, 57), (34, 27)):
        L.put(pts_mask([(x0, y0 + 1), (x0 + 1, y0), (x0 + 2, y0 + 1), (x0 + 3, y0)]) & mp, '#5a6a6a')
    # torn corner & burn marks
    L.put(border(mp) & (value_field(2.0, 9) > 0.6), PAP[1])
    return {}


def bm_poisoned_ring(L, a):
    cx, cy = 25.5, 44.0
    band_o = E(cx, cy, 14.0, 10.5)
    band_i = E(cx, cy + 0.8, 10.4, 7.2)
    ring = band_o & ~band_i
    L.shade(ring, BRS, f_sphere(cx - 3, cy - 5, 16.0, 13.0, amb=0.3), lo=1, hi=5, dith=0.4)
    L.put(border(band_i) & ring & (PY < cy + 1), BRS[1])
    L.put(ring & ~nb(ring, 0, 1) & (PY > cy), BRS[2])
    # setting (poison compartment) + big green gem
    setting = E(cx, 31.5, 8.5, 6.5)
    L.shade(setting, BRS, f_sphere(cx - 1, 29.5, 8.5, 6.5), lo=1, hi=5)
    for k in range(6):
        t = math.radians(k * 60 + 30)
        L.put(C(cx + 7.6 * math.cos(t), 31.5 + 5.6 * math.sin(t), 1.2), BRS[4])
    gem = E(cx, 31.0, 5.8, 4.6)
    L.shade(gem, TOX, f_sphere(cx - 1.5, 29.5, 6.0, 5.0, amb=0.3), lo=1, hi=5)
    L.put(gem & ~nb(gem, 1, 1), TOX[1])
    L.put(pts_mask([(22, 28), (23, 28), (22, 29)]), TOX[5])
    # the poison drop leaking out
    L.put(SEG(25, 36, 25, 39), TOX[3])
    drop = C(25.5, 60.0, 2.6) | P([(23.2, 59.5), (27.8, 59.5), (25.5, 54.0)])
    L.shade(drop, TOX, f_sphere(25.0, 59.0, 2.8), lo=2, hi=5)
    L.put(pts_mask([(24, 58)]), TOX[5])
    return {'glow': (25.5, 38.0, 18.0), 'glowcol': ['#121e12', '#162814']}


PHC = ['#1a2e34', '#2e4a52', '#4a7078', '#74a2a6', '#a8d4d0', '#e0fff8']


def bm_phantom_coin(L, a):
    cx, cy = 24.0, 39.0
    coin = C(cx, cy, 13.0)
    L.shade(coin, PHC, f_sphere(cx - 2, cy - 2, 18.0, amb=0.45), lo=2, hi=4)
    rim = RING(cx, cy, 10.6, 13.0)
    L.put(rim, PHC[4])
    L.put(rim & ((PX - cx) + (PY - cy) > 3), PHC[3])
    L.put(border(C(cx, cy, 10.6)) & ~nb(C(cx, cy, 10.6), -1, -1), PHC[1])
    L.put(C(cx, cy, 10.6), PHC[2])
    L.put(C(cx, cy, 10.6) & ((PX - cx) + (PY - cy) < -9), PHC[3])
    sk = ascii_mask(SKULL9, int(cx) - 4, int(cy) - 5)
    L.put(sk, PHC[4])
    L.put(sk & ~nb(sk, -1, -1), PHC[5])
    L.put(sk & ~nb(sk, 1, 1), PHC[3])
    L.put(dilate(sk) & ~sk & C(cx, cy, 10.6) & ~nb(sk, -1, -1), PHC[1])
    # fading: the right part dissolves into drifting pixels
    t = np.clip((PX - (cx + 4.0)) / 10.0, 0, 1)
    gone = coin & (BAYER < t * 1.25) & (PX > cx + 4)
    L.erase(gone)
    for (x, y, k) in ((39, 31, 3), (41, 36, 2), (40, 42, 3), (43, 46, 2), (42, 27, 2), (44, 39, 2), (38, 48, 3),
                      (45, 33, 1)):
        a[y, x] = hexc(PHC[k + 1])
    return {'glow': (25.5, 39.0, 18.0), 'glowcol': ['#121c1e', '#142426']}


def bm_underworld_pass(L, a):
    # tilted ticket
    t = math.radians(-12)
    cxp, cyp = 25.5, 40.0
    w_, h_ = 13.5, 20.0
    pts = []
    for (dx, dy) in ((-w_, -h_), (w_, -h_), (w_, h_), (-w_, h_)):
        pts.append((cxp + dx * math.cos(t) - dy * math.sin(t), cyp + dx * math.sin(t) + dy * math.cos(t)))
    tk = P(pts)
    # notched corners (half circles on the sides)
    for (dx, dy) in ((-w_, 6.0), (w_, 6.0)):
        x = cxp + dx * math.cos(t) - dy * math.sin(t)
        y = cyp + dx * math.sin(t) + dy * math.cos(t)
        tk &= ~C(x, y, 2.4)
    L.shade(tk, ['#2a0a0e', '#4a1016', '#6e1a20', '#92282a', '#b44034'], 0.8 - 0.5 * f_lin(10, 20, 40, 60), lo=1, hi=4, dith=0.6)
    # perforation line
    for k in range(-12, 13, 2):
        dx, dy = k, 6.0
        x = cxp + dx * math.cos(t) - dy * math.sin(t)
        y = cyp + dx * math.sin(t) + dy * math.cos(t)
        L.put(pts_mask([(int(x), int(y))]) & tk, '#1a0408')
    inner = P([(cxp + (p[0] - cxp) * 0.8, cyp + (p[1] - cyp) * 0.86) for p in pts])
    L.put(border(inner) & tk & ~R(0, 0, 50, 0), BONE[2])
    sk = ascii_mask(SKULL9, 21, 28)
    L.put(sk, BONE[4])
    L.put(sk & ~nb(sk, 1, 1), BONE[2])
    L.put(SEG(17, 52, 33, 48) & tk, BONE[3])
    return {}


def bm_devils_deal(L, a):
    paper = P([(10.0, 19.0), (38.0, 17.0), (41.0, 60.0), (13.0, 63.0)])
    L.shade(paper, PAP, 0.85 - 0.5 * f_lin(10, 19, 41, 63), lo=1, hi=4, dith=0.6)
    for i, y in enumerate(range(24, 44, 3)):
        x1 = 33 if i % 3 != 2 else 26
        L.put(SEG(14, y + 1, x1, y - 0.4) & ((XX % 6) != 5) & paper, PAP[1])
    # signature in blood
    sig = POLYL([(14, 52), (16, 48), (17, 52), (19, 49), (20, 53), (23, 50), (26, 51)])
    L.put(sig, BLD[3])
    L.put(SEG(14, 54, 27, 53), PAP[1])
    # horned wax seal (devil head)
    sx, sy = 30.5, 53.0
    horns = (P([(26.5, 50.0), (23.0, 42.0), (25.0, 43.0), (29.5, 48.0)])
             | P([(34.5, 50.0), (38.0, 42.0), (36.0, 43.0), (31.5, 48.0)]))
    L.put(horns, BLD[3])
    L.put(horns & ~nb(horns, 1, 0), BLD[1])
    L.put(horns & ~nb(horns, -1, 0), BLD[4])
    blob = C(sx, sy, 5.4) | C(26.0, 57.0, 1.4)
    L.put(blob, WAX[3])
    L.put(blob & ~nb(blob, 1, 1), WAX[2])
    L.put(blob & ~nb(blob, -1, -1), WAX[4])
    face = ascii_mask(['#...#', '##.##', '.....', '#...#', '.###.'], 28, 51)
    L.put(face, WAX[1])
    L.put(face & ~nb(face, 0, 1), WAX[0])
    # quill
    q = TH(40.5, 20.0, 34.0, 44.0, 2.2)
    L.put(q, '#1c1a20')
    L.put(TH(41.5, 18.0, 38.0, 30.0, 3.6), '#2a2632')
    L.put(SEG(34, 44, 33, 47), BLD[4])
    return {}


def bm_skeleton_key(L, a):
    cx = 25.5
    skull = C(cx, 23.0, 7.5) | R(20, 25, 31, 31)
    L.shade(skull, BONE, f_sphere(cx - 1.5, 21.0, 8.0, 9.0, amb=0.3), lo=1, hi=4, dith=0.5)
    for x in (22.0, 29.0):
        L.put(C(x, 24.0, 2.0), '#0a0806')
        L.put(C(x, 24.0, 0.8), BLD[4])
    L.put(P([(24.5, 28.5), (26.5, 28.5), (25.5, 26.5)]), '#0a0806')
    for x in (21, 23, 25, 27, 29):
        L.put(R(x, 31, x, 32), BONE[1])
    L.put(R(21, 30, 30, 30), BONE[2])
    shaft = R(24, 32, 27, 60)
    L.shade(shaft, IRB, f_cyl(cx, 2.0), lo=2, hi=5)
    for y in (35, 39):
        L.shade(E(cx, y + 0.5, 3.8, 1.4), IRB, f_cyl(cx, 3.8), lo=2, hi=5)
    bit = R(28, 51, 33, 59) & ~R(31, 51, 33, 52) & ~R(30, 55, 33, 56)
    L.bevel(bit, IRB, 3, up=1, dn=2)
    return {}


# =====================================================================================  assembly
INNER = rings(SHAPE, 5)[1]


def build_fortune(num, fn):
    a = fortune_background()
    L = Layer()
    probe = Layer()
    opts = fn(probe, a.copy()) or {}
    halo = opts.get('halo', (25.5, 40.0, 17.5))
    if halo:
        halo_fortune(a, *halo)
    fn(L, a)
    L.outline(FO)
    comp(a, L, INNER)
    free = ~dilate(dilate(L.mask(), True), True)
    if halo:
        hx, hy, hr = halo
        free &= ~(C(hx, hy, hr + 2.5) & ~C(hx, hy, hr - 2.5))
    place_stars(a, free, seed=num * 13 + 5, n_small=opts.get('stars', 8), n_spark=opts.get('sparks', 3))
    fortune_frame(a, num)
    return a


def rim_light(L, col, t=0.45):
    """tint the right-hand silhouette edge of the motif (lit by a red lamp from the right)."""
    m = L.mask()
    edge = m & ~nb(m, 1, 0)
    edge2 = m & nb(m, 1, 0) & ~nb(m, 2, 0) & ~edge
    for e, tt in ((edge, t), (edge2, t * 0.4)):
        ys, xs = np.nonzero(e)
        for y, x in zip(ys, xs):
            L.c[y, x] = mix(tuple(L.c[y, x][:3]), col, tt)


def build_black(num, fn):
    a = black_background()
    L = Layer()
    probe = Layer()
    opts = fn(probe, a.copy()) or {}
    g = opts.get('glow', (25.5, 40.0, 18.0))
    if g:
        glow_black(a, *g, col=opts.get('glowcol'))
    a0 = a.copy()
    fn(L, a)
    untouched = (a == a0).all(axis=2)
    if opts.get('rim', True):
        rim_light(L, RIM, 0.35)
    L.outline(BO)
    comp(a, L, INNER)
    free = ~dilate(dilate(L.mask(), True), True) & erode(untouched, True)
    place_embers(a, free, seed=num * 17 + 3, n=opts.get('embers', 7))
    black_frame(a)
    return a


FORTUNE_IDS = ['crystal_ball', 'candle', 'raven', 'moon_moth', 'open_hand', 'third_eye', 'key', 'hourglass',
               'serpent', 'mask', 'lantern', 'crown', 'chalice', 'coin', 'star', 'comet', 'tower', 'wheel',
               'feather', 'anchor', 'mirror', 'bell', 'lotus', 'dagger', 'cauldron', 'owl', 'sun', 'spider',
               'fox', 'phoenix']
BLACK_IDS = ['loaded_dice', 'counterfeit', 'rigged_shaker', 'smuggled_gumballs', 'forged_diploma', 'pickpocket',
             'insider_tip', 'bribed_croupier', 'cursed_idol', 'weighted_coin', 'black_cat_bone', 'snake_oil',
             'fake_crown', 'stolen_lantern', 'marked_cards', 'hot_dice', 'ghost_hand', 'mirror_trick',
             'shadow_ledger', 'silver_tongue', 'crooked_scale', 'smoke_lamp', 'grave_dust', 'voodoo_doll',
             'smugglers_map', 'poisoned_ring', 'phantom_coin', 'underworld_pass', 'devils_deal', 'skeleton_key']


# =====================================================================================  card backs
SKULL9 = ['..#####..', '.#######.', '#########', '##..#..##', '##..#..##', '#########',
          '.###.###.', '..#####..', '..#.#.#..']


def fortune_back():
    a = np.zeros((H, W, 4), np.uint8)
    a[:] = hexc(BGF[1])
    # quiet diamond lattice
    lat = (((XX + YY) % 8) == 0) | (((XX - YY) % 8) == 0)
    a[lat] = hexc(BGF[2])
    glow(a, 25.5, 39.5, 24, [BGF[2], BGF[3], BGF[4]])
    a[lat & C(25.5, 39.5, 22)] = hexc(BGF[3])
    cx, cy = 25.5, 39.5
    L = Layer()
    # rays
    for k in range(16):
        t = math.radians(k * 22.5)
        r1 = 19.0 if k % 2 == 0 else 16.0
        L.put(TH(cx + 12.5 * math.cos(t), cy + 12.5 * math.sin(t), cx + r1 * math.cos(t), cy + r1 * math.sin(t),
                 1.6 if k % 2 == 0 else 1.1), GOLD[3] if k % 2 == 0 else GOLD[2])
    ring = RING(cx, cy, 9.5, 12.0)
    L.shade(ring, GOLD, f_sphere(cx, cy, 14.0), lo=2, hi=5)
    disc = C(cx, cy, 9.5)
    L.put(disc, '#1a0c2b')
    L.shade(disc, ['#1a0c2b', '#22103a', '#2c1648'], f_rad(cx, cy, 9.5), dith=1.0)
    moon = C(cx - 1.0, cy, 7.0) & ~C(cx + 2.2, cy - 1.6, 6.0)
    L.shade(moon, GOLD, f_sphere(cx - 3, cy - 2, 8.0), lo=3, hi=5)
    st, _ = star_mask(cx + 3.0, cy + 1.0, 3.6, 1.5)
    L.put(st, GOLD[5])
    for (x, y) in ((cx, cy - 25.0), (cx, cy + 25.0)):
        s2, _ = star_mask(x, y, 3.4, 1.4)
        L.put(s2, GOLD[4])
    for (x, y) in ((cx - 13.0, cy - 19.0), (cx + 13.0, cy - 19.0), (cx - 13.0, cy + 19.0), (cx + 13.0, cy + 19.0)):
        L.put(C(x, y, 1.3), GOLD[3])
    L.outline(FO)
    comp(a, L, INNER)
    # frame: gold band, bosses, studs (no numeral, symmetric)
    sh = SHAPE
    rg, inner = rings(sh, 5)
    a[~sh] = 0
    a[rg[0]] = hexc(FO)
    a[rg[1] & SIDE_TL] = hexc(GOLD[5])
    a[rg[1] & ~SIDE_TL] = hexc(GOLD[3])
    a[rg[2]] = hexc(GOLD[4])
    a[rg[2] & ~SIDE_TL] = hexc(GOLD[3])
    a[rg[3] & SIDE_TL] = hexc(GOLD[2])
    a[rg[3] & ~SIDE_TL] = hexc(GOLD[4])
    a[rg[4]] = hexc(FO)
    a[border(R(6, 6, W - 7, H - 7))] = hexc(BGF[5])
    for (bx, by) in ((4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)):
        man = np.abs(PX - bx) + np.abs(PY - by)
        dia = man <= 3.6
        a[dilate(dia) & ~dia & (man <= 5)] = hexc(FO)
        a[dia] = hexc(GOLD[4])
        a[dia & ((PX - bx) + (PY - by) > 1.5)] = hexc(GOLD[3])
        a[dia & ((PX - bx) + (PY - by) < -1.5)] = hexc(GOLD[5])
        a[man <= 1.6] = hexc(GEMV[1])
        a[int(by), int(bx)] = hexc(GEMV[2])
        a[int(by) - 1, int(bx)] = hexc(GEMV[3])
    for (sx, sy) in ((2.5, 39.5), (W - 2.5, 39.5), (25.5, 2.5), (25.5, H - 2.5)):
        horiz = sy in (2.5, H - 2.5)
        if horiz:
            st_ = (np.abs(PY - sy) * 1.6 + np.abs(PX - sx) <= 4.2)
        else:
            st_ = (np.abs(PX - sx) * 1.6 + np.abs(PY - sy) <= 4.2)
        a[dilate(st_) & ~st_ & SHAPE & (np.abs(PX - sx) <= 6) & (np.abs(PY - sy) <= 6)] = hexc(FO)
        a[st_] = hexc(GOLD[4])
        a[st_ & ((PX - sx) + (PY - sy) > 0.5)] = hexc(GOLD[3])
        a[int(sy), int(sx)] = hexc(GEMV[2])
    a[~SHAPE] = 0
    return a


def black_back():
    a = np.zeros((H, W, 4), np.uint8)
    a[:] = hexc(BGB[1])
    hatch = (((XX + YY) % 6) == 0) | (((XX - YY) % 6) == 0)
    a[hatch] = hexc(BGB[2])
    glow_black(a, 25.5, 39.5, 21.0)
    a[hatch & C(25.5, 39.5, 15)] = hexc('#2e1a1c')
    cx, cy = 25.5, 39.5
    L = Layer()
    # crossed bones behind the seal
    for (x0, y0, x1, y1) in ((12.0, 22.0, 39.0, 57.0), (39.0, 22.0, 12.0, 57.0)):
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px_, py_ = -uy, ux
        bone = TH(x0 + ux * 1.5, y0 + uy * 1.5, x1 - ux * 1.5, y1 - uy * 1.5, 3.2)
        knobs = np.zeros((H, W), bool)
        for (ex, ey, sgn) in ((x0, y0, 1), (x1, y1, -1)):
            for side in (-1, 1):
                knobs |= C(ex + px_ * side * 1.9 + ux * sgn * 0.6, ey + py_ * side * 1.9 + uy * sgn * 0.6, 2.1)
        L.shade(bone | knobs, BONE, 1 - f_lin(0, 20, 0, 60) * 0.6, lo=1, hi=4)
        L.put((bone | knobs) & ~nb(bone | knobs, 1, 1), BONE[1])
    L.outline(BO)
    comp(a, L, INNER)
    # big wax seal
    blob = C(cx, cy, 11.0)
    for (ang, dr, rr) in ((110, 10.0, 2.6), (20, 10.5, 2.0), (230, 10.3, 2.2), (320, 10.6, 1.6)):
        t = math.radians(ang)
        blob |= C(cx + dr * math.cos(t), cy + dr * math.sin(t), rr)
    a[dilate(blob, True) & ~blob] = hexc(BO)
    lev = quant(f_sphere(cx - 1, cy - 1, 13.0, amb=0.3), 4) + 1
    for i in range(1, 5):
        a[blob & (lev == i)] = hexc(WAX[i])
    disc = C(cx, cy, 7.6)
    a[disc] = hexc(WAX[2])
    a[disc & ~nb(disc, -1, -1)] = hexc(WAX[1])
    a[disc & ~nb(disc, 1, 1)] = hexc(WAX[4])
    a[border(C(cx, cy, 9.2)) & ~C(cx, cy, 8.4) & ~disc] = hexc(WAX[2])
    sk = ascii_mask(SKULL9, int(cx) - 4, int(cy) - 4)
    holes = R(int(cx) - 4, int(cy) - 4, int(cx) + 4, int(cy) + 4) & ~sk & dilate(sk) & erode(dilate(sk, True), False)
    a[sk] = hexc(WAX[4])
    a[sk & ~nb(sk, 0, -1)] = hexc(WAX[5])
    a[sk & ~nb(sk, 0, 1)] = hexc(WAX[3])
    a[holes & disc] = hexc(WAX[0])
    black_frame(a, seal=False)
    # extra rivets top / bottom centre
    for (x, y) in ((25, 3), (25, H - 4)):
        m = R(x - 1, y - 1, x + 1, y + 1)
        a[m] = hexc(IRON[2])
        a[y - 1, x - 1] = hexc(IRON[4])
        a[y - 1, x] = hexc(IRON[3])
        a[y, x - 1] = hexc(IRON[3])
        a[y + 1, x + 1] = hexc(IRON[1])
    return a


# =====================================================================================  main
def check(a, name):
    assert a.shape == (H, W, 4), name
    al = a[:, :, 3]
    assert set(np.unique(al)) <= {0, 255}, name + ': soft alpha'
    assert (a[al == 0][:, :3] == 0).all(), name + ': dirty transparent pixels'
    assert (al[SHAPE] == 255).all(), name + ': hole inside the card'


def main():
    os.makedirs(OUT_T, exist_ok=True)
    os.makedirs(OUT_B, exist_ok=True)
    sets = []
    for (ids, prefix, build, out, back) in ((FORTUNE_IDS, 'fm_', build_fortune, OUT_T, fortune_back),
                                            (BLACK_IDS, 'bm_', build_black, OUT_B, black_back)):
        items = []
        for i, cid in enumerate(ids):
            a = build(i + 1, globals()[prefix + cid])
            a[~SHAPE] = 0
            check(a, cid)
            Image.fromarray(a, 'RGBA').save(os.path.join(out, cid + '.png'))
            items.append((cid, a))
        b = back()
        check(b, 'back')
        Image.fromarray(b, 'RGBA').save(os.path.join(out, 'back.png'))
        items.append(('back', b))
        sheet(items, scale=3, cols=8, bg=(30, 22, 36, 255) if out == OUT_T else (24, 22, 24, 255)).save(
            os.path.join(out, 'contact_sheet.png'))
        sets.append(items)
        print('ok', out, len(items))
    dev = os.environ.get('TAROT_DEV')
    if dev:
        for k, items in enumerate(sets):
            sheet(items, scale=2, cols=11, label=False).save(dev_path('_grid2x_%d.png' % k))
            sheet(items, scale=1, cols=16, label=False).save(dev_path('_grid1x_%d.png' % k))


if __name__ == '__main__':
    main()
