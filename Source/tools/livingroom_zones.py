#!/usr/bin/env python3
"""INKBOLT Living Room zones (theme src/data/themes/livingroom.js): three wide hand-placed rooms, written as ASCII maps.

    python3 tools/livingroom_zones.py      # (re)writes src/data/zones/livingroom_{lounge,dining,kitchen}.txt

Each room is a list of placements (symbol, col, row, width, height) on a bordered grid with the exit gate (GGG) in
the north wall and the entry gate (EEE) in the south wall. Every map is checked: the entry reaches the exit, every
spawn and pickup is reachable, spawns stand >= 14 m from the entry with free cells around them.
"""
import os
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))
# cells a robot or the player can stand on (raised pieces you run under count as floor; anchors and overlays too)
WALK = set('.PahYDjOufrxy')


def room(w, h, items, spawns, P, ammo, health):
    g = [['.'] * w for _ in range(h)]
    for c in range(w):
        g[0][c] = '#'
        g[h - 1][c] = '#'
    for r in range(h):
        g[r][0] = '#'
        g[r][w - 1] = '#'
    gc = w // 2 - 1
    for c in range(gc, gc + 3):
        g[0][c] = 'G'
        g[h - 1][c] = 'E'
    for (ch, c0, r0, cw, rh) in items:
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + cw):
                assert g[r][c] == '.', 'overlap %s at %d,%d (%s)' % (ch, c, r, g[r][c])
                g[r][c] = ch
    for (c, r) in spawns:
        assert g[r][c] == '.', 'spawn on %s at %d,%d' % (g[r][c], c, r)
        g[r][c] = 'S'
    for ch, pts in (('P', [P]), ('a', ammo), ('h', health)):
        for (c, r) in pts:
            assert g[r][c] == '.', '%s on %s at %d,%d' % (ch, g[r][c], c, r)
            g[r][c] = ch
    return g


def check(name, g):
    h, w = len(g), len(g[0])
    at = lambda c, r: g[r][c] if 0 <= c < w and 0 <= r < h else '#'
    P = [(c, r) for r in range(h) for c in range(w) if g[r][c] == 'P'][0]
    seen, q = {P}, deque([P])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if n not in seen and at(*n) in WALK | {'S'}:
                seen.add(n)
                q.append(n)
    G = [(c, 0) for c in range(w) if g[0][c] == 'G']
    assert (G[1][0], 1) in seen, name + ': exit unreachable'
    for r in range(h):
        for c in range(w):
            ch = g[r][c]
            if ch == 'S':
                assert (c, r) in seen, '%s: spawn %d,%d unreachable' % (name, c, r)
                assert ((c - P[0]) ** 2 + (r - P[1]) ** 2) ** 0.5 >= 14, '%s: spawn %d,%d near P' % (name, c, r)
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if dc or dr:
                            assert at(c + dc, r + dr) in WALK, '%s: spawn %d,%d crowded' % (name, c, r)
            if ch in 'ah':
                assert (c, r) in seen, '%s: pickup %d,%d unreachable' % (name, c, r)
    # the exit and entry gates have open floor in front of them
    for (c, _) in G:
        assert at(c, 1) in WALK and at(c, 2) in WALK, name + ': exit blocked'
        assert at(c, h - 2) in WALK, name + ': entry blocked'


# ---------------------------------------------------------------- lounge: TV wall north, sofa facing it, rug,
# coffee table, fireplace on the south wall, west windows with sun patches, bookshelves, toys strewn east
LOUNGE = dict(w=64, h=46, P=(32, 42), items=[
    ('V', 11, 1, 12, 3), ('p', 24, 1, 3, 3), ('Q', 38, 1, 6, 2), ('W', 45, 1, 9, 1), ('Q', 55, 1, 6, 2),
    ('W', 1, 7, 1, 9), ('W', 1, 26, 1, 9), ('u', 4, 9, 2, 2), ('u', 4, 28, 2, 2),
    ('O', 16, 18, 2, 2), ('Y', 13, 13, 8, 4), ('n', 23, 15, 3, 2), ('T', 10, 22, 14, 6), ('L', 25, 25, 2, 2),
    ('p', 6, 23, 3, 3), ('F', 8, 43, 10, 2), ('r', 20, 44, 4, 1), ('y', 44, 44, 4, 1), ('q', 40, 42, 2, 2),
    ('r', 62, 9, 1, 4), ('y', 62, 30, 1, 4), ('p', 59, 40, 3, 3),
    ('X', 36, 9, 3, 3), ('c', 40, 9, 1, 1), ('c', 41, 9, 1, 1), ('c', 40, 10, 1, 1),
    ('o', 50, 12, 3, 3), ('v', 42, 17, 4, 2), ('m', 54, 20, 3, 3), ('b', 33, 21, 3, 2),
    ('c', 47, 25, 1, 1), ('c', 48, 25, 1, 1), ('c', 48, 26, 1, 1), ('z', 38, 29, 3, 2),
    ('B', 54, 31, 3, 3), ('g', 29, 31, 2, 2), ('X', 12, 34, 3, 3), ('c', 21, 34, 1, 1), ('c', 22, 34, 1, 1),
    ('b', 46, 36, 3, 2), ('m', 22, 38, 3, 3),
], spawns=[(8, 4), (32, 5), (50, 6), (60, 8), (5, 19), (28, 13), (47, 21), (59, 24), (33, 27), (7, 33),
           (19, 30), (52, 37), (42, 25)],
    ammo=[(30, 17), (57, 16)], health=[(9, 39), (44, 33)])

# ---------------------------------------------------------------- dining: table and chairs under a pendant lamp in the
# middle, sideboard and windows on the north wall, a reading corner, laundry and toys
DINING = dict(w=64, h=48, P=(32, 44), items=[
    ('U', 8, 1, 10, 3), ('W', 19, 1, 9, 1), ('W', 37, 1, 9, 1), ('Q', 47, 1, 6, 2), ('p', 55, 1, 3, 3),
    ('u', 22, 4, 2, 2), ('u', 40, 4, 2, 2),
    ('d', 25, 13, 3, 3), ('d', 30, 13, 3, 3), ('d', 35, 13, 3, 3),
    ('D', 26, 16, 10, 6),
    ('C', 25, 22, 3, 3), ('C', 30, 22, 3, 3), ('C', 35, 22, 3, 3),
    ('w', 8, 46, 9, 1), ('w', 44, 46, 9, 1), ('x', 1, 12, 1, 4), ('f', 1, 30, 1, 4), ('w', 62, 20, 1, 9),
    ('O', 50, 30, 2, 2), ('L', 58, 26, 2, 2), ('p', 4, 4, 3, 3), ('q', 59, 42, 2, 2),
    ('B', 9, 11, 3, 3), ('m', 13, 19, 3, 3), ('c', 6, 27, 1, 1), ('c', 7, 27, 1, 1), ('c', 7, 28, 1, 1),
    ('X', 17, 31, 3, 3), ('o', 45, 10, 3, 3), ('v', 50, 17, 4, 2), ('z', 40, 27, 3, 2),
    ('b', 21, 38, 3, 2), ('g', 36, 34, 2, 2), ('c', 53, 36, 1, 1), ('c', 54, 36, 1, 1), ('m', 8, 37, 3, 3),
    ('X', 47, 40, 3, 3), ('b', 12, 25, 3, 2),
], spawns=[(4, 9), (20, 7), (33, 6), (50, 6), (60, 11), (6, 22), (21, 15), (43, 20), (58, 18), (10, 31),
           (27, 29), (44, 32), (56, 33), (16, 6)],
    ammo=[(30, 27), (55, 24)], health=[(4, 41), (41, 40)])

# ---------------------------------------------------------------- kitchen: counters and the fridge along the north
# wall, a big island with stools, windows west and east, a spill of toys and shopping
KITCHEN = dict(w=64, h=46, P=(32, 42), items=[
    ('k', 6, 1, 12, 4), ('R', 19, 1, 5, 4), ('k', 37, 1, 15, 4), ('p', 53, 1, 3, 3), ('Q', 57, 1, 6, 2),
    ('W', 1, 9, 1, 9), ('W', 1, 27, 1, 9), ('w', 62, 14, 1, 9), ('u', 4, 12, 2, 2), ('u', 4, 30, 2, 2),
    ('I', 26, 13, 12, 6), ('j', 27, 20, 2, 2), ('j', 31, 20, 2, 2), ('j', 35, 20, 2, 2),
    ('r', 10, 44, 4, 1), ('y', 46, 44, 4, 1), ('q', 22, 42, 2, 2), ('L', 58, 40, 2, 2),
    ('B', 10, 9, 3, 3), ('X', 46, 9, 3, 3), ('g', 15, 16, 2, 2), ('c', 20, 13, 1, 1), ('c', 21, 13, 1, 1),
    ('c', 20, 14, 1, 1), ('o', 45, 18, 3, 3), ('z', 52, 13, 3, 2), ('v', 12, 23, 4, 2), ('m', 39, 25, 3, 3),
    ('b', 22, 27, 3, 2), ('X', 52, 27, 3, 3), ('c', 31, 30, 1, 1), ('c', 32, 30, 1, 1), ('c', 31, 31, 1, 1),
    ('B', 14, 33, 3, 3), ('g', 45, 33, 2, 2), ('v', 24, 36, 4, 2), ('m', 50, 37, 3, 3), ('b', 7, 39, 3, 2),
    ('o', 36, 37, 3, 3),
], spawns=[(4, 6), (27, 7), (45, 6), (60, 6), (8, 20), (22, 20), (42, 22), (58, 21), (17, 29), (34, 26),
           (47, 30), (59, 33), (6, 33)],
    ammo=[(29, 25), (56, 17)], health=[(12, 30), (43, 40)])

ROOMS = (('livingroom_lounge', LOUNGE), ('livingroom_dining', DINING), ('livingroom_kitchen', KITCHEN))


def main():
    for name, R in ROOMS:
        g = room(R['w'], R['h'], R['items'], R['spawns'], R['P'], R['ammo'], R['health'])
        check(name, g)
        with open(os.path.join(OUT, name + '.txt'), 'w') as f:
            f.write('\n'.join(''.join(row) for row in g) + '\n')
        print('wrote', name, '%dx%d' % (R['w'], R['h']))


if __name__ == '__main__':
    main()
