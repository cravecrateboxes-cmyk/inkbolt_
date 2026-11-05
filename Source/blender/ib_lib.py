"""INKBOLT Blender helpers shared by every asset family (palette, modelling, outline shell, AO, export, checks)."""
import math
import os
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets'))

# ---------------------------------------------------------------- palettes
BASE = [
    ('HULL', '#15121C'), ('ink', '#15121C'), ('paper', '#FFFDF7'), ('white', '#FFFFFF'),
    ('teal', '#12C7B6'), ('amber', '#FFB21E'), ('gunmetal', '#2B2A33'), ('red', '#F0443A'),
]
PALETTES = {}   # family -> [(name, hex)], registered by each fam_*.py module (BASE first)


GLB = {'common': 'fps-common.glb', 'weapons': 'fps-weapons.glb', 'bots': 'fps-bots.glb', 'kit-toytown': 'fps-kit-toytown.glb'}
# family settings: bevel width (m), outline shell thickness (m) -- brief 2.2
CFG = {'common': (0.02, 0.02), 'weapons': (0.004, 0.006), 'bots': (0.012, 0.015), 'kit-toytown': (0.02, 0.02)}


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


CURRENT_FAMILY = [None]


class Palette:
    def __init__(self, family):
        CURRENT_FAMILY[0] = family
        self.family = family
        self.names = [n for n, _ in PALETTES[family]]
        img = bpy.data.images.new('PAL_' + family, 64, 64, alpha=True)
        px = [0.0] * (64 * 64 * 4)
        for i, (_, hx) in enumerate(PALETTES[family]):
            r, g, b = hex2rgb(hx)
            cx, cy = (i % 8) * 8, (i // 8) * 8
            for y in range(cy, cy + 8):
                for x in range(cx, cx + 8):
                    k = (y * 64 + x) * 4
                    px[k:k + 4] = [r, g, b, 1.0]
        img.pixels.foreach_set(px)
        img.update()
        # write a real PNG (Source/blender/palettes/) and pack that file: generated pixels alone don't pack
        os.makedirs(os.path.join(HERE, 'palettes'), exist_ok=True)
        path = os.path.join(HERE, 'palettes', 'PAL_%s.png' % family)
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        bpy.data.images.remove(img)
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = 'sRGB'
        img.pack()
        self.image = img
        mat = bpy.data.materials.new('PAL_' + family)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = img
        tex.interpolation = 'Closest'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 1.0
        self.material = mat

    def index(self, name):
        return self.names.index(name)

    def uv(self, idx):
        return ((idx % 8) + 0.5) / 8.0, ((idx // 8) + 0.5) / 8.0


# ---------------------------------------------------------------- modelling
def mat_trs(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot], 'XYZ').to_matrix().to_4x4()
            @ Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1.0))))


class Model:
    """Shapes in a bmesh; colour = palette name stored as material index; bevel flag as edge weight."""

    def __init__(self, pal):
        self.pal = pal
        self.bm = bmesh.new()
        self.bw = self.bm.edges.layers.float.new('bevel_weight_edge')
        self.shape = self.bm.faces.layers.int.new('shape_id')
        self.nshape = 0
        self.parent = Matrix.Identity(4)

    def _finish(self, verts, color, bevel):
        faces = {f for v in verts for f in v.link_faces}
        mi = self.pal.index(color)
        self.nshape += 1
        for f in faces:
            f.material_index = mi
            f[self.shape] = self.nshape
        if bevel:
            for f in faces:
                for e in f.edges:
                    e[self.bw] = 1.0
        return faces

    def box(self, loc, size, color, rot=(0, 0, 0), bevel=True):
        m = self.parent @ mat_trs(loc, rot, size)
        return self._finish(bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)['verts'], color, bevel)

    def cyl(self, loc, r1, r2, h, color, seg=12, rot=(0, 0, 0), bevel=True, caps=True):
        """Z-aligned frustum with its base at loc (before rotation)."""
        m = self.parent @ mat_trs(loc, rot) @ Matrix.Translation((0, 0, h / 2))
        v = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=m)['verts']
        return self._finish(v, color, bevel)

    def sphere(self, loc, r, color, seg=(10, 6), scale=(1, 1, 1), rot=(0, 0, 0)):
        m = self.parent @ mat_trs(loc, rot, scale)
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=seg[0], v_segments=seg[1], radius=r, matrix=m)['verts']
        return self._finish(v, color, False)

    def beam(self, a, b, thick, color, bevel=False):
        """Box from point a to point b with square section."""
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        m = self.parent @ Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal(Vector((thick, thick, d.length, 1)))
        return self._finish(bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)['verts'], color, bevel)


def build_object(name, model, bevel_w, hull_t, ao=False, collection=None):
    """Turn a Model into one exported mesh object: bevel -> UV cells -> AO -> outline shell."""
    pal = model.pal
    check_zfight(name, model.bm, model.shape)
    # bevel only real corners (> 40 degrees); smooth curves (cylinder sides, spheres) stay unbevelled
    for e in model.bm.edges:
        if e[model.bw] > 0 and (len(e.link_faces) != 2 or e.calc_face_angle(0.0) < math.radians(40)):
            e[model.bw] = 0.0
    me = bpy.data.meshes.new(name)
    model.bm.to_mesh(me)
    model.bm.free()
    obj = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.data.materials.append(pal.material)
    # bevel (weighted edges only), applied
    if bevel_w > 0:
        mod = obj.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel_w
        mod.segments = 2
        mod.limit_method = 'WEIGHT'
        mod.material = -1
        mod.harden_normals = False
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        obj.modifiers.clear()
        old = obj.data
        obj.data = new
        bpy.data.meshes.remove(old)
        new.name = name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    col = bm.loops.layers.float_color.new('Col')
    for f in bm.faces:
        u, v = pal.uv(f.material_index)
        f.smooth = True
        for l in f.loops:
            l[uvl].uv = (u, v)
            l[col] = (1.0, 1.0, 1.0, 1.0)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40):
            e.smooth = False
        elif len(e.link_faces) != 2:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    if ao:
        bake_ao(obj)
    add_hull(obj, pal, hull_t)
    for p in obj.data.polygons:
        p.material_index = 0
    obj.data.color_attributes.active_color = obj.data.color_attributes['Col']
    return obj


def add_hull(obj, pal, t):
    """Inverted outline shell with even thickness, joined into the same mesh (brief 3.3)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uvl = bm.loops.layers.uv['UVMap']
    col = bm.loops.layers.float_color['Col']
    hull = bm.verts.layers.float_vector.new('_HULL')
    faces = list(bm.faces)
    dup = bmesh.ops.duplicate(bm, geom=faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts}))
    nf = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
    bm.normal_update()
    moves = {}
    for v in nv:
        ns = []
        for f in v.link_faces:
            n = f.normal
            if n.length > 0.5 and not any(abs(n.dot(m)) > 0.9999 for m in ns):
                ns.append(n.copy())
        if not ns:
            continue
        d = Vector((0, 0, 0))
        for n in ns:
            d += n
        if d.length < 1e-6:
            d = ns[0].copy()
        d.normalize()
        k = min(max(d.dot(n), 0.34) for n in ns)
        moves[v] = d * (1.0 / k)
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
        f.smooth = True   # outline normals are unused; smooth keeps shell vertices shared
        for l in f.loops:
            l[uvl].uv = (hu, hv)
            l[col] = (1.0, 1.0, 1.0, 1.0)
    bm.to_mesh(obj.data)
    bm.free()


_ao_ready = {'ok': None}


def bake_ao(obj):
    """Cycles AO bake into the 'Col' attribute, posterised to 2 steps (1.0 / 0.82)."""
    if _ao_ready['ok'] is False:
        return
    sc = bpy.context.scene
    try:
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = 24
        sc.cycles.device = 'CPU'
        # every piece is modelled at the origin: bake each one alone so the others don't occlude it
        hidden = []
        for o in sc.objects:
            o.select_set(False)
            if o is not obj and not o.hide_render:
                o.hide_render = True
                hidden.append(o)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.data.color_attributes.active_color = obj.data.color_attributes['Col']
        bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
        for o in hidden:
            o.hide_render = False
        _ao_ready['ok'] = True
    except Exception as e:  # keep going without AO rather than fail the build
        print('AO bake unavailable:', e)
        _ao_ready['ok'] = False
        return
    attr = obj.data.color_attributes['Col']
    for c in attr.data:
        v = sum(c.color[:3]) / 3.0
        s = 1.0 if v > 0.72 else 0.87   # softer baked shadow (lighter tones)
        c.color = (s, s, s, 1.0)


def socket(name, parent, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.02
    e.parent = parent
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def export(family):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, GLB[family])
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              export_vertex_color='NAME', export_vertex_color_name='Col', export_all_vertex_colors=False, export_attributes=True,
                              export_texcoords=True, export_normals=True, export_tangents=False, export_cameras=False,
                              export_lights=False, export_animations=True, export_animation_mode='ACTIONS',
                              export_skins=True, export_def_bones=False, export_force_sampling=True,
                              export_image_format='AUTO', export_extras=False)
    raw = os.path.getsize(path)
    sys.path.insert(0, HERE)
    import quantize_glb
    quantize_glb.quantize(path)
    print('wrote', path, raw, '->', os.path.getsize(path), 'bytes (quantized)')
    return path




def strip_hull(obj):
    """Remove the outline shell (flat painted marks / all-ink pieces do not need one)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    kill = [v for v in bm.verts if hl and v[hl].length > 0]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


def hull_only(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    kill = [v for v in bm.verts if v[hl].length == 0]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


def join_into(dst, src):
    bm = bmesh.new()
    bm.from_mesh(dst.data)
    bm.from_mesh(src.data)
    bm.to_mesh(dst.data)
    bm.free()
    bpy.data.objects.remove(src)


# ---------------------------------------------------------------- z-fighting guard
ZFIGHT_TOL = 0.0025      # faces of different shapes closer than 2.5 mm, same facing, overlapping -> error
ZFIGHT_AREA = 2e-6       # m^2 of overlap that counts
ZFIGHT_STRICT = {}       # family -> False only while a family is being remodelled (prints instead of failing)


class ZFightError(Exception):
    pass


def _clip(poly, a, b):
    """Sutherland-Hodgman: keep the part of convex poly left of edge a->b (2D)."""
    out = []
    def side(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def _ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if s > 0 else list(reversed(poly))


def check_zfight(name, bm, shape_layer):
    """Fail the build if two different shapes have coplanar, same-facing, overlapping faces (they would flicker)."""
    bm.normal_update()
    buckets = {}
    for f in bm.faces:
        if f.calc_area() < 1e-8:
            continue
        n = f.normal
        if n.z < -0.99 and all(abs(p.co.z) < 1e-4 for p in f.verts):
            continue   # bottom faces resting on the ground plane are never visible
        key = (round(n.x, 2), round(n.y, 2), round(n.z, 2))
        buckets.setdefault(key, []).append((n.dot(f.verts[0].co), f))
    bad = []
    for key, lst in buckets.items():
        if len(lst) < 2:
            continue
        lst.sort(key=lambda t: t[0])
        n = Vector(key).normalized()
        u = n.orthogonal().normalized()
        v = n.cross(u)
        proj = {}
        for i in range(len(lst)):
            di, fi = lst[i]
            for j in range(i + 1, len(lst)):
                dj, fj = lst[j]
                if dj - di > ZFIGHT_TOL:
                    break
                if fi[shape_layer] == fj[shape_layer]:
                    continue
                for f in (fi, fj):
                    if f not in proj:
                        proj[f] = _ccw([(p.co.dot(u), p.co.dot(v)) for p in f.verts])
                pa, pb = proj[fi], proj[fj]
                inter = pa
                for k in range(len(pb)):
                    inter = _clip(inter, pb[k], pb[(k + 1) % len(pb)])
                    if len(inter) < 3:
                        break
                if len(inter) >= 3 and _area(inter) > ZFIGHT_AREA:
                    c = fi.calc_center_median()
                    bad.append('%s: shapes %d/%d coplanar at (%.3f, %.3f, %.3f) normal %s' % (name, fi[shape_layer], fj[shape_layer], c.x, c.y, c.z, key))
    if bad and ZFIGHT_STRICT.get(CURRENT_FAMILY[0], True) is False:
        print('Z-FIGHT WARNING (non-strict family):\n  ' + '\n  '.join(bad[:6]))
        return
    if bad:
        raise ZFightError('z-fighting faces (move details >= 3 mm proud or inset):\n  ' + '\n  '.join(bad[:12]) + ('\n  ...' if len(bad) > 12 else ''))
