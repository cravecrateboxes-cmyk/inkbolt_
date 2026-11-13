#!/usr/bin/env python3
"""Detail texture array generator (tileable material micro-detail for the surface shader).

    python3 Source/tools/gen_detail.py

Writes
    Source/assets/tex/detail-a.webp     512 x 7168, 14 layers of 512 x 512 stacked top to bottom (layer 0 at the top)
    Source/assets/tex/detail-n.webp     same layout, the layers' tangent-space normals
    Source/dist/look/detail-preview.jpg review sheet: every layer tiled 3 x 3, lit from the upper left

The surface shader samples these triplanar in world space (tile sizes 0.5 - 3 m) and MULTIPLIES a flat palette colour
and gloss by them, so everything here is subtle: the albedo multiplier is mostly within x0.8 - x1.2 (mortar, grout and
cracks go down to ~x0.6) and every layer is renormalised so its mean albedo and gloss multiplier are exactly x1.0.

Layers (index = layer = row in the strip; the tile size noted is the one the geometry below is drawn for)
    0  macro      soft blotches; sampled on every class at 1/6 scale to break up repetition
    1  concrete   2.4 m: fine pits, formwork panel joints (1.2 x 2.4 m panels: vertical joints at x = 0 and 1/2,
                  horizontal joint at y = 0), round tie holes on a 0.6 m grid, hairline cracks
    2  brushed    brushed metal: horizontal anisotropic streaks, sparse scratches, small scattered tarnish specks (gloss)
    3  painted    painted metal: near-smooth paint, small chips, a horizontal and a vertical seam with spot welds
    4  planks     1.2 m: 8 boards (15 cm) running along x, staggered butt ends, grain, a few knots
    5  weave      fabric / canvas, plain over-under weave, 64 threads a tile
    6  ground     soil clumps and pebbles
    7  foliage    leaf clusters
    8  rock       warped strata of irregular thickness, low ledges, joints / cracks
    9  brick      running bond, 6 bricks across, 16 courses up, recessed mortar, per-brick tone, worn edges
    10 tile       0.6 m: 2 x 2 tiles of 30 cm, grout, a few chipped corners
    11 asphalt    aggregate, many thin irregular cracks spread over the tile
    12 snow       soft wind drifts and ripples, sparkle in the gloss channel
    13 plaster    smooth paint / plaster: orange peel and scuffs

Packing (opaque RGB only, never data in an alpha channel)
    detail-a  R = albedo multiplier   128 = x1.0, value = 128 + (mul - 1) * 320 clamped to 0..255 (x0.6 -> 0)
              G = gloss multiplier    same encoding
              B = height              0..255, per layer min..max
    detail-n  R = normal x, G = normal y, 128 = flat, value = 128 + n * 127; B = 128 (unused).
              Normals are OpenGL convention: +x = right, +y = UP the image (towards row 0 of the layer); z is
              reconstructed as sqrt(1 - x^2 - y^2).

Every field is built periodic (Fourier-filtered noise, cellular patterns with wrap-around distance, grids with
integer periods, strokes splatted modulo the tile, normals by periodic central differences), so each layer tiles.
The run self-checks the DECODED files (seams, means, normal validity) and exits non-zero on failure.
Deterministic: fixed seeds.
"""
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
OUT_A = os.path.join(SRC, 'assets', 'tex', 'detail-a.webp')
OUT_N = os.path.join(SRC, 'assets', 'tex', 'detail-n.webp')
OUT_PREVIEW = os.path.join(SRC, 'dist', 'look', 'detail-preview.jpg')

N = 512
NAMES = ['macro', 'concrete', 'brushed metal', 'painted metal', 'planks', 'weave', 'ground', 'foliage', 'rock',
         'brick', 'tile', 'asphalt', 'snow', 'plaster']
Q_A = 90
Q_N = 90            # set to None for lossless normals
SIZE_BUDGET = 1.8e6

_k = np.fft.fftfreq(N, 1.0 / N)
KY, KX = np.meshgrid(_k, _k, indexing='ij')            # integer cycles per tile
YY, XX = np.meshgrid(np.arange(N) + 0.5, np.arange(N) + 0.5, indexing='ij')   # pixel centres


# ----------------------------------------------------------------------------------------------------------- toolkit
def noise(rng, f0, f1, slope=1.0, ax=1.0, ay=1.0):
    """Band-limited periodic noise, zero mean, unit std. f0..f1 in cycles per tile; ax > 1 stretches it along x."""
    F = np.fft.fft2(rng.standard_normal((N, N)))
    r = np.sqrt((KX * ax) ** 2 + (KY * ay) ** 2)
    r[0, 0] = 1e-6
    w = r ** (-slope) / (1 + (f0 / r) ** 4) / (1 + (r / f1) ** 4)
    w[0, 0] = 0
    out = np.real(np.fft.ifft2(F * w))
    return (out - out.mean()) / (out.std() + 1e-12)


def blur(img, s):
    """Periodic gaussian blur, sigma in pixels."""
    g = np.exp(-2 * (np.pi * s) ** 2 * ((KX / N) ** 2 + (KY / N) ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(img) * g))


def wrapd(d):
    return (d + N / 2) % N - N / 2


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def worley(rng, g, jitter=0.9):
    """Jittered-grid cellular noise with wrap-around distance: (F1, F2, id of nearest, dx, dy to nearest) in pixels."""
    cs = N / g
    jx = (np.arange(g)[None, :] + 0.5 + jitter * (rng.random((g, g)) - 0.5)) * cs
    jy = (np.arange(g)[:, None] + 0.5 + jitter * (rng.random((g, g)) - 0.5)) * cs
    ci = np.floor(YY / cs).astype(int)
    cj = np.floor(XX / cs).astype(int)
    f1 = np.full((N, N), 1e9)
    f2 = np.full((N, N), 1e9)
    idn = np.zeros((N, N), int)
    ddx = np.zeros((N, N))
    ddy = np.zeros((N, N))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ni = (ci + di) % g
            nj = (cj + dj) % g
            dx = wrapd(jx[ni, nj] - XX)
            dy = wrapd(jy[ni, nj] - YY)
            d = np.hypot(dx, dy)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            f1 = np.where(closer, d, f1)
            idn = np.where(closer, ni * g + nj, idn)
            ddx = np.where(closer, dx, ddx)
            ddy = np.where(closer, dy, ddy)
    return f1, f2, idn, ddx, ddy


def splat(acc, xs, ys, w):
    """Bilinear splat of points (pixel coords, centre convention) into acc, modulo the tile."""
    xs = np.asarray(xs) - 0.5
    ys = np.asarray(ys) - 0.5
    w = np.broadcast_to(w, xs.shape)
    x0 = np.floor(xs)
    y0 = np.floor(ys)
    fx = xs - x0
    fy = ys - y0
    x0 = x0.astype(int)
    y0 = y0.astype(int)
    for oy, wy in ((0, 1 - fy), (1, fy)):
        for ox, wx in ((0, 1 - fx), (1, fx)):
            np.add.at(acc, ((y0 + oy) % N, (x0 + ox) % N), w * wx * wy)


def stroke(acc, pts, w):
    """Splat a polyline (array of (x, y)) sampled every 0.5 px; w is a scalar or a per-vertex weight array."""
    pts = np.asarray(pts, float)
    seg = np.diff(pts, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    t = np.concatenate([[0], np.cumsum(ln)])
    s = np.arange(0, t[-1], 0.5)
    x = np.interp(s, t, pts[:, 0])
    y = np.interp(s, t, pts[:, 1])
    ww = np.interp(s, t, np.broadcast_to(w, t.shape).astype(float))
    splat(acc, x, y, ww)


def line_mask(acc, sigma):
    """Turn splatted strokes into a 0..1 mask (a weight-1 stroke peaks at ~1)."""
    peak = 2.0 / (np.sqrt(2 * np.pi) * max(sigma, 0.3))
    return np.clip(blur(acc, sigma) / peak, 0, 1)


def walk(rng, x, y, a, length, wiggle, drift=0.0):
    da = rng.normal(0, wiggle, int(length)) + drift
    da -= da.mean() * 0.5                                    # no net curling
    ang = a + np.cumsum(da)
    xs = x + np.concatenate([[0], np.cumsum(np.cos(ang))])
    ys = y + np.concatenate([[0], np.cumsum(np.sin(ang))])
    return np.stack([xs, ys], 1), ang


def cracks(rng, count, length, wiggle, branch=2, angle=None, taper=True):
    """Branching random-walk cracks; returns the splat accumulator."""
    acc = np.zeros((N, N))
    for _ in range(count):
        a0 = rng.uniform(0, 2 * np.pi) if angle is None else angle + rng.normal(0, 0.25)
        todo = [(rng.uniform(0, N), rng.uniform(0, N), a0, length * rng.uniform(0.6, 1.2), 1.0)]
        while todo:
            x, y, a, L, wt = todo.pop()
            pts, ang = walk(rng, x, y, a, L, wiggle)
            t = np.linspace(0, 1, len(pts))
            w = wt * (np.sqrt(np.sin(np.pi * np.clip(t, 0, 1)) + 0.05) if taper else np.ones_like(t))
            stroke(acc, pts, w)
            if wt > 0.5:
                for _ in range(branch):
                    k = rng.integers(len(pts) // 5, max(len(pts) // 5 + 1, len(pts) - 2))
                    todo.append((pts[k, 0], pts[k, 1], ang[min(k, len(ang) - 1)] + rng.choice([-1, 1]) *
                                 rng.uniform(0.5, 1.1), L * rng.uniform(0.25, 0.45), wt * 0.6))
    return acc


def grid_dist(coord, period, offset=0.0):
    """Distance from coord to the nearest line at offset + k * period (periodic)."""
    u = (coord - offset) % period
    return np.minimum(u, period - u)


# ------------------------------------------------------------------------------------------------------------ layers
# Each returns (height in pixel units, albedo multiplier, gloss multiplier).
def l_macro(rng):
    h = noise(rng, 1.5, 24, 1.6)
    b = noise(rng, 2, 40, 1.3)
    blot = smoothstep(0.2, 1.6, b)
    a = 1 + 0.07 * h - 0.10 * blot + 0.02 * noise(rng, 20, 80, 1.0)
    g = 1 + 0.10 * noise(rng, 1.5, 20, 1.5) - 0.12 * blot
    return h * 3.0 + blot * 2.0, a, g


def l_concrete(rng):
    base = noise(rng, 3, 60, 1.4)
    fine = noise(rng, 60, 200, 0.5)
    h = 0.6 * base + 0.15 * fine
    a = 1 + 0.04 * base + 0.02 * fine + 0.05 * noise(rng, 1, 8, 1.5)
    # bug holes: small air pits
    f1, _, idn, _, _ = worley(rng, 70)
    rr = np.random.default_rng(11).random(70 * 70)
    rad = np.where(rr < 0.12, 0.7 + 1.9 * np.random.default_rng(12).random(70 * 70), 0)[idn]
    pit = smoothstep(rad + 0.6, rad - 0.6, f1) * (rad > 0)
    h -= 2.2 * pit
    a -= 0.25 * pit
    # formwork joints (panel 1.2 x 2.4 m on a 2.4 m tile): vertical every N/2, horizontal every N; phase N/4 so no
    # joint sits on the tile edge
    dv = grid_dist(XX, N / 2, N / 4)
    dh = grid_dist(YY, N, N / 4)
    fin = np.exp(-(dv / 2.0) ** 2) + 0.8 * np.exp(-(dh / 2.0) ** 2)
    gap = np.maximum(np.exp(-(dv / 1.0) ** 2), 0.8 * np.exp(-(dh / 1.0) ** 2))
    h += 1.6 * fin - 2.4 * gap
    a -= 0.30 * gap - 0.04 * fin
    # tie holes: 0.3 / 0.9 m into each panel, rows every 0.6 m
    tie = np.zeros((N, N))
    for cx in (64, 192, 320, 448):
        for cy in (64, 192, 320, 448):
            d = np.hypot(wrapd(XX - cx), wrapd(YY - cy))
            tie = np.maximum(tie, smoothstep(6.0, 4.4, d) * (0.6 + 0.4 * smoothstep(5, 0, d)))
            h += 0.8 * np.exp(-((d - 7.0) / 1.5) ** 2)
            a -= 0.06 * np.exp(-((d - 7.5) / 2.5) ** 2)
    h -= 4.0 * tie
    a -= 0.40 * tie
    # hairline cracks
    cm = line_mask(cracks(rng, 4, 260, 0.12, branch=2), 0.55)
    h -= 1.2 * cm
    a -= 0.25 * cm
    g = 1 - 0.08 * base - 0.25 * pit - 0.3 * tie - 0.15 * cm + 0.05 * noise(rng, 4, 40, 1.0)
    return h, a, g


def l_brushed(rng):
    streak = noise(rng, 6, 200, 0.6, ax=40)
    band = noise(rng, 2, 40, 1.0, ax=12)
    h = 0.35 * streak + 0.3 * band
    a = 1 + 0.035 * streak + 0.03 * band
    g = 1 + 0.10 * streak + 0.06 * band
    # scratches
    acc = np.zeros((N, N))
    for _ in range(55):
        x, y = rng.uniform(0, N, 2)
        ang = rng.normal(0, 0.5) if rng.random() < 0.6 else rng.uniform(0, np.pi)
        L = rng.uniform(15, 140)
        pts, _ = walk(rng, x, y, ang, L, 0.01)
        stroke(acc, pts, rng.uniform(0.4, 1.0))
    sc = line_mask(acc, 0.45)
    h -= 0.8 * sc
    a += 0.12 * sc
    g += 0.2 * sc
    # tarnish / rust specks: small and scattered, mostly a gloss change (albedo under ~5 %)
    rb = noise(rng, 14, 90, 0.7) + 0.5 * noise(rng, 2, 12, 1.2)
    rust = smoothstep(1.5, 2.6, rb)
    pits = noise(rng, 50, 180, 0.4)
    h += rust * (0.3 * pits + 0.3)
    a -= 0.035 * rust + 0.01 * rust * pits
    g *= (1 - 0.35 * rust) * (1 + 0.06 * noise(rng, 3, 50, 1.0))
    return h, a, g


def l_painted(rng):
    peel = noise(rng, 40, 140, 0.5)
    low = noise(rng, 2, 30, 1.4)
    h = 0.12 * peel + 0.3 * low
    a = 1 + 0.025 * low + 0.008 * peel
    g = 1 + 0.05 * low
    # seams: horizontal at y = N/4 (with spot welds), vertical at x = N * 5/8
    dh = grid_dist(YY, N, N / 4)
    dv = grid_dist(XX, N, N * 5 / 8)
    seam = np.maximum(np.exp(-(dh / 1.4) ** 2), np.exp(-(dv / 1.4) ** 2))
    lip = np.exp(-((dh - 3.2) / 1.5) ** 2) + np.exp(-((dv - 3.2) / 1.5) ** 2)
    h += -3.0 * seam + 0.5 * lip
    a -= 0.28 * seam
    g -= 0.25 * seam
    weld = np.zeros((N, N))
    for k in range(16):
        d = np.hypot(grid_dist(XX, N, k * 32 + 16), wrapd(YY - N / 4 - 9))
        weld = np.maximum(weld, smoothstep(4.0, 2.0, d) * (1 - 0.3 * (d / 4.0) ** 2))
    h += 1.2 * weld
    a -= 0.05 * weld
    # chips: irregular blobs where the paint is gone (step down, darker, duller, light rim)
    edge = noise(rng, 30, 120, 0.6)
    chip = np.zeros((N, N))
    for _ in range(18):
        cx, cy = rng.uniform(0, N, 2)
        r = rng.uniform(2.0, 7.5)
        el = rng.uniform(0.6, 1.6)
        d = np.hypot(wrapd(XX - cx) * el, wrapd(YY - cy) / el) + 1.6 * edge
        chip = np.maximum(chip, smoothstep(r + 0.7, r - 0.7, d))
    # bias chips to the seam edges a little
    for k in range(6):
        cx = rng.uniform(0, N)
        d = np.hypot(wrapd(XX - cx) / 1.8, wrapd(YY - N / 4 - rng.choice([4.0, -4.0]))) + 1.6 * edge
        chip = np.maximum(chip, smoothstep(5.5, 4.0, d))
    rim = np.clip(blur(chip, 1.2) - chip, 0, 1) * 2
    h -= 1.5 * blur(chip, 0.4)
    a += -0.3 * chip + 0.06 * rim
    g -= 0.5 * chip
    return h, a, g


def l_planks(rng):
    boards = 8
    bh = N // boards
    Y = (YY - bh / 2) % N                                    # board gaps half a board off the tile edge
    row = (Y // bh).astype(int) % boards
    vy = Y - row * bh                                        # 0..bh within the board
    grainf = noise(rng, 2, 160, 1.0, ax=18)
    fine = noise(rng, 30, 200, 0.5, ax=25)
    rings = noise(rng, 1, 12, 1.2, ax=3)
    h = np.zeros((N, N))
    a = np.ones((N, N))
    g = np.ones((N, N))
    tone = np.zeros((N, N))
    grain = np.zeros((N, N))
    joint = np.zeros((N, N))
    for b in range(boards):
        m = row == b
        nj = 1 if rng.random() < 0.55 else 2
        xs = np.sort(rng.uniform(0, N, nj))
        if nj == 2 and (xs[1] - xs[0] < 140 or N - xs[1] + xs[0] < 140):
            xs[1] = (xs[0] + rng.uniform(170, N - 170)) % N
            xs = np.sort(xs)
        seg = (np.searchsorted(xs, XX[m]) % nj)
        for s in range(nj):
            ms = np.zeros((N, N), bool)
            ms[m] = seg == s
            shx = rng.integers(0, N)
            shy = rng.integers(0, N)
            # flat-sawn figure: banded rings, warped, plus streaks along the board
            fig = np.roll(np.roll(rings, shx, 1), shy, 0)
            sx = np.roll(np.roll(grainf, shx, 1), shy, 0)
            ff = np.roll(np.roll(fine, shx, 1), shy, 0)
            band = np.sin(2 * np.pi * (0.06 * vy + 1.1 * fig + rng.uniform(0, 1)) * rng.uniform(1.2, 2.2))
            gr = 0.45 * band + 0.35 * sx + 0.3 * ff
            grain[ms] = gr[ms]
            tone[ms] = rng.normal(0, 0.06)
        for x in xs:
            d = grid_dist(XX, N, x)
            joint = np.maximum(joint, np.exp(-(d / 0.9) ** 2) * m)
    gap = np.exp(-(grid_dist(YY, bh, bh / 2) / 1.1) ** 2)
    edge = smoothstep(1.0, 6.0, np.minimum(vy, bh - vy))
    h += 0.45 * grain + 2.0 * edge - 2.5 * gap - 2.5 * joint + 0.2 * blur(noise(rng, 2, 20, 1.2), 1)
    a += tone + 0.07 * grain - 0.38 * np.maximum(gap, joint) - 0.05 * (1 - edge)
    g += 0.12 * grain - 0.3 * np.maximum(gap, joint)
    # knots
    for _ in range(4):
        b = rng.integers(0, boards)
        cx = rng.uniform(0, N)
        cy = b * bh + bh / 2 + rng.uniform(18, bh - 18)
        dx = wrapd(XX - cx)
        dy = wrapd(YY - cy)
        r = np.hypot(dx / 1.6, dy)
        rk = rng.uniform(4, 7)
        same = row == b
        ring = np.sin(r * 1.3) * np.exp(-((r - rk) / (rk * 1.8)) ** 2) * same
        core = smoothstep(rk, rk * 0.5, r) * same
        h += 0.8 * ring - 0.8 * core
        a += 0.05 * ring - 0.28 * core
        g -= 0.2 * core
    return h, a, g


def l_weave(rng):
    p = 16                                                   # 32 threads a tile each way
    X = (XX + p / 2) % N                                     # tile edge runs along a thread, not a gap
    Y = (YY + p / 2) % N
    ix = (X // p).astype(int)
    iy = (Y // p).astype(int)
    u = (X % p) / p
    v = (Y % p) / p
    sx = np.where(ix % 2 == 0, 1.0, -1.0)
    sy = np.where(iy % 2 == 0, 1.0, -1.0)
    slub_w = noise(rng, 1, 40, 0.8, ax=1, ay=10)             # varies along the warp (vertical) threads
    slub_f = noise(rng, 1, 40, 0.8, ax=10, ay=1)
    thw = 0.44 + 0.04 * slub_w
    thf = 0.44 + 0.04 * slub_f
    across_w = np.sqrt(np.clip(1 - ((u - 0.5) / thw) ** 2, 0, 1))
    across_f = np.sqrt(np.clip(1 - ((v - 0.5) / thf) ** 2, 0, 1))
    und_w = 0.5 + 0.5 * sx * np.sin(np.pi * Y / p)
    und_f = 0.5 - 0.5 * sy * np.sin(np.pi * X / p)
    hw = across_w * (0.35 + 0.65 * und_w)
    hf = across_f * (0.35 + 0.65 * und_f)
    top_w = hw >= hf
    hh = np.maximum(hw, hf)
    # twist: fine diagonal fibre lines along each thread
    twist_w = np.sin(2 * np.pi * (Y / 4.0 + X / 8.0))
    twist_f = np.sin(2 * np.pi * (X / 4.0 - Y / 8.0))
    twist = np.where(top_w, twist_w, twist_f) * smoothstep(0.2, 0.7, hh)
    fib = noise(rng, 60, 180, 0.3)
    rngw = np.random.default_rng(5)
    tw = rngw.normal(0, 0.03, N // p)[ix]
    tf = rngw.normal(0, 0.03, N // p)[iy]
    h = 3.0 * hh + 0.15 * twist + 0.08 * fib + 0.3 * noise(rng, 2, 16, 1.4)
    a = 1 + np.where(top_w, tw + 0.025 * slub_w, tf + 0.025 * slub_f) - 0.30 * (1 - smoothstep(0.0, 0.55, hh)) \
        + 0.02 * twist + 0.01 * fib + 0.03 * noise(rng, 1, 8, 1.4)
    g = 1 - 0.3 * (1 - smoothstep(0.0, 0.6, hh)) + 0.02 * fib
    return h, a, g


def l_ground(rng):
    f1, f2, idn, _, _ = worley(rng, 14)
    clump = smoothstep(0, 1, (f2 - f1) / 10.0)
    cid = np.random.default_rng(21).random(14 * 14)[idn]
    soil = noise(rng, 4, 90, 1.1)
    grit = noise(rng, 70, 180, 0.4)
    h = 3.5 * clump * (0.6 + 0.4 * cid) + 1.2 * soil + 0.15 * grit
    a = 1 + 0.06 * soil + 0.02 * grit + 0.08 * (cid - 0.5) - 0.2 * (1 - smoothstep(0.0, 0.5, clump))
    g = 1 - 0.08 * soil + 0.02 * grit
    # pebbles: sparse, varied size, domed, own tone, slightly glossier
    for gsz, frac, rmin, rmax in ((40, 0.25, 3.0, 6.5), (90, 0.18, 1.2, 2.6)):
        p1, _, pid, pdx, pdy = worley(rng, gsz, 0.8)
        pr = np.random.default_rng(gsz).random((3, gsz * gsz))
        rad = np.where(pr[0] < frac, rmin + (rmax - rmin) * pr[1], 0)[pid]
        el = (0.7 + 0.6 * pr[2])[pid]
        d = np.hypot(pdx * el, pdy / el)
        inside = (d < rad) & (rad > 0)
        dome = np.where(inside, np.sqrt(np.clip(1 - (d / np.maximum(rad, 1e-3)) ** 2, 0, 1)), 0)
        ptone = (pr[1] - 0.5)[pid] * 0.5 + (pr[2] - 0.5)[pid] * 0.2
        h = np.where(inside, np.maximum(h, h * 0.4 + 2.0 + rad * 0.8 * dome), h)
        cover = smoothstep(rad, rad - 0.8, d) * (rad > 0)
        a += cover * (0.12 + ptone + 0.05 * dome)
        g += cover * 0.25
        ao = np.clip(blur(cover, 1.5) - cover, 0, 1)
        a -= 0.25 * ao
    return h, a, g


def l_foliage(rng):
    h = np.full((N, N), -6.0)
    tone = np.zeros((N, N))
    vein = np.zeros((N, N))
    nc = 56
    cxs = rng.uniform(0, N, nc)
    cys = rng.uniform(0, N, nc)
    for c in range(nc):
        ctone = rng.normal(0, 0.035)
        rc = rng.uniform(30, 55)
        for _ in range(rng.integers(60, 95)):
            off = rng.normal(0, rc * 0.45, 2)
            dist = np.hypot(*off)
            cx = cxs[c] + off[0]
            cy = cys[c] + off[1]
            th = np.arctan2(off[1], off[0]) + rng.normal(0, 0.5)
            L = rng.uniform(14, 26)
            W = L * rng.uniform(0.38, 0.55)
            base = 4.0 * max(0, 1 - dist / rc) + rng.uniform(0, 2.5)
            R = int(L / 2 + 2)
            oy, ox = np.mgrid[-R:R + 1, -R:R + 1]
            fx = cx - np.floor(cx)
            fy = cy - np.floor(cy)
            dx = ox + 0.5 - fx
            dy = oy + 0.5 - fy
            uu = (dx * np.cos(th) + dy * np.sin(th)) / (L / 2)
            vv = (-dx * np.sin(th) + dy * np.cos(th)) / (W / 2)
            shape = (1 - uu ** 2) * (1 + 0.25 * uu)
            ins = (np.abs(uu) < 1) & (vv ** 2 < np.maximum(shape, 0) ** 2)
            if not ins.any():
                continue
            dome = np.sqrt(np.clip(1 - (vv / np.maximum(shape, 1e-3)) ** 2, 0, 1)) * np.maximum(shape, 0)
            rib = np.exp(-(vv / 0.09) ** 2)
            lh = base + 1.6 * dome - 0.35 * rib - 1.0 * uu
            ys = (int(np.floor(cy)) + oy) % N
            xs = (int(np.floor(cx)) + ox) % N
            cur = h[ys, xs]
            win = ins & (lh > cur)
            h[ys[win], xs[win]] = lh[win]
            tone[ys[win], xs[win]] = ctone + rng.normal(0, 0.045) - 0.03 * uu[win]
            vein[ys[win], xs[win]] = rib[win]
    leaf = h > -5
    occl = smoothstep(-2.0, 5.0, h)
    h = np.where(leaf, h, -3.0 + 0.5 * blur(noise(rng, 10, 100, 0.8), 1))
    a = 1 + np.where(leaf, tone + 0.05 * vein, -0.22) - 0.08 * (1 - occl)
    g = np.where(leaf, 1.12 + 0.1 * vein, 0.65) - 0.15 * (1 - occl)
    return h, a, g


def l_rock(rng):
    n = 11
    warp = 16 * noise(rng, 1, 5, 1.5) + 3 * noise(rng, 6, 30, 1.0)
    yw = YY + warp
    srng = np.random.default_rng(31)
    thick = srng.uniform(0.5, 1.6, n)                         # irregular bed thicknesses, fractions of the tile
    edges = np.concatenate([[0], np.cumsum(thick / thick.sum())])
    t = (yw / N) % 1.0
    idx = np.clip(np.searchsorted(edges, t, side='right') - 1, 0, n - 1)
    fr = (t - edges[idx]) / (edges[idx + 1] - edges[idx])
    s = t * n
    lvl = srng.uniform(0, 1, n)
    btone = srng.normal(0, 0.07, n)
    hard = srng.uniform(0.3, 1, n)
    rough = noise(rng, 6, 180, 1.0)
    fine = noise(rng, 50, 180, 0.5)
    ledge = smoothstep(0.0, 0.10, fr) * (1 - 0.6 * smoothstep(0.6, 1.0, fr))   # sharp lip at the bottom of a band
    bpx = (edges[idx + 1] - edges[idx]) * N                  # bed thickness in pixels
    h = 3.5 * lvl[idx] + 2.1 * ledge + rough * (1.0 + hard[idx]) + 0.15 * fine
    line = np.exp(-(np.minimum(fr, 1 - fr) * bpx / 1.8) ** 2)         # bedding plane, ~2 px
    lam = np.sin(2 * np.pi * s * 5 + 0.5 * rough) * (1 - hard[idx])     # thin laminae in the soft beds
    a = 1 + 0.9 * btone[idx] + 0.04 * rough + 0.03 * fine + 0.03 * lam - 0.15 * line
    h += 0.3 * lam
    g = 1 + 0.08 * rough - 0.14 * line
    # vertical joints and random cracks
    cm = line_mask(cracks(rng, 5, 150, 0.08, branch=1, angle=np.pi / 2), 0.7)
    cm2 = line_mask(cracks(rng, 6, 110, 0.14, branch=1), 0.55)
    c = np.maximum(cm, 0.8 * cm2)
    h -= 3.5 * blur(c, 0.6)
    a -= 0.3 * c
    g -= 0.25 * c
    return h, a, g


def l_brick(rng):
    cols, courses = 6, 16
    bw = N / cols
    ch = N / courses
    Y = (YY + ch / 2) % N                                     # bed joints half a course off the tile edge
    course = (Y // ch).astype(int) % courses
    off = np.where(course % 2 == 0, bw / 4, bw * 3 / 4)       # head joints off the tile edge
    bx = ((XX - off) // bw).astype(int) % cols
    bid = course * cols + bx
    vy = Y - course * ch
    vx = (XX - off) % bw
    edge_n = noise(rng, 20, 120, 0.8)
    mort = 2.0
    d = np.minimum(np.minimum(vx, bw - vx), np.minimum(vy, ch - vy)) - mort + 0.9 * edge_n
    body = smoothstep(-0.5, 2.5, d)
    brng = np.random.default_rng(41)
    btone = brng.normal(0, 0.055, cols * courses)[bid]
    bsurf = noise(rng, 8, 200, 0.9)
    pores = noise(rng, 80, 180, 0.4)
    mt = noise(rng, 30, 180, 0.6)
    h = body * (3.0 + 0.4 * bsurf + 0.08 * pores) + (1 - body) * (0.3 * mt)
    a = 1 + body * (btone + 0.035 * bsurf + 0.015 * pores) + (1 - body) * (-0.26 + 0.04 * mt)
    g = 1 + body * 0.06 * bsurf - (1 - body) * 0.35
    # mortar shadow line under each brick (rake)
    a -= 0.08 * smoothstep(1.5, -0.5, d) * smoothstep(-3, -0.5, d)
    return h, a, g


def l_tile(rng):
    ts = N / 2
    gw = 2.2
    tx = grid_dist(XX, ts, ts / 2)                            # grout a quarter tile off the edge
    ty = grid_dist(YY, ts, ts / 2)
    d = np.minimum(tx, ty) - gw
    tid = (((XX + ts / 2) // ts).astype(int) % 2) + 2 * (((YY + ts / 2) // ts).astype(int) % 2)
    trng = np.random.default_rng(51)
    ttone = trng.normal(0, 0.03, 4)[tid]
    body = smoothstep(-0.3, 2.2, d)
    wav = noise(rng, 1, 12, 1.5)
    gr = noise(rng, 40, 180, 0.5)
    h = body * (2.5 + 0.25 * wav) + (1 - body) * 0.25 * gr
    a = 1 + body * (ttone + 0.012 * wav) + (1 - body) * (-0.33 + 0.05 * gr)
    g = 1 + body * (0.15 + 0.03 * wav) - (1 - body) * 0.55
    # chipped corners / edges
    en = noise(rng, 20, 100, 0.8)
    for (cx, cy, r) in ((128, 128, 9.0), (384, 384, 6.5), (384, 128, 5.0), (256, 384, 4.5)):
        dd = np.hypot(wrapd(XX - cx), wrapd(YY - cy)) + 1.5 * en
        ch = smoothstep(r + 0.5, r - 0.5, dd) * body
        h -= 1.6 * ch
        a -= 0.18 * ch
        g -= 0.5 * ch
    # faint light scratches
    acc = np.zeros((N, N))
    for _ in range(12):
        pts, _ = walk(rng, *rng.uniform(0, N, 2), rng.uniform(0, 6.3), rng.uniform(20, 70), 0.02)
        stroke(acc, pts, 0.6)
    sc = line_mask(acc, 0.5) * body
    a += 0.04 * sc
    g -= 0.2 * sc
    return h, a, g


def l_asphalt(rng):
    f1, _, sid, sdx, sdy = worley(rng, 96, 0.9)
    sr = np.random.default_rng(61).random((2, 96 * 96))
    rad = (1.8 + 2.0 * sr[0])[sid]
    stone = np.sqrt(np.clip(1 - (f1 / rad) ** 2, 0, 1))
    stone_t = (sr[1] - 0.5)[sid]
    g1, _, lid, _, _ = worley(rng, 40, 0.9)
    lr = np.random.default_rng(62).random((2, 1600))
    lrad = np.where(lr[0] < 0.3, 2.5 + 2.5 * lr[1], 0)[lid]
    big = np.where(lrad > 0, np.sqrt(np.clip(1 - (g1 / np.maximum(lrad, 1e-3)) ** 2, 0, 1)), 0)
    binder = noise(rng, 2, 40, 1.2)
    h = 1.0 * stone + 1.6 * big + 0.4 * binder
    agg = np.maximum(stone > 0.05, big > 0.05)
    a = 1 + 0.03 * binder + np.where(agg, 0.10 + 0.16 * stone_t, -0.12) + 0.12 * (big > 0.05)
    g = 1 + np.where(agg, 0.12, -0.1) + 0.05 * binder
    # many thin irregular cracks of moderate length, spread so none dominates the tile
    cm = line_mask(cracks(rng, 16, 110, 0.22, branch=2), 0.5)
    h -= 2.5 * cm
    a -= 0.45 * cm
    g -= 0.25 * cm
    return h, a, g


def l_snow(rng):
    drift = noise(rng, 1, 10, 1.6, ax=2.5)
    rip = noise(rng, 8, 60, 1.0, ax=5)
    rip = np.sign(rip) * np.abs(rip) ** 0.8
    soft = noise(rng, 30, 140, 0.8)
    h = 7.0 * drift + 1.0 * rip + 0.12 * soft
    a = 1 + 0.03 * drift + 0.015 * soft - 0.03 * np.clip(-rip, 0, 2)
    g = 0.95 + 0.03 * soft
    sp = np.random.default_rng(71).random((N, N))
    spark = (sp < 0.0015).astype(float)
    spark = np.clip(blur(spark, 0.5) * 3.0, 0, 1)
    g += 0.5 * spark
    return h, a, g


def l_plaster(rng):
    f1, f2, _, _, _ = worley(rng, 64, 1.0)
    peel = -(f1 / (N / 64)) ** 1.5
    peel = (peel - peel.mean()) / peel.std()
    trowel = noise(rng, 2, 25, 1.3, ax=1.8)
    h = 0.35 * peel + 0.9 * trowel
    a = 1 + 0.03 * trowel + 0.012 * peel + 0.025 * noise(rng, 1, 8, 1.5)
    g = 1 + 0.06 * peel + 0.05 * trowel
    # scuffs: short curved rubbing strokes, darker, a little glossier; a few small dings
    acc = np.zeros((N, N))
    for _ in range(9):
        x, y = rng.uniform(0, N, 2)
        a0 = rng.normal(0, 0.35) + rng.choice([0, np.pi])
        for _k in range(rng.integers(2, 5)):
            pts, _ = walk(rng, x + rng.normal(0, 3), y + rng.normal(0, 4), a0 + rng.normal(0, 0.1),
                          rng.uniform(25, 90), 0.025, drift=rng.normal(0, 0.008))
            stroke(acc, pts, rng.uniform(0.3, 0.9))
    sc = line_mask(acc, 1.3)
    a -= 0.2 * sc
    g += 0.25 * sc
    for _ in range(7):
        cx, cy = rng.uniform(0, N, 2)
        d = np.hypot(wrapd(XX - cx), wrapd(YY - cy))
        r = rng.uniform(1.5, 3.5)
        ding = smoothstep(r + 0.5, r - 0.5, d)
        h -= 1.2 * ding
        a -= 0.12 * ding
    return h, a, g


LAYERS = [l_macro, l_concrete, l_brushed, l_painted, l_planks, l_weave, l_ground, l_foliage, l_rock, l_brick,
          l_tile, l_asphalt, l_snow, l_plaster]
# normal strength per layer (multiplies the height gradient)
NSTR = [0.35, 0.35, 0.3, 0.3, 0.32, 0.35, 0.26, 0.26, 0.22, 0.34, 0.4, 0.28, 0.3, 0.3]


# ------------------------------------------------------------------------------------------------------- derivation
def normals(h, k):
    dhdx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dhdy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5          # +y = up the image
    nx = -dhdx * k
    ny = -dhdy * k
    nz = np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    t = np.sqrt(nx * nx + ny * ny)
    k = np.minimum(1, 0.8 / np.maximum(t, 1e-9))             # cap the tilt at ~53 deg (codec headroom)
    nx, ny = nx * k, ny * k
    return nx, ny, np.sqrt(1 - nx * nx - ny * ny)


def enc_mul(m):
    m = m / m.mean()
    for _ in range(6):                               # keep the CLAMPED encoded mean at 128
        e = np.clip(128 + (m - 1) * 320, 0, 255)
        m = m - (e.mean() - 128) / 320
    return np.clip(np.round(128 + (m - 1) * 320), 0, 255).astype(np.uint8)


def enc_height(h):
    """Height 0..255 centred on 128 (the median), so neighbouring layers in the strip meet at similar values and the
    lossy codec does not bleed one layer's level into the next one's edge rows."""
    c = h - np.median(h)
    lo, hi = np.percentile(c, 0.05), np.percentile(c, 99.95)
    s = 127.0 / max(-lo, hi, 1e-9)
    return np.clip(np.round(128 + c * s), 0, 255).astype(np.uint8)


def build():
    A = np.zeros((N * len(LAYERS), N, 3), np.uint8)
    Nm = np.zeros((N * len(LAYERS), N, 3), np.uint8)
    stats = []
    for i, fn in enumerate(LAYERS):
        rng = np.random.default_rng(1000 + i)
        h, a, g = fn(rng)
        a = np.clip(a, 0.45, 1.6)
        g = np.clip(g, 0.3, 1.8)
        nx, ny, nz = normals(h, NSTR[i])
        sl = slice(i * N, (i + 1) * N)
        A[sl, :, 0] = enc_mul(a)
        A[sl, :, 1] = enc_mul(g)
        A[sl, :, 2] = enc_height(blur(h, 1.0))       # height is for blending, the normals carry the fine detail
        Nm[sl, :, 0] = np.clip(np.round(128 + nx * 127), 0, 255).astype(np.uint8)
        Nm[sl, :, 1] = np.clip(np.round(128 + ny * 127), 0, 255).astype(np.uint8)
        Nm[sl, :, 2] = 128
        am = a / a.mean()
        stats.append((np.mean((am > 0.8) & (am < 1.2)), np.degrees(np.arccos(nz)).mean()))
    return A, Nm, stats


# ----------------------------------------------------------------------------------------------------------- checks
def seam_ok(ch, src=None):
    """Wrap-around neighbour difference across the left/right and top/bottom edges vs the mean interior neighbour
    difference (limit 1.5x).

    On the source data (src None) the limit is strict. On the decoded file (src = the source channel) it allows for
    the codec: lossy WebP is YUV 4:2:0, so with three independent data channels its error is a few levels everywhere,
    smooth inside a block but independent between the two far-apart blocks that meet across a wrapped edge, and the
    decoder's chroma upsampling blends the edge rows of two stacked layers a little. The decoded limit is
    1.5 x interior (the larger of the plain mean and the mean across interior 16 px block boundaries) + sqrt(2) x the
    layer's mean codec error + 1.5 levels (0.5 % albedo, 0.012 normal)."""
    codec = src is not None
    ch = ch.astype(float)
    allow = 0.25
    if codec:
        allow = np.sqrt(2) * np.abs(ch - src)[2:-2, 2:-2].mean() + 1.5
    ok = True
    worst = 0.0
    for axis in (1, 0):
        dd = np.abs(np.diff(ch, axis=axis))
        inner = dd.mean()
        if codec:
            blk = dd[:, 15::16] if axis == 1 else dd[15::16, :]
            inner = max(inner, blk.mean())
        if axis == 1:
            edge = np.abs(ch[:, 0] - ch[:, -1]).mean()
        else:
            edge = np.abs(ch[0, :] - ch[-1, :]).mean()
        r = edge / max(inner, 1e-6)
        worst = max(worst, r if inner > 0.05 else 0)
        if edge > 1.5 * inner + allow:
            ok = False
    return ok, worst


def check(pa, pn, A0, N0):
    da = np.asarray(Image.open(pa).convert('RGB'))
    dn = np.asarray(Image.open(pn).convert('RGB'))
    fail = []
    print('seam = worst edge / interior ratio: raw data (limit 1.5), decoded file (1.5 + codec allowance)')
    print('layer          rawA  rawN   decA  decN   meanR  meanG  rmsA(R,G,B)      rmsN(R,G)  |n|max')
    for i, name in enumerate(NAMES):
        sl = slice(i * N, (i + 1) * N)
        la, ln = da[sl], dn[sl]
        wa = wn = ra = rn = 0.0
        for c in range(3):
            ok, w = seam_ok(A0[sl, :, c]); ra = max(ra, w)
            if not ok:
                fail.append('%s: seam in the detail-a data, channel %d' % (name, c))
            ok, w = seam_ok(la[:, :, c], A0[sl, :, c]); wa = max(wa, w)
            if not ok:
                fail.append('%s: seam in decoded detail-a, channel %d' % (name, c))
        for c in range(2):
            ok, w = seam_ok(N0[sl, :, c]); rn = max(rn, w)
            if not ok:
                fail.append('%s: seam in the detail-n data, channel %d' % (name, c))
            ok, w = seam_ok(ln[:, :, c], N0[sl, :, c]); wn = max(wn, w)
            if not ok:
                fail.append('%s: seam in decoded detail-n, channel %d' % (name, c))
        mr = la[:, :, 0].mean()
        mg = la[:, :, 1].mean()
        if abs(mr - 128) > 2 or abs(mg - 128) > 2:
            fail.append('%s: mean R/G %.2f / %.2f' % (name, mr, mg))
        nx = (ln[:, :, 0].astype(float) - 128) / 127
        ny = (ln[:, :, 1].astype(float) - 128) / 127
        nn = nx * nx + ny * ny
        if nn.max() > 0.97 or not np.isfinite(nn).all():
            fail.append('%s: invalid normals (|nxy|^2 max %.3f)' % (name, nn.max()))
        rms_a = [np.sqrt(((la[:, :, c].astype(float) - A0[sl, :, c]) ** 2).mean()) for c in range(3)]
        rms_n = [np.sqrt(((ln[:, :, c].astype(float) - N0[sl, :, c]) ** 2).mean()) for c in range(2)]
        print('%2d %-11s %4.2f  %4.2f   %4.2f  %4.2f  %6.2f %6.2f  %4.1f %4.1f %4.1f    %4.1f %4.1f    %.2f'
              % (i, name, ra, rn, wa, wn, mr, mg, *rms_a, *rms_n, np.sqrt(nn.max())))
    return fail, da, dn


# ---------------------------------------------------------------------------------------------------------- preview
def preview(da, dn, path, half=True):
    cell = N * 3 // (2 if half else 1)
    cols = 4
    rows = (len(NAMES) + cols - 1) // cols
    lab = 34
    sheet = Image.new('RGB', (cols * cell, rows * (cell + lab)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
    L = np.array([-1.0, 1.0, 1.1])
    L /= np.linalg.norm(L)
    for i, name in enumerate(NAMES):
        sl = slice(i * N, (i + 1) * N)
        am = 1 + (da[sl, :, 0].astype(float) - 128) / 320
        gm = 1 + (da[sl, :, 1].astype(float) - 128) / 320
        nx = (dn[sl, :, 0].astype(float) - 128) / 127
        ny = (dn[sl, :, 1].astype(float) - 128) / 127
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        ndl = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) / L[2]
        # half vector spec for a hint of the gloss channel
        H = L + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)
        spec = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** 40 * 0.12 * gm
        img = 0.5 * am * (0.25 + 0.75 * ndl) + spec
        img = np.clip(np.tile(img, (3, 3)) * 255, 0, 255).astype(np.uint8)
        im = Image.fromarray(img, 'L').convert('RGB')
        if half:
            im = im.resize((cell, cell), Image.LANCZOS)
        cx = (i % cols) * cell
        cy = (i // cols) * (cell + lab)
        sheet.paste(im, (cx, cy + lab))
        draw.text((cx + 10, cy + 3), '%d  %s' % (i, name), fill=(235, 235, 235), font=font)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path, quality=88)


def write_webp(path, arr, quality, passes=5):
    """Lossy WebP with error feedback on the first and last row of every layer: the decoder's chroma upsampling
    interpolates across the boundary between two stacked layers, bleeding one layer's edge row into the next one's
    (about twice the codec's normal error there). Re-encode a few times, pushing the decoded error of those rows back
    into the source, and keep the encode with the smallest boundary-row error."""
    if quality is None:
        Image.fromarray(arr, 'RGB').save(path, lossless=True, method=6)
        return
    import io
    src = arr.astype(float)
    r = np.arange(arr.shape[0]) % N
    m = np.zeros(arr.shape[:2], bool)
    m[(r == 0) | (r == N - 1)] = True
    work = src.copy()
    best = None
    for _ in range(passes):
        buf = io.BytesIO()
        Image.fromarray(np.clip(np.round(work), 0, 255).astype(np.uint8), 'RGB').save(buf, 'WEBP', quality=quality,
                                                                                     method=6)
        dec = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert('RGB')).astype(float)
        err = src - dec
        score = np.abs(err[m]).mean()
        if best is None or score < best[0]:
            best = (score, buf.getvalue())
        work[m] += err[m]
    with open(path, 'wb') as f:
        f.write(best[1])


def main():
    t0 = time.time()
    A, Nm, stats = build()
    os.makedirs(os.path.dirname(OUT_A), exist_ok=True)
    write_webp(OUT_A, A, Q_A)
    write_webp(OUT_N, Nm, Q_N)
    sa, sn = os.path.getsize(OUT_A), os.path.getsize(OUT_N)
    fail, da, dn = check(OUT_A, OUT_N, A, Nm)
    for i, (frac, tilt) in enumerate(stats):
        print('   %-13s albedo within x0.8..1.2: %5.1f%%   mean normal tilt %4.1f deg'
              % (NAMES[i], frac * 100, tilt))
    print('detail-a.webp %d B, detail-n.webp %d B, total %.2f MB' % (sa, sn, (sa + sn) / 1e6))
    if sa + sn > SIZE_BUDGET:
        fail.append('size %.2f MB over budget %.2f MB' % ((sa + sn) / 1e6, SIZE_BUDGET / 1e6))
    preview(da, dn, OUT_PREVIEW)
    if '--crops' in sys.argv:                   # full-resolution per-layer previews for review
        d = sys.argv[sys.argv.index('--crops') + 1]
        os.makedirs(d, exist_ok=True)
        for i in range(len(NAMES)):
            sl = slice(i * N, (i + 1) * N)
            preview_one(da[sl], dn[sl], os.path.join(d, 'layer%02d.png' % i))
    print('preview -> %s   (%.1f s)' % (os.path.relpath(OUT_PREVIEW, os.getcwd()), time.time() - t0))
    if fail:
        print('FAIL:\n  ' + '\n  '.join(fail))
        sys.exit(1)
    print('all checks passed')


def preview_one(la, ln, path):
    L = np.array([-1.0, 1.0, 1.1]); L /= np.linalg.norm(L)
    am = 1 + (la[:, :, 0].astype(float) - 128) / 320
    nx = (ln[:, :, 0].astype(float) - 128) / 127
    ny = (ln[:, :, 1].astype(float) - 128) / 127
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    ndl = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) / L[2]
    img = np.clip(np.tile(0.5 * am * (0.25 + 0.75 * ndl), (2, 2)) * 255, 0, 255).astype(np.uint8)
    g = np.tile(la[:, :, 1], (2, 2))
    Image.fromarray(np.concatenate([img, g], 1), 'L').save(path)


if __name__ == '__main__':
    main()
