#!/usr/bin/env python3
"""INKBOLT Meridian International zones (theme 'airport'): hand-placed layouts -> src/data/zones/airport_*.txt

    python3 tools/airport_zones.py            # write + validate
    python3 tools/airport_zones.py --print    # ... and print the maps
    python3 tools/airport_zones.py --check    # validate only

Zone 1, the Terminal, is 80 x 78 m (gates at columns 38-40, the player starts at (39, 75) in the check-in hall);
layers: "@layer 0.01" (floor marks, the wall logo), "@layer 0.025" (wall-art codes on wall cells, '¤' at (0, 0); no
symbols), "@layer 4.5" (the mezzanine) and "@layer 14" (ceiling pieces). Zone 2, Hangar 2 and its apron, is 72 x 74 m (gates at columns
34-36, entry at (35, 71)); layers "@layer 0.01" (floor tiles, logos), "@layer 0.02" (marks, the engine on its stand), "@layer 0.025" (art codes, '¦' at (0, 0)), "@layer 2.6" and
"@layer 5.2" (work platforms) and "@layer 14" (roof bays, the door header). Symbols: see src/data/themes/airport.js.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonekit import Zone, rects, validate, write  # noqa: E402

WALK1 = set('enU')
WALK2 = set()
PREFAB = {'j': (4, 1), 'I': (3, 6), 'J': (3, 6), 'K': (3, 6), 'L': (3, 6), 'B': (10, 2), 'i': (4, 2), 'e': (3, 2), 'X': (3, 2), 'W': (2, 2),
          'A': (1, 2), 'U': (3, 1), 'Y': (3, 1), 'r': (4, 1), 'C': (4, 1), 'c': (4, 1), 'Q': (4, 1), 'V': (4, 1), 'g': (3, 1),
          'd': (3, 1), 'H': (3, 1), 'f': (2, 2), 'x': (3, 2), 'z': (2, 2), 'R': (6, 2), 'M': (2, 2), 'm': (2, 2), 'F': (3, 1),
          'T': (4, 1), 'N': (3, 1), 'n': (2, 1), 's': (2, 9), '1': (2, 9), 'D': (2, 4), '+': (2, 2), '=': (2, 3), '~': (3, 7),
          '^': (2, 6), '<': (2, 6), '>': (2, 2), '?': (2, 2), '|': (1, 4), '[': (4, 3), '`': (2, 3), ',': (2, 2), '5': (2, 6)}


class AZone(Zone):
    """floor plan + floor layer (f) + deck layers (d: [(y, Zone)]) + roof (k)"""

    def __init__(self, name, w, h, gc, code, decks):
        Zone.__init__(self, name, w, h)
        self.f = Zone(name + '_f', w, h)
        self.a = Zone(name + '_a', w, h)
        self.mk = Zone(name + '_m', w, h)
        self.decks = [(y, Zone(name + '_d%d' % i, w, h)) for i, y in enumerate(decks)]
        self.k = Zone(name + '_k', w, h)
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(gc, 0, 3, 1, 'G')
        self.rect(gc, h - 1, 3, 1, 'E')
        self.put(gc + 1, h - 3, 'P')
        self.a.g[0][0] = code

    def d(self, i=0):
        return self.decks[i][1]

    def art(self, pts, ch):
        for c, r in pts:
            assert self.at(c, r) == '#', (self.name, c, r, 'art on a non-wall cell', self.at(c, r))
            assert self.a.g[r][c] == '.', (self.name, c, r, 'art twice')
            self.a.g[r][c] = ch

    def mark(self, c0, r0, w, h, ch):
        """floor marks over open floor cells only"""
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if self.at(c, r) in '.P' and self.mk.g[r][c] == '.':
                    self.mk.g[r][c] = ch

    def tiles(self, c0, r0, nw, nh, ch, s=4):
        for j in range(nh):
            for i in range(nw):
                self.f.rect(c0 + i * s, r0 + j * s, s, s, ch)

    def text(self):
        out = Zone.text(self) + '@layer 0.01\n' + self.f.text() + '@layer 0.02\n' + self.mk.text() + '@layer 0.025\n' + self.a.text()
        for y, d in self.decks:
            out += '@layer %g\n' % y + d.text()
        return out + '@layer 14\n' + self.k.text()


def check(z, size, walk):
    errs, stats = validate(z, walk, PREFAB, size=size)
    # doors in a glass line: their two ends against glass / wall
    for (c, r, w, h) in rects(z.g, 'n'):
        for (a, b) in ((c - 1, r), (c + w, r)):
            if z.at(a, b) not in '#q':
                errs.append('door n at (%d,%d) end (%d,%d) is %r' % (c, r, a, b, z.at(a, b)))
    # spawns are never under a deck
    for r in range(z.h):
        for c in range(z.w):
            if z.g[r][c] == 'S' and any(d.g[r][c] != '.' for _, d in z.decks):
                errs.append('spawn under a deck at (%d,%d)' % (c, r))
    return errs, stats


# ================================================================ zone 1: the terminal
def zone1():
    W, H = 80, 78
    z = AZone('airport_1', W, H, 38, '¤', [4.5])
    D = z.d()
    # ---------------- check-in hall (rows 54 - 76)
    for c0, ch in ((6, 'I'), (18, 'J'), (56, 'K'), (68, 'L')):
        z.block(c0, 57, 6, 15, ch)
    z.block(35, 58, 10, 2, 'B')
    z.block(46, 66, 4, 2, 'i')
    for r in (59, 61, 63, 65, 67):
        z.put(14, r, 'k')
        z.put(65, r, 'k')
    # queue lanes beside the islands: belt barriers with gaps
    for c in (4, 13, 16, 25, 54, 63, 66, 75):
        for (r0, n) in ((58, 5), (65, 6)):
            z.run(c, r0, n, 'b', vertical=True)
    for (c, r) in ((2, 73), (3, 74), (2, 75), (76, 73), (77, 75), (29, 72), (50, 72), (12, 74), (67, 74), (31, 56), (48, 56)):
        z.put(c, r, 't')
    for (c, r) in ((29, 63), (50, 63)):
        z.put(c, r, 'O')
    for (c0, r) in ((27, 67), (50, 70), (27, 60), (49, 60)):
        z.block(c0, r, 4, 1, 'j')
    for (c, r) in ((33, 74), (46, 74)):
        z.put(c, r, '3')
    for (c, r) in ((17, 74), (62, 74)):
        z.put(c, r, '4')
    # entrance doors in the south curtain wall, mats inside them
    z.art([(c, H - 1) for c in range(13, 17)] + [(c, H - 1) for c in range(63, 67)], '¢')
    z.mk.block(13, 75, 3, 2, 'µ')
    z.mk.block(64, 75, 3, 2, 'µ')
    # landside walls: the MERIDIAN logo over the west wall, ads, screens, fire points
    z.f.block(0, 60, 1, 10, 'Ð')
    z.art([(0, 56)], '²')
    z.art([(0, 73)], '³')
    z.art([(0, 52)], '¹')
    z.art([(W - 1, 58)], '¼')
    z.art([(W - 1, 71)], '½')
    z.art([(W - 1, 64)], '¾')
    z.art([(W - 1, 52)], '¹')
    # ---------------- security (rows 37 - 53)
    # the queue: belt-barrier runs with gaps
    for (c0, n) in ((8, 8), (19, 9), (32, 6), (42, 6), (52, 9), (64, 8)):
        z.run(c0, 52, n, 'b')
    # the screen line (row 49) with e-gate banks, the central shutter, two half-down shutters at the ends
    EG = (9, 18, 27, 50, 59, 68)
    for c0 in EG:
        z.block(c0, 48, 3, 2, 'e')
    z.block(38, 49, 3, 1, 'U')
    z.block(2, 49, 3, 1, 'Y')
    z.block(75, 49, 3, 1, 'Y')
    for c in range(1, W - 1):
        if z.at(c, 49) == '.':
            z.put(c, 49, 'q')
    # screening lanes: X-ray (2 x 9), body scanner, sensor arch per unit; three units west, three mirrored east
    for k in range(3):
        for (xr, sc, ar) in ((7 + 9 * k, 10 + 9 * k, 12 + 9 * k), (71 - 9 * k, 68 - 9 * k, 67 - 9 * k)):
            z.block(xr, 38, 2, 9, 'X')
            z.block(sc, 42, 2, 2, 'W')
            z.block(ar, 42, 1, 2, 'A')
    for c0 in (6, 15, 24, 49, 58, 67):
        z.k.block(c0, 40, 8, 2, 'Ê')
    for (c, r) in ((36, 44), (43, 44), (34, 40), (45, 40)):
        z.put(c, r, 'p')
    for c in (6, 9, 15, 18, 24, 27, 52, 55, 61, 64, 70, 73) + tuple(range(35, 45, 3)):
        z.put(c, 37, 'o')
    for c in (9, 18, 27, 39, 52, 61, 70):
        z.k.put(c, 45, 'Ü')
    for c in (20, 59):
        z.k.put(c, 52, 'Ü')
    z.tiles(0, 37, 20, 3, 'æ')
    z.art([(0, 45)], '¹')
    z.art([(0, 42)], '×')
    z.art([(W - 1, 45)], '÷')
    z.art([(W - 1, 42)], '×')
    # ---------------- airside (rows 1 - 36)
    # mezzanine deck over the west side (c 1 - 12, rows 2 - 31) with a landing for the escalators (c 13 - 18, rows
    # 14 - 19); escalators rise north to the landing, a stair rises north to the deck's south edge
    D.rect(1, 2, 12, 30, 'u')
    D.rect(13, 14, 6, 6, 'u')
    z.block(13, 20, 2, 9, '1')
    z.block(15, 20, 2, 9, '1')
    z.block(3, 32, 2, 9, 's')
    for r in (3, 7, 11, 23, 27, 31):
        z.put(12, r, 'l')
    for (c, r) in ((18, 14), (18, 19), (12, 14), (12, 19)):
        z.put(c, r, 'l')
    # glass rails on the deck edges (not where the stair and escalators arrive)
    for r in list(range(2, 14)) + list(range(20, 32)):
        D.put(12, r, "'", over='u')
    for c in range(13, 19):
        D.put(c, 14, "'", over='u')
    for r in range(15, 20):
        D.put(18, r, "'", over='u')
    D.put(17, 19, "'", over='u')
    for c in (1, 2, 5, 6, 7, 8, 9, 10, 11):
        D.put(c, 31, "'", over='u')
    # the Skybean cafe against the west wall, its tables, benches facing the hall
    D.block(1, 8, 2, 4, '0', over='u')
    for (c, r) in ((4, 5), (4, 10), (7, 7), (7, 12), (4, 15), (7, 17), (4, 24), (7, 26))[:8]:
        D.block(c, r, 2, 2, 'Z', over='u')
    D.block(10, 20, 1, 4, 'C', over='u')
    D.block(10, 25, 1, 4, 'C', over='u')
    # under the deck: restrooms, a flight screen, seating, chargers
    z.art([(0, 6)], '×')
    z.art([(0, 20)], '×')
    z.art([(0, 14)], '¾')
    z.art([(0, 28)], '÷')
    z.art([(0, 10)], '²')
    z.art([(0, 24)], '¼')
    z.block(5, 4, 1, 4, 'C')
    z.block(5, 9, 1, 4, 'C')
    z.block(5, 16, 1, 4, 'C')
    z.block(5, 22, 1, 4, 'C')
    for (c, r) in ((9, 5), (9, 18), (9, 26)):
        z.put(c, r, 'v')
    # the Skylark lounge (north-east): glass on its west and south sides, the door, bar, buffet, chairs
    for r in range(1, 15):
        z.put(57, r, 'q')
    for c in range(57, W - 1):
        z.put(c, 15, 'q', over='.q')
    z.rect(63, 15, 2, 1, 'n')
    z.block(64, 1, 6, 2, 'R')
    z.block(59, 1, 4, 1, 'T')
    z.block(59, 12, 3, 1, 'N')
    for r0 in (3, 7, 11):
        z.block(75, r0, 2, 2, 'M')
    z.block(71, 4, 1, 3, 'F')
    z.block(71, 9, 1, 3, 'F')
    z.block(65, 6, 2, 2, 'm')
    z.block(68, 6, 2, 2, 'm')
    z.block(65, 10, 2, 2, 'M')
    for (c, r) in ((77, 1), (77, 14)):
        z.put(c, r, '3')
    z.tiles(57, 1, 5, 3, 'ø')
    # gates A1 - A3 along the east glass: seat rows facing the apron (back to back pairs), podiums, the jet-bridge
    # door of A3 (row 35)
    for r0 in (17, 23, 29):
        for (c, ch) in ((61, 'c'), (62, 'C'), (65, 'C'), (68, 'c'), (69, 'C'), (72, 'C')):
            z.block(c, r0, 1, 4, ch)
    for (r0, sg) in ((18, 'Ò'), (24, 'Ó'), (31, 'Ô')):
        z.block(77, r0, 1, 3, 'g')
        z.k.block(74, r0, 1, 2, sg)
    z.art([(W - 1, 35)], '£')
    for (c, r) in ((59, 21), (59, 27), (66, 34), (74, 34)):
        z.put(c, r, 'y')
    for (c, r) in ((66, 22), (66, 28), (59, 33)):
        z.put(c, r, 'v')
    # duty free (c 22 - 53, rows 4 - 23): gondola aisles, perfume islands, the chocolate pyramid, the cash desk,
    # wall shelving along the north wall either side of the gate
    for r in (7, 10, 13, 16):
        for c0 in (24, 28, 45, 49):
            z.block(c0, r, 3, 1, 'd')
    for (c, r) in ((34, 7), (42, 7), (34, 14), (42, 14)):
        z.block(c, r, 2, 2, 'f')
    z.block(38, 11, 2, 2, 'z')
    z.block(37, 20, 3, 2, 'x')
    for c0 in (23, 26, 29, 32, 43, 46, 49):
        z.block(c0, 1, 3, 1, 'H')
    z.tiles(22, 4, 8, 5, 'å')
    z.k.block(34, 24, 8, 1, 'Ù')
    # the concourse (rows 25 - 36): seat clusters back to back, tree columns, flight screens, repack benches
    for c0 in (20, 27, 46, 53):
        z.block(c0, 29, 4, 1, 'V')
        z.block(c0, 30, 4, 1, 'Q')
    for (c, r) in ((25, 26), (54, 26), (32, 33), (47, 33)):
        z.put(c, r, 'O')
    for (c, r) in ((36, 31), (43, 31)):
        z.put(c, r, 'y')
    for c0 in (6, 15, 24, 52, 61, 70):
        z.block(c0, 35, 4, 1, 'r')
    for (c, r) in ((18, 27), (59, 9)):
        z.put(c, r, '4')
    # airside walls: ads and a fire point on the north wall, wayfinding on the security walls
    z.art([(10, 0)], '³')
    z.art([(30, 0)], '½')
    z.art([(20, 0)], '¹')
    z.art([(0, 34)], '¿')
    z.art([(W - 1, 47)], '¿')
    z.art([(0, 54)], '¡')
    # ---------------- ceiling (layer 14): signs, airline boards, skylights, baffles over the islands and the lounge
    z.k.block(37, 70, 5, 1, 'Â')
    z.k.block(37, 54, 5, 1, 'Á')
    z.k.block(37, 34, 5, 1, 'À')
    z.k.block(37, 3, 5, 1, 'Ã')
    for c0, sg in ((7, 'È'), (19, 'Ì'), (57, 'Í'), (69, 'Î')):
        z.k.block(c0, 72, 5, 1, sg)
    for c0 in (32, 40):
        for r0 in (62, 67):
            z.k.block(c0, r0, 8, 2, 'Ä')
    for c0 in (24, 48):
        z.k.block(c0, 27, 8, 2, 'Ä')
    for c0 in (6, 18, 56, 68):
        for r0 in (57, 61, 65):
            z.k.block(c0, r0, 4, 4, 'Ö')
    for c0 in (60, 64, 68, 72):
        z.k.block(c0, 4, 4, 4, 'Ö')
    # ---------------- spawns and pickups
    for (c, r) in ((16, 55), (63, 55), (39, 43), (33, 45), (46, 45), (20, 34), (58, 37), (39, 26), (31, 20), (50, 21),
                   (75, 27), (39, 5), (10, 54)):
        z.put(c, r, 'S')
    for (c, r) in ((2, 64), (47, 36), (55, 10)):
        z.put(c, r, 'a')
    for (c, r) in ((77, 64), (32, 36), (20, 4)):
        z.put(c, r, 'h')
    # terrazzo bands across the hall (the edge of the check-in hall, the edge of airside, the concourse)
    z.mark(1, 55, 78, 1, 'þ')
    z.mark(1, 36, 78, 1, 'þ')
    z.mark(19, 24, 3, 1, 'þ')
    z.mark(54, 24, 3, 1, 'þ')
    return z


# ================================================================ zone 2: Hangar 2 and the apron
def zone2():
    W, H = 72, 74
    z = AZone('airport_2', W, H, 34, '¦', [2.6, 5.2])
    D, T = z.d(0), z.d(1)
    # the hangar's front wall (row 44): wall either side of the 36 m opening (c 18 - 53)
    z.rect(1, 44, 17, 1, '#')
    z.rect(54, 44, 17, 1, '#')
    # ---------------- the jet (centre at (35.5, 23.5)), its starboard engine on the pylon, the port engine on its stand
    z.put(35, 23, '@')
    z.put(29, 25, '%')
    z.put(46, 31, '$')
    z.mk.put(46, 31, '%')   # the port engine on its stand (the marks layer: the floor-finish layer is tiled)
    for (c, r) in ((25, 19), (45, 19)):
        z.put(c, r, '&')
    # ---------------- work platforms (2.6): forward docks along the fuselage, aft docks (the east one carries the
    # stair to the tail deck at 5.2); scaffold stairs from the floor at the nose end
    D.rect(30, 24, 3, 12, 'w')
    D.rect(38, 24, 3, 12, 'w')
    D.rect(30, 12, 3, 8, 'w')
    D.rect(38, 9, 3, 14, 'w')
    z.block(30, 36, 2, 6, '5')
    z.block(39, 36, 2, 6, '5')
    D.block(39, 13, 2, 6, '5', over='w')
    T.rect(38, 9, 3, 4, 'w')
    # rails: outer edges (not over stairs' tops), tail deck edges
    # (no rails where a dock lies over the wing: rows 24 - 25 forward, 18 - 22 aft -- you step onto the wing there)
    for r in range(26, 35):
        D.put(30, r, '\\', over='w\\')
        D.put(40, r, '\\', over='w\\')
    for r in range(13, 18):
        D.put(30, r, '\\', over='w\\')
    for c in (30, 31, 32):
        D.put(c, 12, '\\', over='w\\')
    for c in (38, 39, 40):
        D.put(c, 9, '\\', over='w\\')
    D.put(40, 11, '\\', over='w\\')
    for c in (38, 39, 40):
        T.put(c, 9, '\\', over='w\\')
    for r in range(10, 13):
        T.put(40, r, '\\', over='w\\')
    T.put(38, 12, '\\', over='w\\')
    # posts: under the docks on the floor (clear of the wings), under the tail deck on the aft dock
    for (c, r) in ((30, 28), (32, 28), (30, 35), (32, 35), (38, 28), (40, 28), (38, 35), (40, 35),
                   (30, 12), (32, 12), (30, 16), (32, 16), (38, 9), (40, 9), (38, 13), (40, 13), (38, 18), (40, 18)):
        z.put(c, r, ':')
    for (c, r) in ((38, 10), (40, 10), (38, 12), (40, 12)):
        D.put(c, r, ':', over='w')
    # ---------------- hangar floor: stores along the west wall, the engine shop east, lockers, drums, pallets
    z.block(1, 4, 4, 3, '[')
    z.block(1, 30, 4, 3, '[')
    for r in (10, 14, 25):
        z.put(1, r, '{')
    for c in range(6, 12):
        z.put(c, 1, ')')
    for (c, r) in ((28, 34), (43, 34), (26, 12), (60, 30)):
        z.put(c, r, '}')
    for (c, r) in ((27, 21), (44, 22), (8, 40)):
        z.put(c, r, '(')
    for (c, r) in ((66, 2), (68, 2), (67, 3), (69, 4)):
        z.put(c, r, '"')
    z.block(62, 6, 2, 3, '`')
    z.block(66, 7, 2, 2, ',')
    z.block(66, 11, 2, 2, ',')
    z.block(42, 39, 2, 2, '?')
    for (c, r) in ((44, 29), (49, 29), (44, 34), (49, 34), (33, 41), (37, 42)):
        z.put(c, r, '*')
    z.block(62, 36, 2, 2, '>')
    z.block(65, 36, 2, 2, '>')
    # walls: the logo on the back wall, columns every 6 m, fire points, a panel and a safety board
    z.f.block(41, 0, 12, 1, 'Þ')
    cols = [(0, r) for r in range(6, 44, 6)] + [(W - 1, r) for r in range(6, 44, 6)] + [(c, 0) for c in (6, 12, 18, 24, 30, 58, 64)]
    z.art(cols, '§')
    z.art([(0, 9), (W - 1, 27)], '¹')
    z.art([(W - 1, 15), (W - 1, 33)], '©')
    z.art([(0, 21)], '®')
    # floor: epoxy tiles over the hangar, the safety line round the jet, the lead-in line, the stop bar
    z.tiles(0, 1, 18, 11, 'ë')
    # ---------------- the apron (rows 45 - 72): the tug and towbar by the doors, a baggage train, ULDs, the belt
    # loader, the stairs truck, the fuel truck, cones, light masts, fence signs, the ops building's logo
    z.block(37, 46, 2, 4, 'D')
    z.block(41, 46, 1, 4, '|')
    z.block(8, 48, 2, 2, '+')
    for r0 in (50, 53, 56):
        z.block(8, r0, 2, 3, '=')
    for r0 in (50, 53):
        z.block(12, r0, 2, 2, '>')
    z.block(18, 50, 2, 6, '<')
    z.block(52, 49, 2, 6, '^')
    z.block(60, 50, 3, 7, '~')
    for (c, r) in ((16, 48), (50, 47), (57, 48), (28, 62)):
        z.put(c, r, '*')
    for (c, r) in ((4, 62), (67, 62)):
        z.put(c, r, ']')
    z.art([(0, 52), (W - 1, 52), (0, 66), (W - 1, 66)], '°')
    z.f.block(40, H - 1, 10, 1, 'Ø')
    # ---------------- roof (14): truss bays over the hangar, the header over the door opening
    for j in range(11):
        for i in range(3):
            z.k.block(i * 24, j * 4, 24, 4, 'Ú')
    z.k.block(18, 44, 36, 1, 'Û')
    # ---------------- spawns and pickups
    for (c, r) in ((8, 18), (20, 8), (52, 10), (62, 20), (60, 42), (12, 36), (24, 40), (12, 64), (58, 64), (26, 48), (47, 46),
                   (54, 26)):
        z.put(c, r, 'S')
    for (c, r) in ((16, 24), (56, 38), (30, 56)):
        z.put(c, r, 'a')
    for (c, r) in ((4, 38), (66, 46), (44, 66)):
        z.put(c, r, 'h')
    # floor marks (after the props: marks only go on open floor)
    z.mark(35, 45, 1, 27, '_')
    z.mark(35, 38, 1, 6, '_')
    z.mk.block(34, 37, 3, 1, 'ß')
    z.mark(18, 44, 36, 1, '-')
    z.mark(2, 59, 30, 1, 'ç')
    z.mark(40, 59, 30, 1, 'ç')
    return z


def main():
    zones = []
    for fn, size, walk in ((zone1, ((80, 80), (78, 78)), WALK1), (zone2, ((72, 72), (74, 74)), WALK2)):
        z = fn()
        errs, stats = check(z, size, walk)
        zones.append((z, errs, stats))
    ok = write(zones, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
