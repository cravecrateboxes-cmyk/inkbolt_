"""INKBOLT kit-metro ("Metro Central", an underground station: the vaulted ticket hall with its shops, fare gates and
escalator well; the platform hall with an island and two side platforms, trains, footbridges and passages): palette,
modelling helpers and the wall finishes shared by mt_struct.py (wall faces, wall art, sunk side faces, doorways, the
gate, trail, hatch, ceilings, vaults, stairs, escalators, rails), mt_hall.py (ticket hall and shop furniture) and
mt_plat.py (trains, track, platform furniture, maintenance gear) -- the family module is fam_kit_metro.py.

Look: a classic deep-level metro -- glazed cream and white tiles with a deep teal dado and a mustard line in the
ticket hall, white tiles with the line colour (Crimson Line red, Harbour Line blue) on the platforms, green-banded
white tiles in the passages, buff stone above 4 m under ribbed barrel vaults, terrazzo floors, brushed steel.

Conventions (src/game/zones.js, kit_base.py):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up,
    Blender -Y = game +Z (the piece's front), Blender +X = game +X.
  * Wall faces are flat painted quads on a cell's front face (y = -0.5, facing -Y); the theme's chooser turns one face
    piece onto any open side of a wall cell and stacks an art overlay (4 - 8 mm proud) on it.
  * Sunk side faces (theme.sunk) hang from the origin (the higher cell's floor) down to the trackbed / well floor,
    on the cell's front face.
  * Walls are WALL_H (8 m) tall; ceilings hang from their origin (the 4 m tiles, the 8 m vaults).
  * Run pieces (rails) are modelled along Blender Y; [n, 1] prefabs along Blender X.
  * <Piece>_COL<n>: solid box, <Piece>_WCOL<n>: walkable (stair treads, escalator steps, the train floors).
  * Stairs rise RISE (0.16 m) per TREAD (0.25 m), escalator steps 0.15 m per 0.26 m, track steps 0.15 per 0.3 m: at
    most 0.32 m between neighbouring 0.5 m nav cells (the robots step 0.4 m).
"""
import math
import random  # noqa: F401

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text  # noqa: F401
from ac_base import AKit

FAM = 'kit-metro'
PFX = 'KIT_METRO_'
ib_lib.GLB[FAM] = 'fps-kit-metro.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
HULL_T = 0.02
ib_lib.PALETTES[FAM] = BASE + [
    # tiles and stone (8 - 23)
    ('tileW', '#F3EFE4'), ('tileC', '#EADFC4'), ('grout', '#CDC3AC'), ('teal', '#1E6B67'), ('tealD', '#14494A'),
    ('mustard', '#E2A62E'), ('crim', '#C9353D'), ('crimD', '#8E232B'), ('blue', '#2F64B5'), ('blueD', '#1F457F'),
    ('green', '#3D8B50'), ('stone', '#CDBFA4'), ('stoneD', '#A2937A'), ('granite', '#45434A'), ('terr', '#D8D0BF'),
    ('terrD', '#B2A895'),
    # concrete, track (24 - 29)
    ('conc', '#A8A49B'), ('concD', '#7A766F'), ('ballast', '#5E5953'), ('rail', '#8F949A'), ('railT', '#D2D6DA'),
    ('rust', '#8A5A3C'),
    # metals (30 - 34)
    ('steel', '#9DA6AF'), ('steelD', '#5D6671'), ('chrome', '#D8DEE4'), ('black', '#232429'), ('graph', '#3A3D45'),
    # glass, screens, light (35 - 41)
    ('glass', '#79B1C8'), ('glassL', '#C8E6F0'), ('screen', '#18243A'), ('amberL', '#FFB43A'), ('scrB', '#46A6EE'),
    ('lightW', '#FFF4D2'), ('dark', '#101218'),
    # train (42 - 44)
    ('trainW', '#E6E8EB'), ('seat', '#2E56A0'), ('rubber', '#474B54'),
    # wood, shops, goods (45 - 55)
    ('wood', '#B9874F'), ('woodD', '#764F31'), ('woodL', '#DDB984'), ('cafe', '#6B4430'), ('mart', '#2C8A57'),
    ('kiosk', '#E5722B'), ('pink', '#D7547A'), ('purple', '#6C4FB0'), ('foodY', '#F1C34C'), ('cream', '#F6EBD3'),
    ('leaf', '#4E9A45'),
    # office paint (56 - 58)
    ('paintG', '#B9C3B4'), ('paintL', '#E3E6DE'), ('hazard', '#F2C230'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])
NAMES = [n for n, _ in ib_lib.PALETTES[FAM]]

WALL_H = 8.0
CEIL = 4.0        # ceiling tiles of the 4 m rooms
RISE, TREAD = 0.16, 0.25
DOOR_H = 2.6      # doorway head (wall.passage is solid above)
ARCH_H = 3.4      # archway header underside
TRACK_D = 0.9     # trackbed depth below the platforms
WELL_D = 4.5      # escalator well depth
Y0 = -0.5         # a front face

# the finish schemes (theme: data layer 0.05 -> face piece): skirting, dado, dado line, field tile, frieze, upper wall
SCHEMES = {
    'H': dict(skirt='granite', dado='teal', line='mustard', field='tileC', frieze='teal', fline='mustard', upper='stone'),
    'P': dict(skirt='granite', dado='green', line='tileW', field='tileW', frieze='green', fline='mustard', upper='tileW'),
    'R': dict(skirt='granite', dado='crim', line='tileW', field='tileW', frieze='crim', fline='crimD', upper='stone'),
    'B': dict(skirt='granite', dado='blue', line='tileW', field='tileW', frieze='blue', fline='blueD', upper='stone'),
    'I': dict(skirt='granite', dado='graph', line='mustard', field='tileW', frieze='crim', fline='blue', upper='stone'),
    'E': dict(skirt='granite', dado='teal', line='mustard', field='tileW', frieze='teal', fline='mustard', upper='tileW'),
    'O': dict(skirt='graph', dado='paintG', line='steelD', field='paintL', frieze='paintL', fline='paintG', upper='paintL'),
    'K': dict(skirt='graph', dado='kiosk', line='cream', field='cream', frieze='kiosk', fline='cream', upper='cream'),
    'F': dict(skirt='woodD', dado='cafe', line='woodL', field='cream', frieze='cafe', fline='woodL', upper='cream'),
    'N': dict(skirt='graph', dado='blueD', line='tileW', field='paintL', frieze='blue', fline='tileW', upper='paintL'),
    'M': dict(skirt='graph', dado='mart', line='tileW', field='tileW', frieze='mart', fline='tileW', upper='tileW'),
}


def cell(name):
    return NAMES.index(name)


def paint(k, sch, z0=0.0, z1=WALL_H, x0=-0.5, x1=0.5, y=Y0, joints=True):
    """a wall finish on the front face: skirting, dado with its line, field tiles with grout lines, the frieze band at
    3.2 m, the field to 4 m, the upper wall to 8 m (stone with a cornice band)"""
    S = SCHEMES[sch]

    def q(a, b, c, d=0.0):
        a, b = max(a, z0), min(b, z1)
        if b - a > 1e-4:
            k.fq(x0, x1, y - d, a, b, c)
    q(0.0, 0.15, S['skirt'])
    q(0.15, 1.1, S['dado'])
    q(1.1, 1.16, S['line'])
    q(1.16, 3.2, S['field'])
    q(3.2, 3.48, S['frieze'])
    q(3.48, 3.52, S['fline'])
    q(3.52, 4.0, S['field'])
    q(4.0, 7.55, S['upper'])
    q(7.55, 7.75, S['frieze'] if S['upper'] != 'stone' else 'stoneD')
    q(7.75, WALL_H, S['upper'])
    if joints and S['field'] in ('tileW', 'tileC'):
        g = 'grout'
        for z in (1.7, 2.3, 2.9):          # grout courses on the field tiles (3 mm proud)
            if z0 + 0.01 < z < z1 - 0.01:
                k.fq(x0, x1, y - 0.003, z - 0.008, z + 0.008, g)
        if z0 < 2.0 < z1:                  # one vertical joint per cell (the tiles' bond)
            k.fq(-0.008, 0.008, y - 0.006, 1.16, 3.2, g)


def sub_wall(k, sch, depth, x0=-0.5, x1=0.5, y=Y0):
    """a wall face below the floor (the well, the trackbed ends): z from -depth to 0"""
    S = SCHEMES[sch]
    k.fq(x0, x1, y, -depth, -depth + 0.15, S['skirt'])
    if depth > 1.5:
        k.fq(x0, x1, y, -depth + 0.15, -depth + 1.1, S['dado'])
        k.fq(x0, x1, y, -depth + 1.1, -depth + 1.16, S['line'])
        k.fq(x0, x1, y, -depth + 1.16, -0.35, S['field'])
        for z in (-depth + 1.8, -depth + 2.5, -depth + 3.2):
            k.fq(x0, x1, y - 0.003, z - 0.008, z + 0.008, 'grout')
        k.fq(x0, x1, y, -0.35, 0.0, S['frieze'])
    else:
        k.fq(x0, x1, y, -depth + 0.15, 0.0, S['dado'])


class MKit(AKit):
    """AKit (culled boxes, painted quads, chairs, text) plus metro shapes"""

    def plate(self, x0, x1, z0, z1, c, y=Y0, d=0.03, rim=None):
        """a flat sign plate on the front face (d thick), optionally with a rim colour 1 cm round it"""
        self.bx(x0, x1, y - d, y, z0, z1, c, cull='k')
        if rim:
            self.fq(x0 + 0.02, x1 - 0.02, y - d - 0.003, z0 + 0.02, z0 + 0.04, rim)
            self.fq(x0 + 0.02, x1 - 0.02, y - d - 0.003, z1 - 0.04, z1 - 0.02, rim)

    def roundel(self, x, y, z, r, ring='crim', bar='blue', word='METRO', face=-1, cap=None, seg=20):
        """the network's roundel in the plane facing -Y (face -1) or +Y: a ring with a bar across and the word on it"""
        s = face
        yy = y + s * 0.001
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            p = [(x + math.cos(a0) * r * 0.66, yy, z + math.sin(a0) * r * 0.66), (x + math.cos(a0) * r, yy, z + math.sin(a0) * r),
                 (x + math.cos(a1) * r, yy, z + math.sin(a1) * r), (x + math.cos(a1) * r * 0.66, yy, z + math.sin(a1) * r * 0.66)]
            self.poly(p, ring, (0, s, 0))
        bw = r * 1.25
        yb = y + s * 0.004
        self.poly([(x - bw, yb, z - r * 0.2), (x + bw, yb, z - r * 0.2), (x + bw, yb, z + r * 0.2), (x - bw, yb, z + r * 0.2)], bar, (0, s, 0))
        self.text(word, x, y + s * 0.007, z, cap or r * 0.26, 'paper', face='y-' if s < 0 else 'y+', font='display',
                  maxw=bw * 1.8, valign='m')

    def pole(self, x, y, z0, z1, r, c, seg=6, ink=True):
        self.cyl(x, y, z0, r, r, z1 - z0, c, seg=seg, ink=ink, caps=False)
