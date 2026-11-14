"""kit-seabase modelled detail (tactical look plan Stage 11): the fixings, seals, dogs, hinges, flanges and service runs of
a real seabed research station, added to the pieces the player sees most. The kit uses the PM / SM model (hull modes),
so `K` wraps it in the interface the kit_base detail helpers expect: every part is hull='none' (no outline shell),
stands >= 3 mm proud, starts 3 mm inside what it sits on, and horizontal runs stop 5 mm short of the piece's sides.
Faces that look toward Blender -Y use the helpers at the plane y = yf; for other faces `k.push(x, y, deg)` first
(push 90: local -Y looks along world +X; push -90: along -X; push 180: along +Y)."""
import math

from mathutils import Matrix

from kit_base import PROUD, EMBED, bolt_row, rivet_strip, drip_edge, conduit_run, junction_box, vent
from parking_base import poly


class K:
    """a kit_base-style view over an SM model: parts are painted detail (no outline shell)"""

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

    def cyl(self, x, y, z, r1, r2, h, c, seg=8, ink=False, bevel=False, rot=(0, 0, 0), caps=True):
        self.m.cy((x, y, z), r1, r2, h, c, seg=seg, rot=rot, caps=caps, hull='none')


def vbolts(k, x, z0, z1, n, yf, c, s=0.022):
    """n bolt heads in a column along z at x (plane y = yf)"""
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        k.bx(x - s / 2, x + s / 2, yf - PROUD - 0.004, yf + EMBED, z - s / 2, z + s / 2, c)


def hseam(k, x0, x1, z, yf, c, t=0.014, d=0.006):
    k.bx(x0 + 0.005, x1 - 0.005, yf - d, yf + EMBED, z - t / 2, z + t / 2, c)


def hex_bolt(k, x, z, yf, c, r=0.014, h=0.012):
    """a hex bolt head standing on a -Y face at yf"""
    k.cyl(x, yf + EMBED, z, r, r, h + EMBED, c, seg=6, rot=(90, 0, 0))


def bolt_circle(k, x, z, yf, rad, n, c, s=0.02, start=0.0):
    for i in range(n):
        a = start + i / n * 2 * math.pi
        bx, bz = x + math.cos(a) * rad, z + math.sin(a) * rad
        k.bx(bx - s / 2, bx + s / 2, yf - PROUD - 0.004, yf + EMBED, bz - s / 2, bz + s / 2, c)


def handwheel(m, x, y, z, r, c, spoke=0.012):
    """a small handwheel in the plane y facing -Y (rim one closed tube, crossing spokes, hub), no outline shell"""
    n = 8
    pts = [(x + math.cos(i / n * 2 * math.pi) * r, y, z + math.sin(i / n * 2 * math.pi) * r) for i in range(n)]
    m.tube(pts + [pts[0]], 0.012, c, seg=4, hull='none', caps=False)
    for a in (0.4, 0.4 + math.pi / 2):
        m.tube([(x + math.cos(a) * r, y, z + math.sin(a) * r), (x - math.cos(a) * r, y, z - math.sin(a) * r)], spoke, c, seg=4, hull='none', caps=False)
    m.cy((x, y + 0.02, z), 0.022, 0.022, 0.05, 'steelD', seg=6, rot=(90, 0, 0), hull='none')


def gauge_dial(m, x, y, z, r=0.05):
    """a pressure gauge: chrome bezel, dial, needle, facing -Y at plane y (no outline shell)"""
    m.cy((x, y + EMBED, z), r, r, 0.03 + EMBED, 'chrome', seg=10, rot=(90, 0, 0), hull='none')
    m.cy((x, y - 0.03, z), r * 0.8, r * 0.8, 0.004, 'paper', seg=10, rot=(90, 0, 0), hull='none')
    m.bx(x - 0.003, x + 0.003, y - 0.038, y - 0.033, z, z + r * 0.62, 'fireR', hull='none', cull='')


# ================================================================ walls
# wall faces: the base plane is y = -0.5; painted bands sit at -0.506 / -0.509 (service: dado 0.18-1.17 and plate above
# 4.3; research: bands below 1.09 and above 4.5). Detail strips are 16 mm proud of -0.5 everywhere (front plane -0.516),
# so they never share a plane with the 3 mm paint, the lettering (-0.512) or each other.
def cover_strip(k, x, z0, z1, ys, c, w=0.03):
    """a vertical panel-joint cover strip at x with its front at y = -0.516; ys = the face plane it stands on"""
    k.bx(x - w / 2, x + w / 2, -0.516, ys + EMBED, z0, z1, c)


def joint_bolts(k, x, z0, z1, n, ys, c, s=0.012):
    if x < 0:           # bolts on the right-hand cover only: the neighbour module brings the left one
        return
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        k.bx(x - s / 2, x + s / 2, -0.524, ys + EMBED - 0.01, z - s / 2, z + s / 2, c)


def wall_service(m):
    """service-steel wall: panel-joint cover strips with bolts at both module edges, a cap on the hazard band, belt rivets"""
    k = K(m)
    for x in (-0.47, 0.47):
        cover_strip(k, x, 0.2, 1.05, -0.506, 'rib')
        cover_strip(k, x, 1.2, 4.28, -0.5, 'rib')
        cover_strip(k, x, 4.47, 7.4, -0.506, 'rib')
        joint_bolts(k, x, 0.3, 1.0, 3, -0.506, 'steelL')
        joint_bolts(k, x, 1.4, 4.1, 5, -0.5, 'steelL')
        joint_bolts(k, x, 4.6, 7.2, 6, -0.506, 'steelL')
    drip_edge(k, -0.495, 0.495, 1.17, -0.5, 'steelD', d=0.022, t=0.025)
    k.bx(-0.495, 0.495, -0.512, -0.506 + EMBED, 5.993, 6.007, 'rib')
    rivet_strip(k, -0.43, 0.43, 5.9, -0.506, 'steelL', every=0.2, s=0.014)


def service_run(m):
    """the plain service module: a pipe run with clamps, flange joints, a valve and a gauge, a cable tray, a junction box"""
    k = K(m)
    yf = -0.5
    z, r = 3.7, 0.055
    ya = yf - r - 0.04                                  # pipe axis
    k.cyl(-0.495, ya, z, r, r, 0.99, 'tealD', seg=8, rot=(0, 90, 0))
    for x in (-0.36, 0.36):                             # stand-off clamps
        k.bx(x - 0.025, x + 0.025, yf - 0.04, yf + EMBED, z - r - 0.03, z + r + 0.03, 'steelD')
        k.bx(x - 0.03, x + 0.03, ya - r - 0.012, ya - r + 0.012, z - r - 0.03, z + r + 0.03, 'steelL')
    for x in (-0.18, 0.18):                             # flange pairs with bolt heads
        k.cyl(x - 0.015, ya, z, 0.085, 0.085, 0.03, 'steelL', seg=8, rot=(0, 90, 0))
        for a in (0.0, math.pi / 2, math.pi, math.pi * 1.5):
            yy, zz = ya + math.sin(a) * 0.07, z + math.cos(a) * 0.07
            k.bx(x - 0.022, x + 0.022, yy - 0.01, yy + 0.01, zz - 0.01, zz + 0.01, 'rib', cull='')
    # valve on the pipe at x = 0: body, bonnet, stem and handwheel
    m.bx(-0.06, 0.06, ya - 0.075, ya + 0.075, z - 0.075, z + 0.075, 'steel', hull='none', cull='')
    m.cy((0.0, ya, z + 0.075), 0.04, 0.04, 0.09, 'steelD', seg=6, hull='none')
    m.cy((0.0, ya, z + 0.165), 0.012, 0.012, 0.07, 'chrome', seg=5, hull='none')
    m.cy((0.0, ya, z + 0.235), 0.09, 0.09, 0.016, 'fireR', seg=8, hull='none')
    # a gauge on a stub
    k.bx(-0.332, -0.308, ya - 0.03, ya + 0.0, z + 0.05, z + 0.22, 'steelD', cull='')
    gauge_dial(m, -0.32, ya - 0.04, z + 0.27)
    # cable tray with two cables and a junction box with its lid screws
    k.bx(-0.495, 0.495, yf - 0.09, yf + EMBED, 2.45, 2.5, 'steelD')
    k.bx(-0.495, 0.495, yf - 0.09, yf - 0.083, 2.5, 2.56, 'steelD')
    for off, zz in ((0.03, 2.51), (0.06, 2.52)):
        k.bx(-0.485, 0.485, yf - off - 0.012, yf - off + 0.012, zz, zz + 0.024, 'cable')
    junction_box(k, -0.25, 2.0, yf, 'steelD', 'steelL', w=0.2, h=0.26, d=0.08)
    for dx, dz in ((-0.08, -0.1), (0.08, -0.1), (-0.08, 0.1), (0.08, 0.1)):
        hex_bolt(k, -0.25 + dx, 2.0 + dz, yf - 0.08 - PROUD, 'chrome', r=0.01, h=0.008)
    k.bx(0.26, 0.28, yf - 0.03, yf + EMBED, 2.18, 2.45, 'cable')                    # a cable dropping to the tray


def wall_research(m):
    """research-panel wall: panel-joint cover strips with screws, drip caps on the teal band and under the head panel"""
    k = K(m)
    for x in (-0.47, 0.47):
        cover_strip(k, x, 0.17, 0.93, -0.5, 'seam')
        cover_strip(k, x, 1.1, 3.18, -0.5, 'seam')
        cover_strip(k, x, 3.26, 4.48, -0.5, 'seam')
        cover_strip(k, x, 4.52, 7.4, -0.506, 'seam')
        joint_bolts(k, x, 0.3, 0.8, 2, -0.5, 'steelL', s=0.012)
        joint_bolts(k, x, 1.3, 3.0, 4, -0.5, 'steelL', s=0.012)
        joint_bolts(k, x, 4.7, 7.2, 5, -0.506, 'steelL', s=0.012)
    drip_edge(k, -0.495, 0.495, 1.09, -0.5, 'tealD', d=0.02, t=0.022)
    drip_edge(k, -0.495, 0.495, 4.5, -0.5, 'seam', d=0.016, t=0.02)
    rivet_strip(k, -0.43, 0.43, 6.2, -0.506, 'seam', every=0.2, s=0.014)


def research_run(m):
    """the plain research module: a cable tray, a junction box, a louvred vent and a conduit"""
    k = K(m)
    yf = -0.5
    k.bx(-0.495, 0.495, yf - 0.09, yf + EMBED, 3.6, 3.65, 'steelD')
    k.bx(-0.495, 0.495, yf - 0.09, yf - 0.083, 3.65, 3.71, 'steelD')
    for off, zz in ((0.03, 3.66), (0.06, 3.67)):
        k.bx(-0.485, 0.485, yf - off - 0.012, yf - off + 0.012, zz, zz + 0.024, 'cable')
    junction_box(k, 0.26, 2.7, yf, 'panelG', 'steelL', w=0.2, h=0.26, d=0.08)
    vent(k, -0.2, 2.35, yf, 0.3, 0.34, 'steelD', 'rib')
    conduit_run(k, -0.495, 0.495, 1.6, yf, 'steelD', 'steelL', every=0.5)


def wall_hull(m):
    """outer pressure hull: a ring-frame flange with two bolt rows (the module joint) and weld lines"""
    k = K(m)
    yf = -0.5
    k.bx(-0.07, 0.07, yf - 0.024, yf + EMBED, 0.52, 6.88, 'hullD')
    for x in (-0.082, 0.07):
        k.bx(x, x + 0.012, yf - 0.014, yf + EMBED, 0.52, 6.88, 'rib')
    for i in range(22):
        z = 0.62 + i * 0.28
        if 1.85 < z < 2.15 or 3.65 < z < 3.95 or 5.45 < z < 5.75:
            continue
        for x in ((-0.035,) if i % 2 else (0.035,)):
            k.bx(x - 0.011, x + 0.011, yf - 0.036, yf + EMBED - 0.01, z - 0.011, z + 0.011, 'rivet')
    for z in (3.0, 4.8):
        k.bx(-0.495, 0.495, yf - 0.02, yf + EMBED, z - 0.012, z + 0.012, "rib")


def port_rim(m, z, r, c='steelL'):
    """a retaining ring standing proud of a porthole's flange, with hex bolts, so the viewport reads with depth"""
    k = K(m)
    y0 = -0.572
    rr = r + 0.045
    yy = y0 - 0.04
    m.cy((0, y0 + EMBED, z), rr, rr, 0.04 + EMBED, c, seg=14, rot=(90, 0, 0), caps=False, hull='none')
    for i in range(14):
        p, q = i / 14 * 2 * math.pi, (i + 1) / 14 * 2 * math.pi
        pts = [(math.cos(a) * rad, yy, z + math.sin(a) * rad) for a, rad in ((p, r), (p, rr), (q, rr), (q, r))]
        poly(m, pts, c, (0, -1, 0))
    for i in range(7):
        a = (i + 0.5) / 7 * 2 * math.pi + 0.2
        rm = r + 0.022
        hex_bolt(k, math.cos(a) * rm, z + math.sin(a) * rm, yy, 'chrome', r=0.0095, h=0.01)


# ================================================================ pieces
def valve_panel(m):
    """flange joints with bolt heads on the header, screws on the gauge plate"""
    k = K(m)
    for x in (-0.4, 0.0, 0.4):
        m.cy((x - 0.015, -0.66, 1.6), 0.145, 0.145, 0.03, 'steelL', seg=8, rot=(0, 90, 0), hull='none')
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4
            yy, zz = -0.66 + math.cos(ang) * 0.12, 1.6 + math.sin(ang) * 0.12
            k.bx(x - 0.01, x + 0.026, yy - 0.011, yy + 0.011, zz - 0.011, zz + 0.011, 'rib', cull='')
    for x, z in ((-0.26, 2.14), (0.26, 2.14), (-0.26, 2.46), (0.26, 2.46)):
        hex_bolt(k, x, z, -0.54, 'chrome', r=0.011, h=0.008)


def bulkhead(m):
    """watertight door: latch dogs and bolt columns on both frame faces, a manual override wheel, the ram housing's end
    plates, gland and bolt row, kick bolts on the coaming"""
    k = K(m)
    for sy in (-1, 1):
        if sy > 0:
            k.push(0, 0, 180)
        yf = -1.12
        for sx in (-1, 1):
            xc = sx * 1.31
            for z in ((0.6, 1.35, 2.1) if sx > 0 else (0.45, 2.05)):          # dogs: a latch block with a pin
                k.bx(xc - 0.065, xc + 0.065, yf - 0.05, yf + EMBED, z - 0.07, z + 0.07, 'steelL')
                k.bx(xc - 0.03, xc + 0.03, yf - 0.062, yf - 0.05 + EMBED, z - 0.025, z + 0.025, 'rib')
            vbolts(k, xc - 0.085 * sx, 0.4, 2.3, 5, yf, 'steelD', s=0.022)
        yh = -1.16
        for x0, x1 in ((-1.295, -1.26), (0.86, 0.895)):                        # ram housing end plates
            k.bx(x0, x1, yh - 0.014, yh + EMBED, 3.044, 3.306, "rib")
        rivet_strip(k, -1.2, 0.8, 3.175, yh, 'steelL', every=0.2, s=0.016)
        k.cyl(0.895, yh + 0.08, 3.175, 0.035, 0.035, 0.07, 'chrome', seg=8, rot=(0, 90, 0))   # piston gland
        rivet_strip(k, -1.15, 1.15, 0.15, -1.0, 'steelL', every=0.2, s=0.018)  # coaming kick bolts
        if sy > 0:
            k.pop()
    # manual override wheel on the pocket-side jamb: a plate, a stem and the wheel
    k.bx(-1.36, -1.26, -1.12 - 0.012, -1.12 + EMBED, 1.1, 1.4, 'steelD')
    m.cy((-1.31, -1.12 + EMBED, 1.25), 0.03, 0.03, 0.11 + EMBED, 'chrome', seg=6, rot=(90, 0, 0), hull='none')
    handwheel(m, -1.31, -1.225, 1.25, 0.1, 'fireR')


def hatch(m):
    """floor hatch: radial dogs round the rim, a hinge pair, a rubber seal ring on the lid"""
    for i in range(12):
        a = i / 12 * 2 * math.pi + math.pi / 12
        r = 1.185
        m.bxr(math.cos(a) * r, math.sin(a) * r, 0.105, 0.11, 0.07, 0.04, 'steelL', rot=(0, 0, math.degrees(a)), hull='none')
        m.bxr(math.cos(a) * (r + 0.01), math.sin(a) * (r + 0.01), 0.125, 0.04, 0.045, 0.02, 'rib', rot=(0, 0, math.degrees(a)), hull='none')
    for sx in (-1, 1):
        m.bx(sx * 0.3 - 0.07, sx * 0.3 + 0.07, 0.92, 1.12, 0.1, 0.17, 'steelD', hull='none', cull='b')
        m.cy((sx * 0.3 - 0.085, 1.02, 0.17), 0.028, 0.028, 0.17, 'chrome', seg=6, rot=(0, 90, 0), hull='none')
    n = 20
    for i in range(n):
        p, q = i / n * 2 * math.pi, (i + 1) / n * 2 * math.pi
        pts = [(math.cos(a) * rad, math.sin(a) * rad, 0.1625) for a, rad in ((p, 0.78), (q, 0.78), (q, 0.82), (p, 0.82))]
        poly(m, pts, 'rubber', (0, 0, 1))


def stair(m, W, L, n, landing, DECK):
    """stair: tread-end angle brackets, a bolt per step on the stringer faces, base plates under the stanchions"""
    k = K(m)
    run = (L - landing) / n
    for sx in (-1, 1):
        k.push(0, 0, 90 if sx > 0 else -90)             # local -Y looks along sx; local x = sx * world y
        yf = -(W / 2 + 0.08)
        for i in range(n):
            wy = -L / 2 + i * run + run * 0.5
            lx = wy if sx > 0 else -wy
            z = 0.3 + 0.4603 * (wy + L / 2) - 0.13
            k.bx(lx - 0.012, lx + 0.012, yf - PROUD - 0.004, yf + EMBED, z - 0.012, z + 0.012, 'steelL')
        k.pop()
        for i in range(n):
            y0 = -L / 2 + i * run
            top = (i + 1) * DECK / n
            xi = sx * W / 2
            a, b = sorted((xi, xi - sx * 0.045))
            m.bx(a, b, y0 + 0.08, y0 + 0.2, top - 0.2, top - 0.06, 'steelL', hull='none', cull='')
        xr = sx * (W / 2 + 0.04)
        for j in range(4):
            t = (j + 0.5) / 4
            yy = -L / 2 + 0.1 + t * (L - landing - 0.1)
            zz = 0.3 + t * (DECK - 0.3)
            m.bx(xr - 0.033, xr + 0.033, yy - 0.045, yy + 0.045, zz + 0.004, zz + 0.022, 'steelD', hull='none', cull='')


def bench(m):
    """lab bench: toe kick, drawer line, door pulls, panel screws, edge banding, side bolts"""
    k = K(m)
    yf = -0.423
    k.bx(-0.94, 0.94, -0.432, -0.42 + EMBED, 0.004, 0.075, 'steelD')
    hseam(k, -0.9, 0.87, 0.42, yf, 'seam', t=0.012, d=0.004)
    for x in (-0.46, 0.43):
        k.bx(x - 0.1, x + 0.1, yf - 0.032, yf - 0.02, 0.66, 0.686, 'chrome')
        for dx in (-0.08, 0.08):
            k.bx(x + dx - 0.008, x + dx + 0.008, yf - 0.02, yf + EMBED, 0.66, 0.686, 'steelD')
    for x0 in (-0.9, 0.0):
        for xx in (x0 + 0.06, x0 + 0.84):
            for zz in (0.14, 0.72):
                hex_bolt(k, xx, zz, yf, 'steelL', r=0.01, h=0.006)
    k.bx(-0.965, 0.965, -0.464, -0.45 + EMBED, 0.866, 0.912, 'steelL')
    for sx in (-1, 1):
        k.push(0, 0, 90 if sx > 0 else -90)
        vbolts(k, 0.0, 0.2, 0.7, 2, -0.95, 'steelL', s=0.02)
        k.pop()


def dive_locker(m):
    """dive locker: bolt columns on the uprights and divider, kick strip, hook rails with hooks, a header band"""
    k = K(m)
    yf = -0.4
    for x in (-0.92, 0.92, 0.0):
        vbolts(k, x, 0.25, 2.1, 4, yf, 'steelL', s=0.02)
    k.bx(-0.88, 0.88, yf - 0.012, yf + EMBED, 0.004, 0.065, 'steelD')
    for x0 in (-0.89, 0.03):
        k.bx(x0 + 0.04, x0 + 0.82, 0.1 - 0.02, 0.1 + EMBED, 1.93, 1.97, 'steelL')
        for dx in (0.12, 0.7):
            m.bx(x0 + dx - 0.012, x0 + dx + 0.012, 0.03, 0.08, 1.9, 1.98, 'chrome', hull='none', cull='')
            m.bx(x0 + dx - 0.008, x0 + dx + 0.008, 0.025, 0.05, 1.86, 1.91, 'chrome', hull='none', cull='')
    k.bx(-0.88, 0.88, yf - 0.016, yf + EMBED, 2.21, 2.265, 'steelL')
    rivet_strip(k, -0.85, 0.85, 2.24, yf - 0.016, 'steelD', every=0.17, s=0.014)


def tank_rack(m):
    """tank rack: base bolts, ratchet buckles on the straps, backboard bolts and top cap"""
    k = K(m)
    bolt_row(k, -0.9, 0.9, 0.05, -0.3, 6, 'steelL', s=0.022)
    for z in (0.45, 0.95):
        for x in (-0.86, 0.0, 0.86):
            m.bx(x - 0.028, x + 0.028, -0.09, -0.05, z - 0.005, z + 0.065, 'steelL', hull='none', cull='')
    yb = 0.3
    k.bx(-0.94, 0.94, yb - 0.025, yb + EMBED, 1.43, 1.496, 'steelL')
    bolt_row(k, -0.9, 0.9, 1.38, yb, 6, 'steelD', s=0.022)
    bolt_row(k, -0.9, 0.9, 0.22, yb, 6, 'steelD', s=0.022)


def winch(m):
    """winch: bearing bosses with bolt circles on the frame posts, motor end-plate bolts, skid hold-down feet and bolts"""
    k = K(m)
    for sx in (-1, 1):
        x = sx * 0.68
        m.cy((x - sx * EMBED, 0.0, 1.0), 0.17, 0.17, 0.04 + EMBED, 'steelD', seg=10, rot=(0, 90 * sx, 0), hull='none')
        k.push(0, 0, 90 if sx > 0 else -90)
        bolt_circle(k, 0.0, 1.0, -0.72, 0.12, 6, 'steelL', s=0.022, start=0.2)
        k.pop()
    k.push(0, 0, 90)
    bolt_circle(k, -0.25, 0.42, -0.98, 0.17, 6, 'steelL', s=0.022, start=0.5)
    k.pop()
    for sx in (-1, 1):
        for sy in (-1, 1):
            xx, yy = sx * 0.8, sy * 0.62
            m.bx(xx - 0.07, xx + 0.07, yy - 0.07, yy + 0.07, 0.136, 0.158, 'steelL', hull='none', cull='')
            m.cy((xx, yy, 0.158), 0.02, 0.02, 0.016, 'rib', seg=6, hull='none')
    bolt_row(k, -0.9, -0.5, 0.07, -0.8, 3, 'steelL', s=0.026)
    bolt_row(k, 0.5, 0.9, 0.07, -0.8, 3, 'steelL', s=0.026)


def moonpool(m, PX, PY, CW, CH):
    """moon pool: bolted nosing angle along the inner lip, base plate and bolt row on the outer curb faces, foot flanges
    with two bolts under every rail stanchion"""
    k = K(m)
    ox, oy = PX + CW, PY + CW
    k.bx(-PX + 0.005, PX - 0.005, PY - 0.02, PY + EMBED, CH - 0.13, CH - 0.004, 'steelL')     # north bar, inner face
    bolt_row(k, -PX + 0.2, PX - 0.2, CH - 0.065, PY - 0.02, 14, 'rib', s=0.026)
    k.push(0, 0, 180)                                                                           # south bar, inner face
    k.bx(-PX + 0.005, PX - 0.005, PY - 0.02, PY + EMBED, CH - 0.13, CH - 0.004, 'steelL')
    bolt_row(k, -PX + 0.2, PX - 0.2, CH - 0.065, PY - 0.02, 14, 'rib', s=0.026)
    k.pop()
    for sx in (-1, 1):                                                                          # east / west inner faces
        k.push(0, 0, -90 if sx > 0 else 90)
        k.bx(-PY + 0.035, PY - 0.035, PX - 0.02, PX + EMBED, CH - 0.13, CH - 0.004, 'steelL')
        bolt_row(k, -PY + 0.2, PY - 0.2, CH - 0.065, PX - 0.02, 10, 'rib', s=0.026)
        k.pop()
    for sy in (-1, 1):                                                                          # outer faces N / S
        k.push(0, 0, 0 if sy < 0 else 180)
        k.bx(-ox + 0.005, ox - 0.005, -oy - 0.012, -oy + EMBED, 0.004, 0.09, 'steelL')
        bolt_row(k, -ox + 0.2, ox - 0.2, 0.3, -oy, 14, 'steelL', s=0.024)
        k.pop()
    for sx in (-1, 1):                                                                          # outer faces E / W
        k.push(0, 0, 90 if sx > 0 else -90)
        k.bx(-PY + 0.005, PY - 0.005, -ox - 0.012, -ox + EMBED, 0.004, 0.09, 'steelL')
        bolt_row(k, -PY + 0.2, PY - 0.2, 0.3, -ox, 10, 'steelL', s=0.024)
        k.pop()
    spots = []
    for sy in (-1, 1):
        for i in range(9):
            spots.append((-ox + 0.15 + i * (2 * ox - 0.3) / 8, sy * (oy - 0.12)))
    for sx in (-1, 1):
        for i in range(1, 6):
            spots.append((sx * (ox - 0.12), -oy + 0.15 + i * (2 * oy - 0.3) / 6))
    for (x, y) in spots:
        m.bx(x - 0.065, x + 0.065, y - 0.065, y + 0.065, CH - 0.004, CH + 0.02, 'steelD', hull='none', cull='b')
        for d in (-0.045, 0.045):
            m.bx(x + d - 0.011, x + d + 0.011, y + d - 0.011, y + d + 0.011, CH + 0.02, CH + 0.03, 'steelL', hull='none', cull='b')
