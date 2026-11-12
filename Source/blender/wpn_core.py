"""INKBOLT weapons, shared core: palette, the shape kit (Kit) and the gun parts every builder uses.
The guns themselves are in wpn_<group>.py; fam_weapons.py builds the family (guns, arms rig, actions, pickups).

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
    ('trim', '#FFB21E'),     # accent stripes / rings (glow lines on Epic and Legendary)
    # tactical pass: second tones of the three main materials (layered plates, recessed panels), stencil paint,
    # energy cells (lit from Rare up) and rubber (pads, boots: black that still takes shading, unlike 'ink')
    ('body2', '#454357'), ('frame2', '#5E5D73'), ('acc2', '#56546A'), ('mark', '#E6E1D3'), ('emis', '#5FE6FF'), ('rubber', '#2B2A33')]

import os
DEBUG = {} if os.environ.get('IB_DEBUG') else None
HULL_T = 0.0035     # viewmodel outline shell (m): thin enough that 3 mm details stay crisp
GUN_HULL_T = 0.0022  # guns: a finer ink line than the arms (tactical pass); the game's uBaked stays 0.0035


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

    def ext(self, prof, color, o, u, v, w, d0, d1, ch0=0.0, ch1=0.0, hull=True, stations=None, bands=None, caps=(True, True)):
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
        return self.loft(rings, color, hull, bands=bands, caps=caps)

    def ext_y(self, prof, y0, y1, color, ch0=0.0, ch1=0.0, hull=True, x=0.0, z=0.0, stations=None, bands=None):
        return self.ext(prof, color, (x, 0, z), (1, 0, 0), (0, 0, 1), (0, 1, 0), y0, y1, ch0, ch1, hull, stations, bands)

    def ext_x(self, prof, x0, x1, color, ch=0.0, hull=True, stations=None, bands=None):
        return self.ext(prof, color, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), x0, x1, ch, ch, hull, stations, bands)

    def ext_z(self, prof, z0, z1, color, ch0=0.0, ch1=0.0, hull=True, stations=None, bands=None):
        return self.ext(prof, color, (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), z0, z1, ch0, ch1, hull, stations, bands)

    def xbar(self, x0, x1, prof, color, ch=0.0015, hull=True):
        """Side-profile plate across X (sights, levers, triggers)."""
        return self.ext_x(prof, x0, x1, color, ch=ch, hull=hull)

    def lathe(self, prof, color, axis='y', c=(0, 0, 0), seg=12, hull=True, bands=None, a0=None, closed=False, sc=(1.0, 1.0), caps=(True, True)):
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
        return self.loft(rings, color, hull, bands=bands, closed=closed, caps=caps)

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


CAV_DIRS = []
for _i in range(18):                 # cosine-weighted hemisphere (z up), fixed
    _r, _a = math.sqrt((_i + 0.5) / 18), _i * 2.399963
    CAV_DIRS.append((_r * math.cos(_a), _r * math.sin(_a), math.sqrt(1 - _r * _r)))


def cavity(obj, occl=(), dist=0.030, strength=0.62, floor=0.50):
    """Soft contact shading baked into the vertex colour 'Col' (grey, so every material just multiplies it): per face
    corner, how much of the hemisphere within `dist` is blocked by the gun itself (and by `occl`, e.g. the base gun
    under a rarity layer). Recesses, the undersides of rails and the roots of parts go darker; open faces stay white."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    col = bm.loops.layers.float_color.get('Col')
    solid = [f for f in bm.faces if not all(v[hl].length > 0 for v in f.verts)]
    vs, ps = [], []
    for o in [None] + list(occl):
        if o is None:
            src, fs = bm, solid
        else:
            src = bmesh.new()
            src.from_mesh(o.data)
            h2 = src.verts.layers.float_vector.get('_HULL')
            fs = [f for f in src.faces if not all(v[h2].length > 0 for v in f.verts)]
        base = len(vs)
        idx = {}
        for f in fs:
            poly = []
            for v in f.verts:
                if v.index not in idx:
                    idx[v.index] = base + len(idx)
                    vs.append(v.co.copy())
                poly.append(idx[v.index])
            ps.append(poly)
        if o is not None:
            src.free()
    tree = BVHTree.FromPolygons(vs, ps, all_triangles=False)
    cache = {}
    for f in solid:
        n = f.normal
        if n.length < 1e-6:
            continue
        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()
        for l in f.loops:
            p = l.vert.co
            key = (round(p.x, 4), round(p.y, 4), round(p.z, 4), round(n.x, 2), round(n.y, 2), round(n.z, 2))
            a = cache.get(key)
            if a is None:
                q = p + n * 0.0009 + (c - p).normalized() * min(0.0015, (c - p).length * 0.3)
                occ = 0.0
                for dx, dy, dz in CAV_DIRS:
                    hit = tree.ray_cast(q, t * dx + b * dy + n * dz, dist)
                    if hit[0] is not None:
                        occ += 1.0 - hit[3] / dist
                a = cache[key] = max(floor, 1.0 - strength * (occ / len(CAV_DIRS)) * 1.6)
            l[col] = (a, a, a, 1.0)
    bm.to_mesh(obj.data)
    bm.free()


def finish(name, kit, ht=HULL_T, cav=None):
    """Triangulate n-gons (exact z-fight test on convex pieces), build, then drop the shell of inner details.
    cav: a list of occluder objects ([] = just itself) bakes cavity shading into the vertex colour (guns)."""
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
    if cav is not None:
        cavity(obj, cav)
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
         ptop=-0.022, grooves=3, ch=0.004, chequer=0):
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
    elif style == 'flare':     # hand-cannon: curved back strap, butt flared fore and aft
        pts = [(f - 0.003, top), (f + 0.003, -0.030), (f + 0.001, -0.060), (f + 0.006, bottom + 0.006), (f + 0.011, bottom - 0.004),
               (b - 0.008, bottom - 0.008), (b - 0.015, bottom + 0.004), (b - 0.007, -0.052), (b - 0.002, -0.012), (b + 0.006, top)]
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
        k.ext(gprof(rake, pp, ay, az), panel, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), min(x0, x1), max(x0, x1),
              ch0=0.001 if s < 0 else 0.0, ch1=0.001 if s > 0 else 0.0, hull=False, caps=(s < 0, s > 0))
        z_hi, z_lo = ptop - 0.006, bottom + 0.022          # texture: fine grip lines over the whole panel
        nl = max(3, grooves * 3)
        for j in range(nl):
            gz = z_hi + (z_lo - z_hi) * j / (nl - 1)
            a = g2w(rake, f - 0.010, gz, ay, az)
            b2 = g2w(rake, b + 0.008, gz, ay, az)
            xm = s * (w / 2 + 0.0040)
            k.bar((xm, a[0], a[1]), (xm, b2[0], b2[1]), 0.003, 0.0022, 'rubber')
        for j in range(chequer):     # chequering: cross lines over the panel
            gy = f - 0.012 - j * (hy * 2 - 0.022) / max(1, chequer - 1)
            a = g2w(rake, gy, ptop - 0.004, ay, az)
            b2 = g2w(rake, gy, bottom + 0.020, ay, az)
            xm = s * (w / 2 + 0.0080)
            k.bar((xm, a[0], a[1]), (xm, b2[0], b2[1]), 0.0035, 0.003, 'ink')
    zc = bottom + 0.0115
    k.pin(-w / 2 - 0.0050, w / 2 + 0.0050, *g2w(rake, cy, zc, ay, az), 0.0034, color='steel2')


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
    if ribs:            # two raised ribs per side following the curve, witness holes, floor-plate grooves
        for s in (-1, 1):
            for fr in (-0.24, 0.20):
                pts = []
                for i in range(4):
                    t = 0.12 + 0.26 * i
                    y, z = g2w(rake, depth * fr + curve * t * t, top + (bottom - top) * t)
                    pts.append(((s * (w / 2 + 0.0008), y, z), 0.005, 0.007))
                k.tube(pts, 'frame2', sides=4, up=(1, 0, 0), hull=False, a0=45)
            for j in range(3):
                t = wt + 0.13 * j
                y, z = g2w(rake, -depth * 0.02 + curve * t * t, top + (bottom - top) * t)
                k.box((s * (w / 2 + PR / 2 - 0.0005), y, z), (PR + 0.001, 0.0045, 0.0045), 'ink', skip=sk(s))
            for j in range(3):
                gy = -depth * 0.26 + curve + j * depth * 0.26
                y, z = g2w(rake, gy, bottom - plate_h / 2)
                k.box((s * (pw + PR / 2 - 0.0005), y, z), (PR + 0.001, 0.0035, plate_h * 0.6), 'ink', skip=sk(s))
    if brass:
        cy, cz = g2w(rake, 0.002, top + 0.004)
        k.lathe([(cy - depth * 0.35, 0), (cy - depth * 0.35, 0.0055), (cy + depth * 0.15, 0.0055), (cy + depth * 0.32, 0.003), (cy + depth * 0.32, 0)],
                'brass', 'y', (0, 0, cz), 6, hull=False)


def iron_rear(k, y, z, w=0.028, h=0.014, color='gunmetal'):
    """Flip-up aperture rear sight on a rail at height z: clamp with its cross bolt, protective ears, the aperture
    ring between them and a windage knob. Returns the sight-line height."""
    k.cbox((0, y, z + h / 2), (w, 0.016, h), color, ch=0.002, axis='y')
    zr = z + h + 0.0065
    for s in (-1, 1):
        k.ext_x([(y - 0.006, z + h - 0.001), (y + 0.006, z + h - 0.001), (y + 0.004, zr + 0.008), (y - 0.004, zr + 0.008)], min(s * 0.0095, s * 0.0125), max(s * 0.0095, s * 0.0125),
                color, ch=0.0008)
    k.ring('y', (0, 0, zr), y - 0.0025, y + 0.0025, 0.0032, 0.0072, 'ink', seg=8, hull=False)
    k.lathe([(w / 2 - 0.001, 0.0045), (w / 2 + 0.005, 0.0045), (w / 2 + 0.005, 0)], 'steel2', 'x', (0, y, z + h / 2), 8, hull=False, caps=(False, True))
    bolt(k, (-w / 2, y, z + h / 2), (-1, 0, 0), 0.0030)
    return zr


def iron_front(k, y, z, w=0.028, h=0.014, post=0.020, color='gunmetal'):
    """Flip-up front sight: clamp with its cross bolt, two swept ears and the post between them."""
    k.cbox((0, y, z + h / 2), (w, 0.016, h), color, ch=0.002, axis='y')
    zt = z + h + post - 0.002
    for s in (-1, 1):
        k.ext_x([(y - 0.007, z + h - 0.001), (y + 0.007, z + h - 0.001), (y + 0.003, zt + 0.004), (y - 0.003, zt + 0.004)], min(s * 0.006, s * 0.0105), max(s * 0.006, s * 0.0105),
                color, ch=0.0008)
    k.box((0, y, z + h + post / 2 - 0.003), (0.0036, 0.005, post - 0.002), 'ink')
    bolt(k, (w / 2, y, z + h / 2), (1, 0, 0), 0.0030)
    bolt(k, (-w / 2, y, z + h / 2), (-1, 0, 0), 0.0030)


def red_dot(k, y, z, L=0.05, r=0.017, color='gunmetal'):
    """Tube red-dot on a rail at height z: clamp, open tube you look straight through (no glass: a lens plate would
    hide the target when aiming down the sight), dark rims front and back, turret."""
    cz = z + 0.010 + r
    k.cbox((0, y, z + 0.006), (0.030, L * 0.45, 0.012), color, ch=0.002, axis='y')
    k.ring('y', (0, 0, cz), y - L / 2, y + L / 2, r - 0.004, r, color, seg=10, bands=['ink', None, 'ink', None])
    k.lathe([(0, 0), (0, 0.0065), (0.009, 0.0065), (0.009, 0)], 'gun3', 'z', (0, y - L * 0.1, cz + r - 0.003), 8, hull=False)
    return cz


def hood_sight(k, y0, y1, zb, w=0.034, h=0.026, t=0.005, color='gunmetal'):
    """Open reflex / holo sight: a hollow rectangular hood on a base with a red bead; nothing fills the window (a
    lens plate would hide the target when aiming down the sight)."""
    k.cbox((0, (y0 + y1) / 2, zb + 0.004), (w - 0.004, y1 - y0 + 0.006, 0.008), color, ch=0.002, axis='y')
    z0 = zb + 0.007
    oc, ic = rrect(w, h, ct=0.007, cb=0.002, cy=z0 + h / 2), rrect(w - 2 * t, h - 2 * t, ct=0.004, cb=0.001, cy=z0 + h / 2)
    ring = lambda p, y: [(q[0], y, q[1]) for q in p]
    k.loft([ring(ic, y0), ring(oc, y0), ring(oc, y1), ring(ic, y1)], color, closed=True, bands=[None, None, None, 'ink'])
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


def launcher_frame(k, rake, fore_y, fore_top):
    """Shared lower: frame block under the tube / housing, AR grip, guard, trigger, a vertical foregrip on a lug."""
    k.cbox((0, 0.040, 0.012), (0.040, 0.190, 0.044), 'gun2', ch=0.004, axis='y')                     # frame, z -0.010..0.034
    trigger_guard(k, rake, front=0.066, depth=-0.052, w=0.012, top=-0.004, hook=False)
    trigger(k, rake, ext=0.006)
    grip(k, rake, 'ar', w=0.034, top=0.000, ptop=-0.036, grooves=2)
    k.cbox((0, fore_y, fore_top + 0.003), (0.040, 0.044, 0.014), 'gun2', ch=0.003, axis='y')         # foregrip lug
    vgrip(k, fore_y, fore_top, length=0.074, r=0.016, seg=8)



# ================================================================ tactical detail kit (guns)
# Gun details stand PR proud of (or sit PR inside) the surface under them: the gun build runs the z-fight test at
# GUN_ZFIGHT_TOL, finer than the world's 2.5 mm (a gun is never seen from far enough for 1.5 mm to fight).
PR = 0.0015
GUN_ZFIGHT_TOL = 0.0012


def sk(s):
    """skip= for a box on the s side of a body: its hidden inner face"""
    return ('-x',) if s > 0 else ('+x',)


def plate(k, prof, hw, color, t=PR, ch=0.0008, sides=(-1, 1), hull=False, sink=0.001):
    """Cladding plate: a side-profile polygon [(y, z)] standing t proud of a body of half-width hw (both sides by
    default), its rim chamfered so it catches the light. Layer plates of two tones for panel lines and steps."""
    for s in sides:
        a, b = s * (hw - sink), s * (hw + t)
        k.ext(prof, color, (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), min(a, b), max(a, b),
              ch0=ch if s < 0 else 0.0, ch1=ch if s > 0 else 0.0, hull=hull, caps=(s < 0, s > 0))


def rect(y0, y1, z0, z1, c=0.0):
    """side-profile rectangle (optionally corner-cut) for plate()"""
    if c <= 0:
        return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]
    return [(y0 + c, z0), (y1 - c, z0), (y1, z0 + c), (y1, z1 - c), (y1 - c, z1), (y0 + c, z1), (y0, z1 - c), (y0, z0 + c)]


def slots(k, hw, y0, y1, z, n, h=0.006, fill=0.6, color='ink', sides=(-1, 1), slant=0.0, t=PR):
    """Row of n dark slots along y on the side faces of a body of half-width hw (lightening cuts, vents);
    slant leans them (degrees)."""
    pitch = (y1 - y0) / n
    for s in sides:
        for i in range(n):
            yc = y0 + pitch * (i + 0.5)
            k.box((s * (hw + t / 2 - 0.0005), yc, z), (t + 0.001, pitch * fill, h), color, rot=(slant * s, 0, 0), skip=sk(s))


def top_slots(k, z, y0, y1, n, w=0.010, fill=0.6, color='ink', x=0.0, t=PR):
    pitch = (y1 - y0) / n
    for i in range(n):
        k.box((x, y0 + pitch * (i + 0.5), z + t / 2 - 0.0005), (w, pitch * fill, t + 0.001), color, skip=('-z',))


def bolt(k, p, n, r=0.0032, h=0.0028, color='steel2', seg=6, socket=True):
    """Bolt head on a surface at p, facing n: hex head with a dark socket."""
    n = V(n).normalized()
    u = n.orthogonal().normalized()
    prof = [(-0.001, r), (h, r)]
    bands = [None]
    if socket:
        prof += [(h, r * 0.5), (h - 0.0012, r * 0.5), (h - 0.0012, 0)]
        bands += [None, 'ink', 'ink']
    else:
        prof += [(h, 0)]
        bands += [None]
    return k.lathe(prof, color, (n, u, n.cross(u)), p, seg, hull=False, bands=bands, caps=(False, True))


def bolts(k, hw, pts, r=0.0030, color='steel2', sides=(-1, 1), h=0.0028):
    """bolt heads at side-profile points [(y, z)] on both side faces of a body of half-width hw"""
    for s in sides:
        for y, z in pts:
            bolt(k, (s * hw, y, z), (s, 0, 0), r, h, color)


def cross_pin(k, hw, y, z, r=0.0036, color='steel2', ring='ink'):
    """Takedown / pivot pin through a body: a dark washer ring and the pin head, both sides."""
    for s in (-1, 1):
        n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
        k.lathe([(-0.001, r + 0.0022), (PR, r + 0.0022), (PR, r), (PR + 0.0015, r), (PR + 0.0015, 0)], color, n, (s * hw, y, z), 8,
                hull=False, bands=[ring, ring, None, None], caps=(False, True))


def hazard(k, hw, y0, y1, z0, z1, n=4, color='mark', sides=(-1, 1), lean=0.6, t=PR):
    """Diagonal stencil stripes filling a side rectangle (warning band)."""
    pitch = (y1 - y0) / n
    w, dz = pitch * 0.5, z1 - z0
    for i in range(n):
        ya = y0 + pitch * i
        prof = [(ya, z0), (ya + w, z0), (ya + w + dz * lean, z1), (ya + dz * lean, z1)]
        plate(k, prof, hw, color, t=t, ch=0.0, sides=sides)


def stencil(k, text, hw, y, z, cap=0.008, color='mark', sides=(-1, 1), font='display', t=PR, align='c'):
    """Stencilled lettering on the side faces (reads left to right on each side); z is the baseline."""
    import ib_text
    tris, w, x0 = ib_text.layout(text, font)
    ou = {'c': -w / 2, 'l': 0.0, 'r': -w}[align] - x0
    bm = k.bm
    for s in sides:
        before = set(bm.faces)
        for tri in tris:
            vs = [bm.verts.new(k.xf @ V((s * (hw + t), y + s * (u + ou) * cap, z + v * cap))) for (u, v) in tri]
            f = bm.faces.new(vs)
            f.normal_update()
            if (k.xf.to_3x3() @ V((s, 0, 0))).dot(f.normal) < 0:
                f.normal_flip()
        k._reg(before, color, False)
    return w * cap


def top_stencil(k, text, z, y, cap=0.006, color='mark', x=0.0, font='display', t=PR):
    """Lettering on a top face, read from behind the gun (the shooter's view): letters run along +x, tops toward +y."""
    import ib_text
    tris, w, x0 = ib_text.layout(text, font)
    bm = k.bm
    before = set(bm.faces)
    for tri in tris:
        vs = [bm.verts.new(k.xf @ V((x + (u - w / 2 - x0) * cap, y + v * cap, z + t))) for (u, v) in tri]
        f = bm.faces.new(vs)
        f.normal_update()
        if (k.xf.to_3x3() @ V((0, 0, 1))).dot(f.normal) < 0:
            f.normal_flip()
    k._reg(before, color, False)


def cable(k, pts, r=0.0028, color='rubber', sides=5, clamps=(), clamp_color='steel2'):
    """Cable / hose through 3D points; clamps: indices of points that get a clamp ring."""
    k.tube([(p, r * 2, r * 2) for p in pts], color, sides=sides, hull=False)
    for i in clamps:
        a, b = V(pts[max(i - 1, 0)]), V(pts[min(i + 1, len(pts) - 1)])
        d = (b - a).normalized()
        u = d.orthogonal().normalized()
        k.lathe([(-0.003, 0), (-0.003, r + PR), (0.003, r + PR), (0.003, 0)], clamp_color, (d, u, d.cross(u)), pts[i], 6, hull=False)


def octa(w, h, c, cx=0.0, cz=0.0):
    """octagon section [(x, z)] CCW starting at the right side's bottom corner"""
    a, b = w / 2, h / 2
    return [(cx + a, cz - b + c), (cx + a, cz + b - c), (cx + a - c, cz + b), (cx - a + c, cz + b), (cx - a, cz + b - c), (cx - a, cz - b + c),
            (cx - a + c, cz - b), (cx + a - c, cz - b)]


OCTA_FACES = ('R', 'UR', 'T', 'UL', 'L', 'DL', 'B', 'DR')      # face i runs from octa()[i] to octa()[i + 1]


def cage(k, y0, y1, cz, w, h, c, n=6, rib=0.010, open=('R', 'UR', 'UL', 'L'), color='gun3', th=0.0035, edge=0.28, end=0.016,
         rib_color=None, cx=0.0, hull=True):
    """Free-float handguard as a real cage: thin wall strips with open slots (you see the barrel through them)
    between raised ribs. Faces in `open` get a slot between every pair of ribs (the strips keep `edge` of the face
    width on each side); the others are solid. Ribs are hollow rings PR proud of the strips; the first and last
    are `end` long (rear clamp, front cap)."""
    O = octa(w, h, c, cx, cz)
    I = octa(w - 2 * th, h - 2 * th, c - th * 0.42, cx, cz)
    for i, name in enumerate(OCTA_FACES):
        p0, p1, q0, q1 = V(O[i]), V(O[(i + 1) % 8]), V(I[i]), V(I[(i + 1) % 8])
        if name in open:
            for (a, b) in ((0.0, edge), (1.0 - edge, 1.0)):
                quad = [p0.lerp(p1, a), p0.lerp(p1, b), q0.lerp(q1, b), q0.lerp(q1, a)]
                k.ext_y([tuple(v) for v in quad], y0 + 0.004, y1 - 0.004, color, hull=hull)
        else:
            k.ext_y([tuple(p0), tuple(p1), tuple(q1), tuple(q0)], y0 + 0.004, y1 - 0.004, color, hull=hull)
    Or = octa(w + 2 * PR, h + 2 * PR, c + PR * 0.42, cx, cz)
    Ir = octa(w - 2 * th - 0.004, h - 2 * th - 0.004, c - th * 0.42, cx, cz)
    ring3 = lambda pts, y: [(q[0], y, q[1]) for q in pts]
    span = (y1 - y0 - 2 * end) / n
    ys = [(y0, y0 + end)] + [(y0 + end + span * i - rib / 2, y0 + end + span * i + rib / 2) for i in range(1, n)] + [(y1 - end, y1)]
    for (a, b) in ys:
        k.loft([ring3(Ir, a), ring3(Or, a), ring3(Or, b), ring3(Ir, b)], rib_color or color, hull=hull, closed=True)
    return ys


def energy_cell(k, p, L=0.036, r=0.0075, axis='y', color='emis', cap='steel2', cage_bars=3, seg=8):
    """Energy cell: a glowing capsule between two metal caps, with thin cage bars over the glass."""
    ax = AXES[axis]
    k.lathe([(-L / 2, 0), (-L / 2, r + 0.002), (-L / 2 + 0.006, r + 0.002), (-L / 2 + 0.006, r), (L / 2 - 0.006, r), (L / 2 - 0.006, r + 0.002),
             (L / 2, r + 0.002), (L / 2, 0)], cap, ax, p, seg, hull=True, bands=[None, None, None, color, None, None, None])
    for i in range(cage_bars):
        a = 2 * math.pi * (i + 0.5) / cage_bars
        off = ax[1] * (math.cos(a) * (r + 0.0035)) + ax[2] * (math.sin(a) * (r + 0.0035))
        c0 = V(p) + off
        k.bar(c0 - ax[0] * (L / 2 - 0.004), c0 + ax[0] * (L / 2 - 0.004), 0.0022, 0.0022, cap, up=tuple(off.normalized()))


def conduit(k, pts, r=0.003, color='emis', collar='steel2', every=1, sides=6):
    """Glowing conduit through points, a metal collar at every `every`-th point."""
    k.tube([(p, r * 2, r * 2) for p in pts], color, sides=sides, hull=False)
    for i in range(0, len(pts), every):
        a, b = V(pts[max(i - 1, 0)]), V(pts[min(i + 1, len(pts) - 1)])
        d = (b - a).normalized()
        u = d.orthogonal().normalized()
        k.lathe([(-0.004, 0), (-0.004, r + 0.002), (0.004, r + 0.002), (0.004, 0)], collar, (d, u, d.cross(u)), pts[i], 6, hull=False)


def fins(k, c, size, n, axis='y', color='steel2', fill=0.45, hull=False):
    """Heat-sink fin stack: n thin plates inside the box (centre c, size) stacked along axis."""
    ai = 'xyz'.index(axis)
    pitch = size[ai] / n
    for i in range(n):
        cc = list(c)
        cc[ai] = c[ai] - size[ai] / 2 + pitch * (i + 0.5)
        sz = list(size)
        sz[ai] = pitch * fill
        k.box(tuple(cc), tuple(sz), color, hull=hull)


def laser_box(k, y, z, s=1, hw=0.027, L=0.050, w=0.018, h=0.022, color='gun2', lens='emis', cap='steel2'):
    """Side-mounted aiming module: housing with a clamp, a small lens tube and an activation button."""
    xc = s * (hw + w / 2 - 0.001)
    k.cbox((xc, y, z), (w, L, h), color, ch=0.003, hull=True)
    k.lathe([(0, 0), (0, 0.0062), (0.006, 0.0062), (0.006, 0.0042), (0.003, 0.0042), (0.003, 0)], cap, 'y', (xc, y + L / 2 - 0.001, z + 0.002), 8, hull=False,
            bands=[None, None, None, lens, lens])
    k.box((xc, y - L * 0.18, z + h / 2 + PR / 2), (w * 0.5, L * 0.22, PR + 0.001), 'rubber', skip=('-z',))
    bolt(k, (xc + s * w / 2, y - L * 0.25, z - 0.002), (s, 0, 0), 0.0028)
    bolt(k, (xc + s * w / 2, y + L * 0.22, z - 0.002), (s, 0, 0), 0.0028)


def sling_loop(k, y, z, s=1, hw=0.02, r=0.008, color='steel2'):
    """QD sling swivel socket: a recessed cup with a ring."""
    n = (V((s, 0, 0)), V((0, 1, 0)), V((0, 0, s)))
    k.lathe([(-0.001, r), (PR * 2, r), (PR * 2, r * 0.62), (PR, r * 0.62), (PR, 0)], color, n, (s * hw, y, z), 8,
            hull=False, bands=[None, None, 'ink', 'ink'], caps=(False, True))


def gas_block(k, y, z, r=0.012, L=0.022, color='steel2', tube_to=None, tz=None):
    """Low-profile gas block on a barrel at y (and the gas tube back to tube_to at height tz)."""
    k.cbox((0, y, z + 0.004), (r * 2, L, r * 2 + 0.008), color, ch=0.003, axis='y', hull=False)
    if tube_to is not None:
        tz = z + r + 0.004 if tz is None else tz
        k.lathe([(tube_to, 0), (tube_to, 0.0032), (y, 0.0032), (y, 0)], 'steel', 'y', (0, 0, tz), 6, hull=False)


def knurl(k, y0, y1, r, z, n=5, x=0.0, color='ink', seg=10):
    """n dark grip rings around a barrel-axis cylinder of radius r"""
    pitch = (y1 - y0) / n
    for i in range(n):
        yc = y0 + pitch * (i + 0.5)
        k.ring('y', (x, 0, z), yc - pitch * 0.22, yc + pitch * 0.22, r - 0.001, r + PR, color, seg=seg, hull=False)


# Each builder returns (gun kit, mag kit, info). info: rake (grip angle), sockets (weapon space), cls.
WEAPONS = {}


# ================================================================ one weapon -> its meshes
WORLD_ZFIGHT_TOL = ib_lib.ZFIGHT_TOL
TIERS = '12345'          # rarity tiers a layer can be shown on: 1 Standard, 2 Tuned, 3 Rare, 4 Epic, 5 Legendary


def build_weapon(wid, fn, pal, gun=True):
    """WPN_<ID> (+ WPN_<ID>_Mag), its sockets and its rarity layers. A gun builder may return info['layers'] =
    {'345': kit, '5': kit, ...}: extra parts in gun space, one mesh each, named WPN_<ID>_L<tiers> and parented to the
    gun; the game shows a layer when the gun's tier digit is in its name (src/game/gunskins.js layerOn). Likewise
    info['mag_layers'] on the magazine (WPN_<ID>_Mag_L<tiers>, in the magazine's own frame). Guns (not melee) get
    the finer outline, the finer z-fight tolerance and baked cavity shading."""
    k, mk, info = fn(pal)
    ib_lib.ZFIGHT_TOL = GUN_ZFIGHT_TOL if gun else WORLD_ZFIGHT_TOL
    layers = info.pop('layers', {}) if gun else {}
    mlayers = info.pop('mag_layers', {}) if gun else {}
    try:
        try:
            if mk is not None:
                zcheck_together('WPN_%s+Mag' % wid, [(k, (0, 0, 0)), (mk, info['mag'])])
        except ib_lib.ZFightError as e:
            print(e)
            explain(e, [k, mk])
            raise
        for t in TIERS:                 # the parts shown together on each tier must not z-fight either
            on = [lk for mask, lk in layers.items() if t in mask]
            mon = [lk for mask, lk in mlayers.items() if t in mask]
            if not on and not mon:
                continue
            parts = [k] + on + ([mk] + mon if mk is not None else [])
            try:
                zcheck_together('WPN_%s tier %s' % (wid, t), [(p, info['mag'] if p is mk or p in mon else (0, 0, 0)) for p in parts])
            except ib_lib.ZFightError as e:
                print(e)
                explain(e, parts)
                raise
        ht = GUN_HULL_T if gun else HULL_T
        try:
            o = finish('WPN_' + wid, k, ht, [] if gun else None)
        except ib_lib.ZFightError as e:
            explain(e, [k])
            raise
        mo = None
        if mk is not None:
            mo = finish('WPN_%s_Mag' % wid, mk, ht, [] if gun else None)
        for mask, lk in layers.items():
            lo = finish('WPN_%s_L%s' % (wid, mask), lk, ht, [o])
            lo.parent = o
        for mask, lk in mlayers.items():
            lo = finish('WPN_%s_Mag_L%s' % (wid, mask), lk, ht, [mo])
            lo.parent = mo
    finally:
        ib_lib.ZFIGHT_TOL = WORLD_ZFIGHT_TOL
    WEAPONS.setdefault(wid, {}).update(info)
    socket('WPN_%s_MUZZLE' % wid, o, info['muzzle'])
    socket('WPN_%s_MAG' % wid, o, info['mag'])
    socket('WPN_%s_EJECT' % wid, o, info['eject'])
    socket('WPN_%s_SIGHT' % wid, o, info['sight'])
    if 'scope' in info:
        socket('WPN_%s_SCOPE' % wid, o, info['scope'])
    if 'elem' in info:
        socket('WPN_%s_ELEM' % wid, o, info['elem'])
    return o
