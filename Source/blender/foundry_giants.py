"""kit-foundry: the giants. The WARDEN titan (~24 m, a bipedal war titan in bone and crimson) and the STRIDER (~15 m,
a quadruped siege mech with a back-mounted siege gun), built in parts so each piece keeps to the landmark budget and
shared parts are modelled once:

  Titan_LegsFrame + Titan_TorsoFrame                        stage A, bare frame on its jig (zone 1, Bay_Frame)
  Titan_Legs + Titan_TorsoHalf + Titan_ArmL + Titan_GunHung  stage B, legs and left side armoured, the reactor core
                                                            glowing in the open chest, the weapon arm lowered by the
                                                            bridge crane (zone 2, Bay_Armour with its gantry walkway)
  Titan_Legs + Titan_Torso + Titan_ArmL + Titan_ArmGun       stage C, finished on its launch sled (zone 3, Bay_Launch)
  Strider_Legs + Strider_HullHalf                           half built over its siege gun on cradles (Bay_Strider)
  Strider_Legs + Strider_Hull                               finished on its launch sled (Bay_StriderLaunch)
  LaunchDoor                                                the sealed launch doors in the launch hall's south wall

Every part is modelled in its bay's frame (origin = bay centre on the floor, front -Y = game south, toward the entry);
the theme places the parts together with the prefab's `with` list. No eyes, no faces: sensor slits, lamps, the core.
"""
import math

import fd_detail as FD
from mathutils import Matrix, Vector

from foundry_common import (Z, CEIL, DECK, slab, slab3, oslab, tube, drumx, drumy, stencil_digit, stencil_x, floor_digit,
                            chevrons_y, spark_spray, pool_disc, beacon, floodlamp, downlamp, cable, guard_rail, stairs, srt)

V = Vector


def push_rx(k, x, y, z, deg):
    k.stack.append(k.m.parent)
    k.m.parent = k.m.parent @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'X')


# ================================================================ titan geometry
ANK = (3.1, -0.2, 1.9)
KNEE = (3.3, -0.7, 8.2)
HIP = (3.0, 0.2, 13.3)
SH = 5.6          # shoulder drum x
STATIONS = [(15.6, 3.6, 2.4), (18.6, 5.0, 3.0), (21.4, 4.2, 2.6)]   # torso (z, half width, half depth)


def oct_pts(w, d, z, y0=0.3):
    return [(-w * 0.62, y0 - d, z), (w * 0.62, y0 - d, z), (w, y0 - d * 0.45, z), (w, y0 + d * 0.45, z),
            (w * 0.62, y0 + d, z), (-w * 0.62, y0 + d, z), (-w, y0 + d * 0.45, z), (-w, y0 - d * 0.45, z)]


def leg_pts(sx):
    return V((sx * ANK[0], ANK[1], ANK[2])), V((sx * KNEE[0], KNEE[1], KNEE[2])), V((sx * HIP[0], HIP[1], HIP[2]))


def titan_rams(k, sx):
    ank, kn, hp = leg_pts(sx)
    tube(k, V((sx * 3.0, 1.35, 12.2)), V((sx * 3.25, 0.75, 9.6)), 0.3, 'steelDark', seg=8)
    tube(k, V((sx * 3.25, 0.75, 9.6)), V((sx * 3.3, 0.45, 8.4)), 0.15, 'chrome', seg=6, ink=False)
    tube(k, V((sx * 3.15, -1.3, 7.4)), V((sx * 3.12, -1.15, 4.6)), 0.26, 'steelDark', seg=8)
    tube(k, V((sx * 3.12, -1.15, 4.6)), V((sx * 3.1, -1.0, 2.7)), 0.13, 'chrome', seg=6, ink=False)


def titan_legs_frame(k):
    """Stage A legs: girder legs on joint drums, rams, a bare pelvis box (the jig in the bay holds it up)."""
    k.begin()
    for sx in (-1, 1):
        ank, kn, hp = leg_pts(sx)
        fx = sx * ANK[0]
        k.bx(fx - 0.75, fx + 0.75, -2.5, 1.3, 0.0, 0.75, 'steelDark')                    # foot keel
        for tx in (-0.55, 0.55):
            k.beam((fx + tx, -2.45, 0.45), (fx + tx, 1.25, 0.45), 0.24, 'steel2')
        k.bx(fx - 0.5, fx + 0.5, -0.8, 0.4, 0.75, 1.15, 'gun2')
        drumx(k, fx, ANK[1], ANK[2], 0.85, 1.5, 'gun2', seg=12)
        for ox, oy in ((-0.45, -0.4), (0.45, -0.4), (-0.45, 0.4), (0.45, 0.4)):
            o = V((ox, oy, 0))
            k.beam(tuple(ank + o + V((0, 0, 0.6))), tuple(kn + o + V((0, 0, -0.8))), 0.22, 'steel')
            k.beam(tuple(kn + o * 1.2 + V((0, 0, 0.8))), tuple(hp + o * 1.2 + V((0, 0, -0.9))), 0.26, 'steel')
        for z0, z1 in ((3.0, 5.4), (5.4, 7.2)):                                          # bracing on the shin front
            k.beam((fx - 0.42, -0.62 - (z0 - 2.5) * 0.08, z0), (fx + 0.42, -0.62 - (z1 - 2.5) * 0.08, z1), 0.1, 'steel2', ink=False)
        drumx(k, sx * KNEE[0], KNEE[1], KNEE[2], 1.1, 1.9, 'gun2', seg=12)
        drumx(k, sx * HIP[0], HIP[1], HIP[2], 1.25, 2.1, 'gun2', seg=12)
        titan_rams(k, sx)
    k.bx(-2.0, 2.0, -1.6, 1.6, 12.4, 14.4, 'steelDark')                                  # pelvis box
    drumx(k, 0.0, HIP[1], HIP[2], 0.7, 4.6, 'gun', seg=10)
    for y in (-1.75, 1.75):
        k.beam((-4.1, y, 14.55), (4.1, y, 14.55), 0.3, 'steel2')
    k.col(-4.0, -2.2, -2.5, 1.3, 0, 1.2)
    k.col(2.2, 4.0, -2.5, 1.3, 0, 1.2)
    for sx in (-1, 1):
        k.col(sx * 3.2 - 0.7, sx * 3.2 + 0.7, -1.3, 0.4, 1.2, 8.0)
    return k


def titan_legs(k):
    """Stages B and C: armoured, painted legs (bone shells, crimson guards, gunmetal joints) and the pelvis."""
    k.begin()
    for sx in (-1, 1):
        ank, kn, hp = leg_pts(sx)
        fx = sx * ANK[0]
        # foot: heel, toe, three toe caps, ankle guard
        slab3(k, fx, 0.55, [(0.0, 1.25, 1.2, 0, 0), (1.15, 1.15, 1.0, 0, 0.1), (1.85, 0.8, 0.65, 0, 0.0)], 'gun2', ch=0.4)
        slab3(k, fx, -1.55, [(0.0, 1.3, 1.3, 0, 0), (0.85, 1.2, 1.05, 0, 0.25), (1.3, 0.9, 0.6, 0, 0.5)], 'gun', ch=0.35)
        for tx in (-0.78, 0.0, 0.78):
            slab(k, fx + tx, -2.75, 0.0, 0.7, 0.33, 0.32, 0.26, 0.22, 'steelDark', ch=0.1, dy=0.08)
        drumx(k, fx, ANK[1], ANK[2], 0.85, 1.5, 'gun2', seg=12)
        slab(k, fx, -0.9, 1.0, 2.9, 0.8, 0.3, 0.7, 0.22, 'crimson', ch=0.2, dy=-0.1)
        # shin: shell, crimson guard, outer number fin
        oslab(k, ank + V((0, -0.1, 0.6)), kn + V((0, 0.1, -0.9)), 0.95, 0.85, 1.25, 1.1, 'bone', ch=0.35)
        oslab(k, ank + V((0, -0.92, 1.25)), kn + V((0, -0.82, -0.7)), 0.72, 0.2, 0.98, 0.26, 'crimson', ch=0.22)
        x0, x1 = srt(sx * 4.22, sx * 4.47)
        k.bx(x0, x1, -1.0, 0.55, 3.3, 6.6, 'bone2')
        xo = sx * 4.47 + sx * 0.003
        if sx > 0:
            stencil_x(k, 1, -0.75, 3.9, 0.55, 1.9, xo, 1, c='crimson2')
            stencil_x(k, 8, -0.08, 3.9, 0.55, 1.9, xo, 1, c='crimson2')
        else:
            stencil_x(k, 8, -0.75, 3.9, 0.55, 1.9, xo, -1, c='crimson2')
            stencil_x(k, 1, -0.08, 3.9, 0.55, 1.9, xo, -1, c='crimson2')
        # knee: drum, bone cap, a work lamp
        drumx(k, sx * KNEE[0], KNEE[1], KNEE[2], 1.1, 1.9, 'gun2', seg=12)
        slab3(k, sx * KNEE[0], -1.55, [(7.1, 0.9, 0.5, 0, 0.15), (8.2, 1.1, 0.62, 0, -0.12), (9.4, 0.85, 0.45, 0, 0.1)], 'bone2', ch=0.3)
        drumx(k, sx * 4.36, -1.2, 8.9, 0.2, 0.14, 'steelDark', seg=8)                    # work lamp, outer side
        drumx(k, sx * 4.437, -1.2, 8.9, 0.15, 0.002, 'lampW', seg=8, ink=False)
        # thigh: shell, crimson outer plate
        oslab(k, kn + V((0, 0.05, 0.75)), hp + V((0, 0, -0.5)), 1.15, 1.15, 1.35, 1.3, 'bone', ch=0.4)
        oslab(k, kn + V((sx * 1.18, 0.05, 1.3)), hp + V((sx * 1.3, 0.0, -0.6)), 0.22, 0.9, 0.26, 1.05, 'crimson', ch=0.12)
        drumx(k, sx * HIP[0], HIP[1], HIP[2], 1.25, 2.1, 'gun2', seg=12)
        titan_rams(k, sx)
        # hip skirts: front and side plates
        slab(k, sx * 2.25, -2.3, 11.2, 13.7, 1.25, 0.18, 1.45, 0.2, 'crimson', ch=0.15, dy=-0.18)
        x0, x1 = srt(sx * 4.25, sx * 4.75)
        k.hullp([(x0, -1.4, 11.4), (x1, -1.4, 11.4), (x0, 1.7, 11.4), (x1, 1.7, 11.4),
                 (x0, -1.6, 14.0), (x1, -1.6, 14.0), (x0, 1.9, 14.0), (x1, 1.9, 14.0)], 'bone2')
    slab3(k, 0, 0.2, [(12.1, 2.3, 2.0, 0, 0), (13.2, 2.6, 2.3, 0, 0), (14.6, 2.4, 2.1, 0, 0)], 'gun2', ch=0.6)
    k.bx(-1.2, 1.2, -2.45, -2.1, 11.6, 14.1, 'crimson')
    for z in (12.3, 12.95, 13.6):                                                         # pelvis plate bands
        k.qy(-1.1, 1.1, z - 0.12, z + 0.12, -2.453, -1, 'bone')
    for sx in (-1, 1):
        fx = sx * ANK[0]
        k.col(fx - 1.3, fx + 1.3, -3.1, 1.8, 0, 1.9)
        k.col(fx - 0.95, fx + 0.95, -1.4, 0.7, 1.9, 8.6)
        k.col(sx * 3.15 - 1.2, sx * 3.15 + 1.2, -1.0, 1.2, 8.6, 13.0)
    k.col(-4.8, 4.8, -2.4, 2.3, 11.4, 14.6)
    return k


def cage(k, x_min=None, posts=True, c='steel2', t=0.3):
    """Torso cage: octagon rings at the stations, posts between them (x_min: only the part with x >= x_min)."""
    rings = [oct_pts(w, d, z) for (z, w, d) in STATIONS]
    for R in rings:
        for i in range(8):
            a, b = R[i], R[(i + 1) % 8]
            if x_min is not None and (a[0] < x_min or b[0] < x_min):
                continue
            k.beam(a, b, t * (1 + 0.07 * (i % 2)), c)
    if posts:
        for i in range(8):
            for j in range(2):
                a, b = rings[j][i], rings[j + 1][i]
                if x_min is not None and (a[0] < x_min or b[0] < x_min):
                    continue
                k.beam(a, b, t * 0.92, c)


def reactor(k, lit=True, grille=False):
    """The chest reactor: a housing drum, and when lit a glowing core sphere with two containment rings."""
    drumy(k, 0, -2.85, 18.2, 1.35, 0.7, 'gun2', seg=14)
    if not lit:
        k.cyl(0, -3.203, 18.2, 1.0, 1.0, 0.002, 'steelDark', seg=14, rot=(-90, 0, 0), ink=False)
        return
    k.sph(0, -3.25, 18.2, 1.0, 'cyan', seg=(14, 9))
    k.sph(0, -3.62, 18.25, 0.62, 'cyanL', seg=(10, 6), ink=False)
    for i in range(12):                                   # containment ring
        a, b = i / 12 * 2 * math.pi, (i + 1) / 12 * 2 * math.pi
        k.beam((math.cos(a) * 1.3, -3.25, 18.2 + math.sin(a) * 1.3), (math.cos(b) * 1.3, -3.25, 18.2 + math.sin(b) * 1.3), 0.14 + 0.012 * (i % 2), 'steelDark')
    for z in (19.7, 16.7):
        k.bx(-1.8, 1.8, -3.35, -2.6, z - 0.12, z + 0.12, 'steelDark')
    if grille:
        for z in (17.45, 17.95, 18.45, 18.95):
            k.bx(-1.15, 1.15, -4.42, -4.2, z - 0.08, z + 0.08, 'gun2')
        for x in (-1.25, 1.25):
            k.bx(x - 0.1, x + 0.1, -4.45, -3.2, 17.1, 19.3, 'gun2')


def titan_torso_frame(k):
    """Stage A torso: spine, the girder cage, shoulder beam and drums, the empty reactor housing, bare arm frames,
    cable looms and weld sparks."""
    k.begin()
    k.bx(-0.9, 0.9, -0.6, 1.2, 14.4, 21.7, 'steelDark')
    k.cyl(0, 0.3, 14.45, 1.4, 1.4, 1.0, 'gun2', seg=12)
    cage(k, c='steel')
    reactor(k, lit=False)
    k.bx(-5.0, 5.0, -0.45, 0.75, 20.45, 21.35, 'steel2')
    for sx in (-1, 1):
        drumx(k, sx * SH, 0.15, 20.2, 1.15, 1.5, 'gun2', seg=12)
        sh = V((sx * 6.45, 0.1, 19.6))
        el = V((sx * 6.7, -0.2, 15.2))
        wr = V((sx * 6.7, -0.5, 10.9))
        for oy in (-0.35, 0.35):
            k.beam(tuple(sh + V((0, oy, 0))), tuple(el + V((0, oy, 0.5))), 0.26, 'steel2')
            k.beam(tuple(el + V((0, oy, -0.5))), tuple(wr + V((0, oy, 0))), 0.24, 'steel2')
        drumx(k, el.x, el.y, el.z, 0.72, 1.1, 'gun2', seg=10)
        k.bx(wr.x - 0.45, wr.x + 0.45, wr.y - 0.5, wr.y + 0.5, wr.z - 0.7, wr.z, 'gun')
    k.bx(-0.7, 0.7, -0.3, 1.1, 21.7, 22.3, 'gun2')                                       # neck stub
    for a, b, sg, c in (((-3.2, -1.2, 21.3), (1.6, -1.5, 21.2), 1.6, 'cableR'), ((-1.5, 1.6, 21.3), (2.8, 1.8, 21.0), 2.2, 'hose'),
                        ((0.4, -0.9, 21.5), (0.6, -1.3, 15.8), 0.6, 'cable'), ((-2.4, 2.4, 18.4), (2.4, 2.6, 18.4), 1.4, 'cableR')):
        cable(k, a, b, sg, 0.13, c)
    for (x, z) in ((2.25, 15.6), (-3.1, 18.6), (3.2, 18.6), (-2.6, 21.4)):
        spark_spray(k, x, -2.55 if abs(z - 15.6) < 0.1 else -3.1, z, 0.3, seed=int(x * 10 + z))
    return k


def titan_torso_half(k):
    """Stage B torso: the left side plated, the right side still an open cage, the reactor core installed and glowing
    in the open chest, the left pauldron fitted, the right shoulder waiting for its weapon arm."""
    k.begin()
    k.bx(-0.9, 0.9, -0.6, 1.2, 14.4, 21.7, 'steelDark')
    slab3(k, 0, 0.3, [(14.2, 2.6, 1.9, 0, 0), (15.8, 2.9, 2.1, 0, 0)], 'gun2', ch=0.6)
    # left chest shell (x <= -0.3), front crimson plate
    pts = []
    for (z, w, d) in STATIONS:
        pts += [(-w, 0.3 - d * 0.45, z), (-w, 0.3 + d * 0.45, z), (-w * 0.62, 0.3 - d, z), (-w * 0.62, 0.3 + d, z),
                (-1.45, 0.3 - d, z), (-1.45, 0.3 + d, z)]
    k.hullp(pts, 'bone')
    k.hullp([(-3.9, -2.62, 16.0), (-1.55, -2.85, 16.0), (-4.6, -3.25, 18.8), (-1.55, -3.4, 18.8), (-4.0, -2.95, 21.0), (-1.55, -3.1, 21.0),
             (-3.9, -2.2, 16.0), (-1.55, -2.4, 16.0), (-4.6, -2.8, 18.8), (-1.55, -2.9, 18.8), (-4.0, -2.5, 21.0), (-1.55, -2.6, 21.0)], 'crimson')
    cage(k, x_min=-1.5, c='steel')
    reactor(k, lit=True)
    k.bx(-5.0, 5.0, -0.45, 0.75, 20.45, 21.35, 'steel2')
    drumx(k, -SH, 0.15, 20.2, 1.15, 1.5, 'gun2', seg=12)
    drumx(k, SH, 0.15, 20.2, 1.15, 1.5, 'gun2', seg=12)
    k.cyl(SH + 0.753, 0.15, 20.2, 0.8, 0.8, 0.002, 'cyanD', seg=12, rot=(0, 90, 0), ink=False)     # empty arm socket
    pauldron(k, -1)
    k.bx(-0.7, 0.7, -0.3, 1.1, 21.7, 22.3, 'gun2')
    for a, b, sg, c in (((0.6, -2.5, 19.8), (2.9, -2.4, 15.9), 0.5, 'cableR'), ((-0.5, -2.6, 16.8), (2.2, -1.2, 15.5), 0.4, 'hose'),
                        ((0.9, 1.6, 21.6), (4.0, 1.4, 21.2), 1.2, 'cable'), ((1.5, -2.6, 21.2), (4.4, -2.0, 18.8), 0.9, 'cableR')):
        cable(k, a, b, sg, 0.15, c)
    for (x, y, z) in ((3.6, -1.6, 15.6), (4.8, -0.3, 18.6), (2.6, -2.75, 21.4)):
        spark_spray(k, x, y - 0.35, z, 0.32, seed=int(x * 13 + z))
    return k


def pauldron(k, sx):
    slab3(k, sx * 6.4, 0.1, [(18.7, 1.5, 2.3, 0, 0), (20.6, 1.95, 2.6, sx * 0.1, 0), (22.5, 1.35, 2.0, -sx * 0.1, 0.1)], 'crimson', ch=0.7)
    slab3(k, sx * 6.5, 0.1, [(18.1, 1.55, 2.0, 0, 0), (18.75, 1.7, 2.25, 0, 0)], 'bone2', ch=0.5)
    x0, x1 = srt(sx * 8.1, sx * 8.42)
    k.bx(x0, x1, -1.25, 1.25, 19.3, 21.4, 'bone')
    xo = sx * 8.42 + sx * 0.003
    if sx > 0:
        stencil_x(k, 1, -0.9, 19.6, 0.65, 1.5, xo, 1, c='crimson2')
        stencil_x(k, 8, -0.1, 19.6, 0.65, 1.5, xo, 1, c='crimson2')
    else:
        stencil_x(k, 8, -0.9, 19.6, 0.65, 1.5, xo, -1, c='crimson2')
        stencil_x(k, 1, -0.1, 19.6, 0.65, 1.5, xo, -1, c='crimson2')
    beacon(k, sx * 6.3, -0.9, 22.35, c='alarm', r=0.2)


def titan_head(k, x=0.0, y=0.0, z=0.0):
    """Sensor head: a low wedge with a visor band (one glowing slit, no face), side lamp pods, antenna and crest."""
    k.push(x, y, 0, z)
    slab3(k, 0, 0.1, [(0.0, 1.6, 1.5, 0, 0.15), (1.1, 1.7, 1.55, 0, 0.05), (2.0, 1.2, 1.1, 0, 0.35)], 'bone', ch=0.45)
    k.bx(-1.42, 1.42, -1.55, -1.3, 0.62, 1.02, 'steelDark')
    k.qy(-1.3, 1.3, 0.74, 0.88, -1.553, -1, 'alarm')
    for sx in (-1, 1):
        x0, x1 = (1.55, 2.05) if sx > 0 else (-2.05, -1.55)
        k.bx(x0, x1, -0.7, 0.3, 0.55, 1.15, 'gun2')                                 # side sensor pods
        k.qx(-0.55, 0.15, 0.8, 0.9, sx * 2.053, sx, 'crimson')
    k.beam((0.95, 0.9, 1.75), (1.2, 1.5, 3.4), 0.08, 'steelDark')
    slab(k, 0, 0.5, 1.9, 2.5, 0.1, 0.9, 0.06, 0.55, 'crimson', dy=0.2)
    k.pop()


def titan_torso(k):
    """Stage C torso: full armour, the reactor behind its grille, pauldrons, exhaust stacks, the sensor head."""
    k.begin()
    slab3(k, 0, 0.3, [(14.2, 2.6, 1.9, 0, 0), (15.8, 2.9, 2.1, 0, 0)], 'gun2', ch=0.6)
    slab3(k, 0, 0.3, [(z, w, d, 0, 0) for (z, w, d) in STATIONS], 'bone', ch=1.4)
    for sx in (-1, 1):
        x0, x1 = srt(sx * 1.55, sx * 3.9)
        xa, xb = srt(sx * 1.55, sx * 4.6)
        xc, xd = srt(sx * 1.55, sx * 4.0)
        k.hullp([(x0, -2.62, 16.0), (x1, -2.4, 16.0), (xa, -3.4, 18.8), (xb, -3.1, 18.8), (xc, -3.1, 21.0), (xd, -2.9, 21.0),
                 (x0, -2.2, 16.0), (x1, -2.0, 16.0), (xa, -2.9, 18.8), (xb, -2.6, 18.8), (xc, -2.6, 21.0), (xd, -2.4, 21.0)], 'crimson')
        pauldron(k, sx)
        drumx(k, sx * SH, 0.15, 20.2, 1.15, 1.5, 'gun2', seg=12)
    reactor(k, lit=True, grille=True)
    slab(k, 0, 0.4, 21.3, 22.0, 1.6, 1.4, 1.3, 1.2, 'gun2', ch=0.4)
    titan_head(k, 0, -0.3, 21.95)
    slab3(k, 0, 2.9, [(16.0, 2.6, 0.6, 0, 0), (21.0, 3.2, 0.9, 0, 0.2)], 'gun2', ch=0.4)        # back pack
    for i, x in enumerate((-2.1, -0.7, 0.7, 2.1)):
        k.cyl(x, 3.55, 19.5, 0.36, 0.36, 4.8 + 0.4 * (i % 2), 'steelDark', seg=10)
        k.cyl(x, 3.55, 24.3 + 0.4 * (i % 2), 0.3, 0.3, 0.004, 'ember', seg=10, ink=False)
    return k


def titan_arm_l(k):
    """Left arm (stages B, C): armoured upper arm and forearm, a three-fingered crushing claw."""
    k.begin()
    sh = V((-6.45, 0.1, 19.4))
    el = V((-6.75, -0.2, 15.3))
    wr = V((-6.8, -0.7, 11.3))
    oslab(k, sh, el + V((0, 0, 0.3)), 1.0, 1.0, 0.9, 0.9, 'bone', ch=0.3)
    drumx(k, el.x, el.y, el.z, 0.8, 1.3, 'gun2', seg=10)
    slab3(k, el.x, el.y + 0.85, [(14.6, 0.6, 0.4, 0, 0), (15.6, 0.7, 0.5, 0, 0.1)], 'bone2', ch=0.2)
    oslab(k, el + V((0, 0, -0.4)), wr, 1.05, 1.0, 1.2, 1.12, 'crimson', ch=0.35)
    k.bx(wr.x - 1.3, wr.x - 1.15, -1.6, 0.2, 11.8, 14.4, 'bone')                        # forearm guard
    drumx(k, wr.x, wr.y, wr.z - 0.2, 0.7, 1.4, 'gun2', seg=10)
    slab(k, wr.x, wr.y, 9.9, 11.0, 0.85, 0.75, 0.9, 0.8, 'gun', ch=0.25)                 # palm
    for i, (fx, fy) in enumerate(((-0.5, -0.45), (0.5, -0.45), (0.0, 0.55))):
        a = V((wr.x + fx, wr.y + fy, 10.0))
        b = a + V((fx * 0.3, -0.55 if fy < 0 else 0.4, -1.0))
        c = b + V((0, -0.55 if fy < 0 else 0.45, -0.7))
        oslab(k, a, b, 0.24, 0.26, 0.21, 0.23, 'gun2', ch=0.06)
        oslab(k, b, c, 0.21, 0.23, 0.12, 0.14, 'steelDark', ch=0.04)
    return k


def cannon(k, P=True):
    """The weapon arm's forearm (from the elbow at the origin along -Y): housing, rotary barrel cluster, ammo drum."""
    slab3(k, 0, -2.3, [(-0.75, 0.95, 2.2, 0, 0), (0.75, 0.85, 2.1, 0, 0)], 'gun2', ch=0.35)
    k.bx(-0.7, 0.7, -4.1, -0.6, 0.72, 0.95, 'crimson')
    for f in (-1, 1):
        k.push(f * 0.952, -2.3, 90 * f)
        k.stripes(-1.5, 1.5, -0.45, 0.2, 0.0, -1, 8)
        k.pop()
    drumy(k, 0, -5.0, -0.05, 0.75, 1.8, 'steelDark', seg=12)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        drumy(k, math.cos(a) * 0.45, -6.5, math.sin(a) * 0.45 - 0.05, 0.16, 4.2, 'gun', seg=8)
    for yy in (-6.0, -8.1):
        drumy(k, 0, yy, -0.05, 0.86, 0.3, 'gun2', seg=12)
    drumy(k, 0, -8.55, -0.05, 0.18, 0.2, 'steelDark', seg=8)
    drumx(k, 0.0, 1.0, -0.4, 1.1, 1.5, 'olive', seg=12)
    k.cyl(0.753, 1.0, -0.4, 0.7, 0.7, 0.002, 'hazard', seg=12, rot=(0, 90, 0), ink=False)


def titan_arm_gun(k):
    """Right arm (stage C): armoured upper arm, the elbow bent, the rotary cannon forearm pointing forward."""
    k.begin()
    sh = V((6.45, 0.1, 19.4))
    el = V((6.75, -0.2, 15.3))
    oslab(k, sh, el + V((0, 0, 0.3)), 1.0, 1.0, 0.9, 0.9, 'bone', ch=0.3)
    drumx(k, el.x, el.y, el.z, 0.85, 1.52, 'gun2', seg=10)
    k.push(el.x, el.y, 0, el.z - 0.3)
    cannon(k)
    k.pop()
    return k


def titan_gun_hung(k):
    """Stage B: the weapon arm hanging barrels-down from a spreader on four slings, being lowered to the shoulder."""
    k.begin()
    x, y, z = 7.7, -1.2, 18.6
    push_rx(k, x, y, z, 90)
    cannon(k, P=False)
    k.pop()
    k.bx(x - 1.6, x + 1.6, y - 0.3, y + 0.3, z + 2.4, z + 2.75, 'hazard')
    for dx in (-1.4, 1.4):
        for dy in (-0.25, 0.25):
            k.beam((x + dx, y + dy, z + 2.4), (x + dx * 0.55, y + dy * 2.8, z + 0.6), 0.05, 'steelDark', ink=False)
    for dx in (-0.2, 0.2):
        k.bx(x + dx - 0.03, x + dx + 0.03, y - 0.03, y + 0.03, z + 2.75, CEIL - 3.6, 'steelDark', ink=False)
    return k


# ================================================================ bay pieces
def bay_floor(k, hx, hy, digits, z0=0.0, front=None):
    """Painted bay: hazard border, dark plate field, slanted black stripes in the front border, a bay number."""
    k.qz(-hx + 0.05, hx - 0.05, -hy + 0.05, hy - 0.05, z0 + Z['bay'], 1, 'hazard')
    k.qz(-hx + 0.4, hx - 0.4, -hy + 0.4, hy - 0.4, z0 + Z['bay2'], 1, 'pit')
    y0, y1 = -hy + 0.05, -hy + 0.4
    n = int((2 * hx - 0.4) / 0.8)
    for i in range(n):
        x = -hx + 0.25 + i * 0.8
        k.poly([(x, y0, z0 + Z['bay2']), (x + 0.35, y0, z0 + Z['bay2']), (x + 0.6, y1, z0 + Z['bay2']), (x + 0.25, y1, z0 + Z['bay2'])], 'ink', (0, 0, 1))
    fy = front if front is not None else -hy + 0.9
    for i, d in enumerate(digits):
        floor_digit(k, d, -1.0 + i * 1.2, -fy - 1.6, 0.9, 1.5, z0 + Z['sten'])


def tower(k, x, y, h, w=1.2, c='hazard', decks=(6.0, 12.0, 18.0), ladder=True, col=True, z0=0.0):
    """Scaffold tower: corner posts, braces, grating decks with toe boards, a ladder up the -Y face."""
    for (px, py) in ((x - w, y - w), (x + w, y - w), (x - w, y + w), (x + w, y + w)):
        k.bx(px - 0.09, px + 0.09, py - 0.09, py + 0.09, z0, z0 + h, c)
    zs = [z0] + [z0 + d for d in decks if d < h]
    for za, zb in zip(zs, zs[1:]):
        k.beam((x - w, y - w, za + 0.2), (x + w, y - w, zb - 0.2), 0.07, c, ink=False)
        k.beam((x - w, y + w, zb - 0.2), (x - w, y - w, za + 0.2), 0.07, c, ink=False)
        k.beam((x + w, y + w, za + 0.2), (x - w, y + w, zb - 0.2), 0.07, c, ink=False)
    for d in decks:
        if d >= h:
            continue
        zz = z0 + d
        k.bx(x - w - 0.12, x + w + 0.12, y - w - 0.12, y + w + 0.12, zz - 0.12, zz, 'steelDark')
        for f in (-1, 1):
            k.bx(x - w - 0.12, x + w + 0.12, *srt(f * (w + 0.12) + y, f * (w + 0.15) + y), zz, zz + 0.2, c, ink=False)
    k.bx(x - w - 0.1, x + w + 0.1, y - w - 0.1, y + w + 0.1, z0 + h, z0 + h + 0.2, 'steelDark')
    if ladder:
        ly = y - w - 0.25
        for lx in (x - 0.25, x + 0.25):
            k.bx(lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, z0, z0 + h, 'steel2', ink=False)
        for i in range(int(h / 0.6)):
            zz = z0 + 0.4 + i * 0.6
            k.bx(x - 0.22, x + 0.22, ly - 0.015, ly + 0.015, zz, zz + 0.04, 'steel2', ink=False)
    if col:
        k.col(x - w - 0.12, x + w + 0.12, y - w - 0.3, y + w + 0.12, z0, z0 + h)


def goliath(k, hx, hy, h, trolley_x, load=None):
    """Goliath gantry crane straddling the bay: tapered legs on rail sills at x = +-hx, a box girder across at h."""
    for sx in (-1, 1):
        x = sx * hx
        for sy in (-1, 1):
            y = sy * hy
            slab(k, x, y, 0.4, h - 1.0, 0.45, 0.55, 0.32, 0.38, 'hazard', ch=0.12, dy=-sy * 0.0)
        k.bx(x - 0.55, x + 0.55, -hy - 0.8, hy + 0.8, 0.0, 0.4, 'steelDark')            # sill on its rail
        for sy in (-1, 1):
            k.cyl(x, sy * (hy + 0.35), 0.0, 0.32, 0.32, 0.12, 'rubber', seg=8)
        k.bx(x - 0.5, x + 0.5, -hy - 0.4, hy + 0.4, h - 1.0, h - 0.2, 'hazard2')        # leg head beam
        for z in (h * 0.35, h * 0.7):
            k.bx(x - 0.18, x + 0.18, -hy + 0.4, hy - 0.4, z - 0.2, z + 0.2, 'hazard2')
        beacon(k, x, -hy, h - 0.2 + 1.6, c='alarm', r=0.2)
        k.col(x - 0.6, x + 0.6, -hy - 0.8, -hy + 0.8, 0, h)
        k.col(x - 0.6, x + 0.6, hy - 0.8, hy + 0.8, 0, h)
    k.bx(-hx - 0.6, hx + 0.6, -0.9, 0.9, h - 0.2, h + 1.4, 'hazard')                     # box girder
    for f in (-1, 1):
        k.stripes(-hx + 0.6, hx - 0.6, h + 0.1, h + 1.1, f * 0.903, f, 26)
    k.bx(trolley_x - 1.1, trolley_x + 1.1, -1.25, 1.25, h - 0.95, h - 0.2, 'hazard2')       # trolley + hoist
    drumx(k, trolley_x, 0.0, h - 1.35, 0.4, 1.5, 'steelDark', seg=10)
    if load is not None:
        lz = load
        for dx in (-0.15, 0.15):
            k.bx(trolley_x + dx - 0.025, trolley_x + dx + 0.025, -0.025, 0.025, lz + 0.55, h - 1.75, 'steelDark', ink=False)
        k.bx(trolley_x - 0.35, trolley_x + 0.35, -0.2, 0.2, lz + 0.2, lz + 0.55, 'hazard')
        k.stripes(trolley_x - 0.35, trolley_x + 0.35, lz + 0.22, lz + 0.53, -0.203, -1, 4)


def bay_frame(k):
    """Bay A [20, 14]: the jig cradle under the bare titan's pelvis, two scaffold towers with bridges into the
    torso cage, a goliath crane lifting a chest plate, the sensor head waiting on its pallet, cable drums, lamps."""
    k.begin()
    bay_floor(k, 10, 7, (0, 1))
    for (x, y) in ((-1.7, -1.3), (1.7, -1.3), (-1.7, 1.3), (1.7, 1.3)):
        k.bx(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.0, 12.1, 'hazard')
        k.col(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0, 12.1)
    for z in (4.0, 8.0):
        k.bx(-1.42, 1.42, 1.18, 1.42, z - 0.15, z + 0.15, 'hazard2')
        for x in (-1.7, 1.7):
            k.bx(x - 0.12, x + 0.12, -1.02, 1.02, z + 0.2, z + 0.5, 'hazard2')
    k.bx(-2.3, 2.3, -1.8, 1.8, 12.05, 12.35, 'hazard2')
    k.stripes(-2.25, 2.25, 12.07, 12.33, -1.803, -1, 10)
    for sx in (-1, 1):
        tower(k, sx * 8.6, 2.6, 22.0, c='steel2')
        x0, x1 = srt(sx * 7.3, sx * 4.6)
        k.bx(x0, x1, 1.45, 2.45, 17.86, 17.98, 'steelDark')                                 # bridge into the cage
        guard_rail(k, x0, x1, 1.45, 17.98, cols=False)
        guard_rail(k, x0, x1, 2.45, 17.98, cols=False)
        floodlamp(k, sx * 7.7, 1.25, 13.0, s=-1)
        floodlamp(k, sx * 7.7, 1.25, 7.0, s=-1)
    goliath(k, 9.55, 6.0, 26.5, -2.4, load=22.6)
    # the chest plate on the hook, slung from a spreader
    k.bx(-4.0, -0.8, -0.12, 0.12, 22.55, 22.8, 'steelDark')
    for dx in (-1.4, 1.4):
        k.beam((-2.4 + dx, 0.0, 22.6), (-2.4 + dx * 1.1, -3.6, 20.6), 0.04, 'steelDark', ink=False)
    k.hullp([(-4.6, -3.7, 17.4), (-0.2, -3.7, 17.4), (-5.0, -4.2, 19.0), (0.2, -4.2, 19.0), (-4.4, -3.9, 20.6), (-0.4, -3.9, 20.6),
             (-4.6, -3.3, 17.4), (-0.2, -3.3, 17.4), (-5.0, -3.8, 19.0), (0.2, -3.8, 19.0), (-4.4, -3.5, 20.6), (-0.4, -3.5, 20.6)], 'olive')
    # the sensor head waiting on its pallet, front right
    k.bx(4.4, 8.6, -6.3, -2.9, 0.0, 0.55, 'hazard2')
    k.stripes(4.45, 8.55, 0.05, 0.5, -6.303, -1, 10)
    titan_head(k, 6.5, -4.4, 0.55)
    k.col(4.4, 8.6, -6.3, -2.9, 0, 2.6)
    # cable drums and a tool cart, left front
    for (x, y) in ((-7.2, -4.6), (-5.0, -5.4)):
        drumx(k, x, y, 0.9, 0.9, 1.2, 'wood', seg=12)
        drumx(k, x, y, 0.9, 0.62, 1.212, 'cableR' if x < -6 else 'hose', seg=12, ink=False)
        k.col(x - 0.65, x + 0.65, y - 0.9, y + 0.9, 0, 1.8)
    pool_disc(k, 0.0, -1.0, Z['pool'], 4.8, 11, sx=1.4, sy=0.9)
    return k


def bay_armour(k):
    """Bay B [24, 18]: a gantry walkway at 6 m round the titan (two wings and a front bridge, rails, posts) reached by
    two straight stairs, scaffold towers at the back, a ceiling bridge crane lowering the weapon arm, umbilicals from
    the roof to the open chest, the chest plate and the head waiting on cradles in front."""
    k.begin()
    bay_floor(k, 12, 9, (0, 2))
    T = DECK
    for sx in (-1, 1):
        # back scaffold towers with a bridge onto the torso back
        tower(k, sx * 6.6, 5.4, 20.0, w=1.0, decks=(T, 12.0, 16.0), c='steel2')
        x0, x1 = srt(sx * 5.5, sx * 3.2)
        k.bx(x0, x1, 4.0, 4.9, 15.86, 15.98, 'steelDark')
        floodlamp(k, sx * 6.6, 4.2, 9.5, s=-1)
    # ceiling bridge crane: runways along Y at x +-11, a girder across at y -1.2, trolley over the hung weapon arm
    for sx in (-1, 1):
        k.bx(sx * 11.0 - 0.3, sx * 11.0 + 0.3, -8.9, 8.9, CEIL - 2.6, CEIL - 2.1, 'steelDark')
        for y in (-7.5, 0.0, 7.5):
            k.bx(sx * 11.0 - 0.06, sx * 11.0 + 0.06, y - 0.06, y + 0.06, CEIL - 2.1, CEIL, 'steel2', ink=False)
        k.bx(sx * 11.0 - 0.5, sx * 11.0 + 0.5, -2.2, -0.2, CEIL - 3.0, CEIL - 2.6, 'hazard2')
    k.bx(-11.4, 11.4, -1.75, -0.65, CEIL - 3.9, CEIL - 3.0, 'hazard')
    k.stripes(-11.0, 11.0, CEIL - 3.8, CEIL - 3.1, -1.753, -1, 30)
    k.bx(6.6, 8.8, -2.0, -0.4, CEIL - 4.4, CEIL - 3.9, 'hazard2')
    drumx(k, 7.7, -1.2, CEIL - 4.75, 0.38, 1.6, 'steelDark', seg=10)
    # umbilicals from a roof junction box down into the open chest
    k.bx(-3.0, 3.0, -4.6, -2.6, CEIL - 0.8, CEIL - 0.02, 'gun2')
    for (ax, bx_, c) in ((-2.2, -0.9, 'cableR'), (-0.8, 0.0, 'hose'), (0.7, 0.8, 'cable'), (2.1, 1.4, 'cableR')):
        cable(k, (ax, -3.6, CEIL - 0.8), (bx_, -2.9, 19.9), 2.5, 0.22, c, n=8, ink=True)
    # chest plate on a cradle (front left), the head on a pallet (front right)
    k.bx(-6.4, -2.6, -5.9, -4.1, 0.0, 0.6, 'hazard2')
    k.hullp([(-6.2, -5.6, 0.6), (-2.8, -5.6, 0.6), (-6.2, -4.2, 0.6), (-2.8, -4.2, 0.6),
             (-6.0, -5.1, 2.9), (-3.0, -5.1, 2.9), (-6.0, -4.6, 2.9), (-3.0, -4.6, 2.9)], 'crimson')
    k.col(-6.4, -2.6, -5.9, -4.1, 0, 2.9)
    k.bx(2.6, 6.4, -6.0, -3.6, 0.0, 0.5, 'hazard2')
    titan_head(k, 4.5, -4.8, 0.5)
    k.col(2.6, 6.4, -6.0, -3.6, 0, 2.5)
    pool_disc(k, 0.0, -2.0, Z['pool'], 4.4, 13, sx=1.3, sy=0.9)
    return k


def bay_armour_deck(k):
    """Bay B's gantry walkway (the part placed with Bay_Armour): decks at 6 m (walkable), fascia, rails, the two
    stairs and the posts under the decks."""
    k.begin()
    T = DECK
    t = 0.3
    # decks: wings (x +-8..10, y -9..7.5), front bridge (x -8..8, y -9..-6.5), landings (x +-10..12, y 3..7.5)
    decks = [(-10.0, -8.0, -9.0, 7.5), (8.0, 10.0, -9.0, 7.5), (-8.0, 8.0, -9.0, -6.5), (-12.0, -10.0, 3.0, 7.5), (10.0, 12.0, 3.0, 7.5)]
    for (x0, x1, y0, y1) in decks:
        k.bx(x0, x1, y0, y1, T - t, T, 'gun2')
        k.colw(x0, x1, y0, y1, T - t, T)
        for i in range(int((y1 - y0) / 0.5)):                         # grating slats painted on the deck
            yy = y0 + 0.25 + i * 0.5
            k.qz(x0 + 0.08, x1 - 0.08, yy - 0.04, yy + 0.04, T + 0.003, 1, 'steelDark')
    # fascia hazard bands (front faces of the bridge and the wing ends)
    k.qy(-10.0, 10.0, T - t + 0.04, T - 0.04, -9.003, -1, 'hazard')
    k.stripes(-10.0, 10.0, T - t + 0.04, T - 0.04, -9.006, -1, 40)
    # rails
    guard_rail(k, -10.0, 10.0, -8.95, T)                                                    # front bridge outer
    guard_rail(k, -8.0, 8.0, -6.55, T)                                                      # front bridge inner
    for sx in (-1, 1):
        guard_rail(k, -6.55, 7.45, sx * 8.05, T, axis='y')                                   # wing inner (facing the titan)
        guard_rail(k, -8.95, 3.0, sx * 9.95, T, axis='y')                                    # wing outer, beside the stair
        guard_rail(k, 3.0, 7.45, sx * 11.95, T, axis='y')                                    # landing outer
        a, b = srt(sx * 8.05, sx * 11.95)
        guard_rail(k, a, b, 7.45, T)                                                         # back edge
        # stair: x +-10..12, from y -9 (ground) up to y 3 (deck), 18 steps
        a, b = srt(sx * 10.05, sx * 11.95)
        stairs(k, a, b, -9.0, 3.0, 0.0, T, 18)
        # posts under the decks
        for (px, py) in ((sx * 8.2, -8.8), (sx * 9.8, -8.8), (sx * 8.2, -3.0), (sx * 9.8, -3.0), (sx * 8.2, 2.8), (sx * 9.8, 2.8),
                         (sx * 8.2, 7.3), (sx * 11.8, 7.3), (sx * 11.8, 3.2), (sx * 4.0, -8.8), (sx * 4.0, -6.7)):
            k.bx(px - 0.15, px + 0.15, py - 0.15, py + 0.15, 0.0, T - t, 'steel2')
            k.col(px - 0.15, px + 0.15, py - 0.15, py + 0.15, 0, T - t)
        for py in (-8.8, -3.0, 2.8):
            k.beam((sx * 8.2, py, 0.3), (sx * 9.8, py, T - t - 0.3), 0.08, 'steel2', ink=False)
    return k


def bay_launch(k):
    """Bay C [20, 16] (placed 0.9 m up: the parts stand on the sled top at local z 0): the launch sled on its rails,
    ankle clamps, umbilical towers with their arms swung back, uplights, beacons, the bay paint on the floor."""
    k.begin()
    D = -0.9
    bay_floor(k, 10, 8, (0, 3), z0=D)
    k.bx(-7.8, 7.8, -4.6, 3.8, D, 0.0, 'gun2')                                            # sled
    for f, y in ((-1, -4.6), (1, 3.8)):
        k.stripes(-7.7, 7.7, D + 0.1, -0.1, y + f * 0.003, f, 30)
    for f in (-1, 1):
        x = f * 7.8
        k.qx(-4.5, 3.7, D + 0.1, -0.1, x + f * 0.003, f, 'crimson')
    for x in (-2.6, 2.6):                                                                    # rail shoes
        k.bx(x - 0.7, x + 0.7, -5.4, -4.6, D, D + 0.5, 'steelDark')
    for sx in (-1, 1):                                                                       # ankle clamps
        fx = sx * 3.1
        for f in (-1, 1):
            k.bx(fx + f * 1.35 - 0.25, fx + f * 1.35 + 0.25, -1.2, 0.4, 0.005, 1.5, 'crimson')
        for (x, y) in ((sx * 7.2, -4.0), (sx * 7.2, 3.2)):
            beacon(k, x, y, 0.0, c='alarm', r=0.22)
    # uplights at the sled front corners shine at the titan
    for x in (-6.0, 6.0):
        k.bx(x - 0.6, x + 0.6, -4.4, -3.6, 0.0, 0.4, 'steelDark')
        k.qz(x - 0.5, x + 0.5, -4.3, -3.7, 0.403, 1, 'lamp')
    for sx in (-1, 1):
        tower(k, sx * 9.0, 0.5, 19.0, w=0.8, decks=(6.0, 12.0, 17.0), z0=D, ladder=False)
        # swung-back umbilical arm (pointing up and out) with its cable loom to the titan's back
        k.beam((sx * 9.0, 0.5, 17.6), (sx * 7.6, 3.4, 21.5), 0.4, 'steelDark')
        cable(k, (sx * 7.6, 3.4, 21.3), (sx * 2.6, 3.2, 20.0), 1.8, 0.18, 'cableR', n=6, ink=True)
        beacon(k, sx * 9.0, 0.5, 19.2 + D, c='alarm', r=0.25)
        floodlamp(k, sx * 8.2, -0.3, 10.0 + D, s=-1)
    k.col(-7.8, 7.8, -4.6, 3.8, D, 0.0)
    for x in (-2.6, 2.6):
        k.col(x - 0.7, x + 0.7, -5.4, -4.6, D, D + 0.5)
    return k


# ================================================================ strider (quadruped siege mech)
SS = 1.15


def strider_legs(k):
    k.begin()
    k.push(0, 0, 0, s=SS)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hip = V((sx * 2.7, sy * 3.3, 8.2))
            knee = V((sx * 5.2, sy * 4.9, 11.4))
            foot = V((sx * 6.7, sy * 6.2, 0.75))
            k.cyl(hip.x, hip.y, 7.3, 1.0, 1.0, 1.7, 'gun2', seg=12)
            oslab(k, hip + V((0, 0, 0.4)), knee, 0.78, 0.72, 0.62, 0.58, 'gun', ch=0.25)
            k.sph(knee.x, knee.y, knee.z, 0.78, 'steelDark', seg=(10, 6))
            slab3(k, knee.x, knee.y, [(11.6, 0.85, 0.85, 0, 0), (12.6, 0.6, 0.6, sx * 0.2, sy * 0.2)], 'bone', ch=0.3)
            oslab(k, knee + V((0, 0, -0.3)), foot + V((0, 0, 1.2)), 0.72, 0.68, 0.55, 0.52, 'crimson', ch=0.22)
            oslab(k, knee + V((sx * 0.55, sy * 0.4, -1.2)), foot + V((sx * 0.4, sy * 0.3, 2.4)), 0.12, 0.42, 0.1, 0.32, 'bone', ch=0.05)
            slab3(k, foot.x, foot.y, [(0.0, 1.25, 1.25, 0, 0), (0.6, 1.15, 1.15, 0, 0), (1.25, 0.65, 0.65, 0, 0)], 'gun2', ch=0.5)
            for a in (0, 120, 240):
                r = math.radians(a + (45 if sx * sy > 0 else -45))
                cx, cy = foot.x + math.cos(r) * 1.25, foot.y + math.sin(r) * 1.25
                slab(k, cx, cy, 0.0, 0.5, 0.28, 0.28, 0.16, 0.16, 'steelDark', ch=0.08)
            tube(k, hip + V((sx * 0.3, sy * 0.9, 0.8)), knee + V((-sx * 0.2, sy * 0.1, 0.6)), 0.24, 'steelDark', seg=8)
    k.pop()
    for sx in (-1, 1):
        for sy in (-1, 1):
            fx, fy = sx * 6.7 * SS, sy * 6.2 * SS
            k.col(fx - 1.5, fx + 1.5, fy - 1.5, fy + 1.5, 0, 2.2)
            k.col(fx - 0.8, fx + 0.8, fy - 0.8, fy + 0.8, 2.2, 8.0)
    return k


def strider_hull(k, full=True):
    k.begin()
    k.push(0, 0, 0, s=SS)
    k.bx(-1.3, 1.3, -4.7, 4.5, 7.1, 7.9, 'steelDark')                                       # keel
    if full:
        slab3(k, 0, 0, [(7.0, 2.4, 4.6, 0, 0.1), (8.8, 3.1, 5.2, 0, 0), (10.6, 2.6, 4.4, 0, 0.3)], 'crimson', ch=1.2)
        slab3(k, 0, -5.4, [(7.5, 1.6, 0.9, 0, 0), (9.4, 1.8, 1.0, 0, 0), (10.0, 1.2, 0.6, 0, 0.3)], 'bone', ch=0.4)
        for sx in (-1, 1):
            k.hullp([(sx * 2.95, -4.0, 7.4), (sx * 3.35, -4.0, 7.8), (sx * 2.95, 4.2, 7.4), (sx * 3.35, 4.2, 7.8),
                     (sx * 3.05, -4.2, 9.6), (sx * 3.45, -4.2, 9.4), (sx * 3.05, 4.4, 9.6), (sx * 3.45, 4.4, 9.4)], 'bone')
        # turret and siege gun
        slab3(k, 0, 0.6, [(10.5, 2.3, 2.6, 0, 0), (12.2, 1.9, 2.2, 0, 0.2)], 'gun', ch=0.8)
        drumy(k, 0, -5.4, 11.45, 0.58, 8.6, 'gun2', seg=12)
        drumy(k, 0, -2.0, 11.45, 0.82, 2.0, 'steelDark', seg=12)
        slab(k, 0, -10.0, 10.75, 12.15, 0.95, 0.4, 0.9, 0.35, 'steelDark', ch=0.25)
        for sx in (-1, 1):
            k.bx(sx * 2.0 - 0.45, sx * 2.0 + 0.45, -0.6, 1.4, 11.0, 12.0, 'bone2')               # mortar pods
            for dy in (-0.25, 0.35, 0.95):
                k.cyl(sx * 2.0, dy, 12.0, 0.18, 0.18, 0.005, 'steelDark', seg=8, ink=False)
        k.bx(-0.95, 0.95, -5.87, -5.8, 9.0, 9.35, 'ink', ink=False)
        k.qy(-0.85, 0.85, 9.08, 9.27, -5.873, -1, 'alarm')
        for i, x in enumerate((-1.2, 0.0, 1.2)):
            k.cyl(x, 4.6, 9.4, 0.3, 0.3, 2.6, 'steelDark', seg=8)
            k.cyl(x, 4.6, 12.0, 0.24, 0.24, 0.004, 'ember', seg=8, ink=False)
    else:
        # half built: belly plate and the left skirt on, the upper hull open (ribs), engine block and the core inside
        slab3(k, 0, 0, [(7.0, 2.4, 4.6, 0, 0.1), (7.96, 2.9, 5.0, 0, 0)], 'olive', ch=1.0)
        k.hullp([(-2.95, -4.0, 7.4), (-3.35, -4.0, 7.8), (-2.95, 4.2, 7.4), (-3.35, 4.2, 7.8),
                 (-3.05, -4.2, 9.6), (-3.45, -4.2, 9.4), (-3.05, 4.4, 9.6), (-3.45, 4.4, 9.4)], 'bone')
        for y in (-3.6, -1.2, 1.2, 3.6):
            k.beam((-2.8, y, 8.0), (-2.0, y, 10.4), 0.22, 'steel2')
            k.beam((2.8, y, 8.0), (2.0, y, 10.4), 0.22, 'steel2')
            k.beam((-2.0, y, 10.4), (2.0, y, 10.4), 0.245, 'steel2')
        for x in (-2.0, 2.0):
            k.beam((x, -4.4, 10.4), (x, 4.4, 10.4), 0.27, 'steel2')
        k.bx(-1.4, 1.4, 1.5, 4.0, 7.9, 9.4, 'gun2')
        k.sph(0, -1.0, 8.9, 0.85, 'cyan', seg=(12, 8))
        k.cyl(0, -1.0, 7.9, 1.05, 1.05, 0.25, 'steelDark', seg=12)
        k.cyl(0, 0.6, 10.4, 1.9, 1.9, 0.2, 'steelDark', seg=14)                                 # empty turret ring
        slab3(k, 0, -5.4, [(7.5, 1.6, 0.9, 0, 0), (9.4, 1.8, 1.0, 0, 0)], 'olive2', ch=0.4)
        for a, b, c in (((-1.5, -2.2, 10.3), (1.2, 0.5, 9.0), 'cableR'), ((1.4, -3.4, 10.3), (-0.6, -1.2, 9.6), 'hose')):
            cable(k, a, b, 0.6, 0.14, c)
        spark_spray(k, -2.6, -3.0, 8.4, 0.3, seed=21)
    k.pop()
    return k


def bay_strider(k):
    """Strider bay [18, 18] (zone 1): jig columns under the half-built hull, a scaffold tower, the siege gun on floor
    cradles beneath it, a ceiling crane lowering a hull plate, bay paint."""
    k.begin()
    bay_floor(k, 9, 9, (0, 4))
    for (x, y) in ((-2.4, -3.2), (2.4, -3.2), (-2.4, 3.4), (2.4, 3.4)):
        k.bx(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0.0, 7.1 * SS, 'hazard')
        k.col(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0, 7.1 * SS)
    for y in (-3.2, 3.4):
        k.bx(-2.1, 2.1, y - 0.2, y + 0.2, 7.1 * SS - 0.4, 7.1 * SS - 0.02, 'hazard2')
    # the siege gun on three cradles (eye-level detail)
    drumy(k, 0, -3.0, 1.3, 0.66, 9.9, 'gun2', seg=14)
    drumy(k, 0, 1.0, 1.3, 0.92, 2.3, 'steelDark', seg=14)
    slab(k, 0, -8.2, 0.55, 2.05, 1.0, 0.45, 0.95, 0.4, 'steelDark', ch=0.25)
    for y in (-6.5, -2.0, 1.0):
        k.bx(-1.1, 1.1, y - 0.35, y + 0.35, 0.0, 0.62, 'hazard2')
        k.stripes(-1.05, 1.05, 0.05, 0.57, y - 0.353, -1, 6)
    k.col(-1.1, 1.1, -8.7, 2.3, 0, 2.2)
    tower(k, 6.4, -2.0, 15.0, w=1.0, decks=(5.0, 10.0, 14.0), c='steel2')
    # ceiling crane with a hull plate
    for sx in (-1, 1):
        k.bx(sx * 8.4 - 0.3, sx * 8.4 + 0.3, -8.9, 8.9, CEIL - 2.6, CEIL - 2.1, 'steelDark')
        for y in (-7.5, 0.0, 7.5):
            k.bx(sx * 8.4 - 0.06, sx * 8.4 + 0.06, y - 0.06, y + 0.06, CEIL - 2.1, CEIL, 'steel2', ink=False)
    k.bx(-8.8, 8.8, 1.2, 2.3, CEIL - 3.5, CEIL - 2.6, 'hazard')
    k.stripes(-8.4, 8.4, CEIL - 3.4, CEIL - 2.7, 1.197, -1, 24)
    k.bx(-2.6, -0.4, 0.95, 2.55, CEIL - 4.0, CEIL - 3.5, 'hazard2')
    for dx in (-0.15, 0.15):
        k.bx(-1.5 + dx - 0.025, -1.5 + dx + 0.025, 1.725, 1.775, 16.8, CEIL - 4.0, 'steelDark', ink=False)
    k.hullp([(-4.0, 0.0, 15.2), (1.0, 0.0, 15.2), (-4.0, 3.5, 15.2), (1.0, 3.5, 15.2),
             (-3.6, 0.3, 16.4), (0.6, 0.3, 16.4), (-3.6, 3.2, 16.4), (0.6, 3.2, 16.4)], 'crimson')
    k.bx(-1.9, -1.1, 1.5, 2.0, 16.4, 16.8, 'hazard')
    floodlamp(k, 6.4, -3.25, 9.0, s=-1)
    pool_disc(k, 0.0, -1.0, Z['pool'], 4.0, 17, sx=1.2, sy=1.2)
    return k


def bay_strider_launch(k):
    """Strider launch bay [18, 18] (placed 0.9 m up like Bay_Launch): sled, rail shoes, beacon masts, uplights."""
    k.begin()
    D = -0.9
    bay_floor(k, 9, 9, (0, 5), z0=D)
    hx, hy = 8.6, 8.4
    k.bx(-hx, hx, -hy, hy, D, 0.0, 'gun2')
    for f, y in ((-1, -hy), (1, hy)):
        k.stripes(-hx + 0.1, hx - 0.1, D + 0.1, -0.1, y + f * 0.003, f, 34)
    for f in (-1, 1):
        k.qx(-hy + 0.1, hy - 0.1, D + 0.1, -0.1, f * hx + f * 0.003, f, 'crimson')
    for x in (-2.6, 2.6):
        k.bx(x - 0.7, x + 0.7, -hy - 0.6, -hy, D, D + 0.5, 'steelDark')
    for (x, y) in ((-8.25, -2.5), (8.25, -2.5), (-8.25, 2.5), (8.25, 2.5)):
        k.bx(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.0, 9.0, 'hazard')
        beacon(k, x, y, 9.0, c='alarm', r=0.24)
        k.col(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0, 9.0)
    for (x, y) in ((-4.0, -7.4), (4.0, -7.4)):
        k.bx(x - 0.6, x + 0.6, y - 0.4, y + 0.4, 0.0, 0.4, 'steelDark')
        k.qz(x - 0.5, x + 0.5, y - 0.3, y + 0.3, 0.403, 1, 'lamp')
    k.col(-hx, hx, -hy, hy, D, 0.0)
    for x in (-2.6, 2.6):
        k.col(x - 0.7, x + 0.7, -hy - 0.6, -hy, D, D + 0.5)
    return k


# ================================================================ launch door [18, 2]
def launch_door(k, num):
    """A sealed launch door standing in front of the south wall (its back at local y = +1): two leaves meeting on a
    toothed seam, locking bolts, chevrons, crimson stripes, a stencilled door number, beacons on the pillars."""
    k.begin()
    H = 22.0
    for sx in (-1, 1):
        x0, x1 = srt(sx * 7.5, sx * 9.0)
        k.bx(x0, x1, -1.0, 0.95, 0.0, H + 2.6, 'slate2')
        k.bx(x0 + 0.1, x1 - 0.1, -1.06, -1.0, 0.0, 3.0, 'hazard', ink=False)
        k.stripes(x0 + 0.1, x1 - 0.1, 0.1, 2.9, -1.063, -1, 3)
        beacon(k, sx * 8.25, -0.4, H + 2.6, c='alarm', r=0.3, h=0.45)
        for xr in (sx * 7.8, sx * 8.7):                                                         # hydraulic rams
            tube(k, V((xr, -1.25, 3.0)), V((xr, -1.25, 12.0)), 0.18, 'steelDark', seg=8)
            tube(k, V((xr, -1.25, 12.0)), V((xr, -1.25, 19.0)), 0.09, 'chrome', seg=6, ink=False)
            k.bx(xr - 0.25, xr + 0.25, -1.45, -1.07, 2.7, 3.0, 'gun2')
            k.bx(xr - 0.2, xr + 0.2, -1.4, -1.07, 19.0, 19.3, 'gun2')
            k.col(xr - 0.25, xr + 0.25, -1.45, -1.0, 0.0, 19.3)
        for z in (6.0, 12.0, 18.0):
            k.cyl(sx * 8.25, -1.0, z, 0.3, 0.3, 0.12, 'steelDark', seg=8, rot=(90, 0, 0))
            k.cyl(sx * 8.25, -1.12, z, 0.24, 0.24, 0.01, 'alarm', seg=8, rot=(90, 0, 0), ink=False)
    k.bx(-8.95, 8.95, -1.1, 0.93, H, H + 2.58, 'slate')                                         # header
    k.qy(-7.0, 7.0, H + 0.4, H + 2.2, -1.103, -1, 'crimson')
    stencil_digit(k, 0, -1.2, H + 0.6, 0.9, 1.4, -1.106, -1, c='bone')
    stencil_digit(k, num, 0.3, H + 0.6, 0.9, 1.4, -1.106, -1, c='bone')
    FD.door_header(k, H)
    for sx in (-1, 1):
        x0, x1 = srt(sx * 0.06, sx * 7.5)
        k.bx(x0, x1, -0.7, 0.2, 0.0, H, 'gun')                                                  # door leaf
        for z in (5.5, 11.0, 16.5):                                                             # leaf ribs
            k.bx(x0 + 0.1, x1 - 0.1, -0.85, -0.7, z - 0.25, z + 0.25, 'gun2')
        for (za, zb) in ((3.0, 5.1), (5.9, 10.6), (11.4, 16.1), (16.9, 21.6)):                  # recessed panels
            for (pa, pb) in ((0.5, 4.3), (5.9, 7.2)):
                qa, qb = srt(sx * pa, sx * pb)
                k.qy(qa, qb, za, zb, -0.703, -1, 'gun2')
                k.qy(qa + 0.15, qb - 0.15, za + 0.15, zb - 0.15, -0.706, -1, 'slate')
        xa, xb = srt(sx * 4.6, sx * 5.6)
        k.bx(xa, xb, -0.88, -0.72, 0.3, H - 0.3, 'crimson')                                    # vertical stripe
        chevrons_y(k, x0 + 0.1, x1 - 0.1, 0.25, 2.6, -0.703, -1, 4, ca='hazard', cb='ink')
        for z in range(4):                                                                       # locking bolts
            zz = 3.8 + z * 4.6
            drumx(k, sx * 0.85, -0.82, zz, 0.32, 1.3, 'steelDark', seg=8)
    for i in range(11):                                                                          # toothed seam
        z = 0.5 + i * 2.0
        k.hullp([(-0.06, -0.72, z), (0.06, -0.72, z), (0.45, -0.72, z + 0.5), (-0.06, -0.72, z + 1.0), (0.06, -0.72, z + 1.0),
                 (-0.06, -0.78, z), (0.06, -0.78, z), (0.45, -0.78, z + 0.5), (-0.06, -0.78, z + 1.0), (0.06, -0.78, z + 1.0)], 'hazard')
    k.qz(-8.95, 8.95, -1.9, -1.1, Z['door'], 1, 'hazard')
    k.col(-9.0, 9.0, -1.1, 0.95, 0, H + 2.6)
    return k
