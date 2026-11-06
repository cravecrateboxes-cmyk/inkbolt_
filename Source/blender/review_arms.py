"""INKBOLT viewmodel review sheet: arms + guns posed by their actions, rendered like the game.

    python3 review_arms.py                              # default shot list -> renders/hands-sheet.png
    python3 review_arms.py --out /tmp/x.png --only PIP,RIVET --res 400
    python3 review_arms.py --no-gun --shots "[('PIP', 'Idle', 0.0, ('close', (0, 0, -0.05), (1, -0.2, 0.25), 0.2, 40))]"
    python3 review_arms.py --tiles ../tests/e2e/screens/viewmodel/*.png --out renders/x.png   # in-game shots -> sheet

Builds the weapons family in memory with the same code as build_assets.py (nothing is exported), hangs
every gun on the Weapon bone and its magazine on the Mag bone exactly as src/game/weapons.js does, poses
the rig with a frame of a <WEAPON>_<Action> action and renders through the game's viewmodel camera
(vmRoot at (0.19, -0.13, -0.5), yaw 0.06, scale 0.85, 58 deg vertical FOV) or through a close-up camera.
Shading copies the game's toon material: palette colour x 3 light bands from the viewmodel sun, the baked
ink shell drawn by culling back faces (Cycles on the CPU: no GPU needed). Tiles are labelled and joined
into one PNG with PIL.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ib_lib  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

V = Vector
C3 = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))       # three.js (Y up, -Z forward) -> Blender (Z up, +Y forward)
C4 = C3.to_4x4()
VM_SCALE = 0.85
ADS_DIST = {'pistol': 0.34, 'smg': 0.22, 'rifle': 0.17, 'sniper': 0.13}
SUN = (C3 @ V((0.3, 0.9, 0.5))).normalized()           # viewmodel sun (camera space)
NAMES = {'PIP': 'P-12 Warden', 'HANDCANNON': 'R-50 Ironjaw', 'TWINTAP': 'P-16 Twinfire', 'BUZZ': 'KV-9 Buzzsaw', 'WHISK': 'KV-4 Whiplash',
         'HORNET': 'KV-7 Hornet', 'RIVET': 'AR-22 Rivet', 'TRIPLET': 'AR-3 Tribolt', 'LONGTOM': 'DMR-60 Longtom', 'BRICK': 'LMG-26 Bricklayer',
         'NEEDLE': 'SR-160 Needle'}

# (weapon, action, time 0..1 of the action, camera); camera: 'game' | 'ads' | 'zoom' | ('zoom', NDC x, NDC y, size) |
# ('close', target (weapon space), view dir, distance, fov)
CLOSE_R = ('close', (0.0, 0.01, -0.04), (0.9, 0.3, 0.3), 0.20, 40)          # strong hand: knuckles, trigger finger
CLOSE_L = ('close', (-0.01, 0.0, -0.04), (-0.8, 0.5, 0.3), 0.20, 40)        # support hand cupping the strong hand
CLOSE_TOP = ('close', (0.0, 0.0, -0.04), (-0.35, -0.92, 0.24), 0.26, 40)     # from the player's eye
ZOOM = (0.46, -0.42, 0.56)      # game frame cropped to the viewmodel corner: centre (NDC x, y), size
DEFAULT_SHOTS = [
    ('PIP', 'Idle', 0.0, 'zoom'), ('PIP', 'Sprint', 0.0, 'game'), ('PIP', 'Reload', 0.53, 'zoom'), ('PIP', 'Idle', 0.0, CLOSE_R),
    ('HANDCANNON', 'Idle', 0.0, 'zoom'), ('HANDCANNON', 'Sprint', 0.5, 'game'), ('PIP', 'Idle', 0.0, CLOSE_TOP), ('PIP', 'Idle', 0.0, CLOSE_L),
    ('BUZZ', 'Idle', 0.0, 'zoom'), ('BUZZ', 'Sprint', 0.0, 'game'), ('BUZZ', 'Reload', 0.53, 'zoom'),
    ('BUZZ', 'Idle', 0.0, ('close', (0.0, 0.03, -0.02), (1.0, -0.1, 0.2), 0.26, 40)),
    ('RIVET', 'Idle', 0.0, 'zoom'), ('RIVET', 'Sprint', 0.0, 'game'), ('RIVET', 'Reload', 0.53, 'zoom'),
    ('RIVET', 'Idle', 0.0, ('close', (0.0, 0.30, 0.0), (-0.7, -0.4, 0.6), 0.20, 40)),
    ('PIP', 'Sprint', 0.0, ('close', (0.0, -0.05, -0.1), (-0.9, -0.3, -0.1), 0.6, 40)), ('PIP', 'Reload', 0.53, ('close', (0.0, 0.0, -0.08), (-0.7, -0.6, 0.2), 0.40, 40)),
    ('NEEDLE', 'Idle', 0.0, 'zoom'), ('BRICK', 'Sprint', 0.5, 'game'),
]


def toon_material(pal):
    """Emission toon: palette colour x the game's gradient bands (dot(N, sun) < -0.5 / < 0 / else), backfaces cut."""
    m = bpy.data.materials.new('REVIEW_toon')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N = nt.nodes.new
    tex = N('ShaderNodeTexImage')
    tex.image = pal.image
    tex.interpolation = 'Closest'
    geo = N('ShaderNodeNewGeometry')
    dot = N('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = SUN
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    fac = N('ShaderNodeMath')
    fac.operation = 'MULTIPLY_ADD'
    fac.inputs[1].default_value = 0.5
    fac.inputs[2].default_value = 0.5
    nt.links.new(dot.outputs['Value'], fac.inputs[0])
    ramp = N('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    tint = [0x5E / 0x8C, 0x4F / 0x8C, 1.0]
    b0 = [0.72 * (0.6 + 0.4 * c) for c in tint]
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*[c ** 2.2 for c in b0], 1)
    els[1].position, els[1].color = 0.25, (0.9 ** 2.2, 0.9 ** 2.2, 0.9 ** 2.2, 1)
    e = els.new(0.5)
    e.color = (1, 1, 1, 1)
    nt.links.new(fac.outputs['Value'], ramp.inputs['Fac'])
    mul = N('ShaderNodeVectorMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0])
    nt.links.new(ramp.outputs['Color'], mul.inputs[1])
    em = N('ShaderNodeEmission')
    nt.links.new(mul.outputs['Vector'], em.inputs['Color'])
    tr = N('ShaderNodeBsdfTransparent')
    mix = N('ShaderNodeMixShader')
    nt.links.new(geo.outputs['Backfacing'], mix.inputs[0])
    nt.links.new(em.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    out = N('ShaderNodeOutputMaterial')
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def setup_render(res, bg=(0.90, 0.93, 0.97)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 12
    sc.cycles.use_denoising = False
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.max_bounces = 0
    sc.render.resolution_x = res
    sc.render.resolution_y = round(res * 9 / 16)
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('REVIEW')
    w.use_nodes = True
    bgn = w.node_tree.nodes.get('Background')
    bgn.inputs[0].default_value = (*[c ** 2.2 for c in bg], 1)
    sc.world = w
    cam = bpy.data.objects.new('REVIEW_cam', bpy.data.cameras.new('REVIEW_cam'))
    sc.collection.objects.link(cam)
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.clip_start = 0.005
    sc.camera = cam
    return cam


def vm_matrix(pos, rot):
    """weapons.js vmRoot (three.js camera space) as a Blender matrix for the rig object."""
    M = Matrix.Translation(pos) @ Euler(rot, 'XYZ').to_matrix().to_4x4() @ Matrix.Diagonal((VM_SCALE,) * 3 + (1,))
    return C4 @ M @ C4.inverted()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'renders', 'hands-sheet.png'))
    ap.add_argument('--res', type=int, default=480)
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--only', default='')
    ap.add_argument('--no-gun', action='store_true', help='hide the guns (look at the hands alone)')
    ap.add_argument('--shots', default='', help="python list of (weapon, action, t, camera) replacing the default list")
    ap.add_argument('--title', default='INKBOLT arms (Blender, game camera + close-ups)')
    ap.add_argument('--tiles', nargs='+', help='no render: join these PNGs (e.g. tests/e2e/viewmodel-shots.js output) into a sheet')
    ap.add_argument('--tile-width', type=int, default=540)
    a = ap.parse_args(argv)
    if a.tiles:
        from PIL import Image
        tiles = []
        for f in a.tiles:
            im = Image.open(f).convert('RGB')
            tiles.append((os.path.splitext(os.path.basename(f))[0], im.resize((a.tile_width, round(im.height * a.tile_width / im.width)), Image.LANCZOS)))
        sheet(tiles, a.out, a.cols, a.title)
        return
    import fam_weapons as fw
    ib_lib.fresh_scene()
    pal, rig, arms = fw.build_scene()
    mat = toon_material(pal)
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)
            o.hide_render = True
    arms.hide_render = False
    cam = setup_render(a.res)
    shots = DEFAULT_SHOTS if not a.shots else eval(a.shots, {'CLOSE_L': CLOSE_L, 'CLOSE_R': CLOSE_R, 'CLOSE_TOP': CLOSE_TOP})
    if a.only:
        keep = a.only.split(',')
        shots = [s for s in shots if s[0] in keep]
    tiles = []
    tmp = os.path.abspath(a.out) + '.tile.png'
    pb, bones = rig.pose.bones, rig.data.bones
    for i, (wid, act, t, camspec) in enumerate(shots):
        action = bpy.data.actions[wid + '_' + act]
        rig.animation_data.action = action
        if hasattr(rig.animation_data, 'action_slot') and action.slots:
            rig.animation_data.action_slot = action.slots[0]
        f0, f1 = action.frame_range
        f = f0 + (f1 - f0) * t
        sc = bpy.context.scene
        sc.frame_set(int(f), subframe=f - int(f))
        info = fw.WEAPONS[wid]
        if camspec == 'ads':
            sp = V(info.get('scope', info['sight']))
            rig.matrix_world = vm_matrix((-sp.x * VM_SCALE, -sp.z * VM_SCALE, -ADS_DIST[info['cls']] + sp.y * VM_SCALE), (0, 0, 0))
        else:
            rig.matrix_world = vm_matrix((0.19, -0.13, -0.5), (0, 0.06, 0))
        bpy.context.view_layer.update()
        Wp = rig.matrix_world @ pb['Weapon'].matrix @ bones['Weapon'].matrix_local.inverted()
        Mp = rig.matrix_world @ pb['Mag'].matrix @ bones['Mag'].matrix_local.inverted() @ Matrix.Translation(bones['Mag'].head_local)
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith('WPN_'):
                o.hide_render = a.no_gun or o.name not in ('WPN_' + wid, 'WPN_%s_Mag' % wid)
        g, m = bpy.data.objects['WPN_' + wid], bpy.data.objects['WPN_%s_Mag' % wid]
        g.parent = m.parent = None
        g.matrix_world = Wp
        m.matrix_world = Mp
        if isinstance(camspec, tuple) and camspec[0] == 'close':
            _, tgt, d, dist, fov = camspec
            tw = Wp @ V(tgt)
            dw = V(d).normalized()
            cam.location = tw + dw * dist
            cam.rotation_euler = (tw - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.angle_y = math.radians(fov)
            label = '%s - %s close-up' % (NAMES.get(wid, wid), act.lower())
        else:
            # 'game' = the full game frame; 'zoom' = the same camera cropped to the viewmodel's corner
            cx, cy, k = (0.0, 0.0, 1.0) if camspec in ('game', 'ads') else camspec[1:] if isinstance(camspec, tuple) else ZOOM
            asp = sc.render.resolution_x / sc.render.resolution_y
            cam.location = (0, 0, 0)
            cam.rotation_euler = (math.radians(90), 0, 0)
            cam.data.angle_y = 2 * math.atan(math.tan(math.radians(29)) * k)
            cam.data.shift_x, cam.data.shift_y = cx / (2 * k), cy / (2 * k * asp)
            label = '%s - %s%s' % (NAMES.get(wid, wid), act.lower(), ' (ADS)' if camspec == 'ads' else '' if camspec == 'game' else ' (game view, zoomed)')
        if isinstance(camspec, tuple) and camspec[0] == 'close':
            cam.data.shift_x = cam.data.shift_y = 0.0
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        from PIL import Image
        tiles.append((label, Image.open(tmp).convert('RGB')))
        print('rendered %d/%d %s' % (i + 1, len(shots), label))
    os.remove(tmp)
    sheet(tiles, a.out, a.cols, a.title)


def sheet(tiles, out, cols, title):
    from PIL import Image, ImageDraw, ImageFont
    w, h = tiles[0][1].size
    pad, lab, top = 8, 22, 44
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new('RGB', (pad + cols * (w + pad), top + rows * (h + lab + pad)), (0x1F, 0x1D, 0x29))
    d = ImageDraw.Draw(S)
    fb = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    ft, fl = ImageFont.truetype(fb, 22), ImageFont.truetype(fb, 14)
    d.text((pad, 10), title, fill=(0xFF, 0xD3, 0x6E), font=ft)
    for i, (label, im) in enumerate(tiles):
        x, y = pad + (i % cols) * (w + pad), top + (i // cols) * (h + lab + pad)
        d.text((x + 2, y + 3), label, fill=(0xE8, 0xE6, 0xF0), font=fl)
        S.paste(im, (x, y + lab))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    S.save(out)
    print('wrote', out, S.size)


if __name__ == '__main__':
    main(sys.argv[1:])
