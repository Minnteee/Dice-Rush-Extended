"""Review helper: render every dice icon big on the face colour of the first die using it."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pix import contact_sheet, to_img, pad, hexc
import dice_icons
import gen_dice
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

cat = json.load(open(gen_dice.CATALOG, encoding='utf-8'))
uses = {}
for d in cat['dice']:
    for f, g in enumerate(d['art']['glyphs']):
        k, v = g.split(':', 1)
        if k == 'icon' and v not in uses:
            uses[v] = (d, f)
names = sys.argv[1:] or list(uses.keys())
items = []
for n in names:
    d, f = uses[n]
    face = [d['art']['top'], d['art']['left'], d['art']['right']][f]
    oc = gen_dice.glyph_outline(face, d['art']['outline'], d['art']['edge'])
    spr = gen_dice.icon_sprite(n, d['art']['ink'], face, oc)
    bg = np.zeros((24, 24, 4), np.uint8)
    bg[:, :] = hexc(face)
    h, w = spr.shape[:2]
    x0, y0 = (24 - w) // 2, (24 - h) // 2
    m = spr[:, :, 3] > 0
    sub = bg[y0:y0 + h, x0:x0 + w]
    sub[m] = spr[m]
    items.append((n, to_img(bg, 6)))
sheet = contact_sheet(items, (120, 120), 12, label_h=14, bg=(30, 30, 36, 255))
out = os.path.join(REPO, "tools", "art", "_preview", "icons_review.png")
sheet.save(out)
print(len(items), out)

