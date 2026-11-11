"""Rustmoor Salvage zone layouts (src/data/zones/scrapyard_{1,2}.txt). Run from Source/: python3 tools/scrapyard_zones.py

Zone 1, the Stacks (68 x 70): the haul road runs from the entry (south) to the exit (north) past the weighbridge and
its office; west of it, canyons of crushed-car bale stacks (two lines of stacks with cross cuts, tall and low stacks
mixed) under a scrap mountain, the dead-tech piles (monitors, server racks, cable drums, e-waste) and the flattened-car
stacks in the south-west; north-east, the baler line under the material-handling crane with its magnet; east, wrecked
giant limbs and broken giant guns lying among scrap mounds; floodlight towers throw pools of sodium light.

Zone 2, the Titan Graveyard (70 x 72): the kneeling dead titan in the north towers over the yard (you walk between its
legs to the exit); its torn-off arm lies beside it with the salvage scaffold (decks at 3 and 6 m); the fallen torso lies
across the west (walk through it); the ribcage frame in the east carries plating ramps up to decks at 3.0 and 5.4 m;
the enormous head lies in the south-east, the broken cannon in the south-west; dead reactor cores glow among warning
beacons; armour plates stand in the ground; scrap mountains, bale stacks and dead tech round the edges.

Grids: the floor plan and "@layer 0" (the weighbridge and oil stains, wall codes).
Wall codes (on wall cells of the "@layer 0" grid; the theme's wall chooser reads them):
  1 RUSTMOOR SALVAGE sign, 2 DANGER sign, 3 a crushed car nose-down in the bank, 4 tyres, 5 a reactor leak (zone 2),
  6 an armour plate (zone 2), 7 titan fingers (zone 2); 9 on the corner cell (0, 0) marks zone 2 (the graveyard banks)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zonekit import Zone, validate, rects, OUT  # noqa: E402

PREFABS = {'K': (2, 2), 'k': (2, 2), 'Q': (2, 4), 'H': (10, 10), 'm': (4, 4), 'T': (2, 2), 'O': (8, 6), 'Z': (14, 12),
           'Y': (4, 4), 'F': (4, 3), 'L': (8, 3), 'A': (6, 3), 'R': (10, 3), 'N': (6, 3), 'M': (3, 3), 'V': (4, 2),
           'D': (2, 2), 'B': (4, 2), 'W': (2, 4), 'X': (2, 3), 'I': (22, 20), 'J': (18, 10), 'q': (10, 10), 'r': (18, 12),
           'C': (20, 4), 'U': (4, 4), 'n': (12, 4), 'e': (12, 4), 'p': (3, 1)}
LAYER0 = {'w': (4, 10), 'u': (2, 2)}
WALK = set('.SPah')


class Layer:
    def __init__(self, z):
        self.z = z
        self.g = [['.'] * z.w for _ in range(z.h)]

    def put(self, c, r, ch):
        self.g[r][c] = ch

    def block(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.put(c, r, ch)

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


def shell(name, w, h, gate):
    z = Zone(name, w, h)
    z.rect(0, 0, w, 1, '#')
    z.rect(0, h - 1, w, 1, '#')
    z.rect(0, 0, 1, h, '#')
    z.rect(w - 1, 0, 1, h, '#')
    for k in range(3):
        z.g[0][gate + k] = 'G'
        z.g[h - 1][gate + k] = 'E'
    return z


def codes(L, z, cells, ch):
    for (c, r) in cells:
        assert z.at(c, r) == '#', (z.name, c, r, z.at(c, r))
        L.put(c, r, ch)


def stack_line(z, c0, r0, n, vertical, pattern, gaps=()):
    """A line of 2 x 2 bale stacks (2 cells thick): pattern cycles through 'K' (tall) / 'k' (low) per stack;
    gaps: stack indices left open (cross cuts)."""
    for i in range(n):
        if i in gaps:
            continue
        ch = pattern[i % len(pattern)]
        c, r = (c0, r0 + 2 * i) if vertical else (c0 + 2 * i, r0)
        z.block(c, r, 2, 2, ch)


# ================================================================ zone 1: the Stacks
def zone1():
    W, H = 68, 70
    z = shell('scrapyard_1', W, H, 32)
    L0 = Layer(z)
    # ---- scrap mountains in the corners and on the west wall
    z.block(1, 1, 10, 10, 'H')
    z.block(1, 34, 10, 10, 'H')
    z.block(57, 59, 10, 10, 'H')
    # ---- the bale canyons (west): two lines of stacks with cross cuts, a third short line along the road
    stack_line(z, 13, 3, 14, True, 'KKkKkK', gaps=(4, 9))
    stack_line(z, 21, 1, 15, True, 'KkKKkKk', gaps=(3, 8, 12))
    stack_line(z, 1, 13, 5, False, 'kKKk', gaps=(2,))
    stack_line(z, 1, 25, 4, False, 'KkK', gaps=(1,))
    # stacks in the west canyon floor (low cover) and a parked wreck
    z.block(16, 10, 2, 2, 'k')
    z.block(16, 24, 2, 2, 'k')
    z.block(24, 14, 2, 4, 'W')
    z.block(24, 26, 2, 2, 'k')
    z.puts([(17, 18), (18, 32), (25, 6)], 't')
    z.puts([(9, 22), (9, 23), (5, 20)], 'o')
    # ---- floodlight towers (pools of light >= 13 m apart)
    for (c, r) in ((17, 20), (44, 30), (8, 52), (55, 47), (34, 9), (28, 39)):
        z.block(c, r, 2, 2, 'T')
    # ---- the baler line under the crane (north-east), a forklift and a skip beside it, bales waiting
    z.block(47, 4, 14, 12, 'Z')
    z.block(63, 6, 2, 3, 'X')
    z.block(62, 12, 4, 2, 'B')
    stack_line(z, 41, 2, 3, True, 'Kkk')
    z.block(43, 14, 2, 2, 'k')
    z.puts([(62, 2), (63, 2), (65, 3)], 'o')
    # ---- the dead-tech piles (south-west of the canyons)
    z.block(13, 37, 3, 3, 'M')
    z.block(19, 41, 3, 3, 'M')
    z.block(13, 44, 4, 2, 'V')
    z.block(22, 36, 2, 2, 'D')
    z.block(17, 35, 2, 2, 'D')
    z.puts([(24, 41), (24, 42), (11, 47)], 'd')
    z.puts([(19, 38), (20, 38), (12, 41)], 'x')
    # ---- weighbridge and its office (west side of the haul road, the scale in the road)
    z.block(19, 50, 8, 6, 'O')
    L0.block(28, 48, 4, 10, 'w')
    z.run(28, 46, 4, 'j')
    z.run(28, 59, 4, 'j')
    # ---- flattened-car stacks, tyres, a skip and wrecks in the south-west
    for (c, r) in ((2, 57), (5, 57), (12, 60), (15, 60), (2, 62)):
        z.block(c, r, 2, 4, 'Q')
    z.block(9, 64, 4, 2, 'B')
    z.puts([(8, 58), (8, 59), (11, 58), (18, 63), (19, 63), (18, 64)], 't')
    z.block(22, 62, 2, 4, 'W')
    z.block(5, 47, 2, 2, 'k')
    # ---- east: wrecked giant limbs and guns among scrap mounds
    z.block(48, 20, 4, 4, 'Y')
    z.block(57, 22, 8, 3, 'L')
    z.block(42, 40, 10, 3, 'R')
    z.block(56, 34, 6, 3, 'N')
    z.block(46, 50, 4, 3, 'F')
    z.block(38, 26, 6, 3, 'A')
    z.block(60, 27, 4, 4, 'm')
    z.block(42, 33, 4, 4, 'm')
    z.block(53, 54, 4, 4, 'm')
    stack_line(z, 63, 39, 6, True, 'KkK', gaps=(2,))
    z.block(52, 40, 2, 4, 'Q')
    z.block(46, 58, 2, 4, 'Q')
    z.puts([(58, 30), (53, 28), (47, 46), (64, 52)], 't')
    z.puts([(51, 36), (52, 36), (40, 48), (41, 48), (40, 47)], 'x')
    # ---- the wrecks queued for the baler (north), the bale median splitting the haul road into two lanes
    z.block(37, 1, 2, 4, 'W')
    z.block(25, 1, 2, 4, 'Q')
    stack_line(z, 33, 23, 7, True, 'kKkKKk', gaps=(3,))
    # ---- more east cover: a dead-tech pile and a cable drum among the limbs
    z.block(52, 29, 3, 3, 'M')
    z.block(45, 24, 2, 2, 'D')
    # ---- the south-west yard's edge, the south-east bale yard (stacks on a grid, lanes between)
    z.block(2, 52, 2, 2, 'k')
    z.block(12, 49, 2, 2, 'K')
    for (c, r, ch) in ((41, 60, 'K'), (41, 64, 'k'), (49, 60, 'k'), (49, 64, 'K'), (45, 66, 'K'), (53, 64, 'k')):
        z.block(c, r, 2, 2, ch)
    # ---- the haul road: barriers, a parked wreck, oil stains
    z.run(38, 20, 3, 'j')
    z.run(30, 24, 3, 'j')
    z.run(36, 34, 3, 'j')
    z.block(29, 14, 2, 4, 'W')
    for (c, r) in ((33, 20), (31, 31), (35, 41), (37, 60), (24, 9), (52, 26)):
        L0.block(c, r, 2, 2, 'u')
    # ---- entry, spawns, pickups
    z.put(33, 66, 'P')
    z.puts([(17, 5), (25, 30), (6, 30), (8, 18), (36, 16), (40, 22), (57, 19), (60, 45), (50, 46), (36, 30),
            (8, 49), (19, 47)], 'S')
    z.puts([(26, 22), (58, 39), (12, 54)], 'a')
    z.puts([(43, 12), (39, 55)], 'h')
    # ---- wall codes: signs by the gates, cars and tyres in the banks
    codes(L0, z, [(30, 69), (36, 69), (29, 0), (37, 0)], '1')
    codes(L0, z, [(0, 24), (67, 20), (20, 0), (0, 56)], '2')
    codes(L0, z, [(0, 15), (0, 29), (67, 33), (67, 58), (14, 69), (48, 69), (44, 0), (25, 0)], '3')
    codes(L0, z, [(0, 50), (67, 44), (24, 69), (55, 69), (12, 0)], '4')
    return z, [(0, L0)]


# ================================================================ zone 2: the Titan Graveyard
def zone2():
    W, H = 70, 72
    z = shell('scrapyard_2', W, H, 34)
    L0 = Layer(z)
    L0.put(0, 0, '9')
    # ---- the kneeling titan (north, facing south, its legs straddling the way to the exit)
    z.block(24, 3, 22, 20, 'I')
    # its torn-off arm and the salvage scaffold on its west side
    z.block(11, 9, 12, 4, 'e')
    z.block(11, 3, 12, 4, 'n')
    # ---- the fallen torso across the west (walk through, west to east)
    z.block(4, 26, 18, 10, 'J')
    # ---- the ribcage frame in the east (ramps up from the west end)
    z.block(47, 24, 18, 12, 'r')
    # ---- the enormous head (south-east), the broken cannon (south-west)
    z.block(48, 52, 10, 10, 'q')
    z.block(6, 56, 20, 4, 'C')
    # ---- dead reactor cores with warning beacons round them
    z.block(30, 34, 4, 4, 'U')
    z.block(60, 12, 4, 4, 'U')
    z.block(28, 58, 4, 4, 'U')
    z.puts([(29, 33), (34, 38), (59, 11), (64, 16), (27, 57), (32, 62), (46, 8), (23, 24)], 'b')
    # ---- armour plates standing in the ground, giant limbs, a broken gun
    for (c, r) in ((38, 44), (16, 44), (56, 42), (40, 26), (8, 48), (24, 66)):
        z.block(c, r, 3, 1, 'p')
    z.block(36, 48, 4, 4, 'Y')
    z.block(10, 18, 8, 3, 'L')
    z.block(59, 44, 4, 3, 'F')
    z.block(40, 62, 6, 3, 'A')
    z.block(17, 49, 6, 3, 'N')
    # ---- the open graveyard floor: more remains as cover (a giant rifle, mounds, a second hand, stacks, wrecks)
    z.block(18, 40, 10, 3, 'R')
    z.block(40, 29, 4, 4, 'm')
    z.block(28, 45, 4, 4, 'm')
    z.block(45, 37, 2, 2, 'K')
    z.block(19, 22, 2, 2, 'k')
    z.block(36, 26, 2, 2, 'K')
    z.block(13, 52, 2, 4, 'Q')
    z.block(30, 51, 3, 3, 'M')
    z.block(44, 46, 2, 4, 'W')
    z.block(24, 30, 4, 4, 'Y')
    # ---- scrap mountains and stacks round the edges, dead tech
    z.block(1, 61, 10, 10, 'H')
    z.block(59, 61, 10, 10, 'H')
    z.block(59, 1, 10, 10, 'H')
    z.block(1, 1, 4, 4, 'm')
    z.block(1, 38, 4, 4, 'm')
    stack_line(z, 1, 12, 4, True, 'KkK')
    stack_line(z, 66, 38, 8, True, 'KkKK', gaps=(3,))
    stack_line(z, 48, 1, 3, False, 'kKk')
    z.block(52, 38, 3, 3, 'M')
    z.block(42, 56, 4, 2, 'V')
    z.block(24, 38, 2, 2, 'D')
    z.puts([(47, 12), (12, 40), (26, 46), (13, 66)], 'd')
    z.puts([(53, 42), (54, 42), (44, 58), (25, 44)], 'x')
    z.puts([(6, 22), (7, 22), (45, 32), (55, 20), (36, 56)], 't')
    # ---- floodlight towers
    for (c, r) in ((22, 25), (47, 21), (13, 41), (56, 48), (36, 66), (8, 6)):
        z.block(c, r, 2, 2, 'T')
    # oil and coolant stains
    for (c, r) in ((36, 40), (20, 54), (52, 20), (44, 66), (30, 25)):
        L0.block(c, r, 2, 2, 'u')
    # ---- entry, spawns, pickups
    z.put(35, 68, 'P')
    z.puts([(14, 23), (6, 44), (26, 52), (40, 38), (54, 44), (62, 22), (52, 12), (30, 28), (13, 15), (42, 24),
            (62, 40), (20, 64)], "S")
    z.puts([(44, 44), (10, 52), (56, 66)], 'a')
    z.puts([(22, 38), (62, 20)], 'h')
    # ---- wall codes: the graveyard banks (armour plates, fingers, reactor leaks), signs by the gates
    codes(L0, z, [(32, 71), (38, 71), (31, 0), (39, 0)], '2')
    codes(L0, z, [(0, 20), (0, 46), (69, 30), (69, 54), (22, 71), (48, 71), (20, 0)], '5')
    codes(L0, z, [(0, 24), (0, 52), (69, 26), (69, 36), (14, 71), (28, 71), (44, 0), (26, 0)], '6')
    codes(L0, z, [(0, 32), (69, 18), (69, 48), (10, 71), (54, 71), (14, 0)], '7')
    return z, [(0, L0)]


def check(z, layers):
    errs = []
    for y, L in layers:
        for r in range(z.h):
            for c in range(z.w):
                ch = L.g[r][c]
                if ch in LAYER0 and z.at(c, r) not in WALK:
                    errs.append('layer 0 %r over %r at %d,%d' % (ch, z.at(c, r), c, r))
                if ch in '0123456789' and z.at(c, r) != '#':
                    errs.append('wall code off a wall at %d,%d' % (c, r))
        for ch, (sw, sd) in LAYER0.items():
            for (c, r, w, h) in rects(L.g, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('layer 0 %r block %dx%d at (%d,%d)' % (ch, w, h, c, r))
    # floodlight pools (r 6.2) never overlap: towers >= 13 m apart
    T = [(c, r) for (c, r, w, h) in rects(z.g, 'T')]
    for i in range(len(T)):
        for j in range(i):
            if math.hypot(T[i][0] - T[j][0], T[i][1] - T[j][1]) < 13:
                errs.append('flood towers %s %s closer than 13 m' % (T[i], T[j]))
    return errs


def main():
    out = []
    for fn in (zone1, zone2):
        z, layers = fn()
        errs, stats = validate(z, WALK, PREFABS, size=((64, 72), (66, 74)))
        errs += check(z, layers)
        txt = z.text() + ''.join('@layer %s\n' % y + L.text() for y, L in layers)
        out.append((z, errs, stats, txt))
    ok = True
    for z, errs, stats, txt in out:
        print('%-12s %s' % (z.name, stats))
        for e in errs:
            print('   ERROR', e)
            ok = False
    if ok:
        for z, errs, stats, txt in out:
            open(os.path.join(OUT, z.name + '.txt'), 'w').write(txt)
    if '--print' in sys.argv:
        for z, errs, stats, txt in out:
            print('\n' + z.name + '\n' + txt)
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
