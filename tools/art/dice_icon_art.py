"""ASCII / procedural pixel art for the 139 dice icons (see dice_icons.py).

Conventions: each icon <= 16x16, transparent background.  Letters come from
pix.BASE_PAL; I/J/i are the die ink (base/highlight/shade).  Callables get
(ink, face_colour) and return an RGBA array.
"""
import math
import numpy as np
from pix import Canvas, sprite, hexc, mix, lighten, darken, lum, outline_arr, pad, flip_h
import fonts

MONO_FN = set()


def _shade(ink):
    return darken(ink, 0.35)


def _hi(ink):
    return lighten(ink, 0.45) if lum(ink) < 0.85 else mix(ink, '#ffffff', 0.6)


# ---------------------------------------------------------------- procedural icons
def p_d20(ink, face):
    cv = Canvas(15, 16)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    ln = darken(ink, 0.6)
    hexp = [(7.5, 0), (15, 4), (15, 12), (7.5, 16), (0, 12), (0, 4)]
    cv.poly(hexp, I)
    # right side facets darker, bottom darkest
    cv.poly([(15, 4), (7.5, 0), (7.5, 3.5), (12.5, 11.5), (15, 12)], mix(I, i, 0.6))
    cv.poly([(2.5, 11.5), (12.5, 11.5), (15, 12), (7.5, 16), (0, 12)], i)
    cv.poly([(7.5, 3.5), (12.5, 11.5), (2.5, 11.5)], J)
    # facet edges
    for (a, b) in [((7.5, 0), (7.5, 3.5)), ((0, 12), (2.5, 11.5)), ((15, 12), (12.5, 11.5)),
                   ((7.5, 3.5), (2.5, 11.5)), ((7.5, 3.5), (12.5, 11.5)), ((2.5, 11.5), (12.5, 11.5)),
                   ((2.5, 11.5), (7.5, 15.5)), ((12.5, 11.5), (7.5, 15.5))]:
        cv.line(a[0] - 0.5 if a[0] > 7.5 else a[0], a[1], b[0] - 0.5 if b[0] > 7.5 else b[0], b[1], ln)
    # "20" hint on the main facet
    cv.px(6, 8, ln); cv.px(5, 9, ln); cv.px(6, 9, ln)
    cv.px(8, 8, ln); cv.px(9, 8, ln); cv.px(8, 9, ln); cv.px(9, 9, ln)
    return cv.a


def p_shell(ink, face):
    cv = Canvas(15, 14)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    cx, cy = 7.0, 6.8
    for y in range(14):
        for x in range(15):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy * 1.08)
            if r > 6.9:
                continue
            a = math.atan2(dy, dx)
            s = (r - 2.3 * ((a + math.pi) / (2 * math.pi))) / 2.3
            fr = s - math.floor(s)
            if fr < 0.32 and r > 1.0:
                c = i
            elif fr > 0.75 and dy < 1:
                c = J
            else:
                c = I
            cv.px(x, y, c)
    # aperture lip at bottom-right
    cv.px(11, 11, J); cv.px(12, 10, J); cv.px(12, 11, I); cv.px(13, 12, I); cv.px(12, 12, I)
    return cv.a


MONO_FN.add('shell')


def _stamp(cv, art, x0, y0, pal):
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != '.':
                cv.px(x0 + x, y0 + y, pal[ch])


def p_scales_v2(ink, face):
    cv = Canvas(16, 14)
    pal = {'I': hexc(ink), 'J': _hi(ink), 'i': darken(ink, 0.45)}
    sc = ['.iiii.', 'iJJJIi', 'iJIIIi', 'iIIIIi', 'iIIIIi', '.iIIi.']
    for (x0, y0) in [(0, 0), (5, 0), (10, 0), (2, 4), (7, 4), (0, 8), (5, 8), (10, 8)]:
        _stamp(cv, sc, x0, y0, pal)
    return cv.a


MONO_FN.add('scales')


def p_comet(ink, face):
    cv = Canvas(15, 15)
    I, J, i = hexc(ink), _hi(ink), mix(ink, face, 0.45)
    cv.line(1, 1, 9, 9, i, w=2)
    cv.line(5, 1, 10, 7, i)
    cv.line(1, 5, 7, 10, i)
    cv.line(3, 2, 10, 9, I)
    cv.line(2, 3, 9, 10, I)
    cv.circle(10.5, 10.5, 3.6, I)
    cv.px(9, 9, J); cv.px(10, 9, J); cv.px(9, 10, J)
    return cv.a


def p_muscle(ink, face):
    return None


def p_galaxy_v2(ink, face):
    cv = Canvas(16, 16)
    I, J = hexc(ink), _hi(ink)
    c = 8.0
    for arm in (0, math.pi):
        for t in np.linspace(0.0, 3.2, 400):
            r = 1.2 + 1.9 * t
            a = t * 1.15 + arm
            x = c + r * math.cos(a)
            y = c + r * math.sin(a) * 0.85
            w = 1.6 - t * 0.35
            for ox in (-0.5, 0, 0.5):
                for oy in (-0.5, 0, 0.5):
                    if abs(ox) + abs(oy) <= w * 0.6:
                        cv.px(int(math.floor(x + ox)), int(math.floor(y + oy)), I)
    cv.circle(8, 8, 2.6, J)
    cv.rect(7, 7, 8, 8, '#ffffff')
    for (x, y) in ((2, 2), (13, 3), (14, 12), (2, 13)):
        cv.px(x, y, J)
    return cv.a


def p_candy(ink, face):
    cv = Canvas(16, 10)
    pk, pk2, w = hexc('#ff5aa8'), hexc('#c02a78'), hexc('#ffffff')
    cv.poly([(0, 1), (4.5, 4), (4.5, 6), (0, 9)], pk)
    cv.poly([(16, 1), (11.5, 4), (11.5, 6), (16, 9)], pk)
    cv.px(0, 1, pk2); cv.px(0, 8, pk2); cv.px(15, 1, pk2); cv.px(15, 8, pk2)
    cv.vline(1, 2, 7, pk2)
    cv.vline(14, 2, 7, pk2)
    cv.ellipse(8, 5, 4.6, 4.6, w)
    for y in range(10):
        for x in range(3, 13):
            if cv.get(x, y)[3] and cv.get(x, y)[:3] == w[:3]:
                if ((x + y) // 2) % 2 == 0:
                    cv.px(x, y, pk)
    cv.px(6, 2, w); cv.px(5, 3, w)
    return cv.a


def p_bubble(ink, face):
    cv = Canvas(14, 14)
    I, J = hexc(ink), _hi(ink)
    cv.ellipse(7, 7, 6.6, 6.6, I, fill=False)
    cv.px(3, 4, J); cv.px(4, 3, J); cv.px(3, 5, J); cv.px(5, 3, J)
    cv.px(4, 4, J)
    cv.px(9, 10, I)
    return cv.a


MONO_FN.add('bubble')


def p_gear(ink, face):
    cv = Canvas(16, 16)
    I, i = hexc(ink), _shade(ink)
    cx, cy = 8, 8
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            tooth = (math.cos(a * 8) > 0.25)
            rmax = 7.9 if tooth else 5.9
            if r <= rmax and r > 2.3:
                cv.px(x, y, I if r < 5.2 or not tooth else I)
            if 2.3 < r <= 3.3:
                cv.px(x, y, i)
    return cv.a


MONO_FN.add('gear')


def _tetro(cells, base):
    c0 = hexc(base)
    hi = lighten(c0, 0.5)
    sh = darken(c0, 0.35)
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    cv = Canvas((max(xs) + 1) * 4, (max(ys) + 1) * 4)
    for (cx, cy) in cells:
        x0, y0 = cx * 4, cy * 4
        cv.rect(x0, y0, x0 + 3, y0 + 3, c0)
        cv.hline(x0, x0 + 2, y0, hi)
        cv.vline(x0, y0, y0 + 2, hi)
        cv.hline(x0 + 1, x0 + 3, y0 + 3, sh)
        cv.vline(x0 + 3, y0 + 1, y0 + 3, sh)
    return cv.a


def p_tetro_t(ink, face):
    return _tetro([(0, 0), (1, 0), (2, 0), (1, 1)], '#b04aff')


def p_tetro_l(ink, face):
    return _tetro([(0, 0), (0, 1), (0, 2), (1, 2)], '#ff8a1f')


def p_tetro_s(ink, face):
    return _tetro([(1, 0), (2, 0), (0, 1), (1, 1)], '#4fd040')


def p_vault(ink, face):
    cv = Canvas(15, 15)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    cv.circle(7.5, 7.5, 7.4, i)
    cv.circle(7.5, 7.5, 6.3, I)
    cv.circle(7.5, 7.5, 4.6, J)
    cv.circle(7.5, 7.5, 3.6, I)
    # handle spokes
    for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189):
        x1 = 7.5 + math.cos(a) * 5.6
        y1 = 7.5 - math.sin(a) * 5.6
        cv.line(7, 7, x1 - 0.5, y1 - 0.5, i)
    cv.rect(6, 6, 8, 8, i)
    cv.px(7, 7, J)
    # bolts on rim
    for k in range(8):
        a = k * math.pi / 4
        cv.px(int(7.5 + math.cos(a) * 6.6), int(7.5 + math.sin(a) * 6.6), J)
    return cv.a


MONO_FN.add('vault')


def p_dial(ink, face):
    cv = Canvas(15, 15)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    cv.circle(7.5, 7.5, 7.4, I)
    cv.circle(7.5, 7.5, 5.4, J)
    for k in range(12):
        a = k * math.pi / 6
        cv.px(int(7.5 + math.cos(a) * 6.5), int(7.5 + math.sin(a) * 6.5), i)
    cv.circle(7.5, 7.5, 2.3, i)
    cv.line(7, 7, 10, 3, i)
    cv.px(10, 3, i)
    cv.px(7, 0, J)
    return cv.a


MONO_FN.add('dial')


def p_snowflake(ink, face):
    cv = Canvas(15, 15)
    I, J = hexc(ink), _hi(ink)
    c = 7
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 2
        for t in range(0, 8):
            x = c + 0.5 + math.cos(a) * t
            y = c + 0.5 - math.sin(a) * t
            cv.px(int(math.floor(x)), int(math.floor(y)), I)
        # branches
        bx = c + 0.5 + math.cos(a) * 4.2
        by = c + 0.5 - math.sin(a) * 4.2
        for da in (0.75, -0.75):
            for t in (1, 2):
                x = bx + math.cos(a + da) * t
                y = by - math.sin(a + da) * t
                cv.px(int(math.floor(x)), int(math.floor(y)), I)
    cv.rect(6, 6, 8, 8, I)
    cv.px(7, 7, J)
    return cv.a


MONO_FN.add('snowflake')


def p_wheel(ink, face):
    cv = Canvas(15, 15)
    cv.circle(7.5, 7.5, 7.4, '#1b1b1f')
    cv.circle(7.5, 7.5, 4.9, '#c8ccd8')
    cv.circle(7.5, 7.5, 3.6, '#7a7e8c')
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        cv.line(7.5, 7.5, 7.5 + math.cos(a) * 4.2, 7.5 + math.sin(a) * 4.2, '#c8ccd8')
    cv.rect(6, 6, 8, 8, '#e8eaf0')
    cv.px(7, 7, '#4a4c58')
    # tread marks
    for k in range(12):
        a = k * math.pi / 6
        cv.px(int(7.5 + math.cos(a) * 6.4), int(7.5 + math.sin(a) * 6.4), '#3a3a44')
    return cv.a


def p_roulette(ink, face):
    cv = Canvas(16, 16)
    c = 8.0
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            if r > 7.9:
                continue
            a = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
            seg = int(a * 12) % 12
            if r > 5.0:
                if seg == 3:
                    col = '#1aa040'
                else:
                    col = '#e02020' if seg % 2 == 0 else '#1b1b1b'
                if r > 7.0:
                    col = '#c08a3a'
            elif r > 4.0:
                col = '#7a4a1a'
            elif r > 2.0:
                col = '#c08a3a'
            else:
                col = '#f0e0a0'
            cv.px(x, y, col)
    cv.px(4, 4, '#ffffff')  # ball
    cv.px(5, 4, '#e0e0e0')
    return cv.a


def p_atom(ink, face):
    cv = Canvas(16, 16)
    I, J = hexc(ink), _hi(ink)
    c = 8.0
    for ang in (0, math.pi / 3, -math.pi / 3):
        for t in np.linspace(0, 2 * math.pi, 120):
            ex, ey = 7.2 * math.cos(t), 2.6 * math.sin(t)
            x = c + ex * math.cos(ang) - ey * math.sin(ang)
            y = c + ex * math.sin(ang) + ey * math.cos(ang)
            cv.px(int(math.floor(x)), int(math.floor(y)), I)
    cv.circle(8, 8, 1.9, J)
    return cv.a


MONO_FN.add('atom')


def p_blackhole(ink, face):
    cv = Canvas(16, 12)
    I, J = hexc(ink), _hi(ink)
    cv.ellipse(8, 6, 7.9, 3.4, I)
    cv.ellipse(8, 6, 5.9, 2.0, J)
    cv.circle(8, 6, 3.6, '#050508')
    # front part of the disk crosses in front of the hole
    for x in range(2, 14):
        cv.px(x, 7, I if x in (2, 3, 12, 13) else J)
    cv.px(5, 3, '#ffffff')
    return cv.a


def p_swirl(ink, face):
    cv = Canvas(15, 15)
    I = hexc(ink)
    c = 7.5
    for t in np.linspace(0, 5.6 * math.pi, 900):
        r = 0.42 * t
        x = c + r * math.cos(t)
        y = c + r * math.sin(t)
        cv.px(int(math.floor(x)), int(math.floor(y)), I)
        cv.px(int(math.floor(x + 0.6)), int(math.floor(y)), I)
    return cv.a


MONO_FN.add('swirl')


def p_galaxy(ink, face):
    cv = Canvas(16, 16)
    I, J = hexc(ink), _hi(ink)
    c = 8.0
    for arm in (0, math.pi):
        for t in np.linspace(0.2, 2.6 * math.pi / 2, 300):
            r = 1.0 + 1.55 * t
            a = t + arm
            x = c + r * math.cos(a)
            y = c + r * math.sin(a) * 0.8
            cv.px(int(math.floor(x)), int(math.floor(y)), I)
            if r < 5:
                cv.px(int(math.floor(x + 0.7)), int(math.floor(y + 0.4)), I)
    cv.circle(8, 8, 2.2, J)
    cv.px(7, 7, '#ffffff')
    cv.px(8, 7, '#ffffff')
    return cv.a


def p_sun(ink, face):
    cv = Canvas(16, 16)
    I, J = hexc(ink), _hi(ink)
    c = 8.0
    for k in range(8):
        a = k * math.pi / 4
        for t in np.linspace(5.4, 7.9, 6):
            x = c + math.cos(a) * t
            y = c + math.sin(a) * t
            cv.px(int(math.floor(x)), int(math.floor(y)), I)
            if k % 2 == 0:
                cv.px(int(math.floor(x + math.sin(a) * 0.9)), int(math.floor(y - math.cos(a) * 0.9)), I)
    cv.circle(8, 8, 4.4, I)
    cv.px(6, 6, J); cv.px(7, 6, J); cv.px(6, 7, J)
    return cv.a


MONO_FN.add('sun')


def p_sun_jp(ink, face):
    cv = Canvas(14, 14)
    cv.circle(7, 7, 6.8, '#d81e1e')
    cv.px(4, 4, '#ff6a5a'); cv.px(5, 3, '#ff6a5a')
    return cv.a


def p_planet(ink, face):
    cv = Canvas(16, 13)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    # back half of ring
    for t in np.linspace(math.pi, 2 * math.pi, 120):
        x = 8 + 7.8 * math.cos(t)
        y = 6.5 + 2.4 * math.sin(t) - (x - 8) * 0.18
        cv.px(int(math.floor(x)), int(math.floor(y)), i)
    cv.circle(8, 6.5, 4.6, I)
    cv.px(6, 4, J); cv.px(7, 3, J); cv.px(6, 5, J)
    cv.hline(5, 11, 7, i)
    for t in np.linspace(0, math.pi, 120):
        x = 8 + 7.8 * math.cos(t)
        y = 6.5 + 2.4 * math.sin(t) - (x - 8) * 0.18
        cv.px(int(math.floor(x)), int(math.floor(y)), J)
    return cv.a


MONO_FN.add('planet')


def p_supernova(ink, face):
    cv = Canvas(16, 16)
    I, J = hexc(ink), _hi(ink)
    c = 8.0
    for k in range(16):
        a = k * math.pi / 8
        L = 7.8 if k % 2 == 0 else 5.0
        for t in np.linspace(2.5, L, 10):
            cv.px(int(math.floor(c + math.cos(a) * t)), int(math.floor(c + math.sin(a) * t)), I)
    cv.circle(8, 8, 3.4, J)
    cv.circle(8, 8, 1.8, '#ffffff')
    return cv.a


def p_clock(ink, face):
    cv = Canvas(15, 15)
    I = hexc(ink)
    cv.circle(7.5, 7.5, 7.4, I)
    cv.circle(7.5, 7.5, 6.0, '#fff8e8')
    for k in range(12):
        a = k * math.pi / 6
        r = 4.9
        cv.px(int(7.5 + math.cos(a) * r), int(7.5 + math.sin(a) * r), '#8a7a5a' if k % 3 else I)
    cv.line(7, 7, 7, 3, I)
    cv.line(7, 7, 10, 8, I)
    cv.px(7, 7, '#c41a1a')
    return cv.a


def p_honey(ink, face):
    cv = Canvas(16, 15)
    O, o, H = hexc('#ffb020'), hexc('#a85a08'), hexc('#ffe070')

    def hexcell(cx, cy):
        pts = [(cx - 2.5, cy - 4), (cx + 2.5, cy - 4), (cx + 5, cy), (cx + 2.5, cy + 4), (cx - 2.5, cy + 4), (cx - 5, cy)]
        cv.poly(pts, o)
        pts2 = [(cx - 1.7, cy - 3), (cx + 1.7, cy - 3), (cx + 3.6, cy), (cx + 1.7, cy + 3), (cx - 1.7, cy + 3), (cx - 3.6, cy)]
        cv.poly(pts2, O)
        cv.px(int(cx - 1), int(cy - 2), H)
    hexcell(5, 4.5)
    hexcell(12.5, 8.5)
    hexcell(5, 10.5)
    # drip
    cv.vline(9, 12, 14, O)
    return cv.a


def p_scales(ink, face):
    cv = Canvas(15, 14)
    I, J, i = hexc(ink), _hi(ink), _shade(ink)
    rows = [(0, 2.5, [2.5, 7.5, 12.5]), (1, 6.5, [5, 10]), (2, 10.5, [2.5, 7.5, 12.5])]
    for (rr, cy, xs) in rows:
        for cx in xs:
            for y in range(int(cy - 3), int(cy + 4)):
                for x in range(int(cx - 3), int(cx + 4)):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    if dy < -0.5 and dx * dx + dy * dy <= 6.5:
                        pass
                    if dx * dx + (dy * 1.15) ** 2 <= 8.0 and dy > -2.5:
                        c = I
                        if dx * dx + (dy * 1.15) ** 2 >= 5.0 and dy > 0:
                            c = i
                        if dy < -0.5 and dx < 0:
                            c = J
                        cv.px(x, y, c)
    return cv.a


MONO_FN.add('scales')


def p_nebula(ink, face):
    cv = Canvas(16, 14)
    cols = ['#ff5ac8', '#a43ae0', '#4a7aff', '#ffb0f0']
    blobs = [(5, 6, 4.2, 0), (10, 5, 4.0, 1), (9, 9, 3.6, 2), (6, 9, 2.6, 3), (11, 8, 2.0, 3)]
    for (cx, cy, r, ci) in blobs:
        for y in range(14):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.15)
                if d <= r:
                    cv.px(x, y, cols[ci])
    for (x, y) in ((3, 4), (12, 3), (8, 7), (13, 10), (5, 10)):
        cv.px(x, y, '#ffffff')
    return cv.a


def p_d20_alias(ink, face):
    return p_d20(ink, face)


def p_shuriken(ink, face):
    cv = Canvas(15, 15)
    W, w, g = hexc('#eef2fa'), hexc('#9aa2b4'), hexc('#4a4e5c')
    c = 7.5
    for y in range(15):
        for x in range(15):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            R = 2.4 + 5.3 * abs(math.cos(2 * a)) ** 6
            if r <= R:
                q = (a + math.pi * 2) % (math.pi / 2)
                cv.px(x, y, W if q < math.pi / 4 else w)
    cv.circle(7.5, 7.5, 1.6, g)
    cv.px(7, 7, None)
    return cv.a


def p_meteor(ink, face):
    cv = Canvas(16, 16)
    O, Y, R = hexc('#ff7a1f'), hexc('#ffe25a'), hexc('#e8301a')
    cv.line(15, 0, 7, 8, R, w=3)
    cv.line(14, 1, 7, 8, O, w=2)
    cv.line(13, 2, 8, 7, Y)
    cv.line(15, 4, 9, 9, O)
    cv.line(11, 0, 7, 5, O)
    cv.circle(5.5, 10.5, 5.0, '#5a3a2a')
    cv.circle(5.0, 10.0, 3.9, '#8a6450')
    cv.px(3, 8, '#b8957e'); cv.px(4, 8, '#b8957e'); cv.px(3, 9, '#b8957e')
    cv.px(6, 12, '#5a3a2a'); cv.px(7, 11, '#5a3a2a'); cv.px(4, 12, '#6a4a38')
    return cv.a


ICON_FN = {
    'd20': p_d20, 'candy': p_candy, 'bubble': p_bubble, 'gear': p_gear,
    'tetro_t': p_tetro_t, 'tetro_l': p_tetro_l, 'tetro_s': p_tetro_s,
    'snowflake': p_snowflake, 'wheel': p_wheel,
    'wheel_roulette': p_roulette, 'atom': p_atom, 'blackhole': p_blackhole,
    'swirl': p_swirl, 'galaxy': p_galaxy, 'sun': p_sun, 'sun_jp': p_sun_jp,
    'planet': p_planet, 'supernova': p_supernova, 'clock': p_clock,
    'scales': p_scales_v2, 'nebula': p_nebula, 'shuriken': p_shuriken,
    'shell': p_shell, 'comet': p_comet, 'galaxy': p_galaxy_v2, 'meteor': p_meteor,
}
MONO_FN.add('comet')


def register(icon):
    from dice_icon_art2 import register_ascii
    register_ascii(icon)
    for k, fn in ICON_FN.items():  # procedural versions win
        icon(k, fn)


# ---------------------------------------------------------------- special features
def special_parts(name, die):
    from dice_icon_art2 import special_parts as sp
    return sp(name, die)
