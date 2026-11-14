"""kit-observatory modelled detail (tactical look plan Stage 11): dome rib seams with rivets, base-ring bolts, dish panel
lines and pedestal plates, hatch / door frames with heavy hinges, window frames with depth, conduit and trays on the lab
and hall walls, railing foot plates, telescope bolt circles and cable carriers. Every part is ink=False (no outline
shell), >= 3 mm proud, embedded 3 mm, runs inset 5 mm from the piece sides. `DKit.finish` calls the detail function
registered for a piece name just before the piece is closed, so no piece builder changes (names, origins, footprints and
collision boxes stay as they were). Faces facing Blender -Y use the kit_base helpers at plane y = yf; for other faces
`k.push(x, y, deg)` first."""
import math

from mathutils import Vector

from kit_base import (EMBED, bolt_row, rivet_strip, kick_plate, conduit_run, pipe_run, junction_box, vent,
                      cable_tray, window_frame_depth)
import ob_base as B
import ob_summit as SU
import ob_dome as D
from ob_base import TERR, DOOR_H, Y0, YA


def pl(k, x0, x1, y0, y1, z0, z1, c):
    """a detail box (no outline); y0 is the proud face, y1 the buried one"""
    k.bx(x0, x1, y0, y1, z0, z1, c, ink=False)


def strip(k, p0, p1, nrm, w, c, off, gap=0.025):
    """a flat strip along p0 -> p1 lying `off` above the surface (normal nrm), w wide across, short of both ends by
    `gap` (strips that follow a bending surface never overlap at their joints)"""
    p0, p1, n = Vector(p0), Vector(p1), Vector(nrm).normalized()
    u = (p1 - p0).normalized()
    p0, p1 = p0 + u * gap, p1 - u * gap
    t = (p1 - p0).cross(n).normalized() * (w / 2)
    a, b = p0 + n * off, p1 + n * off
    k.poly([tuple(a - t), tuple(b - t), tuple(b + t), tuple(a + t)], c, tuple(n))


def rad(k, x, y, z, s, h, c, push=0.0):
    """a small square bolt head at (x, y, z), turned to face away from the z axis, protruding about s/2 + push"""
    a = math.degrees(math.atan2(y, x))
    k.bxr(x, y, z, s, s, h, c, rot=(0, 0, a), ink=False)


# ------------------------------------------------------------------------------------------------ domes
def old_dome(k):
    R, Hd = 5.0, 5.4
    # stone courses round the drum (thin bands, 12 mm proud of the faceted wall)
    for z in (1.5, 2.4, 3.3, 4.2, 5.0):
        k.cyl(0, 0, z, R + 0.012, R + 0.012, 0.03, 'stoneD', seg=28, ink=False, caps=False)
    # copper dome: meridian ribs along the mesh edges with rivets, a base band with bolts (the slit is left open)
    Rd, zc = R + 0.1, Hd + 0.46
    NA, NE = 28, 8
    slit_az = math.radians(-120)

    def far(a):
        return abs((a - slit_az + math.pi) % (2 * math.pi) - math.pi) < math.radians(26)

    def pt(i, j, r=Rd):
        a = 2 * math.pi * i / NA
        el = (math.pi / 2) * j / NE
        return (math.cos(a) * math.cos(el) * r, math.sin(a) * math.cos(el) * r, zc + math.sin(el) * r)
    for i in range(0, NA, 2):
        if far(2 * math.pi * i / NA):
            continue
        for j in range(0, NE - 1):
            k.beam(pt(i, j), pt(i, j + 1), 0.05 + (0.008 if j % 2 else 0.0), 'copperD', ink=False)
        for j in (2, 5):
            x, y, z = pt(i, j)
            rad(k, x, y, z, 0.075, 0.075, 'brass')
    for i in range(NA):
        a0, a1 = 2 * math.pi * i / NA, 2 * math.pi * (i + 1) / NA
        if far(a0) and far(a1) or far((a0 + a1) / 2):
            continue
        r = Rd + 0.015
        k.poly([(r * math.cos(a0), r * math.sin(a0), zc + 0.02), (r * math.cos(a1), r * math.sin(a1), zc + 0.02),
                (r * math.cos(a1), r * math.sin(a1), zc + 0.2), (r * math.cos(a0), r * math.sin(a0), zc + 0.2)],
               'copperD', (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0))
        if i % 2 == 0:
            x, y = Rd * math.cos(a0) * 1.0, Rd * math.sin(a0)
            rad(k, x, y, zc + 0.11, 0.06, 0.06, 'brass')
    # the porch door: frame, three strap hinges, a pull
    yf = -R - 0.9
    pl(k, -0.7, -0.6, yf - 0.03, yf + EMBED, 0.604, 2.696, 'stoneD')
    pl(k, 0.6, 0.7, yf - 0.03, yf + EMBED, 0.604, 2.696, 'stoneD')
    pl(k, -0.7, 0.7, yf - 0.03, yf + EMBED, 2.7, 2.78, 'stoneD')
    for z in (0.95, 1.65, 2.35):
        pl(k, -0.57, -0.2, yf - 0.025, yf + EMBED, z - 0.05, z + 0.05, 'black')
        pl(k, -0.58, -0.54, yf - 0.032, yf + 0.007, z - 0.07, z + 0.07, 'black')
    pl(k, 0.38, 0.44, yf - 0.05, yf + EMBED, 1.3, 1.7, 'brass')


def dish(k, name):
    az, el = (math.radians(-120), math.radians(32)) if name == 'Dish_A' else (math.radians(-60), math.radians(48))
    # pedestal housing, in the housing's own turn
    k.push(0, 0, math.degrees(az) - 90)
    yf = -1.3
    for x in (-0.85, 0.85):
        pl(k, x - 0.007, x + 0.007, yf - 0.006, yf + EMBED, 1.3, 2.85, 'domeS')
    for x in (-1.3, 1.3):                         # vertical corner guards
        pl(k, x - 0.06 if x > 0 else x + 0.004, x - 0.004 if x > 0 else x + 0.06, yf - 0.008, yf + EMBED, 1.26, 3.55, 'steelD')
    # the access hatch: frame, two heavy hinges, a lever handle
    pl(k, -0.58, -0.5, yf - 0.012, yf + EMBED, 1.24, 2.68, 'steelD')
    pl(k, 0.5, 0.58, yf - 0.012, yf + EMBED, 1.24, 2.68, 'steelD')
    pl(k, -0.5, 0.5, yf - 0.012, yf + EMBED, 2.6, 2.68, 'steelD')
    for z in (1.55, 2.35):
        pl(k, -0.6, -0.51, yf - 0.026, yf + 0.007, z - 0.08, z + 0.08, 'graph')
    pl(k, 0.34, 0.42, yf - 0.028, yf + EMBED, 1.75, 2.15, 'chrome')
    # base plate with anchor bolts under the housing
    pl(k, -1.5, 1.5, -1.5, 1.5, 1.22, 1.34, 'steelD')
    for (x, y) in ((-1.0, -1.4), (1.0, -1.4), (-1.4, 0.0), (1.4, 0.0), (-1.0, 1.4), (1.0, 1.4)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 1.337, 1.352, 'chrome', ink=False)
    # the azimuth bearing: bolt circle on the turntable
    for i in range(4):
        a = math.radians(7.5 + 90 * i)                  # centred on a facet of the 12-sided bearing
        rad(k, math.cos(a) * 1.083, math.sin(a) * 1.083, 3.78, 0.07, 0.07, 'chrome')
    k.pop()
    # the reflector: radial panel lines and two panel rings on the front surface, bolt plates at the feed arm feet
    d, e1, e2 = SU.basis(az, el)
    C = Vector((0, 0, 5.2)) + d * 1.3
    R, f, N = 5.0, 3.4, 24
    rs = [R * (0.12 + 0.88 * j / 4) for j in range(5)]

    def sp(r, i, off):
        a = 2 * math.pi * i / N
        return C + e1 * (r * math.cos(a)) + e2 * (r * math.sin(a)) + d * (r * r / (4 * f) + off)
    for i in range(0, N, 2):
        for j in range(1, 4):
            strip(k, sp(rs[j], i, 0), sp(rs[j + 1], i, 0), d, 0.03, 'domeS', 0.004)
    for j in (3,):
        for i in range(N):
            strip(k, sp(rs[j], i, 0), sp(rs[j], i + 1, 0), d, 0.03, 'domeS', 0.008)
    for i in range(4):
        a = 2 * math.pi * (i + 0.5) / 4
        u = e1 * math.cos(a) + e2 * math.sin(a)
        r0 = R * 0.8
        P0 = C + u * r0 + d * (r0 * r0 / (4 * f) + 0.02)
        k.hullp([tuple(P0 + e1 * su * 0.12 + e2 * sv * 0.12 + d * sw * 0.014 - d * 0.008) for su in (-1, 1) for sv in (-1, 1) for sw in (-1, 1)], 'steelD', ink=False)


def great_dome(k):
    outer = D.dome_rings(D.RD_OUT)
    n = len(outer[0])
    R = D.RD_OUT

    def sc(p, off):
        v = Vector(p)
        return tuple(v * ((R + off) / R))

    def nrm(p):
        return p
    for i in range(2, n - 2, 2):
        for j in range(len(outer) - 1):
            a, b = outer[j][i], outer[j + 1][i]
            if j + 1 == len(outer) - 1 and abs(b[0]) < D.SLIT + 0.3:
                continue
            strip(k, a, b, a, 0.05, 'domeS', 0.004)
    for j in (3, 6):
        for i in range(1, n - 2):
            strip(k, outer[j][i], outer[j][i + 1], outer[j][i], 0.045, 'domeS', 0.008)
    for i in range(4, n - 4, 4):
        for j in (2, 5):
            x, y, z = outer[j][i]
            rad(k, x, y, z, 0.06, 0.06, 'steel')
    # bolts along the ring beam on the wall tops
    for i in range(24):
        a = 2 * math.pi * (i + 0.5) / 24
        rad(k, math.cos(a) * 23.55, math.sin(a) * 23.55, 0.357, 0.12, 0.02, 'steel')


def telescope(k):
    # pier: a bolt circle on the azimuth platform's yellow ring, one on the turntable top
    for i in range(16):
        a = 2 * math.pi * (i + 0.5) / 16
        x, y = math.cos(a) * 4.65, math.sin(a) * 4.65
        k.bxr(x, y, 2.4075, 0.12, 0.12, 0.016, 'chrome', rot=(0, 0, math.degrees(a)), ink=False)
    for i in range(12):
        a = 2 * math.pi * i / 12
        x, y = math.cos(a) * 2.2, math.sin(a) * 2.2
        k.bxr(x, y, 2.9, 0.1, 0.1, 0.012, 'chrome', rot=(0, 0, math.degrees(a)), ink=False)
    # cable carrier links up the outside of each fork arm
    ang = math.degrees(math.atan2(1.1, 7.0))
    for s in (-1, 1):
        for n in range(8):
            z = 3.15 + n * 0.42
            y = 2.4 - 1.1 * (z - 2.9) / 7.0 - 0.45
            k.bxr(s * 4.259, y, z, 0.126, 0.2, 0.36, 'graph', rot=(ang, 0, 0), ink=False)
        for n in (0, 4, 7):
            z = 3.15 + n * 0.42
            y = 2.4 - 1.1 * (z - 2.9) / 7.0 - 0.45
            k.bxr(s * 4.283, y, z, 0.166, 0.26, 0.05, 'yellow', rot=(ang, 0, 0), ink=False)


def ring(k):
    # foot plates under every rail post, in the layout the builder uses
    for r, n, cut in ((D.R_IN + 0.06, 40, False), (D.R_OUT - 0.06, 56, True)):
        pts = [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r) for i in range(n + 1)]
        run, runs = [], []
        for (x, y) in pts:
            if cut and D.ring_open(x, y, r):
                if len(run) > 1:
                    runs.append(run)
                run = []
            else:
                run.append((x, y))
        if len(run) > 1:
            runs.append(run)
        if len(runs) > 1 and runs[0][0] == runs[-1][-1]:
            runs[0] = runs.pop() + runs[0][1:]
        for rn in runs:
            closed = math.hypot(rn[0][0] - rn[-1][0], rn[0][1] - rn[-1][1]) < 1e-6
            for j, (x, y) in enumerate(rn):
                if closed and j == len(rn) - 1:
                    continue
                if j % 2 == 0 or j == len(rn) - 1:
                    k.bxr(x, y, 0.004, 0.15, 0.15, 0.016, 'steel', rot=(0, 0, math.degrees(math.atan2(y, x))), ink=False)


# ------------------------------------------------------------------------------------------------ summit buildings
def ground_station(k):
    H = TERR
    for (yf, push) in ((-2.96, None), (-4.96, 90), (-4.96, -90)):
        if push is not None:
            k.push(0, 0, push)
        wins = (-4.4, -2.6, 2.4, 3.6) if push is None else (-1.9, 0.9)
        for x0 in wins:
            window_frame_depth(k, x0, x0 + 1.0, 1.1, 2.2, yf, 'steel', depth=0.05, t=0.04)
        if push is not None:
            k.pop()
    # the entrance: heavy door frame, hinges, push bar
    yf = -2.96
    pl(k, 0.12, 0.2, yf - 0.03, yf + EMBED, 0.4, 2.5, 'steelD')
    pl(k, 1.4, 1.48, yf - 0.03, yf + EMBED, 0.4, 2.5, 'steelD')
    pl(k, 0.12, 1.48, yf - 0.03, yf + EMBED, 2.5, 2.54, 'steelD')
    for z in (0.75, 1.45, 2.15):
        pl(k, 0.14, 0.3, yf - 0.038, yf + 0.007, z - 0.07, z + 0.07, 'graph')
    pl(k, 1.22, 1.29, yf - 0.045, yf + EMBED, 1.0, 1.55, 'chrome')
    # a louvred vent on the west wall between its windows
    k.push(0, 0, -90)
    vent(k, 0.0, 1.65, -4.96, 0.5, 0.6, 'steelD', 'graph', n=5)
    k.pop()
    # roof rail foot plates
    def plates(a, b, axis, at):
        for t in [0.04] + [0.33, 0.66] + [None]:
            v = (a + 0.04) if t == 0.04 else (b - 0.04) if t is None else a + (b - a) * t
            x, y = (v, at) if axis == 'x' else (at, v)
            zt = (H - 0.003, H + 0.012) if axis == 'x' else (H - 0.006, H + 0.016)   # never level where two runs meet
            k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, zt[0], zt[1], 'steel', ink=False)
    plates(-3.0, 4.92, 'x', -2.92)
    plates(-4.92, 4.92, 'x', 2.92)
    plates(-2.86, 2.86, 'y', -4.92)
    plates(-2.86, -1.0, 'y', 4.92)
    plates(1.0, 2.86, 'y', 4.92)


def shelter(k):
    yf = -1.5
    pl(k, -0.58, -0.5, yf - 0.03, yf + EMBED, 0.205, 2.38, 'steelD')
    pl(k, 0.5, 0.58, yf - 0.03, yf + EMBED, 0.205, 2.38, 'steelD')
    pl(k, -0.5, 0.5, yf - 0.03, yf + EMBED, 2.3, 2.38, 'steelD')
    for z in (0.55, 1.25, 1.95):
        pl(k, -0.6, -0.46, yf - 0.035, yf + 0.007, z - 0.06, z + 0.06, 'graph')
    pl(k, -0.44, 0.44, yf - 0.014, yf + 0.002, 0.24, 0.5, 'steel')                # kick plate
    junction_box(k, -2.2, 1.25, yf, 'panelG', 'steel', w=0.22, h=0.28, d=0.09)
    conduit_run(k, -2.6, -0.6, 0.6, yf, 'steelD', 'steel', r=0.022, every=0.9)
    k.push(0, 0, -90)                                                              # cable port plate on the west end
    bolt_row(k, -0.33, 0.33, 2.07, -2.95, 3, 'chrome', s=0.03)
    bolt_row(k, -0.33, 0.33, 2.33, -2.95, 3, 'chrome', s=0.03)
    k.pop()


# ------------------------------------------------------------------------------------------------ doors, stairs, art
def doorway(k, w, hinge_c='graph'):
    for turn in (0, 180):
        k.push(0, 0, turn)
        for z in (0.45, 1.5, 2.55):                                         # heavy hinges on one jamb
            pl(k, -w + 0.02, -w + 0.12, -0.56 - 0.026, -0.56 + EMBED, z - 0.07, z + 0.07, hinge_c)
        pl(k, w - 0.12, w - 0.03, -0.56 - 0.02, -0.56 + EMBED, 1.0, 1.35, 'chrome')   # strike plate
        rivet_strip(k, -w + 0.3, w - 0.3, H_ + 0.52, -0.563, 'steel', every=0.45 if w < 1.5 else 0.7, s=0.03)
        k.pop()


H_ = DOOR_H


def door2(k):
    doorway(k, 1.0)


def door4(k):
    doorway(k, 2.0)


def stair_steel(name, W, L, H):
    def fn(k):
        n = int(round((L - 1.0) / 0.25))
        y0 = -L / 2
        yl = y0 + n * 0.25
        w = W / 2 - 0.08
        for s in (-1, 1):
            xo = s * (w + 0.08)
            for t in (0.2, 0.4, 0.6, 0.8):
                y = y0 + t * (yl - y0)
                zt = t * (H - 0.1)
                zb = (y - (y0 + 0.3)) * (H - 0.4) / (yl - y0 - 0.6)
                z = 0.5 * (zt + zb)
                a, b = (xo - EMBED, xo + 0.014) if s > 0 else (xo - 0.014, xo + EMBED)
                k.bx(a, b, y - 0.03, y + 0.03, z - 0.03, z + 0.03, 'chrome', ink=False)
    return fn


def stair_c(k):
    n, L, H = 20, 6.0, TERR
    y0 = -L / 2
    yl = y0 + n * 0.25
    ang = math.degrees(math.atan2(H, yl - y0))
    for s in (-1, 1):
        xr = s * 1.875
        for t in (0.15, 0.55, 0.95):
            yy = y0 + 0.2 + t * (yl - y0 - 0.2)
            zs = 0.5 + (yy - y0) / (yl - y0) * H
            k.bxr(xr, yy, zs + 0.004, 0.16, 0.16, 0.016, 'steelD', rot=(ang, 0, 0), ink=False)


def win_frame(k, x0, x1, z0, z1, yf, c, depth=0.04, t=0.04):
    k.bx(x0 - t, x1 + t, yf - depth, yf + EMBED, z1, z1 + t, c, ink=False)
    k.bx(x0 - t, x0, yf - depth, yf + EMBED, z0, z1, c, ink=False)
    k.bx(x1, x1 + t, yf - depth, yf + EMBED, z0, z1, c, ink=False)


def a_win(k):
    win_frame(k, -0.42, 0.42, 1.1, 3.4, -0.5, 'steel')
    win_frame(k, -0.42, 0.42, 5.2, 7.6, -0.5, 'steel')


def a_winup(k):
    win_frame(k, -0.42, 0.42, 4.6, 6.6, -0.5, 'steel')


def a_door(k):
    yf = -0.5
    pl(k, -0.495, -0.462, yf - 0.026, yf + EMBED, 0.0, 2.54, 'steel')
    pl(k, 0.462, 0.495, yf - 0.026, yf + EMBED, 0.0, 2.54, 'steel')
    pl(k, -0.462, 0.462, yf - 0.026, yf + EMBED, 2.5, 2.54, 'steel')
    for z in (0.45, 1.25, 2.05):
        pl(k, -0.49, -0.38, yf - 0.034, yf + 0.007, z - 0.06, z + 0.06, 'graph')
    pl(k, -0.38, 0.38, yf - 0.024, yf + EMBED, 0.03, 0.3, 'steel')


def a_vent(k):
    for x in (-0.33, 0.33):
        for z in (6.43, 7.17):
            k.bx(x - 0.015, x + 0.015, -0.566 - 0.012, -0.566 + EMBED, z - 0.015, z + 0.015, 'chrome', ink=False)


# ------------------------------------------------------------------------------------------------ interior and exterior wall faces
def tray(k, x0, x1, z, yf, d=0.1):
    """an open cable tray: a shelf, a front lip and two cables"""
    k.bx(x0, x1, yf - d, yf + EMBED, z, z + 0.012, 'steelD', ink=False)
    k.bx(x0, x1, yf - d, yf - d + 0.01, z + 0.012, z + 0.06, 'steelD', ink=False)
    for off, c in ((0.03, 'yellow'), (0.065, 'blueS')):
        k.bx(x0 + 0.01, x1 - 0.01, yf - off - 0.012, yf - off + 0.012, z + 0.018, z + 0.042, c, ink=False)


def wall(sch, upper):
    z0 = DOOR_H + 0.6 if upper else 0.0
    yf = Y0

    def fn(k):
        X0, X1 = -0.495, 0.495
        if sch == 'L':
            if not upper:
                kick_plate(k, X0, X1, yf, 'steel', h=0.3, bolts='steelD')
                conduit_run(k, X0, X1, 3.0, yf, 'steelD', 'steel', r=0.022, every=0.9)
            else:
                conduit_run(k, X0, X1, 4.0, yf, 'steelD', 'steel', r=0.022, every=0.9)
            for z in (2.28, 3.48):
                if z > z0:
                    rivet_strip(k, X0 + 0.08, X1 - 0.08, z, yf, 'steel', every=0.2, s=0.016)
        elif sch == 'C':
            if not upper:
                kick_plate(k, X0, X1, yf, 'steel', h=0.3, bolts='steelD')
            tray(k, X0, X1, 3.1 if not upper else 4.0, yf)
            for z in (2.26, 3.46):
                if z > z0:
                    rivet_strip(k, X0 + 0.08, X1 - 0.08, z, yf, 'steel', every=0.2, s=0.016)
        elif sch == 'H':
            if not upper:
                kick_plate(k, X0, X1, yf, 'steelD', h=0.3, bolts='steel')
            pipe_run(k, X0, X1, 3.2 if not upper else 4.0, yf, 0.05, 'steel', 'steelD', every=2.0)
            for z in (2.46, 3.66):
                if z > z0:
                    rivet_strip(k, X0 + 0.08, X1 - 0.08, z, yf, 'steel', every=0.2, s=0.016)
        elif sch == 'A':
            if not upper:
                bolt_row(k, X0 + 0.1, X1 - 0.1, 0.3, yf, 3, 'steelD', s=0.03)
            for z in (1.8, 5.5):
                if z > z0:
                    rivet_strip(k, X0 + 0.08, X1 - 0.08, z, yf, 'steel', every=0.2, s=0.016)
        elif sch == 'M':
            if not upper:
                kick_plate(k, X0, X1, yf, 'steelD', h=0.3, bolts='steel')
            conduit_run(k, X0, X1, 2.2 if not upper else 4.0, yf, 'black', 'steelD', r=0.025, every=0.9)
    return fn


DETAIL = {
    'Landmark_OldDome': old_dome,
    'Dish_A': lambda k: dish(k, 'Dish_A'),
    'Dish_B': lambda k: dish(k, 'Dish_B'),
    'Landmark_Dome': great_dome,
    'Landmark_Telescope': telescope,
    'Landmark_Ring': ring,
    'GroundStation': ground_station,
    'Shelter': shelter,
    'Door2': door2,
    'Door4': door4,
    'Stair30': stair_steel('Stair30', 2.0, 6.0, TERR),
    'Stair48': stair_steel('Stair48', 2.0, 10.0, B.DECK),
    'StairC': stair_c,
    'A_Win': a_win,
    'A_WinUp': a_winup,
    'A_Door': a_door,
    'A_Vent': a_vent,
}
for _s in ('L', 'C', 'H', 'A', 'M'):
    DETAIL['F' + _s] = wall(_s, False)
    DETAIL['F' + _s + '_U'] = wall(_s, True)


class DKit(B.OKit):
    """OKit that adds a piece's registered detail just before the piece is closed"""

    def finish(self, name, bevel=0.0, ao=False):
        fn = DETAIL.get(name)
        if fn:
            fn(self)
        return super().finish(name, bevel=bevel, ao=ao)
