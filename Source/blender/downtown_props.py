"""kit-downtown props: the vehicles kit-parking has not got, battle staging, street furniture, market stalls and the
three landmarks.

Vehicles (front = Blender -Y). The taxi and the police cruiser are kit-parking's Sedan (repainted yellow / white by
the theme) with an add-on piece placed on the same transform (theme symbol option `with`): TaxiTop (roof sign,
checker bands) and PoliceKit (light bar, black doors, POLICE lettering, push bar); both use parking_cars.SEDAN and
the Sedan's built-in skew, so they sit on its body exactly. Bus (city bus), TruckOver (a box truck on its side as a
roadblock) are whole pieces.
"""
import math

from mathutils import Matrix

from downtown_base import *  # noqa: F401,F403
import parking_cars as PC
import downtown_detail as DD

S = PC.SEDAN
SEDAN_T = (3.0, 0.08, 0.1)   # the parking Sedan's skew and offset (parking_cars.build_cars specs)


# ================================================================ vehicles
def build_vehicles(pal, ao):
    hw = S['W'] / 2
    # taxi add-on: roof sign, checker bands along both flanks
    m = new(pal)
    m.parent = rz(*SEDAN_T)
    m.bx(-0.36, 0.36, 0.02, 0.32, S['roof'], S['roof'] + 0.06, 'ink')
    m.bx(-0.33, 0.33, 0.05, 0.29, S['roof'] + 0.06, S['roof'] + 0.3, 'pYellow')
    for (y, f) in ((0.046, 'y-'), (0.294, 'y+')):
        txt(m, 'TAXI', 0.0, y, S['roof'] + 0.18, 0.13, 'ink', face=f, font='display', maxw=0.56)
    for sx in (-1, 1):
        x = sx * (hw + 0.012)
        for k in range(20):
            y0 = -1.0 + k * 0.11
            (rq if sx > 0 else lq)(m, x, y0, y0 + 0.11, 0.6 + (0.06 if k % 2 else 0.0), 0.66 + (0.06 if k % 2 else 0.0), 'ink')
    make('TaxiTop', m, ao)
    # police add-on: light bar, black doors, POLICE on the rear doors, push bar
    m = new(pal)
    m.parent = rz(*SEDAN_T)
    m.bx(-0.6, 0.6, 0.0, 0.3, S['roof'], S['roof'] + 0.05, 'ink')
    for k, c in enumerate(('pipeR', 'pWhite', 'pBlue')):
        m.bx(-0.58 + k * 0.39, -0.21 + k * 0.39, 0.03, 0.27, S['roof'] + 0.05, S['roof'] + 0.16, c, hull='none' if c == 'pWhite' else 'full')
    for sx in (-1, 1):
        x = sx * (hw + 0.012)
        f = rq if sx > 0 else lq
        f(m, x, -1.03, 0.18, 0.36, 0.86, 'ink')
        txt(m, 'POLICE', x + sx * 0.003, 0.72, 0.62, 0.15, 'navy', face='x+' if sx > 0 else 'x-', font='display', maxw=0.9)
        f(m, x, 1.3, 2.1, 0.62, 0.68, 'navy')
    for sx in (-1, 1):
        m.bx(sx * 0.42 - 0.04, sx * 0.42 + 0.04, -2.58, -2.36, 0.25, 0.85, 'ink')
    m.bx(-0.5, 0.5, -2.6, -2.52, 0.55, 0.65, 'ink')
    m.bx(-0.5, 0.5, -2.6, -2.52, 0.75, 0.83, 'ink')
    a = math.radians(SEDAN_T[0])
    make('PoliceKit', m, ao, cols=[rot_box(0.24, 1.0, SEDAN_T[0], 0.85, SEDAN_T[1] + 2.47 * math.sin(a), SEDAN_T[2] - 2.47 * math.cos(a))])
    # city bus (3 x 12): white body, teal skirt and window band, three doors on the right, destination sign
    m = new(pal)
    m.parent = rz(1.5)
    L, W2, H = 11.6, 1.25, 3.05
    for (y, sx) in ((-3.6, -1), (-3.6, 1), (3.3, -1), (3.3, 1)):
        wheel(m, sx * (W2 + 0.02), y, 0.5, 0.3)
    m.bx(-W2, W2, -L / 2, L / 2, 0.35, H, 'pWhite', bevel=True)
    m.bx(-W2 - 0.01, W2 + 0.01, -L / 2 - 0.01, L / 2 + 0.01, 0.35, 0.95, 'pTeal', hull='none', cull='tb')
    for sx in (-1, 1):
        x = sx * (W2 + 0.004)
        f = rq if sx > 0 else lq
        f(m, x, -L / 2 + 0.3, L / 2 - 0.3, 1.25, 2.5, 'ink')
        k = 0
        y = -L / 2 + 0.5
        while y < L / 2 - 0.9:
            f(m, x + sx * 0.003, y, y + 1.0, 1.32, 2.43, 'glass')
            y += 1.12
            k += 1
        f(m, x, -L / 2 + 0.3, L / 2 - 0.3, 2.55, 2.68, 'pTeal')
        if sx > 0:   # doors on the curb side
            for yd in (-5.5, -0.4):
                f(m, x + sx * 0.012, yd, yd + 1.1, 0.4, 2.55, 'mull')
                f(m, x + sx * 0.016, yd + 0.08, yd + 0.52, 0.5, 2.45, 'glass')
                f(m, x + sx * 0.016, yd + 0.58, yd + 1.02, 0.5, 2.45, 'glass')
    fq(m, -1.15, 1.15, -L / 2 - 0.004, 1.15, 2.7, 'ink')                                  # windscreen
    fq(m, -1.05, 1.05, -L / 2 - 0.008, 1.22, 2.35, 'glass')
    fq(m, -1.0, 1.0, -L / 2 - 0.008, 2.42, 2.66, 'ink')
    txt(m, '7  CROSSTOWN', 0.0, -L / 2 - 0.012, 2.54, 0.14, 'litA', font='display', maxw=1.8)
    for sx in (-1, 1):
        fq(m, sx * 0.85 - 0.18, sx * 0.85 + 0.18, -L / 2 - 0.004, 0.55, 0.75, 'light')
        bq(m, sx * 0.9 - 0.14, sx * 0.9 + 0.14, L / 2 + 0.004, 0.6, 0.95, 'red')
    bq(m, -1.0, 1.0, L / 2 + 0.004, 1.4, 2.6, 'ink')
    m.bx(-0.9, 0.9, -1.8, 1.4, H, H + 0.3, 'galv')                                        # roof unit
    make('Bus', m, ao, bevel=0.03, cols=[rot_box(L, 2 * W2 + 0.06, 1.5, H)])
    # box truck on its side across the street (4 x 8): roof toward -X, underside (chassis, wheels) toward +X
    m = new(pal)
    m.parent = rz(-4.0)
    m.bx(-1.25, 1.0, -1.6, 3.7, 0.0, 2.25, 'pWhite')                         # cargo box
    for k in range(3):
        uq(m, -1.15 + k * 0.7, -0.75 + k * 0.7, -1.4, 3.5, 2.255, ('steel', 'cream', 'steel')[k])
    fq(m, -1.2, 0.95, -1.604, 0.6, 1.0, 'pipeR')                                          # stripe on the box front
    m.bx(-1.15, 0.55, -3.7, -1.65, 0.05, 2.15, 'cone')                        # cab
    fq(m, -1.05, 0.35, -3.704, 0.2, 1.95, 'ink')
    fq(m, -0.95, 0.25, -3.708, 0.3, 1.85, 'glass')
    disc(m, -0.6, -3.0, 2.154, 0.25, 'glassL', seg=6, jag=[1.0, 0.5, 1.1, 0.6, 0.9, 0.4])
    m.bx(1.0, 1.25, -3.5, 3.5, 0.6, 1.6, 'steelD')                                        # chassis rails
    for y in (-2.8, 1.9, 2.95):
        for z in (0.15, 1.75):
            m.cy((1.25, y, z), 0.48, 0.48, 0.32, 'tire', seg=8, rot=(0, 90, 0))
            m.cy((1.57, y, z), 0.26, 0.26, 0.02, 'chrome', seg=6, rot=(0, 90, 0), hull='none')
    for (x, y, c) in ((-1.8, 4.3, 'cardb'), (-1.5, 5.0, 'cardb'), (-2.3, 4.8, 'wood')):  # spilled cartons
        m.bx(x - 0.3, x + 0.3, y - 0.25, y + 0.25, 0.0, 0.45, c)
    disc(m, -0.3, 0.0, 0.006, 3.2, 'burnt', seg=10, sx=0.55, jag=[1.0, 0.85, 1.1, 0.9, 1.05, 0.8, 1.0, 0.9, 1.1, 0.85])
    make('TruckOver', m, ao, bevel=0.02, cols=[rot_box(7.4, 2.5, -4.0, 2.25, 0.0, 0.05), rot_box(1.2, 1.1, -4.0, 0.45, -1.9, 4.65)])


# ================================================================ battle staging
def build_battle(pal, ao):
    # sandbag wall: one 1 m run cell, three courses
    m = new(pal)
    sandbag_wall(m, -0.5, 0.5, 0.0, rows=3, seams=True)
    make('Sandbags', m, ao, cols=[box(-0.5, -0.19, 0, 0.5, 0.19, 0.6)])
    # sandbag nest (3 x 3): a U of bags open at the back, a machine gun on a tripod, ammo cans, spent brass
    m = new(pal)
    P0 = m.parent
    for (deg, dx, dy, x0, x1) in ((0, 0, -1.25, -1.45, 1.45), (90, -1.25, 0.05, -1.05, 1.15), (-90, 1.25, 0.05, -1.15, 1.05)):
        m.parent = P0 @ rz(deg, dx, dy)
        sandbag_wall(m, x0, x1, 0.0, rows=3)
    m.parent = P0
    m.bm_((0.0, -0.4, 0.0), (0.0, -0.55, 0.78), 0.04, 'steelD')                          # tripod
    m.bm_((-0.3, 0.0, 0.0), (0.0, -0.5, 0.78), 0.04, 'steelD')
    m.bm_((0.3, 0.0, 0.0), (0.0, -0.5, 0.78), 0.04, 'steelD')
    m.bx(-0.1, 0.1, -0.75, -0.2, 0.75, 0.92, 'ink')                                       # gun body
    m.cy((0.0, -0.75, 0.84), 0.03, 0.03, 0.75, 'ink', seg=6, rot=(90, 0, 0), hull='none')
    m.bx(-0.05, 0.05, -0.25, 0.05, 0.7, 0.86, 'olive')
    for (x, y) in ((0.6, 0.6), (0.85, 0.3)):
        m.bx(x - 0.15, x + 0.15, y - 0.08, y + 0.08, 0.0, 0.2, 'olive')
    for i in range(6):
        m.cy((-0.5 + i * 0.13, 0.3 - (i % 2) * 0.12, 0.0), 0.012, 0.012, 0.05, 'pYellow', seg=5, rot=(90, 0, i * 30), hull='none')
    make('Nest', m, ao, cols=[box(-1.45, -1.44, 0, 1.45, -1.06, 0.6), box(-1.44, -1.05, 0, -1.06, 1.15, 0.6), box(1.06, -1.05, 0, 1.44, 1.15, 0.6)])
    # czech hedgehog: three crossed steel angles on base plates
    m = new(pal)
    for (a, b) in (((-0.6, -0.1, 0.05), (0.6, 0.1, 1.15)), ((0.1, -0.6, 0.05), (-0.1, 0.6, 1.15)), ((-0.45, 0.45, 0.6), (0.45, -0.45, 0.6))):
        m.bm_(a, b, 0.09, 'rust' if a[2] > 0.3 else 'steelD')
    make('Hedgehog', m, ao, cols=[box(-0.42, -0.42, 0, 0.42, 0.42, 1.15)])
    # barbed wire coil along X between two pickets (no collision: robots and the player brush through it)
    m = new(pal)
    m.bx(-0.47, -0.43, -0.02, 0.02, 0.0, 0.85, 'rust', hull='none', cull='b')      # one picket per metre
    for k in range(4):
        x = -0.5 + k * 0.25
        for (z0, z1) in ((0.1, 0.75), (0.75, 0.1)):
            m.bm_((x, -0.18, z0), (x + 0.25, 0.18, z1), 0.012, 'steelD', hull='none')
        m.bm_((x, 0.18, 0.4), (x + 0.25, -0.18, 0.5), 0.012, 'galv', hull='none')
    make('Wire', m, ao)
    # police tape between stanchions (no collision)
    m = new(pal)
    m.cy((-0.45, 0, 0.0), 0.15, 0.15, 0.04, 'ink', seg=6, hull='none')     # one stanchion per metre, at its west end
    m.cy((-0.45, 0, 0.04), 0.025, 0.025, 0.95, 'cone', seg=5, hull='none')
    for k in range(5):
        x0 = -0.5 + k * 0.2
        for (y, f) in ((-0.004, fq), (0.004, bq)):
            f(m, x0, x0 + 0.2, y, 0.86, 0.94, 'lineY' if k % 2 else 'ink')
    make('Tape', m, ao)
    # ammo / supply crates (2 x 1)
    m = new(pal)
    for (x0, x1, z0, h, c) in ((-0.95, -0.05, 0.0, 0.5, 'olive'), (0.05, 0.95, 0.0, 0.5, 'olive'), (-0.6, 0.3, 0.5, 0.4, 'woodD')):
        m.bx(x0, x1, -0.32, 0.32, z0, z0 + h, c)
        fq(m, x0 + 0.1, x1 - 0.1, -0.324, z0 + h * 0.35, z0 + h * 0.65, 'pYellow' if c == 'olive' else 'cream')
    make('Crates', m, ao, bevel=0.015, cols=[box(-0.95, -0.32, 0, 0.95, 0.32, 0.5), box(-0.6, -0.32, 0.5, 0.3, 0.32, 0.9)])
    # burn barrel: a rusty drum with fire in it
    m = new(pal)
    m.cy((0, 0, 0), 0.3, 0.3, 0.88, 'rust', seg=8)
    for z in (0.28, 0.6):
        m.cy((0, 0, z), 0.31, 0.31, 0.04, 'burnt', seg=8, hull='none', caps=False)
    for k, (dx, dy, h, c) in enumerate(((0.0, 0.0, 0.55, 'litA'), (0.1, -0.08, 0.38, 'cone'), (-0.1, 0.08, 0.32, 'pYellow'))):
        m.cy((dx, dy, 0.8 + 0.01 * k), 0.16, 0.0, h, c, seg=5, hull='none')
    make('BurnBarrel', m, ao, cols=[box(-0.3, -0.3, 0, 0.3, 0.3, 0.88)])
    # rubble heap (cover): broken slabs and bricks
    m = new(pal)
    for (x0, y0, x1, y1, z1, c, d) in ((-0.48, -0.4, 0.3, 0.35, 0.35, 'conc', 8), (-0.2, -0.1, 0.45, 0.45, 0.6, 'concF', -12), (-0.45, 0.1, 0.0, 0.45, 0.5, 'brickT', 20)):
        P0 = m.parent
        m.parent = rz(d)
        m.bx(x0, x1, y0, y1, 0.0, z1, c)
        m.parent = P0
    make('RubbleHeap', m, ao, cols=[box(-0.45, -0.42, 0, 0.45, 0.45, 0.55)])


# ================================================================ street furniture
def build_street(pal, ao):
    # street lamp: pole on the curb, arm out over the road (-Y), a cobra head
    m = new(pal)
    m.cy((0, 0.25, 0), 0.12, 0.1, 0.5, 'mull', seg=6)
    m.cy((0, 0.25, 0.5), 0.07, 0.05, 6.4, 'steel', seg=6)
    m.bm_((0, 0.25, 6.7), (0, -1.6, 7.0), 0.07, 'steel')
    m.bx(-0.16, 0.16, -2.05, -1.45, 6.86, 7.06, 'steel')
    dq(m, -0.12, 0.12, -1.98, -1.52, 6.855, 'light')
    DD.lamp_detail(m)
    make('Lamp', m, ao, cols=[box(-0.12, 0.13, 0, 0.12, 0.37, 2.0)])
    # traffic signal: pole, a mast arm out over the lanes (-Y) with two signal heads, a ped signal, a push button
    m = new(pal)
    m.cy((0, 0.3, 0), 0.14, 0.12, 0.4, 'mull', seg=6)
    m.cy((0, 0.3, 0.4), 0.08, 0.07, 5.6, 'lineY', seg=6)
    m.bm_((0, 0.3, 5.6), (0, -5.2, 5.75), 0.08, 'lineY')
    for y in (-2.2, -4.6):
        m.bx(-0.17, 0.17, y - 0.15, y + 0.15, 4.75, 5.68, 'lineY')
        for k, c in enumerate(('red', 'litA', 'exitG')):
            z = 5.4 - k * 0.3
            fq(m, -0.11, 0.11, y - 0.154, z - 0.11, z + 0.11, c if k == 0 else 'mull')
            m.bx(-0.14, 0.14, y - 0.3, y - 0.15, z + 0.1, z + 0.13, 'lineY', hull='none')
    m.bx(-0.17, 0.17, 0.06, 0.18, 2.4, 2.85, 'lineY')
    fq(m, -0.13, 0.13, 0.056, 2.45, 2.8, 'ink')
    fq(m, -0.08, 0.06, 0.053, 2.55, 2.72, 'cone')
    m.bx(-0.07, 0.07, 0.17, 0.2, 1.05, 1.25, 'lineY', hull='none')
    make('Signal', m, ao, cols=[box(-0.14, 0.16, 0, 0.14, 0.44, 2.0)])
    # street tree in an iron grate
    m = new(pal)
    uq(m, -0.6, 0.6, -0.6, 0.6, 0.06, 'ink')
    for k in range(4):
        uq(m, -0.5 + k * 0.27, -0.42 + k * 0.27, -0.5, 0.5, 0.065, 'mull')
    m.cy((0, 0, 0), 0.12, 0.09, 2.4, 'trunk', seg=6)
    for (dx, dy, z, r, c) in ((0.0, 0.0, 3.4, 1.2, 'leaf'), (0.5, 0.3, 2.85, 0.8, 'leafD'), (-0.3, -0.25, 4.1, 0.8, 'leafD')):
        m.sp((dx, dy, z), r, c, seg=(7, 4))
    make('Tree', m, ao, cols=[box(-0.13, -0.13, 0, 0.13, 0.13, 2.2)])
    # fire hydrant
    m = new(pal)
    m.cy((0, 0, 0), 0.16, 0.16, 0.08, 'pipeR', seg=8)
    m.cy((0, 0, 0.08), 0.12, 0.12, 0.5, 'pipeR', seg=8)
    m.cy((0, 0, 0.58), 0.14, 0.06, 0.14, 'pipeR', seg=8)
    m.cy((0.0, 0.1, 0.38), 0.06, 0.06, 0.1, 'chrome', seg=6, rot=(-90, 0, 0))
    for sx in (-1, 1):
        m.cy((sx * 0.1, 0, 0.42), 0.045, 0.045, 0.08, 'chrome', seg=6, rot=(0, sx * 90, 0))
    DD.hydrant_detail(m)
    make('Hydrant', m, ao, cols=[box(-0.16, -0.16, 0, 0.16, 0.16, 0.72)])
    # mailbox
    m = new(pal)
    for x in (-0.18, 0.18):
        m.bx(x - 0.03, x + 0.03, -0.2, 0.2, 0.0, 0.35, 'navy', hull='none', cull='b')
    m.bx(-0.24, 0.24, -0.26, 0.26, 0.35, 1.1, 'navy')
    m.prism([(-0.26, 1.1), (0.26, 1.1), (0.18, 1.25), (-0.18, 1.25)], -0.24, 0.24, ['navy'])
    fq(m, -0.16, 0.16, -0.264, 0.88, 0.95, 'steel')
    fq(m, -0.12, 0.12, -0.264, 0.55, 0.75, 'pWhite')
    make('Mailbox', m, ao, cols=[box(-0.24, -0.26, 0, 0.24, 0.26, 1.25)])
    # news boxes (two coin boxes on a rail)
    m = new(pal)
    for (x, c) in ((-0.24, 'exitG'), (0.24, 'pBlue')):
        m.bx(x - 0.2, x + 0.2, -0.18, 0.18, 0.0, 0.25, 'steelD', hull='none', cull='b')
        m.bx(x - 0.22, x + 0.22, -0.2, 0.2, 0.25, 0.95, c)
        fq(m, x - 0.15, x + 0.15, -0.204, 0.55, 0.85, 'glassL')
        fq(m, x - 0.12, x + 0.12, -0.208, 0.6, 0.8, 'paper')
    make('NewsBoxes', m, ao, cols=[box(-0.46, -0.2, 0, 0.46, 0.2, 0.95)])
    # litter basket
    m = new(pal)
    m.cy((0, 0, 0), 0.24, 0.27, 0.9, 'exitG', seg=8)
    m.cy((0, 0, 0.9), 0.28, 0.28, 0.05, 'mull', seg=8)
    m.cy((0, 0, 0.95), 0.12, 0.08, 0.1, 'paper', seg=5, hull='none')
    make('Basket', m, ao, cols=[box(-0.27, -0.27, 0, 0.27, 0.27, 0.95)])
    # parking meters (a pair)
    m = new(pal)
    for x in (-0.2, 0.2):
        m.cy((x, 0, 0), 0.03, 0.03, 1.05, 'mull', seg=5, hull='none')
        m.bx(x - 0.08, x + 0.08, -0.06, 0.06, 1.05, 1.35, 'steel')
        fq(m, x - 0.05, x + 0.05, -0.064, 1.2, 1.3, 'glassL')
    make('Meters', m, ao, cols=[box(-0.28, -0.06, 0.95, 0.28, 0.06, 1.35), box(-0.24, -0.04, 0, 0.24, 0.04, 0.95)])
    # bench (2 x 1): cast-iron ends, wooden slats
    m = new(pal)
    for x in (-0.85, 0.85):
        m.bx(x - 0.04, x + 0.04, -0.25, 0.25, 0.0, 0.45, 'mull')
        m.bx(x - 0.04, x + 0.04, 0.18, 0.26, 0.45, 0.9, 'mull')
    for k in range(3):
        m.bx(-0.95, 0.95, -0.24 + k * 0.15, -0.12 + k * 0.15, 0.42, 0.47, 'wood', hull='none')
    for k in range(2):
        m.bx(-0.95, 0.95, 0.22, 0.27, 0.56 + k * 0.17, 0.68 + k * 0.17, 'wood', hull='none')
    DD.bench_detail(m)
    make('Bench', m, ao, cols=[box(-0.95, -0.25, 0, 0.95, 0.27, 0.9)])
    # bus shelter (4 x 2): posts, roof, glass back panel, bench, an ad panel at one end; front = -Y (toward the road)
    m = new(pal)
    for x in (-1.85, 1.85):
        for y in (-0.55, 0.65):
            m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 2.45, 'mull', hull='none', cull='b')
    m.bx(-2.0, 2.0, -0.85, 0.8, 2.45, 2.55, 'mull')
    m.bx(-1.95, 1.95, -0.8, 0.75, 2.55, 2.6, 'pTeal', hull='none', cull='b')
    for (y, f) in ((0.62, fq), (0.68, bq)):
        f(m, -1.8, 1.8, y, 0.25, 2.3, 'glass')
    m.bx(-1.8, 1.8, 0.59, 0.61, 0.25, 0.3, 'mull', hull='none')
    m.bx(1.81, 1.89, -0.5, 0.6, 0.15, 2.3, 'mull')
    for (x, f) in ((1.805, lq), (1.895, rq)):
        f(m, x, -0.45, 0.55, 0.3, 2.2, 'pYellow')
    txt(m, 'RIDE TRANSIT', 1.801, 0.05, 1.5, 0.16, 'navy', face='x-', font='display', maxw=0.9)
    m.bx(-1.5, 1.2, 0.2, 0.55, 0.45, 0.5, 'wood')
    for x in (-1.3, 1.0):
        m.bx(x - 0.03, x + 0.03, 0.3, 0.45, 0.0, 0.45, 'mull', hull='none', cull='b')
    m.bx(-2.0, -1.7, -0.85, -0.75, 2.6, 2.95, 'navy')
    txt(m, 'BUS', -1.85, -0.854, 2.77, 0.13, 'pWhite', font='display', maxw=0.26)
    DD.busstop_detail(m)
    make('BusStop', m, ao, cols=[box(-1.8, 0.58, 0, 1.8, 0.7, 2.3), box(1.81, -0.5, 0, 1.89, 0.6, 2.3), box(-1.5, 0.2, 0, 1.2, 0.55, 0.5)])
    # newsstand (2 x 3): green kiosk, awning, magazine racks on the front
    m = new(pal)
    m.bx(-0.95, 0.95, -1.2, 1.45, 0.0, 2.4, 'exitG')
    m.bx(-1.05, 1.05, -1.6, 1.55, 2.4, 2.55, 'mull')
    m.prism([(-1.25, 2.38), (-1.75, 2.0), (-1.75, 1.92), (-1.25, 2.3)], -1.0, 1.0, ['exitG', 'pWhite', 'exitG', 'pWhite'], skip=(3,))
    fq(m, -0.85, 0.85, -1.204, 0.15, 2.15, 'mull')
    for k in range(3):
        z = 0.35 + k * 0.6
        for j in range(5):
            x = -0.78 + j * 0.32
            fq(m, x, x + 0.26, -1.208, z, z + 0.42, ('pipeR', 'lineY', 'pBlue', 'pink', 'paper', 'cone')[(j + k * 2) % 6])
    m.bx(-0.9, 0.9, -1.45, -1.2, 0.85, 0.9, 'mull', hull='none')
    for k in range(3):
        m.bx(-0.8 + k * 0.55, -0.4 + k * 0.55, -1.42, -1.22, 0.9, 0.94, 'paper', hull='none', cull='b')
    txt(m, 'NEWS', 0.0, -1.604, 2.47, 0.11, 'lineY', font='display', maxw=0.8)
    DD.newsstand_detail(m)
    make('Newsstand', m, ao, cols=[box(-0.95, -1.45, 0, 0.95, 1.45, 2.4)])


# ================================================================ market stalls (3 x 2), front = -Y
def stall(m, canopy, goods):
    for x in (-1.35, 1.35):
        for y in (-0.75, 0.75):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 2.3 if y > 0 else 2.1, 'mull', hull='none', cull='b')
    m.prism([(-0.95, 2.1), (0.85, 2.35), (0.85, 2.42), (-0.95, 2.17)], -1.45, 1.45, canopy, hull='full')
    m.bx(-1.4, 1.4, -0.7, 0.3, 0.75, 0.82, 'woodD')
    m.bx(-1.35, 1.35, 0.25, 0.3, 0.0, 0.75, 'woodD', hull='none')
    for i in range(6):
        x = -1.3 + i * 0.44
        c = goods[i % len(goods)]
        m.bx(x, x + 0.4, -0.65, -0.2, 0.82, 0.98, 'wood', hull='none', cull='b')
        m.bx(x + 0.03, x + 0.37, -0.62, -0.23, 0.98, 1.04, c, hull='none', cull='b')
        m.bx(x + 0.03, x + 0.37, -0.2, 0.25, 0.82, 0.96 + 0.06 * (i % 2), goods[(i + 2) % len(goods)], hull='none', cull='b')


def build_stalls(pal, ao):
    m = new(pal)
    stall(m, ['pipeR', 'pWhite', 'pipeR', 'pWhite', 'pipeR', 'pWhite'], ('pipeR', 'lineY', 'leaf', 'cone', 'exitG', 'violet'))
    for (x, y, c) in ((-0.9, 0.7, 'cardb'), (-0.4, 0.75, 'cardb')):
        m.bx(x - 0.22, x + 0.22, y - 0.18, y + 0.18, 0.0, 0.35, c)
    make('Stall_Fruit', m, ao, cols=[box(-1.4, -0.7, 0, 1.4, 0.3, 1.0), box(-1.12, 0.52, 0, -0.18, 0.93, 0.35)])
    m = new(pal)
    stall(m, ['exitG', 'cream', 'exitG', 'cream', 'exitG', 'cream'], ('pink', 'pYellow', 'violet', 'pWhite', 'pipeR', 'leaf'))
    for (x, c) in ((0.8, 'pink'), (1.15, 'pYellow')):
        m.cy((x, -0.95, 0.0), 0.14, 0.12, 0.35, 'galv', seg=6)
        m.sp((x, -0.95, 0.5), 0.17, c, seg=(6, 4))
    make('Stall_Flowers', m, ao, cols=[box(-1.4, -0.7, 0, 1.4, 0.3, 1.0), box(0.66, -1.09, 0, 1.29, -0.81, 0.4)])


# ================================================================ landmarks
def build_landmarks(pal, ao):
    # Commerce Avenue checkpoint (6 x 4): a sandbagged police booth, a raised boom, a floodlight mast, sandbags
    m = new(pal)
    m.bx(-2.9, -0.9, -1.0, 1.0, 0.0, 2.5, 'pWhite')                                      # booth
    m.bx(-3.05, -0.75, -1.15, 1.15, 2.5, 2.7, 'navy')
    for (y, f) in ((-1.004, fq), (1.004, bq)):
        f(m, -2.7, -1.1, y, 1.1, 2.1, 'ink')
        f(m, -2.62, -1.18, y - 0.004 if y < 0 else y + 0.004, 1.18, 2.02, 'glass')
    lq(m, -2.904, -0.7, 0.7, 1.1, 2.1, 'glass')
    txt(m, 'POLICE', -1.9, -1.154, 2.6, 0.13, 'pWhite', font='display', maxw=1.6)
    m.bx(-0.85, -0.55, -0.15, 0.15, 0.0, 1.1, 'lineY')                                    # boom post
    P0 = m.parent
    m.parent = P0 @ Matrix.Translation((-0.7, 0.0, 1.0)) @ Matrix.Rotation(math.radians(-62), 4, 'Y')
    for k in range(6):
        m.bx(0.15 + k * 0.6, 0.75 + k * 0.6, -0.05, 0.05, -0.06, 0.06, 'pipeR' if k % 2 == 0 else 'pWhite', hull='full')
    m.parent = P0
    m.cy((2.4, 1.3, 0.0), 0.1, 0.08, 5.9, 'steelD', seg=6)                               # floodlight mast
    m.bx(1.9, 2.9, 1.2, 1.4, 5.9, 6.0, 'steelD')
    for x in (2.05, 2.75):
        m.bx(x - 0.18, x + 0.18, 1.05, 1.3, 5.75, 6.15, 'mull')
        fq(m, x - 0.14, x + 0.14, 1.046, 5.8, 6.1, 'light')
    m.parent = P0 @ Matrix.Translation((1.0, -1.6, 0))
    sandbag_wall(m, -0.9, 1.9, 0.0, rows=4, seams=True)
    m.parent = P0 @ rz(90, 0.0, 0.0) @ Matrix.Translation((0.2, -2.9, 0))
    sandbag_wall(m, -0.75, 0.6, 0.0, rows=3)
    m.parent = P0
    m.bx(-0.3, 0.3, 0.6, 1.0, 0.0, 0.6, 'olive')
    make('Landmark_Checkpoint', m, ao, cols=[box(-2.9, -1.0, 0, -0.9, 1.0, 2.5), box(-0.85, -0.15, 0, -0.55, 0.15, 1.1),
                                              box(2.3, 1.2, 0, 2.5, 1.4, 2.0), box(0.1, -1.79, 0, 2.9, -1.41, 0.8),
                                              box(-3.09, -0.55, 0, -2.71, 0.8, 0.6), box(-0.3, 0.6, 0, 0.3, 1.0, 0.6)])
    # Liberty Square monument (8 x 8): three granite tiers, a bronze founder with his arm raised, a plaque, lamps
    m = new(pal)
    for (h, z0, z1, c) in ((3.9, 0.0, 0.35, 'limeD'), (2.9, 0.35, 0.75, 'lime'), (1.5, 0.75, 3.0, 'lime')):
        m.bx(-h, h, -h, h, z0, z1, c)
    m.bx(-1.65, 1.65, -1.65, 1.65, 3.0, 3.25, 'limeD')
    fq(m, -1.0, 1.0, -1.504, 1.4, 2.4, 'bronze')
    txt(m, 'FOUNDERS', 0.0, -1.508, 2.08, 0.24, 'cream', font='display', maxw=1.8)
    txt(m, '1871', 0.0, -1.508, 1.65, 0.18, 'cream', font='display', maxw=1.0)
    for sx in (-1, 1):   # the figure: legs, coat, torso, head, the raised arm, a scroll in the other hand
        m.bx(sx * 0.2 - 0.12, sx * 0.2 + 0.12, -0.15, 0.15, 3.25, 4.25, 'bronze')
    m.prism([(-0.35, 4.0), (0.35, 4.0), (0.3, 5.2), (-0.3, 5.2)], -0.48, 0.48, ['bronze'])
    m.bx(-0.32, 0.32, -0.25, 0.25, 5.2, 5.75, 'bronze')
    m.sp((0, 0, 6.05), 0.25, 'bronze', seg=(6, 4))
    m.bm_((0.38, 0.0, 5.55), (0.7, -0.3, 6.7), 0.16, 'bronze')
    m.bm_((-0.4, 0.0, 5.55), (-0.55, -0.2, 4.6), 0.15, 'bronze')
    m.cy((-0.58, -0.3, 4.45), 0.07, 0.07, 0.4, 'cream', seg=6, rot=(0, 90, 0))
    m.sp((0, 0, 6.32), 0.12, 'terra', seg=(6, 3), scale=(1.6, 1.6, 0.5))
    for (x, y) in ((-3.3, -3.3), (3.3, -3.3), (-3.3, 3.3), (3.3, 3.3)):
        m.cy((x, y, 0.35), 0.06, 0.05, 3.2, 'mull', seg=6)
        m.sp((x, y, 3.7), 0.24, 'cream', seg=(6, 3))
    for (deg, y) in ((0, -2.4), (180, -2.4)):   # sandbag walls on the middle tier, front and back
        m.parent = rz(deg) @ Matrix.Translation((0, y, 0.75))
        sandbag_wall(m, -1.2, 1.2, 0.0, rows=2)
    m.parent = Matrix.Identity(4)
    make('Landmark_Monument', m, ao, bevel=0.03, cols=[box(-3.9, -3.9, 0, 3.9, 3.9, 0.35), box(-2.9, -2.9, 0, 2.9, 2.9, 0.75),
                                                         box(-1.65, -1.65, 0, 1.65, 1.65, 3.25)])
    # Market Street tram (3 x 14): a stalled streetcar, cream over red, a long window band, a pantograph, doors open
    m = new(pal)
    m.parent = rz(0.6)
    L, W2 = 13.2, 1.3
    m.bx(-W2, W2, -L / 2, L / 2, 0.55, 1.6, 'pipeR', bevel=True)
    m.bx(-W2, W2, -L / 2, L / 2, 1.6, 3.15, 'cream', bevel=True)
    m.bx(-W2 + 0.15, W2 - 0.15, -L / 2 + 0.6, L / 2 - 0.6, 3.15, 3.45, 'pipeR')
    for sx in (-1, 1):
        x = sx * (W2 + 0.004)
        f = rq if sx > 0 else lq
        f(m, x, -L / 2 + 0.4, L / 2 - 0.4, 1.75, 2.75, 'ink')
        y = -L / 2 + 0.55
        while y < L / 2 - 0.9:
            f(m, x + sx * 0.003, y, y + 0.9, 1.82, 2.68, 'glass')
            y += 1.02
        f(m, x, -L / 2 + 0.2, L / 2 - 0.2, 1.62, 1.68, 'lineY')
        if sx > 0:
            for yd in (-3.6, 2.4):
                f(m, x + sx * 0.008, yd, yd + 1.2, 0.6, 2.75, 'interior')
    for (y, f, s) in ((-L / 2 - 0.004, fq, -1), (L / 2 + 0.004, bq, 1)):
        f(m, -1.0, 1.0, y, 1.75, 2.8, 'ink')
        f(m, -0.9, 0.9, y + s * 0.004, 1.82, 2.6, 'glass')
        f(m, -0.8, 0.8, y + s * 0.004, 2.85, 3.08, 'mull')
    txt(m, 'MARKET ST', 0.0, -L / 2 - 0.012, 2.96, 0.13, 'litA', font='display', maxw=1.5)
    for y in (-4.4, 4.4):
        m.bx(-1.0, 1.0, y - 1.0, y + 1.0, 0.12, 0.55, 'steelD')
    m.bm_((0, -0.6, 3.45), (0, 0.7, 4.3), 0.05, 'steelD')
    m.bm_((0.07, 1.8, 3.45), (0.07, 0.7, 4.3), 0.05, 'steelD')
    m.bx(-0.6, 0.6, 0.62, 0.78, 4.3, 4.36, 'steelD', hull='none')
    m.parent = Matrix.Identity(4)
    make('Landmark_Tram', m, ao, bevel=0.03, cols=[rot_box(L, 2 * W2 + 0.04, 0.6, 3.15)])


def build_props(pal, ao):
    build_vehicles(pal, ao)
    build_battle(pal, ao)
    build_street(pal, ao)
    build_stalls(pal, ao)
    build_landmarks(pal, ao)
