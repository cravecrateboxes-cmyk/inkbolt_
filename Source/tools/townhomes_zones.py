"""Larkspur Glen zone layouts (src/data/zones/townhomes_{1,2}.txt), theme src/data/themes/townhomes.js.

Both zones are 72 x 64. The floor plan holds houses, landmarks, props, fences, cars and the gameplay cells; the
"@layer 0" grid holds the paving and lawns (a lamp on a sidewalk or a tree on a lawn keeps its tile), "@layer 0.32"
the pickups on the ground floors of walk-in houses and "@layer 3.32" the pickups upstairs by the balcony doors.
Town-house lots are 6 x 12 (front porch edge on the street side); S / N in a symbol's name is the side its front
faces. Walk-in houses put a step 0.5 m into the first yard row, so that row stays free of props.
  1 The gated entrance: the approach road outside the wall (the LARKSPUR GLEN sign walls, lamps, beds), the stone
    and iron gate across the boulevard (gatehouse, boom barriers, keypad post, open iron gates, a pedestrian gate),
    the community wall; inside: the boulevard with its planted median, the clubhouse facing Larkspur Lane with the
    fenced pool deck behind it, the mailbox kiosk, a row of town houses facing the lane from the east (rear garage
    lane behind), the north row across the lane (front garages, porches) either side of the Commons green that leads
    to the north gate.
  2 Thistle Court: the court street between two rows of town houses, a cul-de-sac turnaround with a planted island
    at each end, rear garage lanes behind both rows (bins, parked cars, garage aprons), the lot under construction in
    the north row (scaffold, framing, the skip, materials behind a site fence), the park in the south with the
    playground, swings, a gazebo and benches; the entry path from the south gate crosses the park.
Run: python3 tools/townhomes_zones.py [--print]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zonekit as zk  # noqa: E402

W, H = 72, 64
# symbols (mirrors src/data/themes/townhomes.js)
SFACE = {'siding': 'H', 'stucco': 'J', 'brick': 'K', 'garage': 'Q', 'wsiding': '1', 'wstucco': '2', 'wbrick': '3', 'build': '7'}
NFACE = {'siding': 'U', 'stucco': 'V', 'brick': 'X', 'garage': 'Y', 'wsiding': '4', 'wstucco': '5', 'wbrick': '6', 'build': '8'}
WALKIN = set('123456')
HOUSES = set(SFACE.values()) | set(NFACE.values())
FLOOR = set(".-|`!+^'o")              # plan cells you stand on (paint only)
PAVE = set(',;:_=~"')                 # paving layer tiles
LINKS = set('FILDfgjy')               # fence / wall runs
PREFABS = {'R': (17, 6), 'N': (8, 2), 'c': (14, 11), 'O': (12, 6), 'l': (1, 2), 'u': (2, 2), 'M': (4, 3), 'p': (8, 6),
           'i': (4, 2), 'e': (3, 1), 'd': (3, 3), 'Z': (6, 6), 'W': (2, 4), 'w': (2, 1), '&': (2, 1), '@': (3, 6),
           'A': (6, 6), 'B': (2, 1), 'C': (3, 5), 'T': (3, 6), '/': (2, 1), '(': (2, 1)}
for _ch in HOUSES:
    PREFABS[_ch] = (6, 12)


class TZ(zk.Zone):
    def __init__(self, name):
        super().__init__(name, W, H)
        self.pave_g = [['.'] * W for _ in range(H)]
        self.gf = [['.'] * W for _ in range(H)]      # @layer 0.32 (walk-in ground floors)
        self.uf = [['.'] * W for _ in range(H)]      # @layer 3.32 (upstairs)
        self.rect(0, 0, W, H, '#')
        self.lots = []

    def opening(self, c0, r0, w, h):
        self.rect(c0, r0, w, h, '.')

    def paving(self, c0, r0, w, h, ch, over=None):
        for r in range(max(0, r0), min(H, r0 + h)):
            for c in range(max(0, c0), min(W, c0 + w)):
                if over is None or self.pave_g[r][c] in over:
                    self.pave_g[r][c] = ch

    def text(self):
        for r in (1, H - 2):          # no tiles where the gate piers reach into the zone
            for c in range(33, 40):
                self.pave_g[r][c] = '.'
        out = '\n'.join(''.join(row) for row in self.g) + '\n'
        out += '@layer 0\n' + '\n'.join(''.join(row) for row in self.pave_g) + '\n'
        if any(ch != '.' for row in self.gf for ch in row):
            out += '@layer 0.32\n' + '\n'.join(''.join(row) for row in self.gf) + '\n'
        if any(ch != '.' for row in self.uf for ch in row):
            out += '@layer 3.32\n' + '\n'.join(''.join(row) for row in self.uf) + '\n'
        return out

    # ------------------------------------------------------------ houses
    def lot(self, c0, r0, style, face, yard=3, fence='F', pickup=None, up=None):
        """a 6 x 12 lot at (c0, r0) (top-left), front to the S or N, with its front yard (lawn, a path or a driveway
        to the sidewalk, a fence / hedge along the sidewalk with a gap) and the apron behind (garage / back door)"""
        ch = (SFACE if face == 'S' else NFACE)[style]
        self.block(c0, r0, 6, 12, ch)
        self.lots.append((c0, r0, style, face))
        walk = ch in WALKIN
        # door column(s) and the driveway columns (piece x -> cells; N-facing lots are turned a half turn)
        if face == 'S':
            door, drive = [c0 + 1], [c0 + 3, c0 + 4, c0 + 5]
            yr = list(range(r0 + 12, r0 + 12 + yard))
            back = r0 - 1
        else:
            door, drive = [c0 + 4], [c0, c0 + 1, c0 + 2]
            yr = list(range(r0 - 1, r0 - 1 - yard, -1))
            back = r0 + 12
        for r in yr:
            for c in range(c0, c0 + 6):
                self.pave_g[r][c] = ';'
        for r in yr:
            for c in door:
                self.pave_g[r][c] = '_'
        if style == 'garage':
            for r in yr:
                for c in drive:
                    self.pave_g[r][c] = ':'
        if fence and yard >= 2:
            r = yr[-1]
            gaps = set(door) | (set(drive) if style == 'garage' else set())
            for c in range(c0, c0 + 6):
                if c not in gaps and self.g[r][c] == '.':
                    self.g[r][c] = fence
        # a shrub or a small tree in the yard (not in the first row of a walk-in, where its step lies)
        if yard >= 3 and style != 'garage':
            r = yr[1]
            c = c0 + 4 if face == 'S' else c0 + 1
            if self.g[r][c] == '.':
                self.g[r][c] = ')' if (c0 // 6) % 2 else 'z'
        if pickup:
            c = c0 + 3
            (self.gf if pickup[0] == 'g' else self.uf)[r0 + 6][c] = pickup[1]
        if up:
            self.uf[r0 + (3 if face == 'S' else 8)][c0 + 3] = up
        return back

    def row(self, c0, r0, styles, face, yard=3, fence='F', pickups=None):
        for i, s in enumerate(styles):
            p = (pickups or {}).get(i)
            self.lot(c0 + 6 * i, r0, s, face, yard=yard, fence=fence, pickup=p)

    def spawns(self, cands, mind=15):
        """a spawn can at each candidate, nudged to the nearest cell with open floor all round, >= mind m from P and
        3 m from the other cans"""
        P = next((c, r) for r in range(H) for c in range(W) if self.g[r][c] == 'P')
        done = []
        for (c0, r0) in cands:
            best = None
            for rad in range(0, 7):
                for dc in range(-rad, rad + 1):
                    for dr in range(-rad, rad + 1):
                        if max(abs(dc), abs(dr)) != rad:
                            continue
                        c, r = c0 + dc, r0 + dr
                        if not (1 <= c < W - 1 and 1 <= r < H - 1):
                            continue
                        if any(self.g[r + j][c + i] not in FLOOR for i in (-1, 0, 1) for j in (-1, 0, 1)):
                            continue
                        if (c - P[0]) ** 2 + (r - P[1]) ** 2 < mind ** 2 or any((c - a) ** 2 + (r - b) ** 2 < 9 for (a, b) in done):
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

    def dash(self, r, c0, c1, ch='-', every=3):
        for c in range(c0, c1 + 1):
            if c % every != 0 and self.g[r][c] == '.':
                self.g[r][c] = ch

    def dash_v(self, c, r0, r1, ch='|', every=3):
        for r in range(r0, r1 + 1):
            if r % every != 0 and self.g[r][c] == '.':
                self.g[r][c] = ch


def validate(z):
    walk = FLOOR | set('SPEGah')
    errs, stats = zk.validate(z, walk | PAVE | set('Rgj'), PREFABS, size=((70, 74), (60, 66)))   # the gate's lanes are open
    # pickups: the base grid ones plus the walk-in house layers
    na = sum(row.count('a') for G in (z.g, z.gf, z.uf) for row in G)
    nh = sum(row.count('h') for G in (z.g, z.gf, z.uf) for row in G)
    errs = [e for e in errs if not e.startswith('pickups') and 'sealed open cells' not in e]
    if not (2 <= na <= 3 and 2 <= nh <= 3):
        errs.append('pickups a=%d h=%d' % (na, nh))
    # every layer pickup lies inside a walk-in house
    for G in (z.gf, z.uf):
        for r in range(H):
            for c in range(W):
                if G[r][c] in 'ah' and z.g[r][c] not in WALKIN:
                    errs.append('layer pickup at %d,%d not in a walk-in house' % (c, r))
    return errs, stats


# ================================================================ zone 1: the gated entrance
def zone1():
    z = TZ('townhomes_1')
    z.opening(1, 1, W - 2, H - 2)
    z.rect(35, 0, 3, 1, 'G')
    z.rect(35, H - 1, 3, 1, 'E')
    # ---------------- the approach outside the wall (rows 56 .. 62)
    z.paving(1, 51, W - 2, 12, ';')
    z.paving(29, 51, 2, 12, ',')
    z.paving(42, 51, 2, 12, ',')
    z.paving(31, 51, 11, 12, '.', over=';')
    for r in range(56, 62):
        if r % 3:
            z.g[r][36] = '|'
    z.block(19, 58, 8, 2, 'N')
    z.block(46, 58, 8, 2, 'N')
    for (c, r) in ((29, 57), (43, 57), (29, 61), (43, 61)):
        z.put(c, r, 's')
    for (c, r) in ((14, 52), (6, 55), (3, 60), (58, 52), (64, 55), (67, 60), (16, 61), (24, 61), (56, 61), (10, 58), (62, 58)):
        z.put(c, r, 't' if (c + r) % 3 else 'b')
    for c in list(range(17, 28)) + list(range(45, 56)):
        z.paving(c, 60, 1, 1, '"')
    z.put(39, 57, '0')
    # ---------------- the gate (rows 50 .. 55: its iron gates on the wall line, the barriers to the south) and the
    # community wall (row 50)
    z.block(28, 50, 17, 6, 'R')
    z.run(1, 50, 27, 'L')
    z.run(45, 50, 26, 'L')
    for (c0, c1) in ((1, 28), (45, 71)):
        z.paving(c0, 51, c1 - c0, 5, ';')
    z.paving(28, 51, 17, 5, '.', over=';')
    for (c, r) in ((8, 53), (20, 53), (52, 53), (64, 53)):
        z.put(c, r, 'z')
    # ---------------- the boulevard (cols 31 .. 41: lanes, the median 35 .. 37), sidewalks 29-30 and 42-43
    z.paving(29, 27, 2, 18, ',')
    z.paving(42, 27, 2, 18, ',')
    for r0 in (30, 38):
        z.block(35, r0, 3, 6, '@')
    for r in range(27, 45):
        for c in (33, 39):
            if r % 3 and z.g[r][c] == '.':
                z.g[r][c] = '|'
    for c in range(31, 35):
        z.put(c, 28, '+', over='.|')
    z.puts(((32, 36), (40, 33)), 'o')
    # ---------------- Larkspur Lane (rows 20 .. 26), sidewalks 19 and 27-28
    z.paving(1, 19, W - 2, 1, ',')
    z.paving(1, 27, 28, 2, ',')
    z.paving(44, 27, 27, 2, ',')
    for c in range(2, W - 2):
        if c % 3 and z.g[23][c] == '.' and not 31 <= c <= 41:
            z.g[23][c] = '`'
    for r in range(20, 27):
        for c in (29, 30, 42, 43):
            z.g[r][c] = "'" if z.g[r][c] == '.' else z.g[r][c]
    # ---------------- the north row (lots 6 x 12 at rows 5 .. 16, fronts south), the Commons green to the north gate
    z.paving(1, 1, W - 2, 4, '.')
    z.row(3, 5, ['garage', 'wsiding', 'stucco', 'brick'], 'S', yard=2, pickups={1: ('g', 'h')})
    z.row(46, 5, ['siding', 'garage', 'wbrick', 'stucco'], 'S', yard=2, pickups={2: ('u', 'a')})
    z.paving(27, 1, 19, 18, ';')
    z.paving(35, 1, 3, 18, '_')
    z.paving(27, 3, 19, 1, '_')
    for (c, r) in ((29, 6), (43, 6), (29, 13), (43, 13)):
        z.put(c, r, 't')
    for (c, r) in ((33, 9), (39, 9), (33, 15), (39, 15)):
        z.put(c, r, 's')
    z.block(30, 10, 2, 1, 'B')
    z.block(41, 10, 2, 1, 'B')
    z.put(32, 4, 'n')
    z.puts(((28, 17), (44, 17)), 'z')
    for r in range(4, 17):
        for c in (27, 45):
            if z.g[r][c] == '.':
                z.g[r][c] = 'D'
    # rear lane behind the north row (rows 1 .. 4): garage aprons, bins, a parked car
    z.paving(3, 4, 24, 1, ':')
    z.paving(46, 4, 24, 1, ':')
    z.block(10, 1, 2, 1, '/')
    z.block(52, 1, 2, 1, '/')
    z.block(19, 1, 5, 3, 'C')
    z.block(60, 1, 5, 3, 'C')
    # parked cars along Larkspur Lane, a driveway car in front of each garage
    for (c, r) in ((5, 24), (48, 24), (58, 20), (17, 20)):
        z.block(c, r, 5, 3, 'C')
    # ---------------- the clubhouse (rows 29 .. 39, front north to the lane) and its pool deck (rows 40 .. 49)
    z.block(8, 29, 14, 11, 'c')
    z.paving(1, 29, 28, 11, ';')
    z.paving(8, 29, 14, 11, '.')                        # the clubhouse has its own floor
    z.paving(1, 40, 27, 10, '=')
    z.block(8, 42, 12, 6, 'O')
    z.paving(8, 42, 12, 6, '.')                         # the pool's own coping and water
    for c in (9, 11, 13, 15, 17):
        z.block(c, 48, 1, 2, 'l')
    for c in (23, 25):
        z.block(c, 41, 1, 2, 'l')
    z.block(2, 41, 2, 2, 'u')
    z.block(3, 46, 2, 2, 'u')
    z.block(22, 45, 2, 2, 'u')
    z.put(21, 40, 'k')
    # pool fence: along row 40 either side of the clubhouse, down col 27 with a gate
    for c in range(1, 8):
        z.put(c, 40, 'f')
    for c in range(22, 28):
        z.put(c, 40, 'f')
    for r in range(41, 50):
        z.put(27, r, 'j' if r == 44 else 'f')
    z.paving(27, 44, 1, 1, '_')
    z.paving(28, 44, 1, 1, ',')
    # beside the clubhouse: shrubs, a lamp, the mailbox kiosk on the corner
    z.block(24, 30, 4, 3, 'M')
    z.paving(23, 29, 6, 5, ',')
    for (c, r) in ((3, 31), (3, 37), (24, 37)):
        z.put(c, r, 't')
    z.puts(((6, 31), (6, 37), (23, 35)), 's')
    z.put(2, 34, '$')
    # ---------------- the east row (lots at rows 31 .. 42, fronts north to the lane), rear lane rows 43 .. 49
    z.row(46, 31, ['brick', 'wstucco', 'siding', 'stucco'], 'N', yard=2, pickups={1: ('u', 'h')})
    z.paving(44, 29, 2, 22, ';')
    z.paving(46, 43, 24, 1, ':')
    z.block(62, 45, 3, 5, 'C')
    z.block(47, 45, 2, 1, '/')
    z.block(58, 45, 2, 1, '/')
    z.puts(((56, 47), (68, 44)), '[')
    z.put(45, 33, 'b')
    # spawns, the player, pickups
    z.put(36, 60, 'P')
    z.spawns(((8, 22), (24, 22), (50, 22), (64, 22), (36, 13), (36, 5), (12, 2), (58, 2), (56, 47), (66, 47),
              (2, 47), (25, 47), (36, 25)))
    for (c, r, ch) in ((44, 21, 'a'), (20, 45, 'a')):
        z.put(c, r, ch)
    return z


# ================================================================ zone 2: Thistle Court
def zone2():
    z = TZ('townhomes_2')
    z.opening(1, 1, W - 2, H - 2)
    z.rect(35, 0, 3, 1, 'G')
    z.rect(35, H - 1, 3, 1, 'E')
    # ---------------- the park (rows 49 .. 62): lawns, paths, the playground, swings, the gazebo, benches
    z.paving(1, 49, W - 2, 14, ';')
    z.paving(35, 47, 3, 16, '_')
    z.paving(4, 55, 64, 1, '_')
    z.block(5, 49, 8, 6, 'p')
    z.paving(4, 49, 10, 7, '~')
    z.block(15, 52, 4, 2, 'i')
    z.paving(14, 51, 6, 4, '~')
    z.block(15, 57, 3, 1, 'e')
    z.block(5, 57, 3, 3, 'd')
    z.paving(4, 56, 5, 5, '~')
    z.paving(14, 56, 5, 3, '~')
    z.puts(((10, 58), (12, 60)), 'r')
    z.block(52, 50, 6, 6, 'Z')
    z.paving(51, 49, 8, 8, '_')
    for (c, r) in ((40, 53), (46, 58), (30, 58), (22, 53), (62, 59), (66, 51), (25, 61), (58, 61)):
        z.block(c, r, 2, 1, 'B')
    for (c, r) in ((24, 50), (44, 50), (28, 59), (48, 61), (62, 53), (68, 57), (2, 61), (20, 61), (10, 61)):
        z.put(c, r, 't' if (c + r) % 4 else 'z')
    for (c, r) in ((34, 52), (38, 52), (34, 59), (38, 59), (30, 54), (60, 56)):
        z.put(c, r, 's')
    z.puts(((33, 50), (39, 57), (55, 57)), 'n')
    z.put(20, 50, '9')
    # hedge between the south lane and the park, open at the paths
    for c in range(1, W - 1):
        if c not in (2, 3, 35, 36, 37, 68, 69) and z.g[48][c] == '.':
            z.g[48][c] = 'D'
    # ---------------- the south row (lots at rows 30 .. 41, fronts north to the court), south rear lane rows 42 .. 47
    z.row(15, 30, ['brick', 'siding', 'garage', 'stucco'], 'N', yard=2)
    z.row(41, 30, ['wsiding', 'stucco', 'brick'], 'N', yard=2, pickups={0: ('g', 'h')})
    z.paving(39, 28, 2, 14, '_')
    z.paving(15, 42, 45, 1, ':')
    for (c, r) in ((22, 44), (50, 44)):
        z.block(c, r, 5, 3, 'C')
    z.block(30, 43, 3, 5, 'C')
    for c in (17, 47):
        z.block(c, 43, 2, 1, '/')
    z.puts(((28, 43), (55, 43)), '<')
    z.puts(((38, 46), (60, 44)), '[')
    z.put(14, 44, '$')
    # the pocket gardens at the row ends (paths from the park lane round to the turnarounds)
    z.paving(1, 31, 14, 17, ';')
    z.paving(59, 31, 12, 17, ';')
    z.paving(7, 31, 2, 17, '_')
    z.paving(63, 31, 2, 17, '_')
    for (c, r) in ((3, 34), (12, 34), (3, 41), (12, 41), (61, 34), (68, 34), (61, 41), (68, 41)):
        z.put(c, r, 't')
    z.block(10, 38, 2, 1, 'B')
    z.block(66, 38, 2, 1, 'B')
    # ---------------- Thistle Court (rows 20 .. 26) with a turnaround at each end (rows 17 .. 30)
    z.paving(9, 19, 54, 1, ',')
    z.paving(15, 27, 44, 1, ',')
    for c in range(16, 56):
        if c % 3 and z.g[23][c] == '.':
            z.g[23][c] = '-'
    z.block(4, 20, 6, 6, 'A')
    z.block(62, 20, 6, 6, 'A')
    z.paving(1, 15, 8, 2, ',')
    z.paving(63, 15, 8, 2, ',')
    z.paving(1, 29, 14, 2, ',')
    z.paving(59, 29, 12, 2, ',')
    z.puts(((15, 18), (56, 18)), 'v')
    z.put(17, 27, '0')
    for (c, r) in ((12, 18), (60, 28), (28, 19), (46, 19), (28, 27), (46, 27)):
        if z.g[r][c] == '.':
            z.put(c, r, 's')
    z.puts(((10, 28), (62, 18)), ']')
    for (c, r) in ((19, 24), (43, 20)):
        z.block(c, r, 5, 3, 'C')
    # ---------------- the north row (lots at rows 5 .. 16, fronts south): the lot under construction among them
    z.row(9, 5, ['stucco', 'garage', 'wbrick', 'siding'], 'S', yard=2, pickups={2: ('u', 'a')})
    z.lot(33, 5, 'build', 'S', yard=2, fence=None)
    z.row(39, 5, ['brick', 'wstucco', 'garage', 'stucco'], 'S', yard=2, pickups={1: ('g', 'a')})
    # the site in front of the build: a site fence round the yard, the skip, materials, the sign
    for r in (17, 18):
        for c in range(33, 39):
            z.pave_g[r][c] = ':'
    z.block(33, 20, 4, 2, 'W')
    z.block(37, 17, 2, 1, 'w')
    z.put(37, 18, 'x')
    z.put(38, 18, 'q')
    z.block(33, 19, 2, 1, '&')
    z.put(35, 3, '%')
    # end gardens of the north row (cols 1 .. 8 and 63 .. 70)
    z.paving(1, 5, 8, 10, ';')
    z.paving(63, 5, 8, 10, ';')
    for (c, r) in ((3, 7), (6, 12), (66, 7), (68, 12)):
        z.put(c, r, 't')
    z.block(2, 10, 2, 1, '(')
    z.block(65, 10, 2, 1, '(')
    # the north rear lane (rows 1 .. 4): garage aprons, bins, cars, the exit
    z.paving(9, 4, 54, 1, ':')
    for c in (12, 46):
        z.block(c, 1, 2, 1, '/')
    z.puts(((25, 1), (59, 1)), '<')
    z.block(16, 1, 5, 3, 'C')
    z.puts(((28, 3), (42, 2)), '[')
    # spawns, the player, pickups
    z.put(36, 61, 'P')
    z.spawns(((24, 23), (40, 23), (54, 23), (8, 27), (64, 27), (36, 2), (6, 2), (66, 2), (36, 45), (12, 45),
              (60, 45), (44, 53), (28, 52)))
    z.put(66, 60, 'h')
    z.put(6, 27, 'h')
    return z


def main():
    out = []
    for fn in (zone1, zone2):
        z = fn()
        errs, stats = validate(z)
        out.append((z, errs, stats))
    ok = zk.write(out, check_only='--check' in sys.argv)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
