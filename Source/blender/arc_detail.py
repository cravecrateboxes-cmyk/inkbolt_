"""kit-arctic modelled detail (tactical look plan Stage 11): the fixings, seals, hinges, trims and service runs of a real
polar station, added to the pieces the player sees most. The arctic builders use the PM / AM model (hull modes), so
`K` wraps it in the interface the kit_base detail helpers expect: every part is hull='none' (no outline shell), stands
>= 3 mm proud, starts 3 mm inside what it sits on, and horizontal runs stop 5 mm short of the piece's sides.
Faces that look toward Blender -Y use the helpers at the plane y = yf; for other faces `k.push(x, y, deg)` first."""
import math

from mathutils import Matrix

from kit_base import (PROUD, EMBED, bolt_row, rivet_strip, kick_plate, drip_edge, corner_guard, conduit_run,
                      junction_box, vent, sign_plate, window_frame_depth)

OW = 1.2      # half the door opening (arc_doors.OW)
DH = 2.7


class K:
    """a kit_base-style view over an AM model: parts are painted detail (no outline shell)"""

    def __init__(self, m):
        self.m = m
        self.stack = []

    def push(self, x, y, deg=0.0, z=0.0):
        self.stack.append(self.m.parent)
        self.m.parent = self.m.parent @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')

    def pop(self):
        self.m.parent = self.stack.pop()

    def bx(self, x0, x1, y0, y1, z0, z1, c, ink=False, bevel=False, cull='k'):
        if z0 < 1.0:
            cull += 'b'
        if z1 > 3.0:
            cull += 't'
        self.m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)

    def fx(self, x0, x1, y0, y1, z0, z1, c):
        """a free-standing part: every face kept"""
        cull = ('b' if z0 < 0.6 else '') + ('t' if z0 > 3.0 else '')
        self.m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)

    def cyl(self, x, y, z, r1, r2, h, c, seg=8, ink=False, bevel=False, rot=(0, 0, 0), caps=True):
        self.m.cy((x, y, z), r1, r2, h, c, seg=seg, rot=rot, caps=caps, hull='none')

    def wire(self, a, b, t, c):
        self.m.bm_(a, b, t, c, hull='none')


def cable_tray(k, x0, x1, z, yf, c, cable_c, d=0.1):
    """an open cable tray on the wall (shelf, a front rail, two cables); parts overlap, never share a plane"""
    k.bx(x0, x1, yf - d, yf + EMBED, z, z + 0.01, c)
    k.bx(x0 + 0.003, x1 - 0.003, yf - d - 0.004, yf - d + 0.006, z + 0.003, z + 0.06, c)
    for i, off in enumerate((0.03, 0.065)):
        k.bx(x0 + 0.015, x1 - 0.015, yf - off - 0.012, yf - off + 0.012, z + 0.008 + i * 0.004, z + 0.036 + i * 0.004, cable_c)


def vbolts(k, x, z0, z1, every, yf, c, s=0.02, depth=0.0):
    """a column of bolt heads along z at x (the plane y = yf)"""
    n = max(1, int((z1 - z0) / every)) if z1 > z0 else 0
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n if n else z0
        k.bx(x - s / 2, x + s / 2, yf - depth - PROUD - 0.006, yf + EMBED, z - s / 2, z + s / 2, c)


def vseam(k, x, z0, z1, yf, c, w=0.012, d=0.006):
    k.bx(x - w / 2, x + w / 2, yf - d, yf + EMBED, z0, z1, c)


def hseam(k, x0, x1, z, yf, c, t=0.012, d=0.006):
    k.bx(x0 + 0.005, x1 - 0.005, yf - d, yf + EMBED, z - t / 2, z + t / 2, c)


# ------------------------------------------------------------------ walls
def wall_face(m, kind, s=-1):
    """interior wall: a panel joint with its screws, a cap on the dado rail, a skirting cap, lab kick plates"""
    k = K(m)
    if s > 0:
        k.push(0, 0, 180)
    yf = -0.506
    if kind == 'S':
        vseam(k, 0.0, 0.16, 0.99, yf, 'panelG')
        vseam(k, 0.0, 1.1, 3.44, yf, 'panelG')
        for z in (0.55, 2.4):
            vbolts(k, 0.0, z, z, 1, yf, 'steelL', s=0.018, depth=0.006)
        drip_edge(k, -0.495, 0.495, 1.075, yf, 'steelD', d=0.014, t=0.03)
    elif kind == 'M':
        vseam(k, 0.0, 0.16, 1.07, yf, 'woodD')
        vseam(k, 0.0, 1.2, 3.44, yf, 'panelG')
        for z in (0.6, 2.8):
            vbolts(k, 0.0, z, z, 1, yf, 'steelL', s=0.018, depth=0.006)
        drip_edge(k, -0.495, 0.495, 1.175, yf, 'woodD', d=0.016, t=0.03)
    else:
        kick_plate(k, -0.495, 0.495, yf, 'steelD', h=0.12, bolts='steelL')
        vseam(k, 0.0, 0.14, 1.16, yf, 'panelG')
        vseam(k, 0.0, 1.28, 4.0, yf, 'panelG')
        for z in (0.7, 2.6):
            vbolts(k, 0.0, z, z, 1, yf, 'steelL', s=0.018, depth=0.006)
        drip_edge(k, -0.495, 0.495, 1.22, yf, 'steelD', d=0.014, t=0.02)
    if s > 0:
        k.pop()


def wall_run(m, kind, s=-1):
    """a service run on a corridor wall: conduit with a junction box (station), or an open cable tray and an exit sign"""
    k = K(m)
    if s > 0:
        k.push(0, 0, 180)
    yf = -0.506
    if kind == 'L':
        cable_tray(k, -0.495, 0.495, 2.7, yf, 'galv', 'black')
        junction_box(k, 0.28, 2.0, yf, 'steelD', 'steelL', w=0.2, h=0.26, d=0.08)
        conduit_run(k, -0.495, 0.495, 2.0, yf, 'steelD', 'steelL')
        sign_plate(k, -0.25, 3.3, yf, 0.3, 0.14, 'green', 'paper')
    else:
        conduit_run(k, -0.495, 0.495, 3.3, yf, 'steelD', 'steelL', every=0.5)
        junction_box(k, -0.3, 3.3, yf, 'steelD', 'steelL', w=0.18, h=0.22, d=0.08)
        sign_plate(k, 0.3, 2.45, yf, 0.28, 0.12, 'green', 'paper')
    if s > 0:
        k.pop()


def fac_face(m):
    """the station's insulated panel wall: a seam cover with screws, a panel joint, a kick plate"""
    k = K(m)
    yf = -0.506
    kick_plate(k, -0.495, 0.495, yf, 'steelD', h=0.3, bolts='steelL')
    vseam(k, 0.0, 0.3, 3.8, yf, 'steelL', w=0.05, d=0.012)
    for z in (0.5, 1.4, 2.7, 3.2, 3.65):
        k.bx(-0.011, 0.011, yf - 0.026, yf - 0.012 + EMBED, z - 0.011, z + 0.011, 'steelD')
    hseam(k, -0.495, 0.495, 2.2, yf, 'panelG', t=0.014, d=0.006)


def fac_window(m):
    """window sill and head flashing, and corner screws on the frame"""
    k = K(m)
    drip_edge(k, -0.47, 0.47, 0.985, -0.5, 'steelL', d=0.1, t=0.03)
    k.bx(-0.45, 0.45, -0.64, -0.58 + EMBED, 2.7, 2.74, 'steelL')
    for x in (-0.37, 0.37):
        for z in (1.07, 2.63):
            k.bx(x - 0.012, x + 0.012, -0.598, -0.58 + EMBED, z - 0.012, z + 0.012, 'steelD')


def fac_vent(m):
    k = K(m)
    k.bx(-0.4, 0.4, -0.68, -0.6 + EMBED, 3.3, 3.37, 'steelD')       # weather hood
    bolt_row(k, -0.33, 0.33, 3.26, -0.6, 5, 'steelD', s=0.022)
    k.bx(-0.36, 0.36, -0.64, -0.6 + EMBED, 2.5, 2.57, 'steelD')      # lower lip


def fac_light(m):
    k = K(m)
    k.cyl(0.08, -0.512, 3.4, 0.015, 0.015, 0.46, 'black', seg=6)      # cable entry to the eave
    for x in (-0.3, 0.3):
        k.bx(x - 0.03, x + 0.03, -0.728, -0.7 + EMBED, 1.6, 1.68, 'steelD')   # hose box hinges (door top)
        k.bx(x - 0.03, x + 0.03, -0.728, -0.7 + EMBED, 1.12, 1.2, 'steelD')
    k.bx(0.2, 0.26, -0.722, -0.7 + EMBED, 1.3, 1.5, 'black')         # latch handle


# ------------------------------------------------------------------ doors
def door_frame(m, d, cw=0.1, deg_sides=(0, 180)):
    """seals round the opening, heavy hinges and a strike on the jambs, bolts on the casings"""
    k = K(m)
    for sx in (-1, 1):
        xin = sx * OW
        a, b = sorted((xin + sx * 0.003, xin - sx * 0.012))
        k.fx(a, b, -0.03, 0.03, 0.01, DH - 0.01, 'black')
    k.fx(-OW + 0.012, OW - 0.012, -0.03, 0.03, DH - 0.012, DH + 0.003, 'black')
    for z in (0.45, 1.35, 2.25):                                      # hinges on the -x jamb
        k.fx(-OW - 0.003, -OW + 0.014, -0.34, -0.14, z - 0.1, z + 0.1, 'steelD')
        k.cyl(-OW + 0.026, -0.24, z - 0.12, 0.024, 0.024, 0.24, 'steelK', seg=8)
    k.fx(OW - 0.014, OW + 0.003, -0.3, -0.18, 1.0, 1.2, 'steelL')     # strike plate on the +x jamb
    k.fx(OW - 0.017, OW - 0.011, -0.27, -0.21, 1.06, 1.12, 'black')
    for deg in deg_sides:
        k.push(0, 0, deg)
        yf = -(d + 0.003)
        for sx in (-1, 1):
            vbolts(k, sx * (OW + cw / 2), 0.4, 2.4, 1.0, yf, 'steelD', s=0.022)
        bolt_row(k, -0.9, 0.9, DH + cw / 2, yf, 3, 'steelD', s=0.022)
        k.pop()


def vault_leaf(m, dmg):
    """the vault door leaf: heavy hinges with straps on the -x edge, an edge bolt column, a release plate"""
    k = K(m)
    yf = -0.75
    for z in (0.3, 1.0, 1.95):
        k.fx(-1.19, -0.85, yf - 0.012, yf + EMBED, z - 0.07, z + 0.07, 'steelD')
        k.cyl(-1.16, yf - 0.027, z - 0.1, 0.034, 0.034, 0.2, 'steelK', seg=8)
    vbolts(k, 1.16, 0.2, 2.5, 0.32, yf, 'steelD', s=0.026)
    sign_plate(k, 0.8, 1.9, yf, 0.26, 0.16, 'yel', 'black')
    if not dmg:
        k.bx(0.74, 0.86, yf - 0.03, yf - 0.008 + EMBED, 1.52, 1.68, 'redE')   # emergency release


def gate_frame(m, fy):
    k = K(m)
    if fy > 0:
        k.push(0, 0, 180)
    yf = -0.6
    rivet_strip(k, -2.45, 2.45, 3.5, yf, 'steelL', every=0.26, s=0.022)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.68, sx * 2.45))
        kick_plate(k, a, b, yf, 'steelD', h=0.18, bolts='steelL')
    if fy > 0:
        k.pop()


def hatch(m):
    """bolted leaf, hinge lugs on the rim"""
    k = K(m)
    for i in range(10):
        a = (i + 0.5) / 10 * 2 * math.pi
        x, y = 0.8 * math.cos(a), 0.8 * math.sin(a)
        if abs(x) < 0.4 and y > 0.4:
            continue
        k.cyl(x, y, 0.177, 0.026, 0.026, 0.02, 'steelL', seg=6)
    for sx in (-1, 1):
        k.fx(sx * 0.5 - 0.1, sx * 0.5 + 0.1, -1.18, -0.98, 0.1, 0.2, 'steelK')
    k.fx(-0.1, 0.1, 1.0, 1.04, 0.12, 0.2, 'steelK')                  # handle lug spacers


# ------------------------------------------------------------------ exterior props
def fuel_tank(m):
    k = K(m)
    for y in (-0.95, 0.95):                                           # tie-down straps with buckles
        k.cyl(0, y, 1.25, 1.014, 1.014, 0.12, 'steelD', seg=12, rot=(-90, 0, 0), caps=False)
        for sx in (-1, 1):
            k.bx(sx * 0.64 if sx > 0 else -0.78, sx * 0.78 if sx > 0 else -0.64, y - 0.01, y + 0.13, 0.5, 0.62, 'steelL', cull='')
    k.cyl(0, -2.5, 0.45, 0.05, 0.05, 0.32, 'steelD', seg=8, rot=(90, 0, 0))   # drain stub, ball valve, lever
    k.m.sp((0, -2.76, 0.45), 0.09, 'orangeD', seg=(8, 5), hull='none')
    k.fx(-0.2, 0.2, -2.8, -2.77, 0.54, 0.58, 'redE')
    k.cyl(0.35, -1.2, 2.17, 0.02, 0.02, 0.12, 'steelD', seg=6)         # gauge on a riser
    k.cyl(0.35, -1.14, 2.3, 0.085, 0.085, 0.03, 'steelD', seg=10, rot=(90, 0, 0))
    k.cyl(0.35, -1.15, 2.3, 0.07, 0.07, 0.045, 'paper', seg=10, rot=(90, 0, 0))
    k.fx(0.345, 0.355, -1.198, -1.192, 2.3, 2.36, 'redE')
    for z in (0.62, 1.12, 1.62, 2.08):                                # ladder on the rear end, stood off on brackets
        for x in (-0.2, 0.2):
            k.fx(x - 0.011, x + 0.011, 2.497, 2.56, z - 0.02, z + 0.02, 'steelD')
    for x in (-0.2, 0.2):
        k.fx(x - 0.015, x + 0.015, 2.555, 2.59, 0.45, 2.15, 'steelL')
    for i in range(7):
        z = 0.55 + i * 0.26
        k.fx(-0.19, 0.19, 2.565, 2.585, z - 0.012, z + 0.012, 'steelL')


def mast_a(m, top, w, lean):
    """lattice flanges at every section joint; guy wires with insulators to ground anchors (upright mast only)"""
    k = K(m)
    n = int(top / 1.2)
    for i in range(0, n - 1, 2):
        z1 = 0.3 + (i + 1) * (top - 0.3) / n
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.fx(sx * w - 0.065, sx * w + 0.065, sy * w - 0.065, sy * w + 0.065, z1 - 0.02, z1 + 0.02, 'steelD')
    if lean:
        return
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.fx(sx * w - 0.06, sx * w + 0.06, sy * w - 0.06, sy * w + 0.06, 4.05, 4.15, 'steelK')     # collar
            ax, ay = sx * 0.9, sy * 0.9
            k.wire((sx * w, sy * w, 4.1), (ax, ay, 0.32), 0.014, 'steelK')
            mx, my, mz = (sx * w + ax) / 2, (sy * w + ay) / 2, 2.2
            k.wire((mx - sx * 0.0, my, mz + 0.06), (mx, my, mz - 0.06), 0.04, 'panelW')                # insulator
            k.fx(ax - 0.12, ax + 0.12, ay - 0.12, ay + 0.12, -0.003, 0.012, 'galv')                     # anchor plate
            k.fx(ax - 0.025, ax + 0.025, ay - 0.025, ay + 0.025, 0.0, 0.34, 'steelD')                   # stake and eye
            k.fx(ax - 0.05, ax + 0.05, ay - 0.012, ay + 0.012, 0.3, 0.35, 'steelK')


def hut(m):
    """ridge cap, gutters, snow guards, a chimney collar and rain cap, the gable window's frame and sill"""
    k = K(m)
    k.bx(-2.695, 2.695, -0.05, 0.05, 2.56, 2.64, 'steel', cull='')
    slope = 1.3 / 1.9
    for s in (-1, 1):
        k.fx(-2.65, 2.65, s * 1.897 if s > 0 else -1.97, 1.97 if s > 0 else -1.897, 1.2, 1.32, 'galv')   # gutter on the fascia
        y = s * 1.05
        rz = 2.6 - slope * 1.05
        k.fx(-2.4, 2.4, y - 0.015, y + 0.015, rz + 0.07, rz + 0.1, 'steelD')
        for i in range(9):
            x = -2.4 + i * 0.6
            k.fx(x - 0.015, x + 0.015, y - 0.011, y + 0.011, rz - 0.03, rz + 0.115, 'steelD')
    k.cyl(1.2, 0.6, 2.13, 0.17, 0.17, 0.1, 'steelK', seg=8)           # flashing
    k.cyl(1.2, 0.6, 2.7, 0.135, 0.135, 0.04, 'steelD', seg=8)         # clamp band
    k.cyl(1.2, 0.6, 3.28, 0.2, 0.05, 0.1, 'steelD', seg=8)            # rain cap
    k.push(0, 0, 90)
    window_frame_depth(k, -0.4, 0.4, 1.4, 1.9, -2.703, 'woodD', depth=0.035, t=0.04)
    drip_edge(k, -0.46, 0.46, 1.38, -2.703, 'woodD', d=0.07, t=0.03)
    k.pop()


def buried_module(m, roof, rnd=None):
    """container corner posts and window frames on the long faces, a hatch hinge and lock, antenna base and guy wires"""
    k = K(m)
    for deg in (0, 180):
        k.push(0, 0, deg)
        yf = -1.256
        for sx in (-1, 1):
            k.bx(sx * 3.69 - 0.045, sx * 3.69 + 0.045, yf - 0.012, yf + EMBED, 0.0, roof - 0.18, 'steelD')
        if deg == 0:
            for x in (-2.0, 0.8):
                window_frame_depth(k, x - 0.4, x + 0.4, 0.6, 1.2, yf, 'steelD', depth=0.04, t=0.04)
        k.pop()
    yf = 0.297                                                       # the roof hatch: hinges, handle, hasp
    for z in (2.3, 2.55):
        k.cyl(-0.97, yf - 0.02, z, 0.02, 0.02, 0.1, 'steelD', seg=6)
    k.bx(-0.62, -0.48, yf - 0.022, yf + EMBED, 2.42, 2.45, 'steelK')
    k.bx(-0.58, -0.52, yf - 0.02, yf + EMBED, 2.35, 2.4, 'black')
    ax, ay = 2.4, 0.8                                                 # antenna: base plate, collar, three guys to roof anchors
    k.fx(ax - 0.15, ax + 0.15, ay - 0.15, ay + 0.15, roof - 0.003, roof + 0.014, 'galv')
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.fx(ax + sx * 0.1 - 0.012, ax + sx * 0.1 + 0.012, ay + sy * 0.1 - 0.012, ay + sy * 0.1 + 0.012, roof + 0.01, roof + 0.03, 'steelD')
    k.cyl(ax, ay, roof + 0.012, 0.075, 0.075, 0.06, 'steelD', seg=8)
    for (gx, gy) in ((3.5, 1.1), (1.3, 1.15), (2.4, -0.85)):
        k.wire((ax, ay, roof + 1.5), (gx, gy, roof + 0.03), 0.012, 'steelK')
        k.fx(gx - 0.07, gx + 0.07, gy - 0.07, gy + 0.07, roof - 0.003, roof + 0.012, 'galv')
        k.fx(gx - 0.015, gx + 0.015, gy - 0.015, gy + 0.015, roof + 0.01, roof + 0.05, 'steelD')


def genset_s(m):
    k = K(m)
    for x, side in ((-1.295, -1), (1.295, 1)):
        corner_guard(k, x, -0.7, 0.22, 1.58, 'steelD', side=side)
    for x in (-1.2, 0.0, 1.2):
        for y in (-0.75, 0.75):
            k.fx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.197, 0.218, 'steelL')   # skid bolts
    k.cyl(0.9, 0.3, 1.58, 0.14, 0.14, 0.03, 'steelD', seg=8)          # stack flange, clamp band
    k.cyl(0.9, 0.3, 1.95, 0.105, 0.105, 0.04, 'steelD', seg=8)
    k.push(0, 0, 90)                                                  # +x face: a junction box and the cable run to the skid
    junction_box(k, 0.35, 1.0, -1.3, 'steelD', 'steelL', w=0.2, h=0.25, d=0.08)
    k.cyl(0.35, -1.326, 0.2, 0.02, 0.02, 0.68, 'black', seg=6)
    k.pop()


def gen_set(m):
    k = K(m)
    bolt_row(k, -1.1, 1.1, 2.22, -2.6, 8, 'steelL', s=0.026)
    for x, side in ((-1.195, -1), (1.195, 1)):
        corner_guard(k, x, -2.6, 0.32, 2.28, 'steelK', side=side)
    for sx in (-1, 1):
        for y in (-2.5, -1.0, 0.5, 2.0):
            k.fx(sx * 1.7 - 0.03, sx * 1.7 + 0.03, y - 0.03, y + 0.03, 0.297, 0.318, 'steelL')     # skid anchor bolts
    for z in (3.0, 3.8):                                              # stack: flange, clamp bands, rain cap
        k.cyl(0.6, -0.5, z, 0.175, 0.175, 0.05, 'steelD', seg=8)
    k.cyl(0.6, -0.5, 2.147, 0.22, 0.22, 0.043, 'steelD', seg=8)
    k.cyl(0.6, -0.5, 4.85, 0.24, 0.05, 0.12, 'steelD', seg=8)
    k.push(0, 0, 90)                                                  # +x side of the engine: bolts and a cable tray
    rivet_strip(k, -1.55, 1.35, 0.42, -1.1, 'steelD', every=0.3, s=0.02)
    cable_tray(k, -1.5, 1.3, 1.72, -1.1, 'galv', 'black')
    k.pop()


def boiler(m):
    k = K(m)
    for z in (0.9, 1.9, 2.9):                                         # insulation band clamps
        for deg in (90, 270):
            k.push(0.0, 0.2, deg)
            k.fx(-0.07, 0.07, -1.38, -1.25, z - 0.06, z + 0.06, 'steelD')
            k.pop()
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.fx(sx * 1.58 - 0.03, sx * 1.58 + 0.03, sy * 1.6 - 0.03, sy * 1.6 + 0.03, 0.247, 0.27, 'steelL')   # base bolts
    for x in (-0.2, 0.45):
        for z in (0.4, 1.15):
            k.fx(x - 0.02, x + 0.02, -1.778, -1.75 + EMBED, z - 0.02, z + 0.02, 'steelL')
    for z in (0.45, 1.1):                                             # burner door hinge
        k.fx(-0.5, -0.4, -1.775, -1.75 + EMBED, z - 0.06, z + 0.06, 'steelD')
    k.cyl(0, 0.2, 4.34, 0.4, 0.4, 0.05, 'steelD', seg=8)               # stack collar
    for (x, y, z) in ((1.7, -1.2, 5.8),):
        k.cyl(x, y, z, 0.2, 0.2, 0.05, 'steelD', seg=8)               # flue cap


def day_tank(m):
    k = K(m)
    yf = -0.75
    for x in (-0.95, 0.95):
        k.bx(x - 0.04, x + 0.04, yf - 0.012, yf + EMBED, 0.32, 1.58, 'steelD')
        for z in (0.4, 1.5):
            k.bx(x - 0.011, x + 0.011, yf - 0.022, yf - 0.012 + EMBED, z - 0.011, z + 0.011, 'steelL')
    k.cyl(1.1, yf + 0.003, 0.5, 0.04, 0.04, 0.18, 'steelD', seg=8, rot=(90, 0, 0))
    k.m.sp((1.1, yf - 0.2, 0.5), 0.07, 'orangeD', seg=(8, 5), hull='none')
    k.fx(0.95, 1.25, yf - 0.215, yf - 0.19, 0.55, 0.59, 'redE')
    k.cyl(-1.1, yf + 0.003, 0.9, 0.025, 0.025, 0.06, 'glass', seg=6, rot=(90, 0, 0))   # sight glass
    k.cyl(0.9, 0.3, 1.88, 0.14, 0.14, 0.03, 'steelD', seg=8)          # cap lock ring


def switchboard(m):
    k = K(m)
    yf = -0.2
    kick_plate(k, -1.9, 1.9, yf, 'steelD', h=0.14, bolts='steelL')
    k.bx(-1.9, 1.9, yf - 0.03, yf + EMBED, 2.14, 2.196, 'steelD')
    conduit_run(k, -1.9, 1.9, 2.11, yf, 'steelD', 'steelL', every=1.0)
    for i in range(4):
        x = -1.45 + i * 0.97
        for z in (0.5, 1.7):
            k.cyl(x - 0.43, yf - 0.022, z - 0.06, 0.017, 0.017, 0.12, 'steelK', seg=6)
        k.bx(x + 0.4, x + 0.43, yf - 0.026, yf - 0.003 + EMBED, 0.95, 1.15, 'black')


def rack(m, end):
    """core racks: floor plates and wall ties on the uprights"""
    k = K(m)
    for x in (-1.45, 0.0, 1.45):
        k.bx(x - 0.075, x + 0.075, -0.474, 0.474, 0.0, 0.012, 'steelD', cull='')
        k.bx(x - 0.06, x + 0.06, -0.474, 0.474, 2.388, 2.4 + 0.004, 'steelD', cull='')
        for y in (-0.4, 0.4):
            k.fx(x - 0.014, x + 0.014, y - 0.014, y + 0.014, 0.01, 0.026, 'steelL')


def rail_foot(m, x, y, z0, c):
    """a base flange under a guard-rail post"""
    m.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, z0 - 0.003, z0 + 0.012, c, hull='none', cull='b')
