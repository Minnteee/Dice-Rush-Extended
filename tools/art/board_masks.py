"""Segment the original felt image (сукно.png) into felt / wood frame / brass fittings."""
import os
import numpy as np
from PIL import Image
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

SRC = os.path.join(REPO, "work", "recovered", "assets", "art", "сукно.png")
FELT_RECT = (78, 75, 1370, 1008)   # x0, y0, x1, y1 (inclusive) of the felt inside the frame


def rgb_to_hsv(a):
    a = a.astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1)
    mn = a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = ((b - r)[gm] / d[gm]) + 2
    h[bm] = ((r - g)[bm] / d[bm]) + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def load():
    a = np.array(Image.open(SRC).convert('RGB'))
    return a


def masks(a=None):
    if a is None:
        a = load()
    H, W = a.shape[:2]
    h, s, v = rgb_to_hsv(a)
    r = a[..., 0].astype(int)
    g = a[..., 1].astype(int)
    b = a[..., 2].astype(int)
    yy, xx = np.mgrid[0:H, 0:W]
    x0, y0, x1, y1 = FELT_RECT
    inrect = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
    redish = (r > 28) & (g * 100 < r * 17) & (b * 100 < r * 22)
    brass = (h >= 24) & (h <= 62) & (s > 0.42) & (v > 0.30)
    # felt = inside the rect and red, or inside and dark but not brass-adjacent
    felt = inrect & redish & ~brass
    # brass fittings: brass colour anywhere, plus everything inside the rect that is not felt
    # (outlines / shadows of the corner plates)
    plate = inrect & ~felt
    return felt, brass, plate, inrect


def dilate(m, n=1):
    m = m.copy()
    for _ in range(n):
        g = m.copy()
        g[1:, :] |= m[:-1, :]
        g[:-1, :] |= m[1:, :]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        m = g
    return m


def erode(m, n=1):
    return ~dilate(~m, n)


if __name__ == '__main__':
    a = load()
    felt, brass, plate, inrect = masks(a)
    vis = np.zeros(a.shape, np.uint8)
    vis[felt] = (200, 30, 30)
    vis[~felt & brass] = (255, 210, 40)
    vis[plate & ~brass] = (40, 200, 255)
    vis[~inrect & ~brass] = (110, 70, 30)
    out = os.path.join(REPO, "tools", "art", "_preview", "board_masks.png")
    Image.fromarray(vis).resize((724, 543), Image.NEAREST).save(out)
    Image.fromarray(vis[0:300, 0:300]).resize((600, 600), Image.NEAREST).save(out.replace('.png', '_corner.png'))
    print('felt px', felt.sum(), 'brass px', brass.sum(), 'plate px', plate.sum())
