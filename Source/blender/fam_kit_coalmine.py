"""INKBOLT asset family: kit-coalmine (Deep Coal Mine: a big room-and-pillar coal mine, timbered drifts, rail haulage).

Conventions (see src/data/themes.js and kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * Wall modules ('#') face Blender -Y (game +Z); the theme uses wall.facing = 'open', so the engine turns each
    straight module toward its open side and corners / notches get the all-round Rock_Corner lumps.
  * Rock faces are open lofts that share one edge profile (EDGE) at both ends, so a run of modules reads as one
    continuous faceted face with horizontal strata; variants change only the middle stations and the colours
    (coal seams, lamps on brackets, prop timbers, signs, overlooks into the big dark mine beyond).
  * Walls reach WALL_H (9.4 m), just above the ceiling (theme env.ceiling.height 9.0) so the roof always meets them;
    the gate frame's plank bulkhead fills from the cap timber to WALL_H (nothing shows above the gates).
  * Trail pieces (TrailWall) carry a timber set, half the lagging roof (3.86 m) and a narrow-gauge track: the two
    sides of a trail meet in the middle, so the drift between zones is a closed, low timbered tunnel.
  * Light pools are flat warm discs on the floor; each kind sits at its own height (POOL_Z) so pools of different
    pieces may overlap without z-fighting. Same-kind pools never overlap (lamp spacing in the maps / chooser).
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, rz, srt, rock_pts, clamp_pts, shutter_hull

FAM = 'kit-coalmine'
PFX = 'KIT_COALMINE_'
ib_lib.GLB[FAM] = 'fps-kit-coalmine.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
CEIL = 9.0
WALL_H = 9.4
ROOF = 3.86         # trail lagging top (the drift roof seen from below at 3.8)

ib_lib.PALETTES[FAM] = BASE + [
    ('rock', '#54493F'), ('rockB', '#463D36'), ('rock2', '#362F2A'), ('rock3', '#7A6A57'),
    ('rockBack', '#2E2724'), ('coal', '#25242B'), ('coal2', '#383744'), ('glint', '#9AA6C8'),
    ('timber', '#A8743F'), ('timber2', '#87592F'), ('timberEnd', '#D6A66C'), ('plank', '#B98653'),
    ('plank2', '#94653A'), ('steel', '#959FAA'), ('steel2', '#6E7783'), ('steelDark', '#434954'),
    ('rust', '#A65A32'), ('lamp', '#FFD66B'), ('lampHot', '#FFF6CF'), ('pool', '#7C6450'),
    ('pool2', '#9C7F5C'), ('hood', '#2F4A3E'), ('dirt', '#5B4F46'), ('dust', '#3B3430'),
    ('hazard', '#F2C230'), ('rope', '#C9B28A'), ('sack', '#B39A70'), ('sack2', '#958058'),
    ('cart', '#B4503A'), ('cart2', '#8C3C2D'), ('water', '#2C3B48'), ('waterG', '#7C9AB2'),
    ('mach', '#E8B530'), ('mach2', '#BF8D22'), ('rubber', '#2A2830'), ('cable', '#1F1D1C'),
    ('tin', '#7E868F'), ('ceilRock', '#3A322D'), ('ceilRock2', '#2C2522'), ('far', '#3B3330'),
    ('far2', '#2E2826'), ('farLit', '#6E5640'), ('board', '#2E3B33'), ('chalk', '#E9E4D6'),
    ('pit', '#0E0C0C'), ('canvas', '#7D8462'), ('drum', '#3F6A8C'), ('drum2', '#335774'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64

# decal heights (m above the floor): one level per kind, >= 4 mm apart (engine floor at 0.004)
Z_BALLAST = 0.010
POOL_Z = {'S': 0.016, 'N': 0.024, 'E': 0.032, 'W': 0.040, 'post': 0.048, 'work': 0.056, 'drill': 0.080,
          'shack': 0.084, 'set': 0.088, 'head': 0.1, 'hopper': 0.096, 'hatch': 0.104}
Z_PUDDLE = 0.064
Z_DUST = 0.076
SLEEPER_TOP = 0.072
RAIL_TOP = 0.15

# ================================================================ rock faces
# profile levels (z) shared by every module: strata bands between them; the coal seam is the band 1.5-3.0
LV = [0.0, 0.6, 1.5, 3.0, 4.2, 5.6, 7.0, 8.3, WALL_H]
# edge profile (y at each level, then over the top and down the back)
EDGE_Y = [-0.44, -0.5, -0.4, -0.47, -0.35, -0.43, -0.3, -0.37, -0.22]


def prof(ys, back=0.5, lv=LV):
    return [(y, z) for y, z in zip(ys, lv)] + [(back, WALL_H), (back, 0.0)]


EDGE = prof(EDGE_Y)


def band(z):
    for i in range(len(LV) - 1):
        if z < LV[i + 1]:
            return i
    return len(LV) - 2


def rock_fn(seam=False, seam2=False):
    """Colour by face normal and stratum: lit ledges, dark base, alternating strata, coal seams."""
    def fn(f):
        n, c = f.normal, f.calc_center_median()
        b = band(c.z)
        if n.y > 0.5 or c.z > WALL_H - 0.05:
            return 'rockBack'
        if seam and b == 2:
            return 'coal2' if n.z > 0.3 else 'coal'
        if seam2 and b == 5:
            return 'coal'
        if n.z > 0.32:
            return 'rock3'
        if b == 0:
            return 'rock2'
        return 'rock' if b % 2 else 'rockB'
    return fn


def mid_profile(rnd, amp=0.12, seam=False, depth=0.12):
    """A middle station: the edge profile pushed in / out per level (bulges, ledges); the levels wander a little
    so the strata read as rough bands; seams stand proud."""
    ys, lv = [], [LV[0]]
    for i, y in enumerate(EDGE_Y):
        d = rnd.uniform(-amp, amp)
        if seam and i in (2, 3):
            d = -depth - rnd.uniform(0, 0.012)
        ys.append(max(-0.72, min(-0.1, y + d)))
    for i in range(1, len(LV) - 1):
        lv.append(LV[i] + (0 if seam and i in (2, 3) else rnd.uniform(-0.22, 0.22)))
    lv.append(LV[-1])
    return prof(ys, lv=lv)


def rock_face(k, seed, seam=False, seam2=False, amp=0.12, depth=0.12):
    rnd = random.Random(seed)
    a, b = mid_profile(rnd, amp, seam, depth), mid_profile(rnd, amp, seam, depth)
    k.loft([(-0.5, EDGE), (rnd.uniform(-0.22, -0.12), a), (rnd.uniform(0.12, 0.22), b), (0.5, EDGE)], rock_fn(seam, seam2), baffle='rock2')
    if seam:   # coal glints on the seam
        for i in range(3):
            x = -0.35 + i * 0.32 + rnd.uniform(-0.05, 0.05)
            z = 2.0 + rnd.uniform(-0.2, 0.6)
            k.poly([(x, -0.72, z), (x + 0.07, -0.72, z + 0.02), (x + 0.03, -0.72, z + 0.16)], 'glint', (0, -1, 0))


def cable_run(k, z=3.6, y=-0.62):
    """Power cable sagging between hooks along the wall (runs on from module to module)."""
    k.beam((-0.5, y, z), (0.0, y, z - 0.09), 0.035, 'cable', ink=False)
    k.beam((0.0, y + 0.007, z - 0.09), (0.5, y + 0.007, z), 0.035, 'cable', ink=False)
    k.bx(-0.02, 0.02, y + 0.03, y + 0.22, z - 0.12, z - 0.07, 'steelDark', ink=False)


def pool(k, x, y, z, r, seed, sx=1.0, sy=1.0):
    rnd = random.Random(seed)
    k.disc(x, y, z, r, 'pool', n=14, rnd=rnd, jag=0.06, sx=sx, sy=sy)
    k.disc(x, y, z + 0.004, r * 0.55, 'pool2', n=10, rnd=rnd, jag=0.08, sx=sx, sy=sy)


def lantern(k, x, y, z, s=1.0):
    """Miner's lantern hanging at (x, y) with its bail top at z: hood, glass, base."""
    k.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, z - 0.12 * s, z, 'steelDark', ink=False)
    k.cyl(x, y, z - 0.2 * s, 0.11 * s, 0.05 * s, 0.08 * s, 'hood', seg=6)
    k.cyl(x, y, z - 0.42 * s, 0.075 * s, 0.075 * s, 0.22 * s, 'lamp', seg=6)
    k.cyl(x, y, z - 0.47 * s, 0.1 * s, 0.1 * s, 0.05 * s, 'hood', seg=6, ink=False)


def wall_module(k, kind, seed):
    k.begin()
    if kind == 'Seam':
        # the two seam modules stand their coal out by clearly different depths, so where they meet the faces
        # either side of the joint are never near-coplanar
        rock_face(k, seed, seam=True, seam2=(seed % 2 == 0), depth=0.1 if seed % 2 else 0.19)
    else:
        rock_face(k, seed, amp=0.2 if kind in ('A', 'B', 'C') else 0.12)
    cable_run(k)
    if kind.startswith('Lamp'):
        # timber bracket wedged into the rock, lantern hanging out over the floor, warm pool in front
        k.bx(-0.07, 0.07, -0.95, -0.2, 3.25, 3.39, 'timber')
        k.beam((0.0, -0.3, 2.65), (0.0, -0.82, 3.26), 0.09, 'timber2')
        lantern(k, 0.0, -0.88, 3.25)
        pool(k, 0.0, -1.5, POOL_Z[kind[4:]], 2.1, seed, sx=1.15)
    elif kind == 'Prop':
        # roof prop against the wall: post, cap wedged into the rock, wedges
        k.bx(-0.13, 0.13, -0.8, -0.54, 0, 4.0, 'timber')
        k.bx(-0.2, 0.2, -0.86, -0.2, 4.0, 4.28, 'timber2')
        k.bx(-0.16, 0.16, -0.74, -0.58, 4.28, 4.4, 'timberEnd', ink=False)
        k.qy(-0.13, 0.13, 3.95, 4.0, -0.803, -1, 'timberEnd')
        k.bx(-0.18, 0.18, -0.84, -0.5, 0, 0.12, 'timber2', ink=False)
    elif kind == 'Sign':
        # painted level board on two pins: amber diamond, arrow, number blocks
        k.bx(-0.42, 0.42, -0.62, -0.56, 2.0, 2.8, 'plank')
        k.qy(-0.39, 0.39, 2.03, 2.77, -0.623, -1, 'board')
        k.poly([(-0.25, -0.626, 2.4), (-0.12, -0.626, 2.6), (0.01, -0.626, 2.4), (-0.12, -0.626, 2.2)], 'hazard', (0, -1, 0))
        k.poly([(0.08, -0.626, 2.33), (0.24, -0.626, 2.33), (0.24, -0.626, 2.27), (0.33, -0.626, 2.4),
                (0.24, -0.626, 2.53), (0.24, -0.626, 2.47), (0.08, -0.626, 2.47)], 'chalk', (0, -1, 0))
        k.qy(0.1, 0.32, 2.6, 2.66, -0.626, -1, 'chalk')
        for x in (-0.36, 0.36):
            k.bx(x - 0.02, x + 0.02, -0.66, -0.3, 2.65, 2.69, 'steelDark', ink=False)
    elif kind == 'Open':
        pass
    return k


def overlook(k, seed):
    """Opening onto the big dark mine beyond (backdrop): only the rock lintel above 4.2 m, a guard rail below."""
    k.begin()
    rnd = random.Random(seed)
    lv = LV[4:]
    ys = EDGE_Y[4:]
    e = [(y, z) for y, z in zip(ys, lv)] + [(0.5, WALL_H), (0.5, 4.2)]
    mids = []
    for _ in range(2):
        mids.append([(max(-0.62, y + rnd.uniform(-0.1, 0.1)) if z > 4.25 else y, z) for (y, z) in e[:-2]] + e[-2:])
    k.loft([(-0.5, e), (-0.17, mids[0]), (0.17, mids[1]), (0.5, e)], rock_fn(), baffle='rock2')
    k.bx(-0.5, 0.5, -0.33, 0.48, 3.98, 4.26, 'rock2')                 # lintel underside
    cable_run(k, z=4.6, y=-0.5)
    # timber barrier at the cell's open face (the cell's wall box stops the player there: no invisible gap before it)
    for x in (-0.26, 0.26):                                            # posts, two rails
        k.bx(x - 0.07, x + 0.07, -0.44, -0.3, 0, 1.15, 'timber')
    k.bx(-0.5, 0.5, -0.49, -0.43, 0.95, 1.1, 'timber2')
    k.bx(-0.5, 0.5, -0.48, -0.44, 0.45, 0.58, 'timber2')
    k.qy(-0.5, 0.5, 0.75, 0.81, -0.495, -1, 'hazard')
    k.bx(-0.5, 0.5, -0.1, 0.5, -0.4, 0.06, 'rock2', ink=False)        # ledge lip
    return k


def corner(k, seed):
    """Corners, notches and free-standing columns: stacked faceted lumps filling the cell up to the roof."""
    k.begin()
    rnd = random.Random(seed)
    fn = rock_fn()
    hb = rnd.uniform(3.2, 4.2)
    k.hullp(clamp_pts(rock_pts(rnd, (0, 0), 0.56, 0.56, hb, n=8, top=2), 0.5), fn)
    hm = rnd.uniform(6.6, 7.4)
    k.hullp(clamp_pts(rock_pts(rnd, (0.05, -0.05), 0.52, 0.52, hm - hb + 0.6, z0=hb - 0.6, n=7, top=2), 0.5), fn)
    pts = rock_pts(rnd, (-0.04, 0.04), 0.54, 0.54, WALL_H - hm + 0.8, z0=hm - 0.8, n=7, top=0)
    pts += [(0.45, 0.45, WALL_H), (-0.45, 0.45, WALL_H), (0.45, -0.45, WALL_H), (-0.45, -0.45, WALL_H)]
    k.hullp(clamp_pts(pts, 0.5), fn)
    return k


# ================================================================ ceiling, gate, trail, hatch
def ceil_rock(k):
    """12 x 12 m roof patch at the ceiling plane: hanging rock slabs, roof bolts, a cable tray run."""
    k.begin()
    rnd = random.Random(77)
    fn = lambda f: 'ceilRock2' if f.normal.z > -0.5 else ('ceilRock' if f.calc_center_median().z > -0.45 else 'rock2')
    for (x, y, rx, ry, h) in ((-3.5, -2.5, 1.9, 1.4, 0.7), (2.8, 3.1, 1.6, 2.1, 0.9), (3.6, -3.8, 1.3, 1.1, 0.5),
                              (-3.0, 3.6, 1.2, 1.5, 0.55), (0.2, 0.0, 1.0, 0.8, 0.4)):
        pts = rock_pts(rnd, (x, y), rx, ry, h, n=6, top=2)
        k.hullp([(px, py, 0.05 - pz) for (px, py, pz) in pts], fn)
    for (x, y) in ((-1.0, -4.5), (1.4, -1.2), (-4.6, 0.8), (4.8, 0.6), (-0.6, 4.4), (1.8, 5.3), (-5.2, -5.0)):
        k.qz(x - 0.09, x + 0.09, y - 0.09, y + 0.09, -0.006, -1, 'steel2')
    k.bx(-5.9, 5.9, -0.1, 0.1, -0.33, -0.27, 'steelDark', ink=False)    # cable tray along X
    for x in (-4.5, -1.5, 1.5, 4.5):
        k.bx(x - 0.02, x + 0.02, -0.02, 0.02, -0.27, 0.0, 'steelDark', ink=False)
    return k


def bulkhead(k, x0, x1, z0, z1, t=0.1, dark=False):
    """Plank bulkhead (double-faced) closing everything above a timber set up to the roof."""
    k.bx(x0, x1, -t, t, z0, z1, 'plank2' if dark else 'plank')
    n = int((x1 - x0) / 0.32)
    for s in (-1, 1):
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            k.qy(x - 0.012, x + 0.012, z0 + 0.02, z1 - 0.02, s * (t + 0.003), s, 'plank2' if not dark else 'timber2')


def timber_set(k, x_half, y_half=0.17, cap_z=3.9, post=0.15):
    """Timber set: two posts, cap with knee braces."""
    for s in (-1, 1):
        x0, x1 = srt(s * (x_half - post), s * (x_half + post))
        k.bx(x0, x1, -post + 0.01, post - 0.01, 0, cap_z, 'timber')
        k.beam((s * (x_half - post), 0, cap_z - 0.9), (s * (x_half - post - 0.75), 0, cap_z - 0.02), 0.13, 'timber2')
    k.bx(-x_half - 0.5, x_half + 0.5, -y_half, y_half, cap_z, cap_z + 0.34, 'timber2')


def gate_frame(k):
    """Mine portal for the 3 m zone gates: big timber posts and cap, knee braces, plank bulkhead to the roof,
    a teal-edged level board and a lantern each side."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.05)
        k.bx(x0, x1, -0.6, 0.6, 0, 3.3, 'timber')
        for f in (-1, 1):
            y0, y1 = srt(f * 0.6, f * 0.63)
            k.bx(x0 + 0.04, x1 - 0.04, y0, y1, 0.3, 0.36, 'steelDark', ink=False)   # steel band
            k.bx(x0 + 0.04, x1 - 0.04, y0, y1, 2.6, 2.66, 'steelDark', ink=False)
        k.beam((s * 1.55, -0.45, 2.45), (s * 0.9, -0.45, 3.32), 0.16, 'timber2')
        k.beam((s * 1.55, 0.45, 2.45), (s * 0.9, 0.45, 3.32), 0.16, 'timber2')
    k.bx(-2.6, 2.6, -0.62, 0.62, 3.3, 3.85, 'timber2')
    bulkhead(k, -2.4, 2.4, 3.85, WALL_H + 0.03, t=0.16)
    for f in (-1, 1):
        y0, y1 = srt(f * 0.62, f * 0.66)
        k.bx(-0.8, 0.8, y0, y1, 4.3, 4.95, 'board')
        yb = f * 0.663
        k.qy(-0.74, 0.74, 4.36, 4.42, yb, f, 'teal')
        k.qy(-0.74, 0.74, 4.83, 4.89, yb, f, 'teal')
        for i, w in enumerate((0.16, 0.1, 0.22)):
            x = -0.5 + i * 0.36
            k.qy(x, x + w, 4.5, 4.75, yb, f, 'chalk')
        for s in (-1, 1):
            lantern(k, s * 2.3, f * 0.86, 3.2)
            k.bx(s * 2.3 - 0.03, s * 2.3 + 0.03, *srt(f * 0.62, f * 0.9), 3.17, 3.22, 'steelDark', ink=False)
    return k


def gate_shutter(k):
    """Heavy plank barricade: vertical planks, two steel straps, a hazard kick board."""
    k.begin()
    Hs = 3.05
    for i in range(8):
        x0 = -1.5 + i * 0.375
        k.bx(x0 + 0.004, x0 + 0.371, -0.06, 0.06, 0.4, Hs, 'plank' if i % 2 else 'plank2', ink=False)
    for z in (1.0, 2.4):
        k.bx(-1.5, 1.5, -0.08, 0.08, z, z + 0.14, 'steelDark', ink=False)
    for f in (-1, 1):
        for x in (-1.2, -0.4, 0.4, 1.2):
            for z in (1.07, 2.47):
                k.qy(x - 0.03, x + 0.03, z - 0.03, z + 0.03, f * 0.083, f, 'steel')
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.4, 'ink' if j % 2 else 'hazard', ink=False)
    return k


def track(k, x0, x1, y=0.0, gauge=0.6, sleepers=None, ballast=True, sl=1.0):
    """Narrow-gauge track along local X from x0 to x1 centred on y."""
    if ballast:
        k.qz(x0, x1, y - 0.5 * sl, y + 0.5 * sl, Z_BALLAST, 1, 'dust')
    for xs in (sleepers if sleepers is not None else [x0 + (x1 - x0) * (i + 0.5) / max(1, round((x1 - x0) * 2)) for i in range(max(1, round((x1 - x0) * 2)))]):
        k.bx(xs - 0.08, xs + 0.08, y - 0.46 * sl, y + 0.46 * sl, 0, SLEEPER_TOP, 'timber2', ink=False)
    for s in (-1, 1):
        k.bx(x0, x1, y + s * gauge / 2 - 0.02, y + s * gauge / 2 + 0.02, SLEEPER_TOP, RAIL_TOP - 0.025, 'steelDark', ink=False)
        k.bx(x0, x1, y + s * gauge / 2 - 0.036, y + s * gauge / 2 + 0.036, RAIL_TOP - 0.025, RAIL_TOP, 'steel', ink=False)


def trail_wall(k):
    """Drift wall (1 m along Blender Y, corridor to +X): rock face, a timber set (post + half cap), half of the
    lagging roof at ROOF, a narrow-gauge track by the wall, a cable. The back (-X) is plain rock too (seen in the
    hatch room)."""
    k.begin(90)   # author as a wall module facing -Y (the corridor); the turn puts the corridor at +X
    T = 0.25
    ys = [-0.27, -0.31, -0.25, -0.3, -0.24, -0.28, -0.22, -0.26, -0.2]
    def tp(ysx):
        return [(y, z) for y, z in zip(ysx, LV)] + [(0.24, WALL_H), (0.27, 5.0), (0.25, 0.0)]
    rnd = random.Random(5)
    mid = [max(-0.36, y + rnd.uniform(-0.05, 0.03)) for y in ys]
    k.loft([(-0.5, tp(ys)), (0.0, tp(mid)), (0.5, tp(ys))], rock_fn(), baffle='rock2')
    # timber set: post, half cap reaching the middle of the drift, knee brace
    y_mid = -2.25 + 0.003
    k.bx(-0.1, 0.1, -0.42, -0.24, 0, ROOF - 0.32, 'timber')
    k.bx(-0.12, 0.12, y_mid, -0.2, ROOF - 0.32, ROOF - 0.06, 'timber2')
    k.beam((0, -0.42, ROOF - 1.1), (0, -0.95, ROOF - 0.33), 0.1, 'timber2')
    # lagging boards across the top (run along the drift)
    for i in range(4):
        x0 = -0.5 + i * 0.25
        k.bx(x0 + 0.006, x0 + 0.244, y_mid, -0.2, ROOF - 0.06, ROOF, 'plank' if i % 2 else 'plank2', ink=False)
    # track by the wall (two sleepers per metre), cable
    k.push(0, -0.82, 0)
    track(k, -0.5, 0.5, 0.0, gauge=0.5, sleepers=[-0.25, 0.25], sl=0.9)
    k.pop()
    cable_run(k, z=3.1, y=-0.38)
    return k


def hatch(k):
    """Exit: the lift cage. Landing at the pad, the cage under a shaft that rises to the roof (the drift's lagging
    leaves a 1.5 m slot over the room centre: the shaft lining and a lagging patch close it)."""
    k.begin()
    # landing plate with hazard edge
    k.bx(-1.2, 1.2, -1.25, -0.62, 0, 0.05, 'steel2')
    k.qz(-1.16, 1.16, -0.7, -0.64, 0.053, 1, 'hazard')
    for i in range(6):
        x = -1.0 + i * 0.4
        k.poly([(x, -0.7, 0.056), (x + 0.15, -0.7, 0.056), (x + 0.3, -0.64, 0.056), (x + 0.15, -0.64, 0.056)], 'ink', (0, 0, 1))
    for i in range(3):
        y = -1.22 + i * 0.15
        k.poly([(-0.4, y, 0.053), (0, y + 0.12, 0.053), (0.4, y, 0.053), (0.4, y + 0.06, 0.053), (0, y + 0.18, 0.053), (-0.4, y + 0.06, 0.053)], 'teal', (0, 0, 1))
    # cage: floor, corner posts, bars, roof, open front
    C0, C1, W = -0.62, 1.7, 0.72
    k.bx(-W, W, C0, C1, 0, 0.12, 'steelDark')
    for x in (-W, W):
        for y in (C0, C1):
            k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.12, 2.6, 'steel')
    for s in (-1, 1):
        for i in range(1, 7):
            y = C0 + (C1 - C0) * i / 7
            k.bx(s * W - 0.02, s * W + 0.02, y - 0.02, y + 0.02, 0.12, 2.6, 'steel2', ink=False)
        k.bx(s * W - 0.04, s * W + 0.04, C0, C1, 1.05, 1.13, 'steel', ink=False)
    for i in range(1, 6):
        x = -W + 2 * W * i / 6
        k.bx(x - 0.02, x + 0.02, C1 - 0.02, C1 + 0.02, 0.12, 2.6, 'steel2', ink=False)
    k.bx(-W - 0.06, W + 0.06, C0 - 0.06, C1 + 0.06, 2.6, 2.75, 'cart')
    k.bx(-0.15, 0.15, 0.4, 0.7, 2.75, 3.1, 'steelDark')                  # hanger
    lantern(k, 0.0, C0 + 0.15, 2.6, 0.8)
    pool(k, 0.0, 0.5, POOL_Z['hatch'], 1.0, 9)
    # folded scissor gate at the door's side
    for i in range(4):
        x = -W + 0.05 + i * 0.06
        k.beam((x, C0 - 0.1, 0.2), (x + 0.04, C0 - 0.1, 2.3), 0.025, 'steelDark', ink=False)
    # ropes up the shaft to the sheave
    for x in (-0.12, 0.12):
        k.bx(x - 0.02, x + 0.02, 0.53, 0.57, 3.1, 8.6, 'cable', ink=False)
    k.cyl(0, 0.55, 8.75, 0.5, 0.5, 0.12, 'cart2', seg=12, rot=(0, 90, 0))
    k.bx(-0.06, 0.06, 0.48, 0.62, 8.2, 9.3, 'steelDark')
    # shaft lining over the slot (|x| < 0.75 from the trail end to the back wall) and lagging to close the slot
    for s in (-1, 1):
        x0, x1 = srt(s * 0.77, s * 0.95)
        k.bx(x0, x1, -1.55, 2.72, ROOF + 0.04, WALL_H - 0.04, 'plank2')
        for z in (5.0, 6.6, 8.2):
            k.bx(*srt(s * 0.72, s * 0.77), -1.5, 2.7, z, z + 0.22, 'timber', ink=False)
    k.bx(-0.9, 0.9, -1.53, -0.97, ROOF + 0.05, WALL_H - 0.05, 'plank2')        # front of the shaft (over the drift end)
    # signal bell board on the west wall
    k.bx(-2.74, -2.68, 0.6, 1.4, 1.3, 2.1, 'board')
    k.qx(0.66, 1.34, 1.36, 1.42, -2.677, 1, 'hazard')
    k.cyl(-2.62, 1.0, 1.65, 0.1, 0.14, 0.14, 'mach', seg=8, rot=(0, 90, 0))
    k.beam((-2.6, 1.0, 1.6), (-2.6, 1.0, 0.9), 0.02, 'rope', ink=False)
    return k


def stand(k):
    k.begin()
    crate_body(k, 0.45, 0.4, 0.92, 'Powder')
    return k


# ================================================================ cell props
def crate_body(k, hx, hy, h, kind):
    k.bx(-hx, hx, -hy, hy, 0, h, 'plank')
    for f in (-1, 1):
        y = f * (hy + 0.003)
        for z in (h * 0.33, h * 0.66):
            k.qy(-hx + 0.02, hx - 0.02, z - 0.01, z + 0.01, y, f, 'plank2')
        k.qy(-hx + 0.02, -hx + 0.08, 0.02, h - 0.02, y + f * 0.003, f, 'timber2')
        k.qy(hx - 0.08, hx - 0.02, 0.02, h - 0.02, y + f * 0.003, f, 'timber2')
    for f in (-1, 1):
        x = f * (hx + 0.003)
        k.qx(-hy + 0.02, hy - 0.02, h * 0.5 - 0.01, h * 0.5 + 0.01, x, f, 'plank2')
    k.qz(-hx + 0.04, hx - 0.04, -0.012, 0.012, h + 0.003, 1, 'plank2')
    if kind == 'Powder':   # blasting powder box: red band and a black diamond
        k.qy(-hx + 0.1, hx - 0.1, h * 0.38, h * 0.62, -hy - 0.006, -1, 'red')
        k.poly([(0, -hy - 0.009, h * 0.42), (0.09, -hy - 0.009, h * 0.5), (0, -hy - 0.009, h * 0.58), (-0.09, -hy - 0.009, h * 0.5)], 'ink', (0, -1, 0))
    elif kind == 'Tools':
        k.qy(-hx + 0.1, hx - 0.1, h * 0.4, h * 0.6, -hy - 0.006, -1, 'board')
        k.qy(-0.15, 0.15, h * 0.46, h * 0.54, -hy - 0.009, -1, 'chalk')


def crate(k, kind):
    k.begin()
    if kind == 'Lid':      # stacked small box + coiled rope
        crate_body(k, 0.36, 0.3, 0.55, 'Tools')
        k.cyl(0.12, 0.05, 0.55, 0.17, 0.17, 0.09, 'rope', seg=8)
        k.cyl(0.12, 0.05, 0.64, 0.1, 0.1, 0.005, 'timber2', seg=8, ink=False)
    else:
        crate_body(k, 0.46, 0.4, 0.9, kind)
    return k


def sacks(k, variant):
    k.begin()
    rnd = random.Random(variant * 13 + 1)
    spots = [(-0.22, -0.18, 0), (0.22, -0.16, 0), (0.0, 0.2, 0), (0.0, -0.05, 0.32)] if variant == 0 else \
            [(-0.2, 0.0, 0), (0.24, 0.1, 0), (0.02, 0.0, 0.32)]
    for i, (x, y, z) in enumerate(spots):
        a = rnd.uniform(-25, 25)
        k.push(x, y, a, z)
        k.hullp([(sx * 0.24, sy * 0.17, sz) for sx, sy, sz in
                 ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (-1.1, -0.9, 0.18), (1.1, -0.9, 0.17), (1.1, 0.9, 0.19),
                  (-1.1, 0.9, 0.18), (-0.8, -0.6, 0.34), (0.85, -0.6, 0.33), (0.8, 0.6, 0.35), (-0.85, 0.6, 0.34))],
                'sack' if i % 2 == 0 else 'sack2')
        k.qz(-0.05, 0.05, -0.12, 0.12, 0.354, 1, 'cable')
        k.pop()
    return k


def coal_heap(k, variant):
    """2 x 2 m heap of coal lumps (cover)."""
    k.begin()
    rnd = random.Random(31 + variant * 7)
    fn = lambda f: 'coal2' if f.normal.z > 0.55 else 'coal'
    k.hullp(clamp_pts(rock_pts(rnd, (0, 0), 0.95, 0.85, 1.05, n=8, top=3, waist=(0.25, 0.5)), 0.98), fn)
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.75, 0.95)
        c = (math.cos(a) * r, math.sin(a) * r)
        k.hullp(clamp_pts(rock_pts(rnd, c, 0.18, 0.15, 0.2, n=4, top=1), 0.98), fn)
    if variant == 1:   # shovel stuck in
        k.beam((0.3, -0.3, 0.5), (0.55, -0.55, 1.5), 0.04, 'timber')
        k.bxr(0.28, -0.28, 0.42, 0.2, 0.03, 0.28, 'steel', rot=(20, 0, 45))
    return k


def timber_stack(k, variant):
    """Stacked props / sawn timbers (1 cell, runs along X)."""
    k.begin()
    rnd = random.Random(variant + 3)
    k.bx(-0.48, -0.36, -0.42, 0.42, 0, 0.12, 'timber2', ink=False)
    k.bx(0.36, 0.48, -0.42, 0.42, 0, 0.12, 'timber2', ink=False)
    rows = 4 if variant == 0 else 3
    for r in range(rows):
        n = 4 - (r if variant == 1 else 0)
        for i in range(n):
            y = -0.3 + i * 0.2 + (0.1 if r % 2 else 0) * (variant == 1)
            if abs(y) > 0.36:
                continue
            z = 0.12 + r * 0.19
            k.cyl(-0.5, y, z + 0.09, 0.088, 0.088, 1.0, 'timber' if (i + r) % 2 else 'timber2', seg=6, rot=(0, 90, 0))
    for s in (-1, 1):
        k.bx(*srt(s * 0.43, s * 0.47), -0.43, 0.43, 0, 0.18 + rows * 0.19, 'steelDark', ink=False)
    return k


def drums(k, variant):
    k.begin()
    spots = [(-0.22, -0.15), (0.24, 0.16)] if variant == 0 else [(0.0, 0.0)]
    for i, (x, y) in enumerate(spots):
        c, c2 = ('drum', 'drum2') if (i + variant) % 2 == 0 else ('cart', 'cart2')
        k.cyl(x, y, 0, 0.27, 0.27, 0.88, c, seg=10)
        for z in (0.29, 0.58):
            k.cyl(x, y, z, 0.283, 0.283, 0.035, c2, seg=10, ink=False, caps=False)
        k.cyl(x, y, 0.88, 0.22, 0.22, 0.006, c2, seg=10, ink=False)
        k.cyl(x + 0.17, y, 0.886, 0.04, 0.04, 0.02, 'steelDark', seg=6, ink=False)
    if variant == 1:
        k.cyl(-0.05, 0.0, 0.89, 0.1, 0.1, 0.3, 'lamp', seg=6)   # a lantern parked on the drum
        k.cyl(-0.05, 0.0, 1.19, 0.12, 0.04, 0.08, 'hood', seg=6)
    return k


def lantern_post(k, kind):
    k.begin()
    if kind == 'Post':
        k.bx(-0.09, 0.09, -0.09, 0.09, 0, 2.86, 'timber')
        k.bx(-0.07, 0.07, -0.7, 0.07, 2.75, 2.9, 'timber2')
        k.beam((0, 0.0, 2.3), (0, -0.4, 2.76), 0.07, 'timber2')
        lantern(k, 0.0, -0.62, 2.74)
        k.bx(-0.15, 0.15, -0.15, 0.15, 0, 0.25, 'rock2')
        pool(k, 0.0, -0.6, POOL_Z['post'], 2.2, 41)
    else:   # tripod work light with a cable reel
        for a in (0, 120, 240):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            k.beam((ca * 0.42, sa * 0.42, 0), (0, 0, 1.7), 0.05, 'steelDark')
        k.bx(-0.03, 0.03, -0.03, 0.03, 1.6, 2.2, 'steelDark')
        k.push(0, 0, 0, 2.2)
        k.bxr(0, -0.05, 0.05, 0.42, 0.22, 0.32, 'mach', rot=(-25, 0, 0))
        k.bxr(0, -0.17, -0.005, 0.36, 0.01, 0.26, 'lampHot', rot=(-25, 0, 0), ink=False)
        k.pop()
        k.cyl(0.35, 0.3, 0, 0.22, 0.22, 0.3, 'mach2', seg=8, rot=(0, 0, 0))
        k.cyl(0.35, 0.3, 0.3, 0.12, 0.12, 0.004, 'cable', seg=8, ink=False)
        pool(k, 0.0, -1.2, POOL_Z['work'], 2.3, 43, sx=0.9, sy=1.2)
    k.col(-0.15, 0.15, -0.15, 0.15, 0, 2.2)
    return k


def crib(k):
    """2 x 2 m timber crib (log-cabin stack) carrying a roof post and header up to the roof."""
    k.begin()
    z, L = 0.0, 0
    while z < 3.5:
        for s in (-1, 1):
            if L % 2 == 0:
                k.bx(-0.92, 0.92, *srt(s * 0.62, s * 0.9), z, z + 0.26, 'timber' if s > 0 else 'timber2')
            else:
                k.bx(*srt(s * 0.6, s * 0.88), -0.94, 0.94, z, z + 0.26, 'timber2' if s > 0 else 'timber')
        for s in (-1, 1):   # cut ends
            if L % 2 == 0:
                k.qx(*srt(s * 0.63, s * 0.89), z + 0.02, z + 0.24, 0.923, 1, 'timberEnd')
                k.qx(*srt(s * 0.63, s * 0.89), z + 0.02, z + 0.24, -0.923, -1, 'timberEnd')
            else:
                k.qy(*srt(s * 0.61, s * 0.87), z + 0.02, z + 0.24, 0.943, 1, 'timberEnd')
                k.qy(*srt(s * 0.61, s * 0.87), z + 0.02, z + 0.24, -0.943, -1, 'timberEnd')
        z += 0.26
        L += 1
    k.bx(-0.94, 0.94, -0.94, 0.94, z, z + 0.08, 'plank2')
    k.bx(-0.28, 0.28, -0.28, 0.28, z + 0.08, CEIL - 0.42, 'timber')
    k.bx(-0.95, 0.95, -0.33, 0.33, CEIL - 0.42, CEIL + 0.1, 'timber2')
    for a in (0, 90, 180, 270):
        k.push(0, 0, a)
        k.beam((0.28, 0, CEIL - 1.7), (0.9, 0, CEIL - 0.44), 0.16, 'timber2')
        k.pop()
    k.col(-0.95, 0.95, -0.95, 0.95, 0, CEIL)
    return k


def roof_jack(k):
    """Yellow hydraulic roof support with a timber header (1 cell)."""
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0, 0.12, 'steelDark')
    k.cyl(0, 0, 0.12, 0.17, 0.17, 3.2, 'mach', seg=8)
    k.cyl(0, 0, 3.32, 0.12, 0.12, CEIL - 3.32 - 0.5, 'steel', seg=8)
    k.cyl(0, 0, 3.0, 0.2, 0.2, 0.08, 'mach2', seg=8, ink=False)
    k.bx(-0.06, 0.06, -0.23, -0.17, 1.0, 2.6, 'rubber', ink=False)
    k.bx(-0.33, 0.33, -0.33, 0.33, CEIL - 0.5, CEIL - 0.36, 'steelDark')
    k.bx(-0.48, 0.48, -0.2, 0.2, CEIL - 0.36, CEIL + 0.1, 'timber')
    k.col(-0.3, 0.3, -0.3, 0.3, 0, CEIL)
    return k


def conveyor(k, variant):
    """Belt conveyor section (1 m along X): stands, idlers, troughed belt with coal on it."""
    k.begin()
    rnd = random.Random(60 + variant)
    for s in (-1, 1):
        k.bx(-0.5, 0.5, *srt(s * 0.42, s * 0.47), 0.82, 0.98, 'steel2')
    for x in (-0.3, 0.3):
        for s in (-1, 1):
            k.bx(x - 0.04, x + 0.04, *srt(s * 0.38, s * 0.45), 0, 0.82, 'steelDark', ink=False)
        k.bx(x - 0.03, x + 0.03, -0.44, 0.44, 0.2, 0.26, 'steelDark', ink=False)
    k.bx(-0.5, 0.5, -0.36, 0.36, 0.95, 1.0, 'rubber')
    for s in (-1, 1):
        k.bxr(0, s * 0.37, 1.04, 0.98, 0.16, 0.04, 'rubber', rot=(s * -35, 0, 0), ink=False)
    for i in range(3 if variant == 0 else 2):
        x = -0.32 + i * 0.32 + rnd.uniform(-0.05, 0.05)
        k.hullp(rock_pts(rnd, (x, rnd.uniform(-0.1, 0.1)), 0.14, 0.12, 0.16, z0=1.0, n=4, top=1), 'coal')
    k.bx(-0.5, 0.5, -0.33, 0.33, 0.45, 0.5, 'rubber', ink=False)   # return belt
    k.col(-0.5, 0.5, -0.47, 0.47, 0, 1.15)
    return k


def rail(k):
    k.begin()
    track(k, -0.5, 0.5, 0.0, sleepers=[-0.25, 0.25])
    return k


def cart_body(k, coal=True, tip=0.0):
    """Ore cart (1 m wide, 1.6 m long along Y) on four wheels, sitting on the track."""
    k.push(0, 0, 0, 0)
    for sy in (-1, 1):
        for sx in (-1, 1):
            k.cyl(sx * 0.3, sy * 0.48, 0.3, 0.17, 0.17, 0.08, 'steelDark', seg=8, rot=(0, 90, 0))
    k.bx(-0.42, 0.42, -0.72, 0.72, 0.3, 0.4, 'steelDark')
    k.hullp([(-0.48, -0.78, 0.4), (0.48, -0.78, 0.4), (0.48, 0.78, 0.4), (-0.48, 0.78, 0.4),
             (-0.56, -0.84, 1.2), (0.56, -0.84, 1.2), (0.56, 0.84, 1.2), (-0.56, 0.84, 1.2)], 'cart')
    k.bx(-0.58, 0.58, -0.86, 0.86, 1.2, 1.27, 'cart2')
    for s in (-1, 1):
        k.qx(-0.7, 0.7, 0.55, 0.62, s * 0.535, s, 'cart2')
        k.qx(-0.7, 0.7, 0.95, 1.02, s * 0.555, s, 'cart2')
        k.bx(-0.06, 0.06, *srt(s * 0.86, s * 1.0), 0.42, 0.52, 'steelDark', ink=False)   # couplers
    if coal:
        rnd = random.Random(int(tip * 10) + 5)
        k.hullp([(-0.5, -0.76, 1.15), (0.5, -0.76, 1.15), (0.5, 0.76, 1.15), (-0.5, 0.76, 1.15),
                 (-0.3, -0.4, 1.42), (0.3, -0.35, 1.45), (0.25, 0.4, 1.47), (-0.28, 0.35, 1.4), (0.0, 0.0, 1.58)],
                lambda f: 'coal2' if f.normal.z > 0.6 else 'coal')
        for i in range(3):
            x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.5, 0.5)
            k.hullp(rock_pts(rnd, (x, y), 0.12, 0.1, 0.13, z0=1.36, n=4, top=1), 'coal')
    k.pop()


def ore_cart(k, variant):
    """Prefab 1 x 2: track along Y under a loaded (or empty) ore cart."""
    k.begin()
    k.push(0, 0, 90)
    track(k, -1.0, 1.0, 0.0, sleepers=[-0.75, -0.25, 0.25, 0.75])
    k.pop()
    cart_body(k, coal=(variant != 1), tip=variant)
    k.col(-0.58, 0.58, -0.9, 0.9, 0, 1.3)
    return k


def timber_drift(k, variant):
    """Prefab 6 x 1: a timber set across a 6 m drift (posts, cap, braces, lagging) with a plank bulkhead up to the
    roof, so a run of sets is a closed timbered tunnel and its mouths never show the void above the lagging.
    'Rail' variants carry the track along the drift (centred on the cell at local x = +0.5)."""
    k.begin()
    timber_set(k, 2.72, cap_z=3.92)
    for i in range(13):
        x0 = -3.3 + i * 0.508
        k.bx(x0 + 0.006, x0 + 0.5, -0.5, 0.5, 4.26, 4.32, 'plank' if i % 2 else 'plank2', ink=False)
    bulkhead(k, -3.4, 3.4, 4.32, WALL_H + 0.06, t=0.1, dark=True)
    if variant in ('Lamp', 'RailLamp'):
        lantern(k, -1.2, -0.25, 3.92)
        pool(k, -1.2, -0.2, POOL_Z['set'], 0.45, 3)
    if variant.startswith('Rail'):
        k.push(0.5, 0, 90)
        track(k, -0.5, 0.5, 0.0, sleepers=[-0.25, 0.25])
        k.pop()
    for s in (-1, 1):
        k.col(*srt(s * 2.57, s * 2.87), -0.15, 0.15, 0, 3.92)
    return k


def puddle(k, variant):
    k.begin()
    rnd = random.Random(70 + variant)
    k.disc(0.0, 0.0, Z_PUDDLE, 0.85, 'water', n=11, rnd=rnd, jag=0.18, sx=1.0, sy=0.7)
    k.poly([(-0.3, -0.1, Z_PUDDLE + 0.004), (0.1, -0.16, Z_PUDDLE + 0.004), (0.12, -0.11, Z_PUDDLE + 0.004), (-0.28, -0.05, Z_PUDDLE + 0.004)], 'waterG', (0, 0, 1))
    k.poly([(0.2, 0.12, Z_PUDDLE + 0.004), (0.42, 0.08, Z_PUDDLE + 0.004), (0.43, 0.12, Z_PUDDLE + 0.004), (0.21, 0.16, Z_PUDDLE + 0.004)], 'waterG', (0, 0, 1))
    return k


def dust(k, variant):
    k.begin()
    rnd = random.Random(80 + variant)
    k.disc(0.0, 0.0, Z_DUST, 0.9, 'dust', n=12, rnd=rnd, jag=0.25)
    for i in range(6):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.3, 0.8)
        k.hullp(rock_pts(rnd, (math.cos(a) * r, math.sin(a) * r), 0.07, 0.06, 0.08, n=4, top=1), 'coal')
    return k


# ================================================================ landmarks
def drill_rig(k):
    """Landmark 8 x 5: a drill jumbo on crawler tracks, two booms into the coal face (+Y), canopy and work lights,
    a cable reel and a coal heap beside it."""
    k.begin()
    # tracks
    for s in (-1, 1):
        x0, x1 = srt(s * 1.25, s * 1.85)
        k.bx(x0, x1, -2.1, 0.9, 0.12, 0.62, 'rubber')
        for i in range(7):
            y = -1.95 + i * 0.44
            k.qx(y, y + 0.1, 0.16, 0.58, s * (1.853), s, 'steelDark')
        k.bx(x0 + 0.08, x1 - 0.08, -2.0, 0.8, 0.0, 0.12, 'steelDark', ink=False)
    # body
    k.bx(-1.3, 1.3, -2.2, 0.9, 0.62, 1.55, 'mach')
    k.bx(-1.32, 1.32, -2.22, 0.92, 1.0, 1.1, 'mach2', ink=False)
    k.stripes(-1.3, 1.3, 0.66, 0.92, -2.203, -1, 10)
    k.bx(-0.9, 0.2, -2.1, -0.9, 1.55, 2.0, 'mach2')                      # power pack
    for i in range(4):
        k.qz(-0.85, 0.15, -2.02 + i * 0.27, -1.92 + i * 0.27, 2.003, 1, 'steelDark')
    # canopy over the operator seat
    for x in (0.35, 1.25):
        for y in (-2.0, -0.95):
            k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 1.55, 3.0, 'steelDark')
    k.bx(0.25, 1.35, -2.1, -0.85, 3.0, 3.1, 'mach')
    k.bx(0.55, 1.05, -1.75, -1.35, 1.55, 1.95, 'rubber')                 # seat
    k.bx(0.55, 1.05, -1.4, -1.32, 1.95, 2.45, 'rubber')
    k.bx(0.6, 1.0, -1.1, -0.95, 1.55, 2.2, 'steelDark')                   # control stand
    k.qy(0.66, 0.94, 1.95, 2.12, -1.103, -1, 'teal')
    for x in (0.45, 1.15):                                                # work lights + pool ahead
        k.bxr(x, -0.82, 3.12, 0.22, 0.14, 0.16, 'steelDark', rot=(15, 0, 0))
        k.qy(x - 0.08, x + 0.08, 3.08, 3.18, -0.893, -1, 'lampHot')
    pool(k, 0.0, 1.7, POOL_Z['drill'], 1.5, 17, sx=1.6, sy=0.6)
    # booms: turret, boom arm, feed beam and drill steel into the face
    for s in (-1, 1):
        k.push(s * 0.7, 0.9, 0, 1.35)
        k.bx(-0.28, 0.28, -0.25, 0.25, -0.2, 0.3, 'mach2')
        k.beam((0, 0.0, 0.05), (s * 0.25, 1.0, 0.55 + 0.2 * s), 0.26, 'mach')
        k.bx(s * 0.25 - 0.1, s * 0.25 + 0.1, 0.4, 1.55, 0.45 + 0.2 * s, 0.68 + 0.2 * s, 'steel')
        k.bx(s * 0.25 - 0.04, s * 0.25 + 0.04, 1.55, 1.62, 0.53 + 0.2 * s, 0.61 + 0.2 * s, 'steelDark')
        k.cyl(s * 0.25, 1.62, 0.57 + 0.2 * s, 0.07, 0.03, 0.08, 'steelDark', seg=6, rot=(-90, 0, 0))
        k.beam((-0.05 * s, -0.2, 0.25), (s * 0.2, 0.9, 0.4 + 0.2 * s), 0.05, 'rubber', ink=False)
        k.pop()
    # cable reel and cable to the wall, coal heap by the face
    k.cyl(-3.0, -0.8, 0.0, 0.32, 0.32, 0.12, 'steelDark', seg=8)
    k.cyl(-3.4, -0.8, 0.75, 0.7, 0.7, 0.08, 'mach2', seg=12, rot=(0, 90, 0))
    k.cyl(-2.6, -0.8, 0.75, 0.7, 0.7, 0.08, 'mach2', seg=12, rot=(0, -90, 0))
    k.cyl(-3.32, -0.8, 0.75, 0.48, 0.48, 0.64, 'cable', seg=10, rot=(0, 90, 0))
    k.bx(-3.55, -2.45, -1.3, -0.3, 0, 0.1, 'steelDark')
    for s in (-1, 1):
        k.beam((-3.0 + s * 0.5, -0.8, 0.1), (-3.0 + s * 0.42, -0.8, 0.78), 0.08, 'steelDark')
    k.beam((-2.62, -0.4, 0.3), (-1.3, -0.4, 0.9), 0.07, 'cable', ink=False)
    rnd = random.Random(9)
    fn = lambda f: 'coal2' if f.normal.z > 0.55 else 'coal'
    k.hullp(clamp_pts(rock_pts(rnd, (2.9, 1.3), 1.0, 0.9, 1.1, n=7, top=2), 3.9, 2.45), fn)
    k.hullp(clamp_pts(rock_pts(rnd, (-2.6, 1.6), 0.7, 0.6, 0.6, n=6, top=1), 3.9, 2.45), fn)
    crate_body_at(k, 3.1, -1.4, 'Powder')
    k.col(-1.9, 1.9, -2.25, 0.95, 0, 3.1)
    k.col(-1.1, 1.1, 0.95, 2.5, 0.9, 2.2)
    k.col(-3.6, -2.4, -1.5, -0.1, 0, 1.5)
    k.col(2.0, 3.9, 0.4, 2.3, 0, 1.0)
    k.col(2.6, 3.6, -1.85, -0.95, 0, 0.92)
    return k


def crate_body_at(k, x, y, kind, deg=0):
    k.push(x, y, deg)
    crate_body(k, 0.46, 0.4, 0.9, kind)
    k.pop()


def headframe(k):
    """Landmark 6 x 6: the main shaft. Timber collar with hazard rails round a dark pit, the cage parked at the
    landing, a steel A-frame headframe with twin sheave wheels up under the roof and the winder beside it."""
    k.begin()
    S = 2.2
    # collar (low timber curb), pit
    for s in (-1, 1):
        k.bx(-S, S, *srt(s * (S - 0.3), s * S), 0, 0.35, 'timber')
        k.bx(*srt(s * (S - 0.3), s * S), -S + 0.3, S - 0.3, 0, 0.35, 'timber2')
    k.qz(-S + 0.3, S - 0.3, -S + 0.3, S - 0.3, POOL_Z['head'], 1, 'pit')
    # rails on three sides, landing gate (hazard) on the -Y side
    for (x0, x1, y0, y1) in ((-S + 0.1, S - 0.1, S - 0.2, S - 0.1), (-S, -S + 0.1, -S, S), (S - 0.1, S, -S, S)):
        k.bx(x0, x1, y0, y1, 1.0, 1.1, 'hazard')
    for (x, y) in ((-S + 0.05, -S + 0.05), (S - 0.05, -S + 0.05), (-S + 0.05, S - 0.15), (S - 0.05, S - 0.15), (-S + 0.05, 0), (S - 0.05, 0), (0, S - 0.15)):
        k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.35, 1.14, 'steelDark')
    k.bx(-S + 0.1, -0.75, -S + 0.02, -S + 0.12, 0.98, 1.08, 'hazard')
    k.bx(0.75, S - 0.1, -S + 0.02, -S + 0.12, 0.98, 1.08, 'hazard')
    k.stripes(-0.75, 0.75, 0.55, 1.05, -S - 0.003, -1, 6)
    # cage in the shaft
    W, D = 0.9, 0.8
    k.bx(-W, W, -D, D, 0.3, 0.42, 'steelDark')
    for x in (-W, W):
        for y in (-D, D):
            k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.42, 2.9, 'steel')
    for s in (-1, 1):
        for i in range(1, 6):
            y = -D + 2 * D * i / 6
            k.bx(s * W - 0.02, s * W + 0.02, y - 0.02, y + 0.02, 0.42, 2.9, 'steel2', ink=False)
    for i in range(1, 6):
        x = -W + 2 * W * i / 6
        k.bx(x - 0.02, x + 0.02, D - 0.02, D + 0.02, 0.42, 2.9, 'steel2', ink=False)
    k.bx(-W - 0.06, W + 0.06, -D - 0.06, D + 0.06, 2.9, 3.05, 'cart')
    lantern(k, 0.0, -D + 0.1, 2.9, 0.8)
    # headframe: two A-frame legs per side, cross head, sheaves
    for s in (-1, 1):
        k.beam((s * 2.6, -2.6, 0), (s * 1.3, 0.0, 8.0), 0.3, 'steel2')
        k.beam((s * 2.6, 2.6, 0), (s * 1.3, 0.0, 8.0), 0.3, 'steel2')
        k.beam((s * 2.25, -1.9, 2.2), (s * 2.25, 1.9, 2.2), 0.18, 'steelDark')
        k.beam((s * 1.85, -1.1, 4.6), (s * 1.85, 1.1, 4.6), 0.16, 'steelDark')
        k.bx(s * 2.6 - 0.3, s * 2.6 + 0.3, -2.9, -2.3, 0, 0.25, 'rock2')
        k.bx(s * 2.6 - 0.3, s * 2.6 + 0.3, 2.3, 2.9, 0, 0.25, 'rock2')
    k.bx(-1.6, 1.6, -0.35, 0.35, 7.9, 8.4, 'steel2')
    for x in (-0.55, 0.55):
        k.cyl(x - 0.05, 0, 8.55, 0.75, 0.75, 0.1, 'cart', seg=12, rot=(0, 90, 0))
        k.bx(x - 0.015, x + 0.015, -0.71, -0.68, 3.05, 8.5, 'cable', ink=False)
    k.bx(-1.65, 1.65, -0.4, 0.4, 8.4, CEIL + 0.1, 'steelDark')
    # winder house: drum + motor on the +X side corner
    k.col(-S, S, -S, S, 0, 1.1)
    for s in (-1, 1):
        k.col(s * 2.6 - 0.3, s * 2.6 + 0.3, -2.9, -2.3, 0, 2.0)
        k.col(s * 2.6 - 0.3, s * 2.6 + 0.3, 2.3, 2.9, 0, 2.0)
    return k


def hopper(k):
    """Landmark 6 x 4: loading hopper on legs over the track (track along X at local y = +0.5), a cart under the
    chute, and an inclined belt conveyor feeding it from the -X side."""
    k.begin()
    track(k, -3.0, 3.0, 0.5, sleepers=[-2.75 + 0.5 * i for i in range(12)])
    k.push(0.0, 0.5, 90)
    cart_body(k, coal=True, tip=3)
    k.pop()
    for x in (-0.25 - 1.0, 1.25):
        for y in (-1.4, 1.6):
            k.bx(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, 3.3, 'steel2')
    k.beam((-1.25, -1.4, 0.6), (1.25, -1.4, 2.8), 0.1, 'steelDark')
    k.beam((-1.25, 1.6, 0.6), (1.25, 1.6, 2.8), 0.1, 'steelDark')
    k.hullp([(-0.45, 0.15, 2.3), (0.45, 0.15, 2.3), (0.45, 0.85, 2.3), (-0.45, 0.85, 2.3),
             (-1.4, -1.6, 4.4), (1.4, -1.6, 4.4), (1.4, 1.8, 4.4), (-1.4, 1.8, 4.4)], 'cart2')
    k.bx(-1.45, 1.45, -1.65, 1.85, 4.4, 4.55, 'cart')
    k.bx(-0.3, 0.3, 0.2, 0.8, 1.75, 2.35, 'steelDark')
    k.hullp([(-1.2, -1.4, 4.43), (1.2, -1.4, 4.43), (1.2, 1.6, 4.43), (-1.2, 1.6, 4.43), (0, 0.1, 4.95), (-0.5, 0.6, 4.8), (0.6, -0.4, 4.75)],
            lambda f: 'coal2' if f.normal.z > 0.6 else 'coal')
    # inclined conveyor from the floor at -X up to the hopper rim
    a, b = Vector((-3.0, -0.6, 0.6)), Vector((-1.1, -0.6, 4.6))
    k.beam(a, b, 0.5, 'steel2')
    k.beam(a + Vector((0, 0, 0.27)), b + Vector((0, 0, 0.27)), 0.38, 'rubber', ink=False)
    for t in (0.2, 0.55):
        p = a.lerp(b, t)
        k.bx(p.x - 0.07, p.x + 0.07, -0.9, -0.3, 0, p.z - 0.1, 'steelDark')
    lantern(k, 1.4, -1.75, 4.4)
    pool(k, 1.6, -1.6, POOL_Z['hopper'], 1.2, 23)
    k.col(-1.45, 1.45, -1.65, 1.85, 1.75, 4.55)
    for x in (-1.25, 1.25):
        for y in (-1.4, 1.6):
            k.col(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, 3.3)
    k.col(-0.58, 0.58, -0.4, 1.4, 0, 1.3)
    k.col(-3.0, -2.0, -0.95, -0.25, 0, 1.4)
    return k


def shack(k):
    """Landmark 5 x 4: the foreman's shack: plank walls, corrugated roof, lit window, door lamp, chalk board."""
    k.begin()
    X0, X1, Y0, Y1, Hh = -2.3, 2.3, -1.2, 1.8, 2.7
    k.bx(X0, X1, Y0, Y1, 0, Hh, 'plank')
    for s, y in ((-1, Y0 - 0.003), (1, Y1 + 0.003)):
        for i in range(1, 14):
            x = X0 + (X1 - X0) * i / 14
            k.qy(x - 0.012, x + 0.012, 0.05, Hh - 0.05, y, s, 'plank2')
    for s, x in ((-1, X0 - 0.003), (1, X1 + 0.003)):
        for i in range(1, 9):
            y = Y0 + (Y1 - Y0) * i / 9
            k.qx(y - 0.012, y + 0.012, 0.05, Hh - 0.05, x, s, 'plank2')
    k.hullp([(X0 - 0.25, Y0 - 0.45, Hh), (X1 + 0.25, Y0 - 0.45, Hh), (X1 + 0.25, Y1 + 0.25, Hh + 0.15), (X0 - 0.25, Y1 + 0.25, Hh + 0.15),
             (X0 - 0.25, Y0 - 0.45, Hh + 0.12), (X1 + 0.25, Y0 - 0.45, Hh + 0.12), (X1 + 0.25, Y1 + 0.25, Hh + 0.6), (X0 - 0.25, Y1 + 0.25, Hh + 0.6)], 'tin')
    for i in range(10):
        x = X0 - 0.2 + i * 0.5
    # door, window (lit), lamp over the door, chalk board
    k.bx(-1.45, -0.6, Y0 - 0.06, Y0, 0, 2.1, 'timber2')
    k.qy(-1.0, -0.9, 1.0, 1.08, Y0 - 0.063, -1, 'steel')
    k.bx(0.2, 1.5, Y0 - 0.06, Y0, 1.0, 1.9, 'timber2')
    k.qy(0.28, 1.42, 1.08, 1.82, Y0 - 0.063, -1, 'lamp')
    k.qy(0.83, 0.87, 1.08, 1.82, Y0 - 0.066, -1, 'timber2')
    k.qy(0.28, 1.42, 1.43, 1.47, Y0 - 0.069, -1, 'timber2')
    k.bx(-1.08, -0.98, Y0 - 0.45, Y0, 2.3, 2.38, 'steelDark')
    lantern(k, -1.03, Y0 - 0.42, 2.34, 0.85)
    pool(k, -0.4, Y0 - 1.2, POOL_Z['shack'], 1.4, 27, sx=1.4, sy=0.8)
    k.bx(X1, X1 + 0.05, -0.6, 0.9, 1.0, 1.9, 'board')
    k.qx(-0.5, 0.2, 1.6, 1.64, X1 + 0.053, 1, 'chalk')
    k.qx(-0.5, 0.6, 1.4, 1.44, X1 + 0.053, 1, 'chalk')
    k.qx(-0.5, 0.0, 1.2, 1.24, X1 + 0.053, 1, 'chalk')
    # bench and a stack of powder boxes by the wall
    k.bx(0.3, 1.9, Y0 - 0.55, Y0 - 0.15, 0.42, 0.5, 'timber')
    for x in (0.4, 1.8):
        k.bx(x - 0.05, x + 0.05, Y0 - 0.5, Y0 - 0.2, 0, 0.42, 'timber2', ink=False)
    crate_body_at(k, -2.0, Y0 - 0.65, 'Powder', 8)
    k.col(X0, X1, Y0, Y1, 0, Hh + 0.6)
    k.col(-2.5, -1.5, Y0 - 1.1, Y0 - 0.2, 0, 0.92)
    return k


# ================================================================ backdrop (seen through the overlooks)
def backdrop_cavern(k):
    """The far side of the big mine: one long slice (+-110 m along X, facing -Y) of cavern wall with lit drift
    mouths, timber stagings and a distant headframe; it sinks into the dark below the floor line."""
    k.begin()
    rnd = random.Random(101)
    fn = lambda f: 'farLit' if f.normal.z > 0.5 else ('far' if f.normal.y < -0.3 else 'far2')
    x = -112.0
    while x < 112:
        w = rnd.uniform(14, 22)
        h = rnd.uniform(16, 26)
        zb = -6.0 - 0.01 * ((x + 112) % 7)
        yb = 8.0 + 0.3 * ((x + 112) % 5)
        k.hullp([(x, 0, zb), (x + w, 0, zb), (x + w, yb, zb), (x, yb, zb),
                 (x + rnd.uniform(0, 3), rnd.uniform(-1, 1), h * rnd.uniform(0.5, 0.7)),
                 (x + w - rnd.uniform(0, 3), rnd.uniform(-1, 1), h * rnd.uniform(0.5, 0.7)),
                 (x + w * 0.3, 3, h), (x + w * 0.7, 4, h * rnd.uniform(0.85, 1.05)), (x + w * 0.5, yb, h * 1.1)], fn)
        x += w * 0.8
    # drift mouths with lantern glow, stagings
    for (x, z) in ((-90, 2.0), (-62, 6.5), (-30, 1.5), (-6, 9.0), (18, 3.0), (44, 7.5), (70, 2.5), (96, 5.0)):
        k.qy(x - 2.0, x + 2.0, z, z + 3.0, -2.5, -1, 'pit')
        k.qy(x - 0.25, x + 0.25, z + 2.2, z + 2.6, -2.506, -1, 'lamp')
        k.bx(x - 2.4, x - 2.1, -2.8, -2.4, z, z + 3.3, 'timber2')
        k.bx(x + 2.1, x + 2.4, -2.8, -2.4, z, z + 3.3, 'timber2')
        k.bx(x - 2.5, x + 2.5, -2.86, -2.34, z + 3.0, z + 3.35, 'timber2')
        if z > 4:
            k.bx(x - 4, x + 4, -4.0, -2.4, z - 0.25, z, 'timber2')
            for xx in (x - 3.6, x + 3.6):
                k.beam((xx, -3.8, -6), (xx, -3.8, z - 0.25), 0.25, 'timber2', ink=False)
    # distant headframe
    k.beam((30, -4, -6), (33, -4, 18), 0.5, 'far2')
    k.beam((36, -4.6, -6), (33, -4.6, 18), 0.5, 'far2')
    k.cyl(33, -4.3, 18.5, 1.4, 1.4, 0.3, 'farLit', seg=10, rot=(90, 0, 0))
    return k


# ================================================================ build
WALL_KINDS = (('Rock_A', 'A', 11), ('Rock_B', 'B', 23), ('Rock_C', 'C', 37), ('Seam_A', 'Seam', 41),
              ('Seam_B', 'Seam', 52), ('Rock_LampS', 'LampS', 61), ('Rock_LampN', 'LampN', 67),
              ('Rock_LampE', 'LampE', 63), ('Rock_LampW', 'LampW', 69),
              ('Rock_Prop', 'Prop', 73), ('Rock_Sign', 'Sign', 79))


def build_kit_coalmine(ao):
    pal = Palette(FAM)
    k = Kit(pal, PFX, HULL_T)
    for name, kind, seed in WALL_KINDS:
        wall_module(k, kind, seed).finish(name, ao=ao)
    overlook(k, 91).finish('Rock_Open', ao=ao)
    for name, seed in (('Rock_Corner_A', 5), ('Rock_Corner_B', 17)):
        corner(k, seed).finish(name, ao=ao)
    ceil_rock(k).finish('CeilRock')
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    trail_wall(k).finish('TrailWall', ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    for kind in ('Powder', 'Tools', 'Plain', 'Lid'):
        crate(k, kind).finish('Crate_' + kind, ao=ao)
    for v in (0, 1):
        sacks(k, v).finish('Sacks_%s' % 'AB'[v], ao=ao)
        coal_heap(k, v).finish('CoalHeap_%s' % 'AB'[v], ao=ao)
        timber_stack(k, v).finish('Timbers_%s' % 'AB'[v], ao=ao)
        drums(k, v).finish('Drums_%s' % 'AB'[v], ao=ao)
        conveyor(k, v).finish('Conveyor_%s' % 'AB'[v], ao=ao)
        puddle(k, v).finish('Puddle_%s' % 'AB'[v])
        dust(k, v).finish('Dust_%s' % 'AB'[v])
    lantern_post(k, 'Post').finish('LanternPost', ao=ao)
    lantern_post(k, 'Work').finish('WorkLight', ao=ao)
    crib(k).finish('Crib', ao=ao)
    roof_jack(k).finish('RoofJack', ao=ao)
    rail(k).finish('Rail')
    for v, name in ((0, 'OreCart_Full'), (1, 'OreCart_Empty')):
        ore_cart(k, v).finish(name, ao=ao)
    for v in ('Plain', 'Lamp', 'Rail', 'RailLamp'):
        timber_drift(k, v).finish('Drift_' + v, ao=ao)
    drill_rig(k).finish('Landmark_DrillRig', ao=ao)
    headframe(k).finish('Landmark_Headframe', ao=ao)
    hopper(k).finish('Landmark_Hopper', ao=ao)
    shack(k).finish('Landmark_Shack', ao=ao)
    backdrop_cavern(k).finish('Backdrop_Cavern')
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_coalmine
