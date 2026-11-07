"""Small helpers shared by the round-2 theme kits (kit-mall, kit-police, kit-grove).

finish(prefix, tris, name, model, ao, bevel, hull_t, cols): build + outline + per-piece collision empties
(<Piece>_COL<n>: cube empties, location = box centre, scale = half extents, all in Blender coordinates).
Conventions as zones.js: a piece's origin is the centre of its cell / footprint on the floor; Blender -Y = game +Z
(the piece's front, toward the room / the zone entry); Blender Z = up.
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector

from ib_lib import Model, build_object


def finish(prefix, tris, name, m, ao, bevel=0.0, hull_t=0.02, cols=None):
    full = prefix + name
    obj = build_object(full, m, bevel, hull_t, ao=ao)
    tris[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, (c, hlf) in enumerate(cols or []):
        e = bpy.data.objects.new('%s_COL%d' % (full, i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def col_box(x0, y0, z0, x1, y1, z1):
    """collision box from two corners (Blender coords) -> (centre, half extents)"""
    return (((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2))


def tag(m, faces, color=None):
    m.nshape += 1
    ci = m.pal.index(color) if color else None
    for f in faces:
        f[m.shape] = m.nshape
        if ci is not None:
            f.material_index = ci
    return faces


def hull_pts(m, pts, color):
    """convex hull of points as one shape; color = palette name or fn(face) -> name"""
    vs = [m.bm.verts.new(m.parent @ Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(m.bm, input=vs)
    faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
    for g in res.get('geom_interior', []) + res.get('geom_unused', []):
        if isinstance(g, bmesh.types.BMVert) and g.is_valid and not g.link_faces:
            m.bm.verts.remove(g)
    m.bm.normal_update()
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
        f.material_index = m.pal.index(color(f) if callable(color) else color)
    return faces


def blob(m, c, r, color, seg=(9, 6), scale=(1, 1, 1)):
    return m.sphere(c, r, color, seg=seg, scale=scale)


def ring_pts(cx, cy, r, n, z, phase=0.0, jitter=None):
    out = []
    for i in range(n):
        a = phase + i / n * 2 * math.pi
        rr = r * (jitter[i % len(jitter)] if jitter else 1.0)
        out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, z))
    return out
