"""Shared bits of kit-gemmine (Glimmerdeep Colliery): palette, heights, the GK kit and the crystal helpers. Not an asset
family itself (no fam_ prefix); fam_kit_gemmine.py builds the GLB from gem_seam.py (zone 1, the working coal seam) and
gem_cavern.py (zone 2, the gem cavern).

The mine's timbering, rock faces, track, carts and lanterns come from the coal mine kit's helpers (fam_kit_coalmine.py,
imported, never rebuilt); walkable decks and stairs from the foundry kit's (foundry_common.py). The palette keeps every
colour name those helpers paint with, plus the gems and the violet cavern rock.

Conventions (src/data/themes.js, kit_base.py): 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint
at floor level; Blender Z-up; one-sided pieces face Blender -Y (game +Z, south, toward the zone entry). Run pieces
(rotate: 'run') are modelled along Blender X. Shapes marked ink=False get no outline shell.

Glowing gems (theme.glow): GK draws a gem's faces into a companion piece <Piece>_Glow (drawn unlit by the engine, so
the crystals shine in the dark mine) and only the gem's ink outline shell into the piece itself, so the glowing crystal
still sits inside a comic outline and nothing is drawn twice. Facets are shaded by a fixed light direction (light /
mid / dark cell of the gem's colour), which keeps them reading as cut, faceted stones without scene lighting.
"""
import math
import random

import bpy  # noqa: F401  (must load before bmesh/mathutils)
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, srt, rock_pts, clamp_pts
from foundry_common import FK, frame_at
import fam_kit_coalmine as CM

FAM = 'kit-gemmine'
PFX = 'KIT_GEMMINE_'
ib_lib.GLB[FAM] = 'fps-kit-gemmine.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
CEIL = 9.0           # zone 1 roof (theme env.ceiling)
WALL_H = 9.4         # zone 1 wall modules, gate bulkhead, trail
CAVE_H = 18.4        # zone 2 cavern walls (no theme ceiling there: the "@layer 18" roof pieces close it)
ROOF_Y = 18.0

ib_lib.PALETTES[FAM] = BASE + [
    # the coal mine's colours (names the imported coal mine helpers paint with)
    ('rock', '#54493F'), ('rockB', '#463D36'), ('rock2', '#362F2A'), ('rock3', '#7A6A57'),
    ('rockBack', '#2E2724'), ('coal', '#25242B'), ('coal2', '#383744'), ('glint', '#9AA6C8'),
    ('timber', '#A8743F'), ('timber2', '#87592F'), ('timberEnd', '#D6A66C'), ('plank', '#B98653'),
    ('plank2', '#94653A'), ('steel', '#959FAA'), ('steel2', '#6E7783'), ('steelDark', '#434954'),
    ('lamp', '#FFD66B'), ('lampHot', '#FFF6CF'), ('pool', '#7C6450'), ('pool2', '#9C7F5C'),
    ('hood', '#2F4A3E'), ('dust', '#3B3430'), ('hazard', '#F2C230'), ('rope', '#C9B28A'),
    ('sack', '#B39A70'), ('sack2', '#958058'), ('cart', '#B4503A'), ('cart2', '#8C3C2D'),
    ('water', '#2C3B48'), ('waterG', '#7C9AB2'), ('mach', '#E8B530'), ('mach2', '#BF8D22'),
    ('rubber', '#2A2830'), ('cable', '#1F1D1C'), ('ceilRock', '#3A322D'), ('ceilRock2', '#2C2522'),
    ('board', '#2E3B33'), ('chalk', '#E9E4D6'), ('drum', '#3F6A8C'), ('drum2', '#335774'),
    # gems: diamond (white / ice blue), ruby, emerald, sapphire -- light / mid / dark facets
    ('dia', '#CFEFFF'), ('diaD', '#7DB4E6'), ('ruby', '#E3264B'), ('rubyL', '#FF8FA6'),
    ('rubyD', '#8E1232'), ('emer', '#1FC46C'), ('emerL', '#93F7B6'), ('emerD', '#0C7643'),
    ('saph', '#2F68EA'), ('saphL', '#97BCFF'), ('saphD', '#1A3796'),
    # the cavern: violet-grey rock, lit ledges, the black of the chasm; felt on the sorting tables
    ('cave', '#4B4560'), ('cave2', '#3A354C'), ('cave3', '#6E6585'), ('pit', '#07060A'), ('felt', '#35584A'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# floor decal heights (m above the floor): one level per kind, >= 4 mm apart (engine floor lines at 8 - 15.5 mm)
POOL_Z = dict(CM.POOL_Z)
POOL_Z.update({'cS': 0.020, 'cN': 0.028, 'cE': 0.036, 'cW': 0.044, 'table': 0.060, 'heart': 0.068, 'plat': 0.092,
               'chute': 0.064, 'winch': 0.112, 'fan': 0.116, 'hoist': 0.120, 'gal': 0.124, 'sort': 0.128})
Z_DECK = 0.018       # plank decking under the sorting station (floor layer)

LIGHT = Vector((0.35, -0.55, 0.76)).normalized()
GEM = {'dia': ('white', 'dia', 'diaD'), 'ruby': ('rubyL', 'ruby', 'rubyD'), 'emer': ('emerL', 'emer', 'emerD'),
       'saph': ('saphL', 'saph', 'saphD')}
KINDS = ('ruby', 'emer', 'saph', 'dia')


def gem_fn(kind):
    L, M, D = GEM[kind]

    def fn(f):
        d = f.normal.dot(LIGHT)
        return L if d > 0.5 else (M if d > -0.15 else D)
    return fn


class GK(FK):
    """FK (walkable boxes) + glowing shapes: g* calls draw the faces into the piece's _Glow companion and the ink
    outline shell into the piece itself."""

    def __init__(self, pal, prefix, hull_t):
        super().__init__(pal, prefix, hull_t)
        self.glows = []

    def begin(self, rot=0):
        super().begin(rot)
        self.g = Kit(self.pal, self.prefix, self.hull_t)
        self.g.begin(rot)
        self.g.tris = self.tris
        self.h = Kit(self.pal, self.prefix, self.hull_t)
        self.h.begin(rot)
        return self

    def _sync(self):
        self.g.m.parent = self.m.parent.copy()
        self.h.m.parent = self.m.parent.copy()

    def push(self, x, y, deg=0, z=0, sz=1.0, s=1.0):
        super().push(x, y, deg, z, sz, s)
        self._sync()

    def pop(self):
        super().pop()
        self._sync()

    def ghull(self, pts, color, hull=True):
        self.g.hullp(pts, color, ink=False)
        if hull:
            self.h.hullp(pts, 'ink')

    def gcyl(self, x, y, z, r1, r2, h, c, seg=8, rot=(0, 0, 0), hull=True):
        self.g.cyl(x, y, z, r1, r2, h, c, seg=seg, rot=rot, ink=False)
        if hull:
            self.h.cyl(x, y, z, r1, r2, h, c, seg=seg, rot=rot, ink=True)

    def gbx(self, x0, x1, y0, y1, z0, z1, c, hull=True):
        self.g.bx(x0, x1, y0, y1, z0, z1, c, ink=False)
        if hull:
            self.h.bx(x0, x1, y0, y1, z0, z1, c, ink=True)

    def gquad_y(self, x0, x1, z0, z1, y, s, c):
        self.g.qy(x0, x1, z0, z1, y, s, c)

    def finish(self, name, bevel=0.0, ao=False):
        obj = super().finish(name, bevel, ao)
        if len(self.h.m.bm.faces):
            tmp = build_object(self.prefix + name + '_ghull', self.h.m, 0, self.hull_t)
            hull_only(tmp)
            join_into(obj, tmp)
            self.tris[self.prefix + name] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        else:
            self.h.m.bm.free()
        if len(self.g.m.bm.faces):
            self.g.finish(name + '_Glow')
            self.glows.append(name)
        else:
            self.g.m.bm.free()
        return obj


# ================================================================ crystals
def crystal(k, kind, a, b, r, shape=None, glow=True, outline=True):
    """One crystal from its root a (buried in the rock) to its tip b, radius r. Shapes: 'oct' diamond bipyramid
    (square girdle), 'hex' sapphire spindle (hexagonal prism to a point), 'flat' ruby / emerald hexagonal prism with a
    bevelled flat top. glow=False draws it as a lit, outlined shape (loose stones in crates)."""
    shape = shape or ({'dia': 'oct'}.get(kind, 'spike') if r < 0.1 else {'dia': 'oct'}.get(kind, 'hex') if r < 0.3 else
                      {'dia': 'oct', 'saph': 'hex'}.get(kind, 'flat'))
    a, b, ax, side, up, L = frame_at(a, b)
    pts = []
    if shape == 'spike':   # small stones: a four-sided prism to a point (cheap)
        sh = a + ax * L * 0.62
        for i in range(4):
            t = i * math.pi / 2 + 0.4
            pts.append(a + side * math.cos(t) * r * 0.85 + up * math.sin(t) * r * 0.85)
            pts.append(sh + side * math.cos(t) * r + up * math.sin(t) * r)
        pts.append(b)
    elif shape == 'oct':
        g = a + ax * L * 0.42
        for i in range(4):
            t = i * math.pi / 2 + math.pi / 4
            pts.append(g + side * math.cos(t) * r + up * math.sin(t) * r)
        pts += [a + ax * L * 0.05, b]
    else:
        sh = a + ax * L * (0.7 if shape == 'hex' else 0.9)
        for i in range(6):
            t = i / 6 * 2 * math.pi
            pts.append(a + side * math.cos(t) * r * 0.9 + up * math.sin(t) * r * 0.9)
            pts.append(sh + side * math.cos(t) * r + up * math.sin(t) * r)
            if shape == 'flat':
                pts.append(b + side * math.cos(t + math.pi / 6) * r * 0.62 + up * math.sin(t + math.pi / 6) * r * 0.62)
        if shape == 'hex':
            pts.append(b)
    P = [tuple(p) for p in pts]
    if glow:
        k.ghull(P, gem_fn(kind), hull=r >= 0.06 and outline)
    else:
        k.hullp(P, gem_fn(kind))


def cluster(k, kind, base, axis, n, length, r, seed, spread=0.55, glow=True, lo=0.55):
    """n crystals growing out of one point: the axis (a direction) tilted by up to `spread` (radians-ish) per crystal,
    lengths lo..1 of `length`; the biggest grows along the axis itself."""
    rnd = random.Random(seed)
    base, axis = Vector(base), Vector(axis).normalized()
    t1 = axis.orthogonal().normalized()
    t2 = axis.cross(t1).normalized()
    for i in range(n):
        if i == 0:
            d, L, rr = axis, length, r
        else:
            a = rnd.uniform(0, 2 * math.pi)
            s = rnd.uniform(0.35, 1.0) * spread
            d = (axis + t1 * math.cos(a) * s + t2 * math.sin(a) * s).normalized()
            L = length * rnd.uniform(lo, 0.92)
            rr = r * rnd.uniform(0.55, 0.85)
        off = (t1 * math.cos(i * 2.4) + t2 * math.sin(i * 2.4)) * (r * 0.6 if i else 0.0)
        a0 = base + off - d * rr * 0.8
        crystal(k, kind, tuple(a0), tuple(base + off + d * L), rr, glow=glow)


def lantern_g(k, x, y, z, s=1.0):
    """Miner's lantern hanging at (x, y), bail top at z: hood, base (lit, outlined) and a glowing glass."""
    k.bx(x - 0.01, x + 0.01, y - 0.01, y + 0.01, z - 0.12 * s, z, 'steelDark', ink=False)
    k.cyl(x, y, z - 0.2 * s, 0.11 * s, 0.05 * s, 0.08 * s, 'hood', seg=6)
    k.gcyl(x, y, z - 0.415 * s, 0.075 * s, 0.075 * s, 0.21 * s, 'lamp', seg=6)
    k.cyl(x, y, z - 0.47 * s, 0.1 * s, 0.1 * s, 0.05 * s, 'hood', seg=6, ink=False)


def bulb(k, x, y, z, s=1.0):
    """A bare bulb of a lamp string hanging from the cable at height z."""
    k.cyl(x, y, z - 0.07 * s, 0.03 * s, 0.03 * s, 0.07 * s, 'steelDark', seg=6, ink=False)
    k.gcyl(x, y, z - 0.205 * s, 0.05 * s, 0.07 * s, 0.13 * s, 'lampHot', seg=6)


def floodlight(k, x, y, z, s=-1, w=0.5, h=0.34):
    """Box floodlight facing -Y (s=-1) / +Y with a glowing lens."""
    y0, y1 = srt(y, y - s * 0.3)
    k.bx(x - w / 2, x + w / 2, y0, y1, z - h / 2, z + h / 2, 'steelDark')
    k.gbx(x - w / 2 + 0.05, x + w / 2 - 0.05, *srt(y + s * 0.004, y + s * 0.03), z - h / 2 + 0.05, z + h / 2 - 0.05, 'lampHot', hull=False)


def sign_board(k, x, y, z, w, h, lines, bg='board', fg='chalk', s=-1, rim='hazard', font='display'):
    """Painted board on two pins facing -Y (s=-1): a rim band top and bottom and lines [(text, cap, colour|None)]
    laid out from the top. Lettering: ib_text vector glyphs."""
    import ib_text
    y0, y1 = srt(y, y - s * 0.05)
    k.bx(x - w / 2, x + w / 2, y0, y1, z, z + h, 'plank2')
    yf = y + s * 0.003
    k.qy(x - w / 2 + 0.03, x + w / 2 - 0.03, z + 0.03, z + h - 0.03, yf, s, bg)
    if rim:
        k.qy(x - w / 2 + 0.05, x + w / 2 - 0.05, z + h - 0.1, z + h - 0.06, yf + s * 0.003, s, rim)
        k.qy(x - w / 2 + 0.05, x + w / 2 - 0.05, z + 0.06, z + 0.1, yf + s * 0.003, s, rim)
    zz = z + h - 0.14
    for (text, cap, col) in lines:
        zz -= cap
        ib_text.draw(k, text, x, yf + s * 0.006, zz, cap, col or fg, face='y-' if s < 0 else 'y+', font=font, maxw=w - 0.16)
        zz -= cap * 0.35


# ================================================================ decks, stairs, rails (walkable boxes)
def stairs_x(k, xa, xb, y0, y1, z0, z1, n, c='steel2', tread='hazard', rails=(True, True), timber=False):
    """Straight stair rising along X from x = xa (bottom, z0) to x = xb (top, z1) in n steps across y0..y1; the steps
    are walkable blocks solid to the floor (WCOL, like the foundry stairs); stringers, hand rails on the sides asked
    for in rails (-Y side, +Y side) with their collision. Each rise must stay <= 0.35 m, each tread >= 0.5 m."""
    sg = 1 if xb > xa else -1
    run = (xb - xa) / n
    rise = (z1 - z0) / n
    assert rise <= 0.35 + 1e-6 and abs(run) >= 0.5 - 1e-6, (rise, run)
    for i in range(n):
        a, b = srt(xa + run * i, xa + run * (i + 1))
        top = z0 + rise * (i + 1)
        if timber:
            k.bx(a + 0.01, b - 0.01, y0 + 0.04, y1 - 0.04, top - 0.08, top, 'plank' if i % 2 else 'plank2')
        else:
            k.bx(a + 0.01, b - 0.01, y0 + 0.04, y1 - 0.04, top - 0.07, top, c)
            nose = (b - 0.06, b) if sg > 0 else (a, a + 0.06)
            k.qz(nose[0], nose[1], y0 + 0.08, y1 - 0.08, top + 0.003, 1, tread)
        k.colw(a, b, y0, y1, z0, top)
    from foundry_common import oslab
    for y in (y0 + 0.03, y1 - 0.03):
        oslab(k, (xa, y, z0 + rise * 0.5 - 0.22), (xb, y, z1 - 0.22), 0.18, 0.03, 0.18, 0.03, 'timber2' if timber else 'steelDark')
    col = 'timber' if timber else 'hazard'
    for side, y in ((0, y0 - 0.055), (1, y1 + 0.055)):
        if not rails[side]:
            continue
        k.beam((xa + sg * 0.1, y, z0 + 1.0), (xb, y, z1 + 1.0), 0.07, col)
        ym = y + (0.012 if side == 0 else -0.012)
        k.beam((xa + sg * 0.1, ym, z0 + 0.55), (xb, ym, z1 + 0.55), 0.045, col, ink=False)
        for i in (0, n):
            xx = xa + run * min(i, n - 0.5)
            zz = z0 + rise * min(i, n)
            k.bx(xx - 0.04, xx + 0.04, y - 0.04, y + 0.04, zz, zz + 1.0, col)
        for i in range(n + 1):
            a, b = srt(xa + run * max(0, i - 1), xa + run * i) if i else srt(xa - sg * 0.01, xa + sg * 0.01)
            top = z0 + rise * i
            k.col(a, b, y - 0.07, y + 0.07, z0, top + 1.05)


def deck(k, x0, x1, y0, y1, z, t=0.12, c='plank', grate=False, slats=True, along='x'):
    """Walkable deck top at z: a slab with plank seams (or steel grating) and its WCOL box (solid t deep)."""
    if grate:
        k.bx(x0, x1, y0, y1, z - t, z, 'steel2')
        if along == 'x':
            for i in range(int((y1 - y0) / 0.25)):
                yy = y0 + 0.125 + i * 0.25
                k.qz(x0 + 0.06, x1 - 0.06, yy - 0.025, yy + 0.025, z + 0.003, 1, 'steelDark')
        else:
            for i in range(int((x1 - x0) / 0.25)):
                xx = x0 + 0.125 + i * 0.25
                k.qz(xx - 0.025, xx + 0.025, y0 + 0.06, y1 - 0.06, z + 0.003, 1, 'steelDark')
    else:
        k.bx(x0, x1, y0, y1, z - t, z, c)
        if slats:
            if along == 'x':
                n = int((y1 - y0) / 0.3)
                for i in range(1, n):
                    yy = y0 + (y1 - y0) * i / n
                    k.qz(x0 + 0.03, x1 - 0.03, yy - 0.012, yy + 0.012, z + 0.003, 1, 'plank2')
            else:
                n = int((x1 - x0) / 0.3)
                for i in range(1, n):
                    xx = x0 + (x1 - x0) * i / n
                    k.qz(xx - 0.012, xx + 0.012, y0 + 0.03, y1 - 0.03, z + 0.003, 1, 'plank2')
    k.colw(x0, x1, y0, y1, z - t, z)


def rail_x(k, x0, x1, y, z, c='hazard', post=1.5, h=1.1, kick=True):
    from foundry_common import guard_rail
    guard_rail(k, x0, x1, y, z, h=h, post=post, c=c, kick=kick)


def rail_y(k, y0, y1, x, z, c='hazard', post=1.5, h=1.1, kick=True):
    from foundry_common import guard_rail
    guard_rail(k, y0, y1, x, z, h=h, post=post, c=c, axis='y', kick=kick)


def post(k, x, y, z0, z1, c='timber', w=0.13, col=True):
    k.bx(x - w, x + w, y - w, y + w, z0, z1, c)
    if col:
        k.col(x - w, x + w, y - w, y + w, z0, z1)


# ================================================================ rock faces (both zones; cheaper than the coal mine's)
def face_loft(k, seed, lv, edge_y, top, color, amp=0.15, seam=None, depth=0.12, wander=0.22, lo=-1.4, rise=0.0):
    """A 1 m rock face module facing -Y as an open loft through ONE random middle station (two facet columns, the
    coal mine kit's lofts have two middle stations): the shared edge profile edge_y at the levels lv at both ends, so
    modules run on into one continuous face (rise: the top slopes up this much to the back, so the overhanging tops
    of two walls meeting in a corner never share a plane); seam = (i0, i1) levels that stand proud by `depth` (a coal seam); the
    back is left open (only rock or the zone's outside is ever behind it), the top runs back to y +0.5 at `top`."""
    rnd = random.Random(seed)
    ys, lvm = [], [lv[0]]
    for i, y in enumerate(edge_y):
        d = rnd.uniform(-amp, amp)
        if seam and seam[0] <= i <= seam[1]:
            d = -depth - rnd.uniform(0, 0.012)
        ys.append(max(lo, min(-0.1, y + d)))
    for i in range(1, len(lv) - 1):
        lvm.append(lv[i] + (0 if seam and seam[0] <= i <= seam[1] else rnd.uniform(-wander, wander)))
    lvm.append(lv[-1])
    prof = lambda yy, ll: [(y, z) for y, z in zip(yy, ll)] + [(0.5, top + rise)]
    k.loft([(-0.5, prof(edge_y, lv)), (rnd.uniform(-0.18, 0.18), prof(ys, lvm)), (0.5, prof(edge_y, lv))], color, baffle='rock2')
