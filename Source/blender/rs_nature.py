"""INKBOLT kit-resort: palms, the giant treehouse palms, the broken-limb and fallen-frond ramps, hedges, shore rocks,
ground cover and the far-off backdrop greenery (see rs_base.py for the conventions)."""
import math
import random

from rs_base import (RKit, TOP, SLAB, RAMP_L, RAMP_N, WALL_H, leafcol, rockcol, barkcol, blob, frond, palm, tuft,
                     flowers)


# ================================================================ giant treehouse palm [4, 4]
def giant_palm(k, ao, name, seed, lean_az, h=22.0, reach=2.8):
    """an enormous ring-banded palm whose trunk passes through a tree platform at TOP: a timber collar under the
    deck slab and four knee braces carry it; buttress flare at the foot, a crown of huge fronds 22 m up"""
    rnd = random.Random(seed)
    k.begin()
    # foot: flare and root humps (kept inside the 4 x 4 footprint)
    k.cyl(0, 0, -0.05, 1.85, 1.5, 1.25, 'trunk2', seg=12)
    for i in range(5):
        a = i / 5 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        cx, cy = math.cos(a) * 1.55, math.sin(a) * 1.55
        k.hullp([(cx + math.cos(a + s) * 0.35, cy + math.sin(a + s) * 0.35, 0.0) for s in (-1.4, 1.4)] +
                [(cx + math.cos(a) * 0.38, cy + math.sin(a) * 0.38, 0.0), (cx * 0.85, cy * 0.85, 0.75), (cx * 0.8, cy * 0.8, 0.0)], 'trunk2')
    # ring-banded trunk: straight to the platform, then leaning a little toward lean_az
    dx, dy = math.cos(lean_az), math.sin(lean_az)
    n = 8
    zs = [1.0 + (h - 1.0) * i / n for i in range(n + 1)]

    def ctr(z):
        u = max(0.0, (z - 9.0) / (h - 9.0))
        return (dx * 1.7 * u ** 1.6, dy * 1.7 * u ** 1.6)

    def rad(z):
        return 1.45 - 0.45 * (z - 1.0) / (h - 1.0)
    for i in range(n):
        za, zb = zs[i], zs[i + 1]
        (ax, ay), (bx, by) = ctr(za), ctr(zb)
        k.tube((ax, ay, za - 0.03), (bx, by, zb), rad(za) * 1.07, rad(zb) * 0.97, 'trunk' if i % 2 else 'trunk3', seg=9)
    # platform collar (under the slab) and knee braces
    under = TOP - SLAB
    k.cyl(0, 0, under - 0.5, 1.52, 1.52, 0.5, 'wood2', seg=10)
    k.cyl(0, 0, under - 0.62, 1.47, 1.47, 0.12, 'rope', seg=10, ink=False)
    for i in range(4):
        a = i * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        k.beam((ca * 1.3, sa * 1.3, under - 3.0), (ca * reach, sa * reach, under - 0.02), 0.26, 'wood')
        cx, cy = ca * (reach - 0.1), sa * (reach - 0.1)
        k.bx(cx - 0.18, cx + 0.18, cy - 0.18, cy + 0.18, under - 0.3, under - 0.01, 'woodD')
    # crown
    tx, ty = ctr(h)
    k.cyl(tx, ty, h - 0.6, 1.0, 1.25, 0.9, 'frond2', seg=10)
    for i in range(6):
        a = i / 6 * 2 * math.pi + 0.3
        k.sph(tx + math.cos(a) * 1.15, ty + math.sin(a) * 1.15, h - 0.75, 0.42, 'coco' if i % 3 else 'cocoG', seg=(5, 3))
    a0 = rnd.uniform(0, 2 * math.pi)
    for i in range(12):
        a = a0 + (i + rnd.uniform(-0.15, 0.15)) / 12 * 2 * math.pi
        frond(k, (tx + math.cos(a) * 0.6, ty + math.sin(a) * 0.6, h + 0.2), a, rnd.uniform(8.0, 9.5), 2.3,
              lift=rnd.uniform(0.18, 0.3), droop=rnd.uniform(0.5, 0.7), seg=3)
    for i in range(3):   # dead fronds hanging under the crown
        a = a0 + 0.5 + i * 2.1
        frond(k, (tx + math.cos(a) * 0.9, ty + math.sin(a) * 0.9, h - 0.6), a, 4.5, 1.4, lift=0.0, droop=1.25, seg=2,
              col=lambda f: 'frondB' if f.normal.z < 0 else 'frondY')
    k.col(-1.3, 1.3, -1.3, 1.3, 0.0, 1.2)
    k.col(-1.05, 1.05, -1.05, 1.05, 1.2, TOP + 3.0)
    k.finish(name, ao=ao)


# ================================================================ ramps [2, 13] rising toward +Y from 0 to TOP
def ramp_steps(k, w=0.9):
    run = RAMP_L / RAMP_N
    for i in range(RAMP_N):
        y0 = -RAMP_L / 2 + i * run
        top = (i + 1) * TOP / RAMP_N
        k.wcol(-w, w, y0, y0 + run, max(0.0, top - 1.0), top)


def zw(y):
    """walk-surface height of a ramp at y (Blender, footprint centre origin)"""
    return TOP * (y + RAMP_L / 2) / RAMP_L


def limb_col(f):
    n = f.normal
    if n.z > 0.75:
        return 'trunk3'
    if n.y < -0.85:
        return 'heart'
    if n.z < -0.3:
        return 'barkD'
    return 'bark'


def build_ramps(k, ao):
    # a storm-snapped limb: a thick bark log with its top worn flat, the broken end splintered on the sand, its
    # upper end resting on the platform edge; two snapped side branches and a leafy sprig
    for name, seed in (('Ramp_Limb', 51), ('Ramp_LimbB', 52)):
        rnd = random.Random(seed)
        k.begin()
        ys = [-RAMP_L / 2, -2.2, 2.2, RAMP_L / 2]
        wig = [0.0, rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.0]
        rads = [1.0, 0.95, 0.9, 0.86]

        def sect(y, xo, r):
            ft = 0.55
            top = zw(y)
            a1 = math.degrees(math.asin(ft / r))
            out = [(xo + r * math.cos(math.radians(a)), y, top - ft + r * math.sin(math.radians(a))) for a in (a1, 5, -40, -90, -140, -185, 180 - a1)]
            return out
        for i in range(3):
            pa, pb = sect(ys[i], wig[i], rads[i]), sect(ys[i + 1], wig[i + 1], rads[i + 1])
            if i > 0:
                pa = [(x, y + 0.01, z - 0.003) for (x, y, z) in pa]
            k.hullp(pa + pb, limb_col)
        # splinters on the broken foot (pointing up / out of the end face, inside the footprint)
        y0 = -RAMP_L / 2
        for j in range(6):
            a = -0.9 + j * 0.36 + rnd.uniform(-0.08, 0.08)
            bx_, bz = math.sin(a) * 0.62, zw(y0) - 0.55 + math.cos(a) * 0.62
            tip = (bx_ * 1.25, y0 + rnd.uniform(0.05, 0.15), bz + rnd.uniform(0.25, 0.5))
            k.hullp([(bx_ - 0.1, y0 + 0.02, bz - 0.1), (bx_ + 0.1, y0 + 0.02, bz - 0.1), (bx_, y0 + 0.25, bz - 0.12), tip], 'heart' if j % 2 else 'trunk3')
        # snapped side branches and a sprig of leaves (no collision)
        for (yb, side, L, up) in ((-1.0, 1, 2.0, 0.6), (3.6, -1, 1.6, 0.3)):
            z = zw(yb) - 0.75
            a = (side * 0.93, yb + 0.1, z)
            b = (side * (0.93 + L), yb + 0.7, z - 0.35 + up)
            k.tube(a, b, 0.3, 0.2, 'bark', seg=6)
            k.hullp([(b[0] - 0.12, b[1] - 0.12, b[2]), (b[0] + 0.12, b[1] + 0.12, b[2]), (b[0] + side * 0.25, b[1] + 0.1, b[2] + 0.35)], 'heart')
        for j in range(3):
            yy = 0.3 + j * 0.5
            frond(k, (-0.9, yy, zw(yy) - 0.55), math.pi + rnd.uniform(-0.6, 0.4), 1.8, 0.7, lift=0.25, droop=0.6, seg=1,
                  col=leafcol('frond3', 'leaf', 'leafD'))
        ramp_steps(k)
        k.finish(name, ao=ao)
    # a fallen giant frond: its rachis is the walkway, the leaflets droop to the sand either side, the torn sheath
    # at the foot
    rnd = random.Random(53)
    k.begin()

    def rsect(y, w):
        top = zw(y)
        return [(-w, y, top), (w, y, top), (w * 0.95, y, top - 0.16), (0.3 * w, y, top - 0.55), (-0.3 * w, y, top - 0.55), (-w * 0.95, y, top - 0.16)]
    ys = [-RAMP_L / 2, -1.5, 3.0, RAMP_L / 2]
    ws = [0.95, 0.9, 0.86, 0.8]
    rcol = lambda f: 'frondY' if f.normal.z > 0.75 else ('frondB' if f.normal.y < -0.85 else 'frond2')
    for i in range(3):
        pa, pb = rsect(ys[i], ws[i]), rsect(ys[i + 1], ws[i + 1])
        if i > 0:
            pa = [(x, y + 0.01, z - 0.003) for (x, y, z) in pa]
        k.hullp(pa + pb, rcol)
    # torn sheath at the foot: a wide fibrous cup lying on the sand
    y0 = -RAMP_L / 2
    k.hullp([(-0.98, y0, 0.0), (0.98, y0, 0.0), (-0.9, y0 + 1.3, 0.0), (0.9, y0 + 1.3, 0.0), (-0.7, y0 + 0.2, 0.55), (0.7, y0 + 0.2, 0.55),
             (-0.75, y0 + 1.2, zw(y0 + 1.2) - 0.25), (0.75, y0 + 1.2, zw(y0 + 1.2) - 0.25)], lambda f: 'frondB' if f.normal.z < 0.8 else 'frondY')
    for side in (-1, 1):
        for j in range(9):
            yy = -3.0 + j * 1.1
            z = zw(yy) - 0.12
            tipz = max(0.06, z - rnd.uniform(2.0, 2.8))
            reach = rnd.uniform(2.3, 2.8)
            root = (side * 0.8, yy, z)
            tip = (side * reach, yy + rnd.uniform(0.8, 1.2), tipz)
            mid = (side * (0.8 + reach) * 0.55, yy + 0.4, max(tipz + 0.2, z - 0.35))
            k.hullp([(root[0], root[1] - 0.2, root[2]), (root[0], root[1] + 0.2, root[2]), (mid[0], mid[1] - 0.22, mid[2]),
                     (mid[0], mid[1] + 0.22, mid[2]), (mid[0], mid[1], mid[2] - 0.05), tip], leafcol('frond3', 'frond', 'frond2'))
    ramp_steps(k)
    k.finish('Ramp_Frond', ao=ao)


# ================================================================ palms and plants
def build_palms(k, ao):
    for name, seed, h, lean, fr in (('Palm_A', 61, 7.0, 0.16, 7), ('Palm_B', 62, 8.2, 0.22, 7), ('Palm_C', 63, 6.0, 0.1, 6)):
        rnd = random.Random(seed)
        k.begin()
        palm(k, rnd, 0, 0, h, lean=lean, fronds=fr, flen=3.1, fw=0.95, r=(0.21, 0.14), rings=3, nuts=3, seg=5)
        k.cyl(0, 0, -0.02, 0.36, 0.22, 0.25, 'trunk2', seg=6)
        k.col(-0.2, 0.2, -0.2, 0.2, 0.0, 2.6)
        k.finish(name, ao=ao)
    for name, seed, h in (('TallPalm_A', 64, 13.0), ('TallPalm_B', 65, 15.0)):   # [2, 2]
        rnd = random.Random(seed)
        k.begin()
        palm(k, rnd, 0, 0, h, lean=0.18, fronds=8, flen=4.6, fw=1.3, r=(0.36, 0.22), rings=5, nuts=4, seg=7, fseg=2)
        k.cyl(0, 0, -0.02, 0.62, 0.38, 0.4, 'trunk2', seg=8)
        k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 3.0)
        k.finish(name, ao=ao)
    # hibiscus bush
    for name, seed in (('Bush_A', 71), ('Bush_B', 72)):
        rnd = random.Random(seed)
        k.begin()
        blob(k, rnd, 0, 0, 0, 0.5, 0.48, 1.15, leafcol('leaf', 'leaf', 'leafD'), n=6)
        blob(k, rnd, 0.18, -0.12, 0.3, 0.32, 0.3, 0.95, leafcol('frond3', 'leaf', 'leafD'), n=5)
        pts = []
        for i in range(7):
            a = i / 7 * 2 * math.pi
            pts.append((math.cos(a) * 0.47, math.sin(a) * 0.45, 0.45 + 0.4 * ((i * 3) % 4) / 3))
        flowers(k, rnd, pts, 'hibis' if name == 'Bush_A' else 'bloom', 0.1)
        k.col(-0.42, 0.42, -0.42, 0.42, 0.0, 1.1)
        k.finish(name, ao=ao)
    k.begin()
    rnd = random.Random(73)
    for (x, y, r) in ((-0.2, -0.15, 0.55), (0.25, 0.1, 0.45), (-0.05, 0.3, 0.4), (0.3, -0.3, 0.35)):
        tuft(k, rnd, x, y, r, col='grass2' if r > 0.4 else 'grass3', n=5)
    k.finish('DuneGrass', ao=False)


# ================================================================ ground cover: fallen trunk, stump, coconuts, fallen frond
def build_cover(k, ao):
    # fallen palm trunk [6, 2] lying along X: torn root plate at -X, a few dead fronds at +X
    rnd = random.Random(81)
    k.begin()
    n = 6
    for i in range(n):
        xa, xb = -2.55 + 5.1 * i / n, -2.55 + 5.1 * (i + 1) / n
        k.tube((xa - 0.02, 0.0, 0.5 + 0.03 * i), (xb, 0.0, 0.5 + 0.03 * (i + 1)), 0.56, 0.52, 'trunk' if i % 2 else 'trunk3', seg=9)
    k.hullp([(-2.95, y, z) for y in (-0.95, -0.4, 0.4, 0.95) for z in (0.0,)] + [(-2.6, y, z) for (y, z) in ((-0.85, 0.15), (0.85, 0.15), (-0.6, 1.5), (0.6, 1.5), (0.0, 1.75))] +
            [(-2.95, -0.55, 1.35), (-2.95, 0.55, 1.35)], lambda f: 'coco' if f.normal.x < -0.5 else 'barkD')
    for j in range(5):   # root ends sticking out of the plate
        a = j * 1.25
        b = (-2.98, math.cos(a) * 0.6, 0.8 + math.sin(a) * 0.55)
        k.tube((-2.7, b[1] * 0.8, b[2]), (b[0] - 0.02, b[1] * 1.02, b[2]), 0.06, 0.03, 'barkD', seg=4, ink=False)
    k.cyl(2.55, 0.0, 0.68, 0.5, 0.5, 0.08, 'frond2', seg=9, rot=(0, 90, 0))
    for j, a in enumerate((-0.5, 0.1, 0.7)):
        frond(k, (2.75, 0.0, 0.7), a, 2.6, 0.9, lift=0.0, droop=0.25, seg=2, col=lambda f: 'frondB' if f.normal.z < 0 else 'frondY')
    k.col(-2.6, 2.7, -0.55, 0.55, 0.0, 1.05)
    k.col(-2.95, -2.6, -0.9, 0.9, 0.0, 1.6)
    k.finish('FallenTrunk', ao=ao)
    # snapped palm stump [2, 2]
    rnd = random.Random(82)
    k.begin()
    k.cyl(0, 0, -0.05, 0.95, 0.85, 0.5, 'trunk2', seg=10)
    for i, (za, zb) in enumerate(((0.42, 1.2), (1.17, 1.95))):
        k.cyl(0, 0, za, 0.84, 0.8, zb - za, 'trunk' if i else 'trunk3', seg=10)
    for j in range(7):
        a = j / 7 * 2 * math.pi
        h = rnd.uniform(0.35, 0.9)
        cx, cy = math.cos(a) * 0.58, math.sin(a) * 0.58
        k.hullp([(cx + math.cos(a + 1.57) * 0.22, cy + math.sin(a + 1.57) * 0.22, 1.9), (cx - math.cos(a + 1.57) * 0.22, cy - math.sin(a + 1.57) * 0.22, 1.9),
                 (cx * 0.6, cy * 0.6, 1.9), (cx * 1.3, cy * 1.3, 1.88), (cx * 0.95, cy * 0.95, 1.9 + h)], 'heart' if j % 2 else 'trunk3')
    k.cyl(0, 0, 1.9, 0.7, 0.7, 0.03, 'heart', seg=10, ink=False)
    k.col(-0.62, 0.62, -0.62, 0.62, 0.0, 2.1)
    k.finish('Stump', ao=ao)
    # coconut pile
    rnd = random.Random(83)
    k.begin()
    nuts = [(-0.22, -0.18, 0.16), (0.12, -0.25, 0.16), (0.3, 0.08, 0.16), (-0.2, 0.2, 0.16), (-0.02, 0.0, 0.42)]
    for i, (x, y, z) in enumerate(nuts):
        k.sph(x, y, z, 0.17, 'coco' if i % 3 else 'cocoG', seg=(5, 3))
    k.hullp([(0.25, -0.35, 0.0), (0.45, -0.25, 0.0), (0.35, -0.3, 0.12), (0.4, -0.42, 0.04)], 'heart')
    k.col(-0.45, 0.45, -0.42, 0.38, 0.0, 0.58)
    k.finish('CoconutPile', ao=ao)
    # fallen frond lying on the ground [2, 4] (along Y), no collision
    rnd = random.Random(84)
    k.begin()
    frond(k, (0.0, -1.9, 0.12), math.pi / 2, 3.9, 1.6, lift=0.0, droop=0.02, seg=3, col=lambda f: 'frondB' if f.normal.z < 0 else 'frondY')
    k.finish('FallenFrond', ao=False)


# ================================================================ zone edges: hedges (2 m, face -Y) and shore rocks
def hedge_body(k, rnd, x0, x1, h, cols, base=0.42, dy=0.0):
    pts = []
    for x in (x0, x0 + 0.25, (x0 + x1) / 2, x1 - 0.25, x1):
        e = x in (x0, x1)
        for (y, z) in ((-0.3, base), (-0.42, 1.2), (-0.4, h * 0.75), (-0.2, h), (0.3, h * 0.97), (0.46, base)):
            zz = z * (0.9 if e and z > 1 else 1.0) + (rnd.uniform(-0.12, 0.12) if z > 1 else 0)
            yy = y + (0.1 if e and y < 0 else 0.0) + (dy if y > 0.4 else -dy if y < -0.25 else 0.0)
            pts.append((x, yy, zz))
    k.hullp(pts, cols)


def build_edges(k, ao):
    hc = leafcol('frond3', 'leaf', 'leafD')
    # kerb tops differ per module (modules overlap by half a cell at run ends: never two coplanar kerb tops)
    for name, seed, w, extra, kh in (('Hedge_A', 91, 2, None, 0.45), ('Hedge_B', 92, 2, 'flower', 0.462), ('Hedge_C', 93, 2, 'palm', 0.474),
                                     ('Hedge_1', 94, 1, None, 0.486)):
        rnd = random.Random(seed)
        k.begin()
        if w == 1:   # a run-end filler overlaps the last 2 m module by half a cell: set 3 cm back off its front plane
            k.push(0, 0.06)
        x0, x1 = -w / 2, w / 2
        k.bx(x0, x1, -0.5, 0.48 - (kh - 0.45), -0.02 - (kh - 0.45), kh, 'stone')
        vk = round((kh - 0.45) / 0.012)   # variant index: neighbouring modules never share a face plane
        k.bx(x0, x1, -0.52 - (kh - 0.45), -0.35 - 0.006 * vk, kh, kh + 0.05, 'stone2', ink=False)
        hedge_body(k, rnd, x0 + 0.02, x1 - 0.02, WALL_H, hc, base=kh - 0.03, dy=0.006 * vk)
        nf = 4 if extra == 'flower' else 2 * w // 2
        fl = []
        for i in range(nf):
            fl.append((x0 + (i + 0.5) / nf * w + rnd.uniform(-0.15, 0.15), -0.47 + 0.0, rnd.uniform(1.0, WALL_H * 0.8)))
        flowers(k, rnd, [(x, -0.46, z) for (x, _, z) in fl], 'hibis' if seed % 2 else 'pink', 0.1)
        if extra == 'palm':
            palm(k, rnd, 0.0, 1.4, 8.5, lean=0.12, az=math.pi / 2 + rnd.uniform(-0.6, 0.6), fronds=6, flen=3.2, fw=0.95, nuts=2)
        k.finish(name, ao=ao)
    for name, seed in (('Corner_A', 95), ('Corner_B', 96)):
        rnd = random.Random(seed)
        k.begin()
        zb = -0.06 if name == 'Corner_A' else -0.072
        k.cyl(0, 0, zb, 0.62, 0.6, (0.548 if name == 'Corner_A' else 0.56) - zb, 'stone', seg=8)
        blob(k, rnd, 0, 0, 0.5, 0.62, 0.62, WALL_H - 0.3, hc, n=6)
        if name == 'Corner_B':
            palm(k, rnd, 0.0, 0.0, 9.0, lean=0.1, fronds=6, flen=3.2, fw=0.95, nuts=2, z0=WALL_H - 0.4)
        k.finish(name, ao=ao)
    # shore (one cell, face -Y toward the zone; the theme turns it to face east): rock armour along the beach edge,
    # a rope fence on bamboo posts, dune grass; the sea is behind it (the theme's backdrop)
    for name, seed in (('Shore_A', 101), ('Shore_B', 102), ('Shore_C', 103)):
        rnd = random.Random(seed)
        k.begin()
        for (cx, cy, rx, ry, hh) in ((-0.22, 0.08, 0.4, 0.44, rnd.uniform(0.62, 0.8)), (0.26, 0.06, 0.36, 0.44, rnd.uniform(0.5, 0.72))):
            pts = []
            for i in range(5):
                a = (i + rnd.uniform(-0.2, 0.2)) / 5 * 2 * math.pi
                pts.append((max(-0.5, min(0.5, cx + math.cos(a) * rx)), max(-0.42, min(0.5, cy + math.sin(a) * ry)), 0.0))
                pts.append((max(-0.48, min(0.48, cx + math.cos(a + 0.5) * rx * 0.75)), max(-0.38, min(0.48, cy + math.sin(a + 0.5) * ry * 0.75)), hh * rnd.uniform(0.55, 0.75)))
            pts.append((cx, cy, hh))
            k.hullp(pts, rockcol)
        if name != 'Shore_C':
            k.cyl(0.0, -0.36, 0.0, 0.045, 0.04, 1.0, 'bamboo', seg=6)
            k.cyl(0.0, -0.36, 1.0, 0.05, 0.01, 0.06, 'bamboo2', seg=6)
        k.beam((-0.5, -0.36, 0.86), (0.5, -0.36, 0.86), 0.03, 'rope', ink=False)
        if name != 'Shore_A':
            tuft(k, rnd, 0.0, -0.3, 0.4, col='grass3', n=4)
        k.col(-0.5, 0.5, -0.4, 0.5, 0.0, 0.9)
        k.finish(name, ao=ao)
    # trail hedges (1 m along Y, inner face +X)
    for name, seed in (('TrailWall', 111), ('TrailWall_B', 112), ('TrailWall_C', 113)):
        rnd = random.Random(seed)
        k.begin()
        k.bx(-0.5, 0.3, -0.5, 0.5, 0.0, 0.42, 'stone')
        pts = [(x, y, z) for y in (-0.49, 0.49) for (x, z) in ((0.2, 0.42), (0.32, 1.3), (0.25, 2.2), (0.0, 2.6), (-0.5, 2.55), (-0.5, 0.42))]
        k.hullp([(x, y, z + (rnd.uniform(-0.08, 0.08) if z > 2 else 0)) for (x, y, z) in pts], hc)
        flowers(k, rnd, [(0.34, -0.2, 1.1), (0.3, 0.25, 1.8)], 'hibis' if seed % 2 else 'bloom', 0.1)
        if name == 'TrailWall_B':   # tiki torch on the inner side
            k.cyl(0.42, 0.0, 0.0, 0.05, 0.045, 1.9, 'bamboo', seg=6)
            k.cyl(0.42, 0.0, 1.85, 0.07, 0.15, 0.25, 'thatch2', seg=6)
            k.cyl(0.42, 0.0, 2.1, 0.1, 0.02, 0.3, 'flame', seg=5, ink=False)
        if name == 'TrailWall_C':
            flowers(k, rnd, [(0.3, -0.35, 0.7), (0.33, 0.05, 1.45), (0.28, 0.35, 2.05), (0.15, -0.1, 2.45)], 'pink', 0.11)
        k.finish(name, ao=ao)


# ================================================================ backdrop greenery (outside the zones)
def build_backdrop_green(k):
    for name, seed, h in (('Backdrop_Palm_A', 121, 9.0), ('Backdrop_Palm_B', 122, 11.5)):
        rnd = random.Random(seed)
        k.begin()
        palm(k, rnd, 0, 0, h, lean=0.2, fronds=5, flen=3.6, fw=1.1, r=(0.26, 0.17), rings=2, nuts=0, seg=4, fseg=1,
             droop=0.55, cols=('trunk', 'trunk2'))
        k.finish(name)
    for name, seed in (('Backdrop_Jungle_A', 123), ('Backdrop_Jungle_B', 124)):
        rnd = random.Random(seed)
        k.begin()
        for (x, y, r, h, z0) in ((0, 0, 2.6, 5.0, -0.3), (2.2, 1.0, 2.0, 4.0, -0.38), (-2.0, 0.8, 2.2, 4.4, -0.46)):
            blob(k, rnd, x, y, z0, r, r, h, leafcol('far', 'leaf', 'leafD'), n=5)
        k.finish(name)
    rnd = random.Random(125)
    k.begin()   # islet: a rocky hump with sand and two palms
    k.cyl(0, 0, -0.4, 7.0, 5.5, 0.6, 'sand', seg=10)
    blob(k, rnd, 0.5, 0.0, 0.1, 4.0, 3.2, 3.5, rockcol, n=6)
    blob(k, rnd, -1.0, 0.5, 2.5, 2.8, 2.2, 2.2, leafcol('far', 'leaf', 'leafD'), n=5)
    palm(k, rnd, 2.0, -1.0, 8.0, lean=0.25, az=0.4, fronds=5, flen=3.2, fw=1.0, rings=3, nuts=0, seg=5, fseg=1, z0=1.5)
    palm(k, rnd, -2.5, 1.5, 7.0, lean=0.3, az=2.6, fronds=5, flen=3.0, fw=1.0, rings=3, nuts=0, seg=5, fseg=1, z0=1.5)
    k.finish('Backdrop_Islet')


def build_nature(k, ao):
    giant_palm(k, ao, 'Landmark_GiantPalm_A', 41, 0.6)
    giant_palm(k, ao, 'Landmark_GiantPalm_B', 42, 3.6)
    build_ramps(k, ao)
    build_palms(k, ao)
    build_cover(k, ao)
    build_edges(k, ao)
    build_backdrop_green(k)
