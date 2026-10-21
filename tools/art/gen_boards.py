"""Generate 10 board (table felt) designs, 1448x1086 like the original сукно.png.

* The frame geometry is taken pixel-for-pixel from the original: wood and brass
  fittings are recoloured with gradient maps (luminance -> material ramp), so
  the frame outline, bevels, corner plates and diamonds stay exactly in place.
* The felt keeps the same area. It is rebuilt on a 4px native grid (362x272)
  from the original felt's luminance (noise + inner shadow), a theme pattern and
  ordered dithering into a 6-step ramp, then upscaled with NEAREST.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import hexc, hash2, value_noise, contact_sheet, OUT_ROOT
from board_masks import load, masks, dilate
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

OUT = os.path.join(OUT_ROOT, 'boards')
G = 4  # native pixel size of the felt texture
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0

# corner plates and diamonds (regions where brass colour means metal fitting)
FIT_BOXES = [(0, 0, 180, 180), (1268, 0, 1448, 180), (0, 906, 180, 1086), (1268, 906, 1448, 1086),
             (680, 0, 770, 80), (680, 1006, 770, 1086), (0, 498, 80, 590), (1368, 498, 1448, 590)]

THEMES = [
    dict(name='Emerald Casino', frame=['#0e0806', '#24140a', '#3e2414', '#5a361e', '#7a4c2a', '#9c6638'],
         metal=['#2a1404', '#6a3e08', '#b07a14', '#e0a82a', '#ffd860', '#fff4c0'],
         felt=['#032414', '#06321c', '#0a4426', '#0e5530', '#136a3c', '#1a7e48'], pat='casino'),
    dict(name='Royal Velvet', frame=['#2a1804', '#5e3e08', '#9a6c10', '#cfa02a', '#f2cc5a', '#fff2b0'],
         metal=['#2a2410', '#6a5e30', '#a89a60', '#d8cc94', '#f4ecc4', '#ffffff'],
         felt=['#060a2a', '#0a123e', '#101c56', '#18286e', '#223686', '#2e469c'], pat='royal'),
    dict(name='Purple Galaxy', frame=['#14141c', '#3a3c4a', '#686c7c', '#9aa0b0', '#cdd2de', '#ffffff'],
         metal=['#1a1024', '#3e2a5a', '#6a4a96', '#9a7ac8', '#c8b0ec', '#f4ecff'],
         felt=['#0a0418', '#120826', '#1a0e36', '#241448', '#2e1c5a', '#3a266c'], pat='galaxy'),
    dict(name='Deep Ocean', frame=['#1a1714', '#38322c', '#5e564c', '#8a8070', '#b4aa96', '#ddd5c0'],
         metal=['#0a1c18', '#1a4a40', '#2e7a66', '#52a88a', '#8cd4b4', '#d4fff0'],
         felt=['#021a20', '#04242c', '#063038', '#0a3e48', '#0e4e58', '#146068'], pat='ocean'),
    dict(name='Frozen Ice', frame=['#0c1c2c', '#244666', '#4a7aa2', '#7eaed0', '#b6dcf2', '#f2fbff'],
         metal=['#1a2a3a', '#4a6a8a', '#8ab0cc', '#bcd8ec', '#e4f4ff', '#ffffff'],
         felt=['#335f82', '#3f6f92', '#4b7fa2', '#5890b2', '#66a2c2', '#78b4d0'], pat='ice'),
    dict(name='Lava Rock', frame=['#060408', '#140e1a', '#22182c', '#342640', '#4a3a5a', '#6a5880'],
         metal=['#1a0402', '#5a1004', '#a82a08', '#e85a10', '#ffa030', '#fff0a0'],
         felt=['#0c0606', '#140a08', '#1c0e0a', '#24140e', '#2e1a12', '#3a2218'], pat='lava'),
    dict(name='Desert Sands', frame=['#2a1a0c', '#5a3c20', '#8a6440', '#b48c60', '#d8b484', '#f2d8a8'],
         metal=['#1e1206', '#4a2e10', '#7a4e1e', '#a87430', '#d4a050', '#f8d890'],
         felt=['#7e5222', '#946834', '#a87a44', '#ba8c54', '#ca9e66', '#d8ae78'], pat='desert'),
    dict(name='Neon Grid', frame=['#06060c', '#22222e', '#4c4c62', '#8a8aa8', '#ccccea', '#ffffff'],
         metal=['#1a0216', '#4a0840', '#901870', '#d834a8', '#ff6ade', '#ffd0f6'],
         felt=['#020206', '#05040c', '#080712', '#0b0a18', '#0e0d1e', '#121226'], pat='neon'),
    dict(name='Gold Luxury', frame=['#040404', '#0e0e10', '#1a1a1e', '#28282e', '#3a3a42', '#56565e'],
         metal=['#2a1804', '#6a4808', '#b08414', '#e0b42c', '#ffe066', '#fff8c8'],
         felt=['#8e7e58', '#a89870', '#beae88', '#d0c09c', '#ddcdaa', '#e8dab8'], pat='gold'),
    dict(name='Iron Checkers', frame=['#0c0c0e', '#222428', '#3e4046', '#5e626a', '#868a94', '#b2b6c0'],
         metal=['#121214', '#2e3034', '#4e5258', '#72767e', '#9ca0a8', '#d0d4dc'],
         felt=['#121216', '#1a1a20', '#22222a', '#2a2a32', '#323240', '#3a3a46'],
         felt2=['#4a4a52', '#56565e', '#62626a', '#6e6e76', '#7a7a82', '#86868e'], pat='checker'),
]


def ramp_map(t, stops):
    """t in [0,1] -> RGB via piecewise-linear interpolation of the stops."""
    cols = np.array([hexc(s)[:3] for s in stops], np.float32)
    n = len(stops) - 1
    x = np.clip(t, 0, 1) * n
    i = np.clip(np.floor(x).astype(int), 0, n - 1)
    f = (x - i)[..., None]
    return cols[i] * (1 - f) + cols[i + 1] * f


def luminance(a):
    a = a.astype(np.float32)
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0


def normalise(L, m, lo_p=1, hi_p=99.5, gamma=1.0):
    lo, hi = np.percentile(L[m], lo_p), np.percentile(L[m], hi_p)
    t = np.clip((L - lo) / max(hi - lo, 1e-6), 0, 1)
    return t ** gamma


def dither_quant(v, ramp, ox=0, oy=0):
    """v: (h,w) float level 0..1 at native grid -> RGB using ordered dithering."""
    h, w = v.shape
    n = len(ramp) - 1
    x = np.clip(v, 0, 1) * n
    base = np.floor(x)
    frac = x - base
    yy, xx = np.mgrid[0:h, 0:w]
    thr = BAYER4[(yy + oy) % 4, (xx + ox) % 4]
    idx = np.clip(base + (frac > thr), 0, n).astype(int)
    cols = np.array([hexc(s)[:3] for s in ramp], np.uint8)
    return cols[idx]


def voronoi_edges(W, H, cell, seed):
    """distance-to-border field (in texels) of a jittered-grid voronoi diagram"""
    gx, gy = W // cell + 3, H // cell + 3
    pts = []
    for j in range(-1, gy):
        for i in range(-1, gx):
            pts.append(((i + 0.15 + 0.7 * hash2(i, j, seed)) * cell, (j + 0.15 + 0.7 * hash2(i, j, seed + 7)) * cell))
    pts = np.array(pts, np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d1 = np.full((H, W), 1e9, np.float32)
    d2 = np.full((H, W), 1e9, np.float32)
    for (px, py) in pts:
        d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
        upd = d < d1
        d2 = np.where(upd, d1, np.minimum(d2, d))
        d1 = np.where(upd, d, d1)
    return (d2 - d1) * 0.5


def felt_texture(theme, base_lum, felt_native):
    """returns RGB native texture (H,W,3)."""
    H, W = base_lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    med = np.median(base_lum[felt_native])
    f = base_lum / max(med, 1e-6)
    v = 0.60 + 1.25 * (f - 1.0)          # noise + inner shadow of the original
    over = np.zeros((H, W, 3), np.int16)
    over_m = np.zeros((H, W), bool)
    pat = theme['pat']
    rnd = np.vectorize(lambda x, y, s: hash2(int(x), int(y), s))
    if pat == 'casino':
        lat = ((xx + yy) % 26 == 0) | ((xx - yy) % 26 == 0)
        v = v + lat * 0.07
        # faint ring in the middle, like a printed table marking
        cx, cy = W / 2, H / 2
        r = np.sqrt(((xx - cx) / 1.0) ** 2 + ((yy - cy) / 1.0) ** 2)
        v = v + ((np.abs(r - 58) < 0.8) | (np.abs(r - 62) < 0.8)) * 0.08
    elif pat == 'royal':
        v = v + 0.06 * np.sin((xx + yy) * 0.035)
        gx = (xx % 24) - 12
        gy = ((yy + (xx // 24 % 2) * 12) % 24) - 12
        motif = (np.abs(gx) + np.abs(gy) <= 2)
        motif2 = ((np.abs(gx) == 0) & (np.abs(gy) <= 4)) | ((np.abs(gy) == 0) & (np.abs(gx) <= 4))
        v = v + motif * 0.12 + motif2 * 0.07
    elif pat == 'galaxy':
        n = np.zeros((H, W), np.float32)
        for y in range(H):
            for x in range(W):
                n[y, x] = value_noise(x, y, 26.0, 11) * 0.65 + value_noise(x, y, 9.0, 12) * 0.35
        neb = np.clip((n - 0.55) * 2.2, 0, 1)
        v = v + neb * 0.25
        h = rnd(xx, yy, 5)
        stars = h < 0.0045
        big = h < 0.0007
        over[stars] = (210, 200, 255)
        over_m |= stars
        for (y, x) in zip(*np.nonzero(big)):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    over[y + dy, x + dx] = (150, 120, 230)
                    over_m[y + dy, x + dx] = True
            over[y, x] = (255, 255, 255)
        # magenta tint in dense nebula
        tint = neb > 0.55
        over_m_t = tint & ~over_m
        theme['_tint'] = (over_m_t, (0.22, '#8a3aa8'))
    elif pat == 'ocean':
        ph = (yy // 15) * 1.7
        wave = (yy + 2.5 * np.sin(xx * 0.11 + ph)) % 15
        v = v + (wave < 1.0) * 0.16 + ((wave >= 1.0) & (wave < 2.0)) * 0.05
        n = np.zeros((H, W), np.float32)
        for y in range(H):
            for x in range(W):
                n[y, x] = value_noise(x, y, 18.0, 3)
        v = v + (n > 0.72) * 0.05
    elif pat == 'ice':
        e = voronoi_edges(W, H, 30, 21)
        crack = e < 0.7
        v = v + 0.05 * np.sin((xx - yy) * 0.05)
        v = v + crack * 0.30 + ((e >= 0.7) & (e < 1.6)) * 0.10
        h = rnd(xx, yy, 9)
        sp = (h < 0.002) & ~crack
        over[sp] = (240, 252, 255)
        over_m |= sp
    elif pat == 'lava':
        e = voronoi_edges(W, H, 54, 33)
        core = e < 0.55
        halo = (e >= 0.55) & (e < 1.25)
        halo2 = (e >= 1.25) & (e < 2.6)
        over[core] = hexc('#f0902a')[:3]
        over[halo] = hexc('#8e2a0e')[:3]
        over_m |= core | halo
        v = v + halo2 * 0.22
        h = rnd(xx, yy, 4)
        emb = (h < 0.0025) & ~core & ~halo
        over[emb] = hexc('#ff7a2a')[:3]
        over_m |= emb
        # glow only where the felt is not in deep shadow
        theme['_shadow_kill'] = True
    elif pat == 'desert':
        rip = (yy + 4.0 * np.sin(xx * 0.045) + 2.0 * np.sin(xx * 0.13 + yy * 0.02)) % 10
        v = v - (rip < 1.0) * 0.14 + ((rip >= 1.0) & (rip < 2.0)) * 0.07
        h = rnd(xx, yy, 2)
        v = v - (h < 0.004) * 0.25
    elif pat == 'neon':
        cx0, cy0 = W // 2, H // 2
        gxm = (xx - cx0) % 26
        gym = (yy - cy0) % 26
        vline = gxm == 0
        hline = gym == 0
        vglow = (gxm == 1) | (gxm == 25)
        hglow = (gym == 1) | (gym == 25)
        over[vglow] = hexc('#063848')[:3]
        over[hglow] = hexc('#3a0636')[:3]
        over_m |= vglow | hglow
        over[hline] = hexc('#d42ab4')[:3]
        over[vline] = hexc('#00e5ff')[:3]
        over[vline & hline] = (255, 255, 255)
        over_m |= vline | hline
        theme['_shadow_kill'] = True
    elif pat == 'gold':
        lat = ((xx + yy) % 32 == 0) | ((xx - yy) % 32 == 0)
        over[lat] = hexc('#c89a34')[:3]
        over_m |= lat
        # small gold lozenges on the crossings
        gx = (xx + yy) % 32
        gy = (xx - yy) % 32
        cross = ((gx <= 1) | (gx >= 31)) & ((gy <= 1) | (gy >= 31))
        over[cross] = hexc('#f2cc5a')[:3]
        over_m |= cross
        # fans between
        fan = ((xx % 32) == 16) & ((yy % 32) >= 14) & ((yy % 32) <= 18)
        v = v + fan * 0.08
    elif pat == 'checker':
        cx0, cy0 = W // 2, H // 2
        sq = 30
        light = (((xx - cx0) // sq + (yy - cy0) // sq) % 2) == 0
        theme['_checker'] = light
    rgb = dither_quant(v, theme['felt'])
    if pat == 'checker':
        rgb2 = dither_quant(v, theme['felt2'])
        rgb = np.where(theme['_checker'][..., None], rgb2, rgb)
    if '_tint' in theme:
        m, (k, col) = theme.pop('_tint')
        c = np.array(hexc(col)[:3], np.float32)
        rgb = np.where(m[..., None], (rgb * (1 - k) + c * k).astype(np.uint8), rgb)
    if over_m.any():
        keep = over_m
        if theme.pop('_shadow_kill', False):
            # dim overlays inside the dark inner shadow so the edge stays calm
            dim = np.clip((f - 0.55) / 0.35, 0, 1)
            o = over.astype(np.float32) * dim[..., None] + rgb.astype(np.float32) * (1 - dim[..., None])
            rgb = np.where(keep[..., None], o.astype(np.uint8), rgb)
        else:
            rgb = np.where(keep[..., None], over.astype(np.uint8), rgb)
    return rgb


def build():
    os.makedirs(OUT, exist_ok=True)
    a = load()
    H, W = a.shape[:2]
    felt, brass_raw, plate, inrect = masks(a)
    boxes = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in FIT_BOXES:
        boxes[y0:y1, x0:x1] = True
    metal = brass_raw & boxes & ~felt
    # include the bright rim of the fittings (anti-aliased edge pixels)
    metal = metal | (dilate(metal, 1) & boxes & ~felt & (luminance(a) > 0.32))
    wood = ~felt & ~metal
    L = luminance(a)
    t_wood = normalise(L, wood, 0.5, 99.7)
    t_metal = normalise(L, metal, 0.5, 99.9)
    # native felt luminance
    Hn, Wn = (H + G - 1) // G, (W + G - 1) // G
    pad = np.zeros((Hn * G, Wn * G), np.float32)
    pad[:H, :W] = L
    fm = np.zeros((Hn * G, Wn * G), bool)
    fm[:H, :W] = felt
    blk = pad.reshape(Hn, G, Wn, G)
    blkm = fm.reshape(Hn, G, Wn, G)
    cnt = blkm.sum(axis=(1, 3))
    s = (blk * blkm).sum(axis=(1, 3))
    base_lum = np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
    # fill non-felt native cells with nearest felt value (edges) to avoid NaN
    med = np.nanmedian(base_lum)
    base_lum = np.where(np.isnan(base_lum), med * 0.5, base_lum)
    felt_native = cnt > 8
    results = []
    for k, th in enumerate(THEMES, start=1):
        th = dict(th)
        out = np.zeros((H, W, 3), np.uint8)
        out[wood] = ramp_map(t_wood[wood], th['frame']).astype(np.uint8)
        out[metal] = ramp_map(t_metal[metal], th['metal']).astype(np.uint8)
        tex = felt_texture(th, base_lum, felt_native)
        big = np.repeat(np.repeat(tex, G, axis=0), G, axis=1)[:H, :W]
        out[felt] = big[felt]
        if th['pat'] == 'gold':
            # thin gold trim around the felt edge for the black-gold frame
            ring = dilate(felt, 3) & ~felt & ~metal
            out[ring] = (out[ring].astype(np.float32) * 0.3 + np.array(hexc('#d8a830')[:3]) * 0.7).astype(np.uint8)
        im = Image.fromarray(out, 'RGB').convert('RGBA')
        path = os.path.join(OUT, 'board_%d.png' % k)
        im.save(path, optimize=True)
        thumb = im.resize((290, 218), Image.BOX)
        thumb.save(os.path.join(OUT, 'board_%d_thumb.png' % k))
        results.append(('board_%d %s' % (k, th['name']), thumb))
        print('board', k, th['name'])
    orig = Image.open(os.path.join(REPO, "work", "recovered", "assets", "art", "сукно.png")).convert('RGBA').resize((290, 218), Image.BOX)
    sheet = contact_sheet([('original', orig)] + results, (290, 218), 4, label_h=16, bg=(30, 30, 34, 255))
    sheet.save(os.path.join(OUT, 'contact_sheet.png'))


if __name__ == '__main__':
    build()
