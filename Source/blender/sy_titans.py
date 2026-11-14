"""kit-scrapyard: zone 2, the Titan Graveyard -- the remains of colossal war machines, designed here as derelict
walkers (bevelled armour slabs on joint drums, pistons, cables; no faces: visors with dead lenses):

  Landmark_Titan + Landmark_TitanUpper  the kneeling dead titan [22, 20]: one knee down, the other foot planted, its left
                                 hand braced on the ground, slumped forward over the yard; its right arm is torn off at
                                 the shoulder (it lies in the yard: Arm). You walk between its legs, under its belly.
  Landmark_Torso                 a fallen torso lying on its side [18, 10]: walk in at the torn waist, through the
                                 ribbed hull past its cracked reactor (glowing), and out at the neck collar
  Landmark_Head                  an enormous head [10, 10] lying on its cheek: visor with three dead eye lenses
  Landmark_Ribs                  a chest frame on its back [18, 12]: spine, rib arches, and the salvage crew's plating
                                 ramps up to decks at 3.0 m and 5.4 m between the ribs
  Landmark_Cannon                a colossal broken cannon [20, 4]; Reactor_A / Reactor_B dead reactor cores [4, 4]
  Scaffold, Arm, Plates, BeaconPost, the far backdrop (heaps, a dead titan standing far off, a tower crane)

Conventions: sy_base.py. Every part is modelled in its prefab's frame (origin = footprint centre on the floor, front
-Y = game south, toward the zone entry).
"""
import math
import random

from mathutils import Matrix, Vector

from sy_base import (Z, CARS, srt, slab, slab3, oslab, tube, drumx, drumy, frame_at, hull_box, tbox, pool_disc,
                     sodium_head, text, sign_board, plate_ramp, lattice, scrap_fn, heap, plate, ibeam, rock_pts, cable)
from gem_base import stairs_x, deck, rail_x, rail_y
import sy_detail as D
from foundry_common import guard_rail

V = Vector


def joint(k, p, r, L, axis='x', c='gun2', seg=10):
    if axis == 'x':
        drumx(k, p.x, p.y, p.z, r, L, c, seg=seg)
    else:
        drumy(k, p.x, p.y, p.z, r, L, c, seg=seg)


def lens(k, x, y, z, r, s=-1, crack=False):
    """A dead eye lens on a -Y (s=-1) face at y: a dark rim drum standing 0.25 m out, the black glass 3 mm proud of it,
    a cold reflection crescent (and a crack) 3 mm proud of the glass."""
    rot = (90 * -s, 0, 0)
    k.cyl(x, y, z, r * 1.18, r * 1.18, 0.25, 'steelDark', seg=12, rot=rot)
    k.cyl(x, y + s * 0.253, z, r, r, 0.003, 'lensD', seg=12, rot=rot, ink=False)
    yc = y + s * 0.259
    k.poly([(x - r * 0.62, yc, z + r * 0.12), (x - r * 0.4, yc, z + r * 0.52), (x - r * 0.05, yc, z + r * 0.66), (x - r * 0.3, yc, z + r * 0.36)], 'lensR', (0, s, 0))
    if crack:
        k.poly([(x + r * 0.1, yc, z - r * 0.1), (x + r * 0.62, yc, z - r * 0.5), (x + r * 0.2, yc, z - r * 0.18), (x + r * 0.5, yc, z + r * 0.25)], 'lensR', (0, s, 0))


def reactor_core(k, p, r, L, axis='y', lit=True):
    """A reactor drum: a housing with a glowing cyan window band and end rings (faint: the core is dying)."""
    if axis == 'y':
        drumy(k, p.x, p.y, p.z, r, L, 'gun2', seg=12)
        for yy in (p.y - L * 0.42, p.y + L * 0.42):
            drumy(k, p.x, yy, p.z, r * 1.08, L * 0.1, 'steelDark', seg=12)
        if lit:
            k.g.cyl(p.x, p.y - L * 0.18, p.z, r * 1.01, r * 1.01, L * 0.36, 'cyanD', seg=12, rot=(-90, 0, 0), ink=False)
            k.g.cyl(p.x, p.y - L * 0.06, p.z, r * 1.015, r * 1.015, L * 0.12, 'cyan', seg=12, rot=(-90, 0, 0), ink=False)
    else:
        k.cyl(p.x, p.y, p.z - L / 2, r, r, L, 'gun2', seg=12)
        for zz in (p.z - L * 0.47, p.z + L * 0.37):
            k.cyl(p.x, p.y, zz, r * 1.08, r * 1.08, L * 0.1, 'steelDark', seg=12)
        if lit:
            k.g.cyl(p.x, p.y, p.z - L * 0.18, r * 1.01, r * 1.01, L * 0.36, 'cyanD', seg=12, ink=False)
            k.g.cyl(p.x, p.y, p.z - L * 0.06, r * 1.015, r * 1.015, L * 0.12, 'cyan', seg=12, ink=False)


# ================================================================ the kneeling titan [22, 20]
S = 1.55         # the titan's scale (designed at 1/1.55, every point and box goes through P / colS())
DY = -0.3        # shift along y so it sits in its footprint


def P(x, y, z):
    return V((x * S, (y + DY) * S, z * S))


def colS(k, x0, x1, y0, y1, z0, z1):
    k.col(x0 * S, x1 * S, (y0 + DY) * S, (y1 + DY) * S, z0 * S, z1 * S)


def tslab(k, a, b, wa, da, wb, db, c, ch=0.0):
    oslab(k, a, b, wa * S, da * S, wb * S, db * S, c, ch=ch * S)


def tdrum(k, p, r, L, axis='x', c='gun2', seg=10):
    joint(k, p, r * S, L * S, axis=axis, c=c, seg=seg)


def titan_lower(k):
    """The kneeling titan, lower part: the planted left leg (foot, shin, knee, thigh), the kneeling right leg (knee on
    the ground, shin back along the ground, toes dug in), the pelvis, the braced left arm and its fist on the ground."""
    k.begin()
    # -- left leg: foot planted forward, shin up to the knee, thigh back to the hip
    ft = P(-3.3, -3.7, 0.0)
    slab3(k, ft.x, ft.y, [(0.0, 1.3 * S, 1.75 * S, 0, 0), (0.75 * S, 1.25 * S, 1.65 * S, 0, 0.1 * S), (1.3 * S, 0.9 * S, 1.0 * S, 0, 0.4 * S)], 'gun2', ch=0.35 * S)
    for x in (-0.65, 0.65):
        slab(k, ft.x + x * S, ft.y - 1.3 * S, 0.0, 0.7 * S, 0.5 * S, 0.7 * S, 0.42 * S, 0.5 * S, 'olive', ch=0.12 * S, dy=-0.2 * S)
    ank, kn, hp = P(-3.3, -3.4, 1.7), P(-3.4, -3.7, 7.2), P(-2.9, 1.0, 7.6)
    tdrum(k, ank, 0.8, 1.7)
    tslab(k, ank, kn, 1.0, 0.95, 1.1, 1.05, 'olive', ch=0.3)
    tslab(k, ank + V((0, -0.9 * S, 1.0 * S)), kn + V((0, -0.95 * S, -0.8 * S)), 0.75, 0.25, 0.85, 0.3, 'bone', ch=0.12)       # shin guard
    tdrum(k, kn, 1.05, 2.1)
    slab(k, kn.x, kn.y - 0.6 * S, kn.z - 0.2 * S, kn.z + 1.4 * S, 1.05 * S, 0.5 * S, 0.8 * S, 0.35 * S, 'bone', ch=0.2 * S, dy=-0.3 * S)  # knee cap
    tslab(k, kn, hp, 1.1, 1.05, 1.25, 1.15, 'olive', ch=0.35)
    tube(k, P(-4.4, -3.0, 2.5), P(-4.45, -3.3, 6.2), 0.22 * S, 'chrome', seg=6, ink=False)
    tube(k, P(-4.4, -1.0, 6.4), P(-4.3, 0.6, 7.2), 0.25 * S, 'steelDark', seg=8)
    # -- right leg: knee on the ground, the shin lying back, the foot's toes dug in
    kr, ar, hr = P(3.3, -0.7, 1.1), P(3.35, 4.6, 1.0), P(2.9, 1.0, 7.6)
    tdrum(k, kr, 1.05, 2.1)
    slab(k, kr.x, kr.y - 0.75 * S, 0.0, 2.2 * S, 1.0 * S, 0.45 * S, 0.8 * S, 0.3 * S, 'bone', ch=0.2 * S)
    tslab(k, kr, ar, 1.0, 0.95, 0.9, 0.85, 'olive', ch=0.28)
    tslab(k, kr + V((0, 0.9 * S, 0.95 * S)), ar + V((0, -0.8 * S, 0.85 * S)), 0.75, 0.22, 0.65, 0.2, 'bone', ch=0.1)
    tdrum(k, ar, 0.78, 1.6)
    slab3(k, ar.x, ar.y + 1.2 * S, [(0.0, 1.2 * S, 0.9 * S, 0, 0), (1.6 * S, 1.1 * S, 0.7 * S, 0, -0.5 * S), (2.2 * S, 0.8 * S, 0.45 * S, 0, -0.75 * S)], 'gun2', ch=0.3 * S)
    tslab(k, kr, hr, 1.1, 1.05, 1.25, 1.15, 'olive', ch=0.35)
    tube(k, P(4.4, -0.2, 1.8), P(4.3, 0.6, 6.4), 0.24 * S, 'steelDark', seg=8)
    # -- pelvis, hip drums, the crotch plate
    slab3(k, 0.0, 1.0 * DY * 0 + P(0, 1.0, 0).y, [(6.8 * S, 2.4 * S, 1.6 * S, 0, 0), (8.4 * S, 2.9 * S, 1.8 * S, 0, 0), (9.2 * S, 2.6 * S, 1.6 * S, 0, 0.1 * S)], 'gun2', ch=0.5 * S)
    for sx in (-1, 1):
        tdrum(k, P(sx * 2.95, 1.0, 7.6), 1.15, 1.3)
    slab(k, 0.0, P(0, 0.0, 0).y, 6.0 * S, 7.6 * S, 0.9 * S, 0.5 * S, 1.6 * S, 0.6 * S, 'bone', ch=0.25 * S, dy=-0.2 * S)
    # -- left arm: shoulder stub is in the upper part; upper arm, elbow, forearm to the fist braced on the ground
    sh, el, wr = P(-5.6, 0.0, 13.6), P(-6.3, -2.2, 8.6), P(-6.0, -4.5, 2.2)
    tslab(k, sh, el, 0.95, 0.95, 0.85, 0.85, 'olive', ch=0.28)
    tdrum(k, el, 0.85, 1.5)
    tslab(k, el, wr, 1.0, 1.0, 1.1, 1.05, 'olive', ch=0.3)
    tslab(k, el + V((-0.85 * S, 0, -0.5 * S)), wr + V((-0.95 * S, 0, 0.9 * S)), 0.2, 0.9, 0.2, 0.95, 'bone', ch=0.1)
    tdrum(k, wr, 0.7, 1.4)
    fist = P(-6.0, -4.9, 0.0)
    slab3(k, fist.x, fist.y, [(0.0, 1.0 * S, 1.0 * S, 0, 0), (1.5 * S, 1.05 * S, 1.05 * S, 0, 0.1 * S), (2.0 * S, 0.8 * S, 0.8 * S, 0, 0.2 * S)], 'gun2', ch=0.3 * S)
    for i in range(3):
        slab(k, fist.x + (-0.6 + i * 0.6) * S, fist.y - 0.95 * S, 0.0, 0.75 * S, 0.27 * S, 0.35 * S, 0.24 * S, 0.3 * S, 'gun', ch=0.08 * S)
    tube(k, P(-5.3, -1.2, 11.8), P(-5.5, -3.4, 4.4), 0.2 * S, 'chrome', seg=6, ink=False)
    # warpaint and stencils
    text(k, '07', kn.x, kn.y - 1.12 * S, kn.z - 0.15 * S, 0.9, 'crimson', face='y-', maxw=1.4)
    k.stripes(ft.x - 0.95 * S, ft.x + 0.95 * S, 0.2, 0.75, ft.y - 1.776 * S, -1, 6)
    # collision: feet, shins, knees, the fist, the arm's lower part; the belly stays open between the legs
    colS(k, -4.6, -2.0, -5.6, -1.9, 0, 1.4)
    colS(k, -4.4, -2.3, -4.6, -2.2, 1.4, 8.2)
    colS(k, -4.0, -1.8, -2.2, 1.9, 6.4, 8.9)
    colS(k, 2.2, 4.4, -1.8, 6.0, 0, 2.2)
    colS(k, 2.0, 4.2, -1.4, 2.0, 2.2, 8.8)
    colS(k, -7.1, -4.9, -6.0, -3.8, 0, 2.2)
    colS(k, -7.2, -5.0, -4.0, -1.0, 2.2, 9.5)
    return k


def titan_upper(k):
    """The kneeling titan, upper part: the torso slumped forward over the yard (armour, a cracked reactor faintly
    glowing in the chest, back pack with exhaust stacks), pauldrons, the hanging head with its dead visor lenses, the
    torn right shoulder (cables hanging), beacons the salvage crew strapped on."""
    k.begin()
    k.push(0, P(0, 0.2, 0).y, 0, 8.4 * S)
    k.m.parent = k.m.parent @ Matrix.Rotation(math.radians(-22), 4, 'X')   # slumped forward (top toward -Y)
    k._sync()
    T = lambda x, y, z: V((x * S, y * S, z * S))
    slab3(k, 0, 0, [(0.0, 2.3 * S, 1.7 * S, 0, 0), (1.4 * S, 2.6 * S, 1.9 * S, 0, 0)], 'gun2', ch=0.5 * S)           # waist
    slab3(k, 0, 0, [(1.3 * S, 3.4 * S, 2.3 * S, 0, 0), (3.6 * S, 4.6 * S, 2.8 * S, 0, -0.1 * S), (6.0 * S, 4.0 * S, 2.5 * S, 0, 0.1 * S)], 'olive', ch=1.1 * S)
    # chest plates and the reactor housing, cracked, glowing faintly
    for sx in (-1, 1):
        x0, x1 = srt(sx * 0.9 * S, sx * 3.6 * S)
        k.hullp([(x0, -2.45 * S, 1.6 * S), (x1, -2.3 * S, 1.6 * S), (x0, -3.0 * S, 3.8 * S), (x1, -2.8 * S, 3.8 * S), (x0, -2.6 * S, 5.6 * S), (x1, -2.4 * S, 5.6 * S),
                 (x0, -2.0 * S, 1.6 * S), (x1, -1.9 * S, 1.6 * S), (x0, -2.5 * S, 3.8 * S), (x1, -2.3 * S, 3.8 * S), (x0, -2.1 * S, 5.6 * S), (x1, -2.0 * S, 5.6 * S)], 'bone')
    k.cyl(0, -2.6 * S, 3.6 * S, 1.05 * S, 1.05 * S, 0.9 * S, 'steelDark', seg=12, rot=(90, 0, 0))
    k.g.cyl(0, -3.502 * S, 3.6 * S, 0.72 * S, 0.72 * S, 0.004, 'cyanD', seg=12, rot=(90, 0, 0), ink=False)
    k.g.cyl(0, -3.506 * S, 3.6 * S, 0.34 * S, 0.34 * S, 0.004, 'cyan', seg=10, rot=(90, 0, 0), ink=False)
    k.poly([(-0.5 * S, -3.51 * S, 3.2 * S), (0.1 * S, -3.51 * S, 4.4 * S), (0.0 * S, -3.51 * S, 3.7 * S), (0.6 * S, -3.51 * S, 4.1 * S)], 'ink', (0, -1, 0))
    text(k, 'TX-07', -2.2 * S, -2.92 * S, 4.3 * S, 0.7, 'crimson', face='y-', maxw=2.4)
    # back pack, exhaust stacks
    slab3(k, 0, 2.6 * S, [(1.8 * S, 2.6 * S, 0.7 * S, 0, 0), (5.4 * S, 3.0 * S, 0.9 * S, 0, 0.2 * S)], 'gun2', ch=0.4 * S)
    for i, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
        k.cyl(x * S, 3.5 * S, 3.6 * S, 0.34 * S, 0.34 * S, (3.4 + 0.4 * (i % 2)) * S, 'steelDark', seg=8)
    # pauldrons: the left whole, the right torn (its arm lies in the yard)
    slab3(k, -5.3 * S, 0.1 * S, [(4.6 * S, 1.5 * S, 2.2 * S, 0, 0), (6.4 * S, 1.9 * S, 2.5 * S, -0.1 * S, 0), (7.4 * S, 1.3 * S, 1.9 * S, 0.1 * S, 0.1 * S)], 'crimson', ch=0.6 * S)
    drumx(k, -4.6 * S, 0.1 * S, 5.2 * S, 1.1 * S, 1.6 * S, 'gun2', seg=12)
    drumx(k, 4.4 * S, 0.1 * S, 5.2 * S, 1.0 * S, 1.2 * S, 'steelDark', seg=12)
    k.cyl(5.005 * S, 0.1 * S, 5.2 * S, 0.7 * S, 0.7 * S, 0.004, 'rust2', seg=10, rot=(0, 90, 0), ink=False)
    for i, (dy, c, L) in enumerate(((-0.4, 'cable', 3.4), (0.2, 'crimson2', 4.4), (0.55, 'hazard', 2.6), (-0.05, 'cable', 5.2))):
        k.beam((5.0 * S, dy * S, 5.0 * S), (5.25 * S, (dy - 0.3) * S, (5.0 - L) * S), 0.09 * S, c, ink=False)
    k.beacon(-5.0 * S, -0.6 * S, 7.4 * S, r=0.2)
    k.beacon(2.6 * S, 2.8 * S, 6.2 * S, r=0.2)
    # neck and the head hanging forward: a wedge helmet, the visor band with three dead lenses, crest, antenna stub
    k.push(0, -0.9 * S, 0, 6.0 * S)
    k.m.parent = k.m.parent @ Matrix.Rotation(math.radians(-38), 4, 'X')
    k._sync()
    drumx(k, 0.0, 0.3 * S, 0.3 * S, 0.8 * S, 1.6 * S, 'steelDark', seg=10)
    slab3(k, 0, 0, [(0.4 * S, 1.6 * S, 1.6 * S, 0, 0.2 * S), (1.6 * S, 1.75 * S, 1.65 * S, 0, 0.0), (2.6 * S, 1.2 * S, 1.2 * S, 0, 0.35 * S)], 'bone', ch=0.45 * S)
    k.bx(-1.45 * S, 1.45 * S, -1.75 * S, -1.4 * S, 0.95 * S, 1.55 * S, 'steelDark')
    for i, x in enumerate((-0.85, 0.0, 0.85)):
        lens(k, x * S, -1.72 * S + 0.25 * S * 0, 1.25 * S, 0.24 * S, crack=(i == 2))
    slab(k, 0, 0.4 * S, 2.5 * S, 3.2 * S, 0.12 * S, 1.1 * S, 0.06 * S, 0.7 * S, 'crimson', dy=0.25 * S)
    k.beam((1.0 * S, 0.9 * S, 2.3 * S), (1.15 * S, 1.3 * S, 3.4 * S), 0.09 * S, 'steelDark')
    k.pop()
    k.pop()
    k._sync()
    return k


# ================================================================ the fallen torso [18, 10] (walk-through)
def torso(k):
    """A titan torso lying on its side, its spine along x: the chest plates stand as the south wall, the back pack and
    exhaust stacks as the north wall, its flank plating as the roof with a blast hole; walk in at the torn waist (-x),
    past the cracked reactor (glowing) and the hanging cables, out through the neck collar (+x)."""
    k.begin()
    X0, X1, YI, YO, ZT = -7.4, 7.2, 2.25, 3.2, 6.6
    for s in (-1, 1):   # side walls: chest plates (south) / back plating (north), bulging armour slabs with seams
        y0, y1 = srt(s * YI, s * YO)
        for i, (xa, xb) in enumerate(((X0, -3.0), (-3.0, 1.6), (1.6, X1))):
            yo = s * (YO + 0.45)          # the outer face bulges out at mid height
            yi = s * YI
            k.hullp([(xa, yi, 0.0), (xb, yi, 0.0), (xa, s * YO, 0.0), (xb, s * YO, 0.0),
                     (xa + 0.15, yo, 3.0), (xb - 0.15, yo, 3.0), (xa + 0.1, yi, 3.0), (xb - 0.1, yi, 3.0),
                     (xa + 0.3, s * (YO - 0.1), ZT), (xb - 0.3, s * (YO - 0.1), ZT), (xa + 0.3, yi, ZT), (xb - 0.3, yi, ZT)],
                    lambda f, s=s: ('bone' if s < 0 else 'olive') if f.normal.y * s > 0.35 else ('bone2' if s < 0 else 'olive2') if abs(f.normal.y) > 0.35 else 'gun2')
    # the chest's reactor port on the outside of the south wall (its glow seen through the crack), the neck collar
    k.cyl(-0.4, -(YO + 0.45), 3.0, 1.2, 1.2, 0.35, 'steelDark', seg=10, rot=(90, 0, 0))
    k.g.cyl(-0.4, -(YO + 0.802), 3.0, 0.7, 0.7, 0.004, 'cyanD', seg=10, rot=(90, 0, 0), ink=False)
    k.poly([(-0.9, -(YO + 0.81), 2.6), (-0.2, -(YO + 0.81), 3.6), (-0.35, -(YO + 0.81), 3.0), (0.2, -(YO + 0.81), 3.3)], 'ink', (0, -1, 0))
    # the neck: a stub of vertebra blocks over the doorway, its cables hanging
    for j, (xa, xb) in enumerate(((X1 + 0.93, X1 + 1.6), (X1 + 1.7, X1 + 2.3))):
        slab(k, (xa + xb) / 2, 0.0, 3.9 + 0.1 * j, 5.3 - 0.2 * j, (xb - xa) / 2, 1.5 - 0.2 * j, (xb - xa) / 2 - 0.05, 1.2 - 0.2 * j, 'gun2' if j else 'steelDark', ch=0.25)
    for i, (dy, c) in enumerate(((-0.8, 'cable'), (0.5, 'crimson2'), (1.0, 'hazard'))):
        cable(k, (X1 + 1.2 + 0.4 * i, dy, 4.0), (X1 + 1.9 + 0.3 * i, dy * 1.3, 0.04), 0.2, 0.07, c=c, n=4)
    drumx(k, 4.0, 0.0, ZT + 0.7, 1.5, 1.0, 'gun2', seg=12)
    # the roof: flank armour lying flat, a blast hole in the middle third (moonlight falls in)
    for (xa, xb) in ((X0 - 0.2, -2.0), (1.4, X1 + 0.2)):
        slab(k, (xa + xb) / 2, 0.0, ZT - 0.3, ZT + 0.5, (xb - xa) / 2, YO + 0.2, (xb - xa) / 2 - 0.3, YO - 0.2, 'olive', ch=0.4)
    for s in (-1, 1):
        slab(k, -0.3, s * 2.55, ZT - 0.26, ZT + 0.45, 1.75, 0.75, 1.5, 0.6, 'olive', ch=0.25)
    for i in range(5):   # torn plate edges round the hole
        a = i / 5 * math.pi * 2
        tbox(k, -0.3 + math.cos(a) * 1.5, math.sin(a) * 1.3, ZT + 0.5, 0.9, 0.6, 0.1, 'olive2', yaw=math.degrees(a), pitch=25)
    # the pauldron mound on top at the shoulder end, exhaust stacks lying along the north wall
    slab3(k, 4.6, 0.3, [(ZT + 1.1, 2.6, 2.9, 0, 0), (ZT + 2.4, 2.4, 2.6, 0.1, 0), (ZT + 3.2, 1.5, 1.8, 0.2, 0.1)], 'crimson', ch=0.8)
    for i, z in enumerate((1.6, 3.0, 4.4)):
        drumx(k, -1.0 + i * 0.6, YO + 0.42, z, 0.36, 7.5 - i, 'steelDark', seg=8)
    # inside: rib frames on the walls and under the roof every 2.4 m, cables hanging, the reactor against the south wall
    for x in (-5.6, -3.2, -0.8, 1.6, 4.0, 6.2):
        for s in (-1, 1):
            k.bx(x - 0.18, x + 0.18, *srt(s * (YI - 0.35), s * YI), 0.0, ZT - 0.35, 'gun')
        k.bx(x - 0.16, x + 0.16, -YI + 0.01, YI - 0.01, ZT - 0.65, ZT - 0.3, 'gun')
    for i, (x, y, L, c) in enumerate(((-4.3, 0.8, 2.6, 'cable'), (-2.0, -1.2, 3.4, 'crimson2'), (2.8, 1.1, 2.2, 'hazard'), (5.0, -0.6, 3.0, 'cable'))):
        k.beam((x, y, ZT - 0.3), (x + 0.2, y - 0.1, ZT - 0.3 - L), 0.08, c, ink=False)
    k.push(-0.4, -1.3, 90, 0)
    reactor_core(k, V((0.0, 0.0, 1.35)), 1.1, 2.4, axis='y')
    k.pop()
    k.bx(-1.9, 1.1, -2.2, -1.95, 0.0, 0.6, 'steelDark')
    pool_disc(k, -0.4, -0.2, Z['blue'], 1.8, 41, c1='poolB', c2='cyanD')
    # the torn waist (-x): the spine stub, the jagged ring, cables spilling out; the neck collar (+x)
    drumx(k, X0 - 0.4, 2.0, 0.9, 0.85, 0.8, 'steelDark', seg=10)
    for i, (dy, c) in enumerate(((-1.4, 'cable'), (0.4, 'crimson2'), (1.4, 'hazard'))):
        cable(k, (X0 + 0.2, dy, 2.0 + i * 0.8), (X0 - 1.2, dy * 1.1, 0.03), 0.4, 0.07, c=c, n=4)
    for s in (-1, 1):
        k.bx(*srt(X1 - 0.2, X1 + 0.9), *srt(s * 1.6, s * YO), 0.0, 4.6, 'gun2')
    k.bx(X1 - 0.17, X1 + 0.93, -YO + 0.03, YO - 0.03, 3.8, ZT, 'gun2')
    k.stripes(-6.6, -3.4, 0.2, 0.7, -YO - 0.004, -1, 8)
    text(k, 'TX-12', 3.6, -YO - 0.25 * 0.3 - 0.01, 3.4, 0.9, 'crimson', face='y-', maxw=3.0)
    # collision: the two walls, the neck collar's cheeks, the reactor
    k.col(X0, X1 + 0.9, -YO - 0.6, -YI - 0.06, 0, ZT)
    k.col(X0, X1 + 0.9, YI + 0.03, YO + 0.8, 0, ZT)
    k.col(X1 - 0.2, X1 + 0.9, -YO, -1.6, 0, ZT)
    k.col(X1 - 0.2, X1 + 0.9, 1.6, YO, 0, ZT)
    k.col(-1.65, 0.85, -2.25, -0.25, 0, 2.45)
    return k


# ================================================================ the giant head [10, 10]
def head(k):
    """An enormous titan head lying on its cheek: the armoured helmet, the visor recess with three dead eye lenses,
    the jaw guard, a crest, side sensor pods, the torn neck with cables, rust and a painted number."""
    k.begin()
    k.push(0.2, 0.0, 14, 0)
    k.m.parent = k.m.parent @ Matrix.Translation((0, 0, 0.5)) @ Matrix.Rotation(math.radians(16), 4, 'Y')
    k._sync()
    slab3(k, 0, 0.3, [(-0.5, 3.0, 2.6, 0, 0.2), (1.8, 3.3, 2.9, 0, 0.0), (3.8, 2.8, 2.5, 0, 0.2), (4.8, 1.9, 1.8, 0, 0.5)], 'bone', ch=0.9)
    k.bx(-2.8, 2.8, -2.95, -2.4, 1.2, 2.6, 'steelDark')                 # visor recess
    for i, x in enumerate((-1.75, 0.0, 1.75)):
        lens(k, x, -2.95, 1.9, 0.55, crack=(i == 0))
    slab3(k, 0, -1.9, [(-0.44, 2.2, 0.9, 0, 0), (0.9, 2.5, 1.1, 0, -0.2)], 'gun2', ch=0.35)   # jaw guard
    for x in (-1.6, -0.5, 0.5, 1.6):
        k.qy(x - 0.2, x + 0.2, -0.2, 0.6, -3.05, -1, 'steelDark')
    slab(k, 0, 0.6, 4.4, 5.6, 0.25, 2.2, 0.12, 1.5, 'crimson', dy=0.4)         # crest
    for sx in (-1, 1):
        x0, x1 = srt(sx * 3.1, sx * 3.9)
        k.bx(x0, x1, -1.2, 1.0, 1.0, 2.6, 'gun2')                              # sensor pods
        k.qx(-0.9, 0.7, 1.7, 1.95, sx * 3.903, sx, 'crimson')
    k.beam((2.2, 1.2, 4.4), (2.6, 2.2, 6.0), 0.14, 'steelDark')               # antenna (broken)
    drumy(k, 0, 3.0, 1.2, 1.6, 1.0, 'steelDark', seg=12)                      # neck ring
    k.cyl(0, 4.004, 1.2, 1.2, 1.2, 0.004, 'rust2', seg=10, rot=(-90, 0, 0), ink=False)
    for i, (dx, c) in enumerate(((-0.6, 'cable'), (0.3, 'crimson2'), (0.8, 'hazard'))):
        cable(k, (dx, 3.9, 1.4 + 0.2 * i), (dx * 1.6, 4.9, -0.45), 0.25, 0.08, c=c, n=3)
    text(k, '07', -2.0, -2.62, 3.4, 0.8, 'crimson', face='y-', maxw=1.4)
    k.pop()
    k._sync()
    k.col(-3.9, 3.9, -3.3, 3.4, 0, 5.6)
    return k


# ================================================================ the ribcage with the plating ramps [18, 12]
RIBS = (-6.6, -3.9, -1.2, 1.5, 4.2, 6.9)


def rib_pts(x, n=6):
    """A rib arch from the spine (y +4.4, z 1.0) up over the walkway to its tip near the ground (y -5.2)."""
    out = []
    for i in range(n + 1):
        t = i / n
        a = math.pi * (0.08 + 0.84 * t)
        y = -0.4 + 4.8 * math.cos(a)
        z = 0.9 + 8.0 * math.sin(a) * (1.0 - 0.18 * t)
        out.append(V((x, y, z if i < n else 0.6)))
    return out


def ribs(k):
    """A titan chest frame lying on its back: the segmented spine along x, six rib arches over the yard, and the
    salvage crew's plating ramps between them: up from the west to a deck at 3.0 m, then on to the top deck at 5.4 m
    (rails, trestles); a reactor still faintly glowing in the cavity."""
    k.begin()
    for i in range(6):   # the spine: vertebra blocks and discs
        x = -7.8 + i * 3.0
        slab(k, x + 1.0, 4.6, 0.0, 1.6, 1.15, 0.85, 1.0, 0.7, 'gun2', ch=0.3)
        drumx(k, x + 2.5, 4.6, 0.9, 0.6, 0.6, 'steelDark', seg=8)
    for j, x in enumerate(RIBS):
        pts = rib_pts(x)
        for a, b in zip(pts, pts[1:]):
            oslab(k, a, b, 0.32, 0.38, 0.28, 0.32, 'bone' if j % 2 else 'bone2', ch=0.08)
        drumx(k, x, pts[0].y, pts[0].z, 0.5, 0.9, 'gun', seg=8)
    # the reactor in the cavity
    reactor_core(k, V((-4.6, 2.2, 1.3)), 1.0, 2.2, axis='z')
    pool_disc(k, -4.6, 2.2, Z['blue'], 2.2, 51, c1='poolB', c2='cyanD')
    # walkway: ramp 1 (x -8.6 -> -3.6, 0 -> 3.0), deck 1 (-3.6 .. 0.6), ramp 2 (0.6 -> 4.6, 3.0 -> 5.4), top deck (4.6 .. 8.6)
    Y0, Y1 = -1.6, 0.8
    plate_ramp(k, -8.6, -3.6, Y0, Y1, 0.0, 3.0, 10)
    deck(k, -3.6, 0.6, Y0, Y1, 3.0, t=0.14, grate=True)
    plate_ramp(k, 0.6, 4.6, Y0, Y1, 3.0, 5.4, 8, c="bone", c2="bone2")
    deck(k, 4.6, 8.6, Y0, Y1, 5.4, t=0.14, grate=True)
    rail_x(k, -3.6, 0.6, Y0 + 0.05, 3.0, post=1.4)
    rail_x(k, -3.6, 0.6, Y1 - 0.05, 3.0, post=1.4)
    rail_x(k, 4.6, 8.55, Y0 + 0.05, 5.4, post=1.3)
    rail_x(k, 4.6, 8.55, Y1 - 0.05, 5.4, post=1.3)
    rail_y(k, Y0 + 0.05, Y1 - 0.05, 8.55, 5.4, post=1.2)
    for (x, z) in ((-3.5, 3.0), (0.5, 3.0), (4.7, 5.4), (8.5, 5.4)):   # trestles
        for y in (Y0 + 0.12, Y1 - 0.12):
            k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, z - 0.14, 'hazard')
            k.col(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, z - 0.14)
        k.beam((x, Y0 + 0.12, 0.3), (x, Y1 - 0.12, z - 0.4), 0.06, 'hazard', ink=False)
    sodium_head(k, 8.2, Y1 - 0.2, 6.6, s=-1, w=0.5, h=0.3)
    k.bx(8.15, 8.25, Y1 - 0.2, Y1 - 0.1, 5.4, 6.4, 'steelDark')
    k.beacon(8.2, Y1 - 0.15, 6.4, r=0.13)
    # collision: spine, rib feet on both sides, the reactor
    k.col(-8.4, 8.4, 3.75, 5.45, 0, 1.6)
    for x in RIBS:
        pts = rib_pts(x)
        k.col(x - 0.36, x + 0.36, pts[-1].y - 0.3, pts[-1].y + 0.7, 0, 2.4)
        k.col(x - 0.36, x + 0.36, pts[0].y - 0.6, pts[0].y + 0.4, 0, 2.6)
    k.col(-5.6, -3.6, 1.2, 3.2, 0, 2.5)
    return k


# ================================================================ the broken cannon [20, 4]
def cannon(k):
    """A colossal cannon broken off its mount: the breech block with its capacitor bank (faint cyan), the recoil
    cylinders, the barrel snapped at its middle and the muzzle half lying askew, dug in."""
    k.begin()
    k.bx(-9.6, -6.2, -1.6, 1.6, 0.0, 3.0, 'gun2')
    k.stripes(-9.4, -6.4, 0.2, 0.7, -1.603, -1, 8)
    for j in range(3):
        k.bx(-9.3 + j * 1.0, -8.6 + j * 1.0, -1.66, -1.6, 1.2, 2.4, 'steelDark')
        k.g.qy(-9.2 + j * 1.0, -8.7 + j * 1.0, 1.35, 2.25, -1.663, -1, 'cyanD')
        k.g.qy(-9.2 + j * 1.0, -8.7 + j * 1.0, 1.9, 2.05, -1.666, -1, 'cyan')
    text(k, 'TX-12', -7.6, -1.605, 2.45, 0.38, 'bone', face='y-', maxw=2.0)
    drumx(k, -5.4, 0.0, 1.5, 1.45, 1.6, 'steelDark', seg=14)
    tube(k, V((-4.6, 0.0, 1.5)), V((2.6, 0.0, 1.3)), 1.15, 'gun', seg=12, r2=1.0)
    for s in (-1, 1):
        drumx(k, -2.2, s * 1.2, 2.2, 0.32, 4.4, 'chrome', seg=8)
        drumx(k, -3.4, s * 1.2, 2.2, 0.42, 1.6, 'steelDark', seg=8)
    k.cyl(2.602, 0.0, 1.3, 0.7, 0.7, 0.004, 'rust2', seg=10, rot=(0, 90, 0), ink=False)
    k.push(6.6, 0.4, -12, 0)
    k.m.parent = k.m.parent @ Matrix.Rotation(math.radians(-5), 4, 'Y')
    k._sync()
    tube(k, V((-3.4, 0.0, 1.1)), V((2.2, 0.0, 0.9)), 0.98, 'gun', seg=12, r2=0.92)
    drumx(k, 2.8, 0.0, 0.9, 1.15, 1.2, 'steelDark', seg=12)
    for s in (-1, 1):
        k.bx(2.4, 3.2, *srt(s * 1.15, s * 1.35), 0.4, 1.4, 'gun2')
    k.cyl(-3.402, 0.0, 1.1, 0.7, 0.7, 0.004, 'rust2', seg=10, rot=(0, -90, 0), ink=False)
    k.pop()
    k._sync()
    heap(k, 3.4, 0.6, 1.4, 1.2, 0.8, 61, n=7, top=2, fn=lambda f: 'dirt2' if f.normal.z < 0.6 else 'dirt')
    k.col(-9.6, -4.6, -1.6, 1.6, 0, 3.0)
    k.col(-4.6, 2.6, -1.2, 1.2, 0, 2.6)
    k.col(3.0, 9.8, -1.2, 1.9, 0, 2.1)
    return k


# ================================================================ reactor cores [4, 4]
def reactor(k, cracked=False):
    """A dead reactor core [4, 4]: A stands in its cradle (coolant pipes, the window band still glowing faintly, a
    warning board, a beacon); B lies split open on its side, its core shards glowing, a cold blue pool round it."""
    k.begin()
    if not cracked:
        k.bx(-1.7, 1.7, -1.7, 1.7, 0, 0.4, 'conc2')
        for (x, y) in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)):
            k.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.4, 1.6, 'hazard')
        reactor_core(k, V((0.0, 0.0, 2.0)), 1.2, 3.0, axis='z')
        k.cyl(0, 0, 3.5, 0.9, 0.5, 0.5, 'steelDark', seg=10)
        for s in (-1, 1):
            tube(k, V((s * 1.15, 0.4, 2.6)), V((s * 1.7, 1.2, 0.4)), 0.18, 'steel', seg=6)
        sign_board(k, 0.0, -1.73, 0.55, 1.4, 0.7, [('CORE 4', 0.2, None), ('DO NOT OPEN', 0.13, 'crimson2')])
        k.beacon(0.0, 0.0, 4.0, r=0.16)
        pool_disc(k, 0.0, 0.0, Z['blue'], 2.0, 71, c1='poolB', c2='cyanD')
        D.reactor_detail(k)
        k.col(-1.7, 1.7, -1.7, 1.7, 0, 0.4)
        k.col(-1.3, 1.3, -1.3, 1.3, 0.4, 3.6)
        return k
    k.push(0, 0, 25, 0)
    for s in (-1, 1):   # the two shell halves
        k.push(0, s * 0.35, 0, 0)
        k.m.parent = k.m.parent @ Matrix.Rotation(math.radians(s * 14), 4, 'X')
        k._sync()
        pts = []
        for i in range(7):
            a = math.pi * i / 6
            for x in ((-1.5, 1.5) if s < 0 else (-1.44, 1.44)):
                pts.append((x, s * math.sin(a) * 1.1, 1.1 - math.cos(a) * 1.1))
        k.hullp(pts, lambda f: 'gun2' if f.normal.y * s > 0.3 else 'steelDark')
        k.pop()
        k._sync()
    for i in range(5):
        a = i * 1.3
        k.ghull([(math.cos(a) * 0.5 - 0.15, math.sin(a) * 0.3 - 0.12, 0.0), (math.cos(a) * 0.5 + 0.15, math.sin(a) * 0.3, 0.0),
                 (math.cos(a) * 0.5, math.sin(a) * 0.3 + 0.14, 0.0), (math.cos(a) * 0.7, math.sin(a) * 0.4, 0.7 + 0.25 * (i % 3))], 'cyan')
    k.pop()
    k._sync()
    pool_disc(k, 0.0, 0.0, Z['blue'], 2.0, 73, c1='poolB', c2='cyanD')
    k.col(-1.5, 1.5, -1.5, 1.5, 0, 2.0)
    return k


# ================================================================ salvage scaffold [12, 4]
def scaffold(k):
    """The salvage crew's scaffold [12, 4]: tube posts, a stair from the east up to the 3.0 m deck, a second flight
    back west to the 6.0 m deck, toe boards, rails, a floodlight and a beacon on top."""
    k.begin()
    Ya, Yb, Yc = -1.95, -0.65, 0.65   # front row (stair 1 + deck 3), back row (stair 2 + deck 6) up to 1.95
    stairs_x(k, 5.9, 0.9, Ya, Yb - 0.02, 0.0, 3.0, 10, rails=(True, False))
    deck(k, -5.9, 0.9, Ya, Yb, 3.0, t=0.12, grate=True)
    deck(k, -5.9, -4.6, Yb + 0.02, 1.95, 3.0, t=0.12, grate=True)
    stairs_x(k, -4.6, 0.4, Yc - 0.6, 1.86, 3.0, 6.0, 10, rails=(True, True))
    deck(k, 0.4, 5.9, Yc - 0.6, 1.95, 6.0, t=0.12, grate=True)
    rail_x(k, -5.9, 0.9, Ya + 0.05, 3.0, post=1.5)
    rail_y(k, Ya + 0.05, 1.9, -5.85, 3.0, post=1.5)
    rail_x(k, 0.4, 5.79, 1.9, 6.0, post=1.4)
    rail_x(k, 0.4, 5.79, Yc - 0.55, 6.0, post=1.4)
    rail_y(k, Yc - 0.55, 1.9, 5.85, 6.0, post=1.3)
    for (x, y, top) in ((-5.8, Ya + 0.1, 3.0), (-5.8, Yb - 0.1, 3.0), (0.8, Ya + 0.1, 3.0), (0.8, Yb - 0.1, 3.0), (-5.8, 1.85, 3.0),
                        (0.55, Yc - 0.5, 6.0), (0.55, 1.86, 6.0), (5.8, Yc - 0.5, 6.0), (5.8, 1.86, 6.0)):   # scaffold tubes
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, top - 0.12, 'steel')
        k.col(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, top - 0.12)
    for (x, ya, yb, z1) in ((-5.8, Ya + 0.1, Yb - 0.1, 2.7), (0.8, Ya + 0.1, Yb - 0.1, 2.7), (0.55, Yc - 0.5, 1.86, 5.6), (5.8, Yc - 0.5, 1.86, 5.6)):
        k.beam((x, ya, 0.3), (x, yb, z1), 0.05, 'steel', ink=False)
    sodium_head(k, 5.5, 2.0, 7.2, s=-1, w=0.5, h=0.3)
    k.bx(5.45, 5.55, 2.0, 2.1, 5.4, 7.05, 'steelDark')
    k.beacon(1.5, 2.05, 7.1, r=0.13)
    k.bx(1.45, 1.55, 2.0, 2.1, 5.4, 7.1, 'steelDark')
    D.scaffold_detail(k)
    return k


# ================================================================ smaller wrecks
def arm(k):
    """The kneeling titan's torn-off right arm [12, 4]: the shoulder joint under its pauldron, the upper arm, the elbow
    and the cannon forearm with three barrels, lying along x (3.2 m at the pauldron)."""
    k.begin()
    slab3(k, -4.6, 0.0, [(0.0, 1.5, 1.8, 0, 0), (2.2, 1.7, 1.9, 0, 0), (3.2, 1.2, 1.4, 0.2, 0)], 'crimson', ch=0.55)
    drumy(k, -4.6, 0.0, 1.5, 1.05, 2.2, 'gun2', seg=12)
    oslab(k, (-3.4, 0.0, 1.2), (-0.4, 0.1, 1.1), 0.95, 0.9, 0.85, 0.85, 'olive', ch=0.28)
    drumy(k, 0.0, 0.0, 1.05, 0.95, 1.7, 'gun2', seg=12)
    k.bx(0.6, 2.8, -0.95, 0.95, 0.0, 1.9, 'gun2')
    k.stripes(0.8, 2.6, 0.3, 0.7, -0.953, -1, 6)
    for i, (y, z) in enumerate(((-0.45, 0.6), (0.45, 0.6), (0.0, 1.35))):
        drumx(k, 4.6, y, z, 0.32, 3.6, 'gun', seg=8)
    for x in (3.2, 5.4):
        k.bx(x - 0.15, x + 0.15, -0.85, 0.85, 0.15, 1.75, 'steelDark')
    for i, (dy, c) in enumerate(((-0.6, 'cable'), (0.5, 'crimson2'))):
        cable(k, (-5.6, dy, 1.6), (-6.0, dy * 1.4, 0.03), 0.2, 0.08, c=c, n=3)
    k.col(-5.8, -1.0, -1.9, 1.9, 0, 3.2)
    k.col(-1.0, 2.8, -0.95, 0.95, 0, 1.9)
    k.col(2.8, 6.4, -0.85, 0.85, 0, 1.75)
    D.arm_detail(k)
    return k


def plates(k, seed):
    """Armour plates of a dead machine stuck in the ground [3, 1], leaning (2.4 m and 1.5 m), stencilled."""
    k.begin()
    rnd = random.Random(seed)
    c1, c2 = ('bone', 'olive') if seed % 2 else ('navy', 'crimson')
    plate(k, (-0.75, 0.0, -0.3), (-0.55, -0.2, 2.4), 1.35, 0.22, c1, up=(0, -1, 0.1))
    plate(k, (0.8, 0.05, -0.2), (1.0, 0.25, 1.5), 1.1, 0.18, c2, up=(0.1, -1, -0.12))
    k.col(-1.45, 1.55, -0.45, 0.45, 0, 1.5)
    return k


def beacon_post(k):
    """A warning post: a steel post on a footing with a red blinking beacon and a DANGER plate."""
    k.begin()
    k.cyl(0, 0, 0, 0.32, 0.32, 0.25, 'conc', seg=8)
    k.bx(-0.06, 0.06, -0.06, 0.06, 0.25, 2.6, 'hazard')
    for z in (0.6, 1.2, 1.8):
        k.bx(-0.065, 0.065, -0.065, 0.065, z, z + 0.25, 'ink', ink=False)
    k.beacon(0.0, 0.0, 2.6, r=0.17)
    sign_board(k, 0.0, -0.07, 1.4, 0.55, 0.38, [('DANGER', 0.13, 'crimson2')], rim=None)
    D.beacon_post_detail(k)
    k.col(-0.32, 0.32, -0.32, 0.32, 0, 2.6)
    return k


# ================================================================ the far backdrop (fogged, no collision)
def bd_heap(k, seed):
    """A far scrap mountain (25 x 12 m, 9 m tall before scaling): a few big facets in the night colours."""
    k.begin()
    rnd = random.Random(seed)
    fn = lambda f: 'far2' if f.normal.z > 0.55 else 'far'
    k.hullp(rock_pts(rnd, (0, 0), 12.0, 5.5, 9.0, n=8, top=3), fn)
    k.hullp(rock_pts(rnd, (rnd.uniform(-7, 7), rnd.uniform(-1, 1)), 6.0, 3.5, 12.0, n=6, top=2), fn)
    return k


def bd_titan(k):
    """A dead titan standing far off: a slumped silhouette (legs, torso, head bowed, one arm hanging), 30 m."""
    k.begin()
    for sx in (-1, 1):
        oslab(k, (sx * 3.0, 0, 0), (sx * 3.2, 0.5, 12.0), 1.4, 1.6, 1.2, 1.4, 'far')
    slab3(k, 0, 0.5, [(12.0, 3.6, 2.0, 0, 0), (16.0, 5.0, 2.6, 0, -0.6), (21.0, 4.4, 2.4, 0, -1.4)], 'far2', ch=1.2)
    slab3(k, 0, -2.0, [(19.0, 1.6, 1.4, 0, 0), (21.5, 1.4, 1.2, 0, -0.4)], 'far', ch=0.4)
    oslab(k, (-5.6, -0.8, 20.0), (-6.4, -1.6, 9.0), 1.2, 1.2, 1.0, 1.0, 'far')
    k.beacon(5.2, -0.8, 21.0, r=0.5)
    return k


def bd_crane(k):
    """A tower crane far off: lattice mast, jib and counter-jib, a red light at the top (blinks)."""
    k.begin()
    for (x, y) in ((-0.9, -0.9), (0.9, -0.9), (0.9, 0.9), (-0.9, 0.9)):
        k.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 34.0, 'far')
    for i in range(1, 9):
        z = i * 4.0
        k.bx(-0.9, 0.9, -0.95, -0.85, z, z + 0.3, 'far', ink=False)
        k.bx(-0.9, 0.9, 0.85, 0.95, z, z + 0.3, 'far', ink=False)
    k.bx(-1.2, 1.2, -1.2, 1.2, 34.0, 36.0, 'far2')
    k.bx(-30.0, 10.0, -0.6, 0.6, 36.02, 37.4, 'far')
    k.bx(4.0, 9.0, -1.0, 1.0, 34.6, 36.0, 'far2')
    k.beam((-0.4, 0, 38.0), (-22.0, 0, 37.5), 0.25, 'far', ink=False)
    k.beam((0.4, 0, 38.0), (8.0, 0, 37.5), 0.25, 'far', ink=False)
    k.bx(-0.3, 0.3, -0.3, 0.3, 36.0, 38.2, 'far')
    k.beacon(0.0, 0.0, 38.2, r=0.6)
    return k
