#!/usr/bin/env python3
"""INKBOLT Palmyra Cove Resort zones (theme 'resort'): hand-placed layouts -> src/data/zones/resort_*.txt

    python3 tools/resort_zones.py           # write + validate
    python3 tools/resort_zones.py --check   # validate only
    python3 tools/resort_zones.py --print   # also print the maps

Two zones on the west shore of a tropical island (the beach and the open ocean are just past the west wall, the
shore rocks '{'). Every zone file has the floor plan and five layers:
  "@layer 0.2"  boardwalk deck slabs ('w'), "@layer 0.2" their plank decals ('d' runs N-S, 'b' runs E-W: two symbols
                so neighbouring strips never merge into one block that the [4, 2] decal cannot tile),
  "@layer 7.5"  tree-platform deck slabs ('D') and rope bridges ('=', [3, 2]), "@layer 7.5" the platforms' plank and
                joist decals ('J'), "@layer 7.5" what stands on the platforms (rails 'r', villas, hammocks, props).
Zone 1, the resort grounds (72 x 64): the open-air lobby pavilion at the entry, the lagoon pool with its swim-up bar
in the middle (loungers, umbrellas, cabanas round its paved deck), the beach and a long boardwalk on the west, a garden
lounge in the north-west, the service yard in the south-east, and the first treehouse villa up on a 24 m platform
in two giant palms (north-east), reached by a broken limb.
Zone 2, the canopy (76 x 68): four long platforms in eight giant palms (west 10 x 28, centre 24 x 12 with the CANOPY
SUITE landmark, east 10 x 28, north 24 x 8), joined by three rope bridges; five broken limbs / fallen fronds lean
against them as ramps; below them fallen trunks, stumps, coconut piles, crates and a broken-down golf cart.
Symbols: src/data/themes/resort.js.
"""
import os
import sys

from zonekit import Zone, validate, write, rects, OUT

PREFAB = {'L': (14, 10), 'Q': (20, 12), 'C': (4, 4), 'K': (4, 4), 'N': (4, 4), 'l': (1, 2), 'j': (2, 1), 'o': (3, 2),
          'Y': (2, 2), 'y': (3, 1), 'T': (3, 2), 'X': (2, 3), 'F': (6, 2), 'U': (2, 2), 'e': (2, 4), 'Z': (4, 4),
          '^': (2, 13), '>': (13, 2), '<': (13, 2), 'v': (2, 13)}
LAYER_PREFAB = {'d': (4, 2), 'b': (4, 2), 'J': (4, 2), '=': (3, 2), 'V': (6, 5), 'W': (6, 5), '[': (5, 6), ']': (5, 6),
                'M': (8, 6), 'H': (3, 1), 'o': (3, 2)}
WALKABLE = set(',;~ge')
GROUND = '.,;~'


class RZone(Zone):
    def __init__(self, name, w, h, gate_e, gate_g, pc):
        super().__init__(name, w, h, fill=',')
        self.rect(0, 0, w, 1, '#')
        self.rect(0, h - 1, w, 1, '#')
        self.rect(0, 0, 1, h, '#')
        self.rect(w - 1, 0, 1, h, '#')
        self.rect(0, 1, 1, h - 2, '{')
        self.rect(gate_g, 0, 3, 1, 'G')
        self.rect(gate_e, h - 1, 3, 1, 'E')
        self.put(pc, h - 3, 'P', over=',')
        self.L = {k: Zone(name + '_' + k, w, h) for k in ('bw', 'bd', 'dk', 'dj', 'up')}
        self.plats, self.open = [], set()

    # ---- ground
    def paint(self, c0, r0, w, h, ch, over=',.'):
        self.pave(c0, r0, w, h, ch, over=over)

    def blocks(self, ch, pts, over=GROUND):
        w, d = PREFAB[ch]
        for (c, r) in pts:
            self.block(c, r, w, d, ch, over=over)

    def cells(self, ch, pts, over=GROUND):
        for (c, r) in pts:
            self.put(c, r, ch, over=over)

    # ---- boardwalks (layer 0.2): deck slab + plank decal runs
    def boardwalk(self, c0, r0, w, h, decal):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.g[r][c] in GROUND, (self.name, 'boardwalk over', c, r, self.g[r][c])
                self.g[r][c] = ';' if self.g[r][c] in ',.' else self.g[r][c]
        self.L['bw'].rect(c0, r0, w, h, 'w')
        self.L['bd'].rect(c0, r0, w, h, decal)

    # ---- tree platforms (layer 7.5)
    def platform(self, c0, r0, w, h):
        self.L['dk'].block(c0, r0, w, h, 'D')
        self.L['dj'].block(c0, r0, w, h, 'J')
        self.plats.append((c0, r0, w, h))

    def bridge(self, c0, r0, w, h):
        self.L['dk'].block(c0, r0, w, h, '=')
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.L['dk'].at(c + dc, r + dr) == 'D':
                        self.open.add((c + dc, r + dr))

    def ramp(self, c, r, ch):
        """ramp block with its top end against a platform edge: '^' rises north, 'v' south, '>' east, '<' west"""
        w, d = PREFAB[ch]
        self.block(c, r, w, d, ch, over=GROUND)
        top = {'^': [(c + i, r - 1) for i in range(w)], 'v': [(c + i, r + d) for i in range(w)],
               '>': [(c + w, r + i) for i in range(d)], '<': [(c - 1, r + i) for i in range(d)]}[ch]
        for p in top:
            assert self.L['dk'].at(*p) == 'D', (self.name, 'ramp top not at a platform edge', p)
            self.open.add(p)

    def rails(self):
        up = self.L['up']
        for (c0, r0, w, h) in self.plats:
            for r in range(r0, r0 + h):
                for c in range(c0, c0 + w):
                    if (c in (c0, c0 + w - 1) or r in (r0, r0 + h - 1)) and (c, r) not in self.open:
                        assert up.g[r][c] == '.', (self.name, 'rail cell taken', c, r)
                        up.g[r][c] = 'r'

    def up(self, ch, pts):
        w, d = LAYER_PREFAB.get(ch, (1, 1))
        for (c, r) in pts:
            for rr in range(r, r + d):
                for cc in range(c, c + w):
                    assert self.L['dk'].at(cc, rr) == 'D', (self.name, ch, 'off the platform', cc, rr)
            self.L['up'].block(c, r, w, d, ch)

    def text(self):
        L = self.L
        return (Zone.text(self) + '@layer 0.2\n' + L['bw'].text() + '@layer 0.2\n' + L['bd'].text() + '@layer 7.5\n' +
                L['dk'].text() + '@layer 7.5\n' + L['dj'].text() + '@layer 7.5\n' + L['up'].text())


def layer_checks(z):
    errs = []
    for key, chars in (('bd', 'db'), ('dj', 'J'), ('dk', '='), ('up', 'VW[]MHo')):
        G = z.L[key].g
        for ch in chars:
            sw, sd = LAYER_PREFAB[ch]
            for (c, r, w, h) in rects(G, ch):
                if not ((w % sw == 0 and h % sd == 0) or (w % sd == 0 and h % sw == 0)):
                    errs.append('layer %s %r block %dx%d at (%d,%d) does not tile %dx%d' % (key, ch, w, h, c, r, sw, sd))
    # decals cover their slabs exactly; nothing stands in a platform's trunk cells
    for a, b in (('bw', 'bd'), ('dk', 'dj')):
        for r in range(z.h):
            for c in range(z.w):
                sa, sb = z.L[a].g[r][c] in 'wD', z.L[b].g[r][c] != '.'
                if sa != sb:
                    errs.append('decal / slab mismatch %s at (%d,%d)' % (a, c, r))
    for r in range(z.h):
        for c in range(z.w):
            if z.g[r][c] == 'Z' and z.L['up'].g[r][c] not in '.':
                errs.append('platform prop on a trunk cell (%d,%d)' % (c, r))
            if z.L['dk'].g[r][c] == 'D' and z.g[r][c] in 'pYq':
                errs.append('palm under a platform (%d,%d)' % (c, r))
    return errs


def finish(z, ammo, health, spawns):
    z.rails()
    z.cells('a', ammo)
    z.cells('h', health)
    z.cells('S', spawns)
    pre = dict(PREFAB)
    errs, stats = validate(z, WALKABLE, pre, size=((70, 78), (60, 70)))
    errs += layer_checks(z)
    return z, errs, stats


def torches(z, pts):
    z.cells('t', pts)


# ================================================================ zone 1: the resort grounds
def grounds():
    z = RZone('resort_1', 72, 64, 34, 34, 35)
    # paved paths and the pool deck
    z.paint(34, 54, 3, 9, ';')               # entry walk
    z.paint(33, 40, 5, 4, ';')               # lobby to the pool deck
    z.paint(22, 20, 28, 20, ';')             # pool deck
    z.paint(34, 1, 3, 19, ';')               # to the north gate
    z.paint(50, 29, 12, 2, ';')              # pool deck to the treehouse ramp
    z.paint(60, 24, 2, 5, ';')
    z.paint(43, 48, 16, 2, ';')              # lobby to the service yard
    # the beach (west): sand, no lawn
    z.paint(1, 1, 17, 62, '.', over=',')
    z.paint(1, 1, 3, 62, '~', over='.')
    # boardwalks over the sand
    z.boardwalk(16, 8, 2, 40, 'd')
    z.boardwalk(16, 48, 12, 2, 'b')
    z.boardwalk(4, 30, 12, 2, 'b')
    # landmarks
    z.blocks('L', [(29, 44)])
    z.blocks('Q', [(26, 24)])
    # pool deck: loungers north and south, umbrellas between, cabanas east and west
    for c in (27, 30, 39, 42):
        z.blocks('l', [(c, 21), (c + 1, 21)])
        z.cells('u', [(c + 2, 21)])
        z.blocks('l', [(c, 37), (c + 1, 37)])
        z.cells('u', [(c + 2, 38)])
    z.blocks('K', [(47, 21), (47, 32)])
    z.blocks('N', [(22, 21), (22, 32)])
    z.blocks('o', [(22, 27)])
    z.blocks('o', [(47, 27)])
    torches(z, [(21, 20), (50, 20), (21, 39), (50, 39), (33, 42), (37, 42), (33, 55), (37, 55), (33, 59), (37, 59),
                (33, 3), (37, 3), (33, 11), (37, 11), (49, 31), (56, 28), (62, 26), (59, 24)])
    z.cells('q', [(28, 42), (42, 42), (28, 55), (42, 55)])
    # the beach: lounger pairs facing the sea under umbrellas, kayaks, the towel hut, dune grass, palms
    for r in (5, 11, 17, 23, 35, 41):   # (never two 'j' blocks touching: a merged block would tile the wrong way)
        z.blocks('j', [(6, r), (6, r + 2), (10, r), (10, r + 2)])
        z.cells('u', [(7, r + 1), (11, r + 1)])
    z.blocks('y', [(5, 52), (5, 55), (9, 58)])
    z.blocks('T', [(11, 51)])
    z.cells('k', [(13, 45), (2, 8), (14, 27), (13, 56)])
    z.cells('p', [(14, 4), (14, 14), (14, 37), (3, 46), (14, 60)])
    z.cells('g', [(2, 4), (3, 12), (2, 18), (2, 24), (3, 36), (2, 40), (2, 50), (3, 58), (8, 47), (12, 33), (5, 28), (9, 3)])
    z.cells('c', [(12, 54), (14, 54)])
    z.cells('n', [(18, 50)])
    # garden lounge (north-west): tall palms, hibiscus, lounge sets with umbrellas, a cabana
    z.blocks('Y', [(20, 3), (29, 9), (22, 15), (40, 7)])
    z.blocks('o', [(24, 5), (25, 11)])
    z.cells('u', [(23, 8), (29, 13)])
    z.blocks('C', [(28, 2)])
    z.cells('f', [(19, 9), (19, 10), (31, 15), (32, 15), (26, 17), (38, 15), (39, 15), (41, 12), (43, 2), (44, 2)])
    z.cells('p', [(32, 5), (45, 15)])
    # the first treehouse (north-east): a 24 x 8 platform in two giant palms, a villa, a broken limb up from the south
    z.platform(46, 3, 24, 8)
    z.blocks('Z', [(47, 4), (64, 4)])
    z.ramp(61, 11, '^')
    z.cells('I', [(46, 10), (69, 10), (55, 10), (46, 3), (69, 3), (57, 3)])
    z.up('V', [(54, 4)])
    z.up('H', [(51, 8)])
    z.up('o', [(65, 8)])
    z.up('c', [(60, 4), (61, 4)])
    z.up('k', [(52, 4)])
    z.up('t', [(47, 9), (68, 9)])
    z.cells('k', [(52, 12), (66, 12)])
    z.cells('c', [(48, 12), (49, 12), (68, 13)])
    z.cells('f', [(45, 12), (70, 15), (70, 16)])
    z.blocks('U', [(54, 14)])
    # east lawn: palms, hibiscus, a fallen trunk
    z.cells('p', [(64, 20), (69, 28), (66, 38), (55, 42)])
    z.blocks('F', [(62, 32)])
    z.cells('f', [(53, 38), (54, 38), (69, 22), (69, 34)])
    # service yard (south-east): the broken-down golf cart, crates, coconut piles, a stump
    z.blocks('X', [(52, 52)])
    z.cells('c', [(56, 52), (56, 53), (57, 52), (63, 57), (64, 57), (46, 58)])
    z.cells('k', [(60, 52), (48, 52), (67, 50)])
    z.blocks('F', [(58, 59)])
    z.blocks('U', [(64, 45)])
    z.cells('p', [(45, 61), (69, 61), (61, 44)])
    z.cells('f', [(44, 56), (44, 57), (70, 54)])
    z.cells('n', [(45, 50)])
    # south-west lawn by the lobby
    z.cells('p', [(20, 42), (25, 58), (20, 61)])
    z.cells('f', [(23, 52), (24, 52), (19, 55), (31, 59), (39, 61), (40, 61)])
    z.blocks('Y', [(21, 56)])
    z.cells('k', [(26, 42)])
    return finish(z, [(19, 32), (59, 46), (44, 9)], [(12, 47), (52, 26), (26, 50)],
                  [(8, 9), (8, 27), (9, 46), (23, 41), (25, 8), (44, 5), (55, 19), (67, 25), (63, 40), (66, 53), (52, 60), (17, 60)])


# ================================================================ zone 2: the canopy
def canopy():
    z = RZone('resort_2', 76, 68, 34, 37, 35)
    z.paint(1, 1, 7, 66, '.', over=',')
    z.paint(1, 1, 3, 66, '~', over='.')
    z.paint(34, 48, 3, 18, ';')              # the path up from the entry ...
    z.paint(36, 36, 4, 12, ';', over=',')    # ... past the foot of the centre limb
    z.paint(39, 1, 3, 22, ';')               # ... to the north gate
    z.paint(10, 55, 26, 2, ';')              # cart path west
    z.paint(40, 50, 30, 2, ';')              # cart path east
    z.paint(68, 39, 2, 11, ';')
    # platforms, trunks, bridges, ramps
    z.platform(4, 14, 10, 28)     # A west
    z.platform(26, 23, 24, 12)    # B centre
    z.platform(62, 10, 10, 28)    # C east
    z.platform(12, 3, 24, 8)      # D north
    z.blocks('Z', [(6, 17), (6, 35), (28, 27), (44, 27), (65, 13), (65, 31), (13, 5), (31, 5)])
    z.bridge(14, 28, 12, 2)
    z.bridge(50, 28, 12, 2)
    z.bridge(28, 11, 2, 12)
    z.ramp(8, 42, '^')
    z.ramp(37, 35, '^')
    z.ramp(49, 17, '>')
    z.ramp(18, 11, '^')
    z.ramp(66, 38, '^')
    z.cells('I', [(4, 14), (13, 14), (4, 41), (13, 41), (4, 27), (26, 23), (49, 23), (26, 34), (49, 34), (62, 10), (71, 10),
                  (62, 37), (71, 37), (71, 24), (12, 3), (35, 3), (12, 10), (35, 10), (24, 10)])
    # on the platforms: villas (the CANOPY SUITE on the centre one), hammocks, lounges, torches, crates for cover
    z.up('[', [(5, 24)])
    z.up(']', [(66, 21)])
    z.up('V', [(20, 4)])
    z.up('M', [(34, 25)])
    z.up('H', [(9, 32), (63, 35), (27, 4)])
    z.up('o', [(10, 15), (68, 27), (44, 32), (28, 32)])
    z.up('t', [(5, 15), (12, 40), (27, 24), (48, 24), (27, 33), (48, 33), (63, 11), (70, 36), (13, 9), (34, 9), (36, 33), (39, 33)])
    z.up('c', [(11, 22), (11, 23), (5, 33), (42, 24), (43, 24), (32, 24), (64, 25), (64, 26), (69, 19), (17, 4), (17, 5), (26, 8)])
    z.up('k', [(7, 31), (46, 25), (70, 30), (30, 9)])
    # ground cover under and between the platforms (several levels of fighting)
    z.blocks('F', [(15, 34), (54, 40), (20, 46), (44, 8)])
    z.blocks('U', [(22, 26), (55, 22), (10, 60), (60, 60), (47, 14)])
    z.blocks('X', [(28, 52)])
    z.blocks('e', [(16, 16), (57, 31), (2, 12), (40, 26)])
    z.cells('k', [(18, 30), (31, 38), (45, 37), (59, 26), (7, 46), (64, 45), (25, 18), (52, 9)])
    z.cells('c', [(20, 38), (21, 38), (33, 44), (52, 25), (53, 25), (58, 44), (11, 50), (11, 51), (48, 61), (22, 60), (23, 60)])
    z.cells('f', [(17, 40), (24, 41), (43, 43), (60, 34), (55, 13), (16, 25), (30, 18), (57, 56), (46, 57), (73, 44), (73, 45)])
    z.blocks('o', [(29, 41)])
    z.cells('u', [(32, 41)])
    # palms and tall palms kept clear of the platforms
    z.cells('p', [(2, 6), (3, 48), (2, 58), (15, 48), (26, 62), (56, 56), (72, 52), (73, 4), (20, 52), (40, 55)])
    z.blocks('Y', [(48, 1), (71, 1), (25, 58), (63, 63)])
    z.cells('g', [(2, 20), (3, 30), (2, 40), (2, 52), (5, 64), (3, 2)])
    z.cells('n', [(33, 57)])
    torches(z, [(33, 50), (37, 50), (33, 62), (37, 62), (38, 3), (42, 3), (38, 15), (42, 15)])
    return finish(z, [(17, 44), (57, 47), (26, 19)], [(47, 20), (8, 56), (36, 14)],
                  [(9, 8), (27, 15), (47, 4), (60, 7), (73, 21), (58, 38), (73, 40), (16, 37), (42, 40), (14, 52), (62, 54), (23, 21)])


def main():
    zones = [grounds(), canopy()]
    ok = write(zones, check_only=True)
    if '--check' not in sys.argv:
        for z, _, _ in zones:
            with open(os.path.join(OUT, z.name + '.txt'), 'w') as f:
                f.write(z.text())
    if '--print' in sys.argv:
        for z, _, _ in zones:
            print('\n' + z.text())
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
