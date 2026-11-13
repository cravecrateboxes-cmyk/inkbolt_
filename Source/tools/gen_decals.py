"""Tactical look decal atlas (plan Stage 9.1).

    python3 tools/gen_decals.py [--preview out.jpg]

Writes
    Source/assets/tex/decals.webp     1024 x 1024 RGBA, 8 x 8 cells of 128 px. R = G = B = grey value, A = coverage.
                                      Colour comes from a tint per placement (dress.js); the shader multiplies.
    Source/src/data/decals.gen.js     IB.DECALS = { names: [...], cell: { name: index }, kind: { name: 'floor'|'wall'|'any' } }

Deterministic (fixed seeds). Every cell fades to zero alpha 3 px inside its border, so mipmaps never bleed a
neighbour in. The atlas is a plain image texture with true alpha (no pixel read-back), so trap T26 does not apply.
"""
import os
import sys
import json
import numpy as np
from PIL import Image, ImageDraw

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SRC, 'assets', 'tex', 'decals.webp')
OUT_JS = os.path.join(SRC, 'src', 'data', 'decals.gen.js')
C = 128                     # cell size
G = 8                       # cells per side
YY, XX = np.meshgrid((np.arange(C) + 0.5) / C, (np.arange(C) + 0.5) / C, indexing='ij')   # v (down), u (right)


def fbm(rng, base=4, octaves=4, gain=0.55):
    out = np.zeros((C, C))
    amp, tot, f = 1.0, 0.0, base
    for _ in range(octaves):
        small = rng.random((f + 1, f + 1)).astype(np.float32)
        im = Image.fromarray(small, 'F').resize((C, C), Image.BICUBIC)
        out += amp * np.asarray(im)
        tot += amp
        amp *= gain
        f *= 2
    out /= tot
    return (out - out.mean()) / (out.std() + 1e-9)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, s):
    """Separable gaussian blur (sigma in px), edges clamped."""
    r = max(1, int(s * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode='edge')
    p = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, p)


def radial(cx=0.5, cy=0.5, sx=1.0, sy=1.0):
    return np.hypot((XX - cx) / sx, (YY - cy) / sy)


def border():
    d = np.minimum.reduce([XX, 1 - XX, YY, 1 - YY]) * C
    return ss(2.5, 6.0, d)


def canvas(scale=4):
    """A PIL drawing surface at scale x, returned with a finisher that downsamples to a 0..1 cell (antialiased)."""
    im = Image.new('L', (C * scale, C * scale), 0)

    def done(soft=0.0):
        a = np.asarray(im.resize((C, C), Image.LANCZOS)).astype(float) / 255
        return blur(a, soft) if soft else a
    return im, ImageDraw.Draw(im), done


# ------------------------------------------------------------------------------------------------- cell painters
# each returns (grey 0..1, alpha 0..1)
def stain(rng, dark=0.12, ring=0.0, lobes=0.18, size=0.42):
    n = fbm(rng, 3, 4)
    a = np.arctan2(YY - 0.5, XX - 0.5)
    wob = 1 + lobes * (np.sin(a * 3 + rng.uniform(0, 6)) * 0.6 + np.sin(a * 5 + rng.uniform(0, 6)) * 0.4) + 0.12 * n
    r = radial() / (size * wob)
    body = ss(1.0, 0.55, r) * (0.65 + 0.2 * fbm(rng, 8, 3))
    edge = ring * np.exp(-((r - 0.9) / 0.09) ** 2)
    alpha = np.clip(body + edge, 0, 1)
    return np.full((C, C), dark) + 0.06 * fbm(rng, 16, 2), alpha


def streak(rng, width=0.16, dark=0.15, drips=5, length=0.95):
    """Vertical streak from the top (v = 0) fading downwards."""
    n = fbm(rng, 6, 4)
    alpha = np.zeros((C, C))
    for _ in range(drips):
        x0 = 0.5 + rng.normal(0, width * 0.6)
        w = width * rng.uniform(0.25, 0.7)
        L = length * rng.uniform(0.45, 1.0)
        xs = x0 + 0.02 * np.sin(YY * rng.uniform(4, 9) + rng.uniform(0, 6))
        col = np.exp(-((XX - xs) / w) ** 2 * 2.2)
        fade = ss(L, L * 0.35, YY) * ss(0.0, 0.05, YY)
        alpha = np.maximum(alpha, col * fade * rng.uniform(0.6, 1.0))
    alpha = np.clip(alpha * (0.8 + 0.25 * n), 0, 1)
    return np.full((C, C), dark) + 0.05 * n, alpha


def crack_cell(rng, count=1, branch=3, thick=1.4):
    im, d, done = canvas()
    S = 4 * C

    def walk(x, y, a, L, w, depth):
        pts = [(x, y)]
        for _ in range(int(L)):
            a += rng.normal(0, 0.28)
            x += np.cos(a) * 4
            y += np.sin(a) * 4
            pts.append((x, y))
        for i in range(len(pts) - 1):
            t = i / max(1, len(pts) - 1)
            ww = max(1, int(w * (1 - 0.7 * t) * 4))
            d.line([pts[i], pts[i + 1]], fill=255, width=ww)
        if depth < 2:
            for _ in range(branch if depth == 0 else 1):
                k = rng.integers(len(pts) // 4, max(len(pts) // 4 + 1, len(pts) - 1))
                walk(pts[k][0], pts[k][1], a + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1), L * 0.4, w * 0.6, depth + 1)
    for _ in range(count):
        a = rng.uniform(0, 2 * np.pi)
        x, y = S / 2 - np.cos(a) * S * 0.33, S / 2 - np.sin(a) * S * 0.33
        walk(x, y, a, S * 0.65 / 4, thick, 0)
    a = done(0.4)
    halo = blur(a, 2.2) * 0.35
    return np.full((C, C), 0.08), np.clip(a + halo, 0, 1) * (ss(0.5, 0.36, radial()) * 0.6 + 0.4)


def tyre(rng):
    r = radial(0.5, 1.15, 1, 1)
    band = np.zeros((C, C))
    for off in (0.0, 0.11):
        rr = 0.78 + off
        band += np.exp(-((r - rr) / 0.035) ** 2)
    tread = 0.75 + 0.25 * np.sin(np.arctan2(YY - 1.15, XX - 0.5) * 140)
    a = np.clip(band * tread * (0.6 + 0.2 * fbm(rng, 8, 3)), 0, 1) * ss(0.0, 0.25, XX) * ss(1.0, 0.75, XX)
    return np.full((C, C), 0.07), a


def scuff(rng):
    n = fbm(rng, 3, 4)
    lane = np.exp(-((XX - 0.5 - 0.03 * n) / 0.22) ** 2)
    marks = np.clip(fbm(rng, 24, 2) * 0.5 + 0.5, 0, 1) ** 2
    a = lane * (0.25 + 0.5 * marks) * ss(0.0, 0.2, YY) * ss(1.0, 0.8, YY)
    return np.full((C, C), 0.2), np.clip(a, 0, 1)


def puddle(rng):
    g, a = stain(rng, dark=0.05, ring=0.25, lobes=0.25, size=0.44)
    return g, np.clip(a * 1.1, 0, 1)


def patch_cell(rng):
    x0, y0 = rng.uniform(0.12, 0.2), rng.uniform(0.12, 0.2)
    x1, y1 = rng.uniform(0.8, 0.88), rng.uniform(0.8, 0.88)
    box = ss(0.0, 0.015, np.minimum.reduce([XX - x0, x1 - XX, YY - y0, y1 - YY]))
    edge = box - ss(0.015, 0.04, np.minimum.reduce([XX - x0, x1 - XX, YY - y0, y1 - YY]))
    g = 0.42 + 0.06 * fbm(rng, 10, 3) - 0.2 * edge
    return g, box * 0.85


def disc(rng, kind):
    r = radial()
    if kind == 'manhole':
        body = ss(0.43, 0.42, r)
        rim = ss(0.36, 0.37, r) * ss(0.43, 0.42, r)
        pat = (np.sin(XX * 60) * np.sin(YY * 60) > 0.3).astype(float) * ss(0.33, 0.32, r)
        g = 0.22 + 0.25 * rim + 0.18 * pat + 0.04 * fbm(rng, 12, 2)
        return g, body
    # drain: round grille
    body = ss(0.36, 0.35, r)
    slots = (np.abs(np.sin(XX * np.pi * 9)) > 0.45).astype(float) * ss(0.29, 0.28, r)
    g = 0.38 - 0.32 * slots + 0.03 * fbm(rng, 12, 2)
    return g, body


def grate(rng):
    box = ss(0.06, 0.08, np.minimum.reduce([XX, 1 - XX, YY, 1 - YY]))
    bars = (np.abs(np.sin(XX * np.pi * 14)) > 0.55).astype(float)
    inner = ss(0.11, 0.13, np.minimum.reduce([XX, 1 - XX, YY, 1 - YY]))
    g = 0.42 - 0.36 * bars * inner + 0.03 * fbm(rng, 12, 2)
    return g, box


def paint_cell(rng, shape):
    im, d, done = canvas()
    S = 4 * C
    if shape == 'arrow':
        d.polygon([(S * .5, S * .08), (S * .86, S * .46), (S * .64, S * .46), (S * .64, S * .92), (S * .36, S * .92),
                   (S * .36, S * .46), (S * .14, S * .46)], fill=255)
    elif shape == 'chevrons':
        for i in range(-2, 7):
            x = i * S * 0.2
            d.polygon([(x, S * .3), (x + S * 0.1, S * .3), (x + S * 0.1 + S * 0.4, S * .7), (x + S * 0.4, S * .7)], fill=255)
    a = done(0.3)
    wear = np.clip(0.9 + 0.22 * fbm(rng, 20, 3), 0, 1)
    return np.full((C, C), 0.92), a * wear


# 5 x 7 stencil glyphs (bridges are the gaps: the font is drawn with cut bars)
GLYPHS = {
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
    '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'],
    '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],
    '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
    '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'],
    'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
    'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
    ' ': ['00000'] * 7,
}


def text_cell(rng, lines, h=0.22):
    """Stencil text, lines centred; each glyph 5 x 7 blocks with a stencil cut across the middle row."""
    im, d, done = canvas()
    S = 4 * C
    rows = len(lines)
    bh = S * h / 7
    widest = max(len(l) for l in lines)
    bw = min(bh, S * 0.9 / (widest * 6))
    bh = min(bh, bw * 1.15)
    y0 = S / 2 - rows * bh * 8.5 / 2
    for li, line in enumerate(lines):
        x0 = S / 2 - len(line) * bw * 6 / 2
        for ci, ch in enumerate(line):
            gl = GLYPHS.get(ch, GLYPHS[' '])
            for ry, row in enumerate(gl):
                for rx, bit in enumerate(row):
                    if bit == '1':
                        x = x0 + (ci * 6 + rx) * bw
                        y = y0 + (li * 8.5 + ry) * bh
                        cut = bh * 0.18 if ry in (3,) else 0
                        d.rectangle([x, y + cut, x + bw - 1, y + bh - 1 - cut], fill=255)
    a = done(0.35)
    wear = np.clip(0.9 + 0.25 * fbm(rng, 20, 3), 0, 1)
    overspray = blur(a, 2.5) * 0.18
    return np.full((C, C), 0.92), np.clip(a * wear + overspray, 0, 1)


def poster(rng, style):
    x0, y0, x1, y1 = 0.18, 0.08, 0.82, 0.92
    inside = np.minimum.reduce([XX - x0, x1 - XX, YY - y0, y1 - YY])
    paper = ss(0.0, 0.01, inside)
    n = fbm(rng, 6, 4)
    # torn edge: a ragged cut through a random corner region
    tear_ang = rng.uniform(0, 2 * np.pi)
    tear = (XX - 0.5) * np.cos(tear_ang) + (YY - 0.5) * np.sin(tear_ang)
    keep = ss(0.30, 0.27, tear + 0.035 * fbm(rng, 18, 3))
    g = 0.86 + 0.05 * n
    u = (XX - x0) / (x1 - x0)
    v = (YY - y0) / (y1 - y0)
    if style == 0:      # big block + bars
        g = np.where((u > 0.1) & (u < 0.9) & (v > 0.08) & (v < 0.5), 0.25, g)
        for k in range(4):
            g = np.where((u > 0.1) & (u < 0.9 - 0.15 * k) & (np.abs(v - (0.6 + k * 0.08)) < 0.022), 0.35, g)
    elif style == 1:    # circle emblem
        rr = np.hypot(u - 0.5, (v - 0.38) * 1.4)
        g = np.where(rr < 0.3, 0.3, g)
        g = np.where(rr < 0.18, 0.86, g)
        g = np.where((u > 0.15) & (u < 0.85) & (np.abs(v - 0.82) < 0.05), 0.3, g)
    else:               # stripes
        g = np.where(np.sin((u + v) * 22) > 0.3, 0.32, g)
        g = np.where((u > 0.1) & (u < 0.9) & (v > 0.36) & (v < 0.62), 0.86, g)
    g = g * (0.9 + 0.08 * n)
    return g, paper * keep * 0.96


def litter(rng, leaves=False):
    im, d, done = canvas()
    S = 4 * C
    gray = Image.new('L', im.size, 0)
    dg = ImageDraw.Draw(gray)
    for _ in range(rng.integers(9, 15) if leaves else rng.integers(5, 9)):
        cx, cy = rng.uniform(0.18, 0.82) * S, rng.uniform(0.18, 0.82) * S
        s = rng.uniform(0.04, 0.09) * S
        a = rng.uniform(0, np.pi)
        if leaves:
            pts = [(cx + np.cos(a + t) * s * (1 if k % 2 == 0 else 0.42), cy + np.sin(a + t) * s * (1 if k % 2 == 0 else 0.42))
                   for k, t in enumerate(np.linspace(0, 2 * np.pi, 9)[:-1])]
        else:
            w, h = s * rng.uniform(0.8, 1.4), s * rng.uniform(0.6, 1.2)
            pts = [(cx + np.cos(a) * dx - np.sin(a) * dy, cy + np.sin(a) * dx + np.cos(a) * dy)
                   for dx, dy in ((-w, -h), (w, -h * 0.8), (w * 0.9, h), (-w * 1.1, h * 0.9))]
        d.polygon(pts, fill=255)
        dg.polygon(pts, fill=int(rng.uniform(0.35, 0.95) * 255))
    a = done(0.3)
    g = np.asarray(gray.resize((C, C), Image.LANCZOS)).astype(float) / 255
    g = np.where(a > 0.01, g / np.maximum(a, 0.01), 0.6)
    return np.clip(g, 0, 1), a


def prints(rng):
    im, d, done = canvas()
    S = 4 * C
    for i in range(4):
        side = 1 if i % 2 else -1
        cx, cy = S * (0.5 + side * 0.09), S * (0.86 - i * 0.24)
        d.ellipse([cx - S * .05, cy - S * .09, cx + S * .05, cy + S * .03], fill=255)
        d.ellipse([cx - S * .04, cy + S * .045, cx + S * .04, cy + S * .095], fill=255)
    a = done(0.6) * np.clip(0.7 + 0.4 * fbm(rng, 16, 3), 0, 1)
    return np.full((C, C), 0.12), a * 0.8


def scars(rng):
    a = np.zeros((C, C))
    g = np.full((C, C), 0.1)
    for _ in range(rng.integers(3, 7)):
        cx, cy = rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8)
        r = radial(cx, cy) / rng.uniform(0.035, 0.06)
        a = np.maximum(a, ss(1.0, 0.5, r) * 0.95)
        a = np.maximum(a, ss(2.2, 1.0, r) * 0.35 * (0.6 + 0.4 * np.sin(np.arctan2(YY - cy, XX - cx) * 7 + rng.uniform(0, 6))))
    return g, a


def grime(rng, base=False):
    n = fbm(rng, 4, 5)
    if base:   # wall base band: dark at the bottom, fading up, ragged top
        a = ss(0.25 + 0.12 * n, 0.9, YY) * (0.75 + 0.25 * fbm(rng, 12, 3))
        a *= ss(0.0, 0.12, XX) * ss(1.0, 0.88, XX)
        return np.full((C, C), 0.12), np.clip(a, 0, 1)
    a = ss(0.5, 0.2, radial() * (1 + 0.25 * n)) * np.clip(0.5 + 0.5 * fbm(rng, 10, 4), 0, 1)
    return np.full((C, C), 0.16), np.clip(a, 0, 1)


def soot(rng):
    n = fbm(rng, 5, 5)
    a = ss(0.55, 0.0, radial(0.5, 0.15, 0.7, 1.6) * (1 + 0.3 * n)) * ss(0.0, 0.06, YY)
    return np.full((C, C), 0.05), np.clip(a * 0.95, 0, 1)


def moss(rng):
    n = fbm(rng, 4, 5)
    a = ss(0.48, 0.1, radial() * (1 + 0.2 * fbm(rng, 2, 3))) * np.clip(0.4 + 0.6 * (fbm(rng, 18, 3) * 0.5 + 0.5), 0, 1)
    return 0.45 + 0.15 * fbm(rng, 20, 2), np.clip(a, 0, 1)


# ---------------------------------------------------------------------------------------------------- the table
# (name, kind, painter). kind: 'floor' | 'wall' | 'any'. Order is the cell index; append only (indices are data).
def table():
    T = [
        ('oil', 'floor', lambda r: stain(r, 0.06, 0.15, 0.22, 0.4)),
        ('oil2', 'floor', lambda r: stain(r, 0.05, 0.0, 0.35, 0.36)),
        ('water', 'any', lambda r: stain(r, 0.3, 0.45, 0.18, 0.44)),
        ('water2', 'any', lambda r: stain(r, 0.28, 0.6, 0.3, 0.4)),
        ('rust', 'wall', lambda r: streak(r, 0.14, 0.32, 5)),
        ('leak', 'wall', lambda r: streak(r, 0.07, 0.12, 3, 1.0)),
        ('sootStreak', 'wall', lambda r: streak(r, 0.2, 0.05, 7, 0.7)),
        ('soot', 'any', soot),
        ('crack', 'any', lambda r: crack_cell(r, 1, 3, 1.4)),
        ('crack2', 'any', lambda r: crack_cell(r, 1, 2, 1.1)),
        ('crack3', 'any', lambda r: crack_cell(r, 2, 2, 1.0)),
        ('tyre', 'floor', tyre),
        ('scuff', 'floor', scuff),
        ('puddle', 'floor', puddle),
        ('patch', 'any', patch_cell),
        ('drain', 'floor', lambda r: disc(r, 'drain')),
        ('manhole', 'floor', lambda r: disc(r, 'manhole')),
        ('grate', 'floor', grate),
        ('arrow', 'floor', lambda r: paint_cell(r, 'arrow')),
        ('chevrons', 'any', lambda r: paint_cell(r, 'chevrons')),
    ]
    for dgt in '0123456789':
        T.append(('digit' + dgt, 'any', lambda r, dgt=dgt: text_cell(r, [dgt], 0.62)))
    T += [
        ('stencilExit', 'wall', lambda r: text_cell(r, ['EXIT'], 0.3)),
        ('stencilZone', 'wall', lambda r: text_cell(r, ['ZONE', 'B-2'], 0.28)),
        ('stencilNo', 'wall', lambda r: text_cell(r, ['NO', 'PARKING'], 0.24)),
        ('poster', 'wall', lambda r: poster(r, 0)),
        ('poster2', 'wall', lambda r: poster(r, 1)),
        ('poster3', 'wall', lambda r: poster(r, 2)),
        ('paper', 'floor', lambda r: litter(r, False)),
        ('leaves', 'floor', lambda r: litter(r, True)),
        ('prints', 'floor', prints),
        ('scars', 'wall', scars),
        ('scars2', 'wall', scars),
        ('grime', 'any', lambda r: grime(r)),
        ('grime2', 'any', lambda r: grime(r)),
        ('grimeBase', 'wall', lambda r: grime(r, True)),
        ('moss', 'any', moss),
        ('stencilDanger', 'wall', lambda r: text_cell(r, ['DANGER'], 0.3)),
    ]
    return T


def build():
    T = table()
    assert len(T) <= G * G
    rgba = np.zeros((G * C, G * C, 4), np.uint8)
    for i, (name, kind, fn) in enumerate(T):
        rng = np.random.default_rng(9100 + i)
        g, a = fn(rng)
        a = np.clip(a, 0, 1) * border()
        g = np.clip(g, 0, 1)
        y, x = (i // G) * C, (i % G) * C
        gv = np.round(g * 255).astype(np.uint8)
        rgba[y:y + C, x:x + C, 0] = gv
        rgba[y:y + C, x:x + C, 1] = gv
        rgba[y:y + C, x:x + C, 2] = gv
        rgba[y:y + C, x:x + C, 3] = np.round(a * 255).astype(np.uint8)
    return T, rgba


def main():
    T, rgba = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    Image.fromarray(rgba, 'RGBA').save(OUT, 'WEBP', quality=88, alpha_quality=90, method=6)
    names = [t[0] for t in T]
    js = ('/* generated by tools/gen_decals.py: decal atlas cells (assets/tex/decals.webp, 8 x 8 cells). Do not edit. */\n'
          'window.IB = window.IB || {};\nIB.DECALS = ' + json.dumps({
              'grid': G, 'names': names, 'cell': {n: i for i, n in enumerate(names)},
              'kind': {t[0]: t[1] for t in T}}, separators=(',', ':')) + ';\n')
    open(OUT_JS, 'w').write(js)
    print('decals', OUT, os.path.getsize(OUT), 'bytes,', len(T), 'cells')
    if '--preview' in sys.argv:
        p = sys.argv[sys.argv.index('--preview') + 1]
        bg = Image.new('RGB', (G * C, G * C), (150, 140, 128))
        im = Image.fromarray(rgba, 'RGBA')
        bg.paste(im.convert('RGB'), mask=im.split()[3])
        bg.save(p, quality=85)


if __name__ == '__main__':
    main()
