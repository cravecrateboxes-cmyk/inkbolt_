"""kit-metro platforms: the stopped trains (a cab car at each end and middle cars, walk-through, doors open on both
sides, the line colour repainted per train by the theme), the track (concrete slab, sleeper blocks, running rails,
the third rail), the info pylons on the platforms, the station clock (landmark), the staff booth, benches' platform
cousins and the maintenance gear (tool cages, cable drums, track trolleys, cones, electrical cabinets, workbenches).
See mt_base.py for the conventions."""
import math
import random

from mt_base import *  # noqa: F401,F403
import mt_base as B
import mt_detail as DET

TF = TRACK_D + 0.02   # the car floor over the trackbed (2 cm over the platform)
CW = 1.4              # half the car body width (the trackbed is 3 m: 10 cm to each platform edge)
CH = 3.32             # roof line over the trackbed floor
DOORS = (-6.0, 0.0, 6.0)
DW = 0.68             # half door width


def segs(x0, x1, holes):
    """the spans of [x0, x1] between door holes (centre, half width)"""
    out, a = [], x0
    for (c, w) in holes:
        if c - w > a:
            out.append((a, c - w))
        a = c + w
    if a < x1:
        out.append((a, x1))
    return out


def car(k, cab):
    """one 18 m car (origin: trackbed floor, centre of the car); cab: None, '+' (a driving cab at +X) or '-'"""
    x0, x1 = -9.0, 9.0
    holes = [(c, DW) for c in DOORS]
    zw0, zw1, zr = 1.22, 2.38, 3.1           # window band, interior ceiling
    # ---- underframe and bogies
    for bx in (-6.2, 6.2):
        k.bx(bx - 1.2, bx + 1.2, -1.05, 1.05, 0.12, 0.62, 'black', cull='b')
        for wx in (-0.75, 0.75):
            for s in (-1, 1):
                k.cyl(bx + wx, s * 0.72 - 0.05, 0.38, 0.38, 0.38, 0.1, 'graph', seg=8, rot=(90, 0, 0))
    k.bx(x0 + 0.3, x1 - 0.3, -1.2, 1.2, 0.62, TF - 0.02, 'graph', cull='b')
    # ---- the shell: sides (outside face y = +-CW) with door openings, the livery band, windows (dark until the glow)
    for s in (-1, 1):
        y = s * CW
        for (a, b) in segs(x0, x1, holes):
            k.qy(a, b, 0.62, zw0, y, s, 'trainW')
            k.qy(a, b, zw0, zw0 + 0.12, y, s, 'crim')
            k.qy(a, b, zw1, zr + 0.18, y, s, 'trainW')
            k.qy(a, b, zr + 0.18, CH, y, s, 'steel')
            # window piers: glass between 0.3 m piers (the glass is the glow companion, set back 1 cm)
            n = max(1, int((b - a) / 1.6))
            w = (b - a) / n
            for i in range(n + 1):
                xa = a + i * w - (0.12 if i else 0.0)
                xb = a + i * w + (0.12 if i < n else 0.0)
                k.qy(max(a, xa), min(b, xb), zw0 + 0.12, zw1, y, s, 'trainW')
            # inside face of the same wall
            k.qy(a, b, TF, zw0 + 0.12, y - s * 0.08, -s, 'paintL')
            k.qy(a, b, zw1, zr, y - s * 0.08, -s, 'paintL')
            k.qy(a, b, zw1 + 0.08, zw1 + 0.4, y - s * 0.083, -s, 'mustard')   # the ad strip over the windows
            for i in range(n + 1):
                xa = a + i * w - (0.12 if i else 0.0)
                xb = a + i * w + (0.12 if i < n else 0.0)
                k.qy(max(a, xa), min(b, xb), zw0 + 0.12, zw1, y - s * 0.08, -s, 'paintL')
            k.col(a, b, min(y, y - s * 0.1), max(y, y - s * 0.1), TF, CH)
        for (c, w) in holes:
            # the doorway: frame, the threshold (yellow edge) bridging the 10 cm gap to the platform, leaves parked
            for e in (-1, 1):
                k.bx(c + e * w - (0.05 if e > 0 else 0.0), c + e * w + (0.05 if e < 0 else 0.0), min(y, y - s * 0.1), max(y, y - s * 0.1), TF, 2.95, 'steelD', cull='bt')
            k.bx(c - w, c + w, min(y, y - s * 0.1), max(y, y - s * 0.1), 2.95, CH, 'trainW', cull='t')
            ya, yb = sorted((y - s * 0.1, y + s * 0.12))
            k.uq(c - w, c + w, ya, yb, TF, 'steel')
            k.uq(c - w, c + w, min(y + s * 0.07, y + s * 0.12), max(y + s * 0.07, y + s * 0.12), TF + 0.003, 'hazard')
            k.wcol(c - w, c + w, ya, yb, 0.0, TF)
            k.qy(c - w - 0.02, c - w + 0.02, 2.95, CH, y + s * 0.003, s, 'graph')
    # ---- floor, ceiling, roof
    k.uq(x0 + 0.1, x1 - 0.1, -CW + 0.1, CW - 0.1, TF, 'rubber')
    k.wcol(x0, x1, -CW, CW, 0.0, TF)
    k.dq(x0 + 0.1, x1 - 0.1, -CW + 0.08, CW - 0.08, zr, 'tileW')
    k.uq(x0 + (1.6 if cab == '-' else 0.0), x1 - (1.6 if cab == '+' else 0.0), -CW, CW, CH, 'steel')
    k.col(x0, x1, -CW, CW, zr, CH + 0.1)
    for ax in (-4.5, 4.5):
        k.bx(ax - 1.4, ax + 1.4, -0.8, 0.8, CH, CH + 0.3, 'steelD', cull='b')
    # ---- seats (longitudinal benches between the doors), grab poles, grab rails
    for s in (-1, 1):
        y = s * (CW - 0.08)
        for (a, b) in segs(x0 + 0.5, x1 - 0.5, [(c, DW + 0.15) for c in DOORS]):
            ya, yb = sorted((y, y - s * 0.46))
            k.bx(a, b, ya, yb, TF, TF + 0.44, 'seat')
            k.bx(a, b, min(y, y - s * 0.08), max(y, y - s * 0.08), TF + 0.44, TF + 1.0, 'seat', cull='b')
            k.col(a, b, ya, yb, TF, TF + 0.44)
            k.beam((a + 0.05, y - s * 0.32, 2.62), (b - 0.05, y - s * 0.32, 2.62), 0.035, 'hazard')
        for c in DOORS:
            for e in (-1, 1):
                k.pole(c + e * (DW + 0.1), y - s * 0.3, TF, zr, 0.02, 'hazard', ink=False)
    # ---- the ends: a gangway into the next car, or the driving cab
    for e in (-1, 1):
        xe = e * 9.0
        if cab == ('+' if e > 0 else '-'):
            # the cab: a closed bulkhead with its door, the raked nose, windscreen, lights, destination blind
            xi = xe - e * 1.6
            k.qx(-0.45, 0.45, TF, 2.9, xi - e * 0.004, -e, 'graph')
            k.qx(-0.25, 0.25, TF + 1.5, TF + 1.9, xi - e * 0.008, -e, 'black')
            k.col(min(xi, xe), max(xi, xe), -CW, CW, 0.0, CH)
            nose = [(xe - e * 0.2, 0.62), (xe, 1.0), (xe, 1.9), (xe - e * 0.35, CH)]
            k.hullp([(x, y, z) for (x, z) in nose for y in (-CW + 0.05, CW - 0.05)] + [(xi, y, z) for y in (-CW, CW) for z in (0.62, CH)],
                    lambda f: 'paintL' if abs(f.normal.x) > 0.9 and abs(f.calc_center_median().x - xi) < 0.01 else 'trainW')
            for y in (-0.95, 0.95):
                k.bx(min(xe, xe + e * 0.04), max(xe, xe + e * 0.04), y - 0.14, y + 0.14, 1.2, 1.36, 'lightW')
            k.bx(min(xe, xe + e * 0.35), max(xe, xe + e * 0.35), -0.25, 0.25, 0.75, 0.95, 'black')
        else:
            # gangway: the end wall with a 1.2 m opening, black bellows to the next car
            for (ya, yb) in ((-CW, -0.6), (0.6, CW)):
                k.qx(ya, yb, TF, zr, xe - e * 0.15, -e, 'paintL')
                k.col(min(xe, xe - e * 0.15), max(xe, xe - e * 0.15), ya, yb, TF, CH)
            k.qx(-0.6, 0.6, 2.25, zr, xe - e * 0.15, -e, 'paintL')
            xa, xb = sorted((xe, xe - e * 0.15))
            for s in (-1, 1):
                k.qy(xa, xb, TF, 2.25, s * 0.6, -s, 'black')
            k.dq(xa, xb, -0.6, 0.6, 2.25, 'black')
            k.uq(xa, xb, -0.6, 0.6, TF + 0.004, 'steel')
            k.col(min(xe, xe - e * 0.15), max(xe, xe - e * 0.15), -CW, CW, 2.25, CH)


def car_glow(k, cab):
    """the lit windows (the warm interior seen through them) and the ceiling light strips, the destination blind"""
    holes = [(c, DW) for c in DOORS]
    for s in (-1, 1):
        y = s * (CW - 0.04)
        for (a, b) in segs(-9.0, 9.0, holes):
            n = max(1, int((b - a) / 1.6))
            w = (b - a) / n
            for i in range(n):
                xa = a + i * w + (0.12 if i else 0.0)
                xb = a + (i + 1) * w - (0.12 if i < n - 1 else 0.0)
                k.qy(xa, xb, 1.34, 2.38, y, s, 'glass')
    for y in (-0.5, 0.5):
        k.dq(-8.4, 8.4, y - 0.06, y + 0.06, 3.096, 'lightW')
    if cab:
        e = 1 if cab == '+' else -1
        xe = e * 9.0
        k.qx(-1.0, 1.0, 2.0, 2.75, xe - e * 0.16, e, 'screen')
        k.qx(-0.6, 0.6, 2.85, 3.08, xe - e * 0.3, e, 'black')
        k.text('BAYSIDE', xe - e * 0.31, 0.0, 2.9, 0.15, 'amberL', face='x+' if e > 0 else 'x-', font='display', maxw=1.1)


def build_trains(k, ao):
    for name, cab in (('CarHead', '+'), ('CarMid', None), ('CarTail', '-')):
        k.begin()
        car(k, cab)
        k.finish(name, ao=ao)
        k.begin()
        car_glow(k, cab)
        k.finish(name + '_Glow')
    # track [2, 3] along X: the concrete slab with its drain, sleeper blocks, the running rails (bright heads), the
    # third rail on its insulators under a yellow cover board
    k.begin()
    k.uq(-1.0, 1.0, -1.3, 1.3, 0.05, 'ballast')
    k.uq(-1.0, 1.0, -0.12, 0.12, 0.054, 'black')
    for x in (-0.66, 0.0, 0.66):
        for s in (-1, 1):
            k.bx(x - 0.16, x + 0.16, s * 0.72 - 0.18, s * 0.72 + 0.18, 0.05, 0.13, 'conc', ink=False, cull='b')
    for s in (-1, 1):
        y = s * 0.7175
        k.bx(-1.0, 1.0, y - 0.04, y + 0.04, 0.13, 0.25, 'steelD', cull='blr')
        k.uq(-1.0, 1.0, y - 0.04, y + 0.04, 0.253, 'railT')
    k.bx(-1.0, 1.0, 1.12, 1.2, 0.2, 0.3, 'rust', cull='blr')
    k.bx(-1.0, 1.0, 1.08, 1.24, 0.34, 0.36, 'hazard', cull='blr')
    for x in (-0.6, 0.6):
        k.bx(x - 0.05, x + 0.05, 1.11, 1.21, 0.05, 0.2, 'paper', ink=False, cull='b')
    k.finish('Track', ao=ao)


# ================================================================ platform furniture
def build_platform(k, ao):
    # info pylon (1 cell): a granite base, a steel totem with an ad on one face and the line diagram on the other
    k.begin()
    k.bx(-0.5, 0.5, -0.24, 0.24, 0.0, 0.3, 'granite')
    k.bx(-0.45, 0.45, -0.18, 0.18, 0.3, 2.6, 'steelD', cull='b')
    k.bx(-0.48, 0.48, -0.2, 0.2, 2.6, 2.75, 'graph')
    k.fq(-0.38, 0.38, -0.183, 0.6, 2.4, 'crim')
    k.text('FIZZBOLT', 0.0, -0.186, 2.0, 0.14, 'paper', font='display', maxw=0.7)
    k.fq(-0.12, 0.12, -0.186, 0.9, 1.6, 'chrome')
    k.bq(-0.38, 0.38, 0.183, 0.6, 2.4, 'paper')
    for j, (c, z) in enumerate((('crim', 1.9), ('blue', 1.5), ('green', 1.1))):
        k.bq(-0.32, 0.32, 0.186, z - 0.02, z + 0.02, c)
    k.text('CENTRAL', 0.0, 0.186, 2.15, 0.1, 'blueD', face='y+', font='display')
    DET.column(k)
    k.col(-0.5, 0.5, -0.24, 0.24, 0.0, 2.75)
    k.finish('Column', ao=ao)

    # the station clock (landmark) [6, 4]: a granite seat plinth, a tiled tower, four clock faces, the roundel
    k.begin()
    k.bx(-3.0, 3.0, -2.0, 2.0, 0.0, 0.42, 'granite')
    k.bx(-2.9, 2.9, -1.9, 1.9, 0.42, 0.47, 'woodL', cull='b')
    k.bx(-0.7, 0.7, -0.7, 0.7, 0.47, 3.4, 'tileW', cull='b')
    for z0, z1, c in ((0.47, 1.2, 'teal'), (1.2, 1.26, 'mustard'), (3.0, 3.4, 'teal')):
        k.bx(-0.72, 0.72, -0.72, 0.72, z0, z1, c, ink=False, cull='bt')
    k.bx(-0.85, 0.85, -0.85, 0.85, 3.4, 4.7, 'graph')
    for rot in (0, 90, 180, 270):
        k.push(0, 0, rot)
        y = -0.853
        k.poly([(math.cos(a / 16 * 6.283) * 0.6, y, 4.05 + math.sin(a / 16 * 6.283) * 0.6) for a in range(16)], 'paper', (0, -1, 0))
        for h in range(12):
            a = h / 12 * 6.283
            k.fq(math.sin(a) * 0.5 - 0.02, math.sin(a) * 0.5 + 0.02, y - 0.003, 4.05 + math.cos(a) * 0.5 - 0.05, 4.05 + math.cos(a) * 0.5 + 0.05, 'black')
        k.poly([(-0.025, y - 0.006, 4.05), (0.025, y - 0.006, 4.05), (0.3, y - 0.006, 4.35), (0.26, y - 0.006, 4.39)], 'black', (0, -1, 0))
        k.poly([(-0.02, y - 0.009, 4.0), (0.02, y - 0.009, 4.0), (0.02, y - 0.009, 4.52), (-0.02, y - 0.009, 4.52)], 'black', (0, -1, 0))
        # a departure screen on the tower's upper shaft
        k.bx(-0.6, 0.6, -0.86, -0.72, 2.2, 2.7, 'black')
        k.pop()
    k.bx(-0.12, 0.12, -0.12, 0.12, 4.7, 5.2, 'steelD', cull='b')
    k.cyl(0.0, -0.06, 5.25, 0.9, 0.9, 0.12, 'crim', seg=20, rot=(90, 0, 0))
    k.bx(-1.15, 1.15, -0.1, 0.1, 5.1, 5.4, 'blue')
    for s in (-1, 1):
        k.text('CENTRAL', 0.0, s * 0.103, 5.25, 0.17, 'paper', face='y-' if s < 0 else 'y+', font='display', maxw=2.0, valign='m')
    k.col(-3.0, 3.0, -2.0, 2.0, 0.0, 0.47)
    k.col(-0.85, 0.85, -0.85, 0.85, 0.47, 4.7)
    k.finish('Landmark_Clock', ao=ao)
    k.begin()
    for rot in (0, 90, 180, 270):
        k.push(0, 0, rot)
        k.fq(-0.55, 0.55, -0.864, 2.25, 2.65, 'screen')
        k.text('BAYSIDE  2 MIN', 0.0, -0.867, 2.4, 0.09, 'amberL', font='cond', maxw=1.0)
        k.pop()
    k.finish('Landmark_Clock_Glow')

    # platform staff booth [2, 2]: glazed on three sides, a door at the back, the desk and monitor inside
    k.begin()
    k.bx(-0.95, 0.95, -0.95, 0.95, 0.0, 0.9, 'blueD', cull='b')
    for (x, y) in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.9, 2.25, 'steelD', cull='b')
    k.bx(-1.0, 1.0, -1.0, 1.0, 2.25, 2.45, 'blueD')
    k.bx(-0.85, 0.85, 0.86, 0.94, 0.9, 2.25, 'paintL', cull='bt')
    k.bx(-0.8, 0.8, -0.8, -0.4, 0.9, 1.0, 'woodL')
    k.bx(-0.3, 0.3, -0.75, -0.55, 1.0, 1.35, 'black')
    k.fq(-0.42, 0.42, -0.953, 0.3, 0.6, 'paper')
    k.text('STAFF', 0.0, -0.956, 0.36, 0.16, 'blueD', font='display')
    k.col(-1.0, 1.0, -1.0, 1.0, 0.0, 2.45)
    k.finish('Booth', ao=ao)
    k.begin()
    for rot in (0, 90, -90):
        k.push(0, 0, rot)
        k.fq(-0.85, 0.85, -0.9, 0.95, 2.2, 'glass')
        k.pop()
    k.fq(-0.26, 0.26, -0.553, 1.04, 1.31, 'scrB')
    k.finish('Booth_Glow')


# ================================================================ maintenance gear
def build_gear(k, ao):
    rnd = random.Random(5)
    # tool cage [2, 1] (against a wall): mesh doors in a steel frame, tools and boxes inside
    k.begin()
    k.bx(-0.95, 0.95, -0.35, 0.45, 0.0, 0.08, 'steelD')
    for (x, y) in ((-0.95, -0.35), (0.95, -0.35), (-0.95, 0.45), (0.95, 0.45)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 2.0, 'steelD', ink=False)
    k.bx(-0.98, 0.98, -0.38, 0.48, 2.0, 2.05, 'steelD')
    for x0, x1, z0, z1, c in ((-0.85, -0.35, 0.08, 0.6, 'crim'), (-0.25, 0.4, 0.08, 0.4, 'hazard'), (0.5, 0.85, 0.08, 0.9, 'steel'),
                              (-0.8, 0.8, 1.0, 1.04, 'woodL'), (-0.7, -0.2, 1.04, 1.4, 'blue'), (0.1, 0.6, 1.04, 1.3, 'mart')):
        k.bx(x0, x1, -0.2, 0.35, z0, z1, c)
    for s in (-1, 1):
        k.qy(-0.92, 0.92, 0.08, 1.98, -0.351, -1, 'graph') if s < 0 else None
    for j in range(5):
        x = -0.75 + j * 0.37
        k.bx(x - 0.01, x + 0.01, -0.37, -0.35, 0.08, 1.98, 'steel', ink=False)
    k.col(-0.98, 0.98, -0.38, 0.48, 0.0, 2.05)
    k.finish('ToolCage', ao=ao)
    # cable drum (1 cell): a wooden reel with black cable
    k.begin()
    for s in (-1, 1):
        k.cyl(-0.33 if s < 0 else 0.27, 0.0, 0.45, 0.45, 0.45, 0.06, 'wood', seg=10, rot=(0, 90, 0))
    k.cyl(-0.27, 0.0, 0.45, 0.3, 0.3, 0.54, 'black', seg=10, rot=(0, 90, 0), caps=False)
    k.col(-0.35, 0.35, -0.45, 0.45, 0.0, 0.9)
    k.finish('Drum', ao=ao)
    # track trolley [2, 1]: a steel frame on four flanged wheels, rails and clips stacked on it
    k.begin()
    k.bx(-0.9, 0.9, -0.42, 0.42, 0.3, 0.42, 'hazard')
    for x in (-0.65, 0.65):
        for s in (-1, 1):
            k.cyl(x, s * 0.42 - (0.05 if s > 0 else 0.0), 0.16, 0.16, 0.16, 0.05, 'graph', seg=8, rot=(90, 0, 0))
    for j, y in enumerate((-0.25, 0.0, 0.25)):
        k.bx(-0.85, 0.85, y - 0.04, y + 0.04, 0.42, 0.54, 'rail', ink=False)
    k.bx(-0.3, 0.3, -0.3, 0.3, 0.54, 0.8, 'black')
    k.col(-0.9, 0.9, -0.45, 0.45, 0.0, 0.8)
    k.finish('Trolley', ao=ao)
    # cones (1 cell): three traffic cones, one stack
    k.begin()
    for (x, y) in ((-0.2, -0.15), (0.22, 0.1)):
        k.bx(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.0, 0.04, 'black', ink=False)
        k.cyl(x, y, 0.04, 0.15, 0.03, 0.62, 'kiosk', seg=8)
        k.cyl(x, y, 0.3, 0.1, 0.09, 0.08, 'paper', seg=8, ink=False, caps=False)
    k.col(-0.4, 0.42, -0.35, 0.3, 0.0, 0.66)
    k.finish('Cones', ao=ao)
    # electrical cabinets [2, 1] (against a wall): two grey cabinets, warning signs, LEDs (glow)
    k.begin()
    for x0 in (-0.95, 0.02):
        k.bx(x0, x0 + 0.93, -0.3, 0.45, 0.0, 2.0, 'steel', cull='b')
        k.fq(x0 + 0.06, x0 + 0.87, -0.303, 0.1, 1.9, 'paintG')
        k.fq(x0 + 0.3, x0 + 0.62, -0.306, 1.5, 1.75, 'hazard')
        k.poly([(x0 + 0.38, -0.309, 1.55), (x0 + 0.54, -0.309, 1.55), (x0 + 0.46, -0.309, 1.7)], 'black', (0, -1, 0))
        k.bx(x0 + 0.8, x0 + 0.84, -0.33, -0.3, 0.9, 1.1, 'graph', ink=False)
    for x0 in (-0.95, 0.02):
        DET.elec_cab(k, x0)
    k.col(-0.95, 0.95, -0.3, 0.45, 0.0, 2.0)
    k.finish('ElecCab', ao=ao)
    k.begin()
    for x0 in (-0.95, 0.02):
        for j, c in enumerate(('leaf', 'amberL', 'leaf')):
            k.fq(x0 + 0.2 + j * 0.1, x0 + 0.26 + j * 0.1, -0.309, 1.25, 1.3, c)
    k.finish('ElecCab_Glow')
    # workbench [3, 1] (against a wall): a steel bench, a vice, tool board, parts bins
    k.begin()
    k.bx(-1.45, 1.45, -0.4, 0.4, 0.86, 0.92, 'woodD')
    k.legs4(-1.4, 1.4, -0.35, 0.38, 0.86, 'steelD', t=0.06)
    k.bx(-1.34, 1.34, -0.28, 0.3, 0.2, 0.24, 'steelD', ink=False)
    k.bx(-1.45, 1.45, 0.4, 0.46, 0.92, 2.0, 'paintG', cull='b')
    for (x, z, c) in ((-1.0, 1.5, 'crim'), (-0.6, 1.6, 'steel'), (-0.2, 1.45, 'hazard'), (0.3, 1.55, 'steelD'), (0.8, 1.5, 'blue')):
        k.bx(x - 0.04, x + 0.04, 0.33, 0.4, z - 0.25, z + 0.15, c, ink=False)
    k.bx(0.9, 1.25, -0.25, 0.05, 0.92, 1.1, 'blueD')
    k.bx(-1.3, -0.9, -0.2, 0.2, 0.92, 1.12, 'crim')
    k.col(-1.45, 1.45, -0.4, 0.46, 0.0, 0.92)
    k.finish('Workbench', ao=ao)


def build_plat(k, ao):
    build_trains(k, ao)
    build_platform(k, ao)
    build_gear(k, ao)

