"""Downtown Standoff zone layouts (src/data/zones/downtown_{1,2,3}.txt), theme src/data/themes/downtown.js.

Every zone is 64 x 56: a 10-cell band of buildings behind the west and east walls holds the walk-in shops (7 x 8 m
rooms behind a 7-cell frontage: window, window, three doorway cells 'n', window, window), the street area between.
The floor plan holds buildings, shops, props, vehicles, lane paint and the gameplay cells; the "@layer 0" grid holds
the sidewalk and plaza paving (so a lamp or a bench on the sidewalk keeps its paving) and the pickups inside shops.
  1 Commerce Avenue: a six-lane avenue with a planted median, a police checkpoint across it (jersey barriers, a
    sandbag nest, the checkpoint booth on the median, a box truck on its side over the northbound lanes), parked and
    abandoned cars, a crashed bus; Hollis Pharmacy, Lula's Diner (west), Voltaic Electronics, Corner Mart 24 (east).
  2 Liberty Square: a paved square round the Founders monument inside a ring road, sandbag nests and wire round it;
    Inkwell Books, Sal's Barber Shop (west), Fieldhouse Sports (east).
  3 Market Street: a pedestrian market street with a stalled tram on its rails and rows of stalls, a block of
    buildings down the middle with an alley through it, a service lane behind; Kessler Hardware, Lucky 7 Pawn (west),
    Bubbles Laundromat (east, on the service lane).
Run: python3 tools/downtown_zones.py [--print]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zonekit as zk  # noqa: E402

W, H = 64, 56
ROOMS = '567890&$%@'
FLOOR = '.-|~!zZ_:ox*='
WALK = set(FLOOR) | set('n') | set(ROOMS)
PREFABS = {'b': (2, 1), 'u': (4, 2), 'U': (4, 2), 'k': (2, 3), 'Y': (3, 2), 'I': (3, 2), 'C': (3, 5), 'H': (3, 5), 'W': (3, 5),
           'A': (3, 5), 'Q': (3, 5), 'T': (3, 6), 'X': (3, 8), 'B': (3, 12), 'O': (4, 8), 'v': (1, 2), 'K': (2, 4), 'N': (3, 3),
           'c': (2, 1), 'j': (2, 1), 'L': (2, 2), 'y': (2, 1), 'R': (6, 4), 'M': (8, 8), 'V': (3, 14)}
for _ch in ROOMS:
    PREFABS[_ch] = (7, 8)


class DZ(zk.Zone):
    """a zone with its paving layer (sidewalks ',' and plaza ';') and the pickups inside shops"""

    def __init__(self, name):
        super().__init__(name, W, H)
        self.pave_g = [['.'] * W for _ in range(H)]
        self.rect(0, 0, W, H, '#')

    def paving(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.pave_g[r][c] = ch

    def opening(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '.')

    def shop(self, side, r0, ch, pickup=None):
        """a walk-in shop in the west ('W') or east ('E') band: room rows r0 .. r0 + 6, doorway rows r0 + 2 .. r0 + 4"""
        if side == 'W':
            self.rect(1, r0, 8, 7, ch)
            for r in range(r0 + 2, r0 + 5):
                self.g[r][9] = 'n'
            pc = 8
        else:
            self.rect(W - 9, r0, 8, 7, ch)
            for r in range(r0 + 2, r0 + 5):
                self.g[r][W - 10] = 'n'
            pc = W - 9
        if pickup:
            self.pave_g[r0 + 3][pc] = pickup

    def spawns(self, cands):
        """a spawn can at each candidate, nudged to the nearest cell with open floor all round, >= 14 m from P and
        3 m from the other cans"""
        P = next((c, r) for r in range(H) for c in range(W) if self.g[r][c] == 'P')
        done = []
        for (c0, r0) in cands:
            best = None
            for rad in range(0, 6):
                for dc in range(-rad, rad + 1):
                    for dr in range(-rad, rad + 1):
                        if max(abs(dc), abs(dr)) != rad:
                            continue
                        c, r = c0 + dc, r0 + dr
                        if not (1 <= c < W - 1 and 1 <= r < H - 1):
                            continue
                        if any(self.g[r + j][c + i] not in FLOOR for i in (-1, 0, 1) for j in (-1, 0, 1)):
                            continue
                        if (c - P[0]) ** 2 + (r - P[1]) ** 2 < 15 ** 2 or any((c - a) ** 2 + (r - b) ** 2 < 9 for (a, b) in done):
                            continue
                        best = (c, r)
                        break
                    if best:
                        break
                if best:
                    break
            assert best, '%s: no spawn cell near %d,%d' % (self.name, c0, r0)
            self.g[best[1]][best[0]] = 'S'
            done.append(best)

    def text(self):
        out = '\n'.join(''.join(row) for row in self.g) + '\n'
        out += '@layer 0\n' + '\n'.join(''.join(row) for row in self.pave_g) + '\n'
        return out

    def dashes(self, c, r0, r1, ch='|', vertical=True):
        for k in range(r0, r1 + 1):
            if k % 3 != 0:
                if vertical:
                    if self.g[k][c] == '.':
                        self.g[k][c] = ch
                elif self.g[c][k] == '.':
                    self.g[c][k] = ch


def street_base(z, gate_c=31, entry_c=31):
    """bands of building behind the west / east walls, the open street area, sidewalks along all four sides"""
    z.opening(10, 1, W - 20, H - 2)
    z.rect(gate_c, 0, 3, 1, 'G')
    z.rect(entry_c, H - 1, 3, 1, 'E')
    z.paving(10, 1, W - 20, 3, ',')
    z.paving(10, H - 4, W - 20, 3, ',')


def door_rows(z, side):
    """rows of the shop doorways on one side (kept clear on the sidewalk in front)"""
    col = 9 if side == 'W' else W - 10
    return {r for r in range(H) if z.g[r][col] == 'n'}


def sidewalk_props(z, side, c_curb, c_mid, rows_lamp, rows_tree, furn, lamp_ch):
    """lamps and trees on the curb, street furniture along the sidewalk, never in front of a doorway"""
    clear = set()
    for r in door_rows(z, side):
        clear |= {r - 1, r, r + 1}
    for r in rows_lamp:
        if r not in clear:
            z.put(c_curb, r, lamp_ch)
    for r in rows_tree:
        if r not in clear:
            z.put(c_curb, r, 't')
    for (r, ch) in furn:
        if r not in clear:
            z.put(c_mid, r, ch)


# ================================================================ zone 1: Commerce Avenue
def zone1():
    z = DZ('downtown_1')
    street_base(z)
    z.shop('W', 4, '5')
    z.shop('W', 30, '6')
    z.shop('E', 14, '7')
    z.shop('E', 38, '8', pickup='h')
    z.paving(10, 1, 5, H - 2, ',')
    z.paving(49, 1, 5, H - 2, ',')
    z.paving(29, 10, 6, 37, ';')                       # median
    # lane paint: parking-lane lines, lane dashes, median edge double yellow, crosswalks and stop lines
    for c in (18, 45):
        for r in range(11, 44):
            if z.g[r][c] == '.' and r % 2:
                z.g[r][c] = '|'
    for c in (22, 25, 38, 41):
        z.dashes(c, 11, 43)
    for c in (28, 35):
        for r in range(10, 47):
            z.g[r][c] = '!'
    for rr in (6, 7, 8, 47, 48, 49):
        for c in range(15, 49):
            z.g[rr][c] = 'Z'
    for c in range(19, 28):
        z.g[9][c] = '_'
    for c in range(36, 45):
        z.g[46][c] = '_'
    for (c, r) in ((20, 12), (40, 24), (21, 40), (44, 20)):
        z.g[r][c] = 'o'
    # median: trees and lamps, the checkpoint booth (landmark) across it
    for r in (12, 18, 36, 42):
        z.put(31, r, 't')
        z.put(32, r + 3, 'e' if (r // 6) % 2 else 'w')     # median lamps reach over the lanes
    z.block(29, 26, 6, 4, 'R')
    z.paving(29, 26, 6, 4, '.')                        # no paving under the checkpoint
    # sidewalks: signals at the crosswalks, lamps, trees, furniture, a bus shelter, a newsstand, a bike rack
    z.put(14, 5, '3')
    z.put(49, 9, '4')
    z.put(14, 50, '3')
    z.put(49, 46, '4')
    sidewalk_props(z, 'W', 14, 11, (14, 26, 38), (11, 19, 29, 44), ((15, 'm'), (21, 'f'), (27, 'm'), (41, 'f'), (45, 'm')), 'e')
    sidewalk_props(z, 'E', 49, 52, (12, 24, 36), (10, 22, 31, 44), ((11, 'f'), (25, 'm'), (34, 'm'), (47, 'f')), 'w')
    z.block(13, 21, 2, 4, 'u')
    z.block(50, 27, 3, 2, 'k')
    z.block(51, 4, 2, 4, 'K')
    z.block(11, 47, 2, 1, 'b')
    # parked cars along both curbs, abandoned and crashed ones in the lanes
    for (c, r, ch) in ((15, 11, 'C'), (15, 17, 'A'), (15, 34, 'C'), (15, 40, 'T'),
                       (46, 10, 'C'), (46, 21, 'T'), (46, 31, 'C'), (46, 39, 'H'),
                       (19, 13, 'H'), (23, 18, 'W'), (36, 34, 'Q'), (42, 39, 'C'), (36, 10, 'A'), (39, 13, 'X')):
        z.block(c, r, PREFABS[ch][0], PREFABS[ch][1], ch, over='.|!_o')
    z.block(25, 31, 3, 12, 'B', over='.|!_o')           # the crashed bus, nose into the median
    z.puts(((22, 23), (27, 30), (22, 36)), 'x', over='.|')
    z.puts(((24, 24), (26, 17)), '*', over='.|')
    z.block(16, 47, 1, 2, 'v', over='.ZoZ')
    # the checkpoint line: barriers and a nest across the west lanes, the overturned truck across the east lanes
    for c in (15, 19, 23):
        z.block(c, 28, 2, 1, 'j', over='.|!')
    z.block(19, 24, 3, 3, 'N', over='.|')
    z.run(25, 28, 3, 's', over='.|')
    z.block(37, 27, 8, 4, 'O', over='.|')
    z.puts(((36, 31), (45, 27), (47, 30)), 'g', over='.|!')
    z.run(46, 29, 3, 's', over='.|')
    z.put(17, 26, 'F', over='.')
    z.block(26, 26, 2, 1, 'c', over='.|')
    z.puts(((28, 31), (35, 25), (16, 30)), 'q', over='.|!')
    z.run(36, 25, 2, 'p', over='.|!')
    # sandbags in front of the pharmacy, rubble at the corners
    z.run(10, 13, 3, 's', over='.')
    z.puts(((52, 15), (11, 39)), 'd')
    z.put(30, 52, 'P')
    for (c, r) in ((12, 3), (51, 3)):
        z.put(c, r, 'D')
    z.spawns(((20, 4), (43, 4), (17, 22), (27, 13), (40, 22), (31, 7), (12, 33), (51, 41), (21, 36), (43, 34), (30, 3), (47, 16)))
    for (c, r, ch) in ((12, 27, 'a'), (51, 20, 'h'), (24, 50, 'a'), (39, 51, 'h')):
        z.put(c, r, ch, over='.Z')
    return z


# ================================================================ zone 2: Liberty Square
def zone2():
    z = DZ('downtown_2')
    street_base(z)
    z.shop('W', 8, '9')
    z.shop('W', 38, '0', pickup='a')
    z.shop('E', 22, '&')
    z.paving(10, 1, 4, H - 2, ',')
    z.paving(50, 1, 4, H - 2, ',')
    z.paving(20, 10, 24, 36, ';')                      # the square
    # ring road paint: centre lines, crosswalks onto the square
    for r in range(11, 45):
        if r % 2:
            z.g[r][16] = '|'
            z.g[r][47] = '|'
    for c in range(15, 49):
        if c % 2:
            z.g[6][c] = '-'
            z.g[49][c] = '-'
    for c in range(29, 35):
        for r in range(4, 10):
            z.g[r][c] = 'z'
        for r in range(46, 52):
            z.g[r][c] = 'z'
    for r in range(26, 30):
        for c in range(14, 20):
            z.g[r][c] = 'Z'
        for c in range(44, 50):
            z.g[r][c] = 'Z'
    # the monument, trees, lamps and benches round it
    z.block(28, 24, 8, 8, 'M')
    z.paving(28, 24, 8, 8, '.')                        # the monument stands on its own granite
    for (c, r) in ((22, 12), (41, 12), (22, 43), (41, 43), (22, 21), (41, 21), (22, 34), (41, 34), (26, 17), (37, 17), (26, 38), (37, 38)):
        z.put(c, r, 't')
    for (c, r, ch) in ((21, 28, 'e'), (42, 28, 'w')):
        z.put(c, r, ch)
    for (c, r) in ((29, 21), (33, 21), (29, 34), (33, 34)):
        z.block(c, r, 2, 1, 'b')
    z.block(23, 39, 3, 2, 'k')
    # battle: sandbag nests at the square's north corners, sandbags and tape round the monument, wire on the lanes
    z.block(24, 13, 3, 3, 'N')
    z.block(37, 13, 3, 3, 'N')
    z.block(30, 14, 3, 3, 'N')
    for (c0, r, n) in ((25, 23, 3), (35, 23, 3), (25, 32, 3), (36, 32, 3)):
        z.run(c0, r, n, 's')
    z.run(28, 36, 8, 'p')
    z.run(28, 19, 8, 'p')
    z.run(15, 41, 5, 'r', over='.|')
    z.run(44, 14, 5, 'r', over='.|')
    z.puts(((17, 20), (46, 37), (18, 47), (45, 8), (25, 7)), 'g', over='.|-')
    z.puts(((24, 26), (39, 29), (21, 16)), 'F')
    z.block(38, 40, 2, 1, 'c')
    z.block(23, 30, 2, 1, 'c')
    z.puts(((31, 18), (34, 41)), 'd')
    z.puts(((30, 12), (39, 25), (24, 34), (32, 43)), 'x')
    z.puts(((26, 28), (37, 26)), '*')
    # vehicles: on the ring road and the curbs
    for (c, r, ch) in ((14, 12, 'C'), (14, 31, 'W'), (14, 18, 'Q'), (45, 30, 'H'), (45, 16, 'W'), (45, 38, 'T'), (45, 45, 'C'),
                       (36, 4, 'A'), (21, 4, 'C'), (38, 46, 'C'), (17, 34, 'C'), (20, 46, 'X')):
        w_, d_ = PREFABS[ch]
        if ch in ('X',):
            w_, d_ = d_, w_          # turned along the E-W lane
        z.block(c, r, w_, d_, ch, over='.|-zZ')
    z.block(36, 50, 1, 2, 'v', over='.-z')
    z.block(37, 50, 1, 2, 'v', over='.-z')
    # sidewalks
    z.put(13, 4, '3')
    z.put(50, 51, '4')
    sidewalk_props(z, 'W', 13, 11, (16, 33, 47), (5, 20, 30, 50), ((18, 'm'), (24, 'f'), (34, 'm'), (46, 'f')), 'e')
    sidewalk_props(z, 'E', 50, 52, (8, 18, 34, 44), (12, 31, 40, 48), ((6, 'm'), (15, 'f'), (37, 'm')), 'w')
    z.block(51, 44, 2, 4, 'K')
    z.block(12, 25, 2, 4, 'u')
    z.put(30, 53, 'P')
    z.spawns(((20, 5), (43, 5), (16, 9), (47, 11), (27, 14), (35, 11), (21, 25), (42, 24), (17, 28), (47, 25), (12, 2), (51, 2)))
    for (c, r, ch) in ((21, 31, 'a'), (42, 44, 'h'), (11, 52, 'h'), (52, 21, 'a')):
        z.put(c, r, ch, over='.')
    return z


# ================================================================ zone 3: Market Street
def zone3():
    z = DZ('downtown_3')
    street_base(z, gate_c=22, entry_c=22)
    z.shop('W', 6, '$')
    z.shop('W', 34, '%')
    z.shop('E', 14, '@', pickup='h')
    # the middle block (two buildings with an alley through) and the service lane behind it
    z.rect(36, 8, 8, 18, '#')
    z.rect(36, 30, 8, 18, '#')
    z.paving(10, 1, 4, H - 2, ',')
    z.paving(32, 1, 4, H - 2, ',')
    z.paving(36, 1, 8, 7, ',')
    z.paving(36, 48, 8, 7, ',')
    z.paving(36, 26, 8, 4, ',')
    z.paving(50, 1, 4, H - 2, ',')
    z.paving(14, 1, 18, 3, ',')
    z.paving(14, 52, 18, 3, ',')
    # the market street: rails down the middle, the tram, stall rows either side of the track
    for r in range(4, H - 4):
        z.g[r][23] = '='
    z.block(22, 20, 3, 14, 'V', over='.=')
    for r0 in (8, 15, 36, 43):
        z.block(15, r0, 2, 3, 'I')
        z.block(17, r0, 2, 3, 'Y')
    for r0 in (9, 16, 37, 44):
        z.block(27, r0, 2, 3, 'I')
        z.block(29, r0, 2, 3, 'Y')
    for (c, r) in ((16, 22), (19, 28), (27, 23), (29, 33)):
        z.block(c, r, 2, 1, 'c')
    z.puts(((20, 9), (25, 47), (18, 47), (30, 21)), 'D')
    z.puts(((21, 15), (26, 39)), 'F')
    z.block(15, 26, 2, 2, 'L')
    z.puts(((19, 18), (27, 30), (21, 41), (25, 6)), 'x')
    z.puts(((17, 31), (28, 15), (20, 48)), '*')
    # battle: a sandbag line across the street at the tram, a nest at the north end, hedgehogs, wire
    z.run(14, 32, 5, 's')
    z.run(26, 32, 6, 's')
    z.block(17, 4, 3, 3, 'N')
    z.block(27, 4, 3, 3, 'N')
    z.puts(((21, 36), (25, 18), (14, 47), (31, 49)), 'g')
    z.run(14, 50, 6, 'r')
    z.run(26, 50, 6, 'r')
    # sidewalks (west and middle-block fronts): lamps, trees, furniture
    sidewalk_props(z, 'W', 13, 11, (16, 30, 46), (4, 24, 50), ((19, 'm'), (28, 'f'), (43, 'm')), 'e')
    for (c, r, ch) in ((32, 12, 'w'), (32, 28, 'w'), (32, 44, 'w'), (34, 20, 't'), (34, 38, 't'), (33, 6, 'f'), (33, 49, 'm')):
        z.put(c, r, ch)
    z.block(33, 30, 2, 4, 'K')
    z.block(11, 21, 2, 1, 'b')
    z.block(11, 52, 2, 1, 'y')
    # the service lane: trucks at the back doors, bins, pallets, drums, a van, a burnt car
    z.block(45, 32, 3, 8, 'X')
    z.block(45, 10, 3, 6, 'T')
    z.block(45, 42, 3, 5, 'W')
    z.block(48, 22, 2, 1, 'y')
    z.block(48, 36, 2, 1, 'y')
    z.block(44, 27, 2, 2, 'L')
    z.puts(((44, 20), (49, 45), (44, 9)), 'D')
    z.put(47, 18, 'd')
    for (c, r, ch) in ((50, 12, 'w'), (50, 28, 'w'), (50, 44, 'w'), (52, 6, 'f'), (52, 34, 'm'), (52, 49, 't')):
        z.put(c, r, ch)
    z.block(46, 4, 1, 2, 'v')
    z.block(47, 4, 1, 2, 'v')
    z.block(14, 39, 1, 2, 'v')
    z.put(23, 53, 'P')
    z.spawns(((14, 12), (31, 17), (20, 2), (40, 4), (48, 6), (48, 29), (40, 27), (30, 40), (14, 30), (21, 22), (25, 9), (52, 25)))
    for (c, r, ch) in ((19, 26, 'a'), (51, 40, 'h'), (33, 52, 'a')):
        z.put(c, r, ch, over='.')
    return z


def check(z):
    """zonekit.validate on the floor plan (pickups counted with the shop pickups of the paving layer)"""
    errs, stats = zk.validate(z, WALK, PREFABS)
    na = sum(r.count('a') for r in z.g) + sum(r.count('a') for r in z.pave_g)
    nh = sum(r.count('h') for r in z.g) + sum(r.count('h') for r in z.pave_g)
    errs = [e for e in errs if not e.startswith('pickups')]
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    return z, errs, stats


if __name__ == '__main__':
    ok = zk.write([check(zone1()), check(zone2()), check(zone3())])
    sys.exit(0 if ok else 1)
