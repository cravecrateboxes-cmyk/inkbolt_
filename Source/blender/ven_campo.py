"""INKBOLT kit-venetian zone 1, the campo: the Fountain of the Four Winds (landmark), the two walk-in cafes (Caffe
Zanetto with its stair to the roof terrace, Pasticceria Brolo), the merchants' loggia with its roof terrace, cafe
tables, parasols, planters, the kiosk, the flower stall, market stalls, the well-head, lamp posts, benches, crates,
barrels, the hand cart, urns, lemon pots, paving. Conventions: ven_base.py."""
import math
import random

from ven_base import *  # noqa: F401,F403
from ven_base import (kit, done, arch_curve, arched_opening, rect_opening, glints, flowers, flower_box, wall_lantern,
                      balustrade_x, baluster, text, steps, wall_parts)
from fr_base import wall


# ================================================================ cafe furniture (shared with the interiors)
def chair(k, x, y, face=0.0, cols=None, z=0.0):
    """a rattan bistro chair facing `face` degrees (0 = toward -Y)"""
    k.push(x, y, face, z)
    k.bx(-0.2, 0.2, -0.2, 0.2, 0.44, 0.49, 'rattan')
    for a in (-0.17, 0.17):
        k.bxc(a - 0.015, a + 0.015, -0.17, 0.2, 0.0, 0.44, 'iron', cull='tbfk', ink=False)
    k.bxc(-0.19, 0.19, 0.16, 0.21, 0.49, 0.9, 'rattan', cull='b')
    k.pop()
    if cols is not None:
        cols.append((x - 0.22, x + 0.22, y - 0.22, y + 0.22, z, z + 0.9))


def bistro_table(k, x, y, cols=None, z=0.0, cups=True, r=0.34):
    """a round marble bistro table on an iron pedestal, with a cup and a saucer"""
    k.lathe(x, y, z, [(0.2, 0.0), (0.04, 0.06), (0.03, 0.7)], 'iron', seg=5, caps=False)
    k.lathe(x, y, z + 0.7, [(r, 0.0), (r, 0.04), (0.0, 0.04)], 'marble', seg=8)
    if cups:
        k.lathe(x + 0.12, y - 0.06, z + 0.743, [(0.03, 0.0), (0.04, 0.06), (0.0, 0.06)], 'white', seg=5, ink=False)
        k.lathe(x - 0.1, y + 0.08, z + 0.743, [(0.025, 0.0), (0.025, 0.2), (0.0, 0.2)], 'bottle', seg=4, ink=False)
    if cols is not None:
        cols.append((x - r, x + r, y - r, y + r, z, z + 0.74))


def parasol(k, x, y, r=1.25, h=2.4, c='canvas', v='awnR', z=0.0, seg=8):
    """a market parasol: pole, canopy, valance"""
    k.cyl(x, y, z + 0.035, 0.03, 0.03, h + 0.115, 'wood', seg=5, ink=False)
    k.lathe(x, y, z + h - 0.35, [(r, 0.0), (0.0, 0.42)], c, seg=seg, a0=math.pi / seg)
    k.lathe(x, y, z + h - 0.47, [(r + 0.02, 0.0), (r + 0.02, 0.12), (r - 0.01, 0.12), (r - 0.01, 0.0)], v, seg=seg, closed=True, a0=math.pi / seg, ink=False)
    k.cyl(x, y, z + h + 0.07, 0.05, 0.02, 0.1, 'wood', seg=5, ink=False)


def awning(k, x0, x1, y, z, depth, c='canvas', s='awnR', n=None):
    """a striped canvas awning on a front (plane at y facing -Y): sloping out and down `depth`, a scalloped valance"""
    drop = depth * 0.45
    ang = math.degrees(math.atan2(drop, depth))
    L = math.hypot(depth, drop)
    k.bxr((x0 + x1) / 2, y - depth / 2, z - drop / 2, x1 - x0, L, 0.04, c, rot=(-ang, 0, 0))
    n = n or max(2, int(round((x1 - x0) / 0.35)))
    w = (x1 - x0) / n
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for i in range(0, n, 2):
        a, b = x0 + i * w, x0 + (i + 1) * w
        p0 = (y + 0.0, z + 0.024)
        p1 = (y - depth, z - drop + 0.024)
        k.poly([(a, p0[0] - 0.0, p0[1] + 0.003), (b, p0[0], p0[1] + 0.003), (b, p1[0], p1[1] + 0.003), (a, p1[0], p1[1] + 0.003)], s, (0, sa, ca))
    yv = y - depth - 0.022
    for i in range(n):
        a, b = x0 + i * w, x0 + (i + 1) * w
        k.poly([(a, yv, z - drop), (b, yv, z - drop), (b, yv, z - drop - 0.18), ((a + b) / 2, yv, z - drop - 0.26), (a, yv, z - drop - 0.18)],
               s if i % 2 == 0 else c, (0, -1, 0))
    for xx in (x0 + 0.05, x1 - 0.05):
        k.beam((xx, y, z - 0.6), (xx, y - depth + 0.05, z - drop - 0.02), 0.025, 'iron', ink=False)


def bottles(k, rnd, x0, x1, y, z, n, s=1.0):
    for i in range(n):
        bx = x0 + (x1 - x0) * (i + 0.5) / n
        c = ('bottle', 'fOrange', 'glassL', 'bottle', 'fRed')[rnd.randrange(5)]
        k.lathe(bx, y, z, [(0.035 * s, 0.0), (0.035 * s, 0.2 * s), (0.0, 0.3 * s)], c, seg=4, ink=False)


def espresso(k, x, y, z):
    """an espresso machine on the counter (front toward -Y)"""
    k.bx(x - 0.32, x + 0.32, y - 0.22, y + 0.2, z, z + 0.42, 'chrome')
    k.qy(x - 0.28, x + 0.28, z + 0.28, z + 0.38, y - 0.224, -1, 'awnR')
    k.lathe(x, y, z + 0.42, [(0.12, 0.0), (0.12, 0.1), (0.06, 0.16), (0.0, 0.18)], 'chrome', seg=6)
    k.lathe(x, y, z + 0.6, [(0.04, 0.0), (0.03, 0.08), (0.0, 0.1)], 'gold', seg=5, ink=False)
    for gx in (x - 0.15, x + 0.15):
        k.bxc(gx - 0.04, gx + 0.04, y - 0.3, y - 0.22, z + 0.18, z + 0.26, 'iron', cull='k', ink=False)


def counter(k, x0, x1, y0, y1, z=0.0, h=1.05, top='marble', body='wood', cols=None):
    k.bx(x0, x1, y0, y1, z, z + h - 0.05, body)
    k.bxc(x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.02, z + h - 0.05, z + h, top, cull='')
    k.qy(x0 + 0.06, x1 - 0.06, z + 0.12, z + h - 0.18, y0 - 0.004, -1, 'woodD')
    if cols is not None:
        cols.append((x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.02, z, z + h))


def shelf_wall(k, rnd, x0, x1, y, z0, z1, rows=3, face=-1, goods='bottles'):
    """wall shelving at plane y (goods toward face * Y): boards and goods"""
    d = 0.28 * face
    k.qy(x0, x1, z0, z1, y, face, 'woodD')
    for i in range(rows):
        zz = z0 + 0.3 + (z1 - z0 - 0.4) * i / max(1, rows - 1)
        k.bxc(x0, x1, y, y + d, zz - 0.03, zz, 'wood', cull='k' if face < 0 else 'f')
        n = int((x1 - x0) / (0.15 if goods == 'bottles' else 0.3))
        for j in range(n):
            gx = x0 + 0.05 + (x1 - x0 - 0.1) * (j + 0.5) / n
            if goods == 'bottles':
                c = ('bottle', 'fOrange', 'glassL', 'bottle', 'fRed', 'gold')[rnd.randrange(6)]
                hh = 0.24 + 0.06 * rnd.random()
                k.poly([(gx - 0.03, y + d * 0.85, zz), (gx + 0.03, y + d * 0.85, zz), (gx + 0.03, y + d * 0.85, zz + hh * 0.7), (gx + 0.01, y + d * 0.85, zz + hh),
                        (gx - 0.01, y + d * 0.85, zz + hh), (gx - 0.03, y + d * 0.85, zz + hh * 0.7)], c, (0, -face, 0))
            else:
                c = ('fOrange', 'lemon', 'fPink', 'white', 'rattan')[rnd.randrange(5)]
                k.bxc(gx - 0.1, gx + 0.1, y + d * 0.2, y + d * 0.8, zz, zz + 0.12 + rnd.random() * 0.1, c, cull='b' + ('k' if face < 0 else 'f'), ink=False)


# ================================================================ Caffe Zanetto (walk-in, roof terrace) [10, 8]
CW, CD = 10.0, 8.0
T = 0.25   # wall thickness
OPEN = -1.6   # Caffe Zanetto: the stairwell opening in the roof runs from here (local y) to the landing


def build_cafe_a(pal, ao):
    """Footprint x -5..5, y -4..4; the front (y = -4) faces the campo (the theme turns it east), the back stands
    against the house behind. Ground floor: arched windows and the door in the front, a side door (+X), the bar
    along the back with the espresso machine and bottle shelves, three tables, the stair up the -X wall rising
    toward +Y to a landing at the back corner (3.6 m), the roof terrace (balustrade, a parasol table, pots) reached
    through the stairwell opening."""
    rnd = random.Random(11)
    k = kit(pal).begin()
    X0, X1, Y0, Y1 = -CW / 2, CW / 2, -CD / 2, CD / 2
    H = TERR - 0.3   # roof slab bottom
    # ---- walls (outside stucco, inside plaster); the front with three arched openings, a side door
    fr_holes = [(-4.2, -2.6, 0.55, 2.4 + 0.8), (-0.8, 0.8, 0.0, 2.3 + 0.8), (2.6, 4.2, 0.55, 2.4 + 0.8)]
    side_holes = [(-1.4, -0.2, 0.0, 2.4)]
    def shell():
        for (a, b, c0, c1) in wall_parts(X0, X1, 0.0, H - 0.05, fr_holes):
            k.box2(a, b, Y0, Y0 + T, c0, c1, lambda f: 'stucco' if f.normal.y < -0.5 else ('plaster' if f.normal.y > 0.5 else 'stuccoD'))
        for (a, b, c0, c1) in wall_parts(Y0 + T, Y1, 0.0, H - 0.05, side_holes):
            k.box2(X1 - T, X1, a, b, c0, c1, lambda f: 'stucco' if f.normal.x > 0.5 else ('plaster' if f.normal.x < -0.5 else 'stuccoD'))
        k.box2(X0, X0 + T, Y0 + T, Y1, 0.0, H - 0.05, lambda f: 'stucco' if f.normal.x < -0.5 else ('plaster' if f.normal.x > 0.5 else 'stuccoD'))
        k.qy(X0 + T, X1 - T, 0.0, H - 0.054, Y1 - 0.06, -1, 'plaster')
    shell()
    for (a, b, c0, c1) in wall_parts(X0, X1, 0.0, 2.4, [(h[0], h[1], h[2], min(h[3], 2.4)) for h in fr_holes]):
        if c1 - c0 > 0.05:
            k.col(a, b, Y0, Y0 + T, c0, TERR)
    k.col(X0, X1, Y0, Y0 + T, 2.4, TERR)
    for (a, b, c0, c1) in wall_parts(Y0 + T, Y1, 0.0, 2.4, side_holes):
        k.col(X1 - T, X1, a, b, 0.0, TERR)
    k.col(X1 - T, X1, side_holes[0][0], side_holes[0][1], 2.4, TERR)
    k.col(X0, X0 + T, Y0 + T, Y1, 0.0, TERR)
    # arches over the openings: spandrels on both faces, frames, glass in the windows, the door open (leaf inside)
    for (a, b, z0, top) in fr_holes:
        zs = top - (b - a) / 2
        for f in (-1, 1):
            yy = Y0 if f < 0 else Y0 + T
            cur = arch_curve(a, b, zs, 'round', 4)
            left = [(a, zs)] + [p for p in cur if p[0] <= (a + b) / 2 + 1e-6]
            right = [p for p in cur if p[0] >= (a + b) / 2 - 1e-6] + [(b, zs)]
            col = 'stucco' if f < 0 else 'plaster'
            k.poly([(px, yy, pz) for (px, pz) in left] + [(a, yy, top)], col, (0, f, 0))
            k.poly([(b, yy, top)] + [(px, yy, pz) for (px, pz) in right], col, (0, f, 0))
            if f < 0:
                for (pa, pb) in zip(cur, cur[1:]):
                    def out(p):
                        dx, dz = p[0] - (a + b) / 2, p[1] - zs
                        L = math.hypot(dx, dz) or 1.0
                        return (p[0] + dx / L * 0.12, p[1] + max(0.0, dz / L) * 0.12)
                    qa, qb = out(pa), out(pb)
                    k.poly([(pa[0], Y0 - 0.006, pa[1]), (qa[0], Y0 - 0.006, qa[1]), (qb[0], Y0 - 0.006, qb[1]), (pb[0], Y0 - 0.006, pb[1])], 'stone', (0, -1, 0))
        cur = arch_curve(a, b, zs, 'round', 4)
        for (pa, pb) in zip(cur, cur[1:]):
            mx, mz = (pa[0] + pb[0]) / 2 - (a + b) / 2, (pa[1] + pb[1]) / 2 - zs
            k.poly([(pa[0], Y0, pa[1]), (pb[0], Y0, pb[1]), (pb[0], Y0 + T, pb[1]), (pa[0], Y0 + T, pa[1])], 'stuccoD', (-mx, 0, -mz))
        if z0 > 0:
            k.qz(a, b, Y0, Y0 + T, z0 + 0.004, 1, 'stone')
            gl = [(a, Y0 + 0.12, z0), (b, Y0 + 0.12, z0)] + [(px, Y0 + 0.12, pz) for (px, pz) in reversed(cur)][1:-1] + [(a, Y0 + 0.12, zs)]
            k.poly(gl, 'glass', (0, -1, 0))
            k.poly(list(reversed([(px, Y0 + 0.124, pz) for (px, _, pz) in gl])), 'glass', (0, 1, 0))
            k.qy(a, b, zs - 0.03, zs + 0.03, Y0 + 0.116, -1, 'wood')
            k.qy((a + b) / 2 - 0.025, (a + b) / 2 + 0.025, z0, zs, Y0 + 0.112, -1, 'wood')
            glints(k, a, b, z0 + 0.2, zs, Y0 + 0.108)
        else:
            k.qz(a, b, Y0, Y0 + T, 0.006, 1, 'stone')
            # the door leaves folded back inside
            for s in (-1, 1):
                xa = a if s < 0 else b
                k.bxc(min(xa, xa - s * 0.05), max(xa, xa - s * 0.05), Y0 + T + 0.01, Y0 + T + 0.76, 0.02, zs - 0.02, 'wood', cull='b')
    # the side door's leaf ajar inside, its frame
    a, b = side_holes[0][0], side_holes[0][1]
    k.bxc(X1 - T - 0.8, X1 - T - 0.05, b - 0.06, b, 0.02, 2.36, 'wood', cull='b')
    k.qz(X1 - T, X1, a, b, 0.006, 1, 'stone')
    # stone courses outside, the roof slab, the terrace floor, the cornice
    for (a, b, c0, c1) in wall_parts(X0, X1, 0.0, 0.45, [(h[0], h[1], h[2], h[3]) for h in fr_holes if h[2] < 0.1]):
        k.bxc(a, b, Y0 - 0.03, Y0, c0, c1, 'stone', cull='bk' + ('l' if a > X0 else '') + ('r' if b < X1 else ''), ink=False)
    sx0_, sx1_ = X0 + T, X0 + T + 1.2
    k.bxc(X0 - 0.12, X1 + 0.12, Y0 - 0.12, OPEN, H - 0.05, TERR, 'stone', cull='')
    k.bxc(sx1_, X1 + 0.12, OPEN, Y1, H - 0.05, TERR, 'stone', cull='kl')
    k.bxc(X0 - 0.12, sx0_, OPEN, Y1, H - 0.05, TERR, 'stone', cull='kr')
    k.qz(sx1_, X1 - T, OPEN, Y1, H - 0.054, -1, 'plaster')
    k.qz(X0 + T, X1 - T, Y0 + T, OPEN, H - 0.054, -1, 'plaster')
    # the stairwell opening in the slab: drawn as the slab's own hole (re-cut below), its rim
    # ---- the sign band over the door: CAFFE ZANETTO, the awning across the front
    k.qy(-3.0, 3.0, 2.95, 3.28, Y0 - 0.012, -1, 'shutD')
    text(k, 'CAFFE ZANETTO', 0.0, Y0 - 0.016, 2.99, 0.26, 'gold', font='display', maxw=5.6)
    awning(k, X0 + 0.3, X1 - 0.3, Y0 - 0.01, 2.9, 1.1, 'canvas', 'awnR')
    wall_lantern(k, X0 + 0.55, Y0, 2.0, arm=0.28)
    wall_lantern(k, X1 - 0.55, Y0, 2.0, arm=0.28)
    # ---- interior: floor tiles (a checker of terrazzo), the bar, the shelves, tables, the stair
    for i in range(10):
        for j in range(8):
            if (i + j) % 2:
                continue
            x, y = X0 + T + i * 0.95, Y0 + T + j * 0.94
            k.qz(x, min(X1 - T, x + 0.95), y, min(Y1, y + 0.94), 0.006, 1, 'stoneD')
    counter(k, -2.2, 3.0, 2.1, 2.7, cols=k.cols)
    espresso(k, 1.6, 2.4, 1.05)
    bottles(k, rnd, -2.0, 0.6, 2.4, 1.05, 9)
    shelf_wall(k, rnd, -2.0, 4.6, Y1 - 0.07, 1.4, 2.9, rows=2, face=-1)
    for (tx, ty) in ((-0.5, -1.6), (2.4, -0.6), (3.6, -2.4)):
        bistro_table(k, tx, ty, cols=k.cols)
        chair(k, tx - 0.55, ty, 90)
        chair(k, tx + 0.55, ty, -90)
    # the stair along the -X wall: 20 treads rising +Y from y = -2.6 to a landing (3.6) at the back corner
    sx0, sx1 = X0 + T, X0 + T + 1.2
    y0 = -2.6
    ye = steps(k, sx0, sx1, y0, 20, sides='l', c='stone')
    k.bxc(sx0, sx1, ye, Y1, 0.0, TERR, 'stone', cull='bkl')
    k.wcol(sx0, sx1, ye, Y1, 0.0, TERR)
    # its handrail on the room side (an iron rail over a stone string), stepped collision
    L = 20 * TREAD
    for i in range(20):
        ya = y0 + i * TREAD
        za = (i + 1) * RISE
        k.bxc(sx1, sx1 + 0.07, ya, ya + TREAD, 0.0, min(za, H - 0.054) if ya + TREAD > OPEN else za, 'stoneD', cull='bl', ink=False)
    k.beam((sx1 + 0.035, y0 + 0.4, 1.0 + 2 * RISE), (sx1 + 0.035, ye, TERR + 1.0), 0.045, 'iron')
    for i in range(1, 6):
        ya = y0 + i * (L / 6)
        k.bxc(sx1 + 0.015, sx1 + 0.055, ya - 0.015, ya + 0.015, ya * 0 + (ya - y0) / TREAD * RISE, (ya - y0) / TREAD * RISE + 1.0, 'iron', cull='tb', ink=False)
    for i in range(5):
        ya, yb = y0 + i * 1.0, y0 + (i + 1) * 1.0
        k.col(sx1, sx1 + 0.12, ya, yb, 0.0, (yb - y0) / TREAD * RISE + 1.0)
    # ---- the roof slab as walkable boxes round the stairwell (open over y OPEN .. ye at x sx0..sx1)
    k.wcol(X0, X1, Y0, OPEN, H, TERR)
    k.wcol(sx1, X1, OPEN, Y1, H, TERR)
    k.wcol(X0, sx1, ye, Y1, H, TERR)
    # the stairwell's iron railing on the terrace (its two open sides; the landing side stays open), a stone curb
    # round the terrace (the balustrade itself is the zone's rail layer at 3.6 m, on the edge cells)
    O = OPEN
    k.bxc(sx0, sx1 + 0.06, O - 0.06, O, TERR, TERR + 0.08, 'stone', cull='b')
    k.bxc(sx1, sx1 + 0.06, O, ye, TERR, TERR + 0.08, 'stone', cull='b')
    k.beam((sx0 + 0.03, O - 0.03, TERR + 1.0), (sx1 + 0.03, O - 0.03, TERR + 1.0), 0.05, 'iron')
    k.beam((sx1 + 0.03, O, TERR + 1.006), (sx1 + 0.03, ye, TERR + 1.006), 0.042, 'iron')
    for (px, py) in ((sx0 + 0.07, O - 0.03), (sx1 - 0.04, O - 0.03), (sx1 + 0.03, O + 1.2), (sx1 + 0.03, O + 2.4), (sx1 + 0.03, ye - 0.06)):
        k.bxc(px - 0.022, px + 0.022, py - 0.022, py + 0.022, TERR + 0.08, TERR + 0.97, 'iron', cull='tb', ink=False)
    for i in range(1, 4):
        k.beam((sx0 + 0.03, O - 0.03, TERR + 0.25 * i), (sx1 + 0.03, O - 0.03, TERR + 0.25 * i), 0.018, 'iron', ink=False)
        k.beam((sx1 + 0.03, O - 0.01, TERR + 0.25 * i + 0.005), (sx1 + 0.03, ye, TERR + 0.25 * i + 0.005), 0.014, 'iron', ink=False)
    k.col(sx0, sx1 + 0.06, O - 0.08, O + 0.02, TERR, TERR + 1.05)
    k.col(sx1, sx1 + 0.08, O, ye, TERR, TERR + 1.05)
    for (a_, b_, c_, d_) in ((X0, X1, Y0, Y0 + 0.08), (X1 - 0.08, X1, Y0 + 0.08, Y1), (X0, X0 + 0.08, Y0 + 0.08, O)):
        k.bxc(a_, b_, c_, d_, TERR, TERR + 0.1, 'stone', cull='b', ink=False)
    for (px, py) in ((X1 - 1.4, Y1 - 0.45), (0.5, Y1 - 0.45), (-2.9, Y1 - 0.45)):
        k.lathe(px, py, TERR, [(0.18, 0.0), (0.26, 0.42), (0.28, 0.46), (0.0, 0.46)], 'terra', seg=6)
        k.hullp([(px + math.cos(a) * 0.3, py + math.sin(a) * 0.3, TERR + 0.46) for a in (0, 1.6, 3.2, 4.7)] + [(px, py, TERR + 1.05)], 'leaf', ink=False)
        k.col(px - 0.28, px + 0.28, py - 0.28, py + 0.28, TERR, TERR + 0.8)
    bistro_table(k, 1.5, -1.6, z=TERR, cols=k.cols)
    chair(k, 0.95, -1.6, 90, z=TERR)
    chair(k, 2.05, -1.6, -90, z=TERR)
    parasol(k, 1.5, -1.6, r=1.3, h=2.3, z=TERR)
    bistro_table(k, 3.3, 1.5, z=TERR, cols=k.cols)
    chair(k, 3.3, 0.95, 180, z=TERR)
    chair(k, 3.3, 2.05, 0, z=TERR)
    parasol(k, 3.3, 1.5, r=1.2, h=2.3, z=TERR, c='canvas', v='awnG')
    done(k, 'Cafe_A', ao)


# ================================================================ Pasticceria Brolo (walk-in) [8, 7]
def build_cafe_b(pal, ao):
    """Footprint x -4..4, y -3.5..3.5; the front (y = -3.5) with a wide arched shop window and the door, a side door
    (-X); inside the pastry counter (glass front, trays of pastries), the coffee bar along the back, two tables; a
    flat roof with a low parapet and pots (not walkable)."""
    rnd = random.Random(12)
    k = kit(pal).begin()
    X0, X1, Y0, Y1 = -4.0, 4.0, -3.5, 3.5
    Ht = 3.4
    fr_holes = [(-3.4, -0.6, 0.6, 2.2 + 1.4), (0.4, 1.6, 0.0, 2.3 + 0.6), (2.2, 3.4, 0.6, 2.3 + 0.6)]
    side_holes = [(-1.6, -0.4, 0.0, 2.4)]
    for (a, b, c0, c1) in wall_parts(X0, X1, 0.0, Ht - 0.3, fr_holes):
        k.box2(a, b, Y0, Y0 + T, c0, c1, lambda f: 'stucco' if f.normal.y < -0.5 else ('plaster' if f.normal.y > 0.5 else 'stuccoD'))
    for (a, b, c0, c1) in wall_parts(Y0 + T, Y1, 0.0, Ht - 0.3, side_holes):
        k.box2(X0, X0 + T, a, b, c0, c1, lambda f: 'stucco' if f.normal.x < -0.5 else ('plaster' if f.normal.x > 0.5 else 'stuccoD'))
    k.box2(X1 - T, X1, Y0 + T, Y1, 0.0, Ht - 0.3, lambda f: 'stucco' if f.normal.x > 0.5 else ('plaster' if f.normal.x < -0.5 else 'stuccoD'))
    k.qy(X0 + T, X1 - T, 0.0, Ht - 0.304, Y1 - 0.06, -1, 'plaster')
    for (a, b, c0, c1) in wall_parts(X0, X1, 0.0, 2.4, [(h[0], h[1], h[2], min(h[3], 2.4)) for h in fr_holes]):
        if c1 - c0 > 0.05:
            k.col(a, b, Y0, Y0 + T, c0, Ht)
    k.col(X0, X1, Y0, Y0 + T, 2.4, Ht)
    for (a, b, c0, c1) in wall_parts(Y0 + T, Y1, 0.0, 2.4, side_holes):
        k.col(X0, X0 + T, a, b, 0.0, Ht)
    k.col(X0, X0 + T, side_holes[0][0], side_holes[0][1], 2.4, Ht)
    k.col(X1 - T, X1, Y0 + T, Y1, 0.0, Ht)
    for (a, b, z0, top) in fr_holes:
        hw = (b - a) / 2
        zs = top - min(hw, 0.6 if b - a > 2 else hw)
        kind = 'seg' if b - a > 2 else 'round'
        cur = arch_curve(a, b, zs, kind, 4, rise=top - zs)
        for f in (-1, 1):
            yy = Y0 if f < 0 else Y0 + T
            left = [(a, zs)] + [p for p in cur if p[0] <= (a + b) / 2 + 1e-6]
            right = [p for p in cur if p[0] >= (a + b) / 2 - 1e-6] + [(b, zs)]
            col = 'stucco' if f < 0 else 'plaster'
            k.poly([(px, yy, pz) for (px, pz) in left] + [(a, yy, top)], col, (0, f, 0))
            k.poly([(b, yy, top)] + [(px, yy, pz) for (px, pz) in right], col, (0, f, 0))
        for (pa, pb) in zip(cur, cur[1:]):
            mx, mz = (pa[0] + pb[0]) / 2 - (a + b) / 2, (pa[1] + pb[1]) / 2 - (zs - 1.0)
            k.poly([(pa[0], Y0, pa[1]), (pb[0], Y0, pb[1]), (pb[0], Y0 + T, pb[1]), (pa[0], Y0 + T, pa[1])], 'stuccoD', (-mx, 0, -mz))
            k.poly([(pa[0], Y0 - 0.006, pa[1]), (pa[0], Y0 - 0.006, pa[1] + 0.1), (pb[0], Y0 - 0.006, pb[1] + 0.1), (pb[0], Y0 - 0.006, pb[1])], 'stone', (0, -1, 0))
        if z0 > 0:
            k.qz(a, b, Y0, Y0 + T, z0 + 0.004, 1, 'stone')
            gl = [(a, Y0 + 0.12, z0), (b, Y0 + 0.12, z0)] + [(px, Y0 + 0.12, pz) for (px, pz) in reversed(cur)][1:-1] + [(a, Y0 + 0.12, zs)]
            k.poly(gl, 'glass', (0, -1, 0))
            k.poly(list(reversed([(px, Y0 + 0.124, pz) for (px, _, pz) in gl])), 'glass', (0, 1, 0))
            glints(k, a, b, z0 + 0.2, zs, Y0 + 0.116)
        else:
            k.qz(a, b, Y0, Y0 + T, 0.006, 1, 'stone')
            k.bxc(b - 0.05, b, Y0 + T + 0.01, Y0 + T + 0.9, 0.02, zs - 0.02, 'wood', cull='b')
    text(k, 'PASTICCERIA', -2.0, Y0 + 0.112, 1.65, 0.22, 'gold', font='display', maxw=2.4)
    k.qy(-3.6, 3.6, 2.98, 3.3, Y0 - 0.012, -1, 'awnG')
    text(k, 'BROLO DAL 1871', 0.0, Y0 - 0.016, 3.02, 0.26, 'gold', font='display', maxw=6.0)
    awning(k, X0 + 0.3, X1 - 0.3, Y0 - 0.01, 2.92, 0.95, 'canvas', 'awnG')
    k.bxc(X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1, Ht - 0.3, Ht, 'stone', cull='k')
    k.qz(X0 + T, X1 - T, Y0 + T, Y1, Ht - 0.304, -1, 'plaster')
    for (px, py) in ((X0 + 0.4, Y0 + 0.4), (X1 - 0.4, Y0 + 0.4), (0.0, Y0 + 0.4)):
        k.lathe(px, py, Ht, [(0.16, 0.0), (0.22, 0.36), (0.0, 0.36)], 'terra', seg=6)
        k.hullp([(px + math.cos(a) * 0.26, py + math.sin(a) * 0.26, Ht + 0.36) for a in (0, 2.1, 4.2)] + [(px, py, Ht + 0.8)], 'leaf', ink=False)
    k.bxc(X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y0 + 0.1, Ht, Ht + 0.35, 'stone', cull='b')
    # interior: the pastry counter with its glass front and trays, the coffee bar, shelves, two tables
    for i in range(8):
        for j in range(7):
            if (i + j) % 2:
                continue
            x, y = X0 + T + i * 0.94, Y0 + T + j * 0.93
            k.qz(x, min(X1 - T, x + 0.94), y, min(Y1, y + 0.93), 0.006, 1, 'stoneD')
    k.bx(-1.4, 3.2, 0.6, 1.3, 0.0, 0.55, 'wood')
    k.bxc(-1.4, 3.2, 0.6, 1.3, 0.55, 1.15, 'glassL', cull='b', ink=False)
    for i in range(6):
        tx = -1.2 + i * 0.72
        k.qz(tx, tx + 0.6, 0.7, 1.2, 0.56 + 0.004, 1, 'white')
        for j in range(4):
            c = ('fOrange', 'lemon', 'fPink', 'rattan')[(i + j) % 4]
            k.bxc(tx + 0.05 + j * 0.13, tx + 0.15 + j * 0.13, 0.82, 1.0, 0.565, 0.62, c, ink=False)
    k.bxc(-1.45, 3.25, 0.55, 1.35, 1.15, 1.19, 'marble', cull='')
    k.col(-1.45, 3.25, 0.55, 1.35, 0.0, 1.19)
    counter(k, -2.0, 3.4, 2.5, 3.1, cols=k.cols)
    espresso(k, 1.2, 2.8, 1.05)
    shelf_wall(k, rnd, -3.4, 3.4, Y1 - 0.07, 1.3, 2.9, rows=3, face=-1, goods='boxes')
    for (tx, ty) in ((-2.6, -1.6), (-0.6, -2.2)):
        bistro_table(k, tx, ty, cols=k.cols)
        chair(k, tx, ty - 0.55, 0)
        chair(k, tx, ty + 0.55, 180)
    done(k, 'Cafe_B', ao)
