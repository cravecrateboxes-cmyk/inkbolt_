"""INKBOLT asset family: kit-factory2 (Heavy Works: the plant where the enemy builds its BIG robots).

A heavier, taller sister of Robot Works (fam_kit_factory.py) with its own look: 16 m halls with oxide-red block
plinths, deep-teal corrugated siding, a crane runway on corbels and a high clerestory (late dusk outside: furnaces,
cooling stacks, a goliath crane); roof bays with high-bay lamps and overhead bridge cranes carrying armour plates and
legs. On the floor: moving build lines where walker mechs and tread bruisers (4-7 m tall) ride skids through their
stations (bare chassis frame -> drivetrain fitted -> armour plated in primer -> painted and finished), weld cells
with sparks, stacked armour plates, giant wheels and treads, mech legs waiting to be fitted, chassis jigs, plate
machines, a fenced test track (a finished bruiser laps it) and the Titan dock (a 10 m mech in its scaffold).

Conventions (see src/data/themes.js, kit_base.py and fam_kit_factory.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up; one-sided
    pieces face Blender -Y (game +Z). Walls use wall.facing = 'open'.
  * Moving pieces (Mech_*, Part_*, Track_Slat, Belt_Cleat) are animated by the engine (theme symbol option `conveyor`):
    the line tiles (Jig_*) are static; the mechs ride them on skids, the stage swaps happen inside the station booths.
  * Mechs never have eyes or faces: sensor slots, lamps and core domes only.
  * Floor decals sit at their own heights (Z table) so overlapping decals never z-fight.
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, rz, srt, shutter_hull
import ib_text
import f2_detail as FD

FAM = 'kit-factory2'
PFX = 'KIT_FACTORY2_'
ib_lib.GLB[FAM] = 'fps-kit-factory2.glb'
ib_lib.CFG[FAM] = (0.015, 0.02)
HULL_T = 0.02
CEIL = 16.0
WALL_H = 16.4
ROOF = 4.2              # service corridor ceiling
WIN0, WIN1 = 11.4, 15.0  # clerestory band
RAIL = 9.4              # crane runway on the walls

ib_lib.PALETTES[FAM] = BASE + [
    ('conc', '#B3ADA3'), ('conc2', '#958F86'), ('oxide', '#A8442E'), ('oxide2', '#86331F'),
    ('tealS', '#1F5A63'), ('tealS2', '#174850'), ('cream', '#EFE3C4'), ('cream2', '#D3C39E'),
    ('orange', '#F07A22'), ('orange2', '#C25E14'), ('hazard', '#F5B82E'), ('steel', '#A7AFB6'),
    ('steel2', '#7D868F'), ('steelDark', '#353B43'), ('roofEdge', '#2B2F35'), ('glint', '#EAF6FF'),
    ('lamp', '#FFF3C4'), ('lampWarm', '#FFD66B'), ('pool', '#C1BBAF'), ('pool2', '#D0C9BB'),
    ('spark', '#FFE58A'), ('spark2', '#FF9A3A'), ('hot', '#FF6A2A'), ('primer', '#959089'),
    ('primer2', '#B0573F'), ('paintT', '#2C8C8E'), ('paintT2', '#1F6A6C'), ('chrome', '#D8DFE5'),
    ('hose', '#3E4D8C'), ('rubber', '#34323C'), ('tread', '#28272D'), ('core', '#FFC23A'),
    ('weld', '#565B63'), ('curtain', '#3E7D5A'), ('curtain2', '#2F6448'), ('plate', '#7F8891'),
    ('plate2', '#68717A'), ('crate', '#B98A5A'), ('crate2', '#94683C'), ('glassB', '#5E9BD8'),
    ('pit', '#3A3C42'), ('lane', '#ECE6D6'), ('asphalt', '#615F66'), ('far', '#7E7280'),
    ('far2', '#5F5566'), ('farLit', '#F4B26A'), ('smoke', '#E4DCD5'), ('ceil', '#7F858C'),
    ('panel', '#D9DCE0'), ('screen', '#7FD6E8'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

Z = {'pool': 0.016, 'track': 0.024, 'hazard': 0.032, 'cell': 0.04, 'test': 0.048, 'testLine': 0.056,
     'dock': 0.064, 'jig': 0.072, 'mach': 0.08, 'hatch': 0.09}


# ================================================================ shared bits
def stencil_digit(k, d, x, z, w, h, y, s, c='ink', dy=0.003):
    """A stencil-style digit (Bebas Neue vector glyph, ib_text) in the box x..x+w, z..z+h on a -Y (s=-1) / +Y (s=1)
    facing plane, dy proud of y; reads right from the side it faces."""
    ib_text.draw(k, str(d), x + w / 2, y + s * dy, z, h, c, face='y-' if s < 0 else 'y+', font='display', maxw=w * 1.1)


def spark_star(k, x, y, z, r, s=-1, c='spark'):
    """Flat 8-point welding spark star facing -Y (s=-1) or +Y."""
    pts = []
    for i in range(16):
        a = i / 16 * 2 * math.pi
        rr = r if i % 2 == 0 else r * 0.38
        pts.append((x + math.cos(a) * rr, y, z + math.sin(a) * rr))
    k.poly(pts, c, (0, s, 0))


def pool_disc(k, x, y, z, r, seed, sx=1.0, sy=1.0, c1='pool', c2='pool2'):
    rnd = random.Random(seed)
    k.disc(x, y, z, r, c1, n=14, rnd=rnd, jag=0.05, sx=sx, sy=sy)
    k.disc(x, y, z + 0.004, r * 0.55, c2, n=10, rnd=rnd, jag=0.06, sx=sx, sy=sy)


def robot_arm(k, x, y, deg, z=0.0, reach=1.0, tool='claw', s=1.0, c='orange', c2='orange2'):
    """Industrial robot arm (base, turret, upper arm, forearm, wrist, tool), reaching along local -Y."""
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0, 0.42, 0.42, 0.18, 'steelDark', seg=8)
    k.cyl(0, 0, 0.18, 0.32, 0.28, 0.42, c, seg=8)
    k.bx(-0.22, 0.22, -0.2, 0.2, 0.55, 0.85, c2)
    sh = Vector((0, 0, 0.75))
    el = Vector((0, -0.55 * reach, 1.75))
    wr = Vector((0, -1.25 * reach, 1.35))
    k.beam(sh, el, 0.24, c)
    k.cyl(-0.16, el.y, el.z - 0.18, 0.18, 0.18, 0.32, c2, seg=6, rot=(0, 90, 0))
    k.beam(el, wr, 0.17, c)
    k.cyl(-0.1, wr.y, wr.z - 0.1, 0.1, 0.1, 0.2, 'steelDark', seg=8, rot=(0, 90, 0))
    k.beam(wr, wr + Vector((0, -0.1, -0.3)), 0.1, 'steel2')
    tip = wr + Vector((0, -0.1, -0.32))
    if tool == 'claw':
        for sx in (-1, 1):
            k.bx(tip.x + sx * 0.06 - 0.02, tip.x + sx * 0.06 + 0.02, tip.y - 0.03, tip.y + 0.03, tip.z - 0.22, tip.z, 'steelDark', ink=False)
    else:   # welder: torch + spark star
        k.beam(tip, tip + Vector((0, -0.05, -0.2)), 0.04, 'steelDark', ink=False)
        p = tip + Vector((0, -0.05, -0.24))
        spark_star(k, p.x, p.y - 0.004, p.z, 0.16)
    k.beam((0.2, 0.0, 0.6), (0.18, -0.4, 1.6), 0.04, 'hose', ink=False)
    k.pop()


def skid(k):
    """Line carrier: a yellow skid deck on four wheels that ride the floor rails (y = +-1.1, rail top 0.1)."""
    k.bx(-1.75, 1.75, -1.0, 1.0, 0.32, 0.5, 'hazard')
    for f in (-1, 1):
        k.stripes(-1.7, 1.7, 0.34, 0.48, f * 1.003, f, 8)
        for x in (-1.3, 1.3):
            k.bx(x - 0.22, x + 0.22, *srt(f * 0.98, f * 1.2), 0.28, 0.48, 'steelDark', ink=False)
            k.cyl(x, 1.04 if f > 0 else -1.16, 0.27, 0.17, 0.17, 0.12, 'rubber', seg=8, rot=(-90, 0, 0))


# ================================================================ walker mech (bipedal, ~6.6 m)
def walker(k, stage, skid_on=True, x=0.0, y=0.0, z=0.0, s=1.0, deg=0):
    """Bipedal walker mech, front -Y, shoulders along X (|x| <= 1.8, |y| <= 1.3). stage 0 bare chassis frame on a jig,
    1 drivetrain fitted (actuators, hydraulics, feet, power core), 2 armour plated in primer, 3 painted + finished."""
    k.push(x, y, deg, z, s=s)
    if skid_on:
        skid(k)
    B = 0.5 if skid_on else 0.0               # base of the feet
    P = stage == 3
    frame = 'steel2'
    arm_c = 'orange' if P else 'primer'
    arm_c2 = 'cream' if P else 'primer2'
    # ---- frame (every stage)
    for sx in (-1, 1):
        hip = Vector((sx * 0.62, 0.12, B + 3.55))
        knee = Vector((sx * 0.85, -0.45, B + 2.05))
        ank = Vector((sx * 0.95, -0.05, B + 0.62))
        k.beam(hip, knee, 0.22, frame)
        k.beam(knee, ank, 0.2, frame)
        k.bx(sx * 0.95 - 0.36, sx * 0.95 + 0.36, -0.75, 0.55, B, B + 0.14, 'steelDark')          # foot plate
        k.beam((sx * 1.2, 0.2, B + 4.85), (sx * 1.62, 0.15, B + 3.35), 0.16, frame)              # upper arm strut
        k.beam((sx * 1.62, 0.15, B + 3.35), (sx * 1.6, -0.75, B + 2.85), 0.15, frame)            # forearm strut
    k.bx(-0.85, 0.85, -0.5, 0.65, B + 3.35, B + 3.75, frame)                                     # pelvis box
    k.bx(-0.16, 0.16, -0.05, 0.27, B + 3.75, B + 5.6, 'steelDark')                               # spine
    for sx in (-1, 1):                                                                           # torso cage
        for yy in (-0.75, 0.85):
            k.bx(sx * 1.1 - 0.07, sx * 1.1 + 0.07, yy - 0.07, yy + 0.07, B + 3.75, B + 5.55, frame, ink=stage == 0)
    for zz in (B + 3.85, B + 5.55):
        for yy in (-0.75, 0.85):
            k.bx(-1.03, 1.03, yy - 0.06, yy + 0.06, zz - 0.06, zz + 0.06, frame, ink=stage == 0)
    k.bx(-1.25, 1.25, -0.07, 0.31, B + 5.4, B + 5.66, 'steelDark')                              # shoulder beam
    if stage == 0:
        # jig: orange posts hold the unpowered frame up; weld marks
        for sx in (-1, 1):
            k.bx(sx * 0.42 - 0.09, sx * 0.42 + 0.09, 0.66, 0.84, B + 0.12, B + 3.37, 'orange')
            k.bx(sx * 0.42 - 0.14, sx * 0.42 + 0.14, 0.6, 0.9, B, B + 0.12, 'orange2', ink=False)
        k.bx(-0.6, 0.6, 0.68, 0.82, B + 1.6, B + 1.75, 'orange2')
        for (wx, wz) in ((-1.03, B + 3.85), (1.03, B + 5.55), (0.85, B + 3.75)):
            k.cyl(wx, -0.82, wz, 0.05, 0.05, 0.02, 'weld', seg=6, rot=(90, 0, 0), ink=False)
        k.pop()
        return
    # ---- drivetrain (stage 1+)
    for sx in (-1, 1):
        hip = Vector((sx * 0.62, 0.12, B + 3.55))
        knee = Vector((sx * 0.85, -0.45, B + 2.05))
        ank = Vector((sx * 0.95, -0.05, B + 0.62))
        # joint drums along X through the hip, knee and ankle
        k.cyl(sx * 0.42, 0.12, B + 3.55, 0.32, 0.32, 0.4, 'steelDark', seg=10, rot=(0, 90 * sx, 0))
        k.cyl(sx * 0.67, -0.45, B + 2.05, 0.26, 0.26, 0.36, 'steelDark', seg=10, rot=(0, 90 * sx, 0))
        k.cyl(sx * 0.8, -0.05, B + 0.62, 0.2, 0.2, 0.3, 'steelDark', seg=8, rot=(0, 90 * sx, 0))
        # hydraulics: dark cylinder + chrome rod behind the thigh, in front of the shin
        k.beam(hip + Vector((sx * 0.12, 0.42, -0.25)), (hip + knee) / 2 + Vector((sx * 0.12, 0.45, 0)), 0.16, 'steelDark', ink=False)
        k.beam((hip + knee) / 2 + Vector((sx * 0.12, 0.45, 0)), knee + Vector((sx * 0.12, 0.38, 0.2)), 0.08, 'chrome', ink=False)
        k.beam(knee + Vector((sx * 0.1, -0.32, -0.2)), (knee + ank) / 2 + Vector((sx * 0.1, -0.36, 0)), 0.15, 'steelDark', ink=False)
        k.beam((knee + ank) / 2 + Vector((sx * 0.1, -0.36, 0)), ank + Vector((sx * 0.1, -0.3, 0.25)), 0.07, 'chrome', ink=False)
        # foot: heel block + toes
        k.bx(sx * 0.95 - 0.3, sx * 0.95 + 0.3, -0.2, 0.5, B + 0.14, B + 0.42, 'steelDark' if not P else 'cream2')
        for tx in (-0.22, 0.22):
            k.bx(sx * 0.95 + tx - 0.12, sx * 0.95 + tx + 0.12, -0.95, -0.2, B + 0.02, B + 0.3, 'rubber' if not P else 'orange2')
        # arm: shoulder drum, elbow, gun mount
        k.cyl(sx * 1.25, 0.12, B + 5.0, 0.28, 0.28, 0.32, 'steelDark', seg=10, rot=(0, 90 * sx, 0))
        k.cyl(sx * 1.62, 0.15, B + 3.35 - 0.17, 0.17, 0.17, 0.12, 'steelDark', seg=8)
        k.beam((sx * 1.15, 0.5, B + 5.3), (sx * 0.95, 0.45, B + 3.8), 0.07, 'hose', ink=False)
    k.cyl(0, 0.1, B + 4.1, 0.42, 0.42, 0.85, 'steelDark', seg=10)                                # power core can
    k.cyl(0, 0.1, B + 4.95, 0.3, 0.2, 0.18, 'core', seg=10, ink=False)
    if stage == 1:
        k.bx(-0.5, 0.5, 0.95, 1.25, B + 4.0, B + 4.9, 'hose')                                   # cable loom pack
        k.pop()
        return
    # ---- armour (stage 2 primer, stage 3 paint)
    body = 'orange' if P else 'primer'
    body2 = 'cream' if P else 'primer2'
    trim = 'orange2' if P else 'primer'
    # torso shell: chunky hull, chest plate, back pack
    k.hullp([(-1.28, -0.95, B + 3.8), (1.28, -0.95, B + 3.8), (1.28, 0.95, B + 3.8), (-1.28, 0.95, B + 3.8),
             (-1.42, -1.1, B + 4.7), (1.42, -1.1, B + 4.7), (1.42, 1.0, B + 4.8), (-1.42, 1.0, B + 4.8),
             (-1.15, -0.85, B + 5.85), (1.15, -0.85, B + 5.85), (1.15, 0.95, B + 5.85), (-1.15, 0.95, B + 5.85)], body)
    k.hullp([(-0.95, -1.13, B + 4.25), (0.95, -1.13, B + 4.25), (-0.8, -1.2, B + 5.3), (0.8, -1.2, B + 5.3),
             (-0.95, -0.9, B + 4.25), (0.95, -0.9, B + 4.25), (-0.8, -0.9, B + 5.4), (0.8, -0.9, B + 5.4)], body2)
    k.bx(-0.85, 0.85, 0.97, 1.3, B + 4.1, B + 5.5, 'steelDark' if P else 'primer2')               # back pack
    for i in range(3):
        k.cyl(-0.5 + i * 0.5, 1.15, B + 5.5, 0.1, 0.1, 0.35, 'steelDark', seg=6)                    # vents / stacks
    # sensor head: a low block with a horizontal sensor slot (no eyes, no face) and two lamps
    k.bx(-0.55, 0.55, -0.65, 0.55, B + 5.85, B + 6.35, trim)
    k.bx(-0.45, 0.45, -0.68, -0.6, B + 6.02, B + 6.16, 'ink', ink=False)
    k.qy(-0.42, 0.42, B + 6.05, B + 6.13, -0.683, -1, 'amber' if P else 'steelDark')
    k.cyl(0.0, 0.0, B + 6.35, 0.06, 0.04, 0.45, 'steelDark', seg=6, ink=False)                   # antenna
    # shoulder pauldrons
    for sx in (-1, 1):
        k.hullp([(sx * 1.15, -0.75, B + 5.0), (sx * 1.8, -0.75, B + 5.05), (sx * 1.8, 0.85, B + 5.05), (sx * 1.15, 0.85, B + 5.0),
                 (sx * 1.15, -0.6, B + 5.95), (sx * 1.7, -0.6, B + 5.75), (sx * 1.7, 0.7, B + 5.75), (sx * 1.15, 0.7, B + 5.95)], body2)
        # forearm gun pod
        k.bx(sx * 1.6 - 0.2, sx * 1.6 + 0.2, -0.95, 0.35, B + 2.6, B + 3.15, arm_c)
        k.cyl(sx * 1.6, -0.95, B + 2.88, 0.11, 0.11, 0.55, 'steelDark', seg=8, rot=(90, 0, 0))
        # thigh and shin plates (boxes along the leg directions)
        hip = Vector((sx * 0.62, 0.12, B + 3.55))
        knee = Vector((sx * 0.85, -0.45, B + 2.05))
        ank = Vector((sx * 0.95, -0.05, B + 0.62))
        k.beam(hip + Vector((sx * 0.02, -0.05, -0.15)), knee + Vector((sx * 0.02, -0.02, 0.3)), 0.5, body)
        k.beam(knee + Vector((sx * 0.02, -0.12, -0.25)), ank + Vector((sx * 0.02, -0.22, 0.32)), 0.46, body2)
        k.bx(sx * 0.85 - 0.3, sx * 0.85 + 0.3, -0.85, -0.6, B + 1.85, B + 2.3, trim)               # knee guard
        # hip skirt
        k.bx(sx * 0.62 - 0.36, sx * 0.62 + 0.36, -0.78, -0.62, B + 3.1, B + 3.75, trim)
    if P:
        # finish: shoulder lamps, chest core dome, hazard chevrons on the shins, stencil numbers on the shoulders
        for sx in (-1, 1):
            k.cyl(sx * 1.45, -0.62, B + 5.7, 0.13, 0.13, 0.1, 'steelDark', seg=8, rot=(90, 0, 0))
            k.cyl(sx * 1.45, -0.72, B + 5.7, 0.1, 0.1, 0.01, 'lamp', seg=8, rot=(90, 0, 0), ink=False)
        k.cyl(0, -1.15, B + 4.75, 0.24, 0.12, 0.16, 'teal', seg=10, rot=(90, 0, 0))
        stencil_digit(k, 7, -0.8, B + 3.22, 0.3, 0.42, -0.78, -1, c='cream', dy=0.003)
        stencil_digit(k, 4, 0.46, B + 3.22, 0.3, 0.42, -0.78, -1, c='cream', dy=0.003)
    k.pop()


# ================================================================ tread bruiser (dumpster tank, ~4.4 m)
def bruiser(k, stage, skid_on=True, x=0.0, y=0.0, z=0.0, s=1.0, deg=0):
    """Tracked bruiser, front (ram) +X, treads along X (|x| <= 1.85, |y| <= 1.3). stage 0 bare hull frame, 1 drivetrain
    (road wheels, sprockets, tread loops, engine and stacks), 2 armoured dumpster hull in primer, 3 painted + finished."""
    k.push(x, y, deg, z, s=s)
    if skid_on:
        skid(k)
    B = 0.5 if skid_on else 0.0
    P = stage == 3
    frame = 'steel2'
    for f in (-1, 1):
        k.bx(-1.7, 1.7, *srt(f * 0.45, f * 0.7), B + 0.75, B + 1.0, frame)                          # chassis rails
        k.bx(-1.65, 1.65, *srt(f * 0.86, f * 1.0), B + 0.35, B + 0.48, frame, ink=stage == 0)     # tread frame low
        k.bx(-1.55, 1.55, *srt(f * 0.86, f * 1.0), B + 1.18, B + 1.3, frame, ink=stage == 0)      # tread frame high
        for xx in (-1.45, 0.0, 1.45):
            k.bx(xx - 0.06, xx + 0.06, *srt(f * 0.87, f * 0.99), B + 0.48, B + 1.18, frame, ink=False)
    for xx in (-1.4, -0.2, 1.0):
        k.bx(xx - 0.08, xx + 0.08, -0.86, 0.86, B + 0.78, B + 0.97, frame, ink=False)                # cross members
    for (cx, cy) in ((-1.35, -0.55), (1.35, -0.55), (-1.35, 0.55), (1.35, 0.55)):                 # bin frame posts
        k.bx(cx - 0.07, cx + 0.07, cy - 0.07, cy + 0.07, B + 1.0, B + 2.95, frame, ink=stage == 0)
    for f in (-1, 1):
        k.bx(-1.42, 1.42, f * 0.55 - 0.06, f * 0.55 + 0.06, B + 2.95, B + 3.07, frame, ink=stage == 0)
    if stage == 0:
        for xx in (-1.0, 1.0):                                                                    # jig stands
            k.bx(xx - 0.25, xx + 0.25, -0.35, 0.35, B, B + 0.75, 'orange')
        k.cyl(0.6, -0.72, B + 0.88, 0.05, 0.05, 0.02, 'weld', seg=6, rot=(90, 0, 0), ink=False)
        k.cyl(-0.9, -0.72, B + 0.88, 0.05, 0.05, 0.02, 'weld', seg=6, rot=(90, 0, 0), ink=False)
        k.pop()
        return
    # ---- drivetrain
    for f in (-1, 1):
        y0, y1 = srt(f * 1.02, f * 1.3)
        for xx in (-1.0, -0.33, 0.33, 1.0):                                                       # road wheels
            k.cyl(xx, 1.04 if f > 0 else -1.28, B + 0.38, 0.27, 0.27, 0.24, 'steelDark', seg=8, rot=(-90, 0, 0))
        # tread loop: top and bottom runs, end drums (cap faces inset 1 cm from the runs' sides)
        k.bx(-1.55, 1.55, y0, y1, B + 0.0, B + 0.12, 'tread')
        k.bx(-1.55, 1.55, y0, y1, B + 1.0, B + 1.12, 'tread')
        for xx in (-1.55, 1.55):
            k.cyl(xx, y0 + 0.01, B + 0.56, 0.56, 0.56, 0.26, 'tread', seg=10, rot=(-90, 0, 0))
            k.cyl(xx, (y1 - 0.01) if f > 0 else (y0 - 0.01), B + 0.56, 0.22, 0.22, 0.02, 'steel2', seg=8, rot=(-90, 0, 0), ink=False)
        for i in range(9):                                                                         # grousers on the top run
            xx = -1.4 + i * 0.35
            k.bx(xx - 0.05, xx + 0.05, y0 - 0.005, y1 + 0.005, B + 1.12, B + 1.17, 'steelDark', ink=False)
    k.bx(-1.5, -0.5, -0.5, 0.5, B + 1.02, B + 1.9, 'steelDark')                                    # engine
    for i, yy in enumerate((-0.4, 0.0, 0.4)):                                                       # three exhaust stacks
        k.cyl(-1.25, yy, B + 1.9, 0.12, 0.12, 2.0 + 0.15 * i, 'steel2', seg=8)
        k.cyl(-1.25, yy, B + 3.9 + 0.15 * i, 0.135, 0.135, 0.12, 'ink', seg=8, ink=False)
    for f in (-1, 1):                                                                               # ram arms
        k.beam((1.0, f * 0.55, B + 1.05), (1.75, f * 0.6, B + 1.5), 0.16, 'steelDark')
        k.beam((1.2, f * 0.4, B + 1.6), (1.7, f * 0.45, B + 1.55), 0.07, 'chrome', ink=False)
    k.cyl(0.3, 0.0, B + 1.0, 0.36, 0.36, 0.7, 'steelDark', seg=10)                                  # power core can
    k.cyl(0.3, 0.0, B + 1.7, 0.24, 0.16, 0.14, 'core', seg=10, ink=False)
    if stage == 1:
        k.pop()
        return
    # ---- armour: dumpster hull, lid, skirts, ram plow, sensor block
    body = 'paintT' if P else 'primer'
    body2 = 'cream' if P else 'primer2'
    k.hullp([(-1.45, -0.86, B + 1.3), (1.45, -0.86, B + 1.3), (1.45, 0.86, B + 1.3), (-1.45, 0.86, B + 1.3),
             (-1.62, -1.02, B + 3.15), (1.62, -1.02, B + 3.15), (1.62, 1.02, B + 3.15), (-1.62, 1.02, B + 3.15)], body)
    k.bx(-1.7, 1.7, -1.1, 1.1, B + 3.15, B + 3.3, 'paintT2' if P else 'primer2')                    # rim
    k.hullp([(-1.6, -1.0, B + 3.3), (1.6, -1.0, B + 3.3), (1.6, 1.0, B + 3.3), (-1.6, 1.0, B + 3.3),
             (-1.45, -0.9, B + 3.72), (1.45, -0.9, B + 3.45), (1.45, 0.9, B + 3.45), (-1.45, 0.9, B + 3.72)], body2)   # lid
    for f in (-1, 1):
        k.bx(-1.6, 1.4, *srt(f * 1.31, f * 1.36), B + 0.62, B + 1.3, body)                             # skirts
        for xx in (-1.1, 0.0, 1.0):                                                                    # skirt bolts
            k.cyl(xx, f * 1.36, B + 0.96, 0.07, 0.07, 0.025, 'steelDark', seg=6, rot=(-90 if f > 0 else 90, 0, 0), ink=False)
        # number board on the hull side (a vertical plate on the sloped side)
        k.bx(-0.75, 0.55, *srt(f * 0.94, f * 1.0), B + 1.85, B + 2.8, body2 if P else 'primer')
    k.hullp([(1.62, -1.2, B + 0.25), (1.62, 1.2, B + 0.25), (1.95, -1.25, B + 0.15), (1.95, 1.25, B + 0.15),
             (1.62, -1.2, B + 1.55), (1.62, 1.2, B + 1.55), (1.85, -1.25, B + 1.4), (1.85, 1.25, B + 1.4)], 'orange' if P else 'primer')   # plow
    k.bx(-0.6, 0.6, -0.5, 0.5, B + 3.5, B + 3.95, 'steelDark')                                       # sensor block
    k.bx(0.6, 0.66, -0.4, 0.4, B + 3.74, B + 3.86, 'ink', ink=False)
    k.qx(-0.36, 0.36, B + 3.77, B + 3.83, 0.663, 1, 'amber' if P else 'steelDark')
    if P:
        for yy in (-0.8, 0.8):                                                                         # lamps on the plow
            k.cyl(1.86, yy, B + 1.1, 0.12, 0.12, 0.12, 'steelDark', seg=8, rot=(0, 90, 0))
            k.cyl(1.98, yy, B + 1.1, 0.09, 0.09, 0.01, 'lamp', seg=8, rot=(0, 90, 0), ink=False)
        k.cyl(-0.5, 0.0, B + 3.6, 0.3, 0.16, 0.22, 'teal', seg=10)                                      # core dome on the lid
        k.stripes(-1.5, 1.3, B + 0.68, B + 0.98, -1.363, -1, 10, ca='hazard')                         # skirt hazard band
        stencil_digit(k, 2, -0.6, B + 2.0, 0.42, 0.66, -1.0, -1, c='paintT2', dy=0.003)
        stencil_digit(k, 9, -0.05, B + 2.0, 0.42, 0.66, -1.0, -1, c='paintT2', dy=0.003)
    k.pop()


# ================================================================ wall modules
def siding_ribs(k, z0, z1, y, s, x0=-0.5, x1=0.5, c='tealS2', n=4):
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        k.qy(x - 0.035, x + 0.035, z0 + 0.01, z1 - 0.01, y, s, c)


def wall_inner(k, x0, x1, win, pipes=True, rx=None):
    """Room side of a module: oxide block plinth, teal siding, girt, crane runway on corbels, roof edge."""
    k.bx(x0, x1, -0.53, -0.5, 0.0, 3.2, 'oxide', ink=False)                       # plinth
    for z in (0.8, 1.6, 2.4):
        k.qy(x0, x1, z - 0.014, z + 0.014, -0.533, -1, 'oxide2')
    k.stripes(x0, x1, 0.02, 0.26, -0.533, -1, 4, ca='hazard')
    k.bx(x0, x1, -0.57, -0.5, 3.2, 3.3, 'steelDark', ink=False)                     # plinth cap
    siding_ribs(k, 3.3, RAIL - 0.5, -0.503, -1, x0=x0, x1=x1)
    k.bx(x0, x1, -0.62, -0.5, 6.0, 6.2, 'oxide2', ink=False)                        # girt
    if pipes:
        for zz, r, c in ((4.5, 0.12, 'steel2'),):
            k.cyl(x0, -0.8, zz, r, r, x1 - x0, c, seg=6, rot=(0, 90, 0), ink=False)
    # crane runway: rail girder on a corbel (continuous along the hall)
    r0, r1 = rx or (x0, x1)   # the runway stops well short of an inside corner (the other wall's runway crosses there)
    if r1 > r0 + 0.05:
        k.bx(r0, r1, -1.12, -0.5, RAIL - 0.5, RAIL - 0.2, 'orange2', ink=False)
        k.bx(r0, r1, -1.1, -0.82, RAIL - 0.2, RAIL, 'orange')
        k.bx(r0, r1, -1.0, -0.92, RAIL, RAIL + 0.08, 'steelDark', ink=False)        # rail
    siding_ribs(k, RAIL + 0.02, (WIN0 - 0.1) if win else 15.6, -0.503, -1, x0=x0, x1=x1)
    k.bx(x0, x1, -0.58, -0.5, 15.7, WALL_H, 'roofEdge', ink=False)


def wall_outer(k, win):
    k.bx(-0.497, 0.497, 0.5, 0.53, 0.0, (WIN0 - 0.1) if win else WALL_H - 0.4, 'cream', ink=False)
    siding_ribs(k, 0.3, (WIN0 - 0.15) if win else WALL_H - 0.45, 0.533, 1, c='cream2')
    if win:
        k.bx(-0.497, 0.497, 0.5, 0.53, WIN1 + 0.05, WALL_H - 0.4, 'cream', ink=False)
    k.bx(-0.497, 0.497, 0.5, 0.62, WALL_H - 0.4, WALL_H - 0.25, 'roofEdge', ink=False)


def wall_module(k, kind, endL=False, endR=False):
    k.begin()
    win = kind.startswith('Win')
    x0 = -0.497 + (0.14 if endL else 0.0)
    x1 = 0.497 - (0.14 if endR else 0.0)
    if win:
        k.bx(-0.5, 0.5, -0.5, 0.5, 0, WIN0, 'tealS')
        k.bx(-0.5, 0.5, -0.5, 0.5, WIN1, WALL_H, 'tealS')
        k.bx(-0.497, 0.497, -0.6, -0.5, WIN0 - 0.08, WIN0 + 0.02, 'roofEdge')       # sill
        k.bx(-0.06, 0.06, -0.1, 0.1, WIN0 + 0.02, WIN1, 'roofEdge')                # mullion
        k.bx(-0.5, 0.5, -0.08, 0.08, 13.15, 13.25, 'roofEdge', ink=False)          # transom
        if kind == 'Win_B':
            k.poly([(-0.4, -0.02, 11.8), (-0.32, -0.02, 11.8), (0.0, -0.02, 12.8), (-0.08, -0.02, 12.8)], 'glint', (0, -1, 0))
            k.poly([(0.12, -0.02, 13.5), (0.18, -0.02, 13.5), (0.42, -0.02, 14.6), (0.36, -0.02, 14.6)], 'glint', (0, -1, 0))
    else:
        k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'tealS')
    wall_inner(k, x0, x1, win, pipes=not (endL or endR), rx=(-0.497 + (0.68 if endL else 0.0), 0.497 - (0.68 if endR else 0.0)))
    wall_outer(k, win)
    if kind in ('Win_Panel', 'Panel'):
        k.bx(-0.36, 0.06, -0.78, -0.53, 1.0, 2.2, 'panel')
        k.qy(-0.3, 0.0, 1.95, 2.1, -0.783, -1, 'hazard')
        k.qy(-0.32, -0.04, 1.1, 1.85, -0.783, -1, 'steel2')
        k.bx(-0.03, 0.03, -0.62, -0.56, 2.2, 4.25, 'steelDark', ink=False)
        k.bx(0.15, 0.38, -0.66, -0.53, 1.3, 1.6, 'steel2')
        k.qy(0.2, 0.33, 1.42, 1.52, -0.663, -1, 'teal')
    elif kind == 'Win_Sign':
        # a big stencilled bay number on the siding
        k.qy(-0.47, 0.47, 6.4, 8.6, -0.506, -1, 'cream')
        stencil_digit(k, 2, -0.36, 6.7, 0.3, 1.5, -0.506, -1, c='oxide')
        stencil_digit(k, 7, 0.06, 6.7, 0.3, 1.5, -0.506, -1, c='oxide')
    elif kind == 'Win_Duct':
        k.bx(-0.36, 0.36, -1.05, -0.62, 3.34, 8.6, 'steel2')                        # extraction duct up the wall
        k.bx(-0.4, 0.4, -1.1, -0.6, 3.3, 3.6, 'steelDark', ink=False)
        k.qy(-0.3, 0.3, 3.8, 4.4, -1.053, -1, 'steelDark')
        for z in (4.9, 6.6, 8.2):
            k.bx(-0.39, 0.39, -1.08, -0.6, z, z + 0.1, 'steelDark', ink=False)
    elif kind == 'Win_Hose':
        k.bx(-0.2, 0.2, -0.75, -0.53, 1.2, 1.9, 'red')
        k.cyl(0, -0.76, 1.55, 0.15, 0.15, 0.02, 'rubber', seg=10, rot=(90, 0, 0), ink=False)
        k.qy(-0.12, 0.12, 2.0, 2.15, -0.536, -1, 'red')
    FD.wall_detail(k, kind, endL, endR)
    return k


def column(k):
    """Wall pier every 6 m: a heavy orange I-beam column carrying the crane runway corbel, hazard foot."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'tealS')
    wall_inner(k, -0.497, 0.497, False)
    wall_outer(k, False)
    k.bx(-0.34, 0.34, -1.18, -1.08, 0.0, RAIL - 0.5, 'orange')                    # flanges
    k.bx(-0.34, 0.34, -0.66, -0.56, 0.0, CEIL, 'orange')
    k.bx(-0.05, 0.05, -1.08, -0.66, 0.0, RAIL - 0.5, 'orange2', ink=False)
    k.bx(-0.34, 0.34, -1.18, -1.1, RAIL + 0.1, CEIL, 'orange')                     # column above the runway
    k.bx(-0.05, 0.05, -1.1, -0.66, RAIL + 0.1, CEIL, 'orange2', ink=False)
    k.bx(-0.44, 0.44, -1.26, -0.53, 0.0, 0.08, 'steelDark', ink=False)
    k.stripes(-0.34, 0.34, 0.1, 1.5, -1.183, -1, 4, ca='hazard')
    k.qy(-0.22, 0.22, 2.6, 2.95, -1.186, -1, 'cream')
    k.qy(-0.13, 0.13, 2.68, 2.87, -1.189, -1, 'oxide')
    FD.column_detail(k)
    return k


def corner(k):
    """Corners, notches, free-standing piers: concrete with orange hazard wraps (all-round)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'conc')
    for s in (-1, 1):
        k.stripes(-0.5, 0.5, 0.0, 1.4, s * 0.506, s, 4, ca='orange')
        k.qx(-0.5, 0.5, 0.0, 1.4, s * 0.506, s, 'orange')
        for z in (0.15, 0.75):
            k.poly([(s * 0.509, -0.5, z), (s * 0.509, 0.5, z + 0.3), (s * 0.509, 0.5, z + 0.5), (s * 0.509, -0.5, z + 0.2)], 'ink', (s, 0, 0))
    for s in (-1, 1):
        k.qy(-0.5, 0.5, 3.2, 3.26, s * 0.503, s, 'conc2')
        k.qx(-0.5, 0.5, 3.2, 3.26, s * 0.503, s, 'conc2')
    return k


def block_wall(k, kind):
    """Interior walls: oxide plinth, cream block above, to the roof."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H, 'cream')
    k.qy(-0.5, 0.5, 0.0, 3.2, -0.503, -1, 'oxide')
    for z in (0.8, 1.6, 2.4):
        k.qy(-0.5, 0.5, z - 0.014, z + 0.014, -0.506, -1, 'oxide2')
    for z in (4.0, 4.8, 5.6, 6.4):
        k.qy(-0.5, 0.5, z - 0.012, z + 0.012, -0.503, -1, 'cream2')
    k.stripes(-0.5, 0.5, 0.02, 0.26, -0.506, -1, 4, ca='hazard')
    if kind == 'Arrow':
        k.poly([(-0.35, -0.509, 1.6), (0.1, -0.509, 1.6), (0.1, -0.509, 1.4), (0.42, -0.509, 1.8), (0.1, -0.509, 2.2), (0.1, -0.509, 2.0), (-0.35, -0.509, 2.0)], 'cream', (0, -1, 0))
    elif kind == 'Num':
        stencil_digit(k, 1, -0.42, 4.2, 0.36, 1.3, -0.503, -1, c='tealS')
        stencil_digit(k, 6, 0.06, 4.2, 0.36, 1.3, -0.503, -1, c='tealS')
    return k


# ================================================================ ceiling bays, gate, trail, hatch
def ceil_bay(k, crane=None):
    """12 x 12 m roof bay at the ceiling plane: a deep Warren truss along X, purlins, crane runway beams along X at
    y = +-4.6, a high-bay lamp with its pool painted on the floor 16 m below; crane: a bridge crane on the runways with
    a trolley and hook block carrying an armour plate ('Plate') or a mech leg ('Leg')."""
    k.begin()
    D = -CEIL
    k.bx(-5.95, 5.95, -0.14, 0.14, -2.0, -1.84, 'orange')                    # bottom chord
    k.bx(-5.95, 5.95, -0.14, 0.14, -0.16, -0.02, 'orange')                   # top chord
    for i in range(6):
        x0 = -6.0 + i * 2.0
        k.beam((x0 + 0.06, 0, -1.84), (x0 + 1.0, 0, -0.16), 0.11, 'orange2', ink=False)
        k.beam((x0 + 1.0, 0.008, -0.16), (x0 + 1.94, 0.008, -1.84), 0.11, 'orange2', ink=False)
    for x in (-4.5, -1.5, 1.5, 4.5):
        k.bx(x - 0.08, x + 0.08, -5.95, 5.95, -0.32, -0.19, 'steel2', ink=False)
    for y in (-4.55, 4.55):                                                       # runway beams (clear of the walls)
        k.bx(-5.995, 5.995, y - 0.16, y + 0.16, -2.9, -2.5, 'steelDark')
        k.bx(-5.995, 5.995, y - 0.05, y + 0.05, -2.5, -0.3, 'steel2', ink=False)
    # lamp
    k.bx(-0.02, 0.02, 2.98, 3.02, -3.4, -0.02, 'steelDark', ink=False)
    k.cyl(0, 3.0, -4.0, 0.7, 0.2, 0.6, 'steelDark', seg=10)
    k.cyl(0, 3.0, -4.02, 0.64, 0.64, 0.004, 'lamp', seg=10, ink=False)
    pool_disc(k, 0.0, 3.0, D + Z['pool'], 3.4, 4)
    if crane:
        cx = -2.6 if crane == 'Plate' else 2.4
        for f in (-1, 1):                                                       # bridge girders
            k.bx(cx + f * 0.55 - 0.16, cx + f * 0.55 + 0.16, -4.8, 4.8, -3.65, -2.95, 'orange')
        for y in (-4.55, 4.55):                                                   # end trucks on the runways
            k.bx(cx - 1.0, cx + 1.0, y - 0.3, y + 0.3, -3.3, -2.92, 'steelDark')
        k.qx(-4.0, 4.0, -3.55, -3.05, cx + 0.555 + 0.16 + 0.003, 1, 'hazard')
        ty = 0.8 if crane == 'Plate' else -0.6       # loads stay clear of the bays' edges (zone walls)
        k.bx(cx - 0.75, cx + 0.75, ty - 0.6, ty + 0.6, -2.94, -2.4, 'hazard')    # trolley
        k.bx(cx - 0.3, cx + 0.3, ty - 0.35, ty + 0.35, -3.9, -3.66, 'steelDark')  # hoist drum under it
        # loads hang short, lying flat, so they stay above everything on the floor (> 11 m)
        for dx in (-0.12, 0.12):
            k.bx(cx + dx - 0.015, cx + dx + 0.015, ty - 0.015, ty + 0.015, -4.1, -3.9, 'steelDark', ink=False)
        k.bx(cx - 0.3, cx + 0.3, ty - 0.15, ty + 0.15, -4.35, -4.1, 'hazard')       # hook block
        k.stripes(cx - 0.3, cx + 0.3, -4.33, -4.12, ty - 0.153, -1, 4)
        if crane == 'Plate':
            # spreader bar + an armour plate on four slings
            k.bx(cx - 1.2, cx + 1.2, ty - 0.06, ty + 0.06, -4.5, -4.42, 'steelDark')
            for dx in (-1.1, 1.1):
                for dy in (-0.7, 0.7):
                    k.beam((cx + dx, ty + dy * 0.1, -4.45), (cx + dx, ty + dy, -4.62), 0.025, 'steelDark', ink=False)
            k.bx(cx - 0.03, cx + 0.03, ty - 0.03, ty + 0.03, -4.42, -4.35, 'steelDark', ink=False)
            k.hullp([(cx - 1.35, ty - 0.92, -4.86), (cx + 1.35, ty - 0.92, -4.86), (cx - 1.35, ty + 0.92, -4.86), (cx + 1.35, ty + 0.92, -4.86),
                     (cx - 1.2, ty - 0.8, -4.62), (cx + 1.2, ty - 0.8, -4.62), (cx - 1.2, ty + 0.8, -4.62), (cx + 1.2, ty + 0.8, -4.62)], 'primer')
            k.qz(cx - 0.8, cx + 0.8, ty - 0.12, ty + 0.12, -4.617, 1, 'primer2')
        else:
            # a walker leg (thigh, knee drum, shin, foot) slung lying flat
            for dx in (-0.8, 0.6):
                k.beam((cx + dx * 0.12, ty, -4.35), (cx + dx, ty, -4.5), 0.025, 'steelDark', ink=False)
            k.beam((cx - 1.4, ty, -4.7), (cx - 0.1, ty, -4.7), 0.44, 'primer')
            k.cyl(cx - 0.1, ty - 0.27, -4.7, 0.26, 0.26, 0.54, 'steelDark', seg=10, rot=(-90, 0, 0))
            k.beam((cx - 0.1, ty, -4.7), (cx + 1.15, ty, -4.72), 0.4, 'primer2')
            k.bx(cx + 1.15, cx + 1.45, ty - 0.35, ty + 0.35, -4.92, -4.5, 'steelDark')
    return k


def gate_frame(k):
    """Hall gate: hazard posts, a heavy header with a beacon and a zone board, roll housing, teal infill to the roof."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.495, s * 2.15)
        k.bx(x0, x1, -0.62, 0.62, 0, 3.34, 'steelDark')
        for f in (-1, 1):
            y = f * 0.623
            k.qy(x0 + 0.05, x1 - 0.05, 0.1, 3.1, y, f, 'orange')
            for i in range(5):
                z = 0.25 + i * 0.6
                k.poly([(x0 + 0.05, y + f * 0.003, z), (x1 - 0.05, y + f * 0.003, z + 0.25), (x1 - 0.05, y + f * 0.003, z + 0.45), (x0 + 0.05, y + f * 0.003, z + 0.2)], 'ink', (0, f, 0))
    k.bx(-2.35, 2.35, -0.72, 0.72, 3.3, 4.2, 'oxide')                         # header / roll housing
    k.bx(-2.45, 2.45, -0.25, 0.25, 4.2, WALL_H + 0.03, 'tealS')                # infill wall
    for f in (-1, 1):
        y = f * 0.253
        for i in range(12):
            x = -2.25 + i * 0.4
            k.qy(x - 0.035, x + 0.035, 4.25, WALL_H - 0.05, y, f, 'tealS2')
        yb = f * 0.723
        k.qy(-2.0, 2.0, 4.02, 4.1, yb, f, 'hazard')
        k.qy(-2.0, 2.0, 3.4, 3.48, yb, f, 'hazard')
        k.bx(-0.85, 0.85, *srt(f * 0.72, f * 0.76), 4.2, 5.2, 'cream')           # zone board on the header
        stencil_digit(k, 0, -0.6, 4.35, 0.42, 0.7, f * 0.763, f, c='oxide')
        stencil_digit(k, 2, 0.18, 4.35, 0.42, 0.7, f * 0.763, f, c='oxide')
        k.cyl(1.95, f * 0.5, 4.2, 0.13, 0.13, 0.16, 'steelDark', seg=8)          # beacons on the header
        k.cyl(1.95, f * 0.5, 4.36, 0.11, 0.08, 0.22, 'hot', seg=8)
    FD.gate_frame_detail(k)
    return k


def gate_shutter(k):
    k.begin()
    Hs, n = 3.05, 12
    h = (Hs - 0.35) / n
    for i in range(n):
        z0 = 0.35 + i * h
        k.bx(-1.5, 1.5, -0.06, 0.06, z0, z0 + h, 'tealS' if i % 2 else 'tealS2', ink=False)
    for f in (-1, 1):
        for x in (-0.9, -0.3, 0.3, 0.9):
            k.qy(x - 0.2, x + 0.2, 1.9, 2.05, f * 0.063, f, 'roofEdge')
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.35, 'ink' if j % 2 else 'orange', ink=False)
    FD.gate_shutter_detail(k)
    return k


def trail_wall(k):
    """Service corridor wall (1 m along Blender Y, corridor to +X): oxide plinth, pipes, half the lowered ceiling with a
    strip light; cream exterior siding on the back (-X)."""
    k.begin(90)
    k.bx(-0.5, 0.5, -0.25, 0.25, 0, WALL_H, 'tealS')
    k.bx(-0.5, 0.5, -0.28, -0.25, 0, 2.6, 'oxide', ink=False)
    for z in (0.8, 1.6):
        k.qy(-0.5, 0.5, z - 0.014, z + 0.014, -0.283, -1, 'oxide2')
    k.stripes(-0.5, 0.5, 0.02, 0.22, -0.283, -1, 4, ca='hazard')
    k.bx(-0.5, 0.5, -0.31, -0.25, 2.6, 2.68, 'steelDark', ink=False)
    siding_ribs(k, 2.68, ROOF - 0.05, -0.253, -1)
    for zz, r, c in ((3.25, 0.1, 'steel2'), (3.62, 0.07, 'orange'), (3.9, 0.05, 'hose')):
        k.cyl(-0.5, -0.45 - r, zz, r, r, 1.0, c, seg=6, rot=(0, 90, 0), ink=False)
    k.bx(-0.03, 0.03, -0.62, -0.25, 3.1, 4.0, 'steelDark', ink=False)
    y_mid = -2.25 + 0.003
    k.bx(-0.5, 0.5, y_mid, -0.25, ROOF, ROOF + 0.08, 'ceil', ink=False)
    k.qz(-0.5, 0.5, -1.02, -0.98, ROOF - 0.003, -1, 'steel2')
    k.bx(-0.5, 0.5, -1.75, -1.45, ROOF - 0.08, ROOF, 'steelDark', ink=False)
    k.qz(-0.5, 0.5, -1.7, -1.5, ROOF - 0.083, -1, 'lamp')
    k.qz(-0.5, 0.5, -0.75, -0.38, 0.012, 1, 'orange')
    k.bx(-0.5, 0.5, 0.25, 0.28, 0.0, WALL_H - 0.4, 'cream', ink=False)
    siding_ribs(k, 0.3, WALL_H - 0.45, 0.283, 1, c='cream2')
    FD.trail_detail(k)
    return k


def hatch(k):
    """Exit: the heavy dispatch lift. A chevron pad, a freight platform under a lift shaft that closes the roof slot."""
    k.begin()
    k.bx(-1.2, 1.2, -1.25, 1.0, 0, 0.05, 'steel2')
    for i in range(4):
        y = -1.15 + i * 0.5
        k.poly([(-0.9, y, 0.053), (0, y + 0.3, 0.053), (0.9, y, 0.053), (0.9, y + 0.14, 0.053), (0, y + 0.44, 0.053), (-0.9, y + 0.14, 0.053)], 'teal' if i % 2 else 'orange', (0, 0, 1))
    C0, C1, W = 1.05, 2.68, 1.3
    k.bx(-W, W, C0, C1, 0, 0.14, 'steelDark')
    k.qz(-W + 0.05, W - 0.05, C0 + 0.02, C0 + 0.14, 0.143, 1, 'hazard')
    for x in (-W, W):
        k.bx(x - 0.07, x + 0.07, C0 - 0.07, C0 + 0.07, 0.14, ROOF - 0.05, 'orange')
        k.bx(x - 0.07, x + 0.07, C1 - 0.12, C1 - 0.02, 0.14, ROOF - 0.05, 'orange')
        k.stripes(x - 0.07, x + 0.07, 0.2, 1.6, C0 - 0.073, -1, 4)
    k.bx(-W + 0.075, W - 0.075, C1 - 0.06, C1, 0.16, 3.0, 'steel2')
    for i in range(1, 9):
        x = -W + 2 * W * i / 9
        k.qy(x - 0.02, x + 0.02, 0.2, 2.95, C1 - 0.063, -1, 'steel')
    k.bx(-W - 0.07, W + 0.07, C0 - 0.08, C1, ROOF - 0.05, ROOF + 0.1, 'orange2')
    k.bx(-0.6, 0.6, C1 - 0.1, C1 - 0.06, 3.2, 3.8, 'cream')
    k.qy(-0.5, 0.5, 3.3, 3.7, C1 - 0.103, -1, 'ink')
    k.qy(-0.42, -0.1, 3.4, 3.6, C1 - 0.106, -1, 'core')
    k.qy(0.1, 0.42, 3.4, 3.6, C1 - 0.106, -1, 'teal')
    k.cyl(W - 0.2, C0 + 0.1, ROOF + 0.1, 0.1, 0.08, 0.18, 'hot', seg=8)
    for s in (-1, 1):
        x0, x1 = srt(s * 0.77, s * 0.95)
        k.bx(x0, x1, -1.55, 2.72, ROOF + 0.12, WALL_H - 0.04, 'tealS2')
    k.bx(-0.9, 0.9, -1.53, -0.97, ROOF + 0.13, WALL_H - 0.05, 'tealS2')
    for x in (-0.25, 0.25):
        k.bx(x - 0.02, x + 0.02, 1.8, 1.84, ROOF + 0.1, WALL_H - 0.6, 'steelDark', ink=False)
    k.cyl(0, 1.82, WALL_H - 0.9, 0.45, 0.45, 0.12, 'orange', seg=12, rot=(0, 90, 0))
    pool_disc(k, 0.0, 1.8, Z['hatch'], 1.2, 7)
    FD.hatch_detail(k)
    return k


# ================================================================ the build line (prefab 14 x 8, runs of 4)
LW = 3.62     # fence line (|y|)
TL = 7.0      # half tile length
ST0, ST1 = 2.5, 7.0   # station booth span (local x): the stage swap at x = 4.75
HO = 4.2      # house length at the run ends (the pop in / out at x = -+4.9)


def line_base(k):
    """Every line tile: floor track bed with two rails (the skids' wheels ride them), safety fences both sides."""
    k.qz(-TL, TL, -1.5, 1.5, Z['track'], 1, 'pit')
    for f in (-1, 1):
        k.qz(-TL, TL, *srt(f * 1.6, f * 1.75), Z['track'], 1, 'hazard')
        k.bx(-TL, TL, *srt(f * 1.04, f * 1.16), 0.0, 0.1, 'steel')
        # fence: posts, mesh, top rail, kick plate
        for x in (-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0):
            k.bx(x - 0.06, x + 0.06, *srt(f * (LW - 0.06), f * (LW + 0.06)), 0.0, 1.46, 'steelDark')
        k.bx(-TL, TL, *srt(f * (LW - 0.01), f * (LW + 0.01)), 0.16, 1.3, 'steelDark', ink=False)
        k.bx(-TL, TL, *srt(f * (LW - 0.03), f * (LW + 0.03)), 1.3, 1.4, 'orange')
        k.bx(-TL, TL, *srt(f * (LW - 0.04), f * (LW + 0.04)), 0.0, 0.16, 'hazard', ink=False)
    k.col(-TL, TL, -LW - 0.06, LW + 0.06, 0, 1.46)
    k.col(-TL, TL, -1.75, 1.75, 1.46, 5.2)       # the lane: the robots riding it are cover


def portal(k, xm, sg, W, H, low, c, curtain):
    """Mouth of a booth / house at x = xm, sg pointing inward: two posts and a lintel standing proud of the walls, a
    strip curtain hanging just inside."""
    pa, pb = srt(xm - sg * 0.05, xm + sg * 0.3)
    for f in (-1, 1):
        k.bx(pa, pb, *srt(f * (W - 0.15), f * (W + 0.22)), 0.0, H - 0.1, c)
    la, lb = srt(xm - sg * 0.07, xm + sg * 0.32)
    k.bx(la, lb, -W - 0.24, W + 0.24, H - low, H + 0.05, c)
    xc = xm + sg * 0.15
    n = 7
    for i in range(n):
        yy = -W + 0.15 + (2 * W - 0.3) * (i + 0.5) / n
        k.bx(xc - 0.01 - 0.005 * (i % 2), xc + 0.01 - 0.005 * (i % 2), yy - 0.33, yy + 0.33, 0.4, H - low - 0.004, curtain, ink=False)


def booth(k, kind, H=8.4, W=2.75):
    """A station booth over the lane (ST0..ST1): walls, roof, end portals with strip curtains at both mouths (the stage
    swap happens inside). kind: 'Drive' (weld curtains), 'Armour' (plate shop), 'Paint' (paint booth)."""
    x0, x1 = ST0, ST1
    wall = {'Drive': 'curtain', 'Armour': 'steel2', 'Paint': 'cream'}[kind]
    for f in (-1, 1):
        y0, y1 = srt(f * W, f * (W + 0.15))
        k.bx(x0, x1, y0, y1, 0.0, H, wall)
        yo = f * (W + 0.153)
        if kind == 'Drive':
            for i in range(1, 6):
                xx = x0 + (x1 - x0) * i / 6
                k.qy(xx - 0.02, xx + 0.02, 0.2, H - 0.8, yo, f, 'curtain2')
            spark_star(k, x0 + 1.2, yo + f * 0.003, 2.4, 0.35, s=f)
            spark_star(k, x0 + 3.1, yo + f * 0.003, 4.6, 0.25, s=f, c='spark2')
        elif kind == 'Paint':
            k.qy(x0 + 0.4, x1 - 0.4, 4.6, 5.6, yo, f, 'glassB')
            k.qy(x0 + 0.4, x1 - 0.4, 0.1, 0.5, yo, f, 'oxide')
            k.qy(x0 + 0.6, x0 + 1.6, 2.2, 3.2, yo, f, 'tealS')
            k.qy(x0 + 0.72, x0 + 1.48, 2.32, 3.08, yo + f * 0.003, f, 'cream')
            for i, c in enumerate(('orange', 'paintT', 'cream2')):                        # overspray streaks
                k.qy(x1 - 1.6 + i * 0.4, x1 - 1.35 + i * 0.4, 1.0, 3.6 - i * 0.5, yo, f, c)
        else:
            for zz in (2.0, 4.0, 6.0):
                k.qy(x0 + 0.1, x1 - 0.1, zz - 0.04, zz + 0.04, yo, f, 'steelDark')
            k.stripes(x0 + 0.1, x1 - 0.1, 0.05, 0.6, yo, f, 8)
        stencil_digit(k, {'Drive': 1, 'Armour': 2, 'Paint': 3}[kind], x0 + 3.2, H - 2.3, 0.6, 1.1,
                      yo + f * 0.006, f, c='cream' if kind != 'Paint' else 'oxide')
    pc = 'orange' if kind != 'Paint' else 'oxide'
    cc = 'rubber' if kind != 'Paint' else 'cream2'
    portal(k, x0, 1, W, H, 0.7, pc, cc)
    portal(k, x1, -1, W, H, 0.7, pc, cc)
    k.bx(x0 - 0.1, x1 + 0.1, -W - 0.26, W + 0.26, H + 0.05, H + 0.3, 'steelDark')      # roof
    k.col(x0, x1, -W - 0.22, W + 0.22, 0, H + 0.3)


def house(k, kind, H=8.6, W=2.85):
    """Feed / dispatch house at a run end (HO long): a closed hall section with its roll-up door raised over the lane
    mouth and a strip curtain; the mechs pop in / out of sight inside. kind 'Feed' (closed at -TL) or 'Dispatch'."""
    if kind == 'Feed':
        x0, x1, closed, mouth, sg = -TL, -TL + HO, -TL, -TL + HO, 1
    else:
        x0, x1, closed, mouth, sg = TL - HO, TL, TL, TL - HO, -1
    for f in (-1, 1):
        k.bx(x0, x1, *srt(f * W, f * (W + 0.2)), 0.0, H, 'cream')
        yo = f * (W + 0.203)
        k.qy(x0 + 0.4, x1 - 0.4, 0.05, 1.0, yo, f, 'oxide')
        k.qy(x0 + 0.4, x1 - 0.4, H - 2.4, H - 2.1, yo, f, 'tealS')
        k.stripes(x0 + 0.5, x1 - 0.5, 1.1, 1.5, yo, f, 8)
        if kind == 'Feed':
            stencil_digit(k, 0, x0 + 1.4, 3.0, 0.6, 1.1, yo, f, c='tealS')
            stencil_digit(k, 1, x0 + 2.2, 3.0, 0.6, 1.1, yo, f, c='tealS')
        else:
            pts = [(x1 - 3.2, yo + f * 0.003, 3.2), (x1 - 1.8, yo + f * 0.003, 3.2), (x1 - 1.8, yo + f * 0.003, 2.9),
                   (x1 - 1.0, yo + f * 0.003, 3.6), (x1 - 1.8, yo + f * 0.003, 4.3), (x1 - 1.8, yo + f * 0.003, 4.0),
                   (x1 - 3.2, yo + f * 0.003, 4.0)]
            k.poly(pts, 'tealS', (0, f, 0))
    ca, cb = srt(closed + sg * 0.006, closed + sg * 0.25)
    k.bx(ca, cb, -W, W, 0.0, H, 'cream')                                         # closed end wall
    xo = closed + sg * 0.003                                                     # on its outer face (out of the run)
    k.qx(-1.6, 1.6, 2.4, 5.2, xo, -sg, 'tealS')
    k.qx(-1.3, 1.3, 2.7, 4.9, xo - sg * 0.003, -sg, 'cream2')
    k.qx(-1.6, 1.6, 0.05, 0.9, xo, -sg, 'oxide')
    portal(k, mouth, -sg, W, H, 1.0, 'oxide', 'rubber')
    xd = mouth - sg * 0.7                                                        # roll-up door drum (raised)
    k.cyl(xd, -W + 0.05, H - 0.6, 0.3, 0.3, 2 * W - 0.1, 'tealS2', seg=10, rot=(-90, 0, 0))
    k.bx(x0 - 0.1, x1 + 0.1, -W - 0.3, W + 0.3, H + 0.05, H + 0.35, 'steelDark')          # roof
    k.cyl((x0 + x1) / 2, W - 0.4, H + 0.35, 0.16, 0.16, 0.18, 'steelDark', seg=8)           # beacon
    k.cyl((x0 + x1) / 2, W - 0.4, H + 0.53, 0.13, 0.09, 0.26, 'hot' if kind == 'Feed' else 'teal', seg=8)
    k.col(x0, x1, -W - 0.22, W + 0.22, 0, H + 0.35)


def jig_tile(k, kind):
    """Line tiles (14 x 8, the lane along X, downstream +X). Runs of four: Feed (feed house + drivetrain booth),
    Armour (armour booth), Paint (paint booth), Dispatch (dispatch house). The station booths sit at local x
    ST0..ST1, so the mechs change stage at x = 4.75 out of sight; the houses at the run ends hide the pop in / out."""
    k.begin()
    line_base(k)
    if kind != 'Feed':
        FD.line_fence_detail(k)
    H = 8.4
    if kind in ('Feed', 'Armour', 'Paint'):
        booth(k, {'Feed': 'Drive', 'Armour': 'Armour', 'Paint': 'Paint'}[kind], H=H)
    if kind == 'Feed':
        house(k, 'Feed')
        # drivetrain parts waiting beside the lane: a giant wheel each side on a skid plate
        for f in (-1, 1):
            k.bx(-1.75, -0.25, *srt(f * 1.95, f * 2.65), 0.0, 0.08, 'steelDark', ink=False)
            k.cyl(-1.0, 2.0 if f > 0 else -2.5, 0.8, 0.72, 0.72, 0.5, 'rubber', seg=12, rot=(-90, 0, 0))
            k.cyl(-1.0, 2.5 if f > 0 else -2.52, 0.8, 0.36, 0.36, 0.02, 'steel2', seg=10, rot=(-90, 0, 0), ink=False)
        robot_arm(k, 3.6, 2.2, 160, z=H + 0.3, reach=0.9, tool='weld')
        robot_arm(k, 6.0, -2.2, -20, z=H + 0.3, reach=0.9, tool='claw')
    elif kind == 'Armour':
        # plate stacks inside the fence beside the booth, a plate hoist gantry on the roof
        for f in (-1, 1):
            k.bx(ST0 + 0.4, ST1 - 0.4, *srt(f * 3.0, f * 3.3), 0.0, 0.5, 'steelDark')
            for i in range(4):
                y0, y1 = srt(f * (2.96 + 0.01 * i), f * (3.34 - 0.01 * i))
                k.bx(ST0 + 0.5 + 0.05 * i, ST1 - 0.5 - 0.05 * i, y0, y1, 0.5 + i * 0.17, 0.66 + i * 0.17, 'plate' if i % 2 else 'plate2')
        for x in (ST0 + 0.5, ST1 - 0.5):
            for f in (-1, 1):
                k.bx(x - 0.12, x + 0.12, f * 2.6 - 0.12, f * 2.6 + 0.12, H + 0.3, H + 2.2, 'orange')
        k.bx(ST0 + 0.3, ST1 - 0.3, -2.75, 2.75, H + 2.2, H + 2.5, 'orange2')
        k.bx(4.4, 5.1, -0.5, 0.5, H + 1.9, H + 2.2, 'hazard')
        for x in (-5.5, -1.5):                                                 # plate stacks in the open section too
            k.bx(x - 0.8, x + 0.8, *srt(-3.0, -3.3), 0.0, 0.3, 'steelDark')
            k.bx(x - 0.75, x + 0.75, *srt(-2.98, -3.32), 0.3, 0.5, 'plate')
    elif kind == 'Paint':
        for x in (3.4, 6.1):                                                   # extraction ducts on the roof
            k.cyl(x, 0.0, H + 0.3, 0.55, 0.55, 1.6, 'steel2', seg=10)
            k.cyl(x, 0.0, H + 1.9, 0.62, 0.62, 0.18, 'steelDark', seg=10)
        k.bx(3.3, 6.2, -0.3, 0.3, H + 1.2, H + 1.6, 'steel2')
        for f in (-1, 1):                                                      # paint drums inside the fence
            for x, c in ((-5.6, 'orange'), (-5.0, 'paintT'), (-4.4, 'cream')):
                k.cyl(x, f * 3.05, 0.0, 0.26, 0.26, 0.86, c, seg=10)
                k.cyl(x, f * 3.05, 0.86, 0.2, 0.2, 0.006, 'steelDark', seg=10, ink=False)
    elif kind == 'Dispatch':
        house(k, 'Dispatch')
        # inspection lamp gantries over the finished robots
        for x in (-5.5, -1.5):
            for f in (-1, 1):
                k.bx(x - 0.1, x + 0.1, *srt(f * 3.05, f * 3.25), 0.0, 7.8, 'steelDark')
                k.col(x - 0.1, x + 0.1, *srt(f * 3.05, f * 3.25), 0, 7.8)
            k.bx(x - 0.12, x + 0.12, -3.25, 3.25, 7.8, 8.05, 'orange')
            k.bx(x - 0.3, x + 0.3, -1.6, 1.6, 7.55, 7.8, 'steelDark', ink=False)
            k.qz(x - 0.25, x + 0.25, -1.5, 1.5, 7.547, -1, 'lamp')
    return k


def track_slat(k):
    """Chain-conveyor slat between the line rails (slides along the run)."""
    k.begin()
    k.bx(-0.11, 0.11, -0.94, 0.94, 0.0, 0.035, 'steel2', ink=False)
    k.bx(-0.04, 0.04, -0.9, 0.9, 0.035, 0.06, 'hazard', ink=False)
    return k


def mech_piece(k, which, stage):
    k.begin()
    if which == 'Walker':
        walker(k, stage)
    else:
        bruiser(k, stage)
    return k


# ================================================================ small belts ('=' cells)
def belt(k):
    """Heavy belt conveyor section (1 m along X): orange frame on stout legs, side rollers, the rubber belt."""
    k.begin()
    for s in (-1, 1):
        k.bx(-0.5, 0.5, *srt(s * 0.4, s * 0.48), 0.66, 0.9, 'orange')
        k.qy(-0.46, 0.46, 0.72, 0.84, s * 0.483, s, 'orange2')
    for s in (-1, 1):
        k.bx(-0.34, 0.34, *srt(s * 0.36, s * 0.44), 0, 0.66, 'steelDark', ink=False)
    k.bx(-0.04, 0.04, -0.4, 0.4, 0.18, 0.26, 'steelDark', ink=False)
    k.bx(-0.5, 0.5, -0.38, 0.38, 0.76, 0.84, 'rubber')
    k.col(-0.5, 0.5, -0.48, 0.48, 0, 0.98)
    return k


def belt_hood(k, kind, L=0.5, W=0.48, H=1.8, rail=0.9):
    """End hood over a moving belt (local +X = downstream): walls on the rails, roof, a closed motor end and a strip
    curtain over the open mouth. kind 'Feed' (closed upstream end) or 'Exit' (closed downstream end)."""
    k.begin()
    sx = -1 if kind == 'Feed' else 1
    z0 = rail + 0.004
    for s in (-1, 1):
        y0, y1 = srt(s * (W - 0.08), s * W)
        k.bx(-L, L, y0, y1, z0, H, 'tealS')
        k.stripes(-L + 0.04, L - 0.04, rail + 0.06, rail + 0.26, s * (W + 0.003), s, 4, ca='orange')
    k.bx(-L - 0.02, L + 0.02, -W - 0.03, W + 0.03, H, H + 0.08, 'steelDark')
    x0, x1 = srt(sx * (L - 0.066), sx * (L - 0.006))
    k.bx(x0, x1, -W + 0.08, W - 0.08, z0, H, 'tealS2')
    k.bx(*srt(sx * L, sx * (L + 0.14)), -0.22, 0.22, rail - 0.3, rail + 0.4, 'steelDark')
    k.cyl(sx * (L + 0.14), 0, rail + 0.05, 0.14, 0.14, 0.1, 'orange', seg=8, rot=(0, 90 * sx, 0))
    xm = -sx * (L - 0.04)
    for i in range(5):
        y = -W + 0.1 + (2 * W - 0.2) * (i + 0.5) / 5
        k.bx(xm - 0.008 - 0.004 * (i % 2), xm + 0.008 - 0.004 * (i % 2), y - 0.07, y + 0.07, rail + 0.16, H - 0.004, 'rubber', ink=False)
    k.qy(-0.18, 0.18, H - 0.32, H - 0.12, -W - 0.006, -1, 'cream')
    k.qy(-0.12, 0.12, H - 0.29, H - 0.15, -W - 0.009, -1, 'teal' if kind == 'Feed' else 'red')
    k.col(-L, L, -W, W, 0, H + 0.08)
    return k


def belt_cleat(k):
    k.begin()
    k.bx(-0.03, 0.03, -0.36, 0.36, 0.0, 0.025, 'steel2', ink=False)
    return k


def part(k, kind):
    """Parts riding the small belts (origin = belt top): armour plate, wheel hub, hydraulic ram, sensor lamp pod."""
    k.begin()
    if kind == 'Plate':
        k.hullp([(-0.36, -0.3, 0.0), (0.36, -0.3, 0.0), (0.36, 0.3, 0.0), (-0.36, 0.3, 0.0),
                 (-0.3, -0.25, 0.1), (0.3, -0.25, 0.1), (0.3, 0.25, 0.1), (-0.3, 0.25, 0.1)], 'primer')
        k.qz(-0.2, 0.2, -0.04, 0.04, 0.103, 1, 'primer2')
    elif kind == 'Hub':
        k.cyl(0, 0, 0.0, 0.3, 0.3, 0.16, 'steel2', seg=10)
        k.cyl(0, 0, 0.16, 0.16, 0.12, 0.08, 'steelDark', seg=8)
        for i in range(5):
            a = i / 5 * 2 * math.pi
            k.cyl(math.cos(a) * 0.22, math.sin(a) * 0.22, 0.16, 0.03, 0.03, 0.03, 'chrome', seg=5, ink=False)
    elif kind == 'Piston':
        k.cyl(-0.05, 0.0, 0.15, 0.12, 0.12, 0.38, 'steelDark', seg=8, rot=(0, 90, 0))      # barrel (+X)
        k.cyl(-0.05, 0.0, 0.15, 0.06, 0.06, 0.34, 'chrome', seg=6, rot=(0, -90, 0))        # rod (-X)
        k.bx(-0.16, 0.16, -0.14, 0.14, 0.0, 0.03, 'crate2', ink=False)
    else:   # sensor lamp pod
        k.bx(-0.22, 0.22, -0.2, 0.2, 0.0, 0.26, 'orange')
        k.cyl(0, -0.2, 0.13, 0.11, 0.11, 0.05, 'lamp', seg=8, rot=(90, 0, 0))
    return k


# ================================================================ props
def crate(k, kind):
    k.begin()
    if kind == 'Lid':
        k.bx(-0.34, 0.34, -0.28, 0.28, 0, 0.5, 'crate')
        k.qz(-0.32, 0.32, -0.02, 0.02, 0.503, 1, 'crate2')
        k.qy(-0.22, 0.22, 0.15, 0.3, -0.283, -1, 'oxide')
        return k
    hx, hy, h = 0.46, 0.42, 0.9
    k.bx(-hx, hx, -hy, hy, 0, h, 'crate')
    for f in (-1, 1):
        y = f * (hy + 0.003)
        k.qy(-hx + 0.02, hx - 0.02, h * 0.5 - 0.02, h * 0.5 + 0.02, y, f, 'crate2')
        k.qy(-hx + 0.02, -hx + 0.08, 0.02, h - 0.02, y + f * 0.003, f, 'crate2')
        k.qy(hx - 0.08, hx - 0.02, 0.02, h - 0.02, y + f * 0.003, f, 'crate2')
        k.qx(-hy + 0.02, hy - 0.02, h * 0.5 - 0.02, h * 0.5 + 0.02, f * (hx + 0.003), f, 'crate2')
    if kind == 'Open':        # bolts and a hydraulic ram
        k.cyl(-0.3, 0.0, h + 0.104, 0.1, 0.1, 0.6, 'steelDark', seg=8, rot=(0, 90, 0))
        k.cyl(0.3, -0.25, h + 0.004, 0.12, 0.12, 0.1, 'steel2', seg=8)
    else:
        k.qz(-hx + 0.03, hx - 0.03, -0.02, 0.02, h + 0.003, 1, 'crate2')
        k.qy(-0.2, 0.2, h * 0.2, h * 0.42, -hy - 0.006, -1, 'oxide')
    return k


def drums(k, variant):
    k.begin()
    spots = [(-0.22, -0.15), (0.24, 0.16)] if variant == 0 else [(0.0, 0.0)]
    for i, (x, y) in enumerate(spots):
        c, c2 = ('oxide', 'oxide2') if (i + variant) % 2 == 0 else ('paintT', 'paintT2')
        k.cyl(x, y, 0, 0.27, 0.27, 0.88, c, seg=10)
        for z in (0.29, 0.58):
            k.cyl(x, y, z, 0.283, 0.283, 0.035, c2, seg=10, ink=False, caps=False)
        k.cyl(x, y, 0.88, 0.22, 0.22, 0.006, c2, seg=10, ink=False)
    if variant == 1:
        k.qy(-0.12, 0.12, 0.35, 0.55, -0.276, -1, 'hazard')
    return k


def tool_cart(k, kind):
    k.begin()
    if kind == 'Gas':           # oxy-acetylene cart
        k.bx(-0.4, 0.4, -0.3, 0.3, 0.1, 0.16, 'steelDark')
        for x, c in ((-0.18, 'red'), (0.18, 'paintT')):
            k.cyl(x, 0.0, 0.16, 0.14, 0.14, 1.2, c, seg=8)
            k.cyl(x, 0.0, 1.36, 0.1, 0.05, 0.12, 'steelDark', seg=8)
        k.bx(-0.36, 0.36, 0.24, 0.3, 0.16, 1.2, 'steelDark', ink=False)
        for x in (-0.3, 0.3):
            k.cyl(x - 0.05, -0.26, 0.1, 0.1, 0.1, 0.1, 'rubber', seg=8, rot=(0, 90, 0))
        k.beam((0.2, 0.25, 1.1), (0.3, -0.25, 0.4), 0.04, 'hose', ink=False)
        k.col(-0.42, 0.42, -0.32, 0.32, 0, 1.4)
    else:                       # weld screen
        for x in (-0.45, 0.45):
            k.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0, 1.95, 'steelDark')
            k.bx(x - 0.18, x + 0.18, -0.2, 0.2, 0, 0.04, 'steelDark', ink=False)
        k.bx(-0.48, 0.48, -0.03, 0.03, 1.95, 2.01, 'steelDark')
        for i in range(4):
            x0 = -0.42 + i * 0.21
            k.bx(x0, x0 + 0.2, -0.015 + (i % 2) * 0.03, 0.015 + (i % 2) * 0.03, 0.15, 1.9, 'curtain')
        k.col(-0.5, 0.5, -0.2, 0.2, 0, 1.95)
    return k


def hazard_floor(k, variant):
    k.begin()
    zz = Z['hazard']
    k.qz(-0.95, 0.95, -0.95, 0.95, zz, 1, 'orange')
    n = 6
    for i in range(n):
        if i % 2:
            continue
        a = -0.95 + i * 1.9 / n
        if variant == 0:
            k.poly([(-0.95, a, zz + 0.004), (-0.95, a + 1.9 / n, zz + 0.004), (0.95, a + 1.9 / n, zz + 0.004), (0.95, a, zz + 0.004)], 'ink', (0, 0, 1))
        else:
            k.poly([(a, -0.95, zz + 0.004), (a + 1.9 / n, -0.95, zz + 0.004), (a + 1.9 / n, 0.95, zz + 0.004), (a, 0.95, zz + 0.004)], 'ink', (0, 0, 1))
    k.qz(-0.75, 0.75, -0.75, 0.75, zz + 0.008, 1, 'conc2')
    return k


def stand(k):
    k.begin()
    hx, hy, h = 0.45, 0.4, 0.92
    k.bx(-hx, hx, -hy, hy, 0, h, 'crate')
    k.qz(-hx + 0.03, hx - 0.03, -0.02, 0.02, h + 0.003, 1, 'crate2')
    k.qy(-0.2, 0.2, h * 0.2, h * 0.42, -hy - 0.006, -1, 'oxide')
    return k


def plate_stack(k, kind):
    """2 x 2 armour plates: a flat stack on dunnage, or plates standing in an A-rack."""
    k.begin()
    if kind == 'Flat':
        for y in (-0.6, 0.6):
            k.bx(-0.9, 0.9, y - 0.08, y + 0.08, 0, 0.12, 'crate2')
        for i in range(6):
            d = 0.02 * (i % 3)
            k.bx(-0.85 + d, 0.85 - d, -0.82 + d, 0.82 - d, 0.12 + i * 0.16, 0.26 + i * 0.16, 'plate' if i % 2 else 'plate2')
        k.qz(-0.3, 0.3, -0.05, 0.05, 0.12 + 5 * 0.16 + 0.14 + 0.003, 1, 'primer2')
        k.col(-0.9, 0.9, -0.85, 0.85, 0, 1.1)
    else:
        k.bx(-0.9, 0.9, -0.12, 0.12, 0, 0.12, 'steelDark')
        k.bx(-0.08, 0.08, -0.08, 0.08, 0.12, 1.9, 'orange')
        for f in (-1, 1):
            k.beam((f * 0.85, f * 0.02, 0.12), (0.0, f * 0.02, 1.85), 0.1, 'orange')
            for i in range(3):
                y = f * (0.3 + i * 0.16)
                k.bxr(0.0, y, 1.0, 1.6, 0.1, 1.7, 'primer' if i % 2 else 'plate', rot=(f * 12, 0, 0))
        k.col(-0.9, 0.9, -0.85, 0.85, 0, 1.9)
    return k


def wheel_stack(k, kind):
    """2 x 2: giant wheels (stacked lying), a wheel standing in a cradle, or a coiled tread section on a pallet."""
    k.begin()
    if kind == 'Stack':
        for i in range(2):
            z = i * 0.5
            k.cyl(0, 0, z, 0.88, 0.88, 0.46, 'rubber', seg=14)
            k.cyl(0, 0, z + 0.46, 0.5, 0.5, 0.006, 'steel2', seg=12, ink=False)
        k.cyl(0, 0, 0.966, 0.2, 0.2, 0.06, 'steelDark', seg=8)
        k.col(-0.88, 0.88, -0.88, 0.88, 0, 1.0)
    elif kind == 'Cradle':
        k.bx(-0.9, 0.9, -0.5, 0.5, 0, 0.2, 'orange')
        for x in (-0.65, 0.65):
            k.bx(x - 0.12, x + 0.12, -0.45, 0.45, 0.2, 0.55, 'orange2')
        k.cyl(0, -0.28, 1.0, 0.95, 0.95, 0.56, 'rubber', seg=14, rot=(-90, 0, 0))
        k.cyl(0, -0.29, 1.0, 0.52, 0.52, 0.01, 'steel2', seg=12, rot=(90, 0, 0), ink=False)
        k.cyl(0, 0.29, 1.0, 0.52, 0.52, 0.01, 'steel2', seg=12, rot=(-90, 0, 0), ink=False)
        k.cyl(0, -0.31, 1.0, 0.18, 0.18, 0.02, 'steelDark', seg=8, rot=(90, 0, 0), ink=False)
        k.col(-0.95, 0.95, -0.5, 0.5, 0, 1.95)
    else:   # tread coil on a pallet
        k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.14, 'crate2')
        for x in (-0.6, 0.0, 0.6):
            k.qz(x - 0.2, x + 0.2, -0.9, 0.9, 0.143, 1, 'crate')
        for i in range(3):
            r = 0.8 - i * 0.18
            k.cyl(0, 0, 0.14 + 0.002 * i, r, r, 0.62 - 0.0 * i, 'tread', seg=12, caps=False)
        k.cyl(0, 0, 0.14, 0.42, 0.42, 0.6, 'steelDark', seg=10)
        k.col(-0.9, 0.9, -0.9, 0.9, 0, 0.8)
    return k


def leg_rack(k):
    """4 x 2: two walker legs (primer) standing on stands, waiting to be fitted, with a parts tag."""
    k.begin()
    k.bx(-1.9, 1.9, -0.8, 0.8, 0.0, 0.16, 'steelDark')
    k.stripes(-1.85, 1.85, 0.02, 0.14, -0.803, -1, 10)
    for sx in (-1, 1):
        x = sx * 0.95
        hip = Vector((x, 0.1, 3.4))
        knee = Vector((x, -0.4, 1.95))
        ank = Vector((x, -0.05, 0.6))
        k.beam(hip, knee, 0.5, 'primer')
        k.beam(knee + Vector((0, -0.1, -0.2)), ank + Vector((0, -0.2, 0.3)), 0.46, 'primer2')
        k.cyl(x - 0.15, knee.y, knee.z, 0.26, 0.26, 0.3, 'steelDark', seg=10, rot=(0, 90, 0))
        k.cyl(x - 0.12, hip.y, hip.z, 0.3, 0.3, 0.24, 'steelDark', seg=10, rot=(0, 90, 0))
        k.bx(x - 0.35, x + 0.35, -0.75, 0.5, 0.16, 0.44, 'steelDark')
        k.beam(hip + Vector((0, 0.4, -0.2)), knee + Vector((0, 0.4, 0.1)), 0.12, 'chrome', ink=False)
        # stand holding the hip
        k.bx(x - 0.08, x + 0.08, 0.52, 0.68, 0.16, 3.2, 'orange')
        k.bx(x - 0.2, x + 0.2, 0.15, 0.68, 3.2, 3.36, 'orange2')
    k.col(-1.9, 1.9, -0.8, 0.8, 0, 3.6)
    return k


def weld_cell(k, kind):
    """4 x 4 weld bay: green weld curtains on three sides (open to -Y), a jig table with a mech part being welded by a
    robot arm, sparks, a gas cart."""
    k.begin()
    k.qz(-1.95, 1.95, -1.95, 1.95, Z['cell'], 1, 'orange')
    k.qz(-1.7, 1.7, -1.7, 1.7, Z['cell'] + 0.004, 1, 'conc2')
    for (x, y) in ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9), (0, 1.9), (-1.9, 0), (1.9, 0)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0, 2.5, 'steelDark')
    for j, (x0, x1, y0, y1) in enumerate(((-1.9, 1.9, 1.87, 1.93), (-1.93, -1.87, -1.9, 1.9), (1.87, 1.93, -1.9, 1.9))):
        k.bx(x0, x1, y0, y1, 0.15 + 0.005 * j, 2.3 - 0.004 * j, 'curtain', ink=False)
        k.bx(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, 2.36 + 0.006 * j, 2.44 + 0.006 * j, 'orange')
    # jig table and the part
    k.bx(-1.0, 0.6, -0.5, 0.7, 0.0, 0.8, 'steelDark')
    k.bx(-1.05, 0.65, -0.55, 0.75, 0.8, 0.9, 'steel2')
    if kind == 'A':     # a walker shin being welded
        k.beam((-0.8, 0.1, 1.05), (0.4, 0.1, 1.15), 0.42, 'primer2')
        k.bx(0.25, 0.55, -0.15, 0.35, 0.9, 1.4, 'steelDark')
        spark_star(k, -0.2, -0.13, 1.2, 0.22)
        spark_star(k, -0.35, -0.135, 1.0, 0.12, c='spark2')
    else:               # a bruiser road wheel being fitted to a tread frame
        k.bx(-0.9, 0.5, -0.1, 0.3, 0.9, 1.1, 'steel2')
        for x in (-0.6, -0.05):
            k.cyl(x, -0.14, 1.26, 0.25, 0.25, 0.2, 'steelDark', seg=10, rot=(-90, 0, 0))
        spark_star(k, 0.3, -0.12, 1.15, 0.2)
    robot_arm(k, 1.1, 1.0, 40, reach=0.95, tool='weld')
    # gas bottles in the corner
    for x, c in ((-1.55, 'red'), (-1.25, 'paintT')):
        k.cyl(x, 1.5, 0, 0.13, 0.13, 1.3, c, seg=8)
    pool_disc(k, 0.0, -0.6, Z['cell'] + 0.012, 1.2, 23, sx=1.2, sy=0.8, c1='spark2', c2='lampWarm')
    k.col(-1.95, 1.95, 1.84, 1.96, 0, 2.5)
    k.col(-1.96, -1.84, -1.95, 1.95, 0, 2.5)
    k.col(1.84, 1.96, -1.95, 1.95, 0, 2.5)
    FD.weld_cell_detail(k, kind)
    k.col(-1.05, 0.65, -0.55, 0.75, 0, 1.4)
    k.col(0.6, 1.6, 0.5, 1.5, 0, 1.6)
    return k


def machine(k, kind):
    """4 x 2 plate machines: a press brake folding an armour plate, or a plasma cutting table."""
    k.begin()
    if kind == 'Brake':
        for x in (-1.75, 1.75):
            k.bx(x - 0.22, x + 0.22, -0.7, 0.7, 0, 3.0, 'tealS')
            k.stripes(x - 0.2, x + 0.2, 0.1, 0.8, -0.703, -1, 2)
        k.bx(-1.55, 1.55, -0.35, 0.35, 0.0, 0.95, 'steelDark')
        k.bx(-1.55, 1.55, -0.25, 0.25, 1.75, 2.8, 'tealS2')
        k.bx(-1.4, 1.4, -0.06, 0.06, 1.5, 1.75, 'steel')
        k.bx(-1.97, 1.97, -0.72, 0.72, 3.0, 3.25, 'oxide')
        k.bxr(0.0, -0.45, 1.05, 2.4, 0.06, 0.55, 'primer', rot=(-35, 0, 0))
        k.bx(1.4, 1.75, -1.0, -0.72, 1.0, 1.6, 'panel')
        k.qy(1.45, 1.7, 1.35, 1.52, -1.003, -1, 'screen')
        k.qy(1.47, 1.57, 1.1, 1.2, -1.003, -1, 'red')
        FD.brake_detail(k)
        k.col(-1.97, 1.97, -0.72, 0.72, 0, 3.25)
    else:
        k.bx(-1.9, 1.9, -0.9, 0.9, 0.0, 0.8, 'steelDark')
        for i in range(8):
            x = -1.7 + i * 0.48
            k.bx(x - 0.03, x + 0.03, -0.85, 0.85, 0.8, 0.9, 'steel2', ink=False)
        k.bx(-1.2, 0.9, -0.6, 0.55, 0.9, 0.95, 'primer')
        for f in (-1, 1):
            k.bx(-1.95, 1.95, *srt(f * 0.9, f * 1.0), 0.8, 1.0, 'orange')
        k.bx(0.3, 0.55, -1.0, 1.0, 1.0, 1.9, 'orange2')
        k.bx(0.22, 0.63, -0.15, 0.15, 1.2, 1.7, 'steelDark')
        k.cyl(0.42, 0.0, 0.98, 0.04, 0.02, 0.22, 'steelDark', seg=6, ink=False)
        k.qz(0.2, 0.65, -0.25, 0.25, 0.955, 1, 'hot')
        FD.plasma_detail(k)
        k.col(-1.95, 1.95, -1.0, 1.0, 0, 1.9)
    return k


def chassis_jig(k, kind):
    """6 x 4: a big chassis on a build jig with a scaffold tower and a welding arm: a bruiser hull frame, or a walker
    with its drivetrain going in."""
    k.begin()
    k.qz(-2.95, 2.95, -1.95, 1.95, Z['jig'], 1, 'orange')
    k.qz(-2.75, 2.75, -1.75, 1.75, Z['jig'] + 0.004, 1, 'conc2')
    if kind == 'Bruiser':
        for x in (-1.1, 1.1):
            k.bx(x - 0.4, x + 0.4, -0.8, 0.8, 0.0, 0.5, 'orange')
        bruiser(k, 0, skid_on=False, x=-0.4, z=0.5)
    else:
        k.bx(-1.9, 1.3, -1.3, 1.3, 0.0, 0.4, 'steelDark')
        walker(k, 1, skid_on=False, x=-0.3, z=0.4)
    # scaffold tower with a deck on the +X side
    for (x, y) in ((1.9, -1.6), (2.8, -1.6), (1.9, 1.6), (2.8, 1.6)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, 4.56, 'hazard')
    for z in (1.5, 3.0):
        k.bx(1.83, 2.87, -1.67, 1.67, z, z + 0.08, 'steel2')
    k.bx(1.83, 2.87, -1.67, 1.67, 4.5, 4.6, 'steel2')
    for f in (-1, 1):
        k.beam((1.9, f * 1.62, 0.2), (2.8, f * 1.62, 1.5), 0.04, 'hazard', ink=False)
        k.beam((1.9, f * 1.62, 1.6), (2.8, f * 1.62, 3.0), 0.04, 'hazard', ink=False)
    robot_arm(k, 2.35, 0.0, -90, z=4.6, reach=1.0, tool='weld', s=1.1)
    FD.jig_scaffold_detail(k)
    k.col(-2.4, 1.3, -1.35, 1.35, 0, 4.5)
    k.col(1.85, 2.85, -1.65, 1.65, 0, 4.6)
    return k


def test_track(k):
    """16 x 12 fenced test track: asphalt loop with lane lines and a chequered line, tyre barriers and a control hut
    on the infield (a finished bruiser laps it: Mech_Bruiser_Test, animated along the theme's path)."""
    k.begin()
    zt, zl = Z['test'], Z['testLine']
    k.qz(-7.6, 7.6, -5.6, 5.6, zt, 1, 'asphalt')
    # lane lines (inner and outer edge of the loop) as thin painted strips
    for (a, b) in ((7.25, 5.25), (4.55, 2.55)):
        k.qz(-a, a, b - 0.06, b, zl, 1, 'lane')
        k.qz(-a, a, -b, -b + 0.06, zl, 1, 'lane')
        k.qz(a - 0.06, a, -b + 0.06, b - 0.06, zl, 1, 'lane')
        k.qz(-a, -a + 0.06, -b + 0.06, b - 0.06, zl, 1, 'lane')
    for i in range(6):                                                    # chequered start line
        for j in range(2):
            if (i + j) % 2 == 0:
                k.qz(-0.3 + j * 0.3, 0.0 + j * 0.3, -5.25 + i * 0.45, -4.8 + i * 0.45, zl + 0.004, 1, 'lane')
    # infield: raised kerb island with a control hut and tyre stacks
    k.bx(-4.5, 4.5, -2.5, 2.5, 0.0, 0.25, 'conc2')
    k.stripes(-4.45, 4.45, 0.02, 0.23, -2.503, -1, 20, ca='red', cb='white')
    k.stripes(-4.45, 4.45, 0.02, 0.23, 2.503, 1, 20, ca='red', cb='white')
    k.bx(-1.4, 1.4, -1.0, 1.2, 0.25, 2.8, 'cream')
    k.bx(-1.55, 1.55, -1.15, 1.35, 2.8, 3.0, 'oxide')
    k.qy(-1.1, 1.1, 1.3, 2.4, -1.003, -1, 'glassB')
    k.qy(-1.0, -0.2, 1.4, 2.0, -1.006, -1, 'screen')
    k.cyl(1.0, 0.8, 3.0, 0.12, 0.12, 0.6, 'steelDark', seg=6)
    k.cyl(1.0, 0.8, 3.6, 0.13, 0.09, 0.24, 'hot', seg=8)
    for (x, y) in ((-3.4, -1.4), (-3.4, 1.4), (3.4, -1.4), (3.4, 1.4)):
        for i in range(3):
            k.cyl(x, y, 0.25 + i * 0.28, 0.4, 0.4, 0.28, 'rubber' if i % 2 == 0 else 'tread', seg=10)
    # perimeter fence with corner posts and a lamp mast
    for f in (-1, 1):
        k.bx(-7.8, 7.8, *srt(f * 5.75, f * 5.8), 0.15, 1.35, 'steelDark', ink=False)
        k.bx(-7.8, 7.8, *srt(f * 5.72, f * 5.82), 1.35, 1.45, 'orange')
        k.bx(*srt(f * 7.75, f * 7.8), -5.72, 5.72, 0.15, 1.35, 'steelDark', ink=False)
        k.bx(*srt(f * 7.72, f * 7.82), -5.72, 5.72, 1.35, 1.45, 'orange')
        k.bx(-7.8, 7.8, *srt(f * 5.705, f * 5.835), 0.0, 0.15, 'hazard', ink=False)
        k.bx(*srt(f * 7.705, f * 7.835), -5.705, 5.705, 0.0, 0.15, 'hazard', ink=False)
    for x in (-7.77, -3.9, 0.0, 3.9, 7.77):
        for f in (-1, 1):
            k.bx(x - 0.06, x + 0.06, f * 5.77 - 0.06, f * 5.77 + 0.06, 0.0, 1.55, 'steelDark')
    for y in (-2.9, 2.9):
        for f in (-1, 1):
            k.bx(f * 7.77 - 0.06, f * 7.77 + 0.06, y - 0.06, y + 0.06, 0.0, 1.55, 'steelDark')
    k.col(-7.85, 7.85, 5.68, 5.86, 0, 1.55)
    k.col(-7.85, 7.85, -5.86, -5.68, 0, 1.55)
    k.col(-7.86, -7.68, -5.7, 5.7, 0, 1.55)
    k.col(7.68, 7.86, -5.7, 5.7, 0, 1.55)
    return k


def titan_dock(k):
    """Landmark 10 x 8: the Titan, a 10 m finished walker mech standing in its build dock: plinth, two scaffold towers
    with decks and stairs, an overhead gantry with a hoist, work lamps and the dock's pool of light."""
    k.begin()
    k.qz(-4.95, 4.95, -3.95, 3.95, Z['dock'], 1, 'orange')
    k.qz(-4.6, 4.6, -3.6, 3.6, Z['dock'] + 0.004, 1, 'conc2')
    k.bx(-2.9, 2.9, -2.2, 2.2, 0.0, 0.5, 'steelDark')
    k.stripes(-2.85, 2.85, 0.05, 0.45, -2.203, -1, 14)
    walker(k, 3, skid_on=False, z=0.5, s=1.45)
    for sx in (-1, 1):
        x0 = sx * 3.9
        for (x, y) in ((x0 - 0.6, -1.6), (x0 + 0.6, -1.6), (x0 - 0.6, 1.6), (x0 + 0.6, 1.6)):
            k.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 10.45, 'hazard')
        for z in (3.0, 6.0, 9.0):
            k.bx(x0 - 0.68, x0 + 0.68, -1.68, 1.68, z, z + 0.1, 'steel2')
        for z0, z1 in ((0.1, 3.0), (3.1, 6.0), (6.1, 9.0)):
            k.beam((x0 - 0.62 * sx, -1.62, z0), (x0 + 0.62 * sx, -1.62, z1), 0.05, 'hazard', ink=False)
            k.beam((x0 - 0.62 * sx, 1.62, z1), (x0 + 0.62 * sx, 1.62, z0), 0.05, 'hazard', ink=False)
        k.bx(x0 - 0.6, x0 + 0.6, -1.65, -1.59, 9.55, 9.65, 'hazard', ink=False)
        k.bx(x0 - 0.7, x0 + 0.7, -1.7, 1.7, 10.4, 10.5, 'orange2')               # tower cap under the gantry
        k.cyl(x0, -1.65, 9.6, 0.25, 0.25, 0.3, 'steelDark', seg=8, rot=(90, 0, 0))
        k.cyl(x0, -1.95, 9.6, 0.2, 0.2, 0.01, 'lamp', seg=8, rot=(90, 0, 0), ink=False)
    k.bx(-4.6, 4.6, -0.3, 0.3, 10.5, 10.95, 'orange')                        # gantry girder
    k.bx(-2.3, -1.3, -0.5, 0.5, 10.1, 10.5, 'hazard')                        # hoist
    for dx in (-0.15, 0.15):
        k.bx(-1.8 + dx - 0.015, -1.8 + dx + 0.015, -0.015, 0.015, 9.6, 10.1, 'steelDark', ink=False)
    k.bx(-2.1, -1.5, -0.18, 0.18, 9.4, 9.6, 'hazard')
    k.bx(-2.6, 2.6, 3.1, 3.4, 0.0, 2.2, 'cream')                             # dock office wall at the back
    k.qy(-2.3, -0.4, 0.9, 1.9, 3.097, -1, 'glassB')
    stencil_digit(k, 0, 0.3, 0.7, 0.5, 1.1, 3.097, -1, c='oxide')
    stencil_digit(k, 1, 1.0, 0.7, 0.5, 1.1, 3.097, -1, c='oxide')
    pool_disc(k, 0.0, -3.0, Z['dock'] + 0.012, 1.6, 41, sx=1.8, sy=0.5)
    k.col(-2.9, 2.9, -2.2, 2.2, 0, 10.0)
    k.col(-2.6, 2.6, 3.1, 3.4, 0, 2.2)
    for sx in (-1, 1):
        k.col(sx * 3.9 - 0.7, sx * 3.9 + 0.7, -1.7, 1.7, 0, 10.5)
    return k


# ================================================================ backdrop
def backdrop_heavy(k):
    """The heavy works outside the clerestory: one long slice (+-110 m along X, facing -Y): blast furnaces with their
    stoves and downcomers, cooling stacks, a goliath gantry crane over a yard, long halls with lit windows."""
    k.begin()
    rnd = random.Random(17)
    x = -112.0
    i = 0
    while x < 112:
        w = rnd.uniform(18, 28)
        h = rnd.uniform(16, 24)
        d = rnd.uniform(16, 24)
        y0 = (i % 3) * 0.3
        k.bx(x, x + w - 1.0, y0, d, -2.0 - 0.01 * (i % 4), h, 'far' if i % 2 else 'far2')
        k.bx(x - 0.2, x + w - 0.8, y0 - 0.25, d + 0.2, h, h + 1.2, 'far2' if i % 2 else 'far', ink=False)
        for j in range(max(1, int(w / 6))):
            xx = x + 1.5 + j * 5.5
            if xx + 3 < x + w - 1:
                k.qy(xx, xx + 3.2, h * 0.5, h * 0.66, y0 - 0.03, -1, 'farLit')
        if i % 3 == 0:                                                     # blast furnace + stove
            fx = x + w * 0.5
            k.cyl(fx, d * 0.5, h + 1.2, 4.5, 3.2, 20.0, 'oxide2', seg=10)
            k.cyl(fx, d * 0.5, h + 21.2, 2.2, 2.2, 6.0, 'far2', seg=8)
            k.cyl(fx + 7, d * 0.5 + 2, h + 1.26, 2.6, 2.6, 22.0, 'far', seg=8)
            k.sph(fx + 7, d * 0.5 + 2, h + 23.2, 2.6, 'far', seg=(8, 4), scale=(1, 1, 0.6))
            k.beam((fx + 1.5, d * 0.5 - 1.0, h + 26.0), (fx + 6.0, d * 0.5, h + 20.0), 1.0, 'far2', ink=False)
            for m, (dx, dz, r) in enumerate(((0.5, 28.5, 3.0), (3.0, 31.5, 3.8), (6.5, 34.0, 4.6))):
                k.sph(fx + dx, d * 0.5, h + dz, r, 'smoke', seg=(7, 5), scale=(1, 0.8, 0.75))
        elif i % 3 == 1:                                                   # cooling stack
            sx = x + w * 0.6
            k.cyl(sx, d * 0.5, h + 1.2, 1.8, 1.3, 28.8, 'far2', seg=8)
            k.cyl(sx, d * 0.5, h + 27.0, 1.42, 1.42, 1.4, 'oxide', seg=8, ink=False, caps=False)
            for m, (dx, dz, r) in enumerate(((0.5, 32.5, 2.8), (2.8, 35.0, 3.6))):
                k.sph(sx + dx, d * 0.5, h + dz, r, 'smoke', seg=(7, 5), scale=(1, 0.8, 0.75))
        x += w
        i += 1
    # goliath crane over the yard
    for xx in (8, 40):
        for yy in (-6, -2):
            k.bx(xx - 0.8, xx + 0.8, yy - 0.8, yy + 0.8, -2, 34, 'orange2')
    k.bx(4, 44, -6.5, -1.5, 34, 37, 'orange')
    k.bx(20, 26, -7.0, -1.0, 30, 34, 'hazard')
    for (cx, r, hh) in ((-60, 9.0, 22.0), (-41, 7.0, 18.0)):                   # gas holders
        k.cyl(cx, 34, -2, r, r, hh, 'far', seg=12)
        k.cyl(cx, 34, hh - 2, r + 0.3, r + 0.3, 0.8, 'far2', seg=12, ink=False)
    return k


# ================================================================ build
def build_kit_factory2(ao):
    pal = Palette(FAM)
    k = Kit(pal, PFX, HULL_T)
    for kind in ('Win_A', 'Win_B', 'Win_Panel', 'Win_Sign', 'Win_Duct', 'Win_Hose', 'Plain', 'Panel'):
        wall_module(k, kind).finish('Wall_' + kind, ao=ao)
    for side in ('L', 'R', 'LR'):
        wall_module(k, 'End', endL=side in ('L', 'LR'), endR=side in ('R', 'LR')).finish('Wall_End' + side, ao=ao)
    column(k).finish('Wall_Col', ao=ao)
    corner(k).finish('Corner', ao=ao)
    for kind in ('Plain', 'Arrow', 'Num'):
        block_wall(k, kind).finish('Block_' + kind, ao=ao)
    ceil_bay(k).finish('CeilBay')
    ceil_bay(k, 'Plate').finish('CeilBay_Plate')
    ceil_bay(k, 'Leg').finish('CeilBay_Leg')
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    trail_wall(k).finish('TrailWall', ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    # build lines
    for kind in ('Feed', 'Armour', 'Paint', 'Dispatch'):
        jig_tile(k, kind).finish('Jig_' + kind, ao=ao)
    track_slat(k).finish('Track_Slat')
    for which in ('Walker', 'Bruiser'):
        for st, n in enumerate(('Frame', 'Drive', 'Armour', 'Paint')):
            mech_piece(k, which, st).finish('Mech_%s_%s' % (which, n), ao=ao)
    k.begin()
    bruiser(k, 3, skid_on=False, deg=-90)
    k.finish('Mech_Bruiser_Test', ao=ao)
    # small belts
    belt(k).finish('Belt', ao=ao)
    for kind in ('Feed', 'Exit'):
        belt_hood(k, kind).finish('Belt_' + kind, ao=ao)
    belt_cleat(k).finish('Belt_Cleat')
    for kind in ('Plate', 'Hub', 'Piston', 'Lamp'):
        part(k, kind).finish('Part_' + kind, ao=ao)
    # props
    for kind in ('Open', 'Closed', 'Lid'):
        crate(k, kind).finish('Crate_' + kind, ao=ao)
    for v in (0, 1):
        drums(k, v).finish('Drums_%s' % 'AB'[v], ao=ao)
        hazard_floor(k, v).finish('Hazard_%s' % 'AB'[v])
    tool_cart(k, 'Gas').finish('GasCart', ao=ao)
    tool_cart(k, 'Screen').finish('WeldScreen', ao=ao)
    for kind in ('Flat', 'Rack'):
        plate_stack(k, kind).finish('Plates_' + kind, ao=ao)
    for kind in ('Stack', 'Cradle', 'Coil'):
        wheel_stack(k, kind).finish('Wheels_' + kind, ao=ao)
    leg_rack(k).finish('LegRack', ao=ao)
    for kind in ('A', 'B'):
        weld_cell(k, kind).finish('WeldCell_' + kind, ao=ao)
    for kind in ('Brake', 'Plasma'):
        machine(k, kind).finish('Machine_' + kind, ao=ao)
    for kind in ('Bruiser', 'Walker'):
        chassis_jig(k, kind).finish('ChassisJig_' + kind, ao=ao)
    test_track(k).finish('TestTrack', ao=ao)
    titan_dock(k).finish('Landmark_Titan', ao=ao)
    backdrop_heavy(k).finish('Backdrop_Heavy')
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_factory2
