#!/usr/bin/env python3
"""INKBOLT zone generator: big open city-block zones for theme kits (ASCII, 1 char = 1 m).

    python3 tools/gen_zones.py            # (re)writes src/data/zones/tt_*.txt from the ZONES table below

Symbols (brief 5.12 + E): # wall/building, = low wall, c crate, C container (2x2), T landmark (3x3),
p billboard (no collision), S spawn can, P entry/respawn, E entry gate (south edge), G exit gate (north edge),
a ammo, h health, . floor.
Every zone is validated: P -> G path, every spawn reachable and >= 14 m from P, enough cover, no sealed areas.
"""
import os
import random
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))
BLOCK = set('#=cCT')

# name, width, height, seed, buildings, spawns, landmark
ZONES = [
    ('tt_main_street', 58, 46, 11, 7, 12, True),
    ('tt_market', 54, 50, 23, 8, 12, False),
    ('tt_depot', 60, 48, 37, 6, 14, True),
    ('tt_rail_yard', 60, 44, 41, 5, 13, False),
    ('tt_billboard_row', 56, 50, 53, 8, 13, True),
    ('tt_water_works', 58, 52, 67, 7, 14, True),
]


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def get(self, c, r):
        return self.g[r][c] if 0 <= c < self.w and 0 <= r < self.h else '#'

    def set(self, c, r, ch):
        if 0 <= c < self.w and 0 <= r < self.h:
            self.g[r][c] = ch

    def rect_free(self, c0, r0, w, h, pad=0):
        for r in range(r0 - pad, r0 + h + pad):
            for c in range(c0 - pad, c0 + w + pad):
                if self.get(c, r) != '.' or (c, r) in self.reserved:
                    return False
        return True

    def fill(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.set(c, r, ch)

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


def bfs(grid, start):
    seen = {start}
    q = deque([start])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if n in seen:
                continue
            ch = grid.get(*n)
            if ch in BLOCK or (ch == '#'):
                continue
            if ch in 'EG' and n[1] not in (0, grid.h - 1):
                continue
            seen.add(n)
            q.append(n)
    return seen


def make_zone(w, h, seed, n_build, n_spawn, landmark):
    rnd = random.Random(seed)
    for attempt in range(200):
        G = Grid(w, h)
        G.reserved = set()
        # perimeter
        for c in range(w):
            G.set(c, 0, '#'); G.set(c, h - 1, '#')
        for r in range(h):
            G.set(0, r, '#'); G.set(w - 1, r, '#')
        ex = rnd.randint(w // 2 - 4, w // 2 + 2)          # entry gate column (3 wide)
        gx = rnd.randint(6, w - 9)                        # exit gate column (3 wide)
        for k in range(3):
            G.set(ex + k, h - 1, 'E'); G.set(gx + k, 0, 'G')
        P = (ex + 1, h - 4)
        # keep lanes in front of gates and around the entry clear
        for r in range(h - 9, h - 1):
            for c in range(ex - 3, ex + 6):
                G.reserved.add((c, r))
        for r in range(1, 7):
            for c in range(gx - 2, gx + 5):
                G.reserved.add((c, r))
        # perimeter buildings: deepen the boundary with shop blocks along the edges (varied depth)
        c = 1
        while c < w - 1:
            seg = rnd.randint(4, 9); depth = rnd.choice([0, 0, 2, 3, 4])
            for cc in range(c, min(w - 1, c + seg)):
                for d in range(1, depth + 1):
                    if (cc, d) not in G.reserved and abs(cc - gx - 1) > 3:
                        G.set(cc, d, '#')
                    if (cc, h - 1 - d) not in G.reserved and abs(cc - ex - 1) > 4:
                        G.set(cc, h - 1 - d, '#')
            c += seg
        r = 1
        while r < h - 1:
            seg = rnd.randint(4, 9); depth = rnd.choice([0, 0, 2, 3])
            for rr in range(r, min(h - 1, r + seg)):
                for d in range(1, depth + 1):
                    if (d, rr) not in G.reserved:
                        G.set(d, rr, '#')
                    if (w - 1 - d, rr) not in G.reserved:
                        G.set(w - 1 - d, rr, '#')
            r += seg
        # landmark plaza
        if landmark:
            for _ in range(80):
                c0, r0 = rnd.randint(10, w - 14), rnd.randint(9, h - 16)
                if G.rect_free(c0 - 2, r0 - 2, 7, 7):
                    G.fill(c0, r0, 3, 3, 'T')
                    for rr in range(r0 - 3, r0 + 6):
                        for cc in range(c0 - 3, c0 + 6):
                            G.reserved.add((cc, rr))
                    break
        # building blocks with streets >= 4 m between them
        placed = 0
        for _ in range(400):
            if placed >= n_build:
                break
            bw, bh = rnd.randint(5, 11), rnd.randint(4, 8)
            c0, r0 = rnd.randint(4, w - bw - 4), rnd.randint(4, h - bh - 6)
            if G.rect_free(c0, r0, bw, bh, pad=4):
                G.fill(c0, r0, bw, bh, '#')
                # an L-shaped wing sometimes
                if rnd.random() < 0.4:
                    ww, wh = rnd.randint(2, 4), rnd.randint(2, 4)
                    cc = c0 + (bw if rnd.random() < 0.5 else -ww)
                    if G.rect_free(cc, r0, ww, wh, pad=3):
                        G.fill(cc, r0, ww, wh, '#')
                # billboard against a building face
                if rnd.random() < 0.6 and G.get(c0 + bw // 2, r0 + bh) == '.' and (c0 + bw // 2, r0 + bh) not in G.reserved:
                    G.set(c0 + bw // 2, r0 + bh, 'p')
                placed += 1
        # cover: containers, crate clusters, low walls (keep 1 m padding so paths stay open)
        def scatter(n, fn):
            k = 0
            for _ in range(n * 40):
                if k >= n:
                    break
                if fn():
                    k += 1
        def container():
            c0, r0 = rnd.randint(3, w - 6), rnd.randint(3, h - 6)
            if G.rect_free(c0, r0, 2, 2, pad=1):
                G.fill(c0, r0, 2, 2, 'C'); return True
            return False
        def crates():
            c0, r0 = rnd.randint(3, w - 5), rnd.randint(3, h - 5)
            shape = rnd.choice([[(0, 0)], [(0, 0), (1, 0)], [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (0, 1)]])
            if all(G.rect_free(c0 + dc, r0 + dr, 1, 1, pad=1) for dc, dr in shape):
                for dc, dr in shape:
                    G.set(c0 + dc, r0 + dr, 'c')
                return True
            return False
        def lowwall():
            L = rnd.randint(3, 6)
            horiz = rnd.random() < 0.6
            c0, r0 = rnd.randint(3, w - 9), rnd.randint(3, h - 9)
            ww, hh = (L, 1) if horiz else (1, L)
            if G.rect_free(c0, r0, ww, hh, pad=1):
                G.fill(c0, r0, ww, hh, '='); return True
            return False
        area = w * h
        scatter(area // 260, container)
        scatter(area // 110, crates)
        scatter(area // 220, lowwall)
        # spawns: open cells, far from P, spread apart, reachable
        reach = bfs(G, P)
        cand = [(c, r) for (c, r) in reach if G.get(c, r) == '.' and (c, r) not in G.reserved
                and (c - P[0]) ** 2 + (r - P[1]) ** 2 >= 14 ** 2 and 2 <= c < w - 2 and 2 <= r < h - 2]
        rnd.shuffle(cand)
        spawns = []
        for s in cand:
            if all((s[0] - t[0]) ** 2 + (s[1] - t[1]) ** 2 >= 7 ** 2 for t in spawns):
                # spawn can needs its 8 neighbours open so robots can hop out
                if all(G.get(s[0] + dc, s[1] + dr) == '.' for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                    spawns.append(s)
            if len(spawns) >= n_spawn:
                break
        if len(spawns) < n_spawn - 2:
            continue
        for s in spawns:
            G.set(s[0], s[1], 'S')
        # pickups
        opens = [(c, r) for (c, r) in reach if G.get(c, r) == '.' and (c, r) not in G.reserved]
        rnd.shuffle(opens)
        for k, ch in enumerate('aaahh'):
            G.set(opens[k][0], opens[k][1], ch)
        G.set(P[0], P[1], 'P')
        ok, why = validate(G, P)
        if ok:
            return G, attempt
    raise SystemExit('could not generate a valid zone for seed %d (%s)' % (seed, why))


def validate(G, P):
    reach = bfs(G, P)
    gates = [(c, 1) for c in range(G.w) if G.get(c, 0) == 'G']
    if not any(g in reach for g in gates):
        return False, 'no path to exit'
    spawns = [(c, r) for r in range(G.h) for c in range(G.w) if G.get(c, r) == 'S']
    for s in spawns:
        if not any((s[0] + dc, s[1] + dr) in reach for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            return False, 'sealed spawn'
        if (s[0] - P[0]) ** 2 + (s[1] - P[1]) ** 2 < 14 ** 2:
            return False, 'spawn near entry'
    cover = sum(1 for r in range(G.h) for c in range(G.w) if G.get(c, r) in 'cC=')
    if cover < 30:
        return False, 'not enough cover'
    open_cells = sum(1 for r in range(G.h) for c in range(G.w) if G.get(c, r) not in BLOCK)
    if len(reach) < open_cells * 0.92:
        return False, 'sealed pockets'
    return True, ''


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, w, h, seed, nb, ns, lm in ZONES:
        G, attempts = make_zone(w, h, seed, nb, ns, lm)
        with open(os.path.join(OUT, name + '.txt'), 'w') as f:
            f.write(G.text())
        sp = sum(row.count('S') for row in G.g)
        print('%-18s %dx%d  spawns=%d  attempts=%d' % (name, w, h, sp, attempts + 1))


if __name__ == '__main__':
    sys.exit(main())
