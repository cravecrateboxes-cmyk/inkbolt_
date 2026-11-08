"""INKBOLT in-world lettering: real vector glyphs from vendored OFL fonts (third_party/fonts, licences alongside).

A string is laid out once by Blender's text engine (a FONT curve, low curve resolution), filled, converted to a mesh,
triangulated and cached as 2D triangles normalised to a cap height of 1 (baseline at 0). draw() paints those triangles
as one flat, outline-free shape on any axis plane of a model (PM / Model, or a kit_base.Kit), optionally clipped to an
x-range (signs that span several wall modules), with an optional drop shadow a few mm behind for the comic ink look.

Fonts (all SIL OFL 1.1): 'display' Bebas Neue, 'cond' Oswald, 'serif' Playfair Display, 'script' Pacifico,
'sans' Inter Bold.
"""
import math
import os

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'third_party', 'fonts')
FONTS = {
    'display': 'BebasNeue-Regular.ttf',
    'cond': 'Oswald.ttf',
    'serif': 'PlayfairDisplay.ttf',
    'script': 'Pacifico-Regular.ttf',
    'sans': 'Inter-Bold.otf',
}
RES = {'display': 1, 'cond': 1, 'serif': 1, 'script': 1, 'sans': 2}
DISSOLVE = 28.0   # degrees: outline points on runs straighter than this are dropped
_FONT_DB = {}
_CACHE = {}
STATS = {'tris': 0}


def _font(key):
    if key not in _FONT_DB:
        _FONT_DB[key] = bpy.data.fonts.load(os.path.join(DIR, FONTS[key]), check_existing=True)
    return _FONT_DB[key]


def _raw(text, font, res, spacing):
    cu = bpy.data.curves.new('ib_text_tmp', type='FONT')
    cu.body = text
    cu.font = _font(font)
    cu.size = 1.0
    cu.resolution_u = res
    cu.space_character = spacing
    cu.fill_mode = 'BOTH'
    ob = bpy.data.objects.new('ib_text_tmp', cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    # budget: merge the fill into n-gons and drop outline points on near-straight runs, then re-triangulate
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(DISSOLVE), use_dissolve_boundaries=False,
                             verts=bm.verts[:], edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    tris = []
    for f in bm.faces:
        if f.calc_area() < 1e-7:
            continue
        p = [(v.co.x, v.co.y) for v in f.verts]
        # counter-clockwise in (u, v)
        s = (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[1][1] - p[0][1]) * (p[2][0] - p[0][0])
        tris.append(p if s > 0 else p[::-1])
    bm.free()
    return tris


def layout(text, font='sans', res=None, spacing=1.0):
    """(triangles, width, x0) normalised to cap height 1, baseline 0"""
    res = res or RES[font]
    key = (text, font, res, spacing)
    if key not in _CACHE:
        capkey = ('H', font, 3, 1.0, 'cap')
        if capkey not in _CACHE:
            ht = _raw('H', font, 3, 1.0)
            _CACHE[capkey] = max(y for t in ht for (_, y) in t)
        cap = _CACHE[capkey]
        tris = [[(x / cap, y / cap) for (x, y) in t] for t in _raw(text, font, res, spacing)]
        xs = [x for t in tris for (x, _) in t] or [0.0]
        _CACHE[key] = (tris, max(xs) - min(xs), min(xs))
    return _CACHE[key]


def width(text, font='sans', cap=1.0, res=None, spacing=1.0):
    return layout(text, font, res, spacing)[1] * cap


def _clip_x(poly, lo, hi):
    def cut(pts, keep, xv):
        out = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            ip, iq = keep(p[0]), keep(q[0])
            if ip:
                out.append(p)
            if ip != iq:
                t = (xv - p[0]) / (q[0] - p[0])
                out.append((xv, p[1] + (q[1] - p[1]) * t))
        return out
    pts = cut(poly, lambda x: x >= lo, lo)
    if len(pts) >= 3:
        pts = cut(pts, lambda x: x <= hi, hi)
    return pts if len(pts) >= 3 else None


# face -> (map (u, v, d) from text space to local coords, normal); d = offset along the normal
_FACES = {
    'y-': (lambda x, y, z, u, v, d: (x + u, y - d, z + v), (0, -1, 0)),
    'y+': (lambda x, y, z, u, v, d: (x - u, y + d, z + v), (0, 1, 0)),
    'x-': (lambda x, y, z, u, v, d: (x - d, y - u, z + v), (-1, 0, 0)),
    'x+': (lambda x, y, z, u, v, d: (x + d, y + u, z + v), (1, 0, 0)),
    'up': (lambda x, y, z, u, v, d: (x + u, y + v, z + d), (0, 0, 1)),
    'upr': (lambda x, y, z, u, v, d: (x - u, y - v, z + d), (0, 0, 1)),
}


def _model(m):
    """the ib_lib.Model behind m (a kit_base.Kit wraps one as .m)"""
    return m.m if isinstance(getattr(m, 'flat', None), set) and hasattr(m, 'm') else m


def _tag(m, faces, color):
    """one flat, outline-free shape (PM hmode 'none' / Kit flat set / classroom K nh set)"""
    model = _model(m)
    model.nshape += 1
    ci = model.pal.index(color)
    for f in faces:
        f[model.shape] = model.nshape
        f.material_index = ci
    if model is not m:
        m.flat.add(model.nshape)
    if hasattr(model, 'hmode'):
        model.hmode[model.nshape] = 'none'
    if isinstance(getattr(model, 'nh', None), set):
        model.nh.add(model.nshape)


def draw(m, text, x, y, z, cap, color, face='y-', font='sans', align='c', valign='b', maxw=None, clip=None,
         res=None, spacing=1.0, shadow=None, shadow_off=(0.06, -0.08), slant=0.0):
    """Paint `text` with its baseline (valign 'b') or cap middle ('m') at (x, y, z) on the given axis plane.
    cap: cap height in metres (shrunk to fit maxw). clip: (u0, u1) range along the reading direction relative to x
    (for signs split over several modules). shadow: colour of a drop shadow 4 mm behind (offset in cap units).
    Returns the drawn width."""
    tris, w, x0 = layout(text, font, res, spacing)
    s = cap
    if maxw and w * s > maxw:
        s = maxw / w
    ou = {'c': -w / 2, 'l': 0.0, 'r': -w}[align] - x0
    ov = {'b': 0.0, 'm': -0.5, 't': -1.0}[valign]
    fmap, nrm = _FACES[face]
    model = _model(m)
    P = model.parent
    N = P.to_3x3() @ Vector(nrm)
    layers = [(0.0, 0.0, 0.004 if shadow else 0.0, color)]
    if shadow:   # the shadow sits on the given plane, the letters 4 mm in front of it
        layers.insert(0, (shadow_off[0] * s, shadow_off[1] * s, 0.0, shadow))
    for (du, dv, dd, col) in layers:
        faces = []
        for t in tris:
            pts = [((u + ou) * s + du + slant * (v + ov) * s, (v + ov) * s + dv) for (u, v) in t]
            if clip:
                pts = _clip_x(pts, clip[0], clip[1])
                if not pts:
                    continue
            vs = [model.bm.verts.new(P @ Vector(fmap(x, y, z, u, v, dd))) for (u, v) in pts]
            f = model.bm.faces.new(vs)
            f.normal_update()
            if f.normal.dot(N) < 0:
                f.normal_flip()
            faces.append(f)
        if faces:
            _tag(m, faces, col)
            STATS['tris'] += sum(len(f.verts) - 2 for f in faces)
    return w * s
