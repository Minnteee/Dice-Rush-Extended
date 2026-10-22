"""Small numpy pixel-art toolkit for the Dice Shaker scene art (gen_scene.py).

All images are numpy RGBA uint8 arrays (H, W, 4).  Shapes are built as boolean
masks, shaded with a float "level" field and quantised into a short colour ramp
with (optional, mild) ordered dithering - so everything stays hard-pixel art.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0


# ----------------------------------------------------------------- colours
def hexc(s, a=255):
    if isinstance(s, (tuple, list, np.ndarray)):
        s = tuple(int(v) for v in s)
        return s if len(s) == 4 else s + (a,)
    s = s.lstrip('#')
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def mix(c1, c2, t):
    a = np.array(hexc(c1), np.float32)
    b = np.array(hexc(c2), np.float32)
    r = a * (1 - t) + b * t
    return '#%02x%02x%02x' % tuple(int(round(v)) for v in r[:3])


def ramp_arr(stops):
    return np.array([hexc(s)[:3] for s in stops], np.uint8)


def lerp_ramp(stops, n):
    """Resample a list of colour stops to n colours (linear in RGB)."""
    cols = np.array([hexc(s)[:3] for s in stops], np.float32)
    out = []
    for i in range(n):
        x = i / (n - 1) * (len(stops) - 1)
        j = min(int(math.floor(x)), len(stops) - 2)
        f = x - j
        c = cols[j] * (1 - f) + cols[j + 1] * f
        out.append('#%02x%02x%02x' % tuple(int(round(v)) for v in c))
    return out


# ------------------------------------------------------------------ grids
def grid(h, w, ox=0.0, oy=0.0):
    """pixel-centre coordinates (X, Y) of an h x w image whose top-left pixel is at (ox, oy)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return xx + 0.5 + ox, yy + 0.5 + oy


def bayer(h, w, ox=0, oy=0):
    yy, xx = np.mgrid[0:h, 0:w]
    return BAYER4[(yy + int(oy)) % 4, (xx + int(ox)) % 4]


def quantize(level, n, dither=0.5, ox=0, oy=0):
    """level (float 0..1) -> integer ramp index 0..n-1 with ordered dithering of given strength."""
    h, w = level.shape
    x = np.clip(level, 0, 1) * (n - 1)
    b = (bayer(h, w, ox, oy) - 0.5) * dither
    return np.clip(np.floor(x + 0.5 + b), 0, n - 1).astype(np.int32)


# ------------------------------------------------------------------ noise
def _hash(ix, iy, seed):
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + int(seed) * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / float(0x1000000)


def hash01(ix, iy, seed=0):
    return _hash(np.asarray(ix), np.asarray(iy), seed)


def vnoise(X, Y, seed=0):
    """smooth value noise in [0,1] at float coordinates."""
    ix = np.floor(X).astype(np.int64)
    iy = np.floor(Y).astype(np.int64)
    tx = X - ix
    ty = Y - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = _hash(ix, iy, seed)
    b = _hash(ix + 1, iy, seed)
    c = _hash(ix, iy + 1, seed)
    d = _hash(ix + 1, iy + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(X, Y, seed=0, octaves=3):
    v = 0.0
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        v = v + vnoise(X * (2 ** o), Y * (2 ** o), seed + o * 17) * amp
        tot += amp
        amp *= 0.5
    return v / tot


# ------------------------------------------------------------------ masks
def poly_mask(h, w, pts, ox=0.0, oy=0.0):
    img = Image.new('L', (w, h), 0)
    ImageDraw.Draw(img).polygon([(float(x) - ox, float(y) - oy) for x, y in pts], fill=255)
    return np.array(img) > 0


def ellipse_mask(X, Y, cx, cy, rx, ry):
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0


def shift(m, dx, dy, fill=False):
    out = np.full_like(m, fill)
    h, w = m.shape[:2]
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return out


def dilate(m, n=1, diag=False):
    m = m.copy()
    for _ in range(n):
        g = m.copy()
        g[1:, :] |= m[:-1, :]
        g[:-1, :] |= m[1:, :]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        if diag:
            g[1:, 1:] |= m[:-1, :-1]
            g[1:, :-1] |= m[:-1, 1:]
            g[:-1, 1:] |= m[1:, :-1]
            g[:-1, :-1] |= m[1:, 1:]
        m = g
    return m


def erode(m, n=1, diag=False):
    return ~dilate(~m, n, diag)


def edge_out(m, diag=False):
    return dilate(m, 1, diag) & ~m


def edge_in(m, diag=False):
    return m & ~erode(m, 1, diag)


def ellipse_line(h, w, cx, cy, rx, ry, ox=0.0, oy=0.0, part='all'):
    """clean 8-connected 1px ellipse outline (centre/radii in canvas coords, image top-left at ox,oy).
    part: 'all', 'back' (upper half) or 'front' (lower half)."""
    m = np.zeros((h, w), bool)
    # shallow part: one pixel per column
    xs = np.arange(int(math.floor(cx - rx)) - 1, int(math.ceil(cx + rx)) + 2)
    for x in xs:
        u = (x + 0.5 - cx) / rx
        if abs(u) > 1:
            continue
        s = math.sqrt(1 - u * u)
        slope = abs(ry * u / max(s, 1e-6) / rx)
        if slope > 1.0:
            continue
        for sg in (-1, 1):
            if part == 'back' and sg > 0 or part == 'front' and sg < 0:
                continue
            y = cy + sg * ry * s
            yi, xi = int(math.floor(y - oy)), int(x - ox)
            if 0 <= yi < h and 0 <= xi < w:
                m[yi, xi] = True
    # steep part: one pixel per row
    ys = np.arange(int(math.floor(cy - ry)) - 1, int(math.ceil(cy + ry)) + 2)
    for y in ys:
        v = (y + 0.5 - cy) / ry
        if abs(v) > 1:
            continue
        if part == 'back' and v > 0 or part == 'front' and v < 0:
            continue
        s = math.sqrt(1 - v * v)
        slope = abs(rx * v / max(s, 1e-6) / ry)
        if slope >= 1.0:
            continue
        for sg in (-1, 1):
            x = cx + sg * rx * s
            yi, xi = int(y - oy), int(math.floor(x - ox))
            if 0 <= yi < h and 0 <= xi < w:
                m[yi, xi] = True
    return m


def seg_field(X, Y, ax, ay, bx, by):
    """distance to segment a-b, the segment parameter t (0..1) and the signed side coordinate."""
    dx, dy = bx - ax, by - ay
    L2 = max(dx * dx + dy * dy, 1e-6)
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    px = ax + t * dx
    py = ay + t * dy
    d = np.hypot(X - px, Y - py)
    L = math.sqrt(L2)
    side = ((X - ax) * (-dy) + (Y - ay) * dx) / L    # + = left of direction (screen coords)
    return d, t, side


# --------------------------------------------------------------- painting
def paint(img, mask, color):
    img[mask] = hexc(color)


def paint_ramp(img, mask, ramp, idx):
    """paint idx (int array, same shape) from ramp (n,3 uint8) where mask."""
    img[mask, :3] = ramp[np.clip(idx[mask], 0, len(ramp) - 1)]
    img[mask, 3] = 255


def alpha_over(dst, src, x=0, y=0):
    """composite src (RGBA uint8, may be semi transparent) over dst in place at (x,y)."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, W - x), min(h, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return dst
    s = src[sy0:sy1, sx0:sx1].astype(np.float32) / 255.0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1].astype(np.float32) / 255.0
    sa = s[..., 3:4]
    da = d[..., 3:4]
    oa = sa + da * (1 - sa)
    oc = np.where(oa > 0, (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    out = np.concatenate([oc, oa], axis=-1)
    dst[y + sy0:y + sy1, x + sx0:x + sx1] = np.clip(np.round(out * 255), 0, 255).astype(np.uint8)
    return dst


def outline(img, color, diag=False, mask=None):
    """1px outline around opaque pixels of img (in place)."""
    m = img[..., 3] > 0 if mask is None else mask
    e = edge_out(m, diag)
    img[e] = hexc(color)
    return img


def save(a, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def to_img(a, scale=1):
    im = Image.fromarray(a, 'RGBA')
    if scale != 1:
        im = im.resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST)
    return im


def flip_h(a):
    return a[:, ::-1].copy()


# ------------------------------------------------------------ ascii sprites
def sprite(lines, pal):
    """ascii -> RGBA; '.' / ' ' transparent; pal maps chars to colours (hex or rgba tuples)."""
    if isinstance(lines, str):
        lines = [l for l in lines.strip('\n').split('\n')]
    lines = [l.rstrip() for l in lines]
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    lines = [l[ind:] for l in lines]
    w = max(len(l) for l in lines)
    h = len(lines)
    a = np.zeros((h, w, 4), np.uint8)
    for y, l in enumerate(lines):
        for x, ch in enumerate(l):
            if ch in '. ':
                continue
            a[y, x] = hexc(pal[ch])
    return a


def char_map(lines):
    """ascii -> 2D array of chars (for level-shaded stamps)."""
    if isinstance(lines, str):
        lines = [l for l in lines.strip('\n').split('\n')]
    lines = [l.rstrip() for l in lines]
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    lines = [l[ind:] for l in lines]
    w = max(len(l) for l in lines)
    return np.array([list(l.ljust(w, '.')) for l in lines])


def blit(dst, spr, x, y):
    """hard-alpha blit (alpha > 0 copies the pixel)."""
    h, w = spr.shape[:2]
    H, W = dst.shape[:2]
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, W - x), min(h, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = spr[sy0:sy1, sx0:sx1]
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]
    m = sub[..., 3] > 0
    d[m] = sub[m]
