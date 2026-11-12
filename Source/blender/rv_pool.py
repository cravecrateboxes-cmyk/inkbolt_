"""INKBOLT kit-riviera, zone 2 (the pool terrace and the roof garden on the spa podium): the infinity pool along the
cliff (landmark; three segments: the south end, a middle, the north end with the bronze wave sculpture), the spa
pool, the pool bar, sun-lounger pairs under parasols, the towel hut, outdoor showers, tall Canary palms in pots,
planters of lavender, the roof garden's pergola lounges, the belvedere, daybeds, its stairs and paving.
See rv_base.py for the conventions. Pools: water at WATER (0.24 m) over the terrace floor, copings 0.3 m high and
walkable (robots and the player step over them and wade).
"""
import math

from rv_base import H, DECK, RISE, TREAD, WATER, COP, RKit, srt, txt, disc, vdisc, frame_y, potted, bougainvillea
from hotel_base import armchair, sofa, coffee_table, flowers, side_table


# ================================================================ the infinity pool [9, 12] (placed turned: local +X north)
def coping(k, x0, x1, y0, y1):
    k.bx(x0, x1, y0, y1, 0.0, COP, 'marble')
    k.col(x0, x1, y0, y1, 0, COP, True)


def water(k, x0, x1, y0, y1, seed=0):
    k.qz(x0, x1, y0, y1, WATER, 1, 'water')
    n = int((x1 - x0) * (y1 - y0) / 6) + 2
    for i in range(n):
        h1 = (math.sin(seed * 7.1 + i * 12.9898) * 43758.5453) % 1
        h2 = (math.sin(seed * 3.3 + i * 78.233) * 12543.123) % 1
        x = x0 + 0.5 + h1 * (x1 - x0 - 1.0)
        y = y0 + 0.4 + h2 * (y1 - y0 - 0.8)
        w = 0.4 + h1 * 0.8
        k.qz(x - w / 2, x + w / 2, y - 0.025, y + 0.025, WATER + 0.003, 1, 'waterL')


def pool_seg(k, end):
    """one 9 m segment of the infinity pool, 12 m across: the coping on the terrace side (-Y) and, at an end, across
    the end; the west side (+Y) runs out to the vanishing edge (the zone's edge cell); underwater lights in the
    coping's face, chrome ladders; end 'N' adds the bronze wave sculpture on its plinth in the water"""
    k.begin()
    X, Y, C = 4.5, 6.0, 0.45
    coping(k, -X, X, -Y, -Y + C)
    k.qz(-X, X, -Y + 0.06, -Y + 0.12, COP + 0.003, 1, 'tile')
    wx0, wx1 = -X, X
    if end == 'S':
        coping(k, -X, -X + C, -Y + C, Y)
        k.qz(-X + 0.06, -X + 0.12, -Y + C, Y, COP + 0.003, 1, 'tile')
        wx0 = -X + C
    elif end == 'N':
        coping(k, X - C, X, -Y + C, Y)
        k.qz(X - 0.12, X - 0.06, -Y + C, Y, COP + 0.003, 1, 'tile')
        wx1 = X - C
    water(k, wx0, wx1, -Y + C, Y, seed={'S': 1, 'M': 2, 'N': 3}[end])
    # a band of lighter water where it runs to the edge, sun glints
    k.qz(wx0, wx1, Y - 0.5, Y - 0.25, WATER + 0.006, 1, 'tile')
    for (x, y) in ((-2.5, 1.5), (1.0, -2.0), (2.8, 3.2)):
        k.poly([(x, y, WATER + 0.009), (x + 0.5, y + 0.1, WATER + 0.009), (x + 0.45, y + 0.16, WATER + 0.009), (x - 0.05, y + 0.06, WATER + 0.009)], 'glint', (0, 0, 1))
    # chrome ladders
    for x in ((-2.0, 2.0) if end == 'M' else (0.5,)):
        for dx in (-0.25, 0.25):
            k.cyl(x + dx, -Y + C + 0.12, COP - 0.15, 0.022, 0.022, 0.95, 'chrome', seg=5, ink=False)
            k.beam((x + dx, -Y + C + 0.12, COP + 0.8), (x + dx, -Y + 0.15, COP + 0.8), 0.04, 'chrome', ink=False)
            k.beam((x + dx, -Y + 0.15, COP + 0.78), (x + dx, -Y + 0.15, COP), 0.032, 'chrome', ink=False)
        k.col(x - 0.3, x + 0.3, -Y + 0.1, -Y + C + 0.16, COP, COP + 0.85)
    if end == 'N':
        # La Vague: a bronze wave on a mosaic plinth in the water near the north end
        px, py = X - 2.2, 1.5
        k.bx(px - 0.6, px + 0.6, py - 0.6, py + 0.6, 0.0, 0.62, 'marble')
        k.qz(px - 0.54, px + 0.54, py - 0.54, py + 0.54, 0.623, 1, 'tile')
        k.prism_y([(py - 0.5, 0.63), (py - 0.2, 0.63), (py + 0.45, 2.6), (py + 0.2, 2.75)], px - 0.12, px + 0.12, 'bronze')
        k.prism_y([(py + 0.2, 2.75), (py + 0.45, 2.6), (py + 0.85, 3.0), (py + 0.6, 3.2)], px - 0.1, px + 0.1, 'bronze')
        k.prism_y([(py + 0.6, 3.2), (py + 0.85, 3.0), (py + 1.0, 3.12)], px - 0.07, px + 0.07, 'gold')
        k.col(px - 0.6, px + 0.6, py - 0.6, py + 0.6, 0, 0.62, True)
        k.col(px - 0.14, px + 0.14, py - 0.5, py + 0.75, 0.62, 3.1)
    return k


def spa_pool(k):
    """[8, 6] the spa pool: copings all round, mosaic bands, a raised whirlpool basin at one end with a spout, steps
    with a chrome rail"""
    k.begin()
    X, Y, C = 4.0, 3.0, 0.4
    coping(k, -X, X, -Y, -Y + C)
    coping(k, -X, X, Y - C, Y)
    coping(k, -X, -X + C, -Y + C, Y - C)
    coping(k, X - C, X, -Y + C, Y - C)
    for (a, b, c, d) in ((-X, X, -Y + 0.05, -Y + 0.1), (-X, X, Y - 0.1, Y - 0.05)):
        k.qz(a + 0.05, b - 0.05, c, d, COP + 0.003, 1, 'tile')
    water(k, -X + C, X - C, -Y + C, Y - C, seed=7)
    # the whirlpool: a round raised basin (0.6 m) in the east end, its own water with foam
    cx, cy, R = X - 1.6, 0.0, 1.1
    k.cyl(cx, cy, 0, R, R, 0.62, 'marble', seg=14)
    disc(k, cx, cy, 0.623, R - 0.12, 'tile', n=14)
    disc(k, cx, cy, 0.626, R - 0.2, 'waterL', n=12)
    for i in range(8):
        a = i * 0.8
        k.sph(cx + math.cos(a) * 0.45, cy + math.sin(a) * 0.45, 0.63, 0.08, 'ivory', seg=(5, 3), scale=(1, 1, 0.4), ink=False)
    k.col(cx - R * 0.72, cx + R * 0.72, cy - R * 0.72, cy + R * 0.72, 0, 0.62, True)
    k.col(cx - R, cx + R, cy - R * 0.45, cy + R * 0.45, 0, 0.62, True)
    # a bronze spout pouring into the pool from the west coping
    k.bx(-X + 0.05, -X + 0.35, -0.2, 0.2, COP, 0.75, 'stone')
    k.beam((-X + 0.3, 0, 0.65), (-X + 0.65, 0, 0.6), 0.06, 'bronze', ink=False)
    k.beam((-X + 0.67, 0, 0.58), (-X + 0.85, 0, WATER), 0.05, 'waterL', ink=False)
    k.col(-X + 0.05, -X + 0.35, -0.2, 0.2, COP, 0.75)
    # chrome rail at the steps (south side)
    for dx in (-0.25, 0.25):
        k.cyl(-1.0 + dx, -Y + C + 0.1, COP - 0.15, 0.022, 0.022, 0.95, 'chrome', seg=5, ink=False)
        k.beam((-1.0 + dx, -Y + C + 0.1, COP + 0.8), (-1.0 + dx, -Y + 0.15, COP + 0.8), 0.04, 'chrome', ink=False)
        k.beam((-1.0 + dx, -Y + 0.15, COP + 0.78), (-1.0 + dx, -Y + 0.15, COP), 0.032, 'chrome', ink=False)
    k.col(-1.3, -0.7, -Y + 0.1, -Y + C + 0.14, COP, COP + 0.85)
    return k


# ================================================================ terrace furniture
def lounger_at(k, x, y, deg, cushion='ivory', towel='wine'):
    """a teak sun lounger with a cushion and a raised back (the head toward local +Y), a rolled towel"""
    k.push(x, y, deg)
    k.bx(-0.34, 0.34, -0.95, 0.95, 0.22, 0.3, 'teak')
    for (lx, ly) in ((-0.28, -0.85), (0.28, -0.85), (-0.28, 0.85), (0.28, 0.85)):
        k.bx(lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0, 0.22, 'teak2', ink=False)
    k.bx(-0.31, 0.31, -0.92, 0.3, 0.3, 0.38, cushion)
    k.m.box((0, 0.6, 0.55), (0.6, 0.75, 0.08), cushion, rot=(40, 0, 0), bevel=False)
    k._mark(True)
    k.m.box((0, 0.66, 0.5), (0.66, 0.75, 0.05), 'teak', rot=(40, 0, 0), bevel=False)
    k._mark(False)
    k.cyl(-0.2, -0.65, 0.46, 0.08, 0.08, 0.4, towel, seg=8, rot=(0, 90, 0))
    k.pop()


def parasol_at(k, x, y, r=1.25, h=2.45, stripes=('wine', 'canvas')):
    """a market parasol: a white pole, an eight-panel canopy in two colours, a valance"""
    k.cyl(x, y, 0, 0.2, 0.22, 0.08, 'stone2', seg=8)
    k.cyl(x, y, 0.08, 0.025, 0.025, h - 0.08 + 0.1, 'ivory', seg=5)
    n = 8
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        p0 = (x + math.cos(a0) * r, y + math.sin(a0) * r, h - 0.35)
        p1 = (x + math.cos(a1) * r, y + math.sin(a1) * r, h - 0.35)
        k.poly([(x, y, h + 0.12), p0, p1], stripes[i % 2], (0, 0, 1))
        k.poly([(x, y, h + 0.115), p1, p0], stripes[i % 2], (0, 0, -1))
        k.poly([p0, p1, (p1[0], p1[1], p1[2] - 0.16), (p0[0], p0[1], p0[2] - 0.16)], stripes[(i + 1) % 2],
               (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0))
    k.cyl(x, y, h + 0.1, 0.05, 0.02, 0.12, 'ivory', seg=5, ink=False)


def sun_set(k):
    """[3, 3] two loungers facing the sea (local +Y head, so the feet point -Y; the theme turns the set to face west),
    a teak side table with a tray of drinks and a folded towel, a parasol over them"""
    k.begin()
    lounger_at(k, -0.75, 0.1, 0)
    lounger_at(k, 0.75, 0.1, 0, towel='emerald')
    k.bx(-0.22, 0.22, 0.55, 0.95, 0.0, 0.42, 'teak')
    k.qz(-0.15, 0.15, 0.62, 0.88, 0.423, 1, 'ivory')
    k.cyl(-0.06, 0.72, 0.426, 0.035, 0.03, 0.14, 'crystal2', seg=5, ink=False)
    k.cyl(0.08, 0.8, 0.426, 0.035, 0.03, 0.14, 'emerald', seg=5, ink=False)
    parasol_at(k, 0.0, 0.75, 1.35)
    for x in (-0.75, 0.75):
        k.col(x - 0.34, x + 0.34, -0.85, 1.05, 0, 0.5)
        k.col(x - 0.32, x + 0.32, 0.6, 1.0, 0.5, 1.05)
    k.col(-0.22, 0.22, 0.55, 0.95, 0, 0.42)
    k.col(-0.05, 0.05, 0.7, 0.8, 0.42, 2.4)
    return k


def lounger(k):
    """[1, 2] a single lounger (by the spa pool)"""
    k.begin()
    lounger_at(k, 0, 0, 0, towel='teal2')
    k.col(-0.34, 0.34, -0.95, 0.95, 0, 0.5)
    k.col(-0.32, 0.32, 0.45, 0.95, 0.5, 1.05)
    return k


def pool_bar(k):
    """[8, 4] Le Bar de la Plage: a stone-faced U counter with a teak top round a back bar of bottles, under a
    pergola with a blue and white striped canvas; stools along the front"""
    k.begin()
    X, Y = 4.0, 2.0
    # counter: front (-Y) and two returns
    k.bx(-3.2, 3.2, -1.2, -0.7, 0.0, 1.05, 'stucco')
    k.bx(-3.3, 3.3, -1.3, -0.65, 1.05, 1.12, 'teak')
    for s in (-1, 1):
        a, b = srt(s * 3.2, s * 2.7)
        k.bx(a, b, -0.7, 0.9, 0.0, 1.05, 'stucco')
        a2, b2 = srt(s * 3.3, s * 2.65)
        k.bx(a2, b2, -0.65, 0.95, 1.05, 1.12, 'teak')
    for i in range(7):
        x = -2.85 + i * 0.95
        k.qy(x - 0.32, x + 0.32, 0.18, 0.88, -1.203, -1, 'tile' if i % 2 else 'wine')
    # back bar with bottles and a sign
    k.bx(-2.4, 2.4, 1.4, 1.9, 0.0, 1.0, 'teak2')
    k.bx(-2.4, 2.4, 1.6, 1.9, 1.0, 2.4, 'teak2')
    for z in (1.35, 1.8):
        k.bx(-2.35, 2.35, 1.35, 1.6, z - 0.04, z, 'teak', ink=False)
        for i in range(14):
            x = -2.2 + i * 0.33
            c = ('leaf2', 'amber', 'crystal2', 'wine3', 'fire')[(i + int(z * 10)) % 5]
            k.cyl(x, 1.47, z, 0.045, 0.04, 0.28, c, seg=6, ink=False)
    k.qy(-1.6, 1.6, 2.0, 2.35, 1.597, -1, 'wine2')
    txt(k, 'BAR DE LA PLAGE', 0, 1.594, 2.17, 0.2, 'gold', font='serif', valign='m', maxw=3.0)
    # pergola posts and canvas
    for (x, y) in ((-3.7, -1.6), (3.7, -1.6), (-3.7, 1.7), (3.7, 1.7)):
        k.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.0, 2.8, 'ivory')
    for y in (-1.6, 1.7):
        k.bx(-3.9, 3.9, y - 0.08, y + 0.08, 2.8, 2.95, 'teak')
    for i in range(9):
        x = -3.6 + i * 0.9
        k.bx(x - 0.04, x + 0.04, -1.85, 1.95, 2.95, 3.05, 'teak', ink=False)
    for i in range(8):
        x0 = -3.6 + i * 0.9
        k.qz(x0 + 0.04, x0 + 0.86, -1.8, 1.9, 3.053, 1, 'wine' if i % 2 else 'canvas')
        k.qz(x0 + 0.04, x0 + 0.86, -1.8, 1.9, 3.05, -1, 'wine' if i % 2 else 'canvas')
    # stools
    for i in range(6):
        x = -2.6 + i * 1.04
        k.cyl(x, -1.65, 0.0, 0.16, 0.12, 0.04, 'chrome', seg=8, ink=False)
        k.cyl(x, -1.65, 0.04, 0.03, 0.03, 0.66, 'chrome', seg=5, ink=False)
        k.cyl(x, -1.65, 0.7, 0.19, 0.19, 0.07, 'wine', seg=8)
        k.col(x - 0.19, x + 0.19, -1.84, -1.46, 0, 0.77)
    k.col(-3.3, 3.3, -1.3, -0.65, 0, 1.12)
    for s in (-1, 1):
        a2, b2 = srt(s * 3.3, s * 2.65)
        k.col(a2, b2, -0.65, 0.95, 0, 1.12)
    k.col(-2.4, 2.4, 1.4, 1.9, 0, 2.4)
    for (x, y) in ((-3.7, -1.6), (3.7, -1.6), (-3.7, 1.7), (3.7, 1.7)):
        k.col(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, 2.8)
    return k


def towel_hut(k):
    """[3, 2] the towel hut: a white timber kiosk with a striped awning, shelves of rolled towels, the SERVIETTES sign"""
    k.begin()
    k.bx(-1.4, 1.4, -0.2, 0.9, 0.0, 2.5, 'stucco')
    k.bx(-1.5, 1.5, -0.3, 1.0, 2.5, 2.65, 'ivory')
    k.qy(-1.2, 1.2, 0.9, 2.1, -0.203, -1, 'navy2')
    k.bx(-1.4, 1.4, -0.75, -0.2, 0.0, 0.95, 'ivory')
    k.bx(-1.45, 1.45, -0.8, -0.15, 0.95, 1.0, 'teak')
    for i in range(8):
        x = -1.15 + i * 0.33
        for j in range(2):
            k.cyl(x, -0.48 + j * 0.0, 1.0 + j * 0.16, 0.075, 0.075, 0.42, ('wine', 'ivory', 'tile')[(i + j) % 3], seg=8, rot=(90, 0, 0), ink=False)
    for i in range(6):
        x = -1.5 + i * 0.5
        k.poly([(x, -0.3, 2.5), (x + 0.5, -0.3, 2.5), (x + 0.5, -1.0, 2.05), (x, -1.0, 2.05)], 'wine' if i % 2 else 'canvas', (0, -0.55, 0.85))
    k.bx(-1.0, 1.0, 0.3, 0.42, 2.65, 3.05, 'wine2')
    txt(k, 'SERVIETTES', 0, 0.297, 2.85, 0.17, 'ivory', font='sans', valign='m', maxw=1.8)
    k.col(-1.4, 1.4, -0.2, 0.9, 0, 2.65)
    k.col(-1.45, 1.45, -0.8, -0.15, 0, 1.0)
    return k


def shower(k):
    """an outdoor shower: a chrome column with a rain head on a teak grate"""
    k.begin()
    k.bx(-0.42, 0.42, -0.42, 0.42, 0.0, 0.06, 'teak')
    for i in range(6):
        x = -0.35 + i * 0.14
        k.qz(x, x + 0.06, -0.38, 0.38, 0.063, 1, 'teak2')
    k.cyl(0, 0.3, 0.06, 0.05, 0.05, 2.3, 'chrome', seg=6)
    k.beam((0, 0.3, 2.34), (0, -0.05, 2.34), 0.05, 'chrome', ink=False)
    k.cyl(0, -0.08, 2.24, 0.16, 0.16, 0.06, 'chrome', seg=10)
    k.bx(-0.05, 0.05, 0.22, 0.27, 1.1, 1.3, 'chrome', ink=False)
    k.col(-0.08, 0.08, 0.22, 0.38, 0, 2.4)
    return k


def canary_palm(k):
    """a tall Canary Island date palm in a big terracotta pot: a scaled trunk, a crown of arching fronds, dates"""
    k.begin()
    k.cyl(0, 0, 0, 0.42, 0.5, 0.75, 'terra', seg=8)
    k.cyl(0, 0, 0.7, 0.53, 0.53, 0.08, 'emerald2', seg=8, ink=False)
    disc(k, 0, 0, 0.74, 0.46, 'soil', n=8)
    for i in range(3):
        z = 0.74 + i * 1.5
        k.cyl(0.04 * i, 0, z, 0.24 - i * 0.02, 0.21 - i * 0.02, 1.5, 'oak' if i % 2 else 'teak2', seg=6)
    top = 0.74 + 3 * 1.5
    k.sph(0.12, 0, top + 0.1, 0.32, 'leaf2', seg=(5, 3))
    for i in range(8):
        a = i / 8 * math.pi * 2
        ca, sa = math.cos(a), math.sin(a)
        p0 = (0.12 + ca * 0.2, sa * 0.2, top + 0.15)
        p1 = (0.12 + ca * 1.3, sa * 1.3, top + 0.75 - (i % 2) * 0.2)
        p2 = (0.12 + ca * 2.4, sa * 2.4, top - 0.2 - (i % 3) * 0.15)
        k.beam(p0, p1, 0.18, 'leaf' if i % 2 else 'leaf2')
        k.beam(p1, p2, 0.14, 'leaf' if i % 2 else 'leaf2', ink=False)
    for i in range(2):
        a = i * 2.6
        k.sph(0.12 + math.cos(a) * 0.3, math.sin(a) * 0.3, top - 0.2, 0.12, 'fire', seg=(4, 3), ink=False)
    k.col(-0.5, 0.5, -0.5, 0.5, 0, 0.82)
    k.col(-0.25, 0.3, -0.24, 0.24, 0.82, top)
    return k


def planter(k):
    """[3, 1] a long stucco planter with lavender and rosemary, a blue tile band"""
    k.begin()
    k.bx(-1.45, 1.45, -0.4, 0.4, 0.0, 0.62, 'stucco')
    k.bx(-1.5, 1.5, -0.45, 0.45, 0.62, 0.7, 'stone')
    for s in (-1, 1):
        for i in range(6):
            x = -1.35 + i * 0.5
            k.qy(x + 0.03, x + 0.44, 0.2, 0.42, s * 0.403, s, 'wine' if i % 2 else 'tile')
    k.qz(-1.42, 1.42, -0.37, 0.37, 0.66, 1, 'soil')
    for i in range(5):
        x = -1.1 + i * 0.55
        k.sph(x, 0, 0.8, 0.3, 'leaf2' if i % 2 else 'leaf', seg=(5, 3), scale=(1, 1.1, 0.7))
        if i % 2 == 0:
            for j in range(3):
                a = j * 2.1
                k.cyl(x + math.cos(a) * 0.12, math.sin(a) * 0.14, 0.88, 0.035, 0.02, 0.22, 'blush', seg=3, ink=False)
    k.col(-1.5, 1.5, -0.45, 0.45, 0, 0.75)
    return k


def olive_tree(k, s=1.0):
    """an old olive in a square stone planter: a gnarled split trunk, a silvery crown of clumps"""
    k.begin()
    k.bx(-0.85, 0.85, -0.85, 0.85, 0.0, 0.55, 'stone')
    k.bx(-0.9, 0.9, -0.9, 0.9, 0.55, 0.62, 'stone2')
    k.qz(-0.8, 0.8, -0.8, 0.8, 0.6, 1, 'soil')
    for (a, b, t) in (((0, 0, 0.6), (0.25, 0.1, 1.6), 0.22), ((0.25, 0.1, 1.6), (0.55, 0.3, 2.4), 0.16),
                      ((0.2, 0.05, 1.4), (-0.4, -0.2, 2.3), 0.15), ((0.1, 0, 1.0), (0.1, -0.5, 2.1), 0.12)):
        k.beam(a, b, t * s, 'walnut')
    for (x, y, z, r) in ((0.6, 0.35, 2.6, 0.75), (-0.45, -0.25, 2.55, 0.7), (0.1, -0.6, 2.35, 0.6), (0.0, 0.2, 2.95, 0.7)):
        k.sph(x, y, z, r * s, 'leaf2', seg=(6, 4), scale=(1.15, 1.15, 0.75))
        k.sph(x + 0.15, y - 0.1, z + 0.2, r * 0.55 * s, 'leaf', seg=(5, 3), scale=(1.1, 1.1, 0.7), ink=False)
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 0.62)
    k.col(-0.2, 0.35, -0.2, 0.25, 0.62, 2.0)
    return k


# ================================================================ the roof garden
def pergola(k):
    """[4, 6] a pergola lounge: four white columns carrying teak beams and battens, vines with bougainvillea; under it
    an outdoor sofa, two armchairs and a coffee table on an outdoor rug"""
    k.begin()
    X, Y = 2.0, 3.0
    k.qz(-1.5, 1.5, -2.2, 2.2, 0.012, 1, 'wine2')
    k.qz(-1.35, 1.35, -2.05, 2.05, 0.015, 1, 'canvas')
    for (x, y) in ((-1.75, -2.75), (1.75, -2.75), (-1.75, 2.75), (1.75, 2.75)):
        k.cyl(x, y, 0, 0.17, 0.17, 0.2, 'stone2', seg=6, ink=False)
        k.cyl(x, y, 0.2, 0.13, 0.11, 2.6, 'ivory', seg=6)
        k.bx(x - 0.17, x + 0.17, y - 0.17, y + 0.17, 2.8, 2.92, 'stone2')
        k.col(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, 2.92)
    for x in (-1.75, 1.75):
        k.bx(x - 0.08, x + 0.08, -3.0, 3.0, 2.92, 3.14, 'teak')
    for i in range(6):
        y = -2.6 + i * 1.04
        k.bx(-2.0, 2.0, y - 0.04, y + 0.04, 3.14, 3.24, 'teak2', ink=False)
    for (x, y, z) in ((-1.75, -2.4, 2.4), (1.75, 2.4, 2.6), (-0.9, 0.6, 3.25), (0.8, -1.3, 3.25)):
        k.sph(x, y, z, 0.5, 'leaf2', seg=(5, 3), scale=(1.4, 1.0, 0.5))
        k.sph(x + 0.2, y + 0.1, z + 0.12, 0.3, 'bougain', seg=(4, 3), scale=(1.4, 1.0, 0.5), ink=False)
    from rv_inside import light_sofa, light_armchair
    light_sofa(k, 0, 1.5, 0, 2.2, 'ivory', 'teak2')
    light_armchair(k, -1.1, -0.9, 135, 'ivory', 'teak2')
    light_armchair(k, 1.1, -0.9, 225, 'ivory', 'teak2')
    k.bx(-0.6, 0.6, -0.25, 0.45, 0.0, 0.4, 'teak')
    flowers(k, 0.3, 0.1, 0.4, 0.5, 'rose')
    for (x, y) in ((-0.6, 1.62), (0.6, 1.62)):
        k.bx(x - 0.22, x + 0.22, y - 0.05, y + 0.12, 0.5, 0.85, 'wine')
    k.col(-1.2, 1.2, 1.05, 1.95, 0, 0.9)
    k.col(-0.6, 0.6, -0.25, 0.45, 0, 0.42)
    for x in (-1.1, 1.1):
        k.col(x - 0.4, x + 0.4, -1.3, -0.5, 0, 0.82)
    return k


def belvedere(k):
    """[5, 5] the belvedere: a round wrought-iron gazebo on a marble floor (eight slim columns, a ribbed dome with a
    finial, scroll brackets), a round table with four chairs inside"""
    k.begin()
    R, n = 2.2, 8
    k.cyl(0, 0, 0, 2.45, 2.45, 0.12, 'marble', seg=16)
    for i in range(n):
        a = i / n * math.pi * 2 + math.pi / 8
        x, y = math.cos(a) * R, math.sin(a) * R
        k.cyl(x, y, 0.12, 0.06, 0.06, 2.6, 'black', seg=6)
        k.col(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0, 2.7)
        k.beam((x, y, 2.3), (x * 0.86, y * 0.86, 2.72), 0.03, 'black', ink=False)
        k.beam((x, y, 2.72), (0, 0, 4.1), 0.06, 'black')
    for z in (2.72,):
        from rv_base import ring as _ring
        _ring(k, R, z, 16, 0.08, 'black')
    k.cyl(0, 0, 2.72, R + 0.06, 0.3, 1.3, 'wine', seg=16, ink=True)
    k.cyl(0, 0, 4.0, 0.3, 0.08, 0.4, 'black', seg=8)
    k.sph(0, 0, 4.48, 0.12, 'gold', seg=(8, 5), ink=False)
    k.cyl(0, 0, 0.12, 0.25, 0.12, 0.7, 'black', seg=8)
    k.cyl(0, 0, 0.82, 0.62, 0.62, 0.04, 'marble', seg=14)
    from rv_inside import rattan_chair
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        rattan_chair(k, math.cos(a) * 1.05, math.sin(a) * 1.05, math.degrees(a) - 90, 'wine')
        k.col(math.cos(a) * 1.05 - 0.3, math.cos(a) * 1.05 + 0.3, math.sin(a) * 1.05 - 0.3, math.sin(a) * 1.05 + 0.3, 0, 0.9)
    k.col(-0.62, 0.62, -0.62, 0.62, 0, 0.86)
    flowers(k, 0, 0, 0.86, 0.5, 'rose')
    return k


def daybed(k):
    """[2, 2] a cushioned daybed with bolsters, its white canopy on four teak posts"""
    k.begin()
    k.bx(-0.95, 0.95, -0.95, 0.95, 0.0, 0.35, 'teak')
    k.bx(-0.84, 0.84, -0.84, 0.84, 0.35, 0.5, 'ivory')
    for x in (-0.55, 0.0, 0.55):
        k.bx(x - 0.24, x + 0.24, 0.5, 0.8, 0.5, 0.82, 'wine' if x else 'tile')
    for (x, y) in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)):
        k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.35, 2.3, 'teak2')
        k.col(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.5, 2.3)
    k.bx(-0.97, 0.97, -0.97, 0.97, 2.3, 2.36, 'teak2', ink=False)
    k.qz(-0.95, 0.95, -0.95, 0.95, 2.363, 1, 'canvas')
    k.qz(-0.95, 0.95, -0.95, 0.95, 2.297, -1, 'canvas')
    k.col(-0.95, 0.95, -0.95, 0.95, 0, 0.5)
    return k


def roof_stair(k):
    """[8, 4] the stair up to the roof garden (rising toward local +X to 4.5 m): stone treads with terracotta nosings,
    a landing at the top, wrought-iron handrails on both sides (the podium walls stand either side)"""
    k.begin()
    X, Y = 4.0, 2.0
    n = 28
    run = 7.0 / n
    rise = DECK / n
    for i in range(n):
        a, top = -X + i * run, (i + 1) * rise
        k.bx(a, a + run, -Y + 0.02, Y - 0.02, 0.0, top, 'stone')
        k.qx(-Y + 0.04, Y - 0.04, top - 0.05, top, a - 0.003, -1, 'terra')
        k.col(a, a + run, -Y, Y, 0, top, True)
    k.bx(X - 1.0, X, -Y + 0.02, Y - 0.02, 0.0, DECK, 'stone')
    k.qz(X - 0.95, X - 0.05, -Y + 0.1, Y - 0.1, DECK + 0.003, 1, 'terra')
    k.col(X - 1.0, X, -Y, Y, 0, DECK, True)
    for s in (-1, 1):
        y = s * (Y - 0.18)
        k.prism([(-X + 0.2, rise + 0.9), (X - 1.0, DECK + 0.9), (X - 1.0, DECK + 0.96), (-X + 0.2, rise + 0.96)], y - 0.03, y + 0.03, 'black')
        for i in range(0, n, 4):
            a = -X + i * run + run / 2
            k.bx(a - 0.015, a + 0.015, y - 0.015, y + 0.015, (i + 1) * rise, (i + 1) * rise + 0.92, 'black', ink=False)
    return k


def roof_tile(k):
    """[2, 2] terracotta tiles (the roof garden's paving), 0.4 m squares with white joints"""
    k.begin()
    for i in range(5):
        for j in range(5):
            x0, y0 = -1.0 + i * 0.4, -1.0 + j * 0.4
            k.qz(x0 + 0.012, x0 + 0.388, y0 + 0.012, y0 + 0.388, 0.06, 1, 'terra' if (i * 3 + j) % 5 else 'emerald2')
    return k


def lawn(k):
    """[2, 2] a patch of clipped lawn with a stone edge (flat, on the roof garden)"""
    k.begin()
    k.qz(-1.0, 1.0, -1.0, 1.0, 0.06, 1, 'stone2')
    k.qz(-0.94, 0.94, -0.94, 0.94, 0.064, 1, 'leaf')
    for (x, y) in ((-0.5, 0.3), (0.4, -0.4), (0.2, 0.6)):
        k.qz(x - 0.2, x + 0.2, y - 0.02, y + 0.02, 0.067, 1, 'leaf2')
    return k


def terrace_tile(k):
    """[2, 2] the pool terrace's travertine slabs with a blue tile inset (floor layer)"""
    k.begin()
    for i in range(2):
        for j in range(2):
            x0, y0 = -1.0 + i, -1.0 + j
            k.qz(x0 + 0.01, x0 + 0.99, y0 + 0.01, y0 + 0.99, 0.009, 1, 'stone' if (i + j) % 2 else 'cream')
    k.poly([(0, -0.12, 0.012), (0.12, 0, 0.012), (0, 0.12, 0.012), (-0.12, 0, 0.012)], 'wine', (0, 0, 1))
    return k


# ================================================================ backdrop boats (low poly, seen far off on the sea)
def yacht(k):
    """a motor yacht at anchor: a white hull with a blue boot stripe, two decks of dark windows, a mast"""
    k.begin()
    k.prism_y([(-9.0, 0.0), (7.0, 0.0), (9.5, 1.6), (9.6, 2.4), (-9.0, 2.4)], -2.2, 2.2, 'ivory')
    k.bx(-6.5, 4.5, -1.8, 1.8, 2.4, 4.0, 'ivory')
    k.bx(-4.5, 2.0, -1.5, 1.5, 4.0, 5.3, 'ivory')
    k.qy(-6.2, 4.2, 2.9, 3.6, -1.803, -1, 'navy2')
    k.qy(-6.2, 4.2, 2.9, 3.6, 1.803, 1, 'navy2')
    k.qy(-4.2, 1.8, 4.35, 4.95, -1.503, -1, 'navy2')
    k.qy(-4.2, 1.8, 4.35, 4.95, 1.503, 1, 'navy2')
    k.qy(-8.8, 6.8, 0.25, 0.6, -2.203, -1, 'wine')
    k.qy(-8.8, 6.8, 0.25, 0.6, 2.203, 1, 'wine')
    k.cyl(-1.5, 0, 5.3, 0.1, 0.06, 3.0, 'ivory', seg=5)
    return k


def sailboat(k):
    """a sailing yacht: a white hull, a tall mast with a mainsail and a jib"""
    k.begin()
    k.prism_y([(-5.0, 0.0), (4.0, 0.0), (5.5, 1.2), (-5.0, 1.2)], -1.3, 1.3, 'ivory')
    k.qy(-4.8, 4.2, 0.15, 0.4, -1.303, -1, 'navy')
    k.qy(-4.8, 4.2, 0.15, 0.4, 1.303, 1, 'navy')
    k.bx(-2.5, 0.2, -0.9, 0.9, 1.2, 1.8, 'ivory')
    k.cyl(0.5, 0, 1.21, 0.08, 0.06, 12.0, 'steel', seg=5)
    k.poly([(0.4, 0.0, 2.0), (-4.2, 0.0, 2.0), (0.4, 0.0, 12.8)], 'canvas', (0, -1, 0))
    k.poly([(0.4, 0.0, 2.0), (0.4, 0.0, 12.8), (-4.2, 0.0, 2.0)], 'canvas', (0, 1, 0))
    k.poly([(0.7, 0.0, 2.2), (0.7, 0.0, 11.5), (5.2, 0.0, 1.4)], 'ivory', (0, -1, 0))
    k.poly([(0.7, 0.0, 2.2), (5.2, 0.0, 1.4), (0.7, 0.0, 11.5)], 'ivory', (0, 1, 0))
    return k
