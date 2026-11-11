"""kit-downtown walk-in shops: one furnished 7 x 8 m room piece per shop (Shop_<Name>), placed behind a 7-cell
shopfront (tools/downtown_zones.py: two display-window cells, three doorway cells 'n', two display-window cells).

Room frame (Blender): x -3.5 .. 3.5 along the frontage, y -4 (front, toward the doorway) .. 4 (back), the band's wall
cells round the other three sides. The piece draws the floor, the walls (2 cm inside the room footprint), the
ceiling at RH with light panels, the inside of the shopfront (display windows painted on the front wall, a display bed
under each), a partition 2.4 m from the back with a 1.4 m door into the back room (stock shelves, a desk or the
kitchen, the staff exit), and the shop's fittings: shelving against the side walls (at most 0.6 m deep), one island
or a row of fittings in the middle, so two aisles of 1.4 m or more lead to the counter at the back. The front 1.8 m
stay clear (a pickup may lie at (0, -3)). Outside the footprint it draws the street side: the shop's sign board (its
made-up name in vector lettering) on the band over the doorway and a striped awning.
Collision: one box per fitting, cut to what is drawn at player height (collision-audit.spec.js).
"""
import math

from downtown_base import *  # noqa: F401,F403

WX, WY0, WY1 = 3.48, -3.98, 3.98     # inner wall faces
PY = 1.45                           # partition (front face); the back room runs PY + 0.12 .. WY1
FRONT = -5.0                        # street face of the shopfront cells


def solid(cols, x0, y0, z0, x1, y1, z1):
    cols.append(box(x0, y0, z0, x1, y1, z1))


# ---------------------------------------------------------------- shell
def shell(m, cols, floor, wall, trim, door=(-2.2, -0.8), floor2=None, pattern='tiles', back='cream'):
    """floor, walls, skirting, ceiling with light panels, the inside of the shopfront, the partition and back room"""
    uq(m, -WX, WX, -4.0, PY + 0.06, 0.012, floor)
    if pattern == 'tiles' and floor2:      # 1 m checker
        for i in range(7):
            for j in range(6):
                if (i + j) % 2:
                    uq(m, max(-WX, -3.5 + i), min(WX, -2.5 + i), -4.0 + j, min(PY, -3.0 + j), 0.016, floor2)
    elif pattern == 'small' and floor2:    # 0.5 m checker in the front room
        for i in range(14):
            for j in range(11):
                if (i + j) % 2:
                    uq(m, max(-WX, -3.5 + i * 0.5), min(WX, -3.0 + i * 0.5), -4.0 + j * 0.5, -3.5 + j * 0.5, 0.016, floor2)
    elif pattern == 'planks' and floor2:
        x = -WX + 0.35
        while x < WX - 0.1:
            uq(m, x, x + 0.02, -4.0, PY, 0.016, floor2)
            x += 0.35
    # walls: side walls, back wall, the front wall's inside round the doorway, skirting
    rq(m, -WX, -4.0, WY1, 0.0, RH, wall)
    lq(m, WX, -4.0, WY1, 0.0, RH, wall)
    fq(m, -WX, WX, WY1, 0.0, RH, back)
    for (x0, x1) in ((-WX, -1.5), (1.5, WX)):
        bq(m, x0, x1, WY0, 0.0, RH, wall)
        bq(m, x0 + 0.18, x1 - 0.18, WY0 + 0.005, 0.55, 3.1, 'mull')                 # display window from inside
        bq(m, x0 + 0.24, x1 - 0.24, WY0 + 0.01, 0.6, 3.04, 'glass')
        poly(m, [(x0 + 0.5, WY0 + 0.015, 0.9), (x0 + 0.62, WY0 + 0.015, 0.9), (x0 + 0.95, WY0 + 0.015, 2.5), (x0 + 0.83, WY0 + 0.015, 2.5)], 'glassL', (0, 1, 0))
        m.bx(x0 + 0.1, x1 - 0.1, WY0, WY0 + 0.55, 0.0, 0.5, trim, hull='full', cull='bk')  # display bed
        solid(cols, x0 + 0.1, WY0, 0.0, x1 - 0.1, WY0 + 0.55, 0.5)
    bq(m, -1.5, 1.5, WY0, DOOR_H, RH, wall)
    m.bx(-WX, -WX + 0.025, -4.0, WY1, 0.0, 0.1, trim, hull='none', cull='bfkl')
    m.bx(WX - 0.025, WX, -4.0, WY1, 0.0, 0.1, trim, hull='none', cull='bfkr')
    # ceiling: plaster, a light panel per bay
    dq(m, -WX, WX, -4.0, WY1, RH, 'cream')
    for (x, y) in ((-1.6, -2.5), (1.6, -2.5), (-1.6, -0.2), (1.6, -0.2)):
        dq(m, x - 0.6, x + 0.6, y - 0.3, y + 0.3, RH - 0.01, 'light')
    # partition with a door into the back room: wall leaves, header, frame, a STAFF plate
    d0, d1 = door
    for (a, b) in ((-WX, d0), (d1, WX)):
        if b - a > 0.05:
            m.bx(a, b, PY, PY + 0.12, 0.0, RH, wall, hull='full', cull='t')
            solid(cols, a, PY, 0.0, b, PY + 0.12, RH)
    m.bx(d0, d1, PY, PY + 0.12, 2.3, RH, wall, hull='full', cull='t')
    for (a, b, z0, z1) in ((d0 - 0.08, d0, 0.0, 2.3), (d1, d1 + 0.08, 0.0, 2.3), (d0 - 0.08, d1 + 0.08, 2.3, 2.38)):
        fq(m, a, b, PY - 0.004, z0, z1, trim)                                         # door frame
    fq(m, d0 + 0.32, d1 - 0.32, PY - 0.008, 2.5, 2.7, 'paper')                        # STAFF plate over the door
    fq(m, (d0 + d1) / 2 - 0.2, (d0 + d1) / 2 + 0.2, PY - 0.012, 2.57, 2.63, 'ink')
    # back room: bare concrete floor, a strip light, the staff exit with its sign
    uq(m, -WX, WX, PY + 0.06, WY1, 0.012, 'concF')
    dq(m, -0.7, 0.7, 2.6, 2.75, RH - 0.012, 'light')
    ex = 2.4 if d0 < 0 else -2.4
    fq(m, ex - 0.5, ex + 0.5, WY1 - 0.004, 0.0, 2.2, 'steelD')
    fq(m, ex - 0.44, ex + 0.44, WY1 - 0.008, 0.0, 2.12, 'steel')
    fq(m, ex - 0.4, ex + 0.4, WY1 - 0.012, 0.95, 1.05, 'steelD')                       # push bar
    m.bx(ex - 0.18, ex + 0.18, WY1 - 0.1, WY1, 2.3, 2.46, 'exitG', hull='none', cull='k')
    txt(m, 'EXIT', ex, WY1 - 0.104, 2.38, 0.09, 'paper', font='cond', maxw=0.3)


def street(m, name, sign, letter, awning, font='display', cap=0.5):
    """the street side: the sign board over the frontage, a striped awning with a scalloped valance"""
    m.bx(-3.3, 3.3, FRONT - 0.16, FRONT - 0.004, 3.45, 4.4, sign, hull='full', cull='k')
    txt(m, name, 0.0, FRONT - 0.164, 3.93, cap, letter, font=font, maxw=6.0)
    c1, c2 = awning
    m.prism([(FRONT - 0.17, 3.42), (FRONT - 1.4, 3.08), (FRONT - 1.4, 2.98), (FRONT - 0.17, 3.32)], -3.4, 3.4,
            [c1, c2] * 4, hull='full', skip=(3,))
    m.bx(-3.4, 3.4, FRONT - 1.412, FRONT - 1.4, 2.8, 2.985, c1, hull='none', cull='k')
    for k in range(8):
        x = -3.4 + k * 0.85
        poly(m, [(x, FRONT - 1.415, 2.8), (x + 0.85, FRONT - 1.415, 2.8), (x + 0.425, FRONT - 1.415, 2.68)], c1 if k % 2 else c2, (0, -1, 0))


def wall_shelf(m, cols, side, y0, y1, h, colors, frame='woodD', depth=0.45, n=4, step=0.21, back='cream', hull='full'):
    """shelving against a side wall (side -1 = left / -X, +1 = right): carcass, boards, stock faces toward the room"""
    xw = side * WX
    xi = xw - side * depth
    a, b = min(xw, xi), max(xw, xi)
    for y in (y0, y1 - 0.04):
        m.bx(a, b, y, y + 0.04, 0.0, h, frame, hull=hull, cull='b')
    m.bx(a, b, y0 + 0.04, y1 - 0.04, h - 0.05, h, frame, hull=hull, cull='')
    m.bx(a, b, y0 + 0.04, y1 - 0.04, 0.0, 0.12, frame, hull='none', cull='b')
    (rq if side < 0 else lq)(m, xw - side * 0.012, y0 + 0.04, y1 - 0.04, 0.12, h - 0.05, back)
    for k in range(n):
        zb = 0.12 + (k + 1) * (h - 0.2) / (n + 0.3)
        if k < n - 1 or True:
            m.bx(a, b, y0 + 0.04, y1 - 0.04, zb - 0.03, zb, frame, hull='none', cull='b')
        zp = 0.12 + k * (h - 0.2) / (n + 0.3)
        y = y0 + 0.07
        i = 0
        while y < y1 - 0.12:
            w = step * (0.7 + 0.5 * ((i * 7 + k * 3) % 5) / 4)
            hh = (h - 0.2) / (n + 0.3) * (0.55 + 0.3 * ((i * 3 + k) % 3) / 2)
            xs = xw - side * (depth - 0.05)
            (rq if side < 0 else lq)(m, xs, y, min(y + w - 0.015, y1 - 0.07), zp + 0.004, zp + hh, colors[(i + k) % len(colors)])
            y += w
            i += 1
    solid(cols, a, y0, 0.0, b, y1, h)


def gondola(m, cols, x0, x1, y0, y1, h, colors, frame='steel', end=None, n=3):
    """a double-sided shelf island (aisle shelving): stock faces on both long sides, an end cap card"""
    m.bx(x0, x1, y0, y1, 0.0, 0.12, frame, hull='full', cull='b')
    m.bx(x0 + 0.33 * (x1 - x0), x1 - 0.33 * (x1 - x0), y0 + 0.02, y1 - 0.02, 0.12, h, frame, hull='full', cull='b')
    for side in (-1, 1):
        xs = x0 + 0.04 if side < 0 else x1 - 0.04
        for k in range(n):
            zb = 0.12 + (k + 1) * (h - 0.2) / (n + 0.2)
            zp = 0.12 + k * (h - 0.2) / (n + 0.2)
            a, b = sorted((xs, x0 + 0.33 * (x1 - x0) if side < 0 else x1 - 0.33 * (x1 - x0)))
            m.bx(a, b, y0, y1, zb - 0.025, zb, frame, hull='none', cull='b')
            y = y0 + 0.05
            i = 0
            while y < y1 - 0.1:
                w = 0.22 * (0.7 + 0.5 * ((i * 5 + k * 3 + (side > 0)) % 5) / 4)
                hh = (h - 0.2) / (n + 0.2) * (0.55 + 0.3 * ((i + k) % 3) / 2)
                (lq if side < 0 else rq)(m, xs + (0.0 if side < 0 else 0.0), y, min(y + w - 0.015, y1 - 0.05), zp + 0.004, zp + hh, colors[(i * 2 + k + (side > 0)) % len(colors)])
                y += w
                i += 1
    if end:
        fq(m, x0 + 0.05, x1 - 0.05, y0 - 0.004, h - 0.4, h - 0.08, end)
    solid(cols, x0, y0, 0.0, x1, y1, h)


def counter(m, cols, x0, x1, y0, y1, body, top, h=1.0, till=True, front='y-'):
    m.bx(x0, x1, y0, y1, 0.0, h - 0.05, body, hull='full', cull='b')
    m.bx(x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, h - 0.05, h, top, hull='full')
    if till:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        m.bx(cx - 0.2, cx + 0.2, cy - 0.12, cy + 0.12, h, h + 0.1, 'steelD', hull='full', cull='b')
        m.bx(cx - 0.17, cx + 0.17, cy + 0.06, cy + 0.1, h + 0.1, h + 0.36, 'steelD', hull='none', cull='b')
        fq(m, cx - 0.14, cx + 0.14, cy + 0.056, h + 0.13, h + 0.33, 'glass')
    solid(cols, x0 - 0.04, y0 - 0.04, 0.0, x1 + 0.04, y1 + 0.04, h)


def stock(m, cols, x0, x1, y0, y1, h=1.0, rows=2, cols_=2, c=('cardb', 'cardb', 'wood')):
    """stacked cartons in the back room"""
    w, d = (x1 - x0) / cols_, (y1 - y0) / rows
    for i in range(cols_):
        for j in range(rows):
            hh = h * (0.6 + 0.4 * ((i + j * 2) % 3) / 2)
            m.bx(x0 + i * w + 0.02, x0 + (i + 1) * w - 0.02, y0 + j * d + 0.02, y0 + (j + 1) * d - 0.02, 0.0, hh, c[(i + j) % len(c)], hull='none', cull='b')
            uq(m, x0 + i * w + w * 0.45, x0 + i * w + w * 0.55, y0 + j * d + 0.02, y0 + (j + 1) * d - 0.02, hh + 0.003, 'pYellow' if (i + j) % 2 else 'tarp')
    solid(cols, x0, y0, 0.0, x1, y1, h)


def rack(m, cols, side, y0, y1, h=2.2, c='steel', depth=0.6, n=3, colors=('cardb', 'wood', 'cardb', 'pWhite')):
    """steel stock racking against a side wall in the back room, cartons on its decks"""
    xw = side * WX
    a, b = sorted((xw, xw - side * depth))
    for y in (y0, y1 - 0.05):
        for x in (a, b - 0.05):
            m.bx(x, x + 0.05, y, y + 0.05, 0.0, h, c, hull='none', cull='b')
    for k in range(n):
        z = 0.15 + k * (h - 0.2) / (n - 0.5)
        m.bx(a + 0.004, b - 0.004, y0 + 0.05, y1 - 0.05, z, z + 0.04, 'steelD', hull='none')
        yy = y0 + 0.08
        i = 0
        while yy < y1 - 0.4:
            m.bx(a + 0.05, b - 0.05, yy, yy + 0.36, z + 0.04, z + 0.3 + 0.08 * ((i + k) % 2), colors[(i + k) % len(colors)], hull='none', cull='b')
            yy += 0.42
            i += 1
    solid(cols, a, y0, 0.0, b, y1, h)


def chair(m, cols, x, y, c, face=1, seat='seat'):
    """simple chair (0.45 x 0.45), back toward -face * Y"""
    for (dx, dy) in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
        m.bx(x + dx - 0.02, x + dx + 0.02, y + dy - 0.02, y + dy + 0.02, 0.0, 0.45, 'steelD', hull='none', cull='b')
    m.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0.45, 0.5, c, hull='none')
    yb = y - face * 0.2
    m.bx(x - 0.22, x + 0.22, min(yb - 0.03, yb + 0.03), max(yb - 0.03, yb + 0.03), 0.5, 0.92, c, hull='none')
    solid(cols, x - 0.22, y - 0.22, 0.0, x + 0.22, y + 0.22, 0.92)


def table(m, cols, x0, x1, y0, y1, h=0.75, top='wood', leg='steelD'):
    for x in (x0 + 0.05, x1 - 0.09):
        for y in (y0 + 0.05, y1 - 0.09):
            m.bx(x, x + 0.04, y, y + 0.04, 0.0, h - 0.04, leg, hull='none', cull='b')
    m.bx(x0, x1, y0, y1, h - 0.04, h, top, hull='full')
    solid(cols, x0, y0, h - 0.3, x1, y1, h)   # a table top: shoot under it, robots and the player go round the legs
    for x in (x0 + 0.05, x1 - 0.09):
        for y in (y0 + 0.05, y1 - 0.09):
            solid(cols, x, y, 0.0, x + 0.04, y + 0.04, h - 0.3)


def poster(m, x, y, z, w, h, c, word, lc, face='y-', font='display'):
    if face == 'y-':
        fq(m, x - w / 2, x + w / 2, y, z, z + h, c)
        txt(m, word, x, y - 0.004, z + h / 2, h * 0.4, lc, font=font, maxw=w * 0.86)
    elif face == 'x+':
        rq(m, x, y - w / 2, y + w / 2, z, z + h, c)
        txt(m, word, x + 0.004, y, z + h / 2, h * 0.4, lc, face='x+', font=font, maxw=w * 0.86)
    else:
        lq(m, x, y - w / 2, y + w / 2, z, z + h, c)
        txt(m, word, x - 0.004, y, z + h / 2, h * 0.4, lc, face='x-', font=font, maxw=w * 0.86)


def bed_items(m, x0, x1, colors, kind='box'):
    """goods on a display bed (front wall, x0..x1): boxes / bottles / cans in a row"""
    n = int((x1 - x0 - 0.3) / 0.32)
    for i in range(n):
        x = x0 + 0.2 + i * 0.32
        c = colors[i % len(colors)]
        y = WY0 + 0.27
        if kind == 'box':
            m.bx(x, x + 0.22, y - 0.1, y + 0.1, 0.5, 0.5 + 0.2 + 0.12 * (i % 3), c, hull='none', cull='b')
        else:   # bottles: slim boxes with a cap
            m.bx(x + 0.03, x + 0.17, y - 0.07, y + 0.07, 0.5, 0.74 + 0.06 * (i % 2), c, hull='none', cull='b')
            m.bx(x + 0.07, x + 0.13, y - 0.03, y + 0.03, 0.74 + 0.06 * (i % 2), 0.8 + 0.06 * (i % 2), 'pWhite', hull='none', cull='b')


# ---------------------------------------------------------------- the shops
def shop_pharmacy(m, cols):
    """Hollis Pharmacy: shelving both walls, a double-sided gondola, the prescription counter in front of the
    dispensary (back room: pill shelves, a fridge, a desk)"""
    shell(m, cols, 'tileW', 'pWhite', 'pTeal', door=(-2.6, -1.2), floor2='glassL', pattern='tiles')
    street(m, 'HOLLIS PHARMACY', 'exitG', 'pWhite', ('exitG', 'pWhite'), cap=0.56)
    # green cross on the sign's left
    for k, (a, b, c, d) in enumerate(((-3.18, -2.62, 3.82, 4.0), (-2.99, -2.81, 3.63, 4.19))):
        fq(m, a, b, FRONT - 0.17 - 0.004 * k, c, d, 'pWhite')
    meds = ('pWhite', 'pBlue', 'pipeR', 'exitG', 'pTeal', 'lineY', 'pink', 'cream')
    wall_shelf(m, cols, -1, -2.2, 1.3, 2.0, meds, frame='pWhite', back='glassL')
    wall_shelf(m, cols, 1, -2.2, 0.0, 2.0, meds, frame='pWhite', back='glassL')
    gondola(m, cols, -0.5, 0.5, -2.0, -0.2, 1.45, meds, frame='pWhite', end='pTeal')
    # prescription counter: two-tone, a pick-up sign over it, a blood pressure booth beside it
    counter(m, cols, 0.4, 3.0, 0.75, 1.3, 'pTeal', 'pWhite')
    poster(m, 1.7, PY - 0.012, 2.45, 2.2, 0.5, 'exitG', 'PRESCRIPTIONS', 'pWhite', font='cond')
    m.bx(-0.05, 0.25, 0.85, 1.2, 1.0, 1.32, 'pWhite', hull='none', cull='b')              # bag of meds
    m.bx(2.75, WX, 0.2, 0.7, 0.0, 1.7, 'pWhite', hull='full', cull='b')                   # BP kiosk
    lq(m, 2.745, 0.28, 0.62, 1.0, 1.4, 'glass')
    solid(cols, 2.75, 0.2, 0.0, WX, 0.7, 1.7)
    bed_items(m, -3.38, -1.6, ('pink', 'pBlue', 'lineY', 'pWhite'))
    bed_items(m, 1.6, 3.38, ('exitG', 'pWhite', 'pipeR'), kind='bottle')
    # dispensary (back room)
    rack(m, cols, 1, 1.75, 3.9, h=2.2, c='pWhite', colors=('pWhite', 'pBlue', 'cream', 'pTeal'))
    m.bx(-WX, -2.7, 3.2, WY1, 0.0, 1.9, 'pWhite', hull='full', cull='b')                   # fridge
    fq(m, -3.4, -2.78, 3.196, 0.1, 1.8, 'glassL')
    solid(cols, -WX, 3.2, 0.0, -2.7, WY1, 1.9)
    table(m, cols, -2.3, -0.9, 3.3, WY1, h=0.78, top='pWhite')
    m.bx(-1.9, -1.4, 3.55, 3.75, 0.78, 1.15, 'steelD', hull='none', cull='b')
    fq(m, -1.86, -1.44, 3.546, 0.84, 1.1, 'glass')


def shop_diner(m, cols):
    """Lula's Diner: red vinyl booths down the left wall, a counter with stools on the right, pie case and coffee on
    the back bar; the kitchen (grill, fryer, steel table, hood) behind a pass-through"""
    shell(m, cols, 'pWhite', 'cream', 'pipeR', door=(0.9, 2.3), floor2='pipeR', pattern='small', back='cream')
    street(m, "Lula's Diner", 'pipeR', 'pWhite', ('pipeR', 'pWhite'), font='script', cap=0.62)
    # booths: table + two benches, three along the left wall
    for i in range(3):
        y = -1.95 + i * 1.15
        for (a, b) in ((y - 0.53, y - 0.25), (y + 0.25, y + 0.53)):
            m.bx(-WX, -1.9, a, b, 0.0, 0.45, 'pipeR', hull='full', cull='b')
        m.bx(-WX, -1.9, y - 0.6, y - 0.54, 0.0, 1.1, 'pipeR', hull='full', cull='b')
        m.bx(-WX + 0.05, -2.05, y - 0.22, y + 0.22, 0.72, 0.76, 'pWhite', hull='full')
        m.bx(-2.55, -2.47, y - 0.05, y + 0.05, 0.0, 0.72, 'chrome', hull='none', cull='b')
        m.cy((-2.9, y, 0.76), 0.05, 0.04, 0.12, 'lineY', seg=6, hull='none')                   # mustard
        m.cy((-2.75, y + 0.05, 0.76), 0.05, 0.04, 0.12, 'pipeR', seg=6, hull='none')
        solid(cols, -WX, y - 0.6, 0.0, -1.9, y + 0.53, 0.76)
    m.bx(-WX, -1.9, 0.9, 1.0, 0.0, 1.1, 'pipeR', hull='full', cull='b')
    solid(cols, -WX, 0.9, 0.0, -1.9, 1.0, 1.1)
    # counter with five stools, the back bar behind it
    counter(m, cols, 1.55, 2.2, -2.1, 1.2, 'chrome', 'pipeR', h=1.05, till=False)
    fq(m, 1.5, 1.52, -2.1, 0.1, 0.9, 'pipeR')
    lq(m, 1.505, -2.05, 1.15, 0.12, 0.9, 'pipeR')
    for k in range(5):
        y = -1.8 + k * 0.7
        m.cy((1.05, y, 0.0), 0.04, 0.04, 0.7, 'chrome', seg=6, hull='none')
        m.cy((1.05, y, 0.7), 0.2, 0.2, 0.08, 'pipeR', seg=8, hull='none')
        solid(cols, 0.85, y - 0.2, 0.0, 1.25, y + 0.2, 0.78)
    m.cy((1.85, -1.4, 1.05), 0.2, 0.22, 0.3, 'glassL', seg=8, hull='full')                  # cake stand
    m.cy((1.85, -1.4, 1.15), 0.15, 0.15, 0.08, 'pink', seg=8, hull='none')
    m.bx(2.75, WX, -2.1, 1.2, 0.0, 0.95, 'steel', hull='full', cull='b')                   # back bar
    solid(cols, 2.75, -2.1, 0.0, WX, 1.2, 0.95)
    for y in (-1.6, -0.9):                                                                   # coffee machine, pots
        m.bx(2.95, WX - 0.05, y - 0.25, y + 0.25, 0.95, 1.55, 'steelD', hull='full', cull='b')
        m.cy((2.95, y, 0.98), 0.09, 0.08, 0.18, 'woodD', seg=6, hull='none')
    m.bx(2.9, WX - 0.05, -0.3, 1.1, 0.95, 1.5, 'chrome', hull='full', cull='b')           # pie case
    for k in range(3):
        lq(m, 2.896, -0.2 + k * 0.42, 0.1 + k * 0.42, 1.05, 1.18, ('pink', 'cardb', 'lineY')[k])
    poster(m, -WX + 0.004, -0.3, 2.3, 2.6, 0.55, 'pipeR', 'PIE & COFFEE', 'pWhite', face='x+', font='cond')
    m.bx(-2.7, -1.9, PY - 0.42, PY, 0.0, 1.6, 'pink', hull='full', cull='b')               # jukebox
    m.cy((-2.3, PY - 0.4, 1.6), 0.38, 0.38, 0.37, 'pink', seg=8, rot=(-90, 0, 0), hull='none')
    fq(m, -2.6, -2.0, PY - 0.424, 0.7, 1.45, 'lineY')
    solid(cols, -2.7, PY - 0.42, 0.0, -1.9, PY, 1.6)
    # pass-through in the partition with an order rail
    fq(m, -1.0, 0.6, PY - 0.006, 1.3, 1.9, 'interior')
    m.bx(-1.0, 0.6, PY - 0.25, PY, 1.25, 1.3, 'chrome', hull='full')
    for k in range(4):
        fq(m, -0.85 + k * 0.38, -0.6 + k * 0.38, PY - 0.012, 1.95, 2.18, 'paper')
    # kitchen: grill line under a hood along the back, a steel prep table, a fryer
    m.bx(-WX, 0.4, 3.25, WY1, 0.0, 0.92, 'steel', hull='full', cull='b')
    uq(m, -3.2, -1.6, 3.35, 3.85, 0.925, 'ink')
    uq(m, -1.4, -0.4, 3.35, 3.85, 0.925, 'litA')
    m.bx(-WX, 0.4, 3.3, WY1, 2.4, 2.9, 'galv', hull='full')
    solid(cols, -WX, 3.25, 0.0, 0.4, WY1, 0.92)
    table(m, cols, -2.6, -0.6, 1.95, 2.6, h=0.9, top='galv', leg='steel')


def shop_electronics(m, cols):
    """Voltaic Electronics: a TV wall, an accessory pegboard, a laptop table, the service counter; stock and a repair
    bench in the back"""
    shell(m, cols, 'concF', 'pWhite', 'signB', door=(1.6, 3.0), floor2='steel', pattern='tiles', back='pWhite')
    street(m, 'VOLTAIC', 'navy', 'glassL', ('signB', 'pWhite'), cap=0.62)
    # TV wall on the right: screens in three colours over a media unit
    lq(m, WX - 0.006, -2.3, 1.2, 0.95, 2.95, 'ink')
    for i in range(3):
        for k in range(2):
            y, z = -2.2 + i * 1.15, 1.05 + k * 0.95
            m.bx(WX - 0.08, WX - 0.006, y, y + 1.02, z, z + 0.8, 'steelD', hull='none', cull='r')
            lq(m, WX - 0.083, y + 0.04, y + 0.98, z + 0.04, z + 0.76, ('glass', 'signB', 'pTeal', 'glassL', 'violet', 'glass')[i * 2 + k])
            lq(m, WX - 0.086, y + 0.1, y + 0.4, z + 0.45, z + 0.66, 'glassL')
    m.bx(WX - 0.45, WX, -2.3, 1.2, 0.0, 0.6, 'pWhite', hull='full', cull='b')
    solid(cols, WX - 0.45, -2.3, 0.0, WX, 1.2, 0.6)
    # pegboard on the left: headphones, cases, cables
    rq(m, -WX + 0.006, -2.3, 1.2, 0.8, 2.5, 'cream')
    for i in range(6):
        for k in range(3):
            y, z = -2.15 + i * 0.56, 1.0 + k * 0.5
            m.bx(-WX + 0.006, -WX + 0.06, y, y + 0.3, z, z + 0.36, ('signB', 'pipeR', 'ink', 'pTeal', 'lineY', 'exitG')[(i + k) % 6], hull='none', cull='l')
    m.bx(-WX, -WX + 0.5, -2.3, 1.2, 0.0, 0.85, 'glassL', hull='full', cull='b')
    m.bx(-WX, -WX + 0.53, -2.33, 1.23, 0.85, 0.9, 'pWhite', hull='full')
    solid(cols, -WX, -2.33, 0.0, -WX + 0.53, 1.23, 0.9)
    # laptop table in the middle
    m.bx(-0.7, 0.7, -1.9, -0.1, 0.0, 0.86, 'pWhite', hull='full', cull='b')
    m.bx(-0.74, 0.74, -1.94, -0.06, 0.86, 0.9, 'steel', hull='full')
    fq(m, -0.66, 0.66, -1.944, 0.15, 0.75, 'signB')
    for i in range(3):
        for sx in (-1, 1):
            y = -1.7 + i * 0.55
            uq(m, sx * 0.35 - 0.2, sx * 0.35 + 0.2, y, y + 0.28, 0.904, 'steelD')
            m.prism([(y + 0.28, 0.904), (y + 0.3, 0.904), (y + 0.36, 1.15), (y + 0.34, 1.15)], sx * 0.35 - 0.2, sx * 0.35 + 0.2, ['steelD'], hull='none')
            poly(m, [(sx * 0.35 - 0.18, y + 0.28, 0.93), (sx * 0.35 + 0.18, y + 0.28, 0.93), (sx * 0.35 + 0.18, y + 0.33, 1.13), (sx * 0.35 - 0.18, y + 0.33, 1.13)], ('glass', 'pTeal', 'violet')[i], (0, -0.97, 0.24))
    solid(cols, -0.74, -1.94, 0.0, 0.74, -0.06, 0.9)
    # service counter at the back left, a lit sign over it
    counter(m, cols, -2.6, 0.4, 0.75, 1.3, 'navy', 'pWhite')
    poster(m, -1.1, PY - 0.012, 2.4, 2.4, 0.55, 'signB', 'SERVICE DESK', 'pWhite', font='cond')
    bed_items(m, -3.38, -1.6, ('ink', 'signB', 'steelD', 'pWhite'))
    bed_items(m, 1.6, 3.38, ('violet', 'ink', 'pTeal'))
    # back room: TV boxes, a repair bench with a radio in pieces
    stock(m, cols, -WX, -1.5, 2.2, WY1, h=1.4, rows=2, cols_=3)
    table(m, cols, 0.2, 2.0, 3.2, WY1, h=0.9, top='woodD')
    m.bx(0.5, 1.1, 3.45, 3.85, 0.9, 1.2, 'steelD', hull='none', cull='b')
    m.cy((1.5, 3.6, 0.9), 0.05, 0.05, 0.25, 'pipeR', seg=6, hull='none')


def shop_mart(m, cols):
    """Corner Mart 24: drink coolers down the right wall, two snack aisles, a checkout with a lottery screen and the
    cigarette rack by the window; ice machine and stock in the back"""
    shell(m, cols, 'tileW', 'cream', 'pipeR', door=(-0.7, 0.7), floor2='walk', pattern='tiles')
    street(m, 'CORNER MART 24', 'pipeR', 'pWhite', ('lineY', 'pipeR'), cap=0.6)
    # coolers: steel cabinets with glass doors, rows of drinks behind
    m.bx(WX - 0.75, WX, -2.2, 1.3, 0.0, 2.3, 'steel', hull='full', cull='b')
    for k in range(5):
        y = -2.1 + k * 0.68
        lq(m, WX - 0.754, y, y + 0.6, 0.15, 2.15, 'steelD')
        for j in range(5):
            z = 0.3 + j * 0.37
            for q in range(4):
                lq(m, WX - 0.758, y + 0.05 + q * 0.13, y + 0.15 + q * 0.13, z, z + 0.26, ('pipeR', 'exitG', 'pBlue', 'lineY', 'cone', 'pWhite')[(j + q + k) % 6])
        lq(m, WX - 0.762, y + 0.08, y + 0.14, 0.4, 2.0, 'glassL')
    solid(cols, WX - 0.75, -2.2, 0.0, WX, 1.3, 2.3)
    snacks = ('lineY', 'pipeR', 'cone', 'pBlue', 'exitG', 'violet', 'pink', 'cardb')
    gondola(m, cols, -1.65, -0.85, -1.9, 0.9, 1.5, snacks, frame='pWhite', end='lineY')
    gondola(m, cols, 0.55, 1.35, -1.9, 0.9, 1.5, snacks[::-1], frame='pWhite', end='pBlue')
    # checkout at the left of the front room: counter, till, gum rack, the cigarette and lottery wall behind
    counter(m, cols, -WX + 0.6, -2.4, -2.1, -0.9, 'pipeR', 'pWhite', h=1.0)
    for k in range(3):
        m.bx(-2.355, -2.29, -2.0 + k * 0.32, -1.76 + k * 0.32, 0.25, 0.9, ('lineY', 'pink', 'exitG')[k], hull='none', cull='b')
    m.bx(-WX, -WX + 0.3, -2.3, 0.4, 1.2, 2.4, 'woodD', hull='full', cull='b')
    for k in range(4):
        rq(m, -WX + 0.304, -2.2, 0.3, 1.3 + k * 0.27, 1.5 + k * 0.27, ('pWhite', 'pipeR', 'lineY', 'pBlue')[k])
    solid(cols, -WX, -2.3, 1.2, -WX + 0.3, 0.4, 2.4)
    m.bx(-WX, -WX + 0.4, 0.5, 1.3, 0.0, 1.0, 'pBlue', hull='full', cull='b')               # ice chest
    rq(m, -WX + 0.404, 0.6, 1.2, 0.4, 0.8, 'pWhite')
    solid(cols, -WX, 0.5, 0.0, -WX + 0.4, 1.3, 1.0)
    poster(m, 1.9, PY - 0.012, 2.4, 1.8, 0.6, 'lineY', 'HOT COFFEE', 'pipeR', font='display')
    bed_items(m, -3.38, -1.6, ('lineY', 'pipeR', 'pBlue'), kind='bottle')
    bed_items(m, 1.6, 3.38, ('cone', 'exitG', 'lineY', 'pink'))
    # back room: ice machine, stock, a mop bucket
    m.bx(-WX, -2.2, 3.1, WY1, 0.0, 1.7, 'galv', hull='full', cull='b')
    fq(m, -3.3, -2.4, 3.096, 0.9, 1.5, 'steelD')
    solid(cols, -WX, 3.1, 0.0, -2.2, WY1, 1.7)
    stock(m, cols, 1.0, WX, 2.6, WY1, h=1.2, rows=2, cols_=3, c=('cardb', 'cardb', 'pBlue'))
    m.cy((-1.4, 3.6, 0.0), 0.2, 0.2, 0.32, 'lineY', seg=8)
    m.bm_((-1.4, 3.6, 0.3), (-1.2, 3.7, 1.25), 0.03, 'woodD')
    solid(cols, -1.6, 3.4, 0.0, -1.2, 3.8, 0.32)


def shop_books(m, cols):
    """Inkwell Books: tall bookcases on both walls, a new-titles table, a reading chair, the till at the back; boxes of
    stock and a desk in the back room"""
    shell(m, cols, 'wood', 'cream', 'woodD', door=(-2.6, -1.2), floor2='woodD', pattern='planks', back='cream')
    street(m, 'Inkwell Books', 'navy', 'cream', ('navy', 'cream'), font='serif', cap=0.56)
    spines = ('pipeR', 'navy', 'exitG', 'cream', 'woodD', 'lineY', 'pTeal', 'violet', 'brickT')
    wall_shelf(m, cols, -1, -2.3, 1.3, 2.6, spines, frame='woodD', depth=0.4, n=5, step=0.14, back='trunk')
    wall_shelf(m, cols, 1, -2.3, 1.3, 2.6, spines[::-1], frame='woodD', depth=0.4, n=5, step=0.14, back='trunk')
    # new-titles table with stacks and a card
    table(m, cols, -0.75, 0.75, -1.9, -0.9, h=0.8, top='woodD', leg='woodD')
    for i, (x, y, c) in enumerate(((-0.45, -1.6, 'pipeR'), (-0.05, -1.65, 'navy'), (0.35, -1.55, 'exitG'), (-0.3, -1.15, 'lineY'), (0.25, -1.15, 'violet'))):
        m.bx(x - 0.12, x + 0.12, y - 0.16, y + 0.16, 0.8, 0.86 + 0.05 * (i % 3), c, hull='none', cull='b')
    m.prism([(-1.35, 0.8), (-1.25, 0.8), (-1.3, 1.02)], -0.15, 0.15, ['paper'], hull='none')
    # reading chair and a lamp
    m.bx(-0.6, 0.2, 0.2, 0.95, 0.0, 0.45, 'pipeR', hull='full', cull='b')
    m.bx(-0.6, 0.2, 0.8, 1.0, 0.45, 1.05, 'pipeR', hull='full')
    solid(cols, -0.6, 0.2, 0.0, 0.2, 1.0, 1.05)
    m.cy((0.55, 0.9, 0.0), 0.02, 0.02, 1.5, 'bronze', seg=5, hull='none')
    m.cy((0.55, 0.9, 1.4), 0.2, 0.1, 0.22, 'cream', seg=8, hull='full')
    # till desk at the back right, a bust on it
    counter(m, cols, 0.9, 2.6, 0.75, 1.3, 'woodD', 'wood')
    poster(m, 1.75, PY - 0.012, 2.35, 2.0, 0.5, 'navy', 'BOOKS', 'cream', font='display')
    bed_items(m, -3.38, -1.6, ('navy', 'pipeR', 'exitG', 'lineY'))
    bed_items(m, 1.6, 3.38, ('violet', 'cream', 'pTeal'))
    # back room: boxes of books, an old desk with a lamp
    stock(m, cols, 0.6, WX, 2.3, WY1, h=1.3, rows=2, cols_=3)
    table(m, cols, -WX + 0.1, -1.6, 3.3, WY1, h=0.78, top='woodD', leg='woodD')
    m.cy((-2.2, 3.65, 0.78), 0.08, 0.1, 0.4, 'exitG', seg=6, hull='none')


def shop_barber(m, cols):
    """Sal's Barber Shop: three chairs before a mirror counter on the right wall, waiting seats and a magazine rack on
    the left, the till at the back, a striped pole outside; towels and a washer in the back"""
    shell(m, cols, 'pWhite', 'tileW', 'ink', door=(1.6, 3.0), floor2='ink', pattern='small', back='tileW')
    street(m, "SAL'S BARBER SHOP", 'navy', 'pWhite', ('pipeR', 'pWhite'), font='display', cap=0.6)
    for x in (-1.7, 1.7):   # barber poles beside the doorway
        m.cy((x, FRONT - 0.22, 1.7), 0.09, 0.09, 1.1, 'pWhite', seg=8)
        for k in range(3):
            m.cy((x, FRONT - 0.22, 1.86 + k * 0.32), 0.093, 0.093, 0.1, 'pipeR' if k % 2 else 'pBlue', seg=8, hull='none', caps=False)
        m.cy((x, FRONT - 0.22, 2.8), 0.1, 0.06, 0.1, 'chrome', seg=8)
        m.bx(x - 0.04, x + 0.04, FRONT - 0.16, FRONT - 0.004, 2.33, 2.43, 'chrome', hull='none')
    # mirror counter on the right wall and three chairs facing it
    m.bx(WX - 0.5, WX, -2.3, 1.2, 0.0, 0.9, 'woodD', hull='full', cull='b')
    m.bx(WX - 0.53, WX, -2.33, 1.23, 0.9, 0.95, 'pWhite', hull='full')
    solid(cols, WX - 0.53, -2.33, 0.0, WX, 1.23, 0.95)
    lq(m, WX - 0.006, -2.2, 1.1, 1.15, 2.6, 'chrome')
    lq(m, WX - 0.01, -2.1, 1.0, 1.22, 2.53, 'glassL')
    for k in range(3):
        y = -1.75 + k * 1.15
        m.cy((WX - 0.4, y, 0.95), 0.06, 0.06, 0.25, 'tarp', seg=6, hull='none')      # jar of comb disinfectant
        m.cy((1.75, y, 0.0), 0.25, 0.3, 0.1, 'chrome', seg=8, hull='none')
        m.cy((1.75, y, 0.1), 0.06, 0.06, 0.35, 'chrome', seg=6, hull='none')
        m.bx(1.45, 2.05, y - 0.3, y + 0.3, 0.45, 0.65, 'pipeR', hull='full')
        m.bx(1.35, 1.48, y - 0.27, y + 0.27, 0.6, 1.35, 'pipeR', hull='none')
        for sy in (-1, 1):
            m.bx(1.5, 2.0, y + sy * 0.3 - 0.04, y + sy * 0.3 + 0.04, 0.65, 0.8, 'chrome', hull='none')
        m.bx(2.05, 2.3, y - 0.2, y + 0.2, 0.2, 0.26, 'chrome', hull='none')
        solid(cols, 1.35, y - 0.34, 0.0, 2.3, y + 0.34, 1.35)
    # waiting seats against the left wall, a coat stand, a magazine rack
    m.bx(-WX, -WX + 0.55, -2.2, 0.2, 0.0, 0.45, 'ink', hull='full', cull='b')
    m.bx(-WX + 0.05, -WX + 0.5, -2.15, 0.15, 0.45, 0.52, 'pipeR', hull='full')
    m.bx(-WX, -WX + 0.1, -2.15, 0.15, 0.52, 1.05, 'pipeR', hull='full')
    solid(cols, -WX, -2.2, 0.0, -WX + 0.55, 0.2, 1.05)
    m.bx(-WX, -WX + 0.25, 0.4, 1.2, 0.0, 1.2, 'woodD', hull='full', cull='b')
    for k in range(3):
        rq(m, -WX + 0.254, 0.5, 1.1, 0.35 + k * 0.3, 0.6 + k * 0.3, ('pink', 'lineY', 'pBlue')[k])
    solid(cols, -WX, 0.4, 0.0, -WX + 0.25, 1.2, 1.2)
    poster(m, -WX + 0.004, -1.0, 1.6, 1.6, 0.9, 'cream', 'CUTS  12', 'navy', face='x+', font='display')
    counter(m, cols, -2.4, -0.6, 0.75, 1.3, 'navy', 'pWhite')
    bed_items(m, -3.38, -1.6, ('tarp', 'chrome', 'woodD'), kind='bottle')
    bed_items(m, 1.6, 3.38, ('pBlue', 'pWhite', 'pipeR'), kind='bottle')
    # back room: washer, towel shelves, supplies
    m.bx(-WX, -2.6, 3.1, WY1, 0.0, 0.95, 'pWhite', hull='full', cull='b')
    m.cy((-3.05, 3.098, 0.45), 0.26, 0.26, 0.004, 'glass', seg=10, rot=(90, 0, 0), hull='none')
    solid(cols, -WX, 3.1, 0.0, -2.6, WY1, 0.95)
    rack(m, cols, -1, 1.75, 2.95, h=1.9, c='pWhite', colors=('pWhite', 'pipeR', 'pWhite', 'pBlue'))
    stock(m, cols, -0.4, 1.0, 3.2, WY1, h=0.9, rows=1, cols_=2)


def shop_sports(m, cols):
    """Fieldhouse Sports: court-lined floor, a jersey rail and a shoe wall, ball bins and a weight bench in the
    middle, the till at the back; bikes and boxes in the stock room"""
    shell(m, cols, 'wood', 'pWhite', 'exitG', door=(-0.7, 0.7), floor2='woodD', pattern='planks')
    for k, (x0, x1, y0, y1) in enumerate(((-2.5, 2.5, -1.2, -1.12), (-0.04, 0.04, -3.0, 1.2))):
        uq(m, x0, x1, y0, y1, 0.02 + 0.004 * k, 'pWhite')
    street(m, 'FIELDHOUSE', 'exitG', 'pWhite', ('exitG', 'pWhite'), cap=0.62)
    # jersey rail along the left wall
    x = -WX + 0.3
    m.bx(x - 0.015, x + 0.015, -2.2, 1.2, 1.7, 1.74, 'chrome', hull='none')
    for y in (-2.2, 1.2):
        m.cy((x, y, 0.0), 0.02, 0.02, 1.7, 'chrome', seg=5, hull='none')
    y = -2.1
    i = 0
    while y < 1.05:
        c = ('pipeR', 'pBlue', 'lineY', 'exitG', 'pWhite', 'navy')[i % 6]
        m.bx(x - 0.24, x + 0.24, y, y + 0.08, 0.9, 1.66, c, hull='none', cull='b')
        y += 0.19
        i += 1
    solid(cols, x - 0.25, -2.2, 0.0, x + 0.25, 1.2, 1.74)
    poster(m, -WX + 0.004, -0.5, 2.2, 2.0, 0.7, 'navy', 'GO TEAM', 'lineY', face='x+', font='display')
    # shoe wall on the right: angled shelves of trainers
    lq(m, WX - 0.004, -2.2, 1.2, 0.5, 2.6, 'cream')
    for k in range(5):
        z = 0.6 + k * 0.4
        m.bx(WX - 0.35, WX - 0.004, -2.2, 1.2, z, z + 0.03, 'chrome', hull='none', cull='r')
        for j in range(8):
            yy = -2.1 + j * 0.42
            m.bx(WX - 0.32, WX - 0.04, yy, yy + 0.13, z + 0.03, z + 0.15, ('pWhite', 'pipeR', 'ink', 'lineY', 'pBlue')[(j + k) % 5], hull='none', cull='rb')
    solid(cols, WX - 0.36, -2.2, 0.5, WX, 1.2, 2.45)
    # ball bins and a weight bench in the middle
    for (bx, c) in ((-0.9, 'cone'), (0.1, 'pWhite')):
        m.bx(bx, bx + 0.8, -1.9, -1.2, 0.0, 0.7, 'steelD', hull='full', cull='b')
        for k in range(3):
            m.sp((bx + 0.17 + k * 0.23, -1.55 + (0.12 if k == 1 else -0.08), 0.76), 0.13, c if k != 1 else ('ink' if c == 'pWhite' else 'pipeR'), seg=(6, 4), hull='none')
        solid(cols, bx, -1.9, 0.0, bx + 0.8, -1.2, 0.85)
    m.bx(-0.6, 0.6, -0.4, -0.1, 0.0, 0.45, 'ink', hull='full', cull='b')
    m.bx(-0.65, 0.65, -0.45, -0.05, 0.45, 0.52, 'navy', hull='full')
    for sx in (-1, 1):
        m.bx(sx * 0.55 - 0.03, sx * 0.55 + 0.03, -0.1, -0.04, 0.0, 1.1, 'steelD', hull='none', cull='b')
    m.cy((-0.9, -0.07, 1.05), 0.03, 0.03, 1.8, 'chrome', seg=6, rot=(0, 90, 0), hull='none')
    for sx in (-1, 1):
        m.cy((sx * 0.75 - (0.06 if sx > 0 else 0), -0.07, 1.05), 0.2, 0.2, 0.06, 'ink', seg=10, rot=(0, 90, 0), hull='full')
    solid(cols, -0.65, -0.45, 0.0, 0.65, -0.05, 0.52)
    counter(m, cols, 0.9, 2.6, 0.75, 1.3, 'exitG', 'pWhite')
    m.bx(-2.4, -1.4, 0.6, 1.25, 0.18, 1.35, 'ink', hull='full', cull='b')                   # treadmill console
    m.bx(-2.5, -1.3, -0.2, 1.3, 0.0, 0.18, 'steelD', hull='full', cull='b')
    solid(cols, -2.5, -0.2, 0.0, -1.3, 0.6, 0.18)
    solid(cols, -2.4, 0.6, 0.0, -1.4, 1.25, 1.35)
    bed_items(m, -3.38, -1.6, ('pWhite', 'ink', 'pipeR'))
    bed_items(m, 1.6, 3.38, ('lineY', 'pBlue', 'exitG'))
    # stock room: boxes and two bikes on the wall
    stock(m, cols, -WX, -1.0, 2.6, WY1, h=1.3, rows=2, cols_=3)
    for k, c in enumerate(('pipeR', 'pBlue')):
        y = 2.2 + k * 0.9
        for zz in (0.4, 1.3):
            m.cy((WX - 0.2, y, zz), 0.32, 0.32, 0.05, 'tire', seg=10, rot=(0, 90, 0), hull='full')
        m.bm_((WX - 0.25, y, 0.4), (WX - 0.25, y + 0.15, 1.3), 0.04, c)
    solid(cols, WX - 0.25, 1.85, 0.0, WX, 3.35, 1.65)


def shop_hardware(m, cols):
    """Kessler Hardware: steel racking with paint cans and tool cases on both walls, a bin island of nails and
    fixings, a stand of shovels and rakes, the key-cutting counter; lumber and a ladder in the back"""
    shell(m, cols, 'concF', 'cream', 'cone', door=(1.6, 3.0), floor2='steel', pattern='tiles')
    street(m, 'KESSLER HARDWARE', 'cone', 'ink', ('cone', 'pWhite'), cap=0.56)
    goods = ('cone', 'pBlue', 'pipeR', 'lineY', 'steel', 'exitG', 'pWhite', 'ink')
    for side in (-1, 1):
        xw = side * WX
        a, b = sorted((xw, xw - side * 0.6))
        for y in (-2.25, -0.55, 1.1):
            for x in (a, b - 0.06):
                m.bx(x, x + 0.06, y, y + 0.06, 0.0, 2.6, 'pBlue', hull='none', cull='b')
        for k in range(4):
            z = 0.1 + k * 0.72
            m.bx(a + 0.004, b - 0.004, -2.19, 1.1, z, z + 0.05, 'cone', hull='none')
            yy = -2.15
            i = 0
            while yy < 1.0:
                c = goods[(i + k * 3 + (side > 0)) % len(goods)]
                if k % 2 == 0:   # paint cans
                    ca, cb_ = sorted((xw - side * 0.42, xw - side * 0.2))
                    m.bx(ca, cb_, yy, yy + 0.22, z + 0.05, z + 0.29, c, hull='none', cull='b' + ('l' if side < 0 else 'r'))
                    yy += 0.27
                else:            # tool cases
                    m.bx(a + 0.08, b - 0.08, yy, yy + 0.42, z + 0.05, z + 0.3 + 0.06 * (i % 2), c, hull='none', cull='b')
                    yy += 0.47
                i += 1
        solid(cols, a, -2.25, 0.0, b, 1.16, 2.6)
    # bin island: nails and fixings in rows of open bins
    m.bx(-0.6, 0.6, -1.9, -0.5, 0.0, 0.9, 'woodD', hull='full', cull='b')
    for i in range(3):
        for j in range(4):
            x, y = -0.5 + i * 0.36, -1.82 + j * 0.34
            m.bx(x, x + 0.3, y, y + 0.28, 0.9, 1.02, 'steel', hull='none', cull='b')
            uq(m, x + 0.03, x + 0.27, y + 0.03, y + 0.25, 0.99, ('steelD', 'galv', 'chrome', 'pYellow')[(i + j) % 4])
    solid(cols, -0.6, -1.9, 0.0, 0.6, -0.5, 1.02)
    # shovels and rakes in a stand
    m.bx(-0.5, 0.5, 0.1, 0.5, 0.0, 0.4, 'steelD', hull='full', cull='b')
    for k in range(5):
        x = -0.4 + k * 0.2
        m.bm_((x, 0.3, 0.3), (x + 0.03, 0.32, 1.7), 0.035, 'wood')
        m.bx(x - 0.08, x + 0.11, 0.29, 0.35, 1.7, 1.75, 'steelD', hull='none')
    solid(cols, -0.5, 0.1, 0.0, 0.5, 0.5, 1.75)
    counter(m, cols, -2.6, -0.2, 0.75, 1.3, 'cone', 'woodD')
    m.bx(-1.0, -0.6, 0.85, 1.2, 1.0, 1.25, 'steel', hull='full', cull='b')               # key cutter
    poster(m, -1.4, PY - 0.012, 2.4, 2.0, 0.5, 'ink', 'KEYS CUT', 'lineY', font='cond')
    bed_items(m, -3.38, -1.6, ('cone', 'pipeR', 'steel'), kind='bottle')
    bed_items(m, 1.6, 3.38, ('lineY', 'pBlue', 'cone'))
    # back room: a lumber stack, a stepladder, sacks
    for k in range(5):
        m.bx(-WX + 0.1, -0.4, 3.1 + k * 0.0, WY1 - 0.05, k * 0.12, k * 0.12 + 0.1, 'wood' if k % 2 else 'cardb', hull='full', cull='')
    solid(cols, -WX + 0.1, 3.1, 0.0, -0.4, WY1 - 0.05, 0.6)
    for sx in (-1, 1):
        m.bm_((0.6 + sx * 0.25, 2.3, 0.0), (0.6 + sx * 0.18, 2.6, 1.8), 0.05, 'cone')
        m.bm_((0.6 + sx * 0.25, 2.9, 0.0), (0.6 + sx * 0.18, 2.6, 1.8), 0.04, 'steel')
    solid(cols, 0.3, 2.3, 0.0, 0.9, 2.9, 1.8)
    stock(m, cols, 1.4, WX, 3.0, WY1, h=1.0, rows=1, cols_=3, c=('pWhite', 'cardb', 'pWhite'))


def shop_pawn(m, cols):
    """Lucky Seven Pawn: barred windows, glass cases of rings and watches in a U, guitars hung on the left wall,
    a shelf of radios and TVs on the right; the safe and tagged goods in the back"""
    shell(m, cols, 'walkB', 'cream', 'woodD', door=(-2.6, -1.2), floor2='walk', pattern='tiles')
    street(m, 'LUCKY 7 PAWN', 'ink', 'lineY', ('violet', 'lineY'), cap=0.6)
    for (x0, x1) in ((-WX, -1.5), (1.5, WX)):    # security bars inside the windows
        k = x0 + 0.35
        while k < x1 - 0.25:
            bq(m, k, k + 0.035, WY0 + 0.02, 0.6, 3.04, 'steelD')
            k += 0.25
    # glass cases: a U round the clerk
    def case(x0, x1, y0, y1):
        m.bx(x0, x1, y0, y1, 0.0, 0.62, 'woodD', hull='full', cull='b')
        uq(m, x0 + 0.04, x1 - 0.04, y0 + 0.04, y1 - 0.04, 0.625, 'navy')
        n = int((x1 - x0) / 0.18) if (x1 - x0) > (y1 - y0) else int((y1 - y0) / 0.18)
        for i in range(n):
            if (x1 - x0) > (y1 - y0):
                cx, cy = x0 + 0.12 + i * 0.18, (y0 + y1) / 2
            else:
                cx, cy = (x0 + x1) / 2, y0 + 0.12 + i * 0.18
            uq(m, cx - 0.04, cx + 0.04, cy - 0.04, cy + 0.04, 0.629, 'pYellow' if i % 3 else 'chrome')
        for (x, y) in ((x0, y0), (x1 - 0.025, y0), (x0, y1 - 0.025), (x1 - 0.025, y1 - 0.025)):
            m.bx(x, x + 0.025, y, y + 0.025, 0.62, 0.95, 'chrome', hull='none', cull='b')
        m.bx(x0, x1, y0, y1, 0.95, 0.975, 'glassL', hull='full')
        solid(cols, x0, y0, 0.0, x1, y1, 0.975)
    case(-1.6, 1.6, -1.6, -1.05)
    case(1.05, 1.6, -1.05, 0.6)
    case(-1.6, -1.05, -1.05, 0.6)
    # guitars on the left wall
    rq(m, -WX + 0.004, -2.3, 1.2, 1.0, 2.9, 'woodD')
    for k in range(5):
        y = -2.0 + k * 0.7
        c = ('pipeR', 'wood', 'ink', 'pBlue', 'brickT')[k]
        m.bx(-WX + 0.02, -WX + 0.1, y - 0.2, y + 0.2, 1.15, 1.6, c, hull='full', cull='l')
        m.bx(-WX + 0.02, -WX + 0.1, y - 0.15, y + 0.15, 1.6, 1.9, c, hull='full', cull='l')
        m.bx(-WX + 0.04, -WX + 0.08, y - 0.03, y + 0.03, 1.9, 2.6, 'woodD', hull='none', cull='l')
        rq(m, -WX + 0.104, y - 0.06, y + 0.06, 1.42, 1.54, 'ink')
        m.bx(-WX + 0.02, -WX + 0.06, y - 0.05, y + 0.05, 2.6, 2.75, 'ink', hull='none', cull='l')
    solid(cols, -WX, -2.3, 1.15, -WX + 0.1, 1.2, 2.75)
    # shelves of radios, TVs, a drum on the right
    rack(m, cols, 1, -2.3, 0.0, h=2.2, c='steelD', depth=0.55, n=3, colors=('ink', 'steel', 'woodD', 'interior'))
    m.cy((2.85, 0.6, 0.0), 0.3, 0.3, 0.45, 'pipeR', seg=10)
    m.cy((2.85, 0.6, 0.45), 0.29, 0.29, 0.01, 'pWhite', seg=10, hull='none')
    solid(cols, 2.55, 0.3, 0.0, 3.15, 0.9, 0.46)
    poster(m, 0.0, PY - 0.012, 2.35, 2.6, 0.55, 'ink', 'NO REFUNDS', 'lineY', font='display')
    bed_items(m, -3.38, -1.6, ('pYellow', 'ink', 'chrome'))
    bed_items(m, 1.6, 3.38, ('steel', 'woodD', 'pipeR'))
    # back room: a safe, tagged goods
    m.bx(-WX, -2.6, 3.0, WY1, 0.0, 1.4, 'steelD', hull='full', cull='b')
    m.cy((-3.05, 2.996, 0.85), 0.14, 0.14, 0.004, 'chrome', seg=8, rot=(90, 0, 0), hull='none')
    fq(m, -2.95, -2.9, 2.994, 0.45, 0.62, 'chrome')
    solid(cols, -WX, 3.0, 0.0, -2.6, WY1, 1.4)
    rack(m, cols, 1, 1.75, 3.9, h=2.0, c='steel', colors=('cardb', 'ink', 'steel', 'woodD'))


def shop_laundry(m, cols):
    """Bubbles Laundromat: front-loading washers down the left wall, dryers on the right, a folding table and plastic
    chairs in the middle, a change machine; the boiler and detergent drums in the back"""
    shell(m, cols, 'tileW', 'glassL', 'pBlue', door=(-0.7, 0.7), floor2='glass', pattern='tiles', back='glassL')
    street(m, 'BUBBLES LAUNDROMAT', 'pBlue', 'pWhite', ('pBlue', 'pWhite'), font='display', cap=0.7)
    for side, c, n in ((-1, 'pWhite', 5), (1, 'galv', 5)):
        xw = side * WX
        a, b = sorted((xw, xw - side * 0.75))
        m.bx(a, b, -2.25, 1.2, 0.0, 1.0 if side < 0 else 1.9, c, hull='full', cull='b')
        for k in range(n):
            y = -2.25 + 0.35 + k * 0.69
            xf = xw - side * 0.75          # the machines' front plane
            for z in ((0.5,) if side < 0 else (0.5, 1.35)):
                (rq if side < 0 else lq)(m, xf - side * 0.004, y - 0.25, y + 0.25, z - 0.25, z + 0.25, 'steelD')
                m.cy((xf + 0.008 if side < 0 else xf - 0.012, y, z), 0.19, 0.19, 0.004, 'glass' if k % 2 else 'pTeal', seg=8, rot=(0, 90, 0), hull='none')
            (rq if side < 0 else lq)(m, xf - side * 0.005, y - 0.25, y + 0.25, 0.85 if side < 0 else 1.72, 0.95 if side < 0 else 1.85, 'steel')
        solid(cols, a, -2.25, 0.0, b, 1.2, 1.0 if side < 0 else 1.9)
    for k in range(3):   # detergent boxes on the washers
        m.bx(-WX + 0.1, -WX + 0.4, -1.9 + k * 1.1, -1.7 + k * 1.1, 1.0, 1.3, ('cone', 'pBlue', 'lineY')[k], hull='full', cull='b')
    table(m, cols, -0.8, 0.8, -1.7, -0.9, h=0.9, top='pWhite', leg='steel')
    for i, (x, c) in enumerate(((-0.5, 'pBlue'), (-0.05, 'pink'), (0.4, 'pWhite'))):
        m.bx(x - 0.18, x + 0.18, -1.55, -1.1, 0.9, 1.0 + 0.04 * i, c, hull='none', cull='b')
    for k in range(3):
        chair(m, cols, -0.7 + k * 0.7, -0.15, ('pTeal', 'lineY', 'pTeal')[k], face=-1)
    m.bx(1.0, 1.6, 0.85, 1.4, 0.0, 1.7, 'signB', hull='full', cull='b')                    # change machine
    fq(m, 1.1, 1.5, 0.846, 1.0, 1.45, 'glassL')
    solid(cols, 1.0, 0.85, 0.0, 1.6, 1.4, 1.7)
    poster(m, -1.8, PY - 0.012, 2.4, 1.8, 0.5, 'pBlue', 'WASH  2.50', 'pWhite', font='display')
    bed_items(m, -3.38, -1.6, ('pBlue', 'pWhite', 'pink'), kind='bottle')
    bed_items(m, 1.6, 3.38, ('lineY', 'pTeal', 'pBlue'), kind='bottle')
    # back room: boiler, detergent drums
    m.cy((2.6, 3.1, 0.0), 0.6, 0.6, 2.2, 'galv', seg=10)
    m.bm_((2.6, 3.1, 2.2), (2.6, 3.1, RH - 0.01), 0.18, 'steel')
    solid(cols, 2.0, 2.5, 0.0, 3.2, 3.7, 2.2)
    for k in range(3):
        m.cy((-3.0 + k * 0.7, 3.4, 0.0), 0.3, 0.3, 0.9, ('pBlue', 'pBlue', 'pWhite')[k], seg=8)
    solid(cols, -3.3, 3.1, 0.0, -1.3, 3.7, 0.9)


SHOPS = {
    'Shop_Pharmacy': shop_pharmacy, 'Shop_Diner': shop_diner, 'Shop_Electronics': shop_electronics, 'Shop_Mart': shop_mart,
    'Shop_Books': shop_books, 'Shop_Barber': shop_barber, 'Shop_Sports': shop_sports, 'Shop_Hardware': shop_hardware,
    'Shop_Pawn': shop_pawn, 'Shop_Laundry': shop_laundry,
}


def build_shops(pal, ao):
    for name, fn in SHOPS.items():
        m = new(pal)
        cols = []
        fn(m, cols)
        make(name, m, ao, cols=cols)
