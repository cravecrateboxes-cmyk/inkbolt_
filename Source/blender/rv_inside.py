"""INKBOLT kit-riviera, zone 1 (the hotel's ground floor): the imperial staircase (landmark), the restaurant Le Grand
Bleu (dining tables, banquettes, the wine wall, the kitchen pass, the sommelier's trolley, cement-tile floor), the
conference hall Salon Mediterranee (rows of chairs, the lectern, the screen over the stage, the AV desk, the coffee
station, cocktail tables, the registration desk) and the palm court (tea tables, the court fountain).
See rv_base.py for the conventions.
"""
import math

from rv_base import H, DECK, RISE, TREAD, RKit, srt, txt, disc, vdisc, frame_y, potted, ring
from hotel_base import dining_chair, gold_chair, armchair, flowers, table_lamp, legs4, palm


# ================================================================ the imperial staircase (landmark) [13, 10]
def _rail_run(k, pts, z_of, x0, x1, along='y', post=0.3, ends=(True, True)):
    """an iron balustrade with a gilt handrail on a sloped or level run: pts (a, b) along `along`, the walk height at a
    position from z_of(t); the run sits between x0 and x1 across it; ends: draw the end posts (a run meeting another
    leaves its shared post to that one)"""
    a, b = pts
    n = max(1, int(abs(b - a) / post))
    xm = (x0 + x1) / 2
    for i in range(n + 1):
        if (i == 0 and not ends[0]) or (i == n and not ends[1]):
            continue
        t = a + (b - a) * i / n
        z = z_of(t)
        if along == 'y':
            k.bx(xm - 0.012, xm + 0.012, t - 0.012, t + 0.012, z, z + 0.95, 'black', ink=False)
        else:
            k.bx(t - 0.012, t + 0.012, xm - 0.012, xm + 0.012, z, z + 0.95, 'black', ink=False)
    # the handrail as a sloped prism through the run's ends
    za, zb = z_of(a), z_of(b)
    if along == 'y':
        k.prism_y([(a, za + 0.95), (b, zb + 0.95), (b, zb + 1.03), (a, za + 1.03)], xm - 0.04, xm + 0.04, 'gold')
        k.prism_y([(a, za + 0.12), (b, zb + 0.12), (b, zb + 0.16), (a, za + 0.16)], xm - 0.02, xm + 0.02, 'black', ink=False)
    else:
        k.prism([(a, za + 0.95), (b, zb + 0.95), (b, zb + 1.03), (a, za + 1.03)], xm - 0.04, xm + 0.04, 'gold')
        k.prism([(a, za + 0.12), (b, zb + 0.12), (b, zb + 0.16), (a, za + 0.16)], xm - 0.02, xm + 0.02, 'black', ink=False)


def imperial_stair(k):
    """The Imperial Staircase: a central flight of white marble on a blue runner rises north from the lobby to a
    landing at 2.16 m, two flights turn back from it and climb south to the top landings at 4.5 m, from which the
    gallery's bridges lead off east and west. Iron balustrades with gilt rails, bronze lamp standards at the foot,
    urns of flowers on the top landings, a niche with a fountain urn in each flank."""
    k.begin()
    X, Y = 6.5, 5.0
    CX, SX0, SX1 = 2.4, 3.6, 6.4             # the centre flight's half width; a side flight between SX0 and SX1
    y_c0, n_c = -1.0, 12                     # centre flight from y_c0 rising toward +Y, 12 risers to the landing
    LZ = n_c * RISE                          # 2.16
    y_l = y_c0 + n_c * TREAD                 # 2.0: the landing from here to the back
    n_s = 13                                 # side flights: 13 risers from the landing to 4.5
    y_t = y_l - n_s * TREAD                  # -1.25: the top landings from here to the front
    # ---- centre flight
    for i in range(n_c):
        a, top = y_c0 + i * TREAD, (i + 1) * RISE
        k.bx(-CX, CX, a, a + TREAD, 0.0, top, 'marble')
        k.qz(-1.3, 1.3, a, a + TREAD, top + 0.003, 1, 'wine')
        k.qy(-1.3, 1.3, top - RISE + 0.01, top, a - 0.003, -1, 'wine2')
        k.bx(-1.36, 1.36, a + 0.02, a + 0.05, top + 0.003, top + 0.03, 'brass', ink=False)
        k.col(-CX, CX, a, a + TREAD, 0, top, True)
    # ---- the landing
    k.bx(-X, X, y_l, Y, 0.0, LZ, 'marble')
    k.qz(-1.3, 1.3, y_l, Y - 0.6, LZ + 0.003, 1, 'wine')
    k.qz(-5.6, 5.6, Y - 1.6, Y - 0.6, LZ + 0.006, 1, 'wine')
    for s in (-1, 1):
        a0, a1 = srt(s * 4.4, s * 5.6)
        k.qz(a0, a1, y_l, Y - 1.6, LZ + 0.003, 1, 'wine')
    k.col(-X, X, y_l, Y, 0, LZ, True)
    # a medallion of blue and gold in the landing's marble
    disc(k, 0, 3.5, LZ + 0.009, 0.7, 'gold', n=16)
    disc(k, 0, 3.5, LZ + 0.012, 0.55, 'wine2', n=16)
    # ---- side flights and top landings, the solid flanks under them
    for s in (-1, 1):
        xa, xb = srt(s * SX0, s * SX1)
        for j in range(n_s):
            b, top = y_l - j * TREAD, LZ + (j + 1) * RISE
            k.bx(xa, xb, b - TREAD, b, 0.0, top, 'marble')
            ra, rb = srt(s * (SX0 + 0.35), s * (SX1 - 0.35))
            k.qz(ra, rb, b - TREAD, b, top + 0.003, 1, 'wine')
            k.qy(ra, rb, top - RISE + 0.01, top, b + 0.003, 1, 'wine2')
            k.col(xa, xb, b - TREAD, b, 0, top, True)
        fa, fb = srt(s * CX, s * X)
        k.bx(fa, fb, -Y, y_t, 0.0, DECK, 'stone')
        k.qz(fa + 0.1, fb - 0.1, -Y + 0.1, y_t - 0.1, DECK + 0.003, 1, 'marble')
        k.col(fa, fb, -Y, y_t, 0, DECK, True)
        # the separator between the centre flight and the side flight: a stone wall stepping with the side flight
        pa, pb = srt(s * CX, s * SX0)
        prof = [(y_t, 0.0), (y_l, 0.0), (y_l, LZ + 0.12), (y_t, DECK + 0.12)]
        k.prism_y(prof, pa, pb, 'stone')
        for j in range(n_s):
            b, top = y_l - j * TREAD, LZ + (j + 1) * RISE
            k.col(pa, pb, b - TREAD, b, 0, top + 1.05)
        # the flank's front (facing the lobby): a niche with a fountain urn, panels, a plinth
        cx = s * (CX + X) / 2
        k.bx(cx - 1.6, cx + 1.6, -Y - 0.03, -Y + 0.001, 0, 0.26, 'marble2', ink=False)
        k.qy(cx - 0.75, cx + 0.75, 0.6, 2.9, -Y - 0.003, -1, 'stone2')
        k.poly([(cx + math.cos(a) * 0.75, -Y - 0.003, 2.9 + math.sin(a) * 0.75) for a in [i * math.pi / 8 for i in range(9)]], 'stone2', (0, -1, 0))
        k.poly([(cx + math.cos(a) * 0.6, -Y - 0.006, 2.9 + math.sin(a) * 0.6) for a in [i * math.pi / 8 for i in range(9)]], 'wine3', (0, -1, 0))
        k.qy(cx - 0.6, cx + 0.6, 0.75, 2.9, -Y - 0.006, -1, 'wine3')
        k.cyl(cx, -Y - 0.3, 0.3, 0.32, 0.22, 0.5, 'marble', seg=10)
        k.cyl(cx, -Y - 0.3, 0.8, 0.2, 0.42, 0.35, 'marble', seg=10)
        flowers(k, cx, -Y - 0.3, 1.12, 0.9, 'rose')
        k.bx(cx - 0.45, cx + 0.45, -Y - 0.62, -Y - 0.004, 0, 0.3, 'marble2')
        k.col(cx - 0.45, cx + 0.45, -Y - 0.62, -Y, 0, 1.6)
        for px in (cx - 1.5, cx + 1.5):
            k.qy(px - 0.35, px + 0.35, 0.6, 3.6, -Y - 0.003, -1, 'stone2')
            frame_y(k, px - 0.3, px + 0.3, 0.65, 3.55, -Y - 0.006, -1, 'gold', 0.025)
        k.bx(fa, fb, -Y - 0.08, -Y, DECK - 0.42, DECK - 0.1, 'stone2')
        # bronze lamp standards at the foot of the centre flight
        lx = s * (CX - 0.25)
        k.cyl(lx, y_c0 - 0.35, 0, 0.18, 0.14, 0.3, 'marble2', seg=8)
        k.cyl(lx, y_c0 - 0.35, 0.3, 0.05, 0.05, 1.6, 'bronze', seg=6)
        for a in (0, 2.1, 4.2):
            k.beam((lx, y_c0 - 0.35, 1.8), (lx + math.cos(a) * 0.28, y_c0 - 0.35 + math.sin(a) * 0.28, 1.95), 0.03, 'bronze', ink=False)
            k.cyl(lx + math.cos(a) * 0.28, y_c0 - 0.35 + math.sin(a) * 0.28, 1.95, 0.08, 0.06, 0.2, 'glow', seg=6)
        k.col(lx - 0.2, lx + 0.2, y_c0 - 0.55, y_c0 - 0.15, 0, 2.1)
        # an urn of flowers on each top landing's front corner, against the rail
        ux = s * (X - 0.55)
        k.cyl(ux, -Y + 0.55, DECK, 0.2, 0.28, 0.5, 'stone', seg=10)
        flowers(k, ux, -Y + 0.55, DECK + 0.5, 0.8, 'rose')
        k.col(ux - 0.3, ux + 0.3, -Y + 0.25, -Y + 0.85, DECK, DECK + 1.0)
        # balustrades: the side flight's outer edge, the landing's outer end, the top landing's front and inner edge,
        # the separator's top (both flights)
        ox = s * (X - 0.06)
        _rail_run(k, (y_t, y_l), lambda t: LZ + (y_l - t) / TREAD * RISE, ox - 0.03, ox + 0.03)
        _rail_run(k, (y_l, Y - 0.06), lambda t: LZ, ox - 0.03, ox + 0.03, ends=(False, True))
        ix = s * (CX + 0.06)
        _rail_run(k, (-Y + 0.06, y_t), lambda t: DECK, ix - 0.03, ix + 0.03, ends=(True, False))
        _rail_run(k, (y_t, y_l), lambda t: DECK + 0.13 + (t - y_t) / (y_l - y_t) * (LZ - DECK), ix - 0.03, ix + 0.03)
        lo, hi = srt(s * (CX + 0.14), s * (X - 0.14))
        _rail_run(k, (lo, hi), lambda t: DECK, -Y + 0.03, -Y + 0.09, along='x', ends=(False, False))
        k.col(ox - 0.06, ox + 0.06, y_t, Y, 0, LZ + 1.1 + (DECK - LZ) * 0)
        for j in range(n_s):
            b, top = y_l - j * TREAD, LZ + (j + 1) * RISE
            k.col(ox - 0.06, ox + 0.06, b - TREAD, b, 0, top + 1.05)
        k.col(ix - 0.06, ix + 0.06, -Y, y_t, DECK, DECK + 1.05)
        k.col(lo, hi, -Y, -Y + 0.12, DECK, DECK + 1.05)
    # the landing's back edge (over the aisle under the north gallery)
    _rail_run(k, (-X + 0.14, X - 0.14), lambda t: LZ, Y - 0.09, Y - 0.03, along='x', ends=(False, False))
    k.col(-X, X, Y - 0.12, Y, LZ, LZ + 1.05)
    return k


# ================================================================ the restaurant Le Grand Bleu
def posy(k, x, y, z, s=1.0):
    """a small glass vase of roses on a table"""
    k.cyl(x, y, z, 0.04 * s, 0.05 * s, 0.14 * s, 'crystal2', seg=5, ink=False)
    k.sph(x, y, z + 0.2 * s, 0.09 * s, 'rose', seg=(5, 3))


def place_setting(k, x, y, deg):
    k.push(x, y, deg)
    disc(k, 0, -0.18, 0.795, 0.12, 'ivory', n=10)
    disc(k, 0, -0.18, 0.798, 0.07, 'wine', n=8)
    k.cyl(0.13, -0.05, 0.792, 0.025, 0.03, 0.14, 'crystal2', seg=5, ink=False)
    k.pop()


def cloth_table(k, x, y, w, d, h=0.78, round_=False):
    """a dining table under a long white cloth"""
    if round_:
        k.cyl(x, y, 0.0, w / 2 + 0.02, w / 2 + 0.02, h - 0.02, 'ivory', seg=12)
        k.cyl(x, y, h - 0.02, w / 2 + 0.04, w / 2 + 0.04, 0.03, 'ivory', seg=12, ink=False)
    else:
        k.bx(x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0.0, h, 'ivory')


def dine_table(k):
    """[2, 2] a four-top: a square table in white linen, four blue dining chairs, place settings, a candle and roses"""
    k.begin()
    cloth_table(k, 0, 0, 0.92, 0.92)
    for (x, y, d) in ((0, -0.68, 180), (0, 0.68, 0), (-0.68, 0, 270), (0.68, 0, 90)):
        light_chair(k, x, y, d, 'wine', 'walnut')
    for d in (0, 90, 180, 270):
        place_setting(k, 0, 0, d)
    k.cyl(0, 0, 0.78, 0.04, 0.03, 0.14, 'crystal2', seg=6, ink=False)
    posy(k, 0, 0, 0.92, 0.45 * 2)
    k.col(-0.47, 0.47, -0.47, 0.47, 0, 0.8)
    for (x, y) in ((0, -0.7), (0, 0.7), (-0.7, 0), (0.7, 0)):
        k.col(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 0, 1.0)
    return k


def dine_two(k):
    """[2, 1] a round two-top by the windows, its chairs east and west"""
    k.begin()
    cloth_table(k, 0, 0, 0.74, 0.74, round_=True)
    light_chair(k, -0.62, 0, 270, 'wine', 'walnut')
    light_chair(k, 0.62, 0, 90, 'wine', 'walnut')
    place_setting(k, 0, 0, 90)
    place_setting(k, 0, 0, 270)
    k.cyl(0, 0.12, 0.78, 0.035, 0.03, 0.12, 'crystal2', seg=6, ink=False)
    posy(k, 0, 0.12, 0.9, 0.35 * 2)
    k.col(-0.38, 0.38, -0.38, 0.38, 0, 0.8)
    for x in (-0.64, 0.64):
        k.col(x - 0.24, x + 0.24, -0.24, 0.24, 0, 1.0)
    return k


def banquette(k):
    """[4, 2] a blue velvet banquette against a wall (+Y) with two tables and two chairs facing it, a mirror strip
    above the backrest"""
    k.begin()
    k.bx(-1.98, 1.98, 0.45, 0.98, 0.0, 0.46, 'walnut2')
    k.bx(-1.96, 1.96, 0.47, 0.95, 0.46, 0.52, 'wine')
    k.bx(-1.98, 1.98, 0.8, 0.98, 0.52, 1.25, 'wine')
    for i in range(6):
        x = -1.65 + i * 0.66
        k.qy(x - 0.02, x + 0.02, 0.6, 1.2, 0.797, -1, 'wine2')
    k.bx(-1.98, 1.98, 0.78, 0.98, 1.25, 1.32, 'walnut', ink=False)
    for tx in (-1.0, 1.0):
        cloth_table(k, tx, 0.0, 0.8, 0.7)
        light_chair(k, tx, -0.68, 180, 'wine', 'walnut')
        place_setting(k, tx, 0, 0)
        place_setting(k, tx, 0, 180)
        posy(k, tx + 0.25, 0.15, 0.78, 0.35 * 2)
        k.col(tx - 0.4, tx + 0.4, -0.35, 0.35, 0, 0.8)
        k.col(tx - 0.24, tx + 0.24, -0.92, -0.44, 0, 1.0)
    k.col(-1.98, 1.98, 0.45, 0.98, 0, 1.32)
    return k


def wine_wall(k):
    """[3, 1] a wall of wine racks against a wall (+Y): walnut frame, diamond bins full of bottles, a tasting ledge"""
    k.begin()
    k.bx(-1.48, 1.48, 0.1, 0.48, 0.0, 2.6, 'walnut2')
    k.bx(-1.5, 1.5, 0.05, 0.5, 2.6, 2.72, 'walnut')
    for i in range(6):
        x0 = -1.38 + i * 0.46
        for j in range(5):
            z0 = 0.2 + j * 0.46
            k.qy(x0, x0 + 0.42, z0, z0 + 0.42, 0.097, -1, 'black')
            for (u, v) in ((0.1, 0.1), (0.27, 0.1), (0.1, 0.27), (0.27, 0.27), (0.185, 0.185)):
                vdisc(k, x0 + 0.02 + u, 0.094, z0 + 0.02 + v, 0.045, 'leaf2' if (i + j) % 3 else 'wine3', n=6)
    k.bx(-1.48, 1.48, -0.25, 0.1, 1.0, 1.05, 'walnut')
    for x in (-1.0, -0.2, 0.7):
        k.cyl(x, -0.08, 1.05, 0.035, 0.035, 0.28, 'leaf2', seg=6, ink=False)
        k.cyl(x + 0.18, -0.12, 1.05, 0.03, 0.035, 0.15, 'crystal2', seg=5, ink=False)
    k.col(-1.5, 1.5, -0.25, 0.5, 0, 2.72)
    return k


def kitchen_pass(k):
    """[4, 1] the pass in front of the kitchen doors (+Y): a steel counter with plates under heat lamps, a ticket rail"""
    k.begin()
    k.bx(-1.95, 1.95, -0.3, 0.35, 0.0, 0.92, 'steel2')
    k.bx(-1.98, 1.98, -0.33, 0.38, 0.92, 0.96, 'chrome')
    k.qy(-1.9, 1.9, 0.08, 0.86, -0.303, -1, 'steel')
    for x in (-1.4, -0.7, 0.0, 0.7, 1.4):
        disc(k, x, 0.0, 0.965, 0.13, 'ivory', n=10)
        k.sph(x, 0.0, 0.99, 0.06, 'emerald' if x < 0 else 'leaf', seg=(5, 3), scale=(1, 1, 0.5), ink=False)
        k.cyl(x, 0.02, 1.62, 0.12, 0.07, 0.15, 'steel2', seg=8)
        disc(k, x, 0.02, 1.617, 0.1, 'fire', n=8, up=False)
        k.cyl(x, 0.02, 1.77, 0.012, 0.012, 1.2, 'black', seg=4, ink=False)
    k.bx(-1.9, 1.9, 0.3, 0.34, 1.45, 1.5, 'chrome', ink=False)
    for x in (-1.2, -0.5, 0.4, 1.1):
        k.qy(x - 0.06, x + 0.06, 1.27, 1.45, 0.297, -1, 'paper')
    k.col(-1.98, 1.98, -0.33, 0.38, 0, 0.96)
    return k


def wine_trolley(k):
    """a sommelier's trolley: brass frame, an ice bucket with a bottle, glasses, a decanter"""
    k.begin()
    k.bx(-0.36, 0.36, -0.24, 0.24, 0.78, 0.82, 'walnut')
    k.bx(-0.34, 0.34, -0.22, 0.22, 0.24, 0.27, 'walnut', ink=False)
    for (x, y) in ((-0.32, -0.2), (0.32, -0.2), (-0.32, 0.2), (0.32, 0.2)):
        k.cyl(x, y, 0.06, 0.015, 0.015, 0.73, 'brass', seg=4, ink=False)
        k.cyl(x, y, 0.0, 0.05, 0.05, 0.06, 'black', seg=6, ink=False)
    k.cyl(-0.12, 0, 0.82, 0.11, 0.13, 0.22, 'chrome', seg=10)
    k.cyl(-0.12, 0, 0.9, 0.035, 0.035, 0.32, 'leaf2', seg=6, ink=False)
    k.cyl(0.18, -0.08, 0.82, 0.06, 0.03, 0.2, 'crystal2', seg=6, ink=False)
    k.cyl(0.18, 0.1, 0.82, 0.03, 0.035, 0.14, 'crystal2', seg=5, ink=False)
    k.col(-0.36, 0.36, -0.24, 0.24, 0, 1.0)
    return k


def cement_tiles(k):
    """[2, 2] Provencal cement tiles (floor layer): four 1 m tiles in cream and stone, a blue star on the pale ones"""
    k.begin()
    for i in range(2):
        for j in range(2):
            x0, y0 = -1.0 + i, -1.0 + j
            k.qz(x0 + 0.01, x0 + 0.99, y0 + 0.01, y0 + 0.99, 0.009, 1, 'cream' if (i + j) % 2 else 'stone')
            if (i + j) % 2:
                cx, cy, r, q = x0 + 0.5, y0 + 0.5, 0.32, 0.08
                k.poly([(cx, cy - r, 0.012), (cx + q, cy - q, 0.012), (cx + r, cy, 0.012), (cx + q, cy + q, 0.012), (cx, cy + r, 0.012), (cx - q, cy + q, 0.012), (cx - r, cy, 0.012), (cx - q, cy - q, 0.012)], 'wine', (0, 0, 1))
    return k


def banquet_chair(k, x, y):
    """a light gilt banquet chair with a blue seat (the sitter faces local -Y)"""
    k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.0, 0.42, 'gold', ink=False)
    k.bx(x - 0.21, x + 0.21, y - 0.21, y + 0.2, 0.42, 0.5, 'wine')
    k.bx(x - 0.19, x + 0.19, y + 0.15, y + 0.2, 0.5, 0.98, 'gold')
    k.qy(x - 0.13, x + 0.13, 0.62, 0.9, y + 0.147, -1, 'wine')


def chair_row(k):
    """[6, 1] a row of six gilt banquet chairs with blue seats (the sitters face local -Y), a programme on some seats"""
    k.begin()
    for i in range(6):
        x = -2.5 + i
        banquet_chair(k, x, 0)
        if i % 2 == 0:
            k.qz(x - 0.1, x + 0.06, -0.12, 0.08, 0.503, 1, 'paper')
        k.col(x - 0.21, x + 0.21, -0.22, 0.21, 0, 0.98)
    return k


def lectern(k):
    """the speaker's lectern: walnut with a brass name plate, a gooseneck microphone, notes and a water glass"""
    k.begin()
    k.prism_y([(-0.3, 0.0), (0.25, 0.0), (0.25, 1.05), (-0.25, 1.2), (-0.3, 1.2)], -0.32, 0.32, 'walnut')
    k.qy(-0.26, 0.26, 0.2, 0.95, -0.303, -1, 'walnut2')
    k.qy(-0.18, 0.18, 0.62, 0.78, -0.306, -1, 'brass')
    txt(k, 'RIVIERA', 0, -0.309, 0.7, 0.06, 'wine3', font='serif', valign='m', maxw=0.32)
    k.beam((0.18, 0.1, 1.17), (0.12, -0.15, 1.42), 0.015, 'black', ink=False)
    k.sph(0.12, -0.16, 1.43, 0.03, 'black', ink=False)
    k.cyl(-0.2, 0.12, 1.15, 0.03, 0.035, 0.12, 'crystal2', seg=5, ink=False)
    k.col(-0.32, 0.32, -0.3, 0.25, 0, 1.2)
    return k


def stage_screen(k, w=9.0, d=4.0):
    """the projection screen on the wall behind the stage (part of the Stage, its frame): a silver screen with the
    forum's opening slide, blue drapes either side, a valance with the hotel's name"""
    k.begin()
    y = d / 2 - 0.08
    k.bx(-3.2, 3.2, y - 0.06, y, 2.3, 6.2, 'black')
    k.qy(-3.05, 3.05, 2.45, 6.05, y - 0.063, -1, 'steel')
    k.qy(-3.05, 3.05, 2.45, 3.2, y - 0.066, -1, 'wine2')
    k.qy(-2.6, 2.6, 4.2, 5.5, y - 0.066, -1, 'wine')
    txt(k, 'RIVIERA FORUM', 0, y - 0.069, 4.85, 0.42, 'ivory', font='serif', valign='m', maxw=4.8)
    txt(k, 'THE BLUE ECONOMY', 0, y - 0.069, 3.7, 0.22, 'ivory', font='sans', valign='m', maxw=4.0)
    vdisc(k, -2.2, y - 0.069, 2.82, 0.22, 'gold', n=10)
    for s in (-1, 1):
        a0, a1 = srt(s * 3.3, s * 4.4)
        k.bx(a0, a1, y - 0.2, y - 0.025, 0.6, 7.54, 'wine')
        for i in range(4):
            fx = min(a0, a1) + 0.12 + i * 0.26
            k.qy(fx, fx + 0.05, 0.7, 7.5, y - 0.203, -1, 'wine2')
    k.bx(-4.45, 4.45, y - 0.25, y - 0.02, 7.6, 8.2, 'wine2')
    k.bx(-4.45, 4.45, y - 0.27, y - 0.02, 7.55, 7.6, 'gold', ink=False)
    txt(k, 'GRAND HOTEL RIVIERA', 0, y - 0.253, 7.9, 0.28, 'gold', font='serif', valign='m', maxw=6.0)
    return k


def av_desk(k):
    """[3, 2] the AV desk at the back of the hall: a draped table with a mixing desk, two laptops, a camera on a tripod"""
    k.begin()
    k.bx(-1.4, 1.4, -0.1, 0.6, 0.0, 0.76, 'navy')
    k.bx(-1.42, 1.42, -0.12, 0.62, 0.76, 0.79, 'navy2', ink=False)
    k.bx(-0.6, 0.4, 0.0, 0.5, 0.79, 0.86, 'black')
    for i in range(12):
        x = -0.55 + i * 0.08
        k.qz(x, x + 0.03, 0.08, 0.4, 0.863, 1, 'steel' if i % 3 else 'amber')
    for x in (-1.05, 0.85):
        k.bx(x - 0.18, x + 0.18, 0.1, 0.4, 0.79, 0.81, 'steel2', ink=False)
        k.m.box((x, 0.43, 0.93), (0.36, 0.02, 0.24), 'steel2', rot=(-15, 0, 0), bevel=False)
        k._mark(False)
    k.bx(-0.3, 0.3, 0.4, 0.55, 0.0, 0.4, 'black')
    # the camera tripod in front (toward the stage, local -Y)
    for a in (0.3, 2.4, 4.5):
        k.beam((0.0, -0.6, 1.3), (math.cos(a) * 0.35, -0.6 + math.sin(a) * 0.35, 0.0), 0.025, 'black', ink=False)
    k.bx(-0.12, 0.12, -0.82, -0.42, 1.3, 1.52, 'black')
    k.cyl(0, -0.83, 1.41, 0.07, 0.07, 0.12, 'black', seg=8, rot=(90, 0, 0))
    k.col(-1.42, 1.42, -0.12, 0.62, 0, 0.9)
    k.col(-0.2, 0.2, -0.85, -0.38, 0, 1.55)
    return k


def coffee_station(k):
    """[4, 1] the coffee-break table against a wall (+Y): white cloth with a blue skirt band, coffee urns, cups and
    saucers, a platter of pastries, a vase of flowers"""
    k.begin()
    k.bx(-1.95, 1.95, -0.32, 0.4, 0.0, 0.78, 'ivory')
    k.qy(-1.95, 1.95, 0.0, 0.18, -0.323, -1, 'wine')
    for x in (-1.4, -0.85):
        k.cyl(x, 0.12, 0.78, 0.14, 0.14, 0.42, 'chrome', seg=10)
        k.cyl(x, 0.12, 1.2, 0.08, 0.02, 0.08, 'chrome', seg=8, ink=False)
        k.bx(x - 0.03, x + 0.03, -0.06, 0.0, 0.84, 0.9, 'black', ink=False)
    for i in range(6):
        x = -0.4 + (i % 3) * 0.22
        y = -0.12 + (i // 3) * 0.2
        disc(k, x, y, 0.785, 0.07, 'ivory', n=8)
        k.cyl(x, y, 0.788, 0.035, 0.04, 0.06, 'ivory', seg=6, ink=False)
    k.cyl(0.7, 0.0, 0.78, 0.26, 0.26, 0.03, 'steel', seg=12, ink=False)
    for i in range(7):
        a = i * 0.9
        k.sph(0.7 + math.cos(a) * 0.15, math.sin(a) * 0.15, 0.84, 0.06, 'oak', seg=(5, 3), scale=(1.3, 1, 0.6), ink=False)
    posy(k, 1.5, 0.15, 0.78, 0.6 * 2)
    k.col(-1.95, 1.95, -0.32, 0.4, 0, 0.85)
    return k


def high_table(k):
    """a cocktail table in a white stretch cover with a blue sash and a small vase"""
    k.begin()
    k.cyl(0, 0, 0, 0.3, 0.12, 0.55, 'ivory', seg=8)
    k.cyl(0, 0, 0.55, 0.12, 0.33, 0.55, 'ivory', seg=8)
    k.cyl(0, 0, 0.88, 0.235, 0.27, 0.08, 'wine', seg=8, ink=False)
    k.cyl(0.1, 0.05, 1.12, 0.03, 0.025, 0.12, 'crystal2', seg=5, ink=False)
    posy(k, -0.08, -0.06, 1.12, 0.3 * 2)
    k.col(-0.3, 0.3, -0.3, 0.3, 0, 1.12)
    return k


def reg_desk(k):
    """[4, 2] the forum's registration desk: two draped tables with a banner, rows of name badges, a laptop, a stand
    with lanyards; a roll-up banner behind (+Y)"""
    k.begin()
    k.bx(-1.9, 1.9, -0.6, 0.1, 0.0, 0.76, 'ivory')
    k.qy(-1.9, 1.9, 0.05, 0.6, -0.603, -1, 'wine')
    txt(k, 'RIVIERA FORUM', -0.3, -0.606, 0.33, 0.16, 'ivory', font='serif', valign='m', maxw=2.2)
    txt(k, 'REGISTRATION', 1.2, -0.606, 0.33, 0.09, 'ivory', font='sans', valign='m', maxw=0.9)
    for i in range(10):
        x = -1.6 + (i % 5) * 0.16
        y = -0.45 + (i // 5) * 0.12
        k.qz(x, x + 0.11, y, y + 0.08, 0.763, 1, 'paper')
        k.qz(x, x + 0.11, y + 0.06, y + 0.08, 0.766, 1, 'wine')
    k.bx(0.3, 0.66, -0.35, -0.1, 0.76, 0.78, 'steel2', ink=False)
    k.m.box((0.48, -0.08, 0.9), (0.36, 0.02, 0.24), 'steel2', rot=(-15, 0, 0), bevel=False)
    k._mark(False)
    # the roll-up banner
    k.bx(0.9, 1.7, 0.55, 0.62, 0.0, 2.1, 'wine2')
    k.qy(0.95, 1.65, 0.1, 2.05, 0.547, -1, 'wine')
    txt(k, 'RF', 1.3, 0.544, 1.45, 0.3, 'gold', font='serif', valign='m', maxw=0.6)
    k.bx(0.88, 1.72, 0.5, 0.68, 0.0, 0.08, 'steel2', ink=False)
    for x in (-1.3, 0.0):
        light_chair(k, x, 0.5, 0, 'navy', 'walnut2')
    k.col(-1.9, 1.9, -0.6, 0.1, 0, 0.8)
    k.col(0.88, 1.72, 0.5, 0.68, 0, 2.1)
    for x in (-1.3, 0.0):
        k.col(x - 0.24, x + 0.24, 0.27, 0.73, 0, 1.0)
    return k


# ================================================================ the palm court
def rattan_chair(k, x, y, deg, fab='wine'):
    """a round rattan tub chair with a cushion (the sitter faces local -Y)"""
    k.push(x, y, deg)
    k.cyl(0, 0, 0.0, 0.3, 0.33, 0.42, 'oak', seg=8)
    k.cyl(0, 0, 0.42, 0.29, 0.29, 0.07, fab, seg=8, ink=False)
    k.bx(-0.3, 0.3, 0.14, 0.3, 0.44, 0.88, 'oak')
    k.pop()


def tea_set(k):
    """[2, 2] afternoon tea: a round marble table on a rattan base, two rattan tub chairs, a cake stand, a silver
    teapot, cups"""
    k.begin()
    k.cyl(0, 0, 0, 0.22, 0.12, 0.66, 'oak', seg=6)
    k.cyl(0, 0, 0.66, 0.42, 0.42, 0.05, 'marble', seg=10)
    rattan_chair(k, -0.55, 0.42, 225)
    rattan_chair(k, 0.55, -0.42, 45)
    k.cyl(0.12, 0.1, 0.71, 0.012, 0.012, 0.42, 'chrome', seg=3, ink=False)
    for (z, r, c) in ((0.78, 0.15, 'blush'), (0.92, 0.12, 'oak'), (1.05, 0.09, 'blush')):
        k.cyl(0.12, 0.1, z, r, r, 0.03, c, seg=8, ink=False)
    k.sph(-0.14, -0.06, 0.78, 0.08, 'chrome', seg=(6, 4), scale=(1, 1, 0.8))
    for (x, y) in ((-0.2, 0.2), (0.2, -0.22)):
        disc(k, x, y, 0.713, 0.06, 'ivory', n=6)
    k.col(-0.42, 0.42, -0.42, 0.42, 0, 0.72)
    for (x, y) in ((-0.55, 0.42), (0.55, -0.42)):
        k.col(x - 0.33, x + 0.33, y - 0.33, y + 0.33, 0, 0.9)
    return k


def court_fountain(k):
    """[4, 4] the palm court's fountain: an octagonal marble basin with a mosaic band, a fluted pedestal, a scalloped
    bowl and a jet falling back as a sheet"""
    k.begin()
    R, Hb = 1.9, 0.5
    n = 8
    pts = [(math.cos(i / n * math.pi * 2 + math.pi / 8) * R, math.sin(i / n * math.pi * 2 + math.pi / 8) * R) for i in range(n)]
    k.prism_z(pts, 0, Hb, 'marble')
    pin = [(x * 0.86, y * 0.86) for (x, y) in pts]
    k.poly([(x, y, Hb - 0.06) for (x, y) in pin], 'water', (0, 0, 1))
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx_, ny_ = mx / math.hypot(mx, my), my / math.hypot(mx, my)
        L = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        o = 0.003
        k.poly([(x0 + tx * 0.05 + nx_ * o, y0 + ty * 0.05 + ny_ * o, 0.18), (x1 - tx * 0.05 + nx_ * o, y1 - ty * 0.05 + ny_ * o, 0.18),
                (x1 - tx * 0.05 + nx_ * o, y1 - ty * 0.05 + ny_ * o, 0.32), (x0 + tx * 0.05 + nx_ * o, y0 + ty * 0.05 + ny_ * o, 0.32)],
               'tile' if i % 2 else 'wine', (nx_, ny_, 0))
    for i in range(10):
        a = i * 0.63
        k.qz(math.cos(a) * 1.1 - 0.12, math.cos(a) * 1.1 + 0.12, math.sin(a) * 1.1 - 0.02, math.sin(a) * 1.1 + 0.02, Hb - 0.057, 1, 'waterL')
    k.cyl(0, 0, Hb - 0.06, 0.22, 0.16, 0.9, 'marble', seg=10)
    k.cyl(0, 0, Hb + 0.84, 0.16, 0.7, 0.22, 'marble', seg=12)
    disc(k, 0, 0, Hb + 1.063, 0.62, 'water', n=12)
    k.cyl(0, 0, Hb + 1.06, 0.05, 0.03, 0.55, 'waterL', seg=6, ink=False)
    k.cyl(0, 0, Hb + 0.3, 0.66, 0.64, 0.7, 'waterL', seg=12, ink=False, caps=False)
    k.col(-1.75, 1.75, -0.72, 0.72, 0, Hb)
    k.col(-0.72, 0.72, -1.75, -0.72, 0, Hb)
    k.col(-0.72, 0.72, 0.72, 1.75, 0, Hb)
    k.col(-0.25, 0.25, -0.25, 0.25, 0, Hb + 1.1)
    return k


# ================================================================ the gallery's balustrade and columns (light)
def g_rail(k, y0, y1):
    """a white balustrade on the gallery's edge (a run along Y): a marble plinth, flat iron bars, a gilt rail"""
    k.bx(-0.08, 0.08, y0, y1, 0, 0.14, 'marble2')
    n = max(1, int(round((y1 - y0) / 0.2)))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        for s in (-1, 1):
            k.qx(y - 0.012, y + 0.012, 0.14, 0.94, s * 0.012, s, 'black')
    k.bx(-0.06, 0.06, y0, y1, 0.94, 1.03, 'gold')


def g_rails(k):
    k.begin()
    g_rail(k, -0.5, -0.11)
    k.col(-0.1, 0.1, -0.5, 0.0, 0, 1.1)
    k.finish('GRail')
    k.begin()
    g_rail(k, -0.5, 0.5)
    k.col(-0.1, 0.1, -0.5, 0.5, 0, 1.1)
    k.finish('GRailFull')
    k.begin()
    k.bx(-0.1, 0.1, -0.1, 0.1, 0.004, 1.0, 'marble')
    k.bx(-0.12, 0.12, -0.12, 0.12, 1.0, 1.08, 'gold', ink=False)
    k.finish('GRailPost')


def g_columns(k):
    """white marble columns with gilt capitals under the gallery's edge (0 - 4.2) and over it (4.5 - 9)"""
    for name, h in (('GCol_Lo', DECK - 0.3), ('GCol_Hi', H - DECK)):
        k.begin()
        k.bx(-0.4, 0.4, -0.4, 0.4, 0, 0.3, 'marble2')
        k.cyl(0, 0, 0.3, 0.28, 0.25, h - 0.3 - 0.5, 'marble', seg=8)
        k.cyl(0, 0, h - 0.5, 0.25, 0.38, 0.35, 'gold', seg=8, ink=False)
        k.bx(-0.42, 0.42, -0.42, 0.42, h - 0.15, h - 0.004, 'stone2')
        k.col(-0.4, 0.4, -0.4, 0.4, 0, h)
        k.finish(name)


# ================================================================ light furniture (the zone triangle budget)
def light_chair(k, x, y, deg, fab='wine', frame='walnut'):
    """a dining chair: upholstered seat and back on a wooden frame (the sitter faces local -Y)"""
    k.push(x, y, deg)
    k.bx(-0.2, 0.2, -0.2, 0.2, 0.0, 0.42, frame, ink=False)
    k.bx(-0.22, 0.22, -0.22, 0.21, 0.42, 0.5, fab)
    k.bx(-0.21, 0.21, 0.16, 0.21, 0.5, 0.98, frame)
    k.qy(-0.15, 0.15, 0.58, 0.9, 0.157, -1, fab)
    k.pop()


def light_sofa(k, x, y, deg, w=2.0, fab='wine', leg='walnut2'):
    """a sofa (the sitters face local -Y): base, back, arms, a seam line on the seat"""
    k.push(x, y, deg)
    k.bx(-w / 2, w / 2, -0.42, 0.42, 0.08, 0.44, fab)
    k.bx(-w / 2, w / 2, 0.18, 0.42, 0.44, 0.86, fab)
    for s in (-1, 1):
        a, b = srt(s * w / 2, s * (w / 2 - 0.16))
        k.bx(a, b, -0.42, 0.18, 0.44, 0.64, fab)
    k.bx(-w / 2 + 0.05, w / 2 - 0.05, -0.37, 0.37, 0.0, 0.08, leg, ink=False)
    k.qz(-0.012, 0.012, -0.4, 0.17, 0.443, 1, 'cream')
    k.pop()


def light_armchair(k, x, y, deg, fab='wine', leg='walnut2'):
    k.push(x, y, deg)
    k.bx(-0.4, 0.4, -0.38, 0.38, 0.08, 0.44, fab)
    k.bx(-0.4, 0.4, 0.16, 0.38, 0.44, 0.84, fab)
    for s in (-1, 1):
        a, b = srt(s * 0.4, s * 0.27)
        k.bx(a, b, -0.38, 0.16, 0.44, 0.62, fab)
    k.bx(-0.35, 0.35, -0.33, 0.33, 0.0, 0.08, leg, ink=False)
    k.pop()


def lounge_set(k):
    """[4, 3] a seating group on a rug: a blue velvet sofa, two armchairs turned in, a marble coffee table with
    flowers, a side table with a lamp"""
    k.begin()
    k.qz(-1.8, 1.8, -1.3, 1.3, 0.012, 1, 'wine3')
    k.qz(-1.62, 1.62, -1.12, 1.12, 0.015, 1, 'silk')
    light_sofa(k, 0, 0.9, 0, 2.2)
    light_armchair(k, -1.4, -0.5, 115)
    light_armchair(k, 1.4, -0.5, -115)
    k.bx(-0.65, 0.65, -0.5, 0.15, 0.0, 0.36, 'brass', ink=False)
    k.bx(-0.68, 0.68, -0.53, 0.18, 0.36, 0.42, 'marble')
    posy(k, 0.25, -0.15, 0.42, 0.55 * 2)
    k.cyl(1.5, 1.0, 0, 0.24, 0.24, 0.55, 'marble', seg=8)
    k.cyl(1.5, 1.0, 0.55, 0.05, 0.08, 0.3, 'brass', seg=5, ink=False)
    k.cyl(1.5, 1.0, 0.85, 0.2, 0.13, 0.22, 'shade', seg=6)
    k.col(-1.1, 1.1, 0.48, 1.32, 0, 0.86)
    for s in (-1, 1):
        x0, x1 = srt(s * 1.0, s * 1.85)
        k.col(x0, x1, -0.95, -0.05, 0, 0.84)
    k.col(-0.68, 0.68, -0.53, 0.18, 0, 0.42)
    k.col(1.26, 1.74, 0.76, 1.24, 0, 0.6)
    return k


def lustre(k):
    """a crystal chandelier hung from the ceiling plane (3 x 3): a gilt ring of candle arms, a crystal bowl, drops"""
    k.begin()
    k.beam((0, 0, -0.01), (0, 0, -0.9), 0.04, 'gold', ink=False)
    k.cyl(0, 0, -0.12, 0.2, 0.2, 0.1, 'gold', seg=6, ink=False)
    z = -1.6
    ring(k, 0.9, z, 8, 0.06, 'gold')
    for i in range(8):
        a = i / 8 * math.pi * 2
        x, y = math.cos(a) * 0.9, math.sin(a) * 0.9
        k.cyl(x, y, z + 0.04, 0.045, 0.025, 0.22, 'glow', seg=4, ink=False)
        if i % 2 == 0:
            k.beam((x, y, z), (x * 0.2, y * 0.2, z + 0.4), 0.03, 'gold', ink=False)
    k.cyl(0, 0, z - 0.35, 0.06, 0.4, 0.35, 'crystal2', seg=8)
    k.cyl(0, 0, z, 0.1, 0.1, 0.7, 'gold', seg=6, ink=False)
    k.sph(0, 0, z - 0.5, 0.1, 'crystal', seg=(5, 3), scale=(1, 1, 1.5), ink=False)
    return k


def palm_pot(k):
    """a kentia palm in a white urn"""
    k.begin()
    k.cyl(0, 0, 0, 0.2, 0.17, 0.12, 'marble', seg=6)
    k.cyl(0, 0, 0.12, 0.17, 0.3, 0.5, 'marble', seg=8)
    k.cyl(0, 0, 0.62, 0.31, 0.31, 0.05, 'gold', seg=8, ink=False)
    disc(k, 0, 0, 0.666, 0.27, 'soil', n=6)
    for i in range(6):
        a = i / 6 * math.pi * 2 + 0.3
        ca, sa = math.cos(a), math.sin(a)
        mid = (ca * 0.25, sa * 0.25, 1.55 + 0.18 * (i % 3))
        k.beam((ca * 0.04, sa * 0.04, 0.66), mid, 0.03, 'oak', ink=False)
        k.beam(mid, (ca * 0.85, sa * 0.85, 1.2 + 0.15 * (i % 2)), 0.13, 'leaf' if i % 2 else 'leaf2')
    k.col(-0.3, 0.3, -0.3, 0.3, 0, 1.4)
    return k
