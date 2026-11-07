#!/usr/bin/env python3
"""INKBOLT Lagoon Island zones (theme 'island'): hand-placed layouts -> src/data/zones/island_*.txt

    python3 tools/island_zones.py           # write + validate
    python3 tools/island_zones.py --check   # validate only
    python3 tools/island_zones.py --print   # also print the maps

Three wide 64 x 56 arenas on one island. Every edge wall is one cell thick ('#': jungle thickets, basalt outcrops and
dunes behind driftwood fences, picked by the theme's wall chooser); the edge that faces the ocean is a low
rock-armoured sea wall instead ('}' on an east edge, '{' on a west edge) with the beach, the surf and the open sea
right behind it. Symbols (src/data/themes/island.js):
  # edge wall          { } sea wall (W / E edge)   o rock          O outcrop 2x2     c crate (stacks)   b barrels
  t palm               F palm clump 2x2            x driftwood     f driftwood fence = sandbags         r reeds
  p tiki torch / sign  u beach umbrella            B boat 4x2      M grass 3x3       D dune 3x3         W pond 4x4
  w tide pool 3x3      V lagoon 14x10              H beach hut 5x5 L lighthouse 6x6  T ruined lookout 4x4
  R research outpost 7x5   A radio mast 2x2   Q solar array 3x2   K robot charger 2x2   + built-ins S P E G a h .
Water (W, w, V), grass, dunes and reeds are walkable (shallow, wadeable); only the lagoon's palm islet blocks.
"""
import sys

from zonekit import Zone, validate, write

W, H = 64, 56
GC = 30                  # gates on columns 30-32 (centre 31.5): every zone lines up with the next
PREFAB = {'O': (2, 2), 'F': (2, 2), 'B': (4, 2), 'M': (3, 3), 'D': (3, 3), 'W': (4, 4), 'w': (3, 3), 'V': (14, 10),
          'H': (5, 5), 'L': (6, 6), 'T': (4, 4), 'R': (7, 5), 'A': (2, 2), 'Q': (3, 2), 'K': (2, 2)}
WALKABLE = set('MDWwVr')


def shell(name, sea):
    z = Zone(name, W, H)
    z.rect(0, 0, W, 1, '#')
    z.rect(0, H - 1, W, 1, '#')
    z.rect(0, 0, 1, H, '#')
    z.rect(W - 1, 0, 1, H, '#')
    if sea == 'E':
        z.rect(W - 1, 1, 1, H - 2, '}')
    if sea == 'W':
        z.rect(0, 1, 1, H - 2, '{')
    z.rect(GC, 0, 3, 1, 'G')
    z.rect(GC, H - 1, 3, 1, 'E')
    z.put(31, 51, 'P')
    return z


def blocks(z, ch, pts):
    w, d = PREFAB[ch]
    for p in pts:
        c, r = p[0], p[1]
        if len(p) > 2 and p[2] == 'v':
            z.block(c, r, d, w, ch)
        else:
            z.block(c, r, w, d, ch)


def cells(z, ch, pts):
    z.puts(pts, ch)


# ---------------------------------------------------------------- zone 1: Landing Beach (sea to the east)
def beach():
    z = shell('island_beach', 'E')
    # fishing camp: two huts on stilts, fences, torches, crates
    blocks(z, 'H', [(36, 6), (18, 24)])
    z.run(35, 12, 6, 'f')
    z.run(17, 30, 4, 'f')
    cells(z, 'c', [(42, 8), (42, 9), (24, 25), (25, 30)])
    cells(z, 'b', [(35, 13), (16, 26)])
    cells(z, 'p', [(28, 44), (35, 44), (34, 11), (23, 30)])
    # the beach along the sea wall: boats pulled up, tide pools, washed-up crates and barrels, driftwood
    blocks(z, 'B', [(55, 8), (57, 19, 'v'), (52, 49)])
    blocks(z, 'w', [(58, 13), (52, 39), (57, 44)])
    cells(z, 'c', [(54, 16), (55, 16), (60, 25), (59, 33), (60, 34), (48, 51)])
    cells(z, 'b', [(61, 17), (52, 24), (61, 40), (61, 41)])
    z.run(49, 18, 3, 'x')
    z.run(56, 37, 3, 'x')
    cells(z, 'u', [(48, 44), (55, 27)])
    cells(z, 't', [(50, 4), (61, 29), (49, 31), (62, 52), (45, 47)])
    # dunes, grass, palm groves, rocks across the middle
    blocks(z, 'D', [(42, 16), (28, 36), (11, 44), (46, 27)])
    blocks(z, 'M', [(7, 9), (26, 14), (40, 31), (13, 30)])
    blocks(z, 'F', [(30, 19), (44, 40), (10, 20), (23, 47), (4, 50)])
    blocks(z, 'O', [(16, 8), (36, 25), (7, 37), (19, 52)])
    cells(z, 'o', [(22, 10), (33, 31), (12, 26), (40, 49), (47, 12), (27, 21), (3, 26)])
    z.run(25, 40, 3, 'x')
    z.run(36, 35, 3, 'x')
    # freshwater ponds by the jungle edge
    blocks(z, 'W', [(3, 14), (5, 44)])
    cells(z, 'r', [(7, 15), (2, 18), (9, 46), (4, 43)])
    cells(z, 'S', [(8, 4), (24, 4), (46, 4), (57, 4), (14, 16), (37, 19), (52, 12), (6, 30), (29, 26), (55, 31),
                   (16, 40), (48, 35), (23, 35)])
    cells(z, 'a', [(20, 34), (50, 46), (40, 2)])
    cells(z, 'h', [(10, 50), (44, 21), (30, 8)])
    return z


# ---------------------------------------------------------------- zone 2: the Lagoon (sea to the west)
def lagoon():
    z = shell('island_lagoon', 'W')
    blocks(z, 'V', [(25, 18)])
    cells(z, 'r', [(24, 22), (39, 20), (39, 26), (31, 28)])
    blocks(z, 'W', [(47, 7), (9, 41)])
    cells(z, 'r', [(51, 8), (46, 10), (13, 43)])
    # ruined lookout on the east ridge with rubble cover around it
    blocks(z, 'T', [(51, 35)])
    cells(z, 'o', [(50, 34), (55, 38), (49, 40)])
    # west beach: a hut, boats, tide pools, washed-up crates
    blocks(z, 'H', [(6, 17)])
    blocks(z, 'B', [(2, 25, 'v'), (3, 47)])
    blocks(z, 'w', [(2, 9), (3, 33)])
    cells(z, 'c', [(5, 23), (11, 22), (11, 23), (2, 40), (8, 50)])
    cells(z, 'b', [(2, 31), (12, 18)])
    cells(z, 'u', [(6, 38)])
    cells(z, 't', [(2, 4), (8, 28), (1 + 1, 52)])
    # palm groves, outcrops, rocks, grass and dunes
    blocks(z, 'F', [(19, 11), (43, 15), (44, 45), (18, 35), (57, 19), (36, 9)])
    blocks(z, 'O', [(14, 27), (40, 33), (56, 9), (28, 43), (22, 50)])
    cells(z, 'o', [(22, 31), (46, 26), (33, 6), (12, 8), (58, 47), (34, 37), (60, 29)])
    blocks(z, 'M', [(29, 33), (50, 27), (15, 46), (35, 45)])
    blocks(z, 'D', [(7, 6), (55, 50)])
    z.run(44, 30, 4, 'f')
    z.run(12, 14, 3, 'x')
    z.run(6, 30, 3, 'x')
    cells(z, 'p', [(28, 48), (35, 48), (24, 17), (40, 17)])
    cells(z, 'S', [(12, 3), (50, 3), (25, 7), (55, 15), (17, 22), (47, 20), (9, 34), (25, 37), (45, 39),
                   (58, 33), (14, 39), (40, 3)])
    cells(z, 'a', [(38, 13), (20, 44), (56, 53)])
    cells(z, 'h', [(10, 12), (48, 50), (36, 30)])
    return z


# ---------------------------------------------------------------- zone 3: Lighthouse Point (sea to the east)
def point():
    z = shell('island_point', 'E')
    # the lighthouse on its rocks at the point, a boat and tide pools on the shore below it
    blocks(z, 'L', [(55, 3)])
    blocks(z, 'w', [(58, 20), (56, 41)])
    blocks(z, 'B', [(58, 47, 'v')])
    cells(z, 'o', [(53, 10), (61, 11), (58, 30), (54, 12)])
    # the research outpost the robots took over: lab, radio mast, solar arrays, charging pods, sandbag lines
    blocks(z, 'R', [(20, 14)])
    blocks(z, 'A', [(28, 9)])
    blocks(z, 'Q', [(12, 12), (12, 19)])
    blocks(z, 'K', [(31, 22), (35, 22), (39, 22)])
    z.run(16, 26, 6, '=')
    z.run(30, 28, 6, '=')
    z.run(44, 14, 5, '=')
    z.run(17, 8, 4, '=')
    cells(z, 'c', [(28, 16), (29, 16), (27, 13), (18, 21), (43, 26), (44, 26)])
    cells(z, 'b', [(27, 20), (31, 12), (19, 20), (42, 20)])
    cells(z, 'p', [(19, 13), (27, 19), (30, 26), (37, 26)])
    # ponds, grass, palms, outcrops
    blocks(z, 'W', [(45, 30), (7, 40)])
    cells(z, 'r', [(49, 31), (44, 33), (11, 41), (6, 43)])
    blocks(z, 'F', [(5, 5), (40, 6), (50, 46), (16, 46), (34, 38), (2, 24)])
    blocks(z, 'O', [(48, 21), (24, 36), (40, 44), (8, 28), (28, 50)])
    cells(z, 'o', [(38, 32), (14, 34), (20, 30), (47, 9), (33, 46)])
    blocks(z, 'M', [(26, 42), (42, 37), (10, 50)])
    blocks(z, 'D', [(51, 34), (5, 16)])
    cells(z, 't', [(61, 26), (62, 37), (52, 52), (3, 36)])
    z.run(54, 44, 3, 'x')
    cells(z, 'u', [(60, 15)])
    cells(z, 'S', [(6, 3), (46, 3), (35, 6), (10, 16), (44, 18), (25, 24), (58, 15), (6, 34), (30, 33), (54, 38),
                   (20, 40), (46, 41)])
    cells(z, 'a', [(36, 17), (12, 46), (52, 50)])
    cells(z, 'h', [(24, 30), (44, 49), (61, 2)])
    return z


def main():
    out = []
    for z in (beach(), lagoon(), point()):
        errs, stats = validate(z, WALKABLE, PREFAB, size=((56, 64), (48, 58)))
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
