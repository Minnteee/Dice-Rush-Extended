"""Table cloth + cushion renderers with a shared fabric pattern system.

A design (see scene_designs.py) supplies colour ramps and a pattern function
pattern(fab) that edits the fabric 'level' field (tone patterns), picks
alternative ramps (fab.sel) and stamps motifs (fab.stamp / fab.scatter / fab.row).

Fabric coordinates (s, t) are in pixels: s runs left->right, t downwards; on
horizontal surfaces t = screen_y * TS (TS = 2.6, i.e. a mildly cheated
perspective), on hanging/vertical surfaces t = screen_y.
"""
import math

import numpy as np

from scene_lib import (grid, quantize, fbm, vnoise, hash01, ramp_arr, hexc, mix, dilate, erode,
                       edge_out, edge_in, shift, char_map, lerp_ramp, seg_field)
from scene_table import TableGeo, ell_dist, col_rows, WOOD, GOLD

TS = 2.6
OFF = {'1': -0.30, '2': -0.15, '3': 0.0, '4': 0.15, '5': 0.30}


# =================================================================== motifs
class Motif:
    def __init__(self, art):
        self.cm = char_map(art) if isinstance(art, str) else art
        self.h, self.w = self.cm.shape

    def flat(self):
        """vertically squashed copy for horizontal surfaces (keeps the middle row)."""
        h = self.h
        if h <= 3:
            return self
        rows = sorted(set(range(0, h, 2)) | {h // 2})
        if len(rows) > (h + 1) // 2 + 1:
            rows = sorted(set(range(0, h, 2)))
        return Motif(self.cm[rows])

    def mirror(self):
        return Motif(self.cm[:, ::-1].copy())


def lines_motif(segs, w, h, ch='3'):
    cm = np.full((h, w), '.', dtype='<U1')
    for (x0, y0, x1, y1) in segs:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) * 3 + 1
        for i in range(n + 1):
            f = i / max(n, 1)
            x = int(round(x0 + (x1 - x0) * f))
            y = int(round(y0 + (y1 - y0) * f))
            cm[y, x] = ch
    return Motif(cm)


def disc_motif(r, ch='3', hi='4', rim=None):
    n = int(math.ceil(r * 2))
    cm = np.full((n, n), '.', dtype='<U1')
    c = n / 2.0
    for y in range(n):
        for x in range(n):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if d <= r:
                cm[y, x] = ch
                if rim and d > r - 1.0:
                    cm[y, x] = rim
                if hi and (x + 0.5 - c) < -0.2 * r and (y + 0.5 - c) < -0.2 * r and d < r - 0.6:
                    cm[y, x] = hi
    return Motif(cm)


def moon_phase(phase, r=4.0):
    """phase 0..1 (0 new, .5 full). lit = '4'/'5', dark side = 'x' (darker fabric), rim 'o'."""
    n = int(math.ceil(r * 2)) + 1
    cm = np.full((n, n), '.', dtype='<U1')
    c = n / 2.0
    k = math.cos(phase * 2 * math.pi)        # 1 new .. -1 full
    for y in range(n):
        for x in range(n):
            u = (x + 0.5 - c) / r
            v = (y + 0.5 - c) / r
            d = u * u + v * v
            if d > 1.0:
                continue
            w = math.sqrt(max(0.0, 1 - v * v))
            if phase < 0.5:                      # waxing: lit on the right
                lit = u > k * w
            else:                                # waning: lit on the left
                lit = -u > k * w
            if d > (1 - 1.6 / r):
                cm[y, x] = '2' if lit else 'o'
            else:
                cm[y, x] = ('5' if (u < -0.1 and v < -0.1) else '4') if lit else 'x'
    return Motif(cm)


M = {}
M['dot'] = Motif('3')
M['dot2'] = Motif('33\n33')
M['star3'] = Motif('.3.\n353\n.3.')
M['star5'] = Motif("""
..2..
..4..
24542
..4..
..2..
""")
M['star7'] = Motif("""
...2...
...3...
..343..
2345432
..343..
...3...
...2...
""")
M['sparkle'] = Motif("""
.2.2.
..4..
.454.
..4..
.2.2.
""")
M['moon'] = Motif("""
.o44.
o45o.
45o..
45...
45o..
o45o.
.o44.
""")
M['moon_s'] = Motif("""
.44
45.
45.
.44
""")
M['diamond'] = Motif("""
..3..
.343.
34543
.343.
..3..
""")
M['diamond_s'] = Motif('.3.\n343\n.3.')
M['rose'] = Motif("""
..oooo...
.o3443o..
o344543o.
o354453o.
o34543o..
.o3333oA.
AAoooAAA.
.AAB.AA..
..A......
""")
M['rose_s'] = Motif("""
.o44o.
o4554o
o3443o
.ooooA
.AA.A.
""")
M['bud'] = Motif("""
.33.
3443
.33.
.A..
""")
M['leaf'] = Motif("""
...AB
..ABA
.ABA.
ABA..
A....
""")
M['leaf2'] = Motif("""
AB...
ABA..
.ABA.
..ABA
....A
""")
M['vine_leaf'] = Motif("""
.AAA.
ABCBA
ABCBA
.ABA.
..A..
""")
M['snow'] = Motif("""
...3...
.3.4.3.
..343..
3345433
..343..
.3.4.3.
...3...
""")
M['snow_s'] = Motif("""
.3.3.
..4..
34543
..4..
.3.3.
""")
M['heart'] = Motif("""
.33.33.
3445443
3454443
.34443.
..343..
...3...
""")
M['polka'] = Motif("""
.333.
34443
34543
34443
.333.
""")
M['ember'] = Motif("""
.4.
454
.3.
""")
M['flame'] = Motif("""
...4...
..454..
..454..
.34543.
.34543.
2345432
.23432.
""")
M['peacock'] = Motif("""
...AAA...
..ABBBA..
.AB222BA.
AB23332BA
AB2cdc2BA
AB2cdc2BA
AB23332BA
.AB222BA.
..ABBBA..
...AAA...
....A....
....A....
""")
M['peacock_s'] = Motif("""
.AAA.
AB2BA
B2c2B
AB2BA
.AAA.
""")
M['feather_barb'] = Motif("""
A...A
.A.A.
..A..
""")
M['sun'] = Motif("""
....3....
.3..4..3.
..3.4.3..
...444...
344555443
...444...
..3.4.3..
.3..4..3.
....3....
""")
M['sun_s'] = Motif("""
..3..
.343.
34543
.343.
..3..
""")
M['eye'] = Motif("""
..33333..
.3.....3.
3..ooo..3
3.oAAAo.3
3..ooo..3
.3.....3.
..33333..
""")
M['wave_curl'] = Motif("""
..444..
.4...4.
4..44.4
4.4..4.
4..44..
.4.....
""")
M['shell'] = Motif("""
..333..
.34543.
3454543
3343433
.33333.
""")
M['lace'] = Motif("""
.3.3.3.
3.3.3.3
.3.3.3.
""")
M['crown'] = Motif("""
3.3.3
34343
35553
33333
""")
M['key'] = Motif("""
.333.
3...3
.333.
..3..
..33.
..3..
..33.
""")
M['moonstar'] = Motif("""
..o44o.....
.o45o......
o45o....4..
o45....454.
o45o....4..
.o45o......
..o44o.....
""")
M['moonstar_l'] = Motif("""
...ooo........
..o445o.......
.o45oo........
o45o......2...
o45o.....343..
o45o....24542.
o45o.....343..
o45o......2...
.o45oo........
..o445o.......
...ooo........
""")
M['cross_star'] = Motif("""
...3...
...4...
...4...
3445443
...4...
...4...
...3...
""")
M['triangle_eye'] = Motif("""
.....3.....
....343....
...3...3...
..3.ooo.3..
.3.oAAAo.3.
3...ooo...3
33333333333
""")


def rune_glyphs():
    R = []
    segs = [
        [(0, 0, 0, 6), (0, 2, 3, 0), (0, 4, 3, 2)],              # fehu
        [(0, 0, 0, 6), (0, 0, 3, 2), (3, 2, 3, 6)],              # uruz
        [(0, 0, 0, 6), (0, 2, 2, 3), (2, 3, 0, 4)],              # thurisaz
        [(0, 0, 0, 6), (0, 1, 3, 3), (0, 3, 3, 5)],              # ansuz
        [(0, 0, 0, 6), (0, 0, 3, 1), (3, 1, 0, 3), (0, 3, 3, 6)],  # raido
        [(3, 0, 0, 3), (0, 3, 3, 6)],                            # kenaz
        [(0, 0, 4, 6), (4, 0, 0, 6)],                            # gebo
        [(0, 0, 0, 6), (0, 0, 3, 1), (3, 1, 0, 3)],              # wunjo
        [(0, 0, 0, 6), (3, 0, 3, 6), (0, 2, 3, 4)],              # hagalaz
        [(2, 0, 2, 6), (2, 3, 0, 1), (2, 3, 4, 1)],              # algiz
        [(3, 0, 0, 2), (0, 2, 3, 4), (3, 4, 0, 6)],              # sowilo
        [(2, 0, 2, 6), (2, 0, 0, 2), (2, 0, 4, 2)],              # tiwaz
        [(0, 0, 0, 6), (0, 0, 3, 2), (3, 2, 0, 3), (0, 3, 3, 4), (3, 4, 0, 6)],  # berkano
        [(0, 0, 0, 6), (4, 0, 4, 6), (0, 0, 4, 6), (4, 0, 0, 6)],  # dagaz-ish
    ]
    for s in segs:
        R.append(lines_motif(s, 5, 7, '4'))
    return R


RUNES = rune_glyphs()


# ================================================================ fabric ctx
class Fab:
    """pattern context.  Arrays are image-shaped; proj(s, t) -> image (x, y) floats or None."""

    def __init__(self, mask, s, t, lev, flat, proj, design, seed=0):
        self.m = mask
        self.s = s
        self.t = t
        self.lev = lev
        self.flatmask = flat                      # bool array: pixel lies on a horizontal surface
        self.proj = proj
        self.d = design
        self.sel = np.zeros(mask.shape, np.int32)
        self.ov = np.zeros(mask.shape + (4,), np.uint8)
        self.seed = seed
        self.H, self.W = mask.shape
        self.extra = {}

    # -- tone helpers
    def tone(self, field, amp, where=None):
        m = self.m if where is None else (self.m & where)
        self.lev[m] += (field[m] if np.ndim(field) else field) * amp

    def select(self, cond, k):
        self.sel[self.m & cond] = k

    # -- motifs
    def ramp(self, name):
        r = self.d[name] if isinstance(name, str) else name
        return ramp_arr(r)

    def stamp(self, motif, x, y, ramps, need=0.75, flat=None, lev_add=0.0, base_dark=0.22):
        """centre the motif at image coords (x, y).  ramps: list of ramp names / lists."""
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if not (0 <= xi < self.W and 0 <= yi < self.H) or not self.m[yi, xi]:
            return False
        if flat is None:
            flat = bool(self.flatmask[yi, xi])
        mo = motif.flat() if flat else motif
        cm = mo.cm
        h, w = cm.shape
        x0 = xi - w // 2
        y0 = yi - h // 2
        pts = [(j, i, ch) for (j, i), ch in np.ndenumerate(cm) if ch != '.']
        inside = sum(1 for (j, i, ch) in pts if 0 <= y0 + j < self.H and 0 <= x0 + i < self.W and self.m[y0 + j, x0 + i])
        if inside < need * len(pts):
            return False
        rr = [self.ramp(r) for r in ramps]
        base = ramp_arr(self.d['base'])
        for (j, i, ch) in pts:
            Y, X = y0 + j, x0 + i
            if not (0 <= Y < self.H and 0 <= X < self.W) or not self.m[Y, X]:
                continue
            L = self.lev[Y, X] + lev_add
            if ch in OFF:
                r, off = rr[0], OFF[ch]
            elif ch in 'ABCDE':
                r, off = rr[1 % len(rr)], OFF[str('ABCDE'.index(ch) + 1)]
            elif ch in 'abcde':
                r, off = rr[2 % len(rr)], OFF[str('abcde'.index(ch) + 1)]
            elif ch == 'o':
                self.ov[Y, X] = tuple(rr[0][0]) + (255,)
                continue
            elif ch == 'O':
                self.ov[Y, X] = tuple(rr[1 % len(rr)][0]) + (255,)
                continue
            elif ch == 'x':
                r, off = base, -base_dark
            elif ch == 'X':
                r, off = base, +0.14
            else:
                continue
            k = int(np.clip(round((L + off) * (len(r) - 1)), 0, len(r) - 1))
            self.ov[Y, X] = tuple(r[k]) + (255,)
        return True

    def scatter(self, motif, ds, dt, ramps, seed=1, jitter=0.35, stagger=True, need=0.75, s0=0.0, t0=0.0,
                prob=1.0, choose=None, region=None):
        """jittered lattice of motifs over the fabric (s, t) space."""
        ss = self.s[self.m]
        tt = self.t[self.m]
        if ss.size == 0:
            return
        i0, i1 = int(math.floor((ss.min() - s0) / ds)) - 1, int(math.ceil((ss.max() - s0) / ds)) + 1
        j0, j1 = int(math.floor((tt.min() - t0) / dt)) - 1, int(math.ceil((tt.max() - t0) / dt)) + 1
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                h1 = float(hash01(i, j, seed))
                h2 = float(hash01(i, j, seed + 101))
                h3 = float(hash01(i, j, seed + 202))
                if h3 > prob:
                    continue
                s = s0 + (i + (0.5 if (stagger and j % 2) else 0.0) + (h1 - 0.5) * jitter) * ds
                t = t0 + (j + (h2 - 0.5) * jitter) * dt
                p = self.proj(s, t)
                if p is None:
                    continue
                if region is not None and not region(p[0], p[1]):
                    continue
                mo = motif if choose is None else choose(i, j, h1, h2)
                self.stamp(mo, p[0], p[1], ramps, need=need)


# ============================================================== fringes etc
TASSEL = char_map("""
..o3o..
.o454o.
.o343o.
..o2o..
.o454o.
.o343o.
o34543o
o34433o
o34432o
o23432o
o23332o
.o2o2o.
""")

TASSEL_M = char_map("""
.o4o.
o454o
.o3o.
.o5o.
o343o
o344o
o243o
o233o
.o2o.
""")

TASSEL_S = char_map("""
.o4o.
.o3o.
.o5o.
o343o
o343o
o232o
.2.2.
""")


def draw_sprite_lev(img, cm, x0, y0, ramp, base_lev=0.55, outline=None, light=0.0, only_empty=False):
    """draw a char-map sprite: digits are ramp levels (offset from base_lev), 'o' outline."""
    H, W = img.shape[:2]
    r = ramp_arr(ramp)
    oc = hexc(outline if outline is not None else ramp[0])
    h, w = cm.shape
    for (j, i), ch in np.ndenumerate(cm):
        if ch == '.':
            continue
        X, Y = x0 + i, y0 + j
        if not (0 <= X < W and 0 <= Y < H):
            continue
        if only_empty and img[Y, X, 3] > 0:
            continue
        if ch == 'o':
            img[Y, X] = oc
            continue
        L = base_lev + OFF.get(ch, 0.0) + light * ((i - w / 2) / max(w / 2, 1))
        k = int(np.clip(round(L * (len(r) - 1)), 0, len(r) - 1))
        img[Y, X, :3] = r[k]
        img[Y, X, 3] = 255


# ================================================================ the cushion
def _normals(xw, yw, z, flip=False):
    xa = np.gradient(xw, axis=1)
    ya = np.gradient(yw, axis=1)
    za = np.gradient(z, axis=1)
    xb = np.gradient(xw, axis=0)
    yb = np.gradient(yw, axis=0)
    zb = np.gradient(z, axis=0)
    nx = ya * zb - za * yb
    ny = za * xb - xa * zb
    nz = xa * yb - ya * xb
    L = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    nx, ny, nz = nx / L, ny / L, nz / L
    if flip:
        nx, ny, nz = -nx, -ny, -nz
    return nx, ny, nz


class CushionGeo:
    def __init__(self, W=168, H=52, cx=84.0, cyf=35.1, hw=68.0, hd=64.0, bulge=-0.08, phi=12.0,
                 z_s=9.0, ht=22.0, hb=9.5, p=0.85, dent_r=34.0, dent=2.5, bow=0.04, light=(0.42, 0.55, 0.62),
                 mini=False):
        self.__dict__.update(locals())
        del self.__dict__['self']
        self.sinp = math.sin(math.radians(phi))
        self.cosp = math.cos(math.radians(phi))

    def P(self, A, B, surf=1):
        f = np.clip((1 - A * A) * (1 - B * B), 0, 1) ** self.p
        xw = A * self.hw * (1 + self.bulge * (1 - B * B))
        yw = B * self.hd * (1 + self.bow * (1 - A * A))   # front/back seams bow out slightly
        if surf == 1:
            r = np.hypot(xw, yw)
            z = self.z_s + self.ht * f - self.dent * np.exp(-(r / self.dent_r) ** 4)
        else:
            z = np.maximum(self.z_s - self.hb * f, 0.0)
        return xw, yw, z

    def screen(self, xw, yw, z):
        return self.cx + xw, self.cyf + yw * self.sinp - z * self.cosp, yw * self.cosp + z * self.sinp


def render_cushion(design, cg=None, seed=0):
    cg = cg or CushionGeo()
    W, H = cg.W, cg.H
    Lx, Ly, Lz = cg.light
    ln = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz)
    Lx, Ly, Lz = Lx / ln, Ly / ln, Lz / ln
    Cy, Cz = cg.cosp, cg.sinp
    dens = 3.2 if not cg.mini else 4.0
    Na = int(cg.hw * 2 * (1 + cg.bulge) * dens) + 1
    Nb = int(cg.hd * 2 * (1 + cg.bulge) * dens * 0.6) + 1
    A, B = np.meshgrid(np.linspace(-1, 1, Na), np.linspace(-1, 1, Nb))
    samples = []
    for surf in (1, 2):
        xw, yw, z = cg.P(A, B, surf)
        nx, ny, nz = _normals(xw, yw, z, flip=(surf == 2))
        ndl = nx * Lx + ny * Ly + nz * Lz
        ndc = ny * Cy + nz * Cz
        sheen = np.clip(1 - np.abs(ndc), 0, 1) ** 3
        f = np.clip((1 - A * A) * (1 - B * B), 0, 1)
        # stylised 'puff': bright soft centre, darkening towards the seams + directional light
        puff = np.sqrt(f)
        lev = 0.06 + 0.34 * np.clip(ndl, 0, 1) + 0.42 * puff + 0.10 * sheen - 0.16 * (1 - f) ** 4
        if surf == 2:
            lev = 0.16 + 0.30 * np.clip(ndl, 0, 1) - 0.10 * np.clip((cg.z_s - z) / cg.z_s, 0, 1)
        X, Y, D = cg.screen(xw, yw, z)
        vis = ndc > -0.05
        samples.append(dict(X=X[vis], Y=Y[vis], D=D[vis], lev=lev[vis], u=xw[vis], v=yw[vis], z=z[vis],
                            surf=np.full(vis.sum(), surf), A=A[vis], B=B[vis]))
    # piping along the seam (tube)
    sp = []
    nseg = int(cg.hw * 2 * 4)
    tt = np.linspace(-1, 1, nseg)
    rp = 0.8 if not cg.mini else 0.6
    th = np.linspace(0, 2 * math.pi, 14, endpoint=False)
    for (ea, eb) in (('t', -1), ('t', 1), ('l', -1), ('l', 1)):
        if ea == 't':
            Aa, Bb = tt, np.full_like(tt, eb)
            ox, oy = np.zeros_like(tt), np.full_like(tt, float(eb))
        else:
            Aa, Bb = np.full_like(tt, eb), tt
            ox, oy = np.full_like(tt, float(eb)), np.zeros_like(tt)
        xw, yw, z = cg.P(Aa, Bb, 1)
        for a_ in th:
            nxx, nyy, nzz = ox * math.cos(a_), oy * math.cos(a_), np.full_like(tt, math.sin(a_))
            px, py, pz = xw + rp * nxx, yw + rp * nyy, z + rp * nzz
            X, Y, D = cg.screen(px, py, pz)
            ndl = nxx * Lx + nyy * Ly + nzz * Lz
            ndc = nyy * Cy + nzz * Cz
            vis = ndc > -0.2
            twist = np.sign(np.sin(tt * cg.hw * 1.3 + a_ * 0.5)) * 0.10
            sp.append(dict(X=X[vis], Y=Y[vis], D=D[vis] + 0.3,
                           lev=(0.18 + 0.52 * np.clip(ndl, 0, 1) + twist)[vis],
                           u=px[vis], v=py[vis], z=pz[vis], surf=np.full(vis.sum(), 3), A=Aa[vis], B=Bb[vis]))
    samples += sp
    cat = {k: np.concatenate([s_[k] for s_ in samples]) for k in samples[0]}
    xi = np.floor(cat['X']).astype(np.int64)
    yi = np.floor(cat['Y']).astype(np.int64)
    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
    for k in cat:
        cat[k] = cat[k][ok]
    xi, yi = xi[ok], yi[ok]
    order = np.argsort(-cat['D'], kind='stable')
    key = (yi * W + xi)[order]
    _, first = np.unique(key, return_index=True)
    sel = order[first]
    surf = np.zeros((H, W), np.int32)
    lev = np.zeros((H, W), np.float32)
    U = np.zeros((H, W), np.float32)
    V = np.zeros((H, W), np.float32)
    Z = np.zeros((H, W), np.float32)
    AA = np.zeros((H, W), np.float32)
    BB = np.zeros((H, W), np.float32)
    yy, xx = yi[sel], xi[sel]
    surf[yy, xx] = cat['surf'][sel]
    lev[yy, xx] = cat['lev'][sel]
    U[yy, xx] = cat['u'][sel]
    V[yy, xx] = cat['v'][sel]
    Z[yy, xx] = cat['z'][sel]
    AA[yy, xx] = cat['A'][sel]
    BB[yy, xx] = cat['B'][sel]
    # fill single-pixel holes inside the body (sampling gaps)
    body = surf > 0
    hole = ~body & shift(body, 1, 0) & shift(body, -1, 0) & shift(body, 0, 1) & shift(body, 0, -1)
    if hole.any():
        for arr in (surf, lev, U, V, Z, AA, BB):
            arr[hole] = shift(arr, 1, 0)[hole]
    lev += (fbm(np.arange(W)[None, :] / 9.0 + 0 * lev, np.arange(H)[:, None] / 3.0 + 0 * lev, 61 + seed, 2) - 0.5) * 0.05

    img = np.zeros((H, W, 4), np.uint8)
    top = surf == 1
    front = surf == 2
    pip = surf == 3
    Yg = np.arange(H)[:, None] + 0.5 + 0 * lev
    Xg = np.arange(W)[None, :] + 0.5 + 0 * lev
    # seam row per column (first front pixel)
    seam_row = np.full(W, -1, np.int32)
    for x in range(W):
        col = np.nonzero(pip[:, x] | front[:, x])[0]
        if col.size:
            seam_row[x] = col.min()
    front_row = np.where(seam_row[None, :] >= 0, np.floor(Yg).astype(np.int32) - seam_row[None, :], -99)

    s = U.copy()
    t = np.where(top, V * cg.sinp * TS, (cg.z_s - Z) * cg.cosp + 40.0)

    def proj(ss, tt_):
        # top surface only: invert (s, t) -> (A, B) -> screen
        vv = tt_ / (cg.sinp * TS)
        Aq = ss / cg.hw
        Bq = vv / cg.hd
        for _ in range(3):
            Aq = ss / (cg.hw * (1 + cg.bulge * (1 - Bq * Bq)))
            Bq = vv / (cg.hd * (1 + cg.bulge * (1 - Aq * Aq)))
        if abs(Aq) > 0.97 or abs(Bq) > 0.97:
            return None
        xw, yw, z = cg.P(np.array(Aq), np.array(Bq), 1)
        X, Y, _ = cg.screen(xw, yw, z)
        xi_, yi_ = int(math.floor(X)), int(math.floor(Y))
        if 0 <= xi_ < W and 0 <= yi_ < H and surf[yi_, xi_] == 1:
            return (float(X), float(Y))
        return None

    def seam_y(x):
        xi_ = int(math.floor(x))
        if 0 <= xi_ < W and seam_row[xi_] >= 0:
            return float(seam_row[xi_])
        return None

    fab_m = top | front
    fab = Fab(fab_m, s, t, lev.copy(), top, proj, design, seed)
    # emblem position on the top surface in front of the stand
    exw, eyw, ez = cg.P(np.array(0.0), np.array(0.62), 1)
    ex_, ey_, _ = cg.screen(exw, eyw, ez)
    fab.extra.update(dict(kind='cushion', cg=cg, top=top, front=front, front_row=front_row, seam_y=seam_y,
                          cx=cg.cx, half_w=cg.hw, emblem_y=float(ey_), X=Xg, Y=Yg, A=AA, B=BB, mini=cg.mini))
    design['pattern'](fab)

    ramps = [ramp_arr(design['base'])] + [ramp_arr(r) for r in design.get('alt', [])]
    dith = design.get('dither', 0.45) * 0.7
    for k, r in enumerate(ramps):
        mk = fab_m & (fab.sel == k)
        if mk.any():
            idx = quantize(fab.lev, len(r), dith)
            img[mk, :3] = r[idx[mk]]
            img[mk, 3] = 255
    ovm = fab.ov[..., 3] > 0
    img[ovm] = fab.ov[ovm]
    pr = ramp_arr(design.get('piping', design['trim']))
    pi_ = np.clip(np.round(lev * (len(pr) - 1)), 0, len(pr) - 1).astype(np.int32)
    img[pip, :3] = pr[pi_[pip]]
    img[pip, 3] = 255

    # outline + corner tassels
    body = img[..., 3] > 0
    oc = hexc(design.get('out', design['base'][0]))
    tas = design.get('tassel', design['fringe'])
    tcm = TASSEL_M if not cg.mini else TASSEL_S
    corners = []
    for (ca, cb) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        xw, yw, z = cg.P(np.array(ca * 1.0), np.array(cb * 1.0), 1)
        X, Y, _ = cg.screen(xw + ca * 1.0, yw, z)
        corners.append((ca, cb, float(X), float(Y)))
    # back tassels behind the body
    timg = np.zeros_like(img)
    for (ca, cb, X, Y) in corners:
        if cb < 0:
            draw_sprite_lev(timg, tcm, int(X) - tcm.shape[1] // 2 + ca, int(Y) - 1, tas, base_lev=0.42,
                            outline=design.get('tassel_out'))
    e = edge_out(body)
    img[e] = oc
    tm = (timg[..., 3] > 0) & (img[..., 3] == 0)
    img[tm] = timg[tm]
    for (ca, cb, X, Y) in corners:
        if cb > 0:
            draw_sprite_lev(img, tcm, int(X) - tcm.shape[1] // 2 + ca, int(Y) - 1, tas, base_lev=0.56,
                            outline=design.get('tassel_out'))
    return img


# ================================================================ the cloth
def fold_fn(s):
    a = 2 * math.pi
    F = 0.58 * np.sin(a * s / 27.0 + 0.3) + 0.30 * np.sin(a * s / 15.5 + 2.1) + 0.12 * np.sin(a * s / 9.1 + 0.9)
    Fd = (0.58 * a / 27.0 * np.cos(a * s / 27.0 + 0.3) + 0.30 * a / 15.5 * np.cos(a * s / 15.5 + 2.1)
          + 0.12 * a / 9.1 * np.cos(a * s / 9.1 + 0.9)) * 4.0
    return F, Fd


def render_cloth(design, g, table_img=None, seed=0):
    H, W = g.H, g.W
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W, 0, g.y0)
    Yi = np.floor(Y).astype(np.int32)
    dx = X - g.cx
    ex = dx / g.rx
    xs = np.arange(W) + 0.5 - g.cx
    edge_c = g.edge_y(xs)
    e_row = np.floor(edge_c).astype(np.int32)
    E0 = e_row[None, :]
    in_table = ((ex ** 2 + ((Y - g.cy) / g.ry) ** 2 <= 1.0) | (Yi == E0)) & (Yi <= E0) & (np.abs(ex) <= 1.0)
    d_c, rho_c = ell_dist(X, Y, g.cx, g.ccy, g.rc, g.cry)
    top = in_table & (rho_c <= 1.0)
    drop_c = g.drop(xs)
    s_arc = g.rx * np.arcsin(np.clip(xs / g.rx, -1, 1))
    F, Fd = fold_fn(s_arc)
    hang = np.clip(drop_c / 9.0, 0, 1)
    wave = np.where(drop_c > 0, (0.9 * F + 0.4) * hang, 0)
    hem_row = e_row + np.floor(drop_c + wave + 0.5).astype(np.int32)
    has_drape = drop_c > 1.0
    E = e_row[None, :]
    HR = hem_row[None, :]
    drape = has_drape[None, :] & (Yi > E) & (Yi <= HR)
    w_rows = (Yi - E).astype(np.float32)

    # ------------------------------------------------ lighting levels
    lev = np.zeros((H, W), np.float32)
    lt = 0.60 + 0.07 * np.exp(-(dx / 110.0) ** 2) - 0.22 * np.clip((rho_c - 0.72) / 0.28, 0, 1) ** 2
    lt += (fbm(X / 40.0, Y / 5.0, 11 + seed, 1) - 0.5) * 0.05
    lt -= 0.10 * np.clip((np.abs(ex) - 0.45) / 0.25, 0, 1)
    if g.cushion is not None:
        ccx, ccy2, crx, cry = g.cushion
        e = ((X - ccx) / crx) ** 2 + ((Y - ccy2) / cry) ** 2
        lt = np.where(e < 1.0, lt - 0.30, lt)
        lt = np.where((e >= 1.0) & (e < 1.45), lt - 0.16, lt)
        lt = np.where((e >= 1.45) & (e < 2.0), lt - 0.06, lt)
    amp = 0.30 + 0.70 * np.clip(w_rows / 18.0, 0, 1)
    ld = 0.53 + 0.05 * np.exp(-(dx / 110.0) ** 2) - 0.10 * np.clip(w_rows / 28.0, 0, 1)
    ld = ld + amp * (0.19 * F[None, :] - 0.06 * Fd[None, :])
    ld -= 0.14 * np.clip((np.abs(ex) - 0.40) / 0.2, 0, 1)
    ld = np.where(w_rows == 1, ld + 0.26, ld)
    ld = np.where(w_rows == 2, ld + 0.10, ld)
    ld = np.where(w_rows == 3, ld - 0.08, ld)
    ld = np.where(w_rows == 4, ld - 0.04, ld)
    lev = np.where(top, lt, np.where(drape, ld, 0.5)).astype(np.float32)

    # ------------------------------------------------ fabric coordinates
    edge_full = g.edge_y(dx)
    s = np.where(top, dx, s_arc[None, :] * np.ones((H, 1), np.float32))
    t_edge = (edge_full - g.ccy) * TS
    t = np.where(top, (Y - g.ccy) * TS, t_edge + (Y - edge_full))

    trim_flat = top & (d_c < 1.5)
    trim_hem = drape & (HR - Yi < 2)
    body = (top | drape) & ~trim_flat & ~trim_hem

    def proj(ss, tt):
        xt = g.cx + ss
        if abs(ss) < g.rx:
            ey_ = g.cy + g.ry * math.sqrt(max(0.0, 1 - (ss / g.rx) ** 2))
            te = (ey_ - g.ccy) * TS
            if tt <= te:
                return (xt, g.ccy + tt / TS - g.y0)
            # drape
            xd = g.cx + g.rx * math.sin(max(-1.5, min(1.5, ss / g.rx)))
            ey2 = g.cy + g.ry * math.sqrt(max(0.0, 1 - ((xd - g.cx) / g.rx) ** 2))
            te2 = (ey2 - g.ccy) * TS
            return (xd, ey2 + (tt - te2) - g.y0)
        return None

    fab = Fab(body, s, t, lev, top, proj, design, seed)
    fab.extra.update(dict(kind='cloth', g=g, drape=drape, top=top, hem_row=hem_row, e_row=e_row,
                          w_rows=w_rows, X=X, Y=Y, rho_c=rho_c, d_c=d_c, s_arc=s_arc, drop=drop_c, mini=g.mini))
    design['pattern'](fab)

    # ------------------------------------------------ paint body
    ramps = [ramp_arr(design['base'])] + [ramp_arr(r) for r in design.get('alt', [])]
    dith = design.get('dither', 0.3)
    for k, r in enumerate(ramps):
        mk = body & (fab.sel == k)
        if mk.any():
            idx = quantize(fab.lev, len(r), dith, 0, g.y0)
            img[mk, :3] = r[idx[mk]]
            img[mk, 3] = 255
    ovm = fab.ov[..., 3] > 0
    img[ovm] = fab.ov[ovm]

    # ------------------------------------------------ trims
    trim = ramp_arr(design['trim'])
    nt = len(trim)
    tl = np.where(trim_hem, np.where(HR - Yi == 1, 0.78, 0.48), 0.62)
    tl = tl + 0.12 * np.exp(-(dx / 120.0) ** 2) - 0.25 * np.clip((np.abs(ex) - 0.4) / 0.3, 0, 1)
    tl = np.where(trim_flat & (d_c < 1.0), tl - 0.22, tl)
    tl = np.where(trim_hem, tl + 0.10 * F[None, :], tl)
    if design.get('trim_pattern', True):
        stud = (np.mod(np.floor(np.where(top, X, s_arc[None, :] + 1000)), 5) == 0)
        tl = np.where(trim_hem & stud & (HR - Yi == 1), tl + 0.16, tl)
    ti = np.clip(np.round(tl * (nt - 1)), 0, nt - 1).astype(np.int32)
    tm = trim_flat | trim_hem
    img[tm, :3] = trim[ti[tm]]
    img[tm, 3] = 255

    # ------------------------------------------------ fringe hanging from the hem
    fr = ramp_arr(design['fringe'])
    nf = len(fr)
    flen_base = design.get('fringe_len', 5) if not g.mini else 3
    fringe_mask = np.zeros((H, W), bool)
    for xcol in range(W):
        if not has_drape[xcol] or drop_c[xcol] < 1.5:
            continue
        h1 = float(hash01(xcol, 7, 3 + seed))
        L = flen_base + (1 if h1 > 0.72 else 0) - (1 if h1 < 0.18 else 0)
        for j in range(1, L + 1):
            yy = hem_row[xcol] - g.y0 + j
            if 0 <= yy < H:
                base = 0.62 if (xcol % 2 == 0) else 0.46
                lvv = base - 0.07 * j + 0.10 * math.exp(-((xcol + 0.5 - g.cx) / 120.0) ** 2)
                lvv -= 0.2 * max(0.0, (abs(xcol + 0.5 - g.cx) / g.rx - 0.4) / 0.3)
                if j == L:
                    lvv -= 0.12
                k = int(np.clip(round(lvv * (nf - 1)), 0, nf - 1))
                img[yy, xcol, :3] = fr[k]
                img[yy, xcol, 3] = 255
                fringe_mask[yy, xcol] = True
    # flat fringe lying on the wood around the cloth edge
    ff = in_table & (d_c <= 0.0) & (d_c > -1.6) & ~drape & (Yi <= E)
    Xi = np.floor(X).astype(np.int64)
    fl = 0.46 + 0.12 * (np.mod(Xi, 2) == 0) - 0.10 * np.clip(np.abs(ex) - 0.5, 0, 1)
    fi = np.clip(np.round(fl * (nf - 1)), 0, nf - 1).astype(np.int32)
    img[ff, :3] = fr[fi[ff]]
    img[ff, 3] = 255
    fringe_mask |= ff
    shadow_ring = in_table & (d_c <= -1.6) & (d_c > -2.7) & ~drape & (Yi <= E)

    # ------------------------------------------------ tassels on the hem
    tas_ramp = design.get('tassel', design['fringe'])
    period = design.get('tassel_period', 27.0) if not g.mini else 14.0
    hw = g.drape_half_width()
    smax = g.rx * math.asin(min(1.0, hw / g.rx))
    k0 = int(math.floor(-smax / period))
    tcm = TASSEL if not g.mini else TASSEL_S
    for kk in range(k0, -k0 + 1):
        sv = (kk + 0.5 * design.get('tassel_phase', 0)) * period
        xv = g.cx + g.rx * math.sin(sv / g.rx)
        xc = int(math.floor(xv))
        if not (0 <= xc < W) or drop_c[xc] < (7 if not g.mini else 5):
            continue
        top_y = hem_row[xc] - g.y0 - 1
        draw_sprite_lev(img, tcm, xc - tcm.shape[1] // 2, top_y, tas_ramp,
                        base_lev=0.55 + 0.08 * math.exp(-((xv - g.cx) / 120.0) ** 2), outline=design.get('tassel_out'))
        fringe_mask[max(0, top_y):top_y + tcm.shape[0], max(0, xc - 4):xc + 5] |= True

    # ------------------------------------------------ outline + shadows
    cloth_m = (top | drape)
    out_c = design.get('out', design['base'][0])
    ol = edge_out(cloth_m) & ~fringe_mask & (img[..., 3] == 0) & (Yi > E)
    img[ol] = hexc(out_c)
    # dark line between the flat cloth edge and the wood (its thickness/shadow)
    img[shadow_ring & (img[..., 3] == 0)] = hexc(design.get('shadow', '#120709'))
    if table_img is not None:
        # cast shadow of the drape on the table front (only where the table is visible below the fringe)
        below = np.zeros((H, W), bool)
        for xcol in range(W):
            if not has_drape[xcol] or drop_c[xcol] < 1.0:
                continue
            y1 = hem_row[xcol] - g.y0 + flen_base + 1
            below[max(0, y1):min(H, y1 + 2), xcol] = True
        sh = below & (img[..., 3] == 0) & (table_img[..., 3] > 0)
        img[sh, :3] = (table_img[sh, :3].astype(np.float32) * 0.55).astype(np.uint8)
        img[sh, 3] = 255
    return img


# ================================================================ shop thumbnail
THUMB_W, THUMB_H = 96, 64


def thumb_background():
    """opaque dark violet backdrop with a soft warm glow behind the cushion (own art, not the game's)."""
    from scene_lib import grid as _grid
    X, Y = _grid(THUMB_H, THUMB_W)
    r = np.hypot((X - 48) / 58.0, (Y - 22) / 40.0)
    lev = np.clip(1.0 - r, 0, 1) ** 1.4
    ramp = ramp_arr(['#07040b', '#0e0714', '#160a1e', '#200e28', '#2c1230', '#381636'])
    idx = quantize(lev * 0.95, len(ramp), 0.6)
    img = np.zeros((THUMB_H, THUMB_W, 4), np.uint8)
    img[..., :3] = ramp[idx]
    img[..., 3] = 255
    return img


def render_thumb(design, seed=0):
    """96x64 shop preview: a small round table with the cloth and the matching cushion."""
    from scene_lib import alpha_over
    from scene_table import render_table
    g = TableGeo(W=THUMB_W, H=THUMB_H, y0=0, cx=48.0, cy=21.0, rx=50.0, ry=13.0, top_t=3, apron_in=4.0,
                 apron_h=3, leg_dx=40.0, rc=43.0, shift=25.0, ts=2.2, cushion=(48.0, 26.5, 25.0, 5.0),
                 shadows=(), legs=False, mini=True)
    img = thumb_background()
    table = render_table(g)
    cloth = render_cloth(design, g, table, seed=seed)
    cg = CushionGeo(W=THUMB_W, H=THUMB_H, cx=48.0, cyf=26.0, hw=24.0, hd=21.0, bulge=-0.08, phi=18.0,
                    z_s=4.0, ht=8.0, hb=4.0, p=0.85, dent_r=1.0, dent=0.0, bow=0.05, mini=True)
    cush = render_cushion(design, cg, seed=seed)
    alpha_over(img, table, 0, 0)
    alpha_over(img, cloth, 0, 0)
    alpha_over(img, cush, 0, 0)
    img[..., 3] = 255
    return img
