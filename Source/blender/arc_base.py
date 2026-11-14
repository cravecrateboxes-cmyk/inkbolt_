"""INKBOLT kit-arctic ("Kolvane Station K-7", an abandoned polar research station buried under ice and snow): palette and
modelling helpers shared by arc_struct.py (walls in seven finishes, doors, gate, shaft trail, hatch, ceilings, floor
finishes, stairs, rails), arc_surface.py (the trench and the station's upper modules: snowcat, fuel, sleds, masts,
buried huts, the collapsed radar dome, mess hall, bunks, comms) and arc_labs.py (the deep labs: core archive, cryo lab,
generator hall, vault, the ice cavern and the frozen relic). The family module is fam_kit_arctic.py.

Look: cold and clean -- white and blue-white firn and glacier ice with old snow lines, steel and white insulated panels,
emergency-orange accents (doors, the snowcat, stripes, beacons), dead screens, frost everywhere.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; wall modules are H = 12 m tall (the trench, the ice caves and the shaft are 12 m deep);
the station's upper modules have their ceiling at 3.7 m (CS), the deep labs at 4.4 m (CL). Ceiling fittings hang from
their origin. Stairs rise toward Blender +Y (game north) at yaw 0. Flat detail is painted as single faces without an
outline shell (PM hull='none'); details stay >= 3 mm proud of what they sit on.
"""
import math
import random

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401
import ib_text

FAM = 'kit-arctic'
PFX = 'KIT_ARCTIC_'
ib_lib.GLB[FAM] = 'fps-kit-arctic.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # snow and firn (8 - 13)
    ('snowW', '#F5F9FC'), ('snowL', '#E4EDF4'), ('snowS', '#CBDAE6'), ('snowD', '#AEC2D3'),
    ('firn', '#D6E6EF'), ('line', '#8E9DAD'),
    # glacier ice (14 - 19)
    ('iceL', '#DDF2FA'), ('ice', '#AEDDF0'), ('iceM', '#82C4E2'), ('iceD', '#5199C2'), ('iceK', '#2E6B97'), ('iceN', '#1D4A70'),
    # steel (20 - 25)
    ('steelL', '#C6CED6'), ('steel', '#8F9AA6'), ('steelD', '#5E6974'), ('steelK', '#3A424C'), ('black', '#1A1E24'), ('galv', '#A9B3BC'),
    # station panels and floors (26 - 33)
    ('panelW', '#E8ECEF'), ('panelG', '#C7CFD6'), ('panelB', '#93A3B2'), ('panelK', '#5D6F80'),
    ('vinyl', '#7D8B98'), ('vinylD', '#66737F'), ('tileW', '#D9DEE2'), ('tileB', '#4E6278'),
    # orange and safety (34 - 39)
    ('orange', '#F2701E'), ('orangeD', '#B9501A'), ('yel', '#F2C230'), ('redE', '#D63A2F'), ('green', '#3C9E57'), ('blueP', '#2F6CD3'),
    # interiors (40 - 47)
    ('wood', '#B98A5B'), ('woodD', '#8A6342'), ('fabric', '#4E6E8E'), ('fabricR', '#A8443A'),
    ('mattress', '#D7D2C4'), ('paperY', '#EDE6D2'), ('chair', '#2F3540'), ('cardb', '#C99B60'),
    # lights, screens, glass (48 - 56)
    ('lamp', '#FFF3D6'), ('lampC', '#D6F6FF'), ('glowC', '#6FE3FF'), ('scrDead', '#1C2630'), ('scr', '#123049'),
    ('scrG', '#5BE38F'), ('glass', '#9FD6E8'), ('glassD', '#5D9EBB'), ('frost', '#EEF9FD'),
    # the relic and the cores (57 - 63)
    ('relK', '#262A35'), ('relD', '#3A4052'), ('relM', '#566079'), ('relG', '#4FE8D2'),
    ('core', '#E9E4D8'), ('coreB', '#C2DCE8'), ('tube', '#DDEAF1'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

TRIS = {}
HT = 0.02
H = 12.0         # wall modules, trench depth, cave and shaft ceilings
CS = 3.7         # station ceiling (zone 1 upper modules)
CL = 4.4         # lab ceiling (zone 2)
DH = 2.7         # door opening height
WALK = 4.5       # catwalks (generator hall, cavern scaffold)
HIGH = 7.0       # the high platform at the relic
ROOF = 2.2       # walkable roof of the buried module in the trench
NAME = 'KOLVANE'


class AM(PM):
    """PM with rotated boxes (bxr: centre, size, XYZ rotation in degrees)"""

    def bxr(self, cx, cy, cz, sx, sy, sz, c, rot=(0, 0, 0), hull='full'):
        self.cur = hull
        f = self.box((cx, cy, cz), (sx, sy, sz), c, rot=rot, bevel=False)
        self.cur = 'full'
        return f


def new(pal):
    return AM(pal)


def make(name, m, ao, bevel=0.0, cols=None, side=0.45):
    full = PFX + name
    obj = build_object(full, m, bevel, HT, ao=ao)
    post_hull(obj, m.hmode, side)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, col in enumerate(cols or []):
        c, hlf = col[0], col[1]
        walk = len(col) > 2 and col[2]
        e = bpy.data.objects.new('%s_%sCOL%d' % (full, 'W' if walk else '', i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def make_glow(name, m):
    """a glow companion: no outline shell (drawn unlit by the engine)"""
    full = PFX + name
    obj = build_object(full, m, 0.0, 0.0, ao=False)
    strip_hull(obj)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return obj


def at(m, x=0.0, y=0.0, z=0.0, deg=0.0):
    """set the model's parent transform (translate, then turn deg about Z); at(m) resets it"""
    m.parent = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


def tube(m, a, b, r, c, seg=8, hull='full', caps=True):
    """cylinder from point a to point b"""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    old = m.parent
    m.parent = old @ Matrix.Translation(a) @ q.to_matrix().to_4x4()
    m.cy((0, 0, 0), r, r, d.length, c, seg=seg, hull=hull, caps=caps)
    m.parent = old


def hullp(m, pts, color, hull='full'):
    """convex hull of points (piece frame) as one shape; color: palette name or fn(face) -> name"""
    P = m.parent
    vs = [m.bm.verts.new(P @ Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(m.bm, input=vs)
    junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(m.bm, geom=junk, context='VERTS')
    fs = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    bmesh.ops.recalc_face_normals(m.bm, faces=fs)
    m.nshape += 1
    for f in fs:
        f[m.shape] = m.nshape
        f.normal_update()
        f.material_index = m.pal.index(color(f) if callable(color) else color)
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return fs


def lump(m, rnd, cx, cy, rx, ry, h, z0=0.0, color='snowL', n=7, top=3, hull='full', flat_top=False):
    """faceted snow / ice lump (convex hull of a jittered point ring)"""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.85, 1.0)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k, z0))
    for i in range(n):
        a = (i + 0.5 + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        k = rnd.uniform(0.6, 0.85)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k, z0 + h * rnd.uniform(0.45, 0.7)))
    for i in range(top):
        a = rnd.uniform(0, 2 * math.pi)
        k = rnd.uniform(0.0, 0.4)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k, z0 + h * (1.0 if flat_top else rnd.uniform(0.85, 1.0))))
    return hullp(m, pts, color, hull)


def icicles(m, rnd, x0, x1, y, z, n, lmax=0.5, c='iceL', depth=0.06, hull='none'):
    """a fringe of n icicles hanging from z between x0 and x1 at y (thin pyramids)"""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rnd.uniform(0.2, 0.8)) / n
        L = rnd.uniform(0.25, 1.0) * lmax
        w = rnd.uniform(0.03, 0.06)
        hullp(m, [(x - w, y - depth / 2, z), (x + w, y - depth / 2, z), (x + w, y + depth / 2, z), (x - w, y + depth / 2, z),
                  (x + rnd.uniform(-0.01, 0.01), y, z - L)], c, hull)


def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw)


def text_side(m, word, cap, x, yc, z0, c, face, font='display', maxw=None):
    ib_text.draw(m, word, x, yc, z0, cap, c, face=face, font=font, maxw=maxw)


def text_up(m, word, cap, z, xc, yc, c, font='display', maxw=None, flip=False):
    ib_text.draw(m, word, xc, yc, z, cap, c, face='upr' if flip else 'up', font=font, valign='m', maxw=maxw)


def chevrons(m, x0, x1, y, z0, z1, n, back=False, ca='orange', cb_='black'):
    w = (x1 - x0) / n
    for i in range(n):
        (bq if back else fq)(m, x0 + i * w, x0 + (i + 1) * w, y, z0, z1, ca if i % 2 else cb_)


def _foot(m, x, y, z0, c):
    """a base flange under a guard-rail post (arc_detail.rail_foot)"""
    import arc_detail
    arc_detail.rail_foot(m, x, y, z0, c)


def rail_x(m, x0, x1, y, z0, h=1.05, c='orange', post=1.0, toe=True):
    """guard rail along X at y: posts, top and knee rail, toe board"""
    L = x1 - x0
    m.bx(x0, x1, y - 0.03, y + 0.03, z0 + h - 0.05, z0 + h, c)
    m.bx(x0, x1, y - 0.02, y + 0.02, z0 + h * 0.52, z0 + h * 0.52 + 0.04, c, hull='none')
    if toe:
        m.bx(x0, x1, y - 0.01, y + 0.01, z0, z0 + 0.12, c, hull='none', cull='b')
    n = max(1, int(round(L / post)))
    for k in range(n + 1):
        px = min(max(x0 + k * L / n, x0 + 0.03), x1 - 0.03)
        m.bx(px - 0.025, px + 0.025, y - 0.025, y + 0.025, z0, z0 + h - 0.05, c, hull='none', cull='bt')
        _foot(m, px, y, z0, c)


def rail_y(m, x, y0, y1, z0, h=1.05, c='orange', post=1.0, toe=True):
    L = y1 - y0
    m.bx(x - 0.03, x + 0.03, y0, y1, z0 + h - 0.05, z0 + h, c)
    m.bx(x - 0.02, x + 0.02, y0, y1, z0 + h * 0.52, z0 + h * 0.52 + 0.04, c, hull='none')
    if toe:
        m.bx(x - 0.01, x + 0.01, y0, y1, z0, z0 + 0.12, c, hull='none', cull='b')
    n = max(1, int(round(L / post)))
    for k in range(n + 1):
        py = min(max(y0 + k * L / n, y0 + 0.03), y1 - 0.03)
        m.bx(x - 0.025, x + 0.025, py - 0.025, py + 0.025, z0, z0 + h - 0.05, c, hull='none', cull='bt')
        _foot(m, x, py, z0, c)


def frost_spots(m, rnd, x0, x1, z0, z1, y, n, face=-1, c='frost'):
    """irregular frost patches painted on a -Y (face -1) or +Y plane"""
    done = []
    for _ in range(n * 4):
        if len(done) >= n:
            break
        cx, cz = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        r = rnd.uniform(0.06, 0.18)
        if any(math.hypot(cx - px, cz - pz) < r + pr + 0.01 for px, pz, pr in done):
            continue
        done.append((cx, cz, r))
        k = rnd.randint(5, 7)
        pts = []
        for i in range(k):
            a = i / k * 2 * math.pi
            rr = r * rnd.uniform(0.6, 1.0)
            pts.append((min(x1, max(x0, cx + math.cos(a) * rr)), y, min(z1, max(z0, cz + math.sin(a) * rr))))
        poly(m, pts, c, (0, face, 0))


def RND(seed):
    return random.Random(seed)
