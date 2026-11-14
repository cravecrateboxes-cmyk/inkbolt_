"""INKBOLT sculpted shape helpers for the trooper family (fam_trooper.py): rounded / chamfered boxes, curved armour
plates, chamfered prisms (angular plates cut from a polygon), tapered limbs and rounded or faceted cylinders,
emitted into an ib_lib.Model (or an enemy_detail.Deco) like Model.box.

Every shape is modelled in a small bmesh of its own (subdivided, bevelled with bmesh.ops.bevel, then warped in its
local frame), then copied into the Model with the Model's parent and the shape's loc / rot, as ONE shape (one
shape_id, one colour). The shapes carry no bevel weight: their edges are already rounded or chamfered, so
build_object's bevel modifier leaves them alone. Rounds use 2 segments (each step <= 30 degrees, so they shade smooth
under the 40-degree sharp-edge rule); chamfers use 1 segment (each step 45 degrees, a crisp bevelled edge).

Local warps (all in metres, in the shape's own frame before loc / rot):
  top / bot   taper: (fx, fy) scale of x / y at the +z / -z end (linear in z between)
  puff        (px, py, pz): pillow the faces outward, px m at the middle of the +-x faces, nothing at their rims
  curve       [(i, j, sag), ...]: displace axis i by sag x (j / half-size_j)^2 (a plate bent round axis j's ends)
  warp        any callable Vector -> Vector, applied last
`warped(model, fn)` bends every shape added inside the block with one function in the Model's space (a plate and the
detail that sits on it bend together, so the detail stays proud of the plate).
"""
import math
from contextlib import contextmanager

import bmesh
from mathutils import Matrix, Vector

import ib_lib

AX = {'x': 0, 'y': 1, 'z': 2}


def _model(m):
    """the ib_lib.Model behind m (a Model or an enemy_detail.Deco)"""
    return getattr(m, 'm', m) if not isinstance(m, ib_lib.Model) else m


def emit(m, src, M, color):
    """copy the bmesh `src` into model m with the 4x4 transform M (m.parent is applied here) as one shape"""
    mm = _model(m)
    T = mm.parent @ M
    # warped quads are no longer flat: split them (the export triangulates them anyway) so that every face is planar,
    # its normal exact for the z-fight check and for snapping detail onto it
    src.normal_update()
    bent = [f for f in src.faces if len(f.verts) > 3 and
            max(abs((v.co - f.verts[0].co).dot(f.normal)) for v in f.verts) > 2e-5]
    if bent:
        bmesh.ops.triangulate(src, faces=bent, quad_method='BEAUTY', ngon_method='BEAUTY')
    vmap = {}
    for v in src.verts:
        vmap[v] = mm.bm.verts.new(T @ v.co)
    for f in src.faces:
        try:
            mm.bm.faces.new([vmap[v] for v in f.verts])
        except ValueError:   # a duplicate face (never expected); skip rather than fail
            pass
    src.free()
    return mm._finish(list(vmap.values()), color, False)


def _bevel(bm, r, seg, axes=None, min_deg=60.0, prof=0.5):
    """bevel the sharp edges (face angle > min_deg) of bm; axes ('x', 'yz' ...) keeps only edges running along them"""
    if r <= 0:
        return
    edges = []
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_face_angle(0.0) < math.radians(min_deg):
            continue
        if axes:
            d = (e.verts[1].co - e.verts[0].co).normalized()
            if not any(abs(d[AX[a]]) > 0.95 for a in axes):
                continue
        edges.append(e)
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=r, offset_type='OFFSET', profile_type='SUPERELLIPSE', segments=seg,
                        profile=prof, affect='EDGES', clamp_overlap=True, loop_slide=True)


def _subdivide(bm, cuts, size):
    for i, n in enumerate(cuts):
        if n <= 0:
            continue
        es = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized()[i]) > 0.99]
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=n, use_grid_fill=True)


def _warp_point(p, h, top=None, bot=None, puff=None, curve=None, warp=None):
    a = [p[i] / h[i] for i in range(3)]
    if puff:
        q = Vector(p)
        for i in range(3):
            if puff[i]:
                j, k = [n for n in range(3) if n != i]
                fall = max(0.0, 1 - a[j] ** 2) * max(0.0, 1 - a[k] ** 2)
                q[i] += math.copysign(puff[i] * fall * min(1.0, abs(a[i])), p[i])
        p = q
    if top or bot:
        t = (max(-1.0, min(1.0, a[2])) + 1) / 2
        tf, bf = top or (1, 1), bot or (1, 1)
        p = Vector((p.x * (bf[0] + (tf[0] - bf[0]) * t), p.y * (bf[1] + (tf[1] - bf[1]) * t), p.z))
    if curve:
        p = Vector(p)
        for i, j, sag in curve:
            i, j = AX.get(i, i), AX.get(j, j)
            p[i] += sag * min(1.0, a[j] ** 2)
    if warp:
        p = warp(Vector(p))
    return Vector(p)


def _shape(bm, size, top=None, bot=None, puff=None, curve=None, warp=None):
    h = [max(s / 2, 1e-6) for s in size]
    for v in bm.verts:
        v.co = _warp_point(Vector(v.co), h, top, bot, puff, curve, warp)


def face_frame(loc, size, face, u=0.0, v=0.0, rot=(0, 0, 0), top=None, bot=None, puff=None, curve=None, warp=None, on=None,
               **_):
    """frame on the face ('-y', '+x' ...) of an rbox with the same loc / size / rot / warps, at (u, v) metres across
    the face (u, v = x, z on a y face; y, z on an x face; x, y on a z face), +z out of the warped surface. Put the
    plate's detail in it with enemy_detail.at so the detail follows the curved plate. Keep (u, v) off the rounded
    rims (the frame sits on the face plane before rounding). Other rbox keywords (r, cuts ...) are ignored.
    on = the faces rbox returned for that plate (or the whole Model): the frame is snapped onto the real (faceted) surface and takes the
    facet's exact normal, so the detail's faces stay parallel to the facet under them (the z-fight check compares
    plane offsets, which a slightly different normal skews far from the origin)."""
    k, sgn = AX[face[1]], (1 if face[0] == '+' else -1)
    i, j = [n for n in range(3) if n != k]
    h = [max(s / 2, 1e-6) for s in size]

    def at(uu, vv):
        p = Vector((0, 0, 0))
        p[k], p[i], p[j] = sgn * h[k], uu, vv
        return _warp_point(p, h, top, bot, puff, curve, warp)
    o = at(u, v)
    e = 1e-3
    du, dv = at(u + e, v) - at(u - e, v), at(u, v + e) - at(u, v - e)
    n = du.cross(dv).normalized()
    ax = Vector((0, 0, 0)); ax[k] = sgn
    if n.dot(ax) < 0:
        n = -n
    x = du.normalized()
    y = n.cross(x).normalized()
    x = y.cross(n)
    F = Matrix((x, y, n)).transposed().to_4x4()
    F.translation = o
    F = ib_lib.mat_trs(loc, rot) @ F
    return snap(F, on) if on else F


def snap(F, faces, reach=0.04):
    """move frame F along its z onto the nearest facet of `faces` (bmesh faces) and align its z with that facet"""
    from mathutils.bvhtree import BVHTree
    if not isinstance(faces, (set, list, tuple)):
        faces = _model(faces).bm.faces       # a Model: snap onto whatever of it is outermost along the ray
    fl = [f for f in faces if f.is_valid]
    vs = list({v for f in fl for v in f.verts})
    ix = {v: i for i, v in enumerate(vs)}
    tree = BVHTree.FromPolygons([v.co for v in vs], [[ix[v] for v in f.verts] for f in fl])
    o, n = F.translation.copy(), F.col[2].to_3d().normalized()
    hit = tree.ray_cast(o + n * reach, -n, 2 * reach)
    if hit[0] is None:
        return F
    loc, nrm = hit[0], hit[1].normalized()
    if nrm.dot(n) < 0:
        nrm = -nrm
    x = F.col[0].to_3d()
    x = (x - nrm * x.dot(nrm)).normalized()
    y = nrm.cross(x)
    G = Matrix((x, y, nrm)).transposed().to_4x4()
    G.translation = loc
    return G


def rbox(m, loc, size, color, rot=(0, 0, 0), r=0.02, seg=2, axes=None, cuts=(0, 0, 0), top=None, bot=None,
         puff=None, curve=None, warp=None, cham=None):
    """box (centre loc, size) with its edges rounded (r, 2 segments) or chamfered (cham=w: 1 segment); axes limits
    the rounding to edges running along those local axes; then the local warps (see the module docstring)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal(Vector((size[0], size[1], size[2], 1.0))))
    _subdivide(bm, cuts, size)
    if cham:
        r, seg = cham, 1
    r = min(r, min(size) * 0.48 if not axes else min(size[i] for i in range(3) if 'xyz'[i] not in axes) * 0.48)
    _bevel(bm, r, seg, axes)
    _shape(bm, size, top, bot, puff, curve, warp)
    return emit(m, bm, ib_lib.mat_trs(loc, rot), color)


def rcyl(m, loc, r1, r2, h, color, seg=12, rot=(0, 0, 0), cham=0.0, cseg=1, caps=True, cuts=0, warp=None, phase=0.0):
    """Z frustum with its base at loc (as Model.cyl), rims chamfered (cseg 1) or rounded (cseg 2) by cham; phase
    turns the sides about the axis (degrees: 180 / seg puts a flat, not a corner, on the local x / y axes)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h,
                          matrix=Matrix.Translation((0, 0, h / 2)) @ Matrix.Rotation(math.radians(phase), 4, 'Z'))
    if cuts:
        es = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().z) > 0.5]
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=cuts, use_grid_fill=False)
    if caps and cham > 0:
        _bevel(bm, min(cham, h * 0.45, min(r1, r2) * 0.6), cseg, min_deg=50.0)
    if warp:
        for v in bm.verts:
            v.co = warp(Vector(v.co))
    return emit(m, bm, ib_lib.mat_trs(loc, rot), color)


def prism(m, loc, poly, depth, color, axis='y', rot=(0, 0, 0), cham=0.0, s0=None, s1=None, min_deg=25.0):
    """an angular plate: the convex polygon poly [(u, v), ...] (around the origin, in the plane across `axis`:
    u, v = x, z for axis y; y, z for axis x; x, y for axis z) extruded `depth` along `axis`, centred on loc. s0 / s1
    = (fu, fv) scale the cap on the -axis / +axis side (a raked plate whose outer face is smaller than its base).
    Every edge sharper than min_deg is chamfered by cham with ONE segment: flat faces, crisp bevelled edges."""
    k = AX[axis]
    i, j = [n for n in range(3) if n != k]
    bm = bmesh.new()

    def cap(w, sc):
        out = []
        for u, v in poly:
            p = [0.0, 0.0, 0.0]
            p[i], p[j], p[k] = u * sc[0], v * sc[1], w
            out.append(bm.verts.new(p))
        return out
    a, b = cap(-depth / 2, s0 or (1, 1)), cap(depth / 2, s1 or (1, 1))
    n = len(poly)
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for q in range(n):
        bm.faces.new((a[q], b[q], b[(q + 1) % n], a[(q + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if cham > 0:
        _bevel(bm, min(cham, depth * 0.45), 1, min_deg=min_deg)
    return emit(m, bm, ib_lib.mat_trs(loc, rot), color)


def rlimb(m, a, b, r1, r2, color, seg=10, cham=0.0, cseg=1, caps=True, cuts=0, roll=0.0):
    """rounded frustum from point a (radius r1) to b (r2)"""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    M = Matrix.Translation(a) @ q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(roll), 4, 'Z')
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=d.length,
                          matrix=Matrix.Translation((0, 0, d.length / 2)))
    if cuts:
        es = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().z) > 0.5]
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=cuts, use_grid_fill=False)
    if caps and cham > 0:
        _bevel(bm, min(cham, d.length * 0.45, min(r1, r2) * 0.6), cseg, min_deg=50.0)
    return emit(m, bm, M, color)


def ell(m, loc, r, color, seg=(12, 7), scale=(1, 1, 1), rot=(0, 0, 0), zmin=None):
    """ellipsoid (UV sphere radius r, scaled); zmin (in units of r, -1..1) cuts it flat below that height and caps
    the cut, for domes and round shells"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=r)
    if zmin is not None:
        cut = [v for v in bm.verts if v.co.z < zmin * r - 1e-6]
        ring = [v for v in bm.verts if abs(v.co.z - zmin * r) < 1e-6]
        if cut:
            bmesh.ops.delete(bm, geom=cut, context='VERTS')
        if not ring:     # no latitude exactly at the cut: flatten the lowest ring onto it
            lo = min(v.co.z for v in bm.verts)
            for v in bm.verts:
                if abs(v.co.z - lo) < 1e-6:
                    v.co.z = zmin * r
        bnd = [e for e in bm.edges if e.is_boundary]
        if bnd:
            bmesh.ops.edgeloop_fill(bm, edges=bnd)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return emit(m, bm, ib_lib.mat_trs(loc, rot), color)


@contextmanager
def warped(m, fn):
    """bend every vertex added to model m inside the block with fn (Vector -> Vector, in the Model's space)"""
    mm = _model(m)
    before = set(mm.bm.verts)
    try:
        yield m
    finally:
        for v in mm.bm.verts:
            if v not in before:
                v.co = fn(Vector(v.co))


def bend(axis_out, axis_along, centre, sag, half):
    """a warp that pushes axis_out by sag x ((axis_along - centre) / half)^2 (a plate curving back toward its sides)"""
    i, j = AX[axis_out], AX[axis_along]

    def fn(p):
        t = (p[j] - centre) / half
        p[i] += sag * t * t
        return p
    return fn
