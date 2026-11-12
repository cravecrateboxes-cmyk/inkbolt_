"""INKBOLT kit-venetian walls: the campo's house fronts (1 m modules in two heights; the theme repaints the stucco per
building), the mansion's courtyard fronts and its canal facade, inner-corner and zone-corner blocks, the quay
balustrade over the canal, the gate portal with its fanlight and the facades the theme sets over the gates, the
bridge balustrades and the exit lane's walls (trail), the hatch. Conventions: ven_base.py."""
import math
import random

from ven_base import *  # noqa: F401,F403
from ven_base import (kit, done, arch_curve, arched_opening, rect_opening, glints, flower_box, flowers, wall_lantern,
                      lantern_glow, balustrade_x, baluster, text, wall_parts)

Y = -0.5   # the facade plane


# ================================================================ house fronts
def spec(H):
    """storey openings of a house: (z0, z1) of the piano nobile window and the second-floor window (None for H2)"""
    if H == H3:
        return (4.55, 6.45), (7.7, 9.3)
    if H == H2:
        return (4.55, 6.45), None
    return (5.0, 7.3), (9.0, 10.85)   # the mansion


def bands(k, H, gf, x0=-0.5, x1=0.5, ends=(False, False), cornice=True, roof=True, plinth=True, back=False, string=True, gap=None):
    """the horizontal stone courses of a front: plinth, the string course over the ground floor, the cornice, the
    roof slope behind it; ends: keep the end faces (a quoin's side over a lower neighbour, a corner)"""
    cl = ('l' if not ends[0] else '') + ('r' if not ends[1] else '')
    if plinth:
        for (a, b) in ((x0, gap[0]), (gap[1], x1)) if gap else ((x0, x1),):
            c2 = ('l' if (a > x0 or not ends[0]) else '') + ('r' if (b < x1 or not ends[1]) else '')
            k.bxc(a, b, Y - 0.035, Y, 0.0, 0.5, 'stone', cull='bk' + ('' if gap else c2) + (cl if not gap else ''), ink=False)
            k.poly([(a, Y - 0.039, 0.0), (b, Y - 0.039, 0.0), (b, Y - 0.039, 0.06), (a, Y - 0.039, 0.06)], 'stoneD', (0, -1, 0))
    if string:
        k.bxc(x0, x1, Y - 0.06, Y, gf - 0.08, gf + 0.06, 'stone', cull='k' + cl, ink=False)
    if cornice:
        k.bxc(x0, x1, Y - 0.1, Y, H - 0.4, H - 0.26, 'stone', cull='kt' + cl)
        k.bxc(x0, x1, Y - 0.28, Y, H - 0.26, H, 'stone', cull='k' + cl)
        # dentils under the cornice's lip
    if roof:
        # tiles from the eave back over the module: a slope up toward +Y, and the eave's tile edge
        e0, e1 = (x0 + (0.004 if ends[0] else 0.0), x1 - (0.004 if ends[1] else 0.0))
        k.poly([(e0, Y - 0.3, H + 0.04), (e1, Y - 0.3, H + 0.04), (e1, 0.5, H + 0.95), (e0, 0.5, H + 0.95)], 'roof', (0, -0.7, 0.7))
        k.qy(e0, e1, H + 0.0, H + 0.05, Y - 0.304, -1, 'roofD')


def shutters(k, x0, x1, z0, z1, open_=True, c='shut'):
    """green louvred shutters on a window (x0..x1, z0..z1) at the facade plane: open leaves flat against the wall or
    closed leaves across the opening"""
    w = (x1 - x0) / 2
    lw = min(w, 0.49 - w - 0.06)   # an open leaf stays inside the 1 m module centred on the window (the frame: 6 cm)
    leaves = ((x0 - 0.06 - lw, x0 - 0.06), (x1 + 0.06, x1 + 0.06 + lw)) if open_ else ((x0 + 0.004, x0 + w - 0.004), (x0 + w + 0.004, x1 - 0.004))
    yb = Y - 0.004
    for (a, b) in leaves:
        k.bxc(a, b, yb - 0.035, yb, z0, z1, c, cull='ktb', ink=False)
        for i in (1, 3):
            z = z0 + (z1 - z0) * i / 4
            k.poly([(a + 0.03, yb - 0.039, z), (b - 0.03, yb - 0.039, z), (b - 0.03, yb - 0.039, z + 0.05), (a + 0.03, yb - 0.039, z + 0.05)], 'shutD', (0, -1, 0))


def window(k, rnd, x0, x1, z0, z1, kind='open', box=False, back='glass', bars=False):
    rect_opening(k, x0, x1, z0, z1, 0.16, back, frame='stone', fw=0.06)
    if back == 'glass':
        k.qy(x0, x1, (z0 + z1) * 0.5 + 0.06, (z0 + z1) * 0.5 + 0.1, Y + 0.152, -1, 'stone')
        k.qy((x0 + x1) / 2 - 0.02, (x0 + x1) / 2 + 0.02, z0, z1, Y + 0.148, -1, 'stone')
        glints(k, x0, x1, z0, z1, Y + 0.156)
    if bars:
        for i in (1, 2):
            bx = x0 + (x1 - x0) * i / 3
            k.bxc(bx - 0.012, bx + 0.012, Y + 0.02, Y + 0.044, z0, z1, 'iron', cull='ktb', ink=False)
        k.bxc(x0, x1, Y + 0.05, Y + 0.07, (z0 + z1) / 2 - 0.012, (z0 + z1) / 2 + 0.012, 'iron', cull='klr', ink=False)
    if kind in ('open', 'closed'):
        shutters(k, x0, x1, z0, z1, open_=kind == 'open')
    if box:
        flower_box(k, rnd, x0 - 0.06, x1 + 0.06, Y - 0.075, z0 - 0.07 - 0.17, trail=0.5)


def door(k, x0, x1, top, kind='round'):
    """an arched front door: the leaf (panels, knocker) in the reveal, a stone step"""
    cr = arched_opening(k, x0, x1, 0.0, top, kind, 0.2, 'wood', frame='stone', fw=0.08, sill=False)
    yd = Y + 0.2 - 0.004
    xm = (x0 + x1) / 2
    k.qy(xm - 0.008, xm + 0.008, 0.05, top, yd, -1, 'woodD')
    for (a, b) in ((x0 + 0.07, xm - 0.06), (xm + 0.06, x1 - 0.07)):
        for (c0, c1) in ((0.25, 1.15), (1.35, top - 0.15)):
            k.qy(a, b, c0, c1, yd, -1, 'woodD')
            k.qy(a + 0.03, b - 0.03, c0 + 0.03, c1 - 0.03, yd - 0.003, -1, 'wood')
    k.cyl(xm + 0.12, yd - 0.01, 1.25, 0.035, 0.035, 0.012, 'gold', seg=6, rot=(90, 0, 0), ink=False)
    k.bxc(x0 - 0.08, x1 + 0.08, Y - 0.14, Y + 0.2, 0.0, 0.1, 'stone', cull='bk')
    return cr


def shop(k, rnd, x0, x1, top, sign=None):
    """an arched shop window: glass in a wooden frame, goods on a shelf behind it, a stone sill"""
    cr = arched_opening(k, x0, x1, 0.5, top, 'round', 0.16, 'glass', frame='stone', fw=0.08, sill=False)
    yd = Y + 0.16
    k.bxc(x0 - 0.04, x1 + 0.04, Y - 0.08, Y + 0.02, 0.44, 0.535, 'stone', cull='k')
    k.qy(x0, x1, 0.5, 0.62, yd - 0.004, -1, 'wood')
    k.qy(x0, x1, top - 0.04, top, yd - 0.004, -1, 'wood')
    xm = (x0 + x1) / 2
    k.qy(xm - 0.02, xm + 0.02, 0.62, top, yd - 0.008, -1, 'wood')
    for i, c in enumerate(('fRed', 'glassL', 'gold', 'verd', 'fPink')):
        gx = x0 + 0.08 + (x1 - x0 - 0.16) * i / 4
        k.qy(gx - 0.05, gx + 0.05, 0.95, 0.95 + 0.12 + 0.08 * (i % 2), yd - 0.012, -1, c)
    k.qy(x0 + 0.04, x1 - 0.04, 0.9, 0.94, yd - 0.004, -1, 'woodD')
    glints(k, x0, x1, 1.1, top, yd - 0.016)
    return cr


def balcony(k, rnd, x0, x1, z, depth=0.55, ends=(False, False), flowers_=True):
    """a stone balcony on corbels at height z over the module span x0..x1 (ends: return balustrades at -X / +X)"""
    yf = Y - depth
    k.bxc(x0, x1, yf, Y, z - 0.14, z, 'stone', cull='k' + ('' if ends[0] else 'l') + ('' if ends[1] else 'r'))
    for cx in ((x0 + x1) / 2,):
        k.prism_xz([(cx - 0.08, z - 0.14), (cx + 0.08, z - 0.14), (cx + 0.06, z - 0.42), (cx - 0.06, z - 0.42)], Y - depth * 0.8, Y, 'stoneD', cull='k')
    balustrade_x(k, x0 + (0.04 if ends[0] else 0.0), x1 - (0.04 if ends[1] else 0.0), yf + 0.1, z, h=0.95, every=0.33, w=0.14,
                 ends=ends)
    for side, on in ((0, ends[0]), (1, ends[1])):
        if not on:
            continue
        xs = x0 + 0.07 if side == 0 else x1 - 0.07
        k.bxc(xs - 0.06, xs + 0.06, yf + 0.03, Y, z + 0.84, z + 0.935, 'stone', cull='k')
        baluster(k, xs, (yf + Y) / 2, z, 0.85, 'stoneD')
    if flowers_:
        # pots of geraniums on the rail and trailing over the front
        flowers(k, rnd, x0 + 0.04, x1 - 0.04, yf + 0.04, yf + 0.16, z + 0.95, int((x1 - x0) / 0.15),
                ('fRed', 'fPink', 'fRed', 'white', 'fPurp'), s=0.065, trail=0.9, yt=yf + 0.02)


def house(k, rnd, H, kind, inner=None, chimney=False, roof=True):
    """one 1 m module of a house front (x -0.5..0.5, the street face at y = -0.5); kind: Win WinC WinF Pier PierL
    Door Shop BalL BalM BalR Quoin; inner: 'L' / 'R' (an inner corner at local -X / +X: the bands start 0.3 m in)"""
    gf = GF if H != HP else PGF
    pn, sf = spec(H)
    top = H - 0.4
    holes, todo = [], []
    if kind in ('Win', 'WinC', 'WinF'):
        holes.append((-0.25, 0.25, 1.55, 2.45))
        todo.append(lambda: window(k, rnd, -0.25, 0.25, 1.55, 2.45, kind='none', bars=True))
    if kind == 'Door':
        holes.append((-0.38, 0.38, 0.0, 2.55 + 0.38))
        todo.append(lambda: door(k, -0.38, 0.38, 2.55))
    if kind == 'Shop':
        holes.append((-0.4, 0.4, 0.5, 2.6 + 0.4))
        todo.append(lambda: shop(k, rnd, -0.4, 0.4, 2.6))
    bal = kind in ('BalL', 'BalM', 'BalR')
    if kind in ('Win', 'WinC', 'WinF', 'Door', 'Shop', 'Plain'):
        sk = 'closed' if kind == 'WinC' else 'open'
        holes.append((-0.22, 0.22, pn[0], pn[1]))
        todo.append(lambda: window(k, rnd, -0.22, 0.22, pn[0], pn[1], kind=sk, box=kind == 'WinF'))
        if sf:
            holes.append((-0.21, 0.21, sf[0], sf[1]))
            todo.append(lambda: window(k, rnd, -0.21, 0.21, sf[0], sf[1], kind='closed' if kind == 'Shop' else 'open'))
    if bal:
        z0 = gf + 0.15
        cr = z0 + 1.95 + 0.38
        holes.append((-0.31, 0.31, z0, cr))
        todo.append(lambda: arched_opening(k, -0.31, 0.31, z0, z0 + 1.95, 'ogee', 0.16, 'glass', frame='stone', fw=0.07, n=4, rise=0.38))
        todo.append(lambda: glints(k, -0.31, 0.31, z0 + 0.3, z0 + 1.9, Y + 0.155))
        if sf:
            holes.append((-0.21, 0.21, sf[0], sf[1]))
            todo.append(lambda: window(k, rnd, -0.21, 0.21, sf[0], sf[1], kind='open'))
    # the front: stucco strips round the openings
    for (a, b, c0, c1) in wall_parts(-0.5, 0.5, 0.0, top, holes):
        k.qy(a, b, c0, c1, Y, -1, 'stucco')
    for f in todo:
        f()
    if bal:
        balcony(k, rnd, -0.5, 0.5, gf + 0.15, ends=(kind == 'BalL', kind == 'BalR'))
    if kind in ('Pier', 'PierL'):
        # a round stone patera on the piano nobile, a drainpipe on some
        k.cyl(0, Y - 0.004, pn[0] + 0.9, 0.16, 0.16, 0.03, 'stone', seg=8, rot=(90, 0, 0), ink=False)
    if kind == 'PierL':
        wall_lantern(k, 0.0, Y, 2.55)
    if kind == 'Quoin':
        z, i = 0.5, 0
        while z < top - 0.05:
            h = min(0.6, top - z)
            w = 0.36 if i % 2 else 0.26
            k.qy(-w, w, z + 0.01, z + h - 0.01, Y - 0.006, -1, 'stone')
            z += h
            i += 1
    x0 = -0.2 if inner == 'L' else -0.5
    x1 = 0.2 if inner == 'R' else 0.5
    q = kind == 'Quoin'
    bands(k, H, gf, x0, x1, ends=(q or inner == 'L', q or inner == 'R'), roof=roof, gap=(-0.46, 0.46) if kind == 'Door' else None)
    if q:
        # the side faces over a lower neighbour
        k.qx(Y, 0.5, 0.0, top, -0.5, -1, 'stuccoD')
        k.qx(Y, 0.5, 0.0, top, 0.5, 1, 'stuccoD')
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, H)   # the house: solid to the cornice (shots, sight lines; wall.cols)
    if chimney:
        # a funnel chimney on the roof
        k.bxc(-0.16, 0.16, 0.05, 0.37, H + 0.5, H + 1.6, 'stucco', cull='b')
        k.lathe(0, 0.21, H + 1.6, [(0.12, 0.0), (0.3, 0.45), (0.3, 0.62), (0.0, 0.66)], 'brick', seg=8)


def corner_block(k, H, gf):
    """a zone corner: a block of the house's height, its stone courses flush with the cell (the neighbouring fronts'
    courses run up to it); its two outer faces face the canal / the lanes"""
    for s in (-1, 1):
        k.qy(-0.5, 0.5, 0.0, H, s * 0.5, s, 'stucco')
        k.qx(-0.5, 0.5, 0.0, H, s * 0.5, s, 'stucco')
        k.qy(-0.5, 0.5, gf - 0.08, gf + 0.06, s * 0.504, s, 'stone')
        k.qx(-0.5, 0.5, gf - 0.08, gf + 0.06, s * 0.504, s, 'stone')
        k.qy(-0.5, 0.5, H - 0.4, H, s * 0.504, s, 'stone')
        k.qx(-0.5, 0.5, H - 0.4, H, s * 0.504, s, 'stone')
    k.hullp([(-0.5, -0.5, H), (0.5, -0.5, H), (0.5, 0.5, H), (-0.5, 0.5, H), (0, 0, H + 0.6)], 'roof')
    k.col(-0.5, 0.5, -0.5, 0.5, 0.0, H)


def seed(name):
    return sum(ord(c) * (i + 1) for i, c in enumerate(name))


def build_houses(pal, ao):
    for H, tag in ((H3, '3'), (H2, '2')):
        for kind in ('Win', 'WinC', 'WinF', 'Pier', 'PierL', 'Door', 'Shop', 'Plain', 'BalL', 'BalM', 'BalR', 'Quoin'):
            if tag == '2' and kind in ('WinC', 'WinF'):
                continue
            rnd = random.Random(seed(kind + tag))
            k = kit(pal).begin()
            house(k, rnd, H, kind)
            done(k, 'H%s_%s' % (tag, kind), ao, bevel=0.0)
        if tag == '3':
            k = kit(pal).begin()
            house(k, random.Random(7), H, 'Pier', chimney=True)
            done(k, 'H%s_PierC' % tag, ao)
        for inner in ('L', 'R'):
            k = kit(pal).begin()
            house(k, random.Random(5), H, 'Pier', inner=inner)
            done(k, 'H%s_In%s' % (tag, inner), ao)
        k = kit(pal).begin()
        corner_block(k, H, GF)
        done(k, 'H%s_Corner' % tag, ao)
