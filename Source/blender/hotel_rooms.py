"""INKBOLT kit-hotel: the open suites of the guest floor (one 6 x 6 m piece per suite; tools/hotel_zones.py).

A suite stands behind a corridor wall line with a two-cell doorway in its middle ('n', wall.passage): its front
(Blender -Y, y = -3) faces the doorway, the facade's suite windows (SuiteWin) close its back (y = +3) and one-cell
party walls ('#', no module) its sides. The piece draws the carpet, the papered walls 2 cm inside the wall cells (so
the corridor modules' back faces stay hidden), the ceiling at 3.3 m with a cove and a pendant, and the furniture.
Furniture stands against the side walls and under the window, so a 1.6 m aisle runs from the door to the window:
cover to fight round, room for robots to follow. Collision: one box per piece of furniture, cut to what is drawn.
"""
import math

from hotel_base import (RH, srt, txt, disc, dining_chair, armchair, sofa, side_table, table_lamp, floor_lamp, flowers,
                        painting, sconce, rug, coffee_table, books, suitcase, legs4)

WX, WY0, WY1 = 2.98, -2.98, 2.98
DOOR = 1.0            # the doorway runs x -1 .. 1 (the two middle cells of the front wall line)


def shell(k, paper, accent, carpet):
    # carpet and a border
    k.qz(-WX, WX, WY0, WY1, 0.012, 1, carpet)
    k.qz(-WX + 0.25, WX - 0.25, WY0 + 0.25, WY1 - 0.25, 0.015, 1, 'silk')
    k.qz(-WX + 0.32, WX - 0.32, WY0 + 0.32, WY1 - 0.32, 0.018, 1, carpet)
    # walls (inward faces): sides, the front either side of the doorway and over it
    for s in (-1, 1):
        k.qx(WY0, WY1, 0.0, RH, s * WX, -s, paper)
        k.bx(min(s * WX, s * (WX - 0.03)), max(s * WX, s * (WX - 0.03)), WY0, WY1, 0.0, 0.14, 'walnut2', ink=False)
        k.bx(min(s * WX, s * (WX - 0.035)), max(s * WX, s * (WX - 0.035)), WY0, WY1, 0.86, 0.9, accent, ink=False)
        k.bx(min(s * WX, s * (WX - 0.08)), max(s * WX, s * (WX - 0.08)), WY0, WY1, RH - 0.16, RH, 'cream', ink=False)
    for (x0, x1) in ((-WX, -DOOR), (DOOR, WX)):
        k.qy(x0, x1, 0.0, RH, WY0, 1, paper)
    for s in (-1, 1):
        a0, a1 = srt(s * (WX - 0.035), s * (DOOR + 0.12))
        k.bx(a0, a1, WY0, WY0 + 0.03, 0.0, 0.14, 'walnut2', ink=False)
        k.bx(a0, a1, WY0, WY0 + 0.035, 0.86, 0.9, accent, ink=False)
    k.qy(-DOOR, DOOR, 2.7, RH, WY0, 1, paper)
    k.bx(-WX + 0.08, WX - 0.08, WY0, WY0 + 0.08, RH - 0.16, RH, 'cream', ink=False)
    for s in (-1, 1):   # door architrave on the room side
        x0, x1 = srt(s * DOOR, s * (DOOR + 0.12))
        k.bx(x0, x1, WY0, WY0 + 0.05, 0.0, 2.7, 'ivory')
    k.bx(-DOOR - 0.12, DOOR + 0.12, WY0, WY0 + 0.05, 2.7, 2.82, 'ivory')
    # ceiling, a cove light and a small gilt pendant
    k.qz(-WX, WX, WY0, WY1, RH, -1, 'cream')
    disc(k, 0, 0.4, RH - 0.004, 0.35, 'silk2', n=12, up=False)
    k.cyl(0, 0.4, RH - 0.5, 0.05, 0.05, 0.5, 'gold', seg=5, ink=False)
    k.cyl(0, 0.4, RH - 0.75, 0.32, 0.18, 0.25, 'shade', seg=10)
    disc(k, 0, 0.4, RH - 0.753, 0.3, 'glow', n=10, up=False)


def bed(k, cols, x, y, w, l, deg, linen='white', throw='navy', head='silk2'):
    """A bed with its headboard toward local +X of the push frame (length along X)."""
    k.push(x, y, deg)
    hl, hw = l / 2, w / 2
    k.bx(-hl, hl, -hw, hw, 0.12, 0.42, 'walnut')
    k.bx(-hl + 0.03, hl - 0.03, -hw + 0.03, hw - 0.03, 0.42, 0.62, linen)
    k.bx(-hl + 0.02, -hl + 0.6, -hw + 0.02, hw - 0.02, 0.62, 0.66, throw)
    for i in range(2 if w > 1.4 else 1):
        yy = (-hw / 2 + i * hw) if w > 1.4 else 0.0
        k.m.box((hl - 0.3, yy, 0.78), (0.2, min(0.75, w * 0.42), 0.34), 'ivory', rot=(0, 18, 0), bevel=False)
        k._mark(True)
    k.bx(hl, hl + 0.1, -hw - 0.05, hw + 0.05, 0.12, 1.45, head)
    k.bx(hl - 0.02, hl + 0.12, -hw - 0.07, hw + 0.07, 1.45, 1.52, 'gold', ink=False)
    for i in range(int(w / 0.35)):
        yy = -hw + 0.25 + i * 0.35
        if yy > hw - 0.2:
            break
        k.qx(yy - 0.012, yy + 0.012, 0.75, 1.35, hl - 0.003, -1, 'gold')
    k.pop()
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    xs = [x + c * px - s * py for px in (-hl, hl + 0.1) for py in (-hw - 0.05, hw + 0.05)]
    ys = [y + s * px + c * py for px in (-hl, hl + 0.1) for py in (-hw - 0.05, hw + 0.05)]
    k.col(min(xs), max(xs), min(ys), max(ys), 0, 0.66)


def nightstand(k, cols, x, y):
    k.bx(x - 0.24, x + 0.24, y - 0.22, y + 0.22, 0, 0.55, 'walnut')
    k.qy(x - 0.2, x + 0.2, 0.32, 0.48, y - 0.223, -1, 'walnut2')
    k.bx(x - 0.03, x + 0.03, y - 0.24, y - 0.22, 0.38, 0.42, 'gold', ink=False)
    table_lamp(k, x, y + 0.04, 0.55, 0.8)
    k.col(x - 0.24, x + 0.24, y - 0.22, y + 0.22, 0, 0.55)


def desk(k, x, y, deg, fab):
    """Writing desk against a wall (back toward local +Y), a chair, a lamp, a leather blotter, stationery."""
    k.push(x, y, deg)
    k.bx(-0.65, 0.65, -0.3, 0.3, 0.72, 0.77, 'walnut')
    k.bx(-0.6, -0.25, -0.26, 0.26, 0, 0.72, 'walnut2')
    k.bx(0.5, 0.6, -0.26, 0.26, 0, 0.72, 'walnut2')
    k.qz(-0.2, 0.35, -0.2, 0.15, 0.773, 1, 'emerald2')
    k.qz(-0.1, 0.15, -0.12, 0.08, 0.776, 1, 'ivory')
    table_lamp(k, -0.45, 0.12, 0.77, 0.8)
    dining_chair(k, 0.1, -0.55, 180, fab)
    k.pop()


def tv_console(k, x, y, deg):
    """Low walnut media console with a flat screen and a vase (back toward local +Y)."""
    k.push(x, y, deg)
    k.bx(-0.8, 0.8, -0.22, 0.22, 0.08, 0.62, 'walnut')
    for xx in (-0.4, 0.4):
        k.qy(xx - 0.36, xx + 0.36, 0.14, 0.56, -0.223, -1, 'walnut2')
    k.bx(-0.55, 0.55, 0.05, 0.1, 0.9, 1.55, 'black')
    k.qy(-0.52, 0.52, 0.93, 1.52, 0.047, -1, 'screen')
    k.bx(-0.05, 0.05, 0.05, 0.12, 0.62, 0.9, 'black', ink=False)
    flowers(k, 0.62, 0.0, 0.62, 0.6, 'white')
    k.pop()


def wardrobe(k, x, y, deg):
    """Tall walnut armoire with a minibar shelf (back toward local +Y)."""
    k.push(x, y, deg)
    k.bx(-0.55, 0.55, -0.3, 0.3, 0.0, 2.2, 'walnut')
    k.bx(-0.58, 0.58, -0.33, 0.33, 2.2, 2.3, 'walnut2')
    for xx in (-0.27, 0.27):
        k.qy(xx - 0.24, xx + 0.24, 0.2, 2.0, -0.303, -1, 'walnut2')
        k.bx(xx * 0.15 - 0.012, xx * 0.15 + 0.012, -0.33, -0.3, 1.0, 1.3, 'gold', ink=False)
    k.pop()


def suite(k, kind):
    """kind: 'King' (navy, one king bed), 'Twin' (emerald, two beds), 'Salon' (wine, a sitting-room suite)."""
    k.begin()
    paper, accent, carpet, fab = {'King': ('silk', 'navy', 'navy2', 'navy'), 'Twin': ('cream', 'emerald', 'emerald2', 'emerald'),
                                  'Salon': ('silk', 'wine', 'wine2', 'wine')}[kind]
    shell(k, paper, accent, carpet)
    C = []
    if kind == 'King':
        # king bed against the +X party wall, nightstands, a painting over it, a bench at the foot
        bed(k, C, 1.75, 0.6, 2.0, 2.2, 0)
        for y in (-0.75, 1.95):
            nightstand(k, C, 2.65, y)
        k.push(WX, 0.6, -90)
        painting(k, 0, 0, 1.6, 1.3, 0.85, scheme=0, s=-1)
        k.pop()
        k.bx(0.35, 0.6, -0.15, 1.35, 0.1, 0.45, accent)
        k.col(0.35, 0.6, -0.15, 1.35, 0, 0.45)
        # sitting corner under the window: two armchairs and a round table
        armchair(k, -2.2, 2.3, 200, 'cream')
        side_table(k, -1.4, 2.5, 0.6, 'marble', 0.28)
        flowers(k, -1.4, 2.5, 0.6, 0.7, 'rose')
        k.col(-2.65, -1.75, 1.85, 2.75, 0, 0.82)
        k.col(-1.68, -1.12, 2.22, 2.78, 0, 0.6)
        # desk on the -X wall, the TV console on the +X wall's front end, an armoire by the door
        desk(k, -2.6, -0.4, 90, fab)
        k.col(-2.95, -2.3, -1.05, 0.25, 0, 0.77)
        k.col(-2.3, -1.85, -0.75, -0.05, 0, 1.0)
        wardrobe(k, -2.62, -2.2, 90)
        k.col(-2.95, -2.3, -2.78, -1.62, 0, 2.3)
        floor_lamp(k, 2.6, 2.6)
        k.col(2.42, 2.78, 2.42, 2.78, 0, 1.6)

    elif kind == 'Twin':
        for y in (-1.0, 1.6):
            bed(k, C, 1.85, y, 1.2, 2.1, 0, throw='emerald')
        nightstand(k, C, 2.62, 0.3)
        k.push(WX, 0.3, -90)
        painting(k, 0, 0, 1.6, 0.9, 1.0, scheme=2, s=-1)
        k.pop()
        sofa(k, -2.45, 0.9, 90, 1.9, 'emerald')
        k.col(-2.9, -2.0, -0.05, 1.85, 0, 0.84)
        coffee_table(k, -1.55, 0.9, 0.6, 1.0, 0.42, 'marble')
        books(k, -1.55, 0.6, 0.42, 2, 90)
        k.col(-1.85, -1.25, 0.4, 1.4, 0, 0.42)
        tv_console(k, -2.72, -1.6, 90)
        k.col(-2.95, -2.5, -2.4, -0.8, 0, 0.62)
        floor_lamp(k, -2.6, 2.6)
        k.col(-2.78, -2.42, 2.42, 2.78, 0, 1.6)

    else:   # Salon: a sitting-room suite with a dining table for two by the window
        sofa(k, 2.45, 0.0, -90, 2.4, 'wine')
        k.col(2.0, 2.9, -1.25, 1.25, 0, 0.84)
        k.push(WX, 0.0, -90)
        painting(k, 0, 0, 1.4, 1.6, 1.1, scheme=3, s=-1)
        k.pop()
        armchair(k, 0.75, -0.6, 70, 'cream')
        armchair(k, 0.75, 0.6, 110, 'cream')
        k.col(0.3, 1.2, -1.05, -0.15, 0, 0.82)
        k.col(0.3, 1.2, 0.15, 1.05, 0, 0.82)
        coffee_table(k, 1.65, 0.0, 0.7, 1.2, 0.42, 'marble')
        flowers(k, 1.65, 0.3, 0.42, 0.7, 'red')
        books(k, 1.6, -0.3, 0.42, 3, 95)
        k.col(1.3, 2.0, -0.6, 0.6, 0, 0.42)
        # round dining table for two at the window
        k.cyl(-1.9, 2.1, 0, 0.25, 0.25, 0.04, 'gold', seg=10, ink=False)
        k.cyl(-1.9, 2.1, 0.04, 0.05, 0.05, 0.68, 'gold', seg=6, ink=False)
        k.cyl(-1.9, 2.1, 0.72, 0.5, 0.5, 0.04, 'ivory', seg=14)
        disc(k, -1.9, 2.1, 0.763, 0.48, 'white', n=14)
        for (dx, dy, deg) in ((-0.75, 0, 90), (0.75, 0, -90)):
            dining_chair(k, -1.9 + dx, 2.1 + dy, deg, fab)
        k.cyl(-1.9, 2.1, 0.76, 0.03, 0.03, 0.25, 'crystal2', seg=5, ink=False)
        k.sph(-1.9, 2.1, 1.05, 0.06, 'rose', seg=(4, 2), ink=False)
        k.col(-2.4, -1.4, 1.6, 2.6, 0, 0.76)
        k.col(-2.95, -2.4, 1.85, 2.35, 0, 1.0)
        k.col(-1.4, -0.85, 1.85, 2.35, 0, 1.0)
        desk(k, -2.6, -0.6, 90, fab)
        k.col(-2.95, -2.3, -1.25, 0.05, 0, 0.77)
        k.col(-2.3, -1.85, -0.95, -0.25, 0, 1.0)
        wardrobe(k, 2.62, -2.3, -90)
        k.col(2.3, 2.95, -2.88, -1.72, 0, 2.3)
    # sconces either side of the doorway on the room side
    for x in (-1.6, 1.6):
        sconce(k, x, WY0 + 0.003, 2.0, s=1, arms=1)
    return k
