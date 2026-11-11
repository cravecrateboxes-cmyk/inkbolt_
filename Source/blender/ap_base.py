"""INKBOLT kit-airport ("Meridian International", a made-up airport; the home base of the made-up Skylark Air):
palette and modelling helpers shared by ap_struct.py (walls, gates, trail, roof, decks, stairs, floor marks),
ap_term.py (the terminal: check-in, the automated security checkpoint, gates, duty free, the lounge, the cafe deck),
ap_hangar.py (the maintenance hangar: the airliner on jacks and its work platforms, the engine stand, ground support
vehicles, tool cribs) and ap_back.py (outside: the parked airliner with its jet bridge, distant aircraft, the control
tower, apron masts). The family module is fam_kit_airport.py.

Look: a bright modern terminal -- white composite panels over pale stone cladding, a 14 m white ceiling, a full
height glass curtain wall (open glazing with glints, dark mullions every 3 m), timber accents, black-and-yellow
wayfinding signs; the security hall in grey and white machines with blue trim and emissive status lights (glow
companions, theme.glow); the hangar in corrugated steel with a light epoxy floor and yellow safety lines.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are H = 14 m tall (the terminal ceiling and the hangar roof plane); ceiling and roof
pieces hang from their origin (layer y = 14). Runs placed with `links` (glass screens, belt barriers, rails) are
modelled along Blender Y; prefab runs (`sequence: 'run'`, conveyors) along Blender X. Flat detail is painted as single
faces without an outline shell; details stay >= 3 mm proud of what they sit on.
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

FAM = 'kit-airport'
PFX = 'KIT_AIRPORT_'
ib_lib.GLB[FAM] = 'fps-kit-airport.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # structure (8 - 24)
    ('wallW', '#F2F1EC'), ('wallL', '#DCDCD6'), ('joint', '#BDBEB8'), ('stone', '#CFC8BC'), ('stoneD', '#A69E91'),
    ('conc', '#BDBAB2'), ('concD', '#8F8C85'), ('ceil', '#E9E8E2'), ('wood', '#C68A4E'), ('woodD', '#8F5A2E'),
    ('steel', '#8E99A5'), ('steelD', '#56606B'), ('chrome', '#D6DCE3'), ('black', '#202228'), ('mull', '#2E3440'),
    ('glass', '#9FD0E6'), ('glassL', '#E3F5FC'),
    # brands (25 - 29): Skylark Air blue / light blue / yellow, Meridian navy / coral
    ('sky', '#2C7BD9'), ('skyL', '#7FC0F0'), ('sun', '#F5C431'), ('navy', '#1D2B4F'), ('coral', '#E8664A'),
    # goods (30 - 33): what the models use; the theme repaints them per copy (34 - 37 and the brand colours)
    ('gA', '#D8392F'), ('gB', '#2F7BEA'), ('gC', '#F2C230'), ('gD', '#3C9E57'),
    ('pPurple', '#8A5CD8'), ('pPink', '#E86BA0'), ('pLime', '#A7D94A'), ('pOrange', '#F28A2E'),
    # lounge (38 - 42)
    ('carpet', '#3B4A6B'), ('leather', '#A65A2E'), ('brass', '#C9A24A'), ('leaf', '#4FA845'), ('leafD', '#2F7A3A'),
    # screens and lights (43 - 47)
    ('screen', '#14263C'), ('scrB', '#2E8CEB'), ('scrG', '#33D17A'), ('scrR', '#FF4B3A'), ('lightW', '#FFF8E2'),
    # hangar, apron, vehicles (48 - 56)
    ('epoxy', '#B9BEC0'), ('asph', '#5E6064'), ('grass', '#86AE55'), ('tire', '#2A2A2E'), ('rubber', '#3A3D44'),
    ('cream', '#F4E9D2'), ('fab', '#5A6E8C'), ('orange', '#F07A22'), ('belly', '#C7CCD2'),
    # more (57 - 60)
    ('corr', '#C9D1D6'), ('corrD', '#A3AEB5'), ('tug', '#F2B21B'), ('fabD', '#3F4E66'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
GOODS = ['gA', 'gB', 'gC', 'gD']

TRIS = {}
HT = 0.02
H = 14.0         # walls / terminal ceiling / hangar roof plane
DECK = 4.5       # terminal mezzanine deck top
DOCK = 2.6       # hangar work platform (first level); the tail deck stands at 2 * DOCK
DROP = 3.6       # the service corridor's drop ceiling


class APM(PM):
    """PM whose boxes accept their extents in either order (a mirrored detail written as s * a .. s * b)"""

    def bx(self, x0, x1, y0, y1, z0, z1, color, hull='full', bevel=False, cull=''):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        return PM.bx(self, x0, x1, y0, y1, z0, z1, color, hull=hull, bevel=bevel, cull=cull)


def new(pal):
    return APM(pal)


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
    """a glow companion: no outline shell (drawn unlit by the engine, theme.glow)"""
    full = PFX + name
    obj = build_object(full, m, 0.0, 0.0, ao=False)
    strip_hull(obj)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return obj


# ---------------------------------------------------------------- lettering
def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c'):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    return ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw, align=align)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c'):
    return ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw, align=align)


def text_side(m, word, cap, x, yc, z0, c, face, font='display', maxw=None):
    return ib_text.draw(m, word, x, yc, z0, cap, c, face=face, font=font, maxw=maxw)


def text_up(m, word, cap, z, xc, yc, c, font='display', maxw=None, flip=False):
    return ib_text.draw(m, word, xc, yc, z, cap, c, face='upr' if flip else 'up', font=font, valign='m', maxw=maxw)


def sign2(m, word, cap, y0, y1, xc, z0, c, font='display', maxw=None):
    """the same word on both faces of a board (front plane y0 facing -Y, back plane y1 facing +Y)"""
    text_front(m, word, cap, y0, xc, z0, c, font=font, maxw=maxw)
    text_back(m, word, cap, y1, xc, z0, c, font=font, maxw=maxw)


# ---------------------------------------------------------------- shapes
def glint(m, x, y, z, h, w=0.16, c='glassL', face=-1):
    """two slanted glass glints on a plane at y (open glazing: the glass itself is not drawn)"""
    for k, (dx, ww) in enumerate(((0.0, w), (w * 1.3, w * 0.45))):
        pts = [(x + dx, y, z), (x + dx + ww, y, z), (x + dx + ww + h * 0.45, y, z + h), (x + dx + h * 0.45, y, z + h)]
        poly(m, pts, c, (0, face, 0))


def glint_x(m, x, y, z, h, w=0.16, c='glassL', face=1):
    """glints on a plane at x (facing +X or -X)"""
    for k, (dy, ww) in enumerate(((0.0, w), (w * 1.3, w * 0.45))):
        pts = [(x, y + dy, z), (x, y + dy + ww, z), (x, y + dy + ww + h * 0.45, z + h), (x, y + dy + h * 0.45, z + h)]
        poly(m, pts, c, (face, 0, 0))


def ring(m, x, y, z, r0, r1, c, seg=16):
    """flat annulus facing up (painted)"""
    for i in range(seg):
        p, q = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        poly(m, [(x + math.cos(p) * r0, y + math.sin(p) * r0, z), (x + math.cos(p) * r1, y + math.sin(p) * r1, z),
                 (x + math.cos(q) * r1, y + math.sin(q) * r1, z), (x + math.cos(q) * r0, y + math.sin(q) * r0, z)], c, (0, 0, 1))


def vdisc(m, x, y, z, r, c, seg=12, face=-1):
    """a painted disc on a plane at y (facing -Y or +Y)"""
    pts = [(x + math.cos(2 * math.pi * i / seg) * r, y, z + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]
    return poly(m, pts, c, (0, face, 0))


def xdisc(m, x, y, z, r, c, seg=12, face=1):
    pts = [(x, y + math.cos(2 * math.pi * i / seg) * r, z + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]
    return poly(m, pts, c, (face, 0, 0))


def cyl_y(m, x, y0, y1, z, r, c, seg=10, hull='full', r1=None, caps=True):
    """a cylinder along Blender Y from y0 to y1, axis at (x, z)"""
    r1 = r if r1 is None else r1
    return m.cy((x, y0, z), r, r1, y1 - y0, c, seg=seg, rot=(-90, 0, 0), hull=hull, caps=caps)


def cyl_x(m, x0, x1, y, z, r, c, seg=10, hull='full', r1=None, caps=True):
    r1 = r if r1 is None else r1
    return m.cy((x0, y, z), r, r1, x1 - x0, c, seg=seg, rot=(0, 90, 0), hull=hull, caps=caps)


def wheel(m, x, y, z, r, w, c='tire', hub='chrome', seg=10, axis='x'):
    """a wheel turning about X (axis 'x': rolls along Y) with a painted hub on its outer face (+X for x > 0)"""
    s = 1 if x >= 0 else -1
    cyl_x(m, x - w / 2, x + w / 2, y, z, r, c, seg=seg)
    xdisc(m, x + s * (w / 2 + 0.003), y, z, r * 0.5, hub, seg=8, face=s)


def loft(m, rings, c_of, seg=12, hull='full', a0=0.0):
    """a lofted body along Blender Y: rings = [(y, cx, cz, rx, rz), ...] (ellipse sections; rx = 0 closes to a point),
    face colour c_of(ring_index, seg_index, angle) -> palette name. One outlined shape (the fuselage, a nacelle)."""
    bm = m.bm
    P = m.parent
    vr = []
    for (y, cx, cz, rx, rz) in rings:
        if rx <= 1e-4:
            vr.append([bm.verts.new(P @ Vector((cx, y, cz)))])
            continue
        vr.append([bm.verts.new(P @ Vector((cx + math.cos(a0 + 2 * math.pi * i / seg) * rx, y, cz + math.sin(a0 + 2 * math.pi * i / seg) * rz)))
                   for i in range(seg)])
    faces = []
    for k in range(len(vr) - 1):
        a, b = vr[k], vr[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            ang = a0 + 2 * math.pi * (i + 0.5) / seg
            if len(a) == 1:
                f = bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                f = bm.faces.new((a[i], b[0], a[j]))
            else:
                f = bm.faces.new((a[i], b[i], b[j], a[j]))
            f.material_index = m.pal.index(c_of(k, i, ang))
            faces.append(f)
    for end in (vr[0], vr[-1]):
        if len(end) > 1:
            f = bm.faces.new(end)
            f.material_index = m.pal.index(c_of(0, 0, 0))
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return faces


def slab(m, pts, z0, z1, c, hull='full'):
    """a convex polygon (Blender XY) extruded from z0 to z1: wings, fins, ramps seen from above"""
    bm = m.bm
    P = m.parent
    a = [bm.verts.new(P @ Vector((x, y, z0))) for (x, y) in pts]
    b = [bm.verts.new(P @ Vector((x, y, z1))) for (x, y) in pts]
    fs = [bm.faces.new(a), bm.faces.new(b)]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    mi = m.pal.index(c)
    m.nshape += 1
    for f in fs:
        f.material_index = mi
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return fs


def skin(m, quads, c, hull='full'):
    """a closed solid from explicit quads/tris of shared corner points: verts = list of xyz, faces = index tuples"""
    verts, faces = quads
    bm = m.bm
    P = m.parent
    vs = [bm.verts.new(P @ Vector(v)) for v in verts]
    fs = []
    for f in faces:
        ff = bm.faces.new([vs[i] for i in f])
        fs.append(ff)
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    m.nshape += 1
    for f in fs:
        f.material_index = m.pal.index(c if isinstance(c, str) else c(f))
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return fs


def wedge(m, x0, x1, y0, y1, z0, z1, zb0, zb1, c, hull='full'):
    """a box whose top slopes along Y: top at z1 (y0 end) .. zb1 (y1 end); bottom z0 .. zb0 (a ramp, a fin)"""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, zb0), (x0, y1, zb0), (x0, y0, z1), (x1, y0, z1), (x1, y1, zb1), (x0, y1, zb1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return skin(m, (v, f), c, hull=hull)


def leds(m, x0, x1, y, z, n, colors, s=0.03, face=-1):
    """a row of n square status LEDs on a plane at y"""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        (fq if face < 0 else bq)(m, x - s / 2, x + s / 2, y, z - s / 2, z + s / 2, colors[i % len(colors)])


def chevrons(m, x0, x1, y, z0, z1, n, ca='sun', cb_='black', face=-1):
    """hazard stripes (painted slanted bands) on a plane at y"""
    w = (x1 - x0) / n
    (fq if face < 0 else bq)(m, x0, x1, y, z0, z1, cb_)
    for i in range(n):
        if i % 2:
            continue
        a = x0 + i * w
        pts = [(a, y + face * 0.004, z0), (min(x1, a + w), y + face * 0.004, z0), (min(x1, a + w + (z1 - z0) * 0.5), y + face * 0.004, z1), (min(x1, a + (z1 - z0) * 0.5), y + face * 0.004, z1)]
        poly(m, pts, ca, (0, face, 0))
