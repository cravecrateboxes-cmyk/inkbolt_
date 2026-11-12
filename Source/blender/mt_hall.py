"""kit-metro ticket hall: ticket machines (wall banks and back-to-back islands), the fare gates, the DEPARTURES BOARD
(landmark), benches, bins, help points, map totems, queue barriers, planters, vending machines, the coffee cart,
advertising light boxes, the photo booth; the shops' furniture (counters, the cafe's bar and tables, gondolas,
drinks coolers, magazine racks, the freezer, stock shelves) and the ticket office's (desks, safe, lockers, the staff
table). See mt_base.py for the conventions."""
import math
import random

from mt_base import *  # noqa: F401,F403
import mt_base as B


def tvm(k, x, face=-1, body='blueD'):
    """one ticket machine 0.86 wide facing -Y (face -1) or +Y, its back at y = 0"""
    s = face
    ya, yb = sorted((0.0, s * 0.45))
    k.bx(x - 0.43, x + 0.43, ya, yb, 0.0, 1.85, body, cull='b')
    yf = s * 0.45
    k.qy(x - 0.32, x + 0.32, 1.12, 1.6, yf + s * 0.004, s, 'black')
    k.qy(x - 0.3, x + 0.3, 1.7, 1.8, yf + s * 0.004, s, 'mustard')
    k.bx(x - 0.36, x + 0.36, min(yf, yf + s * 0.12), max(yf, yf + s * 0.12), 0.92, 1.02, 'graph')
    k.qy(x + 0.1, x + 0.3, 0.6, 0.75, yf + s * 0.004, s, 'black')
    k.qy(x - 0.3, x - 0.08, 0.6, 0.8, yf + s * 0.004, s, 'steel')


def tvm_glow(k, x, face=-1):
    s = face
    k.qy(x - 0.29, x + 0.29, 1.15, 1.57, s * 0.45 + s * 0.008, s, 'scrB')
    k.qy(x - 0.24, x - 0.04, 1.42, 1.52, s * 0.45 + s * 0.012, s, 'paper')


def build_machines(k, ao):
    # wall bank [3, 1]: three machines under one lit header (their backs to the wall at Blender +Y)
    k.begin()
    k.push(0, 0.45, 0)
    for x in (-0.95, 0.0, 0.95):
        tvm(k, x)
    k.pop()
    k.bx(-1.42, 1.42, -0.0, 0.45, 1.85, 2.2, 'graph')
    k.fq(-1.3, 1.3, -0.003, 1.9, 2.15, 'blueD')
    k.text('TICKETS  TOP UP', 0.0, -0.006, 1.98, 0.13, 'paper', font='display', maxw=2.4)
    k.col(-1.42, 1.42, 0.0, 0.5, 0.0, 2.2)
    k.finish('TVM3', ao=ao)
    k.begin()
    k.push(0, 0.45, 0)
    for x in (-0.95, 0.0, 0.95):
        tvm_glow(k, x)
    k.pop()
    k.finish('TVM3_Glow')
    # island [4, 2]: two pairs back to back, map panels on the ends, a header over all
    k.begin()
    for s in (-1, 1):
        for x in (-0.95, 0.0, 0.95):
            tvm(k, x, s)
    for e in (-1, 1):
        xa, xb = sorted((e * 1.4, e * 1.9))
        k.bx(xa, xb, -0.5, 0.5, 0.0, 2.2, 'graph', cull='b')
        k.qx(-0.4, 0.4, 0.5, 1.9, e * 1.9 + e * 0.004, e, 'paper')
        for j, (c, z) in enumerate((('crim', 1.5), ('blue', 1.2), ('green', 0.9))):
            k.qx(-0.34, 0.34, z - 0.02, z + 0.02, e * 1.9 + e * 0.008, e, c)
    k.bx(-1.4, 1.4, -0.48, 0.48, 1.85, 2.15, 'graph', cull='b')
    for s in (-1, 1):
        k.qy(-1.3, 1.3, 1.9, 2.1, s * 0.483, s, 'blueD')
    k.col(-1.9, 1.9, -0.5, 0.5, 0.0, 2.2)
    k.finish('TVMIsland', ao=ao)
    k.begin()
    for s in (-1, 1):
        for x in (-0.95, 0.0, 0.95):
            tvm_glow(k, x, s)
    k.finish('TVMIsland_Glow')

    # fare gate [2, 1]: one cabinet on the unit's middle (the aisles either side), glass paddles folded open,
    # the card reader on top, the lit arrows at both ends
    for name, wide in (('FareGate', False), ('FareWide', True)):
        k.begin()
        L = 0.55
        k.bx(-0.16, 0.16, -L, L, 0.0, 1.02, 'steel', cull='b')
        k.bx(-0.17, 0.17, -L - 0.01, L + 0.01, 1.02, 1.08, 'graph')
        k.bx(-0.1, 0.1, -0.2, 0.06, 1.08, 1.12, 'hazard', ink=False)
        for e in (-1, 1):
            k.qy(-0.12, 0.12, 0.75, 0.95, e * (L + 0.003), e, 'black')
        for sx in (-1, 1):
            # paddle folded flat against the cabinet side (glass), its hinge post
            k.qx(-0.45, 0.25, 0.55, 1.0 if not wide else 1.45, sx * 0.163, sx, 'glassL')
            k.bx(sx * 0.163 - 0.02, sx * 0.163 + 0.02, 0.22, 0.28, 0.5, 1.0, 'graph', ink=False) if not wide else None
        if wide:
            k.bx(-0.06, 0.06, -0.06, 0.06, 1.12, 1.9, 'steelD', ink=False)
            k.bx(-0.3, 0.3, -0.03, 0.03, 1.9, 2.2, 'blue')
            k.text('WIDE GATE', 0.0, -0.033, 1.98, 0.09, 'paper', font='display', maxw=0.55)
        k.col(-0.17, 0.17, -L - 0.01, L + 0.01, 0.0, 1.08)
        k.finish(name, ao=ao)
    k.begin()
    for e in (-1, 1):
        k.push(0, 0, 0 if e < 0 else 180)
        k.poly([(-0.06, -0.559, 0.78), (0.06, -0.559, 0.78), (0.0, -0.559, 0.92)], 'leaf', (0, -1, 0))
        k.pop()
    k.finish('FareGate_Glow')


def build_hall_props(k, ao):
    # bench [3, 1]: perforated steel seats with arm rests on two cast legs, a low back
    k.begin()
    for x in (-1.2, 1.2):
        k.bx(x - 0.05, x + 0.05, -0.2, 0.2, 0.0, 0.42, 'graph', cull='b')
    k.bx(-1.45, 1.45, -0.24, 0.2, 0.42, 0.47, 'steel')
    k.bx(-1.45, 1.45, 0.18, 0.24, 0.47, 0.85, 'steel', cull='b')
    for x in (-0.5, 0.5):
        k.bx(x - 0.03, x + 0.03, -0.18, 0.18, 0.47, 0.62, 'graph', ink=False)
    for x in (-1.0, -0.2, 0.6):
        k.uq(x, x + 0.4, -0.18, 0.14, 0.473, 'steelD')
    k.col(-1.45, 1.45, -0.24, 0.24, 0.0, 0.47)
    k.col(-1.45, 1.45, 0.18, 0.24, 0.47, 0.85)
    k.finish('Bench', ao=ao)
    # bin (1 cell)
    k.begin()
    k.cyl(0, 0, 0.0, 0.24, 0.24, 0.85, 'steelD', seg=10)
    k.cyl(0, 0, 0.85, 0.26, 0.24, 0.12, 'steel', seg=10)
    k.fq(-0.1, 0.1, -0.243, 0.62, 0.75, 'mart')
    k.col(-0.26, 0.26, -0.26, 0.26, 0.0, 0.97)
    k.finish('Bin', ao=ao)
    # help point (1 cell): a slim blue pillar with the intercom, the lit sign on top
    k.begin()
    k.bx(-0.18, 0.18, -0.12, 0.12, 0.0, 1.9, 'blueD', cull='b')
    k.bx(-0.22, 0.22, -0.14, 0.14, 1.9, 2.25, 'blue')
    k.fq(-0.1, 0.1, -0.123, 1.2, 1.45, 'graph')
    k.fq(-0.06, 0.06, -0.126, 1.0, 1.1, 'crim')
    k.col(-0.22, 0.22, -0.14, 0.14, 0.0, 2.25)
    k.finish('HelpPt', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.push(0, 0, 0 if s < 0 else 180)
        k.fq(-0.19, 0.19, -0.143, 1.95, 2.2, 'paper')
        k.text('HELP', 0.0, -0.146, 2.02, 0.12, 'blueD', font='display')
        k.pop()
    k.finish('HelpPt_Glow')
    # map totem (1 cell): double-sided, the roundel on top
    k.begin()
    k.bx(-0.42, 0.42, -0.12, 0.12, 0.0, 2.1, 'graph', cull='b')
    for s in (-1, 1):
        k.qy(-0.36, 0.36, 0.7, 1.95, s * 0.123, s, 'paper')
        for j, (c, z) in enumerate((('crim', 1.6), ('blue', 1.35), ('green', 1.1), ('mustard', 0.9))):
            k.qy(-0.3, 0.3, z - 0.02, z + 0.02, s * 0.127, s, c)
    k.bx(-0.04, 0.04, -0.04, 0.04, 2.1, 2.3, 'steelD', cull='b', ink=False)
    k.cyl(0, -0.04, 2.55, 0.25, 0.25, 0.08, 'crim', seg=14, rot=(90, 0, 0))
    k.bx(-0.33, 0.33, -0.05, 0.05, 2.48, 2.62, 'blue')
    k.col(-0.42, 0.42, -0.12, 0.12, 0.0, 2.1)
    k.finish('MapTotem', ao=ao)
    # queue barrier [3, 1]: four chrome posts and their blue belts
    k.begin()
    for x in (-1.3, -0.43, 0.43, 1.3):
        k.cyl(x, 0, 0.0, 0.16, 0.16, 0.03, 'steelD', seg=8, ink=False)
        k.cyl(x, 0, 0.03, 0.03, 0.03, 0.95, 'chrome', seg=6)
    for (a, b) in ((-1.3, -0.43), (-0.43, 0.43), (0.43, 1.3)):
        k.bx(a, b, -0.008, 0.008, 0.82, 0.92, 'blue', ink=False)
    k.col(-1.32, 1.32, -0.05, 0.05, 0.0, 0.95)
    k.finish('QueueBar', ao=ao)
    # planter (1 cell): a terrazzo tub, a leafy shrub
    k.begin()
    rnd = random.Random(3)
    k.cyl(0, 0, 0.0, 0.36, 0.42, 0.6, 'terrD', seg=10)
    k.cyl(0, 0, 0.6, 0.36, 0.36, 0.02, 'woodD', seg=10, ink=False)
    for i in range(4):
        a = i / 4 * 6.283
        k.sph(math.cos(a) * 0.18, math.sin(a) * 0.18, 1.05 + rnd.uniform(-0.1, 0.15), 0.32, 'leaf', seg=(6, 4))
    k.sph(0, 0, 1.45, 0.3, 'leaf', seg=(6, 4))
    k.col(-0.42, 0.42, -0.42, 0.42, 0.0, 0.6)
    k.finish('Plant', ao=ao)
    # vending machine (1 cell, front -Y)
    k.begin()
    k.bx(-0.45, 0.45, -0.38, 0.4, 0.0, 1.9, 'crim', cull='b')
    k.fq(-0.38, 0.12, -0.383, 0.75, 1.8, 'graph')
    k.fq(0.18, 0.38, -0.383, 1.2, 1.5, 'black')
    k.fq(-0.38, 0.38, -0.383, 0.15, 0.5, 'black')
    k.text('FIZZBOLT', 0.0, -0.383, 0.58, 0.1, 'paper', font='display')
    k.col(-0.45, 0.45, -0.38, 0.4, 0.0, 1.9)
    k.finish('Vend', ao=ao)
    k.begin()
    k.fq(-0.35, 0.09, -0.386, 0.78, 1.77, 'glassL')
    rnd = random.Random(8)
    for j in range(5):
        z = 0.85 + j * 0.19
        for i in range(4):
            k.fq(-0.33 + i * 0.105, -0.26 + i * 0.105, -0.389, z, z + 0.12, rnd.choice(['crim', 'blue', 'foodY', 'leaf']))
    k.finish('Vend_Glow')
    # coffee cart [2, 1]: a timber cart on wheels with a canopy, the machine on top
    k.begin()
    k.bx(-0.9, 0.9, -0.4, 0.4, 0.25, 1.0, 'cafe', cull='b')
    k.fq(-0.8, 0.8, -0.403, 0.4, 0.9, 'woodL')
    k.text('COGWHEEL', 0.0, -0.406, 0.6, 0.15, 'cafe', font='display')
    k.bx(-0.95, 0.95, -0.45, 0.45, 1.0, 1.05, 'woodD')
    k.bx(-0.5, 0.0, -0.1, 0.3, 1.05, 1.45, 'chrome')
    k.bx(0.3, 0.7, -0.2, 0.3, 1.05, 1.3, 'glassL')
    for x in (-0.85, 0.85):
        k.bx(x - 0.03, x + 0.03, 0.3, 0.36, 1.05, 2.1, 'graph', ink=False)
    k.bx(-1.0, 1.0, -0.5, 0.5, 2.1, 2.2, 'kiosk')
    for x in (-0.65, 0.65):
        k.cyl(x - 0.03, 0.0, 0.15, 0.15, 0.15, 0.06, 'black', seg=8, rot=(0, 90, 0))
    k.col(-0.95, 0.95, -0.45, 0.45, 0.0, 1.05)
    k.finish('CoffeeCart', ao=ao)
    # advertising light box [2, 1]: double-sided, on a plinth
    k.begin()
    k.bx(-0.95, 0.95, -0.18, 0.18, 0.0, 0.25, 'granite')
    k.bx(-0.95, 0.95, -0.15, 0.15, 0.25, 2.35, 'graph', cull='b')
    k.col(-0.95, 0.95, -0.18, 0.18, 0.0, 2.35)
    k.finish('LightBox', ao=ao)
    k.begin()
    for s, (bg, word, c) in ((-1, ('scrB', 'SKYLARK', 'paper')), (1, ('purple', 'OPERA NIGHTS', 'foodY'))):
        k.push(0, 0, 0 if s < 0 else 180)
        k.fq(-0.85, 0.85, -0.153, 0.35, 2.25, bg)
        k.text(word, 0.0, -0.156, 1.75, 0.3, c, font='display', maxw=1.5)
        k.fq(-0.6, 0.6, -0.156, 0.6, 1.4, 'paper' if s < 0 else 'mustard')
        k.pop()
    k.finish('LightBox_Glow')
    # photo booth [2, 1] (against a wall): the cabin, its curtain, the sample photos panel
    k.begin()
    k.bx(-0.95, 0.95, -0.55, 0.45, 0.0, 2.15, 'mustard', cull='b')
    k.fq(-0.85, -0.05, -0.553, 0.25, 1.85, 'crimD')
    k.fq(0.08, 0.85, -0.553, 1.0, 1.75, 'paper')
    for (x, z) in ((0.15, 1.4), (0.5, 1.4), (0.15, 1.08), (0.5, 1.08)):
        k.fq(x, x + 0.28, -0.556, z, z + 0.28, 'scrB')
    k.text('PHOTOS', 0.0, -0.553, 1.92, 0.14, 'crimD', font='display')
    k.col(-0.95, 0.95, -0.55, 0.45, 0.0, 2.15)
    k.finish('PhotoBooth', ao=ao)


# ================================================================ the departures board (landmark) [10, 2]
ROWS = [('BAYSIDE', '2'), ('NORTH PARK', '4'), ('HARBOUR', '6'), ('OLD TOWN', '9'), ('AIRPORT', '11')]


def build_board(k, ao):
    k.begin()
    # the granite plinth with a timber seat all round (cover at seat height)
    k.bx(-5.0, 5.0, -1.0, 1.0, 0.0, 0.42, 'granite')
    k.bx(-4.9, 4.9, -0.9, 0.9, 0.42, 0.47, 'woodL', cull='b')
    k.bx(-0.6, 0.6, -0.6, 0.6, 0.47, 0.75, 'granite', cull='b')
    # two steel legs and the board (double-sided, 8.6 x 2.3 m), a clock and the roundel on top
    for x in (-3.9, 3.9):
        k.bx(x - 0.18, x + 0.18, -0.18, 0.18, 0.47, 2.68, 'graph', cull='bt')
    k.bx(-4.3, 4.3, -0.35, 0.35, 2.8, 5.1, 'black')
    k.bx(-4.35, 4.35, -0.38, 0.38, 5.1, 5.22, 'steelD')
    k.bx(-4.35, 4.35, -0.38, 0.38, 2.68, 2.8, 'steelD')
    for s in (-1, 1):
        y = s * 0.353
        k.qy(-4.1, 4.1, 4.55, 4.95, y, s, 'blueD')
        for j in range(len(ROWS)):
            z = 4.4 - j * 0.32
            k.qy(-4.1, 4.1, z - 0.27, z, y, s, 'graph')
    k.cyl(0, -0.06, 5.7, 0.5, 0.5, 0.12, 'black', seg=16, rot=(90, 0, 0))
    k.bx(-0.06, 0.06, -0.06, 0.06, 5.22, 5.2 + 0.05, 'steelD', ink=False)
    k.col(-5.0, 5.0, -1.0, 1.0, 0.0, 0.47)
    for x in (-3.9, 3.9):
        k.col(x - 0.18, x + 0.18, -0.18, 0.18, 0.47, 2.8)
    k.col(-0.6, 0.6, -0.6, 0.6, 0.47, 0.75)
    k.finish('Landmark_Board', ao=ao)
    k.begin()
    for s in (-1, 1):
        k.push(0, 0, 0 if s < 0 else 180)
        y = -0.357
        k.text('DEPARTURES', -3.95, y, 4.65, 0.24, 'paper', font='display', align='l')
        k.text('PLATFORM  MINS', 3.95, y, 4.65, 0.16, 'paper', font='display', align='r')
        for j, (dest, mins) in enumerate(ROWS):
            z = 4.4 - j * 0.32
            k.text(dest, -3.95, y, z - 0.22, 0.17, 'amberL', font='display', align='l')
            k.text(mins, 3.95, y, z - 0.22, 0.17, 'amberL', font='display', align='r')
            k.fq(1.9, 2.2, y, z - 0.22, z - 0.05, 'crim' if j % 2 == 0 else 'blue')
        # the clock face over the board
        yc = -0.125
        k.poly([(math.cos(a / 16 * 6.283) * 0.45, yc, 5.76 + math.sin(a / 16 * 6.283) * 0.45) for a in range(16)], 'paper', (0, -1, 0))
        k.poly([(-0.02, yc - 0.004, 5.76), (0.02, yc - 0.004, 5.76), (0.02, yc - 0.004, 6.12), (-0.02, yc - 0.004, 6.12)], 'black', (0, -1, 0))
        k.poly([(-0.02, yc - 0.008, 5.76), (0.02, yc - 0.008, 5.76), (0.24, yc - 0.008, 5.92), (0.21, yc - 0.008, 5.95)], 'black', (0, -1, 0))
        k.pop()
    k.finish('Landmark_Board_Glow')


# ================================================================ shops and the ticket office
def goods(k, rnd, x0, x1, y0, y1, z, h, colors, face=-1):
    """a row of goods on a shelf: blocks of mixed width and height, coloured fronts"""
    x = x0
    while x < x1 - 0.06:
        w = min(x1 - x, rnd.uniform(0.18, 0.4))
        hh = rnd.uniform(h * 0.6, h)
        k.bx(x + 0.01, x + w - 0.01, y0, y1, z, z + hh, rnd.choice(colors), ink=False, cull='bk' if face < 0 else 'bf')
        x += w


def build_shop(k, ao):
    rnd = random.Random(11)
    SNACK = ['crim', 'foodY', 'blue', 'kiosk', 'mart', 'purple', 'pink']
    # shop counter [3, 1] (back to the wall at +Y): a panelled counter, the till, a sweets rack on the front
    k.begin()
    k.bx(-1.45, 1.45, -0.35, 0.3, 0.0, 0.95, 'woodD', cull='b')
    k.bx(-1.5, 1.5, -0.4, 0.32, 0.95, 1.0, 'granite')
    k.fq(-1.4, 1.4, -0.353, 0.12, 0.85, 'woodL')
    k.bx(0.6, 1.0, -0.15, 0.2, 1.0, 1.15, 'graph')
    k.bx(0.65, 0.95, 0.05, 0.12, 1.15, 1.45, 'black')
    goods(k, rnd, -1.3, 0.3, -0.3, 0.1, 1.0, 0.22, SNACK)
    k.col(-1.5, 1.5, -0.4, 0.32, 0.0, 1.0)
    k.finish('Counter', ao=ao)
    # cafe bar [4, 2] (back to the wall at +Y): the back bar with shelves and grinders, the counter with the espresso
    # machine and the pastry case
    k.begin()
    k.bx(-2.0, 2.0, 0.5, 1.0, 0.0, 0.95, 'cafe', cull='b')
    k.bx(-2.0, 2.0, 0.85, 1.0, 0.95, 2.0, 'woodD', cull='b')
    for z in (1.35, 1.7):
        k.bx(-1.9, 1.9, 0.7, 0.85, z - 0.03, z, 'woodL', ink=False)
        goods(k, rnd, -1.8, 1.8, 0.72, 0.84, z, 0.22, ['cream', 'paper', 'cafe', 'mustard'])
    k.bx(-2.0, 2.0, -0.6, 0.05, 0.0, 1.0, 'cafe', cull='b')
    k.bx(-2.05, 2.05, -0.65, 0.08, 1.0, 1.05, 'woodL')
    k.fq(-1.9, 1.9, -0.603, 0.1, 0.9, 'woodD')
    k.bx(-1.6, -0.6, -0.3, 0.0, 1.05, 1.5, 'chrome')
    k.bx(-1.5, -0.7, -0.33, -0.3, 1.15, 1.25, 'graph', ink=False)
    k.bx(0.2, 1.8, -0.55, 0.0, 1.05, 1.4, 'woodL')
    k.col(-2.05, 2.05, -0.65, 1.0, 0.0, 1.05)
    k.finish('CafeBar', ao=ao)
    k.begin()
    k.fq(0.25, 1.75, -0.553, 1.08, 1.37, 'glassL')
    for i in range(5):
        k.fq(0.32 + i * 0.29, 0.52 + i * 0.29, -0.556, 1.1, 1.2, rnd.choice(['foodY', 'cafe', 'pink', 'mustard']))
    k.finish('CafeBar_Glow')
    # cafe table [2, 2]: a round table, three chairs
    k.begin()
    k.cyl(0, 0, 0.0, 0.25, 0.25, 0.03, 'black', seg=8, ink=False)
    k.cyl(0, 0, 0.03, 0.04, 0.04, 0.7, 'black', seg=6, caps=False)
    k.cyl(0, 0, 0.73, 0.4, 0.4, 0.04, 'woodL', seg=12)
    for i in range(3):
        a = i / 3 * 6.283 + 0.4
        k.chair(math.cos(a) * 0.72, math.sin(a) * 0.72, math.degrees(a) + 90, 'cafe')
    k.col(-0.4, 0.4, -0.4, 0.4, 0.0, 0.77)
    k.finish('CafeTable', ao=ao)
    # gondola [3, 1]: double-sided shelving, goods on four shelves each side
    k.begin()
    k.bx(-1.41, 1.41, -0.38, 0.38, 0.0, 0.12, 'graph', cull='b')
    k.bx(-1.41, 1.41, -0.04, 0.04, 0.12, 1.6, 'steel', cull='b')
    for e in (-1, 1):
        k.bx(e * 1.45 - (0.04 if e > 0 else 0.0), e * 1.45 + (0.04 if e < 0 else 0.0), -0.4, 0.4, 0.0, 1.62, 'mart')
    for z in (0.12, 0.5, 0.88, 1.26):
        k.bx(-1.37, 1.37, -0.36, 0.36, z - 0.02, z, 'steel', ink=False, cull='b') if z > 0.2 else None
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.05, s * 0.35))
            goods(k, rnd, -1.35, 1.35, y0, y1, z, 0.3, SNACK, face=s)
    k.col(-1.45, 1.45, -0.4, 0.4, 0.0, 1.62)
    k.finish('Gondola', ao=ao)
    # drinks cooler [2, 1] (back to the wall at +Y): two glass doors (the lit inside is the glow)
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.5, 0.0, 2.05, 'steelD', cull='b')
    k.bx(-0.95, 0.95, -0.42, 0.5, 2.05, 2.25, 'mart')
    k.text('COLD DRINKS', 0.0, -0.423, 2.08, 0.14, 'paper', font='display')
    for x in (-0.5, 0.42):
        k.bx(x - 0.02, x + 0.02, -0.46, -0.4, 0.9, 1.4, 'chrome', ink=False)
    k.col(-0.95, 0.95, -0.42, 0.5, 0.0, 2.25)
    k.finish('Cooler', ao=ao)
    k.begin()
    k.fq(-0.88, -0.03, -0.403, 0.15, 1.95, 'glassL')
    k.fq(0.03, 0.88, -0.403, 0.15, 1.95, 'glassL')
    for z in (0.35, 0.8, 1.25, 1.7):
        for i in range(8):
            x = -0.84 + i * 0.215
            if -0.06 < x < 0.06:
                continue
            k.fq(x, x + 0.13, -0.406, z, z + 0.3, rnd.choice(['crim', 'blue', 'leaf', 'foodY', 'kiosk']))
    k.finish('Cooler_Glow')
    # magazine rack [2, 1] (back to the wall at +Y): sloped tiers of covers
    k.begin()
    k.bx(-0.95, 0.95, 0.2, 0.45, 0.0, 1.9, 'woodD', cull='b')
    for j, z in enumerate((0.4, 0.8, 1.2, 1.6)):
        k.bx(-0.92, 0.92, -0.05 - j * 0.0, 0.2, z - 0.04, z, 'woodL', ink=False)
        x = -0.88
        while x < 0.85:
            w = 0.22
            k.qy(x, x + w - 0.02, z, z + 0.3, 0.1 + 0.004, -1, rnd.choice(SNACK + ['paper', 'scrB']))
            x += w
    k.bx(-0.95, 0.95, -0.25, 0.2, 0.0, 0.3, 'woodD', cull='b')
    k.col(-0.95, 0.95, -0.25, 0.45, 0.0, 1.9)
    k.finish('MagRack', ao=ao)
    # magazine island [3, 1]: a low double-sided rack, newspapers on top
    k.begin()
    k.bx(-1.45, 1.45, -0.35, 0.35, 0.0, 0.9, 'woodD', cull='b')
    for s in (-1, 1):
        for j, z in enumerate((0.15, 0.5)):
            x = -1.38
            while x < 1.35:
                k.qy(x, x + 0.24, z, z + 0.32, s * 0.353, s, rnd.choice(SNACK + ['paper']))
                x += 0.27
    k.bx(-1.4, 1.4, -0.3, 0.3, 0.9, 0.98, 'paper')
    k.col(-1.45, 1.45, -0.35, 0.35, 0.0, 0.98)
    k.finish('MagIsland', ao=ao)
    # chest freezer [2, 1]
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.4, 0.0, 0.85, 'tileW', cull='b')
    k.bx(-0.95, 0.95, -0.42, 0.42, 0.85, 0.92, 'steelD')
    k.fq(-0.85, 0.85, -0.403, 0.4, 0.7, 'scrB')
    k.text('ICE CREAM', 0.0, -0.406, 0.48, 0.13, 'paper', font='display')
    k.col(-0.95, 0.95, -0.42, 0.42, 0.0, 0.92)
    k.finish('Freezer', ao=ao)
    # stock shelf [2, 1] (back to the wall): steel shelving with boxes
    k.begin()
    for x in (-0.95, 0.91):
        k.bx(x, x + 0.04, -0.2, 0.45, 0.0, 2.0, 'steelD', ink=False)
    for z in (0.1, 0.65, 1.2, 1.75):
        k.bx(-0.91, 0.91, -0.18, 0.43, z - 0.03, z, 'steel', ink=False)
        goods(k, rnd, -0.88, 0.88, -0.15, 0.4, z, 0.4, ['woodL', 'cream', 'kiosk', 'paper', 'stone'])
    k.col(-0.95, 0.95, -0.2, 0.45, 0.0, 2.0)
    k.finish('Shelf', ao=ao)
    # office desk [2, 1] (back to the window wall at +Y): the clerk's side at -Y with the chair, the monitor facing it
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.4, 0.72, 0.76, 'woodL')
    k.bx(-0.95, -0.55, -0.38, 0.38, 0.0, 0.72, 'woodD', cull='b')
    k.bx(0.88, 0.93, -0.38, 0.38, 0.0, 0.72, 'woodD', cull='b', ink=False)
    k.bx(-0.3, 0.3, 0.1, 0.16, 0.76, 1.15, 'black')
    k.bx(-0.06, 0.06, 0.16, 0.22, 0.76, 0.9, 'graph', ink=False)
    k.bx(0.4, 0.75, -0.2, 0.15, 0.76, 0.9, 'graph')
    k.chair(0.0, -0.7, 180, 'seat')
    k.col(-0.95, 0.95, -0.4, 0.4, 0.0, 0.76)
    k.finish('OfficeDesk', ao=ao)
    k.begin()
    k.fq(-0.27, 0.27, 0.097, 0.8, 1.12, 'scrB')
    k.finish('OfficeDesk_Glow')
    # safe (1 cell)
    k.begin()
    k.bx(-0.4, 0.4, -0.35, 0.4, 0.0, 1.1, 'graph')
    k.cyl(0.1, -0.35, 0.65, 0.1, 0.1, 0.05, 'chrome', seg=8, rot=(90, 0, 0))
    k.fq(-0.3, -0.1, -0.353, 0.55, 0.75, 'steel')
    k.col(-0.4, 0.4, -0.35, 0.4, 0.0, 1.1)
    k.finish('Safe', ao=ao)
    # staff lockers [2, 1] (back to the wall)
    k.begin()
    k.bx(-0.95, 0.95, -0.2, 0.45, 0.0, 1.95, 'steelD', cull='b')
    for i in range(4):
        a, b = -0.93 + i * 0.465, -0.93 + (i + 1) * 0.465 - 0.02
        k.fq(a, b, -0.203, 0.08, 1.9, 'paintG')
        k.fq(a + 0.1, b - 0.1, -0.206, 1.6, 1.75, 'steelD')
    k.col(-0.95, 0.95, -0.2, 0.45, 0.0, 1.95)
    k.finish('Lockers', ao=ao)
    # staff table [2, 2]: a table, four chairs, mugs
    k.begin()
    k.bx(-0.75, 0.75, -0.55, 0.55, 0.72, 0.76, 'paintL')
    k.legs4(-0.72, 0.72, -0.52, 0.52, 0.72, 'steelD', t=0.04)
    for (x, y, d) in ((-0.35, -0.85, 0), (0.35, -0.85, 0), (-0.35, 0.85, 180), (0.35, 0.85, 180)):
        k.chair(x, y, d, 'blue')
    for (x, y) in ((-0.3, -0.2), (0.25, 0.15)):
        k.cyl(x, y, 0.76, 0.05, 0.05, 0.1, 'crim', seg=6)
    k.col(-0.75, 0.75, -0.55, 0.55, 0.0, 0.76)
    k.finish('StaffTable', ao=ao)


def build_hall(k, ao):
    build_machines(k, ao)
    build_hall_props(k, ao)
    build_board(k, ao)
    build_shop(k, ao)
