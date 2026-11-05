"""INKBOLT asset family: weapons."""
import math
import os
import sys

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

ib_lib.ZFIGHT_STRICT['weapons'] = False   # TODO(weapons remodel): set back to True; the build must pass strict
ib_lib.PALETTES['weapons'] = BASE + [('gun2', '#4A4858'), ('glove', '#4E4B5C'), ('glove2', '#5C5970'), ('sleeve', '#5B4E8F'),
                       ('sleeve2', '#6A5DA3'), ('chip', '#FFFFFF'), ('ammo', '#2F7BEA'), ('ammo2', '#1E559F'),
                       ('health', '#5BCF4A'), ('health2', '#3E9C33'), ('steel', '#8C93A0')]

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
    m.box((0, 0.06, 0.03), (0.068, 0.24, 0.016), 'amber', bevel=False)
    for k in range(4):
        m.box((0.033, -0.04 + k * 0.016, 0.005), (0.004, 0.008, 0.04), 'ink', bevel=False)  # slide serrations
    m.box((0, -0.03, -0.07), (0.052, 0.075, 0.1), 'gun2')                                   # grip (mag well)
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
    m.box((0, 0.08, 0.04), (0.083, 0.30, 0.016), 'amber', bevel=False)
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


