"""Generate the 100 Dice Rush Extended dice (+ landmarks.json + contact sheet).

Native grid 64x64, upscaled x4 (NEAREST) -> 256x256 RGBA.

Cube geometry (native pixel columns/rows):
  columns 4..60, centre column 32 (vertical seam)
  top face   : rows yt(x)..yf(x)
  side faces : rows yf(x)+1..yb(x)  (first row = dark seam)
  with dx=|x-32|, k=round(0.6*dx) :  yt=2+k, yf=36-k, yb=62-k
  (slope 3:5 like the original game dice: top rhombus ~57% of the height)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import (Canvas, hexc, mix, darken, lighten, lum, cdist, hash2, value_noise,
                 outline_arr, pad, sprite, save_png, to_img, contact_sheet, OUT_ROOT)
import fonts
import dice_icons
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

CATALOG = os.path.join(REPO, "src", "bdr", "data", "dice_catalog.json")
OUT = os.path.join(OUT_ROOT, 'dice')
N = 64
SCALE = 4
CX = 32

SLOPE = 0.6
KMAX = 17
# continuous landmark geometry in native units (pixel edges)
LM = {
    'T': (32.5, 2.0),
    'R': (61.0, 19.5),
    'F': (32.5, 37.0),
    'L': (4.0, 19.5),
    'BL': (4.0, 46.0),
    'B': (32.5, 63.0),
    'BR': (61.0, 46.0),
}
LM_ORDER = ['T', 'R', 'F', 'L', 'BL', 'B', 'BR']


def k_of(x):
    return int(math.floor(abs(x - CX) * SLOPE + 0.5))


def yt(x):
    return 2 + k_of(x)


def yf(x):
    return 2 + 2 * KMAX - k_of(x)


def yb(x):
    return 62 - k_of(x)


def build_masks():
    top = np.zeros((N, N), bool)
    left = np.zeros((N, N), bool)
    right = np.zeros((N, N), bool)
    seam = np.zeros((N, N), bool)
    for x in range(4, 61):
        for y in range(yt(x), yf(x) + 1):
            top[y, x] = True
        for y in range(yf(x) + 1, yb(x) + 1):
            if x == CX or y == yf(x) + 1:
                seam[y, x] = True
            elif x < CX:
                left[y, x] = True
            else:
                right[y, x] = True
    return top, left, right, seam


TOP, LEFT, RIGHT, SEAM = build_masks()
SIL = TOP | LEFT | RIGHT | SEAM


def face_frame(face):
    """origin, u-vector, v-vector of a face in native continuous coords"""
    T, R, F, L, BL, B, BR = [np.array(LM[k]) for k in LM_ORDER]
    if face == 0:
        return T, R - T, L - T
    if face == 1:
        return L, F - L, BL - L
    return F, R - F, B - F


def uv_of(face, x, y):
    o, u, v = face_frame(face)
    M = np.array([[u[0], v[0]], [u[1], v[1]]])
    p = np.array([x + 0.5, y + 0.5]) - o
    return np.linalg.solve(M, p)


def pt_of(face, u, v):
    o, uu, vv = face_frame(face)
    p = o + u * uu + v * vv
    return p[0], p[1]


# precompute uv for every face pixel
UV = np.zeros((3, N, N, 2), float)
for _f, _m in enumerate((TOP, LEFT, RIGHT)):
    ys, xs = np.nonzero(_m | SEAM)
    for y, x in zip(ys, xs):
        UV[_f, y, x] = uv_of(_f, x, y)

FACE_TEX = {0: (28, 28), 1: (28, 27), 2: (28, 27)}  # texel resolution per face


# ------------------------------------------------------------------ patterns
def pattern_tone(pat, f, u, v, seed):
    """Return tone in -2..+2 for texel; 0 = base colour."""
    nu, nv = FACE_TEX[f]
    tu, tv = int(math.floor(u * nu)), int(math.floor(v * nv))
    s = seed + f * 101
    if pat == 'none':
        return 0
    if pat == 'wood':
        # grain runs along u; wavy
        wv = tv + 1.6 * math.sin(tu * 0.33 + s % 7) + 0.8 * math.sin(tu * 0.11 + s % 3)
        r = wv % 6.0
        if r < 1.0 and hash2(tu // 5, int(wv // 6), s) < 0.8:
            return -1
        if 3.0 <= r < 3.6 and hash2(tu // 3, tv, s) < 0.5:
            return 1
        return 0
    if pat == 'stone':
        n = value_noise(tu, tv, 4.0, s)
        h = hash2(tu, tv, s)
        if h < 0.04:
            return -1
        if n > 0.74:
            return 1
        if n < 0.24:
            return -1
        return 0
    if pat == 'gem':
        a = (tu - tv) % 14
        b = (tu + tv) % 18
        if a in (0, 1):
            return 1
        if a == 2 and hash2(tu, tv, s) < 0.5:
            return 2
        if b in (0, 1, 2) and tv > 4:
            return -1
        if tu < 9 and tv < 9 and (tu + tv) < 9 and (tu + tv) % 3 == 0:
            return 2
        return 0
    if pat == 'metal':
        if tv % 3 == 0 and hash2(tu // 4, tv, s) < 0.55:
            return -1
        d = (tu + tv) % 20
        if d in (2, 3, 4):
            return 1
        if d == 5:
            return 2 if hash2(tu, tv, s) < 0.3 else 1
        return 0
    if pat == 'stripes':
        return 1 if ((tu + tv) // 4) % 2 == 0 else 0
    if pat == 'dots':
        row = tv // 7
        ox = 3 if row % 2 else 0
        lx = (tu + ox) % 7 - 3
        ly = tv % 7 - 3
        if lx * lx + ly * ly <= 2:
            return 1
        return 0
    if pat == 'grid':
        if tu % 7 == 3 or tv % 7 == 3:
            return -1
        return 0
    if pat == 'noise':
        h = hash2(tu, tv, s)
        if h < 0.14:
            return -1
        if h > 0.88:
            return 1
        return 0
    if pat == 'scales':
        row = tv // 5
        ox = 3 if row % 2 else 0
        lx = (tu + ox) % 6 - 2.5
        ly = tv % 5
        d = lx * lx + ly * ly * 1.3
        if 6.0 <= d <= 9.5:
            return -1
        if ly == 1 and abs(lx) < 1:
            return 1
        return 0
    if pat == 'glitch':
        h = hash2(0, tv // 2, s)
        if h < 0.12:
            return 3  # cyan bar
        if h > 0.9:
            return 4  # magenta bar
        if hash2(tu // 5, tv, s) < 0.06:
            return 1
        return 0
    if pat == 'stars':
        h = hash2(tu, tv, s)
        if h < 0.035:
            return 2
        if h < 0.07:
            return 1
        return 0
    if pat == 'bricks':
        row = tv // 5
        if tv % 5 == 4:
            return -1
        ox = 4 if row % 2 else 0
        if (tu + ox) % 9 == 8:
            return -1
        if tv % 5 == 0 and hash2(tu, row, s) < 0.5:
            return 1
        return 0
    if pat == 'swirl':
        cx, cy = nu / 2, nv / 2
        dx, dy = tu - cx, tv - cy
        r = math.sqrt(dx * dx + dy * dy)
        ang = math.atan2(dy, dx)
        t = (ang / (2 * math.pi) + r / 9.0) % 1.0
        if t < 0.18:
            return 1
        return 0
    return 0


def tone_color(base, edge, outline, tone):
    if tone == 0:
        return hexc(base)
    if tone == 1:
        return mix(base, edge, 0.28)
    if tone == 2:
        return mix(base, edge, 0.6)
    if tone == -1:
        return mix(base, darken(base, 0.55), 0.45)
    if tone == -2:
        return mix(base, darken(base, 0.6), 0.85)
    if tone == 3:
        return mix(base, '#00ffe0', 0.45)
    if tone == 4:
        return mix(base, '#ff2ad0', 0.45)
    return hexc(base)


# ------------------------------------------------------------------ glyphs
def shear(a, k):
    """vertical shear: column x shifted by round(k*(x-cx)). returns (arr, y_offset_of_centre)"""
    h, w = a.shape[:2]
    cxg = (w - 1) / 2.0
    shifts = [int(math.floor(k * (x - cxg) + 0.5)) for x in range(w)]
    mn, mx = min(shifts), max(shifts)
    out = np.zeros((h + mx - mn, w, 4), np.uint8)
    for x in range(w):
        s = shifts[x] - mn
        out[s:s + h, x] = a[:, x]
    return out, -mn


def glyph_outline_color(die, face_col):
    return None


def is_light_on_dark(ink, face):
    return lum(ink) > lum(face)


def text_sprite(kind, val, ink, face_col, outline_col):
    if kind == 'num' or kind == 'text':
        if len(val) == 1 and val in fonts.B15:
            m = fonts.text_mask(val, fonts.B15)
        elif '/' not in val and all(c in fonts.B12 for c in val) and len(val) <= 2:
            m = fonts.text_mask(val, fonts.B12, spacing=2)
        elif len(val) == 1 and val in fonts.D13:
            m = fonts.text_mask(val, fonts.D13)
        elif '/' not in val and all(c in fonts.D10 for c in val) and len(val) <= 2:
            m = fonts.text_mask(val, fonts.D10)
        elif val == 'BONK':
            m = fonts.text_mask('BO/NK', fonts.D10, line_gap=2)
        elif len(val) <= 3:
            m = fonts.text_mask(val, fonts.S7, spacing=1, bold=True)
        else:
            m = fonts.text_mask(val, fonts.S7, spacing=1)
    a = fonts.mask_to_rgba(m, ink)
    a = pad(a, 1)
    return decorate_glyph(a, ink, face_col, outline_col, True)


def decorate_glyph(a, ink, face_col, outline_col, mono):
    """outline_col is a (deep, light) pair chosen for the face.
    light glyphs -> deep face-shade outline (like the original d4),
    dark glyphs on lighter faces -> emboss or light halo (like the original pi die)."""
    deep, light = outline_col
    if not mono:
        return outline_arr(a, deep, diag=True)
    li, lf = lum(ink), lum(face_col)
    if li >= lf - 0.05:
        return outline_arr(a, deep, diag=True)
    if lf - li > 0.45 and lf > 0.7:
        return add_emboss(a, lighten(face_col, 0.6))
    return outline_arr(a, light, diag=False)


def add_emboss(a, col):
    """1px light shadow below/right of opaque pixels (for dark ink on light faces)."""
    m = a[:, :, 3] > 0
    sh = np.zeros_like(m)
    sh[1:, :] |= m[:-1, :]
    ring = sh & ~m
    out = a.copy()
    out[ring] = hexc(col)
    return out


def icon_sprite(name, ink, face_col, outline_col):
    spr = dice_icons.get_icon(name, ink, face_col)
    spr = pad(spr, 1)
    mono = dice_icons.is_mono(name)
    return decorate_glyph(spr, ink, face_col, outline_col, mono)


PIP_LAYOUT = {
    1: [(0.5, 0.5)],
    2: [(0.27, 0.27), (0.73, 0.73)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)],
    5: [(0.26, 0.26), (0.74, 0.26), (0.5, 0.5), (0.26, 0.74), (0.74, 0.74)],
    6: [(0.28, 0.22), (0.28, 0.5), (0.28, 0.78), (0.72, 0.22), (0.72, 0.5), (0.72, 0.78)],
}


PIP_SPR = {
    ('top', False): """
.###.
#####
#####
.#hh.""",
    ('top', True): """
...#####...
.#########.
###########
###########
###########
.#######hh.
...#hhhh...""",
    ('side', False): """
.##.
####
####
##hh
.hh.""",
    ('side', True): """
..####..
.######.
########
########
########
########
.####hh.
..hhhh..""",
}


def pip_sprite(f, big, ink, face_col):
    art = PIP_SPR[('top' if f == 0 else 'side', big)]
    hi = mix(ink, '#ffffff', 0.38) if lum(ink) < 0.5 else mix(ink, face_col, 0.45)
    a = sprite(art.replace('#', 'I'), {'I': ink, 'h': hi})
    return a


def draw_pips(cv, f, n, ink, face_col, face_mask, oc):
    pts = PIP_LAYOUT[n]
    big = n == 1
    spr = pip_sprite(f, big, ink, face_col)
    deep, light = oc
    if lum(ink) >= lum(face_col) - 0.05:
        spr = outline_arr(pad(spr, 1), deep)
    elif lum(face_col) < 0.72:
        spr = outline_arr(pad(spr, 1), light)
    if f != 0:
        spr, off = shear(spr, SLOPE if f == 1 else -SLOPE)
    else:
        off = 0
    h, w = spr.shape[:2]
    for (pu, pv) in pts:
        if f == 0:
            # rotate layout 45deg so rows of the 6 run left-right on the rhombus
            pu, pv = pv, pu
        elif f == 2:
            # mirror the right face so its layouts mirror the left face
            pu = 1.0 - pu
        px, py = pt_of(f, pu, pv)
        x0 = int(math.floor(px - w / 2.0 + 0.5))
        y0 = int(math.floor(py - (h - 0) / 2.0 + 0.5))
        cv.blit(spr, x0, y0)


# ------------------------------------------------------------------ specials
SPECIALS = {}


def special_sprite(name, die):
    return dice_icons.special(name, die)


# ------------------------------------------------------------------ render
def render_die(d):
    art = d['art']
    tier = d['tier']
    cols = [art['top'], art['left'], art['right']]
    edge = art['edge']
    ink = art['ink']
    outline = art['outline']
    seed = sum(ord(c) * (i + 3) for i, c in enumerate(d['id']))
    cv = Canvas(N)
    masks = (TOP, LEFT, RIGHT)

    # --- base + pattern
    for f, m in enumerate(masks):
        base = cols[f]
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            u, v = UV[f, y, x]
            t = pattern_tone(art['pattern'], f, u, v, seed)
            c = tone_color(base, edge, outline, t)
            # gentle ambient: side faces darken in the bottom few rows
            if f > 0:
                rows_from_bottom = yb(x) - y
                if rows_from_bottom <= 2 and t <= 0:
                    c = mix(c, darken(base, 0.5), 0.22 if rows_from_bottom > 0 else 0.0)
                if f == 2 and rows_from_bottom <= 2 and t <= 0:
                    c = mix(c, darken(base, 0.5), 0.1)
            cv.px(x, y, c)

    # --- rims
    def inmask(m, x, y):
        return 0 <= x < N and 0 <= y < N and m[y, x]

    rim_top = edge
    rim_top_in = mix(edge, cols[0], 0.55)
    rim_left_outer = mix(edge, cols[1], 0.25)
    rim_left_top = mix(edge, cols[1], 0.40)
    rim_right = mix(edge, cols[2], 0.50)
    rim_right_top = mix(edge, cols[2], 0.55)
    ys, xs = np.nonzero(TOP)
    border = set()
    for y, x in zip(ys, xs):
        if not (inmask(TOP, x - 1, y) and inmask(TOP, x + 1, y) and inmask(TOP, x, y - 1) and inmask(TOP, x, y + 1)):
            border.add((x, y))
    for (x, y) in border:
        cv.px(x, y, rim_top)
    # inner soft rim (second ring) on the top face
    for y, x in zip(ys, xs):
        if (x, y) in border:
            continue
        if any((x + dx, y + dy) in border for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cv.px(x, y, mix(cv.get(x, y), rim_top_in, 0.6))
    ys, xs = np.nonzero(LEFT)
    for y, x in zip(ys, xs):
        if x == 4 or y == yb(x):
            cv.px(x, y, rim_left_outer)
        elif y == yf(x) + 2:
            cv.px(x, y, rim_left_top)
        elif x == CX - 1:
            cv.px(x, y, mix(cv.get(x, y), edge, 0.18))
    ys, xs = np.nonzero(RIGHT)
    for y, x in zip(ys, xs):
        if x == 60 or y == yb(x):
            cv.px(x, y, rim_right)
        elif y == yf(x) + 2:
            cv.px(x, y, rim_right_top)
        elif x == CX + 1:
            cv.px(x, y, mix(cv.get(x, y), edge, 0.25))
    # dark seams
    seam_col = outline
    ys, xs = np.nonzero(SEAM)
    for y, x in zip(ys, xs):
        cv.px(x, y, seam_col)
    # tiny highlight where the three faces meet
    cv.px(CX, yf(CX), mix(edge, '#ffffff', 0.5))

    # --- rivets (3x3 rounded studs)
    if art.get('rivets', True):
        gold = tier >= 6
        for f in range(3):
            base = cols[f]
            if f == 0:
                spots = [(0.15, 0.15), (0.85, 0.15), (0.15, 0.85), (0.85, 0.85)]
            else:
                spots = [(0.14, 0.17), (0.86, 0.17), (0.14, 0.86), (0.86, 0.86)]
            for (u, v) in spots:
                px, py = pt_of(f, u, v)
                x0, y0 = int(math.floor(px - 1.5 + 0.5)), int(math.floor(py - 1.5 + 0.5))
                if gold:
                    c_main, c_hi, c_sh = '#e8a81c', '#fff2a0', '#7a4a08'
                else:
                    c_main = mix(outline, base, 0.30)
                    c_hi = mix(base, '#ffffff', 0.45)
                    c_sh = outline
                edge_c = mix(c_main, base, 0.45)
                cv.px(x0 + 1, y0, edge_c)
                cv.px(x0, y0 + 1, edge_c)
                cv.px(x0 + 2, y0 + 1, c_main)
                cv.px(x0 + 1, y0 + 2, c_main)
                cv.px(x0 + 2, y0 + 2, mix(c_sh, base, 0.35))
                cv.px(x0 + 1, y0 + 1, c_hi if gold else mix(c_main, c_hi, 0.55))

    # --- glyphs
    centres = {0: (32.5, 19.5), 1: (18.4, 42.4), 2: (46.6, 42.4)}
    for f, g in enumerate(art['glyphs']):
        kind, val = g.split(':', 1)
        face_col = cols[f]
        oc = glyph_outline(face_col, outline, edge)
        if kind == 'pip':
            draw_pips(cv, f, int(val), ink, face_col, masks[f], oc)
            continue
        if kind == 'icon':
            spr = icon_sprite(val, ink, face_col, oc)
        else:
            spr = text_sprite(kind, val, ink, face_col, oc)
        h, w = spr.shape[:2]
        cx, cy = centres[f]
        if f == 0:
            x0 = int(math.floor(cx - w / 2.0 + 0.5))
            y0 = int(math.floor(cy - h / 2.0 + 0.5))
            cv.blit(spr, x0, y0)
        else:
            k = SLOPE if f == 1 else -SLOPE
            sh, off = shear(spr, k)
            x0 = int(math.floor(cx - w / 2.0 + 0.5))
            y0 = int(math.floor(cy - h / 2.0 + 0.5)) - off
            cv.blit(sh, x0, y0)

    # --- special features
    sp = art.get('special', '')
    if sp:
        for (spr, x, y) in special_sprite(sp, d):
            cv.blit(spr, x, y)

    # --- tier sparkle
    if tier >= 8:
        spots = [(10, 15), (55, 33)] if tier < 10 else [(10, 15), (55, 33), (25, 57)]
        for (sx, sy) in spots:
            spark(cv, sx, sy, tier)

    # --- outer outline
    cv.a = outline_arr(cv.a, outline, diag=False)
    return cv


def spark(cv, x, y, tier):
    c = '#ffffff'
    c2 = '#fff6b0' if tier < 10 else '#ffe8ff'
    cv.px(x, y, c)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.px(x + dx, y + dy, c2)


def glyph_outline(face_col, outline, edge):
    """(deep, light) outline colours for glyphs on this face."""
    lf = lum(face_col)
    if lf < 0.25:
        deep = mix(face_col, edge, 0.75) if lum(edge) > lf + 0.12 else mix(face_col, '#ffffff', 0.35)
    else:
        deep = darken(face_col, 0.58)
    light = mix(face_col, '#ffffff', 0.5)
    return (deep, light)


def landmarks_256():
    return [[int(round(LM[k][0] * SCALE)), int(round(LM[k][1] * SCALE))] for k in LM_ORDER]


def main(only=None):
    cat = json.load(open(CATALOG, encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)
    lms = {}
    items = []
    small = []
    for d in cat['dice']:
        if only and d['id'] not in only:
            continue
        cv = render_die(d)
        a = cv.a
        a[a[:, :, 3] == 0] = 0
        save_png(a, os.path.join(OUT, d['id'] + '.png'), SCALE)
        lms[d['id']] = landmarks_256()
        items.append((d['id'], to_img(a, 2)))
        small.append((d['id'], to_img(a, 1)))
    if not only:
        with open(os.path.join(OUT, 'landmarks.json'), 'w', encoding='utf-8') as fh:
            json.dump(lms, fh, indent=1)
        sheet = contact_sheet(items, (128, 128), 10, label_h=14)
        sheet.save(os.path.join(OUT, 'contact_sheet.png'))
    return items, small


if __name__ == '__main__':
    only = sys.argv[1:] or None
    items, small = main(only)
    prev = os.path.join(REPO, "tools", "art", "_preview")
    os.makedirs(prev, exist_ok=True)
    sheet = contact_sheet(items, (128, 128), 10, label_h=14)
    sheet.save(os.path.join(prev, 'dice_review.png'))
    sheet2 = contact_sheet(small, (64, 64), 20, label_h=12, pad_px=4)
    sheet2.save(os.path.join(prev, 'dice_review_1x.png'))
    print('ok', len(items))
