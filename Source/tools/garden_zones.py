#!/usr/bin/env python3
"""INKBOLT garden zones: hand-placed layouts for the Wide Garden Playground theme -> src/data/zones/garden_*.txt

    python3 tools/garden_zones.py            # write + validate
    python3 tools/garden_zones.py --check    # validate only
    python3 tools/garden_zones.py --print    # also print the maps

Every placement is deliberate: each garden starts as open lawn inside its hedge border, gets its hedge masses,
gravel paths and paving, its playground (the play tower, the big play fort, the pirate ship), play equipment, flower
beds, trees, benches and lamps, then spawn cans and pickups. Symbols: see src/data/themes/garden.js.
Validation (tools/zonekit.py, mirrors tests/unit/theme_garden.test.js): size, gates, P -> exit path, 10-14 spawns
>= 14 m from P with 3 x 3 open ground, 2-3 ammo / health, weapon-stand cells open, prefab blocks tile exactly,
no sealed open cells.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zonekit import Zone, validate, write  # noqa: E402

WALK = set(',;m')                    # floor symbols you stand on (besides . P E G a h S)
PREFABS = {'b': (2, 1), 'k': (2, 2), 'F': (6, 6), 'Z': (6, 6), 'H': (4, 4), 'Q': (4, 4), 'W': (4, 2), 'w': (4, 2),
           'M': (6, 2), 'T': (10, 10), 'U': (10, 10), 'X': (30, 16), 'Y': (20, 10)}
FLOORS = '.,;m'


def shell(name, w, h, gate, entry):
    z = Zone(name, w, h)
    z.rect(0, 0, w, 1, '#')
    z.rect(0, h - 1, w, 1, '#')
    z.rect(0, 0, 1, h, '#')
    z.rect(w - 1, 0, 1, h, '#')
    z.rect(gate, 0, 3, 1, 'G')
    z.rect(entry, h - 1, 3, 1, 'E')
    return z


def lawns():
    """Zone 1, The Lawns: the play tower in a fenced play area (rubber surface, sandpit, swings, seesaw, monkey bars)
    to the west; flower-bed rows and the fountain on paving to the east; gravel paths from the entry gate to the exit."""
    z = shell('garden_lawns', 56, 52, 26, 26)
    # hedge masses (2+ thick) in the corners and a hedge screen east of the middle
    z.rect(1, 1, 5, 7, '#')
    z.rect(1, 1, 9, 3, '#')
    z.rect(47, 1, 8, 4, '#')
    z.rect(51, 1, 4, 8, '#')
    z.rect(1, 44, 5, 7, '#')
    z.rect(49, 45, 6, 6, '#')
    z.rect(31, 20, 2, 8, '#')
    # gravel paths: entry stem, cross path, east loop, north stem to the exit
    z.pave(26, 39, 3, 12, ',')
    z.pave(6, 38, 44, 3, ',')
    z.pave(45, 12, 3, 27, ',')
    z.pave(26, 12, 21, 3, ',')
    z.pave(26, 1, 3, 12, ',')
    # play area: rubber surface, fence with gaps, play tower, sandpit, swings, seesaw, monkey bars
    z.pave(5, 14, 20, 22, 'm')
    z.block(9, 17, 10, 10, 'T', over='m')
    z.block(20, 15, 4, 4, 'Q', over='m')
    z.block(6, 31, 4, 2, 'W', over='m')
    z.block(13, 31, 4, 2, 'w', over='m')
    z.block(19, 29, 6, 2, 'M', over='m')
    for c in range(4, 26):
        if not 12 <= c <= 15:
            z.put(c, 13, '-', over='.')
        if not 9 <= c <= 13:
            z.put(c, 36, '-', over='.,')
    for r in range(14, 36):
        if not (21 <= r <= 24 or 32 <= r <= 33):
            z.put(25, r, '-', over='.')
    for r in range(14, 36):
        if not 26 <= r <= 28:
            z.put(4, r, '-', over='.')
    # east: fountain on paving, flower-bed rows, benches
    z.pave(34, 23, 10, 10, ';')
    z.block(36, 25, 6, 6, 'F', over=';')
    for r in (16, 19):
        z.run(34, r, 5, 'f')
        z.run(40, r, 4, 'f')
    z.run(34, 35, 4, 'f')
    z.run(39, 35, 4, 'f')
    z.block(36, 33, 2, 1, 'b', over=';.')
    z.block(40, 22, 2, 1, 'b', over=';.')
    z.block(49, 20, 1, 2, 'b')
    z.block(30, 41, 2, 1, 'b')
    z.block(21, 41, 2, 1, 'b')
    z.puts([(34, 23), (43, 23), (34, 32), (43, 32)], 'o', over=';')
    # north: box-hedge rows and trees in the lawn, a birdbath
    z.run(11, 7, 8, '=')
    z.run(33, 7, 8, '=')
    z.run(16, 9, 6, '=')
    z.put(38, 4, 'd')
    for (c, r) in ((7, 10), (21, 5), (12, 4), (31, 4), (42, 9), (50, 13), (51, 27), (50, 36), (3, 20), (3, 30),
                   (13, 45), (40, 46), (8, 42), (19, 47), (35, 44), (46, 42)):
        z.put(c, r, 't')
    # lamps and bins along the paths
    z.puts([(24, 37), (30, 36), (25, 11), (29, 11), (44, 16), (48, 30), (25, 46), (29, 44)], 'l')
    z.puts([(30, 37), (44, 30), (24, 42)], 'i')
    # spawn cans (>= 14 m from P, 3 x 3 open), pickups
    z.puts([(14, 5), (24, 7), (43, 6), (36, 11), (52, 21), (52, 32), (13, 39), (42, 43), (10, 11), (28, 18), (47, 47), (2, 37)], 'S', over=FLOORS)
    z.puts([(18, 40), (41, 13)], 'a', over=FLOORS)
    z.puts([(33, 30), (6, 28), (38, 40)], 'h', over=FLOORS)
    z.put(27, 47, 'P', over=FLOORS)
    return z


def fort():
    """Zone 2, The Fort: the big three-tower play fort in the middle of the lawn (bridges, stairs, a ramp, slides, a
    climbing wall; walk under its decks), the gazebo on paving to the north-west, the fountain to the south-east,
    flower beds and trees round the edges, box hedges and picket runs for cover."""
    z = shell('garden_fort', 58, 54, 27, 27)
    z.rect(1, 1, 3, 4, '#')
    z.rect(1, 1, 6, 2, '#')
    z.rect(50, 1, 7, 3, '#')
    z.rect(53, 1, 4, 7, '#')
    z.rect(1, 46, 6, 7, '#')
    z.rect(52, 47, 5, 6, '#')
    z.rect(1, 24, 2, 6, '#')
    z.rect(55, 22, 2, 8, '#')
    # paths: entry stem, a ring round the fort, north stem to the exit
    z.pave(27, 43, 3, 10, ',')
    z.pave(8, 41, 43, 3, ',')
    z.pave(8, 13, 3, 31, ',')
    z.pave(48, 13, 3, 31, ',')
    z.pave(8, 12, 43, 3, ',')
    z.pave(27, 1, 3, 12, ',')
    # the fort on rubber play surface
    z.pave(12, 15, 34, 26, 'm')
    z.block(14, 19, 30, 16, 'X', over='m')
    # gazebo (north-west) and fountain (south-east) on paving
    z.pave(12, 3, 10, 9, ';')
    z.block(14, 4, 6, 6, 'Z', over=';')
    z.pave(37, 44, 12, 9, ';', over='.')
    z.block(40, 46, 6, 6, 'F', over=';')
    z.puts([(37, 44), (48, 44), (37, 52), (48, 52)], 'o', over=';')
    # flower beds, box hedges, pickets, trees, benches, lamps
    for c0 in (33, 41):
        z.run(c0, 5, 6, 'f')
        z.run(c0, 8, 6, 'f')
    z.run(13, 47, 8, 'f')
    z.run(13, 50, 8, '=')
    z.run(3, 33, 4, '=', vertical=True)
    z.run(53, 33, 4, '=', vertical=True)
    z.run(13, 38, 5, '-', over='m')
    z.run(40, 38, 5, '-', over='m')
    z.block(23, 9, 2, 1, 'b', over=';.')
    z.block(31, 44, 2, 1, 'b')
    z.block(5, 15, 1, 2, 'b')
    z.block(52, 15, 1, 2, 'b')
    for (c, r) in ((4, 7), (25, 4), (47, 7), (52, 11), (4, 20), (53, 19), (5, 38), (52, 41), (9, 46), (23, 48), (35, 50),
                   (51, 44)):
        z.put(c, r, 't')
    z.puts([(11, 12), (47, 12), (11, 43), (47, 41), (25, 45), (31, 45), (26, 10), (30, 10)], 'l', over='.,')
    z.puts([(7, 41), (51, 41)], 'i')
    z.put(36, 4, 'd')
    # spawn cans and pickups
    z.puts([(5, 10), (31, 7), (44, 11), (52, 26), (51, 38), (5, 31), (4, 40), (44, 36), (12, 15), (45, 16), (21, 36), (35, 36)], 'S', over=FLOORS)
    z.puts([(17, 12), (41, 42)], 'a', over=FLOORS)
    z.puts([(46, 27), (11, 27), (29, 16)], 'h', over=FLOORS)
    z.put(28, 49, 'P', over=FLOORS)
    return z


def cove():
    """Zone 3, Pirate Cove: the pirate play ship on its painted sea to the north-west, a second play tower (stairs to
    the north) to the east, the potting shed and a picnic lawn to the south-east, swings by the ship, flower borders
    and an orchard of trees; the exit at the north."""
    z = shell('garden_cove', 58, 52, 33, 27)
    z.rect(1, 1, 4, 5, '#')
    z.rect(1, 1, 8, 2, '#')
    z.rect(51, 1, 6, 5, '#')
    z.rect(1, 45, 7, 6, '#')
    z.rect(53, 44, 4, 7, '#')
    z.rect(27, 24, 2, 7, '#')
    # paths
    z.pave(27, 41, 3, 10, ',')
    z.pave(6, 38, 46, 3, ',')
    z.pave(33, 1, 3, 9, ',')
    z.pave(30, 8, 22, 3, ',')
    z.pave(49, 10, 3, 29, ',')
    z.pave(30, 10, 3, 14, ',')
    # the pirate ship (sea painted in the piece) and swings beside it
    z.block(5, 9, 20, 10, 'Y')
    z.pave(5, 20, 20, 6, 'm')
    z.block(7, 22, 4, 2, 'W', over='m')
    z.block(17, 22, 6, 2, 'M', over='m')
    # the second play tower (stairs north) on rubber, monkey-bar run
    z.pave(35, 13, 12, 13, 'm')
    z.block(36, 15, 10, 10, 'U', over='m')
    # shed and picnic lawn (south-east), sandpit, flower borders, orchard
    z.block(44, 29, 4, 4, 'H')
    for (c, r) in ((33, 30), (37, 33), (40, 29), (36, 43), (42, 44)):
        z.block(c, r, 2, 2, 'k')
    z.block(12, 29, 4, 4, 'Q')
    z.run(10, 4, 8, 'f')
    z.run(20, 4, 6, 'f')
    z.run(38, 4, 8, 'f')
    z.run(8, 34, 6, '=')
    z.run(19, 34, 6, '=')
    z.run(32, 27, 6, '-')
    for (c, r) in ((2, 10), (2, 20), (3, 30), (6, 43), (13, 46), (21, 43), (24, 30), (40, 48), (47, 47), (54, 22),
                   (54, 33), (47, 6), (28, 4), (24, 27)):
        z.put(c, r, 't')
    z.block(17, 27, 2, 1, 'b')
    z.block(44, 36, 2, 1, 'b')
    z.block(32, 45, 1, 2, 'b')
    z.puts([(26, 38), (30, 37), (32, 7), (36, 7), (48, 14), (52, 26), (26, 45)], 'l', over='.,')
    z.puts([(31, 41), (48, 37)], 'i')
    z.put(18, 2, 'o')
    z.put(42, 2, 'o')
    # spawn cans and pickups
    z.puts([(4, 7), (26, 7), (44, 11), (54, 13), (54, 28), (3, 25), (12, 37), (40, 36), (20, 31), (33, 19), (47, 43), (8, 30)], 'S', over=FLOORS)
    z.puts([(14, 42), (52, 41)], 'a', over=FLOORS)
    z.puts([(30, 32), (46, 9), (4, 37)], 'h', over=FLOORS)
    z.put(28, 47, 'P', over=FLOORS)
    return z


def main():
    out = []
    for fn in (lawns, fort, cove):
        z = fn()
        errs, stats = validate(z, WALK, PREFABS)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
