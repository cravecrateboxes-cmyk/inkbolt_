"""Glimmerdeep Colliery zone layouts (src/data/zones/gemmine_{1,2}.txt). Run from Source/: python3 tools/gemmine_zones.py

Zone 1, No. 3 Seam (68 x 70): the working coal seam. A 12 m haulage gallery runs from the entry (south) to the exit
(north) between two lines of coal pillars, steel arch sets every 4 m, two tracks with carts; the ore chute stands over
the east track at the north end, fed by the raised conveyor catwalk from the north-east coal face (face conveyor along
the east wall). West: the west heading's coal face with gem veins, roof jacks and cribs, a timbered drift through the
big west pillar, the haulage winch house in its niche; east: a timbered drift east-west through the east pillar,
the south-east district. The auxiliary fan in the gallery pushes air up its riser into the vent duct along the roof.
Grids: the floor plan, "@layer 0" (rails, wall codes) and "@layer 9" (roof fittings: vent duct, lamp strings).

Zone 2, the Glimmer Vault (70 x 72): a vast cavern. The Gem Heart in the middle, the mining gallery (4.8 m) along the
west wall and another along the north wall, timber platforms (2.4 m), rock ledges with ramps (1.4 m), crystal spires,
clusters and clumps, the chasm along the east wall with the hoist at its lip, the sorting / cutting station in the
south-east on plank decking, a track from the entry to the station. Grids: the floor plan, "@layer 0" (rails, decking,
wall codes) and "@layer 18" (the roof).

Wall codes (on wall cells of the "@layer 0" grid; tools read them through the theme's wall chooser):
  zone 1: 1 ruby / 2 emerald / 3 sapphire / 4 diamond vein in the coal, 8 plain coal seam, 5 6 7 signs (seam, haulage,
          gem vein)
  zone 2: 1 2 3 4 vein modules (ruby, emerald, sapphire, diamond), 9 the chasm edge
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zonekit import Zone, validate, rects, OUT  # noqa: E402

WALK = set('.-AqpCkY') - set('Ck')    # validation walkable set (arch cells, drift tunnels; rails live in layer 0)
WALK |= set('AY')
PREFABS = {'Y': (6, 1), 'A': (12, 1), 'C': (1, 2), 'O': (2, 2), 'X': (2, 2), 'w': (2, 2), 'd': (2, 2), 'Z': (10, 8),
           'B': (20, 3), 'W': (6, 5), 'F': (4, 2), 'H': (12, 12), 'N': (16, 4), 'M': (6, 4), 'R': (8, 4), 'Q': (2, 2),
           'V': (3, 3), 'D': (2, 2), 'J': (2, 2), 'K': (2, 1), 'T': (2, 1), 'U': (4, 4)}


class Layer:
    def __init__(self, z):
        self.z = z
        self.g = [['.'] * z.w for _ in range(z.h)]

    def put(self, c, r, ch):
        self.g[r][c] = ch

    def run(self, c0, r0, n, ch, vertical=False):
        for k in range(n):
            self.put(c0, r0 + k, ch) if vertical else self.put(c0 + k, r0, ch)

    def block(self, c0, r0, w, h, ch):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                self.put(c, r, ch)

    def text(self):
        return '\n'.join(''.join(row) for row in self.g) + '\n'


def shell(name, w, h, gate):
    z = Zone(name, w, h)
    z.rect(0, 0, w, 1, '#')
    z.rect(0, h - 1, w, 1, '#')
    z.rect(0, 0, 1, h, '#')
    z.rect(w - 1, 0, 1, h, '#')
    for k in range(3):
        z.g[0][gate + k] = 'G'
        z.g[h - 1][gate + k] = 'E'
    return z


def codes(L, z, cells, ch):
    for (c, r) in cells:
        assert z.at(c, r) == '#', (z.name, c, r, z.at(c, r))
        L.put(c, r, ch)


# ================================================================ zone 1: No. 3 Seam
def zone1():
    W, H = 68, 70
    z = shell('gemmine_1', W, H, 32)
    L0, L9 = Layer(z), Layer(z)
    # ---- pillars: the gallery's west line (cols 19..26) and east line (cols 39..46)
    for (r0, r1) in ((1, 9), (14, 23), (28, 36), (48, 56)):
        z.rect(19, r0, 8, r1 - r0 + 1, '#')
    for (r0, r1) in ((14, 24), (30, 40), (46, 57)):
        z.rect(39, r0, 8, r1 - r0 + 1, '#')
    # the big west pillar (cols 4..20, rows 37..46) with a timbered drift north-south through it
    z.rect(4, 37, 17, 10, '#')
    z.block(8, 37, 6, 10, 'Y', over='#')
    # the east pillar (cols 50..62, rows 24..37) with a timbered drift east-west through it
    z.rect(50, 24, 13, 14, '#')
    z.block(50, 28, 13, 6, 'Y', over='#')
    # small pillars in the districts
    z.block(10, 55, 2, 2, 'X')
    # where the small pillars of the old workings were robbed: cribs hold the roof, timbers wait to be set
    z.block(10, 15, 2, 2, 'X')
    z.block(56, 47, 2, 2, 'X')
    z.run(54, 50, 4, '=')
    # ---- the haulage gallery (cols 27..38): arch sets every 4 m, tracks (layer 0) at cols 29 and 36, carts
    for r in range(14, 47, 4):
        z.block(27, r, 12, 1, 'A')
    L0.run(29, 3, 63, '-', vertical=True)
    L0.run(36, 12, 54, '-', vertical=True)
    for (c, r) in ((29, 19), (29, 35), (29, 47), (36, 23), (36, 51), (29, 59)):
        z.block(c, r, 1, 2, 'C')
        L0.put(c, r, '.')
        L0.put(c, r + 1, '.')
    # the ore chute over the east track at the north end, the raised conveyor catwalk feeding it from the face
    z.block(35, 4, 10, 8, 'Z')
    z.block(45, 7, 20, 3, 'B')
    # the face conveyor along the north-east coal face (col 66), roof jacks along it, a crib
    z.run(66, 2, 13, 'k', vertical=True)
    for r in (2, 5, 12, 15):
        z.put(64, r, 'I')
    z.block(56, 2, 2, 2, 'X')
    z.block(49, 12, 2, 2, 'O')
    z.put(60, 13, 'L')
    z.puts([(47, 3), (48, 3), (47, 4)], 'c')
    # the fan in the gallery against the west pillar (riser at col 28 row 50), the winch house in its niche
    z.block(27, 51, 2, 4, 'F')
    z.block(21, 38, 6, 5, 'W')
    # ---- west heading: the coal face (col 0) with roof jacks, cribs, heaps, work lights
    for r in (3, 6, 9, 12, 21, 24, 27, 30):
        z.put(2, r, 'I')
    z.block(5, 4, 2, 2, 'X')
    z.block(5, 25, 2, 2, 'X')
    z.block(14, 5, 2, 2, 'O')
    z.block(5, 31, 2, 2, 'O')
    z.block(15, 27, 2, 2, 'd')
    z.put(6, 9, 'L')
    z.put(6, 20, 'L')
    z.puts([(16, 10), (16, 11), (17, 10)], 'c')
    z.run(12, 23, 3, '=')
    z.puts([(3, 16), (4, 16)], 'b')
    z.put(16, 33, 'l')
    z.put(14, 1 + 1, 'l')
    # the timbered drift's mouths: lanterns either side, dust
    z.put(7, 35, 'l')
    z.put(16, 48, 'l')
    # ---- south-west district
    z.block(3, 50, 2, 2, 'X')
    z.block(15, 51, 2, 2, 'O')
    z.block(4, 61, 2, 2, 'w')
    z.block(15, 63, 2, 2, 'd')
    z.puts([(3, 57), (4, 57), (3, 58)], 'c')
    z.put(17, 58, 'u')
    z.run(6, 66, 4, '=')
    z.put(10, 51, 'l')
    z.put(17, 61, 'L')
    z.puts([(2, 66), (2, 65)], 'b')
    # ---- gallery details
    z.puts([(31, 11), (32, 12)], 'c')
    z.block(31, 55, 2, 2, 'd')
    z.put(37, 59, 'l')
    z.put(28, 32, 'l')
    z.puts([(37, 40), (37, 41)], 'c')
    z.put(28, 45, 'u')
    # ---- east district (below the catwalk) and the south-east
    z.block(48, 17, 2, 2, 'X')
    z.block(58, 18, 2, 2, 'O')
    z.put(54, 21, 'l')
    z.puts([(63, 19), (63, 20)], 'b')
    z.block(64, 24, 2, 2, 'w')
    z.run(48, 39, 4, '=')
    z.block(49, 43, 2, 2, 'X')
    z.block(62, 41, 2, 2, 'O')
    z.put(57, 40, 'L')
    z.block(50, 55, 2, 2, 'd')
    z.puts([(63, 53), (63, 54), (64, 53)], 'c')
    z.block(48, 62, 2, 2, 'X')
    z.put(58, 59, 'l')
    z.put(62, 65, 'u')
    z.block(42, 63, 2, 2, 'w')
    # ---- entry, spawns, pickups
    z.put(33, 64, 'P')
    z.puts([(6, 2), (15, 19), (4, 34), (10, 63), (24, 26), (33, 32), (56, 5), (60, 15), (64, 32), (52, 51), (58, 64),
            (33, 8)], 'S')
    z.puts([(17, 30), (52, 22)], 'a')
    z.puts([(33, 44), (6, 53)], 'h')
    # ---- wall codes: the coal faces with gem veins, signs
    face_w = {r: '8' for r in range(2, 33)}
    face_w.update({4: '1', 5: '1', 9: '2', 14: '3', 15: '3', 19: '4', 25: '1', 26: '2', 30: '3'})
    for r, ch in face_w.items():
        codes(L0, z, [(0, r)], ch)
    face_e = {r: '8' for r in range(1, 17)}
    face_e.update({3: '2', 4: '2', 10: '4', 14: '3', 15: '1'})
    for r, ch in face_e.items():
        codes(L0, z, [(67, r)], ch)
    codes(L0, z, [(r, 0) for r in range(48, 66)], '8')
    codes(L0, z, [(55, 0), (56, 0)], '1')
    codes(L0, z, [(61, 0)], '4')
    codes(L0, z, [(0, 12)], '7')
    codes(L0, z, [(67, 7)], '7')
    codes(L0, z, [(26, 52), (39, 36)], '6')
    codes(L0, z, [(26, 18), (39, 31)], '5')
    codes(L0, z, [(45, 57), (26, 3)], '2')
    codes(L0, z, [(46, 50), (19, 31)], '4')
    # ---- roof fittings: the vent duct from the fan riser north along col 28, lamp strings across the gallery
    L9.run(28, 2, 49, 'v', vertical=True)
    for r in (16, 24, 32, 40, 48, 56):
        L9.run(27, r, 12, '~')
    L9.run(48, 13, 16, '~')
    L9.run(2, 20, 15, '~')
    L9.run(2, 64, 15, '~')
    L9.run(48, 60, 16, '~')
    return z, [(0, L0), (9, L9)]


# ================================================================ zone 2: the Glimmer Vault
def zone2():
    W, H = 70, 72
    z = shell('gemmine_2', W, H, 34)
    L0, LR = Layer(z), Layer(z)
    # ---- the Gem Heart (scaffold on its south flank, its stair coming down to the east at rows 28..29)
    z.block(29, 18, 12, 12, 'H')
    # ---- mining galleries: along the west wall (stairs come down at rows 23 / 40) and the north wall
    z.block(1, 24, 4, 16, 'N')
    z.block(44, 1, 16, 4, 'N')
    # ---- platforms and ledges
    z.block(50, 12, 6, 4, 'M')
    z.block(8, 52, 6, 4, 'M')
    z.block(18, 44, 8, 4, 'R')
    z.block(42, 58, 8, 4, 'R')
    z.block(12, 6, 8, 4, 'R')
    # ---- crystal spires, clusters, clumps
    for (c, r) in ((21, 12), (52, 38), (26, 58), (60, 22)):
        z.block(c, r, 3, 3, 'V')
    for (c, r) in ((8, 16), (16, 34), (44, 30), (36, 46), (58, 48), (24, 26), (46, 20), (6, 44), (30, 38), (40, 10)):
        z.block(c, r, 2, 2, 'Q')
    z.puts([(14, 20), (19, 22), (10, 30), (27, 34), (34, 33), (41, 35), (48, 26), (55, 30), (61, 32), (48, 44),
            (42, 52), (30, 50), (20, 54), (15, 40), (11, 12), (28, 6), (38, 5), (63, 10), (57, 8), (66, 58)], 'q')
    # rock stalagmites (natural pillars of the cavern floor)
    for (c, r) in ((38, 50), (12, 28), (48, 47), (24, 64), (6, 20), (62, 14), (17, 14), (56, 36)):
        z.block(c, r, 2, 2, 'D')
    # ---- the chasm along the east wall (rows 18..51), the hoist at its lip
    z.block(65, 30, 4, 4, 'U')
    # ---- sorting / cutting station (south-east) on plank decking, a lantern post and work lights
    L0.block(52, 54, 14, 12, 'p')
    z.block(54, 56, 2, 2, 'J')
    z.block(58, 56, 2, 2, 'J')
    z.block(62, 56, 2, 1, 'K')
    z.block(62, 58, 2, 1, 'K')
    z.block(54, 60, 2, 1, 'T')
    z.block(57, 60, 2, 1, 'T')
    z.block(60, 61, 2, 1, 'T')
    z.puts([(64, 61), (64, 62), (65, 62), (53, 63), (54, 63)], 'x')
    z.put(65, 55, 'u')
    z.put(52, 58, 'l')
    z.put(66, 64, 'L')
    # the track from the entry area east to the station, carts on it
    L0.run(39, 66, 26, '-')
    for c in (45, 57):
        z.block(c, 66, 2, 1, 'C')
        L0.put(c, 66, '.')
        L0.put(c + 1, 66, '.')
    # lamps round the cavern floor
    for (c, r) in ((22, 20), (44, 24), (12, 36), (34, 54), (56, 44), (8, 60), (28, 14), (46, 8), (62, 40)):
        z.put(c, r, 'l')
    for (c, r) in ((26, 30), (43, 16), (60, 28), (40, 62)):
        z.put(c, r, 'L')
    z.puts([(30, 42), (31, 42)], 'x')
    # ---- entry, spawns, pickups
    z.put(35, 66, 'P')
    z.puts([(10, 8), (26, 3), (56, 18), (62, 46), (40, 40), (20, 30), (10, 46), (50, 32), (24, 52), (62, 7), (8, 64),
            (55, 52)], 'S')
    z.puts([(44, 40), (16, 58)], 'a')
    z.puts([(22, 38), (58, 26)], 'h')
    # ---- wall codes: veins along the walls, the gallery's working face, the chasm edge
    codes(L0, z, [(69, r) for r in range(18, 52)], '9')
    veins = {}
    for r in range(24, 40):
        veins[(0, r)] = '1234'[(r // 2) % 4]
    for c in range(44, 60):
        veins[(c, 0)] = '4132'[(c // 2) % 4]
    for (c, r) in ((0, 6), (0, 7), (0, 50), (0, 58), (0, 59), (12, 0), (13, 0), (22, 0), (69, 8), (69, 60), (69, 61),
                   (20, 71), (21, 71), (50, 71), (64, 0), (0, 14), (0, 66)):
        veins[(c, r)] = '1234'[(c * 7 + r * 3) % 4]
    for (c, r), ch in veins.items():
        codes(L0, z, [(c, r)], ch)
    # ---- the roof: rock slabs over everything
    LR.block(0, 0, W, H, 'r')
    return z, [(0, L0), (18, LR)]



def check(z, layers):
    errs = []
    for y, L in layers:
        for r in range(z.h):
            for c in range(z.w):
                ch = L.g[r][c]
                if y == 0 and ch == '-' and z.at(c, r) not in '.SPahA':
                    errs.append('layer 0 %r over %r at %d,%d' % (ch, z.at(c, r), c, r))
                if y == 0 and ch == 'p' and z.at(c, r) in '#GE':
                    errs.append('layer 0 %r over %r at %d,%d' % (ch, z.at(c, r), c, r))
                if 1 < y < 17 and ch != '.' and z.at(c, r) in '#GE':
                    errs.append('roof fitting %r over a wall at %d,%d' % (ch, c, r))
                if y == 0 and ch in '0123456789' and z.at(c, r) != '#':
                    errs.append('wall code off a wall at %d,%d' % (c, r))
    # a stair foot must open onto floor: the galleries' / platforms' / bridge's stair ends
    return errs


def main():
    out = []
    for fn in (zone1, zone2):
        z, layers = fn()
        errs, stats = validate(z, WALK | set('.SPah'), PREFABS, size=((64, 72), (66, 74)))
        errs += check(z, layers)
        txt = z.text() + ''.join('@layer %s\n' % y + L.text() for y, L in layers)
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
