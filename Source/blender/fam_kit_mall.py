"""INKBOLT asset family: kit-mall ("Galleria", a two-storey shopping mall under a glazed roof).

Storefronts: every wall cell stacks a ground-floor and an upper-floor shopfront module (the theme's wall chooser
returns both). Six brands (STYLE fashion, TECH, CAFE, BOOKS, TOYS, GEMS jewellery), each with its own frame and sign
colours, pixel-lettered name across the three middle modules of a 5 m bay, awnings or light boxes, blade signs and a
lit interior you see through the (open, glint-marked) shop windows: mannequins, shelves, counters, books, toys,
display cases. Sandstone pilasters with sconces part the bays; corner blocks and pilasters close the interiors.
Circulation: a steel-and-glass escalator (stair-block collision kept), baluster railings (half modules the engine
links into runs), columns under / over the mezzanine edge, a framed glass lift shaft, a cab and sliding door leaves
(the engine moves cab and leaves). Atrium: tiered fountain, round Guest Services desk with INFO drums, coffee / sweets
/ gadget kiosks, food-court tables and food stalls, palm planters, flower planters, benches, bins, directory totems,
department-store podiums. Floor inlays (an "@layer 0" grid: diamonds, border bands, compass-rose medallions, food-court
checker, entrance mats) and the roof (an "@layer 9.5" grid: glazed coffers, lattice trusses with hanging banners and
pendant lamps, downlights), plus under-deck downlights ("@layer 4.5"). Gate portal with GALLERIA lettering, corridor
walls, hatch.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front. Decks stand at 4.5 m (slab 4.1-4.5); the ceiling is at 9.5 m. Ceiling pieces hang from
their origin (the ceiling plane). Flat detail is painted as single faces without an outline shell (PM hull='none').
"""
import math

import bpy  # noqa: F401
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull

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


# ---------------------------------------------------------------- pixel lettering (3 x 5 font)
FONT = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'], 'C': ['.##', '#..', '#..', '#..', '.##'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'], 'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'], 'I': ['###', '.#.', '.#.', '.#.', '###'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'], 'M': ['#.#', '###', '###', '#.#', '#.#'],
    'N': ['##.', '#.#', '#.#', '#.#', '#.#'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'R': ['##.', '#.#', '##.', '#.#', '#.#'], 'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'W': ['#.#', '#.#', '###', '###', '#.#'], 'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'], 'Z': ['###', '..#', '.#.', '#..', '###'], ' ': ['...', '...', '...', '...', '...'],
}


def word_rects(word, px, xc=0.0, z0=0.0):
    """rectangles (x0, x1, z0, z1) of a word in the pixel font, centred on xc, bottom at z0"""
    n = len(word)
    width = (n * 4 - 1) * px
    out = []
    for i, ch in enumerate(word):
        g = FONT[ch]
        lx = xc - width / 2 + i * 4 * px
        runs = []   # merge row runs vertically
        for row in range(5):
            line = g[row]
            c = 0
            while c < 3:
                if line[c] == '#':
                    e = c
                    while e + 1 < 3 and line[e + 1] == '#':
                        e += 1
                    runs.append((row, c, e))
                    c = e + 1
                else:
                    c += 1
        used = set()
        for k, (row, c0, c1) in enumerate(runs):
            if k in used:
                continue
            r1 = row
            for j in range(k + 1, len(runs)):
                rj, a, b = runs[j]
                if rj == r1 + 1 and a == c0 and b == c1:
                    used.add(j)
                    r1 = rj
            out.append((lx + c0 * px, lx + (c1 + 1) * px, z0 + (4 - r1) * px, z0 + (5 - row) * px))
    return out


def letters(m, rects, y, c, clip=None, off=0.0, back=False, xc=0.0):
    """paint letter rectangles on a plane at y (front-facing, or back-facing mirrored about xc when back=True)"""
    for (x0, x1, z0, z1) in rects:
        x0, x1 = x0 - off, x1 - off
        if clip:
            x0, x1 = max(x0, clip[0]), min(x1, clip[1])
            if x1 - x0 < 0.004:
                continue
        if back:
            bq(m, 2 * xc - x1, 2 * xc - x0, y, z0, z1, c)
        else:
            fq(m, x0, x1, y, z0, z1, c)


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
POS = ['WinA', 'SignL', 'Door', 'SignR', 'WinB']   # k = 1..5 in a bay (the theme mirrors L / R on N and E faces)
GY = -0.40      # glass line (glints); interiors start behind it
BACK = 2.2      # interior back wall


def shop_front(m, brand, pos, S):
    word, band, lc, frame, flo, wall, awn = BRANDS[brand]
    z0, kick, wtop, s0, s1, top, ceil = S['z0'], S['kick'], S['wtop'], S['s0'], S['s1'], S['top'], S['ceil']
    door = pos == 'Door'
    # frame: mullion halves at the module edges (they pair up with the neighbours), transom, kick plate
    for sx in (-1, 1):
        m.bx(sx * 0.5 - (0.04 if sx > 0 else 0), sx * 0.5 + (0.04 if sx < 0 else 0), -0.54, -0.37, z0, wtop, frame, hull='none', cull='ktb' + ('r' if sx > 0 else 'l'))
    m.bx(-0.5, 0.5, -0.545, -0.37, wtop, s0, frame, hull='none', cull='klrt')
    if not door:
        m.bx(-0.5, 0.5, -0.56, -0.37, z0, kick, 'stone2', hull='none', cull='kblr')
        glint(m, -0.42, 0.42, GY, kick, wtop)
    # sign band and letters (the word spans SignL / Door / SignR: bay x -1.5 .. 1.5)
    m.bx(-0.5, 0.5, -0.6, -0.37, s0, s1, band, hull='noside', cull='klrt')
    if pos in ('SignL', 'Door', 'SignR'):
        px = min(0.1, 2.6 / (len(word) * 4 - 1))
        rects = word_rects(word, px, 0.0, (s0 + s1) / 2 - 2.5 * px)
        off = {'SignL': -1.0, 'Door': 0.0, 'SignR': 1.0}[pos]
        letters(m, rects, -0.605, lc, clip=(-0.5, 0.5), off=off)
    else:   # brand roundel at the bay ends
        vdisc(m, (0, -0.604, (s0 + s1) / 2), 0.21, lc, 'y-', seg=10)
        vdisc(m, (0, -0.607, (s0 + s1) / 2), 0.13, band, 'y-', seg=8)
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
        vdisc(m, (-0.386, -0.685, zb), 0.17, lc, 'x+', seg=10)
        vdisc(m, (-0.444, -0.685, zb), 0.17, lc, 'x-', seg=10)
    # interior shell: floor, back wall, ceiling with a light strip
    uq(m, -0.5, 0.5, -0.37, BACK, z0 + 0.012, flo)
    fq(m, -0.5, 0.5, BACK, z0, ceil, wall)
    dq(m, -0.5, 0.5, -0.37, BACK, ceil, 'cream')
    dq(m, -0.5, 0.5, 0.5, 0.7, ceil - 0.004, 'lightW')
    if door:
        door_leaves(m, S, frame)
    else:
        m.bx(-0.5, 0.5, -0.37, 0.15, z0, kick - 0.01, 'cream', hull='none', cull='kblr')   # window plinth
    n0 = m.nshape
    contents(m, brand, pos, S)
    for k in range(n0 + 1, m.nshape + 1):   # shop contents seen through the glass: no outline shells
        m.hmode[k] = 'none'


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
    m.bx(-0.5, 0.5, -0.5, -0.37, d, S['wtop'], 'sign', hull='noside', cull='klr')
    fq(m, -0.2, 0.2, -0.503, d + 0.12, S['wtop'] - 0.12, 'lightW')
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


def contents(m, brand, pos, S):
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
        for i in range(3):
            fq(m, -0.34, 0.1 + 0.08 * (i % 2), BACK - 0.006, z0 + 1.75 + i * 0.2, z0 + 1.8 + i * 0.2, 'paper')
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
        back_sides(m)
        make(name, m, ao)
    # zone corners: a block that fills the corner cell and closes the shop interiors on both walls
    for name, (x0, x1, y0, y1, keep) in (('NW', (-3.2, 0.5, -0.5, 3.2, 'rf')), ('NE', (-0.5, 3.2, -0.5, 3.2, 'lf')),
                                         ('SW', (-3.2, 0.5, -3.2, 0.5, 'rk')), ('SE', (-0.5, 3.2, -3.2, 0.5, 'lk'))):
        m = new(pal)
        cull = ''.join(ch for ch in 'tbfklr' if ch not in keep)
        m.bx(x0, x1, y0, y1, 0.0, H, 'cream', hull='none', cull=cull)
        make('Corner_' + name, m, ao)
    # blank modules (bay ends, beside the gates): directory board / lit poster below, poster / clock above
    for name in ('Blank_Map', 'Blank_Ad'):
        m = new(pal)
        fq(m, -0.5, 0.5, -0.5, 0.0, H, 'stone')
        m.bx(-0.5, 0.5, -0.56, -0.5, 0.0, 0.3, 'stone2', hull='noside', cull='kb')
        m.bx(-0.5, 0.5, -0.56, -0.5, 4.5, 4.75, 'stone2', hull='noside', cull='k')
        m.bx(-0.5, 0.5, -0.62, -0.5, 8.9, 9.12, 'stone2', hull='noside', cull='k')
        m.bx(-0.42, 0.42, -0.6, -0.5, 0.75, 2.75, 'dark', hull='full', cull='k')
        if name == 'Blank_Map':
            fq(m, -0.37, 0.37, -0.603, 0.82, 2.68, 'cream')
            for (a, b, c0, c1, c) in ((-0.33, -0.05, 2.2, 2.62, 'rose'), (-0.01, 0.33, 2.2, 2.62, 'sky'), (-0.33, 0.33, 1.95, 2.13, 'stone2'),
                                       (-0.33, -0.12, 1.35, 1.88, 'mint'), (-0.08, 0.12, 1.35, 1.88, 'orange'), (0.16, 0.33, 1.35, 1.88, 'violet'),
                                       (-0.33, 0.33, 1.1, 1.28, 'stone2'), (-0.33, 0.0, 0.88, 1.04, 'yellow')):
                fq(m, a, b, -0.606, c0, c1, c)
            m.cy((0.12, -0.61, 1.0), 0.05, 0.05, 0.004, 'redT', seg=8, rot=(90, 0, 0), hull='none')
            fq(m, -0.42, 0.42, -0.603, 2.75, 2.95, 'tealM')
            # upper: clock
            m.cy((0, -0.5, 6.6), 0.42, 0.42, 0.08, 'brass', seg=16, rot=(90, 0, 0))
            m.cy((0, -0.585, 6.6), 0.36, 0.36, 0.006, 'cream', seg=16, rot=(90, 0, 0), hull='none')
            m.bx(-0.015, 0.015, -0.603, -0.598, 6.58, 6.88, 'sign', hull='none')
            m.bx(-0.012, 0.2, -0.597, -0.592, 6.585, 6.615, 'sign', hull='none')
        else:
            fq(m, -0.37, 0.37, -0.603, 0.82, 2.68, 'lightW')
            fq(m, -0.37, 0.37, -0.606, 0.82, 1.5, 'tealM')
            m.cy((0.05, -0.609, 1.95), 0.26, 0.26, 0.004, 'orange', seg=12, rot=(90, 0, 0), hull='none')
            m.cy((0.05, -0.612, 1.95), 0.17, 0.17, 0.004, 'yellow', seg=12, rot=(90, 0, 0), hull='none')
            letters(m, word_rects('SALE', 0.045, 0.0, 1.0), -0.61, 'paper')
            # upper: tall poster
            m.bx(-0.4, 0.4, -0.6, -0.5, 5.2, 8.4, 'dark', hull='full', cull='k')
            fq(m, -0.34, 0.34, -0.603, 5.27, 8.33, 'rose')
            fq(m, -0.34, 0.34, -0.606, 5.27, 6.2, 'violetD')
            m.sp((0.0, -0.62, 7.3), 0.25, 'yellow', seg=(10, 6), scale=(1, 0.25, 1))
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
    m = new(pal)
    rail(m, -0.5, -0.04)
    make('Rail', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0, 1.1)])
    m = new(pal)
    rail(m, -0.5, 0.5)
    make('RailFull', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0.5, 1.1)])
    m = new(pal)
    m.bx(-0.045, 0.045, -0.045, 0.045, 0.0, 1.08, 'cream', cull='b')
    m.bx(-0.06, 0.06, -0.06, 0.06, 1.08, 1.13, 'brass', cull='b')
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
    letters(m, word_rects('LIFT', 0.07, 0.0, 7.63), -1.625, 'gold')
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
    make('Bench', m, ao, cols=[col_box(-0.95, -0.27, 0, 0.95, 0.27, 0.47)])
    # bin: two-tone recycling bin
    m = new(pal)
    m.bx(-0.26, 0.26, -0.2, 0.2, 0.0, 0.85, 'steel', cull='b')
    m.bx(-0.28, 0.0, -0.22, 0.22, 0.85, 0.97, 'tealM')
    m.bx(0.0, 0.28, -0.22, 0.22, 0.85, 0.97, 'orange')
    fq(m, -0.2, -0.04, -0.203, 0.4, 0.62, 'tealM')
    fq(m, 0.04, 0.2, -0.203, 0.4, 0.62, 'orange')
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
    make('AdPillar', m, ao, cols=[col_box(-0.36, -0.36, 0, 0.36, 0.36, 2.6)])
    # kiosks 3 x 2 (solid as a whole): coffee cart (canopy), sweets (striped parasol, jars), gadgets (light-box header)
    for name, c, c2 in (('Kiosk_A', 'orange', 'cream'), ('Kiosk_B', 'rose', 'paper'), ('Kiosk_C', 'sky', 'skyL')):
        m = new(pal)
        m.bx(-1.3, 1.3, -0.7, 0.7, 0.0, 0.12, 'sign', cull='b')
        m.bx(-1.25, 1.25, -0.65, 0.65, 0.12, 1.0, 'cream')
        for sy in (-1, 1):
            fq(m, -1.1, 1.1, -0.653, 0.25, 0.85, c) if sy < 0 else bq(m, -1.1, 1.1, 0.653, 0.25, 0.85, c)
        m.bx(-1.35, 1.35, -0.75, 0.75, 1.0, 1.06, 'wood')
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
            letters(m, word_rects('CAFE', 0.05, 0.0, 2.2), -0.865, 'gold')
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
                if sy < 0:
                    letters(m, word_rects('TECH', 0.07, 0.0, 2.3), -0.205, 'paper')
                else:
                    letters(m, word_rects('TECH', 0.07, 0.0, 2.3), 0.205, 'paper', back=True)
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
    for name, word, c, c2 in (('Stall_Pizza', 'PIZZA', 'redT', 'yellow'), ('Stall_Noodle', 'WOK', 'orange', 'sign'), ('Stall_Burger', 'BURGER', 'yellow', 'redT')):
        m = new(pal)
        m.bx(-2.0, 2.0, 0.5, 1.0, 0.0, 3.4, 'cream', cull='b')            # back wall
        m.bx(-2.0, -1.9, -1.0, 0.5, 0.0, 3.4, c, cull='b')
        m.bx(1.9, 2.0, -1.0, 0.5, 0.0, 3.4, c, cull='b')
        m.bx(-1.9, 1.9, -0.95, -0.35, 0.0, 1.05, c2 if c2 != 'sign' else 'wood2', cull='b')   # counter
        fq(m, -1.7, 1.7, -0.953, 0.15, 0.9, c)
        m.bx(-1.9, 1.9, -1.0, -0.3, 1.05, 1.1, 'chrome')
        m.bx(-1.6, 1.6, -0.8, -0.45, 1.1, 1.35, 'glassL', hull='full', cull='kb')
        for i in range(4):
            x = -1.2 + i * 0.8
            m.cy((x, -0.62, 1.1), 0.18, 0.18, 0.04, ('orange', 'yellow', 'greenT', 'redT')[(i + len(word)) % 4], seg=8, hull='none')
        for i in range(3):   # menu boards
            x = -1.25 + i * 1.25
            m.bx(x - 0.55, x + 0.55, 0.42, 0.5, 2.0, 2.8, 'sign', hull='full')
            fq(m, x - 0.45, x + 0.45, 0.417, 2.55, 2.7, c2 if c2 != 'sign' else 'gold')
            for j in range(3):
                fq(m, x - 0.45, x + 0.1 - 0.1 * j, 0.417, 2.1 + j * 0.13, 2.16 + j * 0.13, 'paper')
        m.bx(-2.05, 2.05, -1.1, 0.55, 3.0, 3.6, c)                         # sign box
        letters(m, word_rects(word, 0.08, 0.0, 3.1), -1.105, c2 if c2 != 'sign' else 'paper')
        make(name, m, ao, cols=[col_box(-2.0, -1.0, 0, 2.0, 1.0, 3.6)])
    # department store podium (2 x 1): white plinth, two mannequins, a SALE sign
    m = new(pal)
    m.cy((0, 0, 0), 0.9, 0.9, 0.22, 'cream', seg=14)
    m.cy((0, 0, 0.22), 0.92, 0.92, 0.03, 'gold', seg=14, hull='none')
    figure(m, -0.4, 0.0, 0.25, 'tealM', legs='navy')
    figure(m, 0.4, 0.05, 0.25, 'orange', legs='cream')
    m.bx(-0.2, 0.2, -0.35, -0.3, 0.25, 0.75, 'sign')
    letters(m, word_rects('SALE', 0.025, 0.0, 0.5), -0.355, 'yellow')
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
    rects = word_rects('INFO', 0.075, 0.0, 3.11)
    letters(m, rects, -0.955, 'paper')
    letters(m, rects, 0.955, 'paper', back=True)
    for (x0, x1, z0, z1) in rects:
        rq(m, 0.955, x0, x1, z0, z1, 'paper')
        lq(m, -0.955, -x1, -x0, z0, z1, 'paper')
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
            rects = word_rects(word, 0.055, bxc, -1.95)
            letters(m, rects, ty - 0.015, c2)
            letters(m, rects, ty + 0.015, c2, back=True, xc=bxc)
            vdisc(m, (bxc, ty - 0.016, -2.5), 0.26, c2, 'y-', seg=10)
            vdisc(m, (bxc, ty + 0.016, -2.5), 0.26, c2, 'y+', seg=10)
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
        rects = word_rects('GALLERIA', 0.09, 0.0, 5.15)
        letters(m, rects, -0.595, 'gold') if fy < 0 else letters(m, rects, 0.595, 'gold', back=True)
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
    print('kit-mall: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:16]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-mall'
BUILD = build_kit_mall
