"""INKBOLT asset family: kit-livingroom (Living Room, a "tiny" theme like the Big Bedroom: the player is a robot toy and
the house is giant around them, about x6). One wide open-plan floor: the lounge (sofa, coffee table, TV and games
console, rug, bookshelf, fireplace, plants), the dining end (table, chairs, pendant lamp) and the kitchen (island with
stools, retro fridge, counters with sink, stove and upper cabinets). Warm afternoon light comes in through tall
windows and lies on the floorboards as sun patches.

Scale: 18 m ceiling (a real 2.7 m), 18.4 m walls. Blender Z-up; game +Z (south) = Blender -Y; a piece's origin is the
centre of its cell / footprint at floor level; furniture fronts face -Y (south) as authored.

Pieces (prefix KIT_LIVINGROOM_):
  Wall<s>, Wall<s>_X    1 m wall modules per paint scheme s (1 sage lounge, 2 peach dining, 3 butter kitchen), turned
                        by the engine to face the room (theme wall.facing 'open'); _X modules (east / west walls)
                        carry their trims 6 mm higher so inner corners never share a plane. Wall_Corner hides corners.
  Landmark_Sofa, CoffeeTable, TVStand, Controller, Rug, RugRunner, Bookshelf, Fireplace, Plant_Fig, Plant_Snake,
  FloorLamp, Island, Stool, Fridge, Counter, Counter_Sink, Counter_Stove, DiningTable, DiningChair, Sideboard,
  Cushion, Basket, ToyBox, Block_A..C, Sneaker, Mug, BookPile, ToyTruck, Ball
  Window, Window_R, Frame_A/B(_R), SunPatch      wall overlays (placed in the floor row in front of a wall) and the
                                                 afternoon light lying on the boards
  CeilingTile                                    hung at y = 18 (the dining pendant is part of DiningTable)
  GateFrame (a giant interior door with a pet flap: the 3 m gate is the flap), GateShutter (the flap),
  TrailWall (+ _Photos, _Coats, _Radiator, _Shoes: the hallway), Hatch (a brass floor register)
Collision boxes are <Piece>_COL<n> cube empties (centre, half extents).
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'kit-livingroom'
PRE = 'KIT_LIVINGROOM_'
ib_lib.GLB[FAM] = 'fps-kit-livingroom.glb'
ib_lib.CFG[FAM] = (0.03, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # walls: paint per zone, wainscot, trims
    ('paint1', '#BFDDB2'), ('paint2', '#F7C6A5'), ('paint3', '#FFE49A'), ('wains', '#FFF6E6'), ('trim', '#FFFDF7'),
    ('trim2', '#EADFCC'),
    # woods
    ('oak', '#E2B47A'), ('oak2', '#C99460'), ('walnut', '#9A6A45'), ('walnut2', '#74503A'), ('birch', '#F1D9B0'),
    # fabrics
    ('sofa', '#3FA3A0'), ('sofa2', '#58BCB6'), ('sofaD', '#2C807D'), ('mustard', '#F2B33D'), ('coral', '#F27A62'),
    ('rugR', '#E4705C'), ('rugC', '#FFF0D6'), ('rugB', '#5E8FD1'), ('knit', '#F7E3B5'), ('lilac', '#B9A6E8'),
    # kitchen
    ('cab', '#F4EEDF'), ('cab2', '#8FC1A8'), ('block', '#E2B072'), ('tile', '#FDFBF6'), ('tile2', '#A9DCE3'),
    ('steel', '#C9CFD6'), ('steel2', '#8F96A3'), ('mint', '#9FE0CF'), ('mint2', '#78C9B5'),
    # light, fire, brick
    ('glass', '#CDEBFF'), ('sun', '#FFE9A8'), ('fire', '#FF8A3D'), ('fire2', '#FFD45E'), ('brick', '#C96F52'),
    ('brick2', '#A9553F'), ('stone', '#EBDFCC'), ('lamp', '#FFF0B8'), ('ceil', '#FBF5EA'),
    # screens, plants, toys, misc
    ('screen', '#2E3A55'), ('screen2', '#5C7FC0'), ('black', '#2A2830'), ('leaf', '#5BAF5A'), ('leaf2', '#3F8F4A'),
    ('pot', '#E9875F'), ('tblue', '#3F8CF0'), ('tyellow', '#FFC93C'), ('tgreen', '#5BCF4A'), ('cardboard', '#D8AE76'),
    ('cardboard2', '#BF925A'), ('cream', '#FFF3DA'), ('navy', '#33377A'), ('pink', '#FFB4CF'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64

CEIL = 18.0       # ceiling height (theme env.ceiling.height)
WALL_H = 18.4     # wall modules poke above the ceiling so it always meets them
TRAIL_H = 18.3
FRAME_H = 18.5
FACE = 0.5        # wall face plane (|y| from the wall cell centre)
HT = 0.02
pal = None
STATS = {}


# ================================================================ helpers
def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def tris_of(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def strip_shapes(obj, ids):
    """Remove the outline shell of the given shapes only (flat paint, wall bodies, small details)."""
    if not ids:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    hl = bm.verts.layers.float_vector.get('_HULL')
    sl = bm.faces.layers.int.get('shape_id')
    kill = [f for f in bm.faces if f[sl] in ids and all(v[hl].length > 0 for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()


class K(Model):
    """Model that remembers which shapes get no outline shell and the piece's collision boxes."""

    def __init__(self):
        super().__init__(pal)
        self.nh = set()
        self.cols = []

    def flat(self):
        self.nh.add(self.nshape)

    def colbox(self, x0, y0, z0, x1, y1, z1):
        self.cols.append((((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)))

    def bx(self, x0, y0, z0, x1, y1, z1, color, flat=False, bevel=False, rot=(0, 0, 0)):
        f = self.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), color, rot=rot, bevel=bevel)
        if flat:
            self.flat()
        return f

    def cy(self, x, y, z, r1, r2, h, color, seg=10, flat=False, rot=(0, 0, 0), caps=True):
        self.cyl((x, y, z), r1, r2, h, color, seg=seg, rot=rot, bevel=False, caps=caps)
        if flat:
            self.flat()

    def sp(self, x, y, z, r, color, seg=(8, 5), scale=(1, 1, 1), rot=(0, 0, 0), flat=False):
        self.sphere((x, y, z), r, color, seg=seg, scale=scale, rot=rot)
        if flat:
            self.flat()

    def tri(self, pts, color):
        """One-sided flat triangle (no outline), CCW seen from the front, in parent space."""
        vs = [self.bm.verts.new(self.parent @ Vector(p)) for p in pts]
        self.bm.faces.new(vs)
        self._finish(vs, color, False)
        self.flat()

    def up(self, pts, z, color):
        """Flat horizontal polygon facing up (any winding), no outline."""
        if sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) < 0:
            pts = list(reversed(pts))
        self.quad([(x, y, z) for x, y in pts], color) if len(pts) == 4 else self.tri([(x, y, z) for x, y in pts], color)

    def quad(self, pts, color):
        """One-sided flat quad (no outline); points CCW seen from the front, in parent space."""
        vs = [self.bm.verts.new(self.parent @ Vector(p)) for p in pts]
        self.bm.faces.new(vs)
        self._finish(vs, color, False)
        self.flat()

    def poly(self, pts, z0, z1, color, flat=False):
        """Prism from a convex CCW outline (x, y) between z0 and z1, in parent space."""
        bm = self.bm
        b = [bm.verts.new(self.parent @ Vector((x, y, z0))) for x, y in pts]
        t = [bm.verts.new(self.parent @ Vector((x, y, z1))) for x, y in pts]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((b[i], b[j], t[j], t[i]))
        bm.faces.new(t)
        bm.faces.new(list(reversed(b)))
        self._finish(b + t, color, False)
        if flat:
            self.flat()


WALL_GAP = 0.32    # pieces against a wall keep their backs this far off the wall face (clear of the trims)


def finish(name, m, bevel=0.0, hull=HT, ao=False, strip=False, shift=0.0):
    full = PRE + name
    if shift:
        bmesh.ops.translate(m.bm, vec=Vector((0.0, -shift, 0.0)), verts=list(m.bm.verts))
        m.cols = [((c[0], c[1] - shift, c[2]), h) for (c, h) in m.cols]
    obj = build_object(full, m, bevel, hull, ao=ao)
    if strip:
        strip_hull(obj)
    else:
        strip_shapes(obj, m.nh)
    for i, (c, h) in enumerate(m.cols):
        e = socket('%s_COL%d' % (full, i), obj, c)
        e.scale = h
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
    STATS[full] = tris_of(obj)
    return obj


def normals_up(obj, only_down=True):
    """Shade downward faces as if they faced up (custom normals): the toon light has no ambient term, so a ceiling
    would otherwise fall in the darkest band. Outline-shell faces keep their normals."""
    me = obj.data
    hull = me.attributes.get('_HULL')
    corner = [tuple(n.vector) for n in me.corner_normals]
    out = []
    for poly in me.polygons:
        shell = hull is not None and any(Vector(hull.data[v].vector).length > 0 for v in poly.vertices)
        lift = not shell and (not only_down or poly.normal.z < -0.5)
        for li in poly.loop_indices:
            out.append((0.0, 0.0, 1.0) if lift else corner[li])
    me.normals_split_custom_set(out)
    return obj


def lift_where(obj, pred):
    """Shade the faces pred(centre, normal) picks as if they faced up (custom normals): window glass and the garden
    behind it glow evenly whichever way the wall faces, like daylight coming in."""
    me = obj.data
    hull = me.attributes.get('_HULL')
    corner = [tuple(n.vector) for n in me.corner_normals]
    out = []
    for poly in me.polygons:
        shell = hull is not None and any(Vector(hull.data[v].vector).length > 0 for v in poly.vertices)
        lift = not shell and pred(poly.center, poly.normal)
        for li in poly.loop_indices:
            out.append((0.0, 0.0, 1.0) if lift else corner[li])
    me.normals_split_custom_set(out)
    return obj


BOOKS = ['red', 'tblue', 'tyellow', 'tgreen', 'coral', 'navy', 'mustard', 'sofaD', 'lilac', 'pink', 'brick', 'cab2',
         'walnut', 'teal', 'rugB']


def shelf_row(m, x0, x1, z, zt, ya, yb, rnd, objects=True, thick=1.0):
    """A shelf's worth of things along local x (x0..x1) on z under zt, depth ya..yb (front at ya): books of mixed size
    and colour (spine bands), one leaning, a lying stack, now and then a plant, a photo frame or a vase."""
    hmax = zt - z - 0.1
    d0 = yb - ya
    x, prev, obj, stack = x0 + rnd.uniform(0, 0.06), None, not objects, False
    while x1 - x > 0.14:
        room, r = x1 - x, rnd.random()
        if not stack and room > 0.7 and r < 0.14:
            L = min(room - 0.05, rnd.uniform(0.6, 0.95))
            zz = z
            for i in range(rnd.randint(2, 4)):
                tk = rnd.uniform(0.14, 0.24)
                m.box((x + L / 2 + rnd.uniform(-0.02, 0.02), ya + d0 / 2, zz + tk / 2 + 0.006), (L * rnd.uniform(0.85, 0.97), d0 * rnd.uniform(0.82, 0.95), tk - 0.004),
                      rnd.choice(BOOKS), rot=(0, 0, rnd.uniform(-3, 3) + (0.7 if i % 2 else -0.7)), bevel=False)
                m.flat()
                zz += tk + 0.004
                if zz > z + hmax * 0.5:
                    break
            x += L + 0.06
            stack, prev = True, None
            continue
        if not obj and room > 0.5 and r < 0.26:
            cx, yc = x + 0.24, ya + d0 / 2
            kind = rnd.choice(('plant', 'frame', 'vase'))
            if kind == 'plant':
                m.cy(cx, yc, z, 0.17, 0.2, 0.45, 'pot', seg=8)
                m.sp(cx - 0.06, yc, z + 0.7, 0.26, 'leaf', seg=(7, 5))
                m.sp(cx + 0.12, yc - 0.02, z + 0.58, 0.18, 'leaf2', seg=(6, 4), rot=(0, 0, 30))
            elif kind == 'frame':
                m.bx(cx - 0.22, ya + 0.12, z, cx + 0.22, ya + 0.2, z + 0.6, 'walnut', rot=(-8, 0, 0))
                m.bx(cx - 0.16, ya + 0.11, z + 0.08, cx + 0.16, ya + 0.12, z + 0.5, rnd.choice(('sun', 'glass', 'pink')), flat=True, rot=(-8, 0, 0))
            else:
                m.cy(cx, yc, z, 0.13, 0.19, 0.5, rnd.choice(('tile2', 'coral', 'mustard')), seg=8)
                m.cy(cx, yc, z + 0.5, 0.19, 0.09, 0.25, 'tile2' if r < 0.1 else 'cream', seg=8)
            x += 0.5
            obj, prev = True, None
            continue
        if prev is not None and prev[0] == 'book' and r < 0.45:
            t = rnd.uniform(0.12, 0.2)
            h = min(hmax, prev[2] * rnd.uniform(0.88, 1.08))
            a = math.radians(rnd.uniform(12, 24))
            if h * math.cos(a) < prev[2] - 0.05 and room > h * math.sin(a) + t + 0.06:
                px = prev[1] + h * math.sin(a) + 0.014
                cx = px + t / 2 * math.cos(a) - h / 2 * math.sin(a)
                cz = z + t / 2 * math.sin(a) + h / 2 * math.cos(a) + 0.002
                m.box((cx, ya + d0 / 2, cz), (t - 0.006, d0 * rnd.uniform(0.8, 0.95), h), rnd.choice(BOOKS), rot=(0, -math.degrees(a), 0), bevel=False)
                m.flat()
                x = px + t * math.cos(a) + 0.04
                prev = None
                continue
        t = rnd.choice((0.13, 0.16, 0.2, 0.24, 0.28, 0.32)) * thick
        if t > room - 0.01:
            t = room - 0.01
            if t < 0.11:
                break
        h = hmax * rnd.uniform(0.6, 0.98)
        d = d0 * rnd.uniform(0.8, 0.97)
        c = rnd.choice(BOOKS)
        yo = ya + rnd.uniform(0, d0 - d)
        m.bx(x, yo, z, x + t - 0.012, yo + d, z + h, c, flat=True)
        k = rnd.choice((0, 0, 1, 2))
        if t >= 0.16 and k:
            for (a0, a1) in ((0.7, 0.78),) if k == 1 else ((0.1, 0.14), (0.84, 0.88)):
                m.bx(x + 0.012, yo - 0.005, z + h * a0, x + t - 0.024, yo + d + 0.005, z + h * a1,
                     'cream' if c in ('navy', 'walnut', 'sofaD', 'brick', 'teal', 'rugB', 'tblue') else 'walnut2', flat=True)
        prev = ('book', x + t - 0.012, h)
        x += t + rnd.choice((0.0, 0.0, 0.012, 0.03))


# ================================================================ walls
SCHEMES = {'1': 'paint1', '2': 'paint2', '3': 'paint3'}
WAINS = 6.0        # wainscot (panelled lower wall) height


def wall_module(m, paint, dz):
    """1 m module, room side -Y at y = -0.5: panelled cream wainscot with a chair rail, painted upper wall, picture
    rail, crown moulding. dz lifts the trims (E/W modules) so inner corners never share a plane."""
    y = -FACE
    m.quad([(0.5, y, 0.0), (0.5, y, WAINS + 0.1), (-0.5, y, WAINS + 0.1), (-0.5, y, 0.0)], 'wains')
    m.quad([(0.5, y, WAINS + 0.1), (0.5, y, WALL_H), (-0.5, y, WALL_H), (-0.5, y, WAINS + 0.1)], paint)
    # wainscot panel: a raised frame (stiles at the module edges would show a seam each metre: rails only)
    m.bx(-0.5, y - 0.05, 1.3 + dz, 0.5, y + 0.02, 1.42 + dz, 'trim', flat=True)
    m.bx(-0.5, y - 0.05, 5.0 + dz, 0.5, y + 0.02, 5.12 + dz, 'trim', flat=True)
    m.bx(-0.5, y - 0.16, 0.0, 0.5, y + 0.02, 1.0 + dz, 'trim', flat=True)              # skirting
    m.bx(-0.5, y - 0.2, 1.0 + dz, 0.5, y + 0.02, 1.08 + dz, 'trim2', flat=True)        # skirting bead
    m.bx(-0.5, y - 0.14, WAINS + dz, 0.5, y + 0.02, WAINS + 0.3 + dz, 'oak2', flat=True)   # chair rail
    m.bx(-0.5, y - 0.07, 14.2 + dz, 0.5, y + 0.02, 14.32 + dz, 'oak2', flat=True)      # picture rail
    m.bx(-0.5, y - 0.3, 17.2 + dz, 0.5, y + 0.02, 17.6 + dz, 'trim', flat=True)        # crown
    m.bx(-0.5, y - 0.18, 16.9 + dz, 0.5, y + 0.02, 17.2 + dz, 'trim2', flat=True)


def build_walls():
    for s, paint in SCHEMES.items():
        for tag, dz in (('', 0.0), ('_X', 0.006)):
            m = K()
            wall_module(m, paint, dz)
            finish('Wall%s%s' % (s, tag), m, hull=0.0, strip=True)
    m = K()
    m.bx(-0.5, -0.5, 0.0, 0.5, 0.5, WALL_H, 'trim2', flat=True)
    finish('Wall_Corner', m, hull=0.0, strip=True)


# ================================================================ overlays: windows, frames, sun patches
def build_overlays():
    """Wall overlays sit in the floor row in front of a wall: the wall face is 0.5 m behind the cell centre (+Y as
    authored; the _R twins face north and are used on south / east walls)."""
    for name, R in (('Window', Matrix.Identity(4)), ('Window_R', rz(180))):
        m = K()
        m.parent = R
        wy = 0.5            # wall face
        W, Z0, Z1 = 4.0, 4.6, 14.6
        m.bx(-W - 0.35, wy - 0.42, Z0 - 0.5, W + 0.35, wy - 0.002, Z0, 'trim')                 # sill + apron
        m.bx(-W - 0.2, wy - 0.3, Z0 - 1.2, W + 0.2, wy - 0.002, Z0 - 0.5, 'trim2')
        for sx in (-1, 1):
            m.bx(sx * W - 0.22, wy - 0.34, Z0, sx * W + 0.22, wy - 0.007, Z1 + 0.3, 'trim')    # jambs
        m.bx(-W - 0.3, wy - 0.36, Z1, W + 0.3, wy - 0.002, Z1 + 0.5, 'trim')                   # head
        m.quad([(W - 0.2, wy - 0.18, Z0), (W - 0.2, wy - 0.18, Z1), (-W + 0.2, wy - 0.18, Z1), (-W + 0.2, wy - 0.18, Z0)], 'sun')
        # outside: a pale sky band and a hedge across the lower panes (flat, just in front of the glass)
        m.quad([(W - 0.2, wy - 0.184, Z0 + 3.6), (W - 0.2, wy - 0.184, Z1), (-W + 0.2, wy - 0.184, Z1), (-W + 0.2, wy - 0.184, Z0 + 3.6)], 'glass')
        m.quad([(W - 0.2, wy - 0.188, Z0), (W - 0.2, wy - 0.188, Z0 + 1.6), (-W + 0.2, wy - 0.188, Z0 + 1.6), (-W + 0.2, wy - 0.188, Z0)], 'leaf')
        for i, (cx, r) in enumerate(((-2.6, 1.0), (-1.2, 0.8), (1.5, 1.1), (3.0, 0.7))):
            m.cy(cx, wy - 0.19 - 0.003 * i, Z0 + 1.6, r, r, 0.004, 'leaf2' if i % 2 else 'leaf', seg=8, rot=(90, 0, 0), flat=True)
        # glazing bars (cross panes), proud of the glass
        for x in (-W / 3, W / 3):
            m.bx(x - 0.08, wy - 0.25, Z0, x + 0.08, wy - 0.17, Z1, 'trim', flat=True)
        for z in (Z0 + 3.4, Z0 + 6.8):
            m.bx(-W + 0.2, wy - 0.245, z - 0.08, W - 0.2, wy - 0.175, z + 0.08, 'trim', flat=True)
        # curtains gathered at both sides and a rod
        m.cy(-W - 1.4, wy - 0.45, Z1 + 1.0, 0.1, 0.1, 2 * W + 2.8, 'walnut2', seg=8, rot=(0, 90, 0))
        for sx in (-1, 1):
            for i in range(3):
                xx = sx * (W + 0.55 + i * 0.35)
                m.cy(xx, wy - 0.45 - 0.05 * (i % 2), 0.0, 0.26, 0.2, Z1 + 1.85 - 0.02 * i, 'coral' if i != 1 else 'mustard', seg=7)
            a, b = sorted((sx * (W + 0.3), sx * (W + 1.5)))
            m.colbox(a, wy - 0.8, 0, b, wy, Z1 + 1.8)
        m.parent = Matrix.Identity(4)
        sgn = 1 if name == 'Window' else -1
        lift_where(finish(name, m, bevel=0.02),
                   lambda c, nn: 0.295 < sgn * c.y < 0.33 and sgn * nn.y < -0.9 and Z0 - 0.01 < c.z < Z1 + 0.01 and abs(c.x) < W)
    # picture frames (two designs, both facings)
    for name, R in (('Frame_A', Matrix.Identity(4)), ('Frame_A_R', rz(180)), ('Frame_B', Matrix.Identity(4)), ('Frame_B_R', rz(180))):
        m = K()
        m.parent = R
        wy = 0.5
        if name.startswith('Frame_A'):     # a big landscape print: hills, a sun
            m.bx(-1.6, wy - 0.14, 8.4, 1.6, wy - 0.002, 10.8, 'walnut')
            m.bx(-1.42, wy - 0.15, 8.58, 1.42, wy - 0.14, 10.62, 'cream', flat=True)
            m.bx(-1.2, wy - 0.156, 8.8, 1.2, wy - 0.15, 9.5, 'leaf', flat=True)
            m.cy(0.6, wy - 0.156, 10.0, 0.32, 0.32, 0.006, 'mustard', seg=10, rot=(90, 0, 0), flat=True)
            m.bx(-1.2, wy - 0.153, 9.5, 1.2, wy - 0.15, 10.4, 'glass', flat=True)
        else:                              # two little photos and a round mirror
            for i, (x, z, w, h, c) in enumerate(((-1.1, 9.0, 0.9, 1.2, 'pink'), (0.0, 9.8, 0.8, 1.0, 'tile2'), (1.05, 8.9, 0.9, 1.1, 'sun'))):
                m.bx(x - w / 2, wy - 0.1 - 0.01 * i, z, x + w / 2, wy - 0.002, z + h, ('oak2', 'black', 'trim')[i])
                m.bx(x - w / 2 + 0.12, wy - 0.115 - 0.01 * i, z + 0.12, x + w / 2 - 0.12, wy - 0.1 - 0.01 * i, z + h - 0.12, c, flat=True)
        m.parent = Matrix.Identity(4)
        finish(name, m)
    # SunPatch: afternoon light lying on the boards in front of a window (9 x 6, skewed); just a flat warm decal
    m = K()
    m.up([(-4.2, 2.4), (3.6, 2.4), (5.0, -3.4), (-2.8, -3.4)], 0.014, 'sun')
    for x in (-1.6, 1.0):     # the shadows of the glazing bars
        m.up([(x - 0.12, 2.4), (x + 0.12, 2.4), (x + 1.04, -3.4), (x + 0.8, -3.4)], 0.018, 'oak')
    m.up([(-3.4, 0.3), (4.1, 0.3), (4.15, 0.06), (-3.35, 0.06)], 0.022, 'oak')
    finish('SunPatch', m, hull=0.0, strip=True)


# ================================================================ lounge
def build_lounge(ao):
    # Landmark_Sofa: 14 x 6, seat 2.7, back 5.6; three seat and back cushions, two pillows, a knitted throw
    m = K()
    m.colbox(-7.0, -2.7, 0, 7.0, 3.0, 2.75)
    m.colbox(-7.0, 1.6, 2.75, 7.0, 3.0, 5.6)
    for sx in (-1, 1):
        m.colbox(min(sx * 5.8, sx * 7.0), -2.7, 2.75, max(sx * 5.8, sx * 7.0), 3.0, 4.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 6.4, sy * 2.3, 0, 0.22, 0.16, 0.65, 'walnut2', seg=6)
    m.bx(-6.9, -2.6, 0.65, 6.9, 2.95, 1.7, 'sofaD')                               # base frame
    m.bx(-6.9, 1.55, 1.7, 6.9, 2.95, 5.6, 'sofa', bevel=True)                    # back
    for sx in (-1, 1):
        a, b = sorted((sx * 5.75, sx * 6.95))
        m.bx(a, -2.65, 1.68, b, 2.9, 4.0, 'sofa', bevel=True)                   # arms
        m.cy(sx * 6.35, -2.66, 3.4, 0.62, 0.62, 5.55, 'sofa2', seg=10, rot=(-90, 0, 0))   # rolled arm top
    for i in range(3):
        x0 = -5.7 + i * 3.8
        m.bx(x0 + 0.04, -2.55, 1.7, x0 + 3.76, 1.5, 2.75, 'sofa2', bevel=True)  # seat cushions
        m.bx(x0 + 0.1, 0.6, 2.75, x0 + 3.7, 1.55, 5.3, 'sofa2', bevel=True, rot=(-8, 0, 0))   # back cushions
    m.bx(-5.2, -0.2, 2.75, -3.4, 0.55, 4.6, 'mustard', bevel=True, rot=(-12, 0, 14))   # pillows
    m.bx(3.6, -0.15, 2.75, 5.3, 0.6, 4.5, 'coral', bevel=True, rot=(-12, 0, -10))
    m.bx(3.75, -0.17, 3.3, 5.15, 0.58, 3.4, 'cream', flat=True, rot=(-12, 0, -10))
    # knitted throw over the right arm and down the side
    m.bx(5.6, -1.4, 3.95, 7.05, 1.2, 4.12, 'knit')
    m.bx(6.95, -1.38, 1.6, 7.12, 1.18, 4.1, 'knit')
    for z in (2.0, 2.5, 3.0, 3.5):
        m.bx(7.12, -1.42, z, 7.135, 1.22, z + 0.12, 'coral', flat=True)
    finish('Landmark_Sofa', m, bevel=0.06, ao=ao)

    # CoffeeTable 8 x 4: top at 2.6 on tapered legs (run under); magazines, a mug, a fruit bowl, the remote
    m = K()
    m.colbox(-3.9, -1.9, 2.3, 3.9, 1.9, 2.62)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 3.4, sy * 1.5, 0, 0.12, 0.2, 2.35, 'oak2', seg=6)
            m.colbox(sx * 3.4 - 0.2, sy * 1.5 - 0.2, 0, sx * 3.4 + 0.2, sy * 1.5 + 0.2, 2.3)
    m.bx(-3.9, -1.9, 2.32, 3.9, 1.9, 2.62, 'oak', bevel=True)
    m.bx(-3.7, -1.7, 2.0, 3.7, 1.7, 2.32, 'oak2')
    m.bx(-2.9, -0.9, 2.62, -1.3, 0.3, 2.7, 'coral', rot=(0, 0, 8))                    # magazines
    m.bx(-2.8, -0.85, 2.7, -1.25, 0.2, 2.76, 'tile2', rot=(0, 0, -6))
    m.cy(-0.4, 0.6, 2.62, 0.3, 0.3, 0.55, 'mustard', seg=10)                         # mug
    m.cy(-0.4, 0.6, 3.1, 0.24, 0.24, 0.08, 'walnut2', seg=10, flat=True)
    m.cy(1.8, 0.2, 2.62, 0.45, 0.9, 0.4, 'tile2', seg=12)                            # fruit bowl
    for (x, y, c) in ((1.5, 0.1, 'red'), (2.05, 0.35, 'tyellow'), (1.8, -0.15, 'coral'), (1.85, 0.5, 'tgreen')):
        m.sp(x, y, 3.05, 0.27, c, seg=(8, 5))
    m.bx(2.4, -1.4, 2.62, 3.3, -1.0, 2.75, 'black', rot=(0, 0, 18))                 # remote
    for i, c in enumerate(('red', 'tblue', 'tgreen')):
        m.cy(2.55 + i * 0.2, -1.22 + i * 0.065, 2.75, 0.05, 0.05, 0.03, c, seg=6, flat=True)
    finish('CoffeeTable', m, bevel=0.03, ao=ao)

    # TVStand 12 x 3 against a wall: low walnut console, a big flat TV on its stand, the games console and speakers
    m = K()
    m.colbox(-6.0, -1.5, 0, 6.0, 1.5, 3.2)
    m.colbox(-5.6, 0.2, 3.2, 5.6, 1.0, 10.0)
    for sx in (-1, 1):
        m.cy(sx * 5.5, -1.1, 0, 0.14, 0.1, 0.6, 'walnut2', seg=6)
        m.cy(sx * 5.5, 1.1, 0, 0.14, 0.1, 0.6, 'walnut2', seg=6)
    m.bx(-6.0, -1.5, 0.6, 6.0, 1.5, 3.2, 'walnut', bevel=True)
    for i in range(3):     # three bays: two doors, an open middle shelf with the console
        x0 = -5.8 + i * 3.9
        if i == 1:
            m.bx(x0 + 0.1, -1.505, 0.85, x0 + 3.6, 1.2, 2.95, 'walnut2', flat=True)
            m.bx(x0 + 0.5, -1.2, 0.86, x0 + 3.2, 0.6, 1.55, 'white', bevel=True)          # games console
            m.bx(x0 + 0.6, -1.21, 1.25, x0 + 1.9, -1.2, 1.32, 'teal', flat=True)
            m.bx(x0 + 0.5, -1.0, 1.55, x0 + 3.2, 0.6, 1.62, 'black', flat=True)
            m.bx(x0 + 0.6, -1.0, 1.95, x0 + 3.1, 0.6, 2.25, 'rugB')                     # game boxes
            m.bx(x0 + 0.65, -1.0, 2.25, x0 + 3.05, 0.6, 2.55, 'coral')
        else:
            m.bx(x0 + 0.08, -1.52, 0.75, x0 + 3.65, -1.49, 3.05, 'oak2', flat=True)
            m.cy(x0 + (3.2 if i == 0 else 0.5), -1.52, 1.9, 0.08, 0.08, 0.08, 'steel', seg=6, rot=(90, 0, 0), flat=True)
    m.bx(-1.6, 0.0, 3.2, 1.6, 1.0, 3.32, 'black')                                  # TV foot
    m.bx(-0.3, 0.4, 3.32, 0.3, 0.7, 4.0, 'black')
    m.bx(-5.6, 0.3, 3.9, 5.6, 0.75, 10.0, 'black', bevel=True)                    # TV
    m.bx(-5.35, 0.295, 4.15, 5.35, 0.3, 9.75, 'screen', flat=True)
    m.bx(-5.35, 0.29, 7.8, -0.4, 0.295, 9.75, 'screen2', flat=True)                # a game on screen (simple shapes)
    m.bx(-5.35, 0.289, 4.15, 5.35, 0.29, 5.2, 'tgreen', flat=True)
    m.cy(2.6, 0.289, 7.6, 0.9, 0.9, 0.004, 'tyellow', seg=10, rot=(90, 0, 0), flat=True)
    m.bx(-2.6, 0.287, 5.2, -1.4, 0.289, 6.4, 'red', flat=True)
    for sx in (-1, 1):
        m.bx(sx * 4.6 - 0.45, -1.3, 3.2, sx * 4.6 + 0.45, -0.3, 5.6, 'black')       # speakers
        m.cy(sx * 4.6, -1.3, 4.6, 0.3, 0.3, 0.01, 'steel2', seg=10, rot=(90, 0, 0), flat=True)
        m.cy(sx * 4.6, -1.3, 3.75, 0.18, 0.18, 0.01, 'steel2', seg=8, rot=(90, 0, 0), flat=True)
    finish('TVStand', m, bevel=0.03, ao=ao, shift=WALL_GAP)

    # Controller 3 x 2: a dropped gamepad and its cable (cover the size of a toy car)
    m = K()
    m.colbox(-1.3, -0.8, 0, 1.3, 0.8, 0.7)
    m.bx(-0.75, -0.6, 0.03, 0.75, 0.55, 0.61, 'black', bevel=True)
    for sx in (-1, 1):
        m.cy(sx * 0.95, -0.25, 0.02, 0.45, 0.4, 0.6, 'black', seg=10)
        m.cy(sx * 0.95, -0.25, 0.62, 0.38, 0.38, 0.02, 'screen', seg=10, flat=True)
    m.cy(-0.95, -0.25, 0.64, 0.14, 0.14, 0.18, 'steel2', seg=8)
    for i, (dx, dy, c) in enumerate(((0.95, 0.0, 'tgreen'), (1.15, -0.25, 'red'), (0.75, -0.25, 'tblue'), (0.95, -0.48, 'tyellow'))):
        m.cy(dx, dy, 0.64, 0.09, 0.09, 0.08, c, seg=6, flat=True)
    m.bx(-0.2, 0.55, 0.3, 0.2, 0.75, 0.4, 'black', flat=True)
    for i in range(5):
        a = i * 0.5
        m.bx(-0.12 + 0.35 * math.sin(a), 0.75 + i * 0.12, 0.004 + 0.004 * i, 0.12 + 0.35 * math.sin(a), 0.87 + i * 0.12, 0.12 + 0.004 * i, 'black', flat=True, rot=(0, 0, 20 * math.cos(a)))
    finish('Controller', m, bevel=0.03, ao=ao)

    # Rug 16 x 12: a big woven rug, red field, cream border, blue diamonds, fringe (no collision)
    m = K()
    m.bx(-8.0, -6.0, 0.0, 8.0, 6.0, 0.06, 'rugC', flat=True)
    m.bx(-7.4, -5.4, 0.06, 7.4, 5.4, 0.072, 'rugR', flat=True)
    m.bx(-6.6, -4.6, 0.072, 6.6, 4.6, 0.084, 'rugC', flat=True)
    m.bx(-6.2, -4.2, 0.084, 6.2, 4.2, 0.096, 'rugR', flat=True)
    for i, (x, y, r, c) in enumerate(((0, 0, 2.6, 'rugB'), (0, 0, 1.5, 'mustard'), (0, 0, 0.6, 'rugC'),
                                      (-4.4, 0, 1.0, 'rugB'), (4.4, 0, 1.0, 'rugB'))):
        m.cy(x, y, 0.096 + 0.012 * (i if i < 3 else 1), r, r, 0.012, c, seg=4, flat=True)
    for sx in (-1, 1):
        for j in range(12):
            y = -5.5 + j * 1.0
            m.bx(min(sx * 8.0, sx * 8.45), y - 0.18, 0.0, max(sx * 8.0, sx * 8.45), y + 0.18, 0.03, 'cream', flat=True)
    finish('Rug', m, hull=0.0, strip=True)

    # Bookshelf 6 x 2 against a wall: 12.6 m tall walnut shelving full of books, a plant on top
    m = K()
    rnd = random.Random(77)
    m.colbox(-3.0, -1.0, 0, 3.0, 1.0, 12.6)
    m.bx(-2.83, 0.75, 0.0, 2.83, 0.94, 12.44, 'walnut2', flat=True)                  # back
    for sx in (-1, 1):
        a, b = sorted((sx * 2.82, sx * 3.0))
        m.bx(a, -0.95, 0, b, 0.95, 12.6, 'walnut')
    m.bx(-3.1, -1.05, 12.45, 3.1, 1.0, 12.7, 'walnut', bevel=True)
    lv = [0.6, 3.0, 5.4, 7.8, 10.2, 12.45]
    m.bx(-2.82, -0.95, 0.0, 2.82, 0.75, 0.6, 'walnut2')
    for z in lv[1:-1]:
        m.bx(-2.816, -0.9, z - 0.14, 2.816, 0.75, z, 'walnut', flat=True)
    for i in range(len(lv) - 1):
        shelf_row(m, -2.74, 2.74, lv[i], lv[i + 1] - (0.14 if i < len(lv) - 2 else 0.0), -0.82, 0.72, rnd, objects=(i in (1, 3)), thick=1.5)
    m.cy(1.6, 0.0, 12.7, 0.4, 0.5, 0.9, 'pot', seg=8)
    for (dx, dz, r) in ((-0.2, 1.6, 0.6), (0.35, 1.4, 0.45), (0.0, 2.2, 0.4)):
        m.sp(1.6 + dx, 0.0, 12.7 + dz, r, 'leaf' if dz < 2 else 'leaf2', seg=(6, 4), rot=(0, 0, dz * 30))
    finish('Bookshelf', m, ao=ao, shift=WALL_GAP)

    # Fireplace 10 x 2 against a wall: stone surround, brick firebox with a log fire, walnut mantel with a clock,
    # candles and photos, a mirror above
    m = K()
    m.colbox(-5.0, -0.2, 0, 5.0, 1.0, 8.2)
    m.bx(-5.0, -0.6, 0, 5.0, 1.0, 0.35, 'stone', bevel=True)                       # hearth
    for sx in (-1, 1):
        a, b = sorted((sx * 2.6, sx * 4.6))
        m.bx(a, -0.2, 0.35, b, 0.99, 7.2, 'stone', bevel=True)                   # pillars
    m.bx(-2.6, -0.2, 5.6, 2.6, 0.99, 7.2, 'stone', bevel=True)                    # lintel
    m.bx(-2.6, 0.2, 0.35, 2.6, 0.99, 5.6, 'brick2', flat=True)                     # firebox
    for z in (1.4, 2.6, 3.8, 5.0):
        m.bx(-2.6, 0.195, z - 0.04, 2.6, 0.2, z + 0.04, 'brick', flat=True)
    m.bx(-1.8, -0.1, 0.36, 1.8, 0.6, 0.6, 'black', flat=True)                       # grate
    for i, (x, rot) in enumerate(((-0.7, 8), (0.6, -10), (0.0, 0))):
        m.cy(x - 1.0, 0.1 + 0.1 * i, 0.75 + 0.35 * (i == 2), 0.28, 0.28, 2.0, 'walnut' if i % 2 else 'walnut2', seg=7, rot=(0, 90, rot))
    for (x, h, w, c) in ((-0.6, 2.4, 0.7, 'fire'), (0.4, 2.0, 0.6, 'fire'), (-0.1, 3.0, 0.8, 'fire2'), (0.9, 1.4, 0.4, 'fire2')):
        yf = 0.16 - 0.03 * (c == 'fire2') - 0.004 * x            # flames: flat tongues in front of the bricks
        m.tri([(x + w, yf, 1.0), (x, yf, 1.0 + h), (x - w, yf, 1.0)], c)
    m.bx(-5.3, -0.7, 7.2, 5.3, 1.0, 7.6, 'walnut', bevel=True)                    # mantel shelf
    m.bx(-1.0, -0.35, 7.6, 1.0, 0.6, 9.4, 'oak2', bevel=True)                      # mantel clock
    m.cy(0.0, -0.36, 8.6, 0.65, 0.65, 0.01, 'cream', seg=12, rot=(90, 0, 0), flat=True)
    m.bx(-0.03, -0.38, 8.58, 0.03, -0.37, 9.1, 'black', flat=True)
    m.bx(-0.02, -0.386, 8.57, 0.4, -0.376, 8.63, 'black', flat=True)
    for (x, h) in ((-3.8, 1.6), (-3.3, 1.1), (3.6, 1.4)):
        m.cy(x, 0.2, 7.6, 0.17, 0.17, h, 'cream', seg=8)                           # candles
        m.sp(x, 0.2, 7.6 + h + 0.2, 0.12, 'fire2', seg=(6, 4), scale=(1, 1, 1.6), flat=True)
    m.bx(1.8, 0.35, 7.6, 2.9, 0.55, 9.0, 'black', rot=(-8, 0, 0))                  # photo
    m.bx(1.95, 0.33, 7.75, 2.75, 0.34, 8.85, 'pink', flat=True, rot=(-8, 0, 0))
    m.bx(-4.2, 0.85, 9.6, 4.2, 0.99, 15.0, 'mustard', bevel=True)                 # mirror frame
    m.bx(-3.8, 0.84, 10.0, 3.8, 0.85, 14.6, 'glass', flat=True)
    m.bx(-3.0, 0.835, 12.2, -1.2, 0.84, 12.4, 'white', flat=True, rot=(0, 40, 0))
    finish('Fireplace', m, ao=ao, shift=WALL_GAP)

    # Plant_Fig 3 x 3: a fiddle-leaf fig in a terracotta pot, 9 m tall
    m = K()
    m.colbox(-1.1, -1.1, 0, 1.1, 1.1, 2.4)
    m.cy(0, 0, 0, 0.9, 1.15, 2.2, 'pot', seg=10)
    m.cy(0, 0, 2.2, 1.2, 1.2, 0.2, 'pot', seg=10)
    m.cy(0, 0, 2.38, 1.05, 1.05, 0.04, 'walnut2', seg=10, flat=True)
    m.cy(0, 0, 2.4, 0.1, 0.08, 5.0, 'walnut', seg=6)
    rnd = random.Random(5)
    for i in range(9):
        a = i * 2.4
        z = 3.4 + i * 0.6
        r = 1.1 - 0.05 * i
        m.sp(math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, z, 0.75 - 0.03 * i, 'leaf' if i % 2 else 'leaf2', seg=(6, 4), scale=(1.0, 0.45, 1.3), rot=(rnd.uniform(-30, 30), 0, math.degrees(a) + 90))
    finish('Plant_Fig', m, ao=ao)

    # Plant_Snake 2 x 2: snake plant in a cream pot
    m = K()
    m.colbox(-0.8, -0.8, 0, 0.8, 0.8, 1.8)
    m.cy(0, 0, 0, 0.6, 0.75, 1.8, 'cream', seg=10)
    m.cy(0, 0, 1.78, 0.68, 0.68, 0.04, 'walnut2', seg=10, flat=True)
    for i in range(7):
        a = i * 0.9
        h = 2.6 + (i % 3) * 0.7
        m.box((math.cos(a) * 0.3, math.sin(a) * 0.3, 1.8 + h / 2), (0.32, 0.08, h), 'leaf2' if i % 2 else 'tgreen', rot=(12 * math.sin(a), 12 * math.cos(a), math.degrees(a)), bevel=False)
    finish('Plant_Snake', m, ao=ao)

    # FloorLamp 2 x 2: brass stem, linen drum shade lit warm
    m = K()
    m.colbox(-0.3, -0.3, 0, 0.3, 0.3, 9.0)
    m.cy(0, 0, 0, 0.85, 0.75, 0.2, 'black', seg=12)
    m.cy(0, 0, 0.2, 0.08, 0.08, 8.0, 'mustard', seg=6)
    m.cy(0, 0, 8.0, 1.0, 0.75, 1.9, 'lamp', seg=12, caps=False)
    m.cy(0, 0, 8.02, 0.95, 0.95, 0.01, 'fire2', seg=12, flat=True)
    finish('FloorLamp', m, ao=ao)


# ================================================================ kitchen and dining
def counter_base(m, sink=False, stove=False):
    """3 x 4 counter module against a wall (+Y): base cabinet, butcher-block top, tiled backsplash, upper cabinet."""
    m.colbox(-1.5, -2.0, 0, 1.5, 2.0, 5.5)
    m.colbox(-1.5, 0.6, 9.4, 1.5, 2.0, 14.6)
    m.bx(-1.5, -1.7, 0.0, 1.5, 2.0, 0.5, 'walnut2', flat=True)                    # toe kick
    m.bx(-1.5, -1.85, 0.5, 1.5, 2.0, 5.15, 'cab2')                                 # carcass
    m.bx(-1.53, -2.05, 5.15, 1.53, 2.0, 5.5, 'block', bevel=True)                  # butcher block
    m.quad([(1.5, 1.99, 5.5), (1.5, 1.99, 9.4), (-1.5, 1.99, 9.4), (-1.5, 1.99, 5.5)], 'tile')   # backsplash
    for z in (6.5, 7.5, 8.5):
        m.bx(-1.5, 1.98, z - 0.03, 1.5, 1.985, z + 0.03, 'tile2', flat=True)
    m.bx(-1.5, 0.6, 9.4, 1.5, 2.0, 14.6, 'cab', bevel=True)                         # upper cabinet
    m.bx(-1.4, 0.58, 9.6, -0.04, 0.6, 14.4, 'cab', flat=True)
    m.bx(0.04, 0.58, 9.6, 1.4, 0.6, 14.4, 'cab', flat=True)
    for sx in (-1, 1):
        m.bx(sx * 0.25 - 0.05, 0.5, 10.0, sx * 0.25 + 0.05, 0.58, 10.9, 'steel2', flat=True)
    if not stove:
        for sx in (-1, 1):   # two doors with knobs
            a, b = sorted((sx * 0.04, sx * 1.42))
            m.bx(a, -1.88, 0.62, b, -1.85, 3.9, 'cab2', flat=True)
            m.bx(a + 0.15, -1.9, 0.9, b - 0.15, -1.88, 3.6, 'mint2', flat=True)
            m.cy(sx * 0.3, -1.9, 3.4, 0.08, 0.08, 0.12, 'steel', seg=6, rot=(90, 0, 0), flat=True)
        m.bx(-1.42, -1.88, 4.0, 1.42, -1.85, 5.05, 'cab2', flat=True)            # drawer
        m.bx(-0.4, -1.95, 4.45, 0.4, -1.88, 4.6, 'steel', flat=True)
    if sink:
        m.bx(-1.1, -1.5, 5.48, 1.1, 0.6, 5.52, 'steel2', flat=True)                # sink bowl rim
        m.bx(-0.95, -1.35, 5.52, 0.95, 0.45, 5.53, 'steel', flat=True)
        m.cy(0.0, 1.2, 5.5, 0.12, 0.12, 2.0, 'steel', seg=8)                       # faucet
        m.beam((0.0, 1.2, 7.4), (0.0, 0.3, 7.4), 0.16, 'steel')
        m.cy(0.0, 0.3, 6.9, 0.08, 0.08, 0.5, 'steel', seg=6)
        m.bx(-1.35, -1.0, 5.5, -1.0, -0.4, 6.4, 'tile2', rot=(0, 0, 12))           # dish soap
    if stove:
        m.bx(-1.42, -1.88, 0.62, 1.42, -1.85, 4.2, 'black', flat=True)            # oven door
        m.bx(-1.1, -1.9, 1.4, 1.1, -1.88, 3.4, 'screen', flat=True)
        m.bx(-1.0, -2.1, 3.8, 1.0, -1.9, 3.95, 'steel')                            # handle
        for i in range(4):
            m.cy(-1.05 + i * 0.7, -1.9, 4.65, 0.13, 0.13, 0.1, 'black', seg=8, rot=(90, 0, 0), flat=True)
        m.bx(-1.4, -1.6, 5.5, 1.4, 1.2, 5.6, 'black', flat=True)                   # hob
        for (x, y, r) in ((-0.7, -0.8, 0.45), (0.7, -0.8, 0.35), (-0.7, 0.4, 0.35), (0.7, 0.4, 0.45)):
            m.cy(x, y, 5.6, r, r, 0.02, 'steel2', seg=10, flat=True)
        m.cy(-0.7, -0.8, 5.62, 0.9, 0.9, 0.6, 'red', seg=12)                       # a pot on the hob
        m.cy(-0.7, -0.8, 6.22, 0.92, 0.92, 0.1, 'red', seg=12)
        m.cy(-0.7, -0.8, 6.32, 0.15, 0.15, 0.15, 'black', seg=6)
        m.poly([(-1.5, 0.6), (1.5, 0.6), (1.2, 1.9), (-1.2, 1.9)], 9.0, 9.4, 'steel')   # hood under the cabinet
        m.bx(-1.3, 0.75, 8.99, 1.3, 1.8, 9.0, 'steel2', flat=True)


def build_kitchen(ao):
    for name, kw in (('Counter', {}), ('Counter_Sink', {'sink': True}), ('Counter_Stove', {'stove': True})):
        m = K()
        counter_base(m, **kw)
        if not kw:   # props on the plain counter: a toaster, a jar, a cutting board, fruit
            m.bx(-1.1, 0.2, 5.5, 0.1, 1.2, 6.5, 'mint', bevel=True)
            for x in (-0.75, -0.25):
                m.bx(x - 0.12, 0.45, 6.49, x + 0.12, 0.95, 6.52, 'black', flat=True)
            m.cy(0.8, 0.9, 5.5, 0.38, 0.38, 1.3, 'glass', seg=10)
            m.cy(0.8, 0.9, 6.8, 0.42, 0.42, 0.15, 'walnut', seg=10)
            m.bx(-0.6, -1.7, 5.5, 1.2, -0.5, 5.62, 'oak', rot=(0, 0, -7))
            m.sp(0.6, -1.05, 5.92, 0.3, 'red', seg=(8, 5))
        finish(name, m, bevel=0.03, ao=ao, shift=WALL_GAP)

    # Fridge 5 x 4: a retro mint fridge, 11.5 m, chrome handles, drawings and magnets on the door
    m = K()
    m.colbox(-2.5, -2.0, 0, 2.5, 2.0, 11.6)
    m.bx(-2.4, -1.9, 0.5, 2.4, 2.0, 11.5, 'mint', bevel=True)
    m.bx(-2.3, -1.8, 0.0, 2.3, 1.9, 0.5, 'steel2')
    m.bx(-2.4, -1.94, 7.6, 2.4, -1.9, 7.7, 'mint2', flat=True)                      # door split
    for (z0, z1) in ((5.6, 7.3), (8.0, 9.6)):
        m.bx(1.7, -2.3, z0, 1.95, -2.0, z1, 'steel')
        m.bx(1.75, -2.0, z0 + 0.05, 1.9, -1.9, z0 + 0.2, 'steel', flat=True)
        m.bx(1.75, -2.0, z1 - 0.2, 1.9, -1.9, z1 - 0.05, 'steel', flat=True)
    for i, (x, z, w, h, c) in enumerate(((-1.3, 4.6, 1.5, 1.9, 'paper'), (0.5, 3.4, 1.3, 1.5, 'cream'), (-1.0, 8.6, 1.4, 1.2, 'paper'))):
        m.bx(x - w / 2, -1.92 - 0.004 * i, z, x + w / 2, -1.9, z + h, c, flat=True, rot=(0, 4 - 4 * i, 0))
    m.bx(-1.8, -1.935, 5.0, -0.8, -1.93, 5.6, 'tblue', flat=True)                  # a crayon house, a sun
    m.tri([(-0.7, -1.936, 5.6), (-1.3, -1.936, 6.1), (-1.9, -1.936, 5.6)], 'red')
    m.cy(0.9, -1.93, 4.4, 0.32, 0.32, 0.01, 'tyellow', seg=8, rot=(90, 0, 0), flat=True)
    m.bx(0.1, -1.93, 3.6, 0.9, -1.925, 3.75, 'tgreen', flat=True)
    for (x, z, c) in ((-0.5, 6.4, 'red'), (0.2, 4.95, 'tblue'), (-0.4, 9.9, 'tyellow'), (-1.85, 6.6, 'tgreen')):
        m.cy(x, -1.905, z, 0.16, 0.16, 0.1, c, seg=8, rot=(90, 0, 0))
    finish('Fridge', m, bevel=0.06, ao=ao, shift=WALL_GAP)

    # Island 12 x 6: cabinet base 5.4 m, overhanging butcher-block top on the stool side (-Y), a bowl, a board
    m = K()
    m.colbox(-6.0, -2.4, 0, 6.0, 3.0, 5.5)
    m.bx(-5.7, -1.8, 0.0, 5.7, 2.75, 0.5, 'walnut2', flat=True)
    m.bx(-5.8, -1.9, 0.5, 5.8, 2.85, 5.15, 'cab')
    for i in range(4):
        x0 = -5.6 + i * 2.85
        m.bx(x0, 2.85, 0.75, x0 + 2.65, 2.88, 4.9, 'cab2', flat=True)
        m.bx(x0 + 1.0, 2.88, 4.3, x0 + 1.65, 2.95, 4.42, 'steel', flat=True)
    for i in range(6):   # tongue-and-groove on the stool side
        m.bx(-5.8 + 0.5 + i * 1.95, -1.93, 0.6, -5.8 + 0.58 + i * 1.95, -1.9, 5.05, 'trim2', flat=True)
    m.bx(-6.0, -2.45, 5.15, 6.0, 3.0, 5.5, 'block', bevel=True)
    m.cy(-2.5, 0.6, 5.5, 0.9, 1.4, 0.55, 'tile2', seg=12)
    for (x, y, c) in ((-2.8, 0.4, 'red'), (-2.2, 0.8, 'tgreen'), (-2.5, 0.1, 'tyellow')):
        m.sp(x, y, 6.15, 0.36, c, seg=(8, 5))
    m.bx(1.0, -0.6, 5.5, 3.6, 1.2, 5.65, 'oak', rot=(0, 0, 8))
    for i in range(4):
        m.cy(1.6 + i * 0.5, 0.3, 5.65, 0.22, 0.22, 0.12, 'coral' if i % 2 else 'tgreen', seg=8)
    finish('Island', m, bevel=0.03, ao=ao)

    # Stool 2 x 2: bar stool, seat at 4.4 m on splayed legs (run under), a footrest ring
    m = K()
    m.colbox(-0.75, -0.75, 4.0, 0.75, 0.75, 4.5)
    m.cy(0, 0, 4.1, 0.85, 0.85, 0.35, 'mustard', seg=12)
    m.cy(0, 0, 3.9, 0.7, 0.75, 0.2, 'walnut', seg=10)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        x, y = math.cos(a), math.sin(a)
        m.beam((x * 0.45, y * 0.45, 3.95), (x * 0.78, y * 0.78, 0.0), 0.14, 'walnut')
        m.colbox(x * 0.78 - 0.1, y * 0.78 - 0.1, 0.0, x * 0.78 + 0.1, y * 0.78 + 0.1, 3.9)
    m.cy(0, 0, 1.5, 0.72, 0.72, 0.1, 'walnut2', seg=10, caps=False)
    finish('Stool', m, bevel=0.03, ao=ao)

    # DiningTable 10 x 6: top at 4.5 m on turned legs (run under), runner, vase of tulips, plates
    m = K()
    m.colbox(-5.0, -3.0, 4.15, 5.0, 3.0, 4.55)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 4.4, sy * 2.4
            m.cy(x, y, 0, 0.22, 0.3, 4.15, 'oak2', seg=8)
            m.sp(x, y, 1.0, 0.36, 'oak2', seg=(6, 4))
            m.colbox(x - 0.3, y - 0.3, 0, x + 0.3, y + 0.3, 4.15)
    m.bx(-4.6, -2.6, 3.7, 4.6, 2.6, 4.2, 'oak2')                                   # apron
    m.bx(-5.0, -3.0, 4.2, 5.0, 3.0, 4.55, 'oak', bevel=True)
    m.bx(-1.3, -3.2, 4.55, 1.3, 3.2, 4.58, 'cream', flat=True)                     # runner, hanging over the edges
    for sy in (-1, 1):
        a, b = sorted((sy * 3.0, sy * 3.03))
        m.bx(-1.29, a, 3.9, 1.29, b, 4.575, 'cream', flat=True)
    m.cy(0.0, 0.0, 4.58, 0.4, 0.55, 1.4, 'tile2', seg=10)                          # vase + tulips
    for i, c in enumerate(('red', 'pink', 'mustard', 'coral', 'red')):
        a = i * 1.26
        x, y = math.cos(a) * 0.3, math.sin(a) * 0.3
        m.beam((0, 0, 5.8), (x * 2, y * 2, 7.0 + 0.2 * (i % 2)), 0.06, 'leaf2')
        m.sp(x * 2, y * 2, 7.2 + 0.2 * (i % 2), 0.28, c, seg=(6, 4), scale=(1, 1, 1.3))
    for (x, y) in ((-3.2, -1.5), (3.2, -1.5), (-3.2, 1.5), (3.2, 1.5)):
        m.cy(x, y, 4.55, 0.85, 0.85, 0.06, 'white', seg=8, flat=True)
        m.cy(x, y, 4.61, 0.55, 0.55, 0.02, 'tile2', seg=8, flat=True)
    # the pendant lamp over the table, hung from the 18 m ceiling: a mustard dome on a long cord
    m.cy(0, 0, 17.84, 0.45, 0.35, 0.14, 'trim', seg=8)
    m.cy(0, 0, 12.9, 0.04, 0.04, 4.95, 'black', seg=4, flat=True)
    m.cy(0, 0, 11.5, 2.0, 0.4, 1.4, 'mustard', seg=12, caps=False)
    m.cy(0, 0, 11.48, 1.95, 1.95, 0.02, 'lamp', seg=12, flat=True)
    finish('DiningTable', m, bevel=0.03, ao=ao)

    # DiningChair 3 x 3: spindle-back chair, seat 2.8 m; faces -Y as authored (flip turns it round)
    m = K()
    m.colbox(-1.2, -1.2, 2.5, 1.2, 1.2, 2.9)
    m.colbox(-1.2, 0.85, 2.9, 1.2, 1.2, 6.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 1.0, sy * 1.0, 0, 0.13, 0.16, 2.6, 'oak2', seg=6)
            m.colbox(sx * 1.0 - 0.16, sy * 1.0 - 0.16, 0, sx * 1.0 + 0.16, sy * 1.0 + 0.16, 2.5)
    m.bx(-1.2, -1.2, 2.55, 1.2, 1.2, 2.85, 'oak', bevel=True)
    m.bx(-1.0, -1.0, 2.85, 1.0, 0.9, 3.0, 'mustard', bevel=True)                  # seat pad
    for sx in (-1, 1):
        m.cy(sx * 1.0, 1.0, 2.84, 0.12, 0.12, 3.1, 'oak2', seg=6)
    for i in range(4):
        m.cy(-0.6 + i * 0.4, 1.0, 2.83, 0.07, 0.07, 2.6, 'oak2', seg=6)
    m.bx(-1.15, 0.8, 5.4, 1.15, 1.2, 6.0, 'oak', bevel=True)
    finish('DiningChair', m, bevel=0.03, ao=ao)

    # Sideboard 10 x 3 against a wall: walnut cabinet, a lamp, a bowl, a stack of plates
    m = K()
    m.colbox(-5.0, -1.5, 0, 5.0, 1.5, 5.0)
    for sx in (-1, 1):
        m.cy(sx * 4.6, -1.1, 0, 0.14, 0.1, 0.8, 'walnut2', seg=6)
        m.cy(sx * 4.6, 1.1, 0, 0.14, 0.1, 0.8, 'walnut2', seg=6)
    m.bx(-5.0, -1.5, 0.8, 5.0, 1.5, 4.9, 'walnut', bevel=True)
    for i in range(4):
        x0 = -4.85 + i * 2.43
        m.bx(x0, -1.52, 1.0, x0 + 2.33, -1.5, 4.7, 'oak2', flat=True)
        m.bx(x0 + 0.1, -1.535, 1.1, x0 + 2.23, -1.52, 4.6, ('mustard', 'cab2', 'cab2', 'mustard')[i], flat=True)
        m.cy(x0 + (2.0 if i % 2 == 0 else 0.33), -1.54, 2.9, 0.08, 0.08, 0.1, 'steel', seg=6, rot=(90, 0, 0), flat=True)
    m.cy(-3.0, 0.3, 4.9, 0.5, 0.35, 2.2, 'tile2', seg=10)                          # lamp
    m.cy(-3.0, 0.3, 7.1, 1.0, 0.7, 1.4, 'lamp', seg=10, caps=False)
    m.cy(-3.0, 0.3, 7.12, 0.95, 0.95, 0.01, 'fire2', seg=10, flat=True)
    for i in range(5):
        m.cy(2.6, 0.3, 4.9 + i * 0.1, 0.9, 0.9, 0.094, 'white' if i % 2 else 'tile', seg=12)
    m.cy(0.2, 0.0, 4.9, 0.6, 1.0, 0.5, 'coral', seg=12)
    finish('Sideboard', m, bevel=0.03, ao=ao, shift=WALL_GAP)


# ================================================================ clutter (cover)
def build_clutter(ao):
    # Cushion 3 x 3: a sofa cushion fallen on the floor
    m = K()
    m.colbox(-1.4, -1.2, 0, 1.4, 1.2, 1.1)
    m.bx(-1.35, -1.15, 0.0, 1.35, 1.15, 1.05, 'coral', bevel=True, rot=(0, 0, 9))
    m.bx(-1.36, -0.2, 0.3, 1.36, 0.2, 0.75, 'cream', flat=True, rot=(0, 0, 9))
    finish('Cushion', m, bevel=0.18, ao=ao)
    # Basket 3 x 3: a laundry basket with clothes spilling out
    m = K()
    m.colbox(-1.3, -1.3, 0, 1.3, 1.3, 2.4)
    m.cy(0, 0, 0, 1.1, 1.3, 2.2, 'birch', seg=12, caps=False)
    m.cy(0, 0, 0.0, 1.1, 1.1, 0.05, 'birch', seg=12)
    for i in range(4):
        m.cy(0, 0, 0.4 + i * 0.5, 1.142 + 0.0402 * i + 0.012, 1.142 + 0.0402 * i + 0.032, 0.12, 'oak2', seg=12, caps=False, flat=True)
    m.cy(0, 0, 2.15, 1.32, 1.32, 0.15, 'oak', seg=12)
    m.sp(-0.3, 0.2, 2.2, 0.9, 'rugB', seg=(8, 5), scale=(1.2, 1.0, 0.5))
    m.sp(0.5, -0.3, 2.35, 0.7, 'pink', seg=(8, 5), scale=(1.0, 1.0, 0.55))
    m.bx(0.8, -1.6, 0.0, 1.5, -0.6, 2.3, 'mustard', rot=(0, 30, -20))              # a sleeve hanging out
    finish('Basket', m, ao=ao)
    # ToyBox 3 x 3: an open cardboard box full of toys
    m = K()
    m.colbox(-1.3, -1.3, 0, 1.3, 1.3, 2.3)
    m.bx(-1.25, -1.25, 0, 1.25, 1.25, 2.2, 'cardboard')
    m.bx(-1.1, -1.1, 2.2, 1.1, 1.1, 2.21, 'cardboard2', flat=True)
    for sx in (-1, 1):
        m.bx(sx * 1.25 - 0.03, -1.2, 2.15, sx * 1.25 + 0.03, 1.2, 3.1, 'cardboard', rot=(0, sx * -35, 0))
    m.bx(-1.2, -1.25, 2.15, 1.2, -1.19, 2.8, 'cardboard', rot=(40, 0, 0))
    m.sp(-0.4, 0.3, 2.4, 0.5, 'red', seg=(8, 5))
    m.bx(0.2, -0.5, 2.2, 0.9, 0.2, 2.9, 'tblue', rot=(10, 15, 20))
    m.bx(0.3, 0.4, 2.2, 0.6, 0.7, 3.3, 'tyellow', rot=(-15, 10, 0))
    m.bx(-0.8, -1.26, 0.8, 0.8, -1.25, 1.5, 'navy', flat=True)                     # TOYS label band
    finish('ToyBox', m, ao=ao)
    # Block_A..C: toy blocks (1 cell, 0.92 m) with a raised shape on the faces
    for name, (c, c2, kind) in (('Block_A', ('red', 'white', 'circle')), ('Block_B', ('tblue', 'tyellow', 'square')), ('Block_C', ('tgreen', 'white', 'tri'))):
        m = K()
        m.bx(-0.46, -0.46, 0, 0.46, 0.46, 0.92, c, bevel=True)
        for i in range(4):
            m.parent = rz(90 * i)
            if kind == 'circle':
                m.cy(0, -0.466, 0.46, 0.26, 0.26, 0.01, c2, seg=10, rot=(90, 0, 0), flat=True)
            elif kind == 'square':
                m.bx(-0.24, -0.47, 0.22, 0.24, -0.46, 0.7, c2, flat=True)
            else:
                m.cy(0, -0.466, 0.42, 0.3, 0.3, 0.01, c2, seg=3, rot=(90, 0, 0), flat=True)
        m.parent = Matrix.Identity(4)
        finish(name, m, bevel=0.06, ao=ao)
    # Sneaker 3 x 2: a kid's sneaker on its side (cover)
    m = K()
    m.colbox(-1.4, -0.7, 0, 1.4, 0.7, 1.4)
    m.bx(-1.4, -0.65, 0, 1.4, 0.65, 0.3, 'white', bevel=True)
    m.bx(-1.3, -0.6, 0.3, 0.6, 0.6, 1.3, 'tblue', bevel=True)
    m.sp(0.7, 0, 0.6, 0.62, 'tblue', seg=(8, 5), scale=(1.2, 0.95, 0.75))
    m.bx(-0.9, -0.62, 0.7, -0.2, 0.62, 0.82, 'white', flat=True)
    m.bx(-0.9, -0.62, 1.0, -0.2, 0.62, 1.12, 'white', flat=True)
    m.bx(-1.31, -0.627, 0.32, -0.7, 0.627, 1.32, 'red', flat=True)
    finish('Sneaker', m, bevel=0.06, ao=ao)
    # Mug 2 x 2: a giant mug left on the floor
    m = K()
    m.colbox(-0.8, -0.8, 0, 0.8, 0.8, 2.0)
    m.cy(0, 0, 0, 0.75, 0.75, 2.0, 'cream', seg=12)
    m.cy(0, 0, 1.96, 0.62, 0.62, 0.05, 'walnut2', seg=12, flat=True)
    m.cy(0, 0, 0.6, 0.76, 0.76, 0.5, 'coral', seg=12, flat=True, caps=False)
    m.cy(0.75, 0, 1.0, 0.45, 0.45, 0.16, 'cream', seg=10, rot=(90, 0, 0))
    finish('Mug', m, ao=ao)
    # BookPile 3 x 2: picture books tumbled on the floor
    m = K()
    m.colbox(-1.4, -0.9, 0, 1.4, 0.9, 1.1)
    z = 0.0
    for i, (c, a) in enumerate((('rugB', 4), ('mustard', -9), ('pink', 6), ('tgreen', -3))):
        t = 0.24 + 0.03 * (i % 2)
        m.box((0.05 * (i % 2), 0.03 * i, z + t / 2 + 0.004), (2.4 - 0.15 * i, 1.6 - 0.1 * i, t - 0.004), c, rot=(0, 0, a), bevel=False)
        m.box((0.05 * (i % 2), 0.03 * i, z + t / 2 + 0.004), (2.4 - 0.15 * i - 0.12, 1.6 - 0.1 * i + 0.012, t - 0.07), 'paper', rot=(0, 0, a), bevel=False)
        m.flat()
        z += t + 0.004
    finish('BookPile', m, ao=ao)
    # ToyTruck 4 x 2: a yellow dump truck
    m = K()
    m.colbox(-1.9, -0.9, 0, 1.9, 0.9, 1.9)
    for sx in (-1.2, 1.2):
        for sy in (-1, 1):
            m.cy(sx, sy * 0.78, 0.45, 0.45, 0.45, 0.3, 'black', seg=10, rot=(90, 0, 0))
            m.cy(sx, sy * 0.95, 0.45, 0.2, 0.2, 0.02, 'steel', seg=8, rot=(90, 0, 0), flat=True)
    m.bx(-1.9, -0.75, 0.45, 1.9, 0.75, 0.85, 'black')
    m.bx(0.6, -0.72, 0.85, 1.85, 0.72, 1.85, 'tyellow', bevel=True)                # cab
    m.bx(1.5, -0.73, 1.2, 1.86, 0.73, 1.7, 'glass', flat=True)
    m.bx(-1.85, -0.74, 0.85, 0.5, 0.74, 1.75, 'red', bevel=True, rot=(0, -10, 0))   # tipper
    finish('ToyTruck', m, bevel=0.05, ao=ao)
    # Ball 3 x 3: a striped beach ball
    m = K()
    m.colbox(-1.2, -1.2, 0, 1.2, 1.2, 2.4)
    m.sp(0, 0, 1.2, 1.2, 'red', seg=(12, 7))
    m.sp(0, 0, 1.2, 1.2, 'white', seg=(12, 7), scale=(1.035, 0.42, 1.035), flat=True)      # bands
    m.sp(0, 0, 1.2, 1.2, 'tblue', seg=(12, 7), scale=(0.3, 1.05, 1.05), rot=(0, 0, 45), flat=True)
    m.cy(0, 0, 2.38, 0.3, 0.3, 0.04, 'white', seg=10, flat=True)
    finish('Ball', m, ao=ao)


# ================================================================ ceiling
def build_ceiling():
    m = K()
    corners = [(-0.51, -0.51), (0.51, -0.51), (0.51, 0.51), (-0.51, 0.51)]
    pts = [(x, y, -0.006 - 0.003 * (x + 0.51) - 0.007 * (y + 0.51)) for x, y in corners]
    m.quad([pts[3], pts[2], pts[1], pts[0]], 'ceil')
    normals_up(finish('CeilingTile', m, hull=0.0, strip=True))


# ================================================================ gate, trail, hatch
def build_gate(ao):
    """GateFrame: the doorway between rooms is a giant white interior door (7.1 m wide incl. casing, 13 m tall) with
    the 3 m gate as its pet flap, the wall over it to the ceiling, both faces alike. Half width 3.55 and depth 0.7, so
    it covers the two wall cells either side and closes the trail's end up to the ceiling. GateShutter: the flap."""
    HW, HD, OW, OH = 3.55, 0.8, 1.5, 3.4
    m = K()
    m.colbox(-HW, -HD, 0, -OW, HD, FRAME_H)
    m.colbox(OW, -HD, 0, HW, HD, FRAME_H)
    # body: the door slab and the wall over it (the flap opening cut out)
    for sx in (-1, 1):
        a, b = sorted((sx * (OW + 0.02), sx * (HW - 0.03)))
        m.bx(a, -0.35, 0, b, 0.35, FRAME_H - 0.02, 'trim', flat=True)
    m.bx(-OW - 0.02, -0.35, OH, OW + 0.02, 0.35, FRAME_H - 0.02, 'trim', flat=True)
    # flap tunnel liners
    for sx in (-1, 1):
        a, b = sorted((sx * (OW - 0.012), sx * (OW + 0.1)))
        m.bx(a, -0.49, 0, b, 0.49, OH + 0.1, 'steel2', flat=True)
    m.bx(-OW - 0.05, -0.48, OH - 0.012, OW + 0.05, 0.48, OH + 0.09, 'steel2', flat=True)
    for s in (-1, 1):
        R = rz(0 if s < 0 else 180)
        m.parent = R
        y = -HD
        # casing around the giant door (jambs and head), the wall above in the room paint is replaced by a plain
        # plaster panel (trim) up to the ceiling, with a crown line
        for sx in (-1, 1):
            a, b = sorted((sx * 3.05, sx * HW))
            m.bx(a, y, 0, b, -0.3, 13.6, 'trim', bevel=True)
        m.bx(-HW + 0.01, y - 0.006, 13.0, HW - 0.01, -0.31, 13.8, 'trim', bevel=True)
        m.bx(-HW - 0.05, y - 0.06, 13.8, HW + 0.05, -0.32, 14.0, 'trim2', flat=True)
        m.bx(-HW + 0.025, y - 0.1, 14.0, HW - 0.025, -0.33, FRAME_H - 0.03, 'wains', flat=True)   # soffit panel, proud of every wall trim
        m.bx(-HW - 0.05, y - 0.14, 17.15, HW + 0.05, -0.34, 17.65, 'trim', flat=True)
        # the door slab: six raised panels, a brass knob, hinges on one side
        # in front of every wall trim (skirting 0.2 proud); built around the flap opening (|x| < OW, z < OH) so the
        # opening is see-through once the flap rolls up (a solid slab here hid the open gate)
        for sx in (-1, 1):
            a, b = sorted((sx * (OW + 0.004), sx * 3.046))
            m.bx(a, y + 0.06, 0.0, b, -0.304, 13.0, 'mustard')
        m.bx(-OW - 0.004, y + 0.06, OH + 0.02, OW + 0.004, -0.304, 13.0, 'mustard')
        for (z0, z1) in ((OH + 0.6, 4.2), (4.6, 7.8), (8.4, 12.4)):     # raised panels (the flap replaces the bottom pair)
            for sx in (-1, 1):
                a, b = sorted((sx * 0.35, sx * 2.6))
                m.bx(a, y + 0.025, z0, b, y + 0.06, z1, 'fire2', flat=True)
        m.sp(2.45 * -s, y - 0.2, 6.8, 0.32, 'steel', seg=(8, 5))
        m.cy(2.45 * -s, y + 0.015, 6.8, 0.45, 0.45, 0.04, 'steel2', seg=10, rot=(90, 0, 0), flat=True)
        m.bx(2.3 * -s - 0.08, y + 0.012, 5.9, 2.3 * -s + 0.08, y + 0.055, 6.28, 'black', flat=True)   # keyhole plate
        # flap surround (the pet door frame), teal gate lights and a paw sign
        for sx in (-1, 1):
            a, b = sorted((sx * (OW - 0.006), sx * (OW + 0.4)))
            m.bx(a, y - 0.06, 0, b, y + 0.125, OH + 0.39, 'steel', bevel=True)
        m.bx(-OW - 0.39, y - 0.066, OH, OW + 0.39, y + 0.12, OH + 0.4, 'steel', bevel=True)
        for sx in (-1, 1):
            m.bx(sx * 1.0 - 0.25, y - 0.1, OH + 0.12, sx * 1.0 + 0.25, y - 0.06, OH + 0.3, 'teal', flat=True)
        m.cy(0, y + 0.02, 4.6, 0.36, 0.36, 0.04, 'navy', seg=10, rot=(90, 0, 0), flat=True)
        for (px, pz) in ((-0.35, 5.05), (-0.12, 5.2), (0.12, 5.2), (0.35, 5.05)):
            m.cy(px, y + 0.014, pz, 0.12, 0.12, 0.04, 'navy', seg=8, rot=(90, 0, 0), flat=True)
    m.parent = Matrix.Identity(4)
    finish('GateFrame', m, bevel=0.0)
    # GateShutter: the pet flap (3 m x 3.05 m), clear plastic with a steel bottom bar and a hazard foot
    m = K()
    H = 3.05
    m.bx(-1.49, -0.06, 0.5, 1.49, 0.06, H - 0.01, 'glass')
    m.bx(-1.5, -0.08, H - 0.25, 1.5, 0.08, H, 'steel2')
    for k in range(8):
        m.bx(-1.5 + k * 0.375, -0.08, 0, -1.5 + (k + 1) * 0.375, 0.08, 0.5, 'black' if k % 2 else 'mustard')
    m.bx(-0.4, -0.065, 1.6, 0.4, 0.065, 2.0, 'teal')
    finish('GateShutter', m, hull=0.0, strip=True)
    shutter = bpy.data.objects[PRE + 'GateShutter']
    m = K()
    m.bx(-1.5, -0.08, 0, 1.5, 0.08, H, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    STATS[PRE + 'GateShutter'] = tris_of(shutter)


def hall_base(m, rnd):
    """Hallway wall slice: 1 m along Blender Y, 0.5 thick (x -0.25..0.25), trail face +X: wainscot, wallpaper with a
    stripe, picture rail, crown. One-sided (the hatch room turns its back wall round to show this face too)."""
    x = 0.25
    m.quad([(x, -0.5, 0.0), (x, 0.5, 0.0), (x, 0.5, WAINS + 0.1), (x, -0.5, WAINS + 0.1)], 'cab2')
    m.quad([(x, -0.5, WAINS + 0.1), (x, 0.5, WAINS + 0.1), (x, 0.5, TRAIL_H), (x, -0.5, TRAIL_H)], 'paint2')
    for yy in (-0.25, 0.25):
        m.bx(x, yy - 0.06, WAINS + 0.3, x + 0.004, yy + 0.06, 14.2, 'cream', flat=True)   # wallpaper stripes
    m.bx(x - 0.02, -0.5, 0.0, x + 0.16, 0.5, 1.0, 'trim', flat=True)
    m.bx(x - 0.02, -0.5, 1.0, x + 0.2, 0.5, 1.08, 'trim2', flat=True)
    m.bx(x - 0.02, -0.5, 1.3, x + 0.05, 0.5, 1.42, 'trim', flat=True)
    m.bx(x - 0.02, -0.5, 5.0, x + 0.05, 0.5, 5.12, 'trim', flat=True)
    m.bx(x - 0.02, -0.5, WAINS, x + 0.14, 0.5, WAINS + 0.3, 'oak2', flat=True)
    m.bx(x - 0.02, -0.5, 14.2, x + 0.07, 0.5, 14.32, 'oak2', flat=True)
    m.bx(x - 0.02, -0.5, 16.9, x + 0.18, 0.5, 17.2, 'trim2', flat=True)
    m.bx(x - 0.02, -0.5, 17.2, x + 0.3, 0.5, 17.6, 'trim', flat=True)


def build_trail(ao):
    variants = ('TrailWall', 'TrailWall_Photos', 'TrailWall_Coats', 'TrailWall_Radiator', 'TrailWall_Shoes')
    for i, name in enumerate(variants):
        rnd = random.Random(31 + i)
        m = K()
        hall_base(m, rnd)
        x = 0.25
        if name == 'TrailWall_Photos':      # photo frames hung from the picture rail
            for j, (yc, zc, w, h, c, f) in enumerate(((-0.2, 10.4, 0.5, 0.7, 'sun', 'black'), (0.22, 11.2, 0.4, 0.5, 'pink', 'oak2'),
                                                      (0.05, 8.8, 0.7, 0.55, 'tile2', 'walnut'))):
                m.bx(x + 0.004, yc - w / 2, zc - h / 2, x + 0.06, yc + w / 2, zc + h / 2, f)
                m.bx(x + 0.06, yc - w / 2 + 0.06, zc - h / 2 + 0.06, x + 0.064, yc + w / 2 - 0.06, zc + h / 2 - 0.06, c, flat=True)
        elif name == 'TrailWall_Coats':     # a hook rail with a hanging coat and a scarf
            m.bx(x + 0.004, -0.5, 9.4, x + 0.12, 0.5, 9.7, 'oak2', flat=True)
            for yy in (-0.3, 0.3):
                m.bx(x + 0.12, yy - 0.04, 9.4, x + 0.3, yy + 0.04, 9.5, 'mustard', flat=True)
            m.poly([(x + 0.1, -0.42), (x + 0.5, -0.46), (x + 0.5, -0.02), (x + 0.1, -0.1)], 6.6, 9.45, 'rugB')
            m.bx(x + 0.48, -0.42, 7.2, x + 0.52, -0.08, 9.3, 'navy', flat=True)
            m.bx(x + 0.125, 0.2, 7.0, x + 0.28, 0.4, 9.45, 'coral')
            for z in (7.4, 7.8, 8.2):
                m.bx(x + 0.28, 0.19, z, x + 0.285, 0.41, z + 0.12, 'cream', flat=True)
        elif name == 'TrailWall_Radiator':  # a white panel radiator under a little shelf with a plant
            m.bx(x + 0.004, -0.46, 1.6, x + 0.2, 0.46, 4.4, 'white')
            for j in range(6):
                yy = -0.39 + j * 0.156
                m.bx(x + 0.2, yy - 0.04, 1.75, x + 0.23, yy + 0.04, 4.25, 'trim2', flat=True)
            m.bx(x + 0.004, -0.5, 4.8, x + 0.35, 0.5, 4.95, 'oak')
            m.cy(x + 0.17, 0.1, 4.95, 0.12, 0.14, 0.3, 'pot', seg=8)
            m.sp(x + 0.17, 0.1, 5.45, 0.2, 'leaf', seg=(6, 4))
        elif name == 'TrailWall_Shoes':     # a low shoe rack with two pairs of shoes and an umbrella
            m.bx(x + 0.004, -0.48, 0.0, x + 0.45, -0.44, 2.2, 'walnut')
            m.bx(x + 0.004, 0.44, 0.0, x + 0.45, 0.48, 2.2, 'walnut')
            for z in (0.6, 1.6):
                m.bx(x + 0.004, -0.44, z - 0.06, x + 0.45, 0.44, z, 'oak', flat=True)
            for (yy, z, c) in ((-0.22, 0.6, 'red'), (0.18, 0.6, 'tblue'), (0.0, 1.6, 'mustard')):
                m.bx(x + 0.08, yy - 0.12, z, x + 0.42, yy + 0.1, z + 0.28, c)
            m.bx(x + 0.004, -0.5, 2.2, x + 0.48, 0.5, 2.34, 'walnut')
            m.cy(x + 0.3, 0.25, 2.34, 0.05, 0.05, 3.2, 'navy', seg=6, rot=(0, -8, 0))
        finish(name, m)


def build_hatch(ao):
    """Exit pad: a brass floor register with teal corner lights."""
    m = K()
    m.bx(-1.45, -1.0, 0.0, 1.45, 1.0, 0.1, 'mustard', bevel=True)
    m.bx(-1.2, -0.78, 0.0, 1.2, 0.78, 0.104, 'black', flat=True)
    for i in range(9):
        xx = -1.08 + i * 0.27
        m.bx(xx - 0.06, -0.75, 0.0, xx + 0.06, 0.75, 0.13, 'steel')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy(sx * 1.3, sy * 0.86, 0.1, 0.1, 0.1, 0.04, 'teal', seg=8, flat=True)
    finish('Hatch', m, bevel=0.02)


# ================================================================ build
def build_kit_livingroom(ao):
    global pal
    pal = Palette(FAM)
    STATS.clear()
    build_walls()
    build_overlays()
    build_lounge(ao)
    build_kitchen(ao)
    build_clutter(ao)
    build_ceiling()
    build_gate(ao)
    build_trail(ao)
    build_hatch(ao)
    total = 0
    for k in sorted(STATS):
        print('%-40s %6d tris' % (k, STATS[k]))
        total += STATS[k]
    print('kit-livingroom pieces: %d, total %d tris' % (len(STATS), total))
    export(FAM)


FAMILY = FAM
BUILD = build_kit_livingroom
