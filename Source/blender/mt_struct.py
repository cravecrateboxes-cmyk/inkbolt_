"""kit-metro structure: wall faces (one per finish scheme), the wall art overlays the theme's chooser stacks on them
(posters, billboards, network maps, station name panels, WAY OUT and platform signs, clocks, fire points, menu boards,
toilet, staff and lift doors, tunnel mouths, platform-end signs), the through pieces (shop windows, ticket windows),
the sunk side faces (platform edges with their coping and yellow line, the escalator well walls with the closed
shutter, name panels, ads), doorways and archway headers, the gate, trail walls, the hatch, the weapon stand,
ceiling tiles (4 m), the two barrel vaults and their end walls (8 m), the floor mosaic, the fixed stairs, the
escalator bank, the footbridge stairs, the trackbed steps, the glass and steel rails, hanging screens and signs,
shop fascia signs. See mt_base.py for the conventions."""
import math
import random

from mt_base import *  # noqa: F401,F403
import mt_base as B


def faces(k, ao, name, fn, glow=None):
    k.begin()
    fn(k)
    k.finish(name, ao=ao)
    if glow:
        k.begin()
        glow(k)
        k.finish(name + '_Glow')


YA = Y0 - 0.006    # art overlay plane (6 mm proud of the wall face)


# ================================================================ wall faces
def build_faces(k, ao):
    for sch in B.SCHEMES:
        faces(k, ao, 'I' + sch, lambda k, s=sch: paint(k, s))


# ================================================================ art overlays (no wall paint: stacked on a face)
ADS = [  # word, sub line, background, letters, deco
    ('SKYLARK', 'HOLIDAYS BY RAIL', 'scrB', 'paper', 'sun'),
    ('FIZZBOLT', 'THE CRACKLING COLA', 'crim', 'paper', 'can'),
    ('LUMEN 9', 'SEE IT BRIGHTER', 'black', 'amberL', 'phone'),
    ('OPERA NIGHTS', 'GRAND HALL - TONIGHT', 'purple', 'foodY', 'star'),
]


def poster(i):
    word, sub, bg, fg, deco = ADS[i]

    def fn(k):
        k.bx(-0.42, 0.42, Y0 - 0.035, Y0, 1.2, 2.8, 'steelD', cull='k')
        y = Y0 - 0.039
        k.fq(-0.38, 0.38, y, 1.24, 2.76, bg)
        k.text(word, 0.0, y - 0.004, 2.35, 0.2, fg, font='display', maxw=0.68)
        k.text(sub, 0.0, y - 0.004, 2.2, 0.06, fg, font='cond', maxw=0.66)
        if deco == 'sun':
            k.poly([(math.cos(a / 10 * 6.283) * 0.2, y - 0.004, 1.75 + math.sin(a / 10 * 6.283) * 0.2) for a in range(10)], 'foodY', (0, -1, 0))
            k.fq(-0.38, 0.38, y - 0.004, 1.24, 1.5, 'blueD')
        elif deco == 'can':
            k.fq(-0.12, 0.12, y - 0.004, 1.4, 2.0, 'chrome')
            k.fq(-0.12, 0.12, y - 0.008, 1.6, 1.8, 'crimD')
        elif deco == 'phone':
            k.fq(-0.15, 0.15, y - 0.004, 1.35, 2.05, 'graph')
            k.fq(-0.12, 0.12, y - 0.008, 1.42, 1.98, 'scrB')
        else:
            for (x, z) in ((-0.2, 1.7), (0.15, 1.85), (0.05, 1.5)):
                k.poly([(x + math.cos(a / 5 * 6.283 + 1.57) * (0.09 if a % 1 == 0 else 0.04), y - 0.004, z + math.sin(a / 5 * 6.283 + 1.57) * 0.09) for a in range(5)], 'foodY', (0, -1, 0))
    return fn


BIG = [('NORTHWIND AIR', 'FLY FURTHER FOR LESS', 'blue', 'paper', 'foodY'), ('CITY SYMPHONY', 'BEETHOVEN NIGHTS AT THE GRAND HALL', 'cafe', 'cream', 'mustard')]


def billboard(v, part):
    word, sub, bg, fg, acc = BIG[v]
    i = 'LMR'.index(part)

    def fn(k):
        x0 = -0.44 if part == 'L' else -0.5
        x1 = 0.44 if part == 'R' else 0.5
        k.bx(x0 - (0.04 if part == 'L' else 0), x1 + (0.04 if part == 'R' else 0), Y0 - 0.04, Y0, 1.2, 2.9, 'steelD', cull='k')
        y = Y0 - 0.044
        k.fq(x0, x1, y, 1.24, 2.86, bg)
        k.fq(x0, x1, y - 0.004, 1.24, 1.42, acc)
        ib_text.draw(k, word, 1.5 - 0.5 - i, y - 0.008, 2.15, 0.42, fg, face='y-', font='display', maxw=2.6, clip=(i - 1.5, i + 1 - 1.5))
        ib_text.draw(k, sub, 1.5 - 0.5 - i, y - 0.008, 1.85, 0.11, fg, face='y-', font='cond', maxw=2.4, clip=(i - 1.5, i + 1 - 1.5))
    return fn


LINES = [('crim', [(-0.9, 1.9), (-0.3, 1.75), (0.3, 1.75), (0.9, 1.6)]), ('blue', [(-0.8, 1.35), (-0.2, 1.55), (0.4, 1.95), (0.85, 2.15)]),
         ('green', [(-0.7, 2.3), (0.0, 1.75), (0.6, 1.3)]), ('mustard', [(-0.9, 1.5), (-0.1, 1.5), (0.0, 2.35)])]


def net_map(part):
    """the network map over two cells: four lines through CENTRAL (part L: x -1..0 of the map, R: 0..1)"""
    off = -0.5 if part == 'L' else 0.5

    def fn(k):
        x0 = -0.46 if part == 'L' else -0.5
        x1 = 0.46 if part == 'R' else 0.5
        k.bx(x0 - (0.03 if part == 'L' else 0), x1 + (0.03 if part == 'R' else 0), Y0 - 0.03, Y0, 1.15, 2.55, 'steelD', cull='k')
        y = Y0 - 0.034
        k.fq(x0, x1, y, 1.19, 2.51, 'paper')
        for j, (c, pts) in enumerate(LINES):
            for si, (a, b) in enumerate(zip(pts, pts[1:])):
                yl = y - 0.004 - 0.007 * j - 0.0035 * (si % 2)
                ax, bx_ = a[0] - off, b[0] - off
                lo, hi = max(min(ax, bx_), -0.5), min(max(ax, bx_), 0.5)
                if hi - lo < 0.01:
                    continue
                # clip the segment to this cell
                def at(x):
                    t = (x - ax) / (bx_ - ax) if abs(bx_ - ax) > 1e-6 else 0
                    return a[1] + (b[1] - a[1]) * t
                pa, pb = (lo, at(lo)), (hi, at(hi))
                dx, dz = pb[0] - pa[0], pb[1] - pa[1]
                L = math.hypot(dx, dz) or 1
                nx, nz = -dz / L * 0.022, dx / L * 0.022
                k.poly([(pa[0] - nx, yl, pa[1] - nz), (pb[0] - nx, yl, pb[1] - nz), (pb[0] + nx, yl, pb[1] + nz), (pa[0] + nx, yl, pa[1] + nz)], c, (0, -1, 0))
        if part == 'L':
            k.text('METRO NETWORK', -0.42, y - 0.004, 2.38, 0.08, 'blueD', font='display', align='l')
            k.text('YOU ARE AT CENTRAL', -0.42, y - 0.004, 1.24, 0.05, 'graph', font='cond', align='l')
        else:
            for (x, z) in ((0.1, 1.75), (0.4, 1.95), (0.3, 1.75), (-0.2, 1.55)):
                k.poly([(x + math.cos(a / 6 * 6.283) * 0.028, y - 0.034, z + math.sin(a / 6 * 6.283) * 0.028) for a in range(6)], 'black', (0, -1, 0))
    return fn


def sign_plate(word, x0, x1, z0, z1, bg, fg, cap, arrow=None, font='display', rim=None):
    def fn(k):
        k.bx(x0, x1, Y0 - 0.06, Y0, z0, z1, bg, cull='k')
        y = Y0 - 0.064
        if rim:
            k.fq(x0 + 0.03, x1 - 0.03, y, z1 - 0.05, z1 - 0.03, rim)
        k.text(word, (x0 + x1) / 2 + (0.12 if arrow else 0), y - 0.003, (z0 + z1) / 2, cap, fg, font=font, maxw=(x1 - x0) - (0.4 if arrow else 0.12), valign='m')
        if arrow:
            ax = x0 + 0.13
            zc = (z0 + z1) / 2
            s = min(cap * 0.5, 0.1)
            if arrow == 'up':
                k.poly([(ax - s, y - 0.006, zc), (ax + s, y - 0.006, zc), (ax, y - 0.006, zc + s * 1.1)], fg, (0, -1, 0))
                k.fq(ax - s * 0.35, ax + s * 0.35, y - 0.009, zc - s, zc + 0.001, fg)
            else:
                k.poly([(ax - s * 0.2, y - 0.006, zc - s), (ax + s, y - 0.006, zc), (ax - s * 0.2, y - 0.006, zc + s)], fg, (0, -1, 0))
    return fn


def sliced_plate(word, n, z0, z1, bg, fg, cap, sub=None, rim=None, font='display'):
    """a plate across n cells: cell i draws its slice (read from the viewer's left)"""
    def mk(i):
        def fn(k):
            x0 = -0.46 if i == 0 else -0.5
            x1 = 0.46 if i == n - 1 else 0.5
            k.bx(x0, x1, Y0 - 0.05, Y0, z0, z1, bg, cull='k')
            y = Y0 - 0.054
            if rim:
                k.fq(x0, x1, y, z0 + 0.04, z0 + 0.1, rim)
                k.fq(x0, x1, y, z1 - 0.1, z1 - 0.04, rim)
            zc = (z0 + z1) / 2 + (0.06 if sub else 0)
            ib_text.draw(k, word, n / 2.0 - 0.5 - i, y - 0.004, zc, cap, fg, face='y-', font=font, maxw=n - 0.4,
                         clip=(i - n / 2.0, i + 1 - n / 2.0), valign='m')
            if sub:
                ib_text.draw(k, sub, n / 2.0 - 0.5 - i, y - 0.004, z0 + 0.16, cap * 0.32, fg, face='y-', font='cond', maxw=n - 0.6,
                             clip=(i - n / 2.0, i + 1 - n / 2.0), valign='m')
        return fn
    return mk


def clock(k):
    k.cyl(0, Y0 - 0.02, 2.95, 0.3, 0.3, 0.06, 'black', seg=16, rot=(90, 0, 0))
    y = Y0 - 0.086
    k.poly([(math.cos(a / 16 * 6.283) * 0.26, y, 2.95 + math.sin(a / 16 * 6.283) * 0.26) for a in range(16)], 'paper', (0, -1, 0))
    for h in range(12):
        a = h / 12 * 6.283
        k.fq(math.sin(a) * 0.22 - 0.01, math.sin(a) * 0.22 + 0.01, y - 0.003, 2.95 + math.cos(a) * 0.22 - 0.02, 2.95 + math.cos(a) * 0.22 + 0.02, 'black')
    k.poly([(-0.012, y - 0.006, 2.95), (0.012, y - 0.006, 2.95), (0.1, y - 0.006, 3.1), (0.085, y - 0.006, 3.11)], 'black', (0, -1, 0))
    k.poly([(-0.01, y - 0.009, 2.95), (0.01, y - 0.009, 2.95), (0.01, y - 0.009, 3.15), (-0.01, y - 0.009, 3.15)], 'crim', (0, -1, 0))


def fire_point(k):
    k.bx(-0.3, 0.3, Y0 - 0.12, Y0, 0.5, 1.6, 'crim', cull='k')
    k.fq(-0.24, 0.24, Y0 - 0.123, 1.3, 1.52, 'paper')
    k.text('FIRE POINT', 0.0, Y0 - 0.126, 1.37, 0.08, 'crim', font='display', maxw=0.44)
    k.fq(-0.22, 0.22, Y0 - 0.123, 0.6, 1.22, 'crimD')
    k.cyl(0.0, Y0 - 0.2, 0.62, 0.08, 0.08, 0.5, 'crim', seg=8)
    k.cyl(0.0, Y0 - 0.2, 1.12, 0.03, 0.03, 0.1, 'black', seg=6)
    k.bx(-0.1, 0.1, Y0 - 0.06, Y0, 1.75, 1.95, 'crim', cull='k')
    k.fq(-0.06, 0.06, Y0 - 0.063, 1.79, 1.91, 'paper')


def menu_board(k):
    k.bx(-0.48, 0.48, Y0 - 0.04, Y0, 2.05, 2.85, 'black', cull='k')
    y = Y0 - 0.044
    k.text('MENU', 0.0, y - 0.003, 2.7, 0.1, 'foodY', font='display')
    for j, z in enumerate((2.52, 2.4, 2.28, 2.16)):
        k.fq(-0.4, 0.15, y - 0.003, z, z + 0.035, 'paper')
        k.fq(0.26, 0.4, y - 0.003, z, z + 0.035, 'foodY')


def door_leaf(word, c, sign_c='paper'):
    """a closed door (1 m cell): frame, leaf, kick plate, a sign plate"""
    def fn(k):
        k.bx(-0.48, 0.48, Y0 - 0.03, Y0, 0.0, 2.3, 'steelD', cull='kb')
        k.fq(-0.42, 0.42, Y0 - 0.034, 0.0, 2.22, c)
        k.fq(-0.42, 0.42, Y0 - 0.038, 0.05, 0.3, 'chrome')
        k.bx(0.28, 0.36, Y0 - 0.09, Y0 - 0.034, 1.0, 1.05, 'chrome')
        k.fq(-0.25, 0.25, Y0 - 0.038, 1.55, 1.8, sign_c)
        k.text(word, 0.0, Y0 - 0.041, 1.63, 0.1, 'black' if sign_c == 'paper' else 'paper', font='display', maxw=0.46)
    return fn


def wc_door(word, part):
    def fn(k):
        if part == 'L':
            door_leaf('', 'steel')(k)
        else:
            k.bx(-0.4, 0.4, Y0 - 0.04, Y0, 1.6, 2.2, 'blueD', cull='k')
            k.text(word, 0.0, Y0 - 0.044, 1.83, 0.22, 'paper', font='display', maxw=0.7)
            k.text('TOILETS', 0.0, Y0 - 0.044, 1.68, 0.07, 'paper', font='cond')
    return fn


def lift(part):
    """lift doors over two cells: brushed steel leaves meeting in the middle, the frame, the call buttons and the
    LIFT indicator on the right"""
    def fn(k):
        y = Y0 - 0.01
        if part == 'L':
            k.bx(-0.5, -0.42, Y0 - 0.06, Y0, 0.0, 2.32, 'steelD', cull='k')
            k.bx(-0.42, 0.5, Y0 - 0.04, Y0, 2.2, 2.32, 'steelD', cull='k')
            k.fq(-0.42, 0.5, y, 0.0, 2.2, 'chrome')
            k.fq(0.47, 0.5, y - 0.004, 0.0, 2.2, 'black')
        else:
            k.bx(0.42, 0.5, Y0 - 0.06, Y0, 0.0, 2.32, 'steelD', cull='k')
            k.bx(-0.5, 0.42, Y0 - 0.04, Y0, 2.2, 2.32, 'steelD', cull='k')
            k.fq(-0.5, 0.42, y, 0.0, 2.2, 'chrome')
            k.fq(-0.5, -0.47, y - 0.004, 0.0, 2.2, 'black')
            k.fq(0.22, 0.38, y - 0.004, 1.0, 1.3, 'steelD')
            k.fq(0.27, 0.33, y - 0.008, 1.18, 1.24, 'amberL')
            k.bx(-0.3, 0.3, Y0 - 0.03, Y0, 2.38, 2.58, 'black', cull='k')
            k.text('LIFT', 0.0, Y0 - 0.034, 2.42, 0.12, 'amberL', font='display')
    return fn


def tunnel(part):
    """the tunnel mouth over three cells (viewer's left to right): a dark arch over the trackbed, its tiled ring, a
    signal on the left, cable brackets"""
    i = 'LMR'.index(part)
    R, zc = 1.45, 2.15
    pts = [(-R, 0.0)] + [(-R * math.cos(t / 12 * math.pi), zc + R * math.sin(t / 12 * math.pi)) for t in range(13)] + [(R, 0.0)]

    def clip(poly, lo, hi):
        out = poly
        for (sgn, lim) in ((1, lo), (-1, hi)):
            res = []
            n = len(out)
            for j in range(n):
                a, b = out[j], out[(j + 1) % n]
                ina, inb = sgn * (a[0] - lim) >= 0, sgn * (b[0] - lim) >= 0
                if ina:
                    res.append(a)
                if ina != inb:
                    t = (lim - a[0]) / (b[0] - a[0])
                    res.append((lim, a[1] + (b[1] - a[1]) * t))
            out = res
        return out

    def fn(k):
        lo, hi = i - 1.5, i - 0.5
        ring = [(-R - 0.18, 0.0)] + [(-(R + 0.18) * math.cos(t / 12 * math.pi), zc + (R + 0.18) * math.sin(t / 12 * math.pi)) for t in range(13)] + [((R + 0.18), 0.0)]
        for poly, c, d in ((ring, 'granite', 0.01), (pts, 'dark', 0.014)):
            p2 = clip(poly, lo, hi)
            if len(p2) >= 3:
                k.poly([(x - (i - 1), Y0 - d, z) for (x, z) in p2], c, (0, -1, 0))
        if part == 'L':
            k.bx(-0.4, -0.22, Y0 - 0.16, Y0 - 0.014, 1.9, 2.5, 'black')
            for z, c in ((2.36, 'crim'), (2.2, 'leaf'), (2.04, 'amberL')):
                k.fq(-0.35, -0.27, Y0 - 0.163, z - 0.04, z + 0.04, c)
        if part == 'M':
            k.bx(-0.3, 0.3, Y0 - 0.04, Y0, 3.85, 4.15, 'tileW', cull='k')
            k.text('NO ENTRY', 0.0, Y0 - 0.044, 3.92, 0.12, 'crim', font='display')
    return fn


def end_sign(k):
    k.bx(-0.45, 0.45, Y0 - 0.04, Y0, 1.6, 2.1, 'crim', cull='k')
    k.text('END OF PLATFORM', 0.0, Y0 - 0.044, 1.92, 0.08, 'paper', font='display', maxw=0.8)
    k.text('NO ENTRY BEYOND THIS POINT', 0.0, Y0 - 0.044, 1.72, 0.05, 'paper', font='cond', maxw=0.8)
    # the driver's CCTV monitor on a bracket
    k.bx(-0.04, 0.04, Y0 - 0.5, Y0, 2.62, 2.68, 'steelD')
    k.bx(-0.3, 0.3, Y0 - 0.62, Y0 - 0.48, 2.3, 2.75, 'black')
    k.fq(-0.26, 0.26, Y0 - 0.623, 2.34, 2.71, 'screen')


def notice(k):
    k.bx(-0.45, 0.45, Y0 - 0.03, Y0, 1.1, 2.0, 'woodD', cull='k')
    k.fq(-0.41, 0.41, Y0 - 0.034, 1.14, 1.96, 'paintG')
    for (a, b, c0, c1, c) in ((-0.36, -0.06, 1.5, 1.9, 'paper'), (0.0, 0.34, 1.6, 1.92, 'foodY'), (-0.3, 0.02, 1.18, 1.44, 'paper'), (0.08, 0.36, 1.2, 1.5, 'tileW')):
        k.fq(a, b, Y0 - 0.038, c0, c1, c)


def build_art(k, ao):
    for i in range(4):
        faces(k, ao, 'Ad%d' % (i + 1), poster(i))
    for v in range(2):
        for p in 'LMR':
            faces(k, ao, 'Big%s_%s' % ('AB'[v], p), billboard(v, p))
    for p in 'LR':
        faces(k, ao, 'Map_' + p, net_map(p))
    faces(k, ao, 'WayOut', sign_plate('WAY OUT', -0.46, 0.46, 2.45, 2.85, 'black', 'hazard', 0.22, arrow='up'))
    mk = sliced_plate('WAY OUT', 2, 2.5, 3.0, 'black', 'hazard', 0.32)
    for i in range(2):
        faces(k, ao, 'Exit_' + 'LR'[i], mk(i))
    mk = sliced_plate('PLATFORMS 1 - 2', 2, 2.5, 3.0, 'blueD', 'paper', 0.24)
    for i in range(2):
        faces(k, ao, 'Plat_' + 'LR'[i], mk(i))
    faces(k, ao, 'PlatR', sign_plate('PLATFORM 1  CRIMSON LINE', -0.48, 0.48, 2.5, 2.8, 'crim', 'paper', 0.14))
    faces(k, ao, 'PlatB', sign_plate('PLATFORM 2  HARBOUR LINE', -0.48, 0.48, 2.5, 2.8, 'blue', 'paper', 0.14))
    mk = sliced_plate('CENTRAL', 3, 1.55, 2.45, 'tileW', 'blueD', 0.52, rim='blueD')
    for i in range(3):
        faces(k, ao, 'Name_' + 'LMR'[i], mk(i))
    faces(k, ao, 'Clock', clock)
    faces(k, ao, 'FirePt', fire_point)
    faces(k, ao, 'Menu', menu_board)
    faces(k, ao, 'StaffDoor', door_leaf('STAFF ONLY', 'steelD', 'crim'))
    for w in ('WOMEN', 'MEN'):
        for p in 'LR':
            faces(k, ao, 'WC%s_%s' % (w[0], p), wc_door(w, p))
    for p in 'LR':
        faces(k, ao, 'Lift_' + p, lift(p))
    for p in 'LMR':
        faces(k, ao, 'Tun_' + p, tunnel(p))
    faces(k, ao, 'EndSign', end_sign)
    faces(k, ao, 'Notice', notice)


# ================================================================ through pieces: shop windows, ticket windows
def shop_window(part):
    """a shopfront bay through the 1 m wall: granite stall riser, a dark steel frame, glass 0.45 - 2.6 m (a companion
    near the hall face), the hall's tiles above; the shop side plain"""
    def fn(k):
        xa = -0.42 if part == 'L' else -0.5
        xb = 0.42 if part == 'R' else 0.5
        paint(k, 'H', 2.75, WALL_H, joints=False)
        k.fq(-0.5, 0.5, Y0, 0.0, 0.45, 'granite')
        if part == 'L':
            k.fq(-0.5, -0.42, Y0, 0.45, 2.75, 'graph')
        if part == 'R':
            k.fq(0.42, 0.5, Y0, 0.45, 2.75, 'graph')
        ea = -0.49 if part == 'L' else -0.5
        eb = 0.49 if part == 'R' else 0.5
        k.bx(ea, eb, Y0 - 0.06, Y0 + 0.08, 2.6, 2.75, 'graph', cull='k')
        k.bx(ea, eb, Y0 - 0.04, Y0 + 0.1, 0.42, 0.47, 'graph', cull='b')
        if part == 'M' or part == 'R':
            k.bx(-0.52, -0.48, Y0 - 0.02, Y0 + 0.06, 0.47, 2.6, 'graph') if part == 'M' else None
        k.uq(xa, xb, Y0 + 0.1, 0.5, 0.47, 'woodL')            # display sill inside
        k.dq(xa, xb, Y0 + 0.08, 0.5, 2.6, 'paintL')
        if part == 'L':
            k.rq(xa, Y0 + 0.08, 0.5, 0.47, 2.6, 'paintL')
        if part == 'R':
            k.lq(xb, Y0 + 0.08, 0.5, 0.47, 2.6, 'paintL')
        # the shop side: plain paint, a low display shelf
        k.push(0, 0, 180)
        k.fq(-0.5, 0.5, Y0, 0.0, 0.47, 'graph')
        k.fq(-0.5, 0.5, Y0, 2.6, WALL_H, 'paintL')
        k.pop()
    return fn


def shop_glass(k):
    k.fq(-0.5, 0.5, Y0 + 0.04, 0.47, 2.6, 'tealD')


def ticket_window(part):
    """the ticket office's counter windows through the hall wall: a granite counter, glass with a speech grille and a
    tray, the TICKETS fascia; the office side painted"""
    def fn(k):
        xa = -0.42 if part == 'L' else -0.5
        xb = 0.42 if part == 'R' else 0.5
        paint(k, 'H', 0.0, 0.95, joints=False)
        paint(k, 'H', 2.75, WALL_H, joints=False)
        if part == 'L':
            k.fq(-0.5, -0.42, Y0, 0.95, 2.75, 'tileC')
        if part == 'R':
            k.fq(0.42, 0.5, Y0, 0.95, 2.75, 'tileC')
        k.bx(-0.5, 0.5, Y0 - 0.25, Y0 + 0.3, 0.95, 1.02, 'granite', cull='b')
        k.dq(xa, xb, Y0, 0.5, 2.4, 'paintL')
        if part == 'L':
            k.rq(xa, Y0, 0.5, 1.02, 2.4, 'paintL')
        if part == 'R':
            k.lq(xb, Y0, 0.5, 1.02, 2.4, 'paintL')
        k.bx(-0.5, 0.5, Y0 + 0.24, Y0 + 0.3, 2.3, 2.4, 'steelD', ink=False)
        k.bx(-0.5, 0.5, Y0 + 0.24, Y0 + 0.3, 1.02, 1.08, 'steelD', ink=False)
        if part == 'M':
            k.bx(-0.48, -0.44, Y0 + 0.22, Y0 + 0.32, 1.08, 2.3, 'steelD', ink=False)
        k.bx(-0.45, 0.45, Y0 - 0.08, Y0, 2.45, 2.75, 'blueD', cull='k')
        if part != 'R':
            k.text('TICKETS', 0.0, Y0 - 0.084, 2.52, 0.16, 'paper', font='display')
        else:
            k.text('INFORMATION', 0.0, Y0 - 0.084, 2.54, 0.12, 'paper', font='display', maxw=0.8)
        k.push(0, 0, 180)
        paint(k, 'O', 0.0, 1.02, joints=False)
        paint(k, 'O', 2.4, 4.0, joints=False)
        k.bx(-0.5, 0.5, Y0 - 0.25, Y0, 0.88, 0.95, 'woodL', cull='')
        k.pop()
    return fn


def ticket_glass(k):
    k.fq(-0.5, 0.5, Y0 + 0.235, 1.08, 2.3, 'tealD')
    k.fq(-0.12, 0.12, Y0 + 0.231, 1.45, 1.6, 'steel')


def build_through(k, ao):
    for p in 'LMR':
        faces(k, ao, 'SW_' + p, shop_window(p))
        faces(k, ao, 'TW_' + p, ticket_window(p))
    faces(k, ao, 'SW_Glass', shop_glass)
    faces(k, ao, 'TW_Glass', ticket_glass)


# ================================================================ sunk side faces (hang from the higher cell's floor)
def edge(trim):
    """a platform edge over the trackbed (0.9 m): concrete face with the refuge recess under the lip, the coping lip
    6 cm proud (stopping 6 cm short of both ends: two edges meeting in a corner never overlap), on top the coping
    band and the yellow line (trimmed at the right end, R, where the cell also drops away on that side);
    trim 'P': the plain face beside the trackbed steps (no lip, no bands: the steps land flush)"""
    def fn(k):
        D = TRACK_D
        k.fq(-0.5, 0.5, Y0, -D, -D + 0.12, 'concD')
        k.fq(-0.5, 0.5, Y0, -D + 0.12, -0.42, 'conc')
        if trim == 'P':
            k.fq(-0.5, 0.5, Y0, -0.42, 0.0, 'conc')
            return
        k.fq(-0.5, 0.5, Y0 - 0.003, -0.4, -0.16, 'dark')
        k.fq(-0.5, 0.5, Y0, -0.42, -0.4, 'conc')
        k.fq(-0.5, 0.5, Y0, -0.16, 0.0, 'stone')
        k.bx(-0.44, 0.44, Y0 - 0.06, Y0 - 0.004, -0.16, 0.0, 'stone', cull='k')
        a = -0.5
        b = 0.5 - (0.38 if 'R' in trim else 0.0)
        k.uq(a, b, Y0 - 0.0, Y0 + 0.26, 0.012, 'stone')
        k.uq(a, b, Y0 + 0.26, Y0 + 0.36, 0.012, 'hazard')
        for x in (-0.25, 0.25):
            k.fq(x - 0.06, x + 0.06, Y0 - 0.004, -D + 0.14, -D + 0.22, 'steelD')   # cable brackets
    return fn


def tunnel_base(k):
    k.fq(-0.5, 0.5, Y0, -TRACK_D, 0.0, 'dark')


def wall_base(k):
    sub_wall(k, 'R', TRACK_D)


def well(kind, part=None):
    def fn(k):
        sub_wall(k, 'H', WELL_D)
        k.uq(-0.5, 0.5, Y0, Y0 + 0.22, 0.012, 'granite')
        if kind == 'ad':
            k.push(0, 0, 0, z=-WELL_D)
            poster(1 if part == 1 else 3)(k)
            k.pop()
        elif kind == 'map':
            k.push(0, 0, 0, z=-WELL_D)
            sign_plate('PLATFORMS 3 - 4  CLOSED', -0.46, 0.46, 2.4, 2.75, 'crim', 'paper', 0.12)(k)
            k.pop()
        elif kind == 'name':
            k.push(0, 0, 0, z=-WELL_D)
            sliced_plate('CENTRAL', 3, 1.55, 2.45, 'tileW', 'blueD', 0.52, rim='blueD')(part)(k)
            k.pop()
        elif kind == 'shut':
            # a closed roll-down shutter in a steel frame (0 - 3 m over the lower landing), the sign over it
            zb = -WELL_D
            x0 = -0.42 if part == 0 else -0.5
            x1 = 0.42 if part == 2 else 0.5
            k.fq(x0, x1, Y0 - 0.008, zb, zb + 3.0, 'steel')
            for j in range(10):
                z = zb + 0.15 + j * 0.28
                k.fq(x0, x1, Y0 - 0.012, z, z + 0.04, 'steelD')
            if part == 0:
                k.bx(-0.5, -0.42, Y0 - 0.08, Y0, zb, zb + 3.0, 'graph', cull='k')
            if part == 2:
                k.bx(0.42, 0.5, Y0 - 0.08, Y0, zb, zb + 3.0, 'graph', cull='k')
            k.bx(-0.5, 0.5, Y0 - 0.2, Y0, zb + 3.0, zb + 3.3, 'graph', cull='k')
            if part == 1:
                k.bx(-0.48, 0.48, Y0 - 0.05, Y0, zb + 1.4, zb + 1.9, 'crim', cull='k')
                k.text('CLOSED', 0.0, Y0 - 0.054, zb + 1.58, 0.2, 'paper', font='display')
            k.bx(-0.48, 0.48, Y0 - 0.05, Y0, zb + 3.4, zb + 3.8, 'blueD', cull='k')
            ib_text.draw(k, 'PLATFORMS 3 - 4', 1.0 - part, Y0 - 0.054, zb + 3.6, 0.22, 'paper', face='y-', font='display', maxw=2.6,
                         clip=(part - 1.5, part - 0.5), valign='m')
    return fn


def build_sunk(k, ao):
    for t in ('', 'R', 'P'):
        faces(k, ao, 'Edge' + t, edge(t))
    faces(k, ao, 'TunBase', tunnel_base)
    faces(k, ao, 'WallBase', wall_base)
    faces(k, ao, 'WellWall', well('plain'))
    faces(k, ao, 'WellAd', well('ad', 1))
    faces(k, ao, 'WellAd2', well('ad', 2))
    faces(k, ao, 'WellMap', well('map'))
    for i in range(3):
        faces(k, ao, 'WellN_' + 'LMR'[i], well('name', i))
        faces(k, ao, 'WellSh_' + 'LMR'[i], well('shut', i))


# ================================================================ doorways, headers
def header(k, x0, x1, z0, front='E', back='O', z1=WALL_H):
    paint(k, front, z0, z1, x0, x1, joints=False)
    k.push(0, 0, 180)
    paint(k, back, z0, z1, -x1, -x0, joints=False)
    k.pop()
    k.dq(x0, x1, -0.5, 0.5, z0, 'stone')


def build_doors(k, ao):
    H = DOOR_H
    # shop / office doorway [2, 1]: a dark steel frame, the sliding glass leaves parked behind fixed side panels
    k.begin()
    header(k, -1.0, 1.0, H, 'H', 'O')
    for s in (-1, 1):
        x = s * 1.0
        k.qx(-0.5, 0.5, 0.0, H, x, -s, 'graph')
        a, b = sorted((x, x - s * 0.08))
        k.bx(a, b, -0.08, 0.08, 0.0, H - 0.12, 'graph', cull='b')
        a, b = sorted((s * 0.92, s * 0.5))
        k.bx(a, b, -0.03, 0.03, 0.02, H - 0.05, 'steelD')
        k.bx(a, b, -0.12, -0.06, 0.02, H - 0.05, 'chrome', ink=False)
    k.bx(-1.0, 1.0, -0.1, 0.1, H - 0.12, H, 'graph', cull='t')
    k.finish('Door2', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.fq(min(s * 0.52, s * 0.88), max(s * 0.52, s * 0.88), -0.061, 0.1, H - 0.15, 'tealD')
    k.finish('Door2_Glow')
    # kiosk front [3, 1]: the shutter rolled up into its box, the kiosk's own counter fascia over it
    k.begin()
    header(k, -1.5, 1.5, H + 0.25, 'H', 'K')
    for s in (-1, 1):
        x = s * 1.5
        k.qx(-0.5, 0.5, 0.0, H + 0.25, x, -s, 'graph')
    k.bx(-1.5, 1.5, -0.35, 0.05, H, H + 0.25, 'steelD', cull='t')
    for j in range(3):
        k.fq(-1.48, 1.48, -0.353, H + 0.04 + j * 0.07, H + 0.07 + j * 0.07, 'steel')
    k.finish('Front3', ao=ao)
    # archway header (1 cell): stone from ARCH_H, a tiled archivolt band at the soffit
    k.begin()
    for s in (0, 180):
        k.push(0, 0, s)
        k.fq(-0.5, 0.5, Y0, ARCH_H, ARCH_H + 0.32, 'tileW')
        k.fq(-0.5, 0.5, Y0 - 0.004, ARCH_H + 0.32, ARCH_H + 0.4, 'granite')
        k.fq(-0.5, 0.5, Y0, ARCH_H + 0.4, WALL_H, 'stone')
        k.pop()
    k.dq(-0.5, 0.5, -0.5, 0.5, ARCH_H, 'tileW')
    k.finish('Header', ao=ao)


# ================================================================ the gate, trail walls, hatch, weapon stand
def build_gate(k, ao):
    """a steel portal 5 m wide (the gate and one cell either side): pylons with tiled sides, a lit box sign over the
    opening on both faces, the wall over it to 8 m"""
    k.begin()
    for s in (-1, 1):
        k.qx(-0.5, 0.5, 0.0, WALL_H, s * 2.5, -s, 'stone')
        a, b = sorted((s * 1.5, s * 2.5))
        for side in (-1, 1):
            k.qy(a, b, 0.0, 0.15, side * 0.5, side, 'granite')
            k.qy(a, b, 0.15, 3.6, side * 0.5, side, 'tileW')
            k.qy(a, b, 3.6, WALL_H, side * 0.5, side, 'stone')
            k.qy(a, b, 1.1, 1.16, side * 0.503, side, 'mustard')
        k.qx(-0.5, 0.5, 0.0, 3.25, s * 1.5, -s, 'steelD')
    k.bx(-1.5, 1.5, -0.5, 0.5, 3.25, 3.6, 'steelD', cull='')
    for side in (-1, 1):
        k.qy(-1.5, 1.5, 3.6, WALL_H, side * 0.5, side, 'stone')
        k.push(0, 0, 0 if side < 0 else 180)
        k.bx(-1.3, 1.3, -0.72, -0.5, 3.62, 4.12, 'black')
        k.roundel(-0.95, -0.723, 3.87, 0.2, face=-1)
        k.pop()
    k.finish('GateFrame', ao=ao)
    k.begin()
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        k.fq(-0.62, 1.25, -0.724, 3.68, 4.06, 'black')
        k.text('PLATFORMS  WAY OUT', 0.3, -0.728, 3.87, 0.18, 'hazard', font='display', maxw=1.8, valign='m')
        k.pop()
    k.finish('GateFrame_Glow')
    k.begin()
    Hs, n = 3.05, 12
    for i in range(n):
        z = 0.1 + i * (Hs - 0.1) / n
        k.bx(-1.5, 1.5, -0.05, 0.05, z + 0.005, z + (Hs - 0.1) / n - 0.005, 'steel' if i % 2 else 'chrome', ink=False)
    k.bx(-1.5, 1.5, -0.06, 0.06, 0.0, 0.1, 'steelD', ink=False)
    k.fq(-0.55, 0.55, -0.063, 1.45, 1.8, 'crim')
    k.text('STATION CLOSED', 0.0, -0.066, 1.55, 0.14, 'paper', font='display', maxw=1.0)
    obj = k.finish('GateShutter')
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)

    # trail walls: the connecting tunnel (1 m along Blender Y, the corridor face +X at x 0.25, 3.6 m to its ceiling)
    def tw(k, art=None):
        def q(a, b, c, d=0.0):
            k.rq(0.25 + d, -0.5, 0.5, a, b, c)
        q(0.0, 0.15, 'granite'); q(0.15, 1.1, 'green'); q(1.1, 1.16, 'tileW'); q(1.16, 3.2, 'tileW'); q(3.2, 3.48, 'green'); q(3.48, 3.6, 'tileW')
        for z in (1.8, 2.5):
            k.rq(0.253, -0.5, 0.5, z - 0.008, z + 0.008, 'grout')
        if art == 'ad':
            k.bx(0.25, 0.28, -0.42, 0.42, 1.2, 2.7, 'steelD', cull='l')
            k.rq(0.283, -0.38, 0.38, 1.24, 2.66, 'scrB')
            k.rq(0.286, -0.38, 0.38, 1.24, 1.5, 'blueD')
            k.text('SKYLARK', 0.287, 0.0, 2.3, 0.18, 'paper', face='x+', font='display', maxw=0.68)
        if art == 'sign':
            k.bx(0.25, 0.3, -0.48, 0.48, 2.45, 2.85, 'blueD', cull='l')
            k.text('PLATFORMS', 0.304, 0.0, 2.6, 0.16, 'paper', face='x+', font='display', maxw=0.86)
    for name, art in (('TrailWall', None), ('TrailWall_B', 'ad'), ('TrailWall_C', 'sign')):
        k.begin()
        tw(k, art)
        k.finish(name, ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 1.2, 1.15, 0.1, 'steelD', seg=20)
    k.ring(0, 0, 0.103, 0.92, 1.1, 'mustard', seg=20)
    for j in range(-3, 4):
        k.uq(-0.6, 0.6, j * 0.2 - 0.03, j * 0.2 + 0.03, 0.106, 'steel')
    k.finish('Hatch', ao=ao)
    # weapon stand: a station's lost-property trolley
    k.begin()
    k.bx(-0.45, 0.45, -0.25, 0.25, 0.12, 0.75, 'blueD', cull='b')
    k.fq(-0.4, 0.4, -0.253, 0.5, 0.68, 'paper')
    k.fq(-0.3, 0.3, -0.256, 0.56, 0.62, 'blueD')
    k.bx(-0.45, 0.45, -0.25, 0.25, 0.86, 0.9, 'steel')
    for (x, y) in ((-0.38, -0.2), (0.38, -0.2), (-0.38, 0.2), (0.38, 0.2)):
        k.cyl(x - 0.02, y, 0.06, 0.06, 0.06, 0.04, 'black', seg=6, rot=(0, 90, 0))
        k.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0.06, 0.12, 'steelD', ink=False)
    k.finish('Stand', ao=ao)


# ================================================================ ceilings (layer 4)
def build_ceilings(k, ao):
    def tbar(k, x0, x1, y0, y1, mid=False):
        k.dq(x0, x1, y0, y0 + 0.03, -0.004, 'steelD')
        k.dq(x0, x0 + 0.03, y0 + 0.03, y1, -0.004, 'steelD')
        if mid:
            k.dq(x0 + 0.03, x1, -0.015, 0.015, -0.004, 'steelD')
    k.begin(); k.dq(-0.5, 0.5, -0.5, 0.5, 0.0, 'paintL'); tbar(k, -0.5, 0.5, -0.5, 0.5); k.finish('C_Tile')
    k.begin(); k.dq(-0.5, 0.5, -0.5, 0.5, 0.0, 'paintL'); tbar(k, -0.5, 0.5, -0.5, 0.5); k.dq(-0.3, 0.3, -0.4, 0.4, -0.006, 'steel'); k.finish('C_Light')
    k.begin(); k.dq(-0.27, 0.27, -0.37, 0.37, -0.009, 'lightW'); k.finish('C_Light_Glow')
    k.begin(); k.dq(-0.3, 0.3, -0.6, 0.6, -0.004, 'steel'); k.dq(-0.26, 0.26, -0.56, 0.56, -0.008, 'lightW'); k.finish('C_TrailLight')
    k.begin(); k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'paintL'); tbar(k, -1.0, 1.0, -1.0, 1.0, mid=True); k.finish('C_Tile2')
    k.begin(); k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'paintL'); tbar(k, -1.0, 1.0, -1.0, 1.0, mid=True)
    k.bx(-0.62, 0.62, -0.18, 0.18, -0.06, -0.006, 'steel', cull='t', ink=False); k.finish('C_Light2')
    k.begin(); k.dq(-0.58, 0.58, -0.14, 0.14, -0.064, 'lightW'); k.finish('C_Light2_Glow')


# ================================================================ the vaults (layer 8)
def arc(span, rise, n):
    """points (u, z) of a segmental arch from -span/2 to span/2 rising `rise`"""
    c = span / 2.0
    R = (c * c + rise * rise) / (2 * rise)
    zc = rise - R
    a = math.asin(c / R)
    return [(R * math.sin(-a + 2 * a * i / n), zc + R * math.cos(-a + 2 * a * i / n)) for i in range(n + 1)], R, zc


def vault(k, span, rise, n, depth, along_x, ribs=True, cols=('cream', 'tileC')):
    """a barrel vault bay: the inner surface (facing down / inward), a rib across the middle of the bay, the
    springing ledges; along_x: the span runs along Blender X (bay along Y) else along Y"""
    pts, R, zc = arc(span, rise, n)
    d = depth / 2.0
    for i in range(n):
        (u0, z0), (u1, z1) = pts[i], pts[i + 1]
        c = cols[(i // 2) % 2]
        nu, nz = -(u0 + u1) / 2, -(zc - (z0 + z1) / 2)
        L = math.hypot(nu, nz)
        if along_x:
            k.poly([(u0, -d, z0), (u1, -d, z1), (u1, d, z1), (u0, d, z0)], c, (nu / L, 0, (zc - (z0 + z1) / 2) / L))
        else:
            k.poly([(-d, u0, z0), (-d, u1, z1), (d, u1, z1), (d, u0, z0)], c, (0, nu / L, (zc - (z0 + z1) / 2) / L))
    if ribs:
        t, h = 0.16, 0.28
        def inward(u, z, sft):
            L = math.hypot(u, z - zc)
            return (u - u / L * sft, z - (z - zc) / L * sft)
        def P(u, z, w):
            return (u, w, z) if along_x else (w, u, z)
        for i in range(n):
            (u0, z0), (u1, z1) = pts[i], pts[i + 1]
            a0, a1 = inward(u0, z0, 0.0), inward(u1, z1, 0.0)
            b0, b1 = inward(u0, z0, h), inward(u1, z1, h)
            # the rib's soffit (toward the arch centre) and its two sides
            mu, mz = (b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2
            nrm = (-mu, zc - mz)
            k.poly([P(b0[0], b0[1], -t / 2), P(b1[0], b1[1], -t / 2), P(b1[0], b1[1], t / 2), P(b0[0], b0[1], t / 2)], 'stoneD',
                   (nrm[0], 0, nrm[1]) if along_x else (0, nrm[0], nrm[1]))
            for sg in (-1, 1):
                k.poly([P(a0[0], a0[1], sg * t / 2), P(a1[0], a1[1], sg * t / 2), P(b1[0], b1[1], sg * t / 2), P(b0[0], b0[1], sg * t / 2)], 'stone',
                       (0, sg, 0) if along_x else (sg, 0, 0))
    # springing ledges along both sides
    for s in (-1, 1):
        u = s * span / 2
        a, b = sorted((u - s * 0.5, u - s * 0.9))   # on the wall's face (0.5 in from its centre line)
        if along_x:
            k.bx(a, b, -d, d, -0.3, 0.0, 'stoneD', cull='t')
        else:
            k.bx(-d, d, a, b, -0.3, 0.0, 'stoneD', cull='t')
    return pts, R, zc


def arc_band(k, pts, zc, w, y, c):
    """a flat band w wide just inside an arch's curve, on the plane y facing -Y"""
    def inward(u, z):
        L = math.hypot(u, z - zc)
        return (u - u / L * w, z - (z - zc) / L * w)
    for (u0, z0), (u1, z1) in zip(pts, pts[1:]):
        a, b = inward(u0, z0), inward(u1, z1)
        k.poly([(u0, y, z0), (u1, y, z1), (b[0], y, b[1]), (a[0], y, a[1])], c, (0, -1, 0))


def build_vaults(k, ao):
    # ---- the ticket hall: span 45 m (wall centre to wall centre), rise 5 m, bays 2 m along Blender Y
    SH, RH, NH = 45.0, 5.0, 22
    k.begin(); vault(k, SH, RH, NH, 2.0, True); k.finish('VaultH')
    k.begin()
    pts, R, zc = vault(k, SH, RH, NH, 2.0, True)
    for x in (-12.0, 12.0):
        zt = zc + math.sqrt(R * R - x * x)
        k.cyl(x, 0, -2.4, 0.012, 0.012, zt + 2.4 + 0.2, 'black', seg=4, ink=False, caps=False)
        k.cyl(x, 0, -2.55, 0.55, 0.22, 0.32, 'graph', seg=10, caps=False)
        k.cyl(x, 0, -2.6, 0.56, 0.56, 0.05, 'mustard', seg=10, ink=False, caps=False)
    k.finish('VaultHL')
    k.begin()
    for x in (-12.0, 12.0):
        k.poly([(x + math.cos(-a / 10 * 6.283) * 0.5, math.sin(-a / 10 * 6.283) * 0.5, -2.56) for a in range(10)], 'lightW', (0, 0, -1))
    k.finish('VaultHL_Glow')
    # end walls [44, 1] (layer 8 over the end wall row; the face at y -0.5 toward the hall)
    for name in ('VEndN', 'VEndS'):
        k.begin()
        pts, R, zc = arc(SH, RH, NH)
        k.poly([(u, -0.5, z) for (u, z) in pts], 'stone', (0, -1, 0))
        arc_band(k, pts, zc, 0.35, -0.506, 'stoneD')
        if name == 'VEndN':
            k.bx(-9.0, 9.0, -0.6, -0.5, 1.2, 3.2, 'blueD', cull='k')
            k.text('METRO CENTRAL', 1.0, -0.604, 1.75, 1.0, 'paper', font='display', maxw=13.5)
            k.roundel(-7.2, -0.604, 2.2, 0.85, face=-1)
        else:
            k.cyl(0, -0.52, 2.4, 1.3, 1.3, 0.12, 'black', seg=24, rot=(90, 0, 0))
            y = -0.645
            k.poly([(math.cos(a / 24 * 6.283) * 1.18, y, 2.4 + math.sin(a / 24 * 6.283) * 1.18) for a in range(24)], 'paper', (0, -1, 0))
            for h in range(12):
                a = h / 12 * 6.283
                k.fq(math.sin(a) * 1.0 - 0.04, math.sin(a) * 1.0 + 0.04, y - 0.004, 2.4 + math.cos(a) * 1.0 - 0.09, 2.4 + math.cos(a) * 1.0 + 0.09, 'black')
            k.poly([(-0.05, y - 0.008, 2.4), (0.05, y - 0.008, 2.4), (0.45, y - 0.008, 3.05), (0.38, y - 0.008, 3.1)], 'black', (0, -1, 0))
            k.poly([(-0.035, y - 0.012, 2.35), (0.035, y - 0.012, 2.35), (0.035, y - 0.012, 3.3), (-0.035, y - 0.012, 3.3)], 'black', (0, -1, 0))
            for s in (-1, 1):
                k.bx(s * 5.5 - 2.5, s * 5.5 + 2.5, -0.6, -0.5, 1.0, 2.2, 'black', cull='k')
                k.text('WAY OUT', s * 5.5, -0.604, 1.35, 0.7, 'hazard', font='display', maxw=4.6)
        k.finish(name, ao=ao)
    # ---- the platform hall: span 33 m along Blender Y, rise 4.5 m, bays 2 m along X
    SP, RP, NP = 33.0, 4.5, 18
    k.begin(); vault(k, SP, RP, NP, 2.0, False, cols=('tileW', 'cream')); k.finish('VaultP')
    k.begin()
    pts, R, zc = vault(k, SP, RP, NP, 2.0, False, cols=('tileW', 'cream'))
    for y in (12.5, 0.0, -12.5):
        zt = zc + math.sqrt(R * R - y * y)
        for x in (-0.7, 0.7):
            k.cyl(x, y, -4.0, 0.012, 0.012, zt + 4.0 + 0.2, 'black', seg=4, ink=False, caps=False)
        k.bx(-0.95, 0.95, y - 0.16, y + 0.16, -4.12, -3.98, 'graph')
    k.finish('VaultPL')
    k.begin()
    for y in (12.5, 0.0, -12.5):
        k.dq(-0.9, 0.9, y - 0.11, y + 0.11, -4.124, 'lightW')
    k.finish('VaultPL_Glow')
    k.begin()   # the platform hall's end wall [1, 32] over the tunnel wall, its face at y -0.5 (toward the platforms)
    pts, R, zc = arc(SP, RP, NP)
    k.push(0, 0, 90)
    k.poly([(u, -0.5, z) for (u, z) in pts], 'stone', (0, -1, 0))
    arc_band(k, pts, zc, 0.35, -0.506, 'stoneD')
    k.bx(-4.0, 4.0, -0.6, -0.5, 0.6, 2.4, 'tileW', cull='k')
    k.text('CENTRAL', 0.0, -0.604, 1.1, 0.95, 'blueD', font='display', maxw=7.4)
    k.pop()
    k.finish('PEnd', ao=ao)


# ================================================================ floor mosaic (layer 0.006)
def build_floors(k, ao):
    k.begin()
    k.uq(-4.0, 4.0, -4.0, 4.0, 0.0, 'terrD')
    k.ring(0, 0, 0.003, 2.2, 3.4, 'crim', seg=28)
    k.uq(-3.9, 3.9, -0.6, 0.6, 0.006, 'blue')
    k.text('METRO CENTRAL', 0.0, 0.0, 0.009, 0.62, 'paper', face='up', font='display', maxw=6.8, valign='m')
    for a in range(8):
        t = a / 8 * 6.283
        k.poly([(math.cos(t) * 3.55, math.sin(t) * 3.55, 0.003), (math.cos(t + 0.12) * 3.85, math.sin(t + 0.12) * 3.85, 0.003),
                (math.cos(t) * 3.95, math.sin(t) * 3.95, 0.003), (math.cos(t - 0.12) * 3.85, math.sin(t - 0.12) * 3.85, 0.003)], 'mustard', (0, 0, 1))
    k.finish('F_Mosaic')


# ================================================================ stairs, escalators, steps
def rail_line(k, pts, t, c, ink=True):
    """a handrail along a polyline: segments alternate 8 mm in thickness so their sides never lie in one plane"""
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k.beam(a, b, t + (0.008 if i % 2 else 0.0), c, ink=ink)


def treads(k, along, w0, w1, s0, step, n, rise, c, nose, riser, nw=0.05, walk=True):
    """n flat treads (no outline: the stringers carry it) stepping from s0 by `step` (signed) along Blender `along`,
    w0..w1 across, each a nosing strip, the tread and its riser; walkable boxes solid to the floor"""
    for i in range(n):
        top = (i + 1) * rise
        a = s0 + i * step
        b = a + step
        lo, hi = sorted((a, b))
        if step > 0:
            nlo, nhi, rlo, rhi = a, a + nw, a + nw, b
        else:
            nlo, nhi, rlo, rhi = a - nw, a, b, a - nw
        if along == 'y':
            k.uq(w0, w1, nlo, nhi, top, nose)
            k.uq(w0, w1, rlo, rhi, top, c)
            (k.bq if step < 0 else k.fq)(w0, w1, a, top - rise, top, riser)
            if walk:
                k.wcol(w0, w1, lo, hi, 0.0, top)
        else:
            k.uq(nlo, nhi, w0, w1, top, nose)
            k.uq(rlo, rhi, w0, w1, top, c)
            (k.rq if step < 0 else k.lq)(a, w0, w1, top - rise, top, riser)
            if walk:
                k.wcol(lo, hi, w0, w1, 0.0, top)


def rail_cols(k, x0, x1, ys, zs, h, every=3):
    """stepped collision boxes along a sloped rail: one box per `every` breakpoints (Blender Y), each up to the
    higher end + h"""
    idx = list(range(0, len(ys) - 1, every)) + [len(ys) - 1]
    for a, b in zip(idx, idx[1:]):
        lo, hi = sorted((ys[a], ys[b]))
        if hi - lo > 1e-3:
            k.col(x0, x1, lo, hi, 0.0, max(zs[a:b + 1]) + h)


def build_stairs(k, ao):
    # ---- the well stair [5, 9]: bottom landing at Blender +Y (z 0), 28 treads, the top landing at -Y (z 4.5)
    k.begin()
    n, W, yb, yt = 28, 2.5, 3.5, -3.5
    k.uq(-W, W, yb, 4.5, 0.004, 'terrD')
    treads(k, 'y', -W + 0.1, W - 0.1, yb, -(yb - yt) / n, n, WELL_D / n, 'granite', 'mustard', 'stoneD')
    k.uq(-W + 0.1, W - 0.1, -4.5, yt, WELL_D, 'granite')
    k.wcol(-W + 0.1, W - 0.1, -4.5, yt, 0.0, WELL_D)
    prof = [(4.5, 0.0), (yb, 0.0), (yt, WELL_D), (-4.5, WELL_D)]
    for s in (-1, 1):   # granite stringers close the space under the flight
        xa, xb = sorted((s * W, s * (W - 0.1)))
        k.hullp([(xx, y, z) for xx in (xa, xb) for (y, z) in ((yb, 0.0), (yt, WELL_D - 0.07), (-4.5, WELL_D - 0.07), (-4.5, 0.0))], 'granite')
    ys = [4.45, yb] + [yb - (i + 1) * (yb - yt) / n for i in range(n)] + [-4.45]
    zs = [0.0, 0.0] + [(i + 1) * WELL_D / n for i in range(n)] + [WELL_D]
    for x in (-W + 0.16, 0.0, W - 0.16):
        rail_line(k, [(x, 4.45, 1.05), (x, yb, 1.05), (x, yt, WELL_D + 1.05), (x, -4.45, WELL_D + 1.05)], 0.06, 'steel')
        for t in range(0, 11, 2):
            yy = yb - t * (yb - yt) / 10
            zz = WELL_D * t / 10
            k.bx(x - 0.025, x + 0.025, yy - 0.025, yy + 0.025, zz, zz + 1.05, 'steelD', ink=False, cull='b')
        if x != 0.0:
            for (ya, za, yb2, zb) in ((4.45, 0.0, yb, 0.0), (yb, 0.0, yt, WELL_D), (yt, WELL_D, -4.45, WELL_D)):
                for sg in (-1, 1):
                    k.poly([(x + sg * 0.01, ya, za + 0.1), (x + sg * 0.01, yb2, zb + 0.1), (x + sg * 0.01, yb2, zb + 1.0), (x + sg * 0.01, ya, za + 1.0)], 'glassL', (sg, 0, 0))
        rail_cols(k, x - 0.05, x + 0.05, ys, zs, 1.05)
    k.finish('Stair', ao=ao)

    # ---- the escalator bank [10, 9]: four stopped escalators (1 m steps between glass balustrades, black handrails),
    # stainless interdecks between them, comb plates top and bottom, the truss cladding on the outer sides
    k.begin()
    yb, yt, n = 3.25, -3.25, 30
    rise = WELL_D / n
    k.uq(-5.0, 5.0, yb, 4.5, 0.004, 'steel')
    k.wcol(-5.0, 5.0, yb, 4.5, 0.0, 0.004)
    path = [(4.2, 0.0), (yb, 0.0), (yt, WELL_D), (-4.2, WELL_D)]
    ys = [4.2, yb] + [yb - (i + 1) * (yb - yt) / n for i in range(n)] + [-4.2]
    zs = [0.0, 0.0] + [(i + 1) * rise for i in range(n)] + [WELL_D]
    units = (-3.75, -1.25, 1.25, 3.75)
    for xc in units:
        x0, x1 = xc - 0.5, xc + 0.5
        treads(k, 'y', x0, x1, yb, -(yb - yt) / n, n, rise, 'graph', 'hazard', 'steelD', nw=0.04, walk=False)
        k.uq(x0, x1, -4.5, yt, WELL_D + 0.004, 'steel')
        for s in (-1, 1):
            xg = xc + s * 0.6
            for (ya, za), (yb2, zb) in zip(path, path[1:]):
                k.poly([(xg, ya, za + 0.12), (xg, yb2, zb + 0.12), (xg, yb2, zb + 0.95), (xg, ya, za + 0.95)], 'glass', (-s, 0, 0))
                k.poly([(xc + s * 0.5, ya, za), (xc + s * 0.5, yb2, zb), (xc + s * 0.5, yb2, zb + 0.12), (xc + s * 0.5, ya, za + 0.12)], 'steel', (-s, 0, 0))
            rail_line(k, [(xg, y, z + 1.0) for (y, z) in path], 0.07, 'black')
            k.cyl(xg - 0.04, 4.2, 0.55, 0.45, 0.45, 0.08, 'black', seg=8, rot=(0, 90, 0))
    nw = 26   # walkable: 26 boxes of 0.25 m across the bank (two to a 0.5 m nav cell, 0.35 m rise; the balustrades block the rest)
    for i in range(nw):
        a = yb - i * (yb - yt) / nw
        b = yb - (i + 1) * (yb - yt) / nw
        k.wcol(-4.3, 4.3, b, a, 0.0, (i + 1) * WELL_D / nw)
    k.wcol(-4.3, 4.3, -4.5, yt, 0.0, WELL_D)
    # interdecks between neighbouring units and the outer cladding
    for a, b in ((units[0] + 0.6, units[1] - 0.6), (units[1] + 0.6, units[2] - 0.6), (units[2] + 0.6, units[3] - 0.6)):
        for (ya, za), (yb2, zb) in zip(path, path[1:]):
            k.poly([(a, ya, za + 1.04), (a, yb2, zb + 1.04), (b, yb2, zb + 1.04), (b, ya, za + 1.04)], 'chrome', (0, 0, 1))
        rail_cols(k, a - 0.05, b + 0.05, ys, zs, 1.04)
    for s in (-1, 1):
        xa, xb = sorted((s * (3.75 + 0.66), s * 5.0))
        k.hullp([(xx, y, z) for xx in (xa, xb) for (y, z) in ((4.2, 0.0), (yb, 0.0), (yt, WELL_D), (-4.2, WELL_D), (-4.2, WELL_D + 1.04), (yt, WELL_D + 1.04), (yb, 1.04), (4.2, 1.04))], 'steel')
        rail_cols(k, min(xa, s * 4.3), max(xb, s * 4.3), ys, zs, 1.04)
    k.finish('EscBank', ao=ao)

    # ---- the footbridge stair [8, 2] rising toward Blender +X onto the 4.5 m deck: 28 treads, a 1 m landing
    k.begin()
    n, Wd = 28, 0.85
    treads(k, 'x', -Wd, Wd, -4.0, 7.0 / n, n, 4.5 / n, 'granite', 'mustard', 'stoneD')
    k.uq(3.0, 4.0, -Wd, Wd, 4.5, 'granite')
    k.wcol(3.0, 4.0, -Wd, Wd, 0.0, 4.5)
    xs = [-4.0 + i * 7.0 / n for i in range(n + 1)] + [4.0]
    zz = [(i + 1) * 4.5 / n for i in range(n)] + [4.5, 4.5]
    for s in (-1, 1):
        ya, yb2 = sorted((s * Wd, s * (Wd + 0.12)))
        k.hullp([(x, y, z) for y in (ya, yb2) for (x, z) in ((-4.0, 0.0), (-3.7, 0.0), (3.0, 4.43), (4.0, 4.43), (4.0, 0.0))], 'steelD')
        yr = s * (Wd + 0.06)
        rail_line(k, [(-3.9, yr, 1.05), (3.0, yr, 4.5 + 1.05), (3.98, yr, 4.5 + 1.05)], 0.06, 'steel')
        for t in (0.1, 0.5, 0.9):
            xx = -3.9 + t * 6.9
            k.bx(xx - 0.02, xx + 0.02, yr - 0.02, yr + 0.02, t * 4.5, t * 4.5 + 1.05, 'steel', ink=False, cull='b')
        for j in range(0, len(xs) - 1, 4):
            j2 = min(j + 4, len(xs) - 1)
            k.col(xs[j], xs[j2], ya, yb2, 0.0, max(zz[j:j2]) + 1.05)
    k.finish('BStair', ao=ao)

    # ---- trackbed steps [3, 2]: steel steps up from the trackbed (Blender +Y, z 0) to the platform (-Y, z 0.9)
    k.begin()
    n = 6
    treads(k, 'y', -1.4, 1.4, 1.0, -0.3, n - 1, TRACK_D / n, 'steel', 'hazard', 'steelD')
    k.fq(-1.4, 1.4, -0.5, TRACK_D - TRACK_D / n, TRACK_D, 'steelD')
    k.uq(-1.4, 1.4, -1.0, -0.5, TRACK_D, 'steel')
    k.wcol(-1.4, 1.4, -1.0, -0.5, 0.0, TRACK_D)
    for s in (-1, 1):
        xa, xb = sorted((s * 1.4, s * 1.48))
        k.hullp([(x, y, z) for x in (xa, xb) for (y, z) in ((1.0, 0.0), (1.0, 0.1), (-1.0, TRACK_D), (-1.0, 0.0))], 'steelD')
        xr = s * 1.44
        rail_line(k, [(xr, 1.0, 1.0), (xr, -0.5, TRACK_D + 1.0), (xr, -0.98, TRACK_D + 1.0)], 0.05, 'hazard')
        for y, z in ((0.95, 0.0), (0.2, 0.45), (-0.95, TRACK_D)):
            k.bx(xr - 0.02, xr + 0.02, y - 0.02, y + 0.02, z, z + 1.0, 'steelD', ink=False, cull='b')
        for (a, b, z) in ((1.0, 0.4, 0.3), (0.4, -0.2, 0.6), (-0.2, -1.0, TRACK_D)):
            k.col(xa, xb, b, a, 0.0, z + 1.0)
    k.finish('Steps', ao=ao)


# ================================================================ rails (runs along Blender Y)
def build_rails(k, ao):
    def glass(k, y0, y1):
        k.bx(-0.04, 0.04, y0, y1, 0.0, 0.1, 'steelD', cull='b')
        k.bx(-0.04, 0.04, y0, y1, 1.02, 1.08, 'steel')
        k.qx(y0, y1, 0.1, 1.02, 0.012, 1, 'glassL')
        k.qx(y0, y1, 0.1, 1.02, -0.012, -1, 'glassL')
    k.begin(); glass(k, -0.5, 0.5); k.col(-0.05, 0.05, -0.5, 0.5, 0.0, 1.08); k.finish('GRailFull', ao=ao)
    k.begin(); glass(k, -0.5, -0.04); k.col(-0.05, 0.05, -0.5, 0.0, 0.0, 1.08); k.finish('GRailHalf', ao=ao)
    k.begin(); k.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 1.12, 'steelD', cull='b'); k.finish('GRailPost', ao=ao)

    def mesh(k, y0, y1):
        k.bx(-0.035, 0.035, y0, y1, 1.0, 1.08, 'steelD')
        k.bx(-0.02, 0.02, y0, y1, 0.0, 0.12, 'steelD', cull='b')
        k.qx(y0, y1, 0.12, 1.0, 0.006, 1, 'graph')
        k.qx(y0, y1, 0.12, 1.0, -0.006, -1, 'graph')
        for z in (0.4, 0.7):
            k.bx(-0.015, 0.015, y0, y1, z, z + 0.03, 'steel', ink=False)
    k.begin(); mesh(k, -0.5, 0.5); k.col(-0.05, 0.05, -0.5, 0.5, 0.0, 1.08); k.finish('BRailFull', ao=ao)
    k.begin(); mesh(k, -0.5, -0.04); k.col(-0.05, 0.05, -0.5, 0.0, 0.0, 1.08); k.finish('BRailHalf', ao=ao)
    k.begin(); k.bx(-0.045, 0.045, -0.045, 0.045, 0.0, 1.12, 'steelD', cull='b'); k.finish('BRailPost', ao=ao)


# ================================================================ hanging screens and signs (layer 3.2), fascias (2.9)
def build_hanging(k, ao):
    # departure screen: a double-sided box (front -Y and back +Y) 1.5 x 0.4 m, rods up into the vault
    k.begin()
    k.bx(-0.78, 0.78, -0.09, 0.09, -0.44, 0.0, 'black')
    for x in (-0.5, 0.5):
        k.cyl(x, 0, 0.0, 0.012, 0.012, 9.5, 'black', seg=4, ink=False, caps=False)
    for s in (-1, 1):
        k.qy(-0.72, 0.72, -0.4, -0.04, s * 0.093, s, 'screen')
    k.finish('PID', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.push(0, 0, 0 if s < 0 else 180)
        y = -0.096
        k.text('1  BAYSIDE', -0.66, y, -0.14, 0.07, 'amberL', font='cond', align='l')
        k.text('2 MIN', 0.66, y, -0.14, 0.07, 'amberL', font='cond', align='r')
        k.fq(-0.66, 0.66, y, -0.31, -0.29, 'amberL')
        k.pop()
    k.finish('PID_Glow')
    # hanging direction sign: TRAINS -> on both faces, 3 m wide
    k.begin()
    k.bx(-1.5, 1.5, -0.08, 0.08, -0.5, 0.0, 'blueD')
    for x in (-1.2, 1.2):
        k.cyl(x, 0, 0.0, 0.012, 0.012, 9.5, 'black', seg=4, ink=False, caps=False)
    for s in (-1, 1):
        k.push(0, 0, 0 if s < 0 else 180)
        k.text('TRAINS  PLATFORMS 1 - 2', 0.0, -0.084, -0.25, 0.22, 'paper', font='display', maxw=2.8, valign='m')
        k.pop()
    k.finish('HangSign', ao=ao)
    # shop fascias [7, 1] on the shopfront line (front -Y = the hall): a box sign 7 x 0.55 m with the shop's name
    for name, word, bg, fg, acc in (('SignK', 'SNACKBOX', 'kiosk', 'paper', 'foodY'), ('SignF', 'COGWHEEL COFFEE', 'cafe', 'cream', 'mustard'),
                                    ('SignN', 'PAPERCLIP NEWS', 'blueD', 'paper', 'crim'), ('SignM', 'NIGHTJAR MART', 'mart', 'paper', 'foodY')):
        k.begin()
        k.bx(-3.45, 3.45, -0.68, -0.5, 0.0, 0.55, bg, cull='k')
        k.fq(-3.45, 3.45, -0.683, 0.0, 0.06, acc)
        k.text(word, 0.0, -0.686, 0.29, 0.34, fg, font='display', maxw=6.4, valign='m')
        k.finish(name, ao=ao)


def build_struct(k, ao):
    build_faces(k, ao)
    build_art(k, ao)
    build_through(k, ao)
    build_sunk(k, ao)
    build_doors(k, ao)
    build_gate(k, ao)
    build_ceilings(k, ao)
    build_vaults(k, ao)
    build_floors(k, ao)
    build_stairs(k, ao)
    build_rails(k, ao)
    build_hanging(k, ao)

