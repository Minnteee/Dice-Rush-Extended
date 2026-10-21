"""Generate 10 pixel-art mouse cursors (128x128 RGBA, native 64x64 x2) + cursors.json.

Style follows the original cursor_hand.png: chunky shapes, light from the top-left,
1px black outline plus a coloured outer rim for visibility on any background.
The content fills the canvas like the original (which the game scales to ~68px);
"hotspot" is the exact pointing tip in 128px space.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import Canvas, hexc, mix, darken, lighten, lum, outline_arr, sprite, to_img, contact_sheet, OUT_ROOT
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

OUT = os.path.join(OUT_ROOT, 'cursors')
N = 64
SC = 2


# ------------------------------------------------------------------ shape helpers
def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L2))
    qx, qy = x0 + t * dx, y0 + t * dy
    return math.hypot(px - qx, py - qy)


def capsule(lab, pid, x0, y0, x1, y1, r):
    for y in range(N):
        for x in range(N):
            if seg_dist(x + 0.5, y + 0.5, x0, y0, x1, y1) <= r:
                lab[y, x] = pid


def rrect(lab, pid, x0, y0, x1, y1, rad):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cx = min(max(x + 0.5, x0 + rad), x1 + 1 - rad)
            cy = min(max(y + 0.5, y0 + rad), y1 + 1 - rad)
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= rad + 0.01:
                lab[y, x] = pid


def poly(lab, pid, pts):
    cv = Canvas(N)
    cv.poly(pts, '#ffffff')
    lab[cv.a[:, :, 3] > 0] = pid


def shade_parts(lab, base_cols, hi_cols, sh_cols, sep_col, sep_pairs=None, hi2=None):
    """Fill parts with base colour, add top-left highlight band and bottom-right shadow band.
    Draw separation lines where a part touches a part with a lower id drawn 'behind'."""
    a = np.zeros((N, N, 4), np.uint8)
    for y in range(N):
        for x in range(N):
            p = lab[y, x]
            if p == 0:
                continue
            c = base_cols[p]

            def other(dx, dy):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N:
                    return lab[yy, xx] != p
                return True
            if other(-1, 0) or other(0, -1):
                c = hi_cols[p]
            elif (other(-2, 0) or other(0, -2)) and hi2 is not None:
                c = mix(base_cols[p], hi_cols[p], 0.5)
            if other(1, 0) or other(0, 1):
                c = sh_cols[p]
            elif other(2, 0) or other(0, 2):
                c = mix(base_cols[p], sh_cols[p], 0.5)
            a[y, x] = hexc(c)
    # separation lines between different parts (drawn on the higher id part)
    for y in range(N):
        for x in range(N):
            p = lab[y, x]
            if p == 0:
                continue
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N:
                    q = lab[yy, xx]
                    if q != 0 and q != p and (sep_pairs is None or (p, q) in sep_pairs) and p > q:
                        a[y, x] = hexc(sep_col)
    return a


def finish(a, outer, inner='#0c0a10'):
    a = outline_arr(a, inner, diag=False)
    a = outline_arr(a, outer, diag=False)
    return a


# ------------------------------------------------------------------ the pointing-hand pose
IDX, MID, RNG, PNK, THB, PALM, CUFF = 1, 2, 3, 4, 5, 6, 7


def hand_labels(cuff=True):
    lab = np.zeros((N, N), np.int32)
    if cuff:
        rrect(lab, CUFF, 18, 49, 49, 60, 2)
    rrect(lab, PALM, 17, 29, 51, 52, 7)
    capsule(lab, THB, 18.5, 45, 8.5, 31.5, 4.6)
    capsule(lab, PNK, 47.0, 25.0, 47.0, 37, 3.4)
    capsule(lab, RNG, 40.5, 18.5, 40.5, 36, 3.9)
    capsule(lab, MID, 32.5, 14.5, 32.5, 35, 4.2)
    capsule(lab, IDX, 23.0, 6.5, 23.0, 34, 4.6)
    return lab


HAND_TIP = (23, 2)  # native pixel at the top of the index finger


def tip_of(lab, pid=IDX):
    ys, xs = np.nonzero(lab == pid)
    y = ys.min()
    xs_top = xs[ys == y]
    return int(round(xs_top.mean() - 0.5)), int(y)


# ------------------------------------------------------------------ designs
def cur_golden_gauntlet():
    lab = hand_labels()
    gold, ghi, gsh = '#f2b62a', '#fff0a0', '#a8660c'
    base = {i: gold for i in range(1, 8)}
    base[CUFF] = '#d89a1c'
    hi = {i: ghi for i in range(1, 8)}
    sh = {i: gsh for i in range(1, 8)}
    a = shade_parts(lab, base, hi, sh, '#6a3a08', hi2=True)
    cv = Canvas(N, arr=a)
    # knuckle plates on fingers
    for (pid, ys) in ((IDX, (14, 22, 29)), (MID, (21, 28)), (RNG, (24, 30)), (PNK, (30,))):
        xs = np.nonzero(lab == pid)[1]
        for y in ys:
            for x in range(xs.min() + 1, xs.max()):
                if lab[y, x] == pid:
                    cv.px(x, y, '#8a5208')
                    if lab[y + 1, x] == pid:
                        cv.px(x, y + 1, '#ffe08a')
    # ruby gem on the back of the hand
    cv.ellipse(34, 41, 4.5, 4.0, '#6a0a14')
    cv.ellipse(34, 41, 3.5, 3.0, '#e01c3a')
    cv.px(32, 39, '#ffb0c0'); cv.px(33, 39, '#ff6a80'); cv.px(32, 40, '#ff6a80')
    # cuff rivets
    for x in (22, 28, 34, 40, 45):
        cv.px(x, 55, '#fff0a0'); cv.px(x + 1, 56, '#8a5208')
    cv.hline(19, 48, 50, '#8a5208')
    return finish(cv.a, '#ff8a1f'), tip_of(lab)


def cur_crystal_hand():
    lab = hand_labels()
    base = {i: '#8ee8ff' for i in range(1, 8)}
    base[CUFF] = '#5ab8e8'
    hi = {i: '#f0ffff' for i in range(1, 8)}
    sh = {i: '#3a7ac8' for i in range(1, 8)}
    a = shade_parts(lab, base, hi, sh, '#2a5aa8', hi2=True)
    cv = Canvas(N, arr=a)
    # facets: diagonal light/dark streaks clipped to the shape
    for y in range(N):
        for x in range(N):
            if lab[y, x] == 0:
                continue
            c = cv.get(x, y)
            if (x + y) % 11 == 0:
                cv.px(x, y, mix(c, '#ffffff', 0.55))
            elif (x - y) % 13 == 0:
                cv.px(x, y, mix(c, '#2a5aa8', 0.35))
    # big diamond on the palm
    cv.poly([(34, 34), (40, 40), (34, 47), (28, 40)], '#c8f8ff')
    cv.poly([(34, 34), (40, 40), (34, 40)], '#ffffff')
    cv.poly([(28, 40), (34, 40), (34, 47)], '#6ac8f0')
    # sparkles
    for (x, y) in ((20, 10), (44, 22), (25, 44)):
        cv.px(x, y, '#ffffff')
    return finish(cv.a, '#ffffff', '#16285a'), tip_of(lab)


def cur_skeleton_hand():
    lab = hand_labels(cuff=False)
    # make bones: only keep a central bone core per finger + palm metacarpals
    a = np.zeros((N, N, 4), np.uint8)
    cv = Canvas(N, arr=a)
    bone, bhi, bsh = '#f2ecd8', '#ffffff', '#b8ae94'

    def bone_seg(x0, y0, x1, y1, r):
        tmp = np.zeros((N, N), np.int32)
        capsule(tmp, 1, x0, y0, x1, y1, r)
        for y in range(N):
            for x in range(N):
                if tmp[y, x]:
                    edge_l = x == 0 or not tmp[y, x - 1]
                    edge_r = x == N - 1 or not tmp[y, x + 1]
                    cv.px(x, y, bhi if edge_l else (bsh if edge_r else bone))
        return tmp

    joints = []
    # fingers: three phalanges each, small gaps (joints) between
    fingers = [(23.0, 3.0, 34, 3.0), (32.5, 12.0, 35, 2.8), (40.5, 16.0, 36, 2.6), (47.0, 22.5, 37, 2.3)]
    for (fx, top, bot, r) in fingers:
        L = bot - top
        cuts = [top + L * 0.33, top + L * 0.62]
        bone_seg(fx, top + r, fx, cuts[0] - 0.8, r)
        bone_seg(fx, cuts[0] + 0.8, fx, cuts[1] - 0.8, r)
        bone_seg(fx, cuts[1] + 0.8, fx, bot, r)
        joints += [(fx, cuts[0]), (fx, cuts[1])]
    # metacarpals fanning down to the wrist
    for (fx, top) in ((23.0, 36), (32.5, 37), (40.5, 38), (47.0, 39)):
        bone_seg(fx, top, 30 + (fx - 33) * 0.35, 49, 2.0)
    # thumb
    bone_seg(9.0, 31.5, 13.0, 37.0, 2.8)
    bone_seg(14.0, 38.5, 19.0, 45.0, 2.8)
    # carpals / wrist
    for (x, y) in ((24, 51), (29, 52), (34, 52), (39, 51), (27, 55), (32, 56), (37, 55)):
        bone_seg(x, y, x + 1.5, y, 2.0)
    # forearm bones
    bone_seg(27, 58, 27, 63, 2.3)
    bone_seg(36, 58, 36, 63, 2.3)
    for (jx, jy) in joints:
        cv.px(int(jx) - 1, int(jy), '#8a826c')
        cv.px(int(jx), int(jy), '#8a826c')
    a = finish(cv.a, '#9b5aff', '#0c0a10')
    lab2 = (cv.a[:, :, 3] > 0).astype(np.int32)
    ys, xs = np.nonzero(lab2)
    y = ys.min()
    return a, (int(round(xs[ys == y].mean() - 0.5)), int(y))


def cur_rainbow_glove():
    lab = hand_labels()
    white = '#fbfbff'
    base = {i: white for i in range(1, 8)}
    hi = {i: '#ffffff' for i in range(1, 8)}
    sh = {i: '#b8bcd8' for i in range(1, 8)}
    a = shade_parts(lab, base, hi, sh, '#8a8eb0', hi2=None)
    cv = Canvas(N, arr=a)
    bands = ['#ff3a3a', '#ff9a1f', '#ffe23a', '#4fd040', '#3a8aff', '#a04aff']
    # rainbow stripes across the cuff and the back of the hand
    for y in range(N):
        for x in range(N):
            p = lab[y, x]
            if p == CUFF:
                i = (y - 50) // 2
                if 0 <= i < 6:
                    c = bands[i]
                    if lab[y, x - 1] != CUFF or (y > 0 and lab[y - 1, x] != CUFF):
                        c = mix(c, '#ffffff', 0.35)
                    if x + 1 < N and lab[y, x + 1] != CUFF:
                        c = darken(c, 0.25)
                    cv.px(x, y, c)
    # three classic glove seams on the back of the hand
    for sx in (27, 32, 37):
        for y in range(38, 47):
            cv.px(sx + (y - 38) // 4, y, '#9a9ec0')
    # little rainbow heart
    heart = sprite("""
.RR.RR.
RRRRRRR
RRRRRRR
.RRRRR.
..RRR..
...R...""", {'R': '#ff4a8a'})
    cv.blit(heart, 38, 40)
    return finish(cv.a, '#ff4ad8', '#1a1030'), tip_of(lab)


def polyline_capsule(lab, pid, pts, r0, r1):
    n = len(pts) - 1
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        for t in np.linspace(0, 1, 12):
            k = (i + t) / n
            r = r0 + (r1 - r0) * k
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            capsule(lab, pid, x, y, x, y, r)


def cur_robot_claw():
    cv = Canvas(N)
    lab = np.zeros((N, N), np.int32)
    # arm segment from bottom-right
    capsule(lab, 1, 60, 63, 42, 44, 6.5)
    # wrist hub
    rrect(lab, 2, 27, 25, 45, 43, 6)
    # upper pincer: thick, curving to a sharp tip at the top-left
    polyline_capsule(lab, 3, [(31, 28), (22, 17), (14, 9), (8, 5), (4, 3)], 4.6, 1.0)
    # lower pincer curving up toward the upper tip
    polyline_capsule(lab, 4, [(29, 38), (19, 34), (11, 28), (7, 21), (7, 15)], 4.2, 1.0)
    base = {1: '#8a94a8', 2: '#a8b2c4', 3: '#c8d0dc', 4: '#b0b8c8'}
    hi = {1: '#d8e0ec', 2: '#eef2f8', 3: '#ffffff', 4: '#eef2f8'}
    sh = {1: '#4a5262', 2: '#5a6272', 3: '#6a7282', 4: '#5a6272'}
    a = shade_parts(lab, base, hi, sh, '#2a2e38')
    cv = Canvas(N, arr=a)
    # hydraulic stripes on the arm
    for t in range(3):
        cx, cy = 52 - t * 4, 56 - t * 4
        cv.line(cx - 4, cy + 4, cx + 4, cy - 4, '#3a404c')
    # glowing red eye on the hub + rivets
    cv.ellipse(37.5, 34.5, 3.6, 3.6, '#3a0a0a')
    cv.ellipse(37.5, 34.5, 2.6, 2.6, '#ff3a2a')
    cv.px(36, 33, '#ffd0c0')
    for (x, y) in ((31, 29), (42, 28), (31, 40), (42, 40)):
        cv.px(x, y, '#2a2e38')
        cv.px(x - 1, y - 1, '#ffffff')
    # pincer joint bolts and teeth
    for (x, y) in ((24, 19), (20, 33)):
        cv.circle(x + 0.5, y + 0.5, 1.8, '#5a6272')
        cv.px(x, y, '#ffffff')
    for (x, y) in ((16, 13), (13, 10), (12, 25), (10, 22)):
        cv.px(x, y, '#2a2e38')
    a = finish(cv.a, '#ff3a2a', '#0c0a10')
    ys, xs = np.nonzero(lab == 3)
    i = np.argmin(xs + ys)
    return a, (int(xs[i]), int(ys[i]))


def cur_pirate_hook():
    cv = Canvas(N)
    lab = np.zeros((N, N), np.int32)
    # sleeve (red/white stripes) + wooden cuff
    rrect(lab, 1, 30, 46, 60, 63, 4)
    rrect(lab, 2, 26, 38, 44, 50, 3)
    # hook: a "C" opening to the right; the shaft leaves the cuff, the curve
    # wraps round the left and ends in a sharp point at the top
    hook = np.zeros((N, N), np.int32)
    capsule(hook, 1, 34, 40, 27, 30, 3.0)
    cx, cy, R = 21.0, 18.0, 12.0
    ts = np.linspace(math.radians(-55), math.radians(-300), 160)
    for j, t in enumerate(ts):
        x = cx + R * math.cos(t)
        y = cy - R * math.sin(t)
        k = j / (len(ts) - 1)
        capsule(hook, 1, x, y, x, y, 3.0 - 2.4 * k ** 2)
    lab[(hook > 0) & (lab == 0)] = 3
    base = {1: '#c81e2a', 2: '#8a5a2a', 3: '#c8d0dc'}
    hi = {1: '#ff6a6a', 2: '#c89a5a', 3: '#ffffff'}
    sh = {1: '#7a0c14', 2: '#4a2a10', 3: '#5a6272'}
    a = shade_parts(lab, base, hi, sh, '#2a1a10')
    cv = Canvas(N, arr=a)
    # sleeve stripes
    for y in range(46, 64):
        for x in range(30, 61):
            if lab[y, x] == 1 and ((x + y) // 4) % 2 == 0:
                cv.px(x, y, mix(cv.get(x, y), '#ffffff', 0.8))
    # cuff bands / nails
    for x in (28, 33, 38, 42):
        cv.px(x, 41, '#ffd23a')
        cv.px(x, 47, '#ffd23a')
    a = finish(cv.a, '#ffd23a', '#0c0a10')
    # hook point = end of the curve
    t = math.radians(-300)
    hx = int(math.floor(cx + R * math.cos(t)))
    hy = int(math.floor(cy - R * math.sin(t)))
    return a, (hx, hy)


def cur_wizard_wand():
    cv = Canvas(N)
    # wand shaft: dark wood with silver ferrule, from bottom-right to the star
    lab = np.zeros((N, N), np.int32)
    capsule(lab, 1, 56, 58, 22, 24, 3.0)
    capsule(lab, 2, 60, 62, 52, 54, 3.6)
    base = {1: '#3a2418', 2: '#c8d0dc'}
    hi = {1: '#8a5a3a', 2: '#ffffff'}
    sh = {1: '#1a0e08', 2: '#5a6272'}
    a = shade_parts(lab, base, hi, sh, '#0c0a10')
    cv = Canvas(N, arr=a)
    # gold bands
    for t in (0.25, 0.5):
        x = int(22 + (56 - 22) * t)
        y = int(24 + (58 - 24) * t)
        cv.line(x - 3, y + 3, x + 3, y - 3, '#ffd23a')
    # 5-point star at the tip, one ray pointing to the top-left
    cx, cy = 15.5, 15.5
    pts = []
    rot = math.radians(225)  # first ray toward up-left
    for k in range(10):
        r = 13.5 if k % 2 == 0 else 5.6
        ang = rot + k * math.pi / 5
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    star = Canvas(N)
    star.poly(pts, '#ffd23a')
    sm = star.a[:, :, 3] > 0
    for y in range(N):
        for x in range(N):
            if sm[y, x]:
                c = '#ffd23a'
                if (x + y) < 27:
                    c = '#fff4a0'
                if (x - cx) + (y - cy) > 6:
                    c = '#e8961c'
                cv.px(x, y, c)
    cv.px(14, 14, '#ffffff'); cv.px(15, 14, '#ffffff'); cv.px(14, 15, '#ffffff')
    # sparkle dust
    for (x, y) in ((30, 10), (8, 30), (34, 18), (26, 33)):
        cv.px(x, y, '#ffffff')
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.px(x + dx, y + dy, '#b49aff')
    a = finish(cv.a, '#b45aff', '#0c0a10')
    ys, xs = np.nonzero(sm)
    i = np.argmin(xs + ys)
    return a, (int(xs[i]), int(ys[i]))


def cur_cat_paw():
    cv = Canvas(N)
    lab = np.zeros((N, N), np.int32)
    # leg from bottom-right, paw tilted toward the top-left
    capsule(lab, 1, 52, 62, 34, 40, 9.0)
    capsule(lab, 2, 30, 32, 30, 32, 12.0)   # paw pad mass
    base = {1: '#4a4a58', 2: '#4a4a58'}
    hi = {1: '#7a7a8c', 2: '#7a7a8c'}
    sh = {1: '#26262e', 2: '#26262e'}
    lab[lab == 1] = 2
    a = shade_parts(lab, base, hi, sh, '#14141a')
    cv = Canvas(N, arr=a)
    # toes (fur bumps) along the top-left rim + pink toe beans
    toes = [(15.5, 27.5), (19.5, 18.5), (27.5, 14.5)]
    for (tx, ty) in toes:
        cv.circle(tx, ty, 5.6, '#14141a')
        cv.circle(tx, ty, 4.6, '#5a5a6a')
        cv.px(int(tx) - 2, int(ty) - 2, '#8a8a9c')
    for (tx, ty) in toes:
        cv.ellipse(tx + 0.6, ty + 0.6, 2.4, 2.2, '#ff8fb8')
        cv.px(int(tx), int(ty), '#ffc8dc')
    # main bean
    cv.ellipse(32, 32, 6.5, 5.5, '#ff8fb8')
    cv.ellipse(31, 31, 3.0, 2.0, '#ffc8dc')
    # extended claw from the top toe, pointing to the top-left
    claw = [(17, 13), (16, 12), (15, 11), (14, 10), (13, 9), (12, 8), (11, 7)]
    for i, (x, y) in enumerate(claw):
        cv.px(x, y, '#ffffff')
        cv.px(x + 1, y, '#c8ccd8')
    a = finish(cv.a, '#ff8fb8', '#0c0a10')
    return a, (11, 7)


def cur_sword():
    cv = Canvas(N)
    lab = np.zeros((N, N), np.int32)
    # blade from the hilt (bottom-right) to the tip (top-left)
    poly(lab, 1, [(3, 3), (9, 5), (44, 40), (40, 44), (5, 9)])
    # crossguard
    capsule(lab, 2, 36, 50, 50, 36, 2.6)
    # grip
    capsule(lab, 3, 46, 46, 56, 56, 2.4)
    # pommel
    capsule(lab, 4, 58, 58, 58, 58, 3.4)
    base = {1: '#c8d0dc', 2: '#e8a81c', 3: '#5a3418', 4: '#e8a81c'}
    hi = {1: '#ffffff', 2: '#fff0a0', 3: '#8a5a2a', 4: '#fff0a0'}
    sh = {1: '#6a7282', 2: '#8a5208', 3: '#2a1408', 4: '#8a5208'}
    a = shade_parts(lab, base, hi, sh, '#2a2e38')
    cv = Canvas(N, arr=a)
    # fuller (central groove) along the blade
    for t in np.linspace(0.18, 0.92, 60):
        x = 4 + (42 - 4) * t
        y = 4 + (42 - 4) * t
        cv.px(int(x) + 1, int(y), '#8a94a8')
    # grip wrap
    for t in range(3):
        cv.px(48 + t * 3, 49 + t * 3, '#c89a5a')
    cv.ellipse(58, 58, 1.6, 1.6, '#e01c3a')
    a = finish(cv.a, '#5ae8ff', '#0c0a10')
    return a, (3, 3)


def cur_neon_arrow():
    cv = Canvas(N)
    # classic arrow pointer
    pts = [(2, 2), (2, 46), (13, 36), (21, 56), (29, 52), (21, 33), (36, 33)]
    cv.poly(pts, '#0a0a1a')
    inner = Canvas(N)
    inner.poly([(5, 9), (5, 38), (14, 30), (22, 49), (25, 47), (17, 29), (28, 29)], '#ff2aaa')
    m = inner.a[:, :, 3] > 0
    for y in range(N):
        for x in range(N):
            if m[y, x]:
                cv.px(x, y, '#ff2aaa')
    inner2 = Canvas(N)
    inner2.poly([(7, 15), (7, 31), (13, 26), (19, 40), (20, 39), (15, 26), (21, 26)], '#ffffff')
    m2 = inner2.a[:, :, 3] > 0
    for y in range(N):
        for x in range(N):
            if m2[y, x]:
                cv.px(x, y, '#ffb8e8')
    # cyan neon tube along the edge
    a = cv.a
    sil = a[:, :, 3] > 0
    edge = np.zeros_like(sil)
    for y in range(N):
        for x in range(N):
            if sil[y, x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < N and 0 <= yy < N) or not sil[yy, xx]:
                        edge[y, x] = True
    a[edge] = hexc('#5affff')
    a = outline_arr(a, '#0a0a1a')
    a = outline_arr(a, '#1e9ac0')
    return a, (2, 2)


DESIGNS = [
    ('golden gauntlet', cur_golden_gauntlet),
    ('crystal hand', cur_crystal_hand),
    ('robot claw', cur_robot_claw),
    ('pirate hook', cur_pirate_hook),
    ('wizard wand', cur_wizard_wand),
    ('cat paw', cur_cat_paw),
    ('sword', cur_sword),
    ('neon arrow', cur_neon_arrow),
    ('skeleton hand', cur_skeleton_hand),
    ('rainbow glove', cur_rainbow_glove),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    items = []
    for k, (name, fn) in enumerate(DESIGNS, start=1):
        a, (hx, hy) = fn()
        a = a.copy()
        a[a[:, :, 3] == 0] = 0
        # shift content so that nothing is clipped (keep the tip near top-left)
        img = to_img(a, SC)
        assert img.size == (128, 128)
        path = os.path.join(OUT, 'cursor_%d.png' % k)
        img.save(path)
        hot = [int(hx * SC + SC // 2), int(hy * SC)]
        meta['cursor_%d' % k] = {'hotspot': hot, 'name': name}
        prev = Image.new('RGBA', (128, 128), (70, 90, 80, 255))
        prev.alpha_composite(img)
        # mark hotspot
        px = prev.load()
        for d in range(-3, 4):
            if 0 <= hot[0] + d < 128:
                px[hot[0] + d, hot[1]] = (255, 0, 255, 255)
            if 0 <= hot[1] + d < 128:
                px[hot[0], hot[1] + d] = (255, 0, 255, 255)
        items.append(('cursor_%d %s' % (k, name), prev))
    with open(os.path.join(OUT, 'cursors.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, indent=1)
    sheet = contact_sheet(items, (128, 128), 5, label_h=14)
    sheet.save(os.path.join(OUT, 'contact_sheet.png'))
    small = [(n, im.resize((64, 64), Image.LANCZOS)) for n, im in items]
    contact_sheet(small, (64, 64), 10, label_h=14).save(os.path.join(REPO, "tools", "art", "_preview", "cursors_small.png"))
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
