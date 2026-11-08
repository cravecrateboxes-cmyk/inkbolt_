"""INKBOLT asset family: weapons (11 hitscan viewmodels, gloved arms rig + per-weapon actions, pickups).

Viewmodel space (Blender): +Y forward (barrel), +Z up, +X right; origin at the top of the grip where the
right hand's web sits. Every gun is built from a small kit of exact primitives (chamfered boxes, lofts,
lathes, swept tubes) so silhouettes get chamfers and real recesses (bores, lens wells) at a low triangle
cost. Small inner details (screws, slots, serrations, stripes) carry no outline shell: the ink shell is
kept for the parts that make the silhouette, so the budget goes into readable detail.
Z-fighting: ib_lib.check_zfight runs strict on every object, and gun + magazine are also checked together
(they overlap in the game). Details stand >= 3 mm proud of the surface they sit on.
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

V = Vector
D = math.radians

# ---------------------------------------------------------------- palette (lighter tones; HULL/ink untouched)
_LIFT = {'gunmetal': '#5A586D'}
ib_lib.PALETTES['weapons'] = [(n, _LIFT.get(n, h)) for n, h in BASE] + [
    ('gun2', '#48475A'),     # polymer frames, grips, mags
    ('gun3', '#6E6B85'),     # machined accents, handguards, panels
    ('steel', '#B7BDC9'),    # barrels, pins, bolts
    ('steel2', '#8C92A3'),   # darker steel
    ('brass', '#EDBE5C'),    # cartridges
    ('lens', '#86EAF2'),     # optics glass
    ('glove', '#7C7894'), ('glove2', '#938FAD'), ('glove3', '#625F78'),
    ('sleeve', '#8273C4'), ('sleeve2', '#9B8EDB'), ('sleeve3', '#6A5CAA'),
    ('chip', '#FFFFFF'), ('chip2', '#DCDCE6'), ('ammo', '#2F7BEA'), ('ammo2', '#1E559F'), ('ammo3', '#5C98F0'),
    ('health', '#5BCF4A'), ('health2', '#3E9C33'), ('health3', '#86E078'),
    ('glove4', '#4A465E'),   # moulded glove armour: knuckle / thumb pads, reinforced fingertips
    ('olive', '#7C8A3E'), ('olive2', '#5C672C'), ('olive3', '#A2B060'),   # rocket ammo crate
    # gun skins (src/game/gunskins.js recolours these per gun and rarity; keep the order: the runtime indexes cells)
    ('furn', '#4A4257'),     # furniture: pistol grips, stocks
    ('trim', '#FFB21E')]     # accent stripes / rings (glow lines on Epic and Legendary)

import os
DEBUG = {} if os.environ.get('IB_DEBUG') else None
HULL_T = 0.0035     # viewmodel outline shell (m): thin enough that 3 mm details stay crisp


# ================================================================ geometry kit
def ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return list(poly) if s > 0 else list(reversed(poly))


def inset2d(poly, d):
    """Offset a simple polygon inward by d (miter joins). Shrinks d until no edge flips (no inside-out caps)."""
    P = [V((p[0], p[1])) for p in ccw(poly)]
    n = len(P)
    for _ in range(8):
        out = []
        for i in range(n):
            p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % n]
            e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
            n1, n2 = V((-e1.y, e1.x)), V((-e2.y, e2.x))
            m = n1 + n2
            m = n1 if m.length < 1e-6 else m.normalized()
            out.append(p1 + m * (d / max(m.dot(n1), 0.35)))
        if all((out[(i + 1) % n] - out[i]).dot(P[(i + 1) % n] - P[i]) > 0 for i in range(n)):
            break
        d *= 0.6
    return [(p.x, p.y) for p in out]


def rrect(w, h, c=0.0, cx=0.0, cy=0.0, seg=1, ct=None, cb=None):
    """CCW rectangle with chamfered (seg=1) or rounded (seg>1) corners; ct/cb override top/bottom corners."""
    ct = c if ct is None else ct
    cb = c if cb is None else cb
    pts = []
    for (sx, sy, a0, cc) in ((1, -1, -90, cb), (1, 1, 0, ct), (-1, 1, 90, ct), (-1, -1, 180, cb)):
        if cc <= 0:
            pts.append((cx + sx * w / 2, cy + sy * h / 2))
            continue
        ox, oy = cx + sx * (w / 2 - cc), cy + sy * (h / 2 - cc)
        for k in range(seg + 1):
            a = D(a0 + 90.0 * k / seg)
            pts.append((ox + cc * math.cos(a), oy + cc * math.sin(a)))
    return pts


AXES = {'x': (V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))),
        'y': (V((0, 1, 0)), V((1, 0, 0)), V((0, 0, 1))),
        'z': (V((0, 0, 1)), V((1, 0, 0)), V((0, 1, 0)))}


class Kit:
    """Shape builder on top of ib_lib.Model: each call is one shape (one z-fight id), one palette colour
    (per-band overrides allowed), with or without the outline shell."""

    def __init__(self, pal):
        self.pal = pal
        self.m = Model(pal)
        self.bm = self.m.bm
        self.sl = self.m.shape
        self.nohull = set()
        self.tags = {}            # shape id -> free tag (arms: bone name)
        self.xf = Matrix.Identity(4)
        self.tag = None

    # ---- bookkeeping
    def _reg(self, before, color, hull, fcol=None):
        new = [f for f in self.bm.faces if f not in before]
        self.m.nshape += 1
        sid = self.m.nshape
        mi = self.pal.index(color)
        for f in new:
            f[self.sl] = sid
            f.material_index = self.pal.index(fcol[f]) if fcol and f in fcol else mi
        if not hull:
            self.nohull.add(sid)
        if self.tag:
            self.tags[sid] = self.tag
        if DEBUG is not None:
            import inspect
            DEBUG[(id(self), sid)] = '<'.join('%s:%d' % (fr.function, fr.lineno) for fr in inspect.stack()[2:6])
        return sid

    class _At:
        def __init__(self, kit, m):
            self.kit, self.m = kit, m

        def __enter__(self):
            self.old = self.kit.xf
            self.kit.xf = self.old @ self.m

        def __exit__(self, *a):
            self.kit.xf = self.old

    def at(self, loc=(0, 0, 0), rot=(0, 0, 0), m=None):
        return Kit._At(self, m if m is not None else mat_trs(loc, rot))

    # ---- primitives
    def loft(self, rings, color, hull=True, caps=(True, True), closed=False, bands=None, capcol=(None, None)):
        """Rings of points (a ring of one point is an apex) joined by quads; optional n-gon caps."""
        bm = self.bm
        before = set(bm.faces)
        vr = [[bm.verts.new(self.xf @ V(p)) for p in r] for r in rings]
        fcol = {}
        nb = len(vr) if closed else len(vr) - 1
        for i in range(nb):
            a, b = vr[i], vr[(i + 1) % len(vr)]
            n = max(len(a), len(b))
            for j in range(n):
                j2 = (j + 1) % n
                if len(a) == 1:
                    q = (a[0], b[j], b[j2])
                elif len(b) == 1:
                    q = (a[j], a[j2], b[0])
                else:
                    q = (a[j], a[j2], b[j2], b[j])
                f = bm.faces.new(q)
                if bands and i < len(bands) and bands[i]:
                    fcol[f] = bands[i]
        if not closed:
            if caps[0] and len(vr[0]) >= 3:
                f = bm.faces.new(vr[0])
                if capcol[0]:
                    fcol[f] = capcol[0]
            if caps[1] and len(vr[-1]) >= 3:
                f = bm.faces.new(list(reversed(vr[-1])))
                if capcol[1]:
                    fcol[f] = capcol[1]
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        return self._reg(before, color, hull, fcol)

    def cbox(self, loc, size, color, ch=0.003, seg=1, rot=(0, 0, 0), hull=True, skip=(), axis=None):
        """Box with its edges chamfered (seg=1) or bevelled (seg=2); axis='y' limits that to the edges running
        along local y (cheap extrusion look). skip drops faces of a plain box ('-z', '+x'...)."""
        bm = self.bm
        before = set(bm.faces)
        M = self.xf @ mat_trs(loc, rot, size)
        verts = bmesh.ops.create_cube(bm, size=1.0, matrix=M)['verts']
        if ch > 0:
            edges = list({e for v in verts for e in v.link_edges})
            if axis:
                R = (self.xf @ mat_trs(loc, rot)).to_3x3().inverted()
                ai = 'xyz'.index(axis)
                edges = [e for e in edges if abs((R @ (e.verts[1].co - e.verts[0].co)).normalized()[ai]) > 0.9]
            bmesh.ops.bevel(bm, geom=edges, offset=ch, offset_type='OFFSET', segments=seg,
                            profile=0.5, affect='EDGES', clamp_overlap=True)
        elif skip:
            R = (self.xf @ mat_trs(loc, rot)).to_3x3().inverted()
            kill = []
            for f in {f for v in verts for f in v.link_faces}:
                n = (R @ f.normal).normalized()
                for s in skip:
                    ax = 'xyz'.index(s[1])
                    if n[ax] * (1 if s[0] == '+' else -1) > 0.9:
                        kill.append(f)
            bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
        if not skip:      # closed: make normals outward even under a mirrored transform
            bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in before])
        return self._reg(before, color, hull)

    def box(self, loc, size, color, rot=(0, 0, 0), hull=False, skip=()):
        return self.cbox(loc, size, color, ch=0, rot=rot, hull=hull, skip=skip)

    def bar(self, a, b, w, h, color, hull=False, up=(0, 0, 1)):
        """Box from point a to b, section w (side) x h (up)."""
        a, b = V(a), V(b)
        d = (b - a).normalized()
        upv = V(up) - d * V(up).dot(d)
        upv.normalize()
        s = d.cross(upv)
        R = Matrix((s, d, upv)).transposed().to_4x4()
        M = Matrix.Translation((a + b) / 2) @ R
        with self.at(m=M):
            return self.box((0, 0, 0), (w, (b - a).length, h), color, hull=hull)

    def ext(self, prof, color, o, u, v, w, d0, d1, ch0=0.0, ch1=0.0, hull=True, stations=None, bands=None):
        """Extrude a 2D profile (u, v) along w from d0 to d1; chamfers = inset rings at the ends.
        stations: [(d, inset)] for grooved / stepped extrusions instead of d0/d1/chamfers."""
        o, u, v, w = V(o), V(u), V(v), V(w)
        P = ccw(prof)

        def ring(p2, d):
            return [o + u * p[0] + v * p[1] + w * d for p in p2]
        if stations is None:
            stations = []
            if ch0 > 0:
                stations.append((d0, ch0))
            stations.append((d0 + ch0, 0.0))
            stations.append((d1 - ch1, 0.0))
            if ch1 > 0:
                stations.append((d1, ch1))
        rings = [ring(inset2d(P, s) if s > 0 else P, d) for d, s in stations]
        return self.loft(rings, color, hull, bands=bands)

    def ext_y(self, prof, y0, y1, color, ch0=0.0, ch1=0.0, hull=True, x=0.0, z=0.0, stations=None, bands=None):
        return self.ext(prof, color, (x, 0, z), (1, 0, 0), (0, 0, 1), (0, 1, 0), y0, y1, ch0, ch1, hull, stations, bands)

    def ext_x(self, prof, x0, x1, color, ch=0.0, hull=True, stations=None, bands=None):
        return self.ext(prof, color, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), x0, x1, ch, ch, hull, stations, bands)

    def ext_z(self, prof, z0, z1, color, ch0=0.0, ch1=0.0, hull=True, stations=None, bands=None):
        return self.ext(prof, color, (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), z0, z1, ch0, ch1, hull, stations, bands)

    def xbar(self, x0, x1, prof, color, ch=0.0015, hull=True):
        """Side-profile plate across X (sights, levers, triggers)."""
        return self.ext_x(prof, x0, x1, color, ch=ch, hull=hull)

    def lathe(self, prof, color, axis='y', c=(0, 0, 0), seg=12, hull=True, bands=None, a0=None, closed=False, sc=(1.0, 1.0)):
        """Revolve [(t, r)] around an axis through c; r == 0 makes an apex (closed ends, recessed bores)."""
        ax, u, v = AXES[axis] if isinstance(axis, str) else axis
        c = V(c)
        a0 = (math.pi / seg) if a0 is None else D(a0)
        rings = []
        for t, r in prof:
            if r < 1e-7:
                rings.append([c + ax * t])
            else:
                rings.append([c + ax * t + u * (r * sc[0] * math.cos(a0 + 2 * math.pi * k / seg)) + v * (r * sc[1] * math.sin(a0 + 2 * math.pi * k / seg)) for k in range(seg)])
        return self.loft(rings, color, hull, bands=bands, closed=closed)

    def ring(self, axis, c, t0, t1, r0, r1, color, seg=12, hull=True, bands=None):
        """Washer / tube with a real hole (closed revolve of a rectangle)."""
        return self.lathe([(t0, r0), (t0, r1), (t1, r1), (t1, r0)], color, axis, c, seg, hull, closed=True, bands=bands)

    def tube(self, pts, color, sides=6, up=(0, 0, 1), hull=True, a0=None, bands=None):
        """Swept tube through [(p, w, h)]; w = 0 makes an apex. up may be one vector or one per point."""
        n = len(pts)
        a0 = (math.pi / sides) if a0 is None else D(a0)
        rings = []
        for i, (p, w, h) in enumerate(pts):
            p = V(p)
            t = (V(pts[min(i + 1, n - 1)][0]) - V(pts[max(i - 1, 0)][0])).normalized()
            uu = V(up[i]) if isinstance(up, list) else V(up)
            uu = (uu - t * uu.dot(t)).normalized()
            s = t.cross(uu)
            if w <= 0:
                rings.append([p])
            else:
                rings.append([p + s * (math.cos(a0 + 2 * math.pi * k / sides) * w / 2) + uu * (math.sin(a0 + 2 * math.pi * k / sides) * h / 2) for k in range(sides)])
        return self.loft(rings, color, hull, bands=bands)

    def pin(self, x0, x1, y, z, r, color='steel', seg=6):
        """Cross pin through a part: both ends show (one shape)."""
        return self.lathe([(x0, 0), (x0, r), (x1, r), (x1, 0)], color, 'x', (0, y, z), seg, hull=False)

    def screw(self, p, n, r=0.0032, h=0.004, color='steel2', seg=6):
        n = V(n).normalized()
        u = n.orthogonal().normalized()
        return self.lathe([(-0.001, 0), (-0.001, r), (h, r), (h, 0)], color, (n, u, n.cross(u)), p, seg, hull=False, bands=[None, None, None])


def g2w(rake, gy, gz, ay=0.0, az=0.0):
    """Grip frame (gy forward along the hand, gz along the grip axis) -> weapon (y, z); rake tilts the grip bottom back."""
    a = D(rake)
    return (ay + gy * math.cos(a) + gz * math.sin(a), az - gy * math.sin(a) + gz * math.cos(a))


def gprof(rake, pts, ay=0.0, az=0.0):
    return [g2w(rake, gy, gz, ay, az) for gy, gz in pts]


def finish(name, kit, ht=HULL_T):
    """Triangulate n-gons (exact z-fight test on convex pieces), build, then drop the shell of inner details."""
    bm = kit.bm
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
    if DEBUG is not None:
        cnt = {}
        for f in bm.faces:
            cnt[f[kit.sl]] = cnt.get(f[kit.sl], 0) + len(f.verts) - 2
        tot = sum(c * (1 if sid in kit.nohull else 2) for sid, c in cnt.items())
        print('== %s: %d tris incl. hull' % (name, tot))
        for sid, c in sorted(cnt.items(), key=lambda t: -t[1])[:40]:
            print('   %4d %s  %s' % (c * (1 if sid in kit.nohull else 2), ' ' if sid in kit.nohull else 'H', DEBUG.get((id(kit), sid))))
    obj = build_object(name, kit.m, 0, ht)
    if kit.nohull:
        b2 = bmesh.new()
        b2.from_mesh(obj.data)
        hl = b2.verts.layers.float_vector.get('_HULL')
        sl = b2.faces.layers.int.get('shape_id')
        kill = [f for f in b2.faces if f[sl] in kit.nohull and all(v[hl].length > 0 for v in f.verts)]
        bmesh.ops.delete(b2, geom=kill, context='FACES')
        b2.to_mesh(obj.data)
        b2.free()
    return obj


def explain(err, kits):
    """IB_DEBUG=1: name the code lines that built the shapes in a z-fight error."""
    import re
    if DEBUG is None:
        return
    for a, b in re.findall(r'shapes (\d+)/(\d+)', str(err)):
        for sid in (int(a), int(b)):
            kit = kits[sid // 100000]
            print('   shape', sid, DEBUG.get((id(kit), sid % 100000)))


def zcheck_together(name, parts):
    """Z-fight test of several kits as placed together in the game (e.g. gun + magazine at its socket)."""
    tmp = bmesh.new()
    lay = tmp.faces.layers.int.new('shape_id')
    for i, (kit, off) in enumerate(parts):
        off = V(off)
        for f in kit.bm.faces:
            vs = [tmp.verts.new(v.co + off) for v in f.verts]
            nf = tmp.faces.new(vs)
            nf[lay] = f[kit.sl] + 100000 * i
    check_zfight(name, tmp, lay)
    tmp.free()


# ================================================================ shared gun parts
HAND = {'cy': -0.002, 'hx': 0.017, 'hy': 0.024}       # grip cross-section the glove is modelled around
TRIG = (0.040, -0.013)                                  # trigger face in the grip frame (gy, gz)


def grip(k, rake, style='pistol', color='furn', panel='gun3', w=0.034, ay=0.0, az=0.0, top=0.012, bottom=-0.100,
         ptop=-0.022, grooves=3, ch=0.004):
    """Pistol grip around the standard hand section; texture panels + ink grooves on both sides + a cross screw."""
    hy, cy = HAND['hy'], HAND['cy']
    f, b = cy + hy, cy - hy
    if style == 'pistol':      # beavertail + flared well
        pts = [(f - 0.002, top), (f + 0.002, -0.026), (f - 0.001, -0.046), (f + 0.002, -0.066), (f + 0.001, bottom + 0.006),
               (f + 0.003, bottom), (b - 0.004, bottom), (b - 0.002, -0.050), (b - 0.004, -0.008), (b - 0.020, 0.006),
               (b - 0.020, top), (b + 0.010, top + 0.004)]
    elif style == 'ar':        # A2 style with the finger nub
        pts = [(f - 0.004, top), (f, -0.030), (f + 0.006, -0.044), (f, -0.056), (f + 0.002, bottom),
               (b + 0.004, bottom - 0.004), (b - 0.004, -0.040), (b - 0.006, -0.004), (b + 0.004, top)]
    elif style == 'rubber':    # revolver: finger grooves, rounded butt
        pts = [(f - 0.003, top), (f + 0.003, -0.026), (f - 0.002, -0.045), (f + 0.003, -0.064), (f - 0.004, bottom + 0.002),
               (b + 0.004, bottom - 0.004), (b - 0.004, bottom + 0.010), (b - 0.005, -0.040), (b + 0.006, top)]
    else:                      # 'smg': straight, chunky, palm swell
        pts = [(f - 0.002, top), (f + 0.002, -0.030), (f, -0.056), (f + 0.002, bottom), (b - 0.002, bottom),
               (b - 0.005, -0.050), (b - 0.002, top)]
    k.ext_x(gprof(rake, pts, ay, az), -w / 2, w / 2, color, ch=ch)
    pp = [(f - 0.008, ptop), (f - 0.006, bottom + 0.016), (b + 0.006, bottom + 0.016), (b + 0.005, ptop)]
    gzs = [ptop - 0.008 - j * (ptop - 0.008 - bottom - 0.022) / max(1, grooves - 1) for j in range(grooves)]
    for s in (-1, 1):
        x0, x1 = s * (w / 2 - 0.002), s * (w / 2 + 0.003)
        k.ext_x(gprof(rake, pp, ay, az), min(x0, x1), max(x0, x1), panel, hull=False)
        for gz in gzs:
            a = g2w(rake, f - 0.009, gz, ay, az)
            b2 = g2w(rake, b + 0.007, gz, ay, az)
            xm = s * (w / 2 + 0.0045)
            k.bar((xm, a[0], a[1]), (xm, b2[0], b2[1]), 0.004, 0.0035, 'ink')
    zc = (gzs[0] + gzs[1]) / 2 if grooves > 1 else gzs[0] - 0.012
    k.pin(-w / 2 - 0.0065, w / 2 + 0.0065, *g2w(rake, cy - 0.004, zc, ay, az), 0.0035, color='steel2')


def trigger_guard(k, rake, front=0.072, depth=-0.046, w=0.012, color='gun2', ay=0.0, az=0.0, top=-0.004, hook=True):
    """U-shaped guard in front of the grip (side profile), squared front with an optional finger hook."""
    gyb = HAND['cy'] + HAND['hy'] - 0.004
    yb, zb = g2w(rake, gyb, -0.036, ay, az)
    outer = [(front, top), (front + 0.002, depth + 0.006)]
    if hook:
        outer += [(front + 0.006, depth - 0.002), (front - 0.002, depth - 0.002)]
    else:
        outer += [(front - 0.006, depth)]
    outer += [(yb + 0.010, depth), (yb, zb - 0.004)]
    inner = [(yb + 0.006, zb + 0.004), (yb + 0.014, depth + 0.008), (front - 0.008, depth + 0.008), (front - 0.008, top)]
    k.ext_x(outer + inner, -w / 2, w / 2, color)


def trigger(k, rake, color='steel', ay=0.0, az=0.0, ext=0.0):
    ty, tz = g2w(rake, TRIG[0], TRIG[1], ay, az)
    pts = [(ty - 0.002, tz + 0.016 + ext), (ty + 0.008, tz + 0.016 + ext), (ty + 0.006, tz - 0.002),
           (ty - 0.002, tz - 0.013), (ty - 0.005, tz - 0.009), (ty + 0.0, tz + 0.002)]
    k.ext_x(pts, -0.0035, 0.0035, color)


def muzzle(k, y0, y1, r, z, x=0.0, color='steel', seg=10, ports=0, top_ports=0, hull=True, rb=None, ink_face=False, slot=0.009):
    """Lathe muzzle device with a recessed ink bore; side / top ports are ink slots standing 3+ mm proud."""
    rb = rb or r * 0.5
    k.lathe([(y0, 0), (y0, r), (y1, r), (y1, rb), (y1 - 0.008, rb), (y1 - 0.008, 0)], color, 'y', (x, 0, z), seg, hull,
            bands=[None, None, 'ink' if ink_face else None, 'ink', 'ink'])
    L = y1 - y0
    for i in range(ports):
        yc = y0 + L * (0.3 + 0.45 * i / max(1, ports - 1)) if ports > 1 else y0 + L * 0.5
        for sgn in (-1, 1):
            k.box((x + sgn * (r - 0.0005), yc, z), (0.008, min(slot, L / (ports * 2.2)), r * 0.9), 'ink', skip=('-x' if sgn > 0 else '+x',))
    for i in range(top_ports):
        yc = y0 + L * (0.3 + 0.45 * i / max(1, top_ports - 1)) if top_ports > 1 else y0 + L * 0.5
        k.box((x, yc, z + r - 0.0005), (r * 0.9, min(slot, L / (top_ports * 2.2)), 0.008), 'ink', skip=('-z',))


def barrel(k, y0, y1, r, z, x=0.0, color='steel', seg=10, hull=True):
    k.lathe([(y0, 0), (y0, r), (y1, r), (y1, 0)], color, 'y', (x, 0, z), seg, hull)


def rail(k, y0, y1, z, w=0.022, pitch=0.012, x=0.0, color='gunmetal', base='ink', clear=()):
    """Picatinny-style rail on a surface at height z: dark core (3 mm proud, sides 3 mm inset) and raised
    teeth 4.5 mm above the core. clear: y ranges left without teeth (clamps of sights and optics)."""
    k.box((x, (y0 + y1) / 2, z + 0.0015), (w - 0.006, y1 - y0, 0.003), base, skip=('-z',))
    n = max(1, int((y1 - y0 - 0.004) / pitch))
    gap = (y1 - y0 - n * pitch) / 2
    for i in range(n):
        yc = y0 + gap + pitch * (i + 0.5)
        if any(a - pitch * 0.5 < yc < b + pitch * 0.5 for a, b in clear):
            continue
        k.box((x, yc, z + 0.004), (w, pitch * 0.6, 0.007), color, skip=('-z',))


def stripe(k, y0, y1, z0, z1, half, color='trim'):
    """Flat Amber accent stripe through a body of half-width <= half - 3 mm (shows on both sides)."""
    k.box((0, (y0 + y1) / 2, (z0 + z1) / 2), (half * 2, y1 - y0, z1 - z0), color)


def mag_box(k, rake, top, bottom, depth, w, color='gun2', plate='gun3', curve=0.0, ribs=True, brass=True, plate_h=0.012,
            plate_w=None, plate_d=0.006, wt=0.45):
    """Detachable box magazine in its own frame (origin = MAG socket at the well mouth), built along the
    raked axis; curve bends the bottom forward (rifle mags). Body bottom sits 4 mm inside the base plate."""
    n = 4 if curve else 1
    front, back = [], []
    for i in range(n + 1):
        t = i / n
        gz = top + (bottom - 0.004 - top) * t
        off = curve * t * t
        front.append(g2w(rake, depth / 2 + off, gz))
        back.append(g2w(rake, -depth / 2 + off, gz))
    k.ext_x(front + list(reversed(back)), -w / 2, w / 2, color, ch=0.002)
    pl = [g2w(rake, depth / 2 + curve + plate_d - 0.002, bottom + 0.002), g2w(rake, depth / 2 + curve + plate_d, bottom - plate_h),
          g2w(rake, -depth / 2 + curve - plate_d, bottom - plate_h), g2w(rake, -depth / 2 + curve - plate_d + 0.002, bottom + 0.002)]
    pw = plate_w / 2 if plate_w else w / 2 + 0.0035
    k.ext_x(pl, -pw, pw, plate)
    if ribs:            # one raised rib per side following the curve + witness holes
        for s in (-1, 1):
            pts = []
            for i in range(3):
                t = 0.15 + 0.35 * i
                y, z = g2w(rake, -depth * 0.18 + curve * t * t, top + (bottom - top) * t)
                pts.append(((s * (w / 2 + 0.001), y, z), 0.006, 0.008))
            k.tube(pts, 'gun3', sides=4, up=(1, 0, 0), hull=False, a0=45)
            for j in range(1):
                t = wt + 0.12 * j
                y, z = g2w(rake, depth * 0.22 + curve * t * t, top + (bottom - top) * t)
                k.box((s * (w / 2), y, z), (0.008, 0.005, 0.005), 'ink', skip=('-x' if s > 0 else '+x',))
    if brass:
        cy, cz = g2w(rake, 0.002, top + 0.004)
        k.lathe([(cy - depth * 0.35, 0), (cy - depth * 0.35, 0.0055), (cy + depth * 0.15, 0.0055), (cy + depth * 0.32, 0.003), (cy + depth * 0.32, 0)],
                'brass', 'y', (0, 0, cz), 6, hull=False)


def iron_rear(k, y, z, w=0.028, h=0.014, color='gunmetal'):
    """Flip-up aperture rear sight on a rail at height z (clamp + ring). Returns the sight-line height."""
    k.cbox((0, y, z + h / 2), (w, 0.016, h), color, ch=0.002, axis='y')
    k.ring('y', (0, 0, z + h + 0.0065), y - 0.003, y + 0.003, 0.0035, 0.0075, color, seg=8, hull=False)
    return z + h + 0.0065


def iron_front(k, y, z, w=0.028, h=0.014, post=0.020, color='gunmetal'):
    k.cbox((0, y, z + h / 2), (w, 0.016, h), color, ch=0.002, axis='y')
    for s in (-1, 1):
        k.box((s * 0.0085, y, z + h + post / 2 - 0.002), (0.005, 0.010, post), color, hull=True)
    k.box((0, y, z + h + post / 2 - 0.003), (0.004, 0.006, post - 0.002), 'ink')


def red_dot(k, y, z, L=0.05, r=0.017, color='gunmetal'):
    """Tube red-dot on a rail at height z: clamp, hollow tube with recessed lenses, turret, amber ring."""
    cz = z + 0.010 + r
    k.cbox((0, y, z + 0.006), (0.030, L * 0.45, 0.012), color, ch=0.002, axis='y')
    k.lathe([(y - L / 2 + 0.006, 0), (y - L / 2 + 0.006, r - 0.004), (y - L / 2, r - 0.004), (y - L / 2, r), (y + L / 2, r),
             (y + L / 2, r - 0.004), (y + L / 2 - 0.008, r - 0.004), (y + L / 2 - 0.008, 0)], color, 'y', (0, 0, cz), 10,
            bands=['lens', 'ink', None, None, None, 'ink', 'lens'])
    k.lathe([(0, 0), (0, 0.0065), (0.009, 0.0065), (0.009, 0)], 'gun3', 'z', (0, y - L * 0.1, cz + r - 0.003), 8, hull=False)
    return cz


# ================================================================ weapons
# Each builder returns (gun kit, mag kit, info). info: rake (grip angle), sockets (weapon space), cls.
WEAPONS = {}


def build_pip(pal):
    """P-12 Warden: chunky service pistol."""
    rake = 16
    k = Kit(pal)
    k.ext_y(rrect(0.047, 0.046, ct=0.009, cb=0.003, cy=0.029), -0.086, 0.150, 'gunmetal', ch0=0.004, ch1=0.010)   # slide
    for side in (-1, 1):
        sk = ('-x' if side > 0 else '+x',)
        for i in range(4):
            k.box((side * 0.0245, -0.076 + i * 0.0085, 0.028), (0.006, 0.004, 0.026), 'ink', skip=sk)     # rear serrations
        for i in range(2):
            k.box((side * 0.0245, 0.108 + i * 0.0085, 0.030), (0.006, 0.004, 0.020), 'ink', skip=sk)      # front serrations
    k.box((0.01525, 0.024, 0.0455), (0.0225, 0.050, 0.019), 'ink')             # ejection port (right top)
    k.box((0.012, 0.022, 0.0555), (0.010, 0.040, 0.006), 'steel')              # barrel hood in the port
    muzzle(k, 0.143, 0.1615, 0.0115, 0.030, rb=0.006, hull=False)              # barrel crown
    stripe(k, -0.040, 0.094, 0.010, 0.016, 0.0265)
    for s in (-1, 1):                                                          # rear sight ears, white dots
        k.box((s * 0.0095, -0.066, 0.056), (0.010, 0.013, 0.016), 'ink', hull=True)
        k.box((s * 0.0095, -0.0735, 0.0595), (0.004, 0.004, 0.004), 'paper')
    k.box((0, 0.134, 0.054), (0.0075, 0.012, 0.014), 'ink', hull=True)          # front post + red fibre
    k.box((0, 0.1265, 0.0585), (0.004, 0.004, 0.004), 'red')
    k.ext_y(rrect(0.041, 0.024, c=0.003, cy=-0.001), -0.074, 0.134, 'gun2', ch1=0.008)   # polymer frame
    for i in range(3):
        k.box((0, 0.088 + i * 0.012, -0.0105), (0.047, 0.005, 0.013), 'ink')    # dust-cover rail slots
    k.xbar(-0.005, 0.005, [(-0.084, 0.006), (-0.093, 0.020), (-0.097, 0.034), (-0.090, 0.037), (-0.080, 0.016)], 'steel2', ch=0)  # hammer
    k.xbar(-0.0265, -0.0225, [(0.002, 0.000), (0.042, 0.000), (0.046, 0.006), (0.040, 0.009), (0.004, 0.006)], 'gun3', ch=0, hull=False)  # slide stop
    k.pin(-0.0235, 0.0235, 0.060, -0.004, 0.0028)
    k.pin(-0.0235, 0.0235, -0.050, 0.000, 0.0026)
    for i in range(2):                                                         # lightening cuts on the slide top
        k.box((0, 0.070 + i * 0.024, 0.052), (0.016, 0.016, 0.006), 'ink', skip=('-z',))
    k.box((0, -0.0865, 0.028), (0.024, 0.005, 0.024), 'gun3')                  # slide rear plate
    k.box((0.02375, 0.003, 0.030), (0.0055, 0.014, 0.006), 'steel')            # extractor
    k.box((-0.0225, 0.012, -0.006), (0.006, 0.008, 0.008), 'gun3')             # mag release
    k.box((-0.0235, 0.052, -0.0015), (0.004, 0.008, 0.009), 'gun3')            # takedown lever
    trigger_guard(k, rake, front=0.084, depth=-0.046)
    trigger(k, rake)
    grip(k, rake, 'pistol')
    my, mz = g2w(rake, HAND['cy'], -0.100)
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, 0.0, 0.040, 0.025, plate='gunmetal', plate_h=0.011, plate_w=0.041, ribs=False)
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.164, 0.030), 'eject': (0.03, 0.025, 0.048),
                   'sight': (0, -0.090, 0.062), 'cls': 'pistol'}


def build_rivet(pal):
    """AR-22 Rivet: modular assault rifle."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    k.ext_y(rrect(0.048, 0.044, ct=0.006, cb=0.002, cy=0.034), -0.112, 0.140, 'gunmetal', ch0=0.004, ch1=0.003)   # upper
    k.box((0.01675, 0.050, 0.042), (0.0205, 0.060, 0.016), 'ink')                 # ejection port
    k.box((0.0265, 0.052, 0.0255), (0.006, 0.054, 0.011), 'gun3')                 # open dust cover
    k.lathe([(0.0, 0), (0.0, 0.0065), (0.020, 0.0065), (0.024, 0.004), (0.024, 0)], 'steel2',
            (V((0.45, -0.89, 0)).normalized(), V((0, 0, 1)), V((0.89, 0.45, 0))), (0.019, -0.050, 0.040), 8, hull=False)  # forward assist
    k.ext_y(rrect(0.041, 0.034, c=0.003, cy=-0.004), -0.104, 0.140, 'gun2', ch0=0.004, ch1=0.004)                  # lower
    k.ext_x([(0.074, 0.004), (0.138, 0.004), (0.140, -0.040), (0.134, -0.052), (0.072, -0.052), (0.070, -0.040)], -0.0235, 0.0235, 'gun2', ch=0.003)  # magwell
    k.pin(-0.0265, 0.0265, 0.128, 0.000, 0.003)
    k.pin(-0.0235, 0.0235, -0.094, 0.000, 0.003)
    k.xbar(-0.0240, -0.0205, [(-0.050, -0.004), (-0.030, -0.006), (-0.028, 0.002), (-0.048, 0.004)], 'gun3', ch=0, hull=False)   # selector
    k.xbar(-0.0265, -0.0230, [(0.078, -0.012), (0.098, -0.012), (0.100, -0.004), (0.080, -0.002)], 'ink', ch=0, hull=False)      # bolt catch
    k.cbox((0, -0.118, 0.0535), (0.036, 0.012, 0.011), 'gun3', ch=0.002, axis='x')   # charging handle
    rail(k, -0.108, 0.136, 0.056, w=0.022, pitch=0.016, clear=[(-0.098, -0.082)])
    k.ext_y(rrect(0.054, 0.050, c=0.013, cy=bz), 0.138, 0.360, 'gun3', ch0=0.003, ch1=0.006)   # handguard
    for s in (-1, 1):
        for i in range(5):
            k.box((s * 0.0270, 0.172 + i * 0.036, bz + 0.004), (0.006, 0.022, 0.008), 'ink', skip=('-x' if s > 0 else '+x',))
        for i in range(2):
            k.screw((s * 0.0270, 0.152 + i * 0.196, bz - 0.006), (s, 0, 0))
    k.box((0, 0.250, bz - 0.0145), (0.0600, 0.180, 0.006), 'trim')
    rail(k, 0.141, 0.352, 0.059, w=0.020, pitch=0.018, clear=[(0.322, 0.338)])
    barrel(k, 0.350, 0.450, 0.0085, bz)
    muzzle(k, 0.448, 0.500, 0.0120, bz, rb=0.0055, ports=3)                       # birdcage
    sz = iron_rear(k, -0.090, 0.059)
    iron_front(k, 0.330, 0.062, post=0.008)                                     # post top on the aperture line
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.008, ptop=-0.038, grooves=2)
    k.lathe([(-0.112, 0), (-0.112, 0.014), (-0.270, 0.014), (-0.274, 0.010), (-0.274, 0)], 'steel2', 'y', (0, 0, 0.030), 8)   # buffer tube
    k.ext_x([(-0.180, 0.048), (-0.300, 0.050), (-0.304, -0.040), (-0.282, -0.046), (-0.250, -0.010), (-0.190, 0.012)], -0.019, 0.019, 'furn', ch=0.004)
    k.ext_x([(-0.299, 0.054), (-0.314, 0.054), (-0.316, -0.044), (-0.301, -0.044)], -0.0225, 0.0225, 'ink')    # butt pad
    k.box((0, -0.244, 0.028), (0.044, 0.044, 0.006), 'gun3')
    mk = Kit(pal)
    mag_box(mk, 4, 0.052, -0.120, 0.052, 0.026, curve=0.040)
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.105, -0.052), 'muzzle': (0, 0.502, bz), 'eject': (0.03, 0.050, 0.042),
                   'sight': (0, -0.105, sz), 'cls': 'rifle', 'guard': (0, 0.300, 0.034)}


def hood_sight(k, y0, y1, zb, w=0.034, h=0.026, t=0.005, color='gunmetal'):
    """Open reflex / holo sight: a hollow rectangular hood on a base with a tinted lens plate inside."""
    k.cbox((0, (y0 + y1) / 2, zb + 0.004), (w - 0.004, y1 - y0 + 0.006, 0.008), color, ch=0.002, axis='y')
    z0 = zb + 0.007
    oc, ic = rrect(w, h, ct=0.007, cb=0.002, cy=z0 + h / 2), rrect(w - 2 * t, h - 2 * t, ct=0.004, cb=0.001, cy=z0 + h / 2)
    ring = lambda p, y: [(q[0], y, q[1]) for q in p]
    k.loft([ring(ic, y0), ring(oc, y0), ring(oc, y1), ring(ic, y1)], color, closed=True, bands=[None, None, None, 'ink'])
    k.box((0, (y0 + y1) / 2, z0 + h / 2), (w - 2 * t + 0.003, 0.002, h - 2 * t + 0.003), 'lens')
    k.box((0, y0 + 0.004, z0 + t + 0.0025), (0.005, 0.004, 0.005), 'red')
    return z0 + h / 2


def scope(k, y0, y1, z, rt=0.0125, ro=0.023, re=0.019, lo=0.05, le=0.045, seg=12, color='gunmetal'):
    """Long scope: eyepiece bell, tube, objective bell; both lenses recessed (one closed revolve)."""
    prof = [(y0 + 0.008, 0), (y0 + 0.008, re - 0.004), (y0, re - 0.004), (y0, re), (y0 + le, re), (y0 + le + 0.014, rt),
            (y1 - lo - 0.016, rt), (y1 - lo, ro), (y1, ro), (y1, ro - 0.004), (y1 - 0.010, ro - 0.004), (y1 - 0.010, 0)]
    k.lathe(prof, color, 'y', (0, 0, z), seg, bands=['lens', 'ink', None, None, None, None, None, None, None, 'ink', 'lens'])
    for yy, rr in ((y0 + le - 0.010, re), (y1 - lo + 0.006, ro)):          # lens rings, 3 mm proud
        k.ring('y', (0, 0, z), yy, yy + 0.007, rr - 0.002, rr + 0.003, 'gun3', seg=seg, hull=False)


def turret(k, p, axis, r=0.009, h=0.014, color='gun3', cap='ink'):
    ax = {'z': 'z', 'x': 'x', '-x': (V((-1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)))}[axis]
    k.lathe([(0, 0), (0, r), (h, r), (h + 0.003, r - 0.003), (h + 0.003, 0)], color, ax, p, 8, hull=False, bands=[None, None, None, cap])


def vgrip(k, y, ztop, length=0.075, r=0.016, color='gun2', rake=0.0, seg=10):
    """Vertical foregrip (oval, flared foot) hanging below ztop at y."""
    with k.at((0, y, ztop), (-rake, 0, 0)):
        k.lathe([(-length, 0), (-length, r + 0.004), (-length + 0.010, r + 0.004), (-length + 0.014, r), (0.004, r), (0.004, 0)],
                color, 'z', (0, 0, 0), seg, sc=(1.0, 1.3))
        for j in range(3):
            k.box((-(r + 0.0015), 0, -0.016 - j * (length - 0.030) / 3), (0.006, 0.016, 0.004), 'ink', skip=('+x',))


def bipod_folded(k, y0, y1, z, x=0.014, color='steel2'):
    for s in (-1, 1):
        k.cbox((s * x, (y0 + y1) / 2, z), (0.008, y1 - y0, 0.008), color, ch=0.002, axis='y', hull=True)
        k.box((s * x, y1 - 0.010, z - 0.006), (0.016, 0.014, 0.010), 'ink')


def build_handcannon(pal):
    """R-50 Ironjaw: heavy revolver, full underlug, vent rib, ported barrel, fluted cylinder (the Mag)."""
    rake = 20
    k = Kit(pal)
    bz, cz = 0.040, 0.023
    # frame: recoil shield + topstrap + front block + bottom strap (the cylinder window between them)
    k.ext_x([(-0.034, -0.008), (0.0, -0.008), (0.0, 0.058), (-0.020, 0.060), (-0.034, 0.040)], -0.0215, 0.0215, 'gunmetal', ch=0.003)
    k.box((0, 0.025, 0.0545), (0.022, 0.046, 0.011), 'gunmetal', hull=True)
    k.ext_x([(0.049, -0.008), (0.078, -0.008), (0.078, 0.060), (0.049, 0.060)], -0.017, 0.017, 'gunmetal', ch=0.003)
    k.box((0, 0.025, -0.0055), (0.025, 0.046, 0.010), 'gunmetal', hull=True)
    # barrel with full underlug, vent rib, top ports, amber stripe on the lug
    k.ext_y(rrect(0.027, 0.046, ct=0.012, cb=0.004, cy=0.032, seg=2), 0.074, 0.238, 'gunmetal', ch1=0.006)
    k.box((0, 0.1425, 0.059), (0.008, 0.125, 0.008), 'gun3')
    for i in range(5):
        k.box((0, 0.094 + i * 0.022, 0.0565), (0.014, 0.006, 0.006), 'ink', skip=('-z',))
    for i in range(2):
        k.box((0, 0.210 + i * 0.008, 0.0555), (0.012, 0.004, 0.006), 'ink', skip=('-z',))
    muzzle(k, 0.230, 0.250, 0.0105, bz, rb=0.0055, hull=True, seg=8)
    k.box((0, 0.160, 0.019), (0.0335, 0.120, 0.006), 'trim')
    k.lathe([(0.076, 0), (0.076, 0.0045), (0.228, 0.0045), (0.234, 0.0025), (0.234, 0)], 'steel', 'y', (0, 0, 0.004), 6, hull=False)   # ejector rod
    # sights: front post with red insert, adjustable rear on the topstrap
    k.box((0, 0.226, 0.065), (0.008, 0.012, 0.018), 'ink', hull=True)
    k.box((0, 0.2172, 0.069), (0.004, 0.0055, 0.005), 'red')
    for s in (-1, 1):
        k.box((s * 0.008, 0.002, 0.066), (0.006, 0.012, 0.012), 'ink', hull=True)
        k.box((s * 0.008, -0.0055, 0.068), (0.003, 0.003, 0.004), 'paper')
    # hammer spur, cylinder latch, side-plate screws
    k.xbar(-0.0045, 0.0045, [(-0.030, 0.034), (-0.044, 0.050), (-0.060, 0.058), (-0.062, 0.052), (-0.044, 0.038), (-0.034, 0.020)], 'steel2', ch=0)
    k.cbox((-0.0245, -0.016, 0.034), (0.006, 0.014, 0.008), 'gun3', ch=0.0015, hull=False)
    k.screw((-0.0215, -0.012, 0.004), (-1, 0, 0))
    k.pin(-0.020, 0.020, 0.066, 0.004, 0.003)
    trigger_guard(k, rake, front=0.060, depth=-0.046, hook=False, top=-0.006)
    trigger(k, rake, ext=0.006)
    grip(k, rake, 'rubber', w=0.036, top=-0.004, ptop=-0.026)
    # cylinder (the Mag): 6 flutes, chamfered front, 6 ink chambers, ratchet star at the rear
    mk = Kit(pal)
    R = 0.0215
    prof = []
    for i in range(6):
        a = 60 * i
        prof += [(R * math.cos(D(a - 18)), R * math.sin(D(a - 18))), (R * math.cos(D(a + 18)), R * math.sin(D(a + 18))),
                 ((R - 0.006) * math.cos(D(a + 30)), (R - 0.006) * math.sin(D(a + 30)))]
    mk.ext_y(prof, -0.022, 0.022, 'steel2', ch1=0.003)
    for i in range(6):
        a = D(60 * i + 30 + 30)
        mk.lathe([(0.016, 0), (0.016, 0.0052), (0.0255, 0.0052), (0.0255, 0)], 'ink', 'y', (0.0128 * math.cos(a), 0, 0.0128 * math.sin(a)), 5, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.025, cz), 'muzzle': (0, 0.252, bz), 'eject': (-0.03, 0.025, cz),
                   'sight': (0, -0.012, 0.072), 'cls': 'pistol', 'pivot': (-0.012, 0.025, 0.000)}


def build_twintap(pal):
    """P-16 Twinfire: stacked twin-bore burst pistol, compensator, mini reflex, extended mag."""
    rake = 18
    k = Kit(pal)
    k.ext_y(rrect(0.046, 0.060, ct=0.011, cb=0.003, cy=0.034), -0.084, 0.124, 'gunmetal', ch0=0.004, ch1=0.003)   # tall slide
    for s in (-1, 1):
        sk = ('-x' if s > 0 else '+x',)
        for zz in (0.020, 0.048):            # twin barrel flutes along the slide
            k.box((s * 0.0235, 0.040, zz), (0.006, 0.120, 0.005), 'ink', skip=sk)
        for i in range(2):
            k.box((s * 0.0235, -0.074 + i * 0.010, 0.034), (0.006, 0.0045, 0.040), 'ink', skip=sk)
    k.box((0, 0.045, 0.034), (0.0525, 0.080, 0.006), 'trim')
    k.box((0.015, -0.005, 0.0605), (0.023, 0.046, 0.016), 'ink')                # port
    # compensator with top + side ports, twin crowns
    k.cbox((0, 0.143, 0.034), (0.050, 0.040, 0.058), 'gun3', ch=0.004, axis='y')
    for i in range(3):
        k.box((0, 0.131 + i * 0.011, 0.0635), (0.024, 0.005, 0.008), 'ink', skip=('-z',))
    for s in (-1, 1):
        for i in range(2):
            k.box((s * 0.0255, 0.134 + i * 0.016, 0.034), (0.008, 0.008, 0.030), 'ink', skip=('-x' if s > 0 else '+x',))
    for zz in (0.020, 0.048):
        muzzle(k, 0.156, 0.176, 0.0085, zz, rb=0.0048, hull=False, seg=8)
    # mini reflex on the slide + backup notch
    hz = hood_sight(k, -0.070, -0.040, 0.064, w=0.030, h=0.022, t=0.0045)
    k.box((0, 0.112, 0.0675), (0.007, 0.010, 0.010), 'ink', hull=True)
    # frame with rail slots, squared hooked guard
    k.ext_y(rrect(0.040, 0.024, c=0.003, cy=-0.004), -0.070, 0.118, 'gun2', ch1=0.010)
    for i in range(3):
        k.box((0, 0.086 + i * 0.012, -0.0135), (0.047, 0.005, 0.013), 'ink')
    k.xbar(-0.005, 0.005, [(-0.084, 0.008), (-0.091, 0.024), (-0.087, 0.032), (-0.080, 0.018)], 'steel2', ch=0)
    k.xbar(-0.0255, -0.0215, [(0.000, -0.004), (0.036, -0.004), (0.040, 0.002), (0.004, 0.004)], 'gun3', ch=0, hull=False)
    k.pin(-0.0225, 0.0225, 0.050, -0.008, 0.0028)
    trigger_guard(k, rake, front=0.080, depth=-0.048, hook=True, top=-0.010)
    trigger(k, rake, color='gun3')
    grip(k, rake, 'pistol', w=0.034, top=0.004, ptop=-0.026, grooves=3)
    my, mz = g2w(rake, HAND['cy'], -0.100)
    mk = Kit(pal)
    mag_box(mk, rake, 0.078, -0.030, 0.040, 0.025, plate='gun3', plate_h=0.012, plate_w=0.041, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.0, -0.016)
        mk.box((s * 0.0125, y, z), (0.008, 0.026, 0.020), 'gun2', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.178, 0.034), 'eject': (0.03, -0.005, 0.060),
                   'sight': (0, -0.090, hz), 'cls': 'pistol'}


def build_buzz(pal):
    """KV-9 Buzzsaw: boxy all-round SMG, reflex sight, vertical foregrip, skeleton stock, straight mag."""
    rake = 14
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.048, 0.060, ct=0.009, cb=0.004, cy=0.038), -0.096, 0.140, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    rail(k, -0.090, 0.132, 0.068, w=0.022, clear=[(-0.078, -0.036)])
    hz = hood_sight(k, -0.076, -0.038, 0.071)
    k.box((0.0155, 0.040, 0.050), (0.023, 0.050, 0.016), 'ink')                     # port
    k.box((0.0285, 0.036, 0.050), (0.005, 0.030, 0.010), 'steel')                   # bolt face in the port
    k.ext_y(rrect(0.040, 0.026, c=0.003, cy=0.005), -0.070, 0.124, 'gun2', ch0=0.004, ch1=0.004)                 # trigger housing
    stripe(k, -0.070, 0.110, 0.022, 0.028, 0.0270)
    # charging tube (left, HK style) with knob
    k.lathe([(0.020, 0), (0.020, 0.0065), (0.170, 0.0065), (0.170, 0)], 'gun3', 'y', (-0.025, 0, 0.060), 8, hull=False)
    k.cbox((-0.036, 0.150, 0.060), (0.016, 0.010, 0.010), 'ink', ch=0.002, hull=False)
    # shroud with vents, barrel, birdcage
    k.ext_y(rrect(0.044, 0.044, ct=0.006, cb=0.010, cy=0.030), 0.136, 0.214, 'gun2', ch1=0.006)
    for s in (-1, 1):
        for i in range(3):
            k.box((s * 0.0225, 0.152 + i * 0.020, 0.030), (0.006, 0.010, 0.018), 'ink', skip=('-x' if s > 0 else '+x',))
    barrel(k, 0.205, 0.246, 0.0090, bz)
    muzzle(k, 0.246, 0.280, 0.0115, bz, ports=2, rb=0.0055, seg=8)
    k.box((0, 0.200, 0.064), (0.006, 0.008, 0.016), 'ink', hull=True)               # front post
    # magwell, vertical foregrip, trigger group, grip
    k.ext_x([(0.066, 0.010), (0.118, 0.010), (0.120, -0.030), (0.114, -0.038), (0.066, -0.038), (0.062, -0.026)], -0.0225, 0.0225, 'gun2', ch=0.003)
    vgrip(k, 0.180, 0.010, seg=8)
    trigger_guard(k, rake, front=0.062, depth=-0.046, hook=False, top=0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=0.010, ptop=-0.028, grooves=2)
    k.xbar(-0.0275, -0.0240, [(-0.052, 0.010), (-0.032, 0.008), (-0.030, 0.016), (-0.050, 0.018)], 'gun3', ch=0, hull=False)   # selector
    k.pin(-0.0270, 0.0270, -0.080, 0.012, 0.003)
    # skeleton stock (extended): top bar, sloped lower strut, butt plate
    k.box((0, -0.170, 0.050), (0.016, 0.160, 0.014), 'furn', hull=True)
    k.bar((0, -0.100, 0.004), (0, -0.240, -0.030), 0.014, 0.012, 'furn', hull=True)
    k.ext_x([(-0.236, 0.062), (-0.256, 0.062), (-0.258, -0.044), (-0.238, -0.044)], -0.019, 0.019, 'ink', ch=0.003)
    k.box((0, -0.244, 0.010), (0.044, 0.008, 0.050), 'gun3')
    mk = Kit(pal)
    mag_box(mk, 2, 0.034, -0.150, 0.040, 0.026, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 2, 'mag': (0, 0.092, -0.038), 'muzzle': (0, 0.282, bz), 'eject': (0.03, 0.040, 0.050),
                   'sight': (0, -0.100, hz), 'cls': 'smg', 'fore': (0.180, 0.010)}


def build_whisk(pal):
    """KV-4 Whiplash: compact machine pistol, mag in the grip, long suppressor can, wire stock."""
    rake = 8
    k = Kit(pal)
    bz = 0.032
    k.ext_y(rrect(0.044, 0.064, ct=0.010, cb=0.004, cy=0.026), -0.078, 0.110, 'gunmetal', ch0=0.005, ch1=0.012)   # receiver
    rail(k, -0.075, 0.096, 0.058, w=0.022, clear=[(-0.070, -0.050)])
    k.cbox((0, -0.060, 0.064), (0.024, 0.016, 0.012), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, 0.0755), -0.063, -0.057, 0.003, 0.0065, 'gunmetal', seg=8, hull=False)
    k.box((0.0135, 0.020, 0.046), (0.0225, 0.040, 0.014), 'ink')                       # port
    k.cbox((0, -0.086, 0.050), (0.040, 0.010, 0.010), 'gun3', ch=0.002, axis='x')     # T charging handle
    for s in (-1, 1):
        k.box((s * 0.0235, 0.040, 0.010), (0.006, 0.050, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    # suppressor can: gun3 with one amber band (the accent stripe), recessed bore
    L0, L1, r = 0.106, 0.270, 0.0205
    k.lathe([(L0, 0), (L0, r - 0.004), (L0 + 0.006, r), (0.180, r), (0.180, r + 0.003), (0.202, r + 0.003), (0.202, r), (L1 - 0.004, r),
             (L1, r - 0.004), (L1, 0.006), (L1 - 0.010, 0.006), (L1 - 0.010, 0)], 'gun3', 'y', (0, 0, bz), 12,
            bands=[None, None, None, 'trim', 'trim', 'trim', None, None, None, 'ink', 'ink'])
    for i in range(3):
        k.box((0, 0.230 + i * 0.012, bz + r - 0.0005), (0.010, 0.004, 0.007), 'ink', skip=('-z',))
    k.box((0, 0.216, bz + r + 0.010), (0.005, 0.008, 0.024), 'ink', hull=True)       # front post on the can (on the sight line)
    # folding vertical foregrip, grip (mag well), guard
    vgrip(k, 0.088, -0.006, length=0.060, r=0.014)
    trigger_guard(k, rake, front=0.064, depth=-0.046, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.036, top=0.000, bottom=-0.096, ptop=-0.024)
    # wire stock (collapsed): two rods + butt plate
    for s in (-1, 1):
        k.lathe([(-0.150, 0), (-0.150, 0.004), (-0.074, 0.004), (-0.074, 0)], 'steel', 'y', (s * 0.016, 0, 0.012), 6, hull=True)
    k.ext_x([(-0.146, 0.040), (-0.160, 0.040), (-0.162, -0.034), (-0.148, -0.030)], -0.022, 0.022, 'furn', ch=0.003)
    k.box((0, -0.153, -0.022), (0.050, 0.008, 0.010), 'ink')
    my, mz = g2w(rake, HAND['cy'], -0.096)
    mk = Kit(pal)
    mag_box(mk, rake, 0.080, -0.062, 0.040, 0.025, plate='gun3', plate_w=0.043, ribs=False)
    for s in (-1, 1):
        y, z = g2w(rake, 0.004, -0.030)
        mk.box((s * 0.0125, y, z), (0.008, 0.020, 0.036), 'gun3', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': rake, 'mag': (0, my, mz), 'muzzle': (0, 0.272, bz), 'eject': (0.03, 0.020, 0.046),
                   'sight': (0, -0.072, 0.0755), 'cls': 'smg', 'fore': (0.088, -0.006)}


def build_hornet(pal):
    """KV-7 Hornet: precision SMG, round tubular receiver, curved mag, tube red-dot, retractable stock."""
    rake = 16
    k = Kit(pal)
    bz = 0.040
    k.lathe([(-0.096, 0), (-0.096, 0.021), (-0.090, 0.025), (0.126, 0.025), (0.130, 0.021), (0.130, 0)], 'gunmetal', 'y', (0, 0, bz), 10, a0=18)
    k.ext_y(rrect(0.040, 0.034, c=0.004, cy=0.006), -0.080, 0.064, 'gun2', ch0=0.004, ch1=0.004)                     # trigger housing
    k.box((0.0190, 0.030, 0.050), (0.016, 0.050, 0.016), 'ink')                                                   # port
    rail(k, -0.070, 0.070, 0.0625, w=0.022, clear=[(-0.040, 0.020)])
    rz = red_dot(k, -0.010, 0.0625, L=0.056)
    stripe(k, 0.140, 0.212, 0.016, 0.022, 0.0285)
    # cocking tube above the handguard, handle out to the left
    k.lathe([(0.126, 0), (0.126, 0.0075), (0.236, 0.0075), (0.236, 0)], 'gun3', 'y', (0, 0, 0.066), 8, hull=False)
    k.bar((-0.004, 0.214, 0.066), (-0.034, 0.206, 0.072), 0.008, 0.008, 'ink')
    # handguard: wide rounded, vents
    k.ext_y(rrect(0.051, 0.044, ct=0.013, cb=0.010, cy=0.034), 0.124, 0.228, 'gun2', ch0=0.003, ch1=0.005)
    for s in (-1, 1):
        for i in range(3):
            k.box((s * 0.0255, 0.146 + i * 0.026, 0.040), (0.006, 0.016, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    barrel(k, 0.220, 0.258, 0.0085, bz)
    muzzle(k, 0.258, 0.292, 0.0120, bz, ports=1, top_ports=1, rb=0.0055, seg=8)
    k.box((0, 0.250, bz + 0.018), (0.006, 0.010, 0.012), 'ink', hull=True)
    k.ext_x([(0.060, 0.016), (0.104, 0.016), (0.104, -0.020), (0.098, -0.026), (0.062, -0.026), (0.058, -0.016)], -0.0235, 0.0235, 'gun2', ch=0.003)
    trigger_guard(k, rake, front=0.052, depth=-0.046, hook=False, top=-0.006)
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=-0.006, ptop=-0.030, grooves=2)
    k.xbar(-0.0235, -0.0200, [(-0.060, -0.002), (-0.040, -0.004), (-0.038, 0.004), (-0.058, 0.006)], 'gun3', ch=0, hull=False)
    # retractable stock: two rails, butt with cheek rest
    for s in (-1, 1):
        k.box((s * 0.015, -0.150, 0.036), (0.008, 0.130, 0.010), 'steel2', hull=True)
    k.ext_x([(-0.206, 0.060), (-0.224, 0.060), (-0.226, -0.030), (-0.208, -0.026)], -0.0225, 0.0225, 'furn', ch=0.003)
    k.box((0, -0.215, -0.024), (0.052, 0.010, 0.010), 'ink')
    k.box((0, -0.190, 0.058), (0.026, 0.040, 0.010), 'gun3')
    mk = Kit(pal)
    mag_box(mk, 0, 0.036, -0.120, 0.040, 0.024, curve=0.036, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.081, -0.026), 'muzzle': (0, 0.294, bz), 'eject': (0.03, 0.030, 0.050),
                   'sight': (0, -0.050, rz), 'cls': 'smg', 'guard': (0, 0.215, 0.034)}


def build_triplet(pal):
    """AR-3 Tribolt: bullpup burst rifle, integrated optic, full-hand guard, three-port brake, foregrip."""
    rake = 18
    k = Kit(pal)
    bz = 0.034
    # body side profile (grip forward, mag behind the grip, butt at the rear)
    body = [(0.122, 0.064), (-0.300, 0.064), (-0.318, 0.050), (-0.318, -0.070), (-0.290, -0.074), (-0.170, -0.058),
            (-0.140, -0.030), (-0.040, -0.030), (-0.020, -0.012), (0.122, -0.012)]
    k.ext_x(body, -0.025, 0.025, 'gunmetal', ch=0.005)
    k.ext_x([(-0.300, 0.058), (-0.326, 0.058), (-0.328, -0.072), (-0.302, -0.076)], -0.0285, 0.0285, 'ink', ch=0.003)   # butt pad
    stripe(k, -0.270, 0.100, 0.010, 0.016, 0.0280)
    for s in (-1, 1):                 # side panel line + screws
        k.box((s * 0.0255, -0.200, -0.040), (0.006, 0.110, 0.004), 'ink', skip=('-x' if s > 0 else '+x',))
        k.screw((s * 0.025, -0.250, 0.034), (s, 0, 0))
        k.screw((s * 0.025, -0.190, 0.034), (s, 0, 0))
    k.box((0.020, -0.120, 0.040), (0.0175, 0.060, 0.016), 'ink')                     # ejection port
    k.lathe([(-0.030, 0), (-0.030, 0.005), (0.000, 0.005), (0.000, 0)], 'gun3', 'y', (-0.028, 0, 0.050), 8, hull=False)   # charging slot
    k.cbox((-0.034, -0.010, 0.050), (0.012, 0.008, 0.012), 'ink', ch=0.002, hull=False)
    # integrated optic on a long mount
    k.ext_x([(-0.170, 0.062), (0.040, 0.062), (0.030, 0.078), (-0.160, 0.078)], -0.013, 0.013, 'gun3', ch=0.003)
    scope(k, -0.150, 0.052, 0.096, rt=0.012, ro=0.018, re=0.016, lo=0.030, le=0.028, seg=12)
    # handguard shroud + vents, barrel, three-port brake
    k.ext_y(rrect(0.046, 0.046, ct=0.010, cb=0.008, cy=0.031), 0.118, 0.300, 'gun2', ch1=0.006)
    for s in (-1, 1):
        for i in range(4):
            k.box((s * 0.0235, 0.140 + i * 0.038, 0.040), (0.006, 0.020, 0.008), 'ink', skip=('-x' if s > 0 else '+x',))
    barrel(k, 0.290, 0.396, 0.0090, bz)
    k.cbox((0, 0.420, bz), (0.030, 0.050, 0.026), 'steel', ch=0.004, axis='y')
    for i in range(3):
        k.box((0, 0.404 + i * 0.015, bz), (0.036, 0.006, 0.016), 'ink')
        k.box((0, 0.404 + i * 0.015, bz + 0.0125), (0.014, 0.006, 0.008), 'ink', skip=('-z',))
    muzzle(k, 0.438, 0.450, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # full-hand trigger guard, trigger, grip, foregrip
    hy, cy = HAND['hy'], HAND['cy']
    gb = g2w(rake, cy + hy + 0.022, -0.100)
    k.ext_x([(0.070, -0.010), (0.078, -0.024), (gb[0] + 0.004, gb[1]), (gb[0] - 0.010, gb[1] - 0.008),
             (gb[0] - 0.010, gb[1] + 0.002), (0.064, -0.024), (0.060, -0.010)], -0.006, 0.006, 'gun2')
    trigger(k, rake)
    grip(k, rake, 'smg', w=0.034, top=-0.010, ptop=-0.034)
    vgrip(k, 0.200, 0.008, length=0.070)
    mk = Kit(pal)
    mag_box(mk, 4, 0.030, -0.110, 0.050, 0.026, curve=0.030, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, -0.090, -0.030), 'muzzle': (0, 0.452, bz), 'eject': (0.03, -0.120, 0.040),
                   'sight': (0, -0.170, 0.096), 'cls': 'rifle', 'fore': (0.200, 0.008)}


def build_longtom(pal):
    """DMR-60 Longtom: semi-auto marksman rifle, 1.5x prism optic, long free-float guard, fixed precision stock."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    k.ext_y(rrect(0.048, 0.044, ct=0.006, cb=0.002, cy=0.034), -0.114, 0.140, 'gunmetal', ch0=0.004, ch1=0.003)   # upper
    k.box((0.01675, 0.050, 0.042), (0.0205, 0.058, 0.016), 'ink')
    k.box((0.0265, 0.052, 0.0255), (0.006, 0.050, 0.011), 'gun3')
    k.ext_y(rrect(0.041, 0.034, c=0.003, cy=-0.004), -0.106, 0.140, 'gun2', ch0=0.004, ch1=0.004)                  # lower
    k.ext_x([(0.074, 0.004), (0.138, 0.004), (0.140, -0.040), (0.134, -0.050), (0.072, -0.050), (0.070, -0.040)], -0.0235, 0.0235, 'gun2', ch=0.003)
    k.pin(-0.0265, 0.0265, 0.134, 0.000, 0.003)
    k.pin(-0.0235, 0.0235, -0.096, 0.000, 0.003)
    k.xbar(-0.0240, -0.0205, [(-0.050, -0.004), (-0.030, -0.006), (-0.028, 0.002), (-0.048, 0.004)], 'gun3', ch=0, hull=False)
    k.cbox((0, -0.120, 0.0535), (0.036, 0.012, 0.011), 'gun3', ch=0.002, axis='x')
    rail(k, -0.110, 0.136, 0.056, w=0.022, clear=[(-0.092, 0.066)])
    # 1.5x prism optic: trapezoid housing, recessed lenses in two bells, windage cap, fibre strip
    oz = 0.059
    k.ext_y([(-0.018, oz), (0.018, oz), (0.018, oz + 0.022), (0.012, oz + 0.036), (-0.012, oz + 0.036), (-0.018, oz + 0.022)], -0.060, 0.032, 'gunmetal', ch0=0.003, ch1=0.003)
    lz = oz + 0.020
    k.lathe([(0.052, 0), (0.052, 0.013), (0.060, 0.013), (0.060, 0.017), (0.032, 0.017), (0.032, 0)], 'gunmetal', 'y', (0, 0, lz), 10, bands=['lens', 'ink', None, None, None])
    k.lathe([(-0.078, 0), (-0.078, 0.010), (-0.086, 0.010), (-0.086, 0.014), (-0.060, 0.014), (-0.060, 0)], 'gunmetal', 'y', (0, 0, lz), 10, bands=['lens', 'ink', None, None, None])
    turret(k, (0.018, -0.014, oz + 0.016), 'x', r=0.008, h=0.006)
    k.cbox((0, -0.020, oz + 0.040), (0.010, 0.040, 0.008), 'gun3', ch=0.002, axis='y', hull=False)
    # long octagonal guard with slots, fluted barrel, compensator
    k.ext_y(rrect(0.048, 0.048, c=0.014, cy=bz), 0.138, 0.420, 'gun3', ch0=0.003, ch1=0.006)
    for s in (-1, 1):
        for i in range(6):
            k.box((s * 0.0240, 0.165 + i * 0.040, bz), (0.006, 0.024, 0.008), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.290, bz - 0.0145), (0.0540, 0.220, 0.006), 'trim')
    rail(k, 0.141, 0.250, 0.058, w=0.020, pitch=0.018)
    barrel(k, 0.410, 0.536, 0.0100, bz)
    for s in (-1, 1):
        k.box((s * 0.0105, 0.475, bz), (0.006, 0.100, 0.004), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.475, bz + 0.0105), (0.004, 0.100, 0.006), 'ink', skip=('-z',))
    muzzle(k, 0.536, 0.600, 0.0130, bz, ports=3, top_ports=2, rb=0.0060, seg=8)
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.008, ptop=-0.038, grooves=2)
    # fixed precision stock: cheek riser, butt pad, sling stud
    k.ext_x([(-0.110, 0.050), (-0.180, 0.050), (-0.330, 0.054), (-0.334, -0.060), (-0.300, -0.064), (-0.200, -0.016), (-0.110, -0.016)], -0.020, 0.020, 'furn', ch=0.005)
    k.ext_x([(-0.190, 0.049), (-0.300, 0.053), (-0.300, 0.064), (-0.196, 0.062)], -0.0155, 0.0155, 'gun3', ch=0.003)
    k.ext_x([(-0.330, 0.058), (-0.346, 0.058), (-0.348, -0.064), (-0.332, -0.066)], -0.0235, 0.0235, 'ink', ch=0.003)
    for s in (-1, 1):
        k.box((s * 0.0215, -0.260, -0.004), (0.006, 0.070, 0.004), 'ink', skip=('-x' if s > 0 else '+x',))
    k.ring('x', (0, -0.250, -0.046), -0.023, 0.023, 0.004, 0.0075, 'steel2', seg=8, hull=False)
    mk = Kit(pal)
    mag_box(mk, 4, 0.040, -0.084, 0.056, 0.028, plate='gun3')
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.105, -0.050), 'muzzle': (0, 0.602, bz), 'eject': (0.03, 0.050, 0.042),
                   'sight': (0, -0.100, lz), 'scope': (0, -0.086, lz), 'cls': 'rifle', 'guard': (0, 0.320, 0.034)}


def build_brick(pal):
    """LMG-26 Bricklayer: heavy LMG, feed cover, carry handle, perforated heat shield, folded bipod, brick ammo box."""
    rake = 20
    k = Kit(pal)
    bz = 0.044
    k.ext_y(rrect(0.058, 0.082, ct=0.010, cb=0.004, cy=0.040), -0.130, 0.155, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.ext_y(rrect(0.050, 0.012, ct=0.004, cb=0.0, cy=0.0855), -0.110, 0.130, 'gun3', ch0=0.004, ch1=0.004)       # feed cover
    k.pin(-0.028, 0.028, 0.124, 0.086, 0.004, color='steel2')
    k.ext_y(rrect(0.046, 0.030, c=0.003, cy=-0.006), -0.090, 0.090, 'gun2', ch0=0.004, ch1=0.004)                  # trigger housing
    k.cbox((0, -0.118, 0.090), (0.034, 0.010, 0.010), 'ink', ch=0.002, axis='x', hull=False)                       # cover latch
    for i in range(4):
        k.box((0, -0.080 + i * 0.044, 0.0935), (0.040, 0.010, 0.004), 'ink', skip=('-z',))
    k.ext_x([(-0.090, 0.090), (-0.070, 0.090), (-0.070, 0.112), (-0.078, 0.114), (-0.090, 0.100)], -0.012, 0.012, 'gunmetal')  # leaf sight
    k.box((0, -0.080, 0.111), (0.004, 0.012, 0.006), 'ink')
    stripe(k, -0.110, 0.100, 0.010, 0.017, 0.0320)
    for s in (-1, 1):
        k.screw((s * 0.029, -0.100, 0.060), (s, 0, 0))
    k.box((0.021, 0.020, 0.048), (0.022, 0.060, 0.018), 'ink')                                       # port
    k.cbox((0.036, -0.010, 0.030), (0.012, 0.014, 0.012), 'gun3', ch=0.002, hull=False)               # charging handle
    # barrel, heat shield with holes, gas tube, forend, carry handle, flash hider, front post
    barrel(k, 0.118, 0.466, 0.0120, bz, seg=12)
    hs = [(-0.022, bz - 0.002), (-0.020, bz + 0.012), (-0.010, bz + 0.022), (0.010, bz + 0.022), (0.020, bz + 0.012), (0.022, bz - 0.002),
          (0.017, bz - 0.002), (0.015, bz + 0.009), (0.007, bz + 0.016), (-0.007, bz + 0.016), (-0.015, bz + 0.009), (-0.017, bz - 0.002)]
    k.ext_y(hs, 0.180, 0.400, 'gun2', ch0=0.0, ch1=0.0)
    for i in range(5):
        k.box((0, 0.196 + i * 0.044, bz + 0.0235), (0.012, 0.014, 0.006), 'ink', skip=('-z',))
    k.lathe([(0.156, 0), (0.156, 0.008), (0.380, 0.008), (0.380, 0)], 'steel2', 'y', (0, 0, 0.012), 8, hull=True)    # gas tube
    k.ext_y(rrect(0.046, 0.034, ct=0.006, cb=0.010, cy=0.012), 0.152, 0.300, 'gun2', ch1=0.006)                      # forend
    for s in (-1, 1):
        for i in range(2):
            k.box((s * 0.0235, 0.180 + i * 0.056, 0.010), (0.006, 0.024, 0.006), 'ink', skip=('-x' if s > 0 else '+x',))
    k.tube([((0, 0.190, bz + 0.010), 0.012, 0.010), ((0, 0.200, bz + 0.052), 0.012, 0.010), ((0, 0.280, bz + 0.052), 0.012, 0.010),
            ((0, 0.290, bz + 0.010), 0.012, 0.010)], 'gun3', sides=6, up=(1, 0, 0))
    k.lathe([(0.466, 0), (0.466, 0.0140), (0.500, 0.0175), (0.512, 0.0175), (0.512, 0.0080), (0.500, 0.0080), (0.500, 0)], 'steel', 'y', (0, 0, bz), 12,
            bands=[None, None, None, None, 'ink', 'ink'])
    for i in range(4):
        a = D(45 + 90 * i)
        k.box((0.0185 * math.cos(a), 0.496, bz + 0.0185 * math.sin(a)), (0.006, 0.020, 0.006), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    k.box((0, 0.452, bz + 0.040), (0.006, 0.010, 0.056), 'ink', hull=True)       # tall front post, level with the leaf
    bipod_folded(k, 0.290, 0.440, 0.008, x=0.016)
    k.ring('y', (0, 0, bz), 0.420, 0.432, 0.010, 0.0165, 'steel2', seg=10, hull=False)
    trigger_guard(k, rake, front=0.056, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    # stock: solid with butt plate, buffer ridge
    k.ext_x([(-0.126, 0.072), (-0.320, 0.064), (-0.322, -0.046), (-0.296, -0.050), (-0.180, -0.004), (-0.126, 0.006)], -0.022, 0.022, 'furn', ch=0.005)
    k.ext_x([(-0.318, 0.070), (-0.336, 0.070), (-0.338, -0.050), (-0.320, -0.054)], -0.0265, 0.0265, 'ink', ch=0.003)
    k.box((0, -0.220, 0.040), (0.050, 0.120, 0.006), 'gun3')
    # brick ammo box (the Mag): ribs, lid, feed chute with rounds
    mk = Kit(pal)
    mk.cbox((0, 0, -0.050), (0.064, 0.090, 0.088), 'gun3', ch=0.005, axis='z')
    mk.cbox((0, 0, -0.098), (0.070, 0.096, 0.010), 'gun2', ch=0.003, axis='z')
    mk.box((0, 0, -0.003), (0.054, 0.076, 0.008), 'gun2')
    for s in (-1, 1):
        for j in range(2):
            mk.box((s * 0.0335, -0.018 + j * 0.036, -0.052), (0.006, 0.008, 0.070), 'gun2', skip=('-x' if s > 0 else '+x',))
        mk.box((s * 0.0360, 0, -0.010), (0.006, 0.030, 0.010), 'ink', skip=('-x' if s > 0 else '+x',))
    mk.cbox((-0.046, 0.0, 0.004), (0.020, 0.040, 0.034), 'gun2', ch=0.003, rot=(0, -25, 0))
    for i in range(2):
        mk.lathe([(-0.012, 0), (-0.012, 0.0055), (0.010, 0.0055), (0.018, 0.0030), (0.018, 0)], 'brass', 'y', (-0.020 + i * 0.010, 0.0, 0.009 + i * 0.002), 6, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.010), 'muzzle': (0, 0.514, bz), 'eject': (0.03, 0.020, 0.048),
                   'sight': (0, -0.095, 0.110), 'cls': 'rifle', 'guard': (0, 0.292, 0.012)}


def build_needle(pal):
    """SR-160 Needle: bolt-action sniper, chassis stock, long scope with turrets and lens rings, big brake."""
    rake = 22
    k = Kit(pal)
    bz = 0.032
    k.lathe([(-0.112, 0), (-0.112, 0.016), (-0.106, 0.020), (0.100, 0.020), (0.106, 0.016), (0.106, 0)], 'gunmetal', 'y', (0, 0, bz), 12, a0=0)   # action
    k.box((0.0175, 0.010, bz + 0.006), (0.010, 0.050, 0.014), 'ink')                       # port
    # bolt handle + knob (right side, rear)
    k.tube([((0.016, -0.074, bz + 0.004), 0.008, 0.008), ((0.034, -0.078, bz - 0.006), 0.007, 0.007), ((0.046, -0.082, bz - 0.020), 0.007, 0.007)], 'steel', sides=6, up=(0, 1, 0))
    k.lathe([(0.0, 0), (0.0, 0.006), (0.006, 0.010), (0.016, 0.010), (0.020, 0.005), (0.020, 0)], 'steel2', (V((0.5, -0.1, -0.86)).normalized(), V((0, 1, 0)), V((0.86, 0, 0.5))), (0.042, -0.081, bz - 0.014), 8)
    k.cbox((0, -0.120, bz), (0.026, 0.016, 0.026), 'gun3', ch=0.004, axis='y', hull=False)   # bolt shroud
    # chassis (lighter), forend with slots, amber stripe, folded bipod
    k.ext_x([(-0.100, 0.020), (0.320, 0.020), (0.330, 0.010), (0.330, -0.016), (0.120, -0.024), (0.080, -0.030), (-0.100, -0.030)], -0.0225, 0.0225, 'gun3', ch=0.004)
    for s in (-1, 1):
        for i in range(5):
            k.box((s * 0.0225, 0.150 + i * 0.034, 0.004), (0.006, 0.022, 0.012), 'ink', skip=('-x' if s > 0 else '+x',))
        k.screw((s * 0.0225, 0.060, 0.008), (s, 0, 0))
    k.box((0, 0.230, -0.010), (0.0510, 0.180, 0.005), 'trim')
    bipod_folded(k, 0.200, 0.320, -0.026, x=0.012)
    rail(k, -0.104, 0.098, bz + 0.0195, w=0.020, pitch=0.014, clear=[(-0.074, -0.054), (0.044, 0.064)])
    # barrel (taper) and two-chamber brake
    k.lathe([(0.100, 0), (0.100, 0.0110), (0.600, 0.0090), (0.600, 0)], 'steel', 'y', (0, 0, bz), 10)
    k.cbox((0, 0.634, bz), (0.034, 0.068, 0.026), 'steel2', ch=0.005, axis='y')
    for i in range(2):
        k.box((0, 0.616 + i * 0.030, bz), (0.040, 0.016, 0.016), 'ink')
    muzzle(k, 0.664, 0.672, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # scope with mounts, turrets, parallax knob
    sz = bz + 0.062
    scope(k, -0.150, 0.180, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    for yy in (-0.064, 0.054):
        k.cbox((0, yy, bz + 0.033), (0.024, 0.016, 0.022), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    turret(k, (-0.010, -0.010, sz), '-x', r=0.008, h=0.009, cap='gun3')
    trigger_guard(k, rake, front=0.068, depth=-0.054, w=0.012, top=-0.024, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.022, ptop=-0.040)
    # skeleton chassis stock: top bar with cheek riser, lower strut, butt pad, monopod
    k.cbox((0, -0.2045, 0.020), (0.020, 0.191, 0.020), 'gun3', ch=0.004, axis='y')
    k.cbox((0, -0.225, 0.040), (0.026, 0.090, 0.016), 'furn', ch=0.004, axis='y')
    k.bar((0, -0.100, -0.024), (0, -0.290, -0.056), 0.020, 0.016, 'gun3', hull=True)
    k.ext_x([(-0.296, 0.040), (-0.318, 0.040), (-0.320, -0.074), (-0.298, -0.074)], -0.0215, 0.0215, 'ink', ch=0.003)
    k.lathe([(-0.060, 0), (-0.060, 0.007), (0.0, 0.007), (0.0, 0)], 'steel2', 'z', (0, -0.262, -0.050), 8, hull=False)
    mk = Kit(pal)
    mag_box(mk, 4, 0.034, -0.040, 0.060, 0.026, plate='gun2', ribs=True, wt=0.62)
    return k, mk, {'rake': rake, 'mrake': 4, 'mag': (0, 0.050, -0.030), 'muzzle': (0, 0.674, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.165, sz), 'scope': (0, -0.150, sz), 'cls': 'sniper', 'guard': (0, 0.300, 0.000),
                   'bolt': (0.046, -0.082, bz - 0.020)}


# ================================================================ more guns (round 3): shotguns, battle rifle, rail rifle
def build_scrapper(pal):
    """SG-9 Scrapper: pump shotgun. Tube magazine under the barrel; the pump forend is the 'Mag' part (it slides on
    the tube when the gun is worked); shells go in through the loading port under the receiver."""
    rake = 20
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.046, 0.058, ct=0.010, cb=0.004, cy=0.036), -0.110, 0.120, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.box((0.0225, 0.020, 0.044), (0.008, 0.070, 0.022), 'ink', skip=('-x',))                                   # ejection port
    k.box((0.0, 0.052, 0.0045), (0.024, 0.080, 0.006), 'ink')                                                 # loading port
    k.box((0, 0.052, -0.0005), (0.016, 0.056, 0.006), 'red')                                                  # shell lifter
    stripe(k, -0.100, 0.100, 0.012, 0.019, 0.0265)
    k.ext_y(rrect(0.040, 0.020, c=0.003, cy=-0.004), -0.080, 0.002, 'gun2', ch0=0.004, ch1=0.004)            # trigger plate
    barrel(k, 0.118, 0.560, 0.0125, bz + 0.004, seg=12)
    k.lathe([(0.118, 0), (0.118, 0.0100), (0.500, 0.0100), (0.500, 0)], 'steel2', 'y', (0, 0, bz - 0.024), 10)    # magazine tube
    k.cbox((0, 0.506, bz - 0.012), (0.034, 0.016, 0.048), 'gunmetal', ch=0.004, axis='y')                     # tube cap / barrel clamp
    muzzle(k, 0.556, 0.574, 0.0162, bz + 0.004, rb=0.0095, seg=12)
    k.ext_y(rrect(0.010, 0.006, c=0.002, cy=bz + 0.019), 0.130, 0.546, 'ink')                                # vent rib
    k.cbox((0, 0.548, bz + 0.026), (0.006, 0.006, 0.008), 'red', ch=0.0015)                                   # bead sight
    sz = iron_rear(k, -0.070, 0.066, w=0.026, h=0.010)
    trigger_guard(k, rake, front=0.066, depth=-0.048, w=0.012, top=-0.010, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=-0.006, ptop=-0.036, grooves=2)
    k.pin(-0.0295, 0.0295, -0.060, 0.012, 0.003)
    k.pin(-0.0295, 0.0295, 0.090, 0.012, 0.003)
    # stock: wood-tone polymer with a recoil pad
    k.ext_x([(-0.106, 0.064), (-0.330, 0.050), (-0.332, -0.050), (-0.300, -0.056), (-0.160, -0.004), (-0.106, 0.010)], -0.021, 0.021, 'furn', ch=0.005)
    k.ext_x([(-0.328, 0.056), (-0.348, 0.056), (-0.350, -0.056), (-0.330, -0.060)], -0.025, 0.025, 'ink', ch=0.003)
    for i in range(3):
        k.box((0, -0.200 - i * 0.030, 0.0560 - i * 0.002), (0.050, 0.010, 0.006), 'gun3')
    # the pump (Mag part): ribbed forend round the tube, origin = its rear end on the tube axis
    mk = Kit(pal)
    mk.ext_y(rrect(0.046, 0.040, c=0.010, cy=0.002), 0.0, 0.130, 'gun2', ch0=0.006, ch1=0.006)
    for i in range(6):
        mk.box((0, 0.020 + i * 0.018, -0.0185), (0.050, 0.008, 0.006), 'ink')
    for s in (-1, 1):
        mk.box((s * 0.0235, 0.065, 0.006), (0.006, 0.090, 0.008), 'gun3', skip=('-x' if s > 0 else '+x',))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.300, bz - 0.024), 'muzzle': (0, 0.576, bz + 0.004), 'eject': (0.03, 0.020, 0.050),
                   'sight': (0, -0.070, sz), 'cls': 'shotgun', 'guard': (0, 0.365, bz - 0.022), 'port': (0, 0.052, -0.004)}   # pump: palm under the forend


def build_thunder(pal):
    """SG-12 Thunderclap: box-fed auto shotgun, square shroud, carry handle sight, big drum."""
    rake = 18
    k = Kit(pal)
    bz = 0.040
    k.ext_y(rrect(0.054, 0.072, ct=0.010, cb=0.004, cy=0.036), -0.120, 0.150, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.box((0.0265, 0.030, 0.048), (0.008, 0.060, 0.020), 'ink', skip=('-x',))
    k.ext_y(rrect(0.046, 0.026, c=0.003, cy=-0.002), -0.090, 0.140, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.070, 0.006), (0.140, 0.006), (0.142, -0.030), (0.134, -0.040), (0.070, -0.040), (0.066, -0.028)], -0.0265, 0.0265, 'gun2', ch=0.003)
    k.ext_y(rrect(0.058, 0.060, c=0.008, cy=bz), 0.148, 0.400, 'gun3', ch0=0.003, ch1=0.006)                    # square shroud
    for s in (-1, 1):
        for i in range(4):
            k.box((s * 0.0290, 0.180 + i * 0.052, bz + 0.004), (0.006, 0.030, 0.026), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.214, bz - 0.0305), (0.062, 0.100, 0.006), 'trim')
    barrel(k, 0.390, 0.450, 0.0140, bz, seg=12)
    k.lathe([(0.446, 0), (0.446, 0.0200), (0.488, 0.0200), (0.488, 0.0110), (0.478, 0.0110), (0.478, 0)], 'steel2', 'y', (0, 0, bz), 12)   # brake
    for i in range(4):
        a = D(45 + 90 * i)
        k.box((0.0205 * math.cos(a), 0.470, bz + 0.0205 * math.sin(a)), (0.006, 0.020, 0.008), 'ink', rot=(0, -math.degrees(a), 0), skip=('-x',))
    # carry handle with a peep sight
    k.tube([((0, -0.060, 0.072), 0.014, 0.010), ((0, -0.050, 0.098), 0.014, 0.010), ((0, 0.100, 0.098), 0.014, 0.010), ((0, 0.110, 0.072), 0.014, 0.010)],
           'gunmetal', sides=6, up=(1, 0, 0))
    k.ring('y', (0, 0, 0.112), -0.064, -0.054, 0.004, 0.009, 'ink', seg=8, hull=False)
    k.box((0, 0.380, bz + 0.046), (0.006, 0.010, 0.040), 'ink', hull=True)
    trigger_guard(k, rake, front=0.062, depth=-0.050, hook=False, top=-0.004)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.032)
    vgrip(k, 0.300, bz - 0.030, length=0.070, seg=8)
    k.ext_x([(-0.116, 0.074), (-0.300, 0.060), (-0.302, -0.048), (-0.276, -0.054), (-0.170, -0.004), (-0.116, 0.006)], -0.023, 0.023, 'gun2', ch=0.005)
    k.ext_x([(-0.298, 0.066), (-0.318, 0.066), (-0.320, -0.054), (-0.300, -0.058)], -0.027, 0.027, 'ink', ch=0.003)
    # drum magazine (Mag): round drum with a feed neck
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.012), (0.040, 0.050, 0.030), 'gun2', ch=0.004, axis='x')
    mk.lathe([(-0.034, 0), (-0.034, 0.060), (-0.026, 0.064), (0.026, 0.064), (0.034, 0.060), (0.034, 0)], 'gun3', 'x', (0, 0.010, -0.080), 14)
    mk.ring('x', (0, 0.010, -0.080), 0.034, 0.040, 0.018, 0.030, 'red', seg=12, hull=False)
    mk.ring('x', (0, 0.010, -0.080), -0.040, -0.034, 0.018, 0.030, 'red', seg=12, hull=False)
    for i in range(6):
        a = D(60 * i)
        mk.box((0, 0.010 + 0.0665 * math.cos(a), -0.080 + 0.0665 * math.sin(a)), (0.050, 0.006, 0.006), 'ink', rot=(-math.degrees(a), 0, 0))
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.105, -0.040), 'muzzle': (0, 0.490, bz), 'eject': (0.03, 0.030, 0.050),
                   'sight': (0, -0.090, 0.112), 'cls': 'shotgun', 'fore': (0.300, bz - 0.030)}


def build_vanguard(pal):
    """AR-40 Vanguard: heavy battle rifle, long free-float rail, red-dot over a tall riser, straight 20-round box."""
    rake = 20
    k = Kit(pal)
    bz = 0.036
    k.ext_y(rrect(0.050, 0.050, ct=0.006, cb=0.002, cy=0.036), -0.118, 0.150, 'gunmetal', ch0=0.004, ch1=0.003)
    k.box((0.0195, 0.052, 0.044), (0.020, 0.064, 0.018), 'ink')
    k.cbox((-0.032, 0.090, 0.046), (0.016, 0.012, 0.012), 'gun3', ch=0.002, hull=False)                    # side charging handle
    k.ext_y(rrect(0.044, 0.036, c=0.003, cy=-0.004), -0.110, 0.150, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.074, 0.004), (0.146, 0.004), (0.148, -0.044), (0.140, -0.054), (0.072, -0.054), (0.070, -0.040)], -0.025, 0.025, 'gun2', ch=0.003)
    rail(k, -0.112, 0.146, 0.0625, w=0.022, pitch=0.016, clear=[(-0.060, -0.020)])
    k.ext_y(rrect(0.052, 0.054, c=0.006, cy=bz), 0.146, 0.420, 'gun3', ch0=0.003, ch1=0.006)                 # rail handguard
    for s in (-1, 1):
        for i in range(6):
            k.box((s * 0.0260, 0.170 + i * 0.040, bz), (0.006, 0.026, 0.014), 'ink', skip=('-x' if s > 0 else '+x',))
    k.box((0, 0.280, bz - 0.0285), (0.056, 0.240, 0.006), 'red')
    rail(k, 0.150, 0.412, bz + 0.0285, w=0.020, pitch=0.018, clear=[(0.380, 0.396)])
    barrel(k, 0.410, 0.520, 0.0100, bz)
    k.cbox((0, 0.540, bz), (0.030, 0.048, 0.030), 'steel2', ch=0.005, axis='y')                              # brake
    for i in range(2):
        k.box((0, 0.530 + i * 0.020, bz), (0.036, 0.010, 0.014), 'ink')
    muzzle(k, 0.566, 0.578, 0.0080, bz, hull=False, rb=0.0050, seg=8)
    # red dot on a tall riser
    k.cbox((0, -0.040, 0.074), (0.026, 0.040, 0.020), 'gunmetal', ch=0.003, axis='y')
    sz = red_dot(k, -0.040, 0.094, L=0.056, r=0.018)
    iron_front(k, 0.392, bz + 0.056, post=0.016)
    trigger_guard(k, rake, front=0.068, depth=-0.052, w=0.012, top=-0.012, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.034, top=-0.008, ptop=-0.038, grooves=2)
    k.lathe([(-0.116, 0), (-0.116, 0.015), (-0.260, 0.015), (-0.264, 0.011), (-0.264, 0)], 'steel2', 'y', (0, 0, 0.030), 8)
    k.ext_x([(-0.170, 0.056), (-0.300, 0.058), (-0.304, -0.046), (-0.282, -0.052), (-0.240, -0.014), (-0.180, 0.012)], -0.020, 0.020, 'furn', ch=0.004)
    k.ext_x([(-0.300, 0.062), (-0.316, 0.062), (-0.318, -0.050), (-0.302, -0.054)], -0.024, 0.024, 'ink')
    k.cbox((0, -0.236, 0.066), (0.030, 0.080, 0.014), 'gun3', ch=0.003, axis='y')                         # cheek riser
    mk = Kit(pal)
    mag_box(mk, 2, 0.052, -0.110, 0.058, 0.028, curve=0.010)
    return k, mk, {'rake': rake, 'mrake': 2, 'mag': (0, 0.110, -0.054), 'muzzle': (0, 0.580, bz), 'eject': (0.03, 0.052, 0.044),
                   'sight': (0, -0.040, sz), 'cls': 'rifle', 'guard': (0, 0.330, bz)}


def build_railspike(pal):
    """SR-9 Railspike: semi-auto rail rifle. Twin copper rails in an open frame, glowing coil rings, a battery
    magazine, long scope."""
    rake = 22
    k = Kit(pal)
    bz = 0.034
    k.ext_y(rrect(0.052, 0.060, ct=0.010, cb=0.004, cy=0.030), -0.120, 0.140, 'gunmetal', ch0=0.005, ch1=0.004)   # receiver
    k.ext_y(rrect(0.044, 0.024, c=0.003, cy=-0.004), -0.100, 0.130, 'gun2', ch0=0.004, ch1=0.004)
    k.ext_x([(0.060, 0.002), (0.130, 0.002), (0.132, -0.034), (0.124, -0.044), (0.060, -0.044), (0.056, -0.032)], -0.0255, 0.0255, 'gun2', ch=0.003)
    # open rail frame: two rails (top / bottom) with coil rings between, an ink core
    for zz in (bz + 0.020, bz - 0.020):
        k.cbox((0, 0.392, zz), (0.020, 0.496, 0.012), 'trim', ch=0.003, axis='y')
    k.lathe([(0.140, 0), (0.140, 0.0060), (0.640, 0.0060), (0.640, 0)], 'ink', 'y', (0, 0, bz), 8, hull=False)
    for i in range(5):
        y = 0.180 + i * 0.090
        k.ring('y', (0, 0, bz), y, y + 0.022, 0.024, 0.034, 'gun3', seg=12)
        k.ring('y', (0, 0, bz), y + 0.004, y + 0.018, 0.0335, 0.0375, 'lens', seg=12, hull=False)
    k.cbox((0, 0.640, bz), (0.040, 0.020, 0.064), 'gunmetal', ch=0.005, axis='y')                         # muzzle block
    k.box((0, 0.6515, bz), (0.012, 0.006, 0.012), 'lens')
    stripe(k, -0.100, 0.120, 0.010, 0.016, 0.0290)
    for s in (-1, 1):
        k.screw((s * 0.026, -0.090, 0.050), (s, 0, 0))
    sz = bz + 0.066
    scope(k, -0.160, 0.170, sz, rt=0.0125, ro=0.024, re=0.019, lo=0.055, le=0.048, seg=12)
    for yy in (-0.064, 0.060):
        k.cbox((0, yy, bz + 0.0375), (0.024, 0.016, 0.022), 'gunmetal', ch=0.002, axis='y')
        k.ring('y', (0, 0, sz), yy - 0.007, yy + 0.007, 0.011, 0.0165, 'gunmetal', seg=10, hull=False)
    turret(k, (0, -0.004, sz + 0.010), 'z', r=0.010, h=0.016)
    turret(k, (0.010, -0.004, sz), 'x', r=0.009, h=0.012)
    trigger_guard(k, rake, front=0.066, depth=-0.052, w=0.012, top=-0.016, hook=False)
    trigger(k, rake)
    grip(k, rake, 'ar', w=0.033, top=-0.016, ptop=-0.040)
    k.cbox((0, -0.205, 0.024), (0.022, 0.180, 0.022), 'gun3', ch=0.004, axis='y')
    k.bar((0, -0.110, -0.022), (0, -0.290, -0.052), 0.020, 0.016, 'gun3', hull=True)
    k.ext_x([(-0.290, 0.044), (-0.312, 0.044), (-0.314, -0.072), (-0.292, -0.072)], -0.022, 0.022, 'ink', ch=0.003)
    k.cbox((0, -0.226, 0.044), (0.026, 0.090, 0.016), 'furn', ch=0.004, axis='y')
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.036), (0.030, 0.056, 0.072), 'gun2', ch=0.004, axis='x')                            # battery pack
    mk.box((0, 0.0, -0.036), (0.037, 0.030, 0.040), 'lens')
    mk.cbox((0, 0.0, -0.076), (0.036, 0.062, 0.010), 'gun3', ch=0.003, axis='z')
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.096, -0.044), 'muzzle': (0, 0.656, bz), 'eject': (0.03, 0.010, 0.040),
                   'sight': (0, -0.175, sz), 'scope': (0, -0.160, sz), 'cls': 'sniper', 'guard': (0, 0.300, bz - 0.020)}


# ================================================================ launchers (round 5): no mods fit them (src/data/weapons.js noMods)
def launcher_frame(k, rake, fore_y, fore_top):
    """Shared lower: frame block under the tube / housing, AR grip, guard, trigger, a vertical foregrip on a lug."""
    k.cbox((0, 0.040, 0.012), (0.040, 0.190, 0.044), 'gun2', ch=0.004, axis='y')                     # frame, z -0.010..0.034
    trigger_guard(k, rake, front=0.066, depth=-0.052, w=0.012, top=-0.004, hook=False)
    trigger(k, rake, ext=0.006)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.036, grooves=2)
    k.cbox((0, fore_y, fore_top + 0.003), (0.040, 0.044, 0.014), 'gun2', ch=0.003, axis='y')         # foregrip lug
    vgrip(k, fore_y, fore_top, length=0.074, r=0.016, seg=8)


def build_hothead(pal):
    """RL-3 Hothead: a fat comic rocket tube on a pistol-grip frame. Flared red muzzle bell, venturi exhaust, hazard
    rings, flip-up ring sights, a caged element canister on the left (the game lights its core in the element's
    colour at the ELEM socket) and a 3-rocket cassette (the Mag) under the tube."""
    rake = 18
    k = Kit(pal)
    bz, R = 0.074, 0.046
    k.lathe([(-0.262, 0), (-0.262, R - 0.006), (-0.254, R), (0.296, R), (0.296, 0)], 'gun3', 'y', (0, 0, bz), 16)        # tube
    k.lathe([(-0.240, 0), (-0.240, 0.034), (-0.300, 0.040), (-0.336, 0.054), (-0.344, 0.054), (-0.344, 0.045), (-0.304, 0.030), (-0.304, 0)],
            'gunmetal', 'y', (0, 0, bz), 14, bands=[None, None, None, None, 'ink', 'ink', 'ink'])                            # venturi
    k.lathe([(0.286, 0), (0.286, 0.051), (0.326, 0.055), (0.366, 0.063), (0.378, 0.063), (0.378, 0.051), (0.334, 0.040), (0.334, 0)],
            'red', 'y', (0, 0, bz), 16, bands=[None, None, None, None, 'ink', 'ink', 'ink'])                                 # muzzle bell
    for y in (0.196, 0.226, -0.214):
        k.ring('y', (0, 0, bz), y, y + 0.016, R - 0.010, R + 0.0045, 'trim', seg=16, hull=False)
    k.ring('y', (0, 0, bz), 0.150, 0.162, R - 0.010, R + 0.0040, 'ink', seg=16, hull=False)
    # caged element canister (left side): dark core, three bars, two end caps; ELEM socket at its centre
    cx, cz = -(R + 0.010), bz - 0.004
    k.lathe([(-0.082, 0), (-0.082, 0.023), (-0.066, 0.023), (-0.066, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(0.066, 0), (0.066, 0.023), (0.082, 0.023), (0.082, 0)], 'gunmetal', 'y', (cx, 0, cz), 10)
    k.lathe([(-0.068, 0), (-0.068, 0.008), (0.068, 0.008), (0.068, 0)], 'ink', 'y', (cx, 0, cz), 8, hull=False)
    for a in (100, 180, 260):
        aa = D(a)
        k.cbox((cx + 0.0168 * math.cos(aa), 0.0, cz + 0.0168 * math.sin(aa)), (0.004, 0.134, 0.004), 'steel2', ch=0, hull=True)
    k.cbox((cx + 0.010, 0.0, cz), (0.014, 0.120, 0.014), 'gunmetal', ch=0.002, axis='y', hull=False)                    # saddle onto the tube
    # sights: rear aperture, front ring on posts
    zs = bz + R + 0.028
    k.cbox((0, -0.150, 0.12825), (0.022, 0.032, 0.0245), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.156, -0.148, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.cbox((0, 0.120, 0.1278), (0.012, 0.018, 0.0235), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.116, 0.124, 0.0120, 0.0165, 'trim', seg=12, hull=True)
    # arming lever (rear left) and a shoulder pad under the rear of the tube
    k.cbox((-0.034, -0.110, bz - 0.040), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    k.cbox((0, -0.190, 0.025), (0.034, 0.090, 0.020), 'gun2', ch=0.005, axis='y')
    launcher_frame(k, rake, 0.205, 0.024)
    stripe(k, -0.020, 0.090, 0.012, 0.018, 0.023)
    # 3-rocket cassette: box with three red warheads peeking out of its nose
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.026), (0.046, 0.074, 0.070), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.022), (0.052, 0.056, 0.012), 'trim')
    mk.cbox((0, 0.0, -0.064), (0.052, 0.082, 0.010), 'gun3', ch=0.003, axis='z')
    for i in (-1, 0, 1):
        mk.lathe([(0.030, 0), (0.030, 0.0062), (0.044, 0.0058), (0.052, 0)], 'red', 'y', (i * 0.0140, 0, -0.044), 8, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.384, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.165, zs), 'elem': (cx, 0.0, cz), 'cls': 'rocket', 'fore': (0.205, 0.024)}


def build_murmur(pal):
    """ML-6 Murmur: a shoulder-fired six-pack homing launcher. Two rows of three launch tubes bundled by steel straps,
    red warhead noses poking out of the front rims, flared venturis at the back (rear blast venting), a lock-on
    targeting unit with a seeker lens and whip antenna up top-left, ring sights on the centre line, the Hothead's
    pistol-grip frame + foregrip, and a missile cassette (the Mag) under the bundle with its warheads showing."""
    rake = 18
    k = Kit(pal)
    bz, R, dx, dz = 0.076, 0.018, 0.042, 0.021
    tubes = [(x, bz + z) for z in (-dz, dz) for x in (-dx, 0.0, dx)]
    for x, z in tubes:
        k.lathe([(-0.150, 0), (-0.150, R), (0.252, R), (0.256, R + 0.0028), (0.274, R + 0.0028), (0.274, 0.0150),
                 (0.262, 0.0150), (0.262, 0)], 'gun3', 'y', (x, 0, z), 6,
                bands=[None, None, 'gunmetal', 'gunmetal', 'gunmetal', 'ink', 'ink'])                                  # tube + front rim
        k.lathe([(0.250, 0.0140), (0.280, 0.0128), (0.300, 0)], 'red', 'y', (x, 0, z), 6, hull=False)       # warhead nose
        k.lathe([(-0.140, 0.0150), (-0.176, R + 0.0028), (-0.176, 0.0110), (-0.160, 0)],
                'steel2', 'y', (x, 0, z), 6, bands=[None, None, 'ink'], hull=False)                              # venturi
    for y, w in ((0.230, 0.020), (-0.132, 0.020)):                                                             # bundle straps
        k.cbox((0, y, bz), (2 * (dx + R) + 0.012, w, 2 * (dz + R) + 0.012), 'gunmetal', ch=0.004, axis='y')
    for y in (0.176, -0.090):                                                                                                  # hazard bands
        k.box((0, y, bz), (2 * (dx + R) + 0.006, 0.012, 2 * (dz + R) + 0.006), 'trim')
    k.cbox((0, 0.040, 0.034), (0.100, 0.300, 0.012), 'gun2', ch=0.003, axis='y')                                              # saddle onto the frame
    # lock-on targeting unit (top left): housing on a mount, seeker lens + ring, lock LED, whip antenna
    tx, ty, tz = -0.054, 0.080, 0.140
    k.cbox((tx + 0.006, ty, 0.118), (0.020, 0.050, 0.012), 'gun2', ch=0.002, axis='y')
    k.cbox((tx, ty, tz), (0.034, 0.096, 0.036), 'gun2', ch=0.004, axis='y')
    k.ring('y', (tx, 0, tz), ty + 0.046, ty + 0.058, 0.0100, 0.0150, 'gunmetal', seg=6)
    k.lathe([(ty + 0.046, 0), (ty + 0.046, 0.0102), (ty + 0.052, 0.0080), (ty + 0.055, 0)], 'lens', 'y', (tx, 0, tz), 6, hull=False)
    k.box((tx - 0.0185, ty - 0.010, tz + 0.006), (0.004, 0.030, 0.008), 'trim')
    k.cbox((tx + 0.004, ty - 0.020, tz + 0.020), (0.010, 0.010, 0.008), 'red', ch=0.002)
    k.bar((tx - 0.008, ty - 0.040, tz + 0.016), (tx - 0.008, ty - 0.040, tz + 0.062), 0.004, 0.004, 'ink', hull=False)
    # sights on the centre line (rear aperture, front ring)
    zs = 0.120 + 0.024
    k.cbox((0, -0.120, 0.12575), (0.022, 0.028, 0.0235), 'gunmetal', ch=0.003, axis='y')
    k.ring('y', (0, 0, zs), -0.126, -0.118, 0.0040, 0.0085, 'gunmetal', seg=8, hull=True)
    k.cbox((0, 0.240, 0.12625), (0.012, 0.016, 0.0205), 'gunmetal', ch=0.002, axis='y')
    k.ring('y', (0, 0, zs), 0.236, 0.244, 0.0110, 0.0155, 'trim', seg=12, hull=True)
    # arming lever (rear left, under the bundle) and a shoulder pad
    k.cbox((-0.034, -0.110, 0.030), (0.012, 0.036, 0.012), 'gun3', ch=0.002, axis='y')
    k.cbox((0, -0.190, 0.025), (0.034, 0.090, 0.020), 'gun2', ch=0.005, axis='y')
    launcher_frame(k, rake, 0.200, 0.026)
    stripe(k, -0.020, 0.090, 0.012, 0.018, 0.023)
    # missile cassette: a flat box with an amber label band, three warheads peeking out of its nose
    mk = Kit(pal)
    mk.cbox((0, 0.0, -0.022), (0.050, 0.080, 0.064), 'gun2', ch=0.004, axis='x')
    mk.box((0, 0.0, -0.024), (0.056, 0.060, 0.014), 'trim')
    for i in (-1, 1):
        mk.box((0, i * 0.018, -0.024), (0.062, 0.006, 0.020), 'ink')
    mk.cbox((0, 0.0, -0.058), (0.056, 0.086, 0.010), 'gun3', ch=0.003, axis='z')
    for i in (-1, 0, 1):
        mk.lathe([(0.034, 0), (0.034, 0.0062), (0.054, 0)], 'red', 'y', (i * 0.0150, 0, -0.042), 6, hull=False)
    return k, mk, {'rake': rake, 'mrake': 0, 'mag': (0, 0.110, -0.010), 'muzzle': (0, 0.300, bz), 'eject': (-0.03, -0.10, bz),
                   'sight': (0, -0.135, zs), 'cls': 'rocket', 'fore': (0.200, 0.026)}


# ================================================================ melee (round 3): struck with V; the gun is put away for the swing
# Weapon space for a melee weapon: the handle runs along the grip axis (+Z up), the hand's web at the origin (top of the
# handle, under the guard), the edge faces +Y. rake 0, so the hand frame IS the weapon frame. Two-handed weapons
# (katana, axe) carry a 'hold2' z: the support hand grips the handle that far below the right hand. The nunchucks'
# second stick is the weapon's 'Mag' part, hanging from the chain end (MAG socket) so the Mag bone can swing it.
def blade(k, st, color, edge='steel'):
    """Blade along +Z from stations (z, y_back, y_edge, half_thick, y_bevel): a flat body (spine at the back, flat
    faces to the bevel line) and a separate edge wedge (bevel line to the sharp edge, toward +Y) in its own colour.
    The last station may have y_back == y_edge: the tip apex."""
    body, wedge = [], []
    for z, yb, ye, t, ys in st:
        if abs(ye - yb) < 1e-6:
            body.append([(0.0, ye, z)])
            wedge.append([(0.0, ye, z)])
            continue
        body.append([(t, ys, z), (t, yb + 0.6 * t, z), (0.6 * t, yb, z), (-0.6 * t, yb, z), (-t, yb + 0.6 * t, z), (-t, ys, z)])
        wedge.append([(0.0, ye, z), (t, ys, z), (-t, ys, z)])
    k.loft(body, color, hull=True)
    k.loft(wedge, edge, hull=True)


def wrap_handle(k, z0, z1, rx, ry, color='ink', diamond='paper', n=6):
    """Wrapped handle: oval core, diamond peeks of the under-layer on the edge sides (y), ink binding."""
    k.lathe([(z0, 0), (z0, 1.0), (z1, 1.0), (z1, 0)], color, 'z', (0, 0, 0), 10, sc=(rx, ry))
    step = (z1 - z0) / n
    for i in range(n):
        z = z0 + step * (i + 0.5)
        for s in (-1, 1):
            k.box((0, s * (ry + 0.0010), z), (rx * 0.9, 0.006, step * 0.42), diamond, rot=(0, 45, 0), skip=('-y' if s > 0 else '+y',))


def build_katana(pal):
    """Mk-1 Ronin Blade: katana. Ink-wrapped two-hand handle, round steel guard, brass collar, curved blade with a
    pale temper line along the edge."""
    k = Kit(pal)
    wrap_handle(k, -0.215, 0.010, 0.015, 0.0195, 'ink', 'sleeve', n=7)
    k.lathe([(-0.235, 0), (-0.235, 0.0120), (-0.228, 0.0170), (-0.215, 0.0170), (-0.215, 0)], 'steel2', 'z', (0, 0, 0), 10, sc=(1.0, 1.25))   # end cap
    k.lathe([(0.010, 0), (0.010, 0.0360), (0.022, 0.0360), (0.022, 0)], 'gunmetal', 'z', (0, 0, 0), 16, sc=(0.85, 1.15))      # guard
    k.lathe([(0.022, 0), (0.022, 0.0260), (0.026, 0.0240), (0.026, 0)], 'amber', 'z', (0, 0, 0), 16, hull=False, sc=(0.85, 1.15))   # seppa washer
    k.cbox((0, 0.0, 0.038), (0.016, 0.036, 0.022), 'brass', ch=0.002)                                         # collar
    st = []
    n = 9
    for i in range(n):
        t = i / (n - 1)
        z = 0.046 + 0.600 * t
        sori = -0.030 * t * t                                       # the blade curves back toward the tip
        w = 0.030 - 0.006 * t
        st.append((z, -0.014 + sori, -0.014 + sori + w, 0.0040 - 0.0012 * t, -0.014 + sori + w * 0.62))
    st.append((0.690, -0.050, -0.050, 0, 0))
    blade(k, st, 'steel', 'paper')
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.30), 'muzzle': (0, -0.050, 0.690), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'hold2': -0.098, 'len': 0.69}


def build_eaxe(pal):
    """VX-7 Voltaxe: electric axe. Long steel shaft with a rubber grip, a heavy head with a battery and teal coils, a
    back spike, glowing edge."""
    k = Kit(pal)
    k.lathe([(-0.300, 0), (-0.300, 0.0150), (0.300, 0.0150), (0.300, 0)], 'steel2', 'z', (0, 0, 0), 10, sc=(1.0, 1.2))     # shaft
    for z0, z1 in ((-0.290, -0.110), (-0.080, 0.016)):
        k.lathe([(z0, 0), (z0, 0.0178), (z1, 0.0178), (z1, 0)], 'gun2', 'z', (0, 0, 0), 10, sc=(1.0, 1.2))                    # rubber grips
        for z in [z0 + 0.012 + j * 0.022 for j in range(int((z1 - z0 - 0.012) / 0.022))]:
            k.ring('z', (0, 0, 0), z, z + 0.006, 0.0172, 0.0210, 'gun3', seg=10, hull=False)
    k.lathe([(-0.316, 0), (-0.316, 0.0200), (-0.300, 0.0220), (-0.292, 0.0160), (-0.292, 0)], 'gunmetal', 'z', (0, 0, 0), 10)  # pommel
    # head (z 0.20 .. 0.32): core block, battery on the back, axe blade forward with a glowing edge, back spike
    k.cbox((0, 0.000, 0.262), (0.044, 0.056, 0.090), 'gunmetal', ch=0.006)
    k.cbox((0, -0.040, 0.262), (0.036, 0.030, 0.060), 'gun3', ch=0.004)
    k.box((0, -0.0565, 0.262), (0.024, 0.006, 0.036), 'lens')
    k.ext_x([(0.026, 0.226), (0.090, 0.180), (0.120, 0.196), (0.130, 0.262), (0.120, 0.330), (0.090, 0.346), (0.026, 0.298)], -0.006, 0.006, 'steel', ch=0.002)
    k.ext_x([(0.116, 0.198), (0.126, 0.192), (0.137, 0.262), (0.126, 0.332), (0.116, 0.326), (0.125, 0.262)], -0.0095, 0.0095, 'lens', hull=False)  # glowing edge
    k.ext_x([(-0.020, 0.248), (-0.090, 0.262), (-0.020, 0.278)], -0.008, 0.008, 'steel2', ch=0.002)   # back spike (through the battery)
    for z in (0.236, 0.262, 0.288):
        k.ring('y', (0, 0, z), 0.031, 0.048, 0.009, 0.0135, 'lens', seg=8, hull=False)                   # coils on the neck
    k.lathe([(0.300, 0), (0.300, 0.012), (0.318, 0.008), (0.326, 0)], 'amber', 'z', (0, 0, 0), 8)
    for s in (-1, 1):
        k.box((s * 0.0255, 0.0, 0.262), (0.006, 0.030, 0.050), 'amber', skip=('-x' if s > 0 else '+x',))   # warning plates
        k.box((s * 0.0255, 0.0, 0.262), (0.013, 0.010, 0.010), 'ink', skip=('-x' if s > 0 else '+x',))
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.40), 'muzzle': (0, 0.130, 0.262), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'hold2': -0.200, 'len': 0.33}


def build_dagger(pal):
    """KN-3 Stinger: combat dagger. Ribbed grip, cross guard, a dark clip-point blade with a bright edge."""
    k = Kit(pal)
    k.lathe([(-0.100, 0), (-0.100, 0.0150), (-0.090, 0.0175), (0.006, 0.0175), (0.006, 0)], 'gun2', 'z', (0, 0, 0), 10, sc=(1.0, 1.25))
    for i in range(4):
        z = -0.078 + i * 0.022
        k.ring('z', (0, 0, 0), z, z + 0.007, 0.0170, 0.0205, 'gun3', seg=10, hull=False)
    k.lathe([(-0.112, 0), (-0.112, 0.012), (-0.100, 0.016), (-0.100, 0)], 'steel2', 'z', (0, 0, 0), 8)          # pommel
    k.cbox((0, 0.0, 0.013), (0.020, 0.090, 0.012), 'gunmetal', ch=0.003)                                      # cross guard
    k.box((0, 0.0, 0.013), (0.027, 0.012, 0.006), 'amber')
    st = []
    n = 5
    for i in range(n):
        t = i / (n - 1)
        z = 0.020 + 0.150 * t
        st.append((z, -0.016 + 0.004 * t, 0.018 - 0.006 * t * t, 0.0042 - 0.0012 * t, 0.006 - 0.004 * t))
    st.append((0.205, -0.004, -0.004, 0, 0))
    blade(k, st, 'gun3', 'steel')
    return k, None, {'rake': 0, 'mrake': 0, 'mag': (0, 0, -0.30), 'muzzle': (0, -0.004, 0.205), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                     'cls': 'melee', 'len': 0.205}


def stick(k, z0, z1, color):
    """Nunchuck stick along Z: octagonal hardwood with ink end bands and an amber grip wrap."""
    k.lathe([(z0, 0), (z0, 0.0145), (z1, 0.0145), (z1, 0)], color, 'z', (0, 0, 0), 8)
    for z in (z0 + 0.004, z1 - 0.012):
        k.ring('z', (0, 0, 0), z, z + 0.008, 0.0090, 0.0180, 'ink', seg=8, hull=False)
    for i in range(3):
        z = z0 + 0.050 + i * 0.030
        k.ring('z', (0, 0, 0), z, z + 0.012, 0.0090, 0.0176, 'amber', seg=8, hull=False)


def build_nunchucks(pal):
    """NC-2 Twin Strikers: nunchucks. The held stick (top cap and swivel at the hand's web side), a short chain; the
    second stick (the 'Mag' part) hangs from the chain's far end, which is its origin."""
    k = Kit(pal)
    stick(k, -0.205, 0.075, 'amber')
    k.lathe([(0.075, 0), (0.075, 0.0120), (0.088, 0.0060), (0.094, 0)], 'steel', 'z', (0, 0, 0), 8)          # swivel cap
    for i in range(2):                                                                                       # chain links (held half)
        z = 0.104 + i * 0.020
        k.ring('x' if i % 2 else 'y', (0, 0, z), -0.003, 0.003, 0.004, 0.0090, 'steel2', seg=6, hull=True)
    mk = Kit(pal)
    for i in range(2):                                                                                       # chain links (far half)
        z = -0.010 - i * 0.020
        mk.ring('y' if i % 2 else 'x', (0, 0, z), -0.003, 0.003, 0.004, 0.0090, 'steel2', seg=6, hull=True)
    mk.lathe([(-0.060, 0), (-0.060, 0.0060), (-0.054, 0.0120), (-0.046, 0)], 'steel', 'z', (0, 0, 0), 8)
    with mk.at((0, 0, -0.046)):
        stick(mk, -0.280, 0.0, 'amber')
    return k, mk, {'rake': 0, 'mrake': 0, 'mag': (0.042, 0, 0.150), 'muzzle': (0, 0, -0.33), 'eject': (0, 0, 0), 'sight': (0, 0, 0),
                   'cls': 'melee', 'len': 0.33}


def build_held(pal):
    """Things the support hand holds (ride the HOLD_L socket on the left hand bone): the frag can and a shotgun shell."""
    k = Kit(pal)                                                    # M-15 Frag Can: tin can grenade, red band, lever, pin ring
    k.lathe([(-0.044, 0), (-0.044, 0.028), (-0.040, 0.032), (0.036, 0.032), (0.040, 0.028), (0.040, 0)], 'gun3', 'z', (0, 0, 0), 12)
    k.ring('z', (0, 0, 0), -0.012, 0.012, 0.030, 0.0350, 'red', seg=12, hull=False)
    k.lathe([(0.040, 0), (0.040, 0.014), (0.054, 0.012), (0.058, 0)], 'gunmetal', 'z', (0, 0, 0), 10)        # fuse head
    k.bar((0.0, 0.010, 0.050), (0.0, 0.036, -0.020), 0.010, 0.004, 'steel2', up=(1, 0, 0))                   # spoon lever
    k.ring('x', (0.012, -0.010, 0.054), -0.0015, 0.0015, 0.007, 0.0105, 'amber', seg=8, hull=False)          # pin ring
    for z in (-0.036, 0.018):
        k.ring('z', (0, 0, 0), z, z + 0.004, 0.0315, 0.0350, 'ink', seg=12, hull=False)
    finish('HELD_Frag', k)
    s = Kit(pal)                                                    # 12-gauge shell: red hull, brass head
    s.lathe([(-0.036, 0), (-0.036, 0.0110), (-0.032, 0.0110), (-0.032, 0.0098), (0.034, 0.0098), (0.036, 0.0080), (0.036, 0)], 'red', 'z', (0, 0, 0), 10,
            bands=[None, 'brass', 'brass', None, None, None])
    s.ring('z', (0, 0, 0), -0.030, -0.018, 0.0050, 0.0128, 'brass', seg=10, hull=False)
    finish('HELD_Shell', s)


GUNS = {'PIP': build_pip, 'HANDCANNON': build_handcannon, 'TWINTAP': build_twintap, 'BUZZ': build_buzz, 'WHISK': build_whisk,
        'HORNET': build_hornet, 'RIVET': build_rivet, 'TRIPLET': build_triplet, 'LONGTOM': build_longtom, 'BRICK': build_brick,
        'NEEDLE': build_needle, 'SCRAPPER': build_scrapper, 'THUNDER': build_thunder, 'VANGUARD': build_vanguard,
        'RAILSPIKE': build_railspike, 'HOTHEAD': build_hothead, 'MURMUR': build_murmur, 'KATANA': build_katana, 'EAXE': build_eaxe, 'DAGGER': build_dagger, 'NUNCHUCKS': build_nunchucks}
MELEE = [w for w in ('KATANA', 'EAXE', 'DAGGER', 'NUNCHUCKS')]


def build_weapon_meshes(pal):
    for wid, fn in GUNS.items():
        k, mk, info = fn(pal)
        try:
            if mk is not None:
                zcheck_together('WPN_%s+Mag' % wid, [(k, (0, 0, 0)), (mk, info['mag'])])
        except ib_lib.ZFightError as e:
            print(e)
            explain(e, [k, mk])
            raise
        try:
            o = finish('WPN_' + wid, k)
        except ib_lib.ZFightError as e:
            explain(e, [k])
            raise
        if mk is not None:
            finish('WPN_%s_Mag' % wid, mk)
        WEAPONS.setdefault(wid, {}).update(info)
        socket('WPN_%s_MUZZLE' % wid, o, info['muzzle'])
        socket('WPN_%s_MAG' % wid, o, info['mag'])
        socket('WPN_%s_EJECT' % wid, o, info['eject'])
        socket('WPN_%s_SIGHT' % wid, o, info['sight'])
        if 'scope' in info:
            socket('WPN_%s_SCOPE' % wid, o, info['scope'])
        if 'elem' in info:
            socket('WPN_%s_ELEM' % wid, o, info['elem'])


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


# ================================================================ actions
FPS = 30
# Timing from src/data/weapons.js (fire = one cycle 60/rpm; burst weapons: one burst; reload seconds).
# style: reload choreography. charge: (point, pull) the support hand works after a reload (slide, handle, bolt).
# carry: where the whole viewmodel sits (rig space) so long guns tuck their stocks off-screen.
ANIM = {
    'PIP': {'fire': 60 / 450, 'reload': 1.1, 'style': 'pistol', 'charge': ((0, -0.068, 0.044), (0, -0.030, 0))},
    'HANDCANNON': {'fire': 60 / 150, 'reload': 2.2, 'style': 'revolver', 'heavy': 1.6},
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
    """P: W (weapon delta), FR / FL (hand frames, rig space), curl {bone: deg}, mag (Mag bone delta).
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
        ax = (F0.to_3x3() @ V((0, 0, 1))).normalized()
        lx = (F0.to_3x3() @ V((1, 0, 0))).normalized()     # hand's lateral axis: lifts a finger along the frame
        sg = 1 if side == 'R' else -1
        lift = P.get('lift', {})
        for fn in FINGERS + ('THUMB1', 'THUMB2'):
            bn = fn + '_' + side
            h = rig.data.bones[bn].head_local
            C = T(h) @ Matrix.Rotation(D(sg * P['curl'].get(bn, 0.0)), 4, ax) @ Matrix.Rotation(D(lift.get(bn, 0.0)), 4, lx) @ T(-h)
            M[bn] = M['THUMB1_' + side if fn == 'THUMB2' else 'HAND_' + side] @ C
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
        curl = {'INDEX_R': 14 * trig + idx, 'INDEX_L': curlL, 'THUMB1_L': thumbL, 'THUMB1_R': thumbR}
        for fn in ('MIDDLE', 'RING', 'PINKY'):
            curl[fn + '_R'] = curlR
            curl[fn + '_L'] = curlL
        return {'W': W, 'FR': FR if FR is not None else W @ self.GR, 'FL': FL if FL is not None else W @ self.GL,
                'mag': mag if mag is not None else W @ T(self.magT), 'curl': curl, 'lift': {'INDEX_R': lift},
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

    for wid in GUNS:
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


def revolver_reload(p, r):
    """Cylinder swings out to the left, muzzle up to dump the cases, fresh rounds from the support hand,
    cylinder snaps shut."""
    info = p.info
    fr = lambda t: round(r * t)
    piv = V(info['pivot'])
    swing = lambda Wm, ang: Wm @ T(piv) @ mat_trs((0, 0, 0), (0, -ang, 0)) @ T(-piv) @ T(p.magT)
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


# ================================================================ pickups
def build_pickups(pal):
    # gem: brilliant-cut, 8 sides, two-tone facets (tinted per gem type by instance colour)
    k = Kit(pal)
    n = 8
    rings = [[(0.09 * math.cos(2 * math.pi * i / n), 0.09 * math.sin(2 * math.pi * i / n), 0.17) for i in range(n)],
             [(0.16 * math.cos(2 * math.pi * (i + 0.5) / n), 0.16 * math.sin(2 * math.pi * (i + 0.5) / n), 0.10) for i in range(n)], [(0, 0, -0.18)]]
    k.loft(rings, 'chip', hull=True, caps=(True, False))
    for i, f in enumerate([f for f in k.bm.faces if len(f.verts) == 4]):
        if i % 2:
            f.material_index = pal.index('chip2')
    finish('PICKUP_Gem', k, ht=0.02)
    # ammo box: steel can with lid, handle, latch, label with three rounds
    k = Kit(pal)
    k.cbox((0, 0, 0.21), (0.60, 0.38, 0.42), 'ammo', ch=0.03, axis='z')
    k.cbox((0, 0, 0.445), (0.64, 0.42, 0.07), 'ammo2', ch=0.02, axis='z')
    k.box((0, 0, 0.495), (0.24, 0.06, 0.03), 'ink')
    k.cbox((0, 0, 0.52), (0.30, 0.08, 0.04), 'ammo3', ch=0.012, axis='y')
    k.box((0.30, 0, 0.345), (0.08, 0.16, 0.12), 'ammo3')
    k.box((0, -0.205, 0.21), (0.36, 0.06, 0.20), 'paper')
    for i in (-1, 0, 1):
        k.lathe([(0, 0), (0, 0.03), (0.09, 0.03), (0.13, 0.0)], 'brass', 'z', (i * 0.1, -0.24, 0.145), 6, hull=False)
    k.box((0, 0, 0.12), (0.66, 0.44, 0.04), 'ammo2')
    finish('PICKUP_Ammo', k, ht=0.018)
    # health can: canister with rim bands, cap and a white cross
    k = Kit(pal)
    k.lathe([(0, 0), (0, 0.19), (0.46, 0.19), (0.50, 0.15), (0.50, 0)], 'health', 'z', (0, 0, 0), 8, a0=0)
    k.ring('z', (0, 0, 0), 0.06, 0.12, 0.17, 0.215, 'health2', seg=10, hull=False)
    k.lathe([(0.49, 0), (0.49, 0.10), (0.58, 0.10), (0.58, 0)], 'health3', 'z', (0, 0, 0), 8, hull=False)
    a, b = 0.10, 0.035
    plus = [(b, -a), (b, -b), (a, -b), (a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b), (-b, -a)]
    k.ext_y(plus, -0.20, -0.17, 'paper', z=0.25, hull=False)
    finish('PICKUP_Health', k, ht=0.018)
    # rocket ammo crate (launchers only; soldiers drop it): olive crate, rope handles, a stencilled rocket on the
    # front, two red-tipped rockets strapped on the lid
    k = Kit(pal)
    k.cbox((0, 0, 0.17), (0.66, 0.40, 0.34), 'olive', ch=0.03, axis='z')
    k.cbox((0, 0, 0.355), (0.70, 0.44, 0.06), 'olive2', ch=0.02, axis='z')
    k.box((0, 0, 0.10), (0.72, 0.46, 0.05), 'olive2')
    for x in (-0.24, 0.24):
        k.box((x, 0, 0.21), (0.05, 0.47, 0.25), 'olive2')
    k.box((0, -0.205, 0.21), (0.30, 0.03, 0.16), 'paper', hull=False)
    k.box((-0.02, -0.225, 0.21), (0.16, 0.02, 0.04), 'red', hull=False)          # stencil: rocket body
    k.box((0.075, -0.225, 0.21), (0.04, 0.03, 0.025), 'ink', hull=False)         # nose
    k.box((-0.11, -0.225, 0.21), (0.03, 0.026, 0.08), 'ink', hull=False)         # fins
    for y in (-0.08, 0.08):
        k.lathe([(-0.26, 0), (-0.26, 0.042), (0.16, 0.042), (0.21, 0.030), (0.25, 0)], 'paper', 'x', (0, y, 0.425), 8,
                bands=[None, None, 'red', 'red'])
        k.ring('x', (0, y, 0.425), -0.20, -0.17, 0.038, 0.048, 'amber', seg=8, hull=False)
    k.box((0, 0, 0.425), (0.06, 0.32, 0.10), 'ink')                                 # strap
    finish('PICKUP_Rockets', k, ht=0.018)
    # launcher round in flight (game/launchers.js scales it per launcher): paper body, red warhead, ink fins, amber band
    k = Kit(pal)
    k.lathe([(-0.22, 0), (-0.22, 0.050), (0.14, 0.055), (0.20, 0.050), (0.29, 0)], 'paper', 'y', (0, 0, 0), 8,
            bands=[None, None, 'red', 'red'])
    k.ring('y', (0, 0, 0), -0.06, -0.02, 0.040, 0.056, 'amber', seg=8, hull=False)
    for a in (45, 135, 225, 315):
        with k.at((0, 0, 0), (0, a, 0)):
            k.box((0.055, -0.16, 0), (0.07, 0.10, 0.012), 'ink', hull=True)
    k.lathe([(-0.26, 0), (-0.26, 0.032), (-0.21, 0.036), (-0.21, 0)], 'gunmetal', 'y', (0, 0, 0), 8, bands=['ink', None, None])
    finish('PROJ_Rocket', k, ht=0.012)


def hold_socket(rig):
    """HOLD_L: an empty on the left hand bone where held things sit (the frag can, a shotgun shell): on the support
    glove's grip axis, in the closed fist, upright along the grip axis."""
    e = bpy.data.objects.new('HOLD_L', None)
    e.empty_display_size = 0.02
    bpy.context.scene.collection.objects.link(e)
    e.parent = rig
    e.parent_type = 'BONE'
    e.parent_bone = 'HAND_L'
    bpy.context.view_layer.update()
    e.matrix_world = rig.matrix_world @ RIG['F0']['L'] @ T((0.0, HAND['cy'], -0.046))


def build_scene():
    """Everything in the weapons GLB, in the current (fresh) scene; returns (palette, rig, arms)."""
    pal = Palette('weapons')
    build_weapon_meshes(pal)
    build_pickups(pal)
    build_held(pal)
    rig, arms = build_arms(pal)
    hold_socket(rig)
    fit_support()
    for wid, info in WEAPONS.items():
        if 'curl_L' in info:
            print('support hold %-10s offset %s curl %+.0f' % (wid, tuple(round(c, 3) for c in info['hold_L'].translation), info['curl_L']))
    build_actions(rig)
    return pal, rig, arms


def build_weapons(ao):
    build_scene()
    export('weapons')


FAMILY = 'weapons'
BUILD = build_weapons
