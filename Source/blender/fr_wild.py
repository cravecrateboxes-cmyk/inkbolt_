"""INKBOLT kit-frontier, zone 2 (the edge of the wild) and the trees of both zones: forest-edge wall modules, the
cliff lip and the rim behind it, the ravine banks, the rope bridge, the lookout platform (landmark), the sawmill,
the water wheel (static frame + the turning rotor the theme spins), the flume, the creek (water tiles, the spring
falls), log piles and log decks, lumber stacks, fallen logs and trees, stumps, boulders, conifers and groves, the
logging camp (wall tents, the cook shack, the fire pit, sawhorse, the log arch, tool rack, camp sign), the old mine
entrance, the radio relay, the lean-to, and the instanced backdrop conifers. See fr_base.py for the conventions."""
import math
import random

from fr_base import (polyline, FLOOR, RISE, TREAD, PLAT, WALL_H, by_normal, leafcol, rockcol, barkcol, rock, conifer, log_x,
                     log_y, post, rail_run, lantern, crate, barrel, sack, shed_roof, gable, stairs, wall)
from fr_town import wheel


# ================================================================ trees
def build_trees(k, ao):
    for name, seed, h, r, tiers in (('Pine_A', 101, 7.0, 1.9, 3), ('Pine_B', 102, 9.5, 2.3, 3), ('Pine_C', 103, 12.0, 2.7, 4)):
        rnd = random.Random(seed)
        k.begin()
        conifer(k, rnd, 0.0, 0.0, h, r, tiers=tiers, seg=6)
        q = r * 0.62
        k.col(-q, q, -q, q, 0.0, 2.6)
        k.finish(name, ao=ao)
    # a grove [3, 3]: three conifers of different heights, a rock and a stump between them
    for name, seed in (('Grove_A', 111), ('Grove_B', 112)):
        rnd = random.Random(seed)
        k.begin()
        spots = [(-0.75, -0.6, 8.5, 1.5), (0.8, -0.35, 6.2, 1.25), (-0.1, 0.85, 10.5, 1.55)] if seed == 111 else \
                [(0.7, 0.7, 9.0, 1.5), (-0.8, 0.5, 7.0, 1.3), (0.1, -0.8, 5.5, 1.15)]
        for (x, y, h, r) in spots:
            conifer(k, rnd, x, y, h, r, tiers=3, seg=6)
        rock(k, rnd, 0.95 if seed == 111 else -0.9, 0.9 if seed == 111 else -0.85, 0.42, 0.36, 0.5)
        k.col(-1.2, 1.2, -1.2, 1.2, 0.0, 2.4)
        k.finish(name, ao=ao)
    # stumps, a fern clump (no collision)
    rnd = random.Random(121)
    k.begin()
    k.cyl(0, 0, 0, 0.42, 0.36, 0.55, 'log2', seg=8)
    k.cyl(0, 0, 0.55, 0.36, 0.36, 0.004, 'logEnd', seg=8, ink=False)
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.4
        k.beam((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.2), (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.0), 0.12, 'log2')
    k.col(-0.42, 0.42, -0.42, 0.42, 0.0, 0.56)
    k.finish('Stump', ao=ao)
    k.begin()
    for i in range(7):
        a = i / 7 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        L = rnd.uniform(0.5, 0.75)
        p0 = (0.0, 0.0, 0.02)
        p1 = (math.cos(a) * L * 0.5, math.sin(a) * L * 0.5, 0.45)
        p2 = (math.cos(a) * L, math.sin(a) * L, 0.12)
        sx, sy = -math.sin(a) * 0.09, math.cos(a) * 0.09
        k.hullp([p0, (p1[0] + sx, p1[1] + sy, p1[2]), (p1[0] - sx, p1[1] - sy, p1[2]), p2, (p1[0], p1[1], p1[2] + 0.03)],
                leafcol('grass', 'pine3', 'pine'), ink=False)
    k.finish('Fern', ao=False)


def build_backdrop_trees(k):
    """instanced backdrop conifers: an outlined one for the near rows, an outline-free low one for the far forest"""
    rnd = random.Random(131)
    k.begin()
    conifer(k, rnd, 0.0, 0.0, 9.0, 2.2, tiers=2, seg=5, trunk=False)
    k.finish('Backdrop_Pine')
    k.begin()
    conifer(k, rnd, 0.0, 0.0, 12.0, 2.0, tiers=3, seg=5, trunk=False, cols=('pine2', 'pine', 'pine2'))
    k.finish('Backdrop_Fir')
    k.begin()
    for t, (zb, rr, hh, c) in enumerate(((0.0, 2.6, 6.5, 'pine2'), (4.2, 1.8, 6.0, 'pine'))):
        k.cyl(0, 0, zb, rr, 0.0, hh, c, seg=4, caps=False, ink=False, rot=(0, 0, 45 * t))
    k.finish('Backdrop_PineLow')


# ================================================================ rock: forest-edge walls, cliff lip and rim, ravine banks, boulders
def build_rocks(k, ao):
    # 1 m forest-edge wall modules (face -Y): a jagged rock lump of mixed height, some with a conifer behind
    for name, seed, h, tree in (('Edge_A', 141, 3.4, None), ('Edge_B', 142, 4.4, None), ('Edge_C', 143, 2.6, (7.5, 1.5)),
                                ('Edge_D', 144, 3.0, (10.0, 1.8))):
        rnd = random.Random(seed)
        k.begin()
        rock(k, rnd, 0.0, 0.05, 0.72, 0.6, h, n=6, top=3)
        if tree:
            conifer(k, rnd, 0.1, 0.35, tree[0], tree[1], z0=h * 0.55, tiers=3, seg=6, caps=False)
        k.finish(name, ao=ao)
    rnd = random.Random(145)
    k.begin()
    rock(k, rnd, 0.0, 0.0, 0.8, 0.8, 4.6, n=7, top=3)
    k.finish('Edge_Corner', ao=ao)
    # cliff lip ('{' / '}' cells: the plateau runs up to it): rock to 0.55 m above the plateau on its inner (-Y) side,
    # 0.95 m on its outer side, a log rail along it; the low lip where a plateau falls away (its top 2.6 m); the
    # ravine banks ('R' / 'Q', face -Y toward the ravine: from the ravine floor to 0.45 / 0.6 m above the plateau),
    # the low bank. Every module meets its neighbours at the same edge profile and varies in between (two convex
    # halves per module: peaks, dips, a bulging or a sunken face), so a row reads as one ragged ridge.
    def ridge(mid, f_edge, b_edge, f_mid, b_mid, d_edge, d_mid, y_back=0.5, waist=None, z0=0.0):
        for (xa, xb, ta, tb, fa, fb, da, db) in ((-0.497, mid, f_edge, f_mid, b_edge, b_mid, d_edge, d_mid),
                                                 (mid, 0.497, f_mid, f_edge, b_mid, b_edge, d_mid, d_edge)):
            pts = []
            for (x, ft, bt, d) in ((xa, ta, fa, da), (xb, tb, fb, db)):
                pts += [(x, d - 0.04, z0), (x, y_back, z0), (x, d, ft), (x, y_back, bt)]
                if waist:
                    pts.append((x, d - waist, ft * 0.55))
            k.hullp(pts, rockcol)
    LIPS = (('Lip_A', 0.1, 0.3, 0.25, -0.38, -0.46), ('Lip_B', -0.2, -0.25, -0.15, -0.38, -0.32),
            ('Lip_C', 0.3, 0.15, 0.4, -0.38, -0.42), ('Lip_D', -0.05, -0.35, 0.1, -0.38, -0.36))
    for (name, mid, df, db, d_edge, d_mid) in LIPS:
        k.begin()
        ridge(mid, PLAT + 0.55, PLAT + 0.95, PLAT + 0.55 + df, PLAT + 0.95 + db, d_edge, d_mid, y_back=0.4 + 0.05 * 'ABCD'.index(name[-1]), z0=-0.006 * 'ABCD'.index(name[-1]))
        if name in ('Lip_A', 'Lip_C'):
            k.bx(-0.06, 0.06, -0.06, 0.06, PLAT + 0.6, PLAT + 1.75, 'log2')
        log_x(k, -0.495, 0.495, -0.05, PLAT + 1.6, 0.06, 'log', seg=5, ends=False)
        k.col(-0.5, 0.5, -0.5, 0.5, 0.0, PLAT + 0.9)
        k.finish(name, ao=ao)
    k.begin()
    ridge(0.15, 2.4, 2.6, 2.25, 2.75, -0.36, -0.44, y_back=0.55)
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, 2.6)
    k.finish('Lip_Low', ao=ao)
    for name, seed in (('Rim_A', 153), ('Rim_B', 154)):
        rnd = random.Random(seed)
        k.begin()
        rock(k, rnd, 0.0, 0.1, 0.75, 0.62, PLAT + 1.2 + rnd.uniform(-0.2, 0.3), n=6, top=3)
        k.finish(name, ao=ao)
    BANKS = (('Bank_A', 161, 0.15, 0.3, 0.2, -0.36, -0.5, 0.06), ('Bank_B', 162, -0.25, -0.3, -0.15, -0.36, -0.24, 0.1),
             ('Bank_C', 164, -0.05, 0.15, 0.3, -0.36, -0.44, 0.14))
    for (name, seed, mid, df, db, d_edge, d_mid, waist) in BANKS:
        k.begin()
        ridge(mid, PLAT + 0.45, PLAT + 0.6, PLAT + 0.45 + df, PLAT + 0.6 + db, d_edge, d_mid, waist=waist)
        rr = random.Random(seed + 7)
        rock(k, rr, rr.uniform(-0.25, 0.25), -0.55, 0.22, 0.14, 0.28, n=5, top=2)
        k.col(-0.5, 0.5, -0.5, 0.5, 0.0, PLAT + 0.6)
        k.finish(name, ao=ao)
    k.begin()
    ridge(-0.1, 2.4, 2.6, 2.6, 2.7, -0.36, -0.44, waist=0.08)
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, 2.6)
    k.finish('Bank_Low', ao=ao)
    # boulders [2, 2], a rock (1 cell), a scree cluster for the ravine floor
    for name, seed, rx, ry, h in (('Boulder_A', 171, 0.95, 0.85, 1.5), ('Boulder_B', 172, 0.9, 0.95, 1.9)):
        rnd = random.Random(seed)
        k.begin()
        rock(k, rnd, 0.0, 0.0, rx, ry, h, n=8, top=4)
        rock(k, rnd, rx * 0.75, -ry * 0.55, 0.32, 0.28, 0.45)
        q = 0.7
        k.col(-rx * q, rx * q, -ry * q, ry * q, 0.0, h * 0.85)
        k.finish(name, ao=ao)
    rnd = random.Random(173)
    k.begin()
    rock(k, rnd, 0.0, 0.0, 0.45, 0.4, 0.7, n=7)
    k.col(-0.32, 0.32, -0.28, 0.28, 0.0, 0.6)
    k.finish('Rock', ao=ao)


# ================================================================ timber: logs, piles, lumber, fallen trees
def build_logs(k, ao):
    rnd = random.Random(181)
    # LogPile [4, 2]: 3-2-1 logs along X, chocked by stakes
    k.begin()
    r = 0.27
    rows = [(-0.56, 0.0), (0.0, 0.0), (0.56, 0.0)]
    for lvl, n in enumerate((3, 2, 1)):
        for i in range(n):
            y = (i - (n - 1) / 2) * 0.56
            z = r + lvl * r * 1.72
            x0 = -1.9 + rnd.uniform(-0.1, 0.1)
            log_x(k, x0, x0 + 3.8 + rnd.uniform(-0.1, 0.1), y, z, r * rnd.uniform(0.92, 1.05), 'log' if (i + lvl) % 2 else 'log2', seg=6)
    for sy in (-1, 1):
        for x in (-1.2, 1.2):
            k.bx(x - 0.05, x + 0.05, sy * 0.86 - 0.05, sy * 0.86 + 0.05, 0.0, 0.8, 'log2')
    k.col(-1.95, 1.95, -0.88, 0.88, 0.0, 1.5)
    k.finish('LogPile', ao=ao)
    # LogDeck [6, 3]: a big deck of nine logs 4-3-2, skids under it
    k.begin()
    r = 0.33
    for lvl, n in enumerate((4, 3, 2)):
        for i in range(n):
            y = (i - (n - 1) / 2) * 0.68
            z = 0.12 + r + lvl * r * 1.72
            x0 = -2.85 + rnd.uniform(-0.15, 0.1)
            log_x(k, x0, x0 + 5.6 + rnd.uniform(-0.1, 0.15), y, z, r * rnd.uniform(0.9, 1.06), 'log' if (i + lvl) % 2 else 'log2', seg=6)
    for x in (-2.0, 0.0, 2.0):
        log_y(k, -1.45, 1.45, x, 0.08, 0.1, 'log2', seg=5)
    k.col(-2.9, 2.9, -1.4, 1.4, 0.0, 2.1)
    k.finish('LogDeck', ao=ao)
    # Lumber [3, 2]: sawn boards in two stacks on stickers
    k.begin()
    for (cx, hh) in ((-0.72, 1.25), (0.72, 0.95)):
        k.bx(cx - 0.62, cx + 0.62, -0.85, 0.85, 0.0, 0.12, 'log2')
        n = int(hh / 0.18)
        for i in range(n):
            z = 0.12 + i * 0.18
            k.bx(cx - 0.6, cx + 0.6, -0.85, 0.85, z, z + 0.15, 'plank' if i % 2 else 'plank2', ink=(i == n - 1))
            if i < n - 1:
                k.bx(cx - 0.6, cx + 0.6, -0.04, 0.04, z + 0.15, z + 0.18, 'plank2', ink=False)
            for yy in (-0.85, 0.85):
                k.qy(cx - 0.58, cx + 0.58, z + 0.072, z + 0.078, yy + (0.004 if yy > 0 else -0.004), 1 if yy > 0 else -1, 'plank2')
    k.col(-1.34, 1.34, -0.86, 0.86, 0.0, 1.25)
    k.finish('Lumber', ao=ao)
    # Log [5, 1]: a felled, limbed log on the ground (axe-cut end), branch stubs
    k.begin()
    log_x(k, -2.4, 2.3, 0.0, 0.36, 0.36, 'log', seg=7)
    for (x, a) in ((-1.2, 40), (0.3, -60), (1.4, 120)):
        k.beam((x, 0.0, 0.5), (x + 0.15, math.cos(math.radians(a)) * 0.6, 0.5 + math.sin(math.radians(a)) * 0.4), 0.07, 'log2')
    k.col(-2.4, 2.3, -0.33, 0.33, 0.0, 0.72)
    k.finish('Log', ao=ao)
    # FallenTree [8, 2]: a windthrown conifer -- root plate with earth, trunk, dead branches at the crown end
    k.begin()
    k.tube((-3.0, 0.0, 0.55), (3.6, 0.1, 0.32), 0.42, 0.22, 'log2', seg=7)
    plate = []
    for i in range(9):
        a = i / 9 * 2 * math.pi
        plate += [(-3.4 + rnd.uniform(-0.05, 0.05), math.cos(a) * 1.0, 0.75 + math.sin(a) * 0.95), (-3.15, math.cos(a) * 0.9, 0.75 + math.sin(a) * 0.85)]
    k.hullp([(x, y, max(0.0, z)) for (x, y, z) in plate], by_normal(nx='dirt2', px='dirt', other='dirt2', top='grass2'))
    for (x, y) in ((-3.5, 0.5), (-3.5, -0.4), (-3.45, 0.0)):
        k.beam((-3.3, y * 0.6, 0.9), (x - 0.3, y, 0.3 + rnd.uniform(0, 1.0)), 0.06, 'log2', ink=False)
    for i in range(6):
        x = 0.8 + i * 0.5
        a = rnd.uniform(-1.2, 1.2) + (math.pi if i % 2 else 0)
        k.beam((x, 0.05, 0.42), (x + 0.3, math.cos(a) * 0.75, 0.42 + math.sin(a) * 0.5 + 0.1), 0.05, 'log2', ink=False)
    k.col(-3.0, 3.6, -0.4, 0.4, 0.0, 0.85)
    k.col(-3.45, -3.0, -0.95, 0.95, 0.0, 1.6)
    k.finish('FallenTree', ao=ao)


# ================================================================ the ravine's rope bridge [7, 2] (along X)
def build_bridge(k, ao):
    rnd = random.Random(191)
    k.begin()
    Z = PLAT
    # plank deck on two stringers, 1.4 m wide, from bank to bank (x -3.5 .. 3.5)
    for i in range(14):
        x0 = -3.5 + i * 0.5 + 0.02
        k.bx(x0, x0 + 0.46, -0.68 + rnd.uniform(0, 0.03), 0.68 - rnd.uniform(0, 0.03), Z - 0.08, Z, 'plank' if i % 3 else 'plank2', ink=False)
    for y in (-0.62, 0.62):
        k.bx(-3.5, 3.5, y - 0.07, y + 0.07, Z - 0.3, Z - 0.08, 'log2')
    k.wcol(-3.5, 3.5, -0.7, 0.7, Z - 0.3, Z)
    # log cribs under the deck in the two bank cells (they close the bank where the bridge crosses it)
    for sx in (-1, 1):
        xa, xb = sorted((sx * 1.5, sx * 2.5))
        for lvl in range(3):
            z = 0.45 + lvl * 0.95
            if lvl % 2 == 0:
                for y in (-0.85, 0.85):
                    log_x(k, xa - 0.08, xb + 0.08, y, z, 0.17, 'log2', seg=5, ends=False)
            else:
                for x in (xa + 0.2, xb - 0.2):
                    log_y(k, -1.0, 1.0, x, z, 0.17, 'log', seg=5, ends=False)
        k.bx(xa, xb, -0.95, 0.95, 0.0, Z - 0.32, 'rock2')
        k.col(xa, xb, -1.0, 1.0, 0.0, Z - 0.3)
        k.col(xa, xb, -1.0, -0.7, Z - 0.3, Z + 0.6)
        k.col(xa, xb, 0.7, 1.0, Z - 0.3, Z + 0.6)
        # rope posts at the bank edges and anchors on the landings
        for y in (-0.76, 0.76):
            k.cyl(sx * 2.4, y, Z - 0.36, 0.09, 0.08, 1.6, 'log', seg=6)
            k.cyl(sx * 3.35, y, Z - 0.36, 0.07, 0.06, 0.95, 'log2', seg=5)
    for y in (-0.76, 0.76):
        for (z, sag) in ((Z + 1.12, 0.32), (Z + 0.55, 0.22)):
            pts = []
            for i in range(7):
                u = i / 6
                pts.append((-2.4 + 4.8 * u, y, z - sag * 4 * u * (1 - u)))
            polyline(k, pts, 0.035, 'rope', (0, 1, 0), ink=False)
            e = 0.012 if sag > 0.3 else -0.012
            for sx in (-1, 1):
                k.beam((sx * 2.4, y + e, z), (sx * 3.35, y + e, Z + 0.45 + (0.06 if e > 0 else 0.0)), 0.03, 'rope', ink=False)
        for i in range(1, 6):
            u = i / 6
            x = -2.4 + 4.8 * u
            k.beam((x, y * 0.97, Z), (x, y * 0.97, Z + 1.12 - 0.32 * 4 * u * (1 - u)), 0.02, 'rope', ink=False)
    k.col(-3.5, 3.5, -0.84, -0.7, Z, Z + 1.1)
    k.col(-3.5, 3.5, 0.7, 0.84, Z, Z + 1.1)
    k.finish('Bridge', ao=ao)


# ================================================================ lookout platform (landmark) [8, 8]: deck to the west (-X)
LOOK = 13 * RISE      # deck top 2.34 m above the plateau


def build_lookout(k, ao):
    rnd = random.Random(201)
    k.begin()
    Z = LOOK
    dx0, dx1, dy0, dy1 = -4.0, 0.75, -2.5, 2.5
    posts = [(-3.75, -2.25), (-3.75, 2.25), (-1.5, -2.25), (-1.5, 2.25), (0.75, -2.25), (0.75, 2.25)]
    for (x, y) in posts:
        k.bx(x - 0.25, x + 0.25, y - 0.25, y + 0.25, -0.4, 0.2, 'stone')
        k.cyl(x, y, 0.2, 0.17, 0.15, Z + 2.5 - 0.2, 'log', seg=6)
        k.col(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.0, Z + 1.0)
    for (a, b) in ((posts[0], posts[2]), (posts[2], posts[4]), (posts[1], posts[3]), (posts[3], posts[5]), (posts[0], posts[1])):
        k.beam((a[0], a[1], 0.5 if a[0] == b[0] else 0.4), (b[0], b[1], Z - 0.4), 0.1, 'log2')
    k.bx(dx0, dx1, dy0, dy1, Z - 0.12, Z, 'plank')
    for i in range(1, 17):
        y = dy0 + i * 0.3125
        k.qz(dx0 + 0.01, dx1 - 0.01, y - 0.012, y + 0.012, Z + 0.004, 1, 'plank2')
    for x in (-3.75, -1.5, 0.75):
        k.bx(x - 0.1, x + 0.1, dy0, dy1, Z - 0.36, Z - 0.12, 'log2')
    k.wcol(dx0, dx1, dy0, dy1, Z - 0.2, Z)
    # railing on three sides and the stair side (gap at the stair), the deck faces the wilderness (-X)
    rail_run(k, 'y', dy0 + 0.06, dy1 - 0.06, dx0 + 0.06, Z, 1.05, 'log2', posts=1.25)
    rail_run(k, 'x', dx0 + 0.06, dx1 - 0.06, dy0 + 0.06, Z, 1.05, 'log2', posts=1.25)
    rail_run(k, 'x', dx0 + 0.06, dx1 - 0.06, dy1 - 0.06, Z, 1.05, 'log2', posts=1.25)
    rail_run(k, 'y', dy0 + 0.06, -0.72, dx1 - 0.06, Z, 1.05, 'log2', posts=0.9)
    rail_run(k, 'y', 0.72, dy1 - 0.06, dx1 - 0.06, Z, 1.05, 'log2', posts=0.9)
    for (x0, x1, y0, y1) in ((dx0, dx0 + 0.12, dy0, dy1), (dx0, dx1, dy0, dy0 + 0.12), (dx0, dx1, dy1 - 0.12, dy1),
                             (dx1 - 0.12, dx1, dy0, -0.7), (dx1 - 0.12, dx1, 0.7, dy1)):
        k.col(x0, x1, y0, y1, Z, Z + 1.08)
    # the roof over the back half (a shelter for the watch), the map table, the spotting scope, the bell, the flag
    gable(k, -2.1, 0.75, dy0 + 0.2, dy1 - 0.2, Z + 2.5, Z + 3.5, 0.12, 'shingle', 'shingle2', over=0.3, ridge_along='y')
    k.bx(-0.3, 0.6, -1.9, -1.1, Z, Z + 0.95, 'plank2')
    k.bx(-0.35, 0.65, -1.95, -1.05, Z + 0.95, Z + 1.0, 'plank')
    k.bxr(0.15, -1.5, Z + 1.004, 0.7, 0.55, 0.004, 'canvas', rot=(0, 0, 8), ink=False)
    k.col(-0.35, 0.65, -1.95, -1.05, Z, Z + 1.0)
    k.cyl(-3.6, 0.0, Z, 0.06, 0.06, 1.25, 'iron2', seg=5)
    k.push(-3.6, 0.0, 0, Z + 1.32)
    k.cyl(-0.05, 0, 0, 0.07, 0.09, 0.6, 'fuel', seg=8, rot=(0, -80, 0))
    k.cyl(-0.05 - 0.985 * 0.3, 0, 0.17 * 0.3, 0.1, 0.1, 0.06, 'iron2', seg=8, rot=(0, -80, 0))
    k.pop()
    k.col(-3.7, -3.5, -0.1, 0.1, Z, Z + 1.3)
    k.cyl(0.5, 1.8, Z + 1.9, 0.14, 0.2, 0.3, 'fuel', seg=8)
    k.beam((0.5, 1.8, Z + 2.2), (0.5, 1.8, Z + 2.5), 0.03, 'iron2', ink=False)
    k.cyl(-3.75, 2.25, Z + 2.5, 0.05, 0.04, 2.6, 'log2', seg=5)
    k.hullp([(-3.75, 2.25, Z + 4.5), (-3.75, 2.25, Z + 5.0), (-3.75 - 0.9, 2.3, Z + 4.75), (-3.75, 2.29, Z + 4.5), (-3.75, 2.29, Z + 5.0)], 'cloth')
    lantern(k, -0.6, 0.0, Z + 2.35)
    # sign on the stair side
    k.bx(dx1 + 0.06, dx1 + 0.1, -1.8, -0.9, Z + 0.15, Z + 0.75, 'plank2')
    k.text('LOOKOUT', dx1 + 0.104, -1.35, Z + 0.3, 0.26, 'plankW', face='x+', maxw=0.8, font='display')
    # the stair: 13 treads rising toward -X from x 4.0 to the deck edge at 0.75
    for i in range(13):
        xa = 4.0 - i * TREAD
        xb = xa - TREAD
        za = (i + 1) * RISE
        k.bx(xb, xa, -0.62, 0.62, za - 0.06, za, 'plank' if i % 2 else 'plank2', ink=False)
        k.wcol(xb, xa, -0.62, 0.62, 0.0, za)
    for y in (-0.66, 0.62):
        pts = [(x, yy, z) for yy in (y, y + 0.04) for (x, z) in ((4.0, 0.0), (dx1, Z), (dx1, Z - 0.3), (3.7, 0.0))]
        k.hullp(pts, 'plank2')
        k.beam((3.9, y + 0.02, 1.0), (dx1 + 0.05, y + 0.02, Z + 1.0), 0.06, 'log2')
    # under the deck: a bench and supply crates (the watch's cache)
    k.bx(-3.3, -2.0, -1.9, -1.55, 0.0, 0.45, 'plank2')
    k.col(-3.3, -2.0, -1.9, -1.55, 0.0, 0.45)
    crate(k, -2.8, 1.6, 0.0, 0.8, 0.7, 0.6, 'olive', 'olive2')
    k.col(-3.2, -2.4, 1.25, 1.95, 0.0, 0.6)
    k.finish('Landmark_Lookout', ao=ao)


# ================================================================ sawmill [10, 8], water wheel [3, 6], flume [1, 4]
def build_mill(k, ao):
    rnd = random.Random(211)
    k.begin()
    x0, x1, y0, y1 = -5.0, 5.0, -4.0, 4.0
    E = 4.2
    # heavy timber frame: posts, plates, the plank back and east walls (the wheel shaft comes through the east wall)
    posts = [(-4.8, -3.8), (-1.6, -3.8), (1.6, -3.8), (4.8, -3.8), (-4.8, 3.8), (-1.6, 3.8), (1.6, 3.8), (4.8, 3.8), (-4.8, 0.0)]
    for (x, y) in posts:
        k.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.0, E, 'log2')
        k.col(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.0, E)
    for y in (-3.8, 3.8):
        k.bx(x0, x1, y - 0.16, y + 0.16, E, E + 0.3, 'log2')
    wall(k, 'x', 3.85, -4.65, 4.65, 0.0, E - 0.01, 0.12, [], 'plankG', 'plank', top='plank2', cols=True)
    wall(k, 'y', 4.85, -3.65, 3.65, 0.0, E - 0.01, 0.12, [(-0.95, -0.35, 1.2, 1.8)], 'plankG', 'plank', top='plank2', cols=True)
    for i in range(1, 30):
        x = -4.65 + i * 0.31
        k.qy(x - 0.015, x + 0.015, 0.0, E, 3.85 - 0.066, -1, 'plank2')
    gable(k, x0, x1, y0, y1, E + 0.3, E + 2.2, 0.15, 'tin', 'tin2', over=0.4, ridge_along='x')
    # the gable ends (open below the ridge for the dust), a name board on the front eave
    k.bx(-2.4, 2.4, -4.62, -4.56, E - 0.4, E + 0.25, 'plank2')
    k.text('BRANNOCK SAWMILL', 0.0, -4.624, E - 0.3, 0.4, 'plankW', maxw=4.5, font='display')
    # carriage track and the log carriage with a log dogged on it (along X)
    for y in (-1.45, -0.65):
        k.bx(-4.6, 4.6, y - 0.05, y + 0.05, 0.0, 0.12, 'iron')
    for i in range(10):
        x = -4.4 + i * 0.98
        k.bx(x - 0.1, x + 0.1, -1.7, -0.4, 0.0, 0.06, 'log2', ink=False)
    k.bx(-3.4, 1.8, -1.6, -0.5, 0.12, 0.62, 'plank2')
    for x in (-2.8, -0.6, 1.2):
        k.bx(x - 0.12, x + 0.12, -1.65, -1.45, 0.62, 1.15, 'iron2')
    log_x(k, -3.8, 2.4, -1.05, 1.02, 0.4, 'log', seg=7)
    k.col(-3.8, 2.4, -1.7, -0.4, 0.0, 1.42)
    # the saw table and the big circular blade (teeth ring), the arbor, the drive belt to the wheel shaft (east)
    k.bx(2.8, 3.8, -1.9, 0.6, 0.0, 0.9, 'plank2')
    k.bx(2.75, 3.85, -1.95, 0.65, 0.9, 0.98, 'plank')
    k.cyl(3.3, -0.25, 0.92, 0.82, 0.82, 0.04, 'steel', seg=16, rot=(90, 0, 0))
    for i in range(12):
        a = i / 12 * 2 * math.pi
        k.hullp([(3.3 + math.cos(a) * 0.8, -0.29, 0.92 + math.sin(a) * 0.8), (3.3 + math.cos(a + 0.2) * 0.8, -0.29, 0.92 + math.sin(a + 0.2) * 0.8),
                 (3.3 + math.cos(a) * 0.92, -0.27, 0.92 + math.sin(a) * 0.92), (3.3 + math.cos(a) * 0.8, -0.25, 0.92 + math.sin(a) * 0.8)], 'iron', ink=False)
    k.cyl(3.3, 0.3, 0.92, 0.1, 0.1, 0.8, 'iron2', seg=6, rot=(90, 0, 0))
    k.cyl(3.3, 0.55, 0.92, 0.3, 0.3, 0.14, 'iron', seg=10, rot=(90, 0, 0))
    k.beam((3.3, 0.48, 1.22), (4.8, 0.48, 1.55), 0.05, 'iron2', ink=False)
    k.beam((3.3, 0.48, 0.62), (4.8, 0.48, 1.45), 0.05, 'iron2', ink=False)
    k.col(2.75, 3.85, -1.95, 0.65, 0.0, 1.0)
    # the gear housing at the shaft, sawdust heaps, sawn lumber at the back, peaveys on the wall
    k.bx(4.0, 4.79, 0.0, 1.2, 0.0, 1.9, 'iron2')
    k.col(4.0, 4.79, 0.0, 1.2, 0.0, 1.9)
    for (x, y, r, h) in ((2.4, 1.2, 0.8, 0.45), (3.9, -2.6, 0.6, 0.35)):
        k.cyl(x, y, 0.0, r, r * 0.25, h, 'logEnd', seg=8)
    for (cx, hh) in ((-3.4, 1.15), (-1.0, 0.85)):
        for i in range(int(hh / 0.1)):
            z = i * 0.1
            k.bx(cx - 1.1, cx + 1.1, 2.6, 3.6, z, z + 0.08, 'plank' if i % 2 else 'plank2', ink=(i == 0))
        k.col(cx - 1.1, cx + 1.1, 2.6, 3.6, 0.0, hh)
    for i in range(3):
        k.beam((1.2 + i * 0.3, 3.74, 0.0), (1.3 + i * 0.3, 3.74, 1.7), 0.04, 'plank2', ink=False)
    lantern(k, 0.0, 0.0, E + 0.0)
    k.finish('Mill', ao=ao)
    # water wheel frame [3, 6] (the rotor is its own piece): the stone piers and bearings, the tail race boards
    k.begin()
    for x in (-1.2, 1.2):
        k.bx(x - 0.3, x + 0.3, -0.5, 0.5, 0.0, 2.55, 'stone')
        k.bx(x - 0.33, x + 0.33, -0.53, 0.53, 2.55, 2.7, 'stone2')
        k.bx(x - 0.12, x + 0.12, -0.15, 0.15, 2.7, 2.95, 'iron2')
        k.col(x - 0.3, x + 0.3, -0.5, 0.5, 0.0, 2.7)
    for x in (-0.82, 0.82):
        k.bx(x - 0.05, x + 0.05, -2.9, 2.9, 0.0, 0.5, 'plank2')
    k.qz(-0.77, 0.77, -2.9, 2.9, 0.42, 1, 'water')
    k.cyl(-1.55, 0.0, 2.95, 0.12, 0.12, 0.5, 'iron2', seg=6, rot=(0, -90, 0))
    k.col(-0.85, 0.85, -2.9, 2.9, 0.0, 0.5)
    k.finish('WheelFrame', ao=ao)
    k.begin()
    R, W = 2.55, 1.2
    seg = 10
    for sx in (-0.55, 0.55):
        polyline(k, [(sx, math.cos(i / seg * 2 * math.pi) * R, math.sin(i / seg * 2 * math.pi) * R) for i in range(seg)], 0.12, 'log2', (1, 0, 0), closed=True)
        for i in range(6):
            a = i / 6 * 2 * math.pi
            k.beam((sx, math.cos(a) * 0.2, math.sin(a) * 0.2), (sx, math.cos(a) * R * 0.97, math.sin(a) * R * 0.97), 0.1, 'log')
        k.cyl(sx - 0.1, 0.0, 0.0, 0.28, 0.28, 0.2, 'log2', seg=8, rot=(0, 90, 0))
    for i in range(seg):
        a = (i + 0.5) / seg * 2 * math.pi
        cy, cz = math.cos(a) * (R - 0.15), math.sin(a) * (R - 0.15)
        k.bxr(0.0, cy, cz, W - 0.1, 0.06, 0.38, 'plank', rot=(math.degrees(a), 0, 0), ink=False)
    k.cyl(-0.9, 0.0, 0.0, 0.16, 0.16, 1.8, 'iron2', seg=6, rot=(0, 90, 0))
    k.finish('Wheel_Rotor', ao=False)
    # flume [1, 4] along Y: a plank trough at 5.6 m with water, on A-frame trestles
    k.begin()
    Zf = 5.45
    k.bx(-0.36, 0.36, -2.0, 2.0, Zf, Zf + 0.06, 'plank2')
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.31, sx * 0.36))
        k.bx(xa, xb, -2.0, 2.0, Zf + 0.06, Zf + 0.42, 'plank')
    k.bx(-0.31, 0.31, -2.0, 2.0, Zf + 0.3, Zf + 0.31, 'water', ink=False)
    for y in (-1.0, 1.0):
        for sx in (-1, 1):
            k.beam((sx * 0.75, y, 0.0), (sx * 0.3, y, Zf), 0.12, 'log2')
        k.bx(-0.5, 0.5, y - 0.07, y + 0.07, Zf - 0.15, Zf, 'log2')
        k.beam((-0.68, y, 0.9), (0.68, y, 0.9), 0.08, 'log2')
        for sx in (-1, 1):
            k.col(sx * 0.75 - 0.12, sx * 0.75 + 0.12, y - 0.08, y + 0.08, 0.0, 1.0)
    k.finish('Flume', ao=ao)


# ================================================================ the creek: water tiles, the spring falls
def build_creek(k, ao):
    rnd = random.Random(221)
    for name, seed in (('Water_A', 222), ('Water_B', 223)):
        r2 = random.Random(seed)
        k.begin()
        k.qz(-0.5, 0.5, -0.5, 0.5, 0.05, 1, 'water')
        for i in range(2):
            x = r2.uniform(-0.35, 0.2)
            y = r2.uniform(-0.4, 0.4)
            k.poly([(x, y, 0.056), (x + 0.32, y + 0.02, 0.056), (x + 0.3, y + 0.05, 0.056), (x + 0.02, y + 0.04, 0.056)], 'foam', (0, 0, 1))
        k.finish(name, ao=False)
    k.begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, 0.05, 1, 'water')
    k.poly([(-0.3, 0.2, 0.056), (0.25, 0.25, 0.056), (0.22, 0.29, 0.056), (-0.28, 0.24, 0.056)], 'foam', (0, 0, 1))
    k.finish('Water_C', ao=False)
    # the spring [4, 2] against the north wall: a rock cleft, a white fall, the plunge pool
    k.begin()
    rock(k, rnd, -1.35, 0.35, 0.75, 0.6, 4.6, n=7)
    rock(k, rnd, 1.35, 0.35, 0.7, 0.6, 4.0, n=7)
    rock(k, rnd, 0.0, 0.75, 0.75, 0.3, 5.2, n=6)
    k.hullp([(-0.45, 0.42, 3.9), (0.45, 0.42, 3.9), (-0.55, 0.25, 0.1), (0.55, 0.25, 0.1), (-0.45, 0.36, 3.9), (0.45, 0.36, 3.9), (-0.55, 0.15, 0.1), (0.55, 0.15, 0.1)], 'foam', ink=False)
    k.disc(0.0, -0.2, 0.06, 0.95, 'foam', n=10, rnd=rnd, jag=0.2)
    for (x, y) in ((-0.9, -0.6), (0.85, -0.7)):
        rock(k, rnd, x, y, 0.3, 0.25, 0.35)
    k.col(-2.0, -0.6, -0.2, 1.0, 0.0, 4.0)
    k.col(0.6, 2.0, -0.2, 1.0, 0.0, 3.6)
    k.col(-0.6, 0.6, 0.45, 1.0, 0.0, 4.0)
    k.finish('Falls', ao=ao)


# ================================================================ the logging camp
def build_camp(k, ao):
    rnd = random.Random(231)
    # wall tent [4, 5]: canvas walls on a pole frame, the front flaps tied back (-Y), a cot, a trunk, a lantern
    k.begin()
    hx, hy, zs, zr = 1.75, 2.25, 1.35, 2.6
    for sx in (-1, 1):
        k.hullp([(sx * hx, y, z) for y in (-hy, hy) for z in (0.0, zs)] + [(sx * (hx - 0.04), y, z) for y in (-hy, hy) for z in (0.0, zs)], 'canvas')
        k.hullp([(sx * (hx + 0.06), y, zs - 0.04) for y in (-hy - 0.06, hy + 0.06)] + [(0.0, y, zr) for y in (-hy - 0.06, hy + 0.06)] + [(sx * (hx + 0.02), y, zs - 0.07) for y in (-hy - 0.06, hy + 0.06)] + [(0.0, y, zr - 0.04) for y in (-hy - 0.06, hy + 0.06)],
                by_normal(top='canvas', bot='canvas2', other='canvas2'))
    k.hullp([(x, hy - 0.004, z) for x in (-hx + 0.045, hx - 0.045) for z in (0.0, zs)] + [(0.0, hy - 0.004, zr - 0.05)] + [(x, hy - 0.044, z) for x in (-hx + 0.045, hx - 0.045) for z in (0.0, zs)] + [(0.0, hy - 0.044, zr - 0.05)], 'canvas2')
    k.hullp([(-hx + 0.045, -hy + 0.004, zs), (hx - 0.045, -hy + 0.004, zs), (0.0, -hy + 0.004, zr - 0.05), (-hx + 0.045, -hy + 0.044, zs), (hx - 0.045, -hy + 0.044, zs), (0.0, -hy + 0.044, zr - 0.05)], 'canvas2')
    for sx in (-1, 1):
        k.cyl(sx * (hx - 0.28), -hy - 0.06, 0.0, 0.1, 0.1, zs, 'canvas2', seg=6)
        k.beam((sx * hx, -hy, zs), (sx * (hx + 0.6), -hy - 0.7, 0.0), 0.02, 'rope', ink=False)
        k.beam((sx * hx, hy, zs), (sx * (hx + 0.6), hy + 0.6, 0.0), 0.02, 'rope', ink=False)
        k.bx(sx * (hx + 0.6) - 0.03, sx * (hx + 0.6) + 0.03, -hy - 0.73, -hy - 0.67, 0.0, 0.2, 'plank2', ink=False)
    k.cyl(0.0, -hy - 0.02, 0.0, 0.04, 0.04, zr + 0.25, 'log2', seg=4)
    k.cyl(0.0, hy + 0.02, 0.0, 0.04, 0.04, zr + 0.25, 'log2', seg=4)
    k.cyl(0.0, hy - 0.6, zr - 0.2, 0.06, 0.06, 1.0, 'iron2', seg=5)
    k.bx(-hx + 0.1, -hx + 0.85, -1.0, 1.1, 0.35, 0.45, 'cloth2')
    for y in (-0.9, 1.0):
        k.bx(-hx + 0.12, -hx + 0.83, y - 0.03, y + 0.03, 0.0, 0.35, 'plank2', ink=False)
    k.bx(0.7, 1.5, 1.2, 1.8, 0.0, 0.5, 'plankR')
    lantern(k, 0.0, 0.3, zr - 0.15)
    k.col(-hx, hx, hy - 0.05, hy, 0.0, zs)
    k.col(-hx, -hx + 0.05, -hy, hy, 0.0, zs)
    k.col(hx - 0.05, hx, -hy, hy, 0.0, zs)
    k.col(-hx + 0.1, -hx + 0.85, -1.0, 1.1, 0.0, 0.45)
    k.col(0.7, 1.5, 1.2, 1.8, 0.0, 0.5)
    k.finish('Tent', ao=ao)
    # cook shack [6, 5]: a small log cook house, open front under a lean roof: range, table and benches, pots, water
    k.begin()
    from fr_house import house, table, bench, stove
    holes = {'f': [(-2.3, 2.3, 0.0, 2.35, 'door')], 'l': [(-0.6, 0.6, 1.1, 1.9, 'open')], 'r': [], 'b': [(-0.7, 0.5, 1.1, 1.9, 'win')]}
    F = house(k, 6.0, 5.0, 0.0, 2.7, style='log', out='log', inside='plank', holes=holes, roof='gable_x', ridge=4.1, walkin=False,
              shutters=None, roof_c=('shingle', 'shingle2'), cols=False)
    from fr_base import wall as wall_
    T = 0.22
    for (x0, x1) in ((F['x0'], -2.3), (2.3, F['x1'])):
        k.col(x0, x1, F['yf'] - T / 2, F['yf'] + T / 2, 0.0, 2.7)
    k.col(F['x0'], F['x1'], F['yf'] - T / 2, F['yf'] + T / 2, 2.35, 2.7)
    k.col(F['x0'], F['x1'], F['yb'] - T / 2, F['yb'] + T / 2, 0.0, 2.7)
    k.col(F['x0'], F['x0'] + T, F['yf'], F['yb'], 0.0, 2.7)
    k.col(F['x1'] - T, F['x1'], F['yf'], F['yb'], 0.0, 2.7)
    iy0, iy1, ix0, ix1 = F['yf'] + T / 2, F['yb'] - T / 2, F['x0'] + T, F['x1'] - T
    k.qz(ix0 + 0.01, ix1 - 0.01, iy0 + 0.01, iy1 - 0.01, 0.006, 1, 'plank2')
    # the range against the back wall
    k.bx(-2.5, -1.0, iy1 - 0.75, iy1, 0.0, 0.85, 'iron2')
    k.bx(-2.55, -0.95, iy1 - 0.8, iy1, 0.85, 0.92, 'iron')
    for x in (-2.15, -1.4):
        k.cyl(x, iy1 - 0.4, 0.92, 0.18, 0.15, 0.25, 'steel', seg=8)
    k.cyl(-1.2, iy1 - 0.2, 0.92, 0.08, 0.08, 3.6, 'iron', seg=6)
    k.qy(-2.2, -1.3, 0.25, 0.6, iy1 - 0.754, -1, 'fire')
    k.col(-2.55, -0.95, iy1 - 0.8, iy1, 0.0, 0.92)
    table(k, -0.4, 1.8, iy0 + 1.0, iy0 + 1.9, 0.0, 0.78, 'plank')
    bench(k, -0.3, 1.7, iy0 + 0.5, iy0 + 0.8, 0.0)
    for x in (0.1, 0.9, 1.4):
        k.cyl(x, iy0 + 1.45, 0.78, 0.09, 0.08, 0.1, 'steel', seg=6, ink=False)
    barrel(k, ix1 - 0.4, iy1 - 0.4, 0.0, 0.3, 0.85)
    k.col(ix1 - 0.72, ix1 - 0.08, iy1 - 0.72, iy1 - 0.08, 0.0, 0.85)
    k.bx(ix1 - 0.3, ix1, iy0 + 0.2, iy0 + 1.6, 0.0, 1.6, 'plank2')
    for z in (0.5, 1.05, 1.55):
        for i in range(3):
            k.cyl(ix1 - 0.15, iy0 + 0.45 + i * 0.4, z, 0.09, 0.09, 0.14, ('fuel', 'cloth', 'steel')[i], seg=6, ink=False)
    k.col(ix1 - 0.3, ix1, iy0 + 0.2, iy0 + 1.6, 0.0, 1.6)
    lantern(k, 0.6, 0.0, 2.6)
    k.bx(-1.3, 1.3, F['yf'] - T / 2 - 0.05, F['yf'] - T / 2 - 0.004, 2.38, 2.68, 'plank2')
    k.text('COOKHOUSE', 0.0, F['yf'] - T / 2 - 0.054, 2.43, 0.2, 'plankW', maxw=2.3, font='display')
    k.finish('CookShack', ao=ao)
    # fire pit [3, 3]: stone ring, logs, coals (glow), a cooking tripod with a kettle, log benches on three sides
    k.begin()
    for i in range(7):
        a = i / 7 * 2 * math.pi
        rock(k, rnd, math.cos(a) * 0.6, math.sin(a) * 0.6, 0.2, 0.17, 0.25, n=5, top=2)
    k.disc(0, 0, 0.03, 0.45, 'coal', n=8)
    for i in range(3):
        a = i / 3 * 2 * math.pi + 0.3
        k.beam((math.cos(a) * 0.4, math.sin(a) * 0.4, 0.06), (math.cos(a) * -0.05, math.sin(a) * -0.05, 0.28), 0.1, 'log2')
    for i in range(3):
        a = i / 3 * 2 * math.pi + 1.0
        k.beam((math.cos(a) * 0.7, math.sin(a) * 0.7, 0.0), (0.0, 0.0, 1.45), 0.04, 'iron2')
    k.beam((0.0, 0.0, 1.45), (0.0, 0.0, 0.85), 0.012, 'iron2', ink=False)
    k.cyl(0.0, 0.0, 0.62, 0.17, 0.15, 0.24, 'iron2', seg=8)
    for (x, y, yaw) in ((0.0, -1.25, 0), (-1.25, 0.0, 90), (1.25, 0.1, 90)):
        k.push(x, y, yaw, 0)
        log_x(k, -0.75, 0.75, 0.0, 0.3, 0.2, 'log', seg=6)
        k.bx(-0.6, 0.6, -0.14, 0.14, 0.38, 0.47, 'logEnd', ink=False)
        k.pop()
    k.col(-0.75, 0.75, -1.45, -1.05, 0.0, 0.47)
    k.col(-1.45, -1.05, -0.75, 0.75, 0.0, 0.47)
    k.col(1.05, 1.45, -0.65, 0.85, 0.0, 0.47)
    k.col(-0.55, 0.55, -0.55, 0.55, 0.0, 0.5)
    k.finish('FirePit', ao=ao)
    k.begin()
    for i in range(5):
        a = i / 5 * 2 * math.pi
        k.hullp([(math.cos(a) * 0.12, math.sin(a) * 0.12, 0.05), (math.cos(a + 0.6) * 0.3, math.sin(a + 0.6) * 0.3, 0.04),
                 (math.cos(a + 0.3) * 0.06, math.sin(a + 0.3) * 0.06, 0.45 + 0.2 * (i % 2))], 'fire' if i % 2 else 'fire2', ink=False)
    k.finish('FirePit_Glow', ao=False)
    # sawhorse [2, 1] with a crosscut saw and a log on it
    k.begin()
    for x in (-0.65, 0.65):
        for sy in (-1, 1):
            k.beam((x + sy * 0.035, sy * 0.35, 0.0), (x + sy * 0.035, 0.0, 0.85), 0.06, 'plank2')
    log_x(k, -0.95, 0.95, 0.0, 0.98, 0.17, 'log', seg=6)
    k.bxr(0.25, -0.18, 1.12, 1.4, 0.01, 0.16, 'steel', rot=(0, 0, 8))
    for x in (-0.48, 0.98):
        k.cyl(x + 0.0, -0.18 + 0.0, 1.05, 0.03, 0.03, 0.3, 'plank2', seg=4, ink=False)
    k.col(-0.95, 0.95, -0.38, 0.38, 0.0, 1.15)
    k.finish('Sawhorse', ao=ao)
    # log arch [3, 5]: two big wheels under an arched frame with a log hung by its end (a skidding arch)
    k.begin()
    for sx in (-1, 1):
        wheel(k, sx * 1.15, 0.5, 0.95, 0.95, w=0.12, spokes=6)
        k.beam((sx * 1.15, 0.5, 0.95), (sx * 0.4, 0.5, 2.35), 0.14, 'iron2')
    k.beam((-0.42, 0.5, 2.35), (0.42, 0.5, 2.35), 0.16, 'iron2')
    k.bx(-1.3, 1.3, 0.45, 0.55, 0.9, 1.0, 'iron2', ink=False)
    k.beam((0.0, 0.5, 2.3), (0.0, 0.0, 1.0), 0.03, 'iron', ink=False)
    k.tube((0.0, 0.1, 0.9), (0.0, -2.3, 0.22), 0.3, 0.25, 'log', seg=6)
    k.beam((0.0, 0.5, 0.95), (0.0, 2.4, 0.5), 0.1, 'plank2')
    k.col(-1.3, 1.3, -0.2, 1.2, 0.0, 2.3)
    k.col(-0.3, 0.3, -2.4, -0.2, 0.0, 1.0)
    k.finish('LogArch', ao=ao)
    # tool rack [2, 1]: axes, a crosscut saw, peaveys and a shovel on a pole rack
    k.begin()
    for x in (-0.9, 0.9):
        post(k, x, 0.0, 0.0, 1.5, 0.06, 'log2')
    log_x(k, -0.95, 0.95, 0.0, 1.35, 0.05, 'log', seg=5, ends=False)
    log_x(k, -0.95, 0.95, 0.12, 0.25, 0.04, 'log', seg=5, ends=False)
    for i in range(6):
        x = -0.7 + i * 0.28
        k.beam((x, 0.12, 0.25), (x, 0.0, 1.38), 0.035, 'plank2', ink=False)
        k.bx(x - 0.1, x + 0.04, -0.03, 0.03, 1.2, 1.36, 'steel', ink=False) if i % 2 else k.bx(x - 0.05, x + 0.05, 0.08, 0.16, 0.1, 0.35, 'iron2', ink=False)
    k.col(-0.95, 0.95, -0.15, 0.2, 0.0, 1.5)
    k.finish('ToolRack', ao=ao)
    # camp sign
    k.begin()
    for x in (-0.6, 0.6):
        k.cyl(x, 0.0, 0.0, 0.07, 0.06, 1.9, 'log2', seg=5)
    k.bx(-0.85, 0.85, -0.05, 0.05, 1.1, 1.75, 'plank')
    k.text('CAMP 9', 0.0, -0.054, 1.22, 0.36, 'plankR', maxw=1.5, font='display')
    k.col(-0.68, 0.68, -0.08, 0.08, 0.0, 1.75)
    k.finish('CampSign', ao=ao)


# ================================================================ the old mine entrance [8, 5] (against a wall to the north, +Y)
def build_mine(k, ao):
    rnd = random.Random(241)
    k.begin()
    # the rock mass round the adit, rising toward the back
    for (x, y, rx, ry, h) in ((-2.9, 0.4, 1.2, 1.9, 4.6), (2.9, 0.5, 1.2, 1.8, 5.2), (-1.6, 1.4, 1.2, 1.1, 6.0),
                              (1.7, 1.5, 1.2, 1.0, 6.4), (0.0, 1.9, 1.3, 0.6, 6.8), (-3.4, -1.5, 0.6, 0.5, 1.4), (3.3, -1.6, 0.7, 0.55, 1.1)):
        rock(k, rnd, x, y, rx, ry, h, n=7, top=3)
    # the adit: dark walls and roof (inside), timber sets, the boarded end, rails and an ore cart
    k.bx(-1.75, -1.3, -1.2, 2.45, 0.0, 2.75, 'rock2')
    k.bx(1.3, 1.75, -1.2, 2.45, 0.0, 2.75, 'rock2')
    k.bx(-1.8, 1.8, -1.22, 2.47, 2.75, 3.4, 'rock2')
    k.bx(-1.3, 1.3, 2.3, 2.45, 0.0, 2.75, 'coal')
    k.qx(-1.15, 2.3, 0.0, 2.75, -1.3 + 0.004, 1, 'coal')
    k.qx(-1.15, 2.3, 0.0, 2.75, 1.3 - 0.004, -1, 'coal')
    k.qz(-1.3, 1.3, -1.15, 2.3, 2.75 - 0.004, -1, 'coal')
    for y in (-1.3, 0.3, 1.6):
        for sx in (-1, 1):
            k.bx(sx * 1.15 - 0.13, sx * 1.15 + 0.13, y - 0.13, y + 0.13, 0.0, 2.55, 'log2')
        k.bx(-1.3, 1.3, y - 0.14, y + 0.14, 2.45, 2.72, 'log')
    for i in range(6):
        z = 0.15 + i * 0.42
        k.bx(-1.1, 1.1, 2.12, 2.22, z, z + 0.36, 'plank2' if i % 2 else 'plankG')
    k.beam((-1.0, 2.08, 0.3), (1.0, 2.08, 2.2), 0.1, 'plank2')
    k.bx(-0.6, 0.6, 2.04, 2.06, 1.3, 1.75, 'plankW')
    k.text('KEEP OUT', 0.0, 2.036, 1.38, 0.22, 'cloth', maxw=1.1, font='display')
    for x in (-0.45, 0.45):
        k.bx(x - 0.04, x + 0.04, -2.45, 2.1, 0.06, 0.14, 'iron')
    for i in range(9):
        y = -2.3 + i * 0.5
        k.bx(-0.65, 0.65, y - 0.07, y + 0.07, 0.0, 0.06, 'log2', ink=False)
    # the ore cart on the rails, just outside
    k.push(0.0, -1.8, 0, 0.0)
    k.hullp([(x, y, z) for (x, y, z) in ((-0.55, -0.5, 0.3), (0.55, -0.5, 0.3), (-0.55, 0.5, 0.3), (0.55, 0.5, 0.3),
                                         (-0.65, -0.6, 1.05), (0.65, -0.6, 1.05), (-0.65, 0.6, 1.05), (0.65, 0.6, 1.05))], 'rust')
    k.bx(-0.55, 0.55, -0.5, 0.5, 0.95, 1.02, 'rock2', ink=False)
    for y in (-0.35, 0.35):
        for x in (-0.45, 0.45):
            k.cyl(x - 0.025, y, 0.29, 0.15, 0.15, 0.05, 'iron2', seg=8, rot=(0, 90, 0))
    k.pop()
    k.col(-0.68, 0.68, -2.45, -1.15, 0.0, 1.05)
    # the portal frame, its sign and a lantern
    for sx in (-1, 1):
        k.bx(sx * 1.25 - 0.17, sx * 1.25 + 0.17, -1.4, -1.06, 0.0, 2.9, 'log')
    k.bx(-1.65, 1.65, -1.42, -1.04, 2.9, 3.25, 'log2')
    k.bx(-1.4, 1.4, -1.5, -1.43, 3.3, 3.9, 'plank2')
    k.text('OLD LANTERN MINE', 0.0, -1.504, 3.42, 0.32, 'plankW', maxw=2.6, font='display')
    lantern(k, 1.1, -1.5, 2.8)
    # collision: the rock mass (left, right, back), the adit walls, the portal posts
    k.col(-4.0, -1.42, -0.7, 2.5, 0.0, 4.5)
    k.col(1.42, 4.0, -0.7, 2.5, 0.0, 4.5)
    k.col(-4.0, 4.0, 2.2, 2.5, 0.0, 6.0)
    k.col(-3.9, -2.9, -2.0, -0.7, 0.0, 1.2)
    k.col(2.7, 3.9, -2.1, -0.7, 0.0, 1.0)
    k.col(-1.42, -1.08, -1.4, -0.7, 0.0, 2.9)
    k.col(1.08, 1.42, -1.4, -0.7, 0.0, 2.9)
    for y in (0.3, 1.6):
        for sx in (-1, 1):
            k.col(sx * 1.15 - 0.14, sx * 1.15 + 0.14, y - 0.14, y + 0.14, 0.0, 2.55)
    k.finish('Mine', ao=ao)


# ================================================================ the radio relay and the lean-to (plateau)
def build_highcamp(k, ao):
    rnd = random.Random(251)
    k.begin()
    for i in range(3):
        a = i / 3 * 2 * math.pi + 0.5
        k.beam((math.cos(a) * 0.8, math.sin(a) * 0.8, 0.0), (0.0, 0.0, 2.2), 0.06, 'steel')
    k.cyl(0, 0, 0.0, 0.05, 0.04, 6.5, 'steel', seg=5)
    for (z, L) in ((5.0, 0.7), (6.2, 0.5)):
        k.bx(-L, L, -0.02, 0.02, z, z + 0.04, 'steel', ink=False)
    k.cyl(0.0, 0.0, 6.5, 0.07, 0.07, 0.1, 'red', seg=6, ink=False)
    k.push(0.55, -0.6, 0, 0.0)
    for (x, h) in ((-0.4, 0.5), (0.4, 0.5), (-0.4, 1.1), (0.4, 1.1)):
        k.bx(x - 0.03, x + 0.03, -0.25 if h < 1 else 0.25, (-0.25 if h < 1 else 0.25) + 0.06, 0.0, h, 'steel', ink=False)
    k.bxr(0.0, 0.0, 0.85, 1.0, 0.75, 0.04, 'solar', rot=(-35, 0, 0))
    k.pop()
    k.bx(-0.9, -0.3, 0.3, 0.8, 0.0, 0.6, 'olive')
    k.qy(-0.85, -0.35, 0.25, 0.5, 0.296, -1, 'iron2')
    k.col(-0.9, -0.3, 0.3, 0.8, 0.0, 0.6)
    k.col(0.05, 1.05, -0.95, -0.25, 0.0, 1.15)
    k.col(-0.12, 0.12, -0.12, 0.12, 0.0, 2.2)
    k.finish('Relay', ao=ao)
    # lean-to [4, 3]: a pole frame with a bark-and-tarp roof sloping to the back, a bedroll, crates, a jerry can
    k.begin()
    for x in (-1.8, 1.8):
        k.beam((x, -1.2, 0.0), (x, -1.2, 2.2), 0.12, 'log2')
        k.beam((x, -1.2, 2.2), (x, 1.3, 0.0), 0.1, 'log2')
    log_x(k, -2.0, 2.0, -1.2, 2.2, 0.08, 'log', seg=5)
    shed_roof(k, -1.95, 1.95, -1.35, 1.3, 2.3, 0.15, 0.06, 'olive', 'olive2')
    k.bx(-1.2, 0.6, -0.4, 0.4, 0.0, 0.14, 'cloth2')
    for (x, y, s) in ((1.2, 0.3, 0.6), (1.25, -0.4, 0.5)):
        crate(k, x, y, 0.0, s, s * 0.8, s * 0.7, 'olive', 'olive2')
    k.bx(-1.65, -1.35, 0.1, 0.35, 0.0, 0.42, 'cloth')
    k.col(-1.92, -1.68, -1.32, -1.08, 0.0, 2.2)
    k.col(1.68, 1.92, -1.32, -1.08, 0.0, 2.2)
    k.col(0.9, 1.5, -0.62, 0.55, 0.0, 0.5)
    k.col(-2.0, 2.0, 0.2, 1.3, 0.0, 0.9)
    k.finish('LeanTo', ao=ao)


def build_wild(k, ao):
    build_trees(k, ao)
    build_backdrop_trees(k)
    build_rocks(k, ao)
    build_logs(k, ao)
    build_bridge(k, ao)
    build_lookout(k, ao)
    build_mill(k, ao)
    build_creek(k, ao)
    build_camp(k, ao)
    build_mine(k, ao)
    build_highcamp(k, ao)
