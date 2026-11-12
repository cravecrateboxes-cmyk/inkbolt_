#!/usr/bin/env python3
"""INKBOLT Airfield 7 zones (theme 'airfield7'): hand-placed layouts -> src/data/zones/airfield7_*.txt

    python3 tools/airfield7_zones.py           # write + validate
    python3 tools/airfield7_zones.py --check   # validate only
    python3 tools/airfield7_zones.py --print   # also print the maps

A made-up remote military air base on the arid steppe. Player travel is north.
Zone 1, the flight line (76 x 78): the runway crosses the zone east - west (rows 6-23; the theme paints it and runs it
on for kilometres past both side walls, where the zone is closed by low runway-closure barriers instead of T-walls),
the taxiway parallel to it (rows 28-37) with its two link taxiways, sand and scrub between them, the concrete apron
(rows 40-76). Two fighter revetments on the west apron (fighters nose out), the transport with its ramp down in the
middle of the apron (walk-in hold, the spawn behind its ramp), the fuel bowser at its wing, the control tower
(landmark, terrace at 3.6 m) with the crash tender on the east apron, a fighter on the apron with its tug, a fighter
taxiing, the runway caravan at the threshold, AA guns in sandbag nests on the north shoulder, the runway blocked with
jersey barriers and tank traps, a fighter that rolled out on the runway.
Zone 2, the hangar area (72 x 74): the hardened aircraft shelter (landmark) with a fighter under maintenance, the
maintenance hangar (workshops, parts racks, the tool crib, an engine on its dolly), the engine test stand, the
ordnance igloo with munitions trailers and the forklift, the barracks block (gallery at 3.2 m, two stairs) round
its yard, the supply dump under a camouflage net, sandbag positions.
Each zone file is the floor plan followed by "@layer 0" (aircraft and workshop gear inside the revetments, the shelter
and the hangar). Symbols: src/data/themes/airfield7.js.
"""
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {'T': (12, 12), 'Q': (30, 28), 'R': (18, 18), 'F': (10, 16), 'K': (16, 10), 'W': (16, 10), 'V': (10, 16),
          'M': (10, 16), 'X': (3, 10), 'B': (3, 8), 'C': (3, 6), 'U': (2, 3), 'O': (2, 4), 'g': (2, 2), 'n': (2, 1),
          'm': (2, 1), 'v': (2, 1), 'H': (28, 30), 'N': (28, 22), 'Y': (26, 10), 'D': (16, 12), 'Z': (14, 10),
          'z': (8, 5), 'q': (3, 1), '1': (4, 1), '2': (4, 1), '3': (3, 1), '5': (2, 4), 'p': (2, 2), 'A': (3, 3),
          'J': (2, 4), 'y': (2, 1), '&': (4, 4), '$': (2, 2), '8': (2, 3)}
FLOOR = '.'


class AZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, i):
        return self.L[i][1]

    def pf(self, ch, c, r, n=1, dc=0, dr=0, over=FLOOR, g=None):
        w, d = PREFAB[ch]
        g = g or self
        for k in range(n):
            g.block(c + k * dc, r + k * dr, w, d, ch, over=over)

    def text(self):
        out = Zone.text(self)
        for (y, L) in self.L:
            out += '@layer %s\n' % ('%g' % y) + L.text()
        return out


def ring(z):
    z.rect(0, 0, z.w, 1, '#')
    z.rect(0, z.h - 1, z.w, 1, '#')
    z.rect(0, 0, 1, z.h, '#')
    z.rect(z.w - 1, 0, 1, z.h, '#')


RWY = (6, 24)        # zone 1 runway rows [6, 24)
TWY = (28, 38)       # taxiway rows [28, 38)


# ================================================================ zone 1: the flight line
def zone1():
    W, H = 76, 78
    z = AZone('airfield7_1', W, H, [0.0])
    IN = z.layer(0)
    ring(z)
    z.rect(35, H - 1, 3, 1, 'E')     # the main gate checkpoint
    z.rect(36, 0, 3, 1, 'G')         # the gate in the north T-walls (to the hangar area)
    z.put(36, 74, 'P')
    # ---- the apron: the transport with its ramp down (nose north), the bowser at its wing, a GPU, chocks
    z.pf('Q', 22, 42)
    z.pf('B', 54, 55)
    z.pf('g', 54, 65)
    z.puts([(33, 71), (40, 71)], 'c')
    z.put(30, 74, 'b')
    z.put(44, 74, 'f')
    z.puts([(20, 72), (21, 72)], 'k')
    # ---- the west revetments (open east) with their fighters nose out, gear in front of each
    for r0 in (40, 58):
        z.pf('R', 1, r0)
        IN.block(4, r0 + 4, 16, 10, 'K')
        z.puts([(20, r0 + 6), (20, r0 + 11)], 'c')
        z.put(19, r0 + 1, 'L')
    z.put(21, 60, 'f')
    z.put(21, 43, 'b')
    # ---- the control tower (landmark) on the east apron, the crash tender, a fighter with its tug, light masts
    z.pf('T', 62, 41)
    z.pf('X', 58, 42)
    z.pf('V', 62, 57)
    z.pf('U', 66, 54)
    z.puts([(61, 64), (72, 64)], 'c')
    z.pf('g', 72, 58)
    z.put(74, 74, 'L')
    z.put(56, 75, 'L')
    z.put(59, 53, 'f')
    z.puts([(57, 73), (58, 73), (57, 72)], 'd')
    z.put(74, 40, 'b')
    # ---- the sand strip between the apron and the taxiway: signs, scrub, taxiway lights
    for c in range(3, 74, 6):
        z.put(c, 39, 'i')
    z.pf('n', 26, 38)
    z.pf('m', 48, 38)
    for (c, r) in ((10, 38), (15, 38), (41, 39), (60, 39), (69, 38)):
        z.put(c, r, 's' if c % 2 else 'u')
    # ---- the taxiway: a fighter taxiing west, lights along its edges
    z.pf('W', 44, 28)
    for c in range(2, 74, 6):
        z.put(c, 27, 'i')
    # ---- between the taxiway and the runway: the runway caravan at the west threshold, the holding signs, scrub
    z.block(5, 24, 6, 3, 'C')
    z.pf('v', 18, 25)
    z.pf('v', 58, 25)
    for (c, r) in ((25, 25), (33, 26), (45, 25), (52, 26), (69, 25), (72, 26)):
        z.put(c, r, 's' if c % 2 else 'u')
    # ---- the runway: edge lights, the blocked runway (jersey barrier lines, tank traps), a fighter that rolled out
    for c in range(2, 74, 6):
        z.put(c, RWY[0], 'l')
        z.put(c, RWY[1] - 1, 'l')
    z.pf('W', 50, 9)
    z.pf('U', 46, 12)
    z.puts([(49, 11), (49, 18)], 'c')
    z.run(28, 13, 5, 'j')
    z.run(10, 16, 4, 'j')
    z.run(62, 20, 4, 'j')
    for (c, r) in ((20, 9), (24, 19), (36, 9), (39, 18), (42, 14), (14, 11), (67, 13), (6, 19), (33, 21), (70, 9)):
        z.put(c, r, 'x')
    z.pf('O', 22, 11)
    z.pf('U', 24, 12)
    z.pf('$', 11, 9)
    z.puts([(12, 11), (13, 11)], 'k')
    # ---- the north shoulder: AA guns in sandbag nests, the windsock, edge scrub
    for c0 in (13, 55):
        z.pf('A', c0, 1)
        z.run(c0 - 1, 4, 5, '=')
        z.put(c0 - 1, 3, '=')
        z.put(c0 + 3, 3, '=')
        z.put(c0 + 4, 2, 'k')
    z.put(27, 3, 'w')
    for (c, r) in ((5, 2), (31, 2), (46, 3), (66, 2), (71, 4)):
        z.put(c, r, 's' if c % 2 else 'u')
    # ---- spawn cans and pickups
    for (c, r) in ((7, 33), (20, 34), (33, 32), (63, 33), (70, 31), (18, 8), (34, 16), (57, 21), (71, 17), (49, 5),
                   (29, 3), (56, 47)):
        z.put(c, r, 'S')
    z.puts([(54, 70), (8, 21)], 'a')
    z.put(40, 26, 'a')
    z.puts([(21, 56), (66, 34)], 'h')
    return z


# ================================================================ zone 2: the hangar area
def zone2():
    W, H = 72, 74
    z = AZone('airfield7_2', W, H, [0.0])
    IN = z.layer(0)
    ring(z)
    z.rect(34, H - 1, 3, 1, 'E')
    z.rect(34, 0, 3, 1, 'G')
    z.put(35, 70, 'P')
    # ---- the hardened aircraft shelter (landmark), door south; the fighter under maintenance and its gear inside
    z.pf('H', 2, 2)
    IN.block(11, 11, 10, 16, 'M')
    IN.block(7, 10, 2, 2, 'g')
    IN.puts([(7, 19), (24, 9)], 'b')
    IN.puts([(24, 21), (6, 25)], 'f')
    IN.put(24, 15, 't')
    IN.puts([(15, 28), (16, 28)], 'c')
    # ---- the maintenance hangar, doors south: the tool crib and benches along the back, racks and the lathe on the
    # west wall, the engine on its dolly, tyres, chests, a GPU on the floor
    z.pf('N', 2, 41)
    IN.block(4, 42, 8, 5, 'z')
    IN.block(13, 42, 3, 1, 'q')
    IN.block(17, 42, 3, 1, 'q')
    IN.block(21, 42, 4, 1, '1')
    IN.block(25, 42, 4, 1, '2')
    IN.block(3, 49, 1, 4, '1')
    IN.block(3, 54, 1, 4, '2')
    IN.block(3, 59, 1, 3, '3')
    IN.put(28, 49, '4')
    IN.block(14, 50, 2, 4, '5')
    IN.puts([(8, 51), (21, 55)], 't')
    IN.puts([(19, 47), (27, 57)], 'b')
    IN.block(23, 50, 2, 2, 'g')
    IN.put(9, 57, 'f')
    # ---- the barracks (gallery south) round its yard: picnic tables, the flagpole, sandbags, a jeep
    z.pf('Y', 44, 4)
    z.pf('p', 50, 18)
    z.pf('p', 58, 18)
    z.put(56, 22, '|')
    z.pf('J', 66, 16)
    z.run(44, 23, 6, '=')
    z.puts([(63, 22), (64, 22)], 'k')
    # ---- the engine test stand (intake west, exhaust into its deflector on the east wall)
    z.pf('Z', 57, 28)
    z.put(55, 27, 'L')
    z.puts([(55, 36), (56, 36)], 'd')
    # ---- the central road: the supply dump under its camouflage net, a generator, sandbag positions, light masts
    z.pf('&', 38, 30)
    z.pf('y', 42, 30)
    z.puts([(37, 31), (37, 32)], 'k')
    z.run(30, 38, 5, '=')
    z.run(41, 45, 5, '=')
    z.put(32, 14, 'L')
    z.put(39, 56, 'L')
    z.puts([(31, 24), (31, 25)], 'd')
    z.pf('$', 41, 18)
    # ---- the ordnance igloo (door west) with munitions trailers, the forklift, crates
    z.pf('D', 54, 50)
    z.pf('O', 49, 52)
    z.pf('O', 46, 56)
    z.pf('8', 50, 60)
    z.puts([(48, 64), (49, 64), (48, 65)], 'k')
    z.run(52, 66, 10, '=')
    z.pf('U', 44, 50)
    # ---- the apron at the south: fighters are not here; a tug, a GPU, the fire point, tyres
    z.pf('U', 22, 66)
    z.put(28, 69, 'f')
    z.put(12, 68, 't')
    z.pf('$', 6, 66)
    z.put(64, 70, 'b')
    # ---- spawn cans and pickups
    for (c, r) in ((35, 8), (36, 20), (52, 30), (45, 38), (34, 44), (66, 44), (50, 44), (60, 70), (12, 36), (24, 36),
                   (66, 39), (8, 70)):
        z.put(c, r, 'S')
    z.puts([(40, 27), (61, 68)], 'a')
    z.put(30, 50, 'a')
    z.puts([(48, 16), (15, 34)], 'h')
    return z


def checks(z):
    errs = []
    for (y, L) in z.L:
        for ch, (w, d) in PREFAB.items():
            for (c, r, bw, bh) in rects(L.g, ch):
                if not ((bw % w == 0 and bh % d == 0) or (bw % d == 0 and bh % w == 0)):
                    errs.append('layer %g prefab %r block %dx%d at (%d,%d)' % (y, ch, bw, bh, c, r))
    return errs


def main():
    out = []
    for z, size in ((zone1(), ((76, 76), (78, 78))), (zone2(), ((72, 72), (74, 74)))):
        errs, stats = validate(z, set('lisu'), PREFAB, size=size)
        errs += checks(z)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
