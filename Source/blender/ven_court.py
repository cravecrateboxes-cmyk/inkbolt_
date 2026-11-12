"""INKBOLT kit-venetian zone 2, the mansion's courtyard (and the rails both zones share): the balustrade links (the
cloister's upper walk, the campo's roof terraces), the cloister columns and arches, the grand staircase (landmark),
the service stairs, the garden fountain, parterres, box hedges (links), cypresses in pots, the roof loggia on the
cloister, a stone table with benches, the boat under repair on its trestles, gravel, the moored boat of the backdrop.
Conventions: ven_base.py."""
import math
import random

from mathutils import Euler

from ven_base import *  # noqa: F401,F403
from ven_base import (kit, done, arch_curve, flowers, baluster, steps, wall_lantern)

ARCH_SPRING = 2.55     # cloister columns: the abacus top
COL_STEP = 3           # columns stand every 3 m round both rings of the cloister


# ================================================================ balustrade links (along Blender Y)
def build_rails(pal, ao):
    """BalFull / BalHalf / BalPost: a stone balustrade 1.0 m high on a plinth, modelled along Blender Y (the half
    module runs from the origin toward -Y); collision a thin box on the cell's centre line"""
    def rail(k, y0, y1, n):
        k.bxc(-0.09, 0.09, y0, y1, 0.0, 0.14, 'stone', cull='bfk', ink=False)
        k.bxc(-0.1, 0.1, y0, y1, 0.9, 1.0, 'stone', cull='fk', ink=False)
        for i in range(n):
            yy = y0 + (y1 - y0) * (i + 0.5) / n
            baluster(k, 0.0, yy, 0.14, 0.76, 'stoneD', r=0.055)
    k = kit(pal).begin()
    rail(k, -0.5, 0.5, 2)
    k.col(-0.1, 0.1, -0.5, 0.5, 0.0, 1.0)
    done(k, 'BalFull', ao)
    k = kit(pal).begin()
    rail(k, -0.5, -0.1, 1)
    k.col(-0.1, 0.1, -0.5, 0.0, 0.0, 1.0)
    done(k, 'BalHalf', ao)
    k = kit(pal).begin()
    k.bxc(-0.13, 0.13, -0.13, 0.13, 0.0, 1.06, 'stone', cull='b')
    k.lathe(0, 0, 1.06, [(0.09, 0.0), (0.12, 0.1), (0.0, 0.16)], 'stone', seg=6)
    k.col(-0.13, 0.13, -0.13, 0.13, 0.0, 1.06)
    done(k, 'BalPost', ao)


# ================================================================ box hedge links (along Blender Y)
def build_hedges(pal, ao):
    def hedge(k, y0, y1):
        k.bxc(-0.32, 0.32, y0, y1, 0.0, 0.9, 'leaf', cull='bfk')
        k.qz(-0.28, 0.28, y0, y1, 0.904, 1, 'leafL')
    k = kit(pal).begin()
    hedge(k, -0.5, 0.5)
    k.col(-0.32, 0.32, -0.5, 0.5, 0.0, 0.9)
    done(k, 'HedgeFull', ao)
    k = kit(pal).begin()
    hedge(k, -0.5, 0.0)
    k.col(-0.32, 0.32, -0.5, 0.0, 0.0, 0.9)
    done(k, 'HedgeHalf', ao)
    k = kit(pal).begin()
    k.lathe(0, 0, 0.0, [(0.32, 0.0), (0.34, 0.5), (0.3, 0.86), (0.0, 0.96)], 'leaf', seg=8, a0=math.pi / 8)
    k.col(-0.32, 0.32, -0.32, 0.32, 0.0, 0.9)
    done(k, 'HedgePost', ao)


# ================================================================ the cloister: columns and arches
def build_cloister(pal, ao):
    """Column (1 cell): an Istrian column with a Venetian basket capital and abacus (top 2.55 m). Arch [2, 1]: the
    arch between two columns 3 m apart (x -1.5..1.5, centre to centre), a round arch in rose stucco with a white
    archivolt, up to the underside of the upper walk's deck (DECK - 0.3); no collision (above head height)."""
    k = kit(pal).begin()
    k.bxc(-0.27, 0.27, -0.27, 0.27, 0.0, 0.16, 'stone', cull='b')
    k.lathe(0, 0, 0.16, [(0.15, 0.0), (0.15, 1.95), (0.18, 2.02)], 'stone', seg=6, caps=False)
    k.hullp([(-0.17, -0.17, 2.02), (0.17, -0.17, 2.02), (0.17, 0.17, 2.02), (-0.17, 0.17, 2.02),
             (-0.26, -0.26, 2.4), (0.26, -0.26, 2.4), (0.26, 0.26, 2.4), (-0.26, 0.26, 2.4)], 'stone')
    k.bxc(-0.28, 0.28, -0.28, 0.28, 2.4, ARCH_SPRING, 'stone', cull='t')
    k.col(-0.2, 0.2, -0.2, 0.2, 0.0, ARCH_SPRING)
    done(k, 'Column', ao)
    k = kit(pal).begin()
    top = DECK - 0.3
    cur = arch_curve(-1.22, 1.22, ARCH_SPRING, 'round', 4)
    pts = [(-1.5, ARCH_SPRING + 0.004), (-1.22, ARCH_SPRING + 0.004)] + cur[1:-1] + [(1.22, ARCH_SPRING + 0.004), (1.5, ARCH_SPRING + 0.004), (1.5, top), (-1.5, top)]
    k.prism_xz(pts, -0.2, 0.2, 'rose', cull='lrtb', colors=lambda n: 'roseD' if n.z < -0.2 else 'rose')
    for f in (-1, 1):
        yf = f * 0.204
        for (pa, pb) in zip(cur, cur[1:]):
            def out(p):
                dx, dz = p[0], p[1] - ARCH_SPRING
                L = math.hypot(dx, dz) or 1.0
                return (p[0] + dx / L * 0.14, p[1] + dz / L * 0.14)
            qa, qb = out(pa), out(pb)
            k.poly([(pa[0], yf, pa[1]), (qa[0], yf, qa[1]), (qb[0], yf, qb[1]), (pb[0], yf, pb[1])], 'stone', (0, f, 0))
        k.poly([(-1.5, yf + f * 0.004, top - 0.12), (1.5, yf + f * 0.004, top - 0.12), (1.5, yf + f * 0.004, top), (-1.5, yf + f * 0.004, top)], 'stone', (0, f, 0))
    done(k, 'Arch', ao)


# ================================================================ the grand staircase (landmark) [8, 8]
def build_grand_stair(pal, ao):
    """Footprint x -4..4, y -4..4, rising toward +Y to the cloister's upper walk (DECK): a 5 m wide marble stair in
    two flights of 12 treads with a landing between them (2.16 m), a red runner up the middle, massive side walls
    (x +-2.5..4) whose tops follow the flights carrying a marble balustrade, newel piers with gilt lanterns at the
    foot and urns of flowers on the landing."""
    rnd = random.Random(41)
    k = kit(pal).begin()
    W0, W1 = -2.5, 2.5
    y0 = -4.0
    ya = steps(k, W0, W1, y0, 12, c='marble', nose='stoneD', sides='lr')
    zl = 12 * RISE
    k.bxc(W0, W1, ya, ya + 2.0, 0.0, zl, 'marble', cull='bklr')
    k.wcol(W0, W1, ya, ya + 2.0, 0.0, zl)
    yb = steps(k, W0, W1, ya + 2.0, 12, z0=zl, c='marble', nose='stoneD', sides='lr')
    # the runner: flat red bands on the treads and the landing
    for i in range(12):
        for (yy, z0) in ((y0 + i * TREAD, 0.0), (ya + 2.0 + i * TREAD, zl)):
            za = z0 + (i + 1) * RISE
            k.qz(-0.8, 0.8, yy + 0.02, yy + TREAD, za + 0.004, 1, 'awnR')
    k.qz(-0.8, 0.8, ya, ya + 2.0, zl + 0.004, 1, 'awnR')
    k.qz(-0.9, -0.82, ya + 0.1, ya + 1.9, zl + 0.006, 1, 'gold')
    k.qz(0.82, 0.9, ya + 0.1, ya + 1.9, zl + 0.006, 1, 'gold')
    # the side walls: profile in (y, z) along the flights, extruded across x; arched niches painted on the outside
    prof = [(y0, 0.0), (yb, 0.0), (yb, DECK + 0.2), (ya + 2.0, zl + 0.2), (ya, zl + 0.2), (y0 + 0.4, 0.45), (y0, 0.45)]
    for (xa, xb) in ((-4.0, W0), (W1, 4.0)):
        k.push(0, 0, 90)
        k.prism_xz([(py, pz) for (py, pz) in prof], -xb, -xa, 'stone', colors=lambda n: 'marble' if n.z > 0.5 else 'stone')
        k.pop()
        xo = xa if xa < 0 else xb
        s = -1 if xa < 0 else 1
        for (c0, c1, h) in ((y0 + 1.0, y0 + 2.4, 0.25), (ya + 0.4, ya + 1.6, 0.6), (ya + 2.6, ya + 4.0, 1.2)):
            cur = arch_curve(c0, c1, h + 1.0, 'round', 3)
            pp = [(c0, h), (c1, h)] + list(reversed(cur))[1:-1]
            k.poly([(xo + s * 0.004, py, pz) for (py, pz) in (pp if s > 0 else list(reversed(pp)))], 'stoneD', (s, 0, 0))
        k.col(min(xa, xb), max(xa, xb), y0, y0 + 0.4, 0.0, 0.45 + 1.0)
        for i in range(3):
            c0 = y0 + 0.4 + i * (ya - y0 - 0.4) / 3
            c1 = y0 + 0.4 + (i + 1) * (ya - y0 - 0.4) / 3
            k.col(min(xa, xb), max(xa, xb), c0, c1, 0.0, 0.45 + (c1 - y0 - 0.4) / (ya - y0 - 0.4) * (zl - 0.25) + 1.0)
        k.col(min(xa, xb), max(xa, xb), ya, ya + 2.0, 0.0, zl + 1.2)
        for i in range(3):
            c0 = ya + 2.0 + i * (yb - ya - 2.0) / 3
            c1 = ya + 2.0 + (i + 1) * (yb - ya - 2.0) / 3
            k.col(min(xa, xb), max(xa, xb), c0, c1, 0.0, zl + 0.2 + (c1 - ya - 2.0) / (yb - ya - 2.0) * (DECK - zl) + 1.0)
        # the balustrade on the wall top: balusters up the slopes and along the landing, a handrail beam
        xm = (xa + xb) / 2
        for si, (p0, p1) in enumerate((((y0 + 0.4, 0.45), (ya, zl + 0.2)), ((ya, zl + 0.2), (ya + 2.0, zl + 0.2)), ((ya + 2.0, zl + 0.2), (yb, DECK + 0.2)))):
            L = p1[0] - p0[0]
            n = max(2, int(L / 0.45))
            for i in range(n):
                t = (i + 0.5) / n
                baluster(k, xm, p0[0] + L * t, p0[1] + (p1[1] - p0[1]) * t, 0.72, 'marble', r=0.07)
            k.beam((xm, p0[0], p0[1] + 0.78), (xm, p1[0], p1[1] + 0.78), 0.2 if si != 1 else 0.186, 'marble')
        # newel piers with gilt lanterns at the foot, urns on the landing
        k.bxc(xm - 0.4, xm + 0.4, y0 - 0.05, y0 + 0.8, 0.0, 1.6, 'marble')
        k.lathe(xm, y0 + 0.4, 1.6, [(0.08, 0.0), (0.06, 1.2), (0.12, 1.25)], 'bronze', seg=6, caps=False)
        k.cyl(xm, y0 + 0.4, 2.85, 0.12, 0.17, 0.42, 'lamp', seg=6, ink=False)
        k.cyl(xm, y0 + 0.4, 3.27, 0.22, 0.03, 0.18, 'gold', seg=6)
        k.lathe(xm, ya + 1.0, zl + 0.98, [(0.12, 0.0), (0.3, 0.32), (0.34, 0.44), (0.0, 0.42)], 'stoneD', seg=8)
        flowers(k, rnd, xm - 0.24, xm + 0.24, ya + 0.76, ya + 1.24, zl + 1.42, 6, ('fRed', 'fPink', 'white'), trail=0.5, yt=ya + 0.7)
        k.col(xm - 0.4, xm + 0.4, y0 - 0.05, y0 + 0.8, 0.0, 1.6)
    done(k, 'Landmark_Stair', ao)
    k = kit(pal).begin()
    for xm in (-3.25, 3.25):
        k.cyl(xm, -3.6, 2.9, 0.15, 0.2, 0.4, 'lampW', seg=6, ink=False)
    done(k, 'Landmark_Stair_Glow', False)


# ================================================================ service stairs [2, 6]
def build_service_stair(pal, ao):
    """24 treads rising +Y from y = -3 to the upper walk (DECK): stone treads between brick side walls whose tops
    follow the stair, an iron handrail on each"""
    k = kit(pal).begin()
    W0, W1 = -0.72, 0.72
    ye = steps(k, W0, W1, -3.0, 24, c='stone', sides='lr')
    for (xa, xb) in ((-1.0, W0), (W1, 1.0)):
        k.push(0, 0, 90)
        k.prism_xz([(-3.0, 0.0), (ye, 0.0), (ye, DECK + 0.1), (-3.0 + TREAD, RISE + 0.1)], -xb, -xa, 'brick', colors=lambda n: 'stone' if n.z > 0.5 else 'brick')
        k.pop()
        xm = (xa + xb) / 2
        k.beam((xm, -2.9, 1.0), (xm, ye, DECK + 1.0), 0.06, 'iron')
        for i in range(1, 6):
            yy = -3.0 + i * 1.0
            hz = (yy + 3.0) / TREAD * RISE
            k.bxc(xm - 0.02, xm + 0.02, yy - 0.02, yy + 0.02, hz + 0.1, hz + 1.0, 'iron', cull='tb', ink=False)
        for i in range(6):
            c0, c1 = -3.0 + i * 1.0, -2.0 + i * 1.0
            k.col(min(xa, xb), max(xa, xb), c0, c1, 0.0, (c1 + 3.0) / TREAD * RISE + 1.05)
    done(k, 'Stair', ao)


# ================================================================ the garden fountain [6, 6]
def build_fountain2(pal, ao):
    """An octagonal marble basin (r 2.5, rim 0.7 m) brim full, a fluted baluster column with a shell-less bowl and a
    pine-cone finial whose four jets fall back into the basin"""
    k = kit(pal).begin()
    o = math.pi / 8
    k.lathe(0, 0, 0.0, [(2.2, 0.0), (2.5, 0.0), (2.5, 0.58), (2.6, 0.6), (2.6, 0.7), (2.1, 0.7), (2.1, 0.62), (2.2, 0.58)], 'marble', seg=8, closed=True, a0=o)
    k.disc(0, 0, 0.62, 2.18 / math.cos(o) * math.cos(o), 'water', n=8, a0=o)
    for r in (1.1, 1.7):
        for i in range(12):
            if i % 3 == 2:
                continue
            a0, a1 = i * math.pi / 6, (i + 1) * math.pi / 6
            k.poly([(math.cos(a0) * r, math.sin(a0) * r, 0.624), (math.cos(a1) * r, math.sin(a1) * r, 0.624),
                    (math.cos(a1) * (r + 0.07), math.sin(a1) * (r + 0.07), 0.624), (math.cos(a0) * (r + 0.07), math.sin(a0) * (r + 0.07), 0.624)], 'waterL', (0, 0, 1))
    k.lathe(0, 0, 0.6, [(0.55, 0.0), (0.45, 0.2), (0.22, 0.4), (0.3, 1.1), (0.16, 1.6), (0.2, 1.7)], 'marble', seg=8, caps=False)
    k.lathe(0, 0, 2.3, [(0.2, 0.0), (1.0, 0.25), (1.08, 0.36), (0.95, 0.36), (0.0, 0.3)], 'marble', seg=10)
    k.disc(0, 0, 2.64, 0.95, 'water', n=10)
    k.lathe(0, 0, 2.66, [(0.12, 0.0), (0.2, 0.2), (0.16, 0.45), (0.0, 0.6)], 'bronze', seg=6)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        pts = [(ca * 0.12, sa * 0.12, 3.05)]
        for j in range(1, 6):
            t = j / 5
            d = 0.12 + t * 1.6
            pts.append((ca * d, sa * d, 3.05 + 0.5 * t - 2.95 * t * t))
        for (p, q) in zip(pts, pts[1:]):
            k.beam(p, q, 0.06, 'waterL', ink=False)
    k.lathe(0, 0, 1.75, [(1.12, 0.0), (1.1, 0.6), (1.04, 0.6), (1.06, 0.0)], 'waterL', seg=10, closed=True, ink=False)
    k.col(-2.6, 2.6, -2.6, 2.6, 0.0, 0.7)
    k.col(-2.0, 2.0, -2.0, 2.0, 0.0, 2.2)
    done(k, 'Fountain2', ao)


# ================================================================ garden pieces
def build_garden(pal, ao):
    rnd = random.Random(51)
    # parterre [6, 4]: a box-hedged bed of roses round a clipped cone
    k = kit(pal).begin()
    k.bx(-3.0, 3.0, -2.0, 2.0, 0.0, 0.45, 'leaf')
    k.qz(-2.75, 2.75, -1.75, 1.75, 0.454, 1, 'soil')
    k.qz(-2.75, 2.75, -0.1, 0.1, 0.458, 1, 'gravel')
    for (cx, cy) in ((-1.5, -0.95), (1.5, -0.95), (-1.5, 0.95), (1.5, 0.95)):
        flowers(k, rnd, cx - 1.0, cx + 1.0, cy - 0.55, cy + 0.55, 0.45, 7, ('fRed', 'fPink', 'white', 'fRed', 'fPurp'), s=0.09)
    k.lathe(0, 0, 0.45, [(0.35, 0.0), (0.0, 1.3)], 'leafD', seg=6)
    k.col(-3.0, 3.0, -2.0, 2.0, 0.0, 0.7)
    done(k, 'Parterre', ao)
    # cypress in a pot (1 cell)
    k = kit(pal).begin()
    k.lathe(0, 0, 0.0, [(0.28, 0.0), (0.36, 0.55), (0.4, 0.6), (0.0, 0.58)], 'terra', seg=8)
    k.lathe(0, 0, 0.55, [(0.25, 0.0), (0.32, 0.6), (0.26, 1.8), (0.0, 3.1)], 'cypress', seg=6)
    k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 1.8)
    done(k, 'Cypress', ao)
    # stone table and two benches [3, 2]
    k = kit(pal).begin()
    k.bx(-1.0, 1.0, -0.45, 0.45, 0.72, 0.8, 'stone', bevel=True)
    k.lathe(0, 0, 0.0, [(0.3, 0.0), (0.16, 0.2), (0.18, 0.72)], 'stoneD', seg=6, caps=False)
    for y in (-0.85, 0.85):
        k.bx(-0.9, 0.9, y - 0.17, y + 0.17, 0.4, 0.47, 'stone')
        for x in (-0.6, 0.6):
            k.bxc(x - 0.1, x + 0.1, y - 0.13, y + 0.13, 0.0, 0.4, 'stoneD', cull='t')
    k.col(-1.0, 1.0, -0.45, 0.45, 0.0, 0.8)
    k.col(-0.9, 0.9, -1.02, -0.68, 0.0, 0.47)
    k.col(-0.9, 0.9, 0.68, 1.02, 0.0, 0.47)
    done(k, 'StoneTable', ao)
    # gravel (1 cell, no collision)
    k = kit(pal).begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, 0.008, 1, 'gravel')
    done(k, 'Gravel', False)


# ================================================================ the roof loggia on the cloister [13, 4]
def build_pavilion(pal, ao):
    """Stands on the upper walk (its layer): ten slender columns on the deck's edges (x -6..6 every 3, y +-1.82), an
    entablature, a hipped tiled roof; collision on the columns only"""
    k = kit(pal).begin()
    for x in (-6, -3, 0, 3, 6):
        for y in (-1.82, 1.82):
            k.lathe(x, y, 0.0, [(0.2, 0.0), (0.12, 0.12), (0.11, 2.5), (0.17, 2.6)], 'stone', seg=6, caps=False)
            k.bxc(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 2.6, 2.72, 'stone', cull='t')
            k.col(x - 0.14, x + 0.14, y - 0.14, y + 0.14, 0.0, 2.72)
    k.bxc(-6.3, 6.3, -2.1, 2.1, 2.72, 3.1, 'rose')
    k.qz(-6.0, 6.0, -1.8, 1.8, 2.716, -1, 'plaster')
    k.bxc(-6.45, 6.45, -2.25, 2.25, 3.1, 3.22, 'stone')
    k.hullp([(-6.6, -2.4, 3.22), (6.6, -2.4, 3.22), (6.6, 2.4, 3.22), (-6.6, 2.4, 3.22), (-4.6, 0.0, 4.5), (4.6, 0.0, 4.5)], 'roof')
    for i in range(1, 12):
        x = -6.0 + i * 1.0
        if abs(x) < 4.4:
            k.poly([(x - 0.03, -2.38, 3.235), (x + 0.03, -2.38, 3.235), (x + 0.015, -0.02, 4.49), (x - 0.015, -0.02, 4.49)], 'roofD', (0, -0.73, 0.69))
    done(k, 'Pavilion', ao)


# ================================================================ the boat under repair [3, 11]
def build_gondola(pal, ao):
    """A long black boat (lofted hull, the steel prow comb, the oarlock) on two trestles, a tarp over its middle,
    oars and a paint pot beside it"""
    k = kit(pal).begin()
    L = 10.6
    n = 12
    def half(t):
        return 0.68 * math.sin(math.pi * t) ** 0.6
    def lift(t):
        return 0.95 + 0.9 * (abs(t - 0.5) * 2) ** 3
    rings = []
    for i in range(n + 1):
        t = i / n
        y = -L / 2 + L * t
        w = max(0.04, half(t))
        zt = lift(t)
        rings.append([(-w, y, zt), (w, y, zt), (w * 0.6, y, 0.95 - 0.25 * math.sin(math.pi * t)), (-w * 0.6, y, 0.95 - 0.25 * math.sin(math.pi * t))])
    for i in range(n):
        A, B = rings[i], rings[i + 1]
        k.hullp(A + B, 'boat')
    k.bxr(0, -0.4, 0.98, 1.3, 3.2, 0.04, 'canvas', rot=(0, 0, 0))
    # the prow comb (ferro) and the stern post
    k.push(0, L / 2 - 0.1, 90, 1.7)
    k.prism_xz([(0.0, 0.0), (0.55, 0.0), (0.62, 0.15), (0.6, 0.75), (0.45, 0.9), (0.35, 0.75), (0.1, 0.7), (0.0, 0.3)], -0.02, 0.02, 'chrome')
    k.pop()
    k.bxc(-0.03, 0.03, -L / 2 + 0.15, -L / 2 + 0.25, 1.6, 2.2, 'boat', cull='b')
    k.bxc(0.28, 0.42, 2.2, 2.34, 1.05, 1.75, 'wood', cull='b')
    for y in (-3.0, 3.0):
        for s in (-1, 1):
            k.beam((s * 0.9, y - 0.2, 0.0), (s * 0.25, y, 0.78), 0.08, 'woodD')
            k.beam((s * 0.9, y + 0.2, 0.0), (s * 0.25, y, 0.78), 0.075, 'woodD')
        k.bxc(-0.5, 0.5, y - 0.1, y + 0.1, 0.72, 0.8, 'wood', cull='')
    k.beam((1.2, -4.5, 0.0), (1.3, 0.5, 0.25), 0.07, 'wood')
    k.lathe(-1.1, 4.2, 0.0, [(0.12, 0.0), (0.12, 0.2), (0.0, 0.2)], 'awnR', seg=6)
    k.col(-0.7, 0.7, -L / 2 + 0.4, L / 2 - 0.4, 0.0, 1.5)
    done(k, 'Gondola', ao)
    # the moored boat of the backdrop (seen on the canal): a simpler hull, no trestles
    k = kit(pal).begin()
    for i in range(n):
        A, B = rings[i], rings[i + 1]
        k.hullp([(p[0], p[1], p[2] - 0.95) for p in A + B], 'boat', ink=True)
    k.bxr(0, -0.4, 0.04, 1.2, 2.0, 0.04, 'awnR', rot=(0, 0, 0))
    k.push(0, L / 2 - 0.1, 90, 0.75)
    k.prism_xz([(0.0, 0.0), (0.55, 0.0), (0.62, 0.15), (0.6, 0.75), (0.45, 0.9), (0.35, 0.75), (0.1, 0.7), (0.0, 0.3)], -0.02, 0.02, 'chrome')
    k.pop()
    done(k, 'Backdrop_Boat', False)


def build_court(pal, ao):
    build_rails(pal, ao)
    build_hedges(pal, ao)
    build_cloister(pal, ao)
    build_grand_stair(pal, ao)
    build_service_stair(pal, ao)
    build_fountain2(pal, ao)
    build_garden(pal, ao)
    build_pavilion(pal, ao)
    build_gondola(pal, ao)
