"""Dice Shaker - Area 1 'scene' art generator.

Run:  tools\\venv\\Scripts\\python.exe tools\\shaker_art\\gen_scene.py
Writes build/generated/shaker/art/scene/*.png + layout.json + tables.json and
the composed previews (_preview_scene.png 960x540, _preview_scene_1080.png,
_preview_designs.png contact sheet).  Deterministic (seeded hashes only).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'build', 'generated', 'shaker', 'art', 'scene')
BG = os.path.join(REPO, 'work', 'recovered', 'assets', 'art', 'фон.png')

from scene_lib import alpha_over, save, to_img, hexc, flip_h            # noqa: E402
import scene_table as st                                                 # noqa: E402
import scene_cloth as sc                                                 # noqa: E402
import scene_designs as sd                                               # noqa: E402
import scene_ball as sb                                                  # noqa: E402
import scene_hands as sh                                                 # noqa: E402
import scene_props as sp                                                 # noqa: E402

NATIVE = (480, 270)
HAND_L = (56, 62)
HAND_R = (312, 62)
MACHINE = (18, 70)
CANDLES = [(392, 160, 'candle'), (414, 180, 'candle_short')]
FLAME_OFF = (4, -14)


def layout():
    mx, my = MACHINE
    return {
        "native": [480, 270], "scale": 4,
        "table": [0, 170, 480, 100],
        "cloth": [0, 170, 480, 100],
        "cushion": [156, 170, 168, 52],
        "stand": [sb.STAND_X, sb.STAND_Y, sb.STAND_W, sb.STAND_H],
        "ball": [sb.BALL_X, sb.BALL_Y, sb.BALL_S, sb.BALL_S],
        "ball_inner": {"center": [240, 108], "radius": 56},
        "dice_floor": {"center": [240, 148], "rx": 40, "ry": 8},
        "hand_left": [HAND_L[0], HAND_L[1], sh.W, sh.H],
        "hand_right": [HAND_R[0], HAND_R[1], sh.W, sh.H],
        "gumball_machine": [mx, my, sp.MW, sp.MH],
        "gumball_chute": [int(round(mx + sp.CHUTE[0])), int(math.floor(my + sp.CHUTE[1] + 2))],
        "gumball_slot": [int(math.floor(mx + sp.SLOT[0] + 1.5)), int(math.floor(my + (sp.SLOT[1] + sp.SLOT[3]) / 2))],
        "gumball_crank": [int(round(mx + sp.CRANK_C[0])), int(round(my + sp.CRANK_C[1]))],
        "gumball_globe": {"center": [int(round(mx + sp.GLOBE_C[0])), int(round(my + sp.GLOBE_C[1]))],
                          "radius": int(sp.GLOBE_R)},
        "candles": [[x, y] for (x, y, _) in CANDLES],
        "candle_sprites": [n for (_, _, n) in CANDLES],
        "flame_offset": list(FLAME_OFF),
        "draw_order": ["background", "hand_left", "hand_right", "table", "cloth", "gumball_machine",
                       "gumball_crank", "candles", "flames", "cushion", "ball_back", "dice",
                       "ball_front", "stand"],
    }


def placeholder_die(n=13):
    d = np.zeros((n, n, 4), np.uint8)
    d[...] = (240, 236, 228, 255)
    d[0, :] = d[-1, :] = d[:, 0] = d[:, -1] = (30, 20, 30, 255)
    d[1:-1, -2] = (200, 190, 190, 255)
    d[-2, 1:-1] = (200, 190, 190, 255)
    for (px, py) in ((3, 3), (6, 6), (9, 9)):
        d[py:py + 2, px:px + 2] = (40, 20, 40, 255)
    return d


def compose(parts, design_id=0, hands_frame='', crank=0, flame=0, dice=True, bg=None):
    canvas = np.zeros((NATIVE[1], NATIVE[0], 4), np.uint8)
    if bg is not None:
        canvas[...] = bg
    alpha_over(canvas, parts['hand_left' + hands_frame], *HAND_L)
    alpha_over(canvas, parts['hand_right' + hands_frame], *HAND_R)
    alpha_over(canvas, parts['table'], 0, 170)
    alpha_over(canvas, parts['cloth_%d' % design_id], 0, 170)
    alpha_over(canvas, parts['gumball_machine'], *MACHINE)
    alpha_over(canvas, parts['gumball_crank_%d' % crank], *MACHINE)
    for (x, y, name) in CANDLES:
        alpha_over(canvas, parts[name], x, y)
        alpha_over(canvas, parts['flame_%d' % flame], x + FLAME_OFF[0], y + FLAME_OFF[1])
    alpha_over(canvas, parts['cushion_%d' % design_id], 156, 170)
    alpha_over(canvas, parts['ball_back'], sb.BALL_X, sb.BALL_Y)
    if dice:
        for (x, y) in ((217, 135), (246, 138), (233, 92)):
            alpha_over(canvas, placeholder_die(), x, y)
    alpha_over(canvas, parts['ball_front'], sb.BALL_X, sb.BALL_Y)
    alpha_over(canvas, parts['stand'], sb.STAND_X, sb.STAND_Y)
    return canvas


def render_all(designs=None):
    parts = {}
    g = st.scene_geo()
    parts['table'] = st.render_table(g)
    ids = range(len(sd.DESIGNS)) if designs is None else designs
    for i in ids:
        parts['cloth_%d' % i] = sc.render_cloth(sd.DESIGNS[i], g, parts['table'], seed=i)
        parts['cushion_%d' % i] = sc.render_cushion(sd.DESIGNS[i], seed=i)
    stand, thru = sb.render_stand()
    parts['stand'] = stand
    parts['ball_back'], parts['ball_front'] = sb.render_ball(thru)
    parts.update(sh.render_hands())
    parts['gumball_machine'] = sp.render_gumball_machine()
    for k in range(4):
        parts['gumball_crank_%d' % k] = sp.render_crank(k)
    for k, c in enumerate(sp.BALL_COLOURS):
        parts['gumball_ball_%d' % k] = sp.render_gum_ball(c)
    parts['coin'] = sp.render_coin()
    parts['candle'] = sp.render_candle(31)
    parts['candle_short'] = sp.render_candle(21)
    for k in range(3):
        parts['flame_%d' % k] = sp.render_flame(k)
    return parts


def background(size):
    return np.array(Image.open(BG).convert('RGBA').resize(size, Image.BILINEAR))


def main(quick=False):
    os.makedirs(OUT, exist_ok=True)
    parts = render_all([0] if quick else None)
    for name, a in parts.items():
        save(a, os.path.join(OUT, name + '.png'))
    # shop thumbnails (96x64, opaque)
    for i in (range(len(sd.DESIGNS)) if not quick else [0]):
        save(sc.render_thumb(sd.DESIGNS[i], seed=i), os.path.join(OUT, 'table_%d_thumb.png' % i))
    # json
    lay = layout()
    with open(os.path.join(OUT, 'layout.json'), 'w', encoding='utf-8') as f:
        f.write('{\n' + ',\n'.join(' %s: %s' % (json.dumps(k), json.dumps(v)) for k, v in lay.items()) + '\n}\n')
    tables = [{"id": i, "name_en": d['name_en'], "name_de": d['name_de']} for i, d in enumerate(sd.DESIGNS)]
    with open(os.path.join(OUT, 'tables.json'), 'w', encoding='utf-8') as f:
        json.dump(tables, f, indent=1, ensure_ascii=False)
    # previews: native composite scaled up with NEAREST over the (smoothly scaled) game background
    for (scale, name) in ((2, '_preview_scene.png'), (4, '_preview_scene_1080.png')):
        size = (NATIVE[0] * scale, NATIVE[1] * scale)
        bgbig = Image.open(BG).convert('RGBA').resize(size, Image.BILINEAR)
        comp = compose(parts, 0)
        big = to_img(comp, scale)
        out = bgbig.copy()
        out.alpha_composite(big)
        out.convert('RGB').save(os.path.join(OUT, name))
    if not quick:
        design_sheets(parts)
    print('wrote', len(parts), 'sprites to', OUT)
    return parts


def label_font(size=14):
    try:
        return ImageFont.truetype('arial.ttf', size)
    except Exception:
        return ImageFont.load_default()


def design_sheets(parts):
    """_preview_designs.png: every design in the scene (crop, 2x);
    _preview_thumbs.png: the 20 shop thumbnails (3x)."""
    bg = background(NATIVE)
    n = len(sd.DESIGNS)
    cols = 4
    cw, ch = 300, 116                    # native crop size
    sx0, sy0 = 90, 154
    sc_ = 2
    lab = 22
    rows = (n + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (cw * sc_ + 8) + 8, rows * (ch * sc_ + lab + 8) + 8), (24, 18, 30))
    d = ImageDraw.Draw(sheet)
    fnt = label_font(15)
    for i in range(n):
        comp = compose(parts, i, dice=False, bg=bg)
        crop = to_img(comp[sy0:sy0 + ch, sx0:sx0 + cw], sc_)
        r, c = divmod(i, cols)
        x = 8 + c * (cw * sc_ + 8)
        y = 8 + r * (ch * sc_ + lab + 8)
        sheet.paste(crop.convert('RGB'), (x, y + lab))
        d.text((x + 2, y + 2), '%d  %s / %s' % (i, sd.DESIGNS[i]['name_en'], sd.DESIGNS[i]['name_de']),
               fill=(236, 226, 210), font=fnt)
    sheet.save(os.path.join(OUT, '_preview_designs.png'))
    # thumbnails
    tsc = 3
    tw, th = 96 * tsc, 64 * tsc
    cols = 5
    rows = (n + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (tw + 8) + 8, rows * (th + lab + 8) + 8), (24, 18, 30))
    d = ImageDraw.Draw(sheet)
    for i in range(n):
        im = Image.open(os.path.join(OUT, 'table_%d_thumb.png' % i)).convert('RGB').resize((tw, th), Image.NEAREST)
        r, c = divmod(i, cols)
        x = 8 + c * (tw + 8)
        y = 8 + r * (th + lab + 8)
        sheet.paste(im, (x, y + lab))
        d.text((x + 2, y + 2), '%d  %s' % (i, sd.DESIGNS[i]['name_en']), fill=(236, 226, 210), font=fnt)
    sheet.save(os.path.join(OUT, '_preview_thumbs.png'))


if __name__ == '__main__':
    main(quick='--quick' in sys.argv)
