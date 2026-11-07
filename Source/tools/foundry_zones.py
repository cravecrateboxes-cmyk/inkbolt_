"""Titan Foundry zone layouts (src/data/zones/foundry_{1,2,3}.txt): the floor plan, the "@layer 0" overlay (floor
paint, and the overhead monorail whose cells may pass over the lines) and, in the armour hall, the "@layer 6" gantry
grid (spawns and pickups standing on the titan bay's walkway decks).

  foundry_1  Chassis Hall: the WARDEN titan frame on its jig (NW) and the half-built STRIDER (NE) either side of the
             exit; the spider line runs north along the west wall (intake house at the south end, dispatch house
             facing the titan); weld cells, jigs, test cells and parts on the open floor; a monorail of hover tanks
             and gunships high over the entry.
  foundry_2  Armour Hall: the half-armoured titan in its gantry bay (stairs at both front corners up to the 6 m
             walkway), spare reactor cores and centipede racks beside it, the hound / hover-tank line north along the
             east wall, the monorail over the entry.
  foundry_3  Launch Hall: the finished titan (NW) and strider (NE) on their launch sleds, launch rails and lanes down
             to the two sealed launch doors in the south wall either side of the entry, rows of finished robots on
             dispatch pads in the middle, ammunition everywhere.

The giants stand at the north end and the floor in front of them is kept low (cover under 4 m, no overhead line), so
they are in full view from the entry. Zones are 60 x 72 (1 cell = 1 m), exit GGG at columns 29-31 on row 0, entry EEE
on the last row, P in front of it. Run: python3 tools/foundry_zones.py [--print]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zonekit import Zone, validate, OUT  # noqa: E402

W, H = 60, 72
WALK = set('.ah')
PREFABS = {'L': (12, 8), 'U': (12, 8), 'W': (4, 4), 'J': (6, 4), 'Q': (6, 6), 'K': (10, 4), 'F': (4, 4), 'R': (4, 4),
           'p': (2, 2), 'm': (2, 2), 'k': (2, 2), 'l': (4, 2), 'B': (2, 2), 'T': (20, 14), 'Y': (24, 18), 'Z': (20, 16),
           'X': (18, 18), 'V': (18, 18), 'D': (18, 2)}
DECK_Y = 6
RAIL_ROW = 65           # the monorail (65 % 8 == 1: its ports clear the buttresses)


def shell(name):
    z = Zone(name, W, H)
    z.rect(0, 0, W, 1, '#')
    z.rect(0, H - 1, W, 1, '#')
    z.rect(0, 0, 1, H, '#')
    z.rect(W - 1, 0, 1, H, '#')
    z.rect(29, 0, 3, 1, 'G')
    z.rect(29, H - 1, 3, 1, 'E')
    z.put(30, H - 3, 'P')
    return z


class Paint:
    """The "@layer 0" overlay grid (a paint symbol per cell; prefab decals as blocks; the monorail run)."""

    def __init__(self, z):
        self.z = z
        self.g = [['.'] * W for _ in range(H)]

    def put(self, c, r, ch):
        if self.z.at(c, r) in '#GE' or self.g[r][c] != '.':
            return
        self.g[r][c] = ch

    def run(self, c0, r0, n, ch, vertical=False, skip='TYZXVDLUWJQKFR'):
        for k in range(n):
            c, r = (c0, r0 + k) if vertical else (c0 + k, r0)
            if self.z.at(c, r) in skip:
                continue
            self.put(c, r, ch)

    def block(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                assert self.z.at(c, r) not in '#GE' and self.g[r][c] == '.', (self.z.name, c, r, ch)
                self.g[r][c] = ch

    def rail(self, r):
        for c in range(1, W - 1):
            assert self.g[r][c] == '.', (self.z.name, c, r)
            self.g[r][c] = 'o'

    def text(self):
        return '\n'.join(''.join(r) for r in self.g)


def common_paint(z, P, aisle_rows, drains, oils):
    for r in aisle_rows:   # exit chevrons up the central aisle
        if all(z.at(c, rr) in '.ah' and P.g[rr][c] == '.' for c in (29, 30) for rr in (r, r + 1)):
            P.block(29, r, 2, 2, '6')
    for (c, r) in drains:
        if z.at(c, r) == '.':
            P.put(c, r, '3')
    for (c, r) in oils:
        if z.at(c, r) == '.':
            P.put(c, r, '4')


def boxes(z, P, spots, ch):
    for (c, r) in spots:
        if all(z.at(cc, rr) == '.' and P.g[rr][cc] == '.' for cc in (c, c + 1) for rr in (r, r + 1)):
            P.block(c, r, 2, 2, ch)


def zone1():
    z = shell('foundry_1')
    P = Paint(z)
    P.rail(RAIL_ROW)
    # the giants
    z.block(4, 4, 20, 14, 'T')
    z.block(38, 3, 18, 18, 'X')
    z.block(25, 6, 2, 2, 'B')
    z.block(34, 10, 2, 2, 'B')
    z.block(26, 15, 2, 2, 'k')
    z.block(34, 16, 2, 2, 'm')
    z.puts([(24, 3), (24, 4), (37, 3), (25, 19), (57, 7), (57, 8), (2, 6), (2, 7)], 'c')
    z.puts([(36, 21), (2, 15), (57, 16)], 'b')
    # the spider line north along the west wall (intake at the south end, dispatch toward the titan)
    z.block(4, 20, 8, 48, 'L')
    z.block(13, 22, 2, 2, 'B')
    # the chassis floor
    z.block(16, 27, 4, 4, 'W')
    z.block(49, 26, 4, 4, 'W')
    z.block(24, 27, 4, 2, 'l')
    z.block(40, 28, 4, 2, 'l')
    z.block(15, 37, 6, 4, 'J')
    z.block(43, 37, 6, 4, 'J')
    z.block(51, 45, 6, 6, 'Q')
    z.block(15, 50, 6, 6, 'Q')
    z.block(26, 35, 2, 2, 'p')
    z.block(34, 35, 2, 2, 'p')
    z.block(22, 45, 2, 2, 'm')
    z.block(38, 45, 2, 2, 'm')
    z.block(43, 55, 2, 2, 'k')
    z.block(56, 30, 2, 2, 'B')
    z.puts([(21, 30), (37, 31), (45, 49), (25, 57), (35, 58)], 'x')
    z.puts([(14, 46), (57, 38), (47, 60), (20, 62), (36, 24), (53, 60)], 'b')
    z.puts([(22, 51), (50, 47)], 'n')
    z.puts([(30, 44), (31, 44), (29, 44), (24, 41), (36, 41), (19, 64), (41, 64), (42, 64)], 'c')
    z.run(25, 61, 3, 'g')
    z.run(33, 61, 3, 'g')
    z.run(46, 33, 3, 'g')
    z.puts([(26, 21), (34, 22), (57, 24), (15, 32), (22, 33), (47, 31), (57, 41), (30, 39), (15, 59), (22, 57), (40, 56), (56, 57)], 'S')
    z.puts([(30, 31), (46, 52)], 'a')
    z.puts([(16, 44), (39, 61)], 'h')
    # paint: hazard bands before the bays, the lane beside the line, the central aisle, keep-clear boxes
    P.run(4, 18, 20, '2')
    P.run(38, 21, 18, '2')
    P.run(13, 25, 42, '1', vertical=True)
    P.run(27, 23, 40, '1', vertical=True)
    P.run(33, 23, 40, '1', vertical=True)
    boxes(z, P, ((52, 52), (54, 52), (16, 57), (18, 57), (49, 31), (31, 49)), '0')
    boxes(z, P, ((21, 25), (44, 25), (40, 42), (20, 43), (48, 63), (9, 70)), '5')
    common_paint(z, P, (66, 57, 47, 26, 12, 2), ((17, 22), (52, 23), (20, 47), (45, 41), (56, 66), (24, 60), (36, 66)),
                 ((15, 25), (54, 27), (21, 64), (41, 60), (26, 20), (35, 24), (48, 44), (18, 35)))
    return z, P, None


def zone2():
    z = shell('foundry_2')
    P = Paint(z)
    P.rail(RAIL_ROW)
    z.block(18, 4, 24, 18, 'Y')
    z.block(4, 5, 4, 4, 'R')
    z.block(52, 5, 4, 4, 'R')
    z.block(3, 12, 10, 4, 'K')
    z.block(47, 12, 10, 4, 'K')
    z.block(13, 6, 2, 2, 'B')
    z.block(45, 6, 2, 2, 'B')
    z.block(9, 19, 2, 2, 'p')
    z.block(14, 23, 2, 2, 'k')
    z.puts([(10, 2), (11, 2), (56, 3), (57, 3), (16, 13), (43, 13), (16, 2), (43, 2)], 'c')
    z.puts([(9, 3), (50, 3), (24, 23), (35, 23)], 'b')
    z.puts([(9, 10), (50, 10)], 'n')
    # the hound / hover-tank line north along the east wall
    z.block(48, 20, 8, 48, 'U')
    z.block(45, 22, 2, 2, 'B')
    # the floor: weld cells, jigs, test cells, a spare reactor core at eye level, parts
    z.block(5, 27, 4, 4, 'W')
    z.block(37, 27, 4, 4, 'W')
    z.block(14, 27, 4, 2, 'l')
    z.block(25, 28, 4, 2, 'l')
    z.block(5, 37, 6, 4, 'J')
    z.block(36, 37, 6, 4, 'J')
    z.block(19, 36, 4, 4, 'R')
    z.block(4, 48, 6, 6, 'Q')
    z.block(38, 49, 6, 6, 'Q')
    z.block(16, 45, 2, 2, 'm')
    z.block(27, 52, 2, 2, 'p')
    z.block(33, 44, 2, 2, 'm')
    z.block(44, 58, 2, 2, 'k')
    z.block(2, 30, 2, 2, 'B')
    z.puts([(20, 31), (33, 32), (12, 46), (24, 58), (35, 59)], 'x')
    z.puts([(3, 43), (45, 45), (15, 61), (40, 62), (11, 24)], 'b')
    z.puts([(11, 51), (37, 52)], 'n')
    z.puts([(29, 43), (30, 43), (31, 43), (25, 40), (35, 40), (19, 64), (40, 64), (41, 64)], 'c')
    z.run(25, 61, 3, 'g')
    z.run(33, 61, 3, 'g')
    z.run(13, 33, 3, 'g')
    z.puts([(2, 22), (45, 26), (16, 18), (44, 18), (10, 33), (30, 35), (43, 42), (57, 40), (3, 58), (14, 57), (46, 52)], 'S')
    z.puts([(30, 23), (10, 44)], 'a')
    z.puts([(6, 23), (40, 59)], 'h')
    # gantry layer: spawns on the two back landings, pickups on the front bridge and the west wing
    G = [['.'] * W for _ in range(H)]
    for (c, r) in ((20, 7), (39, 7)):
        G[r][c] = 'S'
    G[20][30] = 'a'
    G[14][20] = 'h'
    P.run(17, 22, 26, '2')
    P.run(46, 25, 40, '1', vertical=True)
    P.run(27, 24, 40, '1', vertical=True)
    P.run(33, 24, 40, '1', vertical=True)
    boxes(z, P, ((5, 55), (7, 55), (39, 56), (41, 56), (19, 41), (21, 41)), '0')
    boxes(z, P, ((8, 23), (40, 24), (22, 48), (13, 41), (34, 48), (2, 69)), '5')
    common_paint(z, P, (66, 55, 46, 32, 24, 1), ((7, 22), (44, 21), (14, 40), (42, 33), (56, 66), (24, 66), (36, 62)),
                 ((5, 35), (35, 25), (20, 64), (41, 66), (26, 21), (10, 57), (33, 50), (16, 31)))
    return z, P, G


def zone3():
    z = shell('foundry_3')
    P = Paint(z)
    z.block(4, 4, 20, 16, 'Z')
    z.block(38, 3, 18, 18, 'V')
    z.block(5, 69, 18, 2, 'D')
    z.block(38, 69, 18, 2, 'D')
    z.block(25, 9, 2, 2, 'B')
    z.block(34, 9, 2, 2, 'B')
    z.block(27, 15, 2, 2, 'm')
    z.block(32, 15, 2, 2, 'm')
    # the army: finished robots on their dispatch pads, two blocks of five either side of the aisle
    z.block(21, 27, 4, 20, 'F')
    z.block(35, 27, 4, 20, 'F')
    # ammunition and parts along the walls and between the lanes
    z.block(2, 26, 2, 2, 'm')
    z.block(2, 38, 2, 2, 'm')
    z.block(56, 26, 2, 2, 'm')
    z.block(56, 38, 2, 2, 'm')
    z.block(2, 56, 2, 2, 'k')
    z.block(56, 56, 2, 2, 'k')
    z.block(26, 56, 2, 2, 'm')
    z.block(32, 56, 2, 2, 'm')
    z.block(29, 33, 2, 2, 'p')
    z.puts([(24, 3), (24, 4), (35, 2), (35, 3), (2, 45), (2, 46), (57, 45), (57, 46), (25, 62), (35, 62), (3, 21), (57, 21)], 'c')
    z.puts([(2, 62), (57, 62), (24, 49), (36, 49)], 'b')
    z.puts([(24, 66), (36, 66), (3, 66), (56, 66)], 'n')
    z.puts([(20, 22), (40, 23), (28, 64), (32, 64)], 'x')
    z.run(5, 48, 2, 'g')
    z.run(21, 48, 2, 'g')
    z.run(37, 48, 2, 'g')
    z.run(54, 48, 2, 'g')
    z.run(27, 24, 6, 'g')
    z.puts([(27, 4), (33, 5), (2, 23), (57, 24), (14, 24), (47, 25), (30, 21), (2, 50), (57, 50), (14, 50), (46, 50), (19, 58), (41, 58)], 'S')
    z.puts([(30, 38), (6, 58)], 'a')
    z.puts([(30, 46), (53, 58)], 'h')
    # paint: launch rails and launch lanes from each sled down to its door, keep-clear boxes before the doors
    for c in (11, 16):
        P.run(c, 20, 48, '8', vertical=True)
    for c in (8, 19):
        P.run(c, 20, 48, '9', vertical=True)
    for c in (44, 49):
        P.run(c, 21, 47, '8', vertical=True)
    for c in (41, 52):
        P.run(c, 21, 47, '9', vertical=True)
    P.run(2, 51, 6, '1')
    P.run(53, 51, 5, '1')
    for (c, r) in ((24, 67), (35, 67), (26, 51), (32, 51)):
        P.block(c, r, 2, 2, '0')
    common_paint(z, P, (59, 41, 29, 18, 10, 2), ((7, 22), (52, 22), (14, 40), (45, 40), (3, 66), (56, 66), (24, 58), (36, 58)),
                 ((5, 38), (54, 27), (20, 64), (41, 64), (26, 21), (35, 23), (10, 41), (50, 41)))
    return z, P, None


def check_layers(z, P, G):
    errs = []
    # a buttress (every 8 m) reaches 1.75 m into the room and collides: nothing stands in the two cells before it
    for k in range(4, max(W, H) - 4, 8):
        cells = []
        if k < H - 4:
            cells += [(1, k), (2, k), (W - 2, k), (W - 3, k)]
        if k < W - 4:
            cells += [(k, 1), (k, 2), (k, H - 2), (k, H - 3)]
        for (c, r) in cells:
            if z.at(c, r) not in '.PD':
                errs.append('%r at %d,%d stands in a buttress' % (z.at(c, r), c, r))
    for r in range(H):
        if P.g[r][1] == 'o' and r % 8 not in (7, 0, 1):
            errs.append('monorail row %d meets a buttress' % r)
        for c in range(W):
            if P.g[r][c] != '.' and z.at(c, r) in '#GE':
                errs.append('paint on a wall at %d,%d' % (c, r))
            if G and G[r][c] != '.' and z.at(c, r) != 'Y':
                errs.append('gantry symbol off the bay at %d,%d' % (c, r))
    return errs


def main():
    out = []
    for fn in (zone1, zone2, zone3):
        z, P, G = fn()
        errs, stats = validate(z, WALK, PREFABS, size=((60, 60), (72, 72)))
        errs += check_layers(z, P, G)
        txt = z.text() + '@layer 0\n' + P.text() + '\n'
        if G:
            txt += '@layer %d\n' % DECK_Y + '\n'.join(''.join(r) for r in G) + '\n'
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
