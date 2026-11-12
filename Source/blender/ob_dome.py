"""kit-observatory, zone 2 (inside the Great Dome): the dome shell [48, 48] (layer 10) with its slit open to the south,
the Vesper 12 m telescope on its fork mount [12, 12] (the landmark), the catwalk ring [26, 26] (layer 4.8, walkable,
open where the stairs and the bridge arrive), the dome floor's compass rings, the laboratories (spectrographs, optical
tables, lab benches, plate archive cabinets, consoles, server racks), the control room (operator desks, the video
wall), the lobby (reception, the telescope model, the meteorite, lockers, planters), the viewing rooms (binocular
viewers, sofas, low tables, the cafe bar) and the service hall (the mirror coating chamber, the mirror cart, the
scissor lift, tool cabinets). See ob_base.py for the conventions."""
import math
import random

from mathutils import Vector

from ob_base import *  # noqa: F401,F403
import ob_base as B
from ob_summit import V, basis


# ================================================================ the dome shell (origin: the springline, hall centre)
RD_IN, RD_OUT, SLIT = 23.6, 24.0, 3.0


def dome_rings(R, n_el=8, n_az=32):
    """rings of points on a sphere of radius R from the springline to where the ring is the slit's width: each ring
    runs from the slit's east edge (x = +SLIT, y < 0) round the back (+Y) to its west edge (x = -SLIT)"""
    el_top = math.acos(SLIT / R)
    rings = []
    for j in range(n_el + 1):
        el = el_top * j / n_el
        rho, z = R * math.cos(el), R * math.sin(el)
        a0 = math.atan2(-math.sqrt(max(0.0, rho * rho - SLIT * SLIT)), SLIT)   # the east edge (y < 0)
        a1 = math.atan2(-math.sqrt(max(0.0, rho * rho - SLIT * SLIT)), -SLIT) + 2 * math.pi
        pts = [(rho * math.cos(a0 + (a1 - a0) * i / n_az), rho * math.sin(a0 + (a1 - a0) * i / n_az), z) for i in range(n_az + 1)]
        rings.append(pts)
    return rings


def build_dome(k, ao):
    k.begin()
    outer, inner = dome_rings(RD_OUT), dome_rings(RD_IN)
    n = len(outer[0])
    verts, faces_o, faces_i = [], [], []
    for R in outer:
        verts.extend(R)
    base_i = len(verts)
    for R in inner:
        verts.extend(R)
    for j in range(len(outer) - 1):
        for i in range(n - 1):
            a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i
            faces_o.append((a, b, c, d))
            faces_i.append((base_i + d, base_i + c, base_i + b, base_i + a))
    # the slit jambs (x = +/-SLIT planes) and the rim of the opening at the top
    jamb = []
    last = len(outer) - 1
    for j in range(last):
        for (i, flip) in ((0, False), (n - 1, True)):
            q = (j * n + i, (j + 1) * n + i, base_i + (j + 1) * n + i, base_i + j * n + i)
            jamb.append(tuple(reversed(q)) if flip else q)
    for i in range(n - 1):
        q = (last * n + i, last * n + i + 1, base_i + last * n + i + 1, base_i + last * n + i)
        jamb.append(q)
    # outer skin: alternate white panels; inner skin dark blue
    def ocol(f):
        cen = f.calc_center_median()
        a = math.atan2(cen.y, cen.x)
        return 'domeW' if int((a + math.pi) / (2 * math.pi) * 24) % 2 else 'panelW'
    vs_o = k.mesh(verts, faces_o + jamb, lambda f: ocol(f) if f.normal.dot(f.calc_center_median()) > 0.2 else 'domeS', ink=True, recalc=False)
    k.mesh(verts, faces_i, 'domeIn', ink=False)
    # meridian ribs inside (skip the slit), two ring girders, the shutter guide rails outside along the slit
    for i in range(1, 16):
        a = -math.pi / 2 + 2 * math.pi * i / 16
        if abs(math.cos(a)) * (RD_IN - 0.2) < SLIT + 0.4 and math.sin(a) < 0:
            continue
        pts = []
        for j in range(11):
            el = (math.pi / 2 * 0.93) * j / 10
            r = RD_IN - 0.18
            p = (r * math.cos(el) * math.cos(a), r * math.cos(el) * math.sin(a), r * math.sin(el))
            if abs(p[0]) < SLIT + 0.3 and p[1] < 0.5:
                break
            pts.append(p)
        for i2, (p, q) in enumerate(zip(pts, pts[1:])):
            k.beam(p, q, 0.34 + (0.01 if i2 % 2 else 0.0), 'domeInD', ink=False)
    for elg in (math.radians(28), math.radians(56)):
        r = (RD_IN - 0.2) * math.cos(elg)
        z = (RD_IN - 0.2) * math.sin(elg)
        a0 = math.atan2(-math.sqrt(r * r - (SLIT + 0.3) ** 2), SLIT + 0.3)
        a1 = math.atan2(-math.sqrt(r * r - (SLIT + 0.3) ** 2), -(SLIT + 0.3)) + 2 * math.pi
        pts = [(r * math.cos(a0 + (a1 - a0) * t / 30), r * math.sin(a0 + (a1 - a0) * t / 30), z) for t in range(31)]
        for i2, (p, q) in enumerate(zip(pts, pts[1:])):
            k.beam(p, q, 0.28 + (0.01 if i2 % 2 else 0.0), 'domeInD', ink=False)
    for s in (-1, 1):
        pts = []
        for j in range(11):
            el = math.acos(SLIT / RD_OUT) * j / 10
            rho = (RD_OUT + 0.14) * math.cos(el)
            x = s * (SLIT + 0.25)
            if rho <= abs(x):
                break
            pts.append((x, -math.sqrt(rho * rho - x * x), (RD_OUT + 0.14) * math.sin(el)))
        for i2, (p, q) in enumerate(zip(pts, pts[1:])):
            k.beam(p, q, 0.3 + (0.01 if i2 % 2 else 0.0), 'domeS')
    # the ring beam on the wall tops and the bogie track
    k.ring_wall(0, 0, 22.9, 24.2, -0.45, 0.35, 'steelD', seg=48, top='graph')
    # the corner slabs between the square hall and the dome's circle (flat, under the wall tops)
    for qx, qy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        arc = [(qx * 24.0 * math.cos(math.pi / 2 * t / 12), qy * 24.0 * math.sin(math.pi / 2 * t / 12)) for t in range(13)]
        corner = (qx * 24.0, qy * 24.0)
        for p, q in zip(arc, arc[1:]):
            k.poly([(corner[0], corner[1], -0.02), (p[0], p[1], -0.02), (q[0], q[1], -0.02)], 'domeInD', (0, 0, -1))
            k.poly([(corner[0], corner[1], 0.4), (p[0], p[1], 0.4), (q[0], q[1], 0.4)], 'concD', (0, 0, 1))
    k.finish('Landmark_Dome', ao=ao)


# ================================================================ the telescope [12, 12]
def build_telescope(k, ao):
    k.begin()
    # the pier and the azimuth platform with its yellow edge
    k.cyl(0, 0, 0, 4.8, 4.8, 1.6, 'conc', seg=28)
    k.cyl(0, 0, 1.6, 5.0, 5.0, 0.8, 'blueD', seg=28)
    k.ring(0, 0, 2.403, 4.45, 4.85, 'yellow', seg=28)
    k.cyl(0, 0, 2.4, 4.2, 4.2, 0.5, 'steelD', seg=24)
    # the fork: two tapered arms, the elevation bearings
    Z = 9.0
    for s in (-1, 1):
        xa, xb = sorted((s * 3.0, s * 4.2))
        k.hullp([(x, y, z) for x in (xa, xb) for (y, z) in ((-2.4, 2.9), (2.4, 2.9), (1.3, Z + 0.9), (-1.3, Z + 0.9))], 'blueS')
        k.cyl(s * 4.2, 0, Z, 1.2, 1.2, 0.5, 'steelD', seg=14, rot=(0, 90 * s, 0))
        # Nasmyth platform on the arm's outside with an instrument
        xo0, xo1 = sorted((s * 4.2, s * 5.6))
        k.bx(xo0, xo1, -1.6, 1.6, 6.6, 6.8, 'graph')
        k.bx(min(xo0, xo1) + 0.2, max(xo0, xo1) - 0.2, -1.0, 1.0, 6.8, 8.4, 'domeW')
        k.fq(min(xo0, xo1) + 0.25, max(xo0, xo1) - 0.25, -1.003, 7.4, 7.7, 'blueS')
    # the tube: centre section, mirror cell, eight truss tubes, the top ring and the secondary on its spider vanes
    d, e1, e2 = basis(math.radians(-90), math.radians(50))
    A = V(0, 0, Z)

    def boxd(c, hu, hv, hw, col):   # a box in the tube frame (e1, e2, d)
        k.hullp([tuple(c + e1 * su * hu + e2 * sv * hv + d * sw * hw) for su in (-1, 1) for sv in (-1, 1) for sw in (-1, 1)], col)
    boxd(A, 2.95, 2.4, 1.3, 'domeW')
    boxd(A - d * 2.6, 2.75, 2.75, 0.95, 'blueS')
    boxd(A - d * 3.75, 2.2, 2.2, 0.25, 'graph')
    k.tube(tuple(A - d * 1.55), tuple(A - d * 1.62), 2.3, 2.3, 'mirror', seg=20, ink=False)
    top = A + d * 12.5
    for su in (-1, 1):
        for sv in (-1, 1):
            p0 = A + d * 1.3 + e1 * su * 2.3 + e2 * sv * 2.3
            for (tu, tv) in ((1, 0), (0, 1)):
                p1 = top + e1 * (su * 2.3 if tu else su * 0.9) + e2 * (sv * 2.3 if tv else sv * 0.9)
                k.beam(tuple(p0), tuple(p1), 0.16, 'chrome')
    k.tube(tuple(top - d * 0.4), tuple(top + d * 0.4), 3.3, 3.3, 'domeW', seg=20, caps=False)
    k.tube(tuple(top - d * 0.38), tuple(top + d * 0.38), 3.05, 3.05, 'graph', seg=20, caps=False, ink=False)
    for a in (0.0, math.pi / 2, math.pi, 1.5 * math.pi):
        u = e1 * math.cos(a) + e2 * math.sin(a)
        k.beam(tuple(top + u * 0.55), tuple(top + u * 3.0), 0.05, 'steel', ink=False)
    k.tube(tuple(top - d * 0.8), tuple(top + d * 0.6), 0.6, 0.6, 'graph', seg=12)
    # cable wrap and a service ladder on the pier
    k.cyl(0, 0, 2.9, 1.4, 1.4, 1.0, 'black', seg=14)
    disc_cols(k, 0, 0, 5.0, 0.0, 2.4)
    for s in (-1, 1):
        xa, xb = sorted((s * 3.0, s * 4.2))
        k.col(xa, xb, -2.4, 2.4, 2.4, Z)
    k.finish('Landmark_Telescope', ao=ao)
    k.begin()
    for s in (-1, 1):
        x = s * 5.62
        k.push(0, 0, 90 if s > 0 else -90)
        k.pop()
    k.text('VESPER 12 M', 0.0, -5.004, 1.85, 0.3, 'lightW', font='display', maxw=3.0)
    k.finish('Landmark_Telescope_Glow')


# ================================================================ the catwalk ring [26, 26] on the 4.8 m layer
R_IN, R_OUT = 11.0, 13.0


def ring_open(x, y, r):
    """the stairs land at the south and north ends (|x| < 1), the bridge at the east end (|y| < 1)"""
    return (abs(x) < 1.0 and abs(y) > r - 1.5) or (abs(y) < 1.5 and x > r - 1.5)


def build_ring(k, ao):
    k.begin()
    k.ring_wall(0, 0, R_IN, R_OUT, -0.3, 0.0, 'steelD', seg=48, top='graph')
    for i in range(48):   # the deck's underside
        a, b = 2 * math.pi * i / 48, 2 * math.pi * (i + 1) / 48
        k.poly([(math.cos(a) * R_IN, math.sin(a) * R_IN, -0.3), (math.cos(b) * R_IN, math.sin(b) * R_IN, -0.3),
                (math.cos(b) * R_OUT, math.sin(b) * R_OUT, -0.3), (math.cos(a) * R_OUT, math.sin(a) * R_OUT, -0.3)], 'steelD', (0, 0, -1))
    # grating seams (radial lines on the deck)
    for i in range(24):
        a = 2 * math.pi * (i + 0.5) / 24
        c, s = math.cos(a), math.sin(a)
        w = 0.03
        k.poly([(c * R_IN - s * w, s * R_IN + c * w, 0.003), (c * R_OUT - s * w, s * R_OUT + c * w, 0.003),
                (c * R_OUT + s * w, s * R_OUT - c * w, 0.003), (c * R_IN + s * w, s * R_IN - c * w, 0.003)], 'steel', (0, 0, 1))

    def rail(r, n, cut):
        pts = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            pts.append((math.cos(a) * r, math.sin(a) * r))
        runs, cur = [], []
        for (x, y) in pts:
            if cut and ring_open(x, y, r):
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append((x, y))
        if len(cur) > 1:
            runs.append(cur)
        if len(runs) > 1 and runs[0][0] == runs[-1][-1]:
            runs[0] = runs.pop() + runs[0][1:]
        for run in runs:
            for j, (p, q) in enumerate(zip(run, run[1:])):
                k.beam((p[0], p[1], 1.05), (q[0], q[1], 1.05), 0.06 + (0.006 if j % 2 else 0.0), 'yellow')
                k.beam((p[0], p[1], 0.55), (q[0], q[1], 0.55), 0.03 + (0.004 if j % 2 else 0.0), 'yellow', ink=False)
            closed = math.hypot(run[0][0] - run[-1][0], run[0][1] - run[-1][1]) < 1e-6
            for j, (x, y) in enumerate(run):
                if closed and j == len(run) - 1:
                    continue
                if j % 2 == 0 or j == len(run) - 1:
                    k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 1.05, 'steelD', ink=False)
        return runs
    rail(R_IN + 0.06, 40, False)
    outer_runs = rail(R_OUT - 0.06, 56, True)
    # stubs from the outer rail's ends at the bridge opening straight on to the bridge's rails (0.5 m over the bridge)
    xe = math.sqrt((R_OUT - 0.06) ** 2 - 1.5 ** 2)
    for sy in (-1.5, 1.5):
        k.beam((xe, sy, 1.05), (13.5, sy, 1.05), 0.066, 'yellow')
        k.beam((xe, sy, 0.55), (13.5, sy, 0.55), 0.034, 'yellow', ink=False)
        k.bx(13.47, 13.53, sy - 0.03, sy + 0.03, 0.0, 1.05, 'steelD', ink=False)
        k.col(xe - 0.05, 13.55, sy - 0.05, sy + 0.05, 0.0, 1.1)
    # toe boards round both edges
    k.ring_wall(0, 0, R_IN, R_IN + 0.02, 0.0, 0.12, 'yellow', seg=48, ink=False)
    # support columns down to the hall floor (16, off the openings), with knee braces
    for i in range(16):
        a = math.radians(11.25 + 22.5 * i)
        x, y = math.cos(a) * 12.0, math.sin(a) * 12.0
        k.bx(x - 0.14, x + 0.14, y - 0.14, y + 0.14, -DECK, -0.3, 'steelD', cull='bt')
        k.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, -DECK, -DECK + 0.03, 'graph', ink=False, cull='b')
        k.col(x - 0.14, x + 0.14, y - 0.14, y + 0.14, -DECK, -0.3)
    # collision: the deck (walkable), the inner rail all round, the outer rail with its openings
    band_cols(k, 0, 0, R_IN - 0.02, R_OUT + 0.02, -0.3, 0.0, step=0.5, walk=True)
    arc_rail_cols(k, 0, 0, R_IN + 0.06, 0.05, 0.0, 1.1)
    for run in outer_runs:
        a0 = math.atan2(run[0][1], run[0][0])
        a1 = math.atan2(run[-1][1], run[-1][0])
        while a1 <= a0:
            a1 += 2 * math.pi
        arc_rail_cols(k, 0, 0, R_OUT - 0.06, 0.05, 0.0, 1.1, a0, a1)
    k.finish('Landmark_Ring', ao=ao)


# ================================================================ floor finish: the dome floor's compass rings (0.012)
def build_floor(k, ao):
    k.begin()
    for (r0, r1, c) in ((23.2, 23.7, 'navy'), (14.0, 14.2, 'blueS'), (6.4, 6.6, 'yellow')):
        k.ring(0, 0, 0.0, r0, r1, c, seg=64)
    for i in range(24):
        a = 2 * math.pi * i / 24
        cs, sn, w = math.cos(a), math.sin(a), 0.04 if i % 6 else 0.1
        r0, r1 = (6.6, 23.2) if i % 6 == 0 else (14.2, 23.2)
        k.poly([(cs * r0 - sn * w, sn * r0 + cs * w, 0.003), (cs * r1 - sn * w, sn * r1 + cs * w, 0.003),
                (cs * r1 + sn * w, sn * r1 - cs * w, 0.003), (cs * r0 + sn * w, sn * r0 - cs * w, 0.003)], 'navy', (0, 0, 1))
    for (word, x, y) in (('N', 0, 21.0), ('S', 0, -21.0), ('E', 21.0, 0), ('W', -21.0, 0)):
        k.text(word, x, y, 0.0065, 1.2, 'navy', face='up', font='display', valign='m')
    k.finish('F_DomeFloor')


# ================================================================ labs, control room
def lab_props(k, ao):
    rnd = random.Random(1931)
    # spectrograph [4, 2]: a blue vacuum tank on a granite optical bench, the camera, the cable loom, a dewar
    for name, flip in (('Spectro_A', False), ('Spectro_B', True)):
        k.begin()
        k.bx(-1.95, 1.95, -0.95, 0.95, 0.0, 0.85, 'graph')
        k.bx(-1.9, 1.9, -0.9, 0.9, 0.85, 0.95, 'rockD')
        k.tube((-1.6, 0.0, 1.55), (1.2, 0.0, 1.55), 0.55, 0.55, 'blueS', seg=14)
        for x in (-1.6, 1.2):
            k.tube((x - 0.04, 0.0, 1.55), (x + 0.04, 0.0, 1.55), 0.64, 0.64, 'steelD', seg=14, ink=False)
        for x in (-1.1, 0.8):
            k.bx(x - 0.2, x + 0.2, -0.45, 0.45, 0.95, 1.08, 'steelD')
        k.tube((1.2, 0.0, 1.55), (1.75, 0.0, 1.55), 0.3, 0.25, 'graph', seg=10)
        k.cyl(1.45, 0.35, 0.95, 0.18, 0.18, 0.75, 'chrome', seg=8)
        k.cyl(1.45, 0.35, 1.7, 0.08, 0.08, 0.12, 'black', seg=6)
        k.push(0, 0, 0)
        k.bxr(-0.25, -0.56, 1.55, 1.1, 0.02, 0.3, 'yellow', rot=(0, 0, 0))
        k.text('ECHELLE 2', -0.25, -0.575, 1.48, 0.16, 'black', font='display', maxw=1.0)
        k.pop()
        for j in range(4):
            k.cyl(-1.9 + j * 0.06, 0.6, 0.95, 0.03, 0.03, 0.45, 'black', seg=4, ink=False)
        k.col(-1.95, 1.95, -0.95, 0.95, 0.0, 2.1)
        k.finish(name, ao=ao)
    # optical table [3, 2]: a honeycomb breadboard with mounts, mirrors and a laser
    k.begin()
    for (x, y) in ((-1.2, -0.7), (1.2, -0.7), (-1.2, 0.7), (1.2, 0.7)):
        k.cyl(x, y, 0.0, 0.16, 0.16, 0.7, 'steelD', seg=8)
    k.bx(-1.45, 1.45, -0.95, 0.95, 0.7, 0.9, 'graph')
    k.uq(-1.4, 1.4, -0.9, 0.9, 0.904, 'steelD')
    for i in range(7):
        x, y = rnd.uniform(-1.2, 1.2), rnd.uniform(-0.7, 0.7)
        k.cyl(x, y, 0.904, 0.03, 0.03, 0.22, 'chrome', seg=5, ink=False)
        k.bx(x - 0.07, x + 0.07, y - 0.015, y + 0.015, 1.06, 1.2, 'mirror')
    k.bx(-1.3, -0.5, 0.45, 0.65, 0.904, 1.05, 'paper')
    k.bx(-0.5, -0.44, 0.52, 0.58, 0.97, 1.0, 'redL', ink=False)
    k.col(-1.45, 1.45, -0.95, 0.95, 0.0, 1.0)
    k.finish('OpticTable', ao=ao)
    k.begin()
    k.bx(-0.44, -0.4, 0.535, 0.565, 0.975, 0.995, 'redL', ink=False)
    k.finish('OpticTable_Glow')
    # lab bench [3, 1] (back to the wall): drawers, a shelf, an oscilloscope, a soldering station, parts bins
    k.begin()
    k.bx(-1.45, 1.45, -0.4, 0.45, 0.0, 0.88, 'panelG')
    k.bx(-1.5, 1.5, -0.45, 0.45, 0.88, 0.94, 'black')
    for x0 in (-1.35, -0.45, 0.45):
        k.fq(x0, x0 + 0.85, -0.403, 0.1, 0.8, 'panelW')
        k.fq(x0 + 0.3, x0 + 0.55, -0.406, 0.7, 0.74, 'steelD')
    k.bx(-1.41, 1.41, 0.15, 0.45, 1.6, 1.64, 'steel')
    for x in (-1.45, 1.41):
        k.bx(x, x + 0.04, 0.15, 0.45, 0.94, 1.64, 'steel', ink=False)
    k.bx(-1.1, -0.5, -0.2, 0.25, 0.94, 1.3, 'graph')
    k.fq(-1.05, -0.75, -0.203, 1.0, 1.25, 'screen')
    k.bx(0.2, 0.55, -0.25, 0.1, 0.94, 1.04, 'blueS')
    for i in range(5):
        k.bx(-1.3 + i * 0.5, -0.9 + i * 0.5, 0.2, 0.42, 1.64, 1.8, ('redL', 'blueS', 'yellow', 'scrG', 'orange')[i])
    k.col(-1.5, 1.5, -0.45, 0.45, 0.0, 0.94)
    k.finish('LabBench', ao=ao)
    k.begin()
    k.fq(-1.03, -0.77, -0.206, 1.02, 1.23, 'scrG')
    k.finish('LabBench_Glow')
    # plate archive cabinet [2, 1] (back to the wall): flat drawers of glass photographic plates
    k.begin()
    k.bx(-0.95, 0.95, -0.35, 0.45, 0.0, 1.9, 'blueD')
    for j in range(8):
        z = 0.1 + j * 0.22
        for x0 in (-0.9, 0.02):
            k.fq(x0, x0 + 0.88, -0.353, z, z + 0.18, 'panelG')
            k.fq(x0 + 0.34, x0 + 0.54, -0.356, z + 0.12, z + 0.15, 'chrome')
            k.fq(x0 + 0.06, x0 + 0.26, -0.356, z + 0.04, z + 0.1, 'paper')
    k.col(-0.95, 0.95, -0.35, 0.45, 0.0, 1.9)
    k.finish('PlateCab', ao=ao)
    # server rack [2, 1] (back to the wall): two racks with blinking LEDs
    k.begin()
    for x in (-0.48, 0.48):
        k.bx(x - 0.44, x + 0.44, -0.45, 0.45, 0.0, 2.1, 'black')
        k.fq(x - 0.38, x + 0.38, -0.453, 0.1, 2.0, 'graph')
        for j in range(10):
            k.fq(x - 0.34, x + 0.34, -0.456, 0.2 + j * 0.18, 0.32 + j * 0.18, 'steelD')
    k.col(-0.95, 0.95, -0.45, 0.45, 0.0, 2.1)
    k.finish('Rack', ao=ao)
    k.begin()
    for x in (-0.48, 0.48):
        for j in range(10):
            k.fq(x + 0.18, x + 0.24, -0.459, 0.24 + j * 0.18, 0.28 + j * 0.18, 'scrG' if (j + int(x > 0)) % 3 else 'amberL')
    k.finish('Rack_Glow')
    # console desk [2, 1]: a desk with three screens and a keyboard (front: the operator side, Blender -Y)
    def desk(k, w):
        k.bx(-w / 2, w / 2, -0.45, 0.4, 0.72, 0.78, 'graph')
        k.bx(-w / 2 + 0.08, w / 2 - 0.08, 0.25, 0.38, 0.0, 0.715, 'steelD')
        for s in (-1, 1):
            k.bx(s * (w / 2 - 0.05) - 0.03, s * (w / 2 - 0.05) + 0.03, -0.4, 0.4, 0.0, 0.72, 'steelD', ink=False)
        n = 3 if w < 2.5 else 4
        for i in range(n):
            x = -w / 2 + (i + 0.5) * w / n
            k.bx(x - 0.03, x + 0.03, 0.15, 0.2, 0.78, 0.98, 'black', ink=False)
            k.bx(x - 0.3, x + 0.3, 0.1, 0.16, 0.95, 1.36, 'black')
            k.fq(x - 0.27, x + 0.27, 0.097, 0.98, 1.33, 'screen')
        k.bx(-0.3, 0.3, -0.3, -0.12, 0.78, 0.8, 'black', ink=False)
        k.col(-w / 2, w / 2, -0.45, 0.4, 0.0, 0.8)
        k.col(-w / 2 + 0.05, w / 2 - 0.05, 0.1, 0.2, 0.8, 1.36)
    k.begin(); desk(k, 1.9); k.chair(0.0, -0.75, 0, c='fabricD'); k.finish('Console', ao=ao)
    k.begin()
    for i in range(3):
        x = -0.95 + (i + 0.5) * 1.9 / 3
        k.fq(x - 0.24, x + 0.24, 0.094, 1.0, 1.31, ('scrB', 'scrG', 'scrB')[i])
    k.finish('Console_Glow')
    k.begin(); desk(k, 2.9); k.finish('OpsDesk', ao=ao)
    k.begin()
    for i in range(4):
        x = -1.45 + (i + 0.5) * 2.9 / 4
        k.fq(x - 0.24, x + 0.24, 0.094, 1.0, 1.31, ('scrB', 'amberL', 'scrG', 'scrB')[i])
    k.finish('OpsDesk_Glow')
    # video wall [6, 1] (back to the wall): 3 x 2 screens in a black frame
    k.begin()
    k.bx(-2.95, 2.95, 0.2, 0.45, 0.9, 3.6, 'black')
    for i in range(3):
        for j in range(2):
            x0 = -2.85 + i * 1.92
            k.fq(x0, x0 + 1.86, 0.197, 1.0 + j * 1.3, 2.25 + j * 1.3, 'screen')
    k.col(-2.95, 2.95, 0.2, 0.45, 0.0, 3.6)
    k.finish('VideoWall', ao=ao)
    k.begin()
    rs = random.Random(12)
    for i in range(3):
        for j in range(2):
            x0 = -2.85 + i * 1.92
            k.fq(x0 + 0.05, x0 + 1.81, 0.194, 1.05 + j * 1.3, 2.2 + j * 1.3, 'chart' if (i + j) % 2 else 'navy')
    for t in range(40):
        x, z = rs.uniform(-2.7, 2.7), rs.uniform(1.1, 3.4)
        k.fq(x - 0.02, x + 0.02, 0.19, z - 0.02, z + 0.02, 'starW')
    k.fq(-0.8, 0.8, 0.19, 2.35, 2.42, 'scrG')
    k.finish('VideoWall_Glow')
    # chair (one cell, turned at random)
    k.begin(); k.chair(0, 0, 0, c='fabricD'); k.col(-0.25, 0.25, -0.25, 0.25, 0.0, 0.5); k.finish('Chair', ao=ao)
    # meeting / plate-viewing table [3, 2] with a light table, plates and a loupe
    k.begin()
    k.bx(-1.45, 1.45, -0.9, 0.9, 0.72, 0.78, 'woodL')
    for (x, y) in ((-1.3, -0.75), (1.3, -0.75), (-1.3, 0.75), (1.3, 0.75)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.72, 'steelD', cull='b')
    k.bx(-0.6, 0.6, -0.4, 0.4, 0.78, 0.84, 'graph')
    k.uq(-0.55, 0.55, -0.35, 0.35, 0.843, 'lightW')
    for (x, y) in ((-1.1, 0.3), (0.9, -0.5), (1.0, 0.4)):
        k.bx(x - 0.2, x + 0.2, y - 0.15, y + 0.15, 0.78, 0.8, 'glassL', ink=False)
    for (x, y, deg) in ((0.0, -1.25, 0), (0.0, 1.25, 180), (-1.0, -1.25, 0), (1.0, 1.25, 180)):
        k.chair(x, y, deg, c='fabric')
    k.col(-1.45, 1.45, -0.9, 0.9, 0.0, 0.84)
    k.finish('PlateTable', ao=ao)
    k.begin(); k.uq(-0.5, 0.5, -0.3, 0.3, 0.847, 'lightW'); k.finish('PlateTable_Glow')
    # instrument crate [2, 2]
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 1.3, 'woodL')
    for z in (0.08, 1.15):
        k.bx(-0.92, 0.92, -0.92, 0.92, z, z + 0.08, 'wood', ink=False)
    for s in (0, 90, 180, 270):
        k.push(0, 0, s)
        k.fq(-0.6, 0.6, -0.923, 0.45, 0.85, 'paper')
        k.text('FRAGILE  OPTICS', 0.0, -0.926, 0.6, 0.12, 'redL', font='display', maxw=1.1)
        k.poly([(-0.1, -0.929, 0.74), (0.1, -0.929, 0.74), (0.0, -0.929, 0.83)], 'black', (0, -1, 0))
        k.pop()
    k.col(-0.92, 0.92, -0.92, 0.92, 0.0, 1.3)
    k.finish('Crate2', ao=ao)


# ================================================================ lobby, viewing rooms
def lobby_props(k, ao):
    # reception desk [4, 2] (front toward the visitors, Blender -Y): a curved timber front, a glass top, screens
    k.begin()
    k.bx(-1.9, 1.9, -0.4, 0.2, 0.0, 1.1, 'wood')
    k.fq(-1.85, 1.85, -0.403, 0.1, 0.12, 'woodD')
    k.bx(-1.95, 1.95, -0.5, 0.25, 1.1, 1.15, 'woodL')
    k.bx(-1.9, 1.9, 0.2, 0.9, 0.72, 0.76, 'woodL')
    k.bx(-1.85, -1.75, 0.2, 0.9, 0.0, 0.72, 'woodD', ink=False)
    k.bx(1.75, 1.85, 0.2, 0.9, 0.0, 0.72, 'woodD', ink=False)
    for x in (-1.0, 0.8):
        k.bx(x - 0.3, x + 0.3, 0.55, 0.6, 0.85, 1.25, 'black')
        k.bx(x - 0.03, x + 0.03, 0.57, 0.62, 0.76, 0.85, 'black', ink=False)
    k.fq(-1.2, 1.2, -0.403, 0.5, 0.8, 'blueD')
    k.text('WELCOME', 0.0, -0.406, 0.57, 0.18, 'paper', font='display', maxw=2.0)
    k.chair(-0.1, 1.35, 180, c='fabricD')
    k.col(-1.95, 1.95, -0.5, 0.25, 0.0, 1.15)
    k.col(-1.9, 1.9, 0.25, 0.9, 0.0, 0.76)
    k.finish('Reception', ao=ao)
    k.begin()
    for x in (-1.0, 0.8):
        k.fq(x - 0.27, x + 0.27, 0.547, 0.88, 1.22, 'scrB')
    k.finish('Reception_Glow')
    # the telescope model in a glass case [2, 2]
    k.begin()
    k.bx(-0.85, 0.85, -0.85, 0.85, 0.0, 0.9, 'woodD')
    k.bx(-0.8, 0.8, -0.8, 0.8, 0.9, 0.94, 'graph')
    k.cyl(0, 0, 0.94, 0.42, 0.42, 0.12, 'conc', seg=14)
    for s in (-1, 1):
        k.bx(s * 0.3 - 0.05, s * 0.3 + 0.05, -0.15, 0.15, 1.06, 1.55, 'blueS')
    d, e1, e2 = basis(math.radians(-90), math.radians(50))
    A = V(0, 0, 1.5)
    k.tube(tuple(A - d * 0.25), tuple(A + d * 0.9), 0.22, 0.24, 'paper', seg=10)
    k.fq(-0.6, 0.6, -0.853, 0.55, 0.75, 'brass')
    k.text('VESPER 12 M  1 : 40', 0.0, -0.856, 0.6, 0.1, 'black', font='display', maxw=1.0)
    for y in (-0.8, 0.8):   # the case's top frame between its corner posts
        k.bx(-0.77, 0.77, y - 0.02, y + 0.02, 2.18, 2.22, 'steel', ink=False)
    for (x, y) in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.94, 2.23, 'steel', ink=False)
    k.col(-0.85, 0.85, -0.85, 0.85, 0.0, 2.22)
    k.finish('ScopeModel', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.qy(-0.76, 0.76, 0.95, 2.17, s * 0.78, s, 'glassL')
        k.qx(-0.76, 0.76, 0.95, 2.17, s * 0.78, s, 'glassL')
    k.finish('ScopeModel_Glow')
    # the meteorite on its plinth [2, 2]
    k.begin()
    k.cyl(0, 0, 0, 0.85, 0.85, 0.8, 'stoneL', seg=16)
    k.cyl(0, 0, 0.8, 0.88, 0.88, 0.06, 'woodD', seg=16)
    from kit_base import rock_pts
    k.hullp(rock_pts(random.Random(9), (0, 0), 0.55, 0.45, 0.7, z0=0.86, n=8, top=3), lambda f: 'black' if f.normal.z < 0.5 else 'rockD')
    disc_cols(k, 0, 0, 0.85, 0.0, 1.5)
    k.finish('Meteorite', ao=ao)
    # lockers [2, 1] (back to the wall)
    k.begin()
    k.bx(-0.95, 0.95, -0.25, 0.45, 0.0, 2.0, 'steelD')
    for i in range(4):
        x0 = -0.92 + i * 0.465
        k.fq(x0, x0 + 0.44, -0.253, 0.08, 1.95, ('blueS', 'blueD', 'blueS', 'blueD')[i])
        for z in (1.7, 1.75, 1.8):
            k.fq(x0 + 0.1, x0 + 0.34, -0.256, z, z + 0.02, 'navy')
        k.fq(x0 + 0.36, x0 + 0.4, -0.256, 1.0, 1.12, 'chrome')
    k.col(-0.95, 0.95, -0.25, 0.45, 0.0, 2.0)
    k.finish('Lockers', ao=ao)
    # planter (a lobby plant)
    k.begin()
    k.cyl(0, 0, 0, 0.32, 0.36, 0.55, 'pot', seg=10)
    k.cyl(0, 0, 0.5, 0.3, 0.3, 0.04, 'woodD', seg=10, ink=False)
    rr = random.Random(5)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        k.sph(math.cos(a) * 0.18, math.sin(a) * 0.18, 0.9 + rr.uniform(0, 0.4), 0.28, 'leaf', seg=(6, 4), scale=(1, 1, 0.8))
    k.col(-0.3, 0.3, -0.3, 0.3, 0.0, 1.3)
    k.finish('Plant', ao=ao)
    # binocular viewer (front: the eyepieces, Blender -Y; it looks toward +Y)
    k.begin()
    k.cyl(0, 0, 0, 0.25, 0.22, 0.08, 'graph', seg=10)
    k.cyl(0, 0, 0.08, 0.07, 0.07, 1.05, 'steelD', seg=8)
    k.bx(-0.32, 0.32, -0.18, 0.22, 1.1, 1.36, 'blueS')
    for s in (-1, 1):
        k.tube((s * 0.16, 0.2, 1.24), (s * 0.16, 0.5, 1.28), 0.1, 0.12, 'blueS', seg=8)
        k.tube((s * 0.11, -0.18, 1.26), (s * 0.11, -0.28, 1.26), 0.04, 0.04, 'black', seg=6)
    k.text('VIEW', 0.0, -0.183, 1.18, 0.07, 'paper', font='display', maxw=0.4)
    k.col(-0.22, 0.22, -0.22, 0.22, 0.0, 1.1)
    k.finish('Viewer', ao=ao)
    # lobby bench [2, 1]: timber slats on steel legs
    k.begin()
    for x in (-0.75, 0.75):
        k.bx(x - 0.04, x + 0.04, -0.2, 0.2, 0.0, 0.42, 'graph', cull='b')
    for j in range(4):
        y = -0.22 + j * 0.115
        k.bx(-0.95, 0.95, y, y + 0.1, 0.42, 0.47, 'woodL' if j % 2 else 'wood')
    k.col(-0.95, 0.95, -0.22, 0.24, 0.0, 0.47)
    k.finish('BenchIn', ao=ao)
    # sofa [3, 1] (front -Y)
    k.begin()
    k.bx(-1.45, 1.45, -0.42, 0.42, 0.08, 0.42, 'fabric')
    k.bx(-1.29, 1.29, 0.18, 0.45, 0.42, 0.85, 'fabric', cull='b')
    for s in (-1, 1):
        a2, b2 = sorted((s * 1.29, s * 1.45))
        k.bx(a2, b2, -0.42, 0.45, 0.42, 0.65, 'fabricD', cull='b')
    for (a2, b2) in ((-1.27, -0.02), (0.02, 1.27)):
        k.bx(a2, b2, -0.4, 0.16, 0.42, 0.52, 'fabric', cull='b')
    k.bx(-1.4, 1.4, -0.38, 0.38, 0.0, 0.08, 'black', cull='b')
    k.col(-1.45, 1.45, -0.42, 0.45, 0.0, 0.62)
    k.finish('Sofa', ao=ao)
    # low table [2, 1]
    k.begin()
    k.bx(-0.85, 0.85, -0.35, 0.35, 0.36, 0.42, 'woodL')
    for (x, y) in ((-0.75, -0.25), (0.75, -0.25), (-0.75, 0.25), (0.75, 0.25)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.36, 'black', cull='b')
    k.cyl(-0.3, 0.05, 0.42, 0.05, 0.05, 0.1, 'paper', seg=8)
    k.bx(0.1, 0.5, -0.15, 0.15, 0.42, 0.44, 'navy', ink=False)
    k.col(-0.85, 0.85, -0.35, 0.35, 0.0, 0.44)
    k.finish('LowTable', ao=ao)
    # the cafe bar [4, 1] (back to the wall): counter, coffee machine, cups, a menu board above
    k.begin()
    k.bx(-1.95, 1.95, -0.45, 0.2, 0.0, 1.05, 'woodD')
    k.fq(-1.9, 1.9, -0.453, 0.1, 0.95, 'wood')
    k.bx(-2.0, 2.0, -0.5, 0.2, 1.05, 1.1, 'black')
    k.bx(-1.95, 1.95, 0.2, 0.45, 0.0, 0.9, 'graph')
    k.bx(-1.4, -0.6, 0.0, 0.4, 1.1, 1.65, 'chrome')
    k.fq(-1.3, -0.7, -0.003, 1.3, 1.5, 'black')
    for x in (0.0, 0.25, 0.5, 0.75):
        k.cyl(x, -0.2, 1.1, 0.05, 0.045, 0.1, 'paper', seg=6)
    k.bx(-1.8, 1.8, 0.4, 0.45, 2.0, 2.8, 'black')
    k.text('COMET CAFE', 0.0, 0.397, 2.45, 0.24, 'amberL', font='display', maxw=2.6)
    k.col(-2.0, 2.0, -0.5, 0.45, 0.0, 1.1)
    k.finish('CafeBar', ao=ao)


# ================================================================ service hall
def service_props(k, ao):
    # the mirror coating chamber [6, 4]: a horizontal vacuum tank with its door end, pumps and a control cabinet
    k.begin()
    for x in (-1.8, 1.8):
        k.bx(x - 0.3, x + 0.3, -1.5, 1.5, 0.0, 0.7, 'yellow')
    k.tube((-2.6, 0.0, 2.0), (2.4, 0.0, 2.0), 1.75, 1.75, 'chrome', seg=20)
    for x in (-1.6, 0.0, 1.6):
        k.tube((x - 0.06, 0.0, 2.0), (x + 0.06, 0.0, 2.0), 1.85, 1.85, 'steelD', seg=20, ink=False)
    k.tube((2.4, 0.0, 2.0), (2.75, 0.0, 2.0), 1.85, 1.6, 'steel', seg=20)
    k.tube((2.75, 0.0, 2.0), (2.85, 0.0, 2.0), 0.5, 0.5, 'graph', seg=10)
    k.bx(-2.95, -2.3, -1.0, 1.0, 0.0, 2.6, 'panelG')
    k.bx(-1.0, -0.2, -1.95, -1.4, 0.0, 1.1, 'blueS')
    k.tube((-0.6, -1.7, 1.1), (-0.6, -1.7, 1.4), 0.15, 0.15, 'steel', seg=8)
    k.beam((-0.6, -1.7, 1.4), (-0.6, -1.2, 2.2), 0.14, 'steel')
    k.push(0, 0, 0)
    k.bxr(0.4, -1.78, 3.25, 2.4, 0.03, 0.34, 'blueD', rot=(-20, 0, 0))
    k.pop()
    k.col(-2.95, 2.85, -1.75, 1.75, 0.0, 3.75)
    k.col(-1.0, -0.2, -1.95, -1.75, 0.0, 1.1)
    k.finish('Coater', ao=ao)
    # the mirror cart [4, 4]: a segment of the primary (a hexagon) on a cradle trolley under its dust cover frame
    k.begin()
    k.bx(-1.9, 1.9, -1.9, 1.9, 0.25, 0.45, 'yellow')
    for (x, y) in ((-1.6, -1.6), (1.6, -1.6), (-1.6, 1.6), (1.6, 1.6)):
        k.cyl(x, y, 0.0, 0.22, 0.22, 0.25, 'black', seg=8)
    hexa = [(math.cos(a) * 1.5, 0.0, 1.9 + math.sin(a) * 1.5) for a in [math.pi / 6 + i * math.pi / 3 for i in range(6)]]
    front = [(x, -0.1, z) for (x, _, z) in hexa]
    back = [(x, 0.1, z) for (x, _, z) in hexa]
    k.hullp(front + back, lambda f: 'mirror' if f.normal.y < -0.9 else 'steelD')
    for s in (-1, 1):
        k.bx(s * 1.3 - 0.1, s * 1.3 + 0.1, -0.3, 0.3, 0.45, 1.6, 'steelD')
    k.bx(-0.5, 0.5, -0.4, 0.4, 0.45, 0.62, 'steelD')
    k.text('SEGMENT M1-47', 0.0, -1.903, 0.29, 0.12, 'black', font='display', maxw=2.4)
    k.col(-1.9, 1.9, -1.9, 1.9, 0.0, 0.45)
    k.col(-1.5, 1.5, -0.3, 0.3, 0.45, 3.4)
    k.finish('MirrorCart', ao=ao)
    # scissor lift [2, 3]
    k.begin()
    k.bx(-0.75, 0.75, -1.3, 1.3, 0.15, 0.55, 'orange')
    for (x, y) in ((-0.6, -1.1), (0.6, -1.1), (-0.6, 1.1), (0.6, 1.1)):
        k.cyl(x - 0.08, y, 0.15, 0.15, 0.15, 0.16, 'black', seg=8, rot=(0, 90, 0))
    for s in (-1, 1):
        x = s * 0.6
        for j in range(3):
            z0, z1 = 0.55 + j * 0.6, 1.15 + j * 0.6
            k.beam((x - 0.05, -1.1, z0), (x - 0.05, 1.1, z1), 0.08, 'graph')
            k.beam((x + 0.05, 1.1, z0), (x + 0.05, -1.1, z1), 0.08, 'graph')
    k.bx(-0.75, 0.75, -1.3, 1.3, 2.35, 2.5, 'orange')
    for (y0, y1) in ((-1.3, -1.25), (1.25, 1.3)):
        k.bx(-0.7, 0.7, y0, y1, 3.4, 3.46, 'yellow')
    for s in (-1, 1):
        a2, b2 = sorted((s * 0.7, s * 0.75))
        k.bx(a2, b2, -1.3, 1.3, 3.4, 3.46, 'yellow')
    for (x, y) in ((-0.72, -1.27), (0.72, -1.27), (-0.72, 1.27), (0.72, 1.27)):
        k.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 2.5, 3.395, 'yellow', ink=False)
    k.col(-0.75, 0.75, -1.3, 1.3, 0.0, 0.55)
    k.col(-0.65, 0.65, -1.15, 1.15, 0.55, 2.5)
    k.finish('Lift', ao=ao)
    # tool cabinet (one cell, rotate edge)
    k.begin()
    k.bx(-0.4, 0.4, -0.3, 0.3, 0.0, 1.0, 'redL')
    for j in range(5):
        k.fq(-0.36, 0.36, -0.303, 0.08 + j * 0.18, 0.22 + j * 0.18, 'red')
        k.fq(-0.1, 0.1, -0.306, 0.18 + j * 0.18, 0.2 + j * 0.18, 'chrome')
    k.bx(-0.42, 0.42, -0.32, 0.32, 1.0, 1.04, 'black')
    k.bx(-0.2, 0.15, -0.1, 0.15, 1.04, 1.12, 'yellow')
    k.col(-0.42, 0.42, -0.32, 0.32, 0.0, 1.04)
    k.finish('ToolCab', ao=ao)


def build_dome_kit(k, ao):
    build_dome(k, ao)
    build_telescope(k, ao)
    build_ring(k, ao)
    build_floor(k, ao)
    lab_props(k, ao)
    lobby_props(k, ao)
    service_props(k, ao)
