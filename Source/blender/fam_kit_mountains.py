"""INKBOLT asset family: kit-mountains (campaign level 1, "Pine Ridge").

Alpine valley kit: slate-blue cliff ridges with snow ledges, snowy pines and spruce stands, log cabin, A-frame
chalet, fire-lookout tower, rope bridge between two rock towers, ski lift, stone walls, log piles, floor patches
(snow drifts, meadow, frozen pond, frozen creek) and a backdrop of big snow-capped peaks and pine forest.

Conventions (see src/game/zones.js): 1 cell = 1 m; a piece's origin is the centre of its cell / footprint at floor
level; Blender -Y = game +Z (south, toward the zone entry). Cliff wall modules are pre-rotated per facing
(Cliff_<S|N|E|W>_<a><b>): the theme's wall chooser picks the one whose rock face looks at the open side, and the
ridge height levels a/b at the two module edges are shared with the neighbours, so the skyline is continuous.
"""
import math
import random

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import join_into
import mtn_pieces as MP
import mtn_shapes as MS

FAM = 'kit-mountains'
PFX = 'KIT_MOUNTAINS_'
ib_lib.GLB[FAM] = 'fps-kit-mountains.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
# cool slate rock, blue-shadowed snow, deep pines, warm timber, red roofs; lifted a little for the pastel comic look
ib_lib.PALETTES[FAM] = BASE + [
    ('rock', '#9DACC2'), ('rock2', '#8193AD'), ('rock3', '#BAC6D6'), ('rockd', '#6C7D98'),
    ('snow', '#F8FBFF'), ('snow2', '#DCE7F4'), ('ice', '#A6D5EE'), ('ice2', '#D6EFFB'),
    ('pine', '#3F8F6A'), ('pine2', '#2F7A5A'), ('pine3', '#5BA97E'), ('trunk', '#8A5C3E'),
    ('log', '#C98B57'), ('log2', '#AD7146'), ('logend', '#EAC690'), ('roof', '#D2603F'),
    ('roof2', '#B44F34'), ('tangerine', '#FF8A3D'), ('glow', '#FFD98A'), ('door', '#7A4A33'),
    ('stone', '#BDB7AE'), ('stone2', '#A39C92'), ('meadow', '#B4D59A'), ('meadow2', '#8FC07A'),
    ('lift', '#5B8FD0'), ('steel', '#8995A6'), ('rope', '#D9C59A'), ('plank', '#BC8656'),
    ('canvas', '#E9DDC2'), ('flame', '#FF6B3D'), ('far', '#A9BCD4'), ('farsnow', '#EEF4FB'),
]

# ridge height levels of the cliff modules (m); the theme's wall chooser uses the same indices
LEVELS = [6.2, 7.4, 8.6, 9.8]
PAIRS = [(a, b) for a in range(4) for b in range(4) if abs(a - b) <= 1]
TRIS = {}


# ================================================================ geometry helpers
def _verts(m, pts):
    return [m.bm.verts.new(m.parent @ Vector(p)) for p in pts]


def tag(m, faces, color=None):
    """Mark faces as one shape (z-fight guard) and optionally colour them."""
    m.nshape += 1
    ci = m.pal.index(color) if color else None
    for f in faces:
        f[m.shape] = m.nshape
        if ci is not None:
            f.material_index = ci
    return faces


def paint(m, faces, fn):
    for f in faces:
        f.normal_update()
        f.material_index = m.pal.index(fn(f))


def _tri(m, faces):
    return bmesh.ops.triangulate(m.bm, faces=faces, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']


def hull(m, pts, color):
    """Convex hull of points -> one shape; color is a palette name or fn(face) -> name."""
    vs = _verts(m, pts)
    res = bmesh.ops.convex_hull(m.bm, input=vs)
    junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(m.bm, geom=junk, context='VERTS')
    fs = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    tag(m, fs)
    paint(m, fs, color if callable(color) else (lambda f: color))
    return fs


def prism(m, prof, a0, a1, color, axis='x', prof1=None, colors=None):
    """Closed prism: (u, z) profile polygon extruded along `axis` from a0 to a1 (profile may change: prof1)."""
    prof1 = prof1 or prof

    def P(a, u, z):
        return (a, u, z) if axis == 'x' else (u, a, z)
    va = _verts(m, [P(a0, u, z) for u, z in prof])
    vb = _verts(m, [P(a1, u, z) for u, z in prof1])
    n = len(prof)
    fs = []
    for i in range(n):
        j = (i + 1) % n
        f = m.bm.faces.new((va[i], va[j], vb[j], vb[i]))
        if colors:
            f.material_index = m.pal.index(colors[i])
        fs.append(f)
    caps = [m.bm.faces.new(va[::-1]), m.bm.faces.new(vb)]
    for c in caps:
        c.material_index = m.pal.index(color)
    if not colors:
        for f in fs:
            f.material_index = m.pal.index(color)
    fs += caps
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    fs = _tri(m, fs)
    tag(m, fs)
    return fs


def loft_open(m, profA, profB, colors, baffle_color, axis='x', a0=-0.5, a1=0.5, inset=0.05):
    """Open-ended lofted rock surface (front-base -> back-base polyline profiles at a0 / a1) plus an inset baffle
    closing each end. Neighbouring modules share their edge profile, so the surface runs on seamlessly and the
    open ends keep the baked outline from drawing an ink seam at every module joint."""
    def P(a, u, z):
        return (a, u, z) if axis == 'x' else (u, a, z)
    n = len(profA)
    va = _verts(m, [P(a0, u, z) for u, z in profA])
    vb = _verts(m, [P(a1, u, z) for u, z in profB])
    side = []
    for i in range(n - 1):
        f = m.bm.faces.new((va[i], va[i + 1], vb[i + 1], vb[i]))
        f.material_index = m.pal.index(colors[i])
        side.append(f)
    bottom = m.bm.faces.new((va[n - 1], va[0], vb[0], vb[n - 1]))
    caps = [m.bm.faces.new(va[::-1]), m.bm.faces.new(vb)]
    bmesh.ops.recalc_face_normals(m.bm, faces=side + [bottom] + caps)
    bmesh.ops.delete(m.bm, geom=[bottom] + caps, context='FACES_ONLY')
    tag(m, _tri(m, side))
    for a, prof, sgn in ((a0, profA, -1), (a1, profB, 1)):
        cu = sum(u for u, z in prof) / n
        cz = sum(z for u, z in prof) / n
        pts = []
        for u, z in prof:
            du, dz = cu - u, cz - z
            L = math.hypot(du, dz) or 1.0
            pts.append(P(a, u + du / L * inset, (z + dz / L * inset) if z > 1e-4 else 0.0))
        bv = _verts(m, pts)
        bf = m.bm.faces.new(bv)
        bf.normal_update()
        out = Vector((1, 0, 0) if axis == 'x' else (0, 1, 0)) * sgn
        if bf.normal.dot(out) < 0:
            bmesh.ops.reverse_faces(m.bm, faces=[bf])
        bf.material_index = m.pal.index(baffle_color)
        tag(m, _tri(m, [bf]))


def star(m, c, r, h, color, pts=7, inner=0.68, droop=0.1, phase=5.0, fan=True, under=0.14, under_color=None):
    """Star-section cone (a pine tier): pts branch tips at radius r drooping a little, apex h above c."""
    cx, cy, cz = c
    ring = []
    for i in range(pts * 2):
        a = math.radians(phase) + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        ring.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz - (droop if i % 2 == 0 else 0.0)))
    vs = _verts(m, ring + [(cx, cy, cz + h), (cx, cy, cz + h * under)])
    N = len(ring)
    A, B = vs[N], vs[N + 1]
    side, bot = [], []
    for i in range(N):
        j = (i + 1) % N
        side.append(m.bm.faces.new((vs[i], vs[j], A)))
        if fan:
            bot.append(m.bm.faces.new((vs[j], vs[i], B)))
    tag(m, side + bot, color)
    if fan:
        for f in bot:
            f.material_index = m.pal.index(under_color or color)
    return side + bot


def rock_pts(rnd, c, rx, ry, h, z0=0.0, n=7, top=3, flat=True, waist=(0.3, 0.55)):
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.82, 1.0)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0 if flat else z0 + h * rnd.uniform(0, 0.12)))
    for i in range(n):
        a = (i + 0.5 + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.86, 1.06)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0 + h * rnd.uniform(*waist)))
    for i in range(top):
        a = rnd.uniform(0, 2 * math.pi)
        k = rnd.uniform(0.1, 0.62)
        pts.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k, z0 + h * rnd.uniform(0.78, 1.0)))
    return pts


def clamp_pts(pts, lim, ylim=None):
    ylim = lim if ylim is None else ylim
    return [(max(-lim, min(lim, x)), max(-ylim, min(ylim, y)), z) for x, y, z in pts]


def top_z(faces, x, y):
    """Height of the highest face above (x, y) (ray cast down), or None."""
    from mathutils.geometry import intersect_ray_tri
    best = None
    o, d = Vector((x, y, 200.0)), Vector((0, 0, -1))
    for f in faces:
        if not f.is_valid or len(f.verts) != 3:
            continue
        p = intersect_ray_tri(f.verts[0].co, f.verts[1].co, f.verts[2].co, d, o, True)
        if p is not None and (best is None or p.z > best):
            best = p.z
    return best


def rock_col(z0, h, snow=0.62, base='rock2', mid='rock', light='rock3', snowc='snow'):
    def fn(f):
        n, c = f.normal, f.calc_center_median()
        if n.z > snow:
            return snowc
        if n.z > 0.3:
            return light
        if c.z < z0 + h * 0.24:
            return base
        return mid
    return fn


def spruce(m, x, y, h, r, rnd, tiers=3, base=0.45, snow=True, trunk=0.13, pts=7):
    """Snowy spruce: tapered trunk and whorls of drooping, snow-loaded fronds (mtn_shapes.frond_tree)."""
    MS.frond_tree(m, hull, top_z, rnd, x, y, h, r, base + 0.25, tiers, trunk_r=trunk, snow=snow, fronds=pts if h > 4.0 else pts - 1,
                  lean=(rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12)), flare=h > 4.0)


def new(pal):
    return Model(pal)


def finish(name, m, ao, bevel=0.0, hull_t=0.02, cols=None):
    full = PFX + name
    flat = getattr(m, 'flat', None)
    if flat:
        # detail shapes (ink=False) go into a second, hull-less mesh joined in after the z-fight check on the whole
        check_zfight(full, m.bm, m.shape)
        fb = m.bm.copy()
        bmesh.ops.delete(m.bm, geom=[f for f in m.bm.faces if f[m.shape] in flat], context='FACES')
        fm = Model(m.pal)
        fm.bm.free()
        fm.bm = fb
        fm.bw = fb.edges.layers.float['bevel_weight_edge']
        fm.shape = fb.faces.layers.int['shape_id']
        bmesh.ops.delete(fb, geom=[f for f in fb.faces if f[fm.shape] not in flat], context='FACES')
        obj = build_object(full, m, bevel, hull_t, ao=ao)
        o2 = build_object(full + '_flat', fm, 0, 0.0)
        strip_hull(o2)
        join_into(obj, o2)
    else:
        obj = build_object(full, m, bevel, hull_t, ao=ao)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, (c, hlf) in enumerate(cols or []):
        e = bpy.data.objects.new('%s_COL%d' % (full, i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def rotate_all(m, deg):
    if deg:
        bmesh.ops.rotate(m.bm, verts=list(m.bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(deg), 3, 'Z'))


def catenary(x, half, z_end, sag):
    return z_end - sag * (1 - (x / half) ** 2)


# ================================================================ cliff wall modules ('#')
def cliff_profile(lv):
    """Front-base -> back-base profile (y, z) for one module edge at ridge level lv. Ledge rises are absolute so
    the snow ledges stay flat; ledge heights vary per level so ledges tilt where the ridge climbs. The back stops
    5 cm short of the next cell line so it never shares a plane with a neighbouring module's end."""
    h = LEVELS[lv]
    f1, f2, f3 = ((0.20, 0.47, 0.71), (0.17, 0.43, 0.68), (0.22, 0.50, 0.74), (0.15, 0.41, 0.66))[lv]
    return [(-0.50, 0.0), (-0.50, f1 * h), (-0.33, f1 * h + 0.06), (-0.25, f2 * h), (-0.04, f2 * h + 0.07),
            (0.06, f3 * h), (0.26, f3 * h + 0.06), (0.40, 0.90 * h), (0.56, h - 0.04), (0.92, h), (1.36, 0.72 * h), (1.45, 0.0)]


CLIFF_COLORS = ['rock2', 'snow', 'rock', 'snow', 'rock3', 'snow', 'rock', 'rock', 'snow', 'snow2', 'rock']


def cliff_module(pal, a, b, seed, rib=False):
    """South-facing module with the west edge at level a and the east edge at level b; 'b' variants carry a buttress rib."""
    m = new(pal)
    loft_open(m, cliff_profile(a), cliff_profile(b), CLIFF_COLORS, 'rock2')
    rnd = random.Random(seed)
    sx = rnd.uniform(-0.15, 0.15)
    hull(m, clamp_pts(rock_pts(rnd, (sx, -0.5, 0), 0.26, 0.17, rnd.uniform(0.3, 0.45), n=5, top=1), 0.46, 2.0), rock_col(0, 0.45))
    if rib:
        h = LEVELS[a]
        cx = rnd.uniform(-0.12, 0.12)
        j = lambda: rnd.uniform(-0.03, 0.03)
        pts = [(cx - 0.17 + j(), -0.64 + j(), 0), (cx + 0.16 + j(), -0.6 + j(), 0), (cx - 0.13, -0.28, 0), (cx + 0.14, -0.3, 0),
               (cx - 0.12 + j(), -0.52 + j(), 0.3 * h), (cx + 0.12 + j(), -0.49 + j(), 0.33 * h),
               (cx - 0.08 + j(), -0.3 + j(), 0.58 * h), (cx + 0.07 + j(), -0.26 + j(), 0.6 * h), (cx + j(), -0.16, 0.67 * h)]
        hull(m, clamp_pts(pts, 0.45, 2.0), rock_col(0, h, base='rock', mid='rock3', light='rock3'))
    # jutting slabs on the three rock bands (map asset upgrade): break the long flat terraces into blocks of varied
    # depth; each stays inside the module (|x| <= 0.42) and at most 12 cm in front of the cell line
    cr = random.Random(seed + 3)
    h = LEVELS[min(a, b)]
    f1, f2, f3 = ((0.20, 0.47, 0.71), (0.17, 0.43, 0.68), (0.22, 0.50, 0.74), (0.15, 0.41, 0.66))[min(a, b)]
    prof = cliff_profile(min(a, b))[:9]           # the rock face, foot to crest

    def face_y(z):
        for (y0, za), (y1, zb) in zip(prof[:-1], prof[1:]):
            if za <= z <= zb and zb > za:
                return y0 + (y1 - y0) * (z - za) / (zb - za)
        return prof[-1][0]
    for j in range(cr.choice((1, 2, 2))):
        H = cr.uniform(1.3, 2.6)
        z0 = cr.uniform(0.25, f3 * h - H * 0.6)
        z1 = min(z0 + H, h * 0.86)
        cx = cr.uniform(-0.2, 0.2) if j == 0 else -cx * 0.6 + cr.uniform(-0.1, 0.1)
        w0, w1 = cr.uniform(0.22, 0.36), cr.uniform(0.12, 0.26)
        t = cr.uniform(-0.12, 0.12)               # the buttress leans sideways a little
        yf0, yf1 = max(face_y(z0) - cr.uniform(0.07, 0.12), -0.62), face_y(z1) - cr.uniform(0.03, 0.07)
        zm = (z0 + z1) / 2
        yfm = min(face_y(zm), (yf0 + yf1) / 2) - cr.uniform(0.04, 0.1)
        P = [(cx - w0, face_y(z0) + 0.2, z0), (cx + w0, face_y(z0) + 0.2, z0), (cx - w0 * 0.8, yf0, z0), (cx + w0 * 0.9, yf0 + 0.03, z0 + 0.05),
             (cx + t / 2 - (w0 + w1) / 2, max(yfm, -0.6), zm + cr.uniform(-0.2, 0.2)), (cx + t / 2 + (w0 + w1) / 2 * 0.8, max(yfm + 0.03, -0.6), zm),
             (cx + t - w1, yf1, z1 - 0.1), (cx + t + w1 * 0.7, yf1 + 0.02, z1), (cx + t, face_y(z1) + 0.2, z1 + 0.1)]
        hull(m, clamp_pts(P, 0.42, 2.0), rock_col(0, h, base='rock2', mid='rock', light='rock3'))
    return m


FACINGS = {'S': 0, 'N': 180, 'E': 90, 'W': -90}


def build_cliffs(pal, ao):
    names = []
    for F, deg in FACINGS.items():
        for (a, b) in PAIRS:
            for var in (('', 'b') if a == b else ('',)):
                # S: (west, east); N: rotated 180 so its west edge was the S module's east edge;
                # E (+90): S west edge -> south, east -> north; W (-90): S west -> north, east -> south
                # names use (west, east) for S/N and (north, south) for E/W
                if F == 'S':
                    wa, wb = a, b
                elif F == 'N':
                    wa, wb = b, a
                elif F == 'E':
                    wa, wb = b, a
                else:
                    wa, wb = a, b
                m = cliff_module(pal, wa, wb, seed=1000 + wa * 37 + wb * 11 + (500 if var else 0), rib=bool(var))
                rotate_all(m, deg)
                n = 'Cliff_%s_%d%d%s' % (F, a, b, var)
                finish(n, m, ao)
                names.append(n)
    # corner / notch pillars: stacked faceted spires, kept inside their cell
    for name, H, seed in (('Cliff_Pillar_A', 10.8, 11), ('Cliff_Pillar_B', 10.3, 23), ('Cliff_Pillar_C', 11.4, 37)):
        m = new(pal)
        rnd = random.Random(seed)
        hb = H * rnd.uniform(0.5, 0.58)
        hull(m, clamp_pts(rock_pts(rnd, (0, 0), 0.66, 0.66, hb, n=7, top=3), 0.5), rock_col(0, H))
        hm = H * rnd.uniform(0.78, 0.84)
        c1 = (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08))
        hull(m, clamp_pts(rock_pts(rnd, c1, 0.46, 0.44, hm - hb * 0.8, z0=hb * 0.8, n=6, top=2), 0.48), rock_col(0, H))
        c2 = (c1[0] + rnd.uniform(-0.1, 0.1), c1[1] + rnd.uniform(-0.1, 0.1))
        pts = rock_pts(rnd, c2, 0.3, 0.28, H - hm * 0.9, z0=hm * 0.9, n=5, top=0)
        pts.append((c2[0] + rnd.uniform(-0.05, 0.05), c2[1], H))
        hull(m, clamp_pts(pts, 0.45), rock_col(0, H, snow=0.5))
        finish(name, m, ao)
        names.append(name)
    return names


# ================================================================ boundary treeline ('%', 2x2)
def build_treeline(pal, ao):
    for name, seed, trees in (('Treeline_A', 5, [(-0.45, 0.35, 8.2, 1.35), (0.55, -0.3, 6.3, 1.2)]),
                              ('Treeline_B', 9, [(-0.5, -0.4, 5.6, 1.15), (0.45, 0.45, 7.6, 1.3)])):
        m = new(pal)
        rnd = random.Random(seed)
        # snowy rock bank the trees stand on
        hull(m, clamp_pts(rock_pts(rnd, (0, 0.1), 1.05, 0.95, 0.75, n=8, top=3), 0.98),
             rock_col(0, 0.75, snow=0.45, base='rock2', mid='rock', light='snow2'))
        for (x, y, h, r) in trees:
            spruce(m, x, y, h, r, rnd, tiers=4 if h > 7 else 3, base=0.55, pts=6)
        hull(m, clamp_pts(rock_pts(rnd, (rnd.uniform(-0.5, 0.3), -0.75), 0.32, 0.22, 0.55, n=6, top=2), 0.98), rock_col(0, 0.55))
        finish(name, m, ao, cols=[((0, 0, 2.5), (1.0, 1.0, 2.5))])


# ================================================================ rocks ('o' 1x1, 'O' 2x2)
def build_rocks(pal, ao):
    for name, seed, h, rx, ry in (('Boulder_A', 3, 1.12, 0.47, 0.44), ('Boulder_B', 8, 0.92, 0.48, 0.4), ('Boulder_C', 15, 1.3, 0.42, 0.46)):
        m = new(pal)
        rnd = random.Random(seed)
        MS.boulder(m, hull, rock_pts, clamp_pts, rock_col, rnd, h, rx, ry)
        finish(name, m, ao, cols=[((0, 0, h / 2), (0.46, 0.46, h / 2))])
    for name, seed, h in (('Outcrop_A', 21, 2.3), ('Outcrop_B', 34, 1.9)):
        m = new(pal)
        rnd = random.Random(seed)
        hull(m, clamp_pts(rock_pts(rnd, (0.05, 0.1), 0.98, 0.9, h, n=8, top=3), 0.98), rock_col(0, h))
        hull(m, clamp_pts(rock_pts(rnd, (-0.45, -0.45), 0.5, 0.48, h * 0.55, n=6, top=2), 0.98), rock_col(0, h * 0.55))
        hull(m, clamp_pts(rock_pts(rnd, (0.55, -0.55), 0.36, 0.3, h * 0.35, n=6, top=2), 0.98), rock_col(0, h * 0.35))
        finish(name, m, ao, cols=[((0, 0, h / 2), (0.96, 0.96, h / 2))])


# ================================================================ walls, fence, log pile, crates
def build_cover(pal, ao):
    # dry-stone wall with a snow cap (1 m run module; cap and core flush with the cell so runs read as one wall)
    for name, seed in (('StoneWall_A', 41), ('StoneWall_B', 47)):
        m = new(pal)
        rnd = random.Random(seed)
        m.box((0, 0, 0.41), (1.0, 0.62, 0.82), 'stone2', bevel=False)
        # dry-stone courses: three courses of irregular, chamfered stones of varied length, height and depth
        # (they stop 2 cm short of the module ends, so neighbouring modules never overlap)
        for fy in (-1, 1):
            MS.stone_courses(m, hull, rnd, fy, 0.31, -0.48, 0.48, ((0.02, 0.3), (0.3, 0.57), (0.57, 0.82)))
        m.box((0, 0, 0.89), (1.0, 0.72, 0.14), 'snow', bevel=False)
        # snow heaped along the coping: an uneven mound (kept off the module ends so runs read as one wall)
        sx = rnd.uniform(-0.08, 0.08)
        hull(m, [(sx - 0.42, -0.3, 0.955), (sx + 0.42, -0.3, 0.955), (sx - 0.42, 0.3, 0.955), (sx + 0.42, 0.3, 0.955),
                 (sx - 0.3, -0.2, 1.0 + rnd.uniform(0, 0.03)), (sx + 0.32, -0.18, 1.0 + rnd.uniform(0, 0.03)),
                 (sx - 0.28, 0.2, 1.0 + rnd.uniform(0, 0.03)), (sx + 0.3, 0.19, 1.0 + rnd.uniform(0, 0.03)),
                 (sx + rnd.uniform(-0.1, 0.1), rnd.uniform(-0.05, 0.05), 1.05 + rnd.uniform(0, 0.03))],
             lambda f: 'snow' if f.normal.z > 0.5 else 'snow2')
        finish(name, m, ao, cols=[((0, 0, 0.5), (0.5, 0.36, 0.5))])
    # split-rail fence (rails flush with the cell: runs join up)
    m = new(pal)
    m.box((-0.38, 0, 0.6), (0.14, 0.14, 1.2), 'log2', bevel=False)
    m.box((-0.38, 0, 1.235), (0.17, 0.17, 0.07), 'snow', bevel=False)
    for z, d in ((0.45, 0.05), (0.88, -0.05)):
        m.box((0, d, z), (1.0, 0.08, 0.13), 'log', bevel=False)
    m.box((0, -0.05, 0.96), (1.0, 0.1, 0.03), 'snow', bevel=False)   # sits exactly on the top rail (0.945)
    MP.fence(m)
    finish('Fence', m, ao, cols=[((0, 0, 0.55), (0.5, 0.14, 0.55))])
    # log pile: three long logs (continuous along the run), stakes, snow on the top log
    m = new(pal)
    r = 0.25
    # logs spaced so their end caps (shared plane) never overlap
    for (y, z) in ((-0.26, r), (0.26, r), (0.0, r + 0.44)):
        fs = list(m.cyl((-0.5, y, z), r, r, 1.0, 'log', seg=8, rot=(0, 90, 0), bevel=False))
        paint(m, fs, lambda f: 'logend' if abs(f.normal.x) > 0.9 else ('snow' if f.normal.z > 0.6 and f.calc_center_median().z > 0.8 else 'log'))
    for sx in (-0.42, 0.42):
        for fy in (-1, 1):
            m.box((sx, fy * 0.52, 0.39), (0.07, 0.07, 0.78), 'log2', bevel=False)
            m.cyl((sx, fy * 0.52, 0.78), 0.05, 0.0, 0.12, 'log2', seg=4, rot=(0, 0, 45), bevel=False)   # sharpened top
    MS.logpile_detail(m, r)
    finish('LogPile', m, ao, cols=[((0, 0, 0.5), (0.5, 0.48, 0.5))])
    # supply crate (also the weapon stand) and the canvas bundle stacked on some
    m = new(pal)
    m.box((0, 0, 0.46), (0.92, 0.92, 0.92), 'plank')
    for fy in (-1, 1):
        m.box((0, fy * 0.465, 0.46), (0.94, 0.03, 0.12), 'log2', bevel=False)
        m.beam((-0.36, fy * 0.47, 0.1), (0.36, fy * 0.47, 0.82), 0.06, 'log2')
        m.box((fy * 0.465, 0, 0.46), (0.03, 0.9, 0.135), 'log2', bevel=False)
    m.box((0, 0, 0.935), (0.8, 0.8, 0.05), 'snow', bevel=False)
    m.box((0.28, -0.505, 0.6), (0.18, 0.02, 0.14), 'teal', bevel=False)
    m.box((0, 0, 0.47), (0.12, 0.975, 0.95), 'rope', bevel=False)
    MP.crate(m)
    finish('Crate', m, ao, bevel=0.015, cols=[((0, 0, 0.5), (0.48, 0.48, 0.5))])
    m = new(pal)
    MS.tarp_bundle(m, hull, random.Random(87))
    finish('Bundle', m, ao, bevel=0.03)


# ================================================================ pines ('t' 1x1) and spruce stands ('F' 2x2)
def build_trees(pal, ao):
    # three distinct pines: a full straight one, a younger narrow one, an old one leaning off the wind with a dead stub
    for name, seed, h, r, trunk_h, tiers, lean, stub in (('Pine_A', 2, 7.2, 1.3, 1.6, 5, (0.0, 0.0), False),
                                                        ('Pine_B', 6, 5.6, 1.0, 1.4, 4, (0.1, -0.08), False),
                                                        ('Pine_C', 13, 6.6, 1.22, 1.9, 4, (0.32, 0.18), True)):
        m = new(pal)
        rnd = random.Random(seed)
        MS.frond_tree(m, hull, top_z, rnd, 0, 0, h, r, trunk_h, tiers, trunk_r=0.19, lean=lean, stub=stub)
        # snow banked round the foot, uneven
        hull(m, [(math.cos(a) * rnd.uniform(0.42, 0.56), math.sin(a) * rnd.uniform(0.42, 0.56), 0) for a in [i * 0.9 for i in range(7)]] +
             [(math.cos(a) * 0.3, math.sin(a) * 0.3, rnd.uniform(0.08, 0.13)) for a in [i * 0.9 + 0.4 for i in range(7)]], 'snow')
        finish(name, m, ao, cols=[((0, 0, 1.3), (0.24, 0.24, 1.3))])
    for name, seed, trees in (('SpruceCluster_A', 17, [(-0.4, 0.35, 6.4, 1.2), (0.5, -0.2, 4.7, 0.95), (-0.35, -0.55, 3.3, 0.7)]),
                              ('SpruceCluster_B', 29, [(0.35, 0.4, 5.6, 1.1), (-0.5, -0.1, 4.2, 0.9), (0.45, -0.6, 2.9, 0.62)])):
        m = new(pal)
        rnd = random.Random(seed)
        hull(m, clamp_pts(rock_pts(rnd, (0, 0), 0.92, 0.88, 0.32, n=8, top=3), 0.98), lambda f: 'snow' if f.normal.z > 0.3 else 'snow2')
        for (x, y, h, r) in trees:
            spruce(m, x, y, h, r, rnd, tiers=3, base=0.35, pts=6)
        hull(m, clamp_pts(rock_pts(rnd, (0.55, 0.55), 0.3, 0.26, 0.55, n=6, top=2), 0.98), rock_col(0, 0.55))
        finish(name, m, ao, cols=[((0, 0, 1.5), (0.85, 0.85, 1.5))])


# ================================================================ floor patches (no collision)
def blob(rnd, n, r0, r1, cx=0.0, cy=0.0, sx=1.0, sy=1.0):
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        rr = rnd.uniform(r0, r1)
        pts.append((cx + math.cos(a) * rr * sx, cy + math.sin(a) * rr * sy))
    return pts


def dome(m, ring, heights, colors, center_h):
    """Low mound from an outline ring: concentric rings shrunk toward the centre at the given heights."""
    n = len(ring)
    cx = sum(x for x, y in ring) / n
    cy = sum(y for x, y in ring) / n
    layers = []
    for k, (s, z) in enumerate(heights):
        layers.append(_verts(m, [(cx + (x - cx) * s, cy + (y - cy) * s, z) for x, y in ring]))
    top = _verts(m, [(cx, cy, center_h)])[0]
    fs = []
    for k in range(len(layers) - 1):
        A, B = layers[k], layers[k + 1]
        for i in range(n):
            j = (i + 1) % n
            f = m.bm.faces.new((A[i], A[j], B[j], B[i]))
            f.material_index = m.pal.index(colors[k])
            fs.append(f)
    L = layers[-1]
    for i in range(n):
        j = (i + 1) % n
        f = m.bm.faces.new((L[i], L[j], top))
        f.material_index = m.pal.index(colors[-1])
        fs.append(f)
    bot = m.bm.faces.new(layers[0][::-1])
    bmesh.ops.recalc_face_normals(m.bm, faces=fs + [bot])
    bmesh.ops.delete(m.bm, geom=[bot], context='FACES_ONLY')
    tag(m, _tri(m, fs))


def build_patches(pal, ao):
    for name, seed in (('Drift_A', 51), ('Drift_B', 57)):
        m = new(pal)
        rnd = random.Random(seed)
        ring = blob(rnd, 14, 1.05, 1.42, sx=1.0, sy=rnd.uniform(0.8, 0.95))
        dome(m, ring, [(1.0, 0.0), (0.9, 0.06), (0.62, 0.13), (0.3, 0.17)], ['snow2', 'snow', 'snow'], 0.19)
        finish(name, m, ao)
    for name, seed in (('Meadow_A', 61), ('Meadow_B', 67)):
        m = new(pal)
        rnd = random.Random(seed)
        ring = blob(rnd, 13, 1.0, 1.4, sy=rnd.uniform(0.85, 1.0))
        dome(m, ring, [(1.0, 0.0), (0.97, 0.022)], ['meadow2', 'meadow'], 0.026)
        # a few flat snow patches left on the grass
        for k in range(3):
            a, rr = rnd.uniform(0, 6.28), rnd.uniform(0.3, 0.7)
            dome(m, blob(rnd, 8, 0.16, 0.26, cx=math.cos(a) * rr, cy=math.sin(a) * rr), [(1.0, 0.0), (0.92, 0.034 + 0.004 * k)], ['snow'], 0.036 + 0.004 * k)
        finish(name, m, ao)
    # frozen pond (4x4): ice, snowy rim, cracks proud of the ice
    m = new(pal)
    rnd = random.Random(71)
    ring = blob(rnd, 16, 1.42, 1.7, sy=0.92)
    dome(m, ring, [(1.0, 0.0), (0.99, 0.032)], ['ice', 'ice'], 0.032)
    rim_o = [(x * 1.12, y * 1.12) for x, y in ring]
    rim_i = [(x * 0.94, y * 0.94) for x, y in ring]
    n = len(ring)
    # rim: ring of low snow wedges (a closed band)
    vo0 = _verts(m, [(x, y, 0.0) for x, y in rim_o])
    vo1 = _verts(m, [(x * 0.985, y * 0.985, 0.075) for x, y in rim_o])
    vi1 = _verts(m, [(x * 1.02, y * 1.02, 0.07) for x, y in rim_i])
    vi0 = _verts(m, [(x, y, 0.02) for x, y in rim_i])
    fs = []
    for i in range(n):
        j = (i + 1) % n
        for A, B in ((vo0, vo1), (vo1, vi1), (vi1, vi0), (vi0, vo0)):
            fs.append(m.bm.faces.new((A[i], A[j], B[j], B[i])))
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    tag(m, _tri(m, fs), 'snow')
    for k in range(4):
        # crossing cracks: each one's top and bottom 4 mm apart from the others
        a = rnd.uniform(0, 6.28)
        L = rnd.uniform(0.5, 1.1)
        x0, y0 = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)
        z0, z1 = 0.026 - 0.004 * k, 0.036 + 0.004 * k
        m.box((x0, y0, (z0 + z1) / 2), (L, 0.035, z1 - z0), 'ice2', rot=(0, 0, math.degrees(a)), bevel=False)
    finish('Pond', m, ao)
    # frozen creek segment (2x2): open-ended ice band and banks, so segments join without outline seams
    m = new(pal)
    creek(m, -1.0, 1.0)
    finish('Creek', m, ao)


def creek(m, y0, y1):
    """Frozen creek band from y0 to y1 (open ends: tiles seamlessly) with low snow banks along both sides."""
    L = y1 - y0
    left = [(-0.55, y0), (-0.6, y0 + 0.3 * L), (-0.44, y0 + 0.66 * L), (-0.55, y1)]
    right = [(0.55, y0), (0.62, y0 + 0.36 * L), (0.47, y0 + 0.7 * L), (0.55, y1)]
    top = _verts(m, [(x, y, 0.028) for x, y in right + left[::-1]])
    bl = _verts(m, [(x, y, 0.0) for x, y in left])
    br = _verts(m, [(x, y, 0.0) for x, y in right])
    n = len(left)
    tl = top[n:][::-1]
    tr = top[:n]
    fs = []

    def face(vs, want):
        f = m.bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(Vector(want)) < 0:
            bmesh.ops.reverse_faces(m.bm, faces=[f])
        fs.append(f)
    face(top, (0, 0, 1))
    for i in range(n - 1):
        face((tr[i], tr[i + 1], br[i + 1], br[i]), (1, 0, 0))
        face((tl[i], tl[i + 1], bl[i + 1], bl[i]), (-1, 0, 0))
    tag(m, _tri(m, fs), 'ice')
    for sx in (-1, 1):
        prof = [(sx * 0.46, 0.0), (sx * 0.58, 0.07), (sx * 0.8, 0.11), (sx * 0.97, 0.03), (sx * 0.97, 0.0)]
        loft_open(m, prof, prof, ['snow2', 'snow', 'snow', 'snow2'], 'snow2', axis='y', a0=y0, a1=y1, inset=0.02)


# ================================================================ small decorations ('p')
def build_decor(pal, ao):
    m = new(pal)
    m.box((0, 0, 1.1), (0.14, 0.14, 2.2), 'log2', bevel=False)
    m.box((0, 0, 2.235), (0.18, 0.18, 0.07), 'snow', bevel=False)
    for z, ang, col, L in ((1.85, 20, 'tangerine', 0.9), (1.5, -35, 'plank', 0.8), (1.15, 160, 'teal', 0.75)):
        m.parent = Matrix.Translation((0, 0, z)) @ Matrix.Rotation(math.radians(ang), 4, 'Z')
        # arrow board along +x from inside the post, pointed tip at the end
        board = [(-0.025, -0.11), (0.025, -0.11), (0.025, 0.11), (-0.025, 0.11)]
        prism(m, board, -0.04, L, col, axis='x')
        prism(m, board, L, L + 0.16, col, axis='x', prof1=[(-0.025, -0.004), (0.025, -0.004), (0.025, 0.004), (-0.025, 0.004)])
        m.parent = Matrix.Identity(4)
    hull(m, [(math.cos(a) * 0.35, math.sin(a) * 0.3, 0) for a in [i * 1.05 for i in range(6)]] + [(0.05, 0.02, 0.12), (-0.1, 0.05, 0.1)], 'snow')
    MP.signpost(m)
    finish('Signpost', m, ao, cols=[((0, 0, 1.1), (0.12, 0.12, 1.1))])
    m = new(pal)
    m.box((0, 0, 1.2), (0.14, 0.14, 2.4), 'log2', bevel=False)
    m.box((0.32, 0, 2.3), (0.6, 0.1, 0.1), 'log2', bevel=False)
    m.box((0.55, 0, 2.08), (0.03, 0.03, 0.34), 'gunmetal', bevel=False)
    m.box((0.55, 0, 1.78), (0.26, 0.26, 0.3), 'gunmetal', bevel=False)
    m.box((0.55, 0, 1.78), (0.2, 0.28, 0.24), 'glow', bevel=False)
    m.box((0.55, 0, 1.78), (0.28, 0.2, 0.2), 'glow', bevel=False)
    m.cyl((0.55, 0, 1.93), 0.17, 0.02, 0.14, 'gunmetal', seg=4, rot=(0, 0, 45), bevel=False)
    m.box((0, 0, 2.435), (0.18, 0.18, 0.07), 'snow', bevel=False)
    m.box((0.32, 0, 2.367), (0.62, 0.12, 0.035), 'snow', bevel=False)
    MP.lanternpost(m)
    finish('LanternPost', m, ao, cols=[((0, 0, 1.2), (0.12, 0.12, 1.2))])
    m = new(pal)
    rnd = random.Random(81)
    hull(m, [(math.cos(a) * 0.42, math.sin(a) * 0.36, 0) for a in [i * 0.9 for i in range(7)]] +
         [(math.cos(a) * 0.25, math.sin(a) * 0.2, 0.2) for a in [i * 1.3 for i in range(5)]], 'snow')
    for k, (col, tilt, yaw) in enumerate((('tangerine', 12, 8), ('lift', -10, -6))):
        mm = Matrix.Translation((0.06 * (1 if k else -1), 0, 0.1)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(tilt), 4, 'Y')
        m.parent = mm
        m.box((0, 0, 0.8), (0.1, 0.035, 1.6), col, bevel=False)
        m.box((0, -0.03, 1.55), (0.088, 0.04, 0.12), col, rot=(25, 0, 0), bevel=False)
        m.parent = Matrix.Identity(4)
    for k, x in enumerate((-0.28, 0.3)):
        m.beam((x, 0.14, 0.05), (x * 1.25, 0.2 + 0.05 * k, 1.25), 0.025, 'gunmetal')
        m.cyl((x * 1.02, 0.15 + 0.01 * k, 0.22), 0.07, 0.07, 0.02, 'gunmetal', seg=5, bevel=False)
    finish('Skis', m, ao, cols=[((0, 0, 0.6), (0.3, 0.2, 0.6))])


# ================================================================ campfire ('Q' 3x3)
def build_campfire(pal, ao):
    m = new(pal)
    rnd = random.Random(91)
    for i in range(9):
        a = i / 9 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
        hull(m, rock_pts(rnd, (math.cos(a) * 0.62, math.sin(a) * 0.62), 0.16, 0.13, 0.2, n=5, top=2), rock_col(0, 0.2, base='stone2', mid='stone', light='stone'))
    hull(m, [(math.cos(a) * 0.45, math.sin(a) * 0.45, 0) for a in [i * 0.8 for i in range(8)]] + [(0, 0, 0.04), (0.1, 0.1, 0.035)], 'gunmetal')
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.4
        m.beam((math.cos(a) * 0.42, math.sin(a) * 0.42, 0.06), (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.6), 0.11, 'log2')
    star(m, (0, 0, 0.12), 0.32, 0.95, 'flame', pts=5, inner=0.55, droop=0.0, phase=10, under=0.1)
    star(m, (0.03, 0.02, 0.15), 0.22, 0.75, 'amber', pts=5, inner=0.55, droop=0.0, phase=46, under=0.1)
    star(m, (-0.02, 0.0, 0.18), 0.12, 0.5, 'glow', pts=4, inner=0.6, droop=0.0, phase=20, under=0.1)
    # cooking tripod with a pot
    for i in range(3):
        a = i / 3 * 2 * math.pi + 1.0
        m.beam((math.cos(a) * 0.72, math.sin(a) * 0.72, 0.0), (0, 0, 1.45), 0.04, 'gunmetal')
    m.beam((0, 0, 1.45), (0, 0, 1.12), 0.015, 'gunmetal')
    m.cyl((0, 0, 0.92), 0.15, 0.17, 0.2, 'gunmetal', seg=8, bevel=False)
    # two split-log benches on stumps
    for (cx, cy, rotz) in ((0, 1.08, 0), (-1.08, -0.1, 90)):
        mm = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(math.radians(rotz), 4, 'Z')
        m.parent = mm
        for sx in (-0.45, 0.45):
            m.cyl((sx, 0, 0), 0.15, 0.14, 0.3, 'trunk', seg=6, bevel=False)
        prism(m, [(-0.17, 0.3), (0.17, 0.3), (0.17, 0.36), (0.1, 0.44), (-0.1, 0.44), (-0.17, 0.36)], -0.68, 0.68, 'log', axis='x')
        m.box((0.2, 0, 0.455), (0.5, 0.2, 0.03), 'snow', bevel=False)
        m.parent = Matrix.Identity(4)
    m.box((1.0, 0.85, 0.25), (0.5, 0.42, 0.5), 'plank', bevel=False)
    m.box((1.0, 0.85, 0.515), (0.44, 0.36, 0.03), 'snow', bevel=False)
    finish('Campfire', m, ao, cols=[((0, 0, 0.3), (0.72, 0.72, 0.3)), ((0, 1.08, 0.23), (0.7, 0.2, 0.23)),
                                     ((-1.08, -0.1, 0.23), (0.2, 0.7, 0.23)), ((1.0, 0.85, 0.27), (0.25, 0.21, 0.27))])


# ================================================================ log cabin ('H' 6x5)
def build_cabin(pal, ao):
    m = new(pal)
    X, Yf, Yb = 2.3, -1.3, 1.9          # side wall line, front/back wall lines
    r, pitch, n = 0.17, 0.345, 7
    m.box((0, (Yf + Yb) / 2, 1.23), (2 * X - 0.1, Yb - Yf - 0.1, 2.46), 'canvas', bevel=False)   # chinking core
    for k in range(n):
        ext = 0.004 * (k % 2)
        for y in (Yf, Yb):
            fs = list(m.cyl((-X - 0.22 - ext, y, r + k * pitch), r, r, 2 * X + 0.44 + 2 * ext, 'log', seg=6, rot=(0, 90, 0), bevel=False))
            paint(m, fs, lambda f: 'logend' if abs(f.normal.x) > 0.9 else 'log')
        for x in (-X, X):
            fs = list(m.cyl((x, Yf - 0.22 - ext, r + pitch / 2 + k * pitch), r, r, Yb - Yf + 0.44 + 2 * ext, 'log', seg=6, rot=(-90, 0, 0), bevel=False))
            paint(m, fs, lambda f: 'logend' if abs(f.normal.y) > 0.9 else 'log2')
    eave, ridge, yr = 2.55, 4.35, (Yf + Yb) / 2
    # gable triangle (attic) and roof slabs with snow
    prism(m, [(Yf - 0.02, eave - 0.1), (Yb + 0.02, eave - 0.1), (yr, ridge - 0.1)], -X - 0.12, X + 0.12, 'log2', axis='x')
    ov, th = 0.45, 0.16
    for sgn in (-1, 1):
        ye = (Yf - ov) if sgn < 0 else (Yb + ov)
        slope = (ridge - eave) / (yr - Yf)
        ze = eave - slope * ov
        prism(m, [(ye, ze), (yr, ridge), (yr, ridge + th), (ye, ze + th)], -X - 0.38, X + 0.38, 'roof', axis='x')
        prism(m, [(ye + 0.07 * -sgn, ze + th + 0.01 + 0.07 * slope), (yr, ridge + th + 0.01), (yr, ridge + th + 0.13), (ye + 0.04 * -sgn, ze + th + 0.12 + 0.04 * slope)],
              -X - 0.33, X + 0.33, 'snow', axis='x')
    m.box((0, yr, ridge + th + 0.15), (2 * X + 0.62, 0.22, 0.12), 'snow', bevel=False)
    # icicles along the front eave
    rnd = random.Random(101)
    slope = (ridge - eave) / (yr - Yf)
    ze = eave - slope * ov
    for i in range(7):
        x = -X + 0.2 + i * (2 * X - 0.4) / 6 + rnd.uniform(-0.1, 0.1)
        m.cyl((x, Yf - ov + 0.06, ze + slope * 0.06 + 0.01), 0.045, 0.0, rnd.uniform(0.2, 0.42), 'ice2', seg=4, rot=(180, 0, 0), bevel=False)
    # porch deck and posts under the front eave
    m.box((0, Yf - 0.62, 0.07), (2 * X + 0.1, 0.84, 0.14), 'plank', bevel=False)
    py = Yf - 0.38
    pz = ze + slope * (py - (Yf - ov))
    for sx in (-1, 1):
        m.box((sx * (X - 0.05), py, (0.14 + pz) / 2), (0.16, 0.16, pz - 0.14), 'log2', bevel=False)
    # door, windows with red shutters, lanterns (frames reach into the logs; each layer >= 3 mm proud)
    fy = Yf - 0.2       # frame centre: frames span -1.56 .. -1.44 (log faces at -1.447)
    m.box((0, fy, 1.06), (1.1, 0.12, 2.08), 'log2', bevel=False)
    m.box((0, fy - 0.08, 1.0), (0.86, 0.04, 1.86), 'door', bevel=False)
    m.box((0.28, fy - 0.12, 1.0), (0.07, 0.04, 0.07), 'amber', bevel=False)
    for sx in (-1, 1):
        x = sx * 1.35
        m.box((x, fy, 1.45), (0.92, 0.12, 0.86), 'log2', bevel=False)
        m.box((x, fy - 0.08, 1.45), (0.72, 0.04, 0.66), 'glow', bevel=False)
        m.box((x, fy - 0.115, 1.45), (0.05, 0.04, 0.72), 'log2', bevel=False)
        m.box((x, fy - 0.12, 1.45), (0.78, 0.04, 0.05), 'log2', bevel=False)
        m.box((x, fy - 0.09, 1.0), (0.98, 0.14, 0.06), 'snow', bevel=False)
        for s2 in (-1, 1):
            m.box((x + s2 * 0.6, fy + 0.0075, 1.45), (0.26, 0.105, 0.86), 'roof', bevel=False)
        m.box((sx * 0.75, fy - 0.1, 1.85), (0.16, 0.16, 0.22), 'gunmetal', bevel=False)
        m.box((sx * 0.75, fy - 0.1, 1.85), (0.12, 0.18, 0.16), 'glow', bevel=False)
        m.box((sx * 0.75, fy, 2.0), (0.04, 0.12, 0.04), 'gunmetal', bevel=False)
    # side window (east) and round gable window (west)
    m.box((X + 0.2, 0.4, 1.45), (0.12, 0.92, 0.86), 'log2', bevel=False)
    m.box((X + 0.28, 0.4, 1.45), (0.04, 0.72, 0.66), 'glow', bevel=False)
    m.box((X + 0.315, 0.4, 1.45), (0.04, 0.05, 0.72), 'log2', bevel=False)
    m.cyl((-X - 0.13, -0.25, 3.15), 0.3, 0.3, 0.05, 'log2', seg=10, rot=(0, -90, 0), bevel=False)
    m.cyl((-X - 0.17, -0.25, 3.15), 0.21, 0.21, 0.04, 'glow', seg=10, rot=(0, -90, 0), bevel=False)
    # stone chimney on the west gable
    cx = -X - 0.42
    m.box((cx, 0.9, 1.6), (0.56, 0.86, 3.2), 'stone2', bevel=False)
    m.box((cx, 0.9, 1.6), (0.6, 0.74, 3.1), 'stone', bevel=False)
    m.box((cx, 0.9, 4.0), (0.44, 0.6, 1.62), 'stone', bevel=False)
    m.box((cx, 0.9, 4.86), (0.54, 0.7, 0.12), 'stone2', bevel=False)
    m.box((cx, 0.9, 4.96), (0.46, 0.62, 0.08), 'snow', bevel=False)
    # firewood stack under the east eave (log ends face east)
    m.box((X + 0.42, -0.2, 0.5), (0.4, 1.6, 1.0), 'log2', bevel=False)
    for i in range(3):
        for j in range(2):
            fs = list(m.cyl((X + 0.3, -0.82 + i * 0.42 + j * 0.2, 0.22 + j * 0.42 + (i % 2) * 0.1), 0.15, 0.15, 0.36, 'log', seg=6, rot=(0, 90, 0), bevel=False))
            paint(m, fs, lambda f: 'logend' if abs(f.normal.x) > 0.9 else 'log')
    m.box((X + 0.42, -0.2, 1.04), (0.44, 1.64, 0.08), 'snow', bevel=False)
    # snow drift against the back-west corner
    hull(m, clamp_pts(rock_pts(rnd, (-2.2, 2.0), 0.8, 0.45, 0.5, n=6, top=2), 2.95), lambda f: 'snow' if f.normal.z > 0.35 else 'snow2')
    MP.cabin(m)
    finish('Landmark_Cabin', m, ao, cols=[((0, 0.3, 1.5), (2.55, 1.85, 1.5)), ((cx, 0.9, 1.5), (0.3, 0.45, 1.5)),
                                          ((0, Yf - 0.62, 0.07), (X + 0.05, 0.42, 0.07)), ((X + 0.42, -0.2, 0.5), (0.22, 0.8, 0.5)),
                                          ((-(X - 0.05), py, 1.1), (0.1, 0.1, 1.1)), ((X - 0.05, py, 1.1), (0.1, 0.1, 1.1))])


# ================================================================ A-frame chalet ('A' 5x6, gable faces -Y)
def build_chalet(pal, ao):
    m = new(pal)
    W, ridge, y0, y1 = 2.42, 6.3, -2.55, 2.75
    zb = 0.35
    # stone footing along the eaves
    for sx in (-1, 1):
        m.box((sx * 2.05, 0.1, 0.18), (0.72, 5.2, 0.36), 'stone2', bevel=False)
    # front and back gable walls
    prism(m, [(-2.05, 0.0), (2.05, 0.0), (0.0, ridge - 0.35)], y0 + 0.2, y0 + 0.42, 'log', axis='y')
    prism(m, [(-2.05, 0.0), (2.05, 0.0), (0.0, ridge - 0.35)], y1 - 0.42, y1 - 0.2, 'log2', axis='y')
    # roof slabs + snow
    slope = (ridge - zb) / W
    for sgn in (-1, 1):
        prism(m, [(sgn * (W + 0.05), zb - 0.05), (sgn * (W + 0.05), zb + 0.15), (0, ridge + 0.2), (0, ridge)], y0, y1, 'roof2', axis='y')
        prism(m, [(sgn * (W - 0.1), zb + 0.15 + 0.15 * slope + 0.02), (sgn * (W - 0.12), zb + 0.3 + 0.12 * slope),
                  (0, ridge + 0.34), (0, ridge + 0.215)], y0 + 0.05, y1 - 0.05, 'snow', axis='y')
    m.box((0, (y0 + y1) / 2, ridge + 0.3), (0.32, y1 - y0 - 0.04, 0.14), 'snow', bevel=False)
    # front glass: panels in the gable (proud of the wall), door, balcony with railing
    fy = y0 + 0.17     # gable front face at y0 + 0.2; frames span fy-0.03 .. fy+0.03
    for (x, z, w, h) in ((-0.95, 1.1, 0.5, 1.2), (0.95, 1.1, 0.5, 1.2), (-0.4, 3.1, 0.5, 0.9), (0.4, 3.1, 0.5, 0.9), (0.0, 4.35, 0.45, 0.6)):
        m.box((x, fy, z), (w + 0.12, 0.06, h + 0.12), 'log2', bevel=False)
        m.box((x, fy - 0.05, z), (w, 0.04, h), 'glow', bevel=False)
        m.box((x, fy - 0.085, z), (w + 0.05, 0.03, 0.05), 'log2', bevel=False)
    m.box((0, fy, 1.05), (1.0, 0.06, 2.1), 'log2', bevel=False)
    m.box((0, fy - 0.05, 1.0), (0.82, 0.04, 1.92), 'door', bevel=False)
    m.box((0.27, fy - 0.09, 1.0), (0.07, 0.04, 0.07), 'amber', bevel=False)
    m.box((0, y0 - 0.12, 0.1), (1.3, 0.5, 0.2), 'stone', bevel=False)
    bz = 2.45
    by = -2.55
    m.box((0, by, bz), (2.9, 0.8, 0.14), 'plank', bevel=False)
    m.box((0, by, bz + 0.085), (2.8, 0.72, 0.03), 'snow', bevel=False)
    ry = -2.88
    for x in (-1.38, -0.46, 0.46, 1.38):
        m.box((x, ry, bz + 0.45), (0.08, 0.08, 0.96), 'log2', bevel=False)
    m.box((0, ry, bz + 0.95), (2.9, 0.1, 0.1), 'log', bevel=False)
    m.box((0, ry, bz + 1.015), (2.9, 0.12, 0.03), 'snow', bevel=False)
    m.box((0, ry, bz + 0.5), (2.8, 0.05, 0.07), 'log', bevel=False)
    for sx in (-1, 1):
        m.beam((sx * 1.38, -2.8, 0.0), (sx * 1.38, -2.8, bz - 0.07), 0.12, 'log2')
    # chimney through the east slope
    m.box((1.1, 1.3, 4.6), (0.5, 0.6, 2.6), 'stone', bevel=False)
    m.box((1.1, 1.3, 5.95), (0.6, 0.7, 0.1), 'stone2', bevel=False)
    m.box((1.1, 1.3, 6.04), (0.52, 0.62, 0.08), 'snow', bevel=False)
    # lantern pair and skis leaning by the door
    for sx in (-1, 1):
        m.box((sx * 0.62, fy - 0.12, 2.0), (0.16, 0.16, 0.22), 'gunmetal', bevel=False)
        m.box((sx * 0.62, fy - 0.12, 2.0), (0.12, 0.18, 0.16), 'glow', bevel=False)
    for k, col in enumerate(('tangerine', 'teal')):
        m.box((1.65 + k * 0.14, y0 - 0.0, 0.85), (0.09, 0.03, 1.7), col, rot=(-8, 4 - k * 6, 0), bevel=False)
    MP.chalet(m)
    finish('Landmark_Chalet', m, ao, cols=[((0, 0.1, 1.5), (2.3, 2.6, 1.5)), ((0, y0 - 0.12, 0.1), (0.65, 0.25, 0.1))])


# ================================================================ fire lookout tower ('T' 4x4)
def build_lookout(pal, ao):
    m = new(pal)
    b, t, top = 1.55, 1.08, 9.0
    legs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for sx, sy in legs:
        m.box((sx * b, sy * b, 0.2), (0.62, 0.62, 0.4), 'stone')
        m.beam((sx * b, sy * b, 0.38), (sx * t, sy * t, top), 0.27, 'log2')

    def leg_at(sx, sy, z):
        k = (z - 0.38) / (top - 0.38)
        return (sx * (b + (t - b) * k), sy * (b + (t - b) * k), z)
    levels = [0.5, 3.3, 6.2, 8.8]
    for i in range(4):
        (ax, ay), (bx, by) = legs[i], legs[(i + 1) % 4]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        for lv in range(3):
            za, zc = levels[lv], levels[lv + 1]
            pa, pb = leg_at(ax, ay, za), leg_at(bx, by, zc)
            pc, pd = leg_at(bx, by, za), leg_at(ax, ay, zc)
            off = 0.05
            m.beam((pa[0] + mx * off, pa[1] + my * off, pa[2]), (pb[0] + mx * off, pb[1] + my * off, pb[2]), 0.11, 'log')
            m.beam((pc[0] - mx * off, pc[1] - my * off, pc[2]), (pd[0] - mx * off, pd[1] - my * off, pd[2]), 0.11, 'log')
            if lv > 0:
                g0, g1 = leg_at(ax, ay, za + 0.02 * (i % 2)), leg_at(bx, by, za + 0.02 * (i % 2))
                m.beam(g0, g1, 0.16, 'log2')
    # stairs: three flights with landings inside the legs
    flights = [((-0.95, -0.62, 0.0), (0.85, -0.62, 3.3)), ((0.85, 0.62, 3.3), (-0.95, 0.62, 6.2)), ((-0.95, -0.62, 6.2), (0.7, -0.62, 8.85))]
    for (p0, p1) in flights:
        for sy in (-0.3, 0.3):
            m.beam((p0[0], p0[1] + sy, p0[2]), (p1[0], p1[1] + sy, p1[2]), 0.08, 'log2')
        steps = 7
        for s in range(1, steps):
            k = s / steps
            m.box((p0[0] + (p1[0] - p0[0]) * k, p0[1], p0[2] + (p1[2] - p0[2]) * k + 0.05), (0.2, 0.62, 0.045), 'plank', bevel=False)
    for (x, y, z) in ((0.95, 0.0, 3.3), (-1.0, 0.0, 6.2)):
        m.box((x, y, z - 0.03), (0.4, 1.9, 0.07), 'plank', bevel=False)
    # cab deck, catwalk railing
    D = 1.7
    m.box((0, 0, top + 0.1), (2 * D, 2 * D, 0.22), 'log2')
    m.box((0, 0, top + 0.225), (2 * D - 0.08, 2 * D - 0.08, 0.03), 'snow', bevel=False)
    for i in range(4):
        (ax, ay), (bx, by) = legs[i], legs[(i + 1) % 4]
        for k in (0.0, 0.5):
            px, py = ax * (1 - k) + bx * k, ay * (1 - k) + by * k
            m.box((px * (D - 0.06), py * (D - 0.06), top + 0.74), (0.09, 0.09, 1.04), 'log2', bevel=False)
        zr = top + 1.18 + 0.004 * (i % 2)
        m.beam((ax * (D - 0.06), ay * (D - 0.06), zr), (bx * (D - 0.06), by * (D - 0.06), zr), 0.08, 'log')
        zm = top + 0.7 + 0.004 * (i % 2)
        m.beam((ax * (D - 0.03), ay * (D - 0.03), zm), (bx * (D - 0.03), by * (D - 0.03), zm), 0.05, 'log')
    # cab: timber lower wall, windows all round (sky glass), white mullions, pyramid roof with snow
    C, zc0, zc1 = 1.18, top + 0.23, top + 2.55
    m.box((0, 0, (zc0 + zc1) / 2), (2 * C, 2 * C, zc1 - zc0), 'log')
    for ang in (0, 90, 180, 270):
        mm = Matrix.Rotation(math.radians(ang), 4, 'Z')
        m.parent = mm
        m.box((0, -C - 0.01, zc0 + 1.45), (2 * C - 0.24, 0.04, 1.15), 'ice', bevel=False)          # -C-0.03 .. -C+0.01
        for x in (-0.4, 0.4):
            m.box((x, -C - 0.045, zc0 + 1.45), (0.07, 0.04, 1.2), 'paper', bevel=False)        # -C-0.065 .. -C-0.025
        m.box((0, -C - 0.04, zc0 + 0.86), (2 * C - 0.2, 0.08, 0.06), 'paper', bevel=False)
        m.parent = Matrix.Identity(4)
    m.cyl((0, 0, zc1), 2.05, 0.0, 1.45, 'roof', seg=4, rot=(0, 0, 45), bevel=False)
    m.cyl((0, 0, zc1 + 0.62), 1.2, 0.0, 0.89, 'snow', seg=4, rot=(0, 0, 45), bevel=False)
    m.cyl((0, 0, zc1 + 1.3), 0.03, 0.03, 0.9, 'gunmetal', seg=4, bevel=False)
    m.sphere((0, 0, zc1 + 2.25), 0.11, 'amber', seg=(6, 4))
    # tangerine pennant on the rod
    m.parent = Matrix.Translation((0.03, 0, zc1 + 1.8))
    prism(m, [(0.0, 0.0), (0.0, 0.3), (0.5, 0.15)], -0.012, 0.012, 'tangerine', axis='y')
    m.parent = Matrix.Identity(4)
    cols = [((sx * b, sy * b, 1.0), (0.32, 0.32, 1.0)) for sx, sy in legs] + [((-0.45, -0.62, 0.6), (0.55, 0.36, 0.6))]
    MP.lookout(m)
    finish('Landmark_Lookout', m, ao, cols=cols)


# ================================================================ rope bridge between two rock towers ('Y' 14x4)
def build_ropebridge(pal, ao):
    m = new(pal)
    half, zend, sag = 3.6, 8.65, 0.75
    for sx, H, seed in ((-1, 9.0, 1), (1, 9.5, 2)):
        rr = random.Random(seed + 200)
        cx = sx * 5.0
        rock = []
        rock += hull(m, clamp_pts([(x + cx, y, z) for x, y, z in rock_pts(rr, (0, 0), 2.0, 1.95, H * 0.62, n=8, top=3)], 6.95, 1.95),
                     rock_col(0, H))
        rock += hull(m, clamp_pts([(x + cx, y, z) for x, y, z in rock_pts(rr, (sx * 0.15, 0.1), 1.55, 1.45, H * 0.45, z0=H * 0.45, n=7, top=2)], 6.95, 1.95),
                     rock_col(0, H))
        rock += hull(m, clamp_pts([(x + cx, y, z) for x, y, z in rock_pts(rr, (sx * 0.35, -0.05), 1.1, 1.0, H * 0.2, z0=H * 0.8, n=6, top=3, waist=(0.5, 0.8))], 6.95, 1.95),
                     rock_col(0, H, snow=0.5))
        # a wind-bent spruce on the summit
        tx, ty = cx + sx * 0.75, 0.55
        tz = top_z(rock, tx, ty) or H
        m.parent = Matrix.Translation((tx, ty, tz - 0.12))
        # own random stream for the tree, so the rocks after it (and the fitted collision) stay as they were
        spruce(m, 0, 0, 2.7, 0.78, random.Random(seed + 777), tiers=3, base=0.25)
        for _ in range(3):
            rr.uniform(-2, 2)
        m.parent = Matrix.Identity(4)
        # masonry abutment the bridge lands on, posts with rope wraps
        # timber cribbing the deck lands on (log courses crossing at the corners)
        ax = sx * 3.95
        m.box((ax, 0, zend - 0.08 - 0.75), (0.96, 1.4, 1.5), 'log2', bevel=False)
        for k in range(3):
            zc = zend - 0.08 - 0.25 - k * 0.5
            fs = list(m.cyl((ax - 0.53, -0.72, zc), 0.12, 0.12, 1.06, 'log', seg=6, rot=(0, 90, 0), bevel=False))
            fs += list(m.cyl((ax - 0.53, 0.72, zc), 0.12, 0.12, 1.06, 'log', seg=6, rot=(0, 90, 0), bevel=False))
            paint(m, fs, lambda f: 'logend' if abs(f.normal.x) > 0.9 else 'log')
        for y in (-0.66, 0.66):
            px = sx * (half + 0.32)
            m.cyl((px, y, zend - 0.1), 0.11, 0.09, 1.5, 'log2', seg=6, bevel=False)
            m.cyl((px, y, zend + 0.82), 0.135, 0.135, 0.14, 'rope', seg=6, bevel=False)
            m.cyl((px, y, zend + 1.4), 0.12, 0.0, 0.16, 'snow', seg=6, bevel=False)
        for k in range(2):
            hull(m, rock_pts(rr, (sx * (3.25 + k * 0.35), -1.35 + k * 2.45), 0.35, 0.3, 0.45, n=6, top=2), rock_col(0, 0.45))
    # bridge: deck planks on a catenary, deck ropes, handrails, suspenders
    N = 15
    for i in range(N):
        x = -half + 0.25 + i * (2 * half - 0.5) / (N - 1)
        z = catenary(x, half, zend, sag)
        dz = 2 * sag * x / half ** 2
        m.box((x, 0, z), (0.3, 1.1, 0.06), 'plank' if i % 3 else 'log2', rot=(0, -math.degrees(math.atan(dz)), 0), bevel=False)
    segs = 6
    for y, dzr, s2, col in ((-0.5, -0.06, sag, 'rope'), (0.5, -0.064, sag, 'rope'), (-0.62, 0.95, sag * 0.8, 'rope'), (0.62, 0.955, sag * 0.8, 'rope')):
        for i in range(segs):
            xa = -half - 0.2 + i * (2 * half + 0.4) / segs
            xb = xa + (2 * half + 0.4) / segs
            za = catenary(max(-half, min(half, xa)), half, zend, s2) + dzr
            zb2 = catenary(max(-half, min(half, xb)), half, zend, s2) + dzr
            yo = y + 0.004 * (i % 2)       # consecutive segments in parallel planes 4 mm apart
            m.beam((xa, yo, za), (xb, yo, zb2), 0.05 if dzr < 0 else 0.06, col)
    for i in range(1, 6):
        x = -half + i * 2 * half / 6
        for y in (-0.56, 0.56):
            zd = catenary(x, half, zend, sag) - 0.03
            zr = catenary(x, half, zend, sag * 0.8) + 0.95
            m.beam((x + 0.012 * (1 if y > 0 else -1), y, zd), (x, y, zr), 0.025, 'rope')
    # bunting along the north handrail
    for i in range(8):
        x = -half + 0.4 + i * (2 * half - 0.8) / 7
        z = catenary(x, half, zend, sag * 0.8) + 0.93
        m.parent = Matrix.Translation((x, 0.63, z))
        prism(m, [(-0.13, 0.0), (0.13, 0.0), (0.0, -0.3)], -0.012, 0.012, ('tangerine', 'teal', 'amber', 'paper')[i % 4], axis='y')
        m.parent = Matrix.Identity(4)
    # frozen creek through the pass (lines up with the 2x2 Creek pieces north and south)
    creek(m, -2.0, 2.0)
    cols = [((sx * 5.0, 0, 4.5), (2.0, 2.0, 4.5)) for sx in (-1, 1)]
    MP.ropebridge(m, catenary, half, zend, sag)
    finish('Landmark_RopeBridge', m, ao, cols=cols)


# ================================================================ ski lift: station ('J' 5x4) and line ('K' 3x12)
CABLE_Z, CABLE_X = 6.1, 1.1


def chair(m, x, y):
    m.box((x, y, CABLE_Z + 0.02), (0.12, 0.3, 0.16), 'gunmetal', bevel=False)
    m.beam((x, y, CABLE_Z - 0.02), (x, y, 4.75), 0.06, 'steel')
    m.box((x, y, 4.75), (0.95, 0.12, 0.06), 'steel', bevel=False)
    m.box((x, y - 0.02, 4.4), (0.95, 0.5, 0.08), 'tangerine', bevel=False)
    m.box((x, y + 0.24, 4.68), (0.93, 0.07, 0.5), 'tangerine', bevel=False)
    for sx in (-0.45, 0.45):
        m.beam((x + sx, y + 0.02, 4.42), (x + sx, y + 0.02, 4.75), 0.04, 'steel')
    m.box((x, y - 0.26, 4.62), (0.9, 0.04, 0.04), 'steel', bevel=False)
    m.box((x, y - 0.02, 4.455), (0.8, 0.4, 0.03), 'snow', bevel=False)


def build_lift(pal, ao):
    # line segment: one tower mid-span, both cables across the full 12 m, four chairs
    m = new(pal)
    m.box((0, 0, 0.15), (0.9, 0.9, 0.3), 'stone')
    m.box((0, 0, 0.315), (0.8, 0.8, 0.03), 'snow', bevel=False)
    m.cyl((0, 0, 0.24), 0.3, 0.2, 6.31, 'lift', seg=8, bevel=False)
    m.box((0, 0, 6.6), (2.8, 0.26, 0.24), 'lift', bevel=False)
    m.box((0, 0, 6.735), (2.7, 0.2, 0.03), 'snow', bevel=False)
    for sx in (-1, 1):
        m.box((sx * CABLE_X, 0, 6.38), (0.12, 0.9, 0.2), 'steel', bevel=False)
        for y in (-0.3, 0.3):
            m.cyl((sx * CABLE_X - 0.08, y, CABLE_Z + 0.06), 0.1, 0.1, 0.06, 'gunmetal', seg=8, rot=(0, 90, 0), bevel=False)
    for z in range(1, 6):
        m.box((0.24, 0.0, z * 1.0 + 0.5), (0.06, 0.34, 0.04), 'steel', bevel=False)
    m.box((0, 0, 5.2), (0.7, 0.04, 0.6), 'paper', bevel=False)
    m.box((0, -0.025, 5.2), (0.5, 0.02, 0.12), 'red', bevel=False)
    for sx in (-1, 1):
        m.beam((sx * CABLE_X, -6.0, CABLE_Z), (sx * CABLE_X, 6.0, CABLE_Z), 0.05, 'gunmetal')
    for (x, y) in ((-CABLE_X, -3.6), (-CABLE_X, 2.6), (CABLE_X, -1.9), (CABLE_X, 4.3)):
        chair(m, x, y)
    MP.liftline(m, CABLE_X)
    finish('Landmark_LiftLine', m, ao, cols=[((0, 0, 1.5), (0.45, 0.45, 1.5))])
    # station: stone platform, A-frame legs, bullwheel under a snowy canopy, operator hut, parked chair
    m = new(pal)
    m.box((0, 0.1, 0.06), (4.8, 3.6, 0.12), 'stone', bevel=False)
    wy = -0.3
    for sx in (-1, 1):
        m.beam((sx * 1.95, 1.6, 0.12), (sx * 0.35, wy + 0.35, 6.75), 0.24, 'lift')
        m.beam((sx * 1.95, -1.45, 0.12), (sx * 0.35, wy - 0.25, 6.75), 0.2, 'lift')
    m.box((0, wy, 6.8), (1.2, 1.0, 0.3), 'lift', bevel=False)
    m.cyl((0, wy, 6.15), 0.18, 0.18, 0.55, 'steel', seg=8, bevel=False)
    m.cyl((0, wy, CABLE_Z - 0.12), CABLE_X + 0.06, CABLE_X + 0.06, 0.24, 'gunmetal', seg=16, bevel=False)
    m.cyl((0, wy, CABLE_Z - 0.13), CABLE_X - 0.1, CABLE_X - 0.1, 0.262, 'steel', seg=16, bevel=False, caps=True)
    for i in range(4):
        a = i * math.pi / 4
        zs = CABLE_Z + 0.14 + 0.006 * i   # crossing spokes at different heights
        m.beam((math.cos(a) * -0.95, wy + math.sin(a) * -0.95, zs), (math.cos(a) * 0.95, wy + math.sin(a) * 0.95, zs), 0.06, 'lift')
    for sx in (-1, 1):
        m.beam((sx * CABLE_X, wy, CABLE_Z), (sx * CABLE_X, -2.0, CABLE_Z), 0.05, 'gunmetal')
    # canopy
    for sgn in (-1, 1):
        prism(m, [(sgn * 2.1, 7.0), (sgn * 2.1, 7.14), (0, 7.9), (0, 7.76)], -1.75, 1.65, 'roof2', axis='y')
        prism(m, [(sgn * 2.0, 7.19), (sgn * 1.98, 7.29), (0, 8.03), (0, 7.92)], -1.7, 1.6, 'snow', axis='y')
    for sx in (-1, 1):
        for y in (-1.5, 1.4):
            m.beam((sx * 1.95, y, 6.85), (sx * 1.0, y, 7.45), 0.1, 'lift')
    m.box((0, -0.05, 7.1), (0.16, 3.2, 0.2), 'lift', bevel=False)
    # operator hut (centre back, between the legs)
    hx, hy = 0.0, 1.05
    m.box((hx, hy, 1.27), (1.4, 1.3, 2.3), 'log')
    m.box((hx + 0.72, hy, 1.55), (0.04, 0.9, 0.7), 'glow', bevel=False)
    m.box((hx, hy - 0.67, 1.55), (0.9, 0.04, 0.7), 'glow', bevel=False)
    m.box((hx, hy - 0.705, 1.55), (0.05, 0.03, 0.7), 'log2', bevel=False)
    m.box((hx, hy, 2.5), (1.6, 1.5, 0.16), 'roof2', bevel=False)
    m.box((hx, hy, 2.62), (1.5, 1.4, 0.09), 'snow', bevel=False)
    m.box((hx + 0.3, hy - 0.67, 2.08), (0.5, 0.04, 0.16), 'tangerine', bevel=False)
    chair(m, CABLE_X, -1.55)
    # loading ramp board and a stack of skis
    m.box((1.2, -1.0, 0.13), (1.6, 1.2, 0.02), 'plank', bevel=False)
    MP.liftstation(m)
    finish('Landmark_LiftStation', m, ao, cols=[((hx, hy, 1.3), (0.72, 0.68, 1.3)), ((-1.85, 1.5, 0.8), (0.2, 0.2, 0.8)),
                                                ((1.85, 1.5, 0.8), (0.2, 0.2, 0.8)), ((-1.85, -1.38, 0.8), (0.18, 0.18, 0.8)),
                                                ((1.85, -1.38, 0.8), (0.18, 0.18, 0.8))])


# ================================================================ gate, trail wall, exit hatch
def build_gate(pal, ao, bw, ht):
    m = new(pal)
    for sx in (-1, 1):
        x = sx * 1.72      # inner faces 3 cm proud of the neighbouring cells' planes
        m.box((x, 0, 0.25), (0.66, 0.62, 0.5), 'stone', bevel=False)
        m.box((x, 0, 2.05), (0.5, 0.46, 3.3), 'log2', bevel=False)
        m.box((x, 0, 1.0), (0.54, 0.5, 0.12), 'rope', bevel=False)
        for fy in (-1, 1):
            m.box((x, fy * 0.245, 3.35), (0.22, 0.03, 0.22), 'teal', bevel=False)
    fs = list(m.cyl((-2.35, 0, 3.92), 0.27, 0.27, 4.7, 'log', seg=8, rot=(0, 90, 0), bevel=False))
    paint(m, fs, lambda f: 'logend' if abs(f.normal.x) > 0.9 else 'log')
    # hazard band board under the header beam (amber / ink)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 3.53), (0.3, 0.3 + 0.004 * (k % 2), 0.24), 'amber' if k % 2 else 'ink', bevel=False)
    # little gable roof with snow over the header
    for sgn in (-1, 1):
        prism(m, [(sgn * 0.62, 3.95), (sgn * 0.62, 4.05), (0, 4.4), (0, 4.3)], -2.5, 2.5, 'roof', axis='x')
        prism(m, [(sgn * 0.56, 4.09), (sgn * 0.55, 4.17), (0, 4.49), (0, 4.425)], -2.45, 2.45, 'snow', axis='x')
    for sx in (-1, 1):
        for fy in (-1, 1):
            m.box((sx * 1.2, fy * 0.42, 3.775), (0.03, 0.03, 0.55), 'gunmetal', bevel=False)
            m.box((sx * 1.2, fy * 0.42, 3.38), (0.18, 0.18, 0.24), 'glow', bevel=False)
    MP.gateframe(m)
    finish('GateFrame', m, ao, bevel=bw)
    # roll-up shutter: log courses with iron straps, hazard band at the foot (one box outline overall)
    m = new(pal)
    H, n = 3.05, 8
    for i in range(n):
        z = 0.55 + (i + 0.5) * (H - 0.55) / n
        m.box((0, 0, z), (3.0, 0.16, (H - 0.55) / n - 0.04), 'log' if i % 2 else 'log2', bevel=False)
    for x in (-0.9, 0.9):
        m.box((x, 0, (H + 0.55) / 2), (0.1, 0.19, H - 0.6), 'gunmetal', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.16, 0.5), 'ink' if k % 2 else 'amber', bevel=False)
    MP.gateshutter(m)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, H / 2), (3.0, 0.2, H), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # trail walls: log palisade on a stone footing; 1 m run along Blender Y, 0.5 thick, inner face +X. Variants
    # (mixed in per module through theme.trail.variants): firewood stacked against it, a lantern on a bracket,
    # a snow drift with a pair of skis leaning on the logs.
    def palisade(m, heights=(2.28, 2.42, 2.34), blocks=True):
        m.box((0, 0, 0.2), (0.5, 1.0, 0.4), 'stone2', bevel=False)
        m.box((0, 0, 0.42), (0.54, 1.0, 0.04), 'snow', bevel=False)
        for k, (y, H, col) in enumerate(zip((-0.333, 0.0, 0.333), heights, ('log', 'log2', 'log'))):
            m.cyl((0, y, 0.3), 0.163, 0.163, H - 0.3, col, seg=7, bevel=False, caps=False)
            m.cyl((0, y, H), 0.163, 0.02, 0.26, 'log2', seg=7, bevel=False)
        m.box((0.19, 0, 1.25), (0.08, 1.0, 0.12), 'log2', bevel=False)
        m.box((-0.19, 0, 1.95), (0.08, 1.0, 0.12), 'log2', bevel=False)
        MP.palisade(m, blocks=blocks)
    m = new(pal)
    palisade(m)
    finish('TrailWall', m, ao)
    m = new(pal)                                   # firewood stack under a snow cap
    palisade(m, (2.36, 2.3, 2.44))
    for r, (n, z) in enumerate(((3, 0.58), (3, 0.86), (2, 1.14))):
        for i in range(n):
            y = -0.32 + i * 0.32 + (0.16 if r == 2 else 0.0)
            m.cyl((0.3, y, z), 0.13, 0.13, 0.32, 'log' if (i + r) % 2 else 'log2', seg=7, rot=(0, 90, 0), bevel=False)
            m.cyl((0.62, y, z), 0.09, 0.09, 0.006, 'logend', seg=7, rot=(0, 90, 0), bevel=False)
    m.box((0.46, 0.0, 1.31), (0.34, 0.7, 0.07), 'snow', bevel=False)
    finish('TrailWall_Wood', m, ao)
    m = new(pal)                                   # a lantern on an iron bracket
    palisade(m, (2.4, 2.32, 2.3))
    m.box((0.3, 0.0, 1.95), (0.2, 0.05, 0.05), 'gunmetal', bevel=False)
    m.box((0.38, 0.0, 1.76), (0.02, 0.02, 0.17), 'gunmetal', bevel=False)
    m.box((0.38, 0.0, 1.55), (0.22, 0.22, 0.26), 'glow', bevel=False)
    m.cyl((0.38, 0.0, 1.68), 0.17, 0.02, 0.14, 'gunmetal', seg=4, bevel=False, rot=(0, 0, 45))
    m.box((0.38, 0.0, 1.405), (0.24, 0.24, 0.03), 'gunmetal', bevel=False)
    finish('TrailWall_Lantern', m, ao)
    m = new(pal)                                   # a drift banked against the logs, skis leaning on them
    palisade(m, (2.32, 2.38, 2.28), blocks=False)
    m.sphere((0.3, 0.05, 0.38), 0.5, 'snow', seg=(8, 5), scale=(0.7, 1.05, 0.42))
    for k, (y, c) in enumerate(((-0.12, 'red'), (0.06, 'amber'))):
        m.box((0.38, y, 1.05), (0.05, 0.09, 1.9), c, rot=(0, -12 - 3 * k, 0), bevel=False)
    finish('TrailWall_Drift', m, ao)
    # exit hatch: round timber pad with teal centre and amber lamps
    m = new(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'stone', seg=20)
    m.cyl((0, 0, 0.12), 1.08, 1.08, 0.02, 'plank', seg=20, bevel=False)
    for k in range(-3, 4):
        m.box((k * 0.3, 0, 0.1415), (0.025, 2 * math.sqrt(1.0 - (k * 0.3) ** 2) * 0.95, 0.009), 'log2', bevel=False)
    m.cyl((0, 0, 0.13), 0.62, 0.62, 0.03, 'teal', seg=16, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.14, math.sin(a) * 1.14, 0.115), 0.07, 0.07, 0.055, 'amber', seg=6, bevel=False)
    finish('Hatch', m, ao, bevel=0.015)


# ================================================================ backdrop (outside the play area, fogged)
def build_backdrop(pal):
    for name, seed, H, R in (('Backdrop_PeakA', 301, 46, 34), ('Backdrop_PeakB', 307, 38, 30), ('Backdrop_PeakC', 311, 54, 38)):
        m = new(pal)
        rnd = random.Random(seed)

        def mcol(Hm):
            def fn(f):
                c, n = f.calc_center_median(), f.normal
                if c.z > Hm * 0.62 or (c.z > Hm * 0.38 and n.z > 0.62):
                    return 'farsnow'
                return 'far' if c.z > Hm * 0.18 else 'rock'
            return fn
        pts = []
        for i in range(9):
            a = (i + rnd.uniform(-0.25, 0.25)) / 9 * 2 * math.pi
            pts.append((math.cos(a) * R * rnd.uniform(0.85, 1.05), math.sin(a) * R * rnd.uniform(0.7, 0.95), 0.0))
        for i in range(7):
            a = (i + 0.5) / 7 * 2 * math.pi
            pts.append((math.cos(a) * R * rnd.uniform(0.38, 0.52), math.sin(a) * R * rnd.uniform(0.35, 0.5), H * rnd.uniform(0.4, 0.55)))
        for i in range(4):
            a = (i + 0.2) / 4 * 2 * math.pi
            pts.append((math.cos(a) * R * rnd.uniform(0.1, 0.2), math.sin(a) * R * rnd.uniform(0.1, 0.2), H * rnd.uniform(0.72, 0.85)))
        pts.append((rnd.uniform(-2, 2), rnd.uniform(-2, 2), H))
        hull(m, pts, mcol(H))
        for sx in (-1, 1):
            Hs = H * rnd.uniform(0.5, 0.7)
            cx = sx * R * rnd.uniform(0.55, 0.75)
            sp = []
            for i in range(7):
                a = (i + rnd.uniform(-0.2, 0.2)) / 7 * 2 * math.pi
                sp.append((cx + math.cos(a) * R * 0.55, rnd.uniform(-3, 3) + math.sin(a) * R * 0.45, 0.0))
            for i in range(5):
                a = (i + 0.5) / 5 * 2 * math.pi
                sp.append((cx + math.cos(a) * R * 0.2, math.sin(a) * R * 0.18, Hs * rnd.uniform(0.5, 0.65)))
            sp.append((cx + rnd.uniform(-2, 2), rnd.uniform(-2, 2), Hs))
            hull(m, sp, mcol(H))
        finish(name, m, False, hull_t=0.25)
    m = new(pal)
    rnd = random.Random(331)
    hull(m, [(math.cos(a) * 17, math.sin(a) * 8, 0.0) for a in [i * 0.7 for i in range(9)]] +
         [(math.cos(a) * 11, math.sin(a) * 5, 2.6) for a in [i * 0.9 + 0.3 for i in range(7)]],
         lambda f: 'snow' if f.normal.z > 0.5 else 'snow2')
    for i in range(15):
        x, y = rnd.uniform(-13.5, 13.5), rnd.uniform(-5, 5)
        MS.ragged_tree(m, star, rnd, x, y, rnd.uniform(6.5, 12.5))
    finish('Backdrop_Forest', m, False, hull_t=0.08)


# ================================================================ family build
def build_kit_mountains(ao):
    pal = Palette(FAM)
    bw, ht = CFG[FAM]
    build_cliffs(pal, ao)
    build_treeline(pal, ao)
    build_rocks(pal, ao)
    build_cover(pal, ao)
    build_trees(pal, ao)
    build_patches(pal, ao)
    build_decor(pal, ao)
    build_campfire(pal, ao)
    build_cabin(pal, ao)
    build_chalet(pal, ao)
    build_lookout(pal, ao)
    build_ropebridge(pal, ao)
    build_lift(pal, ao)
    build_gate(pal, ao, bw, ht)
    build_backdrop(pal)
    total = 0
    for n in sorted(TRIS):
        total += TRIS[n]
    print('kit-mountains: %d pieces, %d triangles (incl. outline hull)' % (len(TRIS), total))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:24]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-mountains'
BUILD = build_kit_mountains
