"""The Aurelian zone maps (src/data/zones/hotel_{lobby,ballroom,sky}.txt), written from scratch by this script.

Each zone is a floor plan plus "@layer" grids (zones.js): "@layer 0" floor finishes (carpets, the medallion, the dance
floor, the pool deck, the suites' number plates), "@layer 4.5" the lobby's mezzanine gallery, "@layer 9" the ceiling
fittings (coffers, chandeliers, downlights) or the sky deck's glass roof. Widths are odd so the gates sit on the
centre line; the lobby and ballroom facades run in 3 m window bays from the gates and the corners (heights 3n), the
sky deck's glass roof tiles are 7 m (51 x 51). The layouts are laid out by hand below; the dressing that follows
from them (rails and columns on the gallery edge, lights, coffers, plates) is derived. A check mirrors the unit test.
Run: python3 tools/hotel_zones.py [--print]
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ZD = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))

PREFAB = {'Z': (4, 10), 'R': (6, 4), 'Q': (3, 2), 'X': (8, 4), 'L': (4, 3), 'K': (3, 3), 'F': (3, 3), 'O': (2, 1),
          'k': (2, 1), 'w': (2, 1), 'T': (3, 3), 'D': (9, 4), 'y': (2, 1), 'v': (2, 1), 'M': (6, 6), 'N': (6, 6),
          'W': (6, 6), 'B': (10, 4), 'l': (1, 2), 'A': (3, 3), 'V': (7, 7), 'f': (2, 2), 'o': (2, 2), 'J': (5, 4),
          'd': (5, 3), 'z': (4, 4), 'g': (3, 1),
          'x': (7, 7), '_': (3, 1), '!': (4, 4), '+': (4, 4), '&': (4, 4), '%': (3, 3), '$': (4, 4),
          '~': (4, 4), 'H': (5, 5), 'Y': (3, 3), '^': (7, 7)}
STAIRS = 'Z'
GROUND_OPEN = set('.ahPn')
DECK_OPEN = set('m;ah')
SUITES = 'MNW'


class Zone:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.g = [['.'] * w for _ in range(h)]
        for c in range(w):
            self.g[0][c] = self.g[h - 1][c] = '#'
        for r in range(h):
            self.g[r][0] = self.g[r][w - 1] = '#'
        self.layers = {}

    def layer(self, y):
        if y not in self.layers:
            L = [['.'] * self.w for _ in range(self.h)]
            if y != '0':
                for c in range(self.w):
                    L[0][c] = L[self.h - 1][c] = '#'
                for r in range(self.h):
                    L[r][0] = L[r][self.w - 1] = '#'
            self.layers[y] = L
        return self.layers[y]

    def put(self, c, r, ch, grid=None, over='.'):
        g = self.g if grid is None else grid
        assert 0 <= c < self.w and 0 <= r < self.h, (self.name, c, r, ch)
        assert g[r][c] in over, '%s: (%d,%d) is %r, placing %r' % (self.name, c, r, g[r][c], ch)
        g[r][c] = ch

    def block(self, c0, r0, w, h, ch, grid=None, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.put(c, r, ch, grid, over)

    def wall(self, c0, r0, w, h):
        self.block(c0, r0, w, h, '#', over='.#')

    def gates(self, gc):
        for k in range(3):
            self.g[0][gc + k] = 'G'
            self.g[self.h - 1][gc + k] = 'E'

    def text(self):
        out = [''.join(row) for row in self.g]
        for y in sorted(self.layers, key=float):
            out.append('@layer ' + y)
            out += [''.join(row) for row in self.layers[y]]
        return '\n'.join(out) + '\n'


def rects(g, ch):
    H, W = len(g), len(g[0])
    used = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if used[r][c] or g[r][c] != ch:
                continue
            w = 1
            while c + w < W and not used[r][c + w] and g[r][c + w] == ch:
                w += 1
            h, ok = 1, True
            while ok and r + h < H:
                for k in range(w):
                    if used[r + h][c + k] or g[r + h][c + k] != ch:
                        ok = False
                        break
                if ok:
                    h += 1
            for y in range(h):
                for x in range(w):
                    used[r + y][c + x] = True
            out.append((c, r, w, h))
    return out


def tiles(z, grid, ch, c0, r0, nx, ny, size=4, avoid=''):
    """size x size tiles from (c0, r0); a tile is left out where it would cover a wall or a cell of `avoid` on the
    plan, or anything already on its own layer."""
    for ty in range(ny):
        for tx in range(nx):
            cs = [(c0 + tx * size + i, r0 + ty * size + j) for i in range(size) for j in range(size)]
            if any(z.g[r][c] == '#' or z.g[r][c] in avoid or grid[r][c] != '.' for (c, r) in cs):
                continue
            for (c, r) in cs:
                grid[r][c] = ch


# ------------------------------------------------------------------ Grand Lobby (street level)
def lobby():
    z = Zone('hotel_lobby', 57, 51)
    z.gates(27)
    mez = z.layer('4.5')
    # the gallery: north (rows 1-9) and down both sides (cols 1-8 / 48-55, rows 10-24); rails on its open edge
    for r in range(1, 50):
        for c in range(1, 56):
            if r <= 9 or (r <= 24 and (c <= 8 or c >= 48)):
                mez[r][c] = 'm'
    for r in range(1, 50):
        for c in range(1, 56):
            if mez[r][c] == 'm' and any(mez[r + dr][c + dc] == '.' for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))):
                mez[r][c] = 'r'
    # two grand stairs rise north to the gallery, either side of the way to the service stair
    for c0 in (16, 37):
        z.block(c0, 10, 4, 10, 'Z')
        for c in range(c0, c0 + 4):
            assert mez[9][c] == 'r', (c, mez[9][c])
            mez[9][c] = 'm'
    # columns under / over the gallery edge
    for (c, r) in ((8, 9), (13, 9), (23, 9), (33, 9), (43, 9), (48, 9), (8, 14), (8, 19), (8, 24), (48, 14), (48, 19), (48, 24),
                   (3, 24), (53, 24)):
        assert mez[r][c] == 'r', (c, r, mez[r][c])
        mez[r][c] = 'i'
        z.put(c, r, 'I')
    # under the north gallery: the lift lobby (lifts in the north wall), ottomans and palms, the way to the stair door
    for (c, r) in ((4, 2), (52, 2), (14, 2), (42, 2)):
        z.put(c, r, 'p')
    for (c, r) in ((9, 5), (46, 5)):
        z.block(c, r, 2, 1, 'O')
    for (c, r) in ((20, 4), (35, 4)):
        z.block(c, r, 2, 1, 'O')
    # reception under the west gallery (its back to the windows), concierge by the door
    z.block(1, 13, 4, 6, 'R')
    z.block(6, 37, 3, 2, 'Q')
    # the Gilt Bar under the east gallery, its back to the east windows, stools along the counter
    z.block(52, 12, 4, 8, 'X')
    for r in range(12, 20):
        if r % 2 == 0:
            z.put(51, r, 'b')
    # centre: the flower table on the medallion under the great chandelier, ottomans round it
    z.block(27, 29, 3, 3, 'F')
    for (c, r) in ((25, 26), (30, 26), (25, 34), (30, 34)):
        z.block(c, r, 2, 1, 'O')
    # lounges either side of the centre, a grand piano by the bar
    for (c, r) in ((10, 27), (10, 33), (43, 27), (43, 33)):
        z.block(c, r, 4, 3, 'L')
    z.block(51, 28, 3, 3, 'K')
    # the entrance: palms by the doors, the bell captain, luggage carts, topiaries along the windows
    for (c, r) in ((24, 49), (32, 49)):
        z.put(c, r, 'p')
    z.put(22, 45, 'j')
    for (c, r) in ((17, 48), (40, 48), (2, 30), (54, 36)):
        z.put(c, r, 'c')
    for (c, r) in ((2, 39), (2, 45), (54, 42), (54, 46), (14, 49), (42, 49), (2, 26), (54, 26)):
        z.put(c, r, 't')
    for (c, r) in ((19, 40), (37, 40)):
        z.block(c, r, 2, 1, 'O')
    z.put(28, 48, 'P')
    for (c, r) in ((5, 8), (51, 8), (20, 24), (36, 24), (5, 30), (51, 32), (16, 38), (40, 38), (12, 22), (44, 22)):
        z.put(c, r, 'S')
    z.put(15, 31, 'a')
    z.put(46, 40, 'h')
    # gallery: lounges and writing desks along the north wall, palms, spawns and pickups upstairs
    for (c, r) in ((9, 2), (44, 2)):
        z.block(c, r, 4, 3, 'L', mez, 'm')
    for (c, r) in ((22, 1), (33, 1)):
        z.block(c, r, 2, 1, 'w', mez, 'm')
    for (c, r) in ((2, 2), (54, 2), (27, 2), (29, 2), (2, 12), (54, 12), (2, 20), (54, 20)):
        z.put(c, r, 'p', mez, 'm')
    for (c, r) in ((4, 16), (52, 16), (17, 4), (39, 4)):
        z.put(c, r, 'S', mez, 'm')
    z.put(4, 21, 'h', mez, 'm')
    z.put(50, 6, 'a', mez, 'm')
    for r in range(1, 50):     # under-deck lights in the gallery's slab
        for c in range(1, 56):
            if mez[r][c] == 'm' and z.g[r][c] == '.' and ((r in (3, 7) and c % 4 == 2) or (c in (4,) and r % 4 == 0 and r > 9) or (c == 52 and r % 4 == 0 and r > 9)):
                mez[r][c] = ';'
    # floor: the medallion, a border band at the gallery edge, lounge carpets, a runner from the door
    fl = z.layer('0')
    z.block(25, 27, 7, 7, 'x', fl, '.FO')
    for c0, r0 in ((10, 26), (10, 32), (43, 26), (43, 32), (5, 13), (5, 17)):
        for r in range(r0, r0 + 4):
            for c in range(c0, c0 + 4):
                assert fl[r][c] == '.', (c, r)
                fl[r][c] = '!'
    z.block(27, 36, 3, 14, '_', fl)
    # ceiling: coffers over the hall, the great chandelier, smaller ones over the lounges and the door, downlights
    rf = z.layer('9')
    z.block(26, 28, 5, 5, 'H', rf)
    for (c, r) in ((11, 30), (44, 30), (27, 41)):
        z.block(c, r, 3, 3, 'Y', rf)
    tiles(z, rf, '~', 9, 25, 10, 6)
    for r in range(1, 50):
        for c in range(1, 56):
            if rf[r][c] == '.' and z.g[r][c] != '#' and (((r in (3, 7)) and c % 4 == 0) or (c in (3, 6, 50, 53) and r % 4 == 1 and r > 9 and r < 25)):
                rf[r][c] = ':'
    return z


# ------------------------------------------------------------------ Floor 24: the Crystal Ballroom and the suites
SUITE_ROWS = [2 + 7 * i for i in range(7)]
SUITE_KIND = 'MNWMWNM'


def ballroom():
    z = Zone('hotel_ballroom', 57, 57)
    z.gates(27)
    g = z.g
    # west band: seven open suites (cols 1-6) behind the corridor wall (col 7), party walls between them
    z.wall(1, 1, 7, 1)
    for i, r0 in enumerate(SUITE_ROWS):
        z.block(1, r0, 6, 6, SUITE_KIND[i])
        for r in range(r0, r0 + 6):
            g[r][7] = 'n' if r in (r0 + 2, r0 + 3) else '#'
        z.wall(1, r0 + 6, 7, 1)
    # the ballroom (cols 12-44, rows 6-40), doors on its west, east and south sides
    z.wall(12, 6, 33, 1)
    z.wall(12, 40, 33, 1)
    z.wall(12, 6, 1, 35)
    z.wall(44, 6, 1, 35)
    for (c, r0) in ((12, 14), (12, 29), (44, 14), (44, 29)):
        for r in range(r0, r0 + 4):
            g[r][c] = 'n'
    for c in range(26, 31):
        g[40][c] = 'n'
    # inside: the bandstand on the north wall, the dance floor, banquet tables round it
    z.block(24, 7, 9, 4, 'D')
    for (c, r) in ((14, 12), (18, 12), (37, 12), (40, 12),
                   (14, 18), (40, 18), (14, 24), (40, 24), (14, 30), (40, 30), (14, 36), (40, 36),
                   (19, 33), (24, 35), (31, 35), (36, 33), (19, 17), (35, 17)):
        z.block(c, r, 3, 3, 'T')
    for (c, r) in ((22, 11), (34, 11)):
        z.put(c, r, 'p')
    # corridor (cols 8-11): housekeeping and room service at work
    for (c, r, ch) in ((9, 12, 'y'), (9, 33, 'v'), (9, 47, 'y')):
        z.block(c, r, 1, 2, ch)
    # north strip (rows 1-5): the back-of-house way to the service stair
    for (c, r, ch) in ((15, 2, 'v'), (39, 2, 'y'), (20, 4, 'v')):
        z.block(c, r, 2, 1, ch)
    for (c, r) in ((13, 4), (43, 4), (24, 2), (32, 2)):
        z.put(c, r, 'p')
    # east foyer (cols 45-55): lounges by the windows, palms, consoles, the event easel by the doors
    for (c, r) in ((49, 3), (49, 21), (49, 25), (49, 44)):
        z.block(c, r, 4, 3, 'L')
    for (c, r) in ((46, 12), (46, 34)):
        z.put(c, r, 'e')
    for (c, r) in ((54, 10), (54, 16), (54, 31), (54, 37), (46, 52), (54, 52)):
        z.put(c, r, 'p')
    for (c, r) in ((53, 12), (53, 33)):
        z.block(c, r, 1, 2, 'v' if r == 33 else 'y')
    # south: the lift lobby off the service stair, consoles and ottomans, the ballroom's main doors
    for (c, r) in ((14, 55), (41, 55)):
        z.block(c, r, 2, 1, 'k')
    for (c, r) in ((22, 45), (33, 45), (16, 48), (39, 48)):
        z.block(c, r, 2, 1, 'O')
    for (c, r) in ((14, 42), (42, 42), (25, 42), (31, 42)):
        z.put(c, r, 'p')
    z.block(2, 52, 2, 1, 'y')
    z.put(28, 54, 'P')
    for (c, r) in ((10, 6), (10, 26), (10, 40), (28, 3), (50, 8), (50, 30), (50, 49), (28, 21), (20, 28), (36, 28), (10, 52)):
        z.put(c, r, 'S')
    z.put(17, 22, 'a')
    z.put(47, 40, 'a')
    z.put(39, 22, 'h')
    z.put(4, 53, 'h')
    # floor: corridor and foyer carpets, the dance floor, suite plates
    fl = z.layer('0')
    for r0 in range(1, 53, 4):
        for c0 in (8,):
            if all(g[r][c] != '#' for r in range(r0, r0 + 4) for c in range(c0, c0 + 4)):
                z.block(c0, r0, 4, 4, '+', fl)
    for r0 in range(1, 53, 4):
        for c0 in (45, 49):
            if all(g[r][c] not in '#' for r in range(r0, r0 + 4) for c in range(c0, c0 + 4)) and all(fl[r][c] == '.' for r in range(r0, r0 + 4) for c in range(c0, c0 + 4)):
                z.block(c0, r0, 4, 4, '+', fl)
    z.block(21, 20, 15, 9, '%', fl)
    plates = z.layer('0.01')
    for i, r0 in enumerate(SUITE_ROWS[:6]):
        plates[r0 + 1][8] = str(i + 1)
    # ceiling: the ballroom's chandeliers, coffers over the dance floor, downlights in the corridor and the foyer
    rf = z.layer('9')
    z.block(26, 23, 5, 5, 'H', rf)
    for (c, r) in ((15, 13), (39, 13), (15, 31), (39, 31), (27, 15), (27, 33)):
        z.block(c, r, 3, 3, 'Y', rf)
    tiles(z, rf, '~', 13, 7, 8, 8, avoid='D')
    for r in range(1, 56):
        for c in range(1, 56):
            if rf[r][c] == '.' and g[r][c] not in '#' + SUITES and ((c in (9, 10) and r % 3 == 1) or (c in (47, 52) and r % 4 == 2) or (r in (3,) and c % 4 == 1) or (r in (48, 52) and c % 4 == 3 and c > 12 and c < 44)):
                rf[r][c] = ':'
    return z


# ------------------------------------------------------------------ Floor 56: the penthouse and the sky deck
def sky():
    z = Zone('hotel_sky', 51, 51)
    z.gates(24)
    g = z.g
    # the penthouse (west, cols 1-20): partitions with wide openings: library / bedroom (north), dining, living
    z.wall(21, 1, 1, 13)
    z.wall(21, 19, 1, 13)
    z.wall(21, 37, 1, 7)
    z.wall(1, 17, 7, 1)
    z.wall(13, 17, 8, 1)
    z.wall(1, 33, 5, 1)
    z.wall(11, 33, 10, 1)
    z.block(3, 1, 4, 4, 'z')
    z.block(9, 1, 3, 1, 'g')
    z.block(14, 8, 5, 4, 'J')
    z.block(5, 23, 5, 3, 'd')
    z.block(14, 18, 3, 1, 'g')
    z.block(3, 38, 5, 4, 'J')
    z.block(12, 39, 3, 3, 'K')
    for (c, r) in ((1, 13), (19, 2), (1, 30), (19, 30), (1, 47), (19, 47)):
        z.put(c, r, 'p')
    z.put(2, 10, 'q')
    z.put(3, 48, 'q')
    # the sky deck (east): the infinity pool on the east glass, loungers and parasols, cabanas, olives, hedges
    z.block(40, 18, 4, 10, 'B')
    for r in (18, 21, 24):
        z.block(36, r, 1, 2, 'l')
        z.block(37, r, 1, 2, 'l')
    for (c, r) in ((35, 18), (35, 24)):
        z.put(c, r, 'u')
    z.block(47, 4, 3, 3, 'A')
    z.block(47, 41, 3, 3, 'A')
    for (c, r) in ((29, 3), (39, 9), (39, 40), (29, 46), (24, 30), (24, 38)):
        z.block(c, r, 2, 2, 'o')
    for c in range(30, 36):
        z.put(c, 33, '=')
    for c in range(40, 46):
        z.put(c, 33, '=')
    # the sky bar in the middle of the deck, fire tables and lounges round it
    z.block(22, 7, 7, 7, 'V')
    for (c, r) in ((33, 8), (33, 13)):
        z.block(c, r, 2, 2, 'f')
    z.block(30, 40, 4, 3, 'L')
    z.block(41, 45, 4, 3, 'L')
    for (c, r) in ((49, 30), (49, 13), (29, 48)):
        if g[r][c] == '.':
            z.put(c, r, 'p')
    z.put(25, 48, 'P')
    for (c, r) in ((4, 14), (11, 21), (4, 29), (11, 44), (17, 27), (33, 4), (44, 12), (32, 28), (46, 30), (39, 36), (46, 37), (30, 18)):
        z.put(c, r, 'S')
    z.put(16, 14, 'a')
    z.put(35, 45, 'a')
    z.put(9, 30, 'h')
    z.put(46, 16, 'h')
    # floor: penthouse carpets, teak round the pool, the bar's medallion
    fl = z.layer('0')
    for (c0, r0, nx, ny) in ((1, 1, 5, 4), (1, 18, 5, 4), (1, 34, 5, 4)):
        tiles(z, fl, '&', c0, r0, nx, ny, avoid='')
    tiles(z, fl, '$', 34, 14, 4, 5)
    # roof: glazed pyramids over the whole zone
    rf = z.layer('9')
    for ty in range(7):
        for tx in range(7):
            z.block(1 + tx * 7, 1 + ty * 7, 7, 7, '^', rf)
    return z


# ------------------------------------------------------------------ checks
def check(z):
    errs = []
    g, W, H = z.g, z.w, z.h
    mez = z.layers.get('4.5')
    at = lambda c, r: g[r][c] if 0 <= c < W and 0 <= r < H else '#'
    mt = lambda c, r: (mez[r][c] if mez and 0 <= c < W and 0 <= r < H else '#')
    G = [c for c in range(W) if g[0][c] == 'G']
    E = [c for c in range(W) if g[H - 1][c] == 'E']
    if len(G) != 3 or G[2] - G[0] != 2 or len(E) != 3 or E[2] - E[0] != 2:
        errs.append('gates')
    if (G[0] + G[2] + 1) / 2 != W / 2:
        errs.append('gate off the centre line')
    for c in G:
        if at(c, 1) not in GROUND_OPEN or at(c, 2) not in GROUND_OPEN:
            errs.append('exit gate needs 2 open rows')
    for c in E:
        if at(c, H - 2) not in GROUND_OPEN or at(c, H - 3) not in GROUND_OPEN:
            errs.append('entry gate needs 2 open rows')
    P = [(c, r) for r in range(H) for c in range(W) if g[r][c] == 'P']
    if len(P) != 1:
        return ['need one P']
    P = P[0]
    for dc in (-2, -1, 1, 2):
        if at(P[0] + dc, P[1] - 4) not in GROUND_OPEN:
            errs.append('weapon stand cell blocked')
    links = []
    for (c, r, w, h) in rects(g, 'Z'):
        for cc in range(c, c + w):
            a, b = (cc, r + h), (cc, r - 1)
            if at(*a) not in GROUND_OPEN or mt(*b) not in DECK_OPEN:
                errs.append('stair end blocked %s %s' % (a, b))
            links.append((a, b))
    seen = {(0,) + P}
    q = deque([(0,) + P])
    while q:
        L, c, r = q.popleft()
        nb = [(L, c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        for a, b in links:
            if L == 0 and (c, r) == a:
                nb.append((1,) + b)
            if L == 1 and (c, r) == b:
                nb.append((0,) + a)
        for n in nb:
            if n in seen:
                continue
            ok = at(n[1], n[2]) in GROUND_OPEN if n[0] == 0 else mt(n[1], n[2]) in DECK_OPEN
            if ok:
                seen.add(n)
                q.append(n)
    sealed = [(c, r) for r in range(H) for c in range(W) if g[r][c] in GROUND_OPEN and (0, c, r) not in seen]
    if sealed:
        errs.append('%d sealed ground cells %s' % (len(sealed), sealed[:5]))
    if mez:
        ds = [(c, r) for r in range(H) for c in range(W) if mez[r][c] in DECK_OPEN and (1, c, r) not in seen]
        if ds:
            errs.append('%d sealed deck cells %s' % (len(ds), ds[:5]))
    if not any((0, c, 1) in seen for c in G):
        errs.append('no path to the exit')
    nS = 0
    for (L, grid, OPEN) in ((0, g, GROUND_OPEN), (1, mez, DECK_OPEN)):
        if grid is None:
            continue
        for r in range(H):
            for c in range(W):
                if grid[r][c] != 'S':
                    continue
                nS += 1
                if L == 0 and (c - P[0]) ** 2 + (r - P[1]) ** 2 < 14 ** 2:
                    errs.append('spawn (%d,%d) < 14 m from P' % (c, r))
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if (dc or dr) and grid[r + dr][c + dc] not in OPEN - set('n'):
                            errs.append('spawn (%d,%d) L%d neighbour %r' % (c, r, L, grid[r + dr][c + dc]))
                if L == 1 and g[r][c] in STAIRS:
                    errs.append('deck spawn over a stair')
    if not 10 <= nS <= 16:
        errs.append('%d spawns' % nS)
    na = sum(row.count('a') for grid in [g] + ([mez] if mez else []) for row in grid)
    nh = sum(row.count('h') for grid in [g] + ([mez] if mez else []) for row in grid)
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for grid in [g] + list(z.layers.values()):
        for ch, (sw, sd) in PREFAB.items():
            for (c, r, w, h) in rects(grid, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('prefab %r %dx%d at (%d,%d)' % (ch, w, h, c, r))
    if mez:
        for r in range(H):
            for c in range(W):
                if mez[r][c] not in '.#mr;i' and g[r][c] in STAIRS:
                    errs.append('deck prop over a stair (%d,%d)' % (c, r))
    return errs


def main():
    ok = True
    for z in (lobby(), ballroom(), sky()):
        errs = check(z)
        print('%-16s %dx%d  %s' % (z.name, z.w, z.h, 'ok' if not errs else ''))
        for e in errs:
            print('   ERROR', e)
            ok = False
        with open(os.path.join(ZD, z.name + '.txt'), 'w') as f:
            f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
