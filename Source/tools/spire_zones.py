"""The Spire zone maps (src/data/zones/spire_{lobby,garden,trading}.txt), written from scratch by this script.

Each zone is a floor plan plus "@layer" grids (zones.js): "@layer 0" floor inlays, "@layer 4.5" a mezzanine deck
(lobby, trading floor), "@layer 9" the ceiling fittings or the garden's glass roof. Sizes are 6n + 2 in both
directions (the diagrid bays of 6 m run evenly from corner to corner) with interiors divisible by 4 (coffer and
glass-roof tiles). The layouts are laid out by hand below; the dressing that follows from them (columns under and
over the rail line, under-deck lights, ceiling tiles, downlights) is derived. A check mirrors the unit test: gates,
one P, reachability on both floors (stairs and escalators link them), spawn cans with open ground round them,
pickups, prefab tiling.
Run: python3 tools/spire_zones.py [--print]
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ZD = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))

PREFAB = {'N': (2, 10), 'V': (2, 10), 'Z': (4, 10), 'U': (4, 10), 'R': (6, 3), 'L': (4, 3), 'C': (4, 4), 'O': (2, 2),
          'B': (2, 1), 'T': (3, 3), 'W': (4, 4), 'Q': (6, 4), 'D': (4, 2), 'M': (8, 6), 'X': (4, 3), 'A': (3, 3),
          'x': (8, 8), 'g': (4, 4), 'w': (4, 4), 'q': (4, 4), '~': (4, 4), 'H': (8, 8), 'Y': (8, 8), '^': (8, 8)}
STAIRS = 'NVZU'
GROUND_OPEN = set('.ahP')
DECK_OPEN = set('ulah')


class Zone:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.g = [['.'] * w for _ in range(h)]
        for c in range(w):
            self.g[0][c] = self.g[h - 1][c] = '#'
        for r in range(h):
            self.g[r][0] = self.g[r][w - 1] = '#'
        self.layers = {}

    def layer(self, y):
        if y not in self.layers:
            L = [['.'] * self.w for _ in range(self.h)]
            if y != '0':
                for c in range(self.w):
                    L[0][c] = L[self.h - 1][c] = '#'
                for r in range(self.h):
                    L[r][0] = L[r][self.w - 1] = '#'
            self.layers[y] = L
        return self.layers[y]

    def put(self, c, r, ch, grid=None, over='.'):
        g = self.g if grid is None else grid
        assert 0 < c < self.w - 1 and 0 < r < self.h - 1, (self.name, c, r, ch)
        assert g[r][c] in over, '%s: (%d,%d) is %r, placing %r' % (self.name, c, r, g[r][c], ch)
        g[r][c] = ch

    def block(self, c0, r0, w, h, ch, grid=None, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.put(c, r, ch, grid, over)

    def gates(self, gc, ec):
        for k in range(3):
            self.g[0][gc + k] = 'G'
            self.g[self.h - 1][ec + k] = 'E'

    def text(self):
        out = [''.join(row) for row in self.g]
        for y in sorted(self.layers, key=float):
            out.append('@layer ' + y)
            out += [''.join(row) for row in self.layers[y]]
        return '\n'.join(out) + '\n'


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
            h, ok = 1, True
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


# ------------------------------------------------------------------ derived dressing
def deck_ring(z, mez, void, gaps):
    """Deck on every interior cell outside the void rectangle; rails on the deck cells bordering the void (except
    the gaps where stairs land)."""
    c0, r0, c1, r1 = void
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if not (c0 <= c <= c1 and r0 <= r <= r1):
                mez[r][c] = 'u'
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if mez[r][c] != 'u':
                continue
            if any(c0 <= c + dc <= c1 and r0 <= r + dr <= r1 for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))):
                mez[r][c] = 'r'
    for (c, r) in gaps:
        assert mez[r][c] == 'r', (z.name, c, r, mez[r][c])
        mez[r][c] = 'u'


def columns(z, mez, spots):
    for (c, r) in spots:
        assert mez[r][c] == 'r' and z.g[r][c] == '.', (z.name, c, r, mez[r][c], z.g[r][c])
        mez[r][c] = 'i'
        z.g[r][c] = 'I'


def under_lights(z, mez, lines_c, lines_r):
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if mez[r][c] != 'u' or z.g[r][c] not in '.':
                continue
            if (c in lines_c and r % 4 == 1) or (r in lines_r and c % 4 == 1):
                mez[r][c] = 'l'


def tiles(z, grid, ch, c0, r0, nx, ny, skip=()):
    for ty in range(ny):
        for tx in range(nx):
            if (tx, ty) in skip:
                continue
            if any(z.g[r][c] == '#' for r in range(r0 + ty * 4, r0 + ty * 4 + 4) for c in range(c0 + tx * 4, c0 + tx * 4 + 4)):
                continue      # never over an inner wall (its top reaches the ceiling)
            z.block(c0 + tx * 4, r0 + ty * 4, 4, 4, ch, grid)


# ------------------------------------------------------------------ Sky Lobby
def lobby():
    z = Zone('spire_lobby', 62, 50)
    z.gates(29, 29)
    g = z.g
    mez = z.layer('4.5')
    void = (8, 8, 53, 48)
    # stairs to the north deck: two escalators and the grand stair in front of the exit
    z.block(14, 8, 2, 10, 'N')
    z.block(46, 8, 2, 10, 'N')
    z.block(29, 8, 4, 10, 'Z')
    deck_ring(z, mez, void, [(14, 7), (15, 7), (29, 7), (30, 7), (31, 7), (32, 7), (46, 7), (47, 7)])
    columns(z, mez, [(7, 14), (7, 22), (7, 30), (7, 38), (7, 46), (54, 14), (54, 22), (54, 30), (54, 38), (54, 46),
                     (10, 7), (22, 7), (39, 7), (51, 7)])
    # ground floor: the model of the Spire under the halo, reception, security line, lounges, planters
    z.block(29, 22, 4, 4, 'C')
    z.block(28, 31, 6, 3, 'R')
    for c in list(range(15, 25)) + list(range(37, 47)):
        z.put(c, 39, 't')
    z.block(11, 24, 4, 3, 'L')
    z.block(47, 24, 4, 3, 'L')
    z.block(11, 42, 4, 3, 'L')
    z.block(47, 42, 4, 3, 'L')
    for (c, r) in ((20, 19), (40, 19), (20, 31), (40, 31)):
        z.block(c, r, 2, 2, 'O')
    for (c, r) in ((24, 27), (36, 27), (24, 45), (36, 45)):
        z.block(c, r, 2, 1, 'B')
    for (c, r) in ((12, 17), (17, 17), (44, 17), (49, 17), (28, 17), (33, 17)):
        z.put(c, r, 'o')
    for (c, r) in ((26, 47), (35, 47), (26, 2), (35, 2)):
        z.put(c, r, 'd')
    for (c, r) in ((2, 2), (59, 2), (2, 47), (59, 47), (2, 25), (59, 25)):
        z.put(c, r, 'p')
    z.put(30, 47, 'P')
    for (c, r) in ((10, 10), (51, 10), (11, 32), (50, 32), (21, 13), (40, 13), (4, 20), (57, 20), (4, 40), (57, 40)):
        z.put(c, r, 'S')
    z.put(18, 35, 'a')
    z.put(44, 35, 'h')
    # mezzanine: lounges, benches and planters along the deck, spawns and pickups upstairs
    for (c, r) in ((2, 28), (56, 28)):
        z.block(c, r, 4, 3, 'L', mez, 'ul')
    for (c, r) in ((18, 2), (40, 2)):
        z.block(c, r, 2, 1, 'B', mez, 'ul')
    for (c, r) in ((2, 10), (59, 10), (2, 44), (59, 44), (26, 2), (35, 2)):
        z.put(c, r, 'o', mez, 'ul')
    for (c, r) in ((3, 16), (58, 16), (3, 38), (58, 38), (12, 3), (49, 3)):
        z.put(c, r, 'S', mez, 'ul')
    z.put(4, 24, 'h', mez, 'u')
    z.put(57, 34, 'a', mez, 'u')
    under_lights(z, mez, (4, 57), (4,))
    # floor inlays: the star medallion under the model
    fl = z.layer('0')
    z.block(27, 20, 8, 8, 'x', fl)
    for c in range(7, 55):                      # border band under the rail line, a carpet runner to reception
        for r in (7,):
            fl[r][c] = '-'
    for r in range(8, 49):
        fl[r][7] = fl[r][54] = '-'
    tiles(z, fl, 'q', 29, 34, 1, 3)
    # ceiling: coffers over the atrium, the halo over the model, downlights over the deck ring and the edges
    rf = z.layer('9')
    tiles(z, rf, '~', 11, 8, 10, 10, skip={(4, 3), (5, 3), (4, 4), (5, 4)})
    z.block(27, 20, 8, 8, 'H', rf)
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if rf[r][c] != '.':
                continue
            if ((c in (4, 57) and r % 4 == 3) or (r == 4 and c % 4 == 3) or (c in (9, 52) and r % 4 == 2 and r > 9)):
                rf[r][c] = ':'
    return z


# ------------------------------------------------------------------ Sky Garden
def garden():
    z = Zone('spire_garden', 50, 50)
    z.gates(29, 17)                 # entry west of centre, exit east of it: the towers stand staggered
    fl = z.layer('0')
    # boardwalks: from the entry north to the crossing, from the crossing north to the exit, and across the middle;
    # lawns round the groves
    for ty in range(6, 12):
        z.block(1 + 4 * 4, 1 + ty * 4, 4, 4, 'w', fl)
    for ty in range(0, 5):
        z.block(1 + 7 * 4, 1 + ty * 4, 4, 4, 'w', fl)
    for tx in range(12):
        for ty in (5,):
            z.block(1 + tx * 4, 1 + ty * 4, 4, 4, 'w', fl)
    for (tx, ty) in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (10, 0), (11, 0), (9, 1), (10, 1), (11, 1), (10, 2), (11, 2),
                     (0, 9), (1, 9), (0, 10), (1, 10), (2, 10), (0, 11), (1, 11), (10, 9), (11, 9), (9, 10), (10, 10), (11, 10), (10, 11), (11, 11),
                     (3, 3), (4, 1), (8, 7), (9, 7), (2, 7), (6, 9), (7, 9)):
        z.block(1 + tx * 4, 1 + ty * 4, 4, 4, 'g', fl)
    # groves in the four corners (cherry / maple) behind hedges, pools and pergolas in between
    for (c, r) in ((3, 3), (8, 6), (3, 9), (40, 3), (44, 8), (38, 9), (3, 38), (8, 41), (4, 44), (39, 38), (44, 37), (40, 44)):
        z.block(c, r, 3, 3, 'T')
    for c in range(2, 14):
        z.put(c, 16, '=')
    for r in range(3, 13):
        z.put(14, r, '=')
    for c in range(37, 48):
        z.put(c, 16, '=')
    for r in range(3, 13):
        z.put(35, r, '=')
    for c in range(2, 13):
        z.put(c, 33, '=')
    for r in range(37, 47):
        z.put(13, r, '=')
    for c in range(37, 48):
        z.put(c, 33, '=')
    for r in range(37, 47):
        z.put(35, r, '=')
    z.block(23, 23, 4, 4, 'W')
    z.block(7, 22, 4, 4, 'W')
    z.block(39, 23, 4, 4, 'W')
    z.block(19, 7, 6, 4, 'Q')
    z.block(25, 38, 6, 4, 'Q')
    for (c, r) in ((27, 4), (34, 4), (27, 12), (34, 12), (15, 36), (22, 36), (15, 44), (22, 44), (13, 20), (36, 20), (13, 29), (36, 29)):
        z.put(c, r, 'j')
    for (c, r) in ((1, 13), (48, 13), (1, 36), (48, 37)):   # rock pairs against the facade (low cover in the open would
        z.put(c, r, 'k')                                    # make pockets robots charging the player stick in)
        z.put(c, r + 1, 'k')
    for (c, r) in ((7, 27), (39, 21), (24, 21), (24, 28)):
        z.block(c, r, 2, 1, 'B')
    for (c, r) in ((16, 2), (33, 2), (12, 47), (37, 47), (2, 20), (47, 29)):
        z.put(c, r, 'o')
    z.block(4, 28, 2, 2, 'O')
    z.block(44, 19, 2, 2, 'O')
    z.put(18, 47, 'P')
    for (c, r) in ((9, 12), (41, 13), (8, 36), (41, 30), (3, 25), (46, 25), (30, 9), (32, 33), (17, 25), (32, 21), (45, 45), (9, 30)):
        z.put(c, r, 'S')
    z.put(6, 31, 'a')
    z.put(43, 31, 'a')
    z.put(22, 17, 'h')
    z.put(29, 31, 'h')
    # the glass roof: pyramids over the whole interior (no flat ceiling here)
    rf = z.layer('9')
    for ty in range(6):
        for tx in range(6):
            z.block(1 + tx * 8, 1 + ty * 8, 8, 8, '^', rf)
    return z


# ------------------------------------------------------------------ Trading Floor
def trading():
    z = Zone('spire_trading', 50, 62)
    z.gates(23, 35)
    mez = z.layer('4.5')
    # north executive deck (rows 1-12) and a west gallery (cols 1-6, rows 13-30)
    for r in range(1, 31):
        for c in range(1, 49):
            if r <= 12 or c <= 6:
                mez[r][c] = 'u'
    for r in range(1, 31):
        for c in range(1, 49):
            if mez[r][c] != 'u':
                continue
            if any(mez[r + dr][c + dc] == '.' and 0 < c + dc < 49 and 0 < r + dr < 61 for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))):
                mez[r][c] = 'r'
    z.block(30, 13, 4, 10, 'Z')
    z.block(40, 13, 2, 10, 'N')
    z.block(2, 31, 2, 10, 'N')
    for (c, r) in ((30, 12), (31, 12), (32, 12), (33, 12), (40, 12), (41, 12), (2, 30), (3, 30)):
        assert mez[r][c] == 'r', (c, r, mez[r][c])
        mez[r][c] = 'u'
    columns(z, mez, [(6, 16), (6, 24), (12, 12), (20, 12), (26, 12), (37, 12), (45, 12)])
    under_lights(z, mez, (3,), (6,))
    # ground: four rows of trading desks round the ticker, video walls, the bolt, lounges, plants
    for r in (27, 31, 35, 39):
        for c in (10, 16, 28, 34, 40):
            z.block(c, r, 4, 2, 'D')
        if r in (27, 39):
            z.block(22, r, 4, 2, 'D')
    for c in range(8, 14):
        z.put(c, 46, '#')
    for c in range(36, 42):
        z.put(c, 46, '#')
    z.block(23, 49, 3, 3, 'A')
    z.block(9, 54, 4, 3, 'L')
    z.block(42, 54, 4, 3, 'L')
    for (c, r) in ((7, 47), (14, 47), (35, 47), (42, 47), (2, 50), (47, 50), (47, 14), (47, 20), (8, 14)):
        z.put(c, r, 'p')
    for (c, r) in ((19, 52), (29, 52)):
        z.block(c, r, 2, 2, 'O')
    z.put(36, 59, 'P')
    for (c, r) in ((5, 45), (44, 45), (10, 22), (45, 26), (15, 4), (34, 4), (4, 8), (45, 8), (25, 17), (12, 50), (45, 40)):
        z.put(c, r, 'S')
    z.put(26, 44, 'a')
    z.put(21, 34, 'h')
    # executive deck: boardroom, executive desks, lounges, planters; spawns and pickups upstairs
    z.block(9, 2, 8, 6, 'M', mez, 'ul')
    z.block(36, 3, 4, 3, 'X', mez, 'ul')
    z.block(42, 3, 4, 3, 'X', mez, 'ul')
    z.block(22, 3, 4, 3, 'L', mez, 'ul')
    z.block(2, 20, 4, 3, 'L', mez, 'ul')
    for (c, r) in ((20, 9), (29, 9), (2, 14), (5, 28), (47, 9), (2, 2)):
        z.put(c, r, 'p', mez, 'ul')
    for (c, r) in ((3, 25), (27, 7), (44, 9), (13, 10)):
        z.put(c, r, 'S', mez, 'ul')
    z.put(4, 17, 'a', mez, 'ul')
    z.put(34, 8, 'h', mez, 'ul')
    # floor inlays: carpet under the desks, the star under the bolt
    fl = z.layer('0')
    tiles(z, fl, 'q', 9, 25, 10, 5)
    z.block(20, 46, 8, 8, 'x', fl)
    # ceiling: coffers over the floor, the ticker ring over the desks, downlights over the deck
    rf = z.layer('9')
    tiles(z, rf, '~', 9, 13, 10, 12, skip={(3, 4), (4, 4), (3, 5), (4, 5)})
    z.block(21, 29, 8, 8, 'Y', rf)
    for r in range(1, z.h - 1):
        for c in range(1, z.w - 1):
            if rf[r][c] == '.' and z.g[r][c] != '#' and ((r in (4, 9) and c % 4 == 3) or (c in (3, 7) and r % 4 == 2 and r > 12) or (r in (45, 47) and c % 4 == 1)):
                rf[r][c] = ':'
    return z


# ------------------------------------------------------------------ checks
def check(z):
    errs = []
    g, W, H = z.g, z.w, z.h
    mez = z.layers.get('4.5')
    at = lambda c, r: g[r][c] if 0 <= c < W and 0 <= r < H else '#'
    mt = lambda c, r: (mez[r][c] if mez and 0 <= c < W and 0 <= r < H else '#')
    G = [c for c in range(W) if g[0][c] == 'G']
    E = [c for c in range(W) if g[H - 1][c] == 'E']
    if len(G) != 3 or G[2] - G[0] != 2 or len(E) != 3 or E[2] - E[0] != 2:
        errs.append('gates')
    for c in G:
        if at(c, 1) not in GROUND_OPEN or at(c, 2) not in GROUND_OPEN:
            errs.append('exit gate needs 2 open rows')
    for c in E:
        if at(c, H - 2) not in GROUND_OPEN or at(c, H - 3) not in GROUND_OPEN:
            errs.append('entry gate needs 2 open rows')
    P = [(c, r) for r in range(H) for c in range(W) if g[r][c] == 'P']
    if len(P) != 1:
        return ['need one P']
    P = P[0]
    for dc in (-2, -1, 1, 2):
        if at(P[0] + dc, P[1] - 4) not in GROUND_OPEN:
            errs.append('weapon stand cell blocked')
    # stairs link the ground cell before the low end with the deck cell past the high end
    links = []
    for ch in STAIRS:
        for (c, r, w, h) in rects(g, ch):
            north = ch in 'NZ'
            lo = [(cc, r + h) for cc in range(c, c + w)] if north else [(cc, r - 1) for cc in range(c, c + w)]
            hi = [(cc, r - 1) for cc in range(c, c + w)] if north else [(cc, r + h) for cc in range(c, c + w)]
            for a, b in zip(lo, hi):
                if at(*a) not in GROUND_OPEN or mt(*b) not in DECK_OPEN:
                    errs.append('%s stair end blocked %s %s' % (ch, a, b))
                links.append((a, b))
    seen = {(0,) + P}
    q = deque([(0,) + P])
    while q:
        L, c, r = q.popleft()
        nb = []
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb.append((L, c + dc, r + dr))
        for a, b in links:
            if L == 0 and (c, r) == a:
                nb.append((1,) + b)
            if L == 1 and (c, r) == b:
                nb.append((0,) + a)
        for n in nb:
            if n in seen:
                continue
            ok = at(n[1], n[2]) in GROUND_OPEN if n[0] == 0 else mt(n[1], n[2]) in DECK_OPEN
            if ok:
                seen.add(n)
                q.append(n)
    sealed = [(c, r) for r in range(H) for c in range(W) if g[r][c] in GROUND_OPEN and (0, c, r) not in seen]
    if sealed:
        errs.append('%d sealed ground cells %s' % (len(sealed), sealed[:5]))
    if mez:
        dsealed = [(c, r) for r in range(H) for c in range(W) if mez[r][c] in DECK_OPEN and (1, c, r) not in seen]
        if dsealed:
            errs.append('%d sealed deck cells %s' % (len(dsealed), dsealed[:5]))
    if not any((0, c, 1) in seen for c in G):
        errs.append('no path to the exit')
    nS = 0
    for (L, grid, OPEN) in ((0, g, GROUND_OPEN), (1, mez, DECK_OPEN)):
        if grid is None:
            continue
        for r in range(H):
            for c in range(W):
                if grid[r][c] != 'S':
                    continue
                nS += 1
                if L == 0 and (c - P[0]) ** 2 + (r - P[1]) ** 2 < 14 ** 2:
                    errs.append('spawn (%d,%d) < 14 m from P' % (c, r))
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if (dc or dr) and grid[r + dr][c + dc] not in OPEN:
                            errs.append('spawn (%d,%d) L%d neighbour %r' % (c, r, L, grid[r + dr][c + dc]))
                if L == 1 and g[r][c] in STAIRS:
                    errs.append('deck spawn over a stair')
    if not 10 <= nS <= 16:
        errs.append('%d spawns' % nS)
    na = sum(row.count('a') for grid in [g] + ([mez] if mez else []) for row in grid)
    nh = sum(row.count('h') for grid in [g] + ([mez] if mez else []) for row in grid)
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for grid in [g] + list(z.layers.values()):
        for ch, (sw, sd) in PREFAB.items():
            for (c, r, w, h) in rects(grid, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('prefab %r %dx%d at (%d,%d)' % (ch, w, h, c, r))
    # deck props stand on the deck (never over the void or a stair)
    if mez:
        for r in range(H):
            for c in range(W):
                if mez[r][c] not in '.#ur' and g[r][c] in STAIRS:
                    errs.append('deck prop over a stair (%d,%d)' % (c, r))
    return errs


def main():
    ok = True
    for z in (lobby(), garden(), trading()):
        errs = check(z)
        print('%-16s %dx%d  %s' % (z.name, z.w, z.h, 'ok' if not errs else ''))
        for e in errs:
            print('   ERROR', e)
            ok = False
        with open(os.path.join(ZD, z.name + '.txt'), 'w') as f:
            f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
