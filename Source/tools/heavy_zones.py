#!/usr/bin/env python3
"""INKBOLT Heavy Works zones (theme factory2): hand-placed layouts -> src/data/zones/factory2_*.txt

    python3 tools/heavy_zones.py            # write + validate
    python3 tools/heavy_zones.py --print    # ... and print the maps
    python3 tools/heavy_zones.py --check    # validate only

Three 64 x 56 halls of the heavy robot plant. Each has one moving build line (a run of four 14 x 8 line tiles,
56 m, wall to wall but for a walkway at each end): walker mechs ('L') or tread bruisers ('U') ride it on skids from
the feed house through the drivetrain, armour and paint booths into the dispatch house.
Symbols (src/data/themes/factory2.js):
  # walls     L walker build line 14x8 (runs of 4)     U bruiser build line 14x8 (runs of 4)
  = moving belt (runs)    C weld cell 4x4    X chassis jig 6x4    M plate machine 4x2    l leg rack 4x2
  p armour plates 2x2     w wheels / treads 2x2    T test track 16x12 (a bruiser laps it)    D Titan dock 10x8
  c parts crates   b drums   x gas cart / weld screen   z hazard pad 2x2 (walkable)   + built-ins S P E G a h
"""
import sys

from zonekit import Zone, validate, write

WALK = set('z')
PREFAB = {'L': (14, 8), 'U': (14, 8), 'C': (4, 4), 'X': (6, 4), 'M': (4, 2), 'l': (4, 2), 'p': (2, 2), 'w': (2, 2),
          'T': (16, 12), 'D': (10, 8), 'z': (2, 2)}
W, H = 64, 56


def shell(name, gate=30, entry=30):
    z = Zone(name, W, H)
    z.rect(0, 0, W, 1, '#')
    z.rect(0, H - 1, W, 1, '#')
    z.rect(0, 0, 1, H, '#')
    z.rect(W - 1, 0, 1, H, '#')
    z.rect(gate, 0, 3, 1, 'G')
    z.rect(entry, H - 1, 3, 1, 'E')
    return z


def line(z, r, ch):
    """A full build line (four tiles, 56 m) from column 4, rows r .. r + 7."""
    z.block(4, r, 56, 8, ch)


# ---------------------------------------------------------------- 1: Chassis Hall (walker line)
def chassis():
    z = shell('factory2_chassis')
    # north store: plates, wheels, two feeder belts, crates
    z.block(5, 3, 2, 2, 'p')
    z.block(9, 3, 2, 2, 'p')
    z.block(49, 2, 2, 2, 'w')
    z.block(53, 2, 2, 2, 'w')
    z.block(57, 5, 2, 2, 'w')
    z.run(14, 5, 12, '=')
    z.run(37, 5, 10, '=')
    z.puts([(18, 2), (19, 2), (18, 3)], 'c')
    z.puts([(41, 2), (42, 2)], 'b')
    z.puts([(26, 2), (35, 8)], 'x')
    line(z, 11, 'L')
    # the floor: weld cells, chassis jigs, machines, leg racks, hazard pads
    z.block(6, 23, 4, 4, 'C')
    z.block(6, 31, 4, 4, 'C')
    z.block(20, 24, 6, 4, 'X')
    z.block(38, 24, 6, 4, 'X')
    z.block(52, 23, 4, 2, 'M')
    z.block(52, 29, 4, 2, 'M')
    z.block(16, 33, 4, 2, 'l')
    z.block(44, 34, 4, 2, 'l')
    z.block(30, 25, 2, 2, 'z')
    z.block(28, 33, 2, 2, 'p')
    z.block(34, 33, 2, 2, 'w')
    z.run(8, 42, 10, '=')
    z.run(46, 42, 10, '=')
    z.puts([(24, 30), (25, 30), (24, 31)], 'c')
    z.puts([(39, 30), (40, 30)], 'b')
    z.puts([(12, 27), (47, 28)], 'x')
    z.block(26, 39, 6, 4, 'X')
    z.block(50, 36, 4, 4, 'C')
    z.block(32, 6, 4, 2, 'l')
    # south: the entry floor
    z.block(5, 47, 2, 2, 'w')
    z.block(25, 46, 2, 2, 'w')
    z.block(36, 46, 2, 2, 'p')
    z.block(56, 47, 2, 2, 'p')
    z.puts([(21, 46), (22, 46), (21, 47)], 'c')
    z.puts([(41, 46), (42, 46)], 'c')
    z.puts([(14, 50), (48, 50)], 'b')
    z.put(31, 51, 'P')
    z.puts([(3, 8), (28, 8), (60, 9), (3, 21), (16, 21), (46, 21), (60, 21), (14, 29), (31, 22), (48, 31), (3, 38), (24, 37), (40, 38), (60, 39)], 'S')
    z.puts([(12, 45), (50, 45), (34, 20)], 'a')
    z.puts([(3, 29), (59, 34), (23, 8)], 'h')
    return z


# ---------------------------------------------------------------- 2: Armour & Test (bruiser line, test track)
def armour():
    z = shell('factory2_armour')
    # north-east: the test track; north-west: weld cells and a chassis jig
    z.block(45, 3, 16, 12, 'T')
    z.block(4, 3, 4, 4, 'C')
    z.block(10, 3, 4, 4, 'C')
    z.block(20, 5, 6, 4, 'X')
    z.block(33, 4, 2, 2, 'p')
    z.block(36, 4, 2, 2, 'p')
    z.block(36, 10, 2, 2, 'w')
    z.puts([(17, 3), (18, 3), (17, 4)], 'c')
    z.puts([(28, 2), (29, 11)], 'x')
    z.run(6, 18, 12, '=')
    z.block(24, 15, 4, 2, 'l')
    z.block(38, 18, 4, 2, 'M')
    z.block(48, 19, 4, 2, 'M')
    z.puts([(56, 18), (57, 18)], 'b')
    z.block(30, 20, 2, 2, 'z')
    line(z, 26, 'U')
    z.block(38, 12, 4, 4, 'C')
    # south: plate shop and wheels
    z.block(32, 39, 4, 4, 'C')
    z.block(8, 49, 2, 2, 'p')
    z.block(56, 48, 2, 2, 'w')
    z.block(6, 38, 4, 2, 'M')
    z.block(14, 39, 4, 2, 'l')
    z.block(46, 38, 4, 2, 'l')
    z.block(54, 39, 4, 2, 'M')
    z.block(24, 40, 2, 2, 'p')
    z.block(38, 40, 2, 2, 'w')
    z.block(41, 40, 2, 2, 'w')
    z.run(48, 45, 10, '=')
    z.run(6, 45, 9, '=')
    z.puts([(20, 46), (21, 46), (20, 47)], 'c')
    z.puts([(42, 48), (43, 48)], 'c')
    z.puts([(12, 50), (52, 51)], 'b')
    z.puts([(28, 43), (35, 44)], 'x')
    z.put(31, 51, 'P')
    z.puts([(3, 10), (16, 10), (31, 8), (41, 8), (3, 22), (20, 22), (44, 23), (60, 22), (3, 36), (20, 36), (32, 37), (52, 36), (60, 45)], 'S')
    z.puts([(14, 14), (44, 46), (33, 24)], 'a')
    z.puts([(26, 12), (59, 17), (3, 46)], 'h')
    return z


# ---------------------------------------------------------------- 3: Dispatch & the Titan (walker line, dock, track)
def dispatch():
    z = shell('factory2_dispatch')
    # north: the Titan dock in the middle, chassis jigs and machines either side
    z.block(27, 4, 10, 8, 'D')
    z.block(6, 4, 6, 4, 'X')
    z.block(50, 4, 6, 4, 'X')
    z.block(16, 3, 4, 2, 'M')
    z.block(42, 3, 4, 2, 'M')
    z.block(15, 9, 2, 2, 'w')
    z.block(46, 9, 2, 2, 'p')
    z.puts([(22, 2), (23, 2), (22, 3)], 'c')
    z.puts([(40, 9), (24, 11)], 'x')
    z.puts([(58, 10), (59, 10)], 'b')
    line(z, 16, 'L')
    # south: the test track (west), weld cells, leg racks, belts
    z.block(4, 30, 16, 12, 'T')
    z.block(26, 30, 4, 4, 'C')
    z.block(52, 29, 4, 4, 'C')
    z.block(36, 31, 4, 2, 'l')
    z.block(44, 36, 4, 2, 'l')
    z.block(33, 37, 2, 2, 'z')
    z.block(56, 40, 2, 2, 'w')
    z.block(25, 39, 2, 2, 'p')
    z.run(42, 44, 12, '=')
    z.block(48, 47, 6, 4, 'X')
    z.block(22, 49, 2, 2, 'w')
    z.run(6, 46, 10, '=')
    z.puts([(23, 45), (24, 45), (23, 46)], 'c')
    z.puts([(40, 48), (41, 48)], 'c')
    z.puts([(14, 51), (50, 51)], 'b')
    z.puts([(48, 30), (30, 43)], 'x')
    z.put(31, 51, 'P')
    z.puts([(3, 9), (20, 13), (42, 13), (60, 13), (3, 26), (24, 26), (40, 27), (60, 26), (22, 35), (46, 33), (60, 36), (36, 28), (3, 44)], 'S')
    z.puts([(20, 7), (47, 47), (30, 36)], 'a')
    z.puts([(44, 7), (3, 29), (58, 45)], 'h')
    return z


def main():
    out = []
    for z in (chassis(), armour(), dispatch()):
        errs, stats = validate(z, WALK, PREFAB, size=((56, 64), (48, 58)))
        out.append((z, errs, stats))
    return 0 if write(out, check_only='--check' in sys.argv) else 1


if __name__ == '__main__':
    sys.exit(main())
