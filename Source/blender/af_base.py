"""INKBOLT kit-airfield7 ("Airfield 7", a made-up remote military air base on the arid steppe): palette and modelling
helpers shared by af_struct.py (T-wall blast barriers, runway closure barriers, gate, trail, hatch, the control
tower, the revetments, the hardened aircraft shelter, the maintenance hangar, the barracks block, the ordnance igloo,
the engine test stand, the tool crib), af_craft.py (the fighter, the transport with its ramp down, the fuel bowser,
the crash tender, the runway caravan, the tug, the munitions trailer) and af_props.py (runway and taxiway lights and
signs, the windsock, ground equipment, workshop and ordnance props, scrub). The family module is fam_kit_airfield7.py.

Look: sun-bleached warm concrete and dark asphalt, sand and dry scrub, desert two-tone camouflage on the fighters,
olive drab on the transport and the trucks, tan corrugated cladding, safety yellow / red and black where things move,
comic ink outlines throughout.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender Z-up,
Blender -Y = game +Z (south, the piece's front), Blender +Y = game north, Blender +X = game east.
  * Wall modules (theme wall.facing 'open') face Blender -Y: the cell spans y -0.5..0.5, the inside face plane is
    y = -0.5 (vertical over the player's height band, so the wall cell's own box matches what is drawn); the T-wall's
    foot and the barrier's back reach outboard past y = +0.5.
  * Prefabs are modelled with their front (doors, open side, aircraft noses) toward Blender -Y.
  * Stairs and ramps rise in walkable steps of 0.5 m (the nav cell) that rise at most 0.2 m (<Piece>_WCOL boxes from
    the floor to the tread); galleries are walkable boxes in the piece.
  * Flat detail (paint, glints, lettering) is a single face without an outline shell, >= 3 mm proud of its surface.
"""
import math

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
from fam_kit_smallcity import PM, post_hull
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb  # noqa: F401
from ap_base import loft, slab, skin, wedge, cyl_x, cyl_y, wheel, chevrons, glint, glint_x, ring, vdisc, xdisc  # noqa: F401
from pel_base import PK, rot_cols, steps, stair_side_cols  # noqa: F401

FAM = 'kit-airfield7'
PFX = 'KIT_AIRFIELD7_'
ib_lib.GLB[FAM] = 'fps-kit-airfield7.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # concrete, asphalt, ground (8 - 21)
    ('conc', '#CBC3B0'), ('concD', '#A8A08E'), ('concL', '#E0DACB'), ('concS', '#8E877A'), ('asph', '#5E5B57'),
    ('asphD', '#46443F'), ('sand', '#D4B57F'), ('sandD', '#B8955E'), ('sandL', '#E6CF9F'), ('earth', '#9F774B'),
    ('scrub', '#8F914F'), ('scrubD', '#6C7140'), ('dry', '#BCA862'), ('rock', '#9A8C79'),
    # camouflage, olive drab (22 - 31)
    ('camoA', '#C9A974'), ('camoB', '#87663F'), ('camoC', '#6E7352'), ('belly', '#C6CAC4'), ('jetD', '#4D4940'),
    ('od', '#6B6F4A'), ('odD', '#51553A'), ('odL', '#878B62'), ('khaki', '#A99A6B'), ('khakiD', '#857750'),
    # steel, paint (32 - 45)
    ('steel', '#A6A8A2'), ('steelD', '#60635F'), ('dark', '#3A3B38'), ('black', '#202022'), ('grey', '#8C8E89'),
    ('yellow', '#F0C22E'), ('yellowD', '#C69A1E'), ('orange', '#EE7A2A'), ('redD', '#B8342C'), ('fire', '#D8382C'),
    ('white2', '#EEEDE6'), ('green', '#4C8E4E'), ('blue', '#2F6FB8'), ('blueD', '#1F4A7E'),
    # glass, light (46 - 52)
    ('glass', '#86C3D8'), ('glassD', '#2C5A70'), ('glassL', '#DDF3FB'), ('lamp', '#FFE9A6'), ('lampR', '#FF5A3D'),
    ('lampG', '#5AF07A'), ('lampB', '#62A8FF'),
    # rubber, cladding, building, misc (53 - 63)
    ('tire', '#2A2A2E'), ('rubber', '#3D4048'), ('corr', '#CDBE9C'), ('corrD', '#A3957A'), ('stucco', '#E3D4B4'),
    ('stuccoD', '#C2AE88'), ('wood', '#A8784A'), ('woodD', '#76522F'), ('rust', '#9A5A3A'), ('canvas', '#B7A57A'),
    ('webbing', '#B04A3A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

TRIS = {}
HT = 0.02
WALL_H = 3.6        # T-walls (their own _COL boxes, theme wall.cols)
BAR_H = 1.1         # runway closure barriers = theme wall.height (the wall cells' own box)
TRAIL_H = 2.6
TOWER_DECK = 3.6    # the control tower's terrace
GALLERY = 3.2       # the barracks' upper gallery
HOLD = 1.2          # the transport's cargo floor
RISE = 0.2          # stair rise per 0.5 m tread


def new(pal, rot=0.0):
    m = PK(pal)
    if rot:
        m.parent = Matrix.Rotation(math.radians(rot), 4, 'Z')
    return m


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


def text(m, word, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b', clip=None):
    return ib_text.draw(m, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign, clip=clip)


# ---------------------------------------------------------------- shared shapes
F4 = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]


def plate(m, pts, off, c, hull='full'):
    """a 4-cornered plate: the quad pts and the same quad moved by `off` (wings, fins, panels at any angle)"""
    v = list(pts) + [(p[0] + off[0], p[1] + off[1], p[2] + off[2]) for p in pts]
    return skin(m, (v, F4), c, hull=hull)


def hazard(m, x0, x1, y, z0, z1, n, face=-1):
    chevrons(m, x0, x1, y, z0, z1, n, ca='yellow', cb_='black', face=face)


def stair_x(cols, m, x0, y0, y1, n, rise=RISE, run=0.5, z0=0.0, sign=1, tread='steel', stringer='steelD', rail='yellow', rails=(True, True)):
    """a steel stair rising along Blender X (toward +X if sign > 0) from x0: n treads of `run`, walkable boxes, stringers
    and hand rails on the y0 / y1 sides; returns the top height"""
    L = n * run
    top = z0 + n * rise
    for i in range(n):
        xa, xb = sorted((x0 + sign * i * run, x0 + sign * (i + 1) * run))
        z = z0 + (i + 1) * rise
        cols.append(cb(xa, y0 + 0.01, z0, xb, y1 - 0.01, z, True))
        m.bx(xa + 0.01, xb - 0.01, y0 + 0.04, y1 - 0.04, z - 0.06, z, tread, cull='b')
        uq(m, xa + 0.03, xa + 0.1, y0 + 0.06, y1 - 0.06, z + 0.003, 'yellow') if sign > 0 else uq(m, xb - 0.1, xb - 0.03, y0 + 0.06, y1 - 0.06, z + 0.003, 'yellow')
    xe = x0 + sign * L
    for k, y in enumerate((y0, y1)):
        a, b = (y - 0.04, y) if k == 0 else (y, y + 0.04)
        # the stringer: a slanted plate from the foot to the top
        pts = [(x0, a, z0), (x0 + sign * 0.3, a, z0), (xe, a, top - 0.3), (xe, a, top)]
        plate(m, [(x0, a, z0), (x0 + sign * 0.35, a, z0), (xe, a, top - 0.32), (xe - sign * 0.3, a, top)], (0, b - a, 0), stringer)
        del pts
        if rails[k]:
            yr = y + (-0.065 if k == 0 else 0.065)
            m.bm_((x0 + sign * 0.1, yr, z0 + 1.0), (xe, yr, top + 1.0), 0.05, rail)
            for j in range(4):
                t = (j + 0.5) / 4
                xx = x0 + sign * (0.1 + t * (L - 0.1))
                zz = z0 + t * (top - z0)
                m.bx(xx - 0.018, xx + 0.018, yr - 0.018, yr + 0.018, zz, zz + 0.97, rail, hull='none', cull='b')
            # the rail's collision: one thin box per 2 m up to the rail height
            q = 0
            while q * 2.0 < L:
                xa, xb = sorted((x0 + sign * q * 2.0, x0 + sign * min(L, (q + 1) * 2.0)))
                hi = z0 + (min(L, (q + 1) * 2.0)) / run * rise + 1.0
                cols.append(cb(xa, yr - 0.05, z0, xb, yr + 0.05, hi))
                q += 1
    return top


def stair_y(cols, m, x0, x1, y0, n, rise=RISE, run=0.5, z0=0.0, sign=1, tread='steel', stringer='steelD', rail='yellow', rails=(True, True)):
    """the same stair rising along Blender Y (toward +Y if sign > 0) from y0, between x0 and x1"""
    L = n * run
    top = z0 + n * rise
    for i in range(n):
        ya, yb = sorted((y0 + sign * i * run, y0 + sign * (i + 1) * run))
        z = z0 + (i + 1) * rise
        cols.append(cb(x0 + 0.01, ya, z0, x1 - 0.01, yb, z, True))
        m.bx(x0 + 0.04, x1 - 0.04, ya + 0.01, yb - 0.01, z - 0.06, z, tread, cull='b')
        if sign > 0:
            uq(m, x0 + 0.06, x1 - 0.06, ya + 0.03, ya + 0.1, z + 0.003, 'yellow')
        else:
            uq(m, x0 + 0.06, x1 - 0.06, yb - 0.1, yb - 0.03, z + 0.003, 'yellow')
    ye = y0 + sign * L
    for k, x in enumerate((x0, x1)):
        a, b = (x - 0.04, x) if k == 0 else (x, x + 0.04)
        plate(m, [(a, y0, z0), (a, y0 + sign * 0.35, z0), (a, ye, top - 0.32), (a, ye - sign * 0.3, top)], (b - a, 0, 0), stringer)
        if rails[k]:
            xr = x + (-0.065 if k == 0 else 0.065)
            m.bm_((xr, y0 + sign * 0.1, z0 + 1.0), (xr, ye, top + 1.0), 0.05, rail)
            for j in range(4):
                t = (j + 0.5) / 4
                yy = y0 + sign * (0.1 + t * (L - 0.1))
                zz = z0 + t * (top - z0)
                m.bx(xr - 0.018, xr + 0.018, yy - 0.018, yy + 0.018, zz, zz + 0.97, rail, hull='none', cull='b')
            q = 0
            while q * 2.0 < L:
                ya, yb = sorted((y0 + sign * q * 2.0, y0 + sign * min(L, (q + 1) * 2.0)))
                hi = z0 + (min(L, (q + 1) * 2.0)) / run * rise + 1.0
                cols.append(cb(xr - 0.05, ya, z0, xr + 0.05, yb, hi))
                q += 1
    return top


def rail_x(cols, m, x0, x1, y, z, c='yellow', posts=1.2):
    """a hand rail along X at height z (top rail, mid rail, posts) with its thin collision box"""
    cyl_x(m, x0, x1, y, z + 1.0, 0.035, c, seg=6, caps=False)
    cyl_x(m, x0, x1, y, z + 0.52, 0.025, c, seg=5, caps=False)
    n = max(1, int(round((x1 - x0) / posts)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        m.bx(x - 0.014, x + 0.014, y - 0.014, y + 0.014, z, z + 0.99, c, hull='none', cull='b')
    cols.append(cb(x0, y - 0.06, z, x1, y + 0.06, z + 1.05))


def rail_y(cols, m, y0, y1, x, z, c='yellow', posts=1.2):
    cyl_y(m, x, y0, y1, z + 1.0, 0.035, c, seg=6, caps=False)
    cyl_y(m, x, y0, y1, z + 0.52, 0.025, c, seg=5, caps=False)
    n = max(1, int(round((y1 - y0) / posts)))
    for i in range(1, n):   # the end posts belong to the rails along X that meet this one
        y = y0 + (y1 - y0) * i / n
        m.bx(x - 0.014, x + 0.014, y - 0.014, y + 0.014, z, z + 0.99, c, hull='none', cull='b')
    cols.append(cb(x - 0.06, y0, z, x + 0.06, y1, z + 1.05))


def window_y(m, x0, x1, y, z0, z1, every=1.0, frame='dark', glass='glassD', face=-1, sill='concL'):
    """a window band on a wall face at y (facing -Y or +Y): glass 3 mm proud, mullions, rails, sill, glints"""
    q = fq if face < 0 else bq
    q(m, x0, x1, y + face * 0.003, z0, z1, glass)
    n = max(1, int(round((x1 - x0) / every)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        q(m, max(x0, x - 0.03), min(x1, x + 0.03), y + face * 0.007, z0, z1, frame)
    q(m, x0, x1, y + face * 0.011, z0, z0 + 0.05, frame)
    q(m, x0, x1, y + face * 0.011, z1 - 0.05, z1, frame)
    if sill:
        ya, yb = sorted((y, y + face * 0.12))
        m.bx(x0 - 0.05, x1 + 0.05, ya, yb, z0 - 0.08, z0, sill, hull='none', cull='k' if face < 0 else 'f')
    for i in range(n):
        if i % 3 == 1:
            continue
        xa = x0 + (x1 - x0) * (i + 0.25) / n
        glint(m, xa, y + face * 0.015, z0 + (z1 - z0) * 0.2, (z1 - z0) * 0.5, w=min(0.14, (x1 - x0) / n * 0.2), c='glassL', face=face)


def window_x(m, y0, y1, x, z0, z1, every=1.0, frame='dark', glass='glassD', face=1):
    """a window band on a wall face at x (facing +X or -X)"""
    q = lq if face < 0 else rq     # lq paints a face looking -X, rq one looking +X
    q(m, x + face * 0.003, y0, y1, z0, z1, glass)
    n = max(1, int(round((y1 - y0) / every)))
    for i in range(n + 1):
        yy = y0 + (y1 - y0) * i / n
        q(m, x + face * 0.007, max(y0, yy - 0.03), min(y1, yy + 0.03), z0, z1, frame)
    q(m, x + face * 0.011, y0, y1, z0, z0 + 0.05, frame)
    q(m, x + face * 0.011, y0, y1, z1 - 0.05, z1, frame)
    for i in range(n):
        if i % 3 == 1:
            continue
        ya = y0 + (y1 - y0) * (i + 0.25) / n
        glint_x(m, x + face * 0.015, ya, z0 + (z1 - z0) * 0.2, (z1 - z0) * 0.5, w=min(0.14, (y1 - y0) / n * 0.2), c='glassL', face=face)


def arch_pts(a, b, n, z0=0.0):
    """points of a half ellipse (half width a, height b) from (-a, z0) over the top to (a, z0)"""
    return [(-a * math.cos(math.pi * i / n), z0 + b * math.sin(math.pi * i / n)) for i in range(n + 1)]


def vault(m, y0, y1, a_out, b_out, a_in, b_in, n, c, c_in=None, hull='full'):
    """an arched shell along Blender Y (a barrel vault, the cross-section a half-elliptical ring): one closed solid"""
    O, I = arch_pts(a_out, b_out, n), arch_pts(a_in, b_in, n)
    verts, faces = [], []
    for y in (y0, y1):
        for (x, z) in O:
            verts.append((x, y, z))
        for (x, z) in I:
            verts.append((x, y, z))
    K = n + 1
    o0, i0, o1, i1 = 0, K, 2 * K, 3 * K
    for i in range(n):
        faces.append((o0 + i, o0 + i + 1, o1 + i + 1, o1 + i))         # outer skin
        faces.append((i0 + i, i1 + i, i1 + i + 1, i0 + i + 1))         # inner skin
        faces.append((o0 + i, i0 + i, i0 + i + 1, o0 + i + 1))         # front face
        faces.append((o1 + i, o1 + i + 1, i1 + i + 1, i1 + i))         # back face
    for e in (0, n):                                                   # the feet
        faces.append((o0 + e, o1 + e, i1 + e, i0 + e))
    inner = set(range(n, 2 * n))

    def col(f):
        return c

    fs = skin(m, (verts, faces), c, hull=hull)
    if c_in:
        mi = m.pal.index(c_in)
        for k, f in enumerate(fs):
            if k % 4 == 1 and k < 4 * n:
                f.material_index = mi
    del inner, col
    return fs


def box_lines(m, x0, x1, y0, y1, w, z, c, sides='nsew'):
    """a painted rectangle outline on the floor (lines of width w; the side lines stop at the end lines, no overlap)"""
    if 's' in sides:
        uq(m, x0, x1, y0, y0 + w, z, c)
    if 'n' in sides:
        uq(m, x0, x1, y1 - w, y1, z, c)
    ya = y0 + (w if 's' in sides else 0.0)
    yb = y1 - (w if 'n' in sides else 0.0)
    if 'w' in sides:
        uq(m, x0, x0 + w, ya, yb, z, c)
    if 'e' in sides:
        uq(m, x1 - w, x1, ya, yb, z, c)


def tyre_stack(m, x, y, n, r=0.42, w=0.24):
    for k in range(n):
        m.cy((x, y, k * w), r, r, w - 0.01, 'tire', seg=10)
        m.cy((x, y, k * w + w - 0.008), r * 0.55, r * 0.55, 0.005, 'black', seg=8, hull='none')
