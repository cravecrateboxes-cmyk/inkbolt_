"""INKBOLT kit-datacenter ("Helix Vault", a hyperscale data center with a secret R&D wing): palette and modelling
helpers shared by dc_struct.py, dc_hall.py and dc_lab.py (the family module is fam_kit_datacenter.py).

Look: clean and cool -- white wall panels, graphite cabinets and trim, teal / cyan light accents, a dark open
ceiling with LED strips and yellow fibre trays. Racks blink (the theme's glow companions: <Piece>_LED pieces modelled
without an outline shell, drawn unlit by the engine and blinked in phase groups by the theme).

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are 6 m (H) tall under a 6 m ceiling; door openings 2.4 m wide, 2.7 m tall.
Ceiling fittings hang from their origin (the ceiling plane, layer y = 6). Flat detail is painted as single faces
without an outline shell (PM hull='none'); details stay >= 3 mm proud of what they sit on.
"""
import math

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull
import ib_text
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401  (generic painted-face helpers)

FAM = 'kit-datacenter'
PFX = 'KIT_DATACENTER_'
ib_lib.GLB[FAM] = 'fps-kit-datacenter.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # walls, floor (8 - 17)
    ('wallW', '#F2F5F7'), ('wallL', '#E1E7EC'), ('wallG', '#C8D1D9'), ('joint', '#A9B5C0'),
    ('tile', '#D9E0E6'), ('tileD', '#B8C3CD'), ('perf', '#7F8C99'), ('ceil', '#2B3038'),
    ('graph', '#3A4048'), ('graphD', '#23282E'),
    # metal (18 - 23)
    ('graphL', '#5A636D'), ('steel', '#8E99A5'), ('steelL', '#C2CBD4'), ('chrome', '#E4E9EE'),
    ('steelD', '#646E79'), ('black', '#17191D'),
    # light accents and LEDs (24 - 33)
    ('tealD', '#0C8F86'), ('cyan', '#3FE6F5'), ('cyanL', '#BDF7FF'), ('glow', '#F0FDFF'),
    ('blue', '#2F7BEA'), ('blueL', '#8ED2FF'), ('ledG', '#4BE37A'), ('ledB', '#45B4FF'),
    ('ledW', '#FFFFFF'), ('holo', '#3BD8F0'),
    # cables (34 - 40)
    ('cabY', '#FFCF2E'), ('cabB', '#2F6CD3'), ('cabR', '#D8392F'), ('cabO', '#F2862E'),
    ('cabP', '#8A6CD8'), ('cabG', '#3C9E57'), ('cabK', '#2A2E35'),
    # safety, glass, mesh (41 - 47)
    ('fireR', '#D63A2F'), ('hazY', '#F2C230'), ('glass', '#9FD6E8'), ('glassL', '#DDF4FB'),
    ('glassD', '#5D9EBB'), ('mesh', '#7C8792'), ('frost', '#EAF8FC'),
    # screens (48 - 53)
    ('screen', '#0E2233'), ('scrB', '#1F5F92'), ('scrC', '#36D2EA'), ('scrG', '#5BE38F'),
    ('scrO', '#FF9F3A'), ('scrP', '#B07CFF'),
    # rooms, labs (54 - 63)
    ('wood', '#B98A5B'), ('woodD', '#8A6342'), ('carpet', '#4B5664'), ('chair', '#2F3540'),
    ('cardb', '#C99B60'), ('gold', '#E8B54A'), ('copper', '#D27A45'), ('mech', '#EEF1F4'),
    ('mechD', '#A5B0BB'), ('field', '#2EA8E8'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

TRIS = {}
HT = 0.02
H = 6.0          # walls / ceiling
DH = 2.7         # door opening height
DW = 2.4         # door opening width


class DM(PM):
    """PM with a transform stack (push / pop: offset and turn about Z) and rotated boxes (bxr)"""

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


def new(pal):
    return DM(pal)


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


def make_glow(name, m, ao=False):
    """a glow companion: no outline shell at all (drawn unlit by the engine)"""
    full = PFX + name
    obj = build_object(full, m, 0.0, 0.0, ao=False)
    strip_hull(obj)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return obj


# ---------------------------------------------------------------- lettering (Bebas Neue by default: condensed tech caps, light on triangles)
def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None):
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw)


def text_side(m, word, cap, x, yc, z0, c, face, font='display', maxw=None):
    ib_text.draw(m, word, x, yc, z0, cap, c, face=face, font=font, maxw=maxw)


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


def torus(m, cx, cy, cz, R, r, c, seg=16, sides=6, axis='y', a0=0.0, a1=2 * math.pi, hull='full'):
    """torus (or an arc of one) as one outlined shape; axis: the ring's axis ('y': standing, facing -Y; 'z': lying)"""
    bm = m.bm
    P = m.parent
    closed = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = seg if closed else seg + 1
    rows = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / seg
        ca, sa = math.cos(a), math.sin(a)
        row = []
        for k in range(sides):
            b = k / sides * 2 * math.pi
            rr = R + r * math.cos(b)
            h = r * math.sin(b)
            if axis == 'y':
                p = (cx + ca * rr, cy + h, cz + sa * rr)
            elif axis == 'z':
                p = (cx + ca * rr, cy + sa * rr, cz + h)
            else:
                p = (cx + h, cy + ca * rr, cz + sa * rr)
            row.append(bm.verts.new(P @ Vector(p)))
        rows.append(row)
    faces = []
    for i in range(seg if closed else seg):
        A, Bb = rows[i], rows[(i + 1) % n]
        for k in range(sides):
            faces.append(bm.faces.new((A[k], Bb[k], Bb[(k + 1) % sides], A[(k + 1) % sides])))
    if not closed:
        for row in (rows[0], rows[-1]):
            faces.append(bm.faces.new(row))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.cur = hull
    m.nshape += 1
    mi = m.pal.index(c)
    for f in faces:
        f[m.shape] = m.nshape
        f.material_index = mi
    if hull != 'full':
        m.hmode[m.nshape] = hull
    m.cur = 'full'
    return faces


def leds(m, x0, x1, y, z, n, colors, s=0.022, face=-1):
    """a row of n square LEDs on a -Y (face -1) or +Y (face 1) plane at y between x0 and x1 at height z"""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        (fq if face < 0 else bq)(m, x - s / 2, x + s / 2, y, z - s / 2, z + s / 2, colors[i % len(colors)])


def chevrons(m, x0, x1, y, z0, z1, n, back=False, ca='hazY', cb_='graphD'):
    w = (x1 - x0) / n
    for i in range(n):
        (bq if back else fq)(m, x0 + i * w, x0 + (i + 1) * w, y, z0, z1, ca if i % 2 else cb_)


def slats(m, x0, x1, y, z0, z1, n, c, face=-1, gap=0.4):
    """n horizontal louvre lines across a plane (grilles, vents)"""
    h = (z1 - z0) / n
    for i in range(n):
        a = z0 + i * h
        (fq if face < 0 else bq)(m, x0, x1, y, a, a + h * (1 - gap), c)


# ---------------------------------------------------------------- modelled detail (tactical look, Stage 11)
# Local equivalents of kit_base's detail helpers for this kit's DM / PM model. Same rules: parts are hull='none'
# (no outline shell), stand >= 3 mm proud of the face they sit on and start 3 mm inside it, horizontal runs stop 5 mm
# short of a piece's sides. `yf` is the face plane, `s` its facing (-1: toward -Y, +1: toward +Y).
EMB = 0.003


def dbx(m, x0, x1, yf, d, z0, z1, c, s=-1):
    """a detail box d proud of the plane y = yf (embedded EMB inside it); back face and unseen floor / ceiling faces dropped"""
    cull = ('k' if s < 0 else 'f') + ('b' if z0 < 0.3 else '') + ('t' if z1 > 5.0 else '')
    y0, y1 = (yf - d, yf + EMB) if s < 0 else (yf - EMB, yf + d)
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def dbolts(m, xs, z, yf, c, d=0.016, sz=0.022, s=-1):
    for x in xs:
        dbx(m, x - sz / 2, x + sz / 2, yf, d, z - sz / 2, z + sz / 2, c, s)


def drails(m, zlow, zhigh, c, x=0.495, yf=-0.5, d=0.02, h=0.04):
    """skirting cap and picture rail across a wall module (zlow: top of the skirt; zhigh: underside of the top band)"""
    dbx(m, -x, x, yf, d, zlow, zlow + h, c)
    dbx(m, -x, x, yf, d, zhigh - h, zhigh, c)


def dconduit(m, x0, x1, z, yf, c, clip_c, r=0.02, clips=(), s=-1):
    """a horizontal conduit on stand-off clips"""
    y = yf - s * (r + 0.006)
    m.cy((x0, y, z), r, r, x1 - x0, c, seg=6, rot=(0, 90, 0), hull='none', caps=False)
    for x in clips:
        dbx(m, x - 0.015, x + 0.015, yf, 2 * r + 0.012, z - r - 0.008, z + r + 0.008, clip_c, s)


def djbox(m, x, z, yf, c, lid_c, s=-1, w=0.2, h=0.26, d=0.08):
    dbx(m, x - w / 2, x + w / 2, yf, d, z - h / 2, z + h / 2, c, s)
    dbx(m, x - w / 2 + 0.02, x + w / 2 - 0.02, yf, d + 0.005, z - h / 2 + 0.02, z + h / 2 - 0.02, lid_c, s)
