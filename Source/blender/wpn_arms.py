"""INKBOLT weapons: the first-person arms (tactical gloves, bracers, sleeves) and their rig.
Built by fam_weapons.py; shape kit and gun parts in wpn_core.py."""
import math
import os

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from ib_lib import *  # noqa: F401,F403
import ib_lib
from wpn_core import *  # noqa: F401,F403


# ================================================================ arms: tactical gloves, bracers, 40-bone rig
# Hand frame (right hand): origin = grip anchor (web of the hand), z = grip axis up, y = forward, x = right. The
# glove is modelled closed round a grip section (ANAT), so the hold IS the rest pose; the left glove is the same
# anatomy mirrored by its rest frame (two-hand pistol hold).
# Glove, in layers:
#  * palm: ONE closed surface, a voxel union of anatomical primitives (palm slab wrapped round the grip, heel,
#    wrist, thenar + thumb metacarpal, a stub at each finger root), relaxed, painted (padded back panel, grip
#    leather inside) and decimated; shading normals from the dense union. Rigid on HAND except the thenar, which
#    follows THUMB1.
#  * digits: lofted tubes skinned to three bones each (digit_rings): a ball at the knuckle turning inside the palm,
#    one ring in the bisector plane of each joint (half on each bone), a raised padded back on the first phalanx,
#    a reinforced tip, grip leather inside. Each has its own ink shell, which draws the gaps between fingers.
#  * armour (own shells): one moulded knuckle guard across the four knuckles and a ribbed shield over the back of
#    the hand (rigid on HAND), a pad over the thumb knuckle (rigid on the thumb's first phalanx).
#  * cuff: an elastic wrist band skinned from HAND to FOREARM across the wrist joint (the wrist bends without a
#    gap or a socket), a strap with a buckle across it.
# Forearm (rigid on FOREARM, see forearm): fitted sleeve bunching into folds at the elbow, an armoured bracer
# strapped over it (base plate, raised plate with one accent line, bolts, two straps) and a wrist device with a
# lit display on the left forearm.
# Posing (wpn_anim.solve): every digit joint is a hinge about the digit's flexion axis, the knuckle also spreads;
# the forearm rolls with the hand (the wrist only bends) and the elbow swings to line the forearm up with the hand.
# Colours are palette cells named in COL. Triangle split is printed by the build (ARMS: ...).
FINGERS = ('INDEX', 'MIDDLE', 'RING', 'PINKY')
DIGITS = FINGERS + ('THUMB',)     # three bones each: <DIGIT>1_<side> (knuckle), 2, 3
MIRROR = Matrix.Diagonal((-1, 1, 1, 1))
SH = {'R': V((0.20, -0.58, -0.30)), 'L': V((-0.42, -0.50, -0.28))}     # shoulders (off screen): support arm comes in from lower left
UPPER_LEN, FORE_LEN = 0.30, 0.29
# palette cells of every part (change a look here)
COL = {'fabric': 'glove4', 'pad': 'glove3', 'grip': 'rubber', 'tip': 'rubber', 'hard': 'glove2', 'groove': 'glove4', 'seam': 'glove3', 'cuff': 'rubber', 'hem': 'glove3',
       'strap': 'rubber', 'buckle': 'steel2', 'sleeve': 'sleeve3', 'crease': 'glove4', 'plate': 'gun2', 'plate2': 'gun3',
       'bolt': 'steel2', 'accent': 'amber', 'screen': 'emis', 'device': 'rubber', 'upper': 'sleeve3'}
# fingers: knuckle height on the grip, radius at MCP / PIP / DIP / tip, phalanx lengths (joint to joint)
FING = {'INDEX': (-0.0125, (0.0094, 0.0090, 0.0085, 0.0079), (0.041, 0.025, 0.016)),
        'MIDDLE': (-0.0320, (0.0098, 0.0094, 0.0088, 0.0082), (0.045, 0.028, 0.018)),
        'RING': (-0.0515, (0.0094, 0.0090, 0.0085, 0.0079), (0.043, 0.026, 0.017)),
        'PINKY': (-0.0705, (0.0084, 0.0080, 0.0076, 0.0071), (0.035, 0.021, 0.015))}
FLAT = 0.90             # finger section squashed along the grip axis: gaps between fingers stay open
# trigger finger: along the frame, a square bend at the middle joint, through the guard, pad on the trigger
INDEX_TRIGGER = [(0.0282, 0.0575, -0.0150), (0.0035, 0.0585, -0.0170), (-0.0120, 0.0545, -0.0180)]
THUMB_R = (0.0118, 0.0112, 0.0106, 0.0098)
WRIST = V((0.019, HAND['cy'] - 0.055, -0.060))
PALM_C = V((0.014, HAND['cy'] - 0.012, -0.042))
# Per-glove anatomy in model space (a right hand round the grip section; the left glove is mirrored by its
# rest frame). grip: section the fingers wrap (the support glove closes round bigger things: the strong hand,
# handguards); palm: slab stations (angle, z top, z bottom, thickness); mcp: knuckles (angle, distance off the
# grip): the knuckle row sits at the front corner of the grip, so the back of the hand is a full palm long;
# thenar / heel: (angle, z, grow, radii); panel: angles of the padded back panel.
# thumb: CMC, MCP, IP, tip as (angle, z, distance off the grip): the strong thumb wraps the back of the grip.
# The support thumb is modelled lying forward along the pistol frame under the strong thumb (given in the
# strong hand's frame), so the two-hand pistol hold is its undeformed rest pose.
ANAT = {
    'R': {'grip': {'hx': HAND['hx'], 'hy': HAND['hy'], 'cy': HAND['cy']}, 'mcp': (30.0, 0.0165), 'trigger': True,
          'palm': [(43, -0.006, -0.077, 0.0185), (30, -0.004, -0.080, 0.0210), (10, -0.002, -0.084, 0.0235), (-12, 0.000, -0.087, 0.0245),
                   (-35, 0.004, -0.090, 0.0245), (-60, 0.007, -0.092, 0.0230), (-90, 0.010, -0.086, 0.0180), (-118, 0.008, -0.062, 0.0160),
                   (-140, 0.003, -0.044, 0.0140)],
          'thumb': [(-97, -0.033, 0.0103), (-147, -0.013, 0.0170), (167, -0.004, 0.0184), (142, -0.002, 0.0248)],
          'thenar': (-122, -0.026, 0.010, (0.011, 0.019, 0.020)), 'heel': (-55, -0.068, 0.012, (0.012, 0.020, 0.018)),
          'panel': (22, -50)},
    'L': {'grip': {'hx': 0.021, 'hy': 0.026, 'cy': HAND['cy']}, 'mcp': (30.0, 0.0165), 'trigger': False,
          'palm': [(43, -0.006, -0.077, 0.0185), (30, -0.004, -0.080, 0.0210), (10, -0.002, -0.084, 0.0235), (-12, 0.000, -0.087, 0.0245),
                   (-35, 0.000, -0.090, 0.0245), (-55, -0.004, -0.090, 0.0230), (-78, -0.012, -0.082, 0.0190)],
          'thumb_strong': [(-0.044, -0.036, -0.032), (-0.040, -0.012, -0.024), (-0.035, 0.016, -0.020), (-0.031, 0.036, -0.019)],
          'thenar': (-50, -0.016, 0.017, (0.012, 0.018, 0.016)), 'heel': (-58, -0.068, 0.012, (0.012, 0.020, 0.018)),
          'panel': (22, -50)},
}
GLOVE_VOXEL = 0.0008
GLOVE_TRIS = 620         # palm / heel / thenar union per glove before its ink shell (x2 with it)
GLOVE_SMOOTH = 7
DIGIT_SIDES = 8
ARM_HULL_T = 0.0028      # ink shell of the arms (m): between the guns' fine line and the old 3.5 mm


def gpt(G, theta, gz, grow):
    """Point on the grip section (angle theta, 0 = right, 90 = front) grown outward by grow, at height gz."""
    t = D(theta)
    return V(((G['hx'] + grow) * math.cos(t), G['cy'] + (G['hy'] + grow) * math.sin(t), gz))


def grip_coords(G, q):
    """Inverse of gpt: (theta deg, grow) of a model-space point."""
    lo, hi = -min(G['hx'], G['hy']) + 0.001, 0.12
    f = lambda g: (q.x / (G['hx'] + g)) ** 2 + ((q.y - G['cy']) / (G['hy'] + g)) ** 2 - 1.0
    if f(lo) < 0:
        return math.degrees(math.atan2(q.y - G['cy'], q.x)), lo
    for _ in range(30):
        m = (lo + hi) / 2
        if f(m) > 0:
            lo = m
        else:
            hi = m
    g = (lo + hi) / 2
    return math.degrees(math.atan2((q.y - G['cy']) / (G['hy'] + g), q.x / (G['hx'] + g))), g


def tangent_ccw(P, A, B, cy):
    """Angle of the point where a line from P touches the ellipse (A, B) wrapping counter-clockwise (+z)."""
    def q(t):
        return V((A * math.cos(t), cy + B * math.sin(t), 0))

    def f(t):
        d = q(t) - V((P.x, P.y, 0))
        tg = V((-A * math.sin(t), B * math.cos(t), 0))
        return d.x * tg.y - d.y * tg.x, d.dot(tg)
    n = 720
    best = None
    a0 = math.atan2((P.y - cy) / B, P.x / A)
    prev = f(a0)
    for i in range(1, n + 1):
        t0, t1 = a0 + 2 * math.pi * (i - 1) / n, a0 + 2 * math.pi * i / n
        cur = f(t1)
        if (prev[0] > 0) != (cur[0] > 0):
            lo, hi, flo = t0, t1, prev[0]
            for _ in range(40):
                m = (lo + hi) / 2
                fm = f(m)[0]
                if (fm > 0) == (flo > 0):
                    lo, flo = m, fm
                else:
                    hi = m
            if f(lo)[1] > 0:
                best = lo
                break
        prev = cur
    return best


def finger_joints(side, fn):
    """MCP, PIP, DIP, tip centre: each phalanx is a straight segment laid tangent to the grip (contact)."""
    an = ANAT[side]
    G = an['grip']
    z, r, L = FING[fn]
    P = gpt(G, an['mcp'][0], z, an['mcp'][1])
    if fn == 'INDEX' and an['trigger']:          # trigger finger: along the frame, pad on the trigger
        return [P] + [V(p) for p in INDEX_TRIGGER]
    pts = [P]
    for i, l in enumerate(L):
        rr = (r[i] + r[i + 1]) / 2
        A, B = G['hx'] + rr + 0.0006, G['hy'] + rr + 0.0006
        t = tangent_ccw(P, A, B, G['cy'])
        if t is None:
            d = V((-math.sin(D(an['mcp'][0])), math.cos(D(an['mcp'][0])), 0))
        else:
            Q = V((A * math.cos(t), G['cy'] + B * math.sin(t), P.z))
            d = Q - P
            d.z = 0
            d.normalize()
        P = P + d * l + V((0, 0, -0.0008))
        pts.append(P)
    return pts


def thumb_joints(side, X):
    an = ANAT[side]
    if 'thumb' in an:
        return [gpt(an['grip'], th, z, g) for th, z, g in an['thumb']]
    M = X[side].inverted() @ X['R']
    return [M @ V(p) for p in an['thumb_strong']]


def flex_axis(J, toward=None):
    """Flexion axis of a digit with joints J: turning a phalanx about it by a positive angle bends the digit more.
    From the bends the digit already has; a straight digit bends toward the point `toward`. Works in any space."""
    J = [V(p) for p in J]
    d = [(J[i + 1] - J[i]).normalized() for i in range(len(J) - 1)]
    c = V((0, 0, 0))
    for a, b in zip(d, d[1:]):
        c += a.cross(b)
    if c.length < 0.30 and toward is not None:
        mid = (J[0] + J[-1]) / 2
        c = (J[-1] - J[0]).cross(V(toward) - mid)
    return c.normalized()


def digit_joints(side, dn, X):
    """Knuckle, two joints and the tip centre of a digit in the glove's model space."""
    return thumb_joints(side, X) if dn == 'THUMB' else finger_joints(side, dn)


def digit_axis(side, J, X=None):
    """Flexion axis of a digit in the space its joints J are given in (model space, or rig space with the glove's
    rest frame X); a straight digit (the support thumb) closes toward the glove's grip axis."""
    G = ANAT[side]['grip']
    X = X if X is not None else Matrix.Identity(4)
    o, z = X @ V((0, G['cy'], 0)), (X.to_3x3() @ V((0, 0, 1))).normalized()
    mid = (V(J[0]) + V(J[-1])) / 2
    return flex_axis(J, o + z * (mid - o).dot(z))


PAD_H = 0.0017           # padded finger back: how far it stands off the finger


def digit_rings(J, r, bones, ax, sides=DIGIT_SIDES, flat=FLAT, pad=True):
    """A finger (or the thumb's two phalanges) as one lofted tube through its joints J (radii r at the joints),
    skinned to one bone per phalanx: a ball at the root joint (it turns inside the palm), ONE ring in the bisector
    plane of each joint (half on each bone, bulged over the knuckle, tucked in at the crease), a raised padded
    back on each phalanx long enough for one and a rounded tip. ax: the flexion axis (back of the digit = d x ax).
    Returns (rings, weight per ring, kind per band: 'root' | 'fabric' | 'pad' (back faces padded) | 'seam' (the
    stitched band where the reinforced tip starts) | 'tip')."""
    J = [V(p) for p in J]
    n = len(J) - 1
    d = [(J[i + 1] - J[i]).normalized() for i in range(n)]
    dors = [q.cross(ax).normalized() for q in d]

    def ring(c, b, rad, kd=1.0, kp=1.0, up=0.0):
        b = b.normalized()
        s = (ax - b * ax.dot(b)).normalized()
        out = []
        for k in range(sides):
            a = 2 * math.pi * (k + 0.5) / sides
            back = math.sin(a) > 0.3
            out.append(c + s * (rad * flat * math.cos(a)) + b * ((rad * (kd if math.sin(a) > 0 else kp) + (up if back else 0.0)) * math.sin(a)))
        return out
    rings, wts, kinds = [], [], []

    def add(pts, w, kind):
        rings.append(pts)
        wts.append(w)
        kinds.append(kind)             # kind of the band that ENDS at this ring
    b0 = bones[0]
    add([J[0] - d[0] * (r[0] * 0.95)], b0, 'root')
    add(ring(J[0] - d[0] * (r[0] * 0.55), dors[0], r[0] * 0.80), b0, 'root')
    add(ring(J[0], dors[0], r[0]), b0, 'root')
    for i in range(n):
        L = (J[i + 1] - J[i]).length
        ra, rb = r[i], r[i + 1]
        rad = lambda t: ra + (rb - ra) * t / L
        e = min(max(0.26 * L, 0.0085), 0.45 * L)
        if i == n - 1:
            add(ring(J[i] + d[i] * e, dors[i], rad(e) * 0.98), bones[i], 'fabric')
            add(ring(J[i] + d[i] * (e + 0.0020), dors[i], rad(e + 0.0020) * 1.0), bones[i], 'seam')
            add(ring(J[i + 1], dors[i], rb * 0.97, kd=0.92), bones[i], 'tip')
            add(ring(J[i + 1] + d[i] * (rb * 0.52), dors[i], rb * 0.74, kd=0.88), bones[i], 'tip')
            add([J[i + 1] + d[i] * (rb * 0.92)], bones[i], 'tip')
            continue
        add(ring(J[i] + d[i] * e, dors[i], rad(e) * 0.97), bones[i], 'fabric')
        if pad and L - 2 * e > 0.010:
            s = 0.0022
            add(ring(J[i] + d[i] * (e + s), dors[i], rad(e + s) * 0.97, up=PAD_H), bones[i], 'pad')
            add(ring(J[i + 1] - d[i] * (e + s), dors[i], rad(L - e - s) * 0.97, up=PAD_H), bones[i], 'pad')
        add(ring(J[i + 1] - d[i] * e, dors[i], rad(L - e) * 0.97), bones[i], 'pad')
        phi = d[i].angle(d[i + 1])
        kd = min(1.0 / max(math.cos(phi / 2), 0.5), 1.16) * 1.03
        add(ring(J[i + 1], dors[i] + dors[i + 1], rb, kd=kd, kp=0.82), {bones[i]: 0.5, bones[i + 1]: 0.5}, 'fabric')
    return rings, wts, kinds[1:]


def pillow(c, n, along, w, l, h, ch=0.0016, sink=0.003, hexa=False):
    """Rings of a hard moulded pad (chamfered rectangle or hexagon pillow) centred at c on a surface of normal n."""
    n, along = V(n).normalized(), V(along)
    along = (along - n * along.dot(n)).normalized()
    side = n.cross(along)
    if hexa:
        rect = [(w / 2, -l * 0.30), (w / 2, l * 0.30), (0, l / 2), (-w / 2, l * 0.30), (-w / 2, -l * 0.30), (0, -l / 2)]
    else:
        k = min(w, l) * 0.28
        rect = [(w / 2, -l / 2 + k), (w / 2, l / 2 - k), (w / 2 - k, l / 2), (-w / 2 + k, l / 2), (-w / 2, l / 2 - k), (-w / 2, -l / 2 + k),
                (-w / 2 + k, -l / 2), (w / 2 - k, -l / 2)]
    ring = lambda dz, ins: [V(c) + n * dz + side * q[0] + along * q[1] for q in (inset2d(rect, ins) if ins > 0 else rect)]
    return [ring(-sink, 0.0), ring(h - ch, 0.0), ring(h, ch)]


def knuckle_guard(K, h=0.0072, sink=0.0042):
    """Rings of one moulded knuckle guard across the four knuckles (K: (centre, outward normal, finger direction,
    radius) index to pinky): a hard band with a raised bump over each knuckle and shallow valleys between."""
    st = []
    for i, (c, n, d, r) in enumerate(K):
        st.append((c, n, d, r * 1.75, h))
        if i + 1 < len(K):
            c2, n2, d2, r2 = K[i + 1]
            st.append(((c + c2) / 2 + ((n + n2) / 2) * -0.0006, ((n + n2) / 2).normalized(), ((d + d2) / 2).normalized(), (r + r2) * 0.72, h * 0.50))
    (c0, n0, d0, w0, h0), (c1, *_) = st[0], st[1]
    (cz, nz, dz, wz, hz), (cy, *_) = st[-1], st[-2]
    st = [(c0 + (c0 - c1).normalized() * 0.0042, n0, d0, w0 * 0.82, h0 * 0.55)] + st + \
         [(cz + (cz - cy).normalized() * 0.0040, nz, dz, wz * 0.82, hz * 0.55)]
    rings = []
    for c, n, d, w, hh in st:
        n = V(n)
        d = (V(d) - n * V(d).dot(n)).normalized()
        q = [(-sink, 0.5), (hh * 0.62, 0.5), (hh, 0.22), (hh, -0.22), (hh * 0.62, -0.5), (-sink, -0.5)]
        rings.append([V(c) + n * a + d * (b * w) for a, b in q])
    return rings


# ---------------------------------------------------------------- closed primitives of the palm union
class Body:
    """Overlapping closed primitives of one glove's palm (rig space); each carries the bone it follows."""

    def __init__(self, X):
        self.X = X
        self.parts = []

    def _part(self, bone):
        bm = bmesh.new()
        self.parts.append({'bm': bm, 'bone': bone})
        return bm

    def loft(self, rings, bone, rig=False):
        bm = self._part(bone)
        vr = [[bm.verts.new(V(p) if rig else self.X @ V(p)) for p in r] for r in rings]
        for i in range(len(vr) - 1):
            a, b = vr[i], vr[i + 1]
            n = max(len(a), len(b))
            for j in range(n):
                j2 = (j + 1) % n
                if len(a) == 1:
                    bm.faces.new((a[0], b[j], b[j2]))
                elif len(b) == 1:
                    bm.faces.new((a[j], a[j2], b[0]))
                else:
                    bm.faces.new((a[j], a[j2], b[j2], b[j]))
        for r in (vr[0], vr[-1]):
            if len(r) >= 3:
                bm.faces.new(r)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        return bm

    def capsule(self, a, b, ra, rb, bone, up=(0, 0, 1), flat=1.0, seg=16, cap=5):
        """Round-ended tapered cylinder a -> b; the section is squashed along `up` by flat."""
        a, b = V(a), V(b)
        d = b - a
        L = d.length
        d.normalize()
        u = V(up) - d * V(up).dot(d)
        if u.length < 1e-6:
            u = d.orthogonal()
        u.normalize()
        s = d.cross(u)
        prof = [(-ra * math.cos(math.pi / 2 * i / cap), ra * math.sin(math.pi / 2 * i / cap)) for i in range(cap + 1)]
        prof += [(L + rb * math.sin(math.pi / 2 * i / cap), rb * math.cos(math.pi / 2 * i / cap)) for i in range(cap + 1)]
        rings = []
        for t, r in prof:
            c = a + d * t
            if r < 1e-7:
                rings.append([c])
            else:
                rings.append([c + s * (r * math.cos(2 * math.pi * k / seg)) + u * (r * flat * math.sin(2 * math.pi * k / seg)) for k in range(seg)])
        return self.loft(rings, bone)

    def ellipsoid(self, c, radii, axes, bone, seg=16):
        """axes: three orthonormal vectors the radii run along."""
        c = V(c)
        rings = []
        n = seg // 2
        for i in range(n + 1):
            ph = math.pi * i / n
            z = -math.cos(ph)
            rr = math.sin(ph)
            if rr < 1e-6:
                rings.append([c + axes[2] * (radii[2] * z)])
            else:
                rings.append([c + axes[0] * (radii[0] * rr * math.cos(2 * math.pi * k / seg)) + axes[1] * (radii[1] * rr * math.sin(2 * math.pi * k / seg))
                              + axes[2] * (radii[2] * z) for k in range(seg)])
        return self.loft(rings, bone)


def palm_at(palm, theta):
    """Interpolated palm station (z top, z bottom, thickness) at an angle."""
    for (t0, a0, b0, c0), (t1, a1, b1, c1) in zip(palm, palm[1:]):
        if t1 <= theta <= t0:
            k = (theta - t0) / (t1 - t0)
            return a0 + (a1 - a0) * k, b0 + (b1 - b0) * k, c0 + (c1 - c0) * k
    return palm[0][1:] if theta > palm[0][0] else palm[-1][1:]


def rrect_gz(g0, g1, z0, z1, rc, seg=3):
    """Rounded rectangle in (grow, z), counter-clockwise."""
    rc = min(rc, (g1 - g0) / 2 - 1e-4, (z1 - z0) / 2 - 1e-4)
    pts = []
    for cg, cz, a0 in ((g1 - rc, z0 + rc, -90), (g1 - rc, z1 - rc, 0), (g0 + rc, z1 - rc, 90), (g0 + rc, z0 + rc, 180)):
        for k in range(seg + 1):
            a = D(a0 + 90.0 * k / seg)
            pts.append((cg + rc * math.cos(a), cz + rc * math.sin(a)))
    return pts


G0 = 0.0012              # palm skin off the grip section
# back-of-hand shield: a moulded plate from behind the knuckle guard toward the wrist, three ribs with two dark
# grooves between; stations (angle, z top edge, z bottom edge, height over the palm)
SHIELD = [(19, -0.0150, -0.0680, 0.0012), (15, -0.0120, -0.0710, 0.0040), (-8, -0.0170, -0.0700, 0.0044), (-30, -0.0240, -0.0660, 0.0040),
          (-37, -0.0290, -0.0620, 0.0010)]
SHIELD_Z = (0.0, 0.07, 0.30, 0.37, 0.63, 0.70, 0.93, 1.0)     # across the plate: edge, three ribs, two grooves


def glove(A, side, X):
    """One glove into the arms mesh A: palm union, skinned digits, knuckle guard and ribs."""
    an = ANAT[side]
    G = an['grip']
    Xs = X[side]
    b = Body(Xs)
    hb, tb = 'HAND_' + side, 'THUMB1_' + side
    Z = V((0, 0, 1))

    def nrm(theta):
        return V((math.cos(D(theta)) / G['hx'], math.sin(D(theta)) / G['hy'], 0)).normalized()
    # palm slab wrapped round the grip, heel (hypothenar), wrist ending in a ball round the wrist joint
    b.loft([[gpt(G, th, z, g) for g, z in rrect_gz(G0, G0 + T, zb, zt, 0.0080)] for th, zt, zb, T in an['palm']], hb)
    th, z, g, rad = an['heel']
    n = nrm(th)
    b.ellipsoid(gpt(G, th, z, 0.0) + n * g, rad, (n, Z.cross(n), Z), hb)
    wa = gpt(G, -50, -0.050, 0.012)
    wd = (WRIST - wa).normalized()
    b.capsule(wa, WRIST + wd * 0.004, 0.0210, 0.0200, hb, up=(0, 0, 1), flat=1.08)
    # fingers: a stub of the palm at each root (the web), the skinned digit, the knuckle under the guard
    knuckles = []
    digits = []
    for fn in FINGERS:
        z, r, L = FING[fn]
        J = finger_joints(side, fn)
        d0 = (J[1] - J[0]).normalized()
        b.capsule(J[0] - d0 * 0.004, J[0] + d0 * (L[0] * 0.26), r[0] * 0.96, r[0] * 0.88, hb, up=(0, 0, 1), flat=FLAT, seg=12, cap=3)
        digits.append((J, r, ['%s%d_%s' % (fn, i, side) for i in (1, 2, 3)], digit_axis(side, J), FLAT))
        n0 = (d0.cross(Z)).normalized()                         # back of the finger: outward, away from the grip
        nk = (n0 + nrm(an['mcp'][0])).normalized()              # the guard sits on the corner between hand and finger
        if fn == 'INDEX' and an['trigger']:
            nk = (nk + Z * 0.30).normalized()
        knuckles.append((J[0] + nk * (r[0] * 0.78), nk, d0 if fn != 'INDEX' or not an['trigger'] else (J[1] - J[0] - Z * 0.004).normalized(), r[0]))
    # thumb: metacarpal inside the thenar mass (union, follows THUMB1), the two phalanges one skinned digit
    T = T2 = thumb_joints(side, X)
    b.capsule(T[0], T[1], THUMB_R[0] + 0.004, THUMB_R[1], tb, up=(0, 0, 1), flat=0.95)
    th, z, g, rad = an['thenar']
    n = nrm(th)
    b.ellipsoid(gpt(G, th, z, 0.0) + n * g, rad, (n, Z.cross(n), Z), tb)
    digits.append((T[1:], THUMB_R[1:], ['THUMB2_' + side, 'THUMB3_' + side], digit_axis(side, T), 0.94))
    # paint: grip leather on the inside of the palm, the padded panel on the back of the hand
    Xi = Xs.inverted()
    t0, t1 = an['panel']

    def paint(p):
        q = Xi @ p
        th, g = grip_coords(G, q)
        if th > an['palm'][0][0] + 6 or th < an['palm'][-1][0] - 8:
            return COL['fabric']
        zt, zb, T = palm_at(an['palm'], th)
        if g < G0 + 0.0060 and zb - 0.004 < q.z < zt + 0.004:
            return COL['grip']
        if g > G0 + T - 0.0050 and t1 < th < t0:
            u = (th - (t0 + t1) / 2) / ((t0 - t1) / 2)
            v = (q.z - (zt + zb) / 2) / ((zt - zb) / 2 - 0.0125)
            if abs(u) ** 5 + abs(v) ** 5 < 1.0:
                return COL['pad']
        return COL['fabric']
    g = union_surface(b, A.pal, paint)
    A.union(g, glove_weights(g, b, side), 'gloves')
    g.free()
    for p in b.parts:
        p['bm'].free()
    for J, r, bones, ax, flat in digits:
        rings, wts, kinds = digit_rings(J, r, bones, ax, flat=flat)
        cols = [COL['tip'] if k == 'tip' else COL['seam'] if k == 'seam' else COL['fabric'] for k in kinds]

        def fcol(i, j, kinds=kinds):
            if kinds[i] == 'pad' and j < DIGIT_SIDES // 2 - 1:
                return COL['pad']
            if kinds[i] not in ('root', 'seam') and DIGIT_SIDES // 2 <= j < DIGIT_SIDES - 1:
                return COL['grip']
        A.loft([[Xs @ p for p in rr] for rr in rings], cols, wts, 'digits', soft=True, fcol=fcol)
    # armour: the knuckle guard, the ribbed shield over the back of the hand from the knuckles toward the wrist
    rings = knuckle_guard(knuckles)
    A.loft([[Xs @ p for p in rr] for rr in rings], [COL['hard']] * len(rings), hb, 'armour')
    rings = []
    for th, z1, z0, up in SHIELD:
        T = palm_at(an['palm'], th)[2]
        zs = [z0 + (z1 - z0) * k for k in SHIELD_Z]
        ring = [gpt(G, th, zs[0], G0 + T - 0.0030)] + [gpt(G, th, z, G0 + T + up) for z in zs[1:-1]] + [gpt(G, th, zs[-1], G0 + T - 0.0030)]
        rings.append(ring)
    A.loft([[Xs @ p for p in rr] for rr in rings], [COL['hard']] * len(rings), hb, 'armour',
           fcol=lambda i, j: COL['groove'] if j in (2, 4) and 0 < i < len(SHIELD) - 2 else None)
    # thumb knuckle pad (rigid on the thumb's first phalanx)
    ta = (T2[2] - T2[1]).normalized()
    tn = T2[1] - PALM_C
    tn = (tn - ta * tn.dot(ta)).normalized()
    rings = pillow(T2[1] + ta * 0.004 + tn * (THUMB_R[1] * 0.86), tn, ta, THUMB_R[1] * 1.30, THUMB_R[1] * 1.9, 0.0040, sink=0.0040)
    A.loft([[Xs @ p for p in rr] for rr in rings], [COL['hard']] * 3, 'THUMB2_' + side, 'armour', caps=(False, True))


# ---------------------------------------------------------------- union -> one surface
def _apply(ob, kind, **props):
    m = ob.modifiers.new(kind.lower(), kind)
    for k, v in props.items():
        setattr(m, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    old = ob.data
    ob.data = new
    bpy.data.meshes.remove(old)


def union_surface(body, pal, paint, voxel=GLOVE_VOXEL, tris=GLOVE_TRIS):
    """Voxel union of the body's primitives, relaxed, painted (paint(rig point) -> palette cell; palette UVs: the
    decimator keeps UV seams, so patch borders stay clean), decimated; returns a triangle bmesh."""
    bm = bmesh.new()
    for p in body.parts:
        pb = p['bm']
        pb.normal_update()
        p['bvh'] = BVHTree.FromBMesh(pb)
        vm = {v: bm.verts.new(v.co) for v in pb.verts}
        for f in pb.faces:
            bm.faces.new([vm[v] for v in f.verts])
    me = bpy.data.meshes.new('_glove')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('_glove', me)
    bpy.context.scene.collection.objects.link(ob)
    _apply(ob, 'REMESH', mode='VOXEL', voxel_size=voxel, adaptivity=0.0)
    _apply(ob, 'LAPLACIANSMOOTH', iterations=GLOVE_SMOOTH, lambda_factor=0.6, use_volume_preserve=True, use_normalized=True)
    hi = bmesh.new()
    hi.from_mesh(ob.data)
    hi.normal_update()
    hi.faces.ensure_lookup_table()
    hbvh = BVHTree.FromBMesh(hi)
    uvl = hi.loops.layers.uv.verify()
    for f in hi.faces:
        uv = pal.uv(pal.index(paint(f.calc_center_median())))
        for lp in f.loops:
            lp[uvl].uv = uv
    hi.to_mesh(ob.data)
    n = len(hi.faces) * 2
    _apply(ob, 'DECIMATE', decimate_type='COLLAPSE', ratio=min(1.0, tris / n), use_collapse_triangulate=True)
    out = bmesh.new()
    out.from_mesh(ob.data)
    bpy.data.objects.remove(ob)
    bmesh.ops.triangulate(out, faces=list(out.faces))
    bmesh.ops.recalc_face_normals(out, faces=list(out.faces))
    ouv = out.loops.layers.uv.active
    for f in out.faces:
        u, v = f.loops[0][ouv].uv
        f.material_index = int(u * 8) + 8 * int(v * 8)
    # shading normals from the dense smooth union (the decimated faces alone shade blotchy under toon bands)
    sn = out.verts.layers.float_vector.new('snor')
    for v in out.verts:
        acc = V((0, 0, 0))
        for loc, nor, idx, d in hbvh.find_nearest_range(v.co, 0.0035):
            acc += nor * (hi.faces[idx].calc_area() * (1.0 - d / 0.0035))
        if acc.length < 1e-9:
            acc = v.normal.copy()
        v[sn] = acc.normalized()
    hi.free()
    # collapse decimation folds (a face turned against its smooth neighbours would show its ink shell)
    for _ in range(6):
        out.normal_update()
        bad = [f for f in out.faces if f.normal.dot(sum((v[sn] for v in f.verts), V((0, 0, 0))).normalized()) < 0.25]
        if not bad:
            break
        bmesh.ops.collapse(out, edges=list({min(f.edges, key=lambda e: e.calc_length()) for f in bad}), uvs=True)
    return out


def sdist(p, part):
    loc, nor, idx, d = part['bvh'].find_nearest(p)
    if loc is None:
        return 1e9
    return d if (p - loc).dot(nor) >= 0 else -d


THENAR_SOFT = 0.0045     # the palm blends into the thumb metacarpal over this distance


def glove_weights(bm, body, side):
    """Palm weights: HAND, blending smoothly into THUMB1 on the thenar mass."""
    hb, tb = 'HAND_' + side, 'THUMB1_' + side
    out = []
    for v in bm.verts:
        dh = min(abs(sdist(v.co, p)) for p in body.parts if p['bone'] == hb)
        dt = min(abs(sdist(v.co, p)) for p in body.parts if p['bone'] == tb)
        k = min(1.0, max(0.0, 0.5 + (dh - dt) / (2 * THENAR_SOFT)))
        k = k * k * (3 - 2 * k)
        out.append({hb: 1.0 - k, tb: k} if 0.02 < k < 0.98 else {tb if k > 0.5 else hb: 1.0})
    return out


# ---------------------------------------------------------------- the arms mesh: lofts with bone weights
class ArmMesh:
    """One bmesh for both arms. Every loft is one shape (own ink shell, own z-fight id), rigid on a bone or
    skinned ring by ring; `soft` shapes shade fully smooth, the others get crisp edges."""

    def __init__(self, pal, names):
        self.pal = pal
        self.bm = bmesh.new()
        self.dl = self.bm.verts.layers.deform.verify()
        self.sl = self.bm.faces.layers.int.new('shape_id')
        self.snl = self.bm.verts.layers.float_vector.new('snor')
        self.gi = {n: i for i, n in enumerate(names)}
        self.sid = 0
        self.soft, self.nohull, self.group = set(), set(), {}

    def _shape(self, group, soft, hull):
        self.sid += 1
        self.group[self.sid] = group
        if soft:
            self.soft.add(self.sid)
        if not hull:
            self.nohull.add(self.sid)
        return self.sid

    def _w(self, v, w):
        for b, x in (w.items() if isinstance(w, dict) else ((w, 1.0),)):
            v[self.dl][self.gi[b]] = x

    def loft(self, rings, colors, w, group, soft=False, hull=True, caps=(True, True), fcol=None, capcol=(None, None)):
        """Closed loft of rings (rig-space points; a one-point ring is an apex). colors: one palette cell per band
        (ring i -> i+1), fcol(i, j) may override a face (band i, column j), capcol the end caps. w: a bone name,
        or per ring a bone name or {bone: weight}."""
        bm, pal = self.bm, self.pal
        sid = self._shape(group, soft, hull)
        vr = [[bm.verts.new(V(p)) for p in r] for r in rings]
        faces = []
        for i in range(len(vr) - 1):
            a, b = vr[i], vr[i + 1]
            n = max(len(a), len(b))
            for j in range(n):
                j2 = (j + 1) % n
                q = (a[0], b[j], b[j2]) if len(a) == 1 else (a[j], a[j2], b[0]) if len(b) == 1 else (a[j], a[j2], b[j2], b[j])
                f = bm.faces.new(q)
                f.material_index = pal.index((fcol and fcol(i, j)) or colors[i])
                faces.append(f)
        for k, (r, c) in enumerate(((vr[0], capcol[0] or colors[0]), (vr[-1], capcol[1] or colors[-1]))):
            if caps[k] and len(r) >= 3:
                f = bm.faces.new(r)
                f.material_index = pal.index(c)
                faces.append(f)
        big = [f for f in faces if len(f.verts) > 4]
        if big:
            res = bmesh.ops.triangulate(bm, faces=big)
            faces = list(dict.fromkeys([f for f in faces if f.is_valid] + list(res['faces'])))
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        for f in faces:
            f[self.sl] = sid
        for k, r in enumerate(vr):
            for v in r:
                self._w(v, w[k] if isinstance(w, list) else w)
        return sid

    def union(self, g, weights, group):
        """A painted union surface (triangles, 'snor' shading normals) with per-vertex weights."""
        sid = self._shape(group, True, True)
        gsn = g.verts.layers.float_vector['snor']
        vm = {}
        for v, w in zip(g.verts, weights):
            nv = self.bm.verts.new(v.co)
            nv[self.snl] = v[gsn]
            self._w(nv, w)
            vm[v] = nv
        for f in g.faces:
            nf = self.bm.faces.new([vm[v] for v in f.verts])
            nf.material_index = f.material_index
            nf[self.sl] = sid
        return sid


# ---------------------------------------------------------------- forearm: cuff, strap, sleeve, bracer, device
# Laid out in the hand's own frame: t runs from the wrist joint to the elbow, the section is an ellipse whose wide
# axis spans thumb side (radial) to little-finger side, its other axis the back of the hand. at(t, phi, extra,
# lift) is a point on it (phi from the thumb side toward the back of the hand).
#   * cuff: the glove's elastic wrist band, skinned HAND -> FOREARM across the joint; strap + buckle behind it.
#   * sleeve: fitted, bunching into diagonal folds toward the elbow (dark crease under each fold).
#   * bracer: a base plate wrapped round the side the camera sees, a raised plate with one accent line and
#     chamfered ends, a bolt at each corner, two straps round the arm; left arm: a wrist device with a lit display.
FORE_SEG = 16
# arm section stations: (t, half width (radial-ulnar), half height (dorsal-volar), shift to the thumb side, shift to the back)
FORE_PROF = [(-0.020, 0.0236, 0.0186, 0.0, 0.0), (0.000, 0.0240, 0.0190, 0.0, 0.0), (0.050, 0.0270, 0.0210, 0.0, 0.0005),
             (0.100, 0.0312, 0.0248, 0.0012, 0.0012), (0.150, 0.0370, 0.0300, 0.0026, 0.0024), (0.195, 0.0425, 0.0352, 0.0040, 0.0032),
             (0.235, 0.0458, 0.0388, 0.0042, 0.0032), (0.268, 0.0450, 0.0394, 0.0030, 0.0020), (0.300, 0.0410, 0.0372, 0.0, 0.0)]
# cuff rings: (t, extra radius over the arm, weight on the forearm, colour of the band that starts here)
CUFF = [(-0.022, -0.0030, 0.0, 'cuff'), (-0.018, 0.0034, 0.0, 'cuff'), (-0.013, 0.0050, 0.0, 'cuff'), (-0.005, 0.0050, 0.30, 'cuff'),
        (0.004, 0.0050, 0.72, 'cuff'), (0.012, 0.0050, 1.0, 'cuff'), (0.042, 0.0052, 1.0, 'hem'), (0.045, 0.0068, 1.0, 'hem'),
        (0.051, 0.0068, 1.0, 'hem'), (0.054, 0.0020, 1.0, 'hem')]
STRAP = (0.017, 0.031, 0.0072)                    # wrist strap: t from, to, extra radius
SLEEVE_T = (0.036, 0.066, 0.100, 0.150, 0.198, 0.208, 0.217, 0.226, 0.235, 0.244, 0.253, 0.262, 0.272, 0.282, 0.292, 0.302)
SLEEVE_EX = 0.0030
FOLDS = ((0.224, 0.0046, 200, 0.55), (0.247, 0.0052, 150, 0.45), (0.270, 0.0046, 230, 0.60), (0.290, 0.0034, 120, 0.50))
FOLD_W, FOLD_SLANT = 0.0100, 0.009       # fold half width along the arm, diagonal (t shift across the arm)
# bracer plates: stations (t, half arc deg, extra radius of the outer face); in: extra radius of the inner face;
# arc: where the section's points sit across the plate (-1..1); accent: the column that takes the accent line
BRACER = {'in': 0.0040, 'st': [(0.062, 62, 0.0062), (0.070, 96, 0.0086), (0.150, 104, 0.0090), (0.188, 100, 0.0090), (0.200, 70, 0.0064)],
          'arc': tuple(-1.0 + 0.25 * i for i in range(9))}
PLATE = {'in': 0.0070, 'st': [(0.078, 30, 0.0104), (0.085, 44, 0.0128), (0.172, 48, 0.0132), (0.184, 34, 0.0106)],
         'arc': (-1.0, -0.6, -0.2, 0.2, 0.54, 0.72, 1.0), 'accent': 4}
BSTRAPS = ((0.086, 0.099), (0.166, 0.179))        # bracer straps (t from, to)
DEVICE = {'t': 0.118, 'w': 0.030, 'l': 0.042, 'h': 0.0070}
CAM_RIG = V((-0.224, -0.588, 0.153))                    # game viewmodel camera in rig space (weapons.js vmRoot)


def fore_prof(t):
    P = FORE_PROF
    if t <= P[0][0]:
        return P[0][1:]
    for p0, p1 in zip(P, P[1:]):
        if p0[0] <= t <= p1[0]:
            k = (t - p0[0]) / (p1[0] - p0[0])
            k = k * k * (3 - 2 * k)
            return tuple(a + (b - a) * k for a, b in zip(p0[1:], p1[1:]))
    return P[-1][1:]


def forearm(A, side, wr, fd, rad, dor, views=(CAM_RIG,)):
    """Cuff, strap, sleeve, bracer and device of one forearm (frame: fd wrist -> elbow, rad thumb side, dor back of
    the hand; views: the game camera in rest space for the holds that matter: the bracer faces them)."""
    fb, hb = 'FOREARM_' + side, 'HAND_' + side

    def at(t, phi, extra=0.0, lift=0.0):
        a, b, ds, du = fore_prof(t)
        a, b = a + extra, b + extra
        ph = D(phi)
        n = V((math.cos(ph) * b, math.sin(ph) * a)).normalized()        # ellipse normal
        x, y = math.cos(ph) * a + n.x * lift + ds, math.sin(ph) * b + n.y * lift + du
        return wr + fd * t + rad * x + dor * y

    def patch(t, phi, ex, pts, lift):
        """2D points (across m, along m) laid on the arm round (t, phi)."""
        a0 = (fore_prof(t)[0] + fore_prof(t)[1]) / 2 + ex
        return [at(t + y, phi + math.degrees(x / a0), ex, lift) for x, y in pts]

    angles = [360.0 * (k + 0.5) / FORE_SEG for k in range(FORE_SEG)]

    def view_angle(cam):            # the side a camera sees (angle from the thumb side toward the back of the hand)
        dc = cam - (wr + fd * 0.12)
        dc -= fd * dc.dot(fd)
        return math.degrees(math.atan2(dc.dot(dor), dc.dot(rad)))
    va = [view_angle(c) for c in views]
    pc = va[0]
    if len(va) > 1:
        dv = (va[1] - va[0] + 180) % 360 - 180
        pc = va[0] + dv * 0.65          # most guns are long guns
    FORE_VIEW[side] = (va, pc)
    # cuff: skinned across the wrist joint
    w = [{fb: k, hb: 1.0 - k} if 0.0 < k < 1.0 else (fb if k >= 1.0 else hb) for _, _, k, _ in CUFF]
    A.loft([[at(t, phi, ex) for phi in angles] for t, ex, _, _ in CUFF], [COL[c] for _, _, _, c in CUFF], w, 'cuffs')
    # strap across the wrist, a buckle on the side the camera sees
    t0, t1, ex = STRAP
    prof = [(t0, ex - 0.0036), (t0 + 0.0012, ex), (t1 - 0.0012, ex), (t1, ex - 0.0036)]
    A.loft([[at(t, phi, e) for phi in angles] for t, e in prof], [COL['strap']] * 4, fb, 'cuffs', caps=(False, False))
    bk = rrect(0.017, t1 - t0 + 0.005, c=0.0028)
    A.loft([patch((t0 + t1) / 2, pc, ex, bk, -0.0020), patch((t0 + t1) / 2, pc, ex, bk, 0.0022), patch((t0 + t1) / 2, pc, ex, inset2d(bk, 0.0026), 0.0022)],
           [COL['buckle']] * 3, fb, 'cuffs', capcol=(None, COL['strap']))
    # sleeve: from under the cuff to the elbow; the cloth bunches into diagonal folds toward the elbow, the shaded
    # underside of each fold (toward the elbow, where it is deep) takes the crease colour
    def fold(t, phi):
        h, slope = 0.0, 0.0
        for tc, amp, pcf, wrap in FOLDS:
            dp = math.cos(D(phi - pcf))
            wa = max(0.0, (dp + wrap) / (1 + wrap)) ** 1.5
            u = (t - tc - FOLD_SLANT * math.sin(D(phi - pcf + 90))) / FOLD_W
            if abs(u) < 1:
                b = 0.5 + 0.5 * math.cos(math.pi * u)
                h += amp * wa * b
                slope += -amp * wa * math.sin(math.pi * u) * (u > 0)
        return h, slope
    rings = [[at(t, phi, SLEEVE_EX + fold(t, phi)[0]) for phi in angles] for t in SLEEVE_T]
    te = SLEEVE_T[-1] + 0.012
    rings.append([wr + fd * te + rad * fore_prof(te)[2] + dor * fore_prof(te)[3]])
    crease = lambda i, j: COL['crease'] if i < len(SLEEVE_T) - 1 and fold((SLEEVE_T[i] + SLEEVE_T[i + 1]) / 2, angles[j] + 180 / FORE_SEG)[1] < -0.0022 else None
    A.loft(rings, [COL['sleeve']] * len(rings), fb, 'sleeves', fcol=crease)

    # bracer: plates are open arcs with thickness, tapered at both ends
    def arc_plate(P, colour, fcol=None):
        rings = []
        for t, half, ex in P['st']:
            arc = [pc + half * k for k in P['arc']]
            rings.append([at(t, a, ex) for a in arc] + [at(t, a, P['in']) for a in reversed(arc)])
        A.loft(rings, [colour] * len(rings), fb, 'bracers', fcol=fcol)
    arc_plate(BRACER, COL['plate'])
    arc_plate(PLATE, COL['plate2'], fcol=lambda i, j: COL['accent'] if i == 1 and j == PLATE['accent'] else None)
    for t0, t1 in BSTRAPS:
        ex = SLEEVE_EX + 0.0022
        prof = [(t0, ex - 0.0030), (t0 + 0.0012, ex), (t1 - 0.0012, ex), (t1, ex - 0.0030)]
        A.loft([[at(t, phi, e) for phi in angles] for t, e in prof], [COL['strap']] * 4, fb, 'bracers', caps=(False, False))
    hexa = [(0.0036 * math.cos(D(60 * k)), 0.0036 * math.sin(D(60 * k))) for k in range(6)]
    for t, da in ((0.078, -78), (0.078, 78), (0.190, -78), (0.190, 78)):
        ex = 0.0088 if t > 0.1 else 0.0080
        A.loft([patch(t, pc + da, ex, hexa, -0.0015), patch(t, pc + da, ex, hexa, 0.0024)], [COL['bolt']] * 2, fb, 'bracers', hull=False)
    if side == 'L':             # wrist device: a bezel with a lit display, two keys behind it
        Dv = DEVICE
        ex = PLATE['st'][2][2]
        box = rrect(Dv['w'], Dv['l'], c=0.0045)
        A.loft([patch(Dv['t'], pc, ex, box, -0.0020), patch(Dv['t'], pc, ex, box, Dv['h'] - 0.0016), patch(Dv['t'], pc, ex, inset2d(box, 0.0034), Dv['h'])],
               [COL['device']] * 3, fb, 'bracers', capcol=(None, COL['screen']))
        for dx in (-0.0075, 0.0075):
            key = rrect(0.0095, 0.0070, c=0.0015)
            kp = [(x + dx, y + Dv['l'] / 2 + 0.0085) for x, y in key]
            A.loft([patch(Dv['t'], pc, ex, kp, -0.0015), patch(Dv['t'], pc, ex, kp, 0.0030)], [COL['bolt']] * 2, fb, 'bracers', hull=False)


FORE_VIEW = {}


def arms_hull(obj, pal, t, nohull=()):
    """ib_lib.add_hull for the arms: glove vertices move out along their smooth shading normal (the
    even-thickness boost spikes in concave creases between fingers), shells along a capped even normal."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uvl = bm.loops.layers.uv['UVMap']
    col = bm.loops.layers.float_color['Col']
    sn = bm.verts.layers.float_vector.get('snor')
    hull = bm.verts.layers.float_vector.new('_HULL')
    sl = bm.faces.layers.int.get('shape_id')
    faces = [f for f in bm.faces if f[sl] not in nohull]     # inner details (bolts, keys) carry no shell
    bvh = BVHTree.FromBMesh(bm)
    dup = bmesh.ops.duplicate(bm, geom=faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts}))
    nf = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
    bm.normal_update()
    moves = {}
    for v in nv:
        if v[sn].length > 0.5:
            # never push the shell through another part of the glove (tight creases, touching fingers)
            n = v[sn].normalized()
            hit = bvh.ray_cast(v.co + n * 0.0001, n, 2.0 * t)
            k = 1.0 if hit[0] is None else max(0.25, min(1.0, 0.55 * (hit[3] + 0.0001) / t))
            moves[v] = n * k
            continue
        ns = []
        for f in v.link_faces:
            n = f.normal
            if n.length > 0.5 and not any(abs(n.dot(m)) > 0.9999 for m in ns):
                ns.append(n.copy())
        if not ns:
            continue
        d = V((0, 0, 0))
        for n in ns:
            d += n
        if d.length < 1e-6:
            d = ns[0].copy()
        d.normalize()
        moves[v] = d * (1.0 / min(max(d.dot(n), 0.7) for n in ns))
    hi = pal.index('HULL')
    hu, hv = pal.uv(hi)
    for v, d in moves.items():
        v.co += d * t
        v[hull] = d
    bmesh.ops.reverse_faces(bm, faces=nf)
    for e in {e for f in nf for e in f.edges}:
        e.smooth = True
    for f in nf:
        f.material_index = hi
        f.smooth = True
        for lp in f.loops:
            lp[uvl].uv = (hu, hv)
            lp[col] = (1.0, 1.0, 1.0, 1.0)
    bm.to_mesh(obj.data)
    bm.free()


def two_bone(s, w, hint, U=UPPER_LEN, F=FORE_LEN, pref=None):
    """Elbow for shoulder s and wrist w; an out-of-reach wrist pulls the (off-screen) shoulder in."""
    d = w - s
    if d.length > U + F - 0.002:
        s = w - d.normalized() * (U + F - 0.002)
        d = w - s
    L = d.length
    dn = d.normalized()
    a = (U * U - F * F + L * L) / (2 * L)
    h = math.sqrt(max(U * U - a * a, 0))
    sd = (hint - dn * hint.dot(dn)).normalized()
    if pref is None or h < 1e-4:
        return s, s + dn * a + sd * h
    # the elbow swings round the shoulder-wrist axis to line the forearm up with the hand (pref: the hand's
    # wrist -> knuckles axis) without leaving the hint's side: no snapped wrists, elbows stay down and out
    c, sv = s + dn * a, dn.cross(sd)
    best = None
    for i in range(-40, 41):
        t = D(i * 2.0)
        e = c + (sd * math.cos(t) + sv * math.sin(t)) * h
        cost = (w - e).normalized().angle(pref) ** 2 + ELBOW_K * t * t
        if best is None or cost < best[0]:
            best = (cost, e)
    return s, best[1]


ELBOW_K = 0.45          # how hard the elbow keeps to its hint side vs. lining the forearm up with the hand


HINT = {'R': V((0.7, -0.2, -1)), 'L': V((-0.8, -0.2, -1))}
RIG = {}


def grip_frame(wid):
    return mat_trs((0, 0, 0), (-WEAPONS[wid]['rake'], 0, 0))


def build_arms(pal):
    F0 = {'R': grip_frame('PIP'), 'L': left_hold('PIP')}
    X = {s: F0[s] @ (MIRROR if s == 'L' else Matrix.Identity(4)) for s in ('R', 'L')}
    arm = bpy.data.armatures.new('ARMS_Rig')
    rig = bpy.data.objects.new('ARMS_Rig', arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    def bone(name, head, tail, parent=None):
        b = eb.new(name)
        b.head, b.tail = V(head), V(tail)
        b.roll = 0
        if parent:
            b.parent = eb[parent]
        b.use_connect = False
        return b
    bone('Root', (0, -0.3, -0.3), (0, -0.2, -0.3))
    bone('Camera', (0, 0, 0.05), (0, 0.1, 0.05), 'Root')
    bone('Weapon', (0, 0, 0), (0, 0.1, 0), 'Root')
    mag0 = V(WEAPONS['PIP']['mag'])
    bone('Mag', mag0, mag0 + V((0, 0, -0.07)), 'Weapon')
    RIG['mag0'] = mag0
    RIG['F0'] = F0
    RIG['S0'], RIG['E0'], RIG['W0'] = {}, {}, {}
    for side in ('R', 'L'):
        Xs = X[side]
        wr = Xs @ WRIST
        RIG.setdefault('X', {})[side] = Xs
        s, e = two_bone(SH[side], wr, HINT[side], pref=hand_axes(side)[0])
        RIG['S0'][side], RIG['E0'][side], RIG['W0'][side] = s, e, wr
        bone('UPPERARM_' + side, s, e, 'Weapon')
        bone('FOREARM_' + side, e, wr, 'Weapon')
        bone('HAND_' + side, wr, Xs @ PALM_C, 'Weapon')
        zr = (Xs.to_3x3() @ V((0, 0, 1))).normalized()          # toward the index / thumb side of the hand
        for dn in DIGITS:
            J = [Xs @ p for p in digit_joints(side, dn, X)]
            par = 'HAND_' + side
            for i in (1, 2, 3):
                par = bone('%s%d_%s' % (dn, i, side), J[i - 1], J[i], par).name
            ax = digit_axis(side, J, Xs)
            d0 = (J[1] - J[0]).normalized()
            sp = d0.cross(ax).normalized()                      # back of the digit: spreading turns about it
            if sp.cross(d0).dot(zr) < 0:
                sp = -sp
            RIG.setdefault('J', {}).setdefault(side, {})[dn] = J
            RIG.setdefault('AX', {}).setdefault(side, {})[dn] = (ax, sp)
            # how far each joint is bent at rest (deg; the knuckle against the palm's own curve round the grip)
            G, (th, g) = ANAT[side]['grip'], ANAT[side]['mcp']
            m = (Xs.to_3x3() @ V((-(G['hx'] + g) * math.sin(D(th)), (G['hy'] + g) * math.cos(D(th)), 0))).normalized()
            dd = [m] + [(J[i + 1] - J[i]).normalized() for i in range(3)]
            RIG.setdefault('REST', {}).setdefault(side, {})[dn] = tuple(
                math.degrees(math.atan2(a.cross(b).dot(ax), a.dot(b))) for a, b in zip(dd, dd[1:]))
    bpy.ops.object.mode_set(mode='OBJECT')
    assert len(arm.bones) == 40, len(arm.bones)
    names = [b.name for b in arm.bones]

    # one mesh: both gloves, cuffs, forearms and upper sleeves
    A = ArmMesh(pal, names)
    for side in ('R', 'L'):
        glove(A, side, X)
        s, e, wr = RIG['S0'][side], RIG['E0'][side], RIG['W0'][side]
        fd = (e - wr).normalized()
        up = V((0, 0, 1))
        _, n0, l0 = hand_axes(side)
        dor = (-n0 - fd * (-n0).dot(fd)).normalized()
        rad = (-l0 - fd * (-l0).dot(fd) - dor * (-l0).dot(dor)).normalized()
        # the camera as the forearm sees it in a long-gun hold (the forearm rolls with the hand): the bracer faces both
        Wl = Matrix.Translation(V(CARRY['rifle']))
        Fl = Wl @ (left_hold('RIVET') if side == 'L' else grip_frame('RIVET'))
        cam_l = (Fl @ RIG['F0'][side].inverted()).inverted() @ CAM_RIG
        forearm(A, side, wr, fd, rad, dor, (CAM_RIG, cam_l))
        ud = (s - e).normalized()
        L = (s - e).length
        u2 = (up - ud * up.dot(ud)).normalized()
        prof = [(-0.036, 0.0, 0.0), (-0.028, 0.034, 0.032), (0.000, 0.0465, 0.0445), (L + 0.02, 0.050, 0.048), (L + 0.03, 0.0, 0.0)]
        rings = []
        for t, a, b in prof:
            c = e + ud * t
            rings.append([c] if a < 1e-7 else [c + ud.cross(u2) * (a * math.cos(2 * math.pi * k / 8)) + u2 * (b * math.sin(2 * math.pi * k / 8)) for k in range(8)])
        A.loft(rings, [COL['upper']] * len(rings), 'UPPERARM_' + side, 'upper arms')
    bm, sl = A.bm, A.sl
    ib_lib.ZFIGHT_TOL = GUN_ZFIGHT_TOL          # a viewmodel like the guns: the same fine tolerance
    try:
        check_zfight('ARMS', bm, sl)
    finally:
        ib_lib.ZFIGHT_TOL = WORLD_ZFIGHT_TOL
    me = bpy.data.meshes.new('ARMS')
    obj = bpy.data.objects.new('ARMS', me)
    bpy.context.scene.collection.objects.link(obj)
    for n in names:
        obj.vertex_groups.new(name=n)
    bm.to_mesh(me)
    bm.free()
    obj.data.materials.append(pal.material)
    # palette UVs, white vertex colour, smooth gloves and digits / crisp armour edges, then one ink shell per piece
    b2 = bmesh.new()
    b2.from_mesh(obj.data)
    uvl = b2.loops.layers.uv.get('UVMap') or b2.loops.layers.uv.new('UVMap')
    col = b2.loops.layers.float_color.new('Col')
    sl2 = b2.faces.layers.int.get('shape_id')
    for f in b2.faces:
        u, v = pal.uv(f.material_index)
        f.smooth = True
        for lp in f.loops:
            lp[uvl].uv = (u, v)
            lp[col] = (1.0, 1.0, 1.0, 1.0)
    for e in b2.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
        elif e.link_faces[0][sl2] not in A.soft and e.calc_face_angle(0.0) > math.radians(40):
            e.smooth = False        # shells: crisp rims, steps and pad edges (gloves stay fully smooth)
    b2.to_mesh(obj.data)
    b2.free()
    arms_hull(obj, pal, ARM_HULL_T, A.nohull)
    me = obj.data
    sn = me.attributes['snor'].data
    hl = me.attributes['_HULL'].data
    ln = []
    for lp in me.loops:
        vi = lp.vertex_index
        n = sn[vi].vector
        ln.append(tuple(n) if n.length > 0.5 and hl[vi].vector.length == 0 else (0.0, 0.0, 0.0))
    me.normals_split_custom_set(ln)
    me.attributes.remove(me.attributes['snor'])
    cnt = {}
    sla = me.attributes['shape_id'].data
    for p in me.polygons:
        g = A.group[sla[p.index].value]
        cnt[g] = cnt.get(g, 0) + len(p.vertices) - 2
    print('ARMS: %d triangles incl. outline shell (%s)' % (sum(cnt.values()), ', '.join('%s %d' % kv for kv in sorted(cnt.items()))))
    print('ARMS: bracer faces %s' % ', '.join('%s views %s centre %.0f' % (sd, ' / '.join('%.0f' % a for a in v[0]), v[1]) for sd, v in FORE_VIEW.items()))
    for p in me.polygons:
        p.material_index = 0
    me.color_attributes.active_color = me.color_attributes['Col']
    obj.parent = rig
    mod = obj.modifiers.new('rig', 'ARMATURE')
    mod.object = rig
    return rig, obj


# ================================================================ timing and holds: clip lengths, per-class handling, where the hands sit on each weapon
FPS = 30
# Timing from src/data/weapons.js (fire = one cycle 60/rpm; burst weapons: one burst; reload seconds).
# style: reload choreography. charge: (point, pull) the support hand works after a reload (slide, handle, bolt).
# carry: where the whole viewmodel sits (rig space) so long guns tuck their stocks off-screen.
ANIM = {
    'PIP': {'fire': 60 / 450, 'reload': 1.1, 'style': 'pistol', 'charge': ((0, -0.068, 0.044), (0, -0.030, 0))},
    # Wyrmforged: very fast. Fire clip = one shot (trigger, small muzzle kick, cylinder indexes 60 deg), 2 frames < 0.08 s
    'HANDCANNON': {'fire': 60 / 750, 'reload': 2.2, 'style': 'revolver', 'heavy': 1.6,
                   'handling': {'kick': {'loc': (0.0, -0.005, 0.0015), 'rot': (1.0, 0.0, 0.0)}}},
    'TWINTAP': {'fire': 60 / 300, 'reload': 1.3, 'burst': 2, 'gap': 0.06, 'style': 'pistol', 'charge': ((0, -0.066, 0.050), (0, -0.030, 0))},
    'BUZZ': {'fire': 60 / 900, 'reload': 1.6, 'style': 'smg', 'charge': ((-0.036, 0.150, 0.060), (0, -0.060, 0))},
    'WHISK': {'fire': 60 / 1100, 'reload': 1.4, 'style': 'smg', 'charge': ((0, -0.086, 0.050), (0, -0.035, 0))},
    'HORNET': {'fire': 60 / 750, 'reload': 1.8, 'style': 'smg', 'charge': ((-0.034, 0.206, 0.072), (0, -0.070, 0))},
    'RIVET': {'fire': 60 / 600, 'reload': 2.0, 'style': 'rifle', 'charge': ((0, -0.118, 0.054), (0, -0.045, 0))},
    'TRIPLET': {'fire': 0.32, 'reload': 2.2, 'burst': 3, 'gap': 0.06, 'style': 'rifle', 'charge': ((-0.034, -0.004, 0.050), (0, -0.060, 0))},
    'LONGTOM': {'fire': 60 / 240, 'reload': 2.4, 'style': 'rifle', 'heavy': 0.6, 'charge': ((0, -0.120, 0.054), (0, -0.045, 0))},
    'BRICK': {'fire': 60 / 500, 'reload': 3.4, 'style': 'rifle', 'heavy': 0.5, 'charge': ((0.036, -0.010, 0.030), (0, -0.060, 0))},
    'NEEDLE': {'fire': 60 / 45, 'reload': 3.0, 'style': 'bolt', 'heavy': 1.4},
    # round 3: Reload of a 'shell' gun is ONE shell (the game loops it per shell); 'pump' fire works the forend
    'SCRAPPER': {'fire': 60 / 70, 'reload': 0.5, 'style': 'shell', 'heavy': 1.2},
    'THUNDER': {'fire': 60 / 240, 'reload': 2.6, 'style': 'rifle', 'heavy': 0.9, 'charge': ((-0.030, -0.010, 0.050), (0, -0.060, 0))},
    'VANGUARD': {'fire': 60 / 480, 'reload': 2.3, 'style': 'rifle', 'heavy': 0.5, 'charge': ((-0.036, 0.090, 0.046), (0, -0.050, 0))},
    'RAILSPIKE': {'fire': 60 / 70, 'reload': 2.6, 'style': 'rifle', 'heavy': 1.0, 'charge': ((0, -0.120, 0.050), (0, -0.040, 0))},
    # round 5 launchers: the support hand swaps the cassette under the frame, then works the arming lever / housing latch
    'HOTHEAD': {'fire': 60 / 120, 'reload': 3.2, 'style': 'rifle', 'heavy': 1.3, 'charge': ((-0.034, -0.110, 0.034), (0, -0.040, 0))},
    'MURMUR': {'fire': 1.0, 'reload': 3.4, 'style': 'rifle', 'heavy': 1.6, 'charge': ((-0.034, -0.110, 0.030), (0, -0.040, 0))},
}

# ---------------------------------------------------------------- handling: data-driven per weapon class
# Every action of a weapon is generated from its class's HANDLING entry (cls from build_<weapon>'s info, the same
# as src/data/weapons.js), so a NEW GUN GETS GOOD HANDLING BY DEFAULT: give it a cls ('pistol', 'smg', 'rifle',
# 'sniper'; anything else falls back to HANDLING_FALLBACK) and an ANIM row with its timings. To tune one gun,
# put a 'handling' dict in its ANIM row: keys there replace the class's keys (dicts are merged one level deep),
# e.g. ANIM['BRICK']['handling'] = {'kick': {'loc': (0, -0.03, 0.006)}}.
# A pose is (loc m, rot deg) of the whole weapon about the grip (rig space: +y forward, +z up; rot = pitch up,
# roll right-side-down, yaw muzzle-left), on top of 'carry'. 'heavy' (ANIM) scales kick and slows the settle.
#   carry     where the viewmodel sits (long guns tuck their stocks off-screen)
#   idle      breathing loop (2 s): two extreme poses visited at 1/4 and 3/4 (a slow figure-8)
#   draw      from -> over (overshoot past rest) -> settle (small counter-swing) -> rest, in 0.3 s
#   holster   rest -> dip -> to, in 0.2 s
#   kick      fire: loc/rot at the shot, then 'recover' (overshoot forward) before rest
#   reload    tilt: weapon pose while the support hand works; seat: bump when the mag seats; low: where the
#             support hand fetches a fresh mag (rig space)
#   sprint    style 'high' (pistols: muzzle up near the face, support arm pumping) or 'low' (long guns: canted
#             across the chest, both hands on); a / b: the two poses of the 0.6 s loop (footfalls);
#             idx / lift: trigger finger off the trigger, straight along the frame (knuckle curl / spread up the frame);
#             pump: the free support fist for the 'high' style ((NDC x, y, depth m), palm direction, wrist bend)
#   slide     a / b: the tucked, canted gun; hand: the free support hand out for balance (as pump), fingers open;
#             hint: where its elbow points
# Finger poses are not in these tables: holds are fitted on the weapon (fit_support, fit_digits), free hands take
# a SHAPES name (see the end of this file).
HANDLING_BASE = {
    'carry': (0.0, -0.17, -0.010),
    'idle': (((0.0005, 0.0015, 0.0035), (1.0, 0.4, -0.5)), ((-0.0005, 0.0010, 0.0020), (0.6, -0.4, 0.3))),
    'draw': {'from': ((0.06, -0.08, -0.20), (-48, -26, 26)), 'over': ((0.0, 0.004, 0.006), (4.0, 1.5, -1.5)),
             'settle': ((0.0, -0.001, -0.002), (-1.2, -0.5, 0.4))},
    'holster': {'dip': ((0.004, -0.010, -0.012), (-6, -4, 3)), 'to': ((0.07, -0.08, -0.21), (-50, -28, 28))},
    'kick': {'loc': (0.0, -0.016, 0.003), 'rot': (3.5, 0.6, 0.0), 'recover': ((0.0, 0.0025, -0.0008), (-0.8, 0.0, 0.0))},
    'reload': {'tilt': ((-0.010, -0.020, 0.030), (10, 26, -16)), 'seat': ((-0.010, -0.017, 0.037), (14, 26, -18)),
               'low': (-0.14, -0.08, -0.46)},
    'sprint': {'style': 'low', 'a': ((-0.030, 0.000, 0.035), (-24, -34, 50)), 'b': ((-0.024, 0.002, 0.022), (-27, -31, 53)),
               'idx': -6, 'lift': 13},
    # slide: gun poses a / b; hand: the free support hand at both ends of the loop ((NDC x, y, depth m), palm
    # direction (rig space), (wrist flex, deviation) deg)
    'slide': {'a': ((-0.030, -0.010, 0.000), (8, -28, 6)), 'b': ((-0.028, -0.014, -0.006), (7, -30, 7)),
              'hand': (((-0.56, -0.62, 0.52), (-0.25, 0.30, -1.0), (-10, 6)), ((-0.54, -0.58, 0.52), (-0.25, 0.35, -1.0), (-12, 6))),
              'hint': (-1.0, 0.0, -0.5)},
}
HANDLING = {
    'pistol': {
        'carry': (0.0, -0.01, 0.0),
        'idle': (((0.0006, 0.0018, 0.0040), (1.3, 0.5, -0.6)), ((-0.0006, 0.0012, 0.0022), (0.7, -0.5, 0.4))),
        'draw': {'from': ((0.05, -0.10, -0.22), (-62, -18, 34)), 'over': ((0.0, 0.006, 0.009), (6.0, 1.0, -2.0)),
                 'settle': ((0.0, -0.001, -0.002), (-1.6, -0.4, 0.5))},
        'holster': {'dip': ((0.004, -0.008, -0.010), (-8, -3, 4)), 'to': ((0.06, -0.10, -0.22), (-62, -18, 34))},
        'kick': {'loc': (0.0, -0.013, 0.004), 'rot': (6.5, 0.0, 0.0), 'recover': ((0.0, 0.002, -0.001), (-1.2, 0.0, 0.0))},
        'reload': {'tilt': ((0.0, -0.030, 0.030), (14, 28, -18)), 'seat': ((0.0, -0.027, 0.036), (18, 28, -20)),
                   'low': (-0.12, -0.10, -0.42)},
        # high ready: pistol raised beside the face, muzzle straight up (12 o'clock: pitch 90, no roll; the yaw turns
        # it about the barrel to show its left side); the free fist pumps at the lower left ((NDC x, y, depth), palm, bend)
        'sprint': {'style': 'high', 'a': ((0.030, -0.080, 0.020), (90, 0, 18)), 'b': ((0.032, -0.076, 0.010), (88, 0, 20)),
                   'idx': -6, 'lift': 14,
                   'pump': (((-0.62, -0.78, 0.46), (0.6, 0.2, -0.4), (10, 0)), ((-0.72, -1.25, 0.44), (0.6, -0.2, -0.4), (10, 0)))},
        'slide': {'a': ((0.000, -0.060, -0.045), (4, -30, 8)), 'b': ((0.002, -0.064, -0.051), (3, -32, 9))},
    },
    'smg': {
        'carry': (0.0, -0.13, -0.006),
        'kick': {'loc': (0.0, -0.011, 0.0025), 'rot': (2.4, 0.5, 0.0), 'recover': ((0.0, 0.0015, -0.0005), (-0.5, 0.0, 0.0))},
        'sprint': {'style': 'low', 'a': ((-0.030, 0.000, 0.030), (-22, -32, 48)), 'b': ((-0.024, 0.002, 0.018), (-25, -29, 51)),
                   'idx': -6, 'lift': 13},
    },
    'rifle': {},
    'shotgun': {'kick': {'loc': (0.0, -0.024, 0.006), 'rot': (7.0, 1.0, 0.0), 'recover': ((0.0, 0.003, -0.001), (-1.4, 0.0, 0.0))}},
    'melee': {'carry': (0.0, -0.02, 0.0)},
    'rocket': {'carry': (0.0, -0.08, -0.010), 'kick': {'loc': (0.0, -0.030, 0.008), 'rot': (8.0, 1.2, 0.0), 'recover': ((0.0, 0.004, -0.001), (-1.6, 0.0, 0.0))}},
    'sniper': {'carry': (0.0, -0.17, -0.010), 'kick': {'loc': (0.0, -0.022, 0.004), 'rot': (5.0, 0.8, 0.0), 'recover': ((0.0, 0.003, -0.001), (-1.0, 0.0, 0.0))}},
}
HANDLING_FALLBACK = 'rifle'


def handling(wid):
    """The handling table of one weapon: base <- its class <- its ANIM['handling'] overrides."""
    cls = WEAPONS[wid]['cls']
    h = {}
    for layer in (HANDLING_BASE, HANDLING.get(cls, HANDLING[HANDLING_FALLBACK]), ANIM.get(wid, {}).get('handling', {})):
        for k, v in layer.items():
            h[k] = dict(h[k], **v) if isinstance(v, dict) and isinstance(h.get(k), dict) else v
    return h


CARRY = {c: HANDLING[c].get('carry', HANDLING_BASE['carry']) for c in HANDLING}


# Support-hand holds. A hold is the support glove's grip axis (index end) and palm direction in weapon space
# (hold_frame); the frame is then slid so the palm touches the part and centred on it (fit by ray casts on
# the gun's visible surface, then seated: slid in until the palm or a knuckle presses on it), and every digit
# closes joint by joint until it meets the part (fit_digits).
# two-hand pistol hold: support glove offset (m) and rotation (deg) from the grip frame (its rest pose: no fit)
PISTOL_LEFT = (-0.018, 0.018, -0.016, 8, 0, 14)
GUARD_THUMB = (42.0, 52.0)              # handguards: the support thumb swings toward the muzzle and reaches round the near side (deg)
GUARD_PALM = V((0.17, 0.0, -0.98))      # handguards: palm under, knuckles at the lower far corner, fingers up the far side, thumb up the near side


def hold_frame(o, axis, palm):
    """Support-glove rest frame: model z (grip axis, index end) along axis, the palm side toward palm."""
    z = V(axis).normalized()
    x = -(V(palm) - z * V(palm).dot(z)).normalized()
    M = Matrix((x, z.cross(x), z)).transposed().to_4x4()
    M.translation = V(o)
    return M


def _gun_bvh(wid):
    info = WEAPONS[wid]
    if 'bvh' not in info:
        bm = bmesh.new()
        bm.from_mesh(bpy.data.objects['WPN_' + wid].data)
        hl = bm.verts.layers.float_vector['_HULL']
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[hl].length > 0], context='VERTS')
        info['bvh'] = BVHTree.FromBMesh(bm)
        bm.free()
    return info['bvh']


def reach(wid, o, d, far=0.046):
    """Distance from o (inside a part) out to the gun's visible surface along d."""
    d = V(d).normalized()
    hit = _gun_bvh(wid).ray_cast(V(o) + d * far, -d, far)
    return far - hit[3] if hit[0] is not None else 0.0


def left_hold(wid):
    """Support-hand frame in weapon space for the hold pose (the fitted frame once fit_support ran)."""
    info = WEAPONS[wid]
    if 'hold_L' in info:
        return info['hold_L']
    if info['cls'] == 'pistol':
        o = PISTOL_LEFT
        return mat_trs(o[:3], (-info['rake'] + o[3], o[4], o[5]))
    if info['cls'] == 'melee':        # two-handed: the support hand on the handle below the right one (else: free)
        return mat_trs((0, 0, info['hold2']), (0, 0, 0)) if 'hold2' in info else None
    if 'fore' in info:
        y, z = info['fore']
        return hold_frame((0, y, z - 0.004), (0, 0, 1), (-1, 0, 0))
    return hold_frame(info['guard'], (0, 1, 0), GUARD_PALM)


def palm_points(side):
    """Rest-space points that seat a hand on a part: the inside of the palm (radius 0) and the knuckle balls."""
    G, X = ANAT[side]['grip'], RIG['X'][side]
    lo = ANAT[side]['palm'][-1][0]
    pts = [(X @ gpt(G, th, z, G0), 0.0) for th in (max(lo, -60), -40, -20, 0, 18, 34) for z in (-0.012, -0.032, -0.052, -0.072)]
    return pts + [(RIG['J'][side][fn][0], FING[fn][1][0]) for fn in FINGERS]


def seat(side, sd, F, far=0.030, deep=0.012):
    """Slide a hand frame F (object space) along its palm direction, from clear of the object in until the palm
    or a knuckle presses on it; returns the seated frame."""
    pts, Hi = palm_points(side), RIG['F0'][side].inverted()
    palm = -F.col[0].xyz if side == 'L' else F.col[0].xyz
    best, d = None, far
    while d >= -deep:
        Fd = F.copy()
        Fd.translation = F.translation + palm * d
        H = Fd @ Hi
        if max(r - sd(H @ q) for q, r in pts) > FIT_SINK:
            break
        best = d
        d -= 0.001
    Fd = F.copy()
    Fd.translation = F.translation + palm * (best if best is not None else 0.0)
    return Fd


def fit_support():
    """Seat each long gun's support frame on its foregrip / handguard (centred across the part, the palm pressed
    on it), then close every hand on its weapon: info['dig_R'] / info['dig_L'] are the digit angles of the hold
    (fit_digits). The strong hand's fingers keep their modelled place on a gun's grip and trigger."""
    for wid, info in WEAPONS.items():
        if info['cls'] in ('pistol', 'melee'):
            continue
        F = left_hold(wid)
        o, x, y, z = F.translation.copy(), F.col[0].xyz, F.col[1].xyz, F.col[2].xyz
        hs = [o + z * FING[fn][0] for fn in FINGERS]     # sample the part across the hand, index to pinky
        rf = sum(reach(wid, h, y) for h in hs) / 4
        rb = sum(reach(wid, h, -y) for h in hs) / 4
        F = F.copy()
        F.translation = o + y * max(-0.008, min(0.008, (rf - rb) / 2))
        info['hold_L'] = seat('L', bvh_sd(hold_bvh(wid)), F)
        info.pop('bvh', None)
    for wid, info in WEAPONS.items():
        sd = bvh_sd(hold_bvh(wid))
        cls = info['cls']
        if cls == 'melee':               # both hands wrap the handle
            info['dig_R'] = fit_digits('R', sd, grip_frame(wid) @ RIG['F0']['R'].inverted())
        elif cls != 'pistol':            # no support hand under the strong thumb: it closes on the grip
            info['dig_R'] = fit_digits('R', sd, grip_frame(wid) @ RIG['F0']['R'].inverted(), ('THUMB',))
        FL = left_hold(wid)
        if FL is not None and cls != 'pistol':      # pistols: the support hand's rest pose IS the two-hand hold
            # on a handguard the thumb turns to point forward along the near side before it closes
            guard = 'guard' in info and 'fore' not in info and cls != 'melee'
            info['dig_L'] = fit_digits('L', sd, FL @ RIG['F0']['L'].inverted(), spread={'THUMB': GUARD_THUMB[0]} if guard else None,
                                       wrap={'THUMB': GUARD_THUMB[1]} if guard else None)
        if os.environ.get('IB_POSE_REPORT'):
            for sd_ in 'RL':
                if 'dig_' + sd_ in info:
                    print('FIT %-10s %s %s' % (wid, sd_, '  '.join('%s %s' % (k[:2], ','.join('%+.0f' % x for x in v[:3])) for k, v in info['dig_' + sd_].items())))


def T(v):
    return Matrix.Translation(V(v))


def seg_delta(a0, b0, a, b):
    q = (b0 - a0).rotation_difference(b - a)
    return T(a) @ q.to_matrix().to_4x4() @ T(-a0)


def hand_axes(side):
    """Rest hand axes in rig space: a (wrist -> middle knuckle), n (palm normal, back of the hand -> palm),
    l (across the wrist, thumb side -> little finger side). The left set is mirrored (left-handed basis)."""
    if side in RIG.get('axes', {}) and RIG['axes'].get('X' + side) is RIG['X'][side]:
        return RIG['axes'][side]
    G = ANAT[side]['grip']
    a = (finger_joints(side, 'MIDDLE')[0] - WRIST).normalized()
    n = V((0.0, G['cy'], PALM_C.z)) - PALM_C
    n = (n - a * n.dot(a)).normalized()
    l = n.cross(a)
    X3 = RIG['X'][side].to_3x3()
    out = tuple((X3 @ v).normalized() for v in (a, n, l))
    RIG.setdefault('axes', {})[side] = out
    RIG['axes']['X' + side] = RIG['X'][side]
    return out


# ================================================================ finger poses: shapes of a free hand, contact fits on things
# A digit pose is (knuckle, joint 2, joint 3[, spread]) in degrees FROM THE REST POSE (the modelled hold), positive
# = closing; a hand pose is {digit: pose} (missing digits stay at rest). Three ways to get one:
#   hand_shape(side, name)      a named shape of a free hand (SHAPES: absolute flexion, so both hands match)
#   fit_digits(side, sd, H)     close the digits on an object until each phalanx touches it
#   literal dicts               for one-off tweaks
# Flexion limits (deg): fingers absolute (0 = in line with the palm), thumb from its rest pose.
FLEX_LIM = {'F': ((-10, 86), (2, 106), (2, 70)), 'T': ((-26, 24), (-28, 46), (-36, 58))}
# shapes: 'f' = finger flexion (knuckle, joint 2, joint 3), 'add' = extra flexion per finger index -> pinky,
# 'spread' = per finger (toward the thumb +), 'thumb' = from rest
SHAPES = {
    'open': {'f': (6, 12, 8), 'add': (0, 2, 6, 12), 'spread': (7, 2, -3, -9), 'thumb': (-20, -8, -6)},
    'relaxed': {'f': (20, 34, 20), 'add': (-4, 0, 5, 10), 'spread': (4, 1, -2, -6), 'thumb': (-10, 0, 4)},
    'fist': {'f': (80, 98, 60), 'add': (0, 0, 0, 0), 'spread': (0, 0, 0, 0), 'thumb': (6, 16, 30)},
    'point': {'f': (0, 10, 6), 'add': (0, 0, 0, 0), 'spread': (0, 0, 0, 0), 'thumb': (0, 0, 0)},
}


def hand_shape(side, name, k=1.0):
    """Digit angles (from rest) of a named free-hand shape; k < 1 stops short of it (blend from the rest pose)."""
    sh = SHAPES[name]
    out = {}
    for i, fn in enumerate(FINGERS):
        rest = RIG['REST'][side][fn]
        out[fn] = tuple((sh['f'][j] + sh['add'][i] * (0.6 if j == 0 else 1.0) - rest[j]) * k for j in range(3)) + (sh['spread'][i] * k,)
    out['THUMB'] = tuple(c * k for c in sh['thumb']) + (0.0,)
    return out


def digit_fk(side, dn, a):
    """Rest-space motion of the three phalanges of a digit for joint angles a (deg from rest[, spread])."""
    J, (ax, sp) = RIG['J'][side][dn], RIG['AX'][side][dn]
    M, out = Matrix.Identity(4), []
    for i in range(3):
        C = Matrix.Rotation(D(a[i]), 4, ax)
        if i == 0 and len(a) > 3 and a[3]:
            C = C @ Matrix.Rotation(D(a[3]), 4, sp)
        M = M @ T(J[i]) @ C @ T(-J[i])
        out.append(M)
    return out


def digit_limits(side, dn):
    """Joint limits of a digit as angles from rest."""
    if dn == 'THUMB':
        return FLEX_LIM['T']
    rest = RIG['REST'][side][dn]
    return tuple((lo - rest[i], hi - rest[i]) for i, (lo, hi) in enumerate(FLEX_LIM['F']))


FIT_STEP, FIT_SINK = 2.0, 0.0012        # sweep step (deg); how far a phalanx may sink into what it holds (m)


def fit_digits(side, sd, H, digits=DIGITS, spread=None, wrap=None):
    """Close the digits of a hand on an object: sd(p) is the signed distance (m) to the object in its own space,
    H takes the rig's rest space to that space with the hand placed (frame @ rest frame inverse). Each digit
    opens, then knuckle, joint 2 and joint 3 close in turn until a phalanx beyond the joint presses into the
    object (nothing there up to the joint's limit: it keeps its rest angle). spread: {digit: deg} set first.
    wrap: {digit: deg}: that digit's knuckle starts that far PAST the rest pose, on the far side of the object, and
    comes back until it touches (a thumb reaching round a handguard). Returns {digit: angles from rest}."""
    out = {}
    for dn in digits:
        J = RIG['J'][side][dn]
        rad = THUMB_R if dn == 'THUMB' else FING[dn][1]
        lim = digit_limits(side, dn)
        sp = (spread or {}).get(dn, 0.0)
        pts = []                         # per phalanx: (rest point, radius)
        for i in range(3):
            fr = (0.3, 0.65, 1.0) if i == 2 else (0.3, 0.55, 0.8, 1.0)
            pts.append([(J[i] + (J[i + 1] - J[i]) * f, (rad[i] + (rad[i + 1] - rad[i]) * f) * 0.93) for f in fr])
        a = [lim[0][0] * 0.75 if dn == 'THUMB' else max(lim[0][0], -RIG['REST'][side][dn][0]),
             max(lim[1][0], -22.0) if dn == 'THUMB' else lim[1][0], lim[2][0] if dn != 'THUMB' else max(lim[2][0], -20.0)]

        def pen(j):                      # deepest any phalanx beyond joint j sinks in
            Ms = digit_fk(side, dn, a + [sp])
            links = range(max(j, 1 if dn == 'THUMB' else 0), 3)
            return max(r - sd(H @ Ms[i] @ p) for i in links for p, r in pts[i])
        for j in range(3):
            lo, hi = lim[j]
            if j == 0 and dn in (wrap or {}):
                a[0] = wrap[dn]
                while pen(0) > FIT_SINK and a[0] < wrap[dn] + 24:       # clear on the far side first
                    a[0] += FIT_STEP
                while a[0] - FIT_STEP >= 0.0:
                    a[0] -= FIT_STEP
                    if pen(0) > FIT_SINK:
                        a[0] += FIT_STEP
                        break
                a[1], a[2] = 0.0, 8.0            # the rest of the digit lies along the part, a little bent
                break
            p0 = pen(j)
            if j == 0:                   # start clear of the object: open the knuckle further if it is not
                while p0 > FIT_SINK and a[0] - FIT_STEP >= lo:
                    a[0] -= FIT_STEP
                    p0 = pen(0)
            best, ang, hit = a[j], a[j], False
            while ang + FIT_STEP <= hi:
                ang += FIT_STEP
                a[j] = ang
                if pen(j) > max(p0 + 0.0006, FIT_SINK):
                    hit = True
                    break
                best = ang
            a[j] = best if hit else min(max(0.0, lo), hi)        # nothing to close on: the joint's rest angle
        out[dn] = (a[0], a[1], a[2], sp)
    return out


def bvh_sd(bvh):
    """Signed distance function (outside +) of a mesh BVH."""
    def sd(p):
        loc, nor, idx, d = bvh.find_nearest(p, 0.06)
        if loc is None:
            return 0.06
        return d if (p - loc).dot(nor) >= 0 else -d
    return sd


def can_sd(radius, half, frame):
    """Signed distance to an upright can (cylinder along z) placed by frame."""
    Fi = frame.inverted()

    def sd(p):
        q = Fi @ p
        return max(math.hypot(q.x, q.y) - radius, abs(q.z) - half)
    return sd


def hold_bvh(wid, gun=True, mag=True):
    """BVH of a weapon's visible surface in weapon space: the gun and / or its magazine at its socket (the
    magazine alone: in its own space)."""
    info = WEAPONS[wid]
    key = 'bvh%d%d' % (gun, mag)
    if key not in HOLD_BVH.setdefault(wid, {}):
        bm = bmesh.new()
        for name, off, on in (('WPN_' + wid, V((0, 0, 0)), gun), ('WPN_%s_Mag' % wid, V(info['mag']) if gun else V((0, 0, 0)), mag)):
            ob = bpy.data.objects.get(name)
            if not on or ob is None:
                continue
            n0 = len(bm.verts)
            bm.from_mesh(ob.data)
            bm.verts.ensure_lookup_table()
            for v in bm.verts[n0:]:
                v.co += off
        hl = bm.verts.layers.float_vector.get('_HULL')
        if hl is not None:
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[hl].length > 0], context='VERTS')
        bm.normal_update()
        HOLD_BVH[wid][key] = BVHTree.FromBMesh(bm)
        bm.free()
    return HOLD_BVH[wid][key]


HOLD_BVH = {}
