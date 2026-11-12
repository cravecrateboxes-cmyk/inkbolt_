"""kit-observatory structure: wall faces (one per finish scheme, a full and an upper-only version for doorways), the
wall art overlays the theme's chooser stacks on them (station and annex windows, doors, vents, wall lamps, star
charts, posters, whiteboards, exit points, clocks), the viewing rooms' full-height glazing (a through piece), the
doorways, the gate, trail walls, the hatch, the weapon stand, parapets, the security fence, deck rails, stairs, steps,
deck posts, ceiling tiles and floor finishes. See ob_base.py for the conventions."""
import math
import random

from ob_base import *  # noqa: F401,F403
import ob_base as B


def faces(k, ao, name, fn, glow=None):
    k.begin()
    fn(k)
    k.finish(name, ao=ao)
    if glow:
        k.begin()
        glow(k)
        k.finish(name + '_Glow')


# ================================================================ wall finishes
# bands from the floor up: (z0, z1, colour); seams: (kind, colour) painted 3 mm proud
SCHEMES = {
    # zone 1: the funicular station (stone plinth, render, larch cladding, dark eave) and the dome annex (white
    # insulated panels with the observatory blue band)
    'S': dict(bands=[(0.0, 0.9, 'stone'), (0.9, 0.98, 'stoneD'), (0.98, 3.9, 'concL'), (3.9, 4.05, 'steelD'),
                     (4.05, 9.3, 'wood'), (9.3, 10.0, 'graph')], seams=('battens', 'woodD', 4.05, 9.3)),
    'A': dict(bands=[(0.0, 0.6, 'concD'), (0.6, 3.4, 'domeW'), (3.4, 3.9, 'blueS'), (3.9, 3.98, 'blueD'),
                     (3.98, 9.5, 'domeW'), (9.5, 10.0, 'steelD')], seams=('panels', 'domeS', 0.6, 9.5)),
    # zone 2: the dome hall (deep blue-grey steel), labs (white panels, blue band), the control room, the lobby
    # (timber and stone), the viewing rooms (charcoal and timber), the service hall (concrete, hazard dado)
    'H': dict(bands=[(0.0, 0.15, 'black'), (0.15, 1.2, 'graph'), (1.2, 1.26, 'yellow'), (1.26, 9.6, 'hallP'),
                     (9.6, 10.0, 'steelD')], seams=('panels', 'navy', 1.26, 9.6)),
    'L': dict(bands=[(0.0, 0.12, 'graph'), (0.12, 1.0, 'panelG'), (1.0, 1.08, 'blueS'), (1.08, 10.0, 'panelW')],
              seams=('panels', 'panelG', 1.08, 4.2)),
    'C': dict(bands=[(0.0, 0.12, 'black'), (0.12, 1.0, 'graph'), (1.0, 1.06, 'scrB'), (1.06, 10.0, 'panelG')],
              seams=('panels', 'steel', 1.06, 4.2)),
    'B': dict(bands=[(0.0, 0.12, 'woodD'), (0.12, 1.1, 'wood'), (1.1, 1.16, 'woodD'), (1.16, 3.0, 'woodL'),
                     (3.0, 3.1, 'woodD'), (3.1, 10.0, 'stoneL')], seams=('battens', 'wood', 1.16, 3.0)),
    'V': dict(bands=[(0.0, 0.12, 'black'), (0.12, 2.6, 'graph'), (2.6, 2.7, 'brass'), (2.7, 10.0, 'woodD')],
              seams=('battens', 'wood', 2.7, 9.0)),
    'M': dict(bands=[(0.0, 0.9, 'yellow'), (0.9, 1.0, 'black'), (1.0, 10.0, 'conc')], seams=('blocks', 'concD', 1.0, 8.0)),
}


def paint(k, sch, z0=0.0, z1=WALL_H, x0=-0.5, x1=0.5, y=Y0):
    S = SCHEMES[sch]
    for (a, b, c) in S['bands']:
        a, b = max(a, z0), min(b, z1)
        if b - a > 1e-4:
            k.fq(x0, x1, y, a, b, c)
    kind, c, s0, s1 = S['seams']
    s0, s1 = max(s0, z0), min(s1, z1)
    if s1 - s0 < 0.05:
        return
    if kind == 'battens':     # vertical boards: two battens a cell
        for x in (-0.25, 0.25):
            if x0 + 0.02 < x < x1 - 0.02:
                k.fq(x - 0.02, x + 0.02, y - 0.003, s0, s1, c)
    elif kind == 'panels':    # insulated panels: a vertical joint per cell, horizontal joints every 1.2 m
        if x0 < 0.0 < x1:
            k.fq(-0.012, 0.012, y - 0.003, s0, s1, c)
        z = s0 + 1.2
        while z < s1 - 0.05:   # interrupted at the vertical joint (same depth, never crossing it)
            for (a, b) in ((x0, -0.012), (0.012, x1)):
                if b - a > 0.01:
                    k.fq(a, b, y - 0.003, z - 0.012, z + 0.012, c)
            z += 1.2
    elif kind == 'blocks':    # concrete block courses
        z = s0 + 0.4
        while z < s1 - 0.05:
            k.fq(x0, x1, y - 0.003, z - 0.01, z + 0.01, c)
            z += 0.4


def build_faces(k, ao):
    for sch in SCHEMES:
        faces(k, ao, 'F' + sch, lambda k, s=sch: paint(k, s))
        faces(k, ao, 'F' + sch + '_U', lambda k, s=sch: paint(k, s, z0=DOOR_H + 0.6))


# ================================================================ art overlays (stacked on a face, no wall paint)
def window(k, z0, z1, frame='graph', glass='glassD', mull=True, sill='steel'):
    """a window set in the face: frame 5 cm proud, dark glazing, a sill"""
    k.fq(-0.42, 0.42, YA, z0, z1, frame)
    k.fq(-0.36, 0.36, YA - 0.004, z0 + 0.06, z1 - 0.06, glass)
    k.fq(-0.34, -0.1, YA - 0.008, z1 - 0.5, z1 - 0.12, 'glassL')    # a sky reflection streak
    if mull:
        k.fq(-0.02, 0.02, YA - 0.008, z0 + 0.06, z1 - 0.06, frame)
    k.bx(-0.45, 0.45, YA - 0.1, YA, z0 - 0.06, z0, sill, cull='k')
    k.snowcap(-0.44, 0.44, YA - 0.09, YA - 0.01, z0)


def build_art(k, ao):
    faces(k, ao, 'A_Win', lambda k: (window(k, 1.1, 3.4), window(k, 5.2, 7.6, frame='woodD')))
    faces(k, ao, 'A_WinUp', lambda k: window(k, 4.6, 6.6, frame='steelD'))

    def door(k):
        k.fq(-0.46, 0.46, YA, 0.0, 2.5, 'steelD')
        k.fq(-0.4, 0.4, YA - 0.004, 0.02, 2.42, 'blueD')
        k.fq(-0.3, 0.3, YA - 0.008, 1.5, 2.2, 'glassD')
        k.bx(0.24, 0.3, YA - 0.08, YA - 0.004, 1.0, 1.08, 'chrome', ink=False)
        k.bx(-0.48, 0.48, YA - 0.6, YA, 2.6, 2.72, 'steel', cull='k')       # a canopy over the door (within its cell)
        k.snowcap(-0.47, 0.47, YA - 0.59, YA - 0.01, 2.72, 0.08)
        k.fq(-0.32, 0.32, YA - 0.008, 1.0, 1.3, 'yellow')
        k.text('STAFF', 0.0, YA - 0.011, 1.15, 0.12, 'black', font='display', maxw=0.5, valign='m')
    faces(k, ao, 'A_Door', door)

    def vent(k):
        k.bx(-0.36, 0.36, YA - 0.06, YA, 6.4, 7.2, 'steel', cull='k')
        for j in range(6):
            z = 6.48 + j * 0.12
            k.fq(-0.32, 0.32, YA - 0.064, z, z + 0.05, 'steelD')
    faces(k, ao, 'A_Vent', vent)

    def lamp(k):
        k.bx(-0.06, 0.06, YA - 0.08, YA, 3.0, 3.4, 'graph', cull='k')
        k.bx(-0.16, 0.16, YA - 0.36, YA - 0.08, 3.3, 3.4, 'graph')
        k.dq(-0.13, 0.13, YA - 0.34, YA - 0.1, 3.296, 'lightW')
    faces(k, ao, 'A_Lamp', lamp, glow=lambda k: k.dq(-0.12, 0.12, YA - 0.33, YA - 0.11, 3.29, 'lightW'))

    # star charts (pairs: the chart spans two cells): a framed navy chart with constellation dots and lines
    rnd = random.Random(45)
    stars = []
    while len(stars) < 30:   # spaced so no two star squares overlap
        p = (rnd.uniform(-0.9, 0.9), rnd.uniform(1.25, 2.85))
        if all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) > 0.06 for q in stars):
            stars.append(p)
    lines = [(0, 3), (3, 7), (7, 12), (12, 15), (4, 9), (9, 14), (14, 20), (20, 22), (18, 25), (25, 27)]

    def chart(k, side):
        x0, x1 = (-0.5, 0.5)
        a, b = (-0.42, 0.5) if side == 'L' else (-0.5, 0.42)
        k.fq(a, b, YA, 1.1, 3.0, 'woodD')
        k.fq(a + (0.05 if side == 'L' else 0.0), b - (0.05 if side == 'R' else 0.0), YA - 0.003, 1.15, 2.95, 'chart')
        off = 0.5 if side == 'L' else -0.5
        for (sx, sz) in stars:
            x = sx + off
            if a + 0.08 < x < b - 0.08:
                k.fq(x - 0.018, x + 0.018, YA - 0.009, sz - 0.018, sz + 0.018, 'starW')
        lv, lf = [], []
        for (i, j) in lines:
            (xa, za), (xb, zb) = stars[i], stars[j]
            xa, xb = xa + off, xb + off
            if not (a + 0.06 < xa < b - 0.06 and a + 0.06 < xb < b - 0.06):
                continue
            dx, dz = xb - xa, zb - za
            L = math.hypot(dx, dz) or 1
            xa, za, xb, zb = xa + dx / L * 0.03, za + dz / L * 0.03, xb - dx / L * 0.03, zb - dz / L * 0.03
            nx, nz = -dz / L * 0.004, dx / L * 0.004
            q = [(xa + nx, YA - 0.006, za + nz), (xb + nx, YA - 0.006, zb + nz), (xb - nx, YA - 0.006, zb - nz), (xa - nx, YA - 0.006, za - nz)]
            # wound to face -Y (one shape for every line: crossings are one colour, never flicker)
            ux, uz = q[1][0] - q[0][0], q[1][2] - q[0][2]
            vx, vz = q[2][0] - q[0][0], q[2][2] - q[0][2]
            if ux * vz - uz * vx < 0:
                q.reverse()
            lv.extend(q)
            lf.append(tuple(range(len(lv) - 4, len(lv))))
        if lf:
            k.mesh(lv, lf, 'scrB', ink=False)
        if side == 'L':
            k.text('NORTHERN SKY', 0.0, YA - 0.009, 2.8, 0.08, 'starW', font='display', maxw=0.7)
    faces(k, ao, 'A_ChartL', lambda k: chart(k, 'L'))
    faces(k, ao, 'A_ChartR', lambda k: chart(k, 'R'))

    POSTERS = [('VESPER 12 M', 'FIRST LIGHT', 'navy', 'scrB'), ('ASTRO SYMPOSIUM', 'SPECTRA OF THE COLD DISC', 'blueD', 'amberL'),
               ('THINK SAFE', 'OXYGEN LOW AT 4212 M', 'yellow', 'black')]

    def poster(k, i):
        word, sub, bg, fg = POSTERS[i]
        k.fq(-0.36, 0.36, YA, 1.2, 2.4, 'paper')
        k.fq(-0.32, 0.32, YA - 0.004, 1.24, 2.36, bg)
        if i == 0:   # a spiral galaxy print
            for j in range(10):
                a = j * 0.7
                r = 0.03 + j * 0.022
                x, z = math.cos(a) * r, 1.9 + math.sin(a) * r * 0.7
                k.fq(x - 0.03, x + 0.03, YA - (0.0115 if j % 2 else 0.008), z - 0.02, z + 0.02, 'starW' if j % 2 else 'scrB')
        elif i == 1:
            for j, c in enumerate(('redL', 'amberL', 'yellow', 'scrG', 'scrB', 'fabric')):
                k.fq(-0.27 + j * 0.09, -0.19 + j * 0.09, YA - 0.008, 1.7, 2.05, c)
        else:
            k.poly([(-0.14, YA - 0.008, 1.75), (0.14, YA - 0.008, 1.75), (0.0, YA - 0.008, 2.05)], 'black', (0, -1, 0))
        k.text(word, 0.0, YA - 0.011, 2.18, 0.08, fg, font='display', maxw=0.58)
        k.text(sub, 0.0, YA - 0.011, 1.38, 0.045, fg if i != 2 else 'black', font='display', maxw=0.58)
    for i in range(3):
        faces(k, ao, 'A_Poster%d' % (i + 1), lambda k, i=i: poster(k, i))

    def board(k):
        k.fq(-0.48, 0.48, YA, 1.0, 2.2, 'steel')
        k.fq(-0.45, 0.45, YA - 0.004, 1.03, 2.17, 'paper')
        for j, z in enumerate((1.9, 1.75, 1.6, 1.4)):
            k.fq(-0.38, -0.38 + 0.5 + 0.1 * (j % 2), YA - 0.008, z, z + 0.02, 'blueS' if j % 3 else 'redL')
        k.bx(-0.42, 0.42, YA - 0.05, YA, 0.98, 1.02, 'steelD', ink=False)
    faces(k, ao, 'A_Board', board)

    def exitpt(k):
        k.bx(-0.3, 0.3, YA - 0.06, YA, 2.6, 2.84, 'scrG', cull='k')
        k.text('EXIT', 0.0, YA - 0.063, 2.72, 0.13, 'paper', font='display', maxw=0.5, valign='m')
        k.fq(-0.18, 0.18, YA, 1.4, 1.75, 'redL')
        k.cyl(0.0, YA - 0.1, 0.4, 0.08, 0.08, 0.5, 'red', seg=8)
        k.cyl(0.0, YA - 0.1, 0.9, 0.03, 0.03, 0.1, 'black', seg=6, ink=False)
    faces(k, ao, 'A_Exit', exitpt, glow=lambda k: k.fq(-0.27, 0.27, YA - 0.066, 2.63, 2.66, 'scrG'))

    def clock(k):
        k.cyl(0.0, YA, 2.6, 0.26, 0.26, 0.06, 'black', seg=16, rot=(90, 0, 0))
        k.cyl(0.0, YA - 0.06, 2.6, 0.22, 0.22, 0.004, 'paper', seg=16, rot=(90, 0, 0), ink=False)
        k.fq(-0.01, 0.01, YA - 0.068, 2.6, 2.78, 'black')
        k.fq(0.0, 0.13, YA - 0.0715, 2.59, 2.61, 'black')
    faces(k, ao, 'A_Clock', clock)

    # the viewing rooms' glazing (the whole cell): sill wall, three tiers of glass to 9 m, mullions on the cell edges,
    # the head band; the glass itself is a glow companion (additive), so the clouds show through
    def glaze(k, mull):
        k.fq(-0.5, 0.5, Y0, 0.0, 0.12, 'graph')
        k.bx(-0.5, 0.5 if not mull else 0.46, Y0 - 0.1, Y0 + 0.2, 0.12, 0.18, 'black', cull='k')
        k.fq(-0.5, 0.5, Y0, 9.0, WALL_H, 'graph')
        right = 0.46 if mull else 0.5
        if mull:
            k.bx(0.46, 0.54, Y0 - 0.12, Y0 + 0.2, 0.0, 9.0, 'black', cull='k')
        for z in (3.2, 6.1):
            k.bx(-0.5, right, Y0 - 0.06, Y0 + 0.14, z - 0.04, z + 0.04, 'black', ink=False)
        k.bx(-0.5, right, Y0 - 0.1, Y0 + 0.18, 8.96, 8.995, 'black', ink=False)
    faces(k, ao, 'TG', lambda k: glaze(k, True), glow=lambda k: k.fq(-0.5, 0.5, Y0 + 0.05, 0.18, 8.96, 'navy'))
    faces(k, ao, 'TG_N', lambda k: glaze(k, False), glow=lambda k: k.fq(-0.5, 0.5, Y0 + 0.05, 0.18, 8.96, 'navy'))


# ================================================================ doorways (wall.passage: the head is solid above DOOR_H)
def build_doors(k, ao):
    H = DOOR_H

    def frame(k, w, c='steelD', track=False):
        for s in (-1, 1):
            x = s * w
            a, b = sorted((x, x - s * 0.14))
            k.bx(a, b, -0.56, 0.56, 0.0, H, c, cull='b')
        k.bx(-w, w, -0.56, 0.56, H, H + 0.6, c, cull='')
        for side in (-1, 1):
            yy = side * 0.563
            k.qy(-w + 0.05, w - 0.05, H + 0.15, H + 0.45, yy, side, 'yellow' if track else 'blueS')
        if track:   # the rolled-up shutter box
            k.bx(-w + 0.14, w - 0.14, -0.2, 0.2, H - 0.3, H, 'steel', cull='t')
        k.uq(-w + 0.14, w - 0.14, -0.5, 0.5, 0.004, 'steelD')     # threshold plate
    k.begin()
    frame(k, 1.0)
    for s in (-1, 1):   # the airlock's glass leaves parked open in the jambs
        a, b = sorted((s * 0.86, s * 0.6))
        k.bx(a, b, -0.03, 0.03, 0.02, H - 0.05, 'chrome', ink=False)
    k.finish('Door2', ao=ao)
    k.begin()
    for side in (-1, 1):
        k.qy(-0.84, 0.84, H + 0.2, H + 0.4, side * 0.567, side, 'scrG')
    k.finish('Door2_Glow')
    k.begin()
    frame(k, 2.0, c='graph', track=True)
    k.finish('Door4', ao=ao)


# ================================================================ the gate, trail walls, hatch, weapon stand
def build_gate(k, ao):
    """the airlock portal, 5 m wide (the gate and one wall cell either side): hazard-striped steel jambs, a lit sign
    over the opening on both faces, the concrete wall over it to 10 m"""
    k.begin()
    for side in (-1, 1):
        for s in (-1, 1):
            a, b = sorted((s * 1.5, s * 2.5))
            k.qy(a, b, 0.0, WALL_H, side * 0.5, side, 'conc')
        k.qy(-1.5, 1.5, 3.9, WALL_H, side * 0.5, side, 'conc')
        for z in (4.6, 6.8, 9.0):
            k.qy(-2.5, 2.5, z - 0.02, z + 0.02, side * 0.503, side, 'concD')
    for s in (-1, 1):
        x = s * 1.5
        a, b = sorted((x, x + s * 0.3))
        k.bx(a, b, -0.62, 0.62, 0.0, 3.25, 'steelD', cull='b')
    k.bx(-1.8, 1.8, -0.6, 0.6, 3.25, 3.9, 'steelD', cull='')
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        for s in (-1, 1):   # hazard bands on the jambs
            x = s * 1.65
            for j in range(5):
                z = 0.3 + j * 0.62
                k.fq(x - 0.13, x + 0.13, -0.626, z, z + 0.3, 'yellow')
        k.bx(-1.3, 1.3, -0.9, -0.62, 3.95, 4.5, 'navy')
        k.pop()
    k.finish('GateFrame', ao=ao)
    k.begin()
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        k.fq(-1.24, 1.24, -0.904, 4.0, 4.45, 'black')
        k.text('AIRLOCK  KEEP CLOSED', 0.0, -0.908, 4.225, 0.2, 'amberL', font='display', maxw=2.2, valign='m')
        k.pop()
    k.finish('GateFrame_Glow')
    k.begin()
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.1 + i * (Hs - 0.1) / n
        k.bx(-1.5, 1.5, -0.05, 0.05, z + 0.005, z + (Hs - 0.1) / n - 0.005, 'domeW' if i % 2 else 'domeS', ink=False)
    k.bx(-1.5, 1.5, -0.06, 0.06, 0.0, 0.1, 'graph', ink=False)
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        k.fq(-0.6, 0.6, -0.063, 1.45, 1.8, 'blueS')
        k.text('SEALED', 0.0, -0.066, 1.53, 0.18, 'paper', font='display', maxw=1.0)
        k.pop()
    obj = k.finish('GateShutter')
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)

    # trail walls: the heated link corridor (1 m along Blender Y, the corridor face +X at x 0.25, 3.6 m to its ceiling)
    def tw(k, art=None):
        def q(a, b, c, d=0.0):
            k.rq(0.25 + d, -0.5, 0.5, a, b, c)
        q(0.0, 0.12, 'graph'); q(0.12, 1.0, 'panelG'); q(1.0, 1.08, 'blueS'); q(1.08, 3.6, 'panelW')
        k.rq(0.253, -0.012, 0.012, 1.08, 3.6, 'panelG')
        k.bx(0.25, 0.32, -0.5, 0.5, 0.95, 1.0, 'steel', ink=False)          # handrail
        if art == 'lamp':
            k.bx(0.25, 0.3, -0.2, 0.2, 2.9, 3.3, 'graph', cull='l')
            k.rq(0.303, -0.16, 0.16, 2.95, 3.25, 'lightW')
        if art == 'sign':
            k.bx(0.25, 0.3, -0.48, 0.48, 2.2, 2.6, 'blueS', cull='l')
            k.text('GREAT DOME', 0.304, 0.0, 2.32, 0.16, 'paper', face='x+', font='display', maxw=0.86)
        if art == 'ext':
            k.rq(0.257, -0.15, 0.15, 1.3, 1.65, 'redL')
            k.cyl(0.36, 0.0, 0.3, 0.08, 0.08, 0.5, 'red', seg=8)
    for name, art in (('TrailWall', None), ('TrailWall_B', 'lamp'), ('TrailWall_C', 'sign'), ('TrailWall_D', 'ext')):
        k.begin()
        tw(k, art)
        k.finish(name, ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 1.2, 1.15, 0.1, 'steelD', seg=20)
    k.ring(0, 0, 0.103, 0.92, 1.1, 'yellow', seg=20)
    for j in range(-3, 4):
        k.uq(-0.6, 0.6, j * 0.2 - 0.03, j * 0.2 + 0.03, 0.106, 'steel')
    k.finish('Hatch', ao=ao)
    # weapon stand: a padded instrument case on a steel trolley
    k.begin()
    k.bx(-0.45, 0.45, -0.25, 0.25, 0.14, 0.72, 'navy', cull='b')
    k.fq(-0.38, 0.38, -0.253, 0.5, 0.64, 'yellow')
    k.text('OPTICS', 0.0, -0.256, 0.53, 0.09, 'black', font='display', maxw=0.6)
    k.bx(-0.47, 0.47, -0.27, 0.27, 0.72, 0.76, 'steel')
    for (x, y) in ((-0.38, -0.2), (0.38, -0.2), (-0.38, 0.2), (0.38, 0.2)):
        k.cyl(x - 0.02, y, 0.06, 0.06, 0.06, 0.04, 'black', seg=6, rot=(0, 90, 0))
        k.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0.06, 0.14, 'steelD', ink=False)
    k.finish('Stand', ao=ao)


# ================================================================ parapets (rotate 'run': along Blender X), fences, rails
def build_runs(k, ao):
    def parapet(k, lamp=False):
        k.bx(-0.5, 0.5, -0.22, 0.22, 0.0, 0.45, 'conc', cull='b')
        k.snowcap(-0.5, 0.5, -0.2, 0.2, 0.45, 0.07)
        k.bx(-0.04, 0.04, -0.04, 0.04, 0.45, 1.15, 'steelD', cull='b')
        for z, t in ((0.8, 0.035), (1.12, 0.05)):
            k.bx(-0.5, 0.5, -t, t, z - t, z + t, 'yellow' if z > 1 else 'steel', ink=z > 1)
        if lamp:   # a bollard light on the curb
            k.bx(0.3, 0.42, -0.1, 0.1, 0.52, 0.86, 'graph')
            k.fq(0.32, 0.4, -0.103, 0.74, 0.82, 'lightW')
        k.col(-0.5, 0.5, -0.22, 0.22, 0.0, 1.17)
    k.begin(); parapet(k); k.finish('Par_A', ao=ao)
    k.begin(); parapet(k, True); k.finish('Par_B', ao=ao)

    # the security fence (links, along Blender Y): galvanised posts, mesh panel, a barbless top rail
    def fence(k, y0, y1):
        for z in (0.35, 1.9):   # rails
            k.bx(-0.04, -0.01, y0, y1, z, z + 0.06, 'steelD', ink=False)
        y = y0 + 0.08
        while y < y1 - 0.05:     # pales with pointed tops, 0.16 m apart
            k.bx(0.0, 0.03, y - 0.03, y + 0.03, 0.05, 2.0, 'steel', cull='b')
            k.hullp([(0.0, y - 0.03, 2.0), (0.03, y - 0.03, 2.0), (0.0, y + 0.03, 2.0), (0.03, y + 0.03, 2.0), (0.015, y, 2.14)], 'steel')
            y += 0.16
    k.begin(); fence(k, -0.5, 0.5); k.col(-0.05, 0.05, -0.5, 0.5, 0.0, 2.16); k.finish('FenceFull', ao=ao)
    k.begin(); fence(k, -0.5, -0.03); k.col(-0.05, 0.05, -0.5, 0.0, 0.0, 2.16); k.finish('FenceHalf', ao=ao)
    k.begin(); k.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 2.2, 'steelD', cull='b'); k.finish('FencePost', ao=ao)

    # deck rails (links): yellow steel handrail, knee rail, toe board
    def rail(k, y0, y1):
        k.bx(-0.03, 0.03, y0, y1, 1.02, 1.08, 'yellow')
        k.bx(-0.015, 0.015, y0, y1, 0.52, 0.56, 'yellow', ink=False)
        k.bx(-0.012, 0.012, y0, y1, 0.0, 0.12, 'steelD', ink=False, cull='b')
    k.begin(); rail(k, -0.5, 0.5); k.col(-0.05, 0.05, -0.5, 0.5, 0.0, 1.08); k.finish('RailFull', ao=ao)
    k.begin(); rail(k, -0.5, -0.03); k.col(-0.05, 0.05, -0.5, 0.0, 0.0, 1.08); k.finish('RailHalf', ao=ao)
    k.begin(); k.bx(-0.04, 0.04, -0.04, 0.04, 0.0, 1.12, 'steelD', cull='b'); k.finish('RailPost', ao=ao)

    # deck posts: a steel column under a deck (top 0.3 under the deck level)
    for name, h in (('Post30', TERR - 0.3), ('Post48', DECK - 0.3)):
        k.begin()
        k.bx(-0.12, 0.12, -0.12, 0.12, 0.0, h, 'steelD', cull='bt')
        k.bx(-0.2, 0.2, -0.2, 0.2, 0.0, 0.03, 'graph', ink=False, cull='b')
        k.bx(-0.18, 0.18, -0.18, 0.18, h - 0.04, h - 0.002, 'graph', ink=False, cull='t')
        k.col(-0.12, 0.12, -0.12, 0.12, 0.0, h)
        k.finish(name, ao=ao)


# ================================================================ stairs (rise toward Blender +Y = game north at yaw 0)
def rail_line(k, pts, t, c, ink=True):
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k.beam(a, b, t + (0.008 if i % 2 else 0.0), c, ink=ink)


def treads(k, w0, w1, s0, step, n, rise, c, nose, riser, walk=True):
    """n treads stepping north from y=s0 by `step`, w0..w1 across; walkable boxes solid to the floor"""
    for i in range(n):
        top = (i + 1) * rise
        a, b = s0 + i * step, s0 + (i + 1) * step
        k.uq(w0, w1, a, a + 0.05, top, nose)
        k.uq(w0, w1, a + 0.05, b, top, c)
        k.fq(w0, w1, a, top - rise, top, riser)
        if walk:
            k.wcol(w0, w1, a, b, 0.0, top)


def stair_steel(k, name, ao, W, L, H):
    """a steel stair W wide over L, rising H: treads from the south end, a 1 m landing at the north end"""
    n = int(round((L - 1.0) / 0.25))
    rise = H / n
    assert rise <= RISE_MAX + 1e-6, (name, rise)
    y0 = -L / 2
    k.begin()
    w = W / 2 - 0.08
    treads(k, -w, w, y0, 0.25, n, rise, 'steelD', 'yellow', 'graph')
    yl = y0 + n * 0.25
    k.uq(-w, w, yl, L / 2, H, 'steelD')
    k.wcol(-w, w, yl, L / 2, 0.0, H)
    for s in (-1, 1):
        xa, xb = sorted((s * w, s * (w + 0.08)))
        k.hullp([(x, y, z) for x in (xa, xb) for (y, z) in ((y0, 0.0), (y0 + 0.3, 0.0), (yl, H - 0.1), (L / 2, H - 0.1), (L / 2, H - 0.35), (yl - 0.3, H - 0.4))], 'steelD')
        xr = s * (w + 0.04)
        rail_line(k, [(xr, y0 + 0.1, 1.05), (xr, yl, H + 1.05), (xr, L / 2 - 0.05, H + 1.05)], 0.05, 'yellow')
        for t in (0.1, 0.4, 0.7, 1.0):
            yy = y0 + 0.1 + t * (yl - y0 - 0.1)
            zz = t * H
            k.bx(xr - 0.02, xr + 0.02, yy - 0.02, yy + 0.02, zz, zz + 1.05, 'steel', ink=False, cull='b')
        # stepped collision along the stringer + handrail
        segs = 6
        for j in range(segs):
            ya, yb = y0 + (yl - y0) * j / segs, y0 + (yl - y0) * (j + 1) / segs
            k.col(xa, xb, ya, yb, 0.0, H * (j + 1) / segs + 1.05)
        k.col(xa, xb, yl, L / 2, 0.0, H + 1.05)
    k.finish(name, ao=ao)


def build_stairs(k, ao):
    stair_steel(k, 'Stair30', ao, 2.0, 6.0, TERR)
    stair_steel(k, 'Stair48', ao, 2.0, 10.0, DECK)
    # the terrace stair [4, 6]: concrete flight between cheek walls, 0 -> 3.0
    k.begin()
    n, L, H = 20, 6.0, TERR
    rise = H / n
    y0 = -L / 2
    treads(k, -1.75, 1.75, y0, 0.25, n, rise, 'concL', 'yellow', 'conc')
    yl = y0 + n * 0.25
    k.uq(-1.75, 1.75, yl, L / 2, H, 'concL')
    k.wcol(-1.75, 1.75, yl, L / 2, 0.0, H)
    for s in (-1, 1):
        xa, xb = sorted((s * 1.75, s * 2.0))
        prof = ((y0, 0.0), (y0, 0.5), (yl, H + 0.5), (L / 2, H + 0.5), (L / 2, 0.0))
        k.hullp([(x, y, z) for x in (xa, xb) for (y, z) in prof], 'conc')
        xr = s * 1.875
        rail_line(k, [(xr, y0 + 0.2, 1.4), (xr, yl, H + 1.4), (xr, L / 2 - 0.05, H + 1.4)], 0.05, 'steel')
        for t in (0.15, 0.55, 0.95):
            yy = y0 + 0.2 + t * (yl - y0 - 0.2)
            zz = 0.5 + t * H
            k.bx(xr - 0.02, xr + 0.02, yy - 0.02, yy + 0.02, zz - 0.02, zz + 0.9, 'steelD', ink=False)
        for j in range(5):
            ya, yb = y0 + (yl - y0) * j / 5, y0 + (yl - y0) * (j + 1) / 5
            k.col(xa, xb, ya, yb, 0.0, H * (j + 1) / 5 + 1.4)
        k.col(xa, xb, yl, L / 2, 0.0, H + 1.4)
    k.finish('StairC', ao=ao)
    # the pad steps [3, 3]: 10 concrete steps 0 -> 1.5 and a 0.5 m landing
    k.begin()
    n, H = 10, PAD
    treads(k, -1.4, 1.4, -1.5, 0.25, n, H / n, 'concL', 'yellow', 'conc')
    k.uq(-1.4, 1.4, 1.0, 1.5, H, 'concL')
    k.wcol(-1.4, 1.4, 1.0, 1.5, 0.0, H)
    for s in (-1, 1):
        xa, xb = sorted((s * 1.4, s * 1.5))
        k.hullp([(x, y, z) for x in (xa, xb) for (y, z) in ((-1.5, 0.0), (-1.5, 0.15), (1.0, H + 0.15), (1.5, H + 0.15), (1.5, 0.0))], 'conc')
        xr = s * 1.45
        rail_line(k, [(xr, -1.4, 1.0), (xr, 1.0, H + 1.0), (xr, 1.45, H + 1.0)], 0.05, 'yellow')
        for (yy, zz) in ((-1.4, 0.0), (-0.2, 0.75), (1.0, H)):
            k.bx(xr - 0.02, xr + 0.02, yy - 0.02, yy + 0.02, zz, zz + 1.0, 'steelD', ink=False, cull='b')
        for j in range(4):
            ya, yb = -1.5 + 2.5 * j / 4, -1.5 + 2.5 * (j + 1) / 4
            k.col(xa, xb, ya, yb, 0.0, H * (j + 1) / 4 + 1.0)
        k.col(xa, xb, 1.0, 1.5, 0.0, H + 1.0)
    k.finish('Steps15', ao=ao)


# ================================================================ ceilings (hang from their layer), floor finishes (0.006)
def build_ceilings(k, ao):
    def tile(k, w, d, light=False):
        k.dq(-w / 2, w / 2, -d / 2, d / 2, 0.0, 'panelW')
        k.dq(-w / 2, w / 2, -d / 2, -d / 2 + 0.03, -0.004, 'steel')
        k.dq(-w / 2, -w / 2 + 0.03, -d / 2 + 0.03, d / 2, -0.004, 'steel')
        if w > 1.5:
            k.dq(-w / 2 + 0.03, w / 2, -0.015, 0.015, -0.004, 'steel')
        if light:
            k.bx(-0.32, 0.32, -0.62, 0.62, -0.06, -0.006, 'steel', cull='t', ink=False)
        k.col(-w / 2, w / 2, -d / 2, d / 2, 0.0, 0.08)     # flyers keep under the ceiling
    k.begin(); tile(k, 2.0, 2.0); k.finish('C_Tile')
    k.begin(); tile(k, 2.0, 2.0, True); k.finish('C_Light')
    k.begin(); k.dq(-0.28, 0.28, -0.58, 0.58, -0.064, 'lightW'); k.finish('C_Light_Glow')
    k.begin(); tile(k, 2.0, 1.0); k.finish('C_Tile1')
    k.begin(); k.dq(-0.3, 0.3, -0.6, 0.6, -0.004, 'steel'); k.dq(-0.26, 0.26, -0.56, 0.56, -0.008, 'lightW'); k.finish('C_TrailLight')

    # floor finishes (flat, on the 0.006 layer)
    k.begin()
    k.uq(-1.0, 1.0, -1.0, 1.0, 0.0, 'stoneL')
    k.mesh([(-0.012, -1.0, 0.003), (0.012, -1.0, 0.003), (0.012, 1.0, 0.003), (-0.012, 1.0, 0.003),
            (-1.0, -0.012, 0.003), (1.0, -0.012, 0.003), (1.0, 0.012, 0.003), (-1.0, 0.012, 0.003)], [(0, 1, 2, 3), (4, 5, 6, 7)], 'stone', ink=False)
    k.finish('F_Stone')
    k.begin()
    k.uq(-1.0, 1.0, -1.0, 1.0, 0.0, 'fabricD')
    k.mesh([(-1.0, -1.0, 0.003), (1.0, -1.0, 0.003), (1.0, -0.97, 0.003), (-1.0, -0.97, 0.003),
            (-1.0, -0.97, 0.003), (-0.97, -0.97, 0.003), (-0.97, 1.0, 0.003), (-1.0, 1.0, 0.003)], [(0, 1, 2, 3), (4, 5, 6, 7)], 'navy', ink=False)
    k.finish('F_Carpet')
