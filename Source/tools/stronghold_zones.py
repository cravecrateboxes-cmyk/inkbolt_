#!/usr/bin/env python3
"""INKBOLT Fort Highwatch zones (theme 'stronghold'): hand-placed layouts -> src/data/zones/stronghold_*.txt

    python3 tools/stronghold_zones.py           # write + validate
    python3 tools/stronghold_zones.py --check   # validate only
    python3 tools/stronghold_zones.py --print   # also print the maps

A military stronghold built and carved into the west face of a huge mountain. Player travel is north.
Zone 1, the outer works (72 x 64): a broad cliff ledge. The cliff rises along the east edge and the south-east, the
rock spur with the fortified gate closes the north (cols 20+); a concrete parapet runs along the west edge, the south
edge west of col 30 and the north edge west of col 20, over a sheer drop. Terrace 1 (3.6 m, solid) fills the
north-east against the cliff, terrace 2 (7.2 m) sits on its north part; each is reached by a switchback (a 1.8 m
flight, a landing, a 1.8 m flight back) and terrace 1 also by a long ramp from the south.
Zone 2, inside the mountain (75 x 64): the observation terrace along the west edge (cols 1-13, open sky, parapet on
col 0) and, behind the terrace face (col 14, four doorways), the carved halls under a 12 m rock roof: the command
centre (north-west) with the tactical table and the ops balcony, the barracks (south-west), the main gallery from the
entry to the exit gate (cols 33-44), the vehicle hangar (north-east) with the armoured truck and a mezzanine, and the
ammo depot (south-east) with its racks and the armory cage. Rock between the halls is two cells thick.
Each zone file is the floor plan followed by its layers ("@layer 0" first: wall codes the chooser reads):
  zone 1: @layer 0 wall codes, 1.8 landing deck, 1.8 its rails, 3.6 terrace 1 deck, 3.6 what stands on it,
          5.4 landing deck, 5.4 its rails, 7.2 terrace 2 deck, 7.2 what stands on it
  zone 2: @layer 0 wall codes, 2.4 decks, 2.4 what stands on them, 12 the cavern roof
Symbols: src/data/themes/stronghold.js.
"""
import sys

from zonekit import Zone, validate, write, rects

PREFAB = {'B': (5, 4), 'K': (4, 4), 'N': (3, 3), 'M': (3, 3), 'H': (14, 14), 'R': (4, 4), 'A': (2, 2), 'C': (2, 2),
          'Z': (4, 4), 'J': (2, 4), 'g': (2, 1), 'F': (2, 4), 'O': (2, 2), '>': (6, 2), '<': (6, 2), '^': (2, 12),
          'u': (2, 6), 'v': (2, 6), 'T': (3, 7), 'X': (8, 1), 'k': (2, 1), '~': (4, 8), ',': (2, 2), 'Y': (4, 1),
          'z': (2, 1), 'Q': (1, 2), 'V': (6, 1), '$': (6, 4), '+': (2, 1), '*': (3, 3), '&': (3, 2), '_': (6, 8)}
WALKABLE = set('t~,')          # under-terrace cells are not walked on at ground level but count as the plan's floor
FLOOR = '.'


class SZone(Zone):
    def __init__(self, name, w, h, layers):
        super().__init__(name, w, h)
        self.L = [(y, Zone(name + '@' + str(y), w, h)) for y in layers]

    def layer(self, i):
        return self.L[i][1]

    def blocks(self, ch, pts, over=FLOOR):
        w, d = PREFAB[ch]
        for (c, r) in pts:
            self.block(c, r, w, d, ch, over=over)

    def cells(self, ch, pts, over=FLOOR):
        for (c, r) in pts:
            self.put(c, r, ch, over=over)

    def text(self):
        out = Zone.text(self)
        for (y, L) in self.L:
            out += '@layer %s\n' % ('%g' % y) + L.text()
        return out


def rail_ring(deck, up, ch, open_cells, sides='NSEW', base=None):
    """rails 'r' on every edge cell of the deck symbol `ch` (in grid `deck`) whose outside neighbour on one of `sides`
    is not deck, except open_cells; base: a grid whose '#' cells count as a wall beside the deck (no rail there)"""
    for r in range(deck.h):
        for c in range(deck.w):
            if deck.g[r][c] != ch or (c, r) in open_cells:
                continue
            need = False
            for s, (dc, dr) in (('N', (0, -1)), ('S', (0, 1)), ('E', (1, 0)), ('W', (-1, 0))):
                if s not in sides:
                    continue
                n = deck.at(c + dc, r + dr)
                if n == ch:
                    continue
                if base is not None and base.at(c + dc, r + dr) == '#':
                    continue
                need = True
            if need:
                assert up.g[r][c] == '.', (deck.name, 'rail cell taken', c, r, up.g[r][c])
                up.g[r][c] = 'r'


# ====================================================================== zone 1: the outer works
def zone1():
    z = SZone('stronghold_1', 72, 64, [0, 1.8, 1.8, 3.6, 3.6, 5.4, 5.4, 7.2, 7.2])
    W, H = z.w, z.h
    CODES, LD1, LR1, D1, UP1, LD2, LR2, D2, UP2 = [z.layer(i) for i in range(9)]
    # ring: parapet on the west, the south (cols 0-29) and the north (cols 0-19); rock elsewhere
    z.rect(0, 0, W, 1, '#'); z.rect(0, H - 1, W, 1, '#'); z.rect(W - 1, 0, 1, H, '#')
    z.rect(0, 1, 1, H - 2, '{')
    z.rect(1, 0, 18, 1, '{'); z.rect(1, H - 1, 28, 1, '{')
    for (c, r) in ((0, 0), (19, 0), (0, H - 1), (29, H - 1)):
        z.g[r][c] = '}'
    z.rect(40, 0, 3, 1, 'G')
    z.rect(60, H - 1, 3, 1, 'E')
    z.put(61, H - 3, 'P')
    # terrace 1 (3.6) and its tongue; terrace 2 (7.2) on it; the two landings
    T1 = [(48, 1, 23, 26), (48, 27, 4, 2)]
    for (c0, r0, w, h) in T1:
        z.rect(c0, r0, w, h, 't')
        D1.rect(c0, r0, w, h, 'D')
    z.rect(58, 27, 4, 4, 't'); LD1.rect(58, 27, 4, 4, 'd')
    for (c0, r0, w, h) in ((50, 1, 21, 10), (50, 11, 4, 2)):
        D2.rect(c0, r0, w, h, 'U')
    LD2.rect(60, 11, 4, 4, 'd')
    # switchback 1 (ground -> 1.8 landing -> terrace 1), the long ramp from the south
    z.block(52, 29, 6, 2, '>')
    z.block(52, 27, 6, 2, '<')
    z.block(66, 27, 2, 12, '^')
    # switchback 2 on terrace 1 (3.6 -> 5.4 landing -> terrace 2)
    UP1.block(54, 13, 6, 2, '>')
    UP1.block(54, 11, 6, 2, '<')
    # rails: terrace 1 (open where the ramps land), terrace 2, the landings
    rail_ring(D1, UP1, 'D', {(51, 27), (51, 28), (66, 26), (67, 26)}, base=z)
    rail_ring(LD1, LR1, 'd', {(58, 27), (58, 28), (58, 29), (58, 30)}, sides='SEW', base=z)
    rail_ring(D2, UP2, 'U', {(53, 11), (53, 12)}, base=z)
    rail_ring(LD2, LR2, 'd', {(60, 11), (60, 12), (60, 13), (60, 14)}, sides='SEW', base=z)
    # the fortified gate: bastions either side of the approach
    z.blocks('B', [(34, 1), (43, 1)])
    # wall codes for the chooser (on the wall cells): 1 bunker door, 2 gun casemate, 3 vent, 4 rock shelf
    for (c, r, k) in ((71, 33, '1'), (71, 41, '2'), (71, 49, '3'), (71, 56, '1'),
                      (36, 63, '2'), (44, 63, '1'), (52, 63, '3'), (66, 63, '2'),
                      (22, 0, '1'), (28, 0, '2'), (32, 0, '4'), (71, 60, '4')):
        assert z.g[r][c] == '#', (c, r)
        CODES.g[r][c] = k
    # ---- ground: the helipad (south-west) with fuel, the windsock
    z.blocks('H', [(3, 40)])
    z.blocks('F', [(18, 45)])
    z.cells('b', [(18, 50), (19, 50), (21, 46)])
    z.cells('w', [(2, 37)])
    z.cells('L', [(2, 55), (17, 38)])
    # gun emplacements on the west parapet (front west), one on the south parapet (front south)
    z.blocks('N', [(1, 8), (1, 24)])
    z.blocks('M', [(13, 60)])
    z.cells('c', [(4, 11), (4, 23), (12, 61), (16, 61)])
    # pillboxes in the field
    z.blocks('K', [(22, 21), (33, 45)])
    # supply dump under camo nets by the gate (north-west), a jeep, a comms mast, generator
    z.blocks('Z', [(22, 3), (27, 3)])
    z.blocks('C', [(22, 9), (31, 8)])
    z.cells('c', [(25, 9), (26, 10), (29, 10), (24, 11)])
    z.blocks('J', [(31, 2)])
    z.blocks('A', [(8, 2)])
    z.cells('b', [(10, 2), (10, 3)])
    z.blocks('g', [(44, 33)])
    z.cells('b', [(46, 33)])
    # defensive lines: sandbags, jersey barriers, tank traps
    z.run(7, 16, 8, '=')
    z.run(24, 34, 9, '=')
    z.run(13, 28, 5, '=', vertical=True)
    z.run(40, 38, 7, 'j')
    z.run(36, 56, 8, 'j')
    z.run(46, 50, 6, 'j')
    z.cells('x', [(9, 31), (12, 33), (16, 31), (38, 25), (41, 28), (27, 54), (44, 44)])
    z.cells('o', [(70, 45), (69, 46), (70, 53), (65, 62), (21, 62), (30, 1), (12, 1)])
    z.blocks('O', [(68, 58), (40, 61)])
    z.cells('L', [(30, 31), (47, 42), (55, 48), (46, 18), (30, 12)])
    z.cells('q', [(57, 58)])
    z.cells('c', [(64, 44), (65, 44), (64, 45), (55, 34), (50, 36), (44, 57), (35, 41)])
    z.blocks('C', [(56, 38), (62, 54)])
    z.blocks(',', [(28, 12), (44, 30), (55, 44)])        # oil stains where vehicles stand and the generator runs
    # ---- terrace 1: a pillbox over the ledge, an emplacement at the west rail, a comms mast, supplies
    UP1.block(56, 18, 4, 4, 'K')
    UP1.block(49, 20, 3, 3, 'N')
    UP1.block(66, 18, 2, 2, 'A')
    for (c, r) in ((62, 22), (63, 22), (69, 23), (69, 24), (64, 16), (65, 16)):
        UP1.put(c, r, 'c')
    UP1.put(69, 25, 'L')
    UP1.block(62, 24, 2, 2, 'C')
    # ---- terrace 2: the radome, an emplacement looking west over everything, a floodlight
    UP2.block(64, 3, 4, 4, 'R')
    UP2.block(51, 3, 3, 3, 'N')
    UP2.put(56, 2, 'c'); UP2.put(57, 2, 'c'); UP2.put(69, 9, 'L')
    # ---- spawns, pickups
    z.cells('S', [(8, 6), (20, 15), (36, 12), (10, 22), (30, 27), (19, 37), (41, 32), (27, 49), (6, 57), (46, 53), (44, 23), (23, 58)])
    z.cells('a', [(6, 34), (52, 41)])
    z.cells('h', [(38, 19), (26, 44)])
    return z


# ====================================================================== zone 2: inside the mountain
def zone2():
    z = SZone('stronghold_2', 75, 64, [0, 2.4, 2.4, 12])
    W, H = z.w, z.h
    CODES, DK, UP, ROOF = [z.layer(i) for i in range(4)]
    z.rect(0, 0, W, 1, '#'); z.rect(0, H - 1, W, 1, '#'); z.rect(W - 1, 0, 1, H, '#')
    z.rect(0, 1, 1, H - 2, '{'); z.rect(1, 0, 13, 1, '{'); z.rect(1, H - 1, 13, 1, '{')
    for (c, r) in ((0, 0), (0, H - 1)):
        z.g[r][c] = '}'
    # the terrace face with its four doorways
    z.rect(14, 0, 1, H, '#')
    for r0 in (4, 13, 40, 54):
        z.rect(14, r0, 1, 3, 'n')
    # rock between the halls (two cells thick) and their openings
    z.rect(31, 1, 2, H - 2, '#')       # command / barracks | gallery
    z.rect(45, 1, 2, H - 2, '#')       # gallery | hangar / depot
    z.rect(15, 30, 16, 2, '#')         # command | barracks
    z.rect(47, 36, 27, 2, '#')         # hangar | depot
    for (c0, r0, w, h) in ((31, 10, 2, 5), (31, 44, 2, 4), (45, 8, 2, 12), (45, 50, 2, 4), (20, 30, 4, 2), (64, 36, 4, 2)):
        z.rect(c0, r0, w, h, '.')
    z.rect(38, 0, 3, 1, 'G')
    z.rect(34, H - 1, 3, 1, 'E')
    z.put(35, H - 3, 'P')
    # wall codes: 5 wall lamp, 6 cable tray with a sector sign (hall walls)
    for (c, r, k) in ((16, 0, '6'), (28, 0, '5'), (31, 3, '5'), (32, 20, '5'), (32, 33, '6'), (31, 55, '5'),
                      (44, 63, '5'), (45, 26, '5'), (46, 30, '6'), (74, 26, '5'), (74, 44, '6'), (74, 52, '5'),
                      (48, 0, '5'), (60, 0, '6'), (52, 63, '5'), (24, 63, '5'), (18, 31, '5'), (70, 37, '5'), (52, 36, '6')):
        assert z.g[r][c] == '#', (c, r, z.g[r][c])
        CODES.g[r][c] = k
    # ---- decks (2.4): the command ops balcony, the hangar mezzanine, the terrace observation post
    for (c0, r0, w, h) in ((15, 25, 16, 5), (66, 1, 8, 20), (4, 28, 6, 8)):
        DK.rect(c0, r0, w, h, 'm')
    z.blocks('v', [(15, 19)])
    z.blocks('u', [(66, 21), (6, 36)])
    rail_ring(DK, UP, 'm', {(15, 25), (16, 25), (66, 20), (67, 20), (6, 35), (7, 35)}, base=z)
    z.cells('I', [(18, 25), (23, 25), (28, 25), (66, 4), (66, 10), (66, 16), (73, 20), (4, 28), (9, 28), (4, 35), (9, 35)])
    UP.put(5, 29, 's'); UP.put(5, 32, 's'); UP.put(8, 30, 'c'); UP.put(8, 33, 'c')
    for (c, r) in ((69, 3), (70, 3), (72, 6), (72, 7), (69, 14), (72, 15)):
        UP.put(c, r, 'c')
    UP.block(70, 10, 2, 2, 'C')
    UP.block(19, 27, 2, 1, '+'); UP.block(25, 27, 2, 1, '+')
    UP.put(29, 28, '!')
    # ---- the cavern roof over the halls (cols 15-74)
    ROOF.rect(15, 0, 60, 64, '_')
    # ---- terrace: AA guns at the parapet, the flagpole, sandbag nests, crates, scopes
    z.blocks('*', [(2, 11), (2, 47)])
    z.cells('|', [(8, 22)])
    z.run(3, 3, 4, '=')
    z.run(3, 58, 4, '=')
    z.run(10, 16, 3, '=', vertical=True)
    z.cells('x', [(9, 50), (6, 26)])
    z.cells('c', [(12, 9), (12, 10), (11, 26), (12, 43), (3, 40), (12, 60)])
    z.cells('s', [(1, 18), (1, 38), (1, 53)])
    z.cells('L', [(13, 2), (13, 33), (13, 61)])
    # ---- command centre (cols 15-30, rows 1-29): video wall, tactical table, consoles, radio racks
    z.blocks('V', [(20, 1)])
    z.blocks('$', [(20, 11)])
    z.blocks('+', [(18, 8), (22, 8), (26, 8), (18, 17), (22, 17), (26, 17)])
    z.cells('!', [(15, 1), (16, 1), (29, 1), (30, 1), (30, 13)])
    z.cells('c', [(17, 12), (29, 22)])
    # ---- barracks (cols 15-30, rows 32-62): bunks with footlockers, lockers, mess tables
    for c in range(16, 30, 2):
        z.blocks('Q', [(c, 61)])
        z.put(c, 60, 'p')
    for c in (17, 19, 21, 25, 27, 29):     # two island rows of bunks, footlockers at their feet (south)
        for r in (46, 52):
            z.blocks('Q', [(c, r)])
            z.put(c, r + 2, 'p')
    z.cells('@', [(30, 34), (30, 35), (30, 36), (30, 37), (30, 38), (30, 39), (15, 32), (16, 32)])
    z.blocks('&', [(18, 35), (24, 35), (18, 40)])
    z.cells('c', [(28, 41), (22, 57)])
    # ---- main gallery (cols 33-44): barricades, pallet stacks, crates, a jeep by the hangar mouth
    z.run(35, 52, 4, 'j')
    z.run(39, 44, 4, 'j')
    z.run(34, 30, 3, '=')
    z.run(40, 22, 4, 'j')
    z.blocks('C', [(42, 36), (34, 14), (41, 6)])
    z.blocks('J', [(43, 24)])
    z.cells('b', [(33, 41), (33, 42), (44, 57)])
    z.cells('c', [(37, 9), (38, 9), (42, 48), (33, 58)])
    # ---- hangar (cols 47-73, rows 1-35): blast door, armoured truck, bays, workbenches, tool chests, tyres, hoist
    z.blocks('X', [(50, 1)])
    z.blocks('T', [(52, 4)])
    z.blocks('J', [(59, 4)])
    z.blocks('~', [(51, 14), (57, 14)])
    z.blocks(',', [(52, 25), (58, 22)])
    z.blocks('k', [(48, 35), (51, 35), (55, 35)])
    z.cells('y', [(53, 35), (57, 35), (73, 28)])
    z.cells('e', [(48, 26), (48, 27), (49, 26), (62, 7), (62, 8)])
    z.cells('i', [(62, 15)])
    z.cells('b', [(70, 4), (71, 4), (72, 4), (68, 12), (68, 13), (63, 30)])
    z.blocks('C', [(70, 7), (70, 15), (60, 28)])
    # ---- ammo depot (cols 47-73, rows 38-62): racks in rows, shell pallets, the armory cage in the south-east corner
    for r in (41, 46):
        z.blocks('Y', [(49, r), (55, r), (61, r), (67, r)])
    z.cells('l', [(50, 50), (51, 50), (56, 50), (62, 50), (63, 50)])
    z.cells('l', [(48, 53), (48, 54), (48, 55), (52, 58), (53, 58), (58, 54)])
    z.blocks('C', [(55, 54), (50, 60)])
    for c in range(61, 74):
        z.put(c, 56, 'f')
    for r in range(57, 63):
        if r not in (58, 59):          # the cage door
            z.put(61, r, 'f')
    z.blocks('z', [(63, 62), (66, 62), (69, 62)])
    z.cells('l', [(72, 59), (72, 60), (72, 61), (64, 59)])
    z.cells('c', [(70, 58), (67, 58)])
    # ---- spawns, pickups
    z.cells('S', [(7, 8), (6, 23), (7, 44), (6, 55), (24, 5), (19, 21), (25, 43), (38, 12), (37, 33), (55, 23), (64, 20), (59, 39), (69, 51)])
    z.cells('a', [(40, 40), (5, 16)])
    z.cells('h', [(60, 12), (22, 55)])
    return z


def checks(z):
    """extra checks: prefabs in the layers tile their footprints, rails only on decks, ramp tops on decks"""
    errs = []
    for (y, L) in z.L:
        for ch, (sw, sd) in PREFAB.items():
            for (c, r, w, h) in rects(L.g, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('layer %g prefab %r block %dx%d at (%d,%d)' % (y, ch, w, h, c, r))
    return errs


def main():
    out = []
    for z in (zone1(), zone2()):
        errs, stats = validate(z, WALKABLE | set('n'), PREFAB, size=((70, 76), (60, 66)))
        errs += checks(z)
        out.append((z, errs, stats))
    ok = write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
