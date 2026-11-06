#!/usr/bin/env python3
"""INKBOLT industrial zones: hand-placed layouts for the Deep Coal Mine (coalmine_*) and the Robot Works
(factory_*) themes -> src/data/zones/<name>.txt

    python3 tools/industrial_zones.py            # write + validate + print every map
    python3 tools/industrial_zones.py --check    # validate the files on disk only
    python3 tools/industrial_zones.py coalmine   # one theme

Every placement below is deliberate: each zone starts as an open floor inside its rock / wall border, then gets its
rock masses, drifts or halls, landmark, lanes, cover clusters, lights, spawn cans and pickups.
Symbols: see src/data/themes/coalmine.js and src/data/themes/factory.js.
Validation (mirrors tests/unit/theme_<id>.test.js): size, gates (3 wide, two open rows in front of the exit, one in
front of the entry), P -> exit path, 10-14 spawns reachable, >= 14 m from P, 3x3 clear, 2-3 ammo and health,
prefab blocks tile exactly, same-kind light pools never overlap, drifts cut through rock on both sides.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))

THEMES = {
    'coalmine': {
        'prefab': {'Y': (6, 1), 'y': (6, 1), 'C': (1, 2), 'O': (2, 2), 'X': (2, 2), 'T': (8, 5), 'H': (6, 6),
                   'Z': (6, 4), 'Q': (5, 4), 'w': (2, 2), 'd': (2, 2)},
        'solid': set('#cuObl=LXIkTHZQC'),        # cells nobody stands in (prefabs counted whole); Y/y drifts, rails, decals walkable
        'lights': {'l': 5.0, 'L': 6.0},            # min distance between two lights of the same kind (pool radius x 2)
    },
    'factory': {
        'prefab': {'A': (8, 4), 'R': (2, 2), 'p': (2, 2), 'K': (2, 8), 'T': (10, 8), 'B': (8, 6), 'Q': (6, 2),
                   'M': (3, 2), 'z': (2, 2), 'W': (4, 4)},
        'solid': set('#=ARcpbgTBQMxW'),
        'lights': {},
    },
}


class Zone:
    def __init__(self, theme, name, w, h, gate, entry):
        self.theme, self.name, self.w, self.h = theme, name, w, h
        self.g = [['.'] * w for _ in range(h)]
        for c in range(w):
            self.g[0][c] = '#'
            self.g[h - 1][c] = '#'
        for r in range(h):
            self.g[r][0] = '#'
            self.g[r][w - 1] = '#'
        for k in range(3):
            self.g[0][gate + k] = 'G'
            self.g[h - 1][entry + k] = 'E'

    def at(self, c, r):
        return self.g[r][c] if 0 <= c < self.w and 0 <= r < self.h else '#'

    def rect(self, c0, r0, w, h, ch='#'):
        """Overwrite (rock masses, carving floor back with '.')."""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 < c < self.w - 1 and 0 < r < self.h - 1, (self.name, c, r)
                self.g[r][c] = ch

    def put(self, c, r, ch):
        assert self.g[r][c] == '.', '%s: (%d,%d) is %r, not floor (placing %r)' % (self.name, c, r, self.g[r][c], ch)
        self.g[r][c] = ch

    def puts(self, pts, ch):
        for c, r in pts:
            self.put(c, r, ch)

    def block(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] == '.', '%s: block %r at (%d,%d) hits %r' % (self.name, ch, c, r, self.g[r][c])
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.g[r][c] = ch

    def run(self, c0, r0, n, ch, vertical=False):
        for k in range(n):
            self.put(c0, r0 + k, ch) if vertical else self.put(c0 + k, r0, ch)

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


# ---------------------------------------------------------------- validation
def blocks(g, ch):
    H, W = len(g), len(g[0])
    used = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if used[r][c] or g[r][c] != ch:
                continue
            w = 1
            while c + w < W and not used[r][c + w] and g[r][c + w] == ch:
                w += 1
            h = 1
            while r + h < H and all(not used[r + h][c + k] and g[r + h][c + k] == ch for k in range(w)):
                h += 1
            for y in range(h):
                for x in range(w):
                    used[r + y][c + x] = True
            out.append((c, r, w, h))
    return out


def validate(z):
    T = THEMES[z.theme]
    SOLID = T['solid']
    errs = []
    g = z.g
    if not (44 <= z.w <= 60 and 40 <= z.h <= 56):
        errs.append('size %dx%d' % (z.w, z.h))
    G = [c for c in range(z.w) if g[0][c] == 'G']
    E = [c for c in range(z.w) if g[z.h - 1][c] == 'E']
    if len(G) != 3 or G[2] - G[0] != 2 or len(E) != 3 or E[2] - E[0] != 2:
        errs.append('gates')
    for c in G:
        if g[1][c] in SOLID or g[2][c] in SOLID:
            errs.append('exit not open at col %d' % c)
    for c in E:
        if g[z.h - 2][c] in SOLID:
            errs.append('entry not open at col %d' % c)
    P = [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] == 'P']
    if len(P) != 1:
        errs.append('P count %d' % len(P))
        return errs, {}
    P = P[0]
    dist = {P: 0}
    q = deque([P])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if n[0] < 1 or n[1] < 1 or n[0] >= z.w - 1 or n[1] >= z.h - 1 or n in dist or g[n[1]][n[0]] in SOLID:
                continue
            dist[n] = dist[(c, r)] + 1
            q.append(n)
    if not any((c, 1) in dist for c in G):
        errs.append('P does not reach the exit')
    S = [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] == 'S']
    if not 10 <= len(S) <= 14:
        errs.append('spawns %d' % len(S))
    for (c, r) in S:
        if (c - P[0]) ** 2 + (r - P[1]) ** 2 < 14 ** 2:
            errs.append('spawn %d,%d near P' % (c, r))
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dc or dr) and z.at(c + dc, r + dr) in SOLID:
                    errs.append('spawn %d,%d not 3x3 open' % (c, r))
        if not any((c + dc, r + dr) in dist for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            errs.append('spawn %d,%d unreachable' % (c, r))
    na = sum(row.count('a') for row in g)
    nh = sum(row.count('h') for row in g)
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for ch, (sw, sd) in T['prefab'].items():
        for (c, r, w, h) in blocks(g, ch):
            if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                errs.append('%s block %dx%d at %d,%d' % (ch, w, h, c, r))
    for ch, dmin in T['lights'].items():
        pts = [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] == ch]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2 < dmin ** 2:
                    errs.append('lights %s too close %s %s' % (ch, pts[i], pts[j]))
    # coal mine drifts: rock along both long sides of every timber-set block
    for ch in ('Y', 'y'):
        if ch not in T['prefab'] or z.theme != 'coalmine':
            continue
        for (c, r, w, h) in blocks(g, ch):
            if w == 6:
                sides = [(c - 1, rr) for rr in range(r, r + h)] + [(c + 6, rr) for rr in range(r, r + h)]
            else:
                sides = [(cc, r - 1) for cc in range(c, c + w)] + [(cc, r + 6) for cc in range(c, c + w)]
            if any(z.at(*p) != '#' for p in sides):
                errs.append('drift %s at %d,%d not cut through rock' % (ch, c, r))
    # interior walls at least 2 thick (a 1-thick wall would show a module's back)
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if g[r][c] != '#':
                continue
            if (g[r - 1][c] not in '#GE' and g[r + 1][c] not in '#GE') or (g[r][c - 1] not in '#GE' and g[r][c + 1] not in '#GE'):
                errs.append('1-thick wall at %d,%d' % (c, r))
    reach = len(dist)
    opencells = sum(1 for r in range(1, z.h - 1) for c in range(1, z.w - 1) if g[r][c] not in SOLID)
    st = {'size': '%dx%d' % (z.w, z.h), 'spawns': len(S), 'reach': '%d/%d' % (reach, opencells)}
    return errs, st


# ================================================================ COAL MINE
def coal_haulage():
    """Zone 1, Haulage Way: the south loading chamber, a pillared hall with the coal hopper on the main line and a
    rock band crossed by two timbered drifts (the west one carries the track) into the north gallery."""
    z = Zone('coalmine', 'coalmine_haulage', 56, 50, 27, 27)
    # ragged cave outline
    for rc in ((1, 1, 6, 2), (1, 3, 2, 3), (49, 1, 6, 3), (53, 4, 2, 2), (1, 45, 5, 4), (1, 42, 2, 3), (50, 45, 5, 4),
               (53, 41, 2, 4), (1, 15, 2, 4), (53, 14, 2, 3), (53, 34, 2, 3)):
        z.rect(*rc)
    # north rock band with two drifts
    z.rect(1, 8, 54, 7)
    z.rect(11, 8, 6, 7, 'y')
    z.rect(39, 8, 6, 7, 'Y')
    z.rect(25, 7, 7, 1)          # a buttress over the band's middle
    # pillars in the hall
    z.rect(22, 25, 6, 6)
    z.rect(41, 27, 6, 5)
    z.rect(4, 26, 5, 5)
    # main line: north gallery stub, through the west drift, down the hall; the hopper spur east
    z.block(14, 2, 1, 2, 'C')
    z.run(14, 4, 4, '-', vertical=True)
    z.run(14, 15, 7, '-', vertical=True)
    z.block(14, 22, 1, 2, 'C')
    z.run(14, 24, 10, '-', vertical=True)
    z.block(14, 34, 1, 2, 'C')
    z.run(14, 36, 3, '-', vertical=True)
    z.block(31, 18, 6, 4, 'Z')
    z.run(16, 19, 15, '-')
    z.run(37, 19, 11, '-')
    z.block(48, 19, 2, 1, 'C')
    # north gallery cover
    z.puts([(20, 3), (21, 3), (20, 4)], 'c')
    z.puts([(35, 4), (36, 4)], 'u')
    z.run(44, 3, 3, '=')
    z.puts([(8, 5), (50, 6)], 'b')
    z.put(24, 5, 'l')
    z.put(40, 2, 'l')
    # hall
    z.block(9, 17, 2, 2, 'X')
    z.block(44, 21, 2, 2, 'X')
    z.block(33, 33, 2, 2, 'X')
    z.puts([(20, 22), (38, 25), (29, 36)], 'I')
    z.block(18, 16, 2, 2, 'O')
    z.block(38, 15, 2, 2, 'O')
    z.puts([(24, 21), (25, 21), (25, 22)], 'c')
    z.puts([(34, 25), (35, 25)], 'u')
    z.run(4, 21, 3, '=')
    z.run(48, 25, 3, '=')
    z.puts([(19, 30), (19, 31), (36, 29)], 'c')
    z.puts([(10, 33), (47, 35)], 'b')
    z.run(28, 33, 3, '=')
    z.block(6, 35, 2, 2, 'O')
    z.puts([(9, 23), (49, 23), (30, 15), (35, 29)], 'l')
    z.puts([(21, 34), (46, 38), (8, 39)], 'L')
    z.block(40, 34, 2, 2, 'w')
    z.block(10, 28, 2, 2, 'd')
    # south loading chamber
    z.puts([(21, 42), (22, 42), (21, 43)], 'c')
    z.puts([(34, 42), (35, 42), (35, 43)], 'c')
    z.run(10, 44, 3, '=')
    z.puts([(45, 43), (46, 43)], 'u')
    z.block(17, 45, 2, 2, 'w')
    z.put(28, 46, 'P')
    # spawns, pickups
    z.puts([(6, 4), (31, 3), (47, 5), (8, 21), (26, 16), (39, 23), (50, 16), (18, 27), (33, 28), (49, 29), (10, 37), (40, 38)], 'S')
    z.puts([(23, 37), (44, 4)], 'a')
    z.puts([(6, 31), (36, 17)], 'h')
    z.put(30, 40, 'a')
    return z


def coal_face():
    """Zone 2, The Coal Face: the drill rig works the north face behind a line of cribs; belt conveyors carry the
    coal east past heaps and carts; a long timbered cross-drift cuts the west rock mass."""
    z = Zone('coalmine', 'coalmine_face', 58, 52, 42, 27)
    for rc in ((1, 1, 4, 3), (1, 4, 2, 3), (53, 1, 4, 2), (55, 3, 2, 3), (1, 47, 6, 4), (1, 44, 3, 3), (51, 46, 6, 5),
               (54, 42, 3, 4), (55, 20, 2, 5), (1, 36, 2, 4)):
        z.rect(*rc)
    # coal face (north wall stays straight from col 5 to 40): drill rig at the face, cribs along it
    z.block(9, 1, 8, 5, 'T')
    z.block(24, 3, 2, 2, 'X')
    z.block(33, 3, 2, 2, 'X')
    z.puts([(20, 2), (29, 2)], 'I')
    z.block(5, 7, 2, 2, 'O')
    # belt conveyor from the face east (gaps to cross)
    z.run(10, 10, 8, 'k')
    z.run(21, 10, 9, 'k')
    z.run(34, 10, 7, 'k')
    z.block(41, 9, 2, 2, 'O')
    z.block(46, 5, 2, 2, 'O')
    # west rock mass with the cross-drift (rows 24-29), rock over and under it
    z.rect(1, 21, 22, 12)
    z.rect(8, 21, 6, 12, 'Y')
    z.rect(15, 18, 7, 3)
    # east: rails with carts and a pillar
    z.rect(38, 24, 7, 6)
    z.run(49, 13, 8, '-', vertical=True)
    z.block(49, 21, 1, 2, 'C')
    z.run(49, 23, 6, '-', vertical=True)
    z.block(49, 29, 1, 2, 'C')
    z.run(49, 31, 6, '-', vertical=True)
    z.block(52, 28, 2, 2, 'O')
    # middle: cover
    z.puts([(28, 18), (29, 18), (28, 19)], 'c')
    z.run(33, 19, 3, '=')
    z.puts([(26, 26), (27, 26)], 'u')
    z.puts([(30, 33), (31, 33), (31, 34)], 'c')
    z.block(25, 38, 2, 2, 'X')
    z.puts([(17, 13), (44, 16), (14, 37)], 'b')
    z.block(9, 38, 2, 2, 'O')
    z.run(36, 38, 3, '=')
    z.puts([(19, 41), (20, 41)], 'u')
    z.puts([(43, 40), (44, 40), (43, 41)], 'c')
    z.puts([(34, 30), (21, 16)], 'I')
    # lights
    z.puts([(6, 12), (31, 14), (45, 12), (27, 22), (36, 34), (15, 40)], 'l')
    z.puts([(19, 6), (41, 20), (8, 35), (46, 44)], 'L')
    z.block(16, 34, 2, 2, 'w')
    z.block(52, 34, 2, 2, 'w')
    z.block(37, 6, 2, 2, 'd')
    z.block(23, 12, 2, 2, 'd')
    z.put(28, 48, 'P')
    z.puts([(4, 15), (24, 7), (37, 14), (53, 9), (13, 16), (32, 23), (46, 21), (8, 42), (30, 29), (54, 37), (24, 31), (44, 37)], 'S')
    z.puts([(44, 33), (26, 34)], 'a')
    z.puts([(24, 28), (40, 6)], 'h')
    return z


def coal_shaft():
    """Zone 3, Main Shaft: through the south drifts into the shaft chamber: the headframe over the pit, the foreman's
    shack, and wide overlooks east and west into the dark of the old workings."""
    z = Zone('coalmine', 'coalmine_shaft', 56, 54, 26, 29)
    for rc in ((1, 1, 5, 3), (1, 4, 3, 2), (50, 1, 5, 4), (52, 5, 3, 2), (1, 49, 4, 4), (51, 49, 4, 4)):
        z.rect(*rc)
    # south rock band (rows 36-42) with a central rail drift and a west plain drift
    z.rect(1, 36, 54, 7)
    z.rect(27, 36, 6, 7, 'y')
    z.rect(8, 36, 6, 7, 'Y')
    z.rect(43, 36, 6, 7, 'Y')
    # track: south chamber -> central drift (track col 30) -> shaft landing
    z.run(30, 43, 5, '-', vertical=True)
    z.block(30, 31, 1, 2, 'C')
    z.run(30, 26, 5, '-', vertical=True)
    z.run(30, 33, 3, '-', vertical=True)
    # headframe (landing gate faces south, toward the track end)
    z.block(27, 17, 6, 6, 'H')
    z.block(10, 6, 5, 4, 'Q')
    # pillars
    z.rect(10, 22, 6, 6)
    z.rect(42, 14, 5, 6)
    z.rect(18, 1, 4, 3)
    # cover
    z.block(20, 12, 2, 2, 'X')
    z.block(38, 25, 2, 2, 'X')
    z.puts([(24, 25), (36, 15), (19, 30)], 'I')
    z.puts([(36, 6), (37, 6), (37, 7)], 'c')
    z.run(22, 8, 3, '=')
    z.puts([(45, 9), (46, 9)], 'u')
    z.block(5, 13, 2, 2, 'O')
    z.block(48, 23, 2, 2, 'O')
    z.puts([(6, 30), (6, 31), (7, 31)], 'c')
    z.run(42, 30, 3, '=')
    z.puts([(22, 32), (36, 32)], 'b')
    z.puts([(17, 18), (39, 20)], 'u')
    # south chamber
    z.puts([(20, 45), (21, 45), (20, 46)], 'c')
    z.puts([(38, 46), (39, 46)], 'u')
    z.run(9, 47, 3, '=')
    z.puts([(46, 45)], 'b')
    # lights
    z.puts([(24, 15), (35, 27), (7, 19), (47, 27), (24, 4), (41, 3), (19, 33)], 'l')
    z.puts([(16, 11), (45, 33), (10, 33), (33, 47)], 'L')
    z.block(31, 9, 2, 2, 'w')
    z.block(15, 46, 2, 2, 'w')
    z.block(41, 21, 2, 2, 'd')
    z.put(31, 50, 'P')
    z.puts([(6, 8), (29, 5), (46, 4), (7, 25), (22, 20), (37, 11), (50, 16), (17, 29), (34, 24), (51, 29), (26, 31), (43, 25)], 'S')
    z.puts([(24, 21), (48, 12), (17, 44)], 'a')
    z.puts([(35, 21), (11, 17)], 'h')
    return z


# ================================================================ FACTORY
def fac_lines():
    """Zone 1, Assembly Hall: two long assembly lines (Crawler, Gunner, Bomber, Drone sections) with a cross aisle,
    feeder conveyors, robot arm cells, an overhead catwalk along the east wall and a machine room in the south-west."""
    z = Zone('factory', 'factory_lines', 56, 52, 27, 27)
    # machine room (block walls) south-west, store bay north-east
    z.rect(1, 37, 8, 9)
    z.rect(46, 1, 9, 5)
    # line 1 (north), split by the cross aisle
    z.block(4, 10, 24, 4, 'A')
    z.block(34, 10, 16, 4, 'A')
    # line 2 (south)
    z.block(12, 25, 16, 4, 'A')
    z.block(34, 25, 16, 4, 'A')
    # feeder conveyors and arm cells
    z.run(6, 19, 9, '=')
    z.run(38, 19, 10, '=')
    z.block(30, 16, 2, 2, 'R')
    z.block(24, 20, 2, 2, 'R')
    z.block(30, 31, 2, 2, 'R')
    z.block(5, 25, 2, 2, 'R')
    # catwalk along the east wall (overhead), hazard pads under the arms
    z.block(52, 8, 2, 32, 'K')
    z.block(30, 18, 2, 2, 'z')
    z.block(24, 22, 2, 2, 'z')
    # machines and parts
    z.block(10, 31, 3, 2, 'M')
    z.block(42, 33, 3, 2, 'M')
    z.block(14, 4, 2, 2, 'p')
    z.block(19, 4, 2, 2, 'p')
    z.block(38, 4, 2, 2, 'p')
    z.puts([(9, 5), (10, 5), (9, 6)], 'c')
    z.puts([(32, 3), (33, 3)], 'b')
    z.puts([(42, 7), (16, 34)], 'g')
    z.puts([(20, 35), (21, 35), (21, 36)], 'c')
    z.puts([(36, 36), (37, 36)], 'c')
    z.block(46, 41, 2, 2, 'p')
    z.puts([(14, 44), (15, 44), (40, 45)], 'c')
    z.puts([(10, 23), (46, 23)], 'x')
    z.puts([(23, 40), (34, 41)], 'b')
    z.put(28, 48, 'P')
    z.puts([(6, 3), (27, 6), (44, 8), (8, 16), (26, 16), (48, 16), (17, 22), (36, 22), (4, 31), (24, 32), (49, 30), (39, 39)], 'S')
    z.puts([(31, 22), (13, 40)], 'a')
    z.puts([(20, 8), (47, 37)], 'h')
    return z


def fac_press():
    """Zone 2, Press Shop: the giant press and its forge in the middle of the hall, test cages either side, racks of
    finished robots along the walls, machine tools, parts pallets, a catwalk over the west aisle."""
    z = Zone('factory', 'factory_press', 58, 52, 28, 27)
    z.rect(1, 1, 6, 6)
    z.rect(51, 44, 6, 7)
    z.block(24, 14, 10, 8, 'T')
    z.block(16, 13, 2, 2, 'z')
    z.block(10, 6, 4, 4, 'W')
    z.block(44, 9, 4, 4, 'W')
    z.block(12, 28, 4, 4, 'W')
    z.block(38, 1, 6, 2, 'Q')
    z.block(14, 1, 6, 2, 'Q')
    z.block(50, 26, 6, 2, 'Q')
    z.block(6, 22, 2, 16, 'K')
    z.block(40, 27, 3, 2, 'M')
    z.block(30, 33, 3, 2, 'M')
    z.block(46, 18, 3, 2, 'M')
    z.block(20, 37, 2, 2, 'p')
    z.block(36, 38, 2, 2, 'p')
    z.block(2, 40, 2, 2, 'p')
    z.run(22, 27, 6, '=')
    z.run(38, 22, 6, '=')
    z.puts([(35, 12), (36, 12), (35, 11)], 'c')
    z.puts([(21, 10), (52, 14)], 'b')
    z.puts([(17, 22), (48, 35)], 'g')
    z.puts([(25, 41), (26, 41), (26, 42)], 'c')
    z.puts([(44, 42), (45, 42)], 'c')
    z.puts([(9, 46), (41, 33)], 'x')
    z.block(30, 25, 2, 2, 'z')
    z.put(28, 48, 'P')
    z.puts([(4, 9), (26, 6), (50, 5), (9, 18), (40, 16), (54, 20), (3, 27), (20, 31), (46, 30), (33, 30), (11, 37), (52, 38)], 'S')
    z.puts([(36, 19), (16, 35)], 'a')
    z.puts([(22, 18), (47, 39)], 'h')
    return z


def fac_dispatch():
    """Zone 3, Control & Dispatch: the raised control booth over the floor, the last line finishing Drones and
    Bombers, racks of robots ready to ship, test cages, a catwalk ring and the dispatch gate."""
    z = Zone('factory', 'factory_dispatch', 56, 54, 26, 27)
    z.rect(1, 47, 7, 6)
    z.rect(48, 47, 7, 6)
    z.rect(22, 30, 4, 4)
    z.rect(32, 30, 4, 4)
    z.block(24, 14, 8, 6, 'B')
    z.block(6, 8, 16, 4, 'A')
    z.block(36, 8, 16, 4, 'A')
    z.block(8, 40, 6, 2, 'Q')
    z.block(42, 40, 6, 2, 'Q')
    z.block(1, 22, 6, 2, 'Q')
    z.block(44, 22, 4, 4, 'W')
    z.block(10, 26, 4, 4, 'W')
    z.block(38, 16, 2, 8, 'K')
    z.block(16, 16, 2, 8, 'K')
    z.run(4, 18, 8, '=')
    z.run(44, 18, 8, '=')
    z.block(27, 35, 2, 2, 'R')
    z.block(28, 24, 2, 2, 'z')
    z.block(19, 33, 3, 2, 'M')
    z.block(38, 34, 3, 2, 'M')
    z.block(50, 30, 2, 2, 'p')
    z.block(3, 31, 2, 2, 'p')
    z.puts([(30, 4), (31, 4), (30, 5)], 'c')
    z.puts([(4, 4), (5, 4)], 'b')
    z.puts([(52, 4), (20, 22)], 'g')
    z.puts([(24, 44), (25, 44), (24, 45)], 'c')
    z.puts([(35, 44), (36, 44)], 'c')
    z.puts([(15, 34), (44, 30)], 'x')
    z.puts([(31, 26)], 'b')
    z.put(27, 50, 'P')
    z.puts([(4, 15), (25, 6), (50, 15), (13, 21), (34, 22), (45, 33), (7, 36), (21, 27), (52, 26), (41, 4), (12, 4), (30, 31)], 'S')
    z.puts([(35, 19), (16, 37)], 'a')
    z.puts([(23, 23), (49, 38)], 'h')
    return z


ZONES = {'coalmine': [coal_haulage, coal_face, coal_shaft], 'factory': [fac_lines, fac_press, fac_dispatch]}


def main(argv):
    themes = [a for a in argv if not a.startswith('-')] or list(ZONES)
    ok = True
    for th in themes:
        for fn in ZONES[th]:
            z = fn()
            errs, st = validate(z)
            print('%s  %s' % (z.name, '  '.join('%s=%s' % kv for kv in st.items())))
            if '--quiet' not in argv:
                print(z.text())
            for e in errs:
                print('  ERROR', e)
            ok = ok and not errs
            if '--check' not in argv:
                with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                    f.write(z.text())
    print('OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
