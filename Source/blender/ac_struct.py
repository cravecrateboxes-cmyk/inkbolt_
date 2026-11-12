"""kit-academy structure: wall faces (interior paint, exterior brick) on every side of a cell, the wall art the theme's
chooser stacks on them (lockers, boards, posters, windows, trophy cases, signs sliced over several cells, restroom
doors, fountains, wall pads, scoreboard, banners; brick windows, downspouts, doors, the school name), doorways
(classroom double doors, wide glass doors, courtyard doors) and archway headers, the gate (an aluminium entrance
with a roll-down grille), trail walls, the hatch, ceiling tiles and light panels (4 m), roof bays (8 m), floor
finishes, the court lines, stairs, rails and deck columns. See ac_base.py for the conventions."""
import math
import random

from ac_base import *  # noqa: F401,F403
import ac_base as B

SIDES = (('F', 0), ('K', 180), ('R', 90), ('L', -90))
Y0 = -0.5          # the face plane of a front piece


def faces(k, ao, name, fn, glow=None):
    """build fn (drawn on the front face, y = -0.5) as one piece; the theme's wall chooser turns it to any side of a
    cell. glow(g): an unlit companion name_Glow"""
    k.begin()
    fn(k)
    k.finish(name, ao=ao)
    if glow:
        k.begin()
        glow(k)
        k.finish(name + '_Glow')


# ================================================================ finishes
def paint_i(k, z0=0.0, z1=WALL_H, x0=-0.5, x1=0.5, band=True, joints=False, y=Y0):
    """interior face: cove base, cream block with a slate / gold band, the paler upper wall over 4 m"""
    def q(a, b, c):
        a, b = max(a, z0), min(b, z1)
        if b - a > 1e-4:
            k.fq(x0, x1, y, a, b, c)
    q(0.0, 0.1, 'cove')
    if band:
        q(0.1, 1.15, 'wallC')
        q(1.15, 1.3, 'slate')
        q(1.3, 1.34, 'gold')
        q(1.34, 4.0, 'wallC')
    else:
        q(0.1, 4.0, 'wallC')
    q(4.0, 8.0, 'wallU')
    if joints:
        for z in (0.5, 2.0, 2.8, 3.6, 5.6, 6.8):
            if z0 + 0.01 < z < z1 - 0.01:
                k.fq(x0, x1, y - 0.003, z - 0.006, z + 0.006, 'joint')


def paint_x(k, z0=0.0, z1=WALL_H, x0=-0.5, x1=0.5, y=Y0, coping=True):
    """exterior face: stone base, red brick, a stone band at the floor line, soldier courses, stone coping"""
    def q(a, b, c, d=0.0):
        a, b = max(a, z0), min(b, z1)
        if b - a > 1e-4:
            k.fq(x0, x1, y - d, a, b, c)
    q(0.0, 0.6, 'stone')
    q(0.6, 3.9, 'brick')
    q(3.9, 4.1, 'stone')
    q(4.1, 7.75, 'brick')
    for z in (1.6, 2.6, 5.4, 6.6):
        q(z - 0.012, z + 0.012, 'mortar', 0.003)
    q(3.02, 3.14, 'brick2', 0.003)
    q(6.92, 7.04, 'brick2', 0.003)
    if coping:
        q(7.75, 8.0, 'stone')          # the stone coping band (flush: perpendicular faces meet at the corners)
        q(7.68, 7.7, 'stoneD', 0.003)


def scribble(k, x0, x1, z, c, rnd, n=3, y=Y0 - 0.006):
    """marker lines (painted dashes) on a board"""
    for i in range(n):
        a = x0 + rnd.uniform(0, 0.15)
        b = min(x1, a + rnd.uniform(0.25, 0.7))
        zz = z - i * 0.14
        k.fq(a, b, y, zz, zz + 0.025, c)


# ================================================================ plain faces
def build_finishes(k, ao):
    faces(k, ao, 'I', lambda k: paint_i(k))
    faces(k, ao, 'X', lambda k: paint_x(k))


# ================================================================ interior wall art
def lockers(k, c):
    """a bank of three lockers 0.15 - 2.0 m (flush, doors 3 mm proud), the wall above"""
    paint_i(k, 2.06, WALL_H, band=False)
    k.fq(-0.5, 0.5, Y0, 0.0, 0.15, 'cove')
    k.fq(-0.5, 0.5, Y0, 0.15, 2.0, 'steelD')
    for i in range(3):
        a = -0.5 + i / 3 + 0.012
        b = -0.5 + (i + 1) / 3 - 0.012
        k.fq(a, b, Y0 - 0.003, 0.17, 1.98, c)
        k.fq(a + 0.06, b - 0.06, Y0 - 0.006, 1.7, 1.9, 'steelD')
        k.fq(b - 0.08, b - 0.04, Y0 - 0.006, 0.95, 1.15, 'chrome')
    k.bx(-0.5, 0.5, Y0 - 0.05, Y0, 2.0, 2.06, 'steelD', cull='kblr', ink=False)


def whiteboard(part):
    def fn(k):
        rnd = random.Random({'L': 1, 'M': 2, 'R': 3, 'T': 4}[part])
        paint_i(k, 0.0, 0.85)
        paint_i(k, 2.25, WALL_H)
        paint_i(k, 0.85, 2.25, band=False, joints=False)
        x0 = -0.44 if part == 'L' else -0.5
        x1 = 0.44 if part == 'R' else 0.5
        k.fq(x0, x1, Y0 - 0.02, 0.92, 2.15, 'board')
        k.bx(x0 - (0.04 if part == 'L' else 0.0), x1 + (0.04 if part == 'R' else 0.0), Y0 - 0.04, Y0, 2.15, 2.2, 'chrome', cull='k')
        k.bx(x0 - (0.04 if part == 'L' else 0.0), x1 + (0.04 if part == 'R' else 0.0), Y0 - 0.1, Y0, 0.86, 0.92, 'chrome', cull='k')
        if part == 'L':
            k.bx(-0.48, -0.44, Y0 - 0.04, Y0, 0.92, 2.15, 'chrome', cull='k')
        if part == 'R':
            k.bx(0.44, 0.48, Y0 - 0.04, Y0, 0.92, 2.15, 'chrome', cull='k')
        if part == 'T':
            k.text('2X + 4 = 10', -0.42, Y0 - 0.025, 1.8, 0.12, 'navy', font='cond', align='l', maxw=0.84)
            k.text('X = 3', -0.42, Y0 - 0.025, 1.55, 0.12, 'chD', font='cond', align='l')
        else:
            scribble(k, x0 + 0.08, x1 - 0.1, 1.9, 'navy', rnd, 3, Y0 - 0.025)
        k.bx(-0.2, -0.06, Y0 - 0.09, Y0 - 0.06, 0.92, 0.95, 'chD' if part != 'R' else 'chA', ink=False)
    return fn


def corkboard(k):
    paint_i(k, 0.0, 0.95)
    paint_i(k, 2.0, WALL_H)
    paint_i(k, 0.95, 2.0, band=False, joints=False)
    k.fq(-0.46, 0.46, Y0 - 0.02, 0.96, 1.99, 'wood')
    k.fq(-0.42, 0.42, Y0 - 0.023, 1.0, 1.95, 'cork')
    rnd = random.Random(7)
    for (a, b, c0, c1, col) in ((-0.36, -0.08, 1.45, 1.85, 'paper'), (-0.02, 0.3, 1.55, 1.88, 'chE'), (0.02, 0.34, 1.08, 1.45, 'paper'),
                                (-0.34, -0.06, 1.06, 1.36, 'skyL')):
        k.fq(a, b, Y0 - 0.026, c0, c1, col)
        k.fq((a + b) / 2 - 0.015, (a + b) / 2 + 0.015, Y0 - 0.029, c1 - 0.04, c1 - 0.01, rnd.choice(['chD', 'chA', 'chC']))


def poster(word, sub, bg, fg, deco=None):
    def fn(k):
        paint_i(k)
        k.fq(-0.32, 0.32, Y0 - 0.004, 1.45, 2.3, bg)
        k.text(word, 0.0, Y0 - 0.007, 1.92, 0.22, fg, font='display', maxw=0.56)
        if sub:
            k.text(sub, 0.0, Y0 - 0.007, 1.62, 0.09, fg, font='cond', maxw=0.54)
        if deco:
            deco(k)
    return fn


def deco_star(k):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = 0.09 if i % 2 == 0 else 0.04
        pts.append((math.cos(a) * r, Y0 - 0.011, 2.19 + math.sin(a) * r))
    k.poly(pts, 'gold', (0, -1, 0))


def deco_cell(k):
    for i in range(12):
        a, b = i / 12 * 2 * math.pi, (i + 1) / 12 * 2 * math.pi
        k.poly([(0.0, Y0 - 0.01, 1.68), (math.cos(a) * 0.24, Y0 - 0.01, 1.68 + math.sin(a) * 0.17),
                (math.cos(b) * 0.24, Y0 - 0.01, 1.68 + math.sin(b) * 0.17)], 'grass', (0, -1, 0))
    for (x, z, r, c) in ((0.0, 1.68, 0.07, 'chF'), (0.12, 1.75, 0.03, 'chD'), (-0.12, 1.61, 0.03, 'chE')):
        pts = [(x + math.cos(i / 8 * 6.283) * r, Y0 - 0.013, z + math.sin(i / 8 * 6.283) * r) for i in range(8)]
        k.poly(pts, c, (0, -1, 0))


def clock(k):
    paint_i(k)
    k.push(0, Y0, 0, 2.75)
    k.cyl(0, 0, 0, 0.2, 0.2, 0.05, 'black', seg=14, rot=(90, 0, 0))
    k.pop()
    pts = [(math.cos(i / 14 * 6.283) * 0.17, Y0 - 0.053, 2.75 + math.sin(i / 14 * 6.283) * 0.17) for i in range(14)]
    k.poly(pts, 'paper', (0, -1, 0))
    k.fq(-0.01, 0.01, Y0 - 0.056, 2.75, 2.88, 'black')
    k.poly([(0.0, Y0 - 0.059, 2.74), (0.1, Y0 - 0.059, 2.7), (0.1, Y0 - 0.059, 2.72), (0.0, Y0 - 0.059, 2.765)], 'black', (0, -1, 0))


def window_i(k):
    """a classroom window (1.0 - 2.7 m) in the outer wall: a painted steel frame, a sill, blinds pulled half down"""
    paint_i(k, 0.0, 0.95)
    paint_i(k, 2.75, WALL_H)
    k.fq(-0.5, -0.42, Y0, 0.95, 2.75, 'wallC')
    k.fq(0.42, 0.5, Y0, 0.95, 2.75, 'wallC')
    k.bx(-0.49, 0.49, Y0 - 0.1, Y0 + 0.02, 0.92, 0.98, 'trimW', cull='kb')
    k.fq(-0.42, 0.42, Y0 - 0.003, 2.68, 2.75, 'steel')
    k.fq(-0.42, -0.38, Y0 - 0.003, 0.98, 2.68, 'steel')
    k.fq(0.38, 0.42, Y0 - 0.003, 0.98, 2.68, 'steel')
    k.fq(-0.38, 0.38, Y0 + 0.2, 1.8, 1.84, 'steel')
    k.fq(-0.37, 0.37, Y0 + 0.2, 2.15, 2.66, 'lam')
    k.rq(-0.38, Y0, Y0 + 0.3, 0.98, 2.68, 'wallC')
    k.lq(0.38, Y0, Y0 + 0.3, 0.98, 2.68, 'wallC')
    k.dq(-0.38, 0.38, Y0, Y0 + 0.3, 2.68, 'wallC')


def window_i_glow(k):
    y = Y0 + 0.3
    k.fq(-0.38, 0.38, y, 0.98, 1.6, 'grass')
    k.fq(-0.38, 0.38, y, 1.6, 1.95, 'leaf')
    k.fq(-0.38, 0.38, y, 1.95, 2.68, 'sky')
    for (x, z, r) in ((-0.2, 1.95, 0.16), (0.15, 1.9, 0.2)):
        k.poly([(x + math.cos(i / 8 * 6.283) * r, y - 0.003, z + math.sin(i / 8 * 6.283) * r * 0.8) for i in range(8)], 'leafD', (0, -1, 0))
    k.fq(-0.38, 0.38, y - 0.006, 2.4, 2.46, 'skyL')


def periodic(part):
    COLS = ['chA', 'chD', 'chE', 'chC', 'chF', 'chB', 'sky', 'chA']

    def fn(k):
        paint_i(k)
        x0, x1 = -0.5 + (0.08 if part == 'L' else 0.0), 0.5 - (0.08 if part == 'R' else 0.0)
        k.fq(x0, x1, Y0 - 0.004, 1.3, 2.5, 'paper')
        if part == 'M':
            k.text('ELEMENTS', 0.0, Y0 - 0.007, 2.36, 0.1, 'navy', font='display', maxw=0.8)
        n = 6
        w = (x1 - x0 - 0.06) / n
        for i in range(n):
            for j in range(6):
                if part == 'L' and i > 1 and j > 1 and j < 6 and i < 6 and j > 0:
                    continue
                if part == 'R' and j < 2 and i < 4:
                    continue
                if part == 'M' and j < 3:
                    continue
                a = x0 + 0.03 + i * w
                z = 1.38 + j * 0.15
                k.fq(a + 0.008, a + w - 0.008, Y0 - 0.007, z, z + 0.13, COLS[(i * 3 + j + {'L': 0, 'M': 2, 'R': 5}[part]) % len(COLS)])
    return fn


def eyewash(k):
    paint_i(k)
    k.fq(-0.3, 0.3, Y0 - 0.004, 1.95, 2.3, 'exitG')
    k.text('EYE WASH', 0.0, Y0 - 0.007, 2.05, 0.12, 'paper', font='display', maxw=0.5)
    k.bx(-0.22, 0.22, Y0 - 0.3, Y0, 0.95, 1.05, 'foodY')
    k.bx(-0.05, 0.05, Y0 - 0.1, Y0, 0.6, 0.95, 'steel', cull='k')
    k.bx(0.24, 0.3, Y0 - 0.12, Y0, 1.25, 1.6, 'foodY', cull='k')


def fire_ext(k):
    paint_i(k)
    k.bx(-0.22, 0.22, Y0 - 0.04, Y0, 0.9, 1.75, 'chD', cull='k')
    k.fq(-0.17, 0.17, Y0 - 0.043, 1.0, 1.6, 'glassL')
    k.fq(-0.06, 0.06, Y0 - 0.046, 1.05, 1.45, 'chD')
    k.fq(-0.16, 0.16, Y0 - 0.046, 1.62, 1.7, 'paper')
    k.text('FIRE', 0.0, Y0 - 0.049, 1.635, 0.05, 'chD', font='display')


def kitchen_pass(k):
    """behind the serving line: a stainless pass-through into the kitchen (hood, shelves, a warm light)"""
    paint_i(k, 0.0, 1.0)
    paint_i(k, 2.4, WALL_H)
    k.fq(-0.5, 0.5, Y0, 1.0, 2.4, 'chrome')
    k.fq(-0.46, 0.46, Y0 - 0.004, 1.05, 2.3, 'steel')
    k.fq(-0.42, 0.42, Y0 - 0.007, 1.9, 2.25, 'steelD')
    for z in (1.35, 1.65):
        k.bx(-0.44, 0.44, Y0 - 0.2, Y0, z, z + 0.03, 'chrome', ink=False)
    for (x, c) in ((-0.25, 'chD'), (0.2, 'foodY')):
        k.cyl(x, Y0 - 0.1, 1.68, 0.06, 0.06, 0.12, c, seg=6)


def menu_board(k):
    paint_i(k, 0.0, 1.0)
    paint_i(k, 1.0, WALL_H, band=False)
    k.bx(-0.48, 0.48, Y0 - 0.06, Y0, 2.6, 3.6, 'black', cull='k')


def menu_glow(k):
    k.fq(-0.44, 0.44, Y0 - 0.063, 2.64, 3.56, 'navy')
    k.fq(-0.42, 0.42, Y0 - 0.066, 3.36, 3.5, 'gold')
    for i, c in enumerate(('paper', 'foodY', 'paper', 'paper')):
        z = 3.18 - i * 0.16
        k.fq(-0.4, 0.1, Y0 - 0.066, z, z + 0.05, c)
        k.fq(0.26, 0.4, Y0 - 0.066, z, z + 0.05, 'exitG')


def clerestory(k):
    paint_i(k, 0.0, 5.2)
    paint_i(k, 7.3, WALL_H)
    k.fq(-0.5, -0.45, Y0, 5.2, 7.3, 'wallU')
    k.fq(0.45, 0.5, Y0, 5.2, 7.3, 'wallU')
    k.bx(-0.5, 0.5, Y0 - 0.08, Y0 + 0.02, 5.15, 5.22, 'trimW', cull='kb')
    k.fq(-0.45, -0.41, Y0 - 0.003, 5.22, 7.3, 'steel')
    k.fq(0.41, 0.45, Y0 - 0.003, 5.22, 7.3, 'steel')
    k.fq(-0.41, 0.41, Y0 + 0.2, 6.22, 6.27, 'steel')
    k.rq(-0.41, Y0 + 0.05, Y0 + 0.25, 5.22, 7.3, 'wallU')
    k.lq(0.41, Y0 + 0.05, Y0 + 0.25, 5.22, 7.3, 'wallU')
    k.dq(-0.41, 0.41, Y0 + 0.05, Y0 + 0.25, 7.3, 'wallU')


def clerestory_glow(k):
    k.fq(-0.41, 0.41, Y0 + 0.25, 5.22, 7.3, 'sky')
    k.fq(-0.41, 0.41, Y0 + 0.247, 6.6, 6.7, 'skyL')


def sliced(word, n, cap, z, c, bg=None, font='display', ext=False, shadow=None):
    """lettering across n modules: module i draws its slice of the word (read from the viewer's left)"""
    def mk(i):
        def fn(k):
            (paint_x if ext else paint_i)(k)
            yb = Y0 - (0.007 if ext else 0.004)
            if bg:
                k.fq(-0.5, 0.5, yb, z - cap * 0.35, z + cap * 1.35, bg)
            ib_text.draw(k, word, n / 2.0 - 0.5 - i, yb - (0.005 if bg else 0.002), z, cap, c, face='y-', font=font, maxw=n - 0.5,
                         clip=(i - n / 2.0, i + 1 - n / 2.0), shadow=shadow, shadow_off=(0.05, -0.05))
        return fn
    return mk


def honour(k):
    paint_i(k)
    k.bx(-0.42, 0.42, Y0 - 0.04, Y0, 1.3, 2.5, 'woodD', cull='k')
    k.fq(-0.36, 0.36, Y0 - 0.043, 2.28, 2.44, 'gold')
    for j in range(6):
        z = 1.4 + j * 0.14
        k.fq(-0.34, -0.02, Y0 - 0.043, z, z + 0.08, 'gold')
        k.fq(0.02, 0.34, Y0 - 0.043, z, z + 0.08, 'gold')


def trophy_case(part):
    """a recessed glass trophy case (0.8 - 2.3 m, 0.4 m deep) with shelves of cups and plaques; glass = companion"""
    def fn(k):
        rnd = random.Random({'L': 11, 'M': 12, 'R': 13}[part])
        paint_i(k, 0.0, 0.8)
        paint_i(k, 2.3, WALL_H)
        xa = -0.42 if part == 'L' else -0.5
        xb = 0.42 if part == 'R' else 0.5
        if part == 'L':
            k.fq(-0.5, -0.42, Y0, 0.8, 2.3, 'wallC')
        if part == 'R':
            k.fq(0.42, 0.5, Y0, 0.8, 2.3, 'wallC')
        D = 0.4
        k.fq(xa, xb, Y0 + D, 0.8, 2.3, 'navy')                 # back of the case
        k.uq(xa, xb, Y0, Y0 + D, 0.8, 'wood')                   # floor of the case
        k.dq(xa, xb, Y0, Y0 + D, 2.3, 'lam')
        if part == 'L':
            k.rq(xa, Y0, Y0 + D, 0.8, 2.3, 'wood')
        if part == 'R':
            k.lq(xb, Y0, Y0 + D, 0.8, 2.3, 'wood')
        k.bx(xa, xb, Y0 - 0.04, Y0, 0.74, 0.8, 'woodD', cull='k')
        k.bx(xa, xb, Y0 - 0.04, Y0, 2.3, 2.36, 'woodD', cull='k')
        for z in (1.3, 1.8):
            k.bx(xa, xb, Y0 + 0.02, Y0 + D, z, z + 0.025, 'glassL', ink=False)
        for z in (0.805, 1.325):
            x = xa + 0.1
            while x < xb - 0.12:
                kind = rnd.random()
                if kind < 0.5:
                    h = rnd.uniform(0.18, 0.38)
                    k.cyl(x, Y0 + 0.2, z, 0.05, 0.05, 0.06, 'black', seg=6)
                    k.cyl(x, Y0 + 0.2, z + 0.06, 0.02, 0.02, h * 0.4, 'gold', seg=6, ink=False)
                    k.cyl(x, Y0 + 0.2, z + 0.06 + h * 0.4, 0.03, 0.08, h * 0.6, 'gold', seg=6)
                elif kind < 0.8:
                    k.bx(x - 0.07, x + 0.07, Y0 + 0.3, Y0 + 0.34, z, z + 0.22, 'woodD')
                    k.fq(x - 0.05, x + 0.05, Y0 + 0.297, z + 0.05, z + 0.17, 'gold')
                else:
                    k.sph(x, Y0 + 0.2, z + 0.1, 0.1, 'chB', seg=(6, 4))
                x += rnd.uniform(0.3, 0.42)
    return fn


def trophy_glow(part):
    def fn(k):
        xa = -0.42 if part == 'L' else -0.5
        xb = 0.42 if part == 'R' else 0.5
        k.fq(xa, xb, Y0 - 0.005, 0.8, 2.3, 'navy')
        k.fq(xa + 0.05, xa + 0.12, Y0 - 0.008, 1.0, 2.2, 'steelD')
        k.dq(xa + 0.02, xb - 0.02, Y0 + 0.05, Y0 + 0.12, 2.29, 'lightW')
    return fn


def world_map(part):
    def fn(k):
        paint_i(k)
        x0, x1 = -0.5 + (0.1 if part == 'L' else 0.0), 0.5 - (0.1 if part == 'R' else 0.0)
        k.fq(x0, x1, Y0 - 0.02, 1.2, 2.45, 'sky')
        k.bx(x0 - (0.04 if part == 'L' else 0.0), x1 + (0.04 if part == 'R' else 0.0), Y0 - 0.06, Y0, 2.45, 2.55, 'steelD', cull='k')
        k.bx(x0, x1, Y0 - 0.04, Y0 - 0.02, 1.16, 1.2, 'woodD', ink=False)
        rnd = random.Random({'L': 21, 'M': 22, 'R': 23}[part])
        for q in range(2):
            cx, cz = rnd.uniform(x0 + 0.2, x1 - 0.2), rnd.uniform(1.5, 2.15)
            pts = [(cx + math.cos(i / 9 * 6.283) * rnd.uniform(0.1, 0.24), Y0 - 0.023 - 0.003 * q, cz + math.sin(i / 9 * 6.283) * rnd.uniform(0.08, 0.2)) for i in range(9)]
            k.poly(pts, rnd.choice(['grass', 'foodY', 'chB', 'leaf']), (0, -1, 0))
    return fn


def timeline(k):
    paint_i(k)
    k.fq(-0.5, 0.5, Y0 - 0.004, 1.88, 1.92, 'navy')
    k.fq(-0.3, 0.1, Y0 - 0.004, 1.98, 2.3, 'paper')
    k.fq(-0.1, 0.3, Y0 - 0.004, 1.48, 1.8, 'foodY')
    k.text('1850', -0.1, Y0 - 0.007, 2.12, 0.1, 'navy', font='cond')
    k.text('1920', 0.1, Y0 - 0.007, 1.6, 0.1, 'navy', font='cond')


def student_art(v):
    def fn(k):
        paint_i(k)
        rnd = random.Random(30 + v)
        for i in range(2):
            x = -0.45 + i * 0.47
            z = 1.4 + rnd.uniform(0.0, 0.25)
            k.fq(x, x + 0.4, Y0 - 0.004, z, z + 0.52, 'paper')
            for q in range(3):
                cx, cz, r = x + rnd.uniform(0.1, 0.3), z + rnd.uniform(0.12, 0.4), rnd.uniform(0.04, 0.09)
                k.poly([(cx + math.cos(t / 7 * 6.283) * r, Y0 - 0.007 - 0.003 * q, cz + math.sin(t / 7 * 6.283) * r) for t in range(7)],
                       rnd.choice(['chA', 'chB', 'chC', 'chD', 'chE', 'chF']), (0, -1, 0))
    return fn


def closed_door(word, c):
    def fn(k):
        paint_i(k, 2.3, WALL_H)
        k.fq(-0.5, -0.45, Y0, 0.0, 2.3, 'wallC')
        k.fq(0.45, 0.5, Y0, 0.0, 2.3, 'wallC')
        k.bx(-0.45, 0.45, Y0 - 0.03, Y0 + 0.02, 2.2, 2.3, 'steelD', cull='k')
        k.bx(-0.45, -0.4, Y0 - 0.03, Y0 + 0.02, 0.0, 2.2, 'steelD', cull='kb')
        k.bx(0.4, 0.45, Y0 - 0.03, Y0 + 0.02, 0.0, 2.2, 'steelD', cull='kb')
        k.fq(-0.4, 0.4, Y0 + 0.01, 0.0, 2.2, c)
        k.bx(0.24, 0.34, Y0 - 0.04, Y0 + 0.01, 1.0, 1.05, 'chrome', ink=False)
        k.fq(-0.38, 0.38, Y0 + 0.007, 0.0, 0.25, 'steel')
        k.bx(-0.2, 0.2, Y0 - 0.02, Y0 + 0.01, 1.55, 1.8, 'paper', cull='k')
        k.text(word, 0.0, Y0 - 0.023, 1.62, 0.1, 'navy', font='display', maxw=0.36)
    return fn


def fountain(k):
    """a drinking fountain in a tiled alcove (the bowl stands 8 cm proud)"""
    paint_i(k, 0.0, 0.5)
    paint_i(k, 1.6, WALL_H)
    k.fq(-0.5, -0.38, Y0, 0.5, 1.6, 'wallC')
    k.fq(0.38, 0.5, Y0, 0.5, 1.6, 'wallC')
    k.fq(-0.38, 0.38, Y0 + 0.25, 0.5, 1.6, 'skyL')
    k.rq(-0.38, Y0, Y0 + 0.25, 0.5, 1.6, 'skyL')
    k.lq(0.38, Y0, Y0 + 0.25, 0.5, 1.6, 'skyL')
    k.uq(-0.38, 0.38, Y0, Y0 + 0.25, 0.5, 'steel')
    k.dq(-0.38, 0.38, Y0, Y0 + 0.25, 1.6, 'skyL')
    k.bx(-0.3, 0.3, Y0 - 0.08, Y0 + 0.22, 0.78, 0.9, 'chrome')
    k.uq(-0.24, 0.24, Y0 - 0.04, Y0 + 0.16, 0.903, 'steelD')
    k.bx(-0.02, 0.02, Y0 + 0.05, Y0 + 0.09, 0.9, 0.96, 'chrome', ink=False)


def pads(k, low=True):
    paint_i(k, 2.2, WALL_H)
    k.fq(-0.5, 0.5, Y0, 0.0, 0.1, 'cove')
    k.fq(-0.5, 0.5, Y0, 0.1, 0.3, 'wallC')
    k.bx(-0.49, 0.49, Y0 - 0.06, Y0, 0.3, 2.2, 'mat', cull='kb')
    k.fq(-0.3, 0.3, Y0 - 0.063, 1.9, 1.98, 'gold')


def scoreboard(part):
    def fn(k):
        k.fq(-0.5, 0.5, Y0, 0.0, 0.1, 'cove')
        k.fq(-0.5, 0.5, Y0, 0.1, 0.3, 'wallC')
        k.bx(-0.49, 0.49, Y0 - 0.06, Y0, 0.3, 2.2, 'mat', cull='kb')
        paint_i(k, 2.2, 4.4, band=False)
        paint_i(k, 6.9, WALL_H)
        xa = -0.5 if part == 'R' else -0.45
        xb = 0.5 if part == 'L' else 0.45
        k.fq(-0.5, 0.5, Y0, 4.4, 6.9, 'wallU')
        k.bx(xa, xb, Y0 - 0.2, Y0, 4.5, 6.8, 'black', cull='k')
        k.fq(xa + 0.05, xb - 0.05, Y0 - 0.203, 6.35, 6.72, 'slate')
        k.text('HOME' if part == 'L' else 'GUEST', 0.0, Y0 - 0.206, 6.42, 0.22, 'paper', font='display', maxw=0.7)
    return fn


def scoreboard_glow(part):
    def fn(k):
        xa = -0.5 if part == 'R' else -0.45
        xb = 0.5 if part == 'L' else 0.45
        k.text('42' if part == 'L' else '38', 0.0, Y0 - 0.206, 5.3, 0.75, 'chD', font='display', maxw=0.8)
        if part == 'L':
            k.text('PERIOD 4', xb - 0.02, Y0 - 0.206, 4.75, 0.2, 'foodY', font='display', align='r', maxw=0.8)
        else:
            k.text('12:00', xa + 0.04, Y0 - 0.206, 4.75, 0.2, 'foodY', font='display', align='l', maxw=0.8)
    return fn


def banner(v):
    def fn(k):
        paint_i(k)
        if v == 0:
            return
        c = ['slate', 'gold', 'curtain'][v - 1]
        fg = 'paper' if c != 'gold' else 'navy'
        k.bx(-0.36, 0.36, Y0 - 0.06, Y0 - 0.03, 7.25, 7.3, 'steelD', ink=False)
        k.poly([(-0.32, Y0 - 0.02, 7.25), (0.32, Y0 - 0.02, 7.25), (0.32, Y0 - 0.02, 5.6), (0.0, Y0 - 0.02, 5.2), (-0.32, Y0 - 0.02, 5.6)], c, (0, -1, 0))
        word = ['STATE', 'CITY', 'REGION'][v - 1]
        k.text(word, 0.0, Y0 - 0.023, 6.75, 0.2, fg, font='display', maxw=0.56)
        k.text('CHAMPS', 0.0, Y0 - 0.023, 6.45, 0.17, fg, font='display', maxw=0.56)
        k.text(['2019', '2022', '2024'][v - 1], 0.0, Y0 - 0.023, 6.0, 0.24, 'gold' if c != 'gold' else 'navy', font='display', maxw=0.5)
    return fn


def flags(v):
    def fn(k):
        paint_i(k)
        c = ['chA', 'chD', 'chC', 'chE'][v]
        k.bx(-0.36, 0.36, Y0 - 0.05, Y0, 6.9, 6.95, 'steelD', ink=False)
        k.fq(-0.3, 0.3, Y0 - 0.01, 5.4, 6.9, c)
        k.fq(-0.3, 0.3, Y0 - 0.013, 5.95, 6.25, 'paper')
    return fn


# ================================================================ exterior wall art
def window_x(k):
    """two storeys of windows in the brick: stone sills, painted lintels and white frames, sky in the glass"""
    paint_x(k, 0.0, 1.0)
    paint_x(k, 3.25, 4.75)
    paint_x(k, 7.0, WALL_H)
    for (z0, z1) in ((1.0, 3.25), (4.75, 7.0)):
        k.fq(-0.5, -0.4, Y0, z0, z1, 'brick')
        k.fq(0.4, 0.5, Y0, z0, z1, 'brick')
        k.bx(-0.46, 0.46, Y0 - 0.08, Y0, z0 - 0.08, z0, 'stone', cull='kb')
        k.fq(-0.4, 0.4, Y0, z1 - 0.14, z1, 'stone')
        k.fq(-0.4, 0.4, Y0, z0, z1 - 0.14, 'trimW')
        k.fq(-0.35, 0.35, Y0 - 0.003, z0 + 0.05, z1 - 0.18, 'glass')
        k.fq(-0.35, 0.35, Y0 - 0.006, (z0 + z1) / 2 - 0.05, (z0 + z1) / 2 - 0.01, 'trimW')
        k.poly([(-0.35, Y0 - 0.009, z1 - 0.55), (-0.12, Y0 - 0.009, z1 - 0.18), (0.04, Y0 - 0.009, z1 - 0.18), (-0.35, Y0 - 0.009, z1 - 0.95)], 'glassL', (0, -1, 0))


def downspout(k):
    paint_x(k)
    k.cyl(0.0, Y0 - 0.09, 0.15, 0.055, 0.055, 7.5, 'steelD', seg=8)
    k.bx(-0.09, 0.09, Y0 - 0.16, Y0, 7.6, 7.75, 'steelD', cull='k')
    for z in (1.5, 3.5, 5.5):
        k.bx(-0.07, 0.07, Y0 - 0.12, Y0, z, z + 0.04, 'steelD', ink=False)


def ext_door(part):
    """closed double doors (the north wing's entrance at the covered walkway): one leaf a cell; L's jamb at -X"""
    def fn(k):
        paint_x(k, 2.8, WALL_H)
        sg = -1 if part == 'L' else 1            # the outer jamb's side
        xo, xi = sg * 0.5, -sg * 0.5
        a, b = sorted((xo, sg * 0.42))
        k.fq(a, b, Y0, 0.0, 2.8, 'brick')
        a, b = sorted((sg * 0.42, sg * 0.36))
        k.bx(a, b, Y0 - 0.04, Y0 + 0.02, 0.0, 2.62, 'steelD', cull='kb')
        a, b = sorted((xo, xi))
        k.bx(a, b, Y0 - 0.04, Y0 + 0.02, 2.62, 2.7, 'steelD', cull='k')
        a, b = sorted((sg * 0.36, xi))
        k.fq(a, b, Y0 + 0.01, 0.0, 2.62, 'slate')
        a, b = sorted((sg * 0.28, -sg * 0.1))
        k.fq(a, b, Y0 + 0.007, 1.2, 2.3, 'glass')
        a, b = sorted((-sg * 0.42, -sg * 0.2))
        k.bx(a, b, Y0 - 0.05, Y0 + 0.007, 1.0, 1.04, 'chrome', ink=False)
    return fn


# ================================================================ doors (prefabs in the wall line) and headers
def wall_header(k, x0, x1, z0, ext_back=False):
    """the wall over an opening: both faces from z0 up, the soffit"""
    paint_i(k, z0, WALL_H, x0, x1, band=False, joints=False, y=-0.5)
    k.push(0, 0, 180)
    if ext_back:
        paint_x(k, z0, WALL_H, -x1, -x0, y=-0.5)
    else:
        paint_i(k, z0, WALL_H, -x1, -x0, band=False, joints=False, y=-0.5)
    k.pop()
    k.dq(x0, x1, -0.5, 0.5, z0, 'wallC')


def door_frame(k, W, H, glass=False):
    """hollow-metal frame in the wall's middle, the reveals (jambs) back to both faces"""
    for s in (-1, 1):
        x = s * W / 2
        k.qx(-0.5, 0.5, 0.0, H, x, -s, 'wallC')
        a, b = sorted((x, x - s * 0.07))
        k.bx(a, b, -0.09, 0.09, 0.0, H - 0.07, 'steelD', cull='b')
    k.bx(-W / 2, W / 2, -0.09, 0.09, H - 0.07, H, 'steelD', cull='t')


def leaf(k, x0, x1, H, c, glass=True, kick=True, y=0.5):
    """an open door leaf lying flat against the back face (+Y side) between x0 and x1"""
    k.bx(x0, x1, y + 0.012, y + 0.057, 0.02, H - 0.1, c)
    if glass:
        xm, w = (x0 + x1) / 2, (x1 - x0)
        k.bq(xm - w * 0.22, xm + w * 0.22, y + 0.06, 1.25, 2.0, 'glassL')
    if kick:
        k.bq(x0 + 0.03, x1 - 0.03, y + 0.06, 0.05, 0.3, 'chrome')


def build_doors(k, ao):
    # classroom double door [2, 1]: 2 m opening, 2.5 m head, both leaves folded open flat against the back wall
    H = DOOR_H
    k.begin()
    wall_header(k, -1.0, 1.0, H)
    door_frame(k, 2.0, H)
    leaf(k, 1.0, 1.96, H, 'slate')
    leaf(k, -1.96, -1.0, H, 'slate')
    for side in (0, 180):
        k.push(0, 0, side)
        k.bx(-0.25, 0.25, -0.53, -0.5, 2.62, 2.8, 'navy', cull='kb')
        k.fq(-0.18, 0.18, -0.533, 2.67, 2.75, 'paper')
        k.pop()
    k.finish('Door2', ao=ao)
    # wide glass double doors [3, 1] (cafeteria, gym, lobby): leaves folded in pairs (bi-fold) against the back wall
    for name, ext in (('Door3', False), ('Door3X', True)):
        k.begin()
        wall_header(k, -1.5, 1.5, H, ext_back=ext)
        door_frame(k, 3.0, H)
        for s in (-1, 1):
            a = s * 1.5
            for j in range(2):
                yy = 0.5 + j * 0.05
                k.bx(min(a, a + s * 0.74), max(a, a + s * 0.74), yy + 0.004, yy + 0.046, 0.02, H - 0.1, 'steel')
            k.bq(min(a + s * 0.15, a + s * 0.6), max(a + s * 0.15, a + s * 0.6), 0.5 + 0.05 + 0.049, 0.9, 2.2, 'glassL')
        k.bx(-0.75, 0.75, -0.56, -0.5, 2.62, 2.92, 'exitG', cull='k')
        k.text('EXIT', 0.0, -0.563, 2.68, 0.2, 'paper', font='display')
        k.finish(name, ao=ao)
    # an open archway's header (1 cell): the wall over the opening from 4 m, both faces and the soffit
    k.begin()
    wall_header(k, -0.5, 0.5, CEIL)
    k.finish('Header', ao=ao)


# ================================================================ the gate, trail walls, hatch
def build_gate(k, ao):
    """an aluminium entrance 5 m wide: double doors (the grille rolls down in them), glass sidelights, a glazed
    transom to the 8 m wall top; the same both sides (it is the way into a room and the way out of one)"""
    k.begin()
    for s in (-1, 1):
        # outer reveals (the wall's thickness) and the sidelight posts
        k.qx(-0.5, 0.5, 0.0, WALL_H, s * 2.5, -s, 'wallC')
        for x in (1.5, 2.42):
            a, b = sorted((s * x, s * (x + 0.08)))
            k.bx(a, b, -0.5, 0.5, 0.0, 3.2, 'steelD', cull='bt')
            k.bx(a, b, -0.08, 0.08, 3.2, WALL_H, 'steelD', cull='bt')
        xa, xb = sorted((s * 1.58, s * 2.42))
        for side in (-1, 1):
            # the sidelights sit at the wall faces (the wall cell's collision is the whole cell): glass over a kick panel
            k.qy(xa, xb, 0.3, 3.2, side * 0.47, side, 'glass')
            k.qy(xa, xb, 0.0, 0.3, side * 0.47, side, 'steelD')
            k.qy(xa + 0.1, xb - 0.1, 1.0, 1.06, side * 0.473, side, 'steel')
    k.bx(-2.42, 2.42, -0.5, 0.5, 3.2, 3.6, 'steelD', cull='')
    for z0, z1 in ((5.6, 5.7), (7.85, WALL_H)):
        k.bx(-2.42, 2.42, -0.09, 0.09, z0, z1, 'steelD', cull='t' if z1 >= WALL_H else '')
    for side in (-1, 1):
        k.qy(-2.42, 2.42, 3.6, 5.6, side * 0.05, side, 'glass')
        k.qy(-2.42, 2.42, 5.7, 7.85, side * 0.05, side, 'glass')
        for x in (-1.25, 0.0, 1.25):
            k.qy(x - 0.03, x + 0.03, 3.6, 7.85, side * 0.054, side, 'steelD')
        k.qy(-2.3, -1.6, 4.0, 5.2, side * 0.054, side, 'glassL')
        k.qy(0.4, 1.0, 6.0, 7.4, side * 0.054, side, 'glassL')
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        k.bx(-0.55, 0.55, -0.68, -0.5, 2.85, 3.15, 'black')
        k.pop()
    k.finish('GateFrame', ao=ao)
    k.begin()
    for side in (-1, 1):
        k.push(0, 0, 0 if side < 0 else 180)
        k.fq(-0.52, 0.52, -0.684, 2.88, 3.12, 'exitG')
        k.text('EXIT', 0.0, -0.687, 2.92, 0.16, 'paper', font='display')
        k.pop()
    k.finish('GateFrame_Glow')
    # roll-down security grille: slatted steel with perforations, a bottom bar
    k.begin()
    Hs, n = 3.05, 14
    for i in range(n):
        z = 0.12 + i * (Hs - 0.12) / n
        k.bx(-1.5, 1.5, -0.05, 0.05, z + 0.005, z + (Hs - 0.12) / n - 0.005, 'steel' if i % 2 else 'chrome', ink=False)
        if i % 2 == 0:
            for j in range(10):
                x = -1.35 + j * 0.3
                k.fq(x, x + 0.14, -0.053, z + 0.05, z + 0.12, 'steelD')
    k.bx(-1.5, 1.5, -0.06, 0.06, 0.0, 0.12, 'slate', ink=False)
    k.fq(-0.5, 0.5, -0.063, 1.5, 1.8, 'gold')
    k.text('CLOSED', 0.0, -0.066, 1.56, 0.18, 'navy', font='display')
    obj = k.finish('GateShutter')
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)
    # trail walls: the link corridor (1 m along Blender Y, the corridor face +X, 4 m to its ceiling)
    def tw_base(k):
        k.rq(0.25, -0.5, 0.5, 0.0, 0.1, 'cove')
        k.rq(0.25, -0.5, 0.5, 0.1, 1.15, 'wallC')
        k.rq(0.25, -0.5, 0.5, 1.15, 1.3, 'slate')
        k.rq(0.25, -0.5, 0.5, 1.3, 1.34, 'gold')
        k.rq(0.25, -0.5, 0.5, 1.34, 4.0, 'wallC')
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        k.begin()
        if name == 'TrailWall_B':   # lockers
            k.rq(0.25, -0.5, 0.5, 0.0, 0.15, 'cove')
            k.rq(0.25, -0.5, 0.5, 0.15, 2.0, 'steelD')
            k.rq(0.25, -0.5, 0.5, 2.06, 4.0, 'wallC')
            for i in range(3):
                a, b = -0.5 + i / 3 + 0.012, -0.5 + (i + 1) / 3 - 0.012
                k.rq(0.253, a, b, 0.17, 1.98, 'slate')
                for zv in (1.72, 1.8, 1.88):
                    k.rq(0.256, a + 0.06, b - 0.06, zv, zv + 0.03, 'steelD')
                k.rq(0.256, a + 0.04, a + 0.08, 0.95, 1.15, 'chrome')
            k.bx(0.25, 0.3, -0.5, 0.5, 2.0, 2.06, 'steelD', cull='lb')
        else:
            tw_base(k)
            if name == 'TrailWall_C':
                k.rq(0.253, -0.36, 0.36, 1.45, 2.3, 'cork')
                k.rq(0.256, -0.3, -0.02, 1.6, 2.1, 'paper')
                k.rq(0.256, 0.04, 0.3, 1.7, 2.2, 'chE')
                k.bx(0.25, 0.28, -0.4, 0.4, 2.3, 2.34, 'wood', cull='l')
        k.finish(name, ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 1.2, 1.15, 0.1, 'steelD', seg=20)
    k.ring(0, 0, 0.103, 0.92, 1.1, 'gold', seg=20)
    for j in range(-3, 4):
        k.uq(-0.6, 0.6, j * 0.2 - 0.03, j * 0.2 + 0.03, 0.106, 'steel')
    k.finish('Hatch', ao=ao)


# ================================================================ ceilings (layer 4) and roofs (layer 8)
def build_ceilings(k, ao):
    """acoustic tiles hanging from the 4 m layer (faces down): a 1-cell tile and a light panel cell, [2, 2] groups of
    tiles with and without a 2 x 4 light panel (the T-bar grid painted 4 mm under the tiles); roof bays [2, 2]"""
    def tbar(k, x0, x1, y0, y1, mid=False):
        k.dq(x0, x1, y0, y0 + 0.03, -0.004, 'steel')
        k.dq(x0, x0 + 0.03, y0 + 0.03, y1, -0.004, 'steel')
        if mid:
            k.dq(x0 + 0.03, x1, -0.015, 0.015, -0.004, 'steel')
    k.begin()
    k.dq(-0.5, 0.5, -0.5, 0.5, 0.0, 'trimW')
    tbar(k, -0.5, 0.5, -0.5, 0.5)
    k.finish('C_Tile')
    k.begin()
    k.dq(-0.5, 0.5, -0.5, 0.5, 0.0, 'trimW')
    tbar(k, -0.5, 0.5, -0.5, 0.5)
    k.dq(-0.3, 0.3, -0.4, 0.4, -0.006, 'steel')
    k.finish('C_Light')
    k.begin()
    k.dq(-0.27, 0.27, -0.37, 0.37, -0.009, 'lightW')
    k.finish('C_Light_Glow')
    k.begin()   # the trails' and the hatch room's ceiling light: the panel is part of the piece (no glow there)
    k.dq(-0.3, 0.3, -0.6, 0.6, -0.004, 'steel')
    k.dq(-0.26, 0.26, -0.56, 0.56, -0.008, 'lightW')
    k.finish('C_TrailLight')
    k.begin()
    k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'trimW')
    tbar(k, -1.0, 1.0, -1.0, 1.0, mid=True)
    k.finish('C_Tile2')
    k.begin()
    k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'trimW')
    tbar(k, -1.0, 1.0, -1.0, 1.0, mid=True)
    k.bx(-0.62, 0.62, -0.32, 0.32, -0.05, -0.006, 'steel', cull='t', ink=False)
    k.finish('C_Light2')
    k.begin()
    k.dq(-0.58, 0.58, -0.28, 0.28, -0.054, 'lightW')
    k.finish('C_Light2_Glow')

    # roof bays [2, 2] (hang from 8 m): a deep coffer grid of acoustic panels (beams on the bay's -X / -Y edges)
    def coffer(k):
        """acoustic ceiling between deep baffles (one along the bay's -X edge every 2 m)"""
        k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'wallU')
        k.bx(-1.0, -0.88, -1.0, 1.0, -0.6, -0.002, 'trimW', cull='tkf', ink=False)
        k.dq(-0.8, 0.92, -0.9, 0.9, -0.004, 'lam')
    k.begin(); coffer(k); k.finish('R_Coffer')
    k.begin(); coffer(k)
    k.cyl(0.06, 0.06, -1.6, 0.015, 0.015, 1.596, 'steelD', seg=4, ink=False, caps=False)
    k.cyl(0.06, 0.06, -2.0, 0.42, 0.3, 0.4, 'slate', seg=8, caps=False)
    k.cyl(0.06, 0.06, -1.62, 0.3, 0.3, 0.03, 'slate', seg=8, ink=False)
    k.finish('R_Pendant')
    k.begin()
    k.poly([(0.06 + math.cos(-i / 8 * 6.283) * 0.38, 0.06 + math.sin(-i / 8 * 6.283) * 0.38, -1.996) for i in range(8)], 'lightW', (0, 0, -1))
    k.finish('R_Pendant_Glow')
    k.begin(); coffer(k)
    for (x0, x1, y0, y1) in ((-0.8, 0.92, -0.8, -0.72), (-0.8, 0.92, 0.84, 0.92), (-0.8, -0.72, -0.72, 0.84), (0.84, 0.92, -0.72, 0.84)):
        k.bx(x0, x1, y0, y1, -0.3, -0.006, 'trimW', cull='t')
    k.finish('R_Sky')
    k.begin()
    k.dq(-0.72, 0.84, -0.72, 0.84, -0.02, 'sky')
    k.dq(-0.6, 0.1, 0.1, 0.7, -0.024, 'skyL')
    k.finish('R_Sky_Glow')

    # gym roof bays [2, 2]: the steel deck's flutes; an open-web joist along X over the bay's middle (every 4 m)
    def deck(k):
        k.dq(-1.0, 1.0, -1.0, 1.0, 0.0, 'steel')
        for y in (-0.5, 0.5):
            k.dq(-1.0, 1.0, y - 0.06, y + 0.06, -0.004, 'steelD')

    def joist(k):
        deck(k)
        k.bx(-1.0, 1.0, -0.05, 0.05, -0.12, -0.006, 'navy', cull='tlr', ink=False)
        k.bx(-1.0, 1.0, -0.04, 0.04, -0.95, -0.87, 'navy', cull='lr')
        k.beam((-0.95, -0.012, -0.12), (0.0, -0.012, -0.87), 0.04, 'navy', ink=False)
        k.beam((0.0, 0.012, -0.87), (0.95, 0.012, -0.12), 0.04, 'navy', ink=False)
    k.begin(); deck(k); k.finish('R_Deck')
    k.begin(); joist(k); k.finish('R_Joist')
    k.begin(); joist(k)
    k.bx(-0.015, 0.015, 0.2, 0.23, -1.6, -0.006, 'steelD', ink=False, cull='t')
    k.cyl(0.0, 0.215, -2.05, 0.34, 0.16, 0.42, 'steelD', seg=8, caps=False)
    k.finish('R_JoistLamp')
    k.begin()
    k.poly([(math.cos(-i / 8 * 6.283) * 0.3, 0.215 + math.sin(-i / 8 * 6.283) * 0.3, -2.045) for i in range(8)], 'lightW', (0, 0, -1))
    k.finish('R_JoistLamp_Glow')


# ================================================================ floors
def build_floors(k, ao):
    k.begin()
    k.uq(-0.5, 0.5, -0.5, 0.5, 0.0, 'steel')
    k.finish('F_Epoxy')
    # the lobby crest [6, 6]: a ring with the school name, a shield, two stars
    k.begin()
    k.disc(0, 0, 0.0, 2.7, 'slate', n=32)
    k.ring(0, 0, 0.003, 2.45, 2.62, 'gold', seg=32)
    k.disc(0, 0, 0.003, 1.85, 'vct', n=32)
    k.ring(0, 0, 0.006, 1.7, 1.78, 'gold', seg=32)
    sh = [(-0.9, 1.0), (0.9, 1.0), (0.9, -0.1), (0.5, -0.8), (0.0, -1.1), (-0.5, -0.8), (-0.9, -0.1)]
    k.poly([(x, y, 0.006) for x, y in sh], 'slate', (0, 0, 1))
    k.poly([(x * 0.8, y * 0.8 + 0.02, 0.009) for x, y in sh], 'gold', (0, 0, 1))
    k.text('CA', 0.0, 0.05, 0.012, 0.75, 'navy', face='up', font='serif', valign='m')
    ib_text.draw(k, 'CHALKSTONE', 0.0, -2.15, 0.008, 0.3, 'paper', face='up', font='display', valign='m')
    ib_text.draw(k, 'ACADEMY', 0.0, 2.15, 0.008, 0.3, 'paper', face='upr', font='display', valign='m')
    k.finish('F_Crest')
    # gym maple [2, 2]: boards along X with seams, a darker board now and then
    k.begin()
    k.uq(-1.0, 1.0, -1.0, 1.0, 0.0, 'maple')
    for j in range(4):
        y = -1.0 + j * 0.5
        k.uq(-1.0, 1.0, y - 0.004, y + 0.004, 0.003, 'mapleD')
    k.uq(-0.4, 0.6, 0.27, 0.48, 0.003, 'mapleD')
    k.finish('F_Maple')
    # lawn cell: grass, a few darker tufts
    for v in range(2):
        k.begin()
        k.uq(-0.5, 0.5, -0.5, 0.5, 0.0, 'grass')
        rnd = random.Random(60 + v)
        for q in range(2):
            x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)
            k.poly([(x + math.cos(i / 5 * 6.283) * 0.12, y + math.sin(i / 5 * 6.283) * 0.09, 0.003 + 0.003 * q) for i in range(5)], 'grass2', (0, 0, 1))
        k.finish('F_Lawn' + 'AB'[v])
    # basketball court lines [28, 16] (on the maple, local X along the court): slate fills at the base, lines 3 mm
    # above them, the circles' rings, the three-point arcs and the name 6 mm above
    k.begin()
    L, Wd, t = 14.0, 8.0, 0.05
    z0, z1, z2 = 0.0, 0.003, 0.006

    def line(x0, x1, y0, y1, z=z1):
        k.uq(x0, x1, y0, y1, z, 'paper')
    line(-L + 0.5, L - 0.5, -Wd + 0.5, -Wd + 0.5 + t)
    line(-L + 0.5, L - 0.5, Wd - 0.5 - t, Wd - 0.5)
    line(-L + 0.5, -L + 0.5 + t, -Wd + 0.5 + t, Wd - 0.5 - t)
    line(L - 0.5 - t, L - 0.5, -Wd + 0.5 + t, Wd - 0.5 - t)
    line(-t / 2, t / 2, -Wd + 0.5 + t, Wd - 0.5 - t)
    k.ring(0, 0, z2, 1.8 - t, 1.8, 'paper', seg=48)
    k.disc(0, 0, z0, 0.62, 'slate', n=32)
    for s in (-1, 1):
        bx = s * (L - 0.5 - t)
        xa, xb = sorted((bx, bx - s * 5.75))
        k.uq(xa, xb, -2.45, 2.45, z0, 'slate')
        xc = bx - s * 5.75
        a0 = -math.pi / 2 if s > 0 else math.pi / 2
        k.ring(xc, 0, z1, 1.8 - t, 1.8, 'paper', seg=32, a0=a0, a1=a0 + math.pi)
        cx = s * (L - 0.5 - 1.6)
        R3 = 6.75
        ang = math.asin(6.6 / R3)
        ya, yb = sorted((bx, cx))
        line(ya, yb, -6.6 - t / 2, -6.6 + t / 2)
        line(ya, yb, 6.6 - t / 2, 6.6 + t / 2)
        c0 = math.pi - ang if s > 0 else -ang
        k.ring(cx, 0, z2, R3 - t, R3, 'paper', seg=48, a0=c0, a1=c0 + 2 * ang)
    ib_text.draw(k, 'COMETS', 0.0, 0.0, z2, 0.42, 'gold', face='up', font='display', valign='m')
    k.finish('F_Court')


# ================================================================ stairs, rails, deck columns
def build_stairs(k, ao):
    """a straight stair [2, 7] rising toward Blender +Y (game north) onto the 4 m deck: 25 treads of 0.25 m (0.16 m
    rise), a 0.75 m landing, painted steel stringers, handrails; walkable treads solid to the floor, rails keep you on it"""
    k.begin()
    Wd, L, n = 1.7, 7.0, 25
    y0 = -L / 2
    for i in range(n):
        top = (i + 1) * RISE
        a = y0 + i * TREAD
        b = a + TREAD if i < n - 1 else L / 2
        k.bx(-Wd / 2, Wd / 2, a, b, top - 0.06, top, 'vctD', cull='')
        k.uq(-Wd / 2 + 0.02, Wd / 2 - 0.02, a + 0.003, a + 0.05, top + 0.003, 'gold')
        k.wcol(-Wd / 2, Wd / 2, a, b, 0.0, top)
    for s in (-1, 1):
        xa, xb = sorted((s * Wd / 2, s * (Wd / 2 + 0.08)))
        prof = [(y0, 0.0), (y0 + 0.3, 0.0), (L / 2 - 1.0, CEIL - 0.45), (L / 2, CEIL - 0.45), (L / 2, CEIL), (L / 2 - 1.1, CEIL), (y0, 0.35)]
        k.hullp([(x, y, zz) for x in (xa, xb) for (y, zz) in prof], 'slate')
        xr = s * (Wd / 2 + 0.04)
        k.beam((xr, y0 + 0.1, 1.05), (xr, L / 2 - 1.0, CEIL + 1.0), 0.05, 'steel')
        k.beam((xr, L / 2 - 1.0, CEIL + 1.0), (xr, L / 2 - 0.05, CEIL + 1.0), 0.036, 'steel')
        for t in (0.15, 0.4, 0.65, 0.9):
            yy = y0 + 0.1 + t * (L - 1.1)
            zz = 0.35 + t * (CEIL - 0.35)
            k.bx(xr - 0.015, xr + 0.015, yy - 0.015, yy + 0.015, zz, zz + 1.0, 'steel', ink=False, cull='b')
        for i in range(n + 1):
            a = y0 + i * TREAD
            b = L / 2 if i == n else a + TREAD
            top = min(CEIL, (i + 1) * RISE) + 1.0
            k.col(xa, xb, a, b, 0.0, top)
    k.finish('Stair', ao=ao)
    # mezzanine rail (along Blender Y): steel pickets, a top rail, a kick plate
    def rail(k, y0, y1):
        k.bx(-0.035, 0.035, y0, y1, 1.0, 1.06, 'slate')
        k.bx(-0.02, 0.02, y0, y1, 0.0, 0.1, 'slate', cull='b')
        y = y0 + 0.08
        while y < y1 - 0.05:
            k.bx(-0.012, 0.012, y, y + 0.024, 0.1, 1.0, 'steel', ink=False, cull='tb')
            y += 0.22
    k.begin(); rail(k, -0.5, 0.5); k.col(-0.04, 0.04, -0.5, 0.5, 0.0, 1.06); k.finish('RailFull', ao=ao)
    k.begin(); rail(k, -0.5, -0.035); k.col(-0.04, 0.04, -0.5, 0.0, 0.0, 1.06); k.finish('RailHalf', ao=ao)
    k.begin(); k.bx(-0.04, 0.04, -0.04, 0.04, 0.0, 1.1, 'slate', cull='b'); k.finish('RailPost', ao=ao)
    k.begin()
    k.cyl(0, 0, 0.0, 0.14, 0.14, CEIL - 0.4, 'slate', seg=10, caps=False)
    k.cyl(0, 0, CEIL - 0.48, 0.2, 0.2, 0.08, 'slate', seg=10)
    k.cyl(0, 0, 0.0, 0.2, 0.2, 0.12, 'cove', seg=10)
    k.col(-0.2, 0.2, -0.2, 0.2, 0.0, CEIL - 0.4)
    k.finish('DeckColumn', ao=ao)


def office_window(part):
    """the main office's counter window, through the 1 m wall: a glazed opening 0.95 - 2.4 m with a transaction ledge
    on the front (the lobby), the office's paint on the back; the glass (a companion) sits in the wall's middle"""
    def fn(k):
        xa = -0.38 if part == 'L' else -0.5
        xb = 0.38 if part == 'R' else 0.5
        for side in (0, 180):
            k.push(0, 0, side)
            paint_i(k, 0.0, 0.95)
            paint_i(k, 2.4, WALL_H)
            # the wall beside the opening at a run's end (seen from the back, the left end is on the right)
            left = (part == 'L') == (side == 0)
            if part in 'LR':
                a, b = (-0.5, -0.38) if left else (0.38, 0.5)
                k.fq(a, b, Y0, 0.95, 2.4, 'wallC')
            k.pop()
        k.uq(xa, xb, -0.5, 0.5, 0.95, 'woodL')
        k.dq(xa, xb, -0.5, 0.5, 2.4, 'wallC')
        if part == 'L':
            k.rq(xa, -0.5, 0.5, 0.95, 2.4, 'wallC')
        if part == 'R':
            k.lq(xb, -0.5, 0.5, 0.95, 2.4, 'wallC')
        k.bx(xa, xb, -0.82, -0.5, 1.02, 1.07, 'wood')
        k.bx(xa + 0.05, xb - 0.05, -0.04, 0.04, 0.95, 1.0, 'steelD', ink=False)
        k.bx(xa + 0.05, xb - 0.05, -0.04, 0.04, 2.35, 2.4, 'steelD', ink=False)
        if part == 'M':
            k.bx(-0.45, 0.45, -0.53, -0.5, 2.5, 2.85, 'slate', cull='k')
            k.text('MAIN OFFICE', 0.0, -0.533, 2.6, 0.17, 'paper', font='display', maxw=0.84)
    return fn


def office_glass(k):
    k.fq(-0.5, 0.5, 0.0, 1.0, 2.35, 'navy')
    k.fq(-0.35, -0.1, -0.003, 1.2, 2.2, 'steelD')
    k.bq(-0.5, 0.5, 0.0, 1.0, 2.35, 'navy')


# ================================================================ the wall art catalogue (built front + back)
def build_art(k, ao):
    for v, c in enumerate(('slate', 'lockT', 'lockR')):
        faces(k, ao, 'Lk' + 'ABC'[v], lambda k, c=c: lockers(k, c))
    for p in 'LMRT':
        faces(k, ao, 'WB_' + p, whiteboard(p))
    faces(k, ao, 'Cork', corkboard)
    faces(k, ao, 'PosterA', poster('READ', 'EVERY DAY', 'chD', 'paper', deco_star))
    faces(k, ao, 'PosterB', poster('THINK', 'ASK QUESTIONS', 'chA', 'paper'))
    faces(k, ao, 'PosterC', poster('BE KIND', 'CHALKSTONE WAY', 'gold', 'navy', deco_star))
    faces(k, ao, 'PosterMath', poster('A2 + B2', '= C2', 'navy', 'gold'))
    faces(k, ao, 'PosterCode', poster('<CODE/>', 'BUILD THINGS', 'black', 'exitG'))
    faces(k, ao, 'PosterCell', poster('THE CELL', '', 'skyL', 'navy', deco_cell))
    faces(k, ao, 'Clock', clock)
    faces(k, ao, 'Win', window_i, glow=window_i_glow)
    for p in 'LMR':
        faces(k, ao, 'PT_' + p, periodic(p))
    faces(k, ao, 'EyeWash', eyewash)
    faces(k, ao, 'FireExt', fire_ext)
    faces(k, ao, 'KitPass', kitchen_pass)
    faces(k, ao, 'Menu', menu_board, glow=menu_glow)
    faces(k, ao, 'Clere', clerestory, glow=clerestory_glow)
    faces(k, ao, 'Honor', honour)
    for p in 'LMR':
        faces(k, ao, 'TC_' + p, trophy_case(p), glow=trophy_glow(p))
        faces(k, ao, 'Map_' + p, world_map(p))
    for p in 'LMR':
        faces(k, ao, 'OW_' + p, office_window(p))
    faces(k, ao, 'OW_Glass', office_glass)
    faces(k, ao, 'Timeline', timeline)
    for v in range(2):
        faces(k, ao, 'Art' + 'AB'[v], student_art(v))
    faces(k, ao, 'DoorBoys', closed_door('BOYS', 'slate'))
    faces(k, ao, 'DoorGirls', closed_door('GIRLS', 'curtain'))
    faces(k, ao, 'DoorJan', closed_door('CUSTODIAN', 'steel'))
    faces(k, ao, 'Fountain', fountain)
    faces(k, ao, 'Pad', pads)
    for p in 'LR':
        faces(k, ao, 'SB_' + p, scoreboard(p), glow=scoreboard_glow(p))
    for v in range(4):
        faces(k, ao, 'Banner%d' % v, banner(v))
    for v in range(4):
        faces(k, ao, 'Flag%d' % v, flags(v))
    # signs sliced over modules
    mk = sliced('CHALKSTONE CAFE', 8, 0.72, 5.6, 'slate', shadow='gold')
    for i in range(8):
        faces(k, ao, 'SignCafe%d' % i, mk(i))
    mk = sliced('ROBOTICS CLUB', 8, 0.5, 2.9, 'paper', bg='navy')
    for i in range(8):
        faces(k, ao, 'SignRobo%d' % i, mk(i))
    mk = sliced('LIBRARY', 5, 0.62, 5.4, 'slate', shadow='gold')
    for i in range(5):
        faces(k, ao, 'SignLib%d' % i, mk(i))
    # exterior
    faces(k, ao, 'XWin', window_x)
    faces(k, ao, 'XPipe', downspout)
    for p in 'LR':
        faces(k, ao, 'XDoor_' + p, ext_door(p))
    mk = sliced('CHALKSTONE ACADEMY', 13, 0.95, 5.0, 'stone', ext=True, font='serif', shadow='brick2')
    for i in range(13):
        faces(k, ao, 'XSign%d' % i, mk(i))
    mk = sliced('GO COMETS', 8, 1.1, 5.0, 'gold', ext=True, bg='slate')
    for i in range(8):
        faces(k, ao, 'XBanner%d' % i, mk(i))


def build_struct(k, ao):
    build_finishes(k, ao)
    build_art(k, ao)
    build_doors(k, ao)
    build_gate(k, ao)
    build_ceilings(k, ao)
    build_floors(k, ao)
    build_stairs(k, ao)
