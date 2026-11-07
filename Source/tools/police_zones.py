#!/usr/bin/env python3
"""INKBOLT Strike Team HQ zones (theme 'police'): hand-placed layouts -> src/data/zones/police_*.txt

    python3 tools/police_zones.py            # write + validate
    python3 tools/police_zones.py --print    # ... and print the maps
    python3 tools/police_zones.py --check    # validate only

Every zone file has three grids: the floor plan, then "@layer 0.008" (floor finishes, plus wall-art codes on the wall
cells, read by the theme's wall chooser) and "@layer 4" (ceiling structure and lights, hanging from the 4 m ceiling).
Interior walls are two cells thick, so every wall module has one room face (its style follows the floor in front).

Floor plan (src/data/themes/police.js):
  R weapon wall [3,1]   b workbench [2,1]   g gear shelf [2,1]   l locker   f filing cabinet   k sandbags (runs)
  x crate / ammo cans   K desk pod [2,2]    T briefing row [4,2]  U lectern  p plant   B waiting bench [2,1]
  o vending / water cooler   H gear stand   z tool chest   t drums / tyres   X pallet [2,2]   D ops console [4,1]
  Q front desk [6,2]    V SWAT van [3,6]    J holding cell [4,3]  y range booth [3,2]   Y target
Floor layer: 1 lobby tile  2 carpet  3 armory rubber  4 garage concrete  5 range floor  6 pale tile  7 entry mat
  / hazard stripes  ^ range firing line  , range lane line  - | garage line (along X / Z)  _ : armory line (X / Z)
  M floor emblem [4,4]
  wall-art codes on wall cells: w window  v projector screen  F flag  W whiteboard  m map board  n notice board
  e badge plaque  c clock  u door  s sign  C cage window  A first-aid  Z extinguisher  r roller door  O tool board
  I panel / warning light  L bullet backstop   (art codes never reuse a symbol: the layer would build it)
Ceiling layer: i panel light  j high-bay lamp  = ! + beam along X / Z / crossing  ~ ; duct along X / Z
  { } cable tray (along X / Z)  $ target carrier rail (along Z)  [ ] doorway lintel (wall along X / Z)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, validate, OUT  # noqa: E402

W, H = 48, 48
WALK = set()
WALK = set()
PREFAB = {'R': (3, 1), 'b': (2, 1), 'g': (2, 1), 'K': (2, 2), 'T': (4, 2), 'B': (2, 1), 'X': (2, 2), 'D': (4, 1),
          'Q': (6, 2), 'V': (3, 6), 'J': (4, 3), 'y': (3, 2)}
FLOORS = '1234567'


class PZone(Zone):
    """floor plan + floor layer (f) + ceiling layer (k)"""

    def __init__(self, name):
        Zone.__init__(self, name, W, H)
        self.f = Zone(name + '_f', W, H)
        self.k = Zone(name + '_k', W, H)
        self.rect(0, 0, W, 1, '#')
        self.rect(0, H - 1, W, 1, '#')
        self.rect(0, 0, 1, H, '#')
        self.rect(W - 1, 0, 1, H, '#')
        self.rect(23, 0, 3, 1, 'G')
        self.rect(23, H - 1, 3, 1, 'E')
        self.put(24, H - 3, 'P')

    def wall(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '#')

    def floor(self, c0, r0, w, h, ch):
        """floor finish over the open cells of a rectangle (wall cells keep their art code)"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) not in '#GE':
                    self.f.g[r][c] = ch

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell')
            self.f.g[r][c] = ch

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
        """a lamp per (col, row) unless the cell is a wall or already holds ceiling structure"""
        for r in rows:
            for c in cols:
                if self.at(c, r) not in '#GE' and self.k.g[r][c] in keep:
                    self.k.g[r][c] = ch

    def text(self):
        out = Zone.text(self)
        out += '@layer 0.008\n' + Zone.text(self.f)
        out += '@layer 4\n' + Zone.text(self.k)
        return out


def border(z, c0, r0, w, h, base, ch):
    """a band of `ch` over the `base` floor cells that touch a wall (room edges, round pillars)"""
    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            if z.f.g[r][c] == base and any(z.at(c + dc, r + dr) == '#' for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                z.f.g[r][c] = ch


def joints(z, c0, r0, w, h, base='4'):
    """concrete slab joints every 4 m: '0' west edge, '9' south edge, '%' both"""
    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            if z.f.g[r][c] != base:
                continue
            a, b = c % 4 == 0, r % 4 == 3
            if a or b:
                z.f.g[r][c] = '%' if a and b else '0' if a else '9'


def lintel(z, c0, r0, w, h, ch):
    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            assert z.at(c, r) not in '#', (z.name, 'lintel over a wall', c, r)
            z.k.g[r][c] = ch


# ====================================================================== zone 1: lobby, briefing room, armory
def zone1():
    z = PZone('police_1')
    # two-cell interior walls: lobby | briefing + armory (doors 7-10, 21-28), briefing | armory (door rows 10-13)
    z.wall(1, 24, 46, 2)
    z.rect(7, 24, 4, 2, '.')
    z.rect(21, 24, 8, 2, '.')
    z.wall(16, 1, 2, 23)
    z.rect(16, 10, 2, 4, '.')
    # lobby pillars
    for c, r in ((11, 31), (35, 31), (11, 39), (35, 39)):
        z.wall(c, r, 2, 2)

    # --- briefing room (cols 1-15, rows 1-23): screen on the north wall, four rows of seats, lectern
    for r in (6, 10, 14, 18):
        z.block(2, r, 4, 2, 'T')
        z.block(9, r, 4, 2, 'T')
    z.put(7, 3, 'U')
    z.puts([(1, 21), (1, 22), (1, 23)], 'f')
    z.puts([(15, 1), (1, 1), (15, 23)], 'p')
    z.puts([(4, 3), (12, 3), (3, 22), (12, 22)], 'S')
    z.floor(1, 1, 15, 23, '2')
    z.art([(c, 0) for c in range(5, 11)], 'v')
    z.art([(2, 0), (13, 0)], 'F')
    z.art([(0, 5), (0, 6), (0, 7)], 'W')
    z.art([(0, 12), (0, 13)], 'm')
    z.art([(0, 16), (0, 17), (0, 18)], 'w')
    z.art([(16, 4), (16, 17)], 'n')
    z.art([(16, 7)], 'c')
    z.art([(3, 24), (13, 24)], 'n')

    # --- armory (cols 18-46, rows 1-23): gun walls north and east, benches, shelves, lockers, gear stands
    for c in (18, 28, 32, 36, 40):
        z.block(c, 1, 3, 1, 'R')
    for r in (4, 8, 12):
        z.block(46, r, 1, 3, 'R')
    z.block(46, 16, 1, 2, 'g')
    z.block(46, 19, 1, 2, 'g')
    z.run(18, 3, 6, 'l', vertical=True)
    for c in (24, 30, 36):
        for r in (8, 15):
            z.block(c, r, 2, 1, 'b')
    z.puts([(21, 5), (21, 8)], 'H')
    z.puts([(19, 21), (20, 22), (19, 22), (44, 22), (43, 22), (44, 21)], 'x')
    z.puts([(22, 12), (42, 5), (33, 19), (27, 20), (41, 12)], 'S')
    z.put(33, 12, 'a')
    z.put(21, 17, 'h')
    z.floor(18, 1, 29, 23, '3')
    z.floor(16, 10, 2, 4, '3')
    z.floor(22, 1, 5, 2, '/')
    for c in range(19, 45):
        if z.f.g[3][c] == '3':
            z.f.g[3][c] = '_'
    for r in range(4, 23):
        z.f.g[r][44] = ':'
    z.art([(31, 0), (35, 0)], 's')
    z.art([(39, 0)], 'Z')
    z.art([(47, 2)], 'A')
    z.art([(30, 24), (31, 24), (32, 24), (33, 24)], 'C')
    z.art([(39, 24)], 'u')
    z.art([(17, 16)], 'A')
    z.art([(17, 19)], 'Z')
    z.art([(47, 15)], 's')

    # --- lobby (cols 1-46, rows 26-46): front desk, floor emblem, waiting benches, records desks, vending
    z.block(21, 29, 6, 2, 'Q')
    for r in (29, 33, 37):
        z.block(3, r, 2, 1, 'B')
    z.puts([(1, 27), (1, 45), (46, 45), (46, 27), (10, 27), (37, 27)], 'p')
    z.puts([(46, 30), (46, 31), (46, 32)], 'o')
    for c in (37, 41):
        for r in (39, 43):
            z.block(c, r, 2, 2, 'K')
    z.puts([(29, 46), (30, 46), (31, 46), (32, 46)], 'f')
    z.puts([(7, 28), (40, 30), (44, 36), (6, 43), (8, 36)], 'S')
    z.put(16, 41, 'a')
    z.put(31, 41, 'h')
    z.floor(1, 26, 46, 21, '1')
    border(z, 1, 26, 46, 21, '1', '8')
    z.floor(7, 24, 4, 2, '1')
    z.floor(21, 24, 8, 2, '1')
    z.floor(22, 34, 4, 4, 'M')
    z.floor(22, 44, 5, 3, '7')
    z.art([(3, 25), (42, 25)], 'n')
    z.art([(15, 25), (33, 25)], 'e')
    z.art([(19, 25), (30, 25)], 'F')
    z.art([(0, 29), (0, 30), (0, 38), (0, 39), (0, 40)], 'w')
    z.art([(0, 34)], 'n')
    z.art([(47, 36), (47, 37), (47, 40), (47, 41), (47, 42)], 'w')
    z.art([(8, 47), (39, 47)], 'u')
    z.art([(3, 47), (4, 47), (14, 47), (34, 47), (43, 47), (44, 47)], 'w')
    z.art([(18, 47), (36, 47)], 'e')
    z.art([(17, 25)], 'c')
    z.art([(12, 25), (37, 25), (0, 36)], 'd')

    # --- ceiling
    lintel(z, 7, 24, 4, 2, '[')
    lintel(z, 21, 24, 8, 2, '[')
    lintel(z, 16, 10, 2, 4, ']')
    z.beams_x((28, 33, 38, 43), 1, 46)
    z.lights('i', range(4, 46, 4), (30, 35, 40, 45))
    z.lights('i', (4, 8, 12), (4, 8, 12, 16, 20))
    z.ceil(2, 2, 1, 21, ';')
    z.beams_z((22, 27, 32, 37, 42), 1, 23)
    z.lights('j', (19, 24, 29, 34, 39, 44), (6, 12, 18))
    z.ceil(45, 1, 1, 23, '}')
    z.ceil(1, 27, 46, 1, '{')
    return z


# ====================================================================== zone 2: locker room, gear store, ops room
def zone2():
    z = PZone('police_2')
    z.wall(1, 22, 46, 2)
    z.rect(5, 22, 4, 2, '.')
    z.rect(21, 22, 8, 2, '.')
    z.rect(39, 22, 4, 2, '.')
    z.wall(18, 1, 2, 21)
    z.rect(18, 8, 2, 4, '.')

    # --- locker room (cols 1-17, rows 1-21)
    z.run(2, 1, 14, 'l')
    z.run(1, 3, 17, 'l', vertical=True)
    z.run(5, 9, 9, 'l')
    z.run(5, 10, 9, 'l')
    for c in (6, 10):
        for r in (5, 15):
            z.block(c, r, 2, 1, 'B')
    z.puts([(16, 3), (13, 19), (4, 19)], 'S')
    z.put(16, 20, 'p')
    z.put(9, 13, 'h')
    z.floor(1, 1, 17, 21, '6')
    z.floor(18, 8, 2, 4, '3')
    z.art([(18, 4), (18, 16)], 'n')
    z.art([(18, 13)], 'c')
    z.art([(3, 22), (13, 22)], 'n')
    z.art([(10, 22)], 's')

    # --- gear store (cols 20-46, rows 1-21): gun walls, shelving aisles, a sandbag drill position
    for c in (28, 32, 36, 40):
        z.block(c, 1, 3, 1, 'R')
    for r in (3, 7, 11, 15):
        z.block(46, r, 1, 3, 'R')
    for c in (29, 35):
        z.block(c, 6, 2, 1, 'g')
        z.block(c, 11, 2, 1, 'g')
    z.block(20, 3, 1, 2, 'g')
    z.block(20, 14, 1, 2, 'g')
    z.run(23, 16, 4, 'k')
    z.run(23, 17, 2, 'k', vertical=True)
    z.block(31, 16, 2, 1, 'b')
    z.block(37, 16, 2, 1, 'b')
    z.puts([(21, 2), (27, 3)], 'H')
    z.puts([(43, 20), (44, 20), (44, 19), (21, 20), (22, 20)], 'x')
    z.puts([(23, 9), (33, 9), (42, 9), (40, 19), (27, 19)], 'S')
    z.put(39, 13, 'a')
    z.floor(20, 1, 27, 21, '3')
    z.floor(22, 1, 5, 2, '/')
    for c in range(28, 45):
        if z.f.g[3][c] == '3':
            z.f.g[3][c] = '_'
    for r in range(4, 21):
        z.f.g[r][44] = ':'
    z.art([(31, 0), (39, 0)], 's')
    z.art([(35, 0)], 'Z')
    z.art([(47, 19)], 'A')
    z.art([(30, 22), (31, 22), (32, 22), (33, 22)], 'C')
    z.art([(19, 17)], 'Z')

    # --- operations room (cols 1-46, rows 24-46): console walls, desk pods, situation table, cabinets
    for c in (10, 14, 32, 36):
        z.block(c, 24, 4, 1, 'D')
    for c in (4, 8, 38, 42):
        for r in (29, 34, 39):
            z.block(c, r, 2, 2, 'K')
    z.block(22, 34, 4, 2, 'T')
    z.puts([(2, 46), (3, 46), (4, 46), (43, 46), (44, 46), (45, 46)], 'f')
    z.puts([(1, 24), (46, 24), (5, 46), (42, 46), (19, 46), (29, 46)], 'p')
    z.puts([(46, 30), (46, 31)], 'o')
    z.puts([(16, 28), (31, 29), (12, 36), (36, 36), (3, 26), (45, 37)], 'S')
    z.put(24, 30, 'a')
    z.put(12, 44, 'h')
    z.floor(1, 24, 46, 23, '2')
    z.floor(5, 22, 4, 2, '6')
    z.floor(21, 22, 8, 2, '2')
    z.floor(39, 22, 4, 2, '2')
    z.floor(22, 44, 5, 3, '7')
    z.art([(0, c) for c in (28, 29, 33, 34, 38, 39, 43)], 'w')
    z.art([(47, c) for c in (35, 36, 40, 41)], 'w')
    z.art([(47, 27)], 'm')
    z.art([(0, 31), (47, 33)], 'd')
    z.art([(0, 25)], 'c')
    z.art([(c, 47) for c in (8, 9, 37, 38)], 'W')
    z.art([(14, 47), (33, 47)], 'F')
    z.art([(18, 47), (30, 47)], 'm')

    # --- ceiling
    lintel(z, 5, 22, 4, 2, '[')
    lintel(z, 21, 22, 8, 2, '[')
    lintel(z, 39, 22, 4, 2, '[')
    lintel(z, 18, 8, 2, 4, ']')
    z.lights('i', (4, 9, 14), (4, 8, 12, 16, 20))
    z.ceil(8, 3, 1, 18, ';')
    z.beams_z((24, 29, 34, 39, 44), 1, 21)
    z.lights('j', (22, 27, 32, 37, 42), (5, 10, 15, 20))
    z.beams_x((27, 32, 37, 42), 1, 46)
    z.lights('i', (4, 9, 14, 19, 24, 29, 34, 39, 44), (29, 34, 39, 44))
    z.ceil(1, 25, 46, 1, '~')
    z.ceil(45, 1, 1, 21, '}')
    z.ceil(2, 2, 1, 20, '}')
    return z


# ====================================================================== zone 3: firing range, vehicle garage, cells
def zone3():
    z = PZone('police_3')
    z.wall(1, 16, 46, 2)
    z.rect(3, 16, 4, 2, '.')
    z.rect(21, 16, 6, 2, '.')
    z.rect(41, 16, 4, 2, '.')

    # --- firing range (cols 1-46, rows 1-15): targets downrange, a line of booths, an aisle through the middle
    z.block(2, 10, 18, 2, 'y')
    z.block(28, 10, 18, 2, 'y')
    for c in list(range(3, 20, 3)) + list(range(29, 46, 3)):
        z.put(c, 4, 'Y')
    z.puts([(6, 7), (16, 2), (34, 2), (41, 7), (11, 13), (37, 13)], 'S')
    z.put(24, 13, 'h')
    z.floor(1, 1, 46, 15, '5')
    for c in list(range(2, 21, 3)) + list(range(28, 47, 3)):
        for r in range(1, 10):
            if z.f.g[r][c] == '5':
                z.f.g[r][c] = ','
    for c in range(1, 47):
        z.f.g[9][c] = '^'
    z.floor(22, 1, 5, 2, '/')
    z.floor(3, 16, 4, 2, '5')
    z.floor(21, 16, 6, 2, '5')
    z.floor(41, 16, 4, 2, '5')
    z.art([(c, 0) for c in list(range(1, 21)) + list(range(28, 47))], 'L')
    z.art([(16, 16), (17, 16), (18, 16), (29, 16), (30, 16), (31, 16)], 'w')
    z.art([(9, 16), (38, 16)], 's')
    z.art([(14, 16), (33, 16)], 'I')
    z.art([(0, 12), (47, 12)], 'I')

    # --- garage (cols 1-46, rows 18-46): parking bays with vans, holding cells, roller doors, tool corner
    for c in (6, 12, 34, 40):
        z.block(c, 20, 3, 6, 'V')
    z.block(1, 31, 3, 12, 'J')
    for r in (21, 25):
        z.block(46, r, 1, 3, 'R')
    z.puts([(46, 29), (46, 42), (46, 43)], 'z')
    z.puts([(44, 30), (44, 33), (44, 37), (44, 40)] + [(c, 28) for c in (4, 10, 16, 32, 38, 44)], 'q')
    z.puts([(19, 24), (30, 25), (40, 44)], 'N')
    z.puts([(45, 45), (46, 45), (46, 44), (1, 45), (2, 45), (9, 45)], 't')
    z.run(17, 33, 3, 'k')
    z.run(28, 33, 3, 'k')
    z.run(12, 39, 3, 'k')
    z.run(33, 39, 3, 'k')
    z.block(10, 43, 2, 2, 'X')
    z.block(36, 43, 2, 2, 'X')
    z.puts([(22, 38), (25, 37), (20, 29), (27, 29)], 'x')
    z.block(14, 45, 2, 1, 'b')
    z.block(31, 46, 2, 1, 'g')
    z.puts([(20, 21), (28, 21), (11, 30), (38, 30), (14, 33), (34, 33)], 'S')
    z.put(24, 25, 'a')
    z.put(41, 46, 'a')
    z.put(6, 37, 'h')
    z.floor(1, 18, 46, 29, '4')
    joints(z, 1, 18, 46, 29)
    for c in (4, 10, 16, 32, 38, 44):
        for r in range(19, 27):
            z.f.g[r][c] = '|'
    for c in list(range(4, 17)) + list(range(32, 45)):
        z.f.g[27][c] = '-'
    z.floor(1, 29, 7, 15, '6')
    z.floor(45, 30, 2, 4, '/')
    z.floor(45, 37, 2, 4, '/')
    z.floor(22, 44, 5, 3, '7')
    z.art([(47, r) for r in range(30, 34)] + [(47, r) for r in range(37, 41)], 'r')
    z.art([(c, 47) for c in (14, 15, 16)], 'O')
    z.art([(12, 17), (35, 17)], 'n')
    z.art([(30, 47), (19, 47)], 'Z')
    z.art([(0, 23), (0, 24)], 'I')
    z.art([(0, 20)], 's')
    z.art([(0, 28)], 's')
    z.art([(47, 35)], 'I')
    z.art([(8, 47), (40, 47)], 'w')

    # --- ceiling
    lintel(z, 3, 16, 4, 2, '[')
    lintel(z, 21, 16, 6, 2, '[')
    lintel(z, 41, 16, 4, 2, '[')
    for c in list(range(3, 20, 3)) + list(range(29, 46, 3)):    # target carrier rails over each lane
        z.ceil(c, 2, 1, 10, '$')
    z.lights('i', [c for c in range(4, 46, 3) if 21 > c or c > 27] + [24], (6, 13))
    z.ceil(1, 14, 46, 1, '~')
    z.beams_z((9, 15, 21, 27, 33, 39), 18, 46)
    z.lights('j', (6, 12, 18, 24, 30, 36, 42), (22, 28, 34, 40, 45))
    z.ceil(2, 18, 1, 29, '}')
    z.ceil(45, 18, 1, 29, '}')
    return z


def check_layers(z):
    errs = []
    for r in range(H):
        for c in range(W):
            base, fl, ce = z.g[r][c], z.f.g[r][c], z.k.g[r][c]
            if base not in '#GE' and fl not in FLOORS + '/^,-|_:M809%':
                errs.append('no floor finish at (%d,%d)' % (c, r))
            if base == '#' and ce != '.':
                errs.append('ceiling piece over a wall at (%d,%d)' % (c, r))
            if base == '#' and fl != '.':   # wall art: the cell in front must be clear floor (no rack, locker, cell...)
                fronts = [z.at(c + dc, r + dr) for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)) if z.at(c + dc, r + dr) not in '#GE']
                if len(fronts) != 1 or fronts[0] not in '.Sah':
                    errs.append('wall art %r at (%d,%d) faces %s' % (fl, c, r, fronts))
    return errs


def main():
    zones = [zone1(), zone2(), zone3()]
    ok = True
    for z in zones:
        errs, stats = validate(z, WALK, PREFAB, size=((44, 60), (40, 56)))
        errs += check_layers(z)
        print('%-12s %s' % (z.name, stats))
        for e in errs:
            print('   ERROR', e)
            ok = False
        if '--check' not in sys.argv:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
