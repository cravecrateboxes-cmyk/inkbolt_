"""INKBOLT asset family: kit-island ('Lagoon Island').

A wide tropical island on a bright day, ringed by open ocean: sandy beaches and grassy dunes, palm groves and dense
jungle thickets, warm basalt rocks, tide pools, freshwater ponds with reeds and lily pads, a big lagoon lake with a
palm islet, beach huts on stilts, a jetty, boats pulled up on the sand, crates and barrels washed ashore, a ruined
stone lookout, a red-and-white lighthouse on its rocks and a small research outpost the robots have taken over
(container lab, radio mast, solar array, robot charging pods, sandbag lines).

Conventions (see src/game/zones.js, src/data/themes/island.js and kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * Wall modules ('#') face Blender -Y (game +Z); the theme sets wall.facing = 'open', so the engine turns that face
    toward the module's open side. The '2' modules (Jungle_A ...) are 2 m wide and centred on their cell (the theme
    puts one on every other cell of a straight run); the '1' modules fill run ends; Corner_* are round clumps.
    Modules are 2 m deep (they fill the back cell of a 2-thick edge) and rise well above the 4.2 m wall collision.
  * Sea walls ('{' / '}', 1 m) are low rock-armoured breakwaters on the zone edges that face the ocean; the theme
    gives them a tall (invisible, justified) collision box. Front (-Y) = the beach side.
  * Water never fights the sand: every flat decal sits on its own height (Z table, >= 4 mm apart) above the floor
    paint (0.004 m), and the pieces of one zone never overlap the same decal type.
  * Wading: ponds, tide pools and the lagoon are shallow and walkable (no collision); only rocks, palms and the
    islet carry _COL boxes.
  * Backdrop_* pieces sit on the island outside the zones and out at sea (placed by the theme's backdrop builder);
    Sea_Glint is the shimmer dash the theme scatters over the ocean as one animated instanced mesh.
"""
import math
import random

import bpy  # must load before bmesh/mathutils  # noqa: F401
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, srt, rock_pts, clamp_pts, shutter_hull

FAM = 'kit-island'
PFX = 'KIT_ISLAND_'
ib_lib.GLB[FAM] = 'fps-kit-island.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02

ib_lib.PALETTES[FAM] = BASE + [
    ('sand', '#F2DDA4'), ('sand2', '#E2C68A'), ('wet', '#D2B27A'),
    ('grass', '#84C860'), ('grass2', '#63AE4E'), ('grass3', '#B0DE7A'),
    ('leaf', '#3DAA5C'), ('leaf2', '#2A8A4E'), ('leaf3', '#6FCB68'), ('leafd', '#1F6E48'),
    ('frond', '#4CBF5E'), ('frond2', '#2F9A4C'),
    ('trunk', '#B88A5A'), ('trunk2', '#977048'), ('coco', '#7A5A36'),
    ('rock', '#ABA59B'), ('rock2', '#8C857C'), ('rock3', '#CCC5B8'), ('rockd', '#6C665F'), ('moss', '#7DAA58'),
    ('water', '#5ED6DF'), ('water2', '#38B9D8'), ('waterd', '#2A92C8'), ('foam', '#F4FFFF'),
    ('lily', '#4FAF55'), ('flower', '#FF8FB8'), ('reed', '#8FBF52'), ('cattail', '#8A5B3A'),
    ('wood', '#C68B55'), ('wood2', '#A06D3E'), ('plank', '#DDB07A'), ('drift', '#CDB48E'), ('drift2', '#A8916E'),
    ('rope', '#E3CC96'), ('thatch', '#E3BC68'), ('thatch2', '#C69A48'), ('hutwall', '#E9D6A8'),
    ('boat', '#3FA3D8'), ('boat2', '#2D7FB0'), ('boatred', '#E6584A'),
    ('metal', '#A3AEBA'), ('metal2', '#707C8A'), ('panel', '#355A92'), ('panel2', '#6A97D2'), ('glow', '#FFE48A'),
    ('flame', '#FF7A3D'), ('crate', '#C99560'), ('barrel', '#D46A3A'), ('barrel2', '#3D84B6'), ('coral', '#F2876F'),
    ('far', '#86B796'), ('farrock', '#A9B6BC'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# flat decal heights (m above the ground; the engine paints the zone floor at 0.004 and the trail arrows at 0.02)
Z = {'grass': 0.010, 'flower': 0.014, 'wet': 0.026, 'rim': 0.032, 'foam': 0.038, 'water': 0.044, 'water2': 0.050,
     'waterd': 0.056, 'lily': 0.062, 'glint': 0.068}
WALL_H = 4.2


# ================================================================ helpers
def _vs(k, pts):
    P = k.m.parent
    return [k.m.bm.verts.new(P @ Vector(p)) for p in pts]


def leafcol(top='leaf3', mid='leaf', low='leaf2'):
    def fn(f):
        n = f.normal
        return top if n.z > 0.5 else (low if n.z < -0.25 else mid)
    return fn


def rockcol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.72:
        return 'rock3'
    if n.z < -0.3 or c.z < 0.18:
        return 'rock2'
    return 'rock'


def blob(k, rnd, cx, cy, z0, rx, ry, h, col=None, n=7):
    """Rounded foliage / bush mass: convex hull of a jittered squashed ellipsoid."""
    pts = []
    for ring, (zf, rf) in enumerate(((0.0, 0.62), (0.4, 1.0), (0.78, 0.66))):
        for i in range(n):
            a = (i + 0.5 * ring + rnd.uniform(-0.25, 0.25)) / n * 2 * math.pi
            kk = rnd.uniform(0.82, 1.08) * rf
            pts.append((cx + math.cos(a) * rx * kk, cy + math.sin(a) * ry * kk, z0 + h * (zf + rnd.uniform(-0.04, 0.04))))
    pts.append((cx + rnd.uniform(-0.1, 0.1) * rx, cy + rnd.uniform(-0.1, 0.1) * ry, z0 + h))
    return k.hullp(pts, col or leafcol())


def rock(k, rnd, cx, cy, rx, ry, h, z0=0.0, n=7, lim=None, ylim=None):
    pts = rock_pts(rnd, (cx, cy), rx, ry, h, z0=z0, n=n, top=3)
    if lim:
        pts = clamp_pts(pts, lim, ylim)
    return k.hullp(pts, rockcol)


def star(k, c, r, h, color, pts=7, inner=0.4, droop=0.5, phase=0.0, under=0.12, under_color=None, ink=True):
    """Star-section umbrella (palm crown / fern / grass tuft): pts tips at radius r drooping, apex h above c."""
    cx, cy, cz = c
    ring = []
    for i in range(pts * 2):
        a = math.radians(phase) + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        ring.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz - (droop if i % 2 == 0 else droop * 0.25)))
    vs = _vs(k, ring + [(cx, cy, cz + h), (cx, cy, cz + h * under)])
    N = len(ring)
    A, B = vs[N], vs[N + 1]
    side, bot = [], []
    for i in range(N):
        j = (i + 1) % N
        side.append(k.m.bm.faces.new((vs[i], vs[j], A)))
        bot.append(k.m.bm.faces.new((vs[j], vs[i], B)))
    k._tag(side + bot, color)
    if under_color:
        ui = k.pal.index(under_color)
        for f in bot:
            f.material_index = ui
    k._mark(ink)


def frond(k, rnd, T, a, r, w=0.62):
    """One palm frond: a rising inner blade and a drooping pointed outer blade (two thin convex hulls)."""
    dx, dy = math.cos(a), math.sin(a)
    sx, sy = -dy, dx
    up = rnd.uniform(0.12, 0.3) * r
    p0 = (T[0] + dx * 0.12, T[1] + dy * 0.12, T[2])
    p1 = (T[0] + dx * r * 0.5, T[1] + dy * r * 0.5, T[2] + up)
    p2 = (T[0] + dx * r, T[1] + dy * r, T[2] + up - r * rnd.uniform(0.55, 0.8))
    t = 0.03

    def pts(p, hw):
        return [(p[0] + sx * hw, p[1] + sy * hw, p[2] + dz) for dz in (-t, t)] + [(p[0] - sx * hw, p[1] - sy * hw, p[2] + dz) for dz in (-t, t)]
    col = lambda f: 'frond' if f.normal.z > 0 else 'frond2'
    k.hullp([(p0[0], p0[1], p0[2] - t), (p0[0], p0[1], p0[2] + t)] + pts(p1, w * 0.5), col)
    q1 = (p1[0] - dx * 0.04, p1[1] - dy * 0.04, p1[2] - 0.012)       # tip blade starts a little inside, narrower
    k.hullp(pts(q1, w * 0.44) + [(p2[0], p2[1], p2[2] - t), (p2[0], p2[1], p2[2] + t)], col)


def palm(k, rnd, x, y, h, lean=0.18, ang=None, r=1.7, z0=0.0, nuts=True, n=6):
    """Leaning palm: two tapered trunk segments, a coconut cluster and n arching fronds."""
    ang = rnd.uniform(0, 2 * math.pi) if ang is None else ang
    dx, dy = math.cos(ang), math.sin(ang)
    pts = []
    for t in (0.0, 0.5, 1.0):
        off = lean * h * t ** 1.6
        pts.append((x + dx * off, y + dy * off, z0 + h * t))
    rads = ((0.2, 0.172), (0.155, 0.12))      # the lower segment's collar stays proud of the upper one
    for i in range(2):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        d = b - a
        tilt = math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))
        az = math.degrees(math.atan2(d.y, d.x))
        k.cyl(a.x, a.y, a.z, rads[i][0], rads[i][1], d.length + 0.06, 'trunk' if i == 0 else 'trunk2', seg=5 if n < 6 else 6, rot=(0, tilt, az))
    tx, ty, tz = pts[2]
    if nuts:
        k.sph(tx, ty, tz - 0.02, 0.26, 'coco', seg=(6, 4))
    else:
        k.cyl(tx, ty, tz - 0.2, 0.2, 0.12, 0.3, 'frond2', seg=5)
    a0 = rnd.uniform(0, 2 * math.pi)
    for i in range(n):
        frond(k, rnd, (tx, ty, tz + 0.05), a0 + (i + rnd.uniform(-0.15, 0.15)) / n * 2 * math.pi, r * rnd.uniform(0.85, 1.1))
    return pts[2]


def fern(k, rnd, x, y, r, z0=0.0, col='leaf3'):
    star(k, (x, y, z0 + r * 0.5), r, r * 0.35, col, pts=6, inner=0.35, droop=r * 0.45, phase=rnd.uniform(0, 60), under_color='leaf2')


def tuft(k, rnd, x, y, r, z0=0.0, col='grass3'):
    """Dune grass: a spiky upright star."""
    star(k, (x, y, z0), r, r * 2.2, col, pts=5, inner=0.25, droop=-r * 0.9, phase=rnd.uniform(0, 70), under=0.05, under_color='grass2')


def wavy(k, x0, x1, y, z, w, c, n=6, amp=0.06):
    """Flat wavy dash (sea glint, foam lick): a strip of quads on z, ink-less."""
    for i in range(n):
        a, b = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
        ya, yb = y + amp * math.sin(i * 1.7), y + amp * math.sin((i + 1) * 1.7)
        ta = w * (0.4 + 0.6 * math.sin(math.pi * i / n))
        tb = w * (0.4 + 0.6 * math.sin(math.pi * (i + 1) / n))
        k.poly([(a, ya - ta / 2, z), (b, yb - tb / 2, z), (b, yb + tb / 2, z), (a, ya + ta / 2, z)], c, (0, 0, 1))


def plank_lines(k, x0, x1, y0, y1, z, n, c='wood2', along='y', w=0.025):
    """Ink-less plank seams on an upward deck face (3 mm proud)."""
    for i in range(1, n):
        if along == 'y':
            x = x0 + (x1 - x0) * i / n
            k.qz(x - w, x + w, y0 + 0.01, y1 - 0.01, z + 0.003, 1, c)
        else:
            y = y0 + (y1 - y0) * i / n
            k.qz(x0 + 0.01, x1 - 0.01, y - w, y + w, z + 0.003, 1, c)


# ================================================================ wall modules ('#', facing the open side = -Y)
def jungle(k, seed, W=2):
    """Dense jungle thicket: a fern-fringed bush at the foot, leafy masses behind, a palm leaning out over it."""
    rnd = random.Random(seed)
    k.begin()
    hw = W / 2
    n = 2 if W == 2 else 1
    blob(k, rnd, rnd.uniform(-0.1, 0.1), -0.15, 0, 0.5 * W + 0.08, 0.5, rnd.uniform(1.0, 1.5), leafcol('leaf3', 'leaf', 'leaf2'), n=6)
    for i in range(n):
        cx = -hw + (i + 0.5) * W / n + rnd.uniform(-0.2, 0.2)
        if rnd.random() < 0.7:
            fern(k, rnd, cx, -0.55, rnd.uniform(0.4, 0.62), col=('leaf3', 'grass2', 'leaf')[rnd.randrange(3)])
        blob(k, rnd, cx, 0.4, 0.8, 0.6 * W / n + 0.28, 0.75, rnd.uniform(2.4, 3.4), leafcol('leaf', 'leaf2', 'leafd'), n=6)
    blob(k, rnd, rnd.uniform(-0.3, 0.3) * W / 2, 1.0, 2.6, 0.55 * W + 0.2, 0.6, rnd.uniform(2.2, 3.4), leafcol('leaf3', 'leaf', 'leafd'), n=6)
    palm(k, rnd, rnd.uniform(-0.4, 0.4) * W / 2, 0.9, rnd.uniform(6.4, 8.4), lean=rnd.uniform(0.08, 0.2), ang=math.radians(rnd.uniform(235, 305)), r=2.0, nuts=False)
    return k


def rocks_mod(k, seed, W=2):
    """Warm basalt outcrop with a fern cap and moss on the ledges."""
    rnd = random.Random(seed)
    k.begin()
    hw = W / 2
    n = 2 if W == 2 else 1
    for i in range(n):
        cx = -hw + (i + 0.5) * W / n
        rock(k, rnd, cx, 0.3, 0.62 * W / n + 0.12, 0.95, rnd.uniform(2.6, 3.6), lim=hw + 0.1, ylim=1.5)
        rock(k, rnd, cx + rnd.uniform(-0.2, 0.2), -0.35, 0.42 * W / n + 0.05, 0.34, rnd.uniform(0.8, 1.3), lim=hw + 0.05, ylim=1.5)
    rock(k, rnd, rnd.uniform(-0.2, 0.2), 0.75, 0.45 * W + 0.1, 0.7, rnd.uniform(4.3, 5.2), z0=0.0, lim=hw + 0.1, ylim=1.5)
    blob(k, rnd, rnd.uniform(-0.3, 0.3), 0.7, 4.0, 0.5 * W, 0.6, 1.3, leafcol('leaf3', 'leaf', 'leaf2'))
    fern(k, rnd, rnd.uniform(-0.4, 0.4), -0.55, 0.45, col='moss')
    return k


def dune_mod(k, seed, W=2):
    """Grassy dune bank behind a driftwood fence (the fence and the dune grass say: no way through)."""
    rnd = random.Random(seed)
    k.begin()
    hw = W / 2 - 0.01
    pts = []
    yf, yb = rnd.uniform(-0.32, -0.14), rnd.uniform(1.4, 1.6)
    for i in range(5):
        x = -hw + 2 * hw * i / 4
        pts += [(x, yf, 0.0), (x, 0.2 + rnd.uniform(-0.08, 0.08), 1.5 + rnd.uniform(0, 0.25)), (x, 0.9, 2.5 + rnd.uniform(-0.15, 0.25)), (x, yb, 0.0)]
    k.hullp(pts, lambda f: 'grass' if f.normal.z > 0.55 else ('sand2' if f.normal.y < -0.2 else 'sand'))
    for i in range(int(W * 2)):
        x = -hw + 0.4 + i * (2 * hw - 0.8) / max(1, int(W * 2) - 1)
        tuft(k, rnd, x + rnd.uniform(-0.05, 0.05), rnd.uniform(0.4, 0.8), rnd.uniform(0.16, 0.24), z0=1.6 + rnd.uniform(0.0, 0.5))
    tuft(k, rnd, rnd.uniform(-0.5, 0.5), -0.2, 0.2, z0=0.25)
    # driftwood fence in front: leaning posts and a rope
    for i in range(W + 1 if W == 2 else 1):
        x = -hw + 0.18 + i * (2 * hw - 0.36) / max(1, W)
        if W == 1:
            x = 0.0
        k.cyl(x, -0.62 if W == 2 else -0.69, 0, 0.06, 0.05, 1.15 + rnd.uniform(-0.1, 0.1), 'drift', seg=5, rot=(rnd.uniform(-6, 6), 0, 0))
    ry, rz = (-0.66, 0.0) if W == 2 else (-0.71, -0.05)      # 1 m end modules overlap a 2 m one: keep their ropes apart
    k.bx(-hw + 0.05, hw - 0.05, ry, ry + 0.04, 0.78 + rz, 0.82 + rz, 'rope')
    k.bx(-hw + 0.05, hw - 0.05, ry, ry + 0.04, 0.4 + rz, 0.44 + rz, 'rope')
    return k


def corner(k, seed, kind):
    """Round clump for corners, notches and gate jambs: rocks + a palm, or a tall jungle clump."""
    rnd = random.Random(seed)
    k.begin()
    if kind == 'A':
        rock(k, rnd, 0, 0, 0.75, 0.75, rnd.uniform(3.4, 4.4), n=7, lim=0.8)
        rock(k, rnd, 0.1, 0.1, 0.55, 0.55, 5.0, z0=2.0, n=6, lim=0.7)
        blob(k, rnd, 0, 0, 4.8, 0.7, 0.7, 1.2)
        palm(k, rnd, 0.1, 0.2, 7.6, lean=0.12, r=1.8, z0=0.0, nuts=False)
    else:
        blob(k, rnd, 0, 0, 0, 0.85, 0.85, 2.0, leafcol('leaf3', 'leaf', 'leaf2'))
        blob(k, rnd, 0, 0.1, 1.6, 0.8, 0.8, 3.2, leafcol('leaf', 'leaf2', 'leafd'))
        blob(k, rnd, 0.1, 0, 4.2, 0.6, 0.6, 1.8, leafcol('leaf3', 'leaf', 'leafd'))
        palm(k, rnd, -0.1, 0.2, 8.4, lean=0.1, r=1.9)
        fern(k, rnd, 0, -0.75, 0.5)
    return k


def seawall(k, seed, kind):
    """Low rock-armoured breakwater (1 m run along X): stone wall + cap, armour rocks on the sea side (+Y),
    a little sand ramp on the beach side. B: a mooring post with a lifebuoy; C: a lamp post."""
    rnd = random.Random(seed)
    k.begin()
    k.bx(-0.5, 0.5, -0.12, 0.42, 0, 0.82, 'rock2')
    k.bx(-0.5, 0.5, -0.17, 0.47, 0.82, 0.96, 'rock3')
    for i in range(3):
        k.qy(-0.5 + i * 0.36 + 0.02, -0.5 + i * 0.36 + 0.3, 0.12 + (i % 2) * 0.28, 0.36 + (i % 2) * 0.28, -0.123, -1, 'rock')
    for i in range(2):
        rock(k, rnd, -0.25 + i * 0.5 + rnd.uniform(-0.08, 0.08), 0.85, 0.36, 0.42, rnd.uniform(0.7, 1.0), n=6, lim=0.62, ylim=1.4)
    if kind == 'B':
        k.cyl(0.0, -0.32, 0, 0.11, 0.1, 1.45, 'wood2', seg=6)
        k.cyl(0.0, -0.32, 1.45, 0.13, 0.13, 0.08, 'wood', seg=6)
        for i in range(8):
            a = i / 8 * 2 * math.pi
            k.bxr(math.cos(a) * 0.22, -0.46, 0.9 + math.sin(a) * 0.22, 0.13, 0.08, 0.13, 'boatred' if i % 2 else 'paper', rot=(0, -math.degrees(a), 0))
    elif kind == 'C':
        k.cyl(0.2, -0.3, 0, 0.06, 0.05, 1.9, 'metal2', seg=6)
        k.bx(0.08, 0.32, -0.42, -0.18, 1.9, 2.16, 'glow')
        k.cyl(0.2, -0.3, 2.16, 0.18, 0.04, 0.16, 'metal2', seg=4, rot=(0, 0, 45))
    return k


# ================================================================ props
def crate(k, seed, kind):
    """Washed-ashore crate (0.86 m) with plank seams, rope and a bit of seaweed; Small: the stacked lid crate."""
    rnd = random.Random(seed)
    k.begin(rnd.uniform(-8, 8))
    s = 0.5 if kind == 'Small' else 0.86
    hz = 0.48 if kind == 'Small' else 0.86
    h = s / 2
    k.bx(-h, h, -h, h, 0, hz, 'crate', bevel=True)
    for f in (-1, 1):
        for i in (1, 2):
            z = hz * i / 3
            k.qy(-h + 0.04, h - 0.04, z - 0.015, z + 0.015, f * (h + 0.003), f, 'wood2')
            k.qx(-h + 0.04, h - 0.04, z - 0.015, z + 0.015, f * (h + 0.003), f, 'wood2')
    k.qz(-h + 0.06, h - 0.06, -0.04, 0.04, hz + 0.003, 1, 'wood2')
    if kind == 'B':
        k.bx(-h - 0.02, h + 0.02, -0.06, 0.06, hz * 0.55, hz * 0.62, 'rope')
        k.bx(-0.06, 0.06, -h - 0.02, h + 0.02, hz * 0.4, hz * 0.47, 'rope')
        star(k, (0.15, -0.1, hz + 0.01), 0.28, 0.04, 'leaf2', pts=5, inner=0.4, droop=0.0, under=0.1)
    return k


def barrels(k, seed, kind):
    rnd = random.Random(seed)
    k.begin()

    def barrel(x, y, c='barrel'):
        k.cyl(x, y, 0, 0.3, 0.3, 0.9, c, seg=10)
        for t in (0.12, 0.78):
            k.cyl(x, y, t * 0.9, 0.312, 0.312, 0.07, 'metal2', seg=10, caps=False, ink=False)
    if kind == 'A':
        barrel(-0.12, 0.05, c='barrel')
        k.cyl(-0.12, 0.05, 0.9, 0.22, 0.22, 0.012, 'metal', seg=8, ink=False)
    else:
        barrel(0.18, 0.2, c='barrel2')
        k.cyl(-0.45, -0.2, 0.3, 0.3, 0.3, 0.9, 'barrel', seg=10, rot=(0, 90, 18))
        k.cyl(0.18, 0.2, 0.9, 0.22, 0.22, 0.012, 'metal', seg=8, ink=False)
    return k


def boulder(k, seed, s=1.0):
    rnd = random.Random(seed)
    k.begin()
    rock(k, rnd, 0, 0, 0.46 * s, 0.44 * s, rnd.uniform(0.9, 1.25) * s, lim=0.5)
    if rnd.random() < 0.6:
        fern(k, rnd, rnd.uniform(-0.2, 0.2), -0.42, 0.3, col='moss')
    return k


def outcrop(k, seed):
    rnd = random.Random(seed)
    k.begin()
    rock(k, rnd, -0.2, 0.1, 0.8, 0.75, rnd.uniform(1.7, 2.1), lim=0.98)
    rock(k, rnd, 0.45, -0.35, 0.5, 0.5, rnd.uniform(1.0, 1.3), lim=0.98)
    rock(k, rnd, 0.3, 0.55, 0.42, 0.38, 2.5, z0=0.6, lim=0.98)
    fern(k, rnd, -0.5, -0.7, 0.35, col='moss')
    tuft(k, rnd, 0.6, 0.5, 0.16, z0=1.8)
    k.col(-0.95, 0.95, -0.95, 0.95, 0, 2.0)
    return k


def palm_piece(k, seed):
    rnd = random.Random(seed)
    k.begin()
    rock(k, rnd, 0.08, 0.1, 0.35, 0.3, 0.32, n=6, lim=0.48) if rnd.random() < 0.5 else fern(k, rnd, 0.1, 0.1, 0.42)
    palm(k, rnd, 0, 0, rnd.uniform(6.8, 8.6), lean=rnd.uniform(0.14, 0.26), r=rnd.uniform(1.7, 2.1))
    k.col(-0.25, 0.25, -0.25, 0.25, 0, 3.0)
    return k


def palm_clump(k, seed):
    rnd = random.Random(seed)
    k.begin()
    blob(k, rnd, 0, 0, 0, 0.9, 0.85, 1.25, leafcol('leaf3', 'leaf', 'leaf2'))
    fern(k, rnd, -0.6, -0.6, 0.45)
    fern(k, rnd, 0.65, 0.5, 0.4)
    for i in range(3):
        a = i / 3 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        palm(k, rnd, math.cos(a) * 0.4, math.sin(a) * 0.4, rnd.uniform(6.0, 8.8), lean=0.2, ang=a, r=rnd.uniform(1.6, 2.0), z0=0.0, nuts=i == 0)
    k.col(-0.8, 0.8, -0.8, 0.8, 0, 1.3)
    return k


def driftwood(k, seed):
    """Bleached log along X with branch stubs and a root knot."""
    rnd = random.Random(seed)
    k.begin(rnd.uniform(-10, 10))
    k.cyl(-0.5, 0, 0.24, 0.24, 0.2, 1.06, 'drift', seg=7, rot=(0, 90, 0))
    k.cyl(-0.52, 0, 0.24, 0.22, 0.22, 0.03, 'drift2', seg=7, rot=(0, -90, 0))
    k.cyl(0.1, 0.05, 0.3, 0.06, 0.03, 0.55, 'drift', seg=5, rot=(-50, 0, 20))
    k.cyl(-0.25, -0.05, 0.36, 0.05, 0.03, 0.4, 'drift2', seg=5, rot=(40, 20, 0))
    k.col(-0.5, 0.5, -0.28, 0.28, 0, 0.55)
    return k


def fence(k, seed):
    rnd = random.Random(seed)
    k.begin()
    for x in (-0.35, 0.35):
        k.cyl(x, 0, 0, 0.07, 0.06, 1.2 + rnd.uniform(-0.08, 0.08), 'drift', seg=5, rot=(rnd.uniform(-5, 5), rnd.uniform(-5, 5), 0))
    for z in (0.45, 0.88):
        k.bxr(0, -0.08, z + rnd.uniform(-0.04, 0.04), 0.96, 0.07, 0.09, 'drift2', rot=(0, rnd.uniform(-4, 4), 0))
    k.col(-0.5, 0.5, -0.15, 0.15, 0, 1.15)
    return k


def sandbags(k, seed):
    """Sandbag line (1 m run along X): three courses of pillow bags."""
    rnd = random.Random(seed)
    k.begin()
    for row, (z, n) in enumerate(((0.0, 3), (0.24, 3), (0.48, 2))):
        for i in range(n):
            x = -0.5 + (i + 0.5) / n + (0.0 if n == 3 else rnd.uniform(-0.03, 0.03))
            k.sph(x, -0.04 + row * 0.03, z + 0.14, 0.5, 'hutwall' if (i + row) % 2 else 'sand2', seg=(8, 4), scale=(1.04 / n, 0.52, 0.3))
    k.col(-0.5, 0.5, -0.32, 0.32, 0, 0.8)
    return k


def reeds(k, seed):
    rnd = random.Random(seed)
    k.begin()
    for i in range(7):
        x, y = rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35)
        h = rnd.uniform(0.8, 1.4)
        k.cyl(x, y, 0, 0.03, 0.015, h, 'reed', seg=4, rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), 0), ink=False)
        if i % 2 == 0:
            k.cyl(x, y, h * 0.7, 0.05, 0.05, 0.22, 'cattail', seg=5)
    tuft(k, rnd, 0, 0, 0.25)
    return k


def torch(k, seed):
    """Tiki torch: bamboo pole, thatch cup, flame."""
    k.begin()
    k.cyl(0, 0, 0, 0.06, 0.05, 1.9, 'wood', seg=6)
    for z in (0.5, 1.1, 1.6):
        k.cyl(0, 0, z, 0.066, 0.066, 0.04, 'wood2', seg=6, caps=False, ink=False)
    k.cyl(0, 0, 1.85, 0.08, 0.17, 0.28, 'thatch2', seg=6)
    k.cyl(0, 0, 2.13, 0.12, 0.02, 0.32, 'flame', seg=5)
    k.col(-0.12, 0.12, -0.12, 0.12, 0, 2.0)
    return k


def signpost(k, seed):
    k.begin()
    k.cyl(0, 0, 0, 0.07, 0.06, 1.9, 'drift2', seg=6)
    k.bxr(0.28, 0, 1.55, 0.7, 0.05, 0.22, 'plank', rot=(0, 4, 0))
    k.bxr(-0.24, 0, 1.18, 0.6, 0.05, 0.2, 'plank', rot=(0, -5, 0))
    for (x, z, w) in ((0.25, 1.55, 0.4), (-0.2, 1.18, 0.34)):
        k.qy(x - w / 2, x + w / 2, z - 0.025, z + 0.025, -0.03, -1, 'wood2')
    k.col(-0.12, 0.12, -0.12, 0.12, 0, 2.0)
    return k


def umbrella(k, seed):
    rnd = random.Random(seed)
    k.begin()
    k.cyl(0, 0, 0, 0.035, 0.035, 2.1, 'paper', seg=5, rot=(6, 0, 0))
    star(k, (0, -0.2, 2.05), 1.0, 0.32, 'boatred', pts=8, inner=0.92, droop=0.25, under=0.2, under_color='paper')
    k.bx(-0.32, 0.32, -0.95, -0.35, 0.28, 0.33, 'barrel2')
    k.bx(-0.3, 0.3, -0.36, -0.3, 0.33, 0.75, 'barrel2')
    for x in (-0.28, 0.28):
        k.bx(x - 0.03, x + 0.03, -0.9, -0.84, 0, 0.28, 'paper')
        k.bx(x - 0.03, x + 0.03, -0.4, -0.34, 0, 0.28, 'paper')
    k.col(-0.1, 0.1, -0.1, 0.1, 0, 2.0)
    return k


def boat(k, seed, kind):
    """[4, 2] rowboat pulled up on the sand (A: upright with seats and oars; B: upturned on chocks)."""
    rnd = random.Random(seed)
    k.begin(rnd.uniform(-6, 6))
    L, W = 1.75, 0.68
    if kind == 'A':
        pts = []
        for i in range(9):
            t = i / 8
            x = -L + 2 * L * t
            w = W * math.sin(math.pi * (0.08 + 0.84 * t)) ** 0.7
            pts += [(x, -w, 0.68), (x, w, 0.68), (x, -w * 0.55, 0.12), (x, w * 0.55, 0.12)]
        pts += [(L + 0.12, 0, 0.78), (-L - 0.05, 0, 0.72)]
        k.hullp(pts, lambda f: 'wood2' if f.normal.z > 0.8 else ('boatred' if f.calc_center_median().z < 0.3 else 'boat'))
        for x in (-0.7, 0.0, 0.7):
            k.bx(x - 0.12, x + 0.12, -0.5, 0.5, 0.68, 0.73, 'plank')
        for s in (-1, 1):
            k.bxr(-0.1, s * 0.48, 0.79, 2.0, 0.07, 0.04, 'wood', rot=(0, 0, s * 8))
            k.bxr(0.85, s * 0.6, 0.8, 0.4, 0.14, 0.03, 'wood', rot=(0, 0, s * 8))
        k.col(-1.8, 1.8, -0.7, 0.7, 0, 0.8)
    else:
        pts = []
        for i in range(9):
            t = i / 8
            x = -L + 2 * L * t
            w = W * math.sin(math.pi * (0.08 + 0.84 * t)) ** 0.7
            pts += [(x, -w, 0.18), (x, w, 0.18), (x, -w * 0.5, 0.78), (x, w * 0.5, 0.78)]
        pts += [(L + 0.1, 0, 0.3), (-L - 0.05, 0, 0.3)]
        k.hullp(pts, lambda f: 'boatred' if f.normal.z > 0.6 else ('paper' if f.calc_center_median().z < 0.3 else 'boat2'))
        k.bx(-L + 0.2, L - 0.2, -0.03, 0.03, 0.8, 0.86, 'wood2')
        for x in (-1.0, 1.0):
            k.bx(x - 0.15, x + 0.15, -0.6, 0.6, 0.0, 0.18, 'drift2')
        k.col(-1.8, 1.8, -0.7, 0.7, 0, 0.85)
    # a tow rope trailing to a stake in the sand
    k.cyl(L + 0.15, 0.0, 0.0, 0.04, 0.03, 0.45, 'wood', seg=5)
    k.bxr(L + 0.05, 0.0, 0.35, 0.3, 0.03, 0.03, 'rope', rot=(0, 25, 0))
    return k


# ---------------------------------------------------------------- floor patches (no collision)
def blobring(rnd, n, rx, ry, jag=0.12, cx=0.0, cy=0.0):
    out = []
    for i in range(n):
        a = i / n * 2 * math.pi
        kk = 1.0 + rnd.uniform(-jag, jag)
        out.append((cx + math.cos(a) * rx * kk, cy + math.sin(a) * ry * kk))
    return out


def flat(k, ring, z, c, s=1.0):
    k.poly([(x * s, y * s, z) for x, y in ring], c, (0, 0, 1))


def grass_patch(k, seed):
    rnd = random.Random(seed)
    k.begin()
    ring = blobring(rnd, 14, 1.4, 1.3, 0.1)
    flat(k, ring, Z['grass'], 'grass')
    for i in range(3):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.2, 0.8)
        flat(k, blobring(rnd, 7, 0.3, 0.24, 0.2, math.cos(a) * r, math.sin(a) * r), Z['flower'] + 0.004 * i, 'grass3')
    for i in range(4):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.3, 1.0)
        tuft(k, rnd, math.cos(a) * r, math.sin(a) * r, rnd.uniform(0.12, 0.2), col='grass2' if i % 2 else 'grass3')
    for i in range(3):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.2, 0.9)
        k.cyl(math.cos(a) * r, math.sin(a) * r, 0.0, 0.06, 0.06, 0.12, 'flower' if i % 2 else 'amber', seg=5)
    return k


def dune(k, seed):
    """[3, 3] low grassy sand mound (walk over it: 0.3 m)."""
    rnd = random.Random(seed)
    k.begin()
    pts = [(x * 1.45, y * 1.35, 0.0) for x, y in blobring(rnd, 10, 1.0, 1.0, 0.06)]
    pts += [(x * 0.95, y * 0.85, 0.2) for x, y in blobring(rnd, 8, 1.0, 1.0, 0.1)]
    pts += [(x * 0.45, y * 0.4, 0.3) for x, y in blobring(rnd, 6, 1.0, 1.0, 0.15)]
    fs = k.hullp(pts, lambda f: 'grass' if f.normal.z > 0.97 else 'sand2')
    bmesh.ops.delete(k.m.bm, geom=[f for f in fs if f.normal.z < -0.9], context='FACES_ONLY')   # open bottom: no ink ring on the sand
    for i in range(5):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.2, 0.8)
        tuft(k, rnd, math.cos(a) * r, math.sin(a) * r, rnd.uniform(0.15, 0.24), z0=0.18)
    return k


def water_body(k, rnd, rx, ry, n=20, cx=0.0, cy=0.0, rim='grass', deep=True):
    """Shallow toon water: ground rim, foam line, water, deeper middle (all flat, each on its own height)."""
    ring = blobring(rnd, n, rx, ry, 0.07, cx, cy)
    flat(k, [(cx + (x - cx) * 1.12, cy + (y - cy) * 1.12) for x, y in ring], Z['rim'], rim)
    flat(k, [(cx + (x - cx) * 1.04, cy + (y - cy) * 1.04) for x, y in ring], Z['foam'], 'foam')
    flat(k, ring, Z['water'], 'water')
    if deep:
        flat(k, [(cx + (x - cx) * 0.62, cy + (y - cy) * 0.62) for x, y in ring], Z['water2'], 'water2')
    return ring


def spots(rnd, n, gen, rad, taken):
    """Up to n non-overlapping spots: gen() -> (x, y); rad = radius each one needs; taken = shared list."""
    out = []
    for _ in range(n * 12):
        if len(out) >= n:
            break
        x, y = gen()
        if all(math.hypot(x - a, y - b) > rad + r for a, b, r in taken):
            taken.append((x, y, rad))
            out.append((x, y))
    return out


def glints(k, rnd, n, rx, ry, cx=0.0, cy=0.0):
    def gen():
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.15, 0.75)
        return cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
    for x, y in spots(rnd, n, gen, 0.55, []):
        L = rnd.uniform(0.25, 0.45)
        wavy(k, x - L, x + L, y, Z['glint'], 0.05, 'foam', n=3, amp=0.03)


def lily(k, rnd, x, y, r):
    pts = []
    for i in range(9):
        a = 0.35 + i / 8 * (2 * math.pi - 0.7)
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r, Z['lily']))
    pts.append((x, y, Z['lily']))
    k.poly(pts, 'lily', (0, 0, 1))


def pond(k, seed):
    """[4, 4] freshwater pond: grassy bank, reeds, lily pads with a flower."""
    rnd = random.Random(seed)
    k.begin()
    water_body(k, rnd, 1.6, 1.45, n=18, rim='grass2')
    def gen():
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.3, 0.9)
        return math.cos(a) * r * 1.4, math.sin(a) * r * 1.2
    for x, y in spots(rnd, 4, gen, 0.25, []):
        lily(k, rnd, x, y, rnd.uniform(0.16, 0.24))
    k.cyl(0.4, 0.3, Z['lily'] - 0.01, 0.07, 0.1, 0.07, 'flower', seg=6)
    glints(k, rnd, 3, 1.4, 1.2)
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        x, y = math.cos(a) * 1.75, math.sin(a) * 1.6
        for j in range(3):
            h = rnd.uniform(0.7, 1.2)
            xx, yy = x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15)
            k.cyl(xx, yy, 0, 0.03, 0.015, h, 'reed', seg=4, rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), 0), ink=False)
            if j == 0:
                k.cyl(xx, yy, h * 0.68, 0.045, 0.045, 0.2, 'cattail', seg=5)
    return k


def tidepool(k, seed):
    """[3, 3] rocky tide pool on wet sand: rim rocks, starfish, shells."""
    rnd = random.Random(seed)
    k.begin()
    ring = blobring(rnd, 16, 1.38, 1.3, 0.08)
    flat(k, ring, Z['wet'], 'wet')
    water_body(k, rnd, 1.0, 0.92, n=14, rim='rock2', deep=True)
    for i in range(5):
        a = i / 5 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        rock(k, rnd, math.cos(a) * 1.15, math.sin(a) * 1.05, 0.22, 0.2, rnd.uniform(0.2, 0.42), n=5, lim=1.45)
    for i, (x, y) in enumerate(spots(rnd, 2, lambda: (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.45, 0.45)), 0.17, [])):
        pts = []
        for j in range(10):
            aa = j / 10 * 2 * math.pi
            rr = 0.16 if j % 2 == 0 else 0.06
            pts.append((x + math.cos(aa) * rr, y + math.sin(aa) * rr, Z['lily'] + 0.004 * i))
        k.poly(pts, 'amber' if i else 'coral', (0, 0, 1))
    glints(k, rnd, 2, 0.8, 0.7)
    return k


def lagoon(k, seed):
    """[14, 10] the big lagoon lake: sandy shore, foam line, shallows, deep blue middle, a palm islet with rocks
    (the only part with collision), lily pads and reeds at one end."""
    rnd = random.Random(seed)
    k.begin()
    ring = blobring(rnd, 32, 6.6, 4.5, 0.04)
    flat(k, [(x * 1.03, y * 1.06) for x, y in ring], Z['wet'], 'wet')
    flat(k, [(x * 0.98, y * 0.97) for x, y in ring], Z['foam'], 'foam')
    flat(k, [(x * 0.94, y * 0.92) for x, y in ring], Z['water'], 'water')
    flat(k, [(x * 0.7, y * 0.66) for x, y in ring], Z['water2'], 'water2')
    flat(k, [(x * 0.42 + 0.6, y * 0.38) for x, y in ring], Z['waterd'], 'waterd')
    # islet (west part): sand, rocks, a palm
    ix, iy = -3.4, 0.4
    isl = blobring(rnd, 12, 1.25, 1.0, 0.1, ix, iy)
    flat(k, isl, Z['lily'], 'sand')
    rock(k, rnd, ix + 0.3, iy - 0.2, 0.55, 0.45, 0.9, n=6)
    rock(k, rnd, ix - 0.45, iy + 0.35, 0.35, 0.3, 0.55, n=5)
    palm(k, rnd, ix - 0.1, iy + 0.1, 7.4, lean=0.24, ang=math.radians(20), r=1.9)
    k.col(ix - 0.95, ix + 0.95, iy - 0.75, iy + 0.75, 0, 1.0)
    # lily pads and reeds at the east end
    for x, y in spots(rnd, 6, lambda: (4.0 + rnd.uniform(-0.9, 0.9), rnd.uniform(-2.0, 2.0)), 0.29, [(4.2, 0.6, 0.12)]):
        lily(k, rnd, x, y, rnd.uniform(0.18, 0.28))
    k.cyl(4.2, 0.6, Z['lily'] - 0.01, 0.07, 0.1, 0.07, 'flower', seg=6)
    for i in range(7):
        a = rnd.uniform(-0.9, 0.9)
        x, y = math.cos(a) * 6.3, math.sin(a) * 4.1
        for j in range(3):
            h = rnd.uniform(0.8, 1.4)
            xx, yy = x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2)
            k.cyl(xx, yy, 0, 0.03, 0.015, h, 'reed', seg=4, rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), 0), ink=False)
            if j == 0:
                k.cyl(xx, yy, h * 0.68, 0.05, 0.05, 0.22, 'cattail', seg=5)
    glints(k, rnd, 8, 5.0, 3.4, cx=0.8)
    return k


def jetty(k, seed):
    """[3, 8] plank jetty on posts running north into the lagoon (walk on it: 0.16 m deck)."""
    rnd = random.Random(seed)
    k.begin()
    k.bx(-1.0, 1.0, -3.9, 3.9, 0.1, 0.16, 'plank')
    plank_lines(k, -1.0, 1.0, -3.9, 3.9, 0.16, 16, along='x')
    for y in (-3.6, -1.2, 1.2, 3.6):
        for x in (-1.08, 1.08):
            k.cyl(x, y, 0, 0.09, 0.09, 0.95 if y > 0 else 0.3, 'wood2', seg=6)
    k.bx(-1.12, -1.04, 0.0, 3.6, 0.82, 0.88, 'rope')
    k.bx(1.04, 1.12, 0.0, 3.6, 0.82, 0.88, 'rope')
    k.cyl(0.6, 3.4, 0.16, 0.18, 0.18, 0.22, 'barrel2', seg=8)
    return k


# ================================================================ landmarks
def hut(k, seed):
    """[5, 5] beach hut on stilts: bamboo walls, a thatched hip roof, a ladder, a porch with a hammock rail."""
    rnd = random.Random(seed)
    k.begin()
    for x in (-1.9, 1.9):
        for y in (-1.6, 1.9):
            k.cyl(x, y, 0, 0.12, 0.11, 1.0, 'wood2', seg=6)
    k.bx(-2.15, 2.15, -2.3, 2.2, 0.85, 1.05, 'wood', bevel=True)
    plank_lines(k, -2.15, 2.15, -2.3, -1.25, 1.05, 8, along='y')
    k.bx(-1.8, 1.8, -1.2, 1.9, 1.05, 3.0, 'hutwall', bevel=True)
    for x in (-1.2, -0.6, 0.0, 0.6, 1.2):
        k.qy(x - 0.03, x + 0.03, 1.1, 2.95, -1.203, -1, 'thatch2')
    k.qy(-0.42, 0.42, 1.05, 2.4, -1.206, -1, 'wood2')          # door
    for sx in (-1, 1):
        k.qy(sx * 1.25 - 0.3, sx * 1.25 + 0.3, 1.8, 2.4, -1.206, -1, 'ink')   # windows
        k.qx(-0.3, 0.6, 1.8, 2.4, sx * 1.803, sx, 'ink')
    k.cyl(0, 0.35, 3.0, 3.25, 0.15, 1.9, 'thatch', seg=4, rot=(0, 0, 45))
    k.cyl(0, 0.35, 2.92, 3.32, 3.32, 0.1, 'thatch2', seg=4, rot=(0, 0, 45), caps=False, ink=False)
    for x in (-2.0, 2.0):
        k.cyl(x, -2.15, 1.05, 0.06, 0.06, 1.0, 'wood2', seg=5)
    k.bx(-2.05, 2.05, -2.25, -2.215, 1.9, 1.98, 'rope')
    for i in range(4):                                         # ladder
        k.bx(-0.45, 0.45, -2.62 - i * 0.0, -2.5, 0.2 + i * 0.22, 0.25 + i * 0.22, 'wood2')
    for x in (-0.48, 0.48):
        k.bxr(x, -2.55, 0.5, 0.06, 0.06, 1.15, 'wood', rot=(-12, 0, 0))
    k.col(-2.2, 2.2, -2.35, 2.25, 0, 3.4)
    return k


def lighthouse(k, seed):
    """[6, 6] red-and-white lighthouse on a rock base: banded tapered tower, door, windows, gallery with rail,
    glowing lantern room, red cap and a vane."""
    rnd = random.Random(seed)
    k.begin()
    for i in range(6):
        a = i / 6 * 2 * math.pi + 0.3
        rock(k, rnd, math.cos(a) * 2.1, math.sin(a) * 2.0, 0.9, 0.8, rnd.uniform(0.9, 1.6), n=6, lim=2.95)
    k.cyl(0, 0, 0, 2.2, 2.1, 1.1, 'rock3', seg=12)
    H, z, r0, r1 = 13.5, 1.1, 1.65, 1.1
    nb = 6
    for i in range(nb):
        za, zb = z + (H - z) * i / nb, z + (H - z) * (i + 1) / nb
        ra, rb = r0 + (r1 - r0) * i / nb, r0 + (r1 - r0) * (i + 1) / nb
        k.cyl(0, 0, za, ra, rb, zb - za, 'red' if i % 2 else 'paper', seg=12, caps=False)
    k.cyl(0, 0, H, 1.75, 1.75, 0.22, 'gunmetal', seg=12)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        k.cyl(math.cos(a) * 1.62, math.sin(a) * 1.62, H + 0.22, 0.03, 0.03, 0.75, 'gunmetal', seg=4, ink=False)
    k.cyl(0, 0, H + 0.92, 1.66, 1.66, 0.07, 'gunmetal', seg=12, caps=False)
    k.cyl(0, 0, H + 0.22, 0.95, 0.95, 1.5, 'glow', seg=8)
    for i in range(8):
        a = (i + 0.5) / 8 * 2 * math.pi
        k.cyl(math.cos(a) * 0.95, math.sin(a) * 0.95, H + 0.22, 0.045, 0.045, 1.5, 'gunmetal', seg=4, ink=False)
    k.cyl(0, 0, H + 1.72, 1.15, 0.12, 1.0, 'red', seg=8)
    k.cyl(0, 0, H + 2.7, 0.03, 0.03, 0.7, 'gunmetal', seg=4)
    k.sph(0, 0, H + 2.72, 0.13, 'red', seg=(6, 4))
    k.bxr(0, 0, H + 3.25, 0.6, 0.04, 0.12, 'gunmetal', rot=(0, 0, 30))
    # door + windows on the south face (-Y)
    k.bx(-0.45, 0.45, -1.72, -1.55, 1.1, 2.9, 'wood2')
    k.bx(-0.6, 0.6, -1.85, -1.5, 2.9, 3.1, 'paper')
    for zz, rr in ((5.6, 1.47), (9.2, 1.3)):
        k.bx(-0.25, 0.25, -rr - 0.03, -rr + 0.2, zz, zz + 0.7, 'ink')
    k.bx(-0.7, 0.7, -2.6, -1.8, 0, 0.45, 'rock2')
    k.bx(-0.6, 0.6, -2.2, -1.75, 0.45, 0.9, 'rock2')
    k.col(-2.25, 2.25, -2.25, 2.25, 0, 3.0)
    k.col(-1.5, 1.5, -1.5, 1.5, 3.0, 14.0)
    return k


def lookout(k, seed):
    """[4, 4] ruined stone lookout: a square tower of offset stone courses, broken top, window holes, vines and a
    collapsed corner with rubble."""
    rnd = random.Random(seed)
    k.begin()
    z = 0.0
    for i in range(7):
        h = 0.9
        s = 1.55 - i * 0.03
        cut = i >= 4
        x1 = s if not cut else s - (i - 3) * 0.5
        k.bx(-s, x1, -s, s - (0.4 * (i - 4) if i > 4 else 0), z, z + h, 'rock3' if i % 2 else 'rock', bevel=True)
        z += h
    for zz in (2.2, 4.0):
        k.bx(-0.3, 0.3, -1.6, -1.2, zz, zz + 0.8, 'ink')
        k.bx(-1.6, -1.2, -0.3, 0.3, zz, zz + 0.8, 'ink')
    k.bx(-0.5, 0.5, -1.62, -1.2, 0.0, 1.9, 'rockd')
    for i in range(5):
        rock(k, rnd, 1.3 + rnd.uniform(-0.4, 0.5), -1.2 + i * 0.55, 0.38, 0.32, rnd.uniform(0.35, 0.7), n=5, lim=1.95)
    blob(k, rnd, -1.0, 1.3, 2.0, 0.6, 0.5, 3.4, leafcol('leaf3', 'leaf', 'leaf2'))
    blob(k, rnd, 1.2, 1.2, 0.0, 0.7, 0.6, 1.6)
    fern(k, rnd, -1.5, -1.6, 0.5)
    palm(k, rnd, 1.45, 1.45, 8.2, lean=0.16, ang=math.radians(40), r=2.0)
    k.col(-1.6, 1.6, -1.6, 1.6, 0, 4.0)
    return k


def outpost(k, seed):
    """[7, 5] research outpost container lab the robots took over: steel box on skids, ribbed sides, a door with
    steps, windows, an AC unit, cable spools, a roof antenna and a small dish, a teal status light bar."""
    rnd = random.Random(seed)
    k.begin()
    for y in (-1.6, 1.6):
        k.bx(-3.3, 3.3, y - 0.15, y + 0.15, 0, 0.25, 'metal2')
    k.bx(-3.2, 3.2, -1.9, 1.9, 0.25, 2.95, 'metal', bevel=True)
    k.bx(-3.3, 3.3, -2.0, 2.0, 2.95, 3.15, 'metal2', bevel=True)
    for i in range(11):
        x = -3.0 + i * 0.6
        if abs(x - 0.0) < 0.7:
            continue
        k.qy(x - 0.06, x + 0.06, 0.4, 2.8, -1.903, -1, 'metal2')
        k.qy(x - 0.06, x + 0.06, 0.4, 2.8, 1.903, 1, 'metal2')
    k.bx(-0.55, 0.55, -1.95, -1.9, 0.3, 2.4, 'panel')
    k.bx(0.3, 0.4, -2.0, -1.95, 1.2, 1.4, 'amber')
    for x in (-2.1, 2.1):
        k.bx(x - 0.55, x + 0.55, -1.96, -1.9, 1.5, 2.3, 'panel2')
        k.bx(x - 0.04, x + 0.04, -1.99, -1.95, 1.53, 2.27, 'metal2')
    k.qy(-3.0, -1.4, 2.55, 2.75, -1.906, -1, 'teal')
    for i in range(3):
        k.bx(-0.65 - 0.01 * i, 0.65 + 0.01 * i, -2.6 + i * 0.2, -2.4 + i * 0.2 - 0.003 * (i == 2), 0.0, 0.1 + i * 0.1, 'metal2' if i % 2 else 'metal')
    k.bx(2.6, 3.4, -0.6, 0.6, 0.4, 1.4, 'metal2')
    k.cyl(3.4, 0, 0.9, 0.35, 0.35, 0.05, 'gunmetal', seg=10, rot=(0, 90, 0), ink=False)
    k.cyl(0, 0, 3.15, 0.06, 0.04, 2.6, 'gunmetal', seg=5)
    k.sph(0, 0, 5.75, 0.09, 'red', seg=(6, 4))
    k.cyl(-2.2, 0.8, 3.15, 0.08, 0.08, 0.5, 'gunmetal', seg=5)
    k.cyl(-2.2, 0.8, 3.65, 0.65, 0.12, 0.35, 'paper', seg=10, rot=(35, 0, 30))
    for i, (x, y) in enumerate(((-3.0, -2.35), (3.0, 2.3))):
        k.cyl(x, y, 0.35, 0.35, 0.35, 0.36, 'wood' if i else 'wood2', seg=10, rot=(90, 0, 0))
        k.cyl(x, y + 0.03, 0.35, 0.22, 0.22, 0.42, 'gunmetal', seg=8, rot=(90, 0, 0))
    k.col(-3.3, 3.3, -2.0, 2.0, 0, 3.2)
    return k


def mast(k, seed):
    """[2, 2] radio mast: lattice tower on a concrete pad, dish, red beacon, guy wires, a generator box."""
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.2, 'rock3')
    H = 7.5
    for (x, y) in ((-0.4, -0.4), (0.4, -0.4), (0.4, 0.4), (-0.4, 0.4)):
        k.beam((x, y, 0.2), (x * 0.25, y * 0.25, H), 0.07, 'metal2')
    for i in range(1, 6):
        z = 0.2 + (H - 0.2) * i / 6
        s = 0.4 - 0.3 * (z - 0.2) / (H - 0.2)
        k.bx(-s, s, -s - 0.02, -s + 0.02, z, z + 0.05, 'metal2', ink=False)
        k.bx(-s, s, s - 0.02, s + 0.02, z, z + 0.05, 'metal2', ink=False)
    k.cyl(0, 0, H, 0.05, 0.05, 0.6, 'metal2', seg=5)
    k.sph(0, 0, H + 0.62, 0.12, 'red', seg=(6, 4))
    k.cyl(0.0, -0.25, 5.4, 0.7, 0.1, 0.3, 'paper', seg=10, rot=(70, 0, 0))
    k.bx(0.25, 0.85, 0.2, 0.8, 0.2, 0.8, 'boat2')
    k.bx(0.3, 0.8, 0.17, 0.2, 0.55, 0.7, 'teal')
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 2.5)
    return k


def solar(k, seed):
    """[3, 2] solar array: two tilted panel rows on a steel frame (cover: 1.2 m)."""
    k.begin()
    for x in (-1.3, 0.0, 1.3):
        k.bx(x - 0.05, x + 0.05, -0.6, -0.5, 0, 0.55, 'metal2')
        k.bx(x - 0.05, x + 0.05, 0.5, 0.6, 0, 1.15, 'metal2')
    k.bxr(0, 0.0, 0.9, 2.9, 1.35, 0.06, 'panel', rot=(-24, 0, 0))
    for i in range(1, 6):
        x = -1.45 + 2.9 * i / 6
        k.bxr(x, 0.0164, 0.9 + 0.0364, 0.025, 1.3, 0.012, 'panel2', rot=(-24, 0, 0))
    k.col(-1.45, 1.45, -0.8, 0.8, 0, 1.2)
    return k


def charger(k, seed):
    """[2, 2] robot charging pod: a hooped steel cradle with a teal glow ring around a half-charged Crawler can
    (no face: robots never have one), cable to a battery box."""
    k.begin()
    k.cyl(0, 0, 0, 0.85, 0.85, 0.15, 'metal2', seg=10)
    k.cyl(0, 0, 0.15, 0.7, 0.7, 0.03, 'teal', seg=10, ink=False)
    k.bx(-0.86, 0.86, -0.06, 0.06, 1.12, 1.24, 'metal')
    k.bx(-0.04, 0.04, -0.86, 0.86, 1.13, 1.23, 'metal')
    for (x, y) in ((-0.75, 0), (0.75, 0), (0, -0.75), (0, 0.75)):
        k.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.15, 1.15, 'metal')
    k.cyl(0, 0, 0.18, 0.32, 0.31, 0.45, 'metal', seg=8)
    k.cyl(0, 0, 0.63, 0.34, 0.34, 0.05, 'metal2', seg=8)
    k.cyl(0, 0, 0.68, 0.14, 0.14, 0.03, 'amber', seg=8, ink=False)
    k.bx(0.55, 0.95, 0.55, 0.95, 0, 0.5, 'boat2')
    k.bx(0.6, 0.9, 0.52, 0.55, 0.3, 0.42, 'teal')
    k.col(-0.85, 0.85, -0.85, 0.85, 0, 1.25)
    return k


# ================================================================ gate, trail, hatch, stand
def gate_frame(k):
    """Bamboo-and-log gate: two lashed log posts with tiki torches, a thatched header with a teal zone board, rock
    jambs filling out to the trail walls (|x| <= 2.5, above the 2.6 m trail walls)."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.52, s * 2.0)
        k.bx(x0, x1, -0.5, 0.5, 0, 3.4, 'wood', bevel=True)
        for z in (0.6, 1.5, 2.4):
            k.bx(x0 - 0.02, x1 + 0.02, -0.52, 0.52, z, z + 0.12, 'rope')
        xa, xb = srt(s * 2.0, s * 2.5)
        k.bx(xa, xb, -0.45, 0.45, 0, 2.95, 'rock')
        k.bx(xa - (0.03 if s < 0 else 0), xb + (0.03 if s > 0 else 0), -0.5, 0.5, 2.95, 3.1, 'rock3')
        for f in (-1, 1):
            k.cyl(s * 1.76, f * 0.66, 2.5, 0.05, 0.05, 1.1, 'wood2', seg=5)
            k.cyl(s * 1.76, f * 0.66, 3.55, 0.08, 0.15, 0.22, 'thatch2', seg=6)
            k.cyl(s * 1.76, f * 0.66, 3.77, 0.1, 0.02, 0.3, 'flame', seg=5)
    k.bx(-2.3, 2.3, -0.62, 0.62, 3.4, 3.75, 'wood2', bevel=True)
    for f in (-1, 1):
        k.qy(-1.6, 1.6, 3.47, 3.68, f * 0.623, f, 'teal')
    for sgn in (-1, 1):
        k.hullp([(-2.6, sgn * 0.95, 3.7), (2.6, sgn * 0.95, 3.7), (-2.6, sgn * 0.95, 3.85), (2.6, sgn * 0.95, 3.85),
                 (-2.4, 0, 4.55), (2.4, 0, 4.55)], lambda f: 'thatch' if f.normal.z > 0.2 else 'thatch2')
    return k


def gate_shutter(k):
    """Roll-up bamboo blind: vertical canes, lashing bands, an amber / ink hazard rail at the foot."""
    k.begin()
    Hs, n = 3.05, 12
    for i in range(n):
        x = -1.5 + (i + 0.5) * 3.0 / n
        k.bx(x - 0.12, x + 0.12, -0.06 + 0.004 * (i % 2), 0.06 - 0.004 * (i % 2), 0.35, Hs, 'wood' if i % 2 else 'thatch', ink=False)
    for z in (1.1, 2.2):
        k.bx(-1.5, 1.5, -0.075, 0.075, z, z + 0.1, 'rope', ink=False)
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.35, 'ink' if j % 2 else 'amber', ink=False)
    return k


def trail_wall(k, seed, kind):
    """Jungle path wall (1 m along Blender Y, path to +X after the 90 degree turn; authored with the path at -Y):
    a rope railing on posts in front of a dense hedge. Variants: Fern (big ferns), Torch (tiki torch), Palm."""
    rnd = random.Random(seed)
    k.begin(90)
    for i in range(2):
        blob(k, rnd, -0.25 + i * 0.5, 0.05, 0, 0.42, 0.32, rnd.uniform(1.7, 2.1), leafcol('leaf3', 'leaf', 'leaf2'))
    blob(k, rnd, rnd.uniform(-0.1, 0.1), 0.15, 1.3, 0.55, 0.3, rnd.uniform(1.4, 1.9), leafcol('leaf', 'leaf2', 'leafd'))
    k.cyl(0.0, -0.3, 0, 0.05, 0.05, 1.0, 'wood2', seg=5)
    k.bx(-0.5, 0.5, -0.33, -0.29, 0.88, 0.92, 'rope')
    k.bx(-0.5, 0.5, -0.33, -0.29, 0.5, 0.54, 'rope')
    if kind == 'Fern':
        fern(k, rnd, 0.0, -0.15, 0.55, z0=0.0)
    elif kind == 'Torch':
        k.cyl(0.3, -0.12, 0, 0.05, 0.04, 2.2, 'wood', seg=6)
        k.cyl(0.3, -0.12, 2.15, 0.07, 0.14, 0.24, 'thatch2', seg=6)
        k.cyl(0.3, -0.12, 2.39, 0.1, 0.02, 0.3, 'flame', seg=5)
    elif kind == 'Palm':
        palm(k, rnd, 0.0, 0.2, rnd.uniform(5.5, 7.0), lean=0.12, ang=math.radians(rnd.uniform(-60, 60)), r=1.6, nuts=False)
    return k


def hatch(k):
    """Exit pad: a round boardwalk platform with a teal centre and amber lamps."""
    k.begin()
    k.cyl(0, 0, 0, 1.3, 1.25, 0.12, 'wood2', seg=16)
    k.cyl(0, 0, 0.12, 1.12, 1.12, 0.02, 'plank', seg=16, ink=False)
    for i in range(-3, 4):
        k.bx(i * 0.3 - 0.012, i * 0.3 + 0.012, -0.9 * math.sqrt(1.0 - (i * 0.3) ** 2), 0.9 * math.sqrt(1.0 - (i * 0.3) ** 2), 0.14, 0.149, 'wood2', ink=False)
    k.cyl(0, 0, 0.143, 0.6, 0.6, 0.03, 'teal', seg=14, ink=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        k.cyl(math.cos(a) * 1.18, math.sin(a) * 1.18, 0.12, 0.07, 0.07, 0.06, 'amber', seg=6, ink=False)
    return k


# ================================================================ backdrop (on the island outside the zones, at sea)
def bd_jungle(k, seed):
    """~10 x 6 m jungle canopy mass with palm crowns poking out (seen over the zone walls)."""
    rnd = random.Random(seed)
    k.begin()
    for i in range(4):
        x = -3.8 + i * 2.55 + rnd.uniform(-0.4, 0.4)
        blob(k, rnd, x, rnd.uniform(-0.8, 0.8), 0, 1.9, 1.9, rnd.uniform(4.5, 6.5), leafcol('leaf', 'leaf2', 'leafd'), n=5)
    for i in range(3):
        x = -2.6 + i * 2.6 + rnd.uniform(-0.4, 0.4)
        blob(k, rnd, x, rnd.uniform(-0.6, 0.6), 4.0, 1.7, 1.6, rnd.uniform(2.4, 3.6), leafcol('leaf3', 'leaf', 'leafd'), n=5)
    for i in range(3):
        palm(k, rnd, -3.5 + i * 3.4 + rnd.uniform(-0.5, 0.5), rnd.uniform(-1.0, 1.0), rnd.uniform(9.0, 11.5), lean=0.1, r=2.4, nuts=False, n=5)
    return k


def bd_palms(k, seed):
    """Palm grove: four tall palms over bushes on a sandy-green knoll."""
    rnd = random.Random(seed)
    k.begin()
    for i in range(3):
        blob(k, rnd, -2.5 + i * 2.5, rnd.uniform(-0.7, 0.7), 0, 1.4, 1.2, rnd.uniform(1.6, 2.4), leafcol('leaf3', 'leaf', 'leaf2'), n=5)
    for i in range(4):
        a = i / 4 * 2 * math.pi + rnd.uniform(-0.4, 0.4)
        palm(k, rnd, math.cos(a) * 2.6, math.sin(a) * 1.6, rnd.uniform(8.0, 11.0), lean=0.18, ang=a, r=2.3, nuts=False, n=5)
    return k


def bd_rocks(k, seed):
    rnd = random.Random(seed)
    k.begin()
    for i in range(4):
        rock(k, rnd, -2.4 + i * 1.6 + rnd.uniform(-0.3, 0.3), rnd.uniform(-0.6, 0.6), rnd.uniform(0.8, 1.3), rnd.uniform(0.7, 1.1), rnd.uniform(0.9, 2.4), n=6)
    return k


def bd_islet(k, seed, big):
    """Distant islet out at sea: a sand ring, rocks, a jungle hump and palms (thick outline for the distance)."""
    rnd = random.Random(seed)
    k.begin()
    R = 14.0 if big else 8.0
    flat(k, blobring(rnd, 18, R, R * 0.7, 0.08), 0.03, 'sand')
    flat(k, blobring(rnd, 18, R * 1.12, R * 0.8, 0.06), 0.012, 'foam')
    pts = [(x, y, 0.0) for x, y in blobring(rnd, 10, R * 0.75, R * 0.5, 0.1)]
    pts += [(x, y, R * 0.35) for x, y in blobring(rnd, 8, R * 0.42, R * 0.28, 0.15)]
    pts += [(rnd.uniform(-1, 1), rnd.uniform(-1, 1), R * 0.5)]
    k.hullp(pts, lambda f: 'far' if f.normal.z > 0.35 else 'farrock')
    for i in range(4 if big else 2):
        a = i / (4 if big else 2) * 6.28 + rnd.uniform(-0.4, 0.4)
        palm(k, rnd, math.cos(a) * R * 0.3, math.sin(a) * R * 0.2, R * 0.5 + rnd.uniform(5, 8), lean=0.12, ang=a, r=2.8, z0=0.0, nuts=False, n=5)
    for i in range(3):
        a = rnd.uniform(0, 6.28)
        rock(k, rnd, math.cos(a) * R * 0.7, math.sin(a) * R * 0.5, 1.6, 1.2, rnd.uniform(1.5, 3.0), n=6)
    return k


def bd_buoy(k, seed):
    """Sailing buoy: red-and-white float, cage top with a light, a pole flag."""
    k.begin()
    k.cyl(0, 0, -0.3, 0.75, 0.9, 0.9, 'red', seg=10)
    k.cyl(0, 0, 0.6, 0.9, 0.6, 0.35, 'paper', seg=10)
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.4
        k.beam((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.9), (math.cos(a) * 0.12, math.sin(a) * 0.12, 2.6), 0.07, 'red')
    k.cyl(0, 0, 2.6, 0.22, 0.22, 0.3, 'glow', seg=8)
    k.cyl(0, 0, 2.9, 0.26, 0.05, 0.2, 'red', seg=8)
    return k


def bd_sailboat(k, seed):
    """Small sailboat on the horizon: hull, mast, two triangular sails."""
    k.begin()
    pts = []
    for i in range(7):
        t = i / 6
        x = -3.0 + 6.0 * t
        w = 1.0 * math.sin(math.pi * (0.1 + 0.8 * t)) ** 0.6
        pts += [(x, -w, 0.9), (x, w, 0.9), (x, -w * 0.4, -0.1), (x, w * 0.4, -0.1)]
    pts += [(3.4, 0, 1.0)]
    k.hullp(pts, lambda f: 'wood2' if f.normal.z > 0.8 else 'paper')
    k.cyl(0.0, 0, 0.9, 0.08, 0.06, 7.5, 'wood2', seg=5)
    k.hullp([(0.15, 0.0, 1.5), (0.15, 0.0, 8.0), (2.9, 0.0, 1.5), (0.15, 0.06, 1.5), (0.15, 0.06, 8.0), (2.9, 0.06, 1.5)], 'paper')
    k.hullp([(-0.15, 0.0, 1.5), (-0.15, 0.0, 6.5), (-2.4, 0.0, 1.5), (-0.15, 0.06, 1.5), (-0.15, 0.06, 6.5), (-2.4, 0.06, 1.5)], 'boatred')
    return k


def sea_glint(k):
    """Shimmer dashes for the ocean (one instanced mesh, scaled in and out over time by the theme)."""
    k.begin()
    rnd = random.Random(5)
    wavy(k, -1.4, 1.4, 0.0, 0.0, 0.16, 'foam', n=6, amp=0.1)
    wavy(k, -0.6, 0.9, 0.55, 0.0, 0.1, 'foam', n=4, amp=0.07)
    wavy(k, -1.0, 0.2, -0.5, 0.0, 0.08, 'foam', n=4, amp=0.06)
    return k


# ================================================================ build
def build_kit_island(ao):
    pal = Palette(FAM)
    k = Kit(pal, PFX, HULL_T)
    seed = 100
    for name, fn in (('Jungle', jungle), ('Rocks', rocks_mod), ('Dune', dune_mod)):
        for v in ('A', 'B'):
            seed += 7
            fn(k, seed, W=2).finish('%s_%s' % (name, v), ao=ao)
        seed += 7
        fn(k, seed, W=1).finish('%s_1' % name, ao=ao)
    corner(k, 31, 'A').finish('Corner_A', ao=ao)
    corner(k, 37, 'B').finish('Corner_B', ao=ao)
    for i, v in enumerate('ABC'):
        seawall(k, 41 + i * 3, v).finish('SeaWall_' + v, ao=ao)
    for i, v in enumerate(('A', 'B', 'Small')):
        crate(k, 51 + i, v).finish('Crate_' + v, bevel=0.015, ao=ao)
    barrels(k, 61, 'A').finish('Barrel_A', ao=ao)
    barrels(k, 62, 'B').finish('Barrel_B', ao=ao)
    for i, v in enumerate('ABC'):
        boulder(k, 71 + i * 5).finish('Rock_' + v, ao=ao)
    outcrop(k, 91).finish('Outcrop_A', ao=ao)
    outcrop(k, 97).finish('Outcrop_B', ao=ao)
    for i, v in enumerate('ABC'):
        palm_piece(k, 111 + i * 4).finish('Palm_' + v, ao=ao)
    palm_clump(k, 131).finish('PalmClump_A', ao=ao)
    palm_clump(k, 137).finish('PalmClump_B', ao=ao)
    driftwood(k, 141).finish('Driftwood', ao=ao)
    fence(k, 143).finish('Fence', ao=ao)
    sandbags(k, 145).finish('Sandbags', bevel=0.03, ao=ao)
    reeds(k, 147).finish('Reeds', ao=ao)
    torch(k, 149).finish('TikiTorch', ao=ao)
    signpost(k, 151).finish('Signpost', ao=ao)
    umbrella(k, 153).finish('Umbrella', ao=ao)
    boat(k, 161, 'A').finish('Boat_A', ao=ao)
    boat(k, 167, 'B').finish('Boat_B', ao=ao)
    grass_patch(k, 171).finish('Grass_A')
    grass_patch(k, 177).finish('Grass_B')
    dune(k, 181).finish('Dune_Patch_A', ao=ao)
    dune(k, 187).finish('Dune_Patch_B', ao=ao)
    pond(k, 191).finish('Pond_A')
    pond(k, 197).finish('Pond_B')
    tidepool(k, 201).finish('TidePool_A')
    tidepool(k, 207).finish('TidePool_B')
    lagoon(k, 211).finish('Lagoon')
    jetty(k, 215).finish('Jetty', ao=ao)
    hut(k, 221).finish('Landmark_Hut', bevel=0.02, ao=ao)
    lighthouse(k, 231).finish('Landmark_Lighthouse', bevel=0.02, ao=ao)
    lookout(k, 241).finish('Landmark_Lookout', bevel=0.03, ao=ao)
    outpost(k, 251).finish('Landmark_Outpost', bevel=0.02, ao=ao)
    mast(k, 261).finish('Mast', ao=ao)
    solar(k, 263).finish('Solar', ao=ao)
    charger(k, 265).finish('Charger', ao=ao)
    gate_frame(k).finish('GateFrame', bevel=0.02, ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    for i, v in enumerate(('', '_Fern', '_Torch', '_Palm')):
        trail_wall(k, 301 + i * 3, v.strip('_')).finish('TrailWall' + v, ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    bd_jungle(k, 401).finish('Backdrop_Jungle_A')
    bd_jungle(k, 409).finish('Backdrop_Jungle_B')
    bd_palms(k, 417).finish('Backdrop_Palms_A')
    bd_palms(k, 423).finish('Backdrop_Palms_B')
    bd_rocks(k, 431).finish('Backdrop_Rocks')
    k.hull_t = 0.12
    bd_islet(k, 441, True).finish('Backdrop_Islet_A')
    bd_islet(k, 447, False).finish('Backdrop_Islet_B')
    k.hull_t = 0.05
    bd_buoy(k, 451).finish('Backdrop_Buoy')
    bd_sailboat(k, 457).finish('Backdrop_Sailboat')
    k.hull_t = HULL_T
    sea_glint(k).finish('Sea_Glint')
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_island
