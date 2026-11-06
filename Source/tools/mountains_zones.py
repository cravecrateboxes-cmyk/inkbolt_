#!/usr/bin/env python3
"""INKBOLT Mountains zones (campaign level 1, "Pine Ridge"): hand-placed layouts -> src/data/zones/mountains_*.txt

    python3 tools/mountains_zones.py          # write + validate + print the three maps
    python3 tools/mountains_zones.py --check  # validate the files on disk only

Every placement below is deliberate (no noise): each zone carves an open valley out of solid cliff ('#'), then adds
its landmark, lanes, cover clusters, spawn cans and pickups. Symbols (src/data/themes/mountains.js):
  # cliff ridge (wall)        % treeline 2x2 (boundary)   o boulder        O outcrop 2x2      = stone wall
  f split-rail fence          x log pile                  c supply crate   t pine             F spruce stand 2x2
  H log cabin 6x5             A A-frame chalet 5x6        T lookout 4x4    Y rope bridge 14x4 J lift station 5x4
  K lift line 3x12            Q campfire 3x3              D snow drift 3x3 M meadow 3x3       W frozen pond 4x4
  w frozen creek 2x2          p signpost / lantern post     k skis in the snow + built-ins S P E G a h .
Validation: P -> exit path, every spawn reachable, >= 14 m from P, 3x3 clear; gates with 2 open rows in front;
prefab blocks tile exactly; cliff modules (2 m deep) have solid cells behind them; the weapon-stand spot is clear.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))
PREFAB = {'%': (2, 2), 'O': (2, 2), 'F': (2, 2), 'H': (6, 5), 'A': (5, 6), 'T': (4, 4), 'Y': (14, 4), 'J': (5, 4), 'K': (3, 12),
          'Q': (3, 3), 'D': (3, 3), 'M': (3, 3), 'W': (4, 4), 'w': (2, 2)}
BLOCKING = set('#%oO=fxctFHATJQSpkY')     # 'Y' refined below (the pass between the towers is open), 'K' only at towers
WALKABLE = set('.PaDMWwhK')


class Z:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.g = [['#'] * w for _ in range(h)]
        self.open_extra = set()   # prefab cells that are walkable (rope bridge pass)

    def rect(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 <= c < self.w and 0 <= r < self.h, (self.name, c, r)
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
        self.rect(c0, r0, w, h, ch)

    def run(self, c0, r0, n, ch, vertical=False):
        for k in range(n):
            if vertical:
                self.put(c0, r0 + k, ch)
            else:
                self.put(c0 + k, r0, ch)

    def at(self, c, r):
        return self.g[r][c] if 0 <= c < self.w and 0 <= r < self.h else '#'

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


# ---------------------------------------------------------------- engine mirrors
def rects(g, ch):
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
            ok = True
            while ok and r + h < H:
                for k in range(w):
                    if used[r + h][c + k] or g[r + h][c + k] != ch:
                        ok = False
                        break
                if ok:
                    h += 1
            for y in range(h):
                for x in range(w):
                    used[r + y][c + x] = True
            out.append((c, r, w, h))
    return out


def walls(zone):
    """Mirror of the theme's wall chooser: which '#' cells get a straight 2 m-deep cliff module vs a pillar."""
    g = zone.g
    solid = lambda c, r: zone.at(c, r) in '#GE'
    mods, pillars, bad = 0, 0, []
    for r in range(zone.h):
        for c in range(zone.w):
            if g[r][c] != '#':
                continue
            exposed = any(not solid(c + dc, r + dr) for dc in (-1, 0, 1) for dr in (-1, 0, 1) if dc or dr)
            if not exposed:
                continue
            o = {'N': not solid(c, r - 1), 'S': not solid(c, r + 1), 'W': not solid(c - 1, r), 'E': not solid(c + 1, r)}
            if sum(o.values()) == 1:
                mods += 1
                d = [k for k, v in o.items() if v][0]
                bc, br = {'N': (c, r + 2), 'S': (c, r - 2), 'W': (c + 2, r), 'E': (c - 2, r)}[d]
                if not solid(bc, br) and zone.at(bc, br) != '%':
                    bad.append((c, r, d))
            else:
                pillars += 1
    return mods, pillars, bad


def passable(zone):
    P = [[zone.g[r][c] not in BLOCKING for c in range(zone.w)] for r in range(zone.h)]
    for (c, r) in zone.open_extra:
        P[r][c] = True
    # lift line: only the tower base (centre cell of each 3x12 prefab) blocks
    for (c0, r0, w, h) in rects(zone.g, 'K'):
        if w == 3:
            for k in range(h // 12):
                P[r0 + k * 12 + 5][c0 + 1] = P[r0 + k * 12 + 6][c0 + 1] = False
    return P


def bfs(zone, P, start):
    seen = {start}
    q = deque([start])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if 0 <= n[0] < zone.w and 0 <= n[1] < zone.h and n not in seen and P[n[1]][n[0]]:
                seen.add(n)
                q.append(n)
    return seen


def validate(zone, first):
    g, errs = zone.g, []
    find = lambda ch: [(c, r) for r in range(zone.h) for c in range(zone.w) if g[r][c] == ch]
    if not (44 <= zone.w <= 60 and 40 <= zone.h <= 56):
        errs.append('size %dx%d' % (zone.w, zone.h))
    Ps = find('P')
    if len(Ps) != 1:
        return ['need exactly one P'], {}
    P0 = Ps[0]
    G = find('G')
    E = find('E')
    if len(G) != 3 or any(r != 0 for c, r in G) or max(c for c, r in G) - min(c for c, r in G) != 2:
        errs.append('exit gate must be GGG on row 0')
    if not first and (len(E) != 3 or any(r != zone.h - 1 for c, r in E)):
        errs.append('entry gate must be EEE on the last row')
    if first and E and (len(E) != 3 or any(r != zone.h - 1 for c, r in E)):
        errs.append('zone 1 entry gate must be EEE on the last row')
    Pm = passable(zone)
    for c, r in G:
        for k in (1, 2):
            if not Pm[r + k][c]:
                errs.append('exit gate needs 2 open rows in front (%d,%d)' % (c, r + k))
    for c, r in E:
        for k in (1, 2):
            if not Pm[r - k][c]:
                errs.append('entry gate needs 2 open rows in front (%d,%d)' % (c, r - k))
    reach = bfs(zone, Pm, P0)
    if not any((c, 1) in reach for c, r in G):
        errs.append('no path from P to the exit')
    if E and not any((c, zone.h - 2) in reach for c, r in E):
        errs.append('no path from the entry gate to P')
    S = find('S')
    for (c, r) in S:
        if not any((c + dc, r + dr) in reach for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            errs.append('spawn (%d,%d) sealed' % (c, r))
        if (c - P0[0]) ** 2 + (r - P0[1]) ** 2 < 14 ** 2:
            errs.append('spawn (%d,%d) < 14 m from P' % (c, r))
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if (dc or dr) and zone.at(c + dc, r + dr) not in '.DMwW':
                    errs.append('spawn (%d,%d) neighbour (%d,%d) is %r' % (c, r, c + dc, r + dr, zone.at(c + dc, r + dr)))
    if not 10 <= len(S) <= 14:
        errs.append('%d spawns' % len(S))
    na, nh = len(find('a')), len(find('h'))
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for ch, (sw, sd) in PREFAB.items():
        for (c, r, w, h) in rects(g, ch):
            if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                errs.append('prefab %r block %dx%d at (%d,%d) does not tile %dx%d' % (ch, w, h, c, r, sw, sd))
    mods, pillars, bad = walls(zone)
    for b in bad:
        errs.append('cliff module at (%d,%d) facing %s has open ground 2 cells behind' % b)
    # weapon stand (one new weapon, centred 3.8 m north of P) and the open ground the title robots stand on
    for dc in (-1, 0, 1):
        for dr in (-5, -4, -3):
            if g[P0[1] + dr][P0[0] + dc] not in '.DMw':
                errs.append('weapon stand area blocked at (%d,%d)' % (P0[0] + dc, P0[1] + dr))
    opn = sum(1 for r in range(zone.h) for c in range(zone.w) if Pm[r][c])
    cover = sum(1 for r in range(zone.h) for c in range(zone.w) if g[r][c] in 'oO=fxcFtQ')
    stats = {'size': '%dx%d' % (zone.w, zone.h), 'open': opn, 'reach': len(reach), 'spawns': len(S), 'cover_cells': cover,
             'cliff_modules': mods, 'pillars': pillars, 'ammo': na, 'health': nh}
    if len(reach) < opn * 0.97:
        errs.append('sealed pockets: %d of %d open cells reachable' % (len(reach), opn))
    return errs, stats


# ---------------------------------------------------------------- zone 1: Trailhead Meadow (52 x 46)
def zone1():
    z = Z('mountains_1', 52, 46)
    z.rect(3, 2, 46, 41, '.')                  # the valley: cliffs W 3, E 3, N 2, S 3 thick
    z.rect(31, 0, 3, 1, 'G')                   # exit gate, notch in front
    z.rect(31, 1, 3, 1, '.')
    # boundary shape: a rock spur from the west wall, a bulge in the east wall, a southern shoulder
    z.rect(3, 17, 3, 9, '#')
    z.rect(46, 7, 3, 7, '#')
    z.rect(44, 38, 5, 5, '#')
    z.rect(3, 39, 3, 4, '#')
    # treelines in front of / instead of the cliffs (the forest edge you can see through)
    z.block(3, 2, 8, 2, '%')
    z.block(39, 2, 8, 2, '%')
    z.block(6, 41, 6, 2, '%')
    z.block(36, 41, 8, 2, '%')
    z.block(47, 30, 2, 6, '%')
    # trailhead camp around the start
    z.put(26, 39, 'P')
    z.block(19, 37, 3, 3, 'Q')
    z.puts([(29, 39), (30, 39), (29, 38)], 'c')
    z.put(23, 40, 'p')                         # signpost
    z.put(31, 41, 'p')                         # lantern post
    z.block(14, 34, 3, 3, 'M')
    z.block(33, 35, 3, 3, 'M')
    # central meadow: low stone walls 10 m north of the camp, log piles, the lookout tower beyond
    z.run(17, 29, 5, '=')
    z.run(31, 29, 5, '=')
    z.block(24, 12, 4, 4, 'T')
    z.run(23, 22, 3, 'x')
    z.run(28, 22, 2, 'x')
    z.block(15, 20, 2, 2, 'O')
    z.block(36, 18, 2, 2, 'O')
    z.puts([(19, 25), (20, 25)], 'o')
    z.put(33, 25, 'o')
    z.puts([(21, 31), (22, 31)], 'o')           # crouch cover by the camp
    z.put(30, 32, 'o')
    z.block(22, 8, 3, 3, 'D')
    z.puts([(29, 9), (30, 9), (30, 10)], 'o')
    # west lane: cabin yard with a fence and a woodpile, pines along the spur
    z.block(7, 6, 6, 5, 'H')
    z.run(5, 12, 3, 'f')
    z.run(10, 12, 4, 'f')
    z.run(14, 7, 3, 'x')
    z.block(17, 8, 2, 2, 'F')
    z.puts([(14, 14), (6, 28), (11, 31), (8, 37)], 't')
    z.block(9, 23, 3, 3, 'D')
    z.run(7, 18, 2, '=', vertical=False)
    z.put(13, 26, 'o')
    z.block(5, 14, 3, 3, 'M')
    # east lane: frozen pond ringed by rocks and spruce, outcrops, a broken wall
    z.block(39, 21, 4, 4, 'W')
    z.block(43, 22, 2, 2, 'F')
    z.puts([(38, 21), (38, 25), (43, 25)], 'o')
    z.block(36, 7, 2, 2, 'F')
    z.puts([(41, 15), (22, 4), (35, 33), (44, 31)], 't')
    z.block(42, 9, 3, 3, 'D')
    z.run(40, 30, 4, '=')
    z.block(36, 27, 2, 2, 'O')
    z.put(45, 19, 'o')
    # spawn cans: spread over the north, the flanks and the mid-field
    z.puts([(5, 5), (18, 4), (27, 6), (37, 4), (44, 5), (9, 16), (20, 16), (33, 14), (44, 17), (12, 21), (28, 19),
            (34, 23), (9, 33), (43, 34)], 'S')
    z.puts([(16, 27), (38, 15)], 'a')
    z.puts([(26, 26), (9, 27)], 'h')
    return z


# ---------------------------------------------------------------- zone 2: Gorge Crossing (56 x 52)
def zone2():
    z = Z('mountains_2', 56, 52)
    z.rect(3, 2, 50, 47, '.')
    z.rect(31, 51, 3, 1, 'E')
    z.rect(31, 49, 3, 2, '.')
    z.rect(20, 0, 3, 1, 'G')
    z.rect(20, 1, 3, 1, '.')
    # the gorge barrier: rock spurs from both walls, the rope-bridge towers, three ways through
    z.rect(3, 21, 10, 6, '#')
    z.rect(43, 21, 10, 6, '#')
    z.block(21, 22, 14, 4, 'Y')
    for r in range(22, 26):
        for c in range(25, 31):
            z.open_extra.add((c, r))
    z.block(17, 22, 2, 2, 'O')
    z.puts([(19, 24), (20, 22), (16, 25)], 'o')
    z.block(35, 22, 2, 2, 'O')
    z.block(37, 24, 2, 2, 'F')
    z.put(38, 22, 'o')
    # frozen creek from the north cliff, through the pass, into the pond by the entry
    z.block(27, 2, 2, 20, 'w')
    z.block(27, 26, 2, 16, 'w')
    z.block(26, 42, 4, 4, 'W')
    # boundary shaping + treelines
    z.rect(3, 2, 3, 6, '#')
    z.rect(47, 40, 6, 9, '#')
    z.rect(3, 44, 4, 5, '#')
    z.block(35, 2, 8, 2, '%')
    z.block(3, 32, 2, 8, '%')
    z.block(51, 11, 2, 6, '%')
    z.block(8, 47, 6, 2, '%')
    # entry (south): P, low walls and rocks to fight from, drifts
    z.put(32, 46, 'P')
    z.puts([(35, 47), (36, 47)], 'c')
    z.put(30, 47, 'p')
    z.run(36, 38, 5, '=')
    z.run(20, 38, 5, '=')
    z.puts([(14, 35), (15, 35), (14, 36)], 'o')
    z.block(42, 32, 2, 2, 'O')
    z.block(9, 37, 3, 3, 'D')
    z.puts([(23, 31), (33, 31), (31, 29)], 'o')
    z.run(16, 29, 3, 'x')
    z.run(38, 29, 3, 'x')
    z.puts([(45, 37), (11, 32), (24, 43)], 't')
    z.block(18, 42, 2, 2, 'F')
    # north: cabin with a fenced yard (west), spruce stands, outcrops, walls covering the exit
    z.block(7, 9, 6, 5, 'H')
    z.run(7, 15, 3, 'f')
    z.run(11, 15, 2, 'f')
    z.run(14, 10, 3, 'x')
    z.block(16, 5, 2, 2, 'F')
    z.block(31, 7, 2, 2, 'F')
    z.block(40, 12, 2, 2, 'O')
    z.block(23, 14, 2, 2, 'O')
    z.run(30, 16, 5, '=')
    z.run(15, 18, 4, '=')
    z.puts([(36, 5), (37, 5), (24, 7)], 'o')
    z.puts([(45, 6), (19, 12), (35, 12), (6, 17)], 't')
    z.block(44, 15, 3, 3, 'D')
    z.puts([(25, 4), (24, 5)], 'c')
    # spawns: north field, flanks of the barrier, south-west and south-east
    z.puts([(9, 4), (30, 4), (40, 6), (48, 4), (20, 8), (45, 11), (11, 19), (36, 19), (47, 30), (9, 28), (19, 33),
            (39, 32)], 'S')
    z.puts([(14, 22), (41, 22)], 'a')
    z.puts([(25, 33), (14, 14)], 'h')
    return z


# ---------------------------------------------------------------- zone 3: Summit Lift (58 x 50)
def zone3():
    z = Z('mountains_3', 58, 50)
    z.rect(3, 2, 52, 45, '.')
    z.rect(23, 49, 3, 1, 'E')
    z.rect(23, 47, 3, 2, '.')
    z.rect(27, 0, 3, 1, 'G')
    z.rect(27, 1, 3, 1, '.')
    # ski lift: summit station (north-east) and the line running down to a rock shoulder in the south
    z.block(41, 3, 5, 4, 'J')
    z.block(42, 7, 3, 36, 'K')
    z.rect(40, 43, 7, 4, '#')
    # boundary shaping + treelines
    z.rect(3, 2, 4, 5, '#')
    z.rect(51, 2, 4, 9, '#')
    z.rect(3, 40, 6, 7, '#')
    z.block(11, 2, 8, 2, '%')
    z.block(3, 20, 2, 8, '%')
    z.block(53, 24, 2, 8, '%')
    z.block(47, 45, 8, 2, '%')
    # entry: P, crates, drifts, a log wall to duck behind
    z.put(24, 44, 'P')
    z.puts([(20, 45), (21, 45), (20, 44)], 'c')
    z.put(27, 45, 'p')
    z.block(12, 42, 3, 3, 'D')
    z.run(28, 37, 4, 'x')
    z.run(16, 36, 4, '=')
    z.puts([(33, 41), (34, 41), (33, 40)], 'o')
    # chalet (west) with ski racks and a supply depot in the centre
    z.block(8, 8, 5, 6, 'A')
    z.put(14, 13, 'p')
    z.puts([(14, 12), (40, 8)], 'k')
    z.puts([(19, 19), (20, 19), (21, 19), (19, 20), (25, 18), (26, 18), (25, 19)], 'c')
    z.run(19, 24, 4, 'x')
    z.block(30, 22, 3, 3, 'Q')
    z.block(14, 27, 2, 2, 'O')
    z.block(35, 29, 2, 2, 'O')
    z.run(22, 31, 5, '=')
    z.puts([(9, 25), (10, 25), (36, 15)], 'o')
    z.block(7, 32, 3, 3, 'D')
    z.block(46, 33, 3, 3, 'D')
    # lift lane (east): rocks and spruce under the chairs
    z.block(47, 16, 2, 2, 'F')
    z.block(38, 23, 2, 2, 'F')
    z.puts([(48, 26), (39, 35), (47, 39)], 'o')
    z.puts([(49, 12), (37, 9), (32, 13), (12, 20), (6, 15), (50, 30)], 't')
    # north: walls covering the exit gate, spruce, drift
    z.run(22, 6, 4, '=')
    z.run(31, 6, 4, '=')
    z.block(17, 8, 2, 2, 'F')
    z.block(33, 9, 3, 3, 'D')
    z.puts([(26, 11), (27, 11)], 'o')
    # spawns
    z.puts([(11, 5), (24, 3), (35, 4), (48, 6), (16, 16), (28, 15), (39, 18), (9, 22), (48, 21), (27, 27), (8, 29),
            (40, 30), (49, 36)], 'S')
    z.puts([(17, 31), (37, 25), (23, 10)], 'a')
    z.puts([(33, 33), (10, 17)], 'h')
    return z


def main(argv):
    zones = [zone1(), zone2(), zone3()]
    ok = True
    for i, z in enumerate(zones):
        errs, st = validate(z, i == 0)
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
