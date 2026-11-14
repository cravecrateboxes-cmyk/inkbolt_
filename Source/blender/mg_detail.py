"""kit-mossgarden modelled detail (tactical look plan Stage 11): coping joints, drip bands and base ledges on the garden
walls and piers, mortar joints between the string courses, gate hinges, pintles and latch, balustrade plinths and
collars, stair riser grooves and newel bands, pergola column collars, strap ties and rafter ends, bench bolts and
end grain, lamp base plate and bolts, bridge keystones and coping joints, glasshouse bar caps, base course, ridge
fixings, gazebo collars and roof seams, signpost shoes and collars, urn pedestal mouldings, maze sign bolts, shed hinges
and muntins. Same rules as every detail pass: every part is ink=False (no outline shell), stands >= 3 mm proud, is sunk
3 mm into what it sits on, horizontal runs stop 5 mm short of a piece's sides, and flat joints are single quads 4-5 mm
proud. Nothing here changes a piece's origin, footprint, collision boxes or the parts already drawn."""
import math

from mg_base import TER, RISE, TREAD


def bx(k, x0, x1, y0, y1, z0, z1, c):
    k.bx(x0, x1, y0, y1, z0, z1, c, ink=False)


def vjoints(k, x0, x1, z0, z1, y, s, step, off, c='stone3', skip=None, w=0.032):
    """staggered vertical mortar joints on a -Y / +Y face at y (quads, 5 mm proud)"""
    x = x0 + step * off
    while x < x1 - 0.06:
        if x > x0 + 0.06 and not (skip and skip(x)):
            k.qy(x - w / 2, x + w / 2, z0, z1, y, s, c)
        x += step


def vjoints_x(k, y0, y1, z0, z1, x, s, step, off, c='stone3', w=0.032):
    y = y0 + step * off
    while y < y1 - 0.06:
        if y > y0 + 0.06:
            k.qx(y - w / 2, y + w / 2, z0, z1, x, s, c)
        y += step


# ================================================================ garden walls
def wall_detail(k, x0, x1, kind):
    w = x1 - x0
    pier = kind == 'pier'

    def skip(x):
        return pier and 0.1 < x < 0.9
    n = max(2, int(round(w / 0.67)))
    for i in range(1, n):
        x = x0 + w * i / n
        if skip(x):
            continue
        k.qz(x - 0.007, x + 0.007, -0.47, 0.495, 3.604, 1, 'stoneD')       # coping joints, top and front
        k.qy(x - 0.007, x + 0.007, 3.43, 3.59, -0.484, -1, 'stoneD')
    bx(k, x0 + 0.005, x1 - 0.005, -0.447, -0.417, 3.34, 3.423, 'stone')    # drip band under the coping
    bx(k, x0 + 0.005, x1 - 0.005, -0.452, -0.417, 0.46, 0.52, 'stone')     # ledge on top of the plinth course
    rows = ((0.535, 1.3), (1.335, 2.2), (2.235, 3.05), (3.085, 3.34))
    for j, (za, zb) in enumerate(rows):
        vjoints(k, x0, x1, za, zb, -0.426, -1, 0.8, 0.5 if j % 2 else 1.0, skip=skip)
    if pier:   # panelled pier: base and neck mouldings and a raised panel frame
        bx(k, 0.17, 0.83, -0.556, 0.485, 0.004, 0.2, 'stone2')
        bx(k, 0.17, 0.83, -0.553, 0.485, 3.64, 3.753, 'stone2')
        y = -0.535
        k.qy(0.28, 0.72, 0.6, 0.625, y, -1, 'stone3')
        k.qy(0.28, 0.72, 3.075, 3.1, y, -1, 'stone3')
        k.qy(0.28, 0.305, 0.625, 3.075, y, -1, 'stone3')
        k.qy(0.695, 0.72, 0.625, 3.075, y, -1, 'stone3')


def pier_faces(k, hx, z0, z1, rows, off=0.5):
    """courses and staggered joints on the four faces of a square pier of half-width hx (5 mm proud)"""
    p = hx + 0.005
    h = hx - 0.005
    for z in rows:
        k.qy(-h, h, z, z + 0.03, -p, -1, 'stone3')
        k.qy(-h, h, z, z + 0.03, p, 1, 'stone3')
        k.qx(-h, h, z, z + 0.03, -p, -1, 'stone3')
        k.qx(-h, h, z, z + 0.03, p, 1, 'stone3')
    zs = [z0] + [z + 0.03 for z in rows]
    ze = list(rows) + [z1]
    for j, (za, zb) in enumerate(zip(zs, ze)):
        x = -0.17 if j % 2 else 0.17
        k.qy(x - 0.016, x + 0.016, za, zb, -p, -1, 'stone3')
        k.qy(-x - 0.016, -x + 0.016, za, zb, p, 1, 'stone3')
        k.qx(x - 0.016, x + 0.016, za, zb, -p, -1, 'stone3')
        k.qx(-x - 0.016, -x + 0.016, za, zb, p, 1, 'stone3')


def wallcorner_detail(k):
    bx(k, -0.53, 0.53, -0.53, 0.53, 0.004, 0.25, 'stone3')
    bx(k, -0.53, 0.53, -0.53, 0.53, 3.66, 3.803, 'stone2')
    pier_faces(k, 0.5, 0.27, 3.66, (0.95, 1.7, 2.45))


# ================================================================ gate
def gate_detail(k):
    for s in (-1, 1):
        x0, x1 = (1.55, 2.45) if s > 0 else (-2.45, -1.55)
        bx(k, x0 - 0.03, x1 + 0.03, -0.48, 0.48, 0.497, 0.56, 'stone')      # ledge on the plinth
        bx(k, x0 - 0.03, x1 + 0.03, -0.48, 0.48, 3.78, 3.903, 'stone')      # neck moulding under the cap
    # hinge pintles on the left pier (they reach the shutter's edge), latch keeper on the right one
    for z in (0.17, 2.77):
        bx(k, -1.553, -1.497, -0.015, 0.015, z - 0.03, z + 0.03, 'bronze')
    bx(k, 1.503, 1.553, -0.03, 0.03, 1.04, 1.14, 'bronze')
    # bolts on the name plaque (verdigris plate, both faces)
    for sy in (-1, 1):
        ya, yb = (-0.082, -0.067) if sy < 0 else (0.067, 0.082)
        for x in (-1.1, 1.1):
            for z in (3.61, 3.93):
                bx(k, x - 0.013, x + 0.013, ya, yb, z - 0.013, z + 0.013, 'bronze')


def shutter_detail(k):
    for sy in (-1, 1):
        y0, y1 = (-0.056, -0.047) if sy < 0 else (0.047, 0.056)
        for z0, z1 in ((0.12, 0.22), (2.72, 2.82)):       # strap hinges on the end rails
            bx(k, -1.495, -1.12, y0, y1, z0 + 0.012, z1 - 0.012, 'bronze')
        bx(k, 1.2, 1.45, y0, y1, 1.062, 1.118, 'bronze')      # latch bar on the middle rail


# ================================================================ terrace
def _terrace_face_joints(k, skip=None, xs=None):
    rows = ((0.0, 0.75), (0.785, 1.55), (1.585, TER))
    for j, (za, zb) in enumerate(rows):
        za = max(za, 0.1) if j == 0 else za
        for x in xs[j]:
            k.qy(x - 0.016, x + 0.016, za, zb, 0.505, 1, 'stone3')


def balustrade_dets(k, xs, z0, h):
    for x in xs:
        bx(k, x - 0.085, x + 0.085, 0.225, 0.395, z0 - 0.003, z0 + 0.03, 'stone2')
        bx(k, x - 0.075, x + 0.075, 0.235, 0.385, z0 + h - 0.04, z0 + h + 0.003, 'stone2')


def terracewall_detail(k):
    _terrace_face_joints(k, xs=([0.2], [-0.25], [0.25]))
    for x in (-0.1665, 0.1665):
        k.qz(x - 0.007, x + 0.007, 0.03, 0.59, TER + 0.104, 1, 'stoneD')           # coping joints
        k.qy(x - 0.007, x + 0.007, TER + 0.01, TER + 0.09, 0.015, -1, 'stoneD')
        k.qz(x - 0.007, x + 0.007, 0.14, 0.48, TER + 0.984, 1, 'stoneD')           # rail joints
        k.qy(x - 0.007, x + 0.007, TER + 0.86, TER + 0.96, 0.125, -1, 'stoneD')
    balustrade_dets(k, (-0.333, 0.0, 0.333), TER + 0.1, 0.74)


def terracewall_p_detail(k):
    _terrace_face_joints(k, xs=([-0.41], [0.41], [-0.41]))
    balustrade_dets(k, (-0.39, 0.39), TER + 0.2, 0.64)
    bx(k, -0.3, 0.3, 0.01, 0.63, TER + 0.097, TER + 0.19, 'stone2')
    bx(k, -0.3, 0.3, 0.01, 0.63, TER + 1.02, TER + 1.123, 'stone2')
    y = 0.035
    k.qy(-0.17, 0.17, TER + 0.3, TER + 0.325, y, -1, 'stone3')
    k.qy(-0.17, 0.17, TER + 0.875, TER + 0.9, y, -1, 'stone3')
    k.qy(-0.17, -0.145, TER + 0.325, TER + 0.875, y, -1, 'stone3')
    k.qy(0.145, 0.17, TER + 0.325, TER + 0.875, y, -1, 'stone3')


def terracecorner_detail(k):
    bx(k, -0.39, 0.39, -0.39, 0.39, TER + 0.147, TER + 0.19, 'stone2')
    bx(k, -0.39, 0.39, -0.39, 0.39, TER + 1.02, TER + 1.103, 'stone2')
    for z in (0.75, 1.55):
        for (face, p, s) in (('y', 0.505, 1), ('y', -0.505, -1), ('x', 0.505, 1), ('x', -0.505, -1)):
            (k.qy if face == 'y' else k.qx)(-0.495, 0.495, z, z + 0.035, p, s, 'stone3')


def stair_detail(k, hw, ch=0.4):
    for i in range(13):       # a shadow groove under each nosing (flat: the treads are untouched)
        y0 = -1.75 + i * TREAD
        k.qy(-hw + 0.01, hw - 0.01, (i + 1) * RISE - 0.035, (i + 1) * RISE - 0.008, y0 - 0.0045, -1, 'stoneD')
    for s in (-1, 1):
        xi, xo = sorted((s * hw, s * (hw + ch)))
        bx(k, xi - 0.06, xo + 0.06, -2.53, -2.05, 0.004, 0.2, 'stone2')
        bx(k, xi - 0.06, xo + 0.06, -2.53, -2.05, 0.93, 1.053, 'stone2')


# ================================================================ pergola, bench, lamp
def pergola_detail(k):
    for x in (-2.55, 0.0, 2.55):
        for y in (-1.6, 1.6):
            k.cyl(x, y, 0.297, 0.19, 0.19, 0.063, 'stone3', seg=8, ink=False)
            k.cyl(x, y, 2.46, 0.19, 0.19, 0.093, 'stone3', seg=8, ink=False)
    for i in range(10):
        x = -2.7 + i * 0.6
        for sy in (-1, 1):
            k.qy(x - 0.045, x + 0.045, 2.955, 3.095, sy * 2.005, sy, 'woodL')    # rafter tail end grain
            ya, yb = sy * 1.6 + sy * 0.1, sy * 1.6 - sy * 0.1
            for yy, s in ((sy * 1.705, sy), (sy * 1.495, -sy)):                    # iron strap ties over the beams
                k.qy(x - 0.03, x + 0.03, 2.74, 2.945, yy, s, 'iron')


def bench_detail(k, x, y, w):
    h = w / 2
    for s in (-1, 1):
        xe = x + s * (h - 0.08)
        bx(k, xe - 0.075, xe + 0.075, y - 0.31, y + 0.27, 0.004, 0.06, 'stone3')      # foot pads
        bx(k, xe - 0.07, xe + 0.07, y + 0.17, y + 0.30, 0.915, 0.94, 'stone')          # arm caps on the back supports
        for j in range(2):
            yc = y - 0.3 + j * 0.25 + 0.125
            k.qz(xe - 0.015, xe + 0.015, yc - 0.015, yc + 0.015, 0.474, 1, 'iron')       # bolts through the slats
            k.qx(yc - 0.1, yc + 0.1, 0.425, 0.465, x + s * (h + 0.004), s, 'woodL')      # end grain
        k.qx(y + 0.205, y + 0.255, 0.62, 0.84, x + s * (h - 0.026), s, 'woodL')


def lamp_detail(k):
    bx(k, -0.2, 0.2, -0.2, 0.2, 0.004, 0.03, 'iron')
    bx(k, -0.2, 0.2, -0.2, 0.2, 0.27, 0.303, 'iron')
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.qz(sx * 0.16 - 0.015, sx * 0.16 + 0.015, sy * 0.16 - 0.015, sy * 0.16 + 0.015, 0.034, 1, 'bronze')
    k.cyl(0, 0, 0.297, 0.1, 0.09, 0.063, 'bronze', seg=6, ink=False)
    k.cyl(0, 0, 2.66, 0.085, 0.085, 0.063, 'bronze', seg=6, ink=False)
    bx(k, -0.2, 0.2, -0.2, 0.2, 3.075, 3.115, 'bronze')


# ================================================================ bridge
def bridge_detail(k, W, P):
    for s in (-1, 1):
        xa, xb = sorted((s * P, s * W))
        for y in (-0.75, 0.0, 0.75):
            k.qz(xa - 0.012, xb + 0.012, y - 0.007, y + 0.007, 1.504, 1, 'stoneD')    # coping joints
            for xx, ss in ((s * (P - 0.005), -s), (s * (W + 0.005), s)):
                k.qx(y - 0.007, y + 0.007, 0.93, 1.38, xx, ss, 'stoneD')              # parapet joints
        k.qx(-0.12, 0.12, 0.68, 0.99, s * (W + 0.011), s, 'stone')                    # keystone
    for side in (-1, 1):
        for s in (-1, 1):
            xa, xb = sorted((s * (P - 0.045), s * (W + 0.035)))
            ya, yb = sorted((side * 2.515, side * 2.22))
            bx(k, xa - 0.03, xb + 0.03, ya - 0.01, yb + 0.01, 0.76, 0.84, 'stone2')   # newel cap slab


# ================================================================ glasshouse
def glasshouse_detail(k, D):
    # glazing-bar caps (verdigris pressure strips) on the outer faces of the mullions
    for i in range(13):
        x = -6.0 + i
        bx(k, x - 0.04, x + 0.04, 4.877, 4.89, 0.72, 3.56, 'verd')
        if abs(x) > D + 0.2:
            bx(k, x - 0.04, x + 0.04, -4.89, -4.877, 0.72, 3.56, 'verd')
    for i in range(9):
        y = -4.0 + i
        if abs(y) > D + 0.2:
            for x in (-6.85, 6.85):
                bx(k, x - 0.04 if x < 0 else x + 0.027, x - 0.027 if x < 0 else x + 0.04, y - 0.04, y + 0.04, 0.72, 3.56, 'verd')
    # base course: foot band, mortar joints and a course line on the dwarf walls
    for (x0, x1, y, s) in ((-6.995, 6.995, 5.0, 1), (-6.995, -D - 0.005, -5.0, -1), (D + 0.005, 6.995, -5.0, -1)):
        bx(k, x0, x1, y if s > 0 else y - 0.03, y + 0.03 if s > 0 else y, 0.004, 0.19, 'stone3')
        yy = y + s * 0.005
        k.qy(x0, x1, 0.3, 0.33, yy, s, 'stoneD')
        vjoints(k, x0, x1, 0.335, 0.6, yy, s, 0.9, 0.5, c='stoneD', w=0.028)
        vjoints(k, x0, x1, 0.2, 0.3, yy, s, 0.9, 1.0, c='stoneD', w=0.028)
    for x, s in ((-7.0, -1), (7.0, 1)):
        for (y0, y1) in ((-4.695, -D - 0.005), (D + 0.005, 4.695)):
            xx = x + s * 0.005
            k.qx(y0, y1, 0.3, 0.33, xx, s, 'stoneD')
            vjoints_x(k, y0, y1, 0.335, 0.6, xx, s, 0.9, 0.5, c='stoneD', w=0.028)
            vjoints_x(k, y0, y1, 0.2, 0.3, xx, s, 0.9, 1.0, c='stoneD', w=0.028)
    # corner posts: caps
    for (x, y) in ((-6.9, -4.9), (6.9, -4.9), (-6.9, 4.9), (6.9, 4.9)):
        bx(k, x - 0.165, x + 0.165, y - 0.165, y + 0.165, 3.847, 3.9, 'verd')
    # ridge bar and fixings, eave gutters of the lantern
    bx(k, -5.145, 5.145, -0.03, 0.03, 7.625, 7.68, 'bronze')
    for i in range(11):
        k.cyl(-5.0 + i, 0.0, 7.64, 0.055, 0.055, 0.05, 'bronze', seg=4, ink=False)
    for sy in (-1, 1):
        bx(k, -5.145, 5.145, sy * 1.148 - (0.03 if sy < 0 else 0.0), sy * 1.148 + (0.0 if sy < 0 else 0.03), 7.07, 7.13, 'bronze')


# ================================================================ gazebo
def gazebo_detail(k, cols):
    for (x, y) in cols:
        k.cyl(x, y, 2.72, 0.1, 0.1, 0.085, 'bronze', seg=6, ink=False)
    for (z, r) in ((2.855, 2.62), (3.385, 1.97), (4.135, 1.0)):
        k.cyl(0, 0, z, r, r, 0.05, 'bronze', seg=8, ink=False)
    k.cyl(0, 0, 4.93, 0.22, 0.22, 0.05, 'bronze', seg=6, ink=False)
    for s in (-1, 1):
        x = s * 1.45
        for d in (-0.07, 0.07):
            k.qz(x + d - 0.006, x + d + 0.006, -0.745, 0.745, 0.844, 1, 'wood2')


# ================================================================ signs, pedestals
def signpost_detail(k, words):
    bx(k, -0.1, 0.1, -0.1, 0.1, 0.004, 0.03, 'iron')
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.qz(sx * 0.07 - 0.012, sx * 0.07 + 0.012, sy * 0.07 - 0.012, sy * 0.07 + 0.012, 0.034, 1, 'bronze')
    bx(k, -0.085, 0.085, -0.085, 0.085, 2.38, 2.453, 'iron')
    for j, (deg, w) in enumerate(words):
        z = 2.15 - j * 0.32
        bx(k, -0.077, 0.077, -0.077, 0.077, z + 0.015, z + 0.045, 'bronze')
        bx(k, -0.077, 0.077, -0.077, 0.077, z + 0.175, z + 0.205, 'bronze')
        k.push(0, 0, deg)
        for sy in (-1, 1):
            k.qy(0.1, 0.13, z + 0.095, z + 0.125, sy * 0.036, sy, 'bronze')
        k.pop()


def pedestal_detail(k, hx, z0, z1, hc):
    """base and neck mouldings and a raised panel on a square pedestal of half-width hx between z0 and z1"""
    m = hx + 0.03
    bx(k, -m, m, -m, m, z0 - 0.003, z0 + 0.06, 'stone3')
    bx(k, -m, m, -m, m, z1 - 0.06, z1 + 0.003, 'stone3')
    p = hx + 0.005
    for (f, s) in (('y', 1), ('y', -1), ('x', 1), ('x', -1)):
        (k.qy if f == 'y' else k.qx)(-hc, hc, z0 + 0.14, z1 - 0.14, s * p, s, 'stone2')


def urn_detail(k):
    pedestal_detail(k, 0.22, 0.14, 0.72, 0.12)


def armillary_detail(k):
    pedestal_detail(k, 0.2, 0.14, 1.0, 0.11)


def mazearch_detail(k):
    for sy in (-1, 1):
        for x in (-0.52, 0.52):
            for z in (2.54, 2.78):
                k.qy(x - 0.014, x + 0.014, z - 0.014, z + 0.014, sy * 0.036, sy, 'bronze')


def shed_detail(k):
    for x0, x1 in ((-2.295, -2.18), (2.18, 2.295)):
        bx(k, x0, x1, -1.615, -1.597, 0.004, 2.39, 'wood2')          # corner boards
    y = -1.665
    for z in (0.35, 1.6):                                              # strap hinges on the door
        k.qy(-0.41, -0.12, z, z + 0.07, y, -1, 'iron')
    k.qy(0.18, 0.4, 0.95, 1.1, y, -1, 'iron')                          # lock plate
    for x in (-1.45, 1.45):
        for (xa, xb) in ((x - 0.4, x - 0.03), (x + 0.03, x + 0.4)):
            bx(k, xa, xb, -1.66, -1.64, 1.4, 1.46, 'frame')          # glazing bar, split round the mullion
