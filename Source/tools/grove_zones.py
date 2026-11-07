#!/usr/bin/env python3
"""INKBOLT Redwood Hollow zones (theme 'grove'): hand-placed layouts -> src/data/zones/grove_*.txt

    python3 tools/grove_zones.py           # write + validate
    python3 tools/grove_zones.py --check   # validate only
    python3 tools/grove_zones.py --print   # also print the maps

Three 50 x 50 clearings in an old-growth redwood forest. Every zone has a floor plan and an "@layer 9" walkway
grid: the climbable redwoods ('Z', 8 x 8, never rotated) carry a platform at 9 m; '=' plank bridges (2 wide, always
east-west, between a tree's east side and the next tree's west side) join them, and the platform rails are layer
pieces placed here on every footprint edge cell except where a bridge lands and over the stairwell (the north edge
cells 4..7 and the east edge cell 1 of the footprint stay open). Trestle piers ('J', 1 x 2) stand under long bridges.
Symbols (src/data/themes/grove.js):
  Z climbable redwood 8x8   Y giant redwood 4x4   y young redwood   x snag 2x2   u stump 2x2   L fallen giant 6x2
  l small log 3x1   R boulder 2x2   r rock   b shrub / huckleberry   n fern   v oxalis   m mushrooms   w trilliums
  p pebbles   e sedge   k creek   W pond 5x5   C ranger station 7x6   T tent 3x3   F campfire 3x3   d woodpile 2x1
  i signpost   j lantern   c crate   q barrel   J bridge pier 1x2   : dirt trail (painted ground)   + S P E G a h .
  layer 9: = bridge   ^ _ [ ] platform rail (N S W E edge)   1 2 3 4 rail corner (NW NE SE SW)
"""
import sys

from zonekit import Zone, validate, write, OUT

W, H = 50, 50
GC = 24                 # gates on columns 24-26
PREFAB = {'Z': (8, 8), 'Y': (4, 4), 'x': (2, 2), 'u': (2, 2), 'L': (6, 2), 'l': (3, 1), 'R': (2, 2), 'W': (5, 5),
          'C': (7, 6), 'T': (3, 3), 'F': (3, 3), 'd': (2, 1), 'J': (1, 2)}
WALKABLE = set(':nvmwpekW')
GROUND = '.:'           # cells small plants may be scattered on


def shell(name):
    z = Zone(name, W, H)
    z.rect(0, 0, W, 1, '#')
    z.rect(0, H - 1, W, 1, '#')
    z.rect(0, 0, 1, H, '#')
    z.rect(W - 1, 0, 1, H, '#')
    z.rect(GC, 0, 3, 1, 'G')
    z.rect(GC, H - 1, 3, 1, 'E')
    z.put(25, 48, 'P')
    z.trees, z.bridges = [], []
    z.layer = [['.'] * W for _ in range(H)]
    return z


def tree(z, c, r):
    """climbable redwood with its footprint's top-left cell at (c, r)"""
    z.block(c, r, 8, 8, 'Z', over='.:')
    z.trees.append((c, r))


def bridge(z, a, b, piers=()):
    """bridge from tree a's east side to tree b's west side (same rows); piers at the given columns"""
    (ca, ra), (cb, rb) = a, b
    assert ra == rb, 'bridges run east-west between trees on the same rows'
    rows = (ra + 3, ra + 4)
    for r in rows:
        for c in range(ca + 8, cb):
            z.layer[r][c] = '='
    for c in piers:
        z.block(c, rows[0], 1, 2, 'J', over='.:nvmwpek')
    z.bridges.append((a, 'E', rows))
    z.bridges.append((b, 'W', rows))


def rails(z):
    for (c0, r0) in z.trees:
        skip = {(c0 + i, r0) for i in range(4, 8)} | {(c0 + 7, r0 + 1), (c0 + 7, r0 + 2)}
        for (t, side, rows) in z.bridges:
            if t != (c0, r0):
                continue
            for r in rows:
                skip.add((c0 + 7, r) if side == 'E' else (c0, r))
        for i in range(8):
            for j in range(8):
                c, r = c0 + i, r0 + j
                if (c, r) in skip or 0 < i < 7 and 0 < j < 7:
                    continue
                ch = {(0, 0): '1', (7, 0): '2', (7, 7): '3', (0, 7): '4'}.get((i, j))
                if ch is None:
                    ch = '^' if j == 0 else '_' if j == 7 else '[' if i == 0 else ']'
                assert z.layer[r][c] == '.', (z.name, c, r)
                z.layer[r][c] = ch


def trail(z, pts, w=2):
    """dirt trail through way points (axis-aligned legs), w cells wide, painted over open ground only"""
    for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
        if c0 == c1:
            for r in range(min(r0, r1), max(r0, r1) + 1):
                z.pave(c0, r, w, 1, ':')
        else:
            for c in range(min(c0, c1), max(c0, c1) + 1):
                z.pave(c, r0, 1, w, ':')


def creek(z, pts, w=2):
    """creek through way points (axis-aligned legs); overwrites trail paint (a ford)"""
    for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
        if c0 == c1:
            for r in range(min(r0, r1), max(r0, r1) + 1):
                z.pave(c0, r, w, 1, 'k', over='.:')
        else:
            for c in range(min(c0, c1), max(c0, c1) + 1):
                z.pave(c, r0, 1, w, 'k', over='.:')


def blocks(z, ch, pts, over='.:'):
    w, d = PREFAB[ch]
    for p in pts:
        c, r = p[0], p[1]
        if len(p) > 2 and p[2] == 'v':
            z.block(c, r, d, w, ch, over=over)
        else:
            z.block(c, r, w, d, ch, over=over)


def cells(z, ch, pts, over='.:'):
    z.puts(pts, ch, over=over)


def scatter(z, ch, n, seed, region=(2, 2, 47, 45), near=None, ground='.', avoid=8, ok=None):
    """n cells of `ch` on plain ground, a fixed pseudo-random pattern; near: symbols at least one of the 8 neighbours
    must hold (ferns along logs and trees); avoid: keep this many cells clear of P"""
    c0, r0, c1, r1 = region
    x = seed * 7919 + 13
    placed, tries = 0, 0
    while placed < n and tries < n * 400:
        tries += 1
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        c = c0 + (x >> 8) % (c1 - c0 + 1)
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        r = r0 + (x >> 8) % (r1 - r0 + 1)
        if z.g[r][c] not in ground or abs(c - 25) + abs(r - 48) < avoid:
            continue
        if near and not any(z.at(c + dc, r + dr) in near for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
            continue
        if any(z.at(c + dc, r + dr) in 'SGE' for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
            continue
        if ok and not ok(c, r):
            continue
        z.g[r][c] = ch
        placed += 1
    return placed


def keep_clear(z):
    """the cells around spawns, gates, the weapon stand and the climbing start stay open: mark them before the scatter"""
    hold = []
    for (c0, r0) in z.trees:   # the stairs start at the SW corner: keep the approach from west and south open
        for (c, r) in [(c0 - 1, r0 + 6), (c0 - 1, r0 + 7), (c0 - 1, r0 + 8), (c0, r0 + 8), (c0 + 1, r0 + 8), (c0 - 2, r0 + 7), (c0, r0 + 9)]:
            if 0 < c < W - 1 and 0 < r < H - 1 and z.g[r][c] in '.:':
                hold.append((c, r, z.g[r][c]))
                z.g[r][c] = '+'
    for c in range(23, 28):
        for r in range(42, 48):
            if z.g[r][c] == '.':
                hold.append((c, r, '.'))
                z.g[r][c] = '+'
    return hold


def release(z, hold):
    for c, r, ch in hold:
        z.g[r][c] = ch


def nearest(z, c, r, ok):
    """the cell nearest (c, r) (spiral search) for which ok(c, r) holds"""
    for d in range(0, 12):
        for dc in range(-d, d + 1):
            for dr in range(-d, d + 1):
                if max(abs(dc), abs(dr)) == d and 1 <= c + dc < W - 1 and 1 <= r + dr < H - 1 and ok(c + dc, r + dr):
                    return c + dc, r + dr
    raise AssertionError('%s: nothing free near (%d,%d)' % (z.name, c, r))


def spawns(z, pts):
    """spawn cans at (or next to) the given cells: 3 x 3 open ground around, >= 14 m from P"""
    def ok(c, r):
        return (c - 25) ** 2 + (r - 48) ** 2 >= 15 ** 2 and all(z.g[r + dr][c + dc] in '.:' for dc in (-1, 0, 1) for dr in (-1, 0, 1)) \
            and all(z.at(c + dc, r + dr) != 'S' for dc in range(-3, 4) for dr in range(-3, 4))
    z.spawn_pts = []
    for (c, r) in pts:
        c, r = nearest(z, c, r, ok)
        z.put(c, r, 'S', over='.:')
        z.spawn_pts.append((c, r))


def pickups(z, ch, pts):
    for (c, r) in pts:
        c, r = nearest(z, c, r, lambda c, r: z.g[r][c] in '.:' and all(z.at(c + dc, r + dr) in '.:nvmwpek' for dc in (-1, 0, 1) for dr in (-1, 0, 1)))
        z.put(c, r, ch, over='.:')


def dress(z, seed, ferns=48, clover=20, shrubs=22, young=10, misc=True):
    """undergrowth: ferns hug trunks, logs and rocks; oxalis carpets; shrubs; young redwoods; small things"""
    hold = keep_clear(z)
    for (c, r) in z.spawn_pts:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if z.g[r + dr][c + dc] in '.:':
                    hold.append((c + dc, r + dr, z.g[r + dr][c + dc]))
                    z.g[r + dr][c + dc] = '+'
    scatter(z, 'n', ferns // 2, seed + 1, near='ZYxuLlRr#k')
    scatter(z, 'n', ferns - ferns // 2, seed + 2)
    scatter(z, 'v', clover, seed + 3)
    scatter(z, 'b', shrubs, seed + 4, avoid=10)
    def clear_sky(c, r):   # young redwood crowns (5..19 m up, 2.6 m wide) stay clear of the platforms and bridges
        return not any(z.at(c + dc, r + dr) == 'Z' or (0 <= r + dr < H and 0 <= c + dc < W and z.layer[r + dr][c + dc] == '=')
                       for dc in range(-3, 4) for dr in range(-3, 4))
    scatter(z, 'y', young, seed + 5, avoid=12, ok=clear_sky)
    if misc:
        scatter(z, 'm', 9, seed + 6, near='ZYxuLl')
        scatter(z, 'w', 10, seed + 7)
        scatter(z, 'p', 8, seed + 8)
        scatter(z, 'r', 10, seed + 9, avoid=10)
        scatter(z, 'e', 14, seed + 10, near='kW')
    release(z, hold)


def finish(z, ammo, health):
    pickups(z, 'a', ammo)
    pickups(z, 'h', health)
    rails(z)
    errs, stats = validate(z, WALKABLE, PREFAB)
    for (c0, r0) in z.trees:   # the stairs start must be reachable from open ground
        if z.at(c0 - 1, r0 + 7) not in WALKABLE | set('.'):
            errs.append('tree at (%d,%d): stairs start blocked' % (c0, r0))
    return z, errs, stats


# ---------------------------------------------------------------- zone 1: Ranger Station (creek, camp, two skyways)
def ranger():
    z = shell('grove_1')
    A, B, Cc, D = (5, 24), (37, 24), (12, 5), (31, 5)
    for t in (A, B, Cc, D):
        tree(z, *t)
    bridge(z, A, B, piers=(19, 30))
    bridge(z, Cc, D, piers=(28,))
    trail(z, [(25, 47), (25, 40), (21, 40), (21, 34), (25, 34), (25, 16), (24, 16), (24, 1)])
    trail(z, [(26, 41), (33, 41)])
    creek(z, [(1, 19), (9, 19), (9, 20), (17, 20), (17, 19), (30, 19), (30, 20), (40, 20), (40, 18), (48, 18)])
    blocks(z, 'C', [(35, 35)])
    blocks(z, 'F', [(29, 43)])
    blocks(z, 'T', [(43, 43), (40, 45)])
    blocks(z, 'd', [(33, 36)])
    cells(z, 'c', [(42, 37), (42, 38)])
    cells(z, 'q', [(34, 41)])
    cells(z, "j", [(22, 46), (27, 38), (23, 22), (27, 13)])
    cells(z, 'i', [(27, 45), (23, 16)])
    blocks(z, 'Y', [(42, 3), (3, 39), (14, 41)])
    blocks(z, 'L', [(15, 30), (31, 13)])
    blocks(z, 'L', [(45, 26, 'v')])
    blocks(z, 'l', [(3, 15), (36, 22), (8, 34)])
    blocks(z, 'R', [(19, 25), (28, 26), (2, 2), (45, 13), (10, 45)])
    blocks(z, "u", [(16, 36), (40, 33), (4, 9)])
    blocks(z, 'x', [(33, 29)])
    spawns(z, [(4, 3), (24, 4), (46, 9), (3, 21), (20, 23), (46, 22), (16, 15), (34, 15), (4, 32), (46, 34), (31, 34), (13, 26)])
    dress(z, 10)
    return finish(z, [(20, 31), (38, 3), (47, 39)], [(29, 23), (7, 14), (13, 46)])


# ---------------------------------------------------------------- zone 2: Giants' Ridge (long skyway, giants, boulders)
def giants():
    z = shell('grove_2')
    A, B, Cc, D = (2, 8), (40, 8), (14, 29), (29, 29)
    for t in (A, B, Cc, D):
        tree(z, *t)
    bridge(z, A, B, piers=(17, 25, 32))
    bridge(z, Cc, D)
    trail(z, [(25, 47), (25, 39), (27, 39), (27, 25), (23, 25), (23, 1)])
    blocks(z, 'W', [(7, 21)])
    creek(z, [(12, 23), (13, 23)], w=1)
    blocks(z, 'Y', [(33, 19), (11, 40), (39, 41), (19, 2), (45, 23)])
    blocks(z, 'L', [(15, 19), (30, 2), (3, 43)])
    blocks(z, 'L', [(45, 31, 'v')])
    blocks(z, 'l', [(39, 37), (6, 33), (19, 43)])
    blocks(z, 'R', [(28, 18), (16, 14), (34, 13), (44, 17), (3, 28), (19, 23), (31, 43), (7, 2)])
    blocks(z, 'u', [(25, 8), (8, 36), (43, 45)])
    blocks(z, 'x', [(36, 25), (2, 18)])
    spawns(z, [(4, 4), (30, 6), (46, 4), (13, 7), (40, 21), (3, 25), (21, 17), (12, 28), (39, 28), (46, 35), (5, 39), (34, 33)])
    dress(z, 20, ferns=50, clover=20, shrubs=24, young=11)
    return finish(z, [(29, 23), (11, 16), (44, 46)], [(23, 34), (37, 2), (6, 46)])


# ---------------------------------------------------------------- zone 3: Fern Gully (pond, creek, three-tree skyway)
def gully():
    z = shell('grove_3')
    A, B, Cc = (3, 18), (21, 18), (39, 18)
    for t in (A, B, Cc):
        tree(z, *t)
    bridge(z, A, B, piers=(14,))
    bridge(z, B, Cc, piers=(34,))
    trail(z, [(25, 47), (25, 37), (18, 37), (18, 28), (16, 28), (16, 12), (24, 12), (24, 1)])
    blocks(z, 'W', [(35, 30)])
    creek(z, [(36, 35), (36, 38), (30, 38), (30, 42), (20, 42), (20, 44), (1, 44)])
    blocks(z, 'Y', [(4, 3), (40, 3), (6, 30), (43, 38)])
    blocks(z, 'L', [(28, 4), (9, 38)])
    blocks(z, 'L', [(31, 25, 'v')])
    blocks(z, 'l', [(17, 6), (40, 27), (2, 35)])
    blocks(z, 'R', [(12, 13), (29, 13), (45, 13), (10, 26), (44, 31), (23, 29), (2, 40)])
    blocks(z, 'u', [(35, 8), (12, 2), (27, 34)])
    blocks(z, 'x', [(19, 33), (46, 45)])
    spawns(z, [(4, 12), (21, 3), (34, 3), (46, 9), (11, 9), (2, 28), (13, 31), (29, 29), (46, 27), (40, 44), (8, 34), (21, 39)])
    dress(z, 30, ferns=54, clover=20, shrubs=22, young=10)
    return finish(z, [(26, 27), (8, 15), (44, 35)], [(15, 30), (32, 8), (5, 46)])


def text(z):
    return z.text() + '@layer 9\n' + '\n'.join(''.join(row) for row in z.layer) + '\n'


def main():
    zones = [ranger(), giants(), gully()]
    ok = write(zones, check_only=True)
    if '--check' not in sys.argv:
        import os
        for z, _, _ in zones:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(text(z))
    if '--print' in sys.argv:
        for z, _, _ in zones:
            print('\n' + text(z))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
