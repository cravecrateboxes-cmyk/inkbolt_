"""INKBOLT kit-megastore ("BULKBARN Warehouse Club", the inside of a huge warehouse store): palette and modelling
helpers shared by ms_struct.py, ms_racks.py, ms_dept.py and ms_back.py (the family module is fam_kit_megastore.py).

Look: a bright warehouse club -- light grey painted block walls with a BULKBARN blue / red band and pale corrugated
cladding above, a polished concrete floor, a light grey steel deck roof 10 m up carried by open-web joists, blue
pallet-rack uprights with orange beams, shrink-wrapped pallets and cardboard everywhere. Product colours are four
'goods' cells (gA - gD) the theme repaints per placed copy (symbol option `paint`) from a dozen product colours, so
no two rack bays carry the same stock.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are 10 m (H) tall under the 10 m roof deck; ceiling fittings hang from their origin
(the roof plane, layer y = 10). Racks are modelled along Blender X (the run direction of the placer: a [3, 2] block's
local X runs along its line of cells), their two shelf faces at Y = -1 / +1. Flat detail is painted as single faces
without an outline shell (PM hull='none'); details stay >= 3 mm proud of what they sit on.
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

FAM = 'kit-megastore'
PFX = 'KIT_MEGASTORE_'
ib_lib.GLB[FAM] = 'fps-kit-megastore.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # walls, roof (8 - 16)
    ('wallW', '#EEF0EC'), ('wallL', '#DADFDB'), ('joint', '#C2C8C4'), ('brand', '#2C63B8'),
    ('brandR', '#D8392F'), ('corr', '#CDD3D6'), ('corrD', '#A9B2B8'), ('ceil', '#A7AFB6'), ('joist', '#5E6873'),
    # floor (17 - 18)
    ('conc', '#C9C6BE'), ('concD', '#9F9B92'),
    # racking (19 - 22)
    ('rackO', '#F07A22'), ('rackB', '#2A5DB0'), ('rackG', '#B9C2CB'), ('wire', '#7E8892'),
    # pallets, wrap, cardboard (23 - 29)
    ('wood', '#C48E55'), ('woodD', '#8E6238'), ('wrap', '#DCE9EF'), ('wrapS', '#B3CBD8'),
    ('card', '#C99B60'), ('cardD', '#A67845'), ('cardL', '#E0BE8A'),
    # goods (30 - 33): what the models use; the theme repaints them from the product colours (34 - 42)
    ('gA', '#D8392F'), ('gB', '#2F7BEA'), ('gC', '#F2C230'), ('gD', '#3C9E57'),
    ('pOrange', '#F28A2E'), ('pPurple', '#8A5CD8'), ('pWhite', '#F4F2EA'), ('pBlack', '#2D2F36'),
    ('pPink', '#E86BA0'), ('pTeal', '#29B5B0'), ('pBrown', '#8E5C3D'), ('pLime', '#A7D94A'), ('pSky', '#7FC4E8'),
    # metal (43 - 46)
    ('steel', '#8E99A5'), ('steelD', '#56606B'), ('chrome', '#D6DCE3'), ('black', '#202228'),
    # safety, lights, screens (47 - 54)
    ('hazY', '#F7C531'), ('lightW', '#FFF8E2'), ('cool', '#E8F8FF'), ('screen', '#14263C'),
    ('scrB', '#2E8CEB'), ('scrC', '#4FDCF2'), ('scrO', '#FF9F3A'), ('exitG', '#25B35E'),
    # glass, leaves, counters, plastics (55 - 63)
    ('glass', '#9FD6E8'), ('glassL', '#DDF4FB'), ('leaf', '#4FA845'), ('cream', '#F4E9D2'),
    ('woodL', '#D9B07C'), ('grey', '#6E7681'), ('navy', '#1E2A44'), ('mint', '#BDEFD8'), ('rose', '#F6C7D3'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
GOODS = ['gA', 'gB', 'gC', 'gD']

TRIS = {}
HT = 0.02
H = 10.0         # walls / roof deck
DECK = 3.5       # mezzanine deck top (stockroom office)


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
def text_front(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c'):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y-', font=font, maxw=maxw, align=align)


def text_back(m, word, cap, y, xc, z0, c, font='display', maxw=None, align='c'):
    ib_text.draw(m, word, xc, y, z0, cap, c, face='y+', font=font, maxw=maxw, align=align)


def text_side(m, word, cap, x, yc, z0, c, face, font='display', maxw=None):
    ib_text.draw(m, word, x, yc, z0, cap, c, face=face, font=font, maxw=maxw)


def text_up(m, word, cap, z, xc, yc, c, font='display', maxw=None, flip=False):
    ib_text.draw(m, word, xc, yc, z, cap, c, face='upr' if flip else 'up', font=font, valign='m', maxw=maxw)


def sign2(m, word, cap, y0, y1, xc, z0, c, font='display', maxw=None):
    """the same word on both faces of a hanging board (front plane y0 facing -Y, back plane y1 facing +Y)"""
    text_front(m, word, cap, y0, xc, z0, c, font=font, maxw=maxw)
    text_back(m, word, cap, y1, xc, z0, c, font=font, maxw=maxw)


# ---------------------------------------------------------------- shapes
def ring(m, x, y, z, r0, r1, c, seg=16):
    """flat annulus facing up (painted)"""
    for i in range(seg):
        p, q = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        poly(m, [(x + math.cos(p) * r0, y + math.sin(p) * r0, z), (x + math.cos(p) * r1, y + math.sin(p) * r1, z),
                 (x + math.cos(q) * r1, y + math.sin(q) * r1, z), (x + math.cos(q) * r0, y + math.sin(q) * r0, z)], c, (0, 0, 1))


def case(m, x0, x1, y0, y1, z0, z1, c, cull='b', tape=None, side=-1, label=None):
    """a carton / case: an outlined box (bottom never seen) with an optional tape strip over the top and a painted
    label on its -Y (side -1) or +Y (side 1) face"""
    m.bx(x0, x1, y0, y1, z0, z1, c, cull=cull)
    if tape:
        w = min(0.05, (x1 - x0) * 0.2)
        xm = (x0 + x1) / 2
        uq(m, xm - w, xm + w, y0, y1, z1 + 0.003, tape)
    if label:
        lw, lh = (x1 - x0) * 0.3, (z1 - z0) * 0.28
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        if side < 0:
            fq(m, xm - lw, xm + lw, y0 - 0.003, zm - lh, zm + lh, label)
        else:
            bq(m, xm - lw, xm + lw, y1 + 0.003, zm - lh, zm + lh, label)


def pallet(m, x0, x1, y0, y1, z0=0.0, c='wood', cd='woodD'):
    """a wooden pallet 0.14 m tall: deck boards on three stringer blocks (the top of the deck at z0 + 0.14)"""
    m.bx(x0, x1, y0, y1, z0 + 0.105, z0 + 0.14, c, cull='')
    w = (x1 - x0)
    for k in range(3):
        a = x0 + 0.02 + k * (w - 0.14) / 2
        m.bx(a, a + 0.1, y0 + 0.02, y1 - 0.02, z0, z0 + 0.105, cd, cull='bt', hull='none')
    # deck board seams painted on the front and the top (light)
    for k in range(1, 5):
        a = x0 + k * w / 5
        uq(m, a - 0.006, a + 0.006, y0, y1, z0 + 0.143, cd)


def load(m, x0, x1, y0, y1, z0, z1, c, wrap=True, rnd=None, face=(-1, 1), bands=2):
    """a pallet load: one block of stock (colour c) with shrink-wrap bands painted across the visible faces"""
    m.bx(x0, x1, y0, y1, z0, z1, c, cull='b')
    if not wrap:
        return
    hgt = z1 - z0
    for k in range(bands):
        za = z0 + hgt * (0.18 + 0.5 * k)
        zb = za + hgt * 0.22
        for s in face:
            if s < 0:
                fq(m, x0, x1, y0 - 0.003, za, zb, 'wrap')
            else:
                bq(m, x0, x1, y1 + 0.003, za, zb, 'wrap')
        lq(m, x0 - 0.003, y0, y1, za, zb, 'wrapS')
        rq(m, x1 + 0.003, y0, y1, za, zb, 'wrapS')
    uq(m, x0 + 0.04, x1 - 0.04, y0 + 0.04, y1 - 0.04, z1 + 0.003, 'wrap')


def stack(m, rnd, x0, x1, y0, y1, z0, ztop, colors, face=-1, nx=None, maxh=0.5):
    """cases of mixed size stacked between x0 and x1 (rows from the front face), each a colour from `colors`,
    labels on the face toward the aisle (face -1: -Y, 1: +Y); returns nothing. Keeps 1 cm between neighbours."""
    nx = nx or max(1, int((x1 - x0) / rnd.uniform(0.38, 0.6)))
    xs = [x0]
    for k in range(nx - 1):
        xs.append(x0 + (x1 - x0) * (k + 1) / nx + rnd.uniform(-0.06, 0.06))
    xs.append(x1)
    for k in range(nx):
        a, b = xs[k] + 0.006, xs[k + 1] - 0.006
        z = z0
        while z < ztop - 0.12:
            hgt = min(ztop - z, rnd.uniform(0.18, maxh))
            if hgt < 0.12:
                break
            d0 = y0 + (rnd.uniform(0.0, 0.12) if face > 0 else 0.0)
            d1 = y1 - (rnd.uniform(0.0, 0.12) if face < 0 else 0.0)
            c = rnd.choice(colors)
            lab = rnd.choice(['pWhite', 'cardL', 'paper', None]) if c not in ('card', 'cardD', 'cardL') else rnd.choice(['gA', 'gB', None])
            case(m, a, b, d0, d1, z, z + hgt - 0.005, c, label=lab, side=face)
            z += hgt
            if rnd.random() < 0.25:
                break


def shelf_row(m, rnd, x0, x1, y0, y1, z0, z1, colors, face=-1, nb=3, col_w=(0.24, 0.42), labels=('paper', 'pWhite', 'cardL', 'pBlack')):
    """a shelf of goods as few blocks: nb blocks of mixed width / height between x0 and x1 (y0..y1 deep), each a
    colour from `colors`, with one painted label per product column on the face toward the aisle (face -1: -Y)"""
    cuts = sorted(rnd.uniform(0.2, 0.8) for _ in range(nb - 1))
    xs = [x0] + [x0 + (x1 - x0) * c for c in cuts] + [x1]
    cull = 'bk' if face < 0 else 'bf'
    for k in range(nb):
        a, b = xs[k] + 0.008, xs[k + 1] - 0.008
        if b - a < 0.12:
            continue
        top = z0 + (z1 - z0) * rnd.uniform(0.72, 1.0)
        c = rnd.choice(colors)
        dy = rnd.uniform(0.0, 0.06)
        ya, yb = (y0 + dy, y1) if face < 0 else (y0, y1 - dy)
        m.bx(a, b, ya, yb, z0, top, c, cull=cull)
        lab = rnd.choice(labels)
        n = max(1, int((b - a) / rnd.uniform(*col_w)))
        for j in range(n):
            xa = a + (b - a) * (j + 0.18) / n
            xb = a + (b - a) * (j + 0.82) / n
            za, zb = z0 + (top - z0) * 0.42, z0 + (top - z0) * 0.6
            if face < 0:
                fq(m, xa, xb, ya - 0.003, za, zb, lab)
            else:
                bq(m, xa, xb, yb + 0.003, za, zb, lab)
