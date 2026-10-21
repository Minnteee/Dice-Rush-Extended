"""Staff icons: 10 chibi workers, 160x160 (native 40x40 x4)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pix import hexc, mix, darken, lighten, to_img, contact_sheet, OUT_ROOT
from iconkit import Icon, OUTLINE, star_pts, sparkle, to_png
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

OUT = os.path.join(OUT_ROOT, 'staff')
SC = 4
SKIN = '#f6c896'
SKIN_SH = '#d8986a'


# ------------------------------------------------------------------ chibi base
def body(ic, top, top2=None, pants='#3a3a52', shoes='#2a1e1e', robe=False, belly=None):
    # legs + shoes
    if not robe:
        ic.part(lambda c: (c.rect(15, 30, 18, 34, '#fff'), c.rect(21, 30, 24, 34, '#fff')), pants)
        ic.part(lambda c: (c.rect(13, 34, 18, 36, '#fff'), c.rect(21, 34, 26, 36, '#fff')), shoes, hi_amt=0.25)
    # arms behind torso
    ic.part(lambda c: c.ellipse(11.5, 26, 3.0, 4.6, '#fff'), top)
    ic.part(lambda c: c.ellipse(27.5, 26, 3.0, 4.6, '#fff'), top)
    if robe:
        ic.part(lambda c: c.poly([(13, 21), (26, 21), (29, 36), (10, 36)], '#fff'), top)
    else:
        ic.part(lambda c: c.ellipse(19.5, 26.5, 7.2, 5.6, '#fff'), top)
    if top2:
        ic.raw(lambda c: c.rect(17, 22, 22, 30 if not robe else 35, top2))
    # hands
    ic.part(lambda c: c.circle(10.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)


def head(ic, skin=SKIN, ears=True):
    if ears:
        ic.part(lambda c: (c.circle(10.5, 14.5, 2.0, '#fff')), skin, sh=SKIN_SH)
        ic.part(lambda c: (c.circle(28.5, 14.5, 2.0, '#fff')), skin, sh=SKIN_SH)
    ic.part(lambda c: c.ellipse(19.5, 12.8, 8.6, 8.3, '#fff'), skin, sh=SKIN_SH, hi=lighten(skin, 0.3))


def face(ic, eyes='open', mouth='smile', blush=True, y=13):
    def d(c):
        if eyes == 'open':
            for ex in (15, 22):
                c.rect(ex, y, ex + 1, y + 2, '#1b1420')
                c.px(ex, y, '#ffffff')
        elif eyes == 'closed':
            for ex in (15, 22):
                c.px(ex - 1, y + 1, '#1b1420'); c.px(ex, y + 2, '#1b1420'); c.px(ex + 1, y + 2, '#1b1420'); c.px(ex + 2, y + 1, '#1b1420')
        elif eyes == 'determined':
            for ex in (15, 22):
                c.rect(ex, y + 1, ex + 1, y + 2, '#1b1420')
                c.px(ex + (1 if ex < 19 else 0), y + 1, '#ffffff')
            c.line(14, y - 1, 17, y, '#1b1420')
            c.line(21, y, 24, y - 1, '#1b1420')
        if blush:
            c.px(13, y + 4, '#ff9aa8'); c.px(14, y + 4, '#ff9aa8')
            c.px(25, y + 4, '#ff9aa8'); c.px(26, y + 4, '#ff9aa8')
        if mouth == 'smile':
            c.px(18, y + 4, '#7a2a1a'); c.px(19, y + 5, '#7a2a1a'); c.px(20, y + 5, '#7a2a1a'); c.px(21, y + 4, '#7a2a1a')
        elif mouth == 'grin':
            c.rect(18, y + 4, 21, y + 5, '#7a2a1a'); c.rect(18, y + 4, 21, y + 4, '#ffffff')
        elif mouth == 'o':
            c.rect(19, y + 4, 20, y + 5, '#7a2a1a')
        elif mouth == 'flat':
            c.rect(18, y + 5, 21, y + 5, '#7a2a1a')
    ic.raw(d)


# ------------------------------------------------------------------ roles
def mechanic():
    ic = Icon(40)
    # big wrench behind the right side
    body(ic, '#ff8a1f', pants='#ff8a1f', shoes='#3a2a1a')
    # overall straps + pocket
    ic.raw(lambda c: (c.rect(15, 21, 15, 26, '#b85a10'), c.rect(24, 21, 24, 26, '#b85a10'),
                      c.rect(17, 25, 22, 28, '#e87414'), c.px(15, 22, '#ffd23a'), c.px(24, 22, '#ffd23a'),
                      c.rect(18, 21, 21, 23, '#5a7aa8')))
    head(ic)
    # cap (blue) with bill
    ic.part(lambda c: (c.ellipse(19.5, 7.8, 8.8, 4.3, '#fff'), c.rect(11, 8, 28, 10, '#fff')), '#3a5ab8')
    ic.part(lambda c: c.rect(20, 9, 30, 11, '#fff'), '#2a3a8a')
    ic.raw(lambda c: (c.rect(18, 5, 20, 6, '#ffd23a')))
    face(ic, eyes='open', mouth='grin', y=13)
    ic.raw(lambda c: (c.px(25, 17, '#7a6a5a'), c.px(26, 18, '#7a6a5a'), c.px(24, 18, '#7a6a5a')))  # grease smudge
    # wrench in the right hand
    ic.part(lambda c: c.line(29, 31, 36, 16, '#fff', w=3), '#b8c0cc', hi='#ffffff', sh='#6a7282')
    ic.part(lambda c: (c.circle(36.5, 14.5, 3.6, '#fff')), '#b8c0cc', hi='#ffffff', sh='#6a7282')
    ic.raw(lambda c: (c.rect(36, 10, 37, 14, (0, 0, 0, 0)), c.px(36, 15, '#4a5262')))
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    return ic


def banker():
    ic = Icon(40)
    # money bag on the left
    body(ic, '#2a3456', top2=None, pants='#232a46', shoes='#141018')
    ic.raw(lambda c: (c.poly([(17, 21), (22, 21), (19.5, 26)], '#ffffff'), c.rect(19, 22, 20, 27, '#d81a2a'),
                      c.px(19, 21, '#ffffff'), c.px(20, 21, '#ffffff'), c.px(14, 24, '#ffd23a'), c.px(25, 24, '#ffd23a')))
    head(ic)
    # monocle + moustache
    face(ic, eyes='open', mouth='flat', y=13)
    ic.raw(lambda c: (c.ellipse(23.0, 14.0, 2.6, 2.6, '#ffd23a', fill=False), c.line(25, 16, 26, 20, '#ffd23a'),
                      c.rect(16, 17, 23, 17, '#5a3a24'), c.px(15, 18, '#5a3a24'), c.px(24, 18, '#5a3a24')))
    # top hat
    ic.part(lambda c: c.rect(12, 6, 27, 7, '#fff'), '#1b1b24', hi='#4a4a5a')
    ic.part(lambda c: c.rect(14, -2, 25, 6, '#fff'), '#1b1b24', hi='#4a4a5a')
    ic.raw(lambda c: c.rect(15, 4, 24, 5, '#d8a82a'))
    # money bag in left hand
    ic.part(lambda c: (c.ellipse(6.5, 32.0, 5.6, 5.4, '#fff'), c.poly([(4, 26), (9, 26), (8, 28), (5, 28)], '#fff')),
            '#d8b878', sh='#9a7a3a')
    ic.raw(lambda c: (c.rect(4, 27, 9, 27, '#7a5a2a'), c.rect(6, 30, 6, 35, '#3a7a2a'), c.rect(5, 31, 7, 31, '#3a7a2a'),
                      c.rect(5, 33, 7, 33, '#3a7a2a')))
    ic.part(lambda c: c.circle(10.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    # coins
    ic.part(lambda c: c.ellipse(33.5, 34.5, 3.4, 1.8, '#fff'), '#ffd23a', sh='#b8860b')
    ic.part(lambda c: c.ellipse(33.5, 32.5, 3.4, 1.8, '#fff'), '#ffd23a', sh='#b8860b')
    return ic


def janitor():
    ic = Icon(40)
    # broom behind
    ic.part(lambda c: c.line(31, 4, 25, 33, '#fff', w=2), '#a8642a', hi='#d89a5a', sh='#5a3414')
    body(ic, '#8a96a8', pants='#5a6272', shoes='#2a2a30')
    ic.raw(lambda c: (c.rect(13, 24, 26, 24, '#5a6272'), c.rect(21, 22, 23, 23, '#e8e8f0'), c.px(16, 27, '#e8e8f0')))
    head(ic)
    face(ic, eyes='open', mouth='smile', y=13)
    # cap
    ic.part(lambda c: (c.ellipse(19.5, 7.8, 8.8, 4.3, '#fff'), c.rect(11, 8, 28, 10, '#fff')), '#6a7686')
    ic.part(lambda c: c.rect(7, 9, 16, 10, '#fff'), '#4a5464')
    # broom head in front at the bottom right
    ic.part(lambda c: c.poly([(21, 32), (29, 32), (31, 39), (19, 39)], '#fff'), '#f2c84a', sh='#b8901a')
    ic.raw(lambda c: (c.line(22, 34, 21, 38, '#b8901a'), c.line(25, 34, 25, 38, '#b8901a'), c.line(28, 34, 29, 38, '#b8901a'),
                      c.rect(21, 32, 29, 32, '#c83a2a')))
    ic.part(lambda c: c.circle(28.5, 28.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    # bubbles
    for (x, y, r) in ((5, 10, 2.4), (8, 5, 1.6), (4, 18, 1.4)):
        ic.part(lambda c, x=x, y=y, r=r: c.circle(x, y, r, '#fff'), '#b8ecff', hi='#ffffff', sh='#6ab8e8')
    return ic


def mage():
    ic = Icon(40)
    # staff behind on the right with glowing orb
    ic.part(lambda c: c.line(31, 36, 33, 9, '#fff', w=2), '#7a4a2a', hi='#a8743a', sh='#3a2010')
    ic.part(lambda c: c.circle(33.5, 6.5, 4.0, '#fff'), '#5affff', hi='#ffffff', sh='#1e9ac0')
    body(ic, '#7a3ac8', robe=True)
    ic.raw(lambda c: (c.rect(18, 22, 21, 35, '#5a28a0'), c.px(19, 26, '#ffd23a'), c.px(20, 30, '#ffd23a'),
                      c.rect(12, 33, 27, 33, '#ffd23a')))
    head(ic)
    # beard
    ic.part(lambda c: c.poly([(12, 15), (27, 15), (25, 22), (19.5, 26), (14, 22)], '#fff'), '#f2f2f8', sh='#b8b8cc')
    ic.raw(lambda c: (c.rect(17, 16, 22, 16, '#d8d8e8')))
    face(ic, eyes='open', mouth=None, blush=False, y=11)
    # hat
    ic.part(lambda c: c.poly([(9, 9), (30, 9), (22, -2), (19, -4)], '#fff'), '#7a3ac8', hi='#a86aff', sh='#4a1a8a')
    ic.part(lambda c: c.ellipse(19.5, 9.0, 11.0, 2.4, '#fff'), '#5a28a0', hi='#8a5ae0')
    ic.raw(lambda c: (c.px(18, 3, '#ffd23a'), c.px(22, 5, '#ffd23a'), c.px(17, 6, '#ffffff')))
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    sparkle(ic, 37, 12, 1)
    sparkle(ic, 29, 2, 1)
    return ic


def chef():
    ic = Icon(40)
    body(ic, '#f4f4f8', pants='#3a3a4a', shoes='#1b1b20')
    ic.raw(lambda c: (c.poly([(16, 21), (23, 21), (19.5, 24)], '#e8261c'), c.px(17, 25, '#3a3a4a'), c.px(17, 28, '#3a3a4a'),
                      c.px(22, 25, '#3a3a4a'), c.px(22, 28, '#3a3a4a')))
    head(ic)
    face(ic, eyes='closed', mouth='smile', y=13)
    ic.raw(lambda c: (c.rect(16, 17, 23, 17, '#5a3a24'), c.px(15, 16, '#5a3a24'), c.px(24, 16, '#5a3a24')))
    # chef toque
    ic.part(lambda c: c.rect(12, 5, 27, 8, '#fff'), '#ffffff', sh='#c8ccd8')
    ic.part(lambda c: (c.circle(14.5, 1.5, 4.5, '#fff'), c.circle(19.5, -0.5, 5.5, '#fff'), c.circle(24.5, 1.5, 4.5, '#fff'),
                       c.rect(12, 1, 27, 5, '#fff')), '#ffffff', sh='#c8ccd8')
    ic.raw(lambda c: (c.line(16, 1, 16, 5, '#d8dce8'), c.line(23, 1, 23, 5, '#d8dce8')))
    # wooden spoon in the right hand
    ic.part(lambda c: c.line(29, 31, 35, 14, '#fff', w=2), '#c8904a', hi='#f0c080', sh='#7a5020')
    ic.part(lambda c: c.ellipse(35.5, 11.5, 2.8, 4.2, '#fff'), '#c8904a', hi='#f0c080', sh='#7a5020')
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    # steam
    ic.raw(lambda c: (c.px(4, 14, '#ffffff'), c.px(5, 13, '#ffffff'), c.px(4, 12, '#ffffff'), c.px(5, 11, '#ffffff'),
                      c.px(7, 18, '#d8dce8'), c.px(8, 17, '#d8dce8'), c.px(7, 16, '#d8dce8')))
    return ic


def scientist():
    ic = Icon(40)
    body(ic, '#f4f6fa', pants='#3a4a6a', shoes='#1b1b20')
    ic.raw(lambda c: (c.rect(19, 21, 20, 31, '#c8ccd8'), c.rect(14, 26, 16, 27, '#5a8ad8'), c.px(14, 25, '#e8261c')))
    head(ic)
    # wild hair
    ic.part(lambda c: (c.circle(11, 8, 3.2, '#fff'), c.circle(14, 4, 3.4, '#fff'), c.circle(19.5, 3, 3.6, '#fff'),
                       c.circle(25, 4, 3.4, '#fff'), c.circle(28, 8, 3.2, '#fff')), '#e8ecf4', sh='#a8acbc')
    face(ic, eyes='open', mouth='o', y=14)
    # goggles on the forehead
    ic.part(lambda c: (c.circle(15.5, 9.5, 2.8, '#fff'), c.circle(23.5, 9.5, 2.8, '#fff'), c.rect(10, 9, 29, 10, '#fff')),
            '#5a5e6c', hi='#8a8e9c')
    ic.raw(lambda c: (c.circle(15.5, 9.5, 1.6, '#5ae8ff'), c.circle(23.5, 9.5, 1.6, '#5ae8ff'), c.px(14, 8, '#ffffff'), c.px(22, 8, '#ffffff')))
    # flask in the right hand
    ic.part(lambda c: (c.rect(31, 15, 34, 21, '#fff'), c.ellipse(32.5, 26.5, 5.4, 5.6, '#fff')), '#d8f4ff', hi='#ffffff', sh='#8ab8d0')
    ic.raw(lambda c: (c.ellipse(32.5, 27.5, 4.2, 3.8, '#4fe040'), c.px(31, 26, '#c8ffb8'), c.px(33, 28, '#2a9a1a'),
                      c.rect(31, 14, 34, 15, '#a8642a')))
    for (x, y, r) in ((30, 10, 1.4), (34, 7, 1.8), (31, 4, 1.2)):
        ic.part(lambda c, x=x, y=y, r=r: c.circle(x, y, r, '#fff'), '#7aff5a', sh='#2a9a1a')
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    return ic


def merchant():
    ic = Icon(40)
    body(ic, '#2e8a4a', top2='#f2e6c8', pants='#6a3a8a', shoes='#3a2010')
    ic.raw(lambda c: (c.rect(13, 27, 26, 28, '#d8a82a'), c.px(19, 27, '#e8261c')))
    head(ic, skin='#e0a870')
    face(ic, eyes='open', mouth='smile', y=13)
    ic.raw(lambda c: (c.rect(16, 17, 23, 17, '#3a2010'), c.px(15, 18, '#3a2010'), c.px(24, 18, '#3a2010')))
    # turban
    ic.part(lambda c: (c.ellipse(19.5, 6.5, 10.0, 5.6, '#fff')), '#e8501a', hi='#ff9a5a', sh='#a82a0a')
    ic.raw(lambda c: (c.line(11, 7, 27, 4, '#c03a10'), c.line(12, 10, 28, 7, '#c03a10')))
    ic.part(lambda c: c.ellipse(19.5, 7.5, 2.0, 2.4, '#fff'), '#3ad8ff', hi='#ffffff', sh='#1a7aa8')
    ic.raw(lambda c: (c.px(19, 2, '#ffd23a'), c.px(19, 1, '#ffffff')))
    # golden balance scale held up in the right hand
    ic.part(lambda c: c.rect(32, 10, 33, 31, '#fff'), '#d8a82a', hi='#fff0a0', sh='#8a5a08')
    ic.part(lambda c: c.rect(26, 10, 39, 11, '#fff'), '#d8a82a', hi='#fff0a0', sh='#8a5a08')
    ic.raw(lambda c: (c.line(27, 12, 26, 17, '#8a5a08'), c.line(27, 12, 29, 17, '#8a5a08'),
                      c.line(38, 12, 36, 15, '#8a5a08'), c.line(38, 12, 39, 15, '#8a5a08')))
    ic.part(lambda c: c.ellipse(27.5, 18.0, 3.4, 1.6, '#fff'), '#d8a82a', hi='#fff0a0', sh='#8a5a08')
    ic.part(lambda c: c.ellipse(37.5, 16.0, 3.0, 1.6, '#fff'), '#d8a82a', hi='#fff0a0', sh='#8a5a08')
    ic.part(lambda c: c.circle(37.5, 13.5, 1.6, '#fff'), '#ffd23a', sh='#b8860b')
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), '#e0a870', sh='#b07840')
    ic.part(lambda c: c.circle(10.5, 30.5, 2.2, '#fff'), '#e0a870', sh='#b07840')
    return ic


def dj():
    ic = Icon(40)
    body(ic, '#2a2a3a', pants='#1b1b24', shoes='#ff3a8a')
    head(ic)
    face(ic, eyes='closed', mouth='grin', y=13)
    # cap backwards
    ic.part(lambda c: (c.ellipse(19.5, 7.5, 8.8, 4.8, '#fff')), '#ff3a8a', hi='#ff8ac0', sh='#a8105a')
    ic.part(lambda c: c.rect(7, 7, 12, 9, '#fff'), '#c81a6a')
    # big headphones
    ic.part(lambda c: c.ellipse(19.5, 6.0, 10.6, 6.0, '#fff', fill=False), '#2a2a34', hi='#5a5a6a')
    ic.part(lambda c: c.ellipse(9.5, 14.0, 3.0, 4.2, '#fff'), '#2a2a34', hi='#5a5a6a')
    ic.part(lambda c: c.ellipse(29.5, 14.0, 3.0, 4.2, '#fff'), '#2a2a34', hi='#5a5a6a')
    ic.raw(lambda c: (c.ellipse(9.5, 14.0, 1.6, 2.6, '#5affff'), c.ellipse(29.5, 14.0, 1.6, 2.6, '#5affff')))
    # turntable deck in front
    ic.part(lambda c: c.rect(2, 28, 37, 38, '#fff'), '#4a4a5a', hi='#7a7a8c', sh='#2a2a34')
    ic.part(lambda c: c.ellipse(12.5, 32.5, 8.0, 3.6, '#fff'), '#14141a', hi='#3a3a48')
    ic.raw(lambda c: (c.ellipse(12.5, 32.5, 5.4, 2.2, '#2a2a34', fill=False), c.ellipse(12.5, 32.5, 1.8, 1.0, '#ff3a3a'),
                      c.rect(24, 31, 26, 31, '#5affff'), c.rect(28, 31, 30, 31, '#ff3a8a'), c.rect(32, 31, 34, 31, '#ffd23a'),
                      c.rect(25, 34, 34, 35, '#2a2a34'), c.rect(27, 34, 28, 35, '#c8ccd8')))
    ic.part(lambda c: c.circle(10.5, 27.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    ic.part(lambda c: c.circle(28.5, 27.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    # music notes
    ic.raw(lambda c: (c.rect(35, 4, 35, 9, '#ffd23a'), c.rect(33, 9, 35, 10, '#ffd23a'), c.rect(36, 4, 37, 5, '#ffd23a'),
                      c.rect(3, 6, 3, 10, '#5affff'), c.rect(1, 10, 3, 11, '#5affff'), c.px(4, 6, '#5affff')))
    return ic


def miner():
    ic = Icon(40)
    # pickaxe behind on the right
    ic.part(lambda c: c.line(26, 34, 34, 12, '#fff', w=2), '#a8642a', hi='#d89a5a', sh='#5a3414')
    ic.part(lambda c: (c.poly([(26, 13), (31, 10), (38, 10), (39, 13), (36, 12), (31, 13), (28, 15)], '#fff')),
            '#b8c0cc', hi='#ffffff', sh='#5a6272')
    body(ic, '#c86a2a', top2=None, pants='#3a4a6a', shoes='#2a1e1e')
    ic.raw(lambda c: (c.rect(13, 25, 26, 26, '#ffd23a'), c.rect(13, 25, 13, 25, '#ffffff')))
    head(ic)
    face(ic, eyes='determined', mouth='smile', y=13)
    ic.raw(lambda c: (c.px(13, 18, '#6a5a4a'), c.px(14, 19, '#6a5a4a'), c.px(25, 11, '#6a5a4a')))
    # helmet with lamp
    ic.part(lambda c: (c.ellipse(19.5, 7.4, 9.4, 5.0, '#fff'), c.rect(9, 8, 30, 10, '#fff')), '#ffd23a', hi='#fff6b0', sh='#c8901a')
    ic.part(lambda c: c.rect(8, 9, 31, 10, '#fff'), '#e8b01c', sh='#a87008')
    ic.part(lambda c: c.rect(17, 3, 22, 7, '#fff'), '#5a5e6c', hi='#8a8e9c')
    ic.part(lambda c: c.rect(18, 4, 21, 6, '#fff'), '#fff6a0', hi='#ffffff', outline=None)
    # light beam
    ic.raw(lambda c: (c.line(17, 2, 10, -3, '#fff6c0'), c.line(22, 2, 28, -3, '#fff6c0'), c.line(19, 1, 19, -3, '#fff6c0')))
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    return ic


def monk():
    ic = Icon(40)
    body(ic, '#8a5a2a', robe=True)
    ic.raw(lambda c: (c.rect(13, 28, 26, 29, '#d8b878'), c.px(25, 30, '#d8b878'), c.px(25, 31, '#d8b878')))
    # hood behind the head
    ic.part(lambda c: c.ellipse(19.5, 15.5, 11.4, 9.4, '#fff'), '#7a4a20', hi='#a8743a', sh='#4a2a10')
    head(ic, ears=False)
    face(ic, eyes='closed', mouth='smile', y=14)
    # tonsure: bald top with a ring of hair
    ic.raw(lambda c: (c.rect(12, 9, 13, 11, '#5a3414'), c.rect(26, 9, 27, 11, '#5a3414'), c.px(17, 6, '#ffffff'), c.px(18, 6, '#ffe8d0')))
    # prayer beads hanging from the hands
    beads = [(10, 31), (11, 33), (13, 34), (15, 35), (17, 36), (19.5, 36.5), (22, 36), (24, 35), (26, 34), (28, 33), (29, 31)]
    for (x, y) in beads:
        ic.part(lambda c, x=x, y=y: c.circle(x + 0.5, y + 0.5, 1.4, '#fff'), '#c8402a', hi='#ff8a6a', sh='#7a1a0a')
    ic.part(lambda c: c.circle(19.8, 38.0, 1.8, '#fff'), '#ffd23a', sh='#b8860b')
    ic.part(lambda c: c.circle(10.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    ic.part(lambda c: c.circle(28.5, 30.5, 2.2, '#fff'), SKIN, sh=SKIN_SH)
    # calm aura
    sparkle(ic, 4, 8, 1, '#fff6b0', '#ffd23a')
    sparkle(ic, 35, 6, 1, '#fff6b0', '#ffd23a')
    return ic


ROLES = [('mechanic', mechanic), ('banker', banker), ('janitor', janitor), ('mage', mage), ('chef', chef),
         ('scientist', scientist), ('merchant', merchant), ('dj', dj), ('miner', miner), ('monk', monk)]


def main():
    items = []
    for name, fn in ROLES:
        ic = fn()
        im = to_png(ic.a, SC, os.path.join(OUT, name + '.png'))
        items.append((name, im))
    sheet = contact_sheet(items, (160, 160), 5, label_h=14, bg=(30, 40, 52, 255))
    sheet.save(os.path.join(OUT, 'contact_sheet.png'))
    small = [(n, im.resize((90, 90), Image.LANCZOS)) for n, im in items]
    contact_sheet(small, (90, 90), 10, label_h=14, bg=(30, 40, 52, 255)).save(os.path.join(REPO, "tools", "art", "_preview", "staff_90.png"))
    print('ok')


if __name__ == '__main__':
    main()
