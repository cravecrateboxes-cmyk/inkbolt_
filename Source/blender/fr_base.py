"""INKBOLT kit-frontier ("Cinder Ridge Outpost", the last campaign map): palette and modelling helpers shared by
fr_town.py (zone 1, the stockade settlement: palisade, gate, watchtowers, the main street's log cabins and plank-front
buildings with their walk-in interiors, the water tower, the well, corrals, wagons, the supply depot's generator,
solar panels, radio mast and fuel tanks) and fr_wild.py (zone 2, the edge of the wild: forest-edge and cliff-lip
walls, the ravine banks and the rope bridge, the sawmill with its water wheel and flume, the logging camp, the old
mine entrance, the lookout platform, conifers, boulders, fallen logs, the instanced backdrop trees).
The family module is fam_kit_frontier.py.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +Y = game north.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (porches, floors, stair treads, decks).
  * Run pieces (fences, flume) are modelled along Blender Y (the half module runs from the origin toward -Y).
  * Wall modules face Blender -Y (the theme turns their -Y face toward the open side: wall.facing 'open').
  * Floors of the walk-in buildings stand FLOOR (0.35 m) up; stairs rise RISE (0.18 m) per 0.25 m tread.
"""
import math
import os
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
from kit_base import Kit
import fr_detail as FD

FAM = 'kit-frontier'
PFX = 'KIT_FRONTIER_'
ib_lib.GLB[FAM] = 'fps-kit-frontier.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    # timber: logs (bark side, lit, shade), cut ends, seams; planks (raw, weathered grey, barn red, whitewash, blue-grey)
    ('log', '#B27B4A'), ('log2', '#8D5C35'), ('log3', '#CC9763'), ('logD', '#553420'), ('logEnd', '#E6BE88'),
    ('plank', '#C8A06E'), ('plank2', '#A27A4E'), ('plankG', '#A0968A'), ('plankR', '#A9473A'), ('plankW', '#E9E1CB'),
    ('plankB', '#5E7F96'), ('plankGr', '#6F8C58'),
    # roofs
    ('shingle', '#6D5A4D'), ('shingle2', '#4D3F37'), ('tin', '#9AA5AD'), ('tin2', '#6C7881'), ('rust', '#A65A34'),
    # stone, rock, earth, water
    ('stone', '#AAA397'), ('stone2', '#837C71'), ('rock', '#928C83'), ('rock2', '#6E6A64'), ('rock3', '#B8B2A8'),
    ('dirt', '#9A7850'), ('dirt2', '#76583A'), ('water', '#4FA9C9'), ('water2', '#3683AA'), ('foam', '#EAF6FA'),
    # living green
    ('pine', '#2F6B46'), ('pine2', '#224F36'), ('pine3', '#4B8C56'), ('grass', '#80A653'), ('grass2', '#5E8941'),
    ('moss', '#6F8D47'),
    # iron, steel, supply gear
    ('iron', '#4A4A51'), ('iron2', '#2E2E35'), ('steel', '#A9B2BA'), ('olive', '#606D3B'), ('olive2', '#47522B'),
    ('fuel', '#DDA830'), ('solar', '#2B4979'), ('solar2', '#5384BD'),
    # cloth, rope, goods
    ('canvas', '#E8DEC2'), ('canvas2', '#C6B68C'), ('rope', '#D9C18B'), ('hay', '#E3C56B'), ('cloth', '#B5403A'),
    ('cloth2', '#3E5E8E'), ('glass', '#3D5F7B'), ('glassL', '#9CC0D3'),
    # fire, light
    ('fire', '#FF8A2A'), ('fire2', '#FFD24A'), ('coal', '#2A2422'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

FLOOR = 0.35     # walk-in floors and porches
RISE = 0.18      # stair rise per tread (0.25 m): 0.36 m per 0.5 m nav cell, under the robots' 0.4 m step
TREAD = 0.25
WALL_H = 4.0     # palisade / zone wall height
DEBUG_SHAPES = bool(os.environ.get('FR_DEBUG'))
PLAT = 3.2       # zone 2 plateau height (terrain) = the rope bridge deck


class FKit(Kit):
    """kit_base.Kit with walkable collision boxes (<Piece>_WCOL<n>) and a few building shapes."""

    def _mark(self, ink):
        super()._mark(ink)
        if DEBUG_SHAPES:
            import traceback
            st = traceback.extract_stack()[-5:-1]
            self.where[self.m.nshape] = ' < '.join('%s:%d' % (f.name, f.lineno) for f in reversed(st))

    def poly(self, pts, c, normal):
        super().poly(pts, c, normal)
        self._mark(False)

    def begin(self, rot=0):
        super().begin(rot)
        self.walk = set()
        self.where = {}
        return self

    def wcol(self, x0, x1, y0, y1, z0, z1):
        self.walk.add(len(self.cols))
        self.cols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        if DEBUG_SHAPES and os.environ.get('FR_PROFILE') and name in os.environ['FR_PROFILE'].split(','):
            cnt = {}
            for f in self.m.bm.faces:
                w = self.where.get(f[self.m.shape], '?').split(' < ')
                key = ' < '.join(w[1:3])
                ink = f[self.m.shape] not in self.flat
                cnt[key] = cnt.get(key, 0) + len(f.verts)
            for kk, v in sorted(cnt.items(), key=lambda t: -t[1])[:22]:
                print('PROF %-10s %6d  %s' % (name, v, kk))
        try:
            obj = super().finish(name, bevel, ao)
        except Exception as e:
            if DEBUG_SHAPES:
                import re
                for sid in sorted({int(x) for x in re.findall(r'shapes (\d+)/(\d+)', str(e)) for x in x}):
                    print('  shape', sid, self.where.get(sid))
            raise
        full = self.prefix + name
        for i in sorted(self.walk):
            bpy.data.objects['%s_COL%d' % (full, i)].name = '%s_WCOL%d' % (full, i)
        return obj

    # ---- shapes
    def tube(self, a, b, r1, r2, c, seg=6, ink=True, caps=True):
        """frustum from point a (radius r1) to point b (radius r2)"""
        a, b = Vector(a), Vector(b)
        d = b - a
        tilt = math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))
        az = math.degrees(math.atan2(d.y, d.x))
        self.cyl(a.x, a.y, a.z, r1, r2, d.length, c, seg=seg, ink=ink, rot=(0, tilt, az), caps=caps)

    def text(self, word, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b'):
        n0 = self.m.nshape
        ib_text.draw(self, word, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)
        # the glyph triangles come with their own corners: weld them (a third of the vertices, same look)
        sh = self.m.shape
        vs = list({v for f in self.m.bm.faces if f[sh] > n0 for v in f.verts})
        if vs:
            bmesh.ops.remove_doubles(self.m.bm, verts=vs, dist=1e-5)

    def box2(self, x0, x1, y0, y1, z0, z1, col, ink=True):
        """box whose faces are coloured by fn(face) (or a name): e.g. outside / inside of a wall"""
        pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        return self.hullp(pts, col, ink=ink)


def by_normal(px=None, nx=None, py=None, ny=None, top=None, bot=None, other='plank'):
    """face colour by the face's normal direction (+x, -x, +y, -y, top, bottom)"""
    def fn(f):
        n = f.normal
        if n.z > 0.7:
            return top or other
        if n.z < -0.7:
            return bot or other
        if abs(n.x) >= abs(n.y):
            return (px if n.x > 0 else nx) or other
        return (py if n.y > 0 else ny) or other
    return fn


def leafcol(top='pine3', mid='pine', low='pine2'):
    def fn(f):
        n = f.normal
        return top if n.z > 0.45 else (low if n.z < -0.2 else mid)
    return fn


def rockcol(f):
    n, c = f.normal, f.calc_center_median()
    if n.z > 0.65:
        return 'rock3' if math.sin(c.x * 1.3 + c.y * 0.7) > -0.6 else 'moss'
    if n.z < -0.3:
        return 'rock2'
    return 'rock' if math.sin(c.x * 2.9 + c.y * 1.7 + c.z * 2.1) > -0.3 else 'rock2'


def barkcol(f):
    n = f.normal
    return 'logEnd' if abs(n.z) > 0.8 else ('log2' if (n.x + n.y) < 0 else 'log')


def rock(k, rnd, cx, cy, rx, ry, h, z0=0.0, n=7, top=3, col=rockcol, ink=True):
    """faceted boulder (convex hull of a ring at the foot, a waist ring and a few crown points)"""
    pts = []
    for i in range(n):
        a = (i + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        q = rnd.uniform(0.82, 1.0)
        pts.append((cx + math.cos(a) * rx * q, cy + math.sin(a) * ry * q, z0))
    for i in range(n):
        a = (i + 0.5 + rnd.uniform(-0.3, 0.3)) / n * 2 * math.pi
        q = rnd.uniform(0.86, 1.06)
        pts.append((cx + math.cos(a) * rx * q, cy + math.sin(a) * ry * q, z0 + h * rnd.uniform(0.32, 0.58)))
    for i in range(top):
        a = rnd.uniform(0, 2 * math.pi)
        q = rnd.uniform(0.1, 0.6)
        pts.append((cx + math.cos(a) * rx * q, cy + math.sin(a) * ry * q, z0 + h * rnd.uniform(0.8, 1.0)))
    return k.hullp(pts, col, ink=ink)


def conifer(k, rnd, x, y, h, r, z0=0.0, tiers=3, seg=6, trunk=True, ink=True, cols=('pine', 'pine3', 'pine2'), caps=True):
    """comic-ink conifer: a short trunk and `tiers` stacked cones, each a little narrower, tipped up at the top"""
    if trunk:
        k.cyl(x, y, z0 - 0.05, r * 0.12, r * 0.09, h * 0.22 + 0.05, 'log2', seg=5, caps=False, ink=ink)
    base = z0 + min(h * 0.16, 1.3) - rnd.uniform(0.0, 0.15)
    span = h - (base - z0)
    for t in range(tiers):
        f = t / max(1, tiers)
        zb = base + span * f * 0.82
        rr = r * (1.0 - 0.62 * f)
        hh = (h - zb + z0) if t == tiers - 1 else span * (0.52 - 0.08 * t)
        ox, oy = rnd.uniform(-0.04, 0.04) * r, rnd.uniform(-0.04, 0.04) * r
        k.cyl(x + ox, y + oy, zb, rr, 0.0, hh, cols[t % 2] if t < tiers - 1 else cols[1], seg=seg, ink=ink,
              rot=(0, 0, rnd.uniform(0, 60)), caps=caps)
    return z0 + h


def log_x(k, x0, x1, y, z, r, c='log', seg=6, ends=True, ink=True):
    """a horizontal log along X (axis at y, z) with cut-end discs"""
    k.cyl(x0, y, z, r, r, x1 - x0, c, seg=seg, rot=(0, 90, 0), caps=False, ink=ink)
    if ends:
        for x, s in ((x0, -1), (x1, 1)):
            pts = [(x + s * 0.003, y + math.cos(i / seg * 2 * math.pi) * r * 0.92, z + math.sin(i / seg * 2 * math.pi) * r * 0.92) for i in range(seg)]
            k.poly(pts, 'logEnd', (s, 0, 0))


def log_y(k, y0, y1, x, z, r, c='log', seg=6, ends=True, ink=True):
    """a horizontal log along Y"""
    k.cyl(x, y0, z, r, r, y1 - y0, c, seg=seg, rot=(-90, 0, 0), caps=False, ink=ink)
    if ends:
        for y, s in ((y0, -1), (y1, 1)):
            pts = [(x + math.cos(i / seg * 2 * math.pi) * r * 0.92, y + s * 0.003, z + math.sin(i / seg * 2 * math.pi) * r * 0.92) for i in range(seg)]
            k.poly(pts, 'logEnd', (0, s, 0))


def post(k, x, y, z0, h, r=0.09, c='log2', seg=6, ink=True):
    k.cyl(x, y, z0, r, r * 0.92, h, c, seg=seg, ink=ink)


def plank_lines(k, face, u0, u1, v0, v1, w, every, c, along='v', step=None):
    """painted board seams on an axis plane: face = ('y', y, sign) / ('x', x, sign); lines every `every` m
    running along v (vertical boards) or along u (horizontal courses)"""
    ax, pos, s = face
    d = s * 0.005
    if along == 'v':
        n = int(round((u1 - u0) / every))
        for i in range(1, n):
            u = u0 + i * (u1 - u0) / n
            if ax == 'y':
                k.qy(u - w / 2, u + w / 2, v0, v1, pos + d, s, c)
            else:
                k.qx(u - w / 2, u + w / 2, v0, v1, pos + d, s, c)
    else:
        n = int(round((v1 - v0) / every))
        for i in range(1, n):
            v = v0 + i * (v1 - v0) / n
            if ax == 'y':
                k.qy(u0, u1, v - w / 2, v + w / 2, pos + d, s, c)
            else:
                k.qx(u0, u1, v - w / 2, v + w / 2, pos + d, s, c)


def segments(u0, u1, holes, v=None):
    """[u0, u1] minus the holes' u ranges (holes: (a, b, z0, z1) ; with v: only holes spanning height v)"""
    out, cur = [], u0
    for (a, b, z0, z1) in sorted(holes):
        if v is not None and not (z0 <= v <= z1):
            continue
        if a > cur + 1e-4:
            out.append((cur, a))
        cur = max(cur, b)
    if u1 > cur + 1e-4:
        out.append((cur, u1))
    return out


def wall_parts(u0, u1, z0, z1, holes):
    """the wall rectangle minus the holes as non-overlapping boxes (u strips between hole edges, merged when equal)"""
    us = sorted({u0, u1} | {min(max(h[0], u0), u1) for h in holes} | {min(max(h[1], u0), u1) for h in holes})
    strips = []
    for a, b in zip(us, us[1:]):
        if b - a < 1e-4:
            continue
        m = (a + b) / 2
        cut = sorted((max(h[2], z0), min(h[3], z1)) for h in holes if h[0] < m < h[1])
        spans, cur = [], z0
        for (c0, c1) in cut:
            if c0 > cur + 1e-4:
                spans.append((cur, c0))
            cur = max(cur, c1)
        if z1 > cur + 1e-4:
            spans.append((cur, z1))
        if strips and strips[-1][2] == spans and abs(strips[-1][1] - a) < 1e-6:
            strips[-1][1] = b
        else:
            strips.append([a, b, spans])
    return [(a, b, c0, c1) for (a, b, spans) in strips for (c0, c1) in spans]


def wall(k, axis, pos, u0, u1, z0, z1, t, holes, outside, inside, top='plank2', cols=True, colz=None):
    """A straight wall slab with rectangular holes (doors / windows): axis 'x' = the wall runs along X at y = pos,
    'y' = along Y at x = pos; t = thickness (centred on pos); outside / inside: colours of its two faces (outside is
    the face whose normal points away from the building centre, given by the sign of pos). holes: [(u0, u1, z0, z1)].
    Collision: the same pieces as boxes (cols=False skips; colz caps a box's top, e.g. under a floor slab)."""
    s = 1 if pos > 0 else -1
    if axis == 'x':
        col = by_normal(py=outside if s > 0 else inside, ny=inside if s > 0 else outside, top=top, bot=top, other=top)
    else:
        col = by_normal(px=outside if s > 0 else inside, nx=inside if s > 0 else outside, top=top, bot=top, other=top)
    parts = wall_parts(u0, u1, z0, z1, holes)
    for (a, b, c0, c1) in parts:
        if axis == 'x':
            k.box2(a, b, pos - t / 2, pos + t / 2, c0, c1, col)
            if cols:
                k.col(a, b, pos - t / 2, pos + t / 2, c0, min(c1, colz or c1))
        else:
            k.box2(pos - t / 2, pos + t / 2, a, b, c0, c1, col)
            if cols:
                k.col(pos - t / 2, pos + t / 2, a, b, c0, min(c1, colz or c1))
    return parts


def window(k, axis, pos, s, u0, u1, z0, z1, t, frame='plankW', glass='glass', open_=False, shutters=None, sill=True, gd=0.01):
    """painted trim (head, jambs, sill), panes with a highlight and a cross mullion, shutters, all flat quads on the
    wall face; s = the outward side (+1 / -1); gd: how far out of the wall's centre line the pane sits (in the hole of
    a walk-in wall, then it is drawn on both sides, or on the face of a closed wall)"""
    fw = 0.08
    f = pos + s * (t / 2 + 0.012)
    def q(a, b, c0, c1, d, c, sg=None):
        if axis == 'x':
            k.qy(a, b, c0, c1, d, sg or s, c)
        else:
            k.qx(a, b, c0, c1, d, sg or s, c)
    q(u0 - fw, u1 + fw, z1, z1 + fw, f, frame)
    q(u0 - fw, u0, z0, z1, f, frame)
    q(u1, u1 + fw, z0, z1, f, frame)
    if sill:
        q(u0 - fw - 0.04, u1 + fw + 0.04, z0 - 0.08, z0, f, frame)
    if not open_:
        um, zm = (u0 + u1) / 2, (z0 + z1) / 2
        g = pos + s * gd
        sides = (1, -1) if gd < t / 2 else (1,)
        for e in sides:
            ss = s * e
            q(u0, u1, z0, z1, g + ss * 0.0, glass, ss)
            q(u0 + 0.06, um - 0.03, zm + 0.04, z1 - 0.07, g + ss * 0.003, 'glassL', ss)
            q(um - 0.025, um + 0.025, z0, z1, g + ss * 0.006, frame, ss)
            q(u0, u1, zm - 0.025, zm + 0.025, g + ss * 0.009, frame, ss)
    if shutters:
        w = (u1 - u0) / 2
        for a, b in ((u0 - fw - 0.06 - w, u0 - fw - 0.06), (u1 + fw + 0.06, u1 + fw + 0.06 + w)):
            q(a, b, z0 - 0.02, z1 + 0.02, f, shutters)
            q(a + 0.05, b - 0.05, (z0 + z1) / 2 - 0.02, (z0 + z1) / 2 + 0.02, f + s * 0.003, 'logD' if shutters != 'logD' else 'ink')


def gable(k, x0, x1, y0, y1, ze, zr, th, c='shingle', c2='shingle2', over=0.35, ridge_along='x', ink=True):
    """gable roof over the rectangle, eaves at ze, ridge at zr, slab thickness th, overhang `over`"""
    if ridge_along == 'x':
        cy = (y0 + y1) / 2
        xa, xb = x0 - over, x1 + over
        for ya, sgn in ((y0 - over, -1), (y1 + over, 1)):
            # eave drops the slope a little further out
            dz = (zr - ze) / ((y1 - y0) / 2) * over
            pts = [(x, y, z) for x in (xa, xb) for (y, z) in ((ya, ze - dz), (cy, zr), (ya, ze - dz - th), (cy, zr - th))]
            k.hullp(pts, by_normal(top=c, bot=c2, other=c2, py=c if sgn > 0 else c2, ny=c if sgn < 0 else c2), ink=ink)
        k.beam((xa - 0.05, cy, zr + 0.02), (xb + 0.05, cy, zr + 0.02), 0.16, c2, ink=ink)
    else:
        cx = (x0 + x1) / 2
        ya, yb = y0 - over, y1 + over
        for xa, sgn in ((x0 - over, -1), (x1 + over, 1)):
            dz = (zr - ze) / ((x1 - x0) / 2) * over
            pts = [(x, y, z) for y in (ya, yb) for (x, z) in ((xa, ze - dz), (cx, zr), (xa, ze - dz - th), (cx, zr - th))]
            k.hullp(pts, by_normal(top=c, bot=c2, other=c2, px=c if sgn > 0 else c2, nx=c if sgn < 0 else c2), ink=ink)
        k.beam((cx, ya - 0.05, zr + 0.02), (cx, yb + 0.05, zr + 0.02), 0.16, c2, ink=ink)


def gable_end(k, axis, pos, a, b, ze, zr, t, c, inside=None):
    """triangular gable wall filling the roof end: axis 'x' = in the plane y = pos spanning x a..b"""
    m = (a + b) / 2
    if axis == 'x':
        pts = [(x, pos + d, z) for d in (-t / 2, t / 2) for (x, z) in ((a, ze), (b, ze), (m, zr))]
        s = 1 if pos > 0 else -1
        k.hullp(pts, by_normal(py=c if s > 0 else (inside or c), ny=c if s < 0 else (inside or c), other=c))
    else:
        pts = [(pos + d, y, z) for d in (-t / 2, t / 2) for (y, z) in ((a, ze), (b, ze), (m, zr))]
        s = 1 if pos > 0 else -1
        k.hullp(pts, by_normal(px=c if s > 0 else (inside or c), nx=c if s < 0 else (inside or c), other=c))


def shed_roof(k, x0, x1, y0, y1, z0, z1, th, c='shingle', c2='shingle2', ink=True):
    """mono-pitch roof slab from y0 (height z0) to y1 (height z1)"""
    pts = [(x, y, z) for x in (x0, x1) for (y, z) in ((y0, z0), (y1, z1), (y0, z0 - th), (y1, z1 - th))]
    k.hullp(pts, by_normal(top=c, bot=c2, other=c2), ink=ink)


def stairs(k, x0, x1, y0, z0, n, c='plank', side='plank2', dir_=1, stringers=True, cols=True):
    """straight stair: n treads of TREAD m rising RISE from z0, starting at y0 and running toward +Y (dir_ 1) or -Y;
    each tread a walkable box solid down to z0 (robot nav and the player's stepping)"""
    for i in range(n):
        ya = y0 + dir_ * i * TREAD
        yb = ya + dir_ * TREAD
        za = z0 + (i + 1) * RISE
        lo, hi = min(ya, yb), max(ya, yb)
        k.bx(x0, x1, lo, hi, za - 0.06, za, c if i % 2 else side, ink=False)
        if cols:
            k.wcol(x0, x1, lo, hi, z0, za)
    if stringers:
        yE = y0 + dir_ * n * TREAD
        for x in (x0 - 0.04, x1):
            pts = [(xx, y, z) for xx in (x, x + 0.04) for (y, z) in ((y0, z0), (yE, z0 + n * RISE), (yE, z0 + n * RISE - 0.3), (y0 + dir_ * 0.3, z0))]
            k.hullp(pts, 'plank2')
    return y0 + dir_ * n * TREAD


def rail_run(k, axis, a, b, c0, z0, h=1.0, c='log2', posts=1.2, r=0.05, ink=True):
    """a simple porch / deck railing along X (axis 'x', at y = c0) or Y (at x = c0) from a to b: posts (a post two
    runs share at a corner is made once) and two rails running between the posts' faces"""
    if not hasattr(k, '_posts') or k._posts[0] is not k.m:
        k._posts = (k.m, set())
    seen = k._posts[1]
    n = max(1, int(round(abs(b - a) / posts)))
    us = [a + (b - a) * i / n for i in range(n + 1)]
    for u in us:
        key = (round(u if axis == 'x' else c0, 3), round(c0 if axis == 'x' else u, 3), round(z0, 3))
        if key in seen:
            continue
        seen.add(key)
        if axis == 'x':
            k.bx(u - r, u + r, c0 - r, c0 + r, z0, z0 + h, c, ink=ink)
        else:
            k.bx(c0 - r, c0 + r, u - r, u + r, z0, z0 + h, c, ink=ink)
    for zz, rr in ((z0 + h - 0.06, r * 0.9), (z0 + h * 0.5, r * 0.7)):
        lo, hi = min(a, b) + r, max(a, b) - r
        if axis == 'x':
            k.bx(lo, hi, c0 - rr, c0 + rr, zz - rr, zz + rr, c, ink=ink)
        else:
            k.bx(c0 - rr, c0 + rr, lo, hi, zz - rr, zz + rr, c, ink=ink)


def polyline(k, pts, t, c, n, ink=True, closed=False, cols=None):
    """beams along a polyline lying in a plane with normal n: neighbouring segments stand 6 mm apart along n, so the
    faces they share where they meet never z-fight"""
    pts = list(pts) + ([pts[0]] if closed else [])
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        e = 0.003 if i % 2 else -0.003
        k.beam((p[0] + n[0] * e, p[1] + n[1] * e, p[2] + n[2] * e), (q[0] + n[0] * e, q[1] + n[1] * e, q[2] + n[2] * e), t,
               (cols[i % len(cols)] if cols else c), ink=ink)


def lantern(k, x, y, z, s=1.0, ink=False):
    """hanging hurricane lantern (a glowing glass and its cap); z = its top"""
    k.cyl(x, y, z - 0.26 * s, 0.075 * s, 0.07 * s, 0.2 * s, 'fire2', seg=5, ink=ink)
    k.cyl(x, y, z - 0.065 * s, 0.09 * s, 0.02 * s, 0.065 * s, 'iron2', seg=5, ink=ink, caps=False)
    k.cyl(x, y, z - 0.3 * s, 0.085 * s, 0.085 * s, 0.04 * s, 'iron2', seg=5, ink=ink)


def crate(k, x, y, z, sx, sy, sz, c='plank', c2='plank2', ink=True):
    """slatted wooden crate (box + edge battens)"""
    k.bx(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, z, z + sz, c, ink=ink)
    b = 0.035
    for yy in (y - sy / 2 - b / 2, y + sy / 2 + b / 2):
        k.bx(x - sx / 2, x + sx / 2, yy - b / 2, yy + b / 2, z + sz * 0.42, z + sz * 0.58, c2, ink=False)
    for xx in (x - sx / 2 - b / 2, x + sx / 2 + b / 2):
        k.bx(xx - b / 2, xx + b / 2, y - sy / 2, y + sy / 2, z + sz * 0.42, z + sz * 0.58, c2, ink=False)
    FD.crate_detail(k, x, y, z, sx, sy, sz, c2)


def barrel(k, x, y, z, r=0.3, h=0.85, c='plank2', hoop='iron', ink=True):
    k.cyl(x, y, z, r * 0.88, r, h * 0.5, c, seg=8, ink=ink, caps=False)
    k.cyl(x, y, z + h * 0.5, r, r * 0.88, h * 0.5, c, seg=8, ink=ink)
    for zz in (z + 0.1 * h, z + 0.85 * h):
        k.cyl(x, y, zz, r * 0.94 + 0.012, r * 0.94 + 0.012, 0.045, hoop, seg=8, caps=False, ink=False)
    FD.barrel_hoops(k, x, y, z, r, h, hoop)


def sack(k, rnd, x, y, z, s=1.0, c='canvas2'):
    pts = []
    for i in range(6):
        a = i / 6 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        pts.append((x + math.cos(a) * 0.26 * s, y + math.sin(a) * 0.2 * s, z))
        pts.append((x + math.cos(a) * 0.24 * s, y + math.sin(a) * 0.18 * s, z + 0.32 * s))
    pts.append((x, y, z + 0.5 * s))
    k.hullp(pts, c, ink=False)
