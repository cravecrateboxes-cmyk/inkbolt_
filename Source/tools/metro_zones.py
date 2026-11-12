#!/usr/bin/env python3
"""INKBOLT Metro Central zones (theme 'metro'): hand-placed layouts -> src/data/zones/metro_*.txt

    python3 tools/metro_zones.py            # write + validate
    python3 tools/metro_zones.py --print    # ... and print the maps
    python3 tools/metro_zones.py --check    # validate only

Every zone file has the floor plan and these layers (symbols: see src/data/themes/metro.js):
  "@layer 0.006" floor finishes (the ticket hall's mosaic, tactile strips)
  "@layer 0.02"  data (theme.dataLayers): art codes for the south / east face of wall cells
  "@layer 0.03"  data: art codes for the north / west face of wall cells
  "@layer 0.04"  data: sunk cells ('t' the trackbeds, 0.9 m down; 'w' the escalator well, 4.5 m down) and, on the
                 cells round them, art codes for the sunk side faces (theme.sunk)
  "@layer 0.05"  data: the finish scheme of each open cell (the wall faces toward it take that scheme's tiles / paint)
  "@layer 2.9"   shop fascia signs over the shopfronts                                           [zone 1]
  "@layer 3.2"   hanging departure screens and signs
  "@layer 4"     ceiling tiles of the 4 m rooms (shops, offices, passages, the depot)
  "@layer 4.5"   the two footbridges over the tracks (deck, rails)                               [zone 2]
  "@layer 8"     the barrel vaults over the ticket hall / the platform hall and their end walls

Zone 1, the ticket hall (72 x 70): the street entrance in the south (player at (35, 66)); the unpaid hall under a
44 m barrel vault with the DEPARTURES BOARD (landmark), ticket machines, the ticket office (counter windows), four
walk-in shops (kiosk, cafe, newsagent, convenience store); the fare gate line (row 35); the paid concourse with the
ESCALATOR WELL (4.5 m deep: an escalator bank and two fixed stairs down to the lower landing), balconies round it; the
platform passage in the north with the exit gate (columns 34-36).
Zone 2, the platforms (72 x 66): the entry hall in the south (player at (35, 62)), the maintenance depot and the
cross passage; side platform A, track 1 (a stopped three-car train), the island platform with its columns and the
station clock (landmark), track 2 (a stopped two-car train), side platform B, all under a 32 m vault; two footbridges
over the tracks (4.5 m); platform-end steps down into each trackbed; the north passage with maintenance alcoves and
the exit gate (columns 34-36).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

# floor plan symbols you can stand on / walk through: doorways and headers, the tracks, the train (its floor), the
# stairs, escalators and track steps (climbed)
WALK = set('DOdn~exXN12FW')
PREFAB = {
    'D': (2, 1), 'd': (2, 1), 'O': (3, 1), 'x': (18, 3), 'V': (3, 1), 'I': (4, 2), 'Z': (10, 2), 'F': (2, 1), 'W': (2, 1), 'B': (3, 1),
    'Q': (3, 1), 'K': (2, 1), 'L': (2, 1), 'X': (10, 9), 'N': (5, 9), 'c': (3, 1), 'C': (4, 2), 't': (2, 2),
    'g': (3, 1), 'f': (2, 1), 'r': (2, 1), 'R': (3, 1), 'z': (2, 1), 'y': (2, 1), 'o': (2, 1), 'l': (2, 1),
    'T': (2, 2), 'p': (2, 1), 'e': (18, 3), '~': (2, 3), '1': (3, 2), '2': (3, 2), '<': (8, 2), '>': (8, 2),
    'J': (2, 2), 'w': (2, 1), 'm': (2, 1), '$': (2, 1), '%': (3, 1), '@': (6, 4),
}
DOORS = 'DOd'
CEIL_SKIP = set('#DOdGE')   # no ceiling tile over walls, doors and gates


class MZone(Zone):
    """floor plan + finishes (f) + art codes (A: S/E faces, B: N/W faces) + sunk cells / side art (K) + schemes (Sc)
    + signs (sg, 2.9) + hanging (hg, 3.2) + ceiling (c, 4) + deck (d, 4.5) + vault (rf, 8)"""

    def __init__(self, name, w, h, gc, ec, p):
        Zone.__init__(self, name, w, h)
        self.f, self.A, self.B, self.K, self.Sc = (Zone(name + s, w, h) for s in ('_f', '_A', '_B', '_K', '_S'))
        self.sg, self.hg, self.c, self.d, self.rf = (Zone(name + s, w, h) for s in ('_sg', '_hg', '_c', '_d', '_r'))
        self.tall = set()
        self.lights = set()
        self.reveal = []
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

    def clear(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '.')

    def door(self, c0, r0, w, h, ch='D'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '#', (self.name, 'door off the wall', c, r)
        self.rect(c0, r0, w, h, ch)

    def opening(self, c0, r0, w, h, scheme='p'):
        """an archway: open floor under a header ('n'); its reveals take the scheme given"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '#', (self.name, 'opening off the wall', c, r)
        self.rect(c0, r0, w, h, 'n')
        self.reveal.append((c0, r0, w, h, scheme))

    def art(self, c, r, side, code, n=1):
        """art code on the `side` face of wall cell (c, r); n cells along the wall"""
        dc, dr = (1, 0) if side in 'NS' else (0, 1)
        L = self.A if side in 'SE' else self.B
        o = {'S': (0, 1), 'N': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[side]
        for k in range(n):
            cc, rr = c + dc * k, r + dr * k
            assert self.g[rr][cc] == '#', (self.name, 'art on a non-wall cell', cc, rr, self.g[rr][cc], code)
            assert self.at(cc + o[0], rr + o[1]) not in '#' + DOORS, (self.name, 'art face not open', cc, rr, side, code)
            assert L.g[rr][cc] == '.', (self.name, 'art twice', cc, rr, side, L.g[rr][cc], code)
            L.g[rr][cc] = code

    def sink(self, c0, r0, w, h, code):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] != '#', (self.name, 'sunk wall', c, r)
                self.K.g[r][c] = code

    def edge(self, c0, r0, w, h, code):
        """art code for the sunk side face on the (higher) cells round a sunk area"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.K.g[r][c] == '.', (self.name, 'edge art on a sunk cell', c, r)
                self.K.g[r][c] = code

    def scheme(self, c0, r0, w, h, code):
        self.Sc.rect(c0, r0, w, h, code)

    def fin(self, c0, r0, w, h, ch, over='.'):
        self.f.pave(c0, r0, w, h, ch, over)

    def high(self, c0, r0, w, h):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.tall.add((c, r))

    def lightgrid(self, c0, r0, w, h, every=(3, 3), off=(1, 1)):
        for r in range(r0 + off[1], r0 + h, every[1]):
            for c in range(c0 + off[0], c0 + w, every[0]):
                self.lights.add((c, r))

    def ceiling(self):
        """tiles over every 4 m cell: [2, 2] groups where all four cells are free ('*' with a light panel where the
        room's light grid falls in it, '-' plain), single cells elsewhere ('+' lit, '=' plain)"""
        def free(c, r):
            return (0 < c < self.w - 1 and 0 < r < self.h - 1 and self.g[r][c] not in CEIL_SKIP and (c, r) not in self.tall
                    and self.c.g[r][c] == '.')
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
        for (c0, r0, w, h, sch) in self.reveal:
            self.Sc.rect(c0, r0, w, h, sch)
        out = Zone.text(self)
        for y, L in (('0.006', self.f), ('0.02', self.A), ('0.03', self.B), ('0.04', self.K), ('0.05', self.Sc),
                     ('2.9', self.sg), ('3.2', self.hg), ('4', self.c), ('4.5', self.d), ('8', self.rf)):
            if any(ch != '.' for row in L.g for ch in row):
                out += '@layer %s\n' % y + L.text()
        return out


def check_codes(z):
    for L in (z.A, z.B):
        for r in range(z.h):
            for c in range(z.w):
                if L.g[r][c] != '.':
                    assert z.g[r][c] == '#', (z.name, 'code off wall', c, r, L.g[r][c])


# =========================================================================================================== zone 1
def zone1():
    z = MZone('metro_1', 72, 70, 34, 34, (35, 66))
    W, H = 72, 70
    # ---- wall lines
    z.wall(0, 6, W, 1)            # the platform passage | the paid concourse
    z.wall(13, 6, 1, 63)          # hall | shops (west)
    z.wall(58, 6, 1, 63)          # hall | ticket office, toilets (east)
    z.wall(1, 1, 13, 5)           # staff block beside the platform passage (west)
    z.wall(58, 1, 13, 5)          # ... (east)
    z.wall(1, 7, 12, 30)          # staff rooms behind the west balcony (rows 7-36)
    z.wall(59, 7, 12, 30)         # ... east (rows 7-36)
    z.wall(1, 44, 12, 1)          # kiosk | cafe
    z.wall(1, 52, 12, 1)          # cafe | newsagent
    z.wall(1, 60, 12, 1)          # newsagent | convenience store
    z.wall(59, 52, 12, 17)        # toilets block (rows 52-68)
    z.opening(16, 6, 4, 1, 'h')   # the paid concourse opens onto the platform passage
    z.opening(33, 6, 6, 1, 'h')
    z.opening(52, 6, 4, 1, 'h')
    # ---- doors and shopfronts
    z.door(13, 39, 1, 3, 'O')     # kiosk: open front, shutter rolled up
    z.door(13, 47, 1, 2)          # cafe
    z.door(13, 55, 1, 2)          # newsagent
    z.door(13, 63, 1, 2)          # convenience store
    z.door(58, 49, 1, 2, 'd')     # ticket office staff door (leaves toward the hall)
    for r0, n in ((37, 2), (42, 2)):
        z.art(13, r0, 'E', 'w', n)            # kiosk side windows
    for r0, n in ((45, 2), (49, 3), (53, 2), (57, 3), (61, 2), (65, 4)):
        z.art(13, r0, 'E', 'w', n)            # shop windows
    z.art(58, 39, 'W', 'T', 9)                # ticket office counter windows (through the wall)
    # shop fascia signs (layer 2.9) on the shopfront line
    for r0, ch in ((37, '3'), (45, '4'), (53, '5'), (61, '6')):
        z.sg.rect(13, r0, 1, 7, ch)

    # ---- schemes
    z.scheme(14, 7, 44, 62, 'h')              # the hall (vaulted)
    z.scheme(14, 1, 44, 5, 'p')               # platform passage
    z.scheme(1, 37, 12, 7, 'k')
    z.scheme(1, 45, 12, 7, 'f')
    z.scheme(1, 53, 12, 7, 'n')
    z.scheme(1, 61, 12, 8, 'm')
    z.scheme(59, 37, 12, 15, 'o')

    # ---- the vault over the hall, its end walls (layer 8)
    for r in range(7, 69, 2):
        z.rf.rect(14, r, 44, 2, ')' if (r - 7) % 6 == 2 else '(')
    z.high(14, 7, 44, 62)
    z.rf.rect(14, 6, 44, 1, '{')              # north lunette (METRO CENTRAL)
    z.rf.rect(14, 69, 44, 1, '}')             # south lunette (clock, WAY OUT)
    z.high(33, 6, 6, 1)

    # ================================================= the escalator well (paid side)
    z.sink(26, 9, 20, 19, 'w')                # 4.5 m down: the lower landing (rows 9-18) and the flights (19-27)
    z.block(31, 19, 10, 9, 'X')               # escalator bank (4 escalators), top to the south
    z.block(26, 19, 5, 9, 'N')                # fixed stairs either side
    z.block(41, 19, 5, 9, 'N')
    z.run(25, 8, 20, '|', vertical=True)      # glass balustrade round the rim (west, north, east)
    z.run(26, 8, 20, '|')
    z.run(46, 8, 20, '|', vertical=True)
    z.edge(34, 8, 3, 1, 'U')                  # the lower landing's north wall: a closed shutter (Platforms 3 - 4)
    z.edge(28, 8, 3, 1, 'n'); z.edge(41, 8, 3, 1, 'n')   # station name panels
    z.edge(25, 11, 1, 2, 'a'); z.edge(25, 15, 1, 1, 'm'); z.edge(46, 11, 1, 2, 'a'); z.edge(46, 15, 1, 1, 'm')
    # the lower landing: benches against the side walls, bins, the departure screens
    z.block(28, 9, 3, 1, 'B'); z.block(41, 9, 3, 1, 'B')
    z.put(26, 10, 'b'); z.put(45, 10, 'b')
    z.put(32, 10, 'H')

    # ================================================= balconies, the rim walk, the gate line (paid side)
    for r0 in (9, 16, 23):
        z.block(14, r0, 1, 3, 'B')            # benches against the west and east walls
        z.block(57, r0, 1, 3, 'B')
    z.block(19, 12, 2, 1, 'K')                # coffee cart
    z.block(19, 19, 2, 1, 'L'); z.block(51, 19, 2, 1, 'L')   # advertising light boxes (double sided)
    z.block(19, 25, 2, 1, 'L'); z.block(51, 12, 2, 1, 'L')
    z.put(14, 14, 'k'); z.put(14, 15, 'k'); z.put(57, 14, 'k')   # vending machines
    z.put(22, 9, 'M'); z.put(49, 9, 'M'); z.put(49, 24, 'H')
    z.put(14, 20, 'b'); z.put(57, 20, 'b'); z.put(22, 27, 'j'); z.put(49, 27, 'j')
    z.put(15, 7, 'j'); z.put(56, 7, 'j')
    z.hg.put(20, 30, '7'); z.hg.put(51, 30, '7'); z.hg.put(35, 30, '9')   # screens and the PLATFORMS sign over the flights
    z.hg.put(20, 16, '8'); z.hg.put(51, 16, '8')
    # the fare gate line (row 35): glass screens at the ends, gates, the wide gates in the middle
    z.run(14, 35, 4, '|'); z.run(54, 35, 4, '|')
    for c in range(18, 34, 2):
        z.block(c, 35, 2, 1, 'F')
    z.block(34, 35, 2, 1, 'W'); z.block(36, 35, 2, 1, 'W')
    for c in range(38, 54, 2):
        z.block(c, 35, 2, 1, 'F')
    z.put(17, 33, 'H'); z.put(54, 33, 'H')
    z.put(16, 30, 'M'); z.put(55, 30, 'M')
    z.put(14, 33, 'b'); z.put(57, 33, 'b')

    # ================================================= the unpaid hall (rows 36-68)
    z.block(31, 46, 10, 2, 'Z')               # the DEPARTURES BOARD (landmark)
    z.fin(32, 52, 8, 8, '^')                  # the floor mosaic (the station roundel)
    z.block(20, 48, 4, 2, 'I'); z.block(48, 48, 4, 2, 'I')   # ticket machine islands
    for c0 in (17, 21, 25, 44, 48, 52):
        z.block(c0, 68, 3, 1, 'V')            # ticket machines along the south wall
    z.block(57, 55, 1, 3, 'V'); z.block(57, 59, 1, 3, 'V')   # ... and the east wall
    z.block(55, 40, 1, 3, 'Q'); z.block(55, 44, 1, 3, 'Q')   # queue barriers at the ticket windows
    z.block(22, 58, 3, 1, 'B'); z.block(47, 58, 3, 1, 'B')
    z.block(22, 41, 3, 1, 'B'); z.block(47, 41, 3, 1, 'B')
    z.block(57, 52, 1, 2, 'p')                # photo booth
    z.put(24, 37, 'H'); z.put(47, 37, 'H')
    z.put(16, 52, 'M'); z.put(55, 50, 'M')
    z.put(15, 44, 'b'); z.put(57, 58, 'b'); z.put(29, 66, 'b'); z.put(42, 66, 'b')
    z.put(14, 68, 'j'); z.put(57, 68, 'j'); z.put(14, 36, 'j'); z.put(57, 36, 'j')
    z.hg.put(26, 44, '7'); z.hg.put(45, 44, '7')
    # wall art: maps, ads, the clock, WAY OUT, fire points, help points
    z.art(13, 9, 'E', 'A', 3); z.art(13, 20, 'E', 'm', 2); z.art(13, 27, 'E', 'A', 3)
    z.art(58, 9, 'W', 'A', 3); z.art(58, 20, 'W', 'm', 2); z.art(58, 27, 'W', 'A', 3)
    z.art(13, 13, 'E', 'x', 1); z.art(58, 13, 'W', 'x', 1)
    z.art(13, 32, 'E', 'a', 1); z.art(58, 32, 'W', 'a', 1); z.art(13, 30, 'E', 'f', 1); z.art(58, 30, 'W', 'f', 1)
    z.art(58, 37, 'W', 'k', 1)
    z.art(16, 69, 'N', 'a', 1); z.art(28, 69, 'N', 'A', 3); z.art(41, 69, 'N', 'A', 3); z.art(55, 69, 'N', 'a', 1)
    z.art(31, 69, 'N', 'X', 2); z.art(39, 69, 'N', 'X', 2)   # WAY OUT beside the street entrance
    z.art(58, 63, 'W', 'g', 2); z.art(58, 66, 'W', 'G', 2); z.art(58, 62, 'W', 'f', 1)   # toilets doors, fire point
    z.art(13, 36, 'E', 'x', 1)
    # ---- the platform passage (rows 1-5) and the exit
    z.block(16, 1, 3, 1, 'B'); z.block(53, 1, 3, 1, 'B')
    z.put(22, 1, 'b'); z.put(49, 1, 'b'); z.put(29, 5, 'M')
    for c0 in (18, 24, 43, 50):
        z.art(c0, 0, 'S', 'a', 1)
    z.art(26, 0, 'S', 'm', 2); z.art(44, 0, 'S', 'm', 2)
    z.art(30, 0, 'S', 'P', 2); z.art(40, 0, 'S', 'P', 2)    # PLATFORMS 1 - 2 over the exit
    z.art(21, 6, 'N', 'A', 3); z.art(45, 6, 'N', 'A', 3)
    z.art(13, 2, 'E', 'x', 1); z.art(58, 2, 'W', 'S', 1)
    z.lightgrid(14, 1, 44, 5, (4, 2), (1, 1))

    # ================================================= shops (west)
    # kiosk (rows 37-43): counter along the north wall, shelves at the back, a cooler
    z.block(3, 37, 3, 1, 'c'); z.block(1, 39, 1, 2, 'y'); z.block(1, 41, 1, 2, 'y')
    z.block(6, 43, 2, 1, 'f'); z.block(9, 43, 2, 1, 'f')
    z.block(6, 40, 3, 1, 'R')
    z.art(0, 37, 'E', 'u', 2)
    z.lightgrid(1, 37, 12, 7)
    # cafe (rows 45-51): the counter and back bar, tables, the menu boards
    z.block(1, 46, 2, 4, 'C')
    z.block(6, 45, 2, 2, 't'); z.block(9, 45, 2, 2, 't'); z.block(6, 49, 2, 2, 't'); z.block(9, 49, 2, 2, 't')
    z.put(1, 51, 'j'); z.put(12, 45, 'j')
    z.art(0, 46, 'E', 'u', 4)
    z.lightgrid(1, 45, 12, 7)
    # newsagent (rows 53-59): magazine racks, the island rack, the counter by the door
    z.block(1, 53, 1, 2, 'r'); z.block(1, 56, 1, 2, 'r')
    z.block(3, 53, 2, 1, 'r'); z.block(6, 53, 2, 1, 'r')
    z.block(5, 56, 3, 1, 'R')
    z.block(9, 59, 3, 1, 'c')
    z.put(11, 53, 'j')
    z.lightgrid(1, 53, 12, 7)
    # convenience store (rows 61-68): coolers along the back, gondolas, the counter, the freezer
    z.block(1, 61, 1, 2, 'f'); z.block(1, 64, 1, 2, 'f'); z.block(1, 67, 1, 2, 'f')
    z.block(4, 63, 3, 1, 'g'); z.block(4, 66, 3, 1, 'g'); z.block(8, 66, 3, 1, 'g')
    z.block(9, 61, 3, 1, 'c')
    z.block(8, 63, 2, 1, 'z')
    z.lightgrid(1, 61, 12, 8)
    # ---- ticket office (cols 59-70, rows 37-51)
    for r0 in (39, 42, 45):
        z.block(59, r0, 1, 2, 'o')            # counter positions behind the windows
    z.block(70, 38, 1, 2, 'l'); z.block(70, 41, 1, 2, 'l')
    z.block(65, 44, 2, 2, 'T')
    z.block(70, 46, 1, 2, 'y'); z.put(70, 49, 's'); z.put(64, 37, 'j')
    z.art(71, 44, 'W', 'b', 1)
    z.lightgrid(59, 37, 12, 15)

    # ---- spawns, pickups
    for (c, r) in ((29, 12), (42, 12), (35, 14), (17, 9), (54, 9), (20, 22), (52, 22), (30, 3), (41, 3), (18, 43),
                   (53, 46), (35, 40)):
        z.put(c, r, 'S')
    z.puts([(23, 30), (6, 47)], 'a')
    z.puts([(48, 30), (64, 40), (36, 10)], 'h')
    z.ceiling()
    check_codes(z)
    return z


# =========================================================================================================== zone 2
def zone2():
    z = MZone('metro_2', 72, 66, 34, 34, (35, 62))
    W, H = 72, 66
    z.wall(1, 1, 70, 2)           # the alcove band north of the passage
    z.clear(30, 1, 12, 2)         # the exit approach
    for c0 in (4, 14, 52, 62):
        z.clear(c0, 1, 6, 2)      # maintenance alcoves
    z.wall(0, 8, W, 1)            # north passage | platform B
    z.wall(0, 41, W, 1)           # platform A | cross passage
    z.wall(0, 47, W, 1)           # cross passage | entry hall, depot
    z.wall(25, 48, 1, 17)         # depot | entry hall
    z.wall(46, 48, 1, 17)         # entry hall | plant rooms
    z.wall(47, 48, 24, 17)        # plant rooms (solid)
    for c0, n in ((9, 4), (33, 6), (59, 4)):
        z.opening(c0, 8, n, 1)
        z.opening(c0, 41, n, 1)
    z.opening(32, 47, 8, 1)
    z.door(12, 47, 2, 1)          # depot from the cross passage
    z.door(25, 55, 1, 2)          # depot from the entry hall

    # ---- schemes
    z.scheme(1, 3, 70, 5, 'p'); z.scheme(1, 1, 70, 2, 'p')
    z.scheme(1, 9, 70, 7, 'b')                # platform B (Harbour line, blue)
    z.scheme(1, 16, 70, 3, 'b')
    z.scheme(1, 19, 70, 12, 'i')              # island
    z.scheme(1, 31, 70, 10, 'r')              # track 1, platform A (Crimson line, red)
    z.scheme(1, 42, 70, 5, 'p')
    z.scheme(26, 48, 20, 17, 'e')
    z.scheme(1, 48, 24, 17, 'o')

    # ---- the platform hall: vault, end walls, tracks
    for c in range(1, 71, 2):
        z.rf.rect(c, 9, 2, 32, ';' if (c - 1) % 6 == 2 and not (13 <= c <= 19 or 51 <= c <= 57) else ':')
    z.rf.rect(0, 9, 1, 32, '!'); z.rf.rect(71, 9, 1, 32, '?')
    z.high(1, 9, 70, 32)
    z.high(9, 8, 4, 1); z.high(33, 8, 6, 1); z.high(59, 8, 4, 1)
    z.high(9, 41, 4, 1); z.high(33, 41, 6, 1); z.high(59, 41, 4, 1)
    z.sink(1, 16, 70, 3, 't')                 # track 2
    z.sink(1, 31, 70, 3, 't')                 # track 1
    # platform-end steps: a notch in the platform end, steps up from the trackbed
    z.sink(1, 14, 3, 2, 't'); z.block(1, 14, 3, 2, '2')    # platform B, west end (rising north)
    z.sink(1, 19, 3, 2, 't'); z.block(1, 19, 3, 2, '1')    # island, west end (rising south)
    z.sink(68, 19, 3, 2, 't'); z.block(68, 19, 3, 2, '1')  # island, east end
    z.sink(68, 29, 3, 2, 't'); z.block(68, 29, 3, 2, '2')  # island, east end (track 1)
    z.sink(1, 34, 3, 2, 't'); z.block(1, 34, 3, 2, '1')    # platform A, west end
    z.block(9, 31, 54, 3, 'e')                # the three-car train on track 1
    z.block(27, 16, 36, 3, 'x')               # the two-car train on track 2 (Harbour line blue)
    z.block(1, 31, 8, 3, '~'); z.block(63, 31, 8, 3, '~')
    z.block(1, 16, 26, 3, '~'); z.block(63, 16, 8, 3, '~')
    for r0 in (16, 31):
        z.art(0, r0, 'E', 'U', 3)             # tunnel mouths at both ends
        z.art(71, r0, 'W', 'U', 3)

    # ---- the footbridges (layer 4.5) and their stairs
    for c0, sym, s0 in ((15, '<', 19), (53, '>', 45)):
        z.d.rect(c0, 9, 4, 32, 'u')
        for r in range(9, 41):
            for cc in (c0, c0 + 3):
                z.d.g[r][cc] = ']'
        for r0 in (9, 24, 39):
            z.block(s0, r0, 8, 2, sym)
            gap = c0 + 3 if sym == '<' else c0
            for r in (r0, r0 + 1):
                z.d.g[r][gap] = 'u'
    # ---- platform B (rows 9-15)
    for c0 in (4, 29, 40, 62):
        z.block(c0, 9, 3, 1, 'B')
    z.put(13, 9, 'b'); z.put(58, 9, 'b'); z.put(32, 9, 'H'); z.put(39, 9, 'k'); z.put(28, 13, 'b')
    for c0, code in ((2, 'a'), (4, 'n'), (13, 'a'), (27, 'n'), (30, 'a'), (31, 'P'), (39, 'm'), (41, 'n'), (54, 'A'), (57, 'a'), (63, 'n'), (67, 'a'), (69, 'a')):
        n = {'n': 3, 'A': 3, 'm': 2, 'P': 1}.get(code, 1)
        z.art(c0, 8, 'S', code, n)
    z.art(0, 10, 'E', 'Y', 1); z.art(71, 10, 'W', 'Y', 1)
    for c in (8, 30, 43, 61):
        z.hg.put(c, 12, '8')
    # ---- the island (rows 19-30): columns, benches, the station clock
    for c in (6, 11, 30, 41, 60, 65):
        z.put(c, 22, 'Y'); z.put(c, 27, 'Y')
    z.block(33, 23, 6, 4, '@')                # the station clock (landmark)
    for c0, r0 in ((7, 24), (28, 24), (41, 25), (61, 24)):
        z.block(c0, r0, 3, 1, 'B')
    z.put(4, 24, 'b'); z.put(66, 25, 'b'); z.put(30, 25, 'H'); z.put(41, 24, 'k')
    z.block(13, 22, 2, 2, 'J')                # platform staff booth
    for c in (8, 24, 47, 63):
        z.hg.put(c, 21, '8'); z.hg.put(c, 28, '8')
    z.art(0, 22, 'E', 'Y', 1); z.art(71, 22, 'W', 'Y', 1)
    z.art(0, 26, 'E', 'x', 1); z.art(71, 26, 'W', 'x', 1)
    # ---- platform A (rows 34-40)
    for c0 in (6, 29, 40, 63):
        z.block(c0, 40, 3, 1, 'B')
    z.put(13, 40, 'b'); z.put(58, 40, 'b'); z.put(39, 40, 'H'); z.put(32, 40, 'k'); z.put(44, 36, 'b')
    z.block(27, 37, 2, 2, 'J')
    for c0, code in ((2, 'a'), (4, 'n'), (13, 'a'), (27, 'n'), (31, 'P'), (39, 'm'), (41, 'n'), (54, 'A'), (57, 'a'), (63, 'n'), (67, 'a'), (69, 'a')):
        n = {'n': 3, 'A': 3, 'm': 2, 'P': 1}.get(code, 1)
        z.art(c0, 41, 'N', code, n)
    z.art(0, 38, 'E', 'Y', 1); z.art(71, 38, 'W', 'Y', 1)
    for c in (8, 30, 43, 61):
        z.hg.put(c, 37, '8')

    # ---- the north passage (rows 3-7) and the alcoves (rows 1-2)
    for c0 in (24, 45):
        z.block(c0, 7, 3, 1, 'B')
    z.put(14, 7, 'M'); z.put(57, 7, 'M'); z.put(29, 3, 'b'); z.put(42, 3, 'b'); z.put(2, 5, 'k')
    z.block(4, 1, 2, 1, 'w'); z.put(7, 1, 'q'); z.put(7, 2, 'q'); z.put(9, 1, 'i')
    z.block(14, 1, 2, 1, '$'); z.block(17, 1, 2, 1, 'w'); z.put(18, 2, 'i')
    z.block(52, 1, 2, 1, 'm'); z.put(55, 1, 'q'); z.block(56, 1, 2, 1, 'w')
    z.block(62, 1, 2, 1, '$'); z.put(65, 1, 'q'); z.block(66, 1, 2, 1, 'w'); z.put(66, 2, 'i')
    z.art(0, 4, 'E', 'x', 1); z.art(71, 4, 'W', 'S', 1)
    for c0, code in ((22, 'a'), (25, 'A'), (47, 'A'), (51, 'a')):
        z.art(c0, 8, 'N', code, 3 if code == 'A' else 1)
    z.art(30, 0, 'S', 'X', 2); z.art(40, 0, 'S', 'X', 2)
    z.lightgrid(1, 1, 70, 7, (4, 3), (2, 1))
    # ---- the cross passage (rows 42-46)
    for c0 in (20, 49):
        z.block(c0, 46, 3, 1, 'B')
    z.put(6, 42, 'k'); z.put(7, 42, 'k'); z.put(65, 46, 'M'); z.put(28, 46, 'b'); z.put(44, 46, 'b')
    for c0, code in ((3, 'a'), (16, 'A'), (24, 'a'), (43, 'a'), (51, 'A'), (66, 'a')):
        z.art(c0, 47, 'N', code, 3 if code == 'A' else 1)
    z.art(18, 41, 'S', 'm', 2); z.art(52, 41, 'S', 'm', 2)
    z.art(0, 44, 'E', 'S', 1); z.art(71, 44, 'W', 'S', 1)
    z.lightgrid(1, 42, 70, 5, (4, 3), (2, 1))
    # ---- the entry hall (cols 26-45, rows 48-64)
    z.block(28, 49, 3, 1, 'B'); z.block(41, 49, 3, 1, 'B')
    z.put(27, 52, 'H'); z.put(44, 52, 'M'); z.put(27, 63, 'j'); z.put(44, 63, 'j'); z.put(44, 57, 'k'); z.put(27, 59, 'b')
    z.art(46, 52, 'W', 'L', 2)                # lift doors
    z.art(25, 50, 'E', 'A', 3); z.art(46, 58, 'W', 'A', 3)
    z.art(29, 65, 'N', 'X', 2); z.art(41, 65, 'N', 'X', 2)
    z.lightgrid(26, 48, 20, 17)
    # ---- the maintenance depot (cols 1-24, rows 48-64)
    z.block(1, 50, 1, 3, '%'); z.block(1, 55, 1, 3, '%')
    z.block(1, 60, 1, 2, '$'); z.block(3, 64, 2, 1, 'w'); z.block(7, 64, 2, 1, 'w')
    z.block(24, 59, 1, 2, 'y'); z.block(24, 62, 1, 2, 'y'); z.block(11, 64, 2, 1, 'l'); z.block(15, 64, 2, 1, 'l')
    z.block(9, 52, 2, 1, 'm'); z.block(16, 52, 2, 1, 'm')
    z.put(8, 57, 'q'); z.put(9, 58, 'q'); z.put(19, 57, 'q'); z.put(21, 49, 'i'); z.put(22, 49, 'i')
    z.block(12, 58, 2, 2, 'T')
    z.art(0, 49, 'E', 'b', 1); z.art(25, 50, 'W', 'S', 1)
    z.lightgrid(1, 48, 24, 17)

    # ---- spawns, pickups
    for (c, r) in ((9, 12), (24, 12), (55, 13), (4, 27), (22, 27), (50, 27), (63, 28), (18, 37), (50, 37), (10, 4),
                   (60, 4), (8, 44), (63, 44), (14, 55)):
        z.put(c, r, 'S')
    z.puts([(35, 13), (12, 60)], 'a')
    z.puts([(36, 37), (2, 44), (35, 4)], 'h')
    z.ceiling()
    check_codes(z)
    return z


if __name__ == '__main__':
    out = []
    for z in (zone1(), zone2()):
        errs, stats = validate(z, WALK, PREFAB, size=((70, 76), (64, 74)))
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)
