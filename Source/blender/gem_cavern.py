"""kit-gemmine, zone 2: the Glimmer Vault, a vast natural cavern the colliery broke into. Tall faceted violet rock walls
(18.4 m) with glowing veins and crystal clusters (diamond, ruby, emerald, sapphire), the chasm edge with its railing and
the far cliff beyond (backdrop), the roof (an "@layer 18" grid of rock slabs with stalactites and hanging crystals), the
Gem Heart (the landmark: giant crystals on a rock mound with a timber scaffold), the mining gallery at 4.8 m, timber
platforms at 2.4 m, rock ledges with ramps at 1.4 m, crystal clusters and spires, and the sorting / cutting station
(sieves, crates of rough gems, lit work tables, a lapidary saw), the hoist at the chasm lip."""
import math
import random

from mathutils import Vector

from gem_base import (CM, CAVE_H, POOL_Z, Z_DECK, KINDS, srt, rock_pts, clamp_pts, crystal, cluster, lantern_g, bulb,
                      floodlight, sign_board, stairs_x, deck, rail_x, rail_y, post, face_loft)

# profile levels of the cavern walls; the edge profile leans in toward the top (an overhang that meets the roof)
LVC = [0.0, 0.7, 1.8, 3.2, 5.0, 7.2, 9.6, 12.2, 14.8, 16.8, CAVE_H]
EYC = [-0.42, -0.5, -0.4, -0.48, -0.4, -0.52, -0.6, -0.78, -0.95, -1.05, -1.1]


def cprof(ys, lv=LVC):
    # the back of the module is left open (nothing ever sees it: the zone's outside, or rock behind a corner lump)
    return [(y, z) for y, z in zip(ys, lv)] + [(0.5, CAVE_H)]


CEDGE = cprof(EYC)


def cband(z):
    for i in range(len(LVC) - 1):
        if z < LVC[i + 1]:
            return i
    return len(LVC) - 2


def cave_fn(f):
    n, c = f.normal, f.calc_center_median()
    b = cband(c.z)
    if n.y > 0.5 or c.z > CAVE_H - 0.05 or (n.z > 0.2 and c.z > CAVE_H - 1.0):
        return 'rockBack'
    if n.z > 0.32:
        return 'cave3'
    if b == 0:
        return 'rock2'
    if b <= 2:
        return 'rock' if b % 2 else 'rockB'
    return 'cave' if b % 2 else 'cave2'


def face_y(z):
    """the edge profile's y at height z (where a vein or a cluster meets the face)"""
    for i in range(len(LVC) - 1):
        if z <= LVC[i + 1]:
            t = (z - LVC[i]) / (LVC[i + 1] - LVC[i])
            return EYC[i] + (EYC[i + 1] - EYC[i]) * t
    return EYC[-1]


def cave_face(k, seed, amp=0.18):
    face_loft(k, seed, LVC, EYC, CAVE_H, cave_fn, amp=amp, wander=0.3, rise=0.4)


def vein(k, kind, seed, z0, z1, n=7):
    """a glowing vein: a chain of small shards across the face along a crack from (x -0.5, z0) to (x 0.5, z1)"""
    rnd = random.Random(seed)
    for i in range(n):
        t = (i + 0.5) / n
        x = -0.5 + t
        z = z0 + (z1 - z0) * t + rnd.uniform(-0.1, 0.1)
        y = face_y(z) + 0.12
        L = rnd.uniform(0.16, 0.28)
        d = Vector((rnd.uniform(-0.4, 0.4), -1.0, rnd.uniform(-0.2, 0.6))).normalized()
        crystal(k, kind, (x, y, z), tuple(Vector((x, y, z)) + d * L), rnd.uniform(0.035, 0.06))


def cave_wall(k, kind, seed):
    """Cavern wall module (1 m, facing -Y, 18.4 m tall): the faceted face, the lamp string at 3.6 m, and per kind a
    lantern, or a gem vein with crystal clusters (low ones stay within 0.4 m of the face, high ones jut out)."""
    k.begin()
    cave_face(k, seed, amp=0.22 if kind in ('A', 'B', 'C') else 0.16)
    rnd = random.Random(seed * 3 + 1)
    g = {'Ruby': 'ruby', 'Emer': 'emer', 'Saph': 'saph', 'Dia': 'dia'}.get(kind)
    if g:
        vein(k, g, seed, rnd.uniform(0.8, 2.0), rnd.uniform(6.0, 9.0), n=5)
        if seed % 3 != 2:      # a low cluster at waist height
            z = rnd.uniform(0.9, 1.3)
            cluster(k, g, (rnd.uniform(-0.15, 0.15), face_y(z) + 0.08, z), (rnd.uniform(-0.3, 0.3), -1.0, 0.9), 4, 0.5, 0.1, seed, spread=0.7)
        if seed % 3 != 1:      # a big cluster up the face
            z = rnd.uniform(4.6, 6.8)
            cluster(k, g, (rnd.uniform(-0.1, 0.1), face_y(z) + 0.15, z), (rnd.uniform(-0.3, 0.3), -1.0, 0.45), 5, 1.25, 0.22, seed + 1, spread=0.6)
    elif kind.startswith('Lamp'):
        k.bx(-0.07, 0.07, -0.95, -0.2, 3.25, 3.39, 'timber')
        k.beam((0.0, -0.3, 2.65), (0.0, -0.82, 3.26), 0.09, 'timber2')
        lantern_g(k, 0.0, -0.88, 3.25)
        CM.pool(k, 0.0, -1.5, POOL_Z['c' + kind[4:]], 2.1, seed, sx=1.15)
    return k


def cave_corner(k, seed):
    """Corners, notches and chasm ends: stacked faceted lumps up to the roof."""
    k.begin()
    rnd = random.Random(seed)
    z = 0.0
    fn = lambda f: 'cave3' if f.normal.z > 0.4 else ('rock2' if f.calc_center_median().z < 1.5 else ('cave' if f.calc_center_median().z > 6 else 'rockB'))
    while z < CAVE_H - 0.1:
        h = min(rnd.uniform(3.5, 5.0), CAVE_H - z + 0.6)
        top = z + h >= CAVE_H - 0.01
        pts = rock_pts(rnd, (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)), 0.56, 0.56, h + 0.6, z0=max(0.0, z - 0.6), n=7, top=0 if top else 2)
        if top or z + h + 0.6 >= CAVE_H:
            pts = [(x, y, min(zz, CAVE_H)) for (x, y, zz) in pts] + [(0.45, 0.45, CAVE_H), (-0.45, 0.45, CAVE_H), (0.45, -0.45, CAVE_H), (-0.45, -0.45, CAVE_H)]
        k.hullp(clamp_pts(pts, 0.5), fn)
        z += h
    return k


def chasm(k, variant, seed):
    """Chasm edge module (the wall cell is the drop): a rock lip, the near cliff falling away beneath it, a steel
    railing at the cell's room face, and per variant a sign or a floodlight aimed down into the chasm."""
    k.begin()
    rnd = random.Random(seed)
    fn = lambda f: 'cave3' if f.normal.z > 0.55 else ('cave2' if f.calc_center_median().z > -6 else 'pit')
    # lip (top flush with the floor), the cliff under it leaning out into the chasm
    k.hullp([(-0.5, -0.5, -0.01), (0.5, -0.5, -0.01), (0.5, 0.25 + rnd.uniform(-0.05, 0.05), 0.0), (-0.5, 0.25 + rnd.uniform(-0.05, 0.05), 0.0),
             (-0.5, -0.5, -0.8), (0.5, -0.5, -0.8), (0.5, 0.45, -0.5), (-0.5, 0.45, -0.5)], fn)
    prof = [(0.3, -0.45), (0.6 + rnd.uniform(-0.1, 0.1), -4.0), (1.0 + rnd.uniform(-0.2, 0.2), -10.0), (1.5 + rnd.uniform(-0.3, 0.3), -20.0), (2.4, -40.0)]
    edge = [(0.3, -0.45), (0.65, -4.0), (1.05, -10.0), (1.55, -20.0), (2.4, -40.0)]

    def p2(ps):   # front (chasm side) going down, then back up inside the rock
        return [(y, z) for (y, z) in ps] + [(-0.4, -40.0), (-0.4, -0.45)]
    k.loft([(-0.5, p2(edge)), (rnd.uniform(-0.1, 0.1), p2(prof)), (0.5, p2(edge))],
           lambda f: 'cave2' if f.calc_center_median().z > -8 else 'pit', baffle='pit')
    # railing: posts at the module ends' middle, top + mid rail, hazard kick board, toe stripes
    k.bx(-0.05, 0.05, -0.47, -0.37, 0, 1.15, 'steel')
    k.bx(-0.5, 0.5, -0.46, -0.38, 1.0, 1.09, 'hazard')
    k.bx(-0.5, 0.5, -0.45, -0.39, 0.52, 0.59, 'hazard', ink=False)
    k.bx(-0.5, 0.5, -0.44, -0.4, 0.0, 0.16, 'steelDark', ink=False)
    k.qz(-0.5, 0.5, -0.5, -0.36, 0.004, 1, 'hazard')
    if variant == 'Sign':
        sign_board(k, 0.0, -0.495, 0.25, 0.9, 0.62, [('DEEP CHASM', 0.15, 'ink'), ('KEEP BACK', 0.13, 'ink')], bg='hazard', rim='ink', s=-1)
    elif variant == 'Lamp':
        k.bx(-0.06, 0.06, -0.36, -0.24, 0, 2.6, 'steelDark')
        k.bx(-0.04, 0.04, -0.3, 0.3, 2.5, 2.58, 'steelDark', ink=False)
        k.push(0.0, 0.3, 0, 2.45)
        k.bxr(0, 0.12, 0, 0.42, 0.3, 0.3, 'steelDark', rot=(-35, 0, 0))
        k.pop()
        k.gbx(-0.16, 0.16, 0.3, 0.33, 2.25, 2.45, 'lampHot', hull=False)
    return k


# ================================================================ the roof ("@layer 18": local z 0 = 18 m)
def cave_roof(k, seed):
    """Roof slab [10, 12]: a down-facing rock plane at 18.2 m, faceted lumps and stalactites hanging from it, glowing
    crystal clusters pointing down."""
    k.begin()
    rnd = random.Random(seed)
    k.qz(-5.0, 5.0, -6.0, 6.0, 0.2, -1, 'cave2')
    fn = lambda f: 'cave' if f.normal.z < -0.6 else ('cave2' if f.calc_center_median().z > -1.0 else 'rock2')
    spots = []
    for i in range(5):
        for _ in range(20):
            x, y = rnd.uniform(-3.8, 3.8), rnd.uniform(-4.8, 4.8)
            if all((x - a) ** 2 + (y - b) ** 2 > 2.4 ** 2 for (a, b) in spots):
                break
        spots.append((x, y))
        r = rnd.uniform(0.7, 1.2)
        if i < 3:   # stalactite: a ring at the roof to a point
            ring = [(x + math.cos(a) * r * rnd.uniform(0.8, 1.0), y + math.sin(a) * r * rnd.uniform(0.8, 1.0), 0.25) for a in [j / 6 * 2 * math.pi for j in range(6)]]
            mid = [(x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45, -rnd.uniform(0.7, 1.1)) for a in [(j + 0.5) / 5 * 2 * math.pi for j in range(5)]]
            k.hullp(ring + mid + [(x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2), -rnd.uniform(1.8, 2.5))], fn)
        else:       # a low lump
            pts = rock_pts(rnd, (x, y), r * 1.3, r * 1.1, rnd.uniform(0.5, 0.9), n=6, top=2)
            k.hullp([(px, py, 0.25 - pz) for (px, py, pz) in pts], fn)
    for j in range(1):
        for _ in range(20):
            x, y = rnd.uniform(-3.6, 3.6), rnd.uniform(-4.6, 4.6)
            if all((x - a) ** 2 + (y - b) ** 2 > 1.8 ** 2 for (a, b) in spots):
                break
        spots.append((x, y))
        cluster(k, KINDS[(seed + j) % 4], (x, y, 0.3), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), -1.0), 5, 1.1, 0.16, seed * 7 + j, spread=0.6)
    return k


# ================================================================ crystals as props
def mound(k, rx, ry, h, seed, n=8, fn=None):
    rnd = random.Random(seed)
    fn = fn or (lambda f: 'cave3' if f.normal.z > 0.6 else ('cave' if f.normal.z > 0.2 else 'cave2'))
    k.hullp(rock_pts(rnd, (0, 0), rx, ry, h, n=n, top=3, waist=(0.4, 0.7)), fn)


def crystal_cluster(k, kind, seed):
    """Prefab 2 x 2: a crystal cluster on a rock knuckle (cover, about 2.3 m tall)."""
    k.begin()
    rnd = random.Random(seed)
    mound(k, 0.85, 0.8, 0.45, seed)
    cluster(k, kind, (0.0, 0.0, 0.25), (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 1.0), 7, 2.1, 0.26, seed, spread=0.65, lo=0.4)
    for i in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        x, y = math.cos(a) * 0.62, math.sin(a) * 0.55
        cluster(k, KINDS[(KINDS.index(kind) + i) % 4] if i == 2 else kind, (x, y, 0.15), (x, y, 0.9), 3, 0.55, 0.08, seed * 3 + i)
    k.col(-0.55, 0.55, -0.55, 0.55, 0, 2.0)
    k.col(-0.9, 0.9, -0.8, 0.8, 0, 0.45)
    return k


def clump(k, seed):
    """1 cell: a low clump of mixed crystals on a rock (low cover, ~0.9 m)."""
    k.begin()
    rnd = random.Random(seed)
    mound(k, 0.45, 0.42, 0.3, seed, n=6)
    for i in range(3):
        a = i / 3 * 2 * math.pi + rnd.uniform(-0.4, 0.4)
        x, y = math.cos(a) * 0.15, math.sin(a) * 0.15
        cluster(k, KINDS[(seed + i) % 4], (x, y, 0.15), (x * 2, y * 2, 1.0), 3, 0.75, 0.09, seed * 5 + i, spread=0.5)
    k.col(-0.42, 0.42, -0.42, 0.42, 0, 0.85)
    return k


def spire(k, seed):
    """Prefab 3 x 3: a tall crystal spire (6.5 - 8 m) with lesser crystals round it on a rock base (breaks long sight
    lines)."""
    k.begin()
    rnd = random.Random(seed)
    kind = ('dia', 'saph')[seed % 2]
    mound(k, 1.3, 1.2, 0.8, seed, n=9)
    tip = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(6.5, 8.0))
    crystal(k, kind, (0, 0, 0.0), tip, 0.62, shape='hex')
    for i in range(4):
        a = i / 4 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        x, y = math.cos(a) * 0.65, math.sin(a) * 0.6
        L = rnd.uniform(2.2, 3.6)
        crystal(k, KINDS[(seed + i) % 4] if i % 2 else kind, (x * 0.6, y * 0.6, 0.2), (x * 1.6, y * 1.6, L), rnd.uniform(0.22, 0.32))
    k.col(-0.75, 0.75, -0.75, 0.75, 0, 6.0)
    k.col(-1.25, 1.25, -1.15, 1.15, 0, 0.7)
    return k


def stalagmite(k, seed):
    """Prefab 2 x 2: a natural rock stalagmite (3.6 - 5.2 m) in two stacked faceted cones, small crystals at its foot."""
    k.begin()
    rnd = random.Random(seed)
    fn = lambda f: 'cave3' if f.normal.z > 0.55 else ('cave' if f.calc_center_median().z > 1.2 else 'cave2')
    h = rnd.uniform(3.6, 5.2)
    k.hullp(rock_pts(rnd, (0, 0), 0.9, 0.85, 1.6, n=7, top=0, waist=(0.4, 0.6)) + [(rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 1.9)], fn)
    tip = (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), h)
    k.hullp([(0.45 * math.cos(a), 0.42 * math.sin(a), 1.2) for a in [i / 6 * 2 * math.pi for i in range(6)]] + [tip], fn)
    for i in range(3):
        a = i / 3 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        x, y = math.cos(a) * 0.75, math.sin(a) * 0.7
        cluster(k, KINDS[(seed + i) % 4], (x, y, 0.05), (x, y, 0.8), 3, 0.45, 0.07, seed * 3 + i, spread=0.5)
    k.col(-0.75, 0.75, -0.7, 0.7, 0, 3.0)
    return k


# ================================================================ the Gem Heart (zone 2 landmark)
def gem_heart(k):
    """Landmark 12 x 12: giant crystals of every kind bursting from a rock mound (the tallest diamond 14 m), a timber
    scaffold on the south flank (deck at 2.4 m, stair down to the east, rails), floodlights trained on the crystals."""
    k.begin()
    rnd = random.Random(3)
    fn = lambda f: 'cave3' if f.normal.z > 0.55 else ('cave' if f.normal.z > 0.15 else 'cave2')
    k.hullp(rock_pts(rnd, (0.3, 0.6), 4.6, 4.2, 1.8, n=11, top=4, waist=(0.35, 0.6)), fn)
    k.hullp(rock_pts(rnd, (0.6, 1.2), 2.8, 2.5, 2.9, n=8, top=2, waist=(0.4, 0.7)), fn)
    # the giants: a 14 m diamond, two leaning diamonds, a sapphire, a ruby and an emerald column
    big = [('dia', (0.5, 1.2, 1.0), (0.2, 1.6, 14.2), 1.25), ('dia', (-0.6, 1.8, 1.2), (-4.6, 3.4, 10.0), 0.9),
           ('dia', (1.4, 0.4, 1.0), (4.9, -0.8, 9.2), 0.85), ('saph', (0.0, 2.6, 1.0), (1.6, 5.4, 9.6), 0.8),
           ('ruby', (-1.6, -0.2, 0.6), (-4.4, -1.6, 6.4), 0.75), ('emer', (2.0, 2.4, 0.8), (4.6, 4.6, 7.0), 0.7)]
    for (g, a, b, r) in big:
        crystal(k, g, a, b, r, shape='hex' if g in ('dia', 'saph') else 'flat')
    # rings of lesser crystals round the mound
    for i in range(13):
        a = i / 13 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
        rr = rnd.uniform(2.6, 3.8)
        x, y = 0.3 + math.cos(a) * rr, 0.6 + math.sin(a) * rr * 0.92
        if y < -2.6 and abs(x) < 3.2:
            continue      # keep the scaffold side clear
        g = KINDS[i % 4]
        L = rnd.uniform(1.6, 3.4)
        d = Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 1.0)).normalized()
        crystal(k, g, (x, y, 0.5), tuple(Vector((x, y, 0.5)) + d * L), rnd.uniform(0.2, 0.34))
    # scaffold on the south flank: deck at 2.4 (x -2.6 .. 2.6, y -5.8 .. -4.2), stair down to the east
    Z = 2.4
    deck(k, -2.6, 2.5, -5.8, -4.2, Z, t=0.12)
    for x in (-2.45, 0.0, 2.45):
        for y in (-5.65, -4.35):
            post(k, x, y, 0, Z - 0.12, c='timber', w=0.1)
        k.beam((x, -5.65, 0.3), (x, -4.35, Z - 0.4), 0.07, 'timber2', ink=False)
    stairs_x(k, 6.0, 2.5, -5.8, -4.2, 0.0, Z, 7, timber=True, rails=(True, True))
    rail_x(k, -2.6, 2.5, -5.85, Z, c='timber', post=2.55)
    rail_x(k, -2.6, 2.5, -4.15, Z, c='timber', post=2.55)
    rail_y(k, -5.8, -4.2, -2.65, Z, c='timber', post=1.6)
    # floodlights on the scaffold, a tool chest and a pick rack on the deck
    for x in (-1.8, 1.0):
        k.bx(x - 0.04, x + 0.04, -4.22, -4.14, Z, Z + 2.2, 'steelDark')
        floodlight(k, x, -4.05, Z + 2.0, s=1)
    k.bx(-0.5, 0.4, -5.6, -5.15, Z, Z + 0.5, 'cart')
    k.col(-0.5, 0.4, -5.6, -5.15, Z, Z + 0.5)
    sign_board(k, 0.0, -5.9, Z - 1.2, 2.2, 0.62, [('THE GEM HEART', 0.2, 'hazard'), ('NO UNAUTHORISED CUTTING', 0.08, None)], s=-1)
    CM.pool(k, 0.0, -2.4, POOL_Z['heart'], 2.8, 61, sx=1.6, sy=0.8)
    # collision: the mound in steps, the giants' trunks
    k.col(-3.6, 4.2, -2.6, 4.4, 0, 1.2)
    k.col(-1.6, 2.6, -0.9, 3.6, 0, 2.6)
    k.col(-0.8, 1.6, 0.4, 2.6, 0, 9.0)
    return k


# ================================================================ walkways (decks robots climb)
def gallery(k):
    """Prefab 16 x 4 against the cavern wall (orient wall: back = +Y): the mining gallery, a 1.9 m deck at 4.8 m
    along the crystal face, two stairs rising from the ends to a front landing in the middle, posts and braces,
    rails; on the deck a rock drill on its leg, gem crates, a lamp mast; a pocket under the deck behind the stairs."""
    k.begin()
    Z = 4.8
    deck(k, -8.0, 8.0, 0.05, 1.85, Z, t=0.14)
    deck(k, -1.0, 1.0, -2.0, 0.05, Z, t=0.14, along='y')
    stairs_x(k, -8.0, -1.0, -2.0, -0.05, 0.0, Z, 14, rails=(True, False), timber=True)
    stairs_x(k, 8.0, 1.0, -2.0, -0.05, 0.0, Z, 14, rails=(True, False), timber=True)
    rail_x(k, -8.0, -1.0, 0.0, Z, c='timber', post=2.4)
    rail_x(k, 1.0, 8.0, 0.0, Z, c='timber', post=2.4)
    rail_x(k, -1.0, 1.0, -2.05, Z, c='timber', post=1.0)
    rail_x(k, -8.0, 8.0, 1.9, Z, c='timber', post=3.2, kick=False)
    for s in (-1, 1):
        rail_y(k, 0.05, 1.85, s * 8.05, Z, c='timber', post=1.0)
    # posts and diagonal braces under the deck (the pocket behind the stairs stays walkable)
    for x in (-7.8, -3.9, 0.0, 3.9, 7.8):
        for y in ((0.2, 1.7) if x in (-7.8, 0.0, 7.8) else (1.7,)):
            post(k, x, y, 0, Z - 0.14, c='timber', w=0.12)
        if x in (-7.8, 0.0, 7.8):
            k.beam((x, 0.2, 0.5), (x, 1.7, Z - 0.6), 0.08, 'timber2', ink=False)
    for x0, x1 in ((-7.8, -3.9), (3.9, 7.8)):
        k.beam((x0, 1.7, 0.6), (x1, 1.7, Z - 0.6), 0.08, 'timber2', ink=False)
    for y in (-1.85, -0.2):
        post(k, -1.0 + 0.12, y, 0, Z - 0.14, c='timber', w=0.1)
        post(k, 1.0 - 0.12, y, 0, Z - 0.14, c='timber', w=0.1)
    # on the deck: a rock drill on its air leg against the face, a crate of rough gems, a lamp mast with floodlights
    k.push(-4.8, 1.0, 0, Z)
    k.beam((0, 0.0, 0.0), (0.0, 0.35, 1.15), 0.07, 'steel2')                       # air leg, drill against the face
    k.bx(-0.11, 0.11, 0.3, 0.75, 1.1, 1.34, 'mach')
    k.bx(-0.03, 0.03, 0.75, 0.95, 1.19, 1.25, 'steel')
    k.beam((0.1, 0.4, 1.2), (0.5, 0.8, 0.05), 0.04, 'rubber', ink=False)
    k.pop()
    for (x, gs) in ((2.6, ('ruby', 'emer', 'dia')), (5.8, ('saph', 'ruby', 'saph'))):   # gem crates against the back rail
        k.bx(x - 0.45, x + 0.45, 1.22, 1.8, Z, Z + 0.55, 'plank')
        k.col(x - 0.45, x + 0.45, 1.22, 1.8, Z, Z + 0.55)
        for i, g in enumerate(gs):
            xx = x - 0.25 + i * 0.25
            crystal(k, g, (xx, 1.5, Z + 0.5), (xx + 0.04, 1.45, Z + 0.78), 0.08)
    k.bx(-0.06, 0.06, 1.55, 1.67, Z, Z + 3.2, 'steelDark')
    k.col(-0.08, 0.08, 1.53, 1.69, Z, Z + 3.2)
    k.bx(-0.6, 0.6, 1.58, 1.64, Z + 3.0, Z + 3.06, 'steelDark', ink=False)
    for s in (-1, 1):
        floodlight(k, s * 0.45, 1.5, Z + 2.8, s=-1)
    sign_board(k, 0.0, -2.08, Z - 1.25, 1.8, 0.62, [('GALLERY B', 0.2, None), ('HARD HATS', 0.1, 'hazard')], s=-1)
    CM.pool(k, 0.0, -3.0, POOL_Z['gal'], 2.2, 71, sx=1.8, sy=0.6)
    return k


def platform(k):
    """Prefab 6 x 4: a timber mining platform, deck at 2.4 m (back strip and a landing at the east end), a stair up
    from the west along the front, rails, a hand winch and crates on the deck; open underneath."""
    k.begin()
    Z = 2.4
    deck(k, -3.0, 3.0, -0.35, 1.9, Z, t=0.12)
    deck(k, 0.5, 3.0, -1.95, -0.35, Z, t=0.12, along='y')
    stairs_x(k, -3.0, 0.5, -1.95, -0.4, 0.0, Z, 7, timber=True, rails=(True, False))
    rail_x(k, -3.0, 0.5, -0.32, Z, c='timber', post=3.5)
    rail_x(k, 0.5, 3.0, -2.0, Z, c='timber', post=2.5)
    rail_x(k, -3.0, 3.0, 1.95, Z, c='timber', post=3.0)
    rail_y(k, -0.35, 1.9, -3.05, Z, c='timber', post=2.25)
    rail_y(k, -1.95, 1.9, 3.05, Z, c='timber', post=1.9)
    for (x, y) in ((-2.85, -0.2), (-2.85, 1.75), (0.0, 1.75), (2.85, 1.75), (2.85, -1.8), (0.65, -1.8), (0.0, -0.2)):
        post(k, x, y, 0, Z - 0.12, c='timber', w=0.11)
    for x in (-2.85, 2.85):
        k.beam((x, -0.2 if x < 0 else -1.8, 0.4), (x, 1.75, Z - 0.4), 0.07, 'timber2', ink=False)
    k.beam((-2.85, 1.75, 0.4), (2.85, 1.75, Z - 0.4), 0.07, 'timber2', ink=False)
    # a hand winch with a rope reel and a crate of picked gems on the deck, a lantern post
    k.bx(-2.2, -1.2, 0.6, 1.4, Z, Z + 0.15, 'steelDark')
    for x in (-2.1, -1.3):
        k.bx(x - 0.05, x + 0.05, 0.9, 1.1, Z + 0.15, Z + 0.85, 'steelDark')
    k.cyl(-2.1, 1.0, Z + 0.7, 0.22, 0.22, 0.8, 'rope', seg=10, rot=(0, 90, 0))
    k.beam((-1.25, 1.0, Z + 0.7), (-1.0, 0.7, Z + 1.0), 0.04, 'steel', ink=False)
    k.col(-2.2, -1.2, 0.6, 1.4, Z, Z + 0.9)
    k.bx(1.2, 2.1, 0.6, 1.4, Z, Z + 0.6, 'plank')
    k.col(1.2, 2.1, 0.6, 1.4, Z, Z + 0.6)
    for i, g in enumerate(('emer', 'saph', 'ruby')):
        crystal(k, g, (1.4 + i * 0.25, 1.0, Z + 0.55), (1.45 + i * 0.25, 0.95, Z + 0.85), 0.08)
    k.bx(2.7, 2.8, 1.5, 1.6, Z, Z + 2.4, 'timber')
    k.bx(2.72, 2.78, 1.1, 1.52, Z + 2.3, Z + 2.37, 'timber2', ink=False)
    lantern_g(k, 2.75, 1.2, Z + 2.3, 0.85)
    k.col(2.65, 2.85, 1.45, 1.65, Z, Z + 2.4)
    CM.pool(k, 0.0, -0.2, POOL_Z['plat'], 1.8, 81, sx=1.4, sy=0.9)
    return k


def ledge(k):
    """Prefab 8 x 4: a rock shelf (top at 1.4 m, x -4 .. 0) reached by a plank ramp up from the east (x 4 .. 0,
    stepped walkable boxes under the sloped boards); crystal clumps along its back edge."""
    k.begin()
    Z = 1.4
    rnd = random.Random(13)
    fn = lambda f: 'cave3' if f.normal.z > 0.7 else ('cave' if f.normal.z > 0.1 else 'cave2')
    top = [(-3.75, -1.75), (-0.05, -1.75), (-0.05, 1.75), (-3.75, 1.75), (-2.0, -1.78), (-2.0, 1.78), (-3.78, 0.0)]
    pts = [(x, y, Z) for (x, y) in top] + [(-3.98, -1.98, 0.0), (0.0, -1.98, 0.0), (0.0, 1.98, 0.0), (-3.98, 1.98, 0.0),
                                           (-2.0, -1.99, 0.6), (-3.99, 0.0, 0.7), (-2.0, 1.99, 0.6)]
    k.hullp(pts, fn)
    k.colw(-3.8, 0.0, -1.8, 1.8, 0, Z)
    # ramp: boards on two stringers from (x 4, z 0) to (x 0, z 1.4), 0.9 m wide
    n = 8
    for i in range(n):
        a, b = 4.0 - (i + 1) * 0.5, 4.0 - i * 0.5
        k.colw(a, b, -0.9, 0.9, 0, Z * (i + 1) / n)
    k.hullp([(4.0, -0.9, 0.0), (4.0, 0.9, 0.0), (0.0, -0.9, Z - 0.1), (0.0, 0.9, Z - 0.1),
             (4.0, -0.9, 0.06), (4.0, 0.9, 0.06), (0.0, -0.9, Z), (0.0, 0.9, Z)], 'plank')
    for i in range(1, 8):
        x = 4.0 - i * 0.5
        zt = Z * i / 8 + 0.06 - 0.06 * i / 8 + 0.004
        k.poly([(x - 0.012, -0.85, zt - 0.003), (x + 0.012, -0.85, zt + 0.003), (x + 0.012, 0.85, zt + 0.003), (x - 0.012, 0.85, zt - 0.003)], 'plank2', (0.35, 0, 1))
    for y in (-0.95, 0.95):
        k.beam((4.0, y, 0.85), (0.0, y, Z + 0.95), 0.06, 'timber')
        for x in (3.6, 1.8, 0.1):
            zz = Z * (4.0 - x) / 4.0
            k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0, zz + 0.95, 'timber')
            k.col(x - 0.05, x + 0.05, y - 0.06, y + 0.06, 0, zz + 0.95)
    # crystal clumps along the back of the shelf (cover up there), a lantern post on the shelf
    for i, (x, g) in enumerate(((-3.2, 'emer'), (-1.9, 'saph'), (-0.7, 'ruby'))):
        cluster(k, g, (x, 1.35, Z - 0.05), (rnd.uniform(-0.3, 0.3), 0.3, 1.0), 4, 0.95, 0.13, 30 + i, spread=0.6)
        k.col(x - 0.35, x + 0.35, 1.0, 1.7, Z, Z + 0.85)
    k.bx(-3.5, -3.4, -1.55, -1.45, Z, Z + 2.2, 'timber')
    k.bx(-3.48, -3.42, -1.47, -1.05, Z + 2.1, Z + 2.17, 'timber2', ink=False)
    lantern_g(k, -3.45, -1.15, Z + 2.1, 0.85)
    k.col(-3.55, -3.35, -1.6, -1.4, Z, Z + 2.2)
    return k


# ================================================================ sorting / cutting station
def sieve(k):
    """Prefab 2 x 2: a hand jig / riddle: a timber frame on four legs, a tilted mesh tray of gravel with rough gems in
    it, a wash trough below, a crank."""
    k.begin()
    for x in (-0.8, 0.8):
        for y in (-0.7, 0.7):
            k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 1.0 + (0.1 if y > 0 else 0), 'timber')
    k.bx(-0.85, 0.85, -0.75, 0.75, 0.3, 0.38, 'timber2', ink=False)
    k.bx(-0.7, 0.7, -0.6, 0.6, 0.38, 0.62, 'drum2')
    k.bx(-0.62, 0.62, -0.52, 0.52, 0.55, 0.6, 'water')
    k.bxr(0, 0.0, 1.06, 1.6, 1.4, 0.1, 'timber2', rot=(4, 0, 0))
    k.bxr(0, 0.0, 1.115, 1.42, 1.22, 0.02, 'steel2', rot=(4, 0, 0), ink=False)
    rnd = random.Random(4)
    for i in range(8):
        x, y = rnd.uniform(-0.55, 0.55), rnd.uniform(-0.45, 0.45)
        z = 1.13 + y * math.tan(math.radians(4))
        if i < 5:
            k.hullp(rock_pts(rnd, (x, y), 0.09, 0.08, 0.07, z0=z - 0.02 + i * 0.006, n=4, top=1), 'dust')
        crystal(k, KINDS[i % 4], (x + 0.05, y, z), (x + 0.07, y + 0.03, z + 0.12), 0.05)
    k.beam((0.85, 0.0, 1.06), (1.1, 0.0, 1.06), 0.05, 'steelDark')
    k.beam((1.1, 0.0, 1.06), (1.1, -0.15, 0.85), 0.04, 'steel')
    k.col(-0.9, 0.9, -0.8, 0.8, 0, 1.2)
    return k


def cut_bench(k):
    """Prefab 2 x 1: the lapidary bench: a heavy bench, a diamond saw wheel under its hood, a drip can, cut stones on
    a felt tray, a glowing lamp on an arm."""
    k.begin()
    k.bx(-0.95, 0.95, -0.45, 0.45, 0.82, 0.92, 'timber')
    for x in (-0.85, 0.85):
        for y in (-0.35, 0.35):
            k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, 0.82, 'timber2')
    k.bx(-0.8, 0.8, -0.3, 0.3, 0.25, 0.3, 'plank2', ink=False)
    k.bx(-0.8, -0.1, -0.3, 0.3, 0.92, 1.0, 'steelDark')
    k.cyl(-0.45, 0.0, 1.22, 0.28, 0.28, 0.025, 'steel', seg=14, rot=(90, 0, 0))
    k.hullp([(-0.78, -0.06, 1.0), (-0.12, -0.06, 1.0), (-0.78, 0.06, 1.0), (-0.12, 0.06, 1.0), (-0.45, -0.06, 1.55), (-0.45, 0.06, 1.55),
             (-0.72, -0.06, 1.38), (-0.18, 0.06, 1.38)], 'cart')
    k.cyl(-0.3, 0.2, 1.55, 0.08, 0.06, 0.18, 'steel2', seg=6)
    k.bx(0.1, 0.8, -0.3, 0.2, 0.92, 0.95, 'felt', ink=False)
    for i, g in enumerate(KINDS):
        x = 0.2 + i * 0.16
        crystal(k, g, (x, -0.05, 0.94), (x, -0.06, 1.04), 0.04, shape='oct')
    k.bx(0.78, 0.84, 0.3, 0.36, 0.92, 1.6, 'steelDark')
    k.beam((0.81, 0.33, 1.6), (0.5, 0.05, 1.55), 0.04, 'steelDark')
    k.cyl(0.48, 0.03, 1.38, 0.09, 0.05, 0.15, 'hood', seg=8)
    k.gcyl(0.48, 0.03, 1.34, 0.065, 0.065, 0.04, 'lampHot', seg=8, hull=False)
    CM.pool(k, 0.3, -0.1, POOL_Z['table'], 0.7, 91, sx=1.3, sy=0.8)
    k.col(-0.95, 0.95, -0.45, 0.45, 0, 1.0)
    return k


def work_table(k, variant):
    """Prefab 2 x 1: a lit sorting table (felt top): trays of gems sorted by colour, a scale, a magnifier lamp
    on an arm (variant 1: a ledger, loupes and a lamp on a stand instead of the scale)."""
    k.begin()
    k.bx(-0.95, 0.95, -0.42, 0.42, 0.8, 0.88, 'plank')
    k.bx(-0.9, 0.9, -0.37, 0.37, 0.88, 0.9, 'felt', ink=False)
    for x in (-0.85, 0.85):
        for y in (-0.33, 0.33):
            k.bx(x - 0.045, x + 0.045, y - 0.045, y + 0.045, 0, 0.8, 'timber2')
    k.bx(-0.9, 0.9, -0.36, 0.36, 0.22, 0.26, 'plank2', ink=False)
    for i, g in enumerate(KINDS if variant == 0 else ('dia', 'ruby', 'emer')):
        x0 = -0.82 + i * 0.36
        k.bx(x0, x0 + 0.3, -0.3, -0.02, 0.9, 0.95, 'timber')
        for j in range(3):
            crystal(k, g, (x0 + 0.06 + j * 0.09, -0.16, 0.94), (x0 + 0.07 + j * 0.09, -0.15, 1.01), 0.035, shape='oct' if g == 'dia' else None)
    if variant == 0:
        k.bx(0.55, 0.8, 0.05, 0.3, 0.9, 0.96, 'steel2')
        k.bx(0.66, 0.69, 0.16, 0.19, 0.96, 1.25, 'steel')
        k.bx(0.5, 0.85, 0.16, 0.19, 1.25, 1.28, 'steel')
        for x in (0.52, 0.83):
            k.cyl(x, 0.175, 1.1, 0.06, 0.06, 0.02, 'steel', seg=8, ink=False)
    else:
        k.bx(0.3, 0.75, 0.0, 0.32, 0.9, 0.93, 'board')
        k.qz(0.33, 0.72, 0.03, 0.29, 0.933, 1, 'chalk')
    # magnifier / task lamp on an arm, glowing
    k.bx(-0.9, -0.84, 0.25, 0.31, 0.9, 1.5, 'steelDark')
    k.beam((-0.87, 0.28, 1.5), (-0.45, 0.0, 1.42), 0.035, 'steelDark')
    k.cyl(-0.42, -0.02, 1.27, 0.11, 0.06, 0.15, 'hood', seg=8)
    k.gcyl(-0.42, -0.02, 1.23, 0.085, 0.085, 0.04, 'lampHot', seg=8, hull=False)
    CM.pool(k, -0.3, -0.1, POOL_Z['table'], 0.75, 93 + variant, sx=1.3, sy=0.8)
    k.col(-0.95, 0.95, -0.42, 0.42, 0, 0.95)
    return k


def gem_crate(k, variant):
    """1 cell: an open crate of rough gems (variant 0 mixed, 1 rubies + emeralds), a stencilled band."""
    k.begin()
    CM.crate_body(k, 0.44, 0.38, 0.62, 'Plain')
    rnd = random.Random(7 + variant)
    k.hullp(rock_pts(rnd, (0, 0), 0.36, 0.3, 0.12, z0=0.56, n=6, top=2), 'dust')
    kinds = KINDS if variant == 0 else ('ruby', 'emer')
    for i in range(7):
        x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.24, 0.24)
        g = kinds[i % len(kinds)]
        crystal(k, g, (x, y, 0.6), (x + rnd.uniform(-0.08, 0.08), y + rnd.uniform(-0.08, 0.08), 0.6 + rnd.uniform(0.12, 0.2)), rnd.uniform(0.04, 0.065))
    import ib_text
    ib_text.draw(k, 'ROUGH' if variant == 0 else 'GRADE A', 0.0, -0.386, 0.22, 0.13, 'ink', face='y-', font='display', maxw=0.7)
    return k


def hoist(k):
    """Prefab 4 x 4 at the chasm lip (orient wall: back = +Y = the chasm): a timber A-frame with a jib reaching out
    over the drop, the rope down to a bucket hanging in the chasm, a hand winch on a skid, a stack of buckets, a
    lantern."""
    k.begin()
    # A-frame legs (front pair at y -0.8, back pair at the lip y 1.7), cap, jib over the chasm to y 4.6
    for s in (-1, 1):
        k.beam((s * 1.5, -0.8, 0.0), (s * 0.35, 1.0, 4.5), 0.2, 'timber')
        k.beam((s * 1.5, 1.8, 0.0), (s * 0.35, 1.0, 4.5), 0.2, 'timber')
        k.bx(s * 1.5 - 0.2, s * 1.5 + 0.2, -1.0, -0.6, 0, 0.09, 'steelDark')
        k.bx(s * 1.5 - 0.2, s * 1.5 + 0.2, 1.6, 1.95, 0, 0.09, 'steelDark')
        k.col(s * 1.5 - 0.2, s * 1.5 + 0.2, -1.0, -0.6, 0, 2.0)
        k.col(s * 1.5 - 0.2, s * 1.5 + 0.2, 1.6, 1.95, 0, 2.0)
        k.beam((s * 1.3, -0.45, 1.0), (s * 1.3, 1.45, 1.0), 0.12, 'timber2')
    k.bx(-0.6, 0.6, 0.85, 1.15, 4.4, 4.7, 'timber2')
    k.beam((0.0, 0.0, 4.55), (0.0, 4.6, 4.3), 0.26, 'timber')
    k.beam((0.0, 1.2, 3.4), (0.0, 3.6, 4.25), 0.14, 'timber2')
    k.cyl(0.0, 4.4, 4.0, 0.25, 0.25, 0.12, 'cart', seg=10, rot=(0, 90, 0))
    k.bx(-0.03, 0.03, 4.62, 4.68, -6.2, 3.85, 'rope', ink=False)
    # the bucket hanging in the chasm
    k.cyl(0.0, 4.65, -7.2, 0.4, 0.5, 0.9, 'steel2', seg=10)
    k.cyl(0.0, 4.65, -6.3, 0.52, 0.52, 0.08, 'steelDark', seg=10, ink=False)
    k.beam((-0.45, 4.65, -6.3), (0.0, 4.65, -6.0), 0.03, 'steelDark', ink=False)
    k.beam((0.45, 4.662, -6.3), (0.0, 4.662, -6.0), 0.03, 'steelDark', ink=False)
    # hand winch on a skid, rope from its drum to the jib
    k.bx(-1.0, 1.0, -1.7, -0.95, 0, 0.15, 'steelDark')
    for x in (-0.8, 0.8):
        k.bx(x - 0.06, x + 0.06, -1.45, -1.2, 0.15, 1.0, 'steelDark')
    k.cyl(-0.75, -1.32, 0.85, 0.24, 0.24, 1.5, 'rope', seg=10, rot=(0, 90, 0))
    k.beam((0.8, -1.32, 0.85), (1.1, -1.32, 0.85), 0.05, 'steelDark')
    k.beam((1.1, -1.32, 0.85), (1.1, -1.55, 0.6), 0.04, 'red')
    k.beam((0.0, -1.1, 1.05), (0.0, 0.0, 4.5), 0.03, 'rope', ink=False)
    k.col(-1.0, 1.0, -1.7, -0.95, 0, 1.1)
    # buckets stacked by the lip, a lantern on the front leg
    for (x, y, z) in ((1.0, 0.6, 0.0), (1.0, 0.6, 0.62), (0.2, 0.9, 0.0)):
        k.cyl(x, y, z, 0.3, 0.38, 0.6, 'steel2', seg=10)
    k.col(0.0, 1.4, 0.2, 1.3, 0, 1.2)
    k.bx(-1.15, -0.8, -0.85, -0.79, 2.3, 2.36, 'steelDark', ink=False)
    lantern_g(k, -0.85, -0.82, 2.3, 0.85)
    CM.pool(k, -0.4, -1.2, POOL_Z['hoist'], 1.5, 99, sx=1.4, sy=0.9)
    sign_board(k, 0.0, -1.75, 1.2, 1.0, 0.5, [('HOIST 2', 0.16, 'ink'), ('KEEP CLEAR', 0.1, 'ink')], bg='hazard', rim='ink', s=-1)
    return k


def planks(k, variant):
    """2 x 2 floor decal: plank decking laid on the rock under the sorting station (no collision)."""
    k.begin()
    k.qz(-1.0, 1.0, -1.0, 1.0, Z_DECK, 1, 'plank' if variant == 0 else 'plank2')
    for i in range(1, 7):
        y = -1.0 + i * 2 / 7
        k.qz(-0.98, 0.98, y - 0.012, y + 0.012, Z_DECK + 0.003, 1, 'timber2')
    for (x, y) in ((-0.7, -0.6), (0.4, 0.2), (0.75, -0.9) if variant else (-0.2, 0.75)):
        k.qz(x - 0.02, x + 0.02, y - 0.02, y + 0.02, Z_DECK + 0.003, 1, 'steelDark')
    return k


# ================================================================ backdrop: the chasm beyond the east edge
def backdrop_chasm(k, L=34.0):
    """The chasm along the zone's east edge (origin: the middle of the lip line; Blender +X = away from the zone =
    game east, the chasm runs along Y for L m): the far cliff 27 - 31 m out falling into the black, end walls closing
    the fissure, glowing crystal outcrops rooted in the far face, old timber stagings with a ladder and a lamp."""
    k.begin()
    rnd = random.Random(141)
    fn = lambda f: 'cave' if f.normal.z > 0.55 else ('cave2' if f.calc_center_median().z > -10 else 'rockBack')
    H = L / 2 + 5.0
    y = -H
    slabs = []
    while y < H:   # the far cliff: slabs 5 - 8 m wide
        w = rnd.uniform(5.0, 8.0)
        x0 = rnd.uniform(27.0, 31.0)
        dz = rnd.uniform(0, 3)
        xb = x0 + 6 + rnd.uniform(0, 2)
        k.hullp([(x0, y, -60.0 - dz), (x0, y + w, -60.0 - dz), (xb, y, -60.0 - dz), (xb, y + w, -60.0 - dz),
                 (x0 + rnd.uniform(-1.5, 0.5), y + 0.3, rnd.uniform(-20, -6)), (x0 + rnd.uniform(-1.5, 0.5), y + w - 0.3, rnd.uniform(-20, -6)),
                 (x0 + rnd.uniform(-0.5, 1.0), y + w * 0.5, rnd.uniform(4, 12)), (x0 + 1.5, y + 0.2, 28.0 + dz), (x0 + 1.5, y + w - 0.2, 28.0 + dz),
                 (xb, y, 28.0 + dz), (xb, y + w, 28.0 + dz)], fn)
        slabs.append((y, y + w, x0))
        y += w * 0.85
    for s in (-1, 1):   # end walls from the zone edge to the far cliff
        yy = s * (L / 2 + 1.0)
        for j, x0 in enumerate((0.0, 10.0, 20.0)):
            b = 5.0 + j * 0.45
            k.hullp([(x0 - 1.0, yy, -60.0 - j), (x0 + 12.0, yy, -60.0 - j), (x0 - 1.0, yy + s * b, -60.0 - j), (x0 + 12.0, yy + s * b, -60.0 - j),
                     (x0, yy + s * rnd.uniform(-1.0, 0.5), rnd.uniform(-8, 4)), (x0 + 10, yy + s * rnd.uniform(-1.0, 0.5), rnd.uniform(-8, 4)),
                     (x0 - 1.0, yy + s * 0.5, 26.0 + j * 0.4), (x0 + 12.0, yy + s * 0.5, 26.0 + j * 0.4), (x0 - 1.0, yy + s * b, 26.0 + j * 0.4), (x0 + 12.0, yy + s * b, 26.0 + j * 0.4)], fn)
    # crystal outcrops rooted in the far face (no outline that far out)
    for i in range(8):
        yy = -L / 2 + 2 + i * (L - 4) / 7 + rnd.uniform(-1, 1)
        x0 = max(x for (a, b, x) in slabs if a <= yy <= b)
        z = rnd.uniform(-14.0, 9.0)
        g = KINDS[i % 4]
        for j in range(4):
            a = Vector((x0 + 0.8, yy + (j - 1.5) * 0.7, z + rnd.uniform(-0.6, 0.6)))
            d = Vector((-1.0, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.3, 0.7))).normalized()
            crystal(k, g, tuple(a), tuple(a + d * rnd.uniform(1.6, 3.0)), rnd.uniform(0.22, 0.38), outline=False)
    # an old timber staging with a ladder on the far face, a lamp left burning
    for (yy, z) in ((-6.0, -3.0), (8.0, 2.5)):
        x0 = max(x for (a, b, x) in slabs if a <= yy <= b) - 1.0
        k.bx(x0 - 3.2, x0 + 0.5, yy - 2.0, yy + 2.0, z - 0.2, z, 'timber2')
        for y2 in (yy - 1.8, yy + 1.8):
            k.beam((x0 - 3.0, y2, z - 0.1), (x0 + 0.3, y2, z - 2.6), 0.15, 'timber2')
        for y2 in (yy - 0.3, yy + 0.3):
            k.bx(x0 - 2.9, x0 - 2.8, y2 - 0.04, y2 + 0.04, z - 9.0, z + 1.2, 'timber')
        for i in range(10):
            k.bx(x0 - 2.88, x0 - 2.82, yy - 0.3, yy + 0.3, z - 8.6 + i * 0.9, z - 8.55 + i * 0.9, 'timber', ink=False)
        lantern_g(k, x0 - 2.8, yy + 1.4, z + 1.4, 1.2)
        k.bx(x0 - 2.85, x0 - 2.75, yy + 1.35, yy + 1.45, z, z + 1.45, 'timber')
    return k
