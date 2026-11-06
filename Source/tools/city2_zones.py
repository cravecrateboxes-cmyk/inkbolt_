#!/usr/bin/env python3
"""INKBOLT City2 zones ('Downtown at Dusk'): hand-placed layouts -> src/data/zones/city2_*.txt

    python3 tools/city2_zones.py            # write + validate
    python3 tools/city2_zones.py --print    # ... and print the maps
    python3 tools/city2_zones.py --check    # validate only

Three downtown blocks walled by 4-6 storey facades (1 cell thick on the zone edge; inner blocks >= 2 thick).
Symbols (src/data/themes/city2.js):
  # facade / building     , sidewalk     ; plaza granite     - | white lane dash (along X / Z)     ~ ! double yellow
  z Z zebra bars along X / Z     o manhole     i l e w street light, arm toward S / N / E / W     I plaza lamp
  t street tree    m hydrant / mailbox / news boxes / litter basket    c trash bags / boxes / pallets
  = sawhorse (runs)   j jersey barrier (runs)   s steam stack   b bench [2,1]   C cab / sedan [2,4]   V box truck [2,5]
  k newsstand [2,3]   n hot-dog cart [2,2]   Y billboard on legs [6,2] (faces south)
  L elevated railway span [4,6]   R span with a stopped train [4,12]   (open underneath: only the columns collide)
  U subway entrance [3,5] (opens south)    Q statue on a granite plinth [4,4]          + built-ins S P E G a h
"""
import sys

from zonekit import Zone, validate, write

WALK = set(',;-|~!zZoLR')
PREFAB = {'b': (2, 1), 'C': (2, 4), 'V': (2, 5), 'k': (2, 3), 'n': (2, 2), 'Y': (6, 2), 'L': (4, 6), 'R': (4, 12),
          'U': (3, 5), 'Q': (4, 4)}


def shell(name, w, h, gate, entry):
    z = Zone(name, w, h)
    z.rect(0, 0, w, 1, '#')
    z.rect(0, h - 1, w, 1, '#')
    z.rect(0, 0, 1, h, '#')
    z.rect(w - 1, 0, 1, h, '#')
    z.rect(gate, 0, 3, 1, 'G')
    z.rect(entry, h - 1, 3, 1, 'E')
    # 3 m sidewalks along every facade
    z.pave(1, 1, w - 2, 3, ',')
    z.pave(1, h - 4, w - 2, 3, ',')
    z.pave(1, 1, 3, h - 2, ',')
    z.pave(w - 4, 1, 3, h - 2, ',')
    return z


def block(z, c0, r0, w, h, walk=3):
    """An inner building block with a sidewalk ring round it."""
    z.pave(c0 - walk, r0 - walk, w + 2 * walk, h + 2 * walk, ',')
    z.rect(c0, r0, w, h, '#')


def dashes(z, c, r0, r1, ch='|'):
    for r in range(r0, r1, 2):
        if z.at(c, r) == '.':
            z.put(c, r, ch)


def dashes_x(z, r, c0, c1, ch='-'):
    for c in range(c0, c1, 2):
        if z.at(c, r) == '.':
            z.put(c, r, ch)


# ---------------------------------------------------------------- 1: El Avenue
def avenue():
    z = shell('city2_avenue', 60, 50, 14, 28)
    block(z, 10, 15, 10, 16)                                 # west block (cols 10-19, rows 15-30)
    # the El down the avenue, wall to wall (into the facades through portals)
    z.rect(40, 1, 4, 18, 'L')
    z.rect(40, 19, 4, 12, 'R')
    z.rect(40, 31, 4, 18, 'L')
    # lane paint and crossings
    dashes(z, 33, 5, 40)
    dashes(z, 50, 5, 40)
    z.rect(24, 41, 16, 3, 'Z')
    z.rect(44, 41, 12, 3, 'Z')
    dashes_x(z, 7, 5, 39)
    z.rect(4, 37, 2, 1, 'z')
    # parked cars, traffic, a truck
    for r in (12, 20, 28):
        z.block(24, r, 2, 4, 'C', over='.-|')
    for r in (8, 16, 33):
        z.block(54, r, 2, 4, 'C', over='.-|')
    z.block(54, 23, 2, 5, 'V', over='.-|')
    z.block(35, 14, 2, 4, 'C', over='.-|')
    z.block(46, 26, 2, 4, 'C', over='.-|')
    z.block(29, 30, 2, 4, 'C', over='.-|')
    z.block(36, 4, 4, 2, 'C', over='.-')
    # newsstand, steam stacks, manholes, roadworks
    z.block(30, 1, 3, 2, 'k', over=',')
    z.puts([(33, 20), (50, 37), (27, 8)], 's', over='.|-')
    z.puts([(37, 10), (47, 18), (31, 38)], 'o', over='.|-')
    z.run(46, 36, 3, '=')
    z.run(52, 36, 2, 'j')
    z.puts([(49, 34), (52, 33)], 'c')
    # lamps (arm over the street), trees, furniture
    z.puts([(6, 3), (22, 3), (34, 3), (51, 3)], 'i', over=',')
    z.puts([(6, 46), (20, 46), (36, 46), (51, 46)], 'l', over=',')
    z.puts([(3, 12), (3, 26), (3, 40)], 'e', over=',')
    z.puts([(56, 12), (56, 28), (56, 42)], 'w', over=',')
    z.puts([(22, 17), (22, 27)], 'e', over=',')
    z.puts([(7, 18), (7, 29)], 'w', over=',')
    z.puts([(12, 2), (26, 2), (48, 2), (12, 47), (24, 47), (46, 47), (2, 20), (2, 34), (57, 20), (57, 36), (14, 12), (18, 33)], 't', over=',')
    z.puts([(7, 3), (23, 3), (35, 3), (52, 46), (2, 13), (57, 13), (21, 33), (8, 12)], 'm', over=',')
    z.puts([(1, 1), (2, 1), (1, 2), (58, 47), (1, 30), (58, 24)], 'c', over=',')
    # spawn cans, pickups, entry
    z.puts([(30, 10), (48, 10), (36, 24), (49, 22), (30, 23), (47, 32), (12, 6), (22, 7), (6, 41), (52, 41), (14, 38), (34, 29)], 'S', over='.,;-|zZ')
    z.puts([(26, 40), (52, 30)], 'a', over='.,;-|zZ')
    z.puts([(36, 20), (5, 24)], 'h', over='.,;-|zZ')
    z.put(29, 45, 'P', over='.,')
    return z


# ---------------------------------------------------------------- 2: Statue Plaza
def plaza():
    z = shell('city2_plaza', 60, 54, 44, 14)
    z.pave(12, 12, 36, 30, ';')                              # the plaza (cols 12-47, rows 12-41)
    z.block(28, 25, 4, 4, 'Q', over=';')
    z.block(15, 15, 3, 5, 'U', over=';')
    z.block(42, 33, 3, 5, 'U', over=';')
    z.puts([(24, 22), (35, 22), (24, 31), (35, 31), (12, 12), (47, 12), (12, 41), (47, 41)], 'I', over=';')
    for (c, r) in ((26, 20), (32, 20), (26, 33), (32, 33)):
        z.block(c, r, 2, 1, 'b', over=';')
    z.puts([(17, 25), (17, 30), (42, 25), (42, 30), (21, 38), (38, 38), (21, 15), (38, 15)], 't', over=';')
    z.block(36, 36, 2, 2, 'n', over=';')
    z.block(20, 27, 2, 2, 'n', over=';')
    z.block(43, 16, 2, 3, 'k', over=';')
    # billboards over the street corners (facing the entry)
    z.block(4, 6, 6, 2, 'Y')
    z.block(50, 6, 6, 2, 'Y')
    # ring road: lane paint, crossings from the sidewalks to the plaza
    dashes_x(z, 8, 12, 48)
    dashes_x(z, 46, 12, 48)
    dashes(z, 8, 12, 42)
    dashes(z, 51, 12, 42)
    for c in range(27, 33):
        for r in range(4, 12):
            if z.at(c, r) in '.-':
                z.g[r][c] = 'Z'
    for c in range(27, 33):
        for r in range(42, 50):
            if z.at(c, r) in '.-':
                z.g[r][c] = 'Z'
    for r in range(24, 30):
        for c in list(range(4, 12)) + list(range(48, 56)):
            if z.at(c, r) in '.|':
                z.g[r][c] = 'z'
    # traffic
    z.block(5, 16, 2, 4, 'C', over='.-|')
    z.block(5, 34, 2, 4, 'C', over='.-|')
    z.block(53, 14, 2, 5, 'V', over='.-|')
    z.block(53, 34, 2, 4, 'C', over='.-|')
    z.block(16, 4, 4, 2, 'C', over='.-|')
    z.block(38, 9, 4, 2, 'C', over='.-|')
    z.block(19, 43, 4, 2, 'C', over='.-|')
    z.block(39, 47, 4, 2, 'C', over='.-|')
    z.puts([(10, 44), (50, 10), (22, 9)], 's')
    z.puts([(23, 6), (45, 44), (9, 22)], 'o')
    # lamps, trees, furniture on the sidewalks
    z.puts([(14, 3), (26, 3), (36, 3), (50, 3)], 'i', over=',')
    z.puts([(6, 50), (24, 50), (36, 50), (52, 50)], 'l', over=',')
    z.puts([(3, 14), (3, 28), (3, 42)], 'e', over=',')
    z.puts([(56, 22), (56, 36), (56, 46)], 'w', over=',')
    z.puts([(20, 2), (32, 2), (42, 2), (12, 51), (30, 51), (46, 51), (2, 20), (2, 36), (57, 28), (57, 42)], 't', over=',')
    z.puts([(15, 3), (37, 3), (25, 50), (2, 29), (57, 23), (51, 50)], 'm', over=',')
    z.puts([(1, 1), (2, 1), (58, 1), (58, 2), (1, 52), (58, 52), (57, 52)], 'c', over=',')
    # spawn cans, pickups, entry
    z.puts([(16, 7), (32, 6), (46, 9), (6, 27), (53, 26), (20, 21), (38, 21), (14, 33), (44, 27), (28, 37), (34, 15), (36, 46)], 'S', over='.,;-|zZ')
    z.puts([(30, 22), (8, 40)], 'a', over='.,;-|zZ')
    z.puts([(30, 33), (51, 40)], 'h', over='.,;-|zZ')
    z.put(15, 49, 'P', over='.,Z')
    return z


# ---------------------------------------------------------------- 3: The Crossing
def crossing():
    z = shell('city2_crossing', 62, 56, 30, 45)
    # the El crosses the district east-west, wall to wall
    z.rect(1, 8, 24, 4, 'L')
    z.rect(25, 8, 12, 4, 'R')
    z.rect(37, 8, 24, 4, 'L')
    block(z, 9, 22, 14, 12)                                  # west block (cols 9-22, rows 22-33)
    z.pave(36, 23, 14, 12, ';')                             # pocket park (cols 36-49, rows 23-34)
    z.puts([(36, 23), (49, 23), (36, 34), (49, 34)], 'I', over=';')
    z.puts([(39, 26), (46, 26), (39, 31), (46, 31)], 't', over=';')
    for (c, r) in ((41, 25), (41, 32)):
        z.block(c, r, 2, 1, 'b', over=';')
    z.block(44, 28, 2, 2, 'n', over=';')
    # avenue paint
    dashes(z, 30, 14, 46)
    dashes_x(z, 15, 4, 28)
    dashes_x(z, 15, 34, 58)
    dashes_x(z, 41, 4, 60, '-')
    for c in range(27, 34):
        for r in range(38, 41):
            if z.at(c, r) in '.|':
                z.g[r][c] = 'Z'
    # a billboard lot, a stalled truck, a crash cordoned off with sawhorses
    z.block(51, 17, 6, 2, 'Y')
    z.block(26, 17, 2, 5, 'V', over='.-|')
    z.block(31, 25, 2, 4, 'C', over='.-|')
    z.block(27, 28, 2, 4, 'C', over='.-|')
    z.run(26, 35, 3, '=')
    z.run(31, 35, 3, '=')
    z.puts([(30, 31), (31, 31)], 'c', over='.|')
    z.block(5, 13, 4, 2, 'C', over='.-|')
    z.block(46, 13, 4, 2, 'C', over='.-|')
    z.block(52, 38, 2, 4, 'C', over='.-|')
    z.block(6, 43, 4, 2, 'C', over='.-|')
    z.block(16, 47, 4, 2, 'C', over='.')
    z.block(40, 44, 2, 5, 'V', over='.-|')
    z.block(54, 46, 2, 3, 'k', over=',.')
    z.run(10, 37, 4, 'j')
    z.puts([(44, 16), (18, 42), (54, 30)], 's', over='.-')
    z.puts([(22, 15), (36, 42), (56, 22)], 'o', over='.-')
    # lamps, trees, furniture
    z.puts([(6, 3), (20, 3), (40, 3), (54, 3)], 'i', over=',')
    z.puts([(8, 52), (22, 52), (36, 52), (52, 52)], 'l', over=',')
    z.puts([(3, 20), (3, 34), (3, 46)], 'e', over=',')
    z.puts([(58, 20), (58, 32), (58, 44)], 'w', over=',')
    z.puts([(24, 25), (24, 31)], 'e', over=',')
    z.puts([(6, 27)], 'w', over=',')
    z.puts([(12, 2), (26, 2), (48, 2), (14, 53), (28, 53), (48, 53), (2, 24), (2, 40), (59, 26), (59, 38), (15, 20)], 't', over=',')
    z.puts([(7, 3), (21, 3), (41, 3), (37, 52), (2, 28), (59, 33), (20, 35)], 'm', over=',')
    z.puts([(1, 1), (2, 1), (60, 1), (60, 2), (1, 54), (60, 54), (59, 54)], 'c', over=',')
    # spawn cans, pickups, entry
    z.puts([(12, 5), (30, 5), (50, 5), (5, 18), (40, 18), (56, 13), (28, 24), (52, 26), (5, 38), (24, 44), (32, 44), (53, 34)], 'S', over='.,;-|zZ')
    z.puts([(14, 16), (44, 38)], 'a', over='.,;-|zZ')
    z.puts([(30, 20), (8, 47)], 'h', over='.,;-|zZ')
    z.put(46, 51, 'P', over='.,')
    return z


def main():
    out = []
    for z in (avenue(), plaza(), crossing()):
        errs, stats = validate(z, WALK, PREFAB, size=((56, 64), (48, 58)))
        out.append((z, errs, stats))
    return 0 if write(out, check_only='--check' in sys.argv) else 1


if __name__ == '__main__':
    sys.exit(main())
