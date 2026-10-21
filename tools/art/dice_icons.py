"""Pixel icons for dice faces (<=16x16) + special features (ears, horns, spoiler).

Palette letters: see pix.BASE_PAL.  I/J/i = die ink / ink highlight / ink shade.
Icons whose art only uses I/J/i are "mono" (tinted by the die's ink colour).
"""
import numpy as np
from pix import sprite, hexc, mix, lighten, darken, lum, outline_arr, pad, flip_h

ICONS = {}
PALS = {}


def icon(name, art, pal=None):
    ICONS[name] = art
    if pal:
        PALS[name] = pal


import dice_icon_art  # noqa: E402

dice_icon_art.register(icon)


def is_mono(name):
    art = ICONS.get(name, '')
    if callable(art):
        return name in dice_icon_art.MONO_FN
    chars = set(art) - set('. \n')
    return chars <= set('IJi')


THIN = set()


def thin_outline(name):
    return name in THIN


def get_icon(name, ink, face_col):
    if name not in ICONS:
        art = """
IIIIIIIIII
I........I
I..IIII..I
I.....I..I
I...III..I
I...I....I
I........I
I...I....I
IIIIIIIIII"""
        print('MISSING ICON', name)
        return sprite(art, ink=ink)
    a = ICONS[name]
    if callable(a):
        return a(ink, face_col)
    pal = dict(PALS.get(name, {}))
    pal['F'] = face_col
    return sprite(a, pal=pal, ink=ink)


# ------------------------------------------------------------------ specials
def special(name, die):
    """returns list of (sprite_array, x, y) in native 64x64 coordinates"""
    return dice_icon_art.special_parts(name, die)
