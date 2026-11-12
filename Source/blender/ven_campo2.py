"""INKBOLT kit-venetian zone 1, part 2: the merchants' loggia with its roof terrace, the Fountain of the Four Winds
(landmark), and the campo's small pieces: cafe table sets, parasol tables, planters, lemon pots, urns, the menu board,
benches, the well-head, lamp posts, the kiosk, the flower stall, market stalls, crates, barrels, the hand cart,
paving (cobbles and the white stone bands). Conventions: ven_base.py."""
import math
import random

from mathutils import Euler

from ven_base import *  # noqa: F401,F403
from ven_base import (kit, done, arch_curve, glints, flowers, balustrade_x, text, steps, lantern_glow)
from ven_campo import chair, bistro_table, parasol, awning


# ================================================================ the merchants' loggia (roof terrace) [16, 6]
def build_loggia(pal, ao):
    """Footprint x -8..8, y -3..3: an open arcade x -8..5.5 (four round arches on each long side on Istrian columns,
    open at the ends) under a flat roof terrace at 3.6 m with a balustrade; the stair x 5.6..7.4 rising +Y along
    the east end to a landing (y 2..3) that steps west onto the terrace. Inside, a stone bench with produce crates."""
    k = kit(pal).begin()
    X0, X1 = -8.0, 5.5
    H = TERR - 0.3
    xs = [X0 + 0.3 + i * (X1 - X0 - 0.6) / 4 for i in range(5)]
    for y in (-2.7, 2.7):
        for x in xs:
            k.lathe(x, y, 0.0, [(0.26, 0.0), (0.26, 0.18), (0.16, 0.26), (0.14, 2.0), (0.19, 2.12), (0.0, 2.12)], 'stone', seg=6, a0=math.pi / 6)
            k.bxc(x - 0.27, x + 0.27, y - 0.27, y + 0.27, 2.12, 2.3, 'stone', cull='t')
            k.col(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0.0, 2.3)
        for (a, b) in zip(xs, xs[1:]):
            cur = arch_curve(a + 0.27, b - 0.27, 2.3, 'seg', 4, rise=0.62)
            top = H - 0.3
            pts = [(a, 2.3), (a + 0.27, 2.3)] + cur[1:-1] + [(b - 0.27, 2.3), (b, 2.3), (b, top), (a, top)]
            k.prism_xz(pts, y - 0.22, y + 0.22, 'stucco', cull='', colors=lambda n: 'stuccoD' if n.z < -0.2 else 'stucco')
            for f in (-1, 1):
                yf = y + f * 0.226
                for (pa, pb) in zip(cur, cur[1:]):
                    def out(p):
                        dx, dz = p[0] - (a + b) / 2, p[1] - 2.3
                        L = math.hypot(dx, dz) or 1.0
                        return (p[0] + dx / L * 0.1, p[1] + max(0.0, dz / L) * 0.1)
                    qa, qb = out(pa), out(pb)
                    k.poly([(pa[0], yf, pa[1]), (qa[0], yf, qa[1]), (qb[0], yf, qb[1]), (pb[0], yf, pb[1])], 'stone', (0, f, 0))
        k.bxc(X0, X1, y - 0.24, y + 0.24, H - 0.3, H, 'stone', cull='t')
    for x in (X0 + 0.3, X1 - 0.3):
        cur = arch_curve(-2.43, 2.43, 2.304, 'seg', 4, rise=0.9)
        pts = [(-2.7, 2.304)] + cur + [(2.7, 2.304), (2.7, H - 0.004), (-2.7, H - 0.004)]
        k.push(x, 0, 90)
        k.prism_xz([(-px, pz) for (px, pz) in pts], -0.2, 0.2, 'stucco', colors=lambda n: 'stuccoD' if n.z < -0.2 else 'stucco')
        k.pop()
    k.bxc(X0 - 0.1, X1, -3.0, 3.0, H, TERR, 'stone')
    k.qz(X0 + 0.3, X1 - 0.3, -2.46, 2.46, H - 0.004, -1, 'plaster')
    k.wcol(X0, X1, -3.0, 3.0, H, TERR)
    text(k, 'LOGGIA DEI MERCANTI', (X0 + X1) / 2, -3.004, H + 0.04, 0.22, 'shutD', font='display', maxw=9.0)
    # a stone curb round the terrace (the balustrade itself is the zone's rail layer at 3.6 m on the edge cells);
    # lemon trees in pots
    for (a_, b_, c_, d_) in ((X0 - 0.1, X1, -3.0, -2.92), (X0 - 0.1, X1, 2.92, 3.0), (X0 - 0.1, X0 - 0.02, -2.92, 2.92)):
        k.bxc(a_, b_, c_, d_, TERR, TERR + 0.1, 'stone', cull='b', ink=False)
    for px in (X0 + 2.0, -1.2, 2.6):
        k.lathe(px, 0.0, TERR, [(0.22, 0.0), (0.3, 0.5), (0.33, 0.55), (0.0, 0.55)], 'terra', seg=6)
        k.cyl(px, 0.0, TERR + 0.55, 0.04, 0.04, 0.5, 'wood', seg=4, ink=False)
        k.sph(px, 0.0, TERR + 1.35, 0.42, 'leaf', seg=(5, 4))
        for i in range(4):
            a = i * 1.6
            k.hullp([(px + math.cos(a) * 0.38 + dx, math.sin(a) * 0.38 + dy, TERR + 1.3 + 0.1 * (i % 2) + dz) for (dx, dy, dz) in ((0.05, 0, 0), (-0.04, 0.03, 0), (0, -0.04, 0.03), (0, 0, -0.05))], 'lemon', ink=False)
        k.col(px - 0.33, px + 0.33, -0.33, 0.33, TERR, TERR + 1.6)
    # the stair along the east end: 20 treads rising +Y from y = -3, the landing block, the outer rail
    sx0, sx1 = 5.6, 7.4
    ye = steps(k, sx0, sx1, -3.0, 20, c='stone')
    k.bxc(X1, sx1 + 0.1, ye, 3.0, 0.0, TERR, 'stone', cull='bl')
    k.wcol(X1, sx1, ye, 3.0, 0.0, TERR)
    k.push(sx1 + 0.003, 0, 90)
    k.prism_xz([(-3.0, 0.0), (ye, 0.0), (ye, TERR), (-3.0 + TREAD, RISE)], 0.0, -0.1, 'stoneD', cull='b')
    k.pop()
    k.beam((sx1 + 0.05, -2.6, 1.0 + 2 * RISE), (sx1 + 0.05, ye, TERR + 1.0), 0.05, 'iron')
    for i in range(1, 7):
        ya = -3.0 + i * 0.75
        hz = (ya + 3.0) / TREAD * RISE
        k.bxc(sx1 + 0.03, sx1 + 0.07, ya - 0.02, ya + 0.02, hz, hz + 1.0, 'iron', cull='tb', ink=False)
    for i in range(5):
        ya, yb = -3.0 + i * 1.0, -2.0 + i * 1.0
        k.col(sx1, sx1 + 0.12, ya, yb, 0.0, (yb + 3.0) / TREAD * RISE + 1.0)
    k.col(sx1, sx1 + 0.12, ye, 3.0, TERR, TERR + 1.0)
    k.push(sx1 + 0.04, (ye + 3.0) / 2, 90, TERR)
    balustrade_x(k, -(3.0 - ye) / 2, (3.0 - ye) / 2, 0.0, 0.0, h=1.0, every=0.4, w=0.12, ends=(True, True))
    k.pop()
    balustrade_x(k, X1 + 0.1, sx1 - 0.07, 2.93, TERR, h=1.0, every=0.4, w=0.12, ends=(True, True))
    k.col(X1, sx1 + 0.12, 2.86, 3.0, TERR, TERR + 1.0)
    # inside: a stone bench down the middle, crates of produce on it
    k.bx(-6.5, 3.5, -0.35, 0.35, 0.0, 0.45, 'stone')
    k.col(-6.5, 3.5, -0.35, 0.35, 0.0, 0.45)
    for i, c in enumerate(('lemon', 'fRed', 'leafL', 'fOrange', 'fPurp', 'leaf')):
        cx = -5.8 + i * 1.6
        k.bx(cx - 0.32, cx + 0.32, -0.25, 0.25, 0.45, 0.72, 'wood')
        k.hullp([(cx - 0.26, -0.2, 0.72), (cx + 0.26, -0.2, 0.72), (cx + 0.26, 0.2, 0.72), (cx - 0.26, 0.2, 0.72), (cx - 0.1, -0.05, 0.84), (cx + 0.12, 0.06, 0.83)], c, ink=False)
    done(k, 'Loggia', ao)


# ================================================================ the Fountain of the Four Winds (landmark) [14, 14]
def volute(k, ang, r0, z0, s=1.0):
    """one of the four winds: an S-scroll of stone leaning out from the pedestal toward `ang`; a jet from its lip
    arcs into the basin"""
    k.push(math.cos(ang) * r0, math.sin(ang) * r0, math.degrees(ang))
    prof = [(-0.25 * s, 0.0), (0.2 * s, 0.0)]
    for i in range(1, 7):
        t = i / 6
        prof.append((0.2 * s + 0.42 * math.sin(t * math.pi * 0.85) * s, (0.15 + 1.5 * t) * s))
    prof += [(0.62 * s, 1.8 * s), (0.35 * s, 1.98 * s), (0.05 * s, 1.85 * s)]
    for i in range(1, 6):
        t = 1 - i / 6
        prof.append((-0.2 * s + 0.32 * math.sin(t * math.pi * 0.85) * s, (0.2 + 1.45 * t) * s))
    k.push(0, 0, 0, z0)
    k.push(0, 0, 0)
    k.m.parent = k.m.parent @ Euler((0.0, 0.0, math.radians(-90))).to_matrix().to_4x4()
    k.prism_xz([(-py, pz) for (py, pz) in prof], -0.24 * s, 0.24 * s, 'stone', colors=lambda n: 'stoneD' if n.z < -0.3 else 'stone')
    k.pop()
    k.pop()
    k.pop()
    sx, sy = math.cos(ang), math.sin(ang)
    d0 = r0 + 0.62 * s
    lip = (sx * d0, sy * d0, z0 + 1.82 * s)
    pts = [lip]
    for i in range(1, 6):
        t = i / 5
        d = d0 + t * 1.5
        pts.append((sx * d, sy * d, lip[2] + 0.35 * t - 1.25 * t * t * (lip[2] - 0.6) / 1.25))
    for (a, b) in zip(pts, pts[1:]):
        k.beam(a, b, 0.09, 'waterL', ink=False)


def build_fountain(pal, ao):
    """Footprint 14 x 14 (x, y -7..7): a low stone platform, the octagonal basin (r 5.2, rim 0.85 m) brim full, the
    pedestal with four great stone scrolls (the four winds) each pouring a jet into the basin, the upper tazza
    spilling a sheet of water, the bronze stem, the gilt armillary sphere with the sun at its heart (about 6 m)."""
    k = kit(pal).begin()
    oct8 = math.pi / 8
    k.lathe(0, 0, 0.0, [(6.6, 0.0), (6.6, 0.05), (0.0, 0.05)], 'stoneD', seg=8, a0=oct8, ink=False)
    k.disc(0, 0, 0.054, 6.2, 'stone', n=8, a0=oct8)
    R0, R1 = 5.2, 4.75
    k.lathe(0, 0, 0.056, [(R1, 0.0), (R0, 0.0), (R0, 0.66), (R0 + 0.12, 0.68), (R0 + 0.12, 0.8), (R1 - 0.08, 0.8), (R1 - 0.08, 0.7), (R1, 0.66)],
            'stone', seg=8, closed=True, a0=oct8)
    for i in range(8):
        a = oct8 * 2 * i
        ca, sa = math.cos(a), math.sin(a)
        rr = R0 * math.cos(oct8) + 0.006
        tx, ty = -sa, ca
        k.poly([(ca * rr + tx * 0.9, sa * rr + ty * 0.9, 0.18), (ca * rr - tx * 0.9, sa * rr - ty * 0.9, 0.18),
                (ca * rr - tx * 0.9, sa * rr - ty * 0.9, 0.58), (ca * rr + tx * 0.9, sa * rr + ty * 0.9, 0.58)], 'marbleR', (ca, sa, 0))
    k.disc(0, 0, 0.73, (R1 - 0.07) / math.cos(oct8) * math.cos(oct8), 'water', n=8, a0=oct8)
    for r in (2.3, 3.2, 4.1):
        ring = [(math.cos(i * math.pi / 8) * r, math.sin(i * math.pi / 8) * r) for i in range(16)]
        ring2 = [(math.cos(i * math.pi / 8) * (r + 0.09), math.sin(i * math.pi / 8) * (r + 0.09)) for i in range(16)]
        for i in range(16):
            if i % 4 == 3:
                continue
            j = (i + 1) % 16
            k.poly([(ring[i][0], ring[i][1], 0.734), (ring[j][0], ring[j][1], 0.734), (ring2[j][0], ring2[j][1], 0.734), (ring2[i][0], ring2[i][1], 0.734)], 'waterL', (0, 0, 1))
    k.lathe(0, 0, 0.73, [(1.6, 0.0), (1.6, 0.2), (1.25, 0.35), (1.0, 0.5), (0.95, 2.1), (1.15, 2.25), (0.0, 2.25)], 'stone', seg=8, a0=oct8)
    for i in range(4):
        volute(k, i * math.pi / 2 + math.pi / 4, 0.8, 0.85, s=1.05)
    k.lathe(0, 0, 2.98, [(0.5, 0.0), (1.9, 0.35), (2.05, 0.5), (1.85, 0.5), (0.0, 0.42)], 'stone', seg=12)
    k.disc(0, 0, 3.44, 1.86, 'water', n=12)
    k.lathe(0, 0, 2.6, [(2.1, 0.0), (2.08, 0.86), (2.0, 0.86), (2.02, 0.0)], 'waterL', seg=12, closed=True, ink=False)
    k.lathe(0, 0, 3.44, [(0.32, 0.0), (0.22, 0.5), (0.14, 1.4), (0.25, 1.6), (0.0, 1.6)], 'bronze', seg=8)
    cz = 5.75
    k.sph(0, 0, cz, 0.28, 'gold', seg=(8, 6))
    for i in range(12):
        a = i * math.pi / 6
        k.beam((math.cos(a) * 0.3, math.sin(a) * 0.3, cz), (math.cos(a) * 0.5, math.sin(a) * 0.5, cz), 0.06, 'gold', ink=False)
    for (rx, ry, c) in ((0, 0, 'gold'), (90, 0, 'gold'), (90, 90, 'gold'), (23, 0, 'bronze')):
        k.push(0, 0, 0, cz)
        k.m.parent = k.m.parent @ Euler((math.radians(rx), 0.0, math.radians(ry))).to_matrix().to_4x4()
        r = 1.05 + (0.04 if c == 'bronze' else 0.0) + (0.02 if (rx, ry) == (90, 90) else 0.0)
        k.lathe(0, 0, -0.05, [(r, 0.0), (r + 0.07, 0.0), (r + 0.07, 0.1), (r, 0.1)], c, seg=16, closed=True)
        k.pop()
    k.beam((0, -0.45, cz - 1.25), (0, 0.45, cz + 1.25), 0.06, 'bronze')
    # collision: the basin (re-cut to the drawn octagon by col_fit), the water inside it up to the pedestal
    k.col(-R0 - 0.12, R0 + 0.12, -R0 - 0.12, R0 + 0.12, 0.0, 0.86)
    k.col(-R1 + 0.25, R1 - 0.25, -R1 + 0.25, R1 - 0.25, 0.0, 2.6)
    done(k, 'Landmark_Fountain', ao)


# ================================================================ small pieces of the campo
def build_small(pal, ao):
    rnd = random.Random(21)
    # cafe table: a bistro table and two chairs (1 cell)
    k = kit(pal).begin()
    bistro_table(k, 0, 0, cols=k.cols)
    chair(k, -0.0, -0.42, 0)
    chair(k, 0.0, 0.42, 180)
    done(k, 'CafeTable', ao)
    # parasol table [2, 2]: a square table, four chairs, the parasol (two paint jobs by the theme)
    for name, v in (('ParasolSet', 'awnR'),):
        k = kit(pal).begin()
        k.bx(-0.38, 0.38, -0.38, 0.38, 0.7, 0.74, 'marble')
        for (a, b) in ((-0.32, -0.32), (0.32, -0.32), (-0.32, 0.32), (0.32, 0.32)):
            k.bxc(a - 0.025, a + 0.025, b - 0.025, b + 0.025, 0.0, 0.7, 'iron', cull='tb', ink=False)
        k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 0.74)
        for (x, y, f) in ((0, -0.62, 0), (0, 0.62, 180), (-0.62, 0, -90), (0.62, 0, 90)):
            chair(k, x, y, f)
        k.lathe(0.12, -0.1, 0.743, [(0.06, 0.0), (0.06, 0.01), (0.0, 0.01)], 'white', seg=6, ink=False)
        k.lathe(-0.15, 0.12, 0.743, [(0.025, 0.0), (0.025, 0.22), (0.0, 0.22)], 'bottle', seg=5, ink=False)
        parasol(k, 0, 0, r=1.35, h=2.45, v=v)
        done(k, name, ao)
    # planter [2, 1]: a wooden box of clipped box hedge
    k = kit(pal).begin()
    k.bx(-0.95, 0.95, -0.35, 0.35, 0.0, 0.55, 'woodD')
    k.qy(-0.9, 0.9, 0.08, 0.5, -0.354, -1, 'wood')
    k.qy(-0.9, 0.9, 0.08, 0.5, 0.354, 1, 'wood')
    k.bx(-0.9, 0.9, -0.3, 0.3, 0.55, 1.05, 'leaf')
    k.qz(-0.86, 0.86, -0.26, 0.26, 1.054, 1, 'leafL')
    k.col(-0.95, 0.95, -0.35, 0.35, 0.0, 1.05)
    done(k, 'Planter', ao)
    # lemon tree in a terracotta pot (1 cell)
    k = kit(pal).begin()
    k.lathe(0, 0, 0.0, [(0.24, 0.0), (0.32, 0.52), (0.36, 0.56), (0.36, 0.62), (0.0, 0.6)], 'terra', seg=6)
    k.disc(0, 0, 0.623, 0.3, 'soil', n=8)
    k.cyl(0, 0, 0.627, 0.04, 0.03, 0.75, 'wood', seg=5, ink=False)
    k.sph(0, 0, 1.62, 0.52, 'leaf', seg=(5, 4))
    for i in range(4):
        a = i * 1.57 + 0.4
        k.hullp([(math.cos(a) * 0.5 + dx, math.sin(a) * 0.5 + dy, 1.45 + 0.25 * (i % 3) / 2 + dz) for (dx, dy, dz) in ((0.05, 0, 0), (-0.04, 0.03, 0), (0, -0.04, 0.03), (0, 0, -0.05))], 'lemon', ink=False)
    k.col(-0.36, 0.36, -0.36, 0.36, 0.0, 1.2)
    done(k, 'LemonPot', ao)
    # an urn on a pedestal with trailing flowers (1 cell)
    k = kit(pal).begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.85, 'stone')
    k.bxc(-0.34, 0.34, -0.34, 0.34, 0.85, 0.93, 'stone')
    k.lathe(0, 0, 0.93, [(0.14, 0.0), (0.12, 0.1), (0.32, 0.38), (0.36, 0.5), (0.3, 0.5), (0.0, 0.48)], 'stoneD', seg=8)
    flowers(k, rnd, -0.26, 0.26, -0.26, 0.26, 1.43, 6, ('fRed', 'fPink', 'white', 'fRed'), trail=0.45, yt=-0.32)
    k.col(-0.34, 0.34, -0.34, 0.34, 0.0, 1.43)
    done(k, 'Urn', ao)
    # menu board (1 cell): an easel chalkboard
    k = kit(pal).begin()
    for s in (-1, 1):
        k.beam((-0.28, s * 0.22, 0.0), (-0.24, s * 0.02, 1.1), 0.04, 'wood')
        k.beam((0.28, s * 0.22, 0.0), (0.24, s * 0.02, 1.1), 0.04, 'wood')
    k.bxr(0, -0.12, 0.62, 0.52, 0.03, 0.7, 'iron', rot=(-10, 0, 0))
    k.push(0, -0.14, 0, 0.62)
    k.m.parent = k.m.parent @ Euler((math.radians(-10), 0, 0)).to_matrix().to_4x4()
    text(k, 'MENU', 0, -0.02, 0.18, 0.1, 'white', font='script')
    for i in range(3):
        k.qy(-0.18, 0.12 - 0.06 * i, -0.15 + i * 0.09, -0.13 + i * 0.09, -0.021, -1, 'white')
    k.pop()
    k.col(-0.3, 0.3, -0.25, 0.25, 0.0, 1.1)
    done(k, 'Menu', ao)
    # stone bench [2, 1]
    k = kit(pal).begin()
    k.bx(-0.95, 0.95, -0.24, 0.24, 0.4, 0.5, 'stone', bevel=True)
    for x in (-0.7, 0.7):
        k.bx(x - 0.12, x + 0.12, -0.2, 0.2, 0.0, 0.4, 'stoneD')
    k.col(-0.95, 0.95, -0.24, 0.24, 0.0, 0.5)
    done(k, 'Bench', ao)
    # the well-head (vera da pozzo) [2, 2]: a carved drum on a stepped base, the iron frame and its pulley
    k = kit(pal).begin()
    k.lathe(0, 0, 0.0, [(0.95, 0.0), (0.95, 0.12), (0.0, 0.12)], 'stoneD', seg=8, a0=math.pi / 8)
    k.lathe(0, 0, 0.12, [(0.62, 0.0), (0.66, 0.1), (0.58, 0.18), (0.58, 0.78), (0.68, 0.86), (0.68, 0.96), (0.42, 0.96), (0.42, 0.12)], 'stone', seg=8, closed=True)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        ca, sa = math.cos(a), math.sin(a)
        r = 0.58 * math.cos(math.pi / 8) + 0.005
        k.poly([(ca * r - sa * 0.14, sa * r + ca * 0.14, 0.38), (ca * r + sa * 0.14, sa * r - ca * 0.14, 0.38),
                (ca * r + sa * 0.14, sa * r - ca * 0.14, 0.62), (ca * r - sa * 0.14, sa * r + ca * 0.14, 0.62)], 'marbleR' if i % 2 else 'stoneD', (ca, sa, 0))
    k.lathe(0, 0, 0.3, [(0.42, 0.0), (0.0, 0.0)], 'boat', seg=8, ink=False)
    for s in (-1, 1):
        k.bxc(s * 0.62 - 0.03, s * 0.62 + 0.03, -0.03, 0.03, 0.96, 2.0, 'iron', cull='b')
    k.beam((-0.62, 0, 2.0), (-0.3, 0, 2.25), 0.038, 'iron')
    k.beam((0.62, 0, 2.0), (0.3, 0, 2.25), 0.038, 'iron')
    k.beam((-0.3, 0, 2.25), (0.3, 0, 2.25), 0.05, 'iron')
    k.cyl(0, -0.03, 2.08, 0.1, 0.1, 0.06, 'iron', seg=8, rot=(-90, 0, 0))
    k.col(-0.68, 0.68, -0.68, 0.68, 0.0, 0.96)
    done(k, 'Well', ao)
    # lamp post (1 cell): a cast-iron column with a lantern; its glow companion
    k = kit(pal).begin()
    k.lathe(0, 0, 0.0, [(0.16, 0.0), (0.16, 0.12), (0.07, 0.4), (0.055, 2.7), (0.09, 2.85), (0.0, 2.85)], 'iron', seg=6)
    k.cyl(0, 0, 2.85, 0.1, 0.16, 0.44, 'lamp', seg=6, ink=False)
    for i in range(3):
        a = i * math.pi * 2 / 3
        k.beam((math.cos(a) * 0.1, math.sin(a) * 0.1, 2.85), (math.cos(a) * 0.165, math.sin(a) * 0.165, 3.29), 0.025, 'iron', ink=False)
    k.cyl(0, 0, 3.29, 0.21, 0.04, 0.16, 'iron', seg=6)
    k.col(-0.14, 0.14, -0.14, 0.14, 0.0, 2.8)
    done(k, 'LampPost', ao)
    k = kit(pal).begin()
    k.cyl(0, 0, 2.86, 0.12, 0.18, 0.42, 'lampW', seg=6, ink=False)
    done(k, 'LampPost_Glow', False)
    # crates (1 cell; also the weapon stand) and barrels (1 cell)
    k = kit(pal).begin()
    for (x, y, z, s, c) in ((-0.18, -0.12, 0.0, 0.5, 'wood'), (0.22, 0.16, 0.0, 0.46, 'woodD'), (-0.12, -0.08, 0.5, 0.44, 'wood')):
        k.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z, z + s, c)
        for yy in (y - s / 2 - 0.006, y + s / 2 + 0.006):
            k.qy(x - s / 2 + 0.02, x + s / 2 - 0.02, z + s * 0.4, z + s * 0.6, yy, -1 if yy < y else 1, 'woodD' if c == 'wood' else 'wood')
    k.col(-0.43, 0.45, -0.37, 0.39, 0.0, 0.94)
    done(k, 'Crates', ao)
    k = kit(pal).begin()
    for (x, y, dz) in ((-0.23, -0.17, 0.0), (0.23, 0.17, 0.012)):
        k.lathe(x, y, 0.0, [(0.21, 0.0), (0.255, 0.38), (0.21, 0.76), (0.0, 0.76)], 'wood', seg=7)
        k.lathe(x, y, 0.6 + dz, [(0.244, 0.0), (0.234, 0.07), (0.0, 0.07)], 'iron', seg=7, ink=False, caps=False)
    k.col(-0.49, 0.49, -0.43, 0.43, 0.0, 0.76)
    done(k, 'Barrels', ao)
    # the hand cart [2, 3]: two big wheels, a plank bed with crates of lemons and oranges
    k = kit(pal).begin()
    k.bx(-0.7, 0.7, -1.0, 1.0, 0.55, 0.65, 'wood')
    for s in (-1, 1):
        k.bxc(s * 0.7 - 0.04, s * 0.7 + 0.04, -1.0, 1.0, 0.65, 0.9, 'woodD', cull='')
        k.cyl(s * 0.78, 0.25, 0.42, 0.42, 0.42, 0.08, 'woodD', seg=10, rot=(0, 90, 0))
        k.cyl(s * 0.79 + (0.05 if s > 0 else -0.05), 0.25, 0.42, 0.1, 0.1, 0.04, 'iron', seg=6, rot=(0, 90, 0), ink=False)
        k.beam((s * 0.6, -1.0, 0.6), (s * 0.5, -1.65, 0.75), 0.06, 'wood')
    k.bxc(-0.2, 0.2, -1.0, -0.9, 0.0, 0.55, 'woodD', cull='')
    for (cx, cy, c) in ((-0.32, -0.5, 'lemon'), (0.32, -0.5, 'fOrange'), (-0.32, 0.4, 'fOrange'), (0.32, 0.4, 'lemon')):
        k.bx(cx - 0.3, cx + 0.3, cy - 0.38, cy + 0.38, 0.65, 0.9, 'wood')
        k.hullp([(cx - 0.26, cy - 0.33, 0.9), (cx + 0.26, cy - 0.33, 0.9), (cx + 0.26, cy + 0.33, 0.9), (cx - 0.26, cy + 0.33, 0.9), (cx - 0.08, cy - 0.1, 1.02), (cx + 0.1, cy + 0.12, 1.0)], c, ink=False)
    k.col(-0.82, 0.82, -1.0, 1.0, 0.0, 1.0)
    done(k, 'HandCart', ao)
    # the kiosk [3, 3]: a little green wooden kiosk selling masks and postcards (front -Y)
    k = kit(pal).begin()
    k.bx(-1.3, 1.3, -1.3, 1.3, 0.0, 0.9, 'shut')
    k.bxc(-1.36, 1.36, -1.36, 1.36, 0.9, 0.96, 'wood', cull='')
    for (x, y) in ((-1.25, -1.25), (1.25, -1.25), (1.25, 1.25), (-1.25, 1.25)):
        k.bxc(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.96, 2.3, 'shutD', cull='tb')
    k.bx(-1.3, 1.3, 0.9, 1.3, 0.96, 2.3, 'shut')
    k.hullp([(-1.6, -1.6, 2.3), (1.6, -1.6, 2.3), (1.6, 1.6, 2.3), (-1.6, 1.6, 2.3), (0, 0, 3.1)], 'shut')
    k.cyl(0, 0, 3.05, 0.08, 0.02, 0.3, 'gold', seg=6, ink=False)
    k.qy(-1.2, 1.2, 2.1, 2.3, -1.304, -1, 'canvas')
    text(k, 'MASCHERE E CARTOLINE', 0, -1.31, 2.13, 0.14, 'shutD', font='display', maxw=2.3)
    for i, c in enumerate(('gold', 'white', 'fRed', 'fPurp', 'white', 'gold', 'fPink')):
        mx = -1.05 + i * 0.35
        k.hullp([(mx - 0.13, 1.28 - 0.0, 1.6), (mx + 0.13, 1.28, 1.6), (mx + 0.1, 1.28, 1.85), (mx - 0.1, 1.28, 1.85), (mx, 1.22, 1.72)], c, ink=False)
        k.qy(mx - 0.07, mx - 0.02, 1.7, 1.74, 1.215, -1, 'iron')
        k.qy(mx + 0.02, mx + 0.07, 1.7, 1.74, 1.215, -1, 'iron')
    for i in range(6):
        px = -1.1 + i * 0.42
        k.qy(px, px + 0.3, 0.3, 0.7, -1.304, -1, ('white', 'glassL', 'lemon', 'fPink', 'white', 'glassL')[i])
    k.col(-1.36, 1.36, -1.36, 1.36, 0.0, 2.3)
    done(k, 'Kiosk', ao)
    # the flower stall [3, 2]: a cart of buckets of flowers under a canvas (front -Y)
    k = kit(pal).begin()
    k.bx(-1.4, 1.4, -0.8, 0.8, 0.0, 0.75, 'wood')
    for (x0, x1, y0, y1, z, c) in ((-1.3, 1.3, -0.7, -0.05, 0.75, 'woodD'), (-1.3, 1.3, 0.05, 0.7, 1.05, 'woodD')):
        k.bx(x0, x1, y0, y1, z, z + 0.06, c)
    k.bxc(-1.3, 1.3, 0.05, 0.7, 0.75, 1.05, 'wood', cull='t')
    cols = ['fRed', 'fPink', 'white', 'fPurp', 'lemon', 'fOrange']
    for row, (y, z) in enumerate(((-0.38, 0.81), (0.38, 1.11))):
        for i in range(5):
            bx = -1.05 + i * 0.52
            k.lathe(bx, y, z, [(0.16, 0.0), (0.2, 0.3), (0.0, 0.3)], 'chrome', seg=6)
            flowers(k, rnd, bx - 0.18, bx + 0.18, y - 0.18, y + 0.18, z + 0.3, 5, (cols[(i + row * 2) % 6], cols[(i + row * 2) % 6], 'leafL'))
    for x in (-1.35, 1.35):
        k.bxc(x - 0.04, x + 0.04, 0.72, 0.8, 0.75, 2.3, 'woodD', cull='tb')
        k.bxc(x - 0.04, x + 0.04, -0.8, -0.72, 0.75, 2.1, 'woodD', cull='tb')
    k.bxr(0, 0.0, 2.2, 3.0, 1.75, 0.04, 'canvas', rot=(6.5, 0, 0))
    k.col(-1.4, 1.4, -0.8, 0.8, 0.0, 1.4)
    done(k, 'FlowerStall', ao)
    # market stalls [3, 2]: a trestle table of produce under a striped awning (front -Y)
    for name, goods, aw in (('Stall', ('lemon', 'fOrange', 'fRed', 'leafL'), 'awnR'),):
        k = kit(pal).begin()
        k.bx(-1.4, 1.4, -0.7, 0.7, 0.72, 0.8, 'wood')
        for (x, y) in ((-1.25, -0.55), (1.25, -0.55), (1.25, 0.55), (-1.25, 0.55)):
            k.bxc(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.72, 'woodD', cull='tb')
        k.qy(-1.4, 1.4, 0.12, 0.7, -0.704, -1, 'canvas')
        k.qy(-1.4, 1.4, 0.12, 0.7, 0.704, 1, 'canvas')
        for i, c in enumerate(goods):
            cx = -1.0 + i * 0.66
            k.bx(cx - 0.3, cx + 0.3, -0.5, 0.5, 0.8, 0.98, 'wood')
            k.hullp([(cx - 0.26, -0.45, 0.98), (cx + 0.26, -0.45, 0.98), (cx + 0.26, 0.45, 0.98), (cx - 0.26, 0.45, 0.98), (cx - 0.1, -0.15, 1.1), (cx + 0.08, 0.2, 1.09)], c, ink=False)
        for x in (-1.36, 1.36):
            k.bxc(x - 0.03, x + 0.03, 0.62, 0.68, 0.8, 2.3, 'woodD', cull='tb')
        awning(k, -1.5, 1.5, 0.66, 2.3, 1.45, 'canvas', aw)
        k.col(-1.4, 1.4, -0.7, 0.7, 0.0, 1.05)
        done(k, name, ao)
    # paving: cobbles (1 cell, three tones in a running bond) and the white Istrian bands
    for name, off in (('Cobble_A', 0.0), ('Cobble_B', 1.0)):
        k = kit(pal).begin()
        for (a, b, y0, y1, c) in ((-0.47, 0.13, -0.47, -0.03, 'cobble'), (0.17, 0.47, -0.47, -0.03, 'pave'), (-0.47, 0.47, 0.03, 0.47, 'paveD')):
            if off:
                a, b = -b, -a
            k.qz(a, b, y0, y1, 0.008, 1, c if not off else {'cobble': 'pave', 'pave': 'paveD', 'paveD': 'cobble'}[c])
        done(k, name, False)
    k = kit(pal).begin()
    k.qz(-0.5, 0.5, -0.2, 0.2, 0.008, 1, 'stone')
    done(k, 'Band', False)
    k = kit(pal).begin()
    k.qz(-0.2, 0.2, -0.2, 0.2, 0.008, 1, 'stone')
    done(k, 'BandX', False)
