#!/usr/bin/env python3
"""INKBOLT Mosswood Gardens zones (theme 'mossgarden'): hand-placed layouts -> src/data/zones/mossgarden_*.txt

    python3 tools/mossgarden_zones.py           # write + validate
    python3 tools/mossgarden_zones.py --check   # validate only
    python3 tools/mossgarden_zones.py --print   # also print the maps

The cobbled paths, plaza rings, the stream, the terrace and the mound are defined once, in GARDEN in
src/data/themes/mossgarden.js (the theme draws the paths and the stream as smooth ribbons and lifts the terrain);
this script reads that block, marks the cells under the ribbons (';' path, '~' stream and its banks) so nothing is
placed on them, builds the terrace ring round the lifted area and lays out the rest by hand.
Zone 1, the formal garden (72 x 70): the tiered fountain on its cobbled plaza in the middle, four parterres round it,
the raised terrace across the north-west (balustrade ring, back border, grand stair, side and east stairs, pergola,
tea tables, belvedere, wall fountains under it), the rose walk on the west, the glasshouse on the east, the entry
court in the south behind yew screens, the exit path up the east side, three giant trees.
Zone 2, the wild garden (74 x 70): the reflecting pool north of the entry, the stream from the grotto (west wall) to
the culvert (east wall) under two stone bridges, the mound with the ruined folly (north-west), the hedge maze
(north-east), the gazebo by the stream, the nursery yard (south-east), meadows, ferns, lumenbell pods, boulders,
logs and three giant trees. Symbols: src/data/themes/mossgarden.js.
"""
import json
import math
import os
import random
import re
import sys

from zonekit import Zone, validate, write, rects, OUT

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(HERE, '..', 'src', 'data', 'themes', 'mossgarden.js')
GARDEN = json.loads(re.search(r'/\*GARDEN\*/(.*?)/\*END\*/', open(THEME).read(), re.S).group(1))

PREFAB = {'U': (5, 5), 'u': (3, 5), 'Y': (5, 3), 'p': (6, 4), 'e': (2, 2), 'F': (9, 9), 'w': (3, 1), 'W': (3, 1),
          'X': (14, 10), 'R': (4, 1), 'O': (4, 4), 'C': (4, 4), 'f': (2, 2), '@': (2, 2), '=': (4, 1), 'b': (4, 2),
          'v': (3, 2), 'n': (2, 2), 'j': (2, 1), 'k': (2, 1), '<': (1, 2), '>': (1, 2), 'M': (7, 7), 'Z': (5, 5),
          'D': (3, 5), 'V': (3, 16), 'N': (4, 2), 'I': (3, 1), '&': (4, 1), '$': (4, 5), 'T': (2, 1), 't': (2, 1),
          '!': (2, 1), '?': (1, 2)}
# half size (m) a one-cell prop needs clear of a ribbon's drawn edge (blocks need 0.55 in every cell)
NEED = {'L': 0.22, 'q': 0.33, 'd': 0.35, 'A': 0.5, 's': 0.42, 'c': 0.42, 'o': 0.42, 'r': 0.45, 'y': 0.48, 'x': 0.45,
        'R': -9.0, 'z': 0.0, 'g': 0.15, '%': 0.45, '+': 0.45, '*': 0.45, 'l': 0.6, 'm': 0.6, 'H': 0.6, 'b': 0.0, 'v': 0.0, 'n': 0.0}
# open ground you can stand on, and the no-collision symbols (beds, ferns, meadows, stepping stones)
GROUND = '.;:_~,'
WALKABLE = set(GROUND + 'bvnzi' + 'UuYDV')


# ---------------------------------------------------------------- the theme's curve sampler (themes/mossgarden.js)
def catmull(pts, step):
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(P) - 3):
        a, b, c, d = P[i], P[i + 1], P[i + 2], P[i + 3]
        n = max(2, math.ceil(math.hypot(c[0] - b[0], c[1] - b[1]) / step))
        for k in range(0 if i == 0 else 1, n + 1):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * b[j] + (-a[j] + c[j]) * t + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * t2 + (-a[j] + 3 * b[j] - 3 * c[j] + d[j]) * t3) for j in (0, 1)))
    return out


def dist_poly(S, x, z):
    return min(math.hypot(px - x, pz - z) for (px, pz) in S)


class GZone(Zone):
    def __init__(self, name, zi, w, h, gate_e, gate_g, pc):
        super().__init__(name, w, h, fill='.')
        self.zi = zi
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gate_g, 0, 3, 1, 'G')
        self.rect(gate_e, h - 1, 3, 1, 'E')
        self.put(pc, h - 3, 'P')
        self.paths = [catmull(p['pts'], 0.2) for p in GARDEN['paths'][zi]]
        self.widths = [p['w'] for p in GARDEN['paths'][zi]]
        self.streams = [(catmull(s['pts'], 0.2), s['w']) for s in GARDEN['streams'][zi]]
        self.skipped = []

    # ---- ground under the ribbons
    def lay_ground(self):
        """gap[r][c]: how far the cell centre is from the drawn ribbons (cobbles and kerb); cells under them (gap < 0.05)
        become ';' (paths, plaza rings), cells within a metre of the stream '~'; a prop goes on a '.' cell only where the
        gap clears its own half size (NEED), so nothing stands on a kerb"""
        self.gap = [[9.0] * self.w for _ in range(self.h)]
        for S, w in self.streams:
            for (x, z) in S:
                for r in range(max(1, int(z - w / 2 - 2)), min(self.h - 1, int(z + w / 2 + 3))):
                    for c in range(max(1, int(x - w / 2 - 2)), min(self.w - 1, int(x + w / 2 + 3))):
                        if self.g[r][c] == '.' and math.hypot(c + 0.5 - x, r + 0.5 - z) < w / 2 + 1.05:
                            self.g[r][c] = '~'
        for S, w in zip(self.paths, self.widths):
            reach = w / 2 + 0.25
            for (x, z) in S:
                for r in range(max(1, int(z - reach) - 1), min(self.h - 1, int(z + reach) + 2)):
                    for c in range(max(1, int(x - reach) - 1), min(self.w - 1, int(x + reach) + 2)):
                        self.gap[r][c] = min(self.gap[r][c], math.hypot(c + 0.5 - x, r + 0.5 - z) - reach)
        for (cx, cz, r0, r1) in GARDEN['plazas'][self.zi]:
            for r in range(1, self.h - 1):
                for c in range(1, self.w - 1):
                    d = math.hypot(c + 0.5 - cx, r + 0.5 - cz)
                    if d > r0 - 0.3:
                        self.gap[r][c] = min(self.gap[r][c], d - (r1 + 0.25))
        for r in range(1, self.h - 1):
            for c in range(1, self.w - 1):
                if self.g[r][c] == '.' and self.gap[r][c] < 0.05:
                    self.g[r][c] = ';'

    def free(self, c, r, w=1, h=1, over='.', need=0.5):
        for rr in range(r, r + h):
            for cc in range(c, c + w):
                if not (0 <= cc < self.w and 0 <= rr < self.h and self.g[rr][cc] in over):
                    return False
                if self.g[rr][cc] == '.' and hasattr(self, 'gap') and self.gap[rr][cc] < need:
                    return False
        return True

    def blocks(self, ch, pts, over='.', must=True):
        w, d = PREFAB[ch]
        for (c, r) in pts:
            if must:
                self.block(c, r, w, d, ch, over=over)
            elif self.free(c, r, w, d, over, NEED.get(ch, 0.55)):
                self.rect(c, r, w, d, ch)
            else:
                self.skipped.append((ch, c, r))

    def cells(self, ch, pts, over='.', must=False):
        for (c, r) in pts:
            if must:
                self.put(c, r, ch, over=over)
            elif self.free(c, r, over=over, need=NEED.get(ch, 0.5)):
                self.g[r][c] = ch
            else:
                self.skipped.append((ch, c, r))

    def line(self, ch, c0, r0, c1, r1, over='.'):
        """a hedge line (inclusive, horizontal or vertical); cells that are not free are left as they are (gaps)"""
        if r0 == r1:
            for c in range(min(c0, c1), max(c0, c1) + 1):
                if self.free(c, r0, over=over, need=0.6):
                    self.g[r0][c] = ch
        else:
            for r in range(min(r0, r1), max(r0, r1) + 1):
                if self.free(c0, r, over=over, need=0.6):
                    self.g[r][c0] = ch

    def paint(self, c0, r0, w, h, ch, over='.'):
        self.pave(c0, r0, w, h, ch, over=over)


def finish(z, ammo, health, spawns):
    if '--draft' in sys.argv:
        ammo, health, spawns = [], [], []
    z.cells('a', ammo, over=GROUND, must=True)
    z.cells('h', health, over=GROUND, must=True)
    z.cells('S', spawns, over='.:,', must=True)
    errs, stats = validate(z, WALKABLE, dict(PREFAB), size=((70, 78), (64, 72)))
    # spawns stand on level ground (the terrain pins spawn cells to 0: never on the terrace or the mound)
    for r in range(z.h):
        for c in range(z.w):
            if z.g[r][c] == 'S':
                for (cc, rr) in ((c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)):
                    if height(z.zi, cc, rr) > 0.01:
                        errs.append('spawn (%d,%d) on raised ground' % (c, r))
    if z.skipped:
        stats['skipped'] = len(z.skipped)
    return z, errs, stats


def height(zi, c, r):
    T, M = GARDEN['terrace'], GARDEN['mound']
    if zi == 0:
        return T[4] if (T[0] <= c <= T[2] and T[1] <= r <= T[3]) else 0.0
    d = math.hypot(c - M[0], r - M[1])
    if d <= M[2]:
        return M[4]
    if d >= M[3]:
        return 0.0
    k = (M[3] - d) / (M[3] - M[2])
    return M[4] * k * k * (3 - 2 * k)


# ================================================================ zone 1: the formal garden
def parterre(z, c0, r0, kind):
    """13 x 13: a box-hedge border with 3-cell openings mid-side, gravel cross walks, a spiral topiary in the middle,
    four planted quadrants"""
    for i in range(13):
        for (c, r) in ((c0 + i, r0), (c0 + i, r0 + 12), (c0, r0 + i), (c0 + 12, r0 + i)):
            if not 5 <= i <= 7 and z.g[r][c] != 'l':
                z.cells('l', [(c, r)])
    z.paint(c0 + 5, r0 + 1, 3, 11, ':')
    z.paint(c0 + 1, r0 + 5, 11, 3, ':')
    z.cells('s', [(c0 + 6, r0 + 6)], over=':')
    for (i0, j0) in ((1, 1), (8, 1), (1, 8), (8, 8)):
        outer = j0 == 1
        jb, jl = (j0, j0 + 2) if outer else (j0 + 2, j0)    # beds toward the border, shrubs toward the walks
        c, r, rl = c0 + i0, r0 + jb, r0 + jl
        bed = 'v' if kind == 'lavender' else 'b'
        z.blocks(bed, [(c, r)], must=False)
        if kind == 'tulip':
            z.blocks('v', [(c, rl)], must=False)
        else:
            sh = {'rose': 'r', 'lavender': 'r', 'hydrangea': 'y'}[kind]
            z.cells(sh, [(c, rl + (0 if outer else 1)), (c + 3, rl + (0 if outer else 1))])
            z.cells('c' if kind == 'rose' else sh, [(c + 1 + (0 if outer else 1), rl + (1 if outer else 0))])


def formal():
    z = GZone('mossgarden_1', 0, 72, 70, 34, 60, 35)
    T = GARDEN['terrace']
    c0, r0, c1, r1 = T[0], T[1], T[2], T[3]       # corner range: interior cells c0..c1-1, r0..r1-1
    # ---- the terrace: interior lawn, the balustrade ring (south row r1, east column c1), the back border on the wall
    z.rect(c0, r0, c1 - c0, r1 - r0, '_')
    z.rect(c0 - 1, r0 - 1, c1 - c0 + 1, 1, 'Q')
    z.rect(c0 - 1, r0, 1, r1 - r0, '^')
    z.rect(c0 - 1, r1, c1 - c0 + 1, 1, 'B')
    z.rect(c1, r0 - 1, 1, r1 - r0 + 1, '|')
    for (c, r) in ((c0 - 1, r1), (c1, r1), (c1, r0 - 1)):
        z.g[r][c] = 'K'
    z.rect(33, r1, 5, 5, 'U')                    # grand stair on the axis (top landing in the ring row)
    z.rect(8, r1, 3, 5, 'u')                     # side stair to the rose walk
    z.rect(c1, 5, 5, 3, 'Y')                     # east stair, rising west
    # ---- ribbons (after the terrace so its cells are not taken), plaza, the fountain
    z.lay_ground()
    z.blocks('F', [(31, 34)], over=';.')
    # on the terrace: pergola with its bench, tea tables, the belvedere at the stair head, borders, topiary
    z.blocks('p', [(11, 3)], over='_')
    z.blocks('e', [(21, 3), (25, 6), (21, 8)], over='_')
    z.cells('L', [(32, 10), (38, 10), (14, 9), (28, 4)], over='_', must=True)
    z.cells('c', [(31, 3), (34, 3), (37, 3), (40, 3)], over='_')
    z.blocks('v', [(40, 6)], over='_', must=False)
    z.blocks('j', [(33, 6), (36, 6)], over='_')
    z.cells('s', [(29, 8)], over='_')
    z.cells('q', [(17, 9), (25, 10), (43, 10)], over='_')
    z.paint(c0, r1 - 2, c1 - c0, 1, ':', over='_')          # gravel walk inside the balustrade
    z.paint(31, r0, 9, r1 - r0 - 2, ':', over='_')          # the belvedere's gravel
    # wall fountains under the balustrade, flanking the grand stair
    z.blocks('w', [(28, r1 + 1), (40, r1 + 1)], over='.;')
    # ---- parterres round the plaza
    parterre(z, 15, 18, 'tulip')
    parterre(z, 44, 18, 'rose')
    parterre(z, 15, 46, 'lavender')
    parterre(z, 44, 46, 'hydrangea')
    # lamps and benches on the plaza approaches
    z.cells('L', [(33, 19), (38, 28), (33, 49), (38, 58), (28, 31), (43, 31), (27, 46), (44, 45)], must=False)
    z.blocks('<', [(38, 22), (38, 52)], must=False)
    z.blocks('>', [(32, 22), (32, 52)], must=False)
    # ---- the rose walk (west): rose arches over the straight stretch, roses and lavender either side, benches
    for r in (22, 25, 28, 31, 34):
        z.blocks('R', [(7, r)], over=';.', must=False)
    for r in (21, 33, 50):
        z.blocks('v', [(3, r)], must=False)
    z.cells('r', [(6, 24), (6, 41), (12, 48)])
    z.blocks('>', [(11, 26), (11, 45)], must=False)
    z.blocks('<', [(6, 36)], must=False)
    z.line('m', 13, 18, 13, 33)
    z.line('m', 13, 44, 13, 57)
    z.cells('y', [(3, 31), (4, 54)])
    z.blocks('O', [(1, 61)])
    # west wall fountain (against the west garden wall, facing east)
    z.rect(1, 37, 1, 3, 'W')
    # ---- the glasshouse (east), its lawn and the east door's border
    z.blocks('X', [(52, 35)], over='.;')
    z.cells('x', [(67, 37), (69, 41)])
    z.blocks('f', [(68, 45)], must=False)
    z.cells('L', [(51, 38), (51, 43)], must=False)
    # ---- north-east: the sundial lawn east of the terrace, the cedar by the exit path
    z.cells('d', [(54, 12)])
    z.line('l', 50, 10, 58, 10)
    z.line('l', 50, 14, 58, 14)
    z.blocks('b', [(50, 11)], must=False)
    z.blocks('C', [(65, 7)])
    z.cells('x', [(67, 18), (56, 3)])
    z.blocks('k', [(52, 3)], must=False)
    z.cells('g', [(58, 26), (33, 31)], must=False)
    z.cells('s', [(59, 20), (64, 12)], must=False)
    # ---- south-east: the oak, tree ferns and hydrangeas round a bench
    z.blocks('O', [(64, 53)])
    z.blocks('f', [(62, 60), (68, 59), (58, 47)], must=False)
    z.cells('y', [(63, 49)])
    z.blocks('j', [(63, 63)], must=False)
    # ---- the entry court: yew screens with gaps, spiral topiary, tulip beds, lamps, benches, wall fountains
    z.line('H', 14, 60, 22, 60)
    z.line('H', 26, 60, 32, 60)
    z.line('H', 39, 60, 45, 60)
    z.line('H', 49, 60, 57, 60)
    z.cells('s', [(32, 62), (38, 62)], must=False)
    z.cells('L', [(33, 67), (37, 67)], must=False)
    z.blocks('b', [(26, 62), (41, 62)], must=False)

    z.blocks('j', [(21, 67), (48, 67)], must=False)
    z.blocks('W', [(26, 68), (43, 68)], must=False)
    z.cells('c', [(15, 62), (21, 62), (50, 62), (56, 62)], must=False)
    z.cells('q', [(30, 66), (40, 66)], must=False)
    z.cells('y', [(9, 62), (62, 66)], must=False)
    # ---- the east strip along the exit path: pods, ferns, hydrangeas, benches facing the path
    z.cells('x', [(68, 22)], must=False)
    z.blocks('f', [(68, 14), (57, 23)], must=False)

    z.blocks('<', [(64, 17)], must=False)
    z.blocks('>', [(58, 28)], must=False)
    ammo = [(30, 44), (47, 33), (6, 18)]
    health = [(42, 44), (10, 57), (26, 5)]
    spawns = [(20, 33), (48, 43), (4, 15), (56, 5), (68, 26), (20, 15), (3, 57), (29, 52), (66, 58), (6, 66), (66, 66), (47, 13)]
    return finish(z, ammo, health, spawns)


# ================================================================ zone 2: the wild garden
def maze(z, c0, r0, nx, ny, seed):
    """a hedge maze of nx x ny rooms (2 x 2 corridors, 1-cell yew walls), carved by depth-first search, then a few
    extra openings so it has loops (flanking routes)"""
    rnd = random.Random(seed)
    W, H = 3 * nx + 1, 3 * ny + 1
    wall = [[True] * W for _ in range(H)]
    for j in range(ny):
        for i in range(nx):
            for dy in (1, 2):
                for dx in (1, 2):
                    wall[3 * j + dy][3 * i + dx] = False
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        i, j = stack[-1]
        nb = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i + di < nx and 0 <= j + dj < ny and (i + di, j + dj) not in seen]
        if not nb:
            stack.pop()
            continue
        a, b = rnd.choice(nb)
        if a != i:
            x = 3 * max(a, i)
            for dy in (1, 2):
                wall[3 * j + dy][x] = False
        else:
            y = 3 * max(b, j)
            for dx in (1, 2):
                wall[y][3 * i + dx] = False
        seen.add((a, b))
        stack.append((a, b))
    for _ in range(6):   # loops
        i, j = rnd.randrange(nx - 1), rnd.randrange(ny)
        for dy in (1, 2):
            wall[3 * j + dy][3 * (i + 1)] = False
    # wall posts left standing alone between four open corners are removed (no lone yew stubs)
    for y in range(3, H - 1, 3):
        for x in range(3, W - 1, 3):
            if not (wall[y - 1][x] or wall[y + 1][x] or wall[y][x - 1] or wall[y][x + 1]):
                wall[y][x] = False
    return wall


def wild():
    z = GZone('mossgarden_2', 1, 74, 70, 16, 36, 17)
    z.lay_ground()
    # ---- the mound and the folly, the plaza ring round it was laid as path; rocks and ferns on the slopes
    z.blocks('M', [(14, 12)], over=';.')
    z.cells('%', [(9, 8), (26, 11), (10, 22), (24, 23), (7, 15), (21, 5)], must=False)
    z.cells('z', [(12, 6), (8, 19), (27, 16), (20, 24)], must=False)
    z.blocks('n', [(9, 11), (22, 19), (11, 3)], must=False)
    z.cells('x', [(14, 9), (21, 9), (14, 21), (22, 20)], must=False)
    # ---- the stream: grotto spring (west wall), bridges, stepping stones, culvert (east wall)
    z.rect(1, 31, 2, 4, 'N')
    z.rect(72, 35, 1, 3, 'I')
    z.blocks('D', [(16, 32), (51, 33)], over='~;.')
    for (c, r) in ((34, 33), (34, 34), (34, 35), (35, 36)):
        if z.g[r][c] == '~':
            z.g[r][c] = 'i'
    # stream-side planting: tree ferns, lumenbell pods, ferns, boulders (outside the bank margin)
    z.blocks('f', [(6, 37), (25, 29), (45, 39), (65, 32)], must=False)
    z.cells('x', [(11, 38), (23, 37), (47, 34), (63, 39)], must=False)
    z.cells('z', [(5, 30), (21, 30), (27, 37), (43, 33), (56, 31), (67, 40)], must=False)
    z.blocks('@', [(30, 28), (44, 36), (62, 33)], must=False)
    # ---- the reflecting pool on the entry axis, benches facing it, urns at its ends, meadows either side
    z.blocks('V', [(16, 44)])
    z.blocks('>', [(10, 47), (10, 55)], must=False)
    z.blocks('<', [(24, 47), (24, 55)], must=False)
    z.cells('q', [(15, 42), (19, 42), (15, 60), (19, 60)], must=False)
    z.blocks('n', [(4, 41), (7, 61), (26, 51), (27, 62)], must=False)
    # ---- the west woodland: an oak, ferns, pods, a log, boulders
    z.blocks('O', [(2, 47)])
    z.blocks('f', [(7, 44), (2, 63), (8, 52)], must=False)
    z.cells('x', [(6, 58), (9, 64), (3, 42)], must=False)
    z.blocks('=', [(4, 60)], must=False)
    z.blocks('@', [(8, 66)], must=False)
    z.cells('z', [(2, 54), (7, 49), (10, 60), (5, 66)], must=False)
    # ---- the middle south: the cedar, meadows, a log, boulders, a wall fountain on the south wall
    z.blocks('C', [(38, 51)])
    z.blocks('n', [(30, 52), (46, 56), (40, 63)], must=False)
    z.blocks('=', [(33, 55), (44, 46)], must=False)
    z.blocks('@', [(28, 47), (43, 61)], must=False)
    z.blocks('W', [(36, 68)], must=False)
    z.cells('x', [(42, 57)], must=False)
    # ---- north of the stream, east of the mound: an oak, ferns, meadows; the exit path
    z.blocks('O', [(32, 20)])
    z.blocks('n', [(37, 26), (30, 12)], must=False)
    z.cells('z', [(30, 25), (38, 22), (41, 26), (33, 15)], must=False)
    z.cells('g', [(39, 7), (55, 41)], must=False)
    # ---- the hedge maze (north-east): yew walls, the arch at the south entrance, the armillary room
    mc, mr, nx, ny = 46, 2, 8, 7
    M = maze(z, mc, mr, nx, ny, 77)
    for y in range(len(M)):
        for x in range(len(M[0])):
            c, r = mc + x, mr + y
            if M[y][x] and z.g[r][c] in '.,;':
                z.g[r][c] = 'H'
            elif not M[y][x] and z.g[r][c] == '.':
                z.g[r][c] = ':'
    ent = mc + 3 * 4                                  # south entrance below room 4 of the last row
    for c in range(ent, ent + 4):
        z.g[mr + 3 * ny][c] = '&'
    for (c, r) in ((mc, mr + 3 * 3 + 1), (mc, mr + 3 * 3 + 2)):   # west entrance
        z.g[r][c] = ':'
    for r in range(mr + 7, mr + 12):                  # the armillary room in the middle
        for c in range(mc + 10, mc + 15):
            z.g[r][c] = ':'
    z.g[mr + 9][mc + 12] = 'A'
    z.blocks('j', [(mc + 11, mr + 7)], over=':', must=False)
    z.blocks('k', [(mc + 11, mr + 11)], over=':', must=False)
    # ---- the gazebo by the stream, meadows round it
    z.blocks('Z', [(58, 40)], over='.;')
    z.blocks('n', [(52, 43), (66, 47)], must=False)
    # ---- the nursery yard (south-east): shed, benches, cold frames, compost, barrow, pots, crates, a mid hedge round it
    z.blocks('$', [(68, 54)])
    z.blocks('T', [(62, 68), (65, 68)], must=False)
    z.blocks('!', [(56, 68), (59, 68)], must=False)
    z.blocks('t', [(60, 57), (60, 60), (63, 60)], must=False)
    z.blocks('?', [(57, 56)], must=False)
    z.cells('+', [(66, 54), (66, 61), (55, 60)], must=False)
    z.cells('*', [(64, 56), (65, 57), (57, 63)], must=False)
    z.line('m', 52, 51, 64, 51)
    z.line('m', 52, 52, 52, 64)
    # ---- the glade north of the stream: a mid hedge room, meadows, ferns, pods, a log, a wall fountain on the north wall
    z.line('m', 34, 14, 42, 14)
    z.line('m', 42, 15, 42, 20)
    z.line('m', 27, 27, 33, 27)
    z.blocks('=', [(36, 18), (26, 2)], must=False)
    z.blocks('f', [(38, 10), (28, 15), (43, 24)], must=False)
    z.cells('x', [(35, 16), (39, 20), (31, 17), (44, 9)], must=False)
    z.blocks('W', [(42, 1)], must=False)
    z.blocks('@', [(29, 22), (40, 4)], must=False)
    ammo = [(26, 40), (60, 47), (40, 12)]
    health = [(46, 30), (11, 50), (28, 3)]
    spawns = [(8, 40), (24, 42), (30, 41), (50, 47), (67, 44), (5, 52), (35, 61), (49, 63), (40, 22), (33, 12), (51, 26), (66, 27)]
    return finish(z, ammo, health, spawns)


def main():
    zones = [formal(), wild()]
    ok = write(zones, check_only=True)
    for z, _, _ in zones:
        if z.skipped:
            print('  %s skipped (not free): %s' % (z.name, ' '.join('%s@%d,%d' % s for s in z.skipped)))
    if '--check' not in sys.argv:
        for z, _, _ in zones:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
    if '--print' in sys.argv:
        for z, _, _ in zones:
            print('\n' + z.text())
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
