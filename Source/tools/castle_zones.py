#!/usr/bin/env python3
"""INKBOLT Castle zones ('Castle Courtyard'): hand-placed layouts -> src/data/zones/castle_*.txt

    python3 tools/castle_zones.py            # write + validate
    python3 tools/castle_zones.py --print    # ... and print the maps
    python3 tools/castle_zones.py --check    # validate only

Three wide wards inside one curtain wall (1 cell thick: the wall modules' backs are the castle's outer face).
Symbols (src/data/themes/castle.js):
  # curtain wall           , cobbles (walk)         ; flagstones (walk)      g grass (walk)
  b barrels  c crates / sacks  y hay bale  f fence (run)  d training dummy  r weapon rack (run)  x archery butt
  i brazier  n banner pole     Y haystack 2x2  M market stall 3x2  K cart 2x3  W well 3x3  O drum tower 5x5
  X stair to the wall walk 2x7 (rises north, parapet east)   V the same, parapet west
  T the keep 12x12            Q trebuchet 4x8 (cocked, arm toward the south)     + built-ins S P E G a h
"""
import sys

from zonekit import Zone, validate, write

WALK = set(',;g')
PREFAB = {'Q': (4, 8), 'Y': (2, 2), 'M': (3, 2), 'K': (2, 3), 'W': (3, 3), 'O': (5, 5), 'X': (2, 7), 'V': (2, 7), 'T': (12, 12)}


def shell(name, w, h, gate, entry):
    z = Zone(name, w, h)
    z.rect(0, 0, w, 1, '#')
    z.rect(0, h - 1, w, 1, '#')
    z.rect(0, 0, 1, h, '#')
    z.rect(w - 1, 0, 1, h, '#')
    z.rect(gate, 0, 3, 1, 'G')
    z.rect(entry, h - 1, 3, 1, 'E')
    return z


def towers(z, spots):
    for (c, r) in spots:
        z.block(c, r, 5, 5, 'O')


# ---------------------------------------------------------------- 1: the market ward
def market():
    z = shell('castle_market', 62, 54, 29, 29)
    towers(z, [(1, 1), (56, 1), (1, 48), (56, 48), (1, 24), (56, 24)])
    z.pave(27, 1, 7, 52, ',')                      # high street, gate to gate
    z.pave(6, 25, 50, 5, ',')                      # cross street
    z.pave(23, 20, 15, 15, ';', over='.,')         # well square
    z.block(29, 26, 3, 3, 'W', over=';')
    z.puts([(24, 21), (36, 21), (24, 33), (36, 33)], 'n', over=';')
    z.puts([(26, 8), (34, 8), (26, 16), (34, 16), (26, 38), (34, 38), (26, 44), (34, 44)], 'i', over='.,')
    # west market: two rows of stalls around an aisle, carts and goods at the ends
    for c in (8, 12, 16, 20):
        z.block(c, 7, 3, 2, 'M')
        z.block(c, 14, 3, 2, 'M')
    z.puts([(7, 7), (11, 8), (23, 7), (7, 15), (19, 14), (23, 15)], 'c')
    z.puts([(15, 7), (11, 15), (23, 8)], 'b')
    z.block(9, 18, 2, 3, 'K')
    z.puts([(12, 19), (13, 19), (12, 20)], 'y')
    z.block(18, 19, 2, 2, 'Y')
    # east market
    for c in (38, 42, 46, 50):
        z.block(c, 7, 3, 2, 'M')
    for c in (38, 50):
        z.block(c, 14, 3, 2, 'M')
    z.block(44, 13, 2, 3, 'K')
    z.puts([(37, 15), (53, 14), (54, 7), (41, 14), (49, 15)], 'c')
    z.puts([(47, 14), (48, 14), (54, 8), (53, 15)], 'b')
    z.block(52, 19, 2, 2, 'Y')
    z.puts([(40, 20), (41, 20), (40, 19)], 'y')
    # stairs up to the wall walk beside the north towers
    z.block(1, 6, 2, 7, 'X')
    z.block(59, 6, 2, 7, 'V')
    # south-west: the hay yard (stacks, bales, a paddock fence, the hay cart)
    for (c, r) in ((7, 34), (7, 39), (11, 36)):
        z.block(c, r, 2, 2, 'Y')
    z.block(17, 35, 2, 3, 'K')
    z.puts([(14, 34), (15, 34), (14, 35), (10, 41), (11, 41), (21, 38)], 'y')
    z.run(14, 41, 9, 'f')
    z.run(14, 44, 4, 'f')
    z.run(19, 44, 4, 'f')
    z.pave(15, 42, 7, 2, 'g')
    z.puts([(6, 45), (7, 45), (6, 44)], 'b')
    z.puts([(24, 47), (21, 47)], 'c')
    # south-east: the cellar stores (barrels, crates, a barrel cart, a stall)
    z.block(42, 34, 2, 3, 'K')
    z.block(48, 40, 3, 2, 'M')
    z.puts([(38, 35), (39, 35), (38, 36), (46, 36), (52, 35), (53, 35), (53, 36), (40, 45), (41, 45)], 'b')
    z.puts([(46, 37), (39, 41), (54, 41), (52, 45), (37, 46)], 'c')
    z.puts([(55, 30), (55, 31)], 'y')
    # spawn cans, pickups, entry
    z.puts([(12, 3), (21, 3), (40, 3), (50, 3), (10, 11), (48, 11), (13, 23), (47, 23), (8, 31), (52, 32), (17, 32), (46, 32)], 'S')
    z.puts([(20, 26), (40, 28)], 'a', over='.,')
    z.puts([(30, 12), (12, 44), (48, 44)], 'h', over='.,')
    z.put(30, 49, 'P', over=',')
    return z


# ---------------------------------------------------------------- 2: the training yard
def yard():
    z = shell('castle_yard', 64, 52, 10, 31)
    towers(z, [(1, 1), (58, 1), (1, 46), (58, 46), (29, 1)])
    z.pave(30, 39, 5, 12, ',')                     # from the entry gate north ...
    z.pave(8, 34, 27, 5, ',')                      # ... west along the drill ground ...
    z.pave(8, 1, 6, 34, ',')                       # ... and north to the exit gate
    z.puts([(14, 30), (14, 22), (14, 14), (7, 30), (7, 22), (7, 14)], 'n')
    # archery range (north-east): butts backed by hay, grass between the butts and the shooting line
    z.pave(37, 6, 20, 11, 'g')
    for c in (39, 44, 49, 54):
        z.put(c, 7, 'x', over='g')
        z.puts([(c - 1, 6), (c, 6), (c + 1, 6)], 'y', over='g')
    z.run(37, 17, 6, 'f')
    z.run(46, 17, 5, 'f')
    z.run(54, 17, 4, 'f')
    z.block(59, 7, 2, 2, 'Y')
    z.puts([(36, 2), (37, 2), (36, 3), (56, 2), (56, 3)], 'b')
    # weapon racks and dummies along the drill line
    z.run(39, 21, 4, 'r')
    z.run(47, 21, 4, 'r')
    z.puts([(44, 24), (52, 24), (36, 24), (40, 27), (48, 27), (56, 27)], 'd')
    # sparring ring 1 (fenced, gaps on every side), dummies inside
    for (c0, r0) in ((17, 10), (39, 31)):
        z.run(c0, r0, 4, 'f')
        z.run(c0 + 7, r0, 4, 'f')
        z.run(c0, r0 + 10, 4, 'f')
        z.run(c0 + 7, r0 + 10, 4, 'f')
        z.run(c0, r0 + 1, 3, 'f', vertical=True)
        z.run(c0, r0 + 7, 3, 'f', vertical=True)
        z.run(c0 + 10, r0 + 1, 3, 'f', vertical=True)
        z.run(c0 + 10, r0 + 7, 3, 'f', vertical=True)
        z.pave(c0 + 1, r0 + 1, 9, 9, 'g')
        z.puts([(c0 + 3, r0 + 3), (c0 + 7, r0 + 3), (c0 + 3, r0 + 7), (c0 + 7, r0 + 7)], 'd', over='g')
        z.puts([(c0 - 1, r0 - 1), (c0 + 11, r0 - 1), (c0 - 1, r0 + 11), (c0 + 11, r0 + 11)], 'i')
    # stairs to the wall walk
    z.block(1, 6, 2, 7, 'X')
    z.block(61, 6, 2, 7, 'V')
    z.block(27, 22, 4, 8, 'Q')                     # the trebuchet on the drill ground
    # stores: hay, barrels, carts, a stall selling to the garrison
    z.block(20, 42, 2, 3, 'K')
    z.block(4, 40, 2, 2, 'Y')
    z.puts([(23, 42), (24, 42), (23, 43), (17, 46), (8, 44), (9, 44)], 'y')
    z.puts([(26, 46), (27, 46), (26, 47), (13, 47), (6, 36), (6, 37)], 'b')
    z.puts([(25, 41), (15, 44), (3, 30)], 'c')
    z.block(52, 41, 2, 3, 'K')
    z.block(44, 46, 3, 2, 'M')
    z.puts([(56, 40), (57, 40), (56, 41), (49, 46), (40, 47), (41, 47)], 'b')
    z.puts([(50, 41), (55, 44), (39, 46)], 'c')
    z.block(18, 27, 2, 2, 'Y')
    z.puts([(24, 25), (25, 25), (24, 26)], 'y')
    z.puts([(28, 18), (29, 18), (28, 19)], 'c')
    # spawn cans, pickups, entry
    z.puts([(20, 4), (40, 12), (50, 12), (32, 9), (22, 15), (4, 25), (36, 29), (58, 21), (45, 36), (24, 31), (11, 41), (58, 35)], 'S', over='.,g')
    z.puts([(11, 26), (49, 24)], 'a', over='.,g')
    z.puts([(22, 21), (54, 35)], 'h', over='.,g')
    z.put(32, 47, 'P', over=',')
    return z


# ---------------------------------------------------------------- 3: the inner ward and the keep
def keep():
    z = shell('castle_keep', 62, 56, 49, 29)
    towers(z, [(1, 1), (56, 1), (1, 50), (56, 50), (1, 26), (56, 26)])
    z.pave(18, 7, 26, 28, ';')                     # flagstone court round the keep
    z.pave(28, 35, 5, 20, ',')                     # approach from the entry gate
    z.pave(44, 7, 11, 5, ',')                      # lane to the exit gate
    z.pave(48, 1, 5, 6, ',')
    z.block(24, 13, 12, 12, 'T', over=';')
    z.puts([(26, 27), (34, 27), (20, 9), (40, 9), (20, 32), (40, 32)], 'n', over=';')
    z.puts([(27, 36), (33, 36), (27, 42), (33, 42), (21, 15), (38, 15), (21, 22), (38, 22)], 'i', over='.;,')
    # west: stables yard and a second well
    z.block(9, 38, 3, 3, 'W')
    z.block(6, 8, 2, 3, 'K')
    z.block(11, 8, 2, 3, 'K')
    for (c, r) in ((7, 15), (11, 17), (6, 20)):
        z.block(c, r, 2, 2, 'Y')
    z.puts([(14, 15), (15, 15), (14, 16), (9, 23), (10, 23), (15, 21)], 'y')
    z.puts([(3, 7), (3, 8), (4, 7), (16, 3), (17, 3)], 'b')
    z.puts([(7, 2), (13, 4)], 'c')
    z.run(4, 31, 5, 'f')
    z.run(11, 31, 5, 'f')
    z.pave(4, 32, 12, 3, 'g')
    z.puts([(14, 44), (15, 44), (14, 45), (5, 45)], 'b')
    z.puts([(6, 44), (17, 48)], 'c')
    z.block(20, 44, 2, 3, 'K')
    # east: the garrison's racks, dummies, a pair of stalls
    z.run(46, 16, 4, 'r')
    z.run(46, 22, 4, 'r')
    z.puts([(53, 15), (53, 19), (53, 23)], 'd')
    z.block(45, 38, 3, 2, 'M')
    z.block(50, 38, 3, 2, 'M')
    z.block(54, 44, 2, 2, 'Y')
    z.puts([(44, 44), (45, 44), (44, 45), (39, 47), (40, 47), (57, 37)], 'b')
    z.puts([(48, 44), (41, 40), (58, 22)], 'c')
    z.puts([(36, 50), (37, 50), (36, 49)], 'y')
    # stairs to the wall walk
    z.block(1, 6, 2, 7, 'X')
    z.block(59, 6, 2, 7, 'V')
    # spawn cans, pickups, entry
    z.puts([(10, 4), (30, 4), (40, 4), (22, 11), (38, 11), (10, 27), (50, 30), (20, 38), (40, 37), (50, 12), (22, 27), (38, 27)], 'S', over='.,;')
    z.puts([(16, 26), (44, 30)], 'a', over='.,;')
    z.puts([(30, 31), (10, 47)], 'h', over='.,;')
    z.put(30, 51, 'P', over=',')
    return z


def main():
    out = []
    for z in (market(), yard(), keep()):
        errs, stats = validate(z, WALK, PREFAB, size=((56, 64), (48, 58)))
        out.append((z, errs, stats))
    return 0 if write(out, check_only='--check' in sys.argv) else 1


if __name__ == '__main__':
    sys.exit(main())
