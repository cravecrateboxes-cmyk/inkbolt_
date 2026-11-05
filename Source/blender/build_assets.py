"""INKBOLT procedural asset build (Blender as a Python module: `pip install bpy`).

    python3 build_assets.py                 # every family
    python3 build_assets.py --family bots   # one family: common | weapons | bots | kit-toytown
    python3 build_assets.py --no-ao         # skip the Cycles AO bake (faster)

Each family is one GLB in Source/assets/ (fps-common.glb, fps-weapons.glb, fps-bots.glb, fps-kit-toytown.glb):
  * one 64x64 palette texture per family (8x8 cells, nearest filtering); UVs point at palette cells
  * chunky bevels (bevel modifier, 2 segments) on silhouette shapes, sharp edges above 40 degrees
  * baked ink outline (brief 3.3): an inverted shell offset along even-thickness normals, reversed winding,
    mapped to the palette's HULL cell, joined into the same mesh -> one mesh, one material, one draw call.
    The shell's offset direction is exported as the custom attribute _HULL so the game can widen
    outlines with distance.
  * static kit props get a Cycles AO bake into the vertex colour, posterised to 2 steps
  * sockets are empties parented to their part (MUZZLE, MAG, EJECT, CORE, HIP0..3 ...)
  * the arms are one skinned mesh on a 22-bone rig with per-weapon actions (<WEAPON>_Idle, _Draw, ...)
Blender is Z-up; the exporter converts to glTF Y-up. Game forward (-Z) is Blender +Y for the viewmodel,
robots face game +Z (Blender -Y).
"""
import argparse
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
PALETTES = {
    'common': BASE + [('cloud', '#FFFDF7'), ('cloudshade', '#EDE6F2'), ('hill', '#7FC47A'), ('hill2', '#9AD38A'),
                      ('pine', '#3F8F6A'), ('trunk', '#8A5A3B'), ('canbody', '#8C93A0'), ('canlid', '#6E7480'),
                      ('canband', '#5E6470'), ('dull', '#E9DFC8')],
    'weapons': BASE + [('gun2', '#4A4858'), ('glove', '#4E4B5C'), ('glove2', '#5C5970'), ('sleeve', '#5B4E8F'),
                       ('sleeve2', '#6A5DA3'), ('chip', '#FFFFFF'), ('ammo', '#2F7BEA'), ('ammo2', '#1E559F'),
                       ('health', '#5BCF4A'), ('health2', '#3E9C33'), ('steel', '#8C93A0')],
    'bots': BASE + [('tin', '#C9CFD6'), ('tin2', '#A9B0BA'), ('rust', '#D9663B'), ('spring', '#8C93A0'),
                    ('core', '#FFC23A'), ('light', '#FFFFFF')],
    'kit-toytown': BASE + [('tangerine', '#FF8A3D'), ('bubblegum', '#FF7FB0'), ('purple', '#8A6CD8'), ('purple2', '#6A55B8'),
                           ('sky', '#5BC0EB'), ('sand', '#F6D57A'), ('coral', '#F26B5B'), ('trim', '#F4EEE2'),
                           ('window', '#8ED2FF'), ('door', '#3B3550'), ('crate2', '#C8642A'), ('lowwall', '#D8D2C4'),
                           ('lowtop', '#EAE5D8'), ('tank', '#F4EEE2'), ('pad', '#E6DCC6'), ('ground', '#F6D57A'),
                           ('canbody', '#8C93A0'), ('canlid', '#6E7480')],
}
GLB = {'common': 'fps-common.glb', 'weapons': 'fps-weapons.glb', 'bots': 'fps-bots.glb', 'kit-toytown': 'fps-kit-toytown.glb'}
# family settings: bevel width (m), outline shell thickness (m) -- brief 2.2
CFG = {'common': (0.02, 0.02), 'weapons': (0.004, 0.006), 'bots': (0.012, 0.015), 'kit-toytown': (0.02, 0.02)}


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


class Palette:
    def __init__(self, family):
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
        self.parent = Matrix.Identity(4)

    def _finish(self, verts, color, bevel):
        faces = {f for v in verts for f in v.link_faces}
        mi = self.pal.index(color)
        for f in faces:
            f.material_index = mi
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
        s = 1.0 if v > 0.72 else 0.82
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


# ================================================================ COMMON
def build_common(ao):
    pal = Palette('common')
    bw, ht = CFG['common']
    # clouds: three puff shapes
    for name, puffs in (('Cloud_A', [(0, 0, 0, 2.2), (2.2, 0.2, -0.3, 1.6), (-2.1, 0, -0.4, 1.5)]),
                        ('Cloud_B', [(0, 0, 0, 1.8), (1.7, 0.3, -0.2, 1.3), (-1.5, -0.2, -0.3, 1.2)]),
                        ('Cloud_C', [(0, 0, 0, 2.6), (2.7, 0, -0.5, 1.7), (-2.5, 0.2, -0.4, 1.9)])):
        m = Model(pal)
        for (x, y, z, r) in puffs:
            m.sphere((x, y, z), r, 'cloud', seg=(8, 4), scale=(1, 1, 0.7))
        build_object(name, m, 0, 0.06)
    m = Model(pal)
    m.sphere((0, 0, 0), 16.0, 'hill', seg=(12, 6), scale=(1, 1, 0.55))
    build_object('Hill', m, 0, 0.15)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.18, 0.14, 0.9, 'trunk', seg=5, bevel=False)
    m.cyl((0, 0, 0.8), 1.3, 0.0, 2.2, 'pine', seg=7, bevel=False)
    m.cyl((0, 0, 2.2), 0.95, 0.0, 1.9, 'pine', seg=7, bevel=False)
    build_object('Tree', m, 0, 0.05)
    # trail arrow (painted chevron, flat, no outline)
    m = Model(pal)
    bm = m.bm
    for sgn in (1, -1):
        pts = [(0, 0.5), (sgn * 0.7, -0.2), (sgn * 0.7, -0.55), (0, 0.15)]
        vs = [bm.verts.new((x, y, 0.0)) for x, y in pts]
        f = bm.faces.new(vs if sgn < 0 else list(reversed(vs)))
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        f.material_index = pal.index('dull')
    obj = build_object('TrailArrow', m, 0, 0.0)
    strip_hull(obj)
    # spawn can (robots hop out of these)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.42, 0.48, 0.95, 'canbody', seg=10, bevel=False)
    for z in (0.18, 0.62):
        m.cyl((0, 0, z), 0.445 + z * 0.06, 0.455 + z * 0.06, 0.06, 'canband', seg=10, bevel=False, caps=False)
    m.cyl((0, 0, 0.95), 0.52, 0.5, 0.1, 'canlid', seg=10, bevel=False)
    m.box((0, 0, 1.08), (0.3, 0.08, 0.08), 'ink', bevel=False)
    build_object('SpawnCan', m, 0, ht, ao=ao)
    # ink chunk set (6 pieces): cans and bolts
    for i in range(6):
        m = Model(pal)
        if i < 3:
            m.cyl((0, 0, -0.08), 0.06 + i * 0.01, 0.06 + i * 0.01, 0.16, 'ink', seg=7, bevel=False)
        else:
            m.cyl((0, 0, -0.03), 0.05, 0.05, 0.03, 'ink', seg=6, bevel=False)
            m.cyl((0, 0, -0.08), 0.02, 0.02, 0.1, 'ink', seg=5, bevel=False)
        obj = build_object('InkChunk_%d' % i, m, 0, 0.0)
        strip_hull(obj)
    export('common')


def strip_hull(obj):
    """Remove the outline shell (flat painted marks / all-ink pieces do not need one)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    kill = [v for v in bm.verts if hl and v[hl].length > 0]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


# ================================================================ BOTS
def build_bots(ao):
    pal = Palette('bots')
    bw, ht = CFG['bots']
    # Crawler: dented tin can on 4 spring legs; one sensor slot, antenna light, gold core dome (weak point)
    m = Model(pal)
    m.cyl((0, 0, 0.30), 0.32, 0.31, 0.42, 'tin', seg=10)
    m.cyl((0, 0, 0.42), 0.335, 0.335, 0.12, 'rust', seg=10, bevel=False, caps=False)
    m.cyl((0, 0, 0.72), 0.35, 0.35, 0.05, 'tin2', seg=10)
    m.box((0, -0.31, 0.60), (0.34, 0.07, 0.07), 'ink', bevel=False)          # sensor slot (front = -Y)
    m.box((0, -0.335, 0.60), (0.22, 0.02, 0.03), 'amber', bevel=False)
    m.sphere((0, 0, 0.77), 0.14, 'core', seg=(8, 4), scale=(1, 1, 0.6))
    m.cyl((0.12, 0.08, 0.76), 0.018, 0.018, 0.3, 'ink', seg=3, bevel=False)
    body = build_object('BOT_CRAWLER_Body', m, bw, ht)
    socket('BOT_CRAWLER_CORE', body, (0, 0, 0.82))
    for i, (x, y) in enumerate([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]):
        socket('BOT_CRAWLER_HIP%d' % i, body, (x, y, 0.33))
    m = Model(pal)
    for i in range(3):
        m.box(((0.035 if i % 2 else -0.035), 0, -0.05 - i * 0.085), (0.13, 0.06, 0.04), 'spring', bevel=False)
    m.box((0, 0, -0.15), (0.03, 0.03, 0.3), 'gunmetal', bevel=False)
    m.cyl((0, 0, -0.355), 0.09, 0.07, 0.05, 'gunmetal', seg=5, bevel=False)
    build_object('BOT_CRAWLER_Leg', m, 0, 0.01)
    m = Model(pal)
    m.box((0, 0, 0), (0.09, 0.09, 0.09), 'light', bevel=False)
    build_object('BOT_CRAWLER_Light', m, 0, 0.008)
    export('bots')


# ================================================================ KIT: TOY TOWN
WALL_COLORS = ['tangerine', 'bubblegum', 'purple', 'sky', 'sand', 'coral']


def build_kit_toytown(ao):
    pal = Palette('kit-toytown')
    bw, ht = CFG['kit-toytown']
    # 1 m wall modules, 3 m tall, centred on the cell; windows/doors on both faces (+Y and -Y)
    for ci, c in enumerate(WALL_COLORS):
        for kind in ('Plain', 'Window', 'Door'):
            m = Model(pal)
            m.box((0, 0, 1.5), (1.0, 1.0, 3.0), c, bevel=False)
            m.box((0, 0, 3.08), (1.04, 1.04, 0.16), 'trim')
            for fy in (-1, 1):
                if kind == 'Window':
                    m.box((0, fy * 0.515, 1.9), (0.62, 0.05, 0.62), 'window', bevel=False)
                    m.box((0, fy * 0.53, 1.56), (0.72, 0.06, 0.07), 'trim', bevel=False)
                elif kind == 'Door':
                    m.box((0, fy * 0.515, 0.95), (0.7, 0.05, 1.9), 'door', bevel=False)
                    m.box((0.22, fy * 0.54, 0.95), (0.06, 0.04, 0.06), 'amber', bevel=False)
            build_object('KIT_TOYTOWN_Wall%s_%s' % (kind, c), m, 0, ht, ao=ao)
    # crate (1 m) and stacked crate top
    for name, c in (('Crate', 'tangerine'), ('CrateB', 'bubblegum')):
        m = Model(pal)
        m.box((0, 0, 0.5), (0.96, 0.96, 0.96), c)
        for fy in (-1, 1):
            m.box((0, fy * 0.49, 0.5), (0.98, 0.04, 0.12), 'crate2', bevel=False)
            m.box((fy * 0.49, 0, 0.5), (0.04, 0.98, 0.12), 'crate2', bevel=False)
            m.beam((-0.4, fy * 0.49, 0.12), (0.4, fy * 0.49, 0.88), 0.07, 'crate2')
        build_object('KIT_TOYTOWN_' + name, m, bw, ht, ao=ao)
    # container 2 x 2 x 2.5 with ribs
    for c in ('teal', 'tangerine', 'bubblegum', 'sky'):
        m = Model(pal)
        m.box((0, 0, 1.25), (1.96, 1.96, 2.5), c)
        for k in range(4):
            o = -0.7 + k * 1.4 / 3
            for fy in (-1, 1):
                m.box((o, fy * 0.99, 1.25), (0.08, 0.06, 2.3), 'ink', bevel=False)
        m.box((0, 0, 2.52), (1.8, 1.8, 0.06), 'trim', bevel=False)
        build_object('KIT_TOYTOWN_Container_' + c, m, bw, ht, ao=ao)
    # low wall (1 m segment, 1 m tall) with alternating cap colour
    for name, cap in (('LowWall', 'teal'), ('LowWallB', 'ink')):
        m = Model(pal)
        m.box((0, 0, 0.45), (0.96, 0.8, 0.9), 'lowwall')
        m.box((0, 0, 0.95), (0.96, 0.9, 0.1), cap, bevel=False)
        build_object('KIT_TOYTOWN_' + name, m, bw, ht, ao=ao)
    # landmark: water tower on purple lattice legs (3 x 3 footprint)
    m = Model(pal)
    hw, legH = 1.3, 7.5
    legs = [(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]
    for (x, y) in legs:
        m.box((x, y, legH / 2), (0.28, 0.28, legH), 'purple')
    for i in range(4):
        a, b = legs[i], legs[(i + 1) % 4]
        for lv in range(2):
            z0 = 1.2 + lv * 3
            m.beam((a[0], a[1], z0), (b[0], b[1], z0 + 3), 0.13, 'purple')
            m.beam((b[0], b[1], z0), (a[0], a[1], z0 + 3), 0.13, 'purple')
            m.beam((a[0], a[1], z0 + 3), (b[0], b[1], z0 + 3), 0.17, 'purple')
    m.box((0, 0, legH + 0.1), (3.2, 3.2, 0.2), 'purple2')
    r = hw + 0.5
    m.cyl((0, 0, legH + 0.2), r, r, 3.0, 'tank', seg=16)
    m.cyl((0, 0, legH + 1.2), r + 0.03, r + 0.03, 0.5, 'bubblegum', seg=16, bevel=False, caps=False)
    m.cyl((0, 0, legH + 3.2), r + 0.1, 0.3, 1.4, 'tangerine', seg=16)
    m.cyl((0, 0, legH + 4.6), 0.06, 0.06, 1.0, 'ink', seg=5, bevel=False)
    build_object('KIT_TOYTOWN_Landmark_WaterTower', m, 0.03, 0.03, ao=False)
    # billboards (decoration, facing -Y = game +Z toward the zone entry)
    for name, c in (('Billboard_A', 'bubblegum'), ('Billboard_B', 'tangerine'), ('Billboard_C', 'teal'), ('Billboard_D', 'purple')):
        m = Model(pal)
        for sx in (-1.2, 1.2):
            m.box((sx, 0, 2.2), (0.16, 0.16, 4.4), 'gunmetal')
        m.box((0, 0, 4.1), (3.6, 0.2, 1.6), 'paper')
        m.box((-0.6, -0.12, 4.1), (2.0, 0.04, 0.8), c, bevel=False)
        m.box((1.15, -0.12, 4.1), (0.7, 0.04, 0.7), 'ink', bevel=False)
        build_object('KIT_TOYTOWN_' + name, m, 0.02, ht)
    # gate frame (3 m opening) and roll-up shutter (theme main colour slats, teal/ink hazard band)
    m = Model(pal)
    for sx in (-1.75, 1.75):
        m.box((sx, 0, 1.8), (0.5, 0.7, 3.6), 'gunmetal')
    m.box((0, 0, 3.35), (4.0, 0.8, 0.6), 'gunmetal')
    for sx in (-1.2, 1.2):
        for fy in (-1, 1):
            m.box((sx, fy * 0.42, 3.35), (0.34, 0.06, 0.24), 'teal', bevel=False)
    build_object('KIT_TOYTOWN_GateFrame', m, bw, ht)
    m = Model(pal)
    H, slats = 3.05, 9
    for i in range(slats):
        z = 0.55 + i * (H - 0.55) / slats + (H - 0.55) / slats / 2
        m.box((0, 0, z), (3.0, 0.14, (H - 0.55) / slats - 0.05), 'tangerine' if i % 2 else 'coral', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.16, 0.5), 'ink' if k % 2 else 'teal', bevel=False)
    build_object('KIT_TOYTOWN_GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects['KIT_TOYTOWN_GateShutter']
    strip_hull(shutter)
    # one clean box outline for the shutter as a whole (slats would outline individually)
    m = Model(pal)
    m.box((0, 0, H / 2), (3.0, 0.16, H), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    # exit hatch pad
    m = Model(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'gunmetal', seg=20)
    m.cyl((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, bevel=False)
    build_object('KIT_TOYTOWN_Hatch', m, 0.015, ht)
    # trail wall (1 m segment, 2.6 m tall, theme secondary with accent posts)
    m = Model(pal)
    m.box((0, 0, 1.3), (0.5, 1.0, 2.6), 'bubblegum', bevel=False)
    m.box((0, 0, 2.68), (0.62, 1.02, 0.16), 'trim')
    m.box((0, 0, 1.3), (0.56, 0.2, 2.55), 'purple', bevel=False)
    build_object('KIT_TOYTOWN_TrailWall', m, 0, ht, ao=ao)
    # spawn can lives in fps-common; ammo/health pickups in fps-weapons
    export('kit-toytown')


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


# ================================================================ WEAPONS + ARMS
# Viewmodel space (Blender): +Y forward (barrel), +Z up, origin at the grip top where the right hand holds.
WEAPONS = {
    'PIP': {'mag': (0, -0.03, -0.125), 'muzzle': (0, 0.2, 0.0), 'eject': (0.035, 0.0, 0.03),
            'gripR': (0, -0.035, -0.075), 'gripL': (-0.045, -0.02, -0.085), 'reload': 1.1, 'fire': 0.2},
    'BUZZ': {'mag': (0, 0.08, -0.1), 'muzzle': (0, 0.37, 0.0), 'eject': (0.04, 0.05, 0.03),
             'gripR': (0, -0.04, -0.08), 'gripL': (-0.005, 0.2, -0.065), 'reload': 1.6, 'fire': 0.067},
}


def build_weapon_meshes(pal):
    bw, ht = CFG['weapons']
    # Pip: chunky pistol, Gunmetal with an Amber accent stripe
    m = Model(pal)
    m.box((0, 0.06, 0.0), (0.06, 0.26, 0.07), 'gunmetal')
    m.box((0, 0.06, 0.026), (0.062, 0.24, 0.018), 'amber', bevel=False)
    for k in range(4):
        m.box((0.031, -0.04 + k * 0.016, 0.005), (0.004, 0.008, 0.04), 'ink', bevel=False)  # slide serrations
    m.box((0, -0.03, -0.065), (0.055, 0.075, 0.1), 'gun2')                                   # grip (mag well)
    m.box((0, 0.025, -0.035), (0.01, 0.04, 0.03), 'gunmetal', bevel=False)                  # trigger guard
    m.box((0, 0.17, 0.045), (0.02, 0.02, 0.02), 'ink', bevel=False)                         # front sight
    m.box((0, -0.06, 0.045), (0.03, 0.015, 0.02), 'ink', bevel=False)                       # rear sight
    pip = build_object('WPN_PIP', m, bw, ht)
    m = Model(pal)
    m.box((0, 0, 0), (0.048, 0.06, 0.06), 'gunmetal')
    m.box((0, 0, -0.033), (0.056, 0.07, 0.012), 'amber', bevel=False)
    build_object('WPN_PIP_Mag', m, bw, ht)
    # Buzz: boxy SMG with a long straight mag
    m = Model(pal)
    m.box((0, 0.08, 0.0), (0.075, 0.36, 0.09), 'gunmetal')
    m.box((0, 0.08, 0.036), (0.077, 0.30, 0.018), 'amber', bevel=False)
    m.cyl((0, 0.25, 0.0), 0.02, 0.02, 0.14, 'ink', seg=8, rot=(-90, 0, 0), bevel=False)       # barrel
    m.box((0, -0.04, -0.08), (0.06, 0.07, 0.12), 'gun2')                                       # grip
    m.box((0, 0.2, -0.06), (0.04, 0.05, 0.08), 'gun2')                                        # foregrip
    m.box((0, -0.14, 0.0), (0.05, 0.12, 0.06), 'gunmetal')                                     # stock stub
    m.box((0, 0.02, 0.06), (0.02, 0.12, 0.025), 'ink', bevel=False)                           # top rail
    build_object('WPN_BUZZ', m, bw, ht)
    m = Model(pal)
    m.box((0, 0, -0.02), (0.045, 0.055, 0.15), 'gun2')
    m.box((0, 0, -0.1), (0.05, 0.06, 0.012), 'amber', bevel=False)
    build_object('WPN_BUZZ_Mag', m, bw, ht)
    for wid, w in WEAPONS.items():
        o = bpy.data.objects['WPN_' + wid]
        socket('WPN_%s_MUZZLE' % wid, o, w['muzzle'])
        socket('WPN_%s_MAG' % wid, o, w['mag'])
        socket('WPN_%s_EJECT' % wid, o, w['eject'])


def build_pickups(pal):
    ht = CFG['weapons'][1] * 3
    m = Model(pal)
    m.sphere((0, 0, 0), 0.16, 'chip', seg=(4, 2), scale=(1, 1, 1.4))
    build_object('PICKUP_Gem', m, 0, 0.02)
    m = Model(pal)
    m.box((0, 0, 0.22), (0.62, 0.4, 0.44), 'ammo', bevel=False)
    m.box((0, 0, 0.45), (0.66, 0.44, 0.06), 'ammo2', bevel=False)
    m.box((0, -0.205, 0.22), (0.3, 0.02, 0.1), 'paper', bevel=False)
    for sx in (-0.2, 0.2):
        m.box((sx, -0.205, 0.32), (0.05, 0.02, 0.12), 'amber', bevel=False)
    build_object('PICKUP_Ammo', m, 0.012, ht)
    m = Model(pal)
    m.cyl((0, 0, 0), 0.2, 0.2, 0.5, 'health', seg=8, bevel=False)
    m.cyl((0, 0, 0.5), 0.21, 0.19, 0.05, 'health2', seg=8, bevel=False)
    m.box((0, -0.2, 0.26), (0.18, 0.02, 0.06), 'paper', bevel=False)
    m.box((0, -0.2, 0.26), (0.06, 0.02, 0.18), 'paper', bevel=False)
    build_object('PICKUP_Health', m, 0.012, ht)


# arms rig: 22 bones. Root, Weapon, Mag, Camera + per side: UPPERARM, FOREARM, HAND, THUMB1, THUMB2, INDEX, MIDDLE, RING, PINKY
SHOULDER = {'R': Vector((0.24, -0.62, -0.32)), 'L': Vector((-0.26, -0.55, -0.34))}
UPPER_LEN, FORE_LEN = 0.30, 0.27


def two_bone(s, w, hint):
    """Elbow position for shoulder s, wrist w, bone lengths, bending toward hint."""
    d = w - s
    L = min(d.length, UPPER_LEN + FORE_LEN - 1e-4)
    dn = d.normalized()
    a = (UPPER_LEN ** 2 - FORE_LEN ** 2 + L ** 2) / (2 * L)
    h = math.sqrt(max(UPPER_LEN ** 2 - a * a, 0))
    side = (hint - (dn * hint.dot(dn))).normalized()
    return s + dn * a + side * h


def arm_targets(wid, side, extra=None):
    w = WEAPONS[wid]
    hand = Vector(w['grip' + side])
    if extra:
        hand = hand + Vector(extra)
    wrist = hand + Vector((0.0 if side == 'R' else -0.02, -0.07, -0.025))
    hint = Vector((0.6 if side == 'R' else -0.6, 0, -1))
    elbow = two_bone(SHOULDER[side], wrist, hint)
    return SHOULDER[side], elbow, wrist, hand


def build_arms(pal):
    bw, ht = CFG['weapons']
    arm = bpy.data.armatures.new('ARMS_Rig')
    rig = bpy.data.objects.new('ARMS_Rig', arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    def bone(name, head, tail, parent=None):
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        b.roll = 0
        if parent:
            b.parent = eb[parent]
        b.use_connect = False
        return b
    bone('Root', (0, -0.3, -0.3), (0, -0.2, -0.3))
    bone('Camera', (0, 0, 0.05), (0, 0.1, 0.05), 'Root')
    bone('Weapon', (0, 0, 0), (0, 0.1, 0), 'Root')
    bone('Mag', WEAPONS['PIP']['mag'], Vector(WEAPONS['PIP']['mag']) + Vector((0, 0, -0.07)), 'Weapon')   # Pip mag socket; Buzz keys its own
    rest = {}
    for side in ('R', 'L'):
        s, e, wr, hand = arm_targets('PIP', side)
        rest[side] = (s, e, wr, hand)
        bone('UPPERARM_' + side, s, e, 'Weapon')
        bone('FOREARM_' + side, e, wr, 'Weapon')
        bone('HAND_' + side, wr, hand, 'Weapon')
        sx = 1 if side == 'R' else -1
        bone('THUMB1_' + side, hand + Vector((sx * 0.03, 0, 0.0)), hand + Vector((sx * 0.03, 0.03, 0.01)), 'HAND_' + side)
        bone('THUMB2_' + side, hand + Vector((sx * 0.03, 0.03, 0.01)), hand + Vector((sx * 0.025, 0.055, 0.015)), 'THUMB1_' + side)
        for k, fn in enumerate(('INDEX', 'MIDDLE', 'RING', 'PINKY')):
            z = 0.02 - k * 0.022
            bone(fn + '_' + side, hand + Vector((-sx * 0.0, 0.02, z)), hand + Vector((-sx * 0.04, 0.03, z)), 'HAND_' + side)
    bpy.ops.object.mode_set(mode='OBJECT')
    assert len(arm.bones) == 22, len(arm.bones)

    # glove + sleeve geometry, each piece rigidly weighted to one bone
    m = Model(pal)
    groups = []   # (faces, bone)

    def seg_box(a, b, w, h, color, bone_name, bevel=True):
        faces = m.beam(a, b, 1.0, color, bevel)
        # beam() makes a unit square section; scale to w x h around the axis
        groups.append((faces, bone_name, (Vector(a), Vector(b), w, h)))

    for side in ('R', 'L'):
        s, e, wr, hand = rest[side]
        sx = 1 if side == 'R' else -1
        seg_box(s, e, 0.09, 0.09, 'sleeve', 'UPPERARM_' + side)
        mid = e + (wr - e) * 0.45
        seg_box(e, mid, 0.08, 0.08, 'sleeve2', 'FOREARM_' + side)
        seg_box(mid, wr, 0.07, 0.07, 'glove', 'FOREARM_' + side)
        cuff = mid + (wr - mid) * 0.15
        seg_box(mid, cuff, 0.076, 0.076, 'amber', 'FOREARM_' + side, bevel=False)
        # palm block, wrapping the grip from the outside
        seg_box(wr, hand + Vector((sx * 0.012, 0, 0)), 0.064, 0.075, 'glove', 'HAND_' + side)
        # 4 chunky fingers curled around the grip (inside), thumb on top
        for k, fn in enumerate(('INDEX', 'MIDDLE', 'RING', 'PINKY')):
            z = 0.022 - k * 0.022
            a = hand + Vector((sx * 0.01, 0.0, z))
            b = hand + Vector((-sx * 0.035, 0.03, z - 0.004))
            seg_box(a, b, 0.024, 0.02, 'glove2' if k % 2 else 'glove', fn + '_' + side, bevel=False)
        seg_box(hand + Vector((sx * 0.03, -0.01, 0.01)), hand + Vector((sx * 0.02, 0.05, 0.025)), 0.024, 0.024, 'glove', 'THUMB2_' + side, bevel=False)

    # rescale beam sections (beam() built 1x1 sections) and record vertex groups by bone
    vbone = {}
    for faces, bname, (a, b, w, h) in groups:
        axis = (b - a).normalized()
        c = (a + b) / 2
        verts = {v for f in faces for v in f.verts}
        q = Vector((0, 0, 1)).rotation_difference(axis)
        qi = q.inverted()
        for v in verts:
            lv = qi @ (v.co - c)
            lv.x *= w
            lv.y *= h
            v.co = c + q @ lv
            vbone[v.index if False else id(v)] = bname
    # tag bone per vertex using a temp int layer
    lay = m.bm.verts.layers.int.new('bone_id')
    names = [b.name for b in arm.bones]
    for faces, bname, _ in groups:
        for f in faces:
            for v in f.verts:
                v[lay] = names.index(bname)
    me = bpy.data.meshes.new('ARMS')
    m.bm.to_mesh(me)
    m.bm.free()
    obj = bpy.data.objects.new('ARMS', me)
    bpy.context.scene.collection.objects.link(obj)
    vg = {n: obj.vertex_groups.new(name=n) for n in names}
    ids = me.attributes['bone_id'].data
    for v in me.vertices:
        vg[names[ids[v.index].value]].add([v.index], 1.0, 'REPLACE')
    me.attributes.remove(me.attributes['bone_id'])
    # finish like any other object (UV cells, outline shell), keeping vertex groups
    finish_existing(obj, pal, bw * 0.5, ht)
    # hull vertices are new: give them the weight of the body vertex they came from (by nearest position)
    fix_hull_weights(obj)
    obj.parent = rig
    mod = obj.modifiers.new('rig', 'ARMATURE')
    mod.object = rig
    return rig, obj


def finish_existing(obj, pal, bevel_w, hull_t):
    obj.data.materials.append(pal.material)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    col = bm.loops.layers.float_color.new('Col')
    for f in bm.faces:
        u, v = pal.uv(f.material_index)
        f.smooth = False
        for l in f.loops:
            l[uvl].uv = (u, v)
            l[col] = (1, 1, 1, 1)
    bm.to_mesh(obj.data)
    bm.free()
    add_hull(obj, pal, hull_t)
    for p in obj.data.polygons:
        p.material_index = 0
    obj.data.color_attributes.active_color = obj.data.color_attributes['Col']


def fix_hull_weights(obj):
    me = obj.data
    hull = me.attributes['_HULL'].data
    body = [v for v in me.vertices if Vector(hull[v.index].vector).length == 0]
    from mathutils import kdtree
    kd = kdtree.KDTree(len(body))
    for i, v in enumerate(body):
        kd.insert(v.co, i)
    kd.balance()
    for v in me.vertices:
        if Vector(hull[v.index].vector).length == 0:
            continue
        _, i, _ = kd.find(v.co)
        src = body[i]
        for g in src.groups:
            obj.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')


FPS = 30


def build_actions(rig):
    """Per-weapon actions on the arms rig: Idle, Draw, Holster, Fire, Reload, Sprint."""
    bpy.context.view_layer.objects.active = rig
    rig.animation_data_create()
    sc = bpy.context.scene
    sc.render.fps = FPS
    pb = rig.pose.bones
    for p in pb:
        p.rotation_mode = 'QUATERNION'

    def pose_weapon(loc=(0, 0, 0), rot=(0, 0, 0)):
        pb['Weapon'].location = Vector(loc)
        pb['Weapon'].rotation_quaternion = Euler([math.radians(a) for a in rot], 'XYZ').to_quaternion()

    def set_bone_world(name, head, tail):
        """Pose a Weapon-child bone so it runs head->tail (armature space, weapon at rest)."""
        b = rig.data.bones[name]
        h0, t0 = b.head_local, b.tail_local
        q = (t0 - h0).normalized().rotation_difference((Vector(tail) - Vector(head)).normalized())
        # pose location is in the bone's rest frame; rotation about the bone head
        rest = b.matrix_local.to_3x3()
        pb[name].rotation_quaternion = (rest.inverted() @ q.to_matrix() @ rest).to_quaternion()
        pb[name].location = rest.inverted() @ (Vector(head) - h0)

    def pose_arms(wid, offsetL=None):
        for side in ('R', 'L'):
            s, e, wr, hand = arm_targets(wid, side, offsetL if side == 'L' else None)
            set_bone_world('UPPERARM_' + side, s, e)
            set_bone_world('FOREARM_' + side, e, wr)
            set_bone_world('HAND_' + side, wr, hand)

    def pose_mag(wid, drop=(0, 0, 0)):
        rest = rig.data.bones['Mag'].head_local
        pb['Mag'].location = rig.data.bones['Mag'].matrix_local.to_3x3().inverted() @ (Vector(WEAPONS[wid]['mag']) + Vector(drop) - rest)

    def key(f):
        for p in pb:
            p.keyframe_insert('location', frame=f)
            p.keyframe_insert('rotation_quaternion', frame=f)

    def reset():
        for p in pb:
            p.location = (0, 0, 0)
            p.rotation_quaternion = (1, 0, 0, 0)

    def action(name, frames_fn):
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        rig.animation_data.action = act
        reset()
        frames_fn()
        return act

    for wid, w in WEAPONS.items():
        def base(f, wloc=(0, 0, 0), wrot=(0, 0, 0), offL=None, mag=(0, 0, 0), trigger=0.0, wid=wid):
            reset()
            pose_weapon(wloc, wrot)
            pose_arms(wid, offL)
            pose_mag(wid, mag)
            pb['INDEX_R'].rotation_quaternion = Euler((0, 0, math.radians(-25 * trigger)), 'XYZ').to_quaternion()
            key(f)

        action(wid + '_Idle', lambda: [base(0), base(30, (0, 0, 0.004), (1.2, 0, 0)), base(60)])
        action(wid + '_Draw', lambda: [base(0, (0, -0.05, -0.14), (-55, 0, 18)), base(6, (0, 0.005, 0.005), (4, 0, 0)), base(9)])
        action(wid + '_Holster', lambda: [base(0), base(6, (0, -0.05, -0.14), (-55, 0, 18))])
        n = max(2, round(w['fire'] * FPS))
        action(wid + '_Fire', lambda n=n: [base(0, trigger=1), base(1, (0, -0.018, 0.006), (5, 0, 0), trigger=1), base(n)])
        r = round(w['reload'] * FPS)

        def reload_frames(r=r):
            tilt = (12, 0, -22)
            base(0)
            base(round(r * 0.15), (0, 0, -0.01), tilt)
            base(round(r * 0.3), (0, 0, -0.01), tilt, offL=(-0.02, -0.08, -0.12), mag=(0, -0.05, -0.3))
            base(round(r * 0.55), (0, 0, -0.01), tilt, offL=(0.0, -0.06, -0.16), mag=(0, -0.04, -0.12))
            base(round(r * 0.72), (0, 0.005, 0.0), tilt, offL=(0.0, -0.02, -0.06), mag=(0, 0, -0.01))
            base(round(r * 0.85), (0, -0.01, 0.0), (6, 0, -8))
            base(r)
        action(wid + '_Reload', reload_frames)
        action(wid + '_Sprint', lambda: [base(0, (-0.03, -0.02, -0.05), (-22, 0, 35)), base(9, (-0.03, -0.02, -0.07), (-25, 0, 38)), base(18, (-0.03, -0.02, -0.05), (-22, 0, 35))])
    # leave the rig in Pip idle at rest
    rig.animation_data.action = bpy.data.actions['PIP_Idle']
    # each action needs its own slot assignment for export in Blender 5 (layered actions)
    for act in bpy.data.actions:
        act.use_fake_user = True


def build_weapons(ao):
    pal = Palette('weapons')
    build_weapon_meshes(pal)
    build_pickups(pal)
    rig, arms = build_arms(pal)
    build_actions(rig)
    export('weapons')


BUILDERS = {'common': build_common, 'bots': build_bots, 'kit-toytown': build_kit_toytown, 'weapons': build_weapons}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--family', default='all', choices=['all'] + list(BUILDERS))
    ap.add_argument('--no-ao', action='store_true')
    a = ap.parse_args(argv)
    fams = list(BUILDERS) if a.family == 'all' else [a.family]
    for f in fams:
        fresh_scene()
        BUILDERS[f](not a.no_ao)


if __name__ == '__main__':
    main(sys.argv[1:])
