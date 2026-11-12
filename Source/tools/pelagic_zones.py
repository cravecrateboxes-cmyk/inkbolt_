#!/usr/bin/env python3
"""INKBOLT Pelagic Airbase zones (theme 'pelagic'): hand-placed layouts -> src/data/zones/pelagic_*.txt

    python3 tools/pelagic_zones.py           # write + validate
    python3 tools/pelagic_zones.py --check   # validate only
    python3 tools/pelagic_zones.py --print   # also print the maps

A made-up offshore military air platform far out at sea. Player travel is north.
Zone 1, the flight deck (78 x 76): the runway runs the length of the platform on its east side (cols 52-75; the
theme paints its markings, and it runs on north past the zone); the deck edges (cols 0 and 77) have railings and
safety nets over the sea; the flight-operations block closes the south (the entry gate is its door; the runway
threshold has a blast fence behind it); the north wall is a blast fence with the exit gate and, across the runway,
the emergency barricade net. The spawn is beside the light aircraft with its open canopy and boarding stair. The
island control tower (landmark, gallery at 3.6 m) stands between the apron and the runway; the helicopter dock
(2.4 m, two stairs) on the north-west deck edge; fighters on the flight line, an engine run-up spot and a fighter
lined up on the runway, each with its raised blast deflector; ordnance staging, deck tractors, the crash tender,
arresting wires across the runway.
Zone 2, the hangar deck (64 x 76): the inner platform module, 12 m wider to the west. Hangar 1 and Hangar 2 (24 x 20,
doors open south) each hold a fighter under maintenance and a mezzanine at 3.0 m along the back wall (a stair up);
the approach-control tower (landmark, balcony at 3.6 m) by the runway fence; two cargo lifts with cargo, the fuel
farm (three tanks in a bund) and its fuel lines to the fuel points, a container yard, a fighter being towed out.
Each zone file is the floor plan followed by its layers:
  zone 1: @layer 2.4 helicopter dock deck, @layer 2.4 pad markings, @layer 2.4 rails and the helicopter
  zone 2: @layer 0 inside the hangars, @layer 3.0 mezzanine decks, @layer 3.0 mezzanine rails, @layer 2.59 stacked
          containers, @layer 0.012 cargo on the lifts
Symbols: src/data/themes/pelagic.js.
"""
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {'I': (10, 20), 'L': (10, 10), 'J': (12, 16), 'j': (12, 16), 'K': (8, 16), 'k': (8, 16), 'D': (8, 2),
          'T': (2, 4), '3': (2, 4), 'O': (2, 3), 'Z': (2, 3), 'F': (3, 7), 'u': (2, 6), 'U': (6, 2), 'q': (2, 2),
          'A': (24, 20), 'B': (24, 20), 'W': (8, 12), 'C': (7, 7), 'X': (3, 6), 'V': (3, 8), 'y': (2, 2),
          'M': (12, 16), 'N': (2, 5), 's': (2, 3), 'H': (3, 2), 'z': (2, 1), 'Q': (3, 1), 'i': (2, 8),
          'Y': (8, 14), '@': (16, 16)}
FLOOR = '.'
RWY = (52, 76)        # zone 1 runway columns [52, 76)


class PZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, i):
        return self.L[i][1]

    def pf(self, ch, c, r, n=1, dc=0, dr=0, over=FLOOR, g=None):
        """n prefabs of symbol ch, the first at (c, r), each next one moved by (dc, dr)"""
        w, d = PREFAB[ch]
        g = g or self
        for k in range(n):
            g.block(c + k * dc, r + k * dr, w, d, ch, over=over)

    def pfr(self, ch, c, r, over=FLOOR, g=None):
        """one prefab of ch turned a quarter (footprint d x w)"""
        w, d = PREFAB[ch]
        (g or self).block(c, r, d, w, ch, over=over)

    def text(self):
        out = Zone.text(self)
        for (y, L) in self.L:
            out += '@layer %s\n' % ('%g' % y) + L.text()
        return out


def ring(z, c0, r0, c1, r1):
    """walls on the zone's outer ring"""
    z.rect(c0, r0, c1 - c0 + 1, 1, '#')
    z.rect(c0, r1, c1 - c0 + 1, 1, '#')
    z.rect(c0, r0, 1, r1 - r0 + 1, '#')
    z.rect(c1, r0, 1, r1 - r0 + 1, '#')


def rails_round(deck, up, ch, gaps, walls=()):
    """rails 'r' on every edge cell of deck symbol ch (grid deck) with an outside neighbour that is not deck,
    except the gap cells (stair tops) and sides whose outside neighbour is in `walls` (a hangar wall stands there)"""
    for r in range(deck.h):
        for c in range(deck.w):
            if deck.g[r][c] != ch or (c, r) in gaps:
                continue
            need = False
            for dc, dr in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                if deck.at(c + dc, r + dr) == ch or (c + dc, r + dr) in walls:
                    continue
                need = True
            if need:
                assert up.g[r][c] in '.r', (deck.name, 'rail cell taken', c, r, up.g[r][c])
                up.g[r][c] = 'r'


# ================================================================ zone 1: the flight deck
def zone1():
    W, H = 78, 76
    z = PZone('pelagic_1', W, H, [2.4, 2.4, 2.4])
    DK, PAD, UP = [z.layer(i) for i in range(3)]
    ring(z, 0, 0, W - 1, H - 1)
    z.rect(23, H - 1, 3, 1, 'E')     # the flight-operations block's door
    z.rect(24, 0, 3, 1, 'G')         # the gate in the north blast fence (to the hangar deck)
    z.put(24, 72, 'P')
    # ---- spawn: the light aircraft (nose north, its boarding stair on the east side toward the player)
    z.pf('L', 12, 62)
    z.puts([(16, 61), (17, 61)], 'c')
    z.pf('T', 6, 66)                  # a tractor by the ops block
    z.puts([(2, 72), (3, 72), (2, 70)], 'o')
    z.puts([(30, 73), (31, 73)], 'o')
    z.put(4, 73, 'f')
    z.put(36, 73, 'f')
    z.put(33, 72, 'g')
    z.pf('q', 9, 70)                  # ground power unit by the plane's nose... and its cart
    # ---- the runway: a fighter lined up for take-off (nose north) with the raised blast deflector behind it,
    # arresting wires across the landing area in the north, wire sheaves at the edges
    z.pf('j', 58, 49)
    z.pf('D', 60, 65)
    z.puts([(57, 52), (70, 52)], 'c')
    for r in (8, 14, 20, 26):
        z.put(RWY[0], r, 'x')
        z.put(RWY[1] - 1, r, 'x')
        z.run(RWY[0] + 1, r, RWY[1] - RWY[0] - 2, 'w')
    # cover on the runway and its shoulders: a stalled tractor with a missile cart, dropped pallets, a GPU
    z.pf('T', 60, 31)
    z.pf('Z', 60, 35)
    z.puts([(68, 40), (69, 40), (68, 41)], 'o')
    z.pf('q', 55, 17)
    z.puts([(71, 11), (72, 11)], 'n')
    z.pf('O', 66, 22)
    z.put(76, 60, 'l')
    z.put(76, 34, 'l')
    z.put(76, 6, 'l')
    # ---- the island control tower (landmark) between the apron and the runway, the crash tender by it
    z.pf('I', 41, 24)
    z.pf('F', 44, 47)
    z.puts([(40, 45), (49, 45)], 'l')
    z.puts([(48, 47), (48, 48)], 'e')
    z.put(39, 30, 'b')
    z.put(39, 31, 'b')
    z.put(39, 40, 'g')
    # ---- the helicopter dock (2.4 m deck) on the north-west deck edge, its posts, two stairs, stores under it
    for r in range(2, 18):
        for c in range(1, 17):
            DK.g[r][c] = '='
    PAD.block(1, 2, 16, 16, '@')
    z.pf('U', 17, 9)                  # stair from the east, rising west to the deck's east edge
    z.pf('u', 7, 18)                  # stair from the south, rising north to the deck's south edge
    for (c, r) in ((3, 4), (9, 4), (15, 4), (3, 10), (15, 10), (3, 16), (11, 16), (15, 16)):
        z.put(c, r, 'p')
    z.puts([(1, 6), (1, 7), (2, 6)], 'g')
    z.puts([(6, 12), (7, 12)], 'd')
    z.pf('q', 11, 8)
    z.puts([(6, 6), (6, 7)], 'n')
    rails_round(DK, UP, '=', gaps={(7, 17), (8, 17), (16, 9), (16, 10)})
    UP.block(5, 3, 8, 14, 'Y', over='.r')
    # ---- the flight line: two fighters, wings folded, noses south, chocks and tractors in front of them
    z.pf('K', 30, 2)
    z.pf('K', 40, 2)
    z.puts([(33, 19), (36, 19), (43, 19), (46, 19)], 'c')
    z.pfr('T', 31, 20)
    z.pf('3', 44, 20)                 # a tractor with its tow bar toward the fighter
    z.put(39, 10, 'b')
    z.put(49, 8, 'e')
    z.put(28, 12, 'f')
    # ---- engine run-up spot on the west apron: a fighter (wings folded, nose north) and its blast deflector
    z.pf('k', 4, 27)
    z.pf('D', 4, 43)
    z.puts([(3, 30), (12, 30)], 'c')
    z.pf('q', 13, 38)
    z.put(1, 45, 'l')
    # ---- ordnance staging between the run-up spot and the island: carts in rows with lanes between them
    for (c, r) in ((20, 30), (24, 30), (28, 30), (20, 38), (28, 38)):
        z.pf('O', c, r)
    for (c, r) in ((32, 30), (24, 38), (32, 38)):
        z.pf('Z', c, r)
    z.pf('T', 36, 33)
    z.puts([(23, 35), (31, 35), (27, 43), (35, 43)], 'n')
    z.put(18, 34, 'l')
    # ---- the south-west apron: a fighter parked with wings spread, a tractor, gear
    z.pf('J', 26, 48)
    z.puts([(31, 64), (32, 64)], 'c')
    z.pf('T', 20, 50)
    z.put(14, 50, 'd')
    z.put(14, 51, 'd')
    z.put(40, 58, 'b')
    z.put(41, 58, 'g')
    z.put(8, 56, 'f')
    z.pf('O', 46, 60)
    z.puts([(4, 58), (5, 58), (4, 59)], 'n')
    z.pf('q', 42, 66)
    z.puts([(44, 69), (45, 69)], 'n')
    z.put(50, 73, 'l')
    # ---- spawn cans and pickups
    for (c, r) in ((9, 52), (19, 45), (33, 25), (25, 22), (52 - 3, 14), (58, 44), (70, 47), (63, 4), (70, 28),
                   (14, 24), (40, 52), (64, 16)):
        z.put(c, r, 'S')
    z.puts([(36, 66), (66, 30)], 'a')
    z.put(18, 26, 'a')
    z.puts([(47, 70), (56, 12)], 'h')
    z.put(14, 34, 'h')
    return z


# ================================================================ zone 2: the hangar deck
def zone2():
    W, H = 64, 76
    z = PZone('pelagic_2', W, H, [0.0, 3.0, 3.0, 2.59, 0.012])
    IN, MZ, MR, TOP, LIFT = [z.layer(i) for i in range(5)]
    ring(z, 0, 0, W - 1, H - 1)
    z.rect(36, H - 1, 3, 1, 'E')
    z.rect(30, 0, 3, 1, 'G')
    z.put(37, 72, 'P')
    # ---- the hangars (doors open south)
    z.pf('A', 2, 3)
    z.pf('B', 38, 3)
    # hangar 1: the fighter under maintenance (nose to the door), the engine on its stand, the hoist over a work
    # stand, the mezzanine along the back wall (west part) with its stair, posts, bench and shelving under it
    IN.block(12, 6, 12, 16, 'M')
    IN.block(4, 13, 2, 5, 'N')
    IN.block(7, 16, 2, 3, 's')
    IN.block(3, 19, 3, 2, 'H')
    IN.block(9, 7, 2, 8, 'i')
    IN.put(6, 10, 'b')
    IN.put(6, 21, 'b')
    IN.block(3, 4, 2, 1, 'z')
    IN.block(5, 4, 3, 1, 'Q')
    IN.puts([(4, 6), (8, 6)], '!')
    IN.put(24, 8, 'e')
    IN.block(8, 20, 2, 2, 'q')
    for r in range(3, 7):
        for c in range(2, 12):
            MZ.g[r][c] = 'm'
    # hangar 2: mirrored (mezzanine on the east part)
    IN.block(40, 6, 12, 16, 'M')
    IN.block(58, 13, 2, 5, 'N')
    IN.block(55, 16, 2, 3, 's')
    IN.block(58, 19, 3, 2, 'H')
    IN.block(53, 7, 2, 8, 'i')
    IN.put(57, 10, 'b')
    IN.put(57, 21, 'b')
    IN.block(59, 4, 2, 1, 'z')
    IN.block(56, 4, 3, 1, 'Q')
    IN.puts([(55, 6), (59, 6)], '!')
    IN.put(39, 8, 'e')
    IN.block(54, 20, 2, 2, 'q')
    for r in range(3, 7):
        for c in range(52, 62):
            MZ.g[r][c] = 'm'
    rails_round(MZ, MR, 'm', gaps={(9, 6), (10, 6), (53, 6), (54, 6)},
                walls={(1, r) for r in range(3, 7)} | {(c, 2) for c in range(2, 12)} | {(62, r) for r in range(3, 7)} | {(c, 2) for c in range(52, 62)})
    # ---- between the hangars (the passage to the exit gate): fuel points, a tool chest, the floodlights
    z.pf('y', 26, 18)
    z.pf('y', 36, 18)
    z.puts([(27, 3), (36, 3)], 'l')
    z.put(26, 10, 'b')
    z.put(37, 12, 'e')
    # ---- in front of the hangars: a fighter being towed out of hangar 2 (nose south, tractor ahead of it)
    z.pf('K', 44, 25)
    z.pf('3', 47, 41)
    z.puts([(43, 30), (52, 30)], 'c')
    z.pf('O', 54, 26)
    z.pf('Z', 57, 26)
    # in front of hangar 1: a missile cart, a GPU and the tool gear
    z.pf('Z', 14, 25)
    z.pf('q', 19, 26)
    z.puts([(10, 26), (11, 26)], 'n')
    z.put(23, 27, 'g')
    # ---- the fuel farm (west): three tanks in a bund, the fuel line to the fuel points between the hangars
    for c in range(1, 17):
        z.put(c, 30, '-')
        z.put(c, 41, '-')
    for r in range(31, 41):
        z.put(1, r, '-')
        if r not in (35, 36, 37):       # the fuel line passes the bund here; a gap beside it to walk in
            z.put(16, r, '-')
    for c in (3, 7, 11):
        z.pf('V', c, 32)
    for c in range(14, 31):
        z.put(c, 35, '~')
    for r in range(20, 35):
        z.put(30, r, '~')
    for c in range(28, 30):
        z.put(c, 20, '~')
    for c in range(31, 36):
        z.put(c, 20, '~')
    z.put(18, 37, 'f')
    z.put(18, 38, 'e')
    # ---- the approach-control tower (landmark) by the runway fence
    z.pf('W', 53, 46)
    z.puts([(51, 47), (51, 48)], 'g')
    z.put(61, 60, 'l')
    # ---- the cargo lifts (south-west) with cargo on them, the container yard (centre), more gear
    z.pf('C', 3, 52)
    z.pf('C', 12, 52)
    LIFT.block(5, 52, 3, 6, 'X')
    LIFT.puts([(13, 53), (14, 53), (13, 54), (17, 56), (17, 57)], 'o')
    LIFT.puts([(16, 53), (16, 54)], 'n')
    z.put(11, 62, 'l')
    for (c, r) in ((24, 46), (32, 46)):
        z.pf('X', c, r)
    z.pfr('X', 24, 56)
    z.pfr('X', 34, 58)
    TOP.block(24, 46, 3, 6, 'X')
    z.puts([(28, 49), (29, 49), (28, 50)], 'o')
    z.pf('T', 40, 52)
    # the south-east apron: a second ordnance staging row, the hangar deck's crash tender by the tower
    for (ch, c) in (('O', 41), ('O', 45), ('Z', 49)):
        z.pf(ch, c, 62)
    z.pf('F', 56, 61)
    z.puts([(52, 66), (53, 66)], 'n')
    z.put(6, 66, 'f')
    z.puts([(2, 70), (3, 70), (2, 69)], 'o')
    z.pf('k', 14, 59)
    z.puts([(13, 61), (22, 61)], 'c')
    z.put(58, 70, 'b')
    z.put(26, 70, 'e')
    # ---- spawn cans and pickups
    for (c, r) in ((32, 26), (20, 44), (40, 44), (58, 42), (8, 46), (26, 60), (55, 34), (28, 38), (60, 66),
                   (50, 59), (12, 72), (24, 66)):
        z.put(c, r, 'S')
    z.puts([(26, 31), (56, 38)], 'a')
    z.put(4, 46, 'a')
    z.puts([(22, 38), (50, 70)], 'h')
    return z


def checks(z):
    """extra checks: prefabs in the layers tile their footprints"""
    errs = []
    for (y, L) in z.L:
        for ch, (w, d) in PREFAB.items():
            for (c, r, bw, bh) in rects(L.g, ch):
                if not ((bw % w == 0 and bh % d == 0) or (bw % d == 0 and bh % w == 0)):
                    errs.append('layer %g prefab %r block %dx%d at (%d,%d)' % (y, ch, bw, bh, c, r))
    return errs


def main():
    out = []
    for z, size in ((zone1(), ((78, 78), (76, 76))), (zone2(), ((64, 64), (76, 76)))):
        errs, stats = validate(z, set('wx~'), PREFAB, size=size)
        errs += checks(z)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
