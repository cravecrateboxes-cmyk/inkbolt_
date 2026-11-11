"""INKBOLT kit-seabase ("Abyssal Station Thalassa", an underwater research station): palette and modelling helpers
shared by sb_struct.py, sb_dock.py, sb_lab.py and sb_back.py (the family module is fam_kit_seabase.py).

Look: cool steel and teal inside with yellow / orange safety accents -- blue-grey ribbed steel plating in the docking
and service level, white composite panels with a teal band in the research ring, the dark riveted outer hull seen
from the observation chambers, hazard yellow on every coaming, rail and edge, orange emergency lights. Glass is a
dark teal companion piece drawn additive (<Piece>_Glass, theme.glow), so the sea and the rooms behind it show through
with a teal sheen and white glints painted on the frames.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are 7.5 m (H) tall; ceiling tiles hang from their origin (the ceiling plane, the
layer's y); door openings 2.4 m wide, 2.7 m tall with a 0.3 m coaming. Wall modules run along Blender X (the placer
turns them); link runs (glass partitions, guard rails) are modelled along Blender Y (the run placer's 'full' module
runs along game Z at yaw 0); span prefabs (doors) run along Blender X. Flat detail is painted as single faces without
an outline shell (hull='none'); details stay >= 3 mm proud of what they sit on.
"""
import math

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull  # noqa: F401
import ib_text
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401  (generic painted-face helpers)

FAM = 'kit-seabase'
PFX = 'KIT_SEABASE_'
ib_lib.GLB[FAM] = 'fps-kit-seabase.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # service steel (8 - 15)
    ('steel', '#7D8E99'), ('steelL', '#A8B7C0'), ('steelD', '#4F5C66'), ('deck', '#3A4650'),
    ('plate', '#5D6B75'), ('rib', '#2F3B45'), ('steelB', '#62748A'), ('grate', '#46525C'),
    # research panels (16 - 20)
    ('panel', '#DDE5E9'), ('panelL', '#F0F4F6'), ('panelG', '#B8C5CC'), ('seam', '#97A7B0'), ('tealM', '#2BA79E'),
    # outer hull (21 - 23)
    ('hull', '#2D3A43'), ('hullD', '#1C262E'), ('rivet', '#56656E'),
    # teal accents (24 - 26)
    ('tealD', '#0D7A76'), ('tealL', '#6FE3D9'), ('cyan', '#3FE6F5'),
    # safety (27 - 31)
    ('hazY', '#F2C230'), ('orange', '#F07A22'), ('fireR', '#D63A2F'), ('redD', '#9C2620'), ('hazK', '#23262B'),
    # glass, light (32 - 37)
    ('glassT', '#123A44'), ('glint', '#E6FAFF'), ('glassE', '#3D7F8E'), ('lamp', '#FFF3D0'), ('lampC', '#DDFBFF'),
    ('beamG', '#173E46'),
    # water, seabed, samples (38 - 46)
    ('deep', '#06222A'), ('murk', '#56704B'), ('murkD', '#34493A'), ('sedim', '#5F5848'), ('sedimL', '#7F7461'),
    ('rock', '#3A4547'), ('rockL', '#56625F'), ('rockD', '#252D30'), ('core', '#8A7659'),
    # screens (47 - 51)
    ('screen', '#0C2630'), ('scrC', '#3BD8F0'), ('scrG', '#5BE38F'), ('scrO', '#FF9F3A'), ('scrB', '#2F7BEA'),
    # materials (52 - 63)
    ('rubber', '#22262B'), ('chrome', '#D6DEE3'), ('brass', '#C9A04A'), ('copper', '#C77A45'), ('fabric', '#33496E'),
    ('subY', '#F5B82E'), ('cable', '#2A2E35'), ('crate', '#5B7F8E'), ('crateO', '#E07B2A'), ('canvas', '#8C8A5E'),
    ('canvasD', '#6B6A47'), ('foam', '#C9D4D0'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

TRIS = {}
HT = 0.02
H = 7.5          # walls
DW = 2.4         # door opening width
DH = 2.7         # door opening height
SILL = 0.3       # door coaming (walkable)
DECK = 3.2       # dock gallery / hub mezzanine top
WATER = 0.22     # flood water surface (drawn by the theme)


class SM(PM):
    """PM with a transform stack (push / pop: offset and turn about Z), rotated boxes and raw quad surfaces"""

    def __init__(self, pal):
        super().__init__(pal)
        self.stack = []

    def push(self, x, y, deg=0.0, z=0.0):
        self.stack.append(self.parent)
        self.parent = self.parent @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')

    def pop(self):
        self.parent = self.stack.pop()

    def bxr(self, cx, cy, cz, sx, sy, sz, c, rot=(0, 0, 0), hull='full'):
        self.cur = hull
        f = self.box((cx, cy, cz), (sx, sy, sz), c, rot=rot, bevel=False)
        self.cur = 'full'
        return f

    def surf(self, rows, color, hull='full', closed_u=False):
        """a quad surface through a grid of points rows[i][j] (one shape); normals recalculated outward-ish"""
        bm = self.bm
        P = self.parent
        V = [[bm.verts.new(P @ Vector(p)) for p in row] for row in rows]
        faces = []
        nu = len(rows[0])
        for i in range(len(rows) - 1):
            for j in range(nu if closed_u else nu - 1):
                j2 = (j + 1) % nu
                a, b, c, d = V[i][j], V[i][j2], V[i + 1][j2], V[i + 1][j]
                if len({a, b, c, d}) < 4:
                    vs = [v for k, v in enumerate((a, b, c, d)) if v not in (a, b, c, d)[:k]]
                    if len(vs) == 3:
                        faces.append(bm.faces.new(vs))
                    continue
                faces.append(bm.faces.new((a, b, c, d)))
        self.cur = hull
        self.nshape += 1
        mi = self.pal.index(color)
        for f in faces:
            f[self.shape] = self.nshape
            f.material_index = mi
            f.normal_update()
        if hull != 'full':
            self.hmode[self.nshape] = hull
        self.cur = 'full'
        return faces

    def tube(self, pts, r, color, seg=8, hull='full', caps=True):
        """a round tube along a polyline of 3D points (one shape)"""
        bm = self.bm
        P = self.parent
        rings = []
        n = len(pts)
        for i, p in enumerate(pts):
            a = Vector(pts[max(0, i - 1)])
            b = Vector(pts[min(n - 1, i + 1)])
            t = (b - a).normalized()
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            u = t.cross(up).normalized()
            v = t.cross(u).normalized()
            ring = []
            for k in range(seg):
                ang = k / seg * 2 * math.pi
                q = Vector(p) + (u * math.cos(ang) + v * math.sin(ang)) * r
                ring.append(bm.verts.new(P @ q))
            rings.append(ring)
        faces = []
        for i in range(n - 1):
            A, B2 = rings[i], rings[i + 1]
            for k in range(seg):
                faces.append(bm.faces.new((A[k], A[(k + 1) % seg], B2[(k + 1) % seg], B2[k])))
        if caps:
            faces.append(bm.faces.new(list(reversed(rings[0]))))
            faces.append(bm.faces.new(rings[-1]))
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        self.cur = hull
        self.nshape += 1
        mi = self.pal.index(color)
        for f in faces:
            f[self.shape] = self.nshape
            f.material_index = mi
        if hull != 'full':
            self.hmode[self.nshape] = hull
        self.cur = 'full'
        return faces


def new(pal):
    return SM(pal)


def make(name, m, ao, bevel=0.0, cols=None, hull=HT):
    full = PFX + name
    obj = build_object(full, m, bevel, hull, ao=ao)
    post_hull(obj, m.hmode)
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
    """a glow / glass companion: no outline shell at all (drawn unlit or additive by the engine)"""
    full = PFX + name
    obj = build_object(full, m, 0.0, 0.0, ao=False)
    strip_hull(obj)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return obj


# ---------------------------------------------------------------- lettering
def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw)


def text_up(m, word, cap, z, xc, yc, c, font='display', maxw=None, flip=False):
    ib_text.draw(m, word, xc, yc, z, cap, c, face='upr' if flip else 'up', font=font, valign='m', maxw=maxw)


# ---------------------------------------------------------------- shapes
def ring(m, x, y, z, r0, r1, c, seg=16, a0=0.0, a1=2 * math.pi, normal=(0, 0, 1), axis='z'):
    """flat annulus (painted, no outline) in the plane normal to `axis` through (x, y, z)"""
    for i in range(seg):
        p, q = a0 + (a1 - a0) * i / seg, a0 + (a1 - a0) * (i + 1) / seg
        pts = []
        for (r, a) in ((r0, p), (r1, p), (r1, q), (r0, q)):
            u, v = math.cos(a) * r, math.sin(a) * r
            pts.append((x + u, y + v, z) if axis == 'z' else (x + u, y, z + v) if axis == 'y' else (x, y + u, z + v))
        poly(m, pts, c, normal)


def leds(m, x0, x1, y, z, n, colors, s=0.022, face=-1):
    """a row of n square LEDs on a -Y (face -1) or +Y (face 1) plane at y between x0 and x1 at height z"""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        (fq if face < 0 else bq)(m, x - s / 2, x + s / 2, y, z - s / 2, z + s / 2, colors[i % len(colors)])


def hazard(m, x0, x1, y, z0, z1, n, face=-1, ca='hazY', cb_='hazK'):
    """yellow / black slanted hazard bands painted on a -Y (face -1) or +Y plane at y"""
    (fq if face < 0 else bq)(m, x0, x1, y, z0, z1, ca)
    w = (x1 - x0) / n
    h = z1 - z0
    d = face * 0.003
    for i in range(0, n, 2):
        a = x0 + i * w
        pts = [(max(x0, a), y + d, z0), (min(x1, a + w), y + d, z0), (min(x1, a + w + 0.5 * h), y + d, z1), (max(x0, a + 0.5 * h), y + d, z1)]
        if pts[1][0] - pts[0][0] > 1e-3 and pts[2][0] - pts[3][0] > 1e-3:
            poly(m, pts, cb_, (0, face, 0))


def hazard_up(m, x0, x1, y0, y1, z, n, ca='hazY', cb_='hazK', along='x'):
    """hazard bands painted on an upward plane (a coaming top, a curb)"""
    uq(m, x0, x1, y0, y1, z, ca)
    if along == 'x':
        w = (x1 - x0) / n
        for i in range(0, n, 2):
            a = x0 + i * w
            b = min(x1, a + w)
            s = (y1 - y0) * 0.6
            pts = [(a, y0, z + 0.003), (b, y0, z + 0.003), (min(x1, b + s), y1, z + 0.003), (min(x1, a + s), y1, z + 0.003)]
            if pts[1][0] > pts[0][0] + 1e-3 and pts[2][0] > pts[3][0] + 1e-3:
                poly(m, pts, cb_, (0, 0, 1))
    else:
        w = (y1 - y0) / n
        for i in range(0, n, 2):
            a = y0 + i * w
            b = min(y1, a + w)
            s = (x1 - x0) * 0.6
            pts = [(x0, a, z + 0.003), (x0, b, z + 0.003), (x1, min(y1, b + s), z + 0.003), (x1, min(y1, a + s), z + 0.003)]
            if pts[1][1] > pts[0][1] + 1e-3 and pts[2][1] > pts[3][1] + 1e-3:
                poly(m, pts, cb_, (0, 0, 1))


def wheel(m, x, y, z, r, c='fireR', axis='y', spokes=4):
    """a valve handwheel: the rim (one closed tube), two crossing spokes of different gauges, the hub; facing -Y
    (axis 'y') or up (axis 'z')"""
    def at(a, rr):
        return (x + math.cos(a) * rr, y, z + math.sin(a) * rr) if axis == 'y' else (x + math.cos(a) * rr, y + math.sin(a) * rr, z)
    n = 8
    pts = [at(i / n * 2 * math.pi, r) for i in range(n)]
    m.tube(pts + [pts[0]], 0.026, c, seg=4, caps=False)
    for k, rad in ((0, 0.018), (1, 0.013)):
        a = k * math.pi / 2 + 0.4
        m.tube([at(a, r), at(a + math.pi, r)], rad, c, seg=4, hull='none', caps=False)
    if axis == 'y':
        m.cy((x, y + 0.04, z), 0.05, 0.05, 0.1, 'steelD', seg=8, rot=(90, 0, 0))
    else:
        m.cy((x, y, z - 0.05), 0.05, 0.05, 0.1, 'steelD', seg=8)


def gauge(m, x, y, z, r=0.07):
    """a round pressure gauge on a -Y plane at y"""
    m.cy((x, y, z), r, r, 0.04, 'chrome', seg=10, rot=(90, 0, 0))
    pts = [(x + math.cos(i / 10 * 2 * math.pi) * r * 0.82, y - 0.043, z + math.sin(i / 10 * 2 * math.pi) * r * 0.82) for i in range(10)]
    poly(m, pts, 'paper', (0, -1, 0))
    poly(m, [(x - 0.005, y - 0.046, z), (x + 0.005, y - 0.046, z), (x + r * 0.6, y - 0.046, z + r * 0.45)], 'fireR', (0, -1, 0))
