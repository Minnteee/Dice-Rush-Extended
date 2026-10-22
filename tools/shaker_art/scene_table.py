"""Round fortune-teller table, table cloths and cushions for the Dice Shaker scene.

Geometry (native 480x270 canvas):  the table top is an ellipse (centre TCX,TCY,
radii TRX,TRY - a round table seen from slightly above).  The cloth is a round
cloth of radius RC that was slid SHIFT units towards the viewer: it leaves the
wooden rim visible at the back and the sides and hangs over the front edge as a
crescent-shaped drape (drop = SHIFT + sqrt(RC^2-x^2) - sqrt(TRX^2-x^2)).
"""
import math

import numpy as np

from scene_lib import (grid, quantize, fbm, vnoise, hash01, ramp_arr, hexc, mix, dilate, erode,
                       edge_out, edge_in, shift, paint, lerp_ramp, ellipse_line, char_map)

# ------------------------------------------------------------- palettes
WOOD = ['#0c0508', '#170a0d', '#230f10', '#311613', '#421d16', '#56261a', '#6c311f', '#863f26', '#a3522f']
WOOD_OUT = '#070304'
GOLD = ['#2c1806', '#5a370c', '#8c5c16', '#bd8624', '#e2ad3a', '#f7d46c', '#fff0bc']
GOLD_OUT = '#1e0f04'


class TableGeo:
    """all lengths in native px; y0 = canvas row of the sprite's top edge."""

    def __init__(self, W=480, H=100, y0=170, cx=240.0, cy=200.0, rx=226.0, ry=28.0, top_t=5,
                 apron_in=10.0, apron_h=12, leg_dx=166.0, rc=160.0, shift=96.0, ts=2.6,
                 cushion=None, shadows=(), legs=True, mini=False):
        self.W, self.H, self.y0 = W, H, y0
        self.cx, self.cy, self.rx, self.ry = cx, cy, rx, ry
        self.k = ry / rx
        self.top_t = top_t
        self.apron_in, self.apron_h = apron_in, apron_h
        self.leg_dx = leg_dx
        self.rc, self.shift = rc, shift
        self.ccy = cy + shift * self.k      # cloth centre (screen y)
        self.cry = rc * self.k
        self.ts = ts                        # vertical stretch of pattern space on the flat top
        self.cushion = cushion              # (cx, cy, rx, ry) footprint for the contact shadow
        self.shadows = shadows              # [(cx, cy, rx, ry, strength)] on the wood top
        self.legs = legs
        self.mini = mini

    def edge_y(self, dx):
        return self.cy + self.ry * np.sqrt(np.clip(1 - (dx / self.rx) ** 2, 0, 1))

    def drop(self, dx):
        d = self.shift + np.sqrt(np.clip(self.rc ** 2 - dx ** 2, 0, None)) - np.sqrt(np.clip(self.rx ** 2 - dx ** 2, 0, None))
        return np.where(np.abs(dx) < min(self.rc, self.rx), d, -1.0)

    def drape_half_width(self):
        a2 = self.rx ** 2 - self.rc ** 2
        b = (a2 / self.shift + self.shift) / 2.0
        return math.sqrt(max(self.rx ** 2 - b * b, 0))


SCENE_GEO = dict(cushion=(240.0, 205.5, 69.0, 12.0),
                 shadows=[(55.0, 208.5, 31.0, 3.6, 0.55), (401.0, 203.0, 10.0, 2.2, 0.5), (423.0, 213.0, 10.0, 2.2, 0.5)])


def scene_geo():
    return TableGeo(**SCENE_GEO)


# ------------------------------------------------------------------ helpers
def ell_dist(X, Y, cx, cy, rx, ry):
    """approx. screen-space signed distance to an ellipse border (inside > 0) and rho."""
    ex = (X - cx) / rx
    ey = (Y - cy) / ry
    rho = np.sqrt(ex * ex + ey * ey)
    g = np.sqrt((ex / rx) ** 2 + (ey / ry) ** 2) / np.maximum(rho, 1e-6)
    return (1 - rho) / np.maximum(g, 1e-6), rho


def ramp_paint(img, mask, stops, lev, dither=0.4, ox=0, oy=0):
    r = ramp_arr(stops)
    idx = quantize(lev, len(stops), dither, ox, oy)
    img[mask, :3] = r[idx[mask]]
    img[mask, 3] = 255


def col_rows(g, H, W, yfun):
    """integer row (canvas y) per column for a curve y = yfun(dx)."""
    xs = np.arange(W) + 0.5
    return np.floor(yfun(xs - g.cx)).astype(np.int32)


# ------------------------------------------------------------------ table
def render_table(g):
    H, W = g.H, g.W
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W, 0, g.y0)
    Yi = np.floor(Y).astype(np.int32)
    dx = X - g.cx
    ex = dx / g.rx
    d_edge, rho = ell_dist(X, Y, g.cx, g.cy, g.rx, g.ry)
    E_rows = col_rows(g, H, W, g.edge_y)[None, :]
    valid = np.abs(ex) <= 1.0
    top = ((rho <= 1.0) | (Yi == E_rows)) & (Yi <= E_rows) & valid      # row based front edge

    # ---------------- table top (polished dark wood)
    lev = np.full((H, W), 0.42, np.float32)
    lev += 0.14 * np.exp(-(dx / 170.0) ** 2)
    lev += 0.12 * np.exp(-((X - 405) / 50.0) ** 2 - ((Y - 204) / 16.0) ** 2)      # candle light
    lev -= 0.16 * np.clip(np.abs(ex), 0, 1) ** 4
    # long grain streaks, one pixel high, following the rows
    row_seed = Yi * 7 + 3
    tone = vnoise(X / 34.0, row_seed * 1.37, 5)
    tone2 = vnoise(X / 21.0 + 50, row_seed * 0.71, 6)
    lev = np.where(tone > 0.70, lev - 0.11, lev)
    lev = np.where(tone > 0.84, lev - 0.07, lev)
    lev = np.where(tone2 < 0.16, lev + 0.07, lev)
    # rim bevel: outer dark line, highlight, soft shadow inside
    lev = np.where(top & (d_edge < 1.0), 0.20, lev)
    lev = np.where(top & (d_edge >= 1.0) & (d_edge < 2.0), lev + 0.26, lev)
    lev = np.where(top & (d_edge >= 2.0) & (d_edge < 3.0), lev + 0.08, lev)
    # contact shadows of the props
    for (sx, sy, srx, sry, st) in g.shadows:
        e = ((X - sx) / srx) ** 2 + ((Y - sy) / sry) ** 2
        lev = np.where(e < 1.0, lev - st * 0.45, lev)
        lev = np.where((e >= 1.0) & (e < 1.8), lev - st * 0.2, lev)
    ramp_paint(img, top, WOOD, lev, 0.25, 0, g.y0)

    # gold inlay ring
    if not g.mini:
        ring = ellipse_line(H, W, g.cx, g.cy, g.rx * 0.905, g.ry * 0.905, 0, g.y0) & top
        glev = 0.52 + 0.30 * np.exp(-(dx / 120.0) ** 2) * (Y < g.cy) - 0.25 * np.abs(ex) ** 3
        glev += 0.2 * np.exp(-((X - 405) / 40.0) ** 2)
        ramp_paint(img, ring, GOLD[1:], glev, 0.0)
        groove = ellipse_line(H, W, g.cx, g.cy, g.rx * 0.905 - 1.6, g.ry * 0.905 - 0.9, 0, g.y0) & top & ~ring
        img[groove, :3] = (np.array(img[groove, :3], np.float32) * 0.62).astype(np.uint8)

    # ---------------- front face of the top (per column rows)
    e_row = col_rows(g, H, W, g.edge_y)[None, :]           # last row of the top surface
    rr = Yi - e_row - 1                                     # 0.. below the top
    valid_col = (np.abs(ex) <= 1.0)
    band = (~top) & valid_col & (rr >= 0) & (rr < g.top_t)
    blev = np.select([rr == 0, rr == 1, rr == 2, rr == 3], [0.74, 0.56, 0.46, 0.36], 0.22).astype(np.float32)
    blev -= 0.34 * np.abs(ex) ** 3
    blev += 0.12 * np.exp(-((X - 405) / 40.0) ** 2)
    ramp_paint(img, band, WOOD, blev, 0.0)

    # ---------------- apron (inset cylinder below the top)
    arx = g.rx - g.apron_in
    exa = dx / arx
    sarc = arx * np.arcsin(np.clip(exa, -1, 1))
    ph = np.mod(sarc + 12.0, 24.0) / 12.0 - 1.0
    scal = np.floor(3.2 * np.sqrt(np.clip(1 - ph * ph, 0, 1)) + 0.35).astype(np.int32)
    ar = rr - g.top_t                                       # rows below the band
    ah = g.apron_h if not g.mini else 3
    apron = (~top) & (np.abs(exa) < 1) & (ar >= 0) & (ar < ah + scal)
    alev = 0.44 - 0.34 * np.abs(exa) ** 2.2
    alev += (vnoise(X / 1.5, np.floor(X / 3.0) * 0.0 + Y / 40.0, 21) - 0.5) * 0.10
    alev = np.where(ar == 0, 0.10, alev)
    alev = np.where(ar == 1, alev - 0.12, alev)
    alev = np.where(ar >= ah + scal - 1, alev - 0.14, alev)
    ramp_paint(img, apron, WOOD, alev, 0.0)
    if not g.mini:
        gl = apron & (ar == ah - 3)
        glv = 0.55 - 0.38 * np.abs(exa) ** 2 + 0.12 * np.exp(-((X - 405) / 40.0) ** 2)
        ramp_paint(img, gl, GOLD[1:6], glv, 0.0)
        under = apron & (ar == ah - 2)
        img[under, :3] = (np.array(img[under, :3], np.float32) * 0.7).astype(np.uint8)

    # ---------------- legs
    if g.legs:
        a_bot_rows = (np.floor(g.edge_y(np.arange(W) + 0.5 - g.cx)) + 1 + g.top_t + ah).astype(int)
        for side in (-1, 1):
            draw_leg(img, g, side, a_bot_rows)

    # ---------------- outline
    m = img[..., 3] > 0
    e = edge_out(m)
    img[e] = hexc(WOOD_OUT)
    return img


# carved acanthus leaf hanging over the knee (gold): a = dark .. e = light
LEAF = char_map("""
.a.....a.
.ab...ba.
..bc.cb..
.abcdcba.
..bcecb..
..abdba..
...bcb...
...aba...
....a....
""")


def leg_profile(j):
    """outer/inner half widths (px) of the cabriole leg at row j below the apron (outer = away from the
    table centre) and the sideways offset of its axis."""
    t = j / 38.0
    if t < 0.5:
        knee = math.sin(math.pi * t / 0.5 * 0.5)
    else:
        knee = math.cos(math.pi * 0.5 * min((t - 0.5) / 0.5, 1.0))
    outer = 6.4 + 4.6 * knee - 1.6 * max(0.0, t - 0.5) / 0.5
    inner = 6.0 - 1.4 * min(t / 0.7, 1.0) + 0.8 * knee
    axis = -2.2 * max(0.0, t - 0.45) / 0.55          # the lower leg sweeps back under the table
    if j < 5:                                         # scroll brackets under the apron
        outer += (5 - j) * 1.15
        inner += (5 - j) * 0.9
    return outer, inner, axis


def draw_leg(img, g, side, a_bot_rows):
    """carved cabriole leg (front view) attached under the apron, cut by the bottom edge."""
    H, W = img.shape[:2]
    lx = g.cx + side * g.leg_dx
    col = int(lx)
    ytop = int(a_bot_rows[col]) - 2            # canvas y where the leg starts (tucked under the apron)
    light = -side                              # lit from the table centre (the glowing ball)
    wood = ramp_arr(WOOD)
    rows = g.y0 + H - ytop
    for j in range(rows):
        y = ytop + j
        t = j / 38.0
        outer, inner, axis = leg_profile(j)
        ax = lx + side * axis
        x0 = ax - inner if side > 0 else ax - outer
        x1 = ax + outer if side > 0 else ax + inner
        for x in range(int(math.floor(x0)), int(math.ceil(x1))):
            if not (0 <= x < W and 0 <= y - g.y0 < H):
                continue
            if img[y - g.y0, x, 3] > 0:
                continue
            c = ((x + 0.5) - (x0 + x1) / 2) / max((x1 - x0) / 2, 1)
            cl = c * light
            lv = 0.36 + 0.26 * cl - 0.16 * min(t, 1.0)
            if abs(cl - 0.45) < 0.16:
                lv += 0.20                            # long glossy highlight
            if cl < -0.66:
                lv -= 0.10
            if j < 5:
                lv = 0.26 + 0.10 * cl + (0.22 if j == 0 else 0) + (0.12 if abs(c) > 0.75 and j in (1, 2) else 0)
            k = int(np.clip(round(lv * (len(WOOD) - 1)), 0, len(WOOD) - 1))
            img[y - g.y0, x, :3] = wood[k]
            img[y - g.y0, x, 3] = 255
    # gold acanthus leaf on the knee
    gold = ramp_arr(GOLD)
    lut = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
    ky = ytop + 4
    half = LEAF.shape[1] // 2
    kx = int(round(lx + side * 2.0)) - half
    for (yy, xx), ch in np.ndenumerate(LEAF):
        if ch == '.':
            continue
        X0, Y0 = kx + xx, ky + yy - g.y0
        if 0 <= X0 < W and 0 <= Y0 < H:
            k = lut[ch] + (1 if (xx - half) * light > 0 and ch in 'bcd' else 0)
            img[Y0, X0, :3] = gold[min(k, 6)]
            img[Y0, X0, 3] = 255
