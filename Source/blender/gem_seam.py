"""kit-gemmine, zone 1: the working coal seam of Glimmerdeep Colliery (No. 3 Seam). Rock faces with banded strata and
coal seams (the coal mine kit's lofts), the first gem veins glinting in the coal, a lamp string along every face, steel
arch sets over the haulage gallery, the ore chute and its feed belt, the raised conveyor catwalk, the haulage winch
house, the ventilation fan and its duct, roof fittings (vent duct, lamp strings) on the "@layer 9" ceiling grid."""
import math
import random

from mathutils import Vector

from gem_base import (CM, CEIL, WALL_H, POOL_Z, KINDS, srt, rock_pts, clamp_pts, crystal, cluster, lantern_g, bulb,
                      floodlight, sign_board, stairs_x, deck, rail_x, post, face_loft)
from foundry_common import oslab, tube

STRING_Z = 3.6     # the lamp string along the faces (CM.cable_run height)
# zone 1 faces: seven profile levels (the coal mine's nine, the upper strata merged), the coal seam the band 1.5 - 3 m
SLV = [0.0, 0.6, 1.5, 3.0, 5.0, 7.4, WALL_H]
SEY = [-0.44, -0.5, -0.4, -0.47, -0.4, -0.33, -0.22]


# ================================================================ rock faces (zone 1)
def cable_flat(k, z=STRING_Z, y=-0.62, sag=0.09, t=0.035):
    """The power / lamp cable along a face, sagging between hooks at the module ends: per half a front quad and an
    under quad (the coal mine's cable_run as boxes costs three times the triangles over a whole zone of faces)."""
    for (xa, za, xb, zb) in ((-0.5, z, 0.0, z - sag), (0.0, z - sag, 0.5, z)):
        k.poly([(xa, y - t / 2, za - t / 2), (xb, y - t / 2, zb - t / 2), (xb, y - t / 2, zb + t / 2), (xa, y - t / 2, za + t / 2)], 'cable', (0, -1, 0))
        k.poly([(xa, y - t / 2, za - t / 2), (xa, y + t / 2, za - t / 2), (xb, y + t / 2, zb - t / 2), (xb, y - t / 2, zb - t / 2)], 'cable', (0, 0, -1))


def string(k, z=STRING_Z, y=-0.62, lit=True):
    cable_flat(k, z=z, y=y)
    if lit:
        bulb(k, 0.0, y - 0.005, z - 0.09)


def seam_wall(k, kind, seed):
    """Wall module (1 m, facing -Y): rock / coal seam face, the lamp string, and per kind a lantern on a bracket,
    a prop timber, a safety sign or a gem vein in the coal."""
    k.begin()
    gem = kind[4:] if kind.startswith('Gem_') else None
    if kind == 'Seam' or gem:
        face_loft(k, seed, SLV, SEY, WALL_H, CM.rock_fn(True, seed % 2 == 0), seam=(2, 3), depth=0.1 if seed % 2 else 0.19)
    else:
        face_loft(k, seed, SLV, SEY, WALL_H, CM.rock_fn(), amp=0.2 if kind in ('A', 'B', 'C') else 0.12, lo=-0.72)
    string(k, lit=kind in ('A', 'Prop') or (kind == 'Seam' and seed % 2 == 1))
    rnd = random.Random(seed * 7 + 3)
    if gem:
        # a vein of small crystals breaking out of the coal band (1.5 - 3 m), in two or three clumps along a crack
        g = {'Ruby': 'ruby', 'Emer': 'emer', 'Saph': 'saph', 'Dia': 'dia'}[gem]
        spots = [(-0.3, 1.85), (0.05, 2.35), (0.32, 2.65)] if seed % 2 else [(-0.22, 2.55), (0.18, 1.95)]
        for i, (x, z) in enumerate(spots):
            n = 3 if i == 0 else 2
            cluster(k, g, (x, -0.5, z), (rnd.uniform(-0.25, 0.25), -1.0, rnd.uniform(0.1, 0.5)), n, 0.26 + 0.06 * (i == 0),
                    0.055, seed * 10 + i, spread=0.6)
        # the crack the vein follows (a dark seam line)
        k.beam((spots[0][0] - 0.1, -0.69, spots[0][1] - 0.15), (spots[-1][0] + 0.1, -0.69, spots[-1][1] + 0.12), 0.03, 'pit', ink=False)
    elif kind.startswith('Lamp'):
        k.bx(-0.07, 0.07, -0.95, -0.2, 3.25, 3.39, 'timber')
        k.beam((0.0, -0.3, 2.65), (0.0, -0.82, 3.26), 0.09, 'timber2')
        lantern_g(k, 0.0, -0.88, 3.25)
        CM.pool(k, 0.0, -1.5, POOL_Z[kind[4:]], 2.1, seed, sx=1.15)
    elif kind == 'Prop':
        k.bx(-0.13, 0.13, -0.8, -0.54, 0, 4.0, 'timber')
        k.bx(-0.2, 0.2, -0.86, -0.2, 4.0, 4.28, 'timber2')
        k.bx(-0.16, 0.16, -0.74, -0.58, 4.28, 4.4, 'timberEnd', ink=False)
        k.bx(-0.18, 0.18, -0.84, -0.5, 0, 0.12, 'timber2', ink=False)
    elif kind.startswith('Sign'):
        if kind == 'SignSeam':
            sign_board(k, 0.0, -0.6, 1.75, 0.95, 0.95, [('NO.3 SEAM', 0.26, None), ('GLIMMERDEEP', 0.12, 'hazard'), ('LEVEL 7', 0.12, None)])
        elif kind == 'SignHaul':
            sign_board(k, 0.0, -0.6, 1.8, 0.95, 0.85, [('HAULAGE', 0.2, 'ink'), ('KEEP CLEAR', 0.15, 'ink'), ('OF CARTS', 0.12, 'ink')], bg='hazard', rim='ink')
        else:
            sign_board(k, 0.0, -0.6, 1.8, 0.95, 0.85, [('GEM VEIN', 0.2, 'rubyL'), ('REPORT ALL', 0.13, None), ('FINDS', 0.13, None)])
        for x in (-0.36, 0.36):
            k.bx(x - 0.02, x + 0.02, -0.56, -0.3, 2.4, 2.44, 'steelDark', ink=False)
    return k


def seam_corner(k, seed):
    """Corners, notches and pillar edges: two stacked faceted lumps filling the cell up to the roof."""
    k.begin()
    rnd = random.Random(seed)
    fn = CM.rock_fn()
    hb = rnd.uniform(3.8, 4.8)
    k.hullp(clamp_pts(rock_pts(rnd, (0, 0), 0.56, 0.56, hb, n=7, top=2), 0.5), fn)
    pts = rock_pts(rnd, (0.04, -0.04), 0.54, 0.54, WALL_H - hb + 0.8, z0=hb - 0.8, n=6, top=0)
    pts += [(0.45, 0.45, WALL_H), (-0.45, 0.45, WALL_H), (0.45, -0.45, WALL_H), (-0.45, -0.45, WALL_H)]
    k.hullp(clamp_pts(pts, 0.5), fn)
    return k


def crib(k):
    """2 x 2 m timber crib (log-cabin stack of 0.34 m sawn timbers) carrying a roof post and header up to the roof."""
    k.begin()
    z, L, T = 0.0, 0, 0.34
    while z < 3.4:
        for s in (-1, 1):
            if L % 2 == 0:
                k.bx(-0.92, 0.92, *srt(s * 0.58, s * 0.9), z, z + T, 'timber' if s > 0 else 'timber2')
                k.qx(*srt(s * 0.6, s * 0.88), z + 0.02, z + T - 0.02, 0.923, 1, 'timberEnd')
                k.qx(*srt(s * 0.6, s * 0.88), z + 0.02, z + T - 0.02, -0.923, -1, 'timberEnd')
            else:
                k.bx(*srt(s * 0.56, s * 0.88), -0.94, 0.94, z, z + T, 'timber2' if s > 0 else 'timber')
                k.qy(*srt(s * 0.58, s * 0.86), z + 0.02, z + T - 0.02, 0.943, 1, 'timberEnd')
                k.qy(*srt(s * 0.58, s * 0.86), z + 0.02, z + T - 0.02, -0.943, -1, 'timberEnd')
        z += T
        L += 1
    k.bx(-0.94, 0.94, -0.94, 0.94, z, z + 0.08, 'plank2')
    k.bx(-0.28, 0.28, -0.28, 0.28, z + 0.08, CEIL - 0.42, 'timber')
    k.bx(-0.95, 0.95, -0.33, 0.33, CEIL - 0.42, CEIL + 0.1, 'timber2')
    for a in (0, 180):
        k.push(0, 0, a)
        k.beam((0.28, 0, CEIL - 1.7), (0.9, 0, CEIL - 0.44), 0.16, 'timber2')
        k.pop()
    k.col(-0.95, 0.95, -0.95, 0.95, 0, CEIL)
    return k


# ================================================================ timber drifts, arches, track and carts
def drift(k, variant):
    """Timber set across a 6 m drift with lagging and a plank bulkhead to the roof (CM.timber_drift); the lamp
    variants hang a glowing lantern from the cap."""
    rail = variant.startswith('Rail')
    CM.timber_drift(k, 'Rail' if rail else 'Plain')
    if variant.endswith('Lamp'):
        lantern_g(k, -1.2, -0.25, 3.92)
        CM.pool(k, -1.2, -0.2, POOL_Z['set'], 0.45, 3)
    return k


def arch_strip(k, pts, t, y0, y1, color):
    """A bent steel section along the polyline pts [(x, z)] (miter joints, so the bend reads smooth), t thick,
    from y0 to y1."""
    n = len(pts)
    off = []
    for i in range(n):
        if i == 0:
            d = Vector((pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]))
        elif i == n - 1:
            d = Vector((pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]))
        else:
            d = Vector((pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]))
        d.normalize()
        nrm = Vector((-d.y, d.x)) * (t / 2)
        off.append(((pts[i][0] - nrm.x, pts[i][1] - nrm.y), (pts[i][0] + nrm.x, pts[i][1] + nrm.y)))
    for i in range(n - 1):
        q = []
        for j in (i, i + 1):
            for (x, z) in off[j]:
                q += [(x, y0, z), (x, y1, z)]
        k.hullp(q, color)


def steel_arch(k, lamp=False):
    """Prefab 12 x 1: a steel arch set over the 12 m haulage gallery (two splayed legs on foot plates, a bent crown
    to 7 m), fishplate joints, a lamp at the crown on some."""
    k.begin()
    W, LEG, TOP = 5.45, 3.6, 7.0
    pts = [(-W - 0.12, 0.0), (-W, LEG)]
    for i in range(1, 10):
        a = math.pi - math.pi * i / 10
        pts.append((math.cos(a) * W, LEG + math.sin(a) * (TOP - LEG)))
    pts += [(W, LEG), (W + 0.12, 0.0)]
    arch_strip(k, pts, 0.24, -0.12, 0.12, 'steel2')
    for s in (-1, 1):
        x = s * (W + 0.06)
        k.bx(x - 0.35, x + 0.35, -0.3, 0.3, 0.0, 0.08, 'steelDark')
        k.col(x - 0.24, x + 0.24, -0.18, 0.18, 0, 3.7)
        # fishplate joints where the crown meets the legs
        k.bx(s * W - 0.2, s * W + 0.2, -0.2, 0.2, LEG - 0.25, LEG + 0.2, 'steel', ink=True)
        # lagging boards against the rock on top of the legs' crown ends
    for x in (-2.6, 0.0, 2.6):   # tie rods to the next set (the ends showing as stubs)
        a = math.acos(max(-1, min(1, x / W)))
        z = LEG + math.sin(a) * (TOP - LEG) - 0.1
        k.bx(x - 0.03, x + 0.03, -0.5, 0.5, z - 0.03, z + 0.03, 'steelDark', ink=False)
    if lamp:
        k.bx(-0.018, 0.018, -0.018, 0.018, TOP - 0.85, TOP - 0.12, 'steelDark', ink=False)
        lantern_g(k, 0.0, 0.0, TOP - 0.85)
        CM.pool(k, 0.0, 0.0, POOL_Z['set'] + 0.004, 1.4, 21, sx=1.6)
    return k


def rail(k):
    """Rail run piece (1 m along X): two sleepers, two rails as single bars, the ballast strip."""
    k.begin()
    k.qz(-0.5, 0.5, -0.45, 0.45, CM.Z_BALLAST, 1, 'dust')
    for xs in (-0.25, 0.25):
        k.bx(xs - 0.08, xs + 0.08, -0.44, 0.44, 0, CM.SLEEPER_TOP, 'timber2', ink=False)
    for sy in (-1, 1):
        k.bx(-0.5, 0.5, sy * 0.3 - 0.03, sy * 0.3 + 0.03, CM.SLEEPER_TOP, CM.RAIL_TOP, 'steel', ink=False)
    return k


def trail_wall(k):
    """Drift wall between the zones (1 m along Blender Y, corridor to +X; the coal mine kit's drift wall, leaner): a
    rock face on the seven levels, a timber set (post, half cap, knee brace), half of the lagging roof, the track by
    the wall, the cable. The back (-X) is plain rock (seen in the hatch room)."""
    k.begin(90)
    ROOF = CM.ROOF
    ys = [-0.27, -0.31, -0.25, -0.3, -0.24, -0.26, -0.2]

    def tp(ysx):
        return [(y, z) for y, z in zip(ysx, SLV)] + [(0.24, WALL_H), (0.25, 0.0)]
    rnd = random.Random(5)
    mid = [max(-0.36, y + rnd.uniform(-0.05, 0.03)) for y in ys]
    k.loft([(-0.5, tp(ys)), (0.0, tp(mid)), (0.5, tp(ys))], CM.rock_fn(), baffle='rock2')
    y_mid = -2.25 + 0.003
    k.bx(-0.1, 0.1, -0.42, -0.24, 0, ROOF - 0.32, 'timber')
    k.bx(-0.12, 0.12, y_mid, -0.2, ROOF - 0.32, ROOF - 0.06, 'timber2')
    k.beam((0, -0.42, ROOF - 1.1), (0, -0.95, ROOF - 0.33), 0.1, 'timber2')
    for i in range(2):   # lagging: two boards per metre, one shade each
        x0 = -0.5 + i * 0.5
        k.bx(x0 + 0.006, x0 + 0.494, y_mid, -0.2, ROOF - 0.06, ROOF, 'plank' if i % 2 else 'plank2', ink=False)
    k.push(0, -0.82, 0)
    k.qz(-0.5, 0.5, -0.4, 0.4, CM.Z_BALLAST, 1, 'dust')
    for xs in (-0.25, 0.25):
        k.bx(xs - 0.08, xs + 0.08, -0.4, 0.4, 0, CM.SLEEPER_TOP, 'timber2', ink=False)
    for sy in (-1, 1):
        k.bx(-0.5, 0.5, sy * 0.25 - 0.03, sy * 0.25 + 0.03, CM.SLEEPER_TOP, CM.RAIL_TOP, 'steel', ink=False)
    k.pop()
    cable_flat(k, z=3.1, y=-0.38)
    return k


def gem_cart(k):
    """Ore cart full of coal with a few rough gems on top (prefab 1 x 2 on its track)."""
    CM.ore_cart(k, 0)
    rnd = random.Random(5)
    for i, g in enumerate(('ruby', 'emer', 'saph', 'dia', 'ruby')):
        x, y = rnd.uniform(-0.3, 0.3), -0.55 + i * 0.27
        crystal(k, g, (x, y, 1.33), (x + rnd.uniform(-0.1, 0.1), y + rnd.uniform(-0.1, 0.1), 1.58), 0.07)
    return k


# ================================================================ lamps
def lantern_post(k):
    k.begin()
    k.bx(-0.09, 0.09, -0.09, 0.09, 0, 2.86, 'timber')
    k.bx(-0.07, 0.07, -0.7, 0.07, 2.75, 2.9, 'timber2')
    k.beam((0, 0.0, 2.3), (0, -0.4, 2.76), 0.07, 'timber2')
    lantern_g(k, 0.0, -0.62, 2.74)
    k.bx(-0.15, 0.15, -0.15, 0.15, 0, 0.25, 'rock2')
    CM.pool(k, 0.0, -0.6, POOL_Z['post'], 2.2, 41)
    k.col(-0.15, 0.15, -0.15, 0.15, 0, 2.2)
    return k


# ================================================================ ceiling fittings ("@layer 9": hanging from z 0 down)
def vent_duct(k):
    """Run piece (1 m along X): the yellow lay-flat ventilation duct hanging from a messenger wire under the roof."""
    k.begin()
    z = -0.9
    k.cyl(-0.5, 0.0, z, 0.36, 0.36, 1.0, 'mach', seg=8, rot=(0, 90, 0), caps=False)
    k.cyl(-0.06, 0.0, z, 0.385, 0.385, 0.12, 'mach2', seg=8, rot=(0, 90, 0), ink=False, caps=False)
    k.bx(-0.5, 0.5, -0.012, 0.012, -0.3, -0.28, 'cable', ink=False)
    for x in (0.0,):
        k.bx(x - 0.006, x + 0.006, -0.005, 0.005, z + 0.34, -0.29, 'cable', ink=False)
    k.bx(-0.04, 0.04, -0.04, 0.04, -0.32, 0.0, 'steelDark', ink=False)
    return k


def lamp_string(k, hanger):
    """Run piece (1 m along X): a lamp string across the gallery at 5.6 m, one bulb per metre; every other piece
    carries the hanger wire up to a roof bolt."""
    k.begin()
    z = -3.4
    cable_flat(k, z=z, y=0.0, sag=0.07, t=0.03)
    if hanger:   # every other metre: the hanger wire to a roof bolt and a bulb
        k.bx(0.47, 0.49, -0.01, 0.01, z, -0.02, 'cable', ink=False)
        k.bx(0.44, 0.52, -0.04, 0.04, -0.03, 0.0, 'steelDark', ink=False)
        bulb(k, 0.0, 0.0, z - 0.07)
    return k


# ================================================================ landmarks and big props
def bin_hull(k, x0, x1, y0, y1, zt, xs0, xs1, ys0, ys1, zb, c='plank'):
    k.hullp([(xs0, ys0, zb), (xs1, ys0, zb), (xs1, ys1, zb), (xs0, ys1, zb),
             (x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt)], c)


def chute(k):
    """Landmark 10 x 8 (zone 1): the ore bin over the east haulage track (track along Y at local x -3.5): a timber
    bin on four legs, its steel chute and gate over a cart, the inclined feed belt rising from the raised conveyor
    catwalk's end (local x +5, belt top 2.95 at local y +0.25) to the bin rim; a sorting platform beside the bin."""
    k.begin()
    TX = -3.5
    k.push(TX, 0, 90)
    CM.track(k, -4.0, 4.0, 0.0, sleepers=[-3.75 + 0.5 * i for i in range(16)])
    k.pop()
    k.push(TX, 0.2, 0)
    CM.cart_body(k, coal=True, tip=3)
    k.pop()
    for c in ('ruby', 'saph'):
        crystal(k, c, (TX + (0.15 if c == 'ruby' else -0.2), 0.0, 1.38), (TX + 0.1, 0.1, 1.62), 0.07)
    # legs (timber with steel shoes), braces
    for x in (TX - 1.15, TX + 1.15):
        for y in (-1.9, 1.9):
            k.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, 3.0, 'timber')
            k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 0.18, 'steelDark')
            k.col(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, 3.0)
        k.beam((x, -1.9, 0.5), (x, 1.9, 2.7), 0.12, 'timber2')
    # the bin: a timber hopper with steel corner bands, coal heaped in it
    bin_hull(k, TX - 1.7, TX + 1.7, -2.3, 2.3, 5.3, TX - 0.55, TX + 0.55, -0.55, 0.55, 3.0)
    for (xx, yy) in ((TX - 1.7, -2.3), (TX + 1.7, -2.3), (TX - 1.7, 2.3), (TX + 1.7, 2.3)):
        k.beam((xx * 0.32 + TX * 0.68, yy * 0.24, 3.0), (xx, yy, 5.3), 0.1, 'steelDark', ink=False)
    k.bx(TX - 1.78, TX + 1.78, -2.38, 2.38, 5.3, 5.44, 'timber2')
    k.hullp([(TX - 1.55, -2.15, 5.38), (TX + 1.55, -2.15, 5.38), (TX + 1.55, 2.15, 5.38), (TX - 1.55, 2.15, 5.38),
             (TX, 0.2, 5.95), (TX - 0.6, 0.8, 5.75), (TX + 0.7, -0.6, 5.7)], lambda f: 'coal2' if f.normal.z > 0.6 else 'coal')
    # chute: steel throat, sloped spout, a gate on a lever
    k.bx(TX - 0.5, TX + 0.5, -0.5, 0.5, 2.55, 3.05, 'steel2')
    k.hullp([(TX - 0.45, -0.45, 2.6), (TX + 0.45, -0.45, 2.6), (TX - 0.45, 0.45, 2.6), (TX + 0.45, 0.45, 2.6),
             (TX - 0.38, -0.2, 2.05), (TX + 0.38, -0.2, 2.05), (TX - 0.38, 0.5, 2.25), (TX + 0.38, 0.5, 2.25)], 'steelDark')
    k.bx(TX - 0.5, TX + 0.5, -0.62, -0.5, 2.1, 2.7, 'cart')
    k.beam((TX + 0.5, -0.56, 2.4), (TX + 1.4, -0.56, 1.5), 0.06, 'steelDark')
    k.cyl(TX + 1.42, -0.56, 1.32, 0.08, 0.08, 0.2, 'red', seg=6)
    k.col(TX - 1.78, TX + 1.78, -2.38, 2.38, 2.6, 5.6)
    k.col(TX - 0.58, TX + 0.58, -0.9, 0.9, 0, 1.3)
    # the feed belt: from the catwalk belt's end (x +5, z 2.95) up to the bin rim
    a, b = Vector((5.0, 0.25, 2.62)), Vector((TX + 1.4, 0.25, 5.25))
    k.beam(a, b, 0.5, 'steel2')
    up = Vector((0, 0, 0.27))
    k.beam(a + up, b + up, 0.36, 'rubber', ink=False)
    for t in (0.12, 0.38, 0.62, 0.86):
        p = a.lerp(b, t) + up + Vector((0, 0, 0.12))
        k.hullp(rock_pts(random.Random(int(t * 100)), (p.x, 0.25 + (t - 0.5) * 0.2), 0.13, 0.11, 0.14, z0=p.z - 0.07, n=4, top=1), 'coal')
    k.cyl(b.x, 0.25, b.z, 0.32, 0.32, 0.62, 'steelDark', seg=10, rot=(90, 0, 0))   # head pulley
    for t in (0.18, 0.55):
        p = a.lerp(b, t)
        for yy in (-0.05, 0.55):
            k.bx(p.x - 0.08, p.x + 0.08, yy - 0.08, yy + 0.08, 0, p.z - 0.2, 'steel2')
            k.col(p.x - 0.08, p.x + 0.08, yy - 0.08, yy + 0.08, 0, p.z - 0.2)
        k.beam((p.x, -0.05, 0.6), (p.x, 0.55, p.z - 0.4), 0.06, 'steelDark', ink=False)
    k.col(-1.2, 5.0, 0.0, 0.5, 2.9, 5.4)
    # a picker's stand beside the bin (lantern, a crate of picked gems), a work light over the loading point
    k.bx(-0.9, 0.2, 2.6, 3.6, 0, 0.9, 'plank')
    k.col(-0.9, 0.2, 2.6, 3.6, 0, 0.9)
    for g, x in (('ruby', -0.7), ('emer', -0.45), ('saph', -0.2), ('dia', 0.05)):
        crystal(k, g, (x, 3.1, 0.88), (x + 0.02, 3.05, 1.08), 0.06)
    post(k, -1.5, -2.9, 0, 3.2, c='timber', w=0.09)
    floodlight(k, -1.5, -3.04, 3.0, s=-1)
    k.beam((-1.5, -2.95, 3.1), (TX + 1.3, -2.4, 4.6), 0.03, 'cable', ink=False)
    CM.pool(k, TX, -1.6, POOL_Z['chute'], 1.6, 31, sx=1.0, sy=1.4)
    # a level board on the bin
    sign_board(k, TX, -2.39, 4.0, 1.5, 0.95, [('BIN 3', 0.28, None), ('NO RIDING', 0.14, 'hazard')], s=-1)
    return k


def belt_bridge(k):
    """Prefab 20 x 3 (zone 1): the raised conveyor catwalk. A troughed belt at 2.95 m on steel trestles along the back
    (local y 0.3 .. 1.2), a walkway deck at 3.0 m along the front (y -1.4 .. 0.2) with stairs down at both ends,
    hand rails, lamps on two posts; the belt feeds the ore chute's feed belt at the west end (x -10)."""
    k.begin()
    Z = 3.0
    BY = 0.75
    # belt: flat along the catwalk, then an incline down to the face conveyor beyond the east end (x 10.9, z 0.95)
    BELT = [(-10.0, Z - 0.1), (4.0, Z - 0.1), (10.9, 0.95)]
    for j, ((xa, za), (xb, zb)) in enumerate(zip(BELT, BELT[1:])):
        e = 0.008 * j     # the incline a hair narrower: its side faces never share a plane with the flat run's
        oslab(k, (xa, BY, za - 0.035), (xb, BY, zb - 0.035), 0.36 - e, 0.035, 0.36 - e, 0.035, 'rubber')
        for s in (-1, 1):
            oslab(k, (xa, BY + s * 0.45, za - 0.17), (xb, BY + s * 0.45, zb - 0.17), 0.03 - e / 2, 0.09, 0.03 - e / 2, 0.09, 'steel2')
    k.bx(-10.0, 4.0, BY - 0.33, BY + 0.33, Z - 0.6, Z - 0.56, 'rubber', ink=False)   # return belt
    k.cyl(10.9, BY - 0.42, 0.95 - 0.2, 0.2, 0.2, 0.84, 'steelDark', seg=10, rot=(-90, 0, 0))   # tail drum
    rnd = random.Random(12)

    def belt_z(x):
        return Z - 0.1 if x <= 4.0 else Z - 0.1 + (0.95 - (Z - 0.1)) * (x - 4.0) / 6.9
    for i in range(9):
        x = -9.0 + i * 2.3 + rnd.uniform(-0.3, 0.3)
        k.hullp(rock_pts(rnd, (x, BY + rnd.uniform(-0.1, 0.1)), 0.15, 0.12, 0.15, z0=belt_z(x) - 0.02, n=4, top=1), 'coal')
    # trestles
    for x in (-9.6, -4.8, 0.0, 4.0, 7.4):
        zt = belt_z(x) - 0.22
        for yy in (BY - 0.45, BY + 0.45):
            k.bx(x - 0.07, x + 0.07, yy - 0.07, yy + 0.07, 0, zt, 'steelDark')
        k.bx(x - 0.05, x + 0.05, BY - 0.45, BY + 0.45, min(0.9, zt - 0.3), min(0.98, zt - 0.22), 'steelDark', ink=False)
        k.col(x - 0.08, x + 0.08, BY - 0.53, BY + 0.53, 0, min(1.0, zt))
    k.col(-10.0, 4.0, BY - 0.5, BY + 0.5, Z - 0.65, Z + 0.25)
    k.col(4.0, 7.2, BY - 0.5, BY + 0.5, 2.0, Z + 0.25)
    k.col(7.2, 10.95, BY - 0.5, BY + 0.5, 0, 2.15)
    # walkway deck (steel grating) on posts, stairs at both ends
    deck(k, -5.5, 5.5, -1.4, 0.2, Z, t=0.1, grate=True)
    for x in (-5.4, -1.8, 1.8, 5.4):
        post(k, x, -1.3, 0, Z - 0.1, c='steelDark', w=0.06)
        post(k, x, 0.1, 0, Z - 0.1, c='steelDark', w=0.06)
    stairs_x(k, -10.0, -5.5, -1.4, 0.2, 0.0, Z, 9, rails=(True, False))
    stairs_x(k, 10.0, 5.5, -1.4, 0.2, 0.0, Z, 9, rails=(True, False))
    rail_x(k, -5.5, 5.5, -1.36, Z, post=2.75)
    rail_x(k, -5.5, 5.5, 0.25, Z, post=2.75, kick=False)
    # lamp posts on the rail, a sign
    for x in (-4.6, 4.6):
        k.bx(x - 0.04, x + 0.04, 0.21, 0.29, Z, Z + 2.3, 'steelDark')
        k.bx(x - 0.03, x + 0.03, -0.4, 0.26, Z + 2.25, Z + 2.33, 'steelDark', ink=False)
        lantern_g(k, x, -0.36, Z + 2.25, 0.85)
    sign_board(k, 0.0, -1.47, Z + 0.15, 1.7, 0.6, [('BELT 3 - NO RIDING', 0.17, 'ink')], bg='hazard', rim='ink', s=-1)
    return k


def winch_house(k):
    """Landmark 6 x 5 (zone 1): the haulage winch house, open toward the track (-Y): plank walls on a sill, a
    corrugated roof, the rope drum with its motor and gearbox, the driver's levers and gauges, the rope leaving over
    a sheave toward the haulage; a lantern over the front."""
    k.begin()
    X0, X1, Y0, Y1, H = -2.9, 2.9, -2.3, 2.4, 3.3
    # walls (back + sides, plank seams), sill, roof
    k.bx(X0 + 0.12, X1 - 0.12, Y1 - 0.12, Y1, 0, H - 0.02, 'plank')
    for s, x in ((-1, X0), (1, X1)):
        x0, x1 = srt(x, x - s * 0.12)
        k.bx(x0, x1, Y0, Y1, 0, H, 'plank')
        for i in range(1, 12):
            y = Y0 + (Y1 - Y0) * i / 12
            k.qx(y - 0.012, y + 0.012, 0.05, H - 0.05, x + s * 0.003, s, 'plank2')
    for i in range(1, 15):
        x = X0 + (X1 - X0) * i / 15
        k.qy(x - 0.012, x + 0.012, 0.05, H - 0.05, Y1 + 0.003, 1, 'plank2')
    k.bx(X0 - 0.1, X1 + 0.1, Y0 - 0.12, Y0 + 0.08, H - 0.4, H - 0.15, 'timber2')       # front header
    for s in (-1, 1):
        k.bx(s * 2.7 - 0.08, s * 2.7 + 0.08, Y0 - 0.05, Y0 + 0.15, 0, H - 0.4, 'timber')
    k.hullp([(X0 - 0.3, Y0 - 0.5, H), (X1 + 0.3, Y0 - 0.5, H), (X1 + 0.3, Y1 + 0.3, H + 0.55), (X0 - 0.3, Y1 + 0.3, H + 0.55),
             (X0 - 0.3, Y0 - 0.5, H + 0.1), (X1 + 0.3, Y0 - 0.5, H + 0.1), (X1 + 0.3, Y1 + 0.3, H + 0.65), (X0 - 0.3, Y1 + 0.3, H + 0.65)], 'steel2')
    for i in range(12):
        x = X0 - 0.15 + i * 0.52
        k.beam((x, Y0 - 0.5, H + 0.11), (x, Y1 + 0.3, H + 0.66), 0.04, 'steel', ink=False)
    # concrete bed, bearing blocks, the rope drum between its flanges, gearbox, motor
    k.bx(-2.2, 2.4, -0.4, 1.8, 0, 0.35, 'rock3')
    for (x0, x1) in ((-1.6, -1.4), (1.0, 1.2)):
        k.bx(x0, x1, 0.15, 1.15, 0.36, 1.22, 'steelDark')
    k.cyl(-1.35, 0.65, 1.15, 0.5, 0.5, 2.3, 'steel2', seg=12, rot=(0, 90, 0))
    k.cyl(-1.28, 0.65, 1.15, 0.58, 0.58, 2.16, 'rope', seg=12, rot=(0, 90, 0), caps=False)
    for x in (-1.4, 0.9):
        k.cyl(x, 0.65, 1.15, 0.78, 0.78, 0.1, 'cart2', seg=12, rot=(0, 90, 0))
    k.bx(1.2, 1.34, 0.3, 1.0, 0.36, 1.5, 'steelDark')
    k.cyl(1.27, 0.65, 1.5, 0.2, 0.2, 0.12, 'cart', seg=8)
    k.bx(1.34, 2.2, 0.2, 1.1, 0.36, 1.28, 'mach')
    k.cyl(2.2, 0.65, 0.82, 0.32, 0.32, 0.14, 'mach2', seg=10, rot=(0, 90, 0))
    # driver's stand: levers, a gauge board, a bell
    k.bx(-2.4, -1.75, -1.6, -0.9, 0, 1.0, 'steelDark')
    for i, x in enumerate((-2.25, -2.05, -1.88)):
        k.beam((x, -1.25, 1.0), (x, -1.45 - 0.12 * i, 1.6), 0.04, 'steel')
        k.cyl(x, -1.45 - 0.12 * i, 1.6, 0.05, 0.05, 0.08, 'red', seg=6)
    k.bx(-2.78, -2.74, -1.7, -0.7, 1.4, 2.2, 'board')
    for i, y in enumerate((-1.45, -0.95)):
        k.cyl(-2.73, y, 1.85, 0.16, 0.16, 0.03, 'chalk', seg=10, rot=(0, 90, 0), ink=False)
    # rope off the drum bottom, over a sheave on a post at the front, then along the floor to the track
    k.bx(-0.3, 0.3, -2.2, -1.6, 0, 0.12, 'steelDark')
    k.bx(-0.07, 0.07, -1.97, -1.83, 0.12, 0.9, 'steelDark')
    k.cyl(0.0, -1.9, 0.72, 0.28, 0.28, 0.1, 'cart', seg=10, rot=(0, 90, 0))
    k.beam((-0.4, 0.1, 0.55), (0.0, -1.7, 0.98), 0.035, 'rope', ink=False)
    k.beam((0.0, -2.12, 0.5), (0.0, -2.6, 0.06), 0.035, 'rope', ink=False)
    # lantern over the opening, a pool in front, a sign
    k.bx(-0.04, 0.04, Y0 - 0.45, Y0 - 0.05, H - 0.33, H - 0.27, 'steelDark', ink=False)
    lantern_g(k, 0.0, Y0 - 0.42, H - 0.3, 0.85)
    CM.pool(k, 0.0, Y0 - 1.3, POOL_Z['winch'], 1.5, 37, sx=1.5, sy=0.8)
    sign_board(k, -1.5, Y0 - 0.15, 2.3, 1.6, 0.48, [('HAULAGE ENGINE', 0.16, None)], s=-1)
    # collision: walls, machine bed, stand, sheave post
    k.col(X0, X1, Y1 - 0.12, Y1, 0, H)
    for x in (X0, X1):
        k.col(*srt(x, x + (0.12 if x < 0 else -0.12)), Y0, Y1, 0, H)
    k.col(-2.2, 2.2, -0.4, 1.8, 0, 1.6)
    k.col(-2.4, -1.75, -1.6, -0.9, 0, 1.2)
    k.col(-0.3, 0.3, -2.2, -1.6, 0, 1.0)
    return k


def fan_unit(k):
    """Prefab 4 x 2 against a wall (zone 1): the auxiliary ventilation fan. A yellow axial fan barrel on a skid along
    local X (axis at y -0.5, a cell centre), its outlet elbow into a riser at (1.5, -0.5) up to the roof and a stub
    along +X into the vent duct of the "@layer 9" grid; a guard grille on the intake, a starter box, a plate."""
    k.begin()
    Y, YB = -0.5, -0.15     # the riser's axis (a cell centre: the duct run continues it), the barrel's (clear of the track)
    k.bx(-1.6, 1.0, YB - 0.55, YB + 0.6, 0, 0.18, 'steelDark')
    k.cyl(-1.4, YB, 1.05, 0.62, 0.62, 2.0, 'mach', seg=12, rot=(0, 90, 0))
    for x in (-1.37, -0.42, 0.42):
        k.cyl(x, YB, 1.05, 0.68, 0.68, 0.08, 'mach2', seg=12, rot=(0, 90, 0), ink=False)
    k.cyl(-1.42, YB, 1.05, 0.55, 0.55, 0.01, 'steelDark', seg=12, rot=(0, -90, 0), ink=False)
    for i in range(-2, 3):
        k.bx(-1.47, -1.44, YB - 0.55, YB + 0.55, 1.05 + i * 0.2 - 0.015, 1.05 + i * 0.2 + 0.015, 'steel', ink=False)
    k.bx(-0.3, 0.2, YB - 0.25, YB + 0.25, 1.62, 1.9, 'steelDark')                   # motor terminal box
    k.bx(-1.2, 0.4, YB - 0.42, YB + 0.42, 0.18, 0.5, 'steelDark')                   # cradle
    tube(k, (0.58, YB, 1.05), (1.5, Y, 1.05), 0.48, 'mach', seg=10)                 # outlet elbow
    # outlet elbow and riser to the roof duct (local z 8.1), the stub into the duct run
    k.cyl(1.5, Y, 1.05, 0.48, 0.48, CEIL - 0.9 - 1.05, 'mach', seg=10)
    for z in (2.6, 4.4, 6.2):
        k.cyl(1.5, Y, z, 0.52, 0.52, 0.1, 'mach2', seg=10, ink=False, caps=False)
    k.bx(1.44, 1.56, 0.02, 0.14, 0.2, CEIL, 'steelDark')                          # riser strut
    k.cyl(1.5, Y, CEIL - 0.9, 0.36, 0.36, 0.5, 'mach', seg=10, rot=(0, 90, 0), caps=False)
    # starter box with a lamp, a warning plate above the barrel
    k.bx(-1.5, -0.9, 0.35, 0.6, 1.9, 2.6, 'board')
    k.gbx(-1.3, -1.1, 0.33, 0.35, 2.4, 2.5, 'emer', hull=False)
    sign_board(k, -0.25, 0.25, 1.85, 0.9, 0.5, [('AUX FAN 2', 0.15, 'ink'), ('KEEP RUNNING', 0.1, 'ink')], bg='hazard', rim='ink', s=-1)
    k.col(-1.6, 1.0, YB - 0.62, YB + 0.62, 0, 1.75)
    k.col(1.0, 2.0, Y - 0.5, Y + 0.5, 0, CEIL)
    return k
