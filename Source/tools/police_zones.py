#!/usr/bin/env python3
"""Zone maps for the Strike Team HQ theme (src/data/zones/police_*.txt).

  police_1  Lobby & Briefing: lobby with the star emblem, a briefing room, a first armory corner
  police_2  Armory: weapon walls all round, workbench rows (mods), gear shelves, barricades, holding cells
  police_3  Vehicle Bay & Range: SWAT vans, a firing range with booths and targets, more racks

Weapon racks ('R', 3 x 1) must touch a wall along their long side; the engine turns them to face the room.

    python3 tools/police_zones.py
"""
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data', 'zones')
W, H = 48, 48


class Grid:
    def __init__(self):
        self.g = [['.'] * W for _ in range(H)]
        for c in range(W):
            self.g[0][c] = self.g[H - 1][c] = '#'
        for r in range(H):
            self.g[r][0] = self.g[r][W - 1] = '#'
        cx = W // 2
        for k in (-1, 0, 1):
            self.g[0][cx + k] = 'G'
            self.g[H - 1][cx + k] = 'E'
        self.g[H - 3][cx] = 'P'

    def free(self, c, r, w=1, h=1, pad=0):
        return all(0 <= x < W and 0 <= y < H and self.g[y][x] == '.' for x in range(c - pad, c + w + pad) for y in range(r - pad, r + h + pad))

    def put(self, c, r, ch, w=1, h=1, pad=0):
        if not self.free(c, r, w, h, pad):
            return False
        for y in range(r, r + h):
            for x in range(c, c + w):
                self.g[y][x] = ch
        return True

    def wall_row(self, r, c0, c1, doors):
        for c in range(c0, c1 + 1):
            if not any(d <= c < d + 3 for d in doors):
                self.g[r][c] = '#'

    def wall_col(self, c, r0, r1, doors):
        for r in range(r0, r1 + 1):
            if not any(d <= r < d + 3 for d in doors):
                self.g[r][c] = '#'

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


def racks_north(g, r, c0, c1):
    """racks against the wall above row r, every 4 cells"""
    for c in range(c0, c1 - 2, 4):
        if all(g.g[r - 1][c + k] == '#' for k in range(3)):   # only against solid wall (never in front of a gate)
            g.put(c, r, 'R', 3, 1)


def racks_side(g, c, r0, r1):
    for r in range(r0, r1 - 2, 6):
        side = c - 1 if c == 1 else c + 1
        if all(g.g[r + k][side] == '#' for k in range(3)):
            g.put(c, r, 'R', 1, 3)


def spawns(g, pts):
    for c, r in pts:
        g.put(c, r, 'S', pad=1)


def zone1():
    g = Grid()
    g.wall_row(24, 1, W - 2, (8, 22, 37))                 # lobby / back rooms partition with three doorways
    g.wall_col(17, 1, 23, (10,))                            # briefing room | armory corner
    # lobby (south): emblem, desks (front counter), plants, cabinets, lockers on the side walls
    g.put(22, 32, 'M', 4, 4)
    for c in (10, 14, 32, 36):
        g.put(c, 40, 'd', 2, 1)
    for (c, r) in ((3, 27), (44, 27), (3, 44), (44, 44), (16, 30), (31, 30)):
        g.put(c, r, 'p')
    for r in range(27, 44, 3):
        g.put(1, r, 'l'); g.put(W - 2, r, 'l')
    for c in (6, 40):
        g.put(c, 25, 'f')
    # briefing room (north-west)
    g.put(5, 8, 'T', 4, 2); g.put(5, 14, 'T', 4, 2); g.put(11, 8, 'T', 4, 2); g.put(11, 14, 'T', 4, 2)
    for c in (2, 6, 10):
        g.put(c, 1, 'f')
    # armory corner (north-east): racks on the north and east walls, a workbench and a gear shelf
    racks_north(g, 1, 19, 45)
    racks_side(g, W - 2, 5, 22)
    g.put(24, 10, 'b', 2, 1); g.put(32, 10, 'b', 2, 1)
    g.put(18, 20, 'g', 2, 1); g.put(18, 5, 'g', 1, 2)
    for (c, r) in ((22, 16), (29, 18), (36, 15)):
        g.put(c, r, 'k', 3, 1)
    spawns(g, ((8, 4), (14, 20), (28, 6), (40, 20), (6, 30), (41, 33), (24, 28)))
    g.put(20, 42, 'a'); g.put(30, 14, 'h')
    return g.text()


def zone2():
    g = Grid()
    # weapon walls on all four sides (doors leave the gates clear)
    racks_north(g, 1, 2, 20); racks_north(g, 1, 28, 46)
    racks_side(g, 1, 4, 42); racks_side(g, W - 2, 4, 42)
    for c in range(3, 20, 4):
        g.put(c, H - 2, 'g', 2, 1)
    for c in range(29, 45, 4):
        g.put(c, H - 2, 'g', 2, 1)
    # workbench rows with barricades between them
    for r in (12, 22, 32):
        for c in (10, 16, 30, 36):
            g.put(c, r, 'b', 2, 1, pad=1)
    for r in (17, 27, 37):
        for c in (8, 21, 25, 38):
            g.put(c, r, 'k', 2, 1, pad=1)
    for (c, r) in ((22, 8), (23, 8), (22, 40), (14, 42), (33, 42), (6, 20), (41, 30)):
        g.put(c, r, 'x', pad=1)
    spawns(g, ((6, 6), (41, 6), (6, 40), (41, 40), (23, 14), (24, 34), (13, 27)))
    g.put(24, 24, 'a'); g.put(5, 30, 'h'); g.put(43, 16, 'a')
    return g.text()


def zone3():
    g = Grid()
    # firing range across the north: booth partitions (lane dividers), targets down range
    for c in range(4, 44, 4):
        for r in range(9, 13):
            g.put(c, r, 'y')
        g.put(c + 2, 3, 'Y')
    g.wall_row(14, 1, W - 2, (5, 22, 38))                 # range / bay partition with doorways
    # vehicle bay: SWAT vans, crates, barricades, racks and gear on the side walls
    for (c, r) in ((7, 20), (16, 20), (30, 20), (39, 20), (11, 33), (35, 33)):
        g.put(c, r, 'V', 3, 6, pad=1)
    racks_side(g, 1, 16, 31); racks_side(g, W - 2, 16, 44)
    g.put(1, 35, 'J', 3, 4)                              # holding cells against the west wall
    for (c, r) in ((22, 22), (23, 22), (24, 22), (25, 36), (22, 40), (27, 18)):
        g.put(c, r, 'x', pad=1)
    for (c, r) in ((18, 29), (27, 29), (6, 41), (40, 41)):
        g.put(c, r, 'k', 3, 1, pad=1)
    g.put(23, 44, 'b', 2, 1); g.put(29, 44, 'g', 2, 1)
    spawns(g, ((10, 6), (36, 6), (5, 30), (42, 30), (23, 26), (18, 42), (30, 40)))
    g.put(14, 16, 'a'); g.put(34, 44, 'h'); g.put(24, 7, 'a')
    return g.text()


def main(argv):
    for n, fn in ((1, zone1), (2, zone2), (3, zone3)):
        with open(os.path.join(OUT, 'police_%d.txt' % n), 'w') as f:
            f.write(fn())
        print('wrote police_%d.txt' % n)


if __name__ == '__main__':
    main(sys.argv[1:])
