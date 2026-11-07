"""INKBOLT asset family: kit-factory (Robot Works: the enemy's robot assembly plant).

A tall steel-framed assembly hall: painted block dado, blue corrugated siding, a clerestory window band (open: the
dusk sky and the works outside show through), roof trusses with high-bay lamps; assembly lines building half-done
Crawlers, Gunners, Bombers and Drones under robot arms; conveyors of parts, crates and pallets, overhead catwalks,
hazard stripes, a giant press with a forge, a raised control booth, finished-robot racks and test cages.

Conventions (see src/data/themes.js and kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * Wall modules ('#') face Blender -Y (game +Z); the theme uses wall.facing = 'open' (the engine turns each straight
    module toward its open side; corners and notches get the all-round Corner column).
  * Walls reach WALL_H (10.4 m), above the ceiling (env.ceiling.height 10.0); the gate frame's infill wall reaches
    WALL_H too. Wall backs are exterior siding (seen through other zones' clerestory windows).
  * TrailWall: a service corridor (corridor to +X): block dado, pipes, half of a lowered ceiling with a continuous
    strip light at ROOF; the two sides meet in the middle, so the passage between halls is closed.
  * Floor decals sit at their own heights (Z table) so overlapping decals of different pieces never z-fight.
  * The half-built robots echo fam_bots.py (tin-can Crawler, wheelie-bin Gunner, bottle Bomber, soda-can Drone).
  * The belts move in the game (theme symbol option `conveyor`): Conveyor and the Line_* sections are static frames;
    the parts (Item_*), the half-built robots (LineBot_*) and the belt cleats are separate pieces the engine slides
    along each run, popping in and out inside the end hoods (Conveyor_Feed / _Exit, Line_Feed / _Exit).
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, rz, srt, rock_pts, clamp_pts, shutter_hull

FAM = 'kit-factory'
PFX = 'KIT_FACTORY_'
ib_lib.GLB[FAM] = 'fps-kit-factory.glb'
ib_lib.CFG[FAM] = (0.015, 0.02)
HULL_T = 0.02
CEIL = 10.0
WALL_H = 10.4
ROOF = 4.2          # service corridor ceiling
WIN0, WIN1 = 6.4, 9.0   # clerestory band

ib_lib.PALETTES[FAM] = BASE + [
    ('conc', '#B7B3AA'), ('conc2', '#9B978F'), ('block', '#CFC9BB'), ('blockLine', '#ADA697'),
    ('siding', '#5F80A0'), ('siding2', '#4E6C8A'), ('ext', '#C9B79A'),
    ('ext2', '#AD9C80'), ('roofEdge', '#3A3F48'), ('steel', '#9EA8B3'), ('steel2', '#77828F'),
    ('steelDark', '#3E4550'), ('beam', '#D0612E'), ('beam2', '#A54A25'), ('hazard', '#F2C230'),
    ('hazard2', '#C99A1E'), ('mullion', '#2F353D'), ('glint', '#EAF6FF'), ('lamp', '#FFF3C4'),
    ('lampWarm', '#FFD66B'), ('pool', '#C4BDAE'), ('pool2', '#D3CCBC'), ('hot', '#FF6A2A'),
    ('hot2', '#FFC24A'), ('brick', '#A9553E'), ('brick2', '#86412F'), ('soot', '#37323A'),
    ('tin', '#D1D6DC'), ('tin2', '#B4BAC3'), ('rust', '#DE7650'), ('core', '#FFC23A'),
    ('bin', '#64AD79'), ('bin2', '#4F9466'), ('rubber', '#3A3844'), ('glassB', '#5797E0'),
    ('glassB2', '#3F7FC6'), ('can', '#E65A50'), ('alu', '#CDD3DA'),
    ('label', '#FFF7E6'), ('crate', '#C99A62'), ('crate2', '#A57A48'),
    ('arm', '#EC7A2E'), ('arm2', '#C25E1E'), ('screen', '#7FD6E8'), ('screen2', '#B6F0D8'),
    ('panel', '#D7DBE0'), ('panelG', '#8E96A0'), ('grate', '#4B525D'), ('curtain', '#C8423A'),
    ('cyl', '#3E7D5A'), ('ceil', '#8E9097'), ('far', '#8C7F86'),
    ('far2', '#6F6470'), ('farLit', '#F4C27A'), ('smoke', '#E9E1DA'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64

Z = {'pool': 0.016, 'hazard': 0.026, 'walk': 0.034, 'test': 0.042, 'pressPool': 0.05, 'furnace': 0.058,
     'booth': 0.066, 'line': 0.074, 'arm': 0.082, 'hatch': 0.09}


# ================================================================ half-built robots (fam_bots shapes, simplified)
def crawler(k, x, y, z, legs=2, top=True, s=1.0, deg=0):
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0.3, 0.32, 0.31, 0.42, 'tin', seg=8)
    k.cyl(0, 0, 0.42, 0.335, 0.335, 0.12, 'rust', seg=8, caps=False, ink=False)
    if top:
        k.cyl(0, 0, 0.72, 0.35, 0.35, 0.05, 'tin2', seg=8)
        k.cyl(0, 0, 0.77, 0.15, 0.15, 0.03, 'core', seg=8, ink=False)
    k.bx(-0.17, 0.17, -0.345, -0.3, 0.56, 0.63, 'ink', ink=False)
    for i in range(legs):
        a = math.radians(45 + 90 * i)
        lx, ly = math.cos(a) * 0.24, math.sin(a) * 0.24
        k.bx(lx - 0.02, lx + 0.02, ly - 0.02, ly + 0.02, 0.03, 0.31, 'steelDark', ink=False)
        k.cyl(lx, ly, 0.0, 0.08, 0.07, 0.05, 'steelDark', seg=5, ink=False)
    k.pop()


def gunner(k, x, y, z, lid=False, gun=True, s=1.0, deg=0):
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0.0, 0.29 * 1.414, 0.33 * 1.414, 0.92, 'bin', seg=4, rot=(0, 0, 45))
    k.cyl(0, 0, 0.92, 0.335 * 1.414, 0.335 * 1.414, 0.06, 'bin2', seg=4, rot=(0, 0, 45))
    k.bx(-0.15, 0.15, -0.333, -0.31, 0.5, 0.7, 'label', ink=False)
    if lid:
        k.bx(-0.36, 0.36, -0.36, 0.36, 0.98, 1.04, 'bin2')
    if gun:
        k.cyl(0.36, -0.05, 0.62, 0.075, 0.075, 0.42, 'gunmetal', seg=8, rot=(90, 0, 0))
        k.cyl(0.36, -0.47, 0.62, 0.05, 0.05, 0.1, 'core', seg=8, rot=(90, 0, 0), ink=False)
    k.pop()


def bottle(k, x, y, z, cap=False, base=True, s=1.0):
    k.push(x, y, 0, z, s=s)
    if base:
        k.cyl(0, 0, 0.0, 0.26, 0.26, 0.22, 'rubber', seg=8)
    k.cyl(0, 0, 0.22, 0.22, 0.22, 0.42, 'glassB', seg=8)
    k.cyl(0, 0, 0.64, 0.22, 0.08, 0.22, 'glassB2', seg=8)
    k.cyl(0, 0, 0.32, 0.226, 0.226, 0.16, 'label', seg=8, caps=False, ink=False)
    k.cyl(0, 0, 0.86, 0.075, 0.075, 0.08, 'glassB2', seg=8)
    if cap:
        k.cyl(0, 0, 0.94, 0.09, 0.09, 0.08, 'red', seg=8)
    k.pop()


def drone(k, x, y, z, arms=2, s=1.0, deg=0):
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0.0, 0.19, 0.19, 0.55, 'can', seg=8)
    k.cyl(0, 0, 0.2, 0.196, 0.196, 0.12, 'alu', seg=8, caps=False, ink=False)
    k.cyl(0, 0, 0.55, 0.17, 0.12, 0.05, 'alu', seg=8)
    for i in range(arms):
        a = math.radians(45 + 90 * i)
        ca, sa = math.cos(a), math.sin(a)
        k.beam((ca * 0.15, sa * 0.15, 0.5), (ca * 0.5, sa * 0.5, 0.56), 0.04, 'gunmetal')
        k.cyl(ca * 0.5, sa * 0.5, 0.56, 0.05, 0.05, 0.06, 'gunmetal', seg=6, ink=False)
        k.bx(ca * 0.5 - 0.22, ca * 0.5 + 0.22, sa * 0.5 - 0.03, sa * 0.5 + 0.03, 0.62, 0.64, 'steelDark', ink=False)
    k.pop()


# ================================================================ wall modules
def siding_ribs(k, z0, z1, y, s, x0=-0.5, x1=0.5, c='siding2', n=4):
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        k.qy(x - 0.03, x + 0.03, z0 + 0.01, z1 - 0.01, y, s, c)


def wall_body(k, kind, endL=False, endR=False):
    """Common module: block dado, siding, girt, pipe pair, roof edge; exterior siding on the back. End modules (next
    to a corner on their local -X / +X side) stop their proud trims short of that corner and carry no pipes, so the
    two walls of an inside corner never stack trims in the same corner square."""
    x0 = -0.497 + (0.14 if endL else 0.0)
    x1 = 0.497 - (0.14 if endR else 0.0)
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'siding')
    k.bx(x0, x1, -0.53, -0.5, 0.0, 3.0, 'block', ink=False)                       # block dado
    for z in (0.6, 1.2, 1.8, 2.4):
        k.qy(x0, x1, z - 0.012, z + 0.012, -0.533, -1, 'blockLine')
    k.stripes(x0, x1, 0.02, 0.24, -0.533, -1, 4)
    k.bx(x0, x1, -0.56, -0.5, 3.0, 3.08, 'steel2', ink=False)                     # dado cap
    siding_ribs(k, 3.08, 6.0, -0.503, -1)
    k.bx(x0, x1, -0.62, -0.5, 5.95, 6.15, 'beam2', ink=False)                     # girt
    if not (endL or endR):
        for zz, r in ((4.35, 0.09), (4.7, 0.06)):                                 # pipe pair (runs on)
            k.cyl(-0.497, -0.78, zz, r, r, 0.994, 'steel2' if r > 0.07 else 'beam', seg=6, rot=(0, 90, 0), ink=False)
        k.bx(-0.03, 0.03, -0.8, -0.5, 4.2, 4.82, 'steelDark', ink=False)        # pipe bracket
    elif not (endL and endR):                                                     # pipe run ends: stub + flange
        xs = -0.497 if endR else 0.397
        for zz, r in ((4.35, 0.09), (4.7, 0.06)):
            k.cyl(xs, -0.78, zz, r, r, 0.1, 'steel2' if r > 0.07 else 'beam', seg=6, rot=(0, 90, 0), ink=False)
            k.cyl(xs + (0.1 if endR else -0.03), -0.78, zz, r + 0.035, r + 0.035, 0.03, 'steelDark', seg=6, rot=(0, 90, 0), ink=False)
    k.bx(x0, x1, -0.58, -0.5, 9.7, WALL_H, 'roofEdge', ink=False)
    # exterior (back) siding
    k.bx(-0.497, 0.497, 0.5, 0.53, 0.0, WALL_H - 0.4, 'ext', ink=False)
    siding_ribs(k, 0.3, WALL_H - 0.45, 0.533, 1, c='ext2')
    k.bx(-0.497, 0.497, 0.5, 0.62, WALL_H - 0.4, WALL_H - 0.25, 'roofEdge', ink=False)


def end_module(k, side):
    k.begin()
    wall_body(k, 'End', endL=side in ('L', 'LR'), endR=side in ('R', 'LR'))
    return k


def wall_module(k, kind):
    k.begin()
    win = kind.startswith('Win')
    if win:
        # same body, but the clerestory band is open with mullions and a sill
        k.bx(-0.5, 0.5, -0.5, 0.5, 0, WIN0, 'siding')
        k.bx(-0.5, 0.5, -0.5, 0.5, WIN1, WALL_H, 'siding')
        k.bx(-0.497, 0.497, -0.53, -0.5, 0.0, 3.0, 'block', ink=False)
        for z in (0.6, 1.2, 1.8, 2.4):
            k.qy(-0.5, 0.5, z - 0.012, z + 0.012, -0.533, -1, 'blockLine')
        k.stripes(-0.5, 0.5, 0.02, 0.24, -0.533, -1, 4)
        k.bx(-0.497, 0.497, -0.56, -0.5, 3.0, 3.08, 'steel2', ink=False)
        siding_ribs(k, 3.08, 5.95, -0.503, -1)
        k.bx(-0.497, 0.497, -0.62, -0.5, 5.95, 6.15, 'beam2', ink=False)
        for zz, r in ((4.35, 0.09), (4.7, 0.06)):
            k.cyl(-0.5, -0.78, zz, r, r, 1.0, 'steel2' if r > 0.07 else 'beam', seg=6, rot=(0, 90, 0), ink=False)
        k.bx(-0.03, 0.03, -0.8, -0.5, 4.2, 4.82, 'steelDark', ink=False)
        k.bx(-0.497, 0.497, -0.6, -0.5, WIN0 - 0.08, WIN0 + 0.02, 'mullion')        # sill
        k.bx(-0.06, 0.06, -0.1, 0.1, WIN0 + 0.02, WIN1, 'mullion')               # mullion (centre)
        k.bx(-0.5, 0.5, -0.08, 0.08, 7.65, 7.75, 'mullion', ink=False)           # transom
        if kind == 'Win_B':
            k.poly([(-0.4, -0.02, 6.7), (-0.32, -0.02, 6.7), (0.0, -0.02, 7.5), (-0.08, -0.02, 7.5)], 'glint', (0, -1, 0))
            k.poly([(0.12, -0.02, 7.9), (0.18, -0.02, 7.9), (0.42, -0.02, 8.7), (0.36, -0.02, 8.7)], 'glint', (0, -1, 0))
        k.bx(-0.497, 0.497, -0.58, -0.5, 9.7, WALL_H, 'roofEdge', ink=False)
        siding_ribs(k, WIN1 + 0.02, 9.68, -0.503, -1)
        k.bx(-0.497, 0.497, 0.5, 0.53, 0.0, WIN0 - 0.1, 'ext', ink=False)
        siding_ribs(k, 0.3, WIN0 - 0.15, 0.533, 1, c='ext2')
        k.bx(-0.497, 0.497, 0.5, 0.53, WIN1 + 0.05, WALL_H - 0.4, 'ext', ink=False)
        k.bx(-0.497, 0.497, 0.5, 0.62, WALL_H - 0.4, WALL_H - 0.25, 'roofEdge', ink=False)
    else:
        wall_body(k, kind)
    if kind in ('Win_Panel', 'Panel'):
        k.bx(-0.36, 0.06, -0.78, -0.53, 1.0, 2.1, 'panel')
        k.qy(-0.3, 0.0, 1.85, 2.0, -0.783, -1, 'hazard')
        k.qy(-0.32, -0.04, 1.1, 1.75, -0.783, -1, 'panelG')
        k.bx(-0.03, 0.03, -0.62, -0.56, 2.1, 4.2, 'steelDark', ink=False)          # conduit
        k.bx(0.15, 0.38, -0.66, -0.53, 1.3, 1.6, 'panelG')
        k.qy(0.2, 0.33, 1.42, 1.52, -0.663, -1, 'teal')
    elif kind in ('Win_Sign', 'Sign'):
        # stencilled robot head and zone number (blocks) on the siding
        k.qy(-0.46, 0.46, 3.3, 5.6, -0.506, -1, 'label')
        k.qy(-0.3, 0.3, 4.1, 5.2, -0.509, -1, 'ink')
        k.qy(-0.22, -0.06, 4.7, 4.9, -0.512, -1, 'core')
        k.qy(0.06, 0.22, 4.7, 4.9, -0.512, -1, 'core')
        k.qy(-0.16, 0.16, 4.3, 4.4, -0.512, -1, 'red')
        k.qy(-0.02, 0.02, 5.2, 5.45, -0.509, -1, 'ink')
        k.qy(-0.4, 0.4, 3.45, 3.85, -0.509, -1, 'red')
    elif kind in ('Win_Vent', 'Vent'):
        k.bx(-0.42, 0.42, -0.66, -0.5, 3.25, 4.1, 'steelDark')
        k.qy(-0.36, 0.36, 3.31, 4.04, -0.663, -1, 'grate')
        k.qy(-0.36, 0.36, 3.65, 3.7, -0.666, -1, 'steel2')
        k.qy(-0.025, 0.025, 3.31, 4.04, -0.669, -1, 'steel2')
        k.qy(-0.08, 0.08, 3.6, 3.75, -0.672, -1, 'hazard')
    elif kind in ('Win_Hose', 'Hose'):
        k.bx(-0.2, 0.2, -0.75, -0.53, 1.2, 1.9, 'red')
        k.cyl(0, -0.76, 1.55, 0.15, 0.15, 0.02, 'rubber', seg=10, rot=(90, 0, 0), ink=False)
        k.qy(-0.12, 0.12, 2.0, 2.15, -0.536, -1, 'red')
    return k


def column(k):
    """Wall pier every 6 m: a red-orange I-beam column on the wall with a crane-rail bracket, base plate."""
    k.begin()
    wall_body(k, 'Col')
    k.bx(-0.28, 0.28, -0.94, -0.86, 0.0, CEIL, 'beam')        # flanges
    k.bx(-0.28, 0.28, -0.64, -0.56, 0.0, CEIL, 'beam')
    k.bx(-0.04, 0.04, -0.86, -0.64, 0.0, CEIL, 'beam2', ink=False)
    k.bx(-0.36, 0.36, -1.0, -0.53, 0.0, 0.06, 'steelDark', ink=False)
    k.stripes(-0.28, 0.28, 0.1, 1.2, -0.943, -1, 4)
    k.bx(-0.3, 0.3, -1.4, -0.94, 7.2, 7.6, 'beam2')            # bracket
    k.qy(-0.18, 0.18, 2.6, 2.9, -0.946, -1, 'label')
    k.qy(-0.1, 0.1, 2.68, 2.82, -0.949, -1, 'ink')
    return k


def corner(k):
    """Corners, notches, free-standing columns: concrete pier with steel angle guards (all-round)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'conc')
    for s in (-1, 1):   # hazard wraps (flat, so nothing pokes into a neighbouring cell)
        k.stripes(-0.5, 0.5, 0.0, 1.2, s * 0.506, s, 4)
        k.qx(-0.5, 0.5, 0.0, 1.2, s * 0.506, s, 'hazard')
        for z in (0.15, 0.65):
            k.poly([(s * 0.509, -0.5, z), (s * 0.509, 0.5, z + 0.3), (s * 0.509, 0.5, z + 0.5), (s * 0.509, -0.5, z + 0.2)], 'ink', (s, 0, 0))
    for s in (-1, 1):
        k.qy(-0.5, 0.5, 2.4, 2.45, s * 0.503, s, 'conc2')
        k.qx(-0.5, 0.5, 2.4, 2.45, s * 0.503, s, 'conc2')
    return k


def block_wall(k, kind):
    """Interior walls (machine rooms, partitions): painted block to the roof, no windows."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'block')
    for z in (0.6, 1.2, 1.8, 2.4, 3.0, 3.6):
        k.qy(-0.5, 0.5, z - 0.012, z + 0.012, -0.503, -1, 'blockLine')
    k.qy(-0.5, 0.5, 4.0, 10.0, -0.503, -1, 'conc2')
    k.stripes(-0.5, 0.5, 0.02, 0.24, -0.503, -1, 4)
    if kind == 'Arrow':
        k.poly([(-0.35, -0.506, 1.6), (0.1, -0.506, 1.6), (0.1, -0.506, 1.4), (0.42, -0.506, 1.8), (0.1, -0.506, 2.2), (0.1, -0.506, 2.0), (-0.35, -0.506, 2.0)], 'teal', (0, -1, 0))
    elif kind == 'Num':
        for i, (x0, x1, z0, z1) in enumerate(((-0.4, -0.1, 5.0, 5.15), (-0.4, -0.35, 5.0, 6.0), (-0.4, -0.1, 5.85, 6.0), (-0.15, -0.1, 5.0, 6.0),
                                              (0.05, 0.4, 5.85, 6.0), (0.35, 0.4, 5.0, 6.0), (0.05, 0.4, 5.42, 5.57), (0.05, 0.4, 5.0, 5.15))):
            k.qy(x0, x1, z0, z1, -0.506 - 0.003 * i, -1, 'ink')
    return k


# ================================================================ ceiling, gate, trail, hatch
def ceil_truss(k):
    """12 x 12 m roof bay at the ceiling plane: a Warren truss along X, purlins along Y, a high-bay lamp with its pool
    of light painted on the floor 10 m below."""
    k.begin()
    D = -CEIL
    k.bx(-5.95, 5.95, -0.12, 0.12, -1.42, -1.3, 'beam')            # bottom chord
    k.bx(-5.95, 5.95, -0.12, 0.12, -0.14, -0.02, 'beam')           # top chord
    for i in range(8):
        x0 = -6.0 + i * 1.5
        k.beam((x0 + 0.05, 0, -1.3), (x0 + 0.75, 0, -0.14), 0.09, 'beam2', ink=False)
        k.beam((x0 + 0.75, 0.007, -0.14), (x0 + 1.45, 0.007, -1.3), 0.09, 'beam2', ink=False)
    for x in (-4.5, -1.5, 1.5, 4.5):
        k.bx(x - 0.07, x + 0.07, -5.95, 5.95, -0.28, -0.17, 'steel2', ink=False)
    # lamp on a rod at the bay centre (off the truss, at y = 6 / mid-bay)
    k.bx(-0.02, 0.02, 2.98, 3.02, -2.6, -0.02, 'steelDark', ink=False)
    k.cyl(0, 3.0, -3.1, 0.55, 0.16, 0.5, 'steelDark', seg=10)
    k.cyl(0, 3.0, -3.12, 0.5, 0.5, 0.004, 'lamp', seg=10, ink=False)
    rnd = random.Random(4)
    k.disc(0.0, 3.0, D + Z['pool'], 3.0, 'pool', n=16, rnd=rnd, jag=0.04)
    k.disc(0.0, 3.0, D + Z['pool'] + 0.004, 1.6, 'pool2', n=12, rnd=rnd, jag=0.05)
    # a chain hoist hanging off the truss
    k.bx(3.0 - 0.015, 3.0 + 0.015, -0.015, 0.015, -4.2, -1.42, 'steelDark', ink=False)
    k.bx(2.85, 3.15, -0.12, 0.12, -1.9, -1.55, 'hazard')
    k.beam((3.0, 0.0, -4.2), (3.0, 0.0, -4.45), 0.06, 'steelDark', ink=False)
    return k


def gate_frame(k):
    """Hall gate: hazard-wrapped steel posts, a header with a beacon and a teal-striped zone board, the roll-up
    housing, and corrugated infill up to the roof (both faces)."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.495, s * 2.1)
        k.bx(x0, x1, -0.62, 0.62, 0, 3.3, 'steelDark')
        for f in (-1, 1):
            y = f * 0.623
            k.qy(x0 + 0.05, x1 - 0.05, 0.1, 3.1, y, f, 'hazard')
            for i in range(5):
                z = 0.25 + i * 0.6
                k.poly([(x0 + 0.05, y + f * 0.003, z), (x1 - 0.05, y + f * 0.003, z + 0.25), (x1 - 0.05, y + f * 0.003, z + 0.45), (x0 + 0.05, y + f * 0.003, z + 0.2)], 'ink', (0, f, 0))
    k.bx(-2.3, 2.3, -0.7, 0.7, 3.3, 4.1, 'steel2')                         # roll housing / header
    k.bx(-2.4, 2.4, -0.25, 0.25, 4.1, WALL_H + 0.03, 'siding')               # infill wall
    for f in (-1, 1):
        y = f * 0.253
        for i in range(12):
            x = -2.25 + i * 0.4
            k.qy(x - 0.03, x + 0.03, 4.15, WALL_H - 0.05, y, f, 'siding2')
        yb = f * 0.703
        k.qy(-1.9, 1.9, 3.95, 4.02, yb, f, 'teal')
        k.qy(-1.9, 1.9, 3.38, 3.45, yb, f, 'teal')
        k.bx(-0.75, 0.75, *srt(f * 0.7, f * 0.74), 4.3, 5.0, 'label')
        for i, w in enumerate((0.2, 0.12, 0.26)):
            x = -0.6 + i * 0.42
            k.qy(x, x + w, 4.45, 4.85, f * 0.743, f, 'ink')
        k.cyl(1.9, f * 0.9, 3.3, 0.12, 0.12, 0.16, 'steelDark', seg=8)
        k.cyl(1.9, f * 0.9, 3.46, 0.1, 0.08, 0.2, 'hot', seg=8)
    return k


def gate_shutter(k):
    """Corrugated roll-up door with vision slots and a hazard bottom rail."""
    k.begin()
    Hs, n = 3.05, 12
    h = (Hs - 0.35) / n
    for i in range(n):
        z0 = 0.35 + i * h
        k.bx(-1.5, 1.5, -0.06, 0.06, z0, z0 + h, 'steel' if i % 2 else 'steel2', ink=False)
    for f in (-1, 1):
        for x in (-0.9, -0.3, 0.3, 0.9):
            k.qy(x - 0.2, x + 0.2, 1.9, 2.05, f * 0.063, f, 'mullion')
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.35, 'ink' if j % 2 else 'hazard', ink=False)
    return k


def trail_wall(k):
    """Service corridor wall (1 m along Blender Y, corridor to +X): block dado, pipes, half the lowered ceiling with
    a strip light; exterior siding on the back (-X)."""
    k.begin(90)
    k.bx(-0.5, 0.5, -0.25, 0.25, 0, WALL_H, 'siding')
    k.bx(-0.5, 0.5, -0.28, -0.25, 0, 2.6, 'block', ink=False)
    for z in (0.65, 1.3, 1.95):
        k.qy(-0.5, 0.5, z - 0.012, z + 0.012, -0.283, -1, 'blockLine')
    k.stripes(-0.5, 0.5, 0.02, 0.22, -0.283, -1, 4)
    k.bx(-0.5, 0.5, -0.31, -0.25, 2.6, 2.68, 'steel2', ink=False)
    siding_ribs(k, 2.68, ROOF - 0.05, -0.253, -1)
    for zz, r, c in ((3.25, 0.1, 'steel2'), (3.62, 0.07, 'beam'), (3.9, 0.05, 'cyl')):
        k.cyl(-0.5, -0.45 - r, zz, r, r, 1.0, c, seg=6, rot=(0, 90, 0), ink=False)
    k.bx(-0.03, 0.03, -0.62, -0.25, 3.1, 4.0, 'steelDark', ink=False)
    y_mid = -2.25 + 0.003
    k.bx(-0.5, 0.5, y_mid, -0.25, ROOF, ROOF + 0.08, 'ceil', ink=False)        # ceiling panel
    k.qz(-0.5, 0.5, -1.02, -0.98, ROOF - 0.003, -1, 'steel2')
    k.bx(-0.5, 0.5, -1.75, -1.45, ROOF - 0.08, ROOF, 'steelDark', ink=False)    # strip light housing
    k.qz(-0.5, 0.5, -1.7, -1.5, ROOF - 0.083, -1, 'lamp')
    k.qz(-0.5, 0.5, -0.75, -0.38, 0.012, 1, 'hazard')                           # walkway edge line
    # exterior
    k.bx(-0.5, 0.5, 0.25, 0.28, 0.0, WALL_H - 0.4, 'ext', ink=False)
    siding_ribs(k, 0.3, WALL_H - 0.45, 0.283, 1, c='ext2')
    return k


def hatch(k):
    """Exit: the dispatch lift. A chevron pad, a freight platform at the back wall under a lift shaft that closes the
    roof slot (the corridor ceiling halves leave 1.5 m open over the room centre)."""
    k.begin()
    k.bx(-1.2, 1.2, -1.25, 1.0, 0, 0.05, 'steel2')
    for i in range(4):
        y = -1.15 + i * 0.5
        k.poly([(-0.9, y, 0.053), (0, y + 0.3, 0.053), (0.9, y, 0.053), (0.9, y + 0.14, 0.053), (0, y + 0.44, 0.053), (-0.9, y + 0.14, 0.053)], 'teal' if i % 2 else 'hazard', (0, 0, 1))
    # lift platform + car frame at the back
    C0, C1, W = 1.05, 2.68, 1.3
    k.bx(-W, W, C0, C1, 0, 0.14, 'steelDark')
    k.qz(-W + 0.05, W - 0.05, C0 + 0.02, C0 + 0.14, 0.143, 1, 'hazard')
    for x in (-W, W):
        k.bx(x - 0.07, x + 0.07, C0 - 0.07, C0 + 0.07, 0.14, ROOF - 0.05, 'beam')
        k.bx(x - 0.07, x + 0.07, C1 - 0.12, C1 - 0.02, 0.14, ROOF - 0.05, 'beam')
        k.stripes(x - 0.07, x + 0.07, 0.2, 1.6, C0 - 0.073, -1, 4)
    k.bx(-W + 0.075, W - 0.075, C1 - 0.06, C1, 0.16, 3.0, 'steel2')
    for i in range(1, 9):
        x = -W + 2 * W * i / 9
        k.qy(x - 0.02, x + 0.02, 0.2, 2.95, C1 - 0.063, -1, 'steel')
    k.bx(-W - 0.07, W + 0.07, C0 - 0.08, C1, ROOF - 0.05, ROOF + 0.1, 'beam2')
    k.bx(-0.6, 0.6, C1 - 0.1, C1 - 0.06, 3.2, 3.8, 'label')
    k.qy(-0.5, 0.5, 3.3, 3.7, C1 - 0.103, -1, 'ink')
    k.qy(-0.42, -0.1, 3.4, 3.6, C1 - 0.106, -1, 'core')
    k.qy(0.1, 0.42, 3.4, 3.6, C1 - 0.106, -1, 'teal')
    k.cyl(W - 0.2, C0 + 0.1, ROOF + 0.1, 0.1, 0.08, 0.18, 'hot', seg=8)
    # shaft over the roof slot
    for s in (-1, 1):
        x0, x1 = srt(s * 0.77, s * 0.95)
        k.bx(x0, x1, -1.55, 2.72, ROOF + 0.12, WALL_H - 0.04, 'siding2')
    k.bx(-0.9, 0.9, -1.53, -0.97, ROOF + 0.13, WALL_H - 0.05, 'siding2')
    for x in (-0.25, 0.25):
        k.bx(x - 0.02, x + 0.02, 1.8, 1.84, ROOF + 0.1, WALL_H - 0.6, 'steelDark', ink=False)
    k.cyl(0, 1.82, WALL_H - 0.9, 0.45, 0.45, 0.12, 'beam', seg=12, rot=(0, 90, 0))
    pool_disc(k, 0.0, 1.8, Z['hatch'], 1.2, 7)
    return k


def pool_disc(k, x, y, z, r, seed, sx=1.0, sy=1.0, c1='pool', c2='pool2'):
    rnd = random.Random(seed)
    k.disc(x, y, z, r, c1, n=14, rnd=rnd, jag=0.05, sx=sx, sy=sy)
    k.disc(x, y, z + 0.004, r * 0.55, c2, n=10, rnd=rnd, jag=0.06, sx=sx, sy=sy)


# ================================================================ props
def crate_body(k, hx, hy, h, kind):
    k.bx(-hx, hx, -hy, hy, 0, h, 'crate')
    for f in (-1, 1):
        y = f * (hy + 0.003)
        k.qy(-hx + 0.02, hx - 0.02, h * 0.5 - 0.02, h * 0.5 + 0.02, y, f, 'crate2')
        k.qy(-hx + 0.02, -hx + 0.08, 0.02, h - 0.02, y + f * 0.003, f, 'crate2')
        k.qy(hx - 0.08, hx - 0.02, 0.02, h - 0.02, y + f * 0.003, f, 'crate2')
    for f in (-1, 1):
        k.qx(-hy + 0.02, hy - 0.02, h * 0.5 - 0.02, h * 0.5 + 0.02, f * (hx + 0.003), f, 'crate2')
    if kind == 'Closed':
        k.qz(-hx + 0.03, hx - 0.03, -0.02, 0.02, h + 0.003, 1, 'crate2')
        k.qy(-0.18, 0.18, h * 0.18, h * 0.42, -hy - 0.006, -1, 'ink')
        k.qy(-0.12, -0.04, h * 0.3, h * 0.36, -hy - 0.009, -1, 'core')
        k.qy(0.04, 0.12, h * 0.3, h * 0.36, -hy - 0.009, -1, 'core')


def crate(k, kind):
    k.begin()
    if kind == 'Lid':      # small closed box with a red stencil
        k.bx(-0.32, 0.32, -0.26, 0.26, 0, 0.5, 'crate')
        k.qz(-0.3, 0.3, -0.02, 0.02, 0.503, 1, 'crate2')
        k.qy(-0.2, 0.2, 0.15, 0.3, -0.263, -1, 'red')
        return k
    crate_body(k, 0.46, 0.4, 0.86, kind)
    if kind == 'Cans':          # open crate of crawler bodies
        k.qz(-0.43, 0.43, -0.37, 0.37, 0.8, 1, 'crate2')
        for x in (-0.22, 0.22):
            for y in (-0.18, 0.18):
                k.cyl(x, y, 0.8, 0.17, 0.17, 0.16, 'tin', seg=8)
                k.cyl(x, y, 0.96, 0.07, 0.07, 0.02, 'core', seg=6, ink=False)
    elif kind == 'Wheels':
        k.qz(-0.43, 0.43, -0.37, 0.37, 0.8, 1, 'crate2')
        for i, (x, y, a) in enumerate(((-0.2, -0.12, 20), (0.18, 0.1, -15), (0.0, 0.0, 75))):
            k.cyl(x, y, 0.82 + i * 0.05, 0.17, 0.17, 0.08, 'rubber', seg=8, rot=(a, 0, 0))
    return k


def pallet(k, kind):
    """2 x 2 pallet of parts (cover)."""
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.14, 'crate2')
    for x in (-0.6, 0.0, 0.6):
        k.qz(x - 0.2, x + 0.2, -0.9, 0.9, 0.143, 1, 'crate')
    if kind == 'Bins':          # stacked gunner shells (bins nest)
        for x in (-0.42, 0.42):
            for y in (-0.42, 0.42):
                gunner(k, x, y, 0.14, gun=False, s=0.85)
    elif kind == 'Cans':        # shrink-wrapped crawler cans, two layers
        for z in (0.14, 0.64):
            for x in (-0.42, 0.42):
                for y in (-0.42, 0.42):
                    k.cyl(x, y, z, 0.36, 0.36, 0.48, 'tin', seg=8)
                    k.cyl(x, y, z + 0.2, 0.365, 0.365, 0.1, 'rust', seg=8, caps=False, ink=False)
        k.qz(-0.85, 0.85, -0.05, 0.05, 1.125, 1, 'hazard')
    else:                       # bottle crates
        for x in (-0.45, 0.45):
            for y in (-0.45, 0.45):
                k.bx(x - 0.43, x + 0.43, y - 0.43, y + 0.43, 0.14, 0.5, 'steel2')
                for dx in (-0.2, 0.2):
                    for dy in (-0.2, 0.2):
                        k.cyl(x + dx, y + dy, 0.5, 0.16, 0.16, 0.34, 'glassB', seg=8)
                        k.cyl(x + dx, y + dy, 0.84, 0.16, 0.06, 0.12, 'glassB2', seg=8, ink=False)
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 1.2)
    return k


def drums(k, variant):
    k.begin()
    spots = [(-0.22, -0.15), (0.24, 0.16)] if variant == 0 else [(0.0, 0.0)]
    for i, (x, y) in enumerate(spots):
        c, c2 = ('beam', 'beam2') if (i + variant) % 2 == 0 else ('cyl', 'steelDark')
        k.cyl(x, y, 0, 0.27, 0.27, 0.88, c, seg=10)
        for z in (0.29, 0.58):
            k.cyl(x, y, z, 0.283, 0.283, 0.035, c2, seg=10, ink=False, caps=False)
        k.cyl(x, y, 0.88, 0.22, 0.22, 0.006, c2, seg=10, ink=False)
        k.cyl(x + 0.17, y, 0.886, 0.04, 0.04, 0.02, 'steelDark', seg=6, ink=False)
    if variant == 1:
        k.qy(-0.12, 0.12, 0.35, 0.55, -0.276, -1, 'hazard')
    return k


def gas_rack(k):
    k.begin()
    for i, x in enumerate((-0.3, 0.0, 0.3)):
        k.cyl(x, 0.1, 0.05, 0.13, 0.13, 1.25, 'cyl' if i != 1 else 'beam', seg=8)
        k.cyl(x, 0.1, 1.3, 0.1, 0.05, 0.12, 'label', seg=8)
        k.cyl(x, 0.1, 1.42, 0.03, 0.03, 0.08, 'steelDark', seg=5, ink=False)
    k.bx(-0.48, 0.48, -0.08, 0.32, 0, 0.05, 'steelDark')
    for x in (-0.47, 0.47):
        k.bx(x - 0.02, x + 0.02, 0.26, 0.3, 0.05, 1.2, 'steelDark', ink=False)
    k.bx(-0.47, 0.47, -0.07, -0.04, 0.85, 0.9, 'hazard', ink=False)
    k.col(-0.48, 0.48, -0.1, 0.32, 0, 1.4)
    return k


def conveyor(k):
    """Belt conveyor section (1 m along X): frame, legs and the rubber belt. It moves in the game: the parts riding it
    (Item_*) and the belt cleats (Belt_Cleat) are separate pieces animated by the engine (theme conveyor option)."""
    k.begin()
    for s in (-1, 1):
        k.bx(-0.5, 0.5, *srt(s * 0.4, s * 0.47), 0.72, 0.92, 'hazard')
    for x in (-0.3, 0.3):
        for s in (-1, 1):
            k.bx(x - 0.04, x + 0.04, *srt(s * 0.36, s * 0.42), 0, 0.72, 'steelDark', ink=False)
        k.bx(x - 0.03, x + 0.03, -0.41, 0.41, 0.2, 0.26, 'steelDark', ink=False)
    k.bx(-0.5, 0.5, -0.38, 0.38, 0.78, 0.86, 'rubber')
    k.col(-0.5, 0.5, -0.47, 0.47, 0, 1.0)
    return k


def belt_hood(k, kind, L=0.5, W=0.47, H=1.72, rail=0.92, base=None):
    """End hood over a moving belt (local +X = downstream), straddling the end cell / tile: side walls standing on the
    belt rails, a roof, a closed motor end and a rubber strip curtain over the open mouth, so the parts pop in and out of
    sight inside it. kind 'Feed' (closed upstream end, at the start of a run) or 'Exit' (closed downstream end)."""
    k.begin()
    sx = -1 if kind == 'Feed' else 1          # the closed end
    z0 = rail + 0.004 if base is None else base   # walls on the rails, or down to the floor beside them
    for s in (-1, 1):
        y0, y1 = srt(s * (W - 0.07), s * W)
        k.bx(-L, L, y0, y1, z0, H, 'steel2')
        k.stripes(-L + 0.04, L - 0.04, rail + 0.06, rail + 0.26, s * (W + 0.003), s, 4)
    k.bx(-L - 0.02, L + 0.02, -W - 0.03, W + 0.03, H, H + 0.08, 'steelDark')
    x0, x1 = srt(sx * (L - 0.066), sx * (L - 0.006))
    k.bx(x0, x1, -W + 0.07, W - 0.07, max(z0, rail - 0.25), H, 'siding2')      # closed end panel (over the belt end)
    k.bx(*srt(sx * L, sx * (L + 0.14)), -0.22, 0.22, rail - 0.3, rail + 0.4, 'steelDark')   # motor
    k.cyl(sx * (L + 0.14), 0, rail + 0.05, 0.14, 0.14, 0.1, 'beam', seg=8, rot=(0, 90 * sx, 0))
    xm = -sx * (L - 0.04)                                                       # strip curtain at the mouth
    n = 5
    for i in range(n):
        y = -W + 0.09 + (2 * W - 0.18) * (i + 0.5) / n
        k.bx(xm - 0.008 - 0.004 * (i % 2), xm + 0.008 - 0.004 * (i % 2), y - 0.07, y + 0.07, rail + 0.16, H - 0.004, 'rubber', ink=False)
    k.qy(-0.18, 0.18, H - 0.3, H - 0.12, -W - 0.003 - 0.003, -1, 'label')
    k.qy(-0.12, 0.12, H - 0.27, H - 0.15, -W - 0.009, -1, 'teal' if kind == 'Feed' else 'red')
    k.col(-L, L, -W, W, 0, H + 0.08)
    return k


def belt_cleat(k, w=0.36):
    """A belt cleat (slides along the moving belt)."""
    k.begin()
    k.bx(-0.03, 0.03, -w, w, 0.0, 0.025, 'grate', ink=False)
    return k


def belt_item(k, variant):
    """Parts riding the factory belt (origin = belt top)."""
    k.begin()
    if variant == 'Can':
        crawler(k, 0.0, 0.0, 0.0, legs=0, top=False, s=0.8)
    elif variant == 'Bottle':
        bottle(k, -0.12, 0.05, 0.0, cap=False, base=False, s=0.75)
        k.cyl(0.25, -0.1, 0.0, 0.09, 0.09, 0.06, 'red', seg=8)
    elif variant == 'Drone':
        drone(k, 0.0, 0.0, 0.0, arms=1, s=0.8, deg=45)
    else:
        k.cyl(-0.2, 0.0, 0.0, 0.16, 0.16, 0.08, 'rubber', seg=8)
        k.cyl(0.18, 0.05, 0.0, 0.16, 0.16, 0.08, 'rubber', seg=8)
        k.cyl(0.18, 0.05, 0.08, 0.06, 0.06, 0.02, 'steel', seg=6, ink=False)
    return k


def tool_station(k, kind):
    k.begin()
    if kind == 'Screen':        # welding curtain on a frame
        for x in (-0.45, 0.45):
            k.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0, 1.9, 'steelDark')
            k.bx(x - 0.18, x + 0.18, -0.2, 0.2, 0, 0.04, 'steelDark', ink=False)
        k.bx(-0.48, 0.48, -0.03, 0.03, 1.9, 1.96, 'steelDark')
        for i in range(4):
            x0 = -0.42 + i * 0.21
            k.bx(x0, x0 + 0.2, -0.015 + (i % 2) * 0.03 - 0.0, 0.015 + (i % 2) * 0.03, 0.15, 1.85, 'curtain')
        k.col(-0.5, 0.5, -0.2, 0.2, 0, 1.9)
    else:                       # rolling tool chest with a vice
        k.bx(-0.4, 0.4, -0.28, 0.28, 0.12, 1.0, 'red')
        for i in range(4):
            z = 0.22 + i * 0.2
            k.qy(-0.36, 0.36, z, z + 0.16, -0.283, -1, 'beam2')
            k.qy(-0.12, 0.12, z + 0.11, z + 0.14, -0.286, -1, 'steel')
        for x in (-0.3, 0.3):
            for y in (-0.2, 0.2):
                k.cyl(x, y, 0.0, 0.06, 0.06, 0.12, 'rubber', seg=6, ink=False)
        k.bx(-0.42, 0.42, -0.3, 0.3, 1.0, 1.04, 'steelDark')
        k.bx(0.1, 0.32, -0.12, 0.08, 1.04, 1.2, 'steel2')
        k.col(-0.42, 0.42, -0.3, 0.3, 0, 1.2)
    return k


def robot_arm(k, x, y, deg, z=0.0, reach=1.0, tool='claw', s=1.0):
    """Industrial robot arm: base, turret, upper arm, forearm, wrist and tool, reaching along local -Y."""
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0, 0.42, 0.42, 0.18, 'steelDark', seg=8)
    k.cyl(0, 0, 0.18, 0.32, 0.28, 0.42, 'arm', seg=8)
    k.bx(-0.22, 0.22, -0.2, 0.2, 0.55, 0.85, 'arm2')
    sh = Vector((0, 0, 0.75))
    el = Vector((0, -0.55 * reach, 1.75))
    wr = Vector((0, -1.25 * reach, 1.35))
    k.beam(sh, el, 0.24, 'arm')
    k.cyl(-0.16, el.y, el.z - 0.18, 0.18, 0.18, 0.32, 'arm2', seg=6, rot=(0, 90, 0))
    k.beam(el, wr, 0.17, 'arm')
    k.cyl(-0.1, wr.y, wr.z - 0.1, 0.1, 0.1, 0.2, 'steelDark', seg=8, rot=(0, 90, 0))
    k.beam(wr, wr + Vector((0, -0.1, -0.3)), 0.1, 'steel2')
    tip = wr + Vector((0, -0.1, -0.32))
    if tool == 'claw':
        for sx in (-1, 1):
            k.bx(tip.x + sx * 0.06 - 0.02, tip.x + sx * 0.06 + 0.02, tip.y - 0.03, tip.y + 0.03, tip.z - 0.22, tip.z, 'steelDark', ink=False)
    else:                       # welder: torch + spark star
        k.beam(tip, tip + Vector((0, -0.05, -0.2)), 0.04, 'steelDark', ink=False)
        p = tip + Vector((0, -0.05, -0.24))
        k.poly([(p.x - 0.12, p.y - 0.004, p.z), (p.x, p.y - 0.004, p.z + 0.04), (p.x + 0.12, p.y - 0.004, p.z),
                (p.x + 0.03, p.y - 0.004, p.z - 0.02), (p.x + 0.06, p.y - 0.004, p.z - 0.12), (p.x, p.y - 0.004, p.z - 0.04),
                (p.x - 0.06, p.y - 0.004, p.z - 0.12), (p.x - 0.03, p.y - 0.004, p.z - 0.02)], 'hot2', (0, -1, 0))
    k.beam((0.2, 0.0, 0.6), (0.18, -0.4, 1.6), 0.04, 'rubber', ink=False)
    k.pop()


def arm_cell(k, kind):
    """2 x 2 standalone robot arm on a hazard-ringed plinth, posed over a work piece."""
    k.begin()
    rnd = random.Random(3)
    k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.12, 'conc2')
    k.qz(-0.86, 0.86, -0.86, 0.86, 0.123, 1, 'hazard')
    k.qz(-0.7, 0.7, -0.7, 0.7, 0.126, 1, 'conc2')
    robot_arm(k, 0.35, 0.45, 20 if kind == 'A' else -15, z=0.12, reach=0.85, tool='claw' if kind == 'A' else 'weld')
    if kind == 'A':
        gunner(k, -0.35, -0.4, 0.126, gun=False, s=0.7)
    else:
        crawler(k, -0.3, -0.35, 0.126, legs=1, s=0.9)
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 1.2)
    return k


def assembly_line(k, kind):
    """Prefab 8 x 4: a belt along X carrying two half-built robots, an arm on each side working on them, an overhead
    gantry with a beacon, hazard lanes painted either side, a parts bin at the end."""
    k.begin()
    for s in (-1, 1):
        k.bx(-4.0, 4.0, *srt(s * 0.52, s * 0.6), 0.74, 0.96, 'hazard')
    for x in (-3.5, -2.0, -0.5, 1.0, 2.5):
        for s in (-1, 1):
            k.bx(x - 0.05, x + 0.05, *srt(s * 0.46, s * 0.52), 0, 0.74, 'steelDark', ink=False)
    k.bx(-4.0, 4.0, -0.46, 0.46, 0.8, 0.88, 'rubber')
    for s in (-1, 1):   # hazard lanes
        k.qz(-4.0, 4.0, *srt(s * 0.9, s * 1.0), Z['line'], 1, 'hazard')
    # the half-built robots ride the moving belt (LineBot_* pieces, animated by the engine); the section's type shows on
    # a placard on the gantry and in its parts bin
    tc = {'Crawler': 'tin', 'Gunner': 'bin', 'Bomber': 'glassB', 'Drone': 'can'}[kind]
    for f in (-1, 1):
        k.bx(-0.5, 0.5, *srt(f * 1.8, f * 1.84), 4.22, 4.38, 'label')
        k.qy(-0.4, 0.4, 4.25, 4.35, f * 1.843, f, tc)
    robot_arm(k, -1.8, 1.55, 0, reach=1.0, tool='weld')
    robot_arm(k, 1.9, -1.55, 180, reach=1.0, tool='claw')
    # gantry
    for x in (-3.8, 3.8):
        for s in (-1, 1):
            k.bx(x - 0.08, x + 0.08, s * 1.7 - 0.08, s * 1.7 + 0.08, 0, 4.2, 'steel2')
    k.bx(-3.9, 3.9, -1.8, -1.62, 4.2, 4.4, 'beam')
    k.bx(-3.9, 3.9, 1.62, 1.8, 4.2, 4.4, 'beam')
    for x in (-3.8, 3.8):
        k.bx(x - 0.09, x + 0.09, -1.62, 1.62, 4.2, 4.38, 'beam2')
    k.bx(-2.6, 2.6, -0.1, 0.1, 4.0, 4.2, 'steelDark', ink=False)        # light bar
    k.qz(-2.5, 2.5, -0.08, 0.08, 3.997, -1, 'lamp')
    k.cyl(3.8, -1.7, 4.4, 0.12, 0.12, 0.12, 'steelDark', seg=8)
    k.cyl(3.8, -1.7, 4.52, 0.1, 0.07, 0.2, 'hot', seg=8)
    # parts bin at the -X end, filled with this section's parts
    k.bx(-3.95, -3.25, 0.75, 1.45, 0, 0.6, 'bin2')
    k.bx(-3.9, -3.3, 0.8, 1.4, 0.6, 0.7, tc)
    k.col(-4.0, 4.0, -0.62, 0.62, 0, 1.05)
    for x in (-1.8, 1.9):
        pass
    k.col(-2.25, -1.35, 1.1, 2.0, 0, 1.2)
    k.col(1.45, 2.35, -2.0, -1.1, 0, 1.2)
    k.col(-3.95, -3.25, 0.75, 1.45, 0, 0.7)
    for x in (-3.8, 3.8):
        for s in (-1, 1):
            k.col(x - 0.08, x + 0.08, s * 1.7 - 0.08, s * 1.7 + 0.08, 0, 4.2)
    return k


def line_bot(k, kind):
    """A half-built robot riding the assembly line (origin = belt top)."""
    k.begin()
    if kind == 'CrawlerBare':
        crawler(k, 0.0, 0.0, 0.0, legs=1, top=False)
    elif kind == 'Crawler':
        crawler(k, 0.0, 0.0, 0.0, legs=3)
    elif kind == 'GunnerBare':
        gunner(k, 0.0, 0.0, 0.0, gun=False, deg=90)
    elif kind == 'Gunner':
        gunner(k, 0.0, 0.0, 0.0, gun=True, deg=90)
    elif kind == 'Bomber':
        bottle(k, 0.0, 0.0, 0.0, cap=True, base=True)
    else:
        drone(k, 0.0, 0.0, 0.0, arms=2, s=1.0, deg=0)
    return k


def catwalk(k):
    """Prefab 2 x 8 (along Y): overhead catwalk on posts at deck 4.0 m: grating deck, toe boards, handrails. Runs of
    them join end to end; robots and the player walk under it."""
    k.begin()
    D = 4.0
    for y in (-3.7, 3.7):
        for x in (-0.8, 0.8):
            k.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0, D - 0.1, 'hazard')
        k.bx(-0.9, 0.9, y - 0.1, y + 0.1, D - 0.3, D - 0.06, 'steel2')
        k.beam((-0.8, y, 0.6), (0.8, y, D - 0.4), 0.06, 'steelDark', ink=False)
    for x in (-0.86, 0.86):
        k.bx(x - 0.06, x + 0.06, -4.0, 4.0, D - 0.25, D - 0.05, 'steelDark')
    k.bx(-0.8, 0.8, -4.0, 4.0, D - 0.05, D, 'grate', ink=False)
    for i in range(16):
        y = -3.75 + i * 0.5
        k.qz(-0.78, 0.78, y - 0.02, y + 0.02, D + 0.003, 1, 'steel2')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.88, s * 0.93)
        k.bx(x0, x1, -4.0, 4.0, D, D + 0.15, 'hazard', ink=False)
        k.bx(x0, x1, -4.0, 4.0, D + 1.0, D + 1.06, 'hazard')
        k.bx(x0, x1, -4.0, 4.0, D + 0.55, D + 0.59, 'hazard2', ink=False)
        for y in (-3.5, -1.5, 0.5, 2.5):
            k.bx(x0 + 0.01, x1 - 0.01, y - 0.03, y + 0.03, D + 0.15, D + 1.0, 'hazard2', ink=False)
    for y in (-3.7, 3.7):
        for x in (-0.8, 0.8):
            k.col(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0, D)
    return k


def machine(k, kind):
    """Prefab 3 x 2 machine tool: CNC mill (lit window) or a parts lathe."""
    k.begin()
    if kind == 'Mill':
        k.bx(-1.3, 1.3, -0.8, 0.8, 0, 2.2, 'panel')
        k.bx(-1.32, 1.32, -0.82, 0.82, 2.2, 2.35, 'steel2')
        k.bx(-1.0, 0.5, -0.83, -0.8, 0.6, 1.9, 'mullion', ink=False)
        k.qy(-0.95, 0.45, 0.65, 1.85, -0.833, -1, 'screen2')
        k.qy(-0.6, -0.3, 0.75, 1.3, -0.836, -1, 'tin2')
        k.bx(0.7, 1.2, -1.0, -0.8, 1.0, 1.8, 'steelDark')
        k.qy(0.75, 1.15, 1.4, 1.7, -1.003, -1, 'screen')
        k.qy(0.78, 0.9, 1.1, 1.2, -1.003, -1, 'red')
        k.qy(0.98, 1.1, 1.1, 1.2, -1.003, -1, 'teal')
        k.stripes(-1.3, 1.3, 0.02, 0.2, -0.803, -1, 8)
        k.cyl(1.0, 0.4, 2.35, 0.08, 0.08, 0.5, 'steelDark', seg=6)
        k.cyl(1.0, 0.4, 2.85, 0.09, 0.09, 0.1, 'hot', seg=6, ink=False)
        k.col(-1.32, 1.32, -1.0, 0.82, 0, 2.35)
    else:
        k.bx(-1.4, 1.4, -0.5, 0.5, 0, 0.9, 'steel2')
        k.bx(-1.42, 1.42, -0.52, 0.52, 0.9, 0.98, 'steelDark')
        k.bx(-1.3, -0.6, -0.45, 0.45, 0.98, 1.7, 'panel')
        k.cyl(-0.6, 0.0, 1.35, 0.22, 0.22, 1.5, 'tin', seg=10, rot=(0, 90, 0))
        k.cyl(0.9, 0.0, 1.35, 0.14, 0.14, 0.35, 'steel', seg=8, rot=(0, 90, 0))
        k.bx(0.95, 1.35, -0.4, 0.4, 0.98, 1.6, 'panel')
        k.qy(-1.2, -0.7, 1.2, 1.55, -0.453, -1, 'screen')
        k.bx(-1.4, 1.4, -1.0, -0.5, 0, 0.03, 'grate', ink=False)
        k.col(-1.42, 1.42, -0.52, 0.52, 0, 1.7)
    return k


def robot_rack(k):
    """Prefab 6 x 2: shelving of finished robots (Crawlers below, Drones hung above) ready to ship."""
    k.begin()
    for x in (-2.9, -0.95, 0.95, 2.9):
        for y in (-0.85, 0.85):
            k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 4.0, 'beam')
    for z in (0.1, 1.6, 3.2):
        for y in (-0.85, 0.85):
            k.bx(-2.98, 2.98, y - 0.07, y + 0.07, z, z + 0.14, 'beam2')
        k.bx(-2.95, 2.95, -0.78, 0.78, z + 0.14, z + 0.18, 'grate', ink=False)
    for i, x in enumerate((-2.2, -0.75, 0.75, 2.2)):
        crawler(k, x, 0.0, 0.28, legs=4, s=0.9, deg=180)
        if i % 2 == 0:
            gunner(k, x, 0.0, 1.78, gun=True, s=0.8, deg=180)
        else:
            bottle(k, x, 0.0, 1.78, cap=True, s=0.9)
    for x in (-1.8, 0.0, 1.8):
        drone(k, x, 0.0, 3.38, arms=4, s=0.85, deg=180)
    k.col(-3.0, 3.0, -0.92, 0.92, 0, 4.0)
    return k


def test_cage(k):
    """Prefab 4 x 4: robot test cell: mesh fence, a turntable with a finished Gunner, a warning sign and beacon."""
    k.begin()
    k.qz(-1.9, 1.9, -1.9, 1.9, Z['test'], 1, 'hazard')
    k.qz(-1.6, 1.6, -1.6, 1.6, Z['test'] + 0.004, 1, 'conc2')
    for (x, y) in ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9), (0, 1.9), (-1.9, 0), (1.9, 0)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, 2.36, 'steelDark')
    for j, (x0, x1, y0, y1) in enumerate(((-1.9, 1.9, 1.88, 1.92), (-1.92, -1.88, -1.9, 1.9), (1.88, 1.92, -1.9, 1.9), (-1.9, -0.6, -1.92, -1.88), (0.6, 1.9, -1.92, -1.88))):
        k.bx(x0, x1, y0, y1, 0.1 + 0.005 * j, 2.19 - 0.004 * j, 'grate', ink=False)
        k.bx(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, 2.2 + 0.006 * j, 2.28 + 0.006 * j, 'hazard')
    k.cyl(0, 0.2, 0.0, 0.9, 0.9, 0.14, 'steel2', seg=12)
    gunner(k, 0, 0.2, 0.14, lid=True, gun=True, deg=-30)
    k.bx(-0.5, 0.5, -1.95, -1.91, 1.4, 1.9, 'label')
    k.qy(-0.4, 0.4, 1.5, 1.8, -1.953, -1, 'red')
    k.cyl(1.9, -1.9, 2.3, 0.1, 0.07, 0.2, 'hot', seg=8)
    k.col(-1.95, 1.95, 1.85, 1.95, 0, 2.3)
    k.col(-1.95, -1.85, -1.95, 1.95, 0, 2.3)
    k.col(1.85, 1.95, -1.95, 1.95, 0, 2.3)
    k.col(-1.95, -0.6, -1.95, -1.85, 0, 2.3)
    k.col(0.6, 1.95, -1.95, -1.85, 0, 2.3)
    k.col(-0.9, 0.9, -0.7, 1.1, 0, 1.2)
    return k


def hazard_floor(k, variant):
    k.begin()
    k.qz(-0.95, 0.95, -0.95, 0.95, Z['hazard'], 1, 'hazard')
    n = 6
    for i in range(n):
        a = -0.95 + i * 1.9 / n
        if i % 2:
            continue
        pts = [(a, -0.95, Z['hazard'] + 0.004), (a + 1.9 / n, -0.95, Z['hazard'] + 0.004)]
        if variant == 0:
            k.poly([(-0.95, a, Z['hazard'] + 0.004), (-0.95, a + 1.9 / n, Z['hazard'] + 0.004), (0.95, a + 1.9 / n, Z['hazard'] + 0.004), (0.95, a, Z['hazard'] + 0.004)], 'ink', (0, 0, 1))
        else:
            k.poly([(a, -0.95, Z['hazard'] + 0.004), (a + 1.9 / n, -0.95, Z['hazard'] + 0.004), (a + 1.9 / n, 0.95, Z['hazard'] + 0.004), (a, 0.95, Z['hazard'] + 0.004)], 'ink', (0, 0, 1))
    k.qz(-0.75, 0.75, -0.75, 0.75, Z['hazard'] + 0.008, 1, 'conc2')
    return k


def stand(k):
    k.begin()
    crate_body(k, 0.45, 0.4, 0.92, 'Closed')
    return k


# ================================================================ landmarks
def press(k):
    """Landmark 10 x 8: the giant stamping press (four columns, crown with cylinders, ram over a red-hot Gunner shell
    on the bolster) and the forge furnace beside it, under a soot hood."""
    k.begin()
    # bed / bolster
    k.bx(-3.4, 3.4, -2.2, 2.2, 0, 1.3, 'steelDark')
    k.stripes(-3.4, 3.4, 0.1, 0.5, -2.203, -1, 16)
    k.bx(-2.6, 2.6, -1.7, 1.7, 1.3, 1.6, 'steel2')
    k.bx(-1.4, 1.4, -1.0, 1.0, 1.6, 1.75, 'steel')
    gunner(k, 0.0, 0.0, 1.75, gun=False, s=1.1)
    # columns
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * 2.95 - 0.38, sx * 2.95 + 0.38, sy * 1.75 - 0.38, sy * 1.75 + 0.38, 1.0, 7.7, 'beam')
            k.qy(sx * 2.95 - 0.3, sx * 2.95 + 0.3, 1.5, 3.0, sy * 1.75 + sy * 0.383, sy, 'hazard')
    # ram (slide) with die, piston rods
    k.bx(-2.45, 2.45, -1.3, 1.3, 4.4, 5.6, 'steel2')
    k.bx(-1.5, 1.5, -1.0, 1.0, 4.1, 4.4, 'steelDark')
    k.stripes(-2.45, 2.45, 4.45, 4.75, -1.303, -1, 12)
    for x in (-1.3, 1.3):
        k.cyl(x, 0, 5.6, 0.22, 0.22, 2.0, 'steel', seg=8)
    # crown
    k.bx(-3.5, 3.5, -2.3, 2.3, 7.6, 9.3, 'beam')
    k.bx(-3.52, 3.52, -2.32, 2.32, 8.2, 8.35, 'beam2', ink=False)
    for x in (-1.3, 1.3):
        k.cyl(x, 0, 9.3, 0.65, 0.65, 0.6, 'steelDark', seg=10)
    k.bx(-0.9, 0.9, -2.33, -2.31, 8.5, 9.1, 'label')
    k.qy(-0.8, 0.8, 8.6, 9.0, -2.333, -1, 'ink')
    k.qy(-0.6, -0.2, 8.7, 8.9, -2.336, -1, 'core')
    k.qy(0.2, 0.6, 8.7, 8.9, -2.336, -1, 'core')
    # hot glow on the shell: orange star decals on the die face
    # forge furnace at -X
    FX = -4.3
    k.bx(FX - 0.7, FX + 0.6, -1.4, 1.4, 0, 2.6, 'brick')
    for z in (0.5, 1.0, 1.5, 2.0):
        k.qx(-1.4, 1.4, z - 0.02, z + 0.02, FX + 0.603, 1, 'brick2')
    k.bx(FX + 0.6, FX + 0.64, -0.6, 0.6, 0.6, 1.5, 'soot')
    k.qx(-0.5, 0.5, 0.65, 1.42, FX + 0.643, 1, 'hot')
    k.qx(-0.3, 0.3, 0.7, 1.2, FX + 0.646, 1, 'hot2')
    k.hullp([(FX - 0.8, -1.5, 2.6), (FX + 0.7, -1.5, 2.6), (FX + 0.7, 1.5, 2.6), (FX - 0.8, 1.5, 2.6),
             (FX - 0.4, -0.5, 4.2), (FX + 0.3, -0.5, 4.2), (FX + 0.3, 0.5, 4.2), (FX - 0.4, 0.5, 4.2)], 'soot')
    k.bx(FX - 0.35, FX + 0.25, -0.45, 0.45, 4.2, CEIL + 0.1, 'soot')
    pool_disc(k, FX + 1.6, 0.0, Z['furnace'], 1.2, 13, sx=0.9, sy=1.4, c1='hot2', c2='lampWarm')
    # control pendant and stamped shells at +X
    k.bx(4.0, 4.06, -0.5, -0.44, 1.2, 4.0, 'steelDark', ink=False)
    k.bx(3.85, 4.2, -0.65, -0.3, 0.9, 1.4, 'hazard')
    k.qy(3.92, 4.13, 1.15, 1.32, -0.653, -1, 'red')
    for i, (x, y) in enumerate(((4.3, 1.2), (4.1, 2.2), (3.6, 2.9))):
        gunner(k, x, y, 0.0, gun=False, s=0.9, deg=20 * i)
    # light curtain posts at the front corners
    for sx in (-1, 1):
        k.bx(sx * 3.7 - 0.06, sx * 3.7 + 0.06, -3.0, -2.88, 0, 1.9, 'hazard')
        k.qy(sx * 3.7 - 0.04, sx * 3.7 + 0.04, 0.4, 1.7, -3.003, -1, 'hot')
    pool_disc(k, 0.0, -3.1, Z['pressPool'], 1.3, 19, sx=2.0, sy=0.5)
    k.col(-3.5, 3.5, -2.3, 2.3, 0, 9.3)
    k.col(FX - 0.8, FX + 0.64, -1.5, 1.5, 0, 4.2)
    k.col(3.85, 4.2, -0.65, -0.3, 0, 1.4)
    k.col(3.2, 4.7, 0.7, 3.3, 0, 1.0)
    return k


def booth(k):
    """Landmark 8 x 6: the line supervisor's control booth on stilts: glazed on three sides, consoles and screens
    inside, a beacon on the roof, a steel stair up the +X side, cabinets underneath."""
    k.begin()
    X0, X1, Y0, Y1, B, T = -3.3, 2.2, -2.2, 2.2, 3.0, 5.6
    for (x, y) in ((X0 + 0.15, Y0 + 0.15), (X1 - 0.15, Y0 + 0.15), (X0 + 0.15, Y1 - 0.15), (X1 - 0.15, Y1 - 0.15)):
        k.bx(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, B, 'beam')
        k.stripes(x - 0.12, x + 0.12, 0.1, 1.2, y - 0.123, -1, 3)
    k.bx(X0, X1, Y0, Y1, B, B + 0.3, 'steelDark')
    k.bx(X0, X1, Y0, Y1, B + 0.3, B + 1.2, 'panel')                     # lower walls
    k.bx(X0, X1, Y0, Y1, T - 0.3, T, 'panel')                           # header
    k.bx(X0 - 0.15, X1 + 0.15, Y0 - 0.15, Y1 + 0.15, T, T + 0.15, 'steelDark')
    # glazing band (inset) with mullions, glints, screens behind
    k.bx(X0 + 0.05, X1 - 0.05, Y0 + 0.05, Y1 - 0.05, B + 1.2, T - 0.3, 'screen2')
    for x in (X0 + 0.05, -1.5, 0.3, X1 - 0.05):
        k.bx(x - 0.06, x + 0.06, Y0 - 0.01, Y0 + 0.1, B + 1.21, T - 0.31, 'mullion')
    for y in (-0.7, 0.7):
        k.bx(X0 - 0.01, X0 + 0.1, y - 0.06, y + 0.06, B + 1.21, T - 0.31, 'mullion')
    for (x0, x1) in ((-3.0, -2.0), (-1.2, -0.4), (0.6, 1.6)):
        k.qy(x0, x1, B + 1.3, B + 1.9, Y0 + 0.047, -1, 'screen')
        k.qy(x0 + 0.1, x0 + 0.5, B + 1.4, B + 1.5, Y0 + 0.044, -1, 'ink')
    k.poly([(-2.8, Y0 + 0.044, B + 2.1), (-2.6, Y0 + 0.044, B + 2.1), (-2.2, Y0 + 0.044, T - 0.4), (-2.4, Y0 + 0.044, T - 0.4)], 'glint', (0, -1, 0))
    k.poly([(0.7, Y0 + 0.044, B + 2.1), (0.8, Y0 + 0.044, B + 2.1), (1.2, Y0 + 0.044, T - 0.4), (1.1, Y0 + 0.044, T - 0.4)], 'glint', (0, -1, 0))
    k.cyl(-2.6, 1.4, T + 0.15, 0.14, 0.14, 0.12, 'steelDark', seg=8)
    k.cyl(-2.6, 1.4, T + 0.27, 0.12, 0.08, 0.26, 'hot', seg=8)
    k.bx(0.6, 1.6, Y0 - 0.02, Y0, T - 0.25, T - 0.05, 'label')
    k.qy(0.7, 1.5, T - 0.22, T - 0.08, Y0 - 0.023, -1, 'ink')
    # stair up the +X side to a landing
    k.bx(X1, X1 + 1.4, 0.4, 2.0, B + 0.1, B + 0.3, 'steelDark')
    n = 10
    for i in range(n):
        z = (i + 1) * B / (n + 1)
        y = -2.6 + i * (3.0 / n)
        k.bx(X1 + 0.3, X1 + 1.3, y, y + 0.28, z - 0.05, z, 'grate')
    for x in (X1 + 0.27, X1 + 1.33):
        k.beam((x, -2.75, 0.0), (x, 0.4, B + 0.1), 0.08, 'hazard')
        k.beam((x, -2.75, 1.0), (x, 0.4, B + 1.1), 0.05, 'hazard', ink=False)
    # cabinets under the booth
    for i, x in enumerate((-2.6, -1.4, -0.2)):
        k.bx(x - 0.55, x + 0.55, 1.2, 1.8, 0, 2.0, 'panel' if i % 2 == 0 else 'panelG')
        k.qy(x - 0.4, x + 0.4, 1.2, 1.7, 1.197, -1, 'panelG' if i % 2 == 0 else 'steel2')
        k.qy(x - 0.1, x + 0.1, 1.75, 1.85, 1.194, -1, 'teal')
    pool_disc(k, -0.5, -0.4, Z['booth'], 1.6, 31, sx=1.4, sy=0.9)
    k.col(X0 + 0.03, X0 + 0.27, Y0 + 0.03, Y0 + 0.27, 0, B)
    k.col(X1 - 0.27, X1 - 0.03, Y0 + 0.03, Y0 + 0.27, 0, B)
    k.col(X0 + 0.03, X0 + 0.27, Y1 - 0.27, Y1 - 0.03, 0, B)
    k.col(X1 - 0.27, X1 - 0.03, Y1 - 0.27, Y1 - 0.03, 0, B)
    k.col(-3.15, 0.35, 1.2, 1.8, 0, 2.0)
    k.col(X1 + 0.25, X1 + 1.35, -2.75, 2.0, 0, 1.6)
    k.col(X0, X1, Y0, Y1, B, T + 0.15)
    return k


# ================================================================ backdrop (seen through the clerestory)
def backdrop_works(k):
    """The works outside: one long slice (+-110 m along X, facing -Y) of sawtooth-roofed halls, smokestacks with
    puffs, a gas holder, a gantry crane and a water tower, under the dusk sky."""
    k.begin()
    rnd = random.Random(11)
    x = -112.0
    i = 0
    while x < 112:
        w = rnd.uniform(16, 26)
        h = rnd.uniform(12, 18)
        d = rnd.uniform(14, 22)
        k.bx(x, x + w - 1.0, 0.0 + (i % 3) * 0.3, d, -2.0 - 0.01 * (i % 4), h, 'far' if i % 2 else 'far2')
        n = int(w / 4)
        for j in range(n):                                      # sawtooth roof
            xx = x + j * (w - 1.0) / n
            ww = (w - 1.0) / n
            k.poly([(xx, 0.0 + (i % 3) * 0.3 - 0.02, h), (xx + ww, 0.0 + (i % 3) * 0.3 - 0.02, h), (xx + ww, 0.0 + (i % 3) * 0.3 - 0.02, h + 2.6)], 'far2' if i % 2 else 'far', (0, -1, 0))
        for j in range(max(1, int(w / 6))):                    # lit windows
            xx = x + 1.5 + j * 5.5
            if xx + 3 < x + w - 1:
                k.qy(xx, xx + 3.0, h * 0.45, h * 0.62, (i % 3) * 0.3 - 0.03, -1, 'farLit')
        if i % 3 == 1:                                          # stack with smoke
            sx = x + w * 0.6
            k.cyl(sx, d * 0.5, h, 1.6, 1.2, 26.0, 'brick2', seg=8)
            k.cyl(sx, d * 0.5, h + 23.0, 1.32, 1.32, 1.2, 'ink', seg=8, ink=False, caps=False)
            for m, (dx, dz, r) in enumerate(((0.5, 28.5, 2.6), (2.8, 31.0, 3.4), (6.2, 33.0, 4.2))):
                k.sph(sx + dx, d * 0.5, h + dz, r, 'smoke', seg=(7, 5), scale=(1, 0.8, 0.75))
        x += w
        i += 1
    # gas holder, gantry crane, water tower
    k.cyl(-40, 30, -2, 12, 12, 26, 'far', seg=14)
    k.cyl(-40, 30, 24, 12.4, 12.4, 0.8, 'far2', seg=14, ink=False)
    for xx in (14, 34):
        k.bx(xx - 0.8, xx + 0.8, -4, -2.4, -2, 30, 'beam2')
    k.bx(12, 36, -4.3, -2.1, 30, 32.5, 'beam')
    k.bx(22, 26, -4.6, -1.8, 26, 30, 'hazard')
    k.cyl(70, 12, 20, 5.0, 5.0, 7.0, 'far2', seg=10)
    k.cyl(70, 12, 27, 5.4, 0.4, 3.0, 'far', seg=10)
    for (dx, dy) in ((-3.5, -3.5), (3.5, -3.5), (-3.5, 3.5), (3.5, 3.5)):
        k.beam((70 + dx, 12 + dy, -2), (70 + dx * 0.8, 12 + dy * 0.8, 20), 0.5, 'far2', ink=False)
    return k


# ================================================================ build
def build_kit_factory(ao):
    pal = Palette(FAM)
    k = Kit(pal, PFX, HULL_T)
    for kind in ('Win_A', 'Win_B', 'Win_Panel', 'Win_Sign', 'Win_Vent', 'Win_Hose', 'Plain', 'Panel'):
        wall_module(k, kind).finish('Wall_' + kind, ao=ao)
    column(k).finish('Wall_Col', ao=ao)
    for side in ('L', 'R', 'LR'):
        end_module(k, side).finish('Wall_End' + side, ao=ao)
    corner(k).finish('Corner', ao=ao)
    for kind in ('Plain', 'Arrow', 'Num'):
        block_wall(k, kind).finish('Block_' + kind, ao=ao)
    ceil_truss(k).finish('CeilTruss')
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    trail_wall(k).finish('TrailWall', ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    for kind in ('Cans', 'Wheels', 'Closed', 'Lid'):
        crate(k, kind).finish('Crate_' + kind, ao=ao)
    for kind in ('Bins', 'Cans', 'Bottles'):
        pallet(k, kind).finish('Pallet_' + kind, ao=ao)
    for v in (0, 1):
        drums(k, v).finish('Drums_%s' % 'AB'[v], ao=ao)
        hazard_floor(k, v).finish('Hazard_%s' % 'AB'[v])
    gas_rack(k).finish('GasRack', ao=ao)
    conveyor(k).finish('Conveyor', ao=ao)
    for kind in ('Feed', 'Exit'):
        belt_hood(k, kind).finish('Conveyor_' + kind, ao=ao)
        belt_hood(k, kind, L=0.6, W=0.68, H=2.12, rail=0.96, base=0.0).finish('Line_' + kind, ao=ao)
    belt_cleat(k, 0.36).finish('Belt_Cleat')
    belt_cleat(k, 0.44).finish('Line_Cleat')
    for kind in ('Can', 'Bottle', 'Drone', 'Wheels'):
        belt_item(k, kind).finish('Item_' + kind, ao=ao)
    for kind in ('CrawlerBare', 'Crawler', 'GunnerBare', 'Gunner', 'Bomber', 'Drone'):
        line_bot(k, kind).finish('LineBot_' + kind, ao=ao)
    tool_station(k, 'Screen').finish('WeldScreen', ao=ao)
    tool_station(k, 'Chest').finish('ToolChest', ao=ao)
    arm_cell(k, 'A').finish('Arm_A', ao=ao)
    arm_cell(k, 'B').finish('Arm_B', ao=ao)
    for kind in ('Crawler', 'Gunner', 'Bomber', 'Drone'):
        assembly_line(k, kind).finish('Line_' + kind, ao=ao)
    catwalk(k).finish('Catwalk', ao=ao)
    machine(k, 'Mill').finish('Machine_Mill', ao=ao)
    machine(k, 'Lathe').finish('Machine_Lathe', ao=ao)
    robot_rack(k).finish('Landmark_RobotRack', ao=ao)
    test_cage(k).finish('TestCage', ao=ao)
    press(k).finish('Landmark_Press', ao=ao)
    booth(k).finish('Landmark_Booth', ao=ao)
    backdrop_works(k).finish('Backdrop_Works')
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_factory
