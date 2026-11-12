"""INKBOLT kit-icecream ("Scoops & Cream", a huge ice cream shop): palette and modelling helpers shared by
ic_struct.py, ic_parlour.py and ic_kitchen.py (the family module is fam_kit_icecream.py).

Look: a bright, playful parlour -- strawberry-pink walls over a mint wainscot with a chocolate-drip band, cream
coffered ceilings with scalloped pendant lamps, a pink / cream checker floor in the seating areas, chunky counters in
pastel enamel with glass-front dipping cabinets full of tubs in dozens of flavour colours, waffle-cone brown trims.
Behind the STAFF ONLY door: the creamery -- white tiled walls with a mint stripe, terracotta quarry-tile floor,
stainless churns, mix tanks, blast freezers, a walk-in freezer of insulated panels, pallets of cone and cup cartons,
and the pink PARTY ROOM up on the mezzanine.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are H (7 m) tall under the ceiling; ceiling fittings hang from their origin (the
ceiling plane, layer y = H). Prefab runs are modelled along Blender X (a [w, d] block's local X runs along its w
cells); link runs (glass, panels, rails, belts: `links` symbols) are modelled along Blender Y, half modules from the
cell centre toward -Y. Flat detail is painted as single faces without an outline shell (PM hull='none'); details stay
>= 3 mm proud of what they sit on.
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull
import ib_text
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401  (generic painted-face helpers)
from ap_base import cyl_x, cyl_y  # noqa: F401
from arc_base import tube, hullp  # noqa: F401
from dc_base import torus  # noqa: F401

FAM = 'kit-icecream'
PFX = 'KIT_ICECREAM_'
ib_lib.GLB[FAM] = 'fps-kit-icecream.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # parlour walls and trims (8 - 21)
    ('wallP', '#F9C6D4'), ('wallC', '#FFF3DE'), ('wallM', '#BDEFD8'), ('pinkD', '#EA5C93'), ('mintD', '#3DBE9A'),
    ('choc', '#6E4130'), ('chocD', '#47281C'), ('waf', '#E5AA5A'), ('wafD', '#B57731'), ('wafL', '#F6D69C'),
    ('cherry', '#D9223C'), ('lemon', '#FFE36A'), ('sky', '#8DD5F5'), ('lilac', '#C6A5EE'),
    # metal, glass, floor (22 - 29)
    ('orange', '#FF9B42'), ('steel', '#AFB9C3'), ('steelD', '#5E6975'), ('chrome', '#E3E9EF'), ('black', '#26232C'),
    ('glass', '#BDE7F3'), ('glassL', '#E6F7FC'), ('tileW', '#FBF5EA'),
    # flavours (30 - 45)
    ('vanilla', '#FFF0C2'), ('strawb', '#FFA2BC'), ('chocF', '#8C5637'), ('mintF', '#A5F1CE'), ('pista', '#BCD983'),
    ('blueb', '#8A96E6'), ('mango', '#FFB448'), ('rasp', '#E64A86'), ('cookie', '#E4DCCF'), ('caramel', '#D8944A'),
    ('grape', '#A982DA'), ('bubble', '#84DCF4'), ('coffee', '#B07D5E'), ('lime', '#B5E65A'), ('peach', '#FFC59C'),
    ('cotton', '#F6B6E4'),
    # lights and screens (46 - 50)
    ('lightW', '#FFF8E0'), ('neonP', '#FF5CA8'), ('neonB', '#5CE2FF'), ('screen', '#1F2A44'), ('exitG', '#25B35E'),
    # kitchen, cartons, plants (51 - 62)
    ('quarry', '#C9603F'), ('quarryD', '#9E432A'), ('frost', '#E6F5FF'), ('panel', '#EEF2F5'), ('hazY', '#F7C531'),
    ('card', '#C99B60'), ('cardD', '#A67845'), ('cardL', '#E3C28E'), ('wood', '#B98353'), ('woodL', '#E2BB86'),
    ('leaf', '#4FA845'), ('glassA', '#0C171C'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
FLAVOURS = ['vanilla', 'strawb', 'chocF', 'mintF', 'pista', 'blueb', 'mango', 'rasp', 'cookie', 'caramel', 'grape',
            'bubble', 'coffee', 'lime', 'peach', 'cotton', 'lemon', 'cherry']

TRIS = {}
HT = 0.02
H = 7.0          # walls / ceiling
DECK = 3.5       # mezzanine deck top (the party room)
UNDER = DECK - 0.4   # deck underside (the engine's deck slab is 0.4 thick)
TER = 1.2        # the parlour's raised terrace (a solid deck slab)
CT = 1.05        # counter top height (customer side)


def new(pal):
    return PM(pal)


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
def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c', shadow=None):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    return ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw, align=align, shadow=shadow)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c', shadow=None):
    return ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw, align=align, shadow=shadow)


def text_side(m, word, cap, x, yc, z0, c, face, font='display', maxw=None):
    return ib_text.draw(m, word, x, yc, z0, cap, c, face=face, font=font, maxw=maxw)


def text_up(m, word, cap, z, xc, yc, c, font='display', maxw=None, flip=False):
    return ib_text.draw(m, word, xc, yc, z, cap, c, face='upr' if flip else 'up', font=font, valign='m', maxw=maxw)


# ---------------------------------------------------------------- shapes
def ring(m, x, y, z, r0, r1, c, seg=16):
    """flat annulus facing up (painted)"""
    for i in range(seg):
        p, q = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        poly(m, [(x + math.cos(p) * r0, y + math.sin(p) * r0, z), (x + math.cos(p) * r1, y + math.sin(p) * r1, z),
                 (x + math.cos(q) * r1, y + math.sin(q) * r1, z), (x + math.cos(q) * r0, y + math.sin(q) * r0, z)], c, (0, 0, 1))


def fdisc(m, x, y, z, r, c, seg=12):
    """a painted disc on a -Y facing plane at y (a dot on a front)"""
    pts = [(x + math.cos(2 * math.pi * i / seg) * r, y, z + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]
    poly(m, pts, c, (0, -1, 0))


def scoop(m, x, y, z, r, c, seg=(8, 5), drip=None):
    """a scoop of ice cream: a squashed sphere sitting on z with a frilly lip ring (and an optional drip colour)"""
    m.sp((x, y, z + r * 0.78), r, c, seg=seg, scale=(1.0, 1.0, 0.86))
    m.cy((x, y, z + r * 0.12), r * 1.06, r * 0.98, r * 0.22, c, seg=seg[0], hull='none')
    if drip:
        for k in range(3):
            a = 2 * math.pi * (k + 0.3) / 3
            m.bx(x + math.cos(a) * r * 0.9 - 0.012, x + math.cos(a) * r * 0.9 + 0.012, y + math.sin(a) * r * 0.9 - 0.012,
                 y + math.sin(a) * r * 0.9 + 0.012, z - r * 0.25, z + r * 0.2, drip, hull='none', cull='t')


def cone(m, x, y, z_tip, z_top, r, c='waf', seg=8, grid=True, lip=True):
    """a waffle cone standing on its tip at z_tip, opening radius r at z_top; a painted criss-cross and a rolled lip"""
    m.cy((x, y, z_tip), 0.0, r, z_top - z_tip, c, seg=seg)
    if lip:
        m.cy((x, y, z_top - 0.002), r * 1.08, r * 1.08, min(0.05, (z_top - z_tip) * 0.12), 'wafL', seg=seg, hull='none')


def tub(m, x, y, z, r, h, c, rim='chrome', top=True, scooped=True, mix=None):
    """a 5 l dipping tub sunk in a cabinet: a steel rim disc, the ice cream surface on it (an optional scooped mound
    and mix-in flecks)"""
    disc(m, x, y, z - 0.004, r, rim, seg=8)
    disc(m, x, y, z, r * 0.88, c, seg=8)
    if scooped:
        m.sp((x + r * 0.2, y - r * 0.1, z), r * 0.45, c, seg=(6, 2), scale=(1.0, 0.8, 0.55), hull='none')
    if mix:
        for k in range(2):
            a = 1.3 + k * 3.0
            rr = r * 0.5
            uq(m, x + math.cos(a) * rr - 0.014, x + math.cos(a) * rr + 0.014, y + math.sin(a) * rr - 0.014,
               y + math.sin(a) * rr + 0.014, z + 0.003, mix)


def stripes_front(m, x0, x1, y, z0, z1, cols, n):
    """n vertical stripes alternating through `cols` on a -Y face (a candy-stripe panel)"""
    w = (x1 - x0) / n
    for k in range(n):
        fq(m, x0 + k * w, x0 + (k + 1) * w, y, z0, z1, cols[k % len(cols)])


def scallops(m, x0, x1, y, z, r, c, n=None, face=-1):
    """a row of half-disc scallops hanging down from z on a Y-facing plane (an awning / cake frill)"""
    n = n or max(1, int(round((x1 - x0) / (2 * r))))
    w = (x1 - x0) / n
    nrm = (0, -1, 0) if face < 0 else (0, 1, 0)
    for k in range(n):
        cx = x0 + (k + 0.5) * w
        pts = [(cx + math.cos(math.pi + math.pi * i / 4) * w / 2, y, z + math.sin(math.pi + math.pi * i / 4) * r) for i in range(5)]
        poly(m, pts[::-1] if face > 0 else pts, c, nrm)


def drip_band(m, x0, x1, y, z, c, n=None, depth=0.18, face=-1, seed=1):
    """a chocolate-drip band on a Y-facing plane: a strip down from z with rounded drips of mixed length"""
    rnd = random.Random(seed)
    n = n or max(2, int((x1 - x0) / 0.25))
    w = (x1 - x0) / n
    nrm = (0, -1, 0) if face < 0 else (0, 1, 0)
    ff = fq if face < 0 else bq
    ff(m, x0, x1, y, z - 0.06, z, c)
    for k in range(n):
        cx = x0 + (k + 0.5) * w
        L = depth * rnd.uniform(0.25, 1.0)
        hw = w * 0.32
        pts = [(cx - hw, y, z - 0.058), (cx - hw, y, z - 0.06 - L)]
        for i in range(1, 6):
            a = math.pi + math.pi * i / 6
            pts.append((cx + math.cos(a) * hw, y, z - 0.06 - L + math.sin(a) * hw))
        pts += [(cx + hw, y, z - 0.06 - L), (cx + hw, y, z - 0.058)]
        dy = -0.003 if face < 0 else 0.003
        pts = [(p[0], p[1] + dy, p[2]) for p in pts]
        poly(m, pts if face < 0 else pts[::-1], c, nrm)


def cushion(m, x0, x1, y0, y1, z0, z1, c, piping=None):
    """an upholstered block: an outlined box (its ink outline traces the edge; `piping` is kept for the callers'
    colour intent and repainted with the upholstery by the theme)"""
    m.bx(x0, x1, y0, y1, z0, z1, c, cull='b')


def pillar(m, x, y, z0, z1, r, cols, seg=12):
    """a fluted round column: seg faces alternating through cols (candy stripes), one outlined shape"""
    bm, P = m.bm, m.parent
    lo = [bm.verts.new(P @ Vector((x + math.cos(2 * math.pi * (i + 0.5) / seg) * r, y + math.sin(2 * math.pi * (i + 0.5) / seg) * r, z0))) for i in range(seg)]
    hi = [bm.verts.new(P @ Vector((x + math.cos(2 * math.pi * (i + 0.5) / seg) * r, y + math.sin(2 * math.pi * (i + 0.5) / seg) * r, z1))) for i in range(seg)]
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        f.material_index = m.pal.index(cols[i % len(cols)])
        faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    for f in faces:
        f.normal_update()
        c = f.calc_center_median()
        if (c - P @ Vector((x, y, c.z))).dot(f.normal) < 0:
            f.normal_flip()
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape


def streaks(g, quad, n=2, w=0.07, c='steelD', off=0.0):
    """additive glass sheen: n slanted streaks across a quad [(p0), (p1), (p2), (p3)] (p0 -> p1 along the bottom,
    p3 -> p2 along the top), drawn both sides (the glass glow companion is double-sided)"""
    P = [Vector(q) for q in quad]
    nrm = (P[1] - P[0]).cross(P[3] - P[0]).normalized()
    for k in range(n):
        t0 = 0.18 + k * 0.32
        for (a, b) in ((t0, t0 + w), (t0 + w * 1.6, t0 + w * 2.0)):
            pts = []
            for (u, v) in ((a, 0.0), (b, 0.0), (b + 0.18, 1.0), (a + 0.18, 1.0)):
                u = min(1.0, u)
                bot = P[0].lerp(P[1], u)
                top = P[3].lerp(P[2], min(1.0, u))
                pts.append(tuple(bot.lerp(top, v) + nrm * off))
            poly(g, pts, c, tuple(nrm))
