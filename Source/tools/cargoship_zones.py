"""Halcyon Vega zone maps (src/data/zones/cargoship_{1,2,3}.txt), theme src/data/themes/cargoship.js.

Zone 1, the main deck (51 x 64, open sky): the bulwarks are the west / east walls, the forecastle bulkhead the south
wall, the front of the superstructure the north wall (the exit is a watertight door into it). Side walkways run the
full length; three hatches carry their hatch covers 1.8 m up ("@layer 1.8") with container stacks on them; steel
stairs climb onto the covers from the cross-deck lanes, where lashing bridges and two deck cranes stand; mooring
winches and bitts on the fore apron, lifeboat davits by the superstructure. Markings on "@layer 0.01" (walkway lines,
hazard hatching, rust, oil) and "@layer 1.81" (hatch seams, twistlock sockets, hatch numbers).
Zone 2, a cargo hold (51 x 56, 13 m deckhead): three bays of container cells with cell guides (empty, 1 - 4 tiers,
a yacht on a flat rack), gantry walkways at 5.2 m ("@layer 5.2") round the hold and across it at two web frames,
stair towers up from the floor, project cargo by the entry; the deckhead ("@layer 13") has the hatch-cover girders,
daylight slots between the panels and floodlights.
Zone 3, the engine room (51 x 56, 13 m deckhead): the main engine in the middle with platforms along it at 5.2 m,
the upper flats along both sides ("@layer 5.2", the control room on the east flat), bridges across in front of and
behind the engine, the shaft line aft to the stern tube, generator sets, pumps, purifiers, tanks, the boiler, the
switchboard and the workshop; overhead crane rails, pipe racks, ducts, lamps and chain hoists ("@layer 13").
The script validates gates, one P, 10 - 14 spawns >= 14 m from P with open ground round them, 2 - 3 ammo and health,
prefab tiling, stairs that arrive on walkable deck, the weapon-stand cells, and that every walkable cell of every
layer is reachable from P through the stairs.
Run: python3 tools/cargoship_zones.py [--print]
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))
SIZES = {'1': (5, 12), '2': (5, 12), '3': (5, 12), '4': (5, 12), '5': (5, 6), '6': (5, 6), 'T': (3, 6), 'F': (3, 12),
         'L': (6, 2), 'K': (4, 4), 'W': (4, 3), 'b': (2, 1), 'V': (2, 2), 'c': (3, 2), 'B': (3, 8), 'R': (3, 8),
         'Z': (3, 4), 'U': (3, 4), 'X': (3, 10), 'N': (3, 10),
         'e': (3, 13), 'i': (3, 13), 'j': (3, 13), 'k': (3, 13), 'l': (3, 13), 'f': (3, 13), 'Y': (4, 6), 'd': (2, 2), 'I': (3, 6),
         'M': (11, 24), 'g': (4, 9), 'u': (2, 2), 'q': (2, 1), 'A': (2, 1), 'O': (3, 3), 'J': (8, 6), 'H': (4, 1), 'Q': (6, 1),
         'C': (2, 1), 'z': (4, 3), 'y': (3, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)}
STAIR_RISE = {'Z': (0, -1), 'U': (0, 1), 'X': (0, -1), 'N': (0, 1)}    # rising north / south
STAIR_TOP = {'Z': '1.8', 'U': '1.8', 'X': '5.2', 'N': '5.2'}
DECKS = {'1.8': 't', '5.2': 'w'}
WALK_FLOOR = set('.SahPEGLe')      # floor cells you stand on (lashing bridges and empty container cells: you walk through)
SOLID = ('1.8',)                  # hatch covers are solid to the deck
WALK_DECK = set('twSah')


def hsh(a, b, k=0):
    h = (a * 374761393 + b * 668265263 + k * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296.0


class Zone:
    def __init__(self, name, W, H, gate=24, entry=24, P0=None):
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
        self.links = []        # (layerA, c, r, layerB, c, r): stair foot <-> top
        self.openings = set()  # (layer, c, r) deck cells where a stair arrives (no rail)

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
                assert 0 < c < self.W - 1 and 0 < r < self.H - 1, (self.name, y, c, r, ch)
                assert g[r][c] in over, '%s @%s: %r at (%d,%d) hits %r' % (self.name, y, ch, c, r, g[r][c])
                g[r][c] = ch

    def put(self, y, c, r, ch, over=None):
        self.fill(y, c, r, 1, 1, ch, over or ('.' if y == '0' else '.tw'))

    def puts(self, y, pts, ch, over=None):
        for c, r in pts:
            self.put(y, c, r, ch, over)

    def block(self, y, ch, c, r, turned=False, over=None):
        w, h = SIZES[ch]
        if turned:
            w, h = h, w
        self.fill(y, c, r, w, h, ch, over or ('.' if y == '0' else '.tw'))
        return (c, r, w, h)

    def stair(self, ch, c, r):
        """a stair block on the floor plan; links the cell beyond its foot with the deck cell beyond its top"""
        w, h = SIZES[ch]
        self.block('0', ch, c, r)
        top = STAIR_TOP[ch]
        for x in range(c, c + w):
            if ch in 'ZX':   # rising north: top beyond row r - 1, foot at r + h
                if c < x < c + w - 1:
                    self.links.append(('0', x, r + h, top, x, r - 1))
                self.openings.add((top, x, r - 1))
            else:
                if c < x < c + w - 1:
                    self.links.append(('0', x, r - 1, top, x, r + h))
                self.openings.add((top, x, r + h))

    def text(self):
        out = [''.join(row) for row in self.g['0']]
        for y in sorted((k for k in self.g if k != '0'), key=float):
            out.append('@layer ' + y)
            out += [''.join(row) for row in self.g[y]]
        return '\n'.join(out) + '\n'

    # ---- helpers
    def deck_cell(self, y, c, r):
        return y in DECKS and self.at(y, c, r) in WALK_DECK and self.at(y, c, r) != '.'

    def rails(self, y, skip=lambda c, r, dc, dr: False):
        """rail every deck cell of layer y that borders open space (not where a stair arrives)"""
        g = self.g[y]
        todo = []
        for r in range(1, self.H - 1):
            for c in range(1, self.W - 1):
                if g[r][c] != DECKS[y] or (y, c, r) in self.openings:
                    continue
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.at(y, c + dc, r + dr)
                    if n == '.' and self.at('0', c + dc, r + dr) != '#' and not skip(c, r, dc, dr):
                        todo.append((c, r))
                        break
        for c, r in todo:
            g[r][c] = 'r'


# ================================================================ validation
def validate(z, size_min=(44, 44)):
    errs = []
    W, H = z.W, z.H
    f = z.g['0']
    if W < size_min[0] or H < size_min[1] or W * H < 2000:
        errs.append('size')
    # prefab tiling
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
    # walkable nodes per layer
    def walk(y, c, r):
        if y == '0':
            return z.at('0', c, r) in WALK_FLOOR and all(z.at(L, c, r) == '.' for L in SOLID if L in z.g)
        return z.at(y, c, r) in WALK_DECK
    layers = [y for y in z.g if y in DECKS or y == '0']
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
    sealed = [(y, c, r) for y in layers for r in range(H) for c in range(W) if walk(y, c, r) and z.at(y, c, r) not in 'EG' and (y, c, r) not in seen]
    if sealed:
        errs.append('%d sealed cells, e.g. %s' % (len(sealed), sealed[:6]))
    for a in z.links:
        if not walk(a[0], a[1], a[2]):
            errs.append('stair foot %s not walkable (%r)' % (str(a[:3]), z.at(*a[:3])))
        if not walk(a[3], a[4], a[5]):
            errs.append('stair top %s not walkable (%r)' % (str(a[3:]), z.at(*a[3:])))
    G = [c for c in range(W) if f[0][c] == 'G']
    for c in G:
        for k in (1, 2):
            if f[k][c] not in '.':
                errs.append('exit approach (%d,%d) %r' % (c, k, f[k][c]))
    if not any(('0', c, 1) in seen for c in G):
        errs.append('no path to the exit')
    E = [c for c in range(W) if f[H - 1][c] == 'E']
    for c in E:
        for k in (2, 3):
            if f[H - k][c] not in '.P':
                errs.append('entry approach (%d,%d) %r' % (c, H - k, f[H - k][c]))
    S, na, nh = [], 0, 0
    for y in layers:
        for r in range(H):
            for c in range(W):
                ch = z.at(y, c, r)
                if ch == 'S':
                    S.append((y, c, r))
                    if (c - P0[0]) ** 2 + (r - P0[1]) ** 2 < 14 ** 2:
                        errs.append('spawn %s < 14 m from P' % str((y, c, r)))
                    for dc in (-1, 0, 1):
                        for dr in (-1, 0, 1):
                            if (dc or dr) and not walk(y, c + dc, r + dr) and z.at(y, c + dc, r + dr) != 'r':
                                errs.append('spawn %s neighbour %r' % (str((y, c, r)), z.at(y, c + dc, r + dr)))
                na += ch == 'a'
                nh += ch == 'h'
    if not 10 <= len(S) <= 14:
        errs.append('%d spawns' % len(S))
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for dc in (-2, -1, 1, 2):
        if z.at('0', P0[0] + dc, P0[1] - 4) != '.':
            errs.append('weapon stand cell (%d,%d) %r' % (P0[0] + dc, P0[1] - 4, z.at('0', P0[0] + dc, P0[1] - 4)))
    stats = {'size': '%dx%d' % (W, H), 'walk': len(seen), 'spawns': len(S)}
    return errs, stats


# ================================================================ zone 1: the main deck
HATCHES = [(6, 18), (24, 36), (42, 54)]   # first / last row of each hatch cover (cols 4..46)


def deck_zone():
    z = Zone('cargoship_1', 51, 64, gate=24, entry=None, P0=(25, 60))
    T = '1.8'
    for r0, r1 in HATCHES:
        z.fill(T, 4, r0, 43, r1 - r0 + 1, 't')
    # ---- stairs onto the hatch covers
    z.stair('U', 14, 2)     # aft apron -> hatch 1
    z.stair('U', 34, 2)
    z.stair('Z', 34, 19)    # lane 1 -> hatch 1
    z.stair('U', 14, 20)    # lane 1 -> hatch 2
    z.stair('Z', 14, 37)    # lane 2 -> hatch 2
    z.stair('U', 34, 38)    # lane 2 -> hatch 3
    z.stair('Z', 4, 55)     # fore apron -> hatch 3
    z.stair('Z', 44, 55)
    # ---- hatch 1 (aft): heavily loaded, a 5 m centre lane lined up with the superstructure door
    for c, ch in ((4, '4'), (9, '4'), (18, '3'), (28, '3'), (37, '4'), (42, '2')):
        z.block(T, ch, c, 6, over='t')
    # ---- hatch 2: partly loaded, an open fighting deck
    for c, ch in ((4, '3'), (9, '2'), (41, '2')):
        z.block(T, ch, c, 25, over='t')
    z.block(T, '5', 20, 27, over='t')
    z.block(T, '6', 27, 29, over='t')
    z.block(T, 'T', 17, 30, over='t')
    z.block(T, 'F', 37, 25, over='t')
    # ---- hatch 3 (forward): stacks on both sides, low reefers, the centre lane open toward the superstructure
    for c, ch in ((7, '2'), (12, '3'), (17, '1'), (28, '1')):
        z.block(T, ch, c, 42, over='t')
    z.block(T, '3', 33, 43, over='t')
    z.block(T, '5', 38, 43, over='t')
    z.block(T, '6', 38, 49, over='t')
    # ---- cross-deck lanes: lashing bridges (you walk under them), the deck cranes (jibs up over the next hatch)
    for c in (4, 20, 26, 37):
        z.block('0', 'L', c, 20)
    for c in (8, 17, 23):
        z.block('0', 'L', c, 38)
    z.block('0', 'K', 4, 37)          # lane 2 west, its jib over hatch 3
    z.block('0', 'K', 43, 19)         # lane 1 east, its jib over hatch 2
    z.block('0', 'c', 10, 22)         # lashing-gear cages
    z.block('0', 'c', 42, 38)
    z.block('0', 'V', 47, 21)         # hold ventilators on the walkways at the lanes
    z.block('0', 'V', 2, 39)
    # ---- aft apron: davits, fire gear, manholes
    z.block('0', 'B', 1, 1)
    z.block('0', 'R', 47, 1)
    z.put('0', 20, 3, 'm')
    z.put('0', 30, 3, 'm')
    z.puts('0', [(8, 3), (42, 3)], 'x')
    z.puts('0', [(6, 2), (6, 3), (44, 2)], 'D')
    # ---- fore apron: mooring winches, bitts, rope coils, foam monitors
    z.block('0', 'W', 9, 57)
    z.block('0', 'W', 38, 57)
    z.block('0', 'b', 2, 61)
    z.block('0', 'b', 47, 61)
    z.block('0', 'b', 18, 61)
    z.block('0', 'b', 31, 61)
    z.puts('0', [(14, 58), (15, 58), (35, 58)], 'o')
    z.puts('0', [(21, 56), (29, 56)], 'm')
    z.puts('0', [(2, 57), (48, 57)], 'D')
    # ---- side walkways: mushroom vents, drums
    for r in (12, 30, 47):
        z.put('0', 3, r, 'v')
        z.put('0', 47, r + 3, 'v')
    # ---- spawns, pickups
    z.puts('0', [(25, 3), (18, 22), (38, 22), (25, 40), (2, 15), (48, 44)], 'S')
    z.puts(T, [(25, 9), (15, 30), (33, 31), (25, 45), (44, 46), (5, 47)], 'S', over='t')
    z.puts('0', [(2, 34), (48, 9)], 'a')
    z.puts(T, [(25, 15)], 'a', over='t')
    z.puts('0', [(48, 30)], 'h')
    z.puts(T, [(5, 53), (40, 34)], 'h', over='t')
    # ---- markings: walkway lines, hatching at the stair feet and crane bases, rust and oil; hatch seams, sockets
    M = '0.01'
    z.L(M)
    for c in (2, 48):
        for r in range(10, 53):
            if z.at('0', c, r) == '.':
                z.put(M, c, r, ':')
    for (c, r) in ((14, 1), (16, 1), (34, 1), (36, 1), (35, 23), (15, 19), (15, 41), (35, 37), (5, 59), (45, 59)):
        if z.at('0', c, r) == '.':
            z.put(M, c, r, '%')
    for k in range(40):
        c, r = 1 + int(hsh(k, 3) * 49), 1 + int(hsh(k, 7) * 62)
        if z.at('0', c, r) == '.' and z.at(M, c, r) == '.' and z.at(T, c, r) == '.':
            z.put(M, c, r, '!' if k % 3 else '&')
    HM = '1.81'
    z.L(HM)
    for (c, r), ch in (((24, 11), '9'), ((24, 33), '8'), ((24, 50), '7')):
        z.put(HM, c, r, ch)
    for r0, r1 in HATCHES:
        for r in (r0 + 4, r1 - 4):
            for c in range(4, 47):
                if z.at(T, c, r) in 'tSah' and z.at(HM, c, r) == '.':
                    z.put(HM, c, r, ';')
        for k in range(14):
            c, r = 5 + int(hsh(k, r0) * 41), r0 + 1 + int(hsh(k, r0 + 5) * (r1 - r0 - 1))
            if z.at(T, c, r) == 't' and z.at(HM, c, r) == '.':
                z.put(HM, c, r, '`')
    return z


# ================================================================ zone 2: the cargo hold
BAYS = [(4, 16), (20, 32), (36, 48)]
COLS = [3 + 3 * k for k in range(15)]   # first column of each container cell


def hold_zone():
    z = Zone('cargoship_2', 51, 56, gate=24, entry=24, P0=(25, 53))
    WL = '5.2'
    D = z.L(WL)
    # walkways: north, south, both sides, two gantries across at the web frames
    z.fill(WL, 1, 1, 49, 3, 'w')
    z.fill(WL, 1, 51, 49, 4, 'w')
    for c in (1, 48):
        z.fill(WL, c, 4, 2, 47, 'w')
    for r in (17, 33):
        z.fill(WL, 3, r, 45, 3, 'w')
    # stair towers in empty cell columns
    z.stair('X', 6, 4)        # bay A west: up to the north walkway
    z.stair('X', 42, 4)       # bay A east
    z.stair('N', 33, 41)      # bay C, east of centre: up to the south walkway
    plan = {
        0: ['l', None, 'l', 'k', 'k', 'j', 'e', 'e', 'e', 'j', 'k', 'l', 'l', None, 'k'],
        1: ['j', 'i', 'e', 'f', 'e', 'i', None, None, None, 'i', 'e', 'e', 'i', 'j', 'k'],
        2: ['l', 'k', 'k', 'j', 'e', 'e', 'i', 'e', 'e', 'e', None, 'k', 'l', 'l', 'k'],
    }
    for bi, (r0, r1) in enumerate(BAYS):
        for k, c in enumerate(COLS):
            ch = plan[bi][k]
            if ch is None:
                continue
            z.block('0', ch, c, r0)
    # bay C centre column above the stair: open floor with its cell guides gone (the stair tower stands there)
    # entry area: project cargo
    z.block('0', 'Y', 4, 49)
    z.block('0', 'd', 11, 49)
    z.block('0', 'I', 36, 50, turned=True)
    z.block('0', 'd', 45, 49)
    # deckhead: hatch-cover girders over the bay ends, daylight slots between the hatch panels, floodlights
    C = '13'
    z.L(C)
    for r in (3, 18, 34, 49):
        for c in range(1, 50):
            z.put(C, c, r, '=')
    for r in (10, 26, 42):
        for c in range(1, 50):
            z.put(C, c, r, '_')
    for r in range(1, 55):
        if z.at(C, 25, r) == '.':
            z.put(C, 25, r, '_')
    for c in (9, 18, 32, 41):
        for r in (7, 14, 22, 30, 38, 45):
            z.put(C, c, r, 'n')
    # walkway rails, grating, floor markings
    z.rails(WL)
    G = '5.21'
    z.L(G)
    for r in range(z.H):
        for c in range(z.W):
            if z.at(WL, c, r) == 'w':
                z.put(G, c, r, '|')
    M = '0.01'
    z.L(M)
    for (c, r) in ((2, 8), (48, 8), (2, 44), (48, 44)):
        z.put(M, c, r, '@')
    for k in range(30):
        c, r = 1 + int(hsh(k, 11) * 49), 1 + int(hsh(k, 13) * 54)
        if z.at('0', c, r) == '.' and z.at(M, c, r) == '.':
            z.put(M, c, r, '!' if k % 2 else '&')
    # spawns and pickups (floor, walkways, gantries)
    z.puts('0', [(25, 25), (13, 34), (37, 34), (2, 18)], 'S')
    z.puts(WL, [(25, 2), (10, 18), (40, 18), (10, 53), (40, 53), (12, 34), (38, 34), (25, 18)], 'S', over='w')
    z.puts('0', [(22, 26), (49, 52)], 'a')
    z.puts(WL, [(25, 34)], 'a', over='w')
    z.puts('0', [(28, 26)], 'h')
    z.puts(WL, [(49, 40), (1, 22)], 'h', over='w')
    return z


# ================================================================ zone 3: the engine room
def engine_zone():
    z = Zone('cargoship_3', 51, 56, gate=40, entry=24, P0=(25, 52))
    UP = '5.2'
    z.L(UP)
    # main engine, its platforms at 5.2 m, the shaft line aft to the stern tube
    z.block('0', 'M', 20, 14)
    z.fill(UP, 20, 14, 3, 24, 'w')
    z.fill(UP, 28, 14, 3, 24, 'w')
    z.block('0', 'y', 24, 1, over='.')
    for r in range(2, 14):
        z.block('0', 'y', 24, r)
    # upper flats along both sides, bridges across behind and in front of the engine
    z.fill(UP, 1, 1, 12, 54, 'w')
    z.fill(UP, 38, 1, 12, 54, 'w')
    z.fill(UP, 13, 10, 25, 3, 'w', over='.w')
    z.fill(UP, 13, 37, 25, 3, 'w', over='.w')
    # stairs: two up to the bridge in front of the engine, one up to the bridge behind it
    z.stair('X', 13, 40)
    z.stair('X', 35, 40)
    z.stair('X', 13, 13)
    # floor: generator sets along the west side (under the flat), switchboard, workshop, pumps
    for r in (2, 12, 22):
        z.block('0', 'g', 3, r)
    z.block('0', 'Q', 1, 33, turned=True)
    z.block('0', 'H', 1, 46, turned=True)
    for r in (33, 35, 37):
        z.block('0', 'q', 8, r)
    z.block('0', 'C', 8, 40)
    # east floor: tanks, air bottles, the boiler in the void, manifolds, pumps
    z.block('0', 'z', 44, 4)
    z.block('0', 'z', 44, 9)
    z.block('0', 'A', 40, 16)
    z.block('0', 'A', 40, 18)
    z.block('0', 'O', 33, 3)
    z.block('0', 'C', 33, 20)
    z.block('0', 'q', 33, 27)
    z.block('0', 'q', 33, 30)
    z.block('0', 'q', 46, 30)
    z.block('0', 'q', 46, 33)
    z.block('0', 'C', 44, 44)
    z.block('0', 'u', 16, 30)
    z.puts('0', [(17, 3), (18, 3), (46, 50), (4, 51)], 'D')
    # upper flats: purifier room (west), control room over the void (east), settling tanks
    for c in (3, 6, 9):
        z.block(UP, 'u', c, 5, over='w')
    z.block(UP, 'z', 2, 20, over='w')
    z.block(UP, 'z', 2, 26, over='w')
    z.block(UP, 'J', 38, 20, turned=True, over='w')
    z.block(UP, 'H', 46, 46, over='w')
    z.block(UP, 'C', 44, 6, over='w')
    # deckhead: crane rails over the engine, a crane bridge, pipe racks, ducts, lamps; chain hoists swing on overlays
    C = '13'
    z.L(C)
    for r in range(12, 40):
        z.put(C, 21, r, '+')
        z.put(C, 29, r, '+')
    for c in range(22, 29):
        z.put(C, c, 33, '*')
    for c in range(1, 50):
        if z.at(C, c, 8) == '.':
            z.put(C, c, 8, '~')
    for r in range(9, 55):
        z.put(C, 11, r, '~')
        z.put(C, 40, r, '~')
    for r in range(1, 55):
        if z.at(C, 6, r) == '.':
            z.put(C, 6, r, '-')
    for c in (16, 34):
        for r in (16, 24, 32, 44, 50):
            z.put(C, c, r, 'n')
    for c in (3, 46):
        for r in (14, 30, 44):
            z.put(C, c, r, 'n')
    z.puts(C, [(16, 28), (34, 36)], '^')
    z.puts(C, [(16, 27), (16, 29), (34, 35), (34, 37)], '+')
    # rails on the flats (not along the engine body, not where stairs arrive)
    z.rails(UP, skip=lambda c, r, dc, dr: dc != 0 and z.at('0', c + dc, r) == 'M')
    G = '5.21'
    z.L(G)
    for r in range(z.H):
        for c in range(z.W):
            if z.at(UP, c, r) == 'w':
                z.put(G, c, r, '|')
    M = '0.01'
    z.L(M)
    for k in range(26):
        c, r = 1 + int(hsh(k, 21) * 49), 1 + int(hsh(k, 23) * 54)
        if z.at('0', c, r) == '.' and z.at(M, c, r) == '.':
            z.put(M, c, r, '&')
    for c in range(19, 32):
        if z.at('0', c, 38) == '.' and z.at(M, c, 38) == '.':
            z.put(M, c, 38, '%')
    # spawns and pickups
    z.puts('0', [(17, 20), (35, 14), (45, 22), (45, 40), (8, 46)], 'S')
    z.puts(UP, [(6, 14), (6, 40), (44, 30), (44, 16), (25, 11), (29, 25), (21, 30)], 'S', over='w')
    z.puts('0', [(17, 34), (45, 26)], 'a')
    z.puts(UP, [(8, 30)], 'a', over='w')
    z.puts('0', [(31, 46)], 'h')
    z.puts(UP, [(43, 50), (25, 38)], 'h', over='w')
    return z


def main():
    ok = True
    for z in (deck_zone(), hold_zone(), engine_zone()):
        errs, stats = validate(z)
        print('%-14s %s' % (z.name, stats))
        for e in errs:
            print('   ERROR', e)
            ok = False
        with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
            f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
