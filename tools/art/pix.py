"""Small pixel-art toolkit used by all Dice Rush Extended art generators.

Everything works on numpy RGBA uint8 arrays (H, W, 4) with hard alpha
(0 or 255) so the results stay crisp when upscaled with NEAREST.
"""
import math
import os
import numpy as np
from PIL import Image
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

OUT_ROOT = os.path.join(REPO, "build", "generated", "bdr", "art")
REF_ROOT = os.path.join(REPO, "work", "recovered", "assets")


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
    c1 = hexc(c1)
    c2 = hexc(c2)
    return tuple(int(round(c1[i] * (1 - t) + c2[i] * t)) for i in range(3)) + (255,)


def darken(c, t):
    return mix(c, (0, 0, 0, 255), t)


def lighten(c, t):
    return mix(c, (255, 255, 255, 255), t)


def lum(c):
    c = hexc(c)
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255.0


def cdist(c1, c2):
    c1 = hexc(c1)
    c2 = hexc(c2)
    return math.sqrt(sum((c1[i] - c2[i]) ** 2 for i in range(3))) / 441.7


def hue_shift_dark(c, t=0.45):
    """Darker, slightly more saturated / cooler shade (nicer than plain black mix)."""
    c = hexc(c)
    r, g, b = c[0] / 255, c[1] / 255, c[2] / 255
    r, g, b = r * (1 - t), g * (1 - t), b * (1 - t * 0.75)
    return (int(r * 255), int(g * 255), int(min(1, b) * 255), 255)


def hash2(x, y, seed=0):
    """Deterministic integer hash -> [0,1)."""
    h = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


def value_noise(x, y, scale, seed=0):
    """Smooth-ish value noise in [0,1]."""
    fx, fy = x / scale, y / scale
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = hash2(ix, iy, seed)
    b = hash2(ix + 1, iy, seed)
    c = hash2(ix, iy + 1, seed)
    d = hash2(ix + 1, iy + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h=None, arr=None):
        if arr is not None:
            self.a = arr
        else:
            self.a = np.zeros((h if h is not None else w, w, 4), np.uint8)

    @property
    def w(self):
        return self.a.shape[1]

    @property
    def h(self):
        return self.a.shape[0]

    def copy(self):
        return Canvas(arr=self.a.copy())

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is None:
                self.a[y, x] = (0, 0, 0, 0)
            else:
                self.a[y, x] = hexc(c)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(int(v) for v in self.a[y, x])
        return (0, 0, 0, 0)

    def opaque(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.a[y, x, 3] > 0

    def rect(self, x0, y0, x1, y1, c):
        """inclusive rectangle fill"""
        x0, x1 = sorted((int(x0), int(x1)))
        y0, y1 = sorted((int(y0), int(y1)))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.w - 1, x1), min(self.h - 1, y1)
        if x1 >= x0 and y1 >= y0:
            self.a[y0:y1 + 1, x0:x1 + 1] = hexc(c) if c is not None else (0, 0, 0, 0)

    def frame(self, x0, y0, x1, y1, c):
        self.hline(x0, x1, y0, c)
        self.hline(x0, x1, y1, c)
        self.vline(x0, y0, y1, c)
        self.vline(x1, y0, y1, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if w == 1:
                self.px(x0, y0, c)
            else:
                r = w // 2
                self.rect(x0 - r, y0 - r, x0 - r + w - 1, y0 - r + w - 1, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c, fill=True):
        """Ellipse centred on (cx,cy) (may be .5) with radii rx, ry (pixel-centre test)."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                dx = (x + 0.5 - cx) / max(rx, 0.01)
                dy = (y + 0.5 - cy) / max(ry, 0.01)
                d = dx * dx + dy * dy
                if fill:
                    if d <= 1.0:
                        self.px(x, y, c)
                else:
                    # ring of ~1px
                    if d <= 1.0:
                        # inner test
                        dx2 = (x + 0.5 - cx) / max(rx - 1, 0.01)
                        dy2 = (y + 0.5 - cy) / max(ry - 1, 0.01)
                        if dx2 * dx2 + dy2 * dy2 > 1.0:
                            self.px(x, y, c)

    def circle(self, cx, cy, r, c, fill=True):
        self.ellipse(cx, cy, r, r, c, fill)

    def poly(self, pts, c):
        """Fill polygon (pixel-centre inclusion, even-odd)."""
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            yc = y + 0.5
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[i] - 0.5))
                xb = int(math.floor(xs[i + 1] - 0.5))
                for x in range(xa, xb + 1):
                    self.px(x, y, c)

    def blit(self, spr, x, y):
        """Composite sprite array (hard alpha) at integer position."""
        if isinstance(spr, Canvas):
            spr = spr.a
        h, w = spr.shape[:2]
        x, y = int(x), int(y)
        sx0, sy0 = max(0, -x), max(0, -y)
        sx1, sy1 = min(w, self.w - x), min(h, self.h - y)
        if sx1 <= sx0 or sy1 <= sy0:
            return
        sub = spr[sy0:sy1, sx0:sx1]
        dst = self.a[y + sy0:y + sy1, x + sx0:x + sx1]
        m = sub[:, :, 3] > 0
        dst[m] = sub[m]

    def outline(self, c, diag=False, only_outside=True):
        self.a = outline_arr(self.a, c, diag)
        return self

    def save(self, path, scale=1):
        save_png(self.a, path, scale)

    def img(self, scale=1):
        return to_img(self.a, scale)


def outline_arr(a, c, diag=False):
    """Add 1px outline around opaque pixels (in place in a copy; no growth)."""
    a = a.copy()
    m = a[:, :, 3] > 0
    grow = np.zeros_like(m)
    grow[1:, :] |= m[:-1, :]
    grow[:-1, :] |= m[1:, :]
    grow[:, 1:] |= m[:, :-1]
    grow[:, :-1] |= m[:, 1:]
    if diag:
        grow[1:, 1:] |= m[:-1, :-1]
        grow[1:, :-1] |= m[:-1, 1:]
        grow[:-1, 1:] |= m[1:, :-1]
        grow[:-1, :-1] |= m[1:, 1:]
    ring = grow & ~m
    a[ring] = hexc(c)
    return a


def pad(a, n=1):
    return np.pad(a, ((n, n), (n, n), (0, 0)))


def crop_to_content(a):
    m = a[:, :, 3] > 0
    if not m.any():
        return a
    ys, xs = np.nonzero(m)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def to_img(a, scale=1):
    im = Image.fromarray(a, 'RGBA')
    if scale != 1:
        im = im.resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST)
    return im


def save_png(a, path, scale=1):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = to_img(a, scale) if not isinstance(a, Image.Image) else a
    im.save(path)


def clean_alpha(a):
    """force hard alpha and zero RGB under transparent pixels"""
    a = a.copy()
    m = a[:, :, 3] >= 128
    a[:, :, 3] = np.where(m, 255, 0)
    a[~m] = 0
    return a


# ------------------------------------------------------------ ascii sprites
BASE_PAL = {
    'K': '#14101c',  # outline black
    'X': '#1b1b1b',
    'W': '#ffffff',
    'w': '#c8ccd8',
    'g': '#8a8e9c',
    'G': '#4a4c58',
    'R': '#e8261c',
    'r': '#9a120c',
    'P': '#ff8fb8',
    'p': '#d0508a',
    'O': '#ff8a1f',
    'o': '#c05a10',
    'Y': '#ffd23a',
    'y': '#c48c0c',
    'E': '#4fc040',
    'e': '#23772a',
    'B': '#3a7aff',
    'b': '#1f3a9a',
    'C': '#5ae8ff',
    'c': '#1e9ac0',
    'V': '#9146ff',
    'v': '#5a23b8',
    'N': '#a8642a',
    'n': '#5a3414',
    'S': '#f6c896',
    's': '#c8905a',
    'T': '#e8d8a8',  # tan / bone
    't': '#b0a070',
    'L': '#b8f070',  # lime
    'l': '#6aa83a',
}


def sprite(lines, pal=None, ink=None):
    """Parse ascii-art into RGBA array. '.' and ' ' are transparent.
    'I' = ink, 'J' = ink highlight, 'i' = ink shade (if ink given)."""
    if isinstance(lines, str):
        lines = [l for l in lines.strip('\n').split('\n')]
    lines = [l.rstrip() for l in lines]
    # strip common indentation
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    lines = [l[ind:] for l in lines]
    w = max(len(l) for l in lines)
    h = len(lines)
    p = dict(BASE_PAL)
    if ink is not None:
        p['I'] = ink
        p['J'] = lighten(ink, 0.45) if lum(ink) < 0.85 else mix(ink, '#ffffff', 0.6)
        p['i'] = darken(ink, 0.35)
    if pal:
        p.update(pal)
    a = np.zeros((h, w, 4), np.uint8)
    for y, l in enumerate(lines):
        for x, ch in enumerate(l):
            if ch in '. ':
                continue
            if ch not in p:
                raise KeyError('palette char %r missing' % ch)
            a[y, x] = hexc(p[ch])
    return a


def scale_arr(a, s):
    return np.repeat(np.repeat(a, s, axis=0), s, axis=1)


def flip_h(a):
    return a[:, ::-1].copy()


def recolor(a, mapping):
    """mapping: {src_hex: dst_hex}"""
    a = a.copy()
    for s, d in mapping.items():
        s = hexc(s)
        d = hexc(d)
        m = (a[:, :, 0] == s[0]) & (a[:, :, 1] == s[1]) & (a[:, :, 2] == s[2]) & (a[:, :, 3] > 0)
        a[m] = d
    return a


# ------------------------------------------------------------ contact sheet
def contact_sheet(items, cell, cols, bg=(38, 70, 52, 255), label_h=14, scale=1, font=None, pad_px=6):
    """items: list of (label, PIL.Image RGBA). Returns PIL image."""
    from PIL import ImageDraw, ImageFont
    rows = (len(items) + cols - 1) // cols
    cw, ch = cell
    W = cols * (cw + pad_px) + pad_px
    H = rows * (ch + label_h + pad_px) + pad_px
    sheet = Image.new('RGBA', (W, H), bg)
    d = ImageDraw.Draw(sheet)
    try:
        fnt = font or ImageFont.truetype('arial.ttf', 11)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (lab, im) in enumerate(items):
        r, c = divmod(i, cols)
        x = pad_px + c * (cw + pad_px)
        y = pad_px + r * (ch + label_h + pad_px)
        im2 = im
        if im2.size != (cw, ch):
            s = min(cw / im2.width, ch / im2.height)
            im2 = im2.resize((max(1, int(im2.width * s)), max(1, int(im2.height * s))), Image.NEAREST)
        sheet.alpha_composite(im2, (x + (cw - im2.width) // 2, y + (ch - im2.height) // 2))
        d.text((x + cw // 2, y + ch + 1), lab, fill=(235, 235, 220, 255), font=fnt, anchor='ma')
    return sheet
