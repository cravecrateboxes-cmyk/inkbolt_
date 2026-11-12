#!/usr/bin/env python3
"""INKBOLT Topsy Toyworks zones (theme 'toyfactory'): hand-placed layouts -> src/data/zones/toyfactory_*.txt

    python3 tools/toyfactory_zones.py            # write + validate
    python3 tools/toyfactory_zones.py --print    # ... and print the maps
    python3 tools/toyfactory_zones.py --check    # validate only

Every zone file has the floor plan and six layers: "@layer 0.01" (floor marks), "@layer 0.02" (wall-art codes on the
wall cells: a data layer the theme's wall chooser reads, never built; cell (0, 0) holds ',' in the warehouse),
"@layer 3.5" (the mezzanine decks and what stands on them), "@layer 4.2" (overhead pellet pipes), "@layer 12" (roof
bays [4, 4]) and a second "@layer 12" (hanging boards). Symbols: see src/data/themes/toyfactory.js.

Zone 1, the Production Floor, is 76 x 66 m (gates at columns 36-38, the player starts at (37, 63)); zone 2, the
Warehouse, is 76 x 64 m (gates at columns 36-38, entry at (37, 61)).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

WALK = set('')
PREFAB = {'k': (2, 1), 'K': (2, 1), 't': (2, 1), 'M': (5, 2), 'D': (2, 2), 'B': (4, 4), 'R': (2, 1), 'U': (6, 3), 'V': (6, 3),
          'L': (6, 3), 'b': (2, 1), 'W': (2, 2), 'Z': (3, 3), 'H': (6, 6), 'Q': (6, 3), 'T': (3, 3), 'I': (2, 2), 'J': (4, 2),
          'F': (2, 2), 'N': (3, 2), 'C': (2, 2), 'x': (2, 2), 'X': (2, 3), 'v': (2, 1), 's': (2, 7), 'l': (7, 2), 'm': (2, 2),
          '$': (2, 1), '@': (8, 5)}
LINES = (14, 24, 34)                 # zone 1: the rows of lines A, B, C
BELT = {14: '=', 24: '~', 34: '-'}


class TZone(Zone):
    """floor plan + floor marks (f) + wall art (a) + deck (d) + pipes (p) + roof bays (k) + hanging boards (s)"""

    def __init__(self, name, w, h, gc):
        Zone.__init__(self, name, w, h)
        for L in ('f', 'a', 'd', 'p', 'k', 's'):
            setattr(self, L, Zone(name + '_' + L, w, h))
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gc, 0, 3, 1, 'G')
        self.rect(gc, h - 1, 3, 1, 'E')
        self.put(gc + 1, h - 3, 'P')

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell', self.at(c, r))
            self.a.g[r][c] = ch

    def mark(self, c0, r0, w, h, ch):
        """floor marks over open floor cells only"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) == '.' and self.f.g[r][c] == '.':
                    self.f.g[r][c] = ch

    def roof(self):
        """[4, 4] roof bays over rows 1 .. h-2: girder bays every 24 m, a high-bay lamp in one bay of three
        (staggered), skylights"""
        nj = (self.h - 2) // 4
        for i in range(self.w // 4):
            for j in range(nj):
                g = i % 6 == 3
                lamp = (i + 2 * j) % 4 == 0
                if g:
                    ch = '5' if lamp else '4'
                elif i % 6 == 0 and j % 3 == 1:
                    ch = '3'
                else:
                    ch = '2' if lamp else '1'
                self.k.rect(i * 4, 1 + j * 4, 4, 4, ch)

    def text(self):
        return (Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer 0.02\n' + self.a.text() + '@layer 3.5\n' + self.d.text() +
                '@layer 4.2\n' + self.p.text() + '@layer 12\n' + self.k.text() + '@layer 12\n' + self.s.text())


def check(z, size):
    errs, stats = validate(z, WALK, PREFAB, size=size)
    # dock doors: a 3-cell bay on the east wall, nothing standing on the leveler plates in front
    for r in range(z.h):
        if z.a.g[r][z.w - 1] in '][':
            assert z.a.g[r - 1][z.w - 1] == '_' and z.a.g[r + 1][z.w - 1] == '_', (z.name, 'dock sides', r)
            for rr in (r - 1, r, r + 1):
                for cc in (z.w - 4, z.w - 3, z.w - 2):
                    if z.at(cc, rr) not in '.':
                        errs.append('dock (%d) apron cell (%d,%d) holds %r' % (r, cc, rr, z.at(cc, rr)))
    # stairs land on deck cells, and the rail is open where they land
    for (c, r, w, h) in rects(z.g, 's'):
        for cc in range(c, c + w):
            if z.d.g[r - 1][cc] != 'd':
                errs.append('stair s at (%d,%d) tops out on %r' % (c, r, z.d.g[r - 1][cc]))
    for (c, r, w, h) in rects(z.g, 'l'):     # rises west
        for rr in range(r, r + h):
            if z.d.g[rr][c - 1] != 'd':
                errs.append('stair l at (%d,%d) tops out on %r' % (c, r, z.d.g[rr][c + w]))
    # nothing on the floor under the deck taller than its underside (only low props, columns, pack stations)
    for r in range(z.h):
        for c in range(z.w):
            if z.d.g[r][c] != '.' and z.at(c, r) not in '.SahicumobpqfgnwjexI$x#':
                errs.append('under the deck at (%d,%d): %r' % (c, r, z.at(c, r)))
    return errs, stats


def belt_line(z, r, c0, c1, ch):
    z.run(c0, r, c1 - c0 + 1, ch)


# ================================================================ zone 1: the Production Floor
def zone1():
    W, H, GC = 76, 66, 36
    z = TZone('toyfactory_1', W, H, GC)
    # ---- the pellet loft over the north-west corner (deck at 3.5 m): pellets stored under it, dryers on it
    z.d.rect(1, 1, 16, 9, 'd')
    for c in range(1, 17):
        if c not in (12, 13):
            z.d.g[9][c] = '+'
    for r in range(1, 9):
        if r not in (4, 5):
            z.d.g[r][16] = '+'
    z.block(12, 10, 2, 7, 's')                     # stair up from the moulding aisle (rises north)
    z.block(17, 4, 7, 2, 'l')                      # stair up from the line A aisle (rises west)
    for (c, r) in ((5, 9), (10, 9), (15, 9), (15, 6), (15, 2), (5, 5), (10, 5)):
        z.put(c, r, 'i')
    for (c, r) in ((2, 2), (3, 2), (2, 3), (7, 2), (8, 2), (12, 2), (12, 3)):
        z.put(c, r, 'p')
    for (c, r) in ((2, 6), (3, 6), (8, 6), (12, 6)):
        z.put(c, r, 'q')
    z.put(9, 8, 'j')
    # on the deck: three dryers against the north wall, pellet gaylords and sacks waiting to be loaded
    for c in (2, 6, 10):
        z.d.block(c, 1, 2, 2, 'D', over='d')
    for (c, r) in ((2, 5), (3, 5), (6, 6), (14, 2), (14, 3)):
        z.d.put(c, r, 'p', over='d')
    for (c, r) in ((2, 7), (8, 5), (11, 6), (12, 7)):
        z.d.put(c, r, 'q', over='d')
    z.s.put(8, 10, ']')
    # ---- moulding: five machines along the west wall (front east), a gaylord of parts at each machine's chute,
    # the pellet pipes overhead
    for r0 in (12, 18, 24, 30, 36):
        z.block(1, r0, 2, 5, 'M')
        z.put(4, r0 + 4, 'g')
    z.put(4, 15, 'g')
    z.p.run(1, 10, 31, '|', vertical=True)
    for (c, r) in ((7, 13), (6, 33)):
        z.put(c, r, 'c')
    for (c, r) in ((7, 19), (6, 27), (8, 37)):
        z.put(c, r, 'u')
    z.block(9, 26, 2, 1, 't')
    z.block(9, 30, 2, 1, 't')
    z.s.put(5, 26, '9')
    # ---- the three assembly lines (west halves 18-33, east halves 40-55, exit hood into the packaging machine)
    for r in LINES:
        ch = BELT[r]
        belt_line(z, r, 18, 33, ch)
        belt_line(z, r, 40, 55, ch)
        # stations: robot arms and benches facing the belt, andons at the line heads, tote racks behind
        for c in (21, 45):
            z.put(c, r - 1, 'y')
        for c in (27, 50):
            z.put(c, r + 1, 'Y')
        for c in (19, 42):
            z.block(c, r + 1, 2, 1, 'K')
        for c in (24, 48):
            z.block(c, r - 1, 2, 1, 'k')
        z.put(18, r - 1, 'A')
        z.put(40, r - 1, 'A')
    z.block(56, 13, 6, 3, 'U')       # line A: case packer
    z.block(56, 23, 6, 3, 'V')       # line B: shrink tunnel
    z.block(56, 33, 6, 3, 'L')       # line C: labeller
    # aisles between the lines: tote racks, carts, tote stacks, columns
    for (c, r) in ((22, 17), (50, 21), (46, 27), (30, 31)):
        z.block(c, r, 2, 1, 't')
    for (c, r) in ((25, 19), (42, 30), (54, 38)):
        z.put(c, r, 'c')
    for (c, r) in ((32, 18), (41, 22), (24, 32), (51, 28)):
        z.put(c, r, 'u')
    for (c, r) in ((17, 19), (17, 29), (59, 19), (59, 29)):
        z.put(c, r, 'O')
    for (k, r) in enumerate(LINES):
        z.s.put(25, r, '678'[k])
        z.s.put(48, r, '678'[k])
    # ---- packing: the carton roller line up to the chute in the north wall, pack benches along it, finished goods
    z.run(68, 1, 22, 'r', vertical=True)
    z.art([(68, 0)], 'c')
    for r0 in (4, 9, 14, 19):
        z.block(67, r0, 1, 2, 'b')
    for (c, r) in ((71, 2), (72, 2), (73, 2), (73, 4), (72, 6), (71, 12), (73, 15), (71, 19)):
        z.put(c, r, 'o')
    for (c, r) in ((70, 12), (70, 13), (73, 9)):
        z.put(c, r, 'f')
    z.block(71, 17 - 9, 2, 2, 'W')
    z.put(70, 21, 'j')
    for (c, r) in ((63, 3), (64, 3), (62, 17), (64, 27), (63, 37)):
        z.put(c, r, 'o')
    z.put(65, 9, 'f')
    z.put(62, 28, 'j')
    z.s.put(70, 10, ')')
    # ---- the north wall: logo over the packing aisle, fire points, panel, safety board, an exit
    z.art([(c, 0) for c in range(44, 52)], '*')
    z.art([(20, 0), (60, 0), (0, 22), (W - 1, 30), (0, 48), (W - 1, 50)], 'f')
    z.art([(31, 0), (0, 42)], '`')
    z.art([(42, 0), (W - 1, 44)], '?')
    z.art([(74, 0), (0, 60), (W - 1, 60)], '>')
    z.art([(W - 1, 6), (W - 1, 18)], '(')
    z.art([(W - 1, 12), (W - 1, 24)], ')')
    # ---- the plush corner: the stuffing machine at line C's head, carts of plush
    z.block(12, 36, 3, 3, 'Z')
    z.put(15, 40, 'c')
    z.s.put(13, 41, '<')
    # ---- paint shop (south-west): two booths against the west wall, drying racks, paint drums
    z.block(1, 43, 4, 4, 'B')
    z.block(1, 49, 4, 4, 'B')
    for (c, r) in ((7, 43), (7, 46), (7, 50)):
        z.block(c, r, 2, 1, 'R')
    for (c, r) in ((6, 54), (9, 55), (1, 55), (2, 55), (12, 44)):
        z.put(c, r, 'n')
    z.block(11, 49, 2, 1, 'R')
    z.put(13, 53, 'c')
    z.s.put(8, 48, '(')
    # ---- the showpiece workshop (south): the landmark ROBO-PAL MAX, the rocking horse with its scaffold, the
    # spinning top, giant bricks and alphabet blocks, giant paint pots
    z.block(43, 45, 6, 6, 'H')
    z.block(51, 53, 6, 3, 'Q')
    z.block(57, 51, 2, 2, 'F')
    z.block(22, 49, 3, 3, 'T')
    for (c, r) in ((19, 43), (28, 45), (14, 58), (30, 54), (51, 43), (60, 46)):
        z.block(c, r, 2, 2, 'I')
    z.block(24, 58, 4, 2, 'J')
    z.block(55, 59, 4, 2, 'J')
    for (c, r) in ((27, 51), (20, 55), (32, 58), (49, 54), (62, 56), (17, 49), (41, 59)):
        z.put(c, r, 'e')
    for (c, r) in ((56, 50), (59, 54), (50, 57), (26, 54)):
        z.put(c, r, 'w')
    z.s.put(46, 54, '[')
    # the walk in from the entry: a pair of giant bricks being stacked, blocks and a pot either side of the aisle
    z.block(41, 52, 2, 2, 'I')
    z.block(29, 50, 2, 2, 'I')
    for (c, r) in ((33, 55), (43, 60), (32, 61)):
        z.put(c, r, 'e')
    z.put(31, 57, 'w')
    for (c, r) in ((17, 45), (59, 41), (17, 57), (59, 59)):
        z.put(c, r, 'O')
    # ---- the south-east: finished goods staged for the warehouse, a wrapper, a cart line
    for (c, r) in ((66, 44), (67, 44), (66, 45), (72, 44), (73, 44), (73, 47), (66, 52), (73, 53), (72, 58)):
        z.put(c, r, 'o')
    z.block(70, 50, 2, 2, 'W')
    for (c, r) in ((64, 61), (65, 61), (69, 62)):
        z.put(c, r, 'c')
    z.put(70, 56, 'f')
    z.put(65, 49, 'j')
    # ---- floor marks: aisle lines either side of the main aisle, keep-clear hatch at the exits, play mats
    for c in (34, 40):
        z.mark(c, 2, 1, 60, '^')
    for r in (11, 41):
        z.mark(16, r, 18, 1, '^')
        z.mark(41, r, 21, 1, '^')
    z.mark(73, 1, 2, 1, '/')
    z.mark(1, 59, 1, 3, '/')
    z.mark(W - 2, 59, 1, 3, '/')
    z.mark(20, 47, 7, 7, '&')
    # ---- spawns and pickups
    for (c, r) in ((20, 8), (28, 3), (53, 4), (36, 19), (64, 22), (11, 24), (37, 29), (64, 32), (20, 39), (55, 41), (36, 44), (68, 56)):
        z.put(c, r, 'S')
    for (c, r) in ((36, 9), (14, 33), (61, 51)):
        z.put(c, r, 'a')
    for (c, r) in ((62, 8), (6, 49), (38, 37)):
        z.put(c, r, 'h')
    z.roof()
    return z


# ================================================================ zone 2: the Warehouse
def zone2():
    W, H, GC = 76, 64, 36
    z = TZone('toyfactory_2', W, H, GC)
    z.a.g[0][0] = ','          # warehouse wall finish
    # ---- tall racks: four rows in the west block, a cross aisle at rows 32-35
    RC = (3, 10, 17, 24)
    for c in RC:
        z.block(c, 11, 2, 18, 'N')
        z.block(c, 34, 2, 12, 'N')
    for k, c in enumerate((7, 14, 21)):
        z.s.put(c, 29, '0!?'[k])
        z.s.put(c, 46, ':;,'[k])
    # rack ends and aisles: pallet jacks, a pallet stack, a forklift working an aisle
    for (c, r) in ((8, 20), (15, 42), (22, 25), (1, 12)):
        z.put(c, r, 'j')
    z.block(5, 38, 2, 2, 'x')
    for (c, r) in ((20, 50), (21, 50), (8, 49), (1, 40), (27, 18), (27, 44)):
        z.put(c, r, 'o')
    # ---- north-west: block-stacked finished goods (no racks), a pallet stack, the returns cage
    for (c, r) in ((2, 2), (3, 2), (9, 2), (15, 2), (16, 2), (21, 2), (26, 2), (2, 6)):
        z.put(c, r, 'o')
    z.block(29, 2, 2, 2, 'C')
    z.block(31, 6, 2, 2, 'x')
    z.put(12, 6, 'f')
    z.put(30, 8, 'j')
    # ---- the dispatch mezzanine (north-east, deck at 3.5 m): the dispatch office on it, pick + pack under it
    z.d.rect(44, 1, 20, 11, 'd')
    for c in range(44, 64):
        if c not in (52, 53):
            z.d.g[11][c] = '+'
    for r in range(1, 11):
        z.d.g[r][44] = '+'
        if r not in (5, 6):
            z.d.g[r][63] = '+'
    z.d.block(50, 2, 8, 5, '@', over='d')
    z.block(52, 12, 2, 7, 's')                     # main stair (rises north)
    z.block(64, 5, 7, 2, 'l')                      # east stair (rises west)
    for (c, r) in ((48, 11), (56, 11), (63, 11), (63, 6), (48, 6), (56, 6), (60, 1)):
        z.put(c, r, 'i')
    for (c, r) in ((45, 2), (45, 8), (49, 8), (58, 8)):
        z.block(c, r, 2, 2, 'm')
    for (c, r) in ((61, 3), (61, 4), (52, 9), (54, 9)):
        z.put(c, r, 'u')
    z.put(46, 5, 'c')
    for (c, r) in ((46, 2), (47, 2), (46, 9), (61, 9), (62, 9)):
        z.d.put(c, r, 'o', over='d')
    z.s.put(46, 13, '}')
    # ---- the sortation line: cartons arrive from production through the south wall and run north to the pack area
    z.run(44, 40, 23, 'z', vertical=True)
    z.art([(44, H - 1)], 'c')
    for r0 in (44, 50):
        z.block(43, r0, 1, 2, 'b')
    # ---- the main aisle: forklifts, pallets waiting to go out, columns
    for (c, r) in ((31, 18), (31, 40), (40, 18), (40, 40)):
        z.put(c, r, 'O')
    z.block(34, 24, 2, 3, 'X')
    for (c, r) in ((30, 12), (31, 26), (41, 30), (30, 48), (42, 54), (33, 55)):
        z.put(c, r, 'o')
    z.block(30, 33, 2, 2, 'x')
    z.block(41, 12, 2, 2, 'x')
    z.block(33, 44, 2, 2, 'x')
    z.put(35, 50, 'j')
    # the staging field between the sortation line and the dock lanes: pallet stacks, wrapped loads, a cage
    for (c, r) in ((48, 16), (48, 19), (53, 22), (48, 38), (53, 41), (48, 47)):
        z.block(c, r, 2, 2, 'x')
    for (c, r) in ((50, 16), (51, 16), (50, 17), (53, 25), (54, 25), (50, 39), (50, 40), (52, 44), (50, 48), (51, 48), (29, 22), (30, 22)):
        z.put(c, r, 'o')
    z.block(51, 28, 2, 2, 'C')
    # the south strip: a pallet stack and a cage by the chargers
    z.block(15, 52, 2, 2, 'x')
    z.block(26, 56, 2, 2, 'C')
    # ---- receiving / shipping: seven dock doors on the east wall (four with a trailer), staging lanes, forklifts
    for k, r in enumerate((17, 23, 29, 35, 41, 47, 53)):
        z.a.g[r - 1][W - 1] = '_'
        z.a.g[r + 1][W - 1] = '_'
        z.a.g[r][W - 1] = ']' if k % 2 == 0 else '['
    for (c, r) in ((66, 16), (67, 16), (62, 17), (66, 24), (67, 22), (62, 29), (66, 28), (63, 35), (66, 36),
                   (62, 41), (67, 42), (63, 47), (66, 46), (66, 52), (67, 54)):
        z.put(c, r, 'o')
    for (c, r) in ((69, 20), (69, 38), (69, 50)):
        z.put(c, r, 'j')
    z.block(60, 25, 2, 3, 'X')
    z.block(64, 43, 2, 3, 'X')
    z.block(58, 33, 2, 2, 'W')
    z.block(58, 57, 2, 2, 'C')
    z.block(68, 57, 2, 1, 'v')
    z.put(72, 59, 'u')
    z.s.put(62, 32, '{')
    z.art([(W - 1, 10), (W - 1, 58)], 'f')
    z.art([(W - 1, 4)], '`')
    # ---- the south strip: forklift charging on the south wall, drums, bins
    z.block(6, 62, 2, 1, '$')
    z.block(12, 62, 2, 1, '$')
    z.block(7, 58, 2, 3, 'X')
    for (c, r) in ((18, 62), (19, 62), (26, 62)):
        z.put(c, r, '`')
    z.block(22, 62, 2, 1, 'v')
    z.art([(0, 20), (0, 46), (16, 0), (60, 0), (30, H - 1), (58, H - 1)], 'f')
    z.art([(0, 33), (24, 0)], '`')
    z.art([(0, 56), (10, H - 1)], '?')
    z.art([(0, 8), (70, 0)], '>')
    # floor marks: the walkway from the entry, aisle lines, keep-clear at the exits
    z.mark(36, 52, 3, 9, '%')
    for c in (29, 43):
        z.mark(c, 2, 1, 58, '^')
    for r in (21, 27, 33, 39, 45, 51):
        z.mark(58, r, 15, 1, '^')
    z.mark(70, 1, 2, 1, '/')
    z.mark(1, 7, 1, 3, '/')
    # ---- spawns and pickups
    for (c, r) in ((7, 6), (24, 7), (37, 11), (8, 33), (21, 33), (36, 30), (56, 22), (70, 26), (56, 40), (70, 45), (8, 54), (22, 54)):
        z.put(c, r, 'S')
    for (c, r) in ((14, 32), (53, 31), (64, 4)):
        z.put(c, r, 'a')
    for (c, r) in ((28, 9), (60, 50), (42, 37)):
        z.put(c, r, 'h')
    z.roof()
    return z


def main():
    zones = []
    for fn, size in ((zone1, ((76, 76), (66, 66))), (zone2, ((76, 76), (64, 64)))):
        z = fn()
        errs, stats = check(z, size)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
