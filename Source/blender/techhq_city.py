"""kit-techhq skyline: the two rows of neighbouring buildings round the tower (Backdrop_RowA / RowB), built from the
table in src/data/themes/techhq.js (between SKYLINE-BEGIN / END), the same table zones.js uses for the shafts that
carry them down to the street. From 120 m up most of them are below us, so their roofs carry the detail: a loft
with a water tank and a roof deck, roof gardens, a rooftop sports court, solar arrays, a hotel pool, a construction
crane; a few glass towers rise above us.
"""
import json
import math
import os
import re

from fam_kit_techhq import HERE, HEX2NAME


def read_skyline():
    src = open(os.path.join(HERE, '..', 'src', 'data', 'themes', 'techhq.js'), encoding='utf-8').read()
    m = re.search(r'/\*SKYLINE-BEGIN\*/(.*?)/\*SKYLINE-END\*/', src, re.S)
    txt = re.sub(r"'", '"', m.group(1))
    txt = re.sub(r'(\w+)\s*:', r'"\1":', txt)
    base = float(re.search(r'var BASE = (-?[\d.]+)', src).group(1))
    return json.loads(txt), base


LOD = 1.9      # window bands and strips are drawn per two floors (the rows stand 60 - 150 m away; the GLB budget)


def strips(k, x0, x1, y0, y1, z0, z1, win, step=2.6):
    """Vertical window strips on all four faces (one quad per strip)."""
    step *= LOD
    w, d = x1 - x0, y1 - y0
    nf, ns = max(2, int(w / step)), max(2, int(d / step))
    for i in range(nf):
        x = x0 + w * (i + 0.5) / nf
        k.qy(x - 0.45, x + 0.45, z0 + 1, z1 - 0.8, y0 - 0.05, -1, win)
        k.qy(x - 0.45, x + 0.45, z0 + 1, z1 - 0.8, y1 + 0.05, 1, win)
    for i in range(ns):
        y = y0 + d * (i + 0.5) / ns
        k.qx(y - 0.45, y + 0.45, z0 + 1, z1 - 0.8, x0 - 0.05, -1, win)
        k.qx(y - 0.45, y + 0.45, z0 + 1, z1 - 0.8, x1 + 0.05, 1, win)


def bands(k, x0, x1, y0, y1, z0, z1, step, win, frac=0.5):
    """Horizontal window ribbons on all four faces."""
    step *= LOD
    z = z0 + step * 0.35
    while z + step * frac < z1 - 0.4:
        k.qy(x0 + 0.4, x1 - 0.4, z, z + step * frac, y0 - 0.05, -1, win)
        k.qy(x0 + 0.4, x1 - 0.4, z, z + step * frac, y1 + 0.05, 1, win)
        k.qx(y0 + 0.4, y1 - 0.4, z, z + step * frac, x0 - 0.05, -1, win)
        k.qx(y0 + 0.4, y1 - 0.4, z, z + step * frac, x1 + 0.05, 1, win)
        z += step


def punched(k, x0, x1, y0, y1, z0, z1, win, col_w=4.4, row_h=4.2):
    """Punched windows (a loft's grid) on the two long faces, ribbons on the short ones."""
    w = x1 - x0
    nc = max(2, int(w / (col_w * 1.3)))
    z = z0 + 1.2
    while z + 3.2 < z1 - 0.8:
        for i in range(nc):
            x = x0 + w * (i + 0.5) / nc
            k.qy(x - 1.1, x + 1.1, z, z + 3.2, y0 - 0.05, -1, win)
            k.qy(x - 1.1, x + 1.1, z, z + 3.2, y1 + 0.05, 1, win)
        k.qx(y0 + 1.0, y1 - 1.0, z, z + 3.2, x0 - 0.05, -1, win)
        k.qx(y0 + 1.0, y1 - 1.0, z, z + 3.2, x1 + 0.05, 1, win)
        z += row_h * LOD


def parapet(k, x0, x1, y0, y1, z, c, h=1.1, t=0.4):
    k.bx(x0, x1, y0, y0 + t, z, z + h, c)
    k.bx(x0, x1, y1 - t, y1, z, z + h, c)
    k.bx(x0, x0 + t, y0 + t + 0.02, y1 - t - 0.02, z, z + h, c)     # 2 cm short of the end walls (float32 at 100 m+)
    k.bx(x1 - t, x1, y0 + t + 0.02, y1 - t - 0.02, z, z + h, c)


def hvac(k, x, y, z, n=2):
    for i in range(n):
        k.bx(x + i * 2.6, x + i * 2.6 + 2.0, y, y + 1.5, z, z + 1.3, 'steel')
        k.cyl(x + i * 2.6 + 1.0, y + 0.75, z + 1.3, 0.55, 0.55, 0.1, 'steelD', seg=8, ink=False)


def tree(k, x, y, z, s=1.0, c='leaf'):
    k.cyl(x, y, z, 0.18 * s, 0.14 * s, 1.6 * s, 'bark', seg=5, ink=False)
    k.sph(x, y, z + 2.3 * s, 1.3 * s, c, seg=(5, 3))


def building(k, t, base):
    x, fy, w, d, col, wcol, top, style = t
    c, wc = HEX2NAME[col.upper()], HEX2NAME[wcol.upper()]
    x0, x1, y0, y1 = x - w / 2, x + w / 2, fy, fy + d
    cx, cy = x, fy + d / 2
    k.bx(x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4, base, base + 0.9, 'concrete')        # where the shaft meets the piece
    z0 = base + 0.9
    if style == 'brick':
        k.bx(x0, x1, y0, y1, z0, top, c)
        punched(k, x0, x1, y0, y1, z0, top, wc)
        parapet(k, x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, top, 'twSand')
        k.qz(x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, top + 0.2, 1, 'concrete')
        k.bx(x0 + 2, x0 + 10, y0 + 2, y0 + 9, top + 0.2, top + 0.45, 'deck')       # roof deck with a pergola
        for px in (x0 + 2.3, x0 + 9.7):
            for py in (y0 + 2.3, y0 + 8.7):
                k.bx(px - 0.15, px + 0.15, py - 0.15, py + 0.15, top + 0.45, top + 3.0, 'graphite')
        for i in range(8):
            k.bx(x0 + 2.2 + i * 1.0, x0 + 2.4 + i * 1.0, y0 + 2.1, y0 + 8.9, top + 3.0, top + 3.2, 'oak', ink=False)
        k.cyl(x1 - 5, y1 - 5, top + 0.2, 0.25, 0.25, 2.2, 'graphite', seg=6, ink=False)
        for (dx, dy) in ((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)):
            k.bx(x1 - 5 + dx - 0.12, x1 - 5 + dx + 0.12, y1 - 5 + dy - 0.12, y1 - 5 + dy + 0.12, top + 0.2, top + 2.4, 'graphite')
        k.cyl(x1 - 5, y1 - 5, top + 2.4, 2.0, 2.0, 3.6, 'oakD', seg=10)              # the water tank
        k.cyl(x1 - 5, y1 - 5, top + 6.0, 2.05, 0.2, 1.6, 'bark', seg=10)
        hvac(k, x0 + 12, y1 - 4, top + 0.2, 2)
    elif style == 'tower':
        tl = top - 14
        k.bx(x0, x1, y0, y1, z0, tl, c)
        bands(k, x0, x1, y0, y1, z0, tl, 4.0, wc, 0.62)
        k.bx(x0 + 2, x1 - 2, y0 + 2, y1 - 2, tl, top, c)
        strips(k, x0 + 2, x1 - 2, y0 + 2, y1 - 2, tl, top, 'twDark', 1.8)
        k.bx(x0 + 1.6, x1 - 1.6, y0 + 1.6, y1 - 1.6, top, top + 1.0, 'twWhite')
        k.bx(x0 + 5, x1 - 5, y0 + 5, y1 - 5, top + 1.0, top + 5.0, 'steel')
        for i in range(6):
            k.qy(x0 + 5.5 + i * (w - 11) / 6, x0 + 5.5 + i * (w - 11) / 6 + 0.8, top + 1.4, top + 4.6, y0 + 4.95, -1, 'steelD')
        k.cyl(cx, cy, top + 5.0, 0.5, 0.15, 14, 'twWhite', seg=6)
        k.sph(cx, cy, top + 19.3, 0.5, 'red', seg=(5, 3), ink=False)
    elif style == 'garden':
        k.bx(x0, x1, y0, y1, z0, top, c)
        bands(k, x0, x1, y0, y1, z0, top, 3.8, wc, 0.5)
        parapet(k, x0, x1, y0, y1, top, 'twWhite', 1.2, 0.3)
        k.bx(x0 + 0.31, x1 - 0.31, y0 + 0.31, y1 - 0.31, top, top + 0.45, 'soil', ink=False)
        k.qz(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, top + 0.453, 1, 'leafL')
        k.qz(cx - 1.0, cx + 1.0, y0 + 0.3, y1 - 0.3, top + 0.456, 1, 'paver')
        k.qz(x0 + 0.3, x1 - 0.3, cy - 0.8, cy + 0.8, top + 0.459, 1, 'paver')
        for i, (dx, dy) in enumerate(((-7, -5), (-4, 6), (9, -7), (7, 5))):
            if abs(dx) < w / 2 - 2 and abs(dy) < d / 2 - 2:
                tree(k, cx + dx, cy + dy, top + 0.45, 0.9 + 0.1 * (i % 3), 'leaf' if i % 2 else 'leaf2')
        k.bx(cx + 2, cx + 7, cy - 6, cy - 2.5, top + 0.45, top + 3.2, 'glass')
        k.bx(cx + 1.8, cx + 7.2, cy - 6.2, cy - 2.3, top + 3.2, top + 3.5, 'twWhite')
    elif style == 'glass':
        k.bx(x0, x1, y0, y1, z0, top, c)
        bands(k, x0, x1, y0, y1, z0, top, 4.0, wc, 0.7)
        k.bx(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, top, top + 0.9, 'twWhite')
        k.bx(x0 + 3, x0 + 12, y0 + 4, y1 - 4, top + 0.9, top + 4.5, 'steel')           # plant room
        for i in range(8):
            k.qy(x0 + 3.4 + i * 1.1, x0 + 3.4 + i * 1.1 + 0.6, top + 1.3, top + 4.1, y0 + 3.95, -1, 'steelD')
        for i in range(4):                                                             # solar rows
            yy = y0 + 2 + i * 3.2
            if yy + 2 < y1 - 1:
                k.prism([(x1 - 9, top + 0.9), (x1 - 2, top + 0.9), (x1 - 2, top + 1.1), (x1 - 9, top + 1.1)], yy, yy + 2.2, 'steelD', ink=False)
                k.poly([(x1 - 9, yy, top + 1.2), (x1 - 2, yy, top + 1.2), (x1 - 2, yy + 2.2, top + 2.0), (x1 - 9, yy + 2.2, top + 2.0)], 'solar', (0, -0.35, 1))
    elif style == 'court':
        k.bx(x0, x1, y0, y1, z0, top, c)
        bands(k, x0, x1, y0, y1, z0, top, 3.4, wc, 0.45)
        parapet(k, x0, x1, y0, y1, top, 'twWhite', 1.0, 0.3)
        k.qz(x0 + 1.5, x1 - 1.5, y0 + 1.5, y1 - 4, top + 0.05, 1, 'sky')
        k.qz(x0 + 3, x1 - 3, y0 + 3, y1 - 5.5, top + 0.08, 1, 'mint')
        for i, (a, b, e, f) in enumerate(((x0 + 3, x1 - 3, y0 + 2.9, y0 + 3.1), (x0 + 3, x1 - 3, y1 - 5.6, y1 - 5.4), (cx - 0.1, cx + 0.1, y0 + 3, y1 - 5.5),
                                          (x0 + 2.9, x0 + 3.1, y0 + 3, y1 - 5.5), (x1 - 3.1, x1 - 2.9, y0 + 3, y1 - 5.5))):
            k.qz(a, b, e, f, top + (0.11 if i < 2 else 0.115), 1, 'white')
        for xx in (x0 + 1.5, x1 - 1.5):
            for i in range(5):
                yy = y0 + 1.5 + i * (d - 5.5) / 4
                k.bx(xx - 0.06, xx + 0.06, yy - 0.06, yy + 0.06, top, top + 3.9, 'graphite', ink=False)
            k.bx(xx - 0.05, xx + 0.05, y0 + 1.5, y1 - 4, top + 3.9, top + 4.0, 'graphite', ink=False)
        for yy in (y0 + 1.5, y1 - 4):
            k.bx(x0 + 1.5, x1 - 1.5, yy - 0.05, yy + 0.05, top + 3.82, top + 3.92, 'graphite', ink=False)
        for xx in (cx - 0.8, cx + 0.8):
            k.bx(xx - 0.1, xx + 0.1, y0 + 2.2, y0 + 2.4, top, top + 3.2, 'white', ink=False)
        k.bx(x0 + 2, x0 + 8, y1 - 3.5, y1 - 0.6, top, top + 3, 'twWhite')
        k.qy(x0 + 2.5, x0 + 7.5, top + 1, top + 2.4, y1 - 3.53, -1, wc)
    elif style == 'solar':
        k.bx(x0, x1, y0, y1, z0, top, c)
        bands(k, x0, x1, y0, y1, z0, top, 3.6, wc, 0.48)
        parapet(k, x0, x1, y0, y1, top, 'concrete', 0.9, 0.3)
        yy = y0 + 1.2
        while yy + 2.0 < y1 - 1.0:
            k.prism([(x0 + 1.2, top), (x1 - 6, top), (x1 - 6, top + 0.25), (x0 + 1.2, top + 0.25)], yy, yy + 1.9, 'steelD', ink=False)
            k.poly([(x0 + 1.2, yy, top + 0.3), (x1 - 6, yy, top + 0.3), (x1 - 6, yy + 1.9, top + 1.1), (x0 + 1.2, yy + 1.9, top + 1.1)], 'solar', (0, -0.4, 1))
            yy += 2.8
        k.bx(x1 - 5, x1 - 1.2, y1 - 6, y1 - 1.2, top, top + 3.2, 'concrete')
        hvac(k, x1 - 5, y0 + 1.5, top, 1)
    elif style == 'crane':
        k.bx(x0, x1, y0, y1, z0, top, c)
        punched(k, x0, x1, y0, y1, z0, top, wc)
        for i in range(3):
            z = top + 3.6 * (i + 1)
            k.bx(x0, x1, y0, y1, z - 0.3, z, 'twWhite')
        for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), (cx, y0), (cx, y1)):
            k.bx(px - 0.4, px + 0.4, py - 0.4, py + 0.4, top, top + 10.6, 'steel')
        mx, my = x0 + 4, cy
        k.bx(mx - 1.0, mx + 1.0, my - 1.0, my + 1.0, top, top + 44, 'sun')
        for j in range(6):
            z = top + 2 + j * 7.0
            k.beam((mx - 1.05, my - 1.05, z), (mx + 1.05, my - 1.05, z + 6.6), 0.12, 'graphite', ink=False)
        k.bx(mx - 14, mx + 34, my - 0.7, my + 0.7, top + 44, top + 45.6, 'sun')
        k.bx(mx - 13, mx - 7, my - 1.5, my + 1.5, top + 41.5, top + 44, 'graphite')
        k.bx(mx + 1.0, mx + 3.2, my - 1.2, my + 1.2, top + 41.6, top + 44, 'twWhite')
        k.beam((mx, my, top + 49), (mx + 34, my, top + 45.6), 0.15, 'graphite', ink=False)
        k.beam((mx, my + 0.2, top + 49), (mx - 14, my + 0.2, top + 45.6), 0.15, 'graphite', ink=False)
        k.bx(mx - 0.3, mx + 0.3, my - 0.3, my + 0.3, top + 45.6, top + 49.5, 'sun')
        k.beam((mx + 24, my + 0.4, top + 44), (mx + 24, my + 0.4, top + 20), 0.06, 'graphite', ink=False)
        k.bx(mx + 23, mx + 25, my - 0.6, my + 1.4, top + 18.5, top + 20, 'oakD')
    else:   # hotel: a stepped tower with a rooftop pool
        t1 = top - 12
        k.bx(x0, x1, y0, y1, z0, t1, c)
        bands(k, x0, x1, y0, y1, z0, t1, 3.4, wc, 0.55)
        k.bx(x0 + 4, x1, y0 + 3, y1, t1, top, c)
        bands(k, x0 + 4, x1, y0 + 3, y1, t1, top, 3.4, wc, 0.55)
        k.bx(x0 - 0.2, x0 + 3.95, y0 - 0.2, y1 + 0.2, t1, t1 + 0.3, 'twWhite')
        k.bx(x0 + 0.8, x0 + 3.4, y0 + 2, y1 - 2, t1 + 0.3, t1 + 0.8, 'twWhite')
        k.qz(x0 + 1.0, x0 + 3.2, y0 + 2.2, y1 - 2.2, t1 + 0.803, 1, 'sky')
        k.bx(x0 + 3.8, x1 + 0.2, y0 + 2.8, y1 + 0.2, top, top + 1.0, 'twWhite')
        k.bx(x0 + 8, x1 - 4, y0 + 7, y1 - 4, top + 1.0, top + 4.0, 'steel')
        k.bx(x1 - 7, x1 - 1, y1 - 3, y1 - 1, top + 1.0, top + 7.0, 'twWhite')
        k.qy(x1 - 6.8, x1 - 1.2, top + 2.0, top + 6.6, y1 - 3.03, -1, 'coral')


def backdrop(k, rows, name, base):
    k.begin()
    for t in rows[name]:
        building(k, t, base)
    return k


def build(k):
    rows, base = read_skyline()
    for name in sorted(rows):
        backdrop(k, rows, name, base).finish(name)
