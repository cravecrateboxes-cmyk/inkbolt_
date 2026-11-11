#!/usr/bin/env python3
"""INKBOLT Helix Vault zones (theme 'datacenter'): hand-placed layouts -> src/data/zones/datacenter_*.txt

    python3 tools/datacenter_zones.py            # write + validate
    python3 tools/datacenter_zones.py --print    # ... and print the maps
    python3 tools/datacenter_zones.py --check    # validate only

Every zone file has three grids: the floor plan, "@layer 0.01" (floor finishes, plus wall-art codes on the wall
cells, read by the theme's wall chooser) and "@layer 6" (ceiling fittings, hanging from the 6 m ceiling). Interior
walls are two cells thick (every wall module has one room face; the security and vault doors are [3, 2]). Glass and
cage partitions are one cell thick, their doors [3, 1]. Symbols: see src/data/themes/datacenter.js.

Zones are 74 m wide (a very wide hall): the gates sit at columns 35-37, the player enters at (36, H - 3).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

W = 74
DOORS = 'DuVdlc'
WALK = set(DOORS)    # doors open when broken: the rooms behind them are reachable
PREFAB = {'R': (3, 1), 'r': (3, 1), ']': (3, 1), '[': (3, 1), 'C': (3, 1), 'T': (2, 1), 'U': (3, 1), 'B': (3, 1), 'Q': (2, 1),
          'N': (4, 2), 'M': (4, 2), 'K': (4, 4), 'W': (3, 1), 'g': (2, 1), 'j': (2, 1), 'H': (3, 2), 'A': (4, 4), 'Y': (4, 4),
          'F': (2, 2), 'b': (2, 1), 'f': (2, 2), 'y': (2, 1), 'X': (6, 6), 'L': (8, 4),
          'D': (3, 2), 'u': (3, 2), 'V': (3, 2), 'd': (3, 1), 'l': (3, 1), 'c': (3, 1)}


class DZone(Zone):
    """floor plan + floor layer (f) + ceiling layer (k)"""

    def __init__(self, name, h):
        Zone.__init__(self, name, W, h)
        self.f = Zone(name + '_f', W, h)
        self.k = Zone(name + '_k', W, h)
        self.rect(0, 0, W, 1, '#')
        self.rect(0, h - 1, W, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(W - 1, 0, 1, h, '#')
        self.rect(35, 0, 3, 1, 'G')
        self.rect(35, h - 1, 3, 1, 'E')
        self.put(36, h - 3, 'P')

    def wall(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '#')

    def door(self, c0, r0, ch, vertical=False):
        """a door block in a wall line (cells must be wall or floor): [3, 2] D u V, [3, 1] d l c"""
        d = 2 if ch in 'DuV' else 1
        w, h = (d, 3) if vertical else (3, d)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] in '#.qw', (self.name, c, r, self.g[r][c], 'door on', ch)
        self.rect(c0, r0, w, h, ch)

    def racks(self, c0, r, n, ch, vertical=False):
        """a run of n rack prefabs (3 m each) from (c0, r) along X (or Z)"""
        if vertical:
            self.block(c0, r, 1, 3 * n, ch)
        else:
            self.block(c0, r, 3 * n, 1, ch)

    def floor(self, c0, r0, w, h, ch, over='.'):
        """floor finish over the open cells of a rectangle (wall cells keep their art code)"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if 0 <= c < self.w and 0 <= r < self.h and self.at(c, r) not in '#GE' and self.f.g[r][c] in over:
                    self.f.g[r][c] = ch

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell', self.at(c, r))
            self.f.g[r][c] = ch

    def ceil(self, c0, r0, w, h, ch, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if 0 <= c < self.w and 0 <= r < self.h and self.at(c, r) not in '#GE' + DOORS and self.k.g[r][c] in over:
                    self.k.g[r][c] = ch

    def secure(self, c0, r0, w, h):
        """a secure room's floor: grey tiles, a hazard band on the cells along its walls"""
        self.floor(c0, r0, w, h, ',')
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.f.g[r][c] == ',' and any(self.at(c + dc, r + dr) == '#' for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.f.g[r][c] = '8'

    def text(self):
        return Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer 6\n' + self.k.text()


def check(z, size):
    errs, stats = validate(z, WALK, PREFAB, size=size)
    # every door block sits in a wall line: its two ends against wall / partition cells, its faces open
    for ch in DOORS:
        for (c, r, w, h) in rects(z.g, ch):
            if w < h:
                ends = [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)]
            else:
                ends = [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)]
            for (a, b) in ends:
                if z.at(a, b) not in '#qw':
                    errs.append('door %r at (%d,%d) end (%d,%d) is %r' % (ch, c, r, a, b, z.at(a, b)))
    return errs, stats


# ================================================================ zone 1: Data Hall A1 + NOC
def zone1():
    H = 50
    z = DZone('datacenter_1', H)
    # the lobby wall (2 thick) between the hall and the entry lobby: a wide spine opening and two security doors
    z.wall(1, 34, 72, 2)
    z.rect(32, 34, 10, 2, '.')
    z.door(17, 34, 'D')
    z.door(54, 34, 'D')
    # ---- hall: CRAC units along both side walls
    for r in (4, 11, 18, 25):
        z.block(1, r, 1, 3, 'C')
        z.block(72, r, 1, 3, 'C')
    z.block(1, 30, 1, 2, 'T')
    z.block(72, 30, 1, 2, 'T')
    # rack row pairs (fronts face a 3 m cold aisle, backs a 2 m hot aisle); blocks between the aisles
    blocks = [(5, 4), (20, 4), (42, 4), (57, 4)]
    pairs = [(5, 9), (14, 18), (25, 29)]
    cuts = {(14, 0): 3, (18, 0): 3, (5, 3): 2, (9, 3): 2, (25, 1): 1, (29, 2): 2}   # (row, block) -> prefabs kept
    for (ra, rb) in pairs:
        for bi, (c0, n) in enumerate(blocks):
            for row, ch in ((ra, 'R'), (rb, 'r')):
                k = cuts.get((row, bi), n)
                off = 0 if bi in (0, 1) else (n - k) * 3
                if (row, bi) == (25, 1):
                    off = 3
                z.racks(c0 + off, row, k, ch)
            z.floor(c0, ra + 1, 12, rb - ra - 1, '1')
            z.floor(c0, rb + 1, 12, 2, '2')
            z.floor(c0, ra - 2, 12, 2, '2')
    # the spine: columns, a walkway line, carts, boxes, an open floor tile and PDUs
    for r in (6, 15, 26):
        z.put(32, r, 'O')
        z.put(41, r, 'O')
    z.floor(36, 1, 2, 33, '0')
    z.block(33, 11, 2, 1, 'Q')
    z.block(39, 22, 2, 1, 'Q')
    z.put(39, 11, 'k')
    z.put(34, 21, 'x')
    z.put(34, 22, 'x')
    z.put(38, 30, 'o')
    z.put(18, 12, 'z')
    z.put(56, 23, 'k')
    z.put(3, 15, 'x')
    z.put(70, 21, 'z')
    z.put(19, 31, 'x')
    z.put(55, 31, 'o')
    # ---- lobby: storage room (west), NOC (east) behind glass with a glass door, the entry plaza
    z.wall(12, 36, 2, 13)
    z.door(12, 41, 'D', vertical=True)
    z.block(2, 36, 2, 1, 'g')
    z.block(6, 36, 3, 1, 'W')
    z.block(1, 42, 1, 2, 'j')
    for (c, r) in ((3, 40), (4, 40), (8, 44), (9, 44), (3, 46), (7, 47)):
        z.put(c, r, 'x')
    z.put(10, 39, 'z')
    z.put(6, 42, 'k')
    z.secure(1, 36, 11, 13)
    # NOC: glass front on column 46 with a glass door and an open doorway, desks facing the east video wall
    for r in range(36, 49):
        if r not in (37, 38, 39):
            z.put(46, r, 'q')
    z.door(46, 43, 'd', vertical=True)
    for c in (51, 57, 63):
        z.block(c, 38, 2, 4, 'N')
        z.block(c, 43, 2, 4, 'N')
    z.put(69, 47, 'k')
    z.put(48, 47, 'x')
    z.floor(47, 36, 26, 13, '7')
    z.art([(73, r) for r in range(38, 47)], 'v')
    z.art([(c, 35) for c in (60, 61, 62)], 'n')
    # entry plaza: columns, walkway, a tank pair on the storage wall, carts
    z.floor(36, 36, 2, 12, '0')
    z.f.rect(35, 37, 4, 4, 'm')
    for (c, r) in ((29, 38), (44, 38), (29, 44), (44, 44)):
        z.put(c, r, 'O')
    z.block(14, 37, 1, 2, 'T')
    z.put(22, 41, 'k')
    z.put(23, 46, 'x')
    z.put(41, 40, 'z')
    z.put(18, 44, 'o')
    # ---- wall art
    z.art([(0, r) for r in (8, 15, 22, 29)] + [(73, r) for r in (8, 15, 22, 29)] + [(c, 0) for c in (10, 26, 47, 63)], 'i')
    z.art([(c, 0) for c in (33, 39)], 's')
    z.art([(c, 35) for c in (8, 26, 45)], 's')
    z.art([(0, 2), (73, 2), (15, 49)], 'p')
    z.art([(30, 49), (43, 49)], '!')
    z.art([(c, 0) for c in (18, 55)], '|')
    # ---- spawns, pickups
    for (c, r) in ((3, 2), (20, 2), (53, 2), (70, 2), (3, 12), (70, 12), (18, 21), (55, 21), (3, 23), (70, 23), (25, 32), (48, 32)):
        z.put(c, r, 'S')
    for (c, r) in ((33, 27), (40, 9), (24, 42)):
        z.put(c, r, 'a')
    for (c, r) in ((40, 27), (33, 9), (50, 47)):
        z.put(c, r, 'h')
    # ---- ceiling: trays over every rack row, ladders over hot aisles, LED strips over cold aisles and the spine
    for r in range(1, 34):
        for c in range(1, 73):
            ch = z.at(c, r)
            if ch in 'Rr':
                z.ceil(c, r, 1, 1, '-')
    for (ra, rb) in pairs:
        z.ceil(5, rb + 2, 63, 1, '=')
        z.ceil(5, ra + 2, 63, 1, '_')
    z.ceil(33, 1, 1, 33, '_')
    z.ceil(40, 1, 1, 33, '_')
    z.ceil(2, 2, 70, 1, '+')
    z.ceil(2, 20, 70, 1, ':')
    z.ceil(2, 31, 70, 1, '_')
    z.ceil(3, 1, 1, 33, '_')
    z.ceil(70, 1, 1, 33, '_')
    z.ceil(2, 39, 9, 1, '_')
    z.ceil(2, 45, 9, 1, '_')
    z.ceil(15, 39, 30, 1, '_')
    z.ceil(15, 45, 30, 1, '_')
    z.ceil(48, 37, 24, 1, '_')
    z.ceil(48, 47, 24, 1, '_')
    for (c, r) in ((10, 3), (30, 3), (44, 3), (64, 3), (12, 32), (60, 32), (24, 40), (50, 40), (6, 46)):
        z.ceil(c, r, 1, 1, ';', over='._')
    return z


# ================================================================ zone 2: Data Hall B2 + the secure core
def zone2():
    H = 54
    z = DZone('datacenter_2', H)
    # north band: CRACs on the north wall
    for c in (6, 18, 44, 50):
        z.block(c, 1, 3, 1, 'C')
    # ---- west wing: north-south rack rows (fronts east / west), a cross aisle at rows 20-23
    for (ca, cb_) in ((4, 8), (12, 16), (20, 24)):
        for r0 in (6, 24):
            n = 4 if not (ca == 12 and r0 == 24) else 3
            z.racks(ca, r0, n, ']', vertical=True)
            z.racks(cb_, r0 + (3 if ca == 20 and r0 == 6 else 0), n - (1 if ca == 20 and r0 == 6 else 0), '[', vertical=True)
        z.floor(ca + 1, 6, 3, 30, '1')
        z.floor(cb_ + 1, 6, 2, 30, '2')
    z.floor(1, 6, 3, 30, '2')
    z.put(14, 21, 'k')
    z.put(6, 22, 'x')
    z.put(22, 21, 'o')
    # ---- the UPS / battery room (south-west), behind the UPS door
    z.wall(1, 38, 22, 2)
    z.wall(21, 40, 2, 13)
    z.door(21, 44, 'u', vertical=True)
    for r in (42, 46):
        z.racks(4, r, 3, 'B')
    z.block(1, 41, 1, 3, 'U')
    z.block(1, 47, 1, 3, 'U')
    z.block(14, 52, 3, 1, 'U')
    z.block(18, 40, 2, 1, 'g')
    z.block(3, 52, 2, 1, 'j')
    z.secure(1, 40, 20, 13)
    # ---- the secure core: a cage ring round the quantum core, cage gates south / north / west / east
    c0, c1, r0, r1 = 26, 47, 11, 34
    for c in range(c0, c1 + 1):
        z.put(c, r0, 'w')
        z.put(c, r1, 'w')
    for r in range(r0 + 1, r1):
        z.put(c0, r, 'w')
        z.put(c1, r, 'w')
    z.door(35, r1, 'c')
    z.door(35, r0, 'c')
    z.door(c0, 21, 'c', vertical=True)
    z.door(c1, 25, 'c', vertical=True)
    z.block(35, 21, 4, 4, 'K')
    # inside: two colocation cages against the ring's north corners (rack rows round a cold aisle, a gear locker each)
    for (line, x0, x1, gate, lock, rk) in ((34, 27, 32, 30, 32, 27), (39, 41, 46, 41, 40, 44)):
        for r in range(r0 + 1, 20):
            z.put(line, r, 'w')
        for c in range(min(line, x0), max(line, x1) + 1):
            if z.at(c, 19) == '.':
                z.put(c, 19, 'w')
        z.door(gate, 19, 'c')
        z.racks(rk, 12, 1, 'R')
        z.racks(x0, 16, 2, 'r')
        z.block(lock, 12, 2, 1, 'g')
        z.floor(x0, 13, 6, 3, '1')
    for (c, r) in ((29, 27), (44, 27), (29, 31), (44, 31)):
        z.put(c, r, 'O')
    z.racks(30, 28, 1, ']', vertical=True)
    z.racks(43, 28, 1, '[', vertical=True)
    z.put(33, 31, 'k')
    z.floor(36, 25, 2, 9, '0')
    z.floor(36, 12, 2, 1, '0')
    # ---- east wing: the vault (north-east), the meeting room (east), a corridor down the west of them
    z.wall(56, 1, 2, 17)
    z.wall(58, 16, 15, 2)
    z.door(56, 7, 'V', vertical=True)
    for r in (2, 6, 10):
        z.block(72, r, 1, 3, 'W')
    z.block(61, 1, 3, 1, 'W')
    z.block(66, 1, 2, 1, 'g')
    for (c, r) in ((62, 9), (63, 9), (65, 12), (60, 5)):
        z.put(c, r, 'x')
    z.secure(58, 1, 15, 15)
    # meeting room: glass on its west side (column 57) with a glass door, walls north / south
    z.wall(56, 22, 17, 2)
    z.wall(56, 36, 17, 2)
    for r in range(24, 36):
        z.put(57, r, 'q')
    z.door(57, 28, 'd', vertical=True)
    z.block(64, 27, 4, 2, 'M')
    z.block(64, 31, 4, 2, 'M')
    z.block(72, 25, 1, 2, 'j')
    z.floor(58, 24, 15, 12, '6')
    # east corridor and the hall north-east: racks along the vault's south side
    z.racks(59, 19, 4, 'R')
    z.floor(59, 20, 12, 2, '1')
    for r in (40, 44):
        z.racks(52, r, 6, 'R' if r == 40 else 'r')
    z.floor(52, 41, 18, 3, '1')
    z.block(72, 47, 1, 3, 'C')
    z.put(52, 30, 'z')
    z.put(52, 9, 'k')
    # ---- south lobby
    for (c, r) in ((30, 44), (43, 44), (30, 49), (43, 49)):
        z.put(c, r, 'O')
    z.floor(36, 35, 2, 16, '0')
    z.put(26, 47, 'x')
    z.put(47, 47, 'o')
    z.block(24, 51, 2, 1, 'Q')
    # ---- wall art
    z.art([(c, 0) for c in (12, 26, 46, 68)] + [(0, r) for r in (10, 30)] + [(73, r) for r in (40, 50)], 'i')
    z.art([(c, 0) for c in (33, 39)], 'I')
    z.art([(c, 53) for c in (30, 42)], '!')
    z.art([(c, 38) for c in (6, 14)], '^')
    z.art([(0, 45), (22, 49)], '&')
    z.art([(73, 8), (73, 13)], '?')
    z.art([(57, 4), (57, 12)], '^')
    z.art([(0, 2), (73, 20)], 'p')
    # ---- spawns, pickups
    for (c, r) in ((2, 3), (24, 3), (50, 3), (70, 3), (2, 21), (24, 21), (50, 20), (25, 37), (49, 34), (60, 47), (71, 44), (14, 36)):
        z.put(c, r, 'S')
    for (c, r) in ((31, 24), (54, 33), (10, 51)):
        z.put(c, r, 'a')
    for (c, r) in ((42, 24), (19, 22), (66, 34)):
        z.put(c, r, 'h')
    # ---- ceiling
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if z.at(c, r) in 'Rr][':
                z.ceil(c, r, 1, 1, '-')
    for c in (6, 14, 22):
        z.ceil(c, 6, 1, 30, '_')
    for c in (10, 18):
        z.ceil(c, 6, 1, 30, '=')
    z.ceil(2, 3, 52, 1, '+')
    z.ceil(2, 21, 23, 1, ':')
    z.ceil(28, 22, 1, 12, '_')
    z.ceil(45, 22, 1, 12, '_')
    z.ceil(30, 20, 14, 1, '_')
    z.ceil(30, 26, 14, 1, '_')
    z.ceil(48, 2, 1, 50, '_')
    z.ceil(26, 37, 22, 1, '_')
    z.ceil(26, 46, 22, 1, '_')
    z.ceil(52, 42, 18, 1, '_')
    z.ceil(59, 4, 12, 1, '_')
    z.ceil(59, 11, 12, 1, '_')
    z.ceil(3, 44, 17, 1, '_')
    z.ceil(3, 48, 17, 1, '_')
    z.ceil(60, 26, 12, 1, '{')
    z.ceil(60, 33, 12, 1, '{')
    for (c, r) in ((12, 2), (40, 2), (64, 8), (30, 40), (44, 40), (10, 45), (66, 30)):
        z.ceil(c, r, 1, 1, ';', over='._{')
    return z


# ================================================================ zone 3: the R&D wing
def zone3():
    H = 54
    z = DZone('datacenter_3', H)
    # the Forge frames the exit (an apron of 3 rows in front of the gate)
    z.block(33, 4, 8, 4, 'L')
    # ---- assembly bay (west): four gantries, cobots, parts shelves, benches
    for (c, r, ch) in ((3, 6, 'A'), (11, 6, 'Y'), (3, 16, 'Y'), (11, 16, 'A')):
        z.block(c, r, 4, 4, ch)
    for (c, r) in ((8, 8), (16, 12), (8, 18), (16, 22)):
        z.put(c, r, 'e')
    for r in (5, 9, 13, 17, 21):
        z.block(1, r, 1, 2, 'y')
    z.block(19, 6, 2, 1, 'b')
    z.block(19, 20, 2, 1, 'b')
    z.floor(9, 5, 1, 21, '5')
    # ---- design floor (centre): holo tables round the HELIXA emblem, fabricators, benches
    for (c, r) in ((27, 13), (44, 13), (27, 23), (44, 23)):
        z.block(c, r, 3, 2, 'H')
    z.block(26, 18, 2, 2, 'f')
    z.block(46, 18, 2, 2, 'f')
    z.block(31, 28, 2, 1, 'b')
    z.block(41, 28, 2, 1, 'b')
    z.put(36, 28, 'k')
    z.floor(35, 18, 4, 4, '3')
    z.f.block(35, 18, 4, 4, 'm', over='3')
    for (c, r) in ((31, 14), (41, 14), (31, 24), (41, 24)):
        z.block(c, r, 2, 1, 'b')
    for (c, r) in ((34, 15), (39, 15), (34, 24), (39, 24)):
        z.put(c, r, 'e')
    z.floor(24, 11, 26, 1, '4')
    z.floor(24, 31, 26, 1, '4')
    z.floor(24, 12, 1, 19, '5')
    z.floor(49, 12, 1, 19, '5')
    z.block(72, 12, 1, 2, 'y')
    z.block(57, 14, 2, 1, 'b')
    z.block(63, 14, 2, 1, 'b')
    # ---- energy test chamber (north-east), cable drums, a cobot
    z.block(58, 5, 6, 6, 'X')
    z.put(55, 6, 'z')
    z.put(66, 9, 'e')
    z.floor(56, 3, 10, 1, '4')
    z.floor(56, 12, 10, 1, '4')
    # ---- weapons lab (east): 2-thick walls, a security door, four prototypes in containment fields, lockers
    z.wall(53, 17, 20, 2)
    z.wall(53, 19, 2, 17)
    z.wall(53, 36, 20, 2)
    z.door(53, 25, 'D', vertical=True)
    for (c, r) in ((58, 21), (64, 21), (58, 30), (64, 30)):
        z.block(c, r, 2, 2, 'F')
    z.block(72, 21, 1, 3, 'W')
    z.block(72, 30, 1, 2, 'g')
    z.block(68, 19, 3, 1, 'W')
    z.block(56, 35, 2, 1, 'j')
    z.secure(55, 19, 18, 17)
    # ---- cryo bay (south-west): glass front with a lab glass door, cryo cylinders along the walls
    z.wall(1, 33, 21, 2)
    for r in range(35, 46):
        z.put(20, r, 'q')
    z.wall(1, 46, 21, 2)
    z.door(20, 39, 'l', vertical=True)
    for c in range(3, 19, 2):
        z.put(c, 35, 'Z')
        z.put(c, 45, 'Z')
    z.block(1, 39, 1, 2, 'y')
    z.block(9, 40, 2, 1, 'b')
    # ---- lab south: fabricators and benches near the entry, columns
    for (c, r) in ((28, 38), (45, 38), (28, 44), (45, 44)):
        z.put(c, r, 'O')
    z.block(24, 41, 2, 2, 'f')
    z.block(48, 41, 2, 2, 'f')
    z.block(23, 48, 2, 1, 'b')
    z.block(49, 48, 2, 1, 'b')
    z.put(56, 44, 'k')
    z.put(57, 40, 'x')
    # prototype store (south-east): a cage against the east wall with a cage gate, gear lockers and crates inside
    for c in range(60, 73):
        z.put(c, 39, 'w')
        z.put(c, 49, 'w')
    for r in range(40, 49):
        z.put(60, r, 'w')
    z.door(60, 43, 'c', vertical=True)
    z.block(72, 41, 1, 2, 'g')
    z.block(72, 46, 1, 2, 'g')
    for (c, r) in ((63, 41), (64, 41), (63, 47), (67, 44), (68, 44)):
        z.put(c, r, 'x')
    z.put(65, 44, 'e')
    z.secure(61, 40, 12, 9)
    # the west lab: a fabricator, benches, parts shelves; the south: cobots and benches round the walkway
    z.block(4, 27, 2, 2, 'f')
    z.block(12, 29, 2, 1, 'b')
    z.block(1, 27, 1, 2, 'y')
    z.block(30, 35, 2, 1, 'b')
    z.block(42, 35, 2, 1, 'b')
    z.put(33, 41, 'e')
    z.put(40, 41, 'e')
    z.block(3, 49, 2, 1, 'b')
    z.block(14, 49, 2, 2, 'f')
    z.floor(36, 32, 2, 19, '5')
    # ---- wall art
    z.art([(c, 0) for c in (12, 24, 49, 62)], 't')
    z.art([(c, 0) for c in (30, 43)], '%')
    z.art([(c, 0) for c in (33, 39)], '@')
    z.art([(0, r) for r in (26, 30)] + [(73, r) for r in (8, 14, 42, 48)], 'J')
    z.art([(c, 53) for c in (28, 44)], '%')
    z.art([(c, 17) for c in (60, 66)], 't')
    z.art([(c, 36) for c in (60, 66)], '^')
    z.art([(c, 33) for c in (6, 14)], 't')
    z.art([(c, 47) for c in (6, 14)], '%')
    # ---- spawns, pickups
    for (c, r) in ((2, 2), (22, 2), (50, 2), (70, 2), (22, 14), (51, 14), (23, 27), (50, 27), (70, 14), (6, 31), (57, 50), (68, 51)):
        z.put(c, r, 'S')
    for (c, r) in ((36, 16), (20, 30), (52, 46)):
        z.put(c, r, 'a')
    for (c, r) in ((36, 25), (51, 22), (10, 50)):
        z.put(c, r, 'h')
    z.floor(1, 1, 72, 52, '3')   # white epoxy everywhere else
    # ---- ceiling: lab light panels on a 4 m grid, LED strips over the walkways, a cable ladder to the chamber
    for r in range(3, H - 2, 4):
        for c in range(3, W - 2, 4):
            if z.at(c, r) in '.SahP':
                z.ceil(c, r, 1, 1, '{')
    z.ceil(23, 2, 1, 30, '_')
    z.ceil(50, 2, 1, 30, '_')
    z.ceil(42, 3, 14, 1, '=')
    z.ceil(56, 23, 15, 1, '_')
    z.ceil(56, 32, 15, 1, '_')
    for (c, r) in ((14, 3), (60, 3), (30, 34), (44, 34), (10, 37)):
        z.ceil(c, r, 1, 1, ';', over='._{')
    return z


def main():
    zones = []
    for fn, size in ((zone1, ((74, 74), (50, 50))), (zone2, ((74, 74), (54, 54))), (zone3, ((74, 74), (54, 54)))):
        z = fn()
        errs, stats = check(z, size)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
