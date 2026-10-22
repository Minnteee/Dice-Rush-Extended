"""Gumball machine (+ crank overlay frames, gum balls, coin) and candles (+ flames)."""
import math

import numpy as np

from scene_lib import grid, ramp_arr, hexc, edge_out, edge_in, dilate, erode, hash01, vnoise, char_map, quantize
from scene_table import GOLD

# ------------------------------------------------------------------ palettes
RED = ['#1e0408', '#40070e', '#6a0c14', '#951519', '#c0221f', '#de3f2c', '#f2724c', '#ffb48c']
RED_OUT = '#160306'
CHROME = ['#15171e', '#353a48', '#5c6274', '#8a91a4', '#b8bfcf', '#e0e5ee', '#ffffff']
CHROME_OUT = '#0e1016'
GUM = {
    'red': ['#4a0610', '#a3141e', '#e8382c', '#ff8a70', '#ffe0d0'],
    'yellow': ['#5a3a04', '#b88410', '#f2c42a', '#ffe680', '#fffbe0'],
    'blue': ['#0a1650', '#1c46b0', '#3c84f0', '#8cc0ff', '#e4f0ff'],
    'green': ['#08381a', '#1a8a3c', '#3cc85c', '#9af0a8', '#e8ffe8'],
    'pink': ['#5a1240', '#c03a8a', '#f070b8', '#ffb4dc', '#fff0f8'],
    'white': ['#5a5664', '#a8a4b4', '#e2dee8', '#f8f6fc', '#ffffff'],
    'orange': ['#5a2004', '#c25a10', '#f68a28', '#ffc07a', '#fff0dc'],
    'purple': ['#2a0a4a', '#6a26b0', '#a45ef0', '#d4aaff', '#f6eaff'],
}
BALL_COLOURS = ['red', 'yellow', 'blue', 'green', 'pink', 'white']

LIGHT = np.array([0.62, -0.45, 0.64])          # from the upper right (the glowing ball)
LIGHT = LIGHT / np.linalg.norm(LIGHT)

MW, MH = 72, 140
CX = 36.0
GLOBE_C = (36.0, 51.0)
GLOBE_R = 30.5
CRANK_C = (36.0, 103.0)
SLOT = (24.0, 91.0, 27.0, 100.0)               # x0, y0, x1, y1 of the coin slot boss
CHUTE = (36.0, 119.5)                          # centre of the chute opening


def rlev(ramp, lev):
    r = ramp_arr(ramp)
    return r[np.clip(np.round(lev * (len(r) - 1)), 0, len(r) - 1).astype(np.int32)]


def shade_rev(X, Y, cx, hw, slope=0.0, spec_pow=26, spec_amt=0.5):
    """body of revolution seen from the front: hw = half width per pixel row (array)."""
    c = np.clip((X - cx) / np.maximum(hw, 0.5), -1, 1)
    nz = np.sqrt(np.clip(1 - c * c, 0, 1))
    nx = c
    ny = np.full_like(c, -slope)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / n, ny / n, nz / n
    ndl = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    hx, hy, hz = LIGHT[0], LIGHT[1], LIGHT[2] + 1.0
    hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    ndh = (nx * hx + ny * hy + nz * hz) / hn
    lev = 0.16 + 0.66 * np.clip(ndl, 0, 1)
    spec = np.clip(ndh, 0, 1) ** spec_pow * spec_amt
    return lev, spec, c


# ============================================================ gumball machine
def gum_ball_disc(img, cx, cy, r, colour, dim=0.0, mask=None):
    """draw one shaded gum ball (hard pixels)."""
    ramp = ramp_arr(GUM[colour])
    H, W = img.shape[:2]
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if not (0 <= x < W and 0 <= y < H):
                continue
            if mask is not None and not mask[y, x]:
                continue
            ddx = (x + 0.5 - cx) / r
            ddy = (y + 0.5 - cy) / r
            d2 = ddx * ddx + ddy * ddy
            if d2 > 1.0:
                continue
            nz = math.sqrt(max(0.0, 1 - d2))
            ndl = ddx * LIGHT[0] + ddy * LIGHT[1] + nz * LIGHT[2]
            lev = 0.12 + 0.78 * max(0.0, ndl) - dim
            if d2 > 0.72:
                lev -= 0.18
            k = int(np.clip(round(lev * 3.2), 0, 3))
            if ndl > 0.93 and d2 < 0.5:
                k = 4
            img[y, x, :3] = ramp[k]
            img[y, x, 3] = 255


def render_gumball_machine(seed=5):
    H, W = MH, MW
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W)

    def paint(mask, rgb):
        img[mask, :3] = rgb[mask] if rgb.ndim == 3 else rgb
        img[mask, 3] = 255

    # ------------------------------------------------ base (foot)
    base_top, base_bot = 124.0, 138.6
    t = np.clip((Y - base_top) / (base_bot - base_top), 0, 1)
    hw = 27.0 + 4.0 * np.sqrt(t) + 0.6 * t
    base = (Y >= base_top) & (Y < base_bot) & (np.abs(X - CX) <= hw)
    # rounded bottom edge (ellipse)
    base &= ~((Y > base_bot - 3) & ((np.abs(X - CX) / hw) ** 2 + ((Y - (base_bot - 3)) / 3.0) ** 2 > 1.0))
    lev, spec, c = shade_rev(X, Y, CX, hw, slope=-0.5)
    band = base & (Y >= 129.0) & (Y < 132.5)                  # chrome band
    paint(base & ~band, rlev(RED, lev + spec - 0.04))
    lev2, spec2, _ = shade_rev(X, Y, CX, hw, slope=0.0, spec_pow=10, spec_amt=0.8)
    paint(band, rlev(CHROME, lev2 + spec2 + 0.06 * (Y < 130.5)))
    # top lip of the base (seen from above: a thin lit ellipse ring)
    lip = (np.abs(Y - base_top - 0.5) < 1.0) & (np.abs(X - CX) <= 27.0)
    paint(lip, rlev(RED, 0.55 + 0.3 * np.clip((X - CX) / 27.0, -1, 1)))

    # ------------------------------------------------ body (truncated cone)
    body_top, body_bot = 84.0, 124.0
    tb = np.clip((Y - body_top) / (body_bot - body_top), 0, 1)
    hwb = 19.0 + 6.0 * tb ** 1.3
    body = (Y >= body_top) & (Y < body_bot) & (np.abs(X - CX) <= hwb)
    lev, spec, c = shade_rev(X, Y, CX, hwb, slope=0.25)
    blev = lev + spec
    # soft reflected highlight on the shadow side (rim)
    blev = np.where(c < -0.82, blev + 0.10, blev)
    paint(body, rlev(RED, blev))
    # chrome front plate (shield)
    pt, pb = 89.0, 123.0
    tp = np.clip((Y - pt) / (pb - pt), 0, 1)
    phw = 13.0 + 2.0 * tp
    plate = (Y >= pt) & (Y < pb) & (np.abs(X - CX) <= phw)
    # rounded top corners
    corner = (Y < pt + 4) & (np.abs(X - CX) > phw - 4)
    cr = ((np.abs(X - CX) - (phw - 4)) / 4.0) ** 2 + ((Y - (pt + 4)) / 4.0) ** 2 > 1.0
    plate &= ~(corner & cr)
    plev, pspec, pc = shade_rev(X, Y, CX, hwb, slope=0.25, spec_pow=8, spec_amt=0.7)
    pl = plev + pspec * 0.8
    # bevelled border of the plate
    pin = erode(plate, 1)
    pl = np.where(plate & ~pin, pl - 0.18, pl)
    pl = np.where(pin & ~erode(pin, 1) & (Y < CRANK_C[1]), pl + 0.16, pl)
    paint(plate, rlev(CHROME, pl))
    # rivets on the plate corners
    for (rx_, ry_) in ((CX - 10.5, pt + 2.0), (CX + 9.5, pt + 2.0), (CX - 12.5, pb - 3.0), (CX + 11.5, pb - 3.0)):
        xi, yi = int(rx_), int(ry_)
        img[yi, xi] = hexc(CHROME[6])
        img[yi + 1, xi] = hexc(CHROME[2])
    # coin slot boss + slot
    x0, y0, x1, y1 = SLOT
    boss = (X >= x0) & (X <= x1 + 1) & (Y >= y0) & (Y <= y1)
    paint(boss, rlev(CHROME, 0.62 + 0.25 * ((X - x0) > 2.0) - 0.2 * (Y > y1 - 1)))
    slot = (X >= x0 + 1.0) & (X < x0 + 2.0) & (Y >= y0 + 1.5) & (Y <= y1 - 1.5)
    img[slot] = hexc('#07080c')
    edge_l = (X >= x0 + 2.0) & (X < x0 + 3.0) & (Y >= y0 + 1.5) & (Y <= y1 - 1.5)
    img[edge_l] = hexc(CHROME[5])
    # crank axle socket (the overlay draws the crank on top)
    sock = (X - CRANK_C[0]) ** 2 + (Y - CRANK_C[1]) ** 2 <= 3.2 ** 2
    paint(sock, rlev(CHROME, np.full(X.shape, 0.18)))
    sock_hi = (X - CRANK_C[0] - 0.8) ** 2 + (Y - CRANK_C[1] - 0.8) ** 2 <= 1.6 ** 2
    img[sock & sock_hi] = hexc(CHROME[0])
    # chute: rounded opening with a little hinged flap
    chx, chy = CHUTE
    ch_hw, ch_top, ch_bot = 5.5, chy - 4.5, chy + 3.0
    opening = (np.abs(X - chx) <= ch_hw) & (Y >= ch_top) & (Y <= ch_bot)
    opening &= ~((Y < ch_top + 3) & (((np.abs(X - chx) - (ch_hw - 3)) / 3.0) ** 2 + ((Y - ch_top - 3) / 3.0) ** 2 > 1.0) & (np.abs(X - chx) > ch_hw - 3))
    rim = dilate(opening, 1) & ~opening
    paint(rim, rlev(CHROME, 0.75 - 0.35 * (Y > chy)))
    img[opening] = hexc('#0a0608')
    inner = opening & (Y > chy + 0.5)
    img[inner] = hexc('#1a0e10')
    # flap (hinged at the top, hanging slightly open)
    flap = (np.abs(X - chx) <= ch_hw - 0.5) & (Y >= ch_top + 0.5) & (Y <= ch_top + 3.6)
    paint(flap, rlev(CHROME, 0.66 + 0.2 * ((X - chx) > 1.5) - 0.25 * (Y > ch_top + 2.6)))
    hinge = (np.abs(X - chx) <= ch_hw - 0.5) & (np.abs(Y - ch_top) < 0.6)
    img[hinge] = hexc(CHROME[1])
    # lip of the chute (where the ball rolls out) - a small chrome tray
    tray = (np.abs(X - chx) <= ch_hw + 1.5) & (Y > ch_bot + 0.5) & (Y < ch_bot + 2.5)
    paint(tray, rlev(CHROME, 0.55 + 0.3 * np.clip((X - chx) / 6.0, -1, 1)))

    # ------------------------------------------------ collar under the globe
    col_top, col_bot = 76.0, 86.5
    tcl = np.clip((Y - col_top) / (col_bot - col_top), 0, 1)
    hwc = 21.5 - 3.5 * tcl
    collar = (Y >= col_top) & (Y < col_bot) & (np.abs(X - CX) <= hwc)
    lev, spec, c = shade_rev(X, Y, CX, hwc, slope=-0.3)
    clv = lev + spec
    clv = np.where(Y < col_top + 2.0, clv + 0.12, clv)
    paint(collar, rlev(RED, clv))
    cband = collar & (Y >= col_bot - 2.5)
    lev2, spec2, _ = shade_rev(X, Y, CX, hwc, spec_pow=10, spec_amt=0.8)
    paint(cband, rlev(CHROME, lev2 + spec2))

    # ------------------------------------------------ glass globe with gum balls
    gx, gy = GLOBE_C
    gR = GLOBE_R
    gdx = X - gx
    gdy = Y - gy
    gr = np.sqrt(gdx * gdx + gdy * gdy)
    globe = gr <= gR
    inner_r = gR - 1.5
    interior = gr <= inner_r
    balls = np.zeros((H, W, 4), np.uint8)
    rng_cols = BALL_COLOURS + ['orange', 'purple']
    pile_top = gy - gR + 10.0
    sp = 6.6
    rr = 3.35
    rowh = sp * 0.866
    # back layer (darker) then front layer
    for layer, (ox, oy, dim, rad) in enumerate(((sp / 2, rowh / 2, 0.22, rr - 0.2), (0.0, 0.0, 0.0, rr))):
        j = 0
        while True:
            cy = gy + gR - 2.0 - j * rowh - oy
            if cy < pile_top - 1:
                break
            off = (sp / 2 if j % 2 else 0.0) + ox
            i = -6
            while i <= 6:
                cxp = gx + i * sp + off + (hash01(i, j, seed + layer) - 0.5) * 1.2
                cyp = cy + (hash01(i, j, seed + 50 + layer) - 0.5) * 1.0
                i += 1
                if math.hypot(cxp - gx, cyp - gy) > inner_r + rad * 0.55:
                    continue
                if cyp < pile_top + (hash01(i, j, seed + 9) - 0.5) * 3:
                    continue
                cidx = int(hash01(i * 7 + layer, j * 3, seed + 31) * len(rng_cols)) % len(rng_cols)
                gum_ball_disc(balls, cxp, cyp, rad, rng_cols[cidx], dim=dim, mask=interior)
            j += 1
    bm = balls[..., 3] > 0
    # dark gaps between balls inside the pile
    pile = interior & (Y > pile_top + 1.5)
    img[pile & ~bm] = hexc('#1c0c18')
    img[bm] = balls[bm]
    # empty glass at the top of the globe: faint tint (semi transparent)
    air = interior & ~pile & ~bm
    img[air] = (150, 120, 190, 46)
    # glass rim, highlights (semi transparent where allowed)
    ang = np.degrees(np.arctan2(-gdy, gdx))
    rim_px = globe & ~interior
    img[rim_px & (gr > gR - 0.8)] = hexc('#10121a')
    ring = globe & (gr <= gR - 0.8) & (gr > inner_r - 0.5)
    lit = (ang > -10) & (ang < 110)
    img[ring & lit] = (210, 225, 255, 200)
    img[ring & ~lit] = (90, 96, 130, 190)
    # big curved reflection on the right, smaller on the left
    refl = interior & (gr > gR * 0.68) & (gr < gR * 0.84) & (ang > 18) & (ang < 72)
    core = interior & (gr > gR * 0.72) & (gr < gR * 0.80) & (ang > 24) & (ang < 64)

    def over(mask, rgba):
        a = rgba[3] / 255.0
        base_rgb = img[mask, :3].astype(np.float32)
        base_a = img[mask, 3].astype(np.float32) / 255.0
        out_a = a + base_a * (1 - a)
        out = (np.array(rgba[:3], np.float32) * a + base_rgb * base_a[:, None] * (1 - a)) / np.maximum(out_a[:, None], 1e-6)
        img[mask, :3] = np.clip(out, 0, 255).astype(np.uint8)
        img[mask, 3] = np.clip(out_a * 255, 0, 255).astype(np.uint8)

    over(refl, (255, 255, 255, 110))
    over(core, (255, 255, 255, 150))
    refl2 = interior & (gr > gR * 0.74) & (gr < gR * 0.86) & (ang > 150) & (ang < 196)
    over(refl2, (220, 220, 255, 70))
    spark = [(int(gx + 0.42 * gR), int(gy - 0.60 * gR))]
    for (sx, sy) in spark:
        for (ddx, ddy, al) in ((0, 0, 255), (1, 0, 170), (-1, 0, 170), (0, 1, 170), (0, -1, 170)):
            img[sy + ddy, sx + ddx] = (255, 255, 255, al)

    # ------------------------------------------------ cap (dome lid) + knob
    cap_cy = 19.5
    dome = ((X - CX) / 16.5) ** 2 + ((Y - cap_cy) / 11.5) ** 2 <= 1.0
    dome &= Y < cap_cy
    skirt = (Y >= cap_cy) & (Y < cap_cy + 4.0) & (np.abs(X - CX) <= 16.5 + (Y - cap_cy) * 0.5)
    capm = dome | skirt
    cdx = (X - CX) / 16.5
    cdy = np.where(Y < cap_cy, (Y - cap_cy) / 11.5, 0.0)
    nz = np.sqrt(np.clip(1 - cdx * cdx - cdy * cdy, 0, 1))
    n = np.sqrt(cdx * cdx + cdy * cdy + nz * nz) + 1e-6
    ndl = (cdx * LIGHT[0] + cdy * LIGHT[1] + nz * LIGHT[2]) / n
    hz = LIGHT + np.array([0, 0, 1.0])
    hz = hz / np.linalg.norm(hz)
    spec = np.clip((cdx * hz[0] + cdy * hz[1] + nz * hz[2]) / n, 0, 1) ** 30
    clev = 0.16 + 0.66 * np.clip(ndl, 0, 1) + 0.7 * spec
    clev = np.where(skirt, clev - 0.12, clev)
    paint(capm, rlev(RED, clev))
    rimc = (Y >= cap_cy + 4.0) & (Y < cap_cy + 6.5) & (np.abs(X - CX) <= 19.0)
    lev2, spec2, _ = shade_rev(X, Y, CX, np.full(X.shape, 19.0), spec_pow=10, spec_amt=0.8)
    paint(rimc, rlev(CHROME, lev2 + spec2 - 0.05 * (Y > cap_cy + 5.5)))
    # knob on top
    knob = (X - CX) ** 2 / 3.4 ** 2 + (Y - 5.0) ** 2 / 3.2 ** 2 <= 1.0
    neck = (np.abs(X - CX) <= 1.6) & (Y >= 7.0) & (Y < 9.5)
    kd = (X - CX) / 3.4
    kdy = (Y - 5.0) / 3.2
    knz = np.sqrt(np.clip(1 - kd * kd - kdy * kdy, 0, 1))
    klev = 0.2 + 0.7 * np.clip(kd * LIGHT[0] + kdy * LIGHT[1] + knz * LIGHT[2], 0, 1)
    paint(neck, rlev(CHROME, np.full(X.shape, 0.45)))
    paint(knob, rlev(CHROME, klev))

    # ------------------------------------------------ outline
    m = img[..., 3] > 0
    e = edge_out(m)
    img[e] = hexc(RED_OUT)
    # dark separation lines between cap/globe/collar/body/base
    for yy in (int(cap_cy + 6.5), int(col_top) - 0, int(body_top), int(base_top)):
        row = (np.floor(Y) == yy) & m & ~(globe & (Y < col_top))
        img[row & (img[..., 3] == 255)] = (np.array(img[row & (img[..., 3] == 255)], np.float32) * [0.55, 0.55, 0.55, 1]).astype(np.uint8)
    return img


def render_crank(frame):
    """overlay: the crank in 4 rotation steps (0, 90, 180, 270 degrees, clockwise)."""
    H, W = MH, MW
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W)
    cx, cy = CRANK_C
    a = math.radians(frame * 90.0)
    ux, uy = math.cos(a), math.sin(a)
    L = 6.5
    # arm
    t = np.clip(((X - cx) * ux + (Y - cy) * uy) / L, 0, 1)
    px, py = cx + t * L * ux, cy + t * L * uy
    d = np.hypot(X - px, Y - py)
    arm = d <= 1.55
    side = (-(X - cx) * uy + (Y - cy) * ux)
    alev = 0.55 + 0.25 * np.clip(-side * LIGHT[1] * 2 + (X - cx) * 0.0, -1, 1)
    alev = 0.50 - 0.28 * np.clip(side * (ux * LIGHT[1] - uy * LIGHT[0]) / 1.5, -1, 1)
    img[arm, :3] = rlev(CHROME, alev)[arm]
    img[arm, 3] = 255
    # hub (round chrome disc with a bolt)
    hd = np.hypot(X - cx, Y - cy)
    hub = hd <= 3.7
    hdx = (X - cx) / 3.7
    hdy = (Y - cy) / 3.7
    hz = np.sqrt(np.clip(1 - hdx * hdx - hdy * hdy, 0, 1))
    hlev = 0.18 + 0.72 * np.clip(hdx * LIGHT[0] + hdy * LIGHT[1] + hz * LIGHT[2], 0, 1)
    img[hub, :3] = rlev(CHROME, hlev)[hub]
    img[hub, 3] = 255
    bolt = hd <= 1.1
    img[bolt] = hexc(CHROME[2])
    # grip knob at the end of the arm (red ball)
    gx, gy = cx + (L + 0.8) * ux, cy + (L + 0.8) * uy
    gd = np.hypot(X - gx, Y - gy)
    grip = gd <= 2.4
    gdx = (X - gx) / 2.4
    gdy = (Y - gy) / 2.4
    gz = np.sqrt(np.clip(1 - gdx * gdx - gdy * gdy, 0, 1))
    glev = 0.15 + 0.78 * np.clip(gdx * LIGHT[0] + gdy * LIGHT[1] + gz * LIGHT[2], 0, 1)
    img[grip, :3] = rlev(RED, glev)[grip]
    img[grip, 3] = 255
    m = img[..., 3] > 0
    img[edge_out(m)] = hexc(CHROME_OUT)
    return img


def render_gum_ball(colour):
    img = np.zeros((10, 10, 4), np.uint8)
    gum_ball_disc(img, 5.0, 5.0, 4.0, colour)
    m = img[..., 3] > 0
    ramp = GUM[colour]
    img[edge_out(m) & (np.mgrid[0:10, 0:10][0] >= 0)] = 0
    # 1 px dark rim on the outer pixels
    rimm = edge_in(m)
    img[rimm, :3] = (img[rimm, :3].astype(np.float32) * 0.62).astype(np.uint8)
    return img


COIN = char_map("""
...oooo...
..o5654o..
.o554443o.
o54365332o
o44666532o
o43565422o
o43354221o
.o333221o.
..o2221o..
...oooo...
""")


def render_coin():
    """10x10 gold coin: lit rim (upper left), embossed four-point star, shine pixel."""
    img = np.zeros((10, 10, 4), np.uint8)
    gold = ramp_arr(GOLD)
    for (y, x), ch in np.ndenumerate(COIN):
        if ch == '.':
            continue
        img[y, x, :3] = gold[0] if ch == 'o' else gold[int(ch)]
        img[y, x, 3] = 255
    return img


# ============================================================ candles
WAX = ['#2a1612', '#5c382c', '#8e6248', '#b98c66', '#d8b286', '#ecd0a6', '#f8e6c6', '#fff6e2']


def render_candle(stick_h=31, W=18):
    """candle in a brass chamberstick; the wick is at the sprite's top (y=0..3).
    The flame sprite (10x16) goes at (+4, -14) relative to the candle's top-left."""
    H = stick_h + 13
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W)
    gold = GOLD
    cx = 9.0
    # ---- dish (thin, wide) with its front rim
    dy0 = H - 4.0
    dish_top = ((X - cx) / 8.6) ** 2 + ((Y - dy0) / 2.2) ** 2 <= 1.0
    dish_rim = (np.abs(X - cx) <= 8.6) & (Y >= dy0) & (((X - cx) / 8.6) ** 2 + ((Y - dy0 - 1.4) / 2.2) ** 2 <= 1.0)
    c = np.clip((X - cx) / 8.6, -1, 1)
    top_lev = 0.66 - 0.22 * c - 0.15 * np.clip((Y - dy0 + 2.2) / 4.4, 0, 1)
    rim_lev = 0.40 - 0.20 * c
    m = dish_top | dish_rim
    img[m, :3] = rlev(gold, np.where(dish_rim & ~dish_top, rim_lev, top_lev))[m]
    img[m, 3] = 255
    # ---- finger ring handle on the right
    hx, hy = cx + 6.6, dy0 - 3.4
    ring = (np.abs(np.hypot(X - hx, (Y - hy) * 1.1) - 2.0) < 0.72) & (X > cx + 4.6)
    img[ring, :3] = rlev(gold, 0.42 + 0.25 * ((Y - hy) < 0))[ring]
    img[ring, 3] = 255
    # ---- socket cup
    st, sb = dy0 - 6.0, dy0 + 0.2
    sock = (Y >= st + 1.0) & (Y <= sb) & (np.abs(X - cx) <= 3.9 + 0.35 * (Y - st))
    sock_lip = (Y >= st) & (Y < st + 1.6) & (np.abs(X - cx) <= 5.0)
    c = np.clip((X - cx) / 5.0, -1, 1)
    slev = 0.40 - 0.28 * c + 0.30 * np.clip(1 - np.abs(c + 0.45) / 0.22, 0, 1)
    sm = sock | sock_lip
    img[sm, :3] = rlev(gold, np.where(sock_lip, slev + 0.14, slev))[sm]
    img[sm, 3] = 255
    # ---- wax stick (7 px wide, centred on x = 9)
    top = 3.0
    stick = (Y >= top) & (Y < st) & (X >= 5.5) & (X < 12.5)
    c = np.clip((X - cx) / 3.5, -1, 1)
    glow = np.clip(1 - (Y - top) / 10.0, 0, 1)
    wlev = 0.58 - 0.34 * c + 0.18 * glow - 0.10 * np.clip((Y - top) / 30.0, 0, 1)
    wlev = np.where(c < -0.7, wlev + 0.10, wlev)
    img[stick, :3] = rlev(WAX, wlev)[stick]
    img[stick, 3] = 255
    # melted top: lit rim, a glowing pool around the wick
    rim_row = stick & (Y < top + 1.0)
    img[rim_row, :3] = rlev(WAX, np.full(X.shape, 0.92))[rim_row]
    pool = rim_row & (X >= 7.0) & (X < 11.0)
    img[pool, :3] = hexc('#ffe9b0')[:3]
    # drips running down the front (lighter, with a round bead at the end)
    for (xd, dl) in ((6, 7), (10, 11), (11, 4)):
        for yy in range(int(top) + 1, int(top) + dl):
            img[yy, xd, :3] = rlev(WAX, np.array(0.86 - 0.30 * (xd > 9) - 0.012 * (yy - top)))
        ye = int(top) + dl
        img[ye, xd, :3] = rlev(WAX, np.array(0.74 - 0.30 * (xd > 9)))
        if xd + 1 < 12.5:
            img[ye - 1, xd + 1, :3] = rlev(WAX, np.array(0.62 - 0.30 * (xd > 9)))
    # wick
    img[1, 9] = hexc('#1a0e0a')
    img[2, 9] = hexc('#2a1810')
    img[2, 8] = hexc('#4a2a18')
    # ---- outline
    mm = img[..., 3] > 0
    e = edge_out(mm)
    img[e] = hexc('#140a06')
    img[0, 9] = 0
    img[0, 8] = 0
    img[0, 10] = 0
    return img


def render_flame(frame):
    """10x16 flame; frame 0..2 calm flicker.  Semi-transparent glow pixels around it."""
    W, H = 10, 16
    img = np.zeros((H, W, 4), np.uint8)
    X, Y = grid(H, W)
    lean = (0.0, -0.7, 0.6)[frame]
    tip_y = (2.4, 3.3, 1.8)[frame]
    base_y = 15.0
    cx = 5.0
    # teardrop: radius profile along y
    t = np.clip((Y - tip_y) / (base_y - tip_y), 0, 1)
    r = 2.9 * np.clip(np.sin(np.pi * np.clip(t, 0, 1) ** 0.75), 0, 1) ** 0.9
    xc = cx + lean * (1 - t) ** 1.5
    dd = np.abs(X - xc) / np.maximum(r, 0.01)
    flame = (Y >= tip_y) & (Y <= base_y) & (dd <= 1.0)
    core = flame & (dd <= 0.48) & (t > 0.42) & (t < 0.93)
    mid = flame & (dd <= 0.78) & (t > 0.18) & ~core
    blue = flame & (t > 0.93)
    img[flame] = hexc('#ff7a1c')
    img[mid] = hexc('#ffc63a')
    img[core] = hexc('#fff4c8')
    img[blue] = hexc('#8a5ad8')
    tipm = flame & (t < 0.12)
    img[tipm] = hexc('#e8541a')
    # glow halo (semi transparent)
    halo = dilate(flame, 1, diag=True) & ~flame
    img[halo] = (255, 150, 60, 80)
    halo2 = dilate(flame, 2) & ~dilate(flame, 1, diag=True) & (Y > tip_y + 2)
    img[halo2] = (255, 130, 50, 36)
    return img
