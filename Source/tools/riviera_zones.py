#!/usr/bin/env python3
"""INKBOLT Grand Hotel Riviera zones (theme 'riviera'): hand-placed layouts -> src/data/zones/riviera_*.txt

    python3 tools/riviera_zones.py           # write + validate
    python3 tools/riviera_zones.py --check   # validate only
    python3 tools/riviera_zones.py --print   # also print the maps

A made-up Belle Epoque grand hotel on a cliff over the Mediterranean (the sea to the west). Player travel is north.
Zone 1, the ground floor (73 x 63, 9 m rooms under the ceiling): the Grand Lobby in the middle (the front doors in the
south, the reception, the concierge, lounges round the marble medallion under the great chandelier, the gallery at
4.5 m on three sides and the Imperial Staircase up to it, bridges from its top landings to the gallery's arms); the
restaurant Le Grand Bleu on the sea side (west: tables by the arched windows, banquettes, the wine wall, the kitchen
pass) with the bar Le Phare at its south end (the bar, a grand piano, lounges); the conference hall Salon
Mediterranee in the north-east (the stage with its screen, rows of chairs either side of the aisle, the AV desk) and
its foyer in the south-east (the registration desk, the coffee station, cocktail tables); the guest wing in the
north-west (a corridor with three walk-in suites on its north side and closed doors on its south side); the palm
court in the north (tea tables, palms, the court fountain, the lifts) with the doors out to the pool terrace (exit).
Zone 2, the pool terrace (75 x 68, open sky): the infinity pool along the cliff edge (west) running out to its
vanishing edge over the sea, the spa pool, the pool bar, pairs of sun loungers under parasols, cabanas along the
north wing, the towel hut, palms, olives, planters; the spa podium in the east (its front of arched windows, doors
and bougainvillea) carries the roof garden at 4.5 m (pergola lounges, the belvedere, daybeds, olives, planters,
hedges, lawns), reached by two stairs set into the podium; the hotel's facades on three sides; the exit through the
north wing.
Each zone file is the floor plan followed by its layers:
  zone 1: @layer 0 floors (medallion, runner, carpets, cement tiles), @layer 4.5 the gallery (deck, balustrades,
          columns, furniture), @layer 9 the ceiling fittings (coffers, chandeliers, downlights)
  zone 2: @layer 4.5 the roof garden's deck, @layer 4.5 its paving and furniture
Symbols: src/data/themes/riviera.js.
"""
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {
    # zone 1
    'X': (13, 10), 'R': (6, 4), 'Q': (3, 2), 'F': (3, 3), 'L': (4, 3), 'K': (3, 3), 'B': (8, 4), 'O': (2, 1), 'k': (2, 1),
    'w': (2, 1), 'T': (3, 3), 'D': (9, 4), 'y': (2, 1), 'v': (2, 1), 'M': (6, 6), 'N': (6, 6), 'W': (6, 6), 'd': (2, 2),
    'u': (2, 1), 'q': (4, 2), 'V': (3, 1), 'Z': (4, 1), 'Y': (6, 1), 'A': (3, 2), 'C': (4, 1), 'g': (4, 2), 's': (2, 2),
    'f': (4, 4), 'x': (7, 7), '_': (3, 1), '!': (4, 4), '+': (4, 4), ',': (2, 2), '~': (4, 4), 'H': (5, 5), '^': (3, 3),
    # zone 2
    '%': (9, 12), '&': (8, 6), '$': (8, 4), '<': (3, 3), '>': (1, 2), '(': (3, 3), ')': (3, 2), '{': (3, 1), '}': (2, 2),
    '?': (8, 4), '/': (4, 6), '1': (5, 5), '2': (2, 2), '3': (2, 2), '8': (2, 2), '9': (2, 2),
}
DECK = 4.5


class RZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, i):
        return self.L[i][1]

    def pf(self, ch, c, r, g=None, over='.', rot=False):
        w, d = PREFAB[ch]
        if rot:
            w, d = d, w
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


# ================================================================ zone 1: the ground floor
def zone1():
    W, H = 73, 63
    z = RZone('riviera_1', W, H, [0, DECK, 9])
    FL, GA, CE = z.layer(0), z.layer(1), z.layer(2)
    ring(z)
    z.rect(35, 0, 3, 1, 'G')          # the doors out to the pool terrace
    z.rect(35, H - 1, 3, 1, 'E')      # the front doors
    z.put(36, 59, 'P')
    # ---- partitions
    z.rect(21, 1, 1, H - 2, '#')      # restaurant / suites | lobby / palm court
    z.rect(51, 1, 1, H - 2, '#')      # lobby / palm court | conference hall / foyer
    z.rect(22, 22, 29, 1, '#')        # palm court | lobby
    z.rect(52, 37, 20, 1, '#')        # conference hall | foyer
    z.rect(1, 7, 20, 1, '#')          # suites' front wall
    z.rect(7, 1, 1, 6, '#')
    z.rect(14, 1, 1, 6, '#')
    z.rect(1, 12, 20, 9, '#')         # the closed suites south of the corridor, the restaurant's north wall
    for (c0, r0, w, h) in ((3, 7, 2, 1), (10, 7, 2, 1), (17, 7, 2, 1),          # suite doorways
                           (21, 8, 1, 4),                                       # corridor -> palm court
                           (27, 22, 3, 1), (43, 22, 3, 1),                      # palm court -> lobby (under the gallery)
                           (51, 14, 1, 3),                                      # palm court -> conference hall
                           (21, 44, 1, 3), (21, 54, 1, 3),                      # lobby -> restaurant, bar
                           (51, 46, 1, 3), (51, 55, 1, 3),                      # lobby -> foyer
                           (55, 37, 3, 1), (66, 37, 3, 1)):                     # foyer -> conference hall
        z.rect(c0, r0, w, h, 'n')
    # ---- the guest wing: three walk-in suites (Salon, King, Twin), a housekeeping cart, a console in the corridor
    z.pf('W', 1, 1)
    z.pf('M', 8, 1)
    z.pf('N', 15, 1)
    z.pf('y', 6, 10)
    z.pf('k', 13, 11)
    z.put(1, 9, 'p')
    FL.block(1, 8, 20, 4, '+')
    # ---- the palm court: tea tables round the fountain, palms in urns, a writing desk, the lifts (in the chooser)
    z.pf('f', 34, 9)
    for (c, r) in ((25, 4), (29, 3), (41, 3), (45, 4), (25, 14), (29, 16), (41, 16), (45, 14), (25, 9), (46, 9)):
        z.pf('s', c, r)
    for (c, r) in ((22, 1), (50, 1), (22, 21), (50, 21), (33, 7), (39, 7), (33, 14), (39, 14)):
        z.put(c, r, 'p')
    z.pf('w', 31, 1)
    z.pf('w', 40, 1)
    z.pf('K', 47, 17)
    z.put(36, 18, 't')
    # ---- the lobby: the Imperial Staircase, columns under the gallery's edge, reception, concierge, lounges
    z.pf('X', 30, 27)
    for r in (27, 32, 38, 43, 48, 53, 58):
        z.put(25, r, 'I')
        if r != 43:                   # the reception stands under the east arm there
            z.put(47, r, 'I')
    for c in (29, 36, 43):
        z.put(c, 26, 'I')
    z.pf('R', 47, 40, rot=True)
    z.pf('Q', 22, 41)
    z.pf('F', 35, 41)
    for (c, r) in ((27, 47), (42, 47), (27, 53), (42, 53)):
        z.pf('L', c, r)
    for (c, r) in ((31, 48), (40, 48), (31, 54), (40, 54)):
        z.pf('O', c, r)
    z.put(33, 60, 'j')
    z.puts([(23, 60), (49, 60), (23, 33), (49, 33), (27, 38), (45, 38)], 'p')
    z.puts([(24, 58), (48, 57)], 'c')
    z.pf('k', 22, 48, rot=True)
    z.pf('k', 50, 34, rot=True)
    # ---- the restaurant Le Grand Bleu: two-tops by the windows, four-tops, the chef's table, banquettes, the wine
    # wall, the pass in front of the kitchen doors, the sommelier's trolleys
    z.pf('Z', 8, 21)
    for r in (24, 27, 30, 33, 36, 39, 42, 45):
        z.pf('u', 2, r)
    for (c, r) in ((7, 25), (7, 31), (7, 43), (12, 28), (12, 40), (12, 46), (7, 46)):
        z.pf('d', c, r)
    z.pf('T', 9, 35)
    for r in (27, 33, 39):
        z.pf('q', 19, r, rot=True)
    z.pf('V', 20, 23, rot=True)
    z.puts([(15, 25), (5, 37), (15, 37)], 'z')
    z.pf('v', 15, 43)
    for c in (2, 6, 10, 14, 18):
        z.put(c, 50, 'p')
    # the bar Le Phare: the bar against the south wall, stools, the piano, lounges
    z.pf('B', 3, 58)
    for c in (3, 5, 7, 9):
        z.put(c, 57, 'b')
    z.pf('K', 15, 57)
    z.pf('L', 2, 52)
    z.pf('L', 9, 52)
    z.pf('O', 16, 53)
    FL.block(1, 22, 20, 28, ',')
    # ---- the conference hall Salon Mediterranee: the stage, the lectern, chair rows, the AV desk, the coffee station
    z.pf('D', 57, 1)
    z.put(67, 5, 'l')
    for r in (9, 11, 13, 15, 17, 19, 21, 23):
        z.pf('Y', 54, r)
        if r != 23:
            z.pf('Y', 64, r)
    z.pf('A', 60, 28)
    z.pf('C', 71, 9, rot=True)
    z.pf('C', 71, 17, rot=True)
    z.puts([(55, 31), (58, 33), (65, 31), (68, 33)], 'o')
    z.puts([(52, 1), (71, 1), (52, 36), (71, 36)], 'p')
    z.put(53, 13, 'e')
    FL.block(52, 6, 20, 24, '!')
    # ---- the foyer: registration desk, coffee station, cocktail tables, lounges, the cloakroom (concierge desk)
    z.pf('g', 59, 41)
    z.pf('C', 56, 61)
    z.pf('C', 63, 61)
    z.pf('Q', 68, 48)
    z.puts([(56, 45), (66, 45), (58, 53), (64, 53), (61, 49)], 'o')
    z.pf('L', 53, 56)
    z.puts([(52, 38), (71, 38), (71, 59), (52, 61)], 'p')
    z.put(70, 43, 'e')
    z.put(53, 44, 'e')
    # ---- floors: the medallion, the runner from the front doors, lobby carpets under the lounges
    FL.block(33, 39, 7, 7, 'x')
    FL.block(35, 46, 3, 16, '_')
    for (c, r) in ((27, 46), (42, 46), (27, 52), (42, 52)):
        FL.block(c, r, 4, 4, '!', over='.!')
    # ---- the gallery (@layer 4.5): the arms on three sides, bridges to the stair's top landings, balustrades on the
    # open edges, columns over the ones below, furniture against the walls
    for r in range(23, H - 1):
        for c in range(22, 26):
            GA.put(c, r, 'm')
        for c in range(47, 51):
            GA.put(c, r, 'm')
    for r in range(23, 27):
        for c in range(26, 47):
            GA.put(c, r, 'm')
    for r in range(33, 37):
        for c in list(range(26, 30)) + list(range(43, 47)):
            GA.put(c, r, 'm')
    # the edges: west arm col 25, east arm col 47, north arm row 26 (over the stair's landing), bridges rows 33 / 36
    for r in range(27, H - 1):
        if not 33 <= r <= 36:
            GA.g[r][25] = 'r'
            GA.g[r][47] = 'r'
    for c in range(26, 47):
        GA.g[26][c] = 'r'
    for c in list(range(26, 30)) + list(range(43, 47)):
        GA.g[33][c] = 'r'
        GA.g[36][c] = 'r'
    GA.g[26][25] = 'r'
    GA.g[26][47] = 'r'
    for (c, r) in [(25, rr) for rr in (27, 32, 38, 43, 48, 53, 58)] + [(47, rr) for rr in (27, 32, 38, 48, 53, 58)] + [(cc, 26) for cc in (29, 36, 43)]:
        GA.g[r][c] = 'i'
    # the stair's own balustrades close its edges; the bridges meet its top landings at cols 30 / 42 (open)
    for (c, r) in ((22, 29), (22, 50), (48, 45)):
        GA.block(c, r, 3, 4, 'L', over='m')
    for (c, r) in ((22, 40), (48, 28), (48, 54), (30, 23), (42, 23)):
        GA.put(c, r, 'p', over='m')
    GA.block(22, 56, 1, 2, 'k', over='m')
    GA.block(50, 37, 1, 2, 'k', over='m')
    GA.puts([(23, 24), (49, 24), (36, 24)], 'S', over='m')
    GA.put(24, 45, 'a', over='m')
    # ---- the ceiling (@layer 9): the great chandelier over the medallion, chandeliers over the palm court, the
    # restaurant, the bar and the conference hall, coffers in the lobby, downlights in the corridors
    CE.block(34, 40, 5, 5, 'H')
    for (c, r) in ((34, 9), (26, 9), (42, 9), (6, 28), (6, 38), (13, 33), (13, 44), (6, 55), (60, 13), (60, 22), (60, 46), (60, 55)):
        CE.block(c, r, 3, 3, '^')
    for (c, r) in ((27, 39), (41, 39), (27, 46), (41, 46), (27, 53), (41, 53), (32, 53), (37, 53), (32, 46), (37, 46)):
        CE.block(c, r, 4, 4, '~', over='.')
    for c in range(3, 20, 4):
        CE.put(c, 9, ':')
    for r in range(28, 61, 4):
        CE.put(23, r, ':')
        CE.put(49, r, ':')
    # ---- spawn cans and pickups
    for (c, r) in ((10, 9), (30, 6), (44, 11), (36, 3), (60, 7), (68, 26), (56, 26), (12, 23), (5, 40), (16, 48),
                   (64, 47), (62, 58)):
        z.put(c, r, 'S')
    z.puts([(17, 31), (62, 34)], 'a')
    z.puts([(29, 19), (55, 51)], 'h')
    return z


# ================================================================ zone 2: the pool terrace and the roof garden
PX0, PX1, PY0, PY1 = 52, 73, 1, 44      # the spa podium (cols, rows inclusive)


def zone2():
    W, H = 75, 68
    z = RZone('riviera_2', W, H, [0, DECK, DECK])
    LW, DK, RG = z.layer(0), z.layer(1), z.layer(2)
    ring(z)
    z.rect(30, 0, 3, 1, 'G')          # through the north wing
    z.rect(35, H - 1, 3, 1, 'E')      # out of the hotel's garden doors
    z.put(36, 64, 'P')
    # ---- the podium and the notches of its two stairs
    z.rect(PX0, PY0, PX1 - PX0 + 1, PY1 - PY0 + 1, '#')
    z.rect(52, 18, 8, 4, '.')
    z.pf('?', 52, 18)                 # rises east to the roof (its top landing at col 59)
    z.rect(64, 37, 4, 8, '.')
    z.pf('?', 64, 37, rot=True)       # rises north (its top landing at row 37)
    # the roof deck over the podium's inner cells and the stair heads
    for r in range(PY0, PY1 + 1):
        for c in range(PX0, PX1 + 1):
            if z.g[r][c] != '#':
                continue
            inner = all(z.at(c + dc, r + dr) == '#' for dc in (-1, 0, 1) for dr in (-1, 0, 1))
            head = (c == 60 and 18 <= r <= 21) or (r == 36 and 64 <= c <= 67)
            if inner or head:
                DK.put(c, r, '=')
    # ---- the infinity pool along the cliff, the spa pool, the pool bar
    z.block(1, 9, 12, 45, '%')        # 12 x 45: five 9 m segments, south end, middles, north end
    z.pf('&', 24, 10)
    z.pf('$', 38, 27)
    # ---- sun loungers in pairs under parasols on the pool deck, facing the sea
    for r in (10, 15, 20, 25, 31, 36, 41, 46):
        z.pf('<', 14, r)
        if r not in (25, 31):
            z.pf('<', 18, r)
    for (c, r) in ((23, 17), (26, 17), (29, 17), (32, 17)):
        z.pf('>', c, r)
    for (c, r) in ((22, 51), (16, 56), (22, 8)):
        z.put(c, r, '[')
    # ---- cabanas along the north wing, the towel hut by the garden doors, the pool bar's palms
    for c in (14, 19, 24, 36, 41, 46):
        z.pf('(', c, 1)
    z.pf(')', 41, 60)
    for (c, r) in ((34, 25), (47, 25), (34, 32), (47, 32), (26, 40), (26, 47), (44, 40), (44, 47), (31, 58), (41, 56),
                   (50, 12), (50, 50), (13, 58), (13, 4)):
        z.put(c, r, ']')
    # ---- planters as low walls, olives, lemon trees, urns, cypresses, the terrace fountain, cafe tables by the bar
    for (c, r) in ((28, 22), (28, 36), (36, 52), (44, 36), (16, 62), (24, 62), (46, 62)):
        z.pf('{', c, r)
    for (c, r) in ((31, 40), (20, 59), (48, 55), (31, 5), (49, 5), (24, 54)):
        z.pf('}', c, r)
    z.pf('f', 35, 45)
    z.puts([(23, 9), (33, 9), (23, 16), (33, 16), (37, 22), (46, 22), (51, 24), (51, 15), (34, 44), (39, 44), (34, 49), (39, 49)], '5')
    z.puts([(51, 46), (51, 66), (1, 66), (1, 56), (1, 3), (12, 66), (73, 66), (73, 46)], '6')
    z.puts([(28, 64), (44, 64), (13, 8), (13, 55)], '7')
    for (c, r) in ((36, 33), (43, 33), (49, 29), (49, 34)):
        z.pf('s', c, r)
    z.pf('3', 30, 53)
    # ---- the lawn garden south of the podium: two pergola lounges, daybeds, olives, a cypress line, a fire table
    z.pf('/', 56, 50)
    z.pf('/', 67, 50)
    for (c, r) in ((62, 47), (62, 57), (55, 60), (69, 60)):
        z.pf('2', c, r)
    for (c, r) in ((59, 62), (65, 62), (71, 47)):
        z.pf('}', c, r)
    z.pf('3', 62, 52)
    for c in range(54, 72):
        if c not in (62, 63, 64):
            z.put(c, 45, '4')
    z.puts([(53, 47), (53, 56), (72, 56), (60, 66), (66, 66)], '6')
    LW.block(54, 46, 18, 20, '9', over='.')
    # ---- the roof garden (@layer 4.5): the belvedere over the pool, pergola lounges, daybeds, fire tables, olives,
    # planters, hedges, lemon trees, cypresses along the parapet, lawns and tiles
    def rg(ch, c, r, rot=False):
        w, d = PREFAB[ch]
        if rot:
            w, d = d, w
        for rr in range(r, r + d):
            for cc in range(c, c + w):
                assert DK.g[rr][cc] == '=' or ch in '89', ('roof garden prop off the deck', ch, cc, rr)
        RG.block(c, r, w, d, ch)
    rg('1', 54, 3)
    rg('/', 61, 3)
    rg('/', 66, 3)
    rg('/', 61, 26)
    rg('2', 54, 10)
    rg('2', 54, 13)
    rg('2', 54, 25)
    rg('2', 54, 28)
    rg('3', 63, 13)
    rg('3', 68, 30)
    rg('}', 57, 33)
    rg('}', 70, 10)
    rg('}', 70, 20)
    rg('}', 57, 39)
    rg('{', 61, 16)
    rg('{', 65, 16)
    rg('{', 69, 37, rot=True)
    for c in range(61, 72):
        RG.put(c, 23, '4')
    for r in range(10, 15):
        RG.put(67, r, '4')
    RG.puts([(53, 2), (53, 8), (53, 16), (53, 31), (53, 37), (53, 43), (60, 43), (72, 43), (72, 2)], '6')
    RG.puts([(59, 8), (59, 13), (63, 9), (69, 9), (63, 21), (69, 21), (59, 30), (66, 30), (60, 39), (70, 26)], '5')
    for (c, r) in ((61, 10), (61, 12), (57, 17), (57, 19), (66, 33), (63, 33), (57, 27), (61, 39)):
        rg('9', c, r)
    RG.puts([(64, 12), (58, 24), (70, 34)], 'S')
    RG.put(66, 18, 'h')
    # ---- spawn cans and pickups (ground)
    for (c, r) in ((8, 5), (28, 6), (44, 8), (38, 17), (22, 26), (31, 30), (46, 18), (24, 44), (42, 41), (17, 52),
                   (48, 50), (28, 48)):
        z.put(c, r, 'S')
    z.puts([(21, 13), (46, 52)], 'a')
    z.puts([(35, 36), (20, 44)], 'h')
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
    for z, size in ((zone1(), ((73, 73), (63, 63))), (zone2(), ((75, 75), (68, 68)))):
        errs, stats = validate(z, set('n'), PREFAB, size=size)
        errs += checks(z)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
