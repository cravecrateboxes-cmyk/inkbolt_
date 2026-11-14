"""INKBOLT enemy review sheet: every robot and trooper from the built GLBs, assembled on its sockets and rendered
like the game (palette colour x the toon light bands, the baked ink shell drawn by culling back faces).

    python3 review_bots.py --bots ../assets/fps-bots.glb --troopers ../assets/fps-troopers.glb --out /tmp/x.png
    python3 review_bots.py ... --before <old-bots.glb> <old-troopers.glb>     # before / after pairs, one row each
    python3 review_bots.py ... --only crawler,hawk --res 360

Reads the GLBs (nothing is rebuilt): parts sit on their sockets as src/game/ai.js and troops.js pose them at rest,
the troopers in a frame of their aiming pose. Each enemy gets a front three-quarter and a back three-quarter view;
the tile label carries the enemy's triangle count (parts x instances, as IB.TRI_BUDGET.robots counts them).
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from review_arms import setup_render, sheet  # noqa: E402

SUN = Vector((0.35, -0.55, 0.75)).normalized()      # world-space key light for the toon bands

# enemy -> list of (part, socket path or fixed point); a socket path is summed (parent socket first)
ROBOTS = {
    'crawler': [('BOT_CRAWLER_Body', None), *[('BOT_CRAWLER_Leg', ['BOT_CRAWLER_HIP%d' % i]) for i in range(4)],
                ('BOT_CRAWLER_Light', (0.12, 0.08, 1.08))],
    'crawler2': [('BOT_CRAWLER_Body2', None), *[('BOT_CRAWLER_Leg2', ['BOT_CRAWLER_HIP%d' % i]) for i in range(4)],
                 ('BOT_CRAWLER_Light', (0.12, 0.08, 1.08)), ('BOT_CRAWLER_Specks', None)],
    'gunner': [('BOT_GUNNER_Body', None), ('BOT_GUNNER_Lid', ['BOT_GUNNER_HINGE']), ('BOT_GUNNER_Gun', ['BOT_GUNNER_GUNPIVOT']),
               ('BOT_GUNNER_Wheel', ['BOT_GUNNER_WHEEL0']), ('BOT_GUNNER_Wheel', ['BOT_GUNNER_WHEEL1']),
               ('BOT_GUNNER_Light', ['BOT_GUNNER_LIGHT'])],
    'bomber': [('BOT_BOMBER_Body', None), ('BOT_BOMBER_Roller', ['BOT_BOMBER_AXLE']), ('BOT_BOMBER_Cap', ['BOT_BOMBER_CAP']),
               ('BOT_BOMBER_Light', ['BOT_BOMBER_CAP', 'BOT_BOMBER_WICK'])],
    'drone': [('BOT_DRONE_Body', None), ('BOT_DRONE_Gun', ['BOT_DRONE_GUNPIVOT']), ('BOT_DRONE_Lid', ['BOT_DRONE_LID']),
              *[('BOT_DRONE_Rotor', ['BOT_DRONE_LID', 'BOT_DRONE_ROTOR%d' % i]) for i in range(4)],
              ('BOT_DRONE_Light', ['BOT_DRONE_LID', 'BOT_DRONE_LIGHT'])],
    'blader': [('BOT_BLADER_Body', None), ('BOT_BLADER_Hub', ['BOT_BLADER_HUB']), ('BOT_BLADER_Katana', ['BOT_BLADER_HUB', 'BOT_BLADER_GRIP']),
               ('BOT_BLADER_Light', ['BOT_BLADER_LIGHT'])],
    'bladerAxe': [('BOT_BLADER_Body', None), ('BOT_BLADER_Hub', ['BOT_BLADER_HUB']), ('BOT_BLADER_Axe', ['BOT_BLADER_HUB', 'BOT_BLADER_GRIP']),
                  ('BOT_BLADER_Light', ['BOT_BLADER_LIGHT'])],
    'hawk': [('BOT_HAWK_Body', None), *[(p, ['BOT_HAWK_FAN%d' % i]) for i in range(2) for p in ('BOT_HAWK_Fan', 'BOT_HAWK_Rotor')],
             ('BOT_HAWK_Gun', ['BOT_HAWK_GUNPIVOT']), ('BOT_HAWK_Light', ['BOT_HAWK_LIGHT'])],
    'soldierBot': [('BOT_SOLDIER_Hips', None), ('BOT_SOLDIER_Thigh', ['BOT_SOLDIER_HIP0']), ('BOT_SOLDIER_Thigh', ['BOT_SOLDIER_HIP1']),
                   ('BOT_SOLDIER_Shin', ['BOT_SOLDIER_HIP0', (0, 0, -0.43)]), ('BOT_SOLDIER_Shin', ['BOT_SOLDIER_HIP1', (0, 0, -0.43)]),
                   ('BOT_SOLDIER_TorsoA', ['BOT_SOLDIER_WAIST']), ('BOT_SOLDIER_HelmA', ['BOT_SOLDIER_WAIST', 'BOT_SOLDIER_NECK']),
                   ('BOT_SOLDIER_Visor', ['BOT_SOLDIER_WAIST', 'BOT_SOLDIER_NECK', 'BOT_SOLDIER_VISOR']),
                   ('BOT_SOLDIER_ArmR', ['BOT_SOLDIER_WAIST', 'BOT_SOLDIER_SHOULDER0']), ('BOT_SOLDIER_ArmL', ['BOT_SOLDIER_WAIST', 'BOT_SOLDIER_SHOULDER1'])],
    'soldierParts': [('BOT_SOLDIER_HelmB', (-0.45, 0, 0.2)), ('BOT_SOLDIER_HelmC', (0.0, 0, 0.2)), ('BOT_SOLDIER_Nade', (0.42, 0, 0.3)),
                     ('BOT_SOLDIER_TorsoB', (0.0, 0.0, -0.75))],
}
TROOPERS = {'soldier': ['TROOPER'], 'grenadier': ['TROOPER', 'TROOPER_GL'], 'mech': ['TROOPER_MECH']}
ORDER = ['crawler', 'crawler2', 'gunner', 'bomber', 'drone', 'blader', 'bladerAxe', 'hawk', 'soldierBot', 'soldierParts',
         'soldier', 'grenadier', 'mech']


def toon(img):
    m = bpy.data.materials.new('REVIEW_toon')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N = nt.nodes.new
    tex = N('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Closest'
    geo = N('ShaderNodeNewGeometry')
    dot = N('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = SUN
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    fac = N('ShaderNodeMath'); fac.operation = 'MULTIPLY_ADD'; fac.inputs[1].default_value = 0.5; fac.inputs[2].default_value = 0.5
    nt.links.new(dot.outputs['Value'], fac.inputs[0])
    ramp = N('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.42, 0.40, 0.55, 1)
    els[1].position, els[1].color = 0.3, (0.78, 0.78, 0.80, 1)
    e = els.new(0.55); e.color = (1, 1, 1, 1)
    nt.links.new(fac.outputs['Value'], ramp.inputs['Fac'])
    mul = N('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(ramp.outputs['Color'], mul.inputs[1])
    em = N('ShaderNodeEmission'); nt.links.new(mul.outputs['Vector'], em.inputs['Color'])
    tr = N('ShaderNodeBsdfTransparent')
    mix = N('ShaderNodeMixShader')
    nt.links.new(geo.outputs['Backfacing'], mix.inputs[0]); nt.links.new(em.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
    out = N('ShaderNodeOutputMaterial'); nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def load(path):
    """Import a GLB into its own collection; returns {name: object} and the palette image."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = {o.name: o for o in bpy.data.objects if o not in before}
    img = next((i for i in bpy.data.images if i.name.startswith('PAL_') and i.users), None)
    for o in objs.values():
        o.hide_render = True
    return objs, img


def tris_of(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def place(objs, enemy, mat):
    """Linked duplicates of the enemy's parts at their sockets; returns (objects, triangle count)."""
    out, tris = [], 0
    for part, at in ROBOTS[enemy]:
        src = objs[part]
        if at is None:
            p = Vector((0, 0, 0))
        elif isinstance(at, tuple):
            p = Vector(at)
        else:
            p = Vector((0, 0, 0))
            for s in at:
                p += Vector(s) if isinstance(s, tuple) else objs[s].matrix_world.translation
        o = bpy.data.objects.new('R_' + part, src.data)
        o.matrix_world = Matrix.Translation(p)
        o.data.materials.clear(); o.data.materials.append(mat)
        bpy.context.scene.collection.objects.link(o)
        out.append(o)
        tris += tris_of(src)
    return out, tris


def show_troopers(objs, enemy, mat):
    rig = objs['TROOPER_Rig']
    act = bpy.data.actions.get('Pistol_Aim_Neutral')
    rig.animation_data_create()
    rig.animation_data.action = act
    if hasattr(rig.animation_data, 'action_slot') and act.slots:
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(act.frame_range[0]) + 2)
    out, tris = [], 0
    for n in TROOPERS[enemy]:
        o = objs[n]
        o.hide_render = False
        for s in o.material_slots:
            s.material = mat
        out.append(o)
        tris += tris_of(o)
    return out, tris


def hide_carbine(body, hide):
    """The Grenadier's material clips the carbine (vertex colour alpha 0): mimic it with a mask modifier."""
    me = body.data
    if 'carbine' not in body.vertex_groups:
        ca = me.color_attributes.get('Col') or (me.color_attributes[0] if me.color_attributes else None)
        idx = set()
        if ca is not None:
            if ca.domain == 'POINT':
                idx = {i for i, c in enumerate(ca.data) if c.color[3] < 0.5}
            else:
                for li, c in enumerate(ca.data):
                    if c.color[3] < 0.5:
                        idx.add(me.loops[li].vertex_index)
        vg = body.vertex_groups.new(name='carbine')
        vg.add(list(set(range(len(me.vertices))) - idx), 1.0, 'REPLACE')
        mod = body.modifiers.new('mask', 'MASK'); mod.vertex_group = 'carbine'
        body['ncarbine'] = len(idx)
    body.modifiers['mask'].show_render = hide


def frame_cam(cam, objs, yaw, pitch=18.0, fov=30.0):
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            c = o.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], c[i]); hi[i] = max(hi[i], c[i])
        ev.to_mesh_clear()
    c = (lo + hi) / 2
    r = (hi - lo).length / 2
    cam.data.angle = math.radians(fov)
    d = r / math.sin(math.radians(fov) / 2) * 0.92
    a, p = math.radians(yaw), math.radians(pitch)
    dirv = Vector((math.sin(a) * math.cos(p), -math.cos(a) * math.cos(p), math.sin(p)))
    cam.location = c + dirv * d
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-dirv).to_track_quat('-Z', 'Y')


def render_set(bots, troopers, enemies, res, tag, tmpdir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cam = setup_render(res, bg=(0.86, 0.88, 0.92))
    bpy.context.scene.render.resolution_y = res
    ob, img = load(bots)
    mb = toon(img)
    imgs = set(bpy.data.images)
    ot, _ = load(troopers)
    timg = next(i for i in bpy.data.images if i not in imgs and i.name.startswith('PAL_')) if any(
        i not in imgs and i.name.startswith('PAL_') for i in bpy.data.images) else img
    mt = toon(timg)
    tiles = []
    for en in enemies:
        if en in ROBOTS:
            shown, tris = place(ob, en, mb)
        else:
            if en in ('soldier', 'grenadier'):
                hide_carbine(ot['TROOPER'], en == 'grenadier')
            shown, tris = show_troopers(ot, en, mt)
        for yaw, view in ((-35, 'front'), (150, 'back')):
            frame_cam(cam, shown, yaw)
            f = os.path.join(tmpdir, '%s-%s-%s.png' % (tag, en, view))
            bpy.context.scene.render.filepath = f
            bpy.ops.render.render(write_still=True)
            tiles.append(((en, view, tris), f))
        for o in shown:
            if o.name.startswith('R_'):
                bpy.data.objects.remove(o)
            else:
                o.hide_render = True
    return tiles


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--bots', default=os.path.join(HERE, '..', 'assets', 'fps-bots.glb'))
    ap.add_argument('--troopers', default=os.path.join(HERE, '..', 'assets', 'fps-troopers.glb'))
    ap.add_argument('--before', nargs=2, default=None, metavar=('BOTS', 'TROOPERS'))
    ap.add_argument('--only', default=None)
    ap.add_argument('--res', type=int, default=320)
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'dist', 'look', 'enemies', 'enemies-sheet.png'))
    ap.add_argument('--split', action='store_true', help='one sheet per enemy next to --out')
    a = ap.parse_args(argv)
    from PIL import Image
    enemies = [e for e in ORDER if not a.only or e in a.only.split(',')]
    tmp = os.path.join(os.path.dirname(os.path.abspath(a.out)), '_tiles')
    os.makedirs(tmp, exist_ok=True)
    new = render_set(a.bots, a.troopers, enemies, a.res, 'after', tmp)
    old = render_set(a.before[0], a.before[1], enemies, a.res, 'before', tmp) if a.before else None
    groups = {}
    for i, ((en, view, tris), f) in enumerate(new):
        row = groups.setdefault(en, [])
        if old:
            (_, _, t0), f0 = old[i]
            row.append(('%s %s  before %d tris' % (en, view, t0), Image.open(f0).convert('RGB')))
        row.append(('%s %s  after %d tris' % (en, view, tris), Image.open(f).convert('RGB')))
    cols = 4 if old else 2
    title = 'INKBOLT enemies: before / after detail pass' if old else 'INKBOLT enemies'
    if a.split:
        base = os.path.splitext(a.out)[0]
        for en, row in groups.items():
            sheet(row, '%s-%s.png' % (base, en), cols, '%s: %s' % (title, en))
    else:
        sheet([t for row in groups.values() for t in row], a.out, cols, title)


if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    main(argv)
