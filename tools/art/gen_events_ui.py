"""Event icons + event sprites + UI icons for Dice Rush Extended.

Sizes: icons 160x160 (native 40x40 x4); extra UI icons 128x128 (native 32x32 x4);
sprites as specified (native = size/4, p1/p2 cursors 48px = 16x16 x3).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pix import hexc, mix, darken, lighten, to_img, contact_sheet, OUT_ROOT, sprite, outline_arr, pad
from iconkit import Icon, OUTLINE, star_pts, sparkle, to_png
import fonts
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

EV = os.path.join(OUT_ROOT, 'events')
UI = os.path.join(OUT_ROOT, 'ui')

GOLD, GOLD_HI, GOLD_SH = '#ffc828', '#fff4a8', '#b87a08'


# ------------------------------------------------------------------ shared drawers
def coin(ic, cx, cy, r, tilt=1.0, mark=True):
    ic.part(lambda c: c.ellipse(cx, cy, r, r * tilt, '#fff'), GOLD, hi=GOLD_HI, sh=GOLD_SH)
    if r >= 3.5:
        ic.raw(lambda c: c.ellipse(cx, cy, r - 1.6, (r - 1.6) * tilt, '#e8a414', fill=False))
    if mark and r >= 4.5:
        ix, iy = int(math.floor(cx)), int(math.floor(cy))
        hh = max(1, int(round((r - 2.5) * tilt)))
        ic.raw(lambda c: (c.rect(ix, iy - hh, ix, iy + hh, '#b87a08')))
    ic.raw(lambda c: c.px(int(cx - r * 0.45), int(cy - r * 0.45 * tilt), '#ffffff'))


def coin_stack(ic, cx, by, n, r=4.5):
    for k in range(n):
        y = by - k * 2
        ic.part(lambda c, y=y: c.ellipse(cx, y, r, r * 0.45, '#fff'), GOLD, hi=GOLD_HI, sh=GOLD_SH)


def mini_die(ic, x0, y0, w, top='#f4f4f8', left='#d0d4e0', right='#a8aec0', pip='#1b1b24', pips=(1, 2, 3), outline=OUTLINE):
    """small iso die in the dice style: x0,y0 = top-left of the bounding box; w even."""
    hw = w / 2.0
    th = round(hw * 0.6)
    sh = round(hw * 0.95)
    T = (x0 + hw, y0)
    L = (x0, y0 + th)
    R = (x0 + w, y0 + th)
    F = (x0 + hw, y0 + 2 * th)
    BL = (x0, y0 + th + sh)
    B = (x0 + hw, y0 + 2 * th + sh)
    BR = (x0 + w, y0 + th + sh)
    ic.part(lambda c: (c.poly([T, R, F, L], '#fff'), c.poly([L, F, B, BL], '#fff'), c.poly([F, R, BR, B], '#fff')),
            top, shade=False, outline=outline)
    ic.raw(lambda c: (c.poly([L, F, B, BL], left), c.poly([F, R, BR, B], right)))
    ic.raw(lambda c: (c.line(L[0], L[1], F[0] - 0.5, F[1], outline), c.line(F[0] - 0.5, F[1], R[0] - 1, R[1], outline),
                      c.line(F[0] - 0.5, F[1], B[0] - 0.5, B[1] - 1, outline)))

    def face_pt(f, u, v):
        if f == 0:
            o, uu, vv = T, (R[0] - T[0], R[1] - T[1]), (L[0] - T[0], L[1] - T[1])
        elif f == 1:
            o, uu, vv = L, (F[0] - L[0], F[1] - L[1]), (BL[0] - L[0], BL[1] - L[1])
        else:
            o, uu, vv = F, (R[0] - F[0], R[1] - F[1]), (B[0] - F[0], B[1] - F[1])
        return (o[0] + u * uu[0] + v * vv[0], o[1] + u * uu[1] + v * vv[1])
    lay = {1: [(0.5, 0.5)], 2: [(0.28, 0.28), (0.72, 0.72)], 3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
           4: [(0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)], 5: [(0.28, 0.28), (0.72, 0.28), (0.5, 0.5), (0.28, 0.72), (0.72, 0.72)],
           6: [(0.3, 0.22), (0.3, 0.5), (0.3, 0.78), (0.7, 0.22), (0.7, 0.5), (0.7, 0.78)]}
    big = w >= 16
    for f, n in enumerate(pips):
        if not n:
            continue
        for (u, v) in lay[n]:
            if f == 2:
                u = 1 - u
            px, py = face_pt(f, u, v)
            ix, iy = int(math.floor(px)), int(math.floor(py))
            if big:
                ic.raw(lambda c, ix=ix, iy=iy: (c.rect(ix - 1, iy, ix, iy, pip), c.rect(ix - 1, iy - 1, ix, iy - 1, pip) if f else None))
            else:
                ic.px(ix, iy, pip)
    return (T, R, F, L, BL, B, BR)


def iso_cube(w=15, S=7, top='#ffffff', left='#d0d4e0', right='#9aa0b4', pip='#1b1b24', pips=(1, 2, 3),
             edge='#ffffff', outline=OUTLINE):
    """small die built exactly like the big dice: 0.6 slope, dark seams, light rims.
    w must be odd. Returns RGBA array (with 1px outline)."""
    c = (w - 1) // 2
    K = int(math.floor(c * 0.6 + 0.5))

    def k_of(x):
        return int(math.floor(abs(x - c) * 0.6 + 0.5))
    H = 2 * K + S + 1
    a = np.zeros((H + 2, w + 2, 4), np.uint8)
    face = np.full((H, w), -1, np.int8)
    for x in range(w):
        k = k_of(x)
        for y in range(k, 2 * K - k + 1):
            face[y, x] = 0
        for y in range(2 * K - k + 1, 2 * K - k + 1 + S):
            if y < H:
                face[y, x] = 3 if (x == c or y == 2 * K - k + 1) else (1 if x < c else 2)
    cols = {0: hexc(top), 1: hexc(left), 2: hexc(right), 3: hexc(outline)}
    for y in range(H):
        for x in range(w):
            f = face[y, x]
            if f < 0:
                continue
            col = cols[int(f)]
            if f == 0:
                # light rim on the top face border
                nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if any(not (0 <= xx < w and 0 <= yy < H) or face[yy, xx] != 0 for xx, yy in nb):
                    col = mix(edge, top, 0.35)
            a[y + 1, x + 1] = col
    # pips via face uv
    Tp, Rp, Fp, Lp = (c + 0.5, 0.0), (w, K + 0.5), (c + 0.5, 2 * K + 1.0), (0.0, K + 0.5)
    BLp, Bp = (0.0, K + 0.5 + S), (c + 0.5, 2 * K + 1.0 + S)

    def pt(f, u, v):
        if f == 0:
            o, uu, vv = Tp, (Rp[0] - Tp[0], Rp[1] - Tp[1]), (Lp[0] - Tp[0], Lp[1] - Tp[1])
        elif f == 1:
            o, uu, vv = Lp, (Fp[0] - Lp[0], Fp[1] - Lp[1]), (BLp[0] - Lp[0], BLp[1] - Lp[1])
        else:
            o, uu, vv = Fp, (Rp[0] - Fp[0], Rp[1] - Fp[1]), (Bp[0] - Fp[0], Bp[1] - Fp[1])
        return o[0] + u * uu[0] + v * vv[0], o[1] + u * uu[1] + v * vv[1]
    lay = {1: [(0.5, 0.5)], 2: [(0.27, 0.27), (0.73, 0.73)], 3: [(0.24, 0.24), (0.5, 0.5), (0.76, 0.76)],
           4: [(0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)], 5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
           6: [(0.3, 0.24), (0.3, 0.5), (0.3, 0.76), (0.7, 0.24), (0.7, 0.5), (0.7, 0.76)]}
    for f, n in enumerate(pips):
        if not n:
            continue
        for (u, v) in lay[n]:
            if f == 0:
                u, v = v, u
            if f == 2:
                u = 1 - u
            px, py = pt(f, u, v)
            ix, iy = int(math.floor(px)), int(math.floor(py))
            cells = [(ix, iy)]
            if n == 1 or w >= 19:
                cells += [(ix - 1, iy), (ix, iy - 1), (ix - 1, iy - 1)] if f else [(ix - 1, iy)]
            for (qx, qy) in cells:
                if 0 <= qy < H and 0 <= qx < w and face[qy, qx] == f:
                    a[qy + 1, qx + 1] = hexc(pip)
    return outline_arr(a, outline)


def clover(ic, cx, cy, s, glow=False):
    """four heart leaves around (cx,cy); s = leaf radius."""
    G, Ghi, Gsh = '#3ac04a', '#a8f08a', '#1a7a2a'
    if glow:
        ic.raw(lambda c: c.circle(cx, cy, s * 2.9, '#fff7b0'))
        ic.raw(lambda c: c.circle(cx, cy, s * 2.5, '#fffbd8'))
    # stem
    ic.part(lambda c: c.line(cx + 1, cy + 1, cx + s * 1.6, cy + s * 3.0, '#fff', w=2), '#2a9a3a', sh=Gsh)
    d = s * 1.05
    for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        lx, ly = cx + dx * d, cy + dy * d
        # heart = two lobes + point toward the centre
        px_, py_ = -dy, dx
        def leaf(c, lx=lx, ly=ly, px_=px_, py_=py_, dx=dx, dy=dy):
            c.circle(lx + px_ * s * 0.55 + dx * s * 0.3, ly + py_ * s * 0.55 + dy * s * 0.3, s * 0.78, '#fff')
            c.circle(lx - px_ * s * 0.55 + dx * s * 0.3, ly - py_ * s * 0.55 + dy * s * 0.3, s * 0.78, '#fff')
            c.poly([(cx, cy), (lx + px_ * s * 1.1 + dx * s * 0.2, ly + py_ * s * 1.1 + dy * s * 0.2),
                    (lx - px_ * s * 1.1 + dx * s * 0.2, ly - py_ * s * 1.1 + dy * s * 0.2)], '#fff')
        ic.part(leaf, G, hi=Ghi, sh=Gsh)
    # veins
    ic.raw(lambda c: (c.line(cx, cy, cx, cy - d * 1.2, Gsh), c.line(cx, cy, cx + d * 1.2, cy, Gsh),
                      c.line(cx, cy, cx, cy + d * 1.2, Gsh), c.line(cx, cy, cx - d * 1.2, cy, Gsh)))
    ic.raw(lambda c: c.px(int(cx - d * 0.9 - s * 0.4), int(cy - s * 0.6), '#e8ffd8'))


def padlock_open(ic, cx, top, s=1.0, col=GOLD, hi=GOLD_HI, sh=GOLD_SH):
    """unlocked padlock: the shackle is lifted and shifted right, its left leg
    hangs free above the body (clear gap) while the right leg stays inserted."""
    w = int(round(16 * s))
    h = int(round(11 * s))
    x0 = int(round(cx - w / 2))
    y0 = int(round(top + 13 * s))
    scx, scy = cx + 3.5 * s, top + 6.0 * s
    ro, ri = 6.0 * s, 3.9 * s

    def shackle(c):
        for y in range(int(scy - ro) - 1, int(y0 + 3 * s) + 1):
            for x in range(int(scx - ro) - 1, int(scx + ro) + 2):
                px_, py_ = x + 0.5, y + 0.5
                d = math.hypot(px_ - scx, py_ - scy)
                if py_ <= scy and ri <= d <= ro:
                    c.px(x, y, '#fff')
                elif py_ > scy:
                    if scx + ri <= px_ <= scx + ro and py_ <= y0 + 2 * s:
                        c.px(x, y, '#fff')        # right leg into the body
                    if scx - ro <= px_ <= scx - ri and py_ <= scy + 2.6 * s:
                        c.px(x, y, '#fff')        # left leg, free
    ic.part(shackle, '#c8ccd8', hi='#ffffff', sh='#6a7282')
    ic.part(lambda c: c.rect(x0, y0, x0 + w - 1, y0 + h - 1, '#fff'), col, hi=hi, sh=sh, band=2)
    kx = int(round(cx)) - 1
    ky = y0 + int(h * 0.3)
    ic.raw(lambda c: (c.rect(kx, ky, kx + 1, ky + 1, '#5a3a08'), c.rect(kx, ky + 2, kx + 1, ky + 2 + max(1, int(2 * s)), '#5a3a08')))


def gamepad(ic, cx, cy, col, w=18, h=10, btn=('#ff3a3a', '#3ac04a', '#3a8aff', '#ffd23a')):
    x0, y0 = cx - w / 2, cy - h / 2
    ic.part(lambda c: (c.ellipse(x0 + 3.5, y0 + h * 0.65, 4.0, h * 0.55, '#fff'), c.ellipse(x0 + w - 3.5, y0 + h * 0.65, 4.0, h * 0.55, '#fff'),
                       c.rect(int(x0 + 2), int(y0), int(x0 + w - 3), int(y0 + h * 0.7), '#fff')), col, band=1)
    dx, dy = int(x0 + 4), int(cy - 1)
    ic.raw(lambda c: (c.rect(dx - 1, dy, dx + 1, dy, '#1b1b24'), c.rect(dx, dy - 1, dx, dy + 1, '#1b1b24')))
    bx, by = int(x0 + w - 5), int(cy - 1)
    ic.raw(lambda c: (c.px(bx, by - 1, btn[3]), c.px(bx - 1, by, btn[2]), c.px(bx + 1, by, btn[0]), c.px(bx, by + 1, btn[1])))


def sack(ic, cx, cy, r, col='#d8b878', sh='#9a7a3a', mark='$'):
    ic.part(lambda c: (c.ellipse(cx, cy, r, r * 0.95, '#fff'), c.poly([(cx - r * 0.45, cy - r * 1.25), (cx + r * 0.45, cy - r * 1.25),
                                                                       (cx + r * 0.3, cy - r * 0.8), (cx - r * 0.3, cy - r * 0.8)], '#fff')),
            col, sh=sh)
    ic.raw(lambda c: c.rect(int(cx - r * 0.45), int(cy - r * 0.9), int(cx + r * 0.45), int(cy - r * 0.9), darken(col, 0.5)))
    if mark == '$':
        m = fonts.text_mask('$', {'$': """
.#.
###
#..
###
..#
###
.#."""})
        h, w = m.shape
        ox, oy = int(round(cx - w / 2)), int(round(cy - h / 2 + r * 0.1))
        ic.raw(lambda c: [c.px(ox + x, oy + y, darken(col, 0.55)) for y in range(h) for x in range(w) if m[y, x]])


def bolt(ic, x, y, s=1.0, col='#ffe23a'):
    pts = [(x + 4 * s, y), (x + 9 * s, y), (x + 6 * s, y + 5 * s), (x + 9 * s, y + 5 * s), (x + 2 * s, y + 14 * s),
           (x + 4 * s, y + 8 * s), (x + 1 * s, y + 8 * s)]
    ic.part(lambda c: c.poly(pts, '#fff'), col, hi='#fffbd0', sh='#c8901a')


# ------------------------------------------------------------------ event icons (40x40)
def meteor(ic, cx, cy, r, ang=math.radians(-35), L=None):
    L = L or r * 4.2
    ux, uy = math.cos(ang), math.sin(ang)   # direction toward the tail (up-right)
    nx, ny = -uy, ux
    tx, ty = cx + ux * L, cy + uy * L
    for (k, col) in ((1.0, '#e8301a'), (0.72, '#ff8a1f'), (0.42, '#ffe25a')):
        w = r * k
        pts = [(cx + nx * w, cy + ny * w), (tx, ty), (cx - nx * w, cy - ny * w)]
        ic.part(lambda c, pts=pts: (c.poly(pts, '#fff'), c.circle(cx, cy, w * 1.05, '#fff')), col, shade=False,
                outline=OUTLINE if k == 1.0 else None)
    ic.part(lambda c: c.circle(cx, cy, r * 0.85, '#fff'), '#7a5a48', hi='#b8957e', sh='#4a3022')
    if r >= 3:
        ic.raw(lambda c: (c.px(int(cx), int(cy + r * 0.2), '#4a3022'), c.px(int(cx - r * 0.4), int(cy - r * 0.1), '#5a4030')))


def ev_meteor_shower():
    ic = Icon(40)
    for (x, y) in ((4, 30), (20, 4), (34, 22), (8, 12), (27, 36)):
        sparkle(ic, x, y, 1, '#ffffff', '#8ab0ff')
    meteor(ic, 28, 12, 3.2)
    meteor(ic, 13, 22, 5.2)
    meteor(ic, 30, 30, 2.6)
    return ic


def ev_coin_rain():
    ic = Icon(40)
    # cloud
    ic.part(lambda c: (c.circle(12, 10, 6, '#fff'), c.circle(20, 7, 7, '#fff'), c.circle(28, 10, 6, '#fff'), c.rect(8, 10, 32, 15, '#fff')),
            '#f4f6ff', hi='#ffffff', sh='#a8acc8')
    for (x, y, r, t) in ((9, 22, 3.6, 1.0), (19, 27, 4.4, 0.55), (29, 21, 3.6, 0.8), (13, 34, 3.4, 0.7), (27, 34, 4.2, 1.0)):
        coin(ic, x, y, r, t, mark=r > 4)
    sparkle(ic, 35, 28, 1)
    sparkle(ic, 4, 30, 1)
    return ic


def ev_tornado():
    ic = Icon(40)
    rows = [(4, 15.0), (9, 13.0), (14, 11.0), (19, 8.6), (24, 6.4), (28, 4.6), (32, 3.2), (35, 2.2)]
    for i, (y, w) in enumerate(rows):
        cx = 20 + math.sin(i * 0.9) * 2.5
        ic.part(lambda c, y=y, w=w, cx=cx: c.ellipse(cx, y, w, 3.0, '#fff'), '#a8b4c8', hi='#e8f0ff', sh='#5a6a84')
    ic.raw(lambda c: (c.line(9, 4, 29, 5, '#e8f0ff'), c.line(11, 13, 27, 15, '#e8f0ff'), c.line(15, 23, 24, 24, '#e8f0ff')))
    # debris
    for (x, y, col) in ((4, 12, '#a8642a'), (35, 9, '#5ac83a'), (33, 20, '#a8642a'), (6, 24, '#ffd23a')):
        ic.part(lambda c, x=x, y=y: c.rect(x, y, x + 1, y + 1, '#fff'), col)
    # dust base
    ic.part(lambda c: (c.ellipse(16, 37, 5, 2.4, '#fff'), c.ellipse(24, 37, 5, 2.4, '#fff')), '#c8b898', sh='#8a7a5a')
    return ic


def ev_happy_hour():
    ic = Icon(40)
    # clock
    ic.part(lambda c: c.circle(14, 14, 11.5, '#fff'), '#ffc828', hi='#fff4a8', sh='#b87a08', band=2)
    ic.part(lambda c: c.circle(14, 14, 8.6, '#fff'), '#fff8ec', sh='#d8ccb0')
    ic.raw(lambda c: ([c.px(int(14 + math.cos(k * math.pi / 6) * 7), int(14 + math.sin(k * math.pi / 6) * 7), '#8a7a5a') for k in range(12)],
                      c.line(14, 14, 14, 8, '#1b1b24'), c.line(14, 14, 18, 15, '#1b1b24'), c.px(14, 14, '#e8261c')))
    # cocktail glass
    ic.part(lambda c: c.poly([(17, 19), (38, 19), (27.5, 30)], '#fff'), '#d8f4ff', hi='#ffffff', sh='#8ab8d0')
    ic.raw(lambda c: c.poly([(19.5, 21), (35.5, 21), (27.5, 28.5)], '#ff4a9a'))
    ic.raw(lambda c: (c.px(24, 23, '#ffb0d0'), c.px(29, 22, '#ffb0d0'), c.px(27, 25, '#ffffff')))
    ic.part(lambda c: (c.rect(27, 30, 28, 36, '#fff'), c.ellipse(27.5, 37.0, 5.0, 1.6, '#fff')), '#d8f4ff', hi='#ffffff', sh='#8ab8d0')
    # cherry + straw
    ic.part(lambda c: c.line(31, 20, 36, 11, '#fff'), '#ffd23a')
    ic.part(lambda c: c.circle(23, 19, 2.2, '#fff'), '#e8261c', hi='#ff9a9a', sh='#8a0c08')
    ic.raw(lambda c: c.line(23, 17, 25, 13, '#3a8a2a'))
    sparkle(ic, 36, 4, 2)
    sparkle(ic, 3, 32, 1)
    sparkle(ic, 37, 26, 1)
    return ic


def ev_rainbow():
    ic = Icon(40)
    cols = ['#ff3a3a', '#ff9a1f', '#ffe23a', '#4fd040', '#3a8aff', '#a04aff']
    for i, col in enumerate(cols):
        R = 17 - i * 2
        ic.part(lambda c, R=R: (c.circle(20, 26, R, '#fff'), c.rect(0, 26, 39, 39, None)), col, outline=OUTLINE if i == 0 else None,
                shade=False)
    ic.raw(lambda c: (c.circle(20, 26, 5, None), c.rect(0, 26, 39, 39, None)))
    ic.a = outline_arr(ic.a, OUTLINE)
    for cx in (6, 34):
        ic.part(lambda c, cx=cx: (c.circle(cx - 3, 28, 4, '#fff'), c.circle(cx + 2, 26, 5, '#fff'), c.circle(cx + 5, 29, 3.5, '#fff'),
                                  c.rect(cx - 6, 28, cx + 8, 32, '#fff')), '#ffffff', sh='#b8bcd8')
    sparkle(ic, 20, 3, 2)
    sparkle(ic, 6, 12, 1)
    sparkle(ic, 35, 13, 1)
    return ic


def cat_sitting(ic, cx, by):
    blk, bhi, bsh = '#2a2436', '#5a5070', '#141018'
    # tail
    ic.part(lambda c: (c.line(cx + 7, by - 2, cx + 13, by - 8, '#fff', w=3), c.line(cx + 13, by - 8, cx + 12, by - 16, '#fff', w=3)), blk, hi=bhi, sh=bsh)
    # body
    ic.part(lambda c: c.ellipse(cx, by - 8, 8.5, 8.5, '#fff'), blk, hi=bhi, sh=bsh)
    # head + ears
    ic.part(lambda c: (c.ellipse(cx, by - 20, 8.2, 7.0, '#fff'), c.poly([(cx - 8, by - 22), (cx - 7, by - 31), (cx - 1.5, by - 25)], '#fff'),
                       c.poly([(cx + 8, by - 22), (cx + 7, by - 31), (cx + 1.5, by - 25)], '#fff')), blk, hi=bhi, sh=bsh)
    ic.raw(lambda c: (c.poly([(cx - 6.5, by - 25), (cx - 6, by - 29), (cx - 3, by - 25.5)], '#ff8fb8'),
                      c.poly([(cx + 6.5, by - 25), (cx + 6, by - 29), (cx + 3, by - 25.5)], '#ff8fb8')))
    # eyes
    for ex in (cx - 4, cx + 2):
        ex = int(ex)
        ic.raw(lambda c, ex=ex: (c.rect(ex, by - 22, ex + 2, by - 19, '#ffe23a'), c.rect(ex + 1, by - 22, ex + 1, by - 19, '#1b1420'),
                                 c.px(ex, by - 22, '#fffbd0')))
    ic.raw(lambda c: (c.px(int(cx) - 1, by - 17, '#ff8fb8'), c.px(int(cx), by - 17, '#ff8fb8'),
                      c.line(cx - 11, by - 18, cx - 6, by - 17, '#8a80a0'), c.line(cx + 6, by - 17, cx + 10, by - 18, '#8a80a0'),
                      c.line(cx - 11, by - 15, cx - 6, by - 16, '#8a80a0'), c.line(cx + 6, by - 16, cx + 10, by - 15, '#8a80a0')))
    # front paws
    ic.part(lambda c: (c.ellipse(cx - 3, by - 1, 2.6, 1.6, '#fff'), c.ellipse(cx + 3, by - 1, 2.6, 1.6, '#fff')), blk, hi=bhi, sh=bsh)


def ev_black_cat():
    ic = Icon(40)
    ic.raw(lambda c: c.ellipse(19, 37, 12, 2.2, '#3a3448'))
    cat_sitting(ic, 18, 37)
    sparkle(ic, 34, 6, 1, '#ffe23a', '#ffb020')
    ic.raw(lambda c: (c.circle(32.5, 8.5, 4.2, '#ffe890'), c.circle(34.5, 7.0, 3.6, None)))
    return ic


def chest(ic, x0, y0, w, h, opened=False, gold=True):
    """treasure chest; (x0,y0) top-left of the body."""
    wood, whi, wsh = '#b8742a', '#e0a060', '#6a3a14'
    band = '#ffc828'
    lid_h = int(h * 0.45)
    if opened:
        # lid tilted back
        ic.part(lambda c: c.poly([(x0 + 1, y0 - 1), (x0 + w - 2, y0 - 1), (x0 + w - 4, y0 - lid_h - 3), (x0 + 3, y0 - lid_h - 3)], '#fff'),
                wood, hi=whi, sh=wsh)
        ic.raw(lambda c: (c.poly([(x0 + 3, y0 - 2), (x0 + w - 4, y0 - 2), (x0 + w - 5, y0 - lid_h - 1), (x0 + 4, y0 - lid_h - 1)], '#5a2e10')))
        ic.raw(lambda c: (c.line(x0 + 3, y0 - lid_h - 3, x0 + w - 4, y0 - lid_h - 3, band)))
        if gold:
            for (gx, gy, r) in ((x0 + w * 0.3, y0 - 1, 3.6), (x0 + w * 0.55, y0 - 3, 4.2), (x0 + w * 0.75, y0 - 1, 3.4), (x0 + w * 0.45, y0, 3.0)):
                coin(ic, gx, gy, r, 0.8, mark=False)
            ic.part(lambda c: c.poly([(x0 + w * 0.62, y0 - 6), (x0 + w * 0.7, y0 - 9), (x0 + w * 0.78, y0 - 6), (x0 + w * 0.7, y0 - 3)], '#fff'),
                    '#3ad8ff', hi='#ffffff', sh='#1a7aa8')
            ic.part(lambda c: c.poly([(x0 + w * 0.2, y0 - 4), (x0 + w * 0.26, y0 - 7), (x0 + w * 0.32, y0 - 4), (x0 + w * 0.26, y0 - 1)], '#fff'),
                    '#ff3a6a', hi='#ffb0c0', sh='#8a0c28')
    else:
        ic.part(lambda c: (c.rect(x0, y0 - lid_h, x0 + w - 1, y0, '#fff'), c.ellipse(x0 + w / 2, y0 - lid_h + 1, w / 2, 3.2, '#fff')),
                wood, hi=whi, sh=wsh)
        ic.raw(lambda c: c.rect(x0, y0, x0 + w - 1, y0, '#5a2e10'))
    # body
    ic.part(lambda c: c.rect(x0, y0 + 1, x0 + w - 1, y0 + h - 1, '#fff'), wood, hi=whi, sh=wsh)
    ic.raw(lambda c: (c.rect(x0, y0 + 1, x0 + w - 1, y0 + 2, band), c.rect(x0 + 2, y0 + 1, x0 + 3, y0 + h - 1, band),
                      c.rect(x0 + w - 4, y0 + 1, x0 + w - 3, y0 + h - 1, band),
                      c.line(x0 + 5, y0 + int(h * 0.6), x0 + w - 6, y0 + int(h * 0.6), wsh)))
    lx = x0 + w // 2 - 2
    ic.part(lambda c: c.rect(lx, y0 + 1, lx + 3, y0 + 5, '#fff'), band, hi=GOLD_HI, sh=GOLD_SH)
    ic.raw(lambda c: (c.px(lx + 1, y0 + 3, '#3a2010'), c.px(lx + 2, y0 + 3, '#3a2010'), c.px(lx + 1, y0 + 4, '#3a2010')))


def ev_treasure_chest():
    ic = Icon(40)
    chest(ic, 6, 20, 28, 16, opened=True)
    sparkle(ic, 9, 6, 2)
    sparkle(ic, 33, 8, 1)
    sparkle(ic, 21, 3, 1)
    return ic


def thief_fig(ic, cx, by, run=False):
    skin, sk_sh = '#f6c896', '#d8986a'
    # sack over the shoulder (behind)
    sack(ic, cx + 9, by - 19, 6.0, col='#d8b878', sh='#9a7a3a')
    # legs
    if run:
        ic.part(lambda c: (c.line(cx - 2, by - 8, cx - 7, by - 2, '#fff', w=3), c.line(cx + 2, by - 8, cx + 6, by - 1, '#fff', w=3)), '#2a2a3a')
        ic.part(lambda c: (c.rect(int(cx - 10), by - 2, int(cx - 6), by - 1, '#fff'), c.rect(int(cx + 5), by - 1, int(cx + 9), by, '#fff')), '#1b1b20')
    else:
        ic.part(lambda c: (c.rect(int(cx - 4), by - 9, int(cx - 1), by - 2, '#fff'), c.rect(int(cx + 1), by - 9, int(cx + 4), by - 2, '#fff')), '#2a2a3a')
        ic.part(lambda c: (c.rect(int(cx - 6), by - 2, int(cx - 1), by, '#fff'), c.rect(int(cx + 1), by - 2, int(cx + 6), by, '#fff')), '#1b1b20')
    # striped shirt
    ic.part(lambda c: c.ellipse(cx, by - 13, 6.5, 5.5, '#fff'), '#f2f2f8', sh='#b8bcc8')
    ic.raw(lambda c: [c.rect(int(cx - 6), by - 16 + k * 3, int(cx + 6), by - 16 + k * 3, '#1b1b24') for k in range(3)])
    ic.a = ic.a  # keep
    # head
    ic.part(lambda c: c.ellipse(cx, by - 24, 6.8, 6.4, '#fff'), skin, sh=sk_sh)
    # beanie
    ic.part(lambda c: (c.ellipse(cx, by - 27, 7.0, 4.4, '#fff'), c.rect(int(cx - 7), by - 27, int(cx + 6), by - 26, '#fff')), '#2a2a34', hi='#5a5a6a')
    # eye mask
    ic.part(lambda c: c.rect(int(cx - 7), by - 25, int(cx + 6), by - 22, '#fff'), '#1b1b24', hi='#3a3a48', shade=False)
    ic.raw(lambda c: (c.rect(int(cx - 4), by - 24, int(cx - 3), by - 23, '#ffffff'), c.rect(int(cx + 2), by - 24, int(cx + 3), by - 23, '#ffffff'),
                      c.px(int(cx - 3), by - 23, '#1b1b24'), c.px(int(cx + 3), by - 23, '#1b1b24'),
                      c.rect(int(cx - 2), by - 19, int(cx + 1), by - 19, '#7a2a1a')))
    # stubble
    ic.raw(lambda c: (c.px(int(cx - 3), by - 20, '#c8986a'), c.px(int(cx + 3), by - 20, '#c8986a'), c.px(int(cx), by - 18, '#c8986a')))
    # arm holding the sack
    ic.part(lambda c: c.line(cx + 4, by - 15, cx + 7, by - 22, '#fff', w=2), '#f2f2f8', sh='#b8bcc8')
    ic.part(lambda c: c.circle(cx + 7.5, by - 22.5, 1.8, '#fff'), skin, sh=sk_sh)


def ev_thief():
    ic = Icon(40)
    thief_fig(ic, 16, 38)
    for (x, y) in ((33, 34), (36, 30)):
        coin(ic, x, y, 2.6, 1.0, mark=False)
    return ic


def ev_lucky_clover():
    ic = Icon(40)
    clover(ic, 19, 17, 5.2)
    sparkle(ic, 34, 5, 2)
    sparkle(ic, 5, 31, 1)
    sparkle(ic, 35, 28, 1)
    return ic


# ------------------------------------------------------------------ sprites
def spr_coin():
    ic = Icon(16)
    coin(ic, 8, 8, 6.6, 1.0, mark=True)
    return ic


def spr_meteor():
    ic = Icon(16)
    meteor(ic, 5.5, 10.5, 3.6, L=11)
    return ic


def spr_tornado():
    ic = Icon(32, 40)
    rows = [(4, 14.0), (9, 12.5), (14, 10.5), (19, 8.4), (24, 6.4), (28, 4.8), (32, 3.4), (35, 2.4)]
    for i, (y, w) in enumerate(rows):
        cx = 16 + math.sin(i * 0.9) * 2.2
        ic.part(lambda c, y=y, w=w, cx=cx: c.ellipse(cx, y, w, 3.0, '#fff'), '#a8b4c8', hi='#e8f0ff', sh='#5a6a84')
    ic.raw(lambda c: (c.line(5, 4, 25, 5, '#e8f0ff'), c.line(8, 13, 23, 15, '#e8f0ff'), c.line(12, 23, 20, 24, '#e8f0ff')))
    ic.part(lambda c: (c.ellipse(12, 37.5, 5, 2.0, '#fff'), c.ellipse(20, 37.5, 5, 2.0, '#fff')), '#c8b898', sh='#8a7a5a')
    for (x, y, col) in ((2, 12, '#a8642a'), (29, 9, '#5ac83a'), (28, 21, '#a8642a')):
        ic.part(lambda c, x=x, y=y: c.rect(x, y, x + 1, y + 1, '#fff'), col)
    return ic


def spr_cat_walk():
    ic = Icon(24, 16)
    blk, bhi, bsh = '#2a2436', '#5a5070', '#141018'
    # tail up
    ic.part(lambda c: (c.line(4, 7, 2, 3, '#fff', w=2), c.line(2, 3, 3, 1, '#fff', w=2)), blk, hi=bhi, sh=bsh)
    # legs (walking)
    ic.part(lambda c: (c.line(6, 10, 4, 14, '#fff', w=2), c.line(9, 10, 10, 14, '#fff', w=2), c.line(14, 10, 13, 14, '#fff', w=2),
                       c.line(17, 10, 19, 14, '#fff', w=2)), blk, hi=bhi, sh=bsh)
    ic.part(lambda c: c.ellipse(11.5, 8.5, 7.5, 3.4, '#fff'), blk, hi=bhi, sh=bsh)
    ic.part(lambda c: (c.ellipse(19.5, 6.0, 3.8, 3.4, '#fff'), c.poly([(16.5, 4), (17, 0), (19, 3)], '#fff'), c.poly([(20, 3), (22, 0), (22.5, 4)], '#fff')),
            blk, hi=bhi, sh=bsh)
    ic.raw(lambda c: (c.px(20, 5, '#ffe23a'), c.px(21, 5, '#ffe23a'), c.px(21, 5, '#1b1420'), c.px(22, 7, '#ff8fb8')))
    return ic


def spr_thief_run():
    ic = Icon(24, 24)
    skin, sk_sh = '#f6c896', '#d8986a'
    sack(ic, 7, 9, 4.6, col='#d8b878', sh='#9a7a3a')
    ic.part(lambda c: (c.line(11, 16, 7, 21, '#fff', w=2), c.line(13, 16, 17, 21, '#fff', w=2)), '#2a2a3a')
    ic.part(lambda c: (c.rect(5, 21, 8, 22, '#fff'), c.rect(16, 21, 19, 22, '#fff')), '#1b1b20')
    ic.part(lambda c: c.ellipse(12.5, 13.0, 4.4, 4.0, '#fff'), '#f2f2f8', sh='#b8bcc8')
    ic.raw(lambda c: (c.rect(8, 12, 16, 12, '#1b1b24'), c.rect(8, 15, 16, 15, '#1b1b24')))
    ic.part(lambda c: c.line(15, 12, 19, 10, '#fff', w=2), '#f2f2f8', sh='#b8bcc8')
    ic.part(lambda c: c.ellipse(14.5, 6.0, 4.6, 4.4, '#fff'), skin, sh=sk_sh)
    ic.part(lambda c: (c.ellipse(14.0, 3.6, 4.8, 2.8, '#fff')), '#2a2a34', hi='#5a5a6a')
    ic.part(lambda c: c.rect(10, 5, 19, 6, '#fff'), '#1b1b24', shade=False)
    ic.raw(lambda c: (c.px(15, 5, '#ffffff'), c.px(17, 5, '#ffffff'), c.px(16, 8, '#7a2a1a'), c.px(17, 8, '#7a2a1a')))
    ic.part(lambda c: c.line(10, 12, 7, 9, '#fff', w=2), '#f2f2f8', sh='#b8bcc8')
    # speed lines
    ic.raw(lambda c: (c.line(0, 14, 3, 14, '#c8ccd8'), c.line(0, 17, 4, 17, '#c8ccd8'), c.line(1, 20, 3, 20, '#c8ccd8')))
    return ic


def spr_chest(opened):
    ic = Icon(32)
    chest(ic, 3, 15, 26, 15, opened=opened)
    if opened:
        sparkle(ic, 6, 3, 1)
        sparkle(ic, 26, 2, 1)
    return ic


def spr_clover():
    ic = Icon(24)
    clover(ic, 11, 10, 3.2)
    return ic


# ------------------------------------------------------------------ UI icons (40x40)
def ui_shop():
    ic = Icon(40)
    # posts
    ic.part(lambda c: (c.rect(5, 14, 7, 37, '#fff'), c.rect(32, 14, 34, 37, '#fff')), '#a8642a', hi='#d89a5a', sh='#5a3414')
    # awning with scallops
    ic.part(lambda c: (c.poly([(2, 12), (37, 12), (33, 3), (6, 3)], '#fff'),
                       [c.circle(4.5 + k * 5, 13.5, 2.6, '#fff') for k in range(7)]), '#e8261c', hi='#ff7a6a', sh='#8a120c')
    ic.raw(lambda c: [c.poly([(6 + k * 5 + (0 if k else 0), 3), (6 + k * 5 + 2.5, 3), (4.5 + k * 5 + 3, 14), (4.5 + k * 5 + 0.2, 14)], '#ffffff') for k in range(0, 6, 2)])
    ic.a = outline_arr(ic.a, OUTLINE)
    # sign
    ic.part(lambda c: c.rect(13, 0, 26, 4, '#fff'), '#ffc828', hi=GOLD_HI, sh=GOLD_SH)
    ic.raw(lambda c: (c.rect(15, 2, 16, 2, '#8a5208'), c.rect(18, 2, 21, 2, '#8a5208'), c.rect(23, 2, 24, 2, '#8a5208')))
    # counter
    ic.part(lambda c: c.rect(3, 27, 36, 37, '#fff'), '#c8843a', hi='#f0b070', sh='#7a4a1a', band=1)
    ic.raw(lambda c: (c.rect(3, 27, 36, 28, '#e8a050'), c.line(4, 32, 35, 32, '#9a5a24')))
    # die + coins on the counter
    ic.add(iso_cube(15, 7, top='#ffffff', left='#d8dce8', right='#a0a6ba', pip='#1b1b24', pips=(1, 2, 3)), 8, 10)
    coin_stack(ic, 29, 25, 3, r=4.0)
    coin(ic, 29, 19.5, 3.4, 0.9, mark=False)
    return ic


def ui_unlock(n=40):
    ic = Icon(n)
    s = n / 40.0
    padlock_open(ic, 20 * s, 3 * s, s=1.45 * s)
    sparkle(ic, int(5 * s), int(9 * s), 2 if n >= 40 else 1)
    sparkle(ic, int(35 * s), int(30 * s), 1)
    sparkle(ic, int(8 * s), int(33 * s), 1)
    return ic


def ui_design():
    ic = Icon(40)
    # palette
    ic.part(lambda c: (c.ellipse(19, 21, 16.5, 13.5, '#fff')), '#d8a060', hi='#f4cc90', sh='#8a5a24', band=2)
    ic.raw(lambda c: c.ellipse(11.5, 27.5, 3.4, 2.8, None))
    ic.a = outline_arr(ic.a, OUTLINE)
    for (x, y, col) in ((10, 15, '#e8261c'), (17, 11, '#ffd23a'), (25, 12, '#4fd040'), (30, 18, '#3a8aff'), (26, 27, '#a04aff'), (19, 30, '#ffffff')):
        ic.part(lambda c, x=x, y=y: c.circle(x, y, 2.8, '#fff'), col, hi=lighten(col, 0.45), sh=darken(col, 0.35))
    # brush
    ic.part(lambda c: c.line(26, 37, 37, 22, '#fff', w=2), '#5a3a8a', hi='#8a6ac8', sh='#2a1a4a')
    ic.part(lambda c: c.rect(35, 19, 37, 22, '#fff'), '#c8ccd8', hi='#ffffff', sh='#6a7282')
    ic.part(lambda c: c.poly([(35, 19), (37, 19), (38, 15), (37, 13), (35, 15)], '#fff'), '#e8261c', hi='#ff8a80', sh='#8a120c')
    return ic


def ui_coop():
    ic = Icon(40)
    gamepad(ic, 14, 15, '#3a7aff', w=22, h=12)
    gamepad(ic, 25, 27, '#ff8a1f', w=22, h=12)
    sparkle(ic, 35, 6, 1)
    return ic


def ui_host():
    ic = Icon(40)
    # broadcast waves
    for r in (9, 13):
        ic.raw(lambda c, r=r: [c.px(int(20 + math.cos(t) * r), int(22 + math.sin(t) * r * 0.9), '#5affd8')
                               for t in np.linspace(math.radians(200), math.radians(250), 18)] +
               [c.px(int(20 + math.cos(t) * r), int(22 + math.sin(t) * r * 0.9), '#5affd8')
                for t in np.linspace(math.radians(290), math.radians(340), 18)])
    gamepad(ic, 20, 29, '#3a7aff', w=26, h=13)
    # crown on top
    ic.part(lambda c: c.poly([(12, 19), (12, 10), (16, 14), (20, 7), (24, 14), (28, 10), (28, 19)], '#fff'), GOLD, hi=GOLD_HI, sh=GOLD_SH)
    ic.raw(lambda c: (c.rect(13, 17, 27, 17, '#b87a08'), c.px(20, 14, '#e8261c'), c.px(15, 16, '#3ad8ff'), c.px(25, 16, '#3ad8ff')))
    return ic


def ui_join():
    ic = Icon(40)
    # door frame + open door
    ic.part(lambda c: c.rect(14, 3, 35, 37, '#fff'), '#5a3414', hi='#8a5a2a', sh='#2a1408')
    ic.raw(lambda c: c.rect(17, 6, 32, 37, '#1b1420'))
    ic.raw(lambda c: c.rect(18, 7, 31, 37, '#fff6c0'))
    ic.part(lambda c: c.poly([(32, 6), (39, 3), (39, 38), (32, 37)], '#fff'), '#b8742a', hi='#e0a060', sh='#6a3a14')
    ic.raw(lambda c: (c.px(34, 22, '#ffd23a'), c.px(34, 23, '#ffd23a')))
    # arrow going in
    ic.part(lambda c: c.poly([(1, 17), (12, 17), (12, 12), (21, 20.5), (12, 29), (12, 24), (1, 24)], '#fff'), '#3ac04a', hi='#a8f08a', sh='#1a7a2a')
    return ic


def ui_invite():
    ic = Icon(40)
    ic.part(lambda c: c.rect(3, 10, 36, 33, '#fff'), '#f4ecd8', hi='#ffffff', sh='#b8ac90')
    ic.raw(lambda c: (c.line(3, 10, 19, 23, '#b8ac90'), c.line(36, 10, 20, 23, '#b8ac90'),
                      c.line(3, 33, 15, 22, '#d8ccb0'), c.line(36, 33, 24, 22, '#d8ccb0')))
    # heart seal
    ic.part(lambda c: (c.circle(17.5, 22, 3.2, '#fff'), c.circle(22.5, 22, 3.2, '#fff'), c.poly([(14.5, 23), (25.5, 23), (20, 29)], '#fff')),
            '#ff3a6a', hi='#ffb0c0', sh='#a8102e')
    # plus badge
    ic.part(lambda c: c.circle(33, 9, 6.0, '#fff'), '#3ac04a', hi='#a8f08a', sh='#1a7a2a')
    ic.raw(lambda c: (c.rect(30, 8, 35, 9, '#ffffff'), c.rect(32, 6, 33, 11, '#ffffff')))
    return ic


def ui_player_cursor(col, col_sh, digit):
    """16x16 native (x3 -> 48px). Arrow tip pixel at native (2,2); small number badge bottom-right."""
    ic = Icon(16)
    pts = [(2, 2), (2, 11.5), (4.6, 9.2), (6.4, 12.8), (7.8, 12.2), (6.1, 8.6), (9.2, 8.6)]
    ic.part(lambda c: c.poly(pts, '#fff'), col, hi=lighten(col, 0.55), sh=col_sh, outline='#ffffff')
    ic.a = outline_arr(ic.a, OUTLINE)
    m = fonts.text_mask(digit, {'1': ".#.\n##.\n.#.\n.#.\n###", '2': "##.\n..#\n.#.\n#..\n###"})
    # number badge: solid player colour, white digit, black outline - fully inside the canvas
    ic.part(lambda c: c.rect(10, 8, 14, 14, '#fff'), col_sh, shade=False, outline=OUTLINE)
    h, w = m.shape
    ic.raw(lambda c: [c.px(11 + x, 9 + y, '#ffffff') for y in range(h) for x in range(w) if m[y, x]])
    return ic


# ------------------------------------------------------------------ coordinator extras (32x32 -> 128)
def ux_lucky_cash():
    ic = Icon(32)
    sack(ic, 15, 18, 9.0, col='#3aa84a', sh='#1a6a2a', mark=None)
    ic.raw(lambda c: c.rect(11, 9, 19, 10, '#ffd23a'))
    m = np.array([[0, 1, 0], [1, 1, 1], [1, 0, 0], [1, 1, 1], [0, 0, 1], [1, 1, 1], [0, 1, 0]])
    ic.raw(lambda c: [c.rect(13 + x * 2, 15 + y * 2 - 2, 14 + x * 2, 16 + y * 2 - 2, '#e8ffe0') for y in range(7) for x in range(3) if m[y, x]])
    coin(ic, 25.5, 26.5, 4.2, 1.0, mark=True)
    coin(ic, 5.5, 27.5, 3.6, 0.8, mark=False)
    coin(ic, 27.5, 18.5, 3.0, 1.0, mark=False)
    sparkle(ic, 4, 5, 1)
    return ic


def ux_lucky_free():
    ic = Icon(32)
    ic.add(iso_cube(15, 7, top='#8ae89a', left='#3ab84a', right='#1e8a2e', pip='#ffffff', pips=(1, 3, 2), edge='#e8ffe8'), 8, 3)
    ic.add(iso_cube(15, 7, top='#8ab8ff', left='#3a7ae8', right='#2452b8', pip='#ffffff', pips=(1, 2, 3), edge='#e0ecff'), 0, 13)
    ic.add(iso_cube(15, 7, top='#ff9a8a', left='#e8361c', right='#a81a10', pip='#ffffff', pips=(5, 4, 6), edge='#ffe8e0'), 15, 13)
    # red ribbon: vertical band over the top die, horizontal band round the base
    red, rhi, rsh = '#e8261c', '#ff8a80', '#8a120c'
    ic.raw(lambda c: (c.rect(15, 5, 16, 31, red), c.px(15, 6, rhi), c.rect(15, 7, 15, 30, '#ff5a4a'),
                      c.rect(1, 25, 30, 26, red), c.rect(1, 25, 30, 25, '#ff5a4a')))
    # bow
    ic.part(lambda c: (c.ellipse(11.0, 3.2, 4.2, 2.8, '#fff'), c.ellipse(21.0, 3.2, 4.2, 2.8, '#fff')), red, hi=rhi, sh=rsh)
    ic.raw(lambda c: (c.ellipse(11.0, 3.2, 1.8, 1.0, rsh), c.ellipse(21.0, 3.2, 1.8, 1.0, rsh)))
    ic.part(lambda c: (c.line(14, 5, 11, 9, '#fff', w=2), c.line(17, 5, 20, 9, '#fff', w=2)), red, hi=rhi, sh=rsh)
    ic.part(lambda c: c.rect(14, 1, 17, 5, '#fff'), '#ff3a2a', hi='#ffb0a8', sh=rsh)
    sparkle(ic, 29, 4, 1)
    sparkle(ic, 2, 6, 1)
    return ic


def ux_lucky_boost():
    ic = Icon(32)
    clover(ic, 14, 13, 4.2, glow=True)
    # x2 badge
    ic.part(lambda c: c.rect(18, 20, 31, 30, '#fff'), '#ffc828', hi=GOLD_HI, sh=GOLD_SH)
    xm = fonts.text_mask('x2', {'x': """
.....
#...#
.#.#.
..#..
.#.#.
#...#""", '2': """
.###.
#...#
....#
..##.
.#...
#####"""}, spacing=1)
    h, w = xm.shape
    ox, oy = 19 + (12 - w) // 2, 22
    ic.raw(lambda c: [c.px(ox + x, oy + y, '#7a2a08') for y in range(h) for x in range(w) if xm[y, x]])
    sparkle(ic, 27, 4, 1)
    return ic


def ux_lucky_unlock():
    return ui_unlock(32)


def ux_sell():
    ic = Icon(32)
    # coin pile at the bottom
    for (x, y, r) in ((8, 27, 4.0), (16, 28, 4.4), (24, 27, 4.0), (12, 24, 3.8), (20, 24, 3.8), (16, 21, 3.6)):
        coin(ic, x, y, r, 0.6, mark=False)
    # falling die
    ic.add(iso_cube(13, 6, top='#ffffff', left='#d8dce8', right='#a0a6ba', pip='#1b1b24', pips=(1, 2, 3)), 9, 6)
    ic.raw(lambda c: (c.line(8, 9, 8, 12, '#c8ccd8'), c.line(24, 8, 24, 11, '#c8ccd8')))
    # hand at the top (open, palm down, fingers letting go)
    skin, sk_sh = '#f6c896', '#c8905a'
    ic.part(lambda c: (c.rect(17, 0, 30, 4, '#fff'), c.ellipse(23.5, 4.5, 6.5, 2.6, '#fff')), skin, sh=sk_sh)
    ic.part(lambda c: (c.rect(16, 4, 17, 8, '#fff'), c.rect(19, 5, 20, 9, '#fff'), c.rect(22, 5, 23, 9, '#fff'), c.rect(25, 5, 26, 8, '#fff')),
            skin, sh=sk_sh)
    ic.part(lambda c: c.rect(26, -1, 31, 1, '#fff'), '#3a5ab8')
    return ic


def ux_event():
    ic = Icon(32)
    # calendar page
    ic.part(lambda c: c.rect(3, 6, 28, 29, '#fff'), '#f8f4ec', hi='#ffffff', sh='#c8c0b0')
    ic.part(lambda c: c.rect(3, 6, 28, 11, '#fff'), '#e8261c', hi='#ff7a6a', sh='#8a120c')
    for x in (8, 15, 22):
        ic.part(lambda c, x=x: c.rect(x, 3, x + 1, 8, '#fff'), '#c8ccd8', hi='#ffffff', sh='#6a7282')
    ic.raw(lambda c: [c.px(6 + (k % 6) * 4, 15 + (k // 6) * 4, '#c8c0b0') for k in range(18)])
    bolt(ic, 10, 12, 1.15)
    # star badge
    ic.part(lambda c: c.poly(star_pts(25.5, 25.5, 6.5, 3.0), '#fff'), GOLD, hi=GOLD_HI, sh=GOLD_SH)
    return ic


EVENTS = [('meteor_shower', ev_meteor_shower), ('coin_rain', ev_coin_rain), ('tornado', ev_tornado), ('happy_hour', ev_happy_hour),
          ('rainbow', ev_rainbow), ('black_cat', ev_black_cat), ('treasure_chest', ev_treasure_chest), ('thief', ev_thief),
          ('lucky_clover', ev_lucky_clover)]
SPRITES = [('coin', spr_coin, 4), ('meteor', spr_meteor, 4), ('tornado_sprite', spr_tornado, 4), ('cat_walk', spr_cat_walk, 4),
           ('thief_run', spr_thief_run, 4), ('chest_closed', lambda: spr_chest(False), 4), ('chest_open', lambda: spr_chest(True), 4),
           ('clover', spr_clover, 4)]
UIS = [('shop_icon', ui_shop), ('unlock_icon', ui_unlock), ('design_icon', ui_design), ('coop_icon', ui_coop),
       ('host_icon', ui_host), ('join_icon', ui_join), ('invite_icon', ui_invite)]
EXTRAS = [('lucky_cash', ux_lucky_cash), ('lucky_free', ux_lucky_free), ('lucky_boost', ux_lucky_boost),
          ('lucky_unlock', ux_lucky_unlock), ('sell_icon', ux_sell), ('event_icon', ux_event)]


def main():
    items = []
    for name, fn in EVENTS:
        im = to_png(fn().a, 4, os.path.join(EV, name + '.png'))
        items.append(('events/' + name, im))
    for name, fn, sc in SPRITES:
        im = to_png(fn().a, sc, os.path.join(EV, name + '.png'))
        items.append(('events/' + name, im))
    for name, fn in UIS:
        im = to_png(fn().a, 4, os.path.join(UI, name + '.png'))
        items.append(('ui/' + name, im))
    for name, col, sh, dg in (('p1_cursor', '#3a8aff', '#1f3a9a', '1'), ('p2_cursor', '#ff8a1f', '#a8500a', '2')):
        im = to_png(ui_player_cursor(col, sh, dg).a, 3, os.path.join(UI, name + '.png'))
        items.append(('ui/' + name, im))
    for name, fn in EXTRAS:
        im = to_png(fn().a, 4, os.path.join(UI, name + '.png'))
        items.append(('ui/' + name, im))
    sheet = contact_sheet(items, (160, 160), 7, label_h=14, bg=(30, 40, 52, 255))
    sheet.save(os.path.join(REPO, "tools", "art", "_preview", "events_ui_review.png"))
    ev_items = [it for it in items if it[0].startswith('events/')]
    ui_items = [it for it in items if it[0].startswith('ui/')]
    contact_sheet(ev_items, (160, 160), 6, label_h=14, bg=(30, 40, 52, 255)).save(os.path.join(EV, 'contact_sheet.png'))
    contact_sheet(ui_items, (160, 160), 6, label_h=14, bg=(30, 40, 52, 255)).save(os.path.join(UI, 'contact_sheet.png'))
    small = [(n.split('/')[-1], im.resize((max(1, im.width * 90 // 160), max(1, im.height * 90 // 160)), Image.LANCZOS)) for n, im in items]
    contact_sheet(small, (90, 90), 12, label_h=14, bg=(30, 40, 52, 255)).save(os.path.join(REPO, "tools", "art", "_preview", "events_ui_90.png"))
    print('ok', len(items))


if __name__ == '__main__':
    main()
