"""INKBOLT asset family: kit-mall ("Galleria", a two-storey shopping mall under a glazed roof).

Storefronts: every wall cell stacks a ground-floor and an upper-floor shopfront module (the theme's wall chooser
returns both). Six colour brands per storey = twelve shops (SHOPS: Atelier, Signal, The Coffee House, Northfield Books,
Toy Workshop, Aurum / Shoe Gallery, Lumen Optics, Bakehouse, Hearth & Home, Field & Court (closed, shutters down),
Leatherworks), each name in real vector lettering (ib_text: serif, script, display, condensed or sans) across the three
middle modules of a 5 m bay, monogram roundels, awnings or light boxes, blade signs and a
lit interior you see through the (open, glint-marked) shop windows: mannequins, shelves, counters, books, toys,
display cases. Sandstone pilasters with sconces part the bays; corner blocks and pilasters close the interiors.
Circulation: a steel-and-glass escalator (stair-block collision kept), baluster railings (half modules the engine
links into runs), columns under / over the mezzanine edge, a framed glass lift shaft, a cab and sliding door leaves
(the engine moves cab and leaves). Atrium: tiered fountain, round Guest Services desk with lettered drums, coffee / sweets
/ gadget kiosks, food-court tables and food stalls, palm planters, flower planters, benches, bins, directory totems,
department-store podiums. Floor inlays (an "@layer 0" grid: diamonds, border bands, compass-rose medallions, food-court
checker, entrance mats) and the roof (an "@layer 9.5" grid: glazed coffers, lattice trusses with hanging banners and
pendant lamps, downlights), plus under-deck downlights ("@layer 4.5"). Gate portal with GALLERIA lettering, corridor
walls, hatch. Walk-in shops: open-front variants of the storefronts (WinAW / OpenL / OpenC / OpenR / WinBW: display beds,
a 3 m doorway under the sign band, the room-side face of the wall line) and one furnished 5 x 6 m room per shop
(mall_rooms.py: floor finish, walls, ceiling with light panels, staff door, cash desk, the shop's fittings, collision
cut per fitting).

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front. Decks stand at 4.5 m (slab 4.1-4.5); the ceiling is at 9.5 m. Ceiling pieces hang from
their origin (the ceiling plane). Flat detail is painted as single faces without an outline shell (PM hull='none').
"""
import math

import bpy  # noqa: F401
import bmesh
from mathutils import Vector, Matrix

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull
import ib_text  # noqa: F401
from ib_text import draw as txt

FAM = 'kit-mall'
PFX = 'KIT_MALL_'
ib_lib.GLB[FAM] = 'fps-kit-mall.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # structure
    ('stone', '#EBDCC3'), ('stone2', '#D4BB96'), ('cream', '#F8F1E3'), ('marble', '#EFE4D0'),
    ('terra', '#D06A4B'), ('terraD', '#A84E3A'), ('tealM', '#2E9E95'), ('tealD', '#1E6C72'),
    ('navy', '#2D406E'), ('gold', '#F0B840'), ('brass', '#C99A3B'), ('chrome', '#CDD5DE'),
    ('steel', '#8592A3'), ('dark', '#38343F'), ('sign', '#2A2635'), ('step', '#4B4957'),
    ('rubber', '#24222B'), ('glass', '#9FD4EE'), ('glassL', '#DDF2FA'), ('skyglass', '#A8DCF6'),
    ('light', '#FFF2C2'), ('lightW', '#FFFBEC'), ('water', '#62BFE6'), ('waterL', '#C4EBF8'),
    # materials
    ('wood', '#C48A57'), ('wood2', '#94643F'), ('woodL', '#E0B888'), ('leaf', '#4FAE63'),
    ('leaf2', '#33874C'), ('leafL', '#86CF72'), ('soil', '#6B4D3A'), ('skin', '#EADFCF'),
    # brands
    ('rose', '#EE6F8C'), ('roseL', '#FAD0DA'), ('sky', '#4E9CE6'), ('skyL', '#D6E9FA'),
    ('orange', '#F28A3C'), ('orangeL', '#FFE0B8'), ('mint', '#3FBF98'), ('mintL', '#CDF1E2'),
    ('yellow', '#FFD447'), ('yellowL', '#FFF1B8'), ('violet', '#9670D8'), ('violetD', '#4D3A78'),
    ('intD', '#3B3F4E'), ('redT', '#E2453F'), ('blueT', '#3A6FD8'), ('greenT', '#5DBB4A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
TRIS = {}
HT = 0.02
H = 9.5          # wall / ceiling height
DECK = 4.5       # mezzanine floor (slab 4.1 - 4.5)


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
        walk = len(col) > 2 and col[2]   # <Piece>_WCOL<n>: robots may walk on it (decks, steps)
        e = bpy.data.objects.new('%s_%sCOL%d' % (full, 'W' if walk else '', i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def col_box(x0, y0, z0, x1, y1, z1, walk=False):
    return (((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2), walk)


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
    """one flat polygon (no outline) facing `normal`"""
    vs = [m.bm.verts.new(m.parent @ Vector(p)) for p in pts]
    f = m.bm.faces.new(vs)
    f.normal_update()
    if f.normal.dot(Vector(normal)) < 0:
        f.normal_flip()
    m.nshape += 1
    f[m.shape] = m.nshape
    f.material_index = m.pal.index(c)
    m.hmode[m.nshape] = 'none'
    return f


def glint(m, x0, x1, y, z0, z1, c='glassL'):
    """two slanted highlight streaks on a glass plane (front-facing at y)"""
    w, h = x1 - x0, z1 - z0
    s = min(0.3 * h, w * 0.4)
    for a, b in ((0.1, 0.13), (0.34, 0.05)):
        xa, bw = x0 + w * a, w * b
        poly(m, [(xa, y, z0 + h * 0.25), (xa + bw, y, z0 + h * 0.25), (xa + bw + s, y, z0 + h * 0.25 + s * 1.6), (xa + s, y, z0 + h * 0.25 + s * 1.6)], c, (0, -1, 0))


def disc(m, x, y, z, r, c, seg=12, up=True):
    """flat disc facing up (or down)"""
    pts = [(x + math.cos(i / seg * 2 * math.pi) * r, y + math.sin(i / seg * 2 * math.pi) * r, z) for i in range(seg)]
    return poly(m, pts, c, (0, 0, 1 if up else -1))


def vdisc(m, ctr, r, c, facing, seg=10):
    """flat vertical disc facing 'x+', 'x-', 'y+' or 'y-'"""
    x, y, z = ctr
    pts = []
    for i in range(seg):
        a = i / seg * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        pts.append((x, y + u, z + v) if facing[0] == 'x' else (x + u, y, z + v))
    n = {'x+': (1, 0, 0), 'x-': (-1, 0, 0), 'y+': (0, 1, 0), 'y-': (0, -1, 0)}[facing]
    return poly(m, pts, c, n)


def annulus(m, z, r0, r1, c, seg=16):
    """flat ring facing up"""
    for i in range(seg):
        a0, a1 = i / seg * 2 * math.pi, (i + 1) / seg * 2 * math.pi
        poly(m, [(math.cos(a0) * r0, math.sin(a0) * r0, z), (math.cos(a0) * r1, math.sin(a0) * r1, z),
                 (math.cos(a1) * r1, math.sin(a1) * r1, z), (math.cos(a1) * r0, math.sin(a1) * r0, z)], c, (0, 0, 1))


# ---------------------------------------------------------------- lettering: vector glyphs (ib_text: Bebas Neue,
# Oswald, Playfair Display, Pacifico, Inter Bold; SIL OFL fonts under third_party/fonts), painted flat >= 3 mm proud;
# merchandise helpers for the window displays


# ---- detail helpers (tactical look Stage 11): finish and fittings, never grime. Same rules as kit_base's helpers: every part is
# hull='none' (no outline shell), stands at least 3 mm proud of its face and starts 3 mm inside it, horizontal runs stop 5 mm
# short of the piece's sides. `s` is the face direction: -1 looks toward Blender -Y (the module front), +1 toward +Y.
PROUD, EMBED = 0.004, 0.003


def _yr(yf, d, s):
    return (yf - d, yf + EMBED) if s < 0 else (yf - EMBED, yf + d)


def dbx(m, x0, x1, yf, d, z0, z1, c, s=-1, cull=''):
    y0, y1 = _yr(yf, d, s)
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def d_base(m, x0, x1, yf, c, h=0.09, d=0.018, z0=0.0, s=-1):
    dbx(m, x0 + 0.005, x1 - 0.005, yf, d, z0 + 0.004, z0 + h, c, s)


def d_cap(m, x0, x1, yf, ztop, c, h=0.07, d=0.03, s=-1):
    dbx(m, x0 + 0.005, x1 - 0.005, yf, d, ztop - h, ztop - 0.004, c, s)


def d_kick(m, x0, x1, yf, c, h=0.24, z0=0.0, d=0.008, s=-1):
    dbx(m, x0 + 0.005, x1 - 0.005, yf, d, z0 + 0.004, z0 + h, c, s)


def d_guard(m, x, yf, z0, z1, c, w=0.05, t=0.008, side=1, s=-1):
    """L-angle strip on a vertical corner at x (side +1: runs inward from x toward -x, -1: toward +x)."""
    a, b = (x - w, x - 0.004) if side > 0 else (x + 0.004, x + w)
    dbx(m, a, b, yf, t, z0, z1, c, s)


def d_seams(m, x0, x1, yf, z0, z1, every, c, t=0.014, s=-1):
    n = max(1, int(round((x1 - x0) / every)))
    for i in range(1, n):
        x = x0 + (x1 - x0) * i / n
        dbx(m, x - t / 2, x + t / 2, yf, PROUD, z0, z1, c, s)


def d_vent(m, x, z, yf, w, h, frame_c, slat_c, s=-1):
    n = max(3, int(h / 0.06))
    for zz0, zz1 in ((z - h / 2, z - h / 2 + 0.03), (z + h / 2 - 0.03, z + h / 2)):
        dbx(m, x - w / 2, x + w / 2, yf, 0.012, zz0, zz1, frame_c, s)
    for xx0, xx1 in ((x - w / 2, x - w / 2 + 0.03), (x + w / 2 - 0.03, x + w / 2)):
        dbx(m, xx0, xx1, yf, 0.012, z - h / 2 + 0.034, z + h / 2 - 0.034, frame_c, s)
    for i in range(n):
        zz = z - h / 2 + 0.04 + (h - 0.08) * (i + 0.5) / n
        y0, y1 = (yf - 0.009, yf - PROUD) if s < 0 else (yf + PROUD, yf + 0.009)
        m.bx(x - w / 2 + 0.034, x + w / 2 - 0.034, y0, y1, zz - 0.008, zz + 0.008, slat_c, hull='none')


def d_frame(m, x0, x1, z0, z1, yf, c, depth=0.06, t=0.03, top=True, s=-1):
    """A frame standing out round a board / opening, so it reads with depth."""
    if top:
        dbx(m, x0 - t, x1 + t, yf, depth, z1 - 0.003, z1 + t, c, s)
    dbx(m, x0 - t, x1 + t, yf, depth, z0 - t, z0 + 0.003, c, s)
    dbx(m, x0 - t, x0 + 0.003, yf, depth, z0 + 0.004, z1 - 0.004, c, s)
    dbx(m, x1 - 0.003, x1 + t, yf, depth, z0 + 0.004, z1 - 0.004, c, s)


def front_trims(m, S, sill):
    """shopfront finish: brass drip under and a cap over the sign band, a chrome sill + skirting on the glazing"""
    d_cap(m, -0.5, 0.5, -0.6, S['s0'] + 0.02, 'brass', h=0.04, d=0.025)
    d_cap(m, -0.5, 0.5, -0.6, S['s1'] + 0.02, 'brass', h=0.04, d=0.025)
    if sill:
        dbx(m, -0.495, 0.495, -0.56, 0.02, S['kick'] - 0.003, S['kick'] + 0.02, 'chrome')
        d_base(m, -0.5, 0.5, -0.56, 'chrome', h=0.06, d=0.012, z0=S['z0'])


def shoe(m, x, y, z, c, heel=False):
    """one shoe, toe toward -X: sole, vamp, collar (or a stiletto heel)"""
    m.bx(x - 0.12, x + 0.12, y - 0.04, y + 0.04, z, z + 0.022, 'paper' if c != 'paper' else 'dark', hull='none')
    if heel:
        m.bx(x - 0.1, x + 0.03, y - 0.035, y + 0.035, z + 0.022, z + 0.06, c, hull='none')
        m.bx(x + 0.03, x + 0.12, y - 0.035, y + 0.035, z + 0.09, z + 0.12, c, hull='none')
        m.bx(x + 0.09, x + 0.11, y - 0.012, y + 0.012, z + 0.022, z + 0.09, 'dark', hull='none')
    else:
        m.bx(x - 0.11, x + 0.03, y - 0.038, y + 0.038, z + 0.022, z + 0.07, c, hull='none')
        m.bx(x + 0.03, x + 0.115, y - 0.038, y + 0.038, z + 0.022, z + 0.12, c, hull='none')


def bag(m, x, y, z, c, w=0.22, h=0.18, strap='dark'):
    """handbag: trapezoid body and an arched handle"""
    m.prism([(y - 0.05, z), (y + 0.05, z), (y + 0.04, z + h), (y - 0.04, z + h)], x - w / 2, x + w / 2, [c], hull='none')
    t = z + h + 0.1   # the two halves of the handle on planes 1 cm apart (no coplanar overlap at the top)
    m.bm_((x - w * 0.3, y - 0.005, z + h), (x, y - 0.005, t), 0.015, strap, hull='none')
    m.bm_((x, y + 0.005, t), (x + w * 0.3, y + 0.005, z + h), 0.015, strap, hull='none')


def cake(m, x, y, z, r, c, top='cream', h=0.1):
    m.cy((x, y, z), r, r, h, c, seg=7, hull='none', caps=False)
    m.cy((x, y, z + h), r * 1.02, r * 1.02, 0.02, top, seg=7, hull='none')


def plant(m, x, y, z, s=1.0, pot='terra'):
    m.cy((x, y, z), 0.09 * s, 0.12 * s, 0.2 * s, pot, seg=8, hull='none')
    m.sp((x, y, z + 0.38 * s), 0.2 * s, 'leaf', seg=(6, 4), hull='none')
    m.sp((x + 0.08 * s, y - 0.04, z + 0.52 * s), 0.12 * s, 'leafL', seg=(5, 3), hull='none')


# ================================================================ storefronts
LO = dict(z0=0.0, kick=0.25, wtop=3.0, s0=3.1, s1=3.75, top=4.1, ceil=3.1, dtop=2.45)
UP = dict(z0=4.5, kick=4.7, wtop=7.3, s0=7.4, s1=8.1, top=9.5, ceil=7.4, dtop=6.95)
# brand: (name, sign band, letter colour, frame, interior floor, interior wall, awning stripes or None)
BRANDS = {
    'rose': ('STYLE', 'rose', 'paper', 'dark', 'woodL', 'roseL', None),
    'sky': ('TECH', 'sky', 'paper', 'chrome', 'cream', 'skyL', None),
    'orange': ('CAFE', 'orange', 'paper', 'wood2', 'wood', 'orangeL', ('orange', 'cream')),
    'mint': ('BOOKS', 'tealD', 'mintL', 'tealD', 'woodL', 'mintL', ('mint', 'cream')),
    'gold': ('TOYS', 'yellow', 'redT', 'blueT', 'cream', 'yellowL', ('redT', 'yellow')),
    'violet': ('GEMS', 'violetD', 'gold', 'brass', 'intD', 'violetD', None),
}
# shop identity per (brand, storey): name, font (ib_text), cap height, sign band colour, letter colour, drop shadow,
# closed (roller shutters down, "Closed" plate). Generic descriptive names: no real or parody brands.
SHOPS = {
    ('rose', 'Lo'): dict(name='Atelier', font='serif', cap=0.34, band='sign', lc='roseL'),
    ('sky', 'Lo'): dict(name='SIGNAL', font='display', cap=0.38, band='sky', lc='paper', sh='navy'),
    ('orange', 'Lo'): dict(name='The Coffee House', font='script', cap=0.22, band='orange', lc='paper', sh='terraD'),
    ('mint', 'Lo'): dict(name='Northfield Books', font='serif', cap=0.27, band='tealD', lc='mintL'),
    ('gold', 'Lo'): dict(name='TOY WORKSHOP', font='display', cap=0.38, band='yellow', lc='redT', sh='blueT'),
    ('violet', 'Lo'): dict(name='Aurum', font='serif', cap=0.36, band='violetD', lc='gold'),
    ('rose', 'Up'): dict(name='Shoe Gallery', font='cond', cap=0.34, band='cream', lc='rose'),
    ('sky', 'Up'): dict(name='Lumen Optics', font='sans', cap=0.28, band='navy', lc='skyL'),
    ('orange', 'Up'): dict(name='Bakehouse', font='script', cap=0.25, band='sign', lc='orangeL'),
    ('mint', 'Up'): dict(name='Hearth & Home', font='serif', cap=0.3, band='cream', lc='tealD'),
    ('gold', 'Up'): dict(name='FIELD & COURT', font='display', cap=0.38, band='navy', lc='yellow', closed=True),
    ('violet', 'Up'): dict(name='Leatherworks', font='script', cap=0.24, band='sign', lc='roseL'),
}
POS = ['WinA', 'SignL', 'Door', 'SignR', 'WinB']   # k = 1..5 in a bay (the theme mirrors L / R on N and E faces)
GY = -0.40      # glass line (glints); interiors start behind it
BACK = 2.2      # interior back wall


def initial(shop):
    n = shop['name']
    return (n[4:] if n.startswith('The ') else n)[0]


def shop_front(m, brand, pos, S):
    _w, _b, _l, frame, flo, wall, awn = BRANDS[brand]
    shop = SHOPS[(brand, 'Lo' if S is LO else 'Up')]
    band, lc, closed = shop['band'], shop['lc'], shop.get('closed', False)
    if S is UP:
        awn = None
    z0, kick, wtop, s0, s1, top, ceil = S['z0'], S['kick'], S['wtop'], S['s0'], S['s1'], S['top'], S['ceil']
    door = pos == 'Door'
    # frame: mullion halves at the module edges (they pair up with the neighbours), transom, kick plate
    for sx in (-1, 1):
        m.bx(sx * 0.5 - (0.04 if sx > 0 else 0), sx * 0.5 + (0.04 if sx < 0 else 0), -0.54, -0.37, z0, wtop, frame, hull='none', cull='ktb' + ('r' if sx > 0 else 'l'))
    m.bx(-0.5, 0.5, -0.545, -0.37, wtop, s0, frame, hull='none', cull='klrt')
    if not door and not closed:
        m.bx(-0.5, 0.5, -0.56, -0.37, z0, kick, 'stone2', hull='none', cull='kblr')
        glint(m, -0.42, 0.42, GY, kick, wtop)
        # window vinyl: a short line of script on the glass
    # sign band and the shop name (spans SignL / Door / SignR: bay x -1.5 .. 1.5, clipped per module)
    m.bx(-0.5, 0.5, -0.6, -0.37, s0, s1, band, hull='noside', cull='klrt')
    front_trims(m, S, not door and not closed)
    if S is LO and pos == 'WinB':   # a louvred vent grille in the bulkhead stone
        d_vent(m, 0.0, (s1 + top) / 2, -0.5, 0.36, 0.2, 'stone2', 'steel')
    zm = (s0 + s1) / 2
    if pos in ('SignL', 'Door', 'SignR'):
        off = {'SignL': -1.0, 'Door': 0.0, 'SignR': 1.0}[pos]
        txt(m, shop['name'], -off, -0.604, zm, shop['cap'], lc, font=shop['font'], valign='m', maxw=2.7,
            clip=(-0.5 + off, 0.5 + off), shadow=shop.get('sh'), shadow_off=(0.05, -0.07))
    else:   # monogram roundel at the bay ends
        vdisc(m, (0, -0.604, zm), 0.22, lc, 'y-', seg=14)
        txt(m, initial(shop), 0.0, -0.608, zm, 0.2, band, font='display', valign='m', maxw=0.3)
    if closed:   # roller shutter down over the window / door, a "Closed" plate on it
        top_ = wtop if not door else S['dtop']
        m.bx(-0.5, 0.5, -0.56, -0.5, top_ - 0.18, wtop, 'dark', hull='noside', cull='klr')
        n = int((top_ - 0.18 - z0) / 0.12)
        for i in range(n):
            fq(m, -0.5, 0.5, -0.53, z0 + i * (top_ - 0.18 - z0) / n, z0 + (i + 1) * (top_ - 0.18 - z0) / n - 0.012, 'steel' if i % 2 else 'chrome')
        m.bx(-0.5, 0.5, -0.545, -0.53, z0, z0 + 0.08, 'dark', hull='none', cull='kb')
        if pos == 'Door':
            zc = z0 + 1.45
            fq(m, -0.3, 0.3, -0.534, zc - 0.17, zc + 0.17, 'paper')
            txt(m, 'Closed', 0.0, -0.538, zc - 0.02, 0.1, 'redT', font='script', maxw=0.5)
            txt(m, 'OPENING SOON', 0.0, -0.538, zc - 0.12, 0.045, 'ink', font='cond', maxw=0.5)
    # bulkhead (ground) / cornice with a gold frieze (upper)
    if top - s1 > 0.5:
        fq(m, -0.5, 0.5, -0.5, s1, top, 'stone')
        for i in range(4):
            fq(m, -0.44 + i * 0.25, -0.31 + i * 0.25, -0.503, s1 + 0.35, s1 + 0.48, 'gold')
        m.bx(-0.5, 0.5, -0.62, -0.5, top - 0.6, top - 0.38, 'stone2', hull='noside', cull='klr')
        m.bx(-0.5, 0.5, -0.56, -0.5, top - 0.16, top, 'cream', hull='noside', cull='ktlr')
    else:
        fq(m, -0.5, 0.5, -0.5, s1, top, 'stone')
    # awning (striped fabric) under the sign on the windows, or a blade sign at the bay's left end
    if awn and not door:
        prof = [(-0.37, wtop + 0.02), (-1.12, wtop - 0.4), (-1.12, wtop - 0.6), (-0.37, wtop - 0.06)]
        m.prism(prof, -0.5, 0.5, [awn[0], awn[1]], hull='noside')
    elif pos == 'WinA':   # blade sign over the window, readable down the concourse
        zb = wtop - 0.45
        m.bx(-0.43, -0.4, -1.0, -0.37, zb + 0.3, zb + 0.36, 'dark', hull='none')
        m.bx(-0.44, -0.39, -0.95, -0.42, zb - 0.3, zb + 0.3, band, hull='full')
        vdisc(m, (-0.386, -0.685, zb), 0.17, lc, 'x+', seg=12)
        vdisc(m, (-0.444, -0.685, zb), 0.17, lc, 'x-', seg=12)
        txt(m, initial(shop), -0.382, -0.685, zb, 0.17, band, face='x+', font='display', valign='m', maxw=0.24)
        txt(m, initial(shop), -0.448, -0.685, zb, 0.17, band, face='x-', font='display', valign='m', maxw=0.24)
    # interior shell: floor, back wall, ceiling with a light strip
    uq(m, -0.5, 0.5, -0.37, BACK, z0 + 0.012, flo)
    fq(m, -0.5, 0.5, BACK, z0, ceil, wall)
    dq(m, -0.5, 0.5, -0.37, BACK, ceil, 'cream')
    dq(m, -0.5, 0.5, 0.5, 0.7, ceil - 0.004, 'lightW')
    if closed:
        return
    if door:
        door_leaves(m, S, frame)
    else:
        m.bx(-0.5, 0.5, -0.37, 0.15, z0, kick - 0.01, 'cream', hull='none', cull='kblr')   # window plinth
    n0 = m.nshape
    contents(m, brand, pos, S)
    for k in range(n0 + 1, m.nshape + 1):   # shop contents seen through the glass: no outline shells
        m.hmode[k] = 'none'


# ---------------------------------------------------------------- walk-in shop fronts (a room behind, mall_rooms.py)
# The bay's two windows keep their glass with a display bed that fills the cell (the room-side face of the wall line is
# drawn); the three middle modules open below the transom (OpenL / OpenC / OpenR: a 3 m doorway, the engine's
# wall.passage keeps only the lintel solid) under the shop's sign band.
POS_W = ['WinAW', 'OpenL', 'OpenC', 'OpenR', 'WinBW']
# room look per (brand, storey): floor, floor accent, walls, trim (mall_rooms.py uses the same)
ROOM = {
    ('rose', 'Lo'): ('woodL', 'wood', 'roseL', 'rose'), ('sky', 'Lo'): ('paper', 'skyL', 'skyL', 'navy'),
    ('orange', 'Lo'): ('wood', 'wood2', 'orangeL', 'orange'), ('mint', 'Lo'): ('woodL', 'wood', 'mintL', 'tealD'),
    ('gold', 'Lo'): ('cream', 'yellow', 'yellowL', 'blueT'), ('violet', 'Lo'): ('intD', 'sign', 'violetD', 'gold'),
    ('rose', 'Up'): ('cream', 'roseL', 'roseL', 'rose'), ('sky', 'Up'): ('skyL', 'paper', 'paper', 'navy'),
    ('orange', 'Up'): ('terra', 'cream', 'cream', 'orange'), ('mint', 'Up'): ('wood', 'wood2', 'mintL', 'tealD'),
    ('violet', 'Up'): ('wood2', 'wood', 'orangeL', 'violetD'),
}
RH = 3.4        # room ceiling above its floor (both storeys); the front's room face runs a little past it


def walk_display(m, brand, tag, pos, bt):
    """one or two pieces of the shop's stock on a window's display bed (top bt)"""
    a = pos == 'WinAW'
    y = -0.05
    if tag == 'Lo':
        if brand == 'rose':
            figure(m, 0.0, y, bt, 'rose' if a else 'navy', legs='cream' if a else 'dark')
        elif brand == 'sky':
            for i, x in enumerate((-0.2, 0.2)):
                m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, bt, bt + 0.35, 'chrome', hull='none')
                m.bx(x - 0.1, x + 0.1, y - 0.04, y - 0.02, bt + 0.3, bt + 0.66, 'dark', hull='none')
                fq(m, x - 0.085, x + 0.085, y - 0.043, bt + 0.32, bt + 0.64, 'sky' if i else 'blueT')
        elif brand == 'orange':
            m.cy((0, y, bt), 0.03, 0.03, 0.55, 'chrome', seg=6, hull='none')
            for i, r in enumerate((0.26, 0.18)):
                zz = bt + 0.2 + i * 0.3
                m.cy((0, y, zz), r, r, 0.015, 'paper', seg=10, hull='none')
                cake(m, 0.0, y, zz + 0.015, r * 0.6, ('roseL', 'woodL')[i], h=0.08)
        elif brand == 'mint':
            for k, w in enumerate((0.4, 0.28, 0.16)):
                m.bx(-w, w, -0.2, 0.15, bt + k * 0.16, bt + (k + 1) * 0.16 - 0.005, ('redT', 'navy', 'gold')[k], hull='none', cull='b')
        elif brand == 'gold':
            if a:
                m.sp((0, y, bt + 0.3), 0.28, 'wood', seg=(7, 4))
                m.sp((0, y - 0.02, bt + 0.74), 0.2, 'wood', seg=(7, 4))
                for sx in (-1, 1):
                    m.sp((sx * 0.15, y, bt + 0.9), 0.07, 'wood2', seg=(6, 4), hull='none')
                m.sp((0, y - 0.19, bt + 0.7), 0.065, 'woodL', seg=(6, 4), hull='none')
            else:
                for i, (x, c) in enumerate(((-0.22, 'redT'), (0.0, 'blueT'), (0.22, 'greenT'))):
                    m.bx(x - 0.1, x + 0.1, y - 0.1, y + 0.1, bt, bt + 0.2 + 0.1 * i, c, hull='full', cull='b')
        elif brand == 'violet':
            m.cy((0.0, y, bt), 0.15, 0.15, 0.6, 'paper', seg=8)
            m.prism([(y - 0.1, bt + 0.6), (y + 0.1, bt + 0.6), (y + 0.05, bt + 1.0), (y - 0.05, bt + 1.0)], -0.12, 0.12, ['sign'])
            m.cy((0.0, y - 0.105, bt + 0.85), 0.09, 0.09, 0.02, 'gold', seg=8, rot=(90, 0, 0), hull='none')
    else:
        if brand == 'rose':
            for i, (x, h, c) in enumerate(((-0.25, 0.15, 'paper'), (0.0, 0.35, 'roseL'), (0.25, 0.05, 'cream'))):
                m.bx(x - 0.11, x + 0.11, -0.15, 0.1, bt, bt + h, c, hull='none', cull='b')
                shoe(m, x, -0.07, bt + h, ('rose', 'dark', 'gold')[i], heel=(i != 1))
                shoe(m, x, 0.03, bt + h, ('rose', 'dark', 'gold')[i], heel=(i != 1))
        elif brand == 'sky':
            for sx in (-1, 1):
                m.cy((sx * 0.17, y, bt + 0.9), 0.15, 0.15, 0.03, 'dark', seg=12, rot=(90, 0, 0), hull='none')
                m.cy((sx * 0.17, y - 0.015, bt + 0.9), 0.12, 0.12, 0.005, 'glassL', seg=12, rot=(90, 0, 0), hull='none')
            m.bx(-0.04, 0.04, y - 0.02, y + 0.02, bt + 0.94, bt + 0.97, 'dark', hull='none')
            m.bx(-0.015, 0.015, y - 0.01, y + 0.02, bt, bt + 0.75, 'chrome', hull='none')
        elif brand == 'orange':
            m.cy((0, y, bt), 0.03, 0.03, 0.7, 'chrome', seg=6, hull='none')
            for i, r in enumerate((0.3, 0.22, 0.15)):
                zz = bt + 0.15 + i * 0.25
                m.cy((0, y, zz), r, r, 0.015, 'paper', seg=12, hull='none')
                cake(m, 0.0, y, zz + 0.015, r * 0.6, ('roseL', 'woodL', 'orangeL')[i], h=0.08)
        elif brand == 'mint':
            plant(m, -0.2, y, bt, 1.4)
            m.cy((0.25, y, bt), 0.12, 0.12, 0.45, 'wood', seg=8, hull='none')
            m.cy((0.25, y, bt + 0.45), 0.06, 0.09, 0.3, 'tealM', seg=8, hull='none')
        elif brand == 'violet':
            for i, (x, h) in enumerate(((-0.22, 0.4), (0.22, 0.2))):
                m.cy((x, y, bt), 0.13, 0.13, h, 'paper', seg=10, hull='none')
                bag(m, x, y, bt + h, ('wood', 'redT')[i], w=0.26, h=0.2)


def shop_front_walk(m, brand, pos, S):
    _w, _b, _l, frame, flo, wall, awn = BRANDS[brand]
    tag = 'Lo' if S is LO else 'Up'
    shop = SHOPS[(brand, tag)]
    band, lc = shop['band'], shop['lc']
    if S is UP:
        awn = None
    z0, kick, wtop, s0, s1, top = S['z0'], S['kick'], S['wtop'], S['s0'], S['s1'], S['top']
    rw, trim = ROOM[(brand, tag)][2], ROOM[(brand, tag)][3]
    win = pos in ('WinAW', 'WinBW')
    rt = z0 + RH + 0.05        # the room-side face of the wall line runs just past the room ceiling
    # frame: mullion halves where a window meets its neighbour (doorways keep only the outer jambs)
    for sx in (-1, 1):
        outer = (pos == 'OpenL' and sx < 0) or (pos == 'OpenR' and sx > 0)
        if win or outer:
            m.bx(sx * 0.5 - (0.04 if sx > 0 else 0), sx * 0.5 + (0.04 if sx < 0 else 0), -0.54, -0.37, z0, wtop, frame, hull='none', cull='ktb' + ('r' if sx > 0 else 'l'))
    m.bx(-0.5, 0.5, -0.545, -0.37, wtop, s0, frame, hull='none', cull='klrt' + ('' if win else 'b'))
    m.bx(-0.5, 0.5, -0.6, -0.37, s0, s1, band, hull='noside', cull='klrt')
    front_trims(m, S, win)
    zm = (s0 + s1) / 2
    if pos in ('OpenL', 'OpenC', 'OpenR'):
        off = {'OpenL': -1.0, 'OpenC': 0.0, 'OpenR': 1.0}[pos]
        txt(m, shop['name'], -off, -0.604, zm, shop['cap'], lc, font=shop['font'], valign='m', maxw=2.7,
            clip=(-0.5 + off, 0.5 + off), shadow=shop.get('sh'), shadow_off=(0.05, -0.07))
    else:
        vdisc(m, (0, -0.604, zm), 0.22, lc, 'y-', seg=14)
        txt(m, initial(shop), 0.0, -0.608, zm, 0.2, band, font='display', valign='m', maxw=0.3)
    if top - s1 > 0.5:
        fq(m, -0.5, 0.5, -0.5, s1, top, 'stone')
        for i in range(4):
            fq(m, -0.44 + i * 0.25, -0.31 + i * 0.25, -0.503, s1 + 0.35, s1 + 0.48, 'gold')
        m.bx(-0.5, 0.5, -0.62, -0.5, top - 0.6, top - 0.38, 'stone2', hull='noside', cull='klr')
        m.bx(-0.5, 0.5, -0.56, -0.5, top - 0.16, top, 'cream', hull='noside', cull='ktlr')
    else:
        fq(m, -0.5, 0.5, -0.5, s1, top, 'stone')
    if awn and pos != 'OpenC':
        prof = [(-0.37, wtop + 0.02), (-1.12, wtop - 0.4), (-1.12, wtop - 0.6), (-0.37, wtop - 0.06)]
        m.prism(prof, -0.5, 0.5, [awn[0], awn[1]], hull='noside')
    elif pos == 'WinAW':
        zb = wtop - 0.45
        m.bx(-0.43, -0.4, -1.0, -0.37, zb + 0.3, zb + 0.36, 'dark', hull='none')
        m.bx(-0.44, -0.39, -0.95, -0.42, zb - 0.3, zb + 0.3, band, hull='full')
        vdisc(m, (-0.386, -0.685, zb), 0.17, lc, 'x+', seg=12)
        vdisc(m, (-0.444, -0.685, zb), 0.17, lc, 'x-', seg=12)
        txt(m, initial(shop), -0.382, -0.685, zb, 0.17, band, face='x+', font='display', valign='m', maxw=0.24)
        txt(m, initial(shop), -0.448, -0.685, zb, 0.17, band, face='x-', font='display', valign='m', maxw=0.24)
    # room side of the wall line, above the opening, with a trim band along the opening's head
    bq(m, -0.5, 0.5, 0.5, wtop, rt, rw)
    m.bx(-0.5, 0.5, 0.44, 0.5, wtop - 0.12, wtop, trim, hull='none', cull='ftlr')
    if win:
        bt = z0 + 0.6
        m.bx(-0.5, 0.5, -0.56, -0.37, z0, kick, 'stone2', hull='none', cull='kblr')
        glint(m, -0.42, 0.42, GY, kick, wtop)
        m.bx(-0.46, 0.46, -0.37, 0.5, z0, bt, 'cream', hull='none', cull='bkft')   # display bed (sides; top below)
        uq(m, -0.46, 0.46, -0.37, 0.5, bt + 0.003, flo)
        bq(m, -0.5, 0.5, 0.503, z0, bt, trim)
        # jamb toward the doorway (the window's inner side), facing the passage
        if pos == 'WinAW':
            rq(m, 0.5, -0.37, 0.5, z0, wtop, 'stone')
        else:
            lq(m, -0.5, -0.37, 0.5, z0, wtop, 'stone')
        n0 = m.nshape
        walk_display(m, brand, tag, pos, bt)
        for k in range(n0 + 1, m.nshape + 1):
            m.hmode[k] = 'none'
    else:
        # soffit over the doorway, a rolled-up shutter box behind the transom, a brass threshold and a dark mat strip
        dq(m, -0.5, 0.5, -0.545, 0.5, wtop, 'stone')
        m.bx(-0.5, 0.5, -0.3, -0.08, wtop - 0.16, wtop - 0.002, 'steel', hull='none', cull='t')
        fq(m, -0.5, 0.5, -0.303, wtop - 0.13, wtop - 0.1, 'chrome')
        uq(m, -0.5, 0.5, -0.5, -0.3, z0 + 0.016, 'brass')
        uq(m, -0.5, 0.5, -0.3, 0.5, z0 + 0.014, 'sign')


def door_leaves(m, S, frame):
    z0, d = S['z0'], S['dtop']
    for sx in (-1, 1):   # two open-frame glass doors with push bars
        x0, x1 = (0.0, 0.46) if sx > 0 else (-0.46, 0.0)
        a, b = min(x0, x1), max(x0, x1)
        m.bx(a + 0.005, a + 0.045, -0.47, -0.43, z0, d, 'chrome', hull='none', cull='k')
        m.bx(b - 0.045, b - 0.005, -0.47, -0.43, z0, d, 'chrome', hull='none', cull='k')
        m.bx(a + 0.045, b - 0.045, -0.465, -0.435, d - 0.08, d, 'chrome', hull='none', cull='k')
        m.bx(a + 0.045, b - 0.045, -0.465, -0.435, z0, z0 + 0.14, 'chrome', hull='none', cull='kb')
        m.bx(a + 0.08, b - 0.08, -0.52, -0.49, z0 + 0.98, z0 + 1.04, 'brass', hull='none', cull='k')
        glint(m, a + 0.05, b - 0.05, -0.452, z0 + 0.2, d - 0.1)
        dbx(m, a + 0.06, b - 0.06, -0.465, 0.012, z0 + 0.02, z0 + 0.13, 'brass')                # kick plate on the foot rail
    dbx(m, 0.16, 0.34, -0.465, 0.02, d - 0.075, d - 0.02, 'dark')                              # door closer on the head rail
    dbx(m, -0.455, 0.455, -0.5, 0.02, d - 0.02, d + 0.003, 'brass')                            # head casing
    m.bx(-0.5, 0.5, -0.5, -0.37, d, S['wtop'], 'sign', hull='noside', cull='klr')
    txt(m, 'OPEN', 0.0, -0.504, (d + S['wtop']) / 2, 0.1, 'lightW', font='display', valign='m', maxw=0.5, spacing=1.3)
    uq(m, -0.4, 0.4, -0.5, -0.37, S['z0'] + 0.008, 'chrome')
    uq(m, -0.42, 0.42, -0.2, 0.6, S['z0'] + 0.02, 'sign')   # mat


def figure(m, x, y, z, outfit, legs='dark', head=True):
    """shop mannequin on a stand (about 1.6 m)"""
    m.cy((x, y, z), 0.11, 0.11, 0.03, 'chrome', seg=8, hull='none')
    m.cy((x, y, z + 0.03), 0.015, 0.015, 0.6, 'chrome', seg=4, hull='none')
    m.bx(x - 0.1, x + 0.1, y - 0.06, y + 0.06, z + 0.3, z + 0.85, legs, hull='none')
    m.prism([(y - 0.08, z + 0.85), (y + 0.08, z + 0.85), (y + 0.06, z + 1.38), (y - 0.06, z + 1.38)], x - 0.15, x + 0.15, [outfit])
    for sx in (-1, 1):
        m.bx(x + sx * 0.16 - 0.025, x + sx * 0.16 + 0.025, y - 0.03, y + 0.03, z + 0.88, z + 1.34, outfit if sx > 0 else 'skin', hull='none')
    if head:
        m.sp((x, y, z + 1.5), 0.1, 'skin', seg=(8, 5))


def shelf_wall(m, z0, h, colors, frame='wood', y=BACK - 0.02, n=3, step=0.13):
    """wall shelving: uprights, boards and rows of coloured stock (books, boxes) painted on the front"""
    fq(m, -0.5, 0.5, y - 0.3, z0, z0 + 0.06, frame)
    for k in range(n):
        zb = z0 + 0.45 + k * (h - 0.5) / n
        m.bx(-0.5, 0.5, y - 0.32, y, zb - 0.03, zb, frame, hull='noside', cull='kb')
        x = -0.47
        i = 0
        while x < 0.44:
            w = step * (0.7 + 0.5 * ((i * 7 + k * 3) % 5) / 4)
            hh = (h - 0.5) / n * (0.55 + 0.3 * ((i * 3 + k) % 3) / 2)
            fq(m, x, min(x + w - 0.012, 0.47), y - 0.22, zb + 0.004, zb + hh, colors[(i + k) % len(colors)])
            x += w
            i += 1


def contents_up(m, brand, pos, S):
    """upper-storey shops: shoes, optics, bakery, homeware, (sports: closed), leather goods"""
    z0, ceil = S['z0'], S['ceil']
    pl = z0 + S['kick'] - 0.01
    win = pos in ('WinA', 'WinB')
    if brand == 'rose':   # Shoe Gallery
        for k in range(3):   # wall shelves of shoes
            zb = z0 + 0.6 + k * 0.6
            m.bx(-0.5, 0.5, BACK - 0.3, BACK - 0.006, zb - 0.03, zb, 'cream', hull='none', cull='kb')
            for i in range(4):   # shoe pairs painted as side profiles on the shelf back
                x = -0.36 + i * 0.24
                c = ('rose', 'navy', 'paper', 'gold', 'dark')[(i + k + len(pos)) % 5]
                poly(m, [(x - 0.09, BACK - 0.003, zb + 0.004), (x + 0.09, BACK - 0.003, zb + 0.004), (x + 0.09, BACK - 0.003, zb + 0.12),
                         (x + 0.02, BACK - 0.003, zb + 0.12), (x - 0.09, BACK - 0.003, zb + 0.05)], c, (0, -1, 0))
        if win:   # stepped plinths with pairs
            for i, (x, h, c) in enumerate(((-0.25, 0.25, 'paper'), (0.0, 0.45, 'roseL'), (0.25, 0.15, 'cream'))):
                m.bx(x - 0.11, x + 0.11, -0.25, 0.0, pl, pl + h, c, hull='none', cull='k')
                shoe(m, x, -0.17, pl + h, ('rose', 'dark', 'gold')[i], heel=(i != 1))
                shoe(m, x, -0.07, pl + h, ('rose', 'dark', 'gold')[i], heel=(i != 1))
        else:
            m.cy((0.0, 0.6, z0), 0.3, 0.3, 0.42, 'rose', seg=10, hull='none')
    elif brand == 'sky':   # Lumen Optics: eye chart, frames on display
        fq(m, -0.3, 0.3, BACK - 0.003, z0 + 1.1, z0 + 2.5, 'paper')
        for i, (row, cap) in enumerate((('E', 0.22), ('F P', 0.12), ('T O Z', 0.08), ('L P E D', 0.055)) if pos == 'Door' else ()):
            txt(m, row, 0.0, BACK - 0.007, z0 + 2.2 - i * 0.28 + (0.0 if i else -0.05), cap, 'ink', font='sans', maxw=0.5)
        m.bx(-0.45, 0.45, 0.5, 0.9, z0, z0 + 0.9, 'cream', hull='none', cull='k')
        for i in range(3):
            x = -0.28 + i * 0.28
            for sx in (-1, 1):
                m.cy((x + sx * 0.045, 0.7, z0 + 0.95), 0.035, 0.035, 0.008, 'dark', seg=8, rot=(90, 0, 0), hull='none')
            m.bx(x - 0.07, x + 0.07, 0.712, 0.73, z0 + 0.9, z0 + 0.92, 'dark', hull='none')
        if win:   # giant spectacles on a stand
            for sx in (-1, 1):
                m.cy((sx * 0.17, -0.1, pl + 1.0), 0.15, 0.15, 0.03, 'dark', seg=12, rot=(90, 0, 0), hull='none')
                m.cy((sx * 0.17, -0.115, pl + 1.0), 0.12, 0.12, 0.005, 'glassL', seg=12, rot=(90, 0, 0), hull='none')
            m.bx(-0.04, 0.04, -0.12, -0.08, pl + 1.04, pl + 1.07, 'dark', hull='none')
            m.bx(-0.015, 0.015, -0.1, -0.07, pl, pl + 0.85, 'chrome', hull='none')
    elif brand == 'orange':   # Bakehouse: cake counter, cake stand, chalk menu
        fq(m, -0.42, 0.42, BACK - 0.003, z0 + 1.3, z0 + 2.4, 'sign')
        if pos == 'Door':
            txt(m, "Today's Bakes", 0.0, BACK - 0.007, z0 + 2.12, 0.1, 'paper', font='script', maxw=0.74)
        for i in range(3):
            fq(m, -0.32, 0.18 + 0.06 * (i % 2), BACK - 0.007, z0 + 1.5 + i * 0.16, z0 + 1.53 + i * 0.16, 'orangeL')
        if win:   # three-tier cake stand
            m.cy((0, -0.1, pl), 0.03, 0.03, 0.7, 'chrome', seg=6, hull='none')
            for i, r in enumerate((0.3, 0.22, 0.15)):
                zz = pl + 0.15 + i * 0.25
                m.cy((0, -0.1, zz), r, r, 0.015, 'paper', seg=12, hull='none')
                cake(m, 0.0, -0.1, zz + 0.015, r * 0.6, ('roseL', 'woodL', 'orangeL')[i], h=0.08)
        else:
            m.bx(-0.5, 0.5, 1.0, 1.4, z0, z0 + 0.95, 'wood2', hull='none', cull='k')
            m.bx(-0.5, 0.5, 1.0, 1.4, z0 + 0.95, z0 + 1.25, 'glassL', hull='none', cull='kb')
            for i in range(3):
                cake(m, -0.3 + i * 0.3, 1.2, z0 + 0.955, 0.1, ('roseL', 'wood', 'cream')[i], top=('paper', 'cream', 'orangeL')[i], h=0.09)
    elif brand == 'mint':   # Hearth & Home: plants, vases, lamp
        m.bx(-0.5, 0.5, BACK - 0.3, BACK, z0 + 1.2, z0 + 1.23, 'woodL', hull='none', cull='kb')
        for i in range(4):
            x = -0.36 + i * 0.24
            m.cy((x, BACK - 0.15, z0 + 1.23), 0.05, 0.07 - 0.02 * (i % 2), 0.2 + 0.08 * (i % 3), ('tealM', 'cream', 'terra', 'navy')[i], seg=8, hull='none')
        if win:
            plant(m, -0.2, -0.1, pl, 1.4)
            m.cy((0.25, -0.1, pl), 0.12, 0.12, 0.5, 'wood', seg=8, hull='none')
            m.cy((0.25, -0.1, pl + 0.5), 0.06, 0.09, 0.3, 'tealM', seg=8, hull='none')
        else:
            m.bx(-0.42, 0.42, 0.4, 1.0, z0, z0 + 0.7, 'woodL', hull='none', cull='k')
            for i in range(3):
                plant(m, -0.28 + i * 0.28, 0.7, z0 + 0.7, 0.8, pot=('terra', 'cream', 'navy')[i])
            m.cy((0.0, 1.5, z0), 0.02, 0.02, 1.5, 'brass', seg=6, hull='none')
            m.cy((0.0, 1.5, z0 + 1.45), 0.22, 0.12, 0.25, 'cream', seg=10, hull='none')
    elif brand == 'violet':   # Leatherworks: bags on plinths and shelves
        for k in range(2):
            zb = z0 + 0.9 + k * 0.7
            m.bx(-0.5, 0.5, BACK - 0.3, BACK - 0.006, zb - 0.03, zb, 'wood2', hull='none', cull='kb')
            for i in range(3):   # bags painted on the shelf back
                x = -0.3 + i * 0.3
                c = ('wood', 'redT', 'dark', 'gold', 'wood2')[(i + k) % 5]
                poly(m, [(x - 0.11, BACK - 0.003, zb + 0.004), (x + 0.11, BACK - 0.003, zb + 0.004), (x + 0.08, BACK - 0.003, zb + 0.17),
                         (x - 0.08, BACK - 0.003, zb + 0.17)], c, (0, -1, 0))
        if win:
            for i, (x, h) in enumerate(((-0.24, 0.5), (0.22, 0.3))):
                m.cy((x, -0.1, pl), 0.13, 0.13, h, 'paper', seg=10, hull='none')
                bag(m, x, -0.1, pl + h, ('wood', 'redT')[i], w=0.26, h=0.2)
        else:
            m.bx(-0.45, 0.45, 0.6, 1.0, z0, z0 + 0.85, 'sign', hull='none', cull='k')
            bag(m, 0.0, 0.8, z0 + 0.85, 'wood2', w=0.3, h=0.22)
        if pos == 'Door':
            txt(m, 'Est. 1984', 0.0, BACK - 0.004, z0 + 2.35, 0.09, 'gold', font='script', maxw=0.6)


def contents(m, brand, pos, S):
    if S is UP:
        return contents_up(m, brand, pos, S)
    z0, ceil = S['z0'], S['ceil']
    pl = z0 + S['kick'] - 0.01      # window plinth top
    win = pos in ('WinA', 'WinB')
    if brand == 'rose':
        if win:
            figure(m, 0.0, -0.12, pl, 'rose' if pos == 'WinA' else 'navy', legs='cream' if pos == 'WinA' else 'dark')
        else:   # clothes rail with garments, a counter behind the door
            m.bx(-0.5, 0.5, 1.2, 1.24, z0 + 1.6, z0 + 1.64, 'chrome', hull='none')
            for i, c in enumerate(('navy', 'rose', 'cream', 'gold', 'tealM')):
                x = -0.4 + i * 0.2
                m.bx(x - 0.07, x + 0.07, 1.1, 1.34, z0 + 0.85, z0 + 1.58, c, hull='none', cull='k')
            if pos == 'Door':
                m.bx(-0.5, 0.5, 1.7, 2.15, z0, z0 + 1.0, 'cream', hull='noside', cull='k')
                fq(m, -0.5, 0.5, 1.696, z0 + 0.7, z0 + 0.8, 'rose')
        fq(m, -0.3, 0.3, BACK - 0.003, z0 + 1.6, z0 + 2.5, 'rose' if pos != 'SignL' else 'gold')
    elif brand == 'sky':
        m.bx(-0.42, 0.42, 0.25 if win else 0.6, 0.85 if win else 1.2, z0, z0 + 0.82, 'cream', hull='full', cull='k')
        y0 = 0.4 if win else 0.75
        for i in range(2):
            x = -0.2 + i * 0.4
            m.bx(x - 0.13, x + 0.13, y0, y0 + 0.2, z0 + 0.82, z0 + 0.84, 'dark', hull='none', cull='b')
            m.bx(x - 0.12, x + 0.12, y0 + 0.18, y0 + 0.21, z0 + 0.84, z0 + 1.0, 'dark', hull='none', cull='k')
            fq(m, x - 0.1, x + 0.1, y0 + 0.177, z0 + 0.855, z0 + 0.99, 'sky')
        fq(m, -0.46, 0.46, BACK - 0.003, z0 + 1.1, z0 + 2.4, 'intD')   # video wall
        fq(m, -0.4, 0.4, BACK - 0.006, z0 + 1.2, z0 + 1.9, 'sky' if pos != 'Door' else 'blueT')
        fq(m, -0.4, 0.1, BACK - 0.009, z0 + 1.3, z0 + 1.5, 'skyL')
    elif brand == 'orange':
        if win:   # window bar with stools and cups
            m.bx(-0.5, 0.5, -0.33, 0.05, z0 + 1.0, z0 + 1.06, 'wood', hull='noside', cull='k')
            m.cy((0.0, 0.35, z0), 0.03, 0.03, 0.68, 'chrome', seg=6, hull='none')
            m.cy((0.0, 0.35, z0 + 0.68), 0.16, 0.16, 0.06, 'orange', seg=10)
            m.cy((0.2, -0.15, z0 + 1.06), 0.04, 0.035, 0.1, 'cream', seg=8, hull='none')
        else:   # counter with an espresso machine, cakes; menu boards on the back wall
            m.bx(-0.5, 0.5, 1.1, 1.6, z0, z0 + 1.0, 'wood2', hull='noside', cull='k')
            uq(m, -0.5, 0.5, 1.08, 1.62, z0 + 1.03, 'cream')
            if pos == 'Door':
                m.bx(-0.25, 0.2, 1.2, 1.5, z0 + 1.03, z0 + 1.45, 'chrome', hull='full')
                fq(m, -0.2, 0.15, 1.196, z0 + 1.2, z0 + 1.38, 'redT')
            else:
                m.bx(-0.4, 0.4, 1.15, 1.5, z0 + 1.03, z0 + 1.3, 'glassL', hull='full', cull='k')
                for i in range(3):
                    m.cy((-0.26 + i * 0.26, 1.33, z0 + 1.05), 0.08, 0.08, 0.07, ('roseL', 'orangeL', 'woodL')[i], seg=8, hull='none')
        fq(m, -0.42, 0.42, BACK - 0.003, z0 + 1.6, z0 + 2.4, 'sign')
        if pos == 'Door':   # neon script over the counter
            txt(m, 'Coffee', 0.0, BACK - 0.007, z0 + 1.85, 0.16, 'orangeL', font='script', maxw=0.72, shadow='orange', shadow_off=(0.03, -0.03))
        else:
            txt(m, 'MENU', 0.0, BACK - 0.007, z0 + 2.2, 0.1, 'gold', font='display', maxw=0.6)
            for i in range(3):
                fq(m, -0.34, 0.1 + 0.08 * (i % 2), BACK - 0.006, z0 + 1.75 + i * 0.13, z0 + 1.78 + i * 0.13, 'paper')
    elif brand == 'mint':
        shelf_wall(m, z0, min(2.5, ceil - z0 - 0.1), ['tealM', 'redT', 'gold', 'navy', 'cream', 'orange', 'violet'], frame='wood2')
        if win:   # book pyramid on the plinth
            for k, w in enumerate((0.5, 0.36, 0.22)):
                m.bx(-w, w, -0.2, 0.05, pl + k * 0.16, pl + (k + 1) * 0.16 - 0.005, ('redT', 'navy', 'gold')[k], hull='full', cull='k')
        else:
            m.bx(-0.42, 0.42, 0.4, 1.0, z0, z0 + 0.75, 'wood', hull='full', cull='k')
            for i in range(3):
                m.bx(-0.36 + i * 0.25, -0.18 + i * 0.25, 0.5, 0.82, z0 + 0.75, z0 + 0.82 + 0.04 * i, ('tealM', 'redT', 'gold')[i], hull='none', cull='b')
    elif brand == 'gold':
        shelf_wall(m, z0, min(2.4, ceil - z0 - 0.1), ['redT', 'blueT', 'greenT', 'orange', 'violet', 'yellow'], frame='cream', n=3, step=0.2)
        if win:   # big teddy bear / balloons
            if pos == 'WinA':
                bx_, by_ = 0.0, -0.05
                m.sp((bx_, by_, pl + 0.32), 0.3, 'wood', seg=(7, 4))
                m.sp((bx_, by_ - 0.02, pl + 0.8), 0.22, 'wood', seg=(7, 4))
                for sx in (-1, 1):
                    m.sp((bx_ + sx * 0.17, by_, pl + 0.98), 0.08, 'wood2', seg=(6, 4))
                m.sp((bx_, by_ - 0.21, pl + 0.75), 0.07, 'woodL', seg=(6, 4))
                m.bx(-0.08, 0.08, by_ - 0.33, by_ - 0.28, pl + 0.5, pl + 0.56, 'redT', hull='none')
            else:
                for i, (x, zz, c) in enumerate(((-0.2, 2.0, 'redT'), (0.15, 2.25, 'blueT'), (0.3, 1.85, 'yellow'))):
                    m.sp((x, 0.3, z0 + zz), 0.16, c, seg=(6, 4))
                    m.bm_((x, 0.3, z0 + zz - 0.16), (0.0, 0.1, pl + 0.3), 0.01, 'dark', hull='none')
                m.bx(-0.2, 0.2, -0.15, 0.15, pl, pl + 0.3, 'greenT', hull='full')
    elif brand == 'violet':
        # glass counters with gold pieces, a pedestal bust in the window, a little chandelier
        if win:
            m.cy((0.0, -0.05, pl), 0.16, 0.16, 0.7, 'paper', seg=8)
            m.prism([(-0.15, pl + 0.7), (0.05, pl + 0.7), (0.0, pl + 1.15), (-0.1, pl + 1.15)], -0.13, 0.13, ['sign'])
            m.cy((0.0, -0.16, pl + 0.95), 0.1, 0.1, 0.02, 'gold', seg=8, rot=(90, 0, 0), hull='none')
            m.cy((0.0, -0.12, pl + 1.15), 0.03, 0.03, 0.12, 'sign', seg=6, hull='none')
        else:
            m.bx(-0.5, 0.5, 0.7, 1.2, z0, z0 + 0.7, 'sign', hull='noside', cull='k')
            m.bx(-0.5, 0.5, 0.7, 1.2, z0 + 0.7, z0 + 0.95, 'glass', hull='noside', cull='kb')
            for i in range(3):
                m.cy((-0.3 + i * 0.3, 0.95, z0 + 0.72), 0.06, 0.06, 0.03, 'gold', seg=8, hull='none')
        fq(m, -0.4, 0.4, BACK - 0.003, z0 + 1.0, z0 + 2.3, 'sign')
        fq(m, -0.06, 0.06, BACK - 0.006, z0 + 1.1, z0 + 2.2, 'gold')
        if pos == 'Door':
            m.cy((0.0, 1.0, ceil - 0.5), 0.25, 0.1, 0.35, 'gold', seg=8)
            m.sp((0.0, 1.0, ceil - 0.55), 0.09, 'light', seg=(6, 4))


def build_shopfronts(pal, ao):
    for brand in BRANDS:
        for pos in POS:
            for tag, S in (('Lo', LO), ('Up', UP)):
                m = new(pal)
                shop_front(m, brand, pos, S)
                make('%s_%s_%s' % (tag, brand, pos), m, ao)
        for tag, S in (('Lo', LO), ('Up', UP)):
            if (brand, tag) not in ROOM:
                continue
            for pos in POS_W:
                m = new(pal)
                shop_front_walk(m, brand, pos, S)
                make('%s_%s_%s' % (tag, brand, pos), m, ao)


def back_sides(m, z0=0.0, z1=H):
    """side faces closing the neighbours' shop interiors behind a pilaster / blank module"""
    rq(m, 0.5, -0.37, BACK + 0.05, z0, z1, 'cream')
    lq(m, -0.5, -0.37, BACK + 0.05, z0, z1, 'cream')


def build_walls(pal, ao):
    # pilaster between bays: sandstone shaft with base, capitals, terracotta inlay, two brass sconces. The narrow
    # variant stands beside a zone corner: nothing of it comes within 0.2 m of the corner, where the perpendicular
    # wall's pilaster stands proud
    for name, w in (('Pilaster', 0.36), ('Pilaster_C', 0.22)):
        wb, wc = w + 0.06, min(w + 0.08, 0.44)
        m = new(pal)
        for sx in (-1, 1):
            fq(m, min(sx * 0.5, sx * w), max(sx * 0.5, sx * w), -0.5, 0.0, H, 'stone')
        m.bx(-w, w, -0.62, -0.5, 0.0, H, 'stone', hull='full', cull='kt')
        for z0, z1 in ((0.0, 0.42), (4.5, 4.78)):
            m.bx(-wb, wb, -0.67, -0.5, z0, z1, 'stone2', hull='full', cull='k' + ('b' if z0 == 0 else ''))
        for z0, z1 in ((3.7, 4.1), (8.85, 9.2)):
            m.bx(-wc, wc, -0.69, -0.5, z0, z1, 'cream', hull='full', cull='k')
        m.bx(-wc, wc, -0.64, -0.5, 9.3, H, 'stone2', hull='full', cull='kt')
        for z0, z1 in ((0.7, 3.3), (5.1, 8.5)):
            fq(m, -0.1, 0.1, -0.625, z0, z1, 'terra')
            fq(m, -0.05, 0.05, -0.628, z0 + 0.12, z1 - 0.12, 'gold')
        for zs in (2.55, 6.6):   # sconce: bracket and glass globe
            m.bx(-0.04, 0.04, -0.95, -0.62, zs - 0.04, zs + 0.03, 'brass', hull='none')
            m.cy((0, -0.95, zs - 0.12), 0.05, 0.07, 0.1, 'brass', seg=6, hull='none', caps=False)
            m.sp((0, -0.95, zs + 0.08), 0.13, 'light', seg=(6, 4), hull='none')
        for sx in (-1, 1):   # brass corner guards at knocking height
            d_guard(m, sx * w, -0.62, 0.5, 1.5, 'brass', side=sx)
        back_sides(m)
        make(name, m, ao)
    # zone corners: a block that fills the corner cell and closes the shop interiors on both walls
    for name, (x0, x1, y0, y1, keep) in (('NW', (-3.2, 0.5, -0.5, 3.2, 'rf')), ('NE', (-0.5, 3.2, -0.5, 3.2, 'lf')),
                                         ('SW', (-3.2, 0.5, -3.2, 0.5, 'rk')), ('SE', (-0.5, 3.2, -3.2, 0.5, 'lk'))):
        m = new(pal)
        cull = ''.join(ch for ch in 'tbfklr' if ch not in keep)
        m.bx(x0, x1, y0, y1, 0.0, H, 'cream', hull='none', cull=cull)
        faces = {'f': (0, y0, x0, x1), 'k': (180, -y1, -x1, -x0), 'r': (90, -x1, y0, y1), 'l': (-90, x0, -y1, -y0)}
        for ch in keep:   # each visible face: skirting, cap and a few seams, in the face's own frame
            deg, yf, a, b = faces[ch]
            m.parent = Matrix.Rotation(math.radians(deg), 4, 'Z')
            d_base(m, a, b, yf, 'stone2', h=0.12, d=0.02)
            d_cap(m, a, b, yf, H, 'stone2', h=0.1, d=0.025)
            d_seams(m, a, b, yf, 0.13, H - 0.11, 0.95, 'stone2')
            m.parent = Matrix.Identity(4)
        make('Corner_' + name, m, ao)
    # blank modules (bay ends, beside the gates): directory board / lit poster below, poster / clock above
    for name in ('Blank_Map', 'Blank_Ad'):
        m = new(pal)
        fq(m, -0.5, 0.5, -0.5, 0.0, H, 'stone')
        m.bx(-0.5, 0.5, -0.56, -0.5, 0.0, 0.3, 'stone2', hull='noside', cull='kb')
        m.bx(-0.5, 0.5, -0.56, -0.5, 4.5, 4.75, 'stone2', hull='noside', cull='k')
        m.bx(-0.5, 0.5, -0.62, -0.5, 8.9, 9.12, 'stone2', hull='noside', cull='k')
        m.bx(-0.42, 0.42, -0.6, -0.5, 0.75, 2.75, 'dark', hull='full', cull='k')
        dbx(m, -0.495, 0.495, -0.56, 0.012, 0.29, 0.31, 'brass')      # skirting cap
        d_frame(m, -0.42, 0.42, 0.75, 2.75, -0.5, 'brass', depth=0.115, top=(name != 'Blank_Map'))
        if name == 'Blank_Map':
            fq(m, -0.37, 0.37, -0.603, 0.82, 2.68, 'cream')
            for (a, b, c0, c1, c) in ((-0.33, -0.05, 2.2, 2.62, 'rose'), (-0.01, 0.33, 2.2, 2.62, 'sky'), (-0.33, 0.33, 1.95, 2.13, 'stone2'),
                                       (-0.33, -0.12, 1.35, 1.88, 'mint'), (-0.08, 0.12, 1.35, 1.88, 'orange'), (0.16, 0.33, 1.35, 1.88, 'violet'),
                                       (-0.33, 0.33, 1.1, 1.28, 'stone2'), (-0.33, 0.0, 0.88, 1.04, 'yellow')):
                fq(m, a, b, -0.606, c0, c1, c)
            m.cy((0.12, -0.61, 1.0), 0.05, 0.05, 0.004, 'redT', seg=8, rot=(90, 0, 0), hull='none')
            txt(m, 'YOU ARE HERE', 0.19, -0.607, 0.9, 0.032, 'redT', font='cond', align='l', maxw=0.17)
            fq(m, -0.42, 0.42, -0.603, 2.75, 2.95, 'tealM')
            txt(m, 'DIRECTORY', 0.0, -0.607, 2.79, 0.12, 'paper', font='display', maxw=0.72)
            # upper: clock
            m.cy((0, -0.5, 6.6), 0.42, 0.42, 0.08, 'brass', seg=16, rot=(90, 0, 0))
            m.cy((0, -0.585, 6.6), 0.36, 0.36, 0.006, 'cream', seg=16, rot=(90, 0, 0), hull='none')
            m.bx(-0.015, 0.015, -0.603, -0.598, 6.58, 6.88, 'sign', hull='none')
            m.bx(-0.012, 0.2, -0.597, -0.592, 6.585, 6.615, 'sign', hull='none')
        else:
            fq(m, -0.37, 0.37, -0.603, 0.82, 2.68, 'lightW')
            fq(m, -0.37, 0.37, -0.606, 0.82, 1.5, 'tealM')
            m.cy((0.0, -0.609, 1.95), 0.26, 0.26, 0.004, 'orange', seg=14, rot=(90, 0, 0), hull='none')
            m.cy((0.0, -0.612, 1.95), 0.21, 0.21, 0.004, 'yellow', seg=14, rot=(90, 0, 0), hull='none')
            txt(m, '50%', 0.0, -0.62, 1.97, 0.13, 'redT', font='display', maxw=0.36)
            txt(m, 'SUMMER SALE', 0.0, -0.606, 2.36, 0.1, 'rose', font='display', maxw=0.68)
            txt(m, 'SALE', 0.0, -0.61, 1.1, 0.22, 'paper', font='display', maxw=0.6)
            # upper: tall fashion poster: silhouette, "New Season"
            m.bx(-0.4, 0.4, -0.6, -0.5, 5.2, 8.4, 'dark', hull='full', cull='k')
            d_frame(m, -0.4, 0.4, 5.2, 8.4, -0.5, 'brass', depth=0.115)
            fq(m, -0.34, 0.34, -0.603, 5.27, 8.33, 'rose')
            fq(m, -0.34, 0.34, -0.606, 5.27, 6.2, 'violetD')
            vdisc(m, (0.0, -0.607, 7.95), 0.08, 'sign', 'y-', seg=10)
            poly(m, [(-0.03, -0.607, 7.8), (0.03, -0.607, 7.8), (0.08, -0.607, 7.55), (-0.08, -0.607, 7.55)], 'sign', (0, -1, 0))
            poly(m, [(-0.08, -0.607, 7.55), (0.08, -0.607, 7.55), (0.22, -0.607, 6.6), (-0.22, -0.607, 6.6)], 'sign', (0, -1, 0))
            for sx in (-1, 1):
                fq(m, sx * 0.07 - 0.022, sx * 0.07 + 0.022, -0.607, 6.24, 6.6, 'sign')
            fq(m, 0.2, 0.32, -0.61, 6.8, 6.95, 'gold')
            txt(m, 'New Season', 0.0, -0.61, 5.82, 0.11, 'paper', font='serif', maxw=0.62)
            txt(m, 'AUTUMN · WINTER', 0.0, -0.61, 5.55, 0.05, 'roseL', font='cond', maxw=0.6)
        back_sides(m)
        make(name, m, ao)
    # ground storey behind a food stall (the stall's own back wall covers it): flat stone, sides closing the neighbours
    m = new(pal)
    fq(m, -0.5, 0.5, -0.5, 0.0, 4.1, 'stone')
    back_sides(m, 0.0, 4.1)
    make('Lo_Plain', m, ao)
    # beside a gate: tall stone pier with a vertical lit name strip; no interior behind (the corridor runs there)
    m = new(pal)
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'stone')
    m.bx(-0.32, 0.32, -0.66, -0.5, 4.6, 9.0, 'tealD', hull='full', cull='k')
    fq(m, -0.24, 0.24, -0.663, 4.75, 8.85, 'tealM')
    for i in range(7):
        fq(m, -0.16, 0.16, -0.666, 4.95 + i * 0.55, 5.3 + i * 0.55, 'gold' if i % 2 else 'lightW')
    m.bx(-0.5, 0.5, -0.6, -0.5, 9.1, H, 'stone2', hull='noside', cull='kt')
    d_kick(m, -0.5, 0.5, -0.5, 'chrome', h=0.24)
    d_guard(m, 0.5, -0.5, 0.3, 1.4, 'chrome', side=1)
    d_guard(m, -0.5, -0.5, 0.3, 1.4, 'chrome', side=-1)
    make('GateSide', m, ao)


# ================================================================ circulation
def build_rail(pal, ao):
    """railing half module (cell centre -> +Z game edge = Blender -Y), full module, post: balusters + wood handrail"""
    def rail(m, y0, y1):
        m.bx(-0.035, 0.035, y0, y1, 0.98, 1.06, 'wood', hull='noend', cull='')
        m.bx(-0.03, 0.03, y0, y1, 0.06, 0.13, 'steel', hull='noend')
        n = max(1, int(round((y1 - y0) / 0.33)))
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            m.bx(-0.012, 0.012, y - 0.012, y + 0.012, 0.13, 0.98, 'chrome', hull='none', cull='tb')
            m.bx(-0.024, 0.024, y - 0.024, y + 0.024, 0.9, 0.95, 'brass', hull='none')      # handrail bracket collar
    m = new(pal)
    rail(m, -0.5, -0.04)
    make('Rail', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0, 1.1)])
    m = new(pal)
    rail(m, -0.5, 0.5)
    make('RailFull', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0.5, 1.1)])
    m = new(pal)
    m.bx(-0.045, 0.045, -0.045, 0.045, 0.0, 1.08, 'cream', cull='b')
    m.bx(-0.06, 0.06, -0.06, 0.06, 1.08, 1.13, 'brass', cull='b')
    m.bx(-0.058, 0.058, -0.058, 0.058, 0.0, 0.09, 'brass', hull='none', cull='b')            # floor collar
    make('RailPost', m, ao)


def build_columns(pal, ao):
    """round sandstone columns on the mezzanine edge: under the slab (0 - 4.1) and over it (deck - ceiling)"""
    for name, h, top in (('Column_Lo', 4.1, True), ('Column_Hi', H - DECK, True)):
        m = new(pal)
        m.bx(-0.42, 0.42, -0.42, 0.42, 0.0, 0.32, 'stone2', cull='b')
        m.cy((0, 0, 0.32), 0.36, 0.33, 0.12, 'cream', seg=10, hull='full')
        m.cy((0, 0, 0.44), 0.3, 0.3, h - 0.44 - 0.5, 'stone', seg=10, caps=False)
        for z in (1.4, h - 1.3):
            m.cy((0, 0, z), 0.315, 0.315, 0.06, 'gold', seg=10, hull='none', caps=False)
        m.cy((0, 0, h - 0.5), 0.3, 0.4, 0.3, 'cream', seg=10, caps=False)
        m.bx(-0.44, 0.44, -0.44, 0.44, h - 0.2, h - 0.004, 'stone2', cull='t')
        m.cy((0, 0, 0.5), 0.315, 0.315, 0.12, 'chrome', seg=10, hull='none', caps=False)     # protective kick band
        for fy in (-1, 1):   # wayfinding plaque on two faces
            y0, y1 = sorted((fy * 0.27, fy * 0.325))
            m.bx(-0.28, 0.28, y0, y1, 2.25, 2.6, 'tealD', hull='full')
            yb = sorted((fy * 0.265, fy * 0.332))
            for xa, xb in ((-0.296, -0.277), (0.277, 0.296)):
                m.bx(xa, xb, yb[0], yb[1], 2.253, 2.597, "brass", hull="none")
            for za, zb in ((2.23, 2.253), (2.597, 2.62)):
                m.bx(-0.296, 0.296, yb[0], yb[1], za, zb, 'brass', hull='none')
            f = 'y-' if fy < 0 else 'y+'
            txt(m, 'LEVEL 0' if name == 'Column_Lo' else 'LEVEL 1', 0.0, fy * 0.329, 2.425, 0.16, 'paper', face=f, font='display', valign='m', maxw=0.48)
        if name == 'Column_Hi':   # a bracket lamp facing the atrium on each side
            for a in (0, 2):
                ca, sa = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
                m.sp((ca * 0.36, sa * 0.36, 2.6), 0.1, 'light', seg=(6, 4), hull='none')
        make(name, m, ao, cols=[col_box(-0.42, -0.42, 0, 0.42, 0.42, h)])


def build_escalator(pal, ao):
    """2 x 10 footprint rising toward +Y (game north): bottom landing, 14 steps of 0.3214 m, top landing at 4.5 m.
    Collision: stair blocks (walkable, kind 'step') and side walls; visuals: steps with yellow nosings, steel skirts,
    teal truss cladding, glass balustrades and black handrails that loop over the newels."""
    m = new(pal)
    n, y0, y1 = 14, -5.0 + 0.9, 5.0 - 1.0
    run, rise = (y1 - y0) / n, DECK / n
    cols = [col_box(-0.84, -5.0, 0, 0.84, y0, 0.05, True)]
    m.bx(-0.8, 0.8, -5.0, y0, 0.0, 0.05, 'chrome', cull='b')
    for i in range(6):
        fq(m, -0.6 + i * 0.24, -0.5 + i * 0.24, -5.003, 0.012, 0.04, 'dark')
    for k in range(n):
        a, top = y0 + k * run, (k + 1) * rise
        m.bx(-0.8, 0.8, a, a + run, top - rise - 0.01 if k else 0.0, top, 'step', cull='bklr')
        uq(m, -0.78, 0.78, a + 0.004, a + 0.06, top + 0.003, 'yellow')
        cols.append(col_box(-0.84, a, 0, 0.84, a + run, top, True))
    m.bx(-0.8, 0.8, y1, 5.0, DECK - 0.4, DECK, 'chrome', cull='')
    uq(m, -0.6, 0.6, y1 + 0.05, y1 + 0.3, DECK + 0.003, 'dark')
    cols.append(col_box(-0.84, y1, 0, 0.84, 5.0, DECK, True))
    # under the top landing: the truss end (steel), visible from the front of the escalator's tail
    m.bx(-0.8, 0.8, y1 - 0.6, 4.99, 0.0, DECK - 0.4, 'tealD', cull='tblr')
    for sx in (-1, 1):
        xi, xo = sx * 0.8, sx * 1.0
        a, b = min(xi, xo), max(xi, xo)
        # truss side: profile under the step line (y, z), teal cladding with a chrome trim stripe
        prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, DECK + 0.12), (y1, DECK + 0.12), (y0 - 0.1, 0.17), (-5.0, 0.17)]
        m.prism(prof, a, b, ['tealM'])
        trim = [(-4.95, 0.11), (y0 - 0.12, 0.11), (y1 + 0.02, DECK + 0.06), (4.95, DECK + 0.06), (4.95, DECK + 0.0), (y1 - 0.01, DECK + 0.0), (y0 - 0.15, 0.05), (-4.95, 0.05)]
        if sx > 0:
            m.prism([(p[0], p[1]) for p in trim], b + 0.0, b + 0.004, ['chrome'], hull='none')
        else:
            m.prism([(p[0], p[1]) for p in trim], a - 0.004, a, ['chrome'], hull='none')
        # glass balustrade (0.95 m) on the truss, handrail on top with round ends
        gx0, gx1 = sx * 0.88 - 0.015, sx * 0.88 + 0.015
        gl = [(-4.7, 0.17), (y0 - 0.1, 0.17), (y1, DECK + 0.12), (4.7, DECK + 0.12), (4.7, DECK + 1.0), (y1 + 0.05, DECK + 1.0), (y0 - 0.05, 1.05), (-4.7, 1.05)]
        m.prism(gl, gx0, gx1, ['glass'], hull='none')
        hr = [(-4.75, 1.02), (y0 - 0.05, 1.02), (y1 + 0.05, DECK + 0.97), (4.75, DECK + 0.97), (4.75, DECK + 1.09), (y1 + 0.06, DECK + 1.09), (y0 - 0.06, 1.14), (-4.75, 1.14)]
        m.prism(hr, sx * 0.88 - 0.05, sx * 0.88 + 0.05, ['rubber'])
        for yy, zz, dirn in ((-4.75, 0.6, -1), (4.75, DECK + 0.55, 1)):   # handrail loops over the newels
            pts = [(yy + dirn * 0.4 * math.sin(i / 6 * math.pi), zz + 0.48 * math.cos(i / 6 * math.pi)) for i in range(7)]
            for i in range(6):
                m.bm_((sx * 0.88, pts[i][0], pts[i][1]), (sx * 0.88, pts[i + 1][0], pts[i + 1][1]), 0.09 - 0.008 * (i % 2), 'rubber')
        # glints on the glass (outer face)
        for k in (0.25, 0.6):
            t = k
            yy = y0 + (y1 - y0) * t
            zz = 0.17 + (DECK - 0.05) * t
            pts = [(yy, zz + 0.15), (yy + 0.35, zz + 0.15 + 0.35 * DECK / (y1 - y0)), (yy + 0.55, zz + 0.75), (yy + 0.2, zz + 0.6)]
            xo2 = sx * 0.899
            poly(m, [(xo2, p[0], p[1]) for p in pts], 'glassL', (sx, 0, 0))
        # collision: side walls following the step line
        for k in range(n + 2):
            if k == 0:
                a2, b2, top = -5.0, y0, 0.05
            elif k == n + 1:
                a2, b2, top = y1, 5.0, DECK
            else:
                a2, b2, top = y0 + (k - 1) * run, y0 + k * run, k * rise
            cols.append(col_box(sx * 0.92 - 0.08, a2, 0, sx * 0.92 + 0.08, b2, top + 1.06))
    make('Escalator', m, ao, cols=cols)


def build_elevator(pal, ao):
    """3 x 3 glass shaft, open toward -Y (game +Z / the piece's front), the cab the engine moves and the door leaves.
    Shaft: chrome corner posts, ring beams, mullioned glass suggested by glints (the cab stays visible), guide rails,
    landing frames with floor indicators and call buttons at both stops, a crown on top."""
    m = new(pal)
    top = H - 0.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 1.42 - 0.08, sx * 1.42 + 0.08, sy * 1.42 - 0.08, sy * 1.42 + 0.08, 0.0, top, 'chrome', cull='b')
    # ring beams (sides + back), front header beams over each landing
    for z0, z1, c in ((0.0, 0.14, 'dark'), (4.08, 4.5, 'tealD'), (top - 0.3, top, 'tealD')):
        for sx in (-1, 1):
            m.bx(sx * 1.42 - 0.06, sx * 1.42 + 0.06, -1.34, 1.34, z0, z1, c, cull='b' if z0 == 0 else '')
        m.bx(-1.34, 1.34, 1.36, 1.48, z0, z1, c, cull='b' if z0 == 0 else '')
    m.bx(-1.34, 1.34, -1.48, -1.36, top - 0.3, top, 'tealD')
    for zz in (2.1, 6.7):
        for sx in (-1, 1):
            m.bx(sx * 1.42 - 0.05, sx * 1.42 + 0.05, -1.34, 1.34, zz, zz + 0.08, 'chrome', hull='none')
        m.bx(-1.34, 1.34, 1.37, 1.47, zz, zz + 0.08, 'chrome', hull='none')
    # mullions and glints (side glass at x = +/-1.44, back glass at y = 1.44)
    for sx in (-1, 1):
        m.bx(sx * 1.44 - 0.025, sx * 1.44 + 0.025, -0.03, 0.03, 0.14, top - 0.3, 'chrome', hull='none', cull='tb')
        for z0, z1 in ((0.14, 2.1), (2.18, 4.08), (4.5, 6.7), (6.78, top - 0.3)):
            for (ya, yb) in ((-1.3, -0.06), (0.06, 1.3)):
                pts = [(ya + 0.15, z0 + 0.3), (ya + 0.4, z0 + 0.3), (ya + 0.85, z1 - 0.4), (ya + 0.6, z1 - 0.4)]
                poly(m, [(sx * 1.47, p[0], p[1]) for p in pts], 'glassL', (sx, 0, 0))
                poly(m, [(sx * 1.41, p[0], p[1]) for p in pts], 'glassL', (-sx, 0, 0))
    m.bx(-0.03, 0.03, 1.415, 1.465, 0.14, top - 0.3, 'chrome', hull='none', cull='tb')
    for z0, z1 in ((0.14, 2.1), (2.18, 4.08), (4.5, 6.7), (6.78, top - 0.3)):
        for (xa, xb) in ((-1.3, -0.06), (0.06, 1.3)):
            pts = [(xa + 0.15, z0 + 0.3), (xa + 0.4, z0 + 0.3), (xa + 0.85, z1 - 0.4), (xa + 0.6, z1 - 0.4)]
            poly(m, [(p[0], 1.47, p[1]) for p in pts], 'glassL', (0, 1, 0))
            poly(m, [(p[0], 1.41, p[1]) for p in pts], 'glassL', (0, -1, 0))
    # guide rails on the back wall (the cab's shoes run on them)
    for sx in (-1, 1):
        m.bx(sx * 0.75 - 0.04, sx * 0.75 + 0.04, 1.26, 1.36, 0.14, top - 0.3, 'steel', hull='none', cull='tb')
    # landings: jambs, fixed side panels, header with a floor indicator, call buttons
    for zs in (0.0, DECK):
        for sx in (-1, 1):
            m.bx(0.65 if sx > 0 else -0.76, 0.76 if sx > 0 else -0.65, -1.5, -1.36, zs, zs + 2.45, 'chrome')
            x0, x1 = (0.76, 1.34) if sx > 0 else (-1.34, -0.76)
            m.bx(x0, x1, -1.49, -1.45, zs + (0.14 if zs == 0 else 0.0), zs + 2.4, 'steel', hull='none')
            glint(m, x0 + 0.04, x1 - 0.04, -1.495, zs + 0.3, zs + 2.2)
            d_kick(m, x0 + 0.04, x1 - 0.04, -1.49, 'chrome', h=0.28, z0=zs + (0.14 if zs == 0 else 0.0), d=0.01)
        m.bx(-0.65, 0.65, -1.5, -1.36, zs - (0.3 if zs else 0.0), zs + 0.025, 'chrome', cull='' if zs else 'b')   # sill
        m.bx(-1.34, 1.34, -1.5, -1.36, zs + 2.45, zs + 2.75, 'tealD')
        fq(m, -0.3, 0.3, -1.503, zs + 2.5, zs + 2.7, 'sign')
        poly(m, [(-0.2, -1.506, zs + 2.53), (-0.1, -1.506, zs + 2.53), (-0.15, -1.506, zs + 2.67)], 'light', (0, -1, 0))
        poly(m, [(0.1, -1.506, zs + 2.67), (0.2, -1.506, zs + 2.67), (0.15, -1.506, zs + 2.53)], 'gold', (0, -1, 0))
        m.bx(0.86, 1.06, -1.53, -1.47, zs + 1.0, zs + 1.4, 'chrome', hull='full')
        for zb in (1.1, 1.28):
            m.cy((0.96, -1.535, zs + zb), 0.035, 0.035, 0.006, 'light', seg=8, rot=(90, 0, 0), hull='none')
    # sign over the upper landing; crown
    m.bx(-1.0, 1.0, -1.62, -1.5, 7.55, 8.05, 'sign')
    txt(m, 'Lifts', 0.0, -1.624, 7.8, 0.24, 'gold', font='sans', valign='m', maxw=1.6)
    m.bx(-1.56, 1.56, -1.56, 1.56, top, top + 0.06, 'gold', hull='none', cull='t')
    cols = [col_box(-1.5, 1.36, 0, 1.5, 1.5, top), col_box(-1.5, -1.5, 0, -1.36, 1.5, top), col_box(1.36, -1.5, 0, 1.5, 1.5, top)]
    make('Landmark_ElevatorShaft', m, ao, cols=cols)

    # ---- cab: floor top at 0.06; local -Y = the door side
    m = new(pal)
    m.bx(-1.3, 1.3, -1.3, 1.3, -0.18, 0.04, 'steel', cull='')
    uq(m, -1.25, 1.25, -1.25, 1.25, 0.062, 'marble')
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.066, 'tealM')
    m.bx(-0.9, 0.9, -0.9, 0.9, -0.5, -0.18, 'dark', cull='t')   # machinery under the floor
    for sx in (-1, 1):   # shoes on the guide rails
        m.bx(sx * 0.75 - 0.08, sx * 0.75 + 0.08, 1.29, 1.355, 0.0, 2.6, 'dark', hull='none')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 1.27 - 0.04, sx * 1.27 + 0.04, sy * 1.27 - 0.04, sy * 1.27 + 0.04, 0.04, 2.55, 'chrome')
    # side and back walls: teal panel below a chrome handrail, glass above (glints); front jambs and header
    for sx in (-1, 1):
        m.bx(sx * 1.27 - 0.02, sx * 1.27 + 0.02, -1.23, 1.23, 0.04, 0.95, 'tealM', cull='tb')
        m.bx(sx * 1.2 - 0.03, sx * 1.2 + 0.03, -1.1, 1.1, 0.98, 1.03, 'chrome', hull='none')
        for (ya, yb) in ((-1.2, 0.0), (0.0, 1.2)):
            pts = [(ya + 0.2, 1.3), (ya + 0.42, 1.3), (ya + 0.82, 2.25), (ya + 0.6, 2.25)]
            poly(m, [(sx * 1.292, p[0], p[1]) for p in pts], 'glassL', (sx, 0, 0))
    m.bx(-1.23, 1.23, 1.25, 1.29, 0.04, 0.95, 'tealM', cull='tb')
    m.bx(-1.1, 1.1, 1.17, 1.23, 0.98, 1.03, 'chrome', hull='none')
    for (xa, xb) in ((-1.2, 0.0), (0.0, 1.2)):
        pts = [(xa + 0.2, 1.3), (xa + 0.42, 1.3), (xa + 0.82, 2.25), (xa + 0.6, 2.25)]
        poly(m, [(p[0], 1.292, p[1]) for p in pts], 'glassL', (0, 1, 0))
    for sx in (-1, 1):   # fixed front panels beside the doorway
        x0, x1 = (0.66, 1.23) if sx > 0 else (-1.23, -0.66)
        m.bx(x0, x1, -1.345, -1.315, 0.04, 2.4, 'chrome', hull='full', cull='')
        fq(m, x0 + 0.06, x1 - 0.06, -1.348, 0.15, 0.95, 'tealM')
    m.bx(-1.23, 1.23, -1.345, -1.25, 2.4, 2.55, 'tealD')
    fq(m, -0.25, 0.25, -1.348, 2.43, 2.52, 'light')
    # roof with a light panel and a gold crown
    m.bx(-1.31, 1.31, -1.31, 1.31, 2.55, 2.7, 'cream')
    dq(m, -0.7, 0.7, -0.7, 0.7, 2.547, 'lightW')
    m.bx(-1.33, 1.33, -1.33, 1.33, 2.7, 2.76, 'gold', hull='none', cull='b')
    make('Elevator_Cab', m, ao)

    # ---- door leaves (0.65 x 2.3, centred on the origin, symmetric front / back): cab (chrome) and landing (steel)
    for name, fr in (('Elevator_CabDoor', 'chrome'), ('Elevator_LandDoor', 'steel')):
        m = new(pal)
        hgt = 2.33
        m.bx(-0.325, 0.325, -0.02, 0.02, 0.0, 0.09, fr)
        m.bx(-0.325, 0.325, -0.02, 0.02, hgt - 0.08, hgt, fr)
        for sx in (-1, 1):
            m.bx(sx * 0.325 - 0.05 if sx > 0 else -0.325, sx * 0.325 if sx > 0 else -0.275, -0.02, 0.02, 0.09, hgt - 0.08, fr)
        m.bx(-0.275, 0.275, -0.008, 0.008, 0.09, hgt - 0.08, 'glass', hull='none', cull='tblr')
        for y, nrm in ((-0.012, -1), (0.012, 1)):
            pts = [(-0.18, 0.5), (-0.06, 0.5), (0.18, 1.5), (0.06, 1.5)]
            poly(m, [(p[0], y, p[1]) for p in pts], 'glassL', (0, nrm, 0))
        m.bx(-0.3, 0.3, -0.024, 0.024, 1.0, 1.05, 'tealM', hull='none')
        m.bx(-0.27, 0.27, -0.026, 0.026, 0.087, 0.28, 'brass', hull='none')                 # kick plate, both faces
        make(name, m, ao)


# ================================================================ props
def build_props(pal, ao):
    # flower planter (1 x 1): terracotta bowl on a foot, a shrub with pink and yellow flowers
    for name, fl in (('Planter', 'rose'), ('Planter_B', 'yellow')):
        m = new(pal)
        m.cy((0, 0, 0), 0.26, 0.3, 0.1, 'terraD', seg=10)
        m.cy((0, 0, 0.1), 0.3, 0.42, 0.52, 'terra', seg=10)
        m.cy((0, 0, 0.62), 0.43, 0.43, 0.06, 'cream', seg=10, caps=False)
        annulus(m, 0.68, 0.36, 0.43, 'cream', seg=10)
        m.cy((0, 0, 0.33), 0.37, 0.37, 0.04, 'gold', seg=10, hull='none', caps=False)       # brass band round the bowl
        disc(m, 0, 0, 0.66, 0.38, 'soil', seg=10)
        m.sp((0, 0, 0.95), 0.36, 'leaf', seg=(6, 4), scale=(1, 1, 0.8))
        m.sp((0.12, -0.1, 1.15), 0.2, 'leafL', seg=(6, 3))
        for i in range(5):
            a = i / 5 * 2 * math.pi + 0.4
            r = 0.3 if i % 2 else 0.22
            m.sp((math.cos(a) * r, math.sin(a) * r, 0.98 + 0.12 * (i % 3)), 0.07, fl if i % 3 else 'paper', seg=(5, 3), hull='none')
        make(name, m, ao, cols=[col_box(-0.42, -0.42, 0, 0.42, 0.42, 1.1)])
    # big planter (2 x 2): octagonal stone bed with a palm and ground cover
    m = new(pal)
    m.cy((0, 0, 0), 0.92, 0.92, 0.62, 'stone2', seg=8)
    m.cy((0, 0, 0.62), 0.96, 0.96, 0.08, 'cream', seg=8, caps=False)
    annulus(m, 0.7, 0.82, 0.96, 'cream', seg=8)
    m.cy((0, 0, 0.1), 0.925, 0.925, 0.16, 'tealM', seg=8, hull='none', caps=False)
    m.cy((0, 0, 0.0), 0.95, 0.95, 0.08, 'stone', seg=8, hull='none')                       # skirting ring
    disc(m, 0, 0, 0.69, 0.86, 'soil', seg=8)
    for k, (x, y) in enumerate(((0.45, 0.3), (-0.45, 0.25), (0.05, -0.5))):
        m.sp((x, y, 0.78), 0.3, 'leaf2' if k % 2 else 'leafL', seg=(6, 3), scale=(1, 1, 0.6))
    pts, z = [], 0.7
    for i in range(6):   # trunk: stacked, slightly leaning rings
        r = 0.16 - i * 0.013
        m.cy((0.03 * i, 0.0, z), r + 0.02, r, 0.55, 'wood2' if i % 2 else 'wood', seg=6, caps=(i == 5))
        z += 0.55
    cx, top = 0.15, z
    for i in range(9):   # fronds: flat drooping blades
        a = i / 9 * 2 * math.pi
        d = (math.cos(a), math.sin(a))
        mid = (cx + d[0] * 0.75, d[1] * 0.75, top + 0.22)
        tip = (cx + d[0] * 1.45, d[1] * 1.45, top - 0.35)
        for (p, q, w) in (((cx, 0, top), mid, 0.34), (mid, tip, 0.26)):
            dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
            L = math.sqrt(dx * dx + dy * dy + dz * dz)
            pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
            yaw = math.degrees(math.atan2(dy, dx))
            m.box(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2), (L, w, 0.04), 'leaf' if i % 2 else 'leaf2',
                  rot=(0, -pitch, yaw), bevel=False)
    m.sp((cx, 0, top + 0.05), 0.2, 'leaf2', seg=(7, 4))
    make('BigPlanter', m, ao, cols=[col_box(-0.92, -0.92, 0, 0.92, 0.92, 0.7)])
    # bench 2 x 1: wooden slats on cast-iron frames with armrests, front -Y
    m = new(pal)
    for sx in (-0.82, 0.82):
        m.bx(sx - 0.04, sx + 0.04, -0.24, 0.2, 0.0, 0.42, 'sign', hull='none')
        m.bx(sx - 0.035, sx + 0.035, 0.16, 0.24, 0.38, 0.9, 'sign', hull='none')
        m.bx(sx - 0.05, sx + 0.05, -0.26, 0.16, 0.6, 0.65, 'sign', hull='none')
    for i in range(3):
        m.bx(-0.95, 0.95, -0.24 + i * 0.15, -0.12 + i * 0.15, 0.42, 0.47, 'wood', cull='')
    for i in range(2):
        m.bx(-0.95, 0.95, 0.17, 0.22, 0.55 + i * 0.17, 0.68 + i * 0.17, 'wood')
    dbx(m, -0.11, 0.11, 0.17, 0.008, 0.585, 0.645, 'brass', s=1)                            # donor plaque on the backrest
    for sx in (-0.82, 0.82):   # rubber foot pads
        for y0, y1 in ((-0.255, -0.17), (0.12, 0.205)):
            m.bx(sx - 0.05, sx + 0.05, y0, y1, 0.0, 0.025, 'rubber', hull='none', cull='b')
    make('Bench', m, ao, cols=[col_box(-0.95, -0.27, 0, 0.95, 0.27, 0.47)])
    # bin: two-tone recycling bin
    m = new(pal)
    m.bx(-0.26, 0.26, -0.2, 0.2, 0.0, 0.85, 'steel', cull='b')
    m.bx(-0.28, 0.0, -0.22, 0.22, 0.85, 0.97, 'tealM')
    m.bx(0.0, 0.28, -0.22, 0.22, 0.85, 0.97, 'orange')
    fq(m, -0.2, -0.04, -0.203, 0.4, 0.62, 'tealM')
    fq(m, 0.04, 0.2, -0.203, 0.4, 0.62, 'orange')
    for sg in (-1, 1):
        d_base(m, -0.26, 0.26, sg * 0.2, 'rubber', h=0.08, d=0.012, s=sg)
    make('Bin', m, ao, cols=[col_box(-0.28, -0.22, 0, 0.28, 0.22, 0.97)])
    # directory totem (ad pillar slot): lit map on both faces, "i" disc on top
    m = new(pal)
    m.bx(-0.36, 0.36, -0.18, 0.18, 0.0, 0.2, 'sign', cull='b')
    m.bx(-0.32, 0.32, -0.14, 0.14, 0.2, 2.4, 'tealD')
    m.bx(-0.36, 0.36, -0.18, 0.18, 2.4, 2.55, 'gold')
    fq(m, -0.26, 0.26, -0.143, 0.6, 2.2, 'lightW')
    bq(m, -0.26, 0.26, 0.143, 0.6, 2.2, 'lightW')
    for (a, b, c0, c1, c) in ((-0.22, -0.02, 1.75, 2.12, 'rose'), (0.02, 0.22, 1.75, 2.12, 'sky'), (-0.22, 0.22, 1.5, 1.66, 'stone2'),
                               (-0.22, -0.06, 1.02, 1.42, 'mint'), (-0.02, 0.22, 1.02, 1.42, 'orange'), (-0.22, 0.22, 0.7, 0.92, 'violet')):
        fq(m, a, b, -0.146, c0, c1, c)
        bq(m, -b, -a, 0.146, c0, c1, c)
    m.cy((0, 0, 2.55), 0.16, 0.16, 0.2, 'tealM', seg=10)
    for sg in (-1, 1):
        d_kick(m, -0.32, 0.32, sg * 0.14, 'brass', h=0.5, z0=0.2, s=sg)
        d_guard(m, 0.32, sg * 0.14, 0.7, 1.9, 'brass', s=sg, side=1)
        d_guard(m, -0.32, sg * 0.14, 0.7, 1.9, 'brass', s=sg, side=-1)
    make('AdPillar', m, ao, cols=[col_box(-0.36, -0.36, 0, 0.36, 0.36, 2.6)])
    # kiosks 3 x 2 (solid as a whole): coffee cart (canopy), sweets (striped parasol, jars), gadgets (light-box header)
    for name, c, c2 in (('Kiosk_A', 'orange', 'cream'), ('Kiosk_B', 'rose', 'paper'), ('Kiosk_C', 'sky', 'skyL')):
        m = new(pal)
        m.bx(-1.3, 1.3, -0.7, 0.7, 0.0, 0.12, 'sign', cull='b')
        m.bx(-1.25, 1.25, -0.65, 0.65, 0.12, 1.0, 'cream')
        for sy in (-1, 1):
            fq(m, -1.1, 1.1, -0.653, 0.25, 0.85, c) if sy < 0 else bq(m, -1.1, 1.1, 0.653, 0.25, 0.85, c)
        m.bx(-1.35, 1.35, -0.75, 0.75, 1.0, 1.06, 'wood')
        for sg in (-1, 1):   # kick plates and corner guards on the long faces
            d_kick(m, -1.25, 1.25, sg * 0.65, 'chrome', h=0.12, z0=0.12, s=sg)
            d_guard(m, 1.25, sg * 0.65, 0.26, 0.95, 'chrome', s=sg, side=1)
            d_guard(m, -1.25, sg * 0.65, 0.26, 0.95, 'chrome', s=sg, side=-1)
        if name == 'Kiosk_A':
            m.bx(-0.9, -0.3, -0.2, 0.3, 1.06, 1.55, 'chrome')
            fq(m, -0.85, -0.35, -0.203, 1.2, 1.45, 'redT')
            for i in range(3):
                m.cy((0.2 + i * 0.3, -0.3, 1.06), 0.05, 0.045, 0.14, 'paper', seg=8, hull='none')
            for sx in (-1.25, 1.25):
                for sy in (-0.65, 0.65):
                    m.cy((sx, sy, 1.06), 0.035, 0.035, 1.45, 'chrome', seg=6, hull='none')
            prof = [(-0.85, 2.5), (0.85, 2.5), (0.85, 2.62), (0.0, 2.9), (-0.85, 2.62)]
            m.prism(prof, -1.45, 1.45, [c, c2, c, c2, c, c2])
            m.bx(-0.6, 0.6, -0.86, -0.8, 2.15, 2.5, 'sign')
            txt(m, 'Espresso', 0.0, -0.864, 2.31, 0.15, 'gold', font='script', valign='m', maxw=1.1)
        elif name == 'Kiosk_B':
            for i in range(4):
                x = -0.9 + i * 0.6
                m.cy((x, 0.0, 1.06), 0.17, 0.17, 0.32, 'glassL', seg=8)
                m.sp((x, 0.0, 1.22), 0.12, ('yellow', 'mint', 'redT', 'violet')[i], seg=(5, 3), hull='none')
                m.cy((x, 0.0, 1.38), 0.18, 0.18, 0.05, 'rose', seg=8)
            m.cy((0, 0, 1.06), 0.04, 0.04, 1.7, 'chrome', seg=6, hull='none')
            m.fan((0, 0, 2.55), 2.95, 1.55, 10, [c, c2])
            m.sp((0, 0, 2.97), 0.07, 'gold', seg=(6, 4))
        else:
            for i in range(3):
                x = -0.8 + i * 0.8
                m.bx(x - 0.3, x + 0.3, -0.3, 0.3, 1.06, 1.4, 'glass', hull='full', cull='b')
                m.bx(x - 0.12, x + 0.12, -0.08, 0.08, 1.06, 1.22, 'dark', hull='none', cull='b')
            m.bx(-0.06, 0.06, -0.06, 0.06, 1.4, 2.2, 'chrome', hull='none', cull='b')
            m.bx(-1.1, 1.1, -0.2, 0.2, 2.2, 2.75, 'sky')
            for sy in (-1, 1):
                txt(m, 'Accessories', 0.0, sy * 0.204, 2.47, 0.18, 'paper', face='y-' if sy < 0 else 'y+', font='sans', valign='m', maxw=2.0)
        make(name, m, ao, cols=[col_box(-1.4, -0.8, 0, 1.4, 0.8, 2.6)])
    # food court tables (2 x 2): round table + four chairs with backs, tray with a burger and drinks; parasol variant
    for name, para in (('FoodTable', False), ('FoodTable_B', True)):
        m = new(pal)
        m.cy((0, 0, 0), 0.3, 0.3, 0.03, 'sign', seg=10)
        m.cy((0, 0, 0.03), 0.06, 0.06, 0.69, 'chrome', seg=6, hull='none')
        m.cy((0, 0, 0.72), 0.55, 0.55, 0.05, 'paper', seg=14)
        for i in range(4):
            a = i / 4 * 2 * math.pi + 0.785
            ca, sa = math.cos(a), math.sin(a)
            x, y = ca * 0.78, sa * 0.78
            cc = ('rose', 'mint', 'gold', 'sky')[i] if not para else ('orange', 'tealM')[i % 2]
            m.cy((x, y, 0), 0.03, 0.03, 0.44, 'chrome', seg=5, hull='none')
            m.cy((x, y, 0.44), 0.2, 0.2, 0.05, cc, seg=8)
            bx_, by_ = x + ca * 0.18, y + sa * 0.18
            m.box((bx_, by_, 0.72), (0.06, 0.36, 0.5), cc, rot=(0, 0, math.degrees(a)), bevel=False)
        m.bx(-0.2, 0.2, -0.14, 0.14, 0.77, 0.79, 'redT', hull='none', cull='b')
        m.cy((-0.05, 0.0, 0.79), 0.08, 0.08, 0.03, 'wood', seg=8, hull='none')
        m.cy((-0.05, 0.0, 0.82), 0.075, 0.075, 0.02, 'greenT', seg=8, hull='none')
        m.cy((-0.05, 0.0, 0.84), 0.08, 0.07, 0.04, 'wood', seg=8, hull='none')
        m.cy((0.12, 0.05, 0.79), 0.035, 0.03, 0.14, 'redT', seg=6, hull='none')
        m.cy((0.25, -0.25, 0.77), 0.04, 0.035, 0.15, 'yellow', seg=6, hull='none')
        if para:
            m.cy((0, 0, 0.77), 0.025, 0.025, 1.6, 'chrome', seg=6, hull='none')
            m.fan((0, 0, 2.2), 2.55, 1.15, 8, ['tealM', 'cream'])
        make(name, m, ao, cols=[col_box(-0.95, -0.95, 0, 0.95, 0.95, 0.77)])
    # food stall 4 x 2 (against a wall; front -Y): counter, food display, menu boards, sign with lettering
    STALL = {'Stall_Pizza': ('Pizzeria', 'script', 0.26, ('PIZZA', 'SIDES', 'DRINKS')),
             'Stall_Noodle': ('NOODLE BAR', 'display', 0.38, ('NOODLES', 'RICE', 'DRINKS')),
             'Stall_Burger': ('Burgers & Fries', 'cond', 0.32, ('BURGERS', 'FRIES', 'SHAKES'))}
    for name, word, c, c2 in (('Stall_Pizza', 'PIZZA', 'redT', 'yellow'), ('Stall_Noodle', 'WOK', 'orange', 'sign'), ('Stall_Burger', 'BURGER', 'yellow', 'redT')):
        sname, sfont, scap, heads = STALL[name]
        m = new(pal)
        m.bx(-2.0, 2.0, 0.5, 1.0, 0.0, 3.4, 'cream', cull='b')            # back wall
        m.bx(-2.0, -1.9, -1.0, 0.5, 0.0, 3.4, c, cull='b')
        m.bx(1.9, 2.0, -1.0, 0.5, 0.0, 3.4, c, cull='b')
        m.bx(-1.9, 1.9, -0.95, -0.35, 0.0, 1.05, c2 if c2 != 'sign' else 'wood2', cull='b')   # counter
        fq(m, -1.7, 1.7, -0.953, 0.15, 0.9, c)
        d_kick(m, -1.9, 1.9, -0.95, 'chrome', h=0.15, d=0.01)
        d_guard(m, 1.9, -0.95, 0.15, 1.0, 'chrome', side=1)
        d_guard(m, -1.9, -0.95, 0.15, 1.0, 'chrome', side=-1)
        m.bx(-1.9, 1.9, -1.0, -0.3, 1.05, 1.1, 'chrome')
        m.bx(-1.6, 1.6, -0.8, -0.45, 1.1, 1.35, 'glassL', hull='full', cull='kb')
        for i in range(4):
            x = -1.2 + i * 0.8
            m.cy((x, -0.62, 1.1), 0.18, 0.18, 0.04, ('orange', 'yellow', 'greenT', 'redT')[(i + len(word)) % 4], seg=8, hull='none')
        for i in range(3):   # menu boards
            x = -1.25 + i * 1.25
            m.bx(x - 0.55, x + 0.55, 0.42, 0.5, 2.0, 2.8, 'sign', hull='full')
            txt(m, heads[i], x, 0.416, 2.56, 0.11, c2 if c2 != 'sign' else 'gold', font='display', maxw=0.8)
            for j in range(3):
                fq(m, x - 0.45, x + 0.1 - 0.1 * j, 0.417, 2.1 + j * 0.13, 2.16 + j * 0.13, 'paper')
        m.bx(-2.05, 2.05, -1.1, 0.55, 3.0, 3.6, c)                         # sign box
        txt(m, sname, 0.0, -1.104, 3.3, scap, c2 if c2 != 'sign' else 'paper', font=sfont, valign='m', maxw=3.5,
            shadow='sign' if name != 'Stall_Noodle' else None, shadow_off=(0.04, -0.05))
        make(name, m, ao, cols=[col_box(-2.0, -1.0, 0, 2.0, 1.0, 3.6)])
    # department store podium (2 x 1): white plinth, two mannequins, a SALE sign
    m = new(pal)
    m.cy((0, 0, 0), 0.9, 0.9, 0.22, 'cream', seg=14)
    m.cy((0, 0, 0.22), 0.92, 0.92, 0.03, 'gold', seg=14, hull='none')
    figure(m, -0.4, 0.0, 0.25, 'tealM', legs='navy')
    figure(m, 0.4, 0.05, 0.25, 'orange', legs='cream')
    m.bx(-0.2, 0.2, -0.35, -0.3, 0.25, 0.75, 'sign')
    txt(m, 'New In', 0.0, -0.354, 0.55, 0.08, 'yellow', font='script', maxw=0.34)
    txt(m, 'ALL STYLES', 0.0, -0.354, 0.4, 0.04, 'paper', font='cond', maxw=0.32)
    make('Display', m, ao, cols=[col_box(-0.9, -0.45, 0, 0.9, 0.45, 1.85)])


def build_fountain(pal, ao):
    m = new(pal)
    seg = 16
    m.cy((0, 0, 0), 1.9, 1.9, 0.5, 'stone2', seg=seg)
    m.cy((0, 0, 0.12), 1.912, 1.912, 0.22, 'tealM', seg=seg, hull='none', caps=False)
    for i in range(seg):   # gold tile dots on the teal band (one per facet)
        a = (i + 0.5) / seg * 2 * math.pi
        m.box((math.cos(a) * 1.885, math.sin(a) * 1.885, 0.23), (0.02, 0.14, 0.09), 'gold', rot=(0, 0, math.degrees(a)), bevel=False)
        m.hmode[m.nshape] = 'none'
    m.cy((0, 0, 0.5), 1.98, 1.98, 0.12, 'cream', seg=seg, caps=False)
    annulus(m, 0.62, 1.72, 1.98, 'cream', seg=seg)
    disc(m, 0, 0, 0.6, 1.76, 'water', seg=seg)
    for r0, r1 in ((1.3, 1.38), (0.95, 1.0)):
        annulus(m, 0.603, r0, r1, 'waterL', seg=seg)
    m.cy((0, 0, 0.5), 0.36, 0.3, 0.95, 'stone', seg=10)
    m.cy((0, 0, 1.45), 0.4, 1.0, 0.24, 'stone2', seg=14)
    disc(m, 0, 0, 1.695, 0.9, 'water', seg=14)
    m.cy((0, 0, 0.6), 1.24, 1.0, 1.09, 'waterL', seg=14, hull='none', caps=False)   # falling water sheet
    m.cy((0, 0, 1.69), 0.18, 0.15, 0.6, 'stone', seg=8)
    m.cy((0, 0, 2.29), 0.2, 0.55, 0.16, 'stone2', seg=12)
    disc(m, 0, 0, 2.455, 0.48, 'water', seg=12)
    m.cy((0, 0, 1.695), 0.6, 0.55, 0.755, 'waterL', seg=12, hull='none', caps=False)
    m.cy((0, 0, 2.45), 0.07, 0.07, 0.35, 'gold', seg=6)
    m.sp((0, 0, 2.9), 0.16, 'gold', seg=(8, 5))
    for i in range(8):   # jets from the rim arcing into the middle bowl
        a = i / 8 * 2 * math.pi + math.pi / 8
        p0 = (math.cos(a) * 1.7, math.sin(a) * 1.7, 0.62)
        p1 = (math.cos(a) * 1.4, math.sin(a) * 1.4, 1.35)
        p2 = (math.cos(a) * 1.1, math.sin(a) * 1.1, 1.62)
        m.bm_(p0, p1, 0.06, 'waterL', hull='none')
        m.bm_(p1, p2, 0.06, 'waterL', hull='none')
    cols = [col_box(-1.6, -1.6, 0, 1.6, 1.6, 0.6), col_box(-0.95, -0.95, 0.6, 0.95, 0.95, 1.85)]
    make('Landmark_Fountain', m, ao, bevel=0.0, cols=cols)


def build_guestdesk(pal, ao):
    """round Guest Services desk (4 x 4): ring counter with teal panels, monitors, a column carrying INFO drums"""
    m = new(pal)
    m.cy((0, 0, 0), 1.75, 1.75, 0.12, 'sign', seg=20)
    m.cy((0, 0, 0.12), 1.7, 1.7, 0.93, 'wood', seg=20)
    for i in range(20):   # teal panels on the counter's facets (cylinder vertices sit at multiples of 18 degrees)
        a0, a1 = i / 20 * 2 * math.pi, (i + 1) / 20 * 2 * math.pi
        nx, ny = math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)
        P0 = (math.cos(a0) * 1.7, math.sin(a0) * 1.7)
        P1 = (math.cos(a1) * 1.7, math.sin(a1) * 1.7)
        A = (P0[0] + (P1[0] - P0[0]) * 0.12 + nx * 0.006, P0[1] + (P1[1] - P0[1]) * 0.12 + ny * 0.006)
        B = (P0[0] + (P1[0] - P0[0]) * 0.88 + nx * 0.006, P0[1] + (P1[1] - P0[1]) * 0.88 + ny * 0.006)
        poly(m, [(A[0], A[1], 0.3), (B[0], B[1], 0.3), (B[0], B[1], 0.88), (A[0], A[1], 0.88)], 'tealM' if i % 2 else 'tealD', (nx, ny, 0))
    m.cy((0, 0, 1.05), 1.85, 1.85, 0.07, 'cream', seg=20)
    m.cy((0, 0, 1.12), 0.42, 0.42, 2.2, 'stone', seg=12)
    m.cy((0, 0, 1.12), 0.46, 0.46, 0.25, 'stone2', seg=12, caps=False)
    for i in range(4):
        a = i / 4 * 2 * math.pi + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        # monitor on the counter, facing out
        m.box((ca * 1.15, sa * 1.15, 1.32), (0.07, 0.42, 0.3), 'dark', rot=(0, 0, math.degrees(a)), bevel=False)
        m.box((ca * 1.188, sa * 1.188, 1.32), (0.004, 0.36, 0.24), 'sky', rot=(0, 0, math.degrees(a)), bevel=False)
        m.hmode[m.nshape] = 'none'
        m.box((ca * 1.05, sa * 1.05, 1.13), (0.12, 0.2, 0.04), 'dark', rot=(0, 0, math.degrees(a)), bevel=False)
    # sign drum: four INFO faces on a square box, gold bands
    m.bx(-0.95, 0.95, -0.95, 0.95, 3.0, 3.6, 'tealD')
    m.bx(-0.97, 0.97, -0.97, 0.97, 2.94, 3.0, 'gold', hull='none')
    m.bx(-0.97, 0.97, -0.97, 0.97, 3.6, 3.66, 'gold', hull='none')
    for face, (fx, fy) in (('y-', (0, -0.955)), ('y+', (0, 0.955)), ('x+', (0.955, 0)), ('x-', (-0.955, 0))):
        txt(m, 'Guest Services', fx, fy, 3.3, 0.2, 'paper', face=face, font='serif', valign='m', maxw=1.7)
    m.cy((0, 0, 3.66), 0.25, 0.25, 0.3, 'gold', seg=10)
    m.sp((0, 0, 4.05), 0.18, 'light', seg=(8, 5))
    # brochure racks on the counter
    for i in range(2):
        a = i * math.pi + 0.3
        m.box((math.cos(a) * 1.45, math.sin(a) * 1.45, 1.22), (0.3, 0.12, 0.26), 'paper', rot=(0, 0, math.degrees(a)), bevel=False)
    make('Landmark_GuestDesk', m, ao, bevel=0.0, cols=[col_box(-1.8, -1.8, 0, 1.8, 1.8, 1.11), col_box(-0.5, -0.5, 0, 0.5, 0.5, 3.6)])


# ================================================================ floor inlays ("@layer 0"), roof ("@layer 9.5"), under-deck lights
def build_floor(pal, ao):
    Z0 = 0.016
    # diamond tile (1 x 1): small terrazzo diamond on the cell centre; A terracotta, B teal
    for name, c in (('Inlay_A', 'terra'), ('Inlay_B', 'tealM')):
        m = new(pal)
        r = 0.34
        poly(m, [(0, -r, Z0), (r, 0, Z0), (0, r, Z0), (-r, 0, Z0)], c, (0, 0, 1))
        poly(m, [(0, -0.11, Z0 + 0.004), (0.11, 0, Z0 + 0.004), (0, 0.11, Z0 + 0.004), (-0.11, 0, Z0 + 0.004)], 'gold', (0, 0, 1))
        make(name, m, ao)
    # border band (1 x 1, runs along local X): navy edges, gold diamond chain on cream
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, Z0, 'marble')
    for sy in (-1, 1):
        uq(m, -0.5, 0.5, sy * 0.5 - (0.16 if sy > 0 else 0), sy * 0.5 + (0.16 if sy < 0 else 0), Z0 + 0.003, 'navy')
    poly(m, [(0, -0.22, Z0 + 0.003), (0.22, 0, Z0 + 0.003), (0, 0.22, Z0 + 0.003), (-0.22, 0, Z0 + 0.003)], 'gold', (0, 0, 1))
    poly(m, [(0, -0.09, Z0 + 0.006), (0.09, 0, Z0 + 0.006), (0, 0.09, Z0 + 0.006), (-0.09, 0, Z0 + 0.006)], 'terra', (0, 0, 1))
    make('Inlay_Band', m, ao)
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, Z0, 'navy')
    poly(m, [(0, -0.4, Z0 + 0.003), (0.4, 0, Z0 + 0.003), (0, 0.4, Z0 + 0.003), (-0.4, 0, Z0 + 0.003)], 'gold', (0, 0, 1))
    disc(m, 0, 0, Z0 + 0.006, 0.12, 'terra', seg=8)
    make('Inlay_Knot', m, ao)
    # compass-rose medallion (8 x 8)
    m = new(pal)
    rings = ((3.9, 'navy', 32, 0.0), (3.6, 'cream', 32, 0.003), (3.3, 'terra', 32, 0.006), (3.0, 'marble', 32, 0.009),
             (1.2, 'tealM', 16, 0.018), (0.5, 'gold', 12, 0.021))
    for (r, c, s, dz) in rings:
        disc(m, 0, 0, Z0 + dz, r, c, seg=s)
    zs = Z0 + 0.012
    for i in range(8):   # eight-point star over the marble ring
        a = i / 8 * 2 * math.pi
        long = 2.95 if i % 2 == 0 else 2.0
        c = 'navy' if i % 2 == 0 else 'terraD'
        zz = zs if i % 2 else zs + 0.003
        for side in (-1, 1):
            b = a + side * (math.pi / 8)
            poly(m, [(0, 0, zz), (math.cos(a) * long, math.sin(a) * long, zz), (math.cos(b) * 0.9, math.sin(b) * 0.9, zz)],
                 c if side > 0 else ('gold' if i % 2 == 0 else 'terra'), (0, 0, 1))
    for i in range(16):   # gold dots on the terracotta ring
        a = i / 16 * 2 * math.pi
        disc(m, math.cos(a) * 3.15, math.sin(a) * 3.15, Z0 + 0.009, 0.07, 'gold', seg=6)
    make('Inlay_Rose', m, ao)
    # food court checker squares (1 x 1)
    for name, c in (('Inlay_ChkA', 'terra'), ('Inlay_ChkB', 'cream')):
        m = new(pal)
        uq(m, -0.5, 0.5, -0.5, 0.5, Z0, c)
        make(name, m, ao)
    # entrance mat (3 x 2)
    m = new(pal)
    uq(m, -1.5, 1.5, -1.0, 1.0, Z0, 'sign')
    for (a, b, c0, c1) in ((-1.4, 1.4, -0.9, -0.82), (-1.4, 1.4, 0.82, 0.9), (-1.4, -1.32, -0.82, 0.82), (1.32, 1.4, -0.82, 0.82)):
        uq(m, a, b, c0, c1, Z0 + 0.003, 'gold')
    for i in range(5):
        uq(m, -1.1, 1.1, -0.6 + i * 0.3, -0.5 + i * 0.3, Z0 + 0.003, 'step')
    make('Mat', m, ao)


def build_ceiling(pal, ao):
    """roof pieces hang from the ceiling plane (origin there): glazed coffers on a 2 m grid, trusses, lamps, banners"""
    def coffer(m):
        # beams on the internal 2 m lines only (x = +/-1, y = +/-1): tiles join into one even grid
        for v in (-1.0, 1.0):
            m.bx(-2.0, 2.0, v - 0.1, v + 0.1, -0.4, -0.004, 'cream', cull='t', hull='noside')
            m.bx(v - 0.09, v + 0.09, -2.0, 2.0, -0.37, -0.004, 'cream', cull='t', hull='noend')
        dq(m, -2.0, 2.0, -2.0, 2.0, -0.012, 'skyglass')
        for (cx, cy) in ((-1.5, -1.5), (0.5, -1.5), (-1.5, 0.5), (0.5, 0.5)):
            for (a, b) in ((0.15, 0.3), (0.6, 0.72)):
                poly(m, [(cx + a - 0.5, cy - 0.5, -0.016), (cx + b - 0.5, cy - 0.5, -0.016), (cx + b + 0.3, cy + 0.5, -0.016), (cx + a + 0.3, cy + 0.5, -0.016)],
                     'glassL', (0, 0, -1))
    m = new(pal)
    coffer(m)
    make('Skylight', m, ao)
    m = new(pal)
    coffer(m)
    for k, (x, y, d) in enumerate(((0.0, 0.0, 2.6), (0.45, 0.25, 2.1), (-0.4, 0.3, 1.8), (0.1, -0.45, 2.3))):   # staggered globe pendants
        m.bm_((x, y, -0.02), (x, y, -d + 0.2), 0.016, 'dark', hull='none')
        m.cy((x, y, -d + 0.12), 0.07, 0.12, 0.1, 'brass', seg=6, hull='none', caps=False)
        m.sp((x, y, -d), 0.18 if k == 0 else 0.14, 'lightW' if k == 0 else 'light', seg=(7, 4), hull='none')
    make('SkylightLamp', m, ao)

    def truss(m):
        ty = -0.5      # truss line: game +0.5 from the tile centre (a cell centre, over the columns)
        m.bx(-2.0, 2.0, ty - 0.11, ty + 0.11, -0.3, -0.06, 'cream', hull='noside', cull='t')
        m.bx(-2.0, 2.0, ty - 0.1, ty + 0.1, -1.35, -1.15, 'cream', hull='noside')
        for i in range(4):
            xa, xb = -2.0 + i, -1.0 + i
            za, zb = (-0.3, -1.15) if i % 2 == 0 else (-1.15, -0.3)
            m.bm_((xa + 0.06, ty, za), (xb - 0.06, ty, zb), 0.08, 'white', hull='full')
        for x in (-1.0, 0.0, 1.0):
            m.bx(x - 0.03, x + 0.03, ty - 0.03, ty + 0.03, -1.15, -0.3, 'steel', hull='none', cull='tb')
        return ty
    m = new(pal)
    coffer(m)
    truss(m)
    make('SkyTruss', m, ao)
    for name, c, c2, word in (('SkyTrussBanA', 'rose', 'gold', 'SALE'), ('SkyTrussBanB', 'tealM', 'cream', 'SHOP')):
        m = new(pal)
        coffer(m)
        ty = truss(m)
        for bxc in (-1.0, 1.0):   # two banners hung on rods under the bottom chord, facing the long axis
            m.bx(bxc - 0.6, bxc + 0.6, ty - 0.03, ty + 0.03, -1.43, -1.37, 'brass', hull='none')
            for k in (-0.45, 0.45):
                m.bm_((bxc + k, ty, -1.35), (bxc + k, ty, -1.4), 0.02, 'dark', hull='none')
            # hangs to about 6.3 m: over the heads of people on the mezzanine (eye 6.05 m) only the pennant tip
            m.bx(bxc - 0.5, bxc + 0.5, ty - 0.012, ty + 0.012, -3.0, -1.42, c, hull='full', cull='t')
            poly(m, [(bxc - 0.5, ty, -3.0), (bxc + 0.5, ty, -3.0), (bxc, ty, -3.3)], c, (0, -1, 0))
            poly(m, [(bxc - 0.5, ty, -3.0), (bxc + 0.5, ty, -3.0), (bxc, ty, -3.3)], c, (0, 1, 0))
            for fy in (-1, 1):
                f = 'y-' if fy < 0 else 'y+'
                if word == 'SALE':
                    txt(m, 'SUMMER', bxc, ty + fy * 0.015, -1.9, 0.18, c2, face=f, font='display', maxw=0.86)
                    vdisc(m, (bxc, ty + fy * 0.016, -2.38), 0.3, c2, f, seg=14)
                    txt(m, 'SALE', bxc, ty + fy * 0.02, -2.38, 0.2, c, face=f, font='display', valign='m', maxw=0.5)
                else:
                    txt(m, 'SHOP', bxc, ty + fy * 0.015, -1.9, 0.2, c2, face=f, font='display', maxw=0.86)
                    vdisc(m, (bxc, ty + fy * 0.016, -2.38), 0.26, c2, f, seg=14)
                    txt(m, 'G', bxc, ty + fy * 0.02, -2.38, 0.26, c, face=f, font='serif', valign='m', maxw=0.4)
        make(name, m, ao)
    # round downlight (mezzanine ceiling) and under-deck downlight (hangs 0.4 under a deck cell's origin)
    m = new(pal)
    disc(m, 0, 0, -0.008, 0.25, 'chrome', seg=8, up=False)
    disc(m, 0, 0, -0.012, 0.17, 'lightW', seg=10, up=False)
    make('CeilLight', m, ao)
    m = new(pal)
    disc(m, 0, 0, -0.408, 0.22, 'chrome', seg=8, up=False)
    disc(m, 0, 0, -0.412, 0.14, 'lightW', seg=10, up=False)
    make('UnderLight', m, ao)


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    """mall entrance portal: sandstone piers, teal lintel, GALLERIA sign and a sunburst fan window above (both faces)"""
    m = new(pal)
    for sx in (-1, 1):
        m.bx(sx * 1.77 - 0.27, sx * 1.77 + 0.27, -0.6, 0.6, 0.0, 3.4, 'stone2', cull='')
        m.bx(sx * 1.77 - 0.31, sx * 1.77 + 0.31, -0.64, 0.64, 0.0, 0.3, 'dark', cull='b')
        m.bx(sx * 1.77 - 0.31, sx * 1.77 + 0.31, -0.64, 0.64, 3.2, 3.5, 'cream')
    m.bx(-2.02, 2.02, -0.62, 0.62, 3.5, 4.1, 'tealD')
    m.bx(-1.5, 1.5, -0.49, 0.49, 4.1, H, 'stone', cull='t')
    for fy in (-1, 1):
        y = fy * 0.62
        for k in range(10):
            fq(m, -1.5 + k * 0.3 + 0.02, -1.5 + (k + 1) * 0.3 - 0.02, -0.625, 3.62, 3.98, 'amber' if k % 2 else 'ink') if fy < 0 else \
                bq(m, -1.5 + k * 0.3 + 0.02, -1.5 + (k + 1) * 0.3 - 0.02, 0.625, 3.62, 3.98, 'amber' if k % 2 else 'ink')
        yy = fy * 0.49
        # name plaque
        m.bx(-1.48, 1.48, min(yy, yy + fy * 0.1), max(yy, yy + fy * 0.1), 5.0, 5.75, 'navy', cull='')
        f = 'y-' if fy < 0 else 'y+'
        txt(m, 'Galleria', 0.0, fy * 0.594, 5.3, 0.34, 'gold', face=f, font='serif', maxw=2.7)
        txt(m, 'SHOPPING CENTRE', 0.0, fy * 0.594, 5.1, 0.08, 'cream', face=f, font='cond', maxw=2.0, spacing=1.2)
        # sunburst fan window
        cz, r = 6.1, 1.35
        for i in range(8):
            a0, a1 = i / 8 * math.pi, (i + 1) / 8 * math.pi
            pts = [(0, cz), (math.cos(a0) * r, cz + math.sin(a0) * r), (math.cos(a1) * r, cz + math.sin(a1) * r)]
            poly(m, [(p[0], fy * 0.495, p[1]) for p in pts], 'skyglass' if i % 2 else 'glassL', (0, fy, 0))
        for i in range(9):
            a = i / 8 * math.pi
            m.bm_((math.cos(a) * 0.2, fy * 0.52, cz + math.sin(a) * 0.2), (math.cos(a) * 1.4, fy * 0.52, cz + math.sin(a) * 1.4), 0.06, 'cream', hull='none')
        for i in range(12):
            a0, a1 = i / 12 * math.pi, (i + 1) / 12 * math.pi
            m.bm_((math.cos(a0) * 1.45, fy * 0.53, cz + math.sin(a0) * 1.45), (math.cos(a1) * 1.45, fy * 0.53, cz + math.sin(a1) * 1.45), 0.12 - 0.014 * (i % 2), 'stone2', hull='full')
        m.bx(-1.5, 1.5, min(fy * 0.49, fy * 0.6), max(fy * 0.49, fy * 0.6), 8.9, 9.15, 'stone2', cull='')
    make('GateFrame', m, ao)
    m = new(pal)
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.55 + (i + 0.5) * (Hs - 0.55) / n
        m.box((0, 0, z), (3.0, 0.12, (Hs - 0.55) / n - 0.06), 'steel' if i % 2 else 'chrome', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.14, 0.5), 'ink' if k % 2 else 'amber', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.16, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor walls, 1 m along Blender Y, 0.5 thick, full height; inner face +X: dado, ad light boxes, cornice
    for name in ('TrailWall', 'TrailWall_Ad'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'stone', hull='noend', cull='t')
        m.bx(0.25, 0.29, -0.5, 0.5, 0.0, 0.25, 'stone2', hull='noend', cull='b')
        m.bx(0.25, 0.28, -0.5, 0.5, 1.0, 1.06, 'terra', hull='none')
        m.bx(0.25, 0.3, -0.5, 0.5, 3.6, 3.75, 'cream', hull='noend')
        m.bx(0.25, 0.32, -0.5, 0.5, 8.9, 9.15, 'stone2', hull='noend')
        if name == 'TrailWall_Ad':
            m.bx(0.25, 0.31, -0.42, 0.42, 1.25, 3.3, 'dark')
            rq(m, 0.313, -0.36, 0.36, 1.31, 3.24, 'lightW')
            rq(m, 0.316, -0.36, 0.36, 1.31, 2.0, 'rose')
            m.cy((0.317, 0.0, 2.6), 0.22, 0.22, 0.003, 'yellow', seg=10, rot=(0, 90, 0), hull='none')
            txt(m, 'Late Nights', 0.32, 0.0, 1.66, 0.11, 'paper', face='x+', font='script', maxw=0.66)
            txt(m, 'THURSDAYS UNTIL 9', 0.32, 0.0, 1.45, 0.05, 'paper', face='x+', font='cond', maxw=0.6)
            txt(m, 'G', 0.324, 0.0, 2.6, 0.24, 'rose', face='x+', font='serif', valign='m', maxw=0.3)
        else:
            rq(m, 0.253, -0.4, 0.4, 1.3, 3.3, 'stone2')
            rq(m, 0.256, -0.34, 0.34, 1.36, 3.24, 'stone')
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.12, 'chrome', seg=20)
    m.cy((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, hull='none')
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cy((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, hull='none')
    make('Hatch', m, ao, bevel=0.015)


def build_kit_mall(ao):
    pal = Palette(FAM)
    build_shopfronts(pal, ao)
    build_walls(pal, ao)
    build_rail(pal, ao)
    build_columns(pal, ao)
    build_escalator(pal, ao)
    build_elevator(pal, ao)
    build_props(pal, ao)
    build_fountain(pal, ao)
    build_guestdesk(pal, ao)
    build_floor(pal, ao)
    build_ceiling(pal, ao)
    build_gate(pal, ao)
    import mall_rooms
    mall_rooms.build_rooms(pal, ao)
    print('kit-mall: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(k for k in TRIS if '_Room_' in k):
        print('  room %-36s %6d' % (n, TRIS[n]))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:16]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-mall'
BUILD = build_kit_mall
