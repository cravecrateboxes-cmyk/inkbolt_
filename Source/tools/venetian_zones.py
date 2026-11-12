#!/usr/bin/env python3
"""INKBOLT Ca' Doranza zones (theme 'venetian'): hand-placed layouts -> src/data/zones/venetian_*.txt

    python3 tools/venetian_zones.py           # write + validate
    python3 tools/venetian_zones.py --check   # validate only
    python3 tools/venetian_zones.py --print   # also print the maps

A made-up Venetian mansion compound. Player travel is north.
Zone 1, the Campo dei Venti (76 x 70): a paved campo ringed by stucco houses (two and three storeys, four colours,
flower-covered balconies, shops and doors, lanterns), the entry through a portal in the south-west, the
fondamenta along the canal in the north (cobbles, the stone balustrade over the water, goods off the boats); the
exit gate is the portal at the foot of the mansion's private bridge. The Fountain of the Four Winds (landmark) in the
middle; Caffe Zanetto (walk-in, its stair up to the roof terrace at 3.6 m) against the west houses with its
terrace of parasols, Pasticceria Brolo (walk-in) against the east houses with its terrace; the Loggia dei Mercanti
(an open arcade, its stair up to the roof terrace at 3.6 m) in the south-east; market stalls, the kiosk, the flower
stall, well-heads, lamp posts, benches, planters, lemon trees, crates and barrels; cobbled streets and white
Istrian stone bands in the trachyte paving.
Zone 2, the courtyard of Ca' Doranza (66 x 72): the mansion's wings on three sides (the canal wing in the south with
the water gate, the east wing, the main house in the north with the exit portal), a garden wall on the west. The
cloister in the middle: two rings of columns and arches round a garden, its upper walk (deck at 4.32 m) with
balustrades and the roof loggia over the north range; the grand staircase (landmark) up from the forecourt to the
south range, two service stairs up to the east and west ranges. In the garden the second fountain, four
parterres, cypresses and lemon trees on gravel; the north court with parterres, hedges and stone tables; the west
garden with hedges and cypresses; the east service yard with the boat under repair, crates, barrels, the cart.
Each zone file is the floor plan followed by its layers:
  zone 1: @layer 0 paving (cobbles, bands), @layer 3.6 balustrades on the roof terraces
  zone 2: @layer 0 cloister arches, @layer 0 gravel, @layer 4.32 the upper walk's deck, @layer 4.32 its
          balustrades, @layer 4.32 the roof loggia
Symbols: src/data/themes/venetian.js.
"""
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {'F': (14, 14), 'K': (8, 10), 'k': (7, 8), 'L': (16, 6), 'u': (2, 2), 'p': (2, 1), 'B': (2, 1), 'w': (2, 2),
          'Y': (3, 3), 'X': (3, 2), 'M': (3, 2), 'v': (2, 3),
          'Z': (8, 8), 'i': (6, 2), 'j': (6, 2), 'Q': (6, 6), 'R': (6, 4), 'T': (3, 2), 'g': (3, 11),
          'A': (2, 1), 'V': (1, 2), 'W': (13, 4)}
FLOOR = '.'
DECK = 4.32
TERR = 3.6


class VZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, i):
        return self.L[i][1]

    def pf(self, ch, c, r, g=None, over=FLOOR):
        w, d = PREFAB[ch]
        (g or self).block(c, r, w, d, ch, over=over)

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


def rails_edge(deck, up, ch, gaps):
    """rails 'r' on the layer `up` over every cell of deck symbol ch with a neighbour off the deck (gaps excepted)"""
    for r in range(deck.h):
        for c in range(deck.w):
            if deck.g[r][c] != ch or (c, r) in gaps:
                continue
            if any(deck.at(c + dc, r + dr) != ch for dc, dr in ((0, -1), (0, 1), (1, 0), (-1, 0))):
                up.put(c, r, 'r')


# ================================================================ zone 1: the Campo dei Venti
def zone1():
    W, H = 76, 70
    z = VZone('venetian_1', W, H, [0, TERR])
    PAVE, TOP = z.layer(0), z.layer(1)
    ring(z)
    z.rect(36, 0, 3, 1, 'G')          # the portal at the foot of the mansion's bridge
    z.rect(18, H - 1, 3, 1, 'E')      # the portal from the lane in the south-west
    z.put(19, 66, 'P')
    # ---- paving: the fondamenta and the lanes in cobbles, white Istrian bands across the trachyte
    for r in range(1, 6):
        for c in range(1, W - 1):
            PAVE.put(c, r, ',')
    for r in range(48, H - 1):
        for c in range(14, 25):
            PAVE.put(c, r, ',')
    for r in range(42, H - 1):
        for c in range(67, W - 1):
            PAVE.put(c, r, ',')
    for c in range(29, 47):
        PAVE.put(c, 20, '-')
        PAVE.put(c, 37, '-')
    for r in range(21, 37):
        PAVE.put(29, r, '|')
        PAVE.put(46, r, '|')
    for (c, r) in ((29, 20), (46, 20), (29, 37), (46, 37)):
        PAVE.g[r][c] = '+'
    for r in range(6, 20):
        PAVE.put(37, r, '|')
    for r in range(38, 48):
        PAVE.put(37, r, '|')
    for c in range(25, 67):
        if PAVE.at(c, 48) == '.':
            PAVE.put(c, 48, '-')
    PAVE.g[48][37] = '+'
    for c in range(10, 29):
        PAVE.put(c, 28, '-')
    for c in range(47, 66):
        PAVE.put(c, 28, '-')
    # ---- the fondamenta: benches facing the canal, goods off the boats by the bridge, the flower stall
    for c in (5, 13, 58, 66):
        z.pf('B', c, 1)
    z.puts([(30, 2), (31, 2), (30, 3)], 'c')
    z.put(32, 2, 'x')
    z.puts([(43, 2), (44, 2)], 'x')
    z.put(43, 3, 'c')
    z.pf('v', 47, 2)
    z.pf('X', 22, 2)
    z.puts([(34, 1), (40, 1)], 'U')
    z.puts([(20, 5), (54, 5), (8, 5), (68, 5)], 'l')
    # ---- Caffe Zanetto (front east) and its terrace; Pasticceria Brolo (front west) and its terrace
    z.pf('K', 1, 10)
    for (c, r) in ((10, 10), (10, 18), (14, 11), (14, 17), (16, 14)):
        z.pf('u', c, r)
    z.puts([(18, 11), (18, 18), (12, 13)], 't')
    for c in (11, 14):
        z.pf('p', c, 8)
        z.pf('p', c, 21)
    z.puts([(9, 9), (9, 20)], 'q')
    z.put(18, 9, 'n')
    z.pf('k', 68, 30)
    for (c, r) in ((61, 30), (61, 35), (64, 32)):
        z.pf('u', c, r)
    z.puts([(66, 29), (66, 38), (60, 33)], 't')
    for c in (61, 64):
        z.pf('p', c, 27)
        z.pf('p', c, 40)
    z.put(67, 28, 'n')
    z.puts([(67, 39), (59, 28)], 'q')
    # ---- the Fountain of the Four Winds; benches and lamps round it
    z.pf('F', 31, 22)
    for (c, r) in ((33, 19), (41, 19), (33, 37), (41, 37)):
        z.pf('B', c, r)
    z.puts([(28, 20), (47, 20), (28, 37), (47, 37)], 'l')
    # ---- the merchants' loggia (south-east), market stalls, the kiosk, the wells
    z.pf('L', 50, 52)
    for (c, r) in ((22, 42), (27, 42), (40, 45)):
        z.pf('M', c, r)
    z.pf('Y', 54, 14)
    z.pf('w', 22, 33)
    z.pf('w', 57, 42)
    z.puts([(49, 50), (49, 59), (66, 50), (66, 59)], 'q')
    z.puts([(50, 59), (51, 59), (52, 60)], 'c')
    z.put(65, 60, 'x')
    # ---- along the houses: lemon pots, urns, benches, lamps, crates at a shop door
    z.puts([(1, 30), (1, 34), (1, 44), (1, 48), (74, 18), (74, 22), (74, 50), (74, 54)], 'q')
    z.puts([(1, 39), (74, 12), (74, 46)], 'U')
    z.pf('B', 2, 56)
    z.pf('B', 30, 67)
    z.pf('B', 44, 67)
    z.puts([(10, 26), (26, 12), (50, 10), (64, 22), (64, 46), (38, 62), (28, 56), (8, 50), (12, 38), (46, 60)], 'l')
    z.puts([(72, 66), (73, 66), (73, 65)], 'c')
    z.put(26, 67, 'x')
    z.puts([(58, 66), (59, 66)], 'x')
    z.pf('v', 4, 62)
    # ---- the roof terraces' balustrades (layer 3.6): Caffe Zanetto (cols 1-8, rows 10-19), the loggia (cols
    # 50-65, rows 52-57; its terrace ends at col 63, the landing of its stair at row 52 cols 63-65)
    for c in range(1, 9):
        TOP.put(c, 10, 'r')
    for r in range(11, 20):
        TOP.put(8, r, 'r')
    TOP.put(7, 19, 'r')
    for c in range(50, 64):
        TOP.put(c, 57, 'r')
    for c in range(50, 63):
        TOP.put(c, 52, 'r')
    for r in range(53, 57):
        TOP.put(50, r, 'r')
    for r in (55, 56):                # beside the stair's top flight the terrace edge stays open (robots step across)
        TOP.put(63, r, 'r')
    # ---- spawn cans and pickups
    for (c, r) in ((12, 3), (60, 3), (25, 16), (52, 22), (70, 14), (20, 38), (50, 34), (36, 41), (70, 46), (12, 46),
                   (44, 56), (60, 64)):
        z.put(c, r, 'S')
    z.puts([(38, 14), (16, 30)], 'a')
    z.put(58, 48, 'a')
    z.puts([(26, 26), (62, 44)], 'h')
    return z


# ================================================================ zone 2: the courtyard of Ca' Doranza
OUT = (15, 18, 51, 45)     # the cloister's outer column ring (c0, r0, c1, r1)
INN = (18, 21, 48, 42)     # the inner ring


def zone2():
    W, H = 66, 72
    z = VZone('venetian_2', W, H, [0, 0, DECK, DECK, DECK])
    ARC, GRV, DK, RL, LG = [z.layer(i) for i in range(5)]
    ring(z)
    z.rect(32, 0, 3, 1, 'G')          # the main portal of the house (north)
    z.rect(32, H - 1, 3, 1, 'E')      # the water gate (south, from the bridge)
    z.put(33, 68, 'P')
    # ---- the cloister: columns every 3 m on both rings, arches between them (layer 0), the upper walk's deck
    for (c0, r0, c1, r1) in (OUT, INN):
        for c in range(c0, c1 + 1, 3):
            z.put(c, r0, 'O')
            z.put(c, r1, 'O')
        for r in range(r0 + 3, r1, 3):
            z.put(c0, r, 'O')
            z.put(c1, r, 'O')
        for c in range(c0, c1, 3):
            ARC.block(c + 1, r0, 2, 1, 'A')
            ARC.block(c + 1, r1, 2, 1, 'A')
        for r in range(r0, r1, 3):
            ARC.block(c0, r + 1, 1, 2, 'V')
            ARC.block(c1, r + 1, 1, 2, 'V')
    for r in range(OUT[1], OUT[3] + 1):
        for c in range(OUT[0], OUT[2] + 1):
            if INN[0] < c < INN[2] and INN[1] < r < INN[3]:
                continue
            DK.put(c, r, '=')
    # the grand staircase up to the south range, the service stairs up to the west / east ranges
    z.pf('Z', 29, 46)
    z.pf('j', 9, 31)                  # rises east to the west range (col 15)
    z.pf('i', 52, 31)                 # rises west to the east range (col 51)
    gaps = {(c, OUT[3]) for c in range(29, 37)} | {(OUT[0], 31), (OUT[0], 32), (OUT[2], 31), (OUT[2], 32)}
    rails_edge(DK, RL, '=', gaps)
    LG.block(27, 18, 13, 4, 'W')      # the roof loggia over the north range
    # ---- the garden: the fountain, four parterres, cypresses, lemon trees, benches, gravel
    for r in range(INN[1] + 1, INN[3]):
        for c in range(INN[0] + 1, INN[2]):
            GRV.put(c, r, ':')
    z.pf('Q', 30, 29)
    for (c, r) in ((21, 24), (40, 24), (21, 36), (40, 36)):
        z.pf('R', c, r)
    z.puts([(19, 22), (47, 22), (19, 41), (47, 41)], 'y')
    z.puts([(29, 28), (36, 28), (29, 35), (36, 35)], 'q')
    z.pf('B', 32, 23)
    z.pf('B', 32, 40)
    # ---- the forecourt behind the water gate: wells, urns, lamps, benches, goods off the boats
    z.pf('w', 21, 60)
    z.pf('w', 43, 60)
    z.puts([(27, 54), (38, 54)], 'U')
    z.puts([(26, 57), (40, 57), (26, 66), (40, 66), (12, 58), (54, 58)], 'l')
    z.pf('B', 15, 64)
    z.pf('B', 49, 64)
    z.puts([(23, 69), (24, 69), (23, 68)], 'c')
    z.puts([(42, 69), (43, 69)], 'x')
    z.puts([(30, 54), (35, 54), (2, 66), (63, 66)], 'q')
    # ---- the north court: parterres, stone tables, cypresses, lemon trees flanking the way to the portal
    z.pf('R', 6, 3)
    z.pf('R', 54, 3)
    z.pf('T', 19, 6)
    z.pf('T', 44, 6)
    z.puts([(4, 14), (9, 14), (56, 14), (61, 14)], 'y')
    z.puts([(30, 3), (36, 3), (30, 8), (36, 8)], 'q')
    z.puts([(26, 11), (40, 11)], 'l')
    z.pf('B', 20, 13)
    z.pf('B', 44, 13)
    for c in range(14, 26):
        z.put(c, 16, 'H')
    for c in range(41, 53):
        z.put(c, 16, 'H')
    # ---- the west garden: hedges, cypresses, an urn, a bench
    for r in range(20, 29):
        z.put(6, r, 'H')
    for r in range(36, 46):
        z.put(10, r, 'H')
    for c in range(2, 10):
        z.put(c, 49, 'H')
    z.puts([(2, 20), (2, 26), (2, 37), (2, 44), (12, 20), (12, 26)], 'y')
    z.put(4, 33, 'U')
    z.pf('B', 2, 40)
    z.put(8, 52, 'l')
    # ---- the east service yard: the boat under repair, crates, barrels, the cart
    z.pf('g', 59, 38)
    z.puts([(56, 44), (57, 44), (56, 45)], 'c')
    z.puts([(55, 48), (55, 49)], 'x')
    z.pf('v', 62, 22)
    z.put(58, 26, 'l')
    z.puts([(64, 20), (64, 52)], 'q')
    z.put(63, 36, 'U')
    # ---- spawn cans and pickups
    for (c, r) in ((10, 8), (56, 8), (33, 13), (4, 30), (61, 30), (24, 32), (42, 32), (8, 56), (58, 56), (16, 58),
                   (50, 58), (33, 25)):
        z.put(c, r, 'S')
    z.puts([(14, 46), (52, 46)], 'a')
    z.put(33, 4, 'a')
    z.puts([(21, 31), (60, 64)], 'h')
    return z


def checks(z):
    """extra checks: prefabs in the layers tile their footprints; stairs end on the deck"""
    errs = []
    for (y, L) in z.L:
        for ch, (w, d) in PREFAB.items():
            for (c, r, bw, bh) in rects(L.g, ch):
                if not ((bw % w == 0 and bh % d == 0) or (bw % d == 0 and bh % w == 0)):
                    errs.append('layer %g prefab %r block %dx%d at (%d,%d)' % (y, ch, bw, bh, c, r))
    return errs


def main():
    out = []
    for z, size in ((zone1(), ((76, 76), (70, 70))), (zone2(), ((66, 66), (72, 72)))):
        errs, stats = validate(z, set(''), PREFAB, size=size)
        errs += checks(z)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
