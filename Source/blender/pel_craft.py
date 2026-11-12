"""INKBOLT kit-pelagic aircraft and vehicles: the light aircraft at the spawn (open canopy, boarding stair), the
naval fighter (body + spread wings / folded wings / closed canopy / maintenance parts, combined per symbol with the
theme's `with`), the helicopter, the deck tractor, the ordnance carts, the crash tender, the escort warships (backdrop).
All made up. Noses point to Blender -Y (the piece's front) unless noted. Conventions: pel_base.py."""
import math

from mathutils import Matrix, Vector

from pel_base import *  # noqa: F401,F403
from pel_base import new, make, text, hazard, window_band, window_band_x

F4 = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]


def plate(m, pts, off, c, hull='full'):
    """a 4-cornered plate: the quad pts and the same quad moved by `off` (wings, fins, panels at any angle)"""
    v = list(pts) + [(p[0] + off[0], p[1] + off[1], p[2] + off[2]) for p in pts]
    return skin(m, (v, F4), c, hull=hull)


def rot_about_x(m, y, z, deg):
    """a parent frame turned deg about the X axis through (y, z)"""
    return m.parent @ Matrix.Translation((0, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'X') @ Matrix.Translation((0, -y, -z))


def le_boxes(cols, xs, le, te, z0, z1, mirror=True):
    """collision for a swept surface: one box per span band, from the leading edge at the band's outer end to the
    trailing edge (so no box sticks out ahead of the drawn edge)"""
    for xa, xb in zip(xs, xs[1:]):
        y0, y1 = le(xb), min(te(xa), te(xb))
        for s in ((-1, 1) if mirror else (1,)):
            cols.append(cb(s * xa, y0, z0, s * xb, y1, z1))


# ================================================================ the naval fighter (made-up "Skua"), nose -Y
FUS = [(-7.6, 0.0, 1.55, 0.0, 0.0), (-7.0, 0.0, 1.56, 0.26, 0.26), (-6.0, 0.0, 1.6, 0.48, 0.46), (-4.6, 0.0, 1.68, 0.66, 0.6),
       (-2.6, 0.0, 1.72, 0.8, 0.64), (0.0, 0.0, 1.7, 0.86, 0.6), (3.6, 0.0, 1.64, 0.86, 0.56), (6.4, 0.0, 1.58, 0.74, 0.5),
       (7.1, 0.0, 1.56, 0.6, 0.44)]
WR, WT = 0.8, 5.4                                    # wing root / tip half span


def w_le(x):
    return -1.8 + (x - WR) * (4.4 / (WT - WR))


def w_te(x):
    return 4.4 - (x - WR) * (0.4 / (WT - WR))


def build_jet(pal, ao):
    m = new(pal)

    def col(k, i, ang):
        if k <= 1:
            return 'navyD'
        return 'navyL' if math.sin(ang) < -0.55 else 'navy'
    loft(m, FUS, col, seg=8, a0=math.pi / 8)
    # engine nacelles with their intakes and nozzles, the spine between them
    for s in (-1, 1):
        x = s * 1.02
        loft(m, [(-1.2, x, 1.38, 0.44, 0.42), (2.0, x, 1.38, 0.5, 0.46), (6.2, x, 1.4, 0.48, 0.44), (7.05, x, 1.4, 0.42, 0.4)],
             lambda k, i, a: 'navyL' if math.sin(a) < -0.55 else 'navy', seg=8, a0=math.pi / 8)
        x0, x1 = sorted((s * 0.72, s * 1.5))
        wedge(m, x0, x1, -3.4, -1.0, 0.98, 1.82, 0.96, 1.82, 'navy')
        fq(m, x0 + 0.06, x1 - 0.06, -3.403, 1.04, 1.76, 'black')
        cyl_y(m, x, 7.0, 7.65, 1.4, 0.43, 'steelD', seg=10, r1=0.38)
        vdisc(m, x, 7.653, 1.4, 0.3, 'black', seg=10, face=1)
        # stabilators
        slab(m, [(s * 1.3, 5.4), (s * 3.6, 6.6), (s * 3.6, 7.45), (s * 1.3, 7.6)][::s], 1.48, 1.58, 'navy')
        # canted twin fins (20 degrees out)
        b0, b1 = (s * 1.05, 3.9, 1.95), (s * 1.05, 7.0, 1.95)
        t0, t1 = (s * 1.85, 6.0, 4.35), (s * 1.85, 7.35, 4.35)
        plate(m, [b0, b1, t1, t0], (-s * 0.075, 0.0, 0.03), 'navy')
        # main gear: strut, wheel, door
        xg = s * 1.55
        m.cy((xg, 1.6, 0.42), 0.06, 0.06, 0.62, 'steel', seg=6)
        wheel(m, xg, 1.6, 0.42, 0.42, 0.26, c='tire', hub='steel', seg=10)
        m.bx(xg - s * 0.02, xg + s * 0.02, 0.9, 2.3, 0.45, 1.05, 'navyL', cull='')
    # cockpit sill, the spine, the nose gear, the tail hook
    m.bx(-0.3, 0.3, -2.3, 6.2, 2.15, 2.32, 'navy', cull='b')
    m.cy((0, -5.0, 0.3), 0.05, 0.05, 1.05, 'steel', seg=6)
    wheel(m, 0.0, -5.0, 0.3, 0.3, 0.18, c='tire', hub='steel', seg=10)
    m.bx(-0.02, 0.02, -5.7, -4.4, 0.75, 1.15, 'navyL', cull='')
    m.bm_((0, 5.9, 1.2), (0, 7.4, 0.55), 0.09, 'yellow')
    m.bm_((0, 7.35, 0.6), (0, 7.55, 0.42), 0.12, 'black')
    # markings: a made-up roundel (a grey ring round a trident bar), the side number, NO STEP boxes
    for s in (-1, 1):
        x = s * 1.505
        xdisc(m, x + s * 0.003, -2.3, 1.42, 0.3, 'navyD', seg=10, face=s)
        xdisc(m, x + s * 0.006, -2.3, 1.42, 0.2, 'navyL', seg=10, face=s)
        m.bx(x + s * 0.007, x + s * 0.009, -2.33, -2.27, 1.27, 1.6, 'navyD', hull='none', cull='tbfk' + ('l' if s > 0 else 'r'))
    for s in (-1, 1):
        text(m, '104', s * 0.62, -5.0, 1.62, 0.3, 'black', face='x+' if s > 0 else 'x-')
    make('Jet_Body', m, ao, cols=[cb(-0.3, -7.2, 1.3, 0.3, -6.2, 1.85), cb(-0.5, -6.2, 1.15, 0.5, -4.9, 2.05), cb(-0.68, -4.9, 1.05, 0.68, -3.4, 2.3),
                                     cb(-1.5, -3.4, 0.9, 1.5, 7.6, 2.35)] + stab_cols())

    # ---- spread wings (with wingtip missiles)
    m = new(pal)
    for s in (-1, 1):
        slab(m, [(s * WR, -1.8), (s * WT, 2.6), (s * WT, 4.0), (s * WR, 4.4)][::s], 1.45, 1.6, 'navy')
        slab(m, [(s * 0.7, -4.6), (s * 1.45, -1.4), (s * 1.45, 0.4), (s * 0.7, 0.4)][::s], 1.55, 1.62, 'navy')
        uq(m, *sorted((s * 1.6, s * 3.0)), 0.6, 2.4, 1.603, 'navyD')
        cyl_y(m, s * (WT + 0.1), 1.6, 4.6, 1.52, 0.09, 'white', seg=6)
        m.cy((s * (WT + 0.1), 1.6, 1.52), 0.0, 0.09, 0.4, 'white', seg=6, rot=(90, 0, 0))
        m.bx(s * WT - 0.05, s * WT + 0.05, 2.0, 4.2, 1.44, 1.62, 'steelD', cull='')
    cols = []
    le_boxes(cols, [1.5, 2.8, 4.1, 5.4], w_le, w_te, 1.42, 1.64)
    make('Jet_Wings', m, ao, cols=cols)

    # ---- folded wings: the inner panels and the outer panels folded straight up at the hinge (x = 3.4)
    m = new(pal)
    XF = 3.4
    for s in (-1, 1):
        slab(m, [(s * WR, -1.8), (s * XF, w_le(XF)), (s * XF, w_te(XF)), (s * WR, 4.4)][::s], 1.45, 1.6, 'navy')
        slab(m, [(s * 0.7, -4.6), (s * 1.45, -1.4), (s * 1.45, 0.4), (s * 0.7, 0.4)][::s], 1.55, 1.62, 'navy')
        span = WT - XF
        pts = [(s * XF, w_le(XF), 1.6), (s * XF, w_te(XF), 1.6), (s * XF, w_te(WT), 1.6 + span), (s * XF, w_le(WT), 1.6 + span)]
        plate(m, pts, (-s * 0.12, 0.0, 0.0), 'navy')
        m.bx(s * XF - 0.08, s * XF + 0.08, w_le(XF) + 0.2, w_te(XF) - 0.2, 1.4, 1.75, 'steelD', cull='')
    cols = []
    le_boxes(cols, [1.5, 2.45, XF], w_le, w_te, 1.42, 1.64)
    for s in (-1, 1):
        cols.append(cb(s * (XF - 0.14), w_le(WT), 1.64, s * (XF + 0.1), w_te(WT), 1.6 + WT - XF))
    make('Jet_WingsFold', m, ao, cols=cols)

    # ---- the closed canopy
    m = new(pal)
    canopy(m)
    make('Jet_Canopy', m, ao)

    # ---- maintenance: the canopy raised on its hinge, access panels open on both sides, the boarding ladder,
    # the nose radome swung open to the right, red streamers on the covers
    m = new(pal)
    m.parent = rot_about_x(m, -2.3, 2.2, -38)
    canopy(m, frame_only=False)
    m.parent = Matrix.Identity(4)
    m.bx(-0.04, 0.04, -2.6, -2.3, 2.1, 2.9, 'steelD', cull='')
    for s in (-1, 1):
        x = s * 1.5
        plate(m, [(x, 0.4, 1.9), (x, 1.6, 1.9), (x + s * 0.55, 1.6, 2.35), (x + s * 0.55, 0.4, 2.35)], (0, 0, -0.04), 'navyL')
        plate(m, [(s * 0.86, 3.6, 1.95), (s * 0.86, 5.0, 1.95), (s * 1.1, 5.0, 2.7), (s * 1.1, 3.6, 2.7)], (-s * 0.04, 0, 0), 'navyL')
    # boarding ladder hooked on the left cockpit sill
    for dy in (-0.2, 0.2):
        m.bm_((-0.88, -3.6 + dy, 2.2), (-1.55, -3.6 + dy, 0.0), 0.05, 'yellow')
    for k in range(5):
        t = (k + 0.5) / 5
        m.bx(-0.88 - 0.67 * t - 0.12, -0.88 - 0.67 * t + 0.12, -3.82, -3.38, 2.2 * (1 - t) - 0.02, 2.2 * (1 - t) + 0.02, 'yellow', cull='')
    for (x, y, z) in ((1.65, 1.0, 2.0), (1.0, 4.3, 2.75), (-1.65, 1.0, 2.0)):
        m.bx(x - 0.02, x + 0.02, y - 0.04, y + 0.04, z - 0.6, z, 'fire', hull='none', cull='')
    make('Jet_Open', m, ao, cols=[cb(-1.62, -3.85, 0.0, -0.95, -3.35, 1.0)])


def stab_cols():
    out = []
    for s in (-1, 1):
        out.append(cb(s * 1.5, 6.6, 1.44, s * 3.6, 7.45, 1.62))
    return out


def canopy(m, frame_only=False):
    rings = [(-5.6, 0.0, 2.02, 0.0, 0.0), (-5.0, 0.0, 2.08, 0.36, 0.32), (-4.0, 0.0, 2.15, 0.48, 0.48), (-3.0, 0.0, 2.15, 0.47, 0.46), (-2.3, 0.0, 2.15, 0.36, 0.3)]
    loft(m, rings, lambda k, i, a: 'glassD' if math.sin(a) > -0.2 else 'navyD', seg=8, a0=math.pi / 8)
    m.bx(-0.48, 0.48, -4.35, -4.25, 2.1, 2.66, 'navyD', cull='b')
    poly(m, [(-0.18, -4.9, 2.42), (-0.08, -4.9, 2.42), (0.05, -4.3, 2.66), (-0.05, -4.3, 2.66)], 'glassL', (0, -0.4, 1))


# ================================================================ the light aircraft at the spawn (made-up "Petrel")
def build_plane(pal, ao):
    """A two-seat low-wing propeller trainer / liaison plane, nose -Y, the canopy swung up on its front hinge (open
    cockpit), a three-step boarding stair against the left wing root. Footprint [10, 10]."""
    m = new(pal)
    CZ = 1.2
    rings = [(-3.9, 0.0, CZ, 0.42, 0.42), (-3.4, 0.0, CZ + 0.02, 0.55, 0.56), (-2.0, 0.0, CZ + 0.05, 0.6, 0.64),
             (-0.2, 0.0, CZ + 0.05, 0.6, 0.62), (1.6, 0.0, CZ + 0.1, 0.46, 0.48), (3.3, 0.0, CZ + 0.3, 0.22, 0.26), (3.9, 0.0, CZ + 0.38, 0.08, 0.1)]

    def col(k, i, ang):
        if k == 0:
            return 'blue'
        sn = math.sin(ang)
        return 'blue' if -0.5 < sn < -0.1 else 'cream'
    loft(m, rings, col, seg=10, a0=0.0)
    # the cockpit opening (dark), the seats, the panel coaming, the stick
    uq(m, -0.44, 0.44, -1.6, 0.6, CZ + 0.66, 'black')
    for y in (-0.9, 0.2):
        m.bx(-0.26, 0.26, y, y + 0.36, CZ + 0.2, CZ + 0.62, 'seat', cull='b')
        m.bx(-0.26, 0.26, y + 0.36, y + 0.48, CZ + 0.2, CZ + 1.0, 'seat', cull='b')
    m.bx(-0.42, 0.42, -1.75, -1.55, CZ + 0.5, CZ + 0.85, 'dark', cull='b')
    # the canopy, swung up on its front hinge (open cockpit): a frame with clear glazing and glints
    M0 = m.parent
    m.parent = rot_about_x(m, -1.65, CZ + 0.72, 55)
    for s in (-1, 1):
        m.bm_((s * 0.44, -1.6, CZ + 0.7), (s * 0.44, 0.6, CZ + 0.7), 0.05, 'dark')
    for y in (-1.6, -0.5, 0.6):
        m.bm_((-0.44, y, CZ + 0.7), (-0.28, y, CZ + 1.08), 0.044, 'dark')
        m.bm_((0.28, y, CZ + 1.08), (0.44, y, CZ + 0.7), 0.044, 'dark')
        m.bm_((-0.28, y, CZ + 1.08), (0.28, y, CZ + 1.08), 0.036, 'dark')
    for s in (-1, 1):   # the glazing: side panes and the roof pane, both faces, a glint on each side
        for d in (0.0, -0.006):
            n = (s, 0, 0.42) if d == 0 else (-s, 0, -0.42)
            poly(m, [(s * (0.44 + d), -1.58, CZ + 0.72), (s * (0.44 + d), 0.58, CZ + 0.72), (s * (0.28 + d), 0.58, CZ + 1.06), (s * (0.28 + d), -1.58, CZ + 1.06)], 'glass', n)
        poly(m, [(s * 0.447, -1.3, CZ + 0.76), (s * 0.447, -0.95, CZ + 0.76), (s * 0.31, -0.7, CZ + 1.02), (s * 0.31, -1.05, CZ + 1.02)], 'glassL', (s, 0, 0.42))
    for d, n in ((0.0, (0, 0, 1)), (-0.006, (0, 0, -1))):
        poly(m, [(-0.28, -1.58, CZ + 1.06 + d), (0.28, -1.58, CZ + 1.06 + d), (0.28, 0.58, CZ + 1.06 + d), (-0.28, 0.58, CZ + 1.06 + d)], 'glass', n)
    m.parent = M0
    # the engine cowl, spinner, a three-blade propeller
    m.cy((0, -3.95, CZ), 0.2, 0.05, 0.45, 'fire', seg=10, rot=(90, 0, 0))
    for k in range(3):
        a = math.radians(90 + k * 120)
        m.bm_((0, -4.1, CZ), (math.cos(a) * 0.95, -4.15, CZ + math.sin(a) * 0.95), 0.09, 'dark')
    fq(m, -0.3, 0.3, -3.903, CZ - 0.3, CZ - 0.1, 'black')
    # the wings (low, slight taper and dihedral), orange tips, a black walkway on the left root
    for s in (-1, 1):
        plate(m, [(s * 0.5, -0.9, 0.62), (s * 4.8, -0.5, 0.82), (s * 4.8, 0.55, 0.82), (s * 0.5, 0.75, 0.62)][::s], (0, 0, 0.1), 'cream')
        plate(m, [(s * 4.8, -0.5, 0.82), (s * 4.95, -0.45, 0.83), (s * 4.95, 0.5, 0.83), (s * 4.8, 0.55, 0.82)][::s], (0, 0, 0.1), 'orange')
    poly(m, [(-0.62, -0.7, 0.735), (-1.45, -0.65, 0.745), (-1.45, 0.55, 0.745), (-0.62, 0.62, 0.735)], 'black', (0, 0, 1))
    # tail: fin and rudder, stabilizer
    plate(m, [(-0.04, 2.6, CZ + 0.45), (-0.04, 3.95, CZ + 0.4), (-0.04, 3.95, CZ + 1.7), (-0.04, 3.3, CZ + 1.7)], (0.08, 0, 0), 'cream')
    for s in (-1, 1):
        plate(m, [(s * 0.15, 3.0, CZ + 0.42), (s * 1.7, 3.4, CZ + 0.42), (s * 1.7, 3.85, CZ + 0.42), (s * 0.15, 3.95, CZ + 0.42)][::s], (0, 0, 0.06), 'cream')
    text(m, 'PELAGIC', 0.05, 3.45, CZ + 0.95, 0.2, 'blue', face='x+')
    text(m, 'PELAGIC', -0.05, 3.45, CZ + 0.95, 0.2, 'blue', face='x-')
    for s in (-1, 1):
        text(m, 'PB-07', s * 0.61, 1.5 * s, CZ - 0.1, 0.26, 'blueD', face='x+' if s > 0 else 'x-')
    # fixed tricycle gear with spats
    for (x, y, r) in ((0.0, -3.0, 0.2), (-1.1, 0.1, 0.25), (1.1, 0.1, 0.25)):
        m.cy((x, y, r), 0.04, 0.04, 0.55 if x else 0.8, 'steel', seg=5)
        wheel(m, x, y, r, r, 0.12, c='tire', hub='steel', seg=8)
        m.bx(x - 0.1, x + 0.1, y - 0.35, y + 0.3, r - 0.02, r + 0.26, 'cream', cull='b')
    # the boarding stair: four steps on a wheeled frame rising toward the fuselage just aft of the wing root, hand
    # rails both sides, its top step by the rear cockpit
    X0, X1, Y0, Y1 = -2.26, -0.66, 0.85, 1.65
    for k in range(4):
        z = 0.3 * (k + 1)
        m.bx(X0 + k * 0.4, X1, Y0, Y1, z - 0.05, z, 'yellow', cull='')
        uq(m, X0 + k * 0.4 + 0.02, X0 + k * 0.4 + 0.1, Y0 + 0.03, Y1 - 0.03, z + 0.003, 'black')
    for y in (Y0 + 0.06, Y1 - 0.06):
        m.prism([(y - 0.03, 0.0), (y + 0.03, 0.0), (y + 0.03, 1.15), (y - 0.03, 1.15)], X1 - 0.08, X1 - 0.02, ['steelD'])
        m.bm_((X0 + 0.04, y, 0.12), (X1 - 0.12, y, 1.1), 0.05, 'steelD')
        m.bm_((X0 + 0.06, y, 0.95), (X1 - 0.05, y, 2.15), 0.045, 'steel')
        m.bm_((X0 + 0.06, y, 0.12), (X0 + 0.06, y, 0.97), 0.035, 'steel')
        for x in (X0 + 0.1, X1 - 0.12):
            m.cy((x, y, 0.0), 0.06, 0.06, 0.1, 'black', seg=6)
    cols = [cb(-0.62, -3.9, 0.55, 0.62, 3.9, 1.9), cb(-4.8, -0.5, 0.62, -0.62, 0.55, 0.85), cb(0.62, -0.5, 0.62, 4.8, 0.55, 0.85),
            cb(-1.7, 3.4, CZ + 0.4, 1.7, 3.85, CZ + 0.5), cb(X0, Y0, 0.0, X1, Y1, 1.2), cb(-0.12, -3.4, 0.0, 0.12, -2.6, 0.55)]
    make('Plane', m, ao, cols=cols)


# ================================================================ the helicopter (made-up "Gannet"), nose -Y
def build_heli(pal, ao):
    m = new(pal)
    rings = [(-6.2, 0.0, 1.55, 0.0, 0.0), (-5.9, 0.0, 1.5, 0.55, 0.6), (-4.8, 0.0, 1.62, 1.05, 1.02), (-2.0, 0.0, 1.8, 1.18, 1.25),
             (1.4, 0.0, 1.85, 1.12, 1.2), (2.6, 0.0, 2.05, 0.6, 0.6), (6.6, 0.0, 2.35, 0.26, 0.28), (7.2, 0.0, 2.4, 0.22, 0.24)]

    def col(k, i, ang):
        return 'navyL' if math.sin(ang) < -0.6 else 'navy'
    loft(m, rings, col, seg=8, a0=math.pi / 8)
    # cockpit glazing, the cabin door (slid open), windows
    for s in (-1, 1):
        x = s * 1.08
        poly(m, [(x, -5.2, 1.6), (x, -3.8, 1.6), (x * 1.02, -3.8, 2.5), (x * 0.9, -5.0, 2.4)], 'glassD', (s, 0, 0))
        glint_x(m, x + s * 0.01, -4.9, 1.75, 0.5, w=0.12, face=s)
    poly(m, [(-0.7, -5.75, 1.75), (0.7, -5.75, 1.75), (0.6, -5.2, 2.45), (-0.6, -5.2, 2.45)], 'glassD', (0, -1, 0.6))
    m.bx(1.16, 1.2, -2.8, -0.9, 0.95, 2.55, 'dark', hull='none', cull='tbfkl')
    m.bx(1.24, 1.32, -1.0, 0.9, 0.95, 2.6, 'navy', cull='')
    window_band_x(m, 0.0, 0.8, -1.2, 1.85, 2.4, every=0.8, face=-1)
    # engines and the rotor mast on the cabin roof, the main rotor (four blades), the hub
    m.bx(-0.75, 0.75, -2.6, 1.6, 2.95, 3.55, 'navy', cull='b')
    for s in (-1, 1):
        cyl_y(m, s * 0.5, -2.9, 1.2, 3.25, 0.3, 'navyD', seg=8)
        vdisc(m, s * 0.5, -2.903, 3.25, 0.22, 'black', seg=8)
    m.cy((0, -0.6, 3.55), 0.22, 0.18, 0.6, 'steelD', seg=8)
    m.cy((0, -0.6, 4.15), 0.38, 0.38, 0.16, 'steel', seg=8)
    for k in range(4):
        a = math.radians(45 + k * 90)
        ca, sa = math.cos(a), math.sin(a)
        p0, p1 = (0.3 * ca, -0.6 + 0.3 * sa), (6.4 * ca, -0.6 + 6.4 * sa)
        nx, ny = -sa * 0.24, ca * 0.24
        plate(m, [(p0[0] - nx, p0[1] - ny, 4.22), (p1[0] - nx, p1[1] - ny, 4.18), (p1[0] + nx, p1[1] + ny, 4.18), (p0[0] + nx, p0[1] + ny, 4.22)], (0, 0, 0.06), 'dark')
    # tail fin and the tail rotor (right side), the horizontal stabilizer
    plate(m, [(-0.06, 6.0, 2.4), (-0.06, 7.2, 2.5), (-0.06, 7.45, 4.0), (-0.06, 6.9, 4.0)], (0.12, 0, 0), 'navy')
    m.cy((0.06, 7.0, 3.6), 0.12, 0.12, 0.3, 'steelD', seg=6, rot=(0, 90, 0))
    for k in range(4):
        a = math.radians(k * 90 + 20)
        m.bm_((0.37 + 0.007 * k, 7.0, 3.6), (0.37 + 0.007 * k, 7.0 + math.cos(a) * 1.2, 3.6 + math.sin(a) * 1.2), 0.1, 'dark')
    for s in (-1, 1):
        plate(m, [(s * 0.2, 5.2, 2.25), (s * 1.6, 5.4, 2.25), (s * 1.6, 5.9, 2.25), (s * 0.2, 6.0, 2.25)][::s], (0, 0, 0.06), 'navy')
    # landing gear: sponsons with wheels, a tail wheel; a sensor turret under the nose
    for s in (-1, 1):
        x = s * 1.25
        m.bx(*sorted((s * 0.9, s * 1.55)), -1.6, 0.4, 0.7, 1.15, 'navy', cull='')
        m.cy((s * 1.45, -0.6, 0.32), 0.05, 0.05, 0.5, 'steel', seg=6)
        wheel(m, s * 1.45, -0.6, 0.32, 0.32, 0.18, c='tire', hub='steel', seg=8)
    m.cy((0, -4.8, 0.3), 0.05, 0.05, 0.6, 'steel', seg=6)
    wheel(m, 0.0, -4.8, 0.25, 0.25, 0.14, c='tire', hub='steel', seg=8)
    m.sp((0, -5.4, 0.85), 0.25, 'dark', seg=(8, 5))
    for s in (-1, 1):
        text(m, 'RESCUE 21', s * 1.0, 2.0 * s, 2.0, 0.26, 'orange', face='x+' if s > 0 else 'x-')
    cols = [cb(-1.15, -5.6, 0.7, 1.15, 1.6, 3.0), cb(-1.55, -1.6, 0.7, 1.55, 0.4, 1.15), cb(-0.75, -2.6, 3.0, 0.75, 1.6, 3.55),
            cb(-0.45, 1.6, 1.3, 0.45, 7.3, 2.7)]
    make('Helicopter', m, ao, cols=cols)


# ================================================================ deck vehicles
def build_tractor(pal, ao):
    """deck tow tractor [2, 4]: a low yellow body, the driver's seat at the back under a roll bar, the tow bar
    lying out in front (toward -Y)"""
    m = new(pal)
    m.bx(-0.75, 0.75, -1.0, 1.5, 0.22, 0.78, 'yellow', cull='b')
    m.bx(-0.7, 0.7, -0.95, 0.4, 0.78, 0.92, 'yellowD', cull='b')
    hazard(m, -0.75, 0.75, -1.003, 0.25, 0.55, 6)
    for (x, y) in ((-0.72, -0.6), (0.72, -0.6), (-0.72, 1.05), (0.72, 1.05)):
        wheel(m, x, y, 0.24, 0.24, 0.18, c='tire', hub='steelD', seg=8)
    m.bx(-0.35, 0.35, 0.7, 1.2, 0.78, 1.05, 'seat', cull='b')
    m.bx(-0.35, 0.35, 1.15, 1.3, 1.05, 1.4, 'seat', cull='b')
    m.cy((0, 0.45, 0.92), 0.03, 0.03, 0.3, 'black', seg=4)
    m.cy((0, 0.42, 1.2), 0.17, 0.17, 0.04, 'black', seg=10, rot=(-60, 0, 0))
    for s in (-1, 1):
        m.bm_((s * 0.66, 1.45, 0.78), (s * 0.66, 1.45, 1.9), 0.07, 'black')
    m.bm_((-0.7, 1.45, 1.94), (0.7, 1.45, 1.94), 0.09, 'black')
    m.cy((0.5, 1.45, 1.9), 0.07, 0.07, 0.12, 'beacon', seg=6)
    for s in (-1, 1):
        m.bm_((s * 0.25, -1.0, 0.32), (0.0, -2.05, 0.12), 0.07, 'steelD')
    m.cy((0, -2.05, 0.04), 0.09, 0.09, 0.12, 'black', seg=6)
    make('Tractor', m, ao, cols=[cb(-0.75, -1.0, 0.0, 0.75, 1.5, 1.05)])


def bomb(m, x, y0, y1, z, r, c='olive', band='yellow'):
    cyl_y(m, x, y0 + 0.5, y1 - 0.25, z, r, c, seg=6)
    m.cy((x, y0 + 0.5, z), r, 0.04, 0.5, c, seg=6, rot=(90, 0, 0), caps=False)
    cyl_y(m, x, y1 - 0.25, y1, z, r, c, seg=6, r1=r * 0.6)
    m.bx(x - r - 0.003, x + r + 0.003, y0 + 0.8, y0 + 0.9, z - 0.02, z + 0.02, band, hull='none', cull='')
    m.bx(x - r * 1.4, x + r * 1.4, y1 - 0.37, y1 - 0.02, z - 0.012, z + 0.012, c, cull='')
    m.bx(x - 0.01, x + 0.01, y1 - 0.36, y1 - 0.03, z - r * 1.4, z + r * 1.4, c, cull='')


def build_carts(pal, ao):
    # bomb cart [2, 3]: a low steel frame on four casters, two bombs strapped on cradles
    m = new(pal)
    m.bx(-0.7, 0.7, -1.3, 1.3, 0.28, 0.4, 'steelD', cull='')
    for (x, y) in ((-0.6, -1.15), (0.6, -1.15), (-0.6, 1.15), (0.6, 1.15)):
        m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.12, 0.28, 'steelD', cull='')
        wheel(m, x, y, 0.12, 0.12, 0.08, c='tire', hub='steel', seg=6)
    for y in (-0.8, 0.8):
        m.bx(-0.65, 0.65, y - 0.06, y + 0.06, 0.4, 0.56, 'yellow', cull='b')
    bomb(m, -0.34, -1.4, 1.35, 0.78, 0.23)
    bomb(m, 0.34, -1.35, 1.4, 0.78, 0.23)
    m.bm_((0, -1.3, 0.34), (0, -1.75, 0.3), 0.06, 'yellow')
    make('BombCart', m, ao, cols=[cb(-0.7, -1.4, 0.0, 0.7, 1.4, 1.05)])
    # missile cart [2, 3]: a rack with three white missiles (fins, seeker noses)
    m = new(pal)
    m.bx(-0.7, 0.7, -1.32, 1.32, 0.28, 0.4, 'steelD', cull='')
    for (x, y) in ((-0.6, -1.15), (0.6, -1.15), (-0.6, 1.15), (0.6, 1.15)):
        m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.12, 0.28, 'steelD', cull='')
        wheel(m, x, y, 0.12, 0.12, 0.08, c='tire', hub='steel', seg=6)
    for y in (-0.9, 0.0, 0.9):
        m.bx(-0.62, 0.62, y - 0.05, y + 0.05, 0.4, 1.0, 'blueD', cull='b')
    for (x, z) in ((-0.38, 0.62), (0.38, 0.62), (0.0, 1.08)):
        cyl_y(m, x, -1.25, 1.36, z, 0.1, 'white', seg=6)
        m.cy((x, -1.25, z), 0.1, 0.0, 0.3, 'white', seg=6, rot=(90, 0, 0))
        m.bx(x - 0.003 - 0.1, x + 0.1 + 0.003, -0.3, -0.24, z - 0.02, z + 0.02, 'gold', hull='none', cull='')
        m.bx(x - 0.24, x + 0.24, 1.0, 1.28, z - 0.01, z + 0.01, 'white', cull='')
        m.bx(x - 0.008, x + 0.008, 1.01, 1.27, z - 0.24, z + 0.24, 'white', cull='')
    make('MissileCart', m, ao, cols=[cb(-0.7, -1.4, 0.0, 0.7, 1.4, 1.2)])


def build_tender(pal, ao):
    """crash tender [3, 7]: a big red fire and rescue truck, cab in front (-Y), the roof turret, roller shutters,
    six wheels"""
    m = new(pal)
    m.bx(-1.2, 1.2, -3.4, -1.4, 0.55, 2.7, 'fire', cull='b')
    m.bx(-1.15, 1.15, -3.45, -3.4, 1.6, 2.5, 'glassD', hull='none', cull='tbk')
    window_band(m, -1.05, 1.05, -3.46, 1.65, 2.45, every=1.05)
    window_band_x(m, -3.2, -2.2, 1.203, 1.65, 2.4, every=1.0, face=1)
    window_band_x(m, -3.2, -2.2, -1.203, 1.65, 2.4, every=1.0, face=-1)
    m.bx(-1.25, 1.25, -1.4, 3.4, 0.55, 2.85, 'fire', cull='b')
    for s in (-1, 1):
        x = s * 1.253
        for (y0, y1) in ((-1.1, 0.6), (1.0, 2.9)):
            m.bx(*sorted((x, x + s * 0.003)), y0, y1, 1.0, 2.55, 'steel', hull='none', cull='tbfk' + ('l' if s > 0 else 'r'))
        m.bx(*sorted((x + s * 0.004, x + s * 0.006)), -3.3, 3.3, 0.7, 0.95, 'yellow', hull='none', cull='tbfk' + ('l' if s > 0 else 'r'))
        text(m, 'PELAGIC FIRE', s * 1.204, -2.4 * s, 1.0, 0.16, 'white', face='x+' if s > 0 else 'x-')
    for y in (-2.6, 1.2, 2.6):
        for s in (-1, 1):
            wheel(m, s * 1.05, y, 0.55, 0.55, 0.36, c='tire', hub='steel', seg=10)
    m.cy((0.0, -1.0, 2.85), 0.3, 0.3, 0.25, 'steelD', seg=8)
    m.bm_((0, -1.0, 3.2), (0, -2.6, 3.35), 0.14, 'steel')
    m.bx(-0.9, 0.9, -3.3, -3.05, 2.7, 2.85, 'beacon', cull='')
    m.bx(-1.25, 1.25, 3.4, 3.43, 0.6, 2.8, 'steelD', hull='none', cull='tbflr')
    hazard(m, -1.25, 1.25, -3.403, 0.55, 0.85, 8)
    make('Tender', m, ao, cols=[cb(-1.25, -3.45, 0.0, 1.25, 3.43, 2.85)])


# ================================================================ escort warships (backdrop, far out)
def ship_hull(m, L, B, D):
    """a sharp-bowed hull along Y (bow at -L/2): sides flare, a transom stern; deck at z = D"""
    h = L / 2
    pts_deck = [(0, -h, D + 1.5), (B * 0.32, -h + L * 0.12, D + 0.8), (B / 2, -h + L * 0.35, D), (B / 2, h - 2, D), (B * 0.42, h, D),
                (-B * 0.42, h, D), (-B / 2, h - 2, D), (-B / 2, -h + L * 0.35, D), (-B * 0.32, -h + L * 0.12, D + 0.8)]
    pts_wl = [(0, -h + 6, 0), (B * 0.28, -h + L * 0.14, 0), (B * 0.46, -h + L * 0.35, 0), (B * 0.46, h - 2, 0), (B * 0.38, h, 0.5),
              (-B * 0.38, h, 0.5), (-B * 0.46, h - 2, 0), (-B * 0.46, -h + L * 0.35, 0), (-B * 0.28, -h + L * 0.14, 0)]
    n = len(pts_deck)
    verts = pts_deck + pts_wl
    faces = [tuple(range(n))[::-1]]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    skin(m, (verts, faces), lambda f: 'hullD' if f.normal.z > 0.9 else 'hull')
    # the boot top at the waterline
    for s in (-1, 1):
        m.bx(*sorted((s * B * 0.455, s * B * 0.47)), -h + L * 0.36, h - 2.2, 0.0, 1.2, 'boot', hull='none', cull='tb' + ('l' if s > 0 else 'r'))


def build_ships(pal, ao):
    # frigate, ~118 m: bow gun, a VLS block, the angular superstructure with its mast, funnel, helo hangar and deck
    m = new(pal)
    L, B, D = 118.0, 15.0, 7.0
    ship_hull(m, L, B, D)
    m.bx(-5.0, 5.0, -28.0, 10.0, D, D + 6.0, 'hull', cull='b')
    m.bx(-4.2, 4.2, -26.0, -14.0, D + 6.0, D + 11.0, 'hull', cull='b')
    m.bx(-3.6, 3.6, -26.5, -25.0, D + 9.0, D + 10.6, 'glassD', hull='none', cull='tb')
    hullpts = [(-2.4, -20.0, D + 11.0), (2.4, -20.0, D + 11.0), (1.6, -18.0, D + 24.0), (-1.6, -18.0, D + 24.0)]
    plate(m, hullpts, (0, 3.0, 0), 'hullD')
    m.cy((0, -18.5, D + 24.0), 0.3, 0.2, 8.0, 'steelD', seg=5)
    m.bx(-3.0, 3.0, -5.0, 3.0, D + 6.0, D + 12.0, 'hullD', cull='b')
    m.bx(-6.0, 6.0, 10.0, 26.0, D, D + 6.5, 'hull', cull='b')
    m.cy((0, -42.0, D + 0.8), 2.2, 2.0, 1.6, 'hull', seg=8)
    m.bm_((0, -42.0, D + 1.8), (0, -48.5, D + 2.1), 0.45, 'steelD')
    m.bx(-3.5, 3.5, -36.0, -31.0, D, D + 1.2, 'hullD', cull='b')
    m.bx(-7.0, 7.0, 26.0, 56.0, D + 0.01, D + 0.05, 'deck2', hull='none', cull='b')
    for s in (-1, 1):
        text(m, '417', s * 7.48, -36.0 * s, D - 4.2, 3.2, 'white', face='x+' if s > 0 else 'x-')
    make('Backdrop_Frigate', m, False)
    # destroyer, ~150 m: two gun mounts, a big blocky superstructure with flat radar panels, two funnels
    m = new(pal)
    L, B, D = 150.0, 19.0, 8.5
    ship_hull(m, L, B, D)
    m.bx(-6.5, 6.5, -32.0, 18.0, D, D + 7.0, 'hull', cull='b')
    pts = [(-5.6, -30.0, D + 7.0), (5.6, -30.0, D + 7.0), (4.0, -27.0, D + 19.0), (-4.0, -27.0, D + 19.0)]
    plate(m, pts, (0, 12.0, 0), 'hull')
    for s in (-1, 1):
        poly(m, [(s * 5.0, -26.5, D + 10.0), (s * 5.0, -22.5, D + 10.0), (s * 4.3, -22.5, D + 15.5), (s * 4.3, -26.5, D + 15.5)], 'navyD', (s, 0, 0.12))
    m.bx(-4.6, 4.6, -30.6, -29.9, D + 12.5, D + 14.0, 'glassD', hull='none', cull='tb')
    m.cy((0, -22.0, D + 19.0), 0.5, 0.25, 14.0, 'steelD', seg=5)
    m.bm_((-6.0, -22.0, D + 28.0), (6.0, -22.0, D + 28.0), 0.4, 'steelD')
    for y in (-2.0, 10.0):
        m.bx(-2.6, 2.6, y - 3.0, y + 3.0, D + 7.0, D + 13.0, 'hullD', cull='b')
        m.bx(-2.2, 2.2, y - 2.6, y + 2.6, D + 13.0, D + 13.6, 'black', cull='b')
    for (y, r) in ((-55.0, 2.4), (44.0, 2.2)):
        m.cy((0, y, D + 0.9 if y < 0 else D), r, r * 0.9, 1.7, 'hull', seg=8)
        m.bm_((0, y, D + 2.0), (0, y - 7.5 if y < 0 else y + 7.5, D + 2.3), 0.5, 'steelD')
    m.bx(-4.0, 4.0, -46.0, -38.0, D, D + 1.0, 'hullD', cull='b')
    m.bx(-7.0, 7.0, 18.0, 36.0, D, D + 6.0, 'hull', cull='b')
    for s in (-1, 1):
        text(m, '82', s * 9.48, -48.0 * s, D - 5.5, 4.0, 'white', face='x+' if s > 0 else 'x-')
    make('Backdrop_Destroyer', m, False)


def build_craft(pal, ao):
    build_jet(pal, ao)
    build_plane(pal, ao)
    build_heli(pal, ao)
    build_tractor(pal, ao)
    build_carts(pal, ao)
    build_tender(pal, ao)
    build_ships(pal, ao)
