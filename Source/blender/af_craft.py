"""INKBOLT kit-airfield7 aircraft and vehicles: the made-up "Kestrel F7" fighter (body + wings, combined per symbol with
a closed canopy under its covers or the raised canopy with the boarding ladder and open panels, theme `with`), the
made-up "Hauler" four-turboprop transport with its rear ramp down and a walk-in hold, the fuel bowser, the crash
tender, the runway control caravan, the aircraft tug and the munitions trailer. All made up. Noses / fronts point to
Blender -Y (the piece's front). Conventions: af_base.py."""
import math

from mathutils import Matrix, Vector

from af_base import *  # noqa: F401,F403
from af_base import new, make, text, hazard, plate, box_lines


# ---------------------------------------------------------------- generic lofts
def loft_pts(m, rings, c_of, cap0=None, cap1=None, hull='full'):
    """a closed body through rings of points (each ring a list of xyz of the same length, or one point = a tip);
    c_of(k, i, p) -> palette name for the face between ring k and k+1 at ring point i (p = its centre)"""
    bm = m.bm
    P = m.parent
    vr = [[bm.verts.new(P @ Vector(p)) for p in r] for r in rings]
    faces = []
    for k in range(len(vr) - 1):
        a, b = vr[k], vr[k + 1]
        n = max(len(a), len(b))
        for i in range(n):
            j = (i + 1) % n
            if len(a) == 1:
                f = bm.faces.new((a[0], b[i], b[j]))
                ctr = rings[k + 1][i]
            elif len(b) == 1:
                f = bm.faces.new((a[i], b[0], a[j]))
                ctr = rings[k][i]
            else:
                f = bm.faces.new((a[i], b[i], b[j], a[j]))
                ctr = rings[k][i]
            f.material_index = m.pal.index(c_of(k, i, ctr))
            faces.append(f)
    for end, c in ((vr[0], cap0), (vr[-1], cap1)):
        if len(end) > 1:
            f = bm.faces.new(end)
            f.material_index = m.pal.index(c or c_of(0, 0, (0, 0, 0)))
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return faces


def sel(A, B, zc, t, y, cx=0.0):
    """a point of a p=4 superellipse (rounded box section) of half width A, half height B, centre (cx, zc), at angle t"""
    c, s = math.cos(t), math.sin(t)
    return (cx + A * math.copysign(abs(c) ** 0.5, c), y, zc + B * math.copysign(abs(s) ** 0.5, s))


def sel_ring(A, B, zc, y, n=16, cx=0.0):
    return [sel(A, B, zc, 2 * math.pi * i / n, y, cx) for i in range(n)]


def t_at(B, zc, z):
    """the angle (below the horizontal, right side) where the superellipse reaches height z"""
    q = max(-1.0, min(1.0, (z - zc) / B))
    return -math.asin(abs(q) ** 2) if q < 0 else math.asin(q ** 2)


def utube(m, rings, n, c_out, c_in, c_cut):
    """an open-bottomed shell (the hold and the upswept tail): rings = [(y, A, B, zc, cut)] -- the outer section and
    the inner one (0.15 m in) from the cut height on the right over the top to the cut height on the left"""
    T = 0.15
    O, I = [], []
    for (y, A, B, zc, cut) in rings:
        ta, ti = t_at(B, zc, cut), t_at(B - T, zc, cut)
        O.append([sel(A, B, zc, ta + (math.pi - 2 * ta) * i / (n - 1), y) for i in range(n)])
        I.append([sel(A - T, B - T, zc, ti + (math.pi - 2 * ti) * i / (n - 1), y) for i in range(n)])
    verts, faces, cols = [], [], []
    for k in range(len(rings)):
        verts += O[k] + I[k]
    R = 2 * n

    def o(k, i):
        return k * R + i

    def ii(k, i):
        return k * R + n + i
    for k in range(len(rings) - 1):
        for i in range(n - 1):
            faces.append((o(k, i), o(k, i + 1), o(k + 1, i + 1), o(k + 1, i)))
            cols.append(c_out(k, i))
            faces.append((ii(k, i), ii(k + 1, i), ii(k + 1, i + 1), ii(k, i + 1)))
            cols.append(c_in)
        for i in (0, n - 1):   # the cut edges along the bottom of the side walls
            faces.append((o(k, i), o(k + 1, i), ii(k + 1, i), ii(k, i)))
            cols.append(c_cut)
    L = len(rings) - 1
    for k in (0, L):           # the U-shaped end faces
        for i in range(n - 1):
            faces.append((o(k, i), ii(k, i), ii(k, i + 1), o(k, i + 1)))
            cols.append(c_cut)
    fs = skin(m, (verts, faces), c_cut)
    for f, c in zip(fs, cols):
        f.material_index = m.pal.index(c)
    return O, I


def prop(m, x, y, z, r=1.9, a0=0.3):
    """a four-blade propeller (spinner and flat blades) in the plane y facing -Y"""
    m.cy((x, y - 0.55, z), 0.0, 0.34, 0.55, 'odD', seg=10, rot=(-90, 0, 0))
    m.cy((x, y - 0.02, z), 0.34, 0.34, 0.2, 'odD', seg=10, rot=(-90, 0, 0))
    for k in range(4):
        a = a0 + k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        px, pz = -sa, ca
        pts = [(x + ca * 0.3 + px * 0.16, y - 0.3, z + sa * 0.3 + pz * 0.16), (x + ca * r + px * 0.1, y - 0.3, z + sa * r + pz * 0.1),
               (x + ca * r - px * 0.1, y - 0.3, z + sa * r - pz * 0.1), (x + ca * 0.3 - px * 0.16, y - 0.3, z + sa * 0.3 - pz * 0.16)]
        plate(m, pts, (0, 0.05, 0), 'black')
        tip = [(x + ca * (r - 0.25) + px * 0.11, y - 0.303, z + sa * (r - 0.25) + pz * 0.11), (x + ca * (r - 0.01) + px * 0.1, y - 0.303, z + sa * (r - 0.01) + pz * 0.1),
               (x + ca * (r - 0.01) - px * 0.1, y - 0.303, z + sa * (r - 0.01) - pz * 0.1), (x + ca * (r - 0.25) - px * 0.11, y - 0.303, z + sa * (r - 0.25) - pz * 0.11)]
        poly(m, tip, 'yellow', (0, -1, 0))


def roundel(m, x, y, z, r, face):
    """the made-up Airfield 7 wing roundel: a dark ring, a sand field and a red bar, on a plane at x"""
    xdisc(m, x + face * 0.003, y, z, r, 'jetD', seg=12, face=face)
    xdisc(m, x + face * 0.006, y, z, r * 0.72, 'sandL', seg=12, face=face)
    (rq if face > 0 else lq)(m, x + face * 0.009, y - r * 0.55, y + r * 0.55, z - r * 0.14, z + r * 0.14, 'redD')


# ================================================================ the fighter (made-up "Kestrel F7"), nose -Y
FUS = [(-7.8, 0.0, 1.85, 0.0, 0.0), (-7.2, 0.0, 1.86, 0.22, 0.22), (-6.0, 0.0, 1.9, 0.45, 0.45), (-4.6, 0.0, 1.95, 0.6, 0.62),
       (-2.8, 0.0, 1.92, 0.72, 0.7), (-0.5, 0.0, 1.84, 0.8, 0.66), (2.5, 0.0, 1.8, 0.8, 0.62), (5.5, 0.0, 1.8, 0.68, 0.56),
       (7.0, 0.0, 1.8, 0.56, 0.5)]
WR, WT = 0.75, 4.8          # wing root / tip half span
W_TE = 6.2


def w_le(x):
    return -2.2 + (x - WR) * (7.0 / (WT - WR))


def le_boxes(cols, xs, z0, z1):
    for xa, xb in zip(xs, xs[1:]):
        for s in (-1, 1):
            a, b = sorted((s * xa, s * xb))
            cols.append(cb(a, w_le(xb), z0, b, W_TE, z1))


def canopy(m):
    rings = [(-5.2, 0.0, 2.25, 0.0, 0.0), (-4.7, 0.0, 2.32, 0.34, 0.3), (-3.9, 0.0, 2.4, 0.5, 0.5), (-3.0, 0.0, 2.38, 0.5, 0.46), (-2.4, 0.0, 2.3, 0.4, 0.32)]
    loft(m, rings, lambda k, i, a: 'glassD' if math.sin(a) > -0.25 else 'jetD', seg=8, a0=math.pi / 8)
    m.bx(-0.5, 0.5, -4.45, -4.35, 2.2, 2.82, 'jetD', cull='b')
    poly(m, [(-0.2, -4.95, 2.48), (-0.1, -4.95, 2.48), (0.04, -4.2, 2.86), (-0.06, -4.2, 2.86)], 'glassL', (0, -0.4, 1))


def build_fighter(pal, ao):
    m = new(pal)

    def col(k, i, ang):
        if math.sin(ang) < -0.35:
            return 'belly'
        if k <= 1:
            return 'jetD'
        return ('camoA', 'camoB', 'camoC')[(k + i) % 3] if (k * 3 + i) % 4 else 'camoA'
    loft(m, FUS, col, seg=8, a0=math.pi / 8)
    # the chin intake, its splitter and dark mouth; the dorsal spine; the nozzle
    m.bx(-0.62, 0.62, -3.6, 0.6, 0.95, 1.5, 'belly', cull='')
    fq(m, -0.56, 0.56, -3.603, 1.0, 1.45, 'black')
    m.bx(-0.66, 0.66, -3.75, -3.6, 1.45, 1.52, 'jetD', cull='')
    m.bx(-0.28, 0.28, -2.4, 6.6, 2.4, 2.58, 'camoB', cull='b')
    cyl_y(m, 0.0, 7.0, 7.75, 1.8, 0.5, 'steelD', seg=10, r1=0.44)
    vdisc(m, 0.0, 7.753, 1.8, 0.36, 'black', seg=10, face=1)
    # the delta wing (inner and outer panels in two camouflage colours), canards
    XS = 2.6
    for s in (-1, 1):
        slab(m, [(s * WR, -2.2), (s * XS, w_le(XS)), (s * XS, W_TE), (s * WR, W_TE)][::s], 1.6, 1.7, 'camoA')
        slab(m, [(s * XS, w_le(XS)), (s * WT, w_le(WT)), (s * WT, W_TE), (s * XS, W_TE)][::s], 1.6, 1.69, 'camoB')
        uq(m, *sorted((s * 1.2, s * 2.2)), 2.0, 4.6, 1.703, 'camoC')
        dq(m, *sorted((s * 1.0, s * 4.6)), 3.0, 6.0, 1.597, 'belly')
        slab(m, [(s * 0.7, -4.4), (s * 2.0, -3.3), (s * 2.0, -2.9), (s * 0.7, -2.9)][::s], 2.0, 2.06, 'camoB')
        # wingtip rail and missile, underwing tank on its pylon
        cyl_y(m, s * (WT + 0.08), 3.4, 6.4, 1.66, 0.075, 'white2', seg=6)
        m.cy((s * (WT + 0.08), 3.4, 1.66), 0.0, 0.075, 0.35, 'white2', seg=6, rot=(90, 0, 0))
        m.bx(s * (WT + 0.08) - 0.01, s * (WT + 0.08) + 0.01, 5.9, 6.3, 1.48, 1.84, 'white2', hull='none', cull='')
        cyl_y(m, s * 2.3, -0.6, 2.4, 1.12, 0.25, 'camoC', seg=8)
        m.cy((s * 2.3, -0.6, 1.12), 0.0, 0.25, 0.8, 'camoC', seg=8, rot=(90, 0, 0))
        m.cy((s * 2.3, 2.4, 1.12), 0.25, 0.08, 0.5, 'camoC', seg=8, rot=(-90, 0, 0))
        m.bx(s * 2.3 - 0.05, s * 2.3 + 0.05, 0.2, 1.6, 1.3, 1.6, 'jetD', cull='')
        # main gear: strut, wheel, door
        xg = s * 1.35
        m.cy((xg, 2.2, 0.4), 0.06, 0.06, 0.9, 'steel', seg=6)
        wheel(m, xg, 2.2, 0.4, 0.4, 0.24, c='tire', hub='steel', seg=10)
        m.bx(xg - s * 0.3 - 0.015, xg - s * 0.3 + 0.015, 1.6, 2.8, 0.55, 1.2, 'belly', cull='')
        roundel(m, s * 0.62, -1.6, 1.22, 0.22, s)
    # nose gear, pitot probe, the tail fin with its markings
    m.cy((0.0, -5.2, 0.32), 0.05, 0.05, 1.2, 'steel', seg=6)
    wheel(m, 0.0, -5.2, 0.32, 0.32, 0.18, c='tire', hub='steel', seg=10)
    m.bx(-0.015, 0.015, -5.9, -4.6, 0.75, 1.3, 'belly', cull='')
    cyl_y(m, 0.0, -8.6, -7.6, 1.85, 0.03, 'steelD', seg=5)
    plate(m, [(-0.07, 3.6, 2.4), (-0.07, 7.0, 2.4), (-0.07, 7.45, 5.1), (-0.07, 6.3, 5.1)], (0.14, 0, 0), 'camoB')
    for s in (-1, 1):
        x = s * 0.074
        text(m, 'AF7', x, 6.2, 3.5, 0.42, 'jetD', face='x+' if s > 0 else 'x-', font='cond')
        text(m, '07', x, 6.55, 2.75, 0.35, 'black', face='x+' if s > 0 else 'x-', font='cond')
        text(m, '714', s * 0.47, -6.0, 1.75, 0.22, 'black', face='x+' if s > 0 else 'x-', font='cond')
    m.bx(-0.05, 0.05, 7.1, 7.5, 4.95, 5.12, 'lampR', cull='')
    make('Fighter', m, ao, cols=[cb(-0.45, -7.3, 1.4, 0.45, -4.6, 2.35), cb(-0.8, -4.6, 0.95, 0.8, 7.75, 2.6), cb(-0.08, 4.4, 2.6, 0.08, 7.3, 4.9),
                                 cb(1.15, 1.95, 0.0, 1.55, 2.45, 0.95), cb(-1.55, 1.95, 0.0, -1.15, 2.45, 0.95),
                                 cb(2.05, -1.4, 0.87, 2.55, 2.9, 1.4), cb(-2.55, -1.4, 0.87, -2.05, 2.9, 1.4)]
         + [c for c in _wing_cols()])

    # ---- the closed canopy with the parked jet's covers: red intake plug, exhaust bung, streamers
    m = new(pal)
    canopy(m)
    m.bx(-0.55, 0.55, -3.63, -3.61, 1.02, 1.43, 'fire', hull='none', cull='')
    m.bx(-0.05, 0.05, -3.7, -3.62, 0.3, 1.1, 'fire', hull='none', cull='')
    text(m, 'REMOVE BEFORE FLIGHT', 0.0, -3.635, 1.17, 0.07, 'white', maxw=0.98)
    vdisc(m, 0.0, 7.757, 1.8, 0.34, 'fire', seg=10, face=1)
    m.bx(-0.03, 0.03, 7.76, 7.8, 0.9, 1.75, 'fire', hull='none', cull='')
    m.bx(-0.05, 0.05, -8.0, -7.85, 1.15, 1.85, 'fire', hull='none', cull='')
    make('Fighter_Canopy', m, ao)

    # ---- maintenance: the canopy raised on its rear hinge, the boarding ladder on the left, access panels open
    m = new(pal)
    m.parent = Matrix.Translation((0, -2.4, 2.35)) @ Matrix.Rotation(math.radians(-42), 4, 'X') @ Matrix.Translation((0, 2.4, -2.35))
    canopy(m)
    m.parent = Matrix.Identity(4)
    m.bm_((0.0, -2.5, 2.3), (0.0, -3.2, 3.05), 0.06, 'steelD')
    m.bx(-0.52, 0.52, -4.6, -2.45, 2.25, 2.4, 'jetD', cull='b')
    m.bx(-0.3, 0.3, -4.1, -3.5, 2.4, 3.05, 'dark', cull='b')        # the ejection seat
    m.bx(-0.22, 0.22, -3.62, -3.45, 3.05, 3.25, 'dark', cull='')
    for dy in (-0.2, 0.2):
        m.bm_((-0.9, -3.4 + dy, 2.3), (-1.6, -3.4 + dy, 0.0), 0.05, 'yellow')
    for k in range(5):
        t = (k + 0.5) / 5
        m.bx(-0.9 - 0.7 * t - 0.12, -0.9 - 0.7 * t + 0.12, -3.62, -3.18, 2.3 * (1 - t) - 0.02, 2.3 * (1 - t) + 0.02, 'yellow', cull='')
    for s in (-1, 1):
        plate(m, [(s * 0.82, 0.4, 2.0), (s * 0.82, 1.6, 2.0), (s * 1.35, 1.6, 2.45), (s * 1.35, 0.4, 2.45)], (0, 0, -0.04), 'belly')
    for (x, y, z) in ((1.4, 1.0, 2.35), (-1.4, 1.0, 2.35), (0.0, -3.66, 1.1)):
        m.bx(x - 0.02, x + 0.02, y - 0.04, y + 0.04, z - 0.6, z, 'fire', hull='none', cull='')
    make('Fighter_Open', m, ao, cols=[cb(-1.62, -3.65, 0.0, -0.95, -3.15, 1.0)])


def _wing_cols():
    out = []
    le_boxes(out, [1.0, 2.2, 3.4, 4.85], 1.57, 1.73)
    for s in (-1, 1):
        a, b = sorted((s * 0.75, s * 2.0))
        out.append(cb(a, -3.3, 1.97, b, -2.9, 2.09))
    return out


# ================================================================ the transport (made-up "Hauler"), nose -Y, ramp +Y
TA, TB, TZ = 2.1, 1.875, 2.775      # the fuselage section: half width, half height, centre height
NOSE0, HOLD0, HOLD1 = -13.0, -5.0, 8.5


def build_transport(pal, ao):
    """Footprint x -15..15 (the wing), y -14..14. A rounded-box fuselage on a high wing with four turboprops, the
    upswept tail with a tall fin and the tailplane, gear sponsons, the cockpit glazing in the nose. The hold (floor at
    1.2 m, 2.9 m wide, 3.3 m high, y -5..8.5) is open at the back: the ramp is down (y 8.5..12.5, walkable treads),
    stowed seats along the walls, lamps, a strapped cargo pallet at the front, the cockpit bulkhead."""
    m = new(pal)
    cols = []
    N = 16
    # ---- the nose and the forward fuselage (closed rings), the bulkhead face at the hold's front
    def nose_col(k, i, p):
        x, y, z = p
        if k in (1, 2) and z > TZ + 0.55 and abs(x) < 1.6:
            return 'glassD'
        if z < 1.5:
            return 'odD'
        return 'od'
    rings = [[(0.0, NOSE0, 2.55)], sel_ring(0.8, 0.75, 2.6, -12.5, N), sel_ring(1.55, 1.4, 2.7, -11.4, N), sel_ring(1.95, 1.75, 2.76, -10.0, N),
             sel_ring(TA, TB, TZ, -8.0, N), sel_ring(TA, TB, TZ, HOLD0, N)]
    loft_pts(m, rings, nose_col, cap1='odL')
    # glazing frames on the windscreen, the radome line
    for x in (-0.55, 0.55):
        m.bm_((x * 1.1, -11.85, 3.35), (x * 1.5, -10.8, 3.95), 0.05, 'dark', hull='none')
    text(m, 'AIR WING 7', 2.103, -6.8, 3.25, 0.32, 'jetD', face='x+', font='cond')
    text(m, 'AIR WING 7', -2.103, -6.8, 3.25, 0.32, 'jetD', face='x-', font='cond')
    # ---- the hold and the upswept tail: one open-bottomed shell
    def out_col(k, i):
        return 'od' if (i > 2 and i < N - 3) or k > 0 else 'odD'
    utube(m, [(HOLD0, TA, TB, TZ, HOLD), (HOLD1, TA, TB, TZ, HOLD), (10.0, 2.0, 1.7, 2.95, 2.0), (11.5, 1.6, 1.3, 3.4, 3.0), (13.0, 0.9, 0.7, 3.9, 3.6)],
          N, out_col, 'odL', 'odD')
    # the tail cap
    tc = [sel(0.9, 0.7, 3.9, t_at(0.7, 3.9, 3.6) + (math.pi - 2 * t_at(0.7, 3.9, 3.6)) * i / (N - 1), 13.0) for i in range(N)]
    loft_pts(m, [tc, [(0.0, 13.9, 4.1)]], lambda k, i, p: 'od', cap0='odD')
    # the belly under the hold floor (its top face is the floor), the floor's roller tracks
    tb = t_at(TB, TZ, HOLD)
    lower = [sel(TA, TB, TZ, tb - (math.pi + 2 * tb) * i / 8.0, 0.0) for i in range(9)]
    lower = [(x, z) for (x, _, z) in lower]
    verts = [(x, HOLD0, z) for (x, z) in lower] + [(x, HOLD1, z) for (x, z) in lower]
    K = len(lower)
    faces = [tuple(range(K)), tuple(range(2 * K - 1, K - 1, -1))] + [(i, K + i, K + i + 1, i + 1) for i in range(K - 1)] + [(K - 1, 2 * K - 1, K, 0)]
    fs = skin(m, (verts, faces), 'odD')
    for f in fs:
        f.normal_update()
        if f.normal.z > 0.99:
            f.material_index = m.pal.index('steelD')
    for x in (-0.9, -0.5, 0.5, 0.9):
        uq(m, x - 0.06, x + 0.06, HOLD0 + 0.2, HOLD1 - 0.1, HOLD + 0.004, 'steel')
    cols.append(cb(-1.45, HOLD0 + 0.05, 0.0, 1.45, HOLD1, HOLD, True))
    # ---- the ramp (down), its treads, hinge and struts
    RT = 12.5
    plate(m, [(-1.42, HOLD1, HOLD), (1.42, HOLD1, HOLD), (1.42, RT, 0.02), (-1.42, RT, 0.02)], (0, 0, -0.12), 'odL')
    for i in range(8):
        y = HOLD1 + 0.25 + i * 0.5
        z = HOLD - (y - HOLD1) * HOLD / (RT - HOLD1)
        uq(m, -1.3, 1.3, y - 0.04, y + 0.04, z + 0.006, 'yellow' if i % 2 else 'steelD')
        top = HOLD - (i + 0.5) * 0.5 * HOLD / (RT - HOLD1)
        cols.append(cb(-1.42, HOLD1 + i * 0.5, 0.0, 1.42, HOLD1 + (i + 1) * 0.5, top, True))
    for s in (-1, 1):
        m.bm_((s * 1.5, HOLD1 + 0.3, 3.2), (s * 1.45, HOLD1 + 2.4, HOLD - 2.4 * HOLD / (RT - HOLD1) + 0.1), 0.08, 'steel')
    # ---- the hold: stowed seats on both walls, lamps, the cargo pallet strapped down at the front
    for s in (-1, 1):
        xw = s * 1.56
        (lq if s > 0 else rq)(m, xw - s * 0.01, HOLD0 + 1.0, HOLD1 - 0.5, 1.55, 2.55, 'webbing')
        for k in range(11):
            y = HOLD0 + 1.2 + k * 1.15
            (lq if s > 0 else rq)(m, xw - s * 0.014, y - 0.03, y + 0.03, 1.5, 2.6, 'steelD')
        cyl_y(m, s * 1.6, HOLD0 + 0.5, HOLD1 - 0.3, 3.6, 0.05, 'steel', seg=5, caps=False)
    for y in (-3.0, 1.0, 5.0):
        m.bx(-0.3, 0.3, y - 0.3, y + 0.3, 4.38, 4.5, 'lamp', hull='none', cull='t')
    for (x0, x1, z0, z1, c) in ((-1.1, 1.1, HOLD, HOLD + 0.12, 'wood'), (-1.0, -0.05, HOLD + 0.12, HOLD + 1.0, 'od'), (0.05, 1.0, HOLD + 0.12, HOLD + 0.85, 'khaki'), (-0.8, 0.4, HOLD + 1.0, HOLD + 1.45, 'odL')):
        m.bx(x0, x1, HOLD0 + 0.4, HOLD0 + 2.4, z0, z1, c, cull='b')
    for y in (HOLD0 + 0.9, HOLD0 + 1.9):
        m.bx(-1.12, 1.12, y - 0.03, y + 0.03, HOLD + 0.1, HOLD + 1.48, 'yellow', hull='none', cull='b')
    cols.append(cb(-1.1, HOLD0, HOLD, 1.1, HOLD0 + 2.4, HOLD + 1.45))
    # ---- the wing on top, the four nacelles with their propellers, the tail fin and tailplane
    for s in (-1, 1):
        slab(m, [(0.0, -2.4), (s * 15.0, -0.8), (s * 15.0, 1.0), (0.0, 1.8)][::s], 4.55, 4.85, 'od')
        dq(m, *sorted((s * 2.3, s * 14.8)), -1.0, 1.0, 4.547, 'odD')
        for xe in (5.0, 9.8):
            x = s * xe
            loft(m, [(-5.0, x, 4.1, 0.32, 0.32), (-4.4, x, 4.1, 0.62, 0.66), (-2.0, x, 4.15, 0.68, 0.74), (1.0, x, 4.3, 0.55, 0.55), (2.6, x, 4.45, 0.2, 0.2)],
                 lambda k, i, a: 'odD' if math.sin(a) < -0.4 else 'od', seg=8, a0=math.pi / 8)
            vdisc(m, x, -5.004, 4.1, 0.24, 'black', seg=8)
            prop(m, x, -5.0, 4.1, r=1.85, a0=0.35 + xe * 0.2)
            cols.append(cb(x - 0.7, -4.4, 3.4, x + 0.7, 1.0, 4.85))
    plate(m, [(-0.12, 9.6, 4.4), (-0.12, 13.4, 4.4), (-0.12, 14.0, 10.0), (-0.12, 12.2, 10.0)], (0.24, 0, 0), 'od')
    for s in (-1, 1):
        slab(m, [(0.0, 11.0), (s * 6.2, 12.2), (s * 6.2, 13.3), (0.0, 13.7)][::s], 4.65, 4.8, 'od')
        text(m, '07-301', s * 0.123, 12.5, 7.2, 0.5, 'black', face='x+' if s > 0 else 'x-', font='cond')
        roundel(m, s * 0.12, 12.6, 8.6, 0.45, s)
        roundel(m, s * TA, 6.6, 3.0, 0.55, s)
        for k in range(4):   # cabin portholes
            y = -3.4 + k * 2.4
            xdisc(m, s * (TA + 0.004), y, 3.3, 0.16, 'glassD', seg=8, face=s)
    m.cy((0.0, 13.0, 10.0), 0.12, 0.12, 0.15, 'lampR', seg=8)
    # ---- gear sponsons with tandem wheels, the nose gear
    for s in (-1, 1):
        xa, xb = sorted((s * 1.85, s * 2.5))
        m.bx(xa, xb, -2.6, 3.2, 0.75, 2.1, 'odD', cull='')
        for y in (-1.2, 1.8):
            wheel(m, s * 2.25, y, 0.55, 0.55, 0.35, c='tire', hub='steel', seg=12)
        cols.append(cb(xa, -2.6, 0.0, xb, 3.2, 2.1))
    m.cy((0.0, -10.0, 0.4), 0.08, 0.08, 1.2, 'steel', seg=6)
    for x in (-0.22, 0.22):
        wheel(m, x, -10.0, 0.4, 0.4, 0.22, c='tire', hub='steel', seg=10)
    # ---- collision: the nose, the hold walls (inside face near the floor-level wall), the tail over the ramp
    cols.append(cb(-1.9, NOSE0 + 0.6, 0.85, 1.9, HOLD0, 4.6))
    cols.append(cb(-0.4, -10.3, 0.0, 0.4, -9.7, 0.85))
    for s in (-1, 1):
        a, b = sorted((s * 1.56, s * 2.12))
        cols.append(cb(a, HOLD0, HOLD, b, HOLD1, 4.6))
        a, b = sorted((s * 1.7, s * 2.05))
        cols.append(cb(a, HOLD1, 2.0, b, 10.8, 4.6))
    cols.append(cb(-1.6, 11.0, 3.6, 1.6, 13.9, 4.7))
    make('Transport', m, ao, cols=cols)


# ================================================================ ground vehicles
def wheels(m, xs, ys, z, r, w):
    for x in xs:
        for y in ys:
            wheel(m, x, y, z, r, w, c='tire', hub='steel', seg=10)


def build_bowser(pal, ao):
    """[3, 8]: a 6x6 tanker: the forward cab, the elliptic tank with its walkway rail and manholes, the hose cabinet at
    the back, placards."""
    m = new(pal)
    m.bx(-1.1, 1.1, -3.9, 3.9, 0.6, 0.95, 'dark', cull='')
    m.bx(-1.25, 1.25, -3.95, -2.25, 0.95, 2.85, 'od', cull='b')
    window_y(m, -1.05, 1.05, -3.95, 2.0, 2.6, every=1.05, frame='odD')
    for s in (-1, 1):
        window_x(m, -3.6, -2.7, s * 1.25, 2.0, 2.6, every=0.9, frame='odD', face=s)
    m.bx(-1.3, 1.3, -4.05, -3.95, 0.7, 1.05, 'black', cull='')
    for x in (-0.9, 0.9):
        vdisc(m, x, -4.054, 1.25, 0.12, 'lamp', seg=8)
    # the tank
    loft(m, [(-2.05, 0.0, 2.0, 1.05, 0.8), (-1.9, 0.0, 2.0, 1.2, 0.92), (3.2, 0.0, 2.0, 1.2, 0.92), (3.35, 0.0, 2.0, 1.05, 0.8)],
         lambda k, i, a: 'od' if math.sin(a) > -0.6 else 'odD', seg=12)
    m.bx(-0.45, 0.45, -1.4, 2.8, 2.92, 2.98, 'steelD', cull='')
    for y in (-0.6, 1.6):
        m.cy((0.0, y, 2.85), 0.28, 0.28, 0.2, 'steelD', seg=8)
    for s in (-1, 1):
        m.cy((s * 0.55, -1.2, 2.9), 0.025, 0.025, 0.9, 'yellow', seg=5)
        m.cy((s * 0.55, 2.6, 2.9), 0.025, 0.025, 0.9, 'yellow', seg=5)
        cyl_y(m, s * 0.55, -1.2, 2.6, 3.78, 0.03, 'yellow', seg=5, caps=False)
        text(m, 'AVTUR', s * 1.205, 0.6, 1.85, 0.42, 'white2', face='x+' if s > 0 else 'x-', font='cond')
        text(m, 'FLAMMABLE', s * 1.205, 0.6, 1.45, 0.2, 'redD', face='x+' if s > 0 else 'x-', font='cond')
    # the rear cabinet with the hose reel
    m.bx(-1.2, 1.2, 3.35, 3.95, 0.95, 2.4, 'od', cull='b')
    bq(m, -1.0, 1.0, 3.953, 1.1, 2.25, 'odD')
    m.cy((0.0, 3.96, 1.68), 0.45, 0.45, 0.3, 'steelD', seg=10, rot=(-90, 0, 0))
    vdisc(m, 0.0, 4.264, 1.68, 0.3, 'black', seg=10, face=1)
    text(m, 'NO SMOKING', 0.0, 3.955, 2.27, 0.1, 'white', face='y+', font='cond', maxw=1.6)
    wheels(m, (-1.12, 1.12), (-3.0, 1.0, 2.4), 0.55, 0.55, 0.32)
    make('Bowser', m, ao, cols=[cb(-1.3, -4.05, 0.0, 1.3, -2.25, 2.85), cb(-1.25, -2.25, 0.0, 1.25, 3.95, 2.95)])


def build_tender(pal, ao):
    """[3, 10]: the airfield crash tender: a 6x6 in fire red with a white band, the wide cab, the roof turret and the
    bumper turret, roller-shutter lockers, the light bar."""
    m = new(pal)
    m.bx(-1.3, 1.3, -4.75, 4.75, 0.55, 0.9, 'dark', cull='')
    m.bx(-1.4, 1.4, -4.8, -2.6, 0.9, 3.05, 'fire', cull='b')
    window_y(m, -1.25, 1.25, -4.8, 2.0, 2.85, every=1.25, frame='black')
    for s in (-1, 1):
        window_x(m, -4.5, -3.0, s * 1.4, 2.0, 2.8, every=0.75, frame='black', face=s)
    m.bx(-1.4, 1.4, -2.6, 4.75, 0.9, 2.85, 'fire', cull='b')
    for s in (-1, 1):
        x = s * 1.4
        (rq if s > 0 else lq)(m, x + s * 0.003, -4.8, 4.75, 1.45, 1.65, 'white2')
        for (ya, yb) in ((-2.3, -0.4), (-0.2, 1.7), (1.9, 3.8)):
            (rq if s > 0 else lq)(m, x + s * 0.006, ya, yb, 1.75, 2.7, 'steel')
            for k in range(1, 6):
                z = 1.75 + k * 0.16
                (rq if s > 0 else lq)(m, x + s * 0.009, ya + 0.04, yb - 0.04, z - 0.01, z + 0.01, 'steelD')
        text(m, 'FIRE RESCUE', x + s * 0.006, -0.9, 1.0, 0.32, 'white2', face='x+' if s > 0 else 'x-', font='cond')
        text(m, 'AF7', x + s * 0.006, -3.7, 1.0, 0.36, 'white2', face='x+' if s > 0 else 'x-', font='cond')
    # the roof turret (monitor) over the cab, the bumper turret, the light bar, the bull bar
    m.cy((0.0, -1.8, 3.05), 0.35, 0.3, 0.3, 'steelD', seg=8)
    m.bm_((0.0, -1.8, 3.45), (0.0, -3.6, 3.65), 0.16, 'white2')
    m.cy((0.0, -3.6, 3.65), 0.12, 0.17, 0.3, 'steelD', seg=8, rot=(90, 0, 0))
    m.bx(-1.0, 1.0, -4.4, -4.0, 3.05, 3.22, 'black', cull='b')
    for x in (-0.75, -0.25, 0.25, 0.75):
        m.bx(x - 0.2, x + 0.2, -4.42, -4.02, 3.22, 3.34, 'lampR' if x < 0 else 'lampB', cull='b')
    m.bx(-1.45, 1.45, -5.0, -4.8, 0.55, 1.0, 'steelD', cull='')
    m.bm_((0.0, -5.0, 1.05), (0.0, -5.7, 1.1), 0.12, 'steelD')
    m.cy((0.0, -5.75, 1.1), 0.08, 0.1, 0.2, 'steel', seg=6, rot=(90, 0, 0))
    m.bx(-0.9, 0.9, 4.75, 4.85, 1.0, 2.6, 'steelD', cull='')
    wheels(m, (-1.2, 1.2), (-3.4, 1.6, 3.3), 0.6, 0.6, 0.36)
    make('Tender', m, ao, cols=[cb(-1.45, -5.0, 0.0, 1.45, 4.85, 3.05)])


def build_caravan(pal, ao):
    """[3, 6]: the runway control caravan: a red / white chequered box on a two-axle trailer, the glazed cupola on top,
    the door steps, the signal lamp, the drawbar."""
    m = new(pal)
    X, Y0, Y1, Z0, Z1 = 1.2, -2.5, 2.5, 0.7, 2.7
    m.bx(-X, X, Y0, Y1, Z0, Z1, 'white2', cull='b')
    sq = 0.5
    for s in (-1, 1):
        for i in range(int((Y1 - Y0) / sq)):
            for j in range(int((Z1 - Z0) / sq)):
                if (i + j) % 2:
                    continue
                ya, za = Y0 + i * sq, Z0 + j * sq
                (rq if s > 0 else lq)(m, s * (X + 0.003), ya, ya + sq, za, za + sq, 'redD')
    for (y, f) in ((Y0, -1), (Y1, 1)):
        for i in range(int(2 * X / sq) - 1):
            for j in range(int((Z1 - Z0) / sq)):
                if (i + j) % 2:
                    continue
                xa, za = -X + 0.1 + i * sq, Z0 + j * sq
                (fq if f < 0 else bq)(m, xa, xa + sq, y + f * 0.003, za, za + sq, 'redD')
    # the cupola
    m.bx(-0.85, 0.85, -1.0, 1.0, Z1, Z1 + 0.15, 'white2', cull='b')
    m.bx(-0.8, 0.8, -0.95, 0.95, Z1 + 0.15, Z1 + 0.95, 'glassD', cull='bt')
    for (x, y) in ((-0.8, -0.95), (0.8, -0.95), (-0.8, 0.95), (0.8, 0.95)):
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, Z1 + 0.15, Z1 + 0.94, 'white2', hull='none', cull='b')
    m.bx(-0.9, 0.9, -1.05, 1.05, Z1 + 0.95, Z1 + 1.05, 'redD', cull='')
    glint(m, -0.6, -0.954, Z1 + 0.25, 0.5, c='glassL')
    m.cy((0.6, 0.6, Z1 + 1.05), 0.12, 0.12, 0.2, 'lampG', seg=8)
    text(m, 'RUNWAY CONTROL', 0.0, Y0 - 0.008, Z1 - 0.32, 0.18, 'black', font='cond', maxw=2.2)
    # door, steps, trailer
    lq(m, -X - 0.009, -0.4, 0.4, Z0 + 0.05, Z1 - 0.25, 'woodD')
    m.bx(-X - 0.5, -X, -0.45, 0.45, 0.35, 0.42, 'steelD', cull='')
    m.bx(-X - 0.5, -X - 0.44, -0.45, 0.45, 0.0, 0.35, 'steelD', hull='none', cull='')
    m.bx(-1.0, 1.0, -2.3, 2.3, 0.45, 0.7, 'dark', cull='')
    wheels(m, (-1.0, 1.0), (-0.9, 0.9), 0.4, 0.4, 0.24)
    m.bm_((0.0, Y0, 0.6), (0.0, Y0 - 0.45, 0.45), 0.08, 'steelD')
    for (x, y) in ((-0.9, -2.2), (0.9, 2.2), (-0.9, 2.2), (0.9, -2.2)):
        m.cy((x, y, 0.0), 0.05, 0.05, 0.45, 'steelD', seg=5)
    make('Caravan', m, ao, cols=[cb(-X, Y0, 0.0, X, Y1, Z1 + 1.05), cb(-X - 0.5, -0.45, 0.0, -X, 0.45, 0.42)])


def build_tug(pal, ao):
    """[2, 3]: a low aircraft tug: the yellow body, a seat and steering wheel, the tow hitch, the beacon."""
    m = new(pal)
    m.bx(-0.8, 0.8, -1.35, 1.35, 0.25, 0.85, 'yellow', cull='b')
    m.bx(-0.75, 0.75, -1.4, -1.3, 0.3, 0.75, 'black', cull='')
    hazard(m, -0.75, 0.75, -1.404, 0.35, 0.7, 6)
    m.bx(-0.45, 0.45, 0.1, 0.65, 0.85, 1.05, 'dark', cull='b')
    m.bx(-0.45, 0.45, 0.55, 0.7, 1.05, 1.6, 'dark', cull='')
    m.bm_((0.0, -0.3, 0.85), (0.0, -0.55, 1.25), 0.05, 'dark')
    m.cy((0.0, -0.6, 1.25), 0.2, 0.2, 0.04, 'black', seg=10, rot=(30, 0, 0))
    m.cy((-0.6, 1.1, 0.85), 0.07, 0.07, 0.15, 'orange', seg=6)
    m.bx(-0.15, 0.15, 1.35, 1.55, 0.3, 0.45, 'steelD', cull='')
    wheels(m, (-0.72, 0.72), (-0.85, 0.85), 0.33, 0.33, 0.24)
    text(m, 'TUG 3', 0.803, 0.0, 0.45, 0.2, 'black', face='x+', font='cond')
    text(m, 'TUG 3', -0.803, 0.0, 0.45, 0.2, 'black', face='x-', font='cond')
    make('Tug', m, ao, cols=[cb(-0.85, -1.42, 0.0, 0.85, 1.55, 1.05)])


def bomb(m, x, y0, y1, z, r, c='od', band='yellow'):
    cyl_y(m, x, y0 + 0.35, y1 - 0.3, z, r, c, seg=8)
    m.cy((x, y0 + 0.35, z), r, 0.04, 0.35, c, seg=8, rot=(90, 0, 0))
    m.cy((x, y1 - 0.3, z), r, r * 0.55, 0.3, c, seg=8, rot=(-90, 0, 0))
    for s in (-1, 1):
        m.bx(x - 0.01, x + 0.01, y1 - 0.25, y1 - 0.03, z - r * 1.2 if s < 0 else z, z if s < 0 else z + r * 1.2, 'odD', hull='none', cull='')
    m.bx(x - r - 0.004, x + r + 0.004, y0 + 0.55, y0 + 0.62, z - r - 0.004, z + r + 0.004, band, hull='none', cull='')


def build_trailer(pal, ao):
    """[2, 4]: the munitions trailer: a flat bed with cradles and three bombs, the drawbar"""
    m = new(pal)
    m.bx(-0.85, 0.85, -1.7, 1.7, 0.55, 0.68, 'od', cull='')
    for y in (-1.0, 1.0):
        m.bx(-0.8, 0.8, y - 0.08, y + 0.08, 0.68, 0.8, 'odD', cull='b')
    for x in (-0.5, 0.5):
        bomb(m, x, -1.6, 1.6, 1.07, 0.27)
    bomb(m, 0.0, -1.5, 1.5, 1.55, 0.25)
    m.bm_((0.0, -1.7, 0.6), (0.0, -2.4, 0.45), 0.08, 'odD')
    m.cy((0.0, -2.4, 0.0), 0.05, 0.05, 0.45, 'steelD', seg=5)
    wheels(m, (-0.78, 0.78), (-1.0, 1.0), 0.32, 0.32, 0.2)
    make('MunTrailer', m, ao, cols=[cb(-0.9, -1.75, 0.0, 0.9, 1.75, 1.8)])


def build_craft(pal, ao):
    build_fighter(pal, ao)
    build_transport(pal, ao)
    build_bowser(pal, ao)
    build_tender(pal, ao)
    build_caravan(pal, ao)
    build_tug(pal, ao)
    build_trailer(pal, ao)
