"""INKBOLT weapons: the first-person arms (gloves, forearms, sleeves) and their rig.
Built by fam_weapons.py; shape kit and gun parts in wpn_core.py."""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from ib_lib import *  # noqa: F401,F403
import ib_lib
from wpn_core import *  # noqa: F401,F403


# ================================================================ arms: gloves, sleeves, 22-bone rig
# Hand frame (right hand): origin = grip anchor (web of the hand), z = grip axis up, y = forward, x = right.
# Tactical glove, two layers:
#  * the palm is ONE closed surface: anatomical primitives (palm slab wrapped round the grip, padded back panel,
#    thenar + thumb metacarpal, heel, wrist ball, a short stub at each finger root) unioned by a voxel remesh,
#    relaxed and decimated to budget. The back panel is painted on the dense union as palette UVs (the decimator
#    keeps UV seams, so its border stays clean); shading normals come from the dense union; skin weights come
#    from the nearest source primitive (falling off smoothly only between a bone and its parent).
#  * fingers and the thumb's phalanges are clean lofted digits (Body.digit), each rigid on its own bone (fingers
#    are one bone each, so a digit never deforms) and outlined by its own ink shell, which draws the gaps between
#    fingers. Colour bands segment them: padded first segment (glove2), dark stretch creases at the joints
#    (glove3), reinforced fingertips (glove4). Hard moulded armour (glove4, own shells): one knuckle guard across
#    the four knuckles (Body.knuckle_guard), a plate on the back of the hand and a thumb knuckle pad (Body.pad).
#    Each digit's root sinks into its stub in the palm union.
# Forearm (rigid on FOREARM, see forearm_shells): an anatomical taper (flat narrow wrist, muscle belly toward the
# elbow) under a sleeve pushed up into diagonal folds, a wrist lame, a vambrace lame and raised armour plates.
# The palm's rounded wrist turns inside the wrist lame's open mouth (ball and socket), so wrist bends never
# stretch or cut the cuff. Posing (solve): the forearm rolls with the hand (forearm_delta: the wrist only bends,
# never twists) and the elbow swings round the shoulder-wrist axis to line the forearm up with the hand
# (two_bone pref); free hands (slide, sprint pump) are built from their forearm (free_hand). IB_POSE_REPORT=1
# prints per action the wrist bend range and where the muzzle points on screen (0 = straight up).
# Triangle split is printed by the build (ARMS: ... digits / pads / gloves ...).
from mathutils.bvhtree import BVHTree

FINGERS = ('INDEX', 'MIDDLE', 'RING', 'PINKY')
MIRROR = Matrix.Diagonal((-1, 1, 1, 1))
SH = {'R': V((0.20, -0.58, -0.30)), 'L': V((-0.42, -0.50, -0.28))}     # shoulders (off screen): support arm comes in from lower left
UPPER_LEN, FORE_LEN = 0.30, 0.29
# fingers: knuckle height on the grip, radius at MCP / PIP / DIP / tip, phalanx lengths (joint to joint)
FING = {'INDEX': (-0.0125, (0.0094, 0.0090, 0.0085, 0.0079), (0.041, 0.025, 0.016)),
        'MIDDLE': (-0.0320, (0.0098, 0.0094, 0.0088, 0.0082), (0.045, 0.028, 0.018)),
        'RING': (-0.0515, (0.0094, 0.0090, 0.0085, 0.0079), (0.043, 0.026, 0.017)),
        'PINKY': (-0.0705, (0.0084, 0.0080, 0.0076, 0.0071), (0.035, 0.021, 0.015))}
FLAT = 0.88             # finger section squashed along the grip axis: gaps between fingers survive the union
INDEX_TRIGGER = [(0.0240, 0.0440, -0.0150), (0.0090, 0.0565, -0.0170), (-0.0040, 0.0560, -0.0180)]
THUMB_R = (0.0118, 0.0112, 0.0106, 0.0098)
WRIST = V((0.019, HAND['cy'] - 0.053, -0.060))
PALM_C = V((0.014, HAND['cy'] - 0.012, -0.042))
# Per-glove anatomy in model space (a right hand round the grip section; the left glove is mirrored by its
# rest frame). grip: section the fingers wrap (the support glove closes round bigger parts: handguards,
# foregrips, the strong hand); palm: slab stations (angle, z top, z bottom, thickness); mcp: knuckles
# (angle, distance off the grip); thenar / heel: (angle, z, grow, radii); panel: angles.
# thumb: CMC, MCP, IP, tip as (angle, z, distance off the grip): the strong thumb wraps the back of the grip.
# The support thumb is modelled abducted, lying forward along the pistol frame under the strong thumb
# (given in the strong hand's frame), so the two-hand pistol hold is its undeformed rest pose; on foregrips
# it points forward along the grip, on handguards it tucks under with the palm.
ANAT = {
    'R': {'grip': {'hx': HAND['hx'], 'hy': HAND['hy'], 'cy': HAND['cy']}, 'mcp': (6.0, 0.0165), 'trigger': True,
          'palm': [(18, -0.003, -0.079, 0.020), (0, -0.001, -0.085, 0.023), (-30, 0.003, -0.090, 0.025), (-60, 0.007, -0.092, 0.023),
                   (-90, 0.010, -0.086, 0.018), (-118, 0.008, -0.062, 0.016), (-140, 0.003, -0.044, 0.014)],
          'thumb': [(-97, -0.033, 0.0103), (-147, -0.013, 0.0170), (167, -0.004, 0.0184), (142, -0.002, 0.0248)],
          'thenar': (-122, -0.026, 0.010, (0.011, 0.019, 0.020)), 'heel': (-55, -0.068, 0.012, (0.012, 0.020, 0.018)),
          'panel': (4, -46)},
    'L': {'grip': {'hx': 0.021, 'hy': 0.026, 'cy': HAND['cy']}, 'mcp': (6.0, 0.0165), 'trigger': False,
          'palm': [(18, -0.003, -0.079, 0.020), (0, -0.001, -0.085, 0.023), (-30, 0.000, -0.090, 0.025), (-55, -0.004, -0.090, 0.023),
                   (-78, -0.012, -0.082, 0.019)],
          'thumb_strong': [(-0.044, -0.036, -0.032), (-0.040, -0.012, -0.024), (-0.035, 0.016, -0.020), (-0.031, 0.036, -0.019)],
          'thenar': (-50, -0.016, 0.017, (0.012, 0.018, 0.016)), 'heel': (-58, -0.068, 0.012, (0.012, 0.020, 0.018)),
          'panel': (4, -46)},
}
GLOVE_VOXEL = 0.0008
GLOVE_TRIS = 320         # palm / back / thenar union per glove before its ink shell (x2 with it)
GLOVE_SMOOTH = 7
DIGIT_SIDES = 7
# finger rings: (joint, offset, radius factor, colour of the band that starts there): padded first segment,
# dark stretch crease over the middle knuckle, plain middle segment, crease + reinforced tip from the last joint
DIGIT_BANDS = [(0, -0.0030, 0.93, 'glove2'), (1, -0.0042, 0.97, 'glove3'), (1, 0.0040, 0.96, 'glove'),
               (2, -0.0034, 0.95, 'glove4'), (3, -0.0040, 0.99, 'glove4')]
THUMB_BANDS = [(0, -0.0030, 0.93, 'glove2'), (1, -0.0045, 0.97, 'glove3'), (1, 0.0042, 0.97, 'glove'),
               (2, -0.0080, 0.99, 'glove4'), (2, -0.0030, 0.99, 'glove4')]


def gpt(G, theta, gz, grow):
    """Point on the grip section (angle theta, 0 = right, 90 = front) grown outward by grow, at height gz."""
    t = D(theta)
    return V(((G['hx'] + grow) * math.cos(t), G['cy'] + (G['hy'] + grow) * math.sin(t), gz))


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


# ---------------------------------------------------------------- closed primitives
class Body:
    """Overlapping closed primitives of one glove; each carries its bone and palette colour."""

    def __init__(self, X):
        self.X = X
        self.parts = []
        self.hard = []        # rigid outlined shells: (rings in rig space, band colours, bone)

    def pad(self, c, n, along, w, l, h, bone, color, ch=0.0018, sink=0.003):
        """Hard moulded pad (rounded rectangle pillow) centred at c on a surface of normal n: its own ink shell."""
        n, along = V(n).normalized(), V(along)
        along = (along - n * along.dot(n)).normalized()
        side = n.cross(along)
        rect = [(w / 2, -l * 0.30), (w / 2, l * 0.30), (0, l / 2), (-w / 2, l * 0.30), (-w / 2, -l * 0.30), (0, -l / 2)]   # hex pillow
        ring = lambda dz, ins: [V(c) + n * dz + side * q[0] + along * q[1] for q in (inset2d(rect, ins) if ins > 0 else rect)]
        rings = [ring(-sink, 0.0), ring(h - ch, 0.0), ring(h, ch)]
        Xm = self.X
        self.hard.append(([[Xm @ p for p in r] for r in rings], [color, color, color], bone, False, (False, True)))   # base hidden

    def knuckle_guard(self, K, bone, h=0.0066, sink=0.0042, color='glove4'):
        """One moulded knuckle guard across the four knuckles (K: (centre, outward normal, finger direction, radius)
        index to pinky): a hard band with a raised bump over each knuckle and shallow valleys between, its own shell."""
        st = []
        for i, (c, n, d, r) in enumerate(K):
            st.append((c, n, d, r * 1.62, h))
            if i + 1 < len(K):
                c2, n2, d2, r2 = K[i + 1]
                st.append(((c + c2) / 2 + ((n + n2) / 2) * -0.0006, ((n + n2) / 2).normalized(), ((d + d2) / 2).normalized(), (r + r2) * 0.70, h * 0.62))
        (c0, n0, d0, w0, h0), (c1, *_) = st[0], st[1]
        (cz, nz, dz, wz, hz), (cy, *_) = st[-1], st[-2]
        st = [(c0 + (c0 - c1).normalized() * 0.0042, n0, d0, w0 * 0.82, h0 * 0.55)] + st + \
             [(cz + (cz - cy).normalized() * 0.0040, nz, dz, wz * 0.82, hz * 0.55)]
        rings = []
        for c, n, d, w, hh in st:
            n = V(n)
            d = (V(d) - n * V(d).dot(n)).normalized()
            q = [(-sink, 0.5), (hh * 0.62, 0.5), (hh, 0.22), (hh, -0.22), (hh * 0.62, -0.5), (-sink, -0.5)]
            rings.append([self.X @ (V(c) + n * a + d * (b * w)) for a, b in q])
        self.hard.append((rings, [color] * len(rings), bone, False, (True, True)))

    def digit(self, J, r, bone, bands, sides=DIGIT_SIDES, flat=FLAT, up=(0, 0, 1)):
        """A finger (or the thumb's phalanges) as one clean lofted tube through its joints J, radii r at the
        joints, rings from bands [(joint, offset m, radius factor, colour of the band that starts here)]:
        a negative offset sits back along the segment that ends at that joint. Rings near a joint lie in the
        joint's bisector plane so bends never fold; root and tip close with apexes (the tip rounded)."""
        J = [V(p) for p in J]
        dirs = [(J[i + 1] - J[i]).normalized() for i in range(len(J) - 1)]
        Z = V(up)

        def ring(c, n, rad):
            u = Z - n * Z.dot(n)
            u = u.normalized() if u.length > 1e-6 else n.orthogonal().normalized()
            s = n.cross(u)
            return [c + s * (rad * math.cos(2 * math.pi * (k + 0.5) / sides)) + u * (rad * flat * math.sin(2 * math.pi * (k + 0.5) / sides))
                    for k in range(sides)]
        rings, cols = [], []
        d0 = dirs[0]
        rings.append([J[0] - d0 * (r[0] * 0.80)])
        cols.append(bands[0][3])
        for i, off, rk, col in bands:
            if off < 0:
                d = dirs[max(0, i - 1)] if i > 0 else dirs[0]
            else:
                d = dirs[min(i, len(dirs) - 1)]
            c = J[i] + d * off
            n = d
            if 0 < i < len(J) - 1 and abs(off) < 0.0075:
                n = (dirs[i - 1] + dirs[i]).normalized()          # joint ring: bisector plane
            rings.append(ring(c, n, r[i] * rk))
            cols.append(col)
        dl = dirs[-1]
        rt = r[-1]
        rings.append(ring(J[-1] + dl * (rt * 0.42), dl, rt * 0.74))
        cols.append(cols[-1])
        rings.append([J[-1] + dl * (rt * 0.86)])
        Xm = self.X
        self.hard.append(([[Xm @ p for p in rr] for rr in rings], cols, bone, True, (True, True)))

    def _part(self, bone, color, prio):
        bm = bmesh.new()
        self.parts.append({'bm': bm, 'bone': bone, 'color': color, 'prio': prio})
        return bm

    def loft(self, rings, bone, color, prio=0):
        bm = self._part(bone, color, prio)
        vr = [[bm.verts.new(self.X @ V(p)) for p in r] for r in rings]
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

    def capsule(self, a, b, ra, rb, bone, color, up=(0, 0, 1), flat=1.0, seg=16, cap=5, prio=0):
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
        return self.loft(rings, bone, color, prio)

    def ellipsoid(self, c, radii, axes, bone, color, seg=16, prio=0):
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
        return self.loft(rings, bone, color, prio)


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


def glove_body(side, X):
    """All primitives of one glove in rig space (X: rest frames, the left one mirrored)."""
    an = ANAT[side]
    G = an['grip']
    b = Body(X[side])
    hb = 'HAND_' + side
    g0 = 0.0012
    Z = V((0, 0, 1))

    def nrm(theta):
        return V((math.cos(D(theta)) / G['hx'], math.sin(D(theta)) / G['hy'], 0)).normalized()
    # palm slab wrapped round the grip; padded back panel raised on it
    b.loft([[gpt(G, th, z, g) for g, z in rrect_gz(g0, g0 + T, zb, zt, 0.0075)] for th, zt, zb, T in an['palm']], hb, 'glove')
    t0, t1 = an['panel']
    rings = []
    for i in range(7):
        th = t0 + (t1 - t0) * i / 6
        zt, zb, T = palm_at(an['palm'], th)
        e = 0.004 if i in (0, 6) else 0.0
        rings.append([gpt(G, th, z, g) for g, z in rrect_gz(g0 + T - 0.006, g0 + T + 0.0028 - e, zb + 0.013 + e, zt - 0.012 - e, 0.003, 2)])
    b.loft(rings, hb, 'glove2', prio=2)
    Xi = X[side].inverted()

    def panel_paint(p):
        q = Xi @ p
        th = math.degrees(math.atan2((q.y - G['cy']) / (G['hy'] + 0.02), q.x / (G['hx'] + 0.02)))
        if not t1 + 2.5 < th < t0 - 2.5:
            return False
        zt, zb, T = palm_at(an['palm'], th)
        z0, z1 = zb + 0.0150, zt - 0.0140
        u = (th - (t0 + t1) / 2) / ((t0 - t1) / 2 - 2.5)
        v = (q.z - (z0 + z1) / 2) / ((z1 - z0) / 2)
        return u ** 4 + v ** 4 < 1.0
    b.parts[-1]['paint'] = panel_paint
    # hard armour plate on the back of the hand, over the padded panel (own shell)
    th = (t0 + t1) / 2
    zt, zb, T = palm_at(an['palm'], th)
    b.pad(gpt(G, th, (zt + zb) / 2 + 0.002, g0 + T + 0.0026), nrm(th), Z, 0.030, 0.034, 0.0046, hb, 'glove4', ch=0.0016, sink=0.0030)
    # heel (hypothenar) and wrist; the wrist ends in a ball round the wrist joint
    th, z, g, rad = an['heel']
    n = nrm(th)
    b.ellipsoid(gpt(G, th, z, 0.0) + n * g, rad, (n, Z.cross(n), Z), hb, 'glove')
    wa = gpt(G, -50, -0.050, 0.012)
    wd = (WRIST - wa).normalized()
    b.capsule(wa, WRIST + wd * 0.002, 0.021, 0.0190, hb, 'glove', up=(0, 0, 1), flat=1.08)
    # fingers: each one a clean lofted digit, rigid on its bone, outlined by its own ink shell (the outline reads
    # the gaps between fingers); banded like a tactical glove: padded first segment (glove2), dark stretch
    # creases at the joints, reinforced tip (glove3). Its root sinks into a stub in the palm union. A hard
    # moulded knuckle pad covers each knuckle (own shell, rigid on the hand).
    knuckles = []
    for fn in FINGERS:
        z, r, L = FING[fn]
        J = finger_joints(side, fn)
        fb = fn + '_' + side
        d0 = (J[1] - J[0]).normalized()
        b.capsule(J[0] - d0 * 0.004, J[0] + d0 * (L[0] * 0.40), r[0] * 0.92, r[0] * 0.86, fb, 'glove', up=(0, 0, 1), flat=FLAT, seg=12, cap=3)
        b.digit(J, r, fb, DIGIT_BANDS)
        n0 = (d0.cross(Z)).normalized()                         # back of the finger: outward, away from the grip
        if fn == 'INDEX' and an['trigger']:
            n0 = (n0 + Z * 0.35).normalized()
        knuckles.append((J[0] + n0 * (r[0] * 0.80) - d0 * 0.0012, n0, d0, r[0]))
    b.knuckle_guard(knuckles, hb)
    # thumb: metacarpal inside the thenar mass (union), the two phalanges one lofted digit, knuckle pad
    T = thumb_joints(side, X)
    b.capsule(T[0], T[1], THUMB_R[0] + 0.004, THUMB_R[1], 'THUMB1_' + side, 'glove', up=(0, 0, 1), flat=0.95)
    th, z, g, rad = an['thenar']
    n = nrm(th)
    b.ellipsoid(gpt(G, th, z, 0.0) + n * g, rad, (n, Z.cross(n), Z), 'THUMB1_' + side, 'glove')
    b.digit(T[1:], THUMB_R[1:], 'THUMB2_' + side, THUMB_BANDS, flat=0.94)
    ta = (T[2] - T[1]).normalized()
    tn = T[1] - PALM_C
    tn = (tn - ta * tn.dot(ta)).normalized()
    b.pad(T[1] + tn * (THUMB_R[1] * 0.80), tn, T[2] - T[0], THUMB_R[1] * 1.45, THUMB_R[1] * 1.30, 0.0060, 'THUMB2_' + side, 'glove4', sink=0.0040)
    return b


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


def union_surface(body, pal, voxel=GLOVE_VOXEL, tris=GLOVE_TRIS):
    """Voxel union of the body's primitives, relaxed, colour regions painted (palette UVs: the decimator
    keeps UV seams, so patch borders stay clean), decimated; returns a triangle bmesh."""
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
    acc = sorted([p for p in body.parts if p['prio'] > 0], key=lambda p: -p['prio'])
    for f in hi.faces:
        c = f.calc_center_median()
        col = next((p['color'] for p in acc if sdist(c, p) < p.get('reach', 0.0012) and p.get('paint', lambda q: True)(c)), 'glove')
        uv = pal.uv(pal.index(col))
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


def classify(bm, body, parents, sigma=0.0022):
    """Vertex weights: nearest bone, blended smoothly only with its parent / child bone."""
    weights = []
    for v in bm.verts:
        db = {}
        for p in body.parts:
            d = abs(sdist(v.co, p))
            if d < db.get(p['bone'], 1e9):
                db[p['bone']] = d
        b0 = min(db, key=db.get)
        w = {b0: 1.0}
        for b1 in db:
            if b1 != b0 and (parents.get(b1) == b0 or parents.get(b0) == b1):
                k = math.exp(-(db[b1] - db[b0]) / sigma)
                if k > 0.08:
                    w[b1] = k
        top = sorted(w.items(), key=lambda t: -t[1])[:2]
        s = sum(x for _, x in top)
        weights.append({bn: x / s for bn, x in top})
    return weights


# ---------------------------------------------------------------- loft helpers (forearm pieces, upper sleeves)
def ring_pts(c, d, up, a, b, seg, a0=0.0):
    u = up - d * up.dot(d)
    u.normalize()
    s = d.cross(u)
    return [c + s * (a * math.cos(a0 + 2 * math.pi * k / seg)) + u * (b * math.sin(a0 + 2 * math.pi * k / seg)) for k in range(seg)]


def lathe_shell(bm, prof, o, d, up, seg, pal, dl, gi, sl, sid):
    """Closed loft of rings along d from o; bands coloured per ring; every vertex fully on bone index gi."""
    rings = []
    for t, a, b, _ in prof:
        c = o + d * t
        if a < 1e-7:
            rings.append([bm.verts.new(c)])
        else:
            rings.append([bm.verts.new(p) for p in ring_pts(c, d, up, a, b, seg)])
    faces = []
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        n = max(len(A), len(B))
        for j in range(n):
            j2 = (j + 1) % n
            if len(A) == 1:
                f = bm.faces.new((A[0], B[j], B[j2]))
            elif len(B) == 1:
                f = bm.faces.new((A[j], A[j2], B[0]))
            else:
                f = bm.faces.new((A[j], A[j2], B[j2], B[j]))
            f.material_index = pal.index(prof[i][3])
            faces.append(f)
    for r, i in ((rings[0], 0), (rings[-1], -1)):
        if len(r) >= 3:
            f = bm.faces.new(r)
            f.material_index = pal.index(prof[i][3])
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    for f in faces:
        f[sl] = sid
    for r in rings:
        for v in r:
            v[dl][gi] = 1.0
    return faces


def rigid_loft(bm, rings, colors, pal, dl, gi, sl, sid, caps=(True, True), fcol=None):
    """Closed loft of rings (rig-space points; a one-point ring is an apex) rigid on bone index gi.
    colors: one per band (ring i -> i+1); fcol(i, j) may override a face's colour (band i, column j)."""
    vr = [[bm.verts.new(V(p)) for p in r] for r in rings]
    faces = []
    for i in range(len(vr) - 1):
        A, B = vr[i], vr[i + 1]
        n = max(len(A), len(B))
        for j in range(n):
            j2 = (j + 1) % n
            q = (A[0], B[j], B[j2]) if len(A) == 1 else (A[j], A[j2], B[0]) if len(B) == 1 else (A[j], A[j2], B[j2], B[j])
            f = bm.faces.new(q)
            f.material_index = pal.index((fcol and fcol(i, j)) or colors[i])
            faces.append(f)
    for k, (r, c) in enumerate(((vr[0], colors[0]), (vr[-1], colors[-1]))):
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
        f[sl] = sid
    for r in vr:
        for v in r:
            v[dl][gi] = 1.0
    return faces


# ---------------------------------------------------------------- forearm v3 (rigid on FOREARM, rolls with the hand)
# The forearm is laid out in the hand's own frame: t runs from the wrist joint to the elbow, the section is an
# ellipse whose wide axis spans thumb side (radial) to little-finger side, its dorsal axis the back of the hand.
# Layers, each a closed piece with its own ink shell:
#   * the arm: an anatomical taper, flat and narrow at the wrist, a muscle belly two thirds of the way up
#     (pushed toward the thumb side and the back), easing in again at the elbow; a sleeve pushed up behind the
#     gauntlet that bunches into diagonal folds (dark crease bands) toward the elbow.
#   * gauntlet: a wrist lame (rolled lip round the glove's wrist, strap tab) under a vambrace lame (wider,
#     overlapping it, strap band near its end), and a raised armour plate with an amber spine on the side the
#     game camera sees at rest.
FORE_SEG = 14
# arm section stations: (t, half width (radial-ulnar), half height (dorsal-volar), shift to the thumb side, shift to the back)
FORE_PROF = [(-0.020, 0.0236, 0.0186, 0.0, 0.0), (0.000, 0.0240, 0.0190, 0.0, 0.0), (0.050, 0.0270, 0.0210, 0.0, 0.0005),
             (0.100, 0.0312, 0.0248, 0.0012, 0.0012), (0.150, 0.0370, 0.0300, 0.0026, 0.0024), (0.195, 0.0425, 0.0352, 0.0040, 0.0032),
             (0.235, 0.0458, 0.0388, 0.0042, 0.0032), (0.268, 0.0450, 0.0394, 0.0030, 0.0020), (0.300, 0.0410, 0.0372, 0.0, 0.0)]
# sleeve rings (t) from under the vambrace to the elbow; the cloth stands off the arm by SLEEVE_EX and bunches into
# FOLDS: (t, bulge m, angle of the deepest side, wrap: how far round it goes (1 = all round)) that run diagonally
SLEEVE_T = (0.118, 0.150, 0.163, 0.172, 0.181, 0.192, 0.204, 0.214, 0.224, 0.236, 0.248, 0.260, 0.272, 0.286, 0.300)
SLEEVE_EX = 0.0028
FOLDS = ((0.176, 0.0042, 200, 0.55), (0.208, 0.0050, 150, 0.45), (0.240, 0.0046, 230, 0.60), (0.268, 0.0040, 120, 0.50))
FOLD_W, FOLD_SLANT = 0.0105, 0.010       # fold half width along the arm, diagonal (t shift across the arm)
# gauntlet lames: (t, extra radius over the arm, colour of the band that starts here)
WRIST_LAME = [(-0.017, 0.0010, 'glove3'), (-0.015, 0.0046, 'glove3'), (-0.010, 0.0064, 'glove2'), (-0.004, 0.0060, 'glove3'),
              (0.034, 0.0056, 'glove3'), (0.040, 0.0030, 'glove3')]
VAMBRACE = [(0.030, 0.0050, 'glove3'), (0.034, 0.0090, 'glove2'), (0.106, 0.0086, 'glove4'), (0.124, 0.0088, 'glove2'),
            (0.150, 0.0090, 'glove3'), (0.160, 0.0090, 'glove3'), (0.168, 0.0052, 'glove3')]
STRAP_TAB = (0.012, 0.010, 0.013, 0.0030)        # amber strap tab on the wrist lame: centre t, width, length, height
PLATE = {'t': (0.046, 0.142), 'arc': (-62, -40, -18, -5, 5, 18, 40, 62), 'lift': (0.0012, 0.0062), 'ch': 0.0042, 'spine': 3}
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


def forearm_shells(bm, pal, dl, gi, sl, sid, wr, fd, rad, dor, side, views=(CAM_RIG,)):
    """Arm + sleeve, wrist lame, vambrace, strap tab and armour plates on one forearm (frame: fd wrist -> elbow,
    rad thumb side, dor back of the hand; views: the game camera in rest space for the holds that matter, a
    plate faces each). Returns (next sid, nohull sids)."""

    def at(t, phi, extra=0.0, lift=0.0):
        a, b, ds, du = fore_prof(t)
        a, b = a + extra, b + extra
        ph = D(phi)
        n = V((math.cos(ph) * b, math.sin(ph) * a)).normalized()        # ellipse normal
        x, y = math.cos(ph) * a + n.x * lift + ds, math.sin(ph) * b + n.y * lift + du
        return wr + fd * t + rad * x + dor * y

    angles = [360.0 * (k + 0.5) / FORE_SEG for k in range(FORE_SEG)]
    # the side the game camera sees at rest (angle from the thumb side toward the back of the hand)
    def view_angle(cam):
        dc = cam - (wr + fd * 0.12)
        dc -= fd * dc.dot(fd)
        return math.degrees(math.atan2(dc.dot(dor), dc.dot(rad)))
    phc = view_angle(views[0])
    plates = [phc]
    for cam in views[1:]:
        a = view_angle(cam)
        if abs((a - phc + 180) % 360 - 180) > 75:
            plates.append(a)
    # arm + sleeve: starts hidden under the vambrace, bunches into diagonal folds toward the elbow; the shaded
    # underside of each fold (toward the elbow, where it is deep) takes the dark crease colour
    def fold(t, phi):
        h, slope = 0.0, 0.0
        for tc, amp, pc, wrap in FOLDS:
            dp = math.cos(D(phi - pc))
            wa = max(0.0, (dp + wrap) / (1 + wrap)) ** 1.5
            u = (t - tc - FOLD_SLANT * math.sin(D(phi - pc + 90))) / FOLD_W
            if abs(u) < 1:
                b = 0.5 + 0.5 * math.cos(math.pi * u)
                h += amp * wa * b
                slope += -amp * wa * math.sin(math.pi * u) * (u > 0)
        return h, slope
    sid += 1
    rings = [[at(t, phi, SLEEVE_EX * min(1.0, (t - SLEEVE_T[0]) / 0.03) + fold(t, phi)[0]) for phi in angles] for t in SLEEVE_T]
    te = SLEEVE_T[-1] + 0.010
    rings.append([wr + fd * te + rad * fore_prof(te)[2] + dor * fore_prof(te)[3]])
    crease = lambda i, j: 'sleeve3' if i < len(SLEEVE_T) - 1 and fold((SLEEVE_T[i] + SLEEVE_T[i + 1]) / 2, angles[j] + 180 / FORE_SEG)[1] < -0.0022 else None
    rigid_loft(bm, rings, ['sleeve'] * len(rings), pal, dl, gi, sl, sid, fcol=crease)
    # wrist lame: rolled lip round the glove's wrist
    sid += 1
    rings = [[at(t, phi, ex) for phi in angles] for t, ex, _ in WRIST_LAME]
    rigid_loft(bm, rings, [c for _, _, c in WRIST_LAME], pal, dl, gi, sl, sid)
    # vambrace lame over it, strap band near its end
    sid += 1
    rings = [[at(t, phi, ex) for phi in angles] for t, ex, _ in VAMBRACE]
    rigid_loft(bm, rings, [c for _, _, c in VAMBRACE], pal, dl, gi, sl, sid)
    # amber strap tab on the wrist lame, toward the camera
    tt, tw, tl, th = STRAP_TAB
    ex = 0.0060
    sid += 1
    tab = []
    a0 = fore_prof(tt)[0] + ex
    for lift in (-0.002, th - 0.0012, th):
        ins = 0.0012 if lift == th else 0.0
        tab.append([at(tt + y, phc + math.degrees(x / a0), ex, lift) for (x, y) in rrect(tw - 2 * ins, tl - 2 * ins, c=0.002)])
    rigid_loft(bm, tab, ['amber', 'amber', 'amber'], pal, dl, gi, sl, sid)
    # raised armour plate on the vambrace (chamfered all round, amber spine)
    B = PLATE
    l0, l1 = B['lift']
    ch = B['ch']
    vex = 0.0088
    for k, pc in enumerate(plates):
        t0, t1 = B['t'] if k == 0 else (B['t'][0] + 0.010, B['t'][1] - 0.022)       # a second, shorter plate (no spine)
        arc = [pc + a * (1.0 if k == 0 else 0.8) for a in B['arc']]

        def section(t, ins):
            a0, a1 = arc[0] + (3 if ins else 0), arc[-1] - (3 if ins else 0)
            outer = [at(t, a, vex, l1 - ins) for a in [a0] + arc[1:-1] + [a1]]
            inner = [at(t, a, vex, l0) for a in [a1] + list(reversed(arc[1:-1])) + [a0]]
            return outer + inner
        rings = [section(t0, ch * 0.6), section(t0 + ch, 0.0), section(t1 - ch, 0.0), section(t1, ch * 0.6)]
        sp = B['spine'] if k == 0 else -1
        sid += 1
        rigid_loft(bm, rings, ['glove4', 'glove4', 'glove4'], pal, dl, gi, sl, sid, fcol=lambda i, j: 'amber' if i == 1 and j == sp else None)
    return sid, set()


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
    faces = [f for f in bm.faces if f[sl] not in nohull]     # inner details (seams) carry no shell
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
    parents = {}
    for side in ('R', 'L'):
        Xs = X[side]
        wr = Xs @ WRIST
        RIG.setdefault('X', {})[side] = Xs
        s, e = two_bone(SH[side], wr, HINT[side], pref=hand_axes(side)[0])
        RIG['S0'][side], RIG['E0'][side], RIG['W0'][side] = s, e, wr
        bone('UPPERARM_' + side, s, e, 'Weapon')
        bone('FOREARM_' + side, e, wr, 'Weapon')
        bone('HAND_' + side, wr, Xs @ PALM_C, 'Weapon')
        T = thumb_joints(side, X)
        bone('THUMB1_' + side, Xs @ T[0], Xs @ T[1], 'HAND_' + side)
        bone('THUMB2_' + side, Xs @ T[1], Xs @ T[3], 'THUMB1_' + side)
        parents['THUMB1_' + side] = 'HAND_' + side
        parents['THUMB2_' + side] = 'THUMB1_' + side
        for fn in FINGERS:
            J = finger_joints(side, fn)
            bone(fn + '_' + side, Xs @ J[0], Xs @ J[-1], 'HAND_' + side)
            parents[fn + '_' + side] = 'HAND_' + side
    bpy.ops.object.mode_set(mode='OBJECT')
    assert len(arm.bones) == 22, len(arm.bones)
    names = [b.name for b in arm.bones]
    gi = {n: i for i, n in enumerate(names)}

    # one bmesh: both gloves (one surface each), both forearm shells, both upper sleeves
    bm = bmesh.new()
    dl = bm.verts.layers.deform.verify()
    sl = bm.faces.layers.int.new('shape_id')
    snl = bm.verts.layers.float_vector.new('snor')
    sid = 0
    soft, nohull = set(), set()      # glove surfaces (fully smooth) / inner details without an ink shell
    group = {}                       # shape id -> part group (triangle report)
    for side in ('R', 'L'):
        body = glove_body(side, X)
        g = union_surface(body, pal)
        ws = classify(g, body, parents)
        vm = {}
        gsn = g.verts.layers.float_vector['snor']
        for v, w in zip(g.verts, ws):
            nv = bm.verts.new(v.co)
            nv[snl] = v[gsn]
            for bn, x in w.items():
                nv[dl][gi[bn]] = x
            vm[v] = nv
        sid += 1
        soft.add(sid)
        for f in g.faces:
            nf = bm.faces.new([vm[v] for v in f.verts])
            nf.material_index = f.material_index
            nf[sl] = sid
        g.free()
        for p in body.parts:
            p['bm'].free()
        for rings, cols, bn, smooth, caps in body.hard:     # digits and pads: own shells, rigid on their bone
            sid += 1
            group[sid] = 'digits' if smooth else 'pads'
            if smooth:
                soft.add(sid)
            rigid_loft(bm, rings, cols, pal, dl, gi[bn], sl, sid, caps=caps)
        s, e, wr = RIG['S0'][side], RIG['E0'][side], RIG['W0'][side]
        fd = (e - wr).normalized()
        up = V((0, 0, 1))
        _, n0, l0 = hand_axes(side)
        dor = (-n0 - fd * (-n0).dot(fd)).normalized()
        rad = (-l0 - fd * (-l0).dot(fd) - dor * (-l0).dot(dor)).normalized()
        s0 = sid
        # the camera as the forearm sees it in a long-gun hold (the forearm rolls with the hand): a plate there too
        Wl = Matrix.Translation(V(CARRY['rifle']))
        Fl = Wl @ (left_hold('RIVET') if side == 'L' else grip_frame('RIVET'))
        cam_l = (Fl @ RIG['F0'][side].inverted()).inverted() @ CAM_RIG
        sid, nh = forearm_shells(bm, pal, dl, gi['FOREARM_' + side], sl, sid, wr, fd, rad, dor, side, (CAM_RIG, cam_l))
        group.update({i: 'forearms' for i in range(s0 + 1, sid + 1)})
        nohull |= nh
        ud = (s - e).normalized()
        sid += 1
        lathe_shell(bm, [(-0.034, 0.0, 0.0, 'sleeve'), (-0.026, 0.036, 0.034, 'sleeve'), (0.000, 0.0465, 0.0445, 'sleeve'),
                         ((s - e).length + 0.02, 0.050, 0.048, 'sleeve'), ((s - e).length + 0.03, 0.0, 0.0, 'sleeve')],
                    e, ud, up, 7, pal, dl, gi['UPPERARM_' + side], sl, sid)
    check_zfight('ARMS', bm, sl)
    me = bpy.data.meshes.new('ARMS')
    obj = bpy.data.objects.new('ARMS', me)
    bpy.context.scene.collection.objects.link(obj)
    for n in names:
        obj.vertex_groups.new(name=n)
    bm.to_mesh(me)
    bm.free()
    obj.data.materials.append(pal.material)
    # palette UVs, white vertex colour, smooth glove / crisp cuff edges, then one ink shell per piece
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
        elif e.link_faces[0][sl2] not in soft and e.calc_face_angle(0.0) > math.radians(40):
            e.smooth = False        # shells: crisp rims, steps and pad edges (gloves stay fully smooth)
    b2.to_mesh(obj.data)
    b2.free()
    arms_hull(obj, pal, HULL_T, nohull)
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
        g = group.get(sla[p.index].value, 'gloves' if sla[p.index].value in soft else 'upper arms')
        cnt[g] = cnt.get(g, 0) + len(p.vertices) - 2
    print('ARMS: %d triangles incl. outline shell (%s)' % (sum(cnt.values()), ', '.join('%s %d' % kv for kv in sorted(cnt.items()))))
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
#             idx / lift: trigger finger off the trigger (curl about the grip axis / lift along the frame);
#             pump: the free support fist for the 'high' style ((NDC x, y, depth m), palm direction, wrist bend)
#   slide     a / b: the tucked, canted gun; hand: the free support hand out for balance (as pump); curl / thumb
#             open its fingers; hint: where its elbow points
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
    # direction (rig space), (wrist flex, deviation) deg); curl / thumb open the fingers
    'slide': {'a': ((-0.030, -0.010, 0.000), (8, -28, 6)), 'b': ((-0.028, -0.014, -0.006), (7, -30, 7)),
              'hand': (((-0.56, -0.62, 0.52), (-0.25, 0.30, -1.0), (-10, 6)), ((-0.54, -0.58, 0.52), (-0.25, 0.35, -1.0), (-12, 6))),
              'curl': -72, 'thumb': -40, 'hint': (-1.0, 0.0, -0.5)},
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
                   'pump': (((-0.62, -0.78, 0.46), (0.6, 0.2, -0.4), (10, 0)), ((-0.72, -1.25, 0.44), (0.6, -0.2, -0.4), (10, 0))), 'fist': 26},
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
# the gun's visible surface), and the fingers / thumb close until they meet it (curl from the gap left).
# two-hand pistol hold: support glove offset (m) and rotation (deg) from the grip frame, thumb swing, finger curl
PISTOL_LEFT = (-0.018, 0.018, -0.016, 8, 0, 14, 0, -8)
GUARD_PALM = V((0.70, 0.0, -0.71))      # handguards: palm under, fingers over the far side, forearm from below


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


def fit_support():
    """Slide each long gun's support frame onto its foregrip / handguard; curl fingers and thumb to the gap."""
    G = ANAT['L']['grip']
    for wid, info in WEAPONS.items():
        if info['cls'] in ('pistol', 'melee'):
            continue
        F = left_hold(wid)
        o, x, y, z = F.translation.copy(), F.col[0].xyz, F.col[1].xyz, F.col[2].xyz
        palm = -x                                   # palm side (the glove is mirrored)
        hs = [o + z * FING[fn][0] for fn in FINGERS]     # sample the part across the hand, index to pinky
        rp = max(reach(wid, h, palm) for h in hs)
        rf = sum(reach(wid, h, y) for h in hs) / 4
        rb = sum(reach(wid, h, -y) for h in hs) / 4
        F = F.copy()
        clamp = lambda v, m: max(-m, min(m, v))
        F.translation = o + palm * clamp(rp - G['hx'], 0.010) + y * clamp((rf - rb) / 2, 0.008)
        info['hold_L'] = F
        info['curl_L'] = max(-25.0, min(25.0, math.degrees((G['hy'] - (rf + rb) / 2) / 0.045)))
        info.pop('bvh', None)


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
