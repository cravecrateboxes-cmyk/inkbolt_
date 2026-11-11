"""kit-scrapyard: the scrap bank walls, the shared pieces (gate, trail fence, exit hoist, weapon stand) and zone 1, the
Stacks: crushed-car bales, flattened car stacks, scrap mountains and mounds, floodlight towers, the weighbridge and its
office, the baler line under the material-handling crane with its electromagnet, wrecked giant limbs and guns lying as
cover, piles of dead tech (monitors, server racks, cable drums, e-waste), tyres, skips, jersey barriers.
Conventions: sy_base.py.
"""
import math
import random

from mathutils import Vector

from sy_base import (SK, Z, WALL_H, TRAIL_H, CARS, srt, rock_pts, clamp_pts, slab, slab3, oslab, tube, drumx, drumy,
                     hull_box, tbox, pool_disc, sodium_head, text, sign_board, tyre, lattice, scrap_fn, heap, plate, ibeam, cable, vdisc)
from gem_base import stairs_x, deck, rail_x, rail_y
from foundry_common import guard_rail

V = Vector

# ================================================================ scrap bank walls
LV = [0.0, 1.3, 3.5, 5.8, 8.1, WALL_H]
EY = [-0.66, -0.6, -0.45, -0.24, 0.02, 0.26]


def face_y(z):
    for i in range(len(LV) - 1):
        if z <= LV[i + 1]:
            t = (z - LV[i]) / (LV[i + 1] - LV[i])
            return EY[i] + (EY[i + 1] - EY[i]) * t
    return EY[-1]


def bank_face(k, seed, amp=0.13, base=None):
    """The scrap bank: an open loft through one random middle station, the shared edge profile (EY at LV) at both
    ends so modules run on into one face; facets coloured as a jumble of rusty and grey scrap. The middle station
    always bulges out toward the yard (0.08 m or more past the edge profile at its height), so the faces either side
    of a module seam always meet at a crease and never lie in one plane (no coplanar overlap across modules)."""
    rnd = random.Random(seed)
    xm = rnd.uniform(-0.2, 0.2)
    ys, lv = [], [LV[0]]
    for i in range(1, len(LV) - 1):
        lv.append(LV[i] + rnd.uniform(-0.3, 0.3))
    lv.append(LV[-1])
    for i, y in enumerate(EY):
        ys.append(y - (rnd.uniform(0.04, 0.1) if i == 0 else rnd.uniform(0.08, 0.08 + amp)))
    prof = lambda yy, ll: [(y, z) for y, z in zip(yy, ll)] + [(0.5, WALL_H)]
    fn = strata_fn(seed, base or STRATA)
    k.loft([(-0.5, prof(EY, LV)), (xm, prof(ys, lv)), (0.5, prof(EY, LV))], fn, baffle='steelDark')


STRATA = ('gun2', 'rust2', 'steelDark', 'rust', 'gun2', 'steel2', 'rust2', 'gun')
GRAVE = ('gun2', 'navy2', 'steelDark', 'olive2', 'gun', 'navy2', 'rust2', 'steelDark')


def strata_fn(seed, bands):
    """Bank facets coloured in horizontal strata of compacted scrap (the bands run on from module to module), now and
    then a facet of another scrap colour; faces looking up a shade lighter."""
    def fn(f):
        c = f.calc_center_median()
        h = math.sin(c.x * 12.9898 + c.y * 78.233 + c.z * 37.719 + seed) * 43758.5453
        h -= math.floor(h)
        if f.normal.z > 0.6:
            return 'rustL' if h < 0.4 else 'gunL'
        if h < 0.22:
            return ('rust', 'steel2', 'rustL', 'gun')[int(h / 0.055) % 4]
        return bands[int(c.z / 1.25) % len(bands)]
    return fn


def junk(k, kind, x, z, rnd, out=0.0):
    """One piece of junk stuck in the bank face at (x, z): it juts out of the face by up to ~0.4 m."""
    y = face_y(z) + 0.06 - out
    if kind == 'plate':
        c = rnd.choice(('rust', 'steel2', 'gun', 'rustL') + CARS[:3])
        tbox(k, x, y - 0.08, z, rnd.uniform(0.4, 0.7), 0.05, rnd.uniform(0.3, 0.55), c, yaw=rnd.uniform(-25, 25), pitch=rnd.uniform(-30, 20), roll=rnd.uniform(-40, 40))
    elif kind == 'tyre':
        k.push(x, y - 0.06, rnd.uniform(-20, 20), z)
        k.cyl(0, 0.12, 0, 0.34, 0.34, 0.24, 'tire', seg=8, rot=(90, 0, 0))
        vdisc(k, 0, -0.124, 0, 0.17, 'steel2')
        k.pop()
    elif kind == 'beam':
        k.beam((x, y + 0.3, z), (x + rnd.uniform(-0.1, 0.1), y - 0.38, z + rnd.uniform(-0.25, 0.1)), 0.2, rnd.choice(('rust', 'rust2', 'hazard')))
    elif kind == 'pipe':
        tube(k, V((x, y + 0.3, z)), V((x + rnd.uniform(-0.2, 0.2), y - 0.3, z + rnd.uniform(-0.15, 0.15))), 0.12, rnd.choice(('steel', 'gunL', 'rust')), seg=6)
    elif kind == 'door':
        c = rnd.choice(CARS)
        k.push(x, y - 0.06, rnd.uniform(-15, 15), z)
        tbox(k, 0, 0, 0, 0.78, 0.07, 0.62, c, pitch=rnd.uniform(-15, 10), roll=rnd.uniform(-25, 25))
        k.pop()
    elif kind == 'rim':
        k.push(x, y - 0.03, rnd.uniform(-25, 25), z)
        k.cyl(0, 0.06, 0, 0.26, 0.26, 0.1, 'chrome', seg=8, rot=(90, 0, 0))
        vdisc(k, 0, -0.044, 0, 0.1, 'steelDark', n=6)
        k.pop()
    elif kind == 'finger':   # a giant robot finger segment
        oslab(k, (x, y + 0.35, z - 0.1), (x + rnd.uniform(-0.12, 0.12), y - 0.42, z + rnd.uniform(-0.1, 0.25)), 0.16, 0.14, 0.12, 0.1, rnd.choice(('bone', 'olive', 'navy')), ch=0.04)


JUNK = ('plate', 'door', 'plate', 'tyre', 'beam', 'door', 'plate', 'rim', 'pipe', 'door')


def bank_wall(k, kind, seed):
    """Scrap bank wall module (1 m, facing -Y, 9.6 m): the face and, per kind, junk, a sodium lamp on a bracket with its
    pool of light, a sign, or (the titan graveyard's) armour plates and fingers of dead war machines."""
    k.begin()
    rnd = random.Random(seed)
    grave = kind.startswith('G')
    bank_face(k, seed, base=GRAVE if grave else None)
    zs = [rnd.uniform(0.5, 1.6), rnd.uniform(2.6, 4.2), rnd.uniform(5.2, 7.6)]
    n = {'A': 2, 'B': 1, 'C': 2, 'GA': 1, 'GB': 2}.get(kind, 1)
    for i in range(n):
        x = rnd.uniform(-0.25, 0.25)
        junk(k, rnd.choice(('finger', 'plate', 'beam', 'pipe')) if grave else rnd.choice(JUNK), x, zs[i], rnd)
    if kind in ('Tyres', 'GTyres'):
        for i, z in enumerate((0.45, 1.15)):
            junk(k, 'tyre', rnd.uniform(-0.12, 0.12) + (0.0 if i == 0 else 0.05), z, rnd)
        junk(k, 'door', 0.0, 3.4, rnd)
    elif kind == 'Car':      # a crushed car nose-down in the bank
        k.push(0.0, face_y(2.6) - 0.15, rnd.uniform(-8, 8), 2.6)
        c = rnd.choice(CARS)
        tbox(k, 0, 0, 0, 0.86, 0.5, 0.9, c, pitch=-25, roll=rnd.uniform(-10, 10))
        tbox(k, 0, -0.22, 0.2, 0.7, 0.12, 0.3, 'glassD', pitch=-25, ink=False)
        k.pop()
        junk(k, 'rim', 0.15, 0.6, rnd)
    elif kind == 'GPlate':   # a titan armour plate leaning in the bank
        p0 = V((rnd.uniform(-0.08, 0.08), face_y(0.4) - 0.06, 0.0))
        plate(k, tuple(p0), (p0.x, face_y(3.6) - 0.02, 3.6), 0.86, 0.16, rnd.choice(('bone', 'olive', 'crimson', 'navy')), up=(0, -1, 0.25))
        k.qy(-0.3, 0.3, 1.6, 2.1, face_y(2.0) - 0.15, -1, 'hazard')
    elif kind == 'GFinger':
        junk(k, 'finger', -0.15, 1.1, rnd)
        junk(k, 'finger', 0.18, 1.5, rnd)
        junk(k, 'plate', 0.0, 4.6, rnd)
    elif kind.startswith('Lamp') or kind.startswith('GLamp'):
        f = kind[-1]
        y = face_y(4.6)
        k.bx(-0.08, 0.08, y - 0.9, y + 0.2, 4.55, 4.7, 'steelDark')
        k.beam((0.0, y - 0.2, 3.9), (0.0, y - 0.8, 4.56), 0.08, 'steelDark')
        sodium_head(k, 0.0, y - 0.95, 4.4, s=-1, w=0.5, h=0.3)
        pool_disc(k, 0.0, -2.4, Z[f], 2.4, seed, sx=1.15)
    elif kind in ('Sign1', 'Sign2', 'GSign'):
        y = face_y(3.4) - 0.1
        k.bx(-0.45, -0.4, y, y + 0.5, 1.8, 4.6, 'steelDark')
        k.bx(0.4, 0.45, y, y + 0.5, 1.8, 4.6, 'steelDark')
        lines = {'Sign1': [('RUSTMOOR', 0.3, None), ('SALVAGE', 0.24, 'crimson2')],
                 'Sign2': [('DANGER', 0.26, 'crimson2'), ('STACKS', 0.2, None), ('NO CLIMB', 0.18, None)],
                 'GSign': [('DANGER', 0.26, 'crimson2'), ('LIVE CORE', 0.2, None), ('KEEP OUT', 0.18, None)]}[kind]
        sign_board(k, 0.0, y - 0.004, 2.7, 0.96, 1.2, lines)
    elif kind == 'GLeak':    # a cold blue reactor leak glowing out of the bank
        y = face_y(1.0)
        k.gcyl(0.05, y - 0.05, 0.6, 0.28, 0.22, 0.5, 'cyan', seg=6, rot=(90, 0, 0))
        k.cyl(0.05, y + 0.1, 0.6, 0.38, 0.38, 0.14, 'gun2', seg=8, rot=(90, 0, 0))
        pool_disc(k, 0.05, -1.8, Z['blue'], 1.6, seed, c1='poolB', c2='cyanD')
    return k


def bank_corner(k, seed, grave=False):
    """Corners, notches and the ends of a bank: stacked scrap lumps all round, up to the wall top."""
    k.begin()
    rnd = random.Random(seed)
    z = 0.0
    fn = strata_fn(seed, GRAVE if grave else STRATA)
    while z < WALL_H - 0.1:
        h = min(rnd.uniform(3.4, 4.6), WALL_H - z + 0.5)
        top = z + h >= WALL_H - 0.01
        r = 0.7 - 0.12 * (z / WALL_H)
        pts = rock_pts(rnd, (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)), r, r, h + 0.5, z0=max(0.0, z - 0.5), n=7, top=0 if top else 2)
        if top or z + h + 0.5 >= WALL_H:
            pts = [(x, y, min(zz, WALL_H)) for (x, y, zz) in pts] + [(0.5, 0.5, WALL_H), (-0.5, 0.5, WALL_H), (0.5, -0.5, WALL_H), (-0.5, -0.5, WALL_H)]
        k.hullp(clamp_pts(pts, 0.62), fn)
        z += h
    junk(k, 'tyre', 0.0, 0.5, rnd, out=0.1)
    return k


# ================================================================ shared: gate, trail fence, exit hoist, weapon stand
def corrugated(k, x0, x1, z0, z1, y, s, c='gun', c2='gun2', every=0.25):
    """Corrugated sheet look on a -Y (s=-1) / +Y face: the sheet colour and darker vertical ribs 3 mm proud."""
    k.qy(x0, x1, z0, z1, y, s, c)
    n = int(round((x1 - x0) / every))
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        k.qy(xa + 0.02, xa + every * 0.45, z0 + 0.01, z1 - 0.01, y + s * 0.003, s, c2)


def gate_frame(k):
    """The yard gate: two I-beam columns with hazard-striped feet, a header with the yard board on both faces and
    beacons, corrugated infill up to the bank top."""
    k.begin()
    HD = 3.2
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.3)
        k.bx(x0, x1, -0.32, 0.32, 0.0, WALL_H - 0.45, 'gun2')
        for f in (-1, 1):
            k.bx(x0 - 0.06, x1 + 0.06, *srt(f * 0.32, f * 0.42), 0.0, WALL_H - 0.45, 'gun')
            k.stripes(x0 + 0.02, x1 - 0.02, 0.1, 1.4, f * 0.423, f, 4)
    k.bx(-2.45, 2.45, -0.5, 0.5, HD, HD + 0.6, 'rust2')
    k.bx(-2.45, 2.45, -0.12, 0.12, HD + 0.6, WALL_H - 0.4, 'gun2')
    for f in (-1, 1):
        corrugated(k, -1.5, 1.5, HD + 2.1, WALL_H - 0.45, f * 0.123, f)
        k.qy(-2.3, 2.3, HD + 0.22, HD + 0.36, f * 0.503, f, 'hazard')
        sign_board(k, 0.0, f * 0.125, HD + 0.68, 2.9, 1.3, [('RUSTMOOR', 0.42, None), ('SALVAGE YARD', 0.26, 'crimson2')], s=f)
        sodium_head(k, 0.0, f * 0.52, HD - 0.15, s=f, w=0.7, h=0.24)
        k.beacon(2.05 * -f, 0.0, WALL_H - 0.2, r=0.15)
    k.bx(-2.45, 2.45, -0.18, 0.18, WALL_H - 0.4, WALL_H - 0.2, 'rust')
    return k


def gate_shutter(k):
    """The sliding yard gate: a corrugated steel leaf in a hazard-striped frame (raised by the engine)."""
    k.begin()
    Hs = 3.05
    for f in (-1, 1):
        corrugated(k, -1.42, 1.42, 0.38, Hs - 0.12, f * 0.06, f, c='rust', c2='rust2', every=0.3)
    k.bx(-1.48, 1.48, -0.055, 0.055, 0.36, Hs - 0.12, 'gun2', ink=False)
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.36, 'ink' if j % 2 else 'hazard', ink=False)
    k.bx(-1.5, 1.5, -0.07, 0.07, Hs - 0.12, Hs, 'steelDark', ink=False)
    return k


def trail_wall(k, lamp=False, seed=1):
    """The fenced alley between the yards (1 m along Blender Y, alley toward +X): a corrugated steel fence, rails,
    an occasional sodium lamp on a bracket."""
    k.begin(90)
    k.bx(-0.5, 0.5, -0.05, 0.05, 0, TRAIL_H - 0.08, 'gun2')
    corrugated(k, -0.5, 0.5, 0.25, TRAIL_H - 0.1, -0.053, -1, c='rust2' if seed % 2 else 'gun', c2='rust' if seed % 2 else 'gun2')
    k.qy(-0.5, 0.5, 0.0, 0.25, -0.053, -1, 'conc2')
    for z in (1.1, 3.4):
        k.bx(-0.5, 0.5, -0.13, -0.06, z, z + 0.12, 'steelDark', ink=False)
    k.bx(-0.497, 0.497, -0.1, 0.1, TRAIL_H - 0.08, TRAIL_H, 'steelDark', ink=False)
    k.qy(-0.5, 0.5, 0.0, TRAIL_H - 0.1, 0.053, 1, 'gun2')
    if lamp:
        k.bx(-0.06, 0.06, -0.75, -0.05, 4.2, 4.32, 'steelDark')
        sodium_head(k, 0.0, -0.8, 4.0, s=-1, w=0.42, h=0.26)
    return k


def hatch(k):
    """Exit: the scrap hoist out of the yard. A chevron pad under a steel portal with the EXIT board and beacons."""
    k.begin()
    k.bx(-1.2, 1.2, -1.25, 1.0, 0, 0.05, 'steel2')
    for i in range(4):
        y = -1.15 + i * 0.5
        k.poly([(-0.9, y, 0.053), (0, y + 0.3, 0.053), (0.9, y, 0.053), (0.9, y + 0.14, 0.053), (0, y + 0.44, 0.053), (-0.9, y + 0.14, 0.053)], 'hazard' if i % 2 else 'cyan', (0, 0, 1))
    C0, C1, W, H = 1.05, 2.6, 1.3, 4.4
    k.bx(-W, W, C0, C1, 0, 0.14, 'steelDark')
    k.qz(-W + 0.05, W - 0.05, C0 + 0.02, C0 + 0.14, 0.143, 1, 'hazard')
    for x in (-W, W):
        k.bx(x - 0.08, x + 0.08, C0 - 0.08, C0 + 0.08, 0.14, H, 'rust')
        k.bx(x - 0.08, x + 0.08, C1 - 0.14, C1 - 0.02, 0.14, H, 'rust')
        k.stripes(x - 0.08, x + 0.08, 0.2, 1.6, C0 - 0.083, -1, 4)
    k.bx(-W + 0.09, W - 0.09, C1 - 0.08, C1 - 0.02, 0.16, 3.0, 'gun2')
    corrugated(k, -W + 0.09, W - 0.09, 0.2, 2.95, C1 - 0.083, -1)
    k.bx(-W - 0.08, W + 0.08, C0 - 0.1, C1, H, H + 0.25, 'rust2')
    sign_board(k, 0.0, C0 - 0.1, H - 0.95, 1.6, 0.8, [('EXIT', 0.36, 'crimson2')], s=-1)
    k.beacon(W - 0.1, C0, H + 0.25, r=0.13)
    k.beacon(-W + 0.1, C0, H + 0.25, r=0.13)
    sodium_head(k, 0.0, C0 + 0.3, H - 0.1, s=-1, w=0.6, h=0.22)
    pool_disc(k, 0.0, 0.3, Z['hatch'], 1.5, 7)
    return k


def stand(k):
    """Weapon stand: a steel trestle the new guns lean on."""
    k.begin()
    k.bx(-0.55, 0.55, -0.3, 0.3, 0.0, 0.12, 'steelDark')
    for x in (-0.45, 0.45):
        k.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.12, 1.0, 'hazard')
    k.bx(-0.48, 0.48, -0.06, 0.06, 0.88, 0.98, 'rust')
    return k


# ================================================================ crushed cars
def bale(k, cx, cy, z0, c, seed, w=1.8, d=1.8, h=1.12, yaw=0.0):
    """One crushed-car bale: a skewed cube in the car's paint with rust faces, a crushed window band, a wheel and a
    bumper line pressed into its sides."""
    rnd = random.Random(seed)
    k.push(cx, cy, yaw, z0)
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz, zz in ((0, 0.0), (1, h)):
                j = 0.06 if sz else 0.02
                pts.append((sx * w / 2 + rnd.uniform(-j, j), sy * d / 2 + rnd.uniform(-j, j), zz + (rnd.uniform(-0.05, 0.03) if sz else 0)))
    for i in range(4):   # crushed sides bulge here and there
        a = i * math.pi / 2 + rnd.uniform(-0.4, 0.4)
        pts.append((math.cos(a) * (w / 2 + rnd.uniform(0.0, 0.05)), math.sin(a) * (d / 2 + rnd.uniform(0.0, 0.05)), h * rnd.uniform(0.3, 0.7)))
    fn = lambda f, c=c: ('rust' if f.normal.z > 0.7 and rnd.random() < 0.4 else ('rust2' if f.normal.z < -0.5 else c))
    k.hullp(pts, fn)
    # pressed-in detail on the four sides (flat, 6 mm proud of the side's nominal plane): the crushed window band, a
    # wheel or a door of another colour, a diagonal crumple, a rust patch
    for side in range(4):
        k.push(0, 0, side * 90)
        dd = (d if side % 2 == 0 else w) / 2 + 0.06
        ww = (w if side % 2 == 0 else d) / 2 - 0.12
        r = rnd.random()
        zb = rnd.uniform(0.35, 0.6)
        k.qy(-ww, ww, zb, zb + rnd.uniform(0.08, 0.16), -dd, -1, 'glassD')
        if r < 0.4:
            vdisc(k, rnd.uniform(-ww + 0.3, ww - 0.3), -dd - 0.004, 0.22, 0.19, 'tire', n=7)
        elif r < 0.7:
            x0 = rnd.uniform(-ww, 0.0)
            k.qy(x0, x0 + rnd.uniform(0.4, 0.7), 0.7, rnd.uniform(0.9, 1.0), -dd - 0.004, -1, rnd.choice(CARS))
        x0, z0 = rnd.uniform(-ww, ww * 0.2), rnd.uniform(0.12, 0.3)
        xa, za = x0 + rnd.uniform(0.25, 0.4), z0 + rnd.uniform(0.25, 0.4)
        xb, zb = xa + rnd.uniform(0.2, 0.35), za - rnd.uniform(0.15, 0.3)
        k.poly([(x0, -dd - 0.008, z0), (x0 + 0.05, -dd - 0.008, z0 - 0.03), (xa + 0.04, -dd - 0.008, za - 0.05), (xa, -dd - 0.008, za)], 'steelDark', (0, -1, 0))
        k.poly([(xa, -dd - 0.008, za), (xa + 0.04, -dd - 0.008, za - 0.05), (xb, -dd - 0.008, zb - 0.03), (xb - 0.02, -dd - 0.008, zb + 0.03)], 'steelDark', (0, -1, 0))
        if rnd.random() < 0.5:
            xr = rnd.uniform(-ww + 0.2, ww - 0.4)
            k.poly([(xr, -dd - 0.012, 0.75), (xr + 0.35, -dd - 0.012, 0.8), (xr + 0.42, -dd - 0.012, 1.0), (xr + 0.05, -dd - 0.012, 1.02)], 'rust', (0, -1, 0))
        k.pop()
    k.pop()


def bales(k, n, seed):
    """Stack of n crushed-car bales on a 2 x 2 footprint (1.12 m a bale), each a different car colour."""
    k.begin()
    rnd = random.Random(seed)
    cols = list(CARS)
    rnd.shuffle(cols)
    z = 0.0
    for i in range(n):
        h = 1.12 + rnd.uniform(-0.04, 0.04)
        bale(k, rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), z, cols[i % len(cols)], seed * 10 + i, h=h, yaw=rnd.uniform(-4, 4))
        z += h + 0.004
    k.col(-0.95, 0.95, -0.95, 0.95, 0, z)
    return k


def pancakes(k, n, seed):
    """Flattened cars stacked n high on a 2 x 4 footprint (0.42 m a car): crushed roof lines, wheels at the sides."""
    k.begin()
    rnd = random.Random(seed)
    z = 0.0
    for i in range(n):
        c = rnd.choice(CARS)
        h = 0.42 + rnd.uniform(-0.03, 0.03)
        k.push(rnd.uniform(-0.1, 0.1), rnd.uniform(-0.15, 0.15), rnd.uniform(-6, 6), z)
        pts = []
        for sx in (-1, 1):
            for sy, yy in ((-1, -1.92), (1, 1.92)):
                for zz in (0.0, h):
                    pts.append((sx * (0.9 if zz else 0.93), yy * (0.97 if zz else 1.0), zz + (rnd.uniform(-0.03, 0.02) if zz else 0)))
        pts += [(0, -1.95, h * 0.5), (0, 1.95, h * 0.5), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.5, 0.5), h + rnd.uniform(0.02, 0.1))]
        k.hullp(pts, lambda f, c=c: 'rust2' if f.normal.z < -0.5 else ('rust' if f.normal.z > 0.6 and i % 3 == 1 else c))
        for sx in (-1, 1):   # tyres squashed at the sides, the window line
            for yy in (-1.25, 1.2):
                vdisc(k, sx * 0.937, yy, h * 0.42, 0.19, 'tire', axis='x', s=sx, n=6)
            k.qx(-0.6, 0.6, h * 0.55, h * 0.8, sx * 0.94, sx, 'glassD')
            if (i + (sx > 0)) % 2:
                k.poly([(sx * 0.944, -1.6, h * 0.2), (sx * 0.944, -1.5, h * 0.2), (sx * 0.944, -0.9, h * 0.75), (sx * 0.944, -1.0, h * 0.75)], 'rust', (sx, 0, 0))
        k.pop()
        z += h + 0.004
    k.col(-0.98, 0.98, -1.98, 1.98, 0, z)
    return k


# ================================================================ scrap mountains, mounds
def scrap_heap(k, seed, R=4.6, H=6.2):
    """A scrap mountain [10, 10]: a main hull and side lumps, cars, beams, tyres and plates sticking out of it."""
    k.begin()
    rnd = random.Random(seed)
    heap(k, 0.0, 0.0, R, R * 0.92, H, seed, n=11, top=5)
    for i in range(4):
        a = i * math.pi / 2 + rnd.uniform(-0.5, 0.5)
        r = rnd.uniform(1.6, 2.2)
        heap(k, math.cos(a) * (R - r * 0.5), math.sin(a) * (R - r * 0.5), r, r * 0.9, H * rnd.uniform(0.35, 0.5), seed + i + 1, n=7, top=2)
    for i in range(12):   # junk on the flanks
        a = rnd.uniform(0, 2 * math.pi)
        t = rnd.uniform(0.25, 0.75)
        rr = R * (1 - t) * 0.95 + 0.4
        z = H * t * 0.85
        x, y = math.cos(a) * rr, math.sin(a) * rr
        kind = ('car', 'beam', 'tyre', 'plate', 'car', 'pipe', 'tyre', 'plate', 'beam', 'tyre', 'car', 'plate')[i]
        if kind == 'car':
            c = rnd.choice(CARS)
            k.push(x, y, math.degrees(a) + 90, z - 0.3)
            tbox(k, 0, 0, 0, 1.7, 3.6, 1.1, c, pitch=rnd.uniform(15, 35), roll=rnd.uniform(-20, 20))
            tbox(k, 0, -0.4, 0.45, 1.5, 1.4, 0.5, 'glassD', pitch=rnd.uniform(15, 35), ink=False)
            k.pop()
        elif kind == 'beam':
            ibeam(k, (x * 0.7, y * 0.7, z + 0.5), (x * 1.15, y * 1.15, z + rnd.uniform(1.5, 2.6)), h=0.4, w=0.26, c=rnd.choice(('rust', 'hazard')))
        elif kind == 'tyre':
            tyre(k, x, y, z + 0.2, r=0.42, w=0.3, axis=rnd.choice(('x', 'y')))
        elif kind == 'plate':
            plate(k, (x * 0.8, y * 0.8, z), (x * 1.05, y * 1.05, z + 1.6), 1.2, 0.08, rnd.choice(('steel2', 'rustL', 'gunL')), up=(math.cos(a), math.sin(a), 0.4))
        else:
            tube(k, V((x * 0.75, y * 0.75, z)), V((x * 1.2, y * 1.2, z + 0.6)), 0.18, 'steel', seg=8)
    k.col(-R * 0.95, R * 0.95, -R * 0.9, R * 0.9, 0, H)
    return k


def mound(k, seed):
    """A small scrap mound [4, 4] (about 2 m) with a tyre, a door and a beam end."""
    k.begin()
    rnd = random.Random(seed)
    heap(k, 0.0, 0.0, 1.75, 1.6, rnd.uniform(1.8, 2.3), seed, n=8, top=3)
    heap(k, rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 1.0, 0.9, 2.6, seed + 3, n=6, top=2, z0=0.3)
    tyre(k, rnd.uniform(-1.2, 1.2), -1.25, 0.55, r=0.38, w=0.26, axis='y')
    plate(k, (1.0, 0.6, 0.4), (1.5, 0.9, 1.6), 0.9, 0.06, rnd.choice(CARS), up=(1, 0.3, 0.3))
    ibeam(k, (-0.6, 0.4, 1.3), (-1.7, 0.9, 2.2), h=0.3, w=0.2, c='rust')
    k.col(-1.6, 1.6, -1.5, 1.5, 0, 2.2)
    return k


# ================================================================ floodlight tower
def flood_tower(k):
    """Floodlight tower [2, 2]: a lattice mast on a concrete footing to 13 m, a head frame with sodium lamps aimed out
    and down on all four sides, a ladder, a cabinet, a red aircraft beacon, and the pool of light on the ground."""
    k.begin()
    k.bx(-0.7, 0.7, -0.7, 0.7, 0, 0.5, 'conc')
    k.qz(-0.7, 0.7, -0.7, 0.7, 0.503, 1, 'conc2')
    lattice(k, -0.42, 0.42, -0.42, 0.42, 0.5, 12.6, c='steel2', t=0.065, every=2.4, braces=False)
    for i in range(4):   # X bracing on the lower half only (the head frame is braced by its platform)
        k.push(0, 0, i * 90)
        k.beam((-0.42, -0.42, 0.6), (0.42, -0.42, 4.2), 0.04, 'steel2', ink=False)
        k.beam((0.42, -0.42, 4.4), (-0.42, -0.42, 8.0), 0.04, 'steel2', ink=False)
        k.pop()
    k.bx(-1.1, 1.1, -1.1, 1.1, 12.6, 12.75, 'steelDark')
    for i in range(4):
        k.push(0, 0, i * 90)
        sodium_head(k, 0.0, -1.15, 12.35, s=-1, w=1.3, h=0.42)
        k.bx(-1.0, 1.0, -1.1, -1.04, 12.75, 13.3, 'hazard', ink=False)
        k.pop()
    k.beacon(0.0, 0.0, 12.75, r=0.16)
    for x in (-0.18, 0.18):   # ladder up the -Y face
        k.bx(x - 0.025, x + 0.025, -0.55, -0.5, 0.5, 12.6, 'hazard', ink=False)
    for i in range(24):
        z = 0.85 + i * 0.5
        k.qy(-0.18, 0.18, z, z + 0.04, -0.553, -1, 'hazard')
    k.bx(0.45, 0.95, -0.35, 0.15, 0.5, 1.4, 'gun')   # electrical cabinet
    k.qx(-0.25, 0.05, 0.9, 1.1, 0.953, 1, 'hazard')
    k.beam((0.7, -0.1, 1.35), (0.42, -0.1, 2.4), 0.04, 'cable', ink=False)
    pool_disc(k, 0.0, 0.0, Z['tower'], 6.2, 11, n=20)
    k.col(-0.7, 0.7, -0.7, 0.7, 0, 12.75)
    return k


# ================================================================ the weighbridge and its office
def weighbridge(k):
    """The truck scale in the haul road [4, 10]: a chequer-plate deck flush with the ground on a concrete frame,
    hazard ends, a reading on the deck."""
    k.begin()
    zt = Z['piece']
    k.qz(-1.95, 1.95, -4.95, 4.95, zt, 1, 'conc2')
    k.qz(-1.7, 1.7, -4.7, 4.7, zt + 0.004, 1, 'steel2')
    for i in range(1, 6):
        x = -1.7 + i * 3.4 / 6
        k.qz(x - 0.015, x + 0.015, -4.7, 4.7, zt + 0.008, 1, 'steelDark')
    for y in (-1.6, 1.6):
        k.qz(-1.7, 1.7, y - 0.015, y + 0.015, zt + 0.012, 1, 'steelDark')
    for s in (-1, 1):
        y0, y1 = srt(s * 4.25, s * 4.7)
        k.qz(-1.7, 1.7, y0, y1, zt + 0.016, 1, 'hazard')
        for j in range(6):
            x = -1.6 + j * 0.6
            k.poly([(x, y0, zt + 0.02), (x + 0.25, y0, zt + 0.02), (x + 0.45, y1, zt + 0.02), (x + 0.2, y1, zt + 0.02)], 'ink', (0, 0, 1))
    text(k, '40 T', 0.0, 0.0, zt + 0.024, 0.9, 'sign', face='up', valign='m')
    return k


def office(k):
    """Weighbridge office [8, 6]: a portacabin on blocks (door and window to the south, the big window to the scale on
    the east end, warm light inside), an AC unit, the yard board on the roof edge, a steel stair up the back to the
    railed roof deck at 3.15 m (high ground)."""
    k.begin()
    X0, X1, Y0, Y1, ZB, ZT = -3.1, 3.1, -1.5, 1.5, 0.3, 3.1
    for x in (-2.7, 0.0, 2.7):
        for y in (-1.2, 1.2):
            k.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0, ZB, 'conc2')
    k.bx(X0, X1, Y0, Y1, ZB, ZT, 'carW')
    k.bx(X0 - 0.06, X1 + 0.06, Y0 - 0.06, Y1 + 0.06, ZT - 0.04, ZT + 0.05, 'steelDark')
    for f in (-1, 1):   # ribbed cladding lines on the long faces
        y = (Y0 if f < 0 else Y1) + f * 0.003
        for i in range(1, 12):
            x = X0 + i * (X1 - X0) / 12
            k.qy(x - 0.02, x + 0.02, ZB + 0.08, ZT - 0.08, y, f, 'beige2')
    yf = Y0 - 0.006
    # south face: door (west), a window
    k.qy(-2.6, -1.7, ZB + 0.05, 2.35, yf, -1, 'gun2')
    k.gquad_y(-2.5, -1.8, 1.55, 2.2, yf - 0.003, -1, 'sodium')
    k.qy(-2.1, -2.0, 1.1, 1.25, yf - 0.003, -1, 'chrome')
    k.qy(-0.9, 1.9, 1.15, 2.35, yf, -1, 'steelDark')
    k.gquad_y(-0.82, 1.82, 1.22, 2.28, yf - 0.003, -1, 'sodium')
    for x in (0.1, 1.0):
        k.qy(x - 0.03, x + 0.03, 1.22, 2.28, yf - 0.006, -1, 'steelDark')
    # east end: the window over the scale
    xe = X1 + 0.006
    k.qx(-1.2, 1.2, 1.15, 2.4, xe, 1, 'steelDark')
    k.g.qx(-1.12, 1.12, 1.22, 2.33, xe + 0.003, 1, 'sodium')
    k.qx(-0.02, 0.02, 1.22, 2.33, xe + 0.006, 1, 'steelDark')
    # steps up to the door
    k.bx(-2.85, -1.45, Y0 - 0.75, Y0 - 0.02, 0, 0.27, 'steel2')
    k.colw(-2.85, -1.45, Y0 - 0.75, Y0 - 0.02, 0, 0.27)
    # AC unit on the west end, a vent, cable to the pole
    k.bx(X0 - 0.6, X0 - 0.02, -0.5, 0.4, 1.0, 1.7, 'beige')
    k.cyl(X0 - 0.605, -0.05, 1.35, 0.25, 0.25, 0.004, 'steelDark', seg=10, rot=(0, -90, 0), ink=False)
    # the board on the roof edge, facing south
    k.bx(-1.9, -1.84, Y0 + 0.17, Y0 + 0.23, ZT + 0.05, ZT + 1.4, 'steelDark')
    k.bx(1.84, 1.9, Y0 + 0.17, Y0 + 0.23, ZT + 0.05, ZT + 1.4, 'steelDark')
    sign_board(k, 0.0, Y0 + 0.098, ZT + 0.45, 4.2, 1.0, [('RUSTMOOR SALVAGE', 0.34, None), ('WEIGHBRIDGE  -  OFFICE', 0.2, 'crimson2')])
    # roof deck: the cabin roof (walkable), railings round it but at the stair head
    k.qz(X0 + 0.05, X1 - 0.05, Y0 + 0.05, Y1 - 0.05, ZT + 0.053, 1, 'gun2')
    k.colw(X0, X1, Y0, Y1, ZB, ZT + 0.05)
    rail_x(k, X0 + 0.05, X1 - 0.05, Y0 + 0.28, ZT + 0.05, post=1.55)
    rail_y(k, Y0 + 0.3, Y1 - 0.2, X1 - 0.08, ZT + 0.05, post=1.4)
    rail_y(k, Y0 + 0.3, Y1 - 0.05, X0 + 0.08, ZT + 0.05, post=1.4)
    rail_x(k, X0 + 0.05, 1.3, Y1 - 0.08, ZT + 0.05, post=1.35)
    # the stair up the back (+Y side): from the ground at the west to a landing at the east, onto the roof
    stairs_x(k, -3.3, 1.7, 1.62, 2.62, 0.0, ZT + 0.05 - 0.315, 10, rails=(False, True))
    deck(k, 1.7, 3.1, 1.58, 2.72, ZT + 0.05, t=0.12, grate=True, along='y')
    rail_y(k, 1.62, 2.72, 3.08, ZT + 0.05, post=1.1)
    rail_x(k, 1.7, 3.08, 2.75, ZT + 0.05, post=1.4)
    for (x, y) in ((1.75, 2.66), (3.04, 2.66), (3.04, 1.58)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, ZT - 0.08, 'steelDark')
        k.col(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, ZT - 0.08)
    k.cyl(2.6, -0.9, ZT + 0.05, 0.05, 0.05, 1.5, 'steelDark', seg=6, ink=False)   # antenna
    k.beacon(-2.8, 1.25, ZT + 0.05, r=0.12)
    k.col(X0 - 0.6, X0, -0.5, 0.4, 1.0, 1.7)
    pool_disc(k, -0.4, -3.0, Z['piece2'], 2.0, 21, sx=1.6, sy=0.7)
    return k


# ================================================================ the baler line and the material-handling crane
def baler(k):
    """The car baler [14, 12] (local x along the line): the charging box with a car in it under the magnet, the press
    housing with its rams, the bale chute and the roller table with a fresh bale, the power pack, the operator's
    platform at 2.4 m with its stair and console, hazard paint, beacons."""
    k.begin()
    Y0, Y1 = 2.0, 5.2
    # charging box (open top): walls, floor, the car crushed into it
    k.bx(-6.6, -1.2, Y0, Y1, 0, 0.5, 'gun2')
    for (x0, x1, y0, y1) in ((-6.6, -1.2, Y0, Y0 + 0.3), (-6.6, -1.2, Y1 - 0.3, Y1), (-6.6, -6.3, Y0 + 0.3, Y1 - 0.3)):
        k.bx(x0, x1, y0, y1, 0.5, 2.3, 'carY')
    k.stripes(-6.5, -1.3, 0.55, 0.95, Y0 - 0.003, -1, 14)
    k.bx(-6.62, -1.18, Y0 - 0.02, Y0 + 0.32, 2.3, 2.42, 'steelDark')
    k.bx(-6.62, -1.18, Y1 - 0.32, Y1 + 0.02, 2.3, 2.42, 'steelDark')
    tbox(k, -3.9, 3.6, 1.0, 3.6, 1.7, 0.9, 'carB', roll=4)
    tbox(k, -4.3, 3.6, 1.55, 1.6, 1.4, 0.35, 'glassD', roll=4, ink=False)
    # press housing: the box, side ram cylinders, the lid ram on top
    k.bx(-1.2, 3.0, Y0 - 0.2, Y1 + 0.2, 0, 3.4, 'carY')
    k.bx(-1.25, 3.05, Y0 - 0.25, Y1 + 0.25, 3.4, 3.6, 'steelDark')
    k.stripes(-1.1, 2.9, 0.1, 0.5, Y0 - 0.203, -1, 10)
    for y in (Y0 + 0.7, Y1 - 0.7):
        drumx(k, -1.2 - 2.0, y, 3.0, 0.22, 2.4, 'chrome', seg=8)
        drumx(k, 0.9, y, 3.85, 0.3, 3.0, 'steel2', seg=8)
    k.bx(-0.3, 2.1, Y0 + 0.4, Y1 - 0.4, 3.6, 4.4, 'gun')
    drumy(k, 0.9, 3.6, 4.65, 0.32, 2.2, 'steel2', seg=8)
    k.beacon(2.7, Y0 + 0.1, 3.6, r=0.15)
    k.beacon(-0.9, Y1 - 0.1, 3.6, r=0.15)
    text(k, 'BALER 2', 0.9, Y0 - 0.206, 1.6, 0.48, 'ink', face='y-', maxw=3.4)
    # bale chute, roller table, a fresh bale
    k.bx(3.0, 3.8, Y0 + 0.4, Y1 - 0.4, 0, 1.25, 'gun2')
    k.bx(3.8, 7.0, Y0 + 0.3, Y1 - 0.3, 0, 0.6, 'steelDark')
    for i in range(7):
        drumy(k, 4.05 + i * 0.45, 3.6, 0.66, 0.06, 2.4, 'steel', seg=6, ink=False)
    bale(k, 5.6, 3.6, 0.72, 'carR', 77, w=1.4, d=1.5, h=1.0)
    # power pack behind the press, hoses
    k.bx(-0.8, 2.6, Y1 + 0.3, 6.6, 0, 1.6, 'gun')
    k.qx(5.6, 6.4, 0.4, 1.2, 2.603, 1, 'steelDark')
    for i in range(3):
        cable(k, (-0.4 + i * 0.6, Y1 + 0.35, 1.5), (-0.4 + i * 0.6, Y1 + 0.2, 3.0), 0.2, 0.05, c='cable', n=3)
    # operator platform at 2.4 m on the south side of the press, stair from the west, console
    PZ = 2.4
    deck(k, -1.2, 3.0, 0.4, 1.78, PZ, t=0.12, grate=True)
    rail_x(k, -1.2, 3.0, 0.45, PZ, post=1.4)
    rail_y(k, 0.45, 1.75, 2.97, PZ, post=1.3)
    for (x, y) in ((-1.1, 0.5), (2.9, 0.5), (2.9, 1.7)):
        k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, PZ - 0.12, 'steelDark')
        k.col(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, PZ - 0.12)
    stairs_x(k, -5.2, -1.2, 0.4, 1.4, 0.0, PZ, 8, rails=(True, False))
    k.bx(1.0, 1.9, 1.3, 1.75, PZ, PZ + 1.06, 'gun2')                      # console
    k.hullp([(0.97, 1.3, PZ + 1.1), (1.93, 1.3, PZ + 1.1), (0.97, 1.0, PZ + 1.0), (1.93, 1.0, PZ + 1.0), (0.97, 1.75, PZ + 1.1), (1.93, 1.75, PZ + 1.1)], 'gun')
    k.g.poly([(1.08, 1.06, PZ + 1.012), (1.82, 1.06, PZ + 1.012), (1.82, 1.28, PZ + 1.102), (1.08, 1.28, PZ + 1.102)], 'cyan', (0, -0.3, 1))
    k.col(1.0, 1.9, 1.3, 1.75, PZ, PZ + 1.1)
    # collision: charging box walls, press, chute + table + bale, power pack
    k.col(-6.6, -1.2, Y0, Y1, 0, 2.42)
    k.col(-1.25, 3.05, Y0 - 0.25, Y1 + 0.25, 0, 4.4)
    k.col(3.0, 7.0, Y0 + 0.3, Y1 - 0.3, 0, 1.72)
    k.col(-0.8, 2.6, Y1 + 0.3, 6.6, 0, 1.6)
    pool_disc(k, 0.5, -0.8, Z['piece'], 3.0, 31, sx=1.8, sy=0.9)
    return k


CR = V((1.6, -3.4, 0.0))     # crane turntable centre (baler frame)


def crane(k):
    """The material handler (placed with the baler, its frame): crawler tracks, turntable, the engine house, the
    raised cab (lit), the boom and stick reaching north over the charging box, the electromagnet on its chains with
    a crushed car stuck to it, rams, beacons."""
    k.begin()
    cx, cy = CR.x, CR.y
    for s in (-1, 1):   # crawler tracks along x
        y0, y1 = srt(cy + s * 1.0, cy + s * 2.0)
        k.hullp([(cx - 2.6, y0, 0.35), (cx - 2.3, y0, 0.0), (cx + 2.3, y0, 0.0), (cx + 2.6, y0, 0.35), (cx + 2.4, y0, 1.05), (cx - 2.4, y0, 1.05),
                 (cx - 2.6, y1, 0.35), (cx - 2.3, y1, 0.0), (cx + 2.3, y1, 0.0), (cx + 2.6, y1, 0.35), (cx + 2.4, y1, 1.05), (cx - 2.4, y1, 1.05)], 'tire')
        yf = (y0 if s < 0 else y1) + s * 0.004
        for i in range(5):
            vdisc(k, cx - 1.8 + i * 0.9, yf + s * 0.002, 0.52, 0.3, 'steelDark', s=s)
        k.qy(cx - 2.2, cx + 2.2, 0.9, 0.98, yf + s * 0.002, s, 'hazard')
    k.bx(cx - 1.2, cx + 1.2, cy - 1.0, cy + 1.0, 1.0, 1.3, 'steelDark')
    k.cyl(cx, cy, 1.3, 1.5, 1.5, 0.3, 'gun2', seg=12)
    # engine house (counterweight at the back, -y), hazard bands
    k.bx(cx - 1.4, cx + 1.4, cy - 2.4, cy + 0.9, 1.6, 3.2, 'carO')
    k.bx(cx - 1.5, cx + 1.5, cy - 2.7, cy - 2.2, 1.55, 2.9, 'gun2')
    k.stripes(cx - 1.4, cx + 1.4, 2.6, 2.85, cy - 2.703, -1, 10)
    k.qx(cy - 1.8, cy - 0.6, 2.2, 2.8, cx + 1.403, 1, 'steelDark')   # engine grille
    k.cyl(cx + 0.9, cy - 1.6, 3.2, 0.12, 0.12, 0.9, 'steelDark', seg=6)   # exhaust
    text(k, 'RUSTMOOR', cx, cy - 2.705, 1.9, 0.42, 'ink', face='y-', maxw=2.6)
    # raised cab on its column (front left)
    k.bx(cx - 1.3, cx - 0.9, cy + 0.3, cy + 0.7, 3.2, 4.6, 'gun')
    k.bx(cx - 1.75, cx - 0.35, cy + 0.0, cy + 1.6, 4.6, 6.2, 'carO')
    k.bx(cx - 1.8, cx - 0.3, cy - 0.05, cy + 1.65, 6.2, 6.3, 'steelDark')
    k.gbx(cx - 1.7, cx - 0.4, cy + 1.6, cy + 1.61, 5.0, 6.05, 'sodium', hull=False)
    k.g.qx(cy + 0.15, cy + 1.45, 5.0, 6.05, cx - 1.753, -1, 'sodium')
    k.g.qx(cy + 0.15, cy + 1.45, 5.0, 6.05, cx - 0.347, 1, 'sodium')
    k.beacon(cx - 1.05, cy + 0.8, 6.3, r=0.14)
    sodium_head(k, cx - 1.05, cy + 1.62, 6.45, s=1, w=0.5, h=0.24)
    # boom: foot at the house front, rising north; the stick hangs from its tip down over the charging box
    P0 = V((cx + 0.5, cy + 0.8, 3.0))
    P1 = V((-1.4, 2.0, 12.6))
    P2 = V((-3.9, 3.6, 8.2))
    oslab(k, P0, P1, 0.42, 0.55, 0.32, 0.42, 'carO', ch=0.12)
    drumx(k, P0.x, P0.y, P0.z, 0.45, 1.0, 'steelDark', seg=10)
    drumx(k, P1.x, P1.y, P1.z, 0.42, 0.9, 'steelDark', seg=10)
    oslab(k, P1, P2, 0.3, 0.36, 0.24, 0.28, 'carO', ch=0.08)
    drumx(k, P2.x, P2.y, P2.z, 0.28, 0.7, 'steelDark', seg=8)
    # rams: house -> boom, boom -> stick
    R0, R1 = V((cx + 0.5, cy + 0.6, 1.9)), P0.lerp(P1, 0.45)
    tube(k, R0, R0.lerp(R1, 0.6), 0.2, 'steelDark', seg=8)
    tube(k, R0.lerp(R1, 0.55), R1, 0.11, 'chrome', seg=6, ink=False)
    R2, R3 = P0.lerp(P1, 0.8) + V((0, 0, 0.5)), P1.lerp(P2, 0.25) + V((0, 0, 0.4))
    tube(k, R2, R3, 0.14, 'steelDark', seg=6)
    # hoses down the boom
    k.beam(tuple(P0 + V((0.45, 0, 0.3))), tuple(P1 + V((0.4, 0, 0.3))), 0.06, 'cable', ink=False)
    # magnet: chains from the stick tip, the disc, the cable, a crushed car stuck under it
    MZ = 5.2
    for a in range(3):
        t = a / 3 * 2 * math.pi
        k.beam(tuple(P2 + V((0, 0, -0.25))), (P2.x + math.cos(t) * 0.55, P2.y + math.sin(t) * 0.55, MZ + 0.55), 0.05, 'steelDark', ink=False)
    k.cyl(P2.x, P2.y, MZ, 0.95, 0.95, 0.55, 'gun2', seg=14)
    k.cyl(P2.x, P2.y, MZ + 0.55, 0.6, 0.4, 0.2, 'steelDark', seg=10)
    k.cyl(P2.x, P2.y, MZ - 0.004, 0.85, 0.85, 0.004, 'steel', seg=14, ink=False)
    k.qy(P2.x - 0.4, P2.x + 0.4, MZ + 0.12, MZ + 0.42, P2.y - 0.955, -1, 'hazard')
    cable(k, tuple(P2 + V((0.3, 0, -0.2))), (P2.x + 0.3, P2.y - 0.2, MZ + 0.75), 0.15, 0.04, n=3)
    tbox(k, P2.x + 0.1, P2.y, MZ - 0.5, 1.5, 2.9, 0.95, 'carG', roll=8, pitch=-6)
    tbox(k, P2.x + 0.15, P2.y - 0.3, MZ - 0.95, 1.2, 1.3, 0.12, 'glassD', roll=8, pitch=-6, ink=False)
    k.col(cx - 2.6, cx + 2.6, cy - 2.7, cy + 2.0, 0, 3.2)
    k.col(cx - 1.8, cx - 0.3, cy - 0.05, cy + 1.65, 3.2, 6.3)
    return k


# ================================================================ wrecked giant limbs and guns (cover)
def giant_hand(k, seed=1, paint='bone'):
    """A giant robot hand [4, 4] lying palm up: armoured back plate, palm block, three fingers and a thumb curled up
    (1.0 - 1.7 m), the wrist torn open with pistons and cables."""
    k.begin()
    rnd = random.Random(seed)
    slab(k, 0.0, 0.2, 0.0, 0.85, 1.25, 1.05, 1.15, 0.95, 'gun2', ch=0.25)
    slab(k, 0.0, 0.2, 0.85, 1.0, 1.1, 0.9, 1.05, 0.85, paint, ch=0.22)
    for i, x in enumerate((-0.8, 0.0, 0.8)):
        a = V((x, -0.7, 0.75))
        b = a + V((rnd.uniform(-0.05, 0.05), -0.75, 0.45))
        c = b + V((0, -0.3, 0.55 + 0.1 * (i == 1)))
        oslab(k, a, b, 0.3, 0.28, 0.27, 0.25, paint, ch=0.07)
        drumx(k, b.x, b.y, b.z, 0.27, 0.62, 'gun', seg=8)
        oslab(k, b, c, 0.25, 0.23, 0.17, 0.16, 'gun2', ch=0.05)
    t0 = V((1.15, 0.2, 0.7))
    t1 = t0 + V((0.6, -0.5, 0.45))
    oslab(k, t0, t1, 0.28, 0.26, 0.22, 0.2, paint, ch=0.06)
    drumy(k, t1.x, t1.y, t1.z, 0.24, 0.5, 'gun', seg=8)
    oslab(k, t1, t1 + V((0.15, -0.5, 0.35)), 0.2, 0.18, 0.14, 0.12, 'gun2', ch=0.04)
    # wrist: torn ring, pistons, cables
    drumy(k, 0.0, 1.4, 0.8, 0.75, 0.5, 'steelDark', seg=10)
    k.cyl(0.0, 1.655, 0.8, 0.55, 0.55, 0.004, 'rust2', seg=10, rot=(-90, 0, 0), ink=False)
    for x in (-0.35, 0.35):
        tube(k, V((x, 1.55, 0.7)), V((x * 1.4, 2.0, 0.3)), 0.1, 'chrome', seg=6, ink=False)
    cable(k, (0.15, 1.6, 0.9), (0.6, 1.95, 0.05), 0.1, 0.06, c='cable', n=3)
    cable(k, (-0.2, 1.6, 0.6), (-0.8, 1.9, 0.04), 0.05, 0.05, c='crimson2', n=3)
    k.stripes(-0.7, 0.3, 0.3, 0.6, -0.857, -1, 5)
    k.col(-1.25, 1.25, -0.95, 1.7, 0, 1.0)
    k.col(-1.1, 1.1, -1.75, -0.95, 0, 1.6)
    k.col(1.1, 1.85, -0.6, 0.6, 0, 1.5)
    return k


def giant_foot(k, paint='olive'):
    """A giant mech foot [4, 3] torn off at the ankle: toe plates, the heel spur, the ankle joint drum, a shin stump
    with its ram, 2.4 m."""
    k.begin()
    slab3(k, 0.0, 0.0, [(0.0, 1.6, 1.15, 0, 0), (0.7, 1.55, 1.1, 0, 0), (1.05, 1.1, 0.9, 0.2, 0)], 'gun2', ch=0.35)
    for x in (-1.0, 0.0, 1.0):
        slab(k, x * 0.95 - 0.35, -0.2, 0.0, 0.85, 0.42, 0.95, 0.38, 0.8, paint, ch=0.12, dx=-0.15)
    slab(k, 1.45, 0.0, 0.0, 0.7, 0.35, 0.6, 0.2, 0.45, 'gun', ch=0.1, dx=0.15)
    drumy(k, 0.25, 0.0, 1.45, 0.62, 1.5, 'steelDark', seg=10)
    oslab(k, (0.25, 0.0, 1.5), (0.55, 0.15, 2.45), 0.55, 0.62, 0.5, 0.55, paint, ch=0.15)
    k.cyl(0.55, 0.15, 2.45, 0.42, 0.42, 0.004, 'rust2', seg=8, ink=False)
    tube(k, V((-0.6, 0.0, 0.95)), V((0.15, 0.1, 2.3)), 0.12, 'chrome', seg=6, ink=False)
    k.stripes(-1.2, -0.2, 0.15, 0.5, -1.152, -1, 5)
    k.col(-1.65, 1.6, -1.15, 1.15, 0, 1.05)
    k.col(-0.4, 1.0, -0.7, 0.7, 1.05, 2.45)
    return k


def giant_leg(k, paint='olive'):
    """A giant mech leg [8, 3] lying on its side: thigh armour, the knee drum, the shin with its rams, the foot."""
    k.begin()
    oslab(k, (-3.9, 0.0, 1.1), (-0.8, 0.1, 1.15), 1.05, 1.0, 0.9, 0.9, paint, ch=0.3)
    k.cyl(-3.905, 0.0, 1.1, 0.7, 0.7, 0.004, 'rust2', seg=8, rot=(0, -90, 0), ink=False)
    drumy(k, -0.4, 0.0, 1.0, 0.95, 1.6, 'gun2', seg=12)
    oslab(k, (0.0, 0.0, 0.85), (2.7, -0.1, 0.8), 0.75, 0.72, 0.6, 0.6, 'gun', ch=0.2)
    slab(k, 1.3, -0.05, 1.35, 1.65, 1.0, 0.55, 0.9, 0.5, paint, ch=0.15)
    tube(k, V((0.1, 0.65, 1.3)), V((2.4, 0.55, 1.05)), 0.14, 'chrome', seg=6, ink=False)
    tube(k, V((0.1, -0.7, 1.2)), V((1.4, -0.65, 0.9)), 0.16, 'steelDark', seg=6)
    slab3(k, 3.2, 0.0, [(0.0, 0.55, 1.1, 0, 0), (1.2, 0.5, 1.05, -0.1, 0), (1.5, 0.3, 0.7, -0.2, 0)], 'gun2', ch=0.2)
    k.col(-3.95, -0.1, -1.05, 1.05, 0, 2.1)
    k.col(-0.1, 3.95, -1.05, 1.05, 0, 1.65)
    return k


def giant_forearm(k, paint='crimson'):
    """A giant forearm [6, 3] lying on its side: the elbow drum, armoured guard, a hydraulic sleeve, wrist stump with
    spilled cables, 1.9 m."""
    k.begin()
    drumy(k, -2.1, 0.0, 0.95, 0.95, 1.7, 'gun2', seg=12)
    k.cyl(-2.1, -0.855, 0.95, 0.5, 0.5, 0.004, 'steelDark', seg=10, rot=(90, 0, 0), ink=False)
    oslab(k, (-1.6, 0.0, 0.85), (2.3, 0.0, 0.75), 0.85, 0.8, 0.7, 0.68, paint, ch=0.22)
    slab(k, 0.4, 0.0, 1.45, 1.75, 1.6, 0.6, 1.5, 0.5, 'bone2', ch=0.15)
    k.stripes(-1.0, 1.4, 0.3, 0.65, -0.86, -1, 8)
    drumx(k, 2.55, 0.0, 0.75, 0.62, 0.5, 'steelDark', seg=10)
    for i, (dy, c) in enumerate(((-0.25, 'cable'), (0.15, 'crimson2'), (0.35, 'hazard'))):
        cable(k, (2.75, dy, 0.85 + 0.1 * i), (2.95, dy * 1.6, 0.03), 0.1, 0.05, c=c, n=3)
    k.col(-2.95, 2.8, -0.9, 0.9, 0, 1.9)
    return k


def giant_rifle(k):
    """A giant broken rifle [10, 3] lying on its side: the stock, receiver with its magazine and sight rail, the
    barrel snapped off and lying askew beyond the shroud (0.6 - 1.6 m: mixed cover)."""
    k.begin()
    k.push(0, 0, 0, 0)
    slab3(k, -4.0, 0.0, [(0.0, 0.7, 0.32, 0, 0), (1.15, 0.9, 0.3, 0.2, 0)], 'gun2', ch=0.1)          # stock
    k.bx(-3.3, 0.6, -0.42, 0.42, 0.0, 1.3, 'gun')                                                     # receiver
    k.bx(-3.25, 0.55, -0.45, 0.45, 0.35, 0.55, 'olive2', ink=False)
    k.bx(-1.9, -0.6, -0.36, 0.36, 1.3, 1.6, 'steelDark')                                              # sight rail
    tbox(k, -0.9, -1.0, 0.32, 0.7, 1.1, 0.62, 'gun2', yaw=-8)                                          # magazine, fallen out
    text(k, 'RT-90', -1.4, -0.453, 0.66, 0.34, 'bone', face='y-', maxw=1.6)
    drumx(k, 2.0, 0.0, 0.62, 0.48, 2.8, 'steelDark', seg=10)                                          # shroud
    for i in range(5):
        k.cyl(0.9 + i * 0.6, -0.482, 0.62, 0.12, 0.12, 0.004, 'gun2', seg=6, rot=(90, 0, 0), ink=False)
    k.pop()
    k.push(4.3, 0.55, 24, 0)                                                                           # the snapped barrel
    drumx(k, 0.0, 0.0, 0.32, 0.3, 2.6, 'gun', seg=10)
    drumx(k, 1.45, 0.0, 0.32, 0.38, 0.3, 'steelDark', seg=10)
    k.cyl(-1.302, 0.0, 0.32, 0.22, 0.22, 0.004, 'rust2', seg=8, rot=(0, -90, 0), ink=False)
    k.pop()
    k.col(-4.0, 0.6, -0.45, 0.45, 0, 1.3)
    k.col(0.6, 3.4, -0.48, 0.48, 0, 1.1)
    k.col(3.2, 5.6, 0.0, 1.35, 0, 0.64)
    return k


def giant_minigun(k):
    """A giant rotary cannon [6, 3] torn off its mount, lying tilted: six barrels in their clamps, the motor housing,
    the ammo chute, 1.0 - 1.8 m."""
    k.begin()
    k.push(0, 0, 0, 0)
    slab3(k, -1.9, 0.0, [(0.0, 0.95, 0.95, 0, 0), (1.8, 0.95, 0.9, 0, 0)], 'olive2', ch=0.3)
    k.stripes(-2.7, -1.1, 0.4, 0.8, -0.952, -1, 6)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        drumx(k, 1.15, math.cos(a) * 0.42, 0.95 + math.sin(a) * 0.42, 0.14, 3.6, 'gun', seg=6)
    for x in (0.0, 1.6, 2.9):
        drumx(k, x, 0.0, 0.95, 0.62, 0.22, 'steelDark', seg=10)
    k.cyl(-2.85, 0.0, 0.95, 0.5, 0.5, 0.004, 'rust2', seg=8, rot=(0, -90, 0), ink=False)
    oslab(k, (-2.2, 0.75, 1.5), (-2.6, 1.4, 0.05), 0.25, 0.12, 0.25, 0.12, 'gun2', ch=0.03)
    k.pop()
    k.col(-2.85, 0.0, -0.95, 0.95, 0, 1.85)
    k.col(0.0, 3.0, -0.62, 0.62, 0, 1.57)
    return k


# ================================================================ dead tech
def crt(k, x, y, z, yaw, s=1.0, cracked=False, c='beige'):
    """An old CRT monitor: case, tapered back, the dead screen (flat) and a bezel line."""
    k.push(x, y, yaw, z, s=s)
    k.bx(-0.25, 0.25, -0.24, 0.0, 0.0, 0.42, c)
    k.hullp([(-0.2, 0.0, 0.05), (0.2, 0.0, 0.05), (-0.2, 0.0, 0.38), (0.2, 0.0, 0.38), (-0.12, 0.3, 0.1), (0.12, 0.3, 0.1), (-0.12, 0.3, 0.32), (0.12, 0.3, 0.32)], 'beige2')
    k.qy(-0.2, 0.2, 0.06, 0.36, -0.243, -1, 'screenD')
    if cracked:
        k.poly([(-0.05, -0.246, 0.2), (0.12, -0.246, 0.34), (0.02, -0.246, 0.18), (0.15, -0.246, 0.09)], 'lensR', (0, -1, 0))
    k.pop()


def monitor_pile(k, seed):
    """A pile of dead CRT monitors and keyboards [3, 3] round an old server case, about 2 m tall."""
    k.begin()
    rnd = random.Random(seed)
    heap(k, 0.0, 0.0, 1.25, 1.2, 0.7, seed, n=8, top=2, fn=lambda f: 'dirt2' if f.normal.z < 0.5 else 'beige2')
    k.bx(-0.3, 0.3, -0.35, 0.35, 0.3, 1.5, 'gun2')
    k.qy(-0.25, 0.25, 0.4, 1.4, -0.353, -1, 'steelDark')
    spots = [(-0.9, -0.7, 0.0, 0), (0.0, -0.95, 0.0, 10), (0.85, -0.6, 0.0, -20), (-1.0, 0.4, 0.0, 70), (1.0, 0.5, 0.0, -80),
             (-0.5, -0.4, 0.55, 15), (0.45, -0.35, 0.55, -10), (0.5, 0.4, 0.6, -95),
             (0.0, -0.45, 1.5, 0)]
    for i, (x, y, z, yaw) in enumerate(spots):
        crt(k, x, y, z, yaw + rnd.uniform(-8, 8), s=rnd.uniform(0.95, 1.1), cracked=i % 4 == 1, c='beige' if i % 3 else 'carW')
    for i in range(3):   # keyboards
        tbox(k, rnd.uniform(-1.1, 1.1), rnd.uniform(-1.2, -1.05) if i < 2 else 1.15, 0.05, 0.6, 0.2, 0.05, 'beige2', yaw=rnd.uniform(-30, 30), roll=rnd.uniform(-10, 10))
    cable(k, (-0.3, -0.3, 1.2), (-1.3, -0.5, 0.05), 0.2, 0.03, c='cable', n=3)
    k.col(-1.3, 1.3, -1.3, 1.3, 0, 1.0)
    k.col(-0.55, 0.55, -0.6, 0.6, 1.0, 1.95)
    return k


def server_racks(k, seed):
    """Toppled server racks [4, 2]: two lying on their backs (servers half pulled out, a sprung door), one leaning on
    them, dead LED strips, cable spill; 0.7 - 2.1 m."""
    k.begin()
    rnd = random.Random(seed)
    for i, x in enumerate((-0.95, 0.55)):
        k.push(x, -0.05, rnd.uniform(-6, 6), 0)
        k.bx(-0.33, 0.33, -0.95, 0.95, 0.0, 0.62, 'gun2')
        k.qz(-0.29, 0.29, -0.92, 0.92, 0.623, 1, 'steelDark')
        for j in range(6):
            y0 = -0.85 + j * 0.29
            out = rnd.uniform(0.0, 0.25) if j % 2 else 0.0
            k.bx(-0.27, 0.27, y0, y0 + 0.24, 0.5, 0.64 + out, 'gun' if j % 3 else 'steel2')
            k.qx(y0 + 0.02, y0 + 0.08, 0.56, 0.6 + out, 0.273, 1, 'pcb')
        k.pop()
    k.push(0.0, 0.62, 0, 0)       # the third rack leaning on the others
    tbox(k, 0.0, 0.0, 1.0, 0.62, 0.6, 2.0, 'gun2', roll=28)
    k.pop()
    plate(k, (1.0, -0.6, 0.02), (1.9, -0.2, 0.02), 0.6, 0.03, 'steel2')      # the sprung door
    cable(k, (0.2, 0.2, 0.6), (1.5, 0.75, 0.03), 0.1, 0.04, c='hazard', n=3)
    cable(k, (-0.6, 0.6, 0.5), (-1.7, 0.85, 0.03), 0.1, 0.04, c='cable', n=3)
    k.col(-1.32, 0.92, -1.0, 0.95, 0, 0.75)
    k.col(-0.6, 0.65, 0.3, 0.95, 0.75, 1.9)
    return k


def cable_drum(k, small=False, seed=1):
    """A wooden cable drum: big [2, 2] lying on its side with copper cable wound, chocks; small [1, 1] standing."""
    k.begin()
    rnd = random.Random(seed)
    if small:
        for z in (0.0, 0.78):
            k.cyl(0, 0, z, 0.46, 0.46, 0.08, 'wood', seg=8)
        k.cyl(0, 0, 0.08, 0.3, 0.3, 0.7, 'cable' if seed % 2 else 'copper', seg=8)
        vdisc(k, 0, 0, 0.864, 0.1, 'wood2', axis='z', s=1)
        k.col(-0.46, 0.46, -0.46, 0.46, 0, 0.86)
        return k
    R, W = 0.82, 1.15
    for s in (-1, 1):
        y = s * (W / 2 - 0.05)
        k.cyl(0, y - 0.05, R, R, R, 0.1, 'wood', seg=12, rot=(-90, 0, 0))
        vdisc(k, 0, y + s * 0.054, R, 0.2, 'wood2', s=s)
    k.cyl(0, -W / 2 + 0.1, R, 0.6, 0.6, W - 0.2, 'copper' if seed % 2 else 'cable', seg=10, rot=(-90, 0, 0))
    for x in (-0.75, 0.75):
        k.bx(x - 0.12, x + 0.12, -0.5, 0.5, 0, 0.15, 'wood2')
    cable(k, (0.0, 0.0, 0.25), (1.0, -0.3, 0.03), 0.05, 0.05, c='copper' if seed % 2 else 'cable', n=3)
    k.col(-R, R, -W / 2, W / 2, 0, 2 * R)
    return k


def ewaste(k, seed):
    """A steel stillage of e-waste [1, 1]: mesh-sided cage (bars) full of circuit boards and dead phones."""
    k.begin()
    rnd = random.Random(seed)
    k.bx(-0.48, 0.48, -0.48, 0.48, 0, 0.12, 'gun2')
    for (x, y) in ((-0.44, -0.44), (0.44, -0.44), (0.44, 0.44), (-0.44, 0.44)):
        k.bx(x - 0.035, x + 0.035, y - 0.035, y + 0.035, 0.12, 0.92, 'hazard')
    k.bx(-0.4, 0.4, -0.4, 0.4, 0.124, 0.8, 'steelDark')
    for f in range(4):
        k.push(0, 0, f * 90)
        for i in range(5):
            x = -0.32 + i * 0.16
            k.qy(x - 0.012, x + 0.012, 0.14, 0.9, -0.423, -1, 'steel2')
        k.qy(-0.4, 0.4, 0.86, 0.89, -0.427, -1, 'steel2')
        k.pop()
    for i in range(6):
        tbox(k, rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), 0.84 + i * 0.012, rnd.uniform(0.25, 0.4), rnd.uniform(0.18, 0.3), 0.02, rnd.choice(('pcb', 'pcb', 'gun', 'beige')), yaw=rnd.uniform(0, 180), roll=rnd.uniform(-8, 8), ink=False)
    k.col(-0.48, 0.48, -0.48, 0.48, 0, 0.92)
    return k


def tyre_stack(k, seed):
    """Four old tyres stacked a little askew [1, 1], one leaning against them."""
    k.begin()
    rnd = random.Random(seed)
    z = 0.0
    for i in range(4):
        tyre(k, rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), z + 0.125, r=0.38, w=0.25, axis='z', hub=(i == 3))
        z += 0.254
    k.col(-0.42, 0.42, -0.42, 0.42, 0, z)
    return k


def skip(k, seed):
    """A roll-off skip [4, 2] full of scrap: sloped ends, top rail, lifting lugs, the yard's stencil."""
    k.begin()
    rnd = random.Random(seed)
    c = ('carY', 'carG', 'carB')[seed % 3]
    pts = []
    for sy in (-1, 1):
        pts += [(-1.55, sy * 0.85, 0.0), (1.55, sy * 0.85, 0.0), (-1.9, sy * 0.92, 1.45), (1.9, sy * 0.92, 1.45)]
    k.hullp(pts, lambda f: 'rust2' if f.normal.z < -0.5 else c)
    k.bx(-1.94, 1.94, -0.96, 0.96, 1.45, 1.55, 'steelDark')
    text(k, 'RUSTMOOR', 0.0, -0.94, 0.55, 0.36, 'ink', face='y-', maxw=2.6)
    for x in (-1.2, 1.2):
        k.bx(x - 0.1, x + 0.1, -0.99, -0.92, 1.0, 1.4, 'steelDark')
    for i in range(6):   # scrap poking out of the top
        x, y = rnd.uniform(-1.4, 1.4), rnd.uniform(-0.5, 0.5)
        if i % 3 == 0:
            ibeam(k, (x, y, 1.2), (x + rnd.uniform(-0.6, 0.6), y + rnd.uniform(-0.2, 0.2), 2.0), h=0.24, w=0.16, c='rust')
        elif i % 3 == 1:
            plate(k, (x, y, 1.3), (x + 0.5, y, 1.75), 0.6, 0.04, rnd.choice(CARS + ('steel2',)), up=(0.3, -0.5, 1))
        else:
            heap(k, x, y, 0.5, 0.4, 0.5, seed + i, n=6, top=1, z0=1.24 + 0.01 * i)
    k.col(-1.92, 1.92, -0.94, 0.94, 0, 1.55)
    return k


def barrier(k, seed):
    """A concrete jersey barrier module (1 m along X, 0.8 m), its yellow band, a chipped corner."""
    k.begin()
    pts = []
    for x in (-0.5, 0.5):
        pts += [(x, -0.3, 0.0), (x, 0.3, 0.0), (x, -0.22, 0.25), (x, 0.22, 0.25), (x, -0.1, 0.8), (x, 0.1, 0.8)]
    k.hullp(pts, lambda f: 'conc' if f.normal.z > 0.6 else 'conc2')
    if seed % 2:
        for s in (-1, 1):
            k.poly([(-0.5, s * 0.2, 0.33), (0.5, s * 0.2, 0.33), (0.5, s * 0.167, 0.48), (-0.5, s * 0.167, 0.48)], 'hazard', (0, s, 0.2))
    k.col(-0.5, 0.5, -0.3, 0.3, 0, 0.8)
    return k


def oil(k, seed):
    """An oil stain and a puddle on the ground [2, 2] (no collision)."""
    k.begin()
    rnd = random.Random(seed)
    k.disc(0.0, 0.0, Z['oil'], 0.95, 'dirt2', n=12, rnd=rnd, jag=0.25)
    k.disc(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), Z['oil'] + 0.004, 0.45, 'lensD', n=9, rnd=rnd, jag=0.3)
    return k
