"""INKBOLT kit-pelagic ("Pelagic Airbase", a made-up offshore military air platform far out at sea): palette and
modelling helpers shared by pel_struct.py (deck-edge railings and safety nets, blast fences, the runway barricade, the
flight-operations block front, gate, trail, hatch, the island control tower, the second tower, the hangar shells,
decks, stairs, rails), pel_craft.py (the light aircraft at the spawn with its open canopy and boarding stair, the
naval fighters, the helicopter, deck tractors, ordnance carts, the crash tender, the escort warships far out) and
pel_props.py (blast deflectors, arresting wires, deck gear, maintenance stands, cargo lifts, fuel tanks and lines,
containers, floodlights). The family module is fam_kit_pelagic.py.

Look: haze-grey naval steel, a dark non-skid flight deck with white / yellow / red markings, safety yellow and
black on everything that moves or trips you, hangars in pale corrugated cladding, comic ink outlines throughout.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender Z-up,
Blender -Y = game +Z (south, the piece's front), Blender +Y = game north, Blender +X = game east.
  * Wall modules (theme wall.facing 'open') face Blender -Y: the cell spans y -0.5..0.5, the inside face plane is
    y = -0.5; what lies outboard (the deck lip, the safety nets) reaches past y = +0.5.
  * Run pieces placed with `links` (stair / deck rails, fuel lines) are modelled along Blender Y (the half module runs
    from the origin toward -Y); pieces placed with rotate 'run' (arresting wires, runway lights, bund kerbs) along X.
  * Stairs rise toward Blender +Y in walkable steps of 0.5 m (the nav cell) that rise 0.2 m (<Piece>_WCOL boxes from
    the floor to the tread); decks are the engine's deck slabs (layers) or walkable boxes in the piece.
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

FAM = 'kit-pelagic'
PFX = 'KIT_PELAGIC_'
ib_lib.GLB[FAM] = 'fps-kit-pelagic.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # deck and naval steel (8 - 21)
    ('deck', '#565C64'), ('deck2', '#454A51'), ('deckL', '#757B83'), ('navy', '#8E99A5'), ('navyD', '#6B7682'),
    ('navyL', '#B7C0C9'), ('dark', '#363C45'), ('steel', '#A7B0B9'), ('steelD', '#5A626C'), ('black', '#202228'),
    ('conc', '#B9B6AE'), ('wall', '#D8D6CF'), ('wallD', '#A7A49B'), ('wallL', '#ECEBE6'),
    # safety colours, paint (22 - 31)
    ('yellow', '#F2C230'), ('yellowD', '#C99A1C'), ('orange', '#EE7A2A'), ('redD', '#B8342C'), ('green', '#3F9E5A'),
    ('blue', '#2F6FB8'), ('blueD', '#1F4A7E'), ('cream', '#F1E7CF'), ('olive', '#6A7344'), ('oliveD', '#4E5631'),
    # glass, light (32 - 40)
    ('glass', '#7EC2DC'), ('glassD', '#2C5A70'), ('glassL', '#DDF3FB'), ('lamp', '#FFE9A6'), ('lampW', '#FFF7DE'),
    ('beacon', '#FF5A3D'), ('lgreen', '#5AF07A'), ('lblue', '#62A8FF'), ('screen', '#46E0CF'),
    # rubber, hangar, cargo, rope, sea (41 - 55)
    ('tire', '#2A2A2E'), ('rubber', '#3D4048'), ('corr', '#C9D1D6'), ('corrD', '#A1ACB4'), ('epoxy', '#AEB6B9'),
    ('cont1', '#2F6FB8'), ('cont2', '#B5402F'), ('cont3', '#4F8A5E'), ('cont4', '#E39A35'), ('net', '#D9CBA2'),
    ('netD', '#A8996F'), ('sea', '#2C7AB2'), ('foam', '#EAF6FA'), ('wood', '#A8784A'), ('seat', '#3F4552'),
    # more (56 - 63)
    ('hull', '#7D8996'), ('hullD', '#5D6875'), ('boot', '#2B2A31'), ('rust', '#9A5A3A'), ('brass', '#D7A341'),
    ('fire', '#D8382C'), ('gold', '#E9B83A'), ('teal2', '#2FA39A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
CONT = ['cont1', 'cont2', 'cont3', 'cont4']   # container colours (the theme repaints them per copy)

TRIS = {}
HT = 0.02
EDGE_H = 1.2        # deck-edge railing / zone wall height (theme wall.height)
FENCE_H = 3.6       # blast fences (their own _COL boxes, theme wall.cols)
OPS_H = 7.6         # flight-operations block front
TRAIL_H = 2.6
GALLERY = 3.6       # island gallery / second tower balcony
HELI = 2.4          # helicopter dock deck
MEZZ = 3.0          # hangar mezzanines
RISE = 0.2          # stair rise per 0.5 m tread
HANGAR_H = 9.0      # hangar eaves


class PK(PM):
    """PM whose boxes accept their extents in either order"""

    def bx(self, x0, x1, y0, y1, z0, z1, color, hull='full', bevel=False, cull=''):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        return PM.bx(self, x0, x1, y0, y1, z0, z1, color, hull=hull, bevel=bevel, cull=cull)

    def push(self, x, y, deg=0.0, z=0.0):
        self._st = getattr(self, '_st', [])
        self._st.append(self.parent)
        self.parent = self.parent @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')

    def pop(self):
        self.parent = self._st.pop()


def new(pal, rot=0.0):
    m = PK(pal)
    if rot:
        m.parent = Matrix.Rotation(math.radians(rot), 4, 'Z')
    return m


def make(name, m, ao, bevel=0.0, cols=None, hull=HT):
    full = PFX + name
    import pel_detail
    pel_detail.apply(name, m)
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


def rot_cols(cols, deg):
    """turn collision boxes (cb tuples) a quarter turn multiple about Z"""
    k = int(round(deg / 90.0)) % 4
    out = []
    for (c, h, *w) in cols:
        x, y, z = c
        hx, hy, hz = h
        for _ in range(k):
            x, y = -y, x
            hx, hy = hy, hx
        out.append(((x, y, z), (hx, hy, hz), w[0] if w else False))
    return out


# ---------------------------------------------------------------- lettering
def text(m, word, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b', clip=None):
    return ib_text.draw(m, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign, clip=clip)


# ---------------------------------------------------------------- shared shapes
def steps(cols, x0, x1, y0, n, rise=RISE, run=0.5, z0=0.0):
    """walkable stair blocks rising toward +Y from y0: n treads of `run`, each `rise` higher (WCOL from z0)"""
    for i in range(n):
        cols.append(cb(x0, y0 + i * run, z0, x1, y0 + (i + 1) * run, z0 + (i + 1) * rise, True))


def stair_visual(m, x0, x1, y0, n, rise=RISE, run=0.5, z0=0.0, tread='steel', stringer='navyD', rails=(True, True), rail_c='yellow'):
    """a steel stair: treads (grating), nosing stripes, side stringers, hand rails; rises toward +Y from y0"""
    L = n * run
    top = z0 + n * rise
    for i in range(n):
        ya = y0 + i * run
        z = z0 + (i + 1) * rise
        m.bx(x0 + 0.04, x1 - 0.04, ya + 0.02, ya + run, z - 0.06, z, tread, cull='b')
        uq(m, x0 + 0.06, x1 - 0.06, ya + 0.03, ya + 0.1, z + 0.003, 'yellow')
    for side, x in ((0, x0), (1, x1)):
        a, b = (x - 0.04, x + 0.0) if side == 0 else (x, x + 0.04)
        prof = [(y0, z0), (y0 + 0.25, z0), (y0 + L, top - 0.3), (y0 + L, top), (y0 + L - 0.25, top), (y0, z0 + 0.3)]
        m.prism(prof, a, b, [stringer])
        if rails[side]:
            xr = x + (-0.02 if side == 0 else 0.02)
            m.bm_((xr, y0 + 0.1, z0 + 1.05), (xr, y0 + L, top + 1.05), 0.05, rail_c)
            for k in range(4):
                t = (k + 0.5) / 4
                yy = y0 + 0.1 + t * (L - 0.1)
                zz = z0 + t * (top - z0)
                m.bx(xr - 0.032, xr + 0.032, yy - 0.02, yy + 0.02, zz, zz + 1.03, rail_c, hull='none', cull='b')
    return top


def stair_side_cols(cols, x, y0, n, rise=RISE, run=0.5, z0=0.0, t=0.06):
    """thin hand-rail collision along a stair side (one box per 2 m, up to the rail height)"""
    L = n * run
    k = 0
    while k * 2.0 < L:
        ya, yb = y0 + k * 2.0, min(y0 + L, y0 + (k + 1) * 2.0)
        top = z0 + (yb - y0) / run * rise + 1.05
        cols.append(cb(x - t, ya, z0, x + t, yb, top))
        k += 1


def hazard(m, x0, x1, y, z0, z1, n, face=-1):
    chevrons(m, x0, x1, y, z0, z1, n, ca='yellow', cb_='black', face=face)


def hazard_up(m, x0, x1, y0, y1, z, n, along='x'):
    """black / yellow bands painted on an upward face (a step edge, a lift border)"""
    uq(m, x0, x1, y0, y1, z, 'black')
    if along == 'x':
        w = (x1 - x0) / n
        for i in range(0, n, 2):
            a = x0 + i * w
            poly(m, [(a, y0, z + 0.003), (min(x1, a + w), y0, z + 0.003), (min(x1, a + w + (y1 - y0) * 0.6), y1, z + 0.003), (min(x1, a + (y1 - y0) * 0.6), y1, z + 0.003)], 'yellow', (0, 0, 1))
    else:
        w = (y1 - y0) / n
        for i in range(0, n, 2):
            a = y0 + i * w
            poly(m, [(x0, a, z + 0.003), (x0, min(y1, a + w), z + 0.003), (x1, min(y1, a + w + (x1 - x0) * 0.6), z + 0.003), (x1, min(y1, a + (x1 - x0) * 0.6), z + 0.003)], 'yellow', (0, 0, 1))


def window_band(m, x0, x1, y, z0, z1, every=1.0, frame='dark', glass='glass', face=-1, glints=True):
    """a row of windows on a plane at y: the dark glass pane with mullions every `every` m and glints"""
    (fq if face < 0 else bq)(m, x0, x1, y, z0, z1, glass)
    d = face * 0.004
    n = max(1, int(round((x1 - x0) / every)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        (fq if face < 0 else bq)(m, max(x0, x - 0.03), min(x1, x + 0.03), y + d, z0, z1, frame)
    (fq if face < 0 else bq)(m, x0, x1, y + 2 * d, z0, z0 + 0.05, frame)
    (fq if face < 0 else bq)(m, x0, x1, y + 2 * d, z1 - 0.05, z1, frame)
    if glints:
        for i in range(n):
            xa = x0 + (x1 - x0) * (i + 0.25) / n
            if (i % 3) == 1:
                continue
            h = (z1 - z0) * 0.55
            glint(m, xa, y + d * 3, z0 + (z1 - z0) * 0.2, h, w=min(0.14, (x1 - x0) / n * 0.2), c='glassL', face=face)


def window_band_x(m, y0, y1, x, z0, z1, every=1.0, frame='dark', glass='glass', face=1):
    """windows on a plane at x (facing +X or -X)"""
    if face > 0:
        m.bx(x, x + 0.002, y0, y1, z0, z1, glass, hull='none', cull='tbfkl')
    else:
        m.bx(x - 0.002, x, y0, y1, z0, z1, glass, hull='none', cull='tbfkr')
    d = face * 0.004
    n = max(1, int(round((y1 - y0) / every)))
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        ya, yb = max(y0, y - 0.03), min(y1, y + 0.03)
        if face > 0:
            m.bx(x + d, x + d + 0.002, ya, yb, z0, z1, frame, hull='none', cull='tbfkl')
        else:
            m.bx(x + d - 0.002, x + d, ya, yb, z0, z1, frame, hull='none', cull='tbfkr')
    for zz in (z0, z1 - 0.05):
        if face > 0:
            m.bx(x + 2 * d, x + 2 * d + 0.002, y0, y1, zz, zz + 0.05, frame, hull='none', cull='tbfkl')
        else:
            m.bx(x + 2 * d - 0.002, x + 2 * d, y0, y1, zz, zz + 0.05, frame, hull='none', cull='tbfkr')
    for i in range(n):
        if i % 3 == 1:
            continue
        ya = y0 + (y1 - y0) * (i + 0.25) / n
        glint_x(m, x + d * 3, ya, z0 + (z1 - z0) * 0.2, (z1 - z0) * 0.55, w=min(0.14, (y1 - y0) / n * 0.2), c='glassL', face=face)
