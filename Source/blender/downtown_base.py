"""INKBOLT kit-downtown ("Downtown Standoff", a wide daylight downtown braced for a battle): palette and modelling
helpers shared by downtown_facades.py, downtown_shops.py and downtown_props.py (the family module is
fam_kit_downtown.py).

The palette keeps every colour name blender/parking_cars.py paints with (same hexes), so the car helpers there
(car_body, the SEDAN / SUV profiles, wheels, open doors, truck cabs) build this kit's taxi, police cruiser, bus and
overturned truck unchanged. The everyday parked cars, vans, box trucks, wrecks, motorbikes and bike racks are the
kit-parking pieces themselves: the theme loads that family too (theme option `families`) and places them by their
full KIT_PARKING_ names, so they cost this GLB nothing.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front. Facade modules face Blender -Y and the theme sets wall.facing 'open'. Flat detail is
painted as single faces without an outline shell (PM hull='none'); details stay >= 3 mm proud of what they sit on.
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull, slant, tile  # noqa: F401
from parking_base import fq, bq, uq, dq, lq, rq, poly, disc, cb, rot_box, wheel  # noqa: F401
import ib_text

FAM = 'kit-downtown'
PFX = 'KIT_DOWNTOWN_'
ib_lib.GLB[FAM] = 'fps-kit-downtown.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # parking_cars.py colours (same names and hexes) (8 - 37)
    ('steelD', '#4F5865'), ('paint', '#D8392F'), ('glass', '#7FB9D9'), ('interior', '#4A4553'),
    ('chrome', '#D6DCE3'), ('seat', '#3B3542'), ('pWhite', '#ECEBE4'), ('lineY', '#FFCF33'),
    ('light', '#FFF4C8'), ('galv', '#B9C2CB'), ('tire', '#2A2830'), ('pipeR', '#D9423A'),
    ('litA', '#FFB01F'), ('rust', '#A4532D'), ('cone', '#F2681F'), ('cardb', '#C99B60'),
    ('steel', '#8A95A3'), ('glassL', '#D2EEF9'), ('tarp', '#5E7FA6'), ('plate', '#F3EFDF'),
    ('burntL', '#6C5B4D'), ('burnt', '#3A3331'), ('wood', '#BC8853'), ('signB', '#2A63CB'),
    ('pipeB', '#3B7CC6'), ('pYellow', '#F2C230'), ('pTeal', '#23A49F'), ('pBlue', '#2F6CD3'),
    ('exitG', '#25B35E'), ('ash', '#8B857D'),
    # street and facades (38 - 52)
    ('navy', '#2B3A67'), ('walk', '#CFC8BC'), ('walkB', '#BDB5A8'), ('curb', '#9A9387'),
    ('conc', '#B8B2A7'), ('lime', '#E6DCC6'), ('limeD', '#C7B99B'), ('brickT', '#C98455'),
    ('brickTD', '#A0603C'), ('terra', '#63B5A8'), ('terraD', '#3E8A7F'), ('concF', '#A7ACB4'),
    ('mull', '#3B4150'), ('roof', '#6E6A74'), ('cream', '#F3EAD5'),
    # shops, battle, nature (53 - 63)
    ('woodD', '#7B5236'), ('tileW', '#E4EAEC'), ('pink', '#E8668F'), ('violet', '#7D55C7'),
    ('sand', '#CDB07C'), ('sandD', '#A68A57'), ('olive', '#6B7843'), ('leaf', '#5FA857'),
    ('leafD', '#43803F'), ('trunk', '#6E4E3A'), ('bronze', '#9C7A4A'),
]
assert len(ib_lib.PALETTES[FAM]) == 64, len(ib_lib.PALETTES[FAM])
TRIS = {}
HT = 0.02

# storeys: ground floor and upper floor heights; walk-in shop ceiling; the doorway's lintel
G_H, U_H = 4.6, 3.4
RH = 3.6
DOOR_H = 3.4


def top_of(n):
    return G_H + (n - 1) * U_H


def new(pal):
    return PM(pal)


def make(name, m, ao, bevel=0.0, cols=None, hull=HT):
    """build one kit piece; cols: collision boxes [(centre, half, walk?)] as cb() / rot_box() return them"""
    full = PFX + name
    obj = build_object(full, m, bevel, hull, ao=ao)
    post_hull(obj, m.hmode)
    TRIS[full] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    for i, col in enumerate(cols or []):
        c, hlf = col[0], col[1]
        walk = len(col) > 2 and col[2]
        e = bpy.data.objects.new('%s_%sCOL%d' % (full, 'W' if walk else '', i), None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.parent = obj
        e.location = c
        e.scale = hlf
    return obj


def box(x0, y0, z0, x1, y1, z1):
    """collision box from two corners, any order (Blender coords)"""
    return cb(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1))


def rz(deg, dx=0.0, dy=0.0, dz=0.0):
    return Matrix.Translation((dx, dy, dz)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


def txt(m, word, x, y, z, cap, color, face='y-', font='sans', valign='m', maxw=None, shadow=None, align='c'):
    ib_text.draw(m, word, x, y, z, cap, color, face=face, font=font, valign=valign, maxw=maxw, shadow=shadow, align=align)


def F(d):
    """y of the front face of a facade detail standing d proud of the module's front plane (y = -0.5)"""
    return -0.5 - d


def sandbag_row(m, x0, x1, y, z, depth=0.36, h=0.2, c='sand', c2='sandD', k0=0, seams=False, top=True):
    """a course of sandbags along X centred on y, base z: bags in two tones (seams: a tie band on each bag's face)"""
    n = max(1, int(round((x1 - x0) / 0.55)))
    w = (x1 - x0) / n
    for i in range(n):
        a = x0 + i * w
        col = c if (i + k0) % 2 else c2
        m.bx(a + 0.01, a + w - 0.01, y - depth / 2, y + depth / 2, z, z + h, col, hull='full' if top else 'none')
        if seams:
            fq(m, a + w * 0.42, a + w * 0.58, y - depth / 2 - 0.004, z + 0.03, z + h - 0.04, 'sandD' if col == 'sand' else 'sand')


def sandbag_wall(m, x0, x1, y, rows=4, depth=0.38, h=0.2, seams=False):
    for k in range(rows):
        inset = 0.04 * k
        sandbag_row(m, x0 + inset + (0.14 if k % 2 else 0.0), x1 - inset - (0.14 if k % 2 else 0.0), y, k * h, depth - 0.03 * k, h, k0=k, seams=seams, top=k == rows - 1)
