"""INKBOLT asset family: kit-office (Office Skyscraper: a corporate floor high in a New York tower, campaign level 4).

Conventions (see src/data/themes.js):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z). Wall modules are 4 m tall = the ceiling height.
  * Perimeter window modules also come pre-turned (_W: room to Blender +X, _E: room to -X) for edge cells the
    engine places unrotated (it counts the outside of the grid as wall, so east/west edge cells get yaw 0);
    the theme's wall chooser picks them from the flags it is given.
  * Shapes marked ink=False get no outline shell (trims, painted quads, desk clutter): they cost 12 triangles a box
    and 2 a quad, which keeps the repeated cubicle pods, ceiling tiles and window walls lean.
  * Collision boxes are <Piece>_COL<n> cube empties (position = box centre, scale = half extents).
"""
import math

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib

FAM = 'kit-office'
PFX = 'KIT_OFFICE_'
ib_lib.GLB[FAM] = 'fps-kit-office.glb'
ib_lib.CFG[FAM] = (0.012, 0.012)          # bevel width, outline shell (thin: lots of small office detail)
HULL_T = ib_lib.CFG[FAM][1]
H = 4.0                                   # wall height = ceiling height

ib_lib.PALETTES[FAM] = BASE + [
    ('mullion', '#2F353D'), ('graphite', '#3B3F47'), ('graphite2', '#5A616C'), ('steel', '#C6CCD3'),
    ('steel2', '#A4ADB8'), ('steelDark', '#7D8792'), ('drywall', '#ECE8E1'), ('drywall2', '#D9D4CB'),
    ('ceil', '#F7F7F4'), ('tbar', '#D3D8DE'), ('glow', '#EAF7FF'), ('fabricBlue', '#7FA3C4'),
    ('fabricTeal', '#6DB3AC'), ('fabricLight', '#C8D6E2'), ('fabricLight2', '#BFE0DC'), ('cap', '#E3E7EB'),
    ('oak', '#DDBE8F'), ('oak2', '#C9A574'), ('walnut', '#A77452'), ('walnut2', '#80563A'),
    ('screen', '#86CDF2'), ('screen2', '#A6E6D8'), ('black', '#25272D'), ('chair', '#3D414B'),
    ('chairMesh', '#5C6370'), ('leaf', '#5FB565'), ('leaf2', '#3F9158'), ('pot', '#F0EFEA'),
    ('soil', '#6E5443'), ('trunk', '#8A6A4E'), ('frost', '#DCEAF0'), ('glint', '#F2FBFF'),
    ('marble', '#EDEAE4'), ('vein', '#CDC7BE'), ('granite', '#5E646C'), ('coral', '#E8876A'),
    ('rug', '#9FB4C7'), ('copier', '#DADDE2'), ('green', '#5BCF4A'), ('cardboard', '#D4AA70'),
    ('ledge', '#CDD3DA'), ('shade', '#E4DED3'), ('column', '#F1F2F3'), ('brass', '#D8B56C'),
    ('bottle', '#8FCBF2'), ('lime', '#E8DECB'), ('lime2', '#D3C6AE'), ('brick', '#CB937A'),
    ('glassB', '#A9CDE2'), ('glassB2', '#87AFCB'), ('glassG', '#A4D0C6'), ('deco', '#D5DAE0'),
    ('winDark', '#64798E'), ('roof', '#A6ABB2'), ('tank', '#AD8059'), ('sofaBlue', '#5F8DB5'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


class Kit:
    """One piece at a time: outlined shapes + flat (no-outline) shapes, checked together for z-fighting."""

    def __init__(self, pal):
        self.pal = pal
        self.tris = {}

    def begin(self, rot=0):
        self.m = Model(self.pal)
        self.base = rz(rot)
        self.m.parent = self.base.copy()
        self.stack = []
        self.flat = set()
        self.cols = []
        return self

    # sub-frames for furniture inside a prefab (turns only: no mirroring, so windings stay right)
    def push(self, x, y, deg=0, z=0, sz=1.0):
        self.stack.append(self.m.parent)
        self.m.parent = self.m.parent @ Matrix.Translation((x, y, z)) @ rz(deg) @ Matrix.Diagonal((1.0, 1.0, sz, 1.0))

    def pop(self):
        self.m.parent = self.stack.pop()

    def _mark(self, ink):
        if not ink:
            self.flat.add(self.m.nshape)

    def bx(self, x0, x1, y0, y1, z0, z1, c, ink=True, bevel=False):
        assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
        self.m.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), c, bevel=bevel)
        self._mark(ink)

    def cyl(self, x, y, z, r1, r2, h, c, seg=8, ink=True, bevel=False, rot=(0, 0, 0), caps=True):
        self.m.cyl((x, y, z), r1, r2, h, c, seg=seg, rot=rot, bevel=bevel, caps=caps)
        self._mark(ink)

    def sph(self, x, y, z, r, c, seg=(6, 4), scale=(1, 1, 1), ink=True):
        self.m.sphere((x, y, z), r, c, seg=seg, scale=scale)
        self._mark(ink)

    def beam(self, a, b, t, c, ink=True):
        self.m.beam(a, b, t, c)
        self._mark(ink)

    def poly(self, pts, c, normal):
        P = self.m.parent
        vs = [self.m.bm.verts.new(P @ Vector(p)) for p in pts]
        f = self.m.bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(P.to_3x3() @ Vector(normal)) < 0:
            f.normal_flip()
        self.m._finish(vs, c, False)
        self.flat.add(self.m.nshape)

    def qy(self, x0, x1, z0, z1, y, s, c):
        self.poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], c, (0, s, 0))

    def qx(self, y0, y1, z0, z1, x, s, c):
        self.poly([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], c, (s, 0, 0))

    def qz(self, x0, x1, y0, y1, z, s, c):
        self.poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], c, (0, 0, s))

    def col(self, x0, x1, y0, y1, z0, z1):
        """Collision box in the piece frame (only the piece's base turn applies)."""
        self.cols.append((x0, x1, y0, y1, z0, z1))

    def finish(self, name, bevel=0.0, ao=False):
        full = PFX + name
        m = self.m
        check_zfight(full, m.bm, m.shape)
        flat = self.flat
        fb = m.bm.copy()
        bmesh.ops.delete(m.bm, geom=[f for f in m.bm.faces if f[m.shape] in flat], context='FACES')
        fm = Model(self.pal)
        fm.bm.free()
        fm.bm = fb
        fm.bw = fb.edges.layers.float['bevel_weight_edge']
        fm.shape = fb.faces.layers.int['shape_id']
        bmesh.ops.delete(fb, geom=[f for f in fb.faces if f[fm.shape] not in flat], context='FACES')
        obj = None
        if len(m.bm.faces):
            obj = build_object(full, m, bevel, HULL_T, ao=ao)
        else:
            m.bm.free()
        if len(fb.faces):
            o2 = build_object(full + '_flat', fm, 0, 0.0)
            strip_hull(o2)
            if obj is None:
                obj = o2
                obj.name = full
                obj.data.name = full
            else:
                join_into(obj, o2)
        else:
            fb.free()
        P = self.base.to_3x3()
        for i, (x0, x1, y0, y1, z0, z1) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_COL%d' % (full, i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj


def srt(a, b):
    return (a, b) if a <= b else (b, a)


# ================================================================ furniture helpers (local frames face -Y)
def task_chair(k, x, y, deg, c='chair'):
    """Office task chair; the sitter faces local -Y (backrest at +Y)."""
    k.push(x, y, deg)
    k.bx(-0.3, 0.3, -0.03, 0.03, 0.05, 0.09, 'graphite', ink=False)
    k.bx(-0.03, 0.03, -0.3, 0.3, 0.055, 0.095, 'graphite', ink=False)
    k.bx(-0.025, 0.025, -0.025, 0.025, 0.095, 0.42, 'steelDark', ink=False)
    k.bx(-0.24, 0.24, -0.23, 0.23, 0.42, 0.5, c)
    k.bx(-0.035, 0.035, 0.21, 0.25, 0.45, 0.62, 'graphite', ink=False)
    k.bx(-0.22, 0.22, 0.2, 0.27, 0.6, 1.05, c)
    k.qy(-0.17, 0.17, 0.66, 0.99, 0.197, -1, 'chairMesh')
    k.pop()


def side_chair(k, x, y, deg, c='chair', frame='graphite'):
    """Meeting / guest chair on two panel legs; faces local -Y."""
    k.push(x, y, deg)
    k.bx(-0.22, 0.22, -0.22, 0.22, 0.42, 0.49, c)
    k.bx(-0.21, 0.21, 0.17, 0.22, 0.49, 0.92, c)
    for s in (-1, 1):
        x0, x1 = srt(s * 0.195, s * 0.215)
        k.bx(x0, x1, -0.2, 0.22, 0, 0.42, frame, ink=False)
    k.pop()


def monitor(k, x, y, deg, z0, scr='screen'):
    """Flat screen on a stand; the screen faces local -Y (front face at y = 0)."""
    k.push(x, y, deg, z0)
    k.bx(-0.11, 0.11, -0.05, 0.08, 0, 0.012, 'black', ink=False)
    k.bx(-0.02, 0.02, 0.03, 0.06, 0.012, 0.2, 'graphite2', ink=False)
    k.bx(-0.27, 0.27, 0.0, 0.03, 0.14, 0.47, 'black')
    k.qy(-0.25, 0.25, 0.16, 0.45, -0.003, -1, scr)
    k.qy(-0.2, 0.05, 0.36, 0.4, -0.006, -1, 'white')      # window bars on the desktop
    k.qy(-0.2, 0.18, 0.22, 0.32, -0.006, -1, 'glow')
    k.pop()


def keyboard(k, x, y, deg, z0):
    k.push(x, y, deg, z0)
    k.bx(-0.21, 0.21, -0.07, 0.07, 0, 0.02, 'black', ink=False)
    k.qz(-0.19, 0.19, -0.055, 0.055, 0.023, 1, 'graphite2')
    k.bx(0.27, 0.33, -0.05, 0.04, 0, 0.022, 'black', ink=False)
    k.pop()


def mug(k, x, y, z, c):
    k.cyl(x, y, z, 0.04, 0.04, 0.1, c, seg=6, ink=False)


def small_plant(k, x, y, z):
    k.cyl(x, y, z, 0.07, 0.09, 0.14, 'pot', seg=6, ink=False)
    k.sph(x, y, z + 0.24, 0.13, 'leaf', seg=(6, 4))


def potted(k, x, y, kind='fig', s=1.0):
    """Floor plant in a planter; base at (x, y, 0)."""
    if kind == 'fig':
        k.cyl(x, y, 0, 0.22 * s, 0.27 * s, 0.55 * s, 'pot', seg=10)
        k.cyl(x, y, 0.55 * s, 0.23 * s, 0.23 * s, 0.004, 'soil', seg=10, ink=False)
        k.cyl(x, y, 0.554 * s, 0.03, 0.025, 0.8 * s, 'trunk', seg=5, ink=False)
        for (dx, dy, dz, r, c) in ((0, 0, 1.55, 0.36, 'leaf'), (0.2, -0.12, 1.25, 0.3, 'leaf2'),
                                   (-0.2, 0.1, 1.3, 0.32, 'leaf'), (0.05, 0.22, 1.05, 0.26, 'leaf2'),
                                   (-0.1, -0.2, 1.8, 0.24, 'leaf2')):
            k.sph(x + dx * s, y + dy * s, dz * s, r * s, c, seg=(7, 5))
    elif kind == 'snake':
        k.bx(x - 0.22 * s, x + 0.22 * s, y - 0.22 * s, y + 0.22 * s, 0, 0.45 * s, 'graphite2')
        k.qz(x - 0.19 * s, x + 0.19 * s, y - 0.19 * s, y + 0.19 * s, 0.45 * s + 0.004, 1, 'soil')
        blades = ((0, 0, 1.3), (0.1, 0.06, 1.15), (-0.11, 0.04, 1.2), (0.05, -0.1, 1.05), (-0.06, -0.09, 1.25),
                  (0.12, -0.04, 0.95), (-0.13, -0.02, 1.0), (0.0, 0.12, 1.1))
        for i, (dx, dy, top) in enumerate(blades):
            a = (x + dx * s, y + dy * s, 0.44 * s)
            b = (x + dx * 1.9 * s, y + dy * 1.9 * s, top * s)
            k.beam(a, b, 0.055 * s, 'leaf' if i % 2 else 'leaf2')
    else:   # palm
        k.cyl(x, y, 0, 0.24 * s, 0.2 * s, 0.5 * s, 'pot', seg=10)
        k.cyl(x, y, 0.5 * s, 0.17 * s, 0.17 * s, 0.004, 'soil', seg=10, ink=False)
        for i in range(7):
            a = i / 7 * math.pi * 2
            ca, sa = math.cos(a), math.sin(a)
            mid = (x + ca * 0.18 * s, y + sa * 0.18 * s, (1.15 + 0.12 * (i % 3)) * s)
            k.beam((x + ca * 0.03, y + sa * 0.03, 0.5 * s), mid, 0.03, 'trunk', ink=False)
            k.beam(mid, (x + ca * 0.62 * s, y + sa * 0.62 * s, (0.95 + 0.1 * (i % 2)) * s), 0.09 * s,
                   'leaf' if i % 2 else 'leaf2')


# ================================================================ wall modules
def window_module(k, kind, rot):
    """Floor-to-ceiling curtain wall bay: interior mullion + exterior fin (left edge), sill kick, guard rail,
    shade pocket, exterior slab ledge with a parapet rail. Open glazing (the skyline shows through)."""
    k.begin(rot)
    k.bx(-0.5, -0.44, -0.5, -0.36, 0, H, 'mullion')                 # interior mullion
    k.bx(-0.5, -0.44, -0.36, -0.2, 0.03, H, 'mullion')              # exterior cap (stands on the ledge)
    k.bx(-0.44, 0.5, -0.5, -0.36, 0, 0.12, 'graphite', ink=False)   # sill kick
    k.bx(-0.44, 0.5, -0.47, -0.41, 0.86, 0.92, 'mullion', ink=False)  # guard rail transom
    k.bx(-0.44, 0.5, -0.5, 0.42, 3.55, H, 'ceil')                   # shade pocket / header
    k.bx(-0.5, 0.5, -0.36, 0.9, -0.5, 0.03, 'ledge')                # exterior slab edge
    k.bx(-0.5, 0.5, 0.84, 0.9, 0.03, 0.15, 'mullion', ink=False)    # parapet rail
    if kind == 'B':     # comic glass glints
        k.poly([(-0.3, -0.37, 1.25), (-0.22, -0.37, 1.25), (0.2, -0.37, 2.55), (0.12, -0.37, 2.55)], 'glint', (0, -1, 0))
        k.poly([(-0.08, -0.37, 1.45), (-0.045, -0.37, 1.45), (0.3, -0.37, 2.5), (0.265, -0.37, 2.5)], 'glint', (0, -1, 0))
    if kind == 'C':     # roller shade half down
        k.bx(-0.42, 0.48, -0.46, -0.43, 2.3, 3.55, 'shade', ink=False)
        k.bx(-0.43, 0.49, -0.47, -0.42, 2.27, 2.33, 'graphite', ink=False)
        k.bx(0.3, 0.31, -0.452, -0.448, 1.2, 2.27, 'graphite2', ink=False)   # pull cord
    return k


def win_column(k, rot):
    k.begin(rot)
    k.bx(-0.495, 0.495, -0.5, 0.42, 0, H, 'column')                 # structural pier
    k.bx(-0.495, 0.495, 0.42, 0.45, 0.03, H, 'mullion', ink=False)  # dark facade cladding
    k.bx(-0.5, 0.5, -0.508, -0.497, 0, 0.12, 'graphite', ink=False)  # baseboard (sunk 3 mm: inner face clear of neighbours)
    k.bx(-0.5, 0.5, -0.36, 0.9, -0.5, 0.03, 'ledge')
    k.bx(-0.5, 0.5, 0.84, 0.9, 0.03, 0.15, 'mullion', ink=False)
    k.qy(-0.3, -0.18, 1.2, 1.32, -0.503, -1, 'white')               # thermostat
    k.qy(-0.28, -0.2, 1.24, 1.29, -0.506, -1, 'screen2')
    return k


def win_corner(k, rot):
    """Building corner (canonical: outside to Blender -X and +Y)."""
    k.begin(rot)
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'mullion')
    k.bx(-0.9, 0.5, 0.5, 0.9, -0.5, 0.03, 'ledge')
    k.bx(-0.9, -0.5, -0.5, 0.5, -0.5, 0.03, 'ledge')
    k.bx(-0.9, 0.5, 0.84, 0.9, 0.03, 0.15, 'mullion', ink=False)
    k.bx(-0.9, -0.84, -0.5, 0.84, 0.03, 0.15, 'mullion', ink=False)
    return k


def drywall(k, kind):
    """Interior 1 m partition (double sided, 1 cell thick); decoration on the -Y face."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'drywall')
    for s in (-1, 1):
        y0, y1 = srt(s * 0.497, s * 0.508)
        k.bx(-0.49, 0.49, y0, y1, 0, 0.1, 'graphite', ink=False)
    return dry_decor(k, kind)


def dry_decor(k, kind):
    """The -Y face decor of a drywall module (wall at y -0.5), in k's current frame."""
    if kind == 'Art':
        k.bx(-0.36, 0.36, -0.53, -0.5, 1.3, 2.2, 'black')
        k.qy(-0.32, 0.32, 1.34, 2.16, -0.533, -1, 'paper')
        k.qy(-0.26, 0.04, 1.62, 2.08, -0.536, -1, 'teal')
        k.qy(0.08, 0.26, 1.62, 2.08, -0.536, -1, 'coral')
        k.qy(-0.26, 0.26, 1.42, 1.56, -0.536, -1, 'amber')
        k.qy(-0.12, -0.02, 1.7, 2.0, -0.539, -1, 'paper')
    elif kind == 'Board':
        k.bx(-0.46, 0.46, -0.53, -0.5, 1.0, 2.1, 'steel', ink=False)
        k.qy(-0.44, 0.44, 1.02, 2.08, -0.533, -1, 'white')
        k.bx(-0.3, 0.3, -0.58, -0.53, 0.97, 1.0, 'steel2', ink=False)
        for i, (h, c) in enumerate(((0.35, 'teal'), (0.55, 'fabricBlue'), (0.28, 'coral'), (0.7, 'teal'))):
            x = -0.3 + i * 0.13
            k.qy(x, x + 0.08, 1.25, 1.25 + h, -0.536, -1, c)
        k.qy(-0.35, 0.3, 1.2, 1.215, -0.536, -1, 'ink')
        k.qy(0.22, 0.42, 1.8, 1.815, -0.536, -1, 'red')
        k.qy(0.22, 0.38, 1.72, 1.735, -0.536, -1, 'ink')
        k.bx(0.15, 0.2, -0.56, -0.53, 1.0, 1.02, 'teal', ink=False)
    elif kind == 'Door':
        for s in (-1, 1):
            y0, y1 = srt(s * 0.493, s * 0.522)        # sunk into the wall: inner faces clear of the baseboards
            k.bx(-0.48, -0.44, y0, y1, 0, 2.2, 'walnut2', ink=False)
            k.bx(0.44, 0.48, y0, y1, 0, 2.2, 'walnut2', ink=False)
            k.bx(-0.48, 0.48, y0, y1, 2.2, 2.25, 'walnut2', ink=False)
            ly0, ly1 = srt(s * 0.493, s * 0.512)
            k.bx(-0.44, 0.44, ly0, ly1, 0, 2.2, 'walnut', ink=False)
            hy0, hy1 = srt(s * 0.512, s * 0.55)
            k.bx(0.3, 0.38, hy0, hy1, 0.98, 1.02, 'steel', ink=False)
            k.qy(-0.06, 0.06, 1.55, 1.71, s * 0.515, s, 'white')     # room sign plate
            k.qy(-0.04, 0.04, 1.6, 1.66, s * 0.518, s, 'teal')
    elif kind == 'Screen':
        k.bx(-0.45, 0.45, -0.56, -0.5, 1.3, 1.85, 'black')
        k.qy(-0.42, 0.42, 1.33, 1.82, -0.563, -1, 'screen')
        for i, h in enumerate((0.12, 0.22, 0.17, 0.3, 0.26)):
            x = -0.32 + i * 0.13
            k.qy(x, x + 0.08, 1.4, 1.4 + h, -0.566, -1, 'white' if i % 2 else 'glow')
        k.qy(-0.36, 0.36, 1.74, 1.77, -0.566, -1, 'white')
    elif kind == 'Ext':
        k.bx(0.12, 0.42, -0.53, -0.5, 0.7, 1.5, 'red')
        k.qy(0.15, 0.39, 0.74, 1.46, -0.533, -1, 'glint')
        k.cyl(0.27, -0.52, 0.78, 0.07, 0.07, 0.48, 'red', seg=8, ink=False)
        k.qy(0.17, 0.37, 1.62, 1.76, -0.503, -1, 'green')
        k.qy(-0.3, -0.2, 1.2, 1.33, -0.503, -1, 'white')                 # light switch
    return k


def core(k):
    """Four-sided module for wall junctions, thick blocks and free-standing columns (plain: cores touch other
    cores on any side, so nothing may stand proud of the cell)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'drywall')
    return k


def lobby(k, kind):
    """One-sided lobby walls by the gates on the north / south edges (room side -Y)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'drywall')
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.12, 'graphite', ink=False)
    if kind.startswith('Wood'):
        k.bx(-0.5, 0.5, -0.53, -0.5, 0.12, 3.3, 'walnut', ink=False)
        k.qy(-0.5, -0.485, 0.12, 3.3, -0.533, -1, 'walnut2')
        k.qy(-0.008, 0.008, 0.12, 3.3, -0.533, -1, 'walnut2')
        k.bx(-0.5, 0.5, -0.54, -0.5, 3.3, 3.36, 'brass', ink=False)
        if kind == 'WoodSconce':
            k.bx(-0.09, 0.09, -0.56, -0.53, 2.1, 2.5, 'brass')
            k.bx(-0.13, 0.13, -0.72, -0.56, 2.2, 2.42, 'glow')
            k.qz(-0.1, 0.1, -0.7, -0.58, 2.197, -1, 'white')
    else:   # stone cladding, coursed
        k.bx(-0.5, 0.5, -0.53, -0.5, 0.12, H, 'marble', ink=False)
        zs = [0.12, 0.92, 1.72, 2.52, 3.32, H]
        for i in range(1, 5):
            k.qy(-0.5, 0.5, zs[i] - 0.01, zs[i] + 0.01, -0.533, -1, 'vein')
        for i in range(5):
            x = -0.5 if i % 2 == 0 else -0.005
            k.qy(x, x + 0.01, zs[i] + 0.01, zs[i + 1] - 0.01, -0.536, -1, 'vein')
    return k


# ================================================================ ceiling, gate, trail, hatch, stand
def ceil_light(k):
    """4 x 4 m ceiling patch hung at the ceiling plane: T-bar tile grid, a troffer light and a supply vent."""
    k.begin()
    for o in (-2.0, -2 / 3, 2 / 3):
        k.qz(-2, 2, o - 0.02, o + 0.02, -0.012, -1, 'tbar')
        k.qz(o - 0.02, o + 0.02, -2, 2, -0.016, -1, 'tbar')
    k.bx(-0.6, 0.6, -0.3, 0.3, -0.04, -0.005, 'ceil')
    k.qz(-0.55, 0.55, -0.25, 0.25, -0.043, -1, 'glow')
    k.qz(-0.55, 0.55, -0.015, 0.015, -0.046, -1, 'tbar')
    v = 4 / 3
    k.bx(v - 0.3, v + 0.3, v - 0.3, v + 0.3, -0.03, -0.005, 'cap', ink=False)
    k.qz(v - 0.2, v + 0.2, v - 0.2, v + 0.2, -0.033, -1, 'tbar')
    k.qz(v - 0.1, v + 0.1, v - 0.1, v + 0.1, -0.036, -1, 'cap')
    return k


def gate_frame(k):
    """Security portal for the 3 m zone gates: graphite posts with Pop Teal light strips, shutter housing."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.495, s * 2.1)
        k.bx(x0, x1, -0.56, 0.56, 0, 3.05, 'graphite')
        lx0, lx1 = srt(s * 1.62, s * 1.72)
        for f in (-1, 1):
            y0, y1 = srt(f * 0.56, f * 0.6)
            k.bx(lx0, lx1, y0, y1, 0.35, 2.75, 'teal', ink=False)
            k.bx(x0 + 0.02, x1 - 0.02, y0, y1, 0, 0.12, 'mullion', ink=False)
        cx = s * 1.9
        k.bx(cx - 0.06, cx + 0.06, -0.63, -0.56, 1.15, 1.35, 'black', ink=False)   # card reader
        k.qy(cx - 0.035, cx + 0.035, 1.28, 1.31, -0.633, -1, 'teal')
    k.bx(-2.1, 2.1, -0.56, 0.56, 3.05, 3.99, 'graphite2')
    for f in (-1, 1):
        y0, y1 = srt(f * 0.56, f * 0.6)
        k.bx(-1.3, 1.3, y0, y1, 3.42, 3.5, 'teal', ink=False)
        k.qy(-2.08, 2.08, 3.12, 3.16, f * 0.563, f, 'steel')
    return k


def gate_shutter(k):
    k.begin()
    Hs, n = 3.05, 10
    h = (Hs - 0.45) / n
    for i in range(n):
        z0 = 0.45 + i * h
        k.bx(-1.5, 1.5, -0.06, 0.06, z0, z0 + h, 'steel' if i % 2 else 'steel2', ink=False)
        for f in (-1, 1):
            k.qy(-1.5, 1.5, z0 + h - 0.015, z0 + h - 0.005, f * 0.063, f, 'steelDark')
    for j in range(8):
        x0 = -1.5 + j * 3 / 8
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.45, 'ink' if j % 2 else 'teal', ink=False)
    for s in (-1, 1):
        k.bx(s * 0.5 - 0.15, s * 0.5 + 0.15, -0.1, -0.07, 0.15, 0.22, 'graphite', ink=False)
    return k


def trail_wall(k):
    """Corridor drywall (1 m along Blender Y, 0.5 m thick), both faces alike, teal wayfinding stripe."""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, H, 'drywall')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.25, s * 0.258)
        k.bx(x0, x1, -0.5, 0.5, 0, 0.1, 'graphite', ink=False)
        k.bx(x0, x1, -0.5, 0.5, 1.15, 1.25, 'teal', ink=False)
        k.bx(x0, x1, -0.5, 0.5, 1.3, 1.33, 'fabricBlue', ink=False)
        k.qx(-0.5, -0.49, 0.1, H, s * 0.253, s, 'drywall2')        # board joint
    return k


def trail_variant(k, kind):
    """Corridor drywall with something on its trail face (+X): a framed print, a whiteboard, a status screen or a
    fire cabinet (the drywall partition decor, turned onto the 0.5 m trail slab)."""
    trail_wall(k)
    k.push(-0.2585, 0, 90, z=0.05)   # drywall frame: its -Y face (y -0.5) lands just proud of the stripe (x +0.2585)
    dry_decor(k, kind)
    k.pop()
    return k


def hatch(k):
    """Exit: an express-elevator landing pad and the elevator doors on the room's back wall (2.7 m north)."""
    k.begin()
    k.bx(-1.25, 1.25, -1.25, 1.25, 0, 0.05, 'steel2')
    k.bx(-1.05, 1.05, -1.05, 1.05, 0.05, 0.07, 'granite', ink=False)
    for i in range(3):            # chevrons pointing at the doors
        y = -0.6 + i * 0.45
        k.poly([(-0.6, y, 0.073), (0, y + 0.35, 0.073), (0, y + 0.5, 0.073), (-0.6, y + 0.15, 0.073)], 'teal', (0, 0, 1))
        k.poly([(0, y + 0.35, 0.074), (0.6, y, 0.074), (0.6, y + 0.15, 0.074), (0, y + 0.5, 0.074)], 'teal', (0, 0, 1))
    for s in (-1, 1):
        k.bx(s * 1.12 - 0.04, s * 1.12 + 0.04, -1.12, 1.12, 0.05, 0.075, 'teal', ink=False)
    Y1 = 2.69
    for s in (-1, 1):
        x0, x1 = srt(s * 0.85, s * 1.05)
        k.bx(x0, x1, 2.52, Y1, 0, 2.6, 'steel')
    k.bx(-1.05, 1.05, 2.52, Y1, 2.6, 2.82, 'steel')
    k.bx(-0.85, 0.0, 2.6, Y1, 0, 2.6, 'steel2', ink=False)
    k.bx(0.0, 0.85, 2.6, Y1, 0, 2.6, 'steel2', ink=False)
    k.qy(-0.008, 0.008, 0.02, 2.58, 2.597, -1, 'steelDark')
    k.bx(-0.32, 0.32, 2.58, Y1, 2.95, 3.2, 'black')
    k.poly([(-0.1, 2.577, 3.0), (0.1, 2.577, 3.0), (0, 2.577, 3.15)], 'teal', (0, -1, 0))
    k.bx(1.2, 1.36, 2.64, Y1, 1.0, 1.4, 'steel', ink=False)
    k.qy(1.25, 1.31, 1.25, 1.31, 2.637, -1, 'teal')
    k.qy(1.25, 1.31, 1.1, 1.16, 2.637, -1, 'white')
    return k


def stand(k):
    """Weapon stand: a two-drawer lateral file with an oak top."""
    k.begin()
    k.bx(-0.45, 0.45, -0.42, 0.42, 0, 0.92, 'cap')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0.92, 0.96, 'oak')
    for i, (z0, z1) in enumerate(((0.06, 0.48), (0.5, 0.9))):
        k.qy(-0.42, 0.42, z0, z1, -0.423, -1, 'column')
        k.bx(-0.14, 0.14, -0.45, -0.423, z1 - 0.1, z1 - 0.06, 'graphite', ink=False)
        k.qy(-0.06, 0.06, z1 - 0.2, z1 - 0.14, -0.426, -1, 'teal' if i == 0 else 'white')
    return k


# ================================================================ cell props
def lateral_file(k, kind):
    k.begin()
    k.bx(-0.47, 0.47, -0.28, 0.28, 0, 1.0, 'cap')
    k.bx(-0.48, 0.48, -0.29, 0.29, 1.0, 1.03, 'graphite2' if kind == 'B' else 'oak')
    k.qy(-0.45, 0.45, 0, 0.05, -0.283, -1, 'graphite')
    for i in range(3):
        z0 = 0.07 + i * 0.31
        k.qy(-0.45, 0.45, z0, z0 + 0.29, -0.283, -1, 'column')
        k.bx(-0.12, 0.12, -0.3, -0.283, z0 + 0.21, z0 + 0.24, 'graphite', ink=False)
        k.qy(-0.32, -0.22, z0 + 0.19, z0 + 0.25, -0.286, -1, 'white')
    if kind == 'B':     # binders and an in-tray
        x = -0.42
        for i, (w, h, c) in enumerate(((0.06, 0.3, 'fabricBlue'), (0.05, 0.28, 'teal'), (0.07, 0.31, 'coral'),
                                       (0.05, 0.27, 'oak2'), (0.06, 0.3, 'graphite2'), (0.05, 0.29, 'fabricBlue'))):
            k.bx(x, x + w, -0.14, 0.14, 1.03, 1.03 + h, c, ink=i % 2 == 0)
            x += w + 0.004
        k.bx(0.05, 0.4, -0.18, 0.16, 1.03, 1.08, 'black', ink=False)
        k.bx(0.08, 0.37, -0.15, 0.13, 1.08, 1.1, 'paper', ink=False)
    elif kind == 'C':   # planter trough with grass
        k.bx(-0.42, 0.42, -0.14, 0.14, 1.03, 1.2, 'pot')
        k.qz(-0.39, 0.39, -0.11, 0.11, 1.203, 1, 'soil')
        for i in range(9):
            x = -0.34 + i * 0.085
            lean = 0.12 if i % 2 else -0.1
            k.beam((x, 0, 1.18), (x + lean * 0.6, lean * 0.5, 1.55 + 0.08 * (i % 3)), 0.035, 'leaf' if i % 3 else 'leaf2')
    k.col(-0.48, 0.48, -0.29, 0.29, 0, 1.03)
    return k


def copier(k, kind):
    k.begin()
    if kind == 'Copier':
        k.bx(-0.33, 0.33, -0.29, 0.29, 0, 0.08, 'graphite', ink=False)
        k.bx(-0.36, 0.36, -0.32, 0.32, 0.08, 0.62, 'copier')
        for i in range(3):
            z0 = 0.11 + i * 0.17
            k.qy(-0.33, 0.33, z0, z0 + 0.15, -0.323, -1, 'cap')
            k.qy(-0.1, 0.1, z0 + 0.1, z0 + 0.125, -0.326, -1, 'graphite')
        k.bx(-0.36, 0.36, -0.32, 0.32, 0.62, 1.0, 'copier')
        k.qy(-0.33, 0.1, 0.7, 0.84, -0.323, -1, 'graphite2')                 # output bay
        k.bx(-0.3, 0.05, -0.31, 0.15, 0.735, 0.75, 'paper', ink=False)
        k.bx(-0.36, 0.36, -0.3, 0.32, 1.0, 1.1, 'graphite2')
        k.bx(0.1, 0.34, -0.42, -0.3, 1.0, 1.06, 'graphite', ink=False)
        k.qz(0.13, 0.31, -0.4, -0.32, 1.063, 1, 'screen')
        k.bx(-0.48, -0.36, -0.2, 0.2, 0.7, 0.72, 'cap', ink=False)
        k.qz(-0.46, -0.37, -0.17, 0.17, 0.723, 1, 'paper')
        k.col(-0.48, 0.36, -0.42, 0.32, 0, 1.1)
    elif kind == 'Printer':
        k.bx(-0.4, 0.4, -0.3, 0.3, 0, 0.7, 'column')
        k.qy(-0.37, -0.01, 0.05, 0.66, -0.303, -1, 'cap')
        k.qy(0.01, 0.37, 0.05, 0.66, -0.303, -1, 'cap')
        k.bx(-0.26, 0.24, -0.22, 0.22, 0.7, 0.95, 'graphite2')
        k.bx(-0.2, 0.18, -0.3, -0.22, 0.78, 0.8, 'graphite', ink=False)
        k.bx(-0.18, 0.16, -0.29, -0.2, 0.8, 0.81, 'paper', ink=False)
        k.qz(0.08, 0.2, -0.18, -0.08, 0.953, 1, 'screen2')
        for j in range(3):
            k.bx(0.27, 0.38, -0.12, 0.16, 0.7 + j * 0.055, 0.75 + j * 0.055, 'paper' if j % 2 == 0 else 'white', ink=False)
        k.col(-0.4, 0.4, -0.3, 0.3, 0, 0.95)
    else:   # archive boxes
        boxes = ((-0.45, -0.03, -0.2, 0.2, 0, 0.3), (0.03, 0.45, -0.22, 0.18, 0, 0.3),
                 (-0.32, 0.1, -0.17, 0.23, 0.3, 0.6), (0.14, 0.44, -0.24, 0.12, 0.3, 0.56), (-0.2, 0.2, -0.2, 0.2, 0.6, 0.88))
        for i, (x0, x1, y0, y1, z0, z1) in enumerate(boxes):
            k.bx(x0, x1, y0, y1, z0, z1, 'cardboard')
            k.qy(x0 + 0.02, x1 - 0.02, z1 - 0.06, z1 - 0.003, y0 - 0.003, -1, 'oak2')       # lid band
            k.qy((x0 + x1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, z0 + 0.1, z0 + 0.15, y0 - 0.006, -1, 'white')   # label
        k.col(-0.45, 0.45, -0.24, 0.23, 0, 0.88)
    return k


def tall_cabinet(k, kind):
    k.begin()
    if kind == 'A':     # two-door storage cabinet
        k.bx(-0.48, 0.48, -0.27, 0.27, 0, 1.85, 'cap')
        k.qy(-0.46, -0.008, 0.06, 1.82, -0.273, -1, 'column')
        k.qy(0.008, 0.46, 0.06, 1.82, -0.273, -1, 'column')
        for s in (-1, 1):
            x0, x1 = srt(s * 0.04, s * 0.06)
            k.bx(x0, x1, -0.3, -0.273, 0.85, 1.15, 'graphite', ink=False)
        k.bx(-0.36, 0.1, -0.2, 0.2, 1.85, 2.1, 'cardboard')
        k.bx(0.16, 0.42, -0.18, 0.16, 1.85, 2.0, 'cardboard')
    else:               # open shelving with binders
        for s in (-1, 1):
            x0, x1 = srt(s * 0.46, s * 0.48)
            k.bx(x0, x1, -0.27, 0.27, 0, 1.85, 'oak2')
        k.bx(-0.46, 0.46, 0.25, 0.27, 0, 1.85, 'oak', ink=False)
        for i in range(4):
            z = i * 0.45
            k.bx(-0.46, 0.46, -0.27, 0.25, z, z + 0.03, 'oak2', ink=i == 0)
            if i < 4:
                x = -0.44
                cols = ('fabricBlue', 'coral', 'teal', 'graphite2', 'oak', 'fabricLight', 'amber')
                for j in range(6 - (i % 2)):
                    w = 0.08 + 0.03 * ((i + j) % 3)
                    hgt = 0.3 + 0.04 * ((i * 3 + j) % 3)
                    k.bx(x, x + w, -0.18, 0.2, z + 0.03, z + 0.03 + hgt, cols[(i * 2 + j) % len(cols)], ink=False)
                    x += w + 0.006
                    if x > 0.36:
                        break
        k.bx(-0.46, 0.46, -0.27, 0.25, 1.82, 1.85, 'oak2', ink=False)
    k.col(-0.48, 0.48, -0.27, 0.27, 0, 1.85)
    return k


def plant(k, kind):
    k.begin()
    potted(k, 0, 0, kind)
    k.col(-0.28, 0.28, -0.28, 0.28, 0, 0.6)
    return k


def rack(k, kind):
    k.begin()
    k.bx(-0.48, 0.48, -0.45, 0.45, 0, 2.1, 'black')
    for f in (-1, 1):
        y = f * 0.453
        k.qy(-0.44, 0.44, 0.08, 2.02, y, f, 'graphite')
        for i in range(9):
            z = 0.14 + i * 0.205
            k.qy(-0.4, 0.4, z, z + 0.15, f * 0.456, f, 'graphite2')
            pattern = (i * 7 + (3 if kind == 'B' else 0)) % 5
            for j in range(3):
                c = ('teal', 'green', 'amber', 'teal', 'screen2')[(pattern + j) % 5]
                x = -0.34 + j * 0.06 + (0.4 if (i + j) % 3 == 0 and kind == 'B' else 0)
                k.qy(x, x + 0.03, z + 0.06, z + 0.09, f * 0.459, f, c)
    k.bx(-0.48, 0.48, -0.1, 0.1, 2.1, 2.16, 'steelDark', ink=False)
    k.col(-0.48, 0.48, -0.45, 0.45, 0, 2.1)
    return k


def counter(k, kind):
    k.begin()
    k.bx(-0.49, 0.49, -0.27, 0.31, 0.1, 0.9, 'column')
    k.bx(-0.49, 0.49, -0.23, 0.31, 0, 0.1, 'graphite', ink=False)
    k.bx(-0.5, 0.5, -0.32, 0.33, 0.9, 0.94, 'marble')
    for x0, x1 in ((-0.46, -0.01), (0.01, 0.46)):
        k.qy(x0, x1, 0.14, 0.86, -0.273, -1, 'cap')
    k.bx(-0.07, -0.04, -0.3, -0.273, 0.6, 0.8, 'steel', ink=False)
    k.bx(0.04, 0.07, -0.3, -0.273, 0.6, 0.8, 'steel', ink=False)
    T = 0.94
    if kind == 'Sink':
        k.qz(-0.25, 0.25, -0.2, 0.16, T + 0.003, 1, 'steel2')
        k.qz(-0.03, 0.03, -0.05, 0.01, T + 0.006, 1, 'steelDark')
        k.cyl(0, 0.24, T, 0.022, 0.022, 0.32, 'steel', seg=6, ink=False)
        k.beam((0, 0.24, T + 0.29), (0, 0.06, T + 0.29), 0.028, 'steel', ink=False)
        k.bx(0.06, 0.16, 0.22, 0.26, T + 0.1, T + 0.13, 'steel', ink=False)
    elif kind == 'Coffee':
        k.bx(-0.26, 0.14, -0.18, 0.26, T, T + 0.46, 'graphite')
        k.qy(-0.23, 0.11, T + 0.22, T + 0.42, -0.183, -1, 'steel')
        k.qy(-0.12, 0.0, T + 0.3, T + 0.36, -0.186, -1, 'screen2')
        k.bx(-0.12, -0.02, -0.26, -0.18, T + 0.16, T + 0.21, 'steelDark', ink=False)
        k.bx(-0.16, 0.02, -0.28, -0.18, T + 0.0, T + 0.02, 'steelDark', ink=False)
        k.cyl(-0.07, -0.23, T + 0.02, 0.035, 0.04, 0.08, 'white', seg=6, ink=False)
        k.cyl(-0.06, 0.04, T + 0.46, 0.08, 0.11, 0.14, 'black', seg=8)
        mug(k, 0.3, -0.12, T, 'teal')
        mug(k, 0.36, 0.02, T, 'coral')
    elif kind == 'Micro':
        k.bx(-0.3, 0.3, -0.2, 0.26, T, T + 0.3, 'steel')
        k.qy(-0.27, 0.12, T + 0.04, T + 0.26, -0.203, -1, 'black')
        k.qy(0.16, 0.27, T + 0.08, T + 0.24, -0.203, -1, 'graphite2')
        k.bx(0.09, 0.11, -0.24, -0.2, T + 0.06, T + 0.24, 'graphite', ink=False)
    else:   # fruit bowl + towel roll
        k.cyl(-0.1, -0.02, T, 0.08, 0.15, 0.07, 'white', seg=8, ink=False)
        for (x, y, c) in ((-0.15, -0.04, 'amber'), (-0.05, 0.02, 'red'), (-0.1, -0.08, 'green')):
            k.sph(x, y, T + 0.1, 0.045, c, seg=(6, 4), ink=False)
        k.cyl(0.28, 0.08, T, 0.06, 0.06, 0.26, 'white', seg=8)
    k.col(-0.5, 0.5, -0.32, 0.33, 0, 0.94)
    return k


def fridge(k, kind):
    k.begin()
    if kind == 'Fridge':
        k.bx(-0.42, 0.42, -0.35, 0.35, 0, 1.85, 'steel')
        k.qy(-0.4, 0.4, 1.235, 1.245, -0.353, -1, 'steelDark')
        k.qy(-0.4, 0.4, 0.02, 0.07, -0.353, -1, 'graphite')
        for (z0, z1) in ((0.4, 1.1), (1.32, 1.7)):
            k.bx(0.3, 0.34, -0.39, -0.35, z0, z1, 'steelDark', ink=False)
        k.qy(-0.3, -0.1, 1.45, 1.6, -0.353, -1, 'paper')       # a note on the door
        k.qy(-0.27, -0.13, 1.5, 1.52, -0.356, -1, 'teal')
        k.col(-0.42, 0.42, -0.39, 0.35, 0, 1.85)
    else:   # snack machine
        k.bx(-0.45, 0.45, -0.4, 0.4, 0, 1.85, 'coral')
        k.qy(-0.39, 0.13, 0.62, 1.76, -0.403, -1, 'black')
        cols = ('amber', 'teal', 'red', 'fabricBlue', 'green', 'paper')
        for r in range(4):
            for c in range(4):
                x = -0.35 + c * 0.12
                z = 0.7 + r * 0.27
                k.qy(x, x + 0.08, z, z + 0.14, -0.406, -1, cols[(r + c * 2) % len(cols)])
            k.qy(-0.38, 0.12, 0.66 + r * 0.27, 0.675 + r * 0.27, -0.406, -1, 'steel')
        k.qy(0.18, 0.4, 1.0, 1.5, -0.403, -1, 'graphite')
        k.qy(0.22, 0.36, 1.3, 1.42, -0.406, -1, 'screen2')
        k.qy(-0.39, 0.13, 0.18, 0.42, -0.403, -1, 'graphite')
        k.qy(-0.4, 0.4, 0.02, 0.1, -0.403, -1, 'ink')
        k.col(-0.45, 0.45, -0.4, 0.4, 0, 1.85)
    return k


def cooler(k, kind):
    k.begin()
    if kind == 'Cooler':
        k.bx(-0.17, 0.17, -0.17, 0.17, 0, 0.95, 'pot')
        k.bx(-0.18, 0.18, -0.18, 0.18, 0.95, 1.0, 'cap', ink=False)
        k.cyl(0, 0, 1.0, 0.05, 0.05, 0.04, 'bottle', seg=8, ink=False)
        k.cyl(0, 0, 1.04, 0.14, 0.14, 0.4, 'bottle', seg=10)
        k.qy(-0.12, 0.12, 0.62, 0.8, -0.173, -1, 'graphite2')
        k.bx(-0.08, -0.03, -0.22, -0.17, 0.7, 0.76, 'fabricBlue', ink=False)
        k.bx(0.03, 0.08, -0.22, -0.17, 0.7, 0.76, 'red', ink=False)
        k.cyl(0.21, 0.0, 0.55, 0.035, 0.035, 0.3, 'white', seg=6, ink=False)
        k.col(-0.2, 0.2, -0.2, 0.2, 0, 1.45)
    else:   # recycling bins
        for x0, x1, c, sym in ((-0.42, -0.02, 'fabricBlue', 'white'), (0.02, 0.42, 'graphite2', 'green')):
            k.bx(x0, x1, -0.2, 0.2, 0, 0.72, c)
            k.bx(x0 - 0.01, x1 + 0.01, -0.21, 0.21, 0.72, 0.77, 'graphite' if c != 'graphite2' else 'black', ink=False)
            k.qz(x0 + 0.08, x1 - 0.08, -0.04, 0.04, 0.773, 1, 'ink')
            k.qy((x0 + x1) / 2 - 0.07, (x0 + x1) / 2 + 0.07, 0.42, 0.56, -0.203, -1, sym)
        k.col(-0.43, 0.43, -0.21, 0.21, 0, 0.77)
    return k


# ================================================================ prefabs
def cubicle_pod(k, variant):
    """4 x 4 m pod of four cubicles: spine + cross partitions (1.47 m), end returns on the X sides, open to +/-Y.
    Each cubicle: L desk, drawer pedestal, monitor(s), keyboard, task chair, clutter."""
    k.begin()
    fab = 'fabricBlue' if variant == 'A' else 'fabricTeal'
    band = 'fabricLight' if variant == 'A' else 'fabricLight2'
    PH = 1.43

    def panel_x(x0, x1, y0, y1, cx0, cx1, cy0, cy1, bands):
        k.bx(x0, x1, y0, y1, 0, PH, fab)
        k.bx(cx0, cx1, cy0, cy1, PH, 1.47, 'cap', ink=False)
        for (axis, pos, s, a0, a1) in bands:
            if axis == 'y':
                k.qy(a0, a1, 1.0, 1.4, pos, s, band)
            else:
                k.qx(a0, a1, 1.0, 1.4, pos, s, band)

    # spine along X
    panel_x(-1.99, 1.99, -0.035, 0.035, -1.993, 1.993, -0.041, 0.041,
            [('y', -0.038, -1, -1.97, 1.97), ('y', 0.038, 1, -1.97, 1.97)])
    for sy in (-1, 1):
        y0, y1 = srt(sy * 0.035, sy * 1.99)
        cy0, cy1 = srt(sy * 0.041, sy * 1.993)
        b0, b1 = srt(sy * 0.06, sy * 1.97)
        panel_x(-0.035, 0.035, y0, y1, -0.041, 0.041, cy0, cy1, [('x', -0.038, -1, b0, b1), ('x', 0.038, 1, b0, b1)])
        for sx in (-1, 1):
            x0, x1 = srt(sx * 1.93, sx * 1.99)
            cx0, cx1 = srt(sx * 1.926, sx * 1.994)
            panel_x(x0, x1, y0, y1, cx0, cx1, cy0, cy1, [('x', sx * 1.927, -sx, b0, b1), ('x', sx * 1.993, sx, b0, b1)])
    k.col(-1.993, 1.993, -0.041, 0.041, 0, 1.47)
    for sy in (-1, 1):
        y0, y1 = srt(sy * 0.041, sy * 1.993)
        k.col(-0.041, 0.041, y0, y1, 0, 1.47)
        for sx in (-1, 1):
            x0, x1 = srt(sx * 1.926, sx * 1.994)
            k.col(x0, x1, y0, y1, 0, 1.47)

    mugs = ('teal', 'coral', 'amber', 'white')
    for qi, (sx, sy) in enumerate(((1, -1), (-1, -1), (-1, 1), (1, 1))):
        def B(u0, u1, v0, v1, z0, z1, c, ink=True):
            x0, x1 = srt(sx * u0, sx * u1)
            y0, y1 = srt(sy * v0, sy * v1)
            k.bx(x0, x1, y0, y1, z0, z1, c, ink=ink)

        def QV(u0, u1, z0, z1, v, c):        # quad facing +v (away from the spine)
            x0, x1 = srt(sx * u0, sx * u1)
            k.qy(x0, x1, z0, z1, sy * v, sy, c)

        def QU(v0, v1, z0, z1, u, c):        # quad facing +u (away from the cross panel)
            y0, y1 = srt(sy * v0, sy * v1)
            k.qx(y0, y1, z0, z1, sx * u, sx, c)

        def face(fu, fv):                    # turn so local -Y points along (fu, fv) in quadrant space
            return math.degrees(math.atan2(sx * fu, -sy * fv))

        B(0.035, 1.93, 0.035, 0.735, 0.72, 0.75, 'oak')                      # desk along the spine
        B(0.035, 0.735, 0.735, 1.6, 0.72, 0.75, 'oak')                       # return desk along the cross panel
        B(1.45, 1.9, 0.08, 0.68, 0, 0.7, 'cap')                             # drawer pedestal
        for (z0, z1) in ((0.05, 0.27), (0.29, 0.48), (0.5, 0.68)):
            QV(1.47, 1.88, z0, z1, 0.683, 'column')
            QV(1.62, 1.73, z1 - 0.06, z1 - 0.035, 0.686, 'graphite')
        B(0.08, 0.7, 1.555, 1.585, 0, 0.72, 'cap', ink=False)               # leg panel
        x0, x1 = srt(sx * 0.035, sx * 1.93)
        k.col(x0, x1, *srt(sy * 0.041, sy * 0.735), 0, 0.75)
        k.col(*srt(sx * 0.041, sx * 0.735), *srt(sy * 0.735, sy * 1.6), 0, 0.75)
        # screen, keyboard, chair
        monitor(k, sx * 1.0, sy * 0.25, face(0, 1), 0.75, 'screen' if (qi + (variant == 'B')) % 2 == 0 else 'screen2')
        keyboard(k, sx * 1.0, sy * 0.47, face(0, 1), 0.75)
        if variant == 'B' and qi % 2 == 0:
            monitor(k, sx * 0.28, sy * 1.05, face(1, 0), 0.75, 'screen2')
        else:
            B(0.15, 0.48, 0.95, 1.22, 0.75, 0.765, 'paper', ink=False)
            B(0.2, 0.5, 1.25, 1.45, 0.75, 0.758, 'white', ink=False)
        task_chair(k, sx * (1.05 + 0.08 * (qi % 2)), sy * 1.25, face(0, -1) + (14 if qi % 2 else -18))
        mug(k, sx * 0.45, sy * 0.5, 0.75, mugs[qi])
        B(0.25, 0.43, 0.3, 0.44, 0.75, 0.79, 'black', ink=False)              # desk phone
        # pinned notes on the spine's upper fabric band
        for j, (u, c) in enumerate(((0.5, 'paper'), (0.78, 'amber'), (1.3, 'paper'))):
            x0, x1 = srt(sx * u, sx * (u + 0.18))
            k.qy(x0, x1, 1.08 + 0.06 * j, 1.3 + 0.03 * j, sy * 0.041, sy, c)
        if variant == 'B' and qi == 1:
            small_plant(k, sx * 1.7, sy * 0.5, 0.75)
        if variant == 'A' and qi == 2:
            B(1.55, 1.85, 0.12, 0.4, 0.75, 0.77, 'graphite2', ink=False)       # laptop base
            k.push(sx * 1.7, sy * 0.12, face(0, 1), 0.77)
            k.bx(-0.15, 0.15, -0.012, 0.0, 0, 0.22, 'graphite2', ink=False)
            k.qy(-0.13, 0.13, 0.02, 0.2, -0.015, -1, 'screen')
            k.pop()
    return k


def bench(k):
    """4 x 3 m open-plan bench: shared oak table for four, low fabric divider."""
    k.begin()
    k.bx(-1.95, 1.95, -0.7, 0.7, 0.72, 0.75, 'oak')
    for x in (-1.88, 0.0, 1.88):
        k.bx(x - 0.02, x + 0.02, -0.64, 0.64, 0, 0.72, 'column', ink=False)
        k.bx(x - 0.03, x + 0.03, -0.66, 0.66, 0, 0.03, 'graphite', ink=False)
    k.bx(-1.9, 1.9, -0.025, 0.025, 0.75, 1.12, 'fabricTeal')
    k.bx(-1.903, 1.903, -0.029, 0.029, 1.12, 1.14, 'cap', ink=False)
    k.col(-1.95, 1.95, -0.7, 0.7, 0, 0.75)
    k.col(-1.903, 1.903, -0.03, 0.03, 0.75, 1.14)
    i = 0
    for sy in (-1, 1):
        f = 0 if sy < 0 else 180       # monitors face away from the divider
        for x in (-0.95, 0.95):
            monitor(k, x, sy * 0.16, f, 0.75, 'screen' if i % 2 else 'screen2')
            keyboard(k, x, sy * 0.43, f, 0.75)
            task_chair(k, x + 0.06 * sy, sy * 1.12, 180 - f + (12 if i % 3 else -10))
            i += 1
        k.bx(-0.3 + sy * 0.05, 0.0 + sy * 0.05, *srt(sy * 0.2, sy * 0.5), 0.75, 0.765, 'paper', ink=False)
        mug(k, 1.5, sy * 0.35, 0.75, 'teal' if sy < 0 else 'amber')
    small_plant(k, 0.4, 0.25, 0.75)
    return k


def meeting(k, variant):
    """8 x 6 m glass meeting room: full-height glazing (open panes + frosted band + glints), two doors,
    long table with eight chairs, wall screen on a credenza."""
    k.begin()
    GX, GY = 3.9, 2.9
    tab, chairc, frame = ('walnut', 'chair', 'graphite') if variant == 'A' else ('column', 'coral', 'steelDark')
    doors = {'S': (-3.2, -1.6), 'N': (1.6, 3.2)}
    # posts: corners + jambs + intermediate
    xs = {'S': [-3.2, -1.6, -0.2, 1.2, 2.6], 'N': [-2.6, -1.2, 0.2, 1.6, 3.2]}
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * GX - 0.04, sx * GX + 0.04, sy * GY - 0.04, sy * GY + 0.04, 0, 3.86, 'mullion')
    for side, sy in (('S', -1), ('N', 1)):
        for x in xs[side]:
            k.bx(x - 0.025, x + 0.025, sy * GY - 0.04, sy * GY + 0.04, 0, 3.86, 'mullion')
    for sx in (-1, 1):
        for y in (-1.45, 0.0, 1.45):
            k.bx(sx * GX - 0.04, sx * GX + 0.04, y - 0.025, y + 0.025, 0, 3.86, 'mullion')
    # glazing runs: (axis, fixed, a0, a1)
    runs = [('x', -GY, -GX, doors['S'][0]), ('x', -GY, doors['S'][1], GX), ('x', GY, -GX, doors['N'][0]),
            ('x', GY, doors['N'][1], GX), ('y', -GX, -GY + 0.04, GY - 0.04), ('y', GX, -GY + 0.04, GY - 0.04)]
    for (ax, fx, a0, a1) in runs:
        if ax == 'x':
            k.bx(a0, a1, fx - 0.035, fx + 0.035, 0, 0.06, 'graphite', ink=False)
            k.bx(a0, a1, fx - 0.035, fx + 0.035, 3.86, 3.99, 'graphite', ink=False)
            k.bx(a0, a1, fx - 0.01, fx + 0.01, 1.05, 1.45, 'frost', ink=False)
            k.col(a0, a1, fx - 0.05, fx + 0.05, 0, 4.0)
        else:
            k.bx(fx - 0.035, fx + 0.035, a0, a1, 0, 0.06, 'graphite', ink=False)
            k.bx(fx - 0.035, fx + 0.035, a0, a1, 3.86, 3.99, 'graphite', ink=False)
            k.bx(fx - 0.01, fx + 0.01, a0, a1, 1.05, 1.45, 'frost', ink=False)
            k.col(fx - 0.05, fx + 0.05, a0, a1, 0, 4.0)
    # glints on the outer faces of a few panes
    for (x, sy) in ((-0.9, -1), (1.9, -1), (-1.9, 1), (0.9, 1)):
        y = sy * (GY + 0.015)
        k.poly([(x - 0.3, y, 1.7), (x - 0.22, y, 1.7), (x + 0.2, y, 2.9), (x + 0.12, y, 2.9)], 'glint', (0, sy, 0))
        k.poly([(x - 0.08, y, 1.85), (x - 0.04, y, 1.85), (x + 0.3, y, 2.8), (x + 0.26, y, 2.8)], 'glint', (0, sy, 0))
    for (y, sx) in ((-0.7, -1), (0.75, 1)):
        x = sx * (GX + 0.015)
        k.poly([(x, y - 0.3, 1.7), (x, y - 0.22, 1.7), (x, y + 0.2, 2.9), (x, y + 0.12, 2.9)], 'glint', (sx, 0, 0))
    # door pulls on the jambs
    for side, sy in (('S', -1), ('N', 1)):
        for x in doors[side]:
            for f in (-1, 1):
                y0, y1 = srt(sy * GY + f * 0.04, sy * GY + f * 0.07)
                k.bx(x - 0.015, x + 0.015, y0, y1, 0.8, 1.3, 'steel', ink=False)
    # table and chairs
    k.bx(-2.0, 2.0, -0.6, 0.6, 0.72, 0.76, tab, bevel=False)
    k.bx(-1.4, -1.1, -0.25, 0.25, 0, 0.72, frame, ink=False)
    k.bx(1.1, 1.4, -0.25, 0.25, 0, 0.72, frame, ink=False)
    k.qz(-0.25, 0.25, -0.1, 0.1, 0.763, 1, 'black')                     # conference phone
    k.col(-2.0, 2.0, -0.6, 0.6, 0, 0.76)
    for i, x in enumerate((-1.3, 0.0, 1.3)):
        side_chair(k, x + 0.05 * (i - 1), -1.0, 180 + (6 if i % 2 else -5), chairc)
        side_chair(k, x - 0.04 * (i - 1), 1.0, 0 + (8 if i == 2 else -4), chairc)
    side_chair(k, -2.45, 0.0, 90, chairc)
    side_chair(k, 2.45, 0.05, -90, chairc)
    for (x, y) in ((-1.0, -0.3), (0.6, 0.25)):
        k.qz(x - 0.11, x + 0.11, y - 0.15, y + 0.15, 0.763, 1, 'paper')
    # credenza + wall screen at the west end
    k.bx(-3.75, -3.35, -0.95, 0.95, 0, 0.7, 'walnut2')
    k.bx(-3.56, -3.52, -0.06, 0.06, 0.7, 1.15, 'graphite', ink=False)
    k.bx(-3.52, -3.45, -0.82, 0.82, 1.1, 2.05, 'black')
    k.qx(-0.78, 0.78, 1.14, 2.01, -3.447, 1, 'screen')
    for i, h in enumerate((0.25, 0.42, 0.33, 0.55, 0.47)):
        y = -0.6 + i * 0.26
        k.qx(y, y + 0.16, 1.25, 1.25 + h, -3.444, 1, 'white' if i % 2 else 'glow')
    k.col(-3.75, -3.35, -0.95, 0.95, 0, 0.7)
    k.col(-3.56, -3.45, -0.82, 0.82, 0.7, 2.05)
    potted(k, 3.35, -2.35, 'snake', 0.8)
    k.col(3.15, 3.55, -2.55, -2.15, 0, 0.5)
    return k


def exec_desk(k):
    """4 x 3 m executive set: walnut desk facing -Y, high-back chair, two guest chairs, credenza with books."""
    k.begin()
    k.bx(-0.9, 0.9, -0.42, 0.42, 0.72, 0.77, 'walnut')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.82, s * 0.88)
        k.bx(x0, x1, -0.38, 0.38, 0, 0.72, 'walnut2')
    k.bx(-0.82, 0.82, -0.32, -0.29, 0.25, 0.72, 'walnut2', ink=False)
    monitor(k, 0.15, -0.15, 180, 0.77)
    keyboard(k, 0.1, 0.2, 180, 0.77)
    k.cyl(-0.6, 0.15, 0.77, 0.07, 0.07, 0.02, 'brass', seg=8, ink=False)               # desk lamp
    k.beam((-0.6, 0.15, 0.79), (-0.6, 0.05, 1.12), 0.02, 'brass', ink=False)
    k.cyl(-0.6, 0.02, 1.04, 0.13, 0.06, 0.12, 'oak', seg=8)
    k.bx(-0.45, -0.2, -0.3, -0.1, 0.77, 0.79, 'paper', ink=False)
    # high-back chair
    k.push(0.0, 0.7, 0)
    k.bx(-0.3, 0.3, -0.03, 0.03, 0.05, 0.09, 'graphite', ink=False)
    k.bx(-0.03, 0.03, -0.3, 0.3, 0.055, 0.095, 'graphite', ink=False)
    k.bx(-0.025, 0.025, -0.025, 0.025, 0.095, 0.42, 'steelDark', ink=False)
    k.bx(-0.28, 0.28, -0.26, 0.26, 0.42, 0.53, 'black')
    k.bx(-0.26, 0.26, 0.22, 0.32, 0.53, 1.3, 'black')
    for s in (-1, 1):
        x0, x1 = srt(s * 0.28, s * 0.33)
        k.bx(x0, x1, -0.2, 0.2, 0.62, 0.68, 'graphite', ink=False)
        k.bx(x0, x1, 0.05, 0.12, 0.53, 0.62, 'graphite', ink=False)
    k.pop()
    side_chair(k, -0.45, -0.95, 180 + 10, 'coral', 'walnut2')
    side_chair(k, 0.45, -0.95, 180 - 12, 'coral', 'walnut2')
    # credenza
    k.bx(-1.3, 1.3, 1.1, 1.45, 0, 0.72, 'walnut2')
    for i in range(4):
        x0 = -1.27 + i * 0.64
        k.qy(x0, x0 + 0.6, 0.06, 0.68, 1.097, -1, 'walnut')
    x = -1.1
    for j, c in enumerate(('fabricBlue', 'coral', 'graphite2', 'amber', 'teal', 'oak2')):
        w = 0.06 + 0.02 * (j % 2)
        k.bx(x, x + w, 1.18, 1.4, 0.72, 0.98 + 0.03 * (j % 3), c, ink=False)
        x += w + 0.005
    small_plant(k, 0.9, 1.27, 0.72)
    k.bx(0.1, 0.4, 1.2, 1.38, 0.72, 0.95, 'black')                                   # photo frame
    k.qy(0.13, 0.37, 0.74, 0.92, 1.197, -1, 'screen2')
    k.col(-0.9, 0.9, -0.42, 0.42, 0, 0.77)
    k.col(-1.3, 1.3, 1.1, 1.45, 0, 0.72)
    return k


def lounge(k, variant):
    """4 x 3 m lounge: sofa, two armchairs, coffee table, rug, floor lamp."""
    k.begin()
    sofa, arm = ('coral', 'sofaBlue') if variant == 'A' else ('sofaBlue', 'coral')
    k.qz(-1.7, 1.7, -1.3, 1.3, 0.014, 1, 'rug')
    k.qz(-1.6, 1.6, -1.2, 1.2, 0.017, 1, 'fabricLight')
    # sofa along +Y facing -Y
    k.bx(-1.1, 1.1, 0.6, 1.4, 0.1, 0.42, sofa)
    k.bx(-1.1, 1.1, 1.15, 1.4, 0.42, 0.85, sofa)
    for s in (-1, 1):
        x0, x1 = srt(s * 0.92, s * 1.1)
        k.bx(x0, x1, 0.6, 1.15, 0.42, 0.62, sofa)
        for yy in (0.66, 1.34):
            k.bx(s * 1.0 - 0.03, s * 1.0 + 0.03, yy - 0.03, yy + 0.03, 0, 0.1, 'walnut2', ink=False)
    for i in range(3):
        x0 = -0.92 + i * 0.6133
        k.bx(x0, x0 + 0.6133, 0.6, 1.15, 0.42, 0.52, sofa)
    for x in (-0.55, 0.55):
        k.bx(x - 0.22, x + 0.22, 0.95, 1.12, 0.52, 0.86, 'fabricLight' if variant == 'A' else 'amber')
    # armchairs
    for s in (-1, 1):
        k.push(s * 1.5, -0.45, -s * 90 + s * 15)
        k.bx(-0.38, 0.38, -0.35, 0.38, 0.12, 0.42, arm)
        k.bx(-0.38, 0.38, 0.2, 0.38, 0.42, 0.8, arm)
        for t in (-1, 1):
            x0, x1 = srt(t * 0.26, t * 0.38)
            k.bx(x0, x1, -0.35, 0.2, 0.42, 0.6, arm)
            for yy in (-0.3, 0.32):
                k.bx(t * 0.32 - 0.025, t * 0.32 + 0.025, yy - 0.025, yy + 0.025, 0, 0.12, 'walnut2', ink=False)
        k.bx(-0.26, 0.26, -0.35, 0.2, 0.42, 0.5, 'fabricLight' if variant == 'A' else 'cap')
        k.pop()
    # coffee table
    k.bx(-0.6, 0.6, -0.4, 0.2, 0.36, 0.4, 'oak')
    k.bx(-0.55, 0.55, -0.35, 0.15, 0.06, 0.08, 'oak2', ink=False)
    for (x, y) in ((-0.55, -0.35), (0.55, -0.35), (-0.55, 0.15), (0.55, 0.15)):
        k.bx(x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0, 0.36, 'walnut2', ink=False)
    k.qz(-0.4, -0.1, -0.3, -0.08, 0.403, 1, 'paper')
    k.qz(-0.32, -0.04, -0.25, -0.02, 0.406, 1, 'teal')
    mug(k, 0.25, -0.1, 0.4, 'white')
    small_plant(k, 0.3, 0.05, 0.4)
    # floor lamp behind the sofa end
    k.cyl(1.6, 1.2, 0.0, 0.14, 0.14, 0.03, 'graphite', seg=8, ink=False)
    k.cyl(1.6, 1.2, 0.03, 0.015, 0.015, 1.45, 'graphite', seg=5, ink=False)
    k.cyl(1.6, 1.2, 1.4, 0.2, 0.14, 0.28, 'glow', seg=10)
    k.col(-1.1, 1.1, 0.6, 1.4, 0, 0.85)
    for s in (-1, 1):
        x0, x1 = srt(s * 1.12, s * 1.88)
        k.col(x0, x1, -0.85, -0.05, 0, 0.8)
    k.col(-0.6, 0.6, -0.4, 0.2, 0, 0.4)
    return k


def elevators(k):
    """Landmark: 12 x 6 m elevator core with three stainless cars on each long face."""
    k.begin()
    k.bx(-5.97, 5.97, -2.97, 2.97, 0, 3.99, 'walnut')
    for f in (-1, 1):
        y0, y1 = srt(f * 2.97, f * 2.985)
        k.bx(-5.97, 5.97, y0, y1, 0, 0.15, 'granite', ink=False)            # stone base
        k.bx(-5.97, 5.97, y0, y1, 3.35, 3.42, 'brass', ink=False)           # brass reveal
        for x in (-5.0, -1.75, 1.75, 5.0):
            k.qy(x - 0.01, x + 0.01, 0.15, 3.35, f * 2.973, f, 'walnut2')
        for cx in (-3.5, 0.0, 3.5):
            # portal frame
            for s in (-1, 1):
                x0, x1 = srt(cx + s * 0.75, cx + s * 0.95)
                k.bx(x0, x1, *srt(f * 2.967, f * 3.08), 0.16, 2.65, 'steel')
            k.bx(cx - 0.95, cx + 0.95, *srt(f * 2.967, f * 3.08), 2.65, 2.85, 'steel')
            k.bx(cx - 0.75, cx, *srt(f * 2.967, f * 3.0), 0.16, 2.65, 'steel2', ink=False)
            k.bx(cx, cx + 0.75, *srt(f * 2.967, f * 3.0), 0.16, 2.65, 'steel2', ink=False)
            k.qy(cx - 0.008, cx + 0.008, 0.18, 2.63, f * 3.003, f, 'steelDark')
            k.bx(cx - 0.95, cx + 0.95, *srt(f * 2.967, f * 3.1), 0.0, 0.16, 'steel', ink=False)    # sill
            # floor indicator
            k.bx(cx - 0.35, cx + 0.35, *srt(f * 2.967, f * 3.05), 2.98, 3.22, 'black')
            k.poly([(cx - 0.22, f * 3.053, 3.03), (cx - 0.08, f * 3.053, 3.03), (cx - 0.15, f * 3.053, 3.17)], 'teal', (0, f, 0))
            k.poly([(cx + 0.08, f * 3.053, 3.17), (cx + 0.22, f * 3.053, 3.17), (cx + 0.15, f * 3.053, 3.03)], 'amber', (0, f, 0))
            k.qy(cx + 0.0, cx + 0.03, 3.04, 3.16, f * 3.053, f, 'glow')
        for cx in (-1.75, 1.75):   # call panels between the cars
            k.bx(cx - 0.09, cx + 0.09, *srt(f * 2.973, f * 3.0), 1.0, 1.45, 'steel', ink=False)
            k.poly([(cx - 0.04, f * 3.003, 1.27), (cx + 0.04, f * 3.003, 1.27), (cx, f * 3.003, 1.35)], 'teal', (0, f, 0))
            k.poly([(cx - 0.04, f * 3.003, 1.2), (cx + 0.04, f * 3.003, 1.2), (cx, f * 3.003, 1.12)], 'white', (0, f, 0))
    for s in (-1, 1):   # end faces: stone with a directory board and a fire cabinet
        x0, x1 = srt(s * 5.97, s * 5.985)
        k.bx(x0, x1, -2.97, 2.97, 0, 0.15, 'granite', ink=False)
        k.bx(x0, x1, -2.97, 2.97, 3.35, 3.42, 'brass', ink=False)
        dx0, dx1 = srt(s * 5.97, s * 6.02)
        k.bx(dx0, dx1, -1.2, 0.2, 1.0, 2.3, 'black')
        for j in range(6):
            z = 1.12 + j * 0.19
            k.qx(-1.1, -0.1 - 0.12 * (j % 3), z, z + 0.08, s * 6.023, s, 'white' if j % 2 else 'glow')
            k.qx(0.0, 0.1, z, z + 0.08, s * 6.023, s, 'teal')
        fx0, fx1 = srt(s * 5.97, s * 6.03)
        k.bx(fx0, fx1, 1.0, 1.6, 0.8, 1.6, 'red')
        k.qx(1.05, 1.55, 0.85, 1.55, s * 6.033, s, 'glint')
    k.col(-5.97, 5.97, -2.97, 2.97, 0, 4.0)
    return k


def reception(k):
    """Landmark: 6 x 3 m reception desk (walnut slats, stone ledge) and a feature wall with a brass emblem."""
    k.begin()
    k.bx(-2.4, 2.4, -0.6, -0.45, 0, 1.1, 'walnut')
    for i in range(23):
        x = -2.3 + i * 0.2
        k.qy(x, x + 0.03, 0.08, 1.04, -0.603, -1, 'walnut2')
    for s in (-1, 1):
        x0, x1 = srt(s * 2.4, s * 2.55)
        k.bx(x0, x1, -0.6, 0.25, 0, 1.1, 'walnut')
    k.bx(-2.6, 2.6, -0.72, -0.3, 1.1, 1.16, 'marble')
    k.bx(-2.4, 2.4, -0.45, 0.25, 0.72, 0.75, 'oak')
    k.qy(-2.35, 2.35, 0.02, 0.06, -0.606, -1, 'glow')                                # toe light
    for x in (-1.0, 1.0):
        monitor(k, x, -0.25, 180, 0.75, 'screen2')
        keyboard(k, x, 0.0, 180, 0.75)
        task_chair(k, x + 0.1, 0.75, 0 + (10 if x > 0 else -8), 'chair')
    k.bx(-0.3, 0.3, -0.35, -0.15, 0.75, 0.76, 'paper', ink=False)
    # feature wall
    k.bx(-2.8, 2.8, 1.2, 1.45, 0, 3.2, 'walnut2')
    for i in range(14):
        x = -2.7 + i * 0.4
        k.qy(x, x + 0.025, 0.05, 3.15, 1.197, -1, 'walnut')
    k.bx(-2.8, 2.8, 1.18, 1.45, 3.2, 3.26, 'brass', ink=False)
    for i, (x, h) in enumerate(((-0.35, 1.0), (0.0, 1.35), (0.35, 0.8))):            # emblem: three towers
        k.bx(x - 0.12, x + 0.12, 1.12, 1.2, 1.5, 1.5 + h, 'brass')
    k.bx(-0.55, 0.55, 1.14, 1.2, 1.38, 1.44, 'teal', ink=False)
    potted(k, -2.6, 0.75, 'fig', 0.95)
    potted(k, 2.6, 0.75, 'palm', 0.95)
    k.col(-2.6, 2.6, -0.72, 0.25, 0, 1.16)
    k.col(-2.8, 2.8, 1.18, 1.45, 0, 3.26)
    k.col(-2.85, -2.35, 0.5, 1.0, 0, 0.6)
    k.col(2.35, 2.85, 0.5, 1.0, 0, 0.6)
    return k


def floor_marble(k):
    k.begin()
    k.bx(-2, 2, -2, 2, 0, 0.02, 'marble', ink=False)
    k.qz(-2, 2, -2, -1.97, 0.023, 1, 'vein')
    k.qz(-2, -1.97, -1.97, 2, 0.023, 1, 'vein')
    k.poly([(0, -0.8, 0.023), (0.8, 0, 0.023), (0, 0.8, 0.023), (-0.8, 0, 0.023)], 'granite', (0, 0, 1))
    k.poly([(0, -0.5, 0.026), (0.5, 0, 0.026), (0, 0.5, 0.026), (-0.5, 0, 0.026)], 'marble', (0, 0, 1))
    k.poly([(0, -0.2, 0.029), (0.2, 0, 0.029), (0, 0.2, 0.029), (-0.2, 0, 0.029)], 'brass', (0, 0, 1))
    return k


# ================================================================ skyline backdrop (fogged, beyond the windows)
# One long slice of Manhattan, placed four times by the theme's backdrop ring (count 4: due east, west, north and
# south of the level, each facing it). Local frame: the row runs along Blender X (+-120 m), the front line is Y = 0
# facing -Y (toward the level), depth goes to +Y. Bases sink to z = -25: the haze plane hides everything below the
# floor we stand on, so only rooftops, upper floors and towers show. Window detail sits on the faces the level sees.
BASE_Z = -25.0


def front_rows(k, x0, x1, y0, z0, z1, step, h, c):
    """Horizontal window ribbons on a front face (y = y0, facing -Y)."""
    z = max(z0, -4.0) + step * 0.5
    while z + h < z1 - 0.6:
        k.qy(x0 + 0.5, x1 - 0.5, z, z + h, y0 - 0.06, -1, c)
        z += step


def front_cols(k, x0, x1, y0, z0, z1, n, w, c):
    """Vertical window strips on a front face."""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        k.qy(x - w, x + w, max(z0, -4.0), z1 - 0.8, y0 - 0.06, -1, c)


def side_cols(k, x0, x1, y0, y1, z0, z1, n, w, c):
    for s, x in ((-1, x0 - 0.06), (1, x1 + 0.06)):
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            k.qx(y - w, y + w, max(z0, -4.0), z1 - 0.8, x, s, c)


def lean_tank(k, x, y, z):
    """Rooftop water tank on a steel frame."""
    k.bx(x - 1.3, x + 1.3, y - 1.3, y + 1.3, z, z + 2.4, 'graphite', ink=False)
    k.cyl(x, y, z + 2.4, 1.6, 1.6, 3.0, 'tank', seg=8)
    k.cyl(x, y, z + 5.4, 1.7, 0.15, 1.5, 'tank', seg=8, ink=False)


def near_block(k, x, y, w, d, h, c, roof):
    """Pre-war block whose roof sits a few metres above the haze."""
    x0, x1, y1 = x - w / 2, x + w / 2, y + d
    k.bx(x0, x1, y, y1, BASE_Z, h, c)
    k.bx(x0 - 0.35, x1 + 0.35, y - 0.35, y1 + 0.35, h, h + 0.7, 'lime' if c != 'lime' else 'lime2')
    k.qz(x0 + 0.4, x1 - 0.4, y + 0.4, y1 - 0.4, h + 0.704, 1, 'roof')
    front_rows(k, x0, x1, y, BASE_Z, h, 3.2, 1.3, 'winDark')
    n = max(2, int(w / 2.4))
    for i in range(n + 1):
        px = x0 + 0.3 + (w - 0.6) * i / n
        k.qy(px - 0.3, px + 0.3, -4.0, h - 0.2, y - 0.09, -1, c)
    if roof == 'tank':
        lean_tank(k, x + w * 0.2, y + d * 0.55, h + 0.7)
        k.bx(x - w * 0.35, x - w * 0.35 + 3.0, y + 2.0, y + 5.0, h + 0.7, h + 3.0, 'lime2')
    elif roof == 'hvac':
        k.bx(x - 3.0, x + 1.0, y + 2.0, y + 5.5, h + 0.7, h + 2.2, 'steel2')
        k.bx(x + 2.0, x + 4.5, y + 3.0, y + 6.0, h + 0.7, h + 1.6, 'steel')


def mid_tower(k, x, y, w, d, h, style):
    x0, x1, y1 = x - w / 2, x + w / 2, y + d
    if style == 'glass':
        k.bx(x0, x1, y, y1, BASE_Z, h, 'glassB')
        front_rows(k, x0, x1, y, BASE_Z, h, 4.0, 0.8, 'glassB2')
        k.bx(x0 + 1.5, x1 - 1.5, y + 1.5, y1 - 1.5, h, h + 3.0, 'deco')
    elif style == 'slab':
        k.bx(x0, x1, y, y1, BASE_Z, h, 'lime2')
        front_cols(k, x0, x1, y, BASE_Z, h, int(w / 2.2), 0.45, 'winDark')
        k.bx(x0 + w * 0.2, x1 - w * 0.2, y + 2.0, y1 - 1.0, h, h + 7.0, 'lime')
        front_cols(k, x0 + w * 0.2, x1 - w * 0.2, y + 2.0, h, h + 7.0, max(2, int(w * 0.6 / 2.2)), 0.4, 'winDark')
    else:   # brick tower with a stepped top
        k.bx(x0, x1, y, y1, BASE_Z, h, 'brick')
        front_rows(k, x0, x1, y, BASE_Z, h, 3.4, 1.2, 'winDark')
        k.bx(x0 + 2.0, x1 - 2.0, y + 2.0, y1 - 2.0, h, h + 4.0, 'oak2')
        lean_tank(k, x + 1.0, y + d * 0.5, h + 4.0)


def far_tower(k, x, y, kind):
    if kind == 'deco':        # art-deco crown and spire
        k.bx(x - 9, x + 9, y, y + 16, BASE_Z, 40, 'lime')
        front_cols(k, x - 9, x + 9, y, BASE_Z, 40, 7, 0.55, 'winDark')
        k.bx(x - 6.5, x + 6.5, y + 2.5, y + 13.5, 40, 66, 'lime')
        front_cols(k, x - 6.5, x + 6.5, y + 2.5, 40, 66, 5, 0.5, 'winDark')
        k.bx(x - 4.5, x + 4.5, y + 4, y + 12, 66, 82, 'deco')
        for j, (r, z0, hh) in enumerate(((5.6, 82, 5.0), (3.8, 87, 6.5))):
            k.cyl(x, y + 8, z0, r, r * 0.8, hh, 'deco', seg=8)
            for i in (5, 6, 7):
                a = (i + 0.5) / 8 * math.pi * 2
                ca, sa = math.cos(a), math.sin(a)
                rr = r * 0.9 + 0.1
                k.poly([(x + ca * rr - sa * 0.5, y + 8 + sa * rr + ca * 0.5, z0 + 0.5), (x + ca * rr + sa * 0.5, y + 8 + sa * rr - ca * 0.5, z0 + 0.5),
                        (x + ca * rr * 0.93, y + 8 + sa * rr * 0.93, z0 + hh - 0.4)], 'winDark', (ca, sa, 0.1))
        k.cyl(x, y + 8, 93.5, 0.7, 0.05, 18, 'deco', seg=6, ink=False)
    elif kind == 'spire':     # stepped limestone tower with a mooring mast
        k.bx(x - 11, x + 11, y, y + 16, BASE_Z, 20, 'lime')
        front_cols(k, x - 11, x + 11, y, BASE_Z, 20, 8, 0.5, 'winDark')
        k.bx(x - 7, x + 7, y + 3, y + 13, 20, 78, 'lime')
        front_cols(k, x - 7, x + 7, y + 3, 20, 78, 6, 0.45, 'winDark')
        k.bx(x - 5, x + 5, y + 4, y + 12, 78, 88, 'lime2')
        k.cyl(x, y + 8, 88, 2.4, 1.6, 9, 'deco', seg=8)
        k.cyl(x, y + 8, 97, 0.45, 0.05, 20, 'deco', seg=6, ink=False)
    elif kind == 'needle':    # super-slim glass tower
        k.bx(x - 4.5, x + 4.5, y, y + 9, BASE_Z, 128, 'glassG')
        front_rows(k, x - 4.5, x + 4.5, y, BASE_Z, 128, 8.0, 0.6, 'glassB2')
        k.bx(x - 3.5, x + 3.5, y + 1, y + 8, 128, 133, 'glassB2')
    elif kind == 'glass':     # blue glass tower with a sloped crown
        k.bx(x - 8, x + 8, y, y + 16, BASE_Z, 84, 'glassB')
        front_rows(k, x - 8, x + 8, y, BASE_Z, 84, 4.0, 0.7, 'glassB2')
        side_cols(k, x - 8, x + 8, y, y + 16, BASE_Z, 84, 3, 0.15, 'deco')
        k.cyl(x, y + 8, 84, 11.3, 5.0, 8, 'glassB2', seg=4, rot=(0, 0, 45))
    else:                     # tall limestone slab
        k.bx(x - 13, x + 13, y, y + 12, BASE_Z, 58, 'lime2')
        front_cols(k, x - 13, x + 13, y, BASE_Z, 58, 10, 0.5, 'winDark')
        k.bx(x - 8, x + 8, y + 2, y + 10, 58, 70, 'lime2')
        front_cols(k, x - 8, x + 8, y + 2, 58, 70, 6, 0.45, 'winDark')


def cloud_bank(k, x, y, s):
    k.sph(x, y, -1.2, 6.0 * s, 'white', seg=(6, 4), scale=(1.0, 0.8, 0.42))
    k.sph(x + 6.5 * s, y + 1.5, -1.6, 4.6 * s, 'paper', seg=(6, 4), scale=(1.0, 0.8, 0.45))


def backdrop_skyline(k):
    """Layered skyline slice: low cloud banks, pre-war rooftops with water tanks, mid towers, tall towers."""
    k.begin()
    for (x, s) in ((-100, 1.0), (-52, 0.9), (-4, 1.1), (46, 0.9), (96, 1.05)):
        cloud_bank(k, x, 3.0, s)
    near = ((-109, 16, 12, 4.0, 'brick', 'tank'), (-88, 18, 14, 6.5, 'lime', 'hvac'), (-66, 15, 11, 3.0, 'oak2', 'tank'),
            (-44, 19, 13, 7.5, 'brick', 'none'), (-22, 16, 12, 5.0, 'lime2', 'tank'), (0, 18, 14, 2.5, 'brick', 'hvac'),
            (22, 15, 12, 6.0, 'lime', 'tank'), (44, 17, 13, 4.5, 'oak2', 'none'), (66, 16, 12, 8.0, 'brick', 'none'),
            (88, 18, 14, 3.5, 'lime2', 'hvac'), (110, 14, 11, 5.5, 'brick', 'tank'))
    for (x, w, d, h, c, roof) in near:
        near_block(k, x, 6.0 + (abs(x) % 3), w, d, h, c, roof)
    mids = ((-100, 16, 12, 34, 'slab'), (-70, 14, 12, 48, 'glass'), (-40, 15, 11, 30, 'brick'), (-8, 18, 12, 52, 'slab'),
            (26, 14, 12, 40, 'glass'), (58, 16, 11, 33, 'brick'), (92, 17, 12, 56, 'slab'))
    for (x, w, d, h, style) in mids:
        mid_tower(k, x, 24.0 + (abs(x) % 3), w, d, h, style)
    k.push(0, 0, 0, 0, 0.78)        # far layer squeezed down: crowns and spires sit inside the window band
    for (x, kind) in ((-90, 'glass'), (-56, 'deco'), (-22, 'needle'), (12, 'spire'), (46, 'slab'), (80, 'deco'), (110, 'needle')):
        far_tower(k, x, 40.0 + (abs(x) % 3), kind)
    k.pop()
    return k


# ================================================================ build
WIN_KINDS = ('A', 'B', 'C')
SIDES = (('', 0), ('_W', 90), ('_E', -90))
CORNERS = (('NW', 0), ('NE', -90), ('SE', 180), ('SW', 90))


def build_kit_office(ao):
    pal = Palette(FAM)
    k = Kit(pal)
    # walls
    for kind in WIN_KINDS:
        for tag, rot in SIDES:
            window_module(k, kind, rot).finish('Win_%s%s' % (kind, tag))
    for tag, rot in SIDES:
        win_column(k, rot).finish('WinCol%s' % tag)
    for tag, rot in CORNERS:
        win_corner(k, rot).finish('WinCorner_%s' % tag)
    for kind in ('A', 'Art', 'Board', 'Door', 'Screen', 'Ext'):
        drywall(k, kind).finish('Dry_%s' % kind, ao=ao)
    core(k).finish('Core', ao=ao)
    for kind in ('Wood', 'WoodSconce', 'Stone'):
        lobby(k, kind).finish('Lobby%s' % kind)
    # ceiling, gate, trail, hatch, stand
    ceil_light(k).finish('CeilLight')
    gate_frame(k).finish('GateFrame', ao=ao)
    shutter = gate_shutter(k).finish('GateShutter')
    m = Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    trail_wall(k).finish('TrailWall', ao=ao)
    for kind in ('Art', 'Board', 'Screen', 'Ext'):
        trail_variant(k, kind).finish('TrailWall_' + kind, ao=ao)
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    # cell props
    for kind in ('A', 'B', 'C'):
        lateral_file(k, kind).finish('File_%s' % kind, ao=ao)
    for kind in ('Copier', 'Printer', 'Boxes'):
        copier(k, kind).finish(kind, ao=ao)
    for kind in ('A', 'B'):
        tall_cabinet(k, kind).finish('Tall_%s' % kind, ao=ao)
    for kind, nm in (('fig', 'Plant_Fig'), ('snake', 'Plant_Snake'), ('palm', 'Plant_Palm')):
        plant(k, kind).finish(nm, ao=ao)
    for kind in ('A', 'B'):
        rack(k, kind).finish('Rack_%s' % kind, ao=ao)
    for kind in ('Plain', 'Sink', 'Coffee', 'Micro'):
        counter(k, kind).finish('Counter_%s' % kind, ao=ao)
    for kind in ('Fridge', 'Vending'):
        fridge(k, kind).finish(kind, ao=ao)
    for kind in ('Cooler', 'Bins'):
        cooler(k, kind).finish(kind, ao=ao)
    # prefabs
    for v in ('A', 'B'):
        cubicle_pod(k, v).finish('Cubicle_%s' % v, ao=ao)
    bench(k).finish('Bench_A', ao=ao)
    for v in ('A', 'B'):
        meeting(k, v).finish('Meeting_%s' % v, ao=ao)
    exec_desk(k).finish('Exec_A', ao=ao)
    for v in ('A', 'B'):
        lounge(k, v).finish('Lounge_%s' % v, ao=ao)
    elevators(k).finish('Landmark_Elevators', ao=ao)
    reception(k).finish('Landmark_Reception', ao=ao)
    floor_marble(k).finish('FloorMarble')
    # skyline
    backdrop_skyline(k).finish('Backdrop_Skyline')
    total = 0
    for n in sorted(k.tris):
        total += k.tris[n]
        print('%-34s %6d tris' % (n, k.tris[n]))
    print('kit-office total (one of each, incl. turned variants): %d tris' % total)
    export(FAM)


FAMILY = 'kit-office'
BUILD = build_kit_office
