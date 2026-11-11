#!/usr/bin/env python3
"""INKBOLT BULKBARN Warehouse Club zones (theme 'megastore'): hand-placed layouts -> src/data/zones/megastore_*.txt

    python3 tools/megastore_zones.py            # write + validate
    python3 tools/megastore_zones.py --print    # ... and print the maps
    python3 tools/megastore_zones.py --check    # validate only

Every zone file has the floor plan and four layers: "@layer 0.01" (floor marks, plus wall-art codes on the wall cells,
read by the theme's wall chooser; cell (0, 0) holds ',' in the stockroom), "@layer 3.5" (the mezzanine deck),
"@layer 10" (roof bays [4, 4]) and a second "@layer 10" (hanging signs). Symbols: see src/data/themes/megastore.js.

Zone 1, the Sales Floor, is 80 x 66 m (gates at columns 39-41, the player starts in the entrance vestibule at
(40, 63)); zone 2, the Stockroom, is 72 x 60 m (gates at columns 35-37, entry at (36, 57)).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

WALK = set('DJ')     # the vestibule's automatic doors and the break-room door are open doorways
PREFAB = {'R': (3, 2), 'T': (3, 2), 'n': (2, 1), 's': (2, 1), 'F': (4, 2), 'V': (2, 2), 'K': (3, 2), 'A': (2, 2), 'Q': (2, 2),
          'H': (8, 3), 'L': (3, 5), 'C': (4, 1), 'D': (4, 1), 'Z': (10, 4), 't': (2, 2), 'X': (2, 3), 'x': (2, 2), 'w': (2, 1),
          'B': (2, 2), 'W': (2, 2), 'M': (2, 2), 'U': (2, 1), 'Y': (3, 1), 'J': (3, 1), 'N': (2, 7)}


class MZone(Zone):
    """floor plan + floor layer (f) + deck layer (d) + roof bays (k) + hanging signs (s)"""

    def __init__(self, name, w, h, gc):
        Zone.__init__(self, name, w, h)
        self.f = Zone(name + '_f', w, h)
        self.d = Zone(name + '_d', w, h)
        self.k = Zone(name + '_k', w, h)
        self.s = Zone(name + '_s', w, h)
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
            self.f.g[r][c] = ch

    def mark(self, c0, r0, w, h, ch):
        """floor marks over open floor cells only"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) == '.' and self.f.g[r][c] == '.':
                    self.f.g[r][c] = ch

    def rack(self, c0, r0, n, ch):
        """a rack row of n bays (3 m each) running north-south from row r0, 2 cells wide"""
        self.block(c0, r0, 2, 3 * n, ch)

    def roof(self, sky=True):
        """[4, 4] roof bays over rows 1 .. h-2: girder bays every 24 m, a high-bay lamp in one bay of four (staggered),
        skylights"""
        nj = (self.h - 2) // 4
        for i in range(self.w // 4):
            for j in range(nj):
                g = i % 6 == 3
                lamp = (i + 2 * j) % 4 == 0
                if g:
                    ch = '|' if lamp else ';'
                elif sky and i % 6 == 0 and j % 3 == 1:
                    ch = ':'
                else:
                    ch = '~' if lamp else '='
                self.k.rect(i * 4, 1 + j * 4, 4, 4, ch)

    def sign(self, c, r, ch):
        self.s.put(c, r, ch)

    def text(self):
        return (Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer 3.5\n' + self.d.text() +
                '@layer 10\n' + self.k.text() + '@layer 10\n' + self.s.text())


def check(z, size):
    errs, stats = validate(z, WALK, PREFAB, size=size)
    # door blocks sit in a wall line: their two ends against wall / glass / partition cells
    for ch in 'DJ':
        for (c, r, w, h) in rects(z.g, ch):
            ends = [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)] if w > h else \
                [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)]
            for (a, b) in ends:
                if z.at(a, b) not in '#qi':
                    errs.append('door %r at (%d,%d) end (%d,%d) is %r' % (ch, c, r, a, b, z.at(a, b)))
    # dock doors: a 3-cell bay on the east wall, nothing standing on the leveler plates in front
    for r in range(z.h):
        if z.f.g[r][z.w - 1] in '][':
            assert z.f.g[r - 1][z.w - 1] == '_' and z.f.g[r + 1][z.w - 1] == '_', (z.name, 'dock sides', r)
            for rr in (r - 1, r, r + 1):
                for cc in (z.w - 4, z.w - 3, z.w - 2):
                    if z.at(cc, rr) not in '.':
                        errs.append('dock (%d) apron cell (%d,%d) holds %r' % (r, cc, rr, z.at(cc, rr)))
    return errs, stats


# ================================================================ zone 1: the Sales Floor
def zone1():
    W, H, GC = 80, 66, 39
    z = MZone('megastore_1', W, H, GC)
    RC = [13, 20, 27, 34, 41, 48, 55, 62]          # rack rows (2 wide), aisles of 5 m between them
    for c in RC:
        z.rack(c, 7, 5, 'R')
        z.rack(c, 27, 5, 'R')
        z.block(c, 6, 2, 1, 'n')
        z.block(c, 22, 2, 1, 's')
        z.block(c, 42, 2, 1, 's')
    AISLES = [c + 4 for c in RC[:-1]]              # aisle centre columns 17, 24, ... 59
    for k, c in enumerate(AISLES):          # one board per aisle, over the cross aisle (seen from both blocks)
        z.sign(c, 23, str(k + 1))
    # cross aisle: columns in the aisle centres, a couple of pallet drops
    for c in (17, 31, 45, 59):
        z.put(c, 24, 'O')
    z.put(24, 24, 'l')
    z.put(52, 24, 'p')
    for c in (20, 41, 62):
        z.put(c, 26, 'p')
    z.put(35, 26, 'l')
    # ---- back aisle and the back wall: dairy, walk-ins, drinks
    z.art([(c, 0) for c in range(2, 15)], 'd')
    z.art([(16, 0), (34, 0), (60, 0)], '<')
    z.art([(c, 0) for c in range(20, 33)] + [(c, 0) for c in range(47, 58)], 'e')
    z.art([(36, 0), (77, 0)], 'f')
    z.art([(44, 0)], '{')
    z.art([(c, 0) for c in range(66, 74)], '*')          # the BULKBARN logo high on the back wall
    for c in (17, 31, 45, 59):
        z.put(c, 3, 'O')
    for (c, r) in ((6, 5), (33, 2), (48, 4), (69, 2)):
        z.put(c, r, 'c')
    z.put(28, 4, 'p')
    z.put(57, 2, 'l')
    # ---- north-west: produce (stands, walk-in coolers on the west wall)
    for r in (7, 11, 15, 19):
        for c in (3, 7):
            z.block(c, r, 2, 2, 'V')
    z.art([(0, 7), (0, 15)], '<')
    z.art([(0, 11)], '(')
    z.art([(0, 19)], ')')
    z.put(10, 9, 'l')
    z.put(5, 23, 'c')
    z.sign(6, 14, '!')
    # ---- west wall: pharmacy / optical counter, a fire point, the front-end fire exit and riser
    z.block(1, 28, 3, 8, 'H')
    z.put(7, 30, 'c')
    z.put(8, 34, 'l')
    z.art([(0, 25), (0, 40)], 'f')
    z.art([(0, 47)], '{')
    z.art([(0, 52)], '>')
    # ---- east: electronics (TV wall, demo tables), apparel (tables, round rails)
    z.art([(W - 1, r) for r in range(3, 22)], '8')
    for r in range(3, 22, 3):
        z.f.g[r][W - 1] = '9'
    for (c, r) in ((67, 5), (72, 5), (67, 10), (72, 10), (67, 15), (72, 15)):
        z.block(c, r, 3, 2, 'K')
    z.put(76, 8, 'p')
    z.put(76, 18, 'p')
    z.put(65, 20, 'l')
    z.sign(70, 12, '@')
    for (c, r, ch) in ((66, 26, 'A'), (70, 26, 'Q'), (74, 26, 'A'), (66, 30, 'Q'), (70, 30, 'A'), (74, 30, 'Q'),
                       (66, 34, 'A'), (70, 34, 'Q'), (74, 34, 'A'), (66, 38, 'Q'), (70, 38, 'A')):
        z.block(c, r, 2, 2, ch)
    z.sign(71, 33, '$')
    z.art([(W - 1, 25), (W - 1, 44)], 'f')
    z.art([(W - 1, 30)], '(')
    z.art([(W - 1, 36)], ')')
    z.art([(W - 1, 41)], '>')
    # ---- front aisle: freezer bunkers, pallet drops, columns
    for c in (15, 29, 50):
        z.block(c, 45, 4, 2, 'F')
    z.sign(31, 46, '%')
    for (c, r) in ((23, 44), (24, 47), (37, 45), (44, 47), (45, 44), (58, 45), (63, 47), (9, 45)):
        z.put(c, r, 'p')
    for (c, r) in ((22, 45), (43, 45), (64, 44)):
        z.put(c, r, 'l')
    for c in (10, 70):
        z.put(c, 47, 'O')
    # ---- the front end: checkout lanes (exit south), the lobby, the vestibule, the food court
    z.block(2, 50, 30, 5, 'L')
    z.block(48, 50, 9, 5, 'L')
    for (c, r) in ((34, 51), (45, 52)):
        z.put(c, r, 'c')
    z.block(3, 57, 4, 1, 'C')
    z.block(12, 57, 4, 1, 'C')
    z.block(24, 57, 4, 1, 'C')
    for (c, r) in ((9, 56), (19, 57), (30, 56), (50, 57)):
        z.put(c, r, 'c')
    z.put(53, 56, 'l')
    # vestibule: glass on three sides, the automatic doors in the north line, a cart line and the greeter podium
    for c in range(34, 47):
        if not 38 <= c <= 41:
            z.put(c, 58, 'q')
    for r in range(59, H - 1):
        z.put(34, r, 'q')
        z.put(46, r, 'q')
    z.block(38, 58, 4, 1, 'D')
    z.block(35, 60, 1, 4, 'C')
    z.put(44, 61, 'g')
    z.put(44, 63, 'c')
    z.f.rect(39, 61, 3, 2, '+')
    # food court: the counter on the south wall, tables in front, a pallet of soda beside it
    z.block(66, 61, 10, 4, 'Z')
    for (c, r) in ((61, 54), (65, 54), (69, 54), (73, 54), (63, 57), (67, 57), (71, 57), (75, 57), (61, 60)):
        z.block(c, r, 2, 2, 't')
    z.art([(W - 1, 55)], 'f')
    z.art([(c, H - 1) for c in (10, 26)], '(')
    z.art([(c, H - 1) for c in range(47, 55)], '*')      # ... and on the front wall over the lobby
    z.art([(c, H - 1) for c in (18, 60)], 'f')
    # floor marks: a keep-clear hatch in front of the fire exits, the walkway into the vestibule
    z.mark(1, 51, 1, 3, '/')
    z.mark(W - 2, 40, 1, 3, '/')
    # ---- spawns and pickups
    for (c, r) in ((10, 3), (25, 3), (53, 3), (72, 3), (17, 14), (45, 14), (31, 34), (59, 34), (38, 24), (66, 23), (11, 41), (66, 44)):
        z.put(c, r, 'S')
    for (c, r) in ((24, 31), (52, 18), (5, 38)):
        z.put(c, r, 'a')
    for (c, r) in ((38, 12), (73, 42), (21, 24)):
        z.put(c, r, 'h')
    z.roof()
    return z


# ================================================================ zone 2: the Stockroom
def zone2():
    W, H, GC = 72, 60, 35
    z = MZone('megastore_2', W, H, GC)
    z.f.g[0][0] = ','          # stockroom wall finish
    # ---- mezzanine over the north-west corner: the receiving office on the deck, the break room under it
    z.d.rect(1, 1, 20, 13, 'u')
    z.d.rect(3, 1, 8, 5, 'o')
    for c in range(1, 21):
        if c not in (15, 16):
            z.d.g[13][c] = 'r'
    for r in range(1, 13):
        z.d.g[r][20] = 'r'
    z.block(15, 14, 2, 7, 'N')
    for (c, r) in ((6, 13), (13, 13), (20, 13), (20, 6), (16, 6)):
        z.put(c, r, 'I')
    # break room: partitions with a door, kitchenette, vending, lockers, tables
    for c in range(1, 13):
        if not 4 <= c <= 6:
            z.put(c, 12, 'i')
    for r in range(1, 12):
        z.put(12, r, 'i')
    z.block(4, 12, 3, 1, 'J')
    z.block(2, 1, 3, 1, 'Y')
    z.put(6, 1, 'v')
    z.put(7, 1, 'v')
    z.block(9, 1, 2, 1, 'U')
    for (c, r) in ((3, 5), (8, 5), (3, 8), (8, 8)):
        z.block(c, r, 2, 2, 'M')
    z.art([(0, 6)], '?')
    z.art([(0, 9)], 'f')
    # under the rest of the deck: returns waiting on pallets
    for (c, r) in ((14, 2), (17, 2), (14, 9), (18, 10)):
        z.put(c, r, 'm' if c < 16 else 'p')
    z.block(16, 4, 2, 2, 'x')
    # ---- baler corner (north wall, east of the deck)
    z.block(22, 1, 2, 2, 'B')
    for (c, r) in ((24, 1), (25, 1), (26, 1), (24, 2), (27, 1), (29, 1), (25, 4)):
        z.put(c, r, 'b')
    for (c, r) in ((22, 5), (23, 6)):
        z.put(c, r, 'y')
    z.art([(28, 0)], '`')
    # ---- tall racks: three rows west of the main aisle, two east of it
    for c in (5, 13, 21):
        z.rack(c, 22, 5, 'T')
        z.rack(c, 42, 4, 'T')
    for c in (44, 51):
        z.rack(c, 6, 5, 'T')
        z.rack(c, 26, 5, 'T')
        z.rack(c, 45, 3, 'T')
    # row ends and aisles: pallet stacks, a jack, gaylords, drums
    for (c, r) in ((9, 39), (17, 38), (2, 30), (26, 46), (48, 22), (55, 43)):
        z.put(c, r, 'm')
    for (c, r) in ((10, 20), (18, 41), (47, 3), (54, 24), (8, 55), (27, 20)):
        z.put(c, r, 'j')
    for (c, r) in ((3, 40), (26, 36), (49, 43)):
        z.put(c, r, 'y')
    for (c, r) in ((1, 56), (1, 54), (28, 56)):
        z.put(c, r, 'k')
    z.block(29, 39, 2, 2, 'x')
    z.block(2, 49, 2, 2, 'x')
    z.sign(36, 30, '&')
    # ---- the main aisle: forklifts, a column line, pallets waiting to go out
    for (c, r) in ((33, 18), (39, 40)):
        z.put(c, r, 'O')
    for (c, r) in ((33, 40), (39, 18)):
        z.put(c, r, 'O')
    z.block(31, 24, 2, 3, 'X')
    z.block(40, 33, 2, 3, 'X')
    for (c, r) in ((31, 8), (32, 8), (40, 11), (31, 47), (41, 49), (40, 50)):
        z.put(c, r, 'p')
    for (c, r) in ((34, 31), (37, 12)):
        z.put(c, r, 'l')
    # ---- receiving: seven dock doors on the east wall (open ones with a trailer), staging lanes in front
    for k, r in enumerate((6, 12, 18, 24, 30, 36, 42, 48)):
        z.f.g[r - 1][W - 1] = '_'
        z.f.g[r + 1][W - 1] = '_'
        z.f.g[r][W - 1] = ']' if k % 2 == 0 else '['
    z.art([(W - 1, 53)], 'f')
    z.art([(W - 1, 2)], '`')
    for (c, r) in ((60, 5), (61, 5), (64, 7), (59, 11), (60, 13), (63, 17), (64, 18), (59, 23), (62, 25), (60, 31),
                   (64, 31), (61, 37), (59, 41), (63, 43), (60, 47), (61, 49), (64, 50)):
        z.put(c, r, 'p')
    for (c, r) in ((65, 12), (66, 24), (65, 36), (66, 47)):
        z.put(c, r, 'j')
    z.block(62, 20, 2, 3, 'X')
    z.block(60, 34, 2, 3, 'X')
    z.block(58, 53, 2, 2, 'W')
    z.block(64, 54, 2, 1, 'w')
    z.block(51, 56, 2, 1, 'w')
    z.sign(62, 28, '^')
    # ---- south: the walkway from the sales-floor doors, fire points and panels
    z.mark(30, 50, 1, 8, '-')
    z.mark(42, 50, 1, 8, '-')
    z.art([(0, 33), (0, 47), (14, 59), (58, 59)], 'f')
    z.art([(0, 20), (24, 59)], '`')
    # ---- spawns and pickups
    for (c, r) in ((9, 30), (17, 45), (2, 46), (28, 30), (36, 6), (48, 14), (55, 20), (48, 35), (66, 40), (66, 9), (27, 9), (55, 52)):
        z.put(c, r, 'S')
    for (c, r) in ((10, 50), (59, 28), (36, 22)):
        z.put(c, r, 'a')
    for (c, r) in ((18, 33), (47, 52), (9, 3)):
        z.put(c, r, 'h')
    # staging lane lines between the dock bays (painted after the props: marks only go on open floor)
    for r in (9, 15, 21, 27, 33, 39, 45):
        z.mark(57, r, 11, 1, '-')
    z.mark(56, 3, 1, 52, '-')
    z.roof(sky=True)
    return z


def main():
    zones = []
    for fn, size in ((zone1, ((80, 80), (66, 66))), (zone2, ((72, 72), (60, 60)))):
        z = fn()
        errs, stats = check(z, size)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
