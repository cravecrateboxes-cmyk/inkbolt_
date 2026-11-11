"""INKBOLT kit-hotel: furniture and landmarks of the lobby, the ballroom floor, the sky deck and penthouse, and the
street outside the lobby (see hotel_base.py for the conventions). Prefab footprints are [x, y] metres round the
origin, the front toward -Y."""
import math

from mathutils import Matrix

from hotel_base import (H, DECK, HKit, srt, txt, disc, vdisc, ring, frame_y, legs4, dining_chair, gold_chair, armchair, sofa,
                        side_table, table_lamp, floor_lamp, flowers, palm, topiary, painting, sconce, rug,
                        coffee_table, books, suitcase)


# ================================================================ lobby
def reception(k):
    """Landmark [6, 4]: the front desk (marble top, walnut front with gilt panels, brass bells and lamps) before a
    walnut backdrop with the crest and three world clocks; staff screens and chairs between them."""
    k.begin()
    # desk (front at y = -1.0)
    k.bx(-2.6, 2.6, -1.0, -0.35, 0, 1.08, 'walnut')
    k.bx(-2.7, 2.7, -1.08, -0.3, 1.08, 1.15, 'marble')
    k.bx(-2.66, 2.66, -1.06, -0.98, 0, 0.12, 'nero', ink=False)
    for i in range(6):
        x = -2.25 + i * 0.9
        k.qy(x - 0.34, x + 0.34, 0.25, 0.92, -1.003, -1, 'walnut2')
        frame_y(k, x - 0.34, x + 0.34, 0.25, 0.92, -1.006, -1, 'gold')
    k.bx(-2.7, 2.7, -1.1, -1.05, 1.0, 1.04, 'gold', ink=False)
    for x in (-1.6, 1.6):
        table_lamp(k, x, -0.7, 1.15, 1.1)
    k.cyl(0.4, -0.75, 1.15, 0.06, 0.04, 0.05, 'gold', seg=8, ink=False)
    k.sph(0.4, -0.75, 1.22, 0.04, 'gold', seg=(5, 3), ink=False)
    k.bx(-0.5, -0.1, -0.85, -0.6, 1.15, 1.17, 'ivory', ink=False)                     # register
    flowers(k, -0.95, -0.72, 1.15, 0.8, 'white')
    # staff side: screens and two chairs
    for x in (-0.9, 0.9):
        k.bx(x - 0.25, x + 0.25, -0.42, -0.38, 1.18, 1.48, 'black')
        k.qy(x - 0.22, x + 0.22, 1.21, 1.45, -0.377, 1, 'screen')
        k.bx(x - 0.03, x + 0.03, -0.415, -0.36, 1.15, 1.2, 'black', ink=False)
    for x in (-0.9, 0.9):
        dining_chair(k, x, 0.35, 0, 'wine')
    # backdrop (y 1.6 .. 1.9): walnut wall, crest, clocks
    k.push(0, -0.16)
    k.bx(-2.8, 2.8, 1.6, 1.95, 0, 3.4, 'walnut')
    k.bx(-2.9, 2.9, 1.55, 1.97, 3.4, 3.6, 'gold')
    k.bx(-2.9, 2.9, 1.55, 1.97, 0, 0.12, 'nero', ink=False)
    for x in (-2.0, 0.0, 2.0):
        k.qy(x - 0.75, x + 0.75, 0.3, 3.2, 1.597, -1, 'walnut2')
    for i, (x, city) in enumerate(((-2.0, 'LONDON'), (0.0, 'NEW YORK'), (2.0, 'TOKYO'))):
        vdisc(k, x, 1.594, 2.35, 0.33, 'gold', n=16)
        vdisc(k, x, 1.591, 2.35, 0.28, 'ivory', n=16)
        a1 = (i * 2.1 + 1.0)
        k.poly([(x - 0.012, 1.588, 2.35), (x + 0.012, 1.588, 2.35), (x + math.cos(a1) * 0.2, 1.588, 2.35 + math.sin(a1) * 0.2)], 'black', (0, -1, 0))
        k.poly([(x - 0.012, 1.585, 2.35), (x + 0.012, 1.585, 2.35), (x, 1.585, 2.58)], 'black', (0, -1, 0))
        txt(k, city, x, 1.594, 1.8, 0.1, 'gold', font='sans', valign='m', maxw=1.2)
    txt(k, 'THE AURELIAN', 0, 1.594, 2.98, 0.2, 'gold', font='serif', valign='m', maxw=3.0)
    k.pop()
    k.col(-2.7, 2.7, -1.1, -0.3, 0, 1.15)
    k.col(-2.8, 2.8, 1.44, 1.79, 0, 3.4)
    return k


def concierge(k):
    """[3, 2] concierge desk: a walnut writing desk with a brass name plate, lamp, maps and a brochure rack."""
    k.begin()
    k.bx(-1.1, 1.1, -0.45, 0.25, 0.72, 0.8, 'walnut')
    k.bx(-1.05, -0.55, -0.4, 0.2, 0, 0.72, 'walnut2')
    k.bx(0.55, 1.05, -0.4, 0.2, 0, 0.72, 'walnut2')
    k.qy(-1.0, -0.6, 0.15, 0.62, -0.403, -1, 'walnut')
    k.qy(0.6, 1.0, 0.15, 0.62, -0.403, -1, 'walnut')
    k.bx(-0.3, 0.3, -0.47, -0.45, 0.6, 0.7, 'brass', ink=False)
    txt(k, 'CONCIERGE', 0, -0.473, 0.65, 0.05, 'black', font='sans', valign='m', maxw=0.52)
    table_lamp(k, 0.7, 0.0, 0.8, 0.9)
    k.qz(-0.5, 0.0, -0.3, 0.05, 0.803, 1, 'canvas')
    k.qz(-0.45, -0.15, -0.25, -0.05, 0.806, 1, 'sky')
    dining_chair(k, 0.0, 0.6, 0, 'emerald')
    # brochure stand
    k.bx(-1.45, -1.25, 0.3, 0.6, 0, 1.3, 'walnut2')
    for i, c in enumerate(('wine', 'sky', 'cgold', 'emerald')):
        z = 0.5 + i * 0.2
        k.qy(-1.43, -1.27, z, z + 0.14, 0.297, -1, c)
    k.col(-1.1, 1.1, -0.45, 0.25, 0, 0.8)
    k.col(-1.45, -1.25, 0.3, 0.6, 0, 1.3)
    return k


def bar(k):
    """Landmark [8, 4]: the lobby bar. A long counter (marble top, walnut front, brass foot rail) facing -Y, the
    bartender's aisle, and a back bar of mirrored, lit shelves with bottles under a gilt cornice."""
    k.begin()
    L = 3.7
    k.bx(-L, L, -1.6, -0.95, 0, 1.08, 'walnut')
    k.bx(-L - 0.08, L + 0.08, -1.7, -0.85, 1.08, 1.15, 'marble')
    k.bx(-L, L, -1.64, -1.6, 0, 0.14, 'nero', ink=False)
    for i in range(8):
        x = -L + 0.46 + i * 0.97
        k.qy(x - 0.38, x + 0.38, 0.22, 0.95, -1.603, -1, 'walnut2')
        k.qy(x - 0.03, x + 0.03, 0.22, 0.95, -1.606, -1, 'gold')
    k.cyl(-L, -1.78, 0.22, 0.03, 0.03, 2 * L, 'brass', seg=6, rot=(0, 90, 0), ink=False)
    for x in (-L + 0.4, 0.0, L - 0.4):
        k.bx(x - 0.02, x + 0.02, -1.8, -1.6, 0.16, 0.22, 'brass', ink=False)
    # on the counter: glasses, a cocktail shaker, a bowl of lemons, a lamp
    for (x, y) in ((-2.6, -1.3), (-2.4, -1.2), (1.2, -1.35), (2.7, -1.25)):
        k.cyl(x, y, 1.15, 0.04, 0.035, 0.12, 'crystal', seg=6, ink=False)
    k.cyl(-0.8, -1.25, 1.15, 0.05, 0.04, 0.22, 'chrome', seg=8)
    disc(k, 0.6, -1.25, 1.153, 0.14, 'brass', n=10)
    for i in range(4):
        k.sph(0.6 + math.cos(i * 1.6) * 0.06, -1.25 + math.sin(i * 1.6) * 0.06, 1.2, 0.045, 'amber', seg=(5, 3), ink=False)
    table_lamp(k, -1.8, -1.2, 1.15, 0.8)
    table_lamp(k, 2.0, -1.2, 1.15, 0.8)
    # back bar (y 1.2 .. 1.9)
    k.bx(-L, L, 1.25, 1.9, 0, 0.95, 'walnut')
    k.bx(-L - 0.05, L + 0.05, 1.2, 1.95, 0.95, 1.0, 'marble')
    k.bx(-L, L, 1.85, 1.95, 1.0, 3.2, 'walnut2')
    k.qy(-L + 0.2, L - 0.2, 1.1, 3.0, 1.847, -1, 'crystal2')
    for z in (1.5, 2.05, 2.6):
        k.bx(-L + 0.2, L - 0.2, 1.6, 1.85, z - 0.03, z, 'crystal', ink=False)
        cols = ('amber', 'emerald', 'wine', 'glassT', 'gold', 'crystal2', 'emerald2', 'amber')
        for i in range(12):
            x = -L + 0.45 + i * 0.6
            c = cols[(i * 3 + int(z * 10)) % len(cols)]
            hh = 0.26 + 0.06 * ((i + int(z * 7)) % 3)
            k.cyl(x, 1.73, z, 0.05, 0.03, hh, c, seg=5, ink=False)
        k.qy(-L + 0.2, L - 0.2, z - 0.06, z - 0.03, 1.597, -1, 'glow')
    k.bx(-L - 0.26, L + 0.26, 1.15, 1.98, 3.2, 3.45, 'gold')
    txt(k, 'THE GILT BAR', 0, 1.147, 3.32, 0.19, 'wine3', font='display', valign='m', maxw=3.0)
    for s in (-1, 1):
        x0, x1 = srt(s * (L + 0.06), s * (L + 0.24))
        k.bx(x0, x1, 1.17, 1.96, 0, 3.2, 'walnut2')
    k.col(-L - 0.08, L + 0.08, -1.8, -0.85, 0, 1.15)
    k.col(-L - 0.24, L + 0.24, 1.17, 1.96, 0, 3.2)
    return k


def stool(k):
    """Bar stool: gilt pedestal and foot ring, a wine velvet seat with a low back."""
    k.begin()
    k.cyl(0, 0, 0, 0.22, 0.22, 0.04, 'brass', seg=10, ink=False)
    k.cyl(0, 0, 0.04, 0.035, 0.035, 0.7, 'gold', seg=6)
    ring(k, 0.18, 0.3, 8, 0.025, 'gold', ink=False)
    k.cyl(0, 0, 0.72, 0.22, 0.2, 0.08, 'wine', seg=10)
    k.bx(-0.16, 0.16, 0.12, 0.18, 0.8, 1.02, 'wine')
    k.col(-0.2, 0.2, -0.2, 0.2, 0, 0.82)
    return k


def lounge(k, v):
    """[4, 3] seating group on a rug: a chesterfield (A) or two facing sofas (B), armchairs, a marble coffee table
    with books and flowers, side tables with lamps."""
    k.begin()
    rug(k, -1.85, 1.85, -1.35, 1.35)
    if v == 'A':
        sofa(k, 0, 0.95, 0, 2.2, 'wine')
        armchair(k, -1.45, -0.55, 115, 'wine')
        armchair(k, 1.45, -0.55, -115, 'wine')
        side_table(k, -1.5, 1.0)
        table_lamp(k, -1.5, 1.0, 0.55)
        side_table(k, 1.5, 1.0)
        flowers(k, 1.5, 1.0, 0.55, 0.8, 'rose')
        coffee_table(k, 0, -0.15, 1.3, 0.7)
        books(k, -0.3, -0.2, 0.42, 3, 12)
        k.col(-1.1, 1.1, 0.53, 1.37, 0, 0.84)
        for s in (-1, 1):
            x0, x1 = srt(s * 1.0, s * 1.9)
            k.col(x0, x1, -1.0, -0.1, 0, 0.82)
            xa, xb = srt(s * 1.25, s * 1.75)
            k.col(xa, xb, 0.75, 1.25, 0, 0.6)
        k.col(-0.65, 0.65, -0.5, 0.2, 0, 0.42)
    else:
        sofa(k, 0, 0.95, 0, 2.0, 'wine')
        sofa(k, 0, -0.95, 180, 2.0, 'wine')
        coffee_table(k, 0, 0, 1.2, 0.6)
        flowers(k, 0.25, 0, 0.42, 0.7, 'white')
        books(k, -0.3, 0.05, 0.42, 2, -8)
        for s in (-1, 1):
            side_table(k, s * 1.5, 0)
            table_lamp(k, s * 1.5, 0, 0.55)
        k.col(-1.0, 1.0, 0.53, 1.37, 0, 0.84)
        k.col(-1.0, 1.0, -1.37, -0.53, 0, 0.84)
        k.col(-0.6, 0.6, -0.3, 0.3, 0, 0.42)
        for s in (-1, 1):
            xa, xb = srt(s * 1.25, s * 1.75)
            k.col(xa, xb, -0.25, 0.25, 0, 0.6)
    return k


def piano(k):
    """[3, 3] black concert grand with the lid up, a bench, sheet music, a candelabra."""
    k.begin()
    body = [(-0.75, -0.9), (0.75, -0.9), (0.75, 0.2), (0.55, 0.85), (0.1, 1.15), (-0.45, 1.25), (-0.75, 1.0)]
    k.prism(body, 0.72, 1.02, 'black')
    for (x, y) in ((-0.62, -0.75), (0.62, -0.75), (-0.3, 1.0)):
        k.cyl(x, y, 0, 0.06, 0.08, 0.72, 'black', seg=6)
        k.cyl(x, y, 0, 0.07, 0.07, 0.04, 'brass', seg=6, ink=False)
    k.bx(-0.72, 0.72, -1.05, -0.9, 0.72, 0.84, 'black')
    for i in range(24):
        x = -0.69 + i * 0.06
        k.bx(x, x + 0.055, -1.05, -0.92, 0.842, 0.86, 'ivory', ink=False)
        if i % 7 not in (2, 6):
            k.bx(x + 0.035, x + 0.07, -1.0, -0.92, 0.86, 0.88, 'black', ink=False)
    k.bx(-0.3, 0.3, -0.9, -0.86, 0.9, 1.12, 'ivory', ink=False)
    k.beam((-0.2, -0.1, 1.02), (-0.2, -0.1, 1.75), 0.03, 'black', ink=False)
    k.m.box((0.25, 0.15, 1.4), (1.1, 1.9, 0.03), 'black', rot=(0, -35, 0), bevel=False)
    k._mark(True)
    k.bx(-0.45, 0.45, -1.65, -1.3, 0.45, 0.52, 'black')
    for x in (-0.38, 0.38):
        k.bx(x - 0.03, x + 0.03, -1.6, -1.35, 0, 0.45, 'black', ink=False)
    k.col(-0.75, 0.75, -1.05, 1.0, 0, 1.05)
    k.col(-0.45, 0.45, -1.65, -1.3, 0, 0.52)
    return k


def flower_table(k):
    """Landmark [3, 3]: the lobby's centre table under the chandelier: a round marble top on a gilt pedestal and
    a towering urn of lilies, roses and trailing greens."""
    k.begin()
    k.cyl(0, 0, 0, 0.7, 0.7, 0.1, 'nero', seg=16)
    k.cyl(0, 0, 0.1, 0.3, 0.45, 0.25, 'gold', seg=12)
    k.cyl(0, 0, 0.35, 0.22, 0.22, 0.4, 'gold', seg=10)
    k.cyl(0, 0, 0.75, 1.2, 1.2, 0.08, 'marble', seg=20)
    k.cyl(0, 0, 0.74, 1.22, 1.22, 0.025, 'gold', seg=20, ink=False, caps=False)
    k.cyl(0, 0, 0.83, 0.3, 0.22, 0.15, 'stone', seg=12)
    k.cyl(0, 0, 0.98, 0.22, 0.42, 0.5, 'crystal2', seg=12)
    k.cyl(0, 0, 1.48, 0.42, 0.44, 0.04, 'gold', seg=12, ink=False)
    k.sph(0, 0, 1.95, 0.75, 'leaf2', seg=(10, 6), scale=(1, 1, 0.75))
    cols = ('ivory', 'blush', 'rose', 'white', 'ivory', 'gold')
    for i in range(18):
        a = i / 18 * math.pi * 2
        for (r, z, sz) in ((0.62, 1.85, 0.11), (0.42, 2.25, 0.1)):
            if i % 2 and r < 0.5:
                continue
            k.sph(math.cos(a) * r, math.sin(a) * r, z + 0.05 * (i % 3), sz, cols[(i + int(r * 10)) % len(cols)], seg=(4, 2), ink=False)
    for i in range(6):
        a = i / 6 * math.pi * 2 + 0.3
        k.beam((math.cos(a) * 0.1, math.sin(a) * 0.1, 2.3), (math.cos(a) * 0.25, math.sin(a) * 0.25, 2.9), 0.03, 'leaf', ink=False)
        k.sph(math.cos(a) * 0.27, math.sin(a) * 0.27, 2.95, 0.08, 'white', seg=(5, 3), ink=False)
    for i in range(8):
        a = i / 8 * math.pi * 2
        k.beam((math.cos(a) * 0.55, math.sin(a) * 0.55, 1.75), (math.cos(a) * 0.95, math.sin(a) * 0.95, 1.05), 0.06, 'leaf', ink=False)
    k.col(-1.0, 1.0, -1.0, 1.0, 0, 1.6)
    return k


def luggage_cart(k):
    """Brass birdcage luggage cart (1 x 1 footprint, 1.3 x 0.7 m) piled with suitcases and a hat box."""
    k.begin()
    k.bx(-0.62, 0.62, -0.32, 0.32, 0.18, 0.24, 'wine')
    k.bx(-0.64, 0.64, -0.34, 0.34, 0.14, 0.18, 'brass', ink=False)
    for (x, y) in ((-0.55, -0.27), (0.55, -0.27), (-0.55, 0.27), (0.55, 0.27)):
        k.cyl(x, y, 0.0, 0.07, 0.07, 0.04, 'black', seg=8, rot=(90, 0, 0), ink=False)
    for s in (-1, 1):
        x = s * 0.6
        k.cyl(x, -0.29, 0.24, 0.02, 0.02, 1.56, 'gold', seg=5, ink=False)
        k.cyl(x, 0.29, 0.24, 0.02, 0.02, 1.56, 'gold', seg=5, ink=False)
    for y in (-0.29, 0.29):        # the birdcage arch over each side
        for i in range(8):
            a0, a1 = math.pi * i / 8, math.pi * (i + 1) / 8
            ro, ri = 0.62, 0.58
            k.prism([(math.cos(a0) * ro, 1.79 + math.sin(a0) * ro * 0.5), (math.cos(a0) * ri, 1.79 + math.sin(a0) * ri * 0.5),
                     (math.cos(a1) * ri, 1.79 + math.sin(a1) * ri * 0.5), (math.cos(a1) * ro, 1.79 + math.sin(a1) * ro * 0.5)], y - 0.02, y + 0.02, 'gold')
    k.beam((0, -0.29, 2.08), (0, 0.29, 2.08), 0.04, 'gold', ink=False)
    suitcase(k, -0.2, 0, 0.24, 0.75, 0.5, 0.22, 'navy')
    suitcase(k, 0.25, 0.02, 0.46, 0.6, 0.45, 0.2, 'wine', 6)
    suitcase(k, -0.38, -0.02, 0.46, 0.42, 0.4, 0.3, 'oak', -8)
    k.cyl(0.25, 0.0, 0.66, 0.16, 0.16, 0.2, 'cream', seg=10)
    k.col(-0.64, 0.64, -0.34, 0.34, 0, 1.0)
    return k


def bell_stand(k):
    """Bellman's podium: a walnut lectern with a brass lamp and a bell."""
    k.begin()
    k.bx(-0.32, 0.32, -0.26, 0.26, 0, 0.12, 'nero')
    k.bx(-0.26, 0.26, -0.2, 0.2, 0.12, 1.0, 'walnut')
    k.qy(-0.18, 0.18, 0.25, 0.9, -0.203, -1, 'walnut2')
    k.m.box((0, -0.02, 1.08), (0.6, 0.48, 0.05), 'walnut', rot=(-14, 0, 0), bevel=False)
    k._mark(True)
    k.cyl(0.16, 0.08, 1.12, 0.05, 0.03, 0.04, 'gold', seg=8, ink=False)
    txt(k, 'BELL CAPTAIN', 0, -0.206, 0.62, 0.035, 'gold', font='sans', valign='m', maxw=0.32)
    k.col(-0.32, 0.32, -0.26, 0.26, 0, 1.12)
    return k


def palm_piece(k):
    k.begin()
    palm(k, 0, 0, 1.0)
    k.col(-0.34, 0.34, -0.34, 0.34, 0, 0.7)
    return k


def topiary_piece(k):
    k.begin()
    topiary(k, 0, 0, 1.0)
    k.col(-0.3, 0.3, -0.3, 0.3, 0, 1.0)
    return k


def ottoman(k):
    """[2, 1] tufted velvet ottoman on gilt feet."""
    k.begin()
    k.bx(-0.85, 0.85, -0.32, 0.32, 0.1, 0.42, 'wine')
    k.bx(-0.86, 0.86, -0.33, 0.33, 0.07, 0.14, 'gold', ink=False)
    for i in range(6):
        for j in range(2):
            x, y = -0.62 + i * 0.25, -0.12 + j * 0.24
            k.qz(x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.423, 1, 'black')
    for (x, y) in ((-0.78, -0.25), (0.78, -0.25), (-0.78, 0.25), (0.78, 0.25)):
        k.cyl(x, y, 0, 0.03, 0.04, 0.1, 'gold', seg=6, ink=False)
    k.col(-0.86, 0.86, -0.33, 0.33, 0, 0.42)
    return k


def console(k):
    """[2, 1] wall console: a gilt table with a marble top, flowers, a pair of lamps and a framed mirror above."""
    k.begin()
    k.bx(-0.85, 0.85, -0.2, 0.25, 0.78, 0.84, 'marble')
    k.bx(-0.8, 0.8, -0.16, 0.22, 0.68, 0.78, 'gold')
    for x in (-0.75, 0.75):
        k.cyl(x, -0.1, 0, 0.03, 0.05, 0.68, 'gold', seg=6, ink=False)
        k.cyl(x, 0.17, 0, 0.03, 0.05, 0.68, 'gold', seg=6, ink=False)
    k.bx(-0.7, 0.7, -0.1, 0.2, 0.15, 0.18, 'gold', ink=False)
    flowers(k, 0, 0.02, 0.84, 1.0, 'white', tall=True)
    table_lamp(k, -0.6, 0.05, 0.84, 1.0)
    table_lamp(k, 0.6, 0.05, 0.84, 1.0)
    k.bx(-0.7, 0.7, 0.4, 0.47, 1.1, 2.6, 'gold')
    k.qy(-0.6, 0.6, 1.2, 2.5, 0.397, -1, 'crystal2')
    k.poly([(-0.4, 0.394, 1.5), (-0.3, 0.394, 1.5), (-0.05, 0.394, 2.2), (-0.15, 0.394, 2.2)], 'glint', (0, -1, 0))
    k.col(-0.85, 0.85, -0.2, 0.25, 0, 0.84)
    return k


def writing_desk(k):
    """[2, 1] writing desk on the mezzanine: walnut with a leather top, a green banker's lamp, stationery, a chair."""
    k.begin()
    k.bx(-0.75, 0.75, -0.1, 0.4, 0.72, 0.78, 'walnut')
    k.qz(-0.6, 0.6, 0.0, 0.32, 0.783, 1, 'emerald2')
    k.bx(-0.7, -0.3, -0.05, 0.35, 0, 0.72, 'walnut2')
    k.bx(0.3, 0.7, -0.05, 0.35, 0, 0.72, 'walnut2')
    k.bx(0.4, 0.5, 0.15, 0.25, 0.78, 0.8, 'brass', ink=False)
    k.cyl(0.45, 0.2, 0.8, 0.012, 0.012, 0.3, 'brass', seg=4, ink=False)
    k.m.box((0.45, 0.15, 1.12), (0.36, 0.14, 0.09), 'emerald', bevel=False)
    k._mark(True)
    k.qz(-0.3, 0.05, 0.05, 0.25, 0.786, 1, 'ivory')
    dining_chair(k, 0, -0.35, 180, 'wine')
    k.col(-0.75, 0.75, -0.1, 0.4, 0, 0.78)
    return k


# ================================================================ ballroom floor
def banquet(k):
    """[3, 3] round banquet table: floor-length ivory cloth, eight gilt chairs, place settings, a tall centrepiece
    of white roses with candles."""
    k.begin()
    R = 0.95
    k.cyl(0, 0, 0, R + 0.04, R, 0.76, 'ivory', seg=16)
    disc(k, 0, 0, 0.763, R * 0.98, 'white', n=16)
    for i in range(6):
        a = i / 6 * math.pi * 2 + math.pi / 6
        ca, sa = math.cos(a), math.sin(a)
        disc(k, ca * 0.7, sa * 0.7, 0.766, 0.13, 'cream', n=8)
        disc(k, ca * 0.7, sa * 0.7, 0.769, 0.09, 'gold', n=6)
        gold_chair(k, ca * 1.3, sa * 1.3, math.degrees(a) - 90)
    k.cyl(0, 0, 0.763, 0.1, 0.06, 0.06, 'gold', seg=8, ink=False)
    k.cyl(0, 0, 0.82, 0.03, 0.03, 0.55, 'crystal2', seg=6)
    k.cyl(0, 0, 1.37, 0.05, 0.14, 0.12, 'crystal2', seg=8)
    k.sph(0, 0, 1.6, 0.3, 'leaf2', seg=(7, 5), scale=(1, 1, 0.8))
    for i in range(9):
        a = i / 9 * math.pi * 2
        k.sph(math.cos(a) * 0.24, math.sin(a) * 0.24, 1.6 + 0.08 * (i % 2), 0.08, ('ivory', 'white', 'blush')[i % 3], seg=(5, 3), ink=False)
    for i in range(3):
        a = i / 3 * math.pi * 2 + 0.5
        x, y = math.cos(a) * 0.3, math.sin(a) * 0.3
        k.cyl(x, y, 0.763, 0.035, 0.035, 0.22, 'ivory', seg=5, ink=False)
        k.cyl(x, y, 0.985, 0.012, 0.0, 0.05, 'amber', seg=4, ink=False)
    k.col(-R, R, -R, R, 0, 0.77)
    k.col(-0.35, 0.35, -0.35, 0.35, 0.77, 1.9)
    return k


def stage(k):
    """Landmark [8, 4]: the bandstand: a low walnut dais (walkable, one step) under a wine velvet drape with a gilt
    valance and the hotel's name, a black grand piano, music stands, a microphone and two potted palms."""
    k.begin()
    Hs = 0.34
    k.bx(-3.9, 3.9, -1.9, 1.6, 0, Hs, 'walnut')
    k.qz(-3.85, 3.85, -1.85, 1.55, Hs + 0.003, 1, 'oak')
    for i in range(1, 15):
        x = -3.85 + i * 0.513
        k.qz(x - 0.006, x + 0.006, -1.85, 1.55, Hs + 0.006, 1, 'teak2')
    k.bx(-3.9, 3.9, -1.93, -1.9, 0.05, Hs - 0.04, 'gold', ink=False)
    k.col(-3.9, 3.9, -1.9, 1.6, 0, Hs, True)
    # drape backdrop
    k.bx(-3.95, 3.95, 1.6, 1.88, 0, 5.6, 'wine')
    for i in range(16):
        x = -3.8 + i * 0.5
        k.qy(x, x + 0.18, 0.4, 5.1, 1.597, -1, 'wine2')
    k.bx(-4.0, 4.0, 1.3, 1.86, 5.1, 5.9, 'gold')
    for i in range(8):
        x = -3.5 + i * 1.0
        k.poly([(x - 0.45, 1.297, 5.1), (x + 0.45, 1.297, 5.1), (x, 1.297, 4.75)], 'gold', (0, -1, 0))
    txt(k, 'THE AURELIAN', 0, 1.294, 5.5, 0.4, 'wine3', font='display', valign='m', maxw=5.0)
    for s in (-1, 1):
        x0, x1 = srt(s * 3.95, s * 3.3)
        k.bx(x0, x1, 1.0, 1.596, 0, 5.1, 'wine')
        k.bx(min(s * 3.6, s * 3.7), max(s * 3.6, s * 3.7), 0.95, 1.65, 1.6, 1.7, 'gold', ink=False)
    k.col(-3.95, 3.95, 1.6, 1.88, 0, 5.6)
    for s in (-1, 1):
        x0, x1 = srt(s * 3.95, s * 3.3)
        k.col(x0, x1, 1.0, 1.6, 0, 5.1)
    # grand piano (small) and music stands
    k.push(-1.8, 0.4, 20, Hs)
    k.prism([(-0.6, -0.7), (0.6, -0.7), (0.6, 0.15), (0.4, 0.7), (-0.35, 1.0), (-0.6, 0.8)], 0.7, 0.98, 'black')
    for (x, y) in ((-0.5, -0.6), (0.5, -0.6), (-0.25, 0.8)):
        k.cyl(x, y, 0, 0.05, 0.07, 0.7, 'black', seg=6)
    k.bx(-0.58, 0.58, -0.82, -0.7, 0.7, 0.8, 'black')
    k.qz(-0.55, 0.55, -0.82, -0.72, 0.803, 1, 'ivory')
    k.m.box((0.2, 0.1, 1.3), (0.9, 1.5, 0.03), 'black', rot=(0, -35, 0), bevel=False)
    k._mark(True)
    k.col(-0.6, 0.6, -0.82, 0.9, 0, 0.98)
    k.pop()
    for (x, y) in ((0.4, 0.2), (1.2, 0.5), (2.0, 0.1)):
        k.cyl(x, y, Hs, 0.12, 0.12, 0.02, 'black', seg=6, ink=False)
        k.cyl(x, y, Hs + 0.02, 0.012, 0.012, 1.0, 'black', seg=4, ink=False)
        k.m.box((x, y - 0.02, Hs + 1.12), (0.42, 0.02, 0.3), 'black', rot=(-15, 0, 0), bevel=False)
        k._mark(False)
    k.cyl(0.0, -1.2, Hs, 0.14, 0.14, 0.02, 'chrome', seg=8, ink=False)
    k.cyl(0.0, -1.2, Hs + 0.02, 0.012, 0.012, 1.4, 'chrome', seg=4, ink=False)
    k.sph(0.0, -1.2, Hs + 1.47, 0.045, 'black', seg=(5, 3))
    for s in (-1, 1):
        k.push(s * 3.4, -1.3, 0, Hs)
        topiary(k, 0, 0, 0.9)
        k.col(-0.27, 0.27, -0.27, 0.27, 0, 0.9)
        k.pop()
    return k


def easel(k):
    """Event easel: a gilt easel with a framed card announcing tonight's ball."""
    k.begin()
    for x in (-0.3, 0.3):
        k.beam((x, -0.15, 0), (x * 0.4, 0.0, 1.85), 0.04, 'gold')
    k.beam((0, 0.45, 0), (0, 0.0, 1.7), 0.035, 'gold', ink=False)
    k.bx(-0.4, 0.4, -0.18, -0.1, 0.9, 0.94, 'gold', ink=False)
    k.m.box((0, -0.12, 1.4), (0.66, 0.03, 0.9), 'gold', rot=(-8, 0, 0), bevel=False)
    k._mark(True)
    k.m.box((0, -0.135, 1.4), (0.56, 0.01, 0.8), 'ivory', rot=(-8, 0, 0), bevel=False)
    k._mark(False)
    k.stack.append(k.m.parent)
    k.m.parent = k.m.parent @ Matrix.Translation((0, -0.135, 1.4)) @ Matrix.Rotation(math.radians(-8), 4, 'X')
    txt(k, 'THE AURELIAN', 0, -0.008, 0.18, 0.06, 'cgold', font='display', valign='m', maxw=0.46)
    txt(k, 'GRAND BALL', 0, -0.008, 0.0, 0.1, 'wine3', font='display', valign='m', maxw=0.46)
    txt(k, 'TONIGHT', 0, -0.008, -0.17, 0.05, 'black', font='display', valign='m', maxw=0.46)
    k.m.parent = k.stack.pop()
    k.col(-0.32, 0.32, -0.2, 0.2, 0, 1.0)
    return k


def hk_cart(k):
    """[2, 1] housekeeping cart: three shelves of folded towels and linen, toiletry caddy, a wine laundry bag and
    a black bin bag, push handle."""
    k.begin()
    W = 0.8
    k.bx(-W, W, -0.3, 0.3, 0.12, 0.16, 'steel')
    for z in (0.16, 0.56, 0.96):
        k.bx(-0.37, 0.72, -0.28, 0.28, z, z + 0.03, 'steel', ink=False)
    for (x, y) in ((-0.4, -0.27), (0.72, -0.27), (-0.4, 0.24), (0.72, 0.24)):
        k.bx(x, x + 0.03, y, y + 0.03, 0.16, 1.32, 'steel2', ink=False)
    k.bx(-0.4, 0.75, -0.28, 0.28, 1.32, 1.36, 'steel')
    for z in (0.19, 0.59, 0.99):
        for i in range(3):
            x = -0.34 + i * 0.35
            for j in range(3):
                k.bx(x, x + 0.31, -0.22, 0.22, z + j * 0.08, z + j * 0.08 + 0.075, ('white', 'ivory', 'cream')[(i + j) % 3], ink=(j == 2))
    k.bx(-W + 0.45, -W + 0.85, -0.2, 0.2, 1.36, 1.5, 'navy')
    for i in range(4):
        k.cyl(-W + 0.5 + i * 0.09, 0.0, 1.5, 0.025, 0.025, 0.12, ('ivory', 'amber', 'teal2', 'ivory')[i], seg=5, ink=False)
    k.bx(-W, -W + 0.38, -0.27, 0.27, 0.2, 1.1, 'wine')
    k.bx(-W - 0.02, -W + 0.4, -0.29, 0.29, 1.1, 1.14, 'steel2', ink=False)
    for (x, y) in ((-W + 0.1, -0.2), (W - 0.1, -0.2), (-W + 0.1, 0.2), (W - 0.1, 0.2)):
        k.cyl(x, y, 0.0, 0.06, 0.06, 0.03, 'black', seg=6, rot=(90, 0, 0), ink=False)
    k.col(-W, W, -0.3, 0.3, 0, 1.36)
    return k


def rs_trolley(k):
    """[2, 1] room-service trolley: a white cloth to the floor, silver cloches, a champagne bucket, a rose."""
    k.begin()
    k.bx(-0.75, 0.75, -0.32, 0.32, 0.08, 0.76, 'white')
    k.bx(-0.77, 0.77, -0.34, 0.34, 0.76, 0.79, 'ivory')
    for (x, y) in ((-0.65, -0.24), (0.65, -0.24), (-0.65, 0.24), (0.65, 0.24)):
        k.cyl(x, y, 0.0, 0.04, 0.04, 0.08, 'chrome', seg=6, ink=False)
    for (x, r) in ((-0.38, 0.16), (0.05, 0.13)):
        k.sph(x, 0, 0.79, r, 'chrome', seg=(8, 4), scale=(1, 1, 0.7))
        k.sph(x, 0, 0.79 + r * 0.72, 0.025, 'chrome', seg=(4, 2), ink=False)
    k.cyl(0.48, 0.05, 0.79, 0.1, 0.12, 0.2, 'chrome', seg=8)
    k.cyl(0.48, 0.05, 0.9, 0.035, 0.035, 0.28, 'emerald2', seg=6, ink=False)
    k.cyl(0.42, -0.2, 0.79, 0.025, 0.02, 0.18, 'crystal', seg=5, ink=False)
    k.sph(0.42, -0.2, 1.0, 0.035, 'rose', seg=(4, 2), ink=False)
    k.bx(0.77, 0.8, -0.28, 0.28, 0.85, 0.89, 'chrome', ink=False)
    k.col(-0.77, 0.77, -0.34, 0.34, 0, 0.9)
    return k


# ================================================================ sky deck and penthouse
def pool(k):
    """Landmark [10, 4]: the sky-deck infinity pool: marble coping, a glass-tile edge, the water with ripples and
    a vanishing edge on the long side, chrome ladders, underwater lights."""
    k.begin()
    X, Y, Hc = 5.0, 2.0, 0.45
    k.bx(-X, X, -Y, -Y + 0.3, 0, Hc, 'marble')
    k.bx(-X, X, Y - 0.3, Y, 0, Hc, 'marble')
    k.bx(-X, -X + 0.3, -Y + 0.3, Y - 0.3, 0, Hc, 'marble')
    k.bx(X - 0.3, X, -Y + 0.3, Y - 0.3, 0, Hc, 'marble')
    k.bx(-X + 0.3, X - 0.3, -Y + 0.3, Y - 0.3, 0, Hc - 0.12, 'tile', ink=False)
    k.qz(-X + 0.3, X - 0.3, -Y + 0.3, Y - 0.3, Hc - 0.07, 1, 'water')
    for (x, y, w) in ((-3.5, -0.8, 1.2), (-1.2, 0.6, 1.6), (1.5, -0.4, 1.1), (3.4, 0.9, 0.9), (0.2, -1.2, 0.8), (-2.6, 1.1, 0.7)):
        k.qz(x - w / 2, x + w / 2, y - 0.03, y + 0.03, Hc - 0.067, 1, 'waterL')
    k.qy(-X + 0.3, X - 0.3, 0.02, Hc - 0.02, -Y - 0.003, -1, 'tile')
    k.qy(-X + 0.3, X - 0.3, 0.12, 0.18, -Y - 0.006, -1, 'nero2')
    for s in (-1, 1):
        x = s * 3.6
        for yy in (-Y + 0.32, -Y + 0.62):
            k.cyl(x - 0.25, yy, Hc - 0.1, 0.02, 0.02, 0.85, 'chrome', seg=5, ink=False)
            k.cyl(x + 0.25, yy, Hc - 0.1, 0.02, 0.02, 0.85, 'chrome', seg=5, ink=False)
        k.beam((x - 0.25, -Y + 0.32, Hc + 0.75), (x - 0.25, -Y + 0.62, Hc + 0.75), 0.03, 'chrome', ink=False)
        k.beam((x + 0.25, -Y + 0.32, Hc + 0.75), (x + 0.25, -Y + 0.62, Hc + 0.75), 0.03, 'chrome', ink=False)
    k.col(-X, X, -Y, Y, 0, Hc)
    return k


def lounger(k):
    """[1, 2] teak sun lounger with a white cushion, a raised back and a rolled navy towel."""
    k.begin()
    k.bx(-0.36, 0.36, -0.95, 0.95, 0.22, 0.3, 'teak')
    for (x, y) in ((-0.3, -0.85), (0.3, -0.85), (-0.3, 0.85), (0.3, 0.85)):
        k.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0, 0.22, 'teak2', ink=False)
    k.bx(-0.33, 0.33, -0.92, 0.3, 0.3, 0.38, 'white')
    k.m.box((0, 0.6, 0.55), (0.62, 0.75, 0.08), 'white', rot=(40, 0, 0), bevel=False)
    k._mark(True)
    k.m.box((0, 0.66, 0.5), (0.68, 0.75, 0.05), 'teak', rot=(40, 0, 0), bevel=False)
    k._mark(False)
    k.cyl(-0.22, -0.65, 0.46, 0.08, 0.08, 0.44, 'navy', seg=8, rot=(0, 90, 0))
    k.col(-0.36, 0.36, -0.95, 0.95, 0, 0.5)
    return k


def umbrella(k):
    """Market parasol (navy and cream gores) on a weighted bronze base."""
    k.begin()
    k.cyl(0, 0, 0, 0.28, 0.28, 0.1, 'bronze', seg=10)
    k.cyl(0, 0, 0.1, 0.03, 0.03, 2.5, 'teak', seg=6)
    n = 8
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        c = 'navy' if i % 2 else 'cream'
        k.poly([(0, 0, 2.7), (math.cos(a0) * 1.4, math.sin(a0) * 1.4, 2.25), (math.cos(a1) * 1.4, math.sin(a1) * 1.4, 2.25)], c, (0, 0, 1))
        k.poly([(0, 0, 2.69), (math.cos(a1) * 1.4, math.sin(a1) * 1.4, 2.24), (math.cos(a0) * 1.4, math.sin(a0) * 1.4, 2.24)], c, (0, 0, -1))
    k.cyl(0, 0, 2.68, 0.06, 0.02, 0.15, 'brass', seg=6, ink=False)
    k.col(-0.28, 0.28, -0.28, 0.28, 0, 1.8)
    return k


def cabana(k):
    """[3, 3] white cabana: four teak posts, a canopy, tied-back drapes, a cushioned daybed with bolsters."""
    k.begin()
    E = 1.35
    for (x, y) in ((-E, -E), (E, -E), (-E, E), (E, E)):
        k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 2.6, 'teak')
    k.bx(-E - 0.1, E + 0.1, -E - 0.1, E + 0.1, 2.6, 2.75, 'teak2')
    k.bx(-E, E, -E, E, 2.75, 2.85, 'ivory')
    for s in (-1, 1):
        x0, x1 = srt(s * E, s * (E - 0.3))
        k.bx(x0, x1, -E - 0.03, -E + 0.05, 0.3, 2.58, 'ivory')
        k.bx(x0, x1, E - 0.05, E + 0.03, 0.0, 2.58, 'ivory')
        k.bx(x0 - 0.01, x1 + 0.01, -E - 0.05, -E + 0.07, 1.2, 1.28, 'gold', ink=False)
    k.bx(-E + 0.3, E - 0.3, E - 0.05, E, 0.0, 2.58, 'cream')
    k.bx(-1.15, 1.15, -1.0, 1.15, 0, 0.42, 'teak')
    k.bx(-1.1, 1.1, -0.95, 1.1, 0.42, 0.55, 'white')
    for x in (-0.6, 0.6):
        k.cyl(x - 0.35, 0.95, 0.65, 0.12, 0.12, 0.7, 'navy', seg=8, rot=(0, 90, 0))
    k.bx(-0.3, 0.3, -0.3, 0.1, 0.55, 0.6, 'navy', ink=False)
    k.col(-1.15, 1.15, -1.0, 1.15, 0, 0.55)
    for (x, y) in ((-E, -E), (E, -E)):
        k.col(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0, 2.6)
    k.col(-E - 0.03, E + 0.03, E - 0.05, E + 0.03, 0, 2.6)
    return k


def sky_bar(k):
    """Landmark [7, 7]: the round sky bar: a ring counter with a glowing onyx front and a brass top, a central
    back-bar drum of lit bottle shelves, and a gilt crown ring hung over it with pendant lights."""
    k.begin()
    Ro, Ri, n = 2.9, 2.35, 14
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        if abs(math.sin((a0 + a1) / 2) + 1.0) < 0.1:
            continue      # the bartenders' gap at the south
        pts = [(math.cos(a0) * Ri, math.sin(a0) * Ri), (math.cos(a1) * Ri, math.sin(a1) * Ri), (math.cos(a1) * Ro, math.sin(a1) * Ro), (math.cos(a0) * Ro, math.sin(a0) * Ro)]
        k.prism(pts, 0, 1.05, 'walnut')
        k.prism([(math.cos(a0) * (Ri - 0.06), math.sin(a0) * (Ri - 0.06)), (math.cos(a1) * (Ri - 0.06), math.sin(a1) * (Ri - 0.06)), (math.cos(a1) * (Ro + 0.08), math.sin(a1) * (Ro + 0.08)), (math.cos(a0) * (Ro + 0.08), math.sin(a0) * (Ro + 0.08))], 1.05, 1.12, 'marble')
        am = (a0 + a1) / 2
        nx, ny = math.cos(am), math.sin(am)
        tx, ty = -ny, nx
        L = Ro * math.sin(math.pi / n) * 0.85
        r = Ro * math.cos(math.pi / n) + 0.004
        k.poly([(nx * r - tx * L, ny * r - ty * L, 0.15), (nx * r + tx * L, ny * r + ty * L, 0.15), (nx * r + tx * L, ny * r + ty * L, 0.95), (nx * r - tx * L, ny * r - ty * L, 0.95)], 'lamp', (nx, ny, 0))
    for i in range(8):
        a0, a1 = i / 8 * math.pi * 2, (i + 1) / 8 * math.pi * 2
        k.prism([(math.cos(a0) * 0.9, math.sin(a0) * 0.9), (math.cos(a1) * 0.9, math.sin(a1) * 0.9), (math.cos(a1) * 0.5, math.sin(a1) * 0.5), (math.cos(a0) * 0.5, math.sin(a0) * 0.5)], 0, 2.6, 'walnut2')
    for z in (1.1, 1.6, 2.1):
        k.cyl(0, 0, z - 0.03, 1.05, 1.05, 0.03, 'crystal', seg=12, ink=False)
        cols = ('amber', 'emerald', 'wine', 'glassT', 'gold', 'crystal2')
        for i in range(7):
            a = i / 7 * math.pi * 2
            c = cols[(i + int(z * 10)) % len(cols)]
            k.cyl(math.cos(a) * 0.98, math.sin(a) * 0.98, z, 0.04, 0.04, 0.26, c, seg=5, ink=False)
    k.cyl(0, 0, 2.6, 1.15, 1.15, 0.15, 'gold', seg=14)
    ring(k, 2.7, 4.3, 16, 0.12, 'gold')
    for i in range(8):
        a = i / 8 * math.pi * 2
        x, y = math.cos(a) * 2.7, math.sin(a) * 2.7
        k.beam((x, y, 4.3), (x, y, 3.6), 0.012, 'black', ink=False)
        k.sph(x, y, 3.5, 0.13, 'glow', seg=(5, 3))
        k.beam((x, y, 4.3), (x * 0.35, y * 0.35, 8.95), 0.02, 'black', ink=False)
    k.col(-Ro, Ro, 0.6, Ro, 0, 1.12)
    k.col(-Ro, -0.6, -Ro, 0.6, 0, 1.12)
    k.col(0.6, Ro, -Ro, 0.6, 0, 1.12)
    k.col(-1.15, 1.15, -1.15, 1.15, 0, 2.75)
    return k


def fire_table(k):
    """[2, 2] low stone fire table with a glowing ember strip and a glass screen."""
    k.begin()
    k.bx(-0.8, 0.8, -0.8, 0.8, 0, 0.42, 'stone2')
    k.bx(-0.85, 0.85, -0.85, 0.85, 0.42, 0.47, 'nero')
    k.qz(-0.5, 0.5, -0.12, 0.12, 0.473, 1, 'black')
    for i in range(6):
        x = -0.42 + i * 0.17
        k.cyl(x, 0, 0.47, 0.06, 0.0, 0.22 + 0.08 * (i % 2), 'fire', seg=5, ink=False)
        k.cyl(x + 0.05, 0.03, 0.476, 0.035, 0.0, 0.14, 'amber', seg=4, ink=False)
    k.col(-0.85, 0.85, -0.85, 0.85, 0, 0.47)
    return k


def olive(k):
    """[2, 2] square stone planter with a gnarled olive tree."""
    k.begin()
    k.bx(-0.8, 0.8, -0.8, 0.8, 0, 0.7, 'stone')
    k.bx(-0.84, 0.84, -0.84, 0.84, 0.7, 0.76, 'stone2')
    k.qz(-0.72, 0.72, -0.72, 0.72, 0.763, 1, 'soil')
    for i in range(4):
        a = i * 1.6 + 0.3
        k.beam((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.76), (math.cos(a) * 0.35, math.sin(a) * 0.35, 1.9), 0.09, 'walnut2')
    for (x, y, z, r) in ((0, 0, 2.4, 0.75), (0.45, 0.2, 2.1, 0.5), (-0.4, -0.3, 2.15, 0.5), (0.1, -0.45, 2.6, 0.45)):
        k.sph(x, y, z, r, 'leaf' if r > 0.6 else 'emerald', seg=(7, 5), scale=(1, 1, 0.7))
    k.col(-0.84, 0.84, -0.84, 0.84, 0, 0.76)
    return k


def hedge(k):
    """1 m run of a long bronze planter with clipped boxwood."""
    k.begin()
    k.bx(-0.5, 0.5, -0.32, 0.32, 0, 0.55, 'bronze')
    k.bx(-0.5, 0.5, -0.34, 0.34, 0.55, 0.6, 'brass', ink=False)
    k.bx(-0.48, 0.48, -0.28, 0.28, 0.6, 1.05, 'leaf2')
    for i in range(3):
        k.sph(-0.32 + i * 0.32, 0.0, 1.03, 0.2, 'leaf', seg=(6, 3), scale=(1, 1.3, 0.5), ink=False)
    k.col(-0.5, 0.5, -0.34, 0.34, 0, 1.05)
    return k


def pent_living(k):
    """[5, 4] penthouse living room: a deep L-shaped sofa in ivory with navy cushions, a long marble coffee table,
    a sheepskin rug, armchair, floor lamp, side table."""
    k.begin()
    rug(k, -2.3, 2.3, -1.8, 1.8, field='cream', border='silk2', inner='navy')
    sofa(k, -0.2, 1.25, 0, 3.4, 'ivory', tufts=False)
    sofa(k, 2.0, -0.3, -90, 2.2, 'ivory', tufts=False)
    for x in (-1.3, -0.4, 0.6):
        k.m.box((x, 1.12, 0.7), (0.4, 0.14, 0.38), 'navy', rot=(-12, 0, 8), bevel=False)
        k._mark(False)
    armchair(k, -1.6, -1.1, 125, 'navy')
    coffee_table(k, 0.0, 0.0, 1.8, 0.8, 0.38)
    books(k, -0.4, 0.05, 0.38, 3, 20)
    flowers(k, 0.4, 0.0, 0.38, 0.8, 'gold')
    floor_lamp(k, -2.15, 1.5)
    side_table(k, 2.1, 1.3)
    table_lamp(k, 2.1, 1.3, 0.55)
    k.col(-1.9, 1.5, 0.83, 1.67, 0, 0.84)
    k.col(1.58, 2.42, -1.4, 0.8, 0, 0.84)
    k.col(-2.05, -1.15, -1.55, -0.65, 0, 0.82)
    k.col(-0.9, 0.9, -0.4, 0.4, 0, 0.38)
    return k


def pent_dining(k):
    """[5, 3] dining for ten: a long walnut table with a runner, silver candelabra, place settings, upholstered chairs."""
    k.begin()
    k.bx(-1.9, 1.9, -0.55, 0.55, 0.72, 0.78, 'walnut')
    legs4(k, -1.8, 1.8, -0.45, 0.45, 0.72, 'walnut2', 0.08)
    k.qz(-1.8, 1.8, -0.18, 0.18, 0.783, 1, 'wine')
    for x in (-0.9, 0.9):
        k.cyl(x, 0, 0.78, 0.08, 0.08, 0.04, 'chrome', seg=8, ink=False)
        k.cyl(x, 0, 0.82, 0.02, 0.02, 0.35, 'chrome', seg=5, ink=False)
        for dx in (-0.14, 0.0, 0.14):
            k.cyl(x + dx, 0, 1.17 if dx == 0 else 1.1, 0.02, 0.02, 0.16, 'ivory', seg=4, ink=False)
        k.beam((x - 0.14, 0, 1.1), (x + 0.14, 0, 1.1), 0.02, 'chrome', ink=False)
    flowers(k, 0, 0, 0.78, 0.8, 'red')
    for i in range(3):
        x = -1.2 + i * 1.2
        for s in (-1, 1):
            disc(k, x, s * 0.36, 0.785, 0.12, 'white', n=8)
            dining_chair(k, x, s * 0.85, 0 if s > 0 else 180, 'emerald')
    for s in (-1, 1):
        dining_chair(k, s * 2.25, 0, -90 * s, 'emerald')
    k.col(-1.9, 1.9, -0.55, 0.55, 0, 0.78)
    for s in (-1, 1):
        y0, y1 = srt(s * 0.6, s * 1.12)
        k.col(-1.65, 1.65, y0, y1, 0, 1.0)
        x0, x1 = srt(s * 2.0, s * 2.5)
        k.col(x0, x1, -0.25, 0.25, 0, 1.0)
    return k


def pent_bed(k):
    """[4, 4] four-poster king bed: walnut posts and canopy frame with drapes, an upholstered headboard, crisp linen,
    a throw and cushions; nightstands with lamps; a bench at the foot."""
    k.begin()
    BW, BY0, BY1 = 1.0, -1.1, 1.3
    k.bx(-BW, BW, BY0, BY1, 0.15, 0.42, 'walnut')
    k.bx(-BW + 0.03, BW - 0.03, BY0 + 0.03, BY1 - 0.05, 0.42, 0.62, 'white')
    k.bx(-BW + 0.02, BW - 0.02, BY0 + 0.02, 0.1, 0.62, 0.66, 'navy')
    for x in (-0.5, 0.5):
        k.m.box((x, 1.05, 0.8), (0.7, 0.2, 0.36), 'ivory', rot=(-18, 0, 0), bevel=False)
        k._mark(True)
    k.m.box((0, 0.9, 0.78), (0.5, 0.14, 0.3), 'wine', rot=(-15, 0, 0), bevel=False)
    k._mark(True)
    k.bx(-BW - 0.05, BW + 0.05, BY1, BY1 + 0.12, 0.15, 1.6, 'silk2')
    for i in range(4):
        x = -0.75 + i * 0.5
        k.qy(x - 0.01, x + 0.01, 0.5, 1.5, BY1 - 0.003, -1, 'gold')
    px, py0, py1 = BW + 0.08, BY0 - 0.08, BY1 + 0.16
    for (x, y) in ((-px, py0), (px, py0), (-px, py1), (px, py1)):
        k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 2.6, 'walnut2')
    for y in (py0, py1):
        k.bx(-px - 0.06, px + 0.06, y - 0.06, y + 0.06, 2.6, 2.75, 'walnut2')
    for x in (-px, px):
        k.bx(x - 0.06, x + 0.06, py0 + 0.06, py1 - 0.06, 2.6, 2.75, 'walnut2')
    for t in (-1, 1):
        x0, x1 = srt(t * (px - 0.06), t * (px - 0.2))
        k.bx(x0, x1, BY1 - 0.35, BY1 - 0.05, 0.7, 2.6, 'wine')
        k.bx(x0, x1, BY0, BY0 + 0.25, 0.7, 2.6, 'wine')
    for s in (-1, 1):
        x = s * 1.5
        k.bx(x - 0.3, x + 0.3, 0.75, 1.3, 0, 0.55, 'walnut')
        k.qy(x - 0.25, x + 0.25, 0.3, 0.45, 0.747, -1, 'gold')
        table_lamp(k, x, 1.02, 0.55, 0.9)
    k.bx(-0.75, 0.75, -1.65, -1.3, 0.1, 0.45, 'wine')
    for x in (-0.7, 0.7):
        k.cyl(x, -1.48, 0, 0.03, 0.04, 0.1, 'gold', seg=6, ink=False)
    k.col(-BW - 0.14, BW + 0.14, BY0 - 0.14, BY1 + 0.22, 0, 0.66)
    k.col(-BW - 0.05, BW + 0.05, BY1, BY1 + 0.12, 0, 1.6)
    for (x, y) in ((-px, py0), (px, py0), (-px, py1), (px, py1)):
        k.col(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.66, 2.6)
    for s in (-1, 1):
        x0, x1 = srt(s * 1.2, s * 1.8)
        k.col(x0, x1, 0.75, 1.3, 0, 0.55)
    k.col(-0.75, 0.75, -1.65, -1.3, 0, 0.45)
    return k


def telescope(k):
    """Brass telescope on a walnut tripod, aimed out over the city."""
    k.begin()
    for i in range(3):
        a = i / 3 * math.pi * 2 + 0.3
        k.beam((math.cos(a) * 0.35, math.sin(a) * 0.35, 0), (0, 0, 1.15), 0.04, 'walnut')
    k.cyl(0, 0, 1.1, 0.06, 0.06, 0.1, 'brass', seg=8)
    k.m.cyl((0, -0.1, 1.25), 0.06, 0.09, 0.9, 'brass', seg=10, rot=(-70, 0, 0), bevel=False)
    k._mark(True)
    k.col(-0.25, 0.25, -0.25, 0.25, 0, 1.2)
    return k


def fireplace(k):
    """[3, 1] wall fireplace (orient: wall): a carved white-marble surround with a glowing fire, brass fender, a
    gilt overmantel mirror and candlesticks."""
    k.begin()
    y0 = 0.5
    k.bx(-1.4, 1.4, -0.1, y0, 0, 0.12, 'nero')
    k.bx(-1.3, -0.75, -0.2, y0, 0.12, 1.15, 'marble')
    k.bx(0.75, 1.3, -0.2, y0, 0.12, 1.15, 'marble')
    k.bx(-1.4, 1.4, -0.3, y0, 1.15, 1.32, 'marble')
    k.bx(-0.75, 0.75, -0.05, y0, 0.95, 1.15, 'marble')
    k.bx(-0.75, 0.75, 0.2, y0, 0.12, 0.95, 'black')
    for i in range(5):
        x = -0.45 + i * 0.22
        k.cyl(x, 0.2, 0.15, 0.09, 0.0, 0.35 + 0.12 * (i % 2), 'fire', seg=5, ink=False)
        k.cyl(x + 0.06, 0.15, 0.156, 0.05, 0.0, 0.2, 'amber', seg=4, ink=False)
    k.cyl(-0.4, 0.25, 0.12, 0.06, 0.06, 0.7, 'walnut2', seg=6, rot=(0, 90, 0), ink=False)
    k.bx(-0.8, 0.8, -0.38, -0.32, 0.12, 0.25, 'brass', ink=False)
    for x in (-1.0, 1.0):
        k.cyl(x, -0.1, 1.32, 0.05, 0.04, 0.3, 'gold', seg=6, ink=False)
        k.cyl(x, -0.1, 1.62, 0.015, 0.015, 0.12, 'ivory', seg=4, ink=False)
    k.bx(-0.95, 0.95, 0.38, y0, 1.5, 3.2, 'gold')
    k.qy(-0.82, 0.82, 1.62, 3.08, 0.377, -1, 'crystal2')
    k.poly([(-0.5, 0.374, 1.9), (-0.4, 0.374, 1.9), (-0.1, 0.374, 2.7), (-0.2, 0.374, 2.7)], 'glint', (0, -1, 0))
    k.col(-1.4, 1.4, -0.3, y0, 0, 1.32)
    return k


# ================================================================ street (outside the lobby, in the backdrop)
def street_canopy(k):
    """The hotel's entrance canopy over the sidewalk: a bronze marquee with the name in gilt letters on its fascia,
    brass posts, a red carpet to the kerb, two potted bay trees."""
    k.begin()
    W, D = 4.0, 6.0
    k.qz(-1.2, 1.2, -D, 0, 0.17, 1, 'wine')
    k.bx(-W, W, -D, 0, 3.6, 3.9, 'bronze')
    k.qz(-W + 0.2, W - 0.2, -D + 0.2, -0.2, 3.597, -1, 'glow')
    k.bx(-W, W, -D - 0.05, -D + 0.05, 3.9, 4.6, 'nero')
    txt(k, 'THE AURELIAN', 0, -D - 0.053, 4.25, 0.42, 'gold', font='serif', valign='m', maxw=7.4)
    for s in (-1, 1):
        k.bx(s * W - 0.05, s * W + 0.05, -D + 0.05, 0, 3.9, 4.6, 'nero')
        k.cyl(s * (W - 0.3), -D + 0.3, 0.15, 0.06, 0.06, 3.45, 'brass', seg=8)
        k.cyl(s * 1.6, -D + 0.6, 0.15, 0.3, 0.25, 0.6, 'nero', seg=10)
        k.sph(s * 1.6, -D + 0.6, 1.3, 0.4, 'leaf2', seg=(7, 5))
        k.cyl(s * 1.6, -D + 0.6, 0.75, 0.025, 0.025, 0.25, 'walnut2', seg=4, ink=False)
    return k


def street_taxi(k):
    """A yellow taxi at the kerb (the comic city's cab)."""
    k.begin()
    k.bx(-0.9, 0.9, -2.2, 2.2, 0.3, 0.95, 'amber')
    k.bx(-0.82, 0.82, -1.1, 0.9, 0.95, 1.5, 'amber')
    k.qy(-0.75, 0.75, 1.0, 1.42, -1.103, -1, 'sky')
    k.qy(-0.75, 0.75, 1.0, 1.42, 0.903, 1, 'sky')
    for s in (-1, 1):
        k.qx(-1.0, 0.8, 1.02, 1.42, s * 0.823, s, 'sky')
    k.bx(-0.3, 0.3, -0.3, 0.1, 1.5, 1.65, 'ivory')
    txt(k, 'TAXI', 0, -0.303, 1.575, 0.09, 'black', font='display', valign='m')
    k.qx(-2.0, 2.0, 0.55, 0.62, 0.903, 1, 'black')
    k.qx(-2.0, 2.0, 0.55, 0.62, -0.903, -1, 'black')
    for (x, y) in ((-0.85, -1.4), (0.85, -1.4), (-0.85, 1.4), (0.85, 1.4)):
        k.cyl(x, y, 0.33, 0.33, 0.33, 0.22, 'black', seg=10, rot=(0, 90, 0))
    k.qy(-0.7, -0.45, 0.65, 0.8, -2.203, -1, 'glow')
    k.qy(0.45, 0.7, 0.65, 0.8, -2.203, -1, 'glow')
    k.qy(-0.7, -0.45, 0.65, 0.8, 2.203, 1, 'red')
    k.qy(0.45, 0.7, 0.65, 0.8, 2.203, 1, 'red')
    return k


def street_lamp(k):
    """Cast-iron street lamp with a twin lantern head."""
    k.begin()
    k.cyl(0, 0, 0, 0.22, 0.16, 0.5, 'nero', seg=8)
    k.cyl(0, 0, 0.5, 0.07, 0.06, 4.2, 'nero', seg=6)
    k.bx(-0.62, 0.62, -0.035, 0.035, 4.62, 4.68, 'nero')
    for s in (-1, 1):
        k.cyl(s * 0.6, 0, 4.2, 0.16, 0.2, 0.4, 'glow', seg=6)
        k.cyl(s * 0.6, 0, 4.6, 0.22, 0.05, 0.22, 'nero', seg=6)
    return k


def street_tree(k):
    """Sidewalk plane tree in an iron grate."""
    k.begin()
    k.qz(-0.7, 0.7, -0.7, 0.7, 0.17, 1, 'nero')
    k.cyl(0, 0, 0.17, 0.16, 0.12, 3.2, 'walnut', seg=7)
    for (x, y, z, r) in ((0, 0, 4.4, 1.6), (0.9, 0.4, 3.8, 1.1), (-0.9, -0.3, 3.9, 1.15)):
        k.sph(x, y, z, r, 'leaf' if r > 1.2 else 'leaf2', seg=(7, 4))
    return k
