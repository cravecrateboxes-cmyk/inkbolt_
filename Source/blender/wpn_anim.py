"""INKBOLT weapons: arm actions (per-weapon clips from the HANDLING tables, reloads, melee swings, throws).
Built by fam_weapons.py; shape kit and gun parts in wpn_core.py.

Every clip is BAKED: one pose per frame (30 fps), each pose solved from moving parts that are evaluated at that
frame's time, so arcs are arcs, nothing waits on a pose, and a hand that holds something is locked to it on every
frame, not only at keys. The parts of a clip (class Clip):
  weapon     a spline track (Track) of offset + rotation about the grip, plus additive wobble
  hands      a Path each: stations (the hold on the gun, a pouch, a magazine, a handle...) that are themselves
             functions of time (a station on the gun moves with the gun), eased blends with an arc between them
  magazine   a function of time: in its well (sliding / rocking out), in the hand (in_hand of the hand's own
             path: locked), falling
  digits     an FPath per hand: finger poses blended with a stagger from index to little finger; the trigger
             finger follows two tracks (off the trigger 0..1, pull 0..1)
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from ib_lib import *  # noqa: F401,F403
import ib_lib
from wpn_core import *  # noqa: F401,F403
from wpn_arms import *  # noqa: F401,F403
import wpn_arms


# ================================================================ rig solve
def basis(c0, c1, c2):
    return Matrix((c0, c1, c2)).transposed()


def forearm_delta(side, MH, e, wr):
    """FOREARM bone motion: the segment goes from its rest place to (e, wr) and rolls about its own axis with
    the hand (pronation / supination), so the wrist only bends and never shows a twist."""
    E0, W0 = RIG['E0'][side], RIG['W0'][side]
    f0, f = (W0 - E0).normalized(), (wr - e).normalized()
    l0 = hand_axes(side)[2]
    l = MH.to_3x3() @ l0

    def frame3(f, l):
        r = l - f * l.dot(f)
        r = r.normalized() if r.length > 1e-4 else f.orthogonal().normalized()
        return basis(f, r, f.cross(r))
    R = frame3(f, l) @ frame3(f0, l0).inverted()
    return T(wr) @ R.to_4x4() @ T(-W0)


def free_hand(side, wrist, palm, bend=(0.0, 0.0), hint=None):
    """Hand frame (rig space, as a hand Path's station) for a hand with its wrist at `wrist`, the palm facing `palm`
    and the hand lined up with the forearm the arm IK gives there, bent by (flex toward the palm, deviation
    toward the little finger) degrees: a free hand never snaps at the wrist."""
    wrist = V(wrist)
    s, e = two_bone(SH[side], wrist, V(hint) if hint is not None else HINT[side])
    f = (wrist - e).normalized()
    a0, n0, l0 = hand_axes(side)
    sg = 1.0 if l0.dot(n0.cross(a0)) > 0 else -1.0
    pn = V(palm).normalized()
    pn = (pn - f * pn.dot(f)).normalized()
    lat = sg * pn.cross(f)
    a = Matrix.Rotation(D(bend[0]), 3, lat) @ f
    a = Matrix.Rotation(D(bend[1]), 3, pn) @ a
    n = (pn - a * pn.dot(a)).normalized()
    l = sg * n.cross(a)
    Rh = basis(a, n, l) @ basis(a0, n0, l0).inverted()
    MH = T(wrist) @ Rh.to_4x4() @ T(-RIG['W0'][side])
    return MH @ RIG['F0'][side]


REPORT = None
VM_POS, VM_YAW, VM_S, TAN_V, ASPECT = V((0.19, -0.13, -0.5)), 0.06, 0.85, math.tan(D(29)), 16 / 9
# the game's swap (src/game/weapons.js VM_TUNE stow*, VM_CLASS hip* / stow): how far the viewmodel is lowered at
# the moment the models change, and the launchers' extra hip offset
VM_STOW = {'pos': V((0.02, -0.10, 0.0)), 'pitch': 0.1, 'roll': 0.1}
VM_CLS = {'rocket': {'hip': V((0.035, -0.03, -0.16)), 'stow': 2.2}}


def ndc(p, stow=0.0, cls=None):
    """Rig point -> the game's viewmodel screen (NDC x, y; desktop 16:9) and depth (m); stow 1 = lowered for a swap."""
    c = VM_CLS.get(cls, {})
    u = stow * c.get('stow', 1.0)
    q = V((p.x, p.z, -p.y)) * VM_S
    R = Euler((VM_STOW['pitch'] * u, VM_YAW, VM_STOW['roll'] * u), 'XYZ').to_matrix()
    q = R @ q + VM_POS + c.get('hip', V((0, 0, 0))) + VM_STOW['pos'] * u
    d = -q.z
    return V((q.x / (d * TAN_V * ASPECT), q.y / (d * TAN_V))), d


def at_ndc(x, y, d):
    """Inverse of ndc: the rig point seen at NDC (x, y), d metres in front of the eye."""
    q = V((x * d * TAN_V * ASPECT, y * d * TAN_V, -d)) - VM_POS
    c, sn = math.cos(VM_YAW), math.sin(VM_YAW)
    q = V((c * q.x - sn * q.z, q.y, sn * q.x + c * q.z)) / VM_S
    return V((q.x, -q.z, q.y))


def wrist_bend(side, MH, e, wr):
    """Angle (deg) between the forearm and the hand's axis (0 = straight wrist)."""
    a = MH.to_3x3() @ hand_axes(side)[0]
    return math.degrees(a.angle((wr - e).normalized()))


WRIST_MAX = 56.0        # deg: past this the forearm follows the hand (the elbow and the off-screen shoulder give way)


def solve(rig, P):
    """P: W (weapon delta), FR / FL (hand frames, rig space), mag (Mag bone delta), dig {side: {digit: (knuckle,
    joint 2, joint 3[, spread]) deg from the rest pose, positive = closing; spread positive = toward the thumb}}.
    Returns {bone: pose basis}: each bone gets the rigid motion that takes its rest place to the target."""
    M = {'Root': Matrix.Identity(4), 'Camera': Matrix.Identity(4), 'Weapon': P['W'], 'Mag': P['mag']}
    for side in ('R', 'L'):
        F0 = RIG['F0'][side]
        MH = P['F' + side] @ F0.inverted()
        M['HAND_' + side] = MH
        wr = MH @ RIG['W0'][side]
        a = (MH.to_3x3() @ hand_axes(side)[0]).normalized()
        s, e = two_bone(SH[side], wr, P.get('hint', {}).get(side, HINT[side]), pref=a)
        f = (wr - e).normalized()
        bend, lim = f.angle(a), D(P.get('wrist', WRIST_MAX))
        if bend > lim:                   # no wrist bends this far: swing the forearm toward the hand
            q = Quaternion().slerp(f.rotation_difference(a), 1.0 - lim / bend)
            e = wr - (q @ f) * FORE_LEN
            s = e + (s - e).normalized() * UPPER_LEN
        M['UPPERARM_' + side] = seg_delta(RIG['S0'][side], RIG['E0'][side], s, e)
        M['FOREARM_' + side] = forearm_delta(side, MH, e, wr)
        if REPORT is not None:
            REPORT.setdefault(side, []).append(wrist_bend(side, MH, e, wr))
        dig = P.get('dig', {}).get(side, {})
        for dn in DIGITS:                  # each joint is a hinge about the digit's flexion axis; the knuckle also spreads
            for i, Md in enumerate(digit_fk(side, dn, dig.get(dn, (0.0, 0.0, 0.0, 0.0)))):
                M['%s%d_%s' % (dn, i + 1, side)] = MH @ Md
    out = {}
    for b in rig.data.bones:
        Rc = b.matrix_local
        Mp = M[b.parent.name] if b.parent else Matrix.Identity(4)
        out[b.name] = Rc.inverted() @ Mp.inverted() @ M[b.name] @ Rc
    return out


# ================================================================ curves, paths
def ez(u, kind='io'):
    """Easing of 0..1: 'io' slow in and out, 'in' accelerating, 'out' decelerating, 'in3' / 'out3' harder,
    'back' overshoots the end by about a tenth and comes back, 'lin'."""
    u = max(0.0, min(1.0, u))
    if kind == 'io':
        return u * u * (3 - 2 * u)
    if kind == 'in':
        return u * u
    if kind == 'out':
        return 1 - (1 - u) * (1 - u)
    if kind == 'in3':
        return u * u * u
    if kind == 'out3':
        return 1 - (1 - u) ** 3
    if kind == 'back':
        s = 1.70158
        return (u - 1) * (u - 1) * ((s + 1) * (u - 1) + s) + 1
    return u


class Track:
    """Keyed vector track through its keys (t, value[, mode]): mode 's' passes through smoothly (the motion keeps
    going: Catmull-Rom tangent), 'h' stops there (zero tangent). period: the loop length of a cyclic track."""

    def __init__(self, keys, period=None):
        ks = sorted(((k[0], tuple(k[1]) if hasattr(k[1], '__len__') else (float(k[1]),), k[2] if len(k) > 2 else 's') for k in keys), key=lambda k: k[0])
        self.t = [k[0] for k in ks]
        self.v = [k[1] for k in ks]
        self.period = period
        n = len(ks)
        self.m = []
        for i, (t, v, mode) in enumerate(ks):
            if mode == 'h' or n < 2 or (period is None and i in (0, n - 1)):
                self.m.append(tuple(0.0 for _ in v))
                continue
            (t0, v0), (t1, v1) = self._nb(i - 1), self._nb(i + 1)
            self.m.append(tuple((b - a) / (t1 - t0) for a, b in zip(v0, v1)))

    def _nb(self, i):
        n = len(self.t)
        if 0 <= i < n:
            return self.t[i], self.v[i]
        k = i % n
        return self.t[k] + self.period * ((i - k) // n), self.v[k]

    def __call__(self, t):
        n = len(self.t)
        if n == 1:
            return self.v[0]
        if self.period is not None:
            t = self.t[0] + (t - self.t[0]) % self.period
            i = max(j for j in range(n) if self.t[j] <= t + 1e-9)
            (t0, v0), (t1, v1) = (self.t[i], self.v[i]), self._nb(i + 1)
            m0, m1 = self.m[i], self.m[(i + 1) % n]
        else:
            if t <= self.t[0]:
                return self.v[0]
            if t >= self.t[-1]:
                return self.v[-1]
            i = max(j for j in range(n - 1) if self.t[j] <= t)
            t0, v0, t1, v1, m0, m1 = self.t[i], self.v[i], self.t[i + 1], self.v[i + 1], self.m[i], self.m[i + 1]
        h = t1 - t0
        u = (t - t0) / h
        u2, u3 = u * u, u * u * u
        a, b, c, d = 2 * u3 - 3 * u2 + 1, u3 - 2 * u2 + u, -2 * u3 + 3 * u2, u3 - u2
        return tuple(a * p0 + b * h * q0 + c * p1 + d * h * q1 for p0, q0, p1, q1 in zip(v0, m0, v1, m1))

    def s(self, t):
        return self(t)[0]


def mix(A, B, k):
    """Blend of two frames: positions straight (k may overshoot), rotations along the short arc."""
    qa, qb = A.to_quaternion(), B.to_quaternion()
    M = qa.slerp(qb, max(0.0, min(1.0, k))).to_matrix().to_4x4()
    M.translation = A.translation.lerp(B.translation, k)
    return M


class Path:
    """A frame moving between stations. A station is a frame or a function of time giving one (a place on the gun
    moves with the gun), held from t0 to t1; between stations the frame blends from the one it left to the one it
    reaches, BOTH evaluated at the current time, eased, with an optional arc (rig space, at mid-way)."""

    def __init__(self, home):
        self.home = home
        self.st = []

    def leave(self, t):
        self.st.append((-1e9, t, self.home, 'io', None))
        return self

    def to(self, t, fn, dwell=0.0, ease='io', arc=None):
        if not self.st:
            self.st.append((-1e9, -1e9, self.home, 'io', None))
        self.st.append((t, t + dwell, fn, ease, V(arc) if arc is not None else None))
        return self

    def back(self, t, ease='io', arc=None):
        return self.to(t, self.home, 1e9, ease, arc)

    def __call__(self, t):
        if not self.st:
            return self.home(t)
        ev = lambda fn: fn(t) if callable(fn) else fn
        prev = self.st[0]
        if t <= prev[1]:
            return ev(prev[2])
        for st in self.st[1:]:
            if t < st[0]:
                u = (t - prev[1]) / (st[0] - prev[1])
                M = mix(ev(prev[2]), ev(st[2]), ez(u, st[3]))
                if st[4] is not None:
                    M.translation += st[4] * math.sin(math.pi * u)
                return M
            if t <= st[1]:
                return ev(st[2])
            prev = st
        return ev(prev[2])


Z4 = (0.0, 0.0, 0.0, 0.0)
ORDER = ('INDEX', 'MIDDLE', 'RING', 'PINKY', 'THUMB')


def dget(d, dn):
    v = d.get(dn, Z4)
    return tuple(v) + (0.0,) * (4 - len(v))


def dmix(a, b, k):
    """Blend of two hand poses; k a number or {digit: number}."""
    return {dn: tuple(x + (y - x) * (k[dn] if isinstance(k, dict) else k) for x, y in zip(dget(a, dn), dget(b, dn))) for dn in DIGITS}


def dadd(a, b):
    return {dn: tuple(x + y for x, y in zip(dget(a, dn), dget(b, dn))) for dn in DIGITS}


class FPath:
    """Digits of one hand moving between poses: like Path, the fingers following each other (stagger s between
    neighbours, index first; a negative stagger leads with the little finger)."""

    def __init__(self, home):
        self.home = home
        self.st = []

    def leave(self, t):
        self.st.append((-1e9, t, self.home, 'io', 0.0))
        return self

    def to(self, t, pose, dwell=0.0, ease='io', stagger=0.012):
        if not self.st:
            self.st.append((-1e9, -1e9, self.home, 'io', 0.0))
        self.st.append((t, t + dwell, pose, ease, stagger))
        return self

    def back(self, t, ease='io', stagger=0.012):
        return self.to(t, self.home, 1e9, ease, stagger)

    def __call__(self, t):
        ev = lambda fn: fn(t) if callable(fn) else fn
        if not self.st:
            return ev(self.home)
        prev = self.st[0]
        if t <= prev[1]:
            return ev(prev[2])
        for st in self.st[1:]:
            if t < st[0]:
                span = st[0] - prev[1]
                lag = min(abs(st[4]), span * 0.12)
                k = {}
                for i, dn in enumerate(ORDER):
                    j = i if st[4] >= 0 else len(ORDER) - 1 - i
                    k[dn] = ez((t - prev[1] - lag * j) / (span - lag * 4), st[3])
                return dmix(ev(prev[2]), ev(st[2]), k)
            if t <= st[1]:
                return ev(st[2])
            prev = st
        return ev(prev[2])


# ================================================================ a weapon's poses
MELEE_GUARD = mat_trs((-0.30, -0.06, -0.22), (-20, 0, -30))       # free support fist, rig space (one-handed weapons)
POINT = (0.0, 10.0, 6.0)        # trigger finger off the trigger: flexion of its three joints (it lies along the frame)


class Poser:
    """One weapon's frames and holds: W = carry @ offset @ rotation about the grip."""

    def __init__(self, wid):
        self.wid, self.info, self.a = wid, WEAPONS[wid], ANIM.get(wid, {})
        self.H = handling(wid)
        self.carry = V(self.H['carry'])
        self.GR = mat_trs((0, 0, 0), (-self.info['rake'], 0, 0))
        self.GL = left_hold(wid)
        self.digR, self.digL = self.info.get('dig_R', {}), self.info.get('dig_L', {})
        self.trigger = self.info['cls'] != 'melee'
        self.magS = V(self.info['mag'])
        self.magT = self.magS - RIG['mag0']
        self.maxis = mat_trs((0, 0, 0), (-self.info['mrake'], 0, 0))        # the magazine's own axis (it slides along z)

    def wm(self, wl=(0, 0, 0), wr=(0, 0, 0)):
        R = wr.to_4x4() if isinstance(wr, Matrix) else mat_trs((0, 0, 0), wr)     # melee keys give the rotation itself
        return T(self.carry) @ T(wl) @ R

    def mag_at(self, W, extra=Matrix.Identity(4)):
        """Mag bone delta for the magazine placed at its socket of weapon pose W (extra: motion in mag space)."""
        return W @ T(self.magS) @ extra @ T(-RIG['mag0'])

    def fit(self, key, side, F, sd=None):
        """Digits of a hand closed on this weapon (or on sd) with its frame at F (weapon space); cached by key."""
        c = self.info.setdefault('fits', {})
        if key not in c:
            c[key] = fit_digits(side, sd or bvh_sd(hold_bvh(self.wid)), F @ RIG['F0'][side].inverted())
        return c[key]

    def hand_r(self, off=0.0, trig=0.0):
        """Strong hand's digits in its hold: off 1 = the trigger finger straight along the frame, trig 1 = pulled."""
        d = dict(self.digR)
        if self.trigger:
            i0 = dget(d, 'INDEX')
            rest, S = RIG['REST']['R']['INDEX'], self.H['sprint']
            pt = (S['idx'], POINT[1] - rest[1], POINT[2] - rest[2], S['lift'])
            on = (i0[0], i0[1] + 5 * trig, i0[2] + 9 * trig, i0[3])
            d['INDEX'] = tuple(a + (b - a) * off for a, b in zip(on, pt))
        return d


def shape(side, name, k=1.0):
    return hand_shape(side, name, k)


class Clip:
    """One clip being built (see the notes at the top of the file): set the weapon keys (w), send the hands along
    their paths (L, R), say where the magazine is (M), pose the digits (dL, dR, off, trig); frames() bakes it."""

    def __init__(self, p, dur, loop=False):
        self.p, self.dur, self.loop = p, dur, loop
        self.wk, self._w, self.wadd, self._memo = [], None, [], {}
        self.base = Matrix.Identity(4)   # a turn the weapon keys are measured from (see turned)
        self.R = Path(lambda t: self.W(t) @ p.GR)
        if p.GL is None:                 # one-handed melee: the support fist up in a guard
            self.L = Path(lambda t: MELEE_GUARD)
            self.dL = FPath(shape('L', 'fist'))
        else:
            self.L = Path(lambda t: self.W(t) @ p.GL)
            self.dL = FPath(p.digL)
        self.M = lambda t: self.W(t) @ T(p.magT)
        self.off = self.trig = lambda t: 0.0
        self.dR = FPath(lambda t: p.hand_r(self.off(t), self.trig(t)))
        self.hint = self.wrist = None

    def f(self, x):
        return x * self.dur

    def w(self, t, loc=(0, 0, 0), rot=(0, 0, 0), mode='s'):
        self.wk.append((t, tuple(loc) + tuple(rot), mode))
        self._w = None
        return self

    def wpose(self, t):
        if self._w is None:
            self._w = Track(self.wk or [(0.0, (0,) * 6)], period=self.dur if self.loop else None)
        v = list(self._w(t))
        for fn in self.wadd:
            v = [a + b for a, b in zip(v, fn(t))]
        return v

    def W(self, t):
        k = round(t * 1e5)
        if k not in self._memo:
            v = self.wpose(t)
            self._memo[k] = T(self.p.carry) @ T(v[:3]) @ self.base @ mat_trs((0, 0, 0), v[3:])
        return self._memo[k]

    def pose(self, t):
        P = {'W': self.W(t), 'FR': self.R(t), 'FL': self.L(t), 'mag': self.M(t), 'dig': {'R': self.dR(t), 'L': self.dL(t)}, 'hint': {}}
        if self.wrist is not None:
            P['wrist'] = self.wrist
        if self.hint is not None:
            P['hint'] = {'L': V(self.hint)}
        return P

    def frames(self, n=None):
        n = n if n is not None else max(1, round(self.dur * FPS))
        return [(i, self.pose(self.dur * i / n)) for i in range(n + 1)]


def turned(roll=0.0, pitch=0.0, yaw=0.0):
    """A weapon turn built the way a hand does it: rolled about its own bore, then the muzzle lifted, then swung."""
    return mat_trs((0, 0, 0), (0, 0, yaw)) @ mat_trs((0, 0, 0), (pitch, 0, 0)) @ mat_trs((0, 0, 0), (0, roll, 0))


def scalar(keys, period=None):
    """A number over time: keys (t, value[, mode])."""
    tr = Track(keys, period)
    return lambda t: tr(t)[0]


def life(base, t, period, amp=(1.0, 1.6, 1.2), phase=0.0, thumb=1.2, digits=ORDER):
    """A hold with small finger life: each of `digits` breathes on its own phase (deg), looping over `period`.
    Every joint that moves costs an animation channel in the clip, so life goes where it shows."""
    out = dict(base)
    for i, dn in enumerate(ORDER):
        if dn not in digits:
            continue
        b = dget(base, dn)
        a = 2 * math.pi * (t / period + phase + 0.19 * i)
        s1, s2 = math.sin(a), math.sin(2 * a + 1.3)
        k = thumb if dn == 'THUMB' else 1.0
        out[dn] = (b[0] + amp[0] * s1 * k, b[1] + amp[1] * (0.7 * s1 + 0.3 * s2) * k, b[2] + amp[2] * s2 * k, b[3])
    return out


# ================================================================ held things, grab frames
HELD = {'can': (0.0335, 0.046), 'shell': (0.0105, 0.036)}      # things in the HOLD_L socket: radius, half length (fam_weapons.build_held)


def held_fit(name):
    """Support-hand digits closed on a thing held in the HOLD_L socket."""
    if name not in RIG.setdefault('held', {}):
        r, h = HELD[name]
        F0 = RIG['F0']['L']
        RIG['held'][name] = fit_digits('L', can_sd(r, h, F0 @ T((0.0, HAND['cy'], -0.046))), Matrix.Identity(4))
    return RIG['held'][name]


def grab_frame(p):
    """Support glove wrapped round the magazine body (mag axis = glove grip axis), in mag-socket space."""
    info = p.info
    return p.maxis @ T((0.0, 0.0, -0.006 if info['cls'] == 'pistol' else -0.040))


def charge_frame(ch):
    """Support glove beside a handle at ch (weapon space): closing on it from the left."""
    return T((min(ch[0], -0.020) - 0.026, ch[1] + 0.020, ch[2] - 0.004)) @ mat_trs((0, 0, 0), (-35, 0, -10))


# working a right-side action (bolt, cocking handle): the gun comes forward and across and rolls its right side up
# toward the eye, so the hand's work is in frame (weapon offset, rotation)
ACTION_POSE = ((-0.055, 0.085, 0.018), (7, -24, 15))


def knob_frame(p, W, off, rot):
    """Right glove frame closing on the bolt knob (off: knob travel, rot: wrist roll)."""
    return W @ T(V(p.info['bolt']) + V(off)) @ mat_trs((0, 0, 0), rot) @ T((-0.030, -0.006, 0.010))


def knob_hand(p):
    """Strong hand's digits closed on the bolt knob (fitted where the hand first takes it)."""
    F = T(V(p.info['bolt'])) @ mat_trs((0, 0, 0), (0, 30, 0)) @ T((-0.030, -0.006, 0.010))
    return p.fit('knob', 'R', F)


def vadd(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vmul(a, k):
    return tuple(x * k for x in a)


# ================================================================ reloads
# How each gun is reloaded (ANIM[wid]['out'] / ['chg'], else by style):
#   out   'drop' the magazine falls free (pistols), 'pull' straight out along its axis, 'rock' rocks forward on
#         its front lip first, 'cass' a launcher cassette drawn back and down
#   chg   what makes the gun ready after the magazine is in: 'stop' thumb on the slide stop (the support hand
#         rolls back into the hold), 'release' palm slap on the bolt release, 'handle' the support hand pulls the
#         charging handle (ANIM 'charge': point, pull) and lets it fly, 'slap' it chops a forward cocking handle
#         home, 'rhandle' the strong hand racks a right-side handle, 'bolt' the strong hand works the bolt
RELOAD_T = {    # fractions of the reload: leave, on the mag, mag out, at the pouch (from, to), under the well, seated, charge (at, pulled, released), home, finger on
    'mag': (0.06, 0.145, 0.235, 0.335, 0.385, 0.495, 0.552, 0.665, 0.735, 0.765, 0.87, 0.93),
    'drop': (0.05, 0.10, 0.16, 0.30, 0.36, 0.50, 0.552, 0.66, 0.70, 0.72, 0.84, 0.92),
}


def mag_reload(p, r):
    """Magazine change with real steps. The support hand is locked to the magazine from the grab to the stow and
    from the pouch to the seat (the magazine is in_hand of the hand's own path); the gun tilts to show the well,
    gives when the magazine is pulled, bumps when it seats and jolts when the bolt goes home."""
    info, a, R = p.info, p.a, p.H['reload']
    out = a.get('out', 'drop' if a['style'] == 'pistol' else 'pull')
    chg = a.get('chg', {'pistol': 'stop', 'bolt': 'bolt'}.get(a['style'], 'handle'))
    c = Clip(p, r / FPS)
    f = c.f
    tL, tOn, tOut, tP0, tP1, tUp, tSeat, tC0, tC1, tC2, tHome, tFin = (f(x) for x in RELOAD_T['drop' if out == 'drop' else 'mag'])
    tl, tr = R['tilt']
    sl_, sr_ = R['seat']
    G = grab_frame(p)
    deep = 0.105 if info['cls'] != 'pistol' else 0.085
    # ---- weapon: anticipation, tilt (a little past, settle), give at the pull, drift while the hand is away, seat bump
    c.w(0.0, mode='h').w(f(0.03), (0.002, 0.003, -0.005), (-2.5, -4, 2)).w(tOn - f(0.025), vmul(tl, 1.08), vmul(tr, 1.1))
    if out == 'drop':                   # a flick as the catch is pressed
        c.w(tOn + f(0.03), vadd(tl, (0.002, 0.0, 0.006)), vadd(tr, (3, -4, 2))).w(tOut + f(0.04), tl, tr)
    else:
        c.w(tOn + f(0.02), tl, tr).w(tOut - f(0.03), vadd(tl, (0.0, 0.0, -0.007)), vadd(tr, (-2.5, 1.5, 0))).w(tOut + f(0.035), vadd(tl, (0.001, 0.002, 0.005)), vadd(tr, (1.5, -1, -1)))
    c.w(tP0 + f(0.02), vadd(tl, (0.004, -0.002, 0.002)), vadd(tr, (2, 2.5, -1.5))).w(tUp - f(0.03), vadd(tl, (-0.002, 0.0, -0.002)), vadd(tr, (-1, 3.5, 0.5)))
    c.w(tSeat - f(0.012), vadd(tl, (0.0, 0.0, -0.005)), vadd(tr, (-1.5, 3, 0))).w(tSeat + f(0.018), sl_, sr_).w(tSeat + f(0.06), vadd(tl, (0.0, 0.0, -0.002)), vadd(tr, (-1, 0, 0)))
    c.off = scalar([(0.0, 0.0, 'h'), (f(0.06), 1.0, 'h'), (tFin - f(0.05), 1.0, 'h'), (tFin, 0.0, 'h')])
    # ---- magazine in the well: depth along its own axis and rock about its front lip
    dOut = scalar([(tOn + f(0.025), 0.0, 'h'), (tOut, -deep, 's' if out != 'drop' else 'h')])
    dIn = scalar([(tUp, -0.085, 'h'), (tSeat - f(0.03), -0.045), (tSeat, 0.0, 'h')])
    rock = scalar([(tOn + f(0.02), 0.0, 'h'), (tOn + f(0.055), 20.0 if out == 'rock' else 0.0), (tOut, 26.0 if out == 'rock' else 0.0, 'h')])
    lip = V((0.0, 0.030, 0.0))

    def well(d, ang=0.0):                 # the magazine's motion in its socket
        return T(lip) @ mat_trs((0, 0, 0), (-ang, 0, 0)) @ T(-lip) @ p.maxis @ T((0, 0, d)) @ p.maxis.inverted()
    at_mag = lambda t, X: c.W(t) @ T(p.magS) @ X @ G
    in_hand = lambda FL: FL @ G.inverted() @ T(-RIG['mag0'])
    low = T(V(R['low'])) @ mat_trs((0, 0, 0), (-25, 0, 0)) @ T(p.magS) @ G
    gm = p.fit('mag', 'L', G, bvh_sd(hold_bvh(p.wid, gun=False)))
    openL = dmix(p.digL, shape('L', 'relaxed'), 0.75)
    L, dL = c.L.leave(tL), c.dL.leave(tL - f(0.01))
    if out == 'drop':
        # the magazine drops free: a flick of the gun, the old one falls out of frame; the hand is already on its way
        # to the pouch for the fresh one
        tRel = tOn
        L.to(tP0, low, tP1 - tP0, ease='io', arc=(-0.03, -0.02, 0.0))
        dL.to(tL + f(0.07), openL).to(tP0, gm, tSeat + f(0.03) - tP0)
        W0 = c.W(tRel)
        ax = (W0.to_3x3() @ p.maxis.to_3x3() @ V((0, 0, -1))).normalized()

        def fall(t):
            u = t - tRel
            return T(ax * (0.9 * u) + V((0, 0, -4.9 * u * u))) @ p.mag_at(W0, mat_trs((0, 0, 0), (-60 * u, 0, 30 * u)))
    else:
        # grab, rock / pull out (hand and magazine share the depth track), stow
        L.to(tOn, lambda t: at_mag(t, well(dOut(t), rock(t))), tOut - tOn, ease='out', arc=(-0.015, 0.0, -0.02))
        L.to(tP0, low, tP1 - tP0, ease='in', arc=(-0.04, -0.02, 0.01))
        dL.to(tOn - f(0.02), openL).to(tOn + f(0.02), gm, tSeat + f(0.03) - tOn - f(0.02), stagger=0.008)
    # fresh magazine up from the pouch on an arc, lined up under the well, driven home
    L.to(tUp, lambda t: at_mag(t, well(dIn(t))), tSeat + f(0.03) - tUp, ease='io', arc=(-0.035, 0.03, 0.02))

    def mag(t):
        if out == 'drop':
            if t < tRel:
                return c.W(t) @ T(p.magT)
            if t < tP0 + (tP1 - tP0) * 0.5:
                return fall(t)
        elif t < tOut:
            return p.mag_at(c.W(t), well(dOut(t), rock(t)))
        if t < tUp:
            return in_hand(L(t))                      # stowed, and the fresh one carried up: locked to the hand
        return p.mag_at(c.W(t), well(dIn(t)))
    c.M = mag
    # ---- make ready
    stance = ((0.0, 0.0, -0.006), (6, -6, -10))
    if chg == 'stop':
        # pistol: the support hand rolls back into the two-hand hold while the thumb drops the slide: a jolt forward
        dL.to(tSeat + f(0.05), dmix(gm, shape('L', 'relaxed'), 0.6))
        L.back(tHome, ease='io', arc=(-0.02, -0.01, -0.01))
        dL.back(tHome + f(0.03))
        c.w(tC0 - f(0.03), (0.0, -0.004, 0.004), (5, 6, -4)).w(tC0 + f(0.012), (0.0, 0.007, -0.003), (-4, 2, -1)).w(tC0 + f(0.06), (0.0, -0.002, 0.002), (2, -1, 0.5))
        thumb = scalar([(tC0 - f(0.05), 0.0, 'h'), (tC0, 1.0), (tC0 + f(0.06), 0.0, 'h')])
        base = c.dR.home
        c.dR = FPath(lambda t: dadd(base(t), {'THUMB': (6 * thumb(t), 10 * thumb(t), 14 * thumb(t), 0.0)}))
    elif chg in ('rhandle', 'bolt'):
        # the support hand goes back to the forend; the strong hand leaves the grip and works the action
        L.back(tC0 - f(0.02), arc=(-0.02, 0.0, -0.02))
        dL.to(tSeat + f(0.05), openL).back(tC0)
        W0 = lambda t: c.W(t)
        al, ar = ACTION_POSE
        c.w(tC0 - f(0.01), al, ar)
        if chg == 'bolt':
            kh = knob_hand(p)
            k0, k1, k2 = ((0, 0, 0), (0, 30, 0)), ((-0.010, 0, 0.020), (0, -20, 0)), ((-0.010, -0.065, 0.020), (0, -20, 0))
        else:
            ch, pull = a['charge']
            Fh = T(V(ch)) @ mat_trs((0, 0, 0), (0, 30, 0)) @ T((-0.030, -0.006, 0.010))
            kh = p.fit('rh', 'R', Fh)
        tA, tB, tCc, tD, tE = tC0, tC0 + f(0.045), tC0 + f(0.10), tC0 + f(0.15), tC0 + f(0.185)
        if chg == 'bolt':
            Rp = c.R.leave(tA - f(0.045))
            Rp.to(tA, lambda t: knob_frame(p, W0(t), *k0), 0.0, ease='out', arc=(0.02, -0.01, 0.02))
            Rp.to(tB, lambda t: knob_frame(p, W0(t), *k1), 0.0, ease='out').to(tCc, lambda t: knob_frame(p, W0(t), *k2), f(0.012), ease='out')
            Rp.to(tD, lambda t: knob_frame(p, W0(t), *k1), 0.0, ease='in').to(tE, lambda t: knob_frame(p, W0(t), *k0), f(0.01), ease='out')
        else:
            hf = lambda u: (lambda t: W0(t) @ T(V(pull) * u) @ Fh)
            Rp = c.R.leave(tA - f(0.045))
            Rp.to(tA, hf(0.0), f(0.015), ease='out', arc=(0.02, -0.01, 0.02)).to(tCc, hf(1.0), 0.0, ease='out').to(tCc + f(0.02), hf(1.15), 0.0, ease='lin')
            tE = tCc + f(0.03)
        Rp.back(tHome + f(0.02), arc=(0.015, -0.01, -0.01))
        c.dR.leave(tA - f(0.05)).to(tA - f(0.015), dmix(p.hand_r(1.0), shape('R', 'relaxed'), 0.7)).to(tA + f(0.012), kh, tE - tA).to(tE + f(0.03), dmix(kh, shape('R', 'relaxed'), 0.6)).back(tHome + f(0.035))
        c.w(tCc, vadd(al, (0.0, -0.009, 0.002)), vadd(ar, (3, -2, -3))).w(tE + f(0.012), vadd(al, (0.0, 0.007, -0.003)), vadd(ar, (-2, 3, 1)))
    else:
        ch, pull = a['charge']
        Fs = charge_frame(ch)
        gc = p.fit('charge', 'L', Fs)
        pv = V(pull)
        c.w(tC0 - f(0.035), stance[0], stance[1])
        if chg == 'release':
            # palm slap on the bolt release: in fast, off at once; the bolt slams and the gun jolts forward
            flat = dmix(gc, shape('L', 'relaxed'), 0.8)
            L.to(tC0, lambda t: c.W(t) @ Fs, f(0.012), ease='in', arc=(-0.03, 0.0, 0.01))
            dL.to(tC0 - f(0.03), flat)
            L.back(tHome, arc=(-0.03, 0.0, -0.01))
            dL.back(tHome + f(0.025))
            c.w(tC0 + f(0.008), vadd(stance[0], (0.004, 0.0, 0.0)), vadd(stance[1], (0, 3.5, -2.5))).w(tC0 + f(0.03), (0.0, 0.007, -0.002), (0.5, -2, -3)).w(tC0 + f(0.075), (0.0, -0.002, 0.001), (3, -1.5, -2))
        elif chg == 'slap':
            # chop the forward cocking handle home from above
            up = lambda t: c.W(t) @ T((-0.02, 0.0, 0.07)) @ Fs
            flat = dmix(gc, shape('L', 'relaxed'), 0.7)
            L.to(tC0, up, f(0.02), arc=(-0.03, 0.0, 0.0)).to(tC1, lambda t: c.W(t) @ Fs, 0.0, ease='in3').to(tC1 + f(0.03), lambda t: c.W(t) @ T((0.0, 0.01, -0.035)) @ Fs, 0.0, ease='out')
            dL.to(tC0 - f(0.03), flat)
            L.back(tHome, arc=(-0.02, 0.0, -0.02))
            dL.back(tHome + f(0.025))
            c.w(tC1 - f(0.01), vadd(stance[0], (0.0, 0.0, 0.003)), vadd(stance[1], (1, 0, 0))).w(tC1 + f(0.015), vadd(stance[0], (0.0, 0.004, -0.010)), vadd(stance[1], (-4, 2, -1))).w(tC1 + f(0.07), (0.0, -0.001, 0.002), (3, -2, -3))
        else:
            # pull the charging handle with the support hand and let it fly
            pu = scalar([(tC0 + f(0.02), 0.0, 'h'), (tC1, 1.0, 'h')])
            L.to(tC0, lambda t: c.W(t) @ T(pv * pu(t)) @ Fs, tC1 - tC0, arc=(-0.03, 0.0, 0.015))
            L.to(tC2, lambda t: c.W(t) @ T(pv * 1.25 + V((-0.012, 0.0, 0.004))) @ Fs, 0.0, ease='out')
            dL.to(tC0 - f(0.03), dmix(gc, shape('L', 'relaxed'), 0.6)).to(tC0 + f(0.015), gc, tC1 - tC0 - f(0.015), stagger=0.006).to(tC2, dmix(gc, shape('L', 'open'), 0.55), stagger=-0.006)
            L.back(tHome, arc=(-0.02, 0.0, -0.02))
            dL.back(tHome + f(0.025))
            pn = pv.normalized()
            c.w(tC1, vadd(stance[0], tuple(pn * -0.004)), vadd(stance[1], (2, 0, 0))).w(tC1 + f(0.02), vadd(stance[0], tuple(pn * -0.009)), vadd(stance[1], (-2, 1, 0))).w(tC2 + f(0.04), (0.0, -0.001, 0.001), (3, -3, -4))
    # ---- back into the shoulder: a little past rest, a small counter-swing, rest
    c.w(tHome + f(0.015), (0.0, 0.003, 0.003), (-1.6, -1.0, 0.8)).w(tFin, (0.0, -0.001, -0.001), (0.6, 0.3, -0.2)).w(c.dur, mode='h')
    return c


def revolver_reload(p, r):
    """Open (thumb on the latch, the cylinder swings out on its crane), muzzle up and a palm strike on the ejector
    rod, muzzle down, a speed loader in from the pouch, a flick of the wrist that swings the cylinder shut."""
    info = p.info
    c = Clip(p, r / FPS)
    f = c.f
    piv = V(info['pivot'])
    sw = scalar([(f(0.10), 0.0, 'h'), (f(0.17), 92.0), (f(0.20), 85.0, 'h'), (f(0.74), 85.0, 'h'), (f(0.775), 0.0, 'h')])
    c.M = lambda t: c.W(t) @ T(piv) @ mat_trs((0, 0, 0), (0, 0, -sw(t))) @ T(-piv) @ T(p.magT)
    t1 = ((0.0, 0.0, -0.010), (10, -30, -8))            # canted left, the cylinder side up
    t2 = ((0.0, -0.030, 0.035), (58, -20, -10))         # muzzle up: cases out
    t3 = ((0.0, 0.0, -0.022), (-26, -26, -8))           # muzzle down: rounds in
    c.w(0.0, mode='h').w(f(0.03), (0.0, 0.003, 0.004), (-3, 5, 2)).w(f(0.11), *t1).w(f(0.17), vadd(t1[0], (-0.004, 0, 0)), vadd(t1[1], (0, -6, -3))).w(f(0.21), *t1)
    c.w(f(0.30), vadd(t2[0], (0, 0, 0.006)), vadd(t2[1], (5, 0, 0))).w(f(0.335), vadd(t2[0], (0, -0.006, -0.008)), vadd(t2[1], (-4, 0, 0))).w(f(0.38), *t2)
    c.w(f(0.47), *t3).w(f(0.54), vadd(t3[0], (0, 0, 0.003)), vadd(t3[1], (2, 0, 1))).w(f(0.585), vadd(t3[0], (0, -0.003, -0.006)), vadd(t3[1], (-3, 0, 0))).w(f(0.66), *t3)
    c.w(f(0.74), (0.004, 0.0, 0.004), (4, -34, -14)).w(f(0.775), (-0.004, 0.0, -0.002), (2, 12, 8)).w(f(0.83), (0.0, 0.002, 0.003), (-2, -4, -2)).w(f(0.92), (0.0, -0.001, -0.001), (0.6, 1, 0.4)).w(c.dur, mode='h')
    c.off = scalar([(0.0, 0.0, 'h'), (f(0.06), 1.0, 'h'), (f(0.86), 1.0, 'h'), (f(0.93), 0.0, 'h')])
    side = lambda t: c.W(t) @ T((-0.040, 0.030, 0.005)) @ mat_trs((0, 0, 0), (-90, 0, -90))        # cupping the frame under the cylinder
    rod = lambda t: c.W(t) @ T((-0.034, 0.105, 0.0)) @ mat_trs((0, 0, 0), (0, 0, -90))             # palm over the ejector rod
    rod2 = lambda t: c.W(t) @ T((-0.034, 0.075, 0.0)) @ mat_trs((0, 0, 0), (0, 0, -90))
    load = lambda t: c.W(t) @ T((-0.060, 0.030, 0.012)) @ mat_trs((0, 0, 0), (-90, 0, -90))        # speed loader behind the open cylinder
    load2 = lambda t: c.W(t) @ T((-0.044, 0.058, 0.010)) @ mat_trs((0, 0, 0), (-90, 0, -90))
    low = T((-0.16, -0.10, -0.46)) @ mat_trs((0, 0, 0), (-40, 0, 0))
    cup, fist = shape('L', 'relaxed'), shape('L', 'fist', 0.7)
    c.L.leave(f(0.05)).to(f(0.12), side, f(0.10), arc=(-0.02, 0.0, -0.02)).to(f(0.30), rod, 0.0, arc=(-0.02, 0.0, 0.03)).to(f(0.335), rod2, f(0.01), ease='in')
    c.L.to(f(0.44), low, f(0.03), arc=(-0.05, -0.02, 0.0)).to(f(0.54), load, 0.0, arc=(-0.04, 0.02, 0.02)).to(f(0.585), load2, f(0.02), ease='in').to(f(0.66), side, f(0.09), ease='out')
    c.L.back(f(0.87), arc=(-0.02, -0.01, -0.01))
    c.dL.leave(f(0.04)).to(f(0.11), cup, f(0.12)).to(f(0.29), shape('L', 'open', 0.8), f(0.05)).to(f(0.43), fist, f(0.14)).to(f(0.62), shape('L', 'open', 0.6), stagger=-0.008).to(f(0.68), cup, f(0.08)).back(f(0.90))
    thumb = scalar([(f(0.06), 0.0, 'h'), (f(0.10), 1.0), (f(0.16), 0.0, 'h')])
    base = c.dR.home
    c.dR = FPath(lambda t: dadd(base(t), {'THUMB': (8 * thumb(t), 12 * thumb(t), 10 * thumb(t), 0.0)}))
    return c


def shell_reload(p, r):
    """One shell (the game loops this clip per shell and shows the shell in the HOLD_L socket from 22 % to 72 %):
    the gun stays rolled over with the port up; the hand is at the belt at 22 %, carries the shell up on an arc,
    thumbs it into the port by 72 % and drops back toward the belt. The first and last frames are the same pose."""
    c = Clip(p, r / FPS, loop=True)
    f = c.f
    c.base = turned(roll=100, pitch=38, yaw=8)             # rolled right over and the muzzle up: the loading port faces the eye
    tl, tr = (-0.040, 0.000, 0.060), (0, 0, 0)
    c.w(0.0, tl, tr).w(f(0.30), vadd(tl, (0.001, 0.0, 0.002)), vadd(tr, (0.8, 1, 0))).w(f(0.62), vadd(tl, (0.0, -0.002, -0.003)), vadd(tr, (-1.2, 0, 0.5)))
    c.w(f(0.72), vadd(tl, (0.0, 0.004, 0.003)), vadd(tr, (1.5, -1, -0.5))).w(f(0.86), vadd(tl, (0.0, -0.001, 0.0)), vadd(tr, (-0.4, 0, 0)))
    port = lambda d: (lambda t: c.W(t) @ T(V(p.info['port']) + V((0.0, d, -0.046))) @ mat_trs((0, 0, 0), (0, 180, 0)))
    low = T((-0.15, -0.06, -0.40)) @ mat_trs((0, 0, 0), (-40, 0, 0))
    mid = T((-0.10, -0.03, -0.22)) @ mat_trs((0, 0, 0), (-28, 30, 0))
    c.L.to(0.0, mid).to(f(0.20), low, f(0.04), ease='out').to(f(0.56), port(-0.050), 0.0, ease='io', arc=(-0.03, 0.0, 0.02)).to(f(0.70), port(0.0), f(0.03), ease='in').to(c.dur, mid, 1.0, ease='io')
    sh = held_fit('shell')
    push = dadd(sh, {'THUMB': (8, 14, 10, 0)})
    rel = dmix(sh, shape('L', 'relaxed'), 0.7)
    c.dL.to(0.0, rel).to(f(0.20), sh, f(0.42), stagger=0.004).to(f(0.70), push, f(0.02)).to(f(0.80), rel, 1.0, stagger=-0.004)
    c.off = lambda t: 1.0
    return c


def lmg_reload(p, r):
    """Belt-fed: the support hand lifts the feed cover (a lift at its latch), takes the box and its belt down and
    away, brings a fresh box up and seats it, lays the belt in the tray, slaps the cover shut; the strong hand
    then racks the cocking handle on the right."""
    info, a, R = p.info, p.a, p.H['reload']
    c = Clip(p, r / FPS)
    f = c.f
    tl, tr = R['tilt']
    G = grab_frame(p)
    cover = V((-0.012, 0.015, 0.090))             # where the hand takes the feed cover (it hinges at the front), clear of the eye
    Fc = charge_frame(cover)
    gcv = p.fit('cover', 'L', Fc)
    lift = scalar([(f(0.10), 0.0, 'h'), (f(0.15), 1.0, 'h')])
    c.w(0.0, mode='h').w(f(0.025), (0.002, 0.002, -0.004), (-2, -3, 1.5)).w(f(0.07), (0.0, -0.004, 0.010), (4, 10, -6)).w(f(0.15), (0.0, -0.010, 0.022), (7, 14, -8))
    c.w(f(0.20), tl, tr).w(f(0.275), vadd(tl, (0, 0, -0.008)), vadd(tr, (-3, 2, 0))).w(f(0.33), vadd(tl, (0.002, 0.002, 0.004)), vadd(tr, (1.5, -1, -1)))
    c.w(f(0.44), vadd(tl, (0.003, -0.002, 0.0)), vadd(tr, (1, 3, -1))).w(f(0.535), vadd(tl, (0, 0, -0.006)), vadd(tr, (-2, 3, 0))).w(f(0.56), R['seat'][0], R['seat'][1])
    c.w(f(0.62), (0.0, -0.010, 0.020), (7, 12, -8)).w(f(0.70), (0.0, -0.008, 0.018), (6, 8, -6)).w(f(0.725), (0.0, -0.004, 0.004), (-3, 4, -3)).w(f(0.77), (0.0, -0.002, 0.004), (4, -4, -4))
    c.off = scalar([(0.0, 0.0, 'h'), (f(0.05), 1.0, 'h'), (f(0.90), 1.0, 'h'), (f(0.95), 0.0, 'h')])
    dOut = scalar([(f(0.225), 0.0, 'h'), (f(0.285), -0.12)])
    dIn = scalar([(f(0.50), -0.10, 'h'), (f(0.535), -0.05), (f(0.555), 0.0, 'h')])
    well = lambda d: T((0, 0, d))
    at_mag = lambda t, X: c.W(t) @ T(p.magS) @ X @ G
    in_hand = lambda FL: FL @ G.inverted() @ T(-RIG['mag0'])
    low = T(V(R['low'])) @ mat_trs((0, 0, 0), (-25, 0, 0)) @ T(p.magS) @ G
    gm = p.fit('mag', 'L', G, bvh_sd(hold_bvh(p.wid, gun=False)))
    openL = dmix(p.digL, shape('L', 'relaxed'), 0.75)
    flat = shape('L', 'open', 0.8)
    L = c.L.leave(f(0.04))
    L.to(f(0.10), lambda t: c.W(t) @ T(V((0.0, 0.02, 0.05)) * lift(t)) @ Fc, f(0.06), arc=(-0.03, 0.0, 0.03))               # lift the cover
    L.to(f(0.215), lambda t: at_mag(t, well(dOut(t))), f(0.07), arc=(-0.03, 0.0, 0.0))                                        # box out
    L.to(f(0.37), low, f(0.05), ease='in', arc=(-0.04, -0.02, 0.01))
    L.to(f(0.50), lambda t: at_mag(t, well(dIn(t))), f(0.075), arc=(-0.035, 0.03, 0.02))                                      # fresh box in
    tray = lambda t: c.W(t) @ charge_frame(V((-0.030, 0.045, 0.070)))
    L.to(f(0.635), tray, f(0.03), arc=(-0.03, 0.0, 0.02))                                                                      # lay the belt
    L.to(f(0.70), lambda t: c.W(t) @ T((0.0, 0.03, 0.06)) @ Fc, 0.0, arc=(-0.01, 0.0, 0.03)).to(f(0.722), lambda t: c.W(t) @ Fc, f(0.012), ease='in3')   # slap the cover shut
    L.back(f(0.80), arc=(-0.03, 0.0, -0.01))
    c.dL.leave(f(0.03)).to(f(0.09), dmix(gcv, shape('L', 'relaxed'), 0.5)).to(f(0.11), gcv, f(0.05)).to(f(0.20), openL).to(f(0.235), gm, f(0.34), stagger=0.008)
    c.dL.to(f(0.62), dmix(gcv, shape('L', 'relaxed'), 0.6), f(0.05)).to(f(0.70), flat, f(0.035)).back(f(0.83))

    def mag(t):
        if t < f(0.285):
            return p.mag_at(c.W(t), well(dOut(t)))
        if t < f(0.50):
            return in_hand(L(t))
        return p.mag_at(c.W(t), well(dIn(t)))
    c.M = mag
    # the strong hand racks the cocking handle
    ch, pull = a['charge']
    Fh = T(V(ch)) @ mat_trs((0, 0, 0), (0, 30, 0)) @ T((-0.030, -0.006, 0.010))
    kh = p.fit('rh', 'R', Fh)
    hf = lambda u: (lambda t: c.W(t) @ T(V(pull) * u) @ Fh)
    tA = f(0.815)
    c.R.leave(tA - f(0.04)).to(tA, hf(0.0), f(0.012), ease='out', arc=(0.02, -0.01, 0.02)).to(tA + f(0.045), hf(1.0), 0.0, ease='out').to(tA + f(0.06), hf(1.15), 0.0, ease='lin').back(f(0.945), arc=(0.015, -0.01, -0.01))
    c.dR.leave(tA - f(0.045)).to(tA - f(0.012), dmix(p.hand_r(1.0), shape('R', 'relaxed'), 0.7)).to(tA + f(0.01), kh, f(0.045)).to(tA + f(0.08), dmix(kh, shape('R', 'relaxed'), 0.6)).back(f(0.955))
    al, ar = ACTION_POSE
    c.w(tA - f(0.005), al, ar).w(tA + f(0.045), vadd(al, (0.0, -0.009, 0.002)), vadd(ar, (3, -2, -3))).w(tA + f(0.07), vadd(al, (0.0, 0.007, -0.003)), vadd(ar, (-2, 3, 1))).w(f(0.93), (0.0, 0.002, 0.002), (-1.5, -1, 0.6)).w(f(0.97), (0.0, -0.001, 0.0), (0.4, 0.2, 0)).w(c.dur, mode='h')
    return c


# ================================================================ fire
def kick_of(p):
    a, K = p.a, p.H['kick']
    heavy = a.get('heavy', 0.0)
    kick = (tuple(c * (1 + 0.8 * heavy) for c in K['loc']), tuple(c * (1 + 0.9 * heavy) for c in K['rot']))
    rec = (tuple(c * (1 + 0.5 * heavy) for c in K['recover'][0]), tuple(c * (1 + 0.5 * heavy) for c in K['recover'][1]))
    return kick, rec


def shot(c, t0, kick, rec, tail, lag=True):
    """One shot on a clip starting at t0: the trigger breaks, the gun snaps back within a frame, rides forward past
    rest and settles over `tail` seconds; the support hand gives a touch later than the gun (lag)."""
    fr = 1.0 / FPS
    c.w(t0, mode='h').w(t0 + fr, kick[0], kick[1], 'h')
    if tail > 3.5 * fr:
        c.w(t0 + fr + tail * 0.42, rec[0], rec[1]).w(t0 + fr + tail * 0.75, vmul(rec[0], -0.3), vmul(rec[1], -0.3))
    c.w(t0 + fr + tail, mode='h')


def fire_clip(p, n):
    """Semi / auto / burst: one cycle. The game adds the spring kick on top; the clip gives the snap, the forward
    ride and the trigger finger."""
    a = p.a
    c = Clip(p, n / FPS)
    kick, rec = kick_of(p)
    fr = 1.0 / FPS
    pulls = [(0.0, 1.0, 'h')]
    if a.get('burst'):
        g = max(1, round(a['gap'] * FPS))
        for i in range(a['burst']):
            last = i == a['burst'] - 1
            c.w(i * g * fr, vmul(kick[0], 0.35 * (i > 0)), vmul(kick[1], 0.35 * (i > 0)), 'h').w(i * g * fr + fr, vmul(kick[0], 1 + 0.25 * i), vmul(kick[1], 1 + 0.25 * i), 'h')
        t1 = ((a['burst'] - 1) * g + 1) * fr
        if c.dur - t1 > 3.5 * fr:
            c.w(t1 + (c.dur - t1) * 0.45, rec[0], rec[1]).w(t1 + (c.dur - t1) * 0.78, vmul(rec[0], -0.3), vmul(rec[1], -0.3))
        c.w(c.dur, mode='h')
        pulls += [(t1, 1.0, 'h'), (min(c.dur, t1 + 3 * fr), 0.15, 'h')]
    else:
        shot(c, 0.0, kick, rec, c.dur - fr)
        pulls += [(fr, 1.0, 'h'), (min(c.dur, 4 * fr), 0.2, 'h')] if n > 2 else [(c.dur, 0.6, 'h')]
    c.trig = scalar(pulls)
    # the support hand rides the kick a touch late and a little less: it slips on the forend for a frame
    if p.GL is not None and n >= 3:
        slip = scalar([(0.0, 0.0, 'h'), (fr, 1.0, 'h'), (min(c.dur, 3 * fr), 0.0, 'h')])
        c.L = Path(lambda t: c.W(t) @ T(V(kick[0]) * (-0.35 * slip(t))) @ p.GL)
    return c


def revolver_fire(p, n):
    """One shot: the trigger breaks, the muzzle kicks, and the cylinder (the Mag part) turns one chamber, 60 deg
    about the bore. The cylinder is six-fold symmetric, so the clip ends on the indexed cylinder and the rest poses
    (which the game crossfades to) show it unchanged."""
    c = Clip(p, n / FPS)
    kick, rec = kick_of(p)
    fr = 1.0 / FPS
    c.w(0.0, mode='h').w(fr, kick[0], kick[1], 'h').w(c.dur, mode='h')
    turn = scalar([(0.0, 0.0, 'h'), (fr, 60.0, 'h')])
    c.M = lambda t: p.mag_at(c.W(t), mat_trs((0, 0, 0), (0, turn(t), 0)))
    c.trig = scalar([(0.0, 1.0, 'h'), (c.dur, 0.5, 'h')])
    return c


def bolt_cycle(p, n):
    """Shot, then the strong hand leaves the grip, lifts the bolt, draws it back, runs it home, turns it down and
    comes back to the grip; the rifle rolls and dips under the hand's work and settles."""
    c = Clip(p, n / FPS)
    f = c.f
    kick, rec = kick_of(p)
    fr = 1.0 / FPS
    al, ar = ACTION_POSE
    c.w(0.0, mode='h').w(2 * fr, kick[0], kick[1], 'h').w(f(0.10), rec[0], rec[1]).w(f(0.24), vmul(al, 1.0), vmul(ar, 1.05))
    c.w(f(0.31), vadd(al, (0.002, 0.0, 0.005)), vadd(ar, (2, -4, -2))).w(f(0.42), vadd(al, (0.0, -0.010, 0.002)), vadd(ar, (3, -2, -3))).w(f(0.50), vadd(al, (0.0, -0.006, 0.002)), vadd(ar, (2, -1, -2)))
    c.w(f(0.60), vadd(al, (0.0, 0.008, -0.002)), vadd(ar, (-2, 1, 1))).w(f(0.68), vadd(al, (-0.002, 0.002, -0.006)), vadd(ar, (-3, 6, 2))).w(f(0.86), (0.0, 0.002, 0.003), (-1.2, -1.5, 0.8)).w(f(0.94), (0.0, -0.001, -0.001), (0.4, 0.5, -0.2)).w(c.dur, mode='h')
    kh = knob_hand(p)
    k0, k1, k2 = ((0, 0, 0), (0, 30, 0)), ((-0.010, 0, 0.020), (0, -20, 0)), ((-0.010, -0.065, 0.020), (0, -20, 0))
    kf = lambda k: (lambda t: knob_frame(p, c.W(t), *k))
    c.R.leave(f(0.13)).to(f(0.24), kf(k0), f(0.02), ease='out', arc=(0.02, -0.01, 0.025)).to(f(0.31), kf(k1), 0.0, ease='out').to(f(0.42), kf(k2), f(0.03), ease='out')
    c.R.to(f(0.58), kf(k1), 0.0, ease='in').to(f(0.66), kf(k0), f(0.02), ease='out').back(f(0.86), arc=(0.015, -0.01, -0.012))
    c.dR.leave(f(0.11)).to(f(0.20), dmix(p.hand_r(1.0), shape('R', 'relaxed'), 0.7)).to(f(0.255), kh, f(0.43), stagger=0.006).to(f(0.74), dmix(kh, shape('R', 'relaxed'), 0.6), stagger=-0.006).back(f(0.89))
    c.trig = scalar([(0.0, 1.0, 'h'), (3 * fr, 1.0, 'h'), (f(0.12), 0.0, 'h')])
    c.off = scalar([(f(0.10), 0.0, 'h'), (f(0.14), 1.0, 'h'), (f(0.86), 1.0, 'h'), (f(0.93), 0.0, 'h')])
    return c


def pump_fire(p, n):
    """Shot, then the support hand racks the pump (forend = the Mag part, locked to the hand by one travel track):
    back hard, a beat, forward to the stop; the gun is tugged back and shoved forward with it."""
    c = Clip(p, n / FPS)
    f = c.f
    kick, rec = kick_of(p)
    fr = 1.0 / FPS
    s = scalar([(f(0.26), 0.0, 'h'), (f(0.33), -0.030), (f(0.42), -0.072, 'h'), (f(0.50), -0.070, 'h'), (f(0.57), -0.035), (f(0.645), 0.0, 'h')])
    c.w(0.0, mode='h').w(fr, kick[0], kick[1], 'h').w(f(0.14), rec[0], rec[1]).w(f(0.24), (0.0, 0.001, 0.002), (1.5, 0, 0))
    c.w(f(0.42), (0.0, -0.012, 0.004), (4.5, 2, -1)).w(f(0.50), (0.0, -0.008, 0.003), (3.5, 1.5, -1)).w(f(0.655), (0.0, 0.009, -0.004), (-2.5, -1, 0.5)).w(f(0.76), (0.0, -0.002, 0.002), (1.2, 0.5, 0)).w(f(0.88), (0.0, 0.0005, -0.0005), (-0.4, 0, 0)).w(c.dur, mode='h')
    c.L = Path(lambda t: c.W(t) @ T((0, s(t), 0)) @ p.GL)
    c.M = lambda t: p.mag_at(c.W(t), T((0, s(t), 0)))
    grip = dadd(p.digL, {dn: (4, 5, 3, 0) for dn in FINGERS})
    c.dL = FPath(p.digL).leave(f(0.20)).to(f(0.27), grip, f(0.38)).back(f(0.75))
    c.trig = scalar([(0.0, 1.0, 'h'), (3 * fr, 1.0, 'h'), (f(0.22), 0.0, 'h')])
    return c


def launcher_fire(p, n):
    """Launchers: a heavy shove back and up, a long ride forward, a slow settle; both hands clamp down."""
    c = Clip(p, n / FPS)
    f = c.f
    kick, rec = kick_of(p)
    fr = 1.0 / FPS
    c.w(0.0, mode='h').w(fr, vmul(kick[0], 0.8), vmul(kick[1], 0.7), 'h').w(3 * fr, kick[0], kick[1]).w(f(0.38), rec[0], rec[1]).w(f(0.58), vmul(rec[0], -0.5), vmul(rec[1], -0.5)).w(f(0.80), vmul(rec[0], 0.2), vmul(rec[1], 0.2)).w(c.dur, mode='h')
    grip = dadd(p.digL, {dn: (3, 5, 4, 0) for dn in FINGERS})
    c.dL = FPath(p.digL).to(fr, grip, f(0.2)).back(f(0.6))
    c.trig = scalar([(0.0, 1.0, 'h'), (4 * fr, 1.0, 'h'), (f(0.4), 0.0, 'h')])
    return c


# ================================================================ loops: idle, sprint, slide
def idle_clip(p):
    """2 s breathing loop: the gun drifts round a slow figure of eight (under the game's own sway), the fingers
    breathe on their own phases and the support hand re-seats its grip once a loop."""
    ia, ib = p.H['idle']
    c = Clip(p, 2.0, loop=True)
    c.w(0.0).w(0.5, *ia).w(1.0, vmul(ia[0], -0.25), vmul(ib[1], 0.3)).w(1.5, *ib)
    seat = scalar([(0.0, 0.0), (1.15, 0.0, 'h'), (1.32, 1.0), (1.58, 0.0, 'h')], period=2.0)
    baseR = c.dR.home
    c.dR = FPath(lambda t: life(baseR(t), t, 2.0, amp=(1.0, 1.8, 0.0), phase=0.3, digits=('THUMB',)))
    if p.GL is not None:
        lift = {dn: (-3.0, -4.5, 0.0, 0.0) for dn in FINGERS}
        c.dL = FPath(lambda t: dadd(life(p.digL, t, 2.0, amp=(0.8, 1.4, 0.0)), {dn: vmul(lift[dn], seat(t - 0.05 * i)) for i, dn in enumerate(FINGERS)}))
    c.trig = scalar([(0.0, 0.0), (0.7, 0.12), (1.4, 0.0)], period=2.0)
    return c


def free_path(q, period, hint=None, side='L'):
    """A free hand swinging through the stations q = [(t, (NDC x, y, depth m), palm, (flex, deviation))] of a loop:
    built from its forearm on every frame (free_hand), so its wrist stays straight all the way."""
    tr = Track([(t, tuple(pos) + tuple(palm) + tuple(bend)) for t, pos, palm, bend in q], period=period)

    def fn(t):
        v = tr(t)
        return free_hand(side, at_ndc(*v[:3]), v[3:6], v[6:8], hint)
    return fn


def sprint_clip(p):
    """0.6 s loop, two footfalls (the game phases it by the distance run): the gun swings between its two carry
    poses on an arc with a drop on each footfall; pistols at high ready with the free fist pumping, long guns at
    low ready across the chest with both hands on; the trigger finger lies along the frame."""
    S = p.H['sprint']
    c = Clip(p, 0.6, loop=True)
    a, b = S['a'], S['b']
    mid = lambda k: (tuple((x + y) / 2 for x, y in zip(a[0], b[0])), tuple((x + y) / 2 for x, y in zip(a[1], b[1])))
    up = (0.0, 0.0, 0.006)
    c.w(0.0, *a).w(0.15, vadd(mid(0)[0], up), vadd(mid(0)[1], (1.2, 1.5, -1))).w(0.30, *b).w(0.45, vadd(mid(0)[0], vmul(up, 0.7)), vadd(mid(0)[1], (-1.0, -1.5, 1)))
    c.off = lambda t: 1.0
    if S['style'] == 'high':
        (pa, na, ba), (pb, nb, bb) = S['pump']
        pm = tuple((x + y) / 2 for x, y in zip(pa, pb))
        q = [(0.0, pa, na, ba), (0.15, (pm[0] + 0.05, pm[1], pm[2] - 0.02), na, (ba[0] + 6, ba[1])), (0.30, pb, nb, bb), (0.45, (pm[0] - 0.05, pm[1], pm[2] + 0.02), nb, (bb[0] - 4, bb[1]))]
        c.L = Path(free_path(q, 0.6))
        c.dL = FPath(shape('L', 'fist'))
    elif p.GL is not None:
        c.dL = FPath(dadd(p.digL, {dn: (2, 3, 2, 0) for dn in FINGERS}))
    return c


def slide_clip(p):
    """0.5 s loop: the gun tucked low and canted in, shaking with the ground; the support arm out to the lower
    left for balance, palm down, fingers spread and working."""
    Sl = p.H['slide']
    c = Clip(p, 0.5, loop=True)
    a, b = Sl['a'], Sl['b']
    c.w(0.0, *a).w(0.11, vadd(a[0], (0.001, 0.0, 0.003)), vadd(b[1], (0.8, 0, 0))).w(0.25, *b).w(0.39, vadd(b[0], (-0.001, 0.001, 0.002)), vadd(a[1], (-0.6, 0, 0)))
    (pa, na, ba), (pb, nb, bb) = Sl['hand']
    pm = tuple((x + y) / 2 for x, y in zip(pa, pb))
    q = [(0.0, pa, na, ba), (0.125, (pm[0] - 0.02, pm[1] + 0.03, pm[2]), na, (ba[0] - 4, ba[1])), (0.25, pb, nb, bb), (0.375, (pm[0] + 0.02, pm[1] - 0.02, pm[2]), nb, (bb[0] + 3, bb[1]))]
    c.L = Path(free_path(q, 0.5, Sl['hint']))
    c.dL = FPath(lambda t: life(shape('L', 'open'), t, 0.5, amp=(2.5, 3.5, 0.0), digits=FINGERS))
    c.hint = Sl['hint']
    c.off = lambda t: 1.0
    return c


# ================================================================ draw, holster, throw
def swap_pose(p, pose, verts):
    """The least of a draw / holster pose that still has the whole gun under the bottom of the frame at the moment
    the game swaps the models (its own stow added: ndc stow 1), so no time is spent out of sight."""
    cls = p.info['cls']
    for k in [0.25 + 0.05 * i for i in range(30)]:
        W = p.wm(vmul(pose[0], k), vmul(pose[1], k))
        if max(ndc(W @ v, 1.0, cls)[0].y for v in verts) < -1.04:
            break
    return vmul(pose[0], k), vmul(pose[1], k)


def gun_points(p):
    """A few hundred points of the gun and its magazine (weapon space) for screen checks."""
    pts = []
    for name, off in (('WPN_' + p.wid, V((0, 0, 0))), ('WPN_%s_Mag' % p.wid, p.magS)):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            vs = ob.data.vertices
            pts += [vs[i].co + off for i in range(0, len(vs), max(1, len(vs) // 300))]
    return pts


def draw_clip(p):
    """0.3 s (the game scales it to its draw time): up from just under the frame on a rising arc with a roll, a
    little past the hold, a small counter-swing and rest. The support hand comes in from the side and takes its
    hold as the gun arrives; the fingers close after the palm lands; the finger finds the trigger last."""
    Dr = p.H['draw']
    c = Clip(p, 0.3)
    f = c.f
    frm = swap_pose(p, Dr['from'], gun_points(p))
    c.w(0.0, frm[0], frm[1], 'h').w(f(0.32), vmul(frm[0], 0.42), vadd(vmul(frm[1], 0.36), (0, -6, 0))).w(f(0.62), *Dr['over']).w(f(0.82), *Dr['settle']).w(c.dur, mode='h')
    c.off = scalar([(0.0, 1.0, 'h'), (f(0.70), 1.0, 'h'), (f(0.95), 0.0, 'h')])
    if p.GL is not None:
        away = lambda t: c.W(t) @ T((-0.07, -0.03, -0.06)) @ p.GL @ mat_trs((0, 0, 0), (0, 0, -18))
        c.L.to(0.0, away, f(0.25)).back(f(0.66), ease='out', arc=(-0.01, 0.0, 0.015))
        c.dL.to(0.0, shape('L', 'relaxed'), f(0.45)).back(f(0.80), stagger=0.008)
    return c


def holster_clip(p):
    """0.2 s: a small lift (weight), then down and out under the frame with a roll; the support hand lets go first
    and falls away ahead of the gun."""
    Ho = p.H['holster']
    c = Clip(p, 0.2)
    f = c.f
    to = swap_pose(p, Ho['to'], gun_points(p))
    c.w(0.0, mode='h').w(f(0.22), (0.0, 0.002, 0.005), (2.5, -2, 1)).w(f(0.55), vmul(to[0], 0.38), vadd(vmul(to[1], 0.42), (0, 5, 0))).w(c.dur, to[0], to[1], 'h')
    c.off = scalar([(0.0, 0.0, 'h'), (f(0.3), 1.0, 'h')])
    if p.GL is not None:
        away = lambda t: c.W(t) @ T((-0.08, -0.03, -0.08)) @ p.GL @ mat_trs((0, 0, 0), (0, 0, -20))
        c.L.leave(f(0.12)).to(f(0.62), away, 1.0, ease='in')
        c.dL.leave(f(0.05)).to(f(0.40), shape('L', 'relaxed'), 1.0, stagger=-0.006)
    return c


# grenade throw (every gun): the gun dips right, the support hand fetches the can from low, winds back by the left
# shoulder, throws forward (release at THROW_RELEASE: the game spawns the grenade then), follows through, comes back
THROW_LEN, THROW_RELEASE = 0.62, 0.52
THROW_L = [(0.19, (-0.16, -0.10, -0.32), (-30, 0, 0)), (0.36, (-0.43, -0.20, 0.03), (55, 0, -32)),
           (0.52, (-0.19, 0.15, 0.16), (-12, 0, -10)), (0.68, (-0.09, 0.13, -0.14), (-62, 0, 12))]
THROW_DIP = ((0.03, -0.03, -0.09), (-22, 12, -14))


def throw_clip(p):
    """The gun dips right and twists away; the support hand drops to the belt for the can, winds up past the
    shoulder (the gun counter-turns), whips forward (release at 52 %, fingers flying open), follows through down
    across the body and comes back to its hold while the gun returns past rest and settles."""
    c = Clip(p, THROW_LEN)
    f = c.f
    dl, dr = THROW_DIP
    c.w(0.0, mode='h').w(f(0.05), (0.0, 0.002, 0.003), (1.5, -2, 1)).w(f(0.20), vmul(dl, 0.8), vmul(dr, 0.8)).w(f(0.36), vadd(dl, (0.006, -0.004, 0.0)), vadd(dr, (0, 4, -6)))
    c.w(f(0.50), vadd(dl, (-0.008, 0.006, 0.004)), vadd(dr, (2, -5, 8))).w(f(0.66), dl, dr).w(f(0.88), (0.0, 0.002, 0.002), (-1.0, 0.0, 0.5)).w(f(0.95), (0.0, -0.001, -0.001), (0.3, 0, -0.2)).w(c.dur, mode='h')
    can, opn = held_fit('can'), shape('L', 'open')
    st = [mat_trs(loc, rot) for _, loc, rot in THROW_L]
    c.L.leave(f(0.04)).to(f(0.19), st[0], f(0.02), arc=(-0.04, -0.02, 0.0)).to(f(0.36), st[1], f(0.02), ease='out', arc=(-0.06, -0.04, 0.02))
    c.L.to(f(0.52), st[2], 0.0, ease='in', arc=(0.0, 0.0, 0.07)).to(f(0.68), st[3], 0.0, ease='out', arc=(0.02, 0.03, 0.0)).back(f(0.93), arc=(-0.03, 0.0, -0.03))
    c.dL.leave(f(0.03)).to(f(0.14), dmix(can, opn, 0.6)).to(f(0.20), can, f(0.30), stagger=0.004).to(f(0.545), opn, f(0.10), ease='out', stagger=-0.004).to(f(0.80), shape('L', 'relaxed')).back(f(0.96))
    c.off = scalar([(0.0, 0.0, 'h'), (f(0.08), 1.0, 'h'), (f(0.85), 1.0, 'h'), (f(0.94), 0.0, 'h')])
    return c


# ================================================================ melee
# A swing is a list of keys (fraction of the swing, hand loc (rig m), rotation[, second stick deg]). It starts and
# ends out of view (low right / low left): the game hides the gun, plays the whole swing, then draws the gun again.
# The hit lands at the weapon's 'hit' fraction (src/data/weapons.js). The keys are the poses the swing passes THROUGH:
# the bake runs a spline through the places and turns, so the blade travels an arc; each table has its wind-up
# (a pull back against the cut), the cut through the hit and a follow-through that carries on out of frame.
def bdir(theta, fwd=0.55, ccw=True):
    """Blade pointing at screen angle theta (deg, 0 = right, 90 = up), tipped forward by fwd; the edge leads the swing
    (ccw: the blade turns counter-clockwise on screen). Returns the rotation (weapon +Z = blade, +Y = edge)."""
    t = math.radians(theta)
    d = V((math.cos(t), fwd, math.sin(t))).normalized()
    e = V((-math.sin(t), 0.0, math.cos(t))) * (1 if ccw else -1)
    return frame(d, e)


def frame(d, e):
    z = V(d).normalized()
    y = (V(e) - z * V(e).dot(z)).normalized()
    x = y.cross(z)
    return Matrix((x, y, z)).transposed()


DIAG = [(0.00, (0.17, -0.20, -0.36), bdir(84)), (0.13, (0.15, -0.15, -0.02), bdir(70)), (0.26, (0.13, -0.13, 0.13), bdir(48, 0.35)),
        (0.36, (0.06, 0.00, 0.10), bdir(88)), (0.44, (-0.06, 0.09, 0.01), bdir(148)), (0.60, (-0.24, 0.04, -0.15), bdir(198)), (1.00, (-0.30, -0.16, -0.44), bdir(226))]
BACK = [(0.00, (-0.28, -0.18, -0.38), bdir(232, ccw=False)), (0.14, (-0.27, -0.10, -0.20), bdir(222, ccw=False)), (0.27, (-0.27, -0.07, -0.13), bdir(226, 0.4, ccw=False)),
        (0.37, (-0.14, 0.05, -0.04), bdir(170, ccw=False)), (0.46, (0.01, 0.10, 0.03), bdir(112, ccw=False)), (0.62, (0.16, 0.05, 0.10), bdir(44, ccw=False)),
        (1.00, (0.22, -0.16, -0.36), bdir(18, ccw=False))]
CHOP = [(0.00, (0.04, -0.18, -0.36), frame((0, 0.3, 1), (0, 1, 0))), (0.16, (0.00, -0.13, 0.02), frame((0.06, -0.1, 1), (0, 1, 0.1))),
        (0.30, (-0.04, -0.12, 0.19), frame((0.1, -0.5, 1), (0, 1, 0.5))), (0.40, (-0.06, 0.04, 0.14), frame((0.0, 0.3, 1), (0, 1, -0.3))),
        (0.50, (-0.07, 0.14, 0.00), frame((-0.05, 0.8, 0.5), (0, 0.5, -0.8))), (0.64, (-0.07, 0.12, -0.19), frame((-0.05, 0.6, -0.8), (0, -0.8, -0.6))),
        (1.00, (-0.05, -0.12, -0.44), frame((0, 0.3, -1), (0, -1, 0)))]
STAB = [(0.00, (0.12, -0.18, -0.34), frame((-0.2, 0.6, 0.7), (0, 0, 1))), (0.18, (0.10, -0.15, -0.10), frame((-0.3, 0.7, 0.6), (0, -0.2, 1))),
        (0.32, (0.09, -0.17, -0.04), frame((-0.38, 0.78, 0.48), (0, -0.3, 1))), (0.46, (-0.07, 0.21, 0.02), frame((-0.45, 0.8, 0.35), (0, -0.2, 1))),
        (0.58, (-0.06, 0.15, 0.00), frame((-0.45, 0.8, 0.32), (0, -0.2, 1))), (0.72, (-0.02, 0.02, -0.08), frame((-0.38, 0.75, 0.45), (0, -0.2, 1))),
        (1.00, (0.08, -0.16, -0.36), frame((-0.2, 0.6, 0.7), (0, 0, 1)))]
WHIRL = [(0.00, (0.12, -0.16, -0.32), bdir(80), (0, 0, 0)), (0.20, (0.11, -0.11, 0.08), bdir(62), (-70, 0, 0)), (0.30, (0.07, -0.02, 0.08), bdir(84), (-130, 0, 0)),
         (0.42, (-0.04, 0.10, 0.02), bdir(140), (-200, 0, 0)), (0.60, (-0.22, 0.05, -0.12), bdir(195), (-295, 0, 0)),
         (1.00, (-0.28, -0.14, -0.40), bdir(225), (-380, 0, 0))]
WHIRL2 = [(0.00, (-0.26, -0.16, -0.34), bdir(230, ccw=False), (0, 0, 0)), (0.22, (-0.23, -0.05, -0.10), bdir(208, ccw=False), (70, 0, 0)),
          (0.32, (-0.14, 0.04, -0.04), bdir(170, ccw=False), (130, 0, 0)), (0.44, (0.00, 0.10, 0.02), bdir(115, ccw=False), (200, 0, 0)),
          (0.62, (0.16, 0.05, 0.08), bdir(45, ccw=False), (295, 0, 0)), (1.00, (0.20, -0.14, -0.36), bdir(20, ccw=False), (380, 0, 0))]
MELEE_SWINGS = {
    'KATANA': {'Strike': (0.46, DIAG), 'Strike2': (0.46, BACK), 'Strike3': (0.50, CHOP)},
    'EAXE': {'Strike': (0.75, DIAG), 'Strike2': (0.75, CHOP)},
    'DAGGER': {'Strike': (0.32, STAB), 'Strike2': (0.34, DIAG)},
    'NUNCHUCKS': {'Strike': (0.30, WHIRL), 'Strike2': (0.30, WHIRL2)},
}
MELEE_READY = ((0.10, -0.06, -0.10), bdir(72, 0.35))      # live melee idle: the weapon held up at the right, ready


class MeleeClip(Clip):
    """A swing: the weapon's place and turn run on a spline through the keys (turns as quaternions on one arc)."""

    def __init__(self, p, dur, keys, loop=False):
        Clip.__init__(self, p, dur, loop)
        qs, last = [], None
        for k in keys:
            q = k[2].to_quaternion()
            if last is not None and last.dot(q) < 0:
                q = -q
            last = q
            qs.append(q)
        per = dur if loop else None
        self.kp = Track([(k[0] * dur, k[1]) for k in keys], per)
        self.kq = Track([(k[0] * dur, tuple(q)) for k, q in zip(keys, qs)], per)
        self.ks = Track([(k[0] * dur, k[3]) for k in keys], per) if len(keys[0]) > 3 else None
        if self.ks is not None:
            self.M = lambda t: p.mag_at(self.W(t), mat_trs((0, 0, 0), self.ks(t)))
        self.wrist = 84.0                # a cut carries the blade across the forearm: the wrist gives more than on a gun

    def W(self, t):
        q = Quaternion(self.kq(t))
        q.normalize()
        return T(self.p.carry) @ T(self.kp(t)) @ q.to_matrix().to_4x4()


def melee_actions(p, action):
    wid = p.wid
    for name, (dur, keys) in MELEE_SWINGS[wid].items():
        c = MeleeClip(p, dur, keys)
        hit = max(0.2, min(0.7, 0.44))
        squeeze = {dn: (5, 7, 5, 0) for dn in FINGERS}
        g = scalar([(0.0, 0.0, 'h'), (dur * (hit - 0.12), 0.3), (dur * hit, 1.0), (dur * (hit + 0.2), 0.3), (dur, 0.0, 'h')])
        baseR = p.digR
        c.dR = FPath(lambda t, g=g, baseR=baseR: dadd(baseR, {dn: vmul(squeeze[dn], g(t)) for dn in FINGERS}))
        if p.GL is not None:
            baseL = p.digL
            c.dL = FPath(lambda t, g=g, baseL=baseL: dadd(baseL, {dn: vmul(squeeze[dn], g(t)) for dn in FINGERS}))
        action(wid + '_' + name, c.frames(max(6, round(dur * FPS))))
    # live idle: held ready at the right, breathing, the grip working
    loc, rot = MELEE_READY
    keys = [(0.0, loc, rot), (0.25, vadd(loc, (0.002, 0.0, 0.004)), rot @ mat_trs((0, 0, 0), (1.5, 0, -1)).to_3x3()),
            (0.5, vadd(loc, (0.0, 0.001, 0.001)), rot @ mat_trs((0, 0, 0), (0, 1.5, 0.5)).to_3x3()), (0.75, vadd(loc, (-0.002, 0.0, 0.003)), rot @ mat_trs((0, 0, 0), (-1.2, 0, 1)).to_3x3())]
    if len(MELEE_SWINGS[wid]['Strike'][1][0]) > 3:
        keys = [k + ((8 * math.sin(2 * math.pi * k[0]), 0, 6 * math.cos(2 * math.pi * k[0])),) for k in keys]
    c = MeleeClip(p, 2.0, keys, loop=True)
    baseR = p.digR
    c.dR = FPath(lambda t: life(baseR, t, 2.0, amp=(0.8, 1.4, 0.0), digits=FINGERS))
    action(wid + '_Idle', c.frames(60))


# ================================================================ build
def build_actions(rig):
    bpy.context.view_layer.objects.active = rig
    rig.animation_data_create()
    bpy.context.scene.render.fps = FPS
    pb = rig.pose.bones
    for p in pb:
        p.rotation_mode = 'QUATERNION'
    last = {}

    def action(name, keys):
        global REPORT
        if hasattr(keys, 'frames'):
            keys = keys.frames()
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        rig.animation_data.action = act
        last.clear()
        if os.environ.get('IB_POSE_REPORT'):
            REPORT = {}
        for f, P in keys:
            for bn, Bm in solve(rig, P).items():
                loc, q, _ = Bm.decompose()
                if bn in last and last[bn].dot(q) < 0:
                    q = -q
                last[bn] = q
                pb[bn].location = loc
                pb[bn].rotation_quaternion = q
                pb[bn].keyframe_insert('location', frame=f)
                pb[bn].keyframe_insert('rotation_quaternion', frame=f)
        if REPORT is not None:
            print('POSE %-20s wrist R %3.0f..%3.0f  L %3.0f..%3.0f' % (name, min(REPORT['R']), max(REPORT['R']), min(REPORT['L']), max(REPORT['L'])))
            REPORT = None
        return act

    only = os.environ.get('IB_ONLY', '').split(',') if os.environ.get('IB_ONLY') else None
    for wid in WEAPONS:      # every built weapon, in build order (fam_weapons.GUNS)
        if only and wid not in only and wid != 'PIP':
            continue
        p = Poser(wid)
        if WEAPONS[wid]['cls'] == 'melee':
            melee_actions(p, action)
            continue
        a = p.a
        action(wid + '_Throw', throw_clip(p))
        action(wid + '_Idle', idle_clip(p))
        action(wid + '_Draw', draw_clip(p))
        action(wid + '_Holster', holster_clip(p))
        # Fire: one cycle (shot, recoil, forward ride, rest); bolt guns cycle the bolt, the pump gun racks
        n = max(2, round(a['fire'] * FPS))
        if a['style'] == 'bolt':
            action(wid + '_Fire', bolt_cycle(p, n))
        elif a['style'] == 'shell':
            action(wid + '_Fire', pump_fire(p, n))
        elif a['style'] == 'revolver':
            action(wid + '_Fire', revolver_fire(p, n))
        elif p.info['cls'] == 'rocket':
            action(wid + '_Fire', launcher_fire(p, n))
        else:
            action(wid + '_Fire', fire_clip(p, n))
        # Reload (length = reload time)
        r = round(a['reload'] * FPS)
        if a['style'] == 'revolver':
            action(wid + '_Reload', revolver_reload(p, r))
        elif a['style'] == 'shell':
            action(wid + '_Reload', shell_reload(p, r))
        elif a.get('chg') == 'lmg':
            action(wid + '_Reload', lmg_reload(p, r))
        else:
            action(wid + '_Reload', mag_reload(p, r))
        action(wid + '_Sprint', sprint_clip(p))
        action(wid + '_Slide', slide_clip(p))
    rig.animation_data.action = bpy.data.actions['PIP_Idle']
    for act in bpy.data.actions:
        act.use_fake_user = True
