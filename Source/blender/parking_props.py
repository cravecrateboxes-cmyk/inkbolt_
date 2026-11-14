"""kit-parking dressing: floor and deck markings (layer pieces 3 mm over the slab), ceiling and under-deck fittings
(hanging from their origin), props, the dock edge, the car wash (see parking_base.py for conventions)."""
import math

from mathutils import Matrix

from parking_base import *  # noqa: F401,F403
import parking_detail as DT
from ib_lib import _clip

# stacking (no two kinds ever share a height where they overlap): bays 3 - 12 mm, hatching 15, arrows / lane lines / crossings 18,
# oil 21 - 24, puddles 27 - 33, drains 36 - 42, patches 45 - 48, skid marks 51
Z0 = 0.003   # markings stand 3 mm over their layer (the layers sit 1 cm over the floor / deck top)


# ================================================================ markings
def bay_lines(m):
    uq(m, -1.5, -1.42, -2.5, 2.5, Z0, 'paper')
    uq(m, 1.42, 1.5, -2.5, 2.5, Z0, 'paper')
    uq(m, -1.42, 1.42, 2.42, 2.5, Z0, 'paper')
    m.bx(-0.75, 0.75, 1.85, 2.05, 0.0, 0.11, 'concL', bevel=True)          # wheel stop
    for x0 in (-0.6, 0.2):
        fq(m, x0, x0 + 0.4, 1.847, 0.02, 0.09, 'lineY')


def build_markings(pal, ao):
    """parking bays (3 x 5, back toward +Y) with wheel stops; numbers, an oil stain, EV and blue-badge bays"""
    for name, num, kind in (('Bay_A', '12', None), ('Bay_B', '27', 'oil'), ('Bay_C', '35', None), ('Bay_D', '48', 'oil'),
                            ('Bay_EV', '06', 'ev'), ('Bay_H', '01', 'h')):
        m = new(pal)
        bay_lines(m)
        if kind == 'ev':
            uq(m, -1.38, 1.38, -2.45, 2.38, Z0, 'exitG')
            uq(m, -0.25, 0.25, -0.5, 0.2, Z0 + 0.003, 'paper')
            for x in (-0.12, 0.12):
                uq(m, x - 0.04, x + 0.04, 0.2, 0.45, Z0 + 0.003, 'paper')
            uq(m, -0.04, 0.04, -0.9, -0.5, Z0 + 0.003, 'paper')
        elif kind == 'h':
            uq(m, -1.38, 1.38, -2.45, 2.38, Z0, 'signB')
            disc(m, 0.0, 0.55, Z0 + 0.003, 0.14, 'paper', seg=8)
            uq(m, -0.06, 0.06, -0.3, 0.35, Z0 + 0.003, 'paper')
            uq(m, -0.06, 0.45, -0.36, -0.24, Z0 + 0.006, 'paper')
            for i in range(10):
                a0, a1 = math.pi * (0.15 + i * 0.11), math.pi * (0.15 + (i + 1) * 0.11)
                poly(m, [(math.cos(a0) * 0.38, -0.35 - math.sin(a0) * 0.38, Z0 + 0.009), (math.cos(a0) * 0.48, -0.35 - math.sin(a0) * 0.48, Z0 + 0.009),
                         (math.cos(a1) * 0.48, -0.35 - math.sin(a1) * 0.48, Z0 + 0.009), (math.cos(a1) * 0.38, -0.35 - math.sin(a1) * 0.38, Z0 + 0.009)], 'paper', (0, 0, 1))
        elif kind == 'oil':
            disc(m, 0.1, -0.6, Z0, 0.5, 'stain', seg=10, sy=0.7, jag=[1.0, 0.8, 1.1, 0.9, 1.05, 0.75, 0.95])
            disc(m, -0.2, 0.6, Z0, 0.28, 'stain', seg=8, jag=[1.0, 0.7, 1.1, 0.85])
        text_up(m, num, 0.08, Z0 + (0.006 if kind in ('ev', 'h') else 0.0), 0.0, 1.45, 'paper' if kind != 'ev' else 'ink')
        make(name, m, ao)
    # lane arrow (painted 2.4 m long, centred on its cell, pointing -Y), dashed centre line, crossing, hatching
    m = new(pal)
    arrow_floor(m, 2.4, 0.3, 0.8, 0.8, Z0 + 0.015, 'paper')
    make('Arrow', m, ao)
    m = new(pal)
    uq(m, -0.27, 0.27, -0.06, 0.06, Z0 + 0.015, 'lineY')
    make('LaneDash', m, ao)
    m = new(pal)
    for y0 in (-0.42, 0.08):
        uq(m, -0.5, 0.5, y0, y0 + 0.34, Z0 + 0.015, 'paper')
    make('Zebra', m, ao)
    m = new(pal)
    sq = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    for k in range(-3, 3):
        c = k * 0.5
        a1 = (c / 2, c / 2)
        p = _clip(sq, a1, (a1[0] + 1, a1[1] - 1))
        a2 = ((c + 0.2) / 2, (c + 0.2) / 2)
        p = _clip(p, a2, (a2[0] - 1, a2[1] + 1)) if len(p) >= 3 else p
        if len(p) >= 3:
            poly(m, [(x, y, Z0 + 0.012) for (x, y) in p], 'lineY', (0, 0, 1))
    make('Hatching', m, ao)
    # oil stains, a puddle with a highlight, a drain grate in a wet ring
    for name, r, jag in (('Oil_A', 0.55, [1.0, 0.8, 1.15, 0.85, 1.05, 0.7, 1.0, 0.9]), ('Oil_B', 0.4, [0.9, 1.1, 0.75, 1.0, 0.85, 1.2])):
        m = new(pal)
        disc(m, 0.0, 0.0, Z0 + 0.018, r, 'stain', seg=len(jag), jag=jag, sy=0.75)
        disc(m, 0.4, 0.3, Z0 + 0.021, r * 0.35, 'stain', seg=6, jag=[1.0, 0.7, 1.2])
        disc(m, -0.08, 0.05, Z0 + 0.021, r * 0.35, 'concW', seg=6, sx=1.6, sy=0.4)
        make(name, m, ao)
    m = new(pal)
    disc(m, 0.0, 0.0, Z0 + 0.024, 0.95, 'puddle', seg=12, sy=0.62, jag=[1.0, 0.85, 1.1, 0.9, 1.0, 0.78, 1.08, 0.92])
    disc(m, 0.75, 0.62, Z0 + 0.03, 0.3, 'puddle', seg=7, jag=[1.0, 0.8, 1.1])
    for (x, y, w) in ((-0.35, -0.1, 0.32), (0.1, 0.12, 0.2)):
        poly(m, [(x, y, Z0 + 0.027), (x + w, y - 0.05, Z0 + 0.027), (x + w + 0.05, y, Z0 + 0.027), (x + 0.05, y + 0.05, Z0 + 0.027)], 'puddleL', (0, 0, 1))
    make('Puddle', m, ao)
    m = new(pal)
    disc(m, 0.0, 0.0, Z0 + 0.033, 0.5, 'concW', seg=10, jag=[1.0, 0.85, 1.1, 0.9, 1.0])
    uq(m, -0.3, 0.3, -0.3, 0.3, Z0 + 0.036, 'steelD')
    for k in range(5):
        uq(m, -0.24, 0.24, -0.24 + k * 0.1, -0.2 + k * 0.1, Z0 + 0.039, 'ink')
    make('Drain', m, ao)
    m = new(pal)
    m.prism([(-0.3, 0.0), (0.3, 0.0), (0.12, 0.07), (-0.12, 0.07)], -0.5, 0.5, ['lineY', 'ink'], skip=(0,))
    make('SpeedBump', m, ao)
    # worn floor: a patched concrete repair (45 mm) and tyre skid marks curving through an aisle (48 mm)
    m = new(pal)
    poly(m, [(-0.75, -0.5, 0.045), (0.7, -0.55, 0.045), (0.78, 0.45, 0.045), (-0.7, 0.52, 0.045)], 'concW', (0, 0, 1))
    for (a, b) in (((-0.3, -0.53), (-0.15, 0.49)), ((0.25, -0.54), (0.4, 0.47))):
        poly(m, [(a[0] - 0.012, a[1], 0.048), (a[0] + 0.012, a[1], 0.048), (b[0] + 0.012, b[1], 0.048), (b[0] - 0.012, b[1], 0.048)], 'concD', (0, 0, 1))
    make('Patch', m, ao)
    m = new(pal)
    for x0 in (-0.8, 0.8):
        pts = [(x0 + 0.35 * math.sin(i / 8 * math.pi), -1.3 + i * 0.325) for i in range(9)]
        for i in range(8):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            w = 0.07 + 0.03 * math.sin(i)
            poly(m, [(ax - w, ay, 0.051), (ax + w, ay, 0.051), (bx + w, by, 0.051), (bx - w, by, 0.051)], 'stain', (0, 0, 1))
    make('Skid', m, ao)


# ================================================================ ceiling and under-deck fittings (hang from origin)
def build_ceiling(pal, ao):
    m = new(pal)
    m.bx(-0.5, 0.5, -0.25, 0.25, -0.5, 0.0, 'concL', hull='noside', cull='t')
    make('Beam', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, -0.56, 0.0, 'concL', cull='t')
    make('BeamX', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.3, 0.3, -1.0, -0.6, 'galv', hull='noside')
    m.bx(-0.04, 0.04, -0.31, 0.31, -1.01, -0.59, 'steel', hull='none')
    for x in (-0.3, 0.3):
        m.bx(x - 0.012, x + 0.012, -0.012, 0.012, -0.6, 0.0, 'steelD', hull='none')
    make('Duct', m, ao)
    m = new(pal)
    m.cy((-0.5, -0.15, -0.35), 0.065, 0.065, 1.0, 'pipeR', seg=6, rot=(0, 90, 0), caps=False, hull='none')
    m.cy((-0.5, 0.18, -0.3), 0.045, 0.045, 1.0, 'pipeB', seg=6, rot=(0, 90, 0), caps=False, hull='none')
    m.bx(-0.02, 0.02, -0.25, 0.28, -0.44, -0.4, 'steelD', hull='none')
    m.bx(-0.012, 0.012, -0.012, 0.012, -0.4, 0.0, 'steelD', hull='none', cull='tb')
    m.bx(0.24, 0.26, -0.16, -0.14, -0.508, -0.42, 'chrome', hull='none', cull='t')
    make('Pipes', m, ao)
    for name, tube in (('Strip', 'lightC'), ('StripOff', 'steel')):
        m = new(pal)
        m.bx(-0.65, 0.65, -0.1, 0.1, -0.5, -0.4, 'white')
        dq(m, -0.62, 0.62, -0.075, 0.075, -0.503, tube)
        for x in (-0.5, 0.5):
            m.bx(x - 0.008, x + 0.008, -0.008, 0.008, -0.4, 0.0, 'steelD', hull='none')
        make(name, m, ao)
    m = new(pal)
    dq(m, -0.63, 0.63, -0.085, 0.085, -0.507, 'lightC')
    for sy in (-1, 1):
        y = sy * 0.103
        (fq if sy < 0 else bq)(m, -0.64, 0.64, y, -0.5, -0.42, 'light')
    make('StripGlow', m, ao)
    # exit sign (green, both faces) and level signs (one per level, both faces)
    m = new(pal)
    m.bx(-0.42, 0.42, -0.07, 0.07, -0.78, -0.46, 'exitG')
    for fy in (-1, 1):
        y = fy * 0.073
        f = fq if fy < 0 else bq
        (text_front if fy < 0 else text_back)(m, 'EXIT', 0.04, y, 0.1 * fy, -0.72, 'paper')
        poly(m, [(0.2, y + fy * 0.002, -0.72), (0.2, y + fy * 0.002, -0.52), (0.36, y + fy * 0.002, -0.62)] if fy < 0 else
             [(-0.2, y + fy * 0.002, -0.72), (-0.2, y + fy * 0.002, -0.52), (-0.36, y + fy * 0.002, -0.62)], 'paper', (0, fy, 0))
    for x in (-0.3, 0.3):
        m.bx(x - 0.01, x + 0.01, -0.01, 0.01, -0.46, 0.0, 'steelD', hull='none')
    make('ExitSign', m, ao)
    for L, (c, cl) in LEVELS.items():
        m = new(pal)
        m.bx(-0.8, 0.8, -0.07, 0.07, -1.05, -0.4, c)
        for fy in (-1, 1):
            y = fy * 0.073
            f = fq if fy < 0 else bq
            f(m, -0.74, 0.74, y, -0.99, -0.46, cl)
            f(m, -0.7, 0.7, y + fy * 0.003, -0.95, -0.5, c)
            (text_front if fy < 0 else text_back)(m, L, 0.075, y + fy * 0.006, 0.18 * fy, -0.91, 'paper')
            pts = [(0.35, -0.6), (0.6, -0.6), (0.475, -0.85)]
            poly(m, [(p[0] if fy < 0 else -p[0], y + fy * 0.006, p[1]) for p in pts], 'paper', (0, fy, 0))
        for x in (-0.6, 0.6):
            m.bx(x - 0.012, x + 0.012, -0.012, 0.012, -0.4, 0.0, 'steelD', hull='none')
        make('LevelSign_' + L, m, ao)
    # height limit bar over a ramp foot / entry lane (yellow and black, "2.1 M")
    m = new(pal)
    m.prism([(-0.06, -0.95), (0.06, -0.95), (0.06, -0.8), (-0.06, -0.8)], -1.5, 1.5, ['lineY', 'ink', 'lineY', 'ink', 'lineY', 'ink'])
    for x in (-1.2, 1.2):
        m.bx(x - 0.012, x + 0.012, -0.012, 0.012, -0.8, 0.0, 'steelD', hull='none')
    make('HeightBar', m, ao)
    # CCTV camera on a wall bracket hanging from the ceiling
    m = new(pal)
    m.bx(-0.03, 0.03, -0.03, 0.03, -0.35, 0.0, 'steelD')
    m.bx(-0.09, 0.09, -0.3, 0.1, -0.5, -0.35, 'white', bevel=True)
    m.cy((0, -0.3, -0.425), 0.05, 0.05, 0.004, 'ink', seg=8, rot=(90, 0, 0), hull='none')
    m.bx(0.05, 0.07, -0.25, -0.22, -0.36, -0.344, 'red', hull='none')
    make('CCTV', m, ao)


# ================================================================ props
def build_props(pal, ao):
    # ticket barrier island (1 x 4): kerbed island, ticket machine, barrier cabinet and a striped arm over the lane (+X)
    for name, up in (('Barrier_Down', False), ('Barrier_Up', True)):
        m = new(pal)
        m.bx(-0.45, 0.45, -2.0, 2.0, 0.0, 0.18, 'concL', bevel=True)
        for sy in (-1, 1):
            (fq if sy < 0 else bq)(m, -0.45, 0.45, sy * 2.003, 0.0, 0.18, 'lineY')
            m.cy((0, sy * 1.78, 0.18), 0.09, 0.09, 0.85, 'lineY', seg=8)
            m.cy((0, sy * 1.78, 0.6), 0.093, 0.093, 0.12, 'ink', seg=8, hull='none', caps=False)
        m.bx(-0.25, 0.25, -1.4, -0.9, 0.18, 1.5, 'signB', bevel=True)
        rq(m, 0.253, -1.35, -0.95, 0.95, 1.3, 'glass')
        rq(m, 0.253, -1.3, -1.0, 0.7, 0.8, 'ink')
        m.bx(0.25, 0.3, -1.12, -1.02, 0.55, 0.62, 'red', hull='none')
        m.bx(-0.28, 0.28, -1.45, -0.85, 1.5, 1.6, 'pWhite')
        m.bx(-0.28, 0.28, 0.95, 1.55, 0.18, 1.15, 'lineY', bevel=True)
        m.bx(-0.3, 0.3, 0.93, 1.57, 1.15, 1.2, 'ink')
        m.cy((0.29, 1.25, 1.0), 0.12, 0.12, 0.1, 'steelD', seg=8, rot=(0, 90, 0))
        stripes = ['pipeR', 'paper'] * 5
        if up:
            mat = Matrix.Translation((0.35, 0, 1.0)) @ Matrix.Rotation(math.radians(-82), 4, 'Y') @ Matrix.Translation((-0.35, 0, -1.0))
        else:
            mat = None
        m.prism([(1.2, 0.95), (1.3, 0.95), (1.3, 1.05), (1.2, 1.05)], 0.35, 3.4, stripes, mat=mat)
        DT.barrier_detail(m)
        make(name, m, ao, cols=[cb(-0.45, -2.0, 0, 0.45, 2.0, 0.18), cb(-0.3, -1.45, 0, 0.3, -0.85, 1.6), cb(-0.3, 0.93, 0, 0.3, 1.57, 1.2)])
    # pay station (1 x 1)
    m = new(pal)
    m.bx(-0.4, 0.4, -0.3, 0.3, 0.0, 0.12, 'concL', cull='b')
    m.bx(-0.32, 0.32, -0.22, 0.22, 0.12, 1.75, 'signB', bevel=True)
    fq(m, -0.24, 0.24, -0.223, 1.15, 1.5, 'glass')
    fq(m, -0.2, 0.2, -0.226, 1.38, 1.46, 'glassL')
    for k in range(9):
        fq(m, -0.18 + (k % 3) * 0.13, -0.1 + (k % 3) * 0.13, -0.223, 0.8 + (k // 3) * 0.1, 0.87 + (k // 3) * 0.1, 'steel')
    fq(m, -0.12, 0.12, -0.223, 0.6, 0.66, 'ink')
    m.bx(-0.38, 0.38, -0.3, 0.3, 1.75, 1.82, 'pWhite')
    m.bx(-0.2, 0.2, -0.05, 0.05, 1.82, 2.22, 'paper')
    for fy in (-1, 1):
        (text_front if fy < 0 else text_back)(m, 'P', 0.06, fy * 0.053, 0.0, 1.88, 'signB')
    DT.paystation_detail(m)
    make('PayStation', m, ao, cols=[cb(-0.34, -0.25, 0, 0.34, 0.25, 1.82)])
    # traffic cones
    for name, n in (('Cone', 1), ('Cones', 2)):
        m = new(pal)
        for i in range(n):
            x, y = (0.0, 0.0) if i == 0 else (0.3, 0.25)
            if i == 1:   # a knocked-over cone
                m.parent = Matrix.Translation((x, y, 0.15)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Translation((0, 0, -0.35))
                x = y = 0.0
            m.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.0, 0.04, 'ink', cull='b' if i == 0 else '')
            m.cy((x, y, 0.04), 0.15, 0.03, 0.66, 'cone', seg=10)
            m.cy((x, y, 0.3), 0.104, 0.084, 0.14, 'paper', seg=10, hull='none', caps=False)
            m.parent = Matrix.Identity(4)
        if n == 2:
            m.parent = Matrix.Identity(4)
        make(name, m, ao, cols=[cb(-0.2, -0.2, 0, 0.2, 0.2, 0.7)])
    # bollard
    m = new(pal)
    m.cy((0, 0, 0), 0.12, 0.12, 0.95, 'lineY', seg=10)
    m.sp((0, 0, 0.95), 0.12, 'lineY', seg=(10, 4), scale=(1, 1, 0.5))
    for z in (0.55, 0.75):
        m.cy((0, 0, z), 0.123, 0.123, 0.08, 'ink', seg=10, hull='none', caps=False)
    m.cy((0, 0, 0.0), 0.17, 0.17, 0.04, 'steelD', seg=10)
    DT.bollard_detail(m)
    make('Bollard', m, ao, cols=[cb(-0.13, -0.13, 0, 0.13, 0.13, 1.0)])
    # jersey barriers (2 x 1): concrete with reflectors, plastic red / white
    prof = [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.08), (0.12, 0.3), (0.08, 0.82), (-0.08, 0.82), (-0.12, 0.3), (-0.3, 0.08)]
    for name, cols in (('Jersey_C', ['concL']), ('Jersey_P', ['pipeR', 'paper', 'pipeR', 'paper'])):
        m = new(pal)
        m.prism(prof, -1.0, 1.0, cols, skip=(0,), bevel=True)
        if name == 'Jersey_C':
            for fy in (-1, 1):
                for x in (-0.6, 0.6):
                    poly(m, [(x - 0.08, fy * 0.104, 0.5), (x + 0.08, fy * 0.104, 0.5), (x + 0.08, fy * 0.099, 0.62), (x - 0.08, fy * 0.099, 0.62)], 'lineY', (0, fy, 0.1))
        make(name, m, ao, cols=[cb(-1.0, -0.3, 0, 1.0, 0.3, 0.82)])
    # maintenance cage (3 x 2): galvanised frame, bars, a padlocked door, shelving, drums and cylinders inside
    m = new(pal)
    W2, D2, Hc = 1.45, 0.95, 2.3
    for x in (-W2, -W2 / 3, W2 / 3, W2):
        for y in (-D2, D2):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, Hc + 0.05, 'galv', cull='b')
    for y in (-D2, D2):
        m.bx(-W2, W2, y - 0.025, y + 0.025, Hc - 0.06, Hc, 'galv')
        m.bx(-W2, W2, y - 0.025, y + 0.025, 0.05, 0.11, 'galv')
    for x in (-W2, W2):
        m.bx(x - 0.025, x + 0.025, -D2, D2, Hc - 0.14, Hc - 0.08, 'galv')
    bars = []
    k = -W2 + 0.15
    while k < W2 - 0.05:
        bars.append(k)
        k += 0.15
    for x in bars:
        for y in (-D2, D2):
            m.bx(x - 0.008, x + 0.008, y - 0.008, y + 0.008, 0.11, Hc - 0.06, 'steel', hull='none', cull='tb')
    for y in [-D2 + 0.15 * i for i in range(1, int(2 * D2 / 0.15))]:
        for x in (-W2, W2):
            m.bx(x - 0.008, x + 0.008, y - 0.008, y + 0.008, 0.11, Hc - 0.06, 'steel', hull='none', cull='tb')
    fq(m, -0.4, 0.4, -D2 - 0.03, 1.2, 1.55, 'lineY')
    m.bx(0.05, 0.15, -D2 - 0.08, -D2 - 0.03, 0.95, 1.07, 'lineY')
    m.bx(-1.3, -0.2, 0.45, 0.85, 0.0, 1.8, 'steelD', cull='b')
    for z in (0.5, 1.0, 1.5):
        uq(m, -1.27, -0.23, 0.48, 0.82, z, 'steel')
        for i, x in enumerate((-1.2, -0.85, -0.55)):
            m.bx(x, x + 0.28, 0.52, 0.8, z, z + 0.24 + 0.05 * (i % 2), 'cardb' if (i + int(z * 2)) % 3 else 'pipeB')
    for x, c in ((0.4, 'pipeB'), (0.95, 'pipeR')):
        m.cy((x, 0.35, 0.0), 0.28, 0.28, 0.9, c, seg=10)
        m.cy((x, 0.35, 0.9), 0.24, 0.24, 0.02, 'steelD', seg=10, hull='none')
    for x in (0.6, 0.85):
        m.cy((x, -0.5, 0.0), 0.12, 0.12, 1.2, 'exitG', seg=8)
        m.sp((x, -0.5, 1.2), 0.12, 'exitG', seg=(8, 3), scale=(1, 1, 0.6))
    m.cy((-0.7, -0.4, 0.0), 0.2, 0.18, 0.32, 'lineY', seg=8)
    m.bm_((-0.7, -0.4, 0.3), (-0.4, -0.2, 1.3), 0.035, 'wood')
    make('Cage', m, ao, cols=[cb(-W2 - 0.03, -D2 - 0.03, 0, W2 + 0.03, D2 + 0.03, Hc)])
    # oil drums (1 x 1)
    m = new(pal)
    for (x, y, c) in ((-0.2, -0.15, 'pipeB'), (0.22, 0.05, 'pipeR'), (-0.12, 0.3, 'exitG')):
        m.cy((x, y, 0.0), 0.2, 0.2, 0.86, c, seg=10)
        for z in (0.28, 0.58):
            m.cy((x, y, z), 0.205, 0.205, 0.04, 'steelD', seg=10, hull='none', caps=False)
        disc(m, x, y, 0.863, 0.16, 'steelD', seg=10)
    make('Drums', m, ao, cols=[cb(-0.42, -0.37, 0, 0.44, 0.52, 0.86)])
    # pallet of boxes (2 x 2)
    m = new(pal)
    m.bx(-0.6, 0.6, -0.5, 0.5, 0.0, 0.14, 'wood')
    for (x0, y0, z0, h) in ((-0.58, -0.48, 0.14, 0.4), (0.0, -0.48, 0.14, 0.4), (-0.58, 0.0, 0.14, 0.4), (0.0, 0.02, 0.14, 0.45),
                            (-0.55, -0.45, 0.54, 0.35), (0.02, -0.4, 0.6, 0.4), (-0.4, 0.06, 0.6, 0.3)):
        m.bx(x0, x0 + 0.56, y0, y0 + 0.46, z0, z0 + h, 'cardb')
        uq(m, x0 + 0.24, x0 + 0.32, y0 + 0.01, y0 + 0.45, z0 + h + 0.003, 'wood')
    make('Pallets', m, ao, cols=[cb(-0.6, -0.5, 0, 0.6, 0.5, 0.95)])
    # wheelie bins (2 x 1)
    m = new(pal)
    for x, c in ((-0.45, 'pGreen'), (0.42, 'steelD')):
        m.prism([(-0.35, 0.05), (0.32, 0.05), (0.36, 1.05), (-0.38, 1.05)], x - 0.33, x + 0.33, [c], bevel=True)
        m.bx(x - 0.36, x + 0.36, -0.42, 0.4, 1.05, 1.11, c)
        for sx in (-1, 1):
            m.cy((x + sx * 0.3 - (0.06 if sx > 0 else 0), 0.3, 0.1), 0.1, 0.1, 0.06, 'tire', seg=8, rot=(0, 90, 0))
    make('Bins', m, ao, cols=[cb(-0.82, -0.42, 0, 0.8, 0.42, 1.11)])
    # forklift (2 x 3)
    m = new(pal)
    m.parent = Matrix.Rotation(math.radians(-6), 4, 'Z')
    for sx in (-1, 1):
        wheel(m, sx * 0.68, -0.55, 0.3, 0.22, hub='steelD')
        wheel(m, sx * 0.66, 0.65, 0.25, 0.2, hub='steelD')
    m.bx(-0.55, 0.55, -0.8, 0.9, 0.22, 0.9, 'lineY', bevel=True)
    m.bx(-0.58, 0.58, 0.62, 1.05, 0.25, 1.15, 'steelD', bevel=True)
    m.bx(-0.3, 0.3, 0.0, 0.45, 0.9, 1.05, 'seat')
    m.bx(-0.3, 0.3, 0.35, 0.47, 1.05, 1.5, 'seat')
    for sx in (-1, 1):
        m.bx(sx * 0.5 - 0.03, sx * 0.5 + 0.03, -0.75, -0.69, 0.9, 2.1, 'ink')
        m.bx(sx * 0.5 - 0.03, sx * 0.5 + 0.03, 0.55, 0.61, 1.15, 2.1, 'ink')
        m.bx(sx * 0.35 - 0.05, sx * 0.35 + 0.05, -0.95, -0.85, 0.1, 2.4, 'steelD')
        m.bx(sx * 0.3 - 0.06, sx * 0.3 + 0.06, -1.55, -0.9, 0.12, 0.18, 'steel')
    m.bx(-0.55, 0.55, -0.78, 0.64, 2.1, 2.16, 'ink')
    m.bx(-0.45, 0.45, -1.03, -0.955, 0.15, 1.0, 'steelD')
    m.cy((0.0, 0.1, 2.16), 0.07, 0.06, 0.12, 'litA', seg=8)
    m.parent = Matrix.Identity(4)
    make('Forklift', m, ao, bevel=0.015, cols=[rot_box(2.6, 1.3, -6, 1.2, 0, -0.25), rot_box(1.4, 1.2, -6, 2.4, 0, 0.0)])


# ================================================================ dock, car wash
def build_dock(pal, ao):
    """dock edge (on the 1.2 m dock layer, front toward the open floor): nosing, hazard face, rubber bumpers;
    DockEdge_L adds a leveller plate"""
    for name, lev in (('DockEdge', False), ('DockEdge_L', True)):
        m = new(pal)
        m.bx(-0.47, 0.47, -0.52, -0.42, -1.2, 0.004, 'steelD', cull='b')
        for k in range(4):
            fq(m, -0.47 + k * 0.235, -0.3525 + k * 0.235, -0.523, -0.3, -0.05, 'lineY')
        m.bx(-0.32, -0.12, -0.68, -0.52, -0.95, -0.35, 'tire')
        m.bx(0.12, 0.32, -0.68, -0.52, -0.95, -0.35, 'tire')
        if lev:
            uq(m, -0.47, 0.47, -0.42, 0.45, 0.007, 'steel')
            for k in range(5):
                uq(m, -0.47 + k * 0.19, -0.375 + k * 0.19, -0.42, -0.3, 0.01, 'lineY')
        make(name, m, ao)
    # car wash (6 x 9): two side portals with brushes, a header with WASH, a dryer arch, wet floor, guide rails
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 2.6, sx * 2.95))
        for y in (-3.6, 0.0, 3.6):
            m.bx(a, b, y - 0.2, y + 0.2, 0.0, 3.1, 'pWhite', bevel=True)
        m.bx(a, b, -3.8, 3.8, 3.1, 3.4, 'pWhite')
        x = sx * 2.95 + sx * 0.003
        (rq if sx > 0 else lq)(m, x, -3.4, -0.2, 0.3, 1.5, 'signB')
        (rq if sx > 0 else lq)(m, x, 0.2, 3.4, 0.3, 1.5, 'signB')
        for y, c in ((-1.8, 'pPurple'), (1.8, 'pTeal')):   # vertical roller brushes
            m.cy((sx * 2.05, y, 0.15), 0.42, 0.42, 2.7, c, seg=10)
            for k in range(5):
                m.cy((sx * 2.05, y, 0.4 + k * 0.5), 0.45, 0.45, 0.12, 'pMint', seg=10, hull='none', caps=False)
            m.bx(sx * 2.05 - 0.04, sx * 2.05 + 0.04, y - 0.04, y + 0.04, 2.85, 3.2, 'steelD')
            m.bx(min(sx * 2.09, sx * 2.6), max(sx * 2.09, sx * 2.6), y - 0.032, y + 0.032, 3.0, 3.08, 'steelD')
    m.bx(-2.95, 2.95, -3.8, -3.4, 3.4, 4.0, 'signB')
    m.bx(-2.95, 2.95, 3.4, 3.8, 3.4, 4.0, 'signB')
    for fy in (-1, 1):   # script "Car Wash" with a drop shadow, both faces
        ib_text.draw(m, 'Car Wash', 0.0, fy * 3.803, 3.53, 0.27, 'paper', face='y-' if fy < 0 else 'y+', font='script',
                     maxw=3.2, shadow='pPurple', shadow_off=(0.05, -0.06))
    m.cy((-2.6, 0.0, 2.75), 0.35, 0.35, 5.2, 'pPurple', seg=10, rot=(0, 90, 0))     # top brush
    m.bx(-2.6, 2.6, -3.0, -2.75, 2.8, 3.1, 'galv')                                # dryer nozzle bar
    for k in range(6):
        m.bx(-2.2 + k * 0.85, -2.0 + k * 0.85, -2.95, -2.8, 2.6, 2.8, 'steel')
    for x in (-1.0, 1.0):
        m.bx(x - 0.06, x + 0.06, -4.3, 4.3, 0.0, 0.12, 'lineY', cull='b')
    disc(m, 0.4, 0.5, 0.058, 1.6, 'puddle', seg=12, sy=1.6, jag=[1.0, 0.85, 1.1, 0.9, 1.0, 0.8])
    disc(m, -0.3, -0.6, 0.064, 0.5, 'puddleL', seg=8, sy=0.4)
    uq(m, -2.4, 2.4, -0.15, 0.15, 0.07, 'steelD')
    cols = []
    for sx in (-1, 1):
        a, b = sorted((sx * 1.6, sx * 2.95))
        cols.append(cb(a, -3.8, 0, b, 3.8, 3.4))
    make('Landmark_CarWash', m, ao, bevel=0.015, cols=cols)
