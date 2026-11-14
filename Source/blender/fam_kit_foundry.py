"""INKBOLT asset family: kit-foundry (Titan Foundry: the enemy's war foundry, where new robot chassis and the giant
titans are built).

Bigger and darker than Robot Works / Heavy Works (fam_kit_factory.py, fam_kit_factory2.py): 30 m halls of indigo
gunmetal plate over slate concrete plinths, stepped buttresses every 8 m with red warning beacons and stencilled bay
numbers, a crane girder at 24 m, a glowing louvre band high under the roof, crimson war banners (chevrons and stripes,
no emblems). Roof bays: deep plate girders with floodlight clusters, some with bridge cranes or long war banners.

On the floor the new chassis (foundry_bots.py) in production: a moving line of six-legged spider walkers through
fitting tunnels, hover tanks and hounds on a second line, hover tanks and drone-carrier gunships riding an overhead
monorail, weld cells, chassis jigs, test cells, a centipede crawler on its assembly rack, spare reactor cores, and in
the launch hall rows of finished robots on their pads. The giants (foundry_giants.py): the WARDEN titan as a bare
frame on its jig, half armoured with its reactor glowing under a gantry walkway, and finished on its launch sled; the
STRIDER siege quad half built and finished; sealed launch doors.

Conventions: see foundry_common.py. Moving pieces (Spider_*, Hover_*, Hound_*, Carrier_*, Line_Slat) are animated by
the engine (theme symbol option `conveyor`).
"""
import math
import random

from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import shutter_hull
from foundry_common import (FAM, PFX, HULL_T, CEIL, WALL_H, ROOF, Z, FK, srt, slab, slab3, oslab, tube, drumx, drumy,
                            stencil_digit, stencil_num, stencil_x, floor_digit, chevrons_y, spark_star, spark_spray, pool_disc,
                            beacon, floodlamp, downlamp, cable, guard_rail, robot_arm, rivet_row)
from foundry_bots import skid, spider, hover, hound, gunship, centipede
import foundry_giants as GI
import fd_detail as FD

V = Vector

# ================================================================ walls
PL = 0.12      # plinth proud
GD = 0.36      # girder proud
GZ0, GZ1 = 24.0, 25.2   # crane girder band
VZ0, VZ1 = 27.0, 28.4   # louvre light band


def strip(k, a, b, d, z0, z1, c, top=True, bot=True, endL=False, endR=False):
    """A detail standing d proud of the wall face (y = -0.5) from x = a to b, drawn as its visible faces only (front,
    top, bottom, and an end face where a run stops): wall modules repeat hundreds of times per zone."""
    y = -0.5 - d
    k.qy(a, b, z0, z1, y, -1, c)
    if top:
        k.qz(a, b, y, -0.5, z1, 1, c)
    if bot:
        k.qz(a, b, y, -0.5, z0, -1, c)
    if endL:
        k.qx(y, -0.5, z0, z1, a, -1, c)
    if endR:
        k.qx(y, -0.5, z0, z1, b, 1, c)


def wall_body(k, cutL=0.0, cutR=0.0, girder=True, vents=True, seams=True):
    """One 1 m wall module, room face at y = -0.5: slate concrete plinth with a hazard foot, plate courses with seams
    and rivets, the crane girder band, the glowing louvre band, a dark roof edge. cutL / cutR shorten everything proud
    on that side (beside an inside corner, so the neighbouring wall's details never overlap; the corner post fills it).
    Only faces that can be seen are drawn (the module is flat detail, no outline shell)."""
    k.qy(-0.5, 0.5, 0.0, WALL_H, -0.5, -1, 'slate')
    k.qz(-0.5, 0.5, -0.5, 0.5, WALL_H, 1, 'ceil')
    k.qy(-0.5, 0.5, 0.0, WALL_H - 0.4, 0.5, 1, 'slate2')
    a, b = -0.5 + cutL, 0.5 - cutR
    eL, eR = cutL > 0, cutR > 0
    strip(k, a, b, PL, 0.0, 4.0, 'conc', bot=False, endL=eL, endR=eR)
    for z in (1.3, 2.6):
        k.qy(a, b, z - 0.02, z + 0.02, -0.5 - PL - 0.003, -1, 'conc2')
    k.stripes(a, b, 0.03, 0.42, -0.5 - PL - 0.003, -1, 4, ca='hazard')
    strip(k, a, b, PL + 0.06, 4.0, 4.16, 'steelDark', endL=eL, endR=eR)
    if seams:
        for z in (8.0, 12.0, 16.0, 20.0):
            k.qy(a, b, z - 0.025, z + 0.025, -0.503, -1, 'slate2')
        for z in (8.0, 16.0):
            rivet_row(k, a, b, z - 0.12, -0.503, -1, 3, c='slate2', r=0.025)
    if girder:
        strip(k, a, b, GD, GZ0, GZ0 + 0.18, 'gun2', endL=eL, endR=eR)
        strip(k, a, b, GD - 0.08, GZ0 + 0.18, GZ1 - 0.18, 'steelDark', top=False, bot=False, endL=eL, endR=eR)
        strip(k, a, b, GD, GZ1 - 0.18, GZ1, 'gun2', endL=eL, endR=eR)
        k.qy(a, b, GZ0 + 0.04, GZ0 + 0.14, -0.5 - GD - 0.003, -1, 'hazard')
    if vents:
        strip(k, a, b, 0.08, VZ0 - 0.12, VZ0, 'steelDark', endL=eL, endR=eR)
        k.qy(a + 0.04, b - 0.04, VZ0 + 0.05, VZ1 - 0.05, -0.503, -1, 'lampW')
        for i in range(4):
            z = VZ0 + 0.2 + i * 0.32
            k.qy(a, b, z, z + 0.1, -0.56, -1, 'slate2')
        strip(k, a, b, 0.08, VZ1, VZ1 + 0.12, 'steelDark', endL=eL, endR=eR)
    strip(k, a, b, 0.1, WALL_H - 0.5, WALL_H - 0.004, 'ceil', top=False, endL=eL, endR=eR)


def wall_module(k, kind, cutL=0.0, cutR=0.0, num=None):
    k.begin()
    near_gate = kind in ('GateIn', 'Gate')
    wall_body(k, cutL=cutL, cutR=cutR, girder=kind not in ('GateIn', 'Back'), vents=kind != 'Back', seams=kind != 'Back')
    if kind == 'Pipes':
        for x, r, c in ((-0.26, 0.12, 'steel2'), (0.02, 0.09, 'crimson'), (0.26, 0.07, 'hose')):
            k.cyl(x, -0.62 - r, 4.16, r, r, GZ0 - 4.16, c, seg=8, ink=False)
        for z in (7.0, 13.0, 19.0):
            k.bx(-0.45, 0.45, -0.9, -0.503, z, z + 0.12, 'steelDark', ink=False)
    elif kind == 'Duct':
        k.bx(-0.36, 0.36, -0.95, -0.5, 4.16, GZ0, 'steel2')
        for z in (6.0, 11.0, 16.0, 21.0):
            k.bx(-0.4, 0.4, -0.99, -0.52, z, z + 0.14, 'steelDark', ink=False)
        k.qy(-0.26, 0.26, 4.5, 5.4, -0.953, -1, 'steelDark')
    elif kind == 'Panel':
        k.bx(-0.4, 0.3, -0.85, -0.5 - PL, 0.9, 2.6, 'gun')
        k.qy(-0.32, 0.22, 1.75, 2.35, -0.853, -1, 'screen')
        k.qy(-0.32, -0.08, 1.05, 1.55, -0.853, -1, 'hazard')
        k.qy(0.0, 0.22, 1.05, 1.55, -0.853, -1, 'steelDark')
        k.bx(-0.06, 0.06, -0.6, -0.503, 4.16, 9.0, 'steelDark', ink=False)
        beacon(k, 0.36, -0.75, 2.75, c='alarm', r=0.08, h=0.14)
    elif kind.startswith('Ban'):
        # war banner across three modules: rod, crimson cloth with a black border and bone chevrons, V tail
        side = kind[3]
        y = -0.62
        k.bx(-0.5, 0.5, -0.66, -0.58, GZ0 - 0.5, GZ0 - 0.38, 'steelDark', ink=False)
        lo = {'L': (10.6, 9.9), 'M': (9.9, 8.8), 'R': (9.9, 10.6)}[side]   # bottom edge z at local x -0.5 / +0.5
        if side == 'M':
            pts = [(-0.5, y, lo[0]), (0.0, y, lo[1]), (0.5, y, lo[0]), (0.5, y, GZ0 - 0.55), (-0.5, y, GZ0 - 0.55)]
        else:
            pts = [(-0.5, y, lo[0]), (0.5, y, lo[1]), (0.5, y, GZ0 - 0.55), (-0.5, y, GZ0 - 0.55)]
        k.poly(pts, 'crimson', (0, -1, 0))
        yb = y - 0.003
        if side in 'LR':
            xb = -0.5 if side == 'L' else 0.32
            k.qy(xb, xb + 0.18, min(lo) + 0.6, GZ0 - 1.5, yb, -1, 'banner2')
        k.qy(-0.5, 0.5, GZ0 - 1.45, GZ0 - 1.15, yb, -1, 'banner2')
        yb = yb - 0.003
        for i in range(3):
            z = 19.0 - i * 2.3
            if side == 'M':
                k.poly([(-0.5, yb, z), (0.0, yb, z - 1.0), (0.5, yb, z), (0.5, yb, z + 0.45), (0.0, yb, z - 0.55), (-0.5, yb, z + 0.45)], 'bone', (0, -1, 0))
            elif side == 'L':
                k.poly([(-0.5, yb, z + 0.5), (0.5, yb, z), (0.5, yb, z + 0.45), (-0.5, yb, z + 0.95)], 'bone', (0, -1, 0))
            else:
                k.poly([(-0.5, yb, z), (0.5, yb, z + 0.5), (0.5, yb, z + 0.95), (-0.5, yb, z + 0.45)], 'bone', (0, -1, 0))
    elif kind == 'Num':
        k.qy(-0.42, 0.42, 11.2, 15.3, -0.506, -1, 'gun')
        stencil_digit(k, num, -0.3, 11.6, 0.6, 3.3, -0.506, -1, c='bone')
    elif kind == 'Hose':
        k.bx(-0.3, 0.3, -0.82, -0.5 - PL, 1.2, 2.2, 'crimson')
        k.qy(-0.2, 0.2, 1.45, 1.95, -0.823, -1, 'rubber')
        k.qy(-0.22, 0.22, 2.3, 2.52, -0.506 - PL, -1, 'crimson')
    FD.wall_extra(k, -0.5 + cutL, 0.5 - cutR, -0.5 - PL, seam=kind in ('Plain', 'Hose', 'Gate', 'GateIn'))
    if kind == 'Num':
        FD.num_plate(k)
    return k


def pilaster(k):
    """Buttress every 8 m: a stepped concrete-and-steel pier to the roof, hazard chevrons at its foot, beacons on
    brackets, a stencilled bay plate; it carries the crane girder on a corbel."""
    k.begin()
    wall_body(k, girder=True)
    k.bx(-0.48, 0.48, -1.75, -0.5 - PL, 0.0, 5.0, 'conc')
    chevrons_y(k, -0.44, 0.44, 0.15, 1.4, -1.753, -1, 2, ca='hazard', cb='ink')
    for f in (-1, 1):
        k.qx(-1.7, -0.7, 0.15, 1.4, f * 0.483, f, 'hazard')
    k.bx(-0.5, 0.5, -1.82, -0.5 - PL, 5.0, 5.3, 'steelDark')
    k.bx(-0.4, 0.4, -1.4, -0.5 - GD, 5.3, GZ0 - 0.6, 'gun')
    k.bx(-0.44, 0.44, -1.5, -0.5 - GD, GZ0 - 0.6, GZ1 + 0.3, 'gun2')                      # corbel
    k.bx(-0.36, 0.36, -1.2, -0.5 - GD, GZ1 + 0.3, WALL_H - 0.5, 'gun')
    for z in (9.0, 17.0):
        k.bx(-0.12, 0.12, -1.75, -1.4, z - 0.15, z, 'steelDark')
        beacon(k, 0.0, -1.58, z, c='alarm', r=0.14, h=0.24)
    k.qy(-0.3, 0.3, 6.2, 8.4, -1.403, -1, 'bone')
    k.qy(-0.26, 0.26, 6.25, 8.35, -1.406, -1, 'crimson')
    for z in (11.0, 14.0, 20.0):
        k.qy(-0.4, 0.4, z - 0.03, z + 0.03, -1.403, -1, 'gun2')
    floodlamp(k, 0.0, -1.5, GZ0 - 1.4, w=0.6, h=0.4, s=-1, c='lamp')
    FD.pilaster_extra(k)
    k.col(-0.5, 0.5, -1.82, -0.5, 0.0, 5.3)          # the theme sets wall.cols: the buttress collides
    k.col(-0.44, 0.44, -1.5, -0.5, 5.3, WALL_H)
    return k


def corner(k, which):
    """Inside zone corner: a concrete corner post reaching into the room diagonal (the walls' details stop 0.42 m
    short of it)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0.0, WALL_H, 'conc2')
    sx = 1 if which[1] == 'W' else -1      # the room lies toward +X of a west corner
    sy = -1 if which[0] == 'N' else 1      # Blender -Y = game +Z = south: a north corner's room lies toward -Y
    x0, x1 = srt(sx * 0.5, sx * 0.9)
    y0, y1 = srt(sy * 0.5, sy * 0.9)
    k.bx(x0, x1, y0, y1, 0.0, WALL_H - 0.5, 'conc')
    k.stripes(*srt(sx * 0.5, sx * 0.9), 0.1, 1.6, y1 + 0.003 if sy > 0 else y0 - 0.003, 1 if sy > 0 else -1, 2, ca='hazard')
    return k


# ================================================================ roof bays (12 x 12 at the ceiling plane)
def ceil_bay(k, kind):
    """12 x 12 m roof bay at the ceiling plane (its parts within +-4.2 m, clear of the buttress tops): two deep plate
    girders along X, cross beams, purlins, a floodlight cluster (its pool painted on the floor 30 m below), a warning
    beacon; 'Crane': a bridge crane with a titan shin plate on the hook; 'Banner': long war banners hanging 12 m."""
    k.begin()
    D = -CEIL
    E = 4.2
    for y in (-3.0, 3.0):
        k.bx(-E, E, y - 0.28, y + 0.28, -2.6, -0.02, 'gun2')
        k.bx(-E, E, y - 0.42, y + 0.42, -2.75, -2.6, 'steelDark')
        for x in (-3.0, 0.0, 3.0):
            k.qy(x - 0.06, x + 0.06, -2.5, -0.15, y - 0.283, -1, 'steelDark')
    for x in (-3.6, 0.0, 3.6):
        k.bx(x - 0.16, x + 0.16, -E, E, -1.4, -0.06, 'steelDark')
    for y in (-3.9, -1.5, 1.5, 3.9):
        k.bx(-E + 0.05, E - 0.05, y - 0.07, y + 0.07, -0.5, -0.1, 'steel2', ink=False)
    for (x, y) in ((-2.4, -1.4), (2.4, -1.4), (-2.4, 1.4), (2.4, 1.4)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, -3.4, -1.4, 'steelDark', ink=False)
        downlamp(k, x, y, -4.0, r=0.62)
    k.bx(-2.6, 2.6, -1.6, 1.6, -3.42, -3.3, 'steelDark')
    k.cyl(3.9, -3.0, -3.15, 0.18, 0.12, 0.39, 'alarm', seg=8)
    pool_disc(k, 0.0, 0.0, D + Z['pool'], 4.2, 3, sx=1.2, sy=0.9)
    if kind == 'Crane':
        for x in (-3.8, 3.8):
            k.bx(x - 0.3, x + 0.3, -E, E, -3.4, -2.75, 'steelDark')
        for f in (-1, 1):
            k.bx(-4.0, 4.0, f * 0.5 - 0.2, f * 0.5 + 0.2, -4.3, -3.4, 'hazard')
        k.stripes(-3.6, 3.6, -4.2, -3.5, -0.703, -1, 10)
        k.bx(0.4, 2.0, -1.0, 1.0, -4.8, -4.3, 'hazard2')
        for dx in (-0.12, 0.12):
            k.bx(1.2 + dx - 0.02, 1.2 + dx + 0.02, -0.02, 0.02, -8.6, -4.8, 'steelDark', ink=False)
        k.bx(0.9, 1.5, -0.18, 0.18, -8.9, -8.6, 'hazard')
        oslab(k, V((1.2, -1.6, -9.4)), V((1.2, 2.2, -9.6)), 0.75, 0.45, 0.95, 0.5, 'bone', ch=0.2)
        oslab(k, V((1.2, -1.5, -9.0)), V((1.2, 2.1, -9.2)), 0.55, 0.12, 0.7, 0.15, 'crimson', ch=0.06)
        for dx, dy in ((1.05, -1.2), (1.35, 1.6)):
            k.beam((dx, 0.0, -8.9), (dx, dy, -9.05), 0.035, 'steelDark', ink=False)
    elif kind == 'Banner':
        for y in (-3.0, 3.0):
            for x in (-2.6, 2.6):
                k.bx(x - 1.0, x + 1.0, y - 0.05, y + 0.05, -2.95, -2.75, 'steelDark', ink=False)
                k.bx(x - 0.95, x + 0.95, y - 0.02, y + 0.02, -14.0, -2.95, 'crimson', ink=False)
                for f in (-1, 1):
                    yy = y + f * 0.023
                    k.qy(x - 0.95, x + 0.95, -4.4, -4.0, yy, f, 'banner2')
                    for i in range(3):
                        z = -7.0 - i * 2.2
                        k.poly([(x - 0.95, yy, z), (x, yy, z - 0.9), (x + 0.95, yy, z), (x + 0.95, yy, z + 0.4), (x, yy, z - 0.5), (x - 0.95, yy, z + 0.4)], 'bone', (0, f, 0))
                    k.poly([(x - 0.95, yy, -14.0), (x, yy, -15.2), (x + 0.95, yy, -14.0)], 'crimson', (0, f, 0))
    return k


# ================================================================ gate, trail, hatch, stand
def gate_frame(k):
    """Hall gate: hazard-striped posts, a crimson header with beacons and the zone board, the slate infill to the roof
    (the crane girder and the louvre band run across it)."""
    k.begin()
    HD = 3.1
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.2)
        k.bx(x0, x1, -0.75, 0.75, 0.0, HD, 'gun2')
        for f in (-1, 1):
            k.stripes(x0 + 0.06, x1 - 0.06, 0.1, HD - 0.2, f * 0.753, f, 4)
    k.bx(-2.45, 2.45, -0.85, 0.85, HD, HD + 1.5, 'crimson2')
    k.bx(-2.45, 2.45, -0.25, 0.25, HD + 1.5, WALL_H + 0.03, 'slate')
    for f in (-1, 1):
        y = f * 0.253
        for z in (8.0, 12.0, 16.0, 20.0):
            k.qy(-2.45, 2.45, z - 0.025, z + 0.025, y, f, 'slate2')
        yb = f * 0.853
        k.qy(-2.3, 2.3, HD + 1.25, HD + 1.38, yb, f, 'hazard')
        k.qy(-2.3, 2.3, HD + 0.12, HD + 0.25, yb, f, 'hazard')
        k.bx(-0.95, 0.95, *srt(f * 0.85, f * 0.9), HD + 1.5, HD + 2.9, 'bone')
        stencil_num(k, (1, 8), -0.7, HD + 1.7, 0.5, 1.0, 0.4, f * 0.903, f, c='crimson2')
        beacon(k, 2.0, f * 0.55, HD + 1.5, c='alarm', r=0.14)
        beacon(k, -2.0, f * 0.55, HD + 1.5, c='alarm', r=0.14)
        FD.gate_extra(k, HD, f)
        # the crane girder band and the louvre band run across the gate infill
        y0, y1 = srt(f * 0.25, f * (0.25 + GD))
        k.bx(-2.45, 2.45, y0, y1, GZ0, GZ1, 'gun2', ink=False)
        k.qy(-2.45, 2.45, GZ0 + 0.04, GZ0 + 0.14, f * (0.25 + GD + 0.003), f, 'hazard')
        y0, y1 = srt(f * 0.25, f * 0.33)
        k.bx(-2.45, 2.45, y0, y1, VZ0 - 0.12, VZ1 + 0.12, 'steelDark', ink=False)
    return k


def gate_shutter(k):
    k.begin()
    Hs, n = 3.05, 10
    h = (Hs - 0.4) / n
    for i in range(n):
        z0 = 0.4 + i * h
        k.bx(-1.5, 1.5, -0.07, 0.07, z0, z0 + h, 'gun' if i % 2 else 'gun2', ink=False)
    for f in (-1, 1):
        for x in (-1.0, 0.0, 1.0):
            k.qy(x - 0.3, x + 0.3, 2.1, 2.25, f * 0.073, f, 'steelDark')
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.08, 0.08, 0, 0.4, 'ink' if j % 2 else 'hazard', ink=False)
    return k


def trail_wall(k):
    """Service corridor wall (1 m along Blender Y, corridor toward +X): concrete plinth, pipes, half the lowered
    ceiling with a strip light, the slate exterior on the back."""
    k.begin(90)
    k.bx(-0.5, 0.5, -0.25, 0.25, 0, WALL_H, 'slate')
    k.bx(-0.5, 0.5, -0.3, -0.25, 0, 2.4, 'conc', ink=False)
    k.stripes(-0.5, 0.5, 0.03, 0.3, -0.303, -1, 4, ca='hazard')
    k.bx(-0.5, 0.5, -0.34, -0.25, 2.4, 2.5, 'steelDark', ink=False)
    for zz, r, c in ((3.0, 0.1, 'steel2'), (3.4, 0.07, 'crimson'), (3.72, 0.05, 'hose')):
        k.cyl(-0.5, -0.45 - r, zz, r, r, 1.0, c, seg=6, rot=(0, 90, 0), ink=False)
    k.bx(-0.03, 0.03, -0.62, -0.25, 2.8, 3.9, 'steelDark', ink=False)
    y_mid = -2.25 + 0.003
    k.bx(-0.5, 0.5, y_mid, -0.25, ROOF, ROOF + 0.08, 'ceil', ink=False)
    k.bx(-0.5, 0.5, -1.75, -1.45, ROOF - 0.08, ROOF, 'steelDark', ink=False)
    k.qz(-0.5, 0.5, -1.7, -1.5, ROOF - 0.083, -1, 'lampW')
    k.qz(-0.5, 0.5, -0.75, -0.4, 0.012, 1, 'hazard')
    k.qy(-0.5, 0.5, 0.0, WALL_H - 0.4, 0.253, 1, 'slate2')
    return k


def hatch(k):
    """Exit: the freight lift down to the next hall. Chevron pad, a platform under a lift shaft that closes the roof."""
    k.begin()
    k.bx(-1.2, 1.2, -1.25, 1.0, 0, 0.05, 'steel2')
    for i in range(4):
        y = -1.15 + i * 0.5
        k.poly([(-0.9, y, 0.053), (0, y + 0.3, 0.053), (0.9, y, 0.053), (0.9, y + 0.14, 0.053), (0, y + 0.44, 0.053), (-0.9, y + 0.14, 0.053)], 'cyan' if i % 2 else 'crimson', (0, 0, 1))
    C0, C1, W = 1.05, 2.68, 1.3
    k.bx(-W, W, C0, C1, 0, 0.14, 'steelDark')
    k.qz(-W + 0.05, W - 0.05, C0 + 0.02, C0 + 0.14, 0.143, 1, 'hazard')
    for x in (-W, W):
        k.bx(x - 0.07, x + 0.07, C0 - 0.07, C0 + 0.07, 0.14, ROOF - 0.05, 'crimson')
        k.bx(x - 0.07, x + 0.07, C1 - 0.12, C1 - 0.02, 0.14, ROOF - 0.05, 'crimson')
        k.stripes(x - 0.07, x + 0.07, 0.2, 1.6, C0 - 0.073, -1, 4)
    k.bx(-W + 0.075, W - 0.075, C1 - 0.06, C1, 0.16, 3.0, 'steel2')
    k.bx(-W - 0.07, W + 0.07, C0 - 0.08, C1, ROOF - 0.05, ROOF + 0.1, 'crimson2')
    k.bx(-0.6, 0.6, C1 - 0.1, C1 - 0.06, 3.2, 3.8, 'bone')
    k.qy(-0.5, 0.5, 3.3, 3.7, C1 - 0.103, -1, 'ink')
    k.qy(-0.42, -0.1, 3.4, 3.6, C1 - 0.106, -1, 'cyan')
    k.qy(0.1, 0.42, 3.4, 3.6, C1 - 0.106, -1, 'alarm')
    k.cyl(W - 0.2, C0 + 0.1, ROOF + 0.1, 0.1, 0.08, 0.18, 'alarm', seg=8)
    for s in (-1, 1):
        x0, x1 = srt(s * 0.77, s * 0.95)
        k.bx(x0, x1, -1.55, 2.72, ROOF + 0.12, WALL_H - 0.04, 'slate2')
    k.bx(-0.9, 0.9, -1.53, -0.97, ROOF + 0.13, WALL_H - 0.05, 'slate2')
    pool_disc(k, 0.0, 1.8, Z['hatch'], 1.2, 7)
    return k


def stand(k):
    """Weapon stand: a steel rack trestle the new guns lean on."""
    k.begin()
    k.bx(-0.55, 0.55, -0.3, 0.3, 0.0, 0.12, 'steelDark')
    for x in (-0.45, 0.45):
        k.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.12, 1.0, 'hazard')
    k.bx(-0.48, 0.48, -0.06, 0.06, 0.88, 0.98, 'crimson')
    return k


# ================================================================ moving chassis line [12, 8]
TL = 6.0          # half tile length
LW = 3.6          # fence line
ST0, ST1 = 1.2, 5.8   # fitting tunnel (station swap at 3.5)


def line_base(k):
    k.qz(-TL, TL, -1.45, 1.45, Z['line'], 1, 'pit')
    k.qz(-TL, TL, -0.12, 0.12, Z['line'] + 0.004, 1, 'cyanD')
    for f in (-1, 1):
        k.qz(-TL, TL, *srt(f * 1.55, f * 1.7), Z['line'], 1, 'hazard')
        k.bx(-TL, TL, *srt(f * 0.98, f * 1.12), 0.0, 0.12, 'steel')
        for x in (-5.0, -3.0, -1.0, 1.0, 3.0, 5.0):
            k.bx(x - 0.06, x + 0.06, *srt(f * (LW - 0.06), f * (LW + 0.06)), 0.0, 1.5, 'hazard')
            FD.fence_plate(k, x, f * LW)
        k.bx(-TL, TL, *srt(f * (LW - 0.012), f * (LW + 0.012)), 0.18, 1.32, 'steel2', ink=False)
        for x in (-4.0, -2.0, 0.0, 2.0, 4.0):
            k.qy(x - 0.6, x + 0.6, 0.5, 1.0, f * (LW + 0.015), f, 'slate2')
        k.bx(-TL, TL, *srt(f * (LW - 0.035), f * (LW + 0.035)), 1.32, 1.42, 'crimson')
        k.bx(-TL, TL, *srt(f * (LW - 0.04), f * (LW + 0.04)), 0.0, 0.18, 'gun2', ink=False)
    k.col(-TL, TL, -LW - 0.06, LW + 0.06, 0, 1.5)
    k.col(-TL, TL, -1.8, 1.8, 1.5, 4.8)


def tunnel(k, n):
    """Fitting tunnel over the lane (ST0..ST1): slate walls with a crimson band, a chamfered roof, cyan scanner frames
    at both mouths, strip curtains, robot arms on the roof reaching in, sparks spilling out, a stage number."""
    H, W = 5.4, 2.8
    x0, x1 = ST0, ST1
    for f in (-1, 1):
        y0, y1 = srt(f * W, f * (W + 0.18))
        k.bx(x0, x1, y0, y1, 0.0, H, 'slate')
        yo = f * (W + 0.183)
        k.qy(x0 + 0.05, x1 - 0.05, 2.6, 3.1, yo, f, 'crimson')
        k.qy(x0 + 0.05, x1 - 0.05, 0.05, 0.5, yo, f, 'conc2')
        stencil_digit(k, n, x0 + 1.9, 3.5, 0.6, 1.2, yo, f, c='bone')
        for xx in (x0 + 0.6, x1 - 0.6):
            k.qy(xx - 0.05, xx + 0.05, 0.6, H - 0.4, yo + f * 0.003, f, 'slate2')
        FD.tunnel_rivets(k, x0, x1, yo, f)
    k.hullp([(x0 - 0.05, -W - 0.25, H), (x1 + 0.05, -W - 0.25, H), (x0 - 0.05, W + 0.25, H), (x1 + 0.05, W + 0.25, H),
             (x0 - 0.05, -W + 0.5, H + 0.9), (x1 + 0.05, -W + 0.5, H + 0.9), (x0 - 0.05, W - 0.5, H + 0.9), (x1 + 0.05, W - 0.5, H + 0.9)], 'gun2')
    for xm, sg in ((x0, 1), (x1, -1)):
        a, b = srt(xm - sg * 0.12, xm + sg * 0.2)
        for f in (-1, 1):
            k.bx(a, b, *srt(f * (W - 0.12), f * (W + 0.26)), 0.0, H - 0.05, 'gun')
        k.bx(a - 0.03, b + 0.03, -W - 0.28, W + 0.28, H - 0.6, H + 0.06, 'gun')
        xf = xm - sg * 0.123
        k.qx(-W + 0.05, W - 0.05, H - 0.5, H - 0.38, xf, -sg, 'cyan')
        for f in (-1, 1):
            k.qx(*srt(f * (W - 0.1), f * (W + 0.2)), 0.4, H - 0.65, xf, -sg, 'cyanD')
        xc = xm + sg * 0.3
        for i in range(8):
            yy = -W + 0.15 + (2 * W - 0.3) * (i + 0.5) / 8
            k.bx(xc - 0.012 - 0.006 * (i % 2), xc + 0.012 - 0.006 * (i % 2), yy - 0.3, yy + 0.3, 0.45, H - 0.62, 'rubber', ink=False)
        spark_spray(k, xm - sg * 0.3, -1.6, 1.6, 0.28, s=-1, seed=n * 7 + sg)
    for (xa, f) in ((x0 + 1.4, -1), (x1 - 1.4, 1)):
        robot_arm(k, xa, f * 1.6, 90 - 90 * f, z=H + 0.9, reach=0.8, tool='weld' if f < 0 else 'claw', s=0.9)
    beacon(k, (x0 + x1) / 2, 0.0, H + 0.9, c='alarm', r=0.18)
    k.col(x0 - 0.12, x1 + 0.12, -W - 0.28, W + 0.28, 0, H + 0.9)


def house(k, feed, H=6.2, W=2.9):
    if feed:
        x0, x1, closed, mouth, sg = -TL, -TL + 4.0, -TL, -TL + 4.0, 1
    else:
        x0, x1, closed, mouth, sg = TL - 4.0, TL, TL, TL - 4.0, -1
    for f in (-1, 1):
        k.bx(x0, x1, *srt(f * W, f * (W + 0.2)), 0.0, H, 'gun')
        yo = f * (W + 0.203)
        k.qy(x0 + 0.3, x1 - 0.3, 0.05, 0.9, yo, f, 'conc2')
        k.stripes(x0 + 0.4, x1 - 0.4, 1.0, 1.4, yo, f, 8)
        k.qy(x0 + 0.3, x1 - 0.3, H - 1.6, H - 1.2, yo, f, 'crimson')
        if feed:
            stencil_digit(k, 0, x0 + 1.2, 2.2, 0.6, 1.2, yo, f, c='bone')
        else:
            pts = [(x1 - 3.0, yo + f * 0.003, 2.4), (x1 - 1.7, yo + f * 0.003, 2.4), (x1 - 1.7, yo + f * 0.003, 2.1),
                   (x1 - 0.9, yo + f * 0.003, 2.8), (x1 - 1.7, yo + f * 0.003, 3.5), (x1 - 1.7, yo + f * 0.003, 3.2), (x1 - 3.0, yo + f * 0.003, 3.2)]
            k.poly(pts, 'cyan', (0, f, 0))
    ca, cb = srt(closed + sg * 0.006, closed + sg * 0.25)
    k.bx(ca, cb, -W, W, 0.0, H, 'gun')
    xo = closed + sg * 0.003
    k.qx(-1.8, 1.8, 0.05, 0.9, xo, -sg, 'conc2')
    k.qx(-1.2, 1.2, 2.4, 4.4, xo, -sg, 'crimson')
    pa, pb = srt(mouth - sg * 0.05, mouth + sg * 0.3)
    for f in (-1, 1):
        k.bx(pa, pb, *srt(f * (W - 0.15), f * (W + 0.24)), 0.0, H - 0.1, 'gun2')
    k.bx(pa - 0.03, pb + 0.03, -W - 0.26, W + 0.26, H - 1.1, H + 0.05, 'gun2')
    xd = mouth - sg * 0.7
    k.cyl(xd, -W + 0.05, H - 0.65, 0.32, 0.32, 2 * W - 0.1, 'slate2', seg=10, rot=(-90, 0, 0))
    xc = mouth + sg * 0.15
    for i in range(7):
        yy = -W + 0.15 + (2 * W - 0.3) * (i + 0.5) / 7
        k.bx(xc - 0.01 - 0.005 * (i % 2), xc + 0.01 - 0.005 * (i % 2), yy - 0.35, yy + 0.35, 0.4, H - 1.104, 'rubber', ink=False)
    k.bx(x0 - 0.1, x1 + 0.1, -W - 0.3, W + 0.3, H + 0.05, H + 0.35, 'steelDark')
    beacon(k, (x0 + x1) / 2, W - 0.4, H + 0.35, c='alarm' if feed else 'cyan', r=0.16)
    k.col(x0, x1, -W - 0.22, W + 0.22, 0, H + 0.35)


def line_tile(k, kind):
    k.begin()
    line_base(k)
    if kind == 'Feed':
        house(k, True)
        tunnel(k, 1)
    elif kind == 'Mid':
        tunnel(k, 2)
        for f in (-1, 1):
            robot_arm(k, -3.2, f * 2.5, 90 - 90 * f, reach=1.0, tool='weld' if f > 0 else 'claw')
            k.col(-3.7, -2.7, *srt(f * 2.0, f * 3.0), 0, 2.0)
        for f in (-1, 1):                                           # parts trolleys inside the fence
            k.bx(-5.6, -4.6, *srt(f * 2.3, f * 3.2), 0.25, 0.9, 'gun2')
            for x in (-5.4, -4.8):
                k.cyl(x, f * 2.75, 0.0, 0.12, 0.12, 0.25, 'rubber', seg=6)
            for i in range(3):
                k.beam((-5.5 + i * 0.3, f * 2.5, 0.92), (-5.4 + i * 0.3, f * 3.0, 1.5), 0.08, 'olive', ink=True)
    elif kind == 'Out':
        house(k, False)
        for x in (-4.5, -0.8):
            for f in (-1, 1):
                k.bx(x - 0.1, x + 0.1, *srt(f * 3.1, f * 3.3), 0.0, 6.0, 'gun2')
                k.col(x - 0.1, x + 0.1, *srt(f * 3.1, f * 3.3), 0, 6.0)
            k.bx(x - 0.13, x + 0.13, -3.3, 3.3, 6.0, 6.25, 'crimson')
            k.bx(x - 0.32, x + 0.32, -1.6, 1.6, 5.75, 6.0, 'steelDark', ink=False)
            k.qz(x - 0.27, x + 0.27, -1.5, 1.5, 5.747, -1, 'lamp')
    return k


def line_slat(k):
    k.begin()
    k.bx(-0.1, 0.1, -0.92, 0.92, 0.0, 0.03, 'steel2', ink=False)
    k.bx(-0.035, 0.035, -0.86, 0.86, 0.03, 0.05, 'hazard', ink=False)
    return k


def line_item(k, what, stage):
    """A line item riding its skid, facing downstream (+X)."""
    k.begin()
    skid(k, *{'Spider': (2.65, 1.85), 'Hover': (2.4, 1.65), 'Hound': (1.75, 1.15)}[what])
    if what == 'Spider':
        spider(k, stage, B=0.44, deg=90)
    elif what == 'Hover':
        hover(k, stage, B=0.09, deg=90, glow=False)
    elif what == 'Hound':
        hound(k, stage, B=0.44, deg=90, s=1.15)
    return k


# ================================================================ overhead monorail ('o' cells, items hang below)
OR = 14.0      # rail bottom (payloads hang 9.8 - 14.5 m: over the line tunnels and houses)


def orail(k, hang):
    k.begin()
    k.bx(-0.5, 0.5, -0.22, 0.22, OR, OR + 0.1, 'gun2', ink=False)
    k.bx(-0.5, 0.5, -0.05, 0.05, OR + 0.1, OR + 0.55, 'steelDark', ink=False)
    k.bx(-0.5, 0.5, -0.24, 0.24, OR + 0.55, OR + 0.67, 'gun2', ink=False)
    k.qy(-0.5, 0.5, OR + 0.02, OR + 0.08, -0.223, -1, 'hazard')
    if hang:
        k.bx(-0.3, 0.3, -0.3, 0.3, OR + 0.67, OR + 0.9, 'steelDark')
        for dy in (-0.15, 0.15):
            k.bx(-0.04, 0.04, dy - 0.04, dy + 0.04, OR + 0.9, CEIL, 'steel2', ink=False)
    return k


def orail_port(k, sg=1):
    """Transfer port at a monorail end (5 m along X, the rail runs in at sg * X: +X at the run start, -X at its end): a
    hanging box housing with a dark mouth, strip curtains, a hazard frame and lamps (the carriers pop in and out of sight
    inside)."""
    k.begin(0 if sg > 0 else 180)
    x0, x1, z0, z1, W = -2.36, 2.4, OR - 5.8, OR + 1.0, 1.9
    k.bx(x0, x1, -W, W, z0, z1, 'gun')
    for f in (-1, 1):
        yo = f * (W + 0.003)
        k.qy(x0 + 0.2, x1 - 0.2, z0 + 0.2, z0 + 0.6, yo, f, 'crimson')
        FD.port_rivets(k, x0 + 0.2, x1 - 0.2, z0 + 0.4, yo, f)
        k.stripes(x0 + 0.2, x1 - 0.2, z1 - 0.7, z1 - 0.3, yo, f, 10)
        stencil_digit(k, 3, -0.4, z0 + 1.6, 0.8, 1.6, yo, f, c='bone')
    k.qx(-W + 0.1, W - 0.1, z0 + 0.1, z1 - 0.4, x1 + 0.003, 1, 'steelDark')
    for i in range(7):
        yy = -W + 0.3 + (2 * W - 0.6) * (i + 0.5) / 7
        k.bx(x1 + 0.01, x1 + 0.03, yy - 0.2, yy + 0.2, z0 + 0.2, z1 - 0.5, 'rubber', ink=False)
    k.bx(x1 - 0.1, x1 + 0.12, -W - 0.15, W + 0.15, z1 - 0.4, z1 + 0.05, 'hazard')
    for f in (-1, 1):
        k.bx(x1 - 0.1, x1 + 0.12, *srt(f * (W - 0.1), f * (W + 0.15)), z0 - 0.06, z1 - 0.4, 'hazard')
    k.bx(-0.3, 0.3, -0.3, 0.3, z1, CEIL - 0.008, 'steelDark')
    k.cyl(0.0, 0.0, z0 - 0.004, 0.4, 0.4, 0.002, 'lamp', seg=10, ink=False)
    beacon(k, 1.6, W - 0.4, z1, c='alarm', r=0.16)
    return k


def carrier(k, what):
    """A monorail carrier (trolley on the rail, a C-hanger) with its payload hanging below."""
    k.begin()
    k.bx(-0.6, 0.6, -0.32, 0.32, OR - 0.5, OR - 0.02, 'hazard2')
    for x in (-0.4, 0.4):
        k.cyl(x, -0.3, OR + 0.32, 0.14, 0.14, 0.6, 'steelDark', seg=8, rot=(-90, 0, 0))
        for f in (-1, 1):
            k.bx(x - 0.06, x + 0.06, *srt(f * 0.26, f * 0.34), OR - 0.02, OR + 0.4, 'steelDark')
    if what == 'Hover':
        top = OR - 1.6
        for x in (-1.2, 1.2):
            k.beam((x * 0.3, 0.0, OR - 0.5), (x, 0.0, top + 0.3), 0.1, 'steelDark')
            k.bx(x - 0.2, x + 0.2, -1.55, 1.55, top + 0.2, top + 0.34, 'steelDark')
        B = top - 2.2 - 0.36
        for x in (-1.2, 1.2):
            for y in (-0.9, 0.9):
                k.bx(x - 0.05, x + 0.05, y - 0.04, y + 0.04, B + 0.35 + 1.2, top + 0.2, 'hazard2', ink=False)
        hover(k, 2, B=B, deg=90, glow=True)
    else:
        top = OR - 1.4
        k.beam((0, 0, OR - 0.5), (0, 0, top + 0.1), 0.14, 'steelDark')
        k.bx(-1.8, 1.8, -0.15, 0.15, top, top + 0.15, 'steelDark')
        gunship(k, 1, B=top - 0.95, deg=90)
    return k


# ================================================================ props
def crate(k, kind):
    k.begin()
    if kind == 'Ammo':
        k.bx(-0.48, 0.48, -0.42, 0.42, 0.0, 0.08, 'wood2')
        k.bx(-0.45, 0.45, -0.38, 0.38, 0.08, 0.95, 'olive')
        for f in (-1, 1):
            k.qy(-0.4, 0.4, 0.3, 0.38, f * 0.383, f, 'hazard')
            stencil_num(k, (5, 0), -0.3, 0.45, 0.22, 0.35, 0.08, f * 0.383, f, c='bone')
        for x in (-0.3, 0.3):
            k.bx(x - 0.05, x + 0.05, -0.42, 0.42, 0.65, 0.75, 'olive2')
        FD.ammo_crate(k)
    elif kind == 'Bin':
        k.bx(-0.46, 0.46, -0.46, 0.46, 0.0, 0.8, 'gun2')
        k.stripes(-0.42, 0.42, 0.6, 0.75, -0.463, -1, 4)
        for i, (x, y) in enumerate(((-0.2, -0.1), (0.15, 0.1), (0.0, -0.2))):
            k.beam((x, y, 0.5), (x + 0.15 * (i - 1), y + 0.3, 1.45 - 0.15 * i), 0.09, 'crimson' if i != 1 else 'steel2')
    elif kind == 'Lid':
        k.bx(-0.44, 0.44, -0.37, 0.37, 0.0, 0.5, 'olive2')
        k.qy(-0.36, 0.36, 0.2, 0.3, -0.373, -1, 'bone')
    return k


def drums(k, v):
    k.begin()
    k.bx(-0.48, 0.48, -0.48, 0.48, 0.0, 0.1, 'wood2')
    spots = ((-0.22, -0.2), (0.22, -0.18), (0.0, 0.22)) if v == 0 else ((-0.2, 0.0), (0.24, 0.05))
    for i, (x, y) in enumerate(spots):
        c = ('cyanD', 'crimson', 'gunL')[i % 3] if v == 0 else ('hazard', 'cyanD')[i % 2]
        k.cyl(x, y, 0.1, 0.21, 0.21, 0.86, c, seg=10)
        k.cyl(x, y, 0.96, 0.17, 0.17, 0.006, 'steelDark', seg=10, ink=False)
        k.cyl(x, y, 0.5, 0.215, 0.215, 0.1, 'steelDark', seg=10, ink=False)
    return k


def cart(k, kind):
    k.begin()
    if kind == 'Gas':
        k.bx(-0.4, 0.4, -0.25, 0.25, 0.12, 0.3, 'crimson')
        for x in (-0.3, 0.3):
            k.cyl(x, 0.0, 0.0, 0.1, 0.1, 0.12, 'rubber', seg=8)
        for x, c in ((-0.17, 'olive'), (0.17, 'cyanD')):
            k.cyl(x, 0.0, 0.3, 0.14, 0.14, 1.1, c, seg=10)
            k.cyl(x, 0.0, 1.4, 0.07, 0.05, 0.12, 'steelDark', seg=8)
        k.bx(-0.36, 0.36, 0.2, 0.25, 0.3, 1.25, 'steelDark')
        k.beam((-0.17, 0.05, 1.5), (0.35, -0.3, 0.9), 0.04, 'hose', ink=False)
    elif kind == 'Chest':
        k.bx(-0.45, 0.45, -0.3, 0.3, 0.06, 1.1, 'crimson')
        for z in (0.35, 0.6, 0.85):
            k.qy(-0.4, 0.4, z - 0.01, z + 0.01, -0.303, -1, 'crimson2')
            k.qy(-0.1, 0.1, z + 0.06, z + 0.1, -0.303, -1, 'steel')
        k.bx(-0.45, 0.45, -0.3, 0.3, 1.1, 1.18, 'steelDark')
        for x in (-0.35, 0.35):
            k.cyl(x, 0.0, 0.0, 0.06, 0.06, 0.06, 'rubber', seg=6)
    elif kind == 'Screen':
        for x in (-0.45, 0.45):
            k.bx(x - 0.03, x + 0.03, -0.2, 0.2, 0.0, 0.05, 'steelDark')
            k.bx(x - 0.025, x + 0.025, -0.025, 0.025, 0.05, 1.8, 'steelDark')
        k.bx(-0.43, 0.43, -0.012, 0.012, 0.2, 1.75, 'olive2', ink=False)
        k.qy(-0.3, 0.3, 1.2, 1.5, -0.015, -1, 'hazard')
    return k


def spool(k):
    k.begin()
    k.bx(-0.9, 0.9, -0.5, 0.5, 0.0, 0.12, 'wood2')
    drumx(k, 0.0, 0.0, 0.85, 0.82, 1.5, 'cableR', seg=12)
    for x in (-0.78, 0.78):
        drumx(k, x, 0.0, 0.85, 0.88, 0.12, 'wood', seg=12)
    k.beam((0.4, -0.75, 0.6), (0.6, -0.95, 0.1), 0.1, 'cableR', ink=False)
    return k


def plates(k, kind):
    k.begin()
    for y in (-0.6, 0.6):
        k.bx(-0.9, 0.9, y - 0.08, y + 0.08, 0.0, 0.14, 'wood')
    if kind == 'Stack':
        for i in range(4):
            z = 0.14 + i * 0.18
            c = ('bone', 'crimson', 'bone2', 'gun')[i]
            k.hullp([(-0.9 + i * 0.04, -0.85, z), (0.9 - i * 0.04, -0.85, z), (-0.9 + i * 0.04, 0.85, z), (0.9 - i * 0.04, 0.85, z),
                     (-0.75, -0.7, z + 0.16), (0.75, -0.7, z + 0.16), (-0.75, 0.7, z + 0.18), (0.75, 0.7, z + 0.18)], c)
    else:   # curved shin plates standing in a rack
        for x in (-0.85, 0.85):
            k.bx(x - 0.06, x + 0.06, -0.85, 0.85, 0.14, 1.6, 'hazard')
        k.bx(-0.85, 0.85, 0.78, 0.84, 1.45, 1.55, 'hazard')
        for i, x in enumerate((-0.5, -0.05, 0.4)):
            k.hullp([(x - 0.06, -0.75, 0.14), (x + 0.06, -0.75, 0.14), (x - 0.06, 0.75, 0.14), (x + 0.06, 0.75, 0.14),
                     (x - 0.16, -0.6, 1.5), (x - 0.02, -0.6, 1.5), (x - 0.16, 0.6, 1.5), (x - 0.02, 0.6, 1.5)], 'crimson' if i % 2 else 'bone')
    return k


def shells(k):
    """Pallet of titan cannon shells (war production)."""
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.14, 'wood')
    k.bx(-0.85, 0.85, -0.85, 0.85, 0.14, 0.2, 'steelDark')
    for i in range(3):
        for j in range(3):
            x, y = -0.55 + i * 0.55, -0.55 + j * 0.55
            if (i, j) == (2, 0):
                continue
            k.cyl(x, y, 0.2, 0.22, 0.22, 0.95, 'copper', seg=8)
            k.cyl(x, y, 1.15, 0.22, 0.06, 0.45, 'crimson' if (i + j) % 2 else 'gun', seg=8)
            k.cyl(x, y, 0.45, 0.225, 0.225, 0.08, 'steelDark', seg=8, ink=False)
    k.bx(0.35, 0.85, -0.85, -0.35, 0.2, 0.6, 'olive')
    return k


def limb_rack(k):
    """Rack of spider legs and hound legs waiting to be fitted."""
    k.begin()
    for x in (-1.8, 0.0, 1.8):
        k.bx(x - 0.08, x + 0.08, -0.5, 0.5, 0.0, 0.1, 'steelDark')
        k.bx(x - 0.05, x + 0.05, -0.05, 0.05, 0.1, 2.3, 'gun2')
    k.bx(-1.9, 1.9, -0.08, 0.08, 2.2, 2.36, 'hazard')
    for i in range(6):
        x = -1.55 + i * 0.62
        a = V((x, -0.12, 2.2))
        kn = V((x + 0.05, -0.35, 1.4))
        ft = V((x, -0.2, 0.25))
        oslab(k, a, kn, 0.1, 0.09, 0.08, 0.08, 'crimson' if i % 2 == 0 else 'bone')
        oslab(k, kn, ft, 0.08, 0.08, 0.05, 0.05, 'gun')
        k.sph(kn.x, kn.y, kn.z, 0.1, 'steelDark', seg=(6, 4))
    k.col(-1.95, 1.95, -0.55, 0.55, 0, 2.36)
    return k


def barrier(k):
    k.begin()
    k.hullp([(-0.5, -0.32, 0.0), (0.5, -0.32, 0.0), (-0.5, 0.32, 0.0), (0.5, 0.32, 0.0),
             (-0.5, -0.12, 0.32), (0.5, -0.12, 0.32), (-0.5, 0.12, 0.32), (0.5, 0.12, 0.32),
             (-0.5, -0.1, 0.85), (0.5, -0.1, 0.85), (-0.5, 0.1, 0.85), (0.5, 0.1, 0.85)], 'conc')
    for f in (-1, 1):
        for x in (-0.25, 0.25):
            k.poly([(x - 0.12, f * 0.1208, 0.4), (x + 0.04, f * 0.1208, 0.4), (x + 0.12, f * 0.1065, 0.78), (x - 0.04, f * 0.1065, 0.78)], 'hazard', (0, f, 0.04))
    return k


def flood_tower(k):
    """Mobile light mast: a wheeled generator base, a 7 m mast, a bar of four floodlights aimed forward and down."""
    k.begin()
    k.bx(-0.85, 0.85, -0.6, 0.6, 0.3, 1.2, 'hazard')
    k.stripes(-0.8, 0.8, 0.35, 0.6, -0.603, -1, 6)
    k.qy(-0.6, -0.1, 0.75, 1.05, -0.603, -1, 'steelDark')
    for x in (-0.6, 0.6):
        for f in (-1, 1):
            drumy(k, x, f * 0.68, 0.3, 0.3, 0.14, 'rubber', seg=10)
    k.bx(-0.12, 0.12, -0.12, 0.12, 1.2, 7.4, 'gun2')
    FD.flood_base(k)
    k.bx(-1.2, 1.2, -0.12, 0.12, 7.4, 7.6, 'steelDark')
    for x in (-0.9, -0.3, 0.3, 0.9):
        k.push(x, -0.15, 0, 7.75)
        floodlamp(k, 0.0, 0.0, 0.0, w=0.5, h=0.4, s=-1)
        k.pop()
    k.col(-0.9, 0.9, -0.65, 0.65, 0, 1.2)
    k.col(-0.15, 0.15, -0.15, 0.15, 1.2, 7.4)
    return k


def console(k):
    k.begin()
    k.bx(-0.45, 0.45, -0.3, 0.3, 0.0, 0.95, 'gun')
    k.hullp([(-0.45, -0.3, 0.95), (0.45, -0.3, 0.95), (-0.45, 0.3, 0.95), (0.45, 0.3, 0.95),
             (-0.45, 0.05, 1.15), (0.45, 0.05, 1.15), (-0.45, 0.3, 1.15), (0.45, 0.3, 1.15)], 'gun2')
    k.bx(-0.4, 0.4, 0.2, 0.3, 1.15, 1.75, 'steelDark')
    k.qy(-0.34, 0.34, 1.25, 1.68, 0.197, -1, 'screen')
    k.qy(-0.3, -0.05, 1.3, 1.45, 0.194, -1, 'cyan')
    beacon(k, 0.35, 0.25, 1.75, c='hazard', r=0.06, h=0.1)
    return k


# ================================================================ robots on display
def weld_cell(k, kind):
    """[4, 4]: a turntable with a chassis on it, two robot arms welding, curtain posts at the corners."""
    k.begin()
    k.qz(-1.95, 1.95, -1.95, 1.95, Z['cell'], 1, 'hazard')
    k.qz(-1.75, 1.75, -1.75, 1.75, Z['cell'] + 0.004, 1, 'pit')
    k.cyl(0, 0, 0.0, 1.6, 1.6, 0.3, 'gun2', seg=16)
    k.cyl(0, 0, 0.3, 1.3, 1.3, 0.005, 'steelDark', seg=16, ink=False)
    if kind == 'Spider':
        spider(k, 2, B=0.305, s=0.6, deg=20)
    else:
        hover(k, 1, B=0.305 - 0.35 * 0.62, s=0.62, deg=-30, glow=False)
    robot_arm(k, -1.5, 1.5, -135, reach=1.0, tool='weld')
    robot_arm(k, 1.5, 1.5, 135, reach=1.0, tool='weld' if kind == 'Spider' else 'claw')
    for (x, y) in ((-1.85, -1.85), (1.85, -1.85)):
        k.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.0, 2.6, 'hazard')
        k.col(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 2.6)
    k.bx(-1.85, 1.85, -1.88, -1.82, 2.5, 2.58, 'hazard')
    k.col(-1.6, 1.6, -1.6, 1.6, 0, 1.9)
    k.col(-2.0, -1.0, 1.0, 2.0, 0, 1.6)
    k.col(1.0, 2.0, 1.0, 2.0, 0, 1.6)
    return k


def chassis_jig(k, kind):
    """[6, 4]: chassis frames in yellow jigs under a lamp gantry."""
    k.begin()
    k.qz(-2.95, 2.95, -1.95, 1.95, Z['cell'], 1, 'hazard')
    k.qz(-2.75, 2.75, -1.75, 1.75, Z['cell'] + 0.004, 1, 'pit')
    if kind == 'Hover':
        for x in (-1.2, 1.2):
            k.bx(x - 0.3, x + 0.3, -1.5, 1.5, 0.0, 0.36, 'hazard')
        hover(k, 0, B=0.02, deg=90, glow=False)
        k.col(-2.4, 2.4, -1.6, 1.6, 0, 1.0)
    else:
        for i, x in enumerate((-1.9, 0.0, 1.9)):
            hound(k, 0 if i != 1 else 1, deg=0, x=x, s=0.95)
        k.col(-2.6, 2.6, -1.6, 1.6, 0, 1.9)
    for x in (-2.8, 2.8):
        for y in (-1.8, 1.8):
            k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 3.6, 'gun2')
            k.col(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0, 3.6)
    for y in (-1.8, 1.8):
        k.bx(-2.9, 2.9, y - 0.09, y + 0.09, 3.6, 3.78, 'crimson')
    k.bx(-0.9, 0.9, -1.0, 1.0, 3.5, 3.6, 'steelDark', ink=False)
    k.qz(-0.85, 0.85, -0.95, 0.95, 3.497, -1, 'lamp')
    return k


def test_cell(k, kind):
    """[6, 6]: a mesh test cage (open front) with a hound on a treadmill or a spider on a tilt table, a lamp bar,
    hazard paint and the control desk outside."""
    k.begin()
    k.qz(-2.95, 2.95, -2.95, 2.95, Z['cell'], 1, 'pit')
    k.qz(-2.95, 2.95, -2.95, -2.55, Z['cell'] + 0.004, 1, 'hazard')
    for (x, y) in ((-2.6, -2.2), (2.6, -2.2), (-2.6, 2.6), (2.6, 2.6)):
        k.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.0, 4.0, 'gun2')
    for f in (-1, 1):
        x0, x1 = srt(f * 2.58, f * 2.62)
        k.bx(x0, x1, -2.1, 2.5, 0.2, 3.8, 'steelDark', ink=False)
        k.col(*srt(f * 2.5, f * 2.7), -2.3, 2.7, 0, 4.0)
    k.bx(-2.5, 2.5, 2.58, 2.62, 0.2, 3.8, 'steelDark', ink=False)
    k.col(-2.7, 2.7, 2.5, 2.7, 0, 4.0)
    for y in (-2.2, 2.6):
        k.bx(-2.7, 2.7, y - 0.12, y + 0.12, 4.0, 4.24, 'crimson')
    for x in (-2.6, 2.6):
        k.bx(x - 0.1, x + 0.1, -2.08, 2.48, 4.03, 4.2, 'crimson')
    k.bx(-2.55, 2.55, 0.0, 0.4, 3.85, 4.03, 'steelDark', ink=False)
    k.qz(-2.3, 2.3, 0.05, 0.35, 3.847, -1, 'lamp')
    beacon(k, 2.6, -2.2, 4.24, c='alarm', r=0.14)
    if kind == 'Hound':
        k.bx(-1.0, 1.0, -1.7, 1.7, 0.0, 0.32, 'steelDark')
        k.bx(-0.85, 0.85, -1.6, 1.6, 0.32, 0.36, 'rubber')
        for y in (-1.6, 1.6):
            drumx(k, 0.0, y, 0.2, 0.17, 1.8, 'gun2', seg=8)
        hound(k, 1, B=0.36, s=1.1)
        for i in range(3):
            k.cyl(-1.6, -0.8 + i * 0.8, 0.0, 0.18, 0.18, 0.5, 'hazard', seg=6)
        k.col(-1.0, 1.0, -1.9, 1.9, 0, 2.0)
    else:
        k.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.6, 'hazard2')
        k.bx(-1.7, 1.7, -1.7, 1.7, 0.6, 0.85, 'gun2')
        k.stripes(-1.65, 1.65, 0.63, 0.82, -1.703, -1, 10)
        spider(k, 3, B=0.85, s=0.66, deg=180)
        k.col(-1.7, 1.7, -1.7, 1.7, 0, 2.4)
    # control desk outside the cage, front right
    k.push(1.9, -2.7, 180)
    k.bx(-0.6, 0.6, -0.25, 0.25, 0.0, 0.95, 'gun')
    k.hullp([(-0.6, -0.25, 0.95), (0.6, -0.25, 0.95), (-0.6, 0.25, 0.95), (0.6, 0.25, 0.95),
             (-0.6, 0.05, 1.12), (0.6, 0.05, 1.12), (-0.6, 0.25, 1.12), (0.6, 0.25, 1.12)], 'gun2')
    k.bx(-0.5, 0.5, 0.15, 0.25, 1.12, 1.6, 'steelDark')
    k.qy(-0.44, 0.44, 1.2, 1.54, 0.147, -1, 'screen')
    k.pop()
    k.col(1.3, 2.5, -2.95, -2.45, 0, 1.6)
    return k


def centipede_rack(k):
    """[10, 4]: the centipede crawler on its assembly rack (cradles, a lamp bar on posts, an arm at the tail)."""
    k.begin()
    k.qz(-4.95, 4.95, -1.95, 1.95, Z['cell'], 1, 'hazard')
    k.qz(-4.75, 4.75, -1.75, 1.75, Z['cell'] + 0.004, 1, 'pit')
    k.push(-0.2, 0, 90)
    centipede(k, n=7, built=5)
    k.pop()
    for x in (-3.0, 0.0, 3.0):
        k.bx(x - 0.4, x + 0.4, -0.5, 0.5, 0.0, 0.42, 'hazard2')
    for x in (-4.8, 4.8):
        for y in (-1.8, 1.8):
            k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 3.4, 'gun2')
            k.col(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0, 3.4)
        k.bx(x - 0.09, x + 0.09, -1.85, 1.85, 3.4, 3.58, 'crimson')
    k.bx(-4.8, 4.8, -0.25, 0.25, 3.3, 3.4, 'steelDark', ink=False)
    k.qz(-4.7, 4.7, -0.2, 0.2, 3.297, -1, 'lamp')
    robot_arm(k, 3.6, 1.6, 150, reach=0.9, tool='weld')
    k.col(-4.6, 4.2, -1.5, 1.5, 0, 1.4)
    k.col(3.1, 4.1, 1.1, 2.0, 0, 1.6)
    return k


def formation(k, kind):
    """[4, 4]: a finished robot on its painted dispatch pad (the army lined up in the launch hall)."""
    k.begin()
    k.qz(-1.95, 1.95, -1.95, 1.95, Z['pad'], 1, 'crimson2')
    k.qz(-1.7, 1.7, -1.7, 1.7, Z['pad'] + 0.004, 1, 'pit')
    for i in range(4):
        x = -1.4 + i * 0.95
    k.qz(-1.6, 1.6, -1.95, -1.82, Z['pad'] + 0.004, 1, 'bone')
    if kind == 'Spider':
        spider(k, 3, s=0.75)
        k.col(-1.1, 1.1, -1.1, 1.1, 0, 2.0)
    elif kind == 'Hound':
        hound(k, 1, s=1.0)
        k.col(-0.7, 0.7, -1.5, 1.4, 0, 1.9)
    else:
        for x in (-1.0, 1.0):
            k.bx(x - 0.18, x + 0.18, -1.2, 1.2, 0.0, 0.3, 'steelDark')
        hover(k, 2, B=0.3 - 0.35 * 0.75, s=0.75, glow=False)
        k.col(-1.3, 1.3, -1.9, 1.9, 0, 1.9)
    return k


def reactor_cradle(k):
    """[4, 4]: a spare titan reactor core glowing in its containment cradle, cables, a hazard pad."""
    k.begin()
    k.qz(-1.95, 1.95, -1.95, 1.95, Z['cell'], 1, 'hazard')
    k.qz(-1.75, 1.75, -1.75, 1.75, Z['cell'] + 0.004, 1, 'pit')
    k.bx(-1.3, 1.3, -1.3, 1.3, 0.0, 0.5, 'gun2')
    k.stripes(-1.25, 1.25, 0.05, 0.45, -1.303, -1, 8)
    k.cyl(0, 0, 0.5, 1.05, 0.9, 0.35, 'steelDark', seg=14)
    k.sph(0, 0, 1.75, 0.95, 'cyan', seg=(14, 9))
    k.sph(0, -0.42, 1.8, 0.55, 'cyanL', seg=(10, 6), ink=False)
    for i in range(14):
        a, b = i / 14 * 2 * math.pi, (i + 1) / 14 * 2 * math.pi
        k.beam((math.cos(a) * 1.25, math.sin(a) * 1.25, 1.75), (math.cos(b) * 1.25, math.sin(b) * 1.25, 1.75), 0.12 + 0.012 * (i % 2), 'steelDark')
    for (x, y) in ((-1.15, -1.15), (1.15, -1.15), (-1.15, 1.15), (1.15, 1.15)):
        k.bx(x - 0.09, x + 0.09, y - 0.09, y + 0.09, 0.5, 3.0, 'gun')
    k.bx(-1.3, 1.3, -1.3, 1.3, 3.0, 3.22, 'gun2')
    k.cyl(0, 0, 2.75, 0.5, 0.35, 0.25, 'steelDark', seg=10)
    cable(k, (1.2, 1.2, 0.5), (1.9, 1.8, 0.1), 0.2, 0.14, 'cableR', n=3)
    cable(k, (-1.2, 1.2, 0.5), (-1.9, 1.9, 0.1), 0.2, 0.14, 'hose', n=3)
    k.col(-1.35, 1.35, -1.35, 1.35, 0, 3.22)
    return k


# ================================================================ floor decals (layer 0)
def decal(k, kind):
    k.begin()
    z = Z['decal']
    if kind == 'Lane':        # double yellow lane line along X
        for y in (-0.22, 0.22):
            k.qz(-0.5, 0.5, y - 0.06, y + 0.06, z, 1, 'hazard')
    elif kind == 'Band':      # hazard band along X
        k.qz(-0.5, 0.5, -0.32, 0.32, Z['hazard'], 1, 'hazard')
        for x in (-0.5, 0.0):
            k.poly([(x, -0.32, Z['hazard'] + 0.003), (x + 0.25, -0.32, Z['hazard'] + 0.003), (x + 0.5, 0.32, Z['hazard'] + 0.003), (x + 0.25, 0.32, Z['hazard'] + 0.003)], 'ink', (0, 0, 1))
    elif kind == 'Drain':
        k.qz(-0.4, 0.4, -0.4, 0.4, z, 1, 'steelDark')
        for i in range(5):
            x = -0.3 + i * 0.15
            k.qz(x - 0.035, x + 0.035, -0.32, 0.32, z + 0.003, 1, 'steel2')
    elif kind == 'Oil':
        rnd = random.Random(9)
        k.disc(0.0, 0.0, z, 0.45, 'oil', n=10, rnd=rnd, jag=0.25, sx=1.2, sy=0.8)
    elif kind == 'Patch':     # [2, 2] riveted floor patch
        k.qz(-0.9, 0.9, -0.9, 0.9, z, 1, 'floorP')
        k.qz(-0.8, 0.8, -0.8, 0.8, z + 0.003, 1, 'floorP2')
        for x in (-0.82, 0.82):
            for y in (-0.82, -0.27, 0.27, 0.82):
                k.qz(x - 0.035, x + 0.035, y - 0.035, y + 0.035, z + 0.006, 1, 'steelDark')
    elif kind == 'Arrow':     # [2, 2] chevrons pointing north (toward the exit)
        for i in range(2):
            yb = -0.75 + i * 0.75
            k.poly([(-0.75, yb, z), (0.0, yb + 0.55, z), (0.75, yb, z), (0.75, yb + 0.28, z), (0.0, yb + 0.83, z), (-0.75, yb + 0.28, z)], 'paintW', (0, 0, 1))
    elif kind == 'Rail':      # launch rail along X: a dark slot and a raised steel rail
        k.qz(-0.5, 0.5, -0.32, 0.32, Z['rail'], 1, 'pit')
        k.bx(-0.5, 0.5, -0.12, 0.12, Z['rail'] + 0.003, 0.11, 'steel')
        for x in (-0.25, 0.25):
            k.qz(x - 0.04, x + 0.04, -0.3, -0.16, Z['rail'] + 0.003, 1, 'hazard')
    elif kind == 'LaneR':     # crimson launch-lane paint with a bone chevron (along X)
        k.qz(-0.5, 0.5, -0.45, 0.45, Z['lane'], 1, 'crimson2')
        k.poly([(-0.4, -0.3, Z['lane'] + 0.003), (0.1, 0.0, Z['lane'] + 0.003), (-0.4, 0.3, Z['lane'] + 0.003), (-0.15, 0.3, Z['lane'] + 0.003), (0.35, 0.0, Z['lane'] + 0.003), (-0.15, -0.3, Z['lane'] + 0.003)], 'bone', (0, 0, 1))
    elif kind == 'Grid':      # [2, 2] hatched keep-clear box
        zz = Z['hazard']
        k.qz(-0.95, 0.95, -0.95, 0.95, zz, 1, 'hazard')
        k.qz(-0.8, 0.8, -0.8, 0.8, zz + 0.003, 1, 'pit')
        for a in (-0.75, -0.25, 0.25):
            k.poly([(a, -0.8, zz + 0.006), (a + 0.2, -0.8, zz + 0.006), (a + 0.5, 0.8, zz + 0.006), (a + 0.3, 0.8, zz + 0.006)], 'hazard', (0, 0, 1))
    return k


# ================================================================ build
def build_kit_foundry(ao):
    pal = Palette(FAM)
    k = FK(pal, PFX, HULL_T)
    for kind in ('Plain', 'Pipes', 'Duct', 'Panel', 'BanL', 'BanM', 'BanR', 'Hose', 'Gate', 'GateIn', 'Back'):
        wall_module(k, kind).finish('Wall_' + kind, ao=ao)
    for d in range(10):
        wall_module(k, 'Num', num=d).finish('Wall_Num%d' % d, ao=ao)
    wall_module(k, 'Plain', cutL=0.42).finish('Wall_EndL', ao=ao)
    wall_module(k, 'Plain', cutR=0.42).finish('Wall_EndR', ao=ao)
    pilaster(k).finish('Pilaster', ao=ao)
    for c in ('NW', 'NE', 'SW', 'SE'):
        corner(k, c).finish('Corner_' + c, ao=ao)
    for kind in ('', '_Crane', '_Banner'):
        ceil_bay(k, kind[1:]).finish('CeilBay' + kind)
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    trail_wall(k).finish('TrailWall', ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    # lines
    for kind in ('Feed', 'Mid', 'Out'):
        line_tile(k, kind).finish('Line_' + kind, ao=ao)
    line_slat(k).finish('Line_Slat')
    for st in range(4):
        line_item(k, 'Spider', st).finish('Spider_%d' % st)
    for st in range(3):
        line_item(k, 'Hover', st).finish('Hover_%d' % st)
    for st in range(2):
        line_item(k, 'Hound', st).finish('Hound_%d' % st)
    orail(k, False).finish('ORail')
    orail(k, True).finish('ORail_Hang')
    orail_port(k, 1).finish('ORail_PortIn', ao=ao)
    orail_port(k, -1).finish('ORail_PortOut', ao=ao)
    carrier(k, 'Hover').finish('Carrier_Hover')
    carrier(k, 'Gunship').finish('Carrier_Gunship')
    # props
    for kind in ('Ammo', 'Bin', 'Lid'):
        crate(k, kind).finish('Crate_' + kind, ao=ao)
    for v in (0, 1):
        drums(k, v).finish('Drums_%s' % 'AB'[v], ao=ao)
    for kind in ('Gas', 'Chest', 'Screen'):
        cart(k, kind).finish('Cart_' + kind, ao=ao)
    spool(k).finish('Spool', ao=ao)
    for kind in ('Stack', 'Rack'):
        plates(k, kind).finish('Plates_' + kind, ao=ao)
    shells(k).finish('Shells', ao=ao)
    limb_rack(k).finish('LimbRack', ao=ao)
    barrier(k).finish('Barrier', ao=ao)
    flood_tower(k).finish('FloodTower', ao=ao)
    console(k).finish('Console', ao=ao)
    # displays
    for kind in ('Spider', 'Hover'):
        weld_cell(k, kind).finish('WeldCell_' + kind, ao=ao)
    for kind in ('Hover', 'Hound'):
        chassis_jig(k, kind).finish('Jig_' + kind, ao=ao)
    for kind in ('Hound', 'Spider'):
        test_cell(k, kind).finish('TestCell_' + kind, ao=ao)
    centipede_rack(k).finish('CentipedeRack', ao=ao)
    for kind in ('Spider', 'Hound', 'Hover'):
        formation(k, kind).finish('Pad_' + kind, ao=ao)
    reactor_cradle(k).finish('ReactorCradle', ao=ao)
    for kind in ('Lane', 'Band', 'Drain', 'Oil', 'Patch', 'Arrow', 'Rail', 'LaneR', 'Grid'):
        decal(k, kind).finish('Decal_' + kind)
    # giants
    GI.titan_legs_frame(k).finish('Landmark_Titan_LegsFrame', ao=ao)
    GI.titan_torso_frame(k).finish('Landmark_Titan_TorsoFrame', ao=ao)
    GI.titan_legs(k).finish('Landmark_Titan_Legs', ao=ao)
    GI.titan_torso_half(k).finish('Landmark_Titan_TorsoHalf', ao=ao)
    GI.titan_torso(k).finish('Landmark_Titan_Torso', ao=ao)
    GI.titan_arm_l(k).finish('Landmark_Titan_ArmL', ao=ao)
    GI.titan_arm_gun(k).finish('Landmark_Titan_ArmGun', ao=ao)
    GI.titan_gun_hung(k).finish('Landmark_Titan_GunHung', ao=ao)
    GI.bay_frame(k).finish('Landmark_Bay_Frame', ao=ao)
    GI.bay_armour(k).finish('Landmark_Bay_Armour', ao=ao)
    GI.bay_armour_deck(k).finish('Landmark_Bay_ArmourDeck', ao=ao)
    GI.bay_launch(k).finish('Landmark_Bay_Launch', ao=ao)
    GI.strider_legs(k).finish('Landmark_Strider_Legs', ao=ao)
    GI.strider_hull(k, full=False).finish('Landmark_Strider_HullHalf', ao=ao)
    GI.strider_hull(k, full=True).finish('Landmark_Strider_Hull', ao=ao)
    GI.bay_strider(k).finish('Landmark_Bay_Strider', ao=ao)
    GI.bay_strider_launch(k).finish('Landmark_Bay_StriderLaunch', ao=ao)
    for n in (1, 2):
        GI.launch_door(k, n).finish('Landmark_LaunchDoor%d' % n, ao=ao)
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_foundry
