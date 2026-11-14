"""INKBOLT kit-cargoship ("Halcyon Vega", a big container ship at sea): palette and modelling helpers shared by
cargo_struct.py (walls, gate, trail, hatch, stairs, rails, deck markings), cargo_cargo.py (containers, cell guides,
lashing bridges, project cargo), cargo_deck.py (main-deck equipment), cargo_engine.py (engine room) and
cargo_backdrop.py (the superstructure tower, funnel, forecastle, lifeboats, gulls, sea glints). The family module is
fam_kit_cargoship.py.

The ship: bow to the south (game +Z), stern to the north. Zone 1 is the main deck (the bulwarks are the zone's west
and east walls, the forecastle bulkhead its south wall, the front of the superstructure its north wall); zone 2 a
cargo hold, zone 3 the engine room, both under a 13 m deckhead. Every wall module is 13 m tall (the deck zone's
bulwarks and forecastle draw only what they really are; the rest of their collision is open air nobody reaches).
Containers are ISO boxes: 40 ft = 12.0 x 2.44 x 2.6 m, 20 ft = 6.0 x 2.44 x 2.6 m, ribbed sides, door ends with
locking bars. Their colours are four paint slots (CSLOT) the theme repaints per placed stack.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front; stairs rise toward Blender +Y (game north) at yaw 0. Ceiling pieces hang from their
origin (the deckhead at 13 m). Flat detail is painted as single faces without an outline shell (PM hull='none');
details stay >= 3 mm proud of what they sit on.
"""
import math

import bpy  # noqa: F401
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb, text_front, text_back, text_side, text_up  # noqa: F401
import ib_text  # noqa: F401
import cargo_detail as D

FAM = 'kit-cargoship'
PFX = 'KIT_CARGOSHIP_'
ib_lib.GLB[FAM] = 'fps-kit-cargoship.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # hull, deck, superstructure (8 - 15)
    ('hullR', '#B23A2E'), ('hullRD', '#7C2620'), ('deckG', '#4F8A5E'), ('deckGD', '#3B6A49'),
    ('deckGL', '#7DB28A'), ('supW', '#EEF0EA'), ('supWD', '#C4CAC4'), ('supG', '#9AA6A8'),
    # steel, grime (16 - 23)
    ('steel', '#8A95A3'), ('steelD', '#4F5865'), ('steelL', '#B9C2CB'), ('galv', '#D2D8DC'),
    ('rust', '#A4532D'), ('rustD', '#6F3A22'), ('grime', '#5E5A55'), ('oil', '#3A3633'),
    # safety, lights, glass (24 - 33)
    ('yel', '#FFCF33'), ('yelD', '#D9A21C'), ('orange', '#F2681F'), ('fireR', '#D9423A'),
    ('exitG', '#25B35E'), ('signB', '#2A63CB'), ('light', '#FFF4C8'), ('day', '#FFFFF0'),
    ('glass', '#7FB9D9'), ('glassD', '#3D6E8C'),
    # machinery, hold paint, rope, wood (34 - 39)
    ('engG', '#7FA79A'), ('engGD', '#557A6E'), ('hold', '#A9B0A2'), ('holdD', '#7E8678'),
    ('rope', '#D8C48E'), ('wood', '#B98552'),
    # container colours (40 - 63): main / ribs. The first four pairs are the paint slots the models use
    ('cBlu', '#2F6CD3'), ('cBluD', '#204C96'), ('cRed', '#C8392F'), ('cRedD', '#8C2720'),
    ('cGrn', '#3C9E57'), ('cGrnD', '#296C3C'), ('cOra', '#EE7A2A'), ('cOraD', '#AE551B'),
    ('cGry', '#9AA3AC'), ('cGryD', '#6B737B'), ('cCrm', '#E3DAC4'), ('cCrmD', '#B2A890'),
    ('cYel', '#F2C230'), ('cYelD', '#B48E1C'), ('cTel', '#1F9C98'), ('cTelD', '#13706C'),
    ('cMar', '#7A2E3A'), ('cMarD', '#521E27'), ('cBrn', '#8E5C3D'), ('cBrnD', '#5E3C27'),
    ('cNav', '#2B3F6E'), ('cNavD', '#1A2848'), ('cWht', '#F1F3EF'), ('cWhtD', '#C2C7C3'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
CSLOT = [('cBlu', 'cBluD'), ('cRed', 'cRedD'), ('cGrn', 'cGrnD'), ('cOra', 'cOraD')]
TRIS = {}
HT = 0.02
H = 13.0         # deckhead (hold, engine room, stair trunks) and every wall module
HATCH = 1.8      # hatch cover tops on the main deck
WALK = 5.2       # gantry walkways (hold) and the upper flat (engine room)
FC = 3.6         # forecastle deck over the main deck
LINE = 'HALCYON'


def new(pal):
    return PM(pal)


def make(name, m, ao, bevel=0.0, cols=None, side=0.45):
    full = PFX + name
    obj = build_object(full, m, bevel, HT, ao=ao)
    post_hull(obj, m.hmode, side)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, col in enumerate(cols or []):
        c, hlf = col[0], col[1]
        walk = len(col) > 2 and col[2]   # <Piece>_WCOL<n>: robots may walk on it (stair steps)
        e = bpy.data.objects.new('%s_%sCOL%d' % (full, 'W' if walk else '', i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def at(m, x=0.0, y=0.0, z=0.0, deg=0.0):
    """set the model's parent transform (translate, then turn deg about Z); at(m) resets it"""
    m.parent = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


def tube(m, a, b, r, c, seg=8, hull='full'):
    """cylinder from point a to point b"""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    old = m.parent
    m.parent = old @ Matrix.Translation(a) @ q.to_matrix().to_4x4()
    m.cy((0, 0, 0), r, r, d.length, c, seg=seg, hull=hull)
    m.parent = old


def rail_run(m, x0, x1, y, z0, h=1.05, c='yel', post=1.0, toe=True, posts=True, foot=False):
    """guard rail along X at y: posts, a top and a knee rail (and a toe board)"""
    L = x1 - x0
    m.bx(x0, x1, y - 0.03, y + 0.03, z0 + h - 0.05, z0 + h, c, hull='noside' if L > 0.95 else 'full')
    m.bx(x0, x1, y - 0.02, y + 0.02, z0 + h * 0.52, z0 + h * 0.52 + 0.04, c, hull='none')
    if toe:
        m.bx(x0, x1, y - 0.01, y + 0.01, z0, z0 + 0.12, c, hull='none', cull='b')
    if posts:
        n = max(1, int(round(L / post)))
        for k in range(n + 1 if L < 0.95 else n):
            px = x0 + (k + 0.5) * L / n if L >= 0.95 else x0 + k * L / n
            m.bx(px - 0.025, px + 0.025, y - 0.025, y + 0.025, z0, z0 + h - 0.05, c, hull='none', cull='bt')
            if foot:
                D.post_foot(m, px, y, z0, x0, x1)


def rail_y(m, x, y0, y1, z0, h=1.05, c='yel', post=1.0, toe=True):
    """guard rail along Y at x"""
    L = y1 - y0
    m.bx(x - 0.03, x + 0.03, y0, y1, z0 + h - 0.05, z0 + h, c)
    m.bx(x - 0.02, x + 0.02, y0, y1, z0 + h * 0.52, z0 + h * 0.52 + 0.04, c, hull='none')
    if toe:
        m.bx(x - 0.01, x + 0.01, y0, y1, z0, z0 + 0.12, c, hull='none', cull='b')
    n = max(1, int(round(L / post)))
    for k in range(n + 1):
        py = y0 + k * L / n
        py = min(max(py, y0 + 0.03), y1 - 0.03)
        m.bx(x - 0.025, x + 0.025, py - 0.025, py + 0.025, z0, z0 + h - 0.05, c, hull='none', cull='bt')


def ladder(m, x, y, z0, z1, w=0.45, c='yel', face=-1, cage=False, brk=True, emb=0.003):
    """vertical ladder standing off a wall: stiles and rungs (face -1: in front of a -Y facing wall at y)"""
    yo = y + face * 0.16
    for sx in (-1, 1):
        m.bx(x + sx * w / 2 - 0.025, x + sx * w / 2 + 0.025, yo - 0.03, yo + 0.03, z0, z1, c)
        m.bx(x + sx * w / 2 - 0.02, x + sx * w / 2 + 0.02, min(y, yo), max(y, yo), z1 - 0.3, z1 - 0.25, c, hull='none', cull='kf')
    if brk:
        D.ladder_brackets(m, x, y, z0, z1, w, face, emb)
    n = int((z1 - z0) / 0.3)
    for k in range(1, n):
        z = z0 + k * 0.3
        m.bx(x - w / 2 + 0.025, x + w / 2 - 0.025, yo - 0.015, yo + 0.015, z - 0.015, z + 0.015, c, hull='none',
             cull='blr' + ('k' if face < 0 else 'f'))
    if cage:
        y0c, y1c = sorted((yo + face * 0.62, yo + face * 0.66))
        ys0, ys1 = sorted((yo, yo + face * 0.66))
        for z in [z0 + 2.4 + k * 2.1 for k in range(int((z1 - z0 - 2.4) / 2.1) + 1)]:
            if z > z1:
                break
            m.bx(x - w / 2 - 0.06, x + w / 2 + 0.06, y0c, y1c, z, z + 0.05, c, hull='none', cull='b')
            for sx in (-1, 1):
                a0, a1 = sorted((x + sx * (w / 2 + 0.06), x + sx * (w / 2 + 0.1)))
                m.bx(a0, a1, ys0, ys1, z + 0.004, z + 0.046, c, hull='none', cull='b' + ('k' if face < 0 else 'f'))
        for sx in (-1, 0, 1):
            xx = x + sx * (w / 2 + 0.03)
            m.bx(xx - 0.015, xx + 0.015, y0c - 0.02, y0c + 0.01, z0 + 2.42, z1, c, hull='none')


def hazard(m, x0, x1, y, z0, z1, n, back=False, ca='yel', cb_='ink'):
    """yellow / black hazard blocks across a vertical plane facing -Y (or +Y with back)"""
    w = (x1 - x0) / n
    f = bq if back else fq
    for i in range(n):
        f(m, x0 + i * w, x0 + (i + 1) * w, y, z0, z1, ca if i % 2 else cb_)


def hazard_up(m, x0, x1, y0, y1, z, n, ca='yel', cb_='ink'):
    """hazard blocks across a floor patch (stripes along Y)"""
    w = (x1 - x0) / n
    for i in range(n):
        uq(m, x0 + i * w, x0 + (i + 1) * w, y0, y1, z, ca if i % 2 else cb_)


def sign(m, x, y, z, w, h, word, bg='signB', fg='paper', px=None, back=False):
    """flat plaque with lettering on a -Y facing plane at y (or +Y with back)"""
    s = -1 if not back else 1
    (bq if back else fq)(m, x - w / 2, x + w / 2, y, z, z + h, bg)
    px = px or min(h * 0.12, (w * 0.9) / max(1, 4 * len(word) - 1) / 0.95)
    (text_back if back else text_front)(m, word, px, y + s * 0.003, x, z + (h - 5 * px) / 2, fg)


def porthole(m, x, y, z, r=0.22, c='glassD', rim='steelL', face=-1, seg=10):
    """round window on a -Y (face -1) or +Y facing wall at y"""
    m.cy((x, y + face * 0.004, z), r + 0.05, r + 0.05, 0.004, rim, seg=seg, rot=(90, 0, 0), hull='none')
    m.cy((x, y + face * 0.008, z), r, r, 0.004, c, seg=seg, rot=(90, 0, 0), hull='none')
