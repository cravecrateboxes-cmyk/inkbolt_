"""Deep Park zone maps (src/data/zones/parking_{1,2,3}.txt), theme src/data/themes/parking.js.

Each zone is a 51 x 56 split-level car park under a 7 m ceiling: the floor plan (the deeper level) and a deck
("@layer 3.6") over part of it, joined by 16 m ramps and stair flights; zone 2 adds a solid platform at 1.8 m between
them, zone 3 a loading dock at 1.2 m. The layout below (decks, ramps, stairs, parking rows, vehicles, props, spawns)
is hand-placed; the script derives the rest:
  * deck-edge rails ('r') on every deck / platform cell that borders open space, except where a ramp or stair arrives
  * columns: 'I' under the deck with 'i' over it on a 6 m grid along the aisles and the deck edge, 'C' in the voids
  * "@layer 0.01" / "@layer 3.61" / "@layer 1.81" markings: bays under every parking row (cars park in some),
    lane arrows and dashed lines in the aisles, hatching at ramp feet, crossings, oil, puddles, drains, speed bumps
  * "@layer 3.2" (under the deck) and "@layer 7" (ceiling) fittings: beams on the column lines, strip lights (a few
    flickering), ducts, sprinkler pipes, exit signs, CCTV, level signs (the floor's level under the deck, the deck's
    level over it; the theme's wall chooser reads the floor level from them)
and validates it: gates, one P, 10-14 spawns >= 14 m from P with open ground round them (on any level), 2-3 ammo and
health, every walkable cell of every level reachable from P through the ramps and stairs.
Run: python3 tools/parking_zones.py [--print]
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'src', 'data', 'zones'))
W, H = 51, 56
GX = 24                       # gate cells 24..26
P0 = (25, 52)
DECK, UNDER, CEIL = '3.6', '3.2', '7'
SIZES = {'V': (3, 5), 'H': (3, 5), 'W': (3, 5), 'T': (3, 6), 'X': (3, 8), 'Y': (4, 10), 'm': (1, 2), 'k': (2, 4), 'g': (2, 3),
         'A': (6, 9), 'N': (5, 16), 'U': (5, 16), 'R': (5, 8), 'Z': (3, 8), 'z': (8, 3), 'q': (8, 3), 'O': (3, 6), 'Q': (2, 3),
         'B': (1, 4), 'J': (2, 1), 'K': (3, 2), 'L': (2, 2), 'w': (2, 1), 'F': (2, 3)}
SOLID_DECKS = {'1.8': 't', '1.2': 'd'}   # platform / dock layers (solid down to the floor)
WALK = set('.SahPEGuetd')               # cells you can stand on (on their own layer)


class Zone:
    def __init__(self, name, floor_level):
        self.name, self.lv = name, floor_level
        self.g = {'0': grid('.')}
        for r in range(H):
            for c in range(W):
                if r in (0, H - 1) or c in (0, W - 1):
                    self.g['0'][r][c] = '#'
        for c in range(GX, GX + 3):
            self.g['0'][0][c] = 'G'
            self.g['0'][H - 1][c] = 'E'
        self.g['0'][P0[1]][P0[0]] = 'P'
        self.links = []        # (layerA, c, r, layerB, c, r): ramp / stair ends
        self.openings = set()  # (layer, c, r) deck cells where a ramp / stair arrives (no rail)

    def L(self, y):
        if y not in self.g:
            self.g[y] = grid('.')
        return self.g[y]

    def fill(self, y, c0, r0, w, h, ch, over='.'):
        g = self.L(y)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert 0 < c < W - 1 and 0 < r < H - 1, (self.name, y, c, r, ch)
                assert g[r][c] in over, '%s @%s: %r at (%d,%d) hits %r' % (self.name, y, ch, c, r, g[r][c])
                g[r][c] = ch

    def put(self, y, c, r, ch, over=None):
        self.fill(y, c, r, 1, 1, ch, over or ('.' if y == '0' else '.utd'))

    def block(self, y, ch, c, r, turned=False, over=None):
        w, h = SIZES[ch]
        if turned:
            w, h = h, w
        self.fill(y, c, r, w, h, ch, over or ('.' if y == '0' else '.utd'))
        return (c, r, w, h)

    # ---- circulation: a ramp / stair block on layer y going from `low` (layer, side) up to the layer `high`
    def ramp(self, y, ch, c, r, high):
        """N / R / Z / O / Q rise north, U south, z west, q east; links the cells beyond both ends"""
        w, h = SIZES[ch]
        self.block(y, ch, c, r, over='.' if y == '0' else '.' + SOLID_DECKS.get(y, 'u'))
        lane = range(c + 1, c + w - 1) if w >= 3 else range(c, c + w)
        rows = range(r + 1, r + h - 1) if h >= 3 else range(r, r + h)
        full_x, full_z = range(c, c + w), range(r, r + h)
        if ch in 'NRZOQ':
            for x in lane:
                self.links.append((y, x, r + h, high, x, r - 1))
            self.openings.update((high, x, r - 1) for x in full_x)
        elif ch == 'U':
            for x in lane:
                self.links.append((y, x, r - 1, high, x, r + h))
            self.openings.update((high, x, r + h) for x in full_x)
        elif ch == 'z':
            for zz in rows:
                self.links.append((y, c + w, zz, high, c - 1, zz))
            self.openings.update((high, c - 1, zz) for zz in full_z)
        elif ch == 'q':
            for zz in rows:
                self.links.append((y, c - 1, zz, high, c + w, zz))
            self.openings.update((high, c + w, zz) for zz in full_z)

    def text(self):
        out = [''.join(row) for row in self.g['0']]
        for y in sorted((k for k in self.g if k != '0'), key=float):
            out.append('@layer ' + y)
            out += [''.join(row) for row in self.g[y]]
        return '\n'.join(out) + '\n'


def hsh(a, b, k=0):
    """deterministic 0..1 hash of a cell"""
    h = (a * 374761393 + b * 668265263 + k * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296.0


def grid(fill):
    return [[fill] * W for _ in range(H)]


def is_deck(z, y, c, r):
    """a standable deck / platform / dock cell on layer y"""
    if y == '0' or y not in z.g:
        return False
    ch = z.g[y][r][c]
    return ch not in '.#'


# ================================================================ derived dressing
def rails(z, y, deck_ch):
    """rails on deck cells that border open space (not wall, not deck), except where ramps / stairs arrive"""
    g = z.g[y]
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if g[r][c] != deck_ch or (y, c, r) in z.openings:
                continue
            edge = False
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = g[r + dr][c + dc]
                if n == '.' and z.g['0'][r + dr][c + dc] != '#':
                    edge = True
            if edge:
                g[r][c] = 'r'


def columns(z, pts):
    """I under the deck + i over it (or on its rail line); C where no deck is above"""
    for (c, r) in pts:
        if z.g['0'][r][c] != '.':
            continue
        d = z.g.get(DECK)
        if d and d[r][c] in 'ur':
            z.g['0'][r][c] = 'I'
            d[r][c] = 'i'
        elif not any(z.g[y][r][c] in SOLID_DECKS.values() or z.g[y][r][c] == 'r' for y in SOLID_DECKS if y in z.g):
            z.g['0'][r][c] = 'C'


def bays(z, y, sym, c0, r0, n, along='x'):
    """n parking bays (3 x 5) in a row on marking layer y: along x (bays 3 wide side by side) or along z"""
    out = []
    for i in range(n):
        if along == 'x':
            z.fill(y, c0 + 3 * i, r0, 3, 5, sym)
            out.append((c0 + 3 * i, r0, False))
        else:
            z.fill(y, c0, r0 + 3 * i, 5, 3, sym)
            out.append((c0, r0 + 3 * i, True))
    return out


def park(z, y, row, pattern):
    """park vehicles in a row of bays: pattern chars per bay (V H W or '.')"""
    for (c, r, turned), ch in zip(row, pattern):
        if ch != '.':
            z.block(y, 'V' if (ch == 'H' and turned) else ch, c, r, turned)   # hazard cars park nose north / south only


def fittings(z, y, cells, level_sign, lit_rows, beam_rows, lamp_cols, duct_cols=(), pipe_rows=(), extra=()):
    """hang fittings on layer y over `cells` (a set of (c, r)): beams along beam_rows (crossings over columns),
    strip lights on lit_rows every 4 m (one in seven flickering), ducts N-S on duct_cols, pipes E-W on pipe_rows"""
    g = z.L(y)
    cols = set()
    for r in range(H):
        for c in range(W):
            if z.g['0'][r][c] in 'IC' or (DECK in z.g and z.g[DECK][r][c] == 'i'):
                cols.add((c, r))
    for (c, r) in sorted(cells):
        if g[r][c] != '.':
            continue
        if r in beam_rows:
            g[r][c] = '+' if (c, r) in cols else '='
        elif c in duct_cols:
            g[r][c] = '-'
        elif r in pipe_rows:
            g[r][c] = '~'
        elif r in lit_rows and c % 4 == 2:
            g[r][c] = 'f' if hsh(c, r, 5) < 0.12 else 'l'
    for (c, r, ch) in extra:
        if (c, r) in cells:
            g[r][c] = ch
            if ch in '1234x':   # hanging signs are wider than a cell: no strip light right beside them
                for dc in (-2, -1, 1, 2):
                    if 0 < c + dc < W - 1 and g[r][c + dc] in 'lf':
                        g[r][c + dc] = '.'


def scatter(z, y, cells, pts):
    for (c, r, ch) in pts:
        if (c, r) in cells and z.L(y)[r][c] == '.':
            z.L(y)[r][c] = ch


# ================================================================ validation
def validate(z):
    errs = []
    base = z.g['0']
    solid = {}
    for y, ch in SOLID_DECKS.items():
        if y in z.g:
            for r in range(H):
                for c in range(W):
                    if z.g[y][r][c] != '.':
                        solid[(c, r)] = y
    nodes = set()
    for r in range(H):
        for c in range(W):
            if base[r][c] in '.SahPEG' and (c, r) not in solid:
                nodes.add(('0', c, r))
            for y in z.g:
                if y in (DECK,) + tuple(SOLID_DECKS) and y != '0' and z.g[y][r][c] in 'uetdSah' and z.g[y][r][c] != '.':
                    nodes.add((y, c, r))
    adj = {}
    for (y, c, r) in nodes:
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (y, c + dc, r + dr)
            if n in nodes:
                adj.setdefault((y, c, r), []).append(n)
    for (ya, ca, ra, yb, cb, rb) in z.links:
        a, b = (ya, ca, ra), (yb, cb, rb)
        if a not in nodes or b not in nodes:
            errs.append('link end not walkable %s -> %s' % (a, b))
            continue
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    start = ('0',) + P0
    seen = {start}
    q = deque([start])
    while q:
        n = q.popleft()
        for m in adj.get(n, []):
            if m not in seen:
                seen.add(m)
                q.append(m)
    sealed = [n for n in nodes if n not in seen and base[n[2]][n[1]] not in 'EG']
    if sealed:
        errs.append('%d sealed cells, e.g. %s' % (len(sealed), sorted(sealed)[:6]))
    if not any(('0', c, 1) in seen for c in range(GX, GX + 3)):
        errs.append('no path to the exit')
    spawns = [(y, c, r) for y in z.g for r in range(H) for c in range(W) if z.g[y][r][c] == 'S']
    if not 10 <= len(spawns) <= 14:
        errs.append('%d spawns' % len(spawns))
    for (y, c, r) in spawns:
        if (c - P0[0]) ** 2 + (r - P0[1]) ** 2 < 14 ** 2:
            errs.append('spawn %s < 14 m from P' % ((y, c, r),))
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if (y, c + dc, r + dr) not in nodes:
                    errs.append('spawn %s neighbour (%d,%d) not open' % ((y, c, r), c + dc, r + dr))
        if (y, c, r) not in seen:
            errs.append('spawn %s unreachable' % ((y, c, r),))
    na = sum(1 for y in z.g for row in z.g[y] for ch in row if ch == 'a')
    nh = sum(1 for y in z.g for row in z.g[y] for ch in row if ch == 'h')
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    for dc in (-2, -1, 1, 2):
        if base[P0[1] - 4][P0[0] + dc] != '.':
            errs.append('weapon stand cell blocked')
    for c in range(GX, GX + 3):
        for k in (1, 2):
            if base[k][c] != '.' or base[H - 1 - k][c] not in '.P':
                errs.append('gate approach blocked at col %d' % c)
    ups = sum(1 for n in seen if n[0] != '0')
    return errs, {'nodes': len(nodes), 'reached': len(seen), 'upper': ups, 'spawns': len(spawns), 'links': len(z.links)}


# ================================================================ zone 1: B1 deck / B2 floor, the entry level
def zone1():
    z = Zone('parking_1', 2)
    # deck: U shape (west and east bands, a north band between them), clear of the gate rows
    z.fill(DECK, 1, 4, 14, 37, 'u')
    z.fill(DECK, 36, 4, 14, 37, 'u')
    z.fill(DECK, 15, 4, 21, 8, 'u')
    # two ramps up to the north band, stairs from the entry plaza to the west / east bands
    z.ramp('0', 'N', 16, 12, DECK)
    z.ramp('0', 'N', 30, 12, DECK)
    z.ramp('0', 'Z', 6, 41, DECK)
    z.ramp('0', 'Z', 42, 41, DECK)
    # parking rows: floor (B2) and deck (B1) along the west / east walls, under / on the north band, the void middle
    F, D = '0.01', '3.61'
    wf = bays(z, F, '(', 2, 5, 11, 'z')
    ef = bays(z, F, ')', 44, 5, 11, 'z')
    nf = bays(z, F, '[', 15, 5, 7)
    cf1 = bays(z, F, '[', 21, 13, 3)
    cf2 = bays(z, F, ']', 21, 22, 3)
    wd = bays(z, D, '(', 2, 5, 11, 'z')
    ed = bays(z, D, ')', 44, 5, 11, 'z')
    nd = bays(z, D, '[', 15, 5, 7)
    park(z, '0', wf, 'VV.WVHV.VTV'[:11].replace('T', 'V'))
    park(z, '0', ef, 'V.VVW.VVHV.')
    park(z, '0', nf, 'VV.VV.V'[:3] + '.' + 'VWV')
    park(z, '0', cf1, 'V.H')
    park(z, '0', cf2, 'VW.')
    park(z, DECK, wd, 'V.VVH.VWV.V')
    park(z, DECK, ed, '.VV.VVW.V.V')
    park(z, DECK, nd, 'VV.V.VV')
    # the void south of the ramps: a box truck and a tow truck as big cover, wrecks, jersey barriers
    z.block('0', 'X', 16, 30)
    z.block('0', 'X', 32, 30)
    z.block('0', 'W', 23, 36, turned=True)
    z.fill('0', 21, 31, 2, 1, 'J')
    z.fill('0', 28, 31, 2, 1, 'J')
    z.fill('0', 24, 29, 2, 1, 'J')
    # deck aisles: a car stopped across the west aisle, a van on the east deck, cones and barriers by the ramp tops
    z.block(DECK, 'V', 9, 18)
    z.block(DECK, 'T', 39, 24)
    z.block(DECK, 'W', 9, 30)
    for (c, r) in ((14, 10), (36, 10), (15, 10), (35, 10)):
        z.put(DECK, c, r, 'o')
    z.block(DECK, 'J', 11, 36)
    z.block(DECK, 'J', 38, 13)
    # entry plaza: ticket barrier islands over the lanes, pay stations by the lift lobby, bikes, bollards
    for c in (13, 19, 31, 37):
        z.block('0', 'B', c, 43)
    for r in (44, 45):
        z.put('0', 2, r, 'p')
    for c in (46, 47, 48, 49):
        z.block('0', 'm', c, 50)
    z.block('0', 'k', 46, 43)
    for (c, r) in ((5, 50), (9, 50), (40, 49), (11, 41), (39, 41), (22, 47), (28, 47)):
        z.put('0', c, r, 'b')
    for (c, r) in ((15, 49), (16, 49), (34, 49), (12, 52)):
        z.put('0', c, r, 'o')
    z.fill('0', 2, 52, 2, 1, 'w')
    # spawns: floor north strip, aisles, the void; deck aisles
    for (c, r) in ((12, 2), (10, 13), (40, 13), (10, 27), (40, 27), (25, 20)):
        z.put('0', c, r, 'S')
    for (c, r) in ((9, 9), (41, 9), (8, 24), (42, 31), (22, 9)):
        z.put(DECK, c, r, 'S')
    z.put('0', 7, 36, 'a')
    z.put('0', 41, 24, 'h')
    z.put(DECK, 11, 14, 'h')
    z.put(DECK, 40, 36, 'a')
    z.put('0', 25, 27, 'h')
    finish(z, cols=[(c, r) for c in (7, 14, 36, 43) for r in (10, 16, 22, 28, 34)] + [(22, 11), (28, 11), (25, 32), (19, 40), (31, 40)],
           beams=(10, 16, 22, 28, 34), under_signs=((10, 20), (40, 20), (10, 33), (40, 33), (25, 7)),
           ceil_signs=((9, 21), (41, 21), (9, 33), (41, 33), (25, 8)), exits=((8, 41), (42, 41), (3, 46)), cctv=((2, 15), (48, 30)),
           ducts=(11, 39))
    marks(z, F, D)
    # aisles: dashed centre lines and arrows (floor and deck), the plaza crossing and speed bumps
    for y in (F, D):
        lanes(z, y, [(10, r, ':') for r in range(12, 40)] + [(40, r, ':') for r in range(12, 40)])
        lanes(z, y, [(10, 17, '^'), (40, 17, 'v'), (10, 35, '^'), (40, 35, 'v')])
    lanes(z, D, [(21, 10, '<'), (29, 10, '>')])
    lanes(z, F, [(25, r, ':') for r in range(28, 41)] + [(c, 48, '|') for c in range(22, 29)] + [(c, 50, '$') for c in range(13, 21)]
          + [(c, 50, '$') for c in range(30, 38)] + [(18, 29, 'v'), (32, 29, 'v'), (16, 52, '^'), (34, 52, '^')])
    return z


def zone2():
    """B2 deck / B3 floor / a split-level platform at 1.8 m: floor -> platform -> deck by half ramps, floor -> deck by a
    full ramp and a stair; the car wash in the double-height aisle"""
    z = Zone('parking_2', 3)
    P = '1.8'
    z.fill(DECK, 1, 4, 32, 10, 'u')          # north band
    z.fill(DECK, 33, 4, 17, 41, 'u')         # east band
    z.fill(P, 1, 14, 17, 25, 't')            # platform
    z.ramp('0', 'R', 10, 39, P)
    z.ramp(P, 'R', 3, 14, DECK)
    z.ramp('0', 'N', 26, 14, DECK)
    z.ramp('0', 'q', 25, 40, DECK)
    F, D, PM = '0.01', '3.61', '1.81'
    nf = bays(z, F, '[', 1, 5, 7)
    nf2 = bays(z, F, '[', 22, 5, 3)
    ef = bays(z, F, ')', 44, 5, 13, 'z')
    ef2 = bays(z, F, '(', 34, 15, 8, 'z')
    nd = bays(z, D, '[', 2, 5, 10)
    ed = bays(z, D, ')', 44, 5, 13, 'z')
    ed2 = bays(z, D, '(', 34, 15, 8, 'z')
    pw = bays(z, PM, '(', 2, 23, 5, 'z')
    pe = bays(z, PM, ')', 12, 23, 4, 'z')
    park(z, '0', nf, 'VWV.VHV')
    park(z, '0', nf2, 'V.V')
    park(z, '0', ef, 'VV.VWVV.VVHV.')
    park(z, '0', ef2, 'V.VWV.VV')
    park(z, DECK, nd, 'VVH.V.VVWV')
    park(z, DECK, ed, 'V.VVV.WVV.VVV')
    park(z, DECK, ed2, '.VV.VHV.')
    park(z, P, pw, 'VVWV.')
    park(z, P, pe, 'V.VV')
    # the double-height aisle: car wash beside the ramp, a pickup and a burnt wreck, barriers
    z.block('0', 'A', 19, 15)
    z.block('0', 'T', 20, 31)
    z.block('0', 'W', 27, 33)
    z.block('0', 'J', 23, 37)
    z.block('0', 'J', 29, 31)
    for (c, r) in ((19, 26), (20, 26), (24, 25)):
        z.put('0', c, r, 'o')
    # platform: a maintenance buggy, cones round the ramp top, drums
    z.block(P, 'g', 9, 16)
    for (c, r) in ((8, 21), (8, 14), (14, 15)):
        z.put(P, c, r, 'o')
    z.put(P, 16, 37, 'D')
    # deck: a van across the aisle, jersey barriers, a covered car
    z.block(DECK, 'T', 40, 27)
    z.block(DECK, 'J', 15, 11)
    z.block(DECK, 'W', 40, 36)
    # south: motorbikes and scooters, a bike rack, bins, pay station, bollards, a tow truck in the open
    for c in range(1, 6):
        z.block('0', 'm', c, 48)
    z.block('0', 'k', 1, 51)
    z.block('0', 'X', 37, 46)
    z.block('0', 'w', 47, 53)
    z.put('0', 20, 49, 'p')
    for (c, r) in ((9, 48), (15, 48), (19, 44), (31, 49), (44, 48)):
        z.put('0', c, r, 'b')
    for (c, r) in ((7, 3), (14, 2), (40, 2)):
        z.put('0', c, r, 'o')
    for (c, r) in ((12, 11), (40, 12), (40, 30), (24, 30), (9, 52), (44, 52)):
        z.put('0', c, r, 'S')
    for (c, r) in ((9, 28), (12, 18)):
        z.put(P, c, r, 'S')
    for (c, r) in ((22, 11), (41, 18), (41, 42)):
        z.put(DECK, c, r, 'S')
    z.put('0', 30, 44, 'a')
    z.put(DECK, 42, 10, 'a')
    z.put(P, 7, 36, 'h')
    z.put('0', 42, 38, 'h')
    z.put(DECK, 6, 12, 'h')
    finish(z, cols=[(c, r) for c in (33, 43) for r in (10, 16, 22, 28, 34, 40)] + [(c, 10) for c in (8, 14, 20, 27)] + [(c, 13) for c in (11, 17, 23)]
           + [(24, 34), (31, 38)], beams=(10, 16, 22, 28, 34, 40), under_signs=((12, 8), (24, 8), (41, 20), (41, 36)),
           ceil_signs=((14, 8), (27, 8), (41, 14), (41, 30), (9, 30)), exits=((36, 41), (3, 44), (48, 50)), cctv=((2, 12), (48, 20)),
           ducts=(21, 47))
    marks(z, F, D, extra_layers=((PM, lambda c, r: z.g[P][r][c] == 't'),))
    for y in (F, D):
        lanes(z, y, [(41, r, ':') for r in range(6, 44)] + [(41, 26, 'v'), (41, 12, '^')])
    lanes(z, D, [(c, 11, ':') for c in range(8, 26)])
    lanes(z, F, [(c, 11, ':') for c in range(2, 32)] + [(31, r, ':') for r in range(30, 45)] + [(28, 31, 'v'), (12, 48, '^')]
          + [(c, 47, '$') for c in range(21, 29)] + [(c, 52, '|') for c in range(22, 29)])
    lanes(z, PM, [(8, r, ':') for r in range(23, 38)] + [(8, 31, '^')])
    return z


def zone3():
    """B3 deck / B4 floor / the loading dock at 1.2 m with delivery trucks backed up to it; the deep parking hall under
    the deck (wrecks, covered cars, maintenance cages); a ramp to a deck tongue and a stair to the east band"""
    z = Zone('parking_3', 4)
    K = '1.2'
    z.fill(DECK, 30, 4, 20, 41, 'u')          # east band
    z.fill(DECK, 21, 12, 9, 6, 'u')           # tongue over the ramp top
    z.fill(K, 1, 1, 20, 6, 'd')               # loading dock
    z.ramp('0', 'N', 23, 18, DECK)
    z.ramp('0', 'Z', 31, 45, DECK)
    z.ramp('0', 'Q', 7, 7, K)
    z.ramp('0', 'O', 16, 7, K)
    # dock edges (bumpers) along the open sides, except where the steps and the ramp arrive
    for c in range(1, 21):
        if (K, c, 6) not in z.openings:
            z.g[K][6][c] = 'e'
    for r in range(1, 6):
        z.g[K][r][20] = 'e'
    z.block('0', 'Y', 3, 7)
    z.block('0', 'Y', 10, 7)
    # on the dock: pallets, a cage, a forklift, drums
    z.block(K, 'L', 2, 1)
    z.block(K, 'L', 5, 1)
    z.block(K, 'K', 13, 2)
    z.block(K, 'F', 9, 2)
    z.put(K, 18, 2, 'D')
    z.put(K, 17, 4, 'D')
    F, D = '0.01', '3.61'
    ef = bays(z, F, ')', 44, 5, 13, 'z')
    wf = bays(z, F, '(', 31, 5, 13, 'z')
    ed = bays(z, D, ')', 44, 5, 13, 'z')
    wd = bays(z, D, '(', 31, 19, 8, 'z')
    park(z, '0', ef, 'WVW.VWVV.WVWV')
    park(z, '0', wf, 'VW.VVW.V.WVV.')
    park(z, DECK, ed, 'VV.VHVV.VWV.V')
    park(z, DECK, wd, 'V.VVW.VV')
    # deep hall: maintenance cages by the east aisle, drums; deck: barriers, a pickup
    z.block('0', 'K', 39, 8)
    z.block('0', 'K', 39, 30)
    z.put('0', 42, 9, 'D')
    z.put('0', 42, 31, 'D')
    z.block(DECK, 'T', 39, 12)
    z.block(DECK, 'J', 37, 34)
    z.block(DECK, 'J', 26, 13)
    # the west hall (double height): box truck, tow truck, wrecks, bikes, buggy, jersey barriers
    z.block('0', 'X', 4, 22)
    z.block('0', 'X', 12, 30)
    z.block('0', 'W', 4, 36, turned=True)
    z.block('0', 'W', 16, 20)
    z.block('0', 'g', 2, 44)
    z.block('0', 'k', 17, 44)
    for c in range(8, 12):
        z.block('0', 'm', c, 46)
    z.block('0', 'J', 21, 38)
    z.block('0', 'J', 8, 18)
    z.block('0', 'L', 19, 9)
    for (c, r) in ((22, 2), (28, 2), (21, 9)):
        z.put('0', c, r, 'o')
    for (c, r) in ((4, 52), (18, 52), (36, 50)):
        z.put('0', c, r, 'b')
    for (c, r) in ((10, 27), (8, 41), (29, 37), (40, 20), (40, 44), (28, 6)):
        z.put('0', c, r, 'S')
    for (c, r) in ((5, 4), (12, 5)):
        z.put(K, c, r, 'S')
    for (c, r) in ((40, 6), (40, 25), (26, 15)):
        z.put(DECK, c, r, 'S')
    z.put('0', 14, 40, 'a')
    z.put(DECK, 41, 40, 'a')
    z.put(K, 18, 4, 'h')
    z.put('0', 41, 26, 'h')
    finish(z, cols=[(c, r) for c in (30, 43) for r in (10, 16, 22, 28, 34, 40)] + [(21, 16), (29, 12)] + [(10, 34), (20, 28)],
           beams=(10, 16, 22, 28, 34, 40), under_signs=((40, 15), (40, 38), (25, 14)),
           ceil_signs=((40, 9), (40, 32), (10, 8), (24, 15)), exits=((32, 44), (2, 7), (48, 50)), cctv=((2, 30), (48, 12)),
           ducts=(19, 41))
    marks(z, F, D)
    for y in (F, D):
        lanes(z, y, [(40, r, ':') for r in range(5, 44)] + [(40, 18, '^'), (40, 34, 'v')])
    lanes(z, F, [(c, 41, ':') for c in range(2, 30)] + [(25, r, ':') for r in range(35, 53)] + [(25, 36, '^'), (9, 33, 'v')]
          + [(c, 49, '$') for c in range(20, 30)])
    return z


def under_cells(z):
    d = z.g[DECK]
    return {(c, r) for r in range(1, H - 1) for c in range(1, W - 1) if d[r][c] != '.'}


def finish(z, cols, beams, under_signs, ceil_signs, exits, cctv, ducts):
    rails(z, DECK, 'u')
    for y, ch in SOLID_DECKS.items():
        if y in z.g:
            rails(z, y, ch)
    columns(z, cols)
    lv, up = str(z.lv), str(z.lv - 1)
    # under the deck: beams on the column rows, strips between, sprinkler pipes, the floor's level signs
    fittings(z, UNDER, under_cells(z), lv, lit_rows=(7, 13, 19, 25, 31, 37, 43), beam_rows=beams, lamp_cols=(), pipe_rows=(5,),
             extra=[(c, r, lv) for (c, r) in under_signs] + [(c, r, 'x') for (c, r) in exits] + [(c, r, 'c') for (c, r) in cctv])
    # ceiling over everything: beams, strips, ducts, the deck's level signs over the deck
    allc = {(c, r) for r in range(1, H - 1) for c in range(1, W - 1)}
    fittings(z, CEIL, allc, up, lit_rows=(2, 7, 13, 19, 25, 31, 37, 43, 49), beam_rows=beams + (46,), lamp_cols=(), duct_cols=ducts,
             pipe_rows=(5, 52), extra=[(c, r, up) for (c, r) in ceil_signs] + [(c, r, 'x') for (c, r) in ((24, 1), (26, 1))]
             + [(c, r, 'c') for (c, r) in ((cc + 1, rr + 2) for (cc, rr) in cctv)])


def marks(z, F, D, extra_layers=()):
    """hatching at ramp / stair feet, oil stains, puddles and drains (deterministic scatter)"""
    base = z.g['0']
    for y, walk in ((F, lambda c, r: base[r][c] == '.' and not is_deck(z, '1.8', c, r) and not is_deck(z, '1.2', c, r)),
                    (D, lambda c, r: z.g[DECK][r][c] == 'u')) + tuple(extra_layers):
        g = z.L(y)
        for (ya, ca, ra, yb, cb, rb) in z.links:   # yellow hatching in front of every ramp / stair foot
            if (y == F and ya == '0') or (y == D and ya == DECK) or (y == '1.81' and ya == '1.8'):
                if ra == rb:
                    continue
                for dr in (0, 1) if ra > rb else (0, -1):
                    for dc in (-1, 0, 1):
                        rr, cc = ra + dr, ca + dc
                        if 0 < rr < H - 1 and g[rr][cc] == '.' and walk(cc, rr):
                            g[rr][cc] = '%'
        for r in range(2, H - 2):
            for c in range(2, W - 2):
                if g[r][c] != '.' or not walk(c, r):
                    continue
                h = hsh(c, r, len(y))
                if h < 0.022:
                    g[r][c] = '!'
                elif h < 0.03 and y == F:
                    g[r][c] = '?'
                elif h < 0.036 and y == F:
                    g[r][c] = '&'


def lanes(z, y, pts):
    g = z.L(y)
    for (c, r, ch) in pts:
        if g[r][c] in '.!?&':
            g[r][c] = ch


if __name__ == '__main__':
    ok = True
    for zf in (zone1, zone2, zone3):
        z = zf()
        errs, st = validate(z)
        print('%-12s %s' % (z.name, st))
        for e in errs:
            print('   ERROR', e)
            ok = False
        with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
            f.write(z.text())
        if '--print' in sys.argv:
            print(z.text())
    sys.exit(0 if ok else 1)
