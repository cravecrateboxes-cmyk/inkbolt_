#!/usr/bin/env python3
"""INKBOLT Abyssal Station Thalassa zones (theme 'seabase'): hand-placed layouts -> src/data/zones/seabase_*.txt

    python3 tools/seabase_zones.py            # write + validate
    python3 tools/seabase_zones.py --print    # ... and print the maps
    python3 tools/seabase_zones.py --check    # validate only

Every zone file has the floor plan and these layers (symbols: see src/data/themes/seabase.js):
  "@layer 0.01"  floor marks (hazard stripes, stencils, drains)
  "@layer 0.22"  codes read by the theme, never symbols: '~' flood water (shin deep), '&' the moon pool's water, wall
                 art on wall cells (o porthole, 1 leaking pipe, 2 emergency light, 3 / 4 warning stencils, 5 valve
                 panel, 6 / 7 deck signs, 8 fire point, 9 screen, 0 logo); cell (0, 0) holds '%' in the research ring
  "@layer 3.2"   the dock gallery / hub mezzanine deck (u), guard rails (r), the dock control cabin (J)
  "@layer 4.5" / "@layer 6" / "@layer 7" / "@layer 7.5"   ceiling tiles of the rooms with that ceiling height
                 (one tile a cell; the hub's glass dome on its own 7 m layer)

Zone 1, Docking & Service Level, 72 x 64 m: the arrival lock in the south (player at (35, 61)), dive lockers, the
pump room, the moon pool dock with its gallery deck, the flooded main passage and ballast passage, the ballast tank
room, the cargo hold, the battery room and the exit lock (gate at columns 34-36).
Zone 2, the Research Ring, 71 x 64 m: the observation hub under its glass dome (mezzanine on three sides, two
stairs) inside a ring corridor, the west and east glass observation chambers bulging into the seabed (notches open to
the sea), glass-fronted labs at the ring ends, the core store, comms, the flooded wet lab, the instrument bay.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

WALK = set('Df')       # bulkhead doors (a walkable coaming) and the glass lab doors are open doorways
PREFAB = {'M': (12, 10), 'W': (2, 2), 'L': (2, 1), 'T': (2, 1), 'U': (2, 2), 'V': (2, 2), 'C': (2, 2), 'K': (2, 2),
          'p': (3, 2), 'm': (4, 1), 't': (2, 2), 'H': (6, 3), 'x': (2, 2), 'e': (2, 1), 'B': (2, 1), 'D': (3, 2),
          'd': (5, 3), 'N': (2, 7), 'j': (3, 2), 'y': (2, 1), 'A': (12, 25), 'Z': (12, 25), 'Y': (9, 9),
          'f': (3, 1), 'R': (2, 2), 'Q': (4, 1), 'l': (2, 1), 'n': (2, 1), 'v': (3, 2), 'z': (2, 1), 'X': (2, 1)}
CEIL = {4.5: None, 6.0: None, 7.0: None, 7.5: None}
NO_CEIL = set('#DGEAZ')   # floor plan cells no ceiling tile hangs over (walls, doors, gates, the observation chambers)


class SZone(Zone):
    """floor plan + floor marks (f) + codes (w) + deck (d) + ceiling layers (c[y])"""

    def __init__(self, name, w, h, gc, ceils):
        Zone.__init__(self, name, w, h)
        self.f = Zone(name + '_f', w, h)
        self.k = Zone(name + '_k', w, h)
        self.d = Zone(name + '_d', w, h)
        self.c = {y: Zone(name + '_c%g' % y, w, h) for y in ceils}
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gc, 0, 3, 1, 'G')
        self.rect(gc, h - 1, 3, 1, 'E')
        self.put(gc + 1, h - 3, 'P')

    def wall(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '#')

    def door(self, c0, r0, w, h):
        """a bulkhead door [3, 2] in a 2-cell wall (the cells must be wall)"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '#', (self.name, 'door off the wall', c, r)
        self.rect(c0, r0, w, h, 'D')

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell', self.at(c, r))
            assert self.k.g[r][c] == '.', (self.name, c, r, 'art twice')
            self.k.g[r][c] = ch

    def water(self, c0, r0, w, h, ch='~'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) not in '#DGE':
                    self.k.g[r][c] = ch

    def mark(self, c0, r0, w, h, ch):
        """floor marks over open floor cells only"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) in '.P' and self.f.g[r][c] == '.':
                    self.f.g[r][c] = ch

    def ceil(self, y, c0, r0, w, h, plain, lamp, pipe=None, every=4, run=None):
        """ceiling tiles over the open cells of a room: lamps on a 4 m grid, an optional pipe run along a corridor
        (run=('r', row) or ('c', col))"""
        L = self.c[y]
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) in NO_CEIL or L.g[r][c] != '.':
                    continue
                ch = plain
                if pipe and run and ((run[0] == 'r' and r == run[1]) or (run[0] == 'c' and c == run[1])):
                    ch = pipe
                elif (c - c0) % every == every // 2 and (r - r0) % every == every // 2:
                    ch = lamp
                L.g[r][c] = ch

    def text(self):
        out = Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer 0.22\n' + self.k.text() + '@layer 3.2\n' + self.d.text()
        for y in sorted(self.c):
            out += '@layer %g\n' % y + self.c[y].text()
        return out


def check(z, size):
    errs, stats = validate(z, WALK, PREFAB, size=size)
    # door blocks sit in a wall line: their two ends against wall / glass cells
    for ch in 'Df':
        for (c, r, w, h) in rects(z.g, ch):
            ends = [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)] if w > h else \
                [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)]
            for (a, b) in ends:
                if z.at(a, b) not in '#q':
                    errs.append('door %r at (%d,%d) end (%d,%d) is %r' % (ch, c, r, a, b, z.at(a, b)))
            faces = [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)] if w > h else \
                [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)]
            for (a, b) in faces:
                if z.at(a, b) not in '.SahPAZ':
                    errs.append('door %r at (%d,%d) blocked at (%d,%d) by %r' % (ch, c, r, a, b, z.at(a, b)))
    # nothing flooded under a wall, no tall ceiling over a lower one in the same cell
    for r in range(z.h):
        for c in range(z.w):
            if z.k.g[r][c] in '~&' and z.at(c, r) in '#DGE':
                errs.append('water on a wall at (%d,%d)' % (c, r))
            n = sum(1 for y in z.c if z.c[y].g[r][c] != '.')
            if n > 1:
                errs.append('two ceilings over (%d,%d)' % (c, r))
            if z.k.g[r][c] in '~' and z.at(c, r) in 'ah':
                errs.append('pickup in the water at (%d,%d)' % (c, r))
    return errs, stats


def runs(z, pts, ch, n, vertical):
    for (c, r) in pts:
        z.run(c, r, n, ch, vertical=vertical)


# ================================================================ zone 1: Docking & Service Level
def zone1():
    W, H, GC = 72, 64, 34
    z = SZone('seabase_1', W, H, GC, (4.5, 6.0, 7.5))
    # ---- walls (2 cells thick between rooms)
    z.wall(0, 11, W, 2)
    z.wall(25, 1, 2, 10)
    z.wall(45, 1, 2, 10)
    z.wall(0, 19, 47, 2)
    z.wall(53, 19, 19, 2)
    z.wall(45, 21, 2, 26)
    z.wall(53, 21, 2, 26)
    z.wall(0, 47, W, 2)
    z.wall(22, 49, 2, 14)
    z.wall(46, 49, 2, 14)
    for d in ((34, 11, 3, 2), (12, 11, 3, 2), (57, 11, 3, 2), (25, 4, 2, 3), (45, 4, 2, 3), (10, 19, 3, 2), (31, 19, 3, 2),
              (62, 19, 3, 2), (45, 31, 2, 3), (53, 25, 2, 3), (53, 39, 2, 3), (31, 47, 3, 2), (39, 47, 3, 2), (9, 47, 3, 2),
              (49, 47, 3, 2), (63, 47, 3, 2), (22, 54, 2, 3), (46, 54, 2, 3)):
        z.door(*d)
    # ---- flood water: the main passage and the ballast passage (held back by the door coamings)
    z.water(1, 13, 70, 6)
    z.water(47, 19, 6, 28)

    # ---- the main passage (rows 13-18): flood barriers across half its width, pipe runs along the walls
    for (c, r, ch) in ((6, 13, 'b'), (18, 16, 's'), (28, 13, 'b'), (40, 16, 's'), (60, 13, 'b'), (67, 16, 's')):
        z.run(c, r, 3, ch, vertical=True)
    for (c, r, n) in ((2, 18, 3), (20, 13, 5), (56, 18, 4), (43, 13, 3)):
        z.run(c, r, n, 'i')
    for (c, r) in ((11, 17), (33, 14), (24, 18), (63, 17), (52, 13)):
        z.put(c, r, 'c')
    z.put(46, 17, 'k')
    z.f.put(14, 15, '!')
    z.f.put(15, 15, '!')
    z.f.put(16, 15, '!')
    z.f.put(36, 16, '!')
    z.f.put(37, 16, '!')
    z.f.put(38, 16, '!')
    # ---- the ballast passage (cols 47-52): barriers across it, a pipe run up its east wall
    z.run(47, 26, 3, 'b')
    z.run(50, 34, 3, 's')
    z.run(47, 42, 3, 'b')
    z.run(52, 28, 4, 'i', vertical=True)
    z.put(48, 38, 'c')
    z.put(51, 22, 'c')

    # ---- moon pool dock (cols 1-44, rows 21-46): the pool, winches, spools, the ROV, baskets, lockers, the gallery
    z.block(13, 30, 12, 10, 'M')
    z.block(13, 26, 2, 2, 'W')
    z.block(23, 26, 2, 2, 'W')
    z.block(8, 33, 2, 2, 'U')
    z.block(28, 36, 2, 2, 'U')
    z.block(3, 40, 2, 2, 'V')
    z.block(7, 43, 2, 2, 'K')
    z.block(31, 43, 2, 2, 'K')
    for (c, r) in ((16, 22), (29, 22), (5, 36)):
        z.block(c, r, 2, 2, 'C')
    for (c, r) in ((19, 24), (20, 44), (32, 40), (11, 39), (26, 42), (6, 29), (2, 33)):
        z.put(c, r, 'c')
    for (c, r) in ((1, 26), (1, 44), (44, 45)):
        z.put(c, r, 'g')
    for (c, r) in ((27, 31), (11, 37)):
        z.put(c, r, 'k')
    for c in (3, 5, 20, 22):
        z.block(c, 21, 2, 1, 'L')
    z.block(7, 21, 2, 1, 'T')
    z.block(25, 21, 2, 1, 'T')
    # gallery deck over the north-east of the dock: control cabin, rails, stair, columns, stores underneath
    z.d.rect(35, 21, 10, 10, 'u')
    z.d.rect(38, 21, 6, 4, 'J')
    for c in range(35, 45):
        if c not in (37, 38):
            z.d.g[30][c] = 'r'
    for r in range(21, 30):
        z.d.g[r][35] = 'r'
    z.block(37, 31, 2, 7, 'N')
    for (c, r) in ((35, 30), (41, 30), (35, 25)):
        z.put(c, r, 'I')
    z.block(39, 21, 2, 1, 'T')
    z.block(42, 21, 2, 1, 'L')
    for (c, r) in ((37, 24), (43, 27), (36, 28)):
        z.put(c, r, 'c')
    z.block(39, 26, 2, 2, 'C')
    z.put(44, 23, 'g')
    z.mark(37, 38, 2, 1, '/')
    for (c, r) in ((9, 30), (29, 30), (9, 41), (29, 41)):
        z.mark(c, r, 1, 1, ';')

    # ---- ballast tank room (cols 55-70, rows 21-46)
    z.block(57, 23, 6, 3, 'H')
    z.block(57, 38, 6, 3, 'H')
    for (c, r) in ((66, 24), (66, 31), (66, 39)):
        z.block(c, r, 2, 2, 'x')
    z.run(60, 29, 6, 'i')
    z.block(70, 33, 1, 2, 'e')
    z.block(70, 43, 1, 2, 'e')
    for (c, r) in ((56, 33), (63, 35), (69, 28)):
        z.put(c, r, 'c')
    z.put(56, 45, 'g')
    z.put(59, 33, 'k')

    # ---- pump room (cols 48-70, rows 49-62)
    for c in (52, 58, 64):
        z.block(c, 53, 3, 2, 'p')
    z.block(54, 49, 4, 1, 'm')
    z.block(67, 49, 4, 1, 'm')
    z.block(52, 59, 2, 2, 't')
    z.block(68, 57, 2, 2, 't')
    z.run(56, 58, 9, 'i')
    z.block(59, 62, 2, 1, 'e')
    z.block(63, 62, 2, 1, 'e')
    for (c, r) in ((49, 56), (70, 53), (66, 60)):
        z.put(c, r, 'c')
    z.put(50, 61, 'g')
    z.put(61, 51, 'k')

    # ---- dive lockers (cols 1-21, rows 49-62)
    for r in (50, 53, 58):
        z.block(1, r, 1, 2, 'L')
    for c in (4, 7, 13, 16):
        z.block(c, 62, 2, 1, 'L')
    z.block(10, 62, 2, 1, 'T')
    z.block(19, 62, 2, 1, 'T')
    for (c, r) in ((6, 55), (6, 58), (13, 55), (13, 58)):
        z.block(c, r, 2, 1, 'B')
    z.block(17, 51, 2, 1, 'y')
    z.block(3, 49, 2, 1, 'y')
    z.put(20, 55, 'k')
    z.put(15, 50, 'c')

    # ---- arrival lock (cols 24-45, rows 49-62): the decompression chamber, cabinets, benches
    z.block(24, 49, 5, 3, 'd')
    z.block(45, 50, 1, 2, 'e')
    z.block(45, 57, 1, 2, 'e')
    z.block(29, 56, 2, 1, 'B')
    z.block(40, 56, 2, 1, 'B')
    for (c, r) in ((31, 52), (39, 52)):
        z.put(c, r, 'O')
    z.put(26, 60, 'k')
    z.put(43, 61, 'c')
    z.put(24, 61, 'g')
    z.block(24, 59, 1, 2, 'T')
    z.block(35, 49, 2, 1, 'L')
    z.block(42, 49, 2, 1, 'L')
    z.block(27, 54, 2, 1, 'y')
    z.block(41, 53, 2, 2, 'K')
    z.mark(34, 62, 3, 1, '/')

    # ---- north band: cargo hold (cols 1-24), exit lock (27-44), battery room (47-70)
    for (c, r) in ((2, 2), (2, 7), (9, 2), (18, 2), (15, 7)):
        z.block(c, r, 2, 2, 'C')
    z.block(6, 6, 2, 2, 'K')
    z.block(21, 6, 2, 2, 'U')
    z.block(12, 4, 2, 2, 'U')
    for (c, r) in ((5, 2), (8, 8), (16, 4), (23, 2), (11, 9)):
        z.put(c, r, 'c')
    z.put(1, 5, 'g')
    z.put(20, 9, 'k')
    for c in (28, 41):
        z.block(c, 1, 2, 1, 'e')
    z.block(30, 7, 2, 1, 'B')
    z.block(39, 7, 2, 1, 'B')
    for (c, r) in ((31, 4), (39, 4)):
        z.put(c, r, 'O')
    z.put(43, 9, 'k')
    z.put(28, 9, 'c')
    for c in (49, 53, 61, 65):
        z.block(c, 1, 2, 1, 'e')
    for c in (50, 56, 62):
        z.block(c, 5, 3, 2, 'j')
    z.block(70, 3, 1, 2, 'e')
    z.block(70, 7, 1, 2, 'e')
    z.put(68, 9, 'c')
    z.put(47, 9, 'k')
    z.mark(34, 1, 3, 1, '/')

    # ---- wall art (codes layer): portholes in the outer hull, emergency lights, leaks, stencils, signs
    z.art([(0, r) for r in (23, 27, 31, 35, 39)] + [(0, 15)] + [(c, 0) for c in (5, 12, 19)] + [(c, 0) for c in (52, 59, 66)] +
          [(71, r) for r in (25, 37, 43, 15)] + [(c, 63) for c in (7, 15, 54, 62)], 'o')
    z.art([(4, 12), (40, 12), (65, 12), (17, 20), (46, 52), (60, 48), (71, 57), (0, 55), (56, 20)], '1')
    z.art([(8, 19), (28, 19), (50, 12), (22, 12), (45, 24), (54, 30), (46, 60), (24, 48), (57, 63), (0, 45), (30, 0), (71, 5)], '2')
    z.art([(1, 20), (17, 12), (52, 48), (71, 51), (68, 20), (36, 20), (16, 48), (54, 22)], '3')
    z.art([(30, 12), (58, 19), (2, 12), (45, 40), (53, 44), (70, 12)], '4')
    z.art([(71, 60), (61, 48), (0, 37), (14, 20), (66, 63)], '5')
    z.art([(27, 20), (26, 12), (35, 48)], '6')
    z.art([(42, 12), (60, 20), (57, 48), (37, 47)], '7')
    z.art([(0, 29), (24, 0), (46, 2), (71, 31), (12, 48), (23, 58)], '8')

    # ---- ceilings
    z.ceil(4.5, 1, 13, 70, 6, '=', '+', pipe='-', run=('r', 15))
    z.ceil(4.5, 47, 19, 6, 28, '=', '+', pipe='-', run=('c', 49))
    z.ceil(7.5, 1, 21, 44, 26, '=', '+', every=6)
    z.ceil(6.0, 55, 21, 16, 26, '=', '+')
    z.ceil(6.0, 48, 49, 23, 14, '=', '+')
    z.ceil(4.5, 1, 49, 21, 14, '=', '+')
    z.ceil(4.5, 24, 49, 22, 14, '=', '+')
    z.ceil(6.0, 1, 1, 24, 10, '=', '+')
    z.ceil(4.5, 27, 1, 18, 10, '=', '+')
    z.ceil(4.5, 47, 1, 24, 10, '=', '+')

    # ---- spawns and pickups
    for (c, r) in ((23, 15), (44, 15), (8, 16), (63, 14), (50, 30), (5, 24), (33, 27), (28, 40), (5, 4), (58, 9),
                   (62, 33), (60, 56), (10, 52)):
        z.put(c, r, 'S')
    for (c, r) in ((21, 46), (69, 45), (36, 5)):
        z.put(c, r, 'a')
    for (c, r) in ((4, 57), (69, 51), (13, 9)):
        z.put(c, r, 'h')
    return z


# ================================================================ zone 2: the Research Ring
def zone2():
    W, H, GC = 71, 64, 34
    z = SZone('seabase_2', W, H, GC, (4.5, 7.0))
    z.k.g[0][0] = '%'          # research finish
    z.wall(0, 9, W, 2)
    z.wall(22, 1, 2, 8)
    z.wall(47, 1, 2, 8)
    z.wall(0, 17, 15, 2)
    z.wall(21, 17, 29, 2)
    z.wall(56, 17, 15, 2)
    z.wall(13, 19, 2, 25)
    z.wall(56, 19, 2, 25)
    z.wall(21, 19, 2, 25)
    z.wall(48, 19, 2, 25)
    z.wall(0, 44, 15, 2)
    z.wall(21, 44, 29, 2)
    z.wall(56, 44, 15, 2)
    z.wall(0, 52, W, 2)
    z.wall(22, 54, 2, 9)
    z.wall(47, 54, 2, 9)
    for d in ((34, 9, 3, 2), (9, 9, 3, 2), (59, 9, 3, 2), (22, 3, 2, 3), (47, 3, 2, 3), (13, 30, 2, 3), (56, 30, 2, 3),
              (34, 17, 3, 2), (34, 44, 3, 2), (21, 23, 2, 3), (48, 23, 2, 3), (28, 52, 3, 2), (40, 52, 3, 2), (9, 52, 3, 2),
              (59, 52, 3, 2), (22, 57, 2, 3), (47, 57, 2, 3)):
        z.door(*d)
    # glass fronts of the four labs at the ring ends (doors in the middle)
    for (c, r0) in ((13, 11), (57, 11), (13, 46), (57, 46)):
        for r in range(r0, r0 + 6):
            z.put(c, r, 'q')
        z.rect(c, r0 + 1, 1, 3, 'f')
    # the observation chambers in the notches, the hub landmark, the dome
    z.block(1, 19, 12, 25, 'A')
    z.block(58, 19, 12, 25, 'Z')
    z.block(31, 27, 9, 9, 'Y')
    # ---- hub mezzanine (layer 3.2): three arms, rails, stairs, columns
    z.d.rect(23, 19, 4, 15, 'u')
    z.d.rect(23, 19, 25, 4, 'u')
    z.d.rect(44, 19, 4, 15, 'u')
    for r in range(22, 34):
        z.d.g[r][26] = 'r'
        z.d.g[r][44] = 'r'
    for c in range(27, 44):
        z.d.g[22][c] = 'r'
    for c in (25, 45):
        z.d.g[33][c] = 'r'
    z.block(23, 34, 2, 7, 'N')     # the stairs rise north onto the arms' ends; their feet open onto the hub floor
    z.block(46, 34, 2, 7, 'N')
    z.mark(23, 41, 2, 1, '/')
    z.mark(46, 41, 2, 1, '/')
    for (c, r) in ((26, 23), (26, 29), (26, 33), (44, 23), (44, 29), (44, 33), (30, 22), (40, 22)):
        z.put(c, r, 'I')
    # under the arms: sonar desks, comms racks, chairs; on the floor: console desks round the hub table
    z.block(23, 30, 2, 3, 'v')
    z.block(46, 30, 2, 3, 'v')
    z.block(23, 27, 1, 2, 'z')
    z.block(47, 27, 1, 2, 'z')
    z.block(30, 19, 2, 1, 'z')
    z.block(39, 19, 2, 1, 'z')
    for (c, r) in ((25, 31), (45, 31), (27, 20), (43, 20)):
        z.put(c, r, 'w')
    for (c, r) in ((28, 25), (41, 25), (28, 38), (41, 38)):
        z.block(c, r, 2, 1, 'X')
    for (c, r) in ((29, 26), (42, 26), (29, 37), (42, 37)):
        z.put(c, r, 'w')
    z.put(36, 41, 'c')
    z.put(28, 42, 'k')
    # ---- ring corridor: carts, crates, screens; benches
    for (c, r) in ((18, 12), (47, 15), (16, 38), (54, 24), (20, 49), (45, 47)):
        z.put(c, r, 'c')
    for (c, r) in ((26, 14), (52, 41), (17, 25)):
        z.put(c, r, 'k')
    z.block(29, 11, 2, 1, 'B')
    z.block(41, 11, 2, 1, 'B')
    z.block(31, 51, 2, 1, 'B')
    z.block(37, 51, 2, 1, 'B')
    for (c, r) in ((15, 21), (15, 41), (55, 21), (55, 41)):
        z.put(c, r, 'g')
    z.block(15, 34, 1, 2, 'e')
    z.block(55, 35, 1, 2, 'e')
    # ---- labs behind glass: sample lab (NW), sonar room (NE), tank lab (SW), geology (SE)
    for (c, r) in ((2, 12), (6, 12), (2, 15), (6, 15)):
        z.block(c, r, 2, 1, 'l')
    z.put(10, 12, 'F')
    z.put(10, 15, 'F')
    for (c, r) in ((4, 13), (8, 14)):
        z.put(c, r, 'w')
    for c in (62, 66):
        z.block(c, 11, 3, 2, 'v')
    z.block(69, 14, 1, 2, 'z')
    z.put(63, 14, 'w')
    z.put(67, 14, 'w')
    for c in (4, 7):
        z.block(c, 47, 2, 2, 'R')
    z.block(1, 46, 1, 4, 'Q')
    z.block(2, 51, 4, 1, 'Q')
    z.put(10, 46, 'F')
    for (c, r) in ((62, 51), (65, 51)):
        z.block(c, r, 2, 1, 'n')
    z.block(69, 48, 1, 2, 'n')
    z.block(60, 47, 2, 1, 'l')
    z.block(64, 47, 2, 1, 'l')
    z.put(68, 47, 'c')
    z.put(68, 49, 'w')
    # ---- north band: core store (NW), exit lobby, comms (NE)
    for c in (2, 5, 8, 14, 17):
        z.block(c, 1, 2, 1, 'n')
    z.block(3, 5, 2, 1, 'l')
    z.block(9, 5, 2, 1, 'l')
    z.block(15, 5, 2, 2, 'C')
    z.put(20, 7, 'c')
    z.put(12, 7, 'k')
    z.put(6, 6, 'w')
    for c in (26, 43):
        z.block(c, 1, 2, 1, 'e')
    z.block(29, 6, 2, 1, 'B')
    z.block(40, 6, 2, 1, 'B')
    for (c, r) in ((31, 3), (39, 3)):
        z.put(c, r, 'O')
    z.put(25, 8, 'c')
    z.put(45, 8, 'k')
    for c in (50, 53, 56, 62, 65):
        z.block(c, 1, 2, 1, 'z')
    for (c, r) in ((52, 5), (58, 5), (64, 5)):
        z.block(c, r, 2, 1, 'X')
    for (c, r) in ((53, 6), (59, 4), (65, 6)):
        z.put(c, r, 'w')
    z.put(69, 7, 'c')
    z.mark(34, 1, 3, 1, '/')
    # ---- south band: wet lab (SW, flooded), entry lobby, instrument bay (SE)
    z.water(1, 54, 21, 9)
    for (c, r) in ((3, 56), (7, 56), (11, 56), (3, 60)):
        z.block(c, r, 2, 2, 'R')
    z.block(15, 62, 4, 1, 'Q')
    z.block(8, 62, 4, 1, 'Q')
    z.block(16, 56, 2, 1, 'l')
    z.run(19, 58, 3, 's', vertical=True)
    z.put(14, 59, 'c')
    z.block(24, 54, 1, 2, 'e')
    z.block(46, 54, 1, 2, 'e')
    z.block(29, 58, 2, 1, 'B')
    z.block(40, 58, 2, 1, 'B')
    for (c, r) in ((31, 56), (39, 56)):
        z.put(c, r, 'O')
    z.put(26, 61, 'k')
    z.put(44, 61, 'c')
    z.block(51, 55, 2, 2, 'V')
    z.block(56, 58, 2, 2, 'K')
    z.block(63, 55, 2, 2, 'C')
    z.block(66, 59, 2, 2, 'U')
    z.block(68, 55, 2, 2, 'C')
    for (c, r) in ((54, 61), (60, 56), (61, 61), (50, 59)):
        z.put(c, r, 'c')
    z.put(57, 55, 'k')
    z.mark(34, 62, 3, 1, '/')

    # ---- wall art: hull portholes in the outer walls, screens, logo, signs, fire points, emergency lights
    z.art([(c, 0) for c in (6, 15, 55, 64)] + [(0, r) for r in (13, 48, 58)] + [(70, r) for r in (13, 48, 58)] +
          [(c, 63) for c in (6, 15, 56, 64)], 'o')
    z.art([(31, 17), (40, 17), (24, 9), (46, 9), (21, 18), (28, 44), (42, 44), (12, 9), (58, 9)], '9')
    z.art([(30, 0), (40, 0)], '0')
    z.art([(26, 18), (44, 18), (26, 44), (44, 44)], '6')
    z.art([(14, 25), (56, 25), (14, 38), (56, 38)], '7')
    z.art([(18, 10), (52, 10), (18, 52), (52, 52), (0, 5), (70, 4)], '8')
    z.art([(14, 22), (56, 22), (14, 40), (56, 40), (38, 10), (35, 53)], '2')
    z.art([(4, 53), (19, 53), (0, 60)], '1')
    z.art([(12, 53), (23, 61)], '4')

    # ---- ceilings: 4.5 m everywhere but the hub (7 m round the dome)
    z.ceil(4.5, 1, 1, 69, 62, '"', "'")
    for r in range(19, 44):
        for c in range(23, 48):
            z.c[4.5].g[r][c] = '.'
    z.c[7.0].rect(27, 23, 17, 17, '@')
    z.ceil(7.0, 23, 19, 25, 25, '"', "'")

    # ---- spawns and pickups
    for (c, r) in ((17, 14), (52, 13), (40, 14), (17, 30), (53, 30), (29, 30), (42, 33), (31, 41), (7, 3), (61, 3),
                   (10, 59), (60, 59), (17, 48), (53, 49)):
        z.put(c, r, 'S')
    for (c, r) in ((5, 13), (44, 49), (36, 5)):
        z.put(c, r, 'a')
    for (c, r) in ((65, 15), (25, 48), (33, 24)):
        z.put(c, r, 'h')
    return z


def main():
    zones = []
    for fn, size in ((zone1, ((72, 72), (64, 64))), (zone2, ((71, 71), (64, 64)))):
        z = fn()
        errs, stats = check(z, size)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
