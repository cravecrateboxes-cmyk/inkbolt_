"""INKBOLT kit-townhomes ("Larkspur Glen", a gated town-house community at midday): palette, dimensions and the
modelling helpers shared by townhomes_houses.py, townhomes_site.py and townhomes_street.py (the family module is
fam_kit_townhomes.py).

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front. Flat detail is painted as single faces without an outline shell (PM hull='none') and
stands >= 3 mm proud of what it sits on. Collision: <Piece>_COL<n> boxes, <Piece>_WCOL<n> for floors, steps, porches
and balconies robots walk on (rises <= 0.32 m, treads >= 0.5 m).

Paint jobs (theme symbol option `paint`): the houses colour their siding, stucco, brick, front door and shutters with
the cells 'sid', 'stu', 'brk', 'door' and 'shut'; the theme moves those UVs onto the alternatives listed here, so one
model shows up in many colour schemes along a row.
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull, tile  # noqa: F401
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401
import ib_text

FAM = 'kit-townhomes'
PFX = 'KIT_TOWNHOMES_'
ib_lib.GLB[FAM] = 'fps-kit-townhomes.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # paint-job sources (8 - 12): siding, stucco, brick, front door, shutters
    ('sid', '#9DB89A'), ('stu', '#E9DCC0'), ('brk', '#B5523B'), ('door', '#B8352E'), ('shut', '#2F3B33'),
    # paint-job targets (13 - 29)
    ('sidB', '#86A5C4'), ('sidY', '#EED58E'), ('sidC', '#EFE6D2'), ('sidG', '#A9ADB4'), ('sidP', '#E3B6A6'),
    ('stuC', '#D99A72'), ('stuW', '#F4EFE6'), ('stuP', '#EBC3A0'),
    ('brkB', '#8C5A45'), ('brkT', '#C79062'),
    ('doorN', '#2B3A67'), ('doorG', '#2F6B4F'), ('doorY', '#E2A632'), ('doorT', '#23A49F'), ('doorK', '#34303B'),
    ('shutN', '#334466'), ('shutW', '#F2EEE4'),
    # trim, roofs, glass, metal (30 - 41)
    ('trim', '#F7F4EC'), ('trimD', '#D6CFC0'), ('mortar', '#E6DCCB'), ('shingle', '#5A5560'), ('shingleD', '#433F49'),
    ('tileR', '#A9543B'), ('glass', '#7FB9D9'), ('glassL', '#D2EEF9'), ('glassD', '#4A6A86'), ('iron', '#2E2B35'),
    ('steel', '#8A95A3'), ('chrome', '#D6DCE3'),
    # street, stone, greens (42 - 53)
    ('walk', '#D3CCC0'), ('walkB', '#C2BAAE'), ('curb', '#A39C90'), ('lineW', '#F1EFE6'), ('lineY', '#F2C230'),
    ('stone', '#CDBF9F'), ('stoneD', '#9E8F76'), ('grass', '#7DBB5A'), ('grassD', '#64A048'), ('leaf', '#5FA857'),
    ('leafD', '#43803F'), ('trunk', '#6E4E3A'),
    # wood, interiors, pool, safety (54 - 63)
    ('wood', '#BC8853'), ('woodD', '#7B5236'), ('woodL', '#DDB37C'), ('plaster', '#F1EBDF'), ('fabric', '#5E7FA6'),
    ('fabricR', '#C25B4A'), ('water', '#4FC3E0'), ('waterL', '#A6E8F5'), ('orange', '#F2681F'), ('flower', '#E8668F'),
]
assert len(ib_lib.PALETTES[FAM]) == 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]
TRIS = {}
HT = 0.02

# ---------------------------------------------------------------- house dimensions (piece frame, front = -Y)
HW = 3.0            # half width of a house lot (6 m)
FW = -4.5           # front wall plane (outer face); the porch strip runs -6 .. FW
BW = 6.0            # back wall plane (outer face)
WT = 0.2            # wall thickness
GF = 0.32           # ground floor surface (two 0.16 risers up from the yard: the step and the porch)
UF = 3.32           # upper floor surface
SLAB = 0.25         # floor slab: underside UF - SLAB
UC = 6.0            # upper ceiling
EAVE2 = 6.35        # eave of a two-storey house
EAVE3 = 9.25        # top of the third storey (brick, modern)
IX = HW - WT        # inner wall faces x = +/-2.8
IY0, IY1 = FW + WT, BW - WT
DOOR = (-2.75, -1.45)   # front / back door opening (x); 1.3 m so robots path through (nav cells 0.5 m)
DOOR_H = 2.55
STAIR = (-2.8, -1.5, -3.2, 1.8)   # x0, x1, y0 (foot), y1 (top): ten 0.3 m risers on 0.5 m treads up to UF
PART_Y = 3.1        # upper partition (front face); the back bedroom behind it
FRENCH = (-0.65, 0.65)  # upper balcony door opening (x)
FR_H = 2.25


def new(pal):
    return PM(pal)


def prune_hidden(m):
    """Drop faces nobody can see (the kit's GLB is size-capped): faces lying on the ground facing down, and axis-aligned
    faces that press against an opposite-facing face of a solid part which covers them (a box standing on a slab,
    a wall meeting a floor). Only solids count as covering: a flat painted quad has no body behind it."""
    bm = m.bm
    bm.normal_update()
    bm.faces.index_update()
    lay = m.shape
    lo, hi = {}, {}
    for f in bm.faces:
        s = f[lay]
        for v in f.verts:
            c = v.co
            a = lo.setdefault(s, [1e9] * 3)
            b = hi.setdefault(s, [-1e9] * 3)
            for i in range(3):
                a[i] = min(a[i], c[i])
                b[i] = max(b[i], c[i])
    buckets = {}
    info = {}
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[ax]) < 0.9999:
            continue
        sg = 1 if n[ax] > 0 else -1
        pl = f.verts[0].co[ax]
        o = [i for i in range(3) if i != ax]
        mn = [min(v.co[i] for v in f.verts) for i in o]
        mx = [max(v.co[i] for v in f.verts) for i in o]
        rect = len(f.verts) == 4 and abs(f.calc_area() - (mx[0] - mn[0]) * (mx[1] - mn[1])) < 1e-7
        info[f.index] = (ax, sg, pl, mn, mx, rect)
        buckets.setdefault((ax, round(pl, 4)), []).append(f)
    dead = set()
    for (ax, pl), lst in buckets.items():
        if abs(pl) < 1e-4 and ax == 2:
            dead.update(f for f in lst if info[f.index][1] < 0)       # on the ground, facing down
        for fa in lst:
            ia = info[fa.index]
            for fb_ in lst:
                if fb_ is fa:
                    continue
                ib_ = info[fb_.index]
                if ib_[1] == ia[1] or not ib_[5]:
                    continue
                s = fb_[lay]
                if hi[s][ax] - lo[s][ax] < 0.02:      # a flat sheet: no body
                    continue
                e = 1e-5
                if ib_[3][0] - e <= ia[3][0] and ia[4][0] <= ib_[4][0] + e and ib_[3][1] - e <= ia[3][1] and ia[4][1] <= ib_[4][1] + e:
                    dead.add(fa)
                    break
    if dead:
        bmesh.ops.delete(bm, geom=list(dead), context='FACES')


def make(name, m, ao, bevel=0.0, cols=None, hull=HT):
    """build one kit piece; cols: collision boxes [(centre, half, walk?)] as box() / wbox() return them"""
    full = PFX + name
    import re as _re
    sh = {}
    for f in m.bm.faces:
        sh.setdefault(f[m.shape], NAMES[f.material_index])
    prune_hidden(m)
    try:
        obj = build_object(full, m, bevel, hull, ao=ao)
    except ZFightError as e:   # name the colours of the clashing shapes (debug aid)
        msg = _re.sub(r'shapes (\d+)/(\d+)', lambda g: 'shapes %s(%s)/%s(%s)' % (g.group(1), sh.get(int(g.group(1))), g.group(2), sh.get(int(g.group(2)))), str(e))
        raise ZFightError(msg)
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


def box(x0, y0, z0, x1, y1, z1):
    """collision box from two corners, any order (Blender coords)"""
    return cb(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1))


def wbox(x0, y0, z0, x1, y1, z1):
    """walkable collision box (a floor, a step, a porch, a balcony)"""
    return cb(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), True)


def rz(deg, dx=0.0, dy=0.0, dz=0.0):
    return Matrix.Translation((dx, dy, dz)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


def txt(m, word, x, y, z, cap, color, face='y-', font='sans', valign='m', maxw=None, shadow=None, align='c'):
    ib_text.draw(m, word, x, y, z, cap, color, face=face, font=font, valign=valign, maxw=maxw, shadow=shadow, align=align)


def srt(a, b):
    return (a, b) if a <= b else (b, a)


# ---------------------------------------------------------------- generic shapes
def post(m, x, y, z0, z1, r, c, seg=6, hull='full'):
    m.cy((x, y, z0), r, r, z1 - z0, c, seg=seg, hull=hull)


def rail_x(m, x0, x1, y, z, t, c, hull='full'):
    m.bx(x0, x1, y - t / 2, y + t / 2, z - t / 2, z + t / 2, c, hull=hull)


def rail_y(m, y0, y1, x, z, t, c, hull='full'):
    m.bx(x - t / 2, x + t / 2, y0, y1, z - t / 2, z + t / 2, c, hull=hull)


def pickets_x(m, x0, x1, y, z0, z1, step, w, c, hull='none'):
    """vertical bars along X (balusters, iron pickets)"""
    n = max(1, int(round((x1 - x0) / step)))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        m.bx(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z0, z1, c, hull=hull, cull='tblr')


def pickets_y(m, y0, y1, x, z0, z1, step, w, c, hull='none'):
    n = max(1, int(round((y1 - y0) / step)))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        m.bx(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z0, z1, c, hull=hull, cull='tbfk')


def shrub(m, x, y, r, c='leaf', c2='leafD', z=0.0, seg=(7, 4), squash=0.8):
    m.sp((x, y, z + r * squash * 0.85), r, c, seg=seg, scale=(1, 1, squash))
    m.sp((x + r * 0.35, y - r * 0.3, z + r * squash * 0.7), r * 0.6, c2, seg=(6, 3), scale=(1, 1, squash))


def flowers(m, x0, x1, y0, y1, z, colors=('flower', 'trim', 'doorY'), n=6, s=0.06):
    """painted blossom dots on a bed / a shrub top"""
    k = 0
    for i in range(n):
        x = x0 + (x1 - x0) * ((i * 0.618) % 1.0)
        y = y0 + (y1 - y0) * ((i * 0.382 + 0.17) % 1.0)
        uq(m, x - s, x + s, y - s, y + s, z + 0.004 * (i % 3), colors[k % len(colors)])
        k += 1


def tree_round(m, x, y, h=4.2, r=1.5, trunk=0.13, c='leaf', c2='leafD'):
    m.cy((x, y, 0), trunk, trunk * 0.75, h * 0.55, 'trunk', seg=5)
    m.sp((x, y, h * 0.72), r, c, seg=(7, 5))
    m.sp((x + r * 0.45, y + r * 0.2, h * 0.62), r * 0.62, c2, seg=(6, 3))
    m.sp((x - r * 0.35, y - r * 0.3, h * 0.86), r * 0.55, c2, seg=(5, 3))
