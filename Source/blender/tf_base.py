"""INKBOLT kit-toyfactory ("Topsy Toyworks", a toy factory and its warehouse): palette and modelling helpers shared by
tf_struct.py, tf_lines.py, tf_giants.py and tf_store.py (the family module is fam_kit_toyfactory.py).

Look: a bright, clean toy plant -- cream painted block walls with the TOPSY red / blue band and white cladding up to a
12 m steel deck roof on open-web joists (skylights, high-bay lamps), a pale epoxy floor, machines in Topsy blue,
teal and machine white, belts in black rubber, toys in primary colours. The warehouse: grey block, a yellow bump rail,
blue pallet racks with orange beams full of printed toy cartons. Toy and carton colours are four 'goods' cells (gA - gD)
the theme repaints per placed copy (symbol option `paint`), so no two rack bays or toy piles look alike.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; walls are H = 12 m tall under the roof deck; ceiling fittings hang from their origin (the
roof plane, layer y = 12). Prefab runs (racks, belts) are modelled along Blender X, the run direction of the placer;
link runs (guard rails) are modelled along Blender Y. Flat detail is painted as single faces without an outline shell
(PM hull='none'); details stay >= 3 mm proud of what they sit on (ib_lib z-fight check).

Reuses the generic painted-face helpers of parking_base (fq / bq / uq / dq / lq / rq / poly / disc / cb), the PM
model of fam_kit_smallcity and the carton / pallet / load helpers of ms_base (their colour names are in this palette).
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
from ms_base import case, pallet, load, stack, shelf_row, ring  # noqa: F401  (carton / pallet helpers)

FAM = 'kit-toyfactory'
PFX = 'KIT_TOYFACTORY_'
ib_lib.GLB[FAM] = 'fps-kit-toyfactory.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # walls, roof (8 - 17)
    ('wallC', '#F3EBD8'), ('wallG', '#D5D9D6'), ('joint', '#C4BFB2'), ('clad', '#E9EEF1'), ('cladD', '#B9C3CA'),
    ('brandR', '#E5392F'), ('brandB', '#2D64D8'), ('hazY', '#F7C531'), ('ceil', '#AEB6BE'), ('joist', '#5E6873'),
    # floor (18 - 19)
    ('conc', '#C9C6BE'), ('concD', '#9F9B92'),
    # racking (20 - 22)
    ('rackO', '#F07A22'), ('rackB', '#2A5DB0'), ('wire', '#7E8892'),
    # pallets, wrap, cardboard (23 - 29)
    ('wood', '#C48E55'), ('woodD', '#8E6238'), ('wrap', '#DCE9EF'), ('wrapS', '#B3CBD8'),
    ('card', '#C99B60'), ('cardD', '#A67845'), ('cardL', '#E0BE8A'),
    # goods (30 - 33): what the models use; the theme repaints them from the toy colours (34 - 42)
    ('gA', '#E5392F'), ('gB', '#2D7BEA'), ('gC', '#F6C230'), ('gD', '#3DB35A'),
    ('pOrange', '#F28A2E'), ('pPurple', '#8A5CD8'), ('pWhite', '#F4F2EA'), ('pBlack', '#2D2F36'),
    ('pPink', '#F07AAE'), ('pTeal', '#29B5B0'), ('pBrown', '#A86E46'), ('pLime', '#A7D94A'), ('pSky', '#7FC4E8'),
    # metal (43 - 46)
    ('steel', '#8E99A5'), ('steelD', '#56606B'), ('chrome', '#D6DCE3'), ('black', '#202228'),
    # lights, screens, glass (47 - 55)
    ('lightW', '#FFF8E2'), ('cool', '#E8F8FF'), ('screen', '#14263C'), ('scrB', '#2E8CEB'), ('scrC', '#4FDCF2'),
    ('scrG', '#5BE38A'), ('exitG', '#25B35E'), ('glass', '#9FD6E8'), ('glassL', '#DDF4FB'),
    # machines, rubber, brass, trims (56 - 63)
    ('machB', '#3A6FC4'), ('machG', '#2E9C8A'), ('machW', '#E9E6DE'), ('rubber', '#2B2B30'), ('brass', '#D9A441'),
    ('grey', '#6E7681'), ('navy', '#1E2A44'), ('cream', '#F4E9D2'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
GOODS = ['gA', 'gB', 'gC', 'gD']
TOYC = GOODS + ['pOrange', 'pPurple', 'pPink', 'pTeal', 'pLime', 'pSky']

TRIS = {}
HT = 0.02
H = 12.0         # walls / roof deck
DECK = 3.5       # mezzanine deck top (pellet loft, dispatch mezzanine)
UNDER = DECK - 0.4
BELT = 0.86      # belt top (items ride here)


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


def make_item(name, m, ao):
    """a conveyor item (no collision; the line is cover)"""
    return make(name, m, ao)


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


# ---------------------------------------------------------------- transforms
class at:
    """with at(m, x, y, z, deg): model a sub-assembly in a moved / turned frame (Z-up, degrees about Z)"""

    def __init__(self, m, x=0.0, y=0.0, z=0.0, deg=0.0, rx=0.0, ry=0.0, s=1.0):
        self.m, self.T = m, (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')
                             @ Matrix.Rotation(math.radians(rx), 4, 'X') @ Matrix.Rotation(math.radians(ry), 4, 'Y')
                             @ Matrix.Diagonal(Vector((s, s, s, 1.0))))

    def __enter__(self):
        self.old = self.m.parent
        self.m.parent = self.old @ self.T
        return self.m

    def __exit__(self, *a):
        self.m.parent = self.old


# ---------------------------------------------------------------- shapes
def tube(m, a, b, r, c, seg=8, hull='full'):
    """a round pipe from point a to point b"""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    old = m.parent
    m.parent = old @ Matrix.Translation(a) @ q.to_matrix().to_4x4()
    m.cy((0, 0, 0), r, r, d.length, c, seg=seg, caps=False, hull=hull)
    m.parent = old


def stud_brick(m, x0, x1, y0, y1, z0, z1, c, nx=2, ny=2, stud=0.3, sh=None, seg=8, hull='full', cull='b'):
    """a building brick: a box with nx x ny round studs on top (stud radius from the pitch)"""
    m.bx(x0, x1, y0, y1, z0, z1, c, cull=cull, hull=hull)
    px, py = (x1 - x0) / nx, (y1 - y0) / ny
    r = min(px, py) * stud
    hs = sh if sh is not None else r * 0.7
    for i in range(nx):
        for j in range(ny):
            m.cy((x0 + (i + 0.5) * px, y0 + (j + 0.5) * py, z1), r, r, hs, c, seg=seg, hull=hull)


def duck(m, x, y, z, s, c='gC', beak='pOrange', deg=0.0):
    """a rubber duck toy (bath toy): body, head, flat beak, a tail tip -- a toy, no eyes (fewer segments when small)"""
    lo = s < 0.6
    with at(m, x, y, z, deg, s=s):
        m.sp((0, 0, 0.32), 0.42, c, seg=(7, 4) if lo else (10, 6), scale=(1.25, 1.0, 0.78))
        m.sp((0.3, 0, 0.82), 0.27, c, seg=(6, 4) if lo else (8, 6))
        m.bx(0.5, 0.72, -0.1, 0.1, 0.72, 0.8, beak, cull='', hull='none' if lo else 'full')
        if not lo:
            m.bx(-0.62, -0.42, -0.09, 0.09, 0.42, 0.62, c, cull='b')


def bear(m, x, y, z, s, c='pBrown', paw='cream', deg=0.0, seated=True, lod=None):
    """a plush teddy bear (a toy without a face): body, head, round ears, a muzzle patch, arms and legs (fewer
    segments and no outline on the small parts when small)"""
    lo = s < 0.6 if lod is None else lod == 0
    big, small = ((7, 4), (5, 3)) if lo else ((8, 5), (6, 4)) if lod == 1 else ((10, 6), (6, 4))
    hs = 'none' if lo else 'full'
    with at(m, x, y, z, deg, s=s):
        m.sp((0, 0, 0.42), 0.36, c, seg=big, scale=(1.0, 0.85, 1.1))
        m.sp((0, 0, 1.0), 0.3, c, seg=big)
        for sx in (-1, 1):
            m.sp((sx * 0.22, 0.02, 1.25), 0.11, c, seg=small, scale=(1.0, 0.6, 1.0), hull=hs)
            m.sp((sx * 0.36, -0.06, 0.55), 0.12, c, seg=small, scale=(0.9, 0.9, 1.6), hull=hs)
            if seated:
                m.sp((sx * 0.2, -0.3, 0.14), 0.14, c, seg=small, scale=(1.0, 1.7, 0.9), hull=hs)
            else:
                m.sp((sx * 0.16, 0.0, 0.06), 0.13, c, seg=small, scale=(1.0, 1.0, 1.4), hull=hs)
        m.sp((0, -0.24, 0.94), 0.12, paw, seg=small, scale=(1.1, 0.6, 0.8), hull='none')
        if not lo:
            fq(m, -0.12, 0.12, -0.32, 0.45, 0.62, paw)


def tin_robot(m, x, y, z, s, c='gB', trim='chrome', deg=0.0):
    """a wind-up tin robot toy: box body with a dial panel, box head with an antenna, tube arms and legs, a key
    (painted details stand 4 mm proud at any scale)"""
    e = max(0.003, 0.004 / s)
    with at(m, x, y, z, deg, s=s):
        for sx in (-1, 1):
            m.bx(sx * 0.1 - 0.08, sx * 0.1 + 0.08, -0.12, 0.12, 0.0, 0.35, trim)
            m.bx(sx * 0.1 - 0.1, sx * 0.1 + 0.1, -0.18, 0.14, 0.0, 0.08, 'pBlack', cull='b')
            m.bx(sx * 0.3 - 0.06, sx * 0.3 + 0.06, -0.08, 0.08, 0.4, 0.75, trim)
        m.bx(-0.24, 0.24, -0.16, 0.16, 0.35, 0.85, c)
        fq(m, -0.15, 0.15, -0.16 - e, 0.5, 0.72, 'pWhite')
        for k in range(3):
            fq(m, -0.11 + k * 0.08, -0.07 + k * 0.08, -0.16 - 2 * e, 0.6, 0.66, ['gA', 'gC', 'gD'][k])
        m.bx(-0.17, 0.17, -0.14, 0.14, 0.88, 1.18, c)
        fq(m, -0.12, 0.12, -0.14 - e, 0.98, 1.06, 'black')
        m.cy((0, 0, 1.18), 0.015, 0.015, 0.14, trim, seg=5, hull='none')
        m.sp((0, 0, 1.33), 0.04, 'gA', seg=(6, 4))
        m.cy((0, 0.16, 0.6), 0.025, 0.025, 0.1, 'brass', seg=5, rot=(-90, 0, 0), hull='none')
        m.bx(-0.12, 0.12, 0.25, 0.28, 0.54, 0.66, 'brass', cull='')


def carton(m, x0, x1, y0, y1, z0, z1, c, word=None, art=None, side=-1, tape='cardD'):
    """a printed toy carton: a coloured box, a white window panel with the product picture, the brand word, tape"""
    m.bx(x0, x1, y0, y1, z0, z1, c, cull='b')
    xm, w, hgt = (x0 + x1) / 2, x1 - x0, z1 - z0
    uq(m, xm - min(0.05, w * 0.12), xm + min(0.05, w * 0.12), y0, y1, z1 + 0.003, tape)
    yf = y0 - 0.003 if side < 0 else y1 + 0.003
    face = fq if side < 0 else bq
    face(m, x0 + w * 0.12, x1 - w * 0.12, yf, z0 + hgt * 0.14, z0 + hgt * 0.62, 'pWhite')
    if art:
        a = art
        yf2 = y0 - 0.006 if side < 0 else y1 + 0.006
        face(m, xm - w * 0.18, xm + w * 0.18, yf2, z0 + hgt * 0.2, z0 + hgt * 0.56, a)
    if word and hgt > 0.25 and w > 0.3:
        yt = y0 - 0.006 if side < 0 else y1 + 0.006
        (text_front if side < 0 else text_back)(m, word, hgt * 0.16, yt, xm, z0 + hgt * 0.7, 'pWhite', maxw=w * 0.8)
