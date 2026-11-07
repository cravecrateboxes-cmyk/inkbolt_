#!/usr/bin/env python3
"""Zone maps for the Redwood Hollow theme (src/data/zones/grove_*.txt).

Bumpy garden valleys (the terrain heights come from the theme; walls, gates, spawns and the listed symbols stand on
level ground) with giant climbable redwoods ('Z', 6 x 6). Two redwoods on the same rows are joined by a two-plank
-wide rope bridge at 9 m: '=' cells in the "@layer 9" grid between the trees' east / west limbs.

    python3 tools/grove_zones.py
"""
import os
import random
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data', 'zones')
W, H = 50, 52


class Grid:
    def __init__(self, fill='.'):
        self.g = [[fill] * W for _ in range(H)]

    def free(self, c, r, w=1, h=1, pad=0):
        return all(0 <= x < W and 0 <= y < H and self.g[y][x] == '.' for x in range(c - pad, c + w + pad) for y in range(r - pad, r + h + pad))

    def put(self, c, r, ch, w=1, h=1, pad=0):
        if not self.free(c, r, w, h, pad):
            return False
        for y in range(r, r + h):
            for x in range(c, c + w):
                self.g[y][x] = ch
        return True

    def text(self):
        return '\n'.join(''.join(row) for row in self.g)


def shell():
    g = Grid()
    for c in range(W):
        g.g[0][c] = g.g[H - 1][c] = '#'
    for r in range(H):
        g.g[r][0] = g.g[r][W - 1] = '#'
    cx = W // 2
    for k in (-1, 0, 1):
        g.g[0][cx + k] = 'G'
        g.g[H - 1][cx + k] = 'E'
    g.g[H - 3][cx] = 'P'
    # ridge spurs: a few rock outcrops reaching in from the side walls
    return g


def zone(n):
    rnd = random.Random(100 + n)
    g, up, cx = shell(), Grid(), W // 2
    for r in range(H):
        for c in range(W):
            if g.g[r][c] in '#GE':
                up.g[r][c] = '#'
    # giant redwoods: a bridged pair on the same rows plus a lone tree
    pair_r = [14, 22, 12][n - 1]
    a_c, b_c = [(7, 35), (6, 33), (9, 36)][n - 1]
    g.put(a_c, pair_r, 'Z', 6, 6); g.put(b_c, pair_r, 'Z', 6, 6)
    mid = pair_r + 2                      # bridge rows: the two rows either side of the trees' centre line
    for c in range(a_c + 6, b_c):
        up.g[mid][c] = '='; up.g[mid + 1][c] = '='
    lone = [(21, 32), (20, 8), (19, 31)][n - 1]
    g.put(lone[0], lone[1], 'Z', 6, 6)
    # garden: vegetable beds, pumpkins, a pond, fences, crates
    beds = [((4, 30), (8, 30), (12, 30)), ((5, 36), (9, 36), (40, 8)), ((4, 24), (8, 24), (40, 30))][n - 1]
    for (c, r) in beds:
        g.put(c, r, 'V', 2, 4, pad=1)
    for (c, r) in [((17, 40), (31, 41)), ((28, 38), (16, 12)), ((30, 42), (14, 38))][n - 1]:
        g.put(c, r, 'U', 2, 2, pad=1)
    pond = [(33, 30), (36, 38), (24, 22)][n - 1]
    g.put(pond[0], pond[1], 'W', 4, 4, pad=1)
    for (c, r) in ((3, 29), (3, 35)):
        for k in range(9):
            if g.free(c + k, r):
                g.put(c + k, r, 'f')
    for k in range(4):
        g.put(rnd.randint(3, W - 4), rnd.randint(4, H - 6), 'c', pad=1)
    # trees, bushes, logs, rocks scattered with room around them
    for ch, count, pad in (('o', 7, 4), ('t', 9, 2), ('L', 3, 1), ('r', 10, 1), ('b', 14, 1), ('B', 8, 1), ('s', 6, 1)):
        placed, tries = 0, 0
        while placed < count and tries < 600:
            tries += 1
            c, r = rnd.randint(3, W - 5), rnd.randint(4, H - 6)
            if ch == 'o' and not (5 <= c <= W - 6 and 5 <= r <= H - 7):
                continue                  # oak crowns (3.3 m) stay clear of the ridge walls
            if abs(c - cx) < 3 and r > H - 9:
                continue                  # keep the entry clear
            if ch == 'o' and mid - 5 <= r <= mid + 6 and a_c - 3 <= c <= b_c + 8:
                continue                  # oak crowns (to ~9.6 m) never reach up into the 9 m bridge
            if ch == 'L':
                ok = g.put(c, r, 'L', 3, 1, pad=pad)
            else:
                ok = g.put(c, r, ch, pad=pad)
            placed += ok
    # ground cover (walk-through): grass, reeds, ferns, flowers
    for ch, count in (('g', 70), ('l', 22), ('n', 22), ('w', 40)):
        for _ in range(count):
            c, r = rnd.randint(3, W - 4), rnd.randint(3, H - 4)
            g.put(c, r, ch)
    # spawn cans on level ground, pickups
    for (c, r) in ((5, 6), (W - 6, 6), (cx, 5), (4, H // 2 + 3), (W - 5, H // 2), (14, H - 10), (W - 15, H - 9)):
        for dc in range(0, 6):
            if g.put(c + dc, r, 'S', pad=1):
                break
    for (c, r, ch) in ((cx - 5, H - 8, 'a'), (cx + 6, 20, 'h'), (W - 8, 40, 'a'), (6, 18, 'h')):
        for dc in range(0, 6):
            if g.put(c + dc, r, ch, pad=1):
                break
    return g.text() + '\n@layer 9\n' + up.text() + '\n'


def main(argv):
    for n in (1, 2, 3):
        with open(os.path.join(OUT, 'grove_%d.txt' % n), 'w') as f:
            f.write(zone(n))
        print('wrote grove_%d.txt' % n)


if __name__ == '__main__':
    main(sys.argv[1:])
