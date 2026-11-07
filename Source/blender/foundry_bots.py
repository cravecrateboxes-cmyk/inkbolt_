"""kit-foundry: the new robot chassis the foundry builds (none of them is an in-game enemy, none is a factory2 walker or
bruiser). Each is drawn by a function k, stage, ... at the current Kit transform, front -Y, standing on z = B.

  spider(k, stage)   six-legged assault walker: a low hexagonal hull, a twin-cannon turret, legs that arch over the
                     hull (stages: 0 bare frame, 1 drivetrain / actuators, 2 armour in olive primer, 3 crimson paint)
  hover(k, stage)    hover tank: a wide skirt with four ducted lift fans glowing underneath, a wedge hull and a
                     long-barrel turret (0 skirt frame + fans, 1 hull in primer, 2 finished: sand / gunmetal)
  hound(k, stage)    armoured quadruped hunter: a sensor wedge (one slit, no face), spine fins, digitigrade hind legs
                     (0 frame, 1 finished: bone / gunmetal / crimson fins)
  gunship(k, stage)  drone carrier: a lifting body with four ducted fan rings and a belly rack of micro drones
  centipede(k, n)    segmented crawler: a cutter head and segments on paired legs; the tail segments still frames
Mechs never have eyes or faces: sensor slits, lamps and core glows only.
"""
import math

from mathutils import Vector

from foundry_common import (slab, slab3, oslab, tube, drumx, drumy, stencil_digit, beacon, spark_spray, srt)


def skid(k, L=1.75, W=1.15):
    """Line carrier: a dark mag-lev pallet with hazard edges, guide shoes into the rails and glowing lift pads."""
    k.bx(-L, L, -W, W, 0.24, 0.44, 'gun2')
    for f in (-1, 1):
        k.stripes(-L + 0.05, L - 0.05, 0.27, 0.41, f * (W + 0.003), f, 10)
        for x in (-L + 0.45, L - 0.45):
            k.bx(x - 0.25, x + 0.25, *srt(f * 0.94, f * 1.12), 0.1, 0.24, 'steelDark', ink=False)
    for x in (-L + 0.6, 0.0, L - 0.6):
        k.qz(x - 0.3, x + 0.3, -0.6, 0.6, 0.237, -1, 'cyan')


# ================================================================ spider walker (6 legs, ~2.6 m tall, 4.4 m span)
SPIDER_LEGS = [(-35, 0.95), (-90, 1.05), (-145, 0.95), (35, 0.95), (90, 1.05), (145, 0.95)]   # (angle from +X, length scale)


def spider(k, stage, B=0.0, s=1.0, deg=0, x=0.0, y=0.0):
    k.push(x, y, deg, B, s=s)
    B = 0.0
    P = stage == 3
    arm = 'crimson' if P else 'olive'
    arm2 = 'gun' if P else 'olive2'
    frame = 'steel2'
    hz = B + 1.25                                   # hull belly
    # hull frame (every stage): a hexagonal ring of beams and a keel
    hexa = [(math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r * 1.2) for a, r in
            ((0, 0.95), (60, 0.85), (120, 0.85), (180, 0.95), (240, 0.85), (300, 0.85))]
    for i in range(6):
        a, b = hexa[i], hexa[(i + 1) % 6]
        k.beam((a[0], a[1], hz + 0.2), (b[0], b[1], hz + 0.2), 0.12 + 0.012 * (i % 2), frame, ink=stage == 0)
    k.bx(-0.16, 0.16, -1.0, 1.0, hz, hz + 0.3, 'steelDark')
    for ang, ls in SPIDER_LEGS:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        hip = Vector((ca * 0.85, sa * 1.0, hz + 0.25))
        knee = Vector((ca * 1.55 * ls, sa * 1.75 * ls, hz + 1.25))
        foot = Vector((ca * 2.15 * ls, sa * 2.35 * ls, B + 0.04))
        if stage <= 1:
            k.beam(tuple(hip), tuple(knee), 0.11, frame)
            k.beam(tuple(knee), tuple(foot), 0.09, frame)
        if stage >= 1:
            k.cyl(hip.x, hip.y, hip.z - 0.18, 0.2, 0.2, 0.36, 'steelDark', seg=6)                     # hip turret
            oslab(k, hip + Vector((0, 0, 0.12)), knee, 0.14, 0.12, 0.11, 0.1, arm)                    # femur shell
            k.sph(knee.x, knee.y, knee.z, 0.17, 'steelDark', seg=(6, 4))
            oslab(k, knee, foot + Vector((0, 0, 0.3)), 0.12, 0.1, 0.07, 0.07, arm2)                  # tibia
            k.cyl(foot.x, foot.y, B, 0.15, 0.1, 0.32, 'steelDark', seg=5)                             # foot spike
            k.beam(tuple(hip + Vector((0, 0, -0.1))), tuple((hip + knee) / 2 + Vector((0, 0, -0.2))), 0.05, 'chrome', ink=False)
    if stage == 0:
        # jig posts hold the bare frame
        for yy in (-0.6, 0.6):
            k.bx(-0.12, 0.12, yy - 0.12, yy + 0.12, B, hz, 'hazard')
        k.pop()
        return
    k.cyl(0, 0.2, hz + 0.3, 0.38, 0.38, 0.45, 'steelDark', seg=10)                                    # power core
    k.cyl(0, 0.2, hz + 0.75, 0.28, 0.2, 0.08, 'cyan', seg=10, ink=False)
    if stage == 1:
        k.bx(-0.45, 0.45, 0.55, 0.95, hz + 0.33, hz + 0.6, 'hose')
        k.pop()
        return
    body = 'crimson' if P else 'olive'
    body2 = 'gun' if P else 'olive2'
    # armoured hull: a low faceted hexagon, a raised spine, a rear module
    slab3(k, 0, 0, [(hz + 0.1, 0.92, 1.18, 0, 0), (hz + 0.55, 1.08, 1.38, 0, 0), (hz + 0.85, 0.82, 1.1, 0, 0.05)], body, ch=0.45)
    slab(k, 0, 0.75, hz + 0.81, hz + 1.1, 0.55, 0.45, 0.45, 0.35, body2, ch=0.12)
    # turret with twin cannons and a sensor bar (one slit, no face)
    slab(k, 0, -0.15, hz + 0.84, hz + 1.3, 0.55, 0.6, 0.45, 0.5, body2, ch=0.18)
    for sx in (-1, 1):
        drumy(k, sx * 0.24, -1.15, hz + 1.06, 0.1, 1.4, 'steelDark', seg=8)
        drumy(k, sx * 0.24, -1.88, hz + 1.06, 0.13, 0.12, 'gun2', seg=8)
    k.bx(-0.36, 0.36, -0.8, -0.69, hz + 1.12, hz + 1.24, 'ink', ink=False)
    k.qy(-0.32, 0.32, hz + 1.15, hz + 1.21, -0.806, -1, 'alarm' if P else 'steelDark')
    if P:
        k.qz(-0.12, 0.12, -0.55, 0.3, hz + 1.306, 1, 'bone')                                          # turret stripe
    k.pop()


# ================================================================ hover tank (~2.3 m tall, 3 x 4.6 m)
def hover(k, stage, B=0.0, s=1.0, deg=0, x=0.0, y=0.0, glow=True):
    k.push(x, y, deg, B, s=s)
    B = 0.0
    P = stage == 2
    frame = 'steel2'
    z0 = B + 0.35
    # skirt frame and the four ducted lift fans (every stage)
    for f in (-1, 1):
        k.beam((-1.35, f * 2.0, z0 + 0.2), (1.35, f * 2.0, z0 + 0.2), 0.12, frame, ink=stage == 0)
        k.beam((f * 1.35, -2.0, z0 + 0.2), (f * 1.35, 2.0, z0 + 0.2), 0.135, frame, ink=stage == 0)
    for (fx, fy) in ((-0.85, -1.25), (0.85, -1.25), (-0.85, 1.25), (0.85, 1.25)):
        k.cyl(fx, fy, z0, 0.62, 0.62, 0.36, 'gun2', seg=12)
        k.cyl(fx, fy, z0 + 0.366, 0.5, 0.5, 0.002, 'steelDark', seg=12, ink=False)
        for i in range(3):
            a = i / 3 * math.pi * 2 + 0.4
            k.poly([(fx, fy, z0 + 0.376), (fx + math.cos(a) * 0.48, fy + math.sin(a) * 0.48, z0 + 0.376),
                    (fx + math.cos(a + 0.5) * 0.48, fy + math.sin(a + 0.5) * 0.48, z0 + 0.376)], 'steel2', (0, 0, 1))
        if glow:
            k.cyl(fx, fy, z0 - 0.006, 0.5, 0.5, 0.003, 'cyan', seg=12, ink=False)
    if stage == 0:
        for yy in (-0.3, 0.3):
            k.bx(-0.7, 0.7, yy - 0.1, yy + 0.1, z0 + 0.2, z0 + 0.4, frame)
        k.pop()
        return
    body = 'sand' if P else 'olive'
    body2 = 'gun2' if P else 'olive2'
    # skirt shell, wedge hull, rear thrusters
    slab3(k, 0, 0, [(z0 + 0.36, 1.55, 2.25, 0, 0), (z0 + 0.66, 1.55, 2.25, 0, 0), (z0 + 0.82, 1.35, 2.05, 0, 0.05)], body2, ch=0.5)
    slab3(k, 0, 0.1, [(z0 + 0.8, 1.25, 1.85, 0, 0), (z0 + 1.25, 1.05, 1.35, 0, 0.25)], body, ch=0.35)
    for sx in (-1, 1):
        drumy(k, sx * 0.9, 2.2, z0 + 0.9, 0.3, 0.6, 'steelDark', seg=10)
        k.cyl(sx * 0.9, 2.506, z0 + 0.9, 0.22, 0.22, 0.002, 'ember', seg=10, rot=(-90, 0, 0), ink=False)
    if stage == 1:
        k.cyl(0, 0.35, z0 + 1.25, 0.55, 0.55, 0.06, 'steelDark', seg=12)                           # empty turret ring
        k.pop()
        return
    # turret with a long gun and a sensor bar
    slab(k, 0, 0.35, z0 + 1.24, z0 + 1.75, 0.75, 0.85, 0.58, 0.66, body, ch=0.25)
    drumy(k, 0, -1.55, z0 + 1.5, 0.11, 2.4, 'steelDark', seg=8)
    drumy(k, 0, -2.86, z0 + 1.5, 0.16, 0.3, 'gun2', seg=8)
    drumy(k, 0, -0.55, z0 + 1.5, 0.2, 0.5, 'gun2', seg=8)
    k.bx(-0.5, 0.5, -0.47, -0.36, z0 + 1.55, z0 + 1.66, 'ink', ink=False)
    k.qy(-0.46, 0.46, z0 + 1.58, z0 + 1.63, -0.476, -1, 'lampW')
    # camo patches and a number board
    k.qz(-0.9, -0.3, -0.8, -0.2, z0 + 1.256, 1, 'sand2')
    k.qz(0.2, 0.9, 0.5, 1.1, z0 + 1.256, 1, 'sand2')
    for f in (-1, 1):
        k.qx(-0.6, 0.6, z0 + 0.42, z0 + 0.6, f * 1.556, f, 'hazard')
    k.qy(-0.7, 0.7, z0 + 0.42, z0 + 0.6, -2.256, -1, 'hazard')
    k.qy(-0.25, 0.25, z0 + 0.45, z0 + 0.57, -2.262, -1, 'ink')
    k.pop()


# ================================================================ hound (quadruped hunter, ~1.9 m tall, 2.9 m long)
def hound(k, stage, B=0.0, s=1.0, deg=0, x=0.0, y=0.0):
    k.push(x, y, deg, B, s=s)
    B = 0.0
    P = stage == 1
    frame = 'steel2'
    sh = Vector((0, -0.75, B + 1.25))     # shoulders
    hp = Vector((0, 0.85, B + 1.2))       # hips
    for sx in (-1, 1):
        # front leg: shoulder -> elbow (back a little) -> paw
        s0 = sh + Vector((sx * 0.42, 0, 0))
        el = s0 + Vector((sx * 0.08, 0.15, -0.6))
        pw = Vector((sx * 0.52, -0.95, B + 0.05))
        # hind leg: hip -> knee (forward) -> hock (back) -> paw
        h0 = hp + Vector((sx * 0.42, 0, 0))
        kn = h0 + Vector((sx * 0.05, -0.35, -0.45))
        hk = Vector((sx * 0.5, 1.15, B + 0.42))
        hpw = Vector((sx * 0.5, 1.0, B + 0.05))
        for a, b, t in ((s0, el, 0.1), (el, pw, 0.08), (h0, kn, 0.11), (kn, hk, 0.09), (hk, hpw, 0.07)):
            if not P or t == 0.07:
                k.beam(tuple(a), tuple(b), t, frame, ink=not P)
        if P:
            oslab(k, s0 + Vector((0, 0, 0.12)), el, 0.13, 0.16, 0.1, 0.11, 'gun')
            oslab(k, el, pw + Vector((0, 0, 0.12)), 0.09, 0.1, 0.07, 0.08, 'bone')
            oslab(k, h0 + Vector((0, 0, 0.12)), kn, 0.14, 0.2, 0.11, 0.13, 'gun')
            oslab(k, kn, hk, 0.1, 0.11, 0.08, 0.09, 'bone')
            for p in (pw, hpw):
                slab(k, p.x, p.y - 0.08, B, B + 0.14, 0.13, 0.2, 0.1, 0.15, 'steelDark', ch=0.05)
            k.sph(el.x, el.y, el.z, 0.11, 'steelDark', seg=(8, 5))
            k.sph(kn.x, kn.y, kn.z, 0.12, 'steelDark', seg=(8, 5))
    k.beam(tuple(sh), tuple(hp), 0.16, frame, ink=not P)                                               # spine
    k.beam((-0.42, sh.y, sh.z), (0.42, sh.y, sh.z), 0.12, frame, ink=not P)
    k.beam((-0.42, hp.y, hp.z), (0.42, hp.y, hp.z), 0.12, frame, ink=not P)
    if not P:
        for yy in (-0.5, 0.6):
            k.bx(-0.1, 0.1, yy - 0.1, yy + 0.1, B, B + 1.1, 'hazard')
        k.beam((0, sh.y - 0.1, sh.z + 0.05), (0, sh.y - 0.6, sh.z + 0.35), 0.1, frame)                  # neck
        k.pop()
        return
    # body: deep chest tapering to the hips, spine fins, sensor head on a strong neck
    slab3(k, 0, 0, [(B + 0.92, 0.36, 0.55, 0, 0.55), (B + 1.2, 0.5, 0.95, 0, 0.05), (B + 1.5, 0.4, 0.85, 0, 0.0)], 'gun', ch=0.18)
    slab3(k, 0, -0.55, [(B + 0.85, 0.42, 0.45, 0, 0), (B + 1.55, 0.48, 0.5, 0, -0.05)], 'bone', ch=0.16)
    for i in range(4):
        yy = -0.5 + i * 0.38
        slab(k, 0, yy, B + 1.48, B + 1.75 - i * 0.04, 0.05, 0.14, 0.03, 0.06, 'crimson', dy=0.06)
    oslab(k, Vector((0, -0.85, B + 1.32)), Vector((0, -1.25, B + 1.62)), 0.2, 0.2, 0.16, 0.16, 'gun')
    slab3(k, 0, -1.45, [(B + 1.42, 0.22, 0.35, 0, 0), (B + 1.84, 0.2, 0.33, 0, 0)], 'bone', ch=0.06)
    slab(k, 0, -1.9, B + 1.39, B + 1.6, 0.16, 0.12, 0.12, 0.1, 'gun', ch=0.04)
    k.bx(-0.19, 0.19, -1.87, -1.79, B + 1.65, B + 1.76, 'ink', ink=False)
    k.qy(-0.16, 0.16, B + 1.68, B + 1.73, -1.876, -1, 'alarm')
    for sx in (-1, 1):
        k.beam((sx * 0.12, -1.35, B + 1.8), (sx * 0.16, -1.1, B + 2.15), 0.03, 'steelDark', ink=False)  # antennas
    k.beam((0, 0.95, B + 1.35), (0, 1.55, B + 1.7), 0.05, 'steelDark', ink=False)                        # tail antenna
    k.sph(0, 1.57, B + 1.71, 0.05, 'alarm', seg=(6, 4), ink=False)
    k.pop()


# ================================================================ gunship / drone carrier (~5 m long)
def gunship(k, stage, B=0.0, s=1.0, deg=0, x=0.0, y=0.0):
    """Hangs or sits with its keel at z = B. stage 0 airframe in primer, 1 finished (gunmetal / hazard nose)."""
    k.push(x, y, deg, B, s=s)
    B = 0.0
    P = stage == 1
    body = 'gunL' if P else 'olive'
    body2 = 'gun2' if P else 'olive2'
    slab3(k, 0, 0, [(B, 0.35, 1.8, 0, 0.1), (B + 0.5, 0.75, 2.4, 0, 0), (B + 0.95, 0.55, 1.9, 0, 0.2)], body, ch=0.3)
    slab3(k, 0, -2.2, [(B + 0.2, 0.32, 0.4, 0, 0), (B + 0.75, 0.42, 0.5, 0, 0), (B + 0.6, 0.15, 0.2, 0, -0.55)], 'hazard' if P else body2, ch=0.12)
    for sx in (-1, 1):
        k.beam((sx * 0.6, -0.9, B + 0.6), (sx * 1.7, -1.3, B + 0.75), 0.18, body2)
        k.beam((sx * 0.6, 1.0, B + 0.6), (sx * 1.7, 1.4, B + 0.75), 0.18, body2)
        for fy in (-1.3, 1.4):
            k.cyl(sx * 2.15, fy, B + 0.55, 0.62, 0.62, 0.38, body2, seg=14)
            k.cyl(sx * 2.15, fy, B + 0.936, 0.5, 0.5, 0.002, 'steelDark', seg=14, ink=False)
            k.cyl(sx * 2.15, fy, B + 0.544, 0.5, 0.5, 0.003, 'cyan' if P else 'steelDark', seg=14, ink=False)
            k.bx(sx * 2.15 - 0.03, sx * 2.15 + 0.03, fy - 0.5, fy + 0.5, B + 0.94, B + 0.97, 'steel2', ink=False)
    # belly rack: micro drones (round pucks with one lamp) on a dark rail
    k.bx(-0.3, 0.3, -1.2, 1.2, B - 0.22, B + 0.0, 'steelDark')
    for i in range(4):
        yy = -0.9 + i * 0.6
        k.cyl(0, yy, B - 0.48, 0.24, 0.2, 0.26, 'gun2' if P else 'olive2', seg=8)
        k.cyl(0, yy - 0.2, B - 0.4, 0.04, 0.04, 0.05, 'alarm', seg=6, rot=(90, 0, 0), ink=False)
    k.bx(-0.32, 0.32, -2.8, -2.66, B + 0.4, B + 0.5, 'ink', ink=False)
    k.qy(-0.28, 0.28, B + 0.42, B + 0.48, -2.806, -1, 'lampW' if P else 'steelDark')
    k.cyl(0, 2.3, B + 0.4, 0.28, 0.2, 0.4, 'steelDark', seg=8, rot=(-90, 0, 0))
    k.pop()


# ================================================================ centipede crawler (segmented, ~8 m)
def centipede(k, n=7, built=5, B=0.0, s=1.0, deg=0, x=0.0, y=0.0):
    """Head at -Y; segments run toward +Y; the first `built` segments armoured (ember / gunmetal), the rest bare."""
    k.push(x, y, deg, B, s=s)
    B = 0.0
    L = 1.15
    for i in range(n):
        yy = -2.9 + i * L * 0.98
        armoured = i < built
        z = B + 0.55
        # paired legs
        for sx in (-1, 1):
            hip = Vector((sx * 0.5, yy, z + 0.25))
            knee = Vector((sx * 1.05, yy - 0.1, z + 0.55))
            foot = Vector((sx * 1.3, yy + 0.05, B + 0.03))
            k.beam(tuple(hip), tuple(knee), 0.08, 'steel2' if not armoured else 'gun')
            k.beam(tuple(knee), tuple(foot), 0.07, 'steel2' if not armoured else 'steelDark')
        k.bx(-0.12, 0.12, yy - L * 0.45, yy + L * 0.45, z + 0.12, z + 0.32, 'steelDark')                      # keel link
        if armoured:
            col = 'ember' if i % 2 == 0 else 'gun'
            slab3(k, 0, yy, [(z, 0.52, 0.4, 0, 0), (z + 0.45, 0.62, 0.48, 0, 0), (z + 0.75, 0.42, 0.38, 0, 0.03)], col, ch=0.22)
            k.qz(-0.25, 0.25, yy - 0.08, yy + 0.08, z + 0.753, 1, 'steelDark')
        else:
            for sx in (-1, 1):
                k.beam((sx * 0.45, yy - 0.42, z + 0.3), (sx * 0.45, yy + 0.42, z + 0.3), 0.06, 'steel2')
            k.beam((-0.45, yy, z + 0.6), (0.45, yy, z + 0.6), 0.06, 'steel2')
    # head: a wedge with twin cutter blades and a sensor bar
    yh = -3.75
    slab3(k, 0, yh, [(B + 0.45, 0.55, 0.5, 0, 0.1), (B + 1.05, 0.5, 0.42, 0, 0.0), (B + 1.2, 0.3, 0.2, 0, 0.15)], 'gun', ch=0.18)
    for sx in (-1, 1):
        k.hullp([(sx * 0.18, yh - 0.35, B + 0.55), (sx * 0.5, yh - 0.35, B + 0.55), (sx * 0.5, yh - 0.35, B + 0.75),
                 (sx * 0.15, yh - 1.15, B + 0.35), (sx * 0.22, yh - 1.15, B + 0.42)], 'chrome')
    k.bx(-0.38, 0.38, yh - 0.48, yh - 0.42, B + 0.85, B + 0.95, 'ink', ink=False)
    k.qy(-0.34, 0.34, B + 0.87, B + 0.93, yh - 0.483, -1, 'alarm')
    k.pop()


def weld_glow(k, x, y, z, s=-1, seed=1):
    spark_spray(k, x, y, z, 0.22, s=s, seed=seed)


__all__ = ['skid', 'spider', 'hover', 'hound', 'gunship', 'centipede', 'weld_glow', 'beacon']
