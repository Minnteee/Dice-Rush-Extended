"""Crystal ball (back + front glass layers) and the carved wooden stand.

Ball: 128x128 at (176,44), centre (240,108), outer radius 64.
Stand: 124x36 at (178,154); a turned wooden cup with brass rings.  The ball
rests in the cup; the back half of the cup (seen through the glass) is drawn
faintly into ball_back so it appears behind the dice.
"""
import math

import numpy as np

from scene_lib import grid, quantize, ramp_arr, hexc, edge_out, edge_in, dilate, erode, fbm, vnoise
from scene_table import WOOD, GOLD

BALL_X, BALL_Y, BALL_S = 176, 44, 128
BALL_C = (240.0, 108.0)
BALL_R = 64.0
STAND_X, STAND_Y, STAND_W, STAND_H = 178, 154, 124, 36

PHI = math.radians(12.0)
SINP, COSP = math.sin(PHI), math.cos(PHI)

# stand profile: (height, radius) from the cushion upwards - a carved wooden drum
# on a round foot, brass bands top and bottom; the ball rests on the brass lip.
PROFILE = [
    (0.0, 33.0), (0.8, 34.6), (2.2, 35.0), (3.2, 34.0),       # brass foot ring
    (3.6, 32.0), (4.6, 30.5), (5.6, 30.0),                    # wooden foot (concave)
    (6.2, 31.5), (7.0, 33.5),                                 # flare into the drum
    (7.6, 35.0), (11.5, 36.2), (15.6, 35.6),                  # carved drum (slight belly)
    (16.0, 36.6), (17.2, 37.4), (18.6, 37.6), (19.6, 37.0),   # brass top band
    (20.0, 36.0),                                             # inner lip
]
MAT = [(0.0, 3.4, 'brass'), (3.4, 15.8, 'wood'), (15.8, 99, 'brass')]
LIP_H = 19.6
LIP_R = 37.0


def prof_r(h):
    hs = [p[0] for p in PROFILE]
    rs = [p[1] for p in PROFILE]
    return np.interp(h, hs, rs)


def stand_base_y():
    """canvas y of the stand's axis at h = 0 so that the ball rests on the lip."""
    centre_h = LIP_H + math.sqrt(BALL_R ** 2 - LIP_R ** 2) - 1.0
    return BALL_C[1] + centre_h * COSP


def render_stand():
    """returns (stand RGBA 124x36, see-through RGBA in ball coordinates 128x128)."""
    W, H = STAND_W, STAND_H
    cx = BALL_C[0] - STAND_X
    yb = stand_base_y() - STAND_Y
    hh = np.arange(0.0, LIP_H + 0.01, 0.12)
    th = np.linspace(-math.pi, math.pi, 1600, endpoint=False)
    TH, HH = np.meshgrid(th, hh)
    R = prof_r(HH)
    dr = np.gradient(R, hh, axis=0)
    # outward normal of the surface of revolution
    nr = 1.0 / np.sqrt(1 + dr * dr)
    nh = -dr / np.sqrt(1 + dr * dr)
    nx = nr * np.sin(TH)
    ny = nr * np.cos(TH)          # towards the viewer
    nz = nh
    X = cx + R * np.sin(TH)
    Y = yb - HH * COSP + R * np.cos(TH) * SINP
    D = R * np.cos(TH) * COSP + HH * SINP
    L = np.array([-0.38, 0.80, 0.46])
    L = L / np.linalg.norm(L)
    # the back half is seen from inside (its inner wall faces the viewer through the glass)
    backside = np.cos(TH) < 0
    nx = np.where(backside, -nx, nx)
    ny = np.where(backside, -ny, ny)
    ndl = nx * L[0] + ny * L[1] + nz * L[2]
    ndc = ny * COSP + nz * SINP
    # top light from the glowing ball
    glow = np.clip(nz, 0, 1) * 0.22
    lev = 0.10 + 0.66 * np.clip(ndl, 0, 1) + glow
    spec = np.clip(ndl, 0, 1) ** 14
    mat = np.full(HH.shape, 'wood', dtype='<U5')
    for (h0, h1, m) in MAT:
        mat[(HH >= h0) & (HH < h1)] = m
    # carved arcade on the drum: recessed arches separated by pilasters
    drum = (HH > 7.8) & (HH < 15.4)
    per = 2 * math.pi / 16.0
    ph = np.mod(TH + per / 2, per) / per - 0.5             # -0.5..0.5 across one arch
    arch_top = 13.2 + 1.6 * np.sqrt(np.clip(1 - (ph / 0.36) ** 2, 0, 1))
    recess = drum & (np.abs(ph) < 0.36) & (HH < arch_top) & (HH > 9.0)
    rim_l = recess & (ph < -0.26)                           # shadowed left jamb
    rim_r = recess & (ph > 0.26)                            # lit right jamb
    lev = np.where(recess, lev - 0.20, lev)
    lev = np.where(rim_l, lev - 0.10, lev)
    lev = np.where(rim_r, lev + 0.22, lev)
    lev = np.where(drum & ~recess & (np.abs(ph) >= 0.36) & (np.abs(ph) < 0.44), lev + 0.10, lev)
    lev = np.where(recess & (HH < 9.8), lev + 0.18, lev)    # lit sill of the arch
    mat = np.where(drum & (HH > arch_top) & (HH < arch_top + 0.7) & (np.abs(ph) < 0.30), 'brass', mat)
    vis = ndc > -0.02
    xi = np.floor(X).astype(np.int64)
    yi = np.floor(Y).astype(np.int64)
    ok = vis & (xi >= 0) & (xi < W) & (yi >= -60) & (yi < H)
    xs, ys, ds = xi[ok], yi[ok], D[ok]
    lv, sp, mt, tt, h_ = lev[ok], spec[ok], mat[ok], TH[ok], HH[ok]
    order = np.argsort(-ds, kind='stable')
    key = (ys - (-60)) * W + xs
    key = key[order]
    _, first = np.unique(key, return_index=True)
    sel = order[first]
    wood = ramp_arr(WOOD)
    gold = ramp_arr(GOLD)
    img = np.zeros((H, W, 4), np.uint8)
    thru = np.zeros((BALL_S, BALL_S, 4), np.uint8)
    for k in sel:
        x, y = xs[k], ys[k]
        back = math.cos(tt[k]) < 0
        gx, gy = x + STAND_X, y + STAND_Y
        inside_ball = (gx + 0.5 - BALL_C[0]) ** 2 + (gy + 0.5 - BALL_C[1]) ** 2 < (BALL_R - 0.5) ** 2
        if mt[k] == 'brass':
            v = lv[k] + 0.35 * sp[k]
            col = gold[int(np.clip(round(v * 6.4), 0, 6))]
        else:
            v = lv[k] + 0.25 * sp[k]
            col = wood[int(np.clip(round(v * 8.6), 0, 8))]
        if back and inside_ball:
            bx, by = gx - BALL_X, gy - BALL_Y
            if 0 <= bx < BALL_S and 0 <= by < BALL_S:
                thru[by, bx] = (int(col[0]), int(col[1]), int(col[2]), 120)
            continue
        if 0 <= y < H:
            img[y, x, :3] = col
            img[y, x, 3] = 255
    # small amethyst cabochons on the brass band
    for a in np.linspace(-1.2, 1.2, 5):
        h = 17.4
        r = prof_r(h) + 0.6
        x = cx + r * math.sin(a)
        y = yb - h * COSP + r * math.cos(a) * SINP
        xi_, yi_ = int(math.floor(x)), int(math.floor(y))
        for (ddx, ddy, c) in ((0, 0, '#b77cf2'), (1, 0, '#7a3cc0'), (0, 1, '#5a2496'), (1, 1, '#3c146c'), (0, -1, '#e2c6ff')):
            if 0 <= xi_ + ddx < W and 0 <= yi_ + ddy < H:
                img[yi_ + ddy, xi_ + ddx] = hexc(c)
    # outline (not over the ball where the lip meets it)
    m = img[..., 3] > 0
    e = edge_out(m)
    img[e] = hexc('#0c0507')
    return img, thru


# ================================================================ the ball
def _alpha_steps(a, steps=(0, 26, 40, 56, 72, 96, 128, 160, 200, 235, 255)):
    st = np.array(steps, np.float32)
    idx = np.abs(a[..., None] - st[None, None, :]).argmin(axis=-1)
    return st[idx]


def render_ball(thru=None):
    S = BALL_S
    X, Y = grid(S, S)
    cx = cy = S / 2.0
    dx = (X - cx) / BALL_R
    dy = (Y - cy) / BALL_R
    r = np.sqrt(dx * dx + dy * dy)
    inside = r <= 1.0
    ang = np.degrees(np.arctan2(-dy, dx))           # 90 = up, 180 = left
    d_px = (1.0 - r) * BALL_R                       # distance from the rim in px

    # ------------------------------------------------ back layer
    back = np.zeros((S, S, 4), np.float32)
    # interior tint: violet in the middle -> deeper towards the rim (fresnel)
    a = 26 + 34 * np.clip((r - 0.35) / 0.55, 0, 1) ** 1.5
    col = np.zeros((S, S, 3), np.float32)
    col[...] = (104, 70, 188)
    # cool cyan in the lower right, warm reflection of the stand at the bottom
    cyan = np.clip((dx * 0.6 + dy * 0.8 - 0.25) / 0.6, 0, 1)
    col = col * (1 - cyan[..., None] * 0.6) + np.array([70, 170, 210], np.float32) * cyan[..., None] * 0.6
    warm = np.clip((dy - 0.62) / 0.3, 0, 1) * np.clip(1 - np.abs(dx) / 0.75, 0, 1)
    col = col * (1 - warm[..., None] * 0.55) + np.array([150, 90, 60], np.float32) * warm[..., None] * 0.55
    a = a + warm * 18
    # soft swirl of mist (very faint)
    sw = np.sin(np.arctan2(dy, dx) * 2.0 + r * 7.0)
    mist = (sw > 0.55) & (r > 0.25) & (r < 0.8)
    a = np.where(mist, a + 10, a)
    col = np.where(mist[..., None], col * 0.8 + np.array([170, 130, 240], np.float32) * 0.2, col)
    # darker back rim band
    rim = d_px < 6.5
    a = np.where(rim, 64 + 46 * np.clip((6.5 - d_px) / 6.5, 0, 1), a)
    col = np.where(rim[..., None], np.array([38, 22, 84], np.float32), col)
    # caustic: light focused on the lower right inside the glass (small, soft)
    ca = ((dx - 0.34) / 0.17) ** 2 + ((dy - 0.60) / 0.07) ** 2
    caus = (ca < 1.0) & (d_px > 4)
    a = np.where(caus, 50 + 16 * (ca < 0.3), a)
    col = np.where(caus[..., None], np.array([170, 220, 255], np.float32), col)
    a = _alpha_steps(a)
    back[..., :3] = col
    back[..., 3] = np.where(inside, a, 0)
    back = np.clip(np.round(back), 0, 255).astype(np.uint8)
    if thru is not None:
        m = (thru[..., 3] > 0) & inside
        # tint the see-through stand towards the glass colour
        tc = thru[..., :3].astype(np.float32) * 0.65 + np.array([60, 40, 110], np.float32) * 0.35
        back[m, :3] = tc[m].astype(np.uint8)
        back[m, 3] = 88

    # ------------------------------------------------ front layer
    fr = np.zeros((S, S, 4), np.uint8)

    def put(mask, c, alpha):
        fr[mask, 0], fr[mask, 1], fr[mask, 2] = c
        fr[mask, 3] = alpha

    # outline + rim light
    outline = inside & (d_px < 1.0)
    put(outline, (20, 10, 38), 235)
    ring2 = inside & (d_px >= 1.0) & (d_px < 2.0)
    upper_left = (ang > 95) & (ang < 215)
    lower_right = (ang < -10) & (ang > -95)
    put(ring2 & upper_left, (214, 196, 255), 170)
    put(ring2 & lower_right, (130, 226, 255), 130)
    put(ring2 & ~upper_left & ~lower_right, (120, 96, 200), 96)
    ring3 = inside & (d_px >= 2.0) & (d_px < 3.0) & (ang > 120) & (ang < 190)
    put(ring3, (200, 180, 255), 72)
    # big curved window reflection (upper left)
    band = inside & (r > 0.70) & (r < 0.84) & (ang > 112) & (ang < 168)
    core = band & (r > 0.735) & (r < 0.805) & (ang > 118) & (ang < 160)
    put(band, (235, 228, 255), 96)
    put(core, (255, 255, 255), 168)
    # second, shorter band (double window)
    band2 = inside & (r > 0.70) & (r < 0.80) & (ang > 172) & (ang < 186)
    put(band2, (235, 228, 255), 84)
    # small glint
    gl = ((dx + 0.33) / 0.065) ** 2 + ((dy + 0.47) / 0.035) ** 2 < 1.0
    put(gl, (255, 255, 255), 210)
    # lower right reflection
    lr = inside & (r > 0.80) & (r < 0.88) & (ang < -22) & (ang > -70)
    put(lr, (150, 236, 255), 88)
    lr2 = inside & (r > 0.825) & (r < 0.86) & (ang < -32) & (ang > -58)
    put(lr2, (190, 246, 255), 140)
    # reflections of the two candles (right side)
    for (ax, ay) in ((0.66, 0.06), (0.74, 0.16)):
        px = int(cx + ax * BALL_R)
        py = int(cy + ay * BALL_R)
        fr[py, px] = (255, 214, 140, 210)
        fr[py + 1, px] = (255, 160, 80, 150)
    # sparkle (4 point star)
    sx, sy = int(cx - 0.50 * BALL_R), int(cy - 0.56 * BALL_R)
    for (ddx, ddy, al) in ((0, 0, 255), (1, 0, 200), (-1, 0, 200), (0, 1, 200), (0, -1, 200),
                           (2, 0, 110), (-2, 0, 110), (0, 2, 110), (0, -2, 110)):
        fr[sy + ddy, sx + ddx] = (255, 255, 255, al)
    return back, fr
