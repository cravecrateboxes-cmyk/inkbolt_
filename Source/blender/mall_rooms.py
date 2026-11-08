"""INKBOLT kit-mall: walk-in shop rooms (one 5 x 6 m piece per shop, both storeys; built by fam_kit_mall.py).

Each room stands behind a walk-in bay (tools/mall_zones.py): front (Blender -Y, y = -3) toward the bay's doorway
(x -1.5 .. 1.5) and its two display windows, the band's wall cells round the other three sides. The piece draws the
floor finish, the walls (2 cm inside the wall cells, so the neighbouring pilasters' side faces stay hidden), the
ceiling at RH with light panels, a cornice, a back-of-house door and the shop's fittings. Fittings stand against the
side walls (at most 0.5 m deep) and on one island in the middle, so two 1.4 m aisles lead to the back of the room:
cover to fight round, room for robots to follow. The front 1.8 m stay clear (a pickup may lie at (0, -1.5)).
Collision: one box per fitting, cut to what is drawn at player height (collision-audit.spec.js).
"""
import math

from fam_kit_mall import (PM, make, col_box, fq, bq, uq, dq, lq, rq, poly, disc, vdisc, shoe, bag, cake, plant, figure,
                          txt, ROOM, RH)

WX, WY0, WY1 = 2.48, -3.0, 2.98      # inner wall faces (the wall cells start at 2.5 / 3.0)
COLS = []


def new(pal):
    return PM(pal)


def solid(cols, x0, y0, z0, x1, y1, z1):
    cols.append(col_box(x0, y0, z0, x1, y1, z1))


# ---------------------------------------------------------------- shell
def shell(m, key, floor='planks', door_x=-1.55):
    fl, fl2, wall, trim = ROOM[key]
    uq(m, -WX, WX, WY0, WY1, 0.014, fl)
    if floor == 'planks':          # boards running front to back
        x = -WX + 0.31
        while x < WX - 0.1:
            uq(m, x, x + 0.018, WY0, WY1, 0.018, fl2)
            x += 0.31
    elif floor == 'tiles':         # 1 m checker
        for i in range(5):
            for j in range(6):
                if (i + j) % 2:
                    uq(m, max(-WX, -2.5 + i), min(WX, -1.5 + i), max(WY0, -3.0 + j), min(WY1, -2.0 + j), 0.018, fl2)
    elif floor == 'carpet':        # a border and a centre field
        uq(m, -WX + 0.35, WX - 0.35, WY0 + 0.4, WY1 - 0.35, 0.018, fl2)
        uq(m, -WX + 0.5, WX - 0.5, WY0 + 0.55, WY1 - 0.5, 0.022, fl)
    # walls, skirting, a trim band under the cornice
    rq(m, -WX, WY0, WY1, 0.0, RH, wall)
    lq(m, WX, WY0, WY1, 0.0, RH, wall)
    fq(m, -WX, WX, WY1, 0.0, RH, wall)
    m.bx(-WX, -WX + 0.025, WY0, WY1, 0.0, 0.12, trim, hull='none', cull='bfkl')
    m.bx(WX - 0.025, WX, WY0, WY1, 0.0, 0.12, trim, hull='none', cull='bfkr')
    m.bx(-WX + 0.025, WX - 0.025, WY1 - 0.025, WY1, 0.0, 0.12, trim, hull='none', cull='bklr')
    for (a, b) in ((RH - 0.42, RH - 0.36),):
        rq(m, -WX + 0.003, WY0, WY1, a, b, trim)
        lq(m, WX - 0.003, WY0, WY1, a, b, trim)
        fq(m, -WX, WX, WY1 - 0.003, a, b, trim)
    # ceiling: plaster with a cove round the edge and three lit panels down the middle
    dq(m, -WX, WX, WY0, WY1, RH, 'cream')
    m.bx(-WX, -WX + 0.3, WY0, WY1, RH - 0.2, RH, 'paper', hull='none', cull='tfkl')
    m.bx(WX - 0.3, WX, WY0, WY1, RH - 0.2, RH, 'paper', hull='none', cull='tfkr')
    m.bx(-WX + 0.3, WX - 0.3, WY1 - 0.3, WY1, RH - 0.2, RH, 'paper', hull='none', cull='tklr')
    for j in range(3):
        y = -2.0 + j * 1.9
        m.bx(-0.95, 0.95, y - 0.5, y + 0.5, RH - 0.03, RH, trim, hull='none', cull='t')
        dq(m, -0.9, 0.9, y - 0.45, y + 0.45, RH - 0.035, 'lightW')
    # back-of-house door: frame, leaf, kick plate, push plate, a "STAFF ONLY" plate
    x = door_x
    fq(m, x - 0.52, x + 0.52, WY1 - 0.004, 0.0, 2.25, trim)
    fq(m, x - 0.45, x + 0.45, WY1 - 0.008, 0.0, 2.15, 'stone2')
    fq(m, x - 0.45, x + 0.45, WY1 - 0.011, 0.02, 0.28, 'steel')
    fq(m, x + 0.25, x + 0.33, WY1 - 0.011, 0.95, 1.25, 'chrome')
    fq(m, x - 0.25, x + 0.25, WY1 - 0.011, 1.55, 1.8, 'paper')
    txt(m, 'STAFF ONLY', x, WY1 - 0.014, 1.675, 0.055, 'redT', font='cond', valign='m', maxw=0.44)
    m.bx(x - 0.12, x + 0.12, WY1 - 0.12, WY1 - 0.008, 2.32, 2.46, 'redT', hull='none', cull='k')   # exit light
    fq(m, x - 0.1, x + 0.1, WY1 - 0.123, 2.35, 2.43, 'lightW')


def cash_desk(m, cols, x0, x1, y0, y1, body, top='cream', front=-1):
    """counter (0 .. 1.0) with a till, a card reader and a paper bag; front: -1 = faces -Y (toward the doorway)"""
    m.bx(x0, x1, y0, y1, 0.0, 0.95, body, hull='full', cull='b')
    m.bx(x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, 0.95, 1.0, top, hull='full')
    if front < 0:
        fq(m, x0 + 0.08, x1 - 0.08, y0 - 0.003, 0.15, 0.8, top)
    cx = (x0 + x1) / 2
    m.bx(cx - 0.2, cx + 0.2, (y0 + y1) / 2 - 0.05, (y0 + y1) / 2 + 0.15, 1.0, 1.1, 'dark', hull='none', cull='b')
    m.bx(cx - 0.17, cx + 0.17, (y0 + y1) / 2 + 0.02, (y0 + y1) / 2 + 0.06, 1.1, 1.36, 'dark', hull='none', cull='b')
    fq(m, cx - 0.14, cx + 0.14, (y0 + y1) / 2 + 0.017, 1.13, 1.33, 'sky')
    m.bx(cx + 0.3, cx + 0.42, (y0 + y1) / 2 - 0.1, (y0 + y1) / 2 + 0.05, 1.0, 1.05, 'sign', hull='none', cull='b')
    m.prism([((y0 + y1) / 2 - 0.07, 1.0), ((y0 + y1) / 2 + 0.07, 1.0), ((y0 + y1) / 2 + 0.05, 1.28), ((y0 + y1) / 2 - 0.05, 1.28)],
            cx - 0.48, cx - 0.3, ['woodL'], hull='none')
    solid(cols, x0 - 0.04, y0 - 0.04, 0.0, x1 + 0.04, y1 + 0.04, 1.0)


def wall_shelf(m, cols, side, y0, y1, h, colors, frame='wood', step=0.13, n=4, depth=0.4, kind='books'):
    """shelving against a side wall (side -1 = left wall, +1 = right wall): carcass, boards, stock painted on the
    shelf back (books / boxes) facing the room"""
    xw = side * WX
    xi = xw - side * depth
    a, b = min(xw, xi), max(xw, xi)
    # carcass: two end panels, top, plinth, a back panel
    for y in (y0, y1 - 0.04):
        m.bx(a, b, y, y + 0.04, 0.0, h - 0.05, frame, hull='full', cull='b')
    m.bx(a, b, y0, y1, h - 0.05, h, frame, hull='full')
    m.bx(a, b, y0 + 0.04, y1 - 0.04, 0.0, 0.14, frame, hull='none', cull='b')
    (rq if side < 0 else lq)(m, xw + side * -0.012, y0 + 0.04, y1 - 0.04, 0.14, h - 0.05, 'intD' if kind == 'books' else 'cream')
    for k in range(n):
        zb = 0.12 + (k + 1) * (h - 0.2) / (n + 0.4)
        m.bx(a, b, y0 + 0.04, y1 - 0.04, zb - 0.03, zb, frame, hull='none', cull='b')
        y = y0 + 0.07
        i = 0
        while y < y1 - 0.12:
            w = step * (0.7 + 0.5 * ((i * 7 + k * 3) % 5) / 4)
            hh = (h - 0.2) / (n + 0.4) * (0.5 + 0.35 * ((i * 3 + k) % 3) / 2)
            xs = xw - side * (depth - 0.06)
            (rq if side < 0 else lq)(m, xs, y, min(y + w - 0.012, y1 - 0.07), zb + 0.004, zb + hh, colors[(i + k) % len(colors)])
            y += w
            i += 1
    solid(cols, a, y0, 0.0, b, y1, h)


def island(m, cols, x0, x1, y0, y1, h, body, top, hull='full'):
    m.bx(x0, x1, y0, y1, 0.0, h - 0.05, body, hull=hull, cull='b')
    m.bx(x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, h - 0.05, h, top, hull=hull)
    solid(cols, x0 - 0.04, y0 - 0.04, 0.0, x1 + 0.04, y1 + 0.04, h)


def glass_case(m, x0, x1, y0, y1, z0, z1, trim='gold'):
    """a glazed case drawn as its frame (corner posts, top rim) with glass streaks on the sides, so what lies in it
    shows (the toon glass is not see-through)"""
    t = 0.025
    for (x, y) in ((x0, y0), (x1 - t, y0), (x0, y1 - t), (x1 - t, y1 - t)):
        m.bx(x, x + t, y, y + t, z0, z1, trim, hull='none', cull='b')
    m.bx(x0 + t, x1 - t, y0, y0 + t, z1 - t, z1, trim, hull='none')
    m.bx(x0 + t, x1 - t, y1 - t, y1, z1 - t, z1, trim, hull='none')
    m.bx(x0, x0 + t, y0 + t, y1 - t, z1 - t, z1, trim, hull='none')
    m.bx(x1 - t, x1, y0 + t, y1 - t, z1 - t, z1, trim, hull='none')
    h = z1 - z0 - t
    for (a, b, w) in ((0.15, 0.08, 0.06), (0.45, 0.04, 0.03)):   # streaks on the long sides, both faces
        for (yy, n) in ((y0 + 0.012, (0, -1, 0)), (y1 - 0.012, (0, 1, 0))):
            xa = x0 + (x1 - x0) * a
            poly(m, [(xa, yy, z0 + h * 0.2), (xa + w, yy, z0 + h * 0.2), (xa + w + h * 0.5, yy, z0 + h * 0.8), (xa + h * 0.5, yy, z0 + h * 0.8)], 'glassL', n)
        for (xx, n) in ((x0 + 0.012, (-1, 0, 0)), (x1 - 0.012, (1, 0, 0))):
            ya = y0 + (y1 - y0) * a
            poly(m, [(xx, ya, z0 + h * 0.2), (xx, ya + w, z0 + h * 0.2), (xx, ya + w + h * 0.5, z0 + h * 0.8), (xx, ya + h * 0.5, z0 + h * 0.8)], 'glassL', n)


def sign_board(m, x, y, z, w, hgt, c, word, lc, font='display'):
    """a board on the back wall with a word on it"""
    fq(m, x - w / 2, x + w / 2, y, z, z + hgt, c)
    txt(m, word, x, y - 0.004, z + hgt / 2, hgt * 0.45, lc, font=font, valign='m', maxw=w * 0.85)


def pendant(m, x, y, c='brass', shade='cream', drop=0.7):
    m.cy((x, y, RH - drop), 0.008, 0.008, drop, 'dark', seg=4, hull='none', caps=False)
    m.cy((x, y, RH - drop - 0.18), 0.22, 0.08, 0.2, shade, seg=10, hull='none')
    disc(m, x, y, RH - drop - 0.184, 0.19, 'light', seg=10, up=False)


def chair(m, cols, x, y, c, face=1):
    """soft armchair (0.8 x 0.8), back toward -face*Y"""
    m.bx(x - 0.4, x + 0.4, y - 0.38, y + 0.38, 0.0, 0.42, c, hull='full', cull='b')
    yb = y - face * 0.3
    m.bx(x - 0.29, x + 0.29, min(yb - 0.1, yb + 0.1), max(yb - 0.1, yb + 0.1), 0.42, 0.95, c, hull='full')
    for sx in (-1, 1):
        m.bx(min(x + sx * 0.4, x + sx * 0.3), max(x + sx * 0.4, x + sx * 0.3), y - 0.38, y + 0.38, 0.42, 0.62, c, hull='full')
    m.bx(x - 0.3, x + 0.3, y - 0.3, y + 0.28, 0.42, 0.5, 'cream', hull='none', cull='b')
    solid(cols, x - 0.4, y - 0.38, 0.0, x + 0.4, y + 0.38, 0.95)


# ---------------------------------------------------------------- the rooms
def room_atelier(m, cols):
    """Atelier (fashion): clothing rails along both walls, mannequins on a round plinth, two fitting rooms, cash desk"""
    shell(m, ('rose', 'Lo'), 'planks', door_x=1.7)
    garments = ('navy', 'rose', 'cream', 'gold', 'tealM', 'sign', 'roseL')
    for side in (-1, 1):
        x = side * (WX - 0.3)
        y0, y1 = (-2.3, 1.4) if side < 0 else (-2.3, 0.9)
        m.bx(x - 0.015, x + 0.015, y0, y1, 1.62, 1.66, 'chrome', hull='none')
        for y in (y0, y1):
            m.cy((x, y, 0.0), 0.02, 0.02, 1.62, 'chrome', seg=5, hull='none')
            m.cy((x, y, 0.0), 0.12, 0.12, 0.03, 'chrome', seg=8, hull='none')
        y = y0 + 0.1
        i = 0
        while y < y1 - 0.12:   # garments on hangers, side on to the room
            c = garments[(i * 3 + (side > 0)) % len(garments)]
            m.bx(x - 0.22, x + 0.22, y, y + 0.1, 0.82 + 0.08 * (i % 3 == 0), 1.58, c, hull='none', cull='b')
            m.bx(x - 0.01, x + 0.01, y + 0.03, y + 0.07, 1.58, 1.62, 'dark', hull='none', cull='b')
            y += 0.2
            i += 1
        solid(cols, x - 0.23, y0, 0.0, x + 0.23, y1, 1.66)
        # mirror panel and a framed print above
        (rq if side < 0 else lq)(m, side * (WX - 0.004), -2.6, -2.45, 0.3, 2.3, 'brass')
    # round plinth with three mannequins in the middle
    m.cy((0, -0.25, 0), 0.62, 0.62, 0.25, 'cream', seg=12)
    m.cy((0, -0.25, 0.25), 0.64, 0.64, 0.03, 'rose', seg=12, hull='none')
    for i, (dx, dy, c, l) in enumerate(((-0.3, -0.4, 'rose', 'cream'), (0.3, -0.35, 'navy', 'dark'), (0.0, 0.05, 'gold', 'navy'))):
        figure(m, dx, dy - 0.25 + 0.25, 0.28, c, legs=l)
    solid(cols, -0.62, -0.87, 0.0, 0.62, 0.37, 1.85)
    # fitting rooms in the back left corner: two cubicles with curtains and a sign
    x0, x1, y0 = -WX, -0.5, 1.75
    m.bx(x0, x1, y0, WY1, 2.3, 2.42, 'cream', hull='full')
    for x in (x0 + 0.02, -1.5, x1 - 0.06):
        m.bx(x, x + 0.06, y0, WY1, 0.0, 2.3, 'cream', hull='full', cull='b')
    for (a, b, c) in ((x0 + 0.08, -1.5, 'roseL'), (-1.44, x1 - 0.06, 'rose')):
        n = 6
        for k in range(n):   # curtain folds
            xa = a + k * (b - a) / n
            m.bx(xa, xa + (b - a) / n - 0.01, y0 + (0.0 if k % 2 else 0.03), y0 + 0.06, 0.12, 2.25, c, hull='none', cull='b')
        m.bx(a, b, y0 + 0.02, y0 + 0.05, 2.25, 2.29, 'chrome', hull='none')
    fq(m, -1.95, -0.65, y0 - 0.005, 2.32, 2.41, 'rose')
    txt(m, 'Fitting Rooms', -1.3, y0 - 0.009, 2.365, 0.06, 'paper', font='serif', valign='m', maxw=1.1)
    solid(cols, x0, y0, 0.0, x1, WY1, 2.42)
    # cash desk back right, a vase of flowers on it
    cash_desk(m, cols, 0.55, 2.0, 1.45, 2.0, 'sign', top='roseL')
    m.cy((1.8, 1.7, 1.0), 0.06, 0.08, 0.22, 'paper', seg=8, hull='none')
    m.sp((1.8, 1.7, 1.32), 0.12, 'rose', seg=(6, 3), hull='none')
    sign_board(m, 0.55, WY1 - 0.004, 2.35, 1.2, 0.45, 'sign', 'Atelier', 'roseL', font='serif')
    pendant(m, 0.0, -0.25, shade='roseL', drop=0.6)


def room_signal(m, cols):
    """SIGNAL (electronics): TV wall, phone tables, accessory pegboards, a genius bar style desk"""
    shell(m, ('sky', 'Lo'), 'tiles', door_x=1.85)
    # TV wall along the right side: dark panel with six screens
    lq(m, WX - 0.006, -2.4, 1.2, 0.9, 2.65, 'intD')
    for i in range(3):
        for k in range(2):
            y = -2.25 + i * 1.18
            z = 1.0 + k * 0.85
            m.bx(WX - 0.08, WX - 0.006, y, y + 1.04, z, z + 0.7, 'dark', hull='none', cull='r')
            lq(m, WX - 0.083, y + 0.04, y + 1.0, z + 0.04, z + 0.66, ('sky', 'blueT', 'tealM', 'skyL', 'violet', 'sky')[i * 2 + k])
            lq(m, WX - 0.086, y + 0.1, y + 0.45, z + 0.4, z + 0.6, 'skyL')
    m.bx(WX - 0.45, WX, -2.4, 1.2, 0.0, 0.62, 'paper', hull='full', cull='b')   # media unit
    lq(m, WX - 0.453, -2.3, 1.1, 0.45, 0.5, 'sky')
    solid(cols, WX - 0.45, -2.4, 0.0, WX, 1.2, 0.62)
    # accessory pegboard on the left: cases, headphones, cables
    rq(m, -WX + 0.006, -2.4, 1.0, 0.8, 2.4, 'paper')
    for i in range(6):
        for k in range(3):
            y = -2.25 + i * 0.55
            z = 1.0 + k * 0.48
            c = ('blueT', 'redT', 'dark', 'sky', 'yellow', 'greenT')[(i + k) % 6]
            m.bx(-WX + 0.006, -WX + 0.05, y, y + 0.3, z, z + 0.36, c, hull='none', cull='l')
    m.bx(-WX, -WX + 0.45, -2.4, 1.0, 0.0, 0.85, 'skyL', hull='full', cull='b')
    m.bx(-WX, -WX + 0.48, -2.43, 1.03, 0.85, 0.9, 'paper', hull='full')
    solid(cols, -WX, -2.43, 0.0, -WX + 0.48, 1.03, 0.9)
    # phone table in the middle: white slab, a row of phones and tablets on it
    island(m, cols, -0.55, 0.55, -0.9, 0.5, 0.92, 'paper', 'chrome')
    fq(m, -0.5, 0.5, -0.945, 0.2, 0.75, 'sky')
    txt(m, 'SIGNAL', 0.0, -0.95, 0.47, 0.12, 'paper', font='display', valign='m', maxw=0.8)
    for i in range(4):
        y = -0.75 + i * 0.36
        for sx in (-1, 1):
            m.bx(sx * 0.3 - 0.07, sx * 0.3 + 0.07, y, y + 0.13, 0.92, 0.935, 'dark', hull='none', cull='b')
            uq(m, sx * 0.3 - 0.06, sx * 0.3 + 0.06, y + 0.01, y + 0.12, 0.939, ('sky', 'blueT', 'skyL', 'tealM')[i])
    # round demo table with tablets and a smart speaker in the back left
    m.cy((-1.55, 1.75, 0), 0.08, 0.08, 0.75, 'chrome', seg=6, hull='none')
    m.cy((-1.55, 1.75, 0.75), 0.45, 0.45, 0.05, 'paper', seg=12)
    for i in range(3):
        a_ = i / 3 * 2 * math.pi
        x, y = -1.55 + math.cos(a_) * 0.25, 1.75 + math.sin(a_) * 0.25
        m.bx(x - 0.1, x + 0.1, y - 0.07, y + 0.07, 0.8, 0.815, 'dark', hull='none', cull='b')
        uq(m, x - 0.09, x + 0.09, y - 0.06, y + 0.06, 0.819, ('sky', 'violet', 'tealM')[i])
    m.cy((-1.55, 1.75, 0.8), 0.06, 0.06, 0.16, 'navy', seg=8, hull='none')
    solid(cols, -2.0, 1.3, 0.0, -1.1, 2.2, 0.8)
    # service desk at the back, a big lit logo over it
    cash_desk(m, cols, -0.6, 1.4, 1.9, 2.4, 'navy', top='paper')
    m.bx(-0.9, 1.3, WY1 - 0.06, WY1, 2.0, 2.8, 'navy', hull='none', cull='k')
    txt(m, 'SIGNAL', 0.2, WY1 - 0.064, 2.4, 0.32, 'paper', font='display', valign='m', maxw=2.0, shadow='sky', shadow_off=(0.03, -0.04))


def room_coffee(m, cols):
    """The Coffee House: counter with an espresso machine and a pastry case, menu boards, cafe tables"""
    shell(m, ('orange', 'Lo'), 'tiles', door_x=1.85)
    # counter across the back, leaving the staff door free on the right
    y0, y1 = 1.55, 2.15
    m.bx(-WX, 1.1, y0, y1, 0.0, 1.0, 'wood2', hull='full', cull='b')
    m.bx(-WX, 1.14, y0 - 0.05, y1 + 0.03, 1.0, 1.05, 'cream', hull='full')
    for i in range(6):
        fq(m, -2.3 + i * 0.57, -1.8 + i * 0.57, y0 - 0.003, 0.15, 0.85, 'wood' if i % 2 else 'woodL')
    solid(cols, -WX, y0 - 0.05, 0.0, 1.14, y1 + 0.03, 1.05)
    # espresso machine, grinder, cups
    m.bx(-1.9, -1.0, y0 + 0.15, y1 - 0.05, 1.05, 1.5, 'chrome', hull='full')
    m.bx(-1.85, -1.05, y0 + 0.13, y0 + 0.17, 1.15, 1.42, 'redT', hull='none')
    for x in (-1.7, -1.2):
        m.cy((x, y0 + 0.08, 1.12), 0.035, 0.035, 0.12, 'dark', seg=6, hull='none')
    m.cy((-0.7, y0 + 0.35, 1.05), 0.1, 0.1, 0.35, 'dark', seg=8)
    m.cy((-0.7, y0 + 0.35, 1.4), 0.12, 0.06, 0.15, 'glassL', seg=8, hull='none')
    for i in range(4):
        m.cy((-2.3, y0 + 0.12 + i * 0.12, 1.05 + 0.0), 0.045, 0.04, 0.1, 'paper', seg=6, hull='none')
    # pastry case on the right of the counter
    glass_case(m, -0.3, 1.05, y0 + 0.02, y1 - 0.08, 1.05, 1.4, trim='chrome')
    for i in range(3):
        cake(m, -0.1 + i * 0.42, y0 + 0.28, 1.06, 0.12, ('roseL', 'wood', 'orangeL')[i], top=('paper', 'cream', 'redT')[i], h=0.1)
    # menu boards over the counter, a neon script
    for i, (head) in enumerate(('COFFEE', 'TEA', 'CAKES')):
        x = -1.8 + i * 1.15
        fq(m, x - 0.5, x + 0.5, WY1 - 0.004, 1.65, 2.6, 'sign')
        txt(m, head, x, WY1 - 0.008, 2.42, 0.11, 'gold', font='display', maxw=0.8)
        for j in range(4):
            fq(m, x - 0.4, x + 0.15 - 0.08 * (j % 2), WY1 - 0.008, 1.8 + j * 0.13, 1.84 + j * 0.13, 'paper')
    txt(m, 'Coffee', -0.65, WY1 - 0.006, 2.82, 0.2, 'orange', font='script', valign='m', maxw=1.2, shadow='terraD', shadow_off=(0.03, -0.03))
    # three cafe tables with chairs: two by the walls, one tall round table in the middle
    for (x, y) in ((-1.75, -1.6), (1.75, -1.0)):
        m.cy((x, y, 0), 0.22, 0.22, 0.03, 'sign', seg=8, hull='none')
        m.cy((x, y, 0.03), 0.035, 0.035, 0.7, 'chrome', seg=6, hull='none')
        m.cy((x, y, 0.73), 0.38, 0.38, 0.04, 'paper', seg=12)
        m.cy((x + 0.1, y, 0.77), 0.045, 0.04, 0.09, 'cream', seg=6, hull='none')
        solid(cols, x - 0.38, y - 0.38, 0.0, x + 0.38, y + 0.38, 0.77)
        for dy in (-0.55, 0.55):
            m.cy((x, y + dy, 0), 0.025, 0.025, 0.45, 'chrome', seg=5, hull='none')
            m.cy((x, y + dy, 0.45), 0.19, 0.19, 0.05, 'orange', seg=8)
            m.bx(x - 0.17, x + 0.17, y + dy + (0.15 if dy > 0 else -0.19), y + dy + (0.19 if dy > 0 else -0.15), 0.5, 0.88, 'orange', hull='full')
            solid(cols, x - 0.19, y + dy - 0.19, 0.0, x + 0.19, y + dy + 0.19, 0.5)
    m.cy((0, -0.2, 0), 0.25, 0.25, 0.03, 'sign', seg=8, hull='none')
    m.cy((0, -0.2, 0.03), 0.04, 0.04, 1.02, 'chrome', seg=6, hull='none')
    m.cy((0, -0.2, 1.05), 0.45, 0.45, 0.05, 'wood', seg=12)
    for i in range(2):
        m.cy((-0.15 + 0.3 * i, -0.2 + 0.1 * i, 1.1), 0.045, 0.04, 0.1, 'cream', seg=6, hull='none')
    solid(cols, -0.45, -0.65, 0.0, 0.45, 0.25, 1.1)
    for (sx, sy) in ((-0.62, 0.3), (0.62, -0.7)):
        m.cy((sx, sy, 0), 0.025, 0.025, 0.72, 'chrome', seg=5, hull='none')
        m.cy((sx, sy, 0.72), 0.18, 0.18, 0.06, 'orange', seg=8)
        solid(cols, sx - 0.18, sy - 0.18, 0.0, sx + 0.18, sy + 0.18, 0.78)
    for x in (-1.0, 0.9):
        pendant(m, x, 0.6, shade='orange', drop=0.8)


def room_books(m, cols):
    """Northfield Books: tall shelves on both walls, a table of new titles, two reading chairs with a lamp"""
    shell(m, ('mint', 'Lo'), 'planks', door_x=-1.6)
    spines = ['tealM', 'redT', 'gold', 'navy', 'cream', 'orange', 'violet', 'greenT']
    for side in (-1, 1):
        for (y0, y1) in ((-2.6, -0.5), (-0.4, 1.5)):
            wall_shelf(m, cols, side, y0, y1, 2.35, spines, frame='wood2', step=0.09, n=4)
        (rq if side < 0 else lq)(m, side * (WX - 0.004), -2.6, 1.5, 2.55, 2.85, 'tealD')
        txt(m, ('FICTION', 'TRAVEL')[side > 0], side * (WX - 0.008), -0.55, 2.7, 0.13, 'mintL', face='x+' if side < 0 else 'x-',
            font='serif', valign='m', maxw=1.6)
    # new titles table: book stacks and a "NEW" card
    island(m, cols, -0.6, 0.6, -0.85, 0.35, 0.78, 'wood', 'woodL')
    for i, (x, y, n) in enumerate(((-0.35, -0.6, 4), (0.05, -0.55, 3), (0.35, -0.3, 5), (-0.3, 0.05, 3), (0.2, 0.15, 2))):
        for k in range(n):
            m.bx(x - 0.13, x + 0.13, y - 0.09, y + 0.09, 0.78 + k * 0.045, 0.82 + k * 0.045, spines[(i + k) % 8], hull='none', cull='b')
    m.prism([(-0.8, 0.78), (-0.74, 0.78), (-0.77, 0.98)], -0.12, 0.12, ['paper'], hull='none')
    txt(m, 'NEW', 0.0, -0.792, 0.86, 0.05, 'redT', font='display', valign='m', maxw=0.2)
    # reading corner at the back: two armchairs, a side table, a floor lamp, a rug
    uq(m, -1.8, 0.6, 1.75, 2.85, 0.026, 'tealD')
    chair(m, cols, -1.45, 2.3, 'redT', face=-1)
    chair(m, cols, 0.25, 2.3, 'tealM', face=-1)
    m.cy((-0.6, 2.4, 0), 0.22, 0.22, 0.55, 'wood2', seg=8)
    m.bx(-0.7, -0.5, 2.3, 2.45, 0.55, 0.6, 'navy', hull='none', cull='b')
    solid(cols, -0.82, 2.18, 0.0, -0.38, 2.62, 0.55)
    m.cy((-0.6, 2.75, 0), 0.015, 0.015, 1.5, 'brass', seg=5, hull='none')
    m.cy((-0.6, 2.75, 1.45), 0.2, 0.12, 0.25, 'cream', seg=8, hull='none')
    # cash desk on the right at the back, a stack of bags
    cash_desk(m, cols, 1.0, 2.0, 1.8, 2.45, 'tealD', top='woodL')
    sign_board(m, 1.5, WY1 - 0.004, 2.1, 1.2, 0.42, 'tealD', 'Books', 'mintL', font='serif')
    pendant(m, 0.0, -0.25, shade='tealM', drop=0.7)


def room_toys(m, cols):
    """Toy Workshop: toy shelves, a train table, a giant plush bear, balloons, cash desk"""
    shell(m, ('gold', 'Lo'), 'tiles', door_x=1.7)
    boxes = ['redT', 'blueT', 'greenT', 'orange', 'violet', 'yellow']
    for side in (-1, 1):
        wall_shelf(m, cols, side, -2.6, 0.9 if side > 0 else 1.6, 1.9, boxes, frame='cream', step=0.24, n=3, depth=0.45, kind='toys')
    # train table: green baize, an oval track, a little engine and wagons
    island(m, cols, -0.65, 0.65, -0.95, 0.45, 0.62, 'blueT', 'greenT')
    for i in range(10):
        a0, a1 = i / 10 * 2 * math.pi, (i + 1) / 10 * 2 * math.pi
        for r, c in ((0.42, 'wood2'),):
            poly(m, [(math.cos(a0) * r * 1.1, -0.25 + math.sin(a0) * r * 1.4, 0.625), (math.cos(a1) * r * 1.1, -0.25 + math.sin(a1) * r * 1.4, 0.625),
                     (math.cos(a1) * (r - 0.06) * 1.1, -0.25 + math.sin(a1) * (r - 0.06) * 1.4, 0.625),
                     (math.cos(a0) * (r - 0.06) * 1.1, -0.25 + math.sin(a0) * (r - 0.06) * 1.4, 0.625)], c, (0, 0, 1))
    for k, (y, c) in enumerate(((-0.55, 'redT'), (-0.3, 'yellow'), (-0.05, 'blueT'))):
        m.bx(0.38, 0.52, y, y + 0.2, 0.625, 0.74, c, hull='full')
    m.cy((0.45, -0.48, 0.74), 0.03, 0.03, 0.1, 'dark', seg=6, hull='none')
    # giant plush bear in the back left corner
    bx_, by_ = -1.7, 2.2
    m.sp((bx_, by_, 0.5), 0.5, 'wood', seg=(8, 5))
    m.sp((bx_, by_ - 0.08, 1.25), 0.36, 'wood', seg=(8, 5))
    for sx in (-1, 1):
        m.sp((bx_ + sx * 0.28, by_, 1.55), 0.12, 'wood2', seg=(6, 4))
        m.sp((bx_ + sx * 0.45, by_ - 0.25, 0.3), 0.18, 'wood', seg=(6, 4))
        m.sp((bx_ + sx * 0.12, by_ - 0.42, 1.3), 0.035, 'ink', seg=(5, 3), hull='none')
    m.sp((bx_, by_ - 0.42, 1.18), 0.11, 'woodL', seg=(6, 4))
    m.bx(bx_ - 0.14, bx_ + 0.14, by_ - 0.42, by_ - 0.36, 0.9, 0.98, 'redT', hull='full')
    solid(cols, bx_ - 0.55, by_ - 0.5, 0.0, bx_ + 0.55, by_ + 0.5, 1.55)
    # balloons tied to the cash desk
    cash_desk(m, cols, 0.4, 1.9, 1.85, 2.4, 'redT', top='yellow')
    for i, (x, y, z, c) in enumerate(((0.6, 2.1, 2.5, 'redT'), (0.85, 2.2, 2.75, 'blueT'), (1.05, 2.05, 2.45, 'yellow'), (0.75, 1.95, 2.95, 'greenT'))):
        m.sp((x, y, z), 0.17, c, seg=(6, 4))
        m.bm_((x, y, z - 0.17), (0.5, 2.1, 1.0), 0.008, 'dark', hull='none')
    sign_board(m, 0.0, WY1 - 0.004, 2.4, 1.6, 0.45, 'yellow', 'TOYS!', 'redT')


def room_aurum(m, cols):
    """Aurum (jewellery): glass cases with gold pieces, velvet walls with lit niches, a chandelier"""
    shell(m, ('violet', 'Lo'), 'carpet', door_x=-1.7)
    # wall cases on both sides: dark plinth, glass box, rings / necklaces on cushions
    for side in (-1, 1):
        xw = side * WX
        xi = xw - side * 0.5
        a, b = min(xw, xi), max(xw, xi)
        for (y0, y1) in ((-2.5, -0.9), (-0.6, 1.0)):
            m.bx(a, b, y0, y1, 0.0, 0.85, 'sign', hull='full', cull='b')
            glass_case(m, a, b, y0, y1, 0.85, 1.2)
            m.bx(a + 0.02, b - 0.02, y0 + 0.02, y1 - 0.02, 0.855, 0.87, 'violetD', hull='none', cull='b')
            for i in range(4):
                y = y0 + 0.2 + i * (y1 - y0 - 0.4) / 3
                m.cy(((a + b) / 2, y, 0.87), 0.05, 0.05, 0.02, 'gold', seg=8, hull='none')
                m.cy(((a + b) / 2, y, 0.89), 0.03, 0.03, 0.03, 'sky' if i % 2 else 'redT', seg=6, hull='none')
            solid(cols, a, y0, 0.0, b, y1, 1.2)
            # lit niche with a necklace bust above
            yc = (y0 + y1) / 2
            (rq if side < 0 else lq)(m, xw - side * 0.004, yc - 0.35, yc + 0.35, 1.5, 2.3, 'sign')
            (rq if side < 0 else lq)(m, xw - side * 0.008, yc - 0.3, yc + 0.3, 1.55, 2.25, 'lightW')
            m.prism([(yc - 0.12, 1.55), (yc + 0.12, 1.55), (yc + 0.06, 1.95), (yc - 0.06, 1.95)], xw - side * 0.15 - 0.06, xw - side * 0.15 + 0.06, ['sign'], hull='none')
            m.cy((xw - side * 0.22, yc, 1.8), 0.07, 0.07, 0.015, 'gold', seg=8, rot=(0, 90, 0), hull='none')
    # centre case: a glass box on a gold-trimmed plinth with a crown
    island(m, cols, -0.5, 0.5, -0.8, 0.3, 0.95, 'sign', 'gold')
    glass_case(m, -0.45, 0.45, -0.75, 0.25, 0.95, 1.3)
    m.cy((0, -0.25, 0.95), 0.12, 0.12, 0.12, 'violetD', seg=8, hull='none')
    m.cy((0, -0.25, 1.07), 0.09, 0.11, 0.1, 'gold', seg=8, hull='none')
    cols[-1] = col_box(-0.54, -0.84, 0.0, 0.54, 0.34, 1.3)
    # cash desk at the back right, a gold monogram on the back wall
    cash_desk(m, cols, 0.3, 1.9, 1.9, 2.45, 'violetD', top='gold')
    vdisc(m, (0.0, WY1 - 0.005, 2.3), 0.38, 'gold', 'y-', seg=16)
    vdisc(m, (0.0, WY1 - 0.009, 2.3), 0.32, 'violetD', 'y-', seg=16)
    txt(m, 'A', 0.0, WY1 - 0.013, 2.3, 0.34, 'gold', font='serif', valign='m', maxw=0.4)
    # chandelier
    m.cy((0, -0.25, RH - 0.5), 0.01, 0.01, 0.5, 'gold', seg=4, hull='none', caps=False)
    m.cy((0, -0.25, RH - 0.85), 0.45, 0.15, 0.35, 'gold', seg=10)
    for i in range(8):
        a = i / 8 * 2 * math.pi
        m.sp((math.cos(a) * 0.42, -0.25 + math.sin(a) * 0.42, RH - 0.9), 0.06, 'light', seg=(5, 3), hull='none')


def room_shoes(m, cols):
    """Shoe Gallery: shoe walls on three sides, two try-on benches with footstools, cash desk"""
    shell(m, ('rose', 'Up'), 'carpet', door_x=1.75)
    pairs = ('rose', 'navy', 'paper', 'gold', 'dark', 'redT', 'wood')
    for side in (-1, 1):
        xw = side * WX
        xi = xw - side * 0.35
        a, b = min(xw, xi), max(xw, xi)
        y0, y1 = -2.6, 1.4
        m.bx(a, b, y0, y1, 0.0, 0.3, 'cream', hull='full', cull='b')
        for k in range(4):   # glass shelves with pairs side on
            zb = 0.65 + k * 0.48
            m.bx(a, b, y0, y1, zb - 0.025, zb, 'chrome' if k % 2 else 'paper', hull='none', cull='b')
            xs = xw - side * 0.008
            for i in range(8):   # pairs painted as side profiles on the wall behind the shelf (toe toward the front)
                y = y0 + 0.25 + i * 0.47
                c = pairs[(i + k * 3 + (side > 0)) % len(pairs)]
                for dy in (-0.11, 0.11):
                    poly(m, [(xs, y + dy - 0.1, zb + 0.004), (xs, y + dy + 0.1, zb + 0.004), (xs, y + dy + 0.1, zb + 0.13),
                             (xs, y + dy + 0.02, zb + 0.13), (xs, y + dy - 0.1, zb + 0.05)], c, (-side, 0, 0))
        (rq if side < 0 else lq)(m, xw - side * 0.004, y0, y1, 0.3, 2.6, 'paper')
        solid(cols, a, y0, 0.0, b, y1, 0.3)
        # the shelves themselves (from 0.62 m up) block the walk only above the step-up: one box from the floor
        cols[-1] = col_box(a, y0, 0.0, b, y1, 2.2)
    # try-on bench in the middle (back to back seats), a mirror and two footstools
    m.bx(-0.45, 0.45, -1.0, 0.4, 0.0, 0.45, 'roseL', hull='full', cull='b')
    m.bx(-0.06, 0.06, -1.0, 0.4, 0.45, 0.9, 'rose', hull='full', cull='b')
    for i in range(3):   # buttoned seams on the cushions either side of the back
        for (a, b) in ((-0.44, -0.08), (0.08, 0.44)):
            uq(m, a, b, -0.85 + i * 0.47, -0.82 + i * 0.47, 0.454, 'rose')
    solid(cols, -0.45, -1.0, 0.0, 0.45, 0.4, 0.9)
    shoe(m, -0.3, -0.5, 0.45, 'redT', heel=True)
    shoe(m, 0.25, 0.05, 0.45, 'navy')
    for (x, y) in ((-1.25, 0.9), (1.25, -0.2)):
        m.cy((x, y, 0), 0.2, 0.2, 0.32, 'rose', seg=8)
        solid(cols, x - 0.2, y - 0.2, 0.0, x + 0.2, y + 0.2, 0.32)
    fq(m, -2.0, -0.7, WY1 - 0.004, 0.3, 2.4, 'brass')
    fq(m, -1.95, -0.75, WY1 - 0.008, 0.35, 2.35, 'skyglass')
    poly(m, [(-1.8, WY1 - 0.011, 1.6), (-1.6, WY1 - 0.011, 1.6), (-1.3, WY1 - 0.011, 2.2), (-1.5, WY1 - 0.011, 2.2)], 'glassL', (0, -1, 0))
    cash_desk(m, cols, 0.3, 1.85, 1.9, 2.45, 'rose', top='cream')
    m.bx(0.5, 0.9, 2.0, 2.3, 1.0, 1.25, 'paper', hull='full', cull='b')   # shoe box
    sign_board(m, 0.05, WY1 - 0.004, 2.45, 1.3, 0.42, 'cream', 'Shoe Gallery', 'rose', font='cond')
    pendant(m, 0.0, -0.3, shade='rose', drop=0.6)


def room_optics(m, cols):
    """Lumen Optics: frame walls, an eye chart, a fitting counter with mirrors, an eye-test chair"""
    shell(m, ('sky', 'Up'), 'planks', door_x=-1.8)
    for side in (-1, 1):   # frame walls: lit panels with rows of spectacles
        xw = side * WX
        (rq if side < 0 else lq)(m, xw - side * 0.004, -2.6, 1.3, 0.9, 2.5, 'navy')
        (rq if side < 0 else lq)(m, xw - side * 0.008, -2.5, 1.2, 1.0, 2.4, 'skyL')
        for k in range(4):
            z = 1.2 + k * 0.32
            for i in range(7):
                y = -2.2 + i * 0.5
                c = ('dark', 'redT', 'navy', 'gold', 'tealM')[(i + k) % 5]
                for dy in (-0.075, 0.075):
                    vdisc(m, (xw - side * 0.012, y + dy, z), 0.06, c, 'x+' if side < 0 else 'x-', seg=8)
                (rq if side < 0 else lq)(m, xw - side * 0.012, y - 0.02, y + 0.02, z + 0.01, z + 0.03, c)
        m.bx(min(xw, xw - side * 0.4), max(xw, xw - side * 0.4), -2.6, 1.3, 0.0, 0.85, 'paper', hull='full', cull='b')
        m.bx(min(xw, xw - side * 0.42), max(xw, xw - side * 0.42), -2.62, 1.32, 0.85, 0.9, 'navy', hull='full')
        solid(cols, min(xw, xw - side * 0.42), -2.62, 0.0, max(xw, xw - side * 0.42), 1.32, 0.9)
    # fitting counter in the middle: a table with two mirrors and a tray of frames, two stools
    island(m, cols, -0.55, 0.55, -0.7, 0.3, 0.78, 'navy', 'paper')
    for sx in (-1, 1):
        m.bx(sx * 0.3 - 0.15, sx * 0.3 + 0.15, -0.22, -0.18, 0.78, 1.15, 'chrome', hull='none')
        fq(m, sx * 0.3 - 0.13, sx * 0.3 + 0.13, -0.223, 0.8, 1.13, 'skyglass')
    m.bx(-0.25, 0.25, 0.0, 0.2, 0.78, 0.8, 'dark', hull='none', cull='b')
    for (x, y) in ((-0.35, -1.05), (0.35, 0.65)):
        m.cy((x, y, 0), 0.025, 0.025, 0.62, 'chrome', seg=5, hull='none')
        m.cy((x, y, 0.62), 0.17, 0.17, 0.05, 'sky', seg=8)
        solid(cols, x - 0.17, y - 0.17, 0.0, x + 0.17, y + 0.17, 0.67)
    # eye-test corner at the back: chart on the wall, a chair and a phoropter on an arm
    fq(m, -0.75, 0.15, WY1 - 0.004, 1.0, 2.6, 'paper')
    for i, (row, cap) in enumerate((('E', 0.3), ('F P', 0.16), ('T O Z', 0.11), ('L P E D', 0.08), ('P E C F D', 0.06))):
        txt(m, row, -0.3, WY1 - 0.008, 2.3 - i * 0.3, cap, 'ink', font='sans', valign='m', maxw=0.8)
    chair(m, cols, -0.3, 1.6, 'navy', face=-1)
    m.cy((-1.0, 2.6, 0), 0.04, 0.04, 1.4, 'chrome', seg=6, hull='none')
    m.bm_((-1.0, 2.6, 1.4), (-0.35, 1.45, 1.35), 0.025, 'chrome', hull='none')
    m.bx(-0.55, -0.15, 1.4, 1.5, 1.25, 1.45, 'dark', hull='full')
    cash_desk(m, cols, 0.75, 1.9, 1.7, 2.3, 'navy', top='skyL')
    sign_board(m, 1.3, WY1 - 0.004, 2.4, 1.2, 0.4, 'navy', 'LUMEN', 'skyL', font='sans')


def room_bakery(m, cols):
    """Bakehouse: a glass cake counter, ovens on the back wall, bread racks, a little table"""
    shell(m, ('orange', 'Up'), 'tiles', door_x=1.85)
    # ovens and a proving cabinet along the back wall (behind the counter)
    for i in range(2):
        x = -1.9 + i * 1.0
        m.bx(x - 0.45, x + 0.45, WY1 - 0.7, WY1, 0.0, 2.2, 'steel', hull='full', cull='b')
        for k in range(2):
            z = 0.5 + k * 0.85
            fq(m, x - 0.35, x + 0.35, WY1 - 0.703, z, z + 0.6, 'dark')
            fq(m, x - 0.3, x + 0.3, WY1 - 0.706, z + 0.05, z + 0.55, 'orange')
            m.bx(x - 0.3, x + 0.3, WY1 - 0.78, WY1 - 0.74, z + 0.62, z + 0.66, 'chrome', hull='none')
    solid(cols, -2.35, WY1 - 0.78, 0.0, -0.45, WY1, 2.2)
    # cake counter across the room, glass top with cakes, a gap to the staff side on the right
    y0, y1 = 0.9, 1.5
    m.bx(-WX, 1.0, y0, y1, 0.0, 0.95, 'cream', hull='full', cull='b')
    for i in range(5):
        fq(m, -2.3 + i * 0.66, -1.8 + i * 0.66, y0 - 0.003, 0.15, 0.8, 'orange' if i % 2 else 'orangeL')
    glass_case(m, -WX + 0.01, 1.0, y0, y1, 0.95, 1.35, trim='chrome')
    for i in range(5):
        cake(m, -2.1 + i * 0.68, (y0 + y1) / 2, 0.96, 0.15, ('roseL', 'wood', 'orangeL', 'cream', 'redT')[i], top=('paper', 'cream', 'redT', 'gold', 'paper')[i], h=0.12)
    solid(cols, -WX, y0, 0.0, 1.0, y1, 1.35)
    # bread rack on the right wall
    xw = WX
    for k in range(4):
        zb = 0.3 + k * 0.45
        m.bx(xw - 0.45, xw, -2.46, -0.64, zb - 0.03, zb, 'wood', hull='none', cull='br')
        for i in range(5):
            y = -2.35 + i * 0.37
            m.sp((xw - 0.22, y, zb + 0.08), 0.13, ('wood', 'woodL', 'wood2')[(i + k) % 3], seg=(6, 3), scale=(1.0, 1.4, 0.6), hull='none')
    for y in (-2.5, -0.64):
        m.bx(xw - 0.45, xw, y, y + 0.04, 0.0, 1.95, 'wood2', hull='full', cull='br')
    solid(cols, xw - 0.45, -2.5, 0.0, xw, -0.6, 1.95)
    # a small table with two chairs by the left wall, a chalk board
    x, y = -1.75, -1.2
    m.cy((x, y, 0.03), 0.035, 0.035, 0.7, 'dark', seg=6, hull='none')
    m.cy((x, y, 0.73), 0.36, 0.36, 0.04, 'paper', seg=12)
    cake(m, x, y, 0.77, 0.08, 'roseL', h=0.06)
    solid(cols, x - 0.36, y - 0.36, 0.0, x + 0.36, y + 0.36, 0.77)
    for dy in (-0.55, 0.55):
        m.cy((x, y + dy, 0), 0.025, 0.025, 0.45, 'dark', seg=5, hull='none')
        m.cy((x, y + dy, 0.45), 0.19, 0.19, 0.05, 'orange', seg=8)
        solid(cols, x - 0.19, y + dy - 0.19, 0.0, x + 0.19, y + dy + 0.19, 0.5)
    rq(m, -WX + 0.004, -2.4, -0.2, 1.3, 2.4, 'sign')
    txt(m, "Today's Bakes", -WX + 0.008, -1.3, 2.15, 0.12, 'paper', face='x+', font='script', maxw=1.8)
    for j in range(3):
        rq(m, -WX + 0.008, -2.1, -0.8 - 0.2 * (j % 2), 1.5 + j * 0.17, 1.54 + j * 0.17, 'orangeL')
    sign_board(m, 0.6, WY1 - 0.004, 2.45, 1.5, 0.42, 'sign', 'Bakehouse', 'orangeL', font='script')
    pendant(m, 0.0, -0.6, shade='orange', drop=0.7)


def room_home(m, cols):
    """Hearth & Home: a sofa and an armchair round a coffee table on a rug, floor lamps, plants, a dresser"""
    shell(m, ('mint', 'Up'), 'planks', door_x=1.75)
    uq(m, -1.3, 1.3, -1.0, 1.0, 0.026, 'tealD')
    uq(m, -1.15, 1.15, -0.85, 0.85, 0.03, 'cream')
    # sofa against the left wall, armchair on the right
    x0 = -WX
    m.bx(x0, x0 + 0.9, -1.1, 1.1, 0.0, 0.45, 'tealM', hull='full', cull='b')
    m.bx(x0, x0 + 0.25, -1.1, 1.1, 0.45, 0.95, 'tealM', hull='full', cull='bl')
    for y in (-1.1, 0.92):
        m.bx(x0 + 0.25, x0 + 0.9, y, y + 0.18, 0.45, 0.65, 'tealM', hull='full', cull='b')
    for y in (-0.92, 0.0):
        m.bx(x0 + 0.25, x0 + 0.88, y + 0.02, y + 0.9, 0.45, 0.53, 'mintL', hull='none', cull='b')
    for y, c in ((-0.6, 'orange'), (0.5, 'gold')):
        m.bx(x0 + 0.27, x0 + 0.4, y - 0.18, y + 0.18, 0.53, 0.85, c, hull='full')
    solid(cols, x0, -1.1, 0.0, x0 + 0.9, 1.1, 0.95)
    # armchair facing the sofa (back to the right wall)
    x, y = 1.7, 0.0
    m.bx(x - 0.4, x + 0.4, y - 0.42, y + 0.42, 0.0, 0.42, 'orange', hull='full', cull='b')
    m.bx(x + 0.2, x + 0.4, y - 0.42, y + 0.42, 0.42, 0.95, 'orange', hull='full')
    for sy in (-1, 1):
        m.bx(x - 0.4, x + 0.2, min(y + sy * 0.42, y + sy * 0.3), max(y + sy * 0.42, y + sy * 0.3), 0.42, 0.62, 'orange', hull='full')
    solid(cols, x - 0.4, y - 0.42, 0.0, x + 0.4, y + 0.42, 0.95)
    # coffee table with a vase and books
    island(m, cols, -0.45, 0.45, -0.35, 0.35, 0.42, 'wood2', 'wood')
    m.cy((0.15, 0.0, 0.42), 0.07, 0.09, 0.25, 'navy', seg=8, hull='none')
    m.sp((0.15, 0.0, 0.75), 0.13, 'leafL', seg=(6, 3), hull='none')
    m.bx(-0.3, 0.0, -0.15, 0.1, 0.42, 0.47, 'redT', hull='none', cull='b')
    # floor lamps either side of the sofa, big plants in the front corners
    for y in (-1.4, 1.4):
        m.cy((-2.15, y, 0), 0.15, 0.15, 0.03, 'brass', seg=8, hull='none')
        m.cy((-2.15, y, 0.03), 0.015, 0.015, 1.5, 'brass', seg=5, hull='none')
        m.cy((-2.15, y, 1.45), 0.25, 0.15, 0.3, 'cream', seg=10)
        disc(m, -2.15, y, 1.446, 0.23, 'light', seg=10, up=False)
        solid(cols, -2.3, y - 0.15, 0.0, -2.0, y + 0.15, 1.75)
    for (px, py) in ((2.05, -2.5), (-2.05, 2.5)):
        m.cy((px, py, 0), 0.22, 0.26, 0.45, 'terra', seg=8)
        for k in range(3):
            m.sp((px + (k - 1) * 0.12, py + (k % 2) * 0.1, 0.8 + k * 0.22), 0.25, ('leaf', 'leaf2', 'leafL')[k], seg=(6, 3), hull='none')
        solid(cols, px - 0.26, py - 0.26, 0.0, px + 0.26, py + 0.26, 0.45)
    # dresser with lamps and vases on the back wall, a framed mirror over it; cash desk on the right at the back
    m.bx(-1.5, 0.2, WY1 - 0.5, WY1, 0.0, 0.85, 'woodL', hull='full', cull='b')
    for i in range(3):
        fq(m, -1.45 + i * 0.56, -0.95 + i * 0.56, WY1 - 0.503, 0.1, 0.75, 'wood')
        m.cy((-1.2 + i * 0.56, WY1 - 0.53, 0.45), 0.025, 0.025, 0.03, 'brass', seg=6, rot=(90, 0, 0), hull='none')
    for i, c in enumerate(('tealM', 'cream', 'terra')):
        m.cy((-1.3 + i * 0.5, WY1 - 0.25, 0.85), 0.06, 0.08, 0.22 + 0.06 * i, c, seg=8, hull='none')
    solid(cols, -1.5, WY1 - 0.5, 0.0, 0.2, WY1, 0.85)
    fq(m, -1.2, -0.1, WY1 - 0.004, 1.2, 2.3, 'brass')
    fq(m, -1.12, -0.18, WY1 - 0.008, 1.28, 2.22, 'skyglass')
    cash_desk(m, cols, 0.75, 1.95, 1.9, 2.45, 'tealD', top='woodL')
    sign_board(m, 1.35, WY1 - 0.004, 2.45, 1.2, 0.38, 'cream', 'Hearth & Home', 'tealD', font='serif')


def room_leather(m, cols):
    """Leatherworks: bag shelves on both walls, a centre table of bags, a leather armchair, cash desk"""
    shell(m, ('violet', 'Up'), 'planks', door_x=-1.7)
    leather = ['wood', 'redT', 'dark', 'gold', 'wood2', 'terra']
    for side in (-1, 1):
        xw = side * WX
        xi = xw - side * 0.45
        a, b = min(xw, xi), max(xw, xi)
        y0, y1 = -2.6, 1.3 if side < 0 else 0.9
        for y in (y0, y1 - 0.05):
            m.bx(a, b, y, y + 0.05, 0.0, 2.3, 'wood2', hull='full', cull='b')
        m.bx(a, b, y0 + 0.05, y1 - 0.05, 0.0, 0.3, 'wood2', hull='full', cull='b')
        (rq if side < 0 else lq)(m, xw - side * 0.006, y0, y1, 0.3, 2.3, 'sign')
        for k in range(3):
            zb = 0.3 + k * 0.68
            if k:
                m.bx(a, b, y0 + 0.05, y1 - 0.05, zb - 0.03, zb, 'wood2', hull='none', cull='b')
            n = int((y1 - y0) / 0.55)
            for i in range(n):
                y = y0 + 0.32 + i * 0.55
                c = leather[(i + k * 2 + (side > 0)) % 6]
                xs = xw - side * 0.22
                m.prism([(y - 0.17, zb), (y + 0.17, zb), (y + 0.13, zb + 0.28), (y - 0.13, zb + 0.28)], xs - 0.08, xs + 0.08, [c], hull='none')
                m.bx(xs - 0.01, xs + 0.01, y - 0.09, y + 0.09, zb + 0.38, zb + 0.41, 'dark', hull='none')
        solid(cols, a, y0, 0.0, b, y1, 2.3)
    # centre table with bags and a wallet tray
    island(m, cols, -0.6, 0.6, -0.85, 0.35, 0.8, 'wood2', 'woodL')
    for i, (x, y, c) in enumerate(((-0.3, -0.5, 'redT'), (0.25, -0.35, 'wood'), (-0.15, 0.05, 'dark'))):
        bag(m, x, y, 0.8, c, w=0.32, h=0.24)
    m.bx(0.15, 0.45, -0.05, 0.2, 0.8, 0.84, 'sign', hull='none', cull='b')
    # leather armchair and a rug at the back left, cash desk at the back right
    uq(m, -2.2, -0.4, 1.6, 2.85, 0.026, 'terraD')
    chair(m, cols, -1.3, 2.3, 'wood2', face=-1)
    cash_desk(m, cols, 0.4, 1.9, 1.85, 2.4, 'wood2', top='cream')
    txt(m, 'Est. 1984', 1.15, WY1 - 0.006, 2.3, 0.14, 'violetD', font='script', valign='m', maxw=1.2)
    sign_board(m, 1.15, WY1 - 0.004, 2.45, 1.4, 0.4, 'violetD', 'Leatherworks', 'roseL', font='script')
    pendant(m, 0.0, -0.25, shade='wood', drop=0.6)
    pendant(m, -1.3, 2.0, shade='wood', drop=0.7)


ROOMS = {
    'Room_Atelier': room_atelier, 'Room_Signal': room_signal, 'Room_Coffee': room_coffee, 'Room_Books': room_books,
    'Room_Toys': room_toys, 'Room_Aurum': room_aurum, 'Room_Shoes': room_shoes, 'Room_Optics': room_optics,
    'Room_Bakery': room_bakery, 'Room_Home': room_home, 'Room_Leather': room_leather,
}


def build_rooms(pal, ao):
    for name, fn in ROOMS.items():
        m = new(pal)
        cols = []
        fn(m, cols)
        make(name, m, ao, cols=cols)
