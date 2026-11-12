"""kit-observatory, zone 1 (the summit compound): the station / annex signs, the 10 m dish antennas, the VSAT dishes,
the lattice radio masts, equipment shelters, the ground station building (walkable roof deck at 3 m), the 1931
Halden Dome (landmark: stone drum, copper dome, slit open, its refractor out), the snowcat, the fuel tank, the
generator house, the weather mast, the all-sky camera, lamp posts, rocks, flight cases, gas bottles, cable drums,
the summit cairn, the panorama board, benches, overhead cable bridges, the visitor telescope.
See ob_base.py for the conventions."""
import math
import random

from mathutils import Vector

from ob_base import *  # noqa: F401,F403
import ob_base as B


def V(*a):
    return Vector(a)


def basis(az, el):
    """boresight d (azimuth from Blender +X, elevation), e1 horizontal across it, e2 = d x e1 (the dish's 'up')"""
    ca, sa, ce, se = math.cos(az), math.sin(az), math.cos(el), math.sin(el)
    d = V(ce * ca, ce * sa, se)
    e1 = V(-sa, ca, 0.0)
    e2 = d.cross(e1)
    return d, e1, e2


def dish(k, C, d, e1, e2, R, f, t=0.12, J=5, N=24, front='domeW', back='steel'):
    """a closed paraboloid reflector (vertex C, axis d, rim radius R, focal length f, thickness t)"""
    def ring(r, off):
        w = r * r / (4 * f)
        return [tuple(C + e1 * (r * math.cos(2 * math.pi * i / N)) + e2 * (r * math.sin(2 * math.pi * i / N)) + d * (w + off)) for i in range(N)]
    rs = [R * (0.12 + 0.88 * j / (J - 1)) for j in range(J)]
    rings = [ring(r, 0.0) for r in rs] + [ring(r, -t) for r in reversed(rs)]
    dd = d.copy()

    def col(fc):
        n = fc.normal
        return front if n.dot(dd) > 0.35 else back if n.dot(dd) < -0.35 else 'steelD'
    k.sweep(rings, col, cap0=True, cap1=True, recalc=True)
    return rs


def beamv(k, a, b, t, c, ink=True):
    k.beam(tuple(a), tuple(b), t, c, ink=ink)


def big_dish(k, ao, name, az, el):
    """a 10 m dish antenna on an elevation-over-azimuth pedestal (front of the footprint: Blender -Y)"""
    k.begin()
    # concrete foundation, steel azimuth housing (turned to the azimuth), the yoke
    k.cyl(0, 0, 0, 2.2, 2.1, 1.2, 'conc', seg=16)
    k.cyl(0, 0, 1.2, 2.18, 2.18, 0.06, 'snow', seg=16, ink=False)
    k.push(0, 0, math.degrees(az) - 90)
    k.bx(-1.3, 1.3, -1.3, 1.3, 1.2, 3.6, 'domeW', cull='b')
    k.fq(-1.2, 1.2, -1.303, 2.9, 3.1, 'blueS')
    k.fq(-0.5, 0.5, -1.303, 1.3, 2.6, 'steelD')
    k.text('VL-%s' % name[-1], 0.0, -1.306, 3.2, 0.22, 'blueD', font='display', maxw=1.2)
    k.cyl(0, 0, 3.6, 1.1, 1.1, 0.35, 'steelD', seg=12)
    for s in (-1, 1):
        k.bx(s * 1.35 - 0.2, s * 1.35 + 0.2, -0.45, 0.45, 3.95, 5.6, 'steel')
    k.pop()
    Z = 5.2
    d, e1, e2 = basis(az, el)
    A = V(0, 0, Z)
    k.tube(tuple(A - e1 * 1.6), tuple(A + e1 * 1.6), 0.28, 0.28, 'steelD', seg=8)
    C = A + d * 1.3
    R, f = 5.0, 3.4
    rs = dish(k, C, d, e1, e2, R, f)
    # backing structure: radial ribs on the back, a ring, the counterweight arm behind the axle
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        u = e1 * math.cos(a) + e2 * math.sin(a)
        p0 = C - d * 0.18 + u * 0.7
        p1 = C + u * (R * 0.92) + d * ((R * 0.92) ** 2 / (4 * f) - 0.2)
        beamv(k, p0, p1, 0.12, 'steelD', ink=False)
    k.tube(tuple(C - d * 0.15), tuple(A - d * 0.2), 0.75, 0.55, 'steel', seg=10)
    cw = A - d * 1.6 - e2 * 0.6
    beamv(k, A - d * 0.2, cw, 0.3, 'steelD', ink=False)
    k.hullp([tuple(cw + e1 * sx + e2 * sy + d * sz) for sx in (-0.8, 0.8) for sy in (-0.5, 0.5) for sz in (-0.4, 0.4)], 'graph')
    # the feed: a quadripod to the subreflector, the feed horn at the vertex
    F = C + d * f * 0.92
    for i in range(4):
        a = 2 * math.pi * (i + 0.5) / 4
        u = e1 * math.cos(a) + e2 * math.sin(a)
        r0 = R * 0.8
        P0 = C + u * r0 + d * (r0 * r0 / (4 * f) + 0.02)
        beamv(k, P0, F, 0.09, 'steel')
    k.tube(tuple(F - d * 0.05), tuple(F + d * 0.25), 0.62, 0.62, 'domeW', seg=12)
    k.tube(tuple(C + d * 0.02), tuple(C + d * 1.1), 0.45, 0.22, 'domeS', seg=10)
    k.tube(tuple(C + d * 1.1), tuple(C + d * 1.16), 0.22, 0.2, 'graph', seg=10, ink=False)
    # a red obstruction light on the subreflector
    k.sph(*(F + d * 0.32), 0.1, 'redL', seg=(6, 4))
    # access ladder up the housing
    k.push(0, 0, math.degrees(az) - 90)
    for s in (-0.22, 0.22):
        k.bx(s - 0.025, s + 0.025, 1.3, 1.36, 1.26, 3.9, 'yellow', ink=False, cull='b')
    for j in range(8):
        k.bx(-0.22, 0.22, 1.31, 1.35, 1.4 + j * 0.3, 1.43 + j * 0.3, 'yellow', ink=False)
    k.pop()
    disc_cols(k, 0, 0, 2.2, 0.0, 3.6)
    k.finish(name, ao=ao)
    k.begin()
    k.sph(*(F + d * 0.32), 0.12, 'redL', seg=(6, 4))
    k.finish(name + '_Glow')


def vsat(k, ao, name, az, el):
    """a 2.4 m VSAT dish on a ballasted ground frame"""
    k.begin()
    for (x0, x1, y0, y1) in ((-0.9, 0.9, -0.9, -0.6), (-0.9, 0.9, 0.6, 0.9)):
        k.bx(x0, x1, y0, y1, 0.0, 0.3, 'concD', cull='b')
    k.bx(-0.06, 0.06, -0.6, 0.6, 0.15, 0.27, 'steelD', ink=False)
    k.cyl(0, 0, 0.27, 0.08, 0.08, 1.2, 'steel', seg=6)
    d, e1, e2 = basis(az, el)
    A = V(0, 0, 1.5)
    C = A + d * 0.2
    dish(k, C, d, e1, e2, 1.2, 0.9, t=0.05, J=4, N=16)
    beamv(k, A - e2 * 0.3, A - e2 * 0.3 - d * 0.6 + V(0, 0, -0.9), 0.05, 'steel', ink=False)
    F = C + d * 0.85 + e2 * (-0.25)
    beamv(k, C + e2 * (-1.0) + d * 0.3, F, 0.05, 'steel')
    k.tube(tuple(F - d * 0.1), tuple(F + d * 0.12), 0.09, 0.07, 'graph', seg=6)
    k.col(-0.9, 0.9, -0.9, 0.9, 0.0, 0.3)
    k.col(-0.25, 0.25, -0.25, 0.25, 0.0, 1.6)
    k.finish(name, ao=ao)


def mast(k, ao):
    """a self-supporting lattice radio mast, 24 m, panel antennas, a work platform, beacons"""
    k.begin()
    k.bx(-1.45, 1.45, -1.45, 1.45, 0.0, 0.3, 'conc', cull='b')
    H, b0, b1, n = 24.0, 1.2, 0.4, 8
    def half(z):
        return b0 + (b1 - b0) * z / H
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    zs = [0.3 + (H - 0.3) * i / n for i in range(n + 1)]
    for (sx, sy) in corners:
        for a, b in zip(zs, zs[1:]):
            k.beam((sx * half(a), sy * half(a), a), (sx * half(b), sy * half(b), b), 0.1, 'redL' if int(b / 3) % 2 else 'paper')
    for i in range(4):
        (ax, ay), (bx_, by) = corners[i], corners[(i + 1) % 4]
        for j, (a, b) in enumerate(zip(zs, zs[1:])):
            ha, hb = half(a), half(b)
            p = (ax * ha, ay * ha, a)
            q = (bx_ * hb, by * hb, b)
            p2 = (bx_ * ha, by * ha, a)
            q2 = (ax * hb, ay * hb, b)
            k.beam(p, q, 0.045, 'steel', ink=False)
            ka, kb = 1 + 0.05 / ha, 1 + 0.05 / hb      # the second diagonal 5 cm outside the first (they cross)
            k.beam((p2[0] * ka, p2[1] * ka, a), (q2[0] * kb, q2[1] * kb, b), 0.05, 'steel', ink=False)
            t = 0.07 / max(0.1, math.hypot(q[0] - q2[0], q[1] - q2[1]))   # stop short of the legs
            k.beam((q2[0] + (q[0] - q2[0]) * t, q2[1] + (q[1] - q2[1]) * t, b), (q[0] - (q[0] - q2[0]) * t, q[1] - (q[1] - q2[1]) * t, b), 0.05, 'steelD', ink=False)
    # work platform at 18 m, panel antennas at 21 m, a whip to 27 m
    hz = half(18.0)
    k.bx(-hz - 0.35, hz + 0.35, -hz - 0.35, hz + 0.35, 17.9, 18.0, 'graph')
    for (x, y, deg) in ((0, -1, 0), (0.87, 0.5, 120), (-0.87, 0.5, 240)):
        k.push(x * (half(21) + 0.15), y * (half(21) + 0.15), deg)
        k.bx(-0.16, 0.16, -0.06, 0.06, 20.0, 21.6, 'domeW')
        k.pop()
    k.cyl(0, 0, H, 0.06, 0.03, 3.0, 'steel', seg=5)
    for z in (12.0, H + 3.0):
        k.sph(0, 0, z + 0.08, 0.12, 'redL', seg=(6, 4)) if z > H else None
    k.sph(half(12) + 0.08, 0, 12.0, 0.1, 'redL', seg=(6, 4))
    for (sx, sy) in corners:
        k.col(sx * 1.2 - 0.12, sx * 1.2 + 0.12, sy * 1.2 - 0.12, sy * 1.2 + 0.12, 0.0, 2.5)
    k.col(-1.45, 1.45, -1.45, 1.45, 0.0, 0.3)
    k.finish('Mast', ao=ao)
    k.begin()
    k.sph(0, 0, H + 3.08, 0.15, 'redL', seg=(6, 4))
    k.sph(half(12) + 0.08, 0, 12.0, 0.13, 'redL', seg=(6, 4))
    k.finish('Mast_Glow')


def shelter(k, ao):
    """an equipment shelter [6, 4]: insulated white box on skids, door on the front, a wall AC unit, cable port"""
    k.begin()
    k.bx(-2.8, 2.8, -1.6, 1.6, 0.0, 0.2, 'steelD', cull='b')
    k.bx(-2.7, 2.7, -1.5, 1.5, 0.2, 2.9, 'domeW')
    k.bx(-2.78, 2.78, -1.58, 1.58, 2.9, 3.0, 'steelD')
    k.snowcap(-2.76, 2.76, -1.56, 1.56, 3.0, 0.1)
    for x in (-1.8, -0.9, 0.9, 1.8):
        k.fq(x - 0.01, x + 0.01, -1.503, 0.25, 2.85, 'domeS')
    k.fq(-0.5, 0.5, -1.503, 0.2, 2.3, 'steelD')
    k.fq(-0.44, 0.44, -1.506, 0.24, 2.24, 'blueD')
    k.bx(0.26, 0.34, -1.58, -1.506, 1.1, 1.18, 'chrome', ink=False)
    k.fq(-2.5, -1.0, -1.507, 2.2, 2.6, 'blueS')
    k.text('VESPERLINK', -1.75, -1.511, 2.31, 0.2, 'paper', font='display', maxw=1.4)
    k.fq(1.2, 2.5, -1.507, 1.5, 1.9, 'yellow')
    k.text('HIGH VOLTAGE', 1.85, -1.511, 1.62, 0.13, 'black', font='display', maxw=1.2)
    # AC unit on the east end, cable entry port and its tray stub on the west end
    k.bx(2.7, 3.0, -0.8, 0.4, 1.0, 2.0, 'panelG')
    for j in range(5):
        k.rq(3.003, -0.75, 0.35, 1.08 + j * 0.18, 1.14 + j * 0.18, 'steelD')
    k.bx(-2.95, -2.7, -0.4, 0.4, 2.0, 2.4, 'steelD')
    k.col(-2.8, 2.8, -1.6, 1.6, 0.0, 3.0)
    k.col(2.7, 3.0, -0.8, 0.4, 1.0, 2.0)
    k.finish('Shelter', ao=ao)


def ground_station(k, ao):
    """the ground station building [10, 6]: a flat-roofed control building whose roof is a deck at 3 m (walkable),
    yellow rails round it except where the gantry (east, middle 2 m) and the stair (south, west 2 m) arrive"""
    H = TERR
    k.begin()
    k.bx(-5.0, 5.0, -3.0, 3.0, 0.0, 0.4, 'concD', cull='b')
    k.bx(-4.96, 4.96, -2.96, 2.96, 0.4, H - 0.25, 'domeW', cull='b')
    k.bx(-5.0, 5.0, -3.0, 3.0, H - 0.25, H, 'blueS')
    k.uq(-4.94, 4.94, -2.94, 2.94, H + 0.004, 'concL')
    for x in (-3.0, -1.0, 1.9):
        k.fq(x - 0.012, x + 0.012, -2.963, 0.45, H - 0.3, 'domeS')
    # the south front: entrance with canopy, windows, the name board
    k.fq(0.2, 1.4, -2.963, 0.4, 2.5, 'steelD')
    k.fq(0.26, 1.34, -2.966, 0.42, 2.44, 'glassD')
    k.fq(0.79, 0.81, -2.97, 0.42, 2.44, 'steelD')
    k.bx(-0.2, 1.8, -3.9, -3.0, 2.55, 2.68, 'steel')
    k.snowcap(-0.18, 1.78, -3.88, -3.02, 2.68, 0.06)
    for x0 in (-4.4, -2.6, 2.4, 3.6):
        k.fq(x0, x0 + 1.0, -2.963, 1.1, 2.2, 'steelD')
        k.fq(x0 + 0.05, x0 + 0.95, -2.966, 1.15, 2.15, 'glassD')
        k.fq(x0 + 0.08, x0 + 0.4, -2.969, 1.7, 2.05, 'glassL')
    k.text('VESPERLINK  GROUND STATION', 0.0, -3.004, H - 0.2, 0.17, 'paper', font='display', maxw=7.0)
    # side windows (east / west)
    for s in (-1, 1):
        for y0 in (-1.9, 0.9):
            k.push(0, 0, 90 if s > 0 else -90)
            k.fq(y0, y0 + 1.0, -4.963, 1.1, 2.2, 'steelD')
            k.fq(y0 + 0.05, y0 + 0.95, -4.966, 1.15, 2.15, 'glassD')
            k.pop()
    # the roof: rails (gaps for the gantry and the stair), an HVAC unit, a roof dish, whips, a cable riser
    def rail(a, b, axis, at):
        if axis == 'x':
            k.bx(a, b, at - 0.03, at + 0.03, H + 1.0, H + 1.06, 'yellow')
            k.bx(a, b, at - 0.015, at + 0.015, H + 0.5, H + 0.53, 'yellow', ink=False)
            for x in [a + 0.04] + [a + (b - a) * t for t in (0.33, 0.66)] + [b - 0.04]:
                k.bx(x - 0.03, x + 0.03, at - 0.03, at + 0.03, H, H + 1.0, 'steelD', ink=False)
            k.col(a, b, at - 0.06, at + 0.06, H, H + 1.06)
        else:
            k.bx(at - 0.03, at + 0.03, a, b, H + 1.0, H + 1.06, 'yellow')
            k.bx(at - 0.015, at + 0.015, a, b, H + 0.5, H + 0.53, 'yellow', ink=False)
            for y in [a + 0.04] + [a + (b - a) * t for t in (0.33, 0.66)] + [b - 0.04]:
                k.bx(at - 0.03, at + 0.03, y - 0.03, y + 0.03, H, H + 1.0, 'steelD', ink=False)
            k.col(at - 0.06, at + 0.06, a, b, H, H + 1.06)
    rail(-3.0, 4.92, 'x', -2.92)          # south (the stair arrives on x -5..-3)
    rail(-4.92, 4.92, 'x', 2.92)          # north
    rail(-2.86, 2.86, 'y', -4.92)         # west
    rail(-2.86, -1.0, 'y', 4.92)          # east, gap y -1..1 for the gantry
    rail(1.0, 2.86, 'y', 4.92)
    k.bx(-2.6, -0.4, 0.6, 2.2, H, H + 1.2, 'panelG')
    k.uq(-2.4, -0.6, 0.8, 2.0, H + 1.204, 'steelD')
    k.cyl(-1.5, 1.4, H + 1.204, 0.45, 0.45, 0.12, 'graph', seg=10)
    k.snowcap(-2.58, -0.42, 0.62, 0.78, H + 1.2, 0.05)
    k.col(-2.6, -0.4, 0.6, 2.2, H, H + 1.2)
    d, e1, e2 = basis(math.radians(-100), math.radians(40))
    A = V(2.8, 1.2, H + 1.3)
    k.cyl(2.8, 1.2, H + 0.12, 0.08, 0.08, 1.18, 'steel', seg=6)
    k.bx(2.4, 3.2, 0.8, 1.6, H, H + 0.12, 'concD', cull='b')
    dish(k, A + d * 0.15, d, e1, e2, 0.9, 0.7, t=0.04, J=3, N=14)
    k.col(2.4, 3.2, 0.8, 1.6, H, H + 1.6)
    for (x, y) in ((4.5, 2.5), (-4.5, 2.5)):
        k.cyl(x, y, H, 0.04, 0.025, 3.5, 'steel', seg=5)
    k.wcol(-5.0, 5.0, -3.0, 3.0, 0.0, H)
    k.finish('GroundStation', ao=ao)
    k.begin()
    for x0 in (-4.4, -2.6, 2.4, 3.6):
        k.fq(x0 + 0.42, x0 + 0.92, -2.972, 1.18, 1.6, 'lightW')
    k.finish('GroundStation_Glow')


def old_dome(k, ao):
    """the Halden Dome (1931), the landmark [12, 12]: a stone drum, a cornice, the copper dome with its slit open to
    the south-west and the old refractor looking out, a door with a porch, brass lettering"""
    k.begin()
    R, Hd = 5.0, 5.4
    k.cyl(0, 0, 0, R + 0.35, R + 0.3, 0.6, 'stoneD', seg=28)
    k.ring_wall(0, 0, R - 0.5, R, 0.6, Hd, 'stone', seg=28, top='stoneD')
    k.cyl(0, 0, 0.6, R - 0.52, R - 0.52, Hd - 0.62, 'stoneD', seg=20, ink=False, caps=True)   # the solid inside
    k.cyl(0, 0, Hd, R + 0.25, R + 0.25, 0.4, 'stoneL', seg=28)
    k.cyl(0, 0, Hd + 0.4, R + 0.27, R + 0.27, 0.06, 'snow', seg=28, ink=False)
    # the dome: copper, slit open (azimuth of the slit toward Blender -Y rotated 30 degrees west)
    Rd, zc = R + 0.1, Hd + 0.46
    slit_az, slit_w = math.radians(-120), math.radians(24)
    NA, NE = 28, 8
    verts, faces = [], []

    def inslit(a):
        da = (a - slit_az + math.pi) % (2 * math.pi) - math.pi
        return abs(da) < slit_w / 2
    rows = []
    for j in range(NE + 1):
        el = (math.pi / 2) * j / NE
        row = []
        for i in range(NA):
            a = 2 * math.pi * i / NA
            row.append(len(verts))
            verts.append((math.cos(a) * math.cos(el) * Rd, math.sin(a) * math.cos(el) * Rd, zc + math.sin(el) * Rd))
        rows.append(row)
    for j in range(NE):
        for i in range(NA):
            a = 2 * math.pi * (i + 0.5) / NA
            if inslit(a) and j < NE - 1:
                continue
            i2 = (i + 1) % NA
            faces.append((rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]))
    k.mesh(verts, faces, lambda f: 'copper' if f.normal.z < 0.93 else 'copperD', recalc=False)
    # the inside seen through the slit: a dark inner shell and the slit jambs
    inner = []
    for j in range(NE):
        el = (math.pi / 2) * j / NE
        inner.append([(math.cos(a) * math.cos(el) * (Rd - 0.2), math.sin(a) * math.cos(el) * (Rd - 0.2), zc + math.sin(el) * (Rd - 0.2)) for a in (slit_az - slit_w / 2 - 0.05, slit_az + slit_w / 2 + 0.05)])
    for j in range(NE - 1):
        k.poly([inner[j][0], inner[j][1], inner[j + 1][1], inner[j + 1][0]], 'domeInD', (-math.cos(slit_az), -math.sin(slit_az), 0.0))
    for side in (-1, 1):   # the shutter jambs (ribs either side of the slit)
        a = slit_az + side * slit_w / 2
        pts = []
        for j in range(NE):
            el = (math.pi / 2) * j / NE
            pts.append((math.cos(a) * math.cos(el) * (Rd + 0.08), math.sin(a) * math.cos(el) * (Rd + 0.08), zc + math.sin(el) * (Rd + 0.08)))
        for i2, (p, q) in enumerate(zip(pts, pts[1:])):
            k.beam(p, q, 0.16 + (0.01 if i2 % 2 else 0.0), 'copperD')
    # the refractor looking out of the slit
    d, e1, e2 = basis(slit_az, math.radians(32))
    A = V(0, 0, zc + 1.2)
    k.tube(tuple(A - d * 1.2), tuple(A + d * 3.6), 0.36, 0.3, 'paper', seg=10)
    k.tube(tuple(A + d * 3.6), tuple(A + d * 4.0), 0.36, 0.36, 'brass', seg=10)
    # the door and its porch on the south side, the brass name
    k.push(0, 0, 0)
    k.bx(-1.0, 1.0, -R - 0.9, -R + 0.3, 0.6, 3.2, 'stoneL')
    k.fq(-0.6, 0.6, -R - 0.903, 0.6, 2.7, 'woodD')
    k.fq(-0.55, -0.02, -R - 0.906, 0.65, 2.65, 'wood')
    k.fq(0.02, 0.55, -R - 0.906, 0.65, 2.65, 'wood')
    k.bx(-1.2, 1.2, -R - 1.1, -R + 0.3, 3.2, 3.45, 'copperD')
    k.snowcap(-1.18, 1.18, -R - 1.08, -R + 0.28, 3.45, 0.07)
    k.bx(-1.1, 1.1, -R - 1.4, -R - 0.9, 0.0, 0.3, 'stoneD', cull='b')
    k.bx(-1.1, 1.1, -R - 1.15, -R - 0.9, 0.3, 0.6, 'stoneD', cull='b')
    k.text('HALDEN DOME 1931', 0.0, -R - 0.904, 2.85, 0.22, 'brass', font='serif', maxw=1.9)
    k.pop()
    # a lightning rod finial and the slit's shutter track on the dome top
    k.cyl(0, 0, zc + Rd - 0.05, 0.12, 0.08, 0.5, 'copperD', seg=6)
    disc_cols(k, 0, 0, R + 0.3, 0.0, Hd + 3.0)
    k.col(-1.0, 1.0, -R - 0.9, -R + 0.3, 0.0, 3.45)
    k.col(-1.1, 1.1, -R - 1.4, -R - 0.9, 0.0, 0.6)
    k.finish('Landmark_OldDome', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.bx(s * 0.8 - 0.08, s * 0.8 + 0.08, -R - 1.0, -R - 0.92, 2.6, 2.9, 'amberL', ink=False)
    k.finish('Landmark_OldDome_Glow')


def vehicles(k, ao):
    # the snowcat [3, 5] (front toward Blender -Y): orange body, a glazed cab, twin tracks, the front blade
    k.begin()
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.75, s * 1.45))
        k.bx(x0, x1, -1.6, 1.8, 0.15, 0.85, 'rubber')
        for y in (-1.6, 1.8):
            k.cyl(x0 + 0.015, y, 0.5, 0.35, 0.35, x1 - x0 - 0.03, 'rubber', seg=10, rot=(0, 90, 0))
        for y in (-1.0, -0.2, 0.6, 1.4):
            k.cyl(x0 - 0.01, y, 0.42, 0.24, 0.24, x1 - x0 + 0.02, 'steelD', seg=8, rot=(0, 90, 0), ink=False)
        for j in range(9):
            y = -1.5 + j * 0.38
            k.bx(x0 - 0.005, x1 + 0.005, y, y + 0.08, 0.85, 0.88, 'graph', ink=False)
    k.bx(-1.1, 1.1, -1.4, 2.1, 0.8, 1.5, 'orange')
    k.bx(-1.0, 1.0, -0.9, 1.0, 1.5, 2.6, 'orange')
    k.fq(-0.9, 0.9, -0.903, 1.6, 2.45, 'glassD')
    k.fq(-0.8, -0.2, -0.906, 2.0, 2.4, 'glassL')
    for s in (-1, 1):
        k.push(0, 0, 90 if s > 0 else -90)
        k.fq(-0.8, 0.85, -1.003, 1.6, 2.45, 'glassD')
        k.pop()
    k.bx(-1.04, 1.04, -0.94, 1.04, 2.6, 2.68, 'black')
    k.snowcap(-1.0, 1.0, -0.9, 1.0, 2.68, 0.06)
    k.bx(-0.2, 0.2, 0.0, 0.3, 2.74, 2.86, 'amberL')
    k.bx(-1.65, 1.65, -2.45, -2.2, 0.15, 1.05, 'steelD')
    k.fq(-1.6, 1.6, -2.453, 0.2, 1.0, 'yellow')
    for x in (-0.9, 0.9):
        k.beam((x, -2.2, 0.6), (x, -1.4, 1.0), 0.12, 'steelD')
    k.fq(-0.8, 0.8, -1.403, 0.9, 1.4, 'black')
    k.text('VESPER 2', 0.0, -1.406, 1.0, 0.24, 'paper', font='display', maxw=1.2)
    k.bx(-1.0, 1.0, 2.1, 2.5, 0.35, 0.8, 'graph')
    k.col(-1.5, 1.5, -2.0, 2.2, 0.0, 1.5)
    k.col(-1.65, 1.65, -2.45, -2.0, 0.15, 1.05)
    k.col(-1.0, 1.0, -0.9, 1.0, 1.5, 2.7)
    k.finish('Snowcat', ao=ao)
    k.begin()
    k.bx(-0.18, 0.18, 0.02, 0.28, 2.75, 2.87, 'amberL', ink=False)
    for s in (-1, 1):
        k.fq(s * 0.85 - 0.15, s * 0.85 + 0.15, -1.405, 1.2, 1.35, 'lightW')
    k.finish('Snowcat_Glow')

    # the fuel tank [2, 5]: a horizontal diesel tank on two saddles, ladder, gauge, the DIESEL stencil
    k.begin()
    for y in (-1.5, 1.5):
        k.bx(-0.85, 0.85, y - 0.2, y + 0.2, 0.0, 0.6, 'concD', cull='b')
    k.cyl(0, 2.3, 1.45, 0.9, 0.9, 4.6, 'domeW', seg=16, rot=(90, 0, 0))
    k.cyl(0, 2.31, 1.45, 0.92, 0.92, 0.06, 'steelD', seg=16, rot=(90, 0, 0))
    k.cyl(0, -2.25, 1.45, 0.92, 0.92, 0.06, 'steelD', seg=16, rot=(90, 0, 0))
    k.cyl(0, 0.6, 2.33, 0.25, 0.25, 0.22, 'steelD', seg=8)
    k.bx(0.88, 0.92, -0.6, -0.3, 0.0, 2.3, 'yellow', ink=False)
    k.col(-0.9, 0.9, -2.3, 2.3, 0.0, 2.36)
    k.finish('FuelTank', ao=ao)

    # the generator house [4, 3] (front -Y): a louvred enclosure, the exhaust stack, a fuel line
    k.begin()
    k.bx(-1.95, 1.95, -1.45, 1.45, 0.0, 0.25, 'concD', cull='b')
    k.bx(-1.85, 1.85, -1.3, 1.3, 0.25, 2.6, 'domeS')
    k.bx(-1.92, 1.92, -1.37, 1.37, 2.6, 2.72, 'steelD')
    k.snowcap(-1.9, 1.9, -1.35, 1.35, 2.72, 0.08)
    for j in range(8):
        z = 0.6 + j * 0.2
        k.fq(-1.6, -0.2, -1.303, z, z + 0.08, 'steelD')
        k.fq(0.2, 1.6, -1.303, z, z + 0.08, 'steelD')
    k.fq(-0.6, 0.6, -1.303, 2.12, 2.46, 'yellow')
    k.text('GENERATOR 2', 0.0, -1.306, 2.2, 0.16, 'black', font='display', maxw=1.1)
    k.cyl(1.2, 0.6, 2.72, 0.16, 0.16, 1.6, 'steelD', seg=8)
    k.cyl(1.2, 0.6, 4.32, 0.2, 0.2, 0.12, 'black', seg=8)
    k.col(-1.95, 1.95, -1.45, 1.45, 0.0, 2.8)
    k.finish('GenHouse', ao=ao)


def small_props(k, ao):
    rnd = random.Random(4212)
    # weather mast: anemometer, vane, radiation shield, solar panel, logger box
    k.begin()
    k.bx(-0.35, 0.35, -0.35, 0.35, 0.0, 0.25, 'conc', cull='b')
    k.cyl(0, 0, 0.25, 0.06, 0.05, 5.8, 'steel', seg=6)
    k.bx(-0.7, 0.7, -0.03, 0.03, 5.6, 5.66, 'steelD')
    k.cyl(-0.7, 0, 5.66, 0.02, 0.02, 0.3, 'steel', seg=4, ink=False)
    for i in range(3):
        a = 2 * math.pi * i / 3
        k.sph(-0.7 + math.cos(a) * 0.16, math.sin(a) * 0.16, 5.96, 0.06, 'black', seg=(6, 4))
    k.cyl(0.7, 0, 5.66, 0.02, 0.02, 0.2, 'steel', seg=4, ink=False)
    k.bx(0.6, 0.95, -0.01, 0.01, 5.86, 5.98, 'black')
    for j in range(5):
        k.cyl(0.2, 0, 3.0 + j * 0.06, 0.14 - j * 0.01, 0.14 - j * 0.01, 0.04, 'paper', seg=8, ink=j == 0)
    k.bxr(0, -0.25, 2.2, 0.6, 0.03, 0.45, 'navy', rot=(35, 0, 0))
    k.bx(-0.18, 0.18, 0.06, 0.26, 1.0, 1.45, 'domeW')
    k.col(-0.35, 0.35, -0.35, 0.35, 0.0, 0.25)
    k.col(-0.12, 0.12, -0.12, 0.12, 0.0, 2.4)
    k.finish('WeatherMast', ao=ao)
    # all-sky camera: a glass bubble on a post
    k.begin()
    k.cyl(0, 0, 0, 0.18, 0.18, 0.12, 'conc', seg=8)
    k.cyl(0, 0, 0.12, 0.07, 0.07, 1.4, 'steel', seg=6)
    k.cyl(0, 0, 1.52, 0.2, 0.2, 0.18, 'graph', seg=10)
    k.sph(0, 0, 1.7, 0.16, 'glassL', seg=(10, 5))
    k.col(-0.2, 0.2, -0.2, 0.2, 0.0, 1.86)
    k.finish('SkyCam', ao=ao)
    # lamp post (LED head toward Blender -Y)
    k.begin()
    k.cyl(0, 0, 0, 0.16, 0.14, 0.3, 'conc', seg=8)
    k.cyl(0, 0, 0.3, 0.07, 0.05, 4.2, 'graph', seg=6)
    k.beam((0, 0, 4.4), (0, -0.7, 4.55), 0.06, 'graph')
    k.bx(-0.16, 0.16, -1.05, -0.55, 4.48, 4.6, 'graph')
    k.dq(-0.13, 0.13, -1.02, -0.58, 4.476, 'lightW')
    k.col(-0.14, 0.14, -0.14, 0.14, 0.0, 2.6)
    k.finish('Lamp', ao=ao)
    k.begin()
    k.dq(-0.12, 0.12, -1.01, -0.59, 4.47, 'lightW')
    k.finish('Lamp_Glow')
    # rocks with snow on their tops
    from kit_base import rock_pts
    for name, seed, rx, ry, h in (('Rock_A', 11, 0.48, 0.42, 0.8), ('Rock_B', 23, 0.46, 0.46, 1.15)):
        k.begin()
        r = random.Random(seed)
        pts = rock_pts(r, (0, 0), rx, ry, h, n=7, top=3)
        k.hullp(pts, lambda f: 'snow' if f.normal.z > 0.72 else ('rockL' if f.normal.z > 0.3 else 'rock'))
        k.col(-rx * 0.8, rx * 0.8, -ry * 0.8, ry * 0.8, 0.0, h * 0.9)
        k.finish(name, ao=ao)
    k.begin()
    r = random.Random(77)
    k.hullp(rock_pts(r, (-0.25, 0.1), 0.95, 0.85, 1.7, n=8, top=4), lambda f: 'snow' if f.normal.z > 0.7 else ('rockL' if f.normal.z > 0.3 else 'rock'))
    k.hullp(rock_pts(r, (0.55, -0.45), 0.42, 0.4, 0.9, n=6, top=2), lambda f: 'snow' if f.normal.z > 0.7 else ('rockD' if f.normal.z < 0.2 else 'rock'))
    k.col(-0.95, 0.6, -0.6, 0.85, 0.0, 1.6)
    k.col(0.2, 0.9, -0.82, -0.1, 0.0, 0.85)
    k.finish('Outcrop', ao=ao)
    # flight cases / crates
    for name, sz, c, word in (('Case_A', (0.8, 0.55, 0.6), 'navy', 'OPTICS'), ('Case_B', (0.9, 0.7, 0.8), 'graph', 'RF UNIT'), ('Case_C', (0.7, 0.7, 1.0), 'woodL', 'FRAGILE')):
        k.begin()
        w, d, h = sz
        k.bx(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, c)
        for z in (0.06, h - 0.1):
            k.bx(-w / 2 - 0.012, w / 2 + 0.012, -d / 2 - 0.012, d / 2 + 0.012, z, z + 0.04, 'steel', ink=False)
        k.fq(-w / 2 + 0.08, w / 2 - 0.08, -d / 2 - 0.016, h * 0.4, h * 0.62, 'yellow' if c != 'woodL' else 'paper')
        k.text(word, 0.0, -d / 2 - 0.019, h * 0.51, 0.1, 'black' if c != 'woodL' else 'redL', font='display', maxw=w - 0.2, valign='m')
        k.snowcap(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, h, 0.04) if c == 'woodL' else None
        k.col(-w / 2, w / 2, -d / 2, d / 2, 0.0, h)
        k.finish(name, ao=ao)
    # gas bottles in a cage
    k.begin()
    k.bx(-0.45, 0.45, -0.3, 0.3, 0.0, 0.06, 'steelD', cull='b')
    for i, c in enumerate(('blueS', 'blueS', 'paper')):
        x = -0.28 + i * 0.28
        k.cyl(x, 0.02, 0.06, 0.12, 0.12, 1.25, c, seg=8)
        k.sph(x, 0.02, 1.31, 0.11, c, seg=(8, 4))
        k.cyl(x, 0.02, 1.38, 0.03, 0.03, 0.12, 'brass', seg=5, ink=False)
    k.bx(-0.43, 0.43, -0.31, -0.28, 0.9, 0.95, 'steel', ink=False)
    for s in (-1, 1):
        k.bx(s * 0.45 - 0.02, s * 0.45, -0.3, 0.3, 0.06, 1.5, 'steel', ink=False)
    k.col(-0.45, 0.45, -0.3, 0.3, 0.0, 1.5)
    k.finish('Cylinders', ao=ao)
    # cable drum
    k.begin()
    for s in (-1, 1):
        k.cyl(s * 0.32, 0, 0.5, 0.5, 0.5, 0.06, 'woodL', seg=12, rot=(0, 90, 0))
    k.cyl(-0.29, 0, 0.5, 0.36, 0.36, 0.58, 'black', seg=10, rot=(0, 90, 0))
    k.col(-0.38, 0.38, -0.45, 0.45, 0.0, 1.0)
    k.finish('Drum', ao=ao)
    # the summit cairn with its brass plaque
    k.begin()
    r = random.Random(4212)
    from kit_base import rock_pts as rp
    k.hullp(rp(r, (0, 0), 0.48, 0.48, 1.3, n=8, top=3, waist=(0.4, 0.7)), lambda f: 'snow' if f.normal.z > 0.75 else 'rockL')
    k.bxr(0, -0.42, 0.7, 0.44, 0.03, 0.3, 'brass', rot=(-12, 0, 0))
    k.col(-0.38, 0.38, -0.38, 0.38, 0.0, 1.25)
    k.finish('Cairn', ao=ao)
    # the panorama board [2, 1]: a steel lectern whose face shows the peaks round the summit
    k.begin()
    for x in (-0.8, 0.8):
        k.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.0, 0.9, 'steelD', cull='b')
    k.bx(-0.95, 0.95, -0.1, 0.1, 0.9, 1.6, 'steelD')
    k.fq(-0.9, 0.9, -0.103, 0.95, 1.55, 'navy')
    ridge = [(-0.88, 1.05), (-0.62, 1.24), (-0.4, 1.12), (-0.12, 1.38), (0.14, 1.16), (0.42, 1.3), (0.66, 1.1), (0.88, 1.18)]
    for (xa, za), (xb, zb) in zip(ridge, ridge[1:]):
        k.poly([(xa, -0.106, 0.98), (xb, -0.106, 0.98), (xb, -0.106, zb), (xa, -0.106, za)], 'rockL', (0, -1, 0))
    for (x, z) in ((-0.62, 1.24), (-0.12, 1.38), (0.42, 1.3)):
        k.poly([(x - 0.06, -0.109, z - 0.06), (x + 0.06, -0.109, z - 0.06), (x, -0.109, z)], 'snow', (0, -1, 0))
    k.text('THE PEAKS OF THE CLOUD SEA', 0.0, -0.109, 1.44, 0.07, 'paper', font='display', maxw=1.6)
    k.snowcap(-0.93, 0.93, -0.08, 0.08, 1.6, 0.04)
    k.col(-0.95, 0.95, -0.1, 0.1, 0.0, 1.64)
    k.finish('Panorama', ao=ao)
    # outdoor equipment cabinet (one cell, rotate edge: the door toward the open side)
    k.begin()
    k.bx(-0.42, 0.42, -0.32, 0.32, 0.0, 0.2, 'concD', cull='b')
    k.bx(-0.38, 0.38, -0.28, 0.28, 0.2, 1.75, 'panelG')
    k.bx(-0.42, 0.42, -0.32, 0.32, 1.75, 1.83, 'steelD')
    k.snowcap(-0.4, 0.4, -0.3, 0.3, 1.83, 0.05)
    k.fq(-0.34, 0.34, -0.283, 0.28, 1.68, 'steel')
    for j in range(4):
        k.fq(-0.26, 0.26, -0.286, 1.3 + j * 0.08, 1.34 + j * 0.08, 'steelD')
    k.fq(0.2, 0.26, -0.286, 0.8, 0.95, 'black')
    k.fq(-0.2, 0.1, -0.286, 0.5, 0.62, 'yellow')
    k.col(-0.42, 0.42, -0.32, 0.32, 0.0, 1.83)
    k.finish('Cabinet', ao=ao)
    # bench [2, 1]
    k.begin()
    for s in (-0.75, 0.75):
        k.bx(s - 0.05, s + 0.05, -0.2, 0.2, 0.0, 0.42, 'graph', cull='b')
    k.bx(-0.95, 0.95, -0.22, 0.22, 0.42, 0.48, 'wood')
    k.bx(-0.95, 0.95, 0.14, 0.2, 0.55, 0.9, 'wood')
    k.snowcap(-0.93, 0.93, -0.2, 0.2, 0.48, 0.03)
    k.col(-0.95, 0.95, -0.22, 0.22, 0.0, 0.5)
    k.finish('Bench', ao=ao)
    # overhead cable bridge (rotate 'run': along Blender X): a tray at 2.6 m; A with its post
    for name, post in (('Cable_A', True), ('Cable_B', False)):
        k.begin()
        k.bx(-0.5, 0.5, -0.22, 0.22, 2.56, 2.62, 'steel', cull='')
        for s in (-1, 1):
            k.bx(-0.5, 0.5, s * 0.22 - 0.015, s * 0.22 + 0.015, 2.62, 2.8, 'steel', ink=False)
        for y in (-0.1, 0.0, 0.1):
            k.cyl(-0.5, y, 2.68, 0.035, 0.035, 1.0, 'black', seg=5, rot=(0, 90, 0), ink=False)
        k.col(-0.5, 0.5, -0.22, 0.22, 2.56, 2.8)    # the tray itself (overhead: nobody walks into it)
        if post:
            k.bx(-0.06, 0.06, -0.06, 0.06, 0.0, 2.5, 'steelD', cull='b')
            k.bx(-0.07, 0.07, -0.3, 0.3, 2.5, 2.555, 'steelD', ink=False)
            k.col(-0.07, 0.07, -0.07, 0.07, 0.0, 2.56)
        k.finish(name, ao=ao)
    # the visitor telescope: a white refractor on a pier
    k.begin()
    k.cyl(0, 0, 0, 0.22, 0.18, 1.1, 'conc', seg=8)
    k.bx(-0.12, 0.12, -0.12, 0.12, 1.1, 1.3, 'graph')
    d, e1, e2 = basis(math.radians(-60), math.radians(30))
    A = V(0, 0, 1.42)
    k.tube(tuple(A - d * 0.5), tuple(A + d * 0.9), 0.1, 0.09, 'paper', seg=8)
    k.tube(tuple(A + d * 0.9), tuple(A + d * 1.05), 0.11, 0.11, 'black', seg=8)
    k.col(-0.22, 0.22, -0.22, 0.22, 0.0, 1.3)
    k.finish('VisitorScope', ao=ao)


def signs(k, ao):
    """facade signs [12, 1] placed in the open cell in front of a wall, their backs 1 cm off the wall face (+Y)"""
    def sign(k, word, sub, z0, bg, fg):
        k.bx(-5.9, 5.9, 0.36, 0.49, z0, z0 + 1.2, bg, cull='k')
        k.fq(-5.8, 5.8, 0.357, z0 + 0.06, z0 + 0.1, fg)
        k.text(word, 0.0, 0.354, z0 + 0.28, 0.6, fg, font='display', maxw=10.8)
        if sub:
            k.text(sub, 0.0, 0.354, z0 + 0.1, 0.14, fg, font='display', maxw=6.0)
    faces(k, ao, 'Sign_Station', lambda k: sign(k, 'VESPER SUMMIT RAILWAY', 'UPPER STATION  4212 M', 7.95, 'graph', 'amberL'))
    faces(k, ao, 'Sign_Annex', lambda k: sign(k, 'VESPER PEAK OBSERVATORY', 'THE GREAT DOME  VISITORS AND STAFF', 7.0, 'blueD', 'paper'))


def faces(k, ao, name, fn):
    k.begin()
    fn(k)
    k.finish(name, ao=ao)


def build_summit(k, ao):
    big_dish(k, ao, 'Dish_A', math.radians(-120), math.radians(32))
    big_dish(k, ao, 'Dish_B', math.radians(-60), math.radians(48))
    vsat(k, ao, 'Vsat_A', math.radians(-110), math.radians(38))
    vsat(k, ao, 'Vsat_B', math.radians(-70), math.radians(30))
    mast(k, ao)
    shelter(k, ao)
    ground_station(k, ao)
    old_dome(k, ao)
    vehicles(k, ao)
    small_props(k, ao)
    signs(k, ao)
