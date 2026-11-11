"""INKBOLT kit-resort ("Palmyra Cove Resort", a luxury tropical resort with treehouse villas in giant palms):
palette and modelling helpers shared by rs_nature.py (palms, giant palms, broken-limb and fallen-frond ramps, hedges,
shore rocks, ground cover) and rs_build.py (lobby pavilion, lagoon pool with swim-up bar, cabanas, loungers, decks,
rails, rope bridges, villas, props, gate, trail, hatch, backdrop). The family module is fam_kit_resort.py.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = game north.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (ramp steps, bridge planks, villa floors).
  * Run pieces (rails) are modelled along Blender Y (the half module runs from the origin toward -Y); [3, 2] / [4, 2]
    run prefabs (rope bridge, plank decals) along Blender X: the prefab placer turns a block's long side onto local X.
  * Tree platforms are the engine's deck slab (theme symbol `deck`) at 7.5 m (TOP); their plank seams and joists are
    a decal piece laid over it, 4 mm above the slab top.
  * Ramps (broken limbs, fallen fronds) rise toward Blender +Y from 0 to TOP over RAMP_L m in RAMP_N walkable steps of
    0.25 m (rise 0.144 m: robots climb 0.4 m per 0.5 m nav cell, the player's feet snap down 0.2 m per step).
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

FAM = 'kit-resort'
PFX = 'KIT_RESORT_'
ib_lib.GLB[FAM] = 'fps-kit-resort.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    ('sand', '#F3DFA8'), ('sand2', '#E4C68B'), ('wet', '#CFAE74'),
    ('grass', '#7DC65A'), ('grass2', '#5BAA48'), ('grass3', '#A9DB76'),
    ('frond', '#3FAE58'), ('frond2', '#2A8A48'), ('frond3', '#74CD63'), ('frondY', '#C8B865'), ('frondB', '#9B7444'),
    ('trunk', '#C29464'), ('trunk2', '#9C7046'), ('trunk3', '#DDB384'), ('bark', '#8C5B37'), ('barkD', '#5E3B22'),
    ('heart', '#ECC28C'), ('coco', '#7A5530'), ('cocoG', '#A4B44C'),
    ('wood', '#BC7C4C'), ('wood2', '#8E5832'), ('wood3', '#DBA56C'), ('woodD', '#573720'),
    ('bamboo', '#D9C27A'), ('bamboo2', '#B3984F'),
    ('thatch', '#E3B865'), ('thatch2', '#C39343'), ('thatch3', '#F1D58F'), ('rope', '#E8D3A0'),
    ('stone', '#EDE2CC'), ('stone2', '#CDBEA3'), ('tile', '#F6EEDF'),
    ('water', '#52D8E2'), ('water2', '#2DB9D7'), ('waterD', '#1F90C5'), ('foam', '#F2FFFF'),
    ('canvas', '#FBF6EC'), ('canvas2', '#E5DAC4'), ('coral', '#F07A52'), ('cushion', '#2E93BC'),
    ('hibis', '#E6405A'), ('bloom', '#F8D24C'), ('leaf', '#2F8E48'), ('leafD', '#1E6A3C'),
    ('rock', '#ACA69C'), ('rock2', '#8B847B'), ('metal', '#A9B3BE'), ('metal2', '#69747F'),
    ('cart', '#F3F0E6'), ('tire', '#2A2A30'), ('flame', '#FF7A3D'), ('flame2', '#FFD35A'),
    ('far', '#82B793'), ('farS', '#A7CCD0'), ('crate', '#C99560'), ('pink', '#FF9EB4'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

TOP = 7.5             # tree platform deck top (zone layer 7.5)
SLAB = 0.35           # deck slab thickness (theme deck.thick)
RAMP_L, RAMP_N = 13.0, 52
WALL_H = 3.6          # hedge height


class RKit(Kit):
    """kit_base.Kit with walkable collision boxes (<Piece>_WCOL<n>)."""

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

    # ---- shapes
    def tube(self, a, b, r1, r2, c, seg=8, ink=True, caps=True):
        """frustum from point a (radius r1) to point b (radius r2)"""
        a, b = Vector(a), Vector(b)
        d = b - a
        tilt = math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))
        az = math.degrees(math.atan2(d.y, d.x))
        self.cyl(a.x, a.y, a.z, r1, r2, d.length, c, seg=seg, ink=ink, rot=(0, tilt, az), caps=caps)

    def text(self, word, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b'):
        ib_text.draw(self, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)


def leafcol(top='frond3', mid='frond', low='frond2'):
    def fn(f):
        n = f.normal
        return top if n.z > 0.45 else (low if n.z < -0.2 else mid)
    return fn


def rockcol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.6:
        return 'stone2'
    if n.z < -0.3:
        return 'rock2'
    return 'rock' if math.sin(c.x * 2.9 + c.y * 1.7 + c.z * 2.1) > -0.3 else 'rock2'


def barkcol(top='heart', side='bark', low='barkD'):
    def fn(f):
        n = f.normal
        return top if n.z > 0.8 else (low if n.z < -0.25 else side)
    return fn


def blob(k, rnd, cx, cy, z0, rx, ry, h, col, n=6, ink=True):
    """faceted lump (shrub, foliage mass): convex hull of a ring at the foot, a waist ring and a crown"""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.25, 0.25)) / n * 2 * math.pi
        pts.append((cx + math.cos(a) * rx * 0.8, cy + math.sin(a) * ry * 0.8, z0))
        a2 = a + math.pi / n
        k2 = rnd.uniform(0.92, 1.05)
        pts.append((cx + math.cos(a2) * rx * k2, cy + math.sin(a2) * ry * k2, z0 + h * rnd.uniform(0.38, 0.55)))
    for i in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        pts.append((cx + math.cos(a) * rx * 0.35, cy + math.sin(a) * ry * 0.35, z0 + h * rnd.uniform(0.9, 1.0)))
    return k.hullp(pts, col, ink=ink)


def frond(k, base, az, L, W, lift=0.25, droop=0.75, seg=2, col=None, rnd=None):
    """one palm frond: a V-sectioned blade along a rising then drooping arc, `seg` hull segments, tapering to a tip"""
    dx, dy = math.cos(az), math.sin(az)
    sx, sy = -dy, dx
    col = col or leafcol()
    ts = [i / seg for i in range(seg + 1)]

    def P(t):
        z = base[2] + lift * L * math.sin(math.pi * min(1.0, t * 1.4) * 0.5) * (1 - t) - droop * L * t * t
        return (base[0] + dx * L * t, base[1] + dy * L * t, z)

    def wid(t):
        return W * (0.35 + 0.65 * math.sin(math.pi * (0.12 + 0.82 * t))) * (1.0 - 0.8 * t ** 3)

    th = 0.035
    for i in range(seg):
        pts = []
        for j, t in enumerate((ts[i], ts[i + 1])):
            p = P(t)
            w = wid(t) if (i + j) < seg else 0.04
            sag = w * 0.32
            q = 0.93 if (j == 0 and i > 0) else 1.0   # the next segment starts a little narrower and lower: no shared faces
            dz = -0.01 if (j == 0 and i > 0) else 0.0
            for e in (-1, 1):
                pts.append((p[0] + sx * e * w / 2 * q, p[1] + sy * e * w / 2 * q, p[2] - sag + dz))
            pts.append((p[0], p[1], p[2] + th + dz))
            pts.append((p[0], p[1], p[2] - th * 0.5 + dz))
        k.hullp(pts, col)
    return P(1.0)


def palm(k, rnd, x, y, h, lean=0.16, az=None, fronds=7, flen=3.0, fw=0.9, r=(0.2, 0.13), rings=4, z0=0.0,
         nuts=3, seg=6, fseg=2, droop=0.75, cols=('trunk', 'trunk2')):
    """curved, ring-banded palm trunk with a crown of fronds and a coconut cluster; returns the crown point"""
    az = rnd.uniform(0, 2 * math.pi) if az is None else az
    dx, dy = math.cos(az), math.sin(az)
    pts = []
    for i in range(rings + 1):
        t = i / rings
        off = lean * h * t ** 1.7
        pts.append((x + dx * off, y + dy * off, z0 + h * t))
    for i in range(rings):
        t0, t1 = i / rings, (i + 1) / rings
        ra = r[0] + (r[1] - r[0]) * t0
        rb = r[0] + (r[1] - r[0]) * t1
        a = pts[i] if i == 0 else (pts[i][0], pts[i][1], pts[i][2] - 0.02)
        k.tube(a, pts[i + 1], ra * 1.08, rb * 0.96, cols[i % 2], seg=seg)
    tx, ty, tz = pts[-1]
    k.cyl(tx, ty, tz - 0.25, r[1] * 1.05, r[1] * 1.35, 0.4, 'frond2', seg=seg)
    for i in range(nuts):
        a = i / max(1, nuts) * 2 * math.pi + 0.4
        k.sph(tx + math.cos(a) * r[1] * 1.15, ty + math.sin(a) * r[1] * 1.15, tz - 0.32, 0.17 * (r[1] / 0.13) ** 0.5, 'coco' if i % 3 else 'cocoG', seg=(5, 3))
    a0 = rnd.uniform(0, 2 * math.pi)
    for i in range(fronds):
        a = a0 + (i + rnd.uniform(-0.18, 0.18)) / fronds * 2 * math.pi
        frond(k, (tx, ty, tz + 0.12), a, flen * rnd.uniform(0.85, 1.1), fw, lift=rnd.uniform(0.15, 0.32), droop=droop * rnd.uniform(0.8, 1.15), seg=fseg)
    return pts[-1]


def tuft(k, rnd, x, y, r, z0=0.0, col='grass2', n=5, ink=False):
    """grass / sedge tuft: a few thin upright blades"""
    for i in range(n):
        a = (i + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        L = r * rnd.uniform(0.7, 1.1)
        tip = (x + math.cos(a) * L * 0.5, y + math.sin(a) * L * 0.5, z0 + L * rnd.uniform(0.9, 1.3))
        b0 = (x + math.cos(a + 1.6) * 0.04, y + math.sin(a + 1.6) * 0.04, z0)
        b1 = (x - math.cos(a + 1.6) * 0.04, y - math.sin(a + 1.6) * 0.04, z0)
        k.hullp([b0, b1, tip, (x, y, z0 + 0.02)], col, ink=ink)


def flowers(k, rnd, pts, c='hibis', s=0.09):
    """small flat-ish flower heads (octahedra) at the given points"""
    for (x, y, z) in pts:
        q = s * rnd.uniform(0.8, 1.2)
        k.hullp([(x + q, y, z), (x - q, y, z), (x, y + q, z), (x, y - q, z), (x, y, z + q * 0.6), (x, y, z - q * 0.6)], c, ink=False)


def rope_sag(k, a, b, sag, c='rope', t=0.035, n=3):
    """a rope from a to b sagging `sag` in the middle (n straight pieces)"""
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u - sag * 4 * u * (1 - u)))
    hx, hy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(hx, hy) or 1.0
    px, py = -hy / L * 0.006, hx / L * 0.006   # neighbouring pieces sit 6 mm apart sideways (no shared faces)
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        e = 1 if i % 2 else -1
        k.beam((p[0] + px * e, p[1] + py * e, p[2]), (q[0] + px * e, q[1] + py * e, q[2]), t, c, ink=False)
