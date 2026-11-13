"""kit-downtown modelled detail (tactical look plan Stage 11): the street-level fittings a player sees up close.

Ground-floor facade fittings (Win / Lobby / Pier modules): shutter guide rails, a bottom bar with pull and lock,
door frames with depth, pull handles and kick plates, a threshold, drainpipes with straps and shoes, utility boxes
with conduit and louvred vents. Street props: hydrant, bench, lamp post, bus shelter, newsstand (base plates,
bolts, hatches, sign plates).

Same rules as the other kits' detail passes: every part is hull='none' (no outline shell), stands at least 3 mm
proud and sinks 3 mm into whatever it sits on; the facade plane is y = -0.5 (F(d) = d proud of it). Nothing here
changes a piece's origin, footprint, collision boxes or the parts already drawn: it only adds shapes.
"""
import math

from downtown_base import F

EMB = 0.003


def fbx(m, x0, x1, d, z0, z1, c, d0=0.0, cull='k'):
    """facade fitting: front face d proud of the facade plane, back sunk EMB into it (d0: back stands d0 proud instead)"""
    m.bx(x0, x1, F(d), F(d0) + EMB, z0, z1, c, hull='none', cull=cull)


def vpipe(m, x, z0, z1, d, r, c, strap_c, straps, shoe=True):
    """a drainpipe on straps: pipe centre sits so its face stands (d) proud, straps hug it and sink into the wall"""
    cy = F(d - r)
    m.cy((x, cy, z0), r, r, z1 - z0, c, seg=8, hull='none')
    for z in straps:
        m.bx(x - r - 0.012, x + r + 0.012, F(d + 0.006), F(0) + EMB, z - 0.016, z + 0.016, strap_c, hull='none', cull='k')
    if shoe:   # the shoe kicking out at the foot
        m.bx(x - r - 0.006, x + r + 0.006, F(d + 0.03), F(0) + EMB, z0, z0 + 0.1, strap_c, hull='none', cull='kb')


def utility_box(m, x, z, w, h, d, c, lid_c):
    """a meter / junction box with a lid panel, a handle and a hasp"""
    fbx(m, x - w / 2, x + w / 2, d, z - h / 2, z + h / 2, c)
    fbx(m, x - w / 2 + 0.02, x + w / 2 - 0.02, d + 0.006, z - h / 2 + 0.02, z + h / 2 - 0.02, lid_c, d0=d - 0.001)
    fbx(m, x + w / 2 - 0.055, x + w / 2 - 0.035, d + 0.016, z - 0.025, z + 0.025, 'chrome', d0=d + 0.003)


def vconduit(m, x, z0, z1, d, c, clip_c, r=0.016, every=0.7):
    m.cy((x, F(d - r), z0), r, r, z1 - z0, c, seg=6, hull='none')
    n = max(1, int((z1 - z0) / every))
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        m.bx(x - r - 0.008, x + r + 0.008, F(d + 0.004), F(0) + EMB, z - 0.012, z + 0.012, clip_c, hull='none', cull='k')


def louvre(m, x, z, w, h, d, frame_c, slat_c, n=None):
    """a louvred grille: frame d proud, slats inside it"""
    n = n or max(3, int(h / 0.045))
    t = 0.022
    fbx(m, x - w / 2, x + w / 2, d, z - h / 2, z - h / 2 + t, frame_c)
    fbx(m, x - w / 2, x + w / 2, d, z + h / 2 - t, z + h / 2, frame_c)
    fbx(m, x - w / 2, x - w / 2 + t, d, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, frame_c)
    fbx(m, x + w / 2 - t, x + w / 2, d, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, frame_c)
    fbx(m, x - w / 2 + t - 0.005, x + w / 2 - t + 0.005, d - 0.012, z - h / 2 + t - 0.005, z + h / 2 - t + 0.005, 'ink', d0=d - 0.004)   # dark void behind
    for i in range(n):
        zz = z - h / 2 + t + (h - 2 * t) * (i + 0.5) / n
        fbx(m, x - w / 2 + t - 0.008, x + w / 2 - t + 0.008, d - 0.007, zz - 0.007, zz + 0.007, slat_c, d0=d - 0.012)


# ================================================================ facade modules
def win_detail(m, mat, si):
    """closed shopfront: shutter guide rails, a bottom bar with pull and lock, a lock plate, a kerb-side base trim.
    si is the same index ground() got (its shutter top height is a function of it)."""
    zt = 1.55 + (si % 3) * 0.3
    for sx in (-1, 1):   # guide rails either side of the shutter
        x0, x1 = (-0.497, -0.452) if sx < 0 else (0.452, 0.497)
        fbx(m, x0, x1, 0.046, 0.33, 3.14, 'steelD', cull='kb')
        for z in (0.55, 1.2, 1.85, 2.5, 3.05):   # rail bolts
            fbx(m, x0 + 0.014, x1 - 0.014, 0.054, z - 0.011, z + 0.011, 'steel', d0=0.046, cull='kb')
    fbx(m, -0.45, 0.45, 0.042, zt - 0.045, zt + 0.004, 'steelD', cull='kb')     # bottom bar
    fbx(m, -0.08, 0.08, 0.052, zt - 0.03, zt - 0.006, 'steel', d0=0.04)           # pull handle
    fbx(m, 0.2, 0.26, 0.05, zt - 0.036, zt - 0.008, 'chrome', d0=0.04)            # lock
    fbx(m, 0.218, 0.242, 0.056, zt - 0.026, zt - 0.018, 'ink', d0=0.049)             # key slot
    fbx(m, -0.46, -0.3, 0.07, 3.145, 3.265, 'steel', d0=0.058)                    # shutter-box access panel
    fbx(m, 0.34, 0.46, 0.07, 3.145, 3.265, 'steel', d0=0.058)
    fbx(m, 0.0, 0.1, 0.07, 3.16, 3.25, 'ink', d0=0.058)                           # motor vent slot


def lobby_detail(m, mat, si):
    """office entrance: framed double doors with pull handles, kick plates, a centre astragal, a threshold step,
    an intercom plate and a wall lamp"""
    # frame depth round the door opening
    fbx(m, -0.455, -0.415, 0.05, 0.02, 2.58, 'mull', cull='kb')
    fbx(m, 0.415, 0.455, 0.05, 0.02, 2.58, 'mull', cull='kb')
    fbx(m, -0.462, 0.462, 0.058, 2.5, 2.6, 'mull', cull='kb')
    fbx(m, -0.02, 0.02, 0.046, 0.02, 2.5, 'mull', cull='kb')                     # astragal between the leaves
    fbx(m, -0.38, -0.022, 0.056, 2.41, 2.45, 'mull', cull='kb')                  # leaf top rail
    fbx(m, 0.022, 0.38, 0.056, 2.41, 2.45, 'mull', cull='kb')
    # kick plates and mid rails
    for a, b in ((-0.38, -0.024), (0.024, 0.38)):
        fbx(m, a, b, 0.036, 0.04, 0.3, 'steel', d0=0.02)
        fbx(m, a, b, 0.032, 1.32, 1.4, 'mull', d0=0.02)
    # pull handles: vertical bar on two stand-offs
    for hx in (-0.075, 0.075):
        fbx(m, hx - 0.012, hx + 0.012, 0.062, 0.95, 1.38, 'chrome', d0=0.046)
        for z in (1.0, 1.32):
            fbx(m, hx - 0.007, hx + 0.007, 0.046, z - 0.012, z + 0.012, 'chrome', d0=0.02)
    # threshold step
    fbx(m, -0.43, 0.43, 0.09, 0.0, 0.035, 'conc', d0=0.0, cull='kb')
    # intercom plate and a lamp beside the door
    fbx(m, 0.445, 0.495, 0.034, 1.1, 1.32, 'steelD', d0=0.01)
    fbx(m, 0.455, 0.485, 0.04, 1.24, 1.29, 'light', d0=0.034)
    fbx(m, 0.455, 0.485, 0.04, 1.14, 1.2, 'ink', d0=0.034)
    fbx(m, -0.485, -0.455, 0.1, 2.15, 2.4, 'steelD', d0=0.01)                      # wall lamp back plate
    fbx(m, -0.48, -0.46, 0.15, 2.19, 2.36, 'light', d0=0.1)


def pier_detail(m, mat, si):
    """solid ground-floor pier: drainpipe on straps with a shoe, a meter box with conduit, a louvred vent"""
    vpipe(m, 0.43, 0.04, 3.26, 0.095, 0.04, 'steelD', 'mull', (0.45, 1.5, 2.55))
    fbx(m, 0.385, 0.475, 0.115, 3.2, 3.28, 'steelD', d0=0.05, cull='k')         # collar under the sign band
    utility_box(m, -0.33, 0.78, 0.26, 0.34, 0.1, 'steel', 'steelD')
    vconduit(m, -0.42, 0.95, 2.0, 0.045, 'galv', 'mull')
    louvre(m, 0.08, 0.6, 0.3, 0.2, 0.034, 'steelD', 'steel')


FACADE_DETAIL = {'Win': win_detail, 'Lobby': lobby_detail, 'Pier': pier_detail}


# ================================================================ street props
def hydrant_detail(m):
    for k in range(4):
        a = k * 1.5708 + 0.7854
        m.cy((math.cos(a) * 0.14, math.sin(a) * 0.14, 0.08), 0.014, 0.014, 0.014, 'steelD', seg=6, hull='none')
    m.cy((0, 0, 0.5), 0.13, 0.13, 0.03, 'steelD', seg=8, hull='none')              # barrel collar
    m.cy((0, 0, 0.7), 0.04, 0.04, 0.04, 'steelD', seg=5, hull='none')              # operating nut
    for sx in (-1, 1):
        m.cy((sx * 0.178, 0, 0.42), 0.05, 0.05, 0.018, 'steelD', seg=6, rot=(0, sx * 90, 0), hull='none')   # outlet caps
    m.cy((0.0, 0.178, 0.38), 0.07, 0.07, 0.016, 'steelD', seg=6, rot=(-90, 0, 0), hull='none')            # pumper cap


def bench_detail(m):
    top = 0.47
    for x in (-0.85, 0.85):
        for y in (-0.18, -0.03, 0.12):   # bolt heads on the seat slats
            m.bx(x - 0.014, x + 0.014, y - 0.014, y + 0.014, top - 0.003, top + 0.009, 'steelD', hull='none', cull='b')
        for z in (0.62, 0.79):           # and on the backrest slats
            m.bx(x - 0.014, x + 0.014, 0.22 - 0.01, 0.22 + EMB, z - 0.014, z + 0.014, 'steelD', hull='none', cull='k')
        # armrest on a post, and floor plates with bolts under both legs
        m.bx(x - 0.05, x + 0.05, -0.22, 0.2, 0.6, 0.645, 'mull', hull='none')
        m.bx(x - 0.022, x + 0.022, -0.21, -0.17, 0.44, 0.61, 'mull', hull='none', cull='b')
        for ya, yb in ((-0.256, -0.12), (0.12, 0.256)):
            m.bx(x - 0.07, x + 0.07, ya, yb, 0.0, 0.014, 'steelD', hull='none', cull='b')
            for yy in (ya + 0.025, yb - 0.025):
                m.bx(x - 0.015, x + 0.015, yy - 0.015, yy + 0.015, 0.011, 0.023, 'steel', hull='none', cull='b')
    m.bx(-0.03, 0.03, -0.2, 0.2, 0.0, 0.43, 'mull', hull='none', cull='b')           # centre support
    m.bx(-0.03, 0.03, 0.2, 0.25, 0.43, 0.9, 'mull', hull='none', cull='b')


def lamp_detail(m):
    # base plate with four bolts
    m.bx(-0.17, 0.17, 0.08, 0.42, 0.0, 0.025, 'steelD', hull='none', cull='b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.125 - 0.016, sx * 0.125 + 0.016, 0.25 + sy * 0.125 - 0.016, 0.25 + sy * 0.125 + 0.016, 0.022, 0.04, 'steel', hull='none', cull='b')
    # hand-hole door on the pole base (road side)
    m.bx(-0.05, 0.05, 0.1404, 0.1621, 0.12, 0.38, 'steelD', hull='none', cull='k')
    m.bx(-0.03, 0.03, 0.1304, 0.1404 + 0.002, 0.15, 0.17, 'steel', hull='none', cull='k')   # lock lug
    m.bx(-0.07, 0.07, 0.1421 - 0.012, 0.1421 + 0.001, 0.115, 0.125, 'mull', hull='none', cull='k')
    # collar, gusset brace under the arm, photocell
    m.cy((0, 0.25, 0.51), 0.085, 0.085, 0.03, 'steelD', seg=6, hull='none')
    m.cy((0, 0.25, 3.8), 0.075, 0.075, 0.035, 'steelD', seg=6, hull='none')
    m.bm_((0, 0.25, 6.1), (0, -0.7, 6.88), 0.04, 'steel', hull='none')
    m.cy((0, -1.55, 7.058), 0.035, 0.035, 0.05, 'ink', seg=6, hull='none')
    # blade sign on the pole, road side, held by two clamps
    for z in (2.62, 2.92):
        m.bx(-0.04, 0.04, 0.128, 0.191, z - 0.012, z + 0.012, 'steelD', hull='none', cull='k')
    m.bx(-0.15, 0.15, 0.1, 0.128, 2.55, 2.98, 'signB', hull='none', cull='k')
    m.bx(-0.11, 0.11, 0.092, 0.101, 2.68, 2.84, 'pWhite', hull='none', cull='k')
    m.bx(-0.11, 0.11, 0.092, 0.101, 2.88, 2.92, 'pWhite', hull='none', cull='k')


def busstop_detail(m):
    for x in (-1.85, 1.85):
        for y in (-0.55, 0.65):   # post base plates and bolts
            m.bx(x - 0.085, x + 0.085, y - 0.085, y + 0.085, 0.0, 0.014, 'steelD', hull='none', cull='b')
            for sx in (-1, 1):
                for sy in (-1, 1):
                    m.bx(x + sx * 0.062 - 0.011, x + sx * 0.062 + 0.011, y + sy * 0.062 - 0.011, y + sy * 0.062 + 0.011, 0.011, 0.024, 'steel', hull='none', cull='b')
    for x in (-1.7, 0.0, 1.7):    # spider clamps on the glass back panel
        for z in (0.27, 2.28):
            m.bx(x - 0.035, x + 0.035, 0.575, 0.64, z - 0.035, z + 0.035, 'steel', hull='none')
            m.bx(x - 0.012, x + 0.012, 0.56, 0.575 + EMB, z - 0.012, z + 0.012, 'chrome', hull='none', cull='k')
    m.bx(-1.97, 1.97, -0.84, -0.8, 2.598, 2.67, 'mull', hull='none', cull='b')     # roof upstand
    # poster frame on the end panel, bolts on the seat
    x0, x1 = 1.79, 1.813
    m.bx(x0, x1, -0.52, 0.62, 0.22, 0.306, 'mull', hull='none', cull='r')
    m.bx(x0, x1, -0.52, 0.62, 2.2, 2.28, 'mull', hull='none', cull='r')
    m.bx(x0 + 0.006, x1 - 0.002, -0.504, -0.45, 0.3, 2.2, 'mull', hull='none', cull='r')
    m.bx(x0 + 0.006, x1 - 0.002, 0.55, 0.604, 0.3, 2.2, 'mull', hull='none', cull='r')
    for x in (-1.3, 1.0):
        for y in (0.28, 0.46):
            m.bx(x - 0.012, x + 0.012, y - 0.012, y + 0.012, 0.497, 0.509, 'steelD', hull='none', cull='b')


def newsstand_detail(m):
    m.bx(-0.93, 0.93, -1.222, -1.197, 0.0, 0.14, 'steelD', hull='none', cull='kb')   # kick plate
    for z in (0.35, 0.95, 1.55):                                                    # shelf lips under each rack row
        m.bx(-0.85, 0.85, -1.236, -1.197, z - 0.035, z, 'steelD', hull='none', cull='k')
    for x in (-0.86, 0.86):                                                         # rack side rails
        m.bx(x - 0.012, x + 0.012, -1.226, -1.197, 0.15, 2.15, 'steelD', hull='none', cull='k')
    # +X wall: louvred vent and drain stub; -X wall: a meter box with conduit
    xf = 0.95
    t = 0.022
    vy, vz, vw, vh = 0.3, 1.6, 0.5, 0.34
    for (ya, yb, za, zb) in ((vy - vw / 2, vy + vw / 2, vz - vh / 2, vz - vh / 2 + t), (vy - vw / 2, vy + vw / 2, vz + vh / 2 - t, vz + vh / 2),
                             (vy - vw / 2, vy - vw / 2 + t, vz - vh / 2 + t, vz + vh / 2 - t), (vy + vw / 2 - t, vy + vw / 2, vz - vh / 2 + t, vz + vh / 2 - t)):
        m.bx(xf - EMB, xf + 0.016, ya, yb, za, zb, 'mull', hull='none', cull='l')
    m.bx(xf - EMB, xf + 0.004, vy - vw / 2 + t - 0.005, vy + vw / 2 - t + 0.005, vz - vh / 2 + t - 0.005, vz + vh / 2 - t + 0.005, 'ink', hull='none', cull='l')
    n = 6
    for i in range(n):
        zz = vz - vh / 2 + t + (vh - 2 * t) * (i + 0.5) / n
        m.bx(xf - 0.002, xf + 0.009, vy - vw / 2 + t - 0.008, vy + vw / 2 - t + 0.008, zz - 0.007, zz + 0.007, 'steel', hull='none', cull='l')
    xm = -0.95   # -X wall meter box
    m.bx(xm - 0.1, xm + EMB, 0.5, 0.78, 0.9, 1.3, 'steel', hull='none', cull='r')
    m.bx(xm - 0.106, xm - 0.099, 0.52, 0.76, 0.92, 1.28, 'steelD', hull='none', cull='r')
    m.bx(xm - 0.116, xm - 0.1, 0.53, 0.55, 1.07, 1.13, 'chrome', hull='none', cull='r')
    m.cy((xm - 0.034, 0.64, 1.3), 0.016, 0.016, 0.9, 'galv', seg=6, hull='none')
    for z in (1.5, 1.95):
        m.bx(xm - 0.06, xm + EMB, 0.62, 0.66, z - 0.012, z + 0.012, 'mull', hull='none', cull='r')
    # back door (+Y wall): frame, handle, kick plate
    yb = 1.45
    for (xa, xb, za, zb) in ((-0.42, 0.42, 0.04, 0.1), (-0.42, 0.42, 2.0, 2.06), (-0.42, -0.36, 0.1, 2.0), (0.36, 0.42, 0.1, 2.0)):
        m.bx(xa, xb, yb - EMB, yb + 0.014, za, zb, 'mull', hull='none', cull='f')
    m.bx(-0.36, 0.36, yb - EMB, yb + 0.006, 0.1, 2.0, 'woodD', hull='none', cull='f')
    m.bx(-0.34, 0.34, yb + 0.004, yb + 0.02, 0.09, 0.34, 'steel', hull='none', cull='f')
    m.bx(0.24, 0.3, yb + 0.004, yb + 0.03, 0.95, 1.05, 'chrome', hull='none', cull='f')
