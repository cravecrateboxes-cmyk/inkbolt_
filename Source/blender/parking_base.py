"""INKBOLT kit-parking ("Deep Park", a multi-level underground car park): palette and modelling helpers shared by
parking_struct.py, parking_cars.py and parking_props.py (the family module is fam_kit_parking.py).

Levels: every zone is a split car park with a deck ("@layer 3.6" in the zone file, slab 3.2 - 3.6) over the floor and
the ceiling at 7 m. Each level has its own colour (B1 blue, B2 green, B3 orange, B4 purple): wall modules come per
level and storey (Lo_<level>_* 0 - 3.6 under the deck, Up_<level>_* 3.6 - 7.0 over it: colour band, big level code,
painted arrows, downpipes and hose reels, piers, fire doors, lift doors, dock shutters); columns, level signs and bay
plaques are modelled in the B1 colours and recoloured per level by the theme (symbol option `paint`).
Circulation: straight car ramps (Ramp 16 m rising 3.6 m, RampHalf 8 m rising 1.8 m, DockRamp) and concrete stair
flights whose collision is a run of walkable stair blocks (<Piece>_WCOL, 0.12 m rises on the ramps), with kerbs and
guard rails on both sides; deck-edge rails (half modules the engine links into runs).
Vehicles (front = Blender -Y): sedans, hatchbacks, SUVs, a sports car, pickups, vans, a box truck, a tow truck, a
delivery truck at the dock, motorbikes, scooters, a bike rack, a maintenance buggy, a covered car, a car on a jack,
burnt-out and smashed wrecks; doors / boot open variants, hazard lights (HazardGlow, blinked by the theme). Body paint
is the 'paint' cell: the theme repaints each placed car from a list of paint jobs.
Dressing: painted bays with wheel stops (numbers, EV and blue-badge bays, oil stains), lane arrows, dashed lane lines,
yellow hatching, crossings, oil stains, puddles, drains, speed bumps; ceiling beams, ducts, sprinkler and water pipes,
strip lights (StripOff + StripGlow flicker overlay), exit signs, level signs, CCTV; ticket barriers, pay stations,
cones, bollards, jersey barriers, maintenance cages, drums, pallets, bins, a forklift, a car wash, dock edges.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; ramps and stairs rise toward Blender +Y (game north) at yaw 0. Ceiling pieces hang from
their origin (the ceiling plane at 7 m, or the deck underside at 3.2 m). Flat detail is painted as single faces
without an outline shell (PM hull='none'); details stay >= 3 mm proud of what they sit on.
"""
import math

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull, slant
import ib_text

FAM = 'kit-parking'
PFX = 'KIT_PARKING_'
ib_lib.GLB[FAM] = 'fps-kit-parking.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # concrete, water, paint lines (8 - 15)
    ('conc', '#BDB6A9'), ('concL', '#D8D2C6'), ('concD', '#8C867D'), ('concW', '#A39C90'),
    ('stain', '#55504C'), ('puddle', '#6F8BA3'), ('puddleL', '#B4CCDD'), ('lineY', '#FFCF33'),
    # metal, pipes, lights (16 - 27)
    ('steel', '#8A95A3'), ('steelD', '#4F5865'), ('galv', '#B9C2CB'), ('chrome', '#D6DCE3'),
    ('rust', '#A4532D'), ('pipeR', '#D9423A'), ('pipeB', '#3B7CC6'), ('light', '#FFF4C8'),
    ('lightC', '#E9FCFF'), ('litA', '#FFB01F'), ('exitG', '#25B35E'), ('signB', '#2A63CB'),
    # vehicles, wrecks, props (28 - 39)
    ('glass', '#7FB9D9'), ('glassL', '#D2EEF9'), ('tire', '#2A2830'), ('seat', '#3B3542'),
    ('interior', '#4A4553'), ('plate', '#F3EFDF'), ('burnt', '#3A3331'), ('burntL', '#6C5B4D'),
    ('ash', '#8B857D'), ('wood', '#BC8853'), ('cardb', '#C99B60'), ('cone', '#F2681F'),
    # level colours (40 - 47): B1 blue, B2 green, B3 orange, B4 purple (dark, light)
    ('lvB', '#3A86E0'), ('lvBL', '#BFDDFB'), ('lvG', '#2FB06A'), ('lvGL', '#BDEFD1'),
    ('lvO', '#F4892C'), ('lvOL', '#FFDDB8'), ('lvP', '#A257DA'), ('lvPL', '#E3C9F7'),
    # car paint jobs (48 - 59): 'paint' is what the models use, the theme swaps it for the others; tarp (60)
    ('paint', '#D8392F'), ('pBlue', '#2F6CD3'), ('pYellow', '#F2C230'), ('pGreen', '#3C9E57'),
    ('pWhite', '#ECEBE4'), ('pBlack', '#3A3842'), ('pSilver', '#A7B0BA'), ('pOrange', '#EE7A2A'),
    ('pTeal', '#23A49F'), ('pPurple', '#7D55C7'), ('pMint', '#86D4B4'), ('pBrown', '#8E5C3D'),
    ('tarp', '#5E7FA6'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
TRIS = {}
HT = 0.02
H = 7.0          # ceiling
DECK = 3.6       # deck top (slab 3.2 - 3.6)
UNDER = 3.2      # deck underside
LEVELS = {'B1': ('lvB', 'lvBL'), 'B2': ('lvG', 'lvGL'), 'B3': ('lvO', 'lvOL'), 'B4': ('lvP', 'lvPL')}

# signage lettering: vector glyphs (ib_text, Inter Bold) -- see text_front / text_back / text_up below


# ================================================================ helpers
def new(pal):
    return PM(pal)


def make(name, m, ao, bevel=0.0, cols=None):
    full = PFX + name
    obj = build_object(full, m, bevel, HT, ao=ao)
    post_hull(obj, m.hmode)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, col in enumerate(cols or []):
        c, hlf = col[0], col[1]
        walk = len(col) > 2 and col[2]   # <Piece>_WCOL<n>: robots may walk on it (decks, steps, ramps)
        e = bpy.data.objects.new('%s_%sCOL%d' % (full, 'W' if walk else '', i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def cb(x0, y0, z0, x1, y1, z1, walk=False):
    """collision box from two corners (Blender coords)"""
    return (((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2), walk)


def rot_box(L, W, deg, z1, dx=0.0, dy=0.0, pad=0.04):
    """axis-aligned collision box around an L x W footprint turned deg about Z (offset dx, dy)"""
    a = math.radians(deg)
    hx = abs(math.cos(a)) * W / 2 + abs(math.sin(a)) * L / 2 + pad
    hy = abs(math.sin(a)) * W / 2 + abs(math.cos(a)) * L / 2 + pad
    return cb(dx - hx, dy - hy, 0.0, dx + hx, dy + hy, z1)


# single painted faces (no outline): front (-Y), back (+Y), up, down, -X, +X
def fq(m, x0, x1, y, z0, z1, c):
    return m.bx(x0, x1, y, y + 0.002, z0, z1, c, hull='none', cull='ktblr')


def bq(m, x0, x1, y, z0, z1, c):
    return m.bx(x0, x1, y - 0.002, y, z0, z1, c, hull='none', cull='ftblr')


def uq(m, x0, x1, y0, y1, z, c):
    return m.bx(x0, x1, y0, y1, z - 0.002, z, c, hull='none', cull='bfklr')


def dq(m, x0, x1, y0, y1, z, c):
    return m.bx(x0, x1, y0, y1, z, z + 0.002, c, hull='none', cull='tfklr')


def lq(m, x, y0, y1, z0, z1, c):
    return m.bx(x, x + 0.002, y0, y1, z0, z1, c, hull='none', cull='tbfkr')


def rq(m, x, y0, y1, z0, z1, c):
    return m.bx(x - 0.002, x, y0, y1, z0, z1, c, hull='none', cull='tbfkl')


def poly(m, pts, c, normal):
    """one flat polygon (no outline) facing `normal` (piece frame)"""
    vs = [m.bm.verts.new(m.parent @ Vector(p)) for p in pts]
    f = m.bm.faces.new(vs)
    f.normal_update()
    if f.normal.dot(m.parent.to_3x3() @ Vector(normal)) < 0:
        f.normal_flip()
    m.nshape += 1
    f[m.shape] = m.nshape
    f.material_index = m.pal.index(c)
    m.hmode[m.nshape] = 'none'
    return f


def disc(m, x, y, z, r, c, seg=12, sx=1.0, sy=1.0, jag=None, a0=0.0):
    pts = []
    for i in range(seg):
        a = a0 + i / seg * 2 * math.pi
        k = jag[i % len(jag)] if jag else 1.0
        pts.append((x + math.cos(a) * r * sx * k, y + math.sin(a) * r * sy * k, z))
    return poly(m, pts, c, (0, 0, 1))


# Lettering: real vector glyphs (ib_text, Inter Bold by default). `px` keeps the old pixel-font sizing: the cap height
# is 5 px and the word is fitted into the old (4 n - 1) px width, so every sign keeps its layout.
def _fit(word, px):
    return dict(cap=5 * px, maxw=(4 * len(word) - 1) * px * 0.95)


def text_front(m, word, px, y, xc, z0, c, font='sans'):
    """letters on a -Y facing plane at y, centred on xc, baseline z0"""
    ib_text.draw(m, word, xc, y, z0, color=c, face='y-', font=font, **_fit(word, px))


def text_back(m, word, px, y, xc, z0, c, font='sans'):
    """letters on a +Y facing plane, reading correctly from behind, centred on xc"""
    ib_text.draw(m, word, xc, y, z0, color=c, face='y+', font=font, **_fit(word, px))


def text_side(m, word, px, x, yc, z0, c, face, font='sans'):
    """letters on a +X ('x+') or -X ('x-') facing plane at x, centred on yc"""
    ib_text.draw(m, word, x, yc, z0, color=c, face=face, font=font, **_fit(word, px))


def text_up(m, word, px, z, xc, yc, c, flip=False, font='sans'):
    """letters painted on the floor, centred on (xc, yc) (reading from -Y toward +Y; flip: from +Y)"""
    ib_text.draw(m, word, xc, yc, z, color=c, face='upr' if flip else 'up', font=font, valign='m', **_fit(word, px))


def arrow_pts(L, w, head, hw, y0=0.0):
    """arrow outline in the XY plane pointing -Y (tail at y0 + L/2)"""
    t, tip = y0 + L / 2, y0 - L / 2
    return [(-w / 2, t), (w / 2, t), (w / 2, tip + head), (hw / 2, tip + head), (0, tip), (-hw / 2, tip + head), (-w / 2, tip + head)]


def floor_poly(m, pts2, z, c):
    """concave-safe floor polygon: fan from the centroid of a convex-ish outline"""
    return poly(m, [(x, y, z) for (x, y) in pts2], c, (0, 0, 1))


def arrow_floor(m, L, w, head, hw, z, c, y0=0.0):
    """painted arrow on the floor pointing -Y: shaft quad + head triangle (both convex)"""
    p = arrow_pts(L, w, head, hw, y0)
    floor_poly(m, [p[0], p[1], p[2], p[6]], z, c)
    floor_poly(m, [p[3], p[4], p[5]], z, c)


def wheel(m, x_out, y, r, w, hub='chrome', seg=10, tire='tire'):
    """wheel on the X axis whose outer face is at x_out (its sign gives the side)"""
    if x_out > 0:
        m.cy((x_out - w, y, r), r, r, w, tire, seg=seg, rot=(0, 90, 0))
        m.cy((x_out, y, r), r * 0.55, r * 0.55, 0.02, hub, seg=6, rot=(0, 90, 0), hull='none')
        m.cy((x_out + 0.02, y, r), r * 0.2, r * 0.2, 0.012, 'steelD', seg=6, rot=(0, 90, 0), hull='none')
    else:
        m.cy((x_out, y, r), r, r, w, tire, seg=seg, rot=(0, 90, 0))
        m.cy((x_out - 0.02, y, r), r * 0.55, r * 0.55, 0.02, hub, seg=6, rot=(0, 90, 0), hull='none')
        m.cy((x_out - 0.032, y, r), r * 0.2, r * 0.2, 0.012, 'steelD', seg=6, rot=(0, 90, 0), hull='none')


def chevrons(m, x0, x1, y, z0, z1, n, ca='lineY', cb_='ink', back=False):
    """yellow / black hazard blocks across a vertical plane (front -Y, or +Y with back)"""
    w = (x1 - x0) / n
    for i in range(n):
        f = bq if back else fq
        f(m, x0 + i * w, x0 + (i + 1) * w, y, z0, z1, ca if i % 2 else cb_)
