"""Dice Shaker - 30 gauntlet mouse cursors  (art/gauntlets/)

Output (build/generated/shaker/art/gauntlets/):
  gauntlet_1.png ... gauntlet_30.png   128x128 RGBA (native 64x64 grid upscaled x2 with NEAREST),
                                        hard alpha (0/255), transparent background
  gauntlets.json                       {"gauntlet_k": {"hotspot": [x, y], "name_en": .., "name_de": ..}}
                                        hotspot = tip of the index finger / talon, in 128px space
  contact_sheet.png                    labelled review sheet (2x, hotspot marked green)
  _preview_check.png                   every cursor at 64x64 on dark purple and on a light background

Format and outline follow the Dice Rush Extended cursors (tools/art/gen_cursors.py): 1px near-black
outline + 1px coloured outer rim, so every cursor reads on dark and on light backgrounds. The game
scales the 128px image to ~68px (nearest), i.e. one native pixel ~ one screen pixel.

How the art is made
* Every hand is built from signed distance shapes in an upright "hand space" (index finger tip at
  the origin, u = towards the little finger, v = towards the wrist). Hand space is rotated by
  atan(1/2) = 26.6 deg (clean 2:1 pixel steps), so the index finger points up-left and its tip is
  the top-left-most point of the hand.
* Parts are layered (later = in front). Each part is lit from the hand's upper left with 1-2px
  highlight / shadow rings along its own edges ("matte", "cloth", "skin", "metal" with specular
  line + reflected light), or flat facets ("gem": quantised bevel normals, "facet": voronoi facets)
  or as an emissive "glow" (fire, lightning). A broad term from the whole silhouette rounds the big
  plates. Then cast shadows, seams between parts, details (plates, rivets, gems, emblems) and small,
  calm effects (flames, icicles, leaves, wings, sparkles - no glow halos).
* Fully deterministic (no random numbers, only fixed hash noise).

run:  tools/venv/Scripts/python.exe tools/shaker_art/gen_gauntlets.py
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(REPO, 'build', 'generated', 'shaker', 'art', 'gauntlets')
N = 64                                          # native grid
SC = 2                                          # upscale factor -> 128x128
ANGLE = math.degrees(math.atan2(1.0, 2.0))      # hand tilt (26.6 deg, 2:1 pixel steps)
YC, XC = np.mgrid[0:N, 0:N].astype(float) + 0.5  # pixel centres
OUTLINE = '#0c0a10'


# ------------------------------------------------------------------ colours
def hexc(c):
    if c is None:
        return (0, 0, 0, 0)
    if isinstance(c, (tuple, list, np.ndarray)):
        t = tuple(int(v) for v in c)
        return t if len(t) == 4 else t + (255,)
    s = c.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def hash2(x, y, seed=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


# ------------------------------------------------------------------ signed distance shapes
def sd_capsule(U, V, a, b, ra, rb=None):
    rb = ra if rb is None else rb
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = np.clip(((U - ax) * dx + (V - ay) * dy) / L2, 0, 1) if L2 > 0 else np.zeros_like(U)
    return np.hypot(U - (ax + t * dx), V - (ay + t * dy)) - (ra + (rb - ra) * t)


def sd_path(U, V, pts, r0, r1=None):
    """tapered thick polyline"""
    r1 = r0 if r1 is None else r1
    lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    tot = sum(lens)
    acc = 0.0
    d = np.full(U.shape, 1e9)
    for i in range(len(pts) - 1):
        ra = r0 + (r1 - r0) * acc / tot
        acc += lens[i]
        rb = r0 + (r1 - r0) * acc / tot
        d = np.minimum(d, sd_capsule(U, V, pts[i], pts[i + 1], ra, rb))
    return d


def sd_circle(U, V, cx, cy, r):
    return np.hypot(U - cx, V - cy) - r


def sd_ellipse(U, V, cx, cy, rx, ry):
    k = np.hypot((U - cx) / rx, (V - cy) / ry)
    return (k - 1.0) * min(rx, ry)


def sd_poly(U, V, pts, r=0.0):
    pts = [(float(a), float(b)) for a, b in pts]
    n = len(pts)
    d = (U - pts[0][0]) ** 2 + (V - pts[0][1]) ** 2
    s = np.ones_like(U)
    j = n - 1
    for i in range(n):
        vi, vj = pts[i], pts[j]
        ex, ey = vj[0] - vi[0], vj[1] - vi[1]
        wx, wy = U - vi[0], V - vi[1]
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = V >= vi[1]
        c2 = V < vj[1]
        c3 = ex * wy > ey * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
        j = i
    return s * np.sqrt(d) - r


def band(V, a, b):
    return np.maximum(a - V, V - b)


def inter(*s):
    return np.maximum.reduce(s)


def union(*s):
    return np.minimum.reduce(s)


# ------------------------------------------------------------------ hand space -> pixels, materials
class Rig:
    def __init__(self, scale, tip, angle=ANGLE):
        th = math.radians(angle)
        self.s = scale
        self.eu = (math.cos(th), -math.sin(th))
        self.ev = (math.sin(th), math.cos(th))
        self.T = tip
        dx = (XC - tip[0]) / scale
        dy = (YC - tip[1]) / scale
        self.U = dx * self.eu[0] + dy * self.eu[1]
        self.V = dx * self.ev[0] + dy * self.ev[1]

    def P(self, u, v):
        return (self.T[0] + self.s * (u * self.eu[0] + v * self.ev[0]),
                self.T[1] + self.s * (u * self.eu[1] + v * self.ev[1]))

    def Pi(self, u, v):
        x, y = self.P(u, v)
        return int(math.floor(x)), int(math.floor(y))


class Mat:
    """colour ramp (dark -> light) + shading model
    kind: 'matte' / 'cloth' / 'skin' / 'metal'  edge-ring shading (metal: specular line + reflected light)
          'gem'    quantised normals of the part's bevel (cut stone look)
          'facet'  flat voronoi facets with bright facet edges (crystal, obsidian, diamond)
          'glow'   emissive: darker rim, bright core (fire, lightning)"""
    EDGES = {
        'matte': [(1, -1), (0, -1)],
        'cloth': [(1, -1), (0, 0)],
        'skin': [(1, -1), (0, 0)],
        'metal': [(1, 0), (2, -2), (0, -1)],
    }

    def __init__(self, ramp, kind='matte', base=None, edges=None, broad=None, fspread=1.5, fborder=1.5):
        self.ramp = [hexc(c) for c in ramp]
        self.kind = kind
        self.base = base if base is not None else (len(self.ramp) - 1) // 2
        # per edge ring (outermost first): (delta on the lit side, delta on the shadow side)
        self.edges = edges if edges is not None else self.EDGES.get(kind, [(1, -1)])
        self.strong = {1: 1} if kind == 'metal' else {}   # extra specular where a metal edge faces the light
        self.broad = broad if broad is not None else {'metal': 1.6, 'gem': 1.0}.get(kind, 1.3)
        self.fspread = fspread   # facet shader: tone spread between facets
        self.fborder = fborder   # facet shader: brightness of the facet edges

    def c(self, i):
        return self.ramp[max(0, min(len(self.ramp) - 1, int(i)))]

    @property
    def dark(self):
        return self.ramp[0]


def M(kind, *cols, **kw):
    return Mat(list(cols), kind, **kw)


# ------------------------------------------------------------------ pixel helpers
def sprite(txt, pal):
    lines = [l for l in txt.strip('\n').split('\n')]
    ind = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    lines = [l[ind:].rstrip() for l in lines]
    w = max(len(l) for l in lines)
    a = np.zeros((len(lines), w, 4), np.uint8)
    for y, l in enumerate(lines):
        for x, ch in enumerate(l):
            if ch not in '. ':
                a[y, x] = hexc(pal[ch])
    return a


def erode4(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    e[0, :] = e[-1, :] = False
    e[:, 0] = e[:, -1] = False
    return e


def rings(m, n):
    """ring index of every pixel of mask m (0 = outer edge), >= n for the interior"""
    r = np.full(m.shape, 99, np.int32)
    cur = m.copy()
    for k in range(n):
        e = erode4(cur)
        r[cur & ~e] = k
        cur = e
    return r


def shift(a, dx, dy):
    """s[y, x] = a[y + dy, x + dx] (zero outside)"""
    s = np.zeros_like(a)
    H, W = a.shape[:2]
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    s[ys0:ys1, xs0:xs1] = a[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return s


def outline_arr(a, c, diag=False):
    a = a.copy()
    m = a[:, :, 3] > 0
    g = np.zeros_like(m)
    g[1:, :] |= m[:-1, :]
    g[:-1, :] |= m[1:, :]
    g[:, 1:] |= m[:, :-1]
    g[:, :-1] |= m[:, 1:]
    if diag:
        g[1:, 1:] |= m[:-1, :-1]
        g[1:, :-1] |= m[:-1, 1:]
        g[:-1, 1:] |= m[1:, :-1]
        g[:-1, :-1] |= m[1:, 1:]
    a[g & ~m] = hexc(c)
    return a


def outlined(spr, col):
    """sprite with a 1px outline of colour col around it (grows by 1px on every side)"""
    a = np.zeros((spr.shape[0] + 2, spr.shape[1] + 2, 4), np.uint8)
    a[1:-1, 1:-1] = spr
    return outline_arr(a, col)


# ------------------------------------------------------------------ the builder
class G:
    """one gauntlet: layered parts (signed distance fields in hand space) -> shaded 64x64 pixels"""

    def __init__(self, scale=1.0, tip=(8.0, 3.0)):
        self.rig = Rig(scale, tip)
        self.U, self.V = self.rig.U, self.rig.V
        self.parts = []
        # light from the hand's upper left (hand space) -> 2D screen direction
        lu, lv = -0.6, -0.8
        sx = lu * self.rig.eu[0] + lv * self.rig.ev[0]
        sy = lu * self.rig.eu[1] + lv * self.rig.ev[1]
        n = math.hypot(sx, sy)
        self.L2 = (sx / n, sy / n)
        self.form_r = 6.0        # bevel radius of the whole silhouette (broad light / shade)
        self.pointer = 'idx'     # part name(s) whose tip is the click point
        self.accents = []
        self.a = None

    # ---- parts
    def add(self, name, sdf, mat, bevel=4.0, seam='hard', shadow=True, bias=0.0, form=True):
        """add a part in front of the previous ones.
        bevel: rounding radius (gem shader); seam: line drawn on this part where it lies over an earlier
        part ('hard' = darkest ramp colour, 'dark' = outline colour, 'soft' = one step darker, '#rrggbb'
        or None); shadow: receives cast shadows; form: belongs to the overall silhouette volume"""
        self.parts.append(dict(name=name, sdf=sdf, mat=mat, bevel=bevel, seam=seam, shadow=shadow, bias=bias,
                               form=form))
        return sdf

    def P(self, u, v):
        return self.rig.P(u, v)

    def Pi(self, u, v):
        return self.rig.Pi(u, v)

    def mask(self, *names):
        m = np.zeros((N, N), bool)
        for nm in names:
            for i, p in enumerate(self.parts, 1):
                if p['name'] == nm or (nm.endswith('*') and p['name'].startswith(nm[:-1])):
                    m |= self.lab == i
        return m

    # ---- rendering of the parts
    def render(self):
        lab = np.zeros((N, N), np.int32)
        for i, p in enumerate(self.parts, 1):
            lab[p['sdf'] <= 0] = i
        self.lab = lab
        idx = np.zeros((N, N), np.int32)
        L2 = self.L2
        # global form (whole silhouette as one rounded volume) -> broad light / shade of the interiors
        sd_all = np.min([p['sdf'] for p in self.parts if p['form']], axis=0)
        dg = np.clip(-sd_all * self.rig.s, 0, None)
        Rg = self.form_r
        kg = np.clip(dg / Rg, 0, 1)
        hg = Rg * np.sqrt(1 - (1 - kg) ** 2)
        ggy, ggx = np.gradient(hg)
        broad = -(ggx * L2[0] + ggy * L2[1])
        for i, p in enumerate(self.parts, 1):
            m = lab == i
            if not m.any():
                continue
            mat = p['mat']
            full = p['sdf'] <= 0
            ring = rings(full, 4)
            gy, gx = np.gradient(p['sdf'])
            facing = (gx * L2[0] + gy * L2[1]) / (np.hypot(gx, gy) + 1e-9)
            v = np.full((N, N), float(mat.base) + p['bias'])
            prof = mat.edges
            inner = ring >= len(prof)
            v += np.where(inner, np.clip(np.round(broad * mat.broad), -1, 1), 0)
            for r, (dl, ds) in enumerate(prof):
                rr = ring == r
                v = np.where(rr & (facing > 0.28), v + dl, v)
                v = np.where(rr & (facing > 0.6), v + mat.strong.get(r, 0), v)
                v = np.where(rr & (facing < -0.28), v + ds, v)
            if mat.kind == 'gem':
                # facets: quantised normal of the part's own bevel
                din = np.clip(-p['sdf'] * self.rig.s, 0, None)
                R = max(p['bevel'], 0.6)
                k = np.clip(din / R, 0, 1)
                h = R * np.sqrt(1 - (1 - k) ** 2)
                hy, hx = np.gradient(h)
                tilt = np.hypot(hx, hy)
                ang = np.arctan2(-hy, -hx)
                q = np.round(ang / (math.pi / 4)) * (math.pi / 4)
                fac = np.cos(q) * L2[0] + np.sin(q) * L2[1]
                fv = np.where(tilt < 0.3, 0.0, np.round(fac * 1.6))
                v = mat.base + p['bias'] + fv + np.where(ring == 0, np.where(facing > 0.28, 1, np.where(facing < -0.28, -1, 0)), 0)
            if mat.kind == 'facet':
                # flat crystal facets: voronoi cells in hand space, each with its own tilt
                fid = self.facets(i, m)
                tone = np.zeros((N, N))
                for f in np.unique(fid[m]):
                    a_ = hash2(f, i, 11) * 2 * math.pi
                    tl = 0.35 + 0.65 * hash2(f, i, 12)
                    fx, fy = math.cos(a_) * tl, math.sin(a_) * tl
                    tone[fid == f] = round((fx * L2[0] + fy * L2[1]) * mat.fspread)
                v = mat.base + p['bias'] + tone
                v = np.where(ring == 0, np.where(facing > 0.28, v + 1, np.where(facing < -0.28, v - 1, v)), v)
                border = np.zeros((N, N), bool)
                border[:, :-1] |= fid[:, :-1] != fid[:, 1:]
                border[:-1, :] |= fid[:-1, :] != fid[1:, :]
                v = np.where(border & (ring > 0), np.maximum(v, mat.base) + mat.fborder, v)
            if mat.kind == 'glow':
                # emissive: dark rim, bright core
                v = np.minimum(ring, len(mat.ramp) - 1).astype(float) + p['bias']
            top = len(mat.ramp) - 1
            iv = np.clip(np.round(v), 0, top).astype(np.int32)
            idx[m] = iv[m]
        # cast shadows: a pixel whose upper-left neighbour belongs to a part in front is darker
        sh = np.zeros((N, N), bool)
        for dx, dy in ((-1, 0), (-1, -1)):
            sh |= (shift(lab, dx, dy) > lab) & (lab > 0)
        for i, p in enumerate(self.parts, 1):
            if p['shadow']:
                m = sh & (lab == i)
                idx[m] = np.maximum(idx[m] - 1, 0)
        # despeckle the quantised shading
        for i, p in enumerate(self.parts, 1):
            m = lab == i
            for y, x in zip(*np.nonzero(m)):
                vals = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < N and 0 <= yy < N and lab[yy, xx] == i:
                        vals.append(idx[yy, xx])
                if len(vals) >= 3 and idx[y, x] not in vals:
                    best = max(set(vals), key=vals.count)
                    if vals.count(best) >= 3:
                        idx[y, x] = best
        self.idx = idx
        a = np.zeros((N, N, 4), np.uint8)
        for i, p in enumerate(self.parts, 1):
            m = lab == i
            ramp = p['mat'].ramp
            for y, x in zip(*np.nonzero(m)):
                a[y, x] = ramp[idx[y, x]]
        # seams on the front part where it touches a part behind it
        for y, x in zip(*np.nonzero(lab)):
            i = lab[y, x]
            p = self.parts[i - 1]
            if p['seam'] is None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N and 0 < lab[yy, xx] < i:
                    s = p['seam']
                    if s == 'hard':
                        a[y, x] = p['mat'].dark
                    elif s == 'dark':
                        a[y, x] = hexc(OUTLINE)
                    elif s == 'soft':
                        a[y, x] = p['mat'].c(idx[y, x] - 1)
                    else:
                        a[y, x] = hexc(s)
                    break
        self.a = a
        return self

    def facets(self, i, m, cell=6.0):
        """voronoi facet id per pixel for part i (seeds on a jittered grid in hand space)"""
        U, V = self.U, self.V
        us, vs = U[m], V[m]
        seeds = []
        for gu in np.arange(math.floor(us.min() / cell) - 1, math.ceil(us.max() / cell) + 2):
            for gv in np.arange(math.floor(vs.min() / cell) - 1, math.ceil(vs.max() / cell) + 2):
                seeds.append((gu * cell + (hash2(gu, gv, 5 + i) - 0.5) * cell * 0.8,
                              gv * cell + (hash2(gu, gv, 9 + i) - 0.5) * cell * 0.8))
        best = np.full((N, N), 1e9)
        fid = np.zeros((N, N), np.int64)
        for k, (su, sv) in enumerate(seeds):
            d = (U - su) ** 2 + (V - sv) ** 2
            better = d < best
            best = np.where(better, d, best)
            fid = np.where(better, k, fid)
        return fid

    # ---- drawing helpers (screen space, positions given in hand space)
    def px(self, x, y, c, m=None):
        x, y = int(x), int(y)
        if 0 <= x < N and 0 <= y < N and (m is None or m[y, x]):
            self.a[y, x] = hexc(c)

    def hpx(self, u, v, c, m=None):
        x, y = self.Pi(u, v)
        self.px(x, y, c, m)

    def line(self, x0, y0, x1, y1, c, m=None):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        pts = []
        while True:
            pts.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        for (x, y) in pts:
            if callable(c):
                self.px(x, y, c(x, y), m)
            else:
                self.px(x, y, c, m)
        return pts

    def hline(self, u0, v0, u1, v1, c, m=None):
        x0, y0 = self.P(u0, v0)
        x1, y1 = self.P(u1, v1)
        return self.line(math.floor(x0), math.floor(y0), math.floor(x1), math.floor(y1), c, m)

    def fill(self, m, c):
        self.a[m] = hexc(c)

    def recolor(self, m, mat, delta=0, scale=1.0):
        """repaint mask m with another ramp, keeping the computed light level"""
        for y, x in zip(*np.nonzero(m & (self.lab > 0))):
            p = self.parts[self.lab[y, x] - 1]
            i = self.idx[y, x]
            k = int(round((i - p['mat'].base) * scale + mat.base + delta))
            self.a[y, x] = mat.c(k)

    def rivet(self, u, v, lit, dark, m=None):
        x, y = self.Pi(u, v)
        self.px(x, y, lit, m)
        self.px(x + 1, y + 1, dark, m)

    def studs(self, u0, v0, u1, v1, n, lit, dark, m=None):
        for t in np.linspace(0, 1, n):
            self.rivet(u0 + (u1 - u0) * t, v0 + (v1 - v0) * t, lit, dark, m)

    def blit(self, spr, x, y, m=None):
        h, w = spr.shape[:2]
        for yy in range(h):
            for xx in range(w):
                if spr[yy, xx, 3]:
                    self.px(x + xx, y + yy, spr[yy, xx], m)

    def blit_h(self, spr, u, v, m=None):
        """blit sprite centred on hand point (u, v)"""
        x, y = self.P(u, v)
        h, w = spr.shape[:2]
        self.blit(spr, int(round(x - w / 2)), int(round(y - h / 2)), m)

    def circle(self, cx, cy, r, c, m=None, ring=False):
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r and (not ring or d > r - 1.0):
                    self.px(x, y, c, m)

    def hsdf(self, sdf, c, m=None):
        mm = sdf <= 0
        if m is not None:
            mm &= m
        self.a[mm] = hexc(c)
        return mm

    def gem(self, cx, cy, rx, ry, cols, m=None):
        """small faceted cabochon in screen space: cols = (dark, base, light, white)"""
        dk, base, lt, wh = cols
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d <= 1.0:
                    c = base
                    if dx + dy > 0.55:
                        c = dk
                    elif dx + dy < -0.45:
                        c = lt
                    self.px(x, y, c, m)
        self.px(math.floor(cx - rx * 0.45), math.floor(cy - ry * 0.45), wh, m)

    def accent(self, spr, x, y, ol=OUTLINE):
        self.accents.append((spr, int(x), int(y), ol))

    # ---- final assembly
    def finish(self, rim, ol=OUTLINE):
        a = self.a.copy()
        a[a[:, :, 3] == 0] = 0
        a = outline_arr(a, ol)
        a = outline_arr(a, rim)
        for spr, x, y, sol in self.accents:
            h, w = spr.shape[:2]
            layer = np.zeros((N, N, 4), np.uint8)
            for yy in range(h):
                for xx in range(w):
                    if spr[yy, xx, 3] and 0 <= x + xx < N and 0 <= y + yy < N:
                        layer[y + yy, x + xx] = spr[yy, xx]
            if sol:
                layer = outline_arr(layer, sol)
            mm = layer[:, :, 3] > 0
            a[mm] = layer[mm]
        return a

    def tip(self):
        """pixel of the pointer part that lies furthest along the finger (= click point)"""
        names = [self.pointer] if isinstance(self.pointer, str) else self.pointer
        m = self.mask(*names)
        ys, xs = np.nonzero(m)
        vv = self.V[ys, xs]
        k = np.argmin(vv + 0.001 * np.abs(self.U[ys, xs]))
        return int(xs[k]), int(ys[k])


# ------------------------------------------------------------------ standard anatomy (hand space)
IDX_R = 4.2
CURL = [(8.6, 22.5, 28.0, 4.0), (15.6, 24.5, 30.0, 3.7), (21.8, 27.5, 32.0, 3.3)]
BACK_PTS = [(-4.0, 24.0), (24.5, 27.5), (22.5, 42.0), (-2.5, 42.0)]


def s_back(g, r=3.0):
    return sd_poly(g.U, g.V, BACK_PTS, r)


def s_idx(g, tip='round', r=IDX_R, base=27.0):
    U, V = g.U, g.V
    if tip == 'round':
        return sd_capsule(U, V, (0, r), (0, base), r)
    if tip == 'pointed':
        return union(sd_capsule(U, V, (0, 6.0), (0, base), r), sd_poly(U, V, [(-r, 6.0), (-0.6, 0.0), (0.6, 0.0), (r, 6.0)]))
    raise ValueError(tip)


def s_curl(g, k, grow=0.0, dv=0.0):
    u, v0, v1, r = CURL[k]
    return sd_capsule(g.U, g.V, (u, v0 + dv), (u, v1), r + grow)


def s_thumb(g, grow=0.0):
    return sd_capsule(g.U, g.V, (-3.0, 39.0), (-9.0, 29.0), 4.6 + grow, 3.6 + grow)


def s_cuff(g, v0=40.0, v1=55.0, w0=(-4.0, 23.0), flare=5.0, r=1.0):
    return sd_poly(g.U, g.V, [(w0[0], v0), (w0[1], v0), (w0[1] + flare, v1), (w0[0] - flare, v1)], r)


def std_hand(g, mat, tip='round', thumb_mat=None, curl_mat=None, back_mat=None, idx_mat=None,
             seam='hard', curl_seam=None, bevel_back=5.0):
    g.add('back', s_back(g), back_mat or mat, bevel_back, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        g.add(nm, s_curl(g, 2 - k), curl_mat or mat, CURL[2 - k][3], seam=curl_seam or seam)
    g.add('thb', s_thumb(g), thumb_mat or mat, 4.0, seam=seam)
    g.add('idx', s_idx(g, tip), idx_mat or mat, IDX_R, seam=seam)


def plated_idx(g, mat, cuts=(8.0, 15.5, 21.5), tip='pointed', seam='dark', grow=0.35, base=27.0):
    """index finger made of overlapping lames (tip plate first, proximal plates on top)"""
    full = [s_idx(g, tip, IDX_R + grow * i, base) for i in range(len(cuts) + 1)]
    edges = [-5.0] + list(cuts) + [base + 6.0]
    names = []
    for i in range(len(cuts) + 1):
        sd = inter(full[i], band(g.V, edges[i], edges[i + 1]))
        nm = 'idx' if i == 0 else 'idx%d' % i
        g.add(nm, sd, mat, IDX_R * 0.8, seam=seam)
        names.append(nm)
    g.pointer = names
    return names


def armor(g, mat, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=True, knuck_mat=None, cuff_mat=None,
          cuff=(40.0, 54.0, 5.0), rim_band=2.5, rim_mat=None, seam='dark', thumb_split=True,
          curl_mat=None, back_mat=None, idx_mat=None, thumb_mat=None, grow=0.35, extra_back=None):
    """standard plate gauntlet: back plate, curled finger plates, knuckle guard, 2-plate thumb,
    articulated index finger, flared cuff with a rolled rim"""
    g.add('back', s_back(g), back_mat or mat, 5.0, seam=None)
    if extra_back:
        extra_back()
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        kk = 2 - k
        g.add(nm, s_curl(g, kk), curl_mat or mat, CURL[kk][3] * 0.85, seam=seam)
    if knuck:
        g.add('knuck', sd_poly(g.U, g.V, [(-4.6, 23.0), (25.5, 26.0), (25.0, 31.5), (-4.0, 30.0)], 1.0),
              knuck_mat or mat, 2.2, seam=seam)
    g.add('thb', s_thumb(g), thumb_mat or mat, 3.6, seam=seam)
    if thumb_split:
        g.add('thb2', inter(s_thumb(g, 0.35), band(g.V, 33.5, 50)), thumb_mat or mat, 3.0, seam=seam)
    plated_idx(g, idx_mat or mat, cuts=cuts, tip=tip, seam=seam, grow=grow)
    v0, v1, fl = cuff
    g.add('cuff', s_cuff(g, v0, v1, flare=fl), cuff_mat or mat, 4.0, seam=seam)
    if rim_band:
        g.add('crim', inter(s_cuff(g, v0, v1 + 1.2, flare=fl + 0.45), band(g.V, v1 - rim_band, v1 + 2.0)),
              rim_mat or cuff_mat or mat, 1.6, seam=seam)


# ------------------------------------------------------------------ effect shapes
def s_spike(g, u0, v0, du, dv, L, w):
    n = math.hypot(du, dv)
    du, dv = du / n, dv / n
    pu, pv = -dv, du
    return sd_poly(g.U, g.V, [(u0 - pu * w / 2, v0 - pv * w / 2), (u0 + du * L, v0 + dv * L),
                              (u0 + pu * w / 2, v0 + pv * w / 2)])


def s_shard(g, u0, v0, du, dv, L, w):
    n = math.hypot(du, dv)
    du, dv = du / n, dv / n
    pu, pv = -dv, du
    h = w / 2
    return sd_poly(g.U, g.V, [(u0 - pu * h, v0 - pv * h), (u0 - pu * h + du * L * 0.68, v0 - pv * h + dv * L * 0.68),
                              (u0 + du * L, v0 + dv * L),
                              (u0 + pu * h + du * L * 0.68, v0 + pv * h + dv * L * 0.68), (u0 + pu * h, v0 + pv * h)])


def s_leaf(U, V, u0, v0, du, dv, L, w):
    n = math.hypot(du, dv)
    du, dv = du / n, dv / n
    pu, pv = -dv, du
    a, b = L / 2, w / 2
    R = (a * a + b * b) / (2 * b)
    d = R - b
    mu, mv = u0 + du * a, v0 + dv * a
    return np.maximum(sd_circle(U, V, mu + pu * d, mv + pv * d, R), sd_circle(U, V, mu - pu * d, mv - pv * d, R))


def x_poly(pts, r=0.0):
    return sd_poly(XC, YC, pts, r)


def x_path(pts, r0, r1):
    return sd_path(XC, YC, pts, r0, r1)


def x_flame(cx, cy, r, h, lean=0.0):
    """teardrop flame in screen space, rising up"""
    c = sd_circle(XC, YC, cx, cy, r)
    t = sd_poly(XC, YC, [(cx - r * 0.98, cy - r * 0.15), (cx + lean, cy - h), (cx + r * 0.98, cy - r * 0.15)])
    return np.minimum(c, t)


def x_icicle(x, y, w, h):
    return sd_poly(XC, YC, [(x - 0.5, y - 1.0), (x + w + 0.5, y - 1.0), (x + w / 2 + 0.3, y + h)])


def x_gear(cx, cy, R, teeth=8, th=1.5, hole=0.0, phase=0.0):
    ang = np.arctan2(YC - cy, XC - cx) + phase
    rr = np.hypot(XC - cx, YC - cy)
    tooth = np.cos(teeth * ang) > 0.15
    sd = rr - (R + th * tooth)
    if hole > 0:
        sd = np.maximum(sd, hole - rr)
    return sd


SPARK4 = """
..W..
..W..
WWwWW
..W..
..W.."""
SPARK3 = """
.W.
WwW
.W."""


def spark(col, small=False, core=None):
    return sprite(SPARK3 if small else SPARK4, {'W': col, 'w': core or '#ffffff'})


def split_shade(g, name, b, d, mat, lit=1, dark=-1):
    """two-tone crystal prism: the half of the part on the light side of its axis is lighter"""
    m = g.mask(name)
    du, dv = d
    for y, x in zip(*np.nonzero(m)):
        side = du * (g.V[y, x] - b[1]) - dv * (g.U[y, x] - b[0])
        k = g.idx[y, x] + (lit if side > 0 else dark)
        g.a[y, x] = mat.c(k)


def wing_l(g, R, mat, seam='hard'):
    """wing spreading to the lower left: curved leading edge with feathers hanging from it"""
    x, y = R
    fe = [((x - 3, y - 1.5), (x - 4.5, y + 5.5)), ((x - 7, y - 3.8), (x - 9.5, y + 5.5)),
          ((x - 11, y - 5.2), (x - 14.5, y + 4.5)), ((x - 14.5, y - 5.5), (x - 19, y + 1.5))]
    for k, (a, b) in enumerate(fe):
        g.add('lwf%d' % k, x_path([a, b], 2.6, 0.7), mat, 2.0, seam=seam)
    g.add('lwe', x_path([(x + 1, y), (x - 6, y - 4.2), (x - 12, y - 6.2), (x - 16.5, y - 5.5)], 2.6, 1.4), mat, 2.0,
          seam=seam)


def wing_r(g, R, mat, seam='hard'):
    """wing rising at the upper right"""
    x, y = R
    fe = [((x + 1.5, y - 3), (x + 7, y - 1)), ((x + 3.5, y - 7.5), (x + 9.5, y - 6)),
          ((x + 5, y - 12), (x + 11, y - 11.5))]
    for k, (a, b) in enumerate(fe):
        g.add('rwf%d' % k, x_path([a, b], 2.4, 0.7), mat, 2.0, seam=seam)
    g.add('rwe', x_path([(x - 1, y + 1), (x + 2.5, y - 6), (x + 4.5, y - 12), (x + 4.0, y - 16)], 2.4, 1.3), mat, 2.0,
          seam=seam)


# ------------------------------------------------------------------ palettes
LEATHER = M('matte', '#2a170c', '#4a2b17', '#6e4426', '#93613a', '#b88250', '#d9a870', base=3)
LEATHER_D = M('matte', '#1e1008', '#3a2112', '#58361e', '#77502e', '#9a6c40', '#b88a58', base=3)
WOOL = M('cloth', '#3c070c', '#650e16', '#911a22', '#b8282e', '#d84a44', '#f07a68', base=3)
CREAM = M('cloth', '#6e665a', '#a0978a', '#cfc7b8', '#ece6d8', '#fbf6ea', '#ffffff', base=3)
IRON = M('metal', '#141519', '#25282e', '#383c43', '#50555e', '#6c727c', '#929aa4', '#c4cad2', base=3)
IRON_D = M('metal', '#101114', '#1f2126', '#2f3238', '#43474f', '#5c616a', '#80868f', '#aab0b8', base=3)
BRONZE = M('metal', '#2e1606', '#552c0e', '#804818', '#ab6a28', '#d08f44', '#ecb46c', '#ffe0a8', base=3)
PATINA = ['#1f4f46', '#2f7a68', '#4fa88c', '#86d0b4']
SILVER = M('metal', '#262c36', '#434c5a', '#68737f', '#929ead', '#bec8d4', '#e4ebf2', '#ffffff', base=3)
GOLD = M('metal', '#3e2205', '#6e420b', '#a26a12', '#d49a22', '#f4c444', '#fde68a', '#fffbe0', base=3)
PLAT = M('metal', '#3a4050', '#5c6476', '#868ea0', '#b2b8c6', '#d8dce6', '#f2f4f8', '#ffffff', base=3)
STEEL = M('metal', '#1a1f26', '#323a46', '#4f5a68', '#76838f', '#a3afba', '#d0d9e0', '#ffffff', base=3)
BRASS = M('metal', '#3a2408', '#6a4612', '#9c6c1e', '#c8962e', '#e8c050', '#fbe48c', '#fffbe0', base=3)
COPPER = M('metal', '#3a1408', '#682812', '#94401e', '#bc5e2e', '#dc8448', '#f2ac74', '#ffe0c0', base=3)
BONE = M('matte', '#3e3526', '#6e624a', '#a49676', '#d2c6a4', '#efe7cc', '#fffbea', base=3)
CRYSTAL = M('facet', '#24124a', '#3e2280', '#5e3eb4', '#8664dc', '#b096f6', '#dccfff', '#ffffff', base=3,
            fborder=1.0)
CRYSTAL_S = M('gem', '#24124a', '#3e2280', '#5e3eb4', '#8664dc', '#b096f6', '#dccfff', '#ffffff', base=3)
RUBY = M('gem', '#33030d', '#5e0819', '#92102a', '#c81e3c', '#f0506a', '#ffa8b8', '#fff0f2', base=3)
EMERALD = M('gem', '#022a14', '#064e28', '#0c7a3e', '#1aa858', '#4ed488', '#a8f4c8', '#ffffff', base=3)
SAPPHIRE = M('gem', '#060e40', '#0c1c70', '#1632a8', '#2a56d8', '#5a8af4', '#a8c8ff', '#ffffff', base=3)
OBSID = M('facet', '#030205', '#0a0710', '#140e1e', '#1e162c', '#30244a', '#56447e', '#a690d8', base=2,
          fspread=2.2, fborder=2.6)
DIAMOND = M('facet', '#2c4a72', '#4c78a8', '#7aaed8', '#aedcf6', '#d8f2ff', '#f2fcff', '#ffffff', base=3)
DIAMOND_G = M('gem', '#2c4a72', '#4c78a8', '#7aaed8', '#aedcf6', '#d8f2ff', '#f2fcff', '#ffffff', base=4)
SKIN = M('skin', '#4a2414', '#7a4228', '#a8673f', '#cf9065', '#ecb88e', '#ffdcbc', base=3)
SKIN_T = M('skin', '#3a2014', '#6a3c26', '#9c6446', '#c88c66', '#e8b48e', '#ffd8b8', base=3)
THIEF = M('matte', '#0c0b10', '#18161e', '#26232e', '#373341', '#4b4657', '#625c70', base=3)
WRAP = M('cloth', '#1e1a16', '#332c24', '#4a4034', '#62574a', '#7c7062', '#968a7a', base=3)
WIZ = M('cloth', '#0a0a26', '#141450', '#20207a', '#3030a4', '#4848c8', '#6a70e4', base=3)
WIZ_D = M('cloth', '#08061c', '#100c3a', '#1a1460', '#262086', '#3830a8', '#5048c8', base=3)
SLEEVE = M('cloth', '#1a0828', '#30104a', '#4a1c6c', '#662c8e', '#8442ae', '#a660cc', base=3)
LACQ = M('metal', '#060508', '#0e0c12', '#18151e', '#24202c', '#363040', '#5a5268', '#a49ab4', base=3)
MAIL = M('matte', '#0c0c10', '#18181e', '#26262e', '#363640', '#4a4a56', '#62626e', base=2)
CORD = M('cloth', '#3a0408', '#600a12', '#8a121e', '#b41e2a', '#dc3a40', '#f4706a', base=3)
ICE = M('metal', '#0e2a4e', '#1b4a80', '#2e70b0', '#4f98d6', '#82c4f0', '#c4eaff', '#ffffff', base=3)
ICICLE = M('matte', '#2e70b0', '#5aa0dc', '#9ad0f4', '#d4f0ff', '#ffffff', base=2, edges=[(1, -1)])
EMBER = M('metal', '#0e0406', '#1e080a', '#34100e', '#4e1a14', '#6c2a1c', '#94422a', '#c86a3a', base=3)
FIRE = M('glow', '#8a1606', '#d8400c', '#ff8a1a', '#ffc83a', '#fff2a0')
SLATE = M('metal', '#0e1118', '#1a1f2c', '#2a3142', '#3e485e', '#56627c', '#7c8aa6', '#b4c2da', base=3)
CLOUD = M('cloth', '#1a1e2a', '#2c3242', '#424a5e', '#5c6680', '#7c87a2', '#a2adc4', base=3)
BOLT = M('glow', '#e89a00', '#ffd21a', '#fff27a', '#fffce0')
LEAF = M('matte', '#0c2a10', '#174a1a', '#24702a', '#3c9a38', '#68c44e', '#a8e67a', base=3)
LEAF2 = M('matte', '#123a14', '#1f5c20', '#348a2c', '#56b23e', '#8ad25e', '#c4f090', base=3)
LEAF3 = M('matte', '#2a4a10', '#46701a', '#6a9a28', '#90c03a', '#b8e060', '#e0f8a0', base=3)
BARK = M('matte', '#24140a', '#3e2614', '#5c3c20', '#7c5630', '#9c7244', '#bc9060', base=3)
SPACE = M('metal', '#05041a', '#0c0a30', '#16124c', '#221c6a', '#30288a', '#4a3cb0', '#8a7ae0', base=3)
SHADOW = M('matte', '#040306', '#0b0812', '#140e20', '#1e1530', '#3a2660', '#7a52c0', '#b090f0', base=2,
           edges=[(3, 0), (1, 0)], broad=0.6)
SMOKE = M('cloth', '#08060c', '#140e1e', '#221832', '#342448', '#4c3468', '#6e4c94', base=2,
          edges=[(2, 0)], broad=0.5)
VELVET = M('cloth', '#2a0410', '#4e081c', '#760e28', '#9e1834', '#c42a44', '#e4505e', base=3)
FUR = M('cloth', '#8a8478', '#b8b2a6', '#ddd8cc', '#f2eee4', '#ffffff', base=3)
PIRATE = M('matte', '#0e0908', '#1c1310', '#2c201a', '#3e2e24', '#544034', '#6c5444', base=3)
BURG = M('matte', '#24060a', '#420c12', '#62141c', '#842028', '#a63238', '#c44c4c', base=3)
SCALE = M('matte', '#06200e', '#0e3c1a', '#185c26', '#247e32', '#36a040', '#5cc456', '#9ae27c', base=3)
BELLY = M('matte', '#4a3a12', '#7a6424', '#a88c38', '#d0b250', '#ecd27a', '#fff0b0', base=3)
TALON = M('matte', '#3a3020', '#706246', '#a89a78', '#d8ccaa', '#f6eed8', '#ffffff', base=3)
SPIKE = M('matte', '#2a0606', '#4a0c0c', '#701814', '#962820', '#bc4030', '#de6a4a', base=3)
PEARL = M('metal', '#4a4a64', '#6e6e8a', '#9898b2', '#c0c0d6', '#e2e2f0', '#f6f6ff', '#ffffff', base=4)
FEATHER = M('cloth', '#4e5a74', '#7e8aa6', '#aab6ce', '#d2dcec', '#eef3fb', '#ffffff', base=4)
DEMON = M('matte', '#1a0204', '#32050a', '#520a10', '#781418', '#a02420', '#c83e28', base=3)
DEMON_D = M('matte', '#120203', '#240407', '#3a080c', '#561014', '#741c1a', '#963022', base=3)
CLAWK = M('metal', '#020102', '#0c0a0c', '#1a1619', '#2a2428', '#403840', '#6a6070', '#a89aa8', base=3)
HORN = M('matte', '#140e0c', '#2a201a', '#463628', '#64503a', '#86704e', '#a89070', base=3)

# small cabochons: (dark, base, light, highlight)
GEM_RED = ('#5e0819', '#c81e3c', '#ff7a90', '#ffffff')
GEM_GREEN = ('#063a20', '#139a52', '#62e49a', '#ffffff')
GEM_BLUE = ('#0c1e66', '#2456d8', '#7ab0ff', '#ffffff')
GEM_PURPLE = ('#3a0e5e', '#8a3ad0', '#c890ff', '#ffffff')
GEM_CYAN = ('#0c4a66', '#2aa8d8', '#9ae8ff', '#ffffff')
GEM_WHITE = ('#7aa8d0', '#d8f2ff', '#ffffff', '#ffffff')


# ------------------------------------------------------------------ designs (in shop order)
def d_leather(g):
    std_hand(g, LEATHER)
    g.add('cuff', s_cuff(g, 40.5, 52.0, flare=1.6, r=1.2), LEATHER_D, 3.0, seam='hard')
    g.render()
    back = g.mask('back')
    # three stitched seams on the back of the hand
    for (u0, u1) in ((4.0, 4.5), (10.0, 10.5), (16.0, 16.0)):
        g.hline(u0, 30.5, u1, 39.0, LEATHER.c(1), back)
    # cuff top stitching + strap with a brass buckle
    cuff = g.mask('cuff')
    for k, t in enumerate(np.linspace(-3.5, 24.0, 15)):
        if k % 2 == 0:
            g.hpx(t, 50.2, LEATHER.c(5), cuff)
    g.hsdf(inter(band(g.V, 43.2, 45.6), s_cuff(g, 40.5, 52.0, flare=1.6, r=1.2)), LEATHER_D.c(1), cuff)
    g.hline(-4.0, 43.6, 25.0, 43.6, LEATHER_D.c(3), cuff)
    bx, by = g.Pi(2.5, 44.4)
    for (dx, dy) in ((0, -1), (1, -1), (2, -1), (0, 0), (2, 0), (0, 1), (1, 1), (2, 1)):
        g.px(bx + dx, by + dy, '#f2c94c' if dy < 1 else '#a87a1c')
    g.px(bx + 1, by, '#4a2b17')
    return '#f2cf96'


def d_mitten(g):
    U, V = g.U, g.V
    pouch = sd_poly(U, V, [(-4.5, 25.0), (2.5, 20.5), (10.0, 18.0), (17.5, 19.5), (23.5, 23.5), (26.5, 29.0),
                           (24.5, 42.0), (-3.0, 42.0)], 3.0)
    g.add('back', pouch, WOOL, 6.0, seam=None)
    g.add('thb', sd_capsule(U, V, (-2.5, 39.0), (-9.5, 28.5), 5.0, 4.2), WOOL, 4.5, seam='hard')
    g.add('idx', sd_capsule(U, V, (0, 4.6), (0, 25.0), 4.6), WOOL, 4.6, seam='hard')
    g.add('cuff', s_cuff(g, 40.0, 53.0, w0=(-5.0, 24.5), flare=2.0, r=2.0), CREAM, 3.0, seam='hard')
    g.render()
    wool = g.mask('back', 'thb', 'idx')
    for y, x in zip(*np.nonzero(wool)):
        u, v = g.U[y, x], g.V[y, x]
        fu = (u / 2.6) % 1.0
        fv = (v / 2.3 + abs(fu - 0.5) * 0.9) % 1.0
        if fv < 0.28:
            g.a[y, x] = WOOL.c(g.idx[y, x] - 1)
    cuff = g.mask('cuff')
    for y, x in zip(*np.nonzero(cuff)):
        if (g.U[y, x] / 2.4) % 1.0 < 0.38 and g.V[y, x] > 41.5:
            g.a[y, x] = CREAM.c(g.idx[y, x] - 1)
    bm = (band(V, 31.0, 35.5) <= 0) & g.mask('back')
    g.recolor(bm, CREAM, 0)
    for t in np.arange(-2.0, 25.0, 3.4):
        g.hpx(t, 33.2, WOOL.c(3), bm)
    flake = sprite("""
        W.W.W
        .WWW.
        WW.WW
        .WWW.
        W.W.W""", {'W': CREAM.c(4)})
    g.blit_h(flake, 13.5, 25.6, g.mask('back'))
    return '#ffffff'


def d_iron(g):
    armor(g, IRON, tip='round', cuts=(8.5, 16.5), knuck=False, cuff=(40.0, 53.0, 3.0), rim_band=2.6, cuff_mat=IRON_D,
          extra_back=lambda: g.add('lame', inter(s_back(g), band(g.V, 33.0, 50.0)), IRON, 3.0, seam='dark'))
    g.render()
    g.studs(-0.5, 27.6, 21.5, 30.4, 4, IRON.c(6), IRON.c(0), g.mask('back'))
    g.studs(-1.0, 35.2, 21.0, 36.2, 4, IRON.c(6), IRON.c(0), g.mask('lame'))
    g.studs(-2.5, 44.5, 22.0, 44.5, 5, IRON.c(6), IRON.c(0), g.mask('cuff'))
    rust = ['#5a2a12', '#86401c', '#a85a2a']
    for (u, v, c) in ((19.0, 38.5, 1), (20.0, 39.5, 0), (-1.0, 47.0, 1), (14.0, 49.5, 2), (3.0, 31.0, 0),
                      (24.0, 47.0, 1), (-6.0, 34.0, 1)):
        g.hpx(u, v, rust[c], g.mask('back', 'lame', 'cuff', 'thb*'))
    return '#a9bdd0'


def d_bronze(g):
    armor(g, BRONZE, tip='round', cuts=(10.0,), knuck=False, cuff=(40.0, 55.0, 0.8), rim_band=3.4)
    g.add('boss', sd_circle(g.U, g.V, 10.5, 34.0, 6.0), BRONZE, 3.2, seam='dark')   # round boss
    g.render()
    cx, cy = g.P(10.5, 34.0)
    g.circle(cx, cy, 3.6, BRONZE.c(1), g.mask('boss'), ring=True)
    g.circle(cx - 0.3, cy - 0.3, 1.6, BRONZE.c(5), g.mask('boss'))
    g.px(math.floor(cx) - 1, math.floor(cy) - 1, BRONZE.c(6))
    cuff = g.mask('cuff')
    g.hline(-4.0, 44.0, 24.0, 44.0, BRONZE.c(1), cuff)
    g.hline(-4.0, 48.6, 24.0, 48.6, BRONZE.c(1), cuff)
    for t in np.arange(-2.0, 24.0, 3.6):
        g.rivet(t, 46.3, BRONZE.c(6), BRONZE.c(1), cuff)
    for (u, v) in ((-3.0, 41.0), (5.0, 40.3), (12.0, 40.5), (20.0, 40.6), (-5.0, 52.0), (23.0, 52.0),
                   (3.0, 10.0), (2.5, 11.0), (-4.0, 29.0), (24.0, 30.0), (16.0, 39.0), (6.0, 39.5)):
        x, y = g.Pi(u, v)
        if 0 <= x < N and 0 <= y < N and g.lab[y, x]:
            g.px(x, y, PATINA[1])
            g.px(x + 1, y, PATINA[2], g.lab > 0)
    return '#ffab4f'


def d_silver(g):
    U, V = g.U, g.V
    # gothic armour: fluted plates, long cuff ending in a point
    armor(g, SILVER, tip='pointed', cuts=(7.5, 14.0, 20.5), cuff=(40.0, 52.0, 3.0), rim_band=0)
    g.add('cuff2', sd_poly(U, V, [(-7.0, 50.5), (26.0, 50.5), (19.0, 58.5), (13.0, 62.0), (6.0, 58.5)], 1.0),
          SILVER, 3.0, seam='dark')
    g.render()
    bk = g.mask('back')
    for (u0, u1) in ((0.5, 2.5), (6.5, 7.5), (12.5, 12.5), (18.5, 17.0)):
        g.hline(u0, 29.5, u1, 40.5, SILVER.c(1), bk)
        g.hline(u0 - 1.1, 29.5, u1 - 1.1, 40.5, SILVER.c(6), bk)
    fm = g.mask('idx*')
    g.hline(0.2, 3.0, 0.2, 27.0, SILVER.c(1), fm)
    g.hline(-0.9, 3.0, -0.9, 27.0, SILVER.c(6), fm)
    cm = g.mask('cuff', 'cuff2')
    moon = (sd_circle(U, V, 10.0, 47.5, 4.0) <= 0) & (sd_circle(U, V, 11.8, 46.2, 3.4) > 0)
    g.fill(moon & cm, SILVER.c(1))
    x, y = g.P(13.0, 57.5)
    g.gem(x, y, 2.0, 2.0, GEM_PURPLE)
    return '#cfeeff'


def d_golden(g):
    armor(g, GOLD, tip='pointed', cuts=(8.0, 15.5, 21.5), cuff=(40.5, 54.5, 5.5), rim_band=2.6)
    g.render()
    cx, cy = g.P(10.5, 36.0)
    bm = g.mask('back')
    for k in range(8):
        a = k * math.pi / 4 + math.radians(ANGLE)
        g.line(cx + 3.2 * math.cos(a), cy + 3.2 * math.sin(a), cx + 4.8 * math.cos(a), cy + 4.8 * math.sin(a), GOLD.c(1), bm)
    g.circle(cx, cy, 2.9, GOLD.c(1), bm)
    g.circle(cx, cy, 2.1, GOLD.c(5), bm)
    g.px(math.floor(cx) - 1, math.floor(cy) - 1, GOLD.c(6), bm)
    for t in (2.0, 9.0, 16.0):
        x, y = g.P(t, 27.4 + t * 0.09)
        g.gem(x, y, 1.6, 1.5, GEM_GREEN)
    cuff = g.mask('cuff')
    g.hline(-5.0, 44.5, 25.0, 44.5, GOLD.c(1), cuff)
    x, y = g.P(9.5, 49.0)
    g.circle(x, y, 3.2, GOLD.c(0), cuff)
    g.gem(x, y, 2.4, 2.4, GEM_GREEN)
    return '#ffb640'


def d_crystal(g):
    armor(g, CRYSTAL, tip='pointed', cuts=(9.0, 17.0), knuck=False, cuff=(40.0, 53.0, 4.0), rim_band=0,
          seam=CRYSTAL.c(1))
    shards = ((16.5, 29.5, 0.42, -1.0, 9.5, 4.8), (20.5, 33.0, 1.0, -0.8, 13.5, 5.8), (22.0, 39.0, 1.0, -0.22, 10.0, 5.0),
              (-6.5, 47.0, -1.0, 0.25, 7.0, 4.2))
    for k, (u0, v0, du, dv, L, w) in enumerate(shards):
        g.add('shard%d' % k, s_shard(g, u0, v0, du, dv, L, w), CRYSTAL_S, 1.6, seam='dark')
    g.render()
    for k, (u0, v0, du, dv, L, w) in enumerate(shards):
        split_shade(g, 'shard%d' % k, (u0, v0), (du, dv), CRYSTAL_S)
    g.accent(spark('#e6dcff', small=True), *g.Pi(-7.5, 12.0))
    g.accent(spark('#ffffff', small=True), *g.Pi(33.0, 18.0))
    return '#d8bcff'


def d_ruby(g):
    U, V = g.U, g.V
    seam = GOLD.c(4)
    g.add('back', s_back(g), RUBY, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        g.add(nm, s_curl(g, 2 - k), RUBY, 3.0, seam=seam)
    g.add('thb', s_thumb(g), RUBY, 3.6, seam=seam)
    plated_idx(g, RUBY, cuts=(9.0, 17.5), seam=seam)
    g.add('cuff', s_cuff(g, 41.5, 53.0, flare=4.2), GOLD, 4.0, seam='dark')
    g.add('crim', inter(s_cuff(g, 41.5, 54.2, flare=4.65), band(V, 50.6, 56.0)), GOLD, 1.6, seam='dark')
    for t in np.linspace(-3.0, 22.0, 5):
        g.add('prong', s_spike(g, t, 42.6, 0.0, -1.0, 5.6, 5.2), GOLD, 1.4, seam='dark')
    g.add('bezel', sd_ellipse(U, V, 10.5, 33.5, 6.0, 4.9), GOLD, 2.0, seam='dark')
    g.add('cab', sd_ellipse(U, V, 10.5, 33.5, 4.3, 3.2), RUBY, 3.0, seam=RUBY.c(0))
    g.render()
    for t in np.linspace(-3.0, 22.0, 5):
        x, y = g.P(t, 37.6)
        g.px(math.floor(x), math.floor(y), '#ff4a64')
    for t in (1.0, 10.0, 19.0):
        x, y = g.P(t, 47.2)
        g.gem(x, y, 1.7, 1.7, GEM_RED)
    x, y = g.P(8.8, 32.3)
    g.px(x, y, '#ffffff')
    g.px(x + 1, y, RUBY.c(5))
    return '#ff5a7a'


def d_emerald(g):
    U, V = g.U, g.V
    seam = SILVER.c(5)
    g.add('back', s_back(g), EMERALD, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        g.add(nm, s_curl(g, 2 - k), EMERALD, 3.0, seam=seam)
    g.add('thb', s_thumb(g), EMERALD, 3.6, seam=seam)
    plated_idx(g, EMERALD, cuts=(8.5, 16.5), tip='round', seam=seam)
    g.add('cuff', sd_poly(U, V, [(-4.0, 40.0), (23.0, 40.0), (27.0, 48.5), (24.0, 53.5), (-5.0, 53.5), (-8.0, 48.5)], 1.0),
          SILVER, 4.0, seam='dark')
    g.add('bezel', sd_poly(U, V, [(4.0, 30.0), (17.0, 31.0), (16.5, 38.5), (3.5, 37.5)], 1.6), SILVER, 2.0, seam='dark')
    g.add('cut', sd_poly(U, V, [(5.5, 31.4), (15.5, 32.2), (15.0, 37.2), (5.0, 36.4)], 0.8), EMERALD, 2.4, seam=EMERALD.c(0))
    for k, t in enumerate((-1.5, 9.5, 20.5)):
        g.add('ecut%d' % k, sd_poly(U, V, [(t - 3.0, 45.0), (t + 3.0, 45.0), (t + 3.0, 49.5), (t - 3.0, 49.5)], 0.6),
              EMERALD, 1.5, seam=EMERALD.c(0))
    g.render()
    cm = g.mask('cut')
    g.hline(6.5, 33.4, 14.5, 34.1, EMERALD.c(5), cm)
    g.hline(6.3, 35.6, 14.3, 36.2, EMERALD.c(2), cm)
    for k, t in enumerate((-1.5, 9.5, 20.5)):
        m = g.mask('ecut%d' % k)
        g.hline(t - 2.0, 46.4, t + 2.0, 46.4, EMERALD.c(5), m)
    g.accent(spark('#c8ffe0', small=True), *g.Pi(-7.0, 9.0))
    return '#5aff9a'


def d_sapphire(g):
    U, V = g.U, g.V
    seam = PLAT.c(5)
    g.add('back', s_back(g), SAPPHIRE, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        g.add(nm, s_curl(g, 2 - k), SAPPHIRE, 3.0, seam=seam)
    g.add('thb', s_thumb(g), SAPPHIRE, 3.6, seam=seam)
    plated_idx(g, SAPPHIRE, cuts=(8.0, 15.5, 21.5), seam=seam)
    pts = [(-4.0, 40.0), (23.0, 40.0)]
    for t in np.linspace(0, 1, 13):
        u = 28.0 - 37.0 * t
        pts.append((u, 53.0 + 1.6 * math.sin(t * math.pi * 4)))
    g.add('cuff', sd_poly(U, V, pts, 1.0), PLAT, 4.0, seam='dark')
    g.add('bezel', sd_circle(U, V, 10.5, 34.5, 6.2), PLAT, 2.0, seam='dark')
    g.add('star', sd_circle(U, V, 10.5, 34.5, 4.6), SAPPHIRE, 3.0, seam=SAPPHIRE.c(0))
    g.render()
    cx, cy = g.P(10.5, 34.5)
    sm = g.mask('star')
    for ang in (0, 60, 120):
        a = math.radians(ang)
        g.line(cx - 3 * math.cos(a), cy - 3 * math.sin(a), cx + 3 * math.cos(a), cy + 3 * math.sin(a), SAPPHIRE.c(5), sm)
    g.px(math.floor(cx), math.floor(cy), '#ffffff')
    cuff = g.mask('cuff')
    for t in (-1.0, 9.5, 20.0):
        x, y = g.P(t, 46.0)
        g.gem(x, y, 1.6, 1.6, GEM_BLUE)
    return '#5ab4ff'


def d_obsidian(g):
    armor(g, OBSID, tip='pointed', cuts=(7.5, 14.5, 21.0), knuck=False, cuff=(40.0, 52.0, 5.0), rim_band=0)
    for (u0, v0, du, dv, L, w) in ((8.6, 20.5, 0.15, -1.0, 6.0, 3.8), (15.6, 22.5, 0.35, -1.0, 5.5, 3.6),
                                   (21.8, 26.0, 0.7, -1.0, 5.0, 3.4), (24.5, 34.0, 1.0, -0.25, 5.0, 3.8),
                                   (24.0, 43.0, 1.0, -0.1, 4.6, 3.6)):
        g.add('spk', s_spike(g, u0, v0, du, dv, L, w), OBSID, 1.5, seam='dark')
    for t in np.linspace(-7.5, 26.5, 6):
        g.add('tooth', s_spike(g, t, 51.0, 0.25, 1.0, 4.6, 5.8), OBSID, 1.5, seam='dark')
    g.render()
    for (u0, v0, u1, v1) in ((-2.0, 3.0, -2.0, 7.0), (-2.2, 10.0, -2.2, 13.0), (3.0, 30.0, 8.0, 27.5),
                             (-3.0, 44.0, 2.0, 42.0), (14.0, 47.0, 19.0, 44.5)):
        g.hline(u0, v0, u1, v1, '#ffffff', g.lab > 0)
    return '#e2dcf2'


def d_bone(g):
    U, V = g.U, g.V
    g.add('arm1', sd_capsule(U, V, (2.5, 46.5), (3.0, 60.0), 2.8, 2.4), BONE, 2.6, seam='hard')
    g.add('arm2', sd_capsule(U, V, (16.5, 46.5), (17.5, 60.0), 2.8, 2.4), BONE, 2.6, seam='hard')
    for (cu, cv, r) in ((1.5, 41.5, 2.4), (6.5, 42.5, 2.4), (11.5, 42.5, 2.4), (16.5, 41.5, 2.4), (4.0, 45.0, 2.2),
                        (9.0, 45.5, 2.2), (14.0, 45.0, 2.2)):
        g.add('carp', sd_circle(U, V, cu, cv, r), BONE, 2.2, seam='hard')
    for (u0, u1, r) in ((0.0, 3.5, 2.4), (8.6, 8.0, 2.3), (15.6, 12.5, 2.2), (21.6, 16.5, 2.1)):
        g.add('meta', sd_capsule(U, V, (u0, 26.5), (u1, 39.0), r), BONE, 2.0, seam='hard')
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        u, v0, v1, r = CURL[2 - k]
        g.add(nm, sd_capsule(U, V, (u, v0 - 0.8), (u, v0 + 3.2), r * 0.8), BONE, 2.5, seam='hard')
        g.add(nm + 'k', sd_circle(U, V, u, v0 + 4.0, r * 0.62), BONE, 2.0, seam='hard')
    g.add('thb1', sd_capsule(U, V, (-1.5, 39.0), (-5.5, 33.0), 2.5), BONE, 2.3, seam='hard')
    g.add('thb2', sd_capsule(U, V, (-6.5, 30.5), (-9.0, 26.0), 2.4), BONE, 2.2, seam='hard')
    g.add('idx3', sd_capsule(U, V, (0, 17.5), (0, 23.8), 3.1), BONE, 3.0, seam='hard')
    g.add('idx2', sd_capsule(U, V, (0, 10.2), (0, 15.2), 2.9), BONE, 2.8, seam='hard')
    g.add('idx', sd_capsule(U, V, (0, 2.8), (0, 8.0), 2.7), BONE, 2.6, seam='hard')
    g.pointer = 'idx'
    g.render()
    return '#9cff5a'


def d_thief(g):
    U, V = g.U, g.V
    std_hand(g, THIEF, seam='hard')
    g.add('idxskin', inter(s_idx(g), band(V, -6.0, 8.8)), SKIN_T, IDX_R, seam='hard')
    for k in range(3):
        u, v0, v1, r = CURL[k]
        g.add('cskin%d' % k, inter(s_curl(g, k), band(V, -6.0, v0 - 0.4)), SKIN_T, r, seam='hard')
    g.pointer = 'idxskin'
    g.add('cuff', s_cuff(g, 40.0, 54.0, flare=0.8, r=1.5), WRAP, 3.0, seam='hard')
    g.add('coin', sd_circle(U, V, -11.0, 27.0, 3.0), GOLD, 1.8, seam='dark')
    g.render()
    cuff = g.mask('cuff')
    for t in np.arange(-10.0, 26.0, 3.2):
        g.hline(t, 40.5, t + 7.0, 54.0, WRAP.c(1), cuff)
    # strap with a silver buckle across the back of the hand
    bk = g.mask('back')
    g.hsdf(inter(band(V, 32.5, 35.0), s_back(g)), '#2e1c12', bk)
    g.hline(-6.0, 32.6, 27.0, 32.6, '#4a3020', bk)
    bx, by = g.Pi(12.5, 33.5)
    for (dx, dy) in ((0, -1), (1, -1), (2, -1), (0, 0), (2, 0), (0, 1), (1, 1), (2, 1)):
        g.px(bx + dx, by + dy, '#d8dce6' if dy < 1 else '#7a8090')
    cm = g.mask('coin')
    x, y = g.P(-11.0, 27.0)
    g.px(math.floor(x), math.floor(y), GOLD.c(1), cm)
    return '#5af0c8'


def d_wizard(g):
    U, V = g.U, g.V
    std_hand(g, WIZ, seam='hard')
    g.add('cuff', s_cuff(g, 40.0, 51.0, flare=5.0), WIZ_D, 4.0, seam='hard')
    for t in np.linspace(-7.5, 26.5, 5):
        g.add('point', s_spike(g, t, 50.0, 0.0, 1.0, 6.0, 7.0), WIZ_D, 2.0, seam='hard')
    g.add('trim', inter(s_cuff(g, 39.2, 51.0, flare=5.2), band(V, 38.0, 41.6)), GOLD, 1.5, seam='dark')
    g.add('ring', inter(sd_capsule(U, V, (0, 4.2), (0, 27.0), IDX_R + 0.4), band(V, 18.6, 21.0)), GOLD, 1.2, seam='dark')
    g.render()
    x, y = g.P(0.0, 19.8)
    g.gem(x, y, 1.6, 1.6, GEM_PURPLE)
    bk = g.mask('back')
    moon = sprite("""
        ..YYY
        .YY..
        YY...
        YY...
        YY...
        .YY..
        ..YYY""", {'Y': '#ffd84a'})
    g.blit_h(moon, 7.5, 34.0, bk)
    star = sprite("""
        ..Y..
        .YYY.
        YYYYY
        .Y.Y.""", {'Y': '#ffe680'})
    g.blit_h(star, 15.0, 31.5, bk)
    for (u, v) in ((3.0, 28.5), (18.5, 37.5), (12.0, 39.0), (-1.0, 9.0), (20.5, 29.5)):
        g.hpx(u, v, '#ffe680', g.mask('back', 'idx', 'cuff'))
    for t in np.linspace(-5.0, 24.0, 4):
        g.hpx(t, 46.0, '#ffd84a', g.mask('cuff'))
    g.accent(spark('#c8a0ff'), *g.Pi(-8.5, 8.0))
    return '#ffe066'


def d_fortune(g):
    U, V = g.U, g.V
    std_hand(g, SKIN, seam=SKIN.c(1))
    g.add('wrist', s_cuff(g, 38.0, 48.0, flare=0.0, r=2.0), SKIN, 3.0, seam=None)
    for (a, b) in ((40.0, 42.6), (43.3, 45.9)):
        g.add('bangle', inter(s_cuff(g, 38.0, 48.0, flare=0.0, r=2.8), band(V, a, b)), GOLD, 1.2, seam=GOLD.c(1))
    g.add('sleeve', s_cuff(g, 47.0, 57.5, w0=(-5.5, 24.5), flare=4.0), SLEEVE, 4.0, seam='dark')
    g.add('lace', union(*[sd_circle(U, V, t, 47.8, 2.5) for t in np.linspace(-6.5, 25.5, 8)]), CREAM, 1.5,
          seam=CREAM.c(1))
    g.render()
    im = g.mask('idx')
    for y, x in zip(*np.nonzero(im)):
        if g.V[y, x] < 3.4:
            g.a[y, x] = hexc(['#4a1060', '#7a28a0', '#a850cc', '#d088ec'][min(3, max(0, g.idx[y, x] - 1))])
    for (u, v, r, gem) in ((0.0, 19.5, IDX_R + 0.35, GEM_RED), (8.6, 22.6, 4.3, GEM_GREEN)):
        m = (inter(sd_capsule(U, V, (u, 0), (u, 30), r), band(V, v - 0.9, v + 0.9)) <= 0) & g.mask('idx', 'mid')
        g.fill(m, GOLD.c(4))
        x, y = g.P(u, v)
        g.gem(x, y, 1.5, 1.5, gem)
    eye = sprite("""
        ..PPP..
        .PWWWP.
        PWpkpWP
        .PWWWP.
        ..PPP..""", {'P': '#4a145e', 'W': '#f6eefc', 'p': '#8a3ad0', 'k': '#16061e'})
    g.blit_h(eye, 11.0, 33.0, g.mask('back'))
    lm = g.mask('lace')
    for t in np.linspace(-6.5, 25.5, 8):
        g.hpx(t, 48.6, CREAM.c(1), lm)
    sl = g.mask('sleeve')
    g.hline(-8.0, 52.0, 28.0, 52.0, GOLD.c(4), sl)
    for t in np.arange(-6.0, 27.0, 4.0):
        g.hpx(t, 54.6, GOLD.c(5), sl)
    return '#ff8ae0'


def d_knight(g):
    armor(g, STEEL, tip='pointed', cuts=(7.5, 14.5, 21.0), knuck=True, cuff=(40.0, 55.0, 7.0), rim_band=2.6,
          rim_mat=BRASS, seam='dark')
    g.render()
    shield = sprite("""
        kkkkkkk
        kWWRWWk
        kWWRWWk
        kRRRRRk
        kWWRWWk
        .kWRWk.
        ..kRk..
        ...k...""", {'k': OUTLINE, 'W': '#f4f4f8', 'R': '#d8202a'})
    g.blit_h(shield, 10.0, 47.5, g.mask('cuff'))
    g.studs(-6.0, 43.0, 26.0, 43.0, 6, BRASS.c(5), BRASS.c(1), g.mask('cuff'))
    g.studs(-1.0, 27.0, 21.0, 29.6, 4, BRASS.c(5), BRASS.c(1), g.mask('knuck'))
    return '#ff6464'


def d_samurai(g):
    U, V = g.U, g.V
    red = CORD.c(2)
    g.add('back', s_back(g), LACQ, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        g.add(nm, s_curl(g, 2 - k), LACQ, 3.0, seam=red)
    g.add('thb', s_thumb(g), LACQ, 3.6, seam=red)
    plated_idx(g, LACQ, cuts=(6.5, 12.5, 18.5), tip='round', seam=red, grow=0.25)
    g.add('tekko', sd_poly(U, V, [(-3.0, 27.5), (23.5, 30.5), (22.0, 41.0), (-2.0, 41.0)], 1.5), LACQ, 3.0, seam=red)
    g.add('cuff', s_cuff(g, 40.5, 56.0, flare=2.0, r=1.5), MAIL, 2.5, seam='dark')
    g.add('cord', inter(s_cuff(g, 40.5, 56.0, flare=2.2), band(V, 40.0, 42.6)), CORD, 1.5, seam='dark')
    g.render()
    cx, cy = g.P(10.5, 35.0)
    tm = g.mask('tekko')
    g.circle(cx, cy, 3.8, '#e8b030', tm, ring=True)
    g.line(cx - 2.6, cy, cx + 2.6, cy, '#ffd860', tm)
    g.line(cx, cy - 2.6, cx, cy + 2.6, '#ffd860', tm)
    cm = g.mask('cuff')
    for y, x in zip(*np.nonzero(cm)):
        if (x + 2 * y) % 4 == 0 and y % 2 == 0:
            g.a[y, x] = MAIL.c(g.idx[y, x] + 2)
    return '#ff4a3a'


def d_frost(g):
    armor(g, ICE, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=False, cuff=(40.0, 52.5, 4.5), rim_band=2.4,
          seam=ICE.c(0))
    for (u, w, h) in ((-6.0, 2.6, 7.0), (2.5, 2.2, 5.0), (10.0, 2.6, 8.0), (18.0, 2.2, 5.5), (25.0, 2.4, 6.5)):
        x, y = g.P(u, 53.6)
        g.add('icicle', x_icicle(x - w / 2, y, w, h), ICICLE, 1.0, seam=None)
    g.render()
    # frost on the lit upper edges
    for y, x in zip(*np.nonzero(g.lab > 0)):
        p = g.parts[g.lab[y, x] - 1]
        if p['mat'] is ICE and hash2(x, y, 7) < 0.35 and g.idx[y, x] >= 5:
            g.a[y, x] = hexc('#ffffff')
    flake = sprite("""
        ...W...
        .W.W.W.
        ..WWW..
        WWWwWWW
        ..WWW..
        .W.W.W.
        ...W...""", {'W': '#e8fbff', 'w': '#ffffff'})
    g.accent(flake, 54, 4)
    g.accent(spark('#e8fbff', small=True), 4, 50)
    return '#e0fbff'


def d_flame(g):
    armor(g, EMBER, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=False, cuff=(40.0, 53.0, 4.5), rim_band=2.4)
    fl = []
    for (u, v, r, h, lean) in ((22.5, 27.0, 2.8, 9.0, 1.5), (16.0, 23.5, 3.0, 11.5, 0.8), (9.0, 21.0, 3.1, 12.5, -0.6),
                               (25.0, 37.0, 2.8, 9.5, 1.8), (26.5, 47.5, 2.8, 9.0, 2.0)):
        x, y = g.P(u, v)
        main = x_flame(x, y, r, h, lean)
        side = x_flame(x + r * 0.75, y + 0.5, r * 0.55, h * 0.55, lean + 1.0)
        fl.append(np.minimum(main, side))
    for k, sd in enumerate(fl):
        g.add('flame%d' % k, sd, FIRE, 2.0, seam=FIRE.c(0), shadow=False, form=False)
    g.render()
    cm = g.mask('back', 'cuff')
    for (u0, v0, u1, v1) in ((2.0, 31.0, 6.5, 34.5), (6.5, 34.5, 5.0, 39.0), (12.0, 30.5, 15.5, 34.5), (15.5, 34.5, 20.5, 36.0),
                             (0.0, 44.5, 6.0, 47.5), (6.0, 47.5, 12.0, 45.0), (15.0, 48.0, 21.0, 50.0)):
        g.hline(u0, v0, u1, v1, '#ff7a1a', cm)
    for (u, v) in ((6.5, 34.5), (15.5, 34.5), (6.0, 47.5)):
        g.hpx(u, v, '#ffd040', cm)
    g.accent(sprite("o", {'o': '#ffc040'}), *g.Pi(4.0, 15.0))
    g.accent(sprite("o", {'o': '#ff9a2a'}), *g.Pi(33.0, 31.0))
    return '#ffa030'


def d_storm(g):
    U, V = g.U, g.V
    armor(g, SLATE, tip='pointed', cuts=(8.0, 16.0), knuck=False, cuff=(40.0, 50.0, 1.0), rim_band=0)
    cl = union(*[sd_circle(U, V, u, v, r) for (u, v, r) in ((-5.0, 47.0, 4.6), (1.5, 50.5, 5.2), (9.5, 51.5, 5.4),
                                                            (17.0, 50.5, 5.2), (24.0, 47.5, 4.8), (10.0, 45.5, 6.0),
                                                            (20.5, 44.0, 4.4), (-1.0, 44.0, 4.4))])
    g.add('cloud', cl, CLOUD, 4.0, seam='dark')
    bolt = [(0, 0), (6.5, 0), (4.0, 4.6), (8.5, 4.6), (0.0, 15.0), (2.4, 7.4), (-2.2, 7.4)]
    bx, by = g.P(9.5, 32.0)
    g.add('bolt', x_poly([(bx + px_ - 3.0, by + py - 7.5) for (px_, py) in bolt]), BOLT, 1.0, seam='dark', form=False)
    lx, ly = g.P(4.0, 55.0)
    zig = [(0, 0), (3.4, 0), (1.2, 3.8), (4.0, 3.8), (-2.6, 11.0), (-0.6, 5.6), (-3.0, 5.6)]
    g.add('zap', x_poly([(lx + px_ - 1.0, ly + py) for (px_, py) in zig]), BOLT, 1.0, seam='dark', form=False)
    g.render()
    g.accent(sprite("o", {'o': '#8af0ff'}), *g.Pi(-6.5, 6.0))
    g.accent(sprite("o", {'o': '#8af0ff'}), *g.Pi(6.5, 13.0))
    return '#7ae6ff'


def d_nature(g):
    U, V = g.U, g.V
    collar = ((-6.5, 46.0, -0.75, 1.0, 10.0, 6.0), (0.5, 47.5, -0.3, 1.0, 10.5, 6.2), (8.5, 48.0, 0.0, 1.0, 10.5, 6.2),
              (16.5, 47.5, 0.3, 1.0, 10.0, 6.0), (23.5, 45.5, 0.8, 1.0, 9.0, 5.6))
    for k, (u0, v0, du, dv, L, w) in enumerate(collar):
        g.add('collar%d' % k, s_leaf(U, V, u0, v0, du, dv, L, w), LEAF2 if k % 2 == 0 else LEAF3, 2.0, seam='hard')
    sprig = ((3.6, 8.5, 1.0, -0.55, 6.5, 3.6), (-3.6, 15.5, -1.0, -0.3, 6.0, 3.4))
    for k, (u0, v0, du, dv, L, w) in enumerate(sprig):
        g.add('sprig%d' % k, s_leaf(U, V, u0, v0, du, dv, L, w), LEAF3, 1.5, seam='hard')
    std_hand(g, LEAF, seam='hard')
    g.add('cuff', s_cuff(g, 40.5, 48.5, flare=1.0, r=1.5), BARK, 3.0, seam='hard')
    g.render()
    for k, (u0, v0, du, dv, L, w) in enumerate(collar + sprig):
        n = math.hypot(du, dv)
        nm = ('collar%d' % k) if k < len(collar) else ('sprig%d' % (k - len(collar)))
        g.hline(u0 + du / n * 1.0, v0 + dv / n * 1.0, u0 + du / n * L * 0.78, v0 + dv / n * L * 0.78, LEAF2.c(1), g.mask(nm))
    vm = g.mask('idx')
    for v in (5.0, 12.0, 19.0):
        g.hline(-4.5, v + 2.5, 4.5, v, BARK.c(2), vm)
        g.hline(-4.5, v + 3.5, 4.5, v + 1.0, BARK.c(4), vm)
    cm = g.mask('cuff')
    for t in np.arange(-6.0, 26.0, 3.5):
        g.hline(t, 41.0, t + 2.5, 48.5, BARK.c(1), cm)
    flower = sprite("""
        ..P.P..
        .PPpPP.
        PPpYpPP
        .ppYYp.
        PPpYpPP
        .PPpPP.
        ..P.P..""", {'P': '#ffb4d6', 'p': '#e8609e', 'Y': '#ffe040'})
    g.blit_h(outlined(flower, '#3a0e24'), 12.0, 33.5, g.mask('back'))
    return '#c0ff60'


def d_cosmic(g):
    U, V = g.U, g.V
    armor(g, SPACE, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=False, cuff=(40.0, 53.0, 5.0), rim_band=2.4,
          rim_mat=GOLD)
    g.render()
    body = (g.lab > 0) & ~g.mask('crim')
    for y, x in zip(*np.nonzero(body)):
        u, v = g.U[y, x], g.V[y, x]
        n = (math.sin(u * 0.45 + v * 0.2) + math.sin(v * 0.33 - u * 0.21 + 1.3)) * 0.5
        if n > 0.55 and g.idx[y, x] >= 2:
            g.a[y, x] = hexc('#8a3aa8' if (x + y) % 2 == 0 or n > 0.75 else g.a[y, x])
        elif n < -0.6 and g.idx[y, x] >= 2:
            g.a[y, x] = hexc('#1e6a8a' if (x + y) % 2 == 0 or n < -0.8 else g.a[y, x])
    for y, x in zip(*np.nonzero(body)):
        if hash2(x, y, 3) < 0.045:
            g.a[y, x] = hexc('#ffffff' if hash2(x, y, 4) < 0.6 else '#ffe680')
    cx, cy = g.P(10.5, 34.0)
    bm = g.mask('back')
    g.circle(cx, cy, 3.6, '#e88a3a', bm)
    g.circle(cx - 0.8, cy - 0.8, 1.8, '#ffc070', bm)
    g.line(cx - 6, cy + 2, cx + 6, cy - 2, '#ffe6a0', bm)
    g.accent(spark('#ffe680', small=True), *g.Pi(-8.0, 6.0))
    g.accent(spark('#ffffff'), *g.Pi(30.0, 22.0))
    return '#ff70e0'


def d_shadow(g):
    U, V = g.U, g.V
    wisps = (([(2.5, 46.0), (6.5, 50.5), (4.0, 55.0), (7.5, 58.5), (10.5, 57.0)], 2.6),
             ([(15.5, 46.0), (20.5, 49.0), (19.0, 53.5), (23.5, 55.0), (25.0, 52.5)], 2.4),
             ([(-3.0, 44.5), (-7.5, 47.0), (-6.0, 51.5), (-10.0, 53.5), (-12.0, 51.0)], 2.2))
    for (pts, r0) in wisps:
        g.add('wisp', sd_path(U, V, pts, r0, 0.35), SMOKE, 2.0, seam=None)
    for (u, v, r) in ((11.5, 55.5, 1.4), (27.5, 49.5, 1.2), (-12.5, 47.0, 1.1)):
        g.add('puff', sd_circle(U, V, u, v, r), SMOKE, 1.0, seam=None)
    std_hand(g, SHADOW, tip='pointed', seam=SHADOW.c(4))
    g.add('cuff', s_cuff(g, 40.0, 49.0, flare=1.5, r=2.0), SHADOW, 3.0, seam=SHADOW.c(4))
    g.render()
    for (u, v) in ((6.0, 33.0), (13.5, 34.0)):
        x, y = g.Pi(u, v)
        for (dx, dy, c) in ((0, 0, '#ffffff'), (1, 0, '#d8c0ff'), (-1, 0, '#9a6ae0'), (0, 1, '#9a6ae0'), (1, 1, '#7a4ac0')):
            g.px(x + dx, y + dy, c)
    return '#b48aff'


def d_royal(g):
    U, V = g.U, g.V
    std_hand(g, VELVET, seam='hard')
    g.add('ring', inter(sd_capsule(U, V, (0, 4.2), (0, 27.0), IDX_R + 0.4), band(V, 18.6, 21.0)), GOLD, 1.2, seam='dark')
    g.add('cuff', s_cuff(g, 39.0, 53.0, flare=3.0, r=3.4), FUR, 4.0, seam='hard')
    g.render()
    x, y = g.P(0.0, 19.8)
    g.gem(x, y, 1.6, 1.6, GEM_BLUE)
    crown = sprite("""
        R...B...R
        Y..YYY..Y
        YY.YYY.YY
        YYYYYYYYY
        YRYYBYYRY
        yyyyyyyyy""", {'y': '#b07a10', 'Y': '#ffd23a', 'R': '#ff4a5a', 'B': '#6aa8ff'})
    g.blit_h(outlined(crown, '#2a0408'), 11.5, 31.0, g.mask('back', 'mid', 'rng'))
    cm = g.mask('cuff')
    tuft = sprite("""
        .k.
        kkk
        .k.""", {'k': '#141018'})
    for (u, v) in ((-3.0, 43.5), (6.0, 44.0), (15.0, 44.0), (22.5, 43.5), (1.5, 49.0), (10.5, 49.5), (19.5, 49.0)):
        g.blit_h(tuft, u, v, cm)
    return '#ffd23a'


def d_clockwork(g):
    U, V = g.U, g.V
    g.add('key', sd_capsule(U, V, (22.0, 35.0), (29.5, 31.5), 1.4), STEEL, 1.4, seam='dark')
    g.add('keybow', union(sd_circle(U, V, 31.5, 33.5, 2.6), sd_circle(U, V, 30.0, 28.5, 2.6)), STEEL, 2.0, seam='dark')
    armor(g, BRASS, tip='round', cuts=(8.5, 16.5), knuck=False, cuff=(40.0, 53.0, 3.5), rim_band=2.4,
          cuff_mat=COPPER, rim_mat=BRASS)
    cx, cy = g.P(9.5, 34.0)
    g.add('gear', x_gear(cx, cy, 5.6, teeth=8, th=1.8, phase=0.2), STEEL, 2.0, seam='dark', form=False)
    g.add('hub', sd_circle(XC, YC, cx, cy, 2.4), BRASS, 1.5, seam='dark', form=False)
    hx, hy = g.P(17.5, 29.5)
    g.add('gear3', x_gear(hx, hy, 2.8, teeth=6, th=1.4, phase=0.5), COPPER, 1.5, seam='dark', form=False)
    gx, gy = g.P(17.0, 47.0)
    g.add('gear2', x_gear(gx, gy, 3.0, teeth=6, th=1.3, phase=0.3), STEEL, 1.5, seam='dark', form=False)
    g.render()
    g.px(math.floor(cx), math.floor(cy), OUTLINE)
    g.px(math.floor(gx), math.floor(gy), OUTLINE)
    g.px(math.floor(hx), math.floor(hy), OUTLINE)
    g.studs(-2.0, 44.5, 9.0, 44.5, 3, COPPER.c(6), COPPER.c(0), g.mask('cuff'))
    g.hline(2.3, 4.0, 2.3, 26.0, BRASS.c(1), g.mask('idx*'))
    x, y = g.P(1.0, 48.0)
    g.circle(x, y, 2.3, '#f4f0e0', g.mask('cuff'))
    g.line(x, y, x + 1, y - 1, '#c01818', g.mask('cuff'))
    return '#ffb84a'


def d_pirate(g):
    U, V = g.U, g.V
    std_hand(g, PIRATE, seam='hard')
    g.add('ring', inter(sd_capsule(U, V, (0, 4.2), (0, 27.0), IDX_R + 0.4), band(V, 18.6, 21.0)), GOLD, 1.2, seam='dark')
    g.add('cuff', s_cuff(g, 39.0, 55.0, flare=8.0), BURG, 4.5, seam='hard')
    g.add('crim', inter(s_cuff(g, 39.0, 56.0, flare=8.6), band(V, 53.0, 57.0)), GOLD, 1.5, seam='dark')
    g.render()
    x, y = g.P(0.0, 19.8)
    g.gem(x, y, 1.6, 1.6, GEM_RED)
    skull = sprite("""
        .WWWWW.
        WWWWWWW
        WkkWkkW
        WkkWkkW
        WWWkWWW
        .WWWWW.
        .WkWkW.""", {'W': '#f4efe0', 'k': '#1a0c0c'})
    g.blit_h(skull, 9.5, 47.0, g.mask('cuff'))
    cm = g.mask('cuff')
    g.hline(-9.0, 41.0, 28.0, 41.0, GOLD.c(3), cm)
    return '#ffcf4a'


def d_dragon(g):
    U, V = g.U, g.V
    for (v0, L) in ((31.0, 6.0), (39.0, 6.5), (47.0, 6.5), (54.0, 5.5)):
        g.add('dspike', s_spike(g, 23.5 + (v0 - 31) * 0.05, v0, 1.0, 0.35, L + 3.0, 5.2), SPIKE, 1.5, seam='hard')
    g.add('back', s_back(g), SCALE, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        kk = 2 - k
        g.add(nm, s_curl(g, kk), SCALE, CURL[kk][3] * 0.85, seam='hard')
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        kk = 2 - k
        u, v0, v1, r = CURL[kk]
        g.add('t' + nm, sd_path(U, V, [(u + 0.5, v0 - r + 2.2), (u - 0.3, v0 - r - 1.0), (u - 2.6, v0 - r - 3.2)], 1.7, 0.25),
              TALON, 1.2, seam='hard')
    g.add('thb', s_thumb(g), SCALE, 3.6, seam='hard')
    g.add('tthb', sd_path(U, V, [(-8.6, 30.5), (-10.8, 26.0), (-10.6, 22.6)], 1.7, 0.25), TALON, 1.2, seam='hard')
    g.add('idx', sd_capsule(U, V, (0, 9.0), (0, 27.0), 3.9), SCALE, 3.6, seam='hard')
    g.add('talon', sd_path(U, V, [(0.4, 11.0), (0.6, 5.5), (0.0, 1.5), (-0.6, -0.5)], 2.8, 0.3), TALON, 1.6, seam='hard')
    g.pointer = 'talon'
    g.add('cuff', s_cuff(g, 40.0, 57.0, flare=1.0, r=1.5), SCALE, 4.0, seam='hard')
    g.add('belly', inter(s_cuff(g, 40.0, 57.0, flare=1.0, r=1.5), sd_poly(U, V, [(-10, 38), (2.0, 38), (0.0, 60), (-10, 60)])),
          BELLY, 2.0, seam='hard')
    g.render()
    sc = g.mask('back', 'cuff', 'idx', 'thb', 'mid', 'rng', 'pnk')
    for y, x in zip(*np.nonzero(sc)):
        u, v = g.U[y, x], g.V[y, x]
        row = math.floor(v / 3.0)
        fu = ((u + (row % 2) * 1.8) / 3.6) % 1.0
        fv = (v / 3.0) % 1.0
        if fv > 0.66 and 0.25 < fu < 0.75:
            g.a[y, x] = SCALE.c(g.idx[y, x] - 1)
        elif fv < 0.3 and 0.3 < fu < 0.6 and g.idx[y, x] >= 3:
            g.a[y, x] = SCALE.c(g.idx[y, x] + 1)
    bl = g.mask('belly')
    for v in np.arange(42.0, 58.0, 3.0):
        g.hline(-10.0, v, 1.5, v, BELLY.c(1), bl)
    eye = sprite("""
        .kkkkk.
        kyYkYyk
        .kkkkk.""", {'k': '#1a0c04', 'Y': '#ffe25a', 'y': '#e8a020'})
    g.blit_h(eye, 10.5, 34.0, g.mask('back'))
    return '#ffd040'


def d_angel(g):
    wing_l(g, g.P(-5.0, 46.5), FEATHER)
    wing_r(g, g.P(25.0, 43.0), FEATHER)
    armor(g, PEARL, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=True, knuck_mat=GOLD, cuff=(40.0, 53.0, 3.0),
          rim_band=2.4, rim_mat=GOLD)
    g.render()
    cx, cy = g.P(10.5, 34.5)
    bm = g.mask('back')
    g.circle(cx, cy, 3.4, GOLD.c(4), bm, ring=True)
    g.circle(cx, cy, 2.4, GOLD.c(2), bm, ring=True)
    g.gem(cx, cy, 1.4, 1.4, GEM_CYAN)
    return '#fff0a0'


def d_demon(g):
    U, V = g.U, g.V
    lx, ly = g.P(-4.0, 45.0)
    g.add('horn1', x_path([(lx, ly), (lx - 7.0, ly + 1.5), (lx - 12.5, ly - 2.0), (lx - 14.5, ly - 8.5)], 3.4, 0.4), HORN, 2.2, seam='hard')
    rx, ry = g.P(24.0, 42.0)
    g.add('horn2', x_path([(rx, ry), (rx + 6.0, ry - 2.5), (rx + 9.0, ry - 8.0), (rx + 8.0, ry - 14.0)], 3.4, 0.4), HORN, 2.2, seam='hard')
    g.add('back', s_back(g), DEMON, 5.0, seam=None)
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        kk = 2 - k
        g.add(nm, s_curl(g, kk), DEMON, CURL[kk][3] * 0.85, seam='hard')
    for k, nm in enumerate(('pnk', 'rng', 'mid')):
        kk = 2 - k
        u, v0, v1, r = CURL[kk]
        g.add('t' + nm, sd_path(U, V, [(u + 0.5, v0 - r + 2.2), (u - 0.3, v0 - r - 1.3), (u - 2.8, v0 - r - 3.8)], 1.8, 0.25),
              CLAWK, 1.2, seam='dark')
    g.add('thb', s_thumb(g), DEMON, 3.6, seam='hard')
    g.add('tthb', sd_path(U, V, [(-8.6, 30.5), (-10.9, 25.5), (-10.6, 22.2)], 1.8, 0.25), CLAWK, 1.2, seam='dark')
    g.add('idx', sd_capsule(U, V, (0, 9.0), (0, 27.0), 3.9), DEMON, 3.6, seam='hard')
    g.add('talon', sd_path(U, V, [(0.4, 11.0), (0.6, 5.5), (0.0, 1.5), (-0.6, -0.5)], 2.8, 0.3), CLAWK, 1.6, seam='dark')
    g.pointer = 'talon'
    g.add('cuff', s_cuff(g, 40.0, 53.0, flare=3.0), DEMON_D, 4.0, seam='hard')
    for t in np.linspace(-6.0, 25.0, 4):
        g.add('cspike', s_spike(g, t, 52.0, 0.2, 1.0, 5.0, 4.2), HORN, 1.5, seam='hard')
    g.render()
    for nm in ('horn1', 'horn2'):
        hm = g.mask(nm)
        for y, x in zip(*np.nonzero(hm)):
            if (x + y) % 3 == 0 and g.idx[y, x] >= 2:
                g.a[y, x] = HORN.c(g.idx[y, x] - 1)
    bm = g.mask('back', 'cuff')
    for (u0, v0, u1, v1) in ((3.0, 30.0, 6.0, 34.0), (6.0, 34.0, 4.0, 38.0), (13.0, 31.0, 15.5, 36.0), (15.5, 36.0, 19.0, 37.5),
                             (2.0, 44.0, 7.0, 47.0), (12.0, 45.0, 17.0, 47.0)):
        g.hline(u0, v0, u1, v1, '#ff6a1a', bm)
    for (u, v) in ((6.0, 34.0), (15.5, 36.0)):
        g.hpx(u, v, '#ffc040', bm)
    return '#ff5a2a'


def d_diamond(g):
    U, V = g.U, g.V
    armor(g, DIAMOND, tip='pointed', cuts=(8.0, 15.5, 21.5), knuck=False, cuff=(40.0, 53.0, 5.0), rim_band=2.4,
          cuff_mat=PLAT, rim_mat=PLAT, seam=DIAMOND.c(1))
    oct_ = [(10.5 + 6.6 * math.cos(math.radians(a)), 34.5 + 6.0 * math.sin(math.radians(a))) for a in range(0, 360, 45)]
    g.add('bezel', sd_poly(U, V, oct_, 1.4), PLAT, 1.6, seam='dark')
    g.add('brill', sd_poly(U, V, oct_, 0.0), DIAMOND_G, 4.0, seam=DIAMOND.c(1))
    g.render()
    cx, cy = g.P(10.5, 34.5)
    bm = g.mask('brill')
    for (u, v) in oct_[::2]:
        x, y = g.P(u, v)
        g.line(cx, cy, x, y, DIAMOND.c(6), bm)
    g.px(math.floor(cx), math.floor(cy), '#ffffff')
    for (u, v, c) in ((7.0, 31.0, '#ffb0e0'), (14.0, 37.0, '#b0ffe0'), (-1.0, 12.0, '#fff0a0'), (16.0, 26.0, '#b0e0ff')):
        g.hpx(u, v, c, g.lab > 0)
    for t in (-2.0, 5.0, 12.0, 19.0):
        x, y = g.P(t, 46.5)
        g.gem(x, y, 1.5, 1.5, GEM_WHITE)
    g.accent(spark('#ffffff'), *g.Pi(-9.0, 7.0))
    g.accent(spark('#d8f2ff', small=True), *g.Pi(30.0, 24.0))
    return '#ffffff'


# rig overrides (a little more room on the right for big cuffs / spikes / wings)
d_dragon.kw = dict(tip=(7.0, 3.0))
d_angel.kw = dict(tip=(7.5, 3.0))
d_pirate.kw = dict(tip=(7.0, 3.0))


DESIGNS = [
    (1, 'Leather Glove', 'Lederhandschuh', d_leather),
    (2, 'Wool Mitten', 'Wollfäustling', d_mitten),
    (3, 'Iron Gauntlet', 'Eisenhandschuh', d_iron),
    (4, 'Bronze Gauntlet', 'Bronzehandschuh', d_bronze),
    (5, 'Silver Gauntlet', 'Silberhandschuh', d_silver),
    (6, 'Golden Gauntlet', 'Goldhandschuh', d_golden),
    (7, 'Crystal Gauntlet', 'Kristallhandschuh', d_crystal),
    (8, 'Ruby Gauntlet', 'Rubinhandschuh', d_ruby),
    (9, 'Emerald Gauntlet', 'Smaragdhandschuh', d_emerald),
    (10, 'Sapphire Gauntlet', 'Saphirhandschuh', d_sapphire),
    (11, 'Obsidian Gauntlet', 'Obsidianhandschuh', d_obsidian),
    (12, 'Bone Hand', 'Knochenhand', d_bone),
    (13, "Thief's Glove", 'Diebeshandschuh', d_thief),
    (14, "Wizard's Glove", 'Zaubererhandschuh', d_wizard),
    (15, "Fortune Teller's Hand", 'Hand der Wahrsagerin', d_fortune),
    (16, "Knight's Gauntlet", 'Ritterhandschuh', d_knight),
    (17, 'Samurai Gauntlet', 'Samurai-Handschuh', d_samurai),
    (18, 'Frost Gauntlet', 'Frosthandschuh', d_frost),
    (19, 'Flame Gauntlet', 'Flammenhandschuh', d_flame),
    (20, 'Storm Gauntlet', 'Sturmhandschuh', d_storm),
    (21, 'Nature Glove', 'Naturhandschuh', d_nature),
    (22, 'Cosmic Gauntlet', 'Kosmischer Handschuh', d_cosmic),
    (23, 'Shadow Glove', 'Schattenhandschuh', d_shadow),
    (24, 'Royal Glove', 'Königlicher Handschuh', d_royal),
    (25, 'Clockwork Gauntlet', 'Uhrwerkhandschuh', d_clockwork),
    (26, 'Pirate Glove', 'Piratenhandschuh', d_pirate),
    (27, 'Dragon Claw', 'Drachenklaue', d_dragon),
    (28, 'Angel Gauntlet', 'Engelshandschuh', d_angel),
    (29, 'Demon Claw', 'Dämonenklaue', d_demon),
    (30, 'Diamond Gauntlet', 'Diamanthandschuh', d_diamond),
]


# ------------------------------------------------------------------ output
DARK_BG = (42, 16, 44, 255)     # dark purple like the game's background
LIGHT_BG = (226, 222, 210, 255)


def make(fn, **kw):
    kw2 = dict(getattr(fn, 'kw', {}))
    kw2.update(kw)
    g = G(**kw2)
    rim = fn(g)
    a = g.finish(rim)
    return g, a


def font(size):
    for name in ('arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def build():
    """render all designs -> list of (k, en, de, rgba64, tip)"""
    res = []
    for (k, en, de, fn) in DESIGNS:
        g, a = make(fn)
        a = a.copy()
        a[a[:, :, 3] == 0] = 0
        assert set(np.unique(a[:, :, 3])) <= {0, 255}
        m = a[:, :, 3] > 0
        assert not (m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()), 'design %d touches the border' % k
        res.append((k, en, de, a, g.tip()))
    return res


def contact_sheet(res, path, cols=6):
    cell, lab_h, pad = 128, 30, 8
    rows = (len(res) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = rows * (cell + lab_h + pad) + pad
    sheet = Image.new('RGBA', (W, H), (24, 14, 30, 255))
    d = ImageDraw.Draw(sheet)
    f1, f2 = font(12), font(10)
    for i, (k, en, de, a, (tx, ty)) in enumerate(res):
        r, c = divmod(i, cols)
        x, y = pad + c * (cell + pad), pad + r * (cell + lab_h + pad)
        bg = Image.new('RGBA', (cell, cell), DARK_BG)
        bg.alpha_composite(Image.fromarray(a, 'RGBA').resize((cell, cell), Image.NEAREST))
        sheet.alpha_composite(bg, (x, y))
        hx, hy = tx * SC + 1, ty * SC + 1
        for dd in (-4, -3, 3, 4):
            d.point((x + hx + dd, y + hy), fill=(0, 255, 120, 255))
            d.point((x + hx, y + hy + dd), fill=(0, 255, 120, 255))
        d.text((x + cell // 2, y + cell + 2), '%d  %s' % (k, en), fill=(240, 232, 214, 255), font=f1, anchor='ma')
        d.text((x + cell // 2, y + cell + 16), de, fill=(170, 160, 190, 255), font=f2, anchor='ma')
    sheet.save(path)


def check_image(res, path, cols=6):
    """every cursor at 64x64 (the size it has on screen) on dark purple and on a light background"""
    pad, lab_h = 6, 14
    cw = 64 * 2 + 2
    rows = (len(res) + cols - 1) // cols
    W = cols * (cw + pad) + pad
    H = rows * (64 + lab_h + pad) + pad
    sheet = Image.new('RGBA', (W, H), (60, 60, 64, 255))
    d = ImageDraw.Draw(sheet)
    f1 = font(10)
    for i, (k, en, de, a, tip) in enumerate(res):
        r, c = divmod(i, cols)
        x, y = pad + c * (cw + pad), pad + r * (64 + lab_h + pad)
        im = Image.fromarray(a, 'RGBA')
        for j, bgc in enumerate((DARK_BG, LIGHT_BG)):
            bg = Image.new('RGBA', (64, 64), bgc)
            bg.alpha_composite(im)
            sheet.alpha_composite(bg, (x + j * 66, y))
        d.text((x + cw // 2, y + 65), '%d %s' % (k, en), fill=(235, 235, 235, 255), font=f1, anchor='ma')
    sheet.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    res = build()
    meta = {}
    for (k, en, de, a, (tx, ty)) in res:
        img = Image.fromarray(a, 'RGBA').resize((N * SC, N * SC), Image.NEAREST)
        img.save(os.path.join(OUT, 'gauntlet_%d.png' % k))
        meta['gauntlet_%d' % k] = {'hotspot': [tx * SC + 1, ty * SC + 1], 'name_en': en, 'name_de': de}
    with open(os.path.join(OUT, 'gauntlets.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    contact_sheet(res, os.path.join(OUT, 'contact_sheet.png'))
    check_image(res, os.path.join(OUT, '_preview_check.png'))
    print('wrote %d gauntlets to %s' % (len(res), OUT))


if __name__ == '__main__':
    main()
