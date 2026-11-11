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
The carbine's vertices carry colour alpha 0 (the game's aMask): the Grenadier hides them and shows TROOPER_GL instead.

Levels 20+ (same rig and animations, one pool of rigs in trooperrig.js):
  TROOPER_GL     a 6-shot 40 mm grenade launcher skinned to the right hand (the Grenadier); socket TROOPER_GL_MUZZLE
  TROOPER_MECH   the Robot Trooper: a robot body built from rigid segments, each skinned 100 % to one bone (so the
                 joints read as servo joints): segmented chassis with a back reactor (socket TROOPER_MECH_CORE),
                 servo pods, piston forearms and shins, cable runs, a sensor head with one optic, its own carbine.
                 Plate keys mplate / mplate2 / mhaz are recoloured per robot (trooperrig.js MECH_VARIANTS).
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
    # Robot Trooper (levels 20+): plate keys (recoloured per robot), frame, servos, chrome pistons, the optic
    ('mplate', '#5E6670'), ('mplate2', '#454C55'), ('mhaz', '#E8A42A'), ('mframe', '#2C3036'), ('servo', '#1C1E23'),
    ('chrome', '#AEB8C4'), ('optic', '#FF3B24'), ('optichi', '#FFD7B0'), ('cable', '#111216'),
    # Grenadier's launcher: olive drab body, darker drum, brass-yellow grenade noses
    ('glbody', '#4E5638'), ('glbody2', '#363B27'), ('glround', '#D8B03C'),
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


def _carbine(m, deg=False):
    """the compact carbine in its grip frame (x side, y forward along the barrel, z up; origin = grip). Model rotations
    are in degrees; the Soldier's carbine has always been built with radians (deg=False keeps it exactly as it was)"""
    rad = (lambda d: d) if deg else math.radians
    m.box((0, 0.09, 0.055), (0.048, 0.3, 0.07), 'steel')            # receiver
    m.box((0, 0.31, 0.055), (0.056, 0.17, 0.062), 'steel2')         # handguard
    m.cyl((0, 0.39, 0.06), 0.012, 0.012, 0.14, 'steel', seg=8, rot=(rad(-90), 0, 0))
    m.cyl((0, 0.52, 0.06), 0.019, 0.019, 0.05, 'strap', seg=8, rot=(rad(-90), 0, 0))
    m.box((0, 0.06, 0.105), (0.036, 0.1, 0.034), 'strap')            # optic
    m.box((0, 0.112, 0.105), (0.026, 0.006, 0.026), 'lens')
    m.box((0, 0.125, -0.035), (0.034, 0.05, 0.13), 'steel', rot=(rad(14), 0, 0))   # mag
    m.box((0, -0.005, -0.025), (0.028, 0.04, 0.09), 'strap', rot=(rad(-16), 0, 0))  # grip
    m.box((0, 0.3, -0.012), (0.026, 0.03, 0.06), 'strap')           # foregrip
    m.cyl((0.034, 0.34, 0.05), 0.012, 0.012, 0.08, 'steel2', seg=8, rot=(rad(-90), 0, 0))   # light
    m.box((0, -0.15, 0.045), (0.034, 0.17, 0.05), 'steel')          # stock
    m.box((0, -0.24, 0.035), (0.04, 0.025, 0.09), 'strap')
    return Vector((0, 0.56, 0.06))


def _launcher(m):
    """a 6-shot 40 mm revolver grenade launcher (M32-like) in the grip frame; returns the muzzle"""
    R90 = (-90, 0, 0)                                    # cylinder axis -> +y (forward)
    m.box((0, 0.045, 0.072), (0.05, 0.16, 0.05), 'steel')             # top frame
    m.box((0, -0.015, 0.03), (0.045, 0.06, 0.07), 'steel2')           # rear frame over the grip
    m.cyl((0, 0.17, 0.095), 0.033, 0.033, 0.27, 'glbody', seg=10, rot=R90)          # barrel
    m.cyl((0, 0.425, 0.095), 0.038, 0.038, 0.035, 'strap', seg=10, rot=R90)          # muzzle ring
    m.cyl((0, 0.30, 0.095), 0.036, 0.036, 0.025, 'glround', seg=10, rot=R90)          # warning band
    m.cyl((0, 0.025, 0.048), 0.068, 0.068, 0.14, 'glbody2', seg=6, rot=R90)          # revolving drum
    for k in range(6):                                                  # grenade noses in the drum's front face
        a = math.radians(30 + 60 * k)
        m.cyl((math.cos(a) * 0.042, 0.163, 0.048 + math.sin(a) * 0.042), 0.015, 0.015, 0.008, 'glround', seg=8, rot=R90)
    m.cyl((0, 0.163, 0.048), 0.014, 0.014, 0.008, 'steel', seg=8, rot=R90)
    m.box((0, 0.33, 0.035), (0.03, 0.04, 0.09), 'strap')             # foregrip
    m.box((0, -0.005, -0.025), (0.028, 0.04, 0.09), 'strap', rot=(-16, 0, 0))  # pistol grip
    m.box((0, -0.15, 0.065), (0.03, 0.17, 0.035), 'steel')           # stock tube
    m.box((0, -0.235, 0.045), (0.045, 0.03, 0.10), 'strap')          # butt pad
    m.box((0.036, 0.21, 0.125), (0.012, 0.05, 0.05), 'tan')          # quadrant sight
    m.box((0, 0.12, 0.145), (0.02, 0.05, 0.025), 'strap')            # leaf sight
    return Vector((0, 0.46, 0.095))


def _held(pal, name, frame, build, to_rest, hull_t):
    """a gun built in the grip frame (aim pose), mapped back to the rest pose and skinned 100 % to the right hand"""
    m = Model(pal)
    m.parent = frame
    tip = build(m)
    obj = build_object(name, m, 0.0, hull_t)
    obj.data.transform(to_rest)
    hull = obj.data.attributes.get('_HULL')
    if hull:   # outline directions rotate with the mesh
        r3 = to_rest.to_3x3()
        for d in hull.data:
            d.vector = r3 @ Vector(d.vector)
    vg = obj.vertex_groups.new(name=HAND)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    return obj, to_rest @ (frame @ tip)


def _seg_frame(a, b, up):
    """a frame at a whose local Z runs to b and whose local Y leans toward `up`"""
    z = (b - a).normalized()
    y = (up - z * up.dot(z)).normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = a
    return M


def _rigid(pal, name, build, bone, hull_t):
    m = Model(pal)
    build(m)
    obj = build_object(name, m, 0.0, hull_t)
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    return obj


def build_mech(rig, pal, ht):
    """the Robot Trooper body: rigid robotic segments, one bone each (rest pose = T pose, facing -Y)"""
    B = lambda n: (rig.data.bones[n].head_local.copy(), rig.data.bones[n].tail_local.copy())
    R90X, RY = (90, 0, 0), lambda sx: (0, 90 * sx, 0)
    parts = []

    def P(name, bone, fn):
        parts.append(_rigid(pal, 'TROOPER_m_' + name, fn, bone, ht))

    # ---- pelvis
    def hips(m):
        m.box((0, 0.02, 0.93), (0.27, 0.19, 0.13), 'mframe')
        m.box((0, -0.093, 0.895), (0.13, 0.03, 0.13), 'mplate', rot=(8, 0, 0))
        m.box((0, -0.1105, 0.93), (0.08, 0.006, 0.02), 'mhaz')
        for sx in (-1, 1):
            m.box((sx * 0.162, 0.0, 0.905), (0.035, 0.17, 0.15), 'mplate2')
            m.cyl((sx * 0.1795, 0.0, 0.92), 0.04, 0.04, 0.012, 'servo', seg=10, rot=RY(sx))
        m.cyl((0, 0.02, 0.99), 0.045, 0.045, 0.08, 'chrome', seg=10)
        m.box((0, 0.125, 0.95), (0.12, 0.05, 0.08), 'mplate2')
    P('hips', 'DEF-hips', hips)

    # ---- segmented abdomen, lower chest, chest with the back reactor (weak spot)
    def ab(m):
        m.box((0, 0.015, 1.083), (0.20, 0.15, 0.045), 'servo')
        m.box((0, 0.015, 1.135), (0.24, 0.17, 0.05), 'mplate2')
        m.box((0, -0.0715, 1.135), (0.16, 0.006, 0.012), 'cable')
    P('ab', 'DEF-spine.001', ab)

    def chest_lo(m):
        m.box((0, 0.01, 1.235), (0.30, 0.20, 0.11), 'mframe')
        m.box((0, -0.098, 1.235), (0.20, 0.025, 0.09), 'mplate')
        m.box((0, -0.1135, 1.25), (0.012, 0.006, 0.07), 'cable')
        for sx in (-1, 1):
            for z in (1.215, 1.245):
                m.box((sx * 0.152, 0.01, z), (0.012, 0.13, 0.014), 'servo')
    P('chestlo', 'DEF-spine.002', chest_lo)

    def chest(m):
        m.box((0, 0.005, 1.385), (0.36, 0.22, 0.16), 'mframe')
        for sx in (-1, 1):
            m.box((sx * 0.085, -0.113, 1.395), (0.15, 0.035, 0.15), 'mplate', rot=(-6, 0, -8 * sx))
            m.box((sx * 0.12, 0.01, 1.4725), (0.14, 0.19, 0.025), 'mplate2')
            m.box((sx * 0.12, -0.03, 1.4875), (0.10, 0.03, 0.006), 'mhaz')
        m.cyl((0, 0.01, 1.452), 0.075, 0.065, 0.03, 'servo', seg=10)
        # back: reactor pack, glowing cell (the weak spot), cooling fins, cables up to the neck and out to the arms
        m.box((0, 0.145, 1.375), (0.24, 0.08, 0.20), 'mplate2')
        m.cyl((0, 0.185, 1.39), 0.05, 0.05, 0.02, 'cell', seg=12, rot=(-90, 0, 0))
        for z in (1.30, 1.325):
            m.box((0, 0.19, z), (0.18, 0.012, 0.012), 'servo')
        for sx in (-1, 1):
            m.beam((sx * 0.05, 0.12, 1.47), (sx * 0.03, 0.05, 1.53), 0.016, 'cable')
            m.beam((sx * 0.11, 0.16, 1.45), (sx * 0.19, 0.11, 1.47), 0.016, 'cable')
    P('chest', 'DEF-spine.003', chest)

    # ---- neck + sensor head (one optic, no helmet, no visor)
    def neck(m):
        m.cyl((0, 0.0, 1.47), 0.03, 0.026, 0.11, 'chrome', seg=8)
        for sx in (-1, 1):
            m.beam((sx * 0.042, 0.012, 1.475), (sx * 0.032, 0.004, 1.565), 0.014, 'servo')
    P('neck', 'DEF-neck', neck)

    def head(m):
        m.box((0, 0.0, 1.655), (0.15, 0.18, 0.13), 'mplate')
        m.box((0, -0.02, 1.583), (0.11, 0.13, 0.05), 'mframe')
        m.box((0, -0.075, 1.716), (0.16, 0.05, 0.025), 'mplate2')                          # brow ridge
        m.cyl((0, -0.09, 1.66), 0.05, 0.046, 0.035, 'mframe', seg=12, rot=R90X)            # optic housing
        m.cyl((0, -0.125, 1.66), 0.034, 0.034, 0.012, 'optic', seg=12, rot=R90X)           # the optic
        m.box((-0.012, -0.139, 1.672), (0.012, 0.006, 0.010), 'optichi')
        for sx in (-1, 1):
            m.cyl((sx * 0.075, 0.015, 1.655), 0.032, 0.03, 0.024, 'servo', seg=10, rot=RY(sx))   # side sensors
            m.box((sx * 0.0785, -0.05, 1.62), (0.006, 0.05, 0.012), 'mhaz')
        m.cyl((0.045, 0.06, 1.72), 0.006, 0.006, 0.13, 'cable', seg=4)                      # antenna
        m.box((0.045, 0.06, 1.855), (0.016, 0.016, 0.016), 'mhaz')
        m.box((0, 0.0, 1.7225), (0.04, 0.12, 0.006), 'cable')                               # panel line
    P('head', 'DEF-head', head)

    for side, sx in (('L', 1), ('R', -1)):
        uh, ut = B('DEF-upper_arm.' + side)
        fh, ft = B('DEF-forearm.' + side)
        hh, htl = B('DEF-hand.' + side)

        def shoulder(m, uh=uh):
            m.sphere((uh.x, uh.y, uh.z), 0.068, 'servo', seg=(12, 7))
        P('sh' + side, 'DEF-shoulder.' + side, shoulder)

        def upper(m, uh=uh, ut=ut, sx=sx):
            x0, y, z = uh.x, uh.y, uh.z
            m.box((x0 + sx * 0.05, y, z + 0.065), (0.17, 0.17, 0.06), 'mplate')                 # pauldron
            m.box((x0 + sx * 0.08, y, z + 0.098), (0.045, 0.15, 0.006), 'mhaz')
            m.box((x0 + sx * 0.05, y - 0.088, z + 0.035), (0.13, 0.006, 0.012), 'cable')
            m.cyl((x0 + sx * 0.04, y, z), 0.032, 0.032, 0.22, 'mframe', seg=8, rot=RY(sx))
            m.box(((uh.x + ut.x) / 2 + sx * 0.02, y, z), (0.15, 0.08, 0.08), 'mplate2')
            m.cyl((x0 + sx * 0.06, y, z - 0.052), 0.012, 0.012, 0.17, 'chrome', seg=6, rot=RY(sx))   # bicep piston
            m.cyl((ut.x, ut.y + 0.05, ut.z), 0.044, 0.044, 0.10, 'servo', seg=10, rot=R90X)       # elbow servo
            m.cyl((ut.x, ut.y + 0.056, ut.z), 0.02, 0.02, 0.112, 'chrome', seg=8, rot=R90X)
        P('ua' + side, 'DEF-upper_arm.' + side, upper)

        def fore(m, fh=fh, ft=ft, sx=sx):
            y, z = fh.y, fh.z
            m.cyl((fh.x + sx * 0.03, y, z), 0.034, 0.034, 0.14, 'mframe', seg=10, rot=RY(sx))     # hydraulic body
            m.cyl((fh.x + sx * 0.165, y, z), 0.018, 0.018, 0.10, 'chrome', seg=8, rot=RY(sx))     # piston rod
            for dz in (-0.038, 0.038):
                m.cyl((fh.x + sx * 0.03, y + 0.02, z + dz), 0.008, 0.008, 0.24, 'chrome', seg=6, rot=RY(sx))
            m.box((fh.x + sx * 0.10, y, z + 0.044), (0.13, 0.06, 0.016), 'mplate')
            m.box((fh.x + sx * 0.10, y - 0.0325, z + 0.044), (0.10, 0.005, 0.006), 'mhaz')
            m.sphere((ft.x, ft.y, ft.z), 0.03, 'servo', seg=(10, 6))                            # wrist
        P('fa' + side, 'DEF-forearm.' + side, fore)

        def hand(m, hh=hh, sx=sx):
            m.box((hh.x + sx * 0.066, 0.07, hh.z), (0.10, 0.085, 0.035), 'mframe')
            m.box((hh.x + sx * 0.09, 0.07, hh.z + 0.0215), (0.04, 0.08, 0.008), 'mplate2')
        P('hand' + side, 'DEF-hand.' + side, hand)
        for f in ('index', 'middle', 'ring', 'pinky', 'thumb'):
            n1, n2, n3 = ['DEF-%s.0%d.%s' % ('thumb' if f == 'thumb' else 'f_' + f, k, side) for k in (1, 2, 3)]
            a1, b1 = B(n1)
            a2, b2 = B(n2)
            a3, b3 = B(n3)

            def seg1(m, a=a1, b=b1):
                m.parent = _seg_frame(a, b, Vector((0, 0, 1)))
                m.box((0, 0, (b - a).length / 2), (0.019, 0.017, (b - a).length + 0.006), 'servo')
                m.parent = Matrix.Identity(4)

            def seg2(m, a=a2, b=b3):
                m.parent = _seg_frame(a, b, Vector((0, 0, 1)))
                m.box((0, 0, (b - a).length / 2), (0.017, 0.015, (b - a).length), 'chrome')
                m.parent = Matrix.Identity(4)
            P(f + '1' + side, n1, seg1)
            P(f + '2' + side, n2, seg2)

        th, tt = B('DEF-thigh.' + side)
        sh_, st = B('DEF-shin.' + side)
        fo, ftt = B('DEF-foot.' + side)
        to, tot = B('DEF-toe.' + side)

        def thigh(m, th=th, tt=tt, sx=sx):
            x = th.x
            m.cyl((x, 0.0, tt.z + 0.03), 0.042, 0.042, th.z - tt.z - 0.07, 'mframe', seg=8)
            m.box((x, -0.06, 0.75), (0.12, 0.04, 0.26), 'mplate')
            m.box((x, -0.0835, 0.80), (0.03, 0.007, 0.10), 'mhaz')
            m.cyl((x + sx * 0.06, 0.0, tt.z + 0.05), 0.011, 0.011, 0.30, 'chrome', seg=6)
            m.cyl((x + sx * 0.06, 0.0, 0.70), 0.021, 0.021, 0.12, 'servo', seg=8)
            m.cyl((x - sx * 0.06, tt.y, tt.z), 0.052, 0.052, 0.12, 'servo', seg=10, rot=RY(sx))   # knee servo
            m.cyl((x - sx * 0.066, tt.y, tt.z), 0.022, 0.022, 0.132, 'chrome', seg=8, rot=RY(sx))
        P('th' + side, 'DEF-thigh.' + side, thigh)

        def shin(m, sh_=sh_, st=st, sx=sx):
            x = sh_.x
            m.box((x, -0.063, 0.50), (0.112, 0.035, 0.10), 'mplate2', rot=(10, 0, 0))   # knee cap
            m.cyl((x, 0.015, 0.30), 0.04, 0.04, 0.19, 'mframe', seg=10)                          # hydraulic body
            m.cyl((x, 0.025, 0.12), 0.02, 0.02, 0.2, 'chrome', seg=8)                            # rod
            m.box((x, -0.05, 0.33), (0.10, 0.03, 0.24), 'mplate')                                # shin guard
            m.box((x, -0.0675, 0.40), (0.06, 0.005, 0.012), 'cable')
            m.box((x, -0.0675, 0.26), (0.06, 0.005, 0.012), 'mhaz')
            m.beam((x, 0.065, 0.46), (x, 0.055, 0.20), 0.03, 'servo')                            # calf actuator
            m.sphere((st.x, st.y, st.z), 0.042, 'servo', seg=(10, 6))                              # ankle
        P('sh' + side + '2', 'DEF-shin.' + side, shin)

        def foot(m, fo=fo, sx=sx):
            x = fo.x
            m.box((x, -0.02, 0.04), (0.12, 0.20, 0.08), 'mframe')
            m.box((x, 0.095, 0.03), (0.08, 0.04, 0.06), 'mplate2')
        P('ft' + side, 'DEF-foot.' + side, foot)

        def toe(m, to=to):
            x = to.x
            m.box((x, -0.20, 0.025), (0.12, 0.17, 0.05), 'mplate2')
            m.box((x, -0.25, 0.053), (0.09, 0.03, 0.006), 'mhaz')
        P('toe' + side, 'DEF-toe.' + side, toe)
    return parts


def _join(objs, name, rig):
    head = objs[0]
    with bpy.context.temp_override(active_object=head, object=head, selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    head.name = name
    head.data.name = name
    a = head.modifiers.new('Armature', 'ARMATURE')
    a.object = rig
    head.parent = rig
    return head


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
    # Grenadier's bandolier of 40 mm grenades across the plate carrier (part of TROOPER_GL, rigid on the chest)
    m = Model(pal)
    ba = Vector((cc.x + pw * 0.42, front + fy * 0.115, pz + ph * 0.44))
    bb = Vector((cc.x - pw * 0.46, front + fy * 0.115, pz - ph * 0.46))
    bd = (bb - ba).normalized()
    m.parent = _seg_frame(ba, bb, F)
    m.box((0, 0, (bb - ba).length / 2), (0.055, 0.012, (bb - ba).length + 0.03), 'strap')
    nrm = Vector((-bd.z, 0, bd.x)).normalized()
    for k in range(5):
        c = ba + bd * ((bb - ba).length * (0.14 + 0.18 * k)) + F * 0.026
        m.parent = _seg_frame(c - nrm * 0.036, c + nrm * 0.036, F)
        m.cyl((0, 0, 0), 0.021, 0.021, 0.056, 'glround', seg=8)
        m.cyl((0, 0, 0.056), 0.017, 0.012, 0.018, 'glbody', seg=8)
    m.parent = Matrix.Identity(4)
    band = build_object('TROOPER_g_band', m, 0.0, ht * 0.8)
    band.vertex_groups.new(name='DEF-spine.003').add(list(range(len(band.data.vertices))), 1.0, 'REPLACE')

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
    to_rest = Rr @ P.inverted()
    rifle, muzzle_rest = _held(pal, 'TROOPER_g_rifle', frame, _carbine, to_rest, ht * 0.6)
    for c in rifle.data.color_attributes['Col'].data:   # alpha 0: the carbine (the Grenadier hides it: aMask)
        c.color = (1.0, 1.0, 1.0, 0.0)
    gear.append(rifle)
    # Grenadier's launcher (its own skinned mesh) and the Robot Trooper's carbine, fitted the same way
    gl, gl_muzzle = _held(pal, 'TROOPER_GL', frame, _launcher, to_rest, ht * 0.6)
    mech_gun, _ = _held(pal, 'TROOPER_m_gun', frame, lambda m: _carbine(m, True), to_rest, ht * 0.6)

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
    # only the palette UVs (the mannequin's second UV map is unused)
    for uvl in list(body.data.uv_layers):
        if uvl.name != 'UVMap':
            body.data.uv_layers.remove(uvl)
    # ---- levels 20+: the grenade launcher and the Robot Trooper body on the same rig
    gl = _join([gl, band], 'TROOPER_GL', rig)
    mech = _join([mech_gun] + build_mech(rig, pal, ht), 'TROOPER_MECH', rig)
    for o in (gl, mech):
        print(o.name, 'verts', len(o.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons))

    # muzzle socket on the hand bone, and the core (power cell) as a socket on the chest
    for name, at, bone in (('TROOPER_MUZZLE', muzzle_rest, HAND), ('TROOPER_CORE', core, 'DEF-spine.003'),
                           ('TROOPER_GL_MUZZLE', gl_muzzle, HAND), ('TROOPER_MECH_CORE', Vector((0, 0.2, 1.39)), 'DEF-spine.003')):
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
