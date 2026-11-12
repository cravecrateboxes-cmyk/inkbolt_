#!/usr/bin/env python3
"""INKBOLT Vesper Peak Observatory zones (theme 'observatory'): hand-placed layouts -> src/data/zones/observatory_*.txt

    python3 tools/observatory_zones.py           # write + validate
    python3 tools/observatory_zones.py --check   # validate only
    python3 tools/observatory_zones.py --print   # also print the maps

Player travel is north. Symbols: src/data/themes/observatory.js (its header comment holds the legend).
Zone 1, the summit compound (72 x 70): the funicular's upper station closes the south (two wings round the entrance
court with the entry gate), the dome annex the north (two wings round the porch with the exit gate, the Great Dome
rising behind it); parapets over the cliffs on the west and east edges. The mast pad (1.5 m) in the north-west with
the radio mast array, the fenced antenna field in the west (two 10 m dishes, VSATs, equipment shelters), the ground
station building in the middle with its roof deck (3 m) and the steel gantry east to the terrace, the east terrace
(3 m) with the Halden Dome (landmark), the weather mast and the visitor telescopes; the plaza, the summit cairn, the
power yard (fuel tanks, generator house), snowy rock knolls between.
Zone 2, inside the Great Dome (72 x 68): the dome hall (48 x 48) with the telescope (landmark), the catwalk ring
(4.8 m) reached by two stairs and a bridge from the east gallery (4.8 m); the west wing: control room, spectrograph
lab, plate archive; the east wing: the star deck (glass, a viewing deck at 4.8 m) and the cloud lounge (glass); the
service hall in the north (the exit gate), the lobby in the south (the entry gate).
Layers: zone 1: 0.01 facade signs, 0.02 / 0.03 wall art codes (S/E and N/W faces of wall cells), 0.04 ground codes
(g road, p paving, r rough rock), 0.05 wall schemes, 1.5 the mast pad, 3 the terrace / gantry / its props.
Zone 2: 0.012 floor finishes, 0.02 / 0.03 wall art codes, 0.05 wall schemes, 4.2 / 5 / 8 / 9 ceilings, 4.8 the ring,
the gallery, the bridge, the star deck and their rails, 10 the dome.
"""
import math
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {
    # zone 1
    'B': (10, 10), 'K': (10, 10), 'v': (2, 2), 'M': (3, 3), 'H': (6, 4), 'C': (10, 6), 'O': (12, 12), 'X': (3, 5),
    'F': (2, 5), 'Z': (4, 3), 'Q': (2, 2), 'i': (2, 1), '=': (2, 1), 'u': (2, 6), 'T': (4, 6), 'Y': (4, 6), 'J': (3, 3),
    '1': (12, 1), '2': (12, 1),
    # zone 2
}
PREFAB2 = {
    'D': (2, 1), 'W': (4, 1), 'T': (12, 12), '@': (26, 26), 'u': (2, 10), 'n': (2, 10), 'e': (2, 10), '^': (48, 48),
    '(': (48, 48), ')': (2, 2), '~': (2, 2), '-': (2, 2), '_': (2, 1), 's': (4, 2), 'O': (3, 2), 'b': (3, 1),
    'p': (2, 1), 'R': (2, 1), 'k': (2, 1), 'K': (3, 1), 'V': (6, 1), 't': (3, 2), 'x': (2, 2), 'F': (4, 2), 'Y': (2, 2),
    'U': (2, 2), 'l': (2, 1), '=': (2, 1), 'f': (3, 1), 'q': (2, 1), 'C': (4, 1), 'A': (6, 4), 'M': (4, 4), 'L': (2, 3),
}
TR2 = {'T': '$', 'u': 'N', 'I': '|', '^': '*', 'O': ',', 'R': 'g', 'k': 'z', 'K': 'w', 'c': '+', 'x': '0', 'F': '3',
       'Y': '4', 'U': '5', '=': ';', 'j': '6', 'v': '9', 'f': '[', 'q': ']', 'C': '&', 'A': '>', 'M': '/', 'L': '?',
       'y': '^', 'g': 'y', 'z': 'k'}
WALK1 = set('`xuTYJ')     # under the terrace / pad (marker), cable bridges, stairs and steps (the plan's floor for the BFS)
WALK2 = set('DWuneI')     # doorways, stairs, deck posts (thin)


def spawn(z, c, r):
    if z.g[r][c] != '.':
        print('   spawn cell taken', z.name, c, r, z.g[r][c])
        return
    z.put(c, r, 'S')


class OZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, y):
        return next(L for (yy, L) in self.L if abs(yy - y) < 1e-6)

    def text(self):
        out = Zone.text(self)
        for (y, L) in self.L:
            out += '@layer %s\n' % ('%g' % y) + L.text()
        return out


def rail_edges(deck, up, ch, keep_out, base, chars=None):
    """rails 'r' on every cell of deck symbol(s) `ch` (in grid `deck`) with an outside neighbour (N S E W) that is not
    deck and not a wall in `base`; keep_out: cells left open (where stairs / bridges arrive)"""
    chars = chars or ch
    for r in range(deck.h):
        for c in range(deck.w):
            if deck.g[r][c] not in chars or (c, r) in keep_out:
                continue
            for dc, dr in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                n = deck.at(c + dc, r + dr)
                if n != '.':          # deck, a rail, or a prop standing on the deck
                    continue
                if base.at(c + dc, r + dr) in '#GE{':
                    continue
                up.g[r][c] = 'r' if deck.g[r][c] in 'Ud' else "'"   # concrete decks / steel decks
                break


# ====================================================================== zone 1: the summit compound
def zone1():
    z = OZone('observatory_1', 72, 70, [0.01, 0.02, 0.03, 0.04, 0.05, 1.5, 3])
    W, H = z.w, z.h
    SIGN, ART_SE, ART_NW, GROUND, SCH, PAD, TER = [z.layer(y) for y in (0.01, 0.02, 0.03, 0.04, 0.05, 1.5, 3)]
    # the station (south wings, rows 64-69) round the entrance court, the annex (north wings, rows 0-2) round the porch
    z.rect(0, 64, 28, 6, '#'); z.rect(44, 64, 28, 6, '#'); z.rect(28, 69, 16, 1, '#')
    z.rect(0, 0, 28, 3, '#'); z.rect(44, 0, 28, 3, '#'); z.rect(28, 0, 16, 1, '#')
    z.rect(34, 69, 3, 1, 'E'); z.rect(34, 0, 3, 1, 'G')
    z.put(35, 66, 'P')
    # parapets over the cliffs
    z.rect(0, 3, 1, 61, '{'); z.rect(71, 3, 1, 61, '{')

    # ---- the mast pad (1.5 m) in the north-west: three lattice masts, radio cabinets, the steps up from the south
    z.rect(1, 3, 19, 15, '`'); PAD.rect(1, 3, 19, 15, 'd')
    for (c, r) in ((3, 5), (13, 5), (8, 11)):
        PAD.block(c, r, 3, 3, 'M', over='d')
    for (c, r) in ((7, 6), (17, 9), (3, 13), (12, 14)):
        PAD.put(c, r, 'R', over='d')
    PAD.put(17, 15, 'c', over='d'); PAD.put(16, 4, 'k', over='d')
    z.block(9, 18, 3, 3, 'J')
    rail_edges(PAD, PAD, 'd', {(9, 17), (10, 17), (11, 17)}, z)

    # ---- the antenna field (fenced) in the west: two 10 m dishes, VSATs, two shelters, the cable bridge east
    for c in range(1, 21):
        z.put(c, 22, 'f')
    for r in range(23, 57):
        if r not in (35, 36, 37, 46, 47, 48):
            z.put(20, r, 'f')
    for c in range(1, 20):
        if c not in (10, 11, 12):
            z.put(c, 56, 'f')
    z.block(2, 24, 10, 10, 'B')
    z.block(5, 44, 10, 10, 'K')
    z.block(13, 35, 6, 4, 'H')
    z.block(2, 36, 6, 4, 'H')
    for (c, r) in ((15, 25), (16, 29), (16, 41), (2, 41)):
        z.block(c, r, 2, 2, 'v')
    z.puts([(14, 33), (1, 34), (18, 54)], 'c')
    z.puts([(19, 39), (8, 40)], 'y')
    for c in (19, 20, 21):
        z.put(c, 36, 'x')

    # ---- the ground station (roof deck 3 m), its stair, the gantry east to the terrace (3 m)
    z.block(22, 38, 10, 6, 'C')
    z.block(22, 44, 2, 6, 'u')
    for c in range(32, 48):
        for r in range(39, 43):
            TER.put(c, r, 'm')
    for c in (36, 41, 45):
        for r in (39, 42):
            z.put(c, r, 'I')
    # ---- the east terrace (3 m): the Halden Dome, the weather mast, sky camera, visitor telescopes, benches
    z.rect(48, 6, 23, 37, '`'); TER.rect(48, 6, 23, 37, 'U')
    TER.block(55, 13, 12, 12, 'O', over='U')
    TER.put(67, 9, '!', over='U'); TER.put(64, 31, 'A', over='U')
    TER.puts([(52, 29), (52, 35), (69, 36)], '%', over='U')
    TER.block(58, 37, 2, 1, '=', over='U'); TER.block(62, 37, 2, 1, '=', over='U')
    TER.puts([(50, 8), (50, 26), (69, 27), (58, 32)], 'L', over='U')
    TER.puts([(53, 11), (66, 28)], 'c', over='U')
    z.block(52, 43, 4, 6, 'T')
    z.block(42, 10, 6, 4, 'Y')
    rail_edges(TER, TER, 'Um', {(48, 10), (48, 11), (48, 12), (48, 13), (52, 42), (53, 42), (54, 42), (55, 42)}, z)
    TER.g[39][48] = 'r'; TER.g[42][48] = 'r'   # the terrace's rails meet the gantry's
    # the gantry's ends are open onto the roof deck and the terrace
    for r in range(39, 43):
        if TER.g[r][32] in "r'" and r in (40, 41):
            TER.g[r][32] = 'm'
        if TER.g[r][47] in "r'" and r in (40, 41):
            TER.g[r][47] = 'm'

    # ---- the plaza and the station court: the cairn, panorama boards at the parapets, lamps, benches
    z.put(35, 55, 'q')
    z.block(69, 46, 1, 2, 'i'); z.block(2, 60, 1, 2, 'j')
    z.block(30, 58, 2, 1, '='); z.block(40, 58, 2, 1, '=')
    z.puts([(27, 61), (44, 61), (27, 50), (44, 50), (33, 25), (38, 25), (33, 12), (38, 12)], 'L')
    z.block(4, 58, 3, 5, 'X')
    z.puts([(27, 55), (44, 55)], '%')                       # coin telescopes at the plaza's edges
    z.puts([(29, 63), (30, 63), (42, 63)], 'c')              # luggage cases by the station doors
    # ---- the power yard (south-east): fuel tanks, the generator house, gas bottles, cable drums
    z.block(63, 51, 2, 5, 'F'); z.block(66, 51, 2, 5, 'F')
    z.block(60, 58, 4, 3, 'Z')
    z.puts([(69, 58), (69, 59)], 'y'); z.puts([(58, 52), (59, 55)], 'k')
    # ---- the annex forecourt: deliveries by the porch, snowy rock knolls and boulders in the open
    z.puts([(29, 4), (30, 4), (42, 4), (41, 5)], 'c')
    z.put(43, 4, 'y'); z.put(28, 7, 'k')
    z.block(23, 4, 3, 5, 'X')
    for (c, r) in ((24, 18), (29, 27), (44, 31), (40, 46), (47, 55), (23, 56), (58, 44), (10, 61)):
        z.block(c, r, 2, 2, 'Q')
    z.puts([(27, 15), (31, 22), (25, 30), (43, 22), (46, 34), (38, 50), (50, 59), (19, 61), (57, 49), (14, 19)], 'o')
    z.puts([(26, 22), (45, 27)], 'A')

    # ---- spawns, pickups
    for (c, r) in ((5, 42), (11, 55), (17, 50), (25, 13), (44, 16), (29, 33), (42, 36), (36, 44), (50, 52), (63, 46),
                   (13, 30), (56, 64 - 3)):
        spawn(z, c, r)
    z.puts([(30, 18), (59, 47)], 'a'); z.puts([(21, 58), (46, 8)], 'h')
    TER.put(60, 34, 'a', over='U')

    # ---- facade signs (0.01), wall art codes (0.03: the north faces of the station; 0.02: the south faces of the annex)
    SIGN.block(8, 63, 12, 1, '1'); SIGN.block(52, 63, 12, 1, '1')
    SIGN.block(50, 3, 12, 1, '2')
    for c in range(0, 28):
        ART_NW.g[64][c] = 'd' if c in (22, 23) else 'l' if c in (21, 24) else '.' if c % 3 == 2 else 'w'
    for c in range(44, 72):
        ART_NW.g[64][c] = 'd' if c in (48, 49) else 'l' if c in (47, 50) else '.' if c % 3 == 0 else 'w'
    for r in range(65, 69):
        ART_NW.g[r][44] = 'w' if r != 67 else 'l'     # the west face of the east wing (court side)
        ART_SE.g[r][27] = 'w' if r != 67 else 'l'     # the east face of the west wing
    for c in range(0, 28):
        ART_SE.g[2][c] = 'v' if c in (4, 14) else 'd' if c in (25,) else 'W'
    for c in range(44, 72):
        ART_SE.g[2][c] = 'v' if c in (64, 68) else 'd' if c in (46,) else 'W'
    for r in (1, 2):
        ART_SE.g[r][27] = 'l'
        ART_NW.g[r][44] = 'l'
    # wall schemes: the station south of the knolls, the annex north
    for r in range(H):
        for c in range(W):
            SCH.g[r][c] = 'S' if r >= 34 else 'A'
    # ground codes: the road from the court to the porch, the plaza, the paths; rough rock knolls in the open
    for r in range(1, 69):
        for c in range(32, 40):
            GROUND.g[r][c] = 'g'
    for r in range(52, 69):
        for c in range(26, 46):
            GROUND.g[r][c] = 'p'
    for r in range(43, 47):
        for c in range(21, 32):
            GROUND.g[r][c] = 'g'
    for (c0, r0, w, h) in ((21, 12, 10, 11), (24, 23, 8, 11), (40, 19, 7, 17), (21, 51, 6, 11), (45, 49, 12, 3), (2, 18, 6, 3), (12, 57, 8, 4)):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if GROUND.g[r][c] == '.':
                    GROUND.g[r][c] = 'r'

    errs, stats = validate(z, set('.') | WALK1, PREFAB, size=((70, 74), (66, 72)))
    return z, errs, stats


# ====================================================================== zone 2: inside the Great Dome
DCX, DCZ = 36, 34      # the dome hall's centre (cell corner)


def zone2():
    z = OZone('observatory_2', 72, 68, [0.012, 0.02, 0.03, 0.05, 4.2, 4.8, 5, 8, 9, 10])
    W, H = z.w, z.h
    FIN, ART_SE, ART_NW, SCH, C42, DK, C50, C80, C90, DOME = [z.layer(y) for y in (0.012, 0.02, 0.03, 0.05, 4.2, 4.8, 5, 8, 9, 10)]
    z.rect(0, 0, W, 1, '#'); z.rect(0, H - 1, W, 1, '#'); z.rect(0, 0, 1, H, '#'); z.rect(W - 1, 0, 1, H, '#')
    z.rect(34, 0, 3, 1, 'G'); z.rect(34, H - 1, 3, 1, 'E')
    z.put(35, 64, 'P')
    # inner walls: the hall square, the lobby line, the wings' partitions
    z.rect(11, 1, 1, 57, '#'); z.rect(60, 1, 1, 57, '#')
    z.rect(12, 9, 48, 1, '#'); z.rect(1, 58, 70, 1, '#')
    z.rect(1, 19, 10, 1, '#'); z.rect(1, 38, 10, 1, '#'); z.rect(61, 29, 10, 1, '#')

    def door(c, r, w=2, vert=False, ch='D'):
        for k in range(w):
            cc, rr = (c, r + k) if vert else (c + k, r)
            assert z.g[rr][cc] == '#', (cc, rr)
            z.g[rr][cc] = ch
    door(20, 58); door(34, 58, 4, ch='W'); door(50, 58); door(5, 58); door(65, 58)
    door(11, 47, vert=True); door(5, 38); door(11, 28, vert=True); door(5, 19); door(11, 4, vert=True)
    door(22, 9, 4, ch='W'); door(46, 9, 4, ch='W')
    door(60, 4, vert=True); door(60, 16, vert=True); door(62, 29); door(60, 44, vert=True)

    # ---- the dome hall: the telescope, the ring and its columns, the stairs, the gallery and the bridge
    z.block(30, 28, 12, 12, 'T')
    DK.block(23, 21, 26, 26, '@')
    for i in range(16):
        a = math.radians(11.25 + 22.5 * i)
        x, y = DCX + math.cos(a) * 12.0, DCZ - math.sin(a) * 12.0
        for (px, py) in ((x - 0.15, y - 0.15), (x + 0.15, y - 0.15), (x - 0.15, y + 0.15), (x + 0.15, y + 0.15)):
            c, r = int(math.floor(px)), int(math.floor(py))
            if z.g[r][c] == '.':
                z.g[r][c] = ':'
    z.block(35, 47, 2, 10, 'u')
    z.block(35, 11, 2, 10, 'n')
    for r in range(14, 55):
        for c in range(54, 60):
            DK.put(c, r, 'm')
    for r in range(32, 36):
        for c in range(49, 54):
            DK.put(c, r, 'm')
    z.block(44, 50, 10, 2, 'e')
    for r in (15, 21, 27, 40, 46, 53):
        z.put(54, r, 'I')
    for c in (51,):
        for r in (32, 35):
            z.put(c, r, 'I')
    keep = {(54, r) for r in (33, 34, 50, 51)} | {(49, 33), (49, 34)}
    rail_edges(DK, DK, 'm', keep, z)
    for (c, r) in ((54, 32), (54, 35)):   # the bridge's rails run on round the gallery edge
        DK.g[r][c] = "'"
    for r in (33, 34):
        for c in range(49, 55):
            if DK.g[r][c] == "'":
                DK.g[r][c] = 'm'
    # hall floor props: instrument crates, carts, gas bottles, tool cabinets, consoles round the pier
    z.block(14, 12, 2, 2, 'x'); z.block(14, 55 - 1, 2, 2, 'x'); z.block(57 - 1, 11, 2, 2, 'x')
    z.block(24, 13, 2, 1, 'k'); z.block(46, 54, 2, 1, 'k'); z.block(25, 54, 3, 1, 'K')
    z.puts([(13, 25), (13, 40), (58, 30), (13, 33)], 'y')
    z.puts([(19, 19), (52, 19), (19, 49), (30, 26), (42, 42)], 'g')
    z.puts([(17, 30), (17, 37), (31, 44), (41, 23)], 'z')
    z.block(15, 22, 2, 3, 'L')
    z.block(27, 41, 2, 2, 'x'); z.block(43, 25, 2, 2, 'x')
    z.block(43, 32, 1, 2, 'k'); z.block(28, 34, 1, 2, 'k')   # instrument consoles by the pier
    # ---- the service hall (north): the coating chamber, the mirror cart, crates, the lift
    z.block(14, 2, 6, 4, 'A'); z.block(51, 2, 4, 4, 'M'); z.block(46, 2, 2, 3, 'L')
    z.block(25, 2, 2, 2, 'x'); z.block(28, 2, 2, 2, 'x'); z.block(41, 3, 2, 2, 'x')
    z.puts([(22, 7), (58, 7), (13, 7)], 'y'); z.puts([(57, 2), (58, 2)], 'g'); z.put(31, 7, 'z')
    # ---- the west wing: control room (video wall, ops desks, racks), spectrograph lab, plate archive
    z.block(3, 1, 6, 1, 'V')
    z.block(2, 6, 3, 1, 'K'); z.block(6, 6, 3, 1, 'K'); z.block(2, 10, 3, 1, 'K'); z.block(6, 10, 3, 1, 'K')
    z.block(1, 13, 1, 2, 'R'); z.block(1, 16, 1, 2, 'R'); z.block(10, 13, 1, 2, 'k')
    z.puts([(3, 7), (7, 7), (3, 11), (7, 11)], 'c')
    z.block(2, 22, 4, 2, 's'); z.block(2, 31, 4, 2, 's'); z.block(7, 25, 3, 2, 'O')
    z.block(10, 33, 1, 3, 'b'); z.block(1, 27, 1, 3, 'b'); z.puts([(9, 34), (2, 28)], 'c')
    z.block(1, 41, 1, 2, 'p'); z.block(1, 44, 1, 2, 'p'); z.block(1, 51, 1, 2, 'p'); z.block(1, 54, 1, 2, 'p')
    z.block(5, 44, 3, 2, 't'); z.block(9, 53, 1, 2, 'k'); z.block(10, 40, 1, 2, 'R')
    # ---- the east wing: the star deck (a viewing deck at 4.8 m along the glass, its stair) and the cloud lounge
    for r in range(3, 9):
        for c in range(63, 71):
            DK.put(c, r, 'm')
    for r in range(9, 27):
        for c in range(65, 71):
            DK.put(c, r, 'm')
    z.block(63, 9, 2, 10, 'u')
    for r in range(3, 27):
        for c in range(63, 71):
            if DK.g[r][c] != 'm':
                continue
            open_side = any(DK.at(c + dc, r + dr) not in "m'" and z.at(c + dc, r + dr) not in '#' for dc, dr in ((0, -1), (0, 1), (1, 0), (-1, 0)))
            if open_side and (c, r) not in ((63, 8), (64, 8)):
                DK.g[r][c] = "'"
    for r in (11, 18, 24):
        z.put(65, r, 'I')
    DK.puts([(70, 5), (70, 12), (70, 20)], 'v', over='m')
    DK.block(67, 14, 1, 3, 'f', over='m')
    z.puts([(70, 10), (70, 16), (70, 22), (70, 27)], 'v')
    z.block(62, 22, 1, 3, 'f'); z.puts([(61, 2), (61, 27)], 'j')
    z.block(66, 33, 1, 3, 'f'); z.block(66, 41, 1, 3, 'f'); z.block(66, 49, 1, 3, 'f')
    z.block(68, 33, 1, 2, 'q'); z.block(68, 41, 1, 2, 'q'); z.block(68, 49, 1, 2, 'q')
    z.puts([(70, 31), (70, 38), (70, 46), (70, 54)], 'v')
    z.block(61, 50, 1, 4, 'C'); z.puts([(61, 31), (61, 57), (70, 57)], 'j')
    # ---- the lobby: reception, the telescope model, the meteorite, lockers, benches, planters
    z.block(12, 60, 4, 2, 'F'); z.block(26, 62, 2, 2, 'Y'); z.block(44, 62, 2, 2, 'U')
    z.block(3, 66, 6, 1, 'l'); z.block(63, 66, 6, 1, 'l')
    z.block(20, 64, 2, 1, '='); z.block(50, 64, 2, 1, '=')
    z.puts([(17, 59), (54, 59), (30, 59), (41, 59), (1, 59), (70, 59)], 'j')

    # ---- spawns, pickups
    for (c, r) in ((17, 15), (16, 51), (28, 50), (46, 15), (22, 34), (49, 41), (5, 15), (6, 35), (5, 49), (40, 6),
                   (63, 36), (5, 62), (66, 62), (68, 2 + 1)):
        spawn(z, c, r)
    z.puts([(20, 28), (51, 24), (67, 14)], 'a'); z.puts([(8, 29), (37, 6), (64, 55)], 'h')

    # ---- layers: floor finishes, ceilings, the dome
    FIN.block(12, 10, 48, 48, '(')
    FIN.block(1, 59, 70, 8, ')')
    FIN.block(61, 1, 10, 28, '~'); FIN.block(61, 30, 10, 28, '~')
    C42.rect(1, 1, 10, 18, '-'); C42.rect(1, 20, 10, 18, '-'); C42.rect(1, 39, 10, 18, '-'); C42.rect(1, 57, 10, 1, '_')
    C50.rect(1, 59, 70, 8, '-')
    C80.rect(12, 1, 48, 8, '-')
    C90.rect(61, 1, 10, 28, '-'); C90.rect(61, 30, 10, 28, '-')
    DOME.block(12, 10, 48, 48, '^')
    # ---- schemes (the finish a wall shows toward each open cell) and the art codes
    for r in range(H):
        for c in range(W):
            if 12 <= c <= 59 and 10 <= r <= 57:
                s = 'H'
            elif r >= 59:
                s = 'B'
            elif c <= 10:
                s = 'C' if r <= 18 else 'L'
            elif c >= 61:
                s = 'V'
            else:
                s = 'M'
            SCH.g[r][c] = s
    # the glazing: the east wall of both viewing rooms (the west face of the ring's east cells)
    for r in list(range(2, 28)) + list(range(31, 57)):
        ART_NW.g[r][71] = 'g'
    # star charts in the labs (pairs), posters, boards, exit points, clocks
    def art(L, c, r, k):
        assert z.g[r][c] == '#', ('art on', c, r, z.g[r][c])
        L.g[r][c] = k
    # west wing: the ring's west cells (c 0) face east -> their E face is on layer 0.02
    for (r0) in (24, 33, 47):
        art(ART_SE, 0, r0, 'c'); art(ART_SE, 0, r0 + 1, 'c')
    for r in (3, 9, 30, 42):
        art(ART_SE, 0, r, 'p')
    for r in (22, 35):
        art(ART_NW, 11, r, 'b')        # the west face of the hall wall, inside the spectrograph lab
    art(ART_NW, 11, 52, 'c'); art(ART_NW, 11, 53, 'c')
    art(ART_NW, 11, 15, 'k')
    # the hall: exit points and posters on its walls (west wall's E face, east wall's W face, the north / south walls)
    for r in (16, 40):
        art(ART_SE, 11, r, 'x')
    for r in (22, 46):
        art(ART_NW, 60, r, 'p')
    for c in (16, 30, 42, 56):
        art(ART_SE, c, 9, 'p' if c in (30, 42) else 'x')
    for c in (16, 28, 44, 56):
        art(ART_NW, c, 58, 'x' if c in (16, 56) else 'p')
    # the lobby: posters, the clock, exits
    for c in (8, 24, 47, 62):
        art(ART_SE, c, 58, 'p')
    art(ART_SE, 32, 58, 'k')
    for c in (10, 30, 41, 60):
        art(ART_NW, c, 67, 'p' if c in (30, 41) else 'x')
    # the service hall's north wall
    for c in (20, 30, 44, 54):
        art(ART_SE, c, 0, 'x' if c in (30, 44) else 'p')
    errs, stats = validate(z, set('.') | WALK2, PREFAB2, size=((70, 74), (66, 70)))
    # one symbol table serves both zones: zone 2's layout letters -> the theme's symbols (data layers keep their codes)
    tr = str.maketrans(TR2)
    for G in [z] + [L for (y, L) in z.L if y not in (0.02, 0.03, 0.05)]:
        G.g = [list(''.join(row).translate(tr)) for row in G.g]
    return z, errs, stats


if __name__ == '__main__':
    ok = write([zone1(), zone2()], check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)
