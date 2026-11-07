"""INKBOLT asset family: kit-grove ("Redwood Hollow", campaign level 16).

An old-growth redwood forest in the game's bold toon style: giant fluted red-brown trunks on buttress roots with
their crowns high overhead, sword ferns, salal and huckleberry, oxalis carpets, mushrooms and trilliums, mossy
boulders, fallen giants with shelf fungi, cut stumps and fire-hollowed snags, a creek and a fern-ringed pond, a log
ranger station with a camp (tent, campfire, woodpile, signposts, lanterns), and a walkway level 9 m up: the climbable
redwoods carry a plank platform reached by a railed staircase that wraps three sides of the trunk, and plank bridges
on trestle piers join the platforms. The zone edges are mossy cliffs and earthen banks; outside them the backdrop
builder (src/data/themes/grove.js) plants more giants.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = north.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (stair treads, platform, bridge planks).
  * Wall modules face -Y (the theme turns that face to the open side): Cliff_* / Bank_* are 2 m wide, centred on
    their (even) cell; *_1 fill run ends; Corner_* are round boulder piles.

Climbable redwood (Landmark_Redwood_*, footprint 8 x 8, origin = trunk centre, never rotated):
  trunk ~1.75 m radius at the stairs; the staircase wraps the trunk: SW corner tread (rise 1), south flight eastward
  (8 treads of 0.5 m), SE corner, east flight northward, NE corner, then 4 treads of the north flight westward to the
  platform at 9 m (24 rises of 0.375 m: robots step 0.4). Treads run from 1.4 m (set into the trunk) to 3.2 m from
  the axis; the outer edge carries a railing (collision per tread) except on the open SW start. The platform covers
  the whole footprint at 9 m except the stairwell over the north flight and the top of the east flight (x 0..4,
  y 2..4 and x 1.2..4, y 1.2..2, Blender: head room for the last treads); its outer rails are separate layer-9 pieces
  (Rail / Rail_Corner, placed by tools/grove_zones.py so bridges can join anywhere else).
"""
import math
import random

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, rock_pts

FAM = 'kit-grove'
PFX = 'KIT_GROVE_'
ib_lib.GLB[FAM] = 'fps-kit-grove.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    ('bark', '#9C4A2B'), ('bark2', '#6E2F1C'), ('bark3', '#BA6440'), ('heart', '#E09A5E'),
    ('wood', '#B97F4C'), ('wood2', '#8A5A34'), ('wood3', '#D6A26A'), ('woodd', '#5E3B22'), ('rope', '#DEC690'),
    ('leaf', '#2E7840'), ('leaf2', '#1F5A33'), ('leaf3', '#3F944C'), ('leaf4', '#5CAE55'),
    ('fern', '#4FA23C'), ('fern2', '#2E7A2C'), ('fern3', '#7CC74E'),
    ('moss', '#6CA83A'), ('moss2', '#93C84C'), ('mossd', '#4A8530'),
    ('clover', '#7ECB58'), ('clover2', '#58A845'),
    ('rock', '#86796A'), ('rock2', '#665C51'), ('rock3', '#A29480'), ('rockd', '#4A433C'),
    ('soil', '#6A4630'), ('duff', '#94643E'), ('mud', '#5C4532'),
    ('water', '#63BFCB'), ('water2', '#4AA6BE'), ('waterd', '#3A88A4'), ('foam', '#EAF7F3'),
    ('mush', '#DC4630'), ('mush2', '#F4E8CF'), ('mush3', '#C8945A'), ('shelf', '#E3A645'),
    ('flower', '#F7F3FF'), ('berry', '#D23A4A'),
    ('roof', '#3F6E4B'), ('roof2', '#2C523A'), ('cabin', '#A8693C'), ('cabin2', '#84502C'), ('window', '#FFE6A0'),
    ('sign', '#E9D3A0'), ('canvas', '#E0B95C'), ('canvas2', '#B98F3E'), ('flame', '#FF8A2A'), ('flame2', '#FFD95A'),
    ('far', '#557A5C'), ('far2', '#3F6449'), ('farbark', '#7A4A36'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# climbable redwood geometry (Blender coords, see the module docstring)
STEP, DECK = 0.375, 9.0
IN, A, OUT, TD = 1.4, 2.0, 3.2, 0.5          # tread inner edge, flight band / corner boundary, outer edge, tread depth
FOOT = 4.0                                   # half footprint
SOLID_RISE = 4                               # the first treads are solid down to the ground


class GKit(Kit):
    """Kit with walkable collision boxes (<Piece>_WCOL<n>)."""

    def begin(self, rot=0):
        super().begin(rot)
        self.walk = set()
        return self

    def wcol(self, x0, x1, y0, y1, z0, z1):
        self.walk.add(len(self.cols))
        self.cols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        obj = super().finish(name, bevel, ao)
        full = self.prefix + name
        for i in sorted(self.walk):
            bpy.data.objects['%s_COL%d' % (full, i)].name = '%s_WCOL%d' % (full, i)
        return obj


# ================================================================ helpers
def rockcol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.72:
        return 'moss'
    if n.z > 0.5:
        return 'moss2'
    if n.z < -0.3:
        return 'rockd'
    return 'rock3' if (math.sin(c.x * 2.7 + c.z * 1.9 + c.y * 1.3) > 0.35) else ('rock' if n.z > -0.05 else 'rock2')


def baldcol(f):
    """rock without moss"""
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.6:
        return 'rock3'
    if n.z < -0.3:
        return 'rockd'
    return 'rock' if math.sin(c.x * 3.1 + c.z * 2.3) > -0.2 else 'rock2'


def leafcol(top='leaf3', mid='leaf', low='leaf2'):
    def fn(f):
        n = f.normal
        return top if n.z > 0.45 else (low if n.z < -0.2 else mid)
    return fn


def barkcol(f):
    n = f.normal
    return 'moss' if n.z > 0.65 else ('bark2' if n.z < -0.2 else 'bark')


def blob(k, rnd, cx, cy, z0, rx, ry, h, col=None, n=6):
    """Foliage / bush mass: convex hull of a jittered squashed ellipsoid."""
    pts = []
    for ring, (zf, rf) in enumerate(((0.0, 0.6), (0.42, 1.0), (0.8, 0.62))):
        for i in range(n):
            a = (i + 0.5 * ring + rnd.uniform(-0.25, 0.25)) / n * 2 * math.pi
            kk = rnd.uniform(0.82, 1.08) * rf
            pts.append((cx + math.cos(a) * rx * kk, cy + math.sin(a) * ry * kk, z0 + h * (zf + rnd.uniform(-0.04, 0.04))))
    pts.append((cx + rnd.uniform(-0.1, 0.1) * rx, cy + rnd.uniform(-0.1, 0.1) * ry, z0 + h))
    return k.hullp(pts, col or leafcol())


_RK = [0]


def rock(k, rnd, cx, cy, rx, ry, h, z0=0.0, n=7, col=rockcol):
    _RK[0] = (_RK[0] + 1) % 7
    z0 -= 0.004 * _RK[0]   # distinct bottoms: rocks of one piece never share a coplanar base
    return k.hullp(rock_pts(rnd, (cx, cy), rx, ry, h, z0=z0, n=n, top=3), col)


def lathe(k, rings, n, colfn, x=0.0, y=0.0, flute=None, phase=0.0, twist=0.0, top=None, ink=True):
    """Closed-side surface of revolution about a vertical axis at (x, y): rings [(z, r)] bottom-up, n vertices per ring,
    flute(i) -> radius factor of vertex i, twist (rad per m) turns the rings, top: apex height (cone cap) or None;
    colfn(i, j) -> palette name of the face between vertices i, i+1 and rings j, j+1 (or (i, -1) for the cap)."""
    m = k.m
    P = m.parent
    rows = []
    for (z, r) in rings:
        row = []
        for i in range(n):
            a = phase + twist * z + i * 2 * math.pi / n
            rr = r * (flute(i) if flute else 1.0)
            row.append(m.bm.verts.new(P @ Vector((x + math.cos(a) * rr, y + math.sin(a) * rr, z))))
        rows.append(row)
    m.nshape += 1
    for j in range(len(rows) - 1):
        Ar, Br = rows[j], rows[j + 1]
        for i in range(n):
            i2 = (i + 1) % n
            f = m.bm.faces.new((Ar[i], Ar[i2], Br[i2], Br[i]))
            f.material_index = k.pal.index(colfn(i, j))
            f[m.shape] = m.nshape
    if top is not None:
        c = m.bm.verts.new(P @ Vector((x, y, top)))
        T = rows[-1]
        for i in range(n):
            f = m.bm.faces.new((T[i], T[(i + 1) % n], c))
            f.material_index = k.pal.index(colfn(i, -1))
            f[m.shape] = m.nshape
    k._mark(ink)


def flute3(i):
    return 0.93 if i % 3 == 0 else 1.0


def bark_faces(seed):
    rnd = random.Random(seed)
    light = [rnd.random() < 0.3 for _ in range(64)]

    def fn(i, j):
        if j < 0:
            return 'bark2'
        if i % 3 == 1:
            return 'bark3' if light[(i // 3 + j * 5) % 64] else 'bark'
        return 'bark2'
    return fn


def star(k, c, r, h, color, pts=7, inner=0.4, droop=0.5, phase=0.0, under=0.12, under_color=None, ink=True):
    """Star-section umbrella (fern / tuft): pts tips at radius r drooping, apex h above c."""
    cx, cy, cz = c
    ring = []
    for i in range(pts * 2):
        a = math.radians(phase) + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        ring.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz - (droop if i % 2 == 0 else droop * 0.25)))
    m = k.m
    P = m.parent
    vs = [m.bm.verts.new(P @ Vector(p)) for p in ring + [(cx, cy, cz + h), (cx, cy, cz + h * under)]]
    N = len(ring)
    A_, B_ = vs[N], vs[N + 1]
    side, bot = [], []
    for i in range(N):
        j = (i + 1) % N
        side.append(m.bm.faces.new((vs[i], vs[j], A_)))
        bot.append(m.bm.faces.new((vs[j], vs[i], B_)))
    k._tag(side + bot, color)
    if under_color:
        ui = k.pal.index(under_color)
        for f in bot:
            f.material_index = ui
    k._mark(ink)


def frond(k, rnd, x, y, z, a, L, w, lift, droop, col=('fern3', 'fern')):
    """One arching sword-fern frond: a thin tapered hull in two sections (rising, then drooping to a point)."""
    dx, dy = math.cos(a), math.sin(a)
    sx, sy = -dy, dx
    p0 = (x + dx * 0.05, y + dy * 0.05, z)
    p1 = (x + dx * L * 0.48, y + dy * L * 0.48, z + lift)
    p2 = (x + dx * L, y + dy * L, z + lift - droop)
    t = 0.025

    def sec(p, hw):
        return [(p[0] + sx * hw, p[1] + sy * hw, p[2] - t), (p[0] - sx * hw, p[1] - sy * hw, p[2] - t), (p[0], p[1], p[2] + t)]
    fn = lambda f: col[0] if f.normal.z > 0 else col[1]
    k.hullp(sec(p0, w * 0.3) + sec(p1, w * 0.5), fn)
    q1 = (p1[0] - dx * 0.03, p1[1] - dy * 0.03, p1[2] - 0.01)
    k.hullp(sec(q1, w * 0.46) + [(p2[0], p2[1], p2[2])], fn)


def fern(k, rnd, x, y, s=1.0, z0=0.0, n=5):
    """Sword fern clump: a low star rosette plus arching fronds."""
    star(k, (x, y, z0 + 0.32 * s), 0.55 * s, 0.22 * s, 'fern', pts=7, inner=0.35, droop=0.26 * s, phase=rnd.uniform(0, 50), under=-0.6, under_color='fern2')
    a0 = rnd.uniform(0, 2 * math.pi)
    for i in range(n):
        a = a0 + (i + rnd.uniform(-0.2, 0.2)) / n * 2 * math.pi
        frond(k, rnd, x, y, z0 + 0.08 * s, a, rnd.uniform(0.85, 1.15) * s, 0.3 * s, rnd.uniform(0.38, 0.55) * s, rnd.uniform(0.45, 0.62) * s)


def conifer(k, rnd, x, y, z0, h, r, tiers=5, col=('leaf3', 'leaf', 'leaf2'), seg=7):
    """Stacked cone tiers (a young redwood crown)."""
    for t in range(tiers):
        f = t / max(1, tiers - 1)
        zb = z0 + h * 0.78 * f
        rr = r * (1.0 - 0.72 * f)
        hh = h * 0.36 * (1.0 - 0.3 * f)
        ox, oy = rnd.uniform(-0.06, 0.06) * r, rnd.uniform(-0.06, 0.06) * r
        k.cyl(x + ox, y + oy, zb, rr, rr * 0.18, hh, col[t % 2], seg=seg, rot=(rnd.uniform(-6, 6), rnd.uniform(-6, 6), rnd.uniform(0, 60)))
    k.cyl(x, y, z0 + h * 0.86, r * 0.16, 0.0, h * 0.2, col[1], seg=5)


def ftop(rnd, n):
    return [rnd.uniform(-0.04, 0.04) for _ in range(n)]


# ================================================================ climbable redwood (landmark)
def treads():
    """[(x0, x1, y0, y1, top, side)] bottom-up; see the module docstring"""
    T, k = [], 1

    def add(x0, x1, y0, y1, side):
        nonlocal k
        T.append((x0, x1, y0, y1, k * STEP, side))
        k += 1
    add(-OUT, -A, -OUT, -A, 'SW')
    for i in range(8):
        add(-A + i * TD, -A + (i + 1) * TD, -OUT, -IN, 'S')
    add(A, OUT, -OUT, -A, 'SE')
    for i in range(8):
        add(IN, OUT, -A + i * TD, -A + (i + 1) * TD, 'E')
    add(A, OUT, A, OUT, 'NE')
    for i in range(4):
        add(A - (i + 1) * TD, A - i * TD, IN, OUT, 'N')
    assert k * STEP == DECK
    return T


ROOTS = [(25, 3.5, 1.7), (105, 3.6, 2.1), (145, 3.8, 2.3), (180, 3.7, 2.0), (210, 3.55, 1.6)]   # angle, reach, height


def trunk_cols(k, rc_steps):
    for (z0, z1, rc) in rc_steps:
        for th in (11.25, 33.75, 56.25, 78.75):
            hx, hy = rc * math.cos(math.radians(th)), rc * math.sin(math.radians(th))
            k.col(-hx, hx, -hy, hy, z0, z1)


def root(k, rnd, ang, reach, h, r0=1.45, cols=True, w=0.36):
    d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    s = (-d[1], d[0])
    pts = []
    for (r, z, hw) in ((r0, h, w), (r0 + (reach - r0) * 0.45, h * 0.42, w * 0.8), (reach, 0.12, w * 0.3)):
        for sg in (-1, 1):
            pts.append((d[0] * r + s[0] * hw * sg, d[1] * r + s[1] * hw * sg, -0.12))
            pts.append((d[0] * r + s[0] * hw * 0.5 * sg, d[1] * r + s[1] * hw * 0.5 * sg, z * rnd.uniform(0.92, 1.05)))
    pts.append((d[0] * (reach + 0.15), d[1] * (reach + 0.15), -0.08))
    k.hullp(pts, barkcol)
    if cols:
        for t in (0.25, 0.55, 0.82):
            r = r0 + (reach - r0) * t + 0.1
            zz = h * (1 - t) * 0.82 + 0.05
            cx, cy = d[0] * r, d[1] * r
            k.col(cx - 0.18, cx + 0.18, cy - 0.18, cy + 0.18, 0, max(0.1, zz))


def crown(k, rnd, z0, z1, reach, tiers, trunk_r):
    """Redwood crown: tiers of drooping limbs with flattened foliage sprays, a narrow spire on top."""
    a0 = rnd.uniform(0, 2 * math.pi)
    for t in range(tiers):
        f = t / max(1, tiers - 1)
        z = z0 + (z1 - z0) * f
        L = reach * (1.0 - 0.62 * f) * rnd.uniform(0.85, 1.1)
        nb = 3 if t % 2 == 0 else 2
        for b in range(nb):
            a = a0 + t * 2.1 + b * 2 * math.pi / nb + rnd.uniform(-0.3, 0.3)
            dx, dy = math.cos(a), math.sin(a)
            rr = trunk_r(z) * 0.7
            tip = (dx * L, dy * L, z - L * 0.18)
            k.beam((dx * rr, dy * rr, z + 0.2), (tip[0] * 0.7, tip[1] * 0.7, tip[2] + 0.3), 0.22 + 0.1 * (1 - f), 'bark2')
            blob(k, rnd, tip[0] * 0.62, tip[1] * 0.62, tip[2] - 0.2, L * 0.42, L * 0.32, 1.25, leafcol('leaf3', 'leaf', 'leaf2'), n=4)
            blob(k, rnd, tip[0] * 0.95, tip[1] * 0.95, tip[2] - 0.55, L * 0.3, L * 0.26, 0.95, leafcol('leaf4', 'leaf3', 'leaf2'), n=4)
    k.cyl(0, 0, z1 - 1.0, 1.25, 0.0, 6.0, 'leaf2', seg=7)
    blob(k, rnd, 0, 0, z1 - 1.6, 1.9, 1.7, 2.2, leafcol('leaf3', 'leaf', 'leaf2'), n=6)


def redwood_trunk_r(z):
    pts = [(-0.3, 2.0), (0.0, 1.98), (0.7, 1.88), (1.6, 1.82), (4.0, 1.79), (9.0, 1.75), (14.0, 1.65), (20.0, 1.48), (27.0, 1.25),
           (34.0, 0.98), (40.0, 0.68), (45.0, 0.38), (48.0, 0.15)]
    for (za, ra), (zb, rb) in zip(pts, pts[1:]):
        if za <= z <= zb:
            return ra + (rb - ra) * (z - za) / (zb - za)
    return 0.15


def build_redwood(k, ao, name, seed):
    rnd = random.Random(seed)
    k.begin()
    rings = [(z, redwood_trunk_r(z)) for z in (-0.3, 0.7, 1.6, 9.0, 14.0, 20.0, 27.0, 34.0, 41.0)]
    lathe(k, rings, 30, bark_faces(seed), flute=flute3, phase=rnd.uniform(0, 1), twist=0.012, top=49.0)
    trunk_cols(k, [(0.0, 0.6, 1.8), (0.6, 14.0, 1.7), (14.0, 24.0, 1.4), (24.0, 34.0, 1.05)])
    for (ang, reach, h) in ROOTS:
        root(k, rnd, ang + rnd.uniform(-4, 4), reach * rnd.uniform(0.95, 1.02), h * rnd.uniform(0.9, 1.1))
    # a mossy stone between the roots
    rock(k, rnd, math.cos(math.radians(163)) * 2.7, math.sin(math.radians(163)) * 2.7, 0.4, 0.34, 0.4)
    # ---- staircase
    T = treads()
    for idx, (x0, x1, y0, y1, top, side) in enumerate(T):
        e = 0.012
        k.bx(x0 + e, x1 - e, y0 + e, y1 - e, top - 0.08, top, 'wood3' if idx % 2 else 'wood')
        if idx < SOLID_RISE:   # solid block down to the ground, boards on the outside
            k.bx(x0 + e + 0.02, x1 - e - 0.02, y0 + e + 0.02, y1 - e - 0.02, -0.1, top - 0.08, 'wood2')
            k.wcol(x0, x1, y0, y1, 0.0, top)
        else:
            k.wcol(x0, x1, y0, y1, top - 0.3, top)
            if idx % 2 and side not in ('SE', 'NE'):
                continue   # a bracket under every other tread (the stringer carries the rest)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ang = math.atan2(cy, cx) if side in ('SE', 'NE') else {'S': -math.pi / 2, 'E': 0.0, 'N': math.pi / 2}[side]
            ox, oy = (cx, cy) if side in ('SE', 'NE') else ((cx, 3.0 * math.sin(ang)) if side in 'SN' else (3.0, cy))
            ix, iy = math.cos(ang) * 1.55, math.sin(ang) * 1.55
            if side in 'SN':
                ix = cx
            if side == 'E':
                iy = cy
            k.beam((ix, iy, top - 0.85), (ox * 0.98, oy * 0.98, top - 0.13), 0.13, 'wood2')
    # outer stringers under the hollow treads, one per flight
    def ttop(i):
        return T[i][4]
    k.beam((-0.25, -3.06, ttop(4) - 0.34), (1.85, -3.06, ttop(8) - 0.34), 0.14, 'woodd')
    k.beam((3.06, -1.75, ttop(10) - 0.34), (3.06, 1.75, ttop(17) - 0.34), 0.14, 'woodd')
    k.beam((1.75, 3.06, ttop(19) - 0.34), (0.25, 3.06, ttop(22) - 0.34), 0.14, 'woodd')
    # support posts from the ground (log posts) that carry on up as rail posts
    posts = [((3.06, -3.06), ttop(9)), ((3.06, 3.06), ttop(18)), ((3.06, -0.25), ttop(13)), ((1.25, 3.06), ttop(20))]
    for (px, py), tz in posts:
        k.cyl(px, py, -0.1, 0.13, 0.11, tz - 0.08 + 0.1, 'wood2', seg=6)
        k.col(px - 0.12, px + 0.12, py - 0.12, py + 0.12, 0.0, tz - 0.08)
        rock(k, rnd, px, py, 0.26, 0.24, 0.22, col=baldcol)
    # railing: posts, handrail and a rope along the outer edge; one collision box per tread edge
    RH = 1.0
    rail_pts = {'S': [], 'E': [], 'N': []}
    for idx, (x0, x1, y0, y1, top, side) in enumerate(T):
        edges = {'SW': [], 'S': ['S'], 'SE': ['S', 'E'], 'E': ['E'], 'NE': ['E', 'N'], 'N': ['N']}[side]
        for ed in edges:
            if ed == 'S':
                k.col(x0, x1, -OUT, -OUT + 0.1, top, top + RH)
            elif ed == 'E':
                k.col(OUT - 0.1, OUT, y0, y1, top, top + RH)
            else:
                k.col(x0, x1, OUT - 0.1, OUT, top, top + RH)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if side == 'S' and idx % 2 == 1:
            rail_pts['S'].append((cx, -3.15, top))
        if side == 'E' and idx % 2 == 0:
            rail_pts['E'].append((3.15, cy, top))
        if side == 'N' and idx % 2 == 1:
            rail_pts['N'].append((cx, 3.15, top))
    for side, pts in rail_pts.items():
        for (px, py, top) in pts:
            k.bx(px - 0.05, px + 0.05, py - 0.05, py + 0.05, top, top + RH + 0.04, 'wood2')
    cSE, cNE = (3.1, -3.1, ttop(9)), (3.1, 3.1, ttop(18))
    for (px, py, top) in (cSE, cNE):
        k.bx(px - 0.06, px + 0.06, py - 0.06, py + 0.06, top, top + RH + 0.05, 'wood2')
    runs = [[rail_pts['S'][0]] + rail_pts['S'] + [cSE], [cSE] + rail_pts['E'] + [cNE], [cNE] + rail_pts['N'] + [(0.03, 3.15, DECK)]]
    for run in runs:
        a, b = run[0], run[-1]
        if run is runs[0]:
            a = (-1.95, -3.15, a[2])
        k.beam((a[0], a[1], a[2] + RH + 0.02), (b[0], b[1], b[2] + RH + 0.02), 0.09, 'wood3')
        k.beam((a[0], a[1], a[2] + RH * 0.5), (b[0], b[1], b[2] + RH * 0.5), 0.035, 'rope', ink=False)
    # ---- platform at 9 m: W part [-4, 0] x [-4, 4], SE part [0, 4] x [-4, E2] plus [0, E2] x [E2, 2]: it keeps clear
    # of the head room over the top of the east flight and the NE corner (E2 = 1.2)
    E2 = 1.2
    zt, zs = DECK, DECK - 0.06
    k.bx(-FOOT + 0.05, 0.0, -FOOT + 0.05, FOOT - 0.05, DECK - 0.28, zs, 'woodd')
    k.bx(0.0, FOOT - 0.05, -FOOT + 0.05, E2, DECK - 0.28, zs, 'woodd')
    k.bx(0.0, E2, E2, A, DECK - 0.28, zs, 'woodd')
    k.wcol(-FOOT, 0.0, -FOOT, FOOT, DECK - 0.3, DECK)
    k.wcol(0.0, FOOT, -FOOT, E2, DECK - 0.3, DECK)
    k.wcol(0.0, E2, E2, A, DECK - 0.3, DECK)
    pc = ['wood', 'wood3', 'wood', 'wood2', 'wood3', 'wood']
    for i in range(20):
        y0 = -FOOT + i * 0.4 + 0.012
        y1 = y0 + 0.376
        k.bx(-FOOT + 0.01, -0.012, y0, y1, zs, zt, pc[i % 6])
        if y1 <= E2:
            k.bx(0.012, FOOT - 0.01, y0, y1, zs, zt, pc[(i + 3) % 6])
        elif y1 <= A:
            k.bx(0.012, E2 - 0.012, y0, y1, zs, zt, pc[(i + 3) % 6])
    # fascia boards on the outer edges (below the plank tops), joists and knee braces underneath
    k.bx(-FOOT, -FOOT + 0.05, -FOOT, FOOT, DECK - 0.32, zs - 0.004, 'wood2')
    k.bx(-FOOT + 0.05, 0.0, FOOT - 0.05, FOOT, DECK - 0.32, zs - 0.004, 'wood2')
    k.bx(-FOOT + 0.05, FOOT - 0.05, -FOOT, -FOOT + 0.05, DECK - 0.32, zs - 0.004, 'wood2')
    k.bx(FOOT - 0.05, FOOT, -FOOT, E2, DECK - 0.32, zs - 0.004, 'wood2')
    for jx in (-3.5, -2.5, -0.6, 0.6, 2.6, 3.5):
        y1 = FOOT - 0.1 if jx < 0 else (A - 0.06 if jx < E2 else E2 - 0.06)
        k.bx(jx - 0.08, jx + 0.08, -FOOT + 0.1, y1, DECK - 0.52, DECK - 0.28, 'wood2')
    for ang in (135, 180, 225, 270, 315):
        a = math.radians(ang)
        k.beam((math.cos(a) * 1.5, math.sin(a) * 1.5, DECK - 2.6), (math.cos(a) * 3.5, math.sin(a) * 3.5, DECK - 0.32), 0.17, 'wood2')
    k.cyl(0, 0, DECK + 0.25, 1.83, 1.83, 0.14, 'rope', seg=12)
    # stairwell rails at deck level: along y = E2 (x E2..4), x = E2 (y E2..2), y = 2 (x 0.6..E2), x = 0 (y 3.2..4)
    rails_n = [0]

    def rail(x0, x1, y0, y1, posts):
        rails_n[0] += 1
        dz = 0.006 * rails_n[0]   # meeting handrails overlap at the corners: each on its own height
        for (px, py) in posts:
            k.bx(px - 0.037, px + 0.037, py - 0.037, py + 0.037, DECK, DECK + RH + 0.04, 'wood2')
        k.bx(x0 - 0.005, x1 + 0.005, y0 - 0.005, y1 + 0.005, DECK + RH + dz, DECK + RH + 0.08 + dz, 'wood3')
        k.col(x0, x1, y0, y1, DECK, DECK + RH)
    rail(E2 - 0.085, FOOT - 0.01, E2 - 0.09, E2, [(E2 - 0.04, E2 - 0.045), (2.6, E2 - 0.045), (FOOT - 0.06, E2 - 0.045)])
    k.bx(E2 + 0.05, FOOT - 0.07, E2 - 0.06, E2 - 0.03, DECK + 0.5, DECK + 0.535, 'rope', ink=False)
    rail(E2 - 0.09, E2, E2 + 0.005, A - 0.012, [(E2 - 0.045, A - 0.05)])
    rail(0.58, E2 - 0.095, A - 0.09, A, [(0.65, A - 0.045)])
    rail(-0.09, 0.0, OUT - 0.02, FOOT - 0.17, [(-0.045, 3.25), (-0.045, 3.78)])
    # a lantern hook and lantern on the trunk above the deck (west side)
    k.beam((-1.75, 0.0, DECK + 2.6), (-2.3, 0.0, DECK + 2.6), 0.06, 'woodd')
    k.bx(-2.38, -2.22, -0.08, 0.08, DECK + 2.0, DECK + 2.45, 'window')
    k.bx(-2.4, -2.2, -0.1, 0.1, DECK + 2.45, DECK + 2.53, 'woodd')
    # ---- above: broken stubs, then the crown
    for i in range(4):
        a = rnd.uniform(0, 2 * math.pi)
        z = 14.5 + i * 1.9
        r = redwood_trunk_r(z)
        k.beam((math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, z), (math.cos(a) * (r + 1.1), math.sin(a) * (r + 1.1), z + 0.5), 0.2, 'bark2')
    crown(k, rnd, 22.0 + rnd.uniform(-1, 1), 44.0, 6.2, 6, redwood_trunk_r)
    k.finish(name, ao=ao)


# ================================================================ big trees (not climbable)
def giant_r(z, s):
    pts = [(-0.3, 1.75), (0.0, 1.72), (0.8, 1.5), (2.0, 1.4), (8.0, 1.32), (16.0, 1.18), (24.0, 1.0), (32.0, 0.78), (40.0, 0.5), (46.0, 0.22)]
    for (za, ra), (zb, rb) in zip(pts, pts[1:]):
        if za <= z <= zb:
            return s * (ra + (rb - ra) * (z - za) / (zb - za))
    return 0.2 * s


def build_giant(k, ao, name, seed, s):
    rnd = random.Random(seed)
    k.begin()
    rings = [(z, giant_r(z, s)) for z in (-0.3, 0.0, 0.8, 2.0, 8.0, 16.0, 24.0, 32.0, 40.0)]
    lathe(k, rings, 24, bark_faces(seed), flute=flute3, phase=rnd.uniform(0, 1), twist=0.015, top=46.0)
    trunk_cols(k, [(0.0, 16.0, 1.3 * s), (16.0, 30.0, 1.0 * s)])
    for i in range(6):
        ang = i * 60 + rnd.uniform(-12, 12)
        root(k, rnd, ang, 2.15 + rnd.uniform(-0.1, 0.25), 1.6 * s * rnd.uniform(0.8, 1.15), r0=1.1 * s, cols=False, w=0.3)
    # a fire-hollow at the foot (dark opening) on the south side
    k.hullp([(-0.45, -1.45 * s - 0.05, 0.0), (0.45, -1.45 * s - 0.05, 0.0), (0.0, -1.42 * s - 0.05, 1.7), (-0.2, -1.38 * s - 0.05, 1.2), (0.25, -1.38 * s - 0.05, 1.0),
             (-0.4, -1.2 * s, 0.0), (0.4, -1.2 * s, 0.0), (0.0, -1.2 * s, 1.6)], 'ink')
    for i in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        z = 13 + i * 2.5
        r = giant_r(z, s)
        k.beam((math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, z), (math.cos(a) * (r + 0.9), math.sin(a) * (r + 0.9), z + 0.4), 0.18, 'bark2')
    crown(k, rnd, 21.0, 42.0, 5.2 * s, 6, lambda z: giant_r(z, s))
    k.finish(name, ao=ao)


def build_young(k, ao):
    for name, seed, h, r, tr in (('Redwood_Young_A', 31, 15.0, 2.2, 0.36), ('Redwood_Young_B', 32, 19.0, 2.6, 0.42), ('Redwood_Young_C', 33, 12.0, 1.9, 0.3)):
        rnd = random.Random(seed)
        k.begin()
        lathe(k, [(-0.2, tr * 1.45), (0.0, tr * 1.4), (0.5, tr * 1.08), (2.0, tr), (h * 0.6, tr * 0.6)], 9,
              lambda i, j: 'bark2' if i % 3 == 0 or j < 0 else ('bark3' if i % 3 == 1 else 'bark'), flute=flute3, top=h * 0.66)
        k.col(-tr * 0.75, tr * 0.75, -tr * 0.75, tr * 0.75, 0, 6.0)
        conifer(k, rnd, 0, 0, h * 0.38, h * 0.64, r, tiers=4, col=('leaf', 'leaf2'), seg=6)
        for i in range(3):
            a = i * 2.1 + rnd.uniform(-0.3, 0.3)
            k.hullp([(math.cos(a) * tr * 0.6, math.sin(a) * tr * 0.6, 0.45), (math.cos(a) * tr * 0.6 + 0.05, math.sin(a) * tr * 0.6, -0.1),
                     (math.cos(a) * (tr + 0.42), math.sin(a) * (tr + 0.42), -0.05), (math.cos(a) * (tr + 0.42), math.sin(a) * (tr + 0.42), 0.06),
                     (math.cos(a + 0.4) * tr, math.sin(a + 0.4) * tr, 0.0), (math.cos(a - 0.4) * tr, math.sin(a - 0.4) * tr, 0.0)], barkcol)
        k.finish(name, ao=ao)


def build_snag_stump(k, ao):
    # fire-hollowed snag (2 x 2): a broken trunk with a jagged top, blackened lower bark, shelf fungi
    rnd = random.Random(41)
    k.begin()
    jag = [1.0, 0.55, 0.85, 0.35, 0.7, 0.95, 0.45, 0.8, 0.6, 0.9, 0.4, 0.75]
    rings = [(-0.2, 0.98), (0.0, 0.95), (0.6, 0.82), (2.5, 0.76), (5.0, 0.7)]
    lathe(k, rings, 12, lambda i, j: ('ink' if (j < 2 and i in (5, 6, 7)) else ('bark2' if i % 2 else 'bark')), flute=lambda i: 0.94 if i % 2 else 1.0)
    # splintered top: a dark hollow cap and jagged shards
    k.hullp([(math.cos(i * math.pi / 6) * 0.69, math.sin(i * math.pi / 6) * 0.69, 4.98) for i in range(12)] + [(0, 0, 5.4)], 'woodd')
    for i in range(12):
        if jag[i] > 0.5:
            a = i * math.pi / 6
            k.hullp([(math.cos(a - 0.22) * 0.72, math.sin(a - 0.22) * 0.72, 4.95), (math.cos(a + 0.22) * 0.72, math.sin(a + 0.22) * 0.72, 4.95),
                     (math.cos(a) * 0.5, math.sin(a) * 0.5, 4.95), (math.cos(a) * 0.62, math.sin(a) * 0.62, 5.0 + 2.2 * jag[i])], lambda f: 'heart' if f.normal.z > 0.3 else 'bark')
    k.col(-0.68, 0.68, -0.68, 0.68, 0, 6.5)
    for (z, a) in ((1.6, 0.4), (2.1, 0.9), (3.2, 2.4)):
        k.cyl(math.cos(a) * 0.72, math.sin(a) * 0.72, z, 0.32, 0.26, 0.09, 'shelf', seg=8)
    for i in range(4):
        a = i * 1.6 + 0.3
        root(k, rnd, math.degrees(a), 1.45, 0.9, r0=0.7, cols=False, w=0.22)
    fern(k, rnd, 0.9, -0.7, 0.7, n=5)
    k.finish('Snag', ao=ao)
    # cut stump (2 x 2): rings on the saw cut, moss, mushrooms
    rnd = random.Random(42)
    k.begin()
    lathe(k, [(-0.2, 1.08), (0.0, 1.05), (0.35, 0.92), (1.05, 0.88)], 18, lambda i, j: 'bark2' if i % 3 == 0 else ('bark3' if (i // 3) % 3 == 0 else 'bark'),
          flute=lambda i: 0.94 if i % 3 == 0 else 1.0)
    k.disc(0, 0, 1.05, 0.86, 'heart', n=18)
    for i, (r, c) in enumerate(((0.7, 'bark3'), (0.56, 'heart'), (0.42, 'bark3'), (0.28, 'heart'), (0.12, 'bark3'))):
        k.disc(0.03 * i, 0.02 * i, 1.05 + 0.004 * (i + 1), r, c, n=14)
    k.col(-0.78, 0.78, -0.78, 0.78, 0, 1.05)
    k.hullp([(math.cos(a) * 1.0, math.sin(a) * 1.0, z) for a in (2.4, 2.9, 3.4, 3.9) for z in (0.0, 0.7)] + [(math.cos(3.1) * 0.75, math.sin(3.1) * 0.75, 0.9)], lambda f: 'moss' if f.normal.z > 0.2 else 'mossd')
    for (a, z, r) in ((0.4, 0.5, 0.11), (0.7, 0.35, 0.08), (5.6, 0.62, 0.09)):
        x, y = math.cos(a) * 0.98, math.sin(a) * 0.98
        k.cyl(x, y, z - 0.16, 0.025, 0.02, 0.17, 'mush2', seg=5)
        k.sph(x, y, z, r, 'mush', seg=(7, 4), scale=(1, 1, 0.55))
    fern(k, rnd, -1.15, -0.3, 0.6, n=5)
    k.finish('Stump', ao=ao)


def log_body(k, rnd, x0, x1, r, zc, moss=True, rings=True):
    k.cyl(x0, 0, zc, r, r * 0.94, x1 - x0, 'bark', seg=10, rot=(0, 90, 0))
    for i in range(5):   # bark ridges along the log
        a = i * 1.25 + 0.4
        k.bxr((x0 + x1) / 2, math.cos(a) * r * 0.97, zc + math.sin(a) * r * 0.97, (x1 - x0) * 0.9, 0.06, 0.06, 'bark2', rot=(math.degrees(a), 0, 0), ink=False)
    if moss:
        L = x1 - x0
        k.hullp([(x0 + L * f, y, zc + r * 0.8 + dz) for f in (0.12, 0.45, 0.78) for (y, dz) in ((-r * 0.55, -0.05), (r * 0.5, -0.06), (0.0, 0.14 + 0.05 * f))],
                lambda f: 'moss2' if f.normal.z > 0.6 else 'moss')
    if rings:
        k.cyl(x1 - 0.002, 0, zc, r * 0.8, r * 0.8, 0.012, 'heart', seg=10, rot=(0, 90, 0), ink=False)


def build_logs(k, ao):
    # fallen giant (6 x 2, along X): root plate at -X, broken splintered end at +X, moss, ferns, shelf fungi
    rnd = random.Random(51)
    k.begin()
    r, zc = 0.66, 0.56
    log_body(k, rnd, -2.45, 2.55, r, zc, rings=False)
    for i in range(7):   # splinters at the break
        a = i * 0.9 + 0.2
        k.hullp([(2.5, math.cos(a) * r * 0.85, zc + math.sin(a) * r * 0.85), (2.5, math.cos(a + 0.5) * r * 0.85, zc + math.sin(a + 0.5) * r * 0.85),
                 (2.5, math.cos(a + 0.25) * r * 0.5, zc + math.sin(a + 0.25) * r * 0.5), (2.75 + 0.25 * (i % 3), math.cos(a + 0.25) * r * 0.7, zc + math.sin(a + 0.25) * r * 0.7)],
                lambda f: 'heart' if f.normal.x > 0.3 else 'bark')
    # root plate: soil disc with root stubs
    k.cyl(-2.95, 0, zc + 0.15, 1.25, 1.15, 0.5, 'soil', seg=12, rot=(0, 90, 0))
    for i in range(7):
        a = i * 0.9
        k.beam((-2.7, math.cos(a) * 0.9, zc + 0.15 + math.sin(a) * 0.9), (-3.0 - 0.15 * (i % 2), math.cos(a) * 1.45, zc + 0.15 + math.sin(a) * 1.45), 0.13, 'bark2')
    rock(k, rnd, -2.75, -0.55, 0.22, 0.2, 0.25, z0=zc + 1.0, col=baldcol)
    k.col(-2.45, 2.55, -0.62, 0.62, 0, zc + r - 0.04)
    k.col(-2.95, -2.45, -1.1, 1.1, 0, 1.75)
    fern(k, rnd, 0.3, 0.12, 0.55, z0=zc + r + 0.02, n=5)
    fern(k, rnd, -1.6, -0.05, 0.45, z0=zc + r + 0.02, n=4)
    for (x, z) in ((-1.0, 0.5), (-0.5, 0.75), (1.5, 0.55)):
        k.cyl(x, -r * 0.98, z, 0.3, 0.24, 0.08, 'shelf', seg=8, rot=(90, 0, 0))
    for (x, y) in ((1.1, 0.85), (1.3, 0.95), (-1.9, -0.95)):
        k.cyl(x, y, 0, 0.022, 0.018, 0.14, 'mush2', seg=5)
        k.sph(x, y, 0.15, 0.08, 'mush', seg=(7, 4), scale=(1, 1, 0.55))
    k.finish('Log_Big', ao=ao)
    # small mossy log (3 x 1)
    rnd = random.Random(52)
    k.begin()
    log_body(k, rnd, -1.42, 1.42, 0.33, 0.3)
    k.cyl(-1.42 - 0.012, 0, 0.3, 0.27, 0.27, 0.014, 'heart', seg=10, rot=(0, 90, 0), ink=False)
    k.col(-1.42, 1.42, -0.33, 0.33, 0, 0.62)
    for (x, z) in ((-0.5, 0.3), (0.6, 0.38)):
        k.cyl(x, -0.32, z, 0.16, 0.13, 0.06, 'shelf', seg=7, rot=(90, 0, 0))
    k.finish('Log_Small', ao=ao)


def build_rocks(k, ao):
    for name, seed, rx, ry, h in (('Rock_A', 61, 0.44, 0.38, 0.62), ('Rock_B', 62, 0.4, 0.42, 0.5)):
        rnd = random.Random(seed)
        k.begin()
        rock(k, rnd, 0, 0, rx, ry, h, z0=-0.08, n=7)
        rock(k, rnd, rx * 0.9, -ry * 0.5, 0.16, 0.14, 0.18, z0=-0.04, n=5, col=baldcol)
        k.col(-rx * 0.8, rx * 0.8, -ry * 0.8, ry * 0.8, 0, h * 0.85)
        k.finish(name, ao=ao)
    for name, seed in (('Boulder_A', 63), ('Boulder_B', 64)):
        rnd = random.Random(seed)
        k.begin()
        rock(k, rnd, 0, 0, 0.98, 0.86, 1.55, z0=-0.12, n=8)
        rock(k, rnd, -0.65, 0.55, 0.45, 0.4, 0.75, z0=-0.1, n=6)
        rock(k, rnd, 0.75, -0.6, 0.3, 0.28, 0.35, z0=-0.06, n=6, col=baldcol)
        fern(k, rnd, 0.75, 0.62, 0.65, n=5)
        k.col(-0.82, 0.82, -0.72, 0.72, 0, 1.35)
        k.finish(name, ao=ao)
    rnd = random.Random(65)
    k.begin()   # pebbles (walk-through)
    for i in range(4):
        a = i * 1.57 + rnd.uniform(-0.3, 0.3)
        rr = rnd.uniform(0.12, 0.38)
        rock(k, rnd, math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(0.07, 0.13), rnd.uniform(0.06, 0.12), rnd.uniform(0.06, 0.12), z0=-0.03, n=5, col=baldcol)
    k.finish('Pebbles', ao=ao)


def build_plants(k, ao):
    for name, seed, s, n in (('Fern_A', 71, 1.2, 6), ('Fern_B', 72, 0.95, 5), ('Fern_C', 73, 1.45, 6)):
        rnd = random.Random(seed)
        k.begin()
        fern(k, rnd, 0, 0, s, n=n)
        k.finish(name, ao=ao)
    # salal / huckleberry shrubs (solid cover)
    for name, seed, cols, berry in (('Shrub_A', 74, ('leaf3', 'leaf', 'leaf2'), None), ('Shrub_B', 75, ('fern3', 'fern', 'fern2'), None),
                                    ('Huckleberry', 76, ('leaf4', 'leaf3', 'leaf'), 'berry')):
        rnd = random.Random(seed)
        k.begin()
        blob(k, rnd, 0, 0, -0.05, 0.5, 0.46, 0.95, leafcol(*cols), n=5)
        blob(k, rnd, 0.22, 0.18, 0.25, 0.32, 0.3, 0.78, leafcol(*cols), n=4)
        blob(k, rnd, -0.25, -0.12, 0.15, 0.3, 0.28, 0.62, leafcol(*cols), n=4)
        for i in range(3):
            a = i * 2.1
            k.beam((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.0), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.35), 0.05, 'woodd')
        if berry:
            for i in range(9):
                a = i * 0.7 + rnd.uniform(-0.1, 0.1)
                z = rnd.uniform(0.35, 0.85)
                rr = 0.49 * math.sqrt(max(0.05, 1 - ((z - 0.42) / 0.55) ** 2)) + 0.03
                k.sph(math.cos(a) * rr, math.sin(a) * rr, z, 0.045, berry, seg=(5, 3), ink=False)
        k.col(-0.42, 0.42, -0.42, 0.42, 0, 0.95)
        k.finish(name, ao=ao)
    # oxalis carpet (walk-through): a low mound of clover leaves with tiny flowers
    for name, seed, fl in (('Clover_A', 77, 'flower'), ('Clover_B', 78, 'mush2')):
        rnd = random.Random(seed)
        k.begin()
        blob(k, rnd, 0, 0, -0.06, 0.62, 0.55, 0.2, leafcol('clover', 'clover2', 'clover2'), n=6)
        for i in range(7):
            a = rnd.uniform(0, 2 * math.pi)
            rr = rnd.uniform(0.1, 0.55)
            x, y = math.cos(a) * rr, math.sin(a) * rr
            z = 0.14 * math.sqrt(max(0.0, 1 - (rr / 0.62) ** 2)) + 0.03
            star(k, (x, y, z + 0.006 * i), 0.13, 0.03, 'clover' if i % 3 else 'fern3', pts=3, inner=0.3, droop=0.01, phase=a * 57, under=-0.5, under_color='clover2', ink=False)
        for i in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            rr = rnd.uniform(0.1, 0.45)
            x, y = math.cos(a) * rr, math.sin(a) * rr
            k.cyl(x, y, 0.05, 0.008, 0.008, 0.16, 'clover2', seg=3, ink=False)
            k.sph(x, y, 0.22, 0.035, fl, seg=(5, 3), ink=False)
        k.finish(name, ao=ao)
    # mushrooms: red caps with white spots / a tan cluster on a bit of rotten wood
    rnd = random.Random(79)
    k.begin()
    for (x, y, h, r) in ((0.0, 0.0, 0.32, 0.16), (0.2, 0.12, 0.22, 0.11), (-0.16, -0.14, 0.16, 0.08)):
        k.cyl(x, y, -0.02, r * 0.32, r * 0.26, h + 0.02, 'mush2', seg=5)
        k.sph(x, y, h, r, 'mush', seg=(7, 3), scale=(1, 1, 0.62))
        for j in range(3 if r > 0.1 else 0):
            a = j * 1.6 + x * 10
            k.sph(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, h + r * 0.42, r * 0.14, 'mush2', seg=(4, 3), scale=(1, 1, 0.5), ink=False)
    k.finish('Mushrooms_A', ao=ao)
    rnd = random.Random(80)
    k.begin()
    k.cyl(-0.4, 0, 0.11, 0.13, 0.12, 0.8, 'wood2', seg=7, rot=(0, 90, 0))
    for i in range(5):
        x, y = rnd.uniform(-0.3, 0.35), rnd.uniform(-0.3, 0.3)
        h = rnd.uniform(0.08, 0.2)
        k.cyl(x, y, -0.02, 0.02, 0.016, h + 0.02, 'mush2', seg=4)
        k.sph(x, y, h, rnd.uniform(0.05, 0.08), 'mush3', seg=(6, 3), scale=(1, 1, 0.5))
    k.finish('Mushrooms_B', ao=ao)
    # trilliums (white three-petal flowers over three broad leaves)
    rnd = random.Random(81)
    k.begin()
    for (x, y, h) in ((0.0, 0.0, 0.3), (0.28, 0.15, 0.24), (-0.22, 0.2, 0.26)):
        k.cyl(x, y, -0.02, 0.012, 0.012, h + 0.02, 'clover2', seg=3, ink=False)
        star(k, (x, y, h - 0.04), 0.16, 0.03, 'fern', pts=3, inner=0.35, droop=0.04, phase=x * 300, under=-0.6, under_color='fern2')
        star(k, (x, y, h + 0.03), 0.09, 0.03, 'flower', pts=3, inner=0.45, droop=-0.01, phase=x * 300 + 60, under=-0.5, under_color='flower')
        k.sph(x, y, h + 0.065, 0.016, 'amber', seg=(4, 3), ink=False)
    k.finish('Trillium', ao=ao)
    # sedge tuft (creek banks): thin arching blades
    rnd = random.Random(82)
    k.begin()
    for i in range(5):
        a = i * 1.26 + rnd.uniform(-0.2, 0.2)
        L = rnd.uniform(0.5, 0.85)
        k.beam((math.cos(a) * 0.04, math.sin(a) * 0.04, -0.02), (math.cos(a) * L * 0.45, math.sin(a) * L * 0.45, L * 0.8), 0.035, ['fern', 'fern2', 'moss'][i % 3])
    k.finish('Sedge', ao=ao)


def build_water(k, ao):
    """creek tiles (1 x 1, flat, walkable): water at 3 cm, ripples and stones on top"""
    for name, seed in (('Creek_A', 91), ('Creek_B', 92), ('Creek_C', 93)):
        rnd = random.Random(seed)
        k.begin()
        k.qz(-0.5, 0.5, -0.5, 0.5, 0.03, 1, 'water')
        if name == 'Creek_A':
            for i in range(2):
                y = -0.25 + i * 0.45
                k.qz(-0.3 + 0.1 * i, 0.15 + 0.1 * i, y - 0.018, y + 0.018, 0.034, 1, 'water2')
        if name == 'Creek_B':
            for (x, y, r) in ((-0.1, 0.05, 0.18),):
                k.disc(x, y, 0.034, r + 0.07, 'foam', n=9, rnd=rnd, jag=0.12)
                rock(k, rnd, x, y, r, r * 0.85, 0.16, z0=-0.02, n=6, col=baldcol)
        if name == 'Creek_C':
            k.qz(-0.38, 0.38, -0.05, 0.05, 0.034, 1, 'waterd')
            k.disc(0.3, 0.3, 0.038, 0.07, 'foam', n=6)
            rock(k, rnd, -0.3, -0.3, 0.1, 0.09, 0.09, z0=-0.02, n=5, col=baldcol)
        k.finish(name, ao=ao)
    # pond (5 x 5): irregular water with a mud rim, stones, skunk cabbage, lily pads, sedges
    rnd = random.Random(94)
    k.begin()
    k.disc(0, 0, 0.018, 2.38, 'mud', n=22, rnd=rnd, jag=0.06)
    k.disc(0, 0, 0.03, 2.08, 'water', n=22, rnd=rnd, jag=0.07)
    k.disc(-0.3, 0.2, 0.034, 1.25, 'water2', n=14, rnd=rnd, jag=0.1)
    for i in range(6):
        a = i * 1.1 + 0.3
        rr = rnd.uniform(0.6, 1.6)
        k.disc(math.cos(a) * rr, math.sin(a) * rr, 0.04, 0.2, 'leaf4', n=8, a0=a)
    k.disc(0.7, 0.9, 0.044, 0.06, 'flower', n=6)
    for i in range(13):
        a = i / 13 * 2 * math.pi + rnd.uniform(-0.15, 0.15)
        rr = 2.25 + rnd.uniform(-0.1, 0.15)
        if i % 3 == 0:
            rock(k, rnd, math.cos(a) * rr, math.sin(a) * rr, 0.3, 0.26, 0.32, z0=-0.05, n=6)
        elif i % 3 == 1:   # sedge blades
            x, y = math.cos(a) * rr, math.sin(a) * rr
            for j in range(3):
                b = j * 2.1 + a
                L = rnd.uniform(0.45, 0.75)
                k.beam((x, y, -0.02), (x + math.cos(b) * L * 0.4, y + math.sin(b) * L * 0.4, L * 0.8), 0.035, ['fern', 'fern2', 'moss'][j % 3])
        else:   # a fern on the bank (every other spot), a couple of yellow marsh flowers
            if i % 4 == 2:
                fern(k, rnd, math.cos(a) * (rr + 0.15), math.sin(a) * (rr + 0.15), 0.75, n=4)
            for j in range(2):
                x, y = math.cos(a + 0.12 * j) * (rr - 0.35), math.sin(a + 0.12 * j) * (rr - 0.35)
                k.cyl(x, y, 0.0, 0.012, 0.012, 0.3, 'fern2', seg=3, ink=False)
                k.sph(x, y, 0.31, 0.05, 'flame2', seg=(5, 3), scale=(1, 1, 0.6))
    k.finish('Pond', ao=ao)


# ================================================================ ranger station and camp
def logwall(k, x0, x1, y0, y1, z0, z1, col='cabin', face=None):
    """box wall with horizontal log grooves on its outer faces (thin dark bands, no outline)"""
    k.bx(x0, x1, y0, y1, z0, z1, col)
    z = z0 + 0.3
    while z < z1 - 0.1:
        for (fx, s) in face or ():
            if fx == 'S':
                k.bx(x0 + 0.016, x1 - 0.016, y0 - 0.004, y0 + 0.01, z - 0.012, z + 0.012, 'cabin2', ink=False)
            elif fx == 'N':
                k.bx(x0 + 0.016, x1 - 0.016, y1 - 0.01, y1 + 0.004, z - 0.012, z + 0.012, 'cabin2', ink=False)
            elif fx == 'W':
                k.bx(x0 - 0.004, x0 + 0.01, y0 + 0.004, y1 - 0.004, z - 0.012, z + 0.012, 'cabin2', ink=False)
            else:
                k.bx(x1 - 0.01, x1 + 0.004, y0 + 0.004, y1 - 0.004, z - 0.012, z + 0.012, 'cabin2', ink=False)
        z += 0.3


def window(k, x, y, z, w, h, s=-1):
    """window on a wall facing s * Y: glowing pane, frame, sill, open shutters"""
    y = y + 0.004 * s
    d = 0.006 * s
    k.qy(x - w / 2, x + w / 2, z, z + h, y + 2 * d, s, 'window')

    def yy(front, back):   # y range from `back` (inside the wall, each part on its own plane) to `front` (proud)
        a, b = y + front * d, y - back * s
        return min(a, b), max(a, b)
    k.bx(x - w / 2 - 0.08, x + w / 2 + 0.08, *yy(12, 0.01), z - 0.1, z, 'wood3')
    for xx in (x - w / 2 - 0.05, x + w / 2 + 0.05):
        k.bx(xx - 0.04, xx + 0.04, *yy(10, 0.02), z, z + h + 0.06, 'woodd')
    k.bx(x - w / 2 - 0.05, x + w / 2 + 0.05, *yy(10.5, 0.03), z + h, z + h + 0.07, 'woodd')
    k.bx(x - 0.02, x + 0.02, *yy(8, 0.04), z, z + h, 'woodd')
    for sx in (-1, 1):   # shutters swung open against the wall
        xs = x + sx * (w / 2 + 0.11 + 0.22)
        k.bx(xs - 0.21, xs + 0.21, *yy(7, 0.05), z, z + h, 'roof')


def build_cabin(k, ao):
    """ranger station (7 x 6): log cabin with a porch (front = -Y), saltbox roof, stone chimney, sign, woodpile"""
    rnd = random.Random(101)
    k.begin()
    X0, X1, Y0, Y1, H = -2.6, 2.6, -1.2, 2.4, 2.8
    k.hullp([(x, y, z) for x in (X0 - 0.12, X1 + 0.12) for y in (Y0 - 0.12, Y1 + 0.12) for z in (-0.2, 0.32)], baldcol)
    logwall(k, X0, X1, Y0, Y1, 0.32, H, face=(('S', 1), ('N', 1), ('W', 1), ('E', 1)))
    for (cx, cy) in ((X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1)):   # crossed log ends at the corners
        for i in range(8):
            z = 0.45 + i * 0.3
            if i % 2:
                k.cyl(cx - 0.22, cy, z, 0.13, 0.13, 0.44, 'cabin', seg=6, rot=(0, 90, 0))
            else:
                k.cyl(cx, cy - 0.22, z, 0.13, 0.13, 0.44, 'cabin2', seg=6, rot=(-90, 0, 0))
    # porch: plank deck at 0.3 on log joists, posts, a bench
    k.bx(-2.85, 2.85, -2.95, Y0, 0.0, 0.24, 'wood2')
    for i in range(7):
        x0 = -2.84 + i * 0.81
        k.bx(x0, x0 + 0.79, -2.94, Y0 - 0.01, 0.24, 0.3, 'wood3' if i % 2 else 'wood')
    k.wcol(-2.85, 2.85, -2.95, Y0, 0.0, 0.3)
    for px in (-2.65, 2.65):
        k.cyl(px, -2.78, 0.3, 0.12, 0.11, 2.05, 'cabin', seg=6)
        k.col(px - 0.12, px + 0.12, -2.9, -2.66, 0.3, 2.35)
    k.bx(-2.8, 2.8, -2.9, -2.66, 2.3, 2.5, 'cabin2')
    k.bx(-1.2, 0.0, Y0 + 0.02, Y0 + 0.42, 0.3, 0.75, 'wood')   # bench against the wall
    k.bx(-1.15, -0.05, Y0 + 0.05, Y0 + 0.4, 0.75, 0.8, 'wood3')
    # door, windows, lantern
    k.bx(-0.45 + 0.6, 0.45 + 0.6, Y0 - 0.05, Y0 + 0.0, 0.3, 2.3, 'wood2')
    for i in range(3):
        k.bx(-0.4 + 0.6 + i * 0.3, -0.16 + 0.6 + i * 0.3, Y0 - 0.06, Y0 - 0.05, 0.42, 2.18, 'wood', ink=False)
    k.bx(-0.55 + 0.6, 0.55 + 0.6, Y0 - 0.07, Y0 + 0.0, 2.3, 2.42, 'woodd')
    k.sph(0.9, Y0 - 0.1, 1.25, 0.05, 'amber', seg=(5, 3))
    window(k, -1.75, Y0, 1.15, 0.8, 0.8, -1)
    window(k, -0.2, Y1, 1.2, 0.9, 0.75, 1)
    k.bx(1.65, 1.85, Y0 - 0.16, Y0 - 0.0, 1.95, 2.0, 'woodd')
    k.bx(1.69, 1.81, Y0 - 0.2, Y0 - 0.08, 1.62, 1.92, 'window')
    # saltbox roof: ridge along X at y = 0.6, front slope down over the porch, short back slope
    yr, zr = 0.6, 4.35
    for (ya, za) in ((-3.1, 2.22), (Y1 + 0.35, 3.05)):
        L = math.hypot(yr - ya, zr - za)
        ang = math.degrees(math.atan2(zr - za, yr - ya))
        cy, cz = (ya + yr) / 2, (za + zr) / 2
        sgn = 1 if ya < yr else -1
        k.bxr(0, cy, cz + 0.1, 6.0, L + 0.06, 0.16, 'roof', rot=(sgn * ang, 0, 0))
        for i in range(1, 6):   # shingle courses
            t = i / 6.0
            yy, zz = ya + (yr - ya) * t, za + (zr - za) * t
            k.bxr(0, yy, zz + 0.1 + 0.085, 5.96, 0.05, 0.02, 'roof2', rot=(sgn * ang, 0, 0), ink=False)
    k.bxr(0, yr, zr + 0.24, 6.1, 0.3, 0.14, 'roof2')
    for x in (X0, X1):   # gable ends
        sx = -1 if x < 0 else 1
        k.hullp([(x - sx * 0.02, Y0 - 0.0, H), (x - sx * 0.02, Y1, H), (x - sx * 0.02, yr, zr - 0.05), (x - sx * 0.2, Y0, H), (x - sx * 0.2, Y1, H), (x - sx * 0.2, yr, zr - 0.05)], 'cabin2')
    # chimney (east side, stone)
    for i in range(9):
        z = i * 0.6
        k.hullp([(2.72 + rnd.uniform(-0.03, 0.03), 0.25 + dy, z + dz) for dy in (0.0, 0.9) for dz in (0.0, 0.6)] +
                [(3.42 + rnd.uniform(-0.04, 0.04), 0.25 + dy, z + dz) for dy in (0.0, 0.9) for dz in (0.0, 0.6)], baldcol)
    k.bx(2.66, 3.48, 0.19, 1.21, 5.4, 5.55, 'rock2')
    k.col(2.7, 3.45, 0.25, 1.15, 0, 5.4)
    # sign board on the porch beam: RANGER STATION in dark blocks
    k.bx(-1.5, 1.5, -2.98, -2.92, 2.52, 2.98, 'sign')
    for i in range(12):
        if i == 6:
            continue
        x = -1.32 + i * 0.24
        k.bx(x, x + 0.16, -2.985, -2.979, 2.62, 2.88, 'ink' if i < 6 else 'roof2', ink=False)
    # firewood stack on the west wall, rain barrel at the east front corner, antenna
    for row in range(4):
        for i in range(5 - (row % 2)):
            y = -0.9 + i * 0.42 + (0.21 if row % 2 else 0)
            k.cyl(-3.05, y, 0.17 + row * 0.3, 0.15, 0.15, 0.7, 'wood' if (i + row) % 2 else 'wood3', seg=6, rot=(0, 90, 0))
            k.cyl(-2.69, y, 0.17 + row * 0.3, 0.1, 0.1, 0.006, 'heart', seg=6, rot=(0, 90, 0), ink=False)
    k.col(-3.45, -2.6, -1.2, 0.95, 0, 1.3)
    k.cyl(2.95, -0.75, 0.0, 0.34, 0.32, 0.95, 'wood2', seg=10)
    k.cyl(2.95, -0.75, 0.95, 0.3, 0.3, 0.012, 'water2', seg=10, ink=False)
    for z in (0.2, 0.75):
        k.cyl(2.95, -0.75, z, 0.352, 0.352, 0.05, 'gunmetal', seg=10)
    k.col(2.62, 3.28, -1.08, -0.42, 0, 0.95)
    k.cyl(-1.6, 1.9, 3.3, 0.04, 0.03, 3.2, 'gunmetal', seg=5)
    k.bx(-1.9, -1.3, 1.88, 1.92, 5.9, 5.94, 'gunmetal')
    k.col(X0 - 0.1, X1 + 0.1, Y0, Y1 + 0.1, 0, H + 0.2)
    k.finish('Landmark_Cabin', ao=ao)


def build_camp(k, ao):
    # tent (3 x 3, door -Y)
    rnd = random.Random(111)
    k.begin()
    hw, hl, hh = 1.05, 1.2, 1.55
    ang = math.degrees(math.atan2(hh, hw))
    L = math.hypot(hw, hh)
    for sx in (-1, 1):
        k.bxr(sx * hw / 2, 0, hh / 2, L + 0.02, 2 * hl - (0.03 if sx > 0 else 0), 0.05, 'canvas' if sx < 0 else 'canvas2', rot=(0, -sx * ang, 0))
    k.hullp([(-hw, hl - 0.02, 0.02), (hw, hl - 0.02, 0.02), (0, hl - 0.02, hh - 0.02), (-hw + 0.03, hl - 0.06, 0.02), (hw - 0.03, hl - 0.06, 0.02), (0, hl - 0.06, hh - 0.06)], 'canvas2')
    k.poly([(-hw * 0.82, -hl + 0.02, 0.02), (hw * 0.82, -hl + 0.02, 0.02), (0, -hl + 0.02, hh * 0.82)], 'ink', (0, -1, 0))
    for sx in (-1, 1):   # door flaps tied back
        k.hullp([(sx * hw * 0.85, -hl - 0.05, 0.02), (sx * hw * 0.35, -hl - 0.05, 0.02), (sx * 0.05, -hl - 0.03, hh * 0.9), (sx * hw * 0.62, -hl - 0.12, 0.5)], 'canvas')
    k.cyl(0, -hl - 0.15, 0, 0.03, 0.03, hh + 0.2, 'woodd', seg=5)
    k.cyl(0, hl + 0.15, 0, 0.03, 0.03, hh + 0.2, 'woodd', seg=5)
    k.cyl(0, -hl - 0.1, hh + 0.04, 0.03, 0.03, 2 * hl + 0.2, 'woodd', seg=5, rot=(-90, 0, 0))
    for (x, y) in ((-1.45, -1.45), (1.45, -1.45), (-1.45, 1.45), (1.45, 1.45)):
        k.beam((x * 0.55, y * 0.82, hh * 0.55), (x, y, 0.03), 0.02, 'rope', ink=False)
        k.cyl(x, y, -0.05, 0.03, 0.02, 0.2, 'woodd', seg=4)
    k.qz(-1.2, 1.2, -1.4, 1.4, 0.012, 1, 'canvas2')
    k.col(-hw, hw, -hl - 0.1, hl + 0.1, 0, hh * 0.8)
    k.finish('Tent', ao=ao)
    # campfire (3 x 3): stone ring, crossed logs, flames, two log benches, a pot on a tripod
    rnd = random.Random(112)
    k.begin()
    for i in range(9):
        a = i / 9 * 2 * math.pi
        rock(k, rnd, math.cos(a) * 0.55, math.sin(a) * 0.55, 0.15, 0.13, 0.2, z0=-0.03, n=5, col=baldcol)
    k.disc(0, 0, 0.02, 0.45, 'ink', n=10)
    for i in range(4):
        a = i * math.pi / 2 + 0.4
        k.beam((math.cos(a) * 0.42, math.sin(a) * 0.42, 0.06), (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.32), 0.09, 'woodd')
    k.cyl(0, 0, 0.1, 0.26, 0.0, 0.62, 'flame', seg=6)
    k.cyl(0.06, -0.04, 0.13, 0.15, 0.0, 0.5, 'flame2', seg=5)
    k.cyl(-0.12, 0.08, 0.116, 0.12, 0.0, 0.38, 'flame2', seg=5)
    for (sy, rot) in ((-1, 0), (1, 0)):
        k.cyl(-0.95, sy * 1.12, 0.24, 0.24, 0.24, 1.9, 'wood' if sy < 0 else 'wood2', seg=8, rot=(0, 90, 0))
        k.bx(-0.9, 0.9, sy * 1.12 - 0.17, sy * 1.12 + 0.17, 0.42, 0.48, 'heart')
        k.col(-0.95, 0.95, sy * 1.12 - 0.24, sy * 1.12 + 0.24, 0, 0.48)
    for i in range(3):   # tripod
        a = i * 2.09 + 0.5
        k.beam((math.cos(a) * 0.7, math.sin(a) * 0.7, 0.0), (0, 0, 1.25), 0.04, 'woodd')
    k.beam((0, 0, 1.22), (0, 0, 0.8), 0.015, 'gunmetal', ink=False)
    k.cyl(0, 0, 0.62, 0.17, 0.2, 0.2, 'gunmetal', seg=8)
    k.col(-0.62, 0.62, -0.62, 0.62, 0, 0.25)
    k.cyl(1.15, 0.0, 0, 0.26, 0.24, 0.42, 'wood2', seg=8)   # stump stool
    k.disc(1.15, 0.0, 0.424, 0.22, 'heart', n=8)
    k.col(0.92, 1.38, -0.23, 0.23, 0, 0.42)
    k.finish('Campfire', ao=ao)
    # woodpile (2 x 1)
    k.begin()
    for row in range(4):
        for i in range(5 - (row % 2)):
            x = -0.8 + i * 0.4 + (0.2 if row % 2 else 0)
            k.cyl(x, -0.32, 0.17 + row * 0.29, 0.145, 0.145, 0.64, 'wood' if (i + row) % 2 else 'wood3', seg=5, rot=(-90, 0, 0))
            k.cyl(x, -0.326, 0.17 + row * 0.29, 0.1, 0.1, 0.006, 'heart', seg=5, rot=(-90, 0, 0), ink=False)
    for x in (-0.98, 0.98):
        k.bx(x - 0.04, x + 0.04, -0.06, 0.06, 0, 1.3, 'woodd')
    k.bx(-1.0, 1.0, -0.45, 0.45, 1.25, 1.31, 'roof')
    k.col(-1.0, 1.0, -0.36, 0.36, 0, 1.25)
    k.finish('Woodpile', ao=ao)
    # signpost with arrow boards
    k.begin()
    k.cyl(0, 0, -0.1, 0.07, 0.06, 2.3, 'wood2', seg=6)
    for (z, a, L, c) in ((1.9, 20, 0.9, 'sign'), (1.6, 160, 0.8, 'sign'), (1.3, 70, 0.7, 'roof')):
        k.push(0, 0, a, z)
        k.bx(0.05, L, -0.03, 0.03, -0.1, 0.1, c)
        k.hullp([(L, -0.03, -0.1), (L, 0.03, -0.1), (L, -0.03, 0.1), (L, 0.03, 0.1), (L + 0.14, -0.03, 0.0), (L + 0.14, 0.03, 0.0)], c)
        k.bx(0.15, L - 0.05, -0.037, -0.031, -0.03, 0.03, 'ink' if c == 'sign' else 'sign', ink=False)
        k.pop()
    k.col(-0.1, 0.1, -0.1, 0.1, 0, 2.2)
    rock(k, random.Random(113), 0.1, 0.05, 0.22, 0.2, 0.18, z0=-0.03, col=baldcol)
    k.finish('Signpost', ao=ao)
    # lantern post
    k.begin()
    k.cyl(0, 0, -0.1, 0.07, 0.06, 2.2, 'wood2', seg=6)
    k.beam((0, 0, 2.0), (0.42, 0, 2.0), 0.06, 'woodd')
    k.bx(0.34, 0.5, -0.08, 0.08, 1.48, 1.84, 'window')
    k.bx(0.32, 0.52, -0.1, 0.1, 1.84, 1.92, 'gunmetal')
    k.bx(0.32, 0.52, -0.1, 0.1, 1.42, 1.48, 'gunmetal')
    k.beam((0.42, 0, 1.92), (0.42, 0, 1.98), 0.02, 'gunmetal', ink=False)
    k.col(-0.1, 0.1, -0.1, 0.1, 0, 2.1)
    k.finish('Lantern', ao=ao)
    # supply crate (also the weapon stand) and a barrel
    k.begin()
    k.bx(-0.4, 0.4, -0.3, 0.3, 0.0, 0.5, 'wood')
    for x in (-0.4, 0.4):
        k.bx(x - 0.03 if x < 0 else x - 0.0, x + 0.0 if x < 0 else x + 0.03, -0.32, 0.32, -0.0, 0.52, 'wood2')
    k.bx(-0.37, 0.37, -0.32, 0.32, 0.22, 0.28, 'wood2')
    k.bx(-0.12, 0.12, -0.306, -0.3, 0.32, 0.44, 'roof', ink=False)
    k.col(-0.4, 0.4, -0.3, 0.3, 0, 0.55)
    k.finish('Crate', ao=ao)
    k.begin()
    k.cyl(0, 0, 0, 0.3, 0.28, 0.9, 'wood2', seg=10)
    for z in (0.12, 0.72):
        k.cyl(0, 0, z, 0.312, 0.312, 0.05, 'gunmetal', seg=10)
    k.cyl(0, 0, 0.9, 0.26, 0.26, 0.01, 'wood', seg=10, ink=False)
    k.col(-0.28, 0.28, -0.28, 0.28, 0, 0.9)
    k.finish('Barrel', ao=ao)


# ================================================================ walkway level (layer 9)
def build_walkway(k, ao):
    # bridge cell: planks across, two stringers, rail post + handrail + rope on the front (-Y) edge
    k.begin()
    for i in range(3):
        x = -1 / 3 + i / 3
        k.bx(x - 0.152, x + 0.152, -0.5, 0.5, -0.07, 0.0, 'wood3' if i % 2 else 'wood')
    k.bx(-0.5, 0.5, -0.45, -0.31, -0.3, -0.07, 'woodd')
    k.bx(-0.05, 0.05, -0.49, -0.4, -0.25, 1.04, 'wood2')
    k.bx(-0.5, 0.5, -0.495, -0.405, 0.97, 1.05, 'wood3')
    k.bx(-0.5, 0.5, -0.465, -0.435, 0.5, 0.53, 'rope', ink=False)
    k.beam((-0.48, -0.45, 0.06), (-0.06, -0.45, 0.94), 0.02, 'rope', ink=False)
    k.wcol(-0.5, 0.5, -0.5, 0.5, -0.16, 0.0)
    k.col(-0.5, 0.5, -0.5, -0.42, 0.0, 1.05)
    k.finish('Bridge', ao=ao)
    # platform rail on a cell's north (+Y) edge, and an L for the north-west corner
    for name, corner in (('Rail', False), ('Rail_Corner', True)):
        k.begin()
        k.bx(-0.05, 0.05, 0.4, 0.49, 0.0, 1.04, 'wood2')
        k.bx(-0.5, 0.5, 0.405, 0.495, 0.97, 1.05, 'wood3')
        k.bx(-0.5, 0.5, 0.435, 0.465, 0.5, 0.53, 'rope', ink=False)
        k.col(-0.5, 0.5, 0.42, 0.5, 0.0, 1.05)
        if corner:
            k.bx(-0.5, -0.39, -0.05, 0.05, 0.0, 1.04, 'wood2')
            k.bx(-0.495, -0.405, -0.5, 0.395, 0.97, 1.05, 'wood3')
            k.bx(-0.465, -0.435, -0.5, 0.39, 0.5, 0.53, 'rope', ink=False)
            k.col(-0.5, -0.42, -0.5, 0.42, 0.0, 1.05)
        k.finish(name, ao=ao)
    # trestle pier under a bridge (1 x 2, base on the ground, cap under the bridge stringers at 8.7)
    rnd = random.Random(121)
    k.begin()
    top = DECK - 0.31
    for y in (-0.72, 0.72):
        k.cyl(0, y, -0.15, 0.17, 0.14, top + 0.15 - 0.16, 'wood2', seg=7)
        k.col(-0.16, 0.16, y - 0.16, y + 0.16, 0.0, top - 0.16)
        rock(k, rnd, 0.0, y, 0.3, 0.28, 0.3, z0=-0.08, col=baldcol)
    k.bx(-0.13, 0.13, -0.95, 0.95, top - 0.16, top, 'woodd')
    for (za, zb) in ((0.9, 4.2), (4.6, 7.9)):
        k.beam((0, -0.7, za), (0, 0.7, zb), 0.1, 'wood')
        k.beam((0.04, 0.7, za), (0.04, -0.7, zb), 0.1, 'wood3')
    k.finish('Pier', ao=ao)


# ================================================================ zone edges: cliffs, banks, corners, gate, trail
def shear(pts, a=0.013):
    """skew a wall module's shapes along x: copies of a module 2 m apart (whose shapes overlap a little) never share a
    plane"""
    return [(x, y + a * x, z + a * x) for (x, y, z) in pts]


def hillside(k, rnd, x0, x1, top, depth=8.0, rise=4.4, by=0.45, z0=0.0):
    """the ridge behind a wall module: a slope rising from the cliff top to a crest `rise` m higher, `depth` m back"""
    pts = []
    for x in (x0, x1):
        j = rnd.uniform(-0.25, 0.25)
        pts += [(x, by, z0), (x, by, top - 0.2), (x, by + depth * 0.45, top + rise * (0.62 + 0.04 * j)), (x, by + depth, top + rise + j), (x, by + depth, z0)]
    k.hullp(shear(pts), lambda f: 'moss' if f.normal.z > 0.75 else ('duff' if f.normal.z > 0.35 else 'soil'))


def cliff_module(k, rnd, w, H, style, idx=0):
    """wall module w m wide (x), front at y = -0.5: a rock face of offset boulders (or an earth bank with roots),
    a mossy lip, and the ridge slope behind it; lean (~300 tris / 2 m)"""
    hw = w / 2
    back = [0.3 + 0.0047 * idx]   # idx: modules overlap at run ends, so no two share a plane
    z00 = -0.05 - 0.013 * idx

    def by():   # every shape's back face on its own plane (never coplanar with a neighbour shape)
        back[0] += 0.023
        return back[0]
    if style == 'cliff':   # staggered columns of boulders: no joint runs straight across the module
        n = 2 if w >= 2 else 1
        tops = []
        for col in range(n):
            xa0, xb0 = -hw + col * w / n - 0.1, -hw + (col + 1) * w / n + 0.1
            z = z00
            first = True
            while z < H - 0.4:
                hgt = min(H - z, rnd.uniform(1.2, 2.2) if first else rnd.uniform(1.8, 2.9))
                first = False
                xa, xb = xa0 + rnd.uniform(-0.1, 0.15), xb0 - rnd.uniform(-0.1, 0.15)
                xa, xb = max(xa, -hw + 0.012), min(xb, hw - 0.012)   # never into the next module (copies would share planes)
                dy = rnd.uniform(-0.16, 0.1)
                yb = by()
                zb = z - 0.006 * col
                zt = z + hgt * rnd.uniform(1.0, 1.12)
                k.hullp(shear([(xa + rnd.uniform(0, 0.12), -0.5 + dy, zb), (xb - rnd.uniform(0, 0.12), -0.5 + dy + rnd.uniform(-0.05, 0.05), zb),
                         ((xa + xb) / 2 + rnd.uniform(-0.15, 0.15), -0.62 + dy, z + hgt * rnd.uniform(0.35, 0.65)),
                         (xa + rnd.uniform(0.05, 0.3), -0.47 + dy, zt), (xb - rnd.uniform(0.05, 0.3), -0.45 + dy, zt - rnd.uniform(0, 0.25)),
                         (xa, yb, zb), (xb, yb, zb), (xa + 0.1, yb, zt), (xb - 0.1, yb, zt)]), rockcol)
                z += hgt * rnd.uniform(0.86, 0.96)
            tops.append(z)
        top = max(tops) + 0.1
    else:   # dark earth face held by a cascade of old roots, a rock at the foot
        top = H
        yb = by()
        k.hullp(shear([(x, y, zz) for x in (-hw + 0.016, hw - 0.016) for (y, zz) in ((-0.5, z00), (-0.46, H * 0.5), (-0.36, H * 0.9), (-0.1, H + 0.12), (yb, z00), (yb, H + 0.12))]),
                lambda f: 'moss' if f.normal.z > 0.75 else ('soil' if f.normal.z < 0.3 else 'duff'))
        for i in range(max(1, int(w))):   # roots: thick at the lip, wandering down, splitting and thinning
            p0 = (-hw + (i + 0.5) * w / max(1, int(w)) + rnd.uniform(-0.3, 0.3), -0.48, H + 0.05)
            th = 0.2
            for seg in range(2):
                p1 = (p0[0] + rnd.uniform(-0.7, 0.7), -0.56 - 0.02 * seg, p0[2] - rnd.uniform(1.6, 2.6))
                k.beam(p0, p1, th, 'bark' if seg == 0 else 'bark2')
                if seg < 1:
                    q = (p1[0] + rnd.choice((-1, 1)) * rnd.uniform(0.4, 0.8), -0.55, p1[2] - rnd.uniform(0.6, 1.0))
                    k.beam(p1, q, th * 0.5, 'bark2')
                p0, th = p1, th * 0.7
        mx, mz, mw = rnd.uniform(-hw * 0.4, hw * 0.4), H * rnd.uniform(0.2, 0.6), rnd.uniform(0.25, 0.45) * w
        k.hullp([(mx - mw, -0.53, mz), (mx + mw * 0.8, -0.53, mz + 0.1), (mx - mw * 0.6, -0.53, mz + 0.45), (mx + mw * 0.5, -0.53, mz + 0.6), (mx, -0.6, mz + 0.3),
                 (mx - mw, -0.42, mz), (mx + mw * 0.8, -0.42, mz + 0.1), (mx, -0.42, mz + 0.6)], lambda f: 'moss2' if f.normal.z > 0.5 else 'moss')
        rock(k, rnd, rnd.uniform(-hw * 0.6, hw * 0.6), -0.5, rnd.uniform(0.35, 0.5) * min(1, w), 0.3, rnd.uniform(0.6, 1.0), z0=-0.1, n=6)
    # mossy lip, the ridge slope behind, a bush or fern on the lip
    yb = by()
    k.hullp(shear([(x, y, zz) for x in (-hw + 0.021, hw - 0.021) for (y, zz) in ((-0.48, top - 0.25), (-0.52, top + 0.05), (-0.2, top + 0.35), (yb, top + 0.25), (yb, top - 0.3))]),
            lambda f: 'moss2' if f.normal.z > 0.8 else ('moss' if f.normal.z > 0.3 else 'mossd'))
    if w >= 2:   # a bush on the ridge crest breaks the skyline
        blob(k, rnd, rnd.uniform(-0.4, 0.4), 6.6 + 0.11 * idx, top + 4.2, 0.9, 0.9, 1.3, leafcol('leaf3', 'leaf', 'leaf2'), n=4)
    hillside(k, rnd, -hw + 0.012, hw - 0.012, top, rise=rnd.uniform(3.8, 5.0), depth=8.0 + 0.11 * idx, by=0.45 + 0.013 * idx, z0=-0.1 - 0.0043 * idx)
    blob(k, rnd, rnd.uniform(-0.3, 0.3) * w, 0.3, top + 0.15, 0.6 * min(w, 1.5), 0.5, rnd.uniform(0.8, 1.3), leafcol('leaf4', 'leaf3', 'leaf'), n=4)
    # a moss drape over the lip (on about half the modules)
    if rnd.random() < 0.5:
        x = rnd.uniform(-hw * 0.6, hw * 0.6)
        L = rnd.uniform(0.7, 1.6)
        dw = rnd.uniform(0.25, 0.45) * min(w, 1.5)
        k.hullp([(x - dw, -0.6, top - 0.05), (x + dw * 0.8, -0.6, top - 0.1), (x - dw * 0.9, -0.66, top - L * 0.55), (x + dw * 0.7, -0.66, top - L * 0.7),
                 (x - dw * 0.3, -0.64, top - L), (x + dw * 0.2, -0.64, top - L * 0.9), (x - dw, -0.5, top - 0.05), (x + dw * 0.8, -0.5, top - 0.1)],
                lambda f: 'mossd' if f.normal.z < -0.3 else 'moss')
    return top


def build_edges(k, ao):
    for idx, (name, w, H, seed, style) in enumerate((('Cliff_A', 2, 6.6, 131, 'cliff'), ('Cliff_B', 2, 7.4, 132, 'cliff'), ('Cliff_1', 1, 6.9, 133, 'cliff'),
                                                    ('Roots_A', 2, 6.4, 134, 'roots'), ('Roots_B', 2, 6.9, 135, 'roots'), ('Roots_1', 1, 6.6, 136, 'roots'))):
        rnd = random.Random(seed)
        k.begin()
        top = cliff_module(k, rnd, w, H, style, idx)
        k.finish(name, ao=ao)
    for name, seed in (('Corner_A', 137), ('Corner_B', 138)):
        rnd = random.Random(seed)
        k.begin()
        z = 0.0
        while z < 6.2:
            hgt = rnd.uniform(1.5, 2.2)
            rr = rnd.uniform(0.85, 1.05)
            k.hullp(rock_pts(rnd, (0.15, 0.15), rr, rr, hgt + 0.3, z0=z, n=7, top=2), rockcol)
            z += hgt
        blob(k, rnd, 0.2, 0.2, z, 0.9, 0.9, 1.1, leafcol('leaf4', 'leaf3', 'leaf'), n=6)
        fern(k, rnd, -0.6, -0.6, 0.8, n=5)
        k.hullp([(x, y, zz) for (x, y) in ((0.4, 0.4), (8.6, 0.4), (0.4, 8.6), (8.6, 8.6)) for zz in (0.0,)] +
                [(0.4, 0.4, 6.4), (8.6, 0.5, 11.0), (0.5, 8.6, 11.0), (8.6, 8.6, 11.4), (4.2, 0.45, 9.0), (0.45, 4.2, 9.0)],
                lambda f: 'moss' if f.normal.z > 0.75 else ('duff' if f.normal.z > 0.35 else 'soil'))
        k.finish(name, ao=ao)


def build_gate(k, ao):
    rnd = random.Random(141)
    k.begin()
    for sx in (-1, 1):
        k.cyl(sx * 1.82, 0, -0.1, 0.34, 0.3, 4.6, 'bark', seg=9)
        z = 0.0
        while z < 6.0:   # rock jambs blending into the cliffs (cells beside the gate)
            hgt = rnd.uniform(1.6, 2.2)
            k.hullp(rock_pts(rnd, (sx * 2.12, 0.1), 0.52, 0.6, hgt + 0.25, z0=z, n=6, top=2), rockcol)
            z += hgt
        fern(k, rnd, sx * 2.1, -0.75, 0.8, n=5)
        blob(k, rnd, sx * 2.1, 0.1, z, 0.7, 0.7, 0.9, leafcol('leaf4', 'leaf3', 'leaf'), n=5)
    k.cyl(-2.45, 0, 4.0, 0.3, 0.28, 4.9, 'bark3', seg=9, rot=(0, 90, 0))
    # sign under the lintel: amber / ink chevron band, rope hangers
    k.bx(-1.45, 1.45, -0.06, 0.06, 3.22, 3.62, 'wood2')
    for fy in (-1, 1):
        for i in range(10):
            k.bx(-1.4 + i * 0.28, -1.4 + (i + 1) * 0.28, fy * 0.06 - (0.008 if fy < 0 else 0), fy * 0.06 + (0.008 if fy > 0 else 0), 3.27, 3.57, 'amber' if i % 2 else 'ink', ink=False)
    for x in (-1.2, 1.2):
        k.beam((x, 0, 3.62), (x, 0, 3.72), 0.03, 'rope', ink=False)
    for sx in (-1, 1):
        k.bx(sx * 1.82 - 0.12, sx * 1.82 + 0.12, -0.42, -0.3, 2.4, 2.75, 'window')
        k.bx(sx * 1.82 - 0.14, sx * 1.82 + 0.14, -0.44, -0.28, 2.75, 2.82, 'gunmetal')
    k.finish('GateFrame', ao=ao)
    # shutter: a palisade of logs with the amber / ink band at the foot
    k.begin()
    Hs, n = 3.05, 10
    for i in range(n):
        x = -1.5 + (i + 0.5) * 3.0 / n
        k.cyl(x, 0, 0.5, 0.145, 0.14, Hs - 0.5 - 0.05 * (i % 2), 'wood' if i % 2 else 'wood2', seg=6, ink=False)
    for z in (1.2, 2.5):
        k.bx(-1.5, 1.5, -0.2, -0.13, z, z + 0.16, 'woodd', ink=False)
    for i in range(8):
        k.bx(-1.5 + i * 3 / 8, -1.5 + (i + 1) * 3 / 8, -0.08, 0.08, 0.0, 0.5, 'ink' if i % 2 else 'amber', ink=False)
    obj = k.finish('GateShutter', ao=False)
    from kit_base import shutter_hull
    shutter_hull(k.pal, obj)
    k.tris[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # trail banks (1 m along Y, inner face +X): mossy rock and earth with ferns on top
    for name, seed in (('TrailWall', 151), ('TrailWall_B', 152), ('TrailWall_C', 153)):
        rnd = random.Random(seed)
        k.begin()
        k.hullp([(x, y, z) for y in (-0.498, 0.498) for (x, z) in ((0.28, 0.0), (0.2, 1.3), (0.05, 2.45), (-0.4, 2.5), (-0.4, 0.0))],
                lambda f: 'moss' if f.normal.z > 0.6 else ('duff' if f.normal.x > 0.2 and f.calc_center_median().z > 1.2 else 'soil'))
        if name == 'TrailWall':
            rock(k, rnd, 0.22, 0.0, 0.32, 0.45, 1.1, z0=-0.1)
        elif name == 'TrailWall_B':
            k.cyl(0.0, 0.0, -0.1, 0.42, 0.36, 3.2, 'bark', seg=8)
            k.disc(0.0, 0.0, 3.1 + 0.004, 0.33, 'heart', n=8)
        else:
            rock(k, rnd, 0.2, -0.2, 0.28, 0.3, 0.6, z0=-0.09)
            k.beam((0.05, 0.1, 2.0), (0.38, 0.25, 0.6), 0.06, 'bark2', ink=False)
        fern(k, rnd, 0.1, 0.0, 0.8, z0=2.45, n=5)
        fern(k, rnd, 0.48, 0.1, 0.55, n=4)
        j = rnd.uniform(-0.3, 0.3)
        k.hullp([(x, y, z) for y in (-0.492, 0.492) for (x, z) in ((-0.35, 0.0), (-0.35, 2.4), (-3.0, 5.6 + j), (-7.5, 10.5 + j), (-7.5, 0.0))],
                lambda f: 'moss' if f.normal.z > 0.75 else ('duff' if f.normal.z > 0.35 else 'soil'))
        k.finish(name, ao=ao)
    # hatch (exit): a timber trapdoor in a log ring
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.2, 0.12, 'wood2', seg=16)
    k.cyl(0, 0, 0.12, 0.95, 0.95, 0.02, 'teal', seg=16, ink=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        k.cyl(math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12, 0.07, 0.07, 0.05, 'amber', seg=6)
    k.finish('Hatch', ao=ao)


# ================================================================ backdrop (outside the zones; placed by the theme)
def build_backdrop(k):
    for name, seed, s, h in (('Backdrop_Trunk_A', 161, 1.0, 52), ('Backdrop_Trunk_B', 162, 1.3, 58), ('Backdrop_Trunk_C', 163, 0.75, 44)):
        rnd = random.Random(seed)
        k.begin()
        r0 = 1.6 * s
        lathe(k, [(-0.5, r0 * 1.3), (1.2, r0 * 1.0), (h * 0.45, r0 * 0.72), (h * 0.8, r0 * 0.38)], 8,
              lambda i, j: 'farbark' if i % 2 else ('bark' if j < 2 else 'bark2'), top=h * 0.9)
        for t in range(3 if name != 'Backdrop_Trunk_C' else 0):
            z = h * (0.52 + 0.13 * t)
            L = (5.5 - t) * s
            a = t * 2.3 + rnd.uniform(-0.3, 0.3)
            blob(k, rnd, math.cos(a) * L * 0.5, math.sin(a) * L * 0.5, z, L * 0.6, L * 0.5, 2.4 * s, leafcol('far', 'far2', 'far2'), n=4)
        k.cyl(0, 0, h * 0.62, 3.2 * s, 0, h * 0.38, 'far2', seg=6)
        k.finish(name)


def build_kit_grove(ao):
    pal = Palette(FAM)
    k = GKit(pal, PFX, HULL_T)
    build_redwood(k, ao, 'Landmark_Redwood_A', 1)
    build_redwood(k, ao, 'Landmark_Redwood_B', 2)
    build_giant(k, ao, 'Landmark_Giant_A', 3, 1.0)
    build_giant(k, ao, 'Landmark_Giant_B', 4, 0.88)
    build_young(k, ao)
    build_snag_stump(k, ao)
    build_logs(k, ao)
    build_rocks(k, ao)
    build_plants(k, ao)
    build_water(k, ao)
    build_cabin(k, ao)
    build_camp(k, ao)
    build_walkway(k, ao)
    build_edges(k, ao)
    build_gate(k, ao)
    build_backdrop(k)
    k.report(FAM)
    export(FAM)


FAMILY = 'kit-grove'
BUILD = build_kit_grove
