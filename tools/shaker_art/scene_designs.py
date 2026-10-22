"""The 20 table-cloth / cushion designs of Dice Shaker.

Every design: name_en, name_de, colour ramps (base = 8 shades dark->light,
trim, fringe, tassel, piping, optional alt ramps / motif ramps) and pattern(fab).
pattern() is called for the cloth (fab.extra['kind'] == 'cloth') and for the
cushion (kind == 'cushion') and edits fab.lev / fab.sel / stamps motifs.
All patterns are calm: low contrast tone patterns, sparse motifs, no fine
high-contrast stripes or checkers.
"""
import math

import numpy as np

from scene_lib import vnoise, fbm, hash01, ramp_arr, ellipse_line
from scene_cloth import M, RUNES, Motif, moon_phase, OFF

# ------------------------------------------------------------ shared ramps
GOLD_T = ['#2c1806', '#5a370c', '#8c5c16', '#bd8624', '#e2ad3a', '#f7d46c', '#fff0bc']
GOLD_F = ['#3a2208', '#6a420e', '#9a6618', '#c88f26', '#e8b840', '#fadc7a']
SILVER_T = ['#1a1d2a', '#3a4054', '#646c84', '#949cb4', '#c0c7da', '#e4e9f4', '#ffffff']
SILVER_F = ['#2a2e3e', '#4c5268', '#767e96', '#a0a8be', '#c8cede', '#ecf0f8']
BRONZE_T = ['#1e1008', '#442610', '#6c3e1a', '#965a26', '#bc7a36', '#dca052', '#f4c886']
BRONZE_F = ['#24140a', '#4a2c14', '#70461e', '#966228', '#ba8236', '#d8a456']
COPPER_T = ['#200c06', '#4a1e0c', '#7a3416', '#a84e20', '#d06c2c', '#ec9448', '#fcc07a']
WHITE_T = ['#3a3442', '#6a6276', '#9a92a6', '#c6bfd0', '#e6e0ec', '#f8f4fa', '#ffffff']
WHITE_F = ['#4a4252', '#7a7086', '#a69eb2', '#cec8d8', '#ece8f2', '#ffffff']
GOLD_M = GOLD_T[1:]                  # motif ramps (6 shades)
SILVER_M = SILVER_T[1:]
TEAL_GLOW = ['#0a2a2a', '#145050', '#1e7a76', '#30a8a0', '#5ad4c8', '#a8fff4']
ROSE_RED = ['#3a0610', '#6a0c1c', '#a0182c', '#d0304a', '#f06a7a', '#ffb0b8']
LEAF_G = ['#08240e', '#14401a', '#22602a', '#3a843c', '#5aa858', '#8ccc80']
MOSS_LEAF = ['#0e1a08', '#1a3010', '#2a4a18', '#3e6622', '#56842e', '#76a43e']
EMBER_M = ['#3a0a04', '#7a1c06', '#c03a0a', '#f06a14', '#ffa63a', '#ffe08a']
TERRA_M = ['#2a0c04', '#5a1e0a', '#8a3214', '#b44a20', '#d66a34', '#f08c50']
SKY_M = ['#163a5a', '#2a5a82', '#4a82aa', '#78acd0', '#b0d6ee', '#e8f6ff']
NAVY_M = ['#02061a', '#061038', '#0c1c5a', '#14307e', '#2048a4', '#3a6ac8']
PEA_GOLD = ['#1e2a06', '#3c4e0c', '#627816', '#8ca424', '#b8cc3c', '#e2ee7a']
PEA_TEAL = ['#02262a', '#064a4e', '#0c7270', '#169c92', '#2ac4b2', '#7ae8d8']
MAGENTA_M = ['#1e0624', '#3c0c48', '#62126e', '#8c1e94', '#b836b6', '#e070d8']
RUST_M = ['#3a0e02', '#6a1a04', '#9a2c08', '#c4440e', '#e2601a', '#f4842e']
LACE_G = ['#1e1d24', '#2e2d36', '#42404c', '#5a5866', '#74727f', '#8e8c99']
LEAF_LIGHT = ['#24400e', '#38601a', '#4e8226', '#68a432', '#86c444', '#a8e060']
ACORN = ['#2a1406', '#4a260c', '#704016', '#965c22', '#b87a34', '#d89c4c']


# ------------------------------------------------------------ helpers
def kind(fab):
    return fab.extra.get('kind')


def mini(fab):
    return fab.extra.get('mini', False)


def paint_ov(fab, m, ramp, lev_add=0.0):
    r = ramp_arr(ramp)
    idx = np.clip(np.round((fab.lev + lev_add) * (len(r) - 1)), 0, len(r) - 1).astype(np.int32)
    fab.ov[m, :3] = r[idx[m]]
    fab.ov[m, 3] = 255


def hem_band(fab, k0, k1, ramp, lev=0.0, every=None, phase=0):
    """overlay a band k0..k1 rows above the hem of the drape (cloth) / below the seam (cushion)."""
    e = fab.extra
    Yi = np.floor(e['Y']).astype(np.int32)
    if kind(fab) == 'cloth':
        HR = e['hem_row'][None, :]
        k = HR - Yi
        m = e['drape'] & (k >= k0) & (k <= k1) & (e['drop'][None, :] > k1 + 4)
    else:
        k = e['front_row']
        m = e['front'] & (k >= k0) & (k <= k1)
    m = m & fab.m
    if every:
        X = np.floor(e['X']).astype(np.int32)
        m &= (np.mod(X + phase, every) == 0)
    paint_ov(fab, m, ramp, lev)
    return m


def hem_motifs(fab, motif, k, spacing, ramps, phase=0.0, need=0.9, choose=None):
    """row of motifs centred k rows above the hem (cloth only)."""
    e = fab.extra
    if kind(fab) != 'cloth':
        return
    g = e['g']
    smax = g.rx * math.asin(min(1.0, g.drape_half_width() / g.rx))
    n = int(smax // spacing) + 1
    for i in range(-n, n + 1):
        sv = (i + phase) * spacing
        x = g.cx + g.rx * math.sin(sv / g.rx)
        xc = int(math.floor(x))
        if not (0 <= xc < fab.W):
            continue
        mo = motif if choose is None else choose(i)
        if mo is None:
            continue
        if e['drop'][xc] < k + mo.h / 2 + 3:
            continue
        y = e['hem_row'][xc] - g.y0 - k + 0.5
        fab.stamp(mo, x, y, ramps, need=need, flat=False)


def emblem(fab, motif, ramps, k=None, need=0.9, cushion=True, cloth=True):
    """a single motif in the middle of the drape / in the middle of the cushion top front."""
    e = fab.extra
    if kind(fab) == 'cloth':
        if not cloth or mini(fab):
            return
        g = e['g']
        xc = int(g.cx)
        d = e['drop'][xc]
        y = e['e_row'][xc] - g.y0 + (d * 0.46 if k is None else k)
        fab.stamp(motif, g.cx, y, ramps, need=need, flat=False)
    elif cushion:
        fab.stamp(motif, e['cx'], e['emblem_y'], ramps, need=need, flat=False)


def edge_ring(fab, inset, ramp, lev=0.0, every=None):
    """thin line parallel to the flat cloth edge (cloth only)."""
    if kind(fab) != 'cloth':
        return None
    e = fab.extra
    g = e['g']
    Yi = np.floor(e['Y']).astype(np.int32)
    H, W = fab.m.shape
    ins = inset + 1.5
    line = ellipse_line(H, W, g.cx, g.ccy, g.rc - ins, g.cry - ins * 0.42, 0, g.y0)
    m = line & e['top'] & fab.m & (Yi < e['e_row'][None, :] - 2)
    if every:
        X = np.floor(e['X']).astype(np.int32)
        m &= np.mod(X, every) == 0
    paint_ov(fab, m, ramp, lev)
    return m


def scatter(fab, motif, ds, dt, ramps, seed=1, prob=1.0, jitter=0.6, need=0.75, choose=None, top_only=False):
    region = None
    if top_only and kind(fab) == 'cloth':
        top = fab.extra['top']
        region = lambda x, y: (0 <= int(y) < fab.H and 0 <= int(x) < fab.W and top[int(y), int(x)])
    fab.scatter(motif, ds, dt, ramps, seed=seed, jitter=jitter, prob=prob, need=need, choose=choose, region=region)


def stars(fab, ramps, density=1.0, seed=3, big=True):
    scatter(fab, M['dot'], 12 / density, 10 / density, ramps, seed=seed, jitter=0.9, prob=0.5)
    scatter(fab, M['star3'], 27 / density, 21 / density, ramps, seed=seed + 7, jitter=0.8, prob=0.75)
    if big:
        scatter(fab, M['star5'], 58 / density, 40 / density, ramps, seed=seed + 13, jitter=0.6, prob=0.8)


def tone_lattice(fab, period, amp, width=0.09):
    u = (fab.s + fab.t) / period
    v = (fab.s - fab.t) / period
    du = np.abs(u - np.round(u))
    dv = np.abs(v - np.round(v))
    fab.tone(((du < width) | (dv < width)).astype(np.float32), amp)


def voronoi_edge(s, t, cell, seed):
    gx0, gx1 = int(np.floor(s.min() / cell)) - 1, int(np.ceil(s.max() / cell)) + 1
    gy0, gy1 = int(np.floor(t.min() / cell)) - 1, int(np.ceil(t.max() / cell)) + 1
    d1 = np.full(s.shape, 1e9, np.float32)
    d2 = np.full(s.shape, 1e9, np.float32)
    for j in range(gy0, gy1 + 1):
        for i in range(gx0, gx1 + 1):
            px = (i + 0.15 + 0.7 * float(hash01(i, j, seed))) * cell
            py = (j + 0.15 + 0.7 * float(hash01(i, j, seed + 7))) * cell
            d = np.sqrt((s - px) ** 2 + (t - py) ** 2)
            upd = d < d1
            d2 = np.where(upd, d1, np.minimum(d2, d))
            d1 = np.where(upd, d, d1)
    return (d2 - d1) * 0.5


# small extra motifs
FLEUR = Motif("""
..X..
.XXX.
X.X.X
..X..
.X.X.
""")
SCALE_DOT = Motif('X')
SUN_BIG = Motif("""
......3......
...3..4..3...
....3.4.3....
.....444.....
..3.45554.3..
...4555554...
3445555555443
...4555554...
..3.45554.3..
.....444.....
....3.4.3....
...3..4..3...
......3......
""")
KILIM = Motif("""
...3...
..343..
.34x43.
34xxx43
.34x43.
..343..
...3...
""")
LACE_FLOWER = Motif("""
..3.3..
.3.4.3.
3.444.3
.44.44.
3.444.3
.3.4.3.
..3.3..
""")
PEACOCK = Motif("""
....A....
...ABA...
..ABCBA..
.ABC2CBA.
.AC232CA.
AB23b32BA
AB2bab2BA
AB23b32BA
.AC232CA.
.ABC2CBA.
..ABCBA..
...ABA...
....A....
....A....
....A....
""")
PEACOCK_S = Motif("""
..A..
.ABA.
AB2BA
B2b2B
AB2BA
.ABA.
..A..
..A..
""")
ACORN_M = Motif("""
.AAA.
ABBBA
.333.
.343.
..3..
""")
MEDALLIONS = []


def _medallion(inner):
    frame = [
        "...oooo...",
        "..o3443o..",
        ".o4....4o.",
        "o4......4o",
        "o3......3o",
        "o3......3o",
        "o3......3o",
        "o4......4o",
        ".o4....4o.",
        "..o3443o..",
        "...oooo...",
    ]
    rows = [list(r) for r in frame]
    for (y, x, ch) in inner:
        rows[y][x] = ch
    return Motif('\n'.join(''.join(r) for r in rows))


# eye, sun, moon, star inside oval frames (inner chars: digits = gold, A.. = second ramp)
MEDALLIONS.append(_medallion([(4, 3, 'A'), (4, 4, 'B'), (4, 5, 'B'), (4, 6, 'A'), (5, 2, 'A'), (5, 3, 'B'), (5, 4, 'O'),
                              (5, 5, 'O'), (5, 6, 'B'), (5, 7, 'A'), (6, 3, 'A'), (6, 4, 'B'), (6, 5, 'B'), (6, 6, 'A')]))
MEDALLIONS.append(_medallion([(3, 4, '3'), (3, 5, '3'), (4, 3, '4'), (4, 4, '5'), (4, 5, '5'), (4, 6, '4'), (5, 2, '3'),
                              (5, 3, '5'), (5, 4, '5'), (5, 5, '5'), (5, 6, '5'), (5, 7, '3'), (6, 3, '4'), (6, 4, '5'),
                              (6, 5, '5'), (6, 6, '4'), (7, 4, '3'), (7, 5, '3')]))
MEDALLIONS.append(_medallion([(3, 4, '4'), (3, 5, '4'), (4, 3, '4'), (4, 4, '5'), (5, 3, '4'), (5, 4, '5'), (6, 3, '4'),
                              (6, 4, '5'), (7, 4, '4'), (7, 5, '4')]))
MEDALLIONS.append(_medallion([(3, 5, '4'), (4, 4, '4'), (4, 5, '5'), (4, 6, '4'), (5, 2, '3'), (5, 3, '4'), (5, 4, '5'),
                              (5, 5, '5'), (5, 6, '5'), (5, 7, '4'), (6, 4, '4'), (6, 5, '5'), (6, 6, '4'), (7, 3, '3'),
                              (7, 7, '3')]))


# ============================================================== patterns
def p_royal(fab):
    hem_band(fab, 3, 3, GOLD_M, 0.05)
    hem_motifs(fab, M['star5'], 8, 18, [GOLD_M], phase=0.5)
    hem_motifs(fab, M['dot'], 8, 18, [GOLD_M], phase=0.0)
    emblem(fab, M['moonstar_l'], [GOLD_M])
    edge_ring(fab, 3.0, GOLD_M, -0.05)
    if kind(fab) == 'cushion':
        scatter(fab, M['star3'], 26, 20, [GOLD_M], seed=5, prob=0.6)


def p_midnight(fab):
    stars(fab, [SILVER_M], 1.0, seed=11)
    hem_band(fab, 3, 3, SILVER_M, -0.05)
    hem_band(fab, 6, 6, SILVER_M, -0.2, every=3)
    edge_ring(fab, 3.0, SILVER_M, -0.1)
    emblem(fab, M['star7'], [SILVER_M], cloth=False)


def p_crimson(fab):
    tone_lattice(fab, 16.0, 0.07)
    fab.scatter(FLEUR, 22.6, 22.6, [GOLD_M], seed=21, jitter=0.0, stagger=True, need=0.9)
    hem_band(fab, 3, 3, GOLD_M, 0.0)
    hem_band(fab, 5, 5, GOLD_M, -0.15)
    edge_ring(fab, 3.0, GOLD_M, -0.05)
    emblem(fab, M['crown'], [GOLD_M], cloth=False)


def p_emerald(fab):
    # silk: long diagonal sheen bands, very smooth
    sheen = np.sin((fab.s * 0.9 + fab.t * 0.5) * 0.045)
    fab.tone(np.clip(sheen, 0, 1) ** 3, 0.18)
    fab.tone(np.clip(-sheen, 0, 1) ** 2, -0.06)
    hem_band(fab, 3, 3, GOLD_M, 0.0)
    hem_motifs(fab, M['diamond_s'], 7, 14, [GOLD_M])
    edge_ring(fab, 3.0, GOLD_M, -0.05)
    emblem(fab, M['diamond'], [GOLD_M], cloth=False)


def p_sun(fab):
    # soft darker rays radiating from the drape centre (cloth) / cushion centre + rust-red suns
    e = fab.extra
    if kind(fab) == 'cloth':
        g = e['g']
        cy_t = float(fab.t[int(e['e_row'][int(g.cx)] - g.y0 + 14), int(g.cx)]) if not mini(fab) else 0.0
        a = np.arctan2(fab.t - cy_t, fab.s)
    else:
        a = np.arctan2(fab.t - float(np.median(fab.t[fab.m])), fab.s)
    rays = (np.cos(a * 16) > 0.55).astype(np.float32)
    fab.tone(rays, -0.06)
    emblem(fab, SUN_BIG, [RUST_M])
    hem_band(fab, 3, 3, RUST_M, 0.0)
    hem_band(fab, 5, 5, RUST_M, -0.1, every=2)
    hem_motifs(fab, M['sun_s'], 9, 16, [RUST_M], phase=0.5)
    scatter(fab, M['sun_s'], 40, 30, [RUST_M], seed=31, prob=0.6, top_only=True)
    edge_ring(fab, 3.0, RUST_M, -0.05)
    if kind(fab) == 'cushion':
        emblem(fab, M['sun'], [RUST_M])
        scatter(fab, M['sun_s'], 30, 24, [RUST_M], seed=33, prob=0.5)


def p_lace(fab):
    # black lace: a soft diamond net, lace flowers in dark grey, a perforated scalloped lace border
    u = (fab.s + fab.t) / 6.0
    v = (fab.s - fab.t) / 6.0
    du = np.abs(u - np.round(u))
    dv = np.abs(v - np.round(v))
    net = ((du < 0.09) | (dv < 0.09)).astype(np.float32)
    fab.tone(net, 0.12)
    scatter(fab, LACE_FLOWER, 30, 26, [LACE_G], seed=41, prob=0.7, jitter=0.5)
    e = fab.extra
    if kind(fab) == 'cloth':
        HR = e['hem_row'][None, :]
        Yi = np.floor(e['Y']).astype(np.int32)
        Xi = np.floor(e['X']).astype(np.int32)
        k = HR - Yi
        sc_ = 2.0 + 3.0 * np.abs(np.sin(e['s_arc'][None, :] * math.pi / 9.0))
        lace = e['drape'] & (k >= 2) & (k < 2 + sc_) & (e['drop'][None, :] > 10)
        rim = lace & (k >= 1 + np.floor(sc_))
        holes = lace & ~rim & (np.mod(Yi, 2) == 0) & (np.mod(Xi + 2 * (np.mod(Yi // 2, 2)), 4) == 0)
        paint_ov(fab, lace & ~holes & ~rim, LACE_G, 0.05)
        paint_ov(fab, rim, LACE_G, 0.25)
        paint_ov(fab, holes, ['#08070a', '#0c0b0e', '#100f13', '#141318', '#18171c', '#1c1b20'], 0.0)
        hem_motifs(fab, LACE_FLOWER, 11, 15, [LACE_G], phase=0.5)
    edge_ring(fab, 3.0, SILVER_M, -0.25)
    emblem(fab, LACE_FLOWER, [LACE_G], cloth=False)


def p_rose(fab):
    scatter(fab, M['rose_s'], 28, 24, [ROSE_RED, LEAF_G], seed=51, prob=0.7, jitter=0.7)
    scatter(fab, M['bud'], 26, 22, [ROSE_RED, LEAF_G], seed=57, prob=0.35, jitter=0.9)
    if kind(fab) == 'cloth':
        hem_band(fab, 3, 3, GOLD_M, -0.05)
        hem_motifs(fab, M['rose'], 10, 20, [ROSE_RED, LEAF_G], phase=0.5)
        hem_motifs(fab, M['vine_leaf'], 9, 20, [LEAF_G, LEAF_G], phase=0.0)
    edge_ring(fab, 3.0, LEAF_G, -0.1)
    emblem(fab, M['rose'], [ROSE_RED, LEAF_G], cloth=False)


def p_ocean(fab):
    # seigaiha (overlapping wave scales) as a soft tone pattern
    Sx, Sy, R = 16.0, 7.0, 8.0
    s, t = fab.s, fab.t
    best_j = np.full(s.shape, -1e9)
    best_d = np.full(s.shape, 1e9)
    j0 = np.floor(t / Sy).astype(np.int64)
    for dj in (0, 1, 2):
        j = j0 + dj
        off = np.where(np.mod(j, 2) == 0, 0.0, Sx / 2)
        ci = np.round((s - off) / Sx)
        cx = ci * Sx + off
        cy = j * Sy
        d = np.hypot(s - cx, t - cy)
        ok = (d <= R) & (j > best_j)
        best_j = np.where(ok, j, best_j)
        best_d = np.where(ok, d, best_d)
    ring = (np.abs(best_d - 7.2) < 0.55) | (np.abs(best_d - 4.6) < 0.5) | (np.abs(best_d - 2.0) < 0.5)
    fab.tone(ring.astype(np.float32), 0.10)
    hem_band(fab, 3, 3, SKY_M, -0.05)
    hem_motifs(fab, M['wave_curl'], 7, 13, [WHITE_T[1:]], phase=0.5)
    edge_ring(fab, 3.0, SKY_M, -0.1)
    emblem(fab, M['shell'], [WHITE_T[1:]], cloth=False)


def p_forest(fab):
    n = fbm(fab.s / 14.0, fab.t / 14.0, 81, 2)
    fab.tone(np.clip((n - 0.5) * 2, -1, 1), 0.07)
    scatter(fab, M['leaf'], 22, 19, [LEAF_LIGHT, LEAF_LIGHT], seed=83, prob=0.65)
    scatter(fab, M['leaf2'], 22, 19, [LEAF_LIGHT, LEAF_LIGHT], seed=89, prob=0.45)
    scatter(fab, ACORN_M, 44, 36, [ACORN, MOSS_LEAF], seed=87, prob=0.5)
    if kind(fab) == 'cloth':
        hem_band(fab, 3, 3, BRONZE_T[1:], 0.0)
        hem_band(fab, 6, 6, LEAF_LIGHT, -0.15)
        hem_motifs(fab, M['vine_leaf'], 10, 11, [LEAF_LIGHT, LEAF_LIGHT], phase=0.5)
        hem_motifs(fab, ACORN_M, 10, 22, [ACORN, MOSS_LEAF], phase=0.0)
    edge_ring(fab, 3.0, BRONZE_T[1:], -0.1)
    emblem(fab, ACORN_M, [ACORN, MOSS_LEAF], cloth=False)


def p_lavender(fab):
    stars(fab, [WHITE_T[1:]], 1.25, seed=91)
    scatter(fab, M['star3'], 31, 25, [GOLD_M], seed=97, prob=0.6)
    hem_band(fab, 3, 3, WHITE_T[1:], -0.1)
    hem_motifs(fab, M['star5'], 8, 15, [WHITE_T[1:]])
    edge_ring(fab, 3.0, WHITE_T[1:], -0.15)
    emblem(fab, M['star7'], [GOLD_M], cloth=False)


def p_moons(fab):
    scatter(fab, M['dot'], 15, 12, [SILVER_M], seed=41, jitter=0.9, prob=0.5)
    scatter(fab, M['star3'], 33, 26, [SILVER_M], seed=47, jitter=0.8, prob=0.7)
    phases = [moon_phase(p) for p in (0.07, 0.17, 0.27, 0.37, 0.5, 0.63, 0.73, 0.83, 0.93)]
    hem_motifs(fab, None, 11 if not mini(fab) else 8, 17, [SILVER_M], choose=lambda i: phases[i % len(phases)])
    hem_band(fab, 3, 3, SILVER_M, -0.05)
    scatter(fab, M['moon_s'], 44, 34, [SILVER_M], seed=43, prob=0.5, top_only=True)
    edge_ring(fab, 3.0, SILVER_M, -0.1)
    emblem(fab, moon_phase(0.5, 4.5), [SILVER_M], cloth=False)


def p_desert(fab):
    s, t = fab.s, fab.t
    rip = np.mod(t + 3.5 * np.sin(s * 0.045) + 1.6 * np.sin(s * 0.13 + t * 0.03), 9.0)
    fab.tone((rip < 1.0).astype(np.float32), -0.10)
    fab.tone(((rip >= 1.0) & (rip < 2.0)).astype(np.float32), 0.06)
    if kind(fab) == 'cloth':
        hem_band(fab, 3, 4, TERRA_M, 0.0)
        hem_motifs(fab, KILIM, 10, 11, [TERRA_M])
        hem_band(fab, 15, 15, TERRA_M, -0.1)
    edge_ring(fab, 3.0, TERRA_M, -0.05)
    emblem(fab, KILIM, [TERRA_M], cloth=False)


def p_frozen(fab):
    e = voronoi_edge(fab.s, fab.t, 24.0, 121)
    fab.tone((e < 0.6).astype(np.float32), 0.20)
    fab.tone(((e >= 0.6) & (e < 1.5)).astype(np.float32), 0.06)
    scatter(fab, M['snow_s'], 34, 28, [WHITE_T[1:]], seed=123, prob=0.6)
    hem_band(fab, 3, 3, WHITE_T[1:], -0.05)
    hem_motifs(fab, M['snow'], 9, 18, [WHITE_T[1:]], phase=0.5)
    edge_ring(fab, 3.0, WHITE_T[1:], -0.1)
    emblem(fab, M['snow'], [WHITE_T[1:]], cloth=False)


def p_ember(fab):
    n = fbm(fab.s / 10.0, fab.t / 8.0, 131, 2)
    fab.tone(np.clip((n - 0.55) * 3, 0, 1), 0.10)
    scatter(fab, M['dot'], 11, 9, [EMBER_M], seed=133, prob=0.35, jitter=0.9)
    scatter(fab, M['ember'], 29, 23, [EMBER_M], seed=137, prob=0.5)
    if kind(fab) == 'cloth':
        hem_motifs(fab, M['flame'], 6, 9, [EMBER_M], need=0.95)
        hem_band(fab, 2, 2, EMBER_M, -0.1)
    edge_ring(fab, 3.0, EMBER_M, -0.15)
    emblem(fab, M['flame'], [EMBER_M], cloth=False)


def p_candy(fab):
    stripe = np.mod(fab.s + fab.t * 0.8, 18.0) < 9.0
    fab.select(stripe, 1)
    scatter(fab, M['heart'], 36, 30, [WHITE_T[1:]], seed=141, prob=0.5)
    hem_band(fab, 3, 3, WHITE_T[1:], 0.0)
    hem_motifs(fab, M['polka'], 7, 12, [WHITE_T[1:]])
    edge_ring(fab, 3.0, WHITE_T[1:], -0.1)
    emblem(fab, M['heart'], [WHITE_T[1:]], cloth=False)


def p_galaxy(fab):
    e = fab.extra
    s, t = fab.s, fab.t
    if kind(fab) == 'cloth':
        c_t = float(np.median(t[e['drape'] & fab.m])) if (e['drape'] & fab.m).any() else 0.0
    else:
        c_t = float(np.median(t[fab.m]))
    dx = s / 1.0
    dy = (t - c_t) * 1.6
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    arm = np.sin(2.0 * th - r * 0.075)
    n = fbm(s / 12.0, t / 9.0, 151, 2)
    neb = np.clip(arm * 0.7 + (n - 0.5) * 1.2, -1, 1)
    fab.tone(np.clip(neb, 0, 1), 0.20)
    fab.select((neb > 0.55) & (np.mod(np.floor(s) + np.floor(t), 1) == 0), 1)
    stars(fab, [SILVER_M], 1.15, seed=153)
    hem_band(fab, 3, 3, SILVER_M, -0.05)
    edge_ring(fab, 3.0, SILVER_M, -0.1)
    emblem(fab, M['sparkle'], [SILVER_M], cloth=False)


def p_chess(fab):
    sq = 12.0
    cell = (np.floor(fab.s / sq) + np.floor((fab.t + 3) / sq)).astype(np.int64)
    fab.select((cell % 2) == 0, 1)
    hem_band(fab, 3, 3, SILVER_M, -0.05)
    edge_ring(fab, 3.0, SILVER_M, -0.1)


def p_runes(fab):
    e = fab.extra
    if kind(fab) == 'cloth':
        hem_band(fab, 4, 4, TEAL_GLOW, -0.05)
        hem_band(fab, 19, 19, TEAL_GLOW, -0.05)
        hem_motifs(fab, None, 11 if not mini(fab) else 9, 9, [TEAL_GLOW],
                   choose=lambda i: RUNES[(i * 5 + 3) % len(RUNES)], need=0.95)
        # ring of runes on the table top around the cushion
        g = e['g']
        if not mini(fab):
            rr = 0.78
            for k in range(40):
                a = math.pi * 2 * k / 40.0
                x = g.cx + g.rc * rr * math.cos(a)
                y = g.ccy + g.cry * rr * math.sin(a) - g.y0
                fab.stamp(RUNES[k % len(RUNES)], x, y, [TEAL_GLOW], need=1.0, flat=True)
        edge_ring(fab, 3.0, TEAL_GLOW, -0.1)
    else:
        for i, x in enumerate(np.arange(-48, 49, 12)):
            fab.stamp(RUNES[(i * 3) % len(RUNES)], e['cx'] + x, e['emblem_y'] + 2, [TEAL_GLOW], need=1.0, flat=True)


def p_tarot(fab):
    # woven tapestry: soft horizontal weave + gold medallions
    weave = (np.mod(np.floor(fab.t), 3) == 0).astype(np.float32)
    fab.tone(weave, -0.035)
    tone_lattice(fab, 20.0, 0.05, 0.06)
    if kind(fab) == 'cloth':
        hem_band(fab, 3, 3, GOLD_M, 0.0)
        hem_band(fab, 21, 21, GOLD_M, -0.08)
        hem_motifs(fab, None, 12 if not mini(fab) else 9, 22, [GOLD_M, ['#160c2a', '#2a1c4e', '#4a3a86', '#7a6ac0', '#b2a6ec', '#ece6ff']],
                   choose=lambda i: MEDALLIONS[i % 4])
    scatter(fab, M['diamond_s'], 26, 22, [GOLD_M], seed=171, prob=0.6, top_only=True)
    edge_ring(fab, 3.0, GOLD_M, -0.05)
    emblem(fab, MEDALLIONS[0], [GOLD_M, ['#160c2a', '#2a1c4e', '#4a3a86', '#7a6ac0', '#b2a6ec', '#ece6ff']],
           cloth=False)


def p_peacock(fab):
    # soft feather barbs (diagonal) + peacock feather eyes
    barb = np.sin((fab.s - fab.t * 0.6) * 0.9) > 0.75
    fab.tone(barb.astype(np.float32), 0.05)
    scatter(fab, PEACOCK, 34, 38, [PEA_TEAL, PEA_GOLD, NAVY_M], seed=181, prob=0.8, jitter=0.4, need=0.8)
    scatter(fab, PEACOCK_S, 34, 38, [PEA_TEAL, PEA_GOLD, NAVY_M], seed=187, prob=0.45, jitter=0.8)
    hem_band(fab, 3, 3, GOLD_M, 0.0)
    hem_motifs(fab, PEACOCK, 13, 19, [PEA_TEAL, PEA_GOLD, NAVY_M], phase=0.5)
    hem_motifs(fab, PEACOCK_S, 7, 19, [PEA_TEAL, PEA_GOLD, NAVY_M])
    edge_ring(fab, 3.0, PEA_GOLD, -0.05)
    emblem(fab, PEACOCK_S, [PEA_TEAL, PEA_GOLD, NAVY_M], cloth=False)


def D(name_en, name_de, base, pattern, trim=GOLD_T, fringe=GOLD_F, tassel=None, out=None, **kw):
    d = dict(name_en=name_en, name_de=name_de, base=base, pattern=pattern, trim=trim, fringe=fringe,
             tassel=tassel or fringe, out=out or base[0], piping=kw.pop('piping', trim), **kw)
    d.setdefault('tassel_out', '#1a0e06')
    return d


DESIGNS = [
    D('Royal Purple', 'Königslila',
      ['#12051e', '#1f0833', '#2f0e4b', '#421564', '#561e7e', '#6c2a96', '#8540ad', '#a35ec4'], p_royal,
      out='#0a0312'),
    D('Midnight Blue', 'Mitternachtsblau',
      ['#03051a', '#070c28', '#0c143c', '#121d52', '#192868', '#22367f', '#2e4796', '#3e5cae'], p_midnight,
      trim=SILVER_T, fringe=SILVER_F, out='#02030e', tassel_out='#141826'),
    D('Crimson Velvet', 'Karminsamt',
      ['#1a0306', '#2e050b', '#460912', '#600e1a', '#7c1422', '#9a1d2c', '#b82c3a', '#d4464e'], p_crimson,
      out='#0e0204'),
    D('Emerald Silk', 'Smaragdseide',
      ['#021a0e', '#052a17', '#083c22', '#0d502e', '#13663b', '#1c7e4a', '#289a5c', '#3ab872'], p_emerald,
      out='#010c06', dither=0.15),
    D('Golden Sun', 'Goldene Sonne',
      ['#2a1402', '#4a2404', '#6e3a06', '#93520a', '#b86e12', '#d48c22', '#e8aa3a', '#f6c862'], p_sun,
      trim=COPPER_T, fringe=['#3a0c04', '#701a06', '#a8300c', '#d44c14', '#f07028', '#ff9a48'], out='#160a02',
      tassel_out='#200802'),
    D('Black Lace', 'Schwarze Spitze',
      ['#050407', '#09080c', '#0f0d13', '#15131a', '#1c1a22', '#24222c', '#2e2b37', '#3a3744'], p_lace,
      trim=SILVER_T, fringe=['#16151a', '#2c2a32', '#46444e', '#66636e', '#8a8794', '#b0adb8'], out='#020203',
      tassel_out='#0a0a0c', piping=['#16151a', '#2c2a32', '#46444e', '#66636e', '#8a8794', '#b0adb8', '#d4d2da']),
    D('Rose Garden', 'Rosengarten',
      ['#2a0a14', '#44101f', '#62182c', '#82223a', '#a0304a', '#bc4560', '#d46078', '#e88296'], p_rose,
      fringe=GOLD_F, out='#16040a'),
    D('Ocean Wave', 'Meereswoge',
      ['#021218', '#041e28', '#072c3a', '#0a3c4e', '#0f4e64', '#16627a', '#207892', '#2e90aa'], p_ocean,
      trim=SILVER_T, fringe=['#2a4652', '#4a6e7c', '#78a0ae', '#a6cad6', '#d2ecf2', '#f4ffff'], out='#01090c',
      tassel_out='#0e2026'),
    D('Forest Moss', 'Waldmoos',
      ['#0a1206', '#121e0a', '#1c2c10', '#283c16', '#344e1c', '#426224', '#52762e', '#64903a'], p_forest,
      trim=BRONZE_T, fringe=BRONZE_F, out='#050902'),
    D('Lavender Stars', 'Lavendelsterne',
      ['#1e1430', '#2e2046', '#40305e', '#544278', '#6a5692', '#806caa', '#9884c0', '#b2a0d6'], p_lavender,
      trim=WHITE_T, fringe=WHITE_F, out='#100a1a', tassel_out='#2a2232'),
    D('Moon Phases', 'Mondphasen',
      ['#06041a', '#0c0a2a', '#14113c', '#1c1850', '#252164', '#302c78', '#3d3a8c', '#4c4aa0'], p_moons,
      trim=SILVER_T, fringe=SILVER_F, out='#03020e', tassel_out='#141826'),
    D('Desert Sand', 'Wüstensand',
      ['#3a2410', '#58381a', '#764e26', '#946634', '#ae7e44', '#c49656', '#d6ac6c', '#e6c286'], p_desert,
      trim=['#2a0c04', '#5a1e0a', '#8a3214', '#b44a20', '#d66a34', '#f08c50', '#ffb478'],
      fringe=['#2a160a', '#4a2c16', '#6e4626', '#946236', '#b88048', '#d8a060'], out='#1c1006', tassel_out='#1c0e06'),
    D('Frozen Lake', 'Gefrorener See',
      ['#14283a', '#1c3850', '#264a66', '#325e7e', '#3f7496', '#4e8aae', '#62a2c4', '#7cbad8'], p_frozen,
      trim=WHITE_T, fringe=['#4a5a6a', '#74889a', '#a0b4c6', '#c8dae8', '#e6f2fa', '#ffffff'], out='#0a1622',
      tassel_out='#2a3a4a', dither=0.2),
    D('Ember', 'Glut',
      ['#0c0606', '#160a08', '#20100c', '#2c1510', '#3a1c14', '#4a2418', '#5c2e1e', '#703a24'], p_ember,
      trim=COPPER_T, fringe=['#3a0c04', '#7a1c06', '#b4340a', '#e05a14', '#fa8a2a', '#ffbe5a'], out='#050202',
      tassel_out='#200802'),
    D('Candy Pink', 'Bonbonrosa',
      ['#3a0a24', '#5a1238', '#7c1c4e', '#a02a66', '#c03c7e', '#d85898', '#ea7cb2', '#f6a2cc'], p_candy,
      alt=[['#5a2a44', '#844060', '#ac5c80', '#cc7c9e', '#e4a0bc', '#f2c0d4', '#fadbe6', '#fff0f6']],
      trim=WHITE_T, fringe=WHITE_F, out='#22041a', tassel_out='#3a2a36'),
    D('Galaxy Swirl', 'Galaxienwirbel',
      ['#04020c', '#080418', '#0e0826', '#160c36', '#201248', '#2c1a5c', '#3a2470', '#4c3086'], p_galaxy,
      alt=[['#10041a', '#1e082c', '#320e44', '#4a165e', '#64207a', '#802c94', '#9c3cac', '#b852c2']],
      trim=SILVER_T, fringe=['#2a2440', '#4a4268', '#726a96', '#a09ac0', '#cac6e2', '#f0eeff'], out='#020106',
      tassel_out='#141228'),
    D('Chess Board', 'Schachbrett',
      ['#0c0a10', '#151219', '#1e1a23', '#28232e', '#322c3a', '#3d3646', '#494152', '#564d60'], p_chess,
      alt=[['#2e2a28', '#45403b', '#5d564e', '#756c62', '#8b8174', '#a09584', '#b3a894', '#c4baa6']],
      trim=SILVER_T, fringe=SILVER_F, out='#060508', tassel_out='#141826'),
    D('Rune Circle', 'Runenkreis',
      ['#06080c', '#0c1016', '#121822', '#1a222e', '#222c3c', '#2c384a', '#38465a', '#46566c'], p_runes,
      trim=BRONZE_T, fringe=BRONZE_F, out='#030406'),
    D('Tarot Tapestry', 'Tarot-Wandteppich',
      ['#14040a', '#220612', '#340a1c', '#481028', '#5e1834', '#762242', '#902e52', '#ac3e64'], p_tarot,
      out='#0a0206'),
    D('Peacock', 'Pfau',
      ['#021412', '#04201c', '#062e28', '#0a3e36', '#0e5046', '#146458', '#1c7a6c', '#289282'], p_peacock,
      fringe=['#2a2e06', '#4e560e', '#7a8618', '#a4b028', '#ccd23c', '#eef08a'], out='#010a08', tassel_out='#1a1e04'),
]
