"""INKBOLT kit-academy ("Chalkstone Academy", a school: classrooms, science labs, the cafeteria, the gymnasium and the
courtyard): palette and modelling helpers shared by ac_struct.py (walls and wall art, doors, gate, trail, ceilings,
roofs, floors), ac_rooms.py (classroom, lab, office, library and cafeteria furniture), ac_gym.py (gym and courtyard)
-- the family module is fam_kit_academy.py.

Look: a bright, well-kept public school -- warm cream painted block walls with a slate-blue and gold band (the school
colours), a dark rubber cove base, recessed slate / teal / red lockers, cream vinyl tile floors, white acoustic tile
ceilings with light panels at 4 m, double-height rooms (lobby, cafeteria, gym) under 8 m roofs; outside, red brick
with stone bands and two storeys of windows.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (the piece's front), Blender +X = game +X.
  * Wall faces are flat painted quads on a cell face: front (_F) at y = -0.5 facing -Y; the same face built turned
    180 / 90 / -90 degrees gives the back (_K, y = +0.5), right (_R, x = +0.5) and left (_L, x = -0.5) faces the theme's
    chooser stacks in one cell (a 1-cell wall seen from both sides, a wall end, a corner).
  * Walls are WALL_H (8 m) tall; ceiling pieces hang from their origin (the 4 m tile layer, the 8 m roof layer).
  * Run pieces (rails) are modelled along Blender Y (the half module runs from the origin toward -Y); [n, 1] prefabs
    are modelled along Blender X (the placer turns them to their line of cells).
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: walkable (stair treads, the stage, the bleacher tiers, the tiers).
  * Stairs rise RISE (0.16 m) per TREAD (0.25 m), bleachers 0.16 m per 0.28 m, the stage steps 1/6 m per 0.25 m, the
    tiers 0.2 m per 0.62 m: at most 0.33 m between neighbouring 0.5 m nav cells (the robots step 0.4 m).
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text  # noqa: F401
from kit_base import rz  # noqa: F401
from fr_base import FKit
from kit_util import ring_pts  # noqa: F401

FAM = 'kit-academy'
PFX = 'KIT_ACADEMY_'
ib_lib.GLB[FAM] = 'fps-kit-academy.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    # walls (8 - 19)
    ('wallC', '#EFE5CD'), ('wallU', '#F5EEDC'), ('slate', '#3E5C86'), ('gold', '#E9B23B'), ('cove', '#4F4741'),
    ('joint', '#DCCFB1'), ('brick', '#B5583F'), ('brick2', '#93432F'), ('mortar', '#D8C4AE'), ('stone', '#CFC7B6'),
    ('stoneD', '#9D9587'), ('trimW', '#F7F4EC'),
    # floors (20 - 27)
    ('vct', '#E4DAC3'), ('vctD', '#CBBE9F'), ('maple', '#DDA76A'), ('mapleD', '#BC8546'), ('conc', '#C2BCB0'),
    ('concD', '#9C968A'), ('grass', '#7CAB4D'), ('grass2', '#5C8B39'),
    # wood, laminate (28 - 31)
    ('woodL', '#D9B37D'), ('wood', '#B9874F'), ('woodD', '#7C5433'), ('lam', '#EAE0CA'),
    # chairs and plastics: the theme repaints chA per copy (32 - 37)
    ('chA', '#2F6FB5'), ('chB', '#E36A2A'), ('chC', '#3F9F5A'), ('chD', '#D9443F'), ('chE', '#F0C031'),
    ('chF', '#7A5CC4'),
    # metals (38 - 41)
    ('steel', '#9CA5AF'), ('steelD', '#5C6570'), ('chrome', '#D7DDE3'), ('black', '#26272C'),
    # lockers, boards (42 - 47)
    ('lockT', '#2E9A92'), ('lockR', '#B8473D'), ('board', '#F7F8F3'), ('chalk', '#305C46'), ('cork', '#C69C64'),
    ('navy', '#22324F'),
    # glass, screens, light (48 - 54)
    ('glass', '#86BFD2'), ('glassL', '#CDEBF3'), ('screen', '#1C2D42'), ('scrB', '#43A3EA'), ('lightW', '#FFF5D6'),
    ('sky', '#9DD3F1'), ('skyL', '#DDF0F9'),
    # green, fabric, food, bone (55 - 63)
    ('leaf', '#4F9B44'), ('leafD', '#2E6C36'), ('bark', '#6E4E37'), ('curtain', '#8E2F3A'), ('mat', '#2F5FA6'),
    ('food', '#C9472F'), ('foodY', '#F1C34C'), ('bone', '#EFE6D1'), ('exitG', '#2DB35E'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]
CHAIRS = ['chA', 'chB', 'chC', 'chD', 'chE', 'chF']

WALL_H = 8.0     # walls and the double-height roofs
CEIL = 4.0       # ceiling tiles of the 4 m rooms; the library deck top
RISE, TREAD = 0.16, 0.25
DOOR_H = 2.5     # doorway head (wall.passage is solid above)


def cell(name):
    return NAMES.index(name)


class AKit(FKit):
    """FKit (kit_base.Kit + walkable boxes, text) with culled boxes and a few school shapes."""

    def bx(self, x0, x1, y0, y1, z0, z1, c, ink=True, bevel=False, cull=''):
        """box; cull: faces never seen, dropped (t b f k l r = +Z -Z -Y +Y -X +X in the box's own frame)"""
        if not cull:
            return super().bx(x0, x1, y0, y1, z0, z1, c, ink=ink, bevel=bevel)
        assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
        m = self.m
        M = m.parent @ Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1.0))
        verts = bmesh.ops.create_cube(m.bm, size=1.0, matrix=M)['verts']
        R = m.parent.to_3x3()
        dirs = {'t': (0, 0, 1), 'b': (0, 0, -1), 'f': (0, -1, 0), 'k': (0, 1, 0), 'l': (-1, 0, 0), 'r': (1, 0, 0)}
        kill = []
        for f in {f for v in verts for f in v.link_faces}:
            f.normal_update()
            for ch in cull:
                d = (R @ Vector(dirs[ch])).normalized()
                if f.normal.dot(d) > 0.99:
                    kill.append(f)
        bmesh.ops.delete(m.bm, geom=kill, context='FACES_ONLY')
        loose = [e for e in {e for v in verts if v.is_valid for e in v.link_edges} if not e.link_faces]
        if loose:
            bmesh.ops.delete(m.bm, geom=loose, context='EDGES')
        verts = [v for v in verts if v.is_valid]
        lone = [v for v in verts if not v.link_edges]
        if lone:
            bmesh.ops.delete(m.bm, geom=lone, context='VERTS')
            verts = [v for v in verts if v.is_valid]
        m._finish(verts, c, bevel)
        self._mark(ink)

    # painted quads (flat, no outline): front (-Y), back (+Y), up (+Z), down (-Z), left (-X), right (+X)
    def fq(self, x0, x1, y, z0, z1, c):
        self.qy(x0, x1, z0, z1, y, -1, c)

    def bq(self, x0, x1, y, z0, z1, c):
        self.qy(x0, x1, z0, z1, y, 1, c)

    def uq(self, x0, x1, y0, y1, z, c):
        self.qz(x0, x1, y0, y1, z, 1, c)

    def dq(self, x0, x1, y0, y1, z, c):
        self.qz(x0, x1, y0, y1, z, -1, c)

    def lq(self, x, y0, y1, z0, z1, c):
        self.qx(y0, y1, z0, z1, x, -1, c)

    def rq(self, x, y0, y1, z0, z1, c):
        self.qx(y0, y1, z0, z1, x, 1, c)

    def ring(self, x, y, z, r0, r1, c, seg=24, a0=0.0, a1=2 * math.pi):
        """flat annulus (or arc band) facing up"""
        for i in range(seg):
            p, q = a0 + (a1 - a0) * i / seg, a0 + (a1 - a0) * (i + 1) / seg
            self.poly([(x + math.cos(p) * r0, y + math.sin(p) * r0, z), (x + math.cos(p) * r1, y + math.sin(p) * r1, z),
                       (x + math.cos(q) * r1, y + math.sin(q) * r1, z), (x + math.cos(q) * r0, y + math.sin(q) * r0, z)], c, (0, 0, 1))

    def legs4(self, x0, x1, y0, y1, z1, c, t=0.04, ink=True):
        for x in (x0, x1 - t):
            for y in (y0, y1 - t):
                self.bx(x, x + t, y, y + t, 0.0, z1, c, ink=ink, cull='b')

    def chair(self, x, y, deg, c='chA', seat=0.45):
        """a classroom chair (moulded shell on a steel frame), facing -Y before the turn (its back toward +Y)"""
        self.push(x, y, deg)
        for sx in (-0.19, 0.17):
            self.bx(sx, sx + 0.02, -0.19, 0.19, 0.0, seat, 'steelD', ink=False, cull='bt')
        self.bx(-0.21, 0.21, -0.21, 0.19, seat, seat + 0.04, c, cull='')
        self.bx(-0.2, 0.2, 0.19, 0.23, seat + 0.06, seat + 0.42, c)
        self.pop()

    def stool(self, x, y, h=0.62, c='steelD', top='black'):
        self.cyl(x, y, 0.0, 0.035, 0.035, h - 0.04, c, seg=4, ink=False, caps=False)
        self.cyl(x, y, 0.0, 0.15, 0.15, 0.03, c, seg=5, ink=False, caps=False)
        self.cyl(x, y, h - 0.04, 0.17, 0.17, 0.05, top, seg=6)

    def book_row(self, rnd, x0, x1, y0, y1, z0, h=(0.2, 0.3), colors=('chA', 'chD', 'chC', 'chE', 'navy', 'woodD', 'chF', 'paper'), face=-1, gap=0.0):
        """books on a shelf: two or three blocks of mixed height, the spines painted on the face toward face (-1: -Y)"""
        n = 3 if x1 - x0 > 1.2 else 2
        cuts = [x0] + sorted(rnd.uniform(x0 + 0.25, x1 - 0.25) for _ in range(n - 1)) + [x1]
        yf = y0 if face < 0 else y1
        for i in range(n):
            a, b = cuts[i] + 0.01, cuts[i + 1] - 0.01
            hh = rnd.uniform(*h)
            self.bx(a, b, y0, y1, z0, z0 + hh, 'paper', cull='bk' if face < 0 else 'bf')
            x = a
            while x < b - 0.04:
                w = min(b - x, rnd.uniform(0.1, 0.22))
                top = z0 + hh * rnd.uniform(0.8, 0.97)
                if face < 0:
                    self.fq(x + 0.003, x + w - 0.003, yf - 0.003, z0 + 0.01, top, rnd.choice(colors))
                else:
                    self.bq(x + 0.003, x + w - 0.003, yf + 0.003, z0 + 0.01, top, rnd.choice(colors))
                x += w
        return
        """(old) books standing on a shelf as a few blocks of mixed height"""
        x = x0
        cull = 'bk' if face < 0 else 'bf'
        while x < x1 - 0.06:
            w = min(x1 - x, rnd.uniform(0.35, 0.7))
            hh = rnd.uniform(*h)
            c = rnd.choice(colors)
            dy = rnd.uniform(0.0, 0.04)
            self.bx(x + 0.004, x + w - 0.004, y0 + (dy if face < 0 else 0), y1 - (dy if face > 0 else 0), z0, z0 + hh, c, cull=cull)
            x += w + gap
