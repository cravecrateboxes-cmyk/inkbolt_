"""Shared bits of kit-scrapyard (Rustmoor Salvage, a scrapyard at night): palette, heights, the SK kit and the helpers
the stacks (sy_stacks.py), the titan graveyard (sy_titans.py) and the walls use. Not an asset family itself (no fam_
prefix); fam_kit_scrapyard.py builds the GLB.

Conventions (src/data/themes.js, kit_base.py): 1 m = 1 ASCII cell; a piece's origin is the centre of its cell /
footprint at floor level; Blender Z-up; one-sided pieces face Blender -Y (game +Z, south, toward the zone entry). Run
pieces (rotate: 'run') are modelled along Blender X. Shapes marked ink=False get no outline shell.

Night: the yard is lit by its own lamps. Lamp lenses, lit windows, reactor cores and screens are drawn into a <Piece>_Glow
companion (unlit in game, theme.glow; the ink outline stays in the piece); red warning beacon domes go into a second
companion <Piece>_Blink that the theme blinks. Pools of light are painted on the ground (each kind at its own height).
The giant wrecks are designed here as derelict war machines (they are not the game's robot models).
"""
import math
import random

import bpy  # noqa: F401  (must load before bmesh/mathutils)
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, srt, rock_pts, clamp_pts
from foundry_common import slab, slab3, oslab, tube, drumx, drumy, frame_at, ring4
from gem_base import GK

FAM = 'kit-scrapyard'
PFX = 'KIT_SCRAPYARD_'
ib_lib.GLB[FAM] = 'fps-kit-scrapyard.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
WALL_H = 9.6         # scrap bank wall modules (theme wall.height 9.0 is the collision)
TRAIL_H = 6.0        # trail fence

ib_lib.PALETTES[FAM] = BASE + [
    # ground, concrete
    ('dirt', '#3B3A41'), ('dirt2', '#2B2B32'), ('conc', '#5D616D'), ('conc2', '#474B57'),
    # scrap metal
    ('rust', '#74462F'), ('rust2', '#563424'), ('rustL', '#8E5C3A'), ('steel', '#8C96A5'),
    ('steel2', '#646D7C'), ('steelDark', '#2A2F3A'), ('gun', '#4B5363'), ('gun2', '#39404E'),
    ('gunL', '#6D778A'), ('chrome', '#BAC4D0'),
    # car paint (faded), glass, tyres -- the cars' cells are repainted per copy (theme symbol option `paint`)
    ('carR', '#8C4541'), ('carB', '#475F80'), ('carG', '#566B4C'), ('carY', '#A88F47'),
    ('carW', '#A2A6AA'), ('carT', '#467270'), ('carO', '#9C6441'), ('carP', '#62546F'),
    ('glassD', '#2B3B4D'), ('tire', '#1E1D23'),
    # the derelict war machines' paint
    ('bone', '#B7AF9A'), ('bone2', '#8D8673'), ('olive', '#5E6647'), ('olive2', '#474D36'),
    ('crimson', '#8F3137'), ('crimson2', '#64222A'), ('navy', '#36435E'), ('navy2', '#283147'),
    # light: sodium lamps, dead reactors' cold blue, red beacons, dead lenses
    ('sodium', '#FFB34D'), ('sodiumL', '#FFE7B3'), ('cyan', '#52D8F0'), ('cyanL', '#C8F7FF'),
    ('cyanD', '#25758E'), ('alarm', '#FF3B2F'), ('alarmD', '#7E1D19'), ('lensD', '#151C27'),
    ('lensR', '#3E5670'), ('pool', '#5A5145'), ('pool2', '#71644F'), ('poolB', '#36485A'),
    # dead tech
    ('screenD', '#1C272C'), ('beige', '#A9A18B'), ('beige2', '#7F7967'), ('pcb', '#2F5B3B'),
    ('copper', '#B26B3B'), ('cable', '#18181E'), ('wood', '#7B5D3D'), ('wood2', '#5A432A'),
    # paint, signs, the far backdrop
    ('hazard', '#D7A52D'), ('sign', '#E3DDC9'), ('far', '#151A28'), ('far2', '#1D2436'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
PAL_NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]
CARS = ('carR', 'carB', 'carG', 'carY', 'carW', 'carT', 'carO', 'carP')

# floor decal heights (m above the floor): one level per kind, 8 mm apart, clear of the engine's floor lines
# (pool_disc draws its inner disc 4 mm above its outer one)
Z = {'S': 0.019, 'N': 0.027, 'E': 0.035, 'W': 0.043, 'tower': 0.051, 'blue': 0.059, 'oil': 0.067, 'piece': 0.075,
     'piece2': 0.083, 'hatch': 0.091}


# ================================================================ the kit: glow + blink companions, walkable boxes
class SK(GK):
    """GK (walkable boxes, glowing shapes in <Piece>_Glow) + warning beacons whose domes go into <Piece>_Blink."""

    def __init__(self, pal, prefix, hull_t):
        super().__init__(pal, prefix, hull_t)
        self.blinks = []

    def begin(self, rot=0):
        super().begin(rot)
        self.b = Kit(self.pal, self.prefix, self.hull_t)
        self.b.begin(rot)
        self.b.tris = self.tris
        return self

    def _sync(self):
        super()._sync()
        self.b.m.parent = self.m.parent.copy()

    def beacon(self, x, y, z, r=0.16, h=0.26):
        """Warning beacon: a dark base (lit, outlined), a red dome that blinks (outline in the piece)."""
        self.cyl(x, y, z, r * 1.2, r * 1.2, 0.08, 'steelDark', seg=8)
        self.b.cyl(x, y, z + 0.08, r, r * 0.55, h, 'alarm', seg=8, ink=False)
        self.h.cyl(x, y, z + 0.08, r, r * 0.55, h, 'alarm', seg=8, ink=True)

    def finish(self, name, bevel=0.0, ao=False):
        obj = super().finish(name, bevel, ao)
        if len(self.b.m.bm.faces):
            self.b.finish(name + '_Blink')
            self.blinks.append(name)
        else:
            self.b.m.bm.free()
        return obj


# ================================================================ shapes
def hull_box(k, cx, cy, cz, sx, sy, sz, c, yaw=0.0, pitch=0.0, roll=0.0, ink=True):
    """A box by centre / size turned by yaw (Z), pitch (X) and roll (Y), as a convex hull (so it can be coloured per
    face and tilted freely)."""
    from mathutils import Matrix
    R = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, 'X') @ Matrix.Rotation(math.radians(roll), 3, 'Y')
    pts = []
    for dx in (-0.5, 0.5):
        for dy in (-0.5, 0.5):
            for dz in (-0.5, 0.5):
                v = R @ Vector((dx * sx, dy * sy, dz * sz))
                pts.append((cx + v.x, cy + v.y, cz + v.z))
    return k.hullp(pts, c, ink=ink)


def tbox(k, cx, cy, cz, sx, sy, sz, c, yaw=0.0, pitch=0.0, roll=0.0, ink=True):
    """Tilted box (bxr): centre, size, rotation in degrees about X, Y, Z."""
    k.bxr(cx, cy, cz, sx, sy, sz, c, rot=(pitch, roll, yaw), ink=ink)


def pool_disc(k, x, y, z, r, seed, sx=1.0, sy=1.0, c1='pool', c2='pool2', n=16):
    rnd = random.Random(seed)
    k.disc(x, y, z, r, c1, n=n, rnd=rnd, jag=0.05, sx=sx, sy=sy)
    k.disc(x, y, z + 0.004, r * 0.5, c2, n=12, rnd=rnd, jag=0.06, sx=sx, sy=sy)


def sodium_head(k, x, y, z, s=-1, w=0.56, h=0.36, tilt=0.0):
    """A sodium floodlight facing -Y (s=-1) / +Y: a dark box with a cowl and a glowing lens."""
    y0, y1 = srt(y, y - s * 0.32)
    k.bx(x - w / 2, x + w / 2, y0, y1, z - h / 2, z + h / 2, 'steelDark')
    k.bx(x - w / 2 - 0.03, x + w / 2 + 0.03, *srt(y - 0.02 * s, y + 0.1 * s), z + h / 2, z + h / 2 + 0.04, 'gun2', ink=False)
    k.gbx(x - w / 2 + 0.05, x + w / 2 - 0.05, *srt(y + s * 0.004, y + s * 0.03), z - h / 2 + 0.05, z + h / 2 - 0.05, 'sodiumL', hull=False)


def text(k, s, x, y, z, cap, col, face='y-', maxw=None, font='display', valign='b'):
    import ib_text
    ib_text.draw(k, s, x, y, z, cap, col, face=face, font=font, maxw=maxw, valign=valign)


def sign_board(k, x, y, z, w, h, lines, bg='sign', fg='ink', s=-1, rim='hazard', post=None):
    """A painted steel sign facing -Y (s=-1) / +Y: plate, rim bands, lines [(text, cap, colour|None)] from the top."""
    y0, y1 = srt(y, y - s * 0.06)
    k.bx(x - w / 2, x + w / 2, y0, y1, z, z + h, 'steelDark')
    yf = y + s * 0.003
    k.qy(x - w / 2 + 0.04, x + w / 2 - 0.04, z + 0.04, z + h - 0.04, yf, s, bg)
    if rim:
        k.qy(x - w / 2 + 0.06, x + w / 2 - 0.06, z + h - 0.12, z + h - 0.07, yf + s * 0.003, s, rim)
        k.qy(x - w / 2 + 0.06, x + w / 2 - 0.06, z + 0.07, z + 0.12, yf + s * 0.003, s, rim)
    zz = z + h - 0.16
    for (t, cap, col) in lines:
        zz -= cap
        text(k, t, x, yf + s * 0.006, zz, cap, col or fg, face='y-' if s < 0 else 'y+', maxw=w - 0.2)
        zz -= cap * 0.35


def tyre(k, x, y, z, r=0.36, w=0.24, axis='z', c='tire', seg=8, hub=True, ink=True):
    """A tyre (a short cylinder with a dark hub disc), its axis along 'x' / 'y' / 'z'; z is the centre height."""
    rot = {'z': (0, 0, 0), 'x': (0, 90, 0), 'y': (90, 0, 0)}[axis]
    if axis == 'z':
        k.cyl(x, y, z - w / 2, r, r, w, c, seg=seg, ink=ink)
        if hub:
            vdisc(k, x, y, z + w / 2 + 0.004, r * 0.48, 'steel2', axis='z', s=1)
    elif axis == 'x':
        k.cyl(x - w / 2, y, z, r, r, w, c, seg=seg, rot=rot, ink=ink)
        if hub:
            vdisc(k, x + w / 2 + 0.004, y, z, r * 0.48, 'steel2', axis='x', s=1)
    else:
        k.cyl(x, y + w / 2, z, r, r, w, c, seg=seg, rot=rot, ink=ink)
        if hub:
            vdisc(k, x, y - w / 2 - 0.004, z, r * 0.48, 'steel2', axis='y', s=-1)


def lattice(k, x0, x1, y0, y1, z0, z1, c='steel2', t=0.07, every=1.6, braces=True):
    """A square lattice mast / frame between (x0, y0) and (x1, y1), z0 to z1: four corner legs, rings and X bracing
    (thin beams, inked)."""
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        k.bx(x - t, x + t, y - t, y + t, z0, z1, c)
    n = max(1, int(round((z1 - z0) / every)))
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        if i:   # rings: the sides along y sit 8 mm higher than those along x (their ends cross at the legs)
            for j, (a, b) in enumerate((((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))):
                zz = z + 0.008 * (j % 2) - 0.06
                k.beam((a[0], a[1], zz), (b[0], b[1], zz), t * (0.8 if j % 2 == 0 else 0.7), c, ink=False)
        if braces and i < n:
            za, zb = z, z0 + (z1 - z0) * (i + 1) / n
            sg = 1 if i % 2 else -1
            for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                p, q = (a, b) if sg > 0 else (b, a)
                k.beam((p[0], p[1], za + 0.05), (q[0], q[1], zb - 0.05), t * 0.6, c, ink=False)


def scrap_fn(seed, base=('rust', 'rust2', 'steel2', 'gun', 'gun2', 'steel', 'steelDark', 'rust2', 'gunL'), top='rustL'):
    """Face colour by a hash of its centre: a jumble of rusty and grey scrap; faces looking up a shade lighter."""
    def fn(f):
        c = f.calc_center_median()
        h = math.sin(c.x * 12.9898 + c.y * 78.233 + c.z * 37.719 + seed) * 43758.5453
        h -= math.floor(h)
        if f.normal.z > 0.75:
            return top if h < 0.5 else base[int(h * len(base)) % len(base)]
        return base[int(h * len(base)) % len(base)]
    return fn


def heap(k, cx, cy, rx, ry, h, seed, n=9, fn=None, z0=0.0, top=4, waist=(0.35, 0.6)):
    """A faceted scrap mound (convex hull of a ring at the floor, a waist ring and a few top points)."""
    rnd = random.Random(seed)
    return k.hullp(rock_pts(rnd, (cx, cy), rx, ry, h, z0=z0, n=n, top=top, waist=waist), fn or scrap_fn(seed))


def plate(k, a, b, w, t, c, up=None, ink=True):
    """A flat armour / steel plate from point a to point b (its length), w wide, t thick; `up` is its face normal
    direction hint (default: as level as possible)."""
    a, b = Vector(a), Vector(b)
    ax = (b - a).normalized()
    up = Vector(up) if up else Vector((0, 0, 1))
    side = ax.cross(up)
    if side.length < 1e-4:
        side = ax.cross(Vector((1, 0, 0)))
    side.normalize()
    nrm = side.cross(ax).normalized()
    pts = []
    for p in (a, b):
        for s in (-1, 1):
            for u in (-1, 1):
                q = p + side * (w / 2 * s) + nrm * (t / 2 * u)
                pts.append((q.x, q.y, q.z))
    return k.hullp(pts, c, ink=ink)


def ibeam(k, a, b, h=0.36, w=0.24, c='rust', ink=True):
    """An I-beam (web + two flanges) from a to b; the web stands vertical where it can."""
    a, b = Vector(a), Vector(b)
    ax = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    side = ax.cross(up).normalized()
    upn = side.cross(ax).normalized()
    plate(k, a + ax * 0.012, b - ax * 0.012, h - 0.04, 0.035, c, up=tuple(side), ink=ink)   # web ends inset
    for s in (-1, 1):
        o = upn * (s * (h / 2 - 0.02))
        plate(k, a + o, b + o, w, 0.04, c, up=tuple(upn), ink=ink)


def plate_ramp(k, xa, xb, y0, y1, z0, z1, n, c='olive', c2='olive2'):
    """A ramp of armour plate laid from x = xa (z0) up to x = xb (z1) across y0..y1: walkable stepped boxes (rise
    (z1 - z0) / n <= 0.35, treads >= 0.5 m) under one sloped plate with weld seams and side stringers."""
    run, rise = (xb - xa) / n, (z1 - z0) / n
    assert rise <= 0.35 + 1e-6 and abs(run) >= 0.5 - 1e-6, (rise, run)
    for i in range(n):
        a, b = srt(xa + run * i, xa + run * (i + 1))
        k.colw(a, b, y0, y1, z0, z0 + rise * (i + 1))
    t = 0.1
    ztop = lambda x: z0 + 0.06 + (z1 - z0 - 0.06) * (x - xa) / (xb - xa)
    k.hullp([(xa, y0, z0), (xa, y1, z0), (xb, y0, z1 - t), (xb, y1, z1 - t),
             (xa, y0, z0 + 0.06), (xa, y1, z0 + 0.06), (xb, y0, z1), (xb, y1, z1)], c)
    slope = (z1 - z0 - 0.06) / (xb - xa)
    for j in (1, 2):
        xs = xa + (xb - xa) * j / 3
        p = [(xs - 0.02, y0 + 0.05), (xs + 0.02, y0 + 0.05), (xs + 0.02, y1 - 0.05), (xs - 0.02, y1 - 0.05)]
        k.poly([(x, y, ztop(x) + 0.004) for (x, y) in p], c2, (-slope, 0, 1))
    for y in (y0 + 0.06, y1 - 0.06):
        oslab(k, (xa, y, z0 - 0.02), (xb, y, z1 - 0.3), 0.06, 0.14, 0.06, 0.14, 'steelDark')


def cable(k, a, b, sag, t, c='cable', n=6, ink=False):
    """A sagging cable from a to b: a chain of n square links, every other one turned 45 degrees about its axis, so
    the faces of neighbouring links (nearly in line where the sag is small) are never parallel."""
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        f = i / n
        p = a.lerp(b, f)
        p.z -= sag * 4 * f * (1 - f)
        pts.append(p)
    for i in range(n):
        p, q, ax, side, up, L = frame_at(tuple(pts[i]), tuple(pts[i + 1]))
        ring = []
        for j in range(4):
            ang = (j + 0.5) * math.pi / 2 + (math.pi / 4 if i % 2 else 0.0)
            o = side * math.cos(ang) * t * 0.7 + up * math.sin(ang) * t * 0.7
            ring += [tuple(p + o), tuple(q + o)]
        k.hullp(ring, c, ink=ink)


def vdisc(k, x, y, z, r, c, axis='y', s=-1, n=8):
    """A flat painted disc (a hub, a wheel pressed into a bale, a lens rim) facing -/+ axis (s), as one polygon."""
    pts = []
    for i in range(n):
        a = (i + 0.5) / n * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        pts.append((x + u, y, z + v) if axis == 'y' else (x, y + u, z + v) if axis == 'x' else (x + u, y + v, z))
    k.poly(pts, c, (0, s, 0) if axis == 'y' else (s, 0, 0) if axis == 'x' else (0, 0, s))
