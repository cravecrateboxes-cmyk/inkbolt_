"""INKBOLT kit-venetian walls, part 2: the mansion's courtyard fronts (zone 2), its canal wing (courtyard front + the
canal face), the garden wall, the quay balustrade over the canal (zone 1 north), the gate portal and the facades over
the gates, the bridge balustrades and the exit lane's walls (trail), the hatch. Conventions: ven_base.py."""
import math
import random

from ven_base import *  # noqa: F401,F403
from ven_base import (kit, done, arch_curve, arched_opening, rect_opening, glints, flowers, wall_lantern, balustrade_x,
                      text, wall_parts)
from ven_facade import Y, house, corner_block, balcony, window, door, bands, spec, seed
from kit_base import shutter_hull
import ven_detail as D


# ================================================================ the mansion's canal face (zone 2 south wall, back)
def flat_window(k, x0, x1, z0, z1, arch=None):
    """a window drawn flat on the facade plane (seen across the canal): a stone frame, the glass, a mullion, a sill;
    arch: 'ogee' for a Gothic light (the glass and frame follow the arch)"""
    if arch:
        cur = arch_curve(x0, x1, z1, 'ogee', 3, rise=0.4)
        fr = [(x0 - 0.07, z0 - 0.02), (x1 + 0.07, z0 - 0.02)] + [((px - (x0 + x1) / 2) * 1.25 + (x0 + x1) / 2, pz + 0.1) for (px, pz) in reversed(cur)]
        k.poly([(px, Y - 0.004, pz) for (px, pz) in fr], 'stone', (0, -1, 0))
        k.poly([(px, Y - 0.008, pz) for (px, pz) in [(x0, z0), (x1, z0)] + list(reversed(cur))[1:-1]], 'glass', (0, -1, 0))
    else:
        k.qy(x0 - 0.06, x1 + 0.06, z0 - 0.04, z1 + 0.08, Y - 0.004, -1, 'stone')
        k.qy(x0, x1, z0, z1, Y - 0.008, -1, 'glass')
    k.qy((x0 + x1) / 2 - 0.02, (x0 + x1) / 2 + 0.02, z0, z1, Y - 0.012, -1, 'stone')
    glints(k, x0, x1, z0, z1, Y - 0.016)


def canal_face(k, rnd, kind):
    """the canal side of a canal-wing module, built facing -Y (the caller turns it to +Y), drawn lean (it is only
    seen across the canal): the stone base from below the water line, flat windows, Gothic lights over a long
    balcony, the water door; kinds: Win Pier Goth GothL GothR Water Quoin"""
    H = HP
    top = H - 0.4
    holes = []
    if kind == 'Water':
        holes.append((-0.45, 0.45, 0.5, 2.4 + 0.45))
    for (a, b, c0, c1) in wall_parts(-0.5, 0.5, 0.5, top, holes):
        k.qy(a, b, c0, c1, Y, -1, 'stucco')
    if kind == 'Water':
        arched_opening(k, -0.45, 0.45, 0.5, 2.4, 'round', 0.3, 'boat', frame='stone', fw=0.1, sill=False)
        k.cyl(0, Y - 0.6, WATER - 0.3, 0.09, 0.09, 4.0, 'shut', seg=6)
    elif kind not in ('Quoin', 'Pier'):
        flat_window(k, -0.2, 0.2, 1.8, 2.6)
    if kind in ('Goth', 'GothL', 'GothR'):
        flat_window(k, -0.29, 0.29, 4.75, 6.55, arch='ogee')
        k.bxc(-0.5, 0.5, Y - 0.6, Y, 4.45, 4.6, 'stone', cull='k' + ('' if kind == 'GothL' else 'l') + ('' if kind == 'GothR' else 'r'))
        k.bxc(-0.5 + (0.06 if kind == 'GothL' else 0.0), 0.5 - (0.06 if kind == 'GothR' else 0.0), Y - 0.6, Y - 0.48, 4.6, 5.45, 'stone', cull='bk' + ('' if kind == 'GothL' else 'l') + ('' if kind == 'GothR' else 'r'))
        for xx in (-0.25, 0.25):
            k.qy(xx - 0.08, xx + 0.08, 4.72, 5.3, Y - 0.604, -1, 'stoneD')
    elif kind in ('Win', 'Water'):
        flat_window(k, -0.24, 0.24, 5.0, 7.3)
    if kind not in ('Pier', 'Quoin'):
        flat_window(k, -0.22, 0.22, 9.0, 10.85)
    if kind == 'Pier':
        wall_lantern(k, 0.0, Y - 0.03, 2.4, arm=0.32)
    if kind == 'Quoin':
        z, i = 0.5, 0
        while z < top - 0.05:
            h = min(0.6, top - z)
            w = 0.36 if i % 2 else 0.26
            k.qy(-w, w, z + 0.01, z + h - 0.01, Y - 0.006, -1, 'stone')
            z += h
            i += 1
    # the stone base from below the water line, a green tide line, the courses, the cornice
    k.qy(-0.5, 0.5, WATER - 0.4, 0.5, Y - 0.03, -1, 'stone')
    k.qy(-0.5, 0.5, WATER - 0.02, WATER + 0.22, Y - 0.034, -1, 'leafD')
    k.qy(-0.5, 0.5, 0.0, 0.03, Y - 0.034, -1, 'stoneD')
    k.qy(-0.5, 0.5, PGF - 0.08, PGF + 0.06, Y - 0.01, -1, 'stone')
    k.bxc(-0.5, 0.5, Y - 0.28, Y, H - 0.3, H, 'stone', cull='klr')


def canal_module(k, rnd, front, back, inner=None):
    """a module of the mansion's canal wing (zone 2 south wall): the courtyard front and the canal face behind it
    (turned to +Y), a ridged roof between them"""
    house(k, rnd, HP, front, inner=inner, roof=False)
    k.push(0, 0, 180)
    canal_face(k, rnd, back)
    k.pop()
    k.poly([(-0.5, Y - 0.3, HP + 0.04), (0.5, Y - 0.3, HP + 0.04), (0.5, 0.0, HP + 0.65), (-0.5, 0.0, HP + 0.65)], 'roof', (0, -0.7, 0.7))
    k.poly([(-0.5, 0.0, HP + 0.65), (0.5, 0.0, HP + 0.65), (0.5, 0.8, HP + 0.04), (-0.5, 0.8, HP + 0.04)], 'roof', (0, 0.7, 0.7))


# ================================================================ the garden wall (zone 2 west)
GW_H = 3.2


def garden_wall(k, rnd, kind):
    """a brick garden wall with a stone coping; kinds: A (a plaster patch), V (vines and a climbing rose), N (a niche
    with an urn), L (an espaliered lemon), D (a little wooden door)"""
    top = GW_H
    holes = []
    if kind == 'N':
        holes.append((-0.3, 0.3, 1.0, 1.95 + 0.3))
    if kind == 'D':
        holes.append((-0.4, 0.4, 0.0, 2.2 + 0.4))
    for (a, b, c0, c1) in wall_parts(-0.5, 0.5, 0.0, top - 0.12, holes):
        k.qy(a, b, c0, c1, Y, -1, 'brick')
    for i in range(1, 9):
        z = i * 0.34
        if kind == 'N' and 0.9 < z < 2.35:
            continue
        if kind == 'D' and z < 2.7:
            continue
        k.qy(-0.5, 0.5, z, z + 0.018, Y - 0.003, -1, 'terraD')
    if kind == 'A':
        k.qy(-0.32, 0.18, 1.4, 2.0, Y - 0.006, -1, 'plaster')
    k.bxc(-0.5, 0.5, Y - 0.06, Y + 0.06, top - 0.12, top, 'stone', cull='lr')
    D.wall_coping_joint(k, top)
    k.qy(-0.5, 0.5, 0.0, 0.25, Y - 0.012, -1, 'stoneD')
    if kind == 'N':
        arched_opening(k, -0.3, 0.3, 1.0, 1.95, 'round', 0.25, 'brick', frame='stone', fw=0.06, reveal='terraD')
        k.lathe(0, Y + 0.13, 1.0, [(0.08, 0.0), (0.12, 0.06), (0.17, 0.25), (0.13, 0.42), (0.16, 0.45), (0.0, 0.46)], 'stone', seg=6)
        flowers(k, rnd, -0.12, 0.12, Y + 0.07, Y + 0.19, 1.46, 4, ('fPurp', 'white', 'fPurp'))
    if kind == 'D':
        door(k, -0.4, 0.4, 2.2)
    if kind in ('V', 'L'):
        cols = ('fPink', 'white', 'fPink') if kind == 'V' else ('lemon', 'lemon', 'lemon')
        for i in range(7):
            ax = -0.4 + 0.8 * rnd.random()
            az = 0.35 + (top - 0.7) * (i / 6.0)
            r = 0.16 + 0.1 * rnd.random()
            yb = Y - 0.01 - i * 0.004
            k.hullp([(ax - r, yb, az - r), (ax + r, yb, az - r * 0.6), (ax + r * 0.8, yb, az + r), (ax - r * 0.7, yb, az + r * 0.9),
                     (ax, Y - 0.1 - i * 0.004, az)], 'leaf' if i % 2 else 'leafD', ink=False)
            if i % 2 == 0:
                k.hullp([(ax - 0.05, Y - 0.12 - i * 0.004, az - 0.04), (ax + 0.05, Y - 0.12 - i * 0.004, az - 0.03), (ax, Y - 0.15 - i * 0.004, az + 0.05), (ax + 0.01, Y - 0.09 - i * 0.004, az + 0.02)], cols[i % 3], ink=False)
    # the outside face (over the neighbour's garden)
    k.qy(-0.5, 0.5, 0.0, top - 0.12, 0.5, 1, 'brick')
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, top)


# ================================================================ the quay balustrade over the canal (zone 1 north)
def quay(k, rnd, kind):
    """the fondamenta's edge: a stone balustrade on the campo (-Y) side of the cell, the paving behind it to the kerb,
    the quay wall down into the canal (+Y side); kinds: A, P (a pier with a lantern), R (a mooring ring)"""
    if kind == 'P':
        k.bxc(-0.24, 0.24, -0.52, -0.08, 0.0, 1.2, 'stone', cull='b')
        k.bxc(-0.28, 0.28, -0.56, -0.04, 1.2, 1.32, 'stone')
        k.cyl(0, -0.3, 1.32, 0.05, 0.05, 0.88, 'iron', seg=6)
        k.cyl(0, -0.3, 2.22, 0.07, 0.11, 0.32, 'lamp', seg=6, ink=False)
        k.cyl(0, -0.3, 2.54, 0.14, 0.03, 0.12, 'iron', seg=6)
        k.cyl(0, -0.3, 2.17, 0.08, 0.08, 0.04, 'iron', seg=6)
        balustrade_x(k, -0.5, -0.24, -0.39, 0.0, h=1.1, every=0.4, w=0.2, ends=(False, True))
        balustrade_x(k, 0.24, 0.5, -0.39, 0.0, h=1.1, every=0.4, w=0.2, ends=(True, False))
    else:
        balustrade_x(k, -0.5, 0.5, -0.39, 0.0, h=1.1, every=0.4, w=0.2, ends=(False, False))
    k.bxc(-0.5, 0.5, 0.25, 0.5, 0.0, 0.1, 'stone', cull='blr', ink=False)
    k.qy(-0.5, 0.5, WATER - 0.4, 0.0, 0.5, 1, 'stoneD')
    k.qy(-0.5, 0.5, WATER - 0.02, WATER + 0.25, 0.503, 1, 'leafD')
    k.qy(-0.5, 0.5, -0.3, -0.27, 0.503, 1, 'stone')
    if kind == 'R':
        k.cyl(0, 0.505, -0.5, 0.1, 0.1, 0.02, 'iron', seg=8, rot=(-90, 0, 0), ink=False)
        D.mooring_ring(k)
    D.quay_joints(k)
    if kind == 'P':
        D.pier_panel(k)
        D.lamp_collars(k, 0, -0.3, ((1.52, 0.065), (1.95, 0.062)))
    else:
        D.coping_joint(k, 0.0, -0.51, -0.27, 1.1)


# ================================================================ the gate portal, the facades over the gates
GATE_TOP = 5.4


def build_gate(pal, ao):
    """GateFrame: a stone portal 5 m wide (piers x +-1.55..2.5, the full cell deep), the opening 3.1 x 3.2 m under an
    iron fanlight in a round arch, an entablature with a shield, lanterns on both faces; the same both ways"""
    k = kit(pal).begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.55, s * 2.5)
        k.bxc(x0, x1, -0.5, 0.5, 0.0, 4.8, 'stone', cull='bt')
        for f in (-1, 1):
            yf = f * 0.503
            for i in range(5):
                z = 0.4 + i * 0.62
                k.qy(x0 + 0.04, x1 - 0.04, z, z + 0.02, yf, f, 'stoneD')
            k.bxc(x0 - 0.04, x1 + 0.04, f * 0.5, f * 0.56, 0.0, 0.45, 'stoneD', cull='b' + ('k' if f < 0 else 'f'))
        wall_lantern(k, s * 2.02, -0.56, 2.7, arm=0.3)
        k.push(0, 0, 180)
        wall_lantern(k, -s * 2.02, -0.56, 2.7, arm=0.3)
        k.pop()
    cur = arch_curve(-1.55, 1.55, 3.2, 'round', 6)
    for f in (-1, 1):
        yf = f * 0.5
        left = [(-1.55, 3.2)] + [p for p in cur if p[0] <= 1e-6]
        right = [p for p in cur if p[0] >= -1e-6] + [(1.55, 3.2)]
        k.poly([(px, yf, pz) for (px, pz) in left] + [(-1.55, yf, 4.8)], 'stone', (0, f, 0))
        k.poly([(1.55, yf, 4.8)] + [(px, yf, pz) for (px, pz) in right], 'stone', (0, f, 0))
        for (pa, pb) in zip(cur, cur[1:]):
            def out(p):
                dx, dz = p[0], p[1] - 3.2
                L = math.hypot(dx, dz) or 1.0
                return (p[0] + dx / L * 0.16, p[1] + dz / L * 0.16)
            qa, qb = out(pa), out(pb)
            yb = yf + f * 0.004
            k.poly([(pa[0], yb, pa[1]), (qa[0], yb, qa[1]), (qb[0], yb, qb[1]), (pb[0], yb, pb[1])], 'stoneD', (0, f, 0))
        k.bxc(-0.16, 0.16, f * 0.5, f * 0.56, 4.5, 4.8, 'stone', cull=('f' if f > 0 else 'k') + 't')
    for (pa, pb) in zip(cur, cur[1:]):
        mx, mz = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 - 3.2
        k.poly([(pa[0], -0.5, pa[1]), (pb[0], -0.5, pb[1]), (pb[0], 0.5, pb[1]), (pa[0], 0.5, pa[1])], 'stoneD', (-mx, 0, -mz))
    k.bxc(-1.55, 1.55, -0.12, 0.12, 3.08, 3.2, 'iron', cull='lr')
    fan = [(-1.55, 3.2)] + cur[1:-1] + [(1.55, 3.2)]
    k.poly([(px, -0.002, pz) for (px, pz) in fan], 'glass', (0, -1, 0))
    k.poly([(px, 0.002, pz) for (px, pz) in fan], 'glass', (0, 1, 0))
    for i in range(1, 8):
        a = math.pi * i / 8
        k.beam((math.cos(a) * 0.3, 0, 3.2 + math.sin(a) * 0.3), (math.cos(a) * 1.5, 0, 3.2 + math.sin(a) * 1.5), 0.04, 'iron', ink=False)
    k.cyl(0, -0.03, 3.2, 0.3, 0.3, 0.06, 'iron', seg=10, rot=(-90, 0, 0), ink=False)
    # the entablature over the portal: frieze, a gilt band, the cornice; the shield with a star on both faces
    k.bxc(-2.6, 2.6, -0.58, 0.58, 4.8, 5.1, 'stone')
    k.bxc(-2.75, 2.75, -0.7, 0.7, 5.1, GATE_TOP, 'stone', bevel=True)
    for f in (-1, 1):
        k.poly([(-1.2, f * 0.584, 4.88), (1.2, f * 0.584, 4.88), (1.2, f * 0.584, 5.02), (-1.2, f * 0.584, 5.02)], 'gold', (0, f, 0))
    k.prism_xz([(-0.3, 3.75), (0.3, 3.75), (0.3, 4.3), (0.0, 4.48), (-0.3, 4.3)], -0.57, 0.57, 'marbleR')
    for f in (-1, 1):
        star = []
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            r = 0.15 if i % 2 == 0 else 0.065
            star.append((math.cos(a) * r, f * 0.574, 4.05 + math.sin(a) * r))
        k.poly(star, 'gold', (0, f, 0))
    k.col(-2.5, -1.55, -0.5, 0.5, 0.0, 4.8)
    k.col(-1.55, 1.55, -0.5, 0.5, 3.2, 4.8)
    k.col(1.55, 2.5, -0.5, 0.5, 0.0, 4.8)
    done(k, 'GateFrame', ao)
    # the shutter: a pair of green panelled doors with iron studs (it rolls up like a portcullis)
    k = kit(pal).begin()
    Hs = 3.05
    k.bxc(-1.5, 1.5, -0.06, 0.06, 0.0, Hs, 'shutD', ink=False)
    for f in (-1, 1):
        yf = f * 0.064
        k.qy(-0.012, 0.012, 0.0, Hs, yf + f * 0.008, f, 'iron')
        for (a, b) in ((-1.42, -0.08), (0.08, 1.42)):
            for (c0, c1) in ((0.15, 1.35), (1.55, 2.9)):
                k.qy(a, b, c0, c1, yf, f, 'shut')
                k.qy(a + 0.06, b - 0.06, c0 + 0.06, c1 - 0.06, yf + f * 0.004, f, 'shutD')
        for xx in (-1.3, -0.25, 0.25, 1.3):
            for zz in (0.5, 2.2):
                k.qy(xx - 0.025, xx + 0.025, zz - 0.025, zz + 0.025, yf + f * 0.008, f, 'iron')
    obj = done(k, 'GateShutter', False)
    shutter_hull(pal, obj)


def gate_top(k, rnd, H, back=None):
    """the facade over a gate portal (x -2.5..2.5, from the portal's top to the cornice) facing -Y, its courses
    matching the neighbouring modules; back: None, 'plain' (a stucco face with a window, +Y) or 'canal'"""
    pn, sf = spec(H)
    top = H - 0.4
    z0 = GATE_TOP + 0.15
    holes = []
    if H == HP:
        for x in (-1.0, 0.0, 1.0):
            holes.append((x - 0.31, x + 0.31, z0, z0 + 1.55 + 0.38))
    else:
        holes.append((-0.28, 0.28, z0 + 0.1, pn[1]))
    sx = (-1.5, 1.5) if H == HP else (-1.0, 1.0)
    for x in sx:
        holes.append((x - 0.26, x + 0.26, sf[0], sf[1]))
    for (a, b, c0, c1) in wall_parts(-2.5, 2.5, GATE_TOP, top, holes):
        k.qy(a, b, c0, c1, Y, -1, 'stucco')
    if H == HP:
        for x in (-1.0, 0.0, 1.0):
            arched_opening(k, x - 0.31, x + 0.31, z0, z0 + 1.55, 'ogee', 0.16, 'glass', frame='stone', fw=0.07, rise=0.38)
            glints(k, x - 0.31, x + 0.31, z0 + 0.2, z0 + 1.5, Y + 0.155)
        balcony(k, rnd, -1.6, 1.6, z0, depth=0.55, ends=(True, True))
    else:
        window(k, rnd, -0.28, 0.28, z0 + 0.1, pn[1], kind='open', box=True)
    for x in sx:
        window(k, rnd, x - 0.26, x + 0.26, sf[0], sf[1], kind='open')
    bands(k, H, GF if H != HP else PGF, -2.5, 2.5, plinth=False, roof=back is None, string=False)
    if back:
        k.push(0, 0, 180)
        if back == 'canal':
            hs = [(x - 0.31, x + 0.31, z0, z0 + 1.55 + 0.4) for x in (-1.0, 0.0, 1.0)] + [(x - 0.26, x + 0.26, 9.0, 10.85) for x in (-1.5, 1.5)]
            for (a, b, c0, c1) in wall_parts(-2.5, 2.5, GATE_TOP, top, hs):
                k.qy(a, b, c0, c1, Y, -1, 'stucco')
            for x in (-1.0, 0.0, 1.0):
                arched_opening(k, x - 0.31, x + 0.31, z0, z0 + 1.55, 'ogee', 0.16, 'glass', frame='stone', fw=0.07, rise=0.4)
            balcony(k, rnd, -1.6, 1.6, z0, depth=0.6, ends=(True, True), flowers_=False)
            for x in (-1.5, 1.5):
                rect_opening(k, x - 0.26, x + 0.26, 9.0, 10.85, 0.16, 'glass', frame='stone', fw=0.06)
        else:
            for (a, b, c0, c1) in wall_parts(-2.5, 2.5, GATE_TOP, top, [(-0.28, 0.28, sf[0], sf[1])]):
                k.qy(a, b, c0, c1, Y, -1, 'stucco')
            rect_opening(k, -0.28, 0.28, sf[0], sf[1], 0.16, 'glass', frame='stone', fw=0.06)
        k.bxc(-2.5, 2.5, Y - 0.1, Y, H - 0.4, H - 0.26, 'stone', cull='ktlr')
        k.bxc(-2.5, 2.5, Y - 0.28, Y, H - 0.26, H, 'stone', cull='klr')
        k.pop()
        k.poly([(-2.5, Y - 0.3, H + 0.04), (2.5, Y - 0.3, H + 0.04), (2.5, 0.0, H + 0.65), (-2.5, 0.0, H + 0.65)], 'roof', (0, -0.7, 0.7))
        k.poly([(-2.5, 0.0, H + 0.65), (2.5, 0.0, H + 0.65), (2.5, 0.8, H + 0.04), (-2.5, 0.8, H + 0.04)], 'roof', (0, 0.7, 0.7))


def build_gate_tops(pal, ao):
    for name, H, back in (('GateTop_3', H3, None), ('GateTop_P', HP, 'plain'), ('GateTop_C', HP, 'canal')):
        k = kit(pal).begin()
        gate_top(k, random.Random(seed(name)), H, back=back)
        done(k, name, ao, recolor=None if H != HP else {'stucco': 'rose', 'stuccoL': 'roseL', 'stuccoD': 'roseD'})


# ================================================================ trail: the bridge's balustrades, the exit lane
def build_trail(pal, ao):
    """trail walls run 1 m along Blender Y with their trail face toward +X (collision x -0.25..0.25). Bridge_A / _B:
    the bridge's balustrade (1.1 m) and its fascia down toward the canal; Calle_A.._C: the exit lane's walls (3.4 m)"""
    for name, lamp in (('Bridge_A', False), ('Bridge_B', True)):
        k = kit(pal).begin()
        k.push(0, 0, 90)   # model along X: local -Y (the trail side) turns to +X
        if lamp:
            k.bxc(-0.2, 0.2, -0.22, 0.22, 0.0, 1.25, 'stone', cull='b')
            k.bxc(-0.24, 0.24, -0.26, 0.26, 1.25, 1.36, 'stone')
            k.cyl(0, 0, 1.36, 0.045, 0.045, 0.78, 'iron', seg=6)
            k.cyl(0, 0, 2.16, 0.07, 0.11, 0.3, 'lamp', seg=6, ink=False)
            k.cyl(0, 0, 2.46, 0.14, 0.03, 0.12, 'iron', seg=6)
            k.cyl(0, 0, 2.11, 0.08, 0.08, 0.04, 'iron', seg=6)
            balustrade_x(k, -0.5, -0.2, 0.0, 0.0, h=1.1, every=0.4, w=0.22, ends=(False, True))
            balustrade_x(k, 0.2, 0.5, 0.0, 0.0, h=1.1, every=0.4, w=0.22, ends=(True, False))
        else:
            balustrade_x(k, -0.5, 0.5, 0.0, 0.0, h=1.1, every=0.4, w=0.22)
        k.qz(-0.5, 0.5, -0.25, -0.11, 0.006, 1, 'cobble')
        k.qz(-0.5, 0.5, 0.11, 0.25, 0.006, 1, 'cobble')
        k.bxc(-0.5, 0.5, 0.25, 0.32, -0.9, 0.06, 'stone', cull='lrb', ink=False)
        D.bridge_detail(k, lamp)
        k.qy(-0.5, 0.5, -0.9, 0.0, 0.324, 1, 'stoneD')
        k.pop()
        done(k, name, ao)
    for name, kind in (('Calle_A', 'A'), ('Calle_B', 'B'), ('Calle_C', 'C')):
        k = kit(pal).begin()
        k.push(0, 0, 90)
        k.push(0, -0.25 - Y, 0)   # the module's face plane (y = -0.5) on the trail side, local y = -0.25
        holes = []
        if kind == 'B':
            holes.append((-0.25, 0.25, 1.6, 2.5))
        if kind == 'C':
            holes.append((-0.4, 0.4, 0.0, 2.3 + 0.4))
        for (a, b, c0, c1) in wall_parts(-0.5, 0.5, 0.0, CALLE_H - 0.15, holes):
            k.qy(a, b, c0, c1, Y, -1, 'stucco' if kind != 'A' else 'terra')
        for (a, b) in (((-0.5, -0.48), (0.48, 0.5)) if kind == 'C' else ((-0.5, 0.5),)):
            k.qy(a, b, 0.0, 0.45, Y - 0.012, -1, 'stone')
        k.bxc(-0.5, 0.5, Y - 0.08, Y + 0.5, CALLE_H - 0.15, CALLE_H, 'stone', cull='lrb')
        if kind == 'B':
            rect_opening(k, -0.25, 0.25, 1.6, 2.5, 0.12, 'glass', frame='stone', fw=0.06)
            k.bxc(-0.32, 0.32, Y - 0.16, Y - 0.07, 1.35, 1.5, 'terra', cull='k', ink=False)
            k.hullp([(-0.3, Y - 0.15, 1.5), (0.3, Y - 0.15, 1.5), (0.3, Y - 0.08, 1.5), (-0.3, Y - 0.08, 1.5), (0.0, Y - 0.12, 1.72)], 'fRed', ink=False)
        if kind == 'C':
            arched_opening(k, -0.4, 0.4, 0.0, 2.3, 'round', 0.18, 'wood', frame='stone', fw=0.07, sill=False)
        if kind == 'A':
            k.qy(-0.3, 0.3, 0.9, 1.6, Y - 0.01, -1, 'plaster')
        k.qy(-0.5, 0.5, 0.0, CALLE_H - 0.15, Y + 0.5, 1, 'stuccoD')
        k.pop()
        k.pop()
        done(k, name, ao)
    # the hatch: a bronze cistern lid in an Istrian stone ring set in the paving
    k = kit(pal).begin()
    k.bxc(-1.3, 1.3, -1.3, 1.3, 0.0, 0.05, 'stone', cull='b')
    k.lathe(0, 0, 0.05, [(0.95, 0.0), (0.95, 0.03), (0.0, 0.03)], 'bronze', seg=16, ink=False)
    for i in range(8):
        a = i * math.pi / 4
        k.beam((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.09), (math.cos(a) * 0.88, math.sin(a) * 0.88, 0.09), 0.04, 'verd', ink=False)
    k.lathe(0, 0, 0.08, [(0.18, 0.0), (0.18, 0.04), (0.0, 0.04)], 'gold', seg=10, ink=False)
    for (x, y) in ((-1.15, -1.15), (1.15, -1.15), (1.15, 1.15), (-1.15, 1.15)):
        k.qz(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.053, 1, 'stoneD')
    done(k, 'Hatch', ao)


def build_walls(pal, ao):
    for kind in ('Win', 'Pier', 'PierL', 'Door', 'BalL', 'BalM', 'BalR', 'Quoin'):
        k = kit(pal).begin()
        house(k, random.Random(seed('P' + kind)), HP, kind)
        done(k, 'HP_%s' % kind, ao)
    for inner in ('L', 'R'):
        k = kit(pal).begin()
        house(k, random.Random(5), HP, 'Pier', inner=inner)
        done(k, 'HP_In%s' % inner, ao)
    k = kit(pal).begin()
    corner_block(k, HP, PGF)
    done(k, 'HP_Corner', ao)
    for name, front, back in (('C_Win', 'Win', 'Win'), ('C_WinC', 'WinC', 'Water'), ('C_Pier', 'Pier', 'Pier'), ('C_PierL', 'PierL', 'Pier'),
                              ('C_BalL', 'BalL', 'GothR'), ('C_BalM', 'BalM', 'Goth'), ('C_BalR', 'BalR', 'GothL'), ('C_Quoin', 'Quoin', 'Quoin')):
        k = kit(pal).begin()
        canal_module(k, random.Random(seed(name)), front, back)
        done(k, name, ao)
    for inner in ('L', 'R'):
        k = kit(pal).begin()
        canal_module(k, random.Random(6), 'Pier', 'Pier', inner=inner)
        done(k, 'C_In%s' % inner, ao)
    for kind in ('A', 'V', 'N', 'L', 'D'):
        k = kit(pal).begin()
        garden_wall(k, random.Random(seed('GW' + kind)), kind)
        done(k, 'GW_%s' % kind, ao)
    for kind in ('A', 'P', 'R'):
        k = kit(pal).begin()
        quay(k, random.Random(seed('Q' + kind)), kind)
        done(k, 'Quay_%s' % kind, ao)
    build_gate(pal, ao)
    build_gate_tops(pal, ao)
    build_trail(pal, ao)
