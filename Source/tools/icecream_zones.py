#!/usr/bin/env python3
"""INKBOLT Scoops & Cream zones (theme 'icecream'): hand-placed layouts -> src/data/zones/icecream_*.txt

    python3 tools/icecream_zones.py            # write + validate
    python3 tools/icecream_zones.py --print    # ... and print the maps
    python3 tools/icecream_zones.py --check    # validate only

Every zone file has the floor plan and three layers: "@layer 0.01" (floor tiles and marks, plus wall-art codes on the
wall cells, read by the theme's wall chooser; cell (0, 0) holds ',' in the creamery), a raised layer ("@layer 1.2":
the parlour's terrace; "@layer 3.5": the creamery's mezzanine) and "@layer 7" (ceiling bays [4, 4]). Symbols: see
src/data/themes/icecream.js.

Zone 1, the Parlour, is 72 x 60 m (gates at columns 34-36, the player starts in the entrance vestibule at (35, 57));
zone 2, the Creamery, is 70 x 58 m (gates at columns 34-36, entry at (35, 55)).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

WALK = set('dJT')     # the vestibule doors and the freezer door are doorways; the terrace steps are walkable
PREFAB = {'D': (2, 2), 'k': (1, 2), 'R': (2, 2), 'U': (3, 2), 'W': (3, 2), 'Y': (3, 2), 'Q': (2, 1), 'b': (2, 1), 'F': (2, 1),
          'L': (6, 6), 'B': (2, 3), 't': (2, 2), 'f': (3, 1), 'n': (2, 1), 'K': (4, 4), 'j': (2, 2), 'd': (4, 1), 'T': (3, 3),
          'M': (2, 2), 'V': (2, 2), 'X': (3, 2), 'J': (3, 1), 'z': (2, 1), 'H': (3, 2), 'A': (2, 1), 'C': (2, 1), 'Z': (2, 2),
          'N': (2, 7), 'o': (8, 5), '<': (2, 1), '/': (3, 1), '>': (2, 2), '=': (3, 1)}
CEIL = {'lamp': '5', 'plain': '6', 'sky': '7', 'k': '8', 'duct': '9'}


class IZone(Zone):
    """floor plan + floor layer (f) + raised layer (d, at dy) + ceiling bays (k)"""

    def __init__(self, name, w, h, gc, dy):
        Zone.__init__(self, name, w, h)
        self.dy = dy
        self.f = Zone(name + '_f', w, h)
        self.d = Zone(name + '_d', w, h)
        self.k = Zone(name + '_k', w, h)
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

    def tiles(self, c0, r0, w, h, fn):
        """floor tiles: fn(c, r) -> symbol or None, on every non-wall cell (props stand on the tiles)"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) not in '#GE' and self.f.g[r][c] == '.':
                    ch = fn(c, r)
                    if ch:
                        self.f.g[r][c] = ch

    def ceiling(self, fn, skip=()):
        """[4, 4] ceiling bays over rows 1 .. h-2 (cols 0 .. w-1 in whole bays); fn(i, j) -> bay symbol; skip: cell
        rectangles (c0, r0, c1, r1) kept clear (a tall landmark under them)"""
        nj = (self.h - 2) // 4
        for i in range(self.w // 4):
            for j in range(nj):
                c0, r0 = i * 4, 1 + j * 4
                if any(not (c0 + 4 <= a or c0 >= c or r0 + 4 <= b or r0 >= d) for (a, b, c, d) in skip):
                    continue
                ch = fn(i, j)
                if ch:
                    self.k.rect(c0, r0, 4, 4, ch)

    def text(self):
        return (Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer %g\n' % self.dy + self.d.text() +
                '@layer 7\n' + self.k.text())


def check(z, size):
    errs, stats = validate(z, WALK, PREFAB, size=size)
    # door blocks sit in a wall line: their two ends against wall / glass / panel cells
    for ch in 'dJ':
        for (c, r, w, h) in rects(z.g, ch):
            ends = [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)] if w > h else \
                [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)]
            for (a, b) in ends:
                if z.at(a, b) not in '#ei':
                    errs.append('door %r at (%d,%d) end (%d,%d) is %r' % (ch, c, r, a, b, z.at(a, b)))
    # nothing stands in front of a door's two faces
    for ch in 'dJ':
        for (c, r, w, h) in rects(z.g, ch):
            for k in range(w):
                for rr in (r - 1, r + h):
                    if z.at(c + k, rr) not in '.SahP':
                        errs.append('door %r face cell (%d,%d) holds %r' % (ch, c + k, rr, z.at(c + k, rr)))
    return errs, stats


# ================================================================ zone 1: the Parlour
def zone1():
    W, H, GC = 72, 60, 34
    z = IZone('icecream_1', W, H, GC, 1.2)
    # ---- the back bar along the north wall (row 1): cake freezers, soft-serve machines, back counters
    west = 'F b Q b b . Q b F b . b b'.replace(' ', '')
    east = 'b b Q b . F b . Q b b b'.replace(' ', '')
    c = 2
    for ch in west:
        if ch != '.':
            z.block(c, 1, 2, 1, ch)
        c += 2
    assert c <= 32, c
    c = 39
    for ch in east:
        if ch != '.':
            z.block(c, 1, 2, 1, ch)
        c += 2
    assert c <= 70, c
    # menu boards over the west back bar, the script logo and more menus over the east one
    for c0 in (11, 23, 55):          # three menu walls of three boards (scoops, cones, sundaes)
        z.art([(c0, 0)], '1')
        z.art([(c0 + 1, 0)], '2')
        z.art([(c0 + 2, 0)], '3')
    z.art([(c, 0) for c in range(41, 51)], '*')
    z.art([(17, 0), (61, 0)], '(')
    z.art([(29, 0)], ')')
    z.art([(1, 0), (32, 0), (38, 0), (70, 0)], '!')
    # ---- the counters (rows 6-7; customers to the south): sundae / waffle station, the scoop bar, the shake bar
    z.block(4, 6, 1, 2, 'k')
    z.block(5, 6, 6, 2, 'U')
    z.block(11, 6, 3, 2, 'W')
    z.block(14, 6, 2, 2, 'R')
    z.block(16, 6, 1, 2, 'k')
    z.block(21, 6, 1, 2, 'k')
    z.block(22, 6, 8, 2, 'D')
    z.block(30, 6, 2, 2, 'R')
    z.block(32, 6, 8, 2, 'D')
    z.block(40, 6, 3, 2, 'U')
    z.block(43, 6, 1, 2, 'k')
    z.block(51, 6, 1, 2, 'k')
    z.block(52, 6, 6, 2, 'Y')
    z.block(58, 6, 3, 2, 'W')
    z.block(61, 6, 2, 2, 'R')
    z.block(63, 6, 1, 2, 'k')
    for col in (52, 54, 56):
        z.put(col, 8, 's')
    # queue belts in front of the scoop bar: a U open to the west
    z.run(25, 10, 14, 'q')
    z.run(25, 12, 14, 'q')
    z.put(38, 11, 'q')
    # napkin stations at the counter gaps
    for (c, r) in ((18, 9), (49, 9)):
        z.put(c, r, 'x')
    # ---- structural columns (candy-striped)
    for (c, r) in ((12, 17), (24, 17), (48, 17), (60, 17), (12, 33), (24, 33), (48, 33), (60, 33)):
        z.put(c, r, 'O')
    # ---- pushcarts in the open floor in front of the queue and by the window bar
    for (c, r) in ((15, 14), (54, 15), (26, 52), (44, 51)):
        z.block(c, r, 2, 1, '<')
    # ---- the giant cone (landmark) under a clear ceiling
    z.block(33, 20, 6, 6, 'L')
    for (c, r) in ((31, 19), (40, 26)):
        z.put(c, r, 'v')
    # ---- west wall booths (three groups) with planters, posters and a fire point between
    for r0 in (13, 24, 34):
        z.block(1, r0, 2, 9, 'B')
    for r in (22, 33):
        z.put(1, r, 'v')
        z.put(2, r, 'c')
    z.art([(0, 14), (0, 28), (0, 39)], '(')
    z.art([(0, 18), (0, 31)], ')')
    z.art([(0, 23)], '!')
    z.art([(0, 44)], '^')
    # ---- east wall: booths by the windows, the milkshake corner
    for r0 in (13, 24):
        z.block(69, r0, 2, 3, 'B')
    z.art([(W - 1, r) for r in range(13, 16)] + [(W - 1, r) for r in range(24, 27)], '[')
    for r in (14, 25):
        z.f.g[r][W - 1] = ']'
    z.art([(W - 1, 21)], '!')
    z.put(69, 20, 'v')
    z.put(70, 30, 'c')
    # ---- the pastel table area (south of the cone): bistro tables in loose clusters, planters, bins
    for (c, r) in ((18, 29), (22, 33), (27, 30), (29, 35), (34, 32), (38, 37), (41, 30), (44, 34),
                   (52, 29), (55, 33), (51, 38), (30, 41), (18, 39)):
        z.block(c, r, 2, 2, 't')
    for (c, r) in ((15, 30), (47, 40)):
        z.put(c, r, 'v')
    for (c, r) in ((20, 26), (57, 28)):
        z.put(c, r, 'c')
    # planter-box dividers between the table groups (low cover)
    for (c, r) in ((13, 26), (25, 27), (45, 27), (55, 26), (24, 44), (37, 46), (46, 45), (14, 33)):
        z.block(c, r, 3, 1, '/')
    # ---- the kids' corner (south-east): soft play, crayon tables, bean bags, the mural
    z.block(64, 44, 4, 4, 'K')
    z.block(58, 50, 2, 2, 'j')
    z.block(63, 51, 2, 2, 'j')
    for (c, r) in ((59, 46), (61, 48), (67, 50), (68, 53), (60, 54), (66, 55)):
        z.put(c, r, 'g')
    for r in (41, 45, 49, 53):
        z.art([(W - 1, r)], '{')
        z.art([(W - 1, r + 2)], '}')
    z.art([(W - 1, 36)], '^')
    # ---- the raised terrace (south-west, 1.2 m): deck, rails, two flights of steps from the south, lounge sofas
    #      and tables up on it
    z.d.rect(1, 44, 16, 11, 'w')
    for c in range(1, 17):
        z.d.g[44][c] = 'l'
    for r in range(44, 55):
        z.d.g[r][16] = 'l'
    for c in range(1, 17):
        if c not in (4, 5, 6, 11, 12, 13):
            z.d.g[54][c] = 'l'
    z.block(4, 55, 3, 3, 'T')
    z.block(11, 55, 3, 3, 'T')
    z.d.block(1, 45, 1, 3, 'f', over='w')
    z.d.block(1, 49, 1, 3, 'f', over='w')
    for (c, r) in ((4, 46), (8, 46), (12, 46), (4, 50), (8, 50), (12, 50)):
        z.d.block(c, r, 2, 2, 't', over='w')
    z.art([(0, r) for r in (46, 51)], ')')
    z.art([(0, 54)], '!')
    # ---- the shop front (south wall): windows, the window bar, the entrance vestibule
    for c in list(range(18, 32)) + list(range(40, 56)):
        if c not in (24, 25, 26, 47, 48, 49):
            z.art([(c, H - 1)], '[' if c % 3 else ']')
    for c in (18, 20, 22, 27, 29, 41, 43, 45, 50, 52):
        z.block(c, H - 2, 2, 1, 'n')
    z.art([(24, H - 1), (48, H - 1)], '!')
    z.art([(16, H - 1), (57, H - 1)], '(')
    for r in range(55, H - 1):
        z.put(32, r, 'e')
        z.put(39, r, 'e')
    z.put(32, 54, 'e')
    z.put(33, 54, 'e')
    z.block(34, 54, 4, 1, 'd')
    z.put(38, 54, 'e')
    z.put(39, 54, 'e')
    z.put(38, 56, 'v')
    z.f.rect(34, 56, 3, 2, '+')
    # ---- floor: pink checker in the customer area, chocolate checker behind the counter
    z.tiles(1, 1, W - 2, 7, lambda c, r: ';' if (c + r) % 2 == 0 else None)
    z.tiles(1, 8, W - 2, H - 9, lambda c, r: ':' if (c + r) % 2 == 0 and not (c <= 16 and 44 <= r <= 54) and z.at(c, r) not in 'B' else None)
    # ---- spawns and pickups
    for (c, r) in ((8, 3), (27, 3), (44, 3), (66, 4), (8, 11), (60, 12), (16, 22), (56, 22), (28, 24), (44, 24), (8, 40), (49, 50)):
        z.put(c, r, 'S')
    for (c, r) in ((19, 10), (63, 27), (24, 49)):
        z.put(c, r, 'a')
    for (c, r) in ((50, 10), (10, 30), (60, 41)):
        z.put(c, r, 'h')
    # ---- ceiling: coffers with pendant lamps in a checker, plain mint / sky coffers between; clear over the cone
    z.ceiling(lambda i, j: CEIL['lamp'] if (i % 2 == 0 and j % 2 == 0) else (CEIL['plain'] if (i + j) % 2 else CEIL['sky']),
              skip=[(31, 18, 41, 28)])
    return z


# ================================================================ zone 2: the Creamery
def zone2():
    W, H, GC = 70, 58, 34
    z = IZone('icecream_2', W, H, GC, 3.5)
    z.f.g[0][0] = ','          # kitchen wall finish
    # ---- the mezzanine over the north-west corner (3.5 m): the PARTY ROOM on it, the walk-in freezer under it
    z.d.rect(1, 1, 22, 16, 'u')
    z.d.block(6, 2, 8, 5, 'o', over='u')
    for c in range(1, 23):
        if c not in (18, 19):
            z.d.g[16][c] = 'r'
    for r in range(1, 16):
        z.d.g[r][22] = 'r'
    for (c, r) in ((4, 9), (10, 9), (15, 12), (4, 13)):
        z.d.block(c, r, 2, 2, 't', over='u')
    for (c, r) in ((2, 2), (15, 3), (20, 9), (8, 14)):
        z.d.put(c, r, '4', over='u')
    z.block(18, 17, 2, 7, 'N')
    for (c, r) in ((8, 16), (15, 16), (22, 16), (22, 9), (17, 9)):
        z.put(c, r, 'I')
    # walk-in freezer: insulated panels with the door, frosted shelving on the walls, pallets of tubs inside
    for c in range(1, 15):
        if not 6 <= c <= 8:
            z.put(c, 12, 'i')
    for r in range(1, 12):
        z.put(14, r, 'i')
    z.block(6, 12, 3, 1, 'J')
    z.block(2, 1, 10, 1, 'z')
    z.block(1, 3, 1, 8, 'z')
    for (c, r) in ((5, 4), (9, 5), (11, 8), (4, 8)):
        z.put(c, r, 'p')
    z.block(6, 7, 2, 2, 'Z')
    # dry store under the rest of the deck: cone and cup pallets, wrapped stacks, empty pallets
    for (c, r) in ((16, 2), (17, 2), (20, 2), (16, 5), (20, 5), (3, 14), (11, 14), (13, 15)):
        z.put(c, r, 'p')
    z.block(18, 4, 2, 2, 'Z')
    z.block(16, 12, 2, 2, 'Z')
    for (c, r) in ((21, 2), (21, 6), (2, 15)):
        z.put(c, r, 'm')
    z.art([(0, 14)], '!')
    z.art([(16, 0)], '`')
    # ---- the mix room (north centre): mix and ageing tanks, cream cans
    for (c, r) in ((26, 3), (30, 3), (26, 8), (30, 8)):
        z.block(c, r, 2, 2, 'V')
    for (c, r) in ((25, 12), (29, 12), (33, 6)):
        z.put(c, r, 'y')
    z.art([(28, 0)], '@')
    # ---- the churn line (row 18-19, facing south) and the prep tables south of it
    for c in (25, 29, 38, 42, 46):
        z.block(c, 17, 2, 2, 'M')
    for (c, r) in ((25, 25), (39, 25), (44, 25), (25, 31), (39, 31)):
        z.block(c, r, 3, 2, 'H')
    for (c, r) in ((33, 20), (48, 28)):
        z.put(c, r, '|')
    # ---- dispatch (north-east): pallets of cartons by the dock door, wrapped stacks, a pallet jack
    z.art([(45, 0)], '$')
    z.f.g[0][44] = '_'
    z.f.g[0][46] = '_'
    for (c, r) in ((40, 3), (41, 3), (49, 3), (50, 3), (49, 7), (54, 2)):
        z.put(c, r, 'p')
    for (c, r) in ((56, 2), (42, 10)):
        z.block(c, r, 2, 2, 'Z')
    for (c, r) in ((53, 9), (59, 3)):
        z.put(c, r, 'm')
    z.put(47, 6, '%')
    z.art([(38, 0), (62, 0)], '!')
    # ---- blast freezers along the east wall, speed racks in front
    for r in (4, 10, 16, 22, 28):
        z.block(67, r, 2, 3, 'X')
    for (c, r) in ((64, 8), (64, 20)):
        z.put(c, r, '|')
    z.art([(W - 1, 35)], '!')
    z.art([(W - 1, 40)], '`')
    z.art([(W - 1, 45)], '?')
    # ---- the cake corner (south-east): decorating tables, a sink, boxed cakes on racks
    for (c, r) in ((55, 38), (60, 38), (55, 44)):
        z.block(c, r, 3, 2, 'H')
    z.block(64, 56, 2, 1, 'A')
    z.block(60, 56, 2, 1, 'A')
    for (c, r) in ((63, 48),):
        z.put(c, r, '|')
    for (c, r) in ((52, 36), (61, 52)):
        z.put(c, r, 'y')
    # ---- the staff entrance (south): lockers, sinks, hand-wash, notices, a fire exit
    for c in (20, 22, 24, 26, 28):
        z.block(c, H - 2, 2, 1, 'C')
    z.block(41, H - 2, 2, 1, 'A')
    z.block(44, H - 2, 2, 1, 'A')
    z.art([(43, H - 1), (47, H - 1)], '&')
    z.art([(31, H - 1)], '?')
    z.art([(17, H - 1)], '!')
    z.art([(0, 45)], '^')
    z.art([(0, 30)], '?')
    z.art([(0, 24)], '&')
    # ---- the west side (south of the deck): cone pallets in bays, wrapped stacks
    for (c, r) in ((3, 28), (4, 28), (7, 29), (3, 36), (8, 41), (12, 30)):
        z.put(c, r, 'p')
    for (c, r) in ((9, 22), (3, 22), (12, 37), (14, 44)):
        z.block(c, r, 2, 2, 'Z')
    for (c, r) in ((5, 47), (12, 47)):
        z.put(c, r, 'm')
    z.put(10, 33, '%')
    # ---- the novelty line (south centre): a churn pair feeding prep tables, speed racks, cans
    for c in (24, 28):
        z.block(c, 42, 2, 2, 'M')
    for (c, r) in ((32, 43), (36, 43)):
        z.block(c, r, 3, 2, 'H')
    for (c, r) in ((41, 43), (30, 47)):
        z.put(c, r, '|')
    z.put(27, 47, 'y')
    # ---- the filling lines (south): a tub filler at the west end of each line, conveyor modules, finished tubs
    for r in (48, 52):          # west of the main aisle (cols 31 - 41 stay clear) and east of it
        z.block(23, r, 2, 2, '>')
        z.block(25, r + 1, 6, 1, '=')
        z.block(42, r, 2, 2, '>')
        z.block(44, r + 1, 9, 1, '=')
        z.put(53, r + 1, 'p')
    z.art([(0, 18), (W - 1, 50), (10, H - 1)], '"')
    z.art([(0, 38), (52, H - 1)], '~')
    # ---- the south-west pallet bays: rows of cone / cup pallets and wrapped stacks
    for (c, r) in ((2, 50), (3, 50), (2, 52), (6, 50), (6, 54)):
        z.put(c, r, 'p')
    z.block(10, 51, 2, 2, 'Z')
    z.block(15, 50, 2, 2, 'Z')
    # ---- kitchen columns
    for (c, r) in ((23, 22), (35, 22), (50, 22), (23, 36), (35, 38), (50, 34), (14, 34), (60, 32)):
        z.put(c, r, '0')
    # ---- floor: quarry tiles everywhere; drains; yellow walkway lines on the main aisle
    for r in range(22, H - 3):
        for c in (32, 38):
            if z.at(c, r) == '.':
                z.f.g[r][c] = '-'
    for (c, r) in ((29, 21), (43, 21), (36, 35), (58, 42), (10, 26), (36, 13)):
        assert z.f.g[r][c] == '.', (c, r)
        z.f.g[r][c] = "'"
    # ---- spawns and pickups
    for (c, r) in ((35, 4), (46, 13), (60, 11), (29, 22), (43, 22), (57, 25), (6, 26), (16, 28), (50, 46), (10, 46), (30, 38), (62, 34)):
        z.put(c, r, 'S')
    for (c, r) in ((36, 30), (20, 40), (57, 50)):
        z.put(c, r, 'a')
    for (c, r) in ((12, 3), (48, 41), (24, 46)):
        z.put(c, r, 'h')
    # ---- ceiling: T-bar bays, duct runs every third row of bays; flat bays over the mezzanine
    z.ceiling(lambda i, j: CEIL['k'] if (i < 6 and j < 4) else (CEIL['duct'] if j % 3 == 1 else CEIL['k']))
    return z


def main():
    zones = []
    for fn, size in ((zone1, ((72, 72), (60, 60))), (zone2, ((70, 70), (58, 58)))):
        z = fn()
        errs, stats = check(z, size)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
