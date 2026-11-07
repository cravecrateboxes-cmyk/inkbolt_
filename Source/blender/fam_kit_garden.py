"""INKBOLT asset family: kit-garden (Wide Garden Playground: a sunny public park).

A wide public garden on a sunny afternoon: lawns with mown stripes, gravel paths and paving, clipped yew hedges as the
zone walls (brick dwarf walls and brick gate piers near the gates), flower beds, low box hedges, picket fences, trees,
benches, picnic tables, lamps, urns, a fountain, a gazebo, a potting shed and a sandpit; and the playgrounds: a play
tower, the big three-tower play fort with bridges, and a pirate play ship. The playgrounds are climbable for the
player AND the robots: their decks, stair steps, ramps, bridge planks, slide beds and the gazebo floor carry walkable
collision boxes (<Piece>_WCOL<n> empties; see src/game/zones.js), everything else plain _COL boxes.

Conventions (see src/data/themes.js and kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * Wall modules ('#') face Blender -Y (game +Z); the theme uses wall.facing = 'open'.
  * Playground pieces are written in PLAN coordinates (x east, z south = game axes; Blender y = -z) through the Plan
    helper so the deck / stair / bridge layout reads like the zone map.
  * Deck tops at 2.1 m (2.7 m for the fort's lookout): the slab underside sits at 1.95 m, so the player (1.7 m) and the
    robots walk under the decks and bridges. Stairs rise 0.3 m per 0.5 m step, ramps 0.21 m, slides 0.3 m: every
    rise is within the player's 0.35 m step-up and the robots' 0.4 m nav step. Climbing walls rise 0.3 m per 0.3 m
    (the player walks up them; robots' nav never links them: cells 0.5 m apart differ by 0.6 m).
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_base import Kit, rz, srt, rock_pts, shutter_hull

FAM = 'kit-garden'
PFX = 'KIT_GARDEN_'
ib_lib.GLB[FAM] = 'fps-kit-garden.glb'
ib_lib.CFG[FAM] = (0.015, 0.02)
HULL_T = 0.02
WALL_H = 3.4          # hedge height (= theme wall.height = trail height)
DECK = 2.1            # play deck top
TALL = 2.7            # the fort's lookout deck
SLAB = 0.15           # deck slab thickness

ib_lib.PALETTES[FAM] = BASE + [
    ('grass', '#7CC35A'), ('grass2', '#8DCF68'), ('hedge', '#3F8F3A'), ('hedge2', '#55A84A'), ('hedge3', '#2E7230'),
    ('leaf', '#5DB04A'), ('leaf2', '#83CC5C'), ('leafD', '#3B8239'), ('blossom', '#F6A9C4'), ('blossom2', '#E07BA0'),
    ('trunk', '#8A5A3C'), ('trunk2', '#6B4430'), ('brick', '#C8613F'), ('brick2', '#A44A30'), ('stone', '#DDD5C4'),
    ('stone2', '#B9B1A0'), ('gravel', '#DCCBA4'), ('gravel2', '#C2B08A'), ('wood', '#D49A5E'), ('wood2', '#B27A45'),
    ('woodD', '#7A4E2E'), ('paintG', '#3E8C6A'), ('paintG2', '#2C6A50'), ('paintW', '#F6F2E6'), ('plY', '#FFC93C'),
    ('plB', '#3D8BE0'), ('plB2', '#2C6CB8'), ('plO', '#FF8A2E'), ('plP', '#9B6BD8'), ('plG', '#45C07A'),
    ('plR', '#E8413B'), ('metal', '#AEB7C1'), ('metal2', '#7F8996'), ('rope', '#EBD49A'), ('sand', '#F2DA9C'),
    ('sand2', '#DCC07C'), ('water', '#5EC2E6'), ('water2', '#A8E6F6'), ('soil', '#6E4A33'), ('flY', '#FFDF4A'),
    ('flP', '#B56AE2'), ('flO', '#FF9A3C'), ('roofR', '#C9503F'), ('roofS', '#56677A'), ('house', '#F3E3C6'),
    ('house2', '#E2C59C'), ('houseB', '#A9C8DD'), ('far', '#79AE74'), ('far2', '#5C9460'), ('glass', '#9FD6EC'),
    ('lamp', '#FFF3C4'), ('mat', '#E58A6E'), ('mat2', '#4C9BD6'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

# floor decal heights (each kind its own, so overlapping decals of different pieces never z-fight)
ZD = {'path': 0.02, 'pave': 0.022, 'mat': 0.026, 'speck': 0.03, 'sea': 0.034, 'swingmat': 0.038}


class GKit(Kit):
    """Kit + walkable collision boxes (<Piece>_WCOL<n>)."""

    def begin(self, rot=0):
        Kit.begin(self, rot)
        self.wcols = []
        return self

    def wcol(self, x0, x1, y0, y1, z0, z1):
        self.wcols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        obj = Kit.finish(self, name, bevel, ao)
        P = self.base.to_3x3()
        for i, (x0, x1, y0, y1, z0, z1) in enumerate(self.wcols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_WCOL%d' % (self.prefix + name, i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        return obj


class Plan:
    """Plan-coordinate front end for a Kit: x east, z south (Blender y = -z), y up."""

    def __init__(self, k):
        self.k = k

    def bx(self, x0, x1, z0, z1, y0, y1, c, ink=True):
        self.k.bx(x0, x1, -z1, -z0, y0, y1, c, ink=ink)

    def col(self, x0, x1, z0, z1, y0, y1):
        self.k.col(x0, x1, -z1, -z0, y0, y1)

    def wcol(self, x0, x1, z0, z1, y0, y1):
        self.k.wcol(x0, x1, -z1, -z0, y0, y1)

    def top(self, x0, x1, z0, z1, y, c):
        self.k.qz(x0, x1, -z1, -z0, y, 1, c)

    def fz(self, x0, x1, y0, y1, z, s, c):
        """Quad facing plan +z (s = 1, south) or -z (s = -1) at plan z."""
        self.k.qy(x0, x1, y0, y1, -z, -s, c)

    def fx(self, z0, z1, y0, y1, x, s, c):
        self.k.qx(-z1, -z0, y0, y1, x, s, c)

    def beam(self, a, b, t, c, ink=True):
        self.k.beam((a[0], -a[1], a[2]), (b[0], -b[1], b[2]), t, c, ink=ink)

    def cyl(self, x, z, y, r1, r2, h, c, seg=8, ink=True, rot=(0, 0, 0), caps=True):
        self.k.cyl(x, -z, y, r1, r2, h, c, seg=seg, ink=ink, rot=rot, caps=caps)

    def hull(self, pts, c, ink=True):
        return self.k.hullp([(x, -z, y) for (x, z, y) in pts], c, ink=ink)

    def sph(self, x, z, y, r, c, seg=(8, 5), scale=(1, 1, 1), ink=True):
        self.k.sph(x, -z, y, r, c, seg=seg, scale=scale, ink=ink)


# ================================================================ foliage helpers
def clumps(k, face, x0, x1, z0, z1, rnd, n, cols=('hedge2', 'hedge3'), d=0.503):
    """Irregular leaf clumps painted on a vertical face (flat, 3 mm proud). face: '-y', '+y', '-x', '+x'."""
    for i in range(n):
        u = x0 + (x1 - x0) * (i + rnd.uniform(0.15, 0.85)) / n
        v = rnd.uniform(z0 + 0.25, z1 - 0.3)
        r = rnd.uniform(0.09, 0.16)
        pts2 = []
        for j in range(6):
            a = j / 6 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
            pts2.append((u + math.cos(a) * r * rnd.uniform(0.8, 1.15), v + math.sin(a) * r * rnd.uniform(0.75, 1.1)))
        c = cols[i % len(cols)]
        dd = d + 0.003 * (i % 2)
        if face == '-y':
            k.poly([(p[0], -dd, p[1]) for p in pts2], c, (0, -1, 0))
        elif face == '+y':
            k.poly([(p[0], dd, p[1]) for p in pts2], c, (0, 1, 0))
        elif face == '-x':
            k.poly([(-dd, p[0], p[1]) for p in pts2], c, (-1, 0, 0))
        else:
            k.poly([(dd, p[0], p[1]) for p in pts2], c, (1, 0, 0))


def blob(k, cx, cy, cz, rx, ry, rz, color, seed, n=7, ink=True):
    """A faceted leafy lump (convex hull)."""
    rnd = random.Random(seed)
    z0 = cz - rz + 0.0037 * (seed % 7)   # flat bottoms of neighbouring lumps never share a plane
    return k.hullp(rock_pts(rnd, (cx, cy), rx, ry, rz * 2, z0=z0, n=n, top=3, waist=(0.35, 0.6)), color, ink=ink)


def flowers(k, x0, x1, y0, y1, z, n, colors, seed, h=(0.12, 0.3)):
    rnd = random.Random(seed)
    placed = []
    for i in range(n * 6):
        if len(placed) >= n:
            break
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        s = rnd.uniform(0.035, 0.055)
        # heads never touch, so no two flowers share a face plane (the build's z-fighting check)
        if any(abs(x - q[0]) < s + q[2] + 0.006 and abs(y - q[1]) < s + q[2] + 0.006 for q in placed):
            continue
        placed.append((x, y, s))
        hh = rnd.uniform(*h)
        k.bx(x - 0.012, x + 0.012, y - 0.012, y + 0.012, z, z + hh, 'leafD', ink=False)
        c = colors[len(placed) % len(colors)]
        k.bx(x - s, x + s, y - s, y + s, z + hh, z + hh + s * 1.2, c, ink=False)


# ================================================================ hedge walls
def hedge_body(k, seed, corner=False):
    rnd = random.Random(seed)
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, WALL_H - 0.2, 'hedge')
    k.bx(-0.5, 0.5, -0.42, 0.42, WALL_H - 0.2, WALL_H, 'hedge2')                   # rounded crown
    faces = ('-y', '+y', '-x', '+x') if corner else ('-y', '+y')
    for f in faces:
        clumps(k, f, -0.42, 0.42, 0.1, WALL_H - 0.25, rnd, 5)
    k.qz(-0.46, 0.46, -0.36, 0.36, WALL_H + 0.003, 1, 'leaf2')                    # sunlit top


def hedge_module(k, kind):
    k.begin()
    hedge_body(k, {'A': 3, 'B': 7, 'C': 11}[kind])
    if kind == 'B':     # flowers along the foot of the hedge
        k.bx(-0.36, 0.36, -0.62, -0.5, 0, 0.12, 'soil', ink=False)     # stops short of the ends: inside corners
        flowers(k, -0.32, 0.32, -0.6, -0.53, 0.12, 5, ('flY', 'paintW', 'flP'), 5, h=(0.1, 0.32))
    elif kind == 'C':   # a climbing rose
        rnd = random.Random(21)
        for i in range(7):
            x = rnd.uniform(-0.38, 0.38)
            z = rnd.uniform(0.5, 2.8)
            r = rnd.uniform(0.06, 0.1)
            pts = [(x + math.cos(a) * r, -0.5115 - 0.003 * i, z + math.sin(a) * r) for a in [j / 5 * 2 * math.pi for j in range(5)]]
            k.poly(pts, 'blossom2' if i % 3 else 'red', (0, -1, 0))
    return k


def hedge_brick(k):
    """Near the gates: a brick dwarf wall with stone coping in front of the hedge."""
    k.begin()
    rnd = random.Random(31)
    k.bx(-0.5, 0.5, -0.1, 0.5, 0, WALL_H - 0.2, 'hedge')
    k.bx(-0.5, 0.5, -0.02, 0.42, WALL_H - 0.2, WALL_H, 'hedge2')
    k.qz(-0.46, 0.46, 0.02, 0.38, WALL_H + 0.003, 1, 'leaf2')
    clumps(k, '+y', -0.42, 0.42, 0.1, WALL_H - 0.25, rnd, 5)
    clumps(k, '-y', -0.42, 0.42, 1.6, WALL_H - 0.25, rnd, 4, d=0.103)
    k.bx(-0.5, 0.5, -0.5, -0.1, 0, 1.45, 'brick')
    k.bx(-0.497, 0.497, -0.56, -0.06, 1.45, 1.57, 'stone')
    for i, z in enumerate((0.25, 0.5, 0.75, 1.0, 1.25)):
        k.qy(-0.5, 0.5, z - 0.012, z + 0.012, -0.503, -1, 'brick2')
        off = 0.0 if i % 2 else 0.25
        for x in (-0.5 + off, off):
            if -0.49 < x < 0.49:
                k.qy(x - 0.012, x + 0.012, z - 0.25 + 0.012, z - 0.012, -0.506, -1, 'brick2')
    return k


def hedge_corner(k):
    k.begin()
    hedge_body(k, 41, corner=True)
    return k


# ================================================================ gate, trail, hatch
def gate_frame(k):
    """Garden gate: brick piers (in the hedge cells either side of the 3 m opening) with stone caps and ball
    finials, a timber pergola with climbing roses over it, and the shutter's green roller box closing the hedge
    line above the opening."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.5, s * 2.5)
        k.bx(x0, x1, -0.55, 0.55, 0, 3.3, 'brick')
        k.bx(x0 - 0.05, x1 + 0.05, -0.6, 0.6, 3.3, 3.44, 'stone')
        k.sph((x0 + x1) / 2, 0, 3.62, 0.2, 'stone', seg=(8, 5))
        for f in (-1, 1):
            for i, z in enumerate((0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8)):
                k.qy(x0 + 0.02, x1 - 0.02, z - 0.012, z + 0.012, f * 0.553, f, 'brick2')
            k.qy(x0 + 0.25, x1 - 0.25, 1.85, 2.2, f * 0.556, f, 'stone')          # a stone plaque
        for z in (0.4, 1.2, 2.0, 2.8):   # mortar lines on the outer pier faces (seen beside the hedge)
            k.qx(-0.53, 0.53, z - 0.012, z + 0.012, (x0 - 0.003) if s < 0 else (x1 + 0.003), s, 'brick2')
    # roller box (closes the hedge line above the opening) and the pergola
    k.bx(-1.5, 1.5, -0.3, 0.3, 3.05, WALL_H + 0.05, 'paintG')
    for f in (-1, 1):
        k.qy(-1.3, 1.3, 3.15, 3.3, f * 0.303, f, 'paintG2')
    for f in (-1, 1):
        k.bx(-2.7, 2.7, f * 0.45 - 0.07, f * 0.45 + 0.07, WALL_H + 0.05, WALL_H + 0.3, 'wood')
    for i in range(9):
        x = -2.4 + i * 0.6
        k.bx(x - 0.05, x + 0.05, -0.75, 0.75, WALL_H + 0.3, WALL_H + 0.42, 'wood2')
    rnd = random.Random(5)
    for i in range(7):
        x = -2.2 + i * 0.73 + rnd.uniform(-0.1, 0.1)
        y = rnd.uniform(-0.4, 0.4)
        blob(k, x, y, WALL_H + 0.45, 0.32, 0.3, 0.14, 'leaf' if i % 2 else 'leafD', 70 + i, n=6)
        k.sph(x + 0.1, y - 0.18, WALL_H + 0.56, 0.07, 'blossom2' if i % 2 else 'red', seg=(5, 3), ink=False)
    k.col(-2.5, -1.5, -0.55, 0.55, 0, WALL_H)
    k.col(1.5, 2.5, -0.55, 0.55, 0, WALL_H)
    return k


def gate_shutter(k):
    """Green-painted slatted timber roller door with a brass handle rail."""
    k.begin()
    Hs, n = 3.05, 13
    h = (Hs - 0.2) / n
    for i in range(n):
        z0 = 0.2 + i * h
        k.bx(-1.5, 1.5, -0.06, 0.06, z0, z0 + h, 'paintG' if i % 2 else 'paintG2', ink=False)
    k.bx(-1.5, 1.5, -0.07, 0.07, 0, 0.2, 'woodD', ink=False)
    for f in (-1, 1):
        k.qy(-0.5, 0.5, 1.0, 1.06, f * 0.073, f, 'flY')
    return k


def trail_wall(k, kind):
    """Hedge along the path between gardens (1 m along Blender Y, path to +X)."""
    k.begin(90)
    rnd = random.Random({'Plain': 1, 'Lamp': 2, 'Rose': 3, 'Box': 4}[kind])
    k.bx(-0.5, 0.5, -0.25, 0.25, 0, WALL_H - 0.2, 'hedge')
    k.bx(-0.5, 0.5, -0.18, 0.18, WALL_H - 0.2, WALL_H, 'hedge2')
    clumps(k, '-y', -0.42, 0.42, 0.1, WALL_H - 0.25, rnd, 5, d=0.253)
    clumps(k, '+y', -0.42, 0.42, 0.1, WALL_H - 0.25, rnd, 4, d=0.253)
    if kind == 'Lamp':
        k.cyl(0, -0.4, 0, 0.07, 0.05, 2.6, 'paintG2', seg=6)
        k.bx(-0.13, 0.13, -0.53, -0.27, 2.6, 2.92, 'glass')
        k.cyl(0, -0.4, 2.92, 0.2, 0.04, 0.16, 'paintG2', seg=6)
    elif kind == 'Rose':
        for i in range(8):
            x = rnd.uniform(-0.4, 0.4)
            z = rnd.uniform(0.4, 2.6)
            r = rnd.uniform(0.06, 0.1)
            k.poly([(x + math.cos(a) * r, -0.2615 - 0.003 * i, z + math.sin(a) * r) for a in [j / 5 * 2 * math.pi for j in range(5)]],
                   'blossom' if i % 2 else 'red', (0, -1, 0))
    elif kind == 'Box':    # a bird box on a post
        k.bx(-0.04, 0.04, -0.34, -0.26, 0, 1.9, 'woodD')
        k.bx(-0.15, 0.15, -0.5, -0.26, 1.9, 2.25, 'wood')
        k.qy(-0.05, 0.05, 2.04, 2.14, -0.503, -1, 'ink')
        k.bx(-0.19, 0.19, -0.55, -0.24, 2.25, 2.31, 'roofR')
    return k


def hatch(k):
    """Exit: a ring of stepping stones round a teal-chevron pad, and a blue garden door in a brick arch at the back."""
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.25, 0.04, 'stone2', seg=12)
    for i in range(3):
        y = -0.65 + i * 0.5
        k.poly([(-0.7, y, 0.043), (0, y + 0.3, 0.043), (0.7, y, 0.043), (0.7, y + 0.14, 0.043), (0, y + 0.44, 0.043), (-0.7, y + 0.14, 0.043)],
               'teal' if i % 2 else 'plY', (0, 0, 1))
    for i in range(10):
        a = i / 10 * 2 * math.pi
        k.cyl(math.cos(a) * 1.55, math.sin(a) * 1.55, 0, 0.2, 0.2, 0.05, 'stone', seg=8)
    # brick arch + door at the back (north, Blender +Y)
    Y0, Y1 = 2.25, 2.7
    for s in (-1, 1):
        x0, x1 = srt(s * 0.75, s * 1.3)
        k.bx(x0, x1, Y0, Y1, 0, 2.5, 'brick')
    k.bx(-1.3, 1.3, Y0, Y1, 2.5, 3.0, 'brick')
    k.bx(-1.35, 1.35, Y0 - 0.05, Y1, 3.0, 3.12, 'stone')
    k.bx(-0.75, 0.75, Y1 - 0.12, Y1, 0, 2.5, 'plB')
    for x in (-0.4, 0.0, 0.4):
        k.qy(x - 0.012, x + 0.012, 0.15, 2.35, Y1 - 0.123, -1, 'plB2')
    k.cyl(0.55, Y1 - 0.16, 1.1, 0.05, 0.05, 0.04, 'flY', seg=6, rot=(90, 0, 0))
    k.qy(-0.5, 0.5, 2.62, 2.88, Y0 - 0.003, -1, 'teal')
    for s in (-1, 1):
        k.cyl(s * 1.05, Y0 - 0.15, 2.2, 0.1, 0.1, 0.25, 'lamp', seg=6)
        k.cyl(s * 1.05, Y0 - 0.15, 2.45, 0.14, 0.03, 0.12, 'paintG2', seg=6)
    return k


def stand(k):
    """Weapon stand: a potting crate with flower pots."""
    k.begin()
    k.bx(-0.45, 0.45, -0.4, 0.4, 0, 0.9, 'wood')
    for f in (-1, 1):
        k.qy(-0.43, 0.43, 0.43, 0.47, f * 0.403, f, 'wood2')
        k.qx(-0.38, 0.38, 0.43, 0.47, f * 0.453, f, 'wood2')
    for x, c in ((-0.25, 'flY'), (0.22, 'red')):
        k.cyl(x, 0.15, 0.9, 0.11, 0.14, 0.18, 'brick', seg=8)
        k.sph(x, 0.15, 1.15, 0.12, c, seg=(6, 4))
    return k


# ================================================================ ground tiles (no collision)
def path_tile(k, kind):
    k.begin()
    rnd = random.Random({'A': 1, 'B': 2}[kind])
    k.qz(-0.5, 0.5, -0.5, 0.5, ZD['path'], 1, 'gravel')
    for i in range(5):
        x, y = rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4)
        s = rnd.uniform(0.03, 0.06)
        k.qz(x - s, x + s, y - s * 0.8, y + s * 0.8, ZD['speck'] + 0.003 * i, 1, 'gravel2')
    return k


def pave_tile(k, kind):
    k.begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, ZD['pave'], 1, 'stone')
    if kind == 'A':
        k.qz(-0.5, 0.5, -0.015, 0.015, ZD['speck'], 1, 'stone2')
        k.qz(-0.015, 0.015, -0.5, -0.015, ZD['speck'] + 0.002, 1, 'stone2')
    else:
        k.qz(-0.5, 0.5, 0.235, 0.265, ZD['speck'], 1, 'stone2')
        k.qz(0.235, 0.265, -0.5, 0.235, ZD['speck'] + 0.002, 1, 'stone2')
    return k


def play_mat(k, kind):
    """Rubber play-surface tile (red / blue), with a painted hopscotch dot on B."""
    k.begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, ZD['mat'], 1, 'mat')
    if kind == 'B':
        k.disc(0.0, 0.0, ZD['speck'], 0.3, 'mat2', n=10)
    return k


# ================================================================ props
def tree(k, kind):
    k.begin()
    rnd = random.Random({'Oak': 1, 'Lime': 2, 'Blossom': 3, 'Pine': 4}[kind])
    if kind == 'Pine':
        k.cyl(0, 0, 0, 0.16, 0.1, 1.2, 'trunk2', seg=6)
        for i, (r, z, h) in enumerate(((1.3, 1.0, 1.8), (1.0, 2.2, 1.6), (0.7, 3.3, 1.5))):
            k.cyl(0, 0, z, r, 0.06, h, 'leafD' if i % 2 else 'hedge', seg=8)
        k.col(-0.2, 0.2, -0.2, 0.2, 0, 2.5)
        return k
    k.cyl(0, 0, 0, 0.2, 0.13, 2.4, 'trunk', seg=7)
    k.beam((0, 0, 1.7), (0.5, 0.2, 2.6), 0.1, 'trunk')
    k.beam((0, 0, 1.9), (-0.45, -0.25, 2.7), 0.09, 'trunk')
    c1, c2, c3 = {'Oak': ('leaf', 'leafD', 'leaf2'), 'Lime': ('leaf2', 'leaf', 'leafD'), 'Blossom': ('blossom', 'blossom2', 'blossom')}[kind]
    sq = 1.25 if kind == 'Lime' else 1.0
    blob(k, 0, 0, 3.5 * sq if kind == 'Lime' else 3.4, 1.4, 1.35, 1.1 * sq, c1, 11 + len(kind), n=8)
    blob(k, 0.75, 0.35, 2.95, 0.85, 0.8, 0.65, c2, 12 + len(kind), n=7)
    blob(k, -0.7, -0.45, 3.1, 0.9, 0.85, 0.7, c3, 13 + len(kind), n=7)
    if kind == 'Blossom':
        for i in range(6):
            a = i / 6 * 2 * math.pi
            k.qz(math.cos(a) * 1.3 - 0.12, math.cos(a) * 1.3 + 0.12, math.sin(a) * 1.3 - 0.08, math.sin(a) * 1.3 + 0.08, ZD['speck'], 1, 'blossom')
    k.col(-0.2, 0.2, -0.2, 0.2, 0, 2.5)
    return k


def flower_bed(k, kind):
    k.begin()
    edge = 'brick' if kind == 'Rose' else 'wood2'
    k.bx(-0.5, 0.5, -0.5, -0.42, 0, 0.25, edge)
    k.bx(-0.5, 0.5, 0.42, 0.5, 0, 0.25, edge)
    k.bx(-0.5, -0.42, -0.42, 0.42, 0, 0.25, edge)
    k.bx(0.42, 0.5, -0.42, 0.42, 0, 0.25, edge)
    k.bx(-0.42, 0.42, -0.42, 0.42, 0, 0.2, 'soil', ink=False)
    cols = {'Tulip': ('red', 'flY', 'plO'), 'Rose': ('red', 'blossom2', 'paintW'), 'Daisy': ('paintW', 'flY', 'flP')}[kind]
    blob(k, -0.15, 0.1, 0.32, 0.26, 0.24, 0.14, 'leaf', 3 + len(kind), n=6)
    blob(k, 0.18, -0.15, 0.3, 0.24, 0.22, 0.12, 'leafD', 4 + len(kind), n=6)
    flowers(k, -0.36, 0.36, -0.36, 0.36, 0.2, 8, cols, 7 + len(kind), h=(0.18, 0.36))
    k.col(-0.5, 0.5, -0.5, 0.5, 0, 0.45)
    return k


def low_hedge(k):
    k.begin()
    rnd = random.Random(9)
    k.bx(-0.5, 0.5, -0.4, 0.4, 0, 0.95, 'hedge2')
    k.bx(-0.5, 0.5, -0.33, 0.33, 0.95, 1.1, 'leaf')
    clumps(k, '-y', -0.42, 0.42, 0.0, 0.9, rnd, 3, cols=('leaf', 'hedge'), d=0.403)
    clumps(k, '+y', -0.42, 0.42, 0.0, 0.9, rnd, 3, cols=('leaf', 'hedge'), d=0.403)
    k.col(-0.5, 0.5, -0.4, 0.4, 0, 1.1)
    return k


def picket(k):
    k.begin()
    k.bx(-0.55, -0.45, -0.05, 0.05, 0, 1.12, 'paintW')
    for z in (0.3, 0.75):
        k.bx(-0.45, 0.5, 0.02, 0.06, z, z + 0.08, 'paintW')
    for i in range(4):
        x = -0.32 + i * 0.23
        k.hullp([(x - 0.045, -0.02, 0.05), (x + 0.045, -0.02, 0.05), (x - 0.045, 0.02, 0.05), (x + 0.045, 0.02, 0.05),
                 (x - 0.045, -0.02, 0.88), (x + 0.045, -0.02, 0.88), (x - 0.045, 0.02, 0.88), (x + 0.045, 0.02, 0.88),
                 (x, -0.02, 0.97), (x, 0.02, 0.97)], 'paintW')
    k.col(-0.5, 0.5, -0.07, 0.07, 0, 1.05)
    return k


def bench(k):
    """2 x 1 park bench: timber slats on green iron ends, facing -Y (game south)."""
    k.begin()
    for s in (-1, 1):
        x = s * 0.8
        k.bx(x - 0.04, x + 0.04, -0.28, 0.22, 0, 0.42, 'paintG2')
        k.bxr(x, 0.24, 0.65, 0.068, 0.08, 0.5, 'paintG2', rot=(-15, 0, 0))
        k.bx(x - 0.05, x + 0.05, -0.3, 0.12, 0.62, 0.68, 'paintG2')
    for i in range(3):
        y = -0.24 + i * 0.15
        k.bx(-0.95, 0.95, y - 0.055, y + 0.055, 0.42, 0.47, 'wood' if i % 2 else 'wood2')
    for i in range(2):
        z = 0.58 + i * 0.2
        k.bxr(0.0, 0.22 + i * 0.05, z, 1.9, 0.04, 0.12, 'wood', rot=(-15, 0, 0))
    k.col(-0.95, 0.95, -0.3, 0.3, 0, 0.9)
    return k


def picnic(k):
    """2 x 2 picnic table with its two benches."""
    k.begin()
    for i in range(4):
        y = -0.33 + i * 0.22
        k.bx(-0.95, 0.95, y - 0.1, y + 0.1, 0.72, 0.78, 'wood' if i % 2 else 'wood2')
    for s in (-1, 1):
        x = s * 0.7
        k.beam((x, -0.62, 0.0), (x, 0.0, 0.72), 0.07, 'woodD')
        k.beam((x, 0.62, 0.0), (x, 0.0, 0.72), 0.058, 'woodD')
        k.bx(x - 0.04, x + 0.04, -0.75, 0.75, 0.38, 0.42, 'woodD')
    for s in (-1, 1):
        k.bx(-0.95, 0.95, s * 0.62 - 0.13, s * 0.62 + 0.13, 0.42, 0.47, 'wood')
    k.cyl(0.3, 0.05, 0.78, 0.08, 0.08, 0.14, 'plR', seg=8)
    k.cyl(-0.35, -0.1, 0.78, 0.14, 0.14, 0.02, 'paintW', seg=8)
    k.col(-0.95, 0.95, -0.45, 0.45, 0, 0.8)
    k.col(-0.95, 0.95, -0.75, -0.45, 0, 0.47)
    k.col(-0.95, 0.95, 0.45, 0.75, 0, 0.47)
    return k


def urn(k):
    k.begin()
    k.bx(-0.3, 0.3, -0.3, 0.3, 0, 0.15, 'stone2')
    k.cyl(0, 0, 0.15, 0.12, 0.16, 0.25, 'stone', seg=8)
    k.cyl(0, 0, 0.4, 0.18, 0.32, 0.3, 'stone', seg=8)
    k.cyl(0, 0, 0.7, 0.34, 0.34, 0.06, 'stone2', seg=8)
    k.cyl(0, 0, 0.705, 0.29, 0.29, 0.06, 'soil', seg=8, ink=False)
    blob(k, 0, 0, 0.9, 0.36, 0.34, 0.2, 'leaf', 5, n=6)
    flowers(k, -0.25, 0.25, -0.25, 0.25, 0.85, 7, ('red', 'flP', 'paintW'), 9, h=(0.12, 0.25))
    k.col(-0.32, 0.32, -0.32, 0.32, 0, 1.0)
    return k


def lamp(k):
    k.begin()
    k.cyl(0, 0, 0, 0.14, 0.14, 0.3, 'paintG2', seg=8)
    k.cyl(0, 0, 0.3, 0.07, 0.05, 2.6, 'paintG2', seg=6)
    k.bx(-0.18, 0.18, -0.03, 0.03, 2.5, 2.56, 'paintG2')
    k.cyl(0, 0, 2.9, 0.2, 0.2, 0.06, 'paintG2', seg=6)
    k.cyl(0, 0, 2.96, 0.16, 0.2, 0.34, 'lamp', seg=6)
    k.cyl(0, 0, 3.3, 0.26, 0.03, 0.2, 'paintG2', seg=6)
    k.col(-0.15, 0.15, -0.15, 0.15, 0, 3.0)
    return k


def litter_bin(k):
    k.begin()
    k.cyl(0, 0, 0, 0.25, 0.27, 0.85, 'paintG', seg=8)
    k.cyl(0, 0, 0.85, 0.29, 0.29, 0.08, 'paintG2', seg=8)
    k.cyl(0, 0, 0.5, 0.275, 0.275, 0.08, 'flY', seg=8, ink=False, caps=False)
    k.col(-0.28, 0.28, -0.28, 0.28, 0, 0.93)
    return k


def birdbath(k):
    k.begin()
    k.cyl(0, 0, 0, 0.25, 0.2, 0.1, 'stone2', seg=8)
    k.cyl(0, 0, 0.1, 0.09, 0.12, 0.7, 'stone', seg=8)
    k.cyl(0, 0, 0.8, 0.12, 0.42, 0.14, 'stone', seg=10)
    k.cyl(0, 0, 0.94, 0.36, 0.36, 0.005, 'water', seg=10, ink=False)
    k.col(-0.3, 0.3, -0.3, 0.3, 0, 0.95)
    return k


def fountain(k):
    """6 x 6 tiered stone fountain in an octagonal basin."""
    k.begin()
    R = 2.7
    oct_ = [(math.cos((i + 0.5) / 8 * 2 * math.pi) * R, math.sin((i + 0.5) / 8 * 2 * math.pi) * R) for i in range(8)]
    k.hullp([(x, y, 0) for x, y in oct_] + [(x, y, 0.45) for x, y in oct_], 'stone2')
    for i in range(8):
        (x0, y0), (x1, y1) = oct_[i], oct_[(i + 1) % 8]
        cx, cy = (x0 + x1) / 2 * 0.96, (y0 + y1) / 2 * 0.96
        L = math.hypot(x1 - x0, y1 - y0)
        a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        k.bxr(cx, cy, 0.53 + 0.004 * (i % 2), L + 0.12, 0.3, 0.16, 'stone', rot=(0, 0, a))
    k.disc(0, 0, 0.455, R * 0.88, 'water', n=16)
    k.disc(0, 0, 0.46, 1.5, 'water2', n=12)
    k.cyl(0, 0, 0.45, 0.35, 0.25, 0.9, 'stone', seg=8)
    k.cyl(0, 0, 1.35, 0.25, 1.2, 0.3, 'stone', seg=10)
    k.cyl(0, 0, 1.65, 1.05, 1.05, 0.005, 'water', seg=10, ink=False)
    k.cyl(0, 0, 1.656, 0.16, 0.12, 0.694, 'stone', seg=8)
    k.cyl(0, 0, 2.35, 0.12, 0.6, 0.2, 'stone', seg=8)
    k.cyl(0, 0, 2.55, 0.5, 0.5, 0.005, 'water', seg=8, ink=False)
    k.sph(0, 0, 2.75, 0.14, 'stone', seg=(8, 5))
    # falling water sheets and a jet
    k.cyl(0, 0, 0.47, 1.22, 1.22, 0.88, 'water2', seg=10, ink=False, caps=False)
    k.cyl(0, 0, 1.67, 0.62, 0.62, 0.68, 'water2', seg=8, ink=False, caps=False)
    k.cyl(0, 0, 2.85, 0.05, 0.02, 0.6, 'water2', seg=6, ink=False)
    k.col(-2.6, 2.6, -2.6, 2.6, 0, 0.62)
    k.col(-1.2, 1.2, -1.2, 1.2, 0, 2.9)
    return k


def gazebo(k):
    """6 x 6 white octagonal gazebo on a raised timber floor (walkable, 0.3 m: one step), entrance to the south
    (Blender -Y), a lattice rail round the other sides, a red roof and a bench along the back."""
    k.begin()
    p = Plan(k)
    R, F = 2.5, 0.3
    oct_ = [(math.cos((i + 0.5) / 8 * 2 * math.pi) * R, math.sin((i + 0.5) / 8 * 2 * math.pi) * R) for i in range(8)]
    k.hullp([(x, y, 0) for x, y in oct_] + [(x, y, F) for x, y in oct_], 'wood')
    for i in range(-4, 5):
        k.qz(i * 0.5 - 0.015, i * 0.5 + 0.015, -1.0, 1.0, F + 0.003, 1, 'wood2')
    k.bx(-0.75, 0.75, -2.75, -2.25, 0, 0.15, 'stone')                       # entrance step (south)
    p.wcol(-0.75, 0.75, 2.25, 2.75, 0, 0.15)
    p.wcol(-2.3, 2.3, -0.95, 0.95, 0, F)
    p.wcol(-0.95, 0.95, -2.3, 2.3, 0, F)
    p.wcol(-1.6, 1.6, -1.6, 1.6, 0, F)
    posts = [(math.cos((i + 0.5) / 8 * 2 * math.pi) * (R - 0.15), math.sin((i + 0.5) / 8 * 2 * math.pi) * (R - 0.15)) for i in range(8)]
    for x, y in posts:
        k.cyl(x, y, F, 0.09, 0.09, 2.45, 'paintW', seg=6)
        k.col(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, F + 2.5)
    for i in range(8):
        (x0, y0), (x1, y1) = posts[i], posts[(i + 1) % 8]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if my < -1.5 and abs(mx) < 0.5:
            continue                                                      # the entrance side
        L = math.hypot(x1 - x0, y1 - y0)
        a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        k.bxr(mx, my, F + 0.85, L - 0.1, 0.08, 0.07, 'paintW', rot=(0, 0, a))
        k.bxr(mx * 1.003, my * 1.003, F + 0.45, L - 0.14, 0.03, 0.7, 'paintW', rot=(0, 0, a), ink=False)
        for t in (0.25, 0.5, 0.75):
            k.bxr(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, F + 0.45, 0.05, 0.06, 0.72, 'paintG', rot=(0, 0, a), ink=False)
        if abs(x1 - x0) < 0.05:          # east / west side
            k.col(mx - 0.06, mx + 0.06, min(y0, y1), max(y0, y1), F, F + 0.95)
        elif abs(y1 - y0) < 0.05:        # north side
            k.col(min(x0, x1), max(x0, x1), my - 0.06, my + 0.06, F, F + 0.95)
        else:                            # diagonal sides: three small boxes along the rail
            for t in (0.2, 0.5, 0.8):
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                k.col(cx - 0.2, cx + 0.2, cy - 0.2, cy + 0.2, F, F + 0.95)
    # bench along the back (north = Blender +Y)
    k.bx(-1.0, 1.0, 1.55, 1.95, F, F + 0.45, 'wood2')
    k.col(-1.0, 1.0, 1.55, 1.95, F, F + 0.45)
    # roof: eave ring + octagonal cone + finial
    Re = 3.0
    eo = [(math.cos((i + 0.5) / 8 * 2 * math.pi) * Re, math.sin((i + 0.5) / 8 * 2 * math.pi) * Re) for i in range(8)]
    k.hullp([(x, y, F + 2.5) for x, y in eo] + [(0, 0, F + 4.1)], 'roofR')
    k.hullp([(x * 0.85, y * 0.85, F + 2.38) for x, y in eo] + [(x * 0.85, y * 0.85, F + 2.5) for x, y in eo], 'paintW')
    k.cyl(0, 0, F + 4.0, 0.1, 0.03, 0.6, 'flY', seg=6)
    k.sph(0, 0, F + 4.62, 0.09, 'flY', seg=(6, 4))
    return k


def shed(k):
    """4 x 4 potting shed: green boards, white trim, a window box, felt roof, water butt."""
    k.begin()
    k.bx(-1.55, 1.55, -1.2, 1.2, 0, 2.2, 'paintG')
    for i in range(1, 12):
        x = -1.55 + i * 0.26
        k.qy(x - 0.012, x + 0.012, 0.05, 2.15, -1.203, -1, 'paintG2')
        k.qy(x - 0.012, x + 0.012, 0.05, 2.15, 1.203, 1, 'paintG2')
    k.qy(-1.15, -0.25, 0.0, 1.95, -1.206, -1, 'paintW')
    k.qy(-1.07, -0.33, 0.0, 1.87, -1.209, -1, 'paintG2')
    k.qy(-0.42, -0.36, 0.9, 1.0, -1.212, -1, 'flY')
    k.qy(0.2, 1.2, 0.95, 1.8, -1.206, -1, 'paintW')
    k.qy(0.27, 1.13, 1.02, 1.73, -1.209, -1, 'glass')
    k.qy(0.68, 0.72, 1.02, 1.73, -1.212, -1, 'paintW')
    k.qy(0.27, 0.68, 1.355, 1.395, -1.212, -1, 'paintW')
    k.qy(0.72, 1.13, 1.355, 1.395, -1.212, -1, 'paintW')
    k.bx(0.15, 1.25, -1.45, -1.2, 0.72, 0.92, 'wood2')
    flowers(k, 0.2, 1.2, -1.42, -1.25, 0.92, 9, ('red', 'flY', 'paintW'), 3, h=(0.08, 0.2))
    k.hullp([(-1.8, -1.45, 2.15), (1.8, -1.45, 2.15), (-1.8, 1.45, 2.15), (1.8, 1.45, 2.15),
             (-1.8, 0, 2.95), (1.8, 0, 2.95), (-1.8, -1.45, 2.25), (1.8, -1.45, 2.25)], 'roofS')
    k.cyl(1.85, 0.6, 0, 0.3, 0.3, 0.9, 'plB2', seg=8)
    k.cyl(1.85, 0.6, 0.9, 0.32, 0.32, 0.05, 'plB', seg=8)
    k.col(-1.6, 1.6, -1.25, 1.25, 0, 2.95)
    k.col(1.55, 2.15, 0.3, 0.9, 0, 0.95)
    return k


def sandpit(k):
    """4 x 4 sandpit: timber kerb (walkable, 0.25 m: stepped over), sand, bucket, spade and a sandcastle."""
    k.begin()
    p = Plan(k)
    for s in (-1, 1):
        k.bx(-1.95, 1.95, *srt(s * 1.7, s * 1.95), 0, 0.25, 'wood')
        k.bx(*srt(s * 1.7, s * 1.95), -1.7, 1.7, 0, 0.25, 'wood2')
        p.wcol(-1.95, 1.95, *srt(s * 1.7, s * 1.95), 0, 0.25)
        p.wcol(*srt(s * 1.7, s * 1.95), -1.7, 1.7, 0, 0.25)
    k.bx(-1.7, 1.7, -1.7, 1.7, 0, 0.12, 'sand', ink=False)
    p.wcol(-1.7, 1.7, -1.7, 1.7, 0, 0.12)
    rnd = random.Random(4)
    for i in range(8):
        x, y = rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5)
        k.qz(x - 0.1, x + 0.1, y - 0.05, y + 0.05, 0.123 + 0.003 * i, 1, 'sand2')
    k.bx(0.3, 0.9, 0.2, 0.8, 0.12, 0.42, 'sand2')
    k.bx(0.4, 0.8, 0.3, 0.7, 0.42, 0.62, 'sand2')
    for x in (0.3, 0.9):
        for y in (0.2, 0.8):
            k.cyl(x, y, 0.42, 0.08, 0.08, 0.3, 'sand', seg=6)
    k.bx(0.58, 0.62, 0.48, 0.52, 0.62, 0.9, 'woodD', ink=False)
    k.poly([(0.62, 0.5, 0.9), (0.85, 0.5, 0.82), (0.62, 0.5, 0.74)], 'red', (0, -1, 0))
    k.cyl(-0.8, -0.6, 0.12, 0.12, 0.16, 0.22, 'plR', seg=8)
    k.beam((-0.2, -0.9, 0.13), (0.3, -0.5, 0.4), 0.04, 'plB')
    k.col(0.3, 0.9, 0.2, 0.8, 0, 0.62)
    return k


def swings(k):
    """4 x 2 swing set: A-frames, top bar, two swings over rubber mats."""
    k.begin()
    for s in (-1, 1):
        x = s * 1.8
        for f in (-1, 1):
            k.beam((x, f * 0.9, 0), (x, 0, 2.45), 0.09 if f < 0 else 0.078, 'plB')
        k.bx(x - 0.055, x + 0.055, -0.5, 0.5, 0.9, 0.98, 'plB2')
        k.col(x - 0.1, x + 0.1, -0.95, 0.95, 0, 2.5)
    k.cyl(-1.9, 0, 2.45, 0.07, 0.07, 3.8, 'plY', seg=8, rot=(0, 90, 0))
    for x, c in ((-0.7, 'plR'), (0.7, 'plB')):
        for dx in (-0.22, 0.22):
            k.beam((x + dx, 0, 2.4), (x + dx, 0, 0.5), 0.025, 'metal2')
        k.bx(x - 0.27, x + 0.27, -0.12, 0.12, 0.45, 0.52, c)
        k.qz(x - 0.5, x + 0.5, -0.6, 0.6, ZD['swingmat'], 1, 'mat2')
    return k


def seesaw(k):
    k.begin()
    k.hullp([(-0.25, -0.3, 0), (0.25, -0.3, 0), (-0.25, 0.3, 0), (0.25, 0.3, 0), (-0.06, -0.3, 0.55), (0.06, -0.3, 0.55),
             (-0.06, 0.3, 0.55), (0.06, 0.3, 0.55)], 'plB')
    ang = math.degrees(math.atan2(0.5, 3.6))
    k.bxr(0, 0, 0.6, 3.7, 0.32, 0.07, 'plY', rot=(0, -ang, 0))
    for s in (-1, 1):
        x = s * 1.55
        z = 0.6 + s * math.tan(math.radians(ang)) * 1.55
        k.bxr(x, 0, z + 0.06, 0.34, 0.36, 0.05, 'plR', rot=(0, -ang, 0))
        k.bx(x - s * 0.25 - 0.03, x - s * 0.25 + 0.03, -0.2, 0.2, z + 0.05, z + 0.35, 'plB2')
        k.bx(x - s * 0.25 - 0.03, x - s * 0.25 + 0.03, -0.22, 0.22, z + 0.35, z + 0.4, 'plB2')
    k.col(-1.9, 1.9, -0.2, 0.2, 0, 0.75)
    return k


def monkey_bars(k):
    """6 x 2 monkey bars: two ladders and a run of rungs at 2.2 m (walk under them)."""
    k.begin()
    H = 2.2
    for s in (-1, 1):
        x = s * 2.6
        for f in (-1, 1):
            k.bx(x - 0.05, x + 0.05, f * 0.38 - 0.05, f * 0.38 + 0.05, 0, H + 0.1, 'plR')
        for i in range(5):
            z = 0.35 + i * 0.38
            k.bx(x - 0.03, x + 0.03, -0.33, 0.33, z, z + 0.05, 'plY')
        k.col(x - 0.08, x + 0.08, -0.45, 0.45, 0, H + 0.1)
    for f in (-1, 1):
        k.bx(-2.55, 2.55, f * 0.38 - 0.045, f * 0.38 + 0.045, H, H + 0.1, 'plG')
    for i in range(12):
        x = -2.2 + i * 0.4
        k.bx(x - 0.03, x + 0.03, -0.36, 0.36, H + 0.02, H + 0.08, 'plY')
    k.qz(-2.9, 2.9, -0.7, 0.7, ZD['swingmat'], 1, 'mat')
    return k


# ================================================================ playground builders (plan coordinates)
def deck(p, x0, x1, z0, z1, h, opens=None, post_top=None, panel=('plB', 'plG'), roof=None, rnd=None, slab='wood'):
    """Play deck: slab (walkable, underside at h - SLAB), corner posts (outside the slab corners) up to post_top,
    railing panels along each edge except the openings, optional pyramid roof. opens: {'N'|'S'|'E'|'W': [(a, b)]}
    ranges along the edge (x for N/S, z for E/W)."""
    opens = opens or {}
    post_top = post_top or h + 1.0
    p.bx(x0, x1, z0, z1, h - SLAB, h, slab)
    p.wcol(x0, x1, z0, z1, h - SLAB, h)
    nx = int(round((x1 - x0) / 0.5))
    for i in range(1, nx):
        x = x0 + i * 0.5
        p.top(x - 0.015, x + 0.015, z0 + 0.1, z1 - 0.1, h + 0.003, 'woodD')
    for (px, pz) in ((x0 - 0.08, z0 - 0.08), (x1 + 0.08, z0 - 0.08), (x0 - 0.08, z1 + 0.08), (x1 + 0.08, z1 + 0.08)):
        p.bx(px - 0.08, px + 0.08, pz - 0.08, pz + 0.08, 0, post_top, 'plB2' if panel[0] != 'plB2' else 'plR')
        p.col(px - 0.09, px + 0.09, pz - 0.09, pz + 0.09, 0, post_top)
        if not roof:
            p.bx(px - 0.1, px + 0.1, pz - 0.1, pz + 0.1, post_top, post_top + 0.08, 'plY')

    def spans(a, b, cuts):
        out, cur = [], a
        for (c0, c1) in sorted(cuts):
            if c0 > cur + 0.05:
                out.append((cur, c0))
            cur = max(cur, c1)
        if b > cur + 0.05:
            out.append((cur, b))
        return out
    TOP = 0.95
    k = 0
    for side in ('N', 'S', 'E', 'W'):
        if side in ('N', 'S'):
            zz = z0 + 0.01 if side == 'N' else z1 - 0.07
            for (a, b) in spans(x0, x1, opens.get(side, [])):
                c = panel[k % len(panel)]
                k += 1
                p.bx(a, b, zz, zz + 0.06, h, h + TOP - 0.12, c)
                p.bx(a, b, zz - 0.005, zz + 0.065, h + TOP - 0.12, h + TOP, 'plY')
                p.col(a, b, zz - 0.01, zz + 0.07, h, h + TOP)
                if b - a > 1.0:      # a porthole / tic-tac-toe badge on the outside face
                    m = (a + b) / 2
                    s = -1 if side == 'N' else 1
                    zf = zz + (0.0 if side == 'N' else 0.06) + s * 0.003
                    p.fz(m - 0.22, m + 0.22, h + 0.25, h + 0.69, zf, s, 'paintW')
                    p.fz(m - 0.15, m + 0.15, h + 0.32, h + 0.62, zf + s * 0.003, s, 'plR' if k % 2 else 'plY')
        else:
            xx = x1 - 0.07 if side == 'E' else x0 + 0.01
            for (a, b) in spans(z0 + 0.08, z1 - 0.08, opens.get(side, [])):
                c = panel[k % len(panel)]
                k += 1
                p.bx(xx, xx + 0.06, a, b, h, h + TOP - 0.12, c)
                p.bx(xx - 0.005, xx + 0.065, a, b, h + TOP - 0.12, h + TOP, 'plY')
                p.col(xx - 0.01, xx + 0.07, a, b, h, h + TOP)
    if roof:
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        e = 0.45
        p.hull([(x0 - e, z0 - e, post_top + 0.08), (x1 + e, z0 - e, post_top + 0.08), (x0 - e, z1 + e, post_top + 0.08), (x1 + e, z1 + e, post_top + 0.08),
                (cx, cz, post_top + 0.08 + roof)], 'roofR' if panel[0] == 'plB' else 'plR')
        p.bx(x0 - 0.2, x1 + 0.2, z0 - 0.2, z1 + 0.2, post_top - 0.15, post_top + 0.08, 'plY')


def stairs(p, x0, x1, edge, d, h, rise=0.3, depth=0.5, step='plG', nose='plY', rails=True):
    """Stairs along plan z from a deck edge (z = edge) running away in direction d (+1 south / -1 north): solid
    walkable steps from the ground, top step one rise under the deck, handrails with collision on both sides."""
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.bx(x0, x1, za, zb, 0, top, step if i % 2 else 'plB')
        p.wcol(x0, x1, za, zb, 0, top)
        zn = zb - 0.12 if d > 0 else za
        p.top(x0 + 0.04, x1 - 0.04, zn, zn + 0.12, top + 0.003, nose)
    if rails:
        zend = edge + d * n * depth
        for xr in (x0 - 0.05, x1 + 0.05):
            p.beam((xr, edge, h + 0.9), (xr, zend, 0.9 + rise), 0.07, 'plY')
            p.bx(xr - 0.05, xr + 0.05, *srt(zend - d * 0.05, zend + d * 0.05), 0, 0.9 + rise, 'plR')
            for i in range(1, n + 1):
                top = h - i * rise
                za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
                p.col(xr - 0.05, xr + 0.05, za, zb, top, top + 0.95)
                if i % 2 == 0:
                    p.bx(xr - 0.02, xr + 0.02, za + 0.2, zb - 0.2, top, top + 0.85, 'plY', ink=False)


def stairs_x(p, z0, z1, edge, d, h, rise=0.3, depth=0.5, step='plG', nose='plY', rails=True, x_stop=None):
    """Stairs along plan x from a deck edge (x = edge) in direction d (+1 east / -1 west)."""
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        xa, xb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.bx(xa, xb, z0, z1, 0, top, step if i % 2 else 'plB')
        p.wcol(xa, xb, z0, z1, 0, top)
        xn = xb - 0.12 if d > 0 else xa
        p.top(xn, xn + 0.12, z0 + 0.04, z1 - 0.04, top + 0.003, nose)
    if rails:
        xend = edge + d * n * depth
        for zr in (z0 - 0.05, z1 + 0.05):
            p.beam((edge, zr, h + 0.9), (xend, zr, 0.9 + rise), 0.07, 'plY')
            for i in range(1, n + 1):
                top = h - i * rise
                xa, xb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
                p.col(xa, xb, zr - 0.05, zr + 0.05, top, top + 0.95)


def ramp(p, x0, x1, edge, d, h, rise, depth=0.5, color='plO', cleat='woodD'):
    """A ramp along plan z: walkable steps under a sloped wedge whose surface
    runs through the steps' centres (feet are never more than rise/2 off it)."""
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.wcol(x0, x1, za, zb, 0, top)
    zend = edge + d * n * depth
    yt, yb = h - rise / 2, rise / 2
    p.hull([(x0, edge, 0), (x1, edge, 0), (x0, edge, yt), (x1, edge, yt), (x0, zend, 0), (x1, zend, 0), (x0, zend, yb), (x1, zend, yb)], color)
    L = n * depth
    slope = (yt - yb) / L
    for i in range(1, n + 1):
        sm = i * depth - depth / 2
        pts = []
        for (x, ds) in ((x0 + 0.05, -0.04), (x1 - 0.05, -0.04), (x1 - 0.05, 0.04), (x0 + 0.05, 0.04)):
            ss = sm + ds
            pts.append((x, -(edge + d * ss), yt - slope * ss + 0.004))
        p.k.poly(pts, cleat, (0, -d * slope, 1))
    for xr in (x0 - 0.05, x1 + 0.05):
        p.beam((xr, edge, h + 0.9), (xr, zend, 0.9 + yb), 0.06, 'plY')
        p.bx(xr - 0.05, xr + 0.05, *srt(zend - d * 0.05, zend + d * 0.05), 0, 0.9 + yb, 'plR')
        for i in range(1, n + 1):
            top = h - i * rise
            za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
            p.col(xr - 0.05, xr + 0.05, za, zb, top, top + 0.95)


def slide_x(p, z0, z1, edge, d, h, color='plY', side='plR'):
    """A slide along plan x from a deck edge (x = edge) in direction d: a sloped chute bed (walkable steps 0.3 m
    under it, floating so the low end stays open), side walls, a run-out and a support leg."""
    rise, depth = 0.3, 0.5
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        xa, xb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.wcol(xa, xb, z0, z1, max(0.0, top - 0.12), top)
    xend = edge + d * n * depth
    yt, yb = h - rise / 2, rise / 2 + 0.05
    t = 0.07
    p.hull([(edge, z0, yt), (edge, z1, yt), (xend, z0, yb), (xend, z1, yb), (edge, z0, yt - t), (edge, z1, yt - t), (xend, z0, yb - t), (xend, z1, yb - t)], color)
    for zs in (z0 - 0.04, z1 + 0.04):
        za, zb = srt(zs - 0.04, zs + 0.04)
        p.hull([(edge, za, yt - t), (edge, zb, yt - t), (edge, za, yt + 0.3), (edge, zb, yt + 0.3),
                (xend, za, yb - t), (xend, zb, yb - t), (xend, za, yb + 0.3), (xend, zb, yb + 0.3)], side)
    xr = xend + d * 0.5
    p.hull([(xend, z0, yb), (xend, z1, yb), (xr, z0, 0.18), (xr, z1, 0.18), (xend, z0, yb - t), (xend, z1, yb - t), (xr, z0, 0.11), (xr, z1, 0.11)], color)
    p.bx(*srt(xend - d * 0.4, xend - d * 0.3), z0 + 0.1, z1 - 0.1, 0, yb + 0.3 * rise, 'plB2')


def bridge_x(p, xa, xb, z0, z1, ha, hb, sag=0.0, kind='rope'):
    """Bridge along plan x between two deck edges: planks (walkable, each its own height on a straight line or a
    sagging rope curve), rope net / plank sides with collision, end posts."""
    n = int(round((xb - xa) / 0.5))
    ys = []
    for i in range(n):
        t = (i + 0.5) / n
        ys.append(round(ha + (hb - ha) * t - sag * math.sin(math.pi * t), 3))
    for i, y in enumerate(ys):
        x = xa + i * 0.5
        p.bx(x + 0.04, x + 0.46, z0 + 0.03, z1 - 0.03, y - 0.08, y, 'wood' if i % 2 else 'wood2')
        p.wcol(x, x + 0.5, z0, z1, y - 0.08, y)
        for zs, zn in ((z0, z0 + 0.03), (z1 - 0.03, z1)):
            if kind == 'rope':
                p.bx(x, x + 0.5, zs, zn, y - 0.05, y + 0.9, 'rope', ink=False)
            else:
                p.bx(x, x + 0.5, zs, zn, y - 0.08, y + 0.8, 'plO' if i % 2 else 'plY', ink=False)
            p.col(x, x + 0.5, zs - 0.01, zn + 0.01, y, y + 0.95)
    for zr in (z0 + 0.015, z1 - 0.015):
        pts = [(xa, ha + 0.95)] + [(xa + (i + 0.5) * 0.5, ys[i] + 0.95) for i in range(n)] + [(xb, hb + 0.95)]
        for j, ((x0_, y0_), (x1_, y1_)) in enumerate(zip(pts, pts[1:])):
            # alternate thickness: neighbouring segments overlap at the joints and must not share face planes
            p.beam((x0_, zr, y0_), (x1_, zr, y1_), 0.06 if j % 2 else 0.05, 'woodD' if kind == 'rope' else 'plY')
    for x, hh in ((xa + 0.08, ha), (xb - 0.08, hb)):
        for zr in (z0 - 0.06, z1 + 0.06):
            p.bx(x - 0.07, x + 0.07, zr - 0.07, zr + 0.07, hh - SLAB, hh + 1.05, 'plR')


def pole(p, x, z, h):
    p.cyl(x, z, 0, 0.05, 0.05, h + 1.2, 'metal', seg=8)
    p.col(x - 0.07, x + 0.07, z - 0.07, z + 0.07, 0, h + 1.2)


def flag(p, x, z, y, c='plR'):
    p.cyl(x, z, y, 0.035, 0.03, 1.1, 'metal', seg=6)
    p.k.poly([(x, -z, y + 1.05), (x + 0.6, -z, y + 0.9), (x, -z, y + 0.72)], c, (0, -1, 0))
    p.k.poly([(x, -z + 0.004, y + 1.05), (x, -z + 0.004, y + 0.72), (x + 0.6, -z + 0.004, y + 0.9)], c, (0, 1, 0))


# ================================================================ the playgrounds
def play_tower(k):
    """10 x 10 play tower: a roofed 3 x 3 deck at 2.1 m; stairs down to the south, a wavy slide to the west, a
    climbing wall to the east, a fireman's pole at the north-east corner, a sandbox shade under the deck."""
    k.begin()
    p = Plan(k)
    deck(p, -1.5, 1.5, -2.5, 0.5, DECK, opens={'S': [(-1.0, 1.0)], 'W': [(-1.4, -0.6)], 'E': [(-1.8, -0.2)]},
         post_top=4.2, roof=1.2)
    flag(p, 0, -1.0, 5.45)
    stairs(p, -1.0, 1.0, 0.5, 1, DECK)
    slide_x(p, -1.4, -0.6, -1.5, -1, DECK)
    climb_x(p, -1.8, -0.2, 1.5, 1, DECK)
    pole(p, 1.95, -2.58, DECK)
    p.bx(1.66, 1.92, -2.62, -2.54, DECK + 0.6, DECK + 0.66, 'metal')
    # a steering wheel and a periscope on the north rail
    p.cyl(0.0, -2.62, DECK + 0.45, 0.32, 0.32, 0.06, 'plR', seg=10, rot=(90, 0, 0))
    p.cyl(0.0, -2.68, DECK + 0.45, 0.08, 0.08, 0.06, 'plY', seg=8, rot=(90, 0, 0))
    return k


def climb_x(p, z0, z1, edge, d, h, color='plP'):
    """Climbing wall along plan x from a deck edge: 0.3 m rise per 0.3 m (the player walks up it; robots' nav does
    not link it), coloured holds on a sloped panel, side rails."""
    rise, depth = 0.3, 0.3
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        xa, xb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.wcol(xa, xb, z0, z1, 0, top)
    xend = edge + d * n * depth
    yt, yb = h - rise / 2, rise / 2
    p.hull([(edge, z0, 0), (edge, z1, 0), (edge, z0, yt), (edge, z1, yt), (xend, z0, 0), (xend, z1, 0), (xend, z0, yb), (xend, z1, yb)], color)
    L = n * depth
    slope = (yt - yb) / L
    rnd = random.Random(int(edge * 11 + z0 * 5) & 0xFF)
    cols = ('plY', 'plR', 'plB', 'plG', 'paintW')
    got = []
    for i in range(int(n * (z1 - z0) * 1.4)):
        s = rnd.uniform(0.2, L - 0.15)
        z = rnd.uniform(z0 + 0.15, z1 - 0.15)
        if any(abs(s - q[0]) < 0.17 and abs(z - q[1]) < 0.17 for q in got):
            continue                     # holds never overlap (their bases share the wall plane)
        got.append((s, z))
        y = yt - slope * s
        x = edge + d * s
        p.k.cyl(x, -z, y - 0.03, 0.07, 0.05, 0.09, cols[i % len(cols)], seg=5, ink=False, rot=(0, d * math.degrees(math.atan(slope)), 0))
    for zr in (z0 - 0.05, z1 + 0.05):
        p.beam((edge, zr, h + 0.9), (xend, zr, 0.9 + yb), 0.06, 'plY')
        p.bx(*srt(xend - d * 0.05, xend + d * 0.05), zr - 0.05, zr + 0.05, 0, 0.9 + yb, 'plR')
        for i in range(1, n + 1):
            top = h - i * rise
            xa, xb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
            p.col(xa, xb, zr - 0.05, zr + 0.05, top, top + 0.95)


# The big play fort (28 x 14) is split into two pieces placed together (theme symbol 'X' with `with`), so each keeps
# to the theme's per-piece triangle budget: the towers (decks, posts, rails, roofs) and the links (bridges, stairs,
# ramp, slides, climbing wall, pole).
FORT = {
    'TW': (-11.0, -7.0, -2.0, 2.0, DECK),
    'TC': (-2.0, 2.0, -3.0, 1.0, TALL),
    'TE': (7.0, 11.0, -2.0, 2.0, DECK),
}


def play_fort(k):
    k.begin()
    p = Plan(k)
    x0, x1, z0, z1, h = FORT['TW']
    deck(p, x0, x1, z0, z1, h, opens={'E': [(-1.0, 1.0)], 'S': [(-10.0, -8.0)], 'W': [(-0.4, 0.4)]}, post_top=4.3, roof=1.3)
    flag(p, -9.0, 0.0, 5.65, 'plY')
    x0, x1, z0, z1, h = FORT['TC']
    deck(p, x0, x1, z0, z1, h, opens={'W': [(-1.0, 1.0)], 'E': [(-1.0, 1.0)], 'S': [(-1.2, 1.2)], 'N': [(-0.4, 0.4)]},
         post_top=5.0, roof=1.6, panel=('plR', 'plY'))
    flag(p, 0.0, -1.0, 6.68, 'plB')
    x0, x1, z0, z1, h = FORT['TE']
    deck(p, x0, x1, z0, z1, h, opens={'W': [(-1.0, 1.0)], 'S': [(8.0, 10.0)], 'E': [(-0.4, 0.4)]}, post_top=4.3, roof=1.3,
         panel=('plG', 'plO'))
    flag(p, 9.0, 0.0, 5.65, 'plR')
    # telescopes / wheels on the outer rails
    p.cyl(-9.0, -2.12, DECK + 0.45, 0.32, 0.32, 0.06, 'plR', seg=10, rot=(90, 0, 0))
    p.cyl(9.0, -2.12, DECK + 0.45, 0.32, 0.32, 0.06, 'plB', seg=10, rot=(90, 0, 0))
    return k


def play_fort_links(k):
    k.begin()
    p = Plan(k)
    bridge_x(p, -7.0, -2.0, -1.0, 1.0, DECK, TALL, 0.0, kind='plank')
    bridge_x(p, 2.0, 7.0, -1.0, 1.0, TALL, DECK, 0.18, kind='rope')
    stairs(p, -10.0, -8.0, 2.0, 1, DECK)                               # TW from the south
    ramp(p, 8.0, 10.0, 2.0, 1, DECK, 0.21)                              # TE from the south (gentle)
    climb_z(p, -1.2, 1.2, 1.0, 1, TALL)                                 # TC from the south: climbing wall
    slide_z(p, -0.4, 0.4, -3.0, -1, TALL, color='plB', side='plY')      # TC down to the north
    slide_x(p, -0.4, 0.4, -11.0, -1, DECK)                              # TW down to the west
    slide_x(p, -0.4, 0.4, 11.0, 1, DECK, color='plG', side='plO')       # TE down to the east
    pole(p, 11.45, -2.08, DECK)
    p.bx(11.16, 11.42, -2.12, -2.04, DECK + 0.6, DECK + 0.66, 'metal')
    return k


def climb_z(p, x0, x1, edge, d, h, color='plP'):
    """Climbing wall along plan z (see climb_x)."""
    rise, depth = 0.3, 0.3
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.wcol(x0, x1, za, zb, 0, top)
    zend = edge + d * n * depth
    yt, yb = h - rise / 2, rise / 2
    p.hull([(x0, edge, 0), (x1, edge, 0), (x0, edge, yt), (x1, edge, yt), (x0, zend, 0), (x1, zend, 0), (x0, zend, yb), (x1, zend, yb)], color)
    L = n * depth
    slope = (yt - yb) / L
    rnd = random.Random(int(edge * 13 + x0 * 7) & 0xFF)
    cols = ('plY', 'plR', 'plB', 'plG', 'paintW')
    got = []
    for i in range(int(n * (x1 - x0) * 1.4)):
        s = rnd.uniform(0.2, L - 0.15)
        x = rnd.uniform(x0 + 0.15, x1 - 0.15)
        if any(abs(s - q[0]) < 0.17 and abs(x - q[1]) < 0.17 for q in got):
            continue                     # holds never overlap (their bases share the wall plane)
        got.append((s, x))
        y = yt - slope * s
        z = edge + d * s
        p.k.cyl(x, -z, y - 0.03, 0.07, 0.05, 0.09, cols[i % len(cols)], seg=5, ink=False, rot=(d * math.degrees(math.atan(slope)), 0, 0))
    for xr in (x0 - 0.05, x1 + 0.05):
        p.beam((xr, edge, h + 0.9), (xr, zend, 0.9 + yb), 0.06, 'plY')
        p.bx(xr - 0.05, xr + 0.05, *srt(zend - d * 0.05, zend + d * 0.05), 0, 0.9 + yb, 'plR')
        for i in range(1, n + 1):
            top = h - i * rise
            za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
            p.col(xr - 0.05, xr + 0.05, za, zb, top, top + 0.95)


def slide_z(p, x0, x1, edge, d, h, color='plY', side='plR'):
    """Slide along plan z (see slide_x)."""
    rise, depth = 0.3, 0.5
    n = int(round(h / rise)) - 1
    for i in range(1, n + 1):
        top = round(h - i * rise, 4)
        za, zb = srt(edge + d * (i - 1) * depth, edge + d * i * depth)
        p.wcol(x0, x1, za, zb, max(0.0, top - 0.12), top)
    zend = edge + d * n * depth
    yt, yb = h - rise / 2, rise / 2 + 0.05
    t = 0.07
    p.hull([(x0, edge, yt), (x1, edge, yt), (x0, zend, yb), (x1, zend, yb), (x0, edge, yt - t), (x1, edge, yt - t), (x0, zend, yb - t), (x1, zend, yb - t)], color)
    for xs in (x0 - 0.04, x1 + 0.04):
        xa, xb = srt(xs - 0.04, xs + 0.04)
        p.hull([(xa, edge, yt - t), (xb, edge, yt - t), (xa, edge, yt + 0.3), (xb, edge, yt + 0.3),
                (xa, zend, yb - t), (xb, zend, yb - t), (xa, zend, yb + 0.3), (xb, zend, yb + 0.3)], side)
    zr = zend + d * 0.45
    p.hull([(x0, zend, yb), (x1, zend, yb), (x0, zr, 0.18), (x1, zr, 0.18), (x0, zend, yb - t), (x1, zend, yb - t), (x0, zr, 0.11), (x1, zr, 0.11)], color)
    p.bx(x0 + 0.1, x1 - 0.1, *srt(zend - d * 0.4, zend - d * 0.3), 0, yb + 0.09, 'plB2')


def play_ship(k):
    """18 x 10 pirate play ship, bow to the east: a solid hull with the main deck at 1.2 m (gangplank ramp from the
    south, stairs from the north), a raised poop deck at the stern (2.1 m, two steps up from the main deck, a slide
    off the back), a mast with a crow's nest and a striped sail, a ship's wheel, a play cannon."""
    k.begin()
    p = Plan(k)
    D1, D2 = 1.2, DECK
    hx0, hx1, hz = -6.0, 5.0, 2.5
    # hull (main deck, walkable) + poop deck block
    p.bx(hx0, hx1, -hz, hz, 0, D1, 'wood2')
    p.wcol(hx0, hx1, -hz, hz, 0, D1)
    p.bx(hx0, -3.0, -hz, hz, D1, D2, 'wood')
    p.wcol(hx0, -3.0, -hz, hz, D1, D2)
    for i in range(1, 16):
        x = -3.0 + i * 0.5
        if x < hx1 - 0.05:
            p.top(x - 0.015, x + 0.015, -hz + 0.12, hz - 0.12, D1 + 0.003, 'woodD')
    for i in range(1, 6):
        x = hx0 + i * 0.5
        p.top(x - 0.015, x + 0.015, -hz + 0.12, hz - 0.12, D2 + 0.003, 'woodD')
    for s in (-1, 1):
        zf = s * (hz + 0.003)
        p.fz(hx0, hx1, 0.62, 0.82, zf, s, 'plR')
        p.fz(hx0, hx1, 0.12, 0.2, zf, s, 'woodD')
        for i in range(5):
            x = -4.5 + i * 2.0
            p.fz(x - 0.17, x + 0.17, 0.85, 1.05, zf + s * 0.003, s, 'paintW')
            p.fz(x - 0.11, x + 0.11, 0.89, 1.01, zf + s * 0.006, s, 'ink')
    p.fx(-hz, hz, 0.62, 0.82, hx0 - 0.003, -1, 'plR')
    p.fx(-1.6, 1.6, D1 + 0.15, D2 - 0.1, hx0 - 0.003, -1, 'plY')                 # stern windows
    for zz in (-1.0, 0.0, 1.0):
        p.fx(zz - 0.25, zz + 0.25, D1 + 0.3, D2 - 0.25, hx0 - 0.006, -1, 'glass')
    p.fx(-1.0, 1.0, D1 + 0.05, D2 - 0.05, -2.997, 1, 'plY')                       # poop deck front trim
    # bow (not walkable: a blocking box keeps the deck end shut)
    p.hull([(hx1, -hz, 0.0), (hx1, hz, 0.0), (hx1, -hz, D1), (hx1, hz, D1), (7.6, 0.0, 0.25), (8.2, 0.0, D1 + 0.55)], 'wood2')
    p.beam((7.6, 0.0, D1 + 0.4), (8.9, 0.0, D1 + 1.1), 0.12, 'woodD')
    p.col(hx1, 7.8, -2.0, 2.0, 0, D1 + 1.0)
    for s in (-1, 1):
        p.beam((hx1, s * (hz - 0.05), D1 + 0.75), (8.0, 0.0, D1 + 0.95), 0.1, 'plR')
    # bulwarks on the main deck (gaps: gangplank to the south x -1..1, stairs to the north x 1..3)
    def bulwark(xa, xb, z, s):
        za, zb = srt(z, z - s * 0.12)
        p.bx(xa, xb, za, zb, D1, D1 + 0.75, 'plR' if s > 0 else 'plB')
        p.bx(xa, xb, za - 0.02, zb + 0.02, D1 + 0.75, D1 + 0.85, 'plY')
        p.col(xa, xb, za - 0.02, zb + 0.02, D1, D1 + 0.9)
    bulwark(-3.0, -1.0, hz, 1)
    bulwark(1.0, hx1, hz, 1)
    bulwark(-3.0, 1.0, -hz, -1)
    bulwark(3.0, hx1, -hz, -1)
    # poop deck rails (gaps: the steps from the main deck z -1..1, the slide off the stern z -0.4..0.4)
    deck_rails(p, hx0, -3.0, -hz, hz, D2, {'E': [(-1.0, 1.0)], 'W': [(-0.4, 0.4)]})
    for i, top in enumerate((D2 - 0.3, D2 - 0.6)):
        xa, xb = -3.0 + i * 0.5, -2.5 + i * 0.5
        p.bx(xa, xb, -1.0, 1.0, D1, top, 'plG' if i == 0 else 'plB')
        p.wcol(xa, xb, -1.0, 1.0, D1, top)
        p.top(xb - 0.12, xb, -0.96, 0.96, top + 0.003, 'plY')
    # gangplank ramp (south) and stairs (north)
    ramp(p, -1.0, 1.0, hz, 1, D1, 0.2, color='wood', cleat='woodD')
    stairs(p, 1.0, 3.0, -hz, -1, D1)
    # slide off the stern (west)
    slide_x(p, -0.4, 0.4, hx0, -1, D2, color='plY', side='plB')
    # mast, crow's nest, sail
    p.cyl(1.0, 0.0, D1, 0.16, 0.12, 6.4, 'woodD', seg=8)
    p.col(0.84, 1.16, -0.16, 0.16, D1, D1 + 6.4)
    p.cyl(1.0, 0.0, 5.6, 0.75, 0.75, 0.6, 'wood', seg=10)
    p.cyl(1.0, 0.0, 6.2, 0.8, 0.8, 0.08, 'plR', seg=10)
    flag(p, 1.0, 0.0, 7.55, 'ink')
    p.beam((1.0, -2.0, 4.9), (1.0, 2.0, 4.9), 0.1, 'woodD')
    p.beam((1.0, -2.0, 2.8), (1.0, 2.0, 2.8), 0.1, 'woodD')
    p.bx(1.12, 1.16, -1.9, 1.9, 2.85, 4.85, 'paintW', ink=False)
    for i in range(3):
        zz = -1.3 + i * 1.3
        p.bx(1.16, 1.19, zz - 0.22, zz + 0.22, 2.85, 4.85, 'plR', ink=False)
        p.bx(1.09, 1.12, zz - 0.22, zz + 0.22, 2.85, 4.85, 'plR', ink=False)
    # wheel on the poop deck, a cannon at the bow end of the main deck
    # (off the centre line: the steps from the main deck and the slide keep a clear lane)
    p.bx(-4.6, -4.4, 1.5, 1.7, D2, D2 + 0.9, 'woodD')
    p.cyl(-4.36, -1.6, D2 + 0.95, 0.42, 0.42, 0.06, 'wood', seg=10, rot=(0, 90, 0))
    p.cyl(-4.32, -1.6, D2 + 0.95, 0.1, 0.1, 0.06, 'plY', seg=8, rot=(0, 90, 0))
    p.col(-4.65, -4.35, 1.45, 1.75, D2, D2 + 1.0)
    p.bx(3.6, 4.4, -0.5, 0.5, D1, D1 + 0.25, 'woodD')
    p.cyl(3.6, 0.0, D1 + 0.45, 0.2, 0.16, 1.2, 'ink', seg=8, rot=(0, 90, 0))
    p.col(3.5, 4.8, -0.5, 0.5, D1, D1 + 0.7)
    # blue sea painted round the hull, with wave crests
    p.top(-10.0, 10.0, -5.0, 5.0, ZD['sea'], 'mat2')
    for (x, z) in ((-8.0, -4.0), (-5.0, -3.6), (6.0, -3.8), (-7.5, 3.8), (4.5, 4.2), (7.8, 3.0), (8.2, -2.0)):
        p.top(x - 0.4, x + 0.4, z - 0.04, z + 0.04, ZD['sea'] + 0.004, 'paintW')
    return k


def deck_rails(p, x0, x1, z0, z1, h, opens):
    """Railing panels only (round a block deck such as the ship's poop deck)."""
    def spans(a, b, cuts):
        out, cur = [], a
        for (c0, c1) in sorted(cuts):
            if c0 > cur + 0.05:
                out.append((cur, c0))
            cur = max(cur, c1)
        if b > cur + 0.05:
            out.append((cur, b))
        return out
    TOP = 0.95
    for side in ('N', 'S', 'E', 'W'):
        if side in ('N', 'S'):
            zz = z0 + 0.01 if side == 'N' else z1 - 0.07
            for (a, b) in spans(x0, x1, opens.get(side, [])):
                p.bx(a, b, zz, zz + 0.06, h, h + TOP - 0.12, 'plB')
                p.bx(a, b, zz - 0.005, zz + 0.065, h + TOP - 0.12, h + TOP, 'plY')
                p.col(a, b, zz - 0.01, zz + 0.07, h, h + TOP)
        else:
            xx = x1 - 0.07 if side == 'E' else x0 + 0.01
            for (a, b) in spans(z0 + 0.08, z1 - 0.08, opens.get(side, [])):
                p.bx(xx, xx + 0.06, a, b, h, h + TOP - 0.12, 'plR')
                p.bx(xx - 0.005, xx + 0.065, a, b, h + TOP - 0.12, h + TOP, 'plY')
                p.col(xx - 0.01, xx + 0.07, a, b, h, h + TOP)


# ================================================================ backdrop
def backdrop_houses(k):
    """Suburb beyond the park: one long slice (+-110 m along X, facing -Y) of houses with red and slate roofs,
    chimneys and garden trees, under the afternoon sky."""
    k.begin()
    rnd = random.Random(17)
    x = -112.0
    i = 0
    while x < 112:
        w = rnd.uniform(9, 14)
        h = rnd.uniform(6, 9)
        d = rnd.uniform(8, 11)
        y0 = (i % 3) * 0.4
        k.bx(x, x + w - 2.0, y0, y0 + d, 0.0, h, ('house', 'house2', 'houseB')[i % 3])
        k.hullp([(x - 0.3, y0 - 0.4, h), (x + w - 1.7, y0 - 0.4, h), (x - 0.3, y0 + d + 0.4, h), (x + w - 1.7, y0 + d + 0.4, h),
                 (x + 0.8, y0 + d / 2, h + 3.4), (x + w - 2.8, y0 + d / 2, h + 3.4)], 'roofR' if i % 2 else 'roofS')
        for j in range(int((w - 2) / 2.6)):
            xx = x + 0.9 + j * 2.6
            k.qy(xx, xx + 1.2, h * 0.55, h * 0.8, y0 - 0.02, -1, 'glass')
            k.qy(xx, xx + 1.2, h * 0.15, h * 0.4, y0 - 0.02, -1, 'glass')
        if i % 2 == 0:
            k.bx(x + w - 4.0, x + w - 3.2, y0 + d / 2, y0 + d / 2 + 0.8, h + 1.5, h + 4.4, 'brick')
        tx = x + w - 1.0
        k.hullp(rock_pts(rnd, (tx, y0 - 2.5), 2.2, 2.0, 5.0, z0=2.0 + 0.004 * (i % 5), n=6, top=2), 'far' if i % 2 else 'far2')
        k.bx(tx - 0.25, tx + 0.25, y0 - 2.75, y0 - 2.25, 0.0, 2.5, 'trunk2', ink=False)
        x += w
        i += 1
    return k


def backdrop_trees(k):
    """Park trees beyond the hedges: a long slice of rounded tree clumps on a grassy bank."""
    k.begin()
    rnd = random.Random(23)
    x = -112.0
    i = 0
    while x < 112:
        w = rnd.uniform(5, 8)
        h = rnd.uniform(7, 11)
        cx = x + w / 2
        cy = rnd.uniform(0.0, 3.0)
        k.hullp(rock_pts(rnd, (cx, cy), w * 0.55, w * 0.5, h * 0.75, z0=h * 0.3 + 0.004 * (i % 5), n=6, top=2), 'far' if i % 3 else 'far2')
        k.bx(cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, 0.0, h * 0.35, 'trunk2', ink=False)
        x += w * 0.85
        i += 1
    return k


# ================================================================ build
def build_kit_garden(ao):
    pal = Palette(FAM)
    k = GKit(pal, PFX, HULL_T)
    for kind in ('A', 'B', 'C'):
        hedge_module(k, kind).finish('Hedge_' + kind, ao=ao)
    hedge_brick(k).finish('Hedge_Brick', ao=ao)
    hedge_corner(k).finish('Hedge_Corner', ao=ao)
    gate_frame(k).finish('GateFrame', ao=ao)
    sh = gate_shutter(k).finish('GateShutter')
    shutter_hull(pal, sh)
    for kind in ('Plain', 'Lamp', 'Rose', 'Box'):
        trail_wall(k, kind).finish('TrailWall' if kind == 'Plain' else 'TrailWall_' + kind, ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    for kind in ('A', 'B'):
        path_tile(k, kind).finish('Path_' + kind)
        pave_tile(k, kind).finish('Pave_' + kind)
        play_mat(k, kind).finish('Mat_' + kind)
    for kind in ('Oak', 'Lime', 'Blossom', 'Pine'):
        tree(k, kind).finish('Tree_' + kind, ao=ao)
    for kind in ('Tulip', 'Rose', 'Daisy'):
        flower_bed(k, kind).finish('Bed_' + kind, ao=ao)
    low_hedge(k).finish('LowHedge', ao=ao)
    picket(k).finish('Picket', ao=ao)
    bench(k).finish('Bench', ao=ao)
    picnic(k).finish('Picnic', ao=ao)
    urn(k).finish('Urn', ao=ao)
    lamp(k).finish('Lamp', ao=ao)
    litter_bin(k).finish('Bin', ao=ao)
    birdbath(k).finish('Birdbath', ao=ao)
    fountain(k).finish('Landmark_Fountain', ao=ao)
    gazebo(k).finish('Landmark_Gazebo', ao=ao)
    shed(k).finish('Shed', ao=ao)
    sandpit(k).finish('Sandpit', ao=ao)
    swings(k).finish('Swings', ao=ao)
    seesaw(k).finish('Seesaw', ao=ao)
    monkey_bars(k).finish('MonkeyBars', ao=ao)
    play_tower(k).finish('Landmark_PlayTower', ao=ao)
    play_fort(k).finish('Landmark_PlayFort', ao=ao)
    play_fort_links(k).finish('Landmark_PlayFortLinks', ao=ao)
    play_ship(k).finish('Landmark_PlayShip', ao=ao)
    backdrop_houses(k).finish('Backdrop_Houses')
    backdrop_trees(k).finish('Backdrop_Trees')
    k.report(FAM)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_garden
