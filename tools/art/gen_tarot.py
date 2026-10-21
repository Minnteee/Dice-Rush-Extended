"""Generate the 40 minor-arcana tarot cards (51x79, 4-colour demichrome palette + 1 accent per suit).

The frame is copied pixel-exact from an original card (label boxes cleared), the
labels use a 3x5 pixel font like the originals, the centre shows the suit pips
in a classic playing-card layout over a quiet slate scenery.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import hexc, sprite, to_img, contact_sheet, OUT_ROOT, REF_ROOT

OUT = os.path.join(OUT_ROOT, 'tarot')
REF_DIR = os.path.join(REF_ROOT, 'art', 'dog_shrine', 'tarot_1x')

D = '#211e20'   # background
S = '#555568'   # slate
K = '#a0a08b'   # khaki
L = '#e9efec'   # light
ACCENT = {'wands': '#78a05a', 'cups': '#5f86b8', 'swords': '#c4d6ea', 'pentacles': '#d8b25a'}
SUITS = ['wands', 'cups', 'swords', 'pentacles']
LABEL = {'wands': 'WANDS', 'cups': 'CUPS', 'swords': 'SWORDS', 'pentacles': 'PENTACLES'}
ROMAN = {1: 'ACE', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}

ART_X0, ART_X1, ART_Y0, ART_Y1 = 3, 47, 11, 67   # inclusive art area

# --------------------------------------------------------------- 3x5 font (like the originals)
F35 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'],
    'C': ['.##', '#..', '#..', '#..', '.##'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'],
    'I': ['###', '.#.', '.#.', '.#.', '###'],
    'L': ['#..', '#..', '#..', '#..', '###'],
    'N': ['#.#', '###', '###', '###', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'P': ['##.', '#.#', '##.', '#..', '#..'],
    'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'],
    'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#...#', '#...#', '#.#.#', '##.##', '#...#'],
    'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
}


def text_w(t):
    return sum(len(F35[c][0]) for c in t) + (len(t) - 1)


def draw_text(a, t, cx, y, col):
    x = cx - text_w(t) // 2
    for c in t:
        g = F35[c]
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == '#':
                    a[y + gy, x + gx] = hexc(col)
        x += len(g[0]) + 1


# --------------------------------------------------------------- frame
def load_frame():
    src = np.array(Image.open(os.path.join(REF_DIR, '17_The Star.png')).convert('RGBA'))
    a = src.copy()
    a[ART_Y0:ART_Y1 + 1, ART_X0:ART_X1 + 1] = hexc(D)
    for (y0, y1) in ((5, 9), (69, 73)):
        for y in range(y0, y1 + 1):
            row = src[y]
            xs = [x for x in range(4, 47) if tuple(row[x][:3]) == hexc(L)[:3]]
            if xs:
                a[y, min(xs):max(xs) + 1] = hexc(L)
    return a


def put(a, x, y, c):
    if ART_X0 <= x <= ART_X1 and ART_Y0 <= y <= ART_Y1:
        a[y, x] = hexc(c)


# --------------------------------------------------------------- sprites
PAL = {'D': D, 'S': S, 'K': K, 'L': L}

PIP = {
    'wands': """
.....A.....
....AKA....
...A.KLA...
.....KL....
..A..KL..A.
...AAKLAA..
.....KL....
....SKL....
.....KL....
....SKL....
.....KL....
.....SK....""",
    'cups': """
LLLLLLLLLLL
LAAAAAAAAAL
LKKKKKKKKKL
LKLKKKKKKKL
.LKKKKKKKL.
..LKKKKKL..
...LLKLL...
.....K.....
....LKL....
..KKKKKKK..
.SSSSSSSSS.""",
    'swords': """
....A....
...LLA...
...LLA...
...LLA...
...LLA...
...LLA...
...LLA...
.KKKKKKK.
K..SKS..K
....K....
....S....
...KKK...""",
    'pentacles': """
...KKKKK...
..K.LLL.K..
.K...A...K.
K....A....K
KLAAAAAAALK
KL.AAAAA.LK
K...AAA...K
K..AA.AA..K
.KAA...AAK.
..K.LLL.K..
...KKKKK...""",
}

ACE = {
    'wands': """
........L........
.......LAL.......
......A.A.A......
.......ALA.......
....AA.LKS.AA....
...A..ALKSA..A...
.......LKS.......
......KKKKK......
..AA...LKS...AA..
....AA.LKS.AA....
......ALKSA......
.......LKS.......
...A...LKS.......
....AA.LKS.......
......ALKS.......
.......LKSA......
.......LKS.AA....
.......LKS...A...
......KKKKK......
.......LKS.......
.......LKS.......
.......LKS.......
.......LKS.......
......ALKS.......
.....A.LKS.......
.......LKS.......
.......LKS.......
......SLKSS......
.......LKS.......
.......LKS.......
.......LKS.......
.......SKS.......
........S........""",
    'cups': """
....A.....A.....A....
.....A...A.A...A.....
..LLLLLLLLLLLLLLLLL..
..LAAAAAAAAAAAAAAAL..
..LKKKKKKKKKKKKKKKL..
..LKLKKKKKKKKKKKKKL..
..LKLKKKKKLKKKKKKKL..
...LKLKKKLLLKKKKKL...
...LKKKKKKLKKKKKKL...
....LKKKKKKKKKKKL....
.....LKKKKKKKKKL.....
......LLKKKKKLL......
........LLKLL........
.........LKL.........
..........K..........
.........LKL.........
..........K..........
..........K..........
.........LKL.........
.......KKKKKKK.......
.....KKLLLLLLLKK.....
....SSSSSSSSSSSSS....""",
    'swords': """
.....L...L...L.....
.....LL.LLL.LL.....
.....LLLLLLLLLL....
......KAKAKAKA.....
.........A.........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
........LAS........
...KKKKKKKKKKKKK...
..KLLLLLLLLLLLLLK..
...KKKKKKKKKKKKK...
.........K.........
........SKS........
.........K.........
........SKS........
.........K.........
........KKK........
.......KLLLK.......
........KKK........""",
    'pentacles': """
.......KKKKKKK.......
.....KKLLLLLLLKK.....
....KLL.......LLK....
...KL.....A.....LK...
..KL.....AAA.....LK..
..KL.....AAA.....LK..
.KL.....AAAAA.....LK.
.KLAAAAAAAAAAAAAAALK.
KL...AAAAAAAAAAA...LK
KL......AAAAA......LK
KL.....AAAAAAA.....LK
KL....AAAA.AAAA....LK
.KL..AAA.....AAA..LK.
.KL.AAA.......AAA.LK.
..KLAA.........AALK..
..KL.............LK..
...KL...........LK...
....KLL.......LLK....
.....KKLLLLLLLKK.....
.......KKKKKKK.......""",
}

# pip grid (card coordinates)
COLX = {'l': 12, 'c': 25, 'r': 38}


def row_y(r):
    return 18 + r * 6.67


LAYOUT = {
    2: [('c', 0.5), ('c', 5.5)],
    3: [('c', 0), ('c', 3), ('c', 6)],
    4: [('l', 0.5), ('r', 0.5), ('l', 5.5), ('r', 5.5)],
    5: [('l', 0), ('r', 0), ('c', 3), ('l', 6), ('r', 6)],
    6: [('l', 0), ('r', 0), ('l', 3), ('r', 3), ('l', 6), ('r', 6)],
    7: [('l', 0), ('r', 0), ('c', 1.5), ('l', 3), ('r', 3), ('l', 6), ('r', 6)],
    8: [('l', 0), ('r', 0), ('c', 1.5), ('l', 3), ('r', 3), ('c', 4.5), ('l', 6), ('r', 6)],
    9: [('l', 0), ('r', 0), ('l', 2), ('r', 2), ('c', 3), ('l', 4), ('r', 4), ('l', 6), ('r', 6)],
    10: [('l', 0), ('r', 0), ('c', 1), ('l', 2), ('r', 2), ('l', 4), ('r', 4), ('c', 5), ('l', 6), ('r', 6)],
}


def blit(a, spr, cx, cy):
    h, w = spr.shape[:2]
    x0 = int(math.floor(cx - w / 2.0 + 0.5))
    y0 = int(math.floor(cy - h / 2.0 + 0.5))
    for yy in range(h):
        for xx in range(w):
            if spr[yy, xx, 3]:
                put_rgba(a, x0 + xx, y0 + yy, spr[yy, xx])
    return (x0, y0, x0 + w - 1, y0 + h - 1)


def put_rgba(a, x, y, c):
    if ART_X0 <= x <= ART_X1 and ART_Y0 <= y <= ART_Y1:
        a[y, x] = c


# --------------------------------------------------------------- scenery (slate only, quiet)
def scenery(a, suit, rng):
    if suit == 'wands':
        # rolling hills
        for x in range(ART_X0, ART_X1 + 1):
            h1 = 62 + 2.2 * math.sin(x * 0.19 + 1.0)
            for y in range(int(h1), ART_Y1 + 1):
                put(a, x, y, S)
            if x % 7 == 3:
                put(a, x, int(h1) - 1, K)
                put(a, x, int(h1) - 2, S)
    elif suit == 'cups':
        # water waves like the original Star card
        for y0 in (61, 64):
            for x in range(ART_X0 + 1, ART_X1):
                ph = (x + (2 if y0 == 64 else 0)) % 6
                if ph in (0, 1):
                    put(a, x, y0, S)
                elif ph == 2 or ph == 5:
                    put(a, x, y0 + 1, S)
                elif ph in (3, 4):
                    put(a, x, y0 + 2, S)
    elif suit == 'swords':
        # wind streaks and a cloud bank
        for (y, x0, x1) in ((14, 5, 14), (16, 9, 19), (15, 33, 44), (17, 29, 37)):
            for x in range(x0, x1 + 1):
                put(a, x, y, S)
        for (cx, cy, r) in ((8, 66, 5), (17, 67, 6), (27, 66, 5), (36, 67, 6), (44, 66, 4)):
            for y in range(cy - r, ART_Y1 + 1):
                for x in range(cx - r, cx + r + 1):
                    if (x - cx) ** 2 + ((y - cy) * 1.5) ** 2 <= r * r:
                        put(a, x, y, S)
    elif suit == 'pentacles':
        # low garden wall of slate bricks with khaki vines
        for y in range(62, ART_Y1 + 1):
            for x in range(ART_X0, ART_X1 + 1):
                row = (y - 62) // 3
                mortar = (y - 62) % 3 == 2 or (x + (3 if row % 2 else 0)) % 6 == 0
                if not mortar:
                    put(a, x, y, S)
        for x in range(ART_X0 + 2, ART_X1, 5):
            put(a, x, 61, K)
            put(a, x + 1, 60, S)
    # a few twinkles
    for (x, y) in rng:
        put(a, x, y, S)


TWINKLES = [(6, 14), (44, 13), (5, 40), (45, 36), (8, 27), (42, 50), (24, 13), (6, 54), (44, 24)]


def free(a, x, y):
    return all(tuple(a[yy, xx][:3]) == hexc(D)[:3] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)
               if ART_X0 <= xx <= ART_X1 and ART_Y0 <= yy <= ART_Y1)


def twinkle(a, x, y, big=False):
    if not free(a, x, y):
        return
    put(a, x, y, K if not big else L)
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(a, x + dx, y + dy, S)


def halo(a, cx, cy, r):
    for k in range(48):
        ang = k * 2 * math.pi / 48
        x = int(round(cx + math.cos(ang) * r))
        y = int(round(cy + math.sin(ang) * r * 1.15))
        put(a, x, y, S)
    for k in range(12):
        ang = k * 2 * math.pi / 12 + 0.26
        x = int(round(cx + math.cos(ang) * r))
        y = int(round(cy + math.sin(ang) * r * 1.15))
        put(a, x, y, K)
    # rays
    for k in range(16):
        ang = k * 2 * math.pi / 16
        for t in range(r + 3, r + 9):
            if (t + k) % 2 == 0:
                put(a, int(round(cx + math.cos(ang) * t)), int(round(cy + math.sin(ang) * t * 1.15)), S)


def make_card(suit, n):
    a = load_frame()
    pal = dict(PAL)
    pal['A'] = ACCENT[suit]
    scenery(a, suit, [])
    if n == 1:
        halo(a, 25, 37, 15)
        spr = sprite(ACE[suit], pal)
        blit(a, spr, 25.5, 37.5)
        for (x, y) in ((8, 16), (42, 16), (7, 52), (43, 53)):
            twinkle(a, x, y, big=True)
    else:
        spr = sprite(PIP[suit], pal)
        for (col, r) in LAYOUT[n]:
            blit(a, spr, COLX[col] + 0.5, row_y(r) + 0.5)
        for (x, y) in TWINKLES:
            twinkle(a, x, y)
    draw_text(a, ROMAN[n], 25, 5, D)
    draw_text(a, LABEL[suit], 25, 69, D)
    return a


def main():
    os.makedirs(OUT, exist_ok=True)
    items = []
    for suit in SUITS:
        for n in range(1, 11):
            a = make_card(suit, n)
            cid = 'm_%s_%d' % (suit, n)
            Image.fromarray(a, 'RGBA').save(os.path.join(OUT, cid + '.png'))
            items.append((cid, to_img(a, 3)))
    refs = ['0_The Fool.png', '13_Death.png', '17_The Star.png', '19_The Sun.png', 'Card Back.png']
    ref_items = []
    for r in refs:
        im = Image.open(os.path.join(REF_DIR, r)).convert('RGBA')
        ref_items.append(('orig ' + r.split('_')[-1].replace('.png', ''),
                          im.resize((im.width * 3, im.height * 3), Image.NEAREST)))
    sheet = contact_sheet(ref_items + items, (153, 237), 9, label_h=14, bg=(52, 48, 50, 255))
    sheet.save(os.path.join(OUT, 'contact_sheet.png'))
    print('ok', len(items))


if __name__ == '__main__':
    main()
