"""INKBOLT kit-riviera ("Grand Hotel Riviera", a made-up Belle Epoque seaside grand hotel on a cliff over the
Mediterranean): palette, kit class and helpers shared by rv_walls.py (the zone walls: the ground floor's interior
walls, arched sea windows, doorways, the closed suite doors; the pool terrace's white stucco facades with blue
shutters, the podium's spa front and its roof parapet, the sea balustrade and the infinity edge; gate, trail, hatch),
rv_inside.py (zone 1: the imperial staircase, the restaurant, the bar, the conference hall, the palm court, the
ceiling tiles) and rv_pool.py (zone 2: the infinity pool, the spa pool, the pool bar, sun loungers, the towel hut,
the roof garden's pergolas, gazebo, planters, paving and its stairs).

Furniture from The Aurelian (kit-hotel, level 20) is built again here from hotel_props / hotel_rooms / hotel_struct
with this kit's palette: the same palette names, recoloured for the Riviera (the hotel's wine velvet is the Riviera
blue here, its emerald a coral, its silk a pale sea-glass), so the borrowed pieces wear this hotel's colours.

Conventions (src/game/zones.js, hotel_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (south, the piece's front), Blender +X = game east.
  * Wall modules face Blender -Y (the theme turns their -Y face to the open side: wall.facing 'open'); the cell spans
    y -0.5..0.5, the face the player meets is the plane y = -0.5. The theme's wall.height is 4.5 m (the gallery /
    roof garden level): taller modules carry their own <Piece>_COL boxes above it (wall.cols).
  * Zone 1: 9 m rooms, the lobby gallery at 4.5 m (slab 4.2 - 4.5); zone 2: the roof garden on the podium at 4.5 m.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: a box robots may walk on (stair treads, landings, pool copings).
  * Stairs rise RISE (0.18 m) per TREAD (0.25 m): 0.36 m per 0.5 m nav cell, under the robots' 0.4 m step.
  * Flat detail (paint, lettering, glints) is a single face without an outline shell, >= 3 mm proud of its surface.
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
import hotel_base as HB

FAM = 'kit-riviera'
PFX = 'KIT_RIVIERA_'
ib_lib.GLB[FAM] = 'fps-kit-riviera.glb'
ib_lib.CFG[FAM] = (0.012, 0.014)
HULL_T = ib_lib.CFG[FAM][1]
H = HB.H            # 9 m rooms (zone 1)
DECK = HB.DECK      # 4.5 m gallery / roof garden
WALLH = 4.5         # the theme's wall.height (collision of every wall cell); taller modules add _COL boxes above
FH = 14.4           # the pool terrace's facades (four storeys of 3.6 m) to the cornice
RISE, TREAD = 0.18, 0.25
WATER = 0.24        # the pools' water surface (wading depth), coping top 0.3
COP = 0.3

# the hotel palette's names (hotel_base.py), recoloured for the Riviera, and the stucco / terracotta / bougainvillea
ib_lib.PALETTES[FAM] = BASE + [
    ('marble', '#F4F0E8'), ('marble2', '#E1D9CB'), ('vein', '#C9C0B2'), ('nero', '#2A2C38'), ('nero2', '#4A4D5C'),
    ('stone', '#EDE5D5'), ('stone2', '#D3C7B0'), ('gold', '#E8BE55'), ('brass', '#CF9F43'), ('bronze', '#8C6430'),
    ('walnut', '#8A5A36'), ('walnut2', '#5E3B24'), ('oak', '#C9955F'),
    # wine -> the Riviera blue (shutters, velvet, runners), emerald -> coral, silk -> pale sea-glass
    ('wine', '#2D6EAE'), ('wine2', '#22548A'), ('wine3', '#173D66'), ('emerald', '#DE7A5B'), ('emerald2', '#B45A40'),
    ('navy', '#243F66'), ('navy2', '#182C4A'), ('teal2', '#2C8A8C'),
    ('cream', '#F7F0E2'), ('ivory', '#FCF8EF'), ('silk', '#D7E7E8'), ('silk2', '#B6D0D5'), ('cgold', '#D9A84C'),
    ('glow', '#FFF2CC'), ('lamp', '#FFE3A3'), ('shade', '#F5E6C0'), ('crystal', '#F3FAFF'), ('crystal2', '#CFE3EE'),
    ('glint', '#FAFDFF'), ('glassT', '#A9CCDC'),
    ('leaf', '#5A9E4E'), ('leaf2', '#3A7040'), ('rose', '#E05470'), ('blush', '#A98BD6'), ('pot', '#EEE6D6'),
    ('soil', '#5A4232'), ('steel', '#C9CDD3'), ('steel2', '#979DA7'), ('chrome', '#E6EAF0'),
    ('water', '#2E9FD0'), ('waterL', '#A4E0F2'), ('tile', '#4FB3CE'), ('teak', '#B57D49'), ('teak2', '#8C5A33'),
    ('screen', '#283849'), ('black', '#1D1A21'), ('fire', '#FF8B2B'), ('sky', '#9FD0EC'), ('canvas', '#ECE3CF'),
    ('stucco', '#F5F0E6'), ('stuccoD', '#D9CEBC'), ('terra', '#C8653D'), ('bougain', '#D23F8E'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]
# upholstery the theme repaints per placed copy (symbol option paint): blue, coral, navy, teal
FABRIC = ['wine', 'emerald', 'navy', 'teal2']

srt = HB.srt
TRIS = {}
txt = HB.txt
disc, vdisc, frame_y, ring = HB.disc, HB.vdisc, HB.frame_y, HB.ring


class RKit(HB.HKit):
    """The Aurelian's kit class (spire / office Kit + walkable boxes + prisms + arcs) under this family's prefix."""

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
            bmesh.ops.remove_doubles(fb, verts=fb.verts[:], dist=1e-5)
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
        for i, (x0, x1, y0, y1, z0, z1, walk) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_%sCOL%d' % (full, 'W' if walk else '', i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj

    def qyd(self, x0, x1, z0, z1, y, s, c):
        """a flat quad facing s * Y, drawn only when it has an area"""
        if x1 - x0 > 1e-4 and z1 - z0 > 1e-4:
            self.qy(x0, x1, z0, z1, y, s, c)


def arch_pts(cx, cz, r, a0, a1, n=8):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cz + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]


def shutter(k, x0, x1, z0, z1, y, s=-1, c='wine', slat='wine2', n=None):
    """A louvred shutter leaf drawn flat on the plane y facing s * Y: the leaf, its stiles and slat lines."""
    k.qy(x0, x1, z0, z1, y, s, c)
    d = 0.003 * s
    w = x1 - x0
    st = min(0.04, w * 0.12)
    k.qy(x0 + st, x1 - st, z0 + 0.05, z1 - 0.05, y + d, s, slat)
    n = n or max(4, int((z1 - z0) / 0.09))
    for i in range(1, n):
        z = z0 + 0.05 + (z1 - z0 - 0.1) * i / n
        k.qy(x0 + st, x1 - st, z - 0.012, z + 0.012, y + 2 * d, s, c)


def balconette(k, x0, x1, z, y, depth=0.32, c='black'):
    """A wrought-iron French balcony rail in front of a window (the face at y, facing -Y): top rail, bottom rail,
    stiles, bars and a scroll band, drawn as thin unoutlined bars, on a stone slab."""
    yf = y - depth
    k.bx(x0 - 0.004, x1 + 0.004, yf - 0.025, yf + 0.025, z + 0.95, z + 1.0, c, ink=False)
    k.bx(x0 - 0.004, x1 + 0.004, yf - 0.02, yf + 0.02, z + 0.06, z + 0.11, c, ink=False)
    for s in (x0, x1 - 0.025):
        k.bx(s, s + 0.025, yf - 0.015, y - 0.004, z + 0.065, z + 0.97, c, ink=False)
    n = max(3, int((x1 - x0) / 0.12))
    for i in range(1, n):
        x = x0 + (x1 - x0) * i / n
        k.bx(x - 0.008, x + 0.008, yf - 0.012, yf + 0.012, z + 0.11, z + 0.95, c, ink=False)
    k.qy(x0 + 0.03, x1 - 0.03, z + 0.62, z + 0.66, yf - 0.029, -1, c)
    k.bx(x0 - 0.04, x1 + 0.04, yf - 0.06, y, z, z + 0.06, 'stone2')
    k.col(x0 - 0.04, x1 + 0.04, yf - 0.06, y, z, z + 1.0)


def bougainvillea(k, x, y, z, w, h, s=-1, seed=0):
    """A cascade of bougainvillea on a wall face (plane y, facing s * Y): leafy clumps in two rows with magenta
    bracts, the lower row hanging lower toward the ends."""
    for i in range(6):
        j = (math.sin(seed * 12.9898 + i * 78.233) * 43758.5453) % 1
        cx = x + ((i % 3) / 2.0 - 0.5) * w * 0.8 + (j - 0.5) * 0.08
        cz = z - (i // 3) * h * 0.45 - (0.25 * h if (i // 3 and i % 3 != 1) else 0.0) + j * 0.06
        r = 0.17 + j * 0.1
        k.sph(cx, y + s * (r * 0.55), cz, r, 'leaf2' if i % 3 == 0 else 'leaf', seg=(6, 4), scale=(1.2, 0.55, 0.9))
        k.sph(cx + 0.05, y + s * (r * 0.95), cz + 0.04, r * 0.55, 'bougain', seg=(5, 3), scale=(1.2, 0.5, 0.9), ink=False)


def potted(k, x, y, r, h, kind='geranium', pot='terra'):
    """A terracotta pot with flowers / herbs on top."""
    k.cyl(x, y, 0, r * 0.82, r, h, pot, seg=10)
    k.cyl(x, y, h - 0.04, r + 0.03, r + 0.03, 0.06, 'emerald2', seg=10, ink=False)
    disc(k, x, y, h - 0.03, r * 0.95, 'soil', n=10)
    if kind == 'geranium':
        k.sph(x, y, h + 0.12, r * 1.05, 'leaf', seg=(7, 4), scale=(1, 1, 0.65))
        for i in range(5):
            a = i * 1.3
            k.sph(x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6, h + 0.2, r * 0.3, 'rose' if i % 2 else 'red', seg=(5, 3), ink=False)
    elif kind == 'lavender':
        for i in range(7):
            a = i * 0.9
            rr = r * 0.55 * (i % 3) / 2
            k.cyl(x + math.cos(a) * rr, y + math.sin(a) * rr, h, 0.05, 0.02, 0.32, 'leaf2', seg=4, ink=False)
            k.cyl(x + math.cos(a) * rr, y + math.sin(a) * rr, h + 0.3, 0.04, 0.02, 0.14, 'blush', seg=4, ink=False)
        k.sph(x, y, h + 0.08, r * 0.9, 'leaf2', seg=(7, 4), scale=(1, 1, 0.5))
