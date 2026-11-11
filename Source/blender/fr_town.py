"""INKBOLT kit-frontier, zone 1 (the stockade settlement): the log palisade and its corner bundles, the timber gate
and its plank leaves, the trail palisade, the hatch, the watchtowers (stair up to a roofed platform), the water
tower (landmark), the well, the street arch, split-rail corral fences, hitching rails, troughs, hay, the covered
wagon and the hand cart, crates, barrels, firewood stacks, lantern posts, the signpost, and the supply depot's
modern gear: the diesel generator, the solar array, the radio mast, the fuel tank, the supply tent, cable spools.
See fr_base.py for the conventions."""
import math
import random

from fr_base import (polyline, FLOOR, RISE, TREAD, WALL_H, by_normal, barkcol, rock, log_x, log_y, post, rail_run, lantern,
                     crate, barrel, sack, shed_roof, gable, stairs)


# ================================================================ palisade (zone 1 wall modules, 1 m, face -Y)
def palisade_log(k, x, y, h, r, rnd, z0=0.0, seg=5, ink=True):
    """one sharpened stockade log"""
    k.cyl(x, y, z0, r, r * 0.96, h - z0, 'log' if rnd.random() < 0.6 else 'log3', seg=seg, caps=False, ink=ink)
    k.cyl(x, y, h, r * 0.96, 0.02, r * 1.6, 'logEnd', seg=seg, caps=False, ink=ink)


def build_palisade(k, ao):
    for name, seed, extra in (('Palisade_A', 11, None), ('Palisade_B', 12, 'brace'), ('Palisade_C', 13, 'lamp'),
                              ('Palisade_D', 14, 'patch'), ('Palisade_EL', 16, 'L'), ('Palisade_ER', 17, 'R')):
        rnd = random.Random(seed)
        k.begin()
        for i, x in enumerate((-0.25, 0.25)):
            h = WALL_H - 0.25 + rnd.uniform(-0.12, 0.12) + (0.1 if i else 0.0)
            palisade_log(k, x, -0.2, h, 0.255, rnd)
        # the backing rail on the inside (-Y) face, spiked through (stopped short of a corner on an end module)
        k.bx(-0.3 if extra == 'L' else -0.5, 0.3 if extra == 'R' else 0.5, -0.56, -0.42, 2.6, 2.78, 'log2')
        if extra == 'brace':
            k.beam((0.0, -0.5, 2.55), (0.0, -1.25, 0.0), 0.14, 'log2')
            k.bx(-0.12, 0.12, -1.38, -1.14, 0.0, 0.08, 'stone2', ink=False)
            k.col(-0.08, 0.08, -1.22, -0.76, 0.0, 1.6)
        elif extra == 'lamp':
            k.bx(-0.04, 0.04, -0.72, -0.45, 2.5, 2.56, 'iron2', ink=False)
            lantern(k, 0.0, -0.68, 2.5)
        elif extra == 'patch':
            k.bx(-0.48, 0.48, -0.47, -0.43, 1.6, 2.3, 'plankG')
        k.finish(name, ao=ao)
    # corner bundle (a corner or a cell walled on both sides): four logs and a binding band
    rnd = random.Random(15)
    k.begin()
    for (x, y) in ((-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)):
        palisade_log(k, x, y, WALL_H + 0.1 + rnd.uniform(-0.1, 0.15), 0.25, rnd)
    k.cyl(0, 0, 2.4, 0.62, 0.62, 0.12, 'iron2', seg=8, caps=False, ink=False)
    k.finish('Palisade_Corner', ao=ao)


def build_gate(k, ao):
    """GateFrame (|x| <= 2.5): two big gate posts, palisade logs out to the trail walls, a crossbeam with a little
    shingle hood and two lanterns. GateShutter: two plank leaves (Z-braced, iron straps), 3 m x 3.05 m."""
    rnd = random.Random(21)
    k.begin()
    for sx in (-1, 1):
        x = sx * 1.82
        k.bx(x - 0.36, x + 0.36, -0.36, 0.36, 0.0, 0.35, 'stone')
        k.cyl(x, 0, 0.35, 0.3, 0.27, 4.85, 'log', seg=8)
        k.cyl(x, 0, 5.2, 0.27, 0.05, 0.4, 'logEnd', seg=8, caps=False)
        palisade_log(k, sx * 2.25, -0.2, WALL_H - 0.15, 0.255, rnd)
        lantern(k, sx * 1.82, -0.42, 3.05)
        k.bx(x - 0.03, x + 0.03, -0.44, -0.29, 3.0, 3.06, 'iron2', ink=False)
    log_x(k, -2.42, 2.42, 0.0, 3.62, 0.24, 'log2')
    log_x(k, -2.2, 2.2, 0.0, 4.25, 0.2, 'log')
    for sx in (-1, 1):
        k.beam((sx * 0.6, 0.0, 3.86), (sx * 1.5, 0.0, 4.07), 0.12, 'log2')
    shed_roof(k, -2.45, 2.45, -0.7, 0.0, 4.4, 4.95, 0.1, 'shingle', 'shingle2')
    shed_roof(k, -2.45, 2.45, 0.7, 0.0, 4.4, 4.95, 0.1, 'shingle', 'shingle2')
    k.col(-2.5, -1.5, -0.36, 0.36, 0.0, 4.8)
    k.col(1.5, 2.5, -0.36, 0.36, 0.0, 4.8)
    k.finish('GateFrame', ao=ao)
    k.begin()
    Hs = 3.05
    for i in range(10):
        x0 = -1.5 + i * 0.3 + 0.01
        k.bx(x0, x0 + 0.28, -0.07, 0.07, 0.0, Hs - 0.04 * (i % 2), 'plank' if i % 3 else 'plank2', ink=False)
    for sx in (-1, 1):
        for z in (0.45, 2.55):
            k.bx(min(sx * 0.02, sx * 1.48), max(sx * 0.02, sx * 1.48), -0.13, -0.07, z, z + 0.2, 'plank2', ink=False)
        k.beam((sx * 0.1, -0.1, 0.6), (sx * 1.4, -0.1, 2.5), 0.12, 'plank2', ink=False)
        for z in (0.5, 2.6):
            k.bx(min(sx * 0.3, sx * 1.45), max(sx * 0.3, sx * 1.45), -0.16, -0.13, z + 0.03, z + 0.14, 'iron2', ink=False)
    k.bx(-0.04, 0.04, -0.175, -0.076, 0.0, Hs - 0.04, 'iron2', ink=False)
    obj = k.finish('GateShutter', ao=False)
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)
    k.tris[k.prefix + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_trail(k, ao):
    """1 m trail palisade along Blender Y (the trail face is +X), 2.6 m; variants with a lantern, firewood, a brace"""
    for name, seed, extra in (('TrailWall', 31, None), ('TrailWall_B', 32, 'lamp'), ('TrailWall_C', 33, 'wood'), ('TrailWall_D', 34, 'brace')):
        rnd = random.Random(seed)
        k.begin()
        for y in (-0.25, 0.25):
            palisade_log(k, -0.06, y, 2.6 - 0.2 + rnd.uniform(-0.1, 0.1), 0.2, rnd)
        k.bx(0.14, 0.26, -0.5, 0.5, 1.7, 1.86, 'log2')
        if extra == 'lamp':
            k.bx(0.26, 0.44, -0.03, 0.03, 1.9, 1.95, 'iron2', ink=False)
            lantern(k, 0.41, 0.0, 1.9)
        elif extra == 'wood':
            for i in range(3):
                for j in range(2):
                    log_y(k, -0.46, 0.46, 0.4 + j * 0.15 + (i % 2) * 0.075, 0.08 + i * 0.13, 0.065, 'log' if (i + j) % 2 else 'log2', seg=5, ink=False)
        elif extra == 'brace':
            k.beam((0.3, 0.0, 1.9), (0.62, 0.0, 0.0), 0.12, 'log2')
        k.finish(name, ao=ao)
    # the hatch: a cellar trapdoor in a log frame (iron ring, straps)
    k.begin()
    k.bx(-1.3, 1.3, -1.3, 1.3, 0.0, 0.1, 'log2')
    k.bx(-1.05, 1.05, -1.05, 1.05, 0.1, 0.13, 'plank', ink=False)
    for i in range(1, 7):
        x = -1.05 + i * 0.3
        k.qz(x - 0.012, x + 0.012, -1.04, 1.04, 0.134, 1, 'plank2')
    for y in (-0.6, 0.6):
        k.bx(-1.0, 1.0, y - 0.06, y + 0.06, 0.13, 0.15, 'iron2', ink=False)
    k.cyl(0, 0, 0.15, 0.16, 0.16, 0.03, 'iron', seg=10, caps=False)
    k.finish('Hatch', ao=ao)


def xbrace(k, a, b, z0, z1, t, c, shrink=1.0, d=0.07):
    """X bracing between two legs at a and b (plan points) from z0 to z1: the two diagonals stand d apart (no shared
    faces where they cross); shrink scales the top points toward the origin (splayed legs)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L * d, dx / L * d
    for (p, q, e) in ((a, b, -1), (b, a, 1)):
        k.beam((p[0] + px * e, p[1] + py * e, z0), (q[0] * shrink + px * e, q[1] * shrink + py * e, z1), t, c)


# ================================================================ watchtower [3, 8]: platform at the back (+Y), stair from the front
TOWER_Z = 20 * RISE          # 3.6 m


def build_tower(k, ao):
    rnd = random.Random(41)
    k.begin()
    Z = TOWER_Z
    py0, py1 = 1.0, 4.0
    # legs (to the roof) on stone footings, X braces between the back legs and the side legs (above head height)
    legs = [(-1.3, 1.2), (1.3, 1.2), (-1.3, 3.8), (1.3, 3.8)]
    for (x, y) in legs:
        k.bx(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0.0, 0.3, 'stone')
        k.cyl(x, y, 0.3, 0.17, 0.15, Z + 2.25 - 0.3, 'log', seg=6)
        k.col(x - 0.17, x + 0.17, y - 0.17, y + 0.17, 0.0, Z + 1.0)
    for (a, b) in (((-1.3, 3.8), (1.3, 3.8)), ((-1.3, 1.2), (-1.3, 3.8)), ((1.3, 1.2), (1.3, 3.8))):
        xbrace(k, a, b, 2.0, Z - 0.35, 0.11, 'log2')
    # the platform deck with joists, a log railing (gap where the stair arrives) and a shingle roof
    k.bx(-1.5, 1.5, py0, py1, Z - 0.12, Z, 'plank')
    for i in range(1, 10):
        x = -1.5 + i * 0.3
        k.qz(x - 0.012, x + 0.012, py0 + 0.01, py1 - 0.01, Z + 0.004, 1, 'plank2')
    for y in (py0 + 0.2, py1 - 0.2):
        k.bx(-1.5, 1.5, y - 0.09, y + 0.09, Z - 0.34, Z - 0.12, 'log2')
    k.wcol(-1.5, 1.5, py0, py1, Z - 0.2, Z)
    rail_run(k, 'x', -1.44, 1.44, py1 - 0.06, Z, 1.05, 'log2', posts=1.44, r=0.05)
    rail_run(k, 'y', py0 + 0.06, py1 - 0.06, -1.44, Z, 1.05, 'log2', posts=1.44, r=0.05)
    rail_run(k, 'y', py0 + 0.06, py1 - 0.06, 1.44, Z, 1.05, 'log2', posts=1.44, r=0.05)
    rail_run(k, 'x', -1.44, -0.7, py0 + 0.06, Z, 1.05, 'log2', posts=0.74, r=0.05)
    rail_run(k, 'x', 0.7, 1.44, py0 + 0.06, Z, 1.05, 'log2', posts=0.74, r=0.05)
    for (x0, x1, y0, y1) in ((-1.5, 1.5, py1 - 0.12, py1), (-1.5, -1.38, py0, py1), (1.38, 1.5, py0, py1), (-1.5, -0.65, py0, py0 + 0.12), (0.65, 1.5, py0, py0 + 0.12)):
        k.col(x0, x1, y0, y1, Z, Z + 1.08)
    # a sack-and-plank parapet on the outer side, a lantern under the roof, the bell
    k.bx(-1.37, 1.37, py1 - 0.115, py1 - 0.075, Z + 0.1, Z + 0.95, 'plankG')
    lantern(k, 0.0, (py0 + py1) / 2, Z + 2.1)
    k.cyl(1.0, py1 - 0.5, Z + 1.75, 0.13, 0.17, 0.25, 'fuel', seg=8)
    k.cyl(1.0, py1 - 0.5, Z + 2.0, 0.02, 0.02, 0.22, 'iron2', seg=4, ink=False)
    gable(k, -1.5, 1.5, py0, py1, Z + 2.25, Z + 3.2, 0.12, 'shingle', 'shingle2', over=0.3, ridge_along='y')
    # the stair (20 treads) from the front up to the platform's front edge, with a log handrail each side
    y0 = py0 - 20 * TREAD
    stairs(k, -0.62, 0.62, y0, 0.0, 20, 'plank', 'plank2', dir_=1)
    for x in (-0.7, 0.7):
        k.beam((x, y0 + 0.05, 1.0), (x, py0 + 0.05, Z + 1.0), 0.07, 'log2')
        for t in (0.15, 0.55, 0.92):
            yy = y0 + (py0 - y0) * t
            k.bx(x - 0.04, x + 0.04, yy - 0.04, yy + 0.04, Z * t, Z * t + 1.0, 'log2', ink=False)
    k.finish('Tower', ao=ao)


# ================================================================ water tower (landmark) [6, 6]
def build_watertower(k, ao):
    rnd = random.Random(51)
    k.begin()
    TZ = 7.6          # tank floor
    legs = [(-2.3, -2.3), (2.3, -2.3), (-2.3, 2.3), (2.3, 2.3)]
    for (x, y) in legs:
        k.bx(x - 0.38, x + 0.38, y - 0.38, y + 0.38, 0.0, 0.5, 'stone')
        k.tube((x, y, 0.5), (x * 0.78, y * 0.78, TZ), 0.24, 0.2, 'log', seg=6)
        k.col(x - 0.38, x + 0.38, y - 0.38, y + 0.38, 0.0, 0.5)
        k.col(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0.5, 3.0)
    # cross bracing on two levels (above head height), girts
    for z0, z1 in ((2.6, 5.0), (5.0, TZ - 0.2)):
        for i in range(4):
            a, b = legs[i], legs[(i + 1) % 4]
            fa0, fa1 = 1 - 0.22 * (z0 - 0.5) / (TZ - 0.5), 1 - 0.22 * (z1 - 0.5) / (TZ - 0.5)
            xbrace(k, (a[0] * fa0, a[1] * fa0), (b[0] * fa0, b[1] * fa0), z0, z1, 0.1, 'log2', shrink=(fa1 / fa0))
        fz = 1 - 0.22 * (z1 - 0.5) / (TZ - 0.5)
        for i in range(4):
            a, b = legs[i], legs[(i + 1) % 4]
            k.beam((a[0] * fz, a[1] * fz, z1), (b[0] * fz, b[1] * fz, z1), 0.13, 'log2')
    # catwalk deck round the tank foot with a rail
    k.cyl(0, 0, TZ - 0.15, 2.75, 2.75, 0.15, 'plank', seg=12)
    for i in range(8):
        a = (i + 0.5) / 8 * 2 * math.pi
        x, y = math.cos(a) * 2.65, math.sin(a) * 2.65
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, TZ, TZ + 0.9, 'log2', ink=False)
    k.cyl(0, 0, TZ + 0.86, 2.68, 2.68, 0.06, 'log2', seg=12, caps=False)
    # the staved tank, three iron hoops, a conical shingle roof with a finial
    k.cyl(0, 0, TZ, 2.15, 2.25, 3.2, 'plank2', seg=16)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        k.bxr(math.cos(a) * 2.21, math.sin(a) * 2.21, TZ + 1.6, 0.02, 0.025, 3.18, 'logD', rot=(0, 0, math.degrees(a)), ink=False)
    for z in (TZ + 0.45, TZ + 1.6, TZ + 2.75):
        f = (z - TZ) / 3.2
        r = 2.15 + 0.1 * f + 0.04
        k.cyl(0, 0, z, r, r, 0.08, 'iron2', seg=16, caps=False, ink=False)
    k.cyl(0, 0, TZ + 3.2, 2.5, 0.15, 1.35, 'shingle', seg=16)
    k.cyl(0, 0, TZ + 4.5, 0.12, 0.02, 0.5, 'iron', seg=6)
    # painted name plate on the tank, facing the street (-Y)
    k.bx(-1.3, 1.3, -2.34, -2.3, TZ + 1.85, TZ + 2.6, 'plankW')
    k.text('CINDER RIDGE', 0.0, -2.344, TZ + 1.98, 0.48, 'plankR', maxw=2.4, font='display')
    # spout with its chain, a ladder up the front leg, the outlet pipe down the middle
    k.beam((1.6, -1.2, TZ + 0.3), (3.0, -1.9, TZ - 1.2), 0.18, 'plank2')
    k.beam((3.0, -1.9, TZ - 1.2), (3.0, -1.9, TZ - 0.4), 0.02, 'iron2', ink=False)
    k.cyl(0, 0, 0.5, 0.14, 0.14, TZ - 0.6, 'iron', seg=6)
    k.cyl(0, 0, 0.0, 0.35, 0.35, 0.5, 'stone2', seg=8)
    k.col(-0.35, 0.35, -0.35, 0.35, 0.0, 3.0)
    lx, ly = -2.3 * 0.9, -2.3 * 0.9 - 0.35
    ends = []
    for x in (lx - 0.25, lx + 0.25):
        p0, p1 = (x, ly, 0.0), (x * 0.86, ly * 0.86 - 0.2, TZ)
        k.beam(p0, p1, 0.05, 'plank2')
        ends.append((p0, p1))
    for i in range(1, 15):
        t = i / 15
        a_, b_ = [tuple(p0[j] + (p1[j] - p0[j]) * t for j in range(3)) for (p0, p1) in ends]
        k.beam(a_, b_, 0.035, 'plank2', ink=False)
    k.finish('Landmark_WaterTower', ao=ao)


def build_well(k, ao):
    rnd = random.Random(52)
    k.begin()
    k.cyl(0, 0, 0.0, 0.85, 0.82, 0.8, 'stone', seg=10)
    k.cyl(0, 0, 0.8, 0.86, 0.86, 0.08, 'stone2', seg=10)
    k.disc(0, 0, 0.884, 0.62, 'iron2', n=10)
    k.disc(0, 0, 0.888, 0.5, 'water2', n=10)
    for sx in (-1, 1):
        k.bx(sx * 0.8 - 0.07, sx * 0.8 + 0.07, -0.07, 0.07, 0.0, 2.3, 'log2')
    log_x(k, -0.92, 0.92, 0.0, 1.45, 0.08, 'log', seg=6)
    k.bx(0.92, 0.96, -0.03, 0.03, 1.2, 1.5, 'iron2', ink=False)
    k.bx(0.96, 1.18, -0.03, 0.03, 1.2, 1.25, 'iron2', ink=False)
    k.cyl(0, 0, 0.98, 0.012, 0.012, 0.42, 'rope', seg=4, ink=False)
    k.cyl(0, 0, 0.88, 0.14, 0.17, 0.22, 'plank2', seg=8)
    gable(k, -0.9, 0.9, -0.7, 0.7, 2.25, 2.85, 0.08, 'shingle', 'shingle2', over=0.2, ridge_along='x')
    k.col(-0.86, 0.86, -0.86, 0.86, 0.0, 0.88)
    k.finish('Well', ao=ao)


def build_arch(k, ao):
    """the street arch [12, 1]: two log posts at the street edges and the CINDER RIDGE OUTPOST board"""
    k.begin()
    for sx in (-1, 1):
        x = sx * 5.6
        k.bx(x - 0.3, x + 0.3, -0.3, 0.3, 0.0, 0.25, 'stone')
        k.cyl(x, 0, 0.25, 0.2, 0.18, 5.6, 'log', seg=6)
        k.beam((x, 0, 3.8), (x - sx * 1.2, 0, 4.9), 0.12, 'log2')
        k.col(x - 0.3, x + 0.3, -0.3, 0.3, 0.0, 3.0)
    log_x(k, -5.9, 5.9, 0.0, 5.0, 0.18, 'log2')
    k.bx(-3.6, 3.6, -0.06, 0.06, 3.95, 4.88, 'plank2')
    for x in (-3.0, 3.0):
        k.beam((x, 0.0, 4.88), (x, 0.0, 5.0), 0.04, 'iron2', ink=False)
    k.text('CINDER RIDGE OUTPOST', 0.0, -0.064, 4.17, 0.52, 'plankW', maxw=6.8, font='display')
    k.finish('Arch', ao=ao)


# ================================================================ corral, hitching rails, troughs, hay
def build_corral(k, ao):
    def rails(y0, y1):
        for z in (0.5, 1.15):
            k.bx(-0.04, 0.04, y0, y1, z - 0.045, z + 0.045, 'log')
    k.begin(); rails(-0.497, 0.497); post(k, 0, 0, 0.0, 1.35, 0.075, 'log2'); k.col(-0.08, 0.08, -0.5, 0.5, 0.0, 1.3); k.finish('FenceFull', ao=ao)
    k.begin(); rails(-0.497, -0.06); k.col(-0.08, 0.08, -0.5, 0.0, 0.0, 1.3); k.finish('FenceHalf', ao=ao)
    k.begin(); post(k, 0, 0, 0.0, 1.4, 0.085, 'log2'); k.cyl(0, 0, 1.4, 0.085, 0.04, 0.08, 'logEnd', seg=6, caps=False); k.finish('FencePost', ao=ao)
    # hitching rail [3, 1] along X
    k.begin()
    for x in (-1.25, 1.25):
        post(k, x, 0, 0.0, 1.05, 0.08, 'log2')
    log_x(k, -1.4, 1.4, 0.0, 1.0, 0.07, 'log', seg=6)
    for x in (-0.5, 0.4):
        k.cyl(x, 0.0, 0.62, 0.02, 0.02, 0.38, 'rope', seg=4, ink=False)
    k.col(-1.4, 1.4, -0.1, 0.1, 0.0, 1.07)
    k.finish('HitchRail', ao=ao)
    # water trough [2, 1]
    k.begin()
    k.bx(-0.9, 0.9, -0.35, 0.35, 0.15, 0.7, 'plank2')
    k.qz(-0.82, 0.82, -0.27, 0.27, 0.704, 1, 'water')
    for x in (-0.75, 0.75):
        k.bx(x - 0.06, x + 0.06, -0.3, 0.3, 0.0, 0.15, 'log2', ink=False)
    k.col(-0.9, 0.9, -0.35, 0.35, 0.0, 0.7)
    k.finish('Trough', ao=ao)
    # hay bales [2, 1]: two bales and one on top
    k.begin()
    for (x, z, yaw) in ((-0.48, 0.0, 0), (0.48, 0.0, 3), (0.0, 0.46, -4)):
        k.push(x, 0, yaw, z)
        k.bx(-0.46, 0.46, -0.3, 0.3, 0.0, 0.45, 'hay')
        for u in (-0.2, 0.2):
            k.bx(u - 0.015, u + 0.015, -0.306, 0.306, 0.004, 0.456, 'rope', ink=False)
        k.pop()
    k.col(-0.95, 0.95, -0.32, 0.32, 0.0, 0.9)
    k.finish('HayBales', ao=ao)


# ================================================================ wagons
def wheel(k, x, y, z, r, w=0.09, spokes=6, c='plank2'):
    """spoked wagon wheel in the X-Z... plane facing X (axle along X) centred at (x, y, z)"""
    seg = 8
    polyline(k, [(x, y + math.cos(i / seg * 2 * math.pi) * r, z + math.sin(i / seg * 2 * math.pi) * r) for i in range(seg)], w, c,
             (1, 0, 0), closed=True, cols=('plank', c), ink=False)
    for i in range(spokes):
        a = i / spokes * 2 * math.pi
        k.beam((x, y + math.cos(a) * 0.1, z + math.sin(a) * 0.1), (x, y + math.cos(a) * r * 0.95, z + math.sin(a) * r * 0.95), 0.04, 'plank', ink=False)
    k.cyl(x - 0.09, y, z, 0.11, 0.11, 0.18, 'iron2', seg=6, rot=(0, 90, 0))


def build_wagons(k, ao):
    rnd = random.Random(61)
    # covered wagon [3, 6]: tongue toward -Y, canvas bonnet on hoops, cargo at the tail
    k.begin()
    k.bx(-0.75, 0.75, -1.9, 1.8, 0.85, 1.0, 'plank2')
    for sx in (-1, 1):
        k.bx(sx * 0.75 - 0.04, sx * 0.75 + 0.04, -1.92, 1.82, 1.0, 1.42, 'plankB')
    k.bx(-0.71, 0.71, 1.72, 1.8, 1.0, 1.4, 'plankB')
    k.bx(-0.71, 0.71, -1.9, -1.82, 1.0, 1.4, 'plankB')
    st = []
    for i in range(4):
        y = -1.7 + i * 1.1333
        st.append((y, [(-0.8 * math.cos(a), 1.4 + 1.05 * math.sin(a)) for a in [j / 5 * math.pi for j in range(6)]]))
    # bonnet: a hull per bay between hoops
    for (ya, pa), (yb, pb) in zip(st, st[1:]):
        pts = [(x, ya, z) for (x, z) in pa] + [(x, yb, z) for (x, z) in pb]
        k.hullp(pts, by_normal(top='canvas', bot='canvas2', other='canvas'))
    for (y, prof) in st:
        polyline(k, [(x * 1.02, y, z + 0.01) for (x, z) in prof], 0.04, 'plank2', (0, 1, 0), ink=False)
    for (y, r) in ((-1.35, 0.55), (1.3, 0.72)):
        for sx in (-1, 1):
            wheel(k, sx * 0.98, y, r, r)
        k.bx(-0.95, 0.95, y - 0.05, y + 0.05, r - 0.05, r + 0.05, 'iron2', ink=False)
    k.beam((0.0, -1.95, 0.9), (0.0, -3.0 + 0.05, 0.45), 0.09, 'plank2')
    k.bx(-0.4, 0.4, -2.9, -2.82, 0.4, 0.5, 'plank2', ink=False)
    barrel(k, -0.45, 2.15, 0.0, 0.26, 0.75)
    k.col(-1.07, 1.07, -1.95, 1.85, 0.0, 2.45)
    k.col(-0.3, 0.3, 1.88, 2.42, 0.0, 0.75)
    k.finish('Wagon', ao=ao)
    # hand cart [2, 3]: two big wheels, a plank bed with firewood, handles toward -Y
    k.begin()
    k.bx(-0.6, 0.6, -0.9, 0.9, 0.62, 0.72, 'plank2')
    for sx in (-1, 1):
        k.bx(sx * 0.6 - 0.04, sx * 0.6 + 0.04, -0.9, 0.9, 0.72, 1.05, 'plank')
        wheel(k, sx * 0.72, 0.2, 0.52, 0.52)
        k.beam((sx * 0.5, -0.9, 0.7), (sx * 0.45, -1.45, 0.82), 0.06, 'plank2')
    k.bx(-0.56, 0.56, 0.84, 0.92, 0.72, 1.02, 'plank')
    for i in range(3):
        for j in range(4):
            log_y(k, -0.7, 0.75, -0.4 + j * 0.26 + (i % 2) * 0.12, 0.84 + i * 0.13, 0.065, 'log' if (i + j) % 2 else 'log2', seg=5, ink=False)
    k.bx(-0.06, 0.06, 0.6, 0.72, 0.0, 0.62, 'plank2', ink=False)
    k.col(-0.82, 0.82, -0.95, 0.95, 0.0, 1.2)
    k.finish('Cart', ao=ao)


# ================================================================ crates, barrels, firewood, lantern post, signpost
def build_small(k, ao):
    rnd = random.Random(71)
    k.begin(); crate(k, 0, 0, 0, 0.9, 0.9, 0.8); k.col(-0.45, 0.45, -0.45, 0.45, 0.0, 0.8); k.finish('Crate_A', ao=ao)
    k.begin()
    crate(k, -0.05, 0.02, 0, 0.85, 0.8, 0.62, 'plank2', 'plank')
    crate(k, 0.05, -0.02, 0.62, 0.62, 0.6, 0.48, 'plank', 'plank2')
    k.col(-0.48, 0.38, -0.38, 0.42, 0.0, 1.1)
    k.finish('Crate_B', ao=ao)
    # olive supply crate with a stencil (modern)
    k.begin()
    k.bx(-0.45, 0.45, -0.32, 0.32, 0.0, 0.55, 'olive')
    for x in (-0.38, 0.38):
        k.bx(x - 0.03, x + 0.03, -0.335, 0.335, 0.0, 0.555, 'olive2', ink=False)
    k.qy(-0.3, 0.3, 0.18, 0.4, -0.326, -1, 'olive2')
    k.text('CR-7', 0.0, -0.33, 0.23, 0.13, 'canvas', maxw=0.5, font='sans')
    k.bx(-0.43, 0.43, -0.3, 0.3, 0.55, 1.0, 'olive2')
    k.bx(-0.44, 0.44, -0.31, 0.31, 1.0, 1.04, 'olive')
    k.col(-0.45, 0.45, -0.34, 0.34, 0.0, 1.04)
    k.finish('SupplyCrate', ao=ao)
    k.begin()
    barrel(k, -0.18, 0.12, 0, 0.29, 0.85)
    barrel(k, 0.22, -0.18, 0, 0.27, 0.8, 'plank')
    k.col(-0.48, 0.5, -0.46, 0.42, 0.0, 0.85)
    k.finish('Barrels', ao=ao)
    # fuel drums (modern): two steel drums, one on its side
    k.begin()
    for (x, y, c) in ((-0.22, 0.17, 'cloth'), (0.24, 0.19, 'olive')):
        k.cyl(x, y, 0.0, 0.22, 0.22, 0.88, c, seg=8)
        for z in (0.29, 0.59):
            k.cyl(x, y, z, 0.23, 0.23, 0.03, 'iron2', seg=8, caps=False, ink=False)
    k.cyl(-0.42, -0.25, 0.19, 0.19, 0.19, 0.84, 'fuel', seg=8, rot=(0, 90, 0))
    k.bx(-0.46, 0.46, -0.46, -0.06, 0.0, 0.04, 'log2', ink=False)
    k.col(-0.46, 0.46, -0.46, 0.43, 0.0, 0.88)
    k.finish('Drums', ao=ao)
    # firewood stack [2, 1] between two posts under a plank cap
    k.begin()
    for x in (-0.92, 0.92):
        post(k, x, 0, 0.0, 1.45, 0.06, 'log2')
    for i in range(5):
        for j in range(3):
            y = -0.25 + j * 0.24 + (i % 2) * 0.1
            if y > 0.33:
                continue
            log_x(k, -0.84, 0.84, y, 0.13 + i * 0.235, 0.13, 'log' if (i + j) % 3 else 'log2', seg=5, ink=False)
    shed_roof(k, -1.05, 1.05, -0.45, 0.4, 1.48, 1.62, 0.06, 'plankG', 'plank2')
    k.col(-1.0, 1.0, -0.4, 0.4, 0.0, 1.45)
    k.finish('Firewood', ao=ao)
    # chopping block with an axe and split wood
    k.begin()
    k.cyl(0, 0, 0, 0.3, 0.28, 0.55, 'log', seg=8)
    k.beam((0.0, 0.05, 0.5), (0.25, 0.3, 1.0), 0.045, 'plank2')
    k.bx(-0.1, 0.06, -0.02, 0.1, 0.5, 0.64, 'steel')
    for i in range(4):
        a = i * 1.4
        k.bxr(math.cos(a) * 0.45, math.sin(a) * 0.45, 0.06, 0.35, 0.1, 0.1, 'log' if i % 2 else 'logEnd', rot=(0, 0, math.degrees(a) + 30))
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 0.6)
    k.finish('ChopBlock', ao=ao)
    # lantern post (the glow companion lights the lantern)
    k.begin()
    k.bx(-0.12, 0.12, -0.12, 0.12, 0.0, 2.7, 'log2')
    k.bx(-0.04, 0.04, -0.65, -0.12, 2.55, 2.62, 'iron2')
    lantern(k, 0.0, -0.58, 2.55)
    k.col(-0.13, 0.13, -0.13, 0.13, 0.0, 2.7)
    k.finish('LampPost', ao=ao)
    k.begin()
    k.cyl(0.0, -0.58, 2.24, 0.065, 0.065, 0.2, 'fire2', seg=6, ink=False)
    k.finish('LampPost_Glow', ao=False)
    # signpost with three boards (made-up places)
    k.begin()
    k.bx(-0.07, 0.07, -0.07, 0.07, 0.0, 2.5, 'log2')
    for (z, yaw, word) in ((2.15, 20, 'SAWMILL'), (1.8, -35, 'CAMP 9'), (1.45, 160, 'GATE')):
        k.push(0, 0, yaw, z)
        k.hullp([(0.08, -0.03, 0.0), (0.95, -0.03, 0.0), (1.1, -0.03, 0.12), (0.95, -0.03, 0.24), (0.08, -0.03, 0.24),
                 (0.08, 0.03, 0.0), (0.95, 0.03, 0.0), (1.1, 0.03, 0.12), (0.95, 0.03, 0.24), (0.08, 0.03, 0.24)], 'plank')
        k.text(word, 0.52, -0.034, 0.05, 0.14, 'ink', maxw=0.75, font='display')
        k.pop()
    k.col(-0.08, 0.08, -0.08, 0.08, 0.0, 2.5)
    k.finish('Signpost', ao=ao)


def build_spool(k, ao):
    k.begin()
    for y in (-0.36, 0.28):
        k.cyl(0, y, 0.55, 0.55, 0.55, 0.08, 'plank', seg=10, rot=(-90, 0, 0))
    k.cyl(0, -0.28, 0.55, 0.38, 0.38, 0.56, 'iron2', seg=10, rot=(-90, 0, 0))
    k.col(-0.55, 0.55, -0.37, 0.37, 0.0, 1.1)
    k.finish('Spool', ao=ao)


# ================================================================ the supply depot's modern gear
def build_depot(k, ao):
    rnd = random.Random(81)
    # FERRO-LINE fuel tank [3, 6]: horizontal tank on steel saddles, ladder, filler, hose reel
    k.begin()
    k.cyl(0, -2.4, 1.45, 1.1, 1.1, 4.8, 'fuel', seg=12, rot=(-90, 0, 0))
    for y in (-1.6, 1.6):
        k.bx(-0.95, 0.95, y - 0.15, y + 0.15, 0.0, 0.55, 'iron')
        k.hullp([(-0.9, y - 0.12, 0.55), (0.9, y - 0.12, 0.55), (-0.9, y + 0.12, 0.55), (0.9, y + 0.12, 0.55), (0, y - 0.12, 0.9), (0, y + 0.12, 0.9)], 'iron')
    for y in (-1.0, 1.0):
        k.cyl(0, y, 1.45, 1.12, 1.12, 0.1, 'iron2', seg=12, rot=(-90, 0, 0), caps=False, ink=False)
    k.qx(-0.9, 0.9, 1.08, 1.82, -1.11, -1, 'ink')
    k.qx(-0.85, 0.85, 1.12, 1.78, -1.114, -1, 'fuel')
    k.text('FERRO-LINE', -1.12, 0.0, 1.32, 0.28, 'ink', face='x-', maxw=1.6, font='display')
    k.qx(-0.9, 0.9, 1.08, 1.82, 1.11, 1, 'ink')
    k.qx(-0.85, 0.85, 1.12, 1.78, 1.114, 1, 'fuel')
    k.text('FERRO-LINE', 1.12, 0.0, 1.32, 0.28, 'ink', face='x+', maxw=1.6, font='display')
    k.cyl(0.3, 0.6, 2.5, 0.12, 0.12, 0.25, 'iron2', seg=6)
    k.cyl(-0.3, -0.8, 2.5, 0.2, 0.2, 0.12, 'iron', seg=8)
    for x in (-0.25, 0.25):
        k.beam((x, -2.55, 0.0), (x, -2.55, 2.55), 0.05, 'steel')
    for i in range(1, 8):
        k.bx(-0.25, 0.25, -2.57, -2.53, i * 0.32, i * 0.32 + 0.04, 'steel', ink=False)
    k.cyl(0.9, 2.55, 0.0, 0.05, 0.05, 1.0, 'iron2', seg=5)
    k.cyl(0.9, 2.62, 0.75, 0.25, 0.25, 0.14, 'iron', seg=8, rot=(-90, 0, 0))
    k.col(-1.1, 1.1, -2.4, 2.4, 0.0, 2.55)
    k.col(-0.3, 0.3, -2.62, -2.4, 0.0, 2.55)
    k.finish('FuelTank', ao=ao)
    # diesel generator [2, 3]: an olive canopy on a skid, louvres, control panel, exhaust stack, cables
    k.begin()
    k.bx(-0.85, 0.85, -1.35, 1.35, 0.0, 0.15, 'iron')
    k.bx(-0.75, 0.75, -1.25, 1.25, 0.15, 1.45, 'olive')
    k.bx(-0.78, 0.78, -1.28, 1.28, 1.45, 1.52, 'olive2')
    for s in (-1, 1):
        for i in range(5):
            z = 0.45 + i * 0.16
            k.qx(-0.9, 0.2, z, z + 0.06, s * 0.754, s, 'olive2')
    k.qy(-0.5, 0.5, 0.8, 1.25, -1.254, -1, 'iron2')
    for i, c in enumerate(('fire2', 'red', 'teal')):
        k.cyl(-0.3 + i * 0.3, -1.26, 1.1, 0.04, 0.04, 0.02, c, seg=6, rot=(90, 0, 0), ink=False)
    k.text('KODA 40kVA', 0.0, -1.257, 0.55, 0.14, 'canvas', maxw=1.2, font='sans')
    k.cyl(0.4, 0.8, 1.52, 0.08, 0.08, 0.7, 'iron2', seg=6)
    k.cyl(0.4, 0.8, 2.2, 0.1, 0.08, 0.06, 'iron', seg=6, caps=False)
    k.beam((-0.6, 1.3, 0.3), (-0.6, 1.9, 0.02), 0.06, 'iron2', ink=False)
    k.col(-0.85, 0.85, -1.35, 1.35, 0.0, 1.52)
    k.finish('Generator', ao=ao)
    # solar array [4, 2]: three panels tilted to the south (-Y) on a timber-and-steel rack, a combiner box
    k.begin()
    for i in range(3):
        x = -1.33 + i * 1.33
        k.push(x, 0.0, 0, 0.0)
        for (px, py, h) in ((-0.55, -0.55, 0.45), (0.55, -0.55, 0.45), (-0.55, 0.45, 1.3), (0.55, 0.45, 1.3)):
            k.bx(px - 0.04, px + 0.04, py - 0.04, py + 0.04, 0.0, h, 'steel')
        k.bxr(0.0, -0.05, 0.9, 1.25, 1.25, 0.05, 'solar', rot=(-34, 0, 0))
        for u in (-0.3, 0.0, 0.3):
            k.bxr(u, -0.05 - 0.03 * math.sin(math.radians(34)), 0.9 + 0.03 * math.cos(math.radians(34)), 0.02, 1.2, 0.004, 'solar2', rot=(-34, 0, 0), ink=False)
        k.pop()
    k.bx(1.75, 1.95, 0.55, 0.75, 0.3, 0.75, 'steel')
    k.bx(1.81, 1.89, 0.55, 0.75, 0.0, 0.3, 'steel', ink=False)
    for i in range(3):
        k.col(-1.33 + i * 1.33 - 0.62, -1.33 + i * 1.33 + 0.62, -0.6, 0.5, 0.0, 1.32)
    k.finish('Solar', ao=ao)
    # radio mast [2, 2]: a triangular lattice mast 14 m, dish and whips, the beacon, an equipment cabinet
    k.begin()
    H = 14.0
    R = 0.32
    tri = [(math.cos(a) * R, math.sin(a) * R) for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)]
    for (x, y) in tri:
        k.cyl(x, y, 0.0, 0.035, 0.03, H, 'steel', seg=4)
    n = 10
    for i in range(n):
        z0, z1 = H * i / n, H * (i + 1) / n
        for j in range(3):
            a, b = tri[j], tri[(j + 1) % 3]
            k.beam((a[0], a[1], z0), (b[0], b[1], z1), 0.022, 'red' if (i // 2) % 2 else 'white', ink=False)
    k.bx(-0.55, 0.55, -0.55, 0.55, 0.0, 0.2, 'stone2')
    k.push(0.0, -0.35, 0, 9.5)
    k.cyl(0, 0, 0, 0.5, 0.15, 0.25, 'white', seg=10, rot=(-80, 0, 0))
    k.pop()
    for (x, y, h) in ((0.25, 0.2, 2.0), (-0.3, 0.1, 1.6)):
        k.cyl(x, y, H, 0.015, 0.01, h, 'iron2', seg=4, ink=False)
    k.cyl(0.0, 0.0, H, 0.09, 0.09, 0.16, 'red', seg=6)
    k.bx(0.55, 1.0, -0.6, 0.2, 0.0, 1.1, 'steel')
    k.qy(0.6, 0.95, 0.5, 1.0, -0.604, -1, 'iron2')
    k.col(-0.55, 0.55, -0.55, 0.55, 0.0, 2.2)
    k.col(0.55, 1.0, -0.6, 0.2, 0.0, 1.1)
    k.finish('RadioMast', ao=ao)
    k.begin()
    k.cyl(0.0, 0.0, 14.02, 0.1, 0.1, 0.12, 'red', seg=6, ink=False)
    k.finish('RadioMast_Glow', ao=False)
    # supply tent [4, 5]: an olive frame tent, front open (-Y), crates and a cot inside
    k.begin()
    hx, hy, zs, zr = 1.85, 2.3, 1.6, 2.7
    for sx in (-1, 1):
        k.hullp([(sx * hx, y, z) for y in (-hy, hy) for z in (0.0, zs)] + [(sx * (hx - 0.04), y, z) for y in (-hy, hy) for z in (0.0, zs)], 'olive')
        k.hullp([(sx * (hx + 0.06), y, zs - 0.04) for y in (-hy - 0.06, hy + 0.06)] + [(0.0, y, zr) for y in (-hy - 0.06, hy + 0.06)] + [(sx * (hx + 0.02), y, zs - 0.07) for y in (-hy - 0.06, hy + 0.06)] + [(0.0, y, zr - 0.04) for y in (-hy - 0.06, hy + 0.06)],
                by_normal(top='olive', bot='olive2', other='olive2'))
    k.hullp([(x, hy - 0.004, z) for x in (-hx + 0.045, hx - 0.045) for z in (0.0, zs)] + [(0.0, hy - 0.004, zr - 0.05)] + [(x, hy - 0.044, z) for x in (-hx + 0.045, hx - 0.045) for z in (0.0, zs)] + [(0.0, hy - 0.044, zr - 0.05)], 'olive2')
    # the front: the flaps rolled up at the sides, the gable triangle closed
    k.hullp([(-hx + 0.045, -hy + 0.004, zs), (hx - 0.045, -hy + 0.004, zs), (0.0, -hy + 0.004, zr - 0.05), (-hx + 0.045, -hy + 0.044, zs), (hx - 0.045, -hy + 0.044, zs), (0.0, -hy + 0.044, zr - 0.05)], 'olive2')
    for sx in (-1, 1):
        k.cyl(sx * (hx - 0.3), -hy - 0.05, 0.0, 0.1, 0.1, zs, 'olive2', seg=6)
        k.beam((sx * hx, -hy, zs), (sx * (hx + 0.7), -hy - 0.8, 0.0), 0.02, 'rope', ink=False)
    for y in (-hy + 0.06, 0.0, hy - 0.06):
        k.cyl(0.0, y, 0.0, 0.04, 0.04, zr - 0.04, 'iron2', seg=4, ink=False)
    k.bx(-hx + 0.1, -hx + 0.85, -0.6, 1.5, 0.35, 0.45, 'olive2')
    for y in (-0.5, 1.4):
        k.bx(-hx + 0.12, -hx + 0.83, y - 0.03, y + 0.03, 0.0, 0.35, 'iron2', ink=False)
    for (x, y, z, s) in ((1.2, 1.5, 0.0, 0.8), (1.25, 1.45, 0.55, 0.6), (1.2, 0.6, 0.0, 0.7)):
        crate(k, x, y, z, s, s * 0.8, s * 0.7, 'olive', 'olive2')
    k.col(-hx, hx, hy - 0.05, hy, 0.0, zs)
    k.col(-hx, -hx + 0.05, -hy, hy, 0.0, zs)
    k.col(hx - 0.05, hx, -hy, hy, 0.0, zs)
    k.col(0.75, 1.65, 0.2, 1.9, 0.0, 0.95)
    k.col(-hx + 0.1, -hx + 0.85, -0.6, 1.5, 0.0, 0.45)
    k.finish('SupplyTent', ao=ao)


def build_town(k, ao):
    build_palisade(k, ao)
    build_gate(k, ao)
    build_trail(k, ao)
    build_tower(k, ao)
    build_watertower(k, ao)
    build_well(k, ao)
    build_arch(k, ao)
    build_corral(k, ao)
    build_wagons(k, ao)
    build_small(k, ao)
    build_spool(k, ao)
    build_depot(k, ao)
