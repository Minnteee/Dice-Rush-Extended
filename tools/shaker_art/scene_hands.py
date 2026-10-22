"""The fortune teller's arms (no face, no body): left arm + hand, 2 frames; the
right arm is the mirror image.

Sprite 112x88.  The left hand box sits at (56,62) in the 480x270 scene; the
ball's left edge (x=176 at its equator) is then at local x=120.  The hand is a
left hand seen from the back: fingers spread in a fan pointing up/right towards
the ball, thumb towards the ball, palm facing the ball.  The wide bell sleeve
comes from the left and dissolves into dark smoke at its far end (so the arm
never shows a hard cut, even when the game slides it a few px).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from scene_lib import (grid, ramp_arr, hexc, edge_out, edge_in, dilate, erode, seg_field, bayer, fbm,
                       vnoise, flip_h, shift)
from scene_table import GOLD

W, H = 112, 88
SS = 3

SKIN = ['#2a1218', '#57283a', '#7f3f4c', '#a65c62', '#c87f7c', '#e0a495', '#f0c6b0', '#fbe3d0']
SKIN_OUT = '#1e0b15'
NAIL = ['#1e0618', '#4a1240', '#7a2266', '#a8408e', '#d27ab8']
SLEEVE = ['#08030e', '#100618', '#190a24', '#240e32', '#311443', '#3f1b56', '#4f246a', '#62307e', '#7a4296']
SLEEVE_OUT = '#050208'
LINING = ['#0a0310', '#170726', '#260c3a']
LACE = ['#2c2232', '#5a4e62', '#8e8298', '#bcb2c4', '#ddd6e2', '#f4f0f6']
GEMS = {'ruby': ['#4a0610', '#9a1028', '#e0304a', '#ff9aaa'],
        'emerald': ['#06301a', '#0e6a38', '#24b060', '#9af0b8'],
        'amethyst': ['#28083e', '#5e1c92', '#a058ea', '#e4c4ff'],
        'sapphire': ['#081438', '#163a8e', '#3a70e8', '#a8c8ff']}

LIGHT = np.array([0.70, -0.45, 0.56])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def deg(a):
    return math.radians(a)


def lvl_to(ramp, lev):
    r = ramp_arr(ramp)
    return r[np.clip(np.round(lev * (len(r) - 1)), 0, len(r) - 1).astype(np.int32)]


# fine grid for supersampled coverage
XF, YF = grid(H * SS, W * SS)
XF, YF = XF / SS, YF / SS
XN, YN = grid(H, W)


def coverage(fine_mask, thr=0.5):
    c = fine_mask.reshape(H, SS, W, SS).mean(axis=(1, 3))
    return c >= thr


def poly_cov(pts, thr=0.5):
    img = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(img).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return coverage(np.array(img) > 0, thr)


def smooth_poly(pts, n=8):
    """Catmull-Rom smoothing of a closed polygon."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


class Chain:
    """tapered capsule chain (finger / thumb / forearm)."""

    def __init__(self, x0, y0, angles, lengths, r0, r1):
        self.pts = [(x0, y0)]
        for a, l in zip(angles, lengths):
            px, py = self.pts[-1]
            self.pts.append((px + l * math.cos(deg(a)), py + l * math.sin(deg(a))))
        self.angles, self.lengths, self.r0, self.r1 = angles, lengths, r0, r1
        self.total = sum(lengths)

    def fields(self, X, Y):
        best = np.full(X.shape, 1e9, np.float32)
        cc = np.zeros(X.shape, np.float32)
        along = np.zeros(X.shape, np.float32)
        seg = np.zeros(X.shape, np.int32)
        inside = np.zeros(X.shape, bool)
        acc = 0.0
        for i, l in enumerate(self.lengths):
            (ax, ay), (bx, by) = self.pts[i], self.pts[i + 1]
            d, t, side = seg_field(X, Y, ax, ay, bx, by)
            al = acc + t * l
            r = self.r0 + (self.r1 - self.r0) * (al / self.total)
            q = d / np.maximum(r, 0.1)
            better = q < best
            best = np.where(better, q, best)
            cc = np.where(better, np.clip(side / np.maximum(r, 0.1), -1, 1), cc)
            along = np.where(better, al, along)
            seg = np.where(better, i, seg)
            inside |= d <= r
            acc += l
        return inside, cc, along, seg

    def mask(self):
        m, _, _, _ = self.fields(XF, YF)
        return coverage(m)

    def tip(self):
        return self.pts[-1]


def cyl_level(c, angle, base=0.22, gain=0.64):
    """shading of a cylinder with axis direction 'angle': c = side coordinate as returned by
    seg_field (positive towards the normal (-dy, dx) of the axis direction)."""
    a = deg(angle)
    lx, ly = -math.sin(a), math.cos(a)
    nx = c * lx
    ny = c * ly
    nz = np.sqrt(np.clip(1 - c * c, 0, 1))
    return base + gain * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)


HAND_POSES = [
    dict(index=(-31, -22, -11), middle=(-52, -43, -32), ring=(-72, -64, -54), pinky=(-93, -85, -75),
         thumb=(14, -6), spread=0.0),
    dict(index=(-35, -25, -12), middle=(-50, -40, -28), ring=(-75, -66, -55), pinky=(-98, -89, -78),
         thumb=(18, -2), spread=0.6),
]


def render_left_hand(frame=0, seed=0):
    pose = HAND_POSES[frame]
    X, Y = XN, YN
    img = np.zeros((H, W, 4), np.uint8)
    owner = np.zeros((H, W), np.int32)

    def put(mask, rgb, pid):
        img[mask, :3] = rgb[mask] if rgb.ndim == 3 else rgb
        img[mask, 3] = 255
        owner[mask] = pid

    # ------------------------------------------------------------ skeleton
    S = 1.36                                        # overall hand scale
    RS = S / 1.18                                   # radius scale (radii were tuned at S = 1.18)
    OX = -7.5                                       # sleeve shift (makes room for the bigger hand)
    Wr = np.array([68.0, 59.5])                     # wrist centre
    hand_dir = -50.0
    d = np.array([math.cos(deg(hand_dir)), math.sin(deg(hand_dir))])
    p = np.array([math.cos(deg(hand_dir + 90)), math.sin(deg(hand_dir + 90))])   # towards thumb side
    K = Wr + 14.0 * S * d                           # knuckle line centre
    cuff = np.array([63.5 + OX, 59.5])              # where the forearm leaves the sleeve
    fore_dir = math.degrees(math.atan2(Wr[1] - cuff[1], Wr[0] - cuff[0]))
    fd = np.array([math.cos(deg(fore_dir)), math.sin(deg(fore_dir))])

    # ------------------------------------------------------------ forearm + bracelets
    fa = Chain(cuff[0] - 6, cuff[1], [fore_dir], [np.linalg.norm(Wr - cuff) + 8.5], 5.2 * RS, 4.4 * RS)
    fa_m = fa.mask()
    _, fa_c, fa_al, _ = fa.fields(X, Y)
    put(fa_m, lvl_to(SKIN, cyl_level(fa_c, fore_dir) - 0.05), 10)
    rel = (X - cuff[0]) * fd[0] + (Y - cuff[1]) * fd[1]
    across = -(X - cuff[0]) * fd[1] + (Y - cuff[1]) * fd[0]
    for (pos, wd, kind_) in ((7.4, 1.2, 'gold'), (10.0, 1.2, 'gold'), (12.2, 0.8, 'thin')):
        band = fa_m & (np.abs(rel - pos) <= wd / 2 + 0.3)
        cl = np.clip(fa_c, -1, 1)
        col = lvl_to(GOLD, 0.50 - 0.34 * cl + (0.12 if kind_ == 'thin' else 0))
        put(band, col, 11)
        # bangles stand out of the arm by a pixel on the lower side
        under = edge_out(band) & ~fa_m & (np.abs(rel - pos) <= wd / 2) & (across > 0)
        put(under, lvl_to(GOLD, np.full(X.shape, 0.30)), 11)
    # one amethyst bead on the middle bangle
    bead = fa_m & (np.abs(rel - 10.0) <= 1.0) & (np.abs(across + 0.2) <= 1.0)
    put(bead, lvl_to(GEMS['amethyst'], np.where(across < -0.2, 0.9, 0.55)), 12)

    # ------------------------------------------------------------ thumb (behind the palm)
    tb = Wr + 4.6 * S * p + 2.4 * d
    th = Chain(tb[0], tb[1], pose['thumb'], [5.6 * S, 4.4 * S], 3.4 * RS, 2.5 * RS)
    th_m = th.mask()
    _, th_c, th_al, th_seg = th.fields(X, Y)
    th_lev = cyl_level(th_c, pose['thumb'][0]) - 0.03
    th_lev = np.where(np.abs(th_al - 5.6 * S) < 0.6, th_lev - 0.07, th_lev)
    put(th_m, lvl_to(SKIN, th_lev), 20)
    # thumb nail
    tt = np.array(th.tip())
    ta = deg(pose['thumb'][-1])
    tdir = np.array([math.cos(ta), math.sin(ta)])
    tn = Chain(tt[0] - 2.8 * tdir[0], tt[1] - 2.8 * tdir[1], [pose['thumb'][-1]], [4.0 * RS], 1.7 * RS, 0.6)
    tn_m = tn.mask() & ~dilate(np.zeros_like(th_m), 0)
    _, tn_c, tn_al, _ = tn.fields(X, Y)
    tn_m &= tn_al > 0.6
    put(tn_m, lvl_to(NAIL, 0.5 - 0.3 * tn_c), 21)

    # ------------------------------------------------------------ palm / back of the hand
    c1 = Wr - 5.2 * RS * p - 0.5 * d
    c2 = Wr + 5.4 * RS * p - 0.5 * d
    c3 = K + 7.6 * S * p + 0.6 * d
    c4 = K - 7.8 * S * p - 0.2 * d
    palm_pts = smooth_poly([tuple(c1), tuple(Wr + 6.4 * S * p + 7 * d), tuple(c3), tuple(K + 2.2 * d),
                            tuple(c4), tuple(Wr - 6.6 * S * p + 7 * d)], 6)
    palm = poly_cov(palm_pts)
    rp = np.stack([X - Wr[0], Y - Wr[1]], -1)
    pp = (rp @ p) / (8.0 * S)
    dd = (rp @ d) / (14.0 * S)
    nx = pp * p[0] * 0.6 + (dd - 0.55) * d[0] * 0.5
    ny = pp * p[1] * 0.6 + (dd - 0.55) * d[1] * 0.5
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    plev = 0.20 + 0.66 * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    put(palm, lvl_to(SKIN, plev), 30)

    # ------------------------------------------------------------ fingers
    specs = [('pinky', -6.2, [6.0, 4.4, 3.6], 2.2, 1.55, 41),
             ('ring', -2.1, [7.6, 5.4, 4.4], 2.5, 1.7, 42),
             ('middle', 2.1, [8.2, 5.8, 4.8], 2.6, 1.75, 43),
             ('index', 6.1, [7.4, 5.2, 4.4], 2.5, 1.7, 44)]
    fing = {}
    for (name, cpos, lens, r0, r1, pid) in specs:
        lens = [l_ * S for l_ in lens]
        cpos = cpos * S
        base = K + cpos * p - 2.0 * d + pose['spread'] * cpos * 0.08 * p
        angs = pose[name]
        ch = Chain(base[0], base[1], angs, lens, r0 * RS, r1 * RS)
        m = ch.mask()
        _, c, al, sg = ch.fields(X, Y)
        segdir = np.choose(np.clip(sg, 0, 2), angs)
        lev = 0.22 + 0.64 * np.clip(0, 0, 0) + 0 * c
        for i, a in enumerate(angs):
            lev = np.where(sg == i, cyl_level(c, a), lev)
        j1, j2 = lens[0], lens[0] + lens[1]
        lev = np.where((np.abs(al - 1.8) < 1.3) & (c > -0.3), lev + 0.06, lev)      # knuckle
        lev = np.where((np.abs(al - j1) < 0.5) & (np.abs(c) < 0.5), lev - 0.05, lev)  # joint crease
        lev = np.where((np.abs(al - j2) < 0.45) & (np.abs(c) < 0.4), lev - 0.04, lev)
        col = lvl_to(SKIN, lev)
        # long painted nail: last 3 px + a pointed tip beyond the finger
        tip = np.array(ch.tip())
        ta = deg(angs[-1])
        tdir = np.array([math.cos(ta), math.sin(ta)])
        nc = Chain(tip[0] - 3.0 * tdir[0], tip[1] - 3.0 * tdir[1], [angs[-1]], [4.6 * RS], r1 * RS * 0.95, 0.5)
        nm = nc.mask()
        _, ncc, nal, _ = nc.fields(X, Y)
        nail = nm & (nal > 0.5)
        ncol = lvl_to(NAIL, 0.48 - 0.32 * ncc + 0.2 * ((ncc < -0.1) & (nal < 2.6)))
        fm = m | nail
        col = np.where(nail[..., None], ncol, col)
        put(fm, col, pid)
        fing[name] = (ch, m, c, al, lens, angs, pid)

    # ------------------------------------------------------------ rings
    ring_specs = {'index': ('ruby', 4.6 * RS, 1.0), 'ring': ('amethyst', 4.2 * RS, 1.4), 'pinky': (None, 3.4 * RS, 0.8)}
    for name, (gem, pos, wd) in ring_specs.items():
        ch, m, c, al, lens, angs, pid = fing[name]
        band = m & (np.abs(al - pos) <= wd) & (owner == pid)
        put(band, lvl_to(GOLD, 0.55 - 0.32 * np.clip(c, -1, 1)), 60)
        if gem:
            g = GEMS[gem]
            gm = band & (np.abs(c + 0.1) < 0.6)
            gcol = np.zeros(X.shape + (3,), np.uint8)
            gcol[...] = ramp_arr([g[2]])[0]
            gcol[gm & (c < -0.2)] = ramp_arr([g[3]])[0]
            gcol[gm & (c > 0.35)] = ramp_arr([g[1]])[0]
            put(gm, gcol, 61)

    # ------------------------------------------------------------ sleeve (bishop / bell sleeve, side view)
    top_y = lambda x: 42.0 + 7.5 * (np.clip(x - OX, 0, None) / 64.0) ** 1.3
    _sp = [(-8, 41.0), (10, None), (26, None), (42, None), (56, None),
           (64.0, 50.4), (66.6, 54.0), (66.8, 59.5), (65.2, 66.0), (62.6, 73.0), (59.4, 80.0),
           (56.8, 86.5), (55.0, 92.0),
           (44, 91.5), (30, 88.0), (16, 84.5), (2, 82.0), (-8, 81.0)]
    sleeve_pts = [(x + OX, float(top_y(x + OX)) if y is None else y) for (x, y) in _sp]
    sleeve = poly_cov(smooth_poly(sleeve_pts, 6))
    # the opening edge (right side of the sleeve): a curve from the top of the cuff down to the bell tip
    open_curve = [(x + OX, y) for (x, y) in [(64.0, 50.4), (66.6, 54.0), (66.8, 59.5), (65.2, 66.0), (62.6, 73.0),
                                             (59.4, 80.0), (56.8, 86.5), (55.0, 92.0)]]
    oc = np.array(smooth_poly(open_curve + open_curve[::-1][1:-1], 6))[: (len(open_curve) - 1) * 6]

    def dist_to_curve(px, py, curve):
        dmin = np.full(px.shape, 1e9, np.float32)
        side = np.zeros(px.shape, np.float32)
        for i in range(len(curve) - 1):
            (ax, ay), (bx, by) = curve[i], curve[i + 1]
            dd_, t_, s_ = seg_field(px, py, ax, ay, bx, by)
            better = dd_ < dmin
            dmin = np.where(better, dd_, dmin)
            side = np.where(better, s_, side)
        return dmin, side

    dco, sco = dist_to_curve(X, Y, oc)
    dcf, scf = dist_to_curve(XF, YF, oc)
    # lace ruffle: a band right of the opening edge with a scalloped outer border
    tpar = np.clip((Y - 50.0) / 42.0, 0, 1)
    lace_w = 3.4 + 0.8 * np.sin(Y * 1.15) ** 2
    lace_wf = 3.4 + 0.8 * np.sin(YF * 1.15) ** 2
    lace = coverage((scf < 0) & (dcf <= lace_wf)) & ~sleeve
    lace &= ~((owner >= 20) & (owner != 0) & (Y < 58))       # never cover the thumb / hand
    lace_lev = 0.66 - 0.30 * tpar + 0.10 * np.clip((X - 60 - OX) / 8.0, -1, 1)
    holes = (np.mod(np.floor(X) + np.floor(Y) * 2, 4) == 0) & (dco < lace_w - 1.2)
    lace_lev = np.where(holes, lace_lev - 0.32, lace_lev)
    put(lace, lvl_to(LACE, lace_lev), 80)
    # small lining crescent visible inside the lower bell
    lin = sleeve & (sco < 3.6) & (sco > 0.0) & (Y > 66) & (dco < 2.2)
    # sleeve fabric
    sl = sleeve & ~lin
    v_top = Y - top_y(np.clip(X, 0, 70))
    fold_phase = (X * 0.42 - v_top * 0.55) * 0.55 + 1.5 * np.sin(X * 0.09 + 1.0)
    fold = np.sin(fold_phase) * np.clip(v_top / 10.0, 0.25, 1.0)
    slev = 0.44 + 0.13 * fold - 0.20 * np.clip((v_top - 18) / 24.0, 0, 1)
    slev += 0.20 * np.clip(1 - v_top / 3.0, 0, 1)                    # rim light along the top
    slev += 0.10 * np.clip((X - 28) / 30.0, 0, 1)                     # nearer to the glowing ball
    slev += 0.10 * np.clip(1 - dco / 6.0, 0, 1) * (sco > 0)           # the cuff is lit
    scol = lvl_to(SLEEVE, slev)
    # gold embroidery: a band parallel to the opening, a hem band and small stars
    emb = sl & (sco > 0) & (dco >= 1.0) & (dco < 3.6)
    emb_edge = sl & (sco > 0) & (dco >= 3.6) & (dco < 4.5)
    glev = 0.50 + 0.18 * np.clip((60 - Y) / 12.0, -1, 1)
    scallop = np.mod(np.floor(Y), 3) == 0
    scol = np.where(emb[..., None], lvl_to(GOLD, glev + 0.10 * scallop - 0.12 * (np.abs(dco - 3.0) > 1.0)), scol)
    scol = np.where(emb_edge[..., None], lvl_to(GOLD, glev - 0.25), scol)
    # hem band along the lower edge of the bell
    bot = np.array([(55.0 + OX, 92.0), (44 + OX, 91.5), (30 + OX, 88.0), (16 + OX, 84.5), (2 + OX, 82.0), (-8 + OX, 81.0)])
    dbo, sbo = dist_to_curve(X, Y, smooth_poly(list(map(tuple, bot)) + list(map(tuple, bot[::-1][1:-1])), 4)[:5 * 4])
    hem = sl & (dbo < 2.6) & (dbo > 0.9) & (X > 4)
    scol = np.where(hem[..., None], lvl_to(GOLD, 0.40 + 0.25 * np.clip((X - 20) / 30.0, 0, 1)), scol)
    star_pts = [(int(x + OX), y) for (x, y) in [(24, 56), (40, 64), (14, 69), (32, 76), (47, 55), (8, 52), (50, 78), (20, 80)]]
    for (sx, sy) in star_pts:
        arm = sl & (((np.abs(X - sx - 0.5) < 0.6) & (np.abs(Y - sy - 0.5) < 1.6)) |
                    ((np.abs(Y - sy - 0.5) < 0.6) & (np.abs(X - sx - 0.5) < 1.6)))
        ctr = sl & (np.abs(X - sx - 0.5) < 0.6) & (np.abs(Y - sy - 0.5) < 0.6)
        gl = 0.40 + 0.2 * np.clip((sx - 10) / 40.0, 0, 1)
        scol = np.where(arm[..., None], lvl_to(GOLD, np.full(X.shape, gl)), scol)
        scol = np.where(ctr[..., None], lvl_to(GOLD, np.full(X.shape, gl + 0.3)), scol)
    put(sl, scol, 90)
    put(lin, lvl_to(LINING, np.clip(0.3 + (Y - 64) / 40.0, 0, 1)), 70)

    # ------------------------------------------------------------ internal lines + outline
    def sep(back_ids, front_ids, scale):
        bm = np.isin(owner, back_ids)
        fm = np.isin(owner, front_ids)
        line = bm & dilate(fm, 1) & ~fm
        img[line, :3] = (img[line, :3].astype(np.float32) * scale).astype(np.uint8)

    sep([20], [30], 0.62)                       # thumb under the palm
    sep([41], [42], 0.72)
    sep([42], [43], 0.72)
    sep([43], [44], 0.72)
    sep([10, 11], [80, 90, 70], 0.45)           # shadow of the cuff on the arm
    opaque = img[..., 3] > 0
    e = edge_out(opaque)
    img[e] = hexc(SKIN_OUT)
    sl_out = e & dilate(np.isin(owner, [90, 70, 80]), 1) & ~dilate(np.isin(owner, [10, 11, 20, 21, 30, 41, 42, 43, 44]), 1)
    img[sl_out] = hexc(SLEEVE_OUT)

    # ------------------------------------------------------------ dissolve the far end of the sleeve into smoke
    # streaky (horizontally stretched) noise -> the fabric frays into wisps of dark smoke
    n1 = vnoise(X / 9.0, Y / 2.2, 77 + seed)
    n2 = vnoise(X / 4.0 + 3.1, Y / 1.6, 91 + seed)
    keep = (X - 2.0) / 30.0 + (n1 - 0.5) * 0.75 + (n2 - 0.5) * 0.25
    kill = (keep < 0.42) & (X < 40)
    img[kill] = 0
    # remaining pixels fade towards a smoky dark violet
    f = np.clip((44 - X) / 40.0, 0, 1)
    smoke = np.array(hexc('#120818')[:3], np.float32)
    alive = img[..., 3] > 0
    mixf = (0.75 * f ** 1.2)[..., None]
    rgb = img[..., :3].astype(np.float32) * (1 - mixf) + smoke * mixf
    img[..., :3] = np.where(alive[..., None], rgb.astype(np.uint8), img[..., :3])
    # remove the outline where the sleeve dissolves (no hard border inside the smoke)
    dark_ol = alive & (X < 30) & (np.all(img[..., :3] < 24, axis=-1))
    lone = dark_ol & ~erode(alive, 1)
    img[lone & (X < 24)] = 0
    return img


def render_hands():
    out = {}
    for fr in (0, 1):
        a = render_left_hand(fr)
        out['hand_left' + ('' if fr == 0 else '_b')] = a
        out['hand_right' + ('' if fr == 0 else '_b')] = flip_h(a)
    return out
