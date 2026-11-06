"""INKBOLT kit helpers shared by the industrial kits (fam_kit_coalmine.py, fam_kit_factory.py).

Not an asset family itself (no fam_ prefix). Same conventions as fam_kit_office.py:
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z).
  * Shapes marked ink=False get no outline shell (trims, painted quads, small detail).
  * Collision boxes are <Piece>_COL<n> cube empties (position = box centre, scale = half extents).
Extras over the office Kit: convex-hull rocks (hullp), multi-station open lofts with inset end baffles (loft: rock
faces that run on seamlessly from module to module), flat discs (light pools), hazard stripes.
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def srt(a, b):
    return (a, b) if a <= b else (b, a)


class Kit:
    """One piece at a time: outlined shapes + flat (no-outline) shapes, checked together for z-fighting."""

    def __init__(self, pal, prefix, hull_t):
        self.pal = pal
        self.prefix = prefix
        self.hull_t = hull_t
        self.tris = {}

    def begin(self, rot=0):
        self.m = Model(self.pal)
        self.base = rz(rot)
        self.m.parent = self.base.copy()
        self.stack = []
        self.flat = set()
        self.cols = []
        return self

    def push(self, x, y, deg=0, z=0, sz=1.0, s=1.0):
        self.stack.append(self.m.parent)
        self.m.parent = self.m.parent @ Matrix.Translation((x, y, z)) @ rz(deg) @ Matrix.Diagonal((s, s, sz * s, 1.0))

    def pop(self):
        self.m.parent = self.stack.pop()

    def _mark(self, ink):
        if not ink:
            self.flat.add(self.m.nshape)

    def bx(self, x0, x1, y0, y1, z0, z1, c, ink=True, bevel=False):
        assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
        self.m.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), c, bevel=bevel)
        self._mark(ink)

    def bxr(self, cx, cy, cz, sx, sy, sz, c, rot=(0, 0, 0), ink=True):
        """Box by centre and size with an XYZ rotation (degrees)."""
        self.m.box((cx, cy, cz), (sx, sy, sz), c, rot=rot, bevel=False)
        self._mark(ink)

    def cyl(self, x, y, z, r1, r2, h, c, seg=8, ink=True, bevel=False, rot=(0, 0, 0), caps=True):
        self.m.cyl((x, y, z), r1, r2, h, c, seg=seg, rot=rot, bevel=bevel, caps=caps)
        self._mark(ink)

    def sph(self, x, y, z, r, c, seg=(6, 4), scale=(1, 1, 1), ink=True):
        self.m.sphere((x, y, z), r, c, seg=seg, scale=scale)
        self._mark(ink)

    def beam(self, a, b, t, c, ink=True):
        self.m.beam(a, b, t, c)
        self._mark(ink)

    def poly(self, pts, c, normal):
        P = self.m.parent
        vs = [self.m.bm.verts.new(P @ Vector(p)) for p in pts]
        f = self.m.bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(P.to_3x3() @ Vector(normal)) < 0:
            f.normal_flip()
        self.m._finish(vs, c, False)
        self.flat.add(self.m.nshape)

    def qy(self, x0, x1, z0, z1, y, s, c):
        self.poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], c, (0, s, 0))

    def qx(self, y0, y1, z0, z1, x, s, c):
        self.poly([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], c, (s, 0, 0))

    def qz(self, x0, x1, y0, y1, z, s, c):
        self.poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], c, (0, 0, s))

    def disc(self, x, y, z, r, c, n=12, rnd=None, jag=0.0, a0=0.0, sx=1.0, sy=1.0):
        """Flat upward polygon (light pool, puddle); jag roughens the rim."""
        pts = []
        for i in range(n):
            a = a0 + i / n * 2 * math.pi
            k = 1.0 + ((rnd.uniform(-jag, jag)) if rnd else 0.0)
            pts.append((x + math.cos(a) * r * k * sx, y + math.sin(a) * r * k * sy, z))
        self.poly(pts, c, (0, 0, 1))

    def stripes(self, x0, x1, z0, z1, y, s, n, ca='hazard', cb='ink', slant=0.5):
        """Hazard stripes on a -Y/+Y facing plane: a base quad and n slanted bands 0.3 mm proud... (3 mm)."""
        self.qy(x0, x1, z0, z1, y, s, ca)
        w = (x1 - x0) / n
        h = z1 - z0
        d = s * 0.003
        for i in range(n):
            if i % 2:
                continue
            a = x0 + i * w
            pts = [(max(x0, a), y + d, z0), (min(x1, a + w), y + d, z0)]
            pts += [(min(x1, a + w + slant * h), y + d, z1), (max(x0, a + slant * h), y + d, z1)]
            if pts[2][0] - pts[3][0] > 1e-3 and pts[1][0] - pts[0][0] > 1e-3:
                self.poly(pts, cb, (0, s, 0))

    def hullp(self, pts, color, ink=True):
        """Convex hull of points (piece frame) -> one shape; color: palette name or fn(face) -> name."""
        m = self.m
        P = m.parent
        vs = [m.bm.verts.new(P @ Vector(p)) for p in pts]
        res = bmesh.ops.convex_hull(m.bm, input=vs)
        junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
        if junk:
            bmesh.ops.delete(m.bm, geom=junk, context='VERTS')
        fs = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
        bmesh.ops.recalc_face_normals(m.bm, faces=fs)
        self._tag(fs, color)
        self._mark(ink)
        return fs

    def _tag(self, fs, color):
        m = self.m
        m.nshape += 1
        for f in fs:
            f[m.shape] = m.nshape
            f.normal_update()
            f.material_index = m.pal.index(color(f) if callable(color) else color)

    def loft(self, stations, color, baffle=None, inset=0.05, ink=True, closed_back=False):
        """Open loft along local X through stations [(x, [(y, z), ...]), ...] (each profile front-base -> back-base,
        same point count). The bottom and the end caps are left open; inset baffles close the ends so neighbouring
        modules that share their edge profile run on without an ink seam."""
        m = self.m
        P = m.parent
        rows = [[m.bm.verts.new(P @ Vector((x, y, z))) for (y, z) in prof] for (x, prof) in stations]
        n = len(stations[0][1])
        fs = []
        for a, b in zip(rows, rows[1:]):
            for i in range(n - 1):
                # profiles run front-base -> up -> back-base with stations along +X: this winding faces outward
                fs.append(m.bm.faces.new((a[i], b[i], b[i + 1], a[i + 1])))
        bm_ = m.bm
        fs = bmesh.ops.triangulate(bm_, faces=fs, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
        self._tag(fs, color)
        self._mark(ink)
        if baffle:
            for (x, prof), sgn in ((stations[0], -1), (stations[-1], 1)):
                cy = sum(y for y, z in prof) / n
                cz = sum(z for y, z in prof) / n
                pts = []
                for y, z in prof:
                    dy, dz = cy - y, cz - z
                    L = math.hypot(dy, dz) or 1.0
                    pts.append((x - sgn * inset * 0.2, y + dy / L * inset, (z + dz / L * inset) if z > 1e-4 else 0.0))
                vs = [m.bm.verts.new(P @ Vector(p)) for p in pts]
                f = m.bm.faces.new(vs)
                f.normal_update()
                if f.normal.dot(P.to_3x3() @ Vector((sgn, 0, 0))) < 0:
                    f.normal_flip()
                fl = bmesh.ops.triangulate(bm_, faces=[f], quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
                self._tag(fl, baffle)
                self._mark(False)
        return fs

    def col(self, x0, x1, y0, y1, z0, z1):
        """Collision box in the piece frame (only the piece's base turn applies)."""
        self.cols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        full = self.prefix + name
        m = self.m
        check_zfight(full, m.bm, m.shape)
        flat = self.flat
        fb = m.bm.copy()
        bmesh.ops.delete(m.bm, geom=[f for f in m.bm.faces if f[m.shape] in flat], context='FACES')
        fm = Model(self.pal)
        fm.bm.free()
        fm.bm = fb
        fm.bw = fb.edges.layers.float['bevel_weight_edge']
        fm.shape = fb.faces.layers.int['shape_id']
        bmesh.ops.delete(fb, geom=[f for f in fb.faces if f[fm.shape] not in flat], context='FACES')
        obj = None
        if len(m.bm.faces):
            obj = build_object(full, m, bevel, self.hull_t, ao=ao)
        else:
            m.bm.free()
        if len(fb.faces):
            o2 = build_object(full + '_flat', fm, 0, 0.0)
            strip_hull(o2)
            if obj is None:
                obj = o2
                obj.name = full
                obj.data.name = full
            else:
                join_into(obj, o2)
        else:
            fb.free()
        P = self.base.to_3x3()
        for i, (x0, x1, y0, y1, z0, z1) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_COL%d' % (full, i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj

    def report(self, fam):
        total = 0
        for n in sorted(self.tris):
            total += self.tris[n]
            print('%-38s %6d tris' % (n, self.tris[n]))
        print('%s total (one of each): %d tris, %d pieces' % (fam, total, len(self.tris)))


def rock_pts(rnd, c, rx, ry, h, z0=0.0, n=7, top=3, waist=(0.3, 0.55)):
    """Point cloud for a faceted boulder / rock lump (convex hull input)."""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.82, 1.0)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0))
    for i in range(n):
        a = (i + 0.5 + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.86, 1.06)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0 + h * rnd.uniform(*waist)))
    for i in range(top):
        a = rnd.uniform(0, 2 * math.pi)
        k = rnd.uniform(0.1, 0.62)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0 + h * rnd.uniform(0.78, 1.0)))
    return pts


def clamp_pts(pts, lim, ylim=None):
    ylim = lim if ylim is None else ylim
    return [(max(-lim, min(lim, x)), max(-ylim, min(ylim, y)), z) for x, y, z in pts]


def shutter_hull(pal, piece, h=3.05, w=3.0, d=0.14):
    """Gate shutters are flat-detail pieces: give them one outline box (hull only) so they read as a solid door."""
    m = Model(pal)
    m.box((0, 0, h / 2), (w, d, h), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(piece, tmp)
