"""INKBOLT asset family: kit-grove ("Redwood Hollow", an overgrown garden valley on bumpy ground).

Mossy rock ridges (wall modules), giant redwoods you climb: broken, split-down branch shelves spiral up the trunk
like stairs (0.45 m per step) to a ring of big limbs at 9 m, with the stairwell side open; plank bridges strung
between trees at the same height (a "@layer 9" in the zone file); oaks, fruit trees (apple, orange, pear), bushes,
berry bushes, tall grass, reeds, ferns, flowers, sunflowers, raised vegetable beds, pumpkin patches, boulders,
fallen logs, a lily pond, picket fences, fruit crates, gate, hedge corridor wall, hatch, rolling-hill backdrop.

Redwood footprint 6 x 6 (origin = trunk centre). Spiral: step k (1..23) has its top at 0.375 k m, centred 1.8 m from
the trunk at angle (k - 24) * 30 degrees (Blender XY, 0 = +X = game east), a 1.1 m square shelf. The ring at 9 m:
east, north and west limbs (1.6 m wide, out to the footprint edge) and the north-east / north-west corners; the
south half stays open above the last turn of the stairs so there is head room.
"""
import math
import random

import bpy  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_util import finish as _finish, col_box, hull_pts

FAM = 'kit-grove'
PFX = 'KIT_GROVE_'
ib_lib.GLB[FAM] = 'fps-kit-grove.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    ('rock', '#9AA391'), ('rock2', '#7F8A78'), ('rock3', '#B6BEAA'), ('moss', '#6FAF55'),
    ('grass', '#7CC05E'), ('grass2', '#5EA64A'), ('grass3', '#A3D677'), ('leaf', '#3F9A5A'),
    ('leaf2', '#2E8350'), ('leaf3', '#5DB86C'), ('bark', '#8A5A3C'), ('bark2', '#6E452D'),
    ('redbark', '#A9583A'), ('split', '#E2B07A'), ('plank', '#C8935C'), ('plank2', '#A9774A'),
    ('rope', '#DCC79A'), ('soil', '#6B4C36'), ('apple', '#E84A3C'), ('orange', '#F59A2E'),
    ('pear', '#C9D65A'), ('berry', '#7B4BC4'), ('pumpkin', '#F28C28'), ('cabbage', '#9BD07A'),
    ('carrot', '#F5862E'), ('tomato', '#E5432F'), ('petal1', '#FF8FB8'), ('petal2', '#FFE15A'),
    ('petal3', '#B48CFF'), ('petal4', '#FFFFFF'), ('sun', '#FFC928'), ('water', '#7FC8E8'),
    ('lily', '#4FB063'), ('fence', '#F3EBDD'), ('far', '#9CC79A'), ('far2', '#7FB287'),
    ('hedge', '#4E9E52'), ('hedge2', '#3F8A47'),
]
TRIS = {}
STEP, NSTEP, RING_Z, RING_T = 0.375, 23, 9.0, 0.35   # 24 rises of 0.375 m (robots climb 0.4) to the 9 m ring


def new(pal):
    return Model(pal)


def finish(name, m, ao, bevel=0.0, hull_t=0.02, cols=None):
    return _finish(PFX, TRIS, name, m, ao, bevel, hull_t, cols)


def blob(m, c, r, color, seg=(7, 5), scale=(1, 1, 1)):
    return m.sphere(c, r, color, seg=seg, scale=scale)


# ================================================================ ridges (wall modules, front = -Y)
def build_ridges(pal, ao):
    for name, hgt, seed in (('Ridge_A', 5.6, 1), ('Ridge_B', 6.6, 2), ('Ridge_C', 7.6, 3)):
        rnd = random.Random(seed)
        m = new(pal)
        m.box((0, 0.05, hgt / 2), (1.0, 0.9, hgt), 'rock', bevel=False)
        z = 0.0
        k = 0
        while z < hgt - 0.3:   # strata on the front layer (inside the cell), alternating tones
            h = min(hgt - z, rnd.uniform(1.6, 2.4))
            m.box((0, -0.45, z + h / 2), (1.0, 0.1, h), ['rock2', 'rock', 'rock3'][k % 3], bevel=False)
            z += h
            k += 1
        m.box((0, 0, hgt + 0.12), (1.0, 1.0, 0.24), 'grass', bevel=False)
        for vx in (rnd.uniform(-0.3, -0.05), rnd.uniform(0.08, 0.3)):   # vines hanging off the cap
            L = rnd.uniform(1.0, 2.6)
            m.box((vx, -0.52, hgt - L / 2), (0.08, 0.03, L), 'moss', bevel=False)
        finish(name, m, ao)
    m = new(pal)
    m.box((0, 0, 4.0), (1.0, 1.0, 8.0), 'rock2', bevel=False)
    m.box((0, 0, 8.12), (1.0, 1.0, 0.24), 'grass', bevel=False)
    for z, c in ((1.5, 'rock'), (4.5, 'rock3')):
        m.box((0, 0, z), (1.04, 1.04, 1.1), c, bevel=False)
    finish('Ridge_Pillar', m, ao)


# ================================================================ redwood (landmark, climbable)
def spiral():
    """(k, top, cx, cy) for every branch step"""
    out = []
    for k in range(1, NSTEP + 1):
        a = math.radians((k - 24) * 30)
        out.append((k, k * STEP, math.cos(a) * 1.8, math.sin(a) * 1.8))
    return out


RING = [  # (x0, y0, x1, y1): east, north, west limbs; north-east, north-west corners (edges only touch)
    (1.0, -0.8, 3.0, 0.8), (-0.8, 1.0, 0.8, 3.0), (-3.0, -0.8, -1.0, 0.8),
    (0.8, 0.8, 2.35, 2.35), (-2.35, 0.8, -0.8, 2.35),
]


def build_redwood(pal, ao, name, seed, crown):
    rnd = random.Random(seed)
    m = new(pal)
    # trunk: flared base, long taper; vertical bark ridges
    m.cyl((0, 0, 0), 1.35, 1.05, 1.5, 'redbark', seg=12, bevel=False)
    m.cyl((0, 0, 1.5), 1.05, 0.62, 28.5, 'redbark', seg=12, bevel=False, caps=False)
    m.cyl((0, 0, 30.0), 0.62, 0.05, 2.5, 'bark2', seg=12, bevel=False)
    cols = [col_box(-1.15, -1.15, 0, 1.15, 1.15, 1.5), col_box(-1.0, -0.45, 1.5, 1.0, 0.45, 30), col_box(-0.45, -1.0, 1.5, 0.45, 1.0, 30),
            col_box(-0.74, -0.74, 1.5, 0.74, 0.74, 30)]
    # branch steps: a split shelf (light split-wood top, bark sides) on a broken stub out of the trunk
    for (k, top, cx, cy) in spiral():
        m.box((cx, cy, top - 0.15), (1.1, 1.1, 0.3), 'bark', bevel=False)
        m.box((cx, cy, top + 0.01), (0.9, 0.9, 0.02), 'split', bevel=False)
        a = math.atan2(cy, cx)
        r0, r1 = 0.85, 2.2
        m.beam((math.cos(a) * r0, math.sin(a) * r0, top - 0.55), (math.cos(a) * r1, math.sin(a) * r1, top - 0.42 - 0.1 * (k % 3)), 0.26, 'bark2')
        cols.append(col_box(cx - 0.55, cy - 0.55, top - 0.3, cx + 0.55, cy + 0.55, top, True))
    # the ring of limbs at 9 m
    for i, (x0, y0, x1, y1) in enumerate(RING):
        m.box(((x0 + x1) / 2, (y0 + y1) / 2, RING_Z - RING_T / 2), (x1 - x0, y1 - y0, RING_T), 'bark', bevel=False)
        m.box(((x0 + x1) / 2, (y0 + y1) / 2, RING_Z + 0.01), (x1 - x0 - 0.2, y1 - y0 - 0.2, 0.02), 'split', bevel=False)
        cols.append(col_box(x0, y0, RING_Z - RING_T, x1, y1, RING_Z, True))
    for (x, y) in ((2.0, 0.0), (0.0, 2.0), (-2.0, 0.0)):   # under-limb braces into the trunk
        m.beam((x * 0.4, y * 0.4, RING_Z - 1.6), (x, y, RING_Z - RING_T - 0.01), 0.3, 'bark2')
    # crown: broken stubs above head height, then layered foliage
    for i in range(6):
        a = i * 1.1 + rnd.uniform(-0.2, 0.2)
        z = 12.5 + i * 1.6
        m.beam((math.cos(a) * 0.5, math.sin(a) * 0.5, z), (math.cos(a) * 2.6, math.sin(a) * 2.6, z + 0.8), 0.22, 'bark2')
    for i, (z, r) in enumerate(crown):
        for j in range(3):
            a = j * 2.1 + i * 0.9
            blob(m, (math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, z + j * 0.3), r * rnd.uniform(0.7, 0.85), ['leaf', 'leaf2', 'leaf3'][(i + j) % 3], seg=(8 + j, 5 + (i % 2)))
    finish(name, m, ao, cols=cols)


# ================================================================ trees, plants, garden
def build_trees(pal, ao):
    for name, seed, h in (('Oak_A', 11, 5.2), ('Oak_B', 12, 6.0)):
        rnd = random.Random(seed)
        m = new(pal)
        m.cyl((0, 0, 0), 0.42, 0.32, h, 'bark', seg=8, bevel=False)
        for i in range(4):
            a = i * 1.57 + rnd.uniform(-0.3, 0.3)
            m.beam((0, 0, h - 1.2 + i * 0.25), (math.cos(a) * 1.8, math.sin(a) * 1.8, h + 0.8 + i * 0.2), 0.2, 'bark2')
        for i in range(6):
            a = i * 1.05 + rnd.uniform(-0.2, 0.2)
            rr = rnd.uniform(1.0, 1.8)
            blob(m, (math.cos(a) * rr, math.sin(a) * rr, h + 1.2 + rnd.uniform(-0.3, 0.8)), rnd.uniform(1.3, 1.8), ['leaf', 'leaf2', 'leaf3'][i % 3], seg=(7 + i % 3, 5))
        blob(m, (0, 0, h + 2.4), 2.0, 'leaf3', seg=(9, 6))
        finish(name, m, ao, cols=[col_box(-0.38, -0.38, 0, 0.38, 0.38, h)])
    for name, fruit, seed in (('Fruit_Apple', 'apple', 21), ('Fruit_Orange', 'orange', 22), ('Fruit_Pear', 'pear', 23)):
        rnd = random.Random(seed)
        m = new(pal)
        m.cyl((0, 0, 0), 0.16, 0.12, 2.5, 'bark', seg=6, bevel=False)
        blob(m, (0, 0, 3.2), 1.3, 'leaf3', seg=(9, 6))
        blob(m, (0.5, 0.3, 2.95), 0.8, 'leaf', seg=(7, 5))
        blob(m, (-0.55, -0.25, 3.0), 0.8, 'leaf2', seg=(8, 5))
        for i in range(8):
            a = i * 0.785 + rnd.uniform(-0.2, 0.2)
            rr = 1.25 + rnd.uniform(-0.05, 0.12)
            m.sphere((math.cos(a) * rr, math.sin(a) * rr, 2.9 + rnd.uniform(-0.3, 0.6)), 0.12, fruit, seg=(6, 4))
        finish(name, m, ao, cols=[col_box(-0.2, -0.2, 0, 0.2, 0.2, 2.5)])


def blades(m, rnd, n, r, h0, h1, colors, w=0.06):
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0, r)
        x, y = math.cos(a) * rr, math.sin(a) * rr
        tx, ty = x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15)
        m.cyl((x, y, 0), w, 0.0, rnd.uniform(h0, h1), colors[i % len(colors)], seg=3, rot=(rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(0, 120)), bevel=False)


def build_plants(pal, ao):
    for name, seed, n, h in (('Grass_A', 31, 9, 0.8), ('Grass_B', 32, 7, 0.6)):
        m = new(pal)
        blades(m, random.Random(seed), n, 0.4, h * 0.6, h, ['grass', 'grass2', 'grass3'])
        finish(name, m, ao, hull_t=0.012)
    m = new(pal)   # reeds / long plants
    rnd = random.Random(33)
    blades(m, rnd, 5, 0.35, 1.2, 1.7, ['grass2', 'grass'], w=0.045)
    for i, (x, y, h) in enumerate(((-0.2, -0.1, 1.5), (0.15, 0.2, 1.62), (0.05, -0.27, 1.4))):
        m.cyl((x, y, 0), 0.015, 0.015, h, 'grass2', seg=4, bevel=False)
        m.cyl((x, y, h), 0.05, 0.05, 0.25, 'bark', seg=6, bevel=False)
    finish('Reeds', m, ao, hull_t=0.012)
    m = new(pal)   # fern
    rnd = random.Random(34)
    for i in range(6):
        a = i * 1.047 + rnd.uniform(-0.2, 0.2)
        m.beam((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.05), (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.35 + 0.03 * i), 0.07 + 0.002 * i, 'leaf3' if i % 2 else 'leaf')
    finish('Fern', m, ao, hull_t=0.012)
    for name, cols_, seed in (('Flowers_A', ['petal1', 'petal2'], 41), ('Flowers_B', ['petal3', 'petal4'], 42), ('Flowers_C', ['petal2', 'petal1', 'petal3'], 43)):
        m = new(pal)
        rnd = random.Random(seed)
        blades(m, rnd, 3, 0.35, 0.25, 0.4, ['grass', 'grass2'])
        for i in range(4):
            x, y, h = rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(0.35, 0.65)
            m.cyl((x, y, 0), 0.012, 0.012, h, 'grass2', seg=4, bevel=False)
            m.sphere((x, y, h + 0.05), 0.09, cols_[i % len(cols_)], seg=(5, 3), scale=(1, 1, 0.6))
        finish(name, m, ao, hull_t=0.012)
    m = new(pal)   # sunflowers (solid: you cannot walk through the stalks)
    rnd = random.Random(44)
    for i in range(3):
        x, y, h = [(-0.2, -0.15, 2.0), (0.22, 0.05, 2.3), (-0.05, 0.25, 1.8)][i]
        m.cyl((x, y, 0), 0.04, 0.03, h, 'grass2', seg=5, bevel=False)
        m.cyl((x, y - 0.02, h), 0.24, 0.24, 0.05, 'sun', seg=10, rot=(80, 0, 0), bevel=False)
        m.cyl((x, y - 0.07, h), 0.11, 0.11, 0.03, 'bark2', seg=8, rot=(80, 0, 0), bevel=False)
        m.beam((x, y, h * 0.5), (x + 0.25, y, h * 0.5 + 0.15), 0.08, 'leaf3')
    finish('Sunflowers', m, ao, cols=[col_box(-0.3, -0.3, 0, 0.3, 0.3, 2.0)])
    for name, extra, seed in (('Bush_A', None, 51), ('Bush_B', None, 52), ('Berry', 'berry', 53)):
        m = new(pal)
        rnd = random.Random(seed)
        blob(m, (0, 0, 0.45), 0.5, 'leaf', seg=(8, 5))
        blob(m, (0.22, 0.12, 0.62), 0.33, 'leaf3', seg=(7, 5))
        blob(m, (-0.2, -0.15, 0.58), 0.34, 'leaf2', seg=(6, 5))
        if extra:
            for i in range(5):
                a = i * 1.25
                m.sphere((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.35 + (i % 3) * 0.15), 0.07, extra, seg=(4, 3))
        finish(name, m, ao, cols=[col_box(-0.45, -0.45, 0, 0.45, 0.45, 0.95)])


def build_garden(pal, ao):
    m = new(pal)   # raised vegetable bed 2 x 4 (long along Y)
    m.box((0, 0, 0.21), (1.9, 3.9, 0.42), 'plank', bevel=False)
    m.box((0, 0, 0.425), (1.7, 3.7, 0.01), 'soil', bevel=False)
    rnd = random.Random(61)
    for k in range(4):   # cabbages
        m.sphere((-0.5, -1.4 + k * 0.6, 0.55), 0.2, 'cabbage', seg=(7, 5))
    for k in range(6):   # carrot tops
        x, y = 0.05, -1.5 + k * 0.5
        m.cyl((x, y, 0.43), 0.05, 0.0, 0.12, 'carrot', seg=4, bevel=False)
        m.cyl((x, y, 0.55), 0.03, 0.0, 0.2, 'grass3', seg=3, bevel=False)
    for k in range(3):   # tomato stakes
        x, y = 0.55, -1.2 + k * 1.2
        m.cyl((x, y, 0.43), 0.025, 0.025, 0.75, 'plank2', seg=4, bevel=False)
        blob(m, (x, y, 0.95), 0.2, 'leaf', seg=(6, 4))
        for j in range(3):
            m.sphere((x + 0.15 * math.cos(j * 2.1), y + 0.15 * math.sin(j * 2.1), 0.8 + j * 0.08), 0.07, 'tomato', seg=(6, 4))
    finish('VeggieBed', m, ao, cols=[col_box(-0.95, -1.95, 0, 0.95, 1.95, 1.15)])
    m = new(pal)   # pumpkin patch 2 x 2
    for k, (x, y, r) in enumerate(((-0.45, -0.4, 0.3), (0.4, -0.3, 0.36), (0.0, 0.45, 0.28), (0.55, 0.55, 0.2))):
        m.sphere((x, y, r * 0.7), r, 'pumpkin', seg=(8, 5), scale=(1, 1, 0.75))
        m.cyl((x, y, r * 1.2), 0.03, 0.03, 0.12, 'bark2', seg=4, bevel=False)
    for k in range(5):
        a = k * 1.25
        m.beam((0, 0, 0.04), (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.06), 0.05, 'leaf')
        blob(m, (math.cos(a) * 0.7, math.sin(a) * 0.7, 0.12), 0.14, 'leaf3', seg=(5, 4))
    finish('Pumpkins', m, ao, cols=[col_box(-0.9, -0.9, 0, 0.9, 0.9, 0.55)])
    for name, seed in (('Rock_A', 71), ('Rock_B', 72)):
        rnd = random.Random(seed)
        m = new(pal)
        pts = [(math.cos(a) * rnd.uniform(0.35, 0.45), math.sin(a) * rnd.uniform(0.35, 0.45), 0.0) for a in [i * 0.9 for i in range(7)]]
        pts += [(math.cos(a) * rnd.uniform(0.2, 0.32), math.sin(a) * rnd.uniform(0.2, 0.32), rnd.uniform(0.55, 0.8)) for a in [i * 1.3 + 0.4 for i in range(5)]]
        hull_pts(m, pts, lambda f: 'moss' if f.normal.z > 0.75 else ('rock' if f.normal.x > 0 else 'rock2'))
        finish(name, m, ao, cols=[col_box(-0.42, -0.42, 0, 0.42, 0.42, 0.75)])
    m = new(pal)   # fallen log 3 x 1 (along X)
    m.cyl((-1.45, 0, 0.38), 0.38, 0.36, 2.9, 'bark', seg=10, rot=(0, 90, 0), bevel=False)
    m.cyl((-1.46, 0, 0.38), 0.3, 0.3, 0.02, 'split', seg=10, rot=(0, 90, 0), bevel=False)
    blob(m, (0.3, 0, 0.72), 0.3, 'moss', seg=(7, 4), scale=(2.0, 1.0, 0.4))
    for k in (-0.8, 0.9):
        m.cyl((k, 0.25, 0.5), 0.08, 0.0, 0.5, 'bark2', seg=5, rot=(-50, 0, 0), bevel=False)
    finish('Log', m, ao, cols=[col_box(-1.45, -0.4, 0, 1.45, 0.4, 0.78)])
    m = new(pal)   # lily pond 4 x 4 (flat, no collision)
    m.cyl((0, 0, 0), 1.8, 1.8, 0.02, 'water', seg=18, bevel=False)
    for i in range(9):
        a = i * 0.7
        m.cyl((math.cos(a) * 1.2, math.sin(a) * 1.2, 0.02), 0.22, 0.22, 0.005 + 0.002 * (i % 2), 'lily', seg=8, bevel=False)
    for i in range(14):
        a = i / 14 * 2 * math.pi
        m.sphere((math.cos(a) * 1.9, math.sin(a) * 1.9, 0.04), 0.13, 'rock3' if i % 2 else 'rock', seg=(5, 3), scale=(1.3, 1.0, 0.5))
    m.sphere((0.5, -0.4, 0.035), 0.06, 'petal1', seg=(5, 3))
    finish('Pond', m, ao, hull_t=0.012)
    m = new(pal)   # picket fence run module (along X)
    for k in range(4):
        x = -0.375 + k * 0.25
        m.box((x, 0, 0.45), (0.1, 0.04, 0.9), 'fence', bevel=False)
        m.cyl((x, 0, 0.9), 0.05, 0.0, 0.1, 'fence', seg=4, rot=(0, 0, 45), bevel=False)
    for z in (0.3, 0.7):
        m.box((0, 0.035, z), (1.0, 0.03, 0.08), 'fence', bevel=False)
    finish('Fence', m, ao, cols=[col_box(-0.5, -0.06, 0, 0.5, 0.06, 1.0)])
    m = new(pal)   # fruit crate
    m.box((0, 0, 0.25), (0.8, 0.6, 0.5), 'plank', bevel=False)
    for i in range(6):
        m.sphere((-0.25 + (i % 3) * 0.25, -0.12 + (i // 3) * 0.24, 0.55), 0.1, ['apple', 'orange', 'pear'][i % 3], seg=(6, 4))
    finish('Crate', m, ao, cols=[col_box(-0.4, -0.3, 0, 0.4, 0.3, 0.6)])


def build_bridge(pal, ao):
    """plank walkway cell for the 9 m layer: deck top at 0, rope rail along the +Z (game) edge = Blender -Y"""
    m = new(pal)
    for k in range(2):
        m.box((-0.25 + k * 0.5, 0, -0.08), (0.49, 1.0, 0.16), 'plank' if k % 2 else 'plank2', bevel=False)
    m.box((0, -0.45, 0.5), (0.08, 0.08, 1.0), 'bark', bevel=False)
    m.box((0, -0.45, 0.95), (1.0, 0.04, 0.04), 'rope', bevel=False)
    finish('Bridge', m, ao, cols=[col_box(-0.5, -0.5, -0.16, 0.5, 0.5, 0, True), col_box(-0.5, -0.5, 0, 0.5, -0.42, 1.0)])


# ================================================================ gate, corridor hedge, hatch, backdrop
def build_gate(pal, ao, bw, ht):
    m = new(pal)
    for sx in (-1, 1):
        m.box((sx * 1.72, 0, 1.75), (0.5, 0.5, 3.5), 'bark', bevel=False)
    m.cyl((-2.3, 0, 3.75), 0.28, 0.28, 4.6, 'bark2', seg=8, rot=(0, 90, 0), bevel=False)
    for fy in (-1, 1):
        for k in range(10):
            m.box((-1.5 + (k + 0.5) * 0.3, fy * 0.28, 3.3), (0.3, 0.02 + 0.004 * (k % 2), 0.24), 'amber' if k % 2 else 'ink', bevel=False)
    blob(m, (-1.9, 0, 4.1), 0.45, 'leaf3', seg=(7, 5))
    blob(m, (1.8, 0.1, 4.05), 0.4, 'leaf', seg=(7, 5))
    finish('GateFrame', m, ao, bevel=bw)
    m = new(pal)
    Hs, n = 3.05, 8
    for i in range(n):
        z = 0.55 + (i + 0.5) * (Hs - 0.55) / n
        m.box((0, 0, z), (3.0, 0.14, (Hs - 0.55) / n - 0.05), 'plank' if i % 2 else 'plank2', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.16, 0.5), 'ink' if k % 2 else 'amber', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.18, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    m = new(pal)   # hedge corridor wall, 1 m along Y, inner face +X
    m.box((0, 0, 1.3), (0.5, 1.0, 2.6), 'hedge', bevel=False)
    blob(m, (0.2, -0.2, 2.5), 0.3, 'hedge2', seg=(6, 4))
    blob(m, (0.22, 0.25, 1.4), 0.25, 'leaf3', seg=(6, 4))
    finish('TrailWall', m, ao)
    m = new(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'plank2', seg=20)
    m.cyl((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, bevel=False)
    finish('Hatch', m, ao, bevel=0.015)


def build_backdrop(pal):
    for name, seed, Hh, R in (('Backdrop_HillA', 81, 22, 30), ('Backdrop_HillB', 82, 16, 26)):
        rnd = random.Random(seed)
        m = new(pal)
        pts = [(math.cos(a) * R * rnd.uniform(0.85, 1.05), math.sin(a) * R * 0.55, 0.0) for a in [i * 0.7 for i in range(9)]]
        pts += [(math.cos(a) * R * 0.45, math.sin(a) * R * 0.3, Hh * rnd.uniform(0.6, 0.8)) for a in [i * 1.1 + 0.3 for i in range(6)]]
        pts.append((rnd.uniform(-3, 3), 0, Hh))
        hull_pts(m, pts, lambda f: 'far' if f.normal.z > 0.6 else 'far2')
        for i in range(9):
            x, y = rnd.uniform(-R * 0.6, R * 0.6), rnd.uniform(-R * 0.25, R * 0.25)
            z = Hh * max(0.0, 1 - abs(x) / (R * 0.9)) * 0.6
            h = rnd.uniform(8, 14)
            m.cyl((x, y, z), 0.5, 0.3, h * 0.5, 'redbark', seg=5, bevel=False)
            m.cyl((x, y, z + h * 0.35), h * 0.18, 0.2, h * 0.75, 'far2', seg=6, bevel=False)
        finish(name, m, False, hull_t=0.2)


def build_kit_grove(ao):
    pal = Palette(FAM)
    bw, ht = CFG[FAM]
    build_ridges(pal, ao)
    build_redwood(pal, ao, 'Landmark_Redwood_A', 1, [(15.0, 3.6), (18.5, 3.2), (22.0, 2.8), (25.5, 2.2), (28.5, 1.4)])
    build_redwood(pal, ao, 'Landmark_Redwood_B', 2, [(14.0, 3.9), (17.0, 3.4), (20.5, 3.0), (24.0, 2.5), (27.0, 1.8), (29.5, 1.0)])
    build_trees(pal, ao)
    build_plants(pal, ao)
    build_garden(pal, ao)
    build_bridge(pal, ao)
    build_gate(pal, ao, bw, ht)
    build_backdrop(pal)
    print('kit-grove: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:12]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-grove'
BUILD = build_kit_grove
