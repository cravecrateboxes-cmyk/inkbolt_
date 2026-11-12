"""INKBOLT kit-mossgarden: built things -- the garden walls, the gate, trail hedges, the raised terrace (retaining walls
with balustrades, piers, back planters, the grand stair and a side stair, the wisteria pergola), the tiered fountain,
wall fountains, the reflecting pool, the grotto spring and the culvert, the stone bridge and stepping stones, the
glasshouse, the gazebo, the ruined folly, benches, lamps, urns, sundial, armillary, signposts, tea tables, the maze
arch, the potting shed and nursery props, the hatch and the backdrop manor (see mg_base.py for the conventions)."""
import math
import random

from mg_base import TER, RISE, TREAD, WALL_H, zcol, stonecol, mosscol, blob, puff, bloom, frond, ring, baluster, urn  # noqa: F401

LEAF = zcol('leafL', 'leaf', 'leafD', 0.45)
HEDGE = zcol('hedgeT', 'hedge', 'hedge2', 0.6, -0.5)
MOSS = zcol('moss', 'moss2', 'mossD', 0.3)


def ivycol(f):
    return 'leaf' if abs(f.normal.y) > 0.5 else 'leafD'


def ivy(k, rnd, x, y, z, r, s=-1):
    """a flat clump of ivy against a wall face at y (s = -1: the face looks toward -Y)"""
    pts = []
    for i in range(7):
        a = (i + rnd.uniform(-0.2, 0.2)) / 7 * 2 * math.pi
        rr = r * rnd.uniform(0.8, 1.05)
        pts.append((x + math.cos(a) * rr, y, z + math.sin(a) * rr * 0.85))
        pts.append((x + math.cos(a) * rr * 0.7, y + s * 0.09, z + math.sin(a) * rr * 0.6))
    k.hullp(pts, ivycol, ink=False)


def courses(k, x0, x1, zs, y, s, c='stone3', step=0.6, skip=None):
    """mortar courses and staggered joints on a wall face at y (5 mm proud; joints end at the course strips)"""
    for z in zs:
        k.qy(x0, x1, z, z + 0.035, y, s, c)
    for j, (za, zb) in enumerate(zip(zs, zs[1:])):
        x = x0 + (step * 0.5 if j % 2 else step)
        while x < x1 - 0.06:
            if not (skip and skip[0] < x < skip[1]):
                k.qy(x - 0.016, x + 0.016, za + 0.035, zb, y, s, c)
            x += step


# ================================================================ garden walls (zone edge '#', front -Y)
WZ = (0.95, 1.4, 1.85, 2.3, 2.75, 3.2)


def wall_module(k, rnd, x0, x1, kind):
    k.bx(x0, x1, -0.42, 0.5, 0.0, 3.42, 'stone2')
    k.qy(x0, x1, 0.0, 0.5, -0.425, -1, 'stone3')   # the plinth course
    k.bx(x0, x1, -0.48, 0.5, 3.42, 3.6, 'stone')
    for z in (1.3, 2.2, 3.05):
        k.qy(x0, x1, z, z + 0.035, -0.426, -1, 'stone3')
    puff(k, rnd, x0 + (x1 - x0) * rnd.uniform(0.25, 0.75), -0.46, 0.5, rnd.uniform(0.14, 0.2), MOSS, n=4, flat=0.5, ink=False)
    if kind == 'ivy':
        cx = x0 + (x1 - x0) * rnd.uniform(0.35, 0.65)
        for (dx, z, r) in ((0.0, 3.2, 0.46), (-0.3, 2.6, 0.38), (0.15, 2.0, 0.3)):
            ivy(k, rnd, cx + dx, -0.43 - 0.004 * (z * 10 % 3), z, r)
    if kind == 'pier':
        k.bx(0.2, 0.8, -0.53, 0.49, 0.0, 3.75, 'stone')
        k.bx(0.14, 0.86, -0.58, 0.49, 3.75, 3.9, 'stone2')
        k.cyl(0.5, -0.04, 3.9, 0.12, 0.1, 0.12, 'stone', seg=6)
        k.sph(0.5, -0.04, 4.18, 0.19, 'stone2', seg=(6, 4))


def build_walls(k, ao):
    for name, kind, seed in (('Wall2_A', None, 401), ('Wall2_B', 'ivy', 402), ('Wall2_C', 'pier', 403)):
        rnd = random.Random(seed)
        k.begin()
        wall_module(k, rnd, -0.5, 1.5, kind)
        k.finish(name, ao=ao)
    rnd = random.Random(404)
    k.begin()
    wall_module(k, rnd, -0.5, 0.5, None)
    k.finish('Wall1', ao=ao)
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0.0, 3.8, 'stone')
    k.bx(-0.56, 0.56, -0.56, 0.56, 3.8, 3.95, 'stone2')
    k.cyl(0, 0, 3.95, 0.14, 0.12, 0.12, 'stone', seg=8)
    k.sph(0, 0, 4.28, 0.23, 'stone2', seg=(8, 5))
    k.finish('WallCorner', ao=ao)


# ================================================================ gate, trail hedges, hatch, crates
def build_gate(k, ao):
    k.begin()
    for s in (-1, 1):
        x0, x1 = (1.55, 2.45) if s > 0 else (-2.45, -1.55)
        k.bx(x0 - 0.05, x1 + 0.05, -0.5, 0.5, 0.0, 0.5, 'stone3')
        k.bx(x0, x1, -0.45, 0.45, 0.5, 3.9, 'stone2')
        k.bx(x0 - 0.06, x1 + 0.06, -0.51, 0.51, 3.9, 4.06, 'stone')
        k.cyl((x0 + x1) / 2, 0, 4.06, 0.16, 0.13, 0.14, 'stone', seg=8)
        k.sph((x0 + x1) / 2, 0, 4.42, 0.26, 'stone2', seg=(8, 5))
        for yy, sg in ((-0.454, -1), (0.454, 1)):
            courses(k, x0, x1, (1.1, 1.75, 2.4, 3.05), yy, sg, step=0.9)
    # wrought-iron overthrow and the name plaque
    pts = [(-1.55 + 3.1 * i / 8, 0.0, 3.4 + 0.75 * math.sin(math.pi * i / 8)) for i in range(9)]
    for a, b in zip(pts, pts[1:]):
        k.beam(a, b, 0.07, 'iron')
    k.bx(-1.55, 1.55, -0.046, 0.046, 3.38, 3.46, 'iron')
    for i in range(1, 8):
        x = -1.55 + 3.1 * i / 8
        k.beam((x, 0, 3.45), (x, 0, 3.4 + 0.75 * math.sin(math.pi * i / 8) - 0.02), 0.03, 'iron', ink=False)
    k.bx(-1.15, 1.15, -0.07, 0.07, 3.56, 3.98, 'verd')
    k.text('MOSSWOOD GARDENS', 0.0, -0.074, 3.64, 0.27, 'tulipW', maxw=2.1, font='display')
    k.text('MOSSWOOD GARDENS', 0.0, 0.074, 3.64, 0.27, 'tulipW', face='y+', maxw=2.1, font='display')
    k.finish('GateFrame', ao=ao)
    k.begin()
    Hs = 3.05
    for z0, z1 in ((0.12, 0.22), (1.05, 1.13), (2.72, 2.82)):
        k.bx(-1.5, 1.5, -0.05, 0.05, z0, z1, 'iron', ink=False)
    k.bx(-0.05, 0.05, -0.06, 0.06, 0.0, Hs, 'iron', ink=False)
    for i in range(20):
        x = -1.43 + i * 0.15
        if abs(x) < 0.07:
            continue
        k.cyl(x, 0, 0.05, 0.022, 0.022, Hs - 0.2 - 0.12 * math.sin(math.pi * (abs(x) / 1.5)), 'iron', seg=4, ink=False)
        top = 0.05 + Hs - 0.2 - 0.12 * math.sin(math.pi * (abs(x) / 1.5))
        k.cyl(x, 0, top, 0.04, 0.0, 0.14, 'bronze', seg=4, ink=False)
    for s in (-1, 1):
        k.cyl(s * 0.75, -0.06, 1.6, 0.16, 0.16, 0.02, 'bronze', seg=10, rot=(90, 0, 0), ink=False)
    obj = k.finish('GateShutter', ao=False)
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)
    k.tris[k.prefix + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # trail hedges: 1 m along Y, inner face +X, on a stone kerb
    for name, seed in (('TrailWall', 411), ('TrailWall_B', 412), ('TrailWall_C', 413)):
        rnd = random.Random(seed)
        k.begin()
        k.bx(-0.5, 0.3, -0.5, 0.5, 0.0, 0.42, 'stone2')
        pts = [(x, y, z) for y in (-0.5, 0.5) for (x, z) in ((0.2, 0.42), (0.22, 2.48), (0.1, 2.6), (-0.5, 2.6), (-0.5, 0.42))]
        k.hullp(pts, HEDGE)
        if name == 'TrailWall_B':
            k.cyl(0.24, 0.0, 0.42, 0.045, 0.04, 1.9, 'iron', seg=6)
            k.bx(0.16, 0.32, -0.08, 0.08, 2.32, 2.36, 'iron')
            k.cyl(0.24, 0.0, 2.36, 0.09, 0.07, 0.26, 'amber', seg=6, ink=False)
            k.cyl(0.24, 0.0, 2.62, 0.11, 0.02, 0.12, 'iron', seg=6)
        if name == 'TrailWall_C':
            for (y, z) in ((-0.3, 0.9), (0.1, 1.4), (0.35, 0.75), (-0.1, 1.9), (0.25, 2.2)):
                bloom(k, 0.24, y, z, 0.085, 'rose', ink=True)
        k.finish(name, ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.2, 0.12, 'stone', seg=16)
    k.cyl(0, 0, 0.12, 0.95, 0.95, 0.02, 'verd', seg=16, ink=False)
    for i in range(8):
        a = i / 8 * math.pi * 2
        k.cyl(math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12, 0.06, 0.06, 0.05, 'bronze', seg=6)
    k.finish('Hatch', ao=ao)
    for name in ('Crate', 'Crate_Seed'):
        rnd = random.Random(421 if name == 'Crate' else 422)
        k.begin()
        k.bx(-0.42, 0.42, -0.42, 0.42, 0.0, 0.55, 'wood')
        for s in (-1, 1):
            for z in (0.18, 0.37):
                k.qy(-0.42, 0.42, z, z + 0.025, s * 0.425, s, 'wood2')
                k.qx(-0.42, 0.42, z, z + 0.025, s * 0.425, s, 'wood2')
        if name == 'Crate_Seed':
            k.bx(-0.38, 0.38, -0.38, 0.38, 0.55, 0.6, 'soil', ink=False)
            for i in range(9):
                x, y = -0.26 + (i % 3) * 0.26, -0.26 + (i // 3) * 0.26
                bloom(k, x, y, 0.68, 0.07, 'leafL')
                bloom(k, x + 0.03, y - 0.02, 0.74, 0.04, 'tulipW' if i % 2 else 'tulipY')
        k.col(-0.42, 0.42, -0.42, 0.42, 0.0, 0.55)
        k.finish(name, ao=ao)


# ================================================================ the raised terrace (TER = 2.34 m)
TZ = (0.45, 0.9, 1.35, 1.8)


def terrace_face(k, rnd, skip=None):
    """the retaining wall's garden face (Blender +Y), moss at its foot"""
    k.bx(-0.5, 0.5, -0.5, 0.5, 0.0, TER, 'stone2')
    for z in (0.75, 1.55):
        for (a, b) in (((-0.5, skip[0]), (skip[1], 0.5)) if skip else ((-0.5, 0.5),)):
            k.qy(a, b, z, z + 0.035, 0.505, 1, 'stone3')
    puff(k, rnd, rnd.uniform(-0.25, 0.25), 0.53, 0.02, rnd.uniform(0.13, 0.17), MOSS, n=4, flat=0.6, ink=False)
    k.bx(-0.5, 0.5, 0.02, 0.6, TER, TER + 0.1, 'stone')


def terrace_cols(k):
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, TER - 1.0)
    k.wcol(-0.5, 0.5, -0.5, 0.5, TER - 1.0, TER)


def build_terrace(k, ao):
    # balustrade module (edge-turned: the front, Blender -Y, faces the terrace; the garden face is +Y)
    rnd = random.Random(431)
    k.begin()
    terrace_face(k, rnd)
    for x in (-0.333, 0.0, 0.333):
        baluster(k, x, 0.31, TER + 0.1, h=0.74)
    k.bx(-0.5, 0.5, 0.13, 0.49, TER + 0.84, TER + 0.98, 'stone')
    terrace_cols(k)
    k.col(-0.5, 0.5, 0.12, 0.5, TER, TER + 0.98)
    k.finish('TerraceWall', ao=ao)
    # balustrade with a pier, a pilaster down the face and an urn of flowers
    rnd = random.Random(432)
    k.begin()
    terrace_face(k, rnd, skip=(-0.32, 0.32))
    k.bx(-0.3, 0.3, 0.5, 0.6, 0.0, TER, 'stone')
    for a, b in ((-0.5, -0.27), (0.27, 0.5)):
        k.bx(a, b, 0.16, 0.46, TER + 0.1, TER + 0.2, 'stone2')
        k.bx(a, b, 0.13, 0.49, TER + 0.84, TER + 0.98, 'stone')
    for x in (-0.39, 0.39):
        baluster(k, x, 0.31, TER + 0.2, h=0.64)
    k.bx(-0.27, 0.27, 0.04, 0.6, TER + 0.1, TER + 1.12, 'stone')
    k.bx(-0.32, 0.32, 0.0, 0.64, TER + 1.12, TER + 1.22, 'stone2')
    urn(k, 0.0, 0.32, TER + 1.22, 0.8)
    terrace_cols(k)
    k.col(-0.5, 0.5, 0.12, 0.5, TER, TER + 0.98)
    k.col(-0.3, 0.3, 0.02, 0.62, TER, TER + 1.85)
    k.finish('TerraceWall_P', ao=ao)
    # corner pier
    rnd = random.Random(433)
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0.0, TER + 0.15, 'stone')
    k.bx(-0.53, 0.53, -0.53, 0.53, 0.0, 0.3, 'stone3')
    k.bx(-0.36, 0.36, -0.36, 0.36, TER + 0.15, TER + 1.1, 'stone2')
    k.bx(-0.42, 0.42, -0.42, 0.42, TER + 1.1, TER + 1.22, 'stone')
    urn(k, 0.0, 0.0, TER + 1.22, 1.0, fl='tulip', rnd=rnd)
    for (x, y) in ((0.3, 0.53), (-0.3, 0.53), (0.53, 0.0)):
        puff(k, rnd, x, y, 0.3, 0.15, MOSS, n=5, flat=0.6, ink=False)
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, TER + 1.22)
    k.finish('TerraceCorner', ao=ao)
    # back cells against the garden wall: the terrace body and a raised flower border (planter toward +Y)
    for name, seed, fl in (('TerraceBack_A', 434, 'tulipY'), ('TerraceBack_B', 435, 'roseP')):
        rnd = random.Random(seed)
        k.begin()
        k.bx(-0.5, 0.5, -0.5, 0.5, 0.0, TER, 'stone2')
        k.bx(-0.5, 0.5, 0.0, 0.5, TER, TER + 0.5, 'stone3')
        k.qz(-0.5, 0.5, 0.06, 0.46, TER + 0.504, 1, 'soil')
        k.hullp([(x, y, TER + 0.512) for x in (-0.47, 0.47) for y in (0.1, 0.44)] + [(x, 0.27, TER + 0.86 + (0.05 if fl == 'roseP' else 0.0)) for x in (-0.36, 0.36)],
                LEAF, ink=False)
        bloom(k, rnd.uniform(-0.2, 0.2), 0.12, TER + 0.8 + rnd.uniform(-0.08, 0.05), 0.09, fl)
        terrace_cols(k)
        k.col(-0.5, 0.5, 0.0, 0.5, TER, TER + 0.5)
        k.finish(name, ao=ao)
    stair(k, ao, 'TerraceStair', 2.1)
    stair(k, ao, 'TerraceStairS', 1.1)
    pergola(k, ao)


def stair(k, ao, name, hw, ch=0.4):
    """a stone stair up the retaining wall [2 (hw + ch), 5], rising toward +Y: a foot landing, 13 steps of 0.18 m on
    0.25 m treads, the top landing in the balustrade row, cheek walls with sloped balustrades, newel piers and urns"""
    rnd = random.Random(int(hw * 100))
    k.begin()
    k.bx(-hw + 0.05, hw - 0.05, -2.47, -1.75, 0.0, 0.05, 'stone', ink=False)
    for i in range(13):
        y0 = -1.75 + i * TREAD
        k.bx(-hw - 0.02, hw + 0.02, y0, y0 + TREAD, 0.0, (i + 1) * RISE, 'stone')
        k.wcol(-hw, hw, y0, y0 + TREAD, max(0.0, (i + 1) * RISE - 1.0), (i + 1) * RISE)
    k.bx(-hw - 0.02, hw + 0.02, 1.5, 2.49, 0.0, TER, 'stone2')
    k.col(-hw, hw, 1.5, 2.5, 0.0, TER - 1.0)
    k.wcol(-hw, hw, 1.5, 2.5, TER - 1.0, TER)

    def line(y):   # stair nosing line + 0.15
        return RISE + 0.72 * (y + 1.75) + 0.15
    for s in (-1, 1):
        xi, xo = sorted((s * hw, s * (hw + ch)))
        xc = (xi + xo) / 2
        top = [(-2.1, 0.35), (1.5, line(1.5)), (2.5, TER + 0.12)]
        pts = []
        for x in (xi, xo):
            pts += [(x, -2.1, 0.0), (x, 2.5, 0.0)] + [(x, y, z) for (y, z) in top]
        k.hullp(pts, stonecol)
        # sloped balustrade then a level run on the top landing
        ra, rb, rc = (-2.1, 0.35 + 0.85), (1.5, line(1.5) + 0.85), (2.5, TER + 0.12 + 0.85)
        k.beam((xc, ra[0], ra[1]), (xc, rb[0], rb[1]), 0.15, 'stone')
        k.beam((xc, rb[0] - 0.05, rb[1]), (xc, rc[0], rc[1] - 0.06), 0.15, 'stone')
        n = 9
        for j in range(n):
            y = -1.8 + j * (3.25 / (n - 1))
            zb = 0.35 + (line(1.5) - 0.35) * (y + 2.1) / 3.6
            zt = zb + 0.85 * 0.88
            k.cyl(xc, y, zb, 0.06, 0.05, zt - zb, 'stone', seg=5, ink=False)
        for y in (1.9, 2.25):
            k.cyl(xc, y, TER + 0.12, 0.06, 0.05, 0.7, 'stone', seg=5, ink=False)
        # newel pier at the foot with an urn of flowers
        k.bx(xi - 0.03, xo + 0.03, -2.5, -2.08, 0.0, 1.05, 'stone')
        k.bx(xi - 0.07, xo + 0.07, -2.54, -2.04, 1.05, 1.16, 'stone2')
        urn(k, xc, -2.29, 1.16, 0.75, fl='tulip', rnd=rnd)
        k.col(xi, xo, -2.5, -2.08, 0.0, 1.6)
        for (y0, y1) in ((-2.08, -0.9), (-0.9, 0.3), (0.3, 1.5), (1.5, 2.5)):
            zt = (line(y1) if y1 <= 1.5 else TER + 0.12) + 0.85
            k.col(xi, xo, y0, y1, 0.0, zt)
    k.finish(name, ao=ao)


def pergola(k, ao):
    """the wisteria pergola [6, 4]: six stone columns, timber beams and rafters, hanging racemes, a bench under it"""
    rnd = random.Random(441)
    k.begin()
    for x in (-2.55, 0.0, 2.55):
        for y in (-1.6, 1.6):
            k.bx(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0.0, 0.3, 'stone2')
            k.cyl(x, y, 0.3, 0.17, 0.15, 2.25, 'stone', seg=8)
            k.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, 2.55, 2.7, 'stone2')
            k.col(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0.0, 2.7)
    for y in (-1.6, 1.6):
        k.bx(-3.0, 3.0, y - 0.1, y + 0.1, 2.7, 2.95, 'wood')
    for i in range(10):
        x = -2.7 + i * 0.6
        k.bx(x - 0.05, x + 0.05, -2.0, 2.0, 2.95, 3.1, 'wood2')
    for i in range(6):
        puff(k, rnd, -2.5 + i * 1.0 + rnd.uniform(-0.2, 0.2), rnd.uniform(-1.2, 1.2), 3.2, rnd.uniform(0.7, 0.95), LEAF, n=6, flat=0.4)
    for i in range(26):
        x, y = rnd.uniform(-2.8, 2.8), rnd.uniform(-1.9, 1.9)
        if min(abs(x - c) for c in (-2.55, 0.0, 2.55)) < 0.35 and abs(abs(y) - 1.6) < 0.35:
            continue
        L = rnd.uniform(0.4, 0.7)
        k.cyl(x, y, 2.93 - L, 0.012, 0.09, L, 'lav' if i % 3 else 'lav2', seg=5, ink=False)
    # a bench under it, facing south
    bench(k, 0.0, 0.55, 1.6)
    k.col(-0.8, 0.8, 0.25, 0.83, 0.0, 0.47)
    k.col(-0.8, 0.8, 0.73, 0.85, 0.47, 0.9)
    k.finish('Pergola', ao=ao)


def bench(k, x, y, w=1.9):
    """a garden bench along X at (x, y) facing -Y: stone end supports, timber slats, a slatted back"""
    h = w / 2
    for s in (-1, 1):
        xe = x + s * (h - 0.08)
        k.bx(xe - 0.07, xe + 0.07, y - 0.3, y + 0.26, 0.0, 0.42, 'stone2')
        k.bx(xe - 0.06, xe + 0.06, y + 0.18, y + 0.29, 0.43, 0.92, 'stone2')
    for j in range(2):
        y0 = y - 0.3 + j * 0.25
        k.bx(x - h, x + h, y0 + 0.01, y0 + 0.24, 0.42, 0.47, 'wood')
    k.bx(x - h + 0.03, x + h - 0.03, y + 0.2, y + 0.26, 0.6, 0.86, 'wood')


# ================================================================ fountains and water
def build_fountains(k, ao):
    rnd = random.Random(451)
    k.begin()
    a0 = math.pi / 8
    for i in range(8):
        a, b = a0 + i * math.pi / 4, a0 + (i + 1) * math.pi / 4
        pts = []
        for t in (a, b):
            c, s = math.cos(t), math.sin(t)
            for (r, z) in ((4.32, 0.0), (4.4, 0.62), (4.4, 0.74), (3.82, 0.74), (3.86, 0.0)):
                pts.append((c * r, s * r, z))
        k.hullp(pts, stonecol)
    k.poly(ring(0, 0, 3.86, 8, 0.55, a0), 'water', (0, 0, 1))
    for R in (2.55, 3.35):
        for i in range(16):
            if i % 4 == 3:
                continue
            t0, t1 = i / 16 * 2 * math.pi, (i + 0.8) / 16 * 2 * math.pi
            pts = [(math.cos(t) * r, math.sin(t) * r, 0.556) for (t, r) in ((t0, R - 0.04), (t1, R - 0.04), (t1, R + 0.04), (t0, R + 0.04))]
            k.poly(pts, 'foam', (0, 0, 1))
    k.cyl(0, 0, 0.0, 1.25, 1.15, 0.95, 'stone2', seg=8)
    k.cyl(0, 0, 0.95, 1.0, 1.0, 0.12, 'stone', seg=8)
    k.cyl(0, 0, 1.07, 0.48, 0.38, 0.85, 'stone', seg=10)
    for (z, rb, rt, h, zs, ss, sh) in ((1.85, 0.42, 2.5, 0.42, 0.0, 0.0, 0.0), (3.25, 0.3, 1.6, 0.32, 2.32, 0.32, 1.0), (4.4, 0.2, 0.9, 0.22, 3.6, 0.22, 0.85)):
        if sh:
            k.cyl(0, 0, zs, ss, ss * 0.88, sh, 'stone', seg=10)
        k.cyl(0, 0, z, rb, rt, h, 'stone', seg=16)
        k.cyl(0, 0, z + h - 0.06, rt + 0.06, rt + 0.06, 0.12, 'stone2', seg=16)
        k.disc(0, 0, z + h + 0.066, rt - 0.03, 'water', n=16)
    k.cyl(0, 0, 4.686, 0.16, 0.12, 0.25, 'stone', seg=8)
    pts = []
    for j, (z, r) in enumerate(((4.9, 0.14), (5.05, 0.24), (5.25, 0.26), (5.45, 0.2), (5.6, 0.08))):
        pts += ring(0, 0, r, 6, z, a0=j * 0.5)
    k.hullp(pts, 'stone2')
    for i in range(4):
        a = i * math.pi / 2
        urn(k, math.cos(a) * 4.1, math.sin(a) * 4.1, 0.74, 0.62, fl='tulip', rnd=rnd)
    # the octagonal basin as strips across it, each as wide as the octagon is at its outer edge (just inside the rim)
    A = 4.32 * math.cos(math.pi / 8)
    for j in range(16):
        y0, y1 = -A + j * (2 * A / 16), -A + (j + 1) * (2 * A / 16)
        hx = min(A, A * math.sqrt(2) - max(abs(y0), abs(y1))) - 0.02
        k.col(-hx, hx, y0 + 0.01, y1 - 0.01, 0.0, 0.74)
    k.col(-1.25, 1.25, -1.25, 1.25, 0.74, 5.6)
    k.finish('Landmark_Fountain', ao=ao)
    # falling water: open curtains from every bowl lip, the jet, splash rings, rim jets (additive companion)
    k.begin()
    for (z, h, rb, rt) in ((0.56, 1.72, 2.78, 2.6), (2.33, 1.22, 1.78, 1.68), (3.61, 1.0, 1.02, 0.97)):
        k.cyl(0, 0, z, rb, rt, h, 'water2', seg=16, caps=False, ink=False)
        k.cyl(0, 0, z, rb + 0.22, rb + 0.22, 0.07, 'foam', seg=16, caps=False, ink=False)
    k.cyl(0, 0, 5.55, 0.07, 0.04, 0.95, 'foam', seg=6, ink=False)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        k.beam((math.cos(a) * 0.05, math.sin(a) * 0.05, 6.45), (math.cos(a) * 0.35, math.sin(a) * 0.35, 6.25), 0.04, 'foam', ink=False)
        k.beam((math.cos(a) * 0.35, math.sin(a) * 0.35, 6.25), (math.cos(a) * 0.55, math.sin(a) * 0.55, 5.7), 0.04, 'foam', ink=False)
    for i in range(8):
        a = i / 8 * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        pts = [(c * (3.85 - 1.0 * t), s * (3.85 - 1.0 * t), 0.78 + 0.8 * math.sin(math.pi * t) - 0.2 * t) for t in (0, 0.33, 0.66, 1.0)]
        for p, q in zip(pts, pts[1:]):
            k.beam(p, q, 0.04, 'foam', ink=False)
    k.finish('Fountain_Spray', ao=False)

    # wall fountain [3, 1]: an arched niche, a shell spout, a half-round basin (front -Y, back against a wall at +0.5)
    rnd = random.Random(452)
    k.begin()
    k.bx(-1.25, 1.25, 0.25, 0.49, 0.0, 2.4, 'stone2')
    pts = [(-0.62, 0.245, 0.7), (0.62, 0.245, 0.7)] + [(math.cos(t) * 0.62, 0.245, 1.7 + math.sin(t) * 0.62) for t in [i / 8 * math.pi for i in range(9)]]
    k.poly(pts, 'stoneD', (0, -1, 0))
    for s in (-1, 1):   # pilasters stop 2 cm inside the block's ends (clear of a wall's coping behind it)
        xa, xb = sorted((s * 1.25, s * 1.48))
        k.bx(xa, xb, 0.15, 0.49, 0.0, 2.6, 'stone')
        k.bx(xa - 0.02, xb + 0.02, 0.11, 0.49, 2.6, 2.7, 'stone2')
    k.hullp([(x, y, z) for x in (-1.58, 1.58) for y in (0.11, 0.49) for z in (2.7,)] + [(0.0, y, 3.2) for y in (0.11, 0.49)], stonecol)
    sh = [(0.0, 0.24, 1.48)] + [(math.cos(t) * 0.34, 0.24 - math.sin(t) * 0.3, 1.62) for t in [i / 6 * math.pi for i in range(7)]] + [(0.0, 0.1, 1.68)]
    k.hullp(sh, 'stone')
    k.cyl(0.0, 0.05, 1.56, 0.04, 0.04, 0.16, 'bronze', seg=6, rot=(90, 0, 0))
    half = [(math.cos(t) * 0.74, 0.25 - math.sin(t) * 0.72, 0.0) for t in [i / 8 * math.pi for i in range(9)]]
    k.hullp(half + [(x, y, 0.6) for (x, y, _) in half], 'stone')
    k.poly([(math.cos(t) * 0.64, 0.25 - math.sin(t) * 0.62, 0.608) for t in [i / 8 * math.pi for i in range(9)]], 'water', (0, 0, 1))
    for i in range(8):
        t = (i + 0.5) / 8 * math.pi
        k.bxr(math.cos(t) * 0.7, 0.25 - math.sin(t) * 0.68, 0.65 + 0.008 * (i % 2), 0.3, 0.09, 0.1, 'stone2', rot=(0, 0, math.degrees(-t) + 90))
    frond(k, (-1.0, 0.3, 3.0), 2.4, 0.7, 0.26, lift=0.5, droop=0.9, seg=2)
    frond(k, (1.0, 0.3, 3.0), 0.7, 0.6, 0.24, lift=0.5, droop=0.9, seg=2)
    k.col(-1.5, 1.5, 0.12, 0.5, 0.0, 2.7)
    k.col(-0.74, 0.74, -0.47, 0.25, 0.0, 0.72)
    k.finish('WallFountain', ao=ao)
    k.begin()
    pts = [(0.0, 0.0, 1.56), (0.0, -0.14, 1.3), (0.0, -0.2, 0.95), (0.0, -0.21, 0.62)]
    for p, q in zip(pts, pts[1:]):
        k.beam(p, q, 0.08, 'water2', ink=False)
    k.cyl(0.0, -0.21, 0.61, 0.16, 0.2, 0.05, 'foam', seg=8, caps=False, ink=False)
    k.finish('WallFountain_Spray', ao=False)

    # reflecting pool [3, 16]: a long still pool with a walkable stone coping, lily pads and water lilies
    rnd = random.Random(453)
    k.begin()
    k.bx(-1.5, 1.5, -8.0, -7.7, 0.0, 0.3, 'stone')
    k.bx(-1.5, 1.5, 7.7, 8.0, 0.0, 0.3, 'stone')
    k.bx(-1.5, -1.2, -7.7, 7.7, 0.0, 0.3, 'stone')
    k.bx(1.2, 1.5, -7.7, 7.7, 0.0, 0.3, 'stone')
    k.qz(-1.2, 1.2, -7.7, 7.7, 0.12, 1, 'water2')
    k.qz(-0.32, 0.32, -7.4, 7.4, 0.126, 1, 'water')
    for i in range(10):
        x, y = rnd.uniform(-0.9, 0.9), -7.0 + i * 1.5 + rnd.uniform(-0.3, 0.3)
        if abs(x) < 0.42:
            x = 0.6 if x >= 0 else -0.6
        r = rnd.uniform(0.2, 0.3)
        pts = [(x + math.cos(t) * r, y + math.sin(t) * r, 0.132) for t in [0.4 + j / 7 * 1.8 * math.pi for j in range(8)]] + [(x, y, 0.132)]
        k.poly(pts, 'leaf', (0, 0, 1))
        if i % 3 == 0:
            bloom(k, x + 0.05, y, 0.17, 0.08, 'roseP', ink=True)
    for (x0, x1, y0, y1) in ((-1.5, 1.5, -8.0, -7.7), (-1.5, 1.5, 7.7, 8.0), (-1.5, -1.2, -7.7, 7.7), (1.2, 1.5, -7.7, 7.7)):
        k.wcol(x0, x1, y0, y1, 0.0, 0.3)
    k.finish('ReflectPool', ao=ao)

    # the grotto spring [4, 2] (back against the west wall): mossy rocks, a dark cave mouth, the cascade into a rock pool
    rnd = random.Random(454)
    k.begin()
    for (cx, cy, rx, ry, z0, h) in ((0.0, 0.5, 2.0, 0.5, 0.0, 3.2), (-1.55, -0.3, 0.45, 0.65, 0.0, 1.5), (1.55, -0.25, 0.45, 0.7, 0.0, 1.7)):
        pts = []
        for i in range(8):
            a = (i + rnd.uniform(-0.2, 0.2)) / 8 * 2 * math.pi
            pts.append((max(-2.0, min(2.0, cx + math.cos(a) * rx)), max(-1.0, min(1.0, cy + math.sin(a) * ry)), z0))
            pts.append((max(-1.95, min(1.95, cx + math.cos(a + 0.4) * rx * 0.8)), max(-0.95, min(0.95, cy + math.sin(a + 0.4) * ry * 0.8)), z0 + h * rnd.uniform(0.55, 0.8)))
        pts.append((cx, cy, z0 + h))
        k.hullp(pts, mosscol)
    k.hullp([(-0.55, 0.0, 0.25), (0.55, 0.0, 0.25), (-0.45, -0.05, 1.5), (0.45, -0.05, 1.5), (0.0, -0.06, 1.95), (0.0, 0.1, 0.9)], 'ink', ink=False)
    for (x, y) in ((-1.1, -0.9), (-0.4, -0.95), (0.4, -0.95), (1.1, -0.88)):
        k.hullp([(x + math.cos(t) * 0.24, y + math.sin(t) * 0.07, 0.0) for t in (0, 2, 4)] + [(x, y, 0.26)], mosscol)
    k.qz(-1.1, 1.1, -0.95, 0.0, 0.08, 1, 'water')
    for (x, a) in ((-1.4, 2.0), (-0.8, 1.6), (0.9, 1.2), (1.5, 0.9)):
        frond(k, (x, 0.6, 3.0 - abs(x) * 0.6), a, 1.0, 0.36, lift=0.6, droop=0.9, seg=2)
    k.col(-2.0, 2.0, 0.0, 1.0, 0.0, 3.2)
    k.col(-2.0, -1.12, -0.95, 0.0, 0.0, 1.4)
    k.col(1.12, 2.0, -0.95, 0.0, 0.0, 1.5)
    k.finish('Grotto', ao=ao)
    k.begin()
    k.poly([(-0.45, -0.12, 2.15), (0.45, -0.12, 2.15), (0.6, -0.5, 0.1), (-0.6, -0.5, 0.1)], 'water2', (0, -1, 0))
    k.poly([(-0.25, -0.16, 1.95), (0.25, -0.16, 1.95), (0.35, -0.53, 0.12), (-0.35, -0.53, 0.12)], 'foam', (0, -1, 0))
    k.cyl(0.0, -0.55, 0.08, 0.6, 0.75, 0.06, 'foam', seg=10, caps=False, ink=False)
    k.finish('Grotto_Spray', ao=False)
    # culvert [3, 1] (back against the east wall): the stream leaves under a stone arch through an iron grate
    rnd = random.Random(455)
    k.begin()
    k.bx(-1.5, 1.5, 0.1, 0.5, 0.0, 1.9, 'stone2')
    k.bx(-1.56, 1.56, 0.04, 0.5, 1.9, 2.05, 'stone')
    arch = [(-0.9, 0.094, 0.0), (0.9, 0.094, 0.0)] + [(math.cos(t) * 0.9, 0.094, 0.62 + math.sin(t) * 0.9) for t in [i / 8 * math.pi for i in range(9)]]
    k.poly(arch, 'ink', (0, -1, 0))
    for i in range(9):
        t = i / 8 * math.pi
        k.bxr(math.cos(t) * 1.04, 0.07, 0.62 + math.sin(t) * 1.04, 0.24, 0.07, 0.3, 'stone3', rot=(0, -math.degrees(t) + 90, 0))
    for i in range(7):
        x = -0.75 + i * 0.25
        h = 0.62 + math.sqrt(max(0.0, 0.9 ** 2 - x * x)) - 0.04
        k.cyl(x, 0.03, 0.0, 0.025, 0.025, h, 'iron', seg=4, ink=False)
    k.beam((-0.88, 0.03, 0.75), (0.88, 0.03, 0.75), 0.04, 'iron', ink=False)
    for x in (-1.2, 1.15):
        puff(k, rnd, x, 0.06, 0.05, 0.22, MOSS, n=5, flat=0.6, ink=False)
    frond(k, (1.3, 0.3, 2.05), 1.9, 0.8, 0.3, lift=0.5, droop=0.9, seg=2)
    k.col(-1.5, 1.5, -0.05, 0.5, 0.0, 2.05)
    k.finish('Culvert', ao=ao)


# ================================================================ the stone bridge [3, 5] (walk along Y) and stepping stones
def build_bridge(k, ao):
    rnd = random.Random(461)
    k.begin()

    def zu(y):
        return 0.72 * math.cos(math.pi * y / 3.0) if abs(y) < 1.5 else 0.0
    W, P = 1.5, 1.15
    for side in (-1, 1):
        for j in range(4):
            y0, y1 = sorted((side * (2.5 - j * 0.25), side * (2.25 - j * 0.25)))
            top = (j + 1) * RISE
            k.bx(-W, W, y0, y1, 0.0, top, stonecol)
            k.wcol(-P, P, y0, y1, max(0.0, top - 1.0), top)
            for s in (-1, 1):
                xa, xb = sorted((s * P, s * W))
                k.bx(xa, xb, y0, y1, top, top + 0.5, 'stone2')
                k.bx(xa - 0.02, xb + 0.02, y0, y1, top + 0.5, top + 0.58 + 0.004 * j, 'stone')
                k.col(xa, xb, y0, y1, 0.0, top + 0.58)
        for s in (-1, 1):   # end newels with ball finials
            xa, xb = sorted((s * (P - 0.045), s * (W + 0.035)))
            ya, yb = sorted((side * 2.515, side * 2.22))
            k.bx(xa, xb, ya, yb, 0.0, 0.82, 'stone')
            k.sph((xa + xb) / 2, (ya + yb) / 2, 0.98, 0.15, 'stone2', seg=(7, 4))
    ys = [-1.5 + i * 0.5 for i in range(7)]
    for ya, yb in zip(ys, ys[1:]):
        pts = [(x, y, z) for x in (-W, W) for y in (ya, yb) for z in (zu(y), 0.9)]
        k.hullp(pts, stonecol)
    for s in (-1, 1):
        xa, xb = sorted((s * P, s * W))
        k.bx(xa, xb, -1.5, 1.5, 0.9, 1.4, 'stone2')
        k.bx(xa - 0.02, xb + 0.02, -1.5, 1.5, 1.4, 1.5, 'stone')
        k.col(xa, xb, -1.5, 1.5, 0.0, 1.5)
        for i in range(6):   # voussoirs round the arch on both faces
            t0, t1 = -1.5 + i * 0.5, -1.0 + i * 0.5
            pts = [(s * (W + 0.005), t0, zu(t0)), (s * (W + 0.005), t1, zu(t1)), (s * (W + 0.005), t1, zu(t1) + 0.2), (s * (W + 0.005), t0, zu(t0) + 0.2)]
            k.poly(pts, 'stone3' if i % 2 else 'stoneD', (s, 0, 0))
    k.wcol(-P, P, -1.5, 1.5, 0.0, 0.9)
    for (x, y) in ((-1.3, -1.6), (1.35, 1.7), (1.3, -2.1)):
        puff(k, rnd, x, y, 0.9 if abs(y) < 1.5 else 0.4, 0.16, MOSS, n=5, flat=0.5, ink=False)
    k.finish('Bridge', ao=ao)
    rnd = random.Random(462)
    k.begin()
    for (cx, cy, r) in ((-0.15, -0.1, 0.34), (0.28, 0.25, 0.22)):
        pts = []
        for i in range(7):
            a = (i + rnd.uniform(-0.2, 0.2)) / 7 * 2 * math.pi
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.85, 0.0))
            pts.append((cx + math.cos(a + 0.4) * r * 0.85, cy + math.sin(a + 0.4) * r * 0.75, 0.13))
        k.hullp(pts, mosscol)
    k.finish('SteppingStone', ao=ao)


# ================================================================ the glasshouse [14, 10] (long axis X, doors W / E / S)
def vault(y, t):
    return (y * math.cos(t), 3.75 + 2.55 * math.sin(t))


def build_glasshouse(k, ao):
    rnd = random.Random(471)
    k.begin()
    D = 1.1
    k.bx(-6.95, 6.95, -4.65, 4.65, 0.0, 0.04, 'gravel', ink=False)
    k.bx(-D + 0.03, D - 0.03, -4.98, -4.65, 0.0, 0.04, 'gravel', ink=False)
    walls = [(-7.0, 7.0, 4.7, 5.0), (-7.0, -D, -5.0, -4.7), (D, 7.0, -5.0, -4.7),
             (-7.0, -6.7, -4.7, -D), (-7.0, -6.7, D, 4.7), (6.7, 7.0, -4.7, -D), (6.7, 7.0, D, 4.7)]
    for (x0, x1, y0, y1) in walls:
        k.bx(x0, x1, y0, y1, 0.0, 0.6, 'stone3')
        if y1 - y0 < 0.5:   # long walls: the cap overhangs both faces; end walls stop short of the long walls' caps
            k.bx(x0, x1, y0 - 0.02, y1 + 0.02, 0.6, 0.66, 'stone')
        else:
            k.bx(x0 - 0.02, x1 + 0.02, max(y0, -4.66), min(y1, 4.66), 0.6, 0.66, 'stone')
        k.col(x0, x1, y0, y1, 0.0, 3.75)
    for (x0, x1, y0, y1) in ((-7.0, -6.7, -D, D), (6.7, 7.0, -D, D), (-D, D, -5.0, -4.7)):
        k.bx(x0, x1, y0, y1, 2.7, 2.82, 'frame')
        k.col(x0, x1, y0, y1, 2.7, 3.75)
    # frame: corner and door posts, mullions, eave beam, sill rail
    for (x, y) in ((-6.9, -4.9), (6.9, -4.9), (-6.9, 4.9), (6.9, 4.9)):
        k.bx(x - 0.135, x + 0.135, y - 0.135, y + 0.135, 0.0, 3.85, 'frame')
    for (x, y) in ((-6.85, -D - 0.065), (-6.85, D + 0.065), (6.85, -D - 0.065), (6.85, D + 0.065), (-D - 0.065, -4.85), (D + 0.065, -4.85)):
        k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 3.75, 'frame')
    for i in range(13):
        x = -6.0 + i
        k.bx(x - 0.03, x + 0.03, 4.82, 4.88, 0.66, 3.6, 'frame', ink=False)
        if abs(x) > D + 0.2:
            k.bx(x - 0.03, x + 0.03, -4.88, -4.82, 0.66, 3.6, 'frame', ink=False)
    for i in range(9):
        y = -4.0 + i
        if abs(y) > D + 0.2:
            for x in (-6.85, 6.85):
                k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.66, 3.6, 'frame', ink=False)
    for (x0, x1, y0, y1) in ((-7.0, 7.0, 4.8, 4.98), (-7.0, 7.0, -4.98, -4.8), (-6.98, -6.8, -4.8, 4.8), (6.8, 6.98, -4.8, 4.8)):
        k.bx(x0, x1, y0, y1, 3.6, 3.76, 'frame')
    for (x0, x1, y0, y1) in ((-7.0, 7.0, 4.84, 4.9), (-7.0, -D, -4.9, -4.84), (D, 7.0, -4.9, -4.84)):
        k.bx(x0, x1, y0, y1, 1.9, 1.95, 'frame', ink=False)
    # vault ribs (ink on the gable arches), purlins, the ridge lantern
    T = [i / 8 * math.pi for i in range(9)]
    for x in (-6.9, -4.0, -2.0, 0.0, 2.0, 4.0, 6.9):
        pts = [(x,) + vault(4.9, t) for t in T]
        for a, b in zip(pts, pts[1:]):
            k.beam((a[0], a[1], a[2]), (b[0], b[1], b[2]), 0.09 if abs(x) > 6 else 0.06, 'frame', ink=abs(x) > 6)
    for t in (T[2], T[4], T[6]):
        y, z = vault(4.92, t)
        k.beam((-6.9, y, z), (6.9, y, z), 0.05, 'frame', ink=False)
    for x in (-6.9, 6.9):
        for t, y0 in ((T[2], 1.2), (T[4], 0.0), (T[6], -1.2)):
            y, z = vault(4.88, t)
            k.beam((x, y0, 3.78), (x, y, z), 0.04, 'frame', ink=False)
    for (x, y) in ((-5.0, -1.0), (5.0, -1.0), (-5.0, 1.0), (5.0, 1.0)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 6.15, 7.0, 'frame')
    for y in (-1.0, 1.0):
        k.bx(-5.05, 5.05, y - 0.06, y + 0.06, 7.0, 7.1, 'frame')
    k.hullp([(x, y, 7.1) for x in (-5.15, 5.15) for y in (-1.15, 1.15)] + [(x, 0.0, 7.65) for x in (-5.15, 5.15)], zcol('verd', 'verd', 'iron', 0.3))
    for i in range(11):
        x = -5.0 + i
        k.cyl(x, 0.0, 7.62, 0.03, 0.0, 0.32, 'verd', seg=4, ink=False)
    for x in (-7.0, 7.0):
        k.sph(x, 0.0, 6.55, 0.14, 'verd', seg=(6, 4))
    # interior: raised beds, the lily pool, two parasol palms, exotic plants, hanging vines
    beds = [(-6.4, 6.4, 3.1, 4.6), (-6.4, -1.7, -4.6, -3.1), (1.7, 6.4, -4.6, -3.1)]
    for (x0, x1, y0, y1) in beds:
        k.bx(x0, x1, y0, y1, 0.0, 0.5, 'stone2')
        k.bx(x0 + 0.1, x1 - 0.1, y0 + 0.1, y1 - 0.1, 0.5, 0.52, 'soil', ink=False)
        k.col(x0, x1, y0, y1, 0.0, 0.52)
    k.cyl(0, 0, 0.0, 1.5, 1.5, 0.45, 'stone', seg=14)
    k.disc(0, 0, 0.456, 1.38, 'water', n=14)
    for (x, y, r) in ((-0.5, 0.35, 0.42), (0.55, -0.2, 0.36), (0.1, -0.75, 0.3)):
        k.disc(x, y, 0.464, r, 'leaf', n=8)
    bloom(k, 0.6, -0.15, 0.5, 0.1, 'roseP', ink=True)
    k.col(-1.5, 1.5, -1.5, 1.5, 0.0, 0.46)
    for sx in (-4.0, 4.0):
        k.cyl(sx, 0, 0.0, 0.9, 0.9, 0.45, 'stone2', seg=10)
        k.cyl(sx, 0, 0.45, 0.8, 0.8, 0.02, 'soil', seg=10, ink=False)
        for i in range(5):
            z0 = 0.47 + i * 0.85
            k.tube((sx + 0.04 * i, 0.02 * i, z0 - 0.015), (sx + 0.04 * (i + 1), 0.02 * (i + 1), z0 + 0.85), 0.17 - i * 0.015, 0.14 - i * 0.015, 'bark' if i % 2 else 'barkL', seg=7)
        tx, ty = sx + 0.2, 0.1
        for i in range(8):
            a = i / 8 * 2 * math.pi + sx
            frond(k, (tx, ty, 4.75), a, rnd.uniform(1.9, 2.3), 0.66, lift=0.35, droop=0.55, seg=2, col=zcol('fern', 'leaf', 'leafD', 0.45))
        k.col(sx - 0.9, sx + 0.9, -0.9, 0.9, 0.0, 0.45)
        k.col(sx - 0.2, sx + 0.2, -0.2, 0.2, 0.45, 4.7)
    # skyleaf bananas (paddle leaves) and rosettes on the north bed, dragon-tongue on the south beds
    for x in (-5.0, -1.2, 2.6):
        k.tube((x, 3.85, 0.5), (x + 0.05, 3.9, 1.9), 0.12, 0.09, 'leafD', seg=6)
        for i in range(5):
            a = i / 5 * 2 * math.pi + x
            frond(k, (x + 0.05, 3.9, 1.85), a, 1.6, 0.66, lift=0.5, droop=0.55, seg=2, col=zcol('leafL', 'leaf', 'leafD', 0.4))
    for x in (-3.2, 0.6, 4.6):
        for i in range(6):
            a = i / 6 * 2 * math.pi
            frond(k, (x, 3.85, 0.55), a, 0.6, 0.18, lift=0.9, droop=0.6, seg=1, col=zcol('tulipO', 'red', 'tulip', 0.4))
    for x in (-5.2, 3.0):
        for i in range(6):
            a = i / 6 * 2 * math.pi + 0.3
            dx, dy = math.cos(a), math.sin(a)
            k.hullp([(x + dx * 0.05, -3.85 + dy * 0.05, 0.52), (x - dy * 0.05, -3.85 + dx * 0.05, 0.52), (x + dx * 0.3, -3.85 + dy * 0.3, 1.1 + 0.1 * (i % 2))], 'red' if i % 2 else 'tulipO', ink=False)
    for i in range(5):
        x = -5.0 + i * 2.5
        y, z = vault(4.9, T[2] if i % 2 else T[6])
        L = rnd.uniform(1.2, 2.0)
        k.beam((x, y * 0.98, z - 0.05), (x + 0.1, y * 0.96, z - L), 0.025, 'leafD', ink=False)
        for j in range(3):
            puff(k, rnd, x + 0.05, y * 0.96, z - L * (0.35 + 0.3 * j), 0.11, 'leaf', n=4, flat=0.8, ink=False)
    k.finish('Landmark_Glasshouse', ao=ao)
    # glass (additive companion): walls, transoms over the doors, the vault, the gable fans, the lantern
    k.begin()
    G = 'pod'
    k.qy(-6.95, 6.95, 0.66, 3.6, 4.85, 1, G)
    for (x0, x1) in ((-6.95, -D), (D, 6.95)):
        k.qy(x0, x1, 0.66, 3.6, -4.85, -1, G)
    k.qy(-D, D, 2.82, 3.6, -4.85, -1, G)
    for x, s in ((-6.85, -1), (6.85, 1)):
        k.qx(-4.85, -D, 0.66, 3.6, x, s, G)
        k.qx(D, 4.85, 0.66, 3.6, x, s, G)
        k.qx(-D, D, 2.82, 3.6, x, s, G)
        k.poly([(x, ) + vault(4.85, t) for t in T], G, (s, 0, 0))
    for a, b in zip(T, T[1:]):
        (ya, za), (yb, zb) = vault(4.88, a), vault(4.88, b)
        k.poly([(-6.9, ya, za), (6.9, ya, za), (6.9, yb, zb), (-6.9, yb, zb)], G, (0, (ya + yb) / 2, (za + zb) / 2 - 3.75))
    for y, s in ((-1.0, -1), (1.0, 1)):
        k.qy(-5.0, 5.0, 6.2, 7.0, y, s, G)
    k.finish('Glasshouse_Glass', ao=False)


# ================================================================ the gazebo [5, 5] (openings north and south)
def octa(r, z, a0=math.pi / 8):
    return ring(0, 0, r, 8, z, a0)


def build_gazebo(k, ao):
    rnd = random.Random(481)
    k.begin()
    k.hullp(octa(2.45, 0.0) + octa(2.45, 0.18), stonecol)
    k.hullp(octa(2.2, 0.17) + octa(2.2, 0.36), stonecol)
    cols = [(math.cos(math.pi / 8 + i * math.pi / 4) * 2.0, math.sin(math.pi / 8 + i * math.pi / 4) * 2.0) for i in range(8)]
    for (x, y) in cols:
        k.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.36, 0.5, 'frame')
        k.cyl(x, y, 0.5, 0.07, 0.07, 2.3, 'frame', seg=6)
        k.bx(x - 0.09, x + 0.09, y - 0.09, y + 0.09, 2.8, 2.9, 'frame')
        k.col(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.36, 2.9)
    for i in range(8):
        a, b = cols[i], cols[(i + 1) % 8]
        k.beam((a[0], a[1], 2.86), (b[0], b[1], 2.86), 0.1, 'frame')
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        k.hullp([(a[0] * 0.97, a[1] * 0.97, 2.8), (b[0] * 0.97, b[1] * 0.97, 2.8), (mx * 0.97, my * 0.97, 2.45)], 'frame', ink=False)
        if i in (1, 5):   # the north and south sides stay open
            continue
        for z, t in ((0.55, 0.06), (1.22, 0.08)):
            k.beam((a[0], a[1], z), (b[0], b[1], z), t, 'frame', ink=z > 1)
        for j in range(1, 4):
            u = j / 4
            x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
            k.cyl(x, y, 0.58, 0.025, 0.025, 0.62, 'frame', seg=4, ink=False)
    k.cyl(0, 0, 2.86, 2.58, 1.9, 0.55, 'verd', seg=8)
    k.cyl(0, 0, 3.41, 1.9, 0.95, 0.75, 'verd', seg=8)
    k.cyl(0, 0, 4.16, 0.95, 0.2, 0.8, 'verd', seg=8)
    k.sph(0, 0, 5.05, 0.15, 'bronze', seg=(7, 4))
    k.cyl(0, 0, 5.15, 0.04, 0.0, 0.45, 'bronze', seg=4)
    for i in range(8):
        a = i * math.pi / 4
        k.beam((math.cos(a) * 2.5, math.sin(a) * 2.5, 2.87), (math.cos(a) * 1.0, math.sin(a) * 1.0, 4.2), 0.05, 'iron', ink=False)
    for s in (-1, 1):   # benches along the east and west sides
        x = s * 1.45
        k.bx(x - 0.22, x + 0.22, -0.75, 0.75, 0.78, 0.84, 'wood')
        for y in (-0.6, 0.6):
            k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.36, 0.78, 'wood2')
        k.col(x - 0.22, x + 0.22, -0.75, 0.75, 0.36, 0.84)
    k.wcol(-2.26, 2.26, -0.94, 0.94, 0.0, 0.18)
    k.wcol(-0.94, 0.94, -2.26, 2.26, 0.0, 0.18)
    k.wcol(-1.6, 1.6, -1.6, 1.6, 0.0, 0.18)
    k.wcol(-2.03, 2.03, -0.84, 0.84, 0.0, 0.36)
    k.wcol(-0.84, 0.84, -2.03, 2.03, 0.0, 0.36)
    k.wcol(-1.44, 1.44, -1.44, 1.44, 0.0, 0.36)
    # rails: the east / west sides are axis-aligned, the four diagonal ones are boxed (col_fit trims them)
    for i in range(8):
        if i in (1, 5):
            continue
        a, b = cols[i], cols[(i + 1) % 8]
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        if x1 - x0 < 0.1:
            x0, x1 = x0 - 0.06, x1 + 0.06
        k.col(x0, x1, y0, y1, 0.36, 1.28)
    k.finish('Gazebo', ao=ao)


# ================================================================ the ruined folly [7, 7] (a broken tholos)
def build_folly(k, ao):
    rnd = random.Random(491)
    k.begin()
    for (r, z0, z1) in ((3.45, 0.0, 0.18), (3.2, 0.17, 0.36), (2.95, 0.35, 0.54)):
        k.hullp(ring(0, 0, r, 16, z0, 0.1) + ring(0, 0, r, 16, z1, 0.1), mosscol)
    A = [math.pi / 8 + i * math.pi / 4 for i in range(8)]
    broken = {5: 2.2, 6: 0.95, 7: 1.55}
    R = 2.5
    for i, a in enumerate(A):
        x, y = math.cos(a) * R, math.sin(a) * R
        k.bx(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.54, 0.74, 'stone2')
        top = broken.get(i, 3.9)
        if i in broken:
            k.cyl(x, y, 0.74, 0.24, 0.23, top - 0.75, stonecol, seg=8)
            pts = ring(x, y, 0.23, 8, top - 0.02, 0.2)
            for j in range(3):
                b = rnd.uniform(0, 6.28)
                pts.append((x + math.cos(b) * 0.12, y + math.sin(b) * 0.12, top + rnd.uniform(0.08, 0.22)))
            k.hullp(pts, stonecol)
            k.col(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.54, top + 0.1)
        else:
            k.cyl(x, y, 0.74, 0.24, 0.21, 3.16, stonecol, seg=8)
            k.bx(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 3.9, 4.1, 'stone2')
            k.bx(x - 0.36, x + 0.36, y - 0.36, y + 0.36, 4.1, 4.2, 'stone')
            k.col(x - 0.36, x + 0.36, y - 0.36, y + 0.36, 0.54, 4.2)
    # what is left of the entablature: four spans over the standing columns 0-4, a cornice, three dome ribs
    rm = R * math.cos(math.pi / 8)
    L = 2 * R * math.sin(math.pi / 8) + 0.5
    for j in range(4):
        am = (A[j] + A[j + 1]) / 2
        e = 0.012 * (j % 2)
        k.bxr(math.cos(am) * rm, math.sin(am) * rm, 4.45 + e, L, 0.55, 0.5, 'stone', rot=(0, 0, math.degrees(am) + 90))
        k.bxr(math.cos(am) * rm, math.sin(am) * rm, 4.76 + e, L + 0.1, 0.68, 0.12, 'stone2', rot=(0, 0, math.degrees(am) + 90))
    for j, frac in ((1, 1.0), (2, 0.62), (3, 1.0)):
        a = A[j]
        pts = [(math.cos(a) * 2.35 * math.cos(t * math.pi / 2), math.sin(a) * 2.35 * math.cos(t * math.pi / 2), 4.82 + 1.75 * math.sin(t * math.pi / 2))
               for t in [i / 4 * frac for i in range(5)]]
        for p, q in zip(pts, pts[1:]):
            k.beam(p, q, 0.24, 'stone')
    sh = []
    for a in (A[1] + 0.12, (A[1] + A[2]) / 2, A[2] - 0.12):
        for t in (0.08, 0.3, 0.5):
            for rr in (2.3, 2.12):
                sh.append((math.cos(a) * rr * math.cos(t * math.pi / 2), math.sin(a) * rr * math.cos(t * math.pi / 2), 4.85 + (rr - 0.55) * math.sin(t * math.pi / 2)))
    k.hullp(sh, stonecol)
    # centre: a pedestal and an urn of lavender; fallen drums and a capital on the platform
    k.bx(-0.32, 0.32, -0.32, 0.32, 0.54, 1.3, 'stone')
    k.bx(-0.38, 0.38, -0.38, 0.38, 1.3, 1.4, 'stone2')
    urn(k, 0.0, 0.0, 1.4, 1.1, fl='lav', rnd=rnd)
    k.col(-0.38, 0.38, -0.38, 0.38, 0.54, 2.3)
    for (r, a, az, h) in ((1.55, A[6] + 0.2, 30, 0.6), (1.7, A[5] - 0.35, 110, 0.5)):
        x, y = math.cos(a) * r, math.sin(a) * r
        k.cyl(x, y, 0.78, 0.23, 0.23, h, stonecol, seg=8, rot=(90, 0, az))
        k.col(x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0.54, 1.0)
    a = A[7] - 0.3
    k.bxr(math.cos(a) * 1.4, math.sin(a) * 1.4, 0.68, 0.64, 0.64, 0.28, 'stone2', rot=(8, 4, 25))
    # ivy and moss
    for (i, z, r) in ((1, 3.2, 0.3), (1, 2.6, 0.26), (3, 3.4, 0.3), (5, 1.8, 0.26), (0, 1.4, 0.24)):
        x, y = math.cos(A[i]) * (R + 0.25), math.sin(A[i]) * (R + 0.25)
        puff(k, rnd, x, y, z, r, LEAF, n=5, flat=0.9, ink=False)
    for j in range(10):
        a = rnd.uniform(0, 6.28)
        r = rnd.choice((3.42, 3.18, 2.92))
        puff(k, rnd, math.cos(a) * r, math.sin(a) * r, {3.42: 0.18, 3.18: 0.36, 2.92: 0.54}[r], 0.18, MOSS, n=5, flat=0.5, ink=False)
    for (r, z0, z1, ap, sq) in ((3.38, 0.0, 0.18, 1.4, 2.4), (3.14, 0.0, 0.36, 1.3, 2.22), (2.89, 0.0, 0.54, 1.2, 2.05)):
        k.wcol(-r, r, -ap, ap, z0, z1)
        k.wcol(-ap, ap, -r, r, z0, z1)
        k.wcol(-sq, sq, -sq, sq, z0, z1)
    k.finish('Landmark_Folly', ao=ao)


# ================================================================ props
def build_props(k, ao):
    k.begin()
    bench(k, 0.0, 0.0)
    k.col(-0.95, 0.95, -0.3, 0.29, 0.0, 0.47)
    k.col(-0.95, 0.95, 0.18, 0.29, 0.47, 0.92)
    k.finish('Bench', ao=ao)
    # lamp post (the lantern glows: LampPost_Glow)
    k.begin()
    k.bx(-0.17, 0.17, -0.17, 0.17, 0.0, 0.3, 'iron')
    k.cyl(0, 0, 0.3, 0.07, 0.05, 2.45, 'iron', seg=6)
    k.cyl(0, 0, 1.0, 0.075, 0.075, 0.08, 'bronze', seg=6, ink=False)
    k.bx(-0.13, 0.13, -0.13, 0.13, 2.72, 2.77, 'iron')
    for (x, y) in ((-0.13, -0.13), (0.13, -0.13), (-0.13, 0.13), (0.13, 0.13)):
        k.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 2.77, 3.1, 'iron', ink=False)
    k.hullp([(x, y, 3.1) for x in (-0.18, 0.18) for y in (-0.18, 0.18)] + [(0, 0, 3.35)], 'iron')
    k.cyl(0, 0, 3.35, 0.04, 0.0, 0.15, 'iron', seg=4, ink=False)
    k.col(-0.17, 0.17, -0.17, 0.17, 0.0, 2.75)
    k.finish('LampPost', ao=ao)
    k.begin()
    k.bx(-0.11, 0.11, -0.11, 0.11, 2.78, 3.08, 'amber', ink=False)
    k.finish('LampPost_Glow', ao=False)
    # urn on a pedestal (flowers repainted like the tulip beds)
    rnd = random.Random(501)
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.14, 'stone2')
    k.bx(-0.22, 0.22, -0.22, 0.22, 0.14, 0.72, 'stone')
    k.bx(-0.28, 0.28, -0.28, 0.28, 0.72, 0.82, 'stone2')
    urn(k, 0.0, 0.0, 0.82, 0.95, fl='tulip', rnd=rnd)
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 1.45)
    k.finish('Urn', ao=ao)
    # sundial and armillary sphere on pedestals
    k.begin()
    k.cyl(0, 0, 0.0, 0.32, 0.3, 0.12, 'stone2', seg=8)
    k.cyl(0, 0, 0.12, 0.17, 0.14, 0.72, 'stone', seg=8)
    k.cyl(0, 0, 0.84, 0.3, 0.3, 0.08, 'stone2', seg=10)
    k.cyl(0, 0, 0.92, 0.26, 0.26, 0.025, 'bronze', seg=12)
    k.hullp([(-0.2, -0.012, 0.945), (0.12, -0.012, 0.945), (-0.2, -0.012, 1.12), (-0.2, 0.012, 0.945), (0.12, 0.012, 0.945), (-0.2, 0.012, 1.12)], 'bronze')
    for i in range(12):
        a = i / 12 * 2 * math.pi
        k.qz(math.cos(a) * 0.2 - 0.008, math.cos(a) * 0.2 + 0.008, math.sin(a) * 0.2 - 0.008, math.sin(a) * 0.2 + 0.008, 0.95, 1, 'ink')
    k.col(-0.32, 0.32, -0.32, 0.32, 0.0, 1.0)
    k.finish('Sundial', ao=ao)
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.14, 'stone2')
    k.bx(-0.2, 0.2, -0.2, 0.2, 0.14, 1.0, 'stone')
    k.bx(-0.26, 0.26, -0.26, 0.26, 1.0, 1.08, 'stone2')
    C, Rr = (0.0, 0.0, 1.55), 0.42
    rings = [lambda t: (math.cos(t) * Rr, math.sin(t) * Rr, 0.0),
             lambda t: (math.cos(t) * Rr, 0.0, math.sin(t) * Rr),
             lambda t: (math.cos(t) * Rr, math.sin(t) * Rr * math.cos(0.41), math.sin(t) * Rr * math.sin(0.41))]
    for ri, fn in enumerate(rings):
        pts = [fn(i / 10 * 2 * math.pi) for i in range(11)]
        for a, b in zip(pts, pts[1:]):
            k.beam((C[0] + a[0], C[1] + a[1], C[2] + a[2]), (C[0] + b[0], C[1] + b[1], C[2] + b[2]), 0.035, 'bronze', ink=ri == 0)
    k.beam((0, 0.2, 1.1), (0, -0.25, 2.0), 0.03, 'bronze', ink=False)
    k.sph(C[0], C[1], C[2], 0.08, 'bronze', seg=(6, 4))
    k.cyl(0, 0, 1.08, 0.06, 0.05, 0.08, 'bronze', seg=6, ink=False)
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 2.0)
    k.finish('Armillary', ao=ao)
    # finger signposts (dark green boards, white lettering, both faces)
    for name, words in (('Signpost_A', ((20, 'FOUNTAIN'), (150, 'GLASSHOUSE'), (265, 'TERRACE'))),
                        ('Signpost_B', ((35, 'THE FOLLY'), (160, 'THE MAZE'), (285, 'POTTING SHED')))):
        k.begin()
        k.bx(-0.07, 0.07, -0.07, 0.07, 0.0, 2.45, 'wood2')
        k.cyl(0, 0, 2.45, 0.1, 0.02, 0.14, 'wood2', seg=4)
        for j, (deg, w) in enumerate(words):
            z = 2.15 - j * 0.32
            k.push(0, 0, deg)
            k.bx(0.08, 1.05, -0.03, 0.03, z, z + 0.22, 'iron')
            k.hullp([(1.05, -0.03, z), (1.05, 0.03, z), (1.05, -0.03, z + 0.22), (1.05, 0.03, z + 0.22), (1.18, -0.03, z + 0.11), (1.18, 0.03, z + 0.11)], 'iron')
            k.text(w, 0.58, -0.034, z + 0.05, 0.12, 'tulipW', maxw=0.86, font='display')
            k.text(w, 0.58, 0.034, z + 0.05, 0.12, 'tulipW', face='y+', maxw=0.86, font='display')
            k.pop()
        k.col(-0.1, 0.1, -0.1, 0.1, 0.0, 2.45)
        k.finish(name, ao=ao)
    # tea table [2, 2]: a round white iron table, two chairs, a teapot and cups
    k.begin()
    k.cyl(0, 0, 0.0, 0.26, 0.22, 0.04, 'frame', seg=8)
    k.cyl(0, 0, 0.04, 0.04, 0.04, 0.66, 'frame', seg=5)
    k.cyl(0, 0, 0.7, 0.4, 0.4, 0.04, 'frame', seg=12)
    k.sph(0.08, 0.05, 0.84, 0.1, 'tulipW', seg=(7, 4), scale=(1, 1, 0.85))
    k.beam((0.17, 0.05, 0.84), (0.27, 0.05, 0.9), 0.025, 'tulipW', ink=False)
    for (x, y) in ((-0.2, -0.12), (-0.12, 0.22)):
        k.cyl(x, y, 0.74, 0.04, 0.05, 0.06, 'tulipW', seg=6)
    for s in (-1, 1):
        x = s * 0.66
        k.bx(x - 0.22, x + 0.22, -0.22, 0.22, 0.44, 0.48, 'frame')
        for (dx, dy) in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
            k.cyl(x + dx, dy, 0.0, 0.018, 0.018, 0.44, 'frame', seg=4, ink=False)
        xb = x + s * 0.2
        k.bx(xb - 0.025, xb + 0.025, -0.2, 0.2, 0.48, 0.95, 'frame')
        k.col(x - 0.22, x + 0.22, -0.22, 0.22, 0.0, 0.48)
        k.col(xb - 0.04, xb + 0.04, -0.2, 0.2, 0.48, 0.95)
    k.col(-0.4, 0.4, -0.4, 0.4, 0.0, 0.74)
    k.finish('TeaTable', ao=ao)
    # the maze arch [4, 1]: yew pillars, a clipped yew arch over the 2 m opening, a hanging iron sign
    k.begin()
    from mg_plants import hedge_box
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.0, s * 2.0))
        hedge_box(k, x0, x1, -0.47, 0.47, 2.75, ch=0.12)
        k.col(x0, x1, -0.47, 0.47, 0.0, 2.75)
    for i in range(6):
        t0, t1 = i / 6 * math.pi, (i + 1) / 6 * math.pi
        pts = []
        for t in (t0, t1):
            for r in (1.0, 1.55):
                for y in (-0.42, 0.42):
                    pts.append((math.cos(t) * r * (0.995 if t == t0 and i else 1.0), y * (1.0 - 0.035 * (i % 2)), 2.25 + math.sin(t) * r * 0.8))
        k.hullp(pts, HEDGE)
    for x in (-0.4, 0.4):
        k.beam((x, 0, 3.05), (x, 0, 2.82), 0.015, 'iron', ink=False)
    k.bx(-0.55, 0.55, -0.03, 0.03, 2.5, 2.82, 'iron')
    k.text('THE MAZE', 0.0, -0.034, 2.58, 0.16, 'tulipW', maxw=0.95)
    k.text('THE MAZE', 0.0, 0.034, 2.58, 0.16, 'tulipW', face='y+', maxw=0.95)
    k.finish('MazeArch', ao=ao)
    build_nursery(k, ao)


def build_nursery(k, ao):
    # potting shed [5, 4] (front -Y): board walls, slate roof, a green door, windows with flower boxes, a sign
    rnd = random.Random(511)
    k.begin()
    k.bx(-2.3, 2.3, -1.6, 1.7, 0.0, 2.4, 'wood')
    for i in range(1, 18):
        x = -2.3 + i * 0.25
        if -0.55 < x < 0.55:
            continue
        k.qy(x - 0.012, x + 0.012, 0.05, 2.38, -1.605, -1, 'wood2')
    for s in (-1, 1):
        k.hullp([(s * 2.3, y, 2.4) for y in (-1.6, 1.7)] + [(s * 2.3, 0.05, 3.35)] + [(s * 2.2, y, 2.4) for y in (-1.6, 1.7)] + [(s * 2.2, 0.05, 3.35)], 'wood')
    k.hullp([(x, y, 2.28) for x in (-2.55, 2.55) for y in (-2.0, 2.1)] + [(x, 0.05, 3.5) for x in (-2.55, 2.55)] +
            [(x, y, 2.36) for x in (-2.55, 2.55) for y in (-2.0, 2.1)], zcol('slate', 'slate', 'wood2', 0.2, -0.2))
    k.bx(-2.6, 2.6, -0.04, 0.14, 3.48, 3.58, 'wood2')
    k.bx(-0.5, 0.5, -1.64, -1.6, 0.0, 2.05, 'frame')
    k.bx(-0.42, 0.42, -1.66, -1.62, 0.04, 1.98, 'verd')
    k.cyl(0.3, -1.67, 1.0, 0.035, 0.035, 0.04, 'bronze', seg=6, rot=(90, 0, 0), ink=False)
    for x in (-1.45, 1.45):
        k.bx(x - 0.48, x + 0.48, -1.64, -1.6, 1.0, 1.9, 'frame')
        k.qy(x - 0.4, x + 0.4, 1.08, 1.82, -1.645, -1, 'glass')
        k.bx(x - 0.03, x + 0.03, -1.66, -1.64, 1.08, 1.82, 'frame', ink=False)
        k.bx(x - 0.5, x + 0.5, -1.92, -1.6, 0.78, 0.98, 'terra')
        for j in range(5):
            bloom(k, x - 0.38 + j * 0.19, -1.78, 1.08 + (j % 2) * 0.05, 0.08, 'tulipP' if j % 2 else 'tulipY', ink=True)
    k.bx(-0.85, 0.85, -1.66, -1.6, 2.1, 2.36, 'frame')
    k.text('POTTING SHED', 0.0, -1.665, 2.16, 0.14, 'iron', maxw=1.6)
    for (x, top, head) in ((1.0, 1.6, 'rake'), (1.25, 1.5, 'spade')):
        k.beam((x, -1.95, 0.02), (x + 0.12, -1.66, top), 0.035, 'woodL', ink=False)
        if head == 'rake':
            k.bx(x - 0.18, x + 0.18, -1.99, -1.92, 0.0, 0.06, 'iron', ink=False)
        else:
            k.bx(x - 0.1, x + 0.1, -1.98, -1.94, 0.0, 0.26, 'iron', ink=False)
    k.col(-2.3, 2.3, -1.6, 1.7, 0.0, 2.4)
    k.finish('Shed', ao=ao)
    # potting bench [2, 1] (front -Y)
    rnd = random.Random(512)
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.38, 0.82, 0.88, 'wood')
    for (x, y) in ((-0.88, -0.33), (0.88, -0.33), (-0.88, 0.32), (0.88, 0.32)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.82, 'wood2')
    k.bx(-0.9, 0.9, -0.36, 0.34, 0.22, 0.26, 'wood2')
    k.bx(-0.95, 0.95, 0.38, 0.44, 0.0, 1.5, 'wood2')
    k.bx(-0.95, 0.95, 0.2, 0.38, 1.25, 1.29, 'wood')
    for i in range(5):
        x = -0.75 + i * 0.36
        k.cyl(x, 0.29, 1.29, 0.06, 0.08, 0.13, 'terra', seg=7)
    k.bx(-0.75, -0.05, -0.3, 0.15, 0.88, 0.94, 'terra2')
    for j in range(6):
        x, y = -0.65 + (j % 3) * 0.24, -0.18 + (j // 3) * 0.22
        bloom(k, x, y, 0.99, 0.06, 'leafL')
    k.cyl(0.45, -0.05, 0.88, 0.13, 0.11, 0.24, 'verd', seg=8)
    k.beam((0.55, -0.05, 0.96), (0.8, -0.05, 1.18), 0.03, 'verd', ink=False)
    k.beam((0.36, -0.05, 1.12), (0.54, -0.05, 1.12), 0.025, 'verd', ink=False)
    for i, (x, h) in enumerate(((0.32, 0.15), (0.06, 0.12), (-0.22, 0.17))):
        k.cyl(x, -0.2, 0.26, 0.07 + i * 0.01, 0.09 + i * 0.01, h, 'terra', seg=7)
    k.col(-0.95, 0.95, -0.4, 0.44, 0.0, 0.94)
    k.col(-0.95, 0.95, 0.2, 0.44, 0.94, 1.5)
    k.finish('PottingBench', ao=ao)
    # cold frame [2, 1]: a timber box of seedlings, its glass lid propped open
    k.begin()
    k.bx(-0.95, 0.95, -0.45, 0.45, 0.0, 0.35, 'wood')
    k.bx(-0.88, 0.88, -0.38, 0.38, 0.35, 0.37, 'soil', ink=False)
    for j in range(10):
        bloom(k, -0.72 + (j % 5) * 0.36, -0.15 + (j // 5) * 0.3, 0.44, 0.07, 'leafL')
    k.bxr(0.0, 0.62, 0.68, 1.9, 0.62, 0.04, 'frame', rot=(-55, 0, 0))
    k.bxr(0.0, 0.62, 0.68, 1.78, 0.52, 0.052, 'glass', rot=(-55, 0, 0), ink=False)
    k.beam((0.85, -0.3, 0.35), (0.85, 0.35, 0.92), 0.03, 'wood2', ink=False)
    k.col(-0.95, 0.95, -0.45, 0.45, 0.0, 0.4)
    k.finish('ColdFrame', ao=ao)
    # compost bays [2, 1]
    rnd = random.Random(513)
    k.begin()
    k.bx(-0.95, 0.95, 0.32, 0.42, 0.0, 0.9, 'wood2')
    for x in (-0.95, 0.0, 0.95):
        k.bx(x - 0.05, x + 0.05, -0.42, 0.32, 0.0, 0.86, 'wood')
    for x0, x1 in ((-0.9, -0.05), (0.05, 0.9)):
        k.bx(x0, x1, -0.42, -0.36, 0.0, 0.32, 'wood2')
        blob(k, rnd, (x0 + x1) / 2, 0.0, 0.0, 0.38, 0.32, 0.62, zcol('soil2', 'soil', 'soil', 0.4), n=5)
    k.beam((0.6, -0.5, 0.0), (0.7, -0.38, 1.1), 0.035, 'woodL', ink=False)
    k.col(-0.95, 0.95, -0.42, 0.42, 0.0, 0.9)
    k.finish('Compost', ao=ao)
    # wheelbarrow [1, 2] (along Y): a green tray of soil and seedlings, iron wheel, timber handles
    rnd = random.Random(514)
    k.begin()
    k.hullp([(x, y, 0.36) for x in (-0.24, 0.24) for y in (-0.42, 0.3)] + [(x, y, 0.68) for x in (-0.36, 0.36) for y in (-0.62, 0.44)], 'verd')
    blob(k, rnd, 0.0, -0.08, 0.6, 0.3, 0.42, 0.2, zcol('soil2', 'soil', 'soil', 0.4), n=5)
    for j in range(3):
        bloom(k, -0.12 + j * 0.12, -0.1 + (j % 2) * 0.15, 0.8, 0.07, 'leafL')
    k.cyl(0.0, -0.72, 0.22, 0.22, 0.22, 0.1, 'iron', seg=10, rot=(0, 90, 0))
    k.cyl(0.05, -0.72, 0.22, 0.06, 0.06, 0.12, 'bronze', seg=6, rot=(0, 90, 0), ink=False)
    for s in (-1, 1):
        k.beam((s * 0.22, -0.7, 0.24), (s * 0.3, 0.92, 0.62), 0.05, 'wood')
        k.beam((s * 0.22, 0.3, 0.36), (s * 0.24, 0.32, 0.0), 0.04, 'iron', ink=False)
    k.col(-0.38, 0.38, -0.9, 0.92, 0.0, 0.7)
    k.finish('Wheelbarrow', ao=ao)
    # stacked pots (1 cell)
    k.begin()
    for (x, y, n) in ((-0.2, -0.18, 3), (0.22, -0.1, 2), (-0.05, 0.25, 4)):
        for j in range(n):
            k.cyl(x, y, j * 0.11, 0.09, 0.14, 0.16, 'terra' if j % 2 else 'terra2', seg=7)
    k.col(-0.38, 0.38, -0.36, 0.42, 0.0, 0.7)
    k.finish('PotStack', ao=ao)


# ================================================================ the backdrop manor (far beyond the north wall)
def build_backdrop_built(k):
    k.begin()
    k.bx(-14, 14, -5, 5, 0, 11, 'stone2')
    k.hullp([(x, y, 11) for x in (-14.5, 14.5) for y in (-5.6, 5.6)] + [(x, 0, 16) for x in (-12, 12)], 'slate')
    for s in (-1, 1):
        k.bx(s * 14, s * 21, -8, 3, 0, 8.5, 'stone2') if s > 0 else k.bx(-21, -14, -8, 3, 0, 8.5, 'stone2')
        xa, xb = (14, 21.4) if s > 0 else (-21.4, -14)
        k.hullp([(x, y, 8.5) for x in (xa, xb) for y in (-8.5, 3.4)] + [((xa + xb) / 2, y, 12) for y in (-8.5, 3.4)], 'slate')
        k.bx(s * 9 - 0.8, s * 9 + 0.8, -0.8, 0.8, 13, 18, 'stone3')
    for row in (2.5, 6.5):
        for i in range(12):
            x = -12.5 + i * 2.27
            k.qy(x - 0.45, x + 0.45, row, row + 2.2, -5.02, -1, 'iron')
    for s in (-1, 1):
        for i in range(3):
            x = s * (15.5 + i * 2.0)
            k.qy(x - 0.45, x + 0.45, 3.0, 5.0, -8.02, -1, 'iron')
    k.bx(-2.5, 2.5, -7, -5, 0, 4.5, 'stone')
    k.finish('Backdrop_Manor')


def build_built(k, ao):
    build_walls(k, ao)
    build_gate(k, ao)
    build_terrace(k, ao)
    build_fountains(k, ao)
    build_bridge(k, ao)
    build_glasshouse(k, ao)
    build_gazebo(k, ao)
    build_folly(k, ao)
    build_props(k, ao)
    build_backdrop_built(k)
