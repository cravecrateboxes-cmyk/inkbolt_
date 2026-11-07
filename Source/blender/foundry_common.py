"""Shared bits of kit-foundry (Titan Foundry): palette, heights, the FK kit (Kit + walkable collision boxes) and the
modelling helpers the walls, robots and giants use. Not an asset family itself (no fam_ prefix); fam_kit_foundry.py
builds the GLB.

Conventions (src/data/themes.js, kit_base.py): 1 m = 1 ASCII cell; a piece's origin is the centre of its cell /
footprint at floor level; Blender Z-up; one-sided pieces face Blender -Y (game +Z, south, toward the zone entry).
Shapes marked ink=False get no outline shell (painted detail, glows, thin trims).
"""
import math
import random
import re

import bpy  # noqa: F401  (must load before bmesh/mathutils)
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, srt

FAM = 'kit-foundry'
PFX = 'KIT_FOUNDRY_'
ib_lib.GLB[FAM] = 'fps-kit-foundry.glb'
ib_lib.CFG[FAM] = (0.015, 0.02)
HULL_T = 0.02
CEIL = 30.0          # hall ceiling
WALL_H = 30.4        # wall modules reach past it
ROOF = 4.2           # service corridor (trail) ceiling
DECK = 6.0           # gantry walkway level (zone 2)

ib_lib.PALETTES[FAM] = BASE + [
    # structure: indigo-gunmetal plate, slate concrete, a dark roof
    ('slate', '#3D4459'), ('slate2', '#30364A'), ('slateL', '#566079'), ('conc', '#6E7282'),
    ('conc2', '#5A5E6D'), ('ceil', '#2C3040'), ('pit', '#30323C'), ('oil', '#474A56'),
    # war paint
    ('crimson', '#C8303A'), ('crimson2', '#8A1E2A'), ('hazard', '#F2B530'), ('hazard2', '#C48A18'),
    ('bone', '#E6DFCB'), ('bone2', '#C3BAA2'), ('olive', '#6F7A50'), ('olive2', '#535C3B'),
    ('sand', '#C9A66A'), ('sand2', '#9B7D4B'), ('paintW', '#E4E1D6'), ('banner2', '#1E1A24'),
    # metal
    ('steel', '#AEB5C2'), ('steel2', '#7D8494'), ('steelDark', '#262934'), ('gun', '#4B5163'),
    ('gun2', '#373B4A'), ('gunL', '#6E7689'), ('chrome', '#D9E0E8'), ('copper', '#C47B3B'),
    # light and heat
    ('cyan', '#55E3F2'), ('cyanL', '#D2FBFF'), ('cyanD', '#1F8FA6'), ('ember', '#FF7A2C'),
    ('emberL', '#FFD07A'), ('spark', '#FFEC8E'), ('lamp', '#F6FAFF'), ('lampW', '#FFE3A0'),
    ('alarm', '#FF3D33'), ('glass', '#7EB6D6'), ('screen', '#7FE0C8'), ('violet', '#7C64D8'),
    # cables, rubber, floor
    ('cable', '#24222B'), ('cableR', '#A8262F'), ('hose', '#3A5FA8'), ('rubber', '#2C2A31'),
    ('pool', '#6C7080'), ('pool2', '#7A7E8D'), ('floorP', '#646878'), ('floorP2', '#585C6B'),
    ('wood', '#A07A4E'), ('wood2', '#7A5A36'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# floor decal heights: every decal class at its own height so overlapping decals never share a plane
# (8 mm apart and clear of the engine's floor lines at 8 - 15.5 mm; details within a class stay < 8 mm above it)
Z = {'pool': 0.019, 'decal': 0.031, 'lane': 0.041, 'hazard': 0.051, 'bay': 0.061, 'bay2': 0.067, 'rail': 0.077,
     'line': 0.087, 'cell': 0.097, 'pad': 0.107, 'hatch': 0.117, 'sten': 0.124, 'door': 0.131}


class FK(Kit):
    """Kit + walkable collision boxes (<Piece>_WCOL<n>: decks, stair steps the robots may walk on)."""

    def begin(self, rot=0):
        super().begin(rot)
        self.walk = set()
        return self

    def colw(self, x0, x1, y0, y1, z0, z1):
        self.walk.add(len(self.cols))
        self.cols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        obj = super().finish(name, bevel, ao)
        for ch in obj.children:
            m = re.match(r'(.*)_COL(\d+)$', ch.name)
            if m and int(m.group(2)) in self.walk:
                ch.name = '%s_WCOL%s' % (m.group(1), m.group(2))
        return obj


# ================================================================ shapes
def ring4(w, d, z, ox=0.0, oy=0.0, ch=0.0):
    """Rectangle (half sizes w, d) at height z, corners chamfered by ch (8 points) or square (4 points)."""
    if ch <= 0:
        return [(ox - w, oy - d, z), (ox + w, oy - d, z), (ox + w, oy + d, z), (ox - w, oy + d, z)]
    c = min(ch, w * 0.9, d * 0.9)
    return [(ox - w + c, oy - d, z), (ox + w - c, oy - d, z), (ox + w, oy - d + c, z), (ox + w, oy + d - c, z),
            (ox + w - c, oy + d, z), (ox - w + c, oy + d, z), (ox - w, oy + d - c, z), (ox - w, oy - d + c, z)]


def slab(k, cx, cy, z0, z1, bw, bd, tw, td, c, ch=0.0, dx=0.0, dy=0.0, ink=True):
    """Tapered armour block: bottom half sizes (bw, bd) at z0, top (tw, td) at z1 shifted by (dx, dy)."""
    return k.hullp(ring4(bw, bd, z0, cx, cy, ch) + ring4(tw, td, z1, cx + dx, cy + dy, ch), c, ink=ink)


def slab3(k, cx, cy, zs, c, ch=0.0, ink=True):
    """Armour hull through several stations zs = [(z, w, d, ox, oy), ...] (convex)."""
    pts = []
    for (z, w, d, ox, oy) in zs:
        pts += ring4(w, d, z, cx + ox, cy + oy, ch)
    return k.hullp(pts, c, ink=ink)


def frame_at(a, b):
    a, b = Vector(a), Vector(b)
    ax = (b - a)
    L = ax.length
    ax.normalize()
    side = Vector((1, 0, 0))
    if abs(ax.dot(side)) > 0.9:
        side = Vector((0, 1, 0))
    side = (side - ax * side.dot(ax)).normalized()
    up = ax.cross(side).normalized()
    return a, b, ax, side, up, L


def oslab(k, a, b, wa, da, wb, db, c, ch=0.0, ink=True, bias=None):
    """Tapered block from point a to point b (cross-section half sizes wa x da at a, wb x db at b; w along the side
    axis (world X where possible), d across it). bias shifts the b end's section along (side, up)."""
    a, b, ax, side, up, L = frame_at(a, b)
    pts = []
    for (p, w, d, o) in ((a, wa, da, (0, 0)), (b, wb, db, bias or (0, 0))):
        for (u, v, _) in ring4(w, d, 0, o[0], o[1], ch):
            q = p + side * u + up * v
            pts.append((q.x, q.y, q.z))
    return k.hullp(pts, c, ink=ink)


def tube(k, a, b, r, c, seg=8, ink=True, r2=None):
    """Cylinder between two points (convex hull of two rings)."""
    a, b, ax, side, up, L = frame_at(a, b)
    r2 = r if r2 is None else r2
    pts = []
    for (p, rr) in ((a, r), (b, r2)):
        for i in range(seg):
            t = i / seg * 2 * math.pi + math.pi / seg
            q = p + side * math.cos(t) * rr + up * math.sin(t) * rr
            pts.append((q.x, q.y, q.z))
    return k.hullp(pts, c, ink=ink)


def drumx(k, xc, y, z, r, L, c, seg=10, ink=True):
    k.cyl(xc - L / 2, y, z, r, r, L, c, seg=seg, rot=(0, 90, 0), ink=ink)


def drumy(k, x, yc, z, r, L, c, seg=10, ink=True):
    k.cyl(x, yc - L / 2, z, r, r, L, c, seg=seg, rot=(-90, 0, 0), ink=ink)


def stencil_digit(k, d, x, z, w, h, y, s, c='ink', dy=0.003):
    """A blocky stencil digit (0-9) on a -Y/+Y facing plane: up to 7 bars, each its own quad. On a +Y face the glyph is
    mirrored so it reads right for someone looking at that face (their right hand is -X)."""
    t = w * 0.24
    m0, m1 = z + h / 2 - t / 2, z + h / 2 + t / 2
    seg = {'a': (x, x + w, z + h - t, z + h), 'g': (x, x + w, m0, m1), 'd': (x, x + w, z, z + t),
           'f': (x, x + t, m1, z + h - t), 'b': (x + w - t, x + w, m1, z + h - t),
           'e': (x, x + t, z + t, m0), 'c': (x + w - t, x + w, z + t, m0)}
    on = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abfgcd'}[d]
    for i, key in enumerate(on):
        x0, x1, z0, z1 = seg[key]
        if s > 0:
            x0, x1 = 2 * x + w - x1, 2 * x + w - x0
        k.qy(x0, x1, z0, z1, y + s * dy * (1 + (i % 2)), s, c)


def stencil_num(k, digits, x, z, w, h, gap, y, s, c='ink', dy=0.003):
    """Several stencil digits on a -Y/+Y face, laid out left to right as seen by someone looking at that face."""
    n = len(digits)
    for i, d in enumerate(digits):
        j = i if s < 0 else n - 1 - i
        stencil_digit(k, d, x + j * (w + gap), z, w, h, y, s, c=c, dy=dy)


def stencil_x(k, d, y, z, w, h, x, s, c='ink', dx=0.003):
    """Stencil digit on a -X/+X facing plane (y runs along the face; mirrored on a -X face, whose viewer's right is -Y)."""
    t = w * 0.24
    m0, m1 = z + h / 2 - t / 2, z + h / 2 + t / 2
    seg = {'a': (y, y + w, z + h - t, z + h), 'g': (y, y + w, m0, m1), 'd': (y, y + w, z, z + t),
           'f': (y, y + t, m1, z + h - t), 'b': (y + w - t, y + w, m1, z + h - t),
           'e': (y, y + t, z + t, m0), 'c': (y + w - t, y + w, z + t, m0)}
    on = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abfgcd'}[d]
    for i, key in enumerate(on):
        y0, y1, z0, z1 = seg[key]
        if s < 0:
            y0, y1 = 2 * y + w - y1, 2 * y + w - y0
        k.qx(y0, y1, z0, z1, x + s * dx * (1 + (i % 2)), s, c)


def floor_digit(k, d, x, y, w, h, z, c='paintW'):
    """Stencil digit painted on the floor (reads from the south: digit top toward +Y)."""
    t = w * 0.24
    m0, m1 = y + h / 2 - t / 2, y + h / 2 + t / 2
    seg = {'a': (x, x + w, y + h - t, y + h), 'g': (x, x + w, m0, m1), 'd': (x, x + w, y, y + t),
           'f': (x, x + t, m1, y + h - t), 'b': (x + w - t, x + w, m1, y + h - t),
           'e': (x, x + t, y + t, m0), 'c': (x + w - t, x + w, y + t, m0)}
    on = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abfgcd'}[d]
    for i, key in enumerate(on):
        x0, x1, y0, y1 = seg[key]
        k.qz(x0, x1, -y1, -y0, z + 0.003 * (i % 2), 1, c)   # flipped: the digit reads upright from the south


def chevrons_y(k, x0, x1, z0, z1, y, s, n, ca='hazard', cb='ink'):
    """Upward chevron band on a -Y/+Y facing plane."""
    k.qy(x0, x1, z0, z1, y, s, ca)
    w = (x1 - x0) / n
    h = z1 - z0
    d = s * 0.003
    for i in range(n):
        a = x0 + i * w
        m = a + w / 2
        k.poly([(a + w * 0.1, y + d, z0 + h * 0.15), (m, y + d, z0 + h * 0.55), (a + w * 0.9, y + d, z0 + h * 0.15),
                (a + w * 0.9, y + d, z0 + h * 0.45), (m, y + d, z0 + h * 0.85), (a + w * 0.1, y + d, z0 + h * 0.45)], cb, (0, s, 0))


def spark_star(k, x, y, z, r, s=-1, c='spark', n=8):
    """Flat welding spark star facing -Y (s=-1) or +Y."""
    pts = []
    for i in range(2 * n):
        a = i / (2 * n) * 2 * math.pi
        rr = r if i % 2 == 0 else r * 0.36
        pts.append((x + math.cos(a) * rr, y, z + math.sin(a) * rr))
    k.poly(pts, c, (0, s, 0))


def spark_spray(k, x, y, z, r, s=-1, seed=1):
    """A weld point: a hot core star and a fan of spark streaks falling away."""
    rnd = random.Random(seed)
    spark_star(k, x, y, z, r, s=s)
    spark_star(k, x, y + s * 0.03, z, r * 0.45, s=s, c='white', n=6)
    for i in range(5):
        dd = s * (0.005 + 0.004 * i)
        a = math.radians(-160 + i * 35 + rnd.uniform(-8, 8))
        L = r * rnd.uniform(1.6, 2.6)
        ex, ez = x + math.cos(a) * L, z + math.sin(a) * L
        nx, nz = -math.sin(a) * 0.02, math.cos(a) * 0.02
        k.poly([(x + math.cos(a) * r * 0.5 - nx, y + dd, z + math.sin(a) * r * 0.5 - nz),
                (x + math.cos(a) * r * 0.5 + nx, y + dd, z + math.sin(a) * r * 0.5 + nz),
                (ex, y + dd, ez)], 'emberL', (0, s, 0))


def pool_disc(k, x, y, z, r, seed, sx=1.0, sy=1.0, c1='pool', c2='pool2'):
    rnd = random.Random(seed)
    k.disc(x, y, z, r, c1, n=14, rnd=rnd, jag=0.05, sx=sx, sy=sy)
    k.disc(x, y, z + 0.004, r * 0.55, c2, n=10, rnd=rnd, jag=0.06, sx=sx, sy=sy)


def beacon(k, x, y, z, c='alarm', r=0.16, h=0.3):
    """Warning beacon: a dark base and a glowing dome (outlined)."""
    k.cyl(x, y, z, r * 1.15, r * 1.15, 0.1, 'steelDark', seg=8)
    k.cyl(x, y, z + 0.1, r, r * 0.7, h, c, seg=8)


def floodlamp(k, x, y, z, w=0.7, h=0.45, s=-1, c='lamp'):
    """A box floodlight facing -Y (s=-1) / +Y with a glowing lens."""
    y0, y1 = srt(y, y - s * 0.4)
    k.bx(x - w / 2, x + w / 2, y0, y1, z - h / 2, z + h / 2, 'steelDark')
    k.qy(x - w / 2 + 0.06, x + w / 2 - 0.06, z - h / 2 + 0.06, z + h / 2 - 0.06, y + s * 0.003, s, c)


def downlamp(k, x, y, z, r=0.6, c='lamp'):
    """Round high-bay floodlight hanging at z (lens facing down)."""
    k.cyl(x, y, z, r, r * 0.45, 0.55, 'steelDark', seg=10)
    k.cyl(x, y, z - 0.004, r * 0.9, r * 0.9, 0.002, c, seg=10, ink=False)


def cable(k, a, b, sag, t, c='cable', n=6, ink=False):
    """Sagging cable from a to b (a chain of n beams)."""
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        f = i / n
        p = a.lerp(b, f)
        p.z -= sag * 4 * f * (1 - f)
        pts.append(p)
    for i in range(n):
        k.beam(tuple(pts[i]), tuple(pts[i + 1]), t, c, ink=ink)


def guard_rail(k, x0, x1, y, z, h=1.1, post=1.5, c='hazard', axis='x', cols=True, kick=True):
    """Guard rail along X (axis 'x', at y) or along Y (axis 'y', at x = y argument): posts, top and mid rails, kick
    plate; collision box 0.12 thick up to h. Rails along Y are sized a few mm apart from rails along X, so where two
    rails meet at a corner none of their faces share a plane."""
    L = x1 - x0
    n = max(1, int(round(L / post)))
    # (post, top bar, mid bar, kick) half thicknesses and a height shift: x rails / y rails
    pw, tb, mb, kb, dz = (0.045, 0.05, 0.035, 0.015, 0.0) if axis == 'x' else (0.06, 0.038, 0.026, 0.021, 0.016)

    def box(u0, u1, v0, v1, z0, z1, col, ink=True):
        if axis == 'x':
            k.bx(u0, u1, v0, v1, z0, z1, col, ink=ink)
        else:
            k.bx(v0, v1, u0, u1, z0, z1, col, ink=ink)
    for i in range(n + 1):
        u = x0 + L * i / n
        box(u - pw, u + pw, y - pw, y + pw, z + dz * 0.75, z + h + dz * 1.9, c)
    for zz, tt in ((h - 0.06 + dz, tb), (h * 0.5 + dz, mb)):
        box(x0, x1, y - tt, y + tt, z + zz, z + zz + 0.07, c)
    if kick:
        box(x0, x1, y - kb, y + kb, z + 0.003 + dz * 0.19, z + 0.16 + dz * 0.38, 'steelDark', ink=False)
    if cols:
        if axis == 'x':
            k.col(x0, x1, y - 0.06, y + 0.06, z, z + h)
        else:
            k.col(y - 0.06, y + 0.06, x0, x1, z, z + h)


def robot_arm(k, x, y, deg, z=0.0, reach=1.0, tool='claw', s=1.0, c='crimson', c2='gun'):
    """Six-axis industrial arm (base, turret, upper arm, forearm, wrist, tool), reaching along local -Y."""
    k.push(x, y, deg, z, s=s)
    k.cyl(0, 0, 0, 0.46, 0.46, 0.16, 'steelDark', seg=8)
    k.cyl(0, 0, 0.16, 0.34, 0.3, 0.44, c2, seg=8)
    k.bx(-0.24, 0.24, -0.22, 0.22, 0.6, 0.9, c)
    sh = Vector((0, 0, 0.78))
    el = Vector((0, -0.5 * reach, 1.85))
    wr = Vector((0, -1.3 * reach, 1.45))
    oslab(k, sh, el, 0.17, 0.14, 0.13, 0.11, c)
    drumx(k, 0.0, el.y, el.z, 0.2, 0.42, c2, seg=8)
    oslab(k, el, wr, 0.12, 0.1, 0.09, 0.08, c)
    drumx(k, 0.0, wr.y, wr.z, 0.11, 0.26, 'steelDark', seg=8)
    k.beam(tuple(wr), tuple(wr + Vector((0, -0.1, -0.3))), 0.1, 'steel2')
    tip = wr + Vector((0, -0.1, -0.32))
    if tool == 'claw':
        for sx in (-1, 1):
            k.bx(tip.x + sx * 0.07 - 0.025, tip.x + sx * 0.07 + 0.025, tip.y - 0.03, tip.y + 0.03, tip.z - 0.24, tip.z, 'steelDark', ink=False)
    else:   # welder: torch + spark
        k.beam(tuple(tip), tuple(tip + Vector((0, -0.05, -0.2))), 0.045, 'steelDark', ink=False)
        p = tip + Vector((0, -0.05, -0.25))
        spark_spray(k, p.x, p.y - 0.06, p.z, 0.17, seed=int(abs(x * 7 + y * 13)) + 3)
    k.beam((0.29, 0.05, 0.62), (0.27, -0.38, 1.7), 0.045, 'cableR', ink=False)
    k.pop()


def rivet_row(k, x0, x1, z, y, s, n, c='steelDark', r=0.03):
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        k.qy(x - r, x + r, z - r, z + r, y, s, c)


def stairs(k, x0, x1, ya, yb, z0, z1, n, c='steel2', tread='hazard', rail=True, side_cols=True):
    """Straight steel stair, rising from y = ya (bottom, z0) to y = yb (top, z1) in n steps; the steps are walkable
    collision blocks (WCOL, solid to the floor like the mall escalator), side stringers and hand rails collide."""
    sg = 1 if yb > ya else -1
    run = (yb - ya) / n
    rise = (z1 - z0) / n
    for i in range(n):
        a, b = srt(ya + run * i, ya + run * (i + 1))
        top = z0 + rise * (i + 1)
        k.bx(x0 + 0.06, x1 - 0.06, a, b, top - 0.07, top, c)
        nose = (b - 0.06, b) if sg > 0 else (a, a + 0.06)
        k.qz(x0 + 0.1, x1 - 0.1, nose[0], nose[1], top + 0.003, 1, tread)
        k.colw(x0, x1, a, b, z0, top)
    # stringers (sloped)
    for x in (x0 + 0.05, x1 - 0.05):
        oslab(k, (x, ya, z0 + rise * 0.5 - 0.2), (x, yb, z1 - 0.2), 0.03, 0.18, 0.03, 0.18, 'steelDark')
    if rail:
        for x in (x0 - 0.025, x1 + 0.025):
            k.beam((x, ya + sg * 0.1, z0 + 1.0), (x, yb, z1 + 1.0), 0.06, 'hazard')
            k.beam((x, ya + sg * 0.1, z0 + 0.55), (x, yb, z1 + 0.55), 0.04, 'hazard', ink=False)
            for i in range(0, n + 1, 4):
                yy = ya + run * min(i, n - 0.5)
                zz = z0 + rise * min(i, n)
                k.bx(x - 0.04, x + 0.04, yy - 0.04, yy + 0.04, zz, zz + 1.0, 'hazard')
        if side_cols:
            for i in range(n + 1):
                a, b = srt(ya + run * max(0, i - 1), ya + run * i) if i else srt(ya - sg * 0.01, ya + sg * 0.01)
                top = z0 + rise * i
                for x in (x0 - 0.02, x1 + 0.02):
                    k.col(x - 0.07, x + 0.07, a, b, z0, top + 1.05)
