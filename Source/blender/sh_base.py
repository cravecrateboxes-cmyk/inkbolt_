"""INKBOLT kit-stronghold ("Fort Highwatch", a military stronghold carved into the side of a huge mountain): palette
and modelling helpers shared by sh_outer.py (the outer works on the cliff ledge: cliff and bunker faces, parapets,
bastions, pillboxes, gun emplacements, ramps, the helipad and its helicopter, radar, masts, floodlights, supplies,
gate, trail, hatch) and sh_inner.py (the carved rock halls: rock faces, the cavern roof, the vehicle hangar and the
armoured truck, the ammo depot, the barracks, the command centre with its tactical table, the observation terrace).
The family module is fam_kit_stronghold.py. The vista round the level (the massif, the valley, the two waterfalls,
the sunset sky dressing) is built in code by the theme (src/data/themes/stronghold.js backdrop.build).

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = game north, Blender +X = game east.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (ramp and stair steps).
  * Wall modules (theme wall.facing 'open') face Blender -Y: the cell spans y -0.5..0.5, the face plane is y = -0.5.
    2 m modules (<Name>2_*) span x -0.5..1.5: this cell and the next one along the module's local +X.
  * Run pieces placed with rotate 'run' (parapets, sandbag walls, jersey barriers) are modelled along Blender X.
    Link runs (rails, cage fence) are modelled along Blender Y (the half module runs from the origin toward -Y).
  * Ramps and stairs rise toward Blender +Y (game north) over their footprint's long side, in walkable steps of
    0.5 m (the nav cell) that rise 0.15 m (ramps) or 0.2 m (stairs): robots climb 0.4 m per nav cell, and a step
    is deeper than the player's radius, so the feet never snap back down over two steps at once.
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
from kit_base import Kit

FAM = 'kit-stronghold'
PFX = 'KIT_STRONGHOLD_'
ib_lib.GLB[FAM] = 'fps-kit-stronghold.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    ('rock', '#9C8477'), ('rock2', '#7F6B64'), ('rock3', '#B59C8B'), ('rockD', '#5C4D4D'), ('rockL', '#CDB29C'),
    ('cave', '#6E625F'), ('cave2', '#5A504F'), ('cave3', '#857772'),
    ('conc', '#BDB5A6'), ('conc2', '#9E978B'), ('conc3', '#D6CEBF'), ('concD', '#726C65'),
    ('olive', '#6B7445'), ('olive2', '#525C36'), ('oliveL', '#8C955E'), ('tan', '#B8A16E'),
    ('bag', '#C9B38A'), ('bag2', '#A8925F'), ('bag3', '#DCC9A0'),
    ('steel', '#8D96A0'), ('steel2', '#5F6872'), ('steelD', '#3B424B'), ('rust', '#9A5A3A'),
    ('crate', '#B98A55'), ('crate2', '#8C6438'), ('tarp', '#7C7F55'),
    ('asph', '#4A4E55'), ('asph2', '#3C4047'), ('paint', '#F3EBD8'),
    ('glass', '#83C9DD'), ('glassD', '#3D6F86'), ('screen', '#46E0CF'), ('screenD', '#1C5762'),
    ('lamp', '#FFE9A6'), ('lampW', '#FFF7DE'), ('beacon', '#FF5A3D'),
    ('map', '#8FB27A'), ('map2', '#6E9A62'), ('mapW', '#5C9BCB'), ('snow', '#F4EEE8'),
    ('tire', '#2A2A30'), ('brass', '#D7A341'), ('blanket', '#5D6B48'), ('linen', '#E2DAC6'),
    ('wood', '#A8784A'), ('flag', '#C7463A'), ('hazard', '#F2C230'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

CLIFF_H = 14.2      # zone 1 cliff / face modules (the massif's shell starts at 14 m above the face line)
HALL_H = 12.0       # zone 2 carved halls: walls up to the cavern roof
LINTEL = 4.2        # passage openings (terrace doorways) are clear up to here
T1, T2 = 3.6, 7.2   # zone 1 terrace tops
MEZZ = 2.4          # zone 2 deck tops
TRAIL_H = 5.0       # trail tunnel walls / ceiling


class SKit(Kit):
    """kit_base.Kit with walkable collision boxes (<Piece>_WCOL<n>) and a few shape helpers."""

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

    def tube(self, a, b, r1, r2, c, seg=8, ink=True, caps=True):
        """frustum from point a (radius r1) to point b (radius r2)"""
        a, b = Vector(a), Vector(b)
        d = b - a
        tilt = math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))
        az = math.degrees(math.atan2(d.y, d.x))
        self.cyl(a.x, a.y, a.z, r1, r2, d.length, c, seg=seg, ink=ink, rot=(0, tilt, az), caps=caps)

    def text(self, word, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b'):
        ib_text.draw(self, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)


# ---------------------------------------------------------------- shared shapes
def rock_face(k, rnd, x0, x1, h, cols, z0=0.0, rows=None, y0=-0.5, back=0.42, jut=0.2, over=0.0, side=-1, split=0.45):
    """A hewn rock face along X from x0 to x1 up to h: rows of irregular convex rock blocks whose fronts bulge out of
    the face plane y0 (toward side: -1 = -Y, +1 = +Y) by up to `jut`, overlapping the neighbouring modules by `over`
    and each other a little, so the seams between modules and rows disappear in the jumble."""
    n = rows or max(2, int(round((h - z0) / 3.6)))
    zs = [z0] + [z0 + (h - z0) * (i + rnd.uniform(-0.22, 0.22)) / n for i in range(1, n)] + [h]

    def col(f):
        nz = f.normal.z
        if nz > 0.55:
            return cols[-1]
        return cols[0] if nz < -0.4 else None
    for i in range(n):
        za, zb = zs[i], zs[i + 1]
        cuts = [x0, x1] if (x1 - x0) < 1.5 or rnd.random() < split else [x0, x0 + (x1 - x0) * rnd.uniform(0.38, 0.62), x1]
        for j, (a, b) in enumerate(zip(cuts, cuts[1:])):
            ea = a - (over if j == 0 else 0.12) - 0.014 * (i % 3)
            eb = b + (over if j == len(cuts) - 2 else 0.12) + 0.014 * ((i + 1) % 3)
            za2 = za - (0.22 if i > 0 else 0.0) + 0.016 * j
            zb2 = zb + (0.18 if i < n - 1 else 0.0) - 0.013 * j
            p = rnd.uniform(0.06, jut)
            yb = y0 - side * (back + 0.011 * ((i * 3 + j) % 6))   # backs staggered: never coplanar
            # the back stays inside the module (copies of a module side by side never share a back plane); the top and
            # bottom tilt along X, so the overlapping fronts of neighbouring copies never lie in one plane either
            ia, ib = a + (0.02 if j == 0 else 0.0), b - (0.02 if j == len(cuts) - 2 else 0.0)
            pts = [(ia, yb, za2 + 0.04), (ib, yb, za2), (ia, yb, zb2), (ib, yb, zb2 - 0.06)]
            for (fx, fz) in ((0.04, 0.02), (0.96, 0.06), (0.06, 0.96), (0.94, 0.93), (rnd.uniform(0.3, 0.7), rnd.uniform(0.3, 0.7))):
                hi, lo = x1 + over - 0.012 - 0.007 * (i % 4), x0 - over + 0.012 + 0.007 * ((i + 2) % 4)   # rows never share a side plane
                x = min(hi, max(lo, ea + (eb - ea) * fx + rnd.uniform(-0.06, 0.06)))
                z = za2 + (zb2 - za2) * fz + rnd.uniform(-0.04, 0.04)
                pts.append((x, y0 + side * p * rnd.uniform(0.35, 1.0), z))
            base = cols[(i + j) % (len(cols) - 1)]
            k.hullp(pts, lambda f, base=base: col(f) or base)


def rock_pillar(k, rnd, h, cols, z0=0.0, r=0.47):
    """a free-standing rock pillar over one cell (corners, notches): rows of irregular blocks all round"""
    n = max(2, int(round((h - z0) / 3.6)))
    zs = [z0] + [z0 + (h - z0) * (i + rnd.uniform(-0.2, 0.2)) / n for i in range(1, n)] + [h]
    for i in range(n):
        za, zb = zs[i] - (0.2 if i else 0.0), zs[i + 1] + (0.15 if i < n - 1 else 0.0)
        pts = []
        for j in range(6):
            a = (j + rnd.uniform(-0.25, 0.25)) / 6 * 2 * math.pi
            rr = r * rnd.uniform(0.9, 1.06)
            pts.append((math.cos(a) * rr, math.sin(a) * rr, za))
            pts.append((math.cos(a + 0.4) * rr * 0.96, math.sin(a + 0.4) * rr * 0.96, zb))
        base = cols[i % (len(cols) - 1)]
        k.hullp(pts, lambda f, base=base: cols[-1] if f.normal.z > 0.55 else base)


def sandbag_row(k, x0, x1, y, z, n=None, c=('bag', 'bag2', 'bag3'), w=0.5, h=0.2, d=0.32, stagger=False, ink=True):
    """one course of sandbags along X centred on y at height z (alternate colours); stagger: half bags at the ends"""
    L = x1 - x0
    n = n or max(1, int(round(L / w)))
    bw = L / n
    cuts = [x0 + i * bw for i in range(n + 1)]
    if stagger and n > 1:
        cuts = [x0] + [x0 + (i + 0.5) * bw for i in range(n)] + [x1]
    for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
        a, b = a + 0.012, b - 0.012
        if b - a < 0.08:
            continue
        k.bx(a, b, y - d / 2, y + d / 2, z, z + h, c[(i + int(z * 7)) % len(c)], ink=ink)


def sandbag_wall(k, x0, x1, y, courses=4, z0=0.0, h=0.21, d=0.42):
    """stacked sandbag wall along X (staggered courses, each a little narrower)"""
    for i in range(courses):
        sandbag_row(k, x0, x1, y, z0 + i * h, h=h - 0.014, d=d - 0.035 * i, stagger=bool(i % 2))


def crate(k, cx, cy, z, sx, sy, sz, c='olive', band='olive2', stencil=None):
    """military crate: body, two straps / battens, end handles"""
    k.bx(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, z, z + sz, c)
    for f in (-0.32, 0.32):
        x = cx + f * sx
        k.bx(x - 0.035, x + 0.035, cy - sy / 2 - 0.012, cy + sy / 2 + 0.012, z + 0.02, z + sz + 0.012, band, ink=False)
    if stencil:
        k.text(stencil, cx, cy - sy / 2 - 0.016, z + sz * 0.38, sz * 0.26, 'paint', maxw=sx * 0.5, font='display')


def drum(k, x, y, z=0.0, r=0.29, h=0.88, c='olive', ring='olive2'):
    k.cyl(x, y, z, r, r, h, c, seg=8)
    k.cyl(x, y, z + h * 0.45 - 0.02, r + 0.012, r + 0.012, 0.04, ring, seg=8, caps=False, ink=False)
    k.cyl(x, y, z + h, r * 0.8, r * 0.8, 0.012, ring, seg=6, ink=False)


def pipe_rail(k, x0, x1, y, z=0.0, h=1.05, posts=None, c='amber', post_c='steel2'):
    """steel pipe railing along X: top rail, mid rail, posts"""
    k.cyl(x0, y, z + h, 0.035, 0.035, x1 - x0, c, seg=6, rot=(0, 90, 0), caps=False)
    k.cyl(x0, y, z + h * 0.52, 0.025, 0.025, x1 - x0, c, seg=6, rot=(0, 90, 0), caps=False, ink=False)
    for x in (posts if posts is not None else [x0 + 0.04, x1 - 0.04]):
        k.cyl(x, y, z, 0.035, 0.035, h, post_c, seg=6)


def lattice(k, x, y, z0, z1, w0, w1, c='steel', every=1.6, brace=True, ink=True):
    """square lattice mast tapering from w0 to w1 (legs, horizontal rings, X braces on two faces)"""
    H = z1 - z0
    legs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for (sx, sy) in legs:
        k.beam((x + sx * w0 / 2, y + sy * w0 / 2, z0), (x + sx * w1 / 2, y + sy * w1 / 2, z1), 0.07, c, ink=ink)
    n = max(1, int(H / every))
    for i in range(1, n + 1):
        t = i / n
        z = z0 + H * t
        w = w0 + (w1 - w0) * t
        tp = (i - 1) / n
        wp = w0 + (w1 - w0) * tp
        zp = z0 + H * tp
        for j in range(4):
            a, b = legs[j], legs[(j + 1) % 4]
            dz = 0.012 * (j % 2)
            k.beam((x + a[0] * w / 2, y + a[1] * w / 2, z + dz), (x + b[0] * w / 2, y + b[1] * w / 2, z + dz), 0.04 - 0.008 * (j % 2), c, ink=False)
            if brace and j % 2 == 0:
                k.beam((x + a[0] * wp / 2, y + a[1] * wp / 2, zp), (x + b[0] * w / 2, y + b[1] * w / 2, z), 0.03, c, ink=False)


def rock_lump(k, rnd, cx, cy, rx, ry, h, z0=0.0, col=None):
    from kit_base import rock_pts
    pts = rock_pts(rnd, (cx, cy), rx, ry, h, z0=z0, n=6, top=3)

    def rc(f):
        n = f.normal
        if n.z > 0.6:
            return 'rockL'
        return 'rock2' if n.z < -0.2 else 'rock'
    return k.hullp(pts, col or rc)


def steps(k, x0, x1, y0, y1, z0, z1, n, wall=False):
    """walkable steps rising toward +Y from z0 at y0 to z1 at y1: n treads (WCOL boxes from the floor to the tread)"""
    run = (y1 - y0) / n
    for i in range(n):
        top = z0 + (i + 1) * (z1 - z0) / n
        k.wcol(x0, x1, y0 + i * run, y0 + (i + 1) * run, 0.0 if not wall else z0, top)
