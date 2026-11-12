"""INKBOLT kit-mossgarden: living things -- the giant trees (a broad mossy oak and a tiered cedar, huge trunks), the
clipped hedges (box 0.6 m, mid 1.25 m, yew 2.7 m as link runs), topiary (spiral, cone, ball), tulip beds, lavender
drifts, rose bushes and the rose arch, wildflower meadow, hydrangeas, tree ferns and ground ferns, the lumenbell pods
(a made-up glowing species: lantern pods whose cores glow, theme.glow), mossy boulders, the fallen log, the stream's
bank stones and reeds, and the low-poly backdrop trees (see mg_base.py for the conventions)."""
import math
import random

from mg_base import (TER, zcol, stonecol, mosscol, blob, puff, bloom, cup, stem, blade, frond, ring)  # noqa: F401

CANOPY = zcol('canopyL', 'canopy', 'canopy2', 0.35, -0.3)
LEAF = zcol('leafL', 'leaf', 'leafD', 0.45)
HEDGE = zcol('hedgeT', 'hedge', 'hedge2', 0.6, -0.5)
FERN = zcol('fern', 'fern', 'fern2', 0.45)


def bark(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.8:
        return 'barkL'
    if n.z < -0.4:
        return 'barkD'
    # moss creeps up the north (Blender +Y) side of the trunks
    if n.y > 0.35 and c.z < 7.0:
        return 'moss2'
    return 'bark' if math.sin(c.z * 1.7 + math.atan2(n.y, n.x) * 3.0) > -0.35 else 'barkD'


# ================================================================ giant trees [4, 4]
def giant_oak(k, ao, name, seed):
    """a vast old oak: buttressed root flare, a trunk 3 m across, six great limbs from 9-12 m, a broad crown of leaf
    masses 20 m wide; the canopy starts 9 m up so the ground under it stays open"""
    rnd = random.Random(seed)
    k.begin()
    k.cyl(0, 0, -0.05, 1.95, 1.62, 1.3, bark, seg=12)
    for i in range(6):
        a = i / 6 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        ca, sa = math.cos(a), math.sin(a)
        k.hullp([(ca * 1.95 + math.cos(a + s) * 0.3, sa * 1.95 + math.sin(a + s) * 0.3, 0.0) for s in (-1.5, 1.5)] +
                [(ca * 1.98, sa * 1.98, 0.0), (ca * 1.5, sa * 1.5, 1.6), (ca * 1.3, sa * 1.3, 0.0)], bark)
    zs = [1.2, 4.2, 7.4, 10.4, 12.6]
    rs = [1.6, 1.48, 1.38, 1.26, 1.0]
    wob = [(0, 0)] + [(rnd.uniform(-0.18, 0.18), rnd.uniform(-0.18, 0.18)) for _ in zs[1:]]
    for i in range(len(zs) - 1):
        k.tube((wob[i][0], wob[i][1], zs[i] - 0.04), (wob[i + 1][0], wob[i + 1][1], zs[i + 1]), rs[i] * 1.02, rs[i + 1] * 0.98, bark, seg=11)
    # moss pillows on the trunk (north side) and a hollow (dark) on the south side
    for (a, z, r) in ((1.4, 2.2, 0.5), (1.9, 3.6, 0.42), (1.2, 5.6, 0.36)):
        rr = 1.52 - z * 0.012
        puff(k, rnd, math.cos(a) * rr, math.sin(a) * rr, z, r, zcol('moss', 'moss2', 'mossD', 0.3), n=6, flat=0.55, ink=False)
    k.hullp([(0.25, -1.56, 2.0), (-0.25, -1.56, 2.0), (0.0, -1.58, 2.9), (0.2, -1.5, 2.4), (-0.2, -1.5, 2.4)], 'barkD', ink=False)
    # limbs and leaf masses
    a0 = rnd.uniform(0, 2 * math.pi)
    tips = []
    for i in range(6):
        a = a0 + (i + rnd.uniform(-0.15, 0.15)) / 6 * 2 * math.pi
        ca, sa = math.cos(a), math.sin(a)
        z0 = 9.0 + (i % 3) * 1.3
        r0 = 0.9 - (i % 3) * 0.08
        L1, L2 = rnd.uniform(3.6, 4.4), rnd.uniform(3.0, 3.8)
        p0 = (ca * 0.6, sa * 0.6, z0)
        p1 = (ca * L1, sa * L1, z0 + rnd.uniform(1.8, 2.6))
        p2 = (ca * (L1 + L2), sa * (L1 + L2), p1[2] + rnd.uniform(1.6, 2.4))
        k.tube(p0, p1, r0, r0 * 0.6, bark, seg=7)
        k.tube((p1[0] * 0.98, p1[1] * 0.98, p1[2] - 0.05), p2, r0 * 0.58, r0 * 0.3, bark, seg=6)
        tips.append(p2)
        puff(k, rnd, p2[0], p2[1], p2[2] + 0.6, rnd.uniform(3.2, 3.9), CANOPY, n=7, flat=0.62)
        mid = (p1[0] * 1.05 + sa * 1.2, p1[1] * 1.05 - ca * 1.2, p1[2] + 1.6)
        puff(k, rnd, mid[0], mid[1], mid[2], rnd.uniform(2.4, 3.0), CANOPY, n=6, flat=0.6)
    for (r, z, s) in ((0.0, 21.0, 4.6), (3.0, 19.0, 3.8), (-2.8, 18.6, 3.6)):
        a = a0 + 0.5 + r
        puff(k, rnd, math.cos(a) * abs(r) * 0.8, math.sin(a) * abs(r) * 0.8, z, s, CANOPY, n=8, flat=0.6)
    k.col(-1.62, 1.62, -1.62, 1.62, 0.0, 1.3)
    k.col(-1.42, 1.42, -1.42, 1.42, 1.3, 12.0)
    k.finish(name, ao=ao)


def giant_cedar(k, ao, name, seed):
    """a towering Mosswood cedar: a fluted trunk 2.8 m across at the foot rising 27 m, flat layered tiers of foliage
    from 9 m up, each tier a ring of broad level plates"""
    rnd = random.Random(seed)
    k.begin()
    k.cyl(0, 0, -0.05, 1.9, 1.5, 1.1, bark, seg=12)
    for i in range(7):
        a = i / 7 * 2 * math.pi + rnd.uniform(-0.15, 0.15)
        ca, sa = math.cos(a), math.sin(a)
        k.hullp([(ca * 1.9 + math.cos(a + s) * 0.26, sa * 1.9 + math.sin(a + s) * 0.26, 0.0) for s in (-1.5, 1.5)] +
                [(ca * 1.95, sa * 1.95, 0.0), (ca * 1.4, sa * 1.4, 2.0), (ca * 1.2, sa * 1.2, 0.0)], bark)
    zs = [1.0, 5.0, 10.0, 15.0, 20.0, 25.5]
    rs = [1.45, 1.3, 1.1, 0.85, 0.6, 0.3]
    for i in range(len(zs) - 1):
        k.tube((0, 0, zs[i] - 0.04), (0, 0, zs[i + 1]), rs[i] * 1.02, rs[i + 1], bark, seg=10 if i < 3 else 7)
    tiers = [(9.0, 7.4, 6), (12.2, 6.6, 6), (15.4, 5.6, 5), (18.6, 4.6, 5), (21.8, 3.4, 4), (24.8, 2.2, 3)]
    for ti, (z, R, n) in enumerate(tiers):
        a0 = rnd.uniform(0, 2 * math.pi)
        for i in range(n):
            a = a0 + (i + rnd.uniform(-0.12, 0.12)) / n * 2 * math.pi
            ca, sa = math.cos(a), math.sin(a)
            rr = R * rnd.uniform(0.55, 0.62)
            k.tube((ca * 0.4, sa * 0.4, z - 0.6), (ca * rr, sa * rr, z - 0.15), 0.32 - ti * 0.04, 0.12, bark, seg=5)
            puff(k, rnd, ca * rr, sa * rr, z + 0.1, R * rnd.uniform(0.42, 0.5), zcol('canopyL', 'canopy2', 'leafD', 0.3, -0.3), n=7, flat=0.24)
    puff(k, rnd, 0, 0, 26.6, 1.6, zcol('canopyL', 'canopy2', 'leafD', 0.3, -0.3), n=6, flat=0.8)
    k.col(-1.55, 1.55, -1.55, 1.55, 0.0, 1.1)
    k.col(-1.38, 1.38, -1.38, 1.38, 1.1, 10.0)
    k.finish(name, ao=ao)


# ================================================================ hedges (link runs, along Blender Y)
HEDGES = {'Box': (0.31, 0.62), 'Mid': (0.42, 1.25), 'Yew': (0.47, 2.7)}


def hedge_box(k, x0, x1, y0, y1, h, ch=0.09, col=HEDGE, ink=True):
    """a clipped hedge block with chamfered top edges"""
    pts = []
    for y in (y0, y1):
        for x in (x0, x1):
            pts.append((x, y, 0.0))
            pts.append((x, y, h - ch))
        pts.append((x0 + ch, y, h))
        pts.append((x1 - ch, y, h))
    k.hullp(pts, col, ink=ink)


def build_hedges(k, ao):
    for kind, (hw, h) in HEDGES.items():
        rnd = random.Random(len(kind) * 7 + int(h * 10))
        # full module: the whole cell; a few leafy bumps break the clipped faces
        k.begin()
        hedge_box(k, -hw, hw, -0.5, 0.5, h, ink=kind != 'Yew')
        k.col(-hw, hw, -0.5, 0.5, 0.0, h)
        k.finish(kind + 'Full', ao=ao)
        # half module: from the post's edge toward -Y (game +Z)
        k.begin()
        hedge_box(k, -hw, hw, -0.5, -hw, h)
        k.col(-hw, hw, -0.5, -hw, 0.0, h)
        k.finish(kind + 'Half', ao=ao)
        # post: the cell centre at runs' ends, corners and junctions (a touch taller, a rounded crown)
        k.begin()
        hedge_box(k, -hw, hw, -hw, hw, h + 0.05, ch=0.14)
        k.col(-hw, hw, -hw, hw, 0.0, h + 0.05)
        k.finish(kind + 'Post', ao=ao)


# ================================================================ topiary (1 cell)
def planter(k, s=0.32, h=0.46, c='stone'):
    k.bx(-s, s, -s, s, 0.0, h, c)
    k.bx(-s - 0.03, s + 0.03, -s - 0.03, s + 0.03, h, h + 0.06, 'stone2')
    k.bx(-s + 0.04, s - 0.04, -s + 0.04, s - 0.04, h + 0.06, h + 0.075, 'soil', ink=False)


def build_topiary(k, ao):
    # spiral: a boxwood helix of 2.4 turns round a hidden stem, in a stone planter
    rnd = random.Random(301)
    k.begin()
    planter(k)
    k.cyl(0, 0, 0.5, 0.05, 0.04, 2.0, 'bark', seg=5, ink=False)
    N, z0, z1 = 10, 0.62, 2.5

    def hel(t):
        a = t * 2.4 * 2 * math.pi
        R = 0.3 * (1 - 0.55 * t) + 0.04
        return (math.cos(a) * R, math.sin(a) * R, z0 + (z1 - z0) * t, 0.2 * (1 - 0.5 * t) + 0.05, a)
    for i in range(N):
        segp = []
        # each segment starts a quarter step back inside the one before, a little thinner (no shared cap planes)
        for (t, q) in (((i - 0.25) / N if i else 0.0, 0.92 if i else 1.0), ((i + 1) / N, 1.0)):
            x, y, z, r, a = hel(t)
            for m in range(4):   # a ring across the helix (its tilt turns with the helix)
                b = m / 4 * 2 * math.pi + 0.4
                u, w = math.cos(b) * r * q, math.sin(b) * r * q
                segp.append((x + math.cos(a) * u, y + math.sin(a) * u, z + w * 0.8))
        k.hullp(segp, HEDGE)
    k.sph(0, 0, z1 + 0.12, 0.13, 'hedgeT', seg=(6, 4))
    k.col(-0.34, 0.34, -0.34, 0.34, 0.0, 0.55)
    k.col(-0.3, 0.3, -0.3, 0.3, 0.55, 2.6)
    k.finish('Spiral', ao=ao)
    # cone yew in a terracotta pot
    k.begin()
    k.cyl(0, 0, 0, 0.26, 0.34, 0.48, 'terra', seg=10)
    k.cyl(0, 0, 0.44, 0.37, 0.37, 0.08, 'terra2', seg=10)
    k.cyl(0, 0, 0.5, 0.42, 0.04, 1.9, HEDGE, seg=9)
    k.col(-0.36, 0.36, -0.36, 0.36, 0.0, 1.4)
    k.finish('ConeTopiary', ao=ao)
    # ball-on-ball box in a square planter
    k.begin()
    planter(k, 0.3, 0.42, 'stone3')
    k.sph(0, 0, 0.92, 0.42, HEDGE, seg=(9, 6))
    k.cyl(0, 0, 1.3, 0.05, 0.05, 0.25, 'bark', seg=5, ink=False)
    k.sph(0, 0, 1.72, 0.27, HEDGE, seg=(8, 5))
    k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 1.9)
    k.finish('BallTopiary', ao=ao)


# ================================================================ flower beds
def build_beds(k, ao):
    # tulip bed [4, 2]: a stone-edged bed, three rows of tulips (the theme repaints the 'tulip' cell per copy)
    rnd = random.Random(311)
    k.begin()
    k.bx(-2.0, 2.0, -1.0, -0.88, 0.0, 0.16, 'stone')
    k.bx(-2.0, 2.0, 0.88, 1.0, 0.0, 0.16, 'stone')
    k.bx(-2.0, -1.88, -0.88, 0.88, 0.0, 0.16, 'stone')
    k.bx(1.88, 2.0, -0.88, 0.88, 0.0, 0.16, 'stone')
    k.bx(-1.88, 1.88, -0.88, 0.88, 0.0, 0.11, 'soil', ink=False)
    for row, y in enumerate((-0.38, 0.38)):
        for i in range(7):
            x = -1.5 + i * 0.5 + (0.25 if row else 0.0) + rnd.uniform(-0.05, 0.05)
            if x > 1.65:
                continue
            yy = y + rnd.uniform(-0.08, 0.08)
            h = rnd.uniform(0.38, 0.52)
            stem(k, (x, yy, 0.11), (x, yy, h), 0.013)
            cup(k, x, yy, h, 0.085, 'tulip', ink=False)
            if i % 2 == row:
                blade(k, (x, yy, 0.11), rnd.uniform(0, 6.28), 0.3, 0.08, 0.24, 'leaf', droop=0.25)
    k.finish('TulipBed', ao=ao)
    # lavender drift [3, 2]: mounded grey-green bushes bristling with purple spikes
    rnd = random.Random(312)
    k.begin()
    for (cx, cy, r) in ((-0.85, -0.3, 0.58), (0.3, -0.42, 0.55), (0.95, 0.38, 0.5), (-0.3, 0.45, 0.55)):
        blob(k, rnd, cx, cy, 0.0, r, r * 0.9, 0.5, zcol('lavG', 'lavG', 'leafD', 0.4), n=5)
        for i in range(7):
            a = rnd.uniform(0, 2 * math.pi)
            d = rnd.uniform(0.0, r * 0.75)
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
            z = 0.42 - d * 0.3 + i * 0.006
            tip = (x + math.cos(a) * 0.06, y + math.sin(a) * 0.06, z + rnd.uniform(0.3, 0.42))
            k.hullp([(x - 0.025, y, z), (x + 0.025, y, z), (x, y + 0.025, z), tip], 'lav' if i % 3 else 'lav2', ink=False)
    k.finish('Lavender', ao=False)
    # wildflower meadow [2, 2]: grass tufts, poppies, cornflowers, ox-eye daisies, buttercups (no collision)
    rnd = random.Random(313)
    k.begin()
    for i in range(6):
        x, y = rnd.uniform(-0.85, 0.85), rnd.uniform(-0.85, 0.85)
        for j in range(3):
            a = (j + rnd.uniform(-0.3, 0.3)) / 3 * 2 * math.pi
            blade(k, (x, y, 0.0), a, rnd.uniform(0.25, 0.4), 0.06, rnd.uniform(0.3, 0.45), 'leafL' if j % 2 else 'leaf', droop=0.15)
    cols = ['red', 'water2', 'tulipW', 'tulipY', 'red', 'tulipW', 'lav']
    for i in range(11):
        x, y = rnd.uniform(-0.88, 0.88), rnd.uniform(-0.88, 0.88)
        h = rnd.uniform(0.3, 0.55)
        stem(k, (x, y, 0.0), (x, y, h), 0.01)
        bloom(k, x, y, h, rnd.uniform(0.05, 0.075), cols[i % len(cols)])
    k.finish('Meadow', ao=False)


# ================================================================ roses, hydrangeas
def build_shrubs(k, ao):
    rnd = random.Random(321)
    k.begin()
    blob(k, rnd, 0, 0, 0.0, 0.42, 0.4, 1.15, LEAF, n=7)
    for i in range(7):
        a = i / 7 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        z = rnd.uniform(0.45, 1.05)
        r = 0.4 * math.sin(math.pi * min(0.95, z / 1.15)) * 0.98 + 0.03
        bloom(k, math.cos(a) * r, math.sin(a) * r, z, 0.085, 'rose', ink=True)
    k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 1.05)
    k.finish('RoseBush', ao=ao)
    # hydrangea: a leafy dome carrying big mop-head blooms (repainted: blue, pink, white)
    rnd = random.Random(322)
    k.begin()
    blob(k, rnd, 0, 0, 0.0, 0.45, 0.45, 1.0, LEAF, n=7)
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.3
        r = 0.3 if i % 2 else 0.2
        puff(k, rnd, math.cos(a) * r, math.sin(a) * r, 0.8 + (i % 2) * 0.1, 0.2, zcol('lav', 'lav', 'lav2', 0.2), n=5, flat=0.8)
    k.col(-0.4, 0.4, -0.4, 0.4, 0.0, 1.05)
    k.finish('Hydrangea', ao=ao)
    # rose arch [4, 1]: two iron hoops over a 3 m path, climbing roses up both sides and over the top
    rnd = random.Random(323)
    k.begin()
    X, H, rise = 1.72, 2.25, 0.75
    for y in (-0.3, 0.3):
        for s in (-1, 1):
            k.bx(s * X - 0.04, s * X + 0.04, y - 0.04, y + 0.04, 0.0, H, 'iron')
        pts = []
        for i in range(9):
            t = i / 8
            x = -X + 2 * X * t
            pts.append((x, y, H + rise * math.sin(math.pi * t)))
        for a, b in zip(pts, pts[1:]):
            k.beam(a, b, 0.07, 'iron')
    for i in range(5):
        x = -X + 2 * X * (i + 0.5) / 5
        z = H + rise * math.sin(math.pi * (i + 0.5) / 5)
        k.beam((x, -0.3, z), (x, 0.3, z), 0.045, 'iron', ink=False)
    for s in (-1, 1):
        blob(k, rnd, s * X, 0.0, 0.0, 0.3, 0.4, 0.9, LEAF, n=5)
        puff(k, rnd, s * X, rnd.uniform(-0.1, 0.1), 1.5, 0.32, LEAF, n=5, flat=1.2)
    for i in range(3):
        t = (i + 0.5) / 3
        puff(k, rnd, -X + 2 * X * t, rnd.uniform(-0.1, 0.1), H + rise * math.sin(math.pi * t) + 0.12, 0.34, LEAF, n=6, flat=0.65)
    for i in range(13):
        t = rnd.uniform(0.0, 1.0)
        if i < 6:
            s = -1 if i % 2 else 1
            x, z = s * (X + rnd.uniform(-0.2, 0.2)), rnd.uniform(0.6, H)
        else:
            x, z = -X + 2 * X * t, H + rise * math.sin(math.pi * t) + rnd.uniform(0.0, 0.35)
        bloom(k, x, rnd.choice((-0.42, 0.42)), z, 0.08, 'rose' if i % 3 else 'roseP', ink=True)
    for s in (-1, 1):
        k.col(s * X - 0.34, s * X + 0.34, -0.42, 0.42, 0.0, 0.9)
        k.col(s * X - 0.12, s * X + 0.12, -0.36, 0.36, 0.9, H)
    k.finish('RoseArch', ao=ao)


# ================================================================ ferns, lumenbell pods, rocks, logs
def build_wild(k, ao):
    # tree fern [2, 2]: a shaggy mossy trunk, a crown of nine arching fronds, two unfurling fiddleheads
    rnd = random.Random(331)
    k.begin()
    k.cyl(0, 0, -0.03, 0.36, 0.28, 0.5, 'barkD', seg=7)
    k.tube((0, 0, 0.45), (0.08, 0.05, 2.2), 0.28, 0.24, zcol('barkL', 'bark', 'barkD'), seg=7)
    for z in (0.9, 1.5):
        puff(k, rnd, 0.0, 0.2, z, 0.2, zcol('moss', 'moss2', 'mossD', 0.3), n=5, flat=0.6, ink=False)
    for i in range(7):
        a = i / 7 * 2 * math.pi + rnd.uniform(-0.15, 0.15)
        frond(k, (0.08 + math.cos(a) * 0.15, 0.05 + math.sin(a) * 0.15, 2.2), a, rnd.uniform(2.0, 2.5), 0.8, lift=0.4, droop=0.62, seg=2, col=FERN)
    for a in (0.6, 3.4):
        x, y = 0.08 + math.cos(a) * 0.12, 0.05 + math.sin(a) * 0.12
        k.tube((x, y, 2.18), (x + math.cos(a) * 0.12, y + math.sin(a) * 0.12, 2.6), 0.04, 0.03, 'fern2', seg=4, ink=False)
        k.sph(x + math.cos(a) * 0.15, y + math.sin(a) * 0.15, 2.66, 0.07, 'fern', seg=(5, 3))
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 2.2)
    k.finish('TreeFern', ao=ao)
    # ground fern (1 cell, no collision)
    rnd = random.Random(332)
    k.begin()
    for i in range(6):
        a = i / 6 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        frond(k, (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.05), a, rnd.uniform(0.75, 0.95), 0.34, lift=0.9, droop=0.75, seg=2, col=FERN, ink=False)
    k.finish('Fern', ao=False)
    # lumenbell pods (made-up species): lantern pods of four curved petals on arching stalks; the glowing cores are the
    # companion piece GlowPod_Glow (theme.glow pulses them)
    rnd = random.Random(333)
    pods = [(0.0, 0.0, 2.2, 0.32), (0.32, -0.2, 1.55, 0.26), (-0.28, 0.2, 1.3, 0.24)]
    k.begin()
    blob(k, rnd, 0, 0, 0.0, 0.42, 0.42, 0.55, zcol('pod2', 'pod', 'leafD', 0.4), n=6)
    for (x, y, h, r) in pods:
        mid = (x * 0.5 + 0.05, y * 0.5 - 0.04, h * 0.5)
        k.tube((x * 0.2, y * 0.2, 0.3), mid, 0.05, 0.04, 'pod', seg=5, ink=False)
        k.tube(mid, (x, y, h - r * 1.15), 0.04, 0.03, 'pod', seg=5, ink=False)
        for i in range(3):
            a = i / 3 * 2 * math.pi + x * 3
            ca, sa = math.cos(a), math.sin(a)
            px, py = -sa, ca
            pts = []
            for (u, zz) in ((0.25, -1.1), (1.0, -0.2), (0.9, 0.55), (0.2, 1.15)):
                for e in (-1, 1):
                    pts.append((x + ca * r * u + px * e * r * 0.5 * u, y + sa * r * u + py * e * r * 0.5 * u, h + zz * r))
            k.hullp(pts, zcol('pod2', 'pod', 'pod', 0.3))
        k.cyl(x, y, h + r * 1.1, r * 0.2, r * 0.05, r * 0.5, 'pod2', seg=5, ink=False)
    k.col(-0.36, 0.36, -0.36, 0.36, 0.0, 1.6)
    k.finish('GlowPod', ao=ao)
    k.begin()
    for (x, y, h, r) in pods:
        k.sph(x, y, h, r * 0.62, 'glowC', seg=(8, 5), scale=(1, 1, 1.35), ink=False)
    k.finish('GlowPod_Glow', ao=False)
    # mossy boulders [2, 2] and a mossy rock (1 cell)
    for name, seed, parts in (('MossBoulder', 341, ((-0.15, 0.05, 0.9, 0.8, 1.15), (0.55, -0.5, 0.45, 0.4, 0.55))),
                              ('MossRock', 342, ((0.0, 0.0, 0.44, 0.4, 0.62),))):
        rnd = random.Random(seed)
        k.begin()
        for (cx, cy, rx, ry, h) in parts:
            pts = []
            for i in range(7):
                a = (i + rnd.uniform(-0.25, 0.25)) / 7 * 2 * math.pi
                pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry, 0.0))
                a2 = a + 0.45
                pts.append((cx + math.cos(a2) * rx * 0.85, cy + math.sin(a2) * ry * 0.85, h * rnd.uniform(0.55, 0.75)))
            for i in range(3):
                a = rnd.uniform(0, 6.28)
                pts.append((cx + math.cos(a) * rx * 0.35, cy + math.sin(a) * ry * 0.35, h * rnd.uniform(0.9, 1.0)))
            k.hullp(pts, mosscol)
        if name == 'MossBoulder':
            k.col(-1.0, 0.75, -0.75, 0.85, 0.0, 1.1)
        else:
            k.col(-0.42, 0.42, -0.38, 0.38, 0.0, 0.6)
        k.finish(name, ao=ao)
    # fallen log [4, 1]: a mossy trunk lying along X, a snapped end, bracket fungi, a fern sprig
    rnd = random.Random(343)
    k.begin()
    k.tube((-1.85, 0.02, 0.36), (1.75, -0.03, 0.34), 0.38, 0.33, zcol('moss', 'bark', 'barkD', 0.55), seg=9)
    k.cyl(-1.86, 0.02, 0.36, 0.3, 0.3, 0.02, 'barkL', seg=9, rot=(0, -90, 0), ink=False)
    for j in range(5):
        a = j / 5 * 2 * math.pi
        tip = (1.75 + rnd.uniform(0.12, 0.22), -0.03 + math.cos(a) * 0.22, 0.34 + math.sin(a) * 0.22)
        k.hullp([(1.72, -0.03 + math.cos(a) * 0.3, 0.34 + math.sin(a) * 0.3), (1.72, -0.03 + math.cos(a + 0.6) * 0.3, 0.34 + math.sin(a + 0.6) * 0.3),
                 (1.72, -0.03, 0.34), tip], 'barkL')
    for (x, z) in ((-0.9, 0.3), (-0.6, 0.45), (0.5, 0.38)):
        k.hullp([(x - 0.16, -0.36, z), (x + 0.16, -0.36, z), (x, -0.56, z + 0.02), (x - 0.1, -0.5, z + 0.05), (x + 0.1, -0.5, z + 0.05)], 'woodL')
    for i in range(3):
        a = 1.2 + i * 0.5
        frond(k, (0.9, 0.3, 0.1), a, 0.7, 0.26, lift=0.8, droop=0.8, seg=2, col=FERN)
    k.col(-1.9, 1.9, -0.4, 0.4, 0.0, 0.72)
    k.finish('FallenLog', ao=ao)


# ================================================================ stream banks (placed by the theme, no collision)
def build_banks(k, ao):
    for name, seed in (('BankStone_A', 351), ('BankStone_B', 352)):
        rnd = random.Random(seed)
        k.begin()
        for (cx, cy, r, h) in ((-0.22, 0.0, 0.32, 0.27), (0.24, 0.1, 0.25, 0.2)):
            pts = []
            for i in range(5):
                a = (i + rnd.uniform(-0.2, 0.2)) / 5 * 2 * math.pi
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.85, 0.0))
                pts.append((cx + math.cos(a + 0.6) * r * 0.7, cy + math.sin(a + 0.6) * r * 0.6, h * rnd.uniform(0.7, 1.0)))
            k.hullp(pts, mosscol, ink=False)
        k.finish(name, ao=False)
    rnd = random.Random(353)
    k.begin()
    for i in range(7):
        a = rnd.uniform(0, 6.28)
        x, y = math.cos(a) * rnd.uniform(0, 0.25), math.sin(a) * rnd.uniform(0, 0.25)
        blade(k, (x, y, 0.0), a, rnd.uniform(0.25, 0.45), 0.05, rnd.uniform(0.7, 1.0), 'leaf' if i % 2 else 'leafD', droop=0.2)
    for i in range(2):
        x, y = rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15)
        stem(k, (x, y, 0.0), (x, y, 0.95), 0.012, 'leafD')
        k.cyl(x, y, 0.8, 0.035, 0.035, 0.2, 'bark', seg=5, ink=False)
    k.finish('Reeds', ao=False)


# ================================================================ backdrop trees (low poly, outside the walls)
def build_backdrop_trees(k):
    rnd = random.Random(361)
    k.begin()
    k.cyl(0, 0, -0.2, 0.45, 0.32, 5.0, 'bark', seg=5)
    for (x, y, z, r) in ((0, 0, 8.0, 3.6), (1.6, 0.8, 6.2, 2.7)):
        puff(k, rnd, x, y, z, r, zcol('canopy', 'canopy2', 'leafD', 0.35), n=5, flat=0.75)
    k.finish('Backdrop_Tree_A')
    k.begin()
    k.cyl(0, 0, -0.2, 0.35, 0.25, 2.0, 'barkD', seg=5)
    k.cyl(0, 0, 1.5, 2.2, 1.2, 4.0, zcol('far', 'farD', 'leafD', 0.3), seg=6)
    k.cyl(0, 0, 5.2, 1.6, 0.1, 7.5, zcol('far', 'farD', 'leafD', 0.3), seg=6)
    k.finish('Backdrop_Tree_B')
    rnd = random.Random(362)
    k.begin()
    k.cyl(0, 0, -0.2, 0.55, 0.4, 7.0, 'bark', seg=5)
    for (x, y, z, r) in ((0, 0, 11.5, 4.8), (2.2, -1.0, 9.0, 3.3), (-2.0, 1.2, 9.4, 3.4)):
        puff(k, rnd, x, y, z, r, zcol('canopyL', 'canopy', 'canopy2', 0.35), n=5, flat=0.7)
    k.finish('Backdrop_Tree_C')


def build_plants(k, ao):
    giant_oak(k, ao, 'Landmark_Oak_A', 201)
    giant_oak(k, ao, 'Landmark_Oak_B', 202)
    giant_cedar(k, ao, 'Landmark_Cedar', 203)
    build_hedges(k, ao)
    build_topiary(k, ao)
    build_beds(k, ao)
    build_shrubs(k, ao)
    build_wild(k, ao)
    build_banks(k, ao)
    build_backdrop_trees(k)
