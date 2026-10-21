"""Helpers for chunky outlined pixel icons (staff / events / ui).

A *part* is drawn as a mask, filled with a base colour, shaded with a light from
the top-left (highlight band on the upper-left rim, shadow band on the lower-right
rim) and outlined with the near-black outline colour, then composited.
"""
import math
import numpy as np
from pix import Canvas, hexc, mix, darken, lighten, lum, outline_arr, sprite, pad

OUTLINE = '#14101c'


class Icon:
    def __init__(self, w, h=None):
        self.w = w
        self.h = h if h is not None else w
        self.a = np.zeros((self.h, self.w, 4), np.uint8)

    def add(self, arr, x=0, y=0):
        h, w = arr.shape[:2]
        sx0, sy0 = max(0, -x), max(0, -y)
        sx1, sy1 = min(w, self.w - x), min(h, self.h - y)
        if sx1 <= sx0 or sy1 <= sy0:
            return
        sub = arr[sy0:sy1, sx0:sx1]
        dst = self.a[y + sy0:y + sy1, x + sx0:x + sx1]
        m = sub[:, :, 3] > 0
        dst[m] = sub[m]

    def part(self, draw, base, hi=None, sh=None, outline=OUTLINE, hi_amt=0.35, sh_amt=0.35,
             band=1, diag=False, shade=True):
        """draw(cv) paints any colour into a fresh canvas; the painted area is the mask."""
        cv = Canvas(self.w, self.h)
        draw(cv)
        m = cv.a[:, :, 3] > 0
        arr = shade_mask(m, base, hi, sh, hi_amt, sh_amt, band, shade)
        if outline:
            arr = outline_arr(arr, outline, diag=diag)
        self.add(arr)
        return m

    def raw(self, draw):
        """draw directly on top (details)."""
        cv = Canvas(self.w, self.h, arr=self.a)
        draw(cv)
        self.a = cv.a

    def ascii(self, art, pal, x, y, outline=None):
        s = sprite(art, pal)
        if outline:
            s = outline_arr(pad(s, 1), outline)
            x -= 1
            y -= 1
        self.add(s, x, y)

    def outline(self, col=OUTLINE):
        self.a = outline_arr(self.a, col)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = hexc(c)


def shade_mask(m, base, hi=None, sh=None, hi_amt=0.35, sh_amt=0.35, band=1, shade=True):
    H, W = m.shape
    base_c = hexc(base)
    hi_c = hexc(hi) if hi else lighten(base, hi_amt)
    sh_c = hexc(sh) if sh else darken(base, sh_amt)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[m] = base_c
    if not shade:
        return arr

    def shifted(dx, dy):
        s = np.zeros_like(m)
        ys0, ys1 = max(0, dy), H + min(0, dy)
        xs0, xs1 = max(0, dx), W + min(0, dx)
        s[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        return s
    # pixel is on the upper-left rim if its left or upper neighbour is outside
    for b in range(1, band + 1):
        ul = m & (~shifted(b, 0) | ~shifted(0, b))
        lr = m & (~shifted(-b, 0) | ~shifted(0, -b))
        k = 1.0 if b == 1 else 0.5
        arr[ul & ~lr] = mix(base_c, hi_c, k) if b > 1 else hi_c
        arr[lr] = mix(base_c, sh_c, k) if b > 1 else sh_c
    return arr


def star_pts(cx, cy, r1, r2, n=5, rot=-math.pi / 2):
    pts = []
    for k in range(n * 2):
        r = r1 if k % 2 == 0 else r2
        a = rot + k * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sparkle(ic, x, y, size=2, col='#ffffff', col2='#fff6b0'):
    ic.px(x, y, col)
    for d in range(1, size + 1):
        c = col2 if d == size else col
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            ic.px(x + dx, y + dy, c)


def to_png(arr, scale, path):
    from PIL import Image
    import os
    a = arr.copy()
    a[a[:, :, 3] == 0] = 0
    im = Image.fromarray(a, 'RGBA')
    if scale != 1:
        im = im.resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im
