#!/usr/bin/env python3
"""INKBOLT Zenith Command zones (theme 'highrise', the final level): hand-placed layouts -> src/data/zones/highrise_*.txt

    python3 tools/highrise_zones.py            # write + validate
    python3 tools/highrise_zones.py --print    # ... and print the maps
    python3 tools/highrise_zones.py --check    # validate only

Interior zones (1, 2): the floor plan, "@layer 0.008" (floor finishes, wall-art codes on wall cells) and "@layer 4.5"
(ceiling fittings). Interior walls are two cells thick (one room face per module); the zone edge is the curtain wall.
The roof (3): the floor plan is the zone's own roof at y = 0 ('_' open air, '%' plank site, '$' plank laid at the
start), "@layer 0.008" walkway pavers, and one "@layer <y>" grid per neighbouring roof height (a deck symbol over its
cells, its equipment, spawns and pickups). Symbols: src/data/themes/highrise.js.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, validate, OUT, rects  # noqa: E402

PREFAB = {'R': (3, 1), 'C': (2, 2), 'b': (2, 1), 'g': (2, 1), 'D': (4, 1), 'K': (4, 2), 'T': (4, 2), 'B': (2, 1),
          'Q': (6, 2), 'y': (3, 2), 'd': (2, 2), 'V': (6, 2), 'O': (4, 4), 'c': (2, 1)}
ROOF_PREFAB = {'F': (3, 2), 'N': (4, 4), 'J': (3, 3), 'M': (6, 4), 'A': (2, 2), 'X': (4, 6), 'L': (3, 2), 'W': (4, 2)}


class IZone(Zone):
    """interior zone: floor plan + floor layer (f) + ceiling layer (k)"""

    def __init__(self, name, W, H):
        Zone.__init__(self, name, W, H)
        self.f = Zone(name + '_f', W, H)
        self.k = Zone(name + '_k', W, H)
        self.rect(0, 0, W, 1, '#')
        self.rect(0, H - 1, W, 1, '#')
        self.rect(0, 0, 1, H, '#')
        self.rect(W - 1, 0, 1, H, '#')
        gc = W // 2 - 1
        self.rect(gc, 0, 3, 1, 'G')
        self.rect(gc, H - 1, 3, 1, 'E')
        self.put(gc + 1, H - 3, 'P')

    def wall(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '#')

    def hole(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '.')

    def floor(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) not in '#GE':
                    self.f.g[r][c] = ch

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell')
            self.f.g[r][c] = ch

    def art_run(self, c0, r0, n, ch, vertical=False):
        self.art([(c0, r0 + k) if vertical else (c0 + k, r0) for k in range(n)], ch)

    def ceil(self, c0, r0, w, h, ch, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) not in '#GE' and self.k.g[r][c] in over:
                    self.k.g[r][c] = ch

    def beams_z(self, cols, r0, r1):
        for c in cols:
            for r in range(r0, r1 + 1):
                if self.at(c, r) in '#GE':
                    continue
                self.k.g[r][c] = '+' if self.k.g[r][c] in '=+' else '!'

    def beams_x(self, rows, c0, c1):
        for r in rows:
            for c in range(c0, c1 + 1):
                if self.at(c, r) in '#GE':
                    continue
                self.k.g[r][c] = '+' if self.k.g[r][c] in '!+' else '='

    def lights(self, ch, cols, rows, keep='.'):
        for r in rows:
            for c in cols:
                if self.at(c, r) not in '#GE' and self.k.g[r][c] in keep:
                    self.k.g[r][c] = ch

    def lintel(self, c0, r0, w, h):
        """a doorway through a 2-thick wall: the lintel over the opening cells (wall along X: '[', along Z: ']')"""
        ch = '[' if w >= h else ']'
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.k.g[r][c] = ch

    def text(self):
        out = Zone.text(self)
        out += '@layer 0.008\n' + Zone.text(self.f)
        out += '@layer 4.5\n' + Zone.text(self.k)
        return out


def border(z, c0, r0, w, h, base, ch):
    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            if z.f.g[r][c] == base and any(z.at(c + dc, r + dr) == '#' for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                z.f.g[r][c] = ch


def door(z, c0, r0, w, h):
    """open a doorway in a 2-thick wall and put the lintel over it"""
    z.hole(c0, r0, w, h)
    z.lintel(c0, r0, w, h)


# ======================================================================== zone 1: Armory Deck
def zone1():
    W, H = 62, 56
    z = IZone('highrise_1', W, H)
    # walls: west wing | hall | east wing over the lobby
    z.wall(19, 1, 2, 38)
    z.wall(47, 1, 2, 38)
    z.wall(1, 39, 60, 2)
    z.wall(1, 25, 18, 2)       # theatre / kit room
    z.wall(49, 18, 12, 2)      # vault / ready room
    z.wall(1, 1, 18, 2)        # the theatre's screen wall
    z.wall(49, 1, 12, 2)       # the vault: walled in all round
    z.wall(59, 3, 2, 15)
    door(z, 19, 10, 2, 4)      # theatre <-> hall
    door(z, 19, 31, 2, 4)      # kit room <-> hall
    door(z, 8, 25, 3, 2)       # theatre <-> kit room
    door(z, 8, 39, 4, 2)       # kit room <-> lobby
    door(z, 25, 39, 12, 2)     # hall <-> lobby (the bio-gate line)
    door(z, 52, 39, 4, 2)      # ready room <-> lobby
    door(z, 47, 28, 2, 4)      # hall <-> ready room
    door(z, 54, 18, 3, 2)      # vault <-> ready room
    z.rect(47, 5, 2, 6, 'V')   # the vault door in the hall's east wall
    # ---- floors
    z.floor(1, 41, 60, 14, '1')
    border(z, 1, 41, 60, 14, '1', '8')
    z.floor(29, 52, 5, 3, '7')
    z.floor(1, 1, 18, 24, '2')
    z.floor(1, 27, 18, 12, '3')
    z.floor(21, 1, 26, 38, '3')
    z.floor(49, 1, 12, 17, '3')
    z.floor(49, 20, 12, 19, '3')
    for c0, r0, w, h in ((25, 39, 12, 2), (8, 39, 4, 2), (52, 39, 4, 2), (19, 10, 2, 4), (19, 31, 2, 4), (8, 25, 3, 2),
                         (47, 28, 2, 4), (54, 18, 3, 2)):
        z.floor(c0, r0, w, h, '3' if r0 < 39 else '1')
    z.floor(25, 39, 12, 2, '/')
    # ---- lobby: front desk, the star, bio-gates, lift-side benches, plants, columns
    z.block(28, 46, 6, 2, 'Q')
    z.f.rect(29, 48, 4, 4, '0')
    for c in (24, 25, 27, 28, 30, 31, 33, 34, 36, 37):
        z.put(c, 42, 't')
    z.f.rect(24, 42, 14, 1, '/')
    for c in (24, 25, 27, 28, 30, 31, 33, 34, 36, 37):
        z.f.g[42][c] = '1'
    for (c, r) in ((10, 46), (51, 46), (16, 50), (45, 50)):
        z.put(c, r, 'I')
    z.block(3, 44, 2, 1, 'B'); z.block(3, 49, 2, 1, 'B'); z.block(57, 44, 2, 1, 'B'); z.block(57, 49, 2, 1, 'B')
    for (c, r) in ((2, 42), (59, 42), (2, 53), (59, 53), (22, 53), (40, 53), (22, 44), (40, 44)):
        z.put(c, r, 'p')
    z.put(13, 53, 'o'); z.put(14, 53, 'o'); z.put(47, 53, 'o')
    z.puts([(7, 47), (8, 47), (54, 47)], 'x')
    z.put(12, 43, 'a'); z.put(49, 52, 'h')
    # ---- briefing theatre (west wing, rows 1-24): lectern + video wall at the north, seat rows facing it
    z.put(9, 4, 'U')
    for r in (7, 10, 13, 16, 19):
        z.block(2, r, 4, 2, 'T'); z.block(7, r, 4, 2, 'T'); z.block(13, r, 4, 2, 'T')
    z.put(1, 22, 'p'); z.put(17, 22, 'p'); z.put(17, 3, 'p'); z.put(1, 3, 'p')
    z.put(4, 23, 'S'); z.put(14, 4, 'S')
    # ---- kit room (west wing, rows 27-38): lockers, exo suits, benches
    z.run(1, 28, 6, 'l', vertical=True)
    z.run(17, 33, 5, 'l', vertical=True)
    z.puts([(4, 27), (6, 27), (12, 27), (14, 27)], 'H')
    z.block(6, 32, 2, 1, 'B'); z.block(10, 32, 2, 1, 'B'); z.block(6, 35, 2, 1, 'B'); z.block(10, 35, 2, 1, 'B')
    z.block(13, 37, 2, 1, 'g')
    z.put(4, 37, 'S'); z.put(15, 30, 'h')
    # ---- armory hall (21-46 x 1-38): gun walls round it, glass gun cases, benches, shelves
    for r0 in (2, 6, 15, 19, 23, 36):
        z.block(21, r0, 1, 3, 'R')
    for r0 in (12, 16, 20, 24, 33):
        z.block(46, r0, 1, 3, 'R')
    z.block(22, 1, 3, 1, 'R'); z.block(26, 1, 3, 1, 'R'); z.block(34, 1, 3, 1, 'R'); z.block(38, 1, 3, 1, 'R')
    z.block(43, 1, 2, 1, 'g')
    z.block(46, 1, 1, 2, 'g')
    z.block(46, 36, 1, 2, 'g')
    for c0 in (25, 30, 36, 41):
        z.block(c0, 6, 2, 2, 'C'); z.block(c0, 11, 2, 2, 'C')
    for c0 in (25, 41):
        z.block(c0, 17, 2, 2, 'C')
    for (c0, r0) in ((29, 18), (35, 18), (29, 23), (35, 23), (26, 28), (38, 28), (32, 32)):
        z.block(c0, r0, 2, 1, 'b')
    z.puts([(30, 15), (31, 15), (36, 15)], 'x')
    z.puts([(24, 33), (24, 34), (43, 30), (43, 31), (27, 36)], 'x')
    z.puts([(33, 4), (45, 9), (22, 28), (21, 1)], 'H')
    z.f.rect(22, 2, 1, 16, '/')
    z.put(29, 9, 'S'); z.put(39, 9, 'S'); z.put(33, 21, 'S'); z.put(25, 25, 'S'); z.put(42, 25, 'S'); z.put(33, 36, 'S')
    z.put(34, 14, 'a')
    # ---- the vault (east wing, rows 1-17): round door, racks all round, cases, crates
    for c0 in (49, 53):
        z.block(c0, 3, 3, 1, 'R')
    z.block(58, 4, 1, 3, 'R'); z.block(58, 9, 1, 3, 'R')
    z.block(50, 7, 2, 2, 'C'); z.block(54, 7, 2, 2, 'C'); z.block(50, 12, 2, 2, 'C'); z.block(54, 12, 2, 2, 'C')
    z.puts([(57, 16), (58, 16), (58, 15), (49, 16)], 'x')
    z.put(53, 10, 'S')
    # ---- ready room (east wing, rows 20-38): shelves, benches, coffee point, lockers
    z.block(60, 21, 1, 2, 'g'); z.block(60, 25, 1, 2, 'g'); z.block(60, 33, 1, 2, 'g')
    z.block(52, 24, 2, 1, 'b'); z.block(56, 24, 2, 1, 'b'); z.block(52, 31, 2, 1, 'b'); z.block(56, 31, 2, 1, 'b')
    z.block(49, 20, 2, 1, 'c')
    z.run(49, 35, 3, 'l', vertical=True)
    z.puts([(58, 37), (59, 37), (57, 28)], 'x')
    z.put(55, 35, 'S'); z.put(51, 22, 'h'); z.put(54, 28, 'a')
    # ---- wall art
    z.art_run(2, 2, 16, 'v')            # the theatre's video wall
    z.art([(19, 21), (14, 25)], 'u')
    z.art([(20, 26), (20, 8)], 's')
    z.art([(47, 26), (47, 13)], 's')
    z.art([(48, 4), (48, 12)], 'k')
    z.art([(22, 40), (39, 40)], 'e')
    z.art([(18, 39), (43, 39)], 'e')
    z.art([(6, 39), (57, 39)], 's')
    z.art([(52, 19), (58, 18)], 'k')
    z.art([(1, 26), (16, 26)], 'u')
    # ---- ceiling
    z.beams_z([27, 33, 40], 1, 38); z.beams_x([9, 19, 29], 21, 46)
    z.beams_x([46, 51], 1, 60)
    z.ceil(21, 4, 26, 1, '{'); z.ceil(21, 34, 26, 1, '{')
    z.ceil(49, 22, 12, 1, '~')
    z.lights('i', range(23, 46, 3), range(3, 38, 4))
    z.lights('i', range(3, 18, 4), range(4, 24, 3))
    z.lights('j', range(5, 18, 4), range(5, 24, 3))
    z.lights('j', range(3, 18, 3), range(29, 38, 3))
    z.lights('i', range(51, 60, 3), range(3, 17, 3))
    z.lights('i', range(51, 60, 3), range(22, 38, 4))
    z.lights('j', range(3, 60, 4), range(43, 54, 4))
    return z


# ======================================================================== zone 2: Operations Deck
def zone2():
    W, H = 62, 56
    z = IZone('highrise_2', W, H)
    z.wall(21, 1, 2, 38)
    z.wall(43, 1, 2, 38)
    z.wall(1, 39, 60, 2)
    z.wall(45, 19, 16, 2)
    z.wall(1, 1, 20, 2)        # the simulator's projection wall
    door(z, 6, 39, 6, 2)       # simulator <-> drone bay
    door(z, 26, 39, 10, 2)     # ops <-> drone bay
    door(z, 50, 39, 5, 2)      # server room <-> drone bay
    door(z, 21, 8, 2, 4)       # simulator <-> ops
    door(z, 43, 8, 2, 4)       # ops <-> gear room
    door(z, 43, 28, 2, 4)      # ops <-> server room
    door(z, 51, 19, 3, 2)      # gear room <-> server room
    # floors
    z.floor(1, 41, 60, 14, '3')
    z.floor(29, 52, 5, 3, '7')
    z.floor(1, 1, 20, 38, '4')
    z.floor(23, 1, 20, 38, '5')
    z.floor(45, 1, 16, 18, '3')
    z.floor(45, 21, 16, 18, '5')
    for c0, r0, w, h, ch in ((6, 39, 6, 2, '4'), (26, 39, 10, 2, '5'), (50, 39, 5, 2, '5'), (21, 8, 2, 4, '5'), (43, 8, 2, 4, '3'),
                             (43, 28, 2, 4, '5'), (51, 19, 3, 2, '3')):
        z.floor(c0, r0, w, h, ch)
    # ---- drone bay (rows 41-54): cradles in two rows, hazard lanes, crates, columns
    for c0 in (3, 9, 15, 44, 50, 56):
        z.block(c0, 43, 2, 2, 'd')
    for c0 in (3, 9, 15, 44, 50, 56):
        z.block(c0, 48, 2, 2, 'd')
    z.f.rect(2, 46, 18, 1, '/'); z.f.rect(43, 46, 17, 1, '/')
    for (c, r) in ((22, 44), (40, 44), (22, 50), (40, 50)):
        z.put(c, r, 'I')
    z.puts([(21, 52), (22, 52), (40, 52), (41, 52), (41, 51), (6, 53), (7, 53), (55, 53)], 'x')
    for c in range(25, 37):   # the launch pad: a hazard frame round the unit's star
        z.f.g[43][c] = '/'; z.f.g[50][c] = '/'
    for r in range(43, 51):
        z.f.g[r][25] = '/'; z.f.g[r][36] = '/'
    z.f.rect(29, 45, 4, 4, '0')
    z.put(2, 41, 'p'); z.put(59, 41, 'p')
    z.put(13, 52, 'a'); z.put(48, 52, 'h')
    z.put(12, 46, 'S'); z.put(50, 46, 'S')
    # ---- shooting simulator (west wing, 1-20 x 1-38): booths along the firing line, holo targets downrange
    for c0 in (2, 6, 10, 14):
        z.block(c0, 31, 3, 2, 'y')
    z.f.rect(1, 30, 20, 1, '^')
    for (c, r) in ((4, 6), (9, 5), (15, 7), (6, 12), (12, 11), (17, 14), (3, 18), (10, 19), (15, 22), (7, 25)):
        z.put(c, r, 'Y')
    z.puts([(18, 35), (18, 36), (1, 36), (2, 36)], 'x')
    z.put(19, 37, 'l'); z.put(19, 36, 'l')
    z.put(4, 10, 'S'); z.put(16, 18, 'S'); z.put(8, 22, 'S')
    z.put(11, 36, 'h')
    # ---- operations room (23-42 x 1-38): the holo table, desk pairs round it, consoles on the walls
    z.block(31, 16, 4, 4, 'O')
    z.block(25, 10, 4, 2, 'K'); z.block(37, 10, 4, 2, 'K'); z.block(25, 24, 4, 2, 'K'); z.block(37, 24, 4, 2, 'K')
    z.block(31, 6, 4, 2, 'K')
    z.block(23, 15, 1, 4, 'D'); z.block(42, 15, 1, 4, 'D'); z.block(23, 30, 1, 4, 'D'); z.block(42, 21, 1, 4, 'D')
    z.puts([(25, 33), (25, 34), (38, 33), (39, 34)], 'x')
    z.put(24, 2, 'p'); z.put(41, 2, 'p'); z.put(24, 37, 'p'); z.put(41, 37, 'p')
    z.f.rect(26, 21, 14, 1, '-')
    z.f.rect(33, 22, 1, 14, '|')
    z.put(28, 18, 'S'); z.put(38, 30, 'S'); z.put(28, 34, 'S')
    z.put(33, 28, 'a')
    # ---- gear room (east wing, rows 1-18): racks, cases, benches, shelves
    z.block(46, 1, 3, 1, 'R'); z.block(50, 1, 3, 1, 'R'); z.block(56, 1, 3, 1, 'R')
    z.block(60, 4, 1, 3, 'R'); z.block(60, 10, 1, 3, 'R')
    z.block(48, 6, 2, 2, 'C'); z.block(54, 6, 2, 2, 'C')
    z.block(48, 11, 2, 1, 'b'); z.block(54, 11, 2, 1, 'b')
    z.block(45, 15, 1, 2, 'g'); z.block(60, 15, 1, 2, 'g'); z.block(57, 17, 2, 1, 'g')
    z.puts([(46, 4), (58, 13)], 'H')
    z.puts([(51, 15), (52, 15)], 'x')
    z.put(57, 9, 'S'); z.put(51, 9, 'S')
    # ---- server room (east wing, rows 21-38): rack rows, a console
    for r in range(23, 37):
        if r in (29, 30):
            continue
        z.put(48, r, 's'); z.put(52, r, 's'); z.put(56, r, 's')
    z.block(60, 23, 1, 4, 'D')
    z.puts([(59, 36), (59, 37)], 'x')
    z.put(54, 30, 'S'); z.put(58, 33, 'h')
    # ---- wall art
    z.art_run(2, 2, 18, 'v')            # the simulator's projection wall
    z.art_run(22, 14, 6, 'v', vertical=True)
    z.art([(43, 15), (43, 16)], 'm')
    z.art([(21, 20), (21, 27)], 's')
    z.art([(44, 4), (44, 24)], 'k')
    z.art([(24, 40), (37, 40)], 'e')
    z.art([(14, 40), (47, 40)], 's')
    z.art([(45, 19), (59, 20)], 'u')
    z.art([(22, 34)], 'u')
    # ---- ceiling
    z.beams_z([7, 14], 1, 38); z.beams_x([12, 26], 1, 20)
    z.beams_z([28, 37], 1, 38); z.beams_x([9, 27], 23, 42)
    z.beams_x([47, 51], 1, 60)
    z.ceil(45, 22, 16, 1, '{'); z.ceil(45, 28, 16, 1, '{')
    z.ceil(1, 33, 20, 1, '~')
    z.lights('i', range(3, 20, 4), range(3, 30, 4))
    z.lights('j', range(3, 20, 3), range(32, 38, 3))
    z.lights('j', range(25, 42, 3), range(3, 38, 3))
    z.lights('i', range(47, 60, 3), range(3, 18, 3))
    z.lights('i', range(50, 60, 4), range(24, 38, 4))
    z.lights('i', range(3, 60, 4), range(43, 54, 4))
    return z


# ======================================================================== zone 3: the roof
class RZone(Zone):
    """the roof: floor plan (the zone's own roof at y = 0, '_' open air) + paver layer + one layer per roof height"""

    def __init__(self, name, W, H):
        Zone.__init__(self, name, W, H, fill='_')
        self.f = Zone(name + '_f', W, H)
        self.L = {}

    def layer(self, y):
        if y not in self.L:
            self.L[y] = Zone('%s@%s' % (self.name, y), self.w, self.h)
        return self.L[y]

    def roof(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '.')

    def deck(self, y, c0, r0, w, h, ch):
        L = self.layer(y)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '_', (self.name, c, r)
                L.g[r][c] = ch

    def text(self):
        out = Zone.text(self)
        out += '@layer 0.008\n' + Zone.text(self.f)
        for y in sorted(self.L):
            out += '@layer %g\n' % y + Zone.text(self.L[y])
        return out


def put_on(L, c, r, ch, over):
    assert L.g[r][c] in over, (L.name, c, r, L.g[r][c], ch)
    L.g[r][c] = ch


def block_on(L, c0, r0, w, h, ch, over):
    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            put_on(L, c, r, ch, over)


def zone3():
    W, H = 76, 64
    z = RZone('highrise_3', W, H)
    # ---- the zone's own roof (y = 0) and the exit building's roof (y = 0)
    z.roof(20, 28, 34, 35)                 # main roof: cols 20-53, rows 28-62
    z.rect(20, 63, 34, 1, '#')             # the HQ tower's facade
    z.rect(37, 63, 3, 1, 'E')
    z.put(38, 60, 'P')
    z.roof(26, 1, 24, 22)                  # exit roof: cols 26-49, rows 1-22
    z.rect(31, 0, 15, 4, '#')              # the stair penthouse round the exit door
    z.rect(37, 1, 3, 3, '.')
    z.rect(37, 0, 3, 1, 'G')
    # gaps and planks between them (rows 23-27)
    z.rect(33, 23, 2, 5, '$')              # laid from the start: the way to the exit
    z.rect(43, 23, 2, 5, '%')
    # ---- neighbouring roofs
    W_Y, E_Y, NE_Y, NW_Y = -2, 1.5, 3, -3
    z.deck(W_Y, 2, 25, 14, 34, 'Z')        # west: an older block, gravel roof, 2 m down
    z.deck(E_Y, 58, 30, 16, 31, 'n')       # east: 1.5 m up
    z.deck(NE_Y, 54, 2, 20, 23, 'n')       # north-east perch: 3 m up
    z.deck(NW_Y, 2, 2, 21, 19, 'Z')        # north-west: 3 m down
    for (c0, r0, w, h) in ((16, 35, 4, 2), (16, 49, 4, 2),     # west <-> main
                           (54, 38, 4, 2), (54, 52, 4, 2),     # main <-> east
                           (64, 25, 2, 5),                     # east <-> north-east
                           (8, 21, 2, 4)):                     # north-west <-> west
        z.rect(c0, r0, w, h, '%')
    # ---- the main roof: lift machine room, cooling towers, HVAC, skylights, the gantry, tank, ducts, hatches, vents
    z.block(36, 30, 6, 4, 'M')
    z.block(46, 32, 4, 4, 'N'); z.block(46, 37, 4, 4, 'N')
    z.block(22, 41, 4, 6, 'X')
    z.block(28, 47, 3, 2, 'F'); z.block(43, 52, 3, 2, 'F'); z.block(29, 33, 3, 2, 'F')
    z.block(33, 42, 3, 2, 'L'); z.block(40, 42, 3, 2, 'L'); z.block(33, 46, 3, 2, 'L')
    z.block(48, 56, 3, 3, 'J')
    z.run(42, 31, 4, 'r'); z.run(31, 35, 1, 'r', vertical=True)
    z.run(31, 49, 6, 'r', vertical=True)
    z.run(44, 45, 6, 'r')
    z.puts([(24, 56), (51, 59), (25, 30)], 'z')
    z.puts([(27, 38), (41, 49), (35, 55), (50, 47), (24, 52)], 'f')
    z.puts([(21, 34), (21, 51)], 'q')
    z.put(26, 58, 'a'); z.put(45, 58, 'h'); z.put(40, 38, 'a')
    z.put(47, 48, 'S'); z.put(26, 36, 'S'); z.put(52, 30, 'S')
    # walkway pavers: the entry to the laid plank and round the machine room
    for r in range(36, 63):
        z.f.g[r][38] = '6'
    for c in range(33, 39):
        z.f.g[36][c] = '6'
    for r in range(28, 36):
        z.f.g[r][33] = '6'; z.f.g[r][34] = '6'
    # ---- the exit roof: penthouse, mast, tank, solar array, HVAC, vents
    z.block(27, 4, 2, 2, 'A')
    z.block(46, 6, 3, 3, 'J')
    z.block(28, 12, 4, 2, 'W'); z.block(28, 16, 4, 2, 'W')
    z.block(41, 13, 3, 2, 'F')
    z.puts([(35, 9), (45, 18), (30, 20)], 'f')
    z.put(36, 15, 'S'); z.put(47, 13, 'S')
    z.put(40, 19, 'h')
    for r in range(4, 19):
        z.f.g[r][38] = '6'
    for c in range(33, 39):
        z.f.g[18][c] = '6'
    for r in range(18, 23):
        z.f.g[r][33] = '6'; z.f.g[r][34] = '6'
    # ---- west roof (-2): old water tank, skylight, duct, HVAC, plank stacks by the sites
    Lw = z.layer(W_Y)
    block_on(Lw, 4, 28, 3, 3, 'J', 'Z'); block_on(Lw, 8, 42, 3, 2, 'L', 'Z'); block_on(Lw, 4, 51, 3, 2, 'F', 'Z')
    for r in range(33, 41):
        put_on(Lw, 4, r, 'r', 'Z')
    put_on(Lw, 13, 33, 'q', 'Z'); put_on(Lw, 13, 47, 'q', 'Z'); put_on(Lw, 10, 26, 'q', 'Z')
    for (c, r) in ((9, 30), (12, 55), (6, 46)):
        put_on(Lw, c, r, 'f', 'Z')
    put_on(Lw, 11, 37, 'S', 'Z'); put_on(Lw, 10, 51, 'S', 'Z')
    # ---- east roof (+1.5): HVACs, cooling tower, mast, plank stacks
    Le = z.layer(E_Y)
    block_on(Le, 66, 33, 3, 2, 'F', 'n'); block_on(Le, 66, 43, 3, 2, 'F', 'n')
    block_on(Le, 68, 49, 4, 4, 'N', 'n')
    block_on(Le, 70, 32, 2, 2, 'A', 'n')
    put_on(Le, 60, 36, 'q', 'n'); put_on(Le, 60, 50, 'q', 'n'); put_on(Le, 63, 31, 'q', 'n')
    for c in range(62, 70):
        put_on(Le, c, 57, 'r', 'n')
    put_on(Le, 63, 40, 'S', 'n'); put_on(Le, 62, 54, 'S', 'n')
    put_on(Le, 71, 39, 'f', 'n')
    # ---- north-east perch (+3): solar, mast, HVAC (snipers)
    Ln = z.layer(NE_Y)
    block_on(Ln, 57, 5, 4, 2, 'W', 'n'); block_on(Ln, 57, 9, 4, 2, 'W', 'n'); block_on(Ln, 67, 4, 2, 2, 'A', 'n')
    block_on(Ln, 66, 13, 3, 2, 'F', 'n')
    put_on(Ln, 62, 22, 'q', 'n')
    put_on(Ln, 58, 17, 'S', 'n'); put_on(Ln, 70, 20, 'S', 'n')
    put_on(Ln, 72, 9, 'f', 'n')
    # ---- north-west (-3): tank, HVAC, skylight
    Lnw = z.layer(NW_Y)
    block_on(Lnw, 4, 4, 3, 3, 'J', 'Z'); block_on(Lnw, 13, 5, 3, 2, 'F', 'n' + 'Z'); block_on(Lnw, 14, 12, 3, 2, 'L', 'Z')
    put_on(Lnw, 7, 18, 'q', 'Z')
    put_on(Lnw, 9, 11, 'S', 'Z'); put_on(Lnw, 19, 16, 'S', 'Z')
    put_on(Lnw, 20, 4, 'f', 'Z')
    return z


# ======================================================================== validation
def check_interior(z):
    walk = set('.Pah') | set('t')   # bio-gates: gaps between them
    errs, stats = validate(z, set('.Pah'), PREFAB, size=((60, 64), (54, 58)))
    # wall-art codes only on wall cells, floor finishes only on floor cells
    for r in range(z.h):
        for c in range(z.w):
            ch = z.f.g[r][c]
            if ch in 'useEvmk' and z.at(c, r) != '#' and ch != '.':
                errs.append('art %r on a non-wall cell (%d,%d)' % (ch, c, r))
    # perimeter: rows 0 / H-1 and cols 0 / W-1 are walls or gates
    for c in range(z.w):
        if z.at(c, 0) not in '#G' or z.at(c, z.h - 1) not in '#E':
            errs.append('perimeter col %d' % c)
    return errs, stats


def check_roof(z):
    errs = []
    g = z.g
    heights = {}
    for r in range(z.h):
        for c in range(z.w):
            ch = g[r][c]
            if ch not in '_%$':
                heights[(c, r)] = 0.0
    for y, L in z.L.items():
        for r in range(z.h):
            for c in range(z.w):
                if L.g[r][c] != '.':
                    if g[r][c] != '_':
                        errs.append('layer %s cell over a non-void floor cell (%d,%d)' % (y, c, r))
                    heights[(c, r)] = y
    # plank sites: both ends on roofs
    links = []
    for ch in '%$':
        for (c0, r0, w, h) in rects(g, ch):
            alongZ = h >= w
            ends = [(c0, r0 - 1), (c0, r0 + h)] if alongZ else [(c0 - 1, r0), (c0 + w, r0)]
            for e in ends:
                if e not in heights:
                    errs.append('plank site %r at (%d,%d) end %s not on a roof' % (ch, c0, r0, e))
            if all(e in heights for e in ends):
                dh = abs(heights[ends[0]] - heights[ends[1]])
                span = (h if alongZ else w)
                if not (3 <= span <= 7):
                    errs.append('plank gap %d m at (%d,%d)' % (span, c0, r0))
                if dh > 2.0:
                    errs.append('plank rise %.1f m at (%d,%d)' % (dh, c0, r0))
                links.append((ends, ch))
    # walkable cells per roof (props block), reachability from P over laid planks only, every roof linked by sites
    solid = set('#GE') | set(ROOF_PREFAB) | set('frqz')
    def free(c, r):
        if (c, r) not in heights:
            return False
        y = heights[(c, r)]
        if y == 0.0:
            return g[r][c] not in solid
        return z.L[y].g[r][c] not in solid
    P = [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] == 'P'][0]

    def reach(use_sites):
        seen = {P}
        q = deque([P])
        while q:
            c, r = q.popleft()
            nb = [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
            for ends, ch in links:
                if (ch == '$' or use_sites) and (c, r) in ends:
                    nb += [e for e in ends if e != (c, r)]
            for n in nb:
                if n in seen or not free(*n):
                    continue
                if heights[n] != heights[(c, r)] and not any(n in e and (c, r) in e for e, _ in links):
                    continue
                seen.add(n)
                q.append(n)
        return seen
    base, full = reach(False), reach(True)
    gates = [(c, 1) for c in range(z.w) if g[0][c] == 'G']
    if not any(gc in base for gc in gates):
        errs.append('exit not reachable over the laid planks')
    for (c, r), y in heights.items():
        if free(c, r) and (c, r) not in full:
            errs.append('roof cell (%d,%d) @%s unreachable even with every plank' % (c, r, y))
            break
    # spawns: 3x3 open round each, away from P
    S = [(c, r, 0.0) for r in range(z.h) for c in range(z.w) if g[r][c] == 'S']
    for y, L in z.L.items():
        S += [(c, r, y) for r in range(z.h) for c in range(z.w) if L.g[r][c] == 'S']
    for c, r, y in S:
        if (c - P[0]) ** 2 + (r - P[1]) ** 2 < 14 ** 2:
            errs.append('spawn (%d,%d) near P' % (c, r))
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                n = (c + dc, r + dr)
                if (dc or dr) and not (free(*n) and heights.get(n) == y):
                    errs.append('spawn (%d,%d)@%s crowded at %s' % (c, r, y, n))
    if not 10 <= len(S) <= 16:
        errs.append('%d spawns' % len(S))
    na = sum(row.count('a') for row in g) + sum(sum(row.count('a') for row in L.g) for L in z.L.values())
    nh = sum(row.count('h') for row in g) + sum(sum(row.count('h') for row in L.g) for L in z.L.values())
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for ch, (sw, sd) in ROOF_PREFAB.items():
        for G2 in [z] + list(z.L.values()):
            for (c, r, w, h) in rects(G2.g, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('prefab %r block %dx%d at (%d,%d)' % (ch, w, h, c, r))
    stats = {'size': '%dx%d' % (z.w, z.h), 'roofs': len(set(heights.values())), 'spawns': len(S), 'sites': len(links)}
    return errs, stats


def main():
    z1, z2, z3 = zone1(), zone2(), zone3()
    out = []
    for z in (z1, z2):
        e, s = check_interior(z)
        out.append((z, e, s))
    e, s = check_roof(z3)
    out.append((z3, e, s))
    ok = True
    for z, errs, stats in out:
        print('%-22s %s' % (z.name, stats))
        for er in errs:
            print('   ERROR', er)
            ok = False
    if '--check' not in sys.argv:
        for z, _, _ in out:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
    if '--print' in sys.argv:
        for z, _, _ in out:
            print('\n' + z.name)
            print(z.text())
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
