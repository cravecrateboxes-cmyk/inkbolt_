#!/usr/bin/env python3
"""INKBOLT Kolvane Station K-7 zones (theme 'arctic'): hand-placed layouts -> src/data/zones/arctic_{1,2}.txt

    python3 tools/arctic_zones.py            # write + validate
    python3 tools/arctic_zones.py --print    # ... and print the maps
    python3 tools/arctic_zones.py --check    # validate only

Zone 1, the buried surface works (64 x 66, open sky): the trench cut down to the half-buried station (south half: the
collapsed radar dome, the snowcat, the fuel depot, sledges, masts and a weather mast out of the drifts, a buried hut's
roof, the buried 1987 lab module whose roof you can climb onto up snow steps), the entry ramp in the south wall buried
by a snow slide; the station's upper modules (north half, 3.7 m ceiling on "@layer 3.7"): the corridor, four bunk
rooms, the comms room, the shaft head room with the winch and the shaft door (exit), the mess hall, the hall and boot
room behind the front airlock, the science office. Three ways in from the trench: the airlock, the side door, and the
breach the ice tore in the mess hall wall. Floor finishes on "@layer 0.01".
Zone 2, the deep labs (66 x 62, a 12 m ice ceiling): the shaft foot hall (entry), the frozen corridors, the drill-core
archive and the cryo lab (lab ceilings at 4.4 m, "@layer 4.4"), the sealed vault (breakable door) between them and the
hall, the generator hall with its catwalk gallery and bridge ("@layer 4.5"), and the ice cavern the drill broke into
(north): the frozen relic in its north wall, a scaffold catwalk in front of it at 4.5 m and a high platform at 7 m
("@layer 7"); hanging ice and lamps on "@layer 12".
Walls in zone 2 are two cells thick (each module has one face); the station's interior walls in zone 1 are one cell
thick (its interior modules are finished on both faces). Symbols: see src/data/themes/arctic.js.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))

SIZES = {'D': (3, 2), 'd': (3, 1), 'B': (3, 2), ',': (3, 2), 'L': (3, 2), 'l': (3, 2), 'V': (3, 2),
         'K': (8, 8), 'Q': (4, 6), 'T': (3, 6), 'Y': (2, 4), 'M': (2, 2), 'H': (6, 4), 'U': (8, 3), 'g': (3, 2), 'O': (2, 2),
         'Z': (3, 4), 'z': (3, 4), 'm': (4, 2), 'n': (4, 1), 'p': (2, 1), 'b': (2, 1), 'e': (2, 1), 't': (2, 1), 'R': (2, 1),
         'A': (3, 2), 'j': (2, 1), 'J': (2, 1), 'I': (2, 2), '@': (4, 3), 'C': (3, 1), 'F': (3, 2), 'q': (2, 2), 's': (2, 1),
         '[': (3, 1), ']': (3, 1), '(': (4, 6), ')': (4, 4), '}': (3, 2), '|': (4, 1), '&': (2, 1), '!': (3, 1), '?': (2, 1),
         '/': (2, 2), '$': (14, 6), 'X': (3, 8), 'N': (3, 8), '<': (3, 6), '^': (3, 3)}
DOORS = 'DdBLlV,'
STAIRS = {'X': ('0', '4.5', -1), 'N': ('0', '4.5', 1), '<': ('4.5', '7', -1), 'Z': ('0', 'roof', -1), 'z': ('0', 'roof', 1)}
WALK_FLOOR = set('.SahPEG' + DOORS)
DECK = 'w'
TILES = '=-+_%~'


def hsh(a, b, k=0):
    h = (a * 374761393 + b * 668265263 + k * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296.0


class Zone:
    def __init__(self, name, W, H, gate, entry, P0):
        self.name, self.W, self.H = name, W, H
        self.g = {'0': self.grid('.')}
        f = self.g['0']
        for r in range(H):
            for c in range(W):
                if r in (0, H - 1) or c in (0, W - 1):
                    f[r][c] = '#'
        for c in range(gate, gate + 3):
            f[0][c] = 'G'
        if entry is not None:
            for c in range(entry, entry + 3):
                f[H - 1][c] = 'E'
        self.P0 = P0
        f[P0[1]][P0[0]] = 'P'
        self.links = []
        self.openings = {}    # (layer, c, r) deck cell where a stair arrives -> the stair's side (dc, dr)
        self.roof = set()

    def grid(self, fill):
        return [[fill] * self.W for _ in range(self.H)]

    def L(self, y):
        if y not in self.g:
            self.g[y] = self.grid('.')
        return self.g[y]

    def at(self, y, c, r):
        if y not in self.g or not (0 <= c < self.W and 0 <= r < self.H):
            return '#' if y == '0' else '.'
        return self.g[y][r][c]

    def fill(self, y, c0, r0, w, h, ch, over='.'):
        g = self.L(y)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 <= c < self.W and 0 <= r < self.H, (self.name, y, c, r, ch)
                assert g[r][c] in over, '%s @%s: %r at (%d,%d) hits %r' % (self.name, y, ch, c, r, g[r][c])
                g[r][c] = ch

    def wall(self, c0, r0, w, h):
        self.fill('0', c0, r0, w, h, '#', over='.#')

    def clear(self, c0, r0, w, h):
        self.fill('0', c0, r0, w, h, '.', over='.#')

    def put(self, ch, c, r, y='0'):
        self.fill(y, c, r, 1, 1, ch)

    def puts(self, ch, pts, y='0'):
        for c, r in pts:
            self.put(ch, c, r, y)

    def block(self, ch, c, r, turned=False, y='0', over='.'):
        w, h = SIZES[ch]
        if turned:
            w, h = h, w
        self.fill(y, c, r, w, h, ch, over)
        if ch == 'U':
            for rr in range(r, r + h):
                for cc in range(c, c + w):
                    self.roof.add((cc, rr))
        return (c, r, w, h)

    def door(self, ch, c, r, vertical=False):
        """a door block in a wall line (the cells must be wall)"""
        w, h = SIZES[ch]
        if vertical:
            w, h = h, w
        self.fill('0', c, r, w, h, ch, over='#')

    def stair(self, ch, c, r):
        y0, y1, d = STAIRS[ch]
        w, h = SIZES[ch]
        self.block(ch, c, r, y=y0, over='.' if y0 == '0' else '.w')
        for x in range(c, c + w):
            top = r - 1 if d < 0 else r + h
            foot = r + h if d < 0 else r - 1
            if c < x < c + w - 1:
                self.links.append((y0, x, foot, y1, x, top))
            self.openings[(y1, x, top)] = (0, 1 if d < 0 else -1)

    def finish(self, c0, r0, w, h, ch, over='.'):
        """floor finish (layer 0.01) over the open / prop cells of a rectangle"""
        f = self.L('0.01')
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if 0 <= c < self.W and 0 <= r < self.H and self.at('0', c, r) not in '#GE' + DOORS and f[r][c] in over:
                    f[r][c] = ch

    def ceiling(self, y, c0, r0, w, h, rnd_seed=0):
        """ceiling tiles over the open / prop cells of a rectangle: a light every 4 m (some dead), vents, broken tiles"""
        g = self.L(y)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at('0', c, r) in '#GE' + DOORS or g[r][c] != '.':
                    continue
                k = hsh(c, r, rnd_seed)
                if c % 4 == 2 and r % 4 == 2:
                    ch = '+' if k < 0.6 else '_'
                elif k < 0.02:
                    ch = '%'
                elif k < 0.05:
                    ch = '~'
                else:
                    ch = '=' if (c + r) % 2 else '-'
                g[r][c] = ch

    def rails(self, y):
        """rail every deck cell of layer y that borders open space (not where a stair arrives)"""
        g = self.g[y]
        todo = []
        for r in range(1, self.H - 1):
            for c in range(1, self.W - 1):
                if g[r][c] != DECK:
                    continue
                side = self.openings.get((y, c, r))
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (dc, dr) == side:
                        continue   # where the stair arrives
                    if self.at(y, c + dc, r + dr) == '.' and self.at('0', c + dc, r + dr) != '#':
                        todo.append((c, r))
                        break
        for c, r in todo:
            g[r][c] = 'r'

    def text(self):
        out = [''.join(row) for row in self.g['0']]
        for y in sorted((k for k in self.g if k != '0'), key=float):
            out.append('@layer ' + y)
            out += [''.join(row) for row in self.g[y]]
        return '\n'.join(out) + '\n'


# ================================================================ validation
def validate(z):
    errs = []
    W, H = z.W, z.H
    f = z.g['0']
    for y, g in z.g.items():
        seen = set()
        for r in range(H):
            for c in range(W):
                ch = g[r][c]
                if ch in SIZES and (c, r) not in seen:
                    w = 1
                    while c + w < W and g[r][c + w] == ch and (c + w, r) not in seen:
                        w += 1
                    h = 1
                    while r + h < H and all(g[r + h][c + k] == ch for k in range(w)):
                        h += 1
                    for rr in range(r, r + h):
                        for cc in range(c, c + w):
                            seen.add((cc, rr))
                    sw, sd = SIZES[ch]
                    if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                        errs.append('@%s prefab %r %dx%d at (%d,%d) vs %dx%d' % (y, ch, w, h, c, r, sw, sd))
                    if ch in DOORS:   # a door block's ends sit against wall
                        ends = [(c - 1, r + k) for k in range(h)] + [(c + w, r + k) for k in range(h)] if w > h else \
                               [(c + k, r - 1) for k in range(w)] + [(c + k, r + h) for k in range(w)]
                        for (a, b) in ends:
                            if z.at('0', a, b) != '#':
                                errs.append('door %r at (%d,%d) end (%d,%d) is %r' % (ch, c, r, a, b, z.at('0', a, b)))

    def walk(y, c, r):
        if y == '0':
            return z.at('0', c, r) in WALK_FLOOR
        if y == 'roof':
            return (c, r) in z.roof
        return z.at(y, c, r) in DECK + 'Sah'
    layers = ['0', 'roof'] + [y for y in z.g if y in ('4.5', '7')]
    P0 = z.P0
    start = ('0', P0[0], P0[1])
    seen = {start}
    q = deque([start])
    adj = {}
    for a in z.links:
        adj.setdefault((a[0], a[1], a[2]), []).append((a[3], a[4], a[5]))
        adj.setdefault((a[3], a[4], a[5]), []).append((a[0], a[1], a[2]))
    while q:
        y, c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (y, c + dc, r + dr)
            if n not in seen and walk(*n):
                seen.add(n)
                q.append(n)
        for n in adj.get((y, c, r), []):
            if n not in seen and walk(*n):
                seen.add(n)
                q.append(n)
    sealed = [(y, c, r) for y in layers for r in range(H) for c in range(W) if walk(y, c, r) and z.at('0', c, r) not in 'EG' and (y, c, r) not in seen]
    if sealed:
        errs.append('%d sealed cells, e.g. %s' % (len(sealed), sealed[:6]))
    for a in z.links:
        if not walk(a[0], a[1], a[2]):
            errs.append('stair foot %s not walkable (%r)' % (str(a[:3]), z.at(*a[:3])))
        if not walk(a[3], a[4], a[5]):
            errs.append('stair top %s not walkable' % (str(a[3:]),))
    G = [c for c in range(W) if f[0][c] == 'G']
    for c in G:
        for k in (1, 2):
            if f[k][c] != '.':
                errs.append('exit approach (%d,%d) %r' % (c, k, f[k][c]))
    if not any(('0', c, 1) in seen for c in G):
        errs.append('no path to the exit')
    E = [c for c in range(W) if f[H - 1][c] == 'E']
    for c in E:
        for k in (2, 3):
            if f[H - k][c] not in '.P':
                errs.append('entry approach (%d,%d) %r' % (c, H - k, f[H - k][c]))
    S, na, nh = [], 0, 0
    for r in range(H):
        for c in range(W):
            ch = f[r][c]
            if ch == 'S':
                S.append((c, r))
                if (c - P0[0]) ** 2 + (r - P0[1]) ** 2 < 14 ** 2:
                    errs.append('spawn %s < 14 m from P' % str((c, r)))
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if (dc or dr) and z.at('0', c + dc, r + dr) not in '.SahP':
                            errs.append('spawn %s neighbour %r' % (str((c, r)), z.at('0', c + dc, r + dr)))
            na += ch == 'a'
            nh += ch == 'h'
    if not 10 <= len(S) <= 14:
        errs.append('%d spawns' % len(S))
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for dc in (-2, -1, 1, 2):
        if z.at('0', P0[0] + dc, P0[1] - 4) != '.':
            errs.append('weapon stand cell (%d,%d) %r' % (P0[0] + dc, P0[1] - 4, z.at('0', P0[0] + dc, P0[1] - 4)))
    # nothing hangs into the catwalks / platforms, no deck over a deck
    for y in ('4.5', '7'):
        if y not in z.g:
            continue
        for r in range(H):
            for c in range(W):
                if z.at(y, c, r) != '.':
                    if f[r][c] in '()$)/' or (y == '7' and z.at('4.5', c, r) != '.') or ('4.4' in z.g and z.at('4.4', c, r) != '.'):
                        errs.append('@%s deck over %r / another deck at (%d,%d)' % (y, f[r][c], c, r))
    stats = {'size': '%dx%d' % (W, H), 'walk': len(seen), 'spawns': len(S)}
    return errs, stats


# ================================================================ zone 1: the buried surface works
def zone1():
    W, H = 64, 66
    z = Zone('arctic_1', W, H, gate=30, entry=None, P0=(31, 61))
    # ---- the station block (rows 1 - 31) and its facade (rows 32 - 33)
    z.wall(1, 32, 62, 2)
    z.wall(1, 13, 62, 1)
    z.wall(1, 18, 62, 1)
    for c in (8, 16, 24, 39, 51):
        z.wall(c, 1, 1, 12)
    for c in (23, 40):
        z.wall(c, 19, 1, 13)
    z.wall(24, 25, 16, 1)
    z.clear(29, 25, 6, 1)      # hall -> boot room
    z.clear(28, 13, 8, 1)      # corridor -> shaft head room
    z.clear(28, 18, 8, 1)      # corridor -> hall
    for c in (3, 11, 19, 44, 56):
        z.door('d', c, 13)
    for c in (9, 17, 50):
        z.door('d', c, 18)
    z.door('d', 23, 21, vertical=True)
    z.door('d', 40, 21, vertical=True)
    z.door('D', 30, 32)        # the front airlock
    z.door('D', 53, 32)        # the side door into the science office
    z.door('B', 8, 32)         # the breach the ice tore into the mess hall
    # bunk rooms A (1-7), B (9-15), C (17-23), D (52-62): bunks on the long walls, lockers by the door, a desk
    for (c0, c1) in ((1, 7), (9, 15), (17, 23)):
        for r in (2, 5, 8):
            z.block('b', c0, r, turned=True)
            z.block('b', c1, r, turned=True)
        z.puts('i', [(c0, 11), (c1, 11), (c1, 12)])
        z.block('e', c0 + 2, 1)
        z.put('k', c0 + 4, 10)
    for c in (53, 56, 59):
        z.block('b', c, 1)
    for r in (4, 8):
        z.block('b', 62, r, turned=True)
    z.block('I', 52, 9)
    z.puts('i', [(52, 1), (61, 12), (62, 12)])
    z.block('e', 55, 12)
    z.put('k', 55, 7)
    # comms (40 - 50): radio racks and the dead terminal on the north wall, the map table, desks, files
    z.block('R', 41, 1); z.block('R', 44, 1); z.block('t', 47, 1)
    z.block('A', 44, 6)
    z.block('e', 50, 4, turned=True); z.block('e', 50, 8, turned=True)
    z.puts('y', [(40, 11), (40, 12), (40, 1)])
    z.puts('k', [(43, 5), (48, 9)])
    z.puts('x', [(49, 12)])
    # shaft head room (25 - 38): the winch, cable drums and boxes, the shaft door (exit) in the north wall
    z.block('@', 25, 3)
    z.block('e', 38, 4, turned=True)
    z.block('I', 37, 9)
    z.puts('x', [(25, 9), (25, 10), (26, 10), (35, 1), (36, 1)])
    z.puts('o', [(25, 12), (26, 12)])
    # corridor: ice in through the west end, a box, a fallen chair
    z.block('I', 1, 15)
    z.puts('x', [(34, 17), (62, 14)])
    z.put('k', 13, 16)
    # mess hall (1 - 22): galley and pantry on the west wall, four tables, chairs down, ice in at the north-east
    z.block('n', 1, 20, turned=True)
    z.block('p', 1, 25, turned=True); z.block('p', 1, 28, turned=True)
    for (c, r) in ((6, 21), (13, 21), (6, 26), (14, 26)):
        z.block('m', c, r)
    z.block('I', 21, 19)
    z.puts('k', [(11, 23), (18, 24), (5, 24), (19, 28), (12, 29)])
    # hall (24 - 39, 19 - 24) and boot room (26 - 31)
    z.puts('x', [(24, 19), (24, 20), (39, 24)])
    z.puts('k', [(26, 22)])
    z.block('!', 36, 19)                      # the station's rifle locker by the airlock
    z.block('J', 25, 26); z.block('J', 37, 26)
    z.block('j', 26, 29); z.block('j', 36, 29)
    z.puts('i', [(24, 30), (24, 31), (39, 30), (39, 31)])
    # science office (41 - 62): terminals on the north wall, desks, the core map table, files, ice through a window
    z.block('t', 42, 19); z.block('t', 45, 19); z.block('e', 55, 19); z.block('e', 58, 19)
    z.block('A', 46, 24)
    z.block('e', 62, 23, turned=True)
    z.puts('y', [(41, 26), (41, 27), (62, 26)])
    z.block('I', 59, 30)
    z.puts('k', [(44, 23), (52, 25), (57, 22)])
    # ---- the trench (rows 34 - 64)
    z.block('K', 4, 38)                       # the collapsed radar dome
    z.block('Q', 47, 44)                      # the snowcat
    z.block('T', 58, 52)                      # the fuel depot
    z.puts('o', [(54, 54), (55, 54), (54, 55), (54, 57), (55, 58), (56, 60)])
    z.puts('c', [(52, 59), (53, 59), (56, 50), (45, 51)])
    z.block('U', 15, 50)                      # the buried 1987 module (walkable roof) and its snow steps
    z.stair('Z', 17, 53)
    z.stair('z', 20, 46)
    z.block('H', 38, 37)                      # a buried hut's roof
    z.block('M', 25, 38); z.block('M', 59, 36); z.block('M', 2, 57)
    z.put('W', 34, 46)
    z.block('Y', 37, 50, turned=False); z.block('Y', 9, 53)
    z.puts('c', [(39, 51), (39, 52), (11, 55), (8, 52)])
    z.block('g', 25, 35)
    for (c, r) in ((15, 39), (33, 41), (44, 57), (24, 59), (5, 49), (52, 41), (40, 61), (13, 61), (29, 50)):
        z.block('O', c, r)
    z.puts('f', [(28, 57), (35, 57), (28, 53), (35, 53), (31, 44), (17, 44), (45, 41)])
    z.puts('o', [(13, 46), (13, 47), (36, 36), (50, 51)])
    # ---- spawns, pickups
    z.puts('S', [(4, 6), (20, 3), (31, 7), (46, 10), (58, 6), (8, 29), (11, 25), (51, 28), (12, 36), (44, 35), (3, 48), (58, 45), (46, 61)])
    z.puts('a', [(21, 58), (31, 10), (60, 21)])
    z.puts('h', [(52, 38), (11, 19), (36, 22)])
    # ---- floor finishes, ceiling
    z.finish(1, 1, 23, 12, '3')               # bunks A-C
    z.finish(52, 1, 11, 12, '3')              # bunk D
    z.finish(40, 1, 11, 12, '1'); z.finish(41, 19, 22, 13, '1')   # comms, science
    z.finish(1, 14, 62, 4, '1')               # corridor
    z.finish(25, 1, 14, 12, '5')              # shaft head room
    z.finish(30, 1, 3, 2, '9', over='5')
    z.finish(1, 19, 22, 13, '2')              # mess
    z.finish(24, 19, 16, 6, '1')              # hall
    z.finish(24, 26, 16, 6, '6')              # boot room grating
    for (c, r, w, h, ch) in ((7, 29, 5, 3, '7'), (30, 30, 3, 2, '7'), (53, 30, 3, 2, '7'), (1, 14, 4, 4, '0'), (20, 19, 3, 3, '0'),
                             (36, 8, 3, 4, '0'), (58, 29, 5, 3, '0'), (51, 8, 3, 4, '0'), (41, 3, 9, 2, '8'), (42, 21, 7, 2, '8'), (46, 26, 4, 2, '8')):
        z.finish(c, r, w, h, ch, over='123456')
    z.ceiling('3.7', 1, 1, 62, 31, 1)
    return z


# ================================================================ zone 2: the deep labs
def zone2():
    W, H = 66, 62
    z = Zone('arctic_2', W, H, gate=31, entry=31, P0=(32, 58))
    # ---- walls
    z.wall(1, 22, 64, 2)                       # cavern | labs
    z.wall(22, 24, 2, 24)                      # archive | cryo, vault corridor
    z.wall(1, 46, 21, 2)                       # archive | west corridor
    z.wall(24, 38, 18, 2)                      # cryo | vault, corridors
    z.wall(27, 40, 2, 5); z.wall(37, 40, 2, 5)  # vault sides
    z.wall(27, 45, 12, 2)                      # vault south
    z.wall(42, 24, 2, 36)                      # labs | generator hall
    z.clear(42, 51, 2, 4)                      # hall -> generator hall
    z.clear(50, 22, 8, 2)                      # generator hall -> cavern
    # ice outcrops: the cavern's flanks, the west caves
    for (c, r, w, h) in ((1, 1, 3, 4), (62, 1, 3, 6), (1, 17, 1, 5), (63, 15, 2, 7), (40, 1, 4, 2), (27, 19, 4, 3),
                         (6, 55, 3, 3), (14, 53, 3, 5), (1, 58, 3, 3), (19, 59, 4, 2)):
        z.wall(c, r, w, h)
    z.door('l', 9, 22)                         # cavern -> archive (the lab face south)
    z.door(',', 30, 22)                        # the breach into the cryo lab
    z.door('L', 10, 46)                        # archive -> west corridor
    z.door('L', 24, 38); z.door('L', 39, 38)   # cryo lab -> the vault corridors
    z.door('V', 31, 45)                        # the vault
    # ---- the drill-core archive (1 - 21, 24 - 45): rack runs, logging tables, core boxes
    for r in (27, 31, 35, 39):
        z.fill('0', 2, r, 9, 1, 'C')
        z.fill('0', 12, r, 9, 1, 'C')
    z.block('F', 3, 42); z.block('F', 15, 42)
    z.puts('v', [(1, 24), (1, 25), (21, 44), (20, 44), (21, 29), (1, 33)])
    # ---- the cryo lab (24 - 41, 24 - 37)
    for c in (34, 37):
        z.block('q', c, 25); z.block('q', c, 29)
    z.block('s', 24, 28, turned=True); z.block('s', 24, 32, turned=True)
    z.block('s', 41, 33, turned=True)
    z.block('[', 27, 31); z.block('[', 27, 34); z.block('[', 32, 34)
    z.block(']', 33, 37)
    z.puts('u', [(26, 25), (40, 27), (39, 32), (24, 36)])
    # ---- the vault (29 - 36, 40 - 44)
    z.block('!', 29, 40); z.block('!', 34, 40)
    z.block('?', 29, 42, turned=True); z.block('?', 36, 42, turned=True)
    # ---- the shaft foot hall (24 - 41, 47 - 60) and the vault corridors
    z.puts('c', [(24, 48), (25, 48), (24, 49), (40, 57), (41, 57), (41, 56)])
    z.puts('o', [(26, 59), (27, 59), (38, 48)])
    z.puts('v', [(36, 59), (37, 59)])
    z.block('Y', 39, 51)
    z.puts(';', [(29, 53), (36, 52), (25, 43), (40, 42)])
    z.block('/', 34, 49)
    # ---- the west caves (1 - 23, 48 - 60)
    z.puts('o', [(3, 49), (4, 49), (9, 53), (10, 53)])
    z.puts('c', [(12, 59), (13, 59), (22, 49), (22, 50)])
    z.puts('v', [(21, 55), (21, 56)])
    z.puts(';', [(4, 54), (11, 57), (20, 53), (16, 49)])
    z.block('Y', 9, 56)
    # ---- the generator hall (44 - 64, 24 - 60): gensets, boiler, day tanks, pumps, pipes, switchboard; catwalks
    z.block('(', 46, 26); z.block('(', 46, 35)
    z.block(')', 55, 27)
    z.block('}', 55, 36); z.block('}', 55, 41)
    z.block('&', 52, 33); z.block('&', 52, 44)
    z.block('|', 64, 36, turned=True)
    for c in range(45, 51):
        z.put('{', c, 44)
    z.puts('o', [(44, 58), (45, 58), (60, 58), (61, 58)])
    z.puts('c', [(64, 52), (64, 53)])
    D = '4.5'
    z.fill(D, 45, 48, 20, 4, 'w')               # the bridge across the hall
    z.fill(D, 61, 33, 4, 15, 'w')               # the east gallery
    z.stair('N', 62, 25)
    z.stair('X', 46, 52)
    # ---- the cavern (1 - 64, 1 - 21): the relic, its scaffold, ice pillars, the abandoned dig
    z.block('$', 6, 1)
    z.fill(D, 3, 8, 24, 4, 'w')                 # the scaffold catwalk in front of the relic
    z.stair('X', 3, 12); z.stair('X', 24, 12)
    z.stair('<', 21, 4)
    z.fill('7', 20, 1, 7, 3, 'w')               # the high platform beside the relic
    for (c, r) in ((34, 7), (48, 12), (57, 4), (40, 16)):
        z.block('/', c, r)
    z.puts(';', [(30, 14), (38, 17), (44, 6), (54, 16), (60, 10), (18, 13), (8, 19), (32, 3)])
    z.puts('o', [(36, 19), (37, 19), (36, 20), (59, 19), (60, 19)])
    z.puts('c', [(29, 9), (30, 9), (29, 10), (52, 9), (53, 9)])
    z.puts('v', [(44, 15), (45, 15), (45, 16)])
    z.block('Y', 39, 9)
    z.rails(D)
    z.rails('7')
    # ---- spawns, pickups
    z.puts('S', [(10, 14), (34, 13), (50, 5), (58, 15), (16, 25), (9, 41), (31, 27), (52, 30), (59, 46), (6, 51), (18, 57), (50, 57)])
    z.puts('a', [(20, 51), (60, 53), (14, 8)])
    z.puts('h', [(40, 25), (5, 59), (24, 4)])
    # ---- floors, ceilings
    z.finish(1, 24, 21, 22, '4')
    z.finish(24, 24, 18, 14, '4')
    z.finish(29, 40, 8, 5, '5')
    z.finish(44, 24, 21, 37, '5')
    for (c, r, w, h, ch) in ((29, 24, 5, 3, '0'), (1, 44, 21, 2, '8'), (24, 35, 6, 3, '8')):
        z.finish(c, r, w, h, ch, over='45')
    z.ceiling('4.4', 1, 24, 21, 22, 2)
    z.ceiling('4.4', 24, 24, 18, 14, 3)
    z.ceiling('4.4', 29, 40, 8, 5, 4)
    T = z.L('12')
    for (c, r, ch) in ((30, 5, '^'), (44, 9, '^'), (55, 2, '^'), (16, 15, '^'), (7, 52, '^'), (26, 53, '^'), (58, 33, '^'), (36, 16, '^')):
        z.fill('12', c, r, 3, 3, ch)
    for (c, r) in ((40, 13), (24, 18), (47, 18), (58, 9), (12, 49), (35, 55), (54, 55), (20, 56), (3, 51), (50, 39)):
        T[r][c] = '*'
    for (c, r) in ((36, 10), (52, 14), (9, 50), (30, 52), (38, 58), (52, 38), (60, 40), (17, 55)):
        T[r][c] = ':'
    return z


def main():
    ok = True
    zones = [zone1(), zone2()]
    for z in zones:
        errs, stats = validate(z)
        print('%-12s %s' % (z.name, stats))
        for e in errs:
            print('   ERROR', e)
            ok = False
        if '--check' not in sys.argv:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
