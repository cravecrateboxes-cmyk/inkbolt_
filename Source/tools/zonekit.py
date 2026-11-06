"""INKBOLT hand-placed zone helper shared by tools/castle_zones.py and tools/city2_zones.py.

A Zone is an ASCII grid (1 char = 1 m, row 0 = north / exit, last row = south / entry). Layout scripts fill it with
rect / block / put / run calls (block and put refuse to overwrite anything but floor, so a typo can't silently bury a
prop), then validate() mirrors the theme unit tests: one P, GGG on row 0 and EEE on the last row with two open rows
in front, BFS reachability from P, 10-14 spawn cans >= 14 m from P with 3 x 3 open ground, 2-3 ammo / health, the
weapon-stand cells 4 rows in front of P, prefab blocks that tile their footprint exactly.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))


class Zone:
    def __init__(self, name, w, h, fill='.'):
        self.name, self.w, self.h = name, w, h
        self.g = [[fill] * w for _ in range(h)]

    def at(self, c, r):
        return self.g[r][c] if 0 <= c < self.w and 0 <= r < self.h else '#'

    def rect(self, c0, r0, w, h, ch):
        """Overwrite a rectangle (walls, paving)."""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 <= c < self.w and 0 <= r < self.h, (self.name, c, r, ch)
                self.g[r][c] = ch

    def pave(self, c0, r0, w, h, ch, over='.'):
        """Paint floor symbols, only over plain floor (or the symbols in `over`)."""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if 0 <= c < self.w and 0 <= r < self.h and self.g[r][c] in over:
                    self.g[r][c] = ch

    def block(self, c0, r0, w, h, ch, over='.'):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 <= c < self.w and 0 <= r < self.h, (self.name, c, r, ch)
                assert self.g[r][c] in over, '%s: block %r at (%d,%d) hits %r' % (self.name, ch, c, r, self.g[r][c])
        self.rect(c0, r0, w, h, ch)

    def put(self, c, r, ch, over='.'):
        assert 0 <= c < self.w and 0 <= r < self.h, (self.name, c, r, ch)
        assert self.g[r][c] in over, '%s: (%d,%d) is %r, not floor (placing %r)' % (self.name, c, r, self.g[r][c], ch)
        self.g[r][c] = ch

    def puts(self, pts, ch, over='.'):
        for c, r in pts:
            self.put(c, r, ch, over)

    def run(self, c0, r0, n, ch, vertical=False, over='.'):
        for k in range(n):
            self.put(c0, r0 + k, ch, over) if vertical else self.put(c0 + k, r0, ch, over)

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


def rects(g, ch):
    """Mirror of zones.js rects(): greedy rectangles of one symbol."""
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


def validate(z, walkable, prefabs, size=((50, 64), (44, 58)), first=False):
    """walkable: set of symbols you can stand on; prefabs: {symbol: (w, d)}. Returns (errors, stats)."""
    g, errs = z.g, []
    find = lambda ch: [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] == ch]
    W = set(walkable) | set('.PEGah')
    (w0, w1), (h0, h1) = size
    if not (w0 <= z.w <= w1 and h0 <= z.h <= h1):
        errs.append('size %dx%d' % (z.w, z.h))
    Ps = find('P')
    if len(Ps) != 1:
        return ['need exactly one P'], {}
    P0 = Ps[0]
    G, E = find('G'), find('E')
    if len(G) != 3 or any(r != 0 for c, r in G) or G[2][0] - G[0][0] != 2:
        errs.append('exit gate must be GGG on row 0')
    if len(E) != 3 or any(r != z.h - 1 for c, r in E) or E[2][0] - E[0][0] != 2:
        errs.append('entry gate must be EEE on the last row')
    for c, r in G:
        for k in (1, 2):
            if z.at(c, r + k) not in W:
                errs.append('exit gate needs 2 open rows in front (%d,%d)' % (c, r + k))
    for c, r in E:
        for k in (1, 2):
            if z.at(c, r - k) not in W:
                errs.append('entry gate needs 2 open rows behind (%d,%d)' % (c, r - k))
    seen = {P0}
    q = deque([P0])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if n not in seen and z.at(*n) in W:
                seen.add(n)
                q.append(n)
    if not any((c, 1) in seen for c, r in G):
        errs.append('no path from P to the exit')
    S = find('S')
    for (c, r) in S:
        if not any((c + dc, r + dr) in seen for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            errs.append('spawn (%d,%d) sealed' % (c, r))
        if (c - P0[0]) ** 2 + (r - P0[1]) ** 2 < 14 ** 2:
            errs.append('spawn (%d,%d) < 14 m from P' % (c, r))
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if (dc or dr) and z.at(c + dc, r + dr) not in W:
                    errs.append('spawn (%d,%d) neighbour (%d,%d) is %r' % (c, r, c + dc, r + dr, z.at(c + dc, r + dr)))
    if not 10 <= len(S) <= 14:
        errs.append('%d spawns' % len(S))
    na, nh = len(find('a')), len(find('h'))
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for dc in (-2, -1, 1, 2):
        if z.at(P0[0] + dc, P0[1] - 4) not in W:
            errs.append('weapon stand cell (%d,%d) blocked' % (P0[0] + dc, P0[1] - 4))
    for ch, (sw, sd) in prefabs.items():
        for (c, r, w, h) in rects(g, ch):
            if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                errs.append('prefab %r block %dx%d at (%d,%d) does not tile %dx%d' % (ch, w, h, c, r, sw, sd))
    # every open cell reachable (no sealed pockets)
    opn = [(c, r) for r in range(z.h) for c in range(z.w) if g[r][c] in W and g[r][c] not in 'EG']
    sealed = [p for p in opn if p not in seen]
    if sealed:
        errs.append('%d sealed open cells, e.g. %s' % (len(sealed), sealed[:4]))
    stats = {'size': '%dx%d' % (z.w, z.h), 'open': len(opn), 'spawns': len(S), 'area': z.w * z.h}
    return errs, stats


def write(zones, check_only=False):
    ok = True
    for z, errs, stats in zones:
        print('%-22s %s' % (z.name, stats))
        for e in errs:
            print('   ERROR', e)
            ok = False
        if not check_only:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
    if '--print' in sys.argv:
        for z, _, _ in zones:
            print('\n' + z.name)
            print(z.text())
    return ok
