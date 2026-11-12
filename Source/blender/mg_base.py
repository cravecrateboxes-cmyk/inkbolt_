"""INKBOLT kit-mossgarden ("Mosswood Gardens", a landscaped garden: formal parterres round a tiered fountain, a raised
terrace, a glasshouse, then a wild garden with a stream, a hedge maze and a ruined folly on a mound): palette and
modelling helpers shared by mg_plants.py (giant trees, hedges, topiary, flower beds, ferns, glowing pods, rocks) and
mg_built.py (walls, gate, terrace, fountains, pools, bridges, glasshouse, gazebo, folly, pergola, shed, props). The
family module is fam_kit_mossgarden.py.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = game north.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (stair steps, bridge decks, plinths).
  * Link-run pieces (hedges: <Kind>Full / <Kind>Half / <Kind>Post) are modelled along Blender Y: the full module spans
    the cell (y -0.5..0.5), the half reaches from the edge of the post toward -Y (game +Z), the post covers the cell
    centre. Prefabs of size [w, d] have w along Blender X.
  * Stairs: walkable steps of 0.18 m rise on 0.25 m treads (robots climb 0.4 m per 0.5 m nav cell); the terrace top
    is TER = 2.34 m (13 steps), the theme's terrain lifts the terrace ground to exactly that height.
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
from rs_base import RKit

FAM = 'kit-mossgarden'
PFX = 'KIT_MOSSGARDEN_'
ib_lib.GLB[FAM] = 'fps-kit-mossgarden.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
# the order matters: the theme repaints flower heads by palette cell index (row * 8 + column, BASE first)
ib_lib.PALETTES[FAM] = BASE + [
    ('stone', '#E8DEC8'), ('stone2', '#D0C2A6'), ('stone3', '#B2A286'), ('stoneD', '#8C8070'),    # 8-11
    ('moss', '#86B851'), ('moss2', '#5E9741'), ('mossD', '#3E7334'), ('gravel', '#E2D5B8'),       # 12-15
    ('hedge', '#3F914A'), ('hedge2', '#2B7038'), ('hedgeT', '#66B552'), ('leaf', '#4FA854'),      # 16-19
    ('leafD', '#2E7D42'), ('leafL', '#8FCD63'), ('canopy', '#43A04E'), ('canopy2', '#2D7F42'),    # 20-23
    ('canopyL', '#7BC45C'), ('bark', '#7B5A3E'), ('barkD', '#52392A'), ('barkL', '#A27C57'),      # 24-27
    ('fern', '#5ABC5D'), ('fern2', '#36934A'), ('soil', '#6B4A33'), ('soil2', '#86603F'),         # 28-31
    ('tulip', '#F2384A'), ('tulipY', '#FFD23A'), ('tulipP', '#FF7DB8'), ('tulipO', '#FF8C2E'),    # 32-35
    ('tulipW', '#FFF2E6'), ('tulipV', '#A65CE2'), ('rose', '#E3304F'), ('roseP', '#FF9EC2'),      # 36-39
    ('lav', '#9C7CE6'), ('lav2', '#7553C6'), ('lavG', '#9DB58C'), ('glowC', '#86FFE8'),           # 40-43
    ('glowL', '#DCFF70'), ('glowM', '#FF92F0'), ('pod', '#2D6878'), ('pod2', '#4F96A2'),          # 44-47
    ('water', '#5ACCEA'), ('water2', '#2EA6D8'), ('foam', '#EFFFFF'), ('iron', '#2C3936'),        # 48-51
    ('verd', '#5FB59E'), ('bronze', '#C2914E'), ('glass', '#9FE2E4'), ('frame', '#F4F6EF'),       # 52-55
    ('wood', '#B57C4C'), ('wood2', '#8A5A33'), ('woodL', '#D6A46D'), ('terra', '#D8724A'),        # 56-59
    ('terra2', '#AE5638'), ('slate', '#5D6A80'), ('far', '#7DAA7C'), ('farD', '#5A8A63'),         # 60-63
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
CELL = {n: i for i, (n, _) in enumerate(ib_lib.PALETTES[FAM])}

TER = 2.34            # terrace top (terrain height, 13 steps of 0.18 m)
RISE, TREAD = 0.18, 0.25
WALL_H = 3.6          # garden wall height (theme wall.height)


class MKit(RKit):
    def text(self, word, x, y, z, cap, c, face='y-', font='serif', maxw=None, align='c', valign='b'):
        ib_text.draw(self, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)

    def _recolor(self, fs, c):
        for f in fs:
            f.normal_update()
            f.material_index = self.pal.index(c(f))

    def cyl(self, x, y, z, r1, r2, h, c, seg=8, ink=True, bevel=False, rot=(0, 0, 0), caps=True):
        """as Kit.cyl; c may be a palette name or fn(face) -> name"""
        if not callable(c):
            return super().cyl(x, y, z, r1, r2, h, c, seg=seg, ink=ink, bevel=bevel, rot=rot, caps=caps)
        self._recolor(self.m.cyl((x, y, z), r1, r2, h, 'stone', seg=seg, rot=rot, bevel=bevel, caps=caps), c)
        self._mark(ink)

    def bx(self, x0, x1, y0, y1, z0, z1, c, ink=True, bevel=False):
        if not callable(c):
            return super().bx(x0, x1, y0, y1, z0, z1, c, ink=ink, bevel=bevel)
        assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
        self._recolor(self.m.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), 'stone', bevel=bevel), c)
        self._mark(ink)

    def sph(self, x, y, z, r, c, seg=(6, 4), scale=(1, 1, 1), ink=True):
        if not callable(c):
            return super().sph(x, y, z, r, c, seg=seg, scale=scale, ink=ink)
        self._recolor(self.m.sphere((x, y, z), r, 'stone', seg=seg, scale=scale), c)
        self._mark(ink)

    _bn = 0

    def beam(self, a, b, t, c, ink=True):
        """as Kit.beam; every other beam is 8 mm thinner, so the sides of joined beams (a polyline: an arch, a ring)
        never lie in one plane"""
        MKit._bn += 1
        super().beam(a, b, t - (0.008 if MKit._bn % 2 else 0.0), c, ink=ink)

    def tube(self, a, b, r1, r2, c, seg=8, ink=True, caps=True):
        a, b = Vector(a), Vector(b)
        d = b - a
        tilt = math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))
        az = math.degrees(math.atan2(d.y, d.x))
        self.cyl(a.x, a.y, a.z, r1, r2, d.length, c, seg=seg, ink=ink, rot=(0, tilt, az), caps=caps)


def zcol(top, mid, low, up=0.5, dn=-0.2):
    """colour by facing: top / sides / underside"""
    def fn(f):
        n = f.normal
        return top if n.z > up else (low if n.z < dn else mid)
    return fn


def stonecol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.6:
        return 'moss' if math.sin(c.x * 3.1 + c.y * 2.3) > 0.55 else 'stone2'
    if n.z < -0.3:
        return 'stoneD'
    return 'stone3' if math.sin(c.x * 2.7 + c.y * 1.9 + c.z * 2.3) > 0.2 else 'stone2'


def mosscol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.35:
        return 'moss' if math.sin(c.x * 2.1 + c.y * 3.3) > -0.4 else 'moss2'
    if n.z < -0.3:
        return 'stoneD'
    return 'stone3' if math.sin(c.x * 2.9 + c.y * 1.7 + c.z * 2.1) > -0.1 else 'stoneD'


def blob(k, rnd, cx, cy, z0, rx, ry, h, col, n=6, ink=True, top=3):
    """faceted lump (shrub, canopy mass): convex hull of a foot ring, a waist ring and a crown"""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.25, 0.25)) / n * 2 * math.pi
        pts.append((cx + math.cos(a) * rx * 0.72, cy + math.sin(a) * ry * 0.72, z0))
        a2 = a + math.pi / n
        k2 = rnd.uniform(0.92, 1.06)
        pts.append((cx + math.cos(a2) * rx * k2, cy + math.sin(a2) * ry * k2, z0 + h * rnd.uniform(0.36, 0.55)))
    for i in range(top):
        a = rnd.uniform(0, 2 * math.pi)
        pts.append((cx + math.cos(a) * rx * 0.38, cy + math.sin(a) * ry * 0.38, z0 + h * rnd.uniform(0.9, 1.0)))
    return k.hullp(pts, col, ink=ink)


def puff(k, rnd, cx, cy, cz, r, col, n=7, flat=0.75, ink=True):
    """roundish faceted cloud of leaves centred on (cx, cy, cz)"""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.2, 0.2)) / n * 2 * math.pi
        pts.append((cx + math.cos(a) * r * rnd.uniform(0.9, 1.05), cy + math.sin(a) * r * rnd.uniform(0.9, 1.05), cz + rnd.uniform(-0.12, 0.12) * r))
    for s in (-1, 1):
        for i in range(3):
            a = (i + 0.5 * (s + 1) / 2 + rnd.uniform(-0.2, 0.2)) / 3 * 2 * math.pi
            pts.append((cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, cz + s * r * flat * rnd.uniform(0.8, 1.0)))
    return k.hullp(pts, col, ink=ink)


def bloom(k, x, y, z, s, c, ink=False):
    """a flower head: a flat octahedron"""
    k.hullp([(x + s, y, z), (x - s, y, z), (x, y + s, z), (x, y - s, z), (x, y, z + s * 0.55), (x, y, z - s * 0.45)], c, ink=ink)


def cup(k, x, y, z, s, c, ink=True):
    """a tulip head: an upright cup (six points)"""
    pts = []
    for i in range(4):
        a = i * math.pi / 2 + 0.4
        pts.append((x + math.cos(a) * s * 0.55, y + math.sin(a) * s * 0.55, z))
        pts.append((x + math.cos(a + 0.78) * s * 0.75, y + math.sin(a + 0.78) * s * 0.75, z + s * 1.2))
    pts.append((x, y, z - s * 0.35))
    k.hullp(pts, c, ink=ink)


def stem(k, a, b, w, c='leafD'):
    """a thin stem: a sliver of four points (four triangles, no outline)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L * w if L > 1e-6 else w, dx / L * w if L > 1e-6 else 0.0
    if math.hypot(dx, dy) < 1e-6:
        px, py = w, 0.0
    k.hullp([(a[0] + px, a[1] + py, a[2]), (a[0] - px, a[1] - py, a[2]), (a[0] + py * 0.7, a[1] - px * 0.7, a[2] + 0.01),
             (b[0], b[1], b[2])], c, ink=False)


def blade(k, base, az, L, W, up, c, droop=0.3):
    """a strap leaf (tulip, iris, grass): base point, direction az, length, width, rise"""
    dx, dy = math.cos(az), math.sin(az)
    sx, sy = -dy * W / 2, dx * W / 2
    x, y, z = base
    mid = (x + dx * L * 0.45, y + dy * L * 0.45, z + up * 0.8)
    tip = (x + dx * L, y + dy * L, z + up - droop * L)
    k.hullp([(x + sx, y + sy, z), (x - sx, y - sy, z), (mid[0] + sx * 0.8, mid[1] + sy * 0.8, mid[2]),
             (mid[0] - sx * 0.8, mid[1] - sy * 0.8, mid[2]), (mid[0], mid[1], mid[2] + 0.02), tip], c, ink=False)


def frond(k, base, az, L, W, lift=0.3, droop=0.8, seg=3, col=None, th=0.03, ink=True):
    """an arching fern / palm frond: V-section blade rising then drooping, seg hull segments to a tip"""
    dx, dy = math.cos(az), math.sin(az)
    sx, sy = -dy, dx
    col = col or zcol('fern', 'fern', 'fern2', 0.45)

    def P(t):
        z = base[2] + lift * L * math.sin(math.pi * min(1.0, t * 1.4) * 0.5) * (1 - t) - droop * L * t * t
        return (base[0] + dx * L * t, base[1] + dy * L * t, z)

    def wid(t):
        return W * (0.3 + 0.7 * math.sin(math.pi * (0.1 + 0.85 * t))) * (1.0 - 0.85 * t ** 3)
    for i in range(seg):
        pts = []
        for j, t in enumerate((i / seg, (i + 1) / seg)):
            p = P(t)
            w = wid(t) if (i + j) < seg else 0.04
            q = 0.93 if (j == 0 and i > 0) else 1.0
            dz = -0.008 if (j == 0 and i > 0) else 0.0
            for e in (-1, 1):
                pts.append((p[0] + sx * e * w / 2 * q, p[1] + sy * e * w / 2 * q, p[2] - w * 0.25 + dz))
            pts.append((p[0], p[1], p[2] + th + dz))
            pts.append((p[0], p[1], p[2] - th * 0.5 + dz))
        k.hullp(pts, col, ink=ink)
    return P(1.0)


def ring(cx, cy, r, n, z, a0=0.0):
    return [(cx + math.cos(a0 + i / n * 2 * math.pi) * r, cy + math.sin(a0 + i / n * 2 * math.pi) * r, z) for i in range(n)]


def baluster(k, x, y, z0, h=0.62, r=0.07, c='stone'):
    """a turned stone baluster: a vase belly and a neck (no outline: the rails carry the ink)"""
    k.cyl(x, y, z0, r * 0.95, r * 1.45, h * 0.5, c, seg=5, ink=False)
    k.cyl(x, y, z0 + h * 0.5, r * 1.45, r * 0.75, h * 0.5, c, seg=5, ink=False)


def urn(k, x, y, z0, s=1.0, c='stone', fl=None, rnd=None):
    """a stone garden urn on its foot; fl: flower colour (trailing flowers spill over the lip)"""
    k.cyl(x, y, z0, 0.16 * s, 0.1 * s, 0.12 * s, c, seg=7)
    k.cyl(x, y, z0 + 0.12 * s, 0.08 * s, 0.08 * s, 0.1 * s, c, seg=6, ink=False)
    k.cyl(x, y, z0 + 0.22 * s, 0.12 * s, 0.3 * s, 0.26 * s, c, seg=8)
    k.cyl(x, y, z0 + 0.48 * s, 0.33 * s, 0.33 * s, 0.06 * s, 'stone2', seg=8)
    if fl:
        rnd = rnd or random.Random(int(x * 100 + y * 37))
        blob(k, rnd, x, y, z0 + 0.5 * s, 0.3 * s, 0.3 * s, 0.32 * s, zcol('leafL', 'leaf', 'leafD'), n=5, top=2)
        for i in range(5):
            a = i / 5 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
            rr = rnd.uniform(0.12, 0.3) * s
            bloom(k, x + math.cos(a) * rr, y + math.sin(a) * rr, z0 + (0.72 + rnd.uniform(-0.05, 0.08)) * s, 0.06 * s, fl)
