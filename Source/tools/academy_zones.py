#!/usr/bin/env python3
"""INKBOLT Chalkstone Academy zones (theme 'academy'): hand-placed layouts -> src/data/zones/academy_*.txt

    python3 tools/academy_zones.py            # write + validate
    python3 tools/academy_zones.py --print    # ... and print the maps
    python3 tools/academy_zones.py --check    # validate only

Every zone file has the floor plan and these layers (symbols: see src/data/themes/academy.js):
  "@layer 0.006" floor finishes (lab epoxy, the lobby crest, gym maple, lawn, mulch)
  "@layer 0.012" overlays on the finishes (the basketball court lines)
  "@layer 0.02"  data (theme.dataLayers: never built as symbols): art codes for the south / east face of wall cells,
                 'o' on open cells that are outdoors (the courtyard: exterior brick on the walls facing them)
  "@layer 0.03"  data: art codes for the north / west face of wall cells
  "@layer 4"     ceiling tiles of the 4 m rooms (classrooms, corridors, labs, offices; one tile a cell)
  "@layer 4"     the library mezzanine deck in the cafeteria (deck, rails, shelves, tables)  [zone 1]
  "@layer 8"     roof bays [2, 2] over the double-height spaces (lobby, cafeteria, gym)

Zone 1, the main building (72 x 70): the entrance hall in the south (player at (35, 67)) with the trophy cases, the
crest and the main office; the main corridor; the west and east corridors and the central spine hall, lockers along
all of them; classrooms, the computer lab, the art room, the robotics lab, the chemistry and biology labs, the
teachers' lounge; the CAFETERIA (landmark) with the library mezzanine on its west side (two stairs); exit gate on the
cafeteria's north wall (columns 34-36).
Zone 2, the gymnasium and the courtyard (72 x 72): the gym lobby in the south-east (player at (59, 69)) with the
snack bar, the locker room and the equipment room; the GYMNASIUM (stage, two banks of pulled-out bleachers, the
court, hoops, mats); three doors north into the COURTYARD: the big tree (landmark) in the lawn quad, the covered
walkway, the flagpole, planters, benches, picnic tables, bike racks, the outdoor classroom tiers; exit gate in the
north facade (columns 34-36).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

# floor plan symbols you can stand on / walk through (doorways are wall.passage cells, the header and the canopy
# leave the floor open, the stage / bleachers / stairs / tiers are climbed)
WALK = set('D7OQn3')
PREFAB = {
    'D': (2, 1), '7': (2, 1), 'O': (3, 1), 'Q': (3, 1), 'T': (2, 1), 't': (2, 1), 'K': (2, 1), 'g': (2, 2), 'A': (2, 2),
    'k': (3, 1), 'c': (2, 1), 'C': (2, 2), 'L': (4, 2), 'F': (2, 1), 'X': (2, 1), 'M': (4, 1), 'm': (4, 1),
    'w': (3, 2), 'R': (6, 2), 'o': (2, 1), 's': (2, 1), 'y': (3, 1), 'Y': (2, 2), 'B': (2, 1), 'Z': (10, 3),
    'l': (6, 2), 'z': (3, 1), '-': (2, 2), '*': (2, 2), 'N': (2, 7), 'U': (2, 7), '{': (8, 5), '}': (8, 5), '<': (2, 1), '>': (2, 1),
    '&': (14, 6), '%': (2, 1), '@': (9, 9), 'r': (4, 2), '1': (2, 2), '2': (4, 1), '3': (2, 4), '4': (2, 2),
    '6': (10, 4), '8': (2, 2), '9': (6, 2), '0': (2, 1), ')': (2, 1),
}
DOORS = 'D7OQ'
CEIL_SKIP = set('#D7OQGE')   # no ceiling tile over walls, doors and gates


class AZone(Zone):
    """floor plan + finishes (f) + overlays (v) + art codes (A: S/E faces, B: N/W faces) + ceiling (c) + deck (d)
    + roof (rf)"""

    def __init__(self, name, w, h, gc, ec, p):
        Zone.__init__(self, name, w, h)
        self.f = Zone(name + '_f', w, h)
        self.v = Zone(name + '_v', w, h)
        self.A = Zone(name + '_A', w, h)
        self.B = Zone(name + '_B', w, h)
        self.c = Zone(name + '_c', w, h)
        self.d = Zone(name + '_d', w, h)
        self.rf = Zone(name + '_r', w, h)
        self.tall = set()        # cells under the 8 m roof (no ceiling tiles)
        self.lights = set()      # ceiling cells that get a light panel
        self.doors = []
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gc, 0, 3, 1, 'G')
        self.rect(ec, h - 1, 3, 1, 'E')
        self.put(p[0], p[1], 'P')

    # ---- structure
    def wall(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '#')

    def door(self, c0, r0, w, h, ch='D'):
        """'D' / 'O' / 'Q': door leaves folded back on the north / west side, '7': on the south / east side"""
        self.doors.append((c0, r0, w, h, ch))
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '#', (self.name, 'door off the wall', c, r)
        self.rect(c0, r0, w, h, ch)

    def opening(self, c0, r0, w, h):
        """an open archway in a wall line: the cells become floor with a header ('n') over them"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '#', (self.name, 'opening off the wall', c, r)
        self.rect(c0, r0, w, h, 'n')

    def art(self, c, r, side, code, n=1, step=None):
        """art code on the `side` ('N', 'S', 'E', 'W') face of wall cell (c, r); n cells along the wall"""
        dc, dr = step or ((1, 0) if side in 'NS' else (0, 1))
        L = self.A if side in 'SE' else self.B
        for k in range(n):
            cc, rr = c + dc * k, r + dr * k
            assert self.g[rr][cc] == '#', (self.name, 'art on a non-wall cell', cc, rr, self.g[rr][cc], code)
            o = {'S': (0, 1), 'N': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[side]
            assert self.at(cc + o[0], rr + o[1]) not in '#' + DOORS, (self.name, 'art face not open', cc, rr, side, code)
            assert L.g[rr][cc] == '.', (self.name, 'art twice', cc, rr, side, L.g[rr][cc], code)
            L.g[rr][cc] = code

    def outdoors(self, c0, r0, w, h):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.g[r][c] not in '#' + DOORS + 'GE':
                    self.A.g[r][c] = 'o'

    def fin(self, c0, r0, w, h, ch, over='.'):
        self.f.pave(c0, r0, w, h, ch, over)

    def high(self, c0, r0, w, h):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.tall.add((c, r))

    def roof(self, c0, r0, w, h, pick):
        """roof bays [2, 2] over a double-height room; pick(i, j) -> symbol per bay"""
        assert w % 2 == 0 and h % 2 == 0, (self.name, 'roof block', c0, r0, w, h)
        self.high(c0, r0, w, h)
        for j in range(h // 2):
            for i in range(w // 2):
                self.rf.rect(c0 + 2 * i, r0 + 2 * j, 2, 2, pick(i, j))

    def lightgrid(self, c0, r0, w, h, every=(3, 3), off=(1, 1)):
        for r in range(r0 + off[1], r0 + h, every[1]):
            for c in range(c0 + off[0], c0 + w, every[0]):
                self.lights.add((c, r))

    def ceiling(self):
        """tiles over every indoor 4 m cell: [2, 2] groups on the even grid where all four cells are free ('*' with a
        light panel where the room's light grid falls in it, '-' plain), single cells elsewhere"""
        def free(c, r):
            return (0 < c < self.w - 1 and 0 < r < self.h - 1 and self.g[r][c] not in CEIL_SKIP and (c, r) not in self.tall
                    and self.A.g[r][c] != 'o' and self.c.g[r][c] == '.')
        for (oc, orr) in ((1, 1), (2, 1), (1, 2), (2, 2)):
            for r in range(orr, self.h - 2, 2):
                for c in range(oc, self.w - 2, 2):
                    cells = [(c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)]
                    if all(free(*p) for p in cells):
                        lit = any(p in self.lights for p in cells) and (c // 2) % 2 == 0 and (r // 2) % 2 == 0
                        for (cc, rr) in cells:
                            self.c.g[rr][cc] = '*' if lit else '-'
        for r in range(1, self.h - 1):
            for c in range(1, self.w - 1):
                if free(c, r):
                    self.c.g[r][c] = '+' if (c, r) in self.lights else '='

    def text(self):
        out = Zone.text(self)
        for y, L in (('0.006', self.f), ('0.012', self.v), ('0.02', self.A), ('0.03', self.B), ('4', self.c), ('4', self.d), ('8', self.rf)):
            if any(ch != '.' for row in L.g for ch in row):
                out += '@layer %s\n' % y + L.text()
        return out


def desks(z, c0, r0, cols, rows, ch='d', dc=2, dr=2):
    for j in range(rows):
        for i in range(cols):
            z.put(c0 + i * dc, r0 + j * dr, ch)


def check_codes(z):
    """art codes never sit on a cell a symbol could claim: they live in data layers only"""
    for L in (z.A, z.B):
        for r in range(z.h):
            for c in range(z.w):
                ch = L.g[r][c]
                if ch != '.' and ch != 'o':
                    assert z.g[r][c] == '#', (z.name, 'code off wall', c, r, ch)


# =========================================================================================================== zone 1
def zone1():
    z = AZone('academy_1', 72, 70, 34, 34, (35, 67))
    W, H = 72, 70
    # ---- wall lines
    z.wall(0, 27, W, 1)          # cafeteria south wall / north band
    z.wall(0, 50, W, 1)          # main corridor north wall
    z.wall(0, 56, W, 1)          # main corridor south wall
    z.wall(13, 0, 1, 51)         # west corridor walls
    z.wall(18, 0, 1, 51)
    z.wall(53, 0, 1, 51)         # east corridor walls
    z.wall(58, 0, 1, 51)
    z.wall(0, 13, 14, 1)         # 101 | 103
    z.wall(58, 13, 14, 1)        # 102 | 104
    z.wall(32, 27, 1, 24)        # spine hall walls
    z.wall(39, 27, 1, 24)
    z.wall(18, 39, 15, 1)        # 107 | 109
    z.wall(58, 39, 14, 1)        # 108 | 110
    z.wall(1, 39, 12, 11)        # restrooms block (closed doors on the west corridor)
    z.wall(13, 56, 1, 13)        # south band: 113 | lounge | lobby | office | 115
    z.wall(25, 56, 1, 13)
    z.wall(46, 56, 1, 13)
    z.wall(59, 56, 1, 13)
    # corridor ends meet the main corridor; the spine meets the main corridor and the cafeteria
    z.rect(14, 50, 4, 1, '.')
    z.rect(54, 50, 4, 1, '.')
    z.rect(33, 50, 6, 1, '.')
    z.rect(14, 27, 4, 1, '.')
    z.rect(54, 27, 4, 1, '.')
    z.opening(33, 27, 6, 1)      # the spine opens into the cafeteria under a header
    z.opening(31, 56, 10, 1)     # the lobby opens onto the main corridor under a header
    # ---- doors
    z.door(13, 9, 1, 2)          # 101 math
    z.door(13, 16, 1, 2)         # 103 computer lab
    z.door(13, 30, 1, 2)         # 105 art
    z.door(58, 9, 1, 2, '7')     # 102 chemistry
    z.door(58, 16, 1, 2, '7')    # 104 biology
    z.door(58, 30, 1, 2, '7')    # 108
    z.door(58, 44, 1, 2, '7')    # 110
    z.door(32, 30, 1, 2)         # 107 from the spine
    z.door(18, 35, 1, 2, '7')    # 107 from the west corridor
    z.door(32, 44, 1, 2)         # 109 from the spine
    z.door(18, 46, 1, 2, '7')    # 109 from the west corridor
    z.door(39, 31, 1, 2, '7')    # robotics from the spine
    z.door(39, 45, 1, 2, '7')    # robotics from the spine (south)
    z.door(53, 38, 1, 2)         # robotics from the east corridor
    z.door(9, 56, 2, 1, '7')     # 113
    z.door(16, 56, 2, 1, '7')    # teachers' lounge
    z.door(61, 56, 2, 1, '7')    # 115
    z.door(49, 56, 2, 1, '7')    # main office from the corridor
    z.door(46, 65, 1, 2, '7')    # main office from the lobby
    z.door(18, 20, 1, 3, 'O')    # cafeteria from the west corridor
    z.door(53, 10, 1, 3, 'O')    # cafeteria from the east corridor
    z.door(53, 20, 1, 3, 'O')

    # ---- double-height spaces: the cafeteria (+ library mezzanine) and the lobby
    z.roof(19, 1, 34, 26, lambda i, j: '!' if (i in (6, 11) and j in (4, 8)) else (';' if (i % 3 == 1 and j % 3 == 1) else ':'))
    z.roof(26, 57, 20, 12, lambda i, j: '!' if (i in (3, 6) and j == 2) else (';' if (i % 3 == 1 and j % 2 == 1) else ':'))
    z.high(31, 56, 10, 1)        # the header cells
    z.high(33, 27, 6, 1)

    # ================================================= north band
    # 101 Math (desks face the whiteboard on the north wall; windows on the west wall)
    desks(z, 2, 4, 5, 3, 'd', 2, 2)          # cols 2-10, rows 4-8
    z.block(9, 2, 2, 1, 'T')
    z.block(1, 12, 2, 1, 'K')
    z.put(11, 11, 'i')
    z.art(3, 0, 'S', 'w', 6)                 # whiteboard
    z.art(10, 0, 'S', 'k')                   # clock
    z.art(0, 2, 'E', 'y', 10)                # windows
    z.art(4, 13, 'N', 'p', 2)                # posters on the back wall
    z.art(8, 13, 'N', 'b', 2)                # cork board
    z.art(13, 2, 'W', 'm', 1)                # math chart
    z.lightgrid(1, 1, 12, 12)
    # 103 Computer lab: desks along the west wall and the south wall, two islands
    z.block(1, 15, 1, 2, 'c'); z.block(1, 18, 1, 2, 'c'); z.block(1, 21, 1, 2, 'c'); z.block(1, 24, 1, 2, 'c')
    z.block(4, 26, 2, 1, 'c'); z.block(7, 26, 2, 1, 'c')
    z.block(5, 17, 2, 2, 'C'); z.block(5, 21, 2, 2, 'C'); z.block(9, 17, 2, 2, 'C'); z.block(9, 21, 2, 2, 'C')
    z.block(10, 14, 2, 1, 'T')
    z.put(12, 25, 'p')
    z.art(0, 15, 'E', 'y', 11)
    z.art(4, 13, 'S', 'w', 5)
    z.art(13, 20, 'W', 'q', 2)              # code poster
    z.lightgrid(1, 14, 12, 13)
    # 102 Chemistry: four lab benches, fume hoods on the east wall, demo bench at the front (north), cabinets
    z.block(60, 4, 4, 2, 'L'); z.block(66, 4, 4, 2, 'L')
    z.block(60, 8, 4, 2, 'L'); z.block(66, 8, 4, 2, 'L')
    z.block(70, 2, 1, 2, 'F'); z.block(70, 10, 1, 2, 'F')
    z.block(62, 1, 4, 1, 'M')
    z.block(59, 1, 1, 2, 'X')
    z.art(61, 0, 'S', 'w', 6)
    z.art(67, 0, 'S', 'T', 3)                # periodic table (3 cells)
    z.art(71, 5, 'W', 'e', 1)                # eyewash / safety shower
    z.art(71, 7, 'W', 'x', 1)                # fire extinguisher
    z.art(64, 13, 'N', 'p', 2)
    z.art(68, 13, 'N', 'T', 3)
    z.fin(59, 1, 12, 12, '_')
    z.lightgrid(59, 1, 12, 12)
    # 104 Biology: lab benches, the skeleton model, specimen cabinets, demo bench
    z.block(60, 17, 4, 2, 'L'); z.block(66, 17, 4, 2, 'L')
    z.block(60, 21, 4, 2, 'L'); z.block(66, 21, 4, 2, 'L')
    z.block(62, 14, 4, 1, 'M')
    z.put(69, 15, 'x')                       # the skeleton model in the corner by the board
    z.block(70, 24, 1, 2, 'X')
    z.block(65, 26, 2, 1, 'K')
    z.block(70, 17, 1, 2, 'F')
    z.art(60, 13, 'S', 'w', 5)
    z.art(66, 13, 'S', 'T', 3)
    z.art(71, 21, 'W', 'e', 1)
    z.art(59, 27, 'N', 'n', 2)               # cell-diagram posters
    z.art(62, 27, 'N', 'p', 2)
    z.fin(59, 14, 12, 13, '_')
    z.lightgrid(59, 14, 12, 13)

    # ---- the CAFETERIA (landmark) and the library mezzanine
    z.block(40, 1, 10, 3, 'Z')               # serving line on the north wall
    z.art(40, 0, 'S', 'u', 10)               # kitchen pass and menu boards behind it
    z.block(50, 1, 3, 1, 'z')                # tray return
    z.put(39, 1, 'W')                        # milk cooler
    z.put(30, 1, 'v'); z.put(31, 1, 'v')     # vending machines on the north wall
    for (c, r) in ((38, 6), (45, 6), (31, 10), (38, 10), (45, 10), (31, 15), (38, 15), (45, 15), (38, 20), (45, 20),
                   (45, 24)):
        z.block(c, r, 6, 2, 'l')
    z.put(52, 4, 'i'); z.put(52, 17, 'i'); z.put(30, 25, 'i')
    # under the mezzanine (cols 19-28, rows 1-17): vending wall, tables, deck columns
    for r in (2, 3, 4, 5, 6):
        z.put(19, r, 'v')
    z.block(20, 9, 6, 2, 'l')
    z.block(20, 13, 6, 2, 'l')
    for (c, r) in ((28, 4), (28, 11), (28, 16), (23, 16)):
        z.put(c, r, 'I')
    z.block(21, 18, 2, 7, 'N')               # stair A rising north onto the deck at row 17
    z.block(29, 7, 7, 2, 'U')                # stair B rising west onto the deck at column 28
    z.art(18, 6, 'E', 'L', 5)                # LIBRARY lettering high on the west wall over the mezzanine
    z.art(19, 0, 'S', 'c', 10)               # clerestory windows over the library
    z.art(53, 2, 'W', 'c', 6)
    z.art(53, 15, 'W', 'c', 3)
    z.art(19, 27, 'N', 'C', 8)               # CHALKSTONE CAFE lettering high on the south wall
    z.art(40, 27, 'N', 'c', 13)
    z.art(52, 0, 'S', 'k', 1)
    # deck layer: deck slab over cols 19-28 rows 1-17, rail on its open edges, shelves, tables, the desk
    D = z.d
    D.rect(19, 1, 10, 17, 'u')
    for r in range(1, 18):
        if r not in (7, 8):
            D.g[r][28] = '|'
    for c in range(19, 29):
        if c not in (21, 22):
            D.g[17][c] = '|'
    D.rect(20, 2, 3, 1, 'H'); D.rect(24, 2, 3, 1, 'H')
    D.rect(20, 5, 3, 1, 'H'); D.rect(24, 5, 3, 1, 'H')
    D.rect(20, 10, 3, 1, 'H'); D.rect(24, 10, 3, 1, 'H')
    D.rect(20, 13, 2, 2, 'J'); D.rect(24, 13, 2, 2, 'J')
    D.rect(23, 8, 4, 2, 'V')
    D.g[15][19] = 'j'
    D.g[9][19] = 'a'                         # ammo on the mezzanine (high ground)

    # ================================================= middle band
    # 105 Art room: big tables, easels, the sink counter, supply shelves, drying rack
    z.block(2, 30, 2, 2, 'A'); z.block(6, 30, 2, 2, 'A'); z.block(2, 34, 2, 2, 'A'); z.block(6, 34, 2, 2, 'A')
    z.put(10, 30, 'e'); z.put(11, 32, 'e'); z.put(10, 35, 'e')
    z.block(1, 38, 3, 1, 'k')
    z.block(5, 38, 2, 1, 'K'); z.block(8, 38, 2, 1, 'K')
    z.art(0, 29, 'E', 'y', 9)
    z.art(3, 27, 'S', 'r', 6)                # student art on the north wall
    z.art(13, 34, 'W', 'b', 2)
    z.lightgrid(1, 28, 12, 11)
    # restroom doors and the janitor's closet on the corridor
    z.art(13, 41, 'E', 'B', 1)
    z.art(13, 47, 'E', 'g', 1)
    z.art(13, 44, 'E', 'f', 1)               # drinking fountain
    z.art(13, 49, 'E', 'J', 1)
    # 107 English: group tables (pods of four), a reading corner, the board on the west wall
    for (c, r) in ((22, 29), (26, 29), (22, 33), (26, 33), (29, 36)):
        z.block(c, r, 2, 2, 'g')
    z.block(20, 38, 2, 1, 'K')
    z.block(29, 29, 2, 1, 'T')
    z.art(22, 27, 'S', 'w', 6)
    z.art(19, 39, 'N', 'r', 4)
    z.art(25, 39, 'N', 'b', 2)
    z.art(32, 34, 'W', 'p', 2)
    z.lightgrid(19, 28, 13, 11)
    # 109 History: desks face south (board on the main corridor wall), a map, a timeline
    desks(z, 20, 41, 5, 3, 'q', 2, 2)       # cols 20-28, rows 41-45
    z.block(24, 48, 2, 1, 't')
    z.block(31, 41, 1, 2, 'K')
    z.art(21, 50, 'N', 'w', 6)
    z.art(19, 39, 'S', 'M', 3)               # world map
    z.art(23, 39, 'S', 'p', 2)
    z.art(27, 39, 'S', 'i', 4)               # timeline
    z.lightgrid(19, 40, 13, 10)
    # the spine hall: lockers both sides, benches, a display case
    z.art(32, 33, 'E', 'l', 10)
    z.art(39, 34, 'W', 'l', 10)
    z.art(32, 28, 'E', 'l', 2)
    z.art(39, 28, 'W', 'l', 3)
    z.art(39, 47, 'W', 'x', 1)
    z.art(32, 47, 'E', 'k', 1)
    z.block(35, 37, 2, 1, 'B')
    z.put(33, 46, 'i')
    z.lightgrid(33, 28, 6, 22, (3, 3), (1, 1))
    # 111 Robotics lab: workbenches with half-built robot arms, a parts shelf, the club banner
    for (c, r) in ((42, 30), (47, 30), (42, 35), (47, 35), (42, 41), (47, 41)):
        z.block(c, r, 3, 2, 'w')
    z.block(52, 28, 1, 2, 'K'); z.block(52, 43, 1, 2, 'K')
    z.put(52, 33, 'p')
    z.art(41, 27, 'S', 'R', 8)               # ROBOTICS CLUB banner
    z.art(53, 30, 'W', 'w', 5)
    z.art(41, 50, 'N', 'r', 6)
    z.art(39, 37, 'E', 'b', 2)
    z.lightgrid(40, 28, 13, 22)
    # 108 and 110: classrooms on the east wing
    desks(z, 61, 31, 5, 2, 'd', 2, 3)        # 108: desks face north
    z.block(65, 28, 2, 1, 'T')
    z.block(69, 38, 2, 1, 'K')
    z.art(61, 27, 'S', 'w', 6)
    z.art(71, 29, 'W', 'y', 9)
    z.art(60, 39, 'N', 'p', 2)
    z.art(66, 39, 'N', 'b', 2)
    z.lightgrid(59, 28, 12, 11)
    desks(z, 60, 41, 3, 4, 'q', 2, 2)        # 110: desks face south (board on the main corridor wall)
    z.block(67, 41, 2, 2, 'g'); z.block(67, 45, 2, 2, 'g')
    z.block(62, 48, 2, 1, 't')
    z.art(60, 50, 'N', 'w', 6)
    z.art(71, 41, 'W', 'y', 8)
    z.art(66, 39, 'S', 'M', 3)
    z.lightgrid(59, 40, 12, 10)

    # ---- corridors: lockers, fountains, extinguishers, the trophy wall, notice boards
    z.art(13, 2, 'E', 'l', 6)
    z.art(13, 19, 'E', 'l', 7)
    z.art(18, 2, 'W', 'l', 5)
    z.art(18, 10, 'W', 'l', 9)
    z.art(18, 25, 'W', 'x', 1)
    z.art(13, 26, 'E', 'b', 2)
    z.art(18, 29, 'W', 'l', 5)
    z.art(18, 38, 'W', 'l', 7)
    z.art(13, 33, 'E', 'l', 5)
    z.art(18, 48, 'W', 'k', 1)
    z.art(53, 2, 'E', 'l', 7)
    z.art(53, 14, 'E', 'l', 5)
    z.art(53, 25, 'E', 'x', 1)
    z.art(53, 28, 'E', 'l', 9)
    z.art(53, 41, 'E', 'l', 8)
    z.art(58, 2, 'W', 'l', 6)
    z.art(58, 19, 'W', 'l', 7)
    z.art(58, 33, 'W', 'l', 10)
    z.art(58, 47, 'W', 'f', 1)
    z.art(14, 0, 'S', 'y', 4)                # windows at the corridor ends
    z.art(54, 0, 'S', 'y', 4)
    z.lightgrid(14, 1, 4, 50, (3, 3), (1, 1))
    z.lightgrid(54, 1, 4, 50, (3, 3), (2, 1))
    # main corridor (rows 51-55)
    z.art(1, 50, 'S', 'l', 12)
    z.art(19, 50, 'S', 'l', 13)
    z.art(40, 50, 'S', 'l', 13)
    z.art(59, 50, 'S', 'l', 12)
    z.art(1, 56, 'N', 'l', 8)
    z.art(14, 56, 'N', 'b', 2)
    z.art(19, 56, 'N', 'l', 6)
    z.art(26, 56, 'N', 'x', 1)
    z.art(42, 56, 'N', 'k', 1)
    z.art(52, 56, 'N', 'l', 6)
    z.art(64, 56, 'N', 'l', 7)
    z.art(0, 52, 'E', 'y', 3)
    z.art(71, 52, 'W', 'y', 3)
    z.lightgrid(1, 51, 70, 5, (3, 5), (1, 2))
    z.block(5, 54, 2, 1, 'B'); z.block(66, 54, 2, 1, 'B')
    z.put(24, 55, 'i'); z.put(47, 51, 'i')

    # ================================================= south band
    # 113 classroom (desks face north; the board on the main corridor wall)
    desks(z, 2, 60, 4, 3, 'd', 2, 2)
    z.block(4, 57, 2, 1, 'T')
    z.block(1, 68, 2, 1, 'K')
    z.art(2, 56, 'S', 'w', 6)
    z.art(0, 58, 'E', 'y', 10)
    z.art(4, 69, 'N', 'p', 2)
    z.art(8, 69, 'N', 'b', 2)
    z.lightgrid(1, 57, 12, 12)
    # teachers' lounge
    z.block(14, 60, 1, 2, 's'); z.block(14, 64, 1, 2, 's')
    z.block(17, 61, 2, 2, 'Y'); z.block(21, 61, 2, 2, 'Y')
    z.block(19, 68, 3, 1, 'y')
    z.put(24, 67, 'p'); z.put(14, 67, 'j'); z.put(24, 58, 'f')
    z.art(14, 69, 'N', 'b', 2)
    z.art(25, 61, 'W', 'p', 2)
    z.lightgrid(14, 57, 11, 12)
    # the LOBBY (entrance hall): trophy cases, the crest in the floor, the office window, benches, banners
    z.art(25, 58, 'E', 't', 6)               # trophy cases on the west wall
    z.art(46, 59, 'W', 'O', 5)               # main office glass + counter
    z.art(27, 56, 'S', 'h', 3)               # honour roll
    z.art(42, 56, 'S', 'h', 3)
    z.art(25, 65, 'E', 'x', 1)
    z.art(46, 57, 'W', 'k', 1)
    z.art(27, 69, 'N', 'y', 6)               # entrance glazing either side of the doors
    z.art(39, 69, 'N', 'y', 6)
    z.fin(32, 59, 6, 6, '^')                 # the crest
    z.block(28, 66, 2, 1, 'B'); z.block(41, 66, 2, 1, 'B')
    z.block(28, 60, 1, 2, 'B'); z.block(43, 60, 1, 2, 'B')
    z.put(26, 57, 'j'); z.put(45, 57, 'j'); z.put(26, 68, 'j'); z.put(45, 68, 'j')
    z.put(31, 58, 'b'); z.put(40, 58, 'b')
    # main office: reception counter facing the lobby window, desks, files, the copier
    z.block(48, 59, 2, 6, 'R')
    z.block(52, 58, 2, 1, 'o'); z.block(52, 62, 2, 1, 'o'); z.block(55, 58, 2, 1, 'o'); z.block(55, 62, 2, 1, 'o')
    for (c, r) in ((58, 57), (58, 58), (58, 59), (57, 68), (58, 68)):
        z.put(c, r, 'f')
    z.put(52, 68, 'p'); z.put(47, 68, 'j')
    z.block(53, 66, 2, 2, 'Y')
    z.art(59, 62, 'W', 'b', 2)
    z.art(47, 69, 'N', 'y', 4)
    z.lightgrid(47, 57, 12, 12)
    # 115 classroom (desks face north, board on the corridor wall)
    desks(z, 62, 60, 4, 3, 'd', 2, 2)
    z.block(65, 57, 2, 1, 'T')
    z.block(69, 68, 2, 1, 'K')
    z.art(64, 56, 'S', 'w', 6)
    z.art(71, 58, 'W', 'y', 10)
    z.art(62, 69, 'N', 'p', 2)
    z.art(66, 69, 'N', 'r', 3)
    z.lightgrid(60, 57, 11, 12)

    # ---- spawns, pickups
    for (c, r) in ((35, 13), (44, 18), (27, 22), (16, 6), (16, 40), (56, 6), (56, 33), (36, 41), (8, 53), (66, 52), (46, 33)):
        z.put(c, r, 'S')
    z.puts([(15, 52), (36, 30)], 'a')
    z.puts([(56, 52), (47, 13), (16, 25)], "h")
    z.ceiling()
    check_codes(z)
    return z


# =========================================================================================================== zone 2
def zone2():
    z = AZone('academy_2', 72, 72, 34, 58, (59, 69))
    W, H = 72, 72
    z.wall(0, 40, W, 1)          # the gym's north wall (courtyard facade)
    z.wall(47, 40, 1, 31)        # gym | east wing
    z.wall(48, 56, 23, 1)        # locker room / equipment | gym lobby
    z.wall(62, 41, 1, 15)        # locker room | equipment room
    z.door(7, 40, 3, 1, 'Q')     # gym -> courtyard (west)
    z.door(42, 40, 3, 1, 'Q')    # gym -> courtyard (east, under the covered walkway)
    z.door(53, 40, 3, 1, 'Q')    # locker room -> courtyard
    z.door(47, 58, 1, 3, 'O')    # gym lobby -> gym
    z.door(47, 44, 1, 2, '7')    # locker room -> gym
    z.door(52, 56, 2, 1)         # lobby -> locker room
    z.door(66, 56, 2, 1)         # lobby -> equipment room

    # ---- the GYMNASIUM (cols 1-46, rows 41-70)
    z.roof(1, 41, 46, 30, lambda i, j: ('?' if i % 3 == 1 else '/') if j % 2 == 1 else '~')
    z.fin(1, 41, 46, 30, '[')
    z.v.rect(10, 48, 28, 16, ']')            # the court lines
    z.block(1, 49, 6, 14, '&')               # the stage at the west end (front east)
    z.block(10, 41, 32, 5, '{')              # north bleachers (front south)
    z.block(10, 66, 32, 5, '}')              # south bleachers (front north)
    z.block(10, 55, 1, 2, '>')               # hoops over the baselines (hung from the roof)
    z.block(37, 55, 1, 2, '<')
    z.block(43, 66, 2, 1, '%'); z.block(43, 68, 2, 1, '%')   # folded mats
    z.block(1, 64, 2, 1, '%')
    z.put(44, 47, '$'); z.put(45, 49, '$'); z.put(2, 46, '$')
    z.art(47, 49, 'W', 'P', 3)               # wall pads at the court's east end, the scoreboard over them
    z.art(47, 54, 'W', 'P', 3)
    z.art(47, 62, 'W', 'P', 3)
    z.art(0, 41, 'E', 'F', 7)                # flag banners... high on the west wall over the stage door side
    z.art(1, 40, 'S', 'c', 6)
    z.art(12, 40, 'S', 'V', 26)              # championship banners high on the north wall
    z.art(14, 71, 'N', 'V', 24)
    z.art(47, 52, 'W', 's', 2)               # the scoreboard over the east end... (upper wall)
    z.art(47, 65, 'W', 'x', 1)
    z.art(0, 64, 'E', 'x', 1)
    # ---- east wing: locker room (cols 48-61, rows 41-55)
    z.art(48, 40, 'S', 'l', 5)
    z.art(56, 40, 'S', 'l', 6)
    z.art(47, 47, 'E', 'l', 8)
    z.art(62, 42, 'W', 'l', 13)
    z.art(48, 56, 'N', 'l', 3)
    z.art(55, 56, 'N', 'l', 7)
    for (c, r) in ((51, 45), (51, 49), (56, 45), (56, 49)):
        z.block(c, r, 2, 1, 'B')
    z.put(61, 53, 'i')
    z.lightgrid(48, 41, 14, 15)
    # equipment room (cols 63-70, rows 41-55)
    z.block(70, 42, 1, 2, ')'); z.block(70, 46, 1, 2, ')'); z.block(70, 50, 1, 2, ')')
    z.put(65, 43, '$'); z.put(66, 48, '$'); z.put(64, 52, '$')
    z.block(63, 54, 2, 1, '%')
    z.lightgrid(63, 41, 8, 15)
    # gym lobby (cols 48-70, rows 57-70): the snack bar, trophy wall, benches
    z.block(56, 57, 6, 2, '9')               # SNACK SHACK counter on the north wall
    z.block(50, 62, 2, 1, '0')               # ticket table
    z.art(71, 59, 'W', 't', 6)               # trophy wall
    z.art(47, 63, 'E', 'b', 2)
    z.art(47, 67, 'E', 'x', 1)
    z.art(50, 71, 'N', 'y', 6)
    z.art(62, 71, 'N', 'y', 6)
    z.block(49, 68, 2, 1, 'B'); z.block(67, 68, 2, 1, 'B')
    z.put(70, 66, 'v'); z.put(70, 67, 'v')
    z.put(48, 57, 'j'); z.put(70, 69, 'j'); z.put(63, 57, 'i')
    z.lightgrid(48, 57, 23, 14)

    # ---- the COURTYARD (rows 1-39): open sky
    z.outdoors(1, 1, 70, 39)
    z.block(42, 1, 4, 38, '3')               # covered walkway from the gym's east door to the north facade
    z.block(16, 14, 9, 9, '@')               # the big tree in its seat wall (landmark)
    # the lawn quad round the tree, paths left in paving
    z.fin(8, 6, 25, 25, ',')
    z.fin(19, 6, 3, 8, '.', over=',')        # path from the north door
    z.fin(19, 23, 3, 8, '.', over=',')       # path to the gym door
    z.fin(8, 17, 8, 3, '.', over=',')
    z.fin(25, 17, 8, 3, '.', over=',')
    z.f.rect(16, 14, 9, 9, '.')
    z.block(28, 2, 2, 2, '4')                # the flagpole by the north door
    # planters (cover): along the lawn's edges and the facades
    for (c, r) in ((9, 4), (25, 4), (3, 12), (3, 24), (34, 12), (34, 24), (12, 32), (24, 32)):
        z.block(c, r, 4, 2, 'r')
    # benches round the tree and along the paths
    for (c, r) in ((17, 12), (22, 12), (17, 24), (22, 24)):
        z.block(c, r, 2, 1, 'B')
    z.block(14, 16, 1, 2, 'B'); z.block(26, 16, 1, 2, 'B')
    # picnic tables in the west court
    for (c, r) in ((3, 4), (3, 18), (3, 30), (9, 36)):
        z.block(c, r, 2, 2, '1')
    # the outdoor classroom (concrete tiers facing south onto a teaching slab) in the east court
    z.block(52, 6, 10, 4, '6')
    for (c, r) in ((49, 15), (57, 15), (64, 15)):
        z.block(c, r, 2, 2, '1')
    # school garden beds
    for (c, r) in ((50, 24), (56, 24), (62, 24), (50, 30), (56, 30), (62, 30)):
        z.block(c, r, 4, 2, 'r')
    # bike racks along the east facade
    z.block(70, 4, 1, 4, '2'); z.block(70, 10, 1, 4, '2')
    # trees in grates along the walkway, lamp posts, bins
    for (c, r) in ((38, 8), (38, 20), (38, 32), (47, 20), (47, 36)):
        z.block(c, r, 2, 2, '8')
    for (c, r) in ((40, 14), (40, 26), (46, 8), (46, 30), (7, 2), (33, 2), (69, 37), (2, 38)):
        z.put(c, r, '5')
    for (c, r) in ((40, 4), (46, 26), (13, 2), (66, 2)):
        z.put(c, r, 'i')
    # facades: windows on both storeys, the school name over the exit, the gym's banner, downspouts
    for c0, n in ((2, 6), (10, 6), (38, 4), (47, 6), (55, 6), (63, 7)):
        z.art(c0, 0, 'S', 'W', n)
    z.art(19, 0, 'S', 'N', 13)               # CHALKSTONE ACADEMY lettering west of the gate frame
    z.art(8, 0, 'S', 'd', 1); z.art(16, 0, 'S', 'd', 1)
    z.art(43, 0, 'S', 'D', 2)                # the walkway's doors into the north wing (closed)
    z.art(53, 0, 'S', 'd', 1); z.art(61, 0, 'S', 'd', 1)
    for r0, n in ((2, 8), (12, 8), (22, 8), (32, 7)):
        z.art(0, r0, 'E', 'W', n)
    for r0, n in ((15, 8), (25, 6), (33, 6)):
        z.art(71, r0, 'W', 'W', n)
    z.art(71, 2, 'W', 'd', 1); z.art(71, 9, 'W', 'd', 1)
    z.art(0, 11, 'E', 'd', 1); z.art(0, 21, 'E', 'd', 1)
    z.art(12, 40, 'N', 'G', 8)               # GO COMETS banner on the gym
    for c0, n in ((1, 4), (21, 6), (29, 6), (59, 11)):
        z.art(c0, 40, 'N', 'W', n)
    z.art(20, 40, 'N', 'd', 1); z.art(35, 40, 'N', 'd', 1); z.art(58, 40, 'N', 'd', 1)

    # ---- spawns, pickups
    for (c, r) in ((12, 9), (29, 9), (8, 27), (29, 28), (20, 35), (55, 19), (66, 19), (58, 36), (30, 52), (21, 61),
                   (42, 52), (54, 47)):
        z.put(c, r, 'S')
    z.puts([(20, 3), (52, 62)], 'a')
    z.puts([(47, 16), (66, 44), (24, 47)], "h")
    z.ceiling()
    check_codes(z)
    return z


if __name__ == '__main__':
    out = []
    for z in (zone1(), zone2()):
        errs, stats = validate(z, WALK, PREFAB, size=((70, 76), (68, 74)))
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)

