"""kit-townhomes furniture for the walk-in houses: two pieces per house, placed with the walk-in shell (theme `with`):
Int_<s>_GF (ground floor: living room at the front, kitchen at the back) and Int_<s>_UF (upper floor: the front room
by the balcony doors, the back bedroom). Same lot frame as townhomes_houses.py; the stair runs along the left party
wall (x -2.8 .. -1.5, y -3.2 .. 1.8), the doors open at x -2.75 .. -1.45. Furniture keeps a 1 m lane from the front
door round the sofa to the kitchen and the back door, and from the stair head to the balcony doors.
  A  (Walk_Siding)  family home: blue sofa, white shaker kitchen with an island; a home office upstairs
  B  (Walk_Stucco)  terracotta and oak: a dining table in the kitchen, a red sofa; a kids' room upstairs
  C  (Walk_Brick)   loft style: grey sectional, dark kitchen with a peninsula; the main bedroom upstairs
Collision: one box per piece of furniture, table tops float over their legs (shots go under them).
"""
from townhomes_base import *  # noqa: F401,F403


def solid(cols, x0, y0, z0, x1, y1, z1):
    cols.append(box(x0, y0, z0, x1, y1, z1))


# ---------------------------------------------------------------- furniture (z0 = the floor it stands on)
def sofa(m, cols, x0, x1, y0, y1, z0, c, back='-x', arms=True):
    """a sofa; back: the side its backrest stands on ('-x', '+x', '-y', '+y')"""
    m.bx(x0, x1, y0, y1, z0 + 0.08, z0 + 0.45, c)
    m.bx(x0 + 0.03, x1 - 0.03, y0 + 0.03, y1 - 0.03, z0, z0 + 0.08, 'woodD', hull='none', cull='b')
    if back == '-x':
        m.bx(x0, x0 + 0.22, y0, y1, z0 + 0.45, z0 + 0.88, c)
    elif back == '+x':
        m.bx(x1 - 0.22, x1, y0, y1, z0 + 0.45, z0 + 0.88, c)
    elif back == '-y':
        m.bx(x0, x1, y0, y0 + 0.22, z0 + 0.45, z0 + 0.88, c)
    else:
        m.bx(x0, x1, y1 - 0.22, y1, z0 + 0.45, z0 + 0.88, c)
    if arms:
        if back in ('-x', '+x'):
            a0, a1 = (x0 + 0.22, x1) if back == '-x' else (x0, x1 - 0.22)
            for (a, b) in ((y0, y0 + 0.18), (y1 - 0.18, y1)):
                m.bx(a0, a1, a, b, z0 + 0.45, z0 + 0.66, c)
        else:
            b0, b1 = (y0 + 0.22, y1) if back == '-y' else (y0, y1 - 0.22)
            for (a, b) in ((x0, x0 + 0.18), (x1 - 0.18, x1)):
                m.bx(a, b, b0, b1, z0 + 0.45, z0 + 0.66, c)
    # cushion seams and a throw pillow
    if back in ('-x', '+x'):
        ym = (y0 + y1) / 2
        uq(m, x0 + 0.25, x1 - 0.05, ym - 0.01, ym + 0.01, z0 + 0.454, 'iron')
        m.bx(x0 + 0.25 if back == '-x' else x1 - 0.42, x0 + 0.42 if back == '-x' else x1 - 0.25, y0 + 0.25, y0 + 0.6, z0 + 0.45, z0 + 0.78, 'trim', hull='none')
    else:
        xm = (x0 + x1) / 2
        uq(m, xm - 0.01, xm + 0.01, y0 + 0.05, y1 - 0.25, z0 + 0.454, 'iron')
        m.bx(x0 + 0.25, x0 + 0.6, y1 - 0.42 if back == '+y' else y0 + 0.25, y1 - 0.25 if back == '+y' else y0 + 0.42, z0 + 0.45, z0 + 0.78, 'trim', hull='none')
    solid(cols, x0, y0, z0, x1, y1, z0 + 0.88)


def table(m, cols, x0, x1, y0, y1, z0, h=0.76, top='wood', leg='woodD'):
    for x in (x0 + 0.05, x1 - 0.1):
        for y in (y0 + 0.05, y1 - 0.1):
            m.bx(x, x + 0.05, y, y + 0.05, z0, z0 + h - 0.05, leg, hull='none', cull='tb')
    m.bx(x0, x1, y0, y1, z0 + h - 0.05, z0 + h, top)
    solid(cols, x0, y0, z0 + h - 0.3, x1, y1, z0 + h)
    for x in (x0 + 0.05, x1 - 0.1):
        for y in (y0 + 0.05, y1 - 0.1):
            solid(cols, x, y, z0, x + 0.05, y + 0.05, z0 + h - 0.3)


def chair(m, cols, x, y, z0, c='wood', face='-y'):
    """dining chair, seat at 0.46, backrest on the side away from `face`"""
    m.bx(x - 0.21, x + 0.21, y - 0.21, y + 0.21, z0 + 0.42, z0 + 0.47, c)
    for (dx, dy) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
        m.bx(x + dx - 0.02, x + dx + 0.02, y + dy - 0.02, y + dy + 0.02, z0, z0 + 0.42, 'woodD', hull='none', cull='tb')
    d = {'-y': (0, 1), '+y': (0, -1), '-x': (1, 0), '+x': (-1, 0)}[face]
    bx_, by_ = x + d[0] * 0.18, y + d[1] * 0.18
    a, b = (bx_ - 0.03, bx_ + 0.03) if d[0] else (x - 0.21, x + 0.21)
    p, q = (by_ - 0.03, by_ + 0.03) if d[1] else (y - 0.21, y + 0.21)
    m.bx(a, b, p, q, z0 + 0.47, z0 + 0.95, c)
    solid(cols, x - 0.21, y - 0.21, z0, x + 0.21, y + 0.21, z0 + 0.95)


def stool(m, cols, x, y, z0, c='iron', seat='fabricR'):
    m.cy((x, y, z0 + 0.03), 0.04, 0.04, 0.63, c, seg=5, hull='none')
    m.cy((x, y, z0), 0.17, 0.17, 0.03, c, seg=8, hull='none')
    m.cy((x, y, z0 + 0.66), 0.19, 0.19, 0.08, seat, seg=8)
    solid(cols, x - 0.19, y - 0.19, z0, x + 0.19, y + 0.19, z0 + 0.74)


def counter_run(m, cols, x0, x1, y0, y1, z0, body, top, sink=None, stove=None, uppers=True, ywall=None, gap=None):
    """base cabinets with a worktop along a wall (the wall on the +y side when ywall > y1, else -y), door lines,
    a sink, a cooktop, wall cabinets above (skipping the window gap (x0, x1))"""
    m.bx(x0, x1, y0, y1, z0, z0 + 0.86, body, cull='b')
    m.bx(x0 - 0.02, x1 + 0.02, y0 - 0.03, y1, z0 + 0.86, z0 + 0.92, top)
    front = y0 if ywall is None or ywall > y1 else y1
    sgn = -1 if front == y0 else 1
    n = max(1, int(round((x1 - x0) / 0.6)))
    for i in range(1, n):
        x = x0 + i * (x1 - x0) / n
        (fq if sgn < 0 else bq)(m, x - 0.008, x + 0.008, front + sgn * 0.004, z0 + 0.08, z0 + 0.8, 'iron')
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        (fq if sgn < 0 else bq)(m, x - 0.06, x + 0.06, front + sgn * 0.006, z0 + 0.7, z0 + 0.73, 'chrome')
    if sink:
        sx = sink
        uq(m, sx - 0.32, sx + 0.32, y0 + 0.08, y1 - 0.1, z0 + 0.924, 'steel')
        m.cy((sx, y1 - 0.06 if sgn < 0 else y0 + 0.06, z0 + 0.92), 0.025, 0.025, 0.3, 'chrome', seg=5, hull='none')
    if stove:
        sx = stove
        uq(m, sx - 0.32, sx + 0.32, y0 + 0.06, y1 - 0.06, z0 + 0.924, 'iron')
        for (dx, dy) in ((-0.15, -0.12), (0.15, -0.12), (-0.15, 0.12), (0.15, 0.12)):
            disc(m, sx + dx, (y0 + y1) / 2 + dy, z0 + 0.928, 0.08, 'shingle', seg=6)
        (fq if sgn < 0 else bq)(m, sx - 0.3, sx + 0.3, front + sgn * 0.009, z0 + 0.12, z0 + 0.6, 'iron')
    solid(cols, x0 - 0.02, y0 - 0.03, z0, x1 + 0.02, y1, z0 + 0.92)
    if uppers:
        yw0, yw1 = (y1 - 0.35, y1) if sgn < 0 else (y0, y0 + 0.35)
        spans = [(x0, x1)] if not gap else [(x0, gap[0]), (gap[1], x1)]
        for (a, b) in spans:
            if b - a < 0.3:
                continue
            m.bx(a, b, yw0, yw1, z0 + 1.45, z0 + 2.2, body)
            k = max(1, int(round((b - a) / 0.5)))
            for i in range(1, k):
                x = a + i * (b - a) / k
                (fq if sgn < 0 else bq)(m, x - 0.008, x + 0.008, (yw0 if sgn < 0 else yw1) + sgn * 0.004, z0 + 1.5, z0 + 2.15, 'iron')
            solid(cols, a, yw0, z0 + 1.45, b, yw1, z0 + 2.2)


def fridge(m, cols, x0, x1, y0, y1, z0, c='chrome', face='-y'):
    m.bx(x0, x1, y0, y1, z0, z0 + 1.85, c)
    if face == '-y':
        fq(m, x0 + 0.02, x1 - 0.02, y0 - 0.004, z0 + 1.15, z0 + 1.17, 'steel')
        fq(m, x1 - 0.1, x1 - 0.07, y0 - 0.008, z0 + 0.6, z0 + 1.05, 'iron')
        for (x, y, c2) in ((x0 + 0.15, z0 + 1.4, 'flower'), (x0 + 0.3, z0 + 1.55, 'doorY'), (x0 + 0.2, z0 + 0.8, 'sidB')):
            fq(m, x - 0.05, x + 0.05, y0 - 0.008, y - 0.06, y + 0.06, c2)
    else:
        lq(m, x0 - 0.004, y0 + 0.02, y1 - 0.02, z0 + 1.15, z0 + 1.17, 'steel')
        lq(m, x0 - 0.008, y0 + 0.07, y0 + 0.1, z0 + 0.6, z0 + 1.05, 'iron')
    solid(cols, x0, y0, z0, x1, y1, z0 + 1.85)


def tv_unit(m, cols, x0, x1, y0, y1, z0, side='+x', c='woodD'):
    """a low media unit against a side wall with a flat TV on it (screen faces away from the wall)"""
    m.bx(x0, x1, y0, y1, z0, z0 + 0.5, c)
    if side == '+x':
        lq(m, x0 - 0.004, y0 + 0.05, (y0 + y1) / 2 - 0.02, z0 + 0.08, z0 + 0.42, 'woodL')
        lq(m, x0 - 0.004, (y0 + y1) / 2 + 0.02, y1 - 0.05, z0 + 0.08, z0 + 0.42, 'woodL')
        xt = x1 - 0.15
        m.bx(xt - 0.03, xt + 0.03, y0 + 0.1, y1 - 0.1, z0 + 0.62, z0 + 1.3, 'iron')
        lq(m, xt - 0.034, y0 + 0.14, y1 - 0.14, z0 + 0.66, z0 + 1.26, 'glassD')
        m.bx(xt - 0.12, xt + 0.12, (y0 + y1) / 2 - 0.15, (y0 + y1) / 2 + 0.15, z0 + 0.5, z0 + 0.62, 'iron', hull='none')
    else:
        rq(m, x1 + 0.004, y0 + 0.05, y1 - 0.05, z0 + 0.08, z0 + 0.42, 'woodL')
        xt = x0 + 0.15
        m.bx(xt - 0.03, xt + 0.03, y0 + 0.1, y1 - 0.1, z0 + 0.62, z0 + 1.3, 'iron')
        rq(m, xt + 0.034, y0 + 0.14, y1 - 0.14, z0 + 0.66, z0 + 1.26, 'glassD')
        m.bx(xt - 0.12, xt + 0.12, (y0 + y1) / 2 - 0.15, (y0 + y1) / 2 + 0.15, z0 + 0.5, z0 + 0.62, 'iron', hull='none')
    solid(cols, x0, y0, z0, x1, y1, z0 + 0.5)
    solid(cols, xt - 0.04, y0 + 0.1, z0 + 0.5, xt + 0.04, y1 - 0.1, z0 + 1.3)


def rug(m, x0, x1, y0, y1, z0, c, c2):
    uq(m, x0, x1, y0, y1, z0 + 0.008, c)
    uq(m, x0 + 0.15, x1 - 0.15, y0 + 0.15, y1 - 0.15, z0 + 0.012, c2)


def lamp(m, cols, x, y, z0, shade='trim'):
    m.cy((x, y, z0), 0.14, 0.14, 0.03, 'iron', seg=6, hull='none')
    m.cy((x, y, z0 + 0.03), 0.02, 0.02, 1.35, 'iron', seg=4, hull='none')
    m.cy((x, y, z0 + 1.3), 0.2, 0.13, 0.3, shade, seg=8)
    solid(cols, x - 0.14, y - 0.14, z0, x + 0.14, y + 0.14, z0 + 1.6)


def plant(m, cols, x, y, z0, h=1.0):
    m.cy((x, y, z0), 0.17, 0.2, 0.32, 'tileR', seg=7)
    m.sp((x, y, z0 + 0.32 + h * 0.4), h * 0.38, 'leaf', seg=(6, 4), scale=(1, 1, 1.2))
    m.sp((x + 0.1, y - 0.08, z0 + 0.32 + h * 0.62), h * 0.24, 'leafD', seg=(5, 3))
    solid(cols, x - 0.2, y - 0.2, z0, x + 0.2, y + 0.2, z0 + 0.32 + h * 0.8)


def shelf(m, cols, x0, x1, y0, y1, z0, h, c='woodD', side='+x', rows=4, books=('fabric', 'fabricR', 'doorY', 'doorG', 'trim')):
    """a bookcase against a wall; side: which wall it backs onto"""
    m.bx(x0, x1, y0, y1, z0, z0 + h, c)
    k = 0
    for r in range(rows):
        zb = z0 + 0.1 + r * (h - 0.15) / rows
        zt = zb + (h - 0.15) / rows * 0.75
        if side in ('+x', '-x'):
            xf = x0 - 0.004 if side == '+x' else x1 + 0.004
            f = lq if side == '+x' else rq
            y = y0 + 0.06
            while y < y1 - 0.12:
                w = 0.06 + 0.04 * ((k * 7) % 3)
                f(m, xf, y, min(y + w, y1 - 0.06), zb, zt - 0.06 * (k % 2), books[k % len(books)])
                y += w + 0.012
                k += 1
        else:
            yf = y0 - 0.004 if side == '+y' else y1 + 0.004
            f = fq if side == '+y' else bq
            x = x0 + 0.06
            while x < x1 - 0.12:
                w = 0.06 + 0.04 * ((k * 7) % 3)
                f(m, x, min(x + w, x1 - 0.06), yf, zb, zt - 0.06 * (k % 2), books[k % len(books)])
                x += w + 0.012
                k += 1
    solid(cols, x0, y0, z0, x1, y1, z0 + h)


def bed(m, cols, x0, x1, y0, y1, z0, cover, head='+x', pillow='trim', frame='woodD'):
    """a bed; head: the wall its headboard stands against"""
    m.bx(x0, x1, y0, y1, z0, z0 + 0.32, frame)
    m.bx(x0 + 0.03, x1 - (0.1 if head == '+x' else 0.03), y0 + 0.03, y1 - (0.1 if head == '+y' else 0.03), z0 + 0.32, z0 + 0.52, 'trim', hull='none')
    if head == '+x':
        m.bx(x0 - 0.02, x1 - 0.45, y0 - 0.02, y1 + 0.02, z0 + 0.5, z0 + 0.6, cover)
        m.bx(x1 - 0.1, x1, y0, y1, z0 + 0.32, z0 + 1.05, frame)
        for (a, b) in ((y0 + 0.1, (y0 + y1) / 2 - 0.05), ((y0 + y1) / 2 + 0.05, y1 - 0.1)):
            m.bx(x1 - 0.45, x1 - 0.12, a, b, z0 + 0.52, z0 + 0.66, pillow, hull='none')
    elif head == '+y':
        m.bx(x0 - 0.02, x1 + 0.02, y0 - 0.02, y1 - 0.45, z0 + 0.5, z0 + 0.6, cover)
        m.bx(x0, x1, y1 - 0.1, y1, z0 + 0.32, z0 + 1.05, frame)
        for (a, b) in ((x0 + 0.1, (x0 + x1) / 2 - 0.05), ((x0 + x1) / 2 + 0.05, x1 - 0.1)):
            m.bx(a, b, y1 - 0.45, y1 - 0.12, z0 + 0.52, z0 + 0.66, pillow, hull='none')
    solid(cols, x0, y0, z0, x1, y1, z0 + 0.62)
    if head == '+x':
        solid(cols, x1 - 0.1, y0, z0 + 0.62, x1, y1, z0 + 1.05)
    else:
        solid(cols, x0, y1 - 0.1, z0 + 0.62, x1, y1, z0 + 1.05)


def cabinet(m, cols, x0, x1, y0, y1, z0, h, c, face='-y', drawers=3):
    m.bx(x0, x1, y0, y1, z0, z0 + h, c)
    for k in range(drawers):
        z = z0 + 0.1 + k * (h - 0.15) / drawers
        zt = z + (h - 0.15) / drawers - 0.04
        if face == '-y':
            fq(m, x0 + 0.05, x1 - 0.05, y0 - 0.004, z, zt, 'woodL' if c != 'woodL' else 'wood')
            fq(m, (x0 + x1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, y0 - 0.008, zt - 0.08, zt - 0.05, 'chrome')
        elif face == '-x':
            lq(m, x0 - 0.004, y0 + 0.05, y1 - 0.05, z, zt, 'woodL' if c != 'woodL' else 'wood')
            lq(m, x0 - 0.008, (y0 + y1) / 2 - 0.06, (y0 + y1) / 2 + 0.06, zt - 0.08, zt - 0.05, 'chrome')
        else:
            rq(m, x1 + 0.004, y0 + 0.05, y1 - 0.05, z, zt, 'woodL' if c != 'woodL' else 'wood')
            rq(m, x1 + 0.008, (y0 + y1) / 2 - 0.06, (y0 + y1) / 2 + 0.06, zt - 0.08, zt - 0.05, 'chrome')
    solid(cols, x0, y0, z0, x1, y1, z0 + h)


def picture(m, x, y, z, w, h, c, face='+x'):
    """a framed picture on a wall (painted)"""
    if face == '+x':      # on the left wall, seen from +x
        rq(m, x + 0.004, y - w / 2, y + w / 2, z - h / 2, z + h / 2, 'woodD')
        rq(m, x + 0.008, y - w / 2 + 0.05, y + w / 2 - 0.05, z - h / 2 + 0.05, z + h / 2 - 0.05, c)
    elif face == '-x':
        lq(m, x - 0.004, y - w / 2, y + w / 2, z - h / 2, z + h / 2, 'woodD')
        lq(m, x - 0.008, y - w / 2 + 0.05, y + w / 2 - 0.05, z - h / 2 + 0.05, z + h / 2 - 0.05, c)
    elif face == '-y':
        fq(m, x - w / 2, x + w / 2, y - 0.004, z - h / 2, z + h / 2, 'woodD')
        fq(m, x - w / 2 + 0.05, x + w / 2 - 0.05, y - 0.008, z - h / 2 + 0.05, z + h / 2 - 0.05, c)
    else:
        bq(m, x - w / 2, x + w / 2, y + 0.004, z - h / 2, z + h / 2, 'woodD')
        bq(m, x - w / 2 + 0.05, x + w / 2 - 0.05, y + 0.008, z - h / 2 + 0.05, z + h / 2 - 0.05, c)


def pendant(m, x, y, zc, c='trim'):
    m.cy((x, y, zc - 0.5), 0.008, 0.008, 0.5, 'iron', seg=3, hull='none')
    m.cy((x, y, zc - 0.72), 0.22, 0.06, 0.22, c, seg=8)


# ---------------------------------------------------------------- the three houses
def int_a(pal, ao):
    """family home (Walk_Siding): blue sofa facing the TV on the right wall, white shaker kitchen with an island"""
    m = new(pal)
    cols = []
    z = GF
    rug(m, -0.2, 2.3, -3.6, -0.6, z, 'sidB', 'trim')
    sofa(m, cols, -0.5, 0.45, -3.2, -1.0, z, 'fabric', back='-x')
    table(m, cols, 0.95, 1.65, -2.6, -1.6, z, h=0.42, top='woodL')
    m.bx(1.1, 1.35, -2.4, -2.2, z + 0.42, z + 0.47, 'flower', hull='none')
    tv_unit(m, cols, 2.35, 2.8, -3.1, -1.5, z, side='+x')
    lamp(m, cols, 2.5, -3.9, z)
    plant(m, cols, 2.5, 0.75, z, h=1.0)
    shelf(m, cols, 2.45, 2.8, -0.9, 0.4, z, 1.9, side='+x')
    # kitchen
    counter_run(m, cols, -1.25, 2.0, 5.2, 5.8, z, 'trim', 'stone', sink=0.5, stove=-0.75, ywall=6, gap=(-0.6, 1.6))
    fridge(m, cols, 2.05, 2.8, 5.05, 5.8, z)
    m.bx(-0.1, 1.7, 2.9, 3.75, z, z + 0.88, 'sidB')
    m.bx(-0.16, 1.76, 2.84, 3.81, z + 0.88, z + 0.94, 'stone')
    solid(cols, -0.16, 2.84, z, 1.76, 3.81, z + 0.94)
    for x in (0.15, 0.8, 1.45):
        stool(m, cols, x, 2.45, z)
    for x in (0.25, 1.35):
        pendant(m, x, 3.3, UF - SLAB)
    m.bx(0.6, 1.0, 3.2, 3.5, z + 0.94, z + 1.04, 'doorY', hull='none', cull='b')   # fruit bowl
    picture(m, IX, 1.6, z + 1.6, 0.9, 0.6, 'sidY', face='-x')
    picture(m, IX, -2.3, z + 1.85, 1.1, 0.55, 'doorT', face='-x')
    make('Int_A_GF', m, ao, cols=cols)
    # upstairs: a home office by the balcony doors, a back bedroom
    m = new(pal)
    cols = []
    z = UF
    table(m, cols, 1.9, 2.75, -3.2, -1.6, z, top='woodL')
    m.bx(2.5, 2.56, -2.7, -2.1, z + 0.76, z + 1.15, 'iron', hull='none')
    lq(m, 2.495, -2.66, -2.14, z + 0.8, z + 1.11, 'glassD')
    chair(m, cols, 1.45, -2.4, z, c='iron', face='+x')
    shelf(m, cols, 2.45, 2.8, -0.9, 0.8, z, 2.0, side='+x')
    sofa(m, cols, -1.3, -0.45, 0.3, 2.4, z, 'sidG', back='-x')
    rug(m, -0.4, 1.6, -1.2, 1.2, z, 'stuP', 'sidC')
    plant(m, cols, -1.2, -3.9, z, h=0.9)
    bed(m, cols, 0.8, 2.8, 3.85, 5.45, z, 'sidB', head='+x')
    cabinet(m, cols, -1.3, 0.2, 5.25, 5.8, z, 1.9, 'trim', face='-y', drawers=2)
    picture(m, IX, 1.9, z + 1.5, 0.7, 0.5, 'leaf', face='-x')
    make('Int_A_UF', m, ao, cols=cols)


def int_b(pal, ao):
    """terracotta and oak (Walk_Stucco): a red sofa, a dining table under a pendant; a kids' room upstairs"""
    m = new(pal)
    cols = []
    z = GF
    rug(m, 0.2, 2.6, -3.6, -1.4, z, 'stuC', 'stuP')
    sofa(m, cols, 0.3, 2.5, -1.95, -1.1, z, 'fabricR', back='+y')
    table(m, cols, 1.0, 1.8, -3.1, -2.5, z, h=0.42, top='wood')
    m.cy((1.4, -2.8, z + 0.42), 0.1, 0.08, 0.16, 'doorT', seg=6, hull='none')
    cabinet(m, cols, 2.35, 2.8, -3.9, -2.9, z, 0.8, 'woodD', face='-x', drawers=2)   # a sideboard
    lamp(m, cols, 2.5, -0.75, z, shade='stuP')
    plant(m, cols, 2.5, -2.45, z, h=1.3)
    picture(m, IX, -2.6, z + 1.7, 1.0, 0.7, 'stuC', face='-x')
    # kitchen: terracotta cabinets along the back, a dining table for four
    counter_run(m, cols, -1.25, 2.1, 5.2, 5.8, z, 'stuC', 'woodL', sink=0.5, stove=1.6, ywall=6, gap=(-0.6, 1.6))
    fridge(m, cols, 2.2, 2.8, 3.7, 4.5, z, c='trim', face='-x')
    table(m, cols, -0.1, 1.5, 1.4, 2.4, z, top='wood')
    for (x, y, f) in ((0.3, 1.0, '+y'), (1.1, 1.0, '+y'), (0.3, 2.8, '-y'), (1.1, 2.8, '-y')):
        chair(m, cols, x, y, z, c='wood', face=f)
    pendant(m, 0.7, 1.9, UF - SLAB, c='tileR')
    m.bx(0.5, 0.9, 1.75, 2.05, z + 0.76, z + 0.84, 'doorY', hull='none', cull='b')
    make('Int_B_GF', m, ao, cols=cols)
    m = new(pal)
    cols = []
    z = UF
    # kids' room: a bunk bed, a toy chest, a play rug
    m.bx(1.86, 2.76, -3.58, -1.62, z, z + 0.3, 'doorT')
    m.bx(1.89, 2.73, -3.55, -1.65, z + 0.3, z + 0.45, 'trim', hull='none')
    m.bx(1.86, 2.76, -3.58, -1.62, z + 1.25, z + 1.4, 'doorT')
    m.bx(1.89, 2.73, -3.55, -1.65, z + 1.4, z + 1.55, 'sidY', hull='none')
    for y in (-3.61, -1.67):
        for x in (1.83, 2.71):
            m.bx(x, x + 0.08, y, y + 0.08, z, z + 1.75, 'doorT', hull='none', cull='tb')
    for k in range(4):
        m.bx(1.8, 1.85, -1.95 + 0.0, -1.85, z + 0.35 + k * 0.3, z + 0.39 + k * 0.3, 'trim', hull='none')
    solid(cols, 1.85, -3.6, z, 2.8, -1.6, z + 1.75)
    m.bx(1.6, 2.5, 2.4, 2.95, z, z + 0.5, 'doorY')
    m.bx(1.56, 2.54, 2.36, 2.99, z + 0.5, z + 0.58, 'fabricR')
    solid(cols, 1.56, 2.36, z, 2.54, 2.99, z + 0.58)
    rug(m, -0.6, 1.4, -2.0, 0.6, z, 'sidY', 'sidB')
    for (x, y, c, s) in ((0.2, -0.5, 'fabricR', 0.18), (0.6, 0.1, 'doorT', 0.14), (-0.3, -1.2, 'doorY', 0.2)):
        m.bx(x - s, x + s, y - s, y + s, z + 0.012, z + 0.012 + s * 1.6, c, hull='full')
        solid(cols, x - s, y - s, z, x + s, y + s, z + 0.012 + s * 1.6)
    m.sp((1.0, -1.4, z + 0.18), 0.17, 'flower', seg=(7, 4))
    solid(cols, 0.83, -1.57, z, 1.17, -1.23, z + 0.35)
    shelf(m, cols, 2.45, 2.8, -0.6, 0.9, z, 1.4, c='trim', side='+x', rows=3)
    picture(m, IX, 2.2, z + 1.6, 0.6, 0.6, 'doorY', face='-x')
    bed(m, cols, 0.8, 2.8, 3.85, 5.45, z, 'stuP', head='+x', frame='wood')
    cabinet(m, cols, -1.3, 0.2, 5.25, 5.8, z, 1.1, 'woodL', face='-y', drawers=3)
    make('Int_B_UF', m, ao, cols=cols)


def int_c(pal, ao):
    """loft style (Walk_Brick): grey sectional, a dark kitchen with a peninsula and stools; the main bedroom upstairs"""
    m = new(pal)
    cols = []
    z = GF
    rug(m, -0.2, 2.2, -3.2, -0.6, z, 'shingle', 'sidG')
    sofa(m, cols, -0.4, 0.5, -3.0, -0.8, z, 'sidG', back='-x')
    sofa(m, cols, 0.5, 2.0, -1.65, -0.8, z, 'sidG', back='+y', arms=False)
    table(m, cols, 0.85, 1.75, -2.6, -1.95, z, h=0.4, top='iron', leg='iron')
    tv_unit(m, cols, 2.35, 2.8, -3.3, -1.7, z, side='+x', c='iron')
    shelf(m, cols, 2.45, 2.8, -0.9, 0.5, z, 2.0, c='iron', side='+x')
    lamp(m, cols, 2.5, -3.85, z, shade='doorY')
    counter_run(m, cols, -1.25, 2.8, 5.2, 5.8, z, 'iron', 'stone', sink=0.5, stove=2.1, ywall=6, gap=(-0.6, 1.6))
    m.bx(2.2, 2.8, 2.6, 4.6, z, z + 0.88, 'iron')
    m.bx(2.14, 2.8, 2.56, 4.64, z + 0.88, z + 0.94, 'stone')
    solid(cols, 2.14, 2.56, z, 2.8, 4.64, z + 0.94)
    for y in (3.0, 3.6, 4.2):
        stool(m, cols, 1.8, y, z, c='chrome', seat='iron')
    for y in (3.0, 4.2):
        pendant(m, 2.45, y, UF - SLAB, c='iron')
    plant(m, cols, -1.2, 1.2, z, h=1.4)
    make('Int_C_GF', m, ao, cols=cols)
    m = new(pal)
    cols = []
    z = UF
    bed(m, cols, 0.7, 2.8, -3.0, -1.0, z, 'sidC', head='+x', pillow='trim', frame='iron')
    for y in (-3.4, -0.6):
        m.bx(2.3, 2.8, y - 0.25, y + 0.25, z, z + 0.55, 'woodD')
        solid(cols, 2.3, y - 0.25, z, 2.8, y + 0.25, z + 0.55)
    m.cy((2.55, -3.4, z + 0.55), 0.1, 0.07, 0.3, 'doorY', seg=6)
    cabinet(m, cols, 2.3, 2.8, 0.4, 1.8, z, 1.0, 'woodD', face='-x', drawers=3)
    rug(m, -0.3, 1.9, -3.6, -0.4, z, 'sidC', 'stuP')
    sofa(m, cols, -1.3, -0.45, 0.6, 2.2, z, 'fabricR', back='-x')
    lamp(m, cols, -1.15, -0.1, z, shade='trim')
    cabinet(m, cols, -1.3, 0.6, 5.25, 5.8, z, 2.1, 'iron', face='-y', drawers=2)
    bed(m, cols, 1.1, 2.8, 3.85, 5.45, z, 'fabric', head='+x', frame='woodD')
    make('Int_C_UF', m, ao, cols=cols)


def build_rooms(pal, ao):
    int_a(pal, ao)
    int_b(pal, ao)
    int_c(pal, ao)
