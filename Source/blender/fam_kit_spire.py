"""INKBOLT asset family: kit-spire (The Spire: a cluster of supertall towers ninety floors up, joined by glass
sky-bridges; campaign level 17).

Built off kit-office (fam_kit_office.py): the Kit class (outlined + flat shapes, z-fight check, collision empties),
the furniture helpers (chairs, monitors, plants) and a few office prefabs (lounges, reception, boardroom, executive
desk) are reused with this family's palette, which keeps the office colour names but re-tints them (petrol
fabrics, teal velvet, warm walnut, brass).

Conventions (src/data/themes.js, src/game/zones.js):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z, the room). Wall modules are 9 m tall (double-height floors); the
    mezzanine deck stands at 4.5 m (slab 4.1 - 4.5); ceiling pieces hang from their origin (the 9 m ceiling plane),
    the glass-roof pyramids stand on it.
  * The diagrid curtain wall: diagonals cross every 6 m (bay) and climb 9 m per half-diamond (nodes at the floor,
    the 4.5 m floor beam and the 9 m header). Each 1 m slice of a bay is its own module Dia_<k> (k = 0..5); the
    theme's wall chooser picks the slice from the cell's place on the wall (mirrored where the engine turns the
    module). Everything of a wall module stays inside its cell: zones.js draws each tower's outside skin 0.6 m out.
  * Sky-bridge trail modules carry half of the bridge deck and roof slabs (the two sides meet on the corridor's
    centre line) and a girder under the floor, so a bridge reads as a bridge from the other towers.
  * Collision: <Piece>_COL<n> empties; <Piece>_WCOL<n> for boxes robots may walk on (stairs, escalators).
  * The skyline pieces (Backdrop_RowA / RowB) are built from the tower table in src/data/themes/spire.js (between the
    SKYLINE-BEGIN / END markers), the same table zones.js uses for the shafts that carry them down to the street.
"""
import json
import math
import os
import re

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import fam_kit_office as O

FAM = 'kit-spire'
PFX = 'KIT_SPIRE_'
ib_lib.GLB[FAM] = 'fps-kit-spire.glb'
ib_lib.CFG[FAM] = (0.012, 0.014)
HULL_T = ib_lib.CFG[FAM][1]
H = 9.0          # wall / ceiling height
DECK = 4.5       # mezzanine floor (slab 4.1 - 4.5)
HERE = os.path.dirname(os.path.abspath(__file__))

ib_lib.PALETTES[FAM] = BASE + [
    # office names (furniture reused from fam_kit_office), re-tinted
    ('mullion', '#2B2F38'), ('graphite', '#34363F'), ('graphite2', '#585C68'), ('steel', '#C9CED6'),
    ('steel2', '#A3AAB6'), ('steelDark', '#757D8A'), ('glow', '#FFF4D6'), ('fabricBlue', '#3E7C8C'),
    ('fabricLight', '#E6DCCB'), ('cap', '#ECE6DA'), ('oak', '#D8B07A'), ('oak2', '#B98B55'),
    ('walnut', '#8A5636'), ('walnut2', '#5E3A26'), ('screen', '#7FD8F0'), ('screen2', '#9FF0C8'),
    ('black', '#1E2027'), ('chair', '#2F3138'), ('chairMesh', '#4C505B'), ('leaf', '#56B45E'),
    ('leaf2', '#2F8A4E'), ('pot', '#EDE7DC'), ('soil', '#5E4535'), ('trunk', '#7A5A40'),
    ('frost', '#E4EEF2'), ('glint', '#F4FBFF'), ('marble', '#F1ECE3'), ('vein', '#CFC5B6'),
    ('granite', '#4A4F57'), ('coral', '#E2725B'), ('rug', '#C9A27A'), ('brass', '#D9A84E'),
    ('sofaBlue', '#1F6F78'),
    # the Spire
    ('dia', '#EEF1F4'), ('stone', '#E9DFCF'), ('stone2', '#CDBFA8'), ('onyx', '#F6D59A'),
    ('gold', '#F2C14E'), ('water', '#4FB3D9'), ('waterL', '#A8E2F2'), ('bark', '#6B4A36'),
    ('leafL', '#8FD16A'), ('blossom', '#F29AB8'), ('lawn', '#79B85A'), ('tickG', '#3BE07A'),
    ('night', '#14202E'), ('skyglass', '#BFE6F7'),
    # skyline
    ('twGlass', '#8FB3D1'), ('twDark', '#4D6178'), ('twSand', '#D8C4A2'), ('twWhite', '#E7E4DE'),
    ('twWin', '#5A6E86'), ('twGreen', '#9CC7BE'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
HEX2NAME = {h.upper(): n for (n, h) in ib_lib.PALETTES[FAM]}


class SKit(O.Kit):
    """The office Kit with this family's prefix, walkable collision boxes and extruded polygons."""

    def col(self, x0, x1, y0, y1, z0, z1, walk=False):
        self.cols.append((x0, x1, y0, y1, z0, z1, walk))

    def prism(self, pts, y0, y1, c, ink=True, open_x=None):
        """Polygon in the XZ plane (convex or a simple outline), extruded along Y from y0 to y1. open_x: leave out
        the side faces lying on x = +-open_x (a member running on into the neighbouring module)."""
        P, bm = self.m.parent, self.m.bm
        a = [bm.verts.new(P @ Vector((x, y0, z))) for (x, z) in pts]
        b = [bm.verts.new(P @ Vector((x, y1, z))) for (x, z) in pts]
        fs = [bm.faces.new(a), bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            if open_x is not None and abs(abs(pts[i][0]) - open_x) < 1e-6 and abs(pts[i][0] - pts[j][0]) < 1e-6:
                continue
            fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.m._finish(a + b, c, False)
        self._mark(ink)

    def prism_y(self, pts, x0, x1, c, ink=True):
        """Polygon in the YZ plane, extruded along X."""
        P, bm = self.m.parent, self.m.bm
        a = [bm.verts.new(P @ Vector((x0, y, z))) for (y, z) in pts]
        b = [bm.verts.new(P @ Vector((x1, y, z))) for (y, z) in pts]
        fs = [bm.faces.new(a), bm.faces.new(b)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.m._finish(a + b, c, False)
        self._mark(ink)

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
        for i, (x0, x1, y0, y1, z0, z1, walk) in enumerate(self.cols):
            c = P @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            h = P @ Vector(((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            e = socket('%s_%sCOL%d' % (full, 'W' if walk else '', i), obj, tuple(c))
            e.empty_display_type = 'CUBE'
            e.scale = (abs(h.x), abs(h.y), abs(h.z))
        self.tris[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        return obj


srt = O.srt


def clip_z(poly, lo, hi):
    """Clip a polygon in (x, z) to lo <= z <= hi (Sutherland-Hodgman against two horizontal lines)."""
    def cut(P, keep, zc):
        out = []
        for i in range(len(P)):
            p, q = P[i], P[(i + 1) % len(P)]
            ip, iq = keep(p[1]), keep(q[1])
            if ip:
                out.append(p)
            if ip != iq:
                t = (zc - p[1]) / (q[1] - p[1])
                out.append((p[0] + (q[0] - p[0]) * t, zc))
        return out
    P = cut(poly, lambda z: z >= lo, lo)
    return cut(P, lambda z: z <= hi, hi) if len(P) >= 3 else P


def glint_y(k, x, y, z0, h, s=-1, w=0.07):
    """Two slanted highlight streaks on a glass plane at y (facing s * Y)."""
    for (dx, ww) in ((0.0, w), (0.16, w * 0.45)):
        a = x + dx
        k.poly([(a, y, z0), (a + ww, y, z0), (a + ww + h * 0.45, y, z0 + h), (a + h * 0.45, y, z0 + h)], 'glint', (0, s, 0))


# ================================================================ curtain wall
MEMW = 0.30                                  # diagrid member width (in the wall plane)
HW = MEMW / 2 * math.sqrt(1 + 1.5 ** 2)      # its half height measured vertically (slope 1.5)


def dia_slice(k, j):
    """1 m slice j (0..5) of a 6 m diagrid bay; room toward -Y, glass at y = 0.2, outside to +Y.
    Diagonal A climbs 1.5 m per metre left to right (bay x 0 -> 6, z 0 -> 9), B falls; they cross at bay x 3,
    z 4.5 (between slices 2 and 3); nodes at bay x 0 (z 0 and 9). B sits 4 cm behind A where they overlap."""
    k.begin()
    za, zb = 1.5 * j, H - 1.5 * j
    # odd slices sit 5 mm back and 6 mm up: a member running on into the next module never shares a plane with
    # itself there (the merged level's z-fight check would see the two caps as one overlapping face)
    o, dz = 0.005 * (j % 2), 0.006 * (j % 2)
    for (z0, slope, y0, y1) in ((za + dz, 1.5, -0.13 + o, 0.15 - o), (zb + dz, -1.5, -0.09 + o, 0.12 - o)):
        poly = [(-0.5, z0 - HW), (0.5, z0 + slope - HW), (0.5, z0 + slope + HW), (-0.5, z0 + HW)]
        poly = clip_z(poly, 0.0, H - 0.3)
        if len(poly) >= 3:
            k.prism(poly, y0, y1, 'dia', open_x=0.5)
    # node plates (half of each lands in the neighbouring slice)
    if j == 0:
        k.bx(-0.497, -0.17, -0.17, -0.13, 0.0, 0.5, 'brass', ink=False)
    if j == 5:
        k.bx(0.17, 0.497, -0.17, -0.13, 0.0, 0.5, 'brass', ink=False)
    if j == 2:
        k.bx(0.15, 0.497, -0.17, -0.13, 4.05, 4.95, 'brass')
    if j == 3:
        k.bx(-0.497, -0.15, -0.17, -0.13, 4.05, 4.95, 'brass')
    # floor beam at the mezzanine level (the deck abuts it), sill kick, header with a light cove
    k.bx(-0.5, 0.5, -0.5, 0.18, DECK - 0.4, DECK, 'dia')
    k.bx(-0.484, 0.484, -0.515, -0.5, DECK - 0.4, DECK - 0.33, 'brass', ink=False)   # (clear of the module round a corner)
    k.bx(-0.5, 0.5, -0.5, -0.36, 0.0, 0.14, 'granite', ink=False)
    k.bx(-0.5, 0.5, -0.5, 0.5, H - 0.4, H, 'dia')
    k.qz(-0.5, 0.5, -0.46, -0.3, H - 0.403, -1, 'glow')
    # guard rails on both floors (tube on stand-offs)
    for zr in (0.98, DECK + 0.98):
        k.bx(-0.5, 0.5, -0.36, -0.31, zr, zr + 0.05, 'brass', ink=False)
        k.bx(-0.02, 0.02, -0.31, -0.18, zr + 0.005, zr + 0.045, 'steelDark', ink=False)
    # glazing transoms (thin), glints on the glass
    for zt in (2.25, 6.75):
        k.bx(-0.5, 0.5, 0.16, 0.19, zt - 0.025, zt + 0.025, 'mullion', ink=False)
    gx = (-0.35, 0.05, -0.2, 0.15, -0.4, 0.0)[j]
    glint_y(k, gx, 0.195, 1.2 + 0.3 * (j % 3), 0.75)
    glint_y(k, gx + 0.1, 0.195, 5.0 + 0.25 * (j % 2), 0.7)
    # outside: slab edge with an upstand (seen when looking down past the glass)
    k.bx(-0.5, 0.5, 0.21, 0.5, -0.7, 0.09, 'stone2')
    return k


def dia_corner(k, rot):
    """Mega-column at a building corner (canonical: outside toward Blender -X and +Y). Its +X and -Y faces meet the
    neighbouring wall modules, so nothing stands proud of the cell there; a slab ledge runs round the outside."""
    k.begin(rot)
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'dia')
    k.bx(-0.5, 0.5, 0.5, 0.56, -0.7, 0.09, 'stone2', ink=False)
    k.bx(-0.56, -0.5, -0.5, 0.56, -0.7, 0.09, 'stone2', ink=False)
    return k


def gate_side(k):
    """Stone pier beside a gate (one-sided, room toward -Y): coursed limestone, brass reveal, a sconce."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone')
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.15, 'granite', ink=False)
    for z in (1.5, 3.0, 6.0, 7.5):
        k.qy(-0.5, 0.5, z - 0.01, z + 0.01, -0.503, -1, 'vein')
    k.bx(-0.5, 0.5, -0.53, -0.5, DECK - 0.4, DECK, 'stone2', ink=False)
    k.qy(-0.03, 0.03, 0.15, DECK - 0.4, -0.506, -1, 'brass')
    k.qy(-0.03, 0.03, DECK, H - 0.2, -0.506, -1, 'brass')
    k.bx(-0.1, 0.1, -0.56, -0.5, 5.6, 6.0, 'brass')                              # sconce over the gate portal's lintel
    k.bx(-0.14, 0.14, -0.7, -0.56, 5.7, 5.92, 'onyx')
    return k


def core(k):
    """Four-sided limestone block for wall junctions, thick blocks and lone columns (nothing proud of the cell)."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone')
    return k


def inner_wall(k, kind):
    """One-sided interior wall module (room toward -Y): limestone, walnut fins, an art banner or a video wall."""
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone')
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.15, 'granite', ink=False)
    k.bx(-0.5, 0.5, -0.53, -0.5, DECK - 0.4, DECK, 'stone2', ink=False)          # band where the deck meets it
    k.bx(-0.5, 0.5, -0.53, -0.5, H - 0.35, H, 'stone2', ink=False)               # cornice
    if kind == 'Stone':
        for z in (1.5, 3.0, 6.0, 7.5):
            k.qy(-0.5, 0.5, z - 0.01, z + 0.01, -0.503, -1, 'vein')
        k.qy(-0.5, -0.49, 0.15, DECK - 0.4, -0.506, -1, 'vein')
        k.qy(-0.5, -0.49, DECK, H - 0.35, -0.506, -1, 'vein')
    elif kind == 'Wood':
        k.qy(-0.5, 0.5, 0.15, DECK - 0.4, -0.503, -1, 'walnut2')
        k.qy(-0.5, 0.5, DECK, H - 0.35, -0.503, -1, 'walnut2')
        for x in (-0.375, -0.125, 0.125, 0.375):
            k.bx(x - 0.04, x + 0.04, -0.6, -0.503, 0.15, DECK - 0.4, 'walnut')
            k.bx(x - 0.04, x + 0.04, -0.6, -0.503, DECK, H - 0.35, 'walnut')
    elif kind == 'Art':
        for z in (1.5, 6.0, 7.5):
            k.qy(-0.5, 0.5, z - 0.01, z + 0.01, -0.503, -1, 'vein')
        k.bx(-0.42, 0.42, -0.56, -0.5, 1.4, 3.9, 'black')
        k.qy(-0.38, 0.38, 1.44, 3.86, -0.563, -1, 'paper')
        k.qy(-0.34, 0.1, 2.6, 3.8, -0.566, -1, 'sofaBlue')
        k.qy(0.14, 0.34, 2.2, 3.8, -0.566, -1, 'coral')
        k.qy(-0.34, 0.34, 1.5, 1.9, -0.566, -1, 'gold')
        k.qy(-0.2, 0.0, 2.0, 2.45, -0.566, -1, 'ink')
        k.qy(-0.1, 0.25, 2.9, 3.05, -0.569, -1, 'paper')
        k.bx(-0.1, 0.1, -0.62, -0.56, 4.0, 4.06, 'brass', ink=False)                # picture light
    else:   # video wall: five tiles a module, candlestick charts, tickers
        variant = kind[-1]
        k.bx(-0.5, 0.5, -0.56, -0.5, 0.75, 3.92, 'black')
        k.bx(-0.5, 0.5, -0.56, -0.5, 4.57, 8.45, 'black')
        tiles = [(0.8, 2.3), (2.35, 3.85), (4.6, 6.1), (6.15, 7.65), (7.7, 8.4)]
        for ti, (z0, z1) in enumerate(tiles):
            k.qy(-0.48, 0.48, z0 + 0.02, z1 - 0.02, -0.563, -1, 'night')
            seed = (ti * 7 + (3 if variant == 'B' else 0)) % 11
            if z1 - z0 < 1.0:                       # ticker strip
                for i in range(5):
                    x = -0.44 + i * 0.18
                    k.qy(x, x + 0.11, z0 + 0.2, z0 + 0.5, -0.566, -1, ('tickG', 'red', 'white', 'tickG', 'amber')[(i + seed) % 5])
                continue
            hgt = z1 - z0
            for i in range(7):
                x = -0.42 + i * 0.12
                up = ((i * 5 + seed) % 7) > 2
                lo = z0 + 0.2 + hgt * 0.5 * (((i * 3 + seed) % 5) / 5.0)
                hh = 0.12 + hgt * 0.06 * ((i + seed) % 4)
                k.qy(x, x + 0.06, lo, lo + hh, -0.566, -1, 'tickG' if up else 'red')
                k.qy(x + 0.025, x + 0.035, lo - 0.06, lo + hh + 0.06, -0.569, -1, 'tickG' if up else 'red')
            k.qy(-0.44, 0.44, z1 - 0.22, z1 - 0.16, -0.566, -1, 'screen')
    return k


# ================================================================ gate, bridge, ceiling, hatch, stand
def gate_frame(k):
    """Portal for the 3 m gates (both faces alike): graphite posts with brass and teal strips, a brass lintel and a
    stone panel up to the 9 m header with a brass spire emblem."""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.495, s * 2.1)
        k.bx(x0, x1, -0.56, 0.56, 0, 3.5, 'graphite')
        lx0, lx1 = srt(s * 1.6, s * 1.68)
        for f in (-1, 1):
            y0, y1 = srt(f * 0.56, f * 0.59)
            k.bx(lx0, lx1, y0, y1, 0.3, 3.2, 'teal', ink=False)
            k.bx(x0 + 0.02, x1 - 0.02, y0, y1, 0, 0.14, 'brass', ink=False)
    k.bx(-2.1, 2.1, -0.56, 0.56, 3.5, 4.1, 'brass')
    k.bx(-2.1, 2.1, -0.49, 0.49, 4.1, H - 0.005, 'stone')
    for f in (-1, 1):
        y = f * 0.493
        k.poly([(-0.55, y, 5.0), (0.55, y, 5.0), (0.0, y, 8.2)], 'brass', (0, f, 0))
        y2 = f * 0.496
        k.poly([(-0.32, y2, 5.25), (0.32, y2, 5.25), (0.0, y2, 7.4)], 'stone', (0, f, 0))
        for i, zz in enumerate((5.55, 6.05, 6.55)):
            w = 0.24 - i * 0.06
            k.qy(-w, w, zz, zz + 0.07, f * 0.499, f, 'brass')
        k.qy(-2.0, 2.0, 4.3, 4.42, f * 0.493, f, 'teal')
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
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.45, 'ink' if j % 2 else 'brass', ink=False)
    return k


def trail_wall(k, kind=''):
    """Sky-bridge side, 1 m along Blender Y, corridor toward +X: white steel upstand, mullion and header, glass
    between them braced with X ties, a brass handrail; half the bridge deck and roof slabs (to the corridor's centre
    line 2.25 m in) and an edge girder under the floor."""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, 0.25, 'dia')                                   # upstand
    k.bx(-0.08, 0.08, -0.5, -0.43, 0.25, H - 0.4, 'dia')                           # mullion
    k.bx(-0.25, 0.25, -0.5, 0.5, H - 0.4, H, 'dia')                                # header
    k.bx(-0.06, 0.06, -0.43, 0.5, DECK - 0.05, DECK + 0.05, 'dia', ink=False)      # mid transom
    k.bx(0.16, 0.21, -0.5, 0.5, 0.98, 1.03, 'brass', ink=False)                    # handrail
    k.bx(0.12, 0.16, -0.47, -0.43, 0.96, 1.0, 'steelDark', ink=False)
    for (z0, z1) in ((DECK + 0.05, H - 0.4),):
        k.beam((0.008, -0.43, z0 + 0.04), (0.008, 0.5, z1 - 0.04), 0.03, 'steel2', ink=False)
        k.beam((-0.008, 0.5, z0 + 0.04), (-0.008, -0.43, z1 - 0.04), 0.03, 'steel2', ink=False)
    for s in (-1, 1):                                                                # glints, both faces of the glass
        x = s * 0.03
        k.poly([(x, -0.25, 1.4), (x, -0.18, 1.4), (x, 0.12, 2.2), (x, 0.05, 2.2)], 'glint', (s, 0, 0))
        k.poly([(x, 0.05, 5.4), (x, 0.11, 5.4), (x, 0.38, 6.1), (x, 0.32, 6.1)], 'glint', (s, 0, 0))
    k.bx(-0.25, 2.25, -0.5, 0.5, -0.55, -0.004, 'stone2')                          # deck slab (half)
    k.bx(-0.32, -0.25, -0.5, 0.5, -1.1, 0.25, 'dia')                               # edge girder
    k.bx(-0.25, 2.25, -0.5, 0.5, H + 0.02, H + 0.36, 'cap')                        # roof slab (half)
    k.bx(-0.32, -0.25, -0.5, 0.5, H - 0.4, H + 0.42, 'dia')                        # roof edge
    if kind == 'Plant':          # a slim green wall on the mullion (corridor side)
        k.bx(0.08, 0.16, -0.42, 0.42, 1.25, 3.4, 'brass')
        k.qx(-0.38, 0.38, 1.29, 3.36, 0.163, 1, 'leaf2')
        for i, (y, z, h) in enumerate(((-0.3, 1.35, 0.5), (-0.05, 1.6, 0.7), (0.22, 1.4, 0.45), (-0.2, 2.3, 0.6), (0.15, 2.2, 0.8), (-0.1, 2.9, 0.4), (0.25, 2.85, 0.45))):
            k.qx(y - 0.1, y + 0.1, z, z + h, 0.166 + 0.003 * (i % 3), 1, 'leafL' if i % 2 else 'leaf')
        for (y, z) in ((-0.25, 1.9), (0.1, 2.75), (0.28, 1.95)):
            k.qx(y - 0.03, y + 0.03, z, z + 0.06, 0.175, 1, 'blossom')
    elif kind == 'Sign':         # wayfinding panel on the mullion
        k.bx(0.08, 0.13, -0.47, -0.05, 2.0, 2.6, 'night')
        k.poly([(0.133, -0.4, 2.3), (0.133, -0.25, 2.45), (0.133, -0.25, 2.15)], 'teal', (1, 0, 0))
        k.qx(-0.24, -0.08, 2.27, 2.33, 0.133, 1, 'teal')
        k.qx(-0.42, -0.1, 2.08, 2.12, 0.133, 1, 'white')
    return k


def ceil_strip(k):
    """Bridge ceiling light: a slim linear LED along the corridor, hung at the ceiling plane."""
    k.begin()
    k.bx(-0.07, 0.07, -1.1, 1.1, -0.09, -0.004, 'cap', ink=False)
    k.qz(-0.05, 0.05, -1.05, 1.05, -0.093, -1, 'glow')
    return k


def hatch(k):
    """Exit: the express-elevator pod: a round pad with chevrons inside a brass-ribbed glass capsule."""
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.25, 0.06, 'steel2', seg=20)
    k.cyl(0, 0, 0.06, 1.0, 1.0, 0.012, 'granite', seg=20, ink=False)
    for i in range(3):
        y = -0.6 + i * 0.45
        k.poly([(-0.55, y, 0.075), (0, y + 0.32, 0.075), (0, y + 0.46, 0.075), (-0.55, y + 0.14, 0.075)], 'teal', (0, 0, 1))
        k.poly([(0, y + 0.32, 0.076), (0.55, y, 0.076), (0.55, y + 0.14, 0.076), (0, y + 0.46, 0.076)], 'teal', (0, 0, 1))
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        if abs(math.sin(a) + 1) < 0.5:     # leave the south side open (the way in)
            continue
        ca, sa = math.cos(a), math.sin(a)
        pts = [(1.22, 0.06), (1.24, 1.2), (1.18, 2.1), (0.95, 2.75), (0.55, 3.1)]
        for j in range(len(pts) - 1):
            k.beam((ca * pts[j][0], sa * pts[j][0], pts[j][1]), (ca * pts[j + 1][0], sa * pts[j + 1][0], pts[j + 1][1]), 0.07, 'brass')
    k.cyl(0, 0, 3.05, 0.6, 0.2, 0.3, 'brass', seg=12)
    k.cyl(0, 0, 3.35, 0.06, 0.02, 0.6, 'brass', seg=6, ink=False)
    k.cyl(0, 0, 3.0, 0.5, 0.5, 0.05, 'glow', seg=12, ink=False)
    return k


def stand(k):
    """Weapon stand: a limestone plinth with a brass top and a teal light line."""
    k.begin()
    k.bx(-0.45, 0.45, -0.42, 0.42, 0, 0.9, 'stone')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0.9, 0.96, 'brass')
    k.qy(-0.4, 0.4, 0.12, 0.16, -0.423, -1, 'teal')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0, 0.1, 'granite', ink=False)
    k.col(-0.47, 0.47, -0.44, 0.44, 0, 0.96)
    return k


# ================================================================ circulation
def rail(k, y0, y1):
    """Glass balustrade (tinted glass, glints) on a white shoe with a brass handrail; one-cell module pieces."""
    k.bx(-0.05, 0.05, y0, y1, 0, 0.1, 'dia', ink=False)
    k.bx(-0.012, 0.012, y0, y1, 0.1, 0.97, 'skyglass', ink=False)
    k.bx(-0.035, 0.035, y0, y1, 0.97, 1.04, 'brass', ink=False)
    for s in (-1, 1):
        x = s * 0.015
        ym = (y0 + y1) / 2
        k.poly([(x, ym - 0.12, 0.35), (x, ym - 0.07, 0.35), (x, ym + 0.08, 0.75), (x, ym + 0.03, 0.75)], 'glint', (s, 0, 0))


def rails(k):
    k.begin()
    rail(k, -0.5, -0.068)                     # half module: stops at the post in the cell centre
    k.col(-0.09, 0.09, -0.5, 0.0, 0, 1.1)
    k.finish('Rail')
    k.begin()
    rail(k, -0.5, 0.5)
    k.col(-0.09, 0.09, -0.5, 0.5, 0, 1.1)
    k.finish('RailFull')
    k.begin()
    k.bx(-0.065, 0.065, -0.065, 0.065, 0, 1.06, 'dia')
    k.bx(-0.08, 0.08, -0.08, 0.08, 1.06, 1.1, 'brass', ink=False)
    k.finish('RailPost')


def columns(k):
    """White steel columns on the mezzanine edge: under the slab (0 - 4.1) and over it (deck - ceiling)."""
    for name, h in (('Column_Lo', DECK - 0.4), ('Column_Hi', H - DECK)):
        k.begin()
        k.bx(-0.4, 0.4, -0.4, 0.4, 0, 0.12, 'granite', ink=False)
        k.cyl(0, 0, 0.12, 0.34, 0.3, 0.2, 'brass', seg=12)
        k.cyl(0, 0, 0.32, 0.27, 0.27, h - 0.32 - 0.5, 'dia', seg=12, caps=False)
        k.cyl(0, 0, 1.4, 0.285, 0.285, 0.06, 'brass', seg=12, ink=False, caps=False)
        k.cyl(0, 0, h - 0.5, 0.27, 0.42, 0.42, 'dia', seg=12)
        k.bx(-0.44, 0.44, -0.44, 0.44, h - 0.08, h - 0.004, 'brass', ink=False)
        k.col(-0.36, 0.36, -0.36, 0.36, 0, h)
        k.finish(name)


def escalator(k):
    """2 x 10 rising toward +Y (game north): landing, 14 steps of 0.32 m, top landing at 4.5 m; walkable stair
    boxes and side walls; white truss cladding, tinted glass balustrades, black handrails."""
    k.begin()
    n, y0, y1 = 14, -5.0 + 0.9, 5.0 - 1.0
    run, rise = (y1 - y0) / n, DECK / n
    k.bx(-0.8, 0.8, -5.0, y0, 0.0, 0.05, 'steel', ink=False)
    k.col(-0.84, 0.84, -5.0, y0, 0, 0.05, True)
    for kk in range(n):
        a, top = y0 + kk * run, (kk + 1) * rise
        k.bx(-0.8, 0.8, a, a + run, top - rise - 0.01 if kk else 0.0, top, 'graphite', ink=False)
        k.bx(-0.78, 0.78, a + 0.004, a + 0.06, top, top + 0.004, 'amber', ink=False)
        k.col(-0.84, 0.84, a, a + run, 0, top, True)
    k.bx(-0.8, 0.8, y1, 5.0, DECK - 0.4, DECK, 'steel')
    k.col(-0.84, 0.84, y1, 5.0, 0, DECK, True)
    k.bx(-0.79, 0.79, y1 - 0.6, 4.99, 0.0, DECK - 0.4, 'steelDark', ink=False)
    for sx in (-1, 1):
        a, b = srt(sx * 0.8, sx * 1.0)
        prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, DECK + 0.12), (y1, DECK + 0.12), (y0 - 0.1, 0.17), (-5.0, 0.17)]
        k.prism_y(prof, a, b, 'dia')
        gx0, gx1 = sx * 0.88 - 0.015, sx * 0.88 + 0.015
        gl = [(-4.7, 0.17), (y0 - 0.1, 0.17), (y1, DECK + 0.12), (4.7, DECK + 0.12), (4.7, DECK + 1.0), (y1 + 0.05, DECK + 1.0), (y0 - 0.05, 1.05), (-4.7, 1.05)]
        k.prism_y(gl, min(gx0, gx1), max(gx0, gx1), 'skyglass', ink=False)
        hr = [(-4.75, 1.02), (y0 - 0.05, 1.02), (y1 + 0.05, DECK + 0.97), (4.75, DECK + 0.97), (4.75, DECK + 1.09), (y1 + 0.06, DECK + 1.09), (y0 - 0.06, 1.14), (-4.75, 1.14)]
        k.prism_y(hr, sx * 0.88 - 0.05, sx * 0.88 + 0.05, 'black')
        trim = [(-4.95, 0.11), (y0 - 0.12, 0.11), (y1 + 0.02, DECK + 0.06), (4.95, DECK + 0.06), (4.95, DECK), (y1 - 0.01, DECK), (y0 - 0.15, 0.05), (-4.95, 0.05)]
        xo = max(a, b) if sx > 0 else min(a, b)
        k.prism_y(trim, xo if sx > 0 else xo - 0.004, xo + 0.004 if sx > 0 else xo, 'brass', ink=False)
        for t in (0.25, 0.6):
            yy = y0 + (y1 - y0) * t
            zz = 0.17 + (DECK - 0.05) * t
            xg = sx * 0.899
            k.poly([(xg, yy, zz + 0.15), (xg, yy + 0.35, zz + 0.15 + 0.35 * DECK / (y1 - y0)), (xg, yy + 0.55, zz + 0.75), (xg, yy + 0.2, zz + 0.6)], 'glint', (sx, 0, 0))
        for kk in range(n + 2):
            if kk == 0:
                a2, b2, top = -5.0, y0, 0.05
            elif kk == n + 1:
                a2, b2, top = y1, 5.0, DECK
            else:
                a2, b2, top = y0 + (kk - 1) * run, y0 + kk * run, kk * rise
            k.col(sx * 0.92 - 0.08, sx * 0.92 + 0.08, a2, b2, 0, top + 1.06)
    return k


def grand_stair(k):
    """4 x 10 limestone stair rising toward +Y to the 4.5 m deck: 14 steps with brass nosings, white stringers,
    tinted glass balustrades with brass handrails. Same step line as the escalator (walkable stair boxes)."""
    k.begin()
    n, y0, y1 = 14, -5.0 + 0.9, 5.0 - 1.0
    run, rise = (y1 - y0) / n, DECK / n
    k.bx(-1.8, 1.8, -5.0, y0, 0.0, 0.03, 'marble', ink=False)
    k.col(-1.85, 1.85, -5.0, y0, 0, 0.03, True)
    for kk in range(n):
        a, top = y0 + kk * run, (kk + 1) * rise
        k.bx(-1.8, 1.8, a, a + run, 0.0, top, 'stone' if kk % 2 else 'marble')
        k.bx(-1.75, 1.75, a - 0.012, a + 0.05, top - 0.04, top + 0.004, 'brass', ink=False)
        k.col(-1.85, 1.85, a, a + run, 0, top, True)
    k.bx(-1.8, 1.8, y1, 5.0, DECK - 0.4, DECK, 'marble')
    k.bx(-1.8, 1.8, y1, 4.99, 0.0, DECK - 0.4, 'stone2', ink=False)
    k.col(-1.85, 1.85, y1, 5.0, 0, DECK, True)
    for sx in (-1, 1):
        a, b = srt(sx * 1.8, sx * 2.0)
        prof = [(-5.0, 0.0), (5.0, 0.0), (5.0, DECK + 0.1), (y1, DECK + 0.1), (y0 - 0.05, 0.25), (-5.0, 0.25)]
        k.prism_y(prof, a, b, 'dia')
        gx = sx * 1.9
        gl = [(-4.8, 0.25), (y0 - 0.05, 0.25), (y1, DECK + 0.1), (4.8, DECK + 0.1), (4.8, DECK + 1.0), (y1 + 0.05, DECK + 1.0), (y0, 1.15), (-4.8, 1.15)]
        k.prism_y(gl, gx - 0.015, gx + 0.015, 'skyglass', ink=False)
        hr = [(-4.85, 1.12), (y0, 1.12), (y1 + 0.05, DECK + 0.97), (4.85, DECK + 0.97), (4.85, DECK + 1.05), (y1 + 0.06, DECK + 1.05), (y0 - 0.01, 1.2), (-4.85, 1.2)]
        k.prism_y(hr, gx - 0.04, gx + 0.04, 'brass')
        xg = sx * 1.921
        for t in (0.2, 0.55, 0.85):
            yy = y0 + (y1 - y0) * t
            zz = 0.3 + (DECK - 0.05) * t
            k.poly([(xg, yy, zz + 0.12), (xg, yy + 0.3, zz + 0.12 + 0.3 * DECK / (y1 - y0)), (xg, yy + 0.5, zz + 0.7), (xg, yy + 0.2, zz + 0.55)], 'glint', (sx, 0, 0))
        for kk in range(n + 2):
            if kk == 0:
                a2, b2, top = -5.0, y0, 0.03
            elif kk == n + 1:
                a2, b2, top = y1, 5.0, DECK
            else:
                a2, b2, top = y0 + (kk - 1) * run, y0 + kk * run, kk * rise
            k.col(sx * 1.92 - 0.1, sx * 1.92 + 0.1, a2, b2, 0, top + 1.1)
    return k


# ================================================================ ceiling and roof (layer 9)
def coffer(k):
    """4 x 4 ceiling coffer hung at the ceiling plane: perimeter beams, a brass-edged light panel."""
    k.begin()
    for s in (-1, 1):
        a, b = srt(s * 2.0, s * 1.86)
        k.bx(a, b, -2.0, 2.0, -0.3, -0.004, 'cap', ink=False)
        k.bx(-1.86, 1.86, a, b, -0.3, -0.004, 'cap', ink=False)
    k.bx(-0.95, 0.95, -0.95, 0.95, -0.06, -0.004, 'brass', ink=False)
    k.qz(-0.88, 0.88, -0.88, 0.88, -0.063, -1, 'glow')
    k.qz(-0.88, 0.88, -0.015, 0.015, -0.066, -1, 'cap')
    k.qz(-0.015, 0.015, -0.88, 0.88, -0.069, -1, 'cap')
    return k


def downlight(k):
    k.begin()
    k.cyl(0, 0, -0.035, 0.16, 0.16, 0.031, 'brass', seg=10, ink=False)
    k.cyl(0, 0, -0.041, 0.11, 0.11, 0.006, 'glow', seg=10, ink=False)
    return k


def under_light(k):
    """Downlight under the mezzanine slab (the piece stands on the deck top; the slab underside is 0.4 m below)."""
    k.begin()
    k.cyl(0, 0, -0.43, 0.14, 0.14, 0.026, 'brass', seg=10, ink=False)
    k.cyl(0, 0, -0.436, 0.1, 0.1, 0.006, 'glow', seg=10, ink=False)
    return k


def ring(k, r, z, n, t, c, ink=True):
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        k.beam((math.cos(a0) * r, math.sin(a0) * r, z), (math.cos(a1) * r, math.sin(a1) * r, z), t, c, ink=ink)


def halo(k):
    """Landmark: suspended brass halo chandelier (three rings at different heights, glowing inner bands,
    crystal drops, cables to the ceiling), 8 x 8, hung from the ceiling plane."""
    k.begin()
    rings = ((3.3, -3.1, 28), (2.3, -2.3, 22), (1.35, -3.9, 16))
    for (r, z, n) in rings:
        ring(k, r, z, n, 0.14, 'brass')
        ring(k, r - 0.13, z - 0.03, n, 0.05, 'glow', ink=False)
        for i in range(0, n, 2):
            a = (i + 0.5) / n * math.pi * 2
            x, y = math.cos(a) * r, math.sin(a) * r
            k.beam((x, y, z - 0.07), (x, y, z - 0.42), 0.012, 'steel', ink=False)
            k.sph(x, y, z - 0.5, 0.075, 'frost', seg=(4, 2), scale=(1, 1, 1.6))
        for i in range(4):
            a = (i + 0.25) / 4 * math.pi * 2
            k.beam((math.cos(a) * r, math.sin(a) * r, z + 0.07), (math.cos(a) * r * 0.97, math.sin(a) * r * 0.97, -0.01), 0.014, 'steelDark', ink=False)
    k.cyl(0, 0, -0.18, 0.5, 0.5, 0.176, 'brass', seg=12)
    k.cyl(0, 0, -4.5, 0.18, 0.05, 0.5, 'gold', seg=8)
    k.beam((0, 0, -0.18), (0, 0, -4.0), 0.02, 'steelDark', ink=False)
    return k


def ticker(k):
    """Landmark: a hanging LED ticker ring over the trading floor (16 facets, 1.3 m tall, outer and inner faces
    showing scrolling quotes and charts), 8 x 8, hung from the ceiling plane."""
    k.begin()
    n, r, z0, z1 = 16, 3.2, -3.4, -2.1
    for i in range(n):
        a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
        p0 = (math.cos(a0) * r, math.sin(a0) * r)
        p1 = (math.cos(a1) * r, math.sin(a1) * r)
        q0 = (math.cos(a0) * (r - 0.18), math.sin(a0) * (r - 0.18))
        q1 = (math.cos(a1) * (r - 0.18), math.sin(a1) * (r - 0.18))
        bm = k.m.bm
        P = k.m.parent
        vs = [bm.verts.new(P @ Vector(v)) for v in ((p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1),
                                                     (q0[0], q0[1], z0), (q1[0], q1[1], z0), (q1[0], q1[1], z1), (q0[0], q0[1], z1))]
        fs = [bm.faces.new((vs[0], vs[1], vs[2], vs[3])), bm.faces.new((vs[5], vs[4], vs[7], vs[6])),
              bm.faces.new((vs[3], vs[2], vs[6], vs[7])), bm.faces.new((vs[4], vs[5], vs[1], vs[0]))]
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        k.m._finish(vs, 'night', False)
        # quote strips on the outer face and the inner face
        mid = (a0 + a1) / 2
        for side, rr in ((1, r + 0.004), (-1, r - 0.184)):
            nx, ny = math.cos(mid), math.sin(mid)
            tx, ty = -ny, nx
            L = 2 * r * math.sin(math.pi / n) * 0.42
            for j in range(3):
                c = ('tickG', 'red', 'amber', 'white', 'tickG', 'screen')[(i + j * 2 + (side > 0)) % 6]
                u0, u1 = -L + j * (2 * L / 3) + 0.03, -L + (j + 1) * (2 * L / 3) - 0.03
                zz0, zz1 = (z0 + 0.15, z0 + 0.5) if j % 2 == 0 else (z0 + 0.62, z0 + 1.08)
                pts = [(nx * rr + tx * u0, ny * rr + ty * u0, zz0), (nx * rr + tx * u1, ny * rr + ty * u1, zz0),
                       (nx * rr + tx * u1, ny * rr + ty * u1, zz1), (nx * rr + tx * u0, ny * rr + ty * u0, zz1)]
                k.poly(pts, c, (nx * side, ny * side, 0))
    ring(k, r - 0.09, z1 + 0.06, n, 0.12, 'brass')
    ring(k, r - 0.09, z0 - 0.06, n, 0.12, 'brass')
    for i in range(4):
        a = (i + 0.5) / 4 * math.pi * 2
        k.beam((math.cos(a) * (r - 0.09), math.sin(a) * (r - 0.09), z1 + 0.12), (math.cos(a) * (r - 0.09), math.sin(a) * (r - 0.09), -0.01), 0.02, 'steelDark', ink=False)
    return k


def glass_roof(k):
    """8 x 8 glazed pyramid standing on the ceiling plane (Sky Garden): white steel edge beams, hip ribs and purlin
    rings up to an apex vent, open glazing with a few glints on the panes (seen from below)."""
    k.begin()
    A, E = 2.3, 4.0
    for s in (-1, 1):
        a, b = srt(s * E, s * (E - 0.12))
        k.bx(a, b, -E, E, -0.2, 0.14, 'dia')
        k.bx(-(E - 0.12), E - 0.12, a, b, -0.2, 0.14, 'dia')
    for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        k.beam((x * (E - 0.1), y * (E - 0.1), 0.14), (x * 0.25, y * 0.25, A - 0.08), 0.12, 'dia')
    for f in (0.36, 0.68):                                    # purlin rings (thin)
        r, z = E * (1 - f), 0.14 + f * (A - 0.22)
        for i, (x0, y0, x1, y1) in enumerate(((-r, -r, r, -r), (r, -r, r, r), (r, r, -r, r), (-r, r, -r, -r))):
            zz = z + 0.008 * (i % 2)
            k.beam((x0, y0, zz), (x1, y1, zz), 0.06, 'steel', ink=False)
    for (x, y) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        k.beam((x * (E - 0.1), y * (E - 0.1), 0.14), (x * 0.25, y * 0.25, A - 0.08), 0.05, 'steel', ink=False)
    k.cyl(0, 0, A - 0.15, 0.4, 0.22, 0.4, 'dia', seg=8)
    for (ax, ay) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        tx, ty = -ay, ax
        for (u, w) in ((-1.9, 0.22), (-1.45, 0.1)):
            d0, d1 = 3.3, 1.8
            p = lambda d, uu, z: (ax * d + tx * uu, ay * d + ty * uu, z)
            z0 = 0.14 + (E - d0) / E * (A - 0.14) + 0.05
            z1 = 0.14 + (E - d1) / E * (A - 0.14) + 0.05
            k.poly([p(d0, u, z0), p(d0, u + w, z0), p(d1, u + w + 0.6, z1), p(d1, u + 0.6, z1)], 'glint', (-ax * 0.5, -ay * 0.5, -0.85))
    return k


# ================================================================ floor inlays (layer 0)
def inlay_star(k):
    """8 x 8 compass star medallion: limestone disc, marble star, brass inner star, teal centre."""
    k.begin()
    def disc(r, z, c, n=16):
        k.poly([(math.cos(i / n * math.pi * 2) * r, math.sin(i / n * math.pi * 2) * r, z) for i in range(n)], c, (0, 0, 1))
    disc(3.8, 0.014, 'stone2')
    disc(3.55, 0.017, 'granite')
    def star(ro, ri, z, c, n=8, ph=0.0):
        for i in range(n):
            a = i / n * math.pi * 2 + ph
            b0, b1 = a - math.pi / n, a + math.pi / n
            k.poly([(0, 0, z), (math.cos(b0) * ri, math.sin(b0) * ri, z), (math.cos(a) * ro, math.sin(a) * ro, z), (math.cos(b1) * ri, math.sin(b1) * ri, z)], c, (0, 0, 1))
    star(3.4, 1.2, 0.02, 'marble')
    star(2.2, 0.8, 0.023, 'brass', ph=math.pi / 8)
    disc(0.6, 0.026, 'sofaBlue', 12)
    disc(0.3, 0.029, 'gold', 10)
    return k


def inlay_band(k):
    """1 m border band (runs along the atrium's rail line): granite with a brass inlay line."""
    k.begin()
    k.qz(-0.5, 0.5, -0.4, 0.4, 0.014, 1, 'granite')
    k.qz(-0.5, 0.5, -0.05, 0.05, 0.017, 1, 'brass')
    return k


def lawn(k):
    k.begin()
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.014, 1, 'lawn')
    pts = ((-1.4, -1.1), (-0.6, 1.3), (0.4, -0.2), (1.3, 0.9), (1.1, -1.4))
    for i, (x, y) in enumerate(pts):
        for j in range(2):
            a = j * 2.1 + i
            k.beam((x, y, 0.014), (x + math.cos(a) * 0.05, y + math.sin(a) * 0.05, 0.13 + 0.03 * (j % 2)), 0.03, 'leafL' if j % 2 else 'leaf', ink=False)
        if i % 2 == 0:
            k.sph(x + 0.2, y + 0.15, 0.06, 0.04, 'white' if i % 4 else 'blossom', seg=(4, 2), ink=False)
    for (x, y, c) in ((-0.8, -0.4, 'white'), (0.9, 1.6, 'gold'), (-1.6, 1.5, 'white'), (1.7, -0.6, 'blossom')):
        k.qz(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.017, 1, c)
    return k


def decking(k):
    k.begin()
    k.bx(-1.996, 1.996, -1.996, 1.996, 0.0, 0.03, 'oak2', ink=False)
    for i in range(1, 16):
        x = -2.0 + i * 0.25
        k.qz(x - 0.008, x + 0.008, -2.0, 2.0, 0.033, 1, 'walnut')
    for (x, y) in ((-1.875, -1.0), (-1.375, 0.7), (-0.875, -0.3), (-0.375, 1.2), (0.125, -1.4), (0.625, 0.2), (1.125, -0.8), (1.625, 1.0)):
        k.qz(x - 0.1, x + 0.1, y - 0.006, y + 0.006, 0.036, 1, 'walnut2')
    return k


def carpet(k):
    k.begin()
    k.qz(-2.0, 2.0, -2.0, 2.0, 0.014, 1, 'fabricBlue')
    for s in (-1, 1):
        a, b = srt(s * 1.9, s * 1.8)
        k.qz(a, b, -1.9, 1.9, 0.017, 1, 'sofaBlue')
        k.qz(-1.8, 1.8, a, b, 0.017, 1, 'sofaBlue')
    k.poly([(0, -0.9, 0.02), (0.9, 0, 0.02), (0, 0.9, 0.02), (-0.9, 0, 0.02)], 'cap', (0, 0, 1))
    k.poly([(0, -0.6, 0.023), (0.6, 0, 0.023), (0, 0.6, 0.023), (-0.6, 0, 0.023)], 'fabricBlue', (0, 0, 1))
    return k


# ================================================================ lobby props
def turnstile(k):
    """Security gate pedestal (glass flaps toward its neighbours in the run, a teal reader)."""
    k.begin()
    k.bx(-0.11, 0.11, -0.42, 0.42, 0, 1.0, 'graphite')
    k.bx(-0.13, 0.13, -0.44, 0.44, 1.0, 1.04, 'brass')
    k.qz(-0.08, 0.08, -0.3, -0.12, 1.043, 1, 'teal')
    for s in (-1, 1):
        a, b = srt(s * 0.11, s * 0.4)
        k.bx(a, b, -0.015, 0.015, 0.45, 0.95, 'skyglass', ink=False)
        k.bx(a + 0.004, b - 0.004, -0.02, 0.02, 0.93, 0.96, 'brass', ink=False)
    k.qy(-0.09, 0.09, 0.1, 0.9, -0.423, -1, 'teal')
    k.col(-0.42, 0.42, -0.44, 0.44, 0, 1.04)
    return k


def totem(k):
    k.begin()
    k.bx(-0.3, 0.3, -0.16, 0.16, 0, 0.12, 'brass')
    k.bx(-0.26, 0.26, -0.11, 0.11, 0.12, 2.1, 'black')
    for f in (-1, 1):
        y = f * 0.113
        k.qy(-0.22, 0.22, 0.5, 1.95, y, f, 'night')
        for i, (c, h) in enumerate((('screen', 0.12), ('white', 0.06), ('teal', 0.08), ('white', 0.06), ('gold', 0.1))):
            z = 1.75 - i * 0.24
            k.qy(-0.18, -0.18 + 0.36 * (0.5 + 0.1 * i), z, z + h, f * 0.116, f, c)
    k.col(-0.3, 0.3, -0.16, 0.16, 0, 2.1)
    return k


def planter(k, kind):
    k.begin()
    if kind == 'A':     # limestone cube with a clipped topiary ball
        k.bx(-0.4, 0.4, -0.4, 0.4, 0, 0.7, 'stone')
        k.bx(-0.42, 0.42, -0.42, 0.42, 0.7, 0.76, 'stone2')
        k.qz(-0.36, 0.36, -0.36, 0.36, 0.763, 1, 'soil')
        k.cyl(0, 0, 0.76, 0.04, 0.04, 0.3, 'trunk', seg=5, ink=False)
        k.sph(0, 0, 1.25, 0.42, 'leaf2', seg=(8, 6))
        k.col(-0.42, 0.42, -0.42, 0.42, 0, 0.76)
    else:               # tall white drum with ornamental grasses
        k.cyl(0, 0, 0, 0.36, 0.3, 0.85, 'pot', seg=12)
        k.cyl(0, 0, 0.85, 0.3, 0.3, 0.004, 'soil', seg=12, ink=False)
        for i in range(9):
            a = i / 9 * math.pi * 2
            k.beam((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.85), (math.cos(a) * 0.42, math.sin(a) * 0.42, 1.55 + 0.12 * (i % 3)), 0.05, 'leafL' if i % 2 else 'leaf')
        k.col(-0.36, 0.36, -0.36, 0.36, 0, 0.85)
    return k


def olive_planter(k):
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.6, 'stone')
    k.bx(-0.94, 0.94, -0.94, 0.94, 0.6, 0.66, 'brass', ink=False)
    k.qz(-0.85, 0.85, -0.85, 0.85, 0.663, 1, 'soil')
    trunk = [(0, 0, 0.66), (0.12, -0.05, 1.3), (-0.05, 0.08, 1.9), (0.1, 0.0, 2.4)]
    for i in range(len(trunk) - 1):
        k.beam(trunk[i], trunk[i + 1], 0.14 - i * 0.025, 'bark')
    for (x, y, z, r, c) in ((0.1, 0.0, 2.75, 0.7, 'leafL'), (-0.45, 0.2, 2.45, 0.5, 'leaf'), (0.5, -0.25, 2.4, 0.48, 'leaf'),
                            (0.2, 0.45, 2.3, 0.42, 'leafL'), (-0.25, -0.4, 2.6, 0.45, 'leafL')):
        k.sph(x, y, z, r, c, seg=(7, 5), scale=(1, 1, 0.75))
    k.col(-0.94, 0.94, -0.94, 0.94, 0, 0.66)
    k.col(-0.2, 0.2, -0.2, 0.2, 0.66, 2.2)
    return k


def bench(k):
    """2 x 1: travertine slab bench with a walnut seat on brass feet."""
    k.begin()
    for s in (-1, 1):
        a, b = srt(s * 0.7, s * 0.86)
        k.bx(a, b, -0.24, 0.24, 0, 0.36, 'stone2')
    k.bx(-0.95, 0.95, -0.26, 0.26, 0.36, 0.42, 'stone')
    k.bx(-0.9, 0.9, -0.22, 0.22, 0.42, 0.46, 'walnut', ink=False)
    for i in range(1, 9):
        x = -0.9 + i * 0.2
        k.qz(x - 0.005, x + 0.005, -0.22, 0.22, 0.463, 1, 'walnut2')
    k.col(-0.95, 0.95, -0.26, 0.26, 0, 0.46)
    return k


def spire_model(k):
    """Landmark: the architects' model of the Spire on a limestone plinth: a twisting diagrid tower with a needle,
    two lower towers and the gold sky-bridges between them."""
    k.begin()
    k.bx(-1.6, 1.6, -1.6, 1.6, 0, 0.85, 'stone')
    k.bx(-1.66, 1.66, -1.66, 1.66, 0.85, 0.92, 'brass')
    k.bx(-1.66, 1.66, -1.66, 1.66, 0, 0.1, 'granite', ink=False)
    for f in (-1, 1):
        k.qy(-0.6, 0.6, 0.4, 0.55, f * 1.603, f, 'brass')
    k.bx(-1.5, 1.5, -1.5, 1.5, 0.92, 0.96, 'night', ink=False)                       # site base
    for i in range(16):
        s = 1.0 - i * 0.028
        k.push(0.25, 0.1, i * 5.5, z=0.96 + i * 0.2)
        k.bx(-0.45 * s, 0.45 * s, -0.45 * s, 0.45 * s, 0, 0.16, 'dia' if i % 2 else 'skyglass', ink=(i % 4 == 0))
        k.pop()
    k.cyl(0.25, 0.1, 0.96 + 16 * 0.2, 0.18, 0.04, 1.0, 'dia', seg=6)
    k.cyl(0.25, 0.1, 0.96 + 16 * 0.2 + 1.0, 0.03, 0.01, 0.5, 'gold', seg=4, ink=False)
    for (x, y, h, c) in ((-0.95, -0.7, 1.4, 'skyglass'), (-0.8, 0.95, 1.9, 'dia')):
        k.bx(x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0.96, 0.96 + h, c)
        k.bx(x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.96 + h, 0.96 + h + 0.05, 'twWin', ink=False)
    k.bx(-0.65, -0.1, -0.6, -0.48, 1.9, 2.0, 'gold')
    k.bx(-0.9, -0.78, 0.1, 0.63, 2.4, 2.5, 'gold')
    k.col(-1.66, 1.66, -1.66, 1.66, 0, 0.92)
    k.col(-0.5, 1.0, -0.65, 0.85, 0.92, 4.6)
    return k


# ================================================================ garden
def tree(k, kind):
    """3 x 3: a round limestone planter with a cherry (blossom) or a maple; canopy from 3 m up."""
    k.begin()
    k.cyl(0, 0, 0, 1.35, 1.3, 0.62, 'stone', seg=14)
    k.cyl(0, 0, 0.62, 1.38, 1.38, 0.06, 'stone2', seg=14)
    k.cyl(0, 0, 0.68, 1.22, 1.22, 0.004, 'soil', seg=14, ink=False)
    for (x, y) in ((0.6, 0.5), (-0.7, 0.3), (0.1, -0.8)):
        k.sph(x, y, 0.72, 0.2, 'leaf2', seg=(5, 3), scale=(1, 1, 0.6))
    k.cyl(0, 0, 0.684, 0.24, 0.17, 2.3, 'bark', seg=7, caps=False)
    if kind == 'Cherry':
        br = ((1.3, 0.4, 3.6), (-1.1, 0.8, 3.8), (-0.3, -1.3, 3.5), (0.5, 1.1, 4.3))
        blobs = ((0, 0, 4.9, 1.45, 'blossom'), (1.3, 0.5, 4.2, 1.0, 'blossom'), (-1.2, 0.8, 4.4, 1.05, 'coral'),
                 (-0.4, -1.3, 4.1, 0.95, 'blossom'), (0.6, -0.6, 5.3, 0.9, 'paper'), (-0.7, 0.1, 5.4, 0.85, 'blossom'),
                 (0.7, 1.2, 4.9, 0.8, 'coral'))
    else:
        br = ((1.2, -0.5, 3.4), (-1.2, -0.4, 3.6), (0.2, 1.3, 3.5), (-0.4, 0.9, 4.4))
        blobs = ((0, 0, 5.1, 1.5, 'leaf'), (1.3, -0.5, 4.2, 1.05, 'leafL'), (-1.3, -0.4, 4.4, 1.1, 'leaf'),
                 (0.2, 1.35, 4.3, 1.0, 'leafL'), (0.52, 0.47, 5.63, 0.93, 'leaf2'), (-0.7, 0.6, 5.3, 0.9, 'leafL'),
                 (-0.2, -1.1, 5.0, 0.85, 'leaf2'))
    for (x, y, z) in br:
        k.beam((0, 0, 2.6), (x, y, z), 0.12, 'bark')
    for (x, y, z, r, c) in blobs:
        k.sph(x, y, z, r, c, seg=(8, 6), scale=(1, 1, 0.82))
    k.col(-1.3, 1.3, -1.3, 1.3, 0, 0.68)
    k.col(-0.28, 0.28, -0.28, 0.28, 0.68, 3.0)
    return k


def hedge(k, kind):
    k.begin()
    k.bx(-0.5, 0.5, -0.42, 0.42, 0, 0.5, 'stone')
    k.bx(-0.5, 0.5, -0.45, 0.45, 0.5, 0.56, 'stone2', ink=False)
    k.bx(-0.5, 0.5, -0.36, 0.36, 0.56, 1.1, 'leaf2', ink=False)
    k.bx(-0.5, 0.5, -0.3, 0.3, 1.1, 1.16, 'leaf', ink=False)
    if kind == 'B':
        for (x, y) in ((-0.3, -0.37), (0.1, 0.37), (0.35, -0.37), (-0.1, 0.37)):
            k.sph(x, y, 0.85, 0.08, 'blossom', seg=(4, 3), ink=False)
    return k


def pool(k):
    """4 x 4 reflecting pool: limestone rim, water with ripples and lily pads, a brass bubbler."""
    k.begin()
    for s in (-1, 1):
        a, b = srt(s * 2.0, s * 1.65)
        k.bx(a, b, -2.0, 2.0, 0, 0.45, 'stone')
        k.bx(-1.65, 1.65, a, b, 0, 0.45, 'stone')
    k.bx(-1.65, 1.65, -1.65, 1.65, 0, 0.3, 'sofaBlue', ink=False)
    k.qz(-1.65, 1.65, -1.65, 1.65, 0.303, 1, 'water')
    for (x, y, w) in ((-0.9, -0.6, 0.5), (0.3, 0.9, 0.6), (0.6, -1.0, 0.4), (-0.6, 1.2, 0.35)):
        k.qz(x - w, x + w, y - 0.02, y + 0.02, 0.306, 1, 'waterL')
    for (x, y, r) in ((-1.0, 0.7, 0.22), (-0.7, 1.0, 0.16), (1.0, -0.3, 0.2), (1.2, 0.1, 0.14), (0.2, -1.2, 0.18)):
        k.cyl(x, y, 0.306, r, r, 0.012, 'leaf', seg=7, ink=False)
    k.sph(-1.0, 0.7, 0.33, 0.06, 'blossom', seg=(4, 3), ink=False)
    k.cyl(0, 0, 0.3, 0.14, 0.1, 0.12, 'brass', seg=8)
    k.cyl(0, 0, 0.42, 0.05, 0.02, 0.3, 'waterL', seg=6, ink=False)
    k.col(-2.0, 2.0, -2.0, 2.0, 0, 0.45)
    return k


def pergola(k):
    """6 x 4 timber pergola: six posts, twin beams, slatted roof at 3.2 m with vines, a long bench underneath."""
    k.begin()
    for x in (-2.7, 0.0, 2.7):
        for y in (-1.7, 1.7):
            k.bx(x - 0.11, x + 0.11, y - 0.11, y + 0.11, 0, 3.0, 'walnut')
            k.bx(x - 0.16, x + 0.16, y - 0.16, y + 0.16, 0, 0.2, 'stone2', ink=False)
            k.col(x - 0.14, x + 0.14, y - 0.14, y + 0.14, 0, 3.0)
    for y in (-1.7, 1.7):
        k.bx(-3.0, 3.0, y - 0.09, y + 0.09, 3.0, 3.28, 'walnut')
    for i in range(13):
        x = -2.88 + i * 0.48
        k.bx(x - 0.04, x + 0.04, -2.0, 2.0, 3.28, 3.38, 'oak')
    for (x, y, z, r) in ((-2.7, -1.7, 2.6, 0.32), (-2.4, -1.75, 3.25, 0.38), (2.7, 1.7, 2.3, 0.3), (2.3, 1.6, 3.3, 0.42),
                         (0.0, 1.75, 3.35, 0.3), (-1.0, -1.3, 3.45, 0.32), (1.2, 0.4, 3.45, 0.28)):
        k.sph(x, y, z, r, 'leaf' if r > 0.31 else 'leafL', seg=(6, 4))
    for (x, y, z) in ((-2.4, -1.75, 3.0), (2.3, 1.6, 3.0), (-1.0, -1.3, 3.2)):
        k.sph(x + 0.2, y, z, 0.07, 'blossom', seg=(4, 3), ink=False)
    # bench along the middle
    for x in (-1.9, 0.0, 1.9):
        k.bx(x - 0.15, x + 0.15, -0.2, 0.2, 0, 0.4, 'stone2')
    k.bx(-2.3, 2.3, -0.25, 0.25, 0.4, 0.47, 'oak')
    k.col(-2.3, 2.3, -0.25, 0.25, 0, 0.47)
    return k


def lamp(k):
    k.begin()
    k.cyl(0, 0, 0, 0.16, 0.14, 0.14, 'graphite', seg=8)
    k.cyl(0, 0, 0.14, 0.05, 0.04, 3.0, 'graphite', seg=6, ink=False)
    k.bx(-0.16, 0.16, -0.16, 0.16, 3.1, 3.42, 'glow')
    k.bx(-0.2, 0.2, -0.2, 0.2, 3.42, 3.5, 'graphite')
    k.cyl(0, 0, 3.5, 0.12, 0.02, 0.15, 'graphite', seg=6, ink=False)
    k.col(-0.16, 0.16, -0.16, 0.16, 0, 3.5)
    return k


def boulder(k):
    k.begin()
    k.sph(-0.1, 0.05, 0.25, 0.48, 'granite', seg=(7, 5), scale=(1.0, 0.85, 0.75))
    k.sph(0.25, -0.15, 0.2, 0.32, 'stone2', seg=(6, 4), scale=(1.0, 1.0, 0.8))
    k.sph(-0.3, -0.3, 0.12, 0.2, 'granite', seg=(5, 4))
    k.col(-0.45, 0.45, -0.45, 0.45, 0, 0.6)
    return k


# ================================================================ trading floor
def tmon(k, x, y, deg, z0, v):
    """Trading monitor: the office monitor with candlestick charts on the screen (screen faces local -Y)."""
    k.push(x, y, deg, z0)
    k.bx(-0.03, 0.03, 0.03, 0.07, 0.0, 0.16, 'graphite2', ink=False)
    k.bx(-0.27, 0.27, 0.0, 0.03, 0.12, 0.45, 'black')
    k.qy(-0.25, 0.25, 0.14, 0.43, -0.003, -1, 'night')
    for i in range(6):
        xx = -0.22 + i * 0.075
        up = (i * 3 + v) % 5 > 1
        lo = 0.18 + 0.03 * ((i * 7 + v) % 5)
        k.qy(xx, xx + 0.04, lo, lo + 0.05 + 0.02 * ((i + v) % 3), -0.006, -1, 'tickG' if up else 'red')
    k.qy(-0.23, 0.23, 0.39, 0.41, -0.006, -1, 'screen' if v % 2 else 'amber')
    k.pop()


def trade_desk(k, v):
    """4 x 2 double-sided trading desk: white top on graphite legs, a monitor spine with three screens per seat
    (two seats a side), keyboards, chairs."""
    k.begin()
    k.bx(-1.95, 1.95, -0.8, 0.8, 0.72, 0.76, 'cap')
    for x in (-1.85, 0.0, 1.85):
        k.bx(x - 0.04, x + 0.04, -0.7, 0.7, 0, 0.72, 'graphite', ink=False)
    k.bx(-1.9, 1.9, -0.05, 0.05, 0.764, 0.9, 'graphite')
    for f, deg in ((-1, 0), (1, 180)):
        for sx in (-0.95, 0.95):
            for (dx, rot) in ((-0.52, -18), (0.0, 0), (0.52, 18)):
                tmon(k, sx + dx, f * 0.12, deg + rot * (1 if f < 0 else -1), 0.76, int((sx + 2) * 3 + dx * 4 + v * 5 + f) % 7)
            O.keyboard(k, sx, f * 0.45, deg, 0.76)
            O.task_chair(k, sx + 0.1 * f, f * 1.15, deg + 180 + (8 if sx > 0 else -6), 'chair' if v == 0 else 'sofaBlue')
        O.mug(k, -1.6, f * 0.5, 0.76, 'white' if f < 0 else 'coral')
    k.col(-1.95, 1.95, -0.8, 0.8, 0, 0.76)
    k.col(-1.9, 1.9, -0.3, 0.3, 0.76, 1.25)
    return k


def bolt_sculpture(k):
    """Landmark: a giant chrome lightning bolt on a granite plinth with a brass ring (3 x 3)."""
    k.begin()
    k.cyl(0, 0, 0, 1.3, 1.3, 0.55, 'granite', seg=16)
    k.cyl(0, 0, 0.55, 1.34, 1.34, 0.06, 'brass', seg=16)
    k.cyl(0, 0, 0.61, 1.15, 1.15, 0.004, 'stone2', seg=16, ink=False)
    pts = [(-0.2, 0.616), (0.35, 0.616), (0.15, 2.0), (0.75, 2.0), (-0.1, 5.4), (0.05, 3.3), (-0.55, 3.3)]
    k.prism(pts, -0.22, 0.22, 'steel')
    inner = [(-0.02, 1.0), (0.18, 1.0), (0.04, 2.25), (0.44, 2.25), (0.0, 4.2), (-0.05, 3.05), (-0.3, 3.05)]
    for f in (-1, 1):
        k.poly([(x, f * 0.223, z) for (x, z) in inner], 'gold', (0, f, 0))
    k.col(-1.3, 1.3, -1.3, 1.3, 0, 0.61)
    k.col(-0.6, 0.75, -0.25, 0.25, 0.61, 5.2)
    return k


# ================================================================ skyline (from the theme's tower table)
def read_skyline():
    src = open(os.path.join(HERE, '..', 'src', 'data', 'themes', 'spire.js'), encoding='utf-8').read()
    m = re.search(r'/\*SKYLINE-BEGIN\*/(.*?)/\*SKYLINE-END\*/', src, re.S)
    txt = re.sub(r"'", '"', m.group(1))
    txt = re.sub(r'(\w+)\s*:', r'"\1":', txt)
    base = float(re.search(r'var BASE = (-?[\d.]+)', src).group(1))
    return json.loads(txt), base


def strips(k, x0, x1, y0, y1, z0, z1, win, n_front=None):
    """Vertical window strips on all four faces (one quad per strip, whatever the height)."""
    w, d = x1 - x0, y1 - y0
    nf = n_front or max(2, int(w / 2.6))
    ns = max(2, int(d / 2.6))
    for i in range(nf):
        x = x0 + w * (i + 0.5) / nf
        k.qy(x - 0.45, x + 0.45, z0 + 1, z1 - 0.8, y0 - 0.05, -1, win)
        k.qy(x - 0.45, x + 0.45, z0 + 1, z1 - 0.8, y1 + 0.05, 1, win)
    for i in range(ns):
        y = y0 + d * (i + 0.5) / ns
        k.qx(y - 0.45, y + 0.45, z0 + 1, z1 - 0.8, x0 - 0.05, -1, win)
        k.qx(y - 0.45, y + 0.45, z0 + 1, z1 - 0.8, x1 + 0.05, 1, win)


def bands(k, x0, x1, y0, y1, z0, z1, step, win):
    """Horizontal window ribbons on all four faces."""
    z = z0 + step * 0.4
    while z + step * 0.45 < z1 - 0.5:
        k.qy(x0 + 0.4, x1 - 0.4, z, z + step * 0.45, y0 - 0.05, -1, win)
        k.qy(x0 + 0.4, x1 - 0.4, z, z + step * 0.45, y1 + 0.05, 1, win)
        k.qx(y0 + 0.4, y1 - 0.4, z, z + step * 0.45, x0 - 0.05, -1, win)
        k.qx(y0 + 0.4, y1 - 0.4, z, z + step * 0.45, x1 + 0.05, 1, win)
        z += step


def sky_tower(k, t, base):
    x, fy, w, d, col, wcol, top, style = t
    c, wc = HEX2NAME[col.upper()], HEX2NAME[wcol.upper()]
    x0, x1, y0, y1 = x - w / 2, x + w / 2, fy, fy + d
    cx, cy = x, fy + d / 2

    def body(a0, a1, b0, b1, z0, z1, cc=c):
        k.bx(a0, a1, b0, b1, z0, z1, cc)

    def cornice(a0, a1, b0, b1, z, cc='twWhite'):
        k.bx(a0 - 0.4, a1 + 0.4, b0 - 0.4, b1 + 0.4, z, z + 0.9, cc)

    cornice(x0, x1, y0, y1, base, 'stone2')                      # band where the shaft below meets the piece
    if style == 'deco':
        t1, t2 = top - 26, top - 11
        body(x0, x1, y0, y1, base + 0.9, t1)
        strips(k, x0, x1, y0, y1, base + 0.9, t1, wc)
        body(x0 + 3, x1 - 3, y0 + 3, y1 - 3, t1, t2)
        strips(k, x0 + 3, x1 - 3, y0 + 3, y1 - 3, t1, t2, wc)
        body(x0 + 6, x1 - 6, y0 + 6, y1 - 6, t2, top, 'twWhite')
        bands(k, x0 + 6, x1 - 6, y0 + 6, y1 - 6, t2, top, 3.0, 'gold')
        k.cyl(cx, cy, top, 2.6, 0.4, 7, 'twWhite', seg=8)
        k.cyl(cx, cy, top + 7, 0.35, 0.05, 14, 'twWhite', seg=6, ink=False)
    elif style == 'needle':
        body(x0, x1, y0, y1, base + 0.9, top)
        bands(k, x0, x1, y0, y1, max(base + 0.9, top - 90), top, 4.2, wc)
        strips(k, x0, x1, y0, y1, base + 0.9, top - 90, wc)
        k.bx(x0 + 2, x1 - 2, y0 + 2, y1 - 2, top, top + 5, 'twWhite')
        k.cyl(cx, cy, top + 5, 0.8, 0.15, 26, 'twWhite', seg=6)
        k.sph(cx, cy, top + 31.5, 0.6, 'red', seg=(5, 3), ink=False)
    elif style == 'helipad':
        body(x0, x1, y0, y1, base + 0.9, top)
        bands(k, x0, x1, y0, y1, top - 60, top, 3.6, wc)
        strips(k, x0, x1, y0, y1, base + 0.9, top - 60, wc)
        k.bx(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, top, top + 1.1, 'twWhite')
        k.cyl(cx, cy, top + 1.1, min(w, d) * 0.36, min(w, d) * 0.36, 0.25, 'twDark', seg=16)
        k.cyl(cx, cy, top + 1.35, min(w, d) * 0.32, min(w, d) * 0.32, 0.01, 'amber', seg=16, ink=False)
        k.cyl(cx, cy, top + 1.36, min(w, d) * 0.29, min(w, d) * 0.29, 0.01, 'twDark', seg=16, ink=False)
        s = min(w, d) * 0.12
        k.qz(cx - s, cx - s * 0.6, cy - s, cy + s, top + 1.38, 1, 'white')
        k.qz(cx + s * 0.6, cx + s, cy - s, cy + s, top + 1.38, 1, 'white')
        k.qz(cx - s * 0.6, cx + s * 0.6, cy - s * 0.15, cy + s * 0.15, top + 1.38, 1, 'white')
        k.bx(x0 + 1, x0 + 6, y1 - 7, y1 - 1, top + 1.1, top + 3.5, 'steel2')
    elif style == 'twist':
        tl = top - 64
        body(x0, x1, y0, y1, base + 0.9, tl)
        strips(k, x0, x1, y0, y1, base + 0.9, tl, wc)
        sz = min(w, d) * 0.92
        for i in range(16):
            k.push(cx, cy, i * 4.0, z=tl + i * 4.0)
            k.bx(-sz / 2, sz / 2, -sz / 2, sz / 2, 0, 3.3, c)
            k.bx(-sz / 2 + 0.3, sz / 2 - 0.3, -sz / 2 + 0.3, sz / 2 - 0.3, 3.3, 4.0, wc, ink=False)
            k.pop()
        k.push(cx, cy, 64.0)
        k.bx(-sz / 2 + 2, sz / 2 - 2, -sz / 2 + 2, sz / 2 - 2, top, top + 3, 'twWhite')
        k.pop()
    elif style == 'prism':
        tl = top - 18
        body(x0, x1, y0, y1, base + 0.9, tl)
        bands(k, x0, x1, y0, y1, tl - 50, tl, 4.0, wc)
        strips(k, x0, x1, y0, y1, base + 0.9, tl - 50, wc)
        k.prism([(x0 + 0.06, tl), (x1 - 0.06, tl), (x1 - 0.06, top - 6), (x0 + 0.06, top)], y0 + 0.06, y1 - 0.06, c)
        k.prism([(x0 + 0.5, top - 0.2), (x1 - 0.5, top - 6.2), (x1 - 0.5, top - 5.6), (x0 + 0.5, top + 0.4)], y0 + 0.5, y1 - 0.5, 'twWhite', ink=False)
    elif style == 'crane':
        body(x0, x1, y0, y1, base + 0.9, top)
        bands(k, x0, x1, y0, y1, top - 40, top, 3.6, wc)
        strips(k, x0, x1, y0, y1, base + 0.9, top - 40, wc)
        for i in range(3):                                         # open frame of the floors being built
            z = top + 3.6 * (i + 1)
            k.bx(x0, x1, y0, y1, z - 0.3, z, 'twWhite')
        for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), (cx, y0), (cx, y1)):
            k.bx(px - 0.4, px + 0.4, py - 0.4, py + 0.4, top, top + 10.6, 'steel2')
        mx, my = x0 + 4, cy
        k.bx(mx - 1.0, mx + 1.0, my - 1.0, my + 1.0, top, top + 44, 'amber')
        for j in range(10):
            z = top + 2 + j * 4.2
            k.beam((mx - 1.05, my - 1.05, z), (mx + 1.05, my - 1.05, z + 4.0), 0.12, 'graphite', ink=False)
        k.bx(mx - 14, mx + 34, my - 0.7, my + 0.7, top + 44, top + 45.6, 'amber')
        k.bx(mx - 13, mx - 7, my - 1.5, my + 1.5, top + 41.5, top + 44, 'graphite')
        k.bx(mx + 1.0, mx + 3.2, my - 1.2, my + 1.2, top + 41.6, top + 44, 'twWhite')
        k.beam((mx, my, top + 49), (mx + 34, my, top + 45.6), 0.15, 'graphite', ink=False)
        k.beam((mx, my + 0.2, top + 49), (mx - 14, my + 0.2, top + 45.6), 0.15, 'graphite', ink=False)
        k.bx(mx - 0.3, mx + 0.3, my - 0.3, my + 0.3, top + 45.6, top + 49.5, 'amber')
        k.beam((mx + 24, my + 0.4, top + 44), (mx + 24, my + 0.4, top + 20), 0.06, 'graphite', ink=False)
        k.bx(mx + 23, mx + 25, my - 0.6, my + 1.4, top + 18.5, top + 20, 'twSand')
    elif style == 'obelisk':
        tl = top - 80
        body(x0, x1, y0, y1, base + 0.9, tl)
        strips(k, x0, x1, y0, y1, base + 0.9, tl, wc)
        r0 = min(w, d) / 2 * math.sqrt(2)
        k.cyl(cx, cy, tl, r0, r0 * 0.45, 80, c, seg=4, rot=(0, 0, 45))
        k.cyl(cx, cy, top, r0 * 0.45, 0.2, 14, 'twWhite', seg=4, rot=(0, 0, 45))
        for i in range(8):
            z = tl + 6 + i * 9.0
            r = r0 * (1 - 0.55 * (z - tl) / 80) + 0.06
            k.cyl(cx, cy, z, r, r - 0.02, 0.8, wc, seg=4, rot=(0, 0, 45), ink=False)
        k.cyl(cx, cy, top + 14, 0.15, 0.04, 12, 'twWhite', seg=4, ink=False)
    elif style == 'garden':
        body(x0, x1, y0, y1, base + 0.9, top)
        bands(k, x0, x1, y0, y1, top - 60, top, 3.8, wc)
        strips(k, x0, x1, y0, y1, base + 0.9, top - 60, wc)
        k.bx(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, top, top + 1.2, 'twWhite')
        k.qz(x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5, top + 0.4, 1, 'lawn')
        k.bx(cx - 4, cx + 4, cy - 2, cy + 2, top + 0.4, top + 0.6, 'water')
        for i, (dx, dy) in enumerate(((-8, -6), (-4, 7), (6, -7), (8, 5), (0, 8), (-9, 3))):
            if abs(dx) < w / 2 - 1.5 and abs(dy) < d / 2 - 1.5:
                k.cyl(cx + dx, cy + dy, top + 0.4, 0.2, 0.15, 2.0, 'bark', seg=5, ink=False)
                k.sph(cx + dx, cy + dy, top + 3.2, 1.6, 'leaf' if i % 2 else 'leafL', seg=(6, 4))
    else:   # slab
        body(x0, x1, y0, y1, base + 0.9, top)
        strips(k, x0, x1, y0, y1, base + 0.9, top, wc, max(3, int(w / 1.8)))
        k.bx(x0 + 3, x1 - 3, y0 + 3, y1 - 3, top, top + 6, 'steel2')
        k.bx(x0 + 1, x0 + 3, y0 + 1, y0 + 3, top, top + 9, 'twWhite')


def backdrop(k, rows, name, base):
    k.begin()
    for t in rows[name]:
        sky_tower(k, t, base)
    return k


# ================================================================ build
CORNERS = (('NW', 0), ('NE', -90), ('SE', 180), ('SW', 90))


def build_kit_spire(ao):
    pal = Palette(FAM)
    k = SKit(pal)
    # walls
    for j in range(6):
        dia_slice(k, j).finish('Dia_%d' % j)
    for tag, rot in CORNERS:
        dia_corner(k, rot).finish('DiaCorner_%s' % tag)
    gate_side(k).finish('GateSide', ao=ao)
    core(k).finish('Core', ao=ao)
    for kind in ('Stone', 'Wood', 'Art', 'ScreenA', 'ScreenB'):
        inner_wall(k, kind).finish('Wall_%s' % kind, ao=ao)
    # gate, bridge, ceiling, hatch, stand
    gate_frame(k).finish('GateFrame', ao=ao)
    shutter = gate_shutter(k).finish('GateShutter')
    m = Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    trail_wall(k).finish('TrailWall', ao=ao)
    trail_wall(k, 'Plant').finish('TrailWall_Plant', ao=ao)
    trail_wall(k, 'Sign').finish('TrailWall_Sign', ao=ao)
    ceil_strip(k).finish('CeilStrip')
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    # circulation
    rails(k)
    columns(k)
    escalator(k).finish('Escalator', ao=ao)
    grand_stair(k).finish('GrandStair', ao=ao)
    # ceiling / roof
    coffer(k).finish('Coffer')
    downlight(k).finish('Downlight')
    under_light(k).finish('UnderLight')
    halo(k).finish('Landmark_Halo')
    ticker(k).finish('Landmark_Ticker')
    glass_roof(k).finish('GlassRoof')
    # floor inlays
    inlay_star(k).finish('Inlay_Star')
    inlay_band(k).finish('Inlay_Band')
    lawn(k).finish('Lawn')
    decking(k).finish('Decking')
    carpet(k).finish('Carpet')
    # lobby
    O.reception(k).finish('Landmark_Reception', ao=ao)
    for v in ('A', 'B'):
        O.lounge(k, v).finish('Lounge_%s' % v, ao=ao)
    spire_model(k).finish('Landmark_Model', ao=ao)
    turnstile(k).finish('Turnstile', ao=ao)
    totem(k).finish('Totem', ao=ao)
    planter(k, 'A').finish('Planter', ao=ao)
    planter(k, 'B').finish('Planter_B', ao=ao)
    olive_planter(k).finish('OlivePlanter', ao=ao)
    bench(k).finish('Bench', ao=ao)
    for kind, nm in (('fig', 'Plant_Fig'), ('palm', 'Plant_Palm'), ('snake', 'Plant_Snake')):
        O.plant(k, kind).finish(nm, ao=ao)
    # garden
    tree(k, 'Cherry').finish('Tree_Cherry', ao=ao)
    tree(k, 'Maple').finish('Tree_Maple', ao=ao)
    hedge(k, 'A').finish('Hedge_A', ao=ao)
    hedge(k, 'B').finish('Hedge_B', ao=ao)
    pool(k).finish('Pool', ao=ao)
    pergola(k).finish('Pergola', ao=ao)
    lamp(k).finish('Lamp', ao=ao)
    boulder(k).finish('Boulder', ao=ao)
    # trading floor
    trade_desk(k, 0).finish('TradeDesk_A', ao=ao)
    trade_desk(k, 1).finish('TradeDesk_B', ao=ao)
    O.meeting(k, 'A').finish('Boardroom', ao=ao)
    O.exec_desk(k).finish('Exec', ao=ao)
    bolt_sculpture(k).finish('Landmark_Bolt', ao=ao)
    # skyline
    rows, base = read_skyline()
    for name in sorted(rows):
        backdrop(k, rows, name, base).finish(name)
    total = 0
    for n in sorted(k.tris):
        total += k.tris[n]
        print('%-34s %6d tris' % (n, k.tris[n]))
    print('kit-spire total (one of each): %d tris' % total)
    export(FAM)


FAMILY = 'kit-spire'
BUILD = build_kit_spire
