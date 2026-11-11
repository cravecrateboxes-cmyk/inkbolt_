"""NOVYX HQ zone maps (src/data/zones/techhq_{lobby,eng,lab}.txt), written from scratch by this script.

A tech company's headquarters on floors 27-33 of a mid-rise tower. Every zone is a double-height floor (8 m) in a
glass curtain wall; a mezzanine deck at 4 m ("@layer 4") runs along part of it. Layers: "@layer 0" floor finishes
(carpet tiles, epoxy, terrace decking and pavers), "@layer 4" the deck and what stands on it, "@layer 8" ceiling
fittings (felt baffles, pendants) or, in the lab, the roof tiles over the indoor part (the terrace is open to the sky).
Sizes are 62 wide (60 inside: 3 m facade bays and 4 m ceiling tiles both run evenly). The layouts are laid out by hand
below; the dressing that follows from them (rails along the deck edge, columns under and over it, under-deck lights,
ceiling tiles, pendants) is derived. A check mirrors the unit test: gates, one P, reachability on both floors (stairs
link them), spawn cans with open ground round them, pickups, prefab tiling.
Run: python3 tools/techhq_zones.py [--print]
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ZD = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))

PREFAB = {'N': (3, 10), 'V': (3, 10), 'Z': (10, 10), 'R': (6, 3), 'Y': (14, 2), 'K': (8, 3), 'D': (4, 2), 'A': (3, 1),
          'L': (4, 3), 'O': (2, 2), 'X': (4, 2), 'B': (2, 1), 'Q': (6, 4), 'T': (3, 2), 'F': (2, 1), 'H': (4, 3),
          'M': (4, 4), 'm': (2, 2), 'C': (4, 2), 'J': (4, 2), 'W': (2, 2), 'U': (2, 2), 'c': (6, 6), 'x': (4, 2),
          's': (2, 1), 't': (3, 3), 'v': (4, 3), '!': (2, 2), '?': (6, 4), '[': (4, 3), ']': (8, 6),
          'q': (4, 4), 'w': (4, 4), 'z': (4, 3), 'y': (4, 4), '~': (4, 4), '^': (4, 4), '&': (8, 8)}
STAIRS = 'NVZ'
GROUND_OPEN = set('.ahPn')
DECK_OPEN = set('ulah')
DECK_Y = '4'


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
        assert 0 < c < self.w - 1 and 0 < r < self.h - 1, (self.name, c, r, ch)
        assert g[r][c] in over, '%s: (%d,%d) is %r, placing %r' % (self.name, c, r, g[r][c], ch)
        g[r][c] = ch

    def puts(self, pts, ch, grid=None, over='.'):
        for (c, r) in pts:
            self.put(c, r, ch, grid, over)

    def block(self, c0, r0, w, h, ch, grid=None, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.put(c, r, ch, grid, over)

    def gates(self, gc, ec):
        for k in range(3):
            self.g[0][gc + k] = 'G'
            self.g[self.h - 1][ec + k] = 'E'

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


# ------------------------------------------------------------------ derived dressing
def deck(z, mask, gaps):
    """Deck on every interior cell where mask(c, r); rails on deck cells next to open interior floor that is not deck
    (8-neighbourhood), except the gaps where stairs land."""
    mez = z.layer(DECK_Y)
    inside = lambda c, r: 0 < c < z.w - 1 and 0 < r < z.h - 1
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if mask(c, r) and z.g[r][c] != '#':
                mez[r][c] = 'u'
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if mez[r][c] != 'u':
                continue
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                cc, rr = c + dc, r + dr
                if inside(cc, rr) and mez[rr][cc] not in 'ur' and z.g[rr][cc] != '#':
                    mez[r][c] = 'r'
                    break
    for (c, r) in gaps:
        assert mez[r][c] == 'r', (z.name, c, r, mez[r][c])
        mez[r][c] = 'u'
    return mez


def columns(z, mez, spots):
    for (c, r) in spots:
        assert mez[r][c] == 'r' and z.g[r][c] == '.', (z.name, c, r, mez[r][c], z.g[r][c])
        mez[r][c] = 'i'
        z.g[r][c] = 'I'


def under_lights(z, mez, every=4):
    """A downlight under the deck every few metres on open ground (not on rails or props)."""
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if mez[r][c] == 'u' and z.g[r][c] == '.' and c % every == 2 and r % every == 2:
                mez[r][c] = 'l'


def tiles(z, grid, ch, c0, r0, nx, ny, skip=(), solid='#', checker=False):
    for ty in range(ny):
        for tx in range(nx):
            if (tx, ty) in skip or (checker and (tx + ty) % 2):
                continue
            cells = [(c0 + tx * 4 + i, r0 + ty * 4 + j) for j in range(4) for i in range(4)]
            if any(z.g[r][c] in solid for (c, r) in cells) or any(grid[r][c] != '.' for (c, r) in cells):
                continue
            z.block(c0 + tx * 4, r0 + ty * 4, 4, 4, ch, grid)


def pendants(z, rf, mez, cells):
    for (c, r) in cells:
        if rf[r][c] == '.' and z.g[r][c] != '#' and (mez is None or mez[r][c] == '.'):
            rf[r][c] = ':'


# ------------------------------------------------------------------ zone 1: reception and showroom (floor 27)
def lobby():
    z = Zone('techhq_lobby', 62, 50)
    z.gates(29, 29)
    W, Hh = z.w, z.h
    # the U-shaped mezzanine: north deck over rows 1-11, galleries over the west / east walls to row 30
    mez = deck(z, lambda c, r: r <= 11 or (r <= 30 and (c <= 6 or c >= 55)),
               [(c, 11) for c in list(range(26, 36)) + [7, 8, 9, 52, 53, 54]])
    # ways up: the bleacher stair in the middle (town-hall seating facing the stage), oak stairs by the galleries
    z.block(26, 12, 10, 10, 'Z')
    z.block(7, 12, 3, 10, 'N')
    z.block(52, 12, 3, 10, 'N')
    columns(z, mez, [(13, 11), (20, 11), (41, 11), (48, 11), (6, 24), (55, 24), (6, 30), (55, 30), (6, 11), (55, 11)])
    # arrival: reception in front of the entry, the logo wall behind it (its back is the stage's video wall),
    # the demo stage facing the bleacher
    z.block(28, 39, 6, 3, 'R')
    z.block(24, 35, 14, 2, 'Y')
    z.block(27, 32, 8, 3, 'K')
    # west showroom: display tables with open laptops, plinths, accessory shelves under the gallery
    for r in (24, 30, 36):
        z.block(12, r, 4, 2, 'D')
        z.block(18, r, 4, 2, 'D')
    z.puts([(10, 27), (23, 27), (10, 33), (23, 33)], 'd')
    for r in (14, 18, 22, 26):
        z.block(1, r, 1, 3, 'A')
    # east: lounge and beanbags by the windows, more tables, shelves under the gallery
    for r in (30, 36):
        z.block(40, r, 4, 2, 'D')
        z.block(46, r, 4, 2, 'D')
    z.block(42, 41, 4, 3, 'L')
    z.block(49, 41, 4, 3, 'L')
    z.puts([(41, 25), (43, 26), (45, 24), (47, 26)], 'b')
    for r in (14, 18, 22, 26):
        z.block(60, r, 1, 3, 'A')
    # entry court: big planters, plants in the corners, benches of plinths
    z.block(20, 41, 2, 2, 'O')
    z.block(40, 45, 2, 2, 'O')
    z.puts([(24, 44), (37, 44), (2, 47), (59, 47), (2, 33), (59, 33), (8, 47), (53, 47)], 'p')
    z.puts([(14, 44), (17, 44)], 'o')
    # under the north deck: the heritage line of plinths (west), glass briefing pods, the espresso bar (east)
    z.puts([(4, 2), (7, 2), (10, 2), (13, 2), (16, 2), (19, 2)], 'd')
    z.block(3, 5, 4, 4, 'M')
    z.block(11, 5, 4, 4, 'M')
    for c in range(42, 54):
        z.put(c, 1, 'k')
    z.block(44, 5, 4, 2, 'C')
    z.block(50, 5, 4, 2, 'C')
    z.puts([(23, 3), (38, 3)], 'o')
    z.put(30, 47, 'P')
    for (c, r) in ((16, 15), (45, 15), (21, 22), (40, 22), (4, 40), (57, 40), (13, 41), (33, 4), (50, 9)):
        z.put(c, r, 'S')
    z.put(31, 27, 'a')
    z.put(57, 10, 'h')
    # mezzanine: a glass pod, lounges, beanbags, a coffee counter; the museum line on the west gallery, phone booths east
    z.block(14, 2, 4, 4, 'M', mez, 'u')
    z.block(22, 3, 4, 3, 'L', mez, 'u')
    z.block(36, 3, 4, 3, 'L', mez, 'u')
    z.puts([(29, 4), (31, 3), (33, 5)], 'b', mez, 'u')
    for c in range(45, 54):
        z.put(c, 1, 'k', mez, 'u')
    z.block(46, 4, 4, 2, 'C', mez, 'u')
    z.puts([(3, 14), (3, 18), (3, 22), (3, 26)], 'd', mez, 'u')
    z.block(57, 14, 2, 2, 'm', mez, 'u')
    z.block(57, 20, 2, 2, 'm', mez, 'u')
    z.puts([(2, 2), (59, 2), (41, 2), (20, 2)], 'p', mez, 'u')
    for (c, r) in ((3, 8), (58, 8), (29, 8), (8, 4), (4, 28)):
        z.put(c, r, 'S', mez, 'u')
    z.put(57, 27, 'a', mez, 'u')
    z.put(18, 9, 'h', mez, 'u')
    under_lights(z, mez)
    # floor: carpet under the lounges and the stage audience
    fl = z.layer('0')
    tiles(z, fl, 'q', 41, 41, 3, 1)
    tiles(z, fl, 'q', 25, 23, 3, 2)
    # ceiling: felt baffles over the hall, pendants over the tables and the galleries
    rf = z.layer('8')
    tiles(z, rf, '~', 9, 13, 12, 9, skip={(4, 2), (5, 2), (6, 2), (4, 3), (5, 3), (6, 3)}, checker=True)
    pendants(z, rf, mez, [(c, r) for r in range(12, 49) for c in (13, 19, 41, 47) if r % 6 == 3])
    pendants(z, rf, None, [(c, 15) for c in (2, 4, 57, 59)] + [(c, 4) for c in (6, 18, 30, 42, 54)])
    return z


# ------------------------------------------------------------------ zone 2: engineering floor (floor 29)
def eng():
    z = Zone('techhq_eng', 62, 62)
    z.gates(47, 29)
    mez = deck(z, lambda c, r: r <= 12 or (r <= 36 and c >= 51),
               [(20, 12), (21, 12), (22, 12), (53, 36), (54, 36), (55, 36)])
    z.block(20, 13, 3, 10, 'N')
    z.block(53, 37, 3, 10, 'N')
    columns(z, mez, [(8, 12), (15, 12), (28, 12), (36, 12), (44, 12), (51, 12), (51, 20), (51, 28), (51, 36), (58, 36)])
    # the service core in the middle: a living green wall to the south, whiteboards west, oak north, screens east
    for r in range(27, 35):
        for c in range(27, 37):
            z.g[r][c] = '#'
    # dev desks: two neighbourhoods south of the core, one in the north-east
    for r in (41, 45, 49, 53):
        for c in (4, 8, 15, 19):
            z.block(c, r, 4, 2, 'X')
    for r in (41, 45, 49):
        for c in (39, 43):
            z.block(c, r, 4, 2, 'X')
    for r in (16, 20):
        z.block(38, r, 4, 2, 'X')
        z.block(43, r, 4, 2, 'X')
    # scrum boards at the ends of the desk rows and round the stand-up spot by the core
    z.block(12, 39, 2, 1, 'B')
    z.block(12, 57, 2, 1, 'B')
    z.block(24, 44, 2, 1, 'B')
    z.block(24, 51, 2, 1, 'B')
    z.block(39, 25, 2, 1, 'B')
    z.block(44, 25, 2, 1, 'B')
    # west wall: glass meeting pods, phone booths, the server closet
    z.block(2, 14, 4, 4, 'M')
    z.block(2, 20, 4, 4, 'M')
    z.block(1, 27, 6, 4, 'Q')
    z.block(2, 33, 2, 2, 'm')
    z.block(5, 33, 2, 2, 'm')
    # hack lounge under the north deck: arcade line, ping-pong, foosball, the console sofa, beanbags
    z.puts([(2, 1), (3, 1), (4, 1), (5, 1), (6, 1)], 'g')
    z.block(9, 4, 3, 2, 'T')
    z.block(14, 3, 2, 1, 'F')
    z.block(14, 7, 2, 1, 'F')
    z.block(2, 6, 4, 3, 'H')
    z.puts([(8, 9), (10, 10), (12, 9), (17, 10)], 'b')
    # north-east under the deck: library shelves and lockers, lounge
    for c in (30, 33, 36):
        z.block(c, 1, 3, 1, 'A')
    z.block(31, 6, 4, 3, 'L')
    z.block(38, 6, 4, 3, 'L')
    # micro-kitchen along the south wall (east of the entry), the coffee bar islands
    for c in range(44, 58):
        z.put(c, 60, 'k')
    z.block(45, 55, 4, 2, 'C')
    z.block(52, 55, 4, 2, 'C')
    z.block(58, 50, 2, 2, 'O')
    # plants and big planters round the floor
    z.block(25, 37, 2, 2, 'O')
    z.block(37, 37, 2, 2, 'O')
    z.puts([(2, 59), (59, 47), (23, 59), (36, 59), (26, 24), (37, 24), (49, 38), (2, 38)], 'p')
    z.puts([(28, 25), (35, 25)], 'o')
    z.put(30, 58, 'P')
    for (c, r) in ((13, 47), (35, 44), (48, 43), (24, 30), (40, 31), (12, 18), (30, 18), (46, 4), (21, 7)):
        z.put(c, r, 'S')
    z.put(30, 38, 'a')
    z.put(9, 25, 'h')
    # mezzanine: quiet desks, a glass pod, lounges and beanbags; phone booths and a lounge on the east gallery
    for r in (3, 7):
        for c in (4, 8, 26, 30):
            z.block(c, r, 4, 2, 'X', mez, 'u')
    z.block(14, 3, 4, 4, 'M', mez, 'u')
    z.block(40, 3, 4, 3, 'L', mez, 'u')
    z.puts([(46, 8), (48, 7), (44, 9)], 'b', mez, 'u')
    z.block(58, 15, 2, 2, 'm', mez, 'u')
    z.block(58, 19, 2, 2, 'm', mez, 'u')
    z.block(54, 27, 4, 3, 'L', mez, 'u')
    for c in (36, 37, 38):
        z.put(c, 1, 'A', mez, 'u')
    z.puts([(2, 2), (59, 2), (20, 2), (59, 33)], 'p', mez, 'u')
    for (c, r) in ((22, 5), (54, 6), (55, 22), (36, 9)):
        z.put(c, r, 'S', mez, 'u')
    z.put(56, 32, 'h', mez, 'u')
    z.put(12, 10, 'a', mez, 'u')
    under_lights(z, mez)
    fl = z.layer('0')
    tiles(z, fl, 'q', 3, 41, 6, 4)
    tiles(z, fl, 'q', 39, 41, 2, 3)
    tiles(z, fl, 'q', 37, 15, 3, 2)
    rf = z.layer('8')
    tiles(z, rf, '~', 1, 13, 15, 12, checker=True)
    pendants(z, rf, mez, [(c, r) for r in (42, 46, 50, 54) for c in (6, 10, 17, 21, 41, 45)] + [(c, r) for r in (17, 21) for c in (40, 45)])
    return z


# ------------------------------------------------------------------ zone 3: hardware lab, design studio, exec deck, roof terrace (floor 33)
def lab():
    z = Zone('techhq_lab', 62, 50)
    z.gates(29, 29)
    # the glass wall between the terrace (rows 1-11, open to the sky) and the lab, with three sliding doorways
    for c in range(1, 61):
        z.g[12][c] = '#'
    for c in (9, 10, 11, 29, 30, 31, 32, 49, 50, 51):
        z.g[12][c] = 'n'
    # executive deck against the glass wall, looking out over the terrace
    mez = deck(z, lambda c, r: 13 <= r <= 22, [(8, 22), (9, 22), (10, 22), (51, 22), (52, 22), (53, 22)])
    z.block(8, 23, 3, 10, 'N')
    z.block(51, 23, 3, 10, 'N')
    columns(z, mez, [(15, 22), (22, 22), (29, 22), (34, 22), (40, 22), (46, 22), (1, 22), (60, 22)])
    # under the deck: the anechoic chamber, the drop tower, hinge-cycle rigs, thermal test chambers
    z.block(14, 14, 6, 6, 'c')
    z.block(23, 15, 2, 2, 'U')
    z.block(37, 14, 2, 2, 'W')
    z.block(41, 14, 2, 2, 'W')
    z.puts([(45, 14), (46, 14), (2, 14), (3, 14)], 'e')
    z.block(56, 14, 2, 2, 'U')
    # hardware lab (east): prototype benches, 3D printers along the east wall
    for r in (27, 32, 37, 42):
        z.block(36, r, 4, 2, 'J')
        z.block(43, r, 4, 2, 'J')
    for r in (35, 37, 39, 41, 43):
        z.put(60, r, 'j')
    z.puts([(56, 45), (57, 45)], 'e')
    # design studio (west): design tables, material boards, the concept turntable
    for r in (36, 41):
        z.block(3, r, 4, 2, 'x')
        z.block(12, r, 4, 2, 'x')
    z.block(3, 46, 2, 1, 's')
    z.block(12, 46, 2, 1, 's')
    z.block(1, 27, 1, 2, 's')
    z.block(18, 39, 3, 3, 't')
    z.puts([(2, 33), (22, 46), (40, 47), (59, 33)], 'p')
    z.block(26, 44, 2, 2, 'O')
    z.block(34, 44, 2, 2, 'O')
    z.put(30, 47, 'P')
    for (c, r) in ((9, 18), (32, 17), (52, 17), (24, 29), (52, 41), (8, 44), (30, 3), (14, 9), (46, 9)):
        z.put(c, r, 'S')
    z.put(31, 32, 'h')
    z.put(49, 6, 'a')
    # terrace: pergolas with lounges, outdoor sofas round fire tables, big planters, grass planters, lamp posts
    z.block(3, 3, 6, 4, '?')
    z.block(53, 3, 6, 4, '?')
    z.block(15, 4, 4, 3, 'v')
    z.block(42, 4, 4, 3, 'v')
    z.block(20, 8, 2, 2, '!')
    z.block(40, 8, 2, 2, '!')
    z.block(25, 3, 2, 2, 'O')
    z.block(35, 3, 2, 2, 'O')
    for c in list(range(2, 8)) + list(range(54, 60)):
        z.put(c, 9, '=')
    z.puts([(12, 2), (24, 9), (37, 9), (49, 2)], '$')
    # executive deck: corner offices, the boardroom in glass, a lounge
    z.block(26, 14, 8, 6, ']', mez, 'u')
    z.block(3, 15, 4, 3, '[', mez, 'u')
    z.block(15, 15, 4, 3, '[', mez, 'u')
    z.block(42, 15, 4, 3, '[', mez, 'u')
    z.block(54, 15, 4, 3, '[', mez, 'u')
    z.block(36, 16, 4, 3, 'L', mez, 'u')
    z.puts([(2, 13), (59, 13), (24, 13), (35, 13)], 'p', mez, 'u')
    for (c, r) in ((11, 15), (21, 19), (48, 19), (58, 20)):
        z.put(c, r, 'S', mez, 'u')
    z.put(12, 20, 'a', mez, 'u')
    z.put(40, 20, 'h', mez, 'u')
    under_lights(z, mez)
    # floor: decking and pavers on the terrace, ESD epoxy in the lab, carpet in the studio
    fl = z.layer('0')
    tiles(z, fl, 'w', 1, 1, 15, 2, solid='#G')
    for tx in range(15):
        z.block(1 + tx * 4, 9, 4, 3, 'z', fl, '.')
    tiles(z, fl, 'y', 33, 25, 7, 6)
    tiles(z, fl, 'q', 1, 33, 6, 4, skip={(4, 1)})
    # roof over the indoor part: 4 x 4 slab tiles with their lights, the exploded-laptop sculpture under a skylight
    rf = z.layer('8')
    z.block(25, 29, 8, 8, '&', rf)
    tiles(z, rf, '^', 1, 13, 15, 9)
    return z


# ------------------------------------------------------------------ checks
def check(z):
    errs = []
    g, W, H = z.g, z.w, z.h
    mez = z.layers.get(DECK_Y)
    at = lambda c, r: g[r][c] if 0 <= c < W and 0 <= r < H else '#'
    mt = lambda c, r: (mez[r][c] if mez and 0 <= c < W and 0 <= r < H else '#')
    G = [c for c in range(W) if g[0][c] == 'G']
    E = [c for c in range(W) if g[H - 1][c] == 'E']
    if len(G) != 3 or G[2] - G[0] != 2 or len(E) != 3 or E[2] - E[0] != 2:
        errs.append('gates')
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
    for ch in STAIRS:
        for (c, r, w, h) in rects(g, ch):
            north = ch in 'NZ'
            lo = [(cc, r + h) for cc in range(c, c + w)] if north else [(cc, r - 1) for cc in range(c, c + w)]
            hi = [(cc, r - 1) for cc in range(c, c + w)] if north else [(cc, r + h) for cc in range(c, c + w)]
            for a, b in zip(lo, hi):
                if at(*a) not in GROUND_OPEN or mt(*b) not in DECK_OPEN:
                    errs.append('%s stair end blocked %s %s' % (ch, a, b))
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
        errs.append('%d sealed ground cells %s' % (len(sealed), sealed[:6]))
    if mez:
        ds = [(c, r) for r in range(H) for c in range(W) if mez[r][c] in DECK_OPEN and (1, c, r) not in seen]
        if ds:
            errs.append('%d sealed deck cells %s' % (len(ds), ds[:6]))
    if not any((0, c, 1) in seen for c in G):
        errs.append('no path to the exit')
    nS = nD = 0
    for (L, grid, OPEN) in ((0, g, GROUND_OPEN), (1, mez, DECK_OPEN)):
        if grid is None:
            continue
        for r in range(H):
            for c in range(W):
                if grid[r][c] != 'S':
                    continue
                nS += 1
                nD += L
                if L == 0 and (c - P[0]) ** 2 + (r - P[1]) ** 2 < 14 ** 2:
                    errs.append('spawn (%d,%d) < 14 m from P' % (c, r))
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if (dc or dr) and grid[r + dr][c + dc] not in OPEN:
                            errs.append('spawn (%d,%d) L%d neighbour %r' % (c, r, L, grid[r + dr][c + dc]))
                if L == 1 and g[r][c] in STAIRS:
                    errs.append('deck spawn over a stair')
    if not 10 <= nS <= 16:
        errs.append('%d spawns' % nS)
    if mez and nD < 3:
        errs.append('only %d deck spawns' % nD)
    cnt = lambda ch: sum(row.count(ch) for grid in [g] + ([mez] if mez else []) for row in grid)
    if not (2 <= cnt('a') <= 3 and 2 <= cnt('h') <= 3):
        errs.append('pickups a=%d h=%d' % (cnt('a'), cnt('h')))
    for grid in [g] + list(z.layers.values()):
        for ch, (sw, sd) in PREFAB.items():
            for (c, r, w, h) in rects(grid, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('prefab %r %dx%d at (%d,%d)' % (ch, w, h, c, r))
    if mez:
        for r in range(H):
            for c in range(W):
                if mez[r][c] not in '.#urli' and g[r][c] in STAIRS:
                    errs.append('deck prop over a stair (%d,%d)' % (c, r))
                if mez[r][c] not in '.#' and g[r][c] in STAIRS and mez[r][c] != '.':
                    errs.append('deck over a stair (%d,%d)' % (c, r))
    return errs


def main():
    ok = True
    for z in (lobby(), eng(), lab()):
        errs = check(z)
        print('%-14s %dx%d  %s' % (z.name, z.w, z.h, 'ok' if not errs else ''))
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
