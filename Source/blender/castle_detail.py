"""kit-castle modelled detail (tactical look plan Stage 11): ashlar courses and perpends, plinth ledges, string courses,
coping joints, arrow-slit reveals, drain spouts, putlog holes, door ironwork, stall posts and ties, well roof,
torch brackets, banner fixings. Every part is hull='none' (no outline shell), at least 3 mm proud, sunk 3 mm into what
it sits on, and horizontal runs stop 5 mm short of a module's sides. Nothing here changes a piece's origin, footprint,
collision boxes or the parts already drawn; it only adds shapes. Wall faces look toward Blender -Y (plane y = -0.5).
The builders pass their PM model `m`; shapes in another frame use m.parent (restored before returning)."""
import math

import bmesh
from mathutils import Matrix, Vector

WALK = 7.6
FRONT = 'tbklr'    # keep only the -Y face (painted lines: the other faces are never seen)
UNDER = 'tfklr'    # keep only the bottom face


def box(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def line(m, x0, x1, z0, z1, c, yf=-0.505, yb=-0.497):
    """a painted joint on a face at y = -0.5: 5 mm proud, front face only"""
    return box(m, x0, x1, yf, yb, z0, z1, c, FRONT)


def tie(m, x, y, z, r, c='rope', h=0.03):
    """a rope / iron wrap round a pole along X"""
    m.cy((x - h / 2, y, z), r, r, h, c, seg=6, rot=(0, 90, 0), caps=False, hull='none')


def ring_pull(m, x, y, z, r=0.05, c='iron'):
    """an iron ring on the -Y face of a boss whose front is at y: 8-sided annulus, 12 mm thick"""
    seg = 8
    r0 = r * 0.72
    bm = m.bm
    M = m.parent
    vs = []
    for (rr, yy) in ((r, y), (r, y - 0.012), (r0, y - 0.012), (r0, y)):
        vs.append([bm.verts.new(M @ Vector((x + math.cos(i * 2 * math.pi / seg) * rr, yy, z + math.sin(i * 2 * math.pi / seg) * rr))) for i in range(seg)])
    faces = []
    for k in range(3):
        a, b = vs[k], vs[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.nshape += 1
    for f in faces:
        f.material_index = m.pal.index(c)
        f[m.shape] = m.nshape
    m.hmode[m.nshape] = 'none'


def studs(m, xs, z, yf, yb, c='ironL', s=0.028):
    """square iron stud heads (front y = yf, sunk to yb) in a row at height z"""
    for x in xs:
        box(m, x - s / 2, x + s / 2, yf, yb, z - s / 2, z + s / 2, c, 'k')


# ================================================================ curtain walls
BEDS = (1.9, 2.7, 3.1, 3.9, 4.3, 5.1, 5.5)          # thin bed joints between the existing 1.2 m mortar courses
COURSE_Z = (1.9, 2.3, 2.7, 3.1, 3.5, 3.9, 4.3, 4.7, 5.1, 5.5, 5.9, 6.1)


def courses(m, skip=()):
    """0.4 m ashlar courses in running bond: thin bed joints between the existing mortar bands, and perpends in two
    alternating joint sets that repeat every module (stones 0.5 m long, running on across the module edge)."""
    for z in BEDS:
        line(m, -0.495, 0.495, z, z + 0.016, 'mortar')
    for i in range(len(COURSE_Z) - 1):
        za, zb = COURSE_Z[i] + 0.04, COURSE_Z[i + 1] - 0.002
        for x in ((-0.3, 0.2) if i % 2 == 0 else (-0.05, 0.45)):
            if any(x0 - 0.02 <= x <= x1 + 0.02 and zb > z0 and za < z1 for (z0, z1, x0, x1) in skip):
                continue
            line(m, x - 0.005, x + 0.005, za, zb, 'mortar', yf=-0.506)


def plinth(m, door=False):
    """course lines following the batter, a projecting cap ledge on it, and a string course under the corbels"""
    def yb(z):
        return -0.74 + 0.24 * (z - 0.32) / 1.28
    for z in ((0.62, 1.02) if not door else ()):
        box(m, -0.495, 0.495, yb(z) - 0.004, yb(z + 0.025) + 0.01, z, z + 0.025, 'mortar', 'kb')
    if door:
        for (xa, xb) in ((-0.495, -0.43), (0.43, 0.495)):
            box(m, xa, xb, -0.565, -0.497, 1.6, 1.68, 'stoneL', 'kb')
    else:
        box(m, -0.495, 0.495, -0.565, -0.497, 1.6, 1.68, 'stoneL', 'kb')
    box(m, -0.495, 0.495, -0.56, -0.497, 6.12, 6.24, 'stoneL', 'kb')


def coping(m, merlon, slit=False):
    """coping stone joints (front) and merlon bed / cap joints"""
    for x in (-0.2, 0.17):
        box(m, x - 0.005, x + 0.005, -0.846, -0.837, WALK + 0.005, WALK + 0.135, 'mortar', FRONT)
    if merlon:
        for (xa, xb) in (((-0.435, -0.1), (0.1, 0.435)) if slit else ((-0.435, 0.435),)):
            box(m, xa, xb, -0.806, -0.797, WALK + 0.67, WALK + 0.69, 'mortar', FRONT)
        box(m, -0.005, 0.005, -0.836, -0.827, WALK + 1.255, WALK + 1.355, 'mortar', FRONT)
        box(m, -0.005, 0.005, -0.83, -0.27, WALK + 1.357, WALK + 1.363, 'mortar', 'bfklr')


def spout(m, x):
    """stone drain spout through the parapet foot (stone block, projecting lip, dark mouth)"""
    box(m, x - 0.06, x + 0.06, -0.812, -0.797, 6.72, 6.9, 'stoneL', 'tbklr')
    box(m, x - 0.045, x + 0.045, -0.96, -0.797, 6.76, 6.84, 'stoneD', 'k')
    box(m, x - 0.03, x + 0.03, -0.966, -0.958, 6.775, 6.825, 'ink', FRONT)


def slit_reveal(m):
    """arrow slit: splayed jambs, sill and lintel round the dark loop, a stone sill and drip under / over the surround,
    and the same jambs round the loop in the merlon"""
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.058, sx * 0.1))
        box(m, x0, x1, -0.558, -0.527, 3.9, 5.1, 'stoneD', 'k')
    box(m, -0.1, 0.1, -0.558, -0.527, 3.83, 3.9, 'stoneD', 'k')
    box(m, -0.1, 0.1, -0.558, -0.527, 5.1, 5.17, 'stoneD', 'k')
    box(m, -0.25, 0.25, -0.58, -0.497, 3.68, 3.754, 'stoneL', 'kb')
    box(m, -0.22, 0.22, -0.545, -0.497, 5.25, 5.31, 'stoneL', 'kb')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.046, sx * 0.08))
        box(m, x0, x1, -0.817, -0.797, WALK + 0.4, WALK + 1.0, 'stoneL', 'k')
    box(m, -0.075, 0.075, -0.817, -0.797, WALK + 0.35, WALK + 0.4, 'stoneL', 'k')
    box(m, -0.075, 0.075, -0.817, -0.797, WALK + 1.0, WALK + 1.05, 'stoneL', 'k')


def door_base(m):
    """two worn steps in front of the postern (its plinth is cut away behind them)"""
    box(m, -0.47, 0.47, -0.72, -0.497, 0.0, 0.1, 'stoneD', 'kb')
    box(m, -0.45, 0.45, -0.62, -0.497, 0.1, 0.18, 'stoneL', 'kb')


def door_irons(m):
    """postern door (door front y -0.56, straps y -0.57): plank joints, studs on both straps, pintles, a ring pull and a lintel"""
    for x in (-0.165, 0.0, 0.165):
        box(m, x - 0.004, x + 0.004, -0.566, -0.557, 0.2, 2.12, 'ink', FRONT)
    for z in (0.5, 1.6):
        studs(m, (-0.28, -0.14, 0.0, 0.14, 0.28), z + 0.035, -0.586, -0.567)
        box(m, -0.37, -0.33, -0.575, -0.537, z - 0.005, z + 0.075, 'iron', 'k')
    ring_pull(m, 0.21, -0.577, 0.99, r=0.05)
    box(m, -0.45, 0.45, -0.58, -0.497, 2.35, 2.41, 'stoneL', 'kb')


def torch_irons(m):
    """back plate, diagonal stay and a band on the wall torch (the torch itself is untouched)"""
    box(m, -0.1, 0.1, -0.512, -0.497, 2.33, 2.97, 'iron', 'kb')
    m.bm_((0, -0.52, 2.4), (0, -0.8, 2.62), 0.03, 'iron', hull='none')
    m.cy((0, -0.84, 2.88), 0.0747, 0.0747, 0.03, 'ironL', seg=6, caps=False, hull='none')


def banner_irons(m):
    """banner pole fixings: back plates, rope wraps and loops, a hem rod"""
    for x in (-0.44, 0.44):
        box(m, x - 0.045, x + 0.045, -0.812, -0.797, 6.46, 6.64, 'iron', 'k')
    for x in (-0.3, 0.0, 0.3):
        tie(m, x, -0.98, 6.55, 0.047, 'rope', h=0.035)
        box(m, x - 0.014, x + 0.014, -1.007, -0.996, 6.4, 6.52, 'rope', FRONT)
    box(m, -0.42, 0.42, -1.012, -0.997, 3.28, 3.34, 'woodD', 'k')


def putlogs(m, extra):
    for (x, z) in ((-0.05, 2.9), (0.2, 4.1), (-0.05, 5.3)):
        if (extra == 'slit' and z == 4.1) or (extra == 'torch' and z == 2.9):
            continue
        box(m, x - 0.05, x + 0.05, -0.524, -0.497, z - 0.045, z + 0.045, 'ink', 'k')


def curtain_detail(m, extra, merlon, seed):
    """everything a plain / slit / banner / torch / buttress / door curtain module gets"""
    skip = {'slit': [(3.65, 5.35, -0.26, 0.26)], 'bannerR': [(3.0, 6.55, -0.42, 0.42)], 'bannerB': [(3.0, 6.55, -0.42, 0.42)],
            'torch': [(2.4, 3.95, -0.2, 0.2)], 'buttress': [(1.6, 6.2, -0.36, 0.36)]}.get(extra, [])
    courses(m, skip=skip)
    plinth(m, extra == 'door')
    coping(m, merlon, extra == 'slit')
    if extra not in ('bannerR', 'bannerB', 'buttress'):
        putlogs(m, extra)
    if extra not in ('bannerR', 'bannerB', 'buttress', 'torch'):
        spout(m, 0.38 if seed % 2 else -0.38)
    if extra == 'slit':
        slit_reveal(m)
    elif extra == 'door':
        door_base(m)
        door_irons(m)
    elif extra == 'torch':
        torch_irons(m)
    elif extra in ('bannerR', 'bannerB'):
        banner_irons(m)


def inner_detail(m):
    """beside an inner corner nothing stands proud of the face: only the painted courses"""
    courses(m)


def corner_detail(m):
    """the four-way turret: courses and perpends on every face, an arrow slit with splayed jambs, corbels under the top"""
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        for z in BEDS + (6.3, 6.7, 7.1, 7.5, 7.9):
            box(m, -0.615, 0.615, -0.625, -0.617, z, z + 0.016, 'mortar', FRONT)
        zs = COURSE_Z + (6.3, 6.7, 7.1, 7.5, 7.9, 8.3)
        for i in range(len(zs) - 1):
            for x in ((0.0,) if i % 2 == 0 else (-0.31, 0.31)):
                box(m, x - 0.005, x + 0.005, -0.626, -0.617, zs[i] + 0.04, zs[i + 1] - 0.002 if zs[i + 1] - zs[i] > 0.1 else zs[i + 1] - 0.0, 'mortar', FRONT)
        box(m, -0.045, 0.045, -0.652, -0.617, 3.9, 5.1, 'ink', 'k')
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.05, sx * 0.095))
            box(m, x0, x1, -0.668, -0.617, 3.9, 5.1, 'stoneL', 'k')
        box(m, -0.09, 0.09, -0.668, -0.617, 5.1, 5.17, 'stoneL', 'k')
        box(m, -0.09, 0.09, -0.668, -0.617, 3.83, 3.9, 'stoneL', 'k')
        for x in (-0.45, 0.0, 0.45):                                              # corbels under the top slab
            box(m, x - 0.07, x + 0.07, -0.78, -0.617, 7.95, 8.3, 'stoneD', 'kt')
    m.parent = Matrix.Identity(4)


# ================================================================ gatehouse
GD = 0.95
GW = 2.96


def gate_detail(m):
    """gatehouse: course lines on the piers and over the arch, string course under the machicolation, dark machicolation
    slots, wall plates behind the torches, rope wraps and plates on the banner poles, merlon joints, a finial"""
    for sy in (-1, 1):
        m.parent = Matrix.Rotation(0 if sy < 0 else math.pi, 4, 'Z')
        yf, yb = -GD - 0.006, -GD + 0.003
        for z in (1.3, 1.8, 2.8):
            for sx in (-1, 1):
                x0, x1 = sorted((sx * 1.72, sx * 2.94))
                box(m, x0, x1, yf, yb, z, z + 0.016, 'mortar', FRONT)
        for z in (7.8, 8.3):
            box(m, -2.94, 2.94, yf, yb, z, z + 0.016, 'mortar', FRONT)
        box(m, -2.955, 2.955, -GD - 0.05, yb, 8.5, 8.62, 'stoneL', 'kb')
        for x in (-2.3, 2.3):
            box(m, x - 0.08, x + 0.08, -GD - 0.014, yb, 2.12, 2.38, 'iron', 'k')        # torch plate
            box(m, x - 0.15, x + 0.15, -GD - 0.011, yb, 3.0, 3.6, 'stoneDD', FRONT)    # soot
        for k in range(7):                                                                # dark machicolation slots
            xg = -2.65 + (k + 0.5) * 0.757
            box(m, xg - 0.2, xg + 0.2, -GD - 0.28, -GD - 0.04, 9.047, 9.053, 'ink', UNDER)
        for k in range(5):                                                                # merlon joints
            x = -2.5 + k * 1.25
            box(m, x - 0.005, x + 0.005, -GD - 0.336, -GD - 0.327, 10.0 + 1.055, 10.0 + 1.155, 'mortar', FRONT)
    m.parent = Matrix.Identity(4)
    m.cy((0, 0, 12.6), 0.05, 0.0, 0.14, 'gold', seg=5, hull='none')
    m.cy((0, 0, 12.0), 0.0545, 0.0545, 0.03, 'rope', seg=6, caps=False, hull='none')


def shutter_detail(m):
    """iron ferrule bands round each oak bar, on both faces"""
    for sy in (-1, 1):
        for k in range(7):
            x = -1.29 + k * 0.43
            y0, y1 = sorted((sy * 0.085 - sy * 0.003, sy * 0.085 + sy * 0.012))
            box(m, x - 0.11, x + 0.11, y0, y1, 1.5, 1.57, 'iron', 'k' if sy < 0 else 'f')


# ================================================================ drum towers
def tower_detail(m, R, roof):
    """plinth cap ledge, course rings every 0.8 m (between the existing mortar rings), slit reveals, door ironwork,
    barred windows, merlon joints"""
    m.cy((0, 0, 1.6), R + 0.07, R + 0.07, 0.1, 'stoneL', seg=16, hull='none')
    for z in (2.4, 4.0, 4.8, 6.4, 7.2, 8.8, 9.6):
        m.cy((0, 0, z), R + 0.006, R + 0.006, 0.016, 'mortar', seg=16, caps=False, hull='none')
    for k in (0, 1):
        for a in (-0.9, 0.9):
            m.parent = Matrix.Rotation(k * math.pi + a, 4, 'Z')
            for (z0, z1) in ((4.2, 5.5), (7.1, 8.2)):
                for sx in (-1, 1):
                    x0, x1 = sorted((sx * 0.076, sx * 0.12))
                    box(m, x0, x1, -R - 0.04, -R + 0.05, z0, z1, 'stoneL', 'k')
                box(m, -0.12, 0.12, -R - 0.06, -R + 0.05, z0 - 0.05, z0, 'stoneL', 'kb')
        m.parent = Matrix.Rotation(k * math.pi, 4, 'Z')
        yd = -R - 0.39
        for x in (-0.24, 0.0, 0.24):
            box(m, x - 0.004, x + 0.004, yd - 0.005, yd + 0.003, 0.1, 2.25, 'ink', FRONT)
        for z in (0.6, 1.6):
            studs(m, (-0.36, -0.12, 0.12, 0.36), z + 0.04, -R - 0.43, -R - 0.407)
        box(m, 0.14, 0.26, -R - 0.42, -R - 0.387, 1.1, 1.22, 'iron', 'k')
        ring_pull(m, 0.2, -R - 0.417, 1.06, r=0.06)
        box(m, -0.66, 0.66, -R - 0.4, -R + 0.3, 2.6, 2.66, 'stoneL', 'kb')                   # door hood
        for x in (-0.15, 0.0, 0.15):                                                          # window bars
            box(m, x - 0.012, x + 0.012, -R - 0.135, -R - 0.117, 6.02, 6.98, 'iron', 'k')
        box(m, -0.38, 0.38, -R - 0.2, -R + 0.1, 7.0, 7.07, 'stoneL', 'kb')
    m.parent = Matrix.Identity(4)
    if not roof:
        for k in range(10):
            m.parent = Matrix.Rotation(k * 2 * math.pi / 10, 4, 'Z')
            box(m, -0.005, 0.005, -R - 0.456, -R - 0.447, 12.855, 12.945, 'mortar', FRONT)
        m.parent = Matrix.Identity(4)
        m.cy((0, 0, 14.97), 0.05, 0.0, 0.12, 'gold', seg=5, hull='none')
    else:
        m.cy((0, 0, 19.4), 0.05, 0.0, 0.12, 'gold', seg=5, hull='none')


# ================================================================ keep
def keep_detail(m, W, D):
    """course lines on all four faces, window sills and glazing bars, pilaster bases, a plinth cap, the door ironwork,
    banner and torch fixings"""
    box(m, -W - 0.43, W + 0.43, -D - 0.43, D + 0.43, 1.36, 1.46, 'stoneL', 'b')
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        half = W if k % 2 == 0 else D
        depth = D if k % 2 == 0 else W
        for i in range(17):
            z = 2.2 + 0.8 * i
            if abs(z - 14.2) < 0.05:
                continue
            box(m, -half + 0.905, half - 0.905, -depth - 0.005, -depth + 0.003, z, z + 0.016, 'mortar', FRONT)
        xs = (-3.2, 0.0, 3.2) if k % 2 == 0 else (-2.0, 2.0)
        for x in xs:
            for (z, big) in ((6.1, False), (10.6, True)):
                if k == 0 and x == 0.0 and not big:
                    continue
                w, h = (0.5, 2.0) if big else (0.36, 1.4)
                box(m, x - w - 0.2, x + w + 0.2, -depth - 0.14, -depth + 0.003, z - 0.18, z - 0.09, 'stoneL', 'k')
                box(m, x - w + 0.01, x + w - 0.01, -depth - 0.085, -depth - 0.065, z + h * 0.45, z + h * 0.45 + 0.035, 'iron', 'k')
        if k % 2 == 0:
            for x in (-1.6, 1.6):
                box(m, x - 0.35, x + 0.35, -depth - 0.28, -depth + 0.003, 1.4, 1.8, 'stoneD', 'kb')
                box(m, x - 0.35, x + 0.35, -depth - 0.28, -depth + 0.003, 15.4, 15.55, 'stoneL', 'k')
    m.parent = Matrix.Identity(4)
    # forebuilding door: plank joints, three straps with studs, a ring pull; torch and banner fixings
    yd = -D - 0.1
    for x in (-0.275, 0.0, 0.275):
        box(m, x - 0.005, x + 0.005, yd - 0.006, yd + 0.003, 4.28, 5.95, 'ink', FRONT)
    for z in (4.5, 5.5):
        box(m, -0.54, 0.54, yd - 0.015, yd + 0.003, z, z + 0.08, 'iron', 'k')
    for z in (4.5, 5.0, 5.5):
        studs(m, (-0.45, -0.3, -0.15, 0.15, 0.3, 0.45), z + 0.04, yd - 0.037, yd - 0.012, s=0.03)
    box(m, 0.1, 0.2, yd - 0.04, yd + 0.003, 5.2, 5.3, 'iron', 'k')
    ring_pull(m, 0.15, yd - 0.037, 5.17, r=0.07)
    box(m, -0.88, 0.88, -D - 0.12, -D + 0.003, 6.85, 6.93, 'stoneL', 'kb')               # hood over the surround
    box(m, -1.11, -0.99, -D - 0.014, -D + 0.003, 5.12, 5.38, 'iron', 'k')                 # torch wall plate
    for x in (-0.7, 0.7):                                                                 # banner pole stand-offs
        box(m, x - 0.025, x + 0.025, -D - 0.45, -D + 0.003, 14.775, 14.825, 'iron', 'k')
    for x in (-0.8, -0.3, 0.3, 0.8):
        tie(m, x, -D - 0.45, 14.8, 0.052, 'rope', h=0.04)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.047, sx * 1.12))
        box(m, x0, x1, -D - 0.485, -D - 0.415, 14.755, 14.845, 'gold', '')


# ================================================================ market stalls, crates, well, brazier, banner poles
def stall_detail(m):
    for x in (-1.4, 1.4):
        for y, top in ((-0.85, 2.45), (0.85, 2.1)):
            box(m, x - 0.09, x + 0.09, y - 0.09, y + 0.09, 0.0, 0.1, 'stoneD', 'b')        # foot stone
            tz = 2.28 if y < 0 else 1.9                                                       # rope tie under the roof
            box(m, x - 0.072, x + 0.072, y - 0.072, y + 0.072, tz, tz + 0.06, 'rope', '')
        for z in (1.5, 1.85):                                                                 # pegs on the front posts
            box(m, x - 0.018, x + 0.018, -0.995, -0.907, z, z + 0.04, 'woodD', 'k')
    box(m, -1.37, 1.37, -0.88, -0.82, 2.18, 2.26, 'wood', '')                               # front rail between the posts
    box(m, -1.395, 1.395, -0.92, -0.897, 0.1, 0.18, 'wood', 'kb')                           # bottom rail of the counter
    box(m, -1.395, 1.395, -0.92, -0.897, 0.78, 0.86, 'wood', 'kbt')                          # apron under the counter top
    box(m, -1.595, 1.595, -1.085, -1.047, 2.48, 2.54, 'rope', 'k')                         # rope along the valance top
    for x in (-0.9, 0.0, 0.9):                                                              # basket hoops
        for z in (0.1, 0.28):
            r = 0.24 + 0.06 * z / 0.38 + 0.011
            m.cy((x, 0.15, z), r, r, 0.03, 'wood', seg=8, caps=False, hull='none')


def crate_detail(m, cx, cy, z, s):
    """corner battens and side bands on one crate"""
    h = s / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((cx + sx * (h - 0.04), cx + sx * (h + 0.012)))
            ya, yb = sorted((cy + sy * (h - 0.04), cy + sy * (h + 0.012)))
            box(m, xa, xb, ya, yb, z + 0.004, z + s - 0.006, 'woodD', '')
        xa, xb = sorted((cx + sx * (h - 0.003), cx + sx * (h + 0.006)))
        for zz in (z + 0.03, z + s - 0.09):
            box(m, xa, xb, cy - h + 0.045, cy + h - 0.045, zz, zz + 0.06, 'wood', '')


def well_detail(m):
    for k in range(14):                                                                     # coping joints on the rim
        m.parent = Matrix.Rotation(k * 2 * math.pi / 14, 4, 'Z')
        box(m, 0.8, 1.2, -0.006, 0.006, 0.967, 0.973, 'mortar', 'bfkl')
    m.parent = Matrix.Identity(4)
    m.cy((0, 0, 0.42), 1.157, 1.157, 0.02, 'mortar', seg=14, caps=False, hull='none')       # drum bed joint
    for sx in (-1, 1):
        m.bm_((sx * 1.03, 0, 2.0), (sx * 0.7, 0, 2.48), 0.07, 'wood', hull='none')           # braces under the roof beam
    for x in (-0.82, 0.82):
        tie(m, x, 0, 1.75, 0.092, 'iron', h=0.05)                                           # windlass bands
    for sy in (-1, 1):                                                                      # shingle courses on the roof
        for t in (0.3, 0.55, 0.8):
            ang = math.atan(0.72) * (1 if sy < 0 else -1)
            m.parent = Matrix.Translation((0, sy * t, 3.25 - 0.72 * t)) @ Matrix.Rotation(ang, 4, 'X')
            box(m, -1.28, 1.28, -0.015, 0.015, -0.003, 0.004, 'slateD', 'b')
    m.parent = Matrix.Identity(4)
    box(m, -1.29, 1.29, -0.045, 0.045, 3.2, 3.29, 'woodD', 'b')                              # ridge board


def brazier_detail(m):
    for z in (0.25,):                                                                       # plinth course
        for k in range(4):
            m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
            box(m, -0.315, 0.315, -0.328, -0.317, z, z + 0.016, 'mortar', FRONT)
    m.parent = Matrix.Identity(4)
    for k in range(4):                                                                      # iron ribs up the basket
        a = k * math.pi / 2 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        r0, r1 = 0.12 + 0.22 * 0.03 / 0.32 + 0.022, 0.12 + 0.22 * 0.29 / 0.32 + 0.022
        m.bm_((c * r0, s * r0, 1.51), (c * r1, s * r1, 1.77), 0.03, 'iron', hull='none')
    m.cy((0, 0, 1.74), 0.3088, 0.3088, 0.06, 'ironL', seg=8, caps=False, hull='none')       # rim band
    m.cy((0, 0, 0.62), 0.082, 0.082, 0.05, 'ironL', seg=6, caps=False, hull='none')         # post collar


def bannerpole_detail(m):
    box(m, -0.33, 0.33, -0.33, 0.33, 0.345, 0.4, 'stoneL', 'b')
    m.cy((0, 0, 0.4), 0.09, 0.062, 0.1, 'iron', seg=6, hull='none')
    m.cy((0, 0, 1.4), 0.073, 0.073, 0.05, 'iron', seg=6, caps=False, hull='none')
    for x in (0.2, 0.5, 0.8):
        tie(m, x, 0, 5.3, 0.045, 'rope', h=0.03)
        for sy in (-1, 1):
            y0, y1 = sorted((sy * 0.022, sy * 0.032))
            box(m, x - 0.012, x + 0.012, y0, y1, 5.06, 5.3, 'rope', 'k' if sy < 0 else 'f')


def trail_detail(m):
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.357, sx * 0.366))
        box(m, x0, x1, -0.005, 0.005, WALK + 0.005, WALK + 0.135, 'mortar', '')              # coping joint
        x0, x1 = sorted((sx * 0.247, sx * 0.274))
        box(m, x0, x1, -0.05, 0.05, 4.0, 4.09, 'ink', 'l' if sx > 0 else 'r')                  # putlog hole
