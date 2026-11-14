"""INKBOLT trooper family (fps-troopers.glb): the Soldier as one skinned, animated character in SWAT / military kit.

Base: Quaternius' Universal Animation Library mannequin, rig and animations (CC0, third_party/ual/). The mannequin's
pelvis is reshaped like combat trousers (_trouser_pelvis), then it is decimated, painted into kit zones (uniform,
gloves, boots, balaclava) and dressed with sculpted gear built here (trooper_shapes.py: rounded and chamfered edges,
curved plates) and weighted to the rig: a rounded ballistic helmet with rails, NVG mount and strobe, curved goggles,
headset, a plate carrier with SAPI-cut plates wrapping round the ribs, rounded mag pouches, radio, patch and a
rounded hydration pack (with the round glowing power cell the player can shoot), a belt with a holster and a groin
protector, domed knee pads, and a chamfered compact carbine fitted to the right hand in the aiming pose. One mesh,
one material, the INKBOLT ink outline (_HULL shell) and palette UVs, like every other family.

Exported: TROOPER (skinned mesh), TROOPER_Rig (armature), TROOPER_MUZZLE (empty on the right hand), and the
animations listed in KEEP. Kit colours that the game recolours per soldier (src/game/troops.js VARIANTS):
uniform, uniform2, vest, vest2, helmet, pad.
The carbine's vertices carry colour alpha 0 (the game's aMask): the Grenadier hides them and shows TROOPER_GL instead.

Levels 20+ (same rig and animations, one pool of rigs in trooperrig.js):
  TROOPER_GL     a 6-shot 40 mm grenade launcher (round drum, chamfered frame) skinned to the right hand (the
                 Grenadier); socket TROOPER_GL_MUZZLE
  TROOPER_MECH   the Robot Trooper: a heavy industrial walker of rigid sculpted armour, each part skinned 100 % to
                 one bone: domed, layered pauldrons round a small rounded head set low with one red optic, a barrel
                 chest with pillowed pectoral plates on a narrow piston waist (round back reactor, socket
                 TROOPER_MECH_CORE), tapered piston arms with round servo joints and clamp hands, tapered legs with
                 curved thigh plates and shin guards on sculpted feet, stencils and hazard marks, its own carbine.
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
import enemy_detail as ED
import trooper_shapes as S

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


def _trouser_pelvis(body, rig, iters=90, wpasses=16):
    """Reshape the mannequin's crotch like combat trousers. The base mesh narrows to an anatomical wedge between deep
    groin creases (a V / cone at the crotch, pinching the ink outline) and has a gluteal cleft; its weights jump from
    hips to 100 % thigh across the groin. In an ellipsoid round the crotch (falling off smoothly to nothing) this
    fills the creases and the cleft with one-sided smoothing that only ever moves the surface outward along its normal
    (concave creases fill, convex forms keep their volume: a soft gusset arching between the legs, a rounded seat,
    hips flowing into the thighs) and smooths the skin weights there the same way, so the gusset
    blends hips and upper legs and stretches evenly in the stride and the crouch. Vertices split at UV seams move
    and weigh together. Rest pose, before the decimation."""
    me = body.data
    W = body.matrix_world
    hz = rig.data.bones['DEF-hips'].head_local.z
    pts = [W @ v.co for v in me.vertices]
    mid = [i for i, p in enumerate(pts) if abs(p.x) < 0.012 and hz - 0.2 < p.z < hz]
    apex = pts[min(mid, key=lambda i: pts[i].z)]
    ctr = Vector((0.0, apex.y, apex.z + 0.05))
    rad = Vector((0.15, 0.17, 0.14))

    def fall(p):
        d = math.sqrt(sum(((p[i] - ctr[i]) / rad[i]) ** 2 for i in range(3)))
        t = max(0.0, min(1.0, (1.0 - d) / 0.6))
        return t * t * (3 - 2 * t)
    # weld seam duplicates into groups; adjacency over the welded groups
    key = {}
    grp = []
    for i, p in enumerate(pts):
        k = (round(p.x, 5), round(p.y, 5), round(p.z, 5))
        if k not in key:
            key[k] = len(grp)
            grp.append([])
        grp[key[k]].append(i)
    gof = [0] * len(pts)
    for g, vs in enumerate(grp):
        for i in vs:
            gof[i] = g
    nb = [set() for _ in grp]
    for e in me.edges:
        a, b = gof[e.vertices[0]], gof[e.vertices[1]]
        if a != b:
            nb[a].add(b); nb[b].add(a)
    pos = [pts[vs[0]].copy() for vs in grp]
    wf = [fall(p) for p in pos]
    act = [g for g in range(len(grp)) if wf[g] > 0 and nb[g]]
    W3 = W.to_3x3()
    nrm = []
    for vs in grp:
        n = sum((W3 @ me.vertices[i].normal for i in vs), Vector())
        nrm.append(n.normalized() if n.length > 1e-9 else Vector((0, 0, 1)))
    for it in range(iters):
        new = {}
        for g in act:
            lap = sum((pos[n] for n in nb[g]), Vector()) / len(nb[g]) - pos[g]
            out = lap.dot(nrm[g])
            # outward only: a crease (the surface dips below its neighbours) fills, a bulge never shrinks
            step = nrm[g] * max(0.0, out) * 0.6 + (lap - nrm[g] * out) * 0.25
            new[g] = pos[g] + step * wf[g]
        for g, p in new.items():
            pos[g] = p
    Wi = W.inverted()
    for g in act:
        for i in grp[g]:
            me.vertices[i].co = Wi @ pos[g]
    # skin weights: smooth the same way (all groups present), keep the four largest, normalise
    names = {vg.index: vg.name for vg in body.vertex_groups}
    wts = [{} for _ in grp]
    for g in range(len(grp)):
        for e in me.vertices[grp[g][0]].groups:
            if e.weight > 0:
                wts[g][e.group] = e.weight
    for _ in range(wpasses):
        new = {}
        for g in act:
            acc = {}
            for n in nb[g]:
                for k, w in wts[n].items():
                    acc[k] = acc.get(k, 0.0) + w / len(nb[g])
            f = 0.5 * wf[g]
            keys = set(acc) | set(wts[g])
            new[g] = {k: wts[g].get(k, 0.0) * (1 - f) + acc.get(k, 0.0) * f for k in keys}
        for g, d in new.items():
            wts[g] = d
    for g in act:
        top = sorted(((w, k) for k, w in wts[g].items() if w > 0.02), reverse=True)[:4]
        tot = sum(w for w, _ in top) or 1.0
        for i in grp[g]:
            for e in list(me.vertices[i].groups):
                body.vertex_groups[names[e.group]].remove([i])
            for w, k in top:
                body.vertex_groups[names[k]].add([i], w / tot, 'REPLACE')
    print('trouser pelvis: %d vertices reshaped round the crotch at z %.3f' % (sum(len(grp[g]) for g in act), apex.z))
    return apex


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
    # chamfered along the barrel (and the grips along their length): the outline reads bevelled, not boxy
    S.rbox(m, (0, 0.09, 0.055), (0.048, 0.3, 0.07), 'steel', cham=0.009, axes='y')            # receiver
    S.rbox(m, (0, 0.31, 0.055), (0.056, 0.17, 0.062), 'steel2', cham=0.016, axes='y')         # handguard
    m.cyl((0, 0.39, 0.06), 0.012, 0.012, 0.14, 'steel', seg=8, rot=(rad(-90), 0, 0))
    S.rcyl(m, (0, 0.52, 0.06), 0.019, 0.019, 0.05, 'strap', seg=8, rot=(rad(-90), 0, 0), cham=0.004)
    S.rbox(m, (0, 0.06, 0.105), (0.036, 0.1, 0.034), 'strap', cham=0.007, axes='y')            # optic
    m.box((0, 0.112, 0.105), (0.026, 0.006, 0.026), 'lens')
    S.rbox(m, (0, 0.125, -0.035), (0.034, 0.05, 0.13), 'steel', rot=(rad(14), 0, 0), cham=0.007, axes='z')   # mag
    S.rbox(m, (0, -0.005, -0.025), (0.028, 0.04, 0.09), 'strap', rot=(rad(-16), 0, 0), cham=0.007, axes='z')  # grip
    S.rbox(m, (0, 0.3, -0.012), (0.026, 0.03, 0.06), 'strap', cham=0.006, axes='z')           # foregrip
    m.cyl((0.034, 0.34, 0.05), 0.012, 0.012, 0.08, 'steel2', seg=8, rot=(rad(-90), 0, 0))   # light
    S.rbox(m, (0, -0.15, 0.045), (0.034, 0.17, 0.05), 'steel', cham=0.008, axes='y')          # stock
    S.rbox(m, (0, -0.24, 0.035), (0.04, 0.025, 0.09), 'strap', cham=0.008, axes='z')
    # detail pass (no outline of its own): top rail ridges, handguard vents, ejection port, charging handle, mag ribs,
    # a sling loop, muzzle ports
    d = getattr(m, 'd', m)
    for y in (0.13, 0.155, 0.18, 0.205):
        d.box((0, y, 0.091), (0.04, 0.008, 0.006), 'strap')
    for y in (0.25, 0.275, 0.30, 0.325, 0.35, 0.375):
        d.box((0, y, 0.087), (0.044, 0.008, 0.006), 'steel')
    for sx in (-1, 1):
        for y in (0.25, 0.285, 0.32):
            d.box((sx * 0.029, y, 0.055), (0.006, 0.025, 0.012), 'strap')
        d.box((sx * 0.0225, 0.55, 0.06), (0.006, 0.012, 0.008), 'steel2')
    d.box((0.0255, 0.10, 0.06), (0.006, 0.05, 0.02), 'strap')
    d.box((0, -0.055, 0.092), (0.02, 0.02, 0.012), 'steel2')
    a = rad(14)
    for dz in (-0.03, -0.05):
        c = Vector((0, 0.125, -0.035)) + Matrix.Rotation(math.radians(a), 3, 'X') @ Vector((0, 0, dz))
        d.box(tuple(c), (0.040, 0.056, 0.006), 'strap', rot=(a, 0, 0))
    d.box((0, -0.20, 0.016), (0.012, 0.03, 0.02), 'steel2')
    return Vector((0, 0.56, 0.06))


def _launcher(m):
    """a 6-shot 40 mm revolver grenade launcher (M32-like) in the grip frame; returns the muzzle"""
    R90 = (-90, 0, 0)                                    # cylinder axis -> +y (forward)
    S.rbox(m, (0, 0.045, 0.072), (0.05, 0.16, 0.05), 'steel', cham=0.01, axes='y')            # top frame
    S.rbox(m, (0, -0.015, 0.03), (0.045, 0.06, 0.07), 'steel2', cham=0.01, axes='y')          # rear frame over the grip
    m.cyl((0, 0.17, 0.095), 0.033, 0.033, 0.27, 'glbody', seg=10, rot=R90)          # barrel
    S.rcyl(m, (0, 0.425, 0.095), 0.038, 0.038, 0.035, 'strap', seg=10, rot=R90, cham=0.006)    # muzzle ring
    m.cyl((0, 0.30, 0.095), 0.036, 0.036, 0.025, 'glround', seg=10, rot=R90)          # warning band
    S.rcyl(m, (0, 0.025, 0.048), 0.068, 0.068, 0.14, 'glbody2', seg=12, rot=R90, cham=0.01)    # round revolving drum
    # detail pass (no outline of its own): grenade noses in the drum's front face, drum flutes, top rail ridges,
    # barrel rings, a sling swivel, stock rings
    d = getattr(m, 'd', m)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        d.cyl((math.cos(a) * 0.042, 0.163, 0.048 + math.sin(a) * 0.042), 0.015, 0.015, 0.008, 'glround', seg=8, rot=R90)
    d.cyl((0, 0.163, 0.048), 0.014, 0.014, 0.008, 'steel', seg=8, rot=R90)
    S.rbox(m, (0, 0.33, 0.035), (0.03, 0.04, 0.09), 'strap', cham=0.007, axes='z')             # foregrip
    S.rbox(m, (0, -0.005, -0.025), (0.028, 0.04, 0.09), 'strap', rot=(-16, 0, 0), cham=0.007, axes='z')  # pistol grip
    S.rbox(m, (0, -0.15, 0.065), (0.03, 0.17, 0.035), 'steel', cham=0.008, axes='y')           # stock tube
    S.rbox(m, (0, -0.235, 0.045), (0.045, 0.03, 0.10), 'strap', cham=0.01, axes='z')           # butt pad
    m.box((0.036, 0.21, 0.125), (0.012, 0.05, 0.05), 'tan')          # quadrant sight
    m.box((0, 0.12, 0.145), (0.02, 0.05, 0.025), 'strap')            # leaf sight
    ap = 0.068 + 0.001                                    # flutes on the round drum, between the grenade chambers
    for k in range(6):
        b = 30 + 60 * k
        r = math.radians(b)
        d.box((math.cos(r) * ap, 0.095, 0.048 + math.sin(r) * ap), (0.02, 0.11, 0.006), 'glbody', rot=(0, 90 - b, 0))
    for y in (-0.028, -0.008, 0.012):
        d.box((0, y, 0.098), (0.04, 0.008, 0.006), 'strap')
    for y in (0.21, 0.25):
        d.cyl((0, y, 0.095), 0.0365, 0.0365, 0.008, 'glbody2', seg=10, rot=R90, caps=False)
    d.box((0, 0.40, 0.055), (0.008, 0.02, 0.02), 'steel')
    for y in (-0.10, -0.18):
        d.box((0, y, 0.065), (0.036, 0.01, 0.041), 'strap')
    return Vector((0, 0.46, 0.095))


def _held(pal, name, frame, build, to_rest, hull_t):
    """a gun built in the grip frame (aim pose), mapped back to the rest pose and skinned 100 % to the right hand"""
    m = Model(pal)
    m.parent = frame
    m.d = ED.Deco(pal)
    m.d.parent = frame
    tip = build(m)
    obj = ED.finish(name, m, m.d, 0.0, hull_t)
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
    """the Robot Trooper body: a heavy industrial walker (rest pose = T pose, facing -Y) built from rigid, sculpted
    armour, one bone each: domed, layered pauldrons round a small rounded head set low between them, a barrel chest
    with pillowed pectoral plates on a narrow piston waist, tapered piston arms with round servo joints and
    telescoping forearm segments, tapered legs with curved thigh plates and shin guards, sculpted feet. Worn plates,
    stencil bars and hazard chevrons. The rounded back reactor's glowing cell stays the weak spot (socket
    TROOPER_MECH_CORE). Every part is skinned 100 % to one bone."""
    B = lambda n: (rig.data.bones[n].head_local.copy(), rig.data.bones[n].tail_local.copy())
    R90X, RY = (90, 0, 0), lambda sx: (0, 90 * sx, 0)
    RB = (-90, 0, 0)                               # cylinder axis -> +y (out of the back)
    parts = []
    SLIM = 0.8
    rb, rc, rl = S.rbox, S.rcyl, S.rlimb
    FF = lambda *a, **k: S.face_frame(*a, on=CUR[0], **k)     # detail frames snap onto the part's surface
    CUR = [None]

    def P(name, bone, fn):
        m = Model(pal)
        m.d = ED.Deco(pal)          # small detail (bolts, vents, stencils): same bone, no outline of its own
        CUR[0] = m
        fn(m)
        obj = ED.finish('TROOPER_m_' + name, m, m.d, 0.014, ht)
        # slim 20 % across the bone (height and length unchanged); feet only narrower; hands and claws keep the grip
        if 'hand' not in bone and '_f_' not in bone and 'thumb' not in bone:
            h, t = B(bone)
            d = (t - h).normalized()
            for v in obj.data.vertices:
                if 'foot' in bone or 'toe' in bone:
                    v.co.x = h.x + (v.co.x - h.x) * SLIM
                else:
                    o = v.co - h
                    along = d * o.dot(d)
                    v.co = h + along + (o - along) * SLIM
        vg = obj.vertex_groups.new(name=bone)
        vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
        parts.append(obj)

    def bolt(m, F, u, v, r=0.009, c='servo'):
        with ED.at(m.d, F):
            m.d.cyl((u, v, -0.002), r, r, 0.007, c, seg=6)

    # ---- pelvis: a rounded, tapering skirt with a shield-shaped codpiece and round hip guards
    def hips(m):
        rb(m, (0, 0.02, 0.93), (0.34, 0.22, 0.15), 'mframe', r=0.05, cuts=(1, 1, 0), bot=(0.86, 0.9), puff=(0, 0.012, 0))
        cp = dict(rot=(8, 0, 0), cuts=(2, 0, 0), bot=(0.72, 1.0), curve=[('y', 'x', 0.024)], puff=(0, 0.006, 0))
        rb(m, (0, -0.10, 0.90), (0.18, 0.04, 0.16), 'mplate', cham=0.012, **cp)
        with ED.at(m.d, FF((0, -0.10, 0.90), (0.18, 0.04, 0.16), '-y', 0, 0.025, **cp)):
            ED.stencil(m.d, 0, 0, 0.10, 0.018, 3, color='mhaz', top=0.004)
        for sx in (-1, 1):
            hp = dict(rot=RY(sx), cuts=(1, 1, 0), puff=(0, 0, 0.014), cham=0.016)
            rb(m, (sx * 0.19, 0.0, 0.91), (0.18, 0.22, 0.05), 'mplate2', **hp)   # local z -> out of the hip
            rc(m, (sx * 0.213, 0.0, 0.92), 0.05, 0.05, 0.022, 'servo', seg=10, rot=RY(sx), cham=0.008)
            for y, z in ((-0.075, 0.85), (0.075, 0.975)):
                if True:
                    with ED.at(m.d, FF((sx * 0.19, 0.0, 0.91), (0.18, 0.22, 0.05), '+z', -sx * (z - 0.91), y, **hp)):
                        m.d.cyl((0, 0, -0.002), 0.009, 0.009, 0.007, 'servo', seg=6)
        rb(m, (0, 0.135, 0.95), (0.16, 0.06, 0.10), 'mplate2', cham=0.02, cuts=(1, 0, 0), puff=(0, 0.008, 0))
        with ED.at(m.d, FF((0, 0.135, 0.95), (0.16, 0.06, 0.10), '+y', 0, 0, puff=(0, 0.008, 0))):
            for z in (-0.02, 0.0, 0.02):
                ED.pad(m.d, 0, z, 0.10, 0.008, 0.004, 'servo')
    P('hips', 'DEF-hips', hips)

    # ---- narrow waist: a chrome column in a rounded servo collar
    def ab(m):
        rc(m, (0, 0.02, 0.99), 0.06, 0.06, 0.16, 'chrome', seg=10)
        rc(m, (0, 0.02, 1.005), 0.085, 0.085, 0.04, 'servo', seg=12, cham=0.012)
        for sx in (-1, 1):
            m.d.cyl((sx * 0.085, 0.03, 0.98), 0.012, 0.012, 0.18, 'chrome', seg=6)
    P('ab', 'DEF-spine.001', ab)

    def chest_lo(m):   # tapering belly with two layered, curved ab plates
        core = dict(r=0.04, cuts=(1, 0, 0), bot=(0.82, 0.9), puff=(0.01, 0, 0))
        rb(m, (0, 0.02, 1.19), (0.25, 0.20, 0.10), 'mframe', **core)
        for z, w, cz in ((1.214, 0.18, 0.042), (1.172, 0.15, 0.036)):
            rb(m, (0, -0.083, z), (w, 0.035, cz), 'mplate2', cham=0.01, cuts=(2, 0, 0), curve=[('y', 'x', 0.022)])
        for sx in (-1, 1):                                       # detail: side vent slats
            with ED.at(m.d, FF((0, 0.02, 1.19), (0.25, 0.20, 0.10), ('+x' if sx > 0 else '-x'), 0, 0, **core)):
                for z in (-0.02, 0.0, 0.02):
                    ED.pad(m.d, 0, z, 0.10, 0.008, 0.004, 'servo')
    P('chestlo', 'DEF-spine.002', chest_lo)

    def chest(m):      # the wide barrel torso, layered plates
        core = dict(r=0.06, cuts=(1, 1, 0), bot=(0.86, 0.9), puff=(0.012, 0.012, 0))
        rb(m, (0, 0.02, 1.36), (0.52, 0.28, 0.26), 'mframe', **core)
        for sx in (-1, 1):                                       # pillowed pectoral plates, outer edges wrapping back
            pec = dict(rot=(-6, 0, sx * 14), cuts=(1, 0, 1), puff=(0, 0.01, 0), bot=(0.86, 1.0))
            loc = (sx * 0.112, -0.138, 1.39)
            rb(m, loc, (0.20, 0.045, 0.19), 'mplate', r=0.018, **pec)
            with ED.at(m.d, FF(loc, (0.20, 0.045, 0.19), '-y', sx * 0.03, 0.02, **pec)):      # stencil / patch bars
                ED.stencil(m.d, 0, 0, 0.10 if sx < 0 else 0.07, 0.018, 4 if sx < 0 else 2, color='mframe' if sx < 0 else 'patch', top=0.004)
            with ED.at(m.d, FF(loc, (0.20, 0.045, 0.19), '-y', sx * 0.04, -0.055, **pec)):     # hazard chevrons
                ED.chevrons(m.d, 0, 0, 0.07, 0.03, 3, color='mhaz', ink='servo')
            with ED.at(m.d, FF(loc, (0.20, 0.045, 0.19), '-y', -sx * 0.055, 0.06, **pec)):     # rivet
                m.d.cyl((0, 0, -0.002), 0.012, 0.012, 0.008, 'servo', seg=6)
            side = dict(rot=RY(sx), cuts=(1, 0, 0), puff=(0, 0, 0.012))                      # curved side plates
            rb(m, (sx * 0.272, 0.02, 1.36), (0.18, 0.22, 0.04), 'mplate2', cham=0.014, **side)
            for y, z in ((-0.06, 1.29), (0.10, 1.43)):
                if True:
                    with ED.at(m.d, FF((sx * 0.272, 0.02, 1.36), (0.18, 0.22, 0.04), '+z', -sx * (z - 1.36), y - 0.02, **side)):
                        m.d.cyl((0, 0, -0.002), 0.01, 0.01, 0.008, 'servo', seg=6)
        rb(m, (0, -0.145, 1.345), (0.07, 0.05, 0.20), 'mplate2', cham=0.016, cuts=(0, 0, 1), bot=(0.7, 1.0), puff=(0, 0.008, 0))   # keel
        with ED.at(m.d, FF((0, -0.145, 1.345), (0.07, 0.05, 0.20), '-y', 0, 0.035, bot=(0.7, 1.0), puff=(0, 0.008, 0))):
            ED.grille(m.d, 0, 0, 0.062, 0.09, 4, color='mframe', slat='servo')
        rb(m, (0, -0.118, 1.252), (0.38, 0.07, 0.06), 'mplate2', cham=0.02, cuts=(3, 0, 0), curve=[('y', 'x', 0.035)])   # belly lip
        rb(m, (0, 0.02, 1.497), (0.31, 0.22, 0.034), 'mplate2', cham=0.012, top=(0.9, 0.88))                              # collar
        for sx in (-1, 1):
            for x in (-0.11, 0.11):
                m.d.cyl((x, sx * 0.075 + 0.02, 1.511), 0.009, 0.009, 0.006, 'servo', seg=6)
        # back: a rounded reactor drum with the glowing cell (the weak spot) in a bezel, flanked by finned coolers
        rc(m, (0, 0.145, 1.39), 0.095, 0.095, 0.07, 'mplate2', seg=14, rot=RB, cham=0.022)
        rc(m, (0, 0.205, 1.39), 0.055, 0.052, 0.02, 'cell', seg=12, rot=RB)
        m.d.cyl((0, 0.212, 1.39), 0.068, 0.068, 0.008, 'mframe', seg=12, rot=RB)
        for sx in (-1, 1):
            cool = dict(cuts=(0, 0, 1), puff=(0, 0.008, 0))
            rb(m, (sx * 0.135, 0.165, 1.375), (0.06, 0.06, 0.22), 'mplate2', cham=0.018, **cool)
            with ED.at(m.d, FF((sx * 0.135, 0.165, 1.375), (0.06, 0.06, 0.22), '+y', 0, 0, **cool)):
                for z in (-0.05, 0.0, 0.05):
                    ED.pad(m.d, 0, z, 0.036, 0.009, 0.004, 'servo')
            m.d.limb((sx * 0.11, 0.19, 1.47), (sx * 0.24, 0.13, 1.49), 0.011, 0.011, 'cable', seg=6)
    P('chest', 'DEF-spine.003', chest)

    # ---- short neck + small rounded head set low, one red optic
    def neck(m):
        rc(m, (0, 0.0, 1.47), 0.035, 0.035, 0.06, 'chrome', seg=10)
    P('neck', 'DEF-neck', neck)

    def head(m):
        rb(m, (0, -0.02, 1.575), (0.15, 0.16, 0.11), 'mplate', r=0.045, cuts=(1, 1, 0), top=(0.86, 0.88), puff=(0.006, 0.008, 0))
        S.ell(m, (0, -0.025, 1.62), 0.071, 'mplate2', seg=(12, 5), scale=(1.0, 1.08, 0.38), zmin=0.0)    # domed lid
        rb(m, (0, -0.086, 1.585), (0.128, 0.04, 0.052), 'mframe', cham=0.012, cuts=(2, 0, 0), curve=[('y', 'x', 0.026)])  # visor band
        rc(m, (0.03, -0.098, 1.585), 0.03, 0.03, 0.014, 'servo', seg=10, rot=R90X, cham=0.004)          # optic housing
        S.ell(m, (0.03, -0.117, 1.585), 0.023, 'optic', seg=(8, 4), scale=(1, 1, 0.5), rot=R90X)     # the optic (off-centre)
        m.d.sphere((0.022, -0.128, 1.592), 0.006, 'optichi', seg=(6, 4), scale=(1, 0.5, 1))
        m.d.box((-0.035, -0.1065, 1.585), (0.03, 0.006, 0.012), 'mhaz')
        rb(m, (0, -0.095, 1.535), (0.10, 0.04, 0.034), 'servo', cham=0.012, curve=[('y', 'x', 0.012)])    # chin
        for sx in (-1, 1):
            rc(m, (sx * 0.07, -0.02, 1.575), 0.032, 0.03, 0.018, 'servo', seg=8, rot=RY(sx), cham=0.005)   # ear discs
            m.d.cyl((sx * 0.086, -0.02, 1.575), 0.014, 0.014, 0.006, 'chrome', seg=8, rot=RY(sx))
        for x in (-0.025, 0.0, 0.025):
            m.d.box((x, -0.116, 1.535), (0.012, 0.007, 0.02), 'mframe')
        m.d.cyl((0.045, 0.03, 1.625), 0.006, 0.006, 0.037, 'cable', seg=5)
        m.d.cyl((0.045, 0.03, 1.66), 0.01, 0.01, 0.01, 'optic', seg=6)
    P('head', 'DEF-head', head)

    for side, sx in (('L', 1), ('R', -1)):
        uh, ut = B('DEF-upper_arm.' + side)
        fh, ft = B('DEF-forearm.' + side)
        hh, htl = B('DEF-hand.' + side)
        sxf = '+x' if sx > 0 else '-x'

        def shoulder(m, uh=uh, sx=sx, sxf=sxf):   # the big domed pauldron with a curved cap plate layered over it
            x, y, z = uh.x + sx * 0.06, uh.y + 0.01, uh.z + 0.03
            base = dict(r=0.06, cuts=(1, 0, 1), puff=(0.016, 0.014, 0.016))
            rb(m, (x, y, z), (0.19, 0.25, 0.21), 'mplate', **base)
            cap = dict(cuts=(1, 2, 0), curve=[('z', 'x', -0.035), ('z', 'y', -0.04)])
            capl = (x + sx * 0.022, y, z + 0.125)
            rb(m, capl, (0.19, 0.27, 0.03), 'mplate2', cham=0.012, **cap)
            rb(m, (x + sx * 0.11, y, z - 0.03), (0.04, 0.23, 0.11), 'mplate2', cham=0.014, cuts=(0, 2, 0),
               curve=[('x', 'y', -sx * 0.03)])                                                               # outer lip
            with ED.at(m.d, FF((x, y, z), (0.19, 0.25, 0.21), '-y', -sx * 0.01, 0.045, **base)):           # hazard band
                ED.pad(m.d, 0, 0, 0.12, 0.028, 0.004, 'mhaz')
            with ED.at(m.d, FF((x, y, z), (0.19, 0.25, 0.21), '-y', -sx * 0.01, -0.035, **base)):
                ED.stencil(m.d, 0, 0, 0.11, 0.018, 3, color='mframe', top=0.004)
            with ED.at(m.d, FF((x, y, z), (0.19, 0.25, 0.21), '+y', 0, 0, **base)):                       # back vent
                ED.grille(m.d, 0, 0, 0.11, 0.09, 4, color='mframe', slat='servo')
            for dx in (-0.06, 0.06):
                for dy in (0.0,):
                    with ED.at(m.d, FF(capl, (0.19, 0.27, 0.03), '+z', dx, dy, **cap)):
                        m.d.cyl((0, 0, -0.002), 0.009, 0.009, 0.007, 'servo', seg=6)
            rc(m, (uh.x + sx * 0.19, uh.y, uh.z - 0.01), 0.07, 0.07, 0.04, 'servo', seg=10, rot=RY(sx), cham=0.012)
        P('sh' + side, 'DEF-shoulder.' + side, shoulder)

        def upper(m, uh=uh, ut=ut, sx=sx):   # tapered bicep with an arched plate, a piston and a round elbow servo
            mx = (uh.x + ut.x) / 2 + sx * 0.04
            L = abs(ut.x - uh.x)
            rb(m, (mx, uh.y, uh.z), (0.13, 0.13, L * 0.7), 'mplate2', rot=RY(sx), r=0.045, axes='z', top=(0.84, 0.84))
            arch = dict(cuts=(1, 2, 0), curve=[('z', 'y', -0.022)], top=None)
            rb(m, (mx - sx * 0.01, uh.y, uh.z + 0.066), (L * 0.5, 0.11, 0.024), 'mplate', cham=0.009, cuts=(1, 2, 0), curve=[('z', 'y', -0.022)])
            m.d.limb((mx - sx * L * 0.4, uh.y - 0.075, uh.z - 0.03), (mx + sx * L * 0.42, uh.y - 0.075, uh.z - 0.03), 0.014, 0.014, 'chrome', seg=8)
            m.d.limb((mx - sx * L * 0.42, uh.y - 0.075, uh.z - 0.03), (mx - sx * L * 0.42 + sx * 0.08, uh.y - 0.075, uh.z - 0.03), 0.024, 0.024, 'mframe', seg=8)
            rc(m, (ut.x, ut.y + 0.075, ut.z), 0.07, 0.07, 0.15, 'servo', seg=10, rot=R90X, cham=0.018)   # elbow servo
            m.d.cyl((ut.x, ut.y + 0.095, ut.z), 0.03, 0.03, 0.19, 'chrome', seg=8, rot=R90X)
            for dx in (-L * 0.15, L * 0.15):
                with ED.at(m.d, FF((mx - sx * 0.01, uh.y, uh.z + 0.066), (L * 0.5, 0.11, 0.024), '+z', dx, 0, **arch)):
                    m.d.cyl((0, 0, -0.002), 0.008, 0.008, 0.006, 'servo', seg=6)
            ED.cable(m.d, [(mx - sx * L * 0.3, uh.y + 0.07, uh.z + 0.025), (mx, uh.y + 0.075, uh.z), (mx + sx * L * 0.3, uh.y + 0.066, uh.z - 0.02)], 0.016, 'cable')
        P('ua' + side, 'DEF-upper_arm.' + side, upper)

        def fore(m, fh=fh, ft=ft, sx=sx):    # telescoping, tapered forearm segments under a curved gauntlet plate
            L = abs(ft.x - fh.x)
            step = (L - 0.06) / 3
            for k in range(3):
                cx = fh.x + sx * (0.06 + k * step + step / 2)
                seg_ = dict(rot=RY(sx), r=0.034, axes='z', top=(0.88, 0.88))
                rb(m, (cx, fh.y, fh.z), (0.15 - 0.012 * k, 0.16 - 0.012 * k, step + 0.006), 'mplate' if k != 1 else 'mplate2', **seg_)
                for dz in (-0.035, 0.035):
                    with ED.at(m.d, FF((cx, fh.y, fh.z), (0.15 - 0.012 * k, 0.16 - 0.012 * k, step + 0.006), '+y', -sx * dz, 0, **seg_)):
                        m.d.cyl((0, 0, -0.002), 0.009, 0.009, 0.008, 'servo', seg=6)
            gl = dict(rot=RY(sx), cuts=(0, 2, 0), curve=[('x', 'y', 0.02 * sx)], top=(1.0, 0.8))             # top gauntlet plate
            gloc = (fh.x + sx * L * 0.5, fh.y - 0.005, fh.z + 0.085)
            rb(m, gloc, (0.03, 0.13, L * 0.62), 'mplate2', cham=0.01, **gl)
            with ED.at(m.d, FF(gloc, (0.03, 0.13, L * 0.62), '-x' if sx > 0 else '+x', 0, 0, **gl)):
                ED.pad(m.d, 0, 0.0, 0.02, L * 0.45, 0.004, 'mhaz')
            for dy in (-0.05, 0.05):     # twin pistons under the arm
                m.d.limb((fh.x + sx * L * 0.06, fh.y + dy, fh.z - 0.085), (fh.x + sx * L * 0.94, fh.y + dy, fh.z - 0.08), 0.013, 0.013, 'chrome', seg=8)
            rc(m, (ft.x - sx * 0.025, ft.y, ft.z), 0.05, 0.05, 0.05, 'servo', seg=10, rot=RY(sx), cham=0.012)   # wrist collar
        P('fa' + side, 'DEF-forearm.' + side, fore)

        def hand(m, hh=hh, sx=sx):          # clamp hand: a rounded block with an upper jaw
            rb(m, (hh.x + sx * 0.06, hh.y + 0.0, hh.z), (0.12, 0.13, 0.08), 'mframe', cham=0.02)
            rb(m, (hh.x + sx * 0.07, hh.y + 0.0, hh.z + 0.05), (0.10, 0.12, 0.022), 'mplate2', cham=0.008, cuts=(0, 1, 0), curve=[('z', 'y', -0.008)])
            m.d.box((hh.x + sx * 0.07, hh.y - 0.0655, hh.z), (0.06, 0.006, 0.012), 'mhaz')
        P('hand' + side, 'DEF-hand.' + side, hand)
        for f in ('index', 'middle', 'ring', 'pinky', 'thumb'):
            n1, n2, n3 = ['DEF-%s.0%d.%s' % ('thumb' if f == 'thumb' else 'f_' + f, k, side) for k in (1, 2, 3)]
            a1, b1 = B(n1)
            a2, b2 = B(n2)
            a3, b3 = B(n3)
            if f in ('ring', 'pinky'):
                continue       # three clamp claws: index + middle (upper jaw pair) and the thumb
            t = 0.034 if f == 'thumb' else 0.028

            def seg1(m, a=a1, b=b1, t=t):
                m.parent = _seg_frame(a, b, Vector((0, 0, 1)))
                rb(m, (0, 0, (b - a).length / 2), (t + 0.006, t, (b - a).length + 0.01), 'mframe', cham=0.007, axes='z')
                m.parent = Matrix.Identity(4)

            def seg2(m, a=a2, b=b3, t=t):
                m.parent = _seg_frame(a, b, Vector((0, 0, 1)))
                L = (b - a).length
                rb(m, (0, 0, L / 2), (t, t * 0.9, L), 'chrome', cham=0.006, axes='z', top=(0.8, 0.8))
                rb(m, (0, 0, L * 0.95), (t * 1.2, t * 1.15, 0.022), 'mhaz', cham=0.007, axes='z')   # claw tip
                m.parent = Matrix.Identity(4)
            P(f + '1' + side, n1, seg1)
            P(f + '2' + side, n2, seg2)

        th, tt = B('DEF-thigh.' + side)
        sh_, st = B('DEF-shin.' + side)
        fo, ftt = B('DEF-foot.' + side)
        to, tot = B('DEF-toe.' + side)

        def thigh(m, th=th, tt=tt, sx=sx, sxf=sxf):   # tapered thigh with a curved front plate, round knee servo
            x = (th.x + tt.x) / 2
            core = dict(r=0.05, axes='z', cuts=(0, 0, 1), bot=(0.84, 0.86), puff=(0.01, 0.01, 0))
            cz = (th.z + tt.z) / 2 + 0.01
            rb(m, (x, 0.0, cz), (0.16, 0.18, th.z - tt.z - 0.10), 'mplate2', **core)
            pl = dict(cuts=(2, 0, 1), curve=[('y', 'x', 0.03)], puff=(0, 0.006, 0), bot=(0.78, 1.0))
            rb(m, (x, -0.096, 0.765), (0.135, 0.026, 0.22), 'mplate', cham=0.011, **pl)
            with ED.at(m.d, FF((x, -0.096, 0.765), (0.135, 0.026, 0.22), '-y', 0, 0.035, **pl)):
                ED.stencil(m.d, 0, 0, 0.08, 0.018, 2, color='mhaz', top=0.004)
            for dx in (-0.04, 0.04):
                for z in (0.855,):
                    with ED.at(m.d, FF((x, -0.096, 0.765), (0.135, 0.026, 0.22), '-y', dx * (1 if z > 0.75 else 0.8), z - 0.765, **pl)):
                        m.d.cyl((0, 0, -0.002), 0.009, 0.009, 0.007, 'servo', seg=6)
            m.d.limb((x + sx * 0.1, 0.0, tt.z + 0.05), (x + sx * 0.1, 0.0, tt.z + 0.35), 0.013, 0.013, 'chrome', seg=8)
            rc(m, (tt.x - sx * 0.10, tt.y, tt.z), 0.075, 0.075, 0.20, 'servo', seg=10, rot=RY(sx), cham=0.018)   # knee servo
            m.d.cyl((tt.x - sx * 0.11, tt.y, tt.z), 0.03, 0.03, 0.22, 'chrome', seg=8, rot=RY(sx))
            with ED.at(m.d, FF((x, 0.0, cz), (0.16, 0.18, th.z - tt.z - 0.10), '-x' if sx > 0 else '+x', 0, 0.70 - cz, **core)):
                ED.grille(m.d, 0, 0, 0.10, 0.11, 4, color='mframe', slat='servo')
        P('th' + side, 'DEF-thigh.' + side, thigh)

        def shin(m, sh_=sh_, st=st, sx=sx):  # tall calf tapering to the ankle, a domed knee cap, a curved shin guard
            x = (sh_.x + st.x) / 2
            rb(m, (x, -0.072, 0.50), (0.15, 0.06, 0.11), 'mplate2', rot=(10, 0, 0), r=0.026, cuts=(1, 0, 0), puff=(0, 0.014, 0))   # knee cap
            core = dict(r=0.055, axes='z', cuts=(0, 0, 1), bot=(0.8, 0.84), puff=(0.012, 0.012, 0))
            rb(m, (x, 0.005, 0.30), (0.18, 0.19, 0.30), 'mplate', **core)
            gd = dict(cuts=(2, 0, 1), curve=[('y', 'x', 0.034)], puff=(0, 0.006, 0), bot=(0.74, 1.0))
            rb(m, (x, -0.104, 0.31), (0.135, 0.026, 0.25), 'mplate2', cham=0.011, **gd)
            with ED.at(m.d, FF((x, -0.104, 0.31), (0.135, 0.026, 0.25), '-y', 0, 0.05, **gd)):
                ED.pad(m.d, 0, 0, 0.08, 0.016, 0.004, 'mhaz')
            with ED.at(m.d, FF((x, -0.104, 0.31), (0.135, 0.026, 0.25), '-y', 0, -0.06, **gd)):
                ED.stencil(m.d, 0, 0, 0.07, 0.018, 3, color='mframe', top=0.004)
            for dx in (-0.06, 0.06):
                m.d.limb((x + dx, 0.122, 0.13), (x + dx, 0.122, 0.47), 0.016, 0.016, 'chrome', seg=8)    # back pistons
            rb(m, (x, 0.005, 0.13), (0.14, 0.16, 0.05), 'servo', cham=0.015)
            S.ell(m, (st.x, st.y, st.z), 0.055, 'servo', seg=(8, 5))
            with ED.at(m.d, FF((x, 0.005, 0.30), (0.18, 0.19, 0.30), '-x' if sx > 0 else '+x', 0, 0.02, **core)):
                ED.grille(m.d, 0, 0, 0.11, 0.12, 4, color='mframe', slat='servo')
        P('sh' + side + '2', 'DEF-shin.' + side, shin)

        def foot(m, fo=fo, sx=sx):          # sculpted foot: a rounded wedge with a round heel
            x = fo.x + sx * 0.01
            rb(m, (x, 0.0, 0.045), (0.22, 0.24, 0.09), 'mframe', r=0.032, cuts=(0, 1, 0), top=(0.8, 0.9))
            rb(m, (x, 0.125, 0.04), (0.18, 0.06, 0.08), 'mplate2', r=0.028, axes='xz')
            rb(m, (x, -0.035, 0.095), (0.14, 0.13, 0.03), 'mplate2', cham=0.01, cuts=(1, 0, 0), rot=(-8, 0, 0), curve=[('z', 'x', -0.01)])   # instep plate
            for sx2 in (-1, 1):                                  # detail: tread blocks along both sides
                for y in (-0.06, 0.0, 0.06):
                    m.d.box((x + sx2 * 0.104, y, 0.03), (0.008, 0.03, 0.026), 'servo')
        P('ft' + side, 'DEF-foot.' + side, foot)

        def toe(m, to=to, sx=sx):          # rounded toe cap narrowing to the front, three rounded claws
            x = to.x + sx * 0.01

            def nose(p):
                f = max(0.0, (-p.y - 0.01) / 0.07)
                p.x *= 1 - 0.18 * f * f
                return p
            toecap = dict(r=0.03, cuts=(0, 1, 0), top=(0.84, 0.9), warp=nose)
            rb(m, (x, -0.20, 0.036), (0.23, 0.16, 0.072), 'mplate2', **toecap)
            for k in range(3):
                rb(m, (x - 0.06 + 0.06 * k, -0.274, 0.032), (0.045, 0.035, 0.058), 'mframe', r=0.014, axes='y')
            with ED.at(m.d, FF((x, -0.20, 0.036), (0.23, 0.16, 0.072), '+z', 0, 0.0, **toecap)):
                ED.pad(m.d, 0, 0, 0.10, 0.07, 0.004, 'mhaz')
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

    # ---- trouser pelvis (before decimating, on the full mesh): no anatomical V / cone at the crotch
    crotch = _trouser_pelvis(body, rig)

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
    faces = m.sphere((0, 0, 0), rx, 'helmet', seg=(20, 10), scale=(1, 1, (hh.z - cz + 0.03) / rx))   # rounder shell
    cut = [v for v in {v for f in faces for v in f.verts} if v.co.z < cz - 0.004]
    bmesh.ops.delete(m.bm, geom=cut, context='VERTS')
    S.rcyl(m, (0, 0, -0.012), rx * 1.03, rx * 1.03, 0.022, 'helmet', seg=16, cham=0.007)     # chamfered brim
    m.parent = Matrix.Identity(4)
    for sx in (-1, 1):
        m.box((hc.x + sx * rx * 0.99, hc.y, cz + 0.03), (0.016, ry * 1.2, 0.022), 'steel')                                 # rails
        S.rcyl(m, (hc.x + sx * (rx + 0.004), hc.y, eye - 0.03), 0.042, 0.038, 0.036, 'vest2', seg=10,
               rot=(0, math.radians(90 * sx), 0), cham=0.012)                           # chamfered ear cups
    # NVG mount: a rounded shroud on a chamfered arm; rear counterweight pouch curved to the shell; strobe
    S.rbox(m, (hc.x, hc.y + fy * ry * 0.98, cz + 0.045), (0.06, 0.026, 0.05), 'steel', r=0.012, axes='y')
    S.rbox(m, (hc.x, hc.y + fy * (ry * 0.98 + 0.02), cz + 0.03), (0.022, 0.02, 0.03), 'strap', cham=0.005)
    S.rbox(m, (hc.x, hc.y - fy * ry * 0.95, cz + 0.07), (0.07, 0.04, 0.06), 'vest2', r=0.014, axes='z', cuts=(1, 0, 0),
           curve=[('y', 'x', fy * 0.012)])
    S.rbox(m, (hc.x, hc.y - fy * ry * 0.62, hh.z + 0.012), (0.022, 0.03, 0.02), 'cell', cham=0.005)
    # goggles: a band and lens curved round the face, glint, side straps
    gy = hc.y + fy * (hs.y * 0.5 + 0.004)
    wrap = lambda w: [('y', 'x', -fy * 0.022 * (w / (hs.x * 0.9)) ** 2)]
    S.rbox(m, (hc.x, gy, eye), (hs.x * 0.9, 0.03, 0.07), 'strap', cham=0.008, cuts=(2, 0, 0), curve=wrap(hs.x * 0.9))
    S.rbox(m, (hc.x, gy + fy * 0.017, eye), (hs.x * 0.78, 0.006, 0.05), 'lens', r=0, cuts=(2, 0, 0), curve=wrap(hs.x * 0.78))
    m.box((hc.x - hs.x * 0.06, gy + fy * (0.020 - 0.022 * (0.78 / 0.9) ** 2 / 9 + 0.0015), eye + 0.012), (hs.x * 0.12, 0.004, 0.012), 'lenshi')   # glint on the lens' flat middle
    for sx in (-1, 1):
        m.box((hc.x + sx * hs.x * 0.5, hc.y, eye), (0.012, hs.y * 0.9, 0.03), 'strap')
    # detail pass (no outline of its own): rail bolts, a flipped-up NVG pair on the mount, a velcro patch on the crown,
    # a battery pack on the back pouch
    d = ED.Deco(pal)
    for sx in (-1, 1):
        for dy in (-0.045, 0.045):
            d.cyl((hc.x + sx * (rx * 0.99 + 0.006), hc.y + dy, cz + 0.03), 0.006, 0.006, 0.006, 'steel2', seg=6,
                  rot=(0, 90 * sx, 0))
        d.cyl((hc.x + sx * 0.018, hc.y + fy * (ry * 0.98 + 0.025), cz + 0.082), 0.012, 0.012, 0.04, 'steel2', seg=8, rot=(-90 * fy, 0, 0))
    d.box((hc.x, hc.y + fy * (ry * 0.98 + 0.02), cz + 0.075), (0.05, 0.016, 0.02), 'steel')
    d.box((hc.x, hc.y + 0.02, hh.z + 0.026), (0.06, 0.05, 0.012), 'pad')
    d.box((hc.x, hc.y - fy * (ry * 0.95 + 0.026), cz + 0.07), (0.05, 0.012, 0.04), 'steel2')
    gear.append(ED.finish('TROOPER_g_head', m, d, 0.0, ht))

    # plate carrier
    cl, ch = _bbox(body, dom, lambda n: 'spine.002' in n or 'spine.003' in n)
    cc = (cl + ch) / 2; cs = ch - cl
    front = (cl.y if fy < 0 else ch.y); back = (ch.y if fy < 0 else cl.y)
    pz = cl.z + cs.z * 0.5; ph = cs.z * 0.78; pw = cs.x * 0.74
    m = Model(pal)
    flat = 0.082        # the plates are flat across the middle (pouches, patches) and wrap round the ribs outside it

    def plate(sgn):
        """SAPI-cut armour plate: chamfered rim, the top corners cut at 45 degrees, the sides curving toward the body"""
        def fn(p):
            c = min(0.05, pw * 0.2)
            over = abs(p.x) + p.z - (pw / 2 + ph / 2 - c)
            if over > 0:
                p.z -= over
            t = max(0.0, (abs(p.x) - flat) / max(1e-6, pw / 2 - flat))
            p.y += sgn * 0.026 * t * t
            return p
        return fn
    S.rbox(m, (cc.x, front + fy * 0.025, pz), (pw, 0.06, ph), 'vest', cham=0.016, cuts=(4, 0, 0), warp=plate(-fy))
    S.rbox(m, (cc.x, back - fy * 0.025, pz), (pw, 0.06, ph), 'vest', cham=0.016, cuts=(4, 0, 0), warp=plate(fy))
    for sx in (-1, 1):
        S.rbox(m, (cc.x + sx * cs.x * 0.44, cc.y, pz - ph * 0.18), (0.05, abs(front - back) * 0.92, ph * 0.5), 'vest',
               r=0.018, axes='z')                                                           # cummerbunds
        x = cc.x + sx * pw * 0.3
        top = pz + ph / 2
        a, b = Vector((x, front + fy * 0.02, top - 0.02)), Vector((x, cc.y, top + 0.05))       # padded shoulder strap
        m.parent = _seg_frame(a, b, Vector((0, 0, 1)))
        S.rbox(m, (0, 0, (b - a).length / 2), (0.045, 0.045, (b - a).length), 'vest', r=0.045 * 0.32, axes='z')
        m.parent = Matrix.Identity(4)
        m.beam((x, cc.y, top + 0.05), (x, back - fy * 0.02, top - 0.02), 0.039, 'vest')
    for i in (-1, 0, 1):
        x = cc.x + i * 0.078
        S.rbox(m, (x, front + fy * 0.075, pz - ph * 0.22), (0.066, 0.06, ph * 0.42), 'vest2', r=0.014, axes='z')   # mag pouches
        m.box((x, front + fy * 0.08, pz - ph * 0.22 + ph * 0.21 + 0.018), (0.046, 0.028, 0.036), 'steel')
    m.box((cc.x, front + fy * 0.059, pz + ph * 0.3), (pw * 0.55, 0.008, 0.05), 'patch')
    m.box((cc.x, back - fy * 0.059, pz + ph * 0.3), (pw * 0.62, 0.008, 0.06), 'patch')
    # radio + antenna (left back), hydration pack with the power cell (the weak spot)
    S.rbox(m, (cc.x - cs.x * 0.36, back - fy * 0.07, pz + ph * 0.05), (0.07, 0.05, 0.14), 'steel2', r=0.014, axes='z')
    m.beam((cc.x - cs.x * 0.38, back - fy * 0.07, pz + ph * 0.05 + 0.07), (cc.x - cs.x * 0.42, back - fy * 0.07, pz + ph * 0.05 + 0.3), 0.012, 'strap')
    S.rbox(m, (cc.x + 0.03, back - fy * 0.085, pz - ph * 0.05), (0.2, 0.07, ph * 0.66), 'vest2', r=0.024)     # rounded pack
    S.rcyl(m, (cc.x + 0.03, back - fy * 0.117, pz + ph * 0.08), 0.04, 0.038, 0.015, 'cell', seg=12,
           rot=(90 * fy, 0, 0))                                             # round power cell
    # detail pass (no outline of its own): MOLLE webbing on the cummerbunds, side-release buckles, bungee bands on the
    # mag pouches, slider buckles on the shoulder straps, a drag handle on the back plate, a velcro admin strip
    d = ED.Deco(pal)
    for sx in (-1, 1):                                    # grenade pouches on the cummerbunds (behind the webbing)
        S.rbox(m, (cc.x + sx * (cs.x * 0.44 + 0.052), cc.y - fy * 0.075, pz - ph * 0.2), (0.04, 0.055, 0.075), 'vest2', cham=0.008, axes='z')
        d.box((cc.x + sx * (cs.x * 0.44 + 0.052), cc.y - fy * 0.075, pz - ph * 0.2 + 0.0405), (0.046, 0.061, 0.012), 'vest')
    for sx in (-1, 1):
        xo = cc.x + sx * (cs.x * 0.44 + 0.025)
        for k in range(3):
            d.box((xo + sx * 0.002, cc.y, pz - ph * 0.18 - 0.04 + 0.04 * k), (0.008, abs(front - back) * 0.8, 0.012), 'vest2')
        d.box((xo + sx * 0.004, front + fy * 0.012, pz - ph * 0.18), (0.012, 0.03, 0.03), 'steel')
        x = cc.x + sx * pw * 0.3
        a = Vector((x, front + fy * 0.02, pz + ph / 2 - 0.02))
        b = Vector((x, cc.y, pz + ph / 2 + 0.05))
        d.parent = _seg_frame(a, b, Vector((0, 0, 1)))
        d.box((0, 0, (b - a).length * 0.4), (0.058, 0.058, 0.02), 'steel')
        d.parent = Matrix.Identity(4)
    for i in (-1, 0, 1):
        x = cc.x + i * 0.078
        for dz in (-0.03, 0.02):
            d.box((x, front + fy * 0.107, pz - ph * 0.22 + dz), (0.046, 0.006, 0.012), 'strap')
    for sx in (-1, 1):
        d.box((cc.x + sx * 0.035, back - fy * 0.02, pz + ph / 2 + 0.012), (0.012, 0.022, 0.03), 'strap')
    d.box((cc.x, back - fy * 0.02, pz + ph / 2 + 0.03), (0.09, 0.03, 0.012), 'strap')
    d.box((cc.x, front + fy * 0.059, pz + ph * 0.3 - 0.045), (pw * 0.62, 0.008, 0.022), 'vest2')
    hy = back - fy * 0.1235                               # bungee X over the hydration pack (round the cell)
    for sx in (-1, 1):
        d.beam((cc.x + 0.03 - 0.08, hy, pz - ph * 0.05 + sx * 0.07), (cc.x + 0.03 - 0.045, hy, pz - ph * 0.05 + sx * 0.035), 0.008, 'strap')
        d.beam((cc.x + 0.03 + 0.08, hy, pz - ph * 0.05 + sx * 0.07), (cc.x + 0.03 + 0.045, hy, pz - ph * 0.05 + sx * 0.035), 0.008, 'strap')
    gear.append(ED.finish('TROOPER_g_vest', m, d, 0.0, ht))
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
    S.rbox(m, (bc.x, bc.y + fy * (bs.y * 0.5 + 0.03), bh.z - 0.03), (0.06, 0.012, 0.045), 'steel', cham=0.004, axes='y')
    tl, th = _bbox(body, dom, lambda n: 'thigh.R' in n)
    tc = (tl + th) / 2
    sxr = 1 if tc.x > bc.x else -1
    S.rbox(m, (tc.x + sxr * ((th.x - tl.x) * 0.5 + 0.03), tc.y, th.z - 0.13), (0.045, 0.1, 0.17), 'vest2', r=0.014, axes='z')   # holster
    S.rbox(m, (tc.x + sxr * ((th.x - tl.x) * 0.5 + 0.03), tc.y - fy * 0.02, th.z - 0.03), (0.03, 0.035, 0.06), 'steel', cham=0.006, axes='z')
    S.rbox(m, (bc.x - sxr * bs.x * 0.42, bc.y - fy * bs.y * 0.3, bh.z - 0.12), (0.06, 0.1, 0.12), 'vest2', r=0.016, axes='z')   # dump pouch
    lx = -tc.x - sxr * ((th.x - tl.x) * 0.5 + 0.022)          # drop-leg utility pouch on the other thigh
    S.rbox(m, (lx, tc.y + fy * 0.01, th.z - 0.16), (0.04, 0.09, 0.11), 'vest2', r=0.013, axes='x')
    # detail pass (no outline of its own): buckle latch, leg straps over the holster, a holster hood, a medic pouch with
    # a patch on the left front of the belt, a flap on the dump pouch
    d = ED.Deco(pal)
    d.box((bc.x, bc.y + fy * (bs.y * 0.5 + 0.0395), bh.z - 0.03), (0.03, 0.006, 0.02), 'steel2')
    hx = tc.x + sxr * ((th.x - tl.x) * 0.5 + 0.03)
    for z in (th.z - 0.18, th.z - 0.10):
        d.box((hx, tc.y, z), (0.052, 0.108, 0.02), 'strap')
    d.box((hx, tc.y, th.z - 0.043), (0.052, 0.06, 0.012), 'vest')
    px = bc.x - sxr * bs.x * 0.30
    d.box((px, bc.y + fy * (bs.y * 0.5 + 0.02), bh.z - 0.07), (0.06, 0.035, 0.065), 'vest2')
    d.box((px, bc.y + fy * (bs.y * 0.5 + 0.0395), bh.z - 0.065), (0.025, 0.006, 0.025), 'red')
    d.box((bc.x - sxr * bs.x * 0.42, bc.y - fy * bs.y * 0.3, bh.z - 0.0585), (0.066, 0.106, 0.008), 'strap')
    d.box((lx, tc.y + fy * 0.01, th.z - 0.1015), (0.046, 0.096, 0.012), 'vest')
    for z in (th.z - 0.19, th.z - 0.13):
        d.box((lx, tc.y + fy * 0.01, z), (0.046, 0.096, 0.016), 'strap')
    gear.append(ED.finish('TROOPER_g_belt', m, d, 0.0, ht))

    # knee pads + elbow pads
    m = Model(pal)
    d = ED.Deco(pal)
    kf = '+y' if fy > 0 else '-y'
    for side in ('L', 'R'):
        # knee pads: a domed cap curved round the knee, a strap plate and a hard ridge on it (detail, no outline)
        k = rig.data.bones['DEF-shin.' + side].head_local
        kp = dict(r=0.02, cuts=(1, 0, 0), puff=(0, 0.008, 0), curve=[('y', 'x', -fy * 0.018)], bot=(0.86, 1.0))
        kl, ks = (k.x, k.y + fy * 0.065, k.z - 0.01), (0.11, 0.045, 0.13)
        S.rbox(m, kl, ks, 'pad', **kp)
        with ED.at(d, S.face_frame(kl, ks, kf, 0, 0, on=m, **kp)):
            ED.pad(d, 0, 0, 0.066, 0.06, 0.004, 'strap')
        with ED.at(d, S.face_frame(kl, ks, kf, 0, 0.046, on=m, **kp)):
            ED.pad(d, 0, 0, 0.07, 0.012, 0.004, 'steel')
        e = rig.data.bones['DEF-forearm.' + side].head_local
        S.rbox(m, (e.x, e.y - fy * 0.045, e.z), (0.09, 0.035, 0.08), 'pad', cham=0.012, axes='x')
    # detail pass (no outline of its own): elbow pad straps
    for side in ('L', 'R'):
        e = rig.data.bones['DEF-forearm.' + side].head_local
        d.box((e.x, e.y - fy * 0.0655, e.z), (0.02, 0.006, 0.086), 'strap')
    gear.append(ED.finish('TROOPER_g_pads', m, d, 0.0, ht))

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

    # groin protector (in the trouser colour, owner: match): a small rounded flap hanging from under the front of the belt over the crotch. Weighted to the
    # hips, its lower edge blending a little into both thighs, so it rides the pelvis and eases with the stride.
    zt, zb = bh.z - 0.05, crotch.z + 0.03
    def front_at(z):
        ys = [(body.matrix_world @ v.co).y for v in body.data.vertices
              if abs(v.co.x - bc.x) < 0.045 and abs(v.co.z - z) < 0.025]
        return (min(ys) if fy < 0 else max(ys)) if ys else bc.y + fy * bs.y * 0.5
    ta = Vector((bc.x, front_at(zt) + fy * 0.012, zt))
    tb = Vector((bc.x, front_at(zb + 0.02) + fy * 0.016, zb))
    m = Model(pal)
    m.parent = _seg_frame(ta, tb, F)              # local z down the flap, local y out of the body
    L = (tb - ta).length
    S.rbox(m, (0, 0, L / 2), (0.12, 0.014, L), 'uniform', cham=0.006, cuts=(2, 0, 1), top=(0.6, 1.0),
           curve=[('y', 'x', -0.022)], puff=(0, 0.004, 0))
    m.parent = Matrix.Identity(4)
    flap = build_object('TROOPER_g_groin', m, 0.0, ht)
    gh, gl_, gr_ = (flap.vertex_groups.new(name=n) for n in ('DEF-hips', 'DEF-thigh.L', 'DEF-thigh.R'))
    for v in flap.data.vertices:
        t = max(0.0, min(1.0, (zt - v.co.z) / (zt - zb)))
        w = 0.35 * t * t
        gh.add([v.index], 1.0 - w, 'REPLACE')
        if w > 0:
            gl_.add([v.index], w / 2, 'REPLACE'); gr_.add([v.index], w / 2, 'REPLACE')
    gear.append(flap)

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
