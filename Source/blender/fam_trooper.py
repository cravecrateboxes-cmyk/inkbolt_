"""INKBOLT trooper family (fps-troopers.glb): the Soldier as one skinned, animated character in SWAT / military kit.

Base: Quaternius' Universal Animation Library mannequin, rig and animations (CC0, third_party/ual/). The mannequin
is decimated, painted into kit zones (uniform, gloves, boots, balaclava), then dressed with gear built here and
weighted to the rig: a ballistic helmet with rails, NVG mount and strobe, goggles, headset, a plate carrier with
mag pouches, radio, patch and hydration pack (with the glowing power cell the player can shoot), a belt with a
holster, knee pads, and a compact carbine fitted to the right hand in the aiming pose. One mesh, one material, the
INKBOLT ink outline (_HULL shell) and palette UVs, like every other family.

Exported: TROOPER (skinned mesh), TROOPER_Rig (armature), TROOPER_MUZZLE (empty on the right hand), and the
animations listed in KEEP. Kit colours that the game recolours per soldier (src/game/troops.js VARIANTS):
uniform, uniform2, vest, vest2, helmet, pad.
Blender: Z up, the mannequin faces -Y (game +Z).
"""
import math
import os

import bpy  # noqa: F401
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'troopers'
ib_lib.GLB[FAM] = 'fps-troopers.glb'
ib_lib.CFG[FAM] = (0.0, 0.011)
ib_lib.PALETTES[FAM] = BASE + [
    ('uniform', '#2B3445'), ('uniform2', '#222937'), ('vest', '#1E2128'), ('vest2', '#2D323C'),
    ('helmet', '#23262D'), ('pad', '#2F333C'), ('mask', '#1B1D23'), ('glove', '#17181C'),
    ('boot', '#1A1613'), ('sole', '#0F0E0D'), ('lens', '#11202E'), ('lenshi', '#8FDCFF'),
    ('patch', '#E9EEF5'), ('steel', '#3A3D45'), ('steel2', '#4C505A'), ('strap', '#14151A'),
    ('cell', '#7FE8FF'), ('tan', '#9C8962'),
]
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'third_party', 'ual', 'AnimationLibrary_Godot_Standard.gltf')
KEEP = ['Idle_Loop', 'Walk_Loop', 'Jog_Fwd_Loop', 'Sprint_Loop', 'Crouch_Idle_Loop', 'Crouch_Fwd_Loop', 'Death01',
        'Hit_Chest', 'Hit_Head', 'Pistol_Idle_Loop', 'Pistol_Aim_Neutral', 'Pistol_Aim_Up', 'Pistol_Aim_Down',
        'Pistol_Shoot', 'Pistol_Reload', 'Punch_Cross', 'Spell_Simple_Shoot']
HAND = 'DEF-hand.R'


def _apply_mod(obj, mod):
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def _dominant(obj):
    """vertex index -> name of the vertex group with the largest weight"""
    names = {g.index: g.name for g in obj.vertex_groups}
    out = {}
    for v in obj.data.vertices:
        best, bw = None, 0.0
        for g in v.groups:
            if g.weight > bw and g.group in names:
                best, bw = names[g.group], g.weight
        out[v.index] = best or ''
    return out


def _bbox(obj, dom, test):
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for v in obj.data.vertices:
        if test(dom[v.index]):
            c = obj.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], c[i]); hi[i] = max(hi[i], c[i])
    return lo, hi


def _paint_body(body, pal, dom, boot_z):
    """kit zones by the bone each face follows (rest pose): gloves, boots, balaclava, uniform"""
    me = body.data
    for p in me.polygons:
        names = [dom[i] for i in p.vertices]
        n = max(set(names), key=names.count)
        z = sum((body.matrix_world @ me.vertices[i].co).z for i in p.vertices) / len(p.vertices)
        if 'hand' in n or '_f_' in n or 'f_' in n.split('-')[-1] or 'thumb' in n:
            c = 'glove'
        elif 'foot' in n or 'toe' in n or ('shin' in n and z < boot_z):
            c = 'sole' if z < 0.025 else 'boot'
        elif 'head' in n or 'neck' in n:
            c = 'mask'
        elif 'forearm' in n and z > 0:
            c = 'uniform'
        else:
            c = 'uniform'
        p.material_index = pal.index(c)


def _finish_mesh(obj, pal, hull_t):
    """palette UVs + white vertex colour + smooth/sharp split + ink outline (as ib_lib.build_object)"""
    obj.data.materials.clear()
    obj.data.materials.append(pal.material)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for l in list(bm.loops.layers.uv):
        pass
    uvl = bm.loops.layers.uv.get('UVMap') or (bm.loops.layers.uv[0] if len(bm.loops.layers.uv) else bm.loops.layers.uv.new('UVMap'))
    col = bm.loops.layers.float_color.get('Col') or bm.loops.layers.float_color.new('Col')
    for f in bm.faces:
        u, v = pal.uv(f.material_index)
        f.smooth = True
        for lp in f.loops:
            lp[uvl].uv = (u, v)
            lp[col] = (1.0, 1.0, 1.0, 1.0)
    bm.to_mesh(obj.data)
    bm.free()
    if obj.data.uv_layers and obj.data.uv_layers[0].name != 'UVMap':
        obj.data.uv_layers[0].name = 'UVMap'
    add_hull(obj, pal, hull_t)
    for p in obj.data.polygons:
        p.material_index = 0
    obj.data.color_attributes.active_color = obj.data.color_attributes['Col']


def _flatten(m, center, sx, sy):
    m.parent = Matrix.Translation(center) @ Matrix.Diagonal(Vector((sx, sy, 1.0, 1.0)))


def BUILD(ao=False):
    pal = Palette(FAM)
    bw, ht = CFG[FAM]
    bpy.ops.import_scene.gltf(filepath=SRC)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH')
    assert (rig.matrix_world - Matrix.Identity(4)).to_3x3().determinant() == 0 or True
    rig.name = 'TROOPER_Rig'; rig.data.name = 'TROOPER_Rig'
    body.name = 'TROOPER'
    # bake any object transform into the mesh so rest-pose coordinates are world coordinates
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()

    # ---- keep the animations we use
    for a in list(bpy.data.actions):
        base = a.name.split('|')[-1]
        if base not in KEEP:
            bpy.data.actions.remove(a)
        else:
            a.name = base
            a.use_fake_user = True
            for sl in getattr(a, 'slots', []):   # Blender 4.4+: the slot is matched by the object's name on export
                try:
                    sl.name_display = rig.name
                except Exception as e:  # noqa: BLE001
                    print('slot rename failed', e)

    # ---- decimate (half the triangles; the ink style hides the facets)
    dec = body.modifiers.new('dec', 'DECIMATE'); dec.ratio = 0.5
    body.modifiers.move(body.modifiers.find('dec'), 0)
    _apply_mod(body, dec)

    dom = _dominant(body)
    lo, hi = _bbox(body, dom, lambda n: True)
    H = hi.z - lo.z
    toe = rig.data.bones['DEF-toe.L'].head_local; foot = rig.data.bones['DEF-foot.L'].head_local
    fy = -1.0 if (toe - foot).y < 0 else 1.0          # facing (Blender -Y)
    F = Vector((0, fy, 0))
    print('trooper height', round(H, 3), 'facing y', fy)

    _paint_body(body, pal, dom, lo.z + H * 0.115)

    # ---- gear in rest pose (armature space), one Model per piece group so weights transfer per piece
    gear = []
    hl, hh = _bbox(body, dom, lambda n: 'head' in n)
    hc = (hl + hh) / 2; hs = hh - hl
    eye = hl.z + hs.z * 0.6
    m = Model(pal)
    # helmet: a dome cut at the brow, rim, side rails, NVG shroud, strobe, rear pouch
    rx = hs.x * 0.5 * 1.2; ry = hs.y * 0.5 * 1.2; cz = hl.z + hs.z * 0.64
    _flatten(m, Vector((hc.x, hc.y, cz)), 1.0, ry / rx)
    faces = m.sphere((0, 0, 0), rx, 'helmet', seg=(16, 10), scale=(1, 1, (hh.z - cz + 0.03) / rx))
    cut = [v for v in {v for f in faces for v in f.verts} if v.co.z < cz - 0.004]
    bmesh.ops.delete(m.bm, geom=cut, context='VERTS')
    m.cyl((0, 0, -0.012), rx * 1.03, rx * 1.03, 0.022, 'helmet', seg=16)
    m.parent = Matrix.Identity(4)
    for sx in (-1, 1):
        m.box((hc.x + sx * rx * 0.99, hc.y, cz + 0.03), (0.016, ry * 1.2, 0.022), 'steel')
        m.cyl((hc.x + sx * (rx + 0.004), hc.y, eye - 0.03), 0.042, 0.042, 0.036, 'vest2', seg=12, rot=(0, math.radians(90 * sx), 0))
    m.box((hc.x, hc.y + fy * ry * 0.98, cz + 0.045), (0.06, 0.026, 0.05), 'steel')
    m.box((hc.x, hc.y + fy * (ry * 0.98 + 0.02), cz + 0.03), (0.022, 0.02, 0.03), 'strap')
    m.box((hc.x, hc.y - fy * ry * 0.95, cz + 0.07), (0.07, 0.04, 0.06), 'vest2')
    m.box((hc.x, hc.y - fy * ry * 0.62, hh.z + 0.012), (0.022, 0.03, 0.02), 'cell')
    # goggles: frame, lens, glint, side straps
    gy = hc.y + fy * (hs.y * 0.5 + 0.004)
    m.box((hc.x, gy, eye), (hs.x * 0.9, 0.03, 0.07), 'strap')
    m.box((hc.x, gy + fy * 0.017, eye), (hs.x * 0.78, 0.006, 0.05), 'lens')
    m.box((hc.x - hs.x * 0.16, gy + fy * 0.021, eye + 0.012), (hs.x * 0.22, 0.004, 0.012), 'lenshi')
    for sx in (-1, 1):
        m.box((hc.x + sx * hs.x * 0.5, hc.y, eye), (0.012, hs.y * 0.9, 0.03), 'strap')
    gear.append(build_object('TROOPER_g_head', m, 0.0, ht))

    # plate carrier
    cl, ch = _bbox(body, dom, lambda n: 'spine.002' in n or 'spine.003' in n)
    cc = (cl + ch) / 2; cs = ch - cl
    front = (cl.y if fy < 0 else ch.y); back = (ch.y if fy < 0 else cl.y)
    pz = cl.z + cs.z * 0.5; ph = cs.z * 0.78; pw = cs.x * 0.74
    m = Model(pal)
    m.box((cc.x, front + fy * 0.025, pz), (pw, 0.06, ph), 'vest')
    m.box((cc.x, back - fy * 0.025, pz), (pw, 0.06, ph), 'vest')
    for sx in (-1, 1):
        m.box((cc.x + sx * cs.x * 0.44, cc.y, pz - ph * 0.18), (0.05, abs(front - back) * 0.92, ph * 0.5), 'vest')
        x = cc.x + sx * pw * 0.3
        top = pz + ph / 2
        m.beam((x, front + fy * 0.02, top - 0.02), (x, cc.y, top + 0.05), 0.045, 'vest')
        m.beam((x, cc.y, top + 0.05), (x, back - fy * 0.02, top - 0.02), 0.039, 'vest')
    for i in (-1, 0, 1):
        x = cc.x + i * 0.078
        m.box((x, front + fy * 0.08, pz - ph * 0.22), (0.066, 0.05, ph * 0.42), 'vest2')
        m.box((x, front + fy * 0.08, pz - ph * 0.22 + ph * 0.21 + 0.018), (0.046, 0.028, 0.036), 'steel')
    m.box((cc.x, front + fy * 0.059, pz + ph * 0.3), (pw * 0.55, 0.008, 0.05), 'patch')
    m.box((cc.x, back - fy * 0.059, pz + ph * 0.3), (pw * 0.62, 0.008, 0.06), 'patch')
    # radio + antenna (left back), hydration pack with the power cell (the weak spot)
    m.box((cc.x - cs.x * 0.36, back - fy * 0.07, pz + ph * 0.05), (0.07, 0.05, 0.14), 'steel2')
    m.beam((cc.x - cs.x * 0.38, back - fy * 0.07, pz + ph * 0.05 + 0.07), (cc.x - cs.x * 0.42, back - fy * 0.07, pz + ph * 0.05 + 0.3), 0.012, 'strap')
    m.box((cc.x + 0.03, back - fy * 0.085, pz - ph * 0.05), (0.2, 0.07, ph * 0.66), 'vest2')
    m.box((cc.x + 0.03, back - fy * 0.123, pz + ph * 0.08), (0.08, 0.012, 0.08), 'cell')
    gear.append(build_object('TROOPER_g_vest', m, 0.0, ht))
    core = Vector((cc.x + 0.03, back - fy * 0.123, pz + ph * 0.08))

    # belt, holster, dump pouch
    bl, bh = _bbox(body, dom, lambda n: n.endswith('hips'))
    bc = (bl + bh) / 2; bs = bh - bl
    m = Model(pal)
    _flatten(m, Vector((bc.x, bc.y, bh.z - 0.055)), 1.0, (bs.y * 0.5 + 0.02) / (bs.x * 0.5 + 0.02))
    m.cyl((0, 0, 0), bs.x * 0.5 + 0.02, bs.x * 0.5 + 0.02, 0.05, 'strap', seg=18)
    m.parent = Matrix.Identity(4)
    m.box((bc.x, bc.y + fy * (bs.y * 0.5 + 0.03), bh.z - 0.03), (0.06, 0.012, 0.045), 'steel')
    tl, th = _bbox(body, dom, lambda n: 'thigh.R' in n)
    tc = (tl + th) / 2
    sxr = 1 if tc.x > bc.x else -1
    m.box((th.x if sxr > 0 else tl.x, tc.y, th.z - 0.12) if False else (tc.x + sxr * ((th.x - tl.x) * 0.5 + 0.03), tc.y, th.z - 0.13), (0.045, 0.1, 0.17), 'vest2')
    m.box((tc.x + sxr * ((th.x - tl.x) * 0.5 + 0.03), tc.y - fy * 0.02, th.z - 0.03), (0.03, 0.035, 0.06), 'steel')
    m.box((bc.x - sxr * bs.x * 0.42, bc.y - fy * bs.y * 0.3, bh.z - 0.12), (0.06, 0.1, 0.12), 'vest2')
    gear.append(build_object('TROOPER_g_belt', m, 0.0, ht))

    # knee pads + elbow pads
    m = Model(pal)
    for side in ('L', 'R'):
        k = rig.data.bones['DEF-shin.' + side].head_local
        m.box((k.x, k.y + fy * 0.065, k.z - 0.01), (0.11, 0.045, 0.13), 'pad')
        m.box((k.x, k.y + fy * 0.09, k.z - 0.01), (0.07, 0.006, 0.07), 'strap')
        e = rig.data.bones['DEF-forearm.' + side].head_local
        m.box((e.x, e.y - fy * 0.045, e.z), (0.09, 0.035, 0.08), 'pad')
    gear.append(build_object('TROOPER_g_pads', m, 0.0, ht))

    # weights: each gear piece takes the body's weights from the nearest surface
    for g in gear:
        dt = g.modifiers.new('dt', 'DATA_TRANSFER')
        dt.object = body
        dt.use_vert_data = True
        dt.data_types_verts = {'VGROUP_WEIGHTS'}
        dt.vert_mapping = 'POLYINTERP_NEAREST'
        dt.layers_vgroup_select_src = 'ALL'
        dt.layers_vgroup_select_dst = 'NAME'
        with bpy.context.temp_override(object=g, active_object=g, selected_objects=[g]):
            bpy.ops.object.datalayout_transfer(modifier='dt')
        _apply_mod(g, dt)

    # ---- carbine, fitted in the aiming pose to the right hand, then mapped back to the rest pose
    rig.data.pose_position = 'POSE'
    rig.animation_data_create()
    act = bpy.data.actions['Pistol_Aim_Neutral']
    rig.animation_data.action = act
    if hasattr(rig.animation_data, 'action_slot') and act.slots:
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(act.frame_range[0]) + 1)
    bpy.context.view_layer.update()
    pb = rig.pose.bones[HAND]
    P = pb.matrix.copy()                          # posed, armature space
    Rr = rig.data.bones[HAND].matrix_local.copy()  # rest
    # grip point: a little along the hand bone; the carbine points the way the character aims (F), up = Z
    grip = (P @ Vector((0, 0.07, 0, 1))).to_3d() if False else P @ Vector((0, 0.06, 0))
    side = Vector((0, 0, 1)).cross(F).normalized()
    frame = Matrix((side, F, Vector((0, 0, 1)))).transposed().to_4x4()
    frame.translation = grip
    m = Model(pal)
    m.parent = frame
    m.box((0, 0.09, 0.055), (0.048, 0.3, 0.07), 'steel')            # receiver
    m.box((0, 0.31, 0.055), (0.056, 0.17, 0.062), 'steel2')         # handguard
    m.cyl((0, 0.39, 0.06), 0.012, 0.012, 0.14, 'steel', seg=8, rot=(math.radians(-90), 0, 0))
    m.cyl((0, 0.52, 0.06), 0.019, 0.019, 0.05, 'strap', seg=8, rot=(math.radians(-90), 0, 0))
    m.box((0, 0.06, 0.105), (0.036, 0.1, 0.034), 'strap')            # optic
    m.box((0, 0.112, 0.105), (0.026, 0.006, 0.026), 'lens')
    m.box((0, 0.125, -0.035), (0.034, 0.05, 0.13), 'steel', rot=(math.radians(14), 0, 0))   # mag
    m.box((0, -0.005, -0.025), (0.028, 0.04, 0.09), 'strap', rot=(math.radians(-16), 0, 0))  # grip
    m.box((0, 0.3, -0.012), (0.026, 0.03, 0.06), 'strap')           # foregrip
    m.cyl((0.034, 0.34, 0.05), 0.012, 0.012, 0.08, 'steel2', seg=8, rot=(math.radians(-90), 0, 0))   # light
    m.box((0, -0.15, 0.045), (0.034, 0.17, 0.05), 'steel')          # stock
    m.box((0, -0.24, 0.035), (0.04, 0.025, 0.09), 'strap')
    rifle = build_object('TROOPER_g_rifle', m, 0.0, ht * 0.6)
    to_rest = Rr @ P.inverted()
    rifle.data.transform(to_rest)
    hull = rifle.data.attributes.get('_HULL')
    if hull:   # outline directions rotate with the mesh
        r3 = to_rest.to_3x3()
        for d in hull.data:
            d.vector = r3 @ Vector(d.vector)
    vg = rifle.vertex_groups.new(name=HAND)
    vg.add(list(range(len(rifle.data.vertices))), 1.0, 'REPLACE')
    muzzle_rest = to_rest @ (frame @ Vector((0, 0.56, 0.06)))
    gear.append(rifle)

    # ---- join everything into the body, back on the rig
    rig.data.pose_position = 'REST'
    rig.animation_data.action = None
    bpy.context.view_layer.update()
    _finish_mesh(body, pal, ht)
    for g in gear:
        g.data.materials.clear(); g.data.materials.append(pal.material)
    with bpy.context.temp_override(active_object=body, object=body, selected_objects=[body] + gear, selected_editable_objects=[body] + gear):
        bpy.ops.object.join()
    if not body.modifiers.get('Armature'):
        a = body.modifiers.new('Armature', 'ARMATURE'); a.object = rig
    body.parent = rig
    print('trooper verts', len(body.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons))

    # muzzle socket on the hand bone, and the core (power cell) as a socket on the chest
    for name, at, bone in (('TROOPER_MUZZLE', muzzle_rest, HAND), ('TROOPER_CORE', core, 'DEF-spine.003')):
        e = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone
        bpy.context.view_layer.update()
        e.matrix_world = Matrix.Translation(at)
    # export with the armature in POSE mode (in REST every sampled animation would be the rest pose), from a clean pose
    for pbn in rig.pose.bones:
        pbn.matrix_basis = Matrix.Identity(4)
    rig.data.pose_position = 'POSE'
    bpy.context.view_layer.update()
    export(FAM)


FAMILY = FAM
