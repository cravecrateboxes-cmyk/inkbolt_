#!/usr/bin/env python3
"""INKBOLT Cinder Ridge Outpost zones (theme 'frontier'): hand-placed layouts -> src/data/zones/frontier_*.txt

    python3 tools/frontier_zones.py           # write + validate
    python3 tools/frontier_zones.py --check   # validate only
    python3 tools/frontier_zones.py --print   # also print the maps

Zone 1, the settlement (72 x 70): a log stockade with the main gate (south) and the back gate (north), timber
watchtowers in the four corners, the main street (12 m) with the street arch, the general store (walk-in, upstairs),
the trading post (walk-in), the bunkhouse (walk-in), cabins and plank houses, the claims & radio office, the smithy on
the square, the water tower (landmark) and the well in the square, the corral and the stable in the west yard, the
supply depot (fuel tanks, generator, solar rows, radio mast, supply tents) in the east yard, the woodlots.
Zone 2, the edge of the wild (76 x 72): flat ground in the south (the logging camp, the forest edge), two plateaus
3.2 m up in the north (theme.terrain: terrain_height below and in themes/frontier.js) split by a ravine whose floor
runs north to the exit gate; the rope bridge joins the plateaus; the lookout platform (landmark) stands on the west
plateau's cliff edge over the valley; the creek runs down the east side from its spring past the sawmill, its water
wheel and the flume; the old mine in a rock outcrop on the west wall.
Symbols: src/data/themes/frontier.js.
"""
import math
import os
import sys

from zonekit import Zone, validate, write, rects, OUT

PLAT = 3.2
# prefab sizes as they lie in the grid ([w, h] cells; fixed-facing prefabs turned a quarter are given turned)
PREFAB = {'H': (10, 10), 'T': (9, 10), 'B': (8, 12), 'M': (7, 8), 'K': (7, 8), 'k': (7, 8), 'U': (7, 8), 'u': (7, 8),
          'O': (8, 8), 'L': (6, 10), 'Y': (3, 8), 'y': (3, 8), 'W': (6, 6), 'w': (3, 3), 'A': (12, 1),
          'r': (3, 1), 't': (2, 1), 'b': (2, 1), 'V': (3, 6), 'v': (2, 3), 'e': (2, 1), 'g': (2, 3), 'z': (4, 2),
          'm': (2, 2), 'F': (3, 6), 'N': (4, 5),
          '=': (7, 2), 'X': (8, 8), 'I': (10, 8), 'J': (3, 6), '|': (1, 4), 'Z': (4, 2), 'D': (6, 3), '7': (4, 2),
          '8': (3, 2), '9': (5, 1), '0': (8, 2), '1': (2, 2), '@': (3, 3), 'C': (6, 5), '3': (4, 5), '5': (3, 3),
          '6': (2, 1), '&': (3, 5), '%': (2, 1), '*': (5, 8), '+': (2, 2), '^': (4, 3)}
GROUND = '.,:;'
# cells you can stand on (open ground and the props that leave room to walk: the arch's posts, ferns, water)
WALK = set(GROUND) | set("A'~=")
FLAT = 'HTBMKkUuOLYyWwCIJZ*35'     # buildings stand on level ground (theme.terrain.flat)


def fall(v, a, b):
    if v <= a:
        return 1.0
    if v >= b:
        return 0.0
    return 0.5 + 0.5 * math.cos(math.pi * (v - a) / (b - a))


def terrain_height(c, r, zi):
    """vertex (c, r) height before the engine's flat easing -- the same function as themes/frontier.js"""
    if zi != 1:
        return 0.0
    if c <= 30:
        return PLAT * fall(r, 21, 29)
    if c <= 34:
        return 0.0
    return PLAT * fall(r, 15, 23) * fall(c, 50, 58)


def eased(z, zi):
    """the engine's terrain (zones.js buildTerrain, ramp [0, 1]): flat cells pin their corners to 0"""
    W, H = z.w + 1, z.h + 1
    INF = 1e9
    dist = [[INF] * W for _ in range(H)]
    from collections import deque
    q = deque()
    for r in range(z.h):
        for c in range(z.w):
            if r == 0 or c == 0 or r == z.h - 1 or c == z.w - 1 or z.g[r][c] in '#GEPS' + FLAT:
                for (cc, rr) in ((c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)):
                    if dist[rr][cc] > 0:
                        dist[rr][cc] = 0
                        q.append((cc, rr))
    while q:
        c, r = q.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nc, nr = c + dc, r + dr
                if 0 <= nc < W and 0 <= nr < H:
                    nd = dist[r][c] + (1.41 if dc and dr else 1)
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        q.append((nc, nr))
    hf = [[0.0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            k = max(0.0, min(1.0, dist[r][c]))
            k = k * k * (3 - 2 * k)
            hf[r][c] = max(0.0, terrain_height(c, r, zi) * k)
    return hf


class FZone(Zone):
    def __init__(self, name, w, h, gate_e, gate_g, pc, fill=','):
        super().__init__(name, w, h, fill=fill)
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gate_g, 0, 3, 1, 'G')
        self.rect(gate_e, h - 1, 3, 1, 'E')
        self.put(pc, h - 3, 'P', over=fill)

    def paint(self, c0, r0, w, h, ch, over=',.;:'):
        self.pave(c0, r0, w, h, ch, over=over)

    def pf(self, ch, pts, over=GROUND):
        w, d = PREFAB[ch]
        for (c, r) in pts:
            self.block(c, r, w, d, ch, over=over)

    def pfv(self, ch, pts, over=GROUND):
        """the prefab turned a quarter (the block is [d, w])"""
        w, d = PREFAB[ch]
        for (c, r) in pts:
            self.block(c, r, d, w, ch, over=over)

    def cells(self, ch, pts, over=GROUND):
        for (c, r) in pts:
            self.put(c, r, ch, over=over)


def fence(z, c0, r0, c1, r1, gaps=()):
    """a corral fence rectangle ('f' runs) with openings at the given cells"""
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            if (c, r) not in gaps:
                z.put(c, r, 'f', over=GROUND)
    for r in range(r0 + 1, r1):
        for c in (c0, c1):
            if (c, r) not in gaps:
                z.put(c, r, 'f', over=GROUND)


# ---------------------------------------------------------------- zone 1: the settlement
def settlement():
    z = FZone('frontier_1', 72, 70, 34, 34, 35)
    # ground: grass yards, the main street and the square (packed dirt), trodden paths
    z.paint(30, 1, 12, 68, ':')
    z.paint(22, 26, 28, 15, ':')
    for (c0, r0, w, h) in ((19, 52, 11, 2), (42, 52, 9, 2), (19, 42, 11, 1), (42, 42, 9, 1), (20, 24, 10, 2), (42, 22, 8, 2),
                           (5, 36, 17, 3), (50, 33, 16, 3), (51, 46, 15, 4), (8, 46, 12, 2), (50, 12, 14, 2), (10, 12, 12, 2)):
        z.paint(c0, r0, w, h, ';')
    # west row (fronts east): store, cabin, bunkhouse, house; the water tower on the square
    z.pf('H', [(20, 54)])
    z.pf('K', [(23, 43)])
    z.pf('B', [(22, 12)])
    z.pf('U', [(23, 2)])
    z.pf('W', [(23, 31)])
    # east row (fronts west): trading post, office, smithy on the square, cabin, house
    z.pf('T', [(42, 54)])
    z.pf('O', [(42, 43)])
    z.pf('M', [(42, 30)])
    z.pf('k', [(42, 13)])
    z.pf('u', [(42, 2)])
    # the square: the well in the middle, the street arch near the main gate
    z.pf('w', [(34, 32)])
    z.pf('A', [(30, 65)])
    # hitching rails and troughs by the store and the trading post (clear of their doors)
    z.pf('r', [])
    for (c, r) in ((31, 54), (31, 61), (40, 54), (40, 61)):
        z.block(c, r, 1, 3, 'r', over=GROUND)
    for (c, r) in ((31, 52), (40, 52), (31, 41), (40, 28)):
        z.block(c, r, 1, 2, 't', over=GROUND)
    # lantern posts along the street, the signpost, a wagon and a cart in the street
    z.cells('l', [(30, 50), (41, 50), (30, 27), (41, 27), (30, 11), (41, 11), (41, 39), (22, 40), (49, 40)])
    z.cells('n', [(40, 41)])
    z.block(37, 44, 3, 6, 'V', over=GROUND)
    z.block(32, 15, 2, 3, 'v', over=GROUND)
    z.cells('c', [(31, 49), (32, 49), (40, 47), (40, 46), (33, 24), (39, 6)])
    z.cells('x', [(31, 48), (40, 36), (38, 24), (32, 6)])
    # west yard: the corral (fence, gate gap, trough, hay), the stable against the palisade, wagons, woodlots
    fence(z, 4, 28, 17, 44, gaps={(17, 35), (17, 36), (17, 37)})
    z.block(9, 31, 2, 1, 't', over=GROUND)
    z.block(13, 40, 2, 1, 'b', over=GROUND)
    z.block(6, 41, 2, 1, 'b', over=GROUND)
    z.cells('c', [(15, 30)])
    z.pf('L', [(1, 47)])
    z.block(10, 48, 3, 6, 'V', over=GROUND)
    z.block(15, 50, 2, 3, 'v', over=GROUND)
    z.block(8, 46, 2, 1, 'b', over=GROUND + ';')
    z.pf('Y', [(1, 1), (68, 1)])
    z.pf('y', [(1, 61), (68, 61)])
    for (c, r) in ((5, 2), (9, 2), (13, 2), (1, 20), (1, 24)):
        z.block(c, r, 2, 1, 'e', over=GROUND) if r < 5 else z.block(c, r, 1, 2, 'e', over=GROUND)
    z.cells('q', [(8, 5), (14, 6)])
    z.cells('p', [(6, 9), (16, 17), (3, 15), (18, 5), (12, 25)])
    z.cells('j', [(9, 15), (14, 10), (5, 22), (19, 21)])
    z.cells('c', [(12, 57), (13, 57), (7, 64), (16, 66)])
    z.cells('x', [(13, 58), (8, 64)])
    z.block(20, 66, 1, 2, 'e', over=GROUND)
    # east yard: the supply depot
    z.pf('F', [(62, 35), (66, 35)])
    z.pf('g', [(58, 37)])
    z.pf('z', [(53, 43), (58, 43), (63, 43)])
    z.pf('m', [(56, 29)])
    z.pf('N', [(53, 52), (59, 52)])
    z.cells('$', [(64, 52), (65, 52), (64, 53), (55, 38), (55, 39), (61, 31)])
    z.cells('d', [(60, 38), (60, 39), (68, 43), (69, 43), (51, 29)])
    z.cells('o', [(57, 33), (58, 33), (52, 40)])
    z.cells('c', [(52, 58), (53, 58), (66, 58), (60, 64), (61, 64)])
    z.block(56, 62, 2, 3, 'v', over=GROUND)
    # north-east yard: woodlots, firewood, a wagon, trees
    for (c, r) in ((53, 2), (57, 2), (61, 2)):
        z.block(c, r, 2, 1, 'e', over=GROUND)
    z.block(70, 20, 1, 2, 'e', over=GROUND)
    z.cells('q', [(56, 6)])
    z.block(60, 16, 3, 6, 'V', over=GROUND)
    z.cells('p', [(54, 18), (66, 10), (64, 24), (52, 25)])
    z.cells('j', [(58, 9), (62, 25), (68, 14)])
    z.cells('c', [(55, 22), (56, 22), (66, 28)])
    a = [(36, 20), (8, 56), (60, 47)]
    h = [(35, 45), (52, 10), (8, 26)]
    s = [(10, 10), (20, 30), (11, 36), (36, 8), (36, 28), (57, 9), (64, 20), (52, 34), (65, 62), (14, 60), (47, 25), (24, 49)]
    return finish(z, a, h, s, 0)


# ---------------------------------------------------------------- zone 2: the edge of the wild
def wild():
    z = FZone('frontier_2', 76, 72, 36, 31, 37)
    hf = None
    # the cliff lips on the plateau edges (west column, north row) and the ravine banks
    def lip(c, r, hi, lo):
        h = terrain_height(c + (1 if hi == '{' else 0), r + (1 if hi == '}' else 0), 1)
        if h >= 2.6:
            z.put(c, r, hi, over=',')
        elif h >= 0.6:
            z.put(c, r, lo, over=',')
    for r in range(1, 29):
        lip(1, r, '{', '[')
    for c in range(2, 30):
        lip(c, 1, '}', ']')
    for c in range(35, 58):
        lip(c, 1, '}', ']')
    # ravine: floor c 31..33 from the exit gate south; banks in c 30 (west) and c 34 (east), lower where the
    # plateaus fall away; the rope bridge at rows 10-11
    for r in range(1, 29):
        for c in (30, 34):
            hc = terrain_height(c if c == 30 else 35, r, 1)
            if r in (10, 11):
                continue
            if hc >= 1.75:
                z.put(c, r, 'R' if c == 30 else 'Q', over=',')
            elif hc >= 0.75:
                z.put(c, r, '(' if c == 30 else ')', over=',')
    z.pf('=', [(29, 10)], over=',')
    z.paint(31, 1, 3, 30, ':', over=',')
    # the creek: from the spring at the north wall down the east side and out under the south wall
    z.pf('Z', [(62, 1)], over=',')
    cre = {}
    for r in range(3, 71):
        cc = 63 + int(round(1.5 * math.sin(r / 8.0 + 1.0))) + (1 if r > 44 else 0)
        w = 3 if r < 50 else 4
        cre[r] = (cc, w)
    # sawmill, its water wheel and the flume (the wheel stands west of the creek; the flume feeds it from the spring)
    z.pf('I', [(47, 30)], over=',')
    z.pf('J', [(57, 31)], over=',')
    for r in range(3, 31, 4):
        z.block(58, r, 1, 4, '|', over=',')
    for r, (cc, w) in cre.items():
        for c in range(cc - (w - 1) // 2, cc - (w - 1) // 2 + w):
            if z.g[r][c] in ',.;:':
                z.g[r][c] = '~'
    # the mill yard: log decks, piles, lumber, the log arch, sawdust and crates
    z.pf('D', [(39, 30), (39, 34)], over=',')
    z.pf('7', [(48, 40), (40, 40)], over=',')
    z.pf('8', [(53, 40)], over=',')
    z.pfv('9', [(45, 30)], over=',')
    z.pf('&', [(44, 38)], over=',')
    z.cells('c', [(57, 38), (57, 39)], over=',')
    z.cells('d', [(47, 43)], over=',')
    z.pf('g', [(55, 43)], over=',')
    z.paint(38, 28, 20, 2, ';', over=',')
    z.paint(38, 38, 20, 6, ';', over=',')
    # logging camp in the south-west: cook shack, wall tents, the fire pit, sawhorse, tool rack, the camp sign
    z.pf('C', [(5, 45)], over=',')
    z.pf('3', [(13, 45), (18, 45)], over=',')
    z.pf('5', [(13, 53)], over=',')
    z.pf('6', [(19, 53)], over=',')
    z.pf('%', [(5, 52)], over=',')
    z.cells('!', [(24, 50)], over=',')
    z.pf('7', [(4, 58)], over=',')
    z.pfv('9', [(23, 55)], over=',')
    z.pf('0', [(9, 62)], over=',')
    z.cells('j', [(17, 59), (21, 63), (26, 60), (13, 66), (6, 66), (25, 66)], over=',')
    z.cells('c', [(11, 45), (11, 46), (23, 45)], over=',')
    z.cells('d', [(23, 46), (4, 51)], over=',')
    z.cells('q', [(10, 53)], over=',')
    z.paint(3, 43, 24, 15, ';', over=',')
    # the old mine in its outcrop on the west wall (low ground), ore and rails come out of it
    z.pf('*', [(1, 31)], over=',')
    z.cells('`', [(7, 33), (8, 38)], over=',')
    # west plateau: the lookout on the cliff edge, the lean-to, groves, boulders, a fallen tree, the trails up
    z.pf('X', [(2, 6)], over=',')
    z.pf('^', [(13, 3)], over=',')
    z.pf('+', [(24, 4)], over=',')
    z.pf('@', [(19, 8), (3, 16), (24, 14), (11, 22)], over=',')
    z.pf('1', [(14, 12), (7, 2), (26, 20)], over=',')
    z.pf('0', [(13, 17)], over=',')
    z.cells('p', [(18, 3), (26, 6), (8, 19), (21, 18)], over=',')
    z.cells('`', [(12, 8), (22, 11), (5, 25)], over=',')
    z.cells('$', [(17, 6), (18, 6)], over=',')
    # east plateau: groves, boulders, a felled log, the flume runs past its foot
    z.pf('@', [(37, 3), (46, 6), (52, 13), (40, 16)], over=',')
    z.pf('1', [(43, 13), (49, 3), (38, 6)], over=',')
    z.pfv('9', [(48, 18)], over=',')
    z.cells('p', [(54, 4), (38, 13), (45, 15), (53, 19)], over=',')
    z.cells('j', [(42, 8), (50, 9)], over=',')
    # the low ground: forest edges with groves, fallen trees, boulders, stumps, ferns; the trails
    z.pf('@', [(28, 40), (33, 46), (68, 46), (70, 56), (44, 60), (55, 64), (2, 40), (29, 64), (66, 20), (70, 28)], over=',')
    z.pf('0', [(40, 57), (55, 50), (66, 9)], over=',')
    z.pf('1', [(20, 37), (48, 54), (68, 64), (40, 66), (65, 36), (24, 30)], over=',')
    z.pfv('9', [(31, 57), (60, 57)], over=',')
    z.cells('p', [(35, 35), (27, 47), (45, 49), (52, 59), (59, 41), (71, 47), (49, 66), (34, 62), (16, 39), (68, 12), (72, 4), (66, 30)], over=',')
    z.cells('j', [(38, 57), (52, 47), (47, 63), (59, 61)], over=',')
    z.cells('`', [(42, 48), (50, 56), (36, 41), (63, 54)], over=',')
    z.cells("'", [(31, 37), (42, 55), (57, 47), (26, 52), (70, 40), (46, 44), (19, 34), (66, 15), (37, 61), (61, 67)], over=GROUND)
    # trails: from the entry up to the ravine mouth and the plateaus, west to the camp, east to the mill
    z.paint(35, 44, 5, 27, ':', over=',')
    z.paint(31, 28, 9, 17, ':', over=',')
    z.paint(18, 22, 13, 4, ':', over=',')
    z.paint(14, 26, 6, 18, ':', over=',')
    z.paint(14, 15, 5, 9, ':', over=',')
    z.paint(9, 13, 6, 3, ':', over=',')
    z.paint(36, 22, 10, 4, ':', over=',')
    z.paint(40, 44, 16, 3, ':', over=',')
    z.paint(20, 49, 15, 3, ':', over=',')
    a = [(32, 18), (60, 44), (10, 55)]
    h = [(48, 22), (16, 10), (38, 50)]
    s = [(50, 25), (26, 34), (12, 36), (22, 42), (8, 50), (28, 57), (46, 46), (52, 52), (64, 60), (42, 28), (55, 25), (18, 64)]
    return finish(z, a, h, s, 1)


def nearest(z, c0, r0, test):
    """the open cell nearest (c0, r0) that passes test(c, r)"""
    best = None
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if test(c, r):
                d = (c - c0) ** 2 + (r - r0) ** 2
                if best is None or d < best[0]:
                    best = (d, c, r)
    return best[1], best[2]


def finish(z, ammo, health, spawns, zi):
    hf = eased(z, zi) if zi == 1 else None
    P = [(c, r) for r in range(z.h) for c in range(z.w) if z.g[r][c] == 'P'][0]
    def level(c, r):
        return hf is None or max(hf[r][c], hf[r][c + 1], hf[r + 1][c], hf[r + 1][c + 1]) < 0.01
    for (c, r) in ammo + health:
        cc, rr = nearest(z, c, r, lambda x, y: z.g[y][x] in GROUND)
        z.put(cc, rr, 'a' if (c, r) in ammo else 'h', over=GROUND)
    for (c, r) in spawns:
        def ok(x, y):
            if (x - P[0]) ** 2 + (y - P[1]) ** 2 < 15 ** 2:
                return False
            if any(z.g[y + dy][x + dx] not in GROUND for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                return False
            # level ground, and a spawn's flat pin must not pull a slope next to it out of shape
            return all(level(x + dx, y + dy) for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)
                       if 0 < x + dx < z.w - 1 and 0 < y + dy < z.h - 1)
        cc, rr = nearest(z, c, r, ok)
        z.put(cc, rr, 'S', over=GROUND)
    pre = {ch: PREFAB[ch] for ch in PREFAB}
    errs, stats = validate(z, WALK, pre, size=((70, 78), (68, 74)))
    errs += terrain_checks(z, zi)
    return z, errs, stats


def terrain_checks(z, zi):
    """zone 2: open ground climbable by robots (a 0.4 m step per 0.5 m nav cell, so <= 0.8 m per metre) except the
    cells walled off by lips and banks, nothing standing on a slope that must be level, spawns on level ground"""
    errs = []
    if zi != 1:
        return errs
    hf = eased(z, zi)
    steep = 0
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            ch = z.g[r][c]
            corners = [hf[r][c], hf[r][c + 1], hf[r + 1][c], hf[r + 1][c + 1]]
            if (ch in WALK or ch in 'Sah') and ch != '=':
                a, b, d, e = corners
                edge = max(abs(a - b), abs(d - e), abs(a - d), abs(b - e))
                diag = max(abs(a - e), abs(b - d))
                if edge > 0.75 or diag > 1.0:
                    steep += 1
                    if steep < 6:
                        errs.append('steep open cell (%d,%d) %.2f / %.2f' % (c, r, edge, diag))
            if ch in FLAT and max(corners) > 0.05:
                errs.append('level prefab %r on a slope at (%d,%d)' % (ch, c, r))
            if ch == 'S' and max(corners) > 0.01:
                errs.append('spawn (%d,%d) off the level ground' % (c, r))
    # the bridge ends land on the plateau (3.2) and its middle stands on the ravine floor (0)
    for (c, r, w, h) in rects(z.g, '='):
        if abs(hf[r][c] - PLAT) > 0.01 or abs(hf[r][c + w] - PLAT) > 0.01 or hf[r][c + 3] > 0.01:
            errs.append('bridge ends %.2f / %.2f, middle %.2f' % (hf[r][c], hf[r][c + w], hf[r][c + 3]))
    for (c, r, w, h) in rects(z.g, 'X'):
        if any(abs(hf[rr][cc] - PLAT) > 0.01 for rr in range(r, r + h + 1) for cc in range(c, c + w + 1)):
            errs.append('lookout off the plateau top')
    return errs


def main():
    zones = [settlement(), wild()]
    ok = write(zones, check_only=True)
    if '--check' not in sys.argv:
        for z, _, _ in zones:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
    if '--print' in sys.argv:
        for z, _, _ in zones:
            print('\n' + z.text())
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
