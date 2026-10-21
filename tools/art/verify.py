"""Sanity checks for all generated art: sizes, RGBA, hard alpha, stray pixels, landmarks, hotspots."""
import glob
import json
import os
import sys
from collections import deque

import numpy as np
from PIL import Image
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

ROOT = os.path.join(REPO, "build", "generated", "bdr", "art")

EXPECT = {
    'dice/*.png': (256, 256),
    'tarot/m_*.png': (51, 79),
    'cursors/cursor_*.png': (128, 128),
    'boards/board_?.png': (1448, 1086),
    'boards/board_10.png': (1448, 1086),
    'boards/board_*_thumb.png': (290, 218),
    'staff/*.png': (160, 160),
}
SPECIFIC = {
    'events/coin.png': (64, 64), 'events/meteor.png': (64, 64), 'events/tornado_sprite.png': (128, 160),
    'events/cat_walk.png': (96, 64), 'events/thief_run.png': (96, 96), 'events/chest_closed.png': (128, 128),
    'events/chest_open.png': (128, 128), 'events/clover.png': (96, 96),
    'ui/p1_cursor.png': (48, 48), 'ui/p2_cursor.png': (48, 48),
}
for n in ['meteor_shower', 'coin_rain', 'tornado', 'happy_hour', 'rainbow', 'black_cat', 'treasure_chest', 'thief', 'lucky_clover']:
    SPECIFIC['events/%s.png' % n] = (160, 160)
for n in ['shop_icon', 'unlock_icon', 'design_icon', 'coop_icon', 'host_icon', 'join_icon', 'invite_icon']:
    SPECIFIC['ui/%s.png' % n] = (160, 160)
for n in ['lucky_cash', 'lucky_free', 'lucky_boost', 'lucky_unlock', 'sell_icon', 'event_icon']:
    SPECIFIC['ui/%s.png' % n] = (128, 128)


def components(mask, min_size=1):
    H, W = mask.shape
    seen = np.zeros_like(mask)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                n = 0
                while q:
                    cy, cx = q.popleft()
                    n += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = cy + dy, cx + dx
                            if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True
                                q.append((yy, xx))
                comps.append(n)
    return sorted(comps, reverse=True)


def check(path, size, problems, native=None):
    im = Image.open(path)
    rel = os.path.relpath(path, ROOT)
    if im.size != size:
        problems.append('%s: size %s != %s' % (rel, im.size, size))
    if im.mode != 'RGBA':
        problems.append('%s: mode %s' % (rel, im.mode))
        return
    a = np.array(im)
    al = a[:, :, 3]
    vals = set(np.unique(al).tolist())
    if not vals <= {0, 255}:
        problems.append('%s: soft alpha values %s' % (rel, sorted(vals)[:6]))
    if (a[al == 0][:, :3] != 0).any():
        problems.append('%s: RGB garbage under transparent pixels' % rel)
    return a


def main():
    problems = []
    files = []
    for pat, size in EXPECT.items():
        for p in sorted(glob.glob(os.path.join(ROOT, pat))):
            if 'contact_sheet' in p:
                continue
            if pat == 'boards/board_?.png' and p.endswith('_thumb.png'):
                continue
            files.append((p, size))
    for rel, size in SPECIFIC.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            problems.append('MISSING ' + rel)
            continue
        files.append((p, size))
    seen = set()
    for p, size in files:
        if p in seen:
            continue
        seen.add(p)
        a = check(p, size, problems)
        if a is None:
            continue
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        if rel.startswith('boards/'):
            if (a[:, :, 3] != 255).any():
                problems.append(rel + ': board not fully opaque')
            continue
        if rel.startswith('tarot/'):
            continue
        # stray pixel check on native grid
        scale = 4
        if rel.startswith('cursors/'):
            scale = 2
        if rel in ('ui/p1_cursor.png', 'ui/p2_cursor.png'):
            scale = 3
        m = a[::scale, ::scale, 3] > 0
        comps = components(m)
        small = [c for c in comps[1:] if c <= 3]
        if small:
            problems.append('%s: %d tiny detached blobs %s (main %d)' % (rel, len(small), small[:8], comps[0]))
    # dice extras
    lm = json.load(open(os.path.join(ROOT, 'dice', 'landmarks.json'), encoding='utf-8'))
    cat = json.load(open(os.path.join(REPO, "src", "bdr", "data", "dice_catalog.json"), encoding='utf-8'))
    ids = [d['id'] for d in cat['dice']]
    for i in ids:
        if i not in lm:
            problems.append('landmarks missing ' + i)
        elif len(lm[i]) != 7:
            problems.append('landmarks wrong count ' + i)
        if not os.path.exists(os.path.join(ROOT, 'dice', i + '.png')):
            problems.append('dice png missing ' + i)
    # landmark plausibility: each landmark should lie on the cube's outline (within 2px of an opaque pixel edge)
    for i in ids[:100]:
        a = np.array(Image.open(os.path.join(ROOT, 'dice', i + '.png')))
        op = a[:, :, 3] > 0
        for (x, y) in lm[i]:
            x0, x1 = max(0, x - 3), min(256, x + 3)
            y0, y1 = max(0, y - 3), min(256, y + 3)
            if not op[y0:y1, x0:x1].any():
                problems.append('%s: landmark (%d,%d) not near opaque pixels' % (i, x, y))
    # cursors hotspot inside canvas and near opaque
    cj = json.load(open(os.path.join(ROOT, 'cursors', 'cursors.json'), encoding='utf-8'))
    for k in range(1, 11):
        key = 'cursor_%d' % k
        hx, hy = cj[key]['hotspot']
        a = np.array(Image.open(os.path.join(ROOT, 'cursors', key + '.png')))
        win = a[max(0, hy - 3):hy + 4, max(0, hx - 3):hx + 4, 3]
        if not (win > 0).any():
            problems.append('%s hotspot (%d,%d) not on the cursor' % (key, hx, hy))
        if hx > 70 or hy > 70:
            problems.append('%s hotspot (%d,%d) not near the top-left' % (key, hx, hy))
    print('checked', len(seen), 'files')
    for p in problems:
        print('PROBLEM', p)
    if not problems:
        print('ALL OK')


if __name__ == '__main__':
    main()
