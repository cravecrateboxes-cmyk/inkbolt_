"""INKBOLT enemy detail helpers (the modelled detail pass on the robots of fam_bots.py and the troopers of
fam_trooper.py). Same rules as the kit detail brief (docs/tactical-look/KIT-BRIEF.md):

  * everything here is deco: no ink outline of its own (fam_bots Part deco=True; for plain Models use `Deco` and
    `finish`), so detail never thickens the comic outline and costs half the triangles
  * a detail starts inside the face it sits on (EMBED) and stands at least 3 mm proud of it (PROUD), so the strict
    z-fighting check (ib_lib.check_zfight) passes; layered detail steps out 3 mm per layer
  * colours are existing palette cells only (no new cells)

Frames: most helpers draw in a local frame whose x / y span the face and whose +z is the face's outward normal, with
the face at z = 0 (`facet_frame` for a facet of a round body, `edge_frame` for fam_bots.on_edge style frames, or any
Matrix). `at(p, frame)` pushes a frame on a Part / Model (`p.parent`) for a `with` block.
"""
import math
from contextlib import contextmanager

import bmesh
import bpy
from mathutils import Matrix, Vector

import ib_lib

EMBED = 0.002     # how far a detail starts inside the face under it
PROUD = 0.004     # default height of a detail above the face under it (>= 3 mm: the z-fight rule)


@contextmanager
def at(p, frame):
    old = p.parent
    p.parent = old @ frame
    try:
        yield p
    finally:
        p.parent = old


def facet_frame(k, seg, r_body, z, phase=0.0, out=0.0):
    """Frame on facet k of a seg-sided round body around Z (r_body = its vertex radius at that height): x along the
    facet, y up, z outward; origin on the facet centre line at height z, `out` m off the facet."""
    a = phase + 2 * math.pi * (k + 0.5) / seg
    d = r_body * math.cos(math.pi / seg) + out
    n = Vector((math.cos(a), math.sin(a), 0.0))
    t = Vector((-math.sin(a), math.cos(a), 0.0))
    o = n * d + Vector((0, 0, z))
    m = Matrix.Identity(4)
    for r in range(3):
        m[r][0], m[r][1], m[r][2], m[r][3] = t[r], (0, 0, 1)[r], n[r], o[r]
    return m


def slope_frame(k, seg, a, b, t, phase=0.0, out=0.0):
    """Frame on facet k of a lathe band between profile points a = (r0, z0) and b = (r1, z1), at t along it (as
    fam_bots.Part.on_slope): x along the facet, y up the slope, z outward."""
    (r0, z0), (r1, z1) = a, b
    phi = math.atan2(r0 - r1, z1 - z0)
    r, z = r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
    ang = phase + 2 * math.pi * (k + 0.5) / seg
    n = Vector((math.cos(ang) * math.cos(phi), math.sin(ang) * math.cos(phi), math.sin(phi)))
    tx = Vector((-math.sin(ang), math.cos(ang), 0.0))
    ty = n.cross(tx).normalized()
    if ty.z < 0:
        ty = -ty
    o = Vector((math.cos(ang), math.sin(ang), 0)) * (r * math.cos(math.pi / seg)) + Vector((0, 0, z)) + n * out
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = tx[i], ty[i], n[i], o[i]
    if m.to_3x3().determinant() < 0:
        for i in range(3):
            m[i][0] = -m[i][0]
    return m


def axis_frame(origin, normal, up=(0, 0, 1)):
    """Frame at origin with +z along normal and +y toward `up` (projected)."""
    n = Vector(normal).normalized()
    u = Vector(up)
    if abs(u.normalized().dot(n)) > 0.98:
        u = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    y = (u - n * u.dot(n)).normalized()
    x = y.cross(n)
    m = Matrix((x, y, n)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


# ---------------------------------------------------------------- shapes in a face frame (z out of the face)
def pad(p, x, y, w, h, top=PROUD, color='gunmetal', base=0.0, rot=0.0, deco=True):
    """Flat plate on the face: from base - EMBED to base + top, w x h, rotated rot degrees about the normal."""
    z0, z1 = base - EMBED, base + top
    p.box((x, y, (z0 + z1) / 2), (w, h, z1 - z0), color, rot=(0, 0, rot), deco=deco)


def bolt(p, x, y, r=0.012, top=0.006, color='steel', base=0.0, seg=6, deco=True):
    """Hex bolt head on the face (a 6-sided stub along the normal)."""
    p.cyl((x, y, base - EMBED), r, r * 0.92, top + EMBED, color, seg=seg, deco=deco)


def bolts(p, pts, r=0.012, top=0.006, color='steel', base=0.0, seg=6):
    for x, y in pts:
        bolt(p, x, y, r, top, color, base, seg)


def bolt_row(p, x0, x1, y, n, **kw):
    bolts(p, [(x0 + (x1 - x0) * (i / (n - 1) if n > 1 else 0.5), y) for i in range(n)], **kw)


def grille(p, x, y, w, h, n, top=PROUD, color='ink', slat='gunmetal', base=0.0, vertical=False):
    """Vent: a dark recess plate with n slats standing 3 mm proud of it."""
    pad(p, x, y, w, h, top, color, base)
    s = (w if vertical else h) / n
    for i in range(n):
        c = -(w if vertical else h) / 2 + s * (i + 0.5)
        if vertical:
            pad(p, x + c, y, s * 0.45, h * 0.86, 0.003, slat, base + top)
        else:
            pad(p, x, y + c, w * 0.9, s * 0.45, 0.003, slat, base + top)


def stencil(p, x, y, w, h, n=3, color='ink', base=0.0, top=0.003):
    """Serial / stencil marks: a row of short painted bars."""
    for k in range(n):
        pad(p, x - w / 2 + (k + 0.5) * w / n, y, w / n * 0.55, h, top, color, base)


def serial_plate(p, x, y, w=0.08, h=0.035, color='paper', ink='ink', base=0.0):
    """A small riveted serial plate: plate, two text bars, two rivets."""
    pad(p, x, y, w, h, 0.004, color, base)
    pad(p, x - w * 0.08, y + h * 0.18, w * 0.6, h * 0.18, 0.003, ink, base + 0.004)
    pad(p, x - w * 0.16, y - h * 0.2, w * 0.44, h * 0.14, 0.003, ink, base + 0.004)
    for sx in (-1, 1):
        bolt(p, x + sx * w * 0.4, y, r=h * 0.12, top=0.003, color='steel', base=base + 0.004, seg=5)


def chevrons(p, x, y, w, h, n=4, color='amber', ink='ink', base=0.0):
    """Hazard stencil: amber plate with slanted ink bars (as fam_bots.hazard, at a point of a frame)."""
    pad(p, x, y, w, h, 0.004, color, base)
    s = w / n
    for k in range(n):
        cx = x - w / 2 + s * (k + 0.5)
        pad(p, cx, y, s * 0.4, h * 0.82, 0.003, ink, base + 0.004, rot=-30)


def lamp(p, x, y, r, lens='amber', rim='gunmetal', w=0.008, base=0.0, seg=8):
    """Lamp / sensor: a bezel disc (r + w) standing 4 mm proud and the lens 3 mm proud of the bezel."""
    p.cyl((x, y, base - EMBED), r + w, r + w, 0.004 + EMBED, rim, seg=seg, deco=True)
    p.cyl((x, y, base + 0.002), r, r * 0.9, 0.005, lens, seg=seg, deco=True)


# ---------------------------------------------------------------- round bodies and joints
def bolt_ring(p, cx, cy, z, R, n, r=0.011, h=0.008, color='steel', phase=0.0, seg=6):
    """n bolt heads standing on a flat face (normal +Z) at height z, on a circle of radius R."""
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        p.cyl((cx + R * math.cos(a), cy + R * math.sin(a), z - EMBED), r, r * 0.92, h + EMBED, color, seg=seg, deco=True)


def piston(p, a, b, r_body, r_rod, k=0.55, body='gunmetal', rod='steel', seg=6, deco=True):
    """Hydraulic piston from a to b: a cylinder body over the first k of the run and a thinner rod to the end."""
    a, b = Vector(a), Vector(b)
    m = a + (b - a) * k
    p.limb(tuple(a), tuple(m), r_body, r_body, body, seg=seg, deco=deco)
    p.limb(tuple(a + (b - a) * (k - 0.08)), tuple(b), r_rod, r_rod, rod, seg=seg, deco=deco)


def cable(p, pts, thick=0.012, color='ink', seg=5):
    """Cable / hose through points (thin round segments, deco; round so that bends never leave coplanar sides)."""
    for a, b in zip(pts, pts[1:]):
        p.limb(a, b, thick / 2, thick / 2, color, seg=seg, deco=True)


# ---------------------------------------------------------------- plain Models (the troopers): deco layer
class Deco:
    """A second Model for the small detail of a plain Model (no ink shell of its own). Build both with `finish`,
    which checks z-fighting across both and joins the deco (shell stripped) into the main object."""

    def __init__(self, pal):
        self.m = ib_lib.Model(pal)

    @property
    def parent(self):
        return self.m.parent

    @parent.setter
    def parent(self, v):
        self.m.parent = v

    def box(self, loc, size, color, rot=(0, 0, 0), bevel=False, deco=True):
        return self.m.box(loc, size, color, rot=rot, bevel=False)

    def cyl(self, loc, r1, r2, h, color, seg=8, rot=(0, 0, 0), bevel=False, caps=True, deco=True):
        return self.m.cyl(loc, r1, r2, h, color, seg=seg, rot=rot, bevel=False, caps=caps)

    def sphere(self, loc, r, color, seg=(8, 5), scale=(1, 1, 1), rot=(0, 0, 0), deco=True):
        return self.m.sphere(loc, r, color, seg=seg, scale=scale, rot=rot)

    def beam(self, a, b, thick, color, deco=True):
        return self.m.beam(a, b, thick, color)

    def limb(self, a, b, r1, r2, color, seg=6, deco=True, caps=True):
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        old = self.m.parent
        self.m.parent = old @ Matrix.Translation(a) @ q.to_matrix().to_4x4()
        self.m.cyl((0, 0, 0), r1, r2, d.length, color, seg=seg, bevel=False, caps=caps)
        self.m.parent = old


def check_models(name, models):
    """The strict z-fighting check over several Models together (shape ids kept apart)."""
    bm = bmesh.new()
    off = 0
    for mdl in models:
        me = bpy.data.meshes.new('_zchk')
        mdl.bm.to_mesh(me)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        lay = bm.faces.layers.int.get('shape_id')
        bm.faces.ensure_lookup_table()
        for i in range(n0, len(bm.faces)):
            bm.faces[i][lay] += off
        off += mdl.nshape + 1
    ib_lib.check_zfight(name, bm, bm.faces.layers.int.get('shape_id'))
    bm.free()


def finish(name, main, deco, bevel_w, hull_t):
    """build_object for a main Model plus its Deco layer: one z-fight check over both, the deco joined without a shell."""
    dm = deco.m if isinstance(deco, Deco) else deco
    if dm.nshape == 0:
        dm.bm.free()
        return ib_lib.build_object(name, main, bevel_w, hull_t)
    check_models(name, [main, dm])
    obj = ib_lib.build_object(name, main, bevel_w, hull_t)
    d = ib_lib.build_object(name + '_deco', dm, 0, hull_t)
    ib_lib.strip_hull(d)
    ib_lib.join_into(obj, d)
    return obj
