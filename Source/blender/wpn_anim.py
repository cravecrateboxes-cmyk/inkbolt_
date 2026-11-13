"""INKBOLT weapons: arm actions (per-weapon clips from the HANDLING tables, reloads, melee swings, throws).
Built by fam_weapons.py; shape kit and gun parts in wpn_core.py."""
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


# ================================================================ actions


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
    """Hand frame (rig space, as Poser's FL / FR) for a hand with its wrist at `wrist`, the palm facing `palm`
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


def ndc(p):
    """Rig point -> the game's viewmodel screen (NDC x, y; desktop 16:9) and depth (m)."""
    q = V((p.x, p.z, -p.y)) * VM_S
    c, sn = math.cos(VM_YAW), math.sin(VM_YAW)
    q = V((c * q.x + sn * q.z, q.y, -sn * q.x + c * q.z)) + VM_POS
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
        s, e = two_bone(SH[side], wr, P.get('hint', {}).get(side, HINT[side]), pref=MH.to_3x3() @ hand_axes(side)[0])
        M['UPPERARM_' + side] = seg_delta(RIG['S0'][side], RIG['E0'][side], s, e)
        M['FOREARM_' + side] = forearm_delta(side, MH, e, wr)
        if REPORT is not None:
            REPORT.setdefault(side, []).append(wrist_bend(side, MH, e, wr))
        dig = P.get('dig', {}).get(side, {})
        for dn in DIGITS:                  # each joint is a hinge about the digit's flexion axis; the knuckle also spreads
            J, (ax, sp) = RIG['J'][side][dn], RIG['AX'][side][dn]
            a = dig.get(dn, (0.0, 0.0, 0.0, 0.0))
            Mp = MH
            for i in range(3):
                C = Matrix.Rotation(D(a[i]), 4, ax)
                if i == 0 and len(a) > 3 and a[3]:
                    C = C @ Matrix.Rotation(D(a[3]), 4, sp)
                Mp = M['%s%d_%s' % (dn, i + 1, side)] = Mp @ T(J[i]) @ C @ T(-J[i])
    out = {}
    for b in rig.data.bones:
        Rc = b.matrix_local
        Mp = M[b.parent.name] if b.parent else Matrix.Identity(4)
        out[b.name] = Rc.inverted() @ Mp.inverted() @ M[b.name] @ Rc
    return out


class Poser:
    """Builds pose dicts for one weapon: W = carry @ offset @ rotation about the grip."""

    def __init__(self, wid):
        self.wid, self.info, self.a = wid, WEAPONS[wid], ANIM.get(wid, {})
        self.H = handling(wid)
        self.carry = V(self.H['carry'])
        self.GR = mat_trs((0, 0, 0), (-self.info['rake'], 0, 0))
        self.GL = left_hold(wid)
        self.cl0 = self.info.get('curl_L', 0.0)
        self.magS = V(self.info['mag'])
        self.magT = self.magS - RIG['mag0']

    spin = 0.0     # melee: turn about the handle (deg) so the flat of the blade faces the camera and the edge leads

    def wm(self, wl=(0, 0, 0), wr=(0, 0, 0)):
        R = wr.to_4x4() if isinstance(wr, Matrix) else mat_trs((0, 0, 0), wr)     # melee keys give the rotation itself
        return T(self.carry) @ T(wl) @ R @ mat_trs((0, 0, 0), (0, 0, self.spin))

    def __call__(self, wl=(0, 0, 0), wr=(0, 0, 0), trig=0.0, FL=None, FR=None, mag=None, curlL=0.0, curlR=0.0, idx=0.0, thumbL=0.0, thumbR=0.0,
                 lift=0.0, hintL=None):
        W = self.wm(wl, wr)
        if FL is None and self.GL is None:                   # one-handed melee: support fist up in a guard, low left
            FL, curlL, thumbL = MELEE_GUARD, curlL + 30, thumbL - 15
        if FL is None and self.info['cls'] == 'pistol':      # two-hand pistol hold
            thumbL, curlL = thumbL + PISTOL_LEFT[6], curlL + PISTOL_LEFT[7]
        elif FL is None:                                     # foregrip / handguard: close on the part
            thumbL, curlL = thumbL + self.cl0, curlL + self.cl0
        if self.offk and FR is None:          # trigger finger straight along the frame (sprint, slide, reload, draw)
            idx += self.offk * self.H['sprint']['idx']
            lift += self.offk * self.H['sprint']['lift']
        dig = {'R': {'INDEX': (14 * trig + idx, 0.0, 0.0, lift), 'THUMB': (thumbR, 0.0, 0.0, 0.0)},
               'L': {'INDEX': (curlL, 0.0, 0.0, 0.0), 'THUMB': (thumbL, 0.0, 0.0, 0.0)}}
        for fn in ('MIDDLE', 'RING', 'PINKY'):
            dig['R'][fn] = (curlR, 0.0, 0.0, 0.0)
            dig['L'][fn] = (curlL, 0.0, 0.0, 0.0)
        return {'W': W, 'FR': FR if FR is not None else W @ self.GR, 'FL': FL if FL is not None else W @ self.GL,
                'mag': mag if mag is not None else W @ T(self.magT), 'dig': dig,
                'hint': {'L': V(hintL)} if hintL is not None else {}}

    offk = 0.0

    def off(self, k=1.0):
        """Following poses keep the trigger finger off the trigger (k = 1) or on it (k = 0)."""
        self.offk = k
        return self

    def mag_at(self, W, extra=Matrix.Identity(4)):
        """Mag bone delta for the magazine placed at its socket of weapon pose W (extra: motion in mag space)."""
        return W @ T(self.magS) @ extra @ T(-RIG['mag0'])


# ---------------------------------------------------------------- melee swings and grenade throws (round 3)
# A swing is a list of keys (fraction of the swing, weapon loc m, weapon rot deg (pitch, roll, yaw) as in HANDLING,
# extras). The swing starts and ends out of view (low right / low left): the game hides the gun, plays the whole swing,
# then draws the gun again. The hit lands at the weapon's 'hit' fraction (src/data/weapons.js windup / length).
# Nunchucks: 'swing' turns the second stick about the chain end (deg, weapon space).
MELEE_GUARD = mat_trs((-0.30, -0.06, -0.22), (-20, 0, -30))       # free support fist, rig space (one-handed weapons)


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


# The sword arcs read like a clock hand sweeping across the screen (the swing plane faces the camera, tipped forward):
# DIAG cuts from up-right down to the left (counter-clockwise), BACK rises from low left to up right (clockwise),
# CHOP comes straight down, STAB thrusts forward and in. Keys: (fraction, hand loc (rig m), rotation[, second stick deg]).
DIAG = [(0.00, (0.16, -0.20, -0.36), bdir(80)), (0.20, (0.10, -0.12, 0.10), bdir(55)), (0.42, (-0.04, 0.08, 0.02), bdir(140)),
        (0.60, (-0.24, 0.04, -0.14), bdir(195)), (1.00, (-0.30, -0.16, -0.44), bdir(225))]
BACK = [(0.00, (-0.28, -0.18, -0.38), bdir(230, ccw=False)), (0.22, (-0.24, -0.04, -0.14), bdir(205, ccw=False)),
        (0.45, (0.00, 0.10, 0.02), bdir(115, ccw=False)), (0.62, (0.16, 0.05, 0.10), bdir(45, ccw=False)),
        (1.00, (0.22, -0.16, -0.36), bdir(20, ccw=False))]
CHOP = [(0.00, (0.04, -0.18, -0.36), frame((0, 0.3, 1), (0, 1, 0))), (0.24, (-0.04, -0.10, 0.16), frame((0.1, -0.35, 1), (0, 1, 0.3))),
        (0.46, (-0.07, 0.14, 0.02), frame((-0.05, 0.75, 0.6), (0, 0.6, -0.8))), (0.62, (-0.07, 0.12, -0.18), frame((-0.05, 0.6, -0.8), (0, -0.8, -0.6))),
        (1.00, (-0.05, -0.12, -0.44), frame((0, 0.3, -1), (0, -1, 0)))]
STAB = [(0.00, (0.12, -0.18, -0.34), frame((-0.2, 0.6, 0.7), (0, 0, 1))), (0.28, (0.07, -0.12, -0.06), frame((-0.35, 0.75, 0.5), (0, -0.3, 1))),
        (0.46, (-0.07, 0.20, 0.02), frame((-0.45, 0.8, 0.35), (0, -0.2, 1))), (0.64, (-0.05, 0.12, -0.02), frame((-0.45, 0.8, 0.3), (0, -0.2, 1))),
        (1.00, (0.08, -0.16, -0.36), frame((-0.2, 0.6, 0.7), (0, 0, 1)))]
WHIRL = [(0.00, (0.12, -0.16, -0.32), bdir(80), (0, 0, 0)), (0.20, (0.10, -0.10, 0.08), bdir(60), (-90, 0, 0)),
         (0.42, (-0.04, 0.10, 0.02), bdir(140), (-190, 0, 0)), (0.60, (-0.22, 0.05, -0.12), bdir(195), (-290, 0, 0)),
         (1.00, (-0.28, -0.14, -0.40), bdir(225), (-360, 0, 0))]
WHIRL2 = [(0.00, (-0.26, -0.16, -0.34), bdir(230, ccw=False), (0, 0, 0)), (0.22, (-0.22, -0.04, -0.10), bdir(205, ccw=False), (90, 0, 0)),
          (0.44, (0.00, 0.10, 0.02), bdir(115, ccw=False), (190, 0, 0)), (0.62, (0.16, 0.05, 0.08), bdir(45, ccw=False), (290, 0, 0)),
          (1.00, (0.20, -0.14, -0.36), bdir(20, ccw=False), (360, 0, 0))]
# the rotation already carries the edge direction, so no extra spin about the handle
SPIN = {}
MELEE_SWINGS = {
    'KATANA': {'Strike': (0.46, DIAG), 'Strike2': (0.46, BACK), 'Strike3': (0.50, CHOP)},
    'EAXE': {'Strike': (0.75, DIAG), 'Strike2': (0.75, CHOP)},
    'DAGGER': {'Strike': (0.32, STAB), 'Strike2': (0.34, DIAG)},
    'NUNCHUCKS': {'Strike': (0.30, WHIRL), 'Strike2': (0.30, WHIRL2)},
}
# grenade throw (every gun): the gun dips right, the support hand fetches the can from low, winds back by the left
# shoulder, throws forward (release at THROW_RELEASE: the game spawns the grenade then), follows through, comes back
THROW_LEN, THROW_RELEASE = 0.62, 0.52
THROW_L = [(0.20, (-0.16, -0.10, -0.32), (-30, 0, 0)), (0.36, (-0.42, -0.18, 0.02), (50, 0, -30)),
           (0.52, (-0.20, 0.14, 0.15), (-10, 0, -10)), (0.70, (-0.10, 0.10, -0.15), (-60, 0, 10))]
THROW_DIP = ((0.03, -0.03, -0.09), (-22, 12, -14))


def melee_actions(p, action):
    wid = p.wid
    for name, (dur, keys) in MELEE_SWINGS[wid].items():
        n = max(6, round(dur * FPS))
        p.spin = SPIN.get(id(keys), 0.0)
        frames = []
        for key in keys:
            f, wl, wr = key[0], key[1], key[2]
            kw = {'curlR': 10}
            if len(key) > 3:
                kw['mag'] = p.mag_at(p.wm(wl, wr), mat_trs((0, 0, 0), key[3]))
            frames.append((round(f * n), p(wl, wr, **kw)))
        action(wid + '_' + name, frames)
    rest = DIAG[-1]
    action(wid + '_Idle', [(0, p(rest[1], rest[2], curlR=10)), (30, p(rest[1], rest[2], curlR=10))])
    p.spin = 0.0


def throw_action(p, action):
    n = round(THROW_LEN * FPS)
    dl, dr = THROW_DIP
    keys = [(0, p())]
    p.off()
    for f, loc, rot in THROW_L:
        keys.append((round(f * n), p(dl, dr, FL=mat_trs(loc, rot), curlL=12, thumbL=-6)))
    p.off(0)
    keys.append((round(0.88 * n), p((0.0, 0.002, 0.002), (-1.0, 0.0, 0.5))))
    keys.append((n, p()))
    action(p.wid + '_Throw', keys)


def pump_fire(p, n, kick):
    """Shot, then the support hand racks the pump (forend = the Mag part) back and forward."""
    back = T((0, -0.070, 0))
    W = p.wm()
    Wk = p.wm(*kick)
    f = lambda t: max(1, round(n * t))
    return [(0, p(trig=1)), (1, p(*kick, trig=1)), (f(0.25), p()),
            (f(0.45), p(FL=W @ back @ p.GL, mag=p.mag_at(W, back))), (f(0.62), p(FL=W @ back @ p.GL, mag=p.mag_at(W, back))),
            (f(0.80), p()), (n, p())]


def shell_reload(p, r):
    """One shell: tilt the gun, the support hand drops to the belt, brings a shell (HOLD_L socket, shown by the game)
    up to the loading port and thumbs it in, back to the forend."""
    fr = lambda t: round(r * t)
    tl, tr = (-0.010, -0.010, 0.040), (12, 34, -14)
    W = p.wm(tl, tr)
    port = W @ T(V(p.info['port']) + V((0.0, 0.0, -0.035))) @ mat_trs((0, 0, 0), (0, 180, 0))
    low = T((-0.16, -0.06, -0.40)) @ mat_trs((0, 0, 0), (-40, 0, 0))
    return [(0, p(tl, tr)), (fr(0.25), p(tl, tr, FL=low)), (fr(0.55), p(tl, tr, FL=port @ T((0, 0, -0.03)))),
            (fr(0.72), p(tl, tr, FL=port)), (r, p(tl, tr))]


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
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        rig.animation_data.action = act
        last.clear()
        if os.environ.get('IB_POSE_REPORT'):
            REPORT = {}
            wid = name.rsplit('_', 1)[0]
            mz = V(WEAPONS[wid]['muzzle'])
            scr = []
            for f, P in keys:
                (a, _), (b, _) = ndc(P['W'] @ (mz - V((0, 0.1, 0)))), ndc(P['W'] @ mz)
                h = {sd: ndc(P['F' + sd].translation)[0] for sd in ('R', 'L')}
                scr.append('%d:%+.0f%s' % (f, math.degrees(math.atan2(b.x - a.x, b.y - a.y)),
                                           ''.join(' %s(%+.2f,%+.2f)' % (sd, h[sd].x, h[sd].y) for sd in 'RL') if '_S' in name or '_Th' in name else ''))
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
            print('POSE %-20s wrist R %3.0f..%3.0f  L %3.0f..%3.0f  barrel %s' % (
                name, min(REPORT['R']), max(REPORT['R']), min(REPORT['L']), max(REPORT['L']), ' '.join(scr)))
            REPORT = None
        return act

    for wid in WEAPONS:      # every built weapon, in build order (fam_weapons.GUNS)
        p = Poser(wid)
        if WEAPONS[wid]['cls'] == 'melee':
            melee_actions(p, action)
            continue
        info, a, H = p.info, p.a, p.H
        heavy = a.get('heavy', 0.0)
        throw_action(p, action)
        p.off(0)
        # Idle: 2 s breathing loop, rest -> a -> rest -> b -> rest (a slow figure-8 under the game's own sway)
        ia, ib = H['idle']
        action(wid + '_Idle', [(0, p()), (15, p(*ia)), (30, p()), (45, p(*ib)), (60, p())])
        # Draw 0.3 s: swing up from low, overshoot, small counter-swing, settle; finger finds the trigger last
        Dr = H['draw']
        action(wid + '_Draw', [(0, p.off()(*Dr['from'])), (5, p.off(0.5)(*Dr['over'])), (7, p.off(0)(*Dr['settle'])), (9, p())])
        # Holster 0.2 s: a small dip (weight), then down and away
        Ho = H['holster']
        action(wid + '_Holster', [(0, p()), (2, p.off()(*Ho['dip'])), (6, p(*Ho['to']))])
        p.off(0)
        # Fire: one cycle (shot, recoil, forward overshoot, rest); bursts kick once per round; bolt guns cycle the bolt
        n = max(2, round(a['fire'] * FPS))
        K = H['kick']
        kick = (tuple(c * (1 + 0.8 * heavy) for c in K['loc']), tuple(c * (1 + 0.9 * heavy) for c in K['rot']))
        rec = (tuple(c * (1 + 0.5 * heavy) for c in K['recover'][0]), tuple(c * (1 + 0.5 * heavy) for c in K['recover'][1]))
        if a.get('burst'):
            g = max(1, round(a['gap'] * FPS))
            keys = []
            for i in range(a['burst']):
                keys += [(i * g, p(trig=1)), (i * g + 1, p(*kick, trig=1))]
            if n - (a['burst'] - 1) * g - 1 >= 4:
                keys.append(((a['burst'] - 1) * g + 1 + (n - (a['burst'] - 1) * g - 1) // 2, p(*rec)))
            keys.append((n, p()))
            action(wid + '_Fire', keys)
        elif a['style'] == 'bolt':
            action(wid + '_Fire', bolt_cycle(p, n, kick))
        elif a['style'] == 'shell':
            action(wid + '_Fire', pump_fire(p, n, kick))
        elif a['style'] == 'revolver':
            action(wid + '_Fire', revolver_fire(p, n, kick))
        else:
            keys = [(0, p(trig=1)), (1, p(*kick, trig=1))]
            if n >= 4:
                keys.append((max(2, round(n * 0.5)), p(*rec)))
            keys.append((n, p()))
            action(wid + '_Fire', keys)
        # Reload (length = reload time)
        r = round(a['reload'] * FPS)
        if a['style'] == 'revolver':
            action(wid + '_Reload', revolver_reload(p, r))
        elif a['style'] == 'shell':
            action(wid + '_Reload', shell_reload(p, r))
        else:
            action(wid + '_Reload', mag_reload(p, r))
        p.off(0)
        # Sprint loop 0.6 s (two footfalls): pistols at high ready with the free arm pumping, long guns at low
        # ready across the chest; trigger finger straight along the frame
        S = H['sprint']
        p.off()
        if S['style'] == 'high':
            fa, fb = (free_hand('L', at_ndc(*q[0]), q[1], q[2]) for q in S['pump'])
            fist = dict(curlL=S['fist'], thumbL=-18)
            action(wid + '_Sprint', [(0, p(*S['a'], FL=fa, **fist)), (9, p(*S['b'], FL=fb, **fist)), (18, p(*S['a'], FL=fa, **fist))])
        else:
            action(wid + '_Sprint', [(0, p(*S['a'])), (9, p(*S['b'])), (18, p(*S['a']))])
        # Slide loop 0.5 s: the gun tucked low and canted in, the support arm out to the lower left for balance,
        # palm to the ground, fingers relaxed open; the free hand follows its forearm (free_hand: no snapped wrist)
        Sl = H['slide']
        h1, h2 = (free_hand('L', at_ndc(*q[0]), q[1], q[2], Sl['hint']) for q in Sl['hand'])
        o = dict(curlL=Sl['curl'], thumbL=Sl['thumb'], hintL=Sl['hint'])
        action(wid + '_Slide', [(0, p(*Sl['a'], FL=h1, **o)), (7, p(*Sl['b'], FL=h2, **o)), (15, p(*Sl['a'], FL=h1, **o))])
        p.off(0)
    rig.animation_data.action = bpy.data.actions['PIP_Idle']
    for act in bpy.data.actions:
        act.use_fake_user = True


def grab_frame(p):
    """Support glove wrapped round the magazine body (mag axis = glove grip axis), in mag-socket space."""
    info = p.info
    return mat_trs((0, 0, 0), (-info['mrake'], 0, 0)) @ T((0.0, 0.0, -0.006 if info['cls'] == 'pistol' else -0.040))


def mag_reload(p, r):
    """Tilt, mag drops out, support hand fetches a fresh one from below, seats it, slaps it, then works
    the slide / charging handle."""
    info, a, R = p.info, p.a, p.H['reload']
    fr = lambda t: round(r * t)
    tl, tr = R['tilt']
    tl1 = tuple(c * 1.08 for c in tl)
    tr1 = tuple(c * 1.08 for c in tr)
    W, W1 = p.wm(tl, tr), p.wm(tl1, tr1)
    G = grab_frame(p)
    at_mag = lambda Wm, d=0.0: Wm @ T(p.magS) @ T((0, 0, d)) @ G
    in_hand = lambda FL: FL @ G.inverted() @ T(-RIG['mag0'])
    low = T(V(R['low'])) @ mat_trs((0, 0, 0), (-25, 0, 0)) @ T(p.magS) @ G
    mid = T(V(R['low']) * 0.45 + V((-0.03, 0.02, 0.0))) @ mat_trs((0, 0, 0), (-12, 0, 6)) @ T(p.magS) @ G   # arc up from the pouch
    keys = [(0, p())]
    p.off()
    keys.append((fr(0.08), p(tl, tr)))                                                              # tilt: show the well
    keys.append((fr(0.17), p(tl1, tr1, FL=at_mag(W1, -0.05), mag=p.mag_at(W1, T((0, 0, -0.03))))))   # hand on the mag, pull
    keys.append((fr(0.26), p(tl, tr, FL=low, mag=p.mag_at(W, T((0, -0.02, -0.60)) @ mat_trs((0, 0, 0), (-30, -20, 0))))))
    keys.append((fr(0.36), p(tl1, tr1, FL=low, mag=in_hand(low))))                                    # fresh mag from the pouch
    keys.append((fr(0.45), p(tl1, tr1, FL=mid, mag=in_hand(mid))))
    F1 = at_mag(W, -0.085)
    keys.append((fr(0.53), p(tl, tr, FL=F1, mag=in_hand(F1))))                                        # lined up under the well
    Wd = p.wm(tuple(c + d for c, d in zip(tl, (0, 0, -0.004))), tr)                                    # weapon gives a little
    F2 = at_mag(Wd, -0.002)
    keys.append((fr(0.61), p(tuple(c + d for c, d in zip(tl, (0, 0, -0.004))), tr, FL=F2, mag=in_hand(F2))))
    sl_, sr_ = R['seat']
    keys.append((fr(0.67), p(sl_, sr_, FL=at_mag(p.wm(sl_, sr_), 0.006))))                              # palm slap: seats, bump up
    keys.append((fr(0.72), p(tl, tr)))
    if a['style'] == 'bolt':      # right hand works the bolt to chamber
        W0 = p.wm()
        for t, off, rot in ((0.76, (0, 0, 0), (0, 30, 0)), (0.81, (-0.010, 0, 0.020), (0, -20, 0)), (0.87, (-0.010, -0.065, 0.020), (0, -20, 0)),
                            (0.92, (-0.010, 0, 0.020), (0, -20, 0))):
            keys.append((fr(t), p(FR=knob_frame(p, W0, off, rot))))
        p.off(0)
        keys.append((r, p()))
        return keys
    # slide / charging handle: the support glove closes on the part from the left side and pulls it back
    ch, pull = a['charge']
    tl3, tr3 = (0.0, 0.0, -0.006), (6, -6, -10)
    Wc = p.wm(tl3, tr3)
    side = Wc @ T((min(ch[0], -0.020) - 0.026, ch[1] + 0.020, ch[2] - 0.004)) @ mat_trs((0, 0, 0), (-35, 0, -10))
    keys.append((fr(0.80), p(tl3, tr3, FL=side, curlL=6)))
    tl4, tr4 = (0.0, -0.004, -0.004), (5, -7, -10)                                                    # slide snaps home: a jolt
    keys.append((fr(0.88), p(tl4, tr4, FL=T(Wc.to_3x3() @ V(pull)) @ side, curlL=6)))
    p.off(0)
    keys.append((fr(0.95), p((0.0, 0.002, 0.002), (-1.0, 0.0, 0.5))))                                # small overshoot back to rest
    keys.append((r, p()))
    return keys


def revolver_fire(p, n, kick):
    """One shot: the trigger breaks, the muzzle kicks up a little, and the cylinder (the Mag part) turns one chamber,
    60 deg about the bore. The cylinder is six-fold symmetric, so the clip ends on the indexed cylinder and the rest
    poses (which the game crossfades to) show it unchanged. The whole clip is n frames (round(60/rpm * 30))."""
    idx = lambda Wm: p.mag_at(Wm, mat_trs((0, 0, 0), (0, 60, 0)))
    return [(0, p(trig=1)), (1, p(*kick, trig=1, mag=idx(p.wm(*kick)))), (n, p(mag=idx(p.wm())))]


def revolver_reload(p, r):
    """Cylinder swings out to the left on its crane (a turn about the vertical pin at the front of the frame), muzzle up
    to dump the cases, fresh rounds from the support hand, cylinder snaps shut."""
    info = p.info
    fr = lambda t: round(r * t)
    piv = V(info['pivot'])
    swing = lambda Wm, ang: Wm @ T(piv) @ mat_trs((0, 0, 0), (0, 0, -ang)) @ T(-piv) @ T(p.magT)
    side = lambda Wm: Wm @ T((-0.040, 0.030, 0.005)) @ mat_trs((0, 0, 0), (-90, 0, -90))
    keys = [(0, p())]
    p.off()
    t1 = ((0.0, 0.0, -0.01), (10, -30, -8))
    W1 = p.wm(*t1)
    keys.append((fr(0.12), p(*t1, FL=side(W1))))
    keys.append((fr(0.22), p(*t1, FL=side(W1), mag=swing(W1, 85))))
    t2 = ((0.0, -0.03, 0.03), (55, -20, -10))
    W2 = p.wm(*t2)
    keys.append((fr(0.34), p(*t2, FL=W2 @ T((-0.034, 0.075, 0.0)) @ mat_trs((0, 0, 0), (0, 0, -90)), mag=swing(W2, 85))))
    t3 = ((0.0, 0.0, -0.02), (-25, -25, -8))
    W3 = p.wm(*t3)
    low = T((-0.16, -0.10, -0.46)) @ mat_trs((0, 0, 0), (-40, 0, 0))
    keys.append((fr(0.46), p(*t3, FL=low, mag=swing(W3, 85))))
    keys.append((fr(0.62), p(*t3, FL=W3 @ T((-0.040, 0.075, 0.010)) @ mat_trs((0, 0, 0), (-90, 0, -90)), mag=swing(W3, 85))))
    keys.append((fr(0.74), p(*t1, FL=side(W1), mag=swing(W1, 0))))
    p.off(0)
    keys.append((fr(0.88), p((0.0, 0.002, 0.003), (-2.0, 1.0, 0.5))))     # cylinder snapped home: settle with a little swing
    keys.append((r, p()))
    return keys


def knob_frame(p, W, off, rot):
    """Right glove frame closing on the bolt knob (off: knob travel, rot: wrist roll)."""
    return W @ T(V(p.info['bolt']) + V(off)) @ mat_trs((0, 0, 0), rot) @ T((-0.030, -0.006, 0.010))


def bolt_cycle(p, n, kick):
    """Shot, then the right hand works the bolt (up, back, forward, down) and returns to the grip."""
    info = p.info
    W = p.wm()
    knob = lambda off, rot: knob_frame(p, W, off, rot)
    f = lambda t: round(n * t)
    keys = [(0, p(trig=1)), (2, p(*kick, trig=1)), (f(0.15), p())]
    keys.append((f(0.28), p(FR=knob((0, 0, 0), (0, 30, 0)))))
    keys.append((f(0.40), p(FR=knob((-0.010, 0, 0.020), (0, -20, 0)))))
    keys.append((f(0.55), p(FR=knob((-0.010, -0.065, 0.020), (0, -20, 0)))))
    keys.append((f(0.70), p(FR=knob((-0.010, 0, 0.020), (0, -20, 0)))))
    keys.append((f(0.80), p(FR=knob((0, 0, 0), (0, 30, 0)))))
    keys.append((n, p()))
    return keys
