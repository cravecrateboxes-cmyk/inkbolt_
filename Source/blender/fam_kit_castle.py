"""INKBOLT asset family: kit-castle ('Castle Courtyard').

The wide wards of a sandstone castle on a bright summer day: battered curtain walls with corbelled parapets and
merlons, round drum towers, a square keep with a forebuilding stair, gatehouses with timber portcullises, packed-earth
yards with cobbled lanes, a market of striped stalls and carts, hay, barrels, a stone well, a training yard with
dummies, weapon racks and archery butts, braziers and banners. Beyond the walls: higher outer ramparts and towers,
green hills and a village.

Conventions (see fam_kit_smallcity.py and ib_lib.py):
  * 1 ASCII cell = 1 m; a piece's origin is the centre of its cell / footprint at floor level
  * a wall module's face is its Blender -Y side; the theme sets wall.facing = 'open', so the engine turns that face to
    the module's single open side (S / N / E / W); corners and notches get the four-way symmetric 'Corner' turret
  * wall modules drop their outline shell on the +/-X faces ('noside') so a run reads as one wall; merlons, towers,
    corners and props keep the full ink outline
  * every coplanar pair of faces is avoided by construction (check_zfight fails the build otherwise)
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull, col_box, ring
import castle_detail as cd

FAM = 'kit-castle'
PRE = 'KIT_CASTLE_'
ib_lib.GLB[FAM] = 'fps-kit-castle.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # masonry
    ('stone', '#D3C4A6'), ('stoneL', '#E6DAC0'), ('stoneD', '#B3A386'), ('stoneDD', '#93866C'),
    ('mortar', '#A39478'), ('slate', '#5F6E88'), ('slateD', '#4B5770'), ('plaster', '#F1E6CB'),
    # timber, iron, fire
    ('wood', '#8C5B3A'), ('woodL', '#B98651'), ('woodD', '#5E3E2A'), ('iron', '#383943'),
    ('ironL', '#666A76'), ('fire', '#FF9530'), ('fireY', '#FFD65C'), ('glassD', '#3C4762'),
    # heraldry and cloth
    ('bannerR', '#C33F38'), ('bannerB', '#3D5DA8'), ('gold', '#EAB83B'), ('canvas', '#F4EBD6'),
    ('clothG', '#4F8D5C'), ('clothP', '#7E5CA6'), ('rope', '#C9A56B'), ('leather', '#9A5E3A'),
    # yard
    ('earth', '#CDB48A'), ('earthD', '#B39873'), ('cobble', '#C1B7A4'), ('cobbleL', '#CCC3B0'),
    ('cobbleD', '#B2A894'), ('grass', '#8FBF5C'), ('grassD', '#76A64B'), ('hay', '#EAC35A'),
    ('hayD', '#CC9F3C'), ('water', '#78C0D8'), ('leaf', '#79B456'), ('leafD', '#5B9044'),
    # market goods
    ('apple', '#D9483B'), ('cabbage', '#A4CE6E'), ('bread', '#D99A4E'), ('pot', '#C2714A'),
    ('cheese', '#F2CF63'), ('fish', '#A9C1CF'),
    # backdrop
    ('flag', '#D9CDB3'), ('flagL', '#E3D8C0'),
    ('hill', '#9CC46C'), ('hillD', '#7DA957'), ('roofR', '#B85A43'), ('bdStone', '#C9BFAE'),
    ('bdSlate', '#7D8AA3'), ('bdWall', '#E2D6C2'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

HT = 0.02
WALK = 7.6     # top of the curtain body (the coping sits on it)


def make(name, m, bevel=0.0, hull=HT, ao=False):
    obj = build_object(PRE + name, m, bevel, hull, ao=ao)
    post_hull(obj, m.hmode)
    return obj


def F(d):
    return -0.5 - d


def poly_y(m, pts, y0, y1, color, hull='full'):
    """Polygon pts [(x, z), ...] in the X-Z plane extruded along Y from y0 to y1 (banner tails, gables). One shape."""
    bm = m.bm
    M = m.parent
    a = [bm.verts.new(M @ Vector((x, y0, z))) for (x, z) in pts]
    b = [bm.verts.new(M @ Vector((x, y1, z))) for (x, z) in pts]
    faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    m.nshape += 1
    for f in faces:
        f.material_index = m.pal.index(color)
        f[m.shape] = m.nshape
    if hull != 'full':
        m.hmode[m.nshape] = hull
    return faces


def flame(m, x, y, z, s=1.0):
    """Comic flame: three stacked cones, orange outside, yellow core (no outline on the core)."""
    m.cy((x, y, z), 0.16 * s, 0.0, 0.42 * s, 'fire', seg=6)
    m.cy((x + 0.06 * s, y - 0.04 * s, z + 0.04 * s), 0.09 * s, 0.0, 0.3 * s, 'fire', seg=5)
    m.cy((x, y - 0.03 * s, z + 0.02 * s), 0.09 * s, 0.0, 0.28 * s, 'fireY', seg=5, hull='none')


# ================================================================ curtain walls
def ashlar(m, rnd, z_lo, z_hi, d=0.018):
    """A few proud / sunk ashlar blocks between the courses (lighter and darker stones) so runs never read as tiles."""
    courses = [(0.35 + 1.25, 2.3), (2.335, 3.5), (3.535, 4.7), (4.735, 5.9), (5.935, 6.3)]
    for (c0, c1) in courses:
        if c1 <= z_lo or c0 >= z_hi:
            continue
        x = -0.45 + rnd.random() * 0.15
        while x < 0.3:
            w = 0.28 + rnd.random() * 0.3
            if x + w > 0.46:
                break
            if rnd.random() < 0.4:
                h0 = c0 + 0.05 + rnd.random() * 0.05
                h1 = min(c1 - 0.05, h0 + 0.35 + rnd.random() * 0.4)
                m.det(x, x + w, d, 0.0, h0, h1, rnd.choice(('stoneL', 'stoneD', 'stoneL')))
            x += w + 0.08 + rnd.random() * 0.2


def curtain(pal, name, merlon, extra, seed, ao):
    m = PM(pal)
    rnd = random.Random(seed)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, WALK, 'stone', hull='noside', cull='bt')
    # battered plinth (the postern's plinth is cut back to its two ends: steps lead up to the door)
    for (px0, px1) in (((-0.5, -0.48), (0.48, 0.5)) if extra == 'door' else ((-0.5, 0.5),)):
        m.prism([(-0.5, 0.0), (-0.74, 0.0), (-0.74, 0.32), (-0.5, 1.6)], px0, px1, ['stoneD'], hull='noside', skip=(3,))
    # mortar courses (full width: they join along a run)
    for z in (2.3, 3.5, 4.7, 5.9):
        m.bx(-0.5, 0.5, F(0.008), -0.5, z, z + 0.035, 'mortar', hull='none', cull='ktblr')
    ashlar(m, rnd, 1.6, 6.3)
    # corbels carrying the parapet
    for x in (-0.25, 0.25):
        m.bx(x - 0.1, x + 0.1, -0.77, -0.5, 6.28, 6.72, 'stoneD', cull='k')
    m.bx(-0.5, 0.5, -0.8, -0.5, 6.72, WALK, 'stone', hull='noside', cull='kt')              # parapet face
    m.bx(-0.5, 0.5, -0.84, 0.5, WALK, WALK + 0.14, 'stoneL', hull='noside')                 # coping (whole wall top)
    if merlon:
        m.bx(-0.44, 0.44, -0.8, -0.3, WALK + 0.14, WALK + 1.25, 'stone', cull='b')
        m.bx(-0.47, 0.47, -0.83, -0.27, WALK + 1.25, WALK + 1.36, 'stoneL')
        if extra == 'slit' or seed % 3 == 0:
            m.bx(-0.04, 0.04, -0.807, -0.79, WALK + 0.4, WALK + 1.0, 'ink', hull='none', cull='k')
    if extra == 'slit':                                                                        # arrow slit
        m.det(-0.2, 0.2, 0.03, 0.0, 3.75, 5.25, 'stoneL', hull='full')
        m.det(-0.055, 0.055, 0.045, 0.02, 3.9, 5.1, 'ink')                                    # a plain vertical loop (no cross arm)
    elif extra in ('bannerR', 'bannerB'):
        c = extra
        m.cy((-0.5, -0.98, 6.55), 0.035, 0.035, 1.0, 'iron', seg=6, rot=(0, 90, 0))           # pole
        for x in (-0.44, 0.44):
            m.bx(x - 0.025, x + 0.025, -0.99, -0.8, 6.49, 6.61, 'iron', hull='none', cull='k')
        m.bx(-0.4, 0.4, -1.0, -0.96, 3.3, 6.52, c)                                              # cloth
        poly_y(m, [(-0.4, 3.3), (0.0, 3.3), (-0.2, 2.75)], -1.0, -0.96, c)                     # swallow tail
        poly_y(m, [(0.0, 3.3), (0.4, 3.3), (0.2, 2.75)], -1.0, -0.96, c)
        m.bx(-0.33, 0.33, -1.007, -0.999, 6.0, 6.08, 'gold', hull='none', cull='k')            # trim
        poly_y(m, [(0.0, 5.55), (0.22, 5.1), (0.0, 4.4), (-0.22, 5.1)], -1.012, -0.999, 'gold', hull='none')   # lozenge
        poly_y(m, [(0.0, 5.3), (0.1, 5.08), (0.0, 4.75), (-0.1, 5.08)], -1.02, -1.011, 'bannerR' if c == 'bannerB' else 'bannerB', hull='none')
    elif extra == 'torch':
        m.bx(-0.07, 0.07, -0.56, -0.48, 2.45, 2.85, 'iron', cull='k')                           # back plate
        m.bm_((0, -0.53, 2.55), (0, -0.82, 2.85), 0.045, 'iron')
        m.cy((0, -0.84, 2.7), 0.08, 0.06, 0.3, 'iron', seg=6)
        m.cy((0, -0.84, 2.6), 0.04, 0.05, 0.12, 'wood', seg=5, hull='none')
        flame(m, 0, -0.84, 2.98, 0.9)
        m.det(-0.18, 0.18, 0.012, 0.0, 3.05, 3.9, 'stoneDD', hull='none')                       # soot
    elif extra == 'buttress':
        m.bx(-0.34, 0.34, -1.2, -0.49, 0, 2.6, 'stoneD', cull='kb')
        m.prism([(-1.2, 2.6), (-0.49, 2.6), (-0.49, 3.3)], -0.34, 0.34, ['stoneL'], skip=(1,))
        m.bx(-0.28, 0.28, -0.85, -0.49, 2.7, 5.6, 'stone', cull='kb')
        m.prism([(-0.85, 5.6), (-0.49, 5.6), (-0.49, 6.1)], -0.28, 0.28, ['stoneL'], skip=(1,))
    elif extra == 'door':                                                                      # postern door
        m.det(-0.42, 0.42, 0.04, 0.0, 0.0, 2.35, 'stoneL', hull='full')
        m.det(-0.33, 0.33, 0.06, 0.02, 0.0, 2.15, 'woodD')
        for z in (0.5, 1.6):
            m.det(-0.35, 0.35, 0.07, 0.03, z, z + 0.07, 'iron')
        m.det(0.18, 0.24, 0.08, 0.04, 1.0, 1.08, 'gold')
    cd.curtain_detail(m, extra, merlon, seed)
    return make(name, m, ao=ao)


def inner(pal, ao):
    """Beside an inner corner: the perpendicular wall's parapet crosses this module's front, so nothing here stands
    proud of the face; the coping is flush and the merlon set back on the wall top. The corner turret covers the join."""
    m = PM(pal)
    rnd = random.Random(17)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, WALK, 'stone', hull='noside', cull='bt')
    m.prism([(-0.5, 0.0), (-0.74, 0.0), (-0.74, 0.32), (-0.5, 1.6)], -0.5, 0.5, ['stoneD'], hull='noside', skip=(3,))
    for z in (2.3, 3.5, 4.7, 5.9):
        m.bx(-0.5, 0.5, F(0.008), -0.5, z, z + 0.035, 'mortar', hull='none', cull='ktblr')
    ashlar(m, rnd, 1.6, 6.3)
    m.bx(-0.5, 0.5, -0.5, 0.5, WALK, WALK + 0.14, 'stoneL', hull='noside', cull='b')
    m.bx(-0.44, 0.44, -0.47, 0.03, WALK + 0.14, WALK + 1.25, 'stone', cull='b')
    m.bx(-0.47, 0.47, -0.5, 0.06, WALK + 1.25, WALK + 1.36, 'stoneL')
    cd.inner_detail(m)
    return make('Curtain_Inner', m, ao=ao)


def corner(pal, ao):
    """Four-way symmetric corner turret (inner and outer corners, wall ends, notches)."""
    m = PM(pal)
    m.bx(-0.62, 0.62, -0.62, 0.62, 0, 8.3, 'stone', cull='bt')
    m.bx(-0.77, 0.77, -0.77, 0.77, 0, 0.9, 'stoneD', cull='bt')
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        m.prism([(-0.77, 0.9), (-0.62, 1.18), (-0.62, 0.9)], -0.62, 0.62, ['stoneD'], hull='none', skip=(1,))
    m.parent = Matrix.Identity(4)
    for z in (2.3, 3.5, 4.7, 5.9):
        m.bx(-0.627, 0.627, -0.627, 0.627, z, z + 0.035, 'mortar', hull='none')
    m.bx(-0.81, 0.81, -0.81, 0.81, 8.3, 8.48, 'stoneL')
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * 0.22, sx * 0.76))
            y0, y1 = sorted((sy * 0.22, sy * 0.76))
            m.bx(x0, x1, y0, y1, 8.48, 9.5, 'stone', cull='b')
            m.bx(x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03, 9.5, 9.6, 'stoneL')
    m.bx(-0.22, 0.22, -0.22, 0.22, 8.48, 8.9, 'stoneD', cull='b')
    cd.corner_detail(m)
    return make('Corner', m, ao=ao)


def build_walls(pal, ao):
    curtain(pal, 'Curtain_M', True, None, 1, ao)
    curtain(pal, 'Curtain_M2', True, None, 7, ao)
    curtain(pal, 'Curtain_C', False, None, 2, ao)
    curtain(pal, 'Curtain_C2', False, None, 11, ao)
    curtain(pal, 'Curtain_Slit', True, 'slit', 5, ao)
    curtain(pal, 'Curtain_BannerR', False, 'bannerR', 4, ao)
    curtain(pal, 'Curtain_BannerB', False, 'bannerB', 8, ao)
    curtain(pal, 'Curtain_Torch', False, 'torch', 10, ao)
    curtain(pal, 'Curtain_Buttress', True, 'buttress', 13, ao)
    curtain(pal, 'Curtain_Door', True, 'door', 14, ao)
    inner(pal, ao)
    corner(pal, ao)


# ================================================================ yard surfaces
def paving(m, colors, h=0.012):
    """1 m paving tile of four 0.5 m stones (colors in reading order), 1.2 cm proud of the yard, no sides and no
    outline (a joint would turn to ink at grazing angles). Tiles alternate A / B, so neighbouring stones differ."""
    bm = m.bm
    xs = (-0.5, 0.0, 0.5)
    V = {(i, j): bm.verts.new((x, y, h)) for i, x in enumerate(xs) for j, y in enumerate(xs)}
    faces = []
    for i in range(2):
        for j in range(2):
            f = bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]))
            f.material_index = m.pal.index(colors[j * 2 + i])
            f.normal_update()
            if f.normal.z < 0:
                f.normal_flip()
            faces.append(f)
    m.nshape += 1
    for f in faces:
        f[m.shape] = m.nshape
    m.hmode[m.nshape] = 'none'


def build_floor(pal):
    for name, cols in (('Cobble', ('cobble', 'cobbleL', 'cobbleD', 'cobble')), ('CobbleB', ('cobbleL', 'cobble', 'cobble', 'cobbleD')),
                       ('Flag', ('flagL', 'flag', 'flag', 'flagL')), ('FlagB', ('flag', 'flagL', 'flagL', 'flag'))):
        m = PM(pal)
        paving(m, cols)
        make(name, m, hull=0)
    # grass patch with a few tufts
    for name, seed in (('Grass', 3), ('GrassB', 9)):
        m = PM(pal)
        rnd = random.Random(seed)
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, 0.018, 'grass', hull='none', cull='b')
        for k in range(2):
            x, y = rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35)
            m.cy((x, y, 0.004 + 0.004 * k), 0.1, 0.0, 0.24 + rnd.random() * 0.1, 'grassD' if k % 2 else 'leaf', seg=4, hull='none', caps=False)
        make(name, m, hull=0)


# ================================================================ gatehouse, trail, hatch
GW = 2.96      # gatehouse half width (just inside the second wall cell beside the opening)
GD = 0.95      # half depth


def build_gate(pal, ao):
    """Gatehouse over the 3 m opening, the same on both faces (entry and exit gates): battered piers, a round arch
    of voussoirs over a filled tympanum, a heraldic shield, corbelled machicolation, merlons, two banners, torches."""
    m = PM(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.48, sx * GW))
        m.bx(x0, x1, -GD, GD, 0, 9.4, 'stone', cull='b')                                     # piers
        m.bx(x0 - 0.06 if sx < 0 else x0 + 0.03, x1 + 0.06 if sx > 0 else x1 - 0.03, -GD - 0.14, GD + 0.14, 0, 1.0, 'stoneD', cull='b')
        for z in (2.3, 4.7):
            m.bx(x0 - 0.005 if sx < 0 else x0 + 0.005, x1 + 0.005 if sx > 0 else x1 - 0.005, -GD - 0.005, GD + 0.005, z, z + 0.035, 'mortar', hull='none')
    m.bx(-1.48, 1.48, -GD, GD, 3.2, 9.4, 'stone', cull='')                                    # lintel mass
    for sy in (-1, 1):
        rot = Matrix.Rotation(0 if sy < 0 else math.pi, 4, 'Z')
        m.parent = rot
        # arch: voussoirs on a 1.5 m radius over a dark filled tympanum
        poly_y(m, [(-1.5, 3.2)] + [(math.cos(math.pi - a * math.pi / 8) * 1.45, 3.2 + math.sin(math.pi - a * math.pi / 8) * 1.45) for a in range(1, 8)] + [(1.5, 3.2)],
               -GD - 0.02, -GD, 'woodD', hull='none')
        for k in range(9):
            a0, a1 = math.pi - k * math.pi / 9, math.pi - (k + 1) * math.pi / 9
            pts = [(math.cos(a0) * 1.5, 3.2 + math.sin(a0) * 1.5), (math.cos(a0) * 2.05, 3.2 + math.sin(a0) * 2.05),
                   (math.cos(a1) * 2.05, 3.2 + math.sin(a1) * 2.05), (math.cos(a1) * 1.5, 3.2 + math.sin(a1) * 1.5)]
            poly_y(m, pts, -GD - 0.08 - (0.03 if k == 4 else 0.0), -GD + 0.02, 'stoneL' if k != 4 else 'stone')
        for x in (-1.5, 1.5):                                                                  # imposts
            m.bx(x - 0.2, x + 0.2, -GD - 0.1, -GD + 0.02, 2.95, 3.2, 'stoneL')
        # shield over the arch
        poly_y(m, [(-0.55, 6.9), (0.55, 6.9), (0.55, 6.25), (0.0, 5.55), (-0.55, 6.25)], -GD - 0.06, -GD + 0.02, 'bannerB')
        poly_y(m, [(0.0, 6.74), (0.26, 6.32), (0.0, 5.86), (-0.26, 6.32)], -GD - 0.075, -GD - 0.05, 'gold', hull='none')   # lozenge, as on the banners
        # banners on poles beside the arch
        for x in (-2.25, 2.25):
            m.cy((x - 0.45, -GD - 0.32, 7.35), 0.035, 0.035, 0.9, 'iron', seg=6, rot=(0, 90, 0))
            m.bx(x - 0.025, x + 0.025, -GD - 0.32, -GD + 0.02, 7.29, 7.41, 'iron', hull='none', cull='k')
            m.bx(x - 0.37, x + 0.37, -GD - 0.34, -GD - 0.3, 4.6, 7.32, 'bannerR')
            poly_y(m, [(x - 0.37, 4.6), (x + 0.37, 4.6), (x, 4.05)], -GD - 0.34, -GD - 0.3, 'bannerR')
            poly_y(m, [(x, 6.6), (x + 0.2, 6.2), (x, 5.75), (x - 0.2, 6.2)], -GD - 0.35, -GD - 0.335, 'gold', hull='none')
        # torches at head height
        for x in (-2.3, 2.3):
            m.bm_((x, -GD + 0.01, 2.25), (x, -GD - 0.3, 2.55), 0.05, 'iron')
            m.cy((x, -GD - 0.32, 2.42), 0.08, 0.06, 0.26, 'iron', seg=6)
            flame(m, x, -GD - 0.32, 2.68, 0.85)
        # corbels and the machicolation band
        for k in range(8):
            x = -2.65 + k * 0.757
            m.bx(x - 0.1, x + 0.1, -GD - 0.3, -GD + 0.02, 8.65, 9.05, 'stoneD', cull='k')
    m.parent = Matrix.Identity(4)
    m.bx(-GW - 0.12, GW + 0.12, -GD - 0.32, GD + 0.32, 9.05, 9.85, 'stone', cull='')       # machicolation
    m.bx(-GW - 0.16, GW + 0.16, -GD - 0.36, GD + 0.36, 9.85, 10.0, 'stoneL')
    for k in range(5):
        x = -2.5 + k * 1.25
        m.bx(x - 0.36, x + 0.36, -GD - 0.3, GD + 0.3, 10.0, 11.05, 'stone', cull='b')
        m.bx(x - 0.39, x + 0.39, -GD - 0.33, GD + 0.33, 11.05, 11.16, 'stoneL')
    # flagpole with a pennant
    m.cy((0, 0, 10.0), 0.05, 0.04, 2.6, 'woodD', seg=6)
    poly_y(m, [(0.04, 12.5), (1.3, 12.25), (0.04, 12.0)], -0.02, 0.02, 'bannerR')
    # passage soffit and the portcullis slot
    m.bx(-1.505, 1.505, -0.12, 0.12, 3.06, 3.2, 'iron', hull='none', cull='t')
    cd.gate_detail(m)
    obj = make('GateFrame', m, ao=ao)
    return obj


def build_shutter(pal):
    """Timber gate: upright oak bars (both faces) on a dark backing (no see-through), held by one head beam and one
    foot beam with a row of studs each, iron spikes at the foot. No bars cross in the open field."""
    m = PM(pal)
    H = 3.05
    m.bx(-1.49, 1.49, -0.03, 0.03, 0.35, H, 'woodD', hull='none')
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.03, sy * 0.085))
        for k in range(7):
            x = -1.29 + k * 0.43
            m.bx(x - 0.105, x + 0.105, y0, y1, 0.2, H - 0.26, 'woodL', hull='none')
        y0, y1 = sorted((sy * 0.03, sy * 0.13))
        m.bx(-1.49, 1.49, y0, y1, H - 0.26, H, 'wood', hull='none')                              # head beam
        y0, y1 = sorted((sy * 0.085, sy * 0.13))
        m.bx(-1.49, 1.49, y0, y1, 0.35, 0.53, 'wood', hull='none')                               # foot beam
        y0, y1 = sorted((sy * 0.13, sy * 0.145))
        for z in (0.44, H - 0.13):
            for k in range(8):
                x = -1.505 + k * 0.43
                m.cy((x, (y0 + y1) / 2, z), 0.04, 0.04, 0.015, 'iron', seg=6, rot=(90, 0, 0), hull='none')
    for k in range(7):
        x = -1.29 + k * 0.43
        m.cy((x, 0, 0.0), 0.0, 0.07, 0.22, 'iron', seg=4, hull='none')
    cd.shutter_detail(m)
    sh = make('GateShutter', m, hull=0)
    m = PM(pal)
    m.bx(-1.5, 1.5, -0.15, 0.15, 0, H, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(sh, tmp)


def build_trail(pal, ao):
    """Trail wall: 1 m of the passage between two wards (a 'zwinger'), as high as the curtain walls so nothing beyond
    shows over it; both faces dressed alike (the hatch room turns some of them round). It repeats every metre, so its
    face is plain coursed ashlar in a running bond (joints alternate between mid-module and the module ends), with a
    battered plinth and a merlon per metre on top. Runs along Blender Y."""
    m = PM(pal)
    m.bx(-0.25, 0.25, -0.5, 0.5, 0.8, WALK, 'stone', hull='noend', cull='bt')
    m.bx(-0.33, 0.33, -0.5, 0.5, 0, 0.8, 'stoneD', hull='noend', cull='b')
    for sx in (-1, 1):
        cl = 'r' if sx < 0 else 'l'

        def face(d, y0, y1, z0, z1, c):
            x0, x1 = sorted((sx * 0.25, sx * (0.25 + d)))
            m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cl + 'tbfk')
        for k in range(12):                                                                 # bed joints
            z = 1.4 + k * 0.55
            if z > WALK - 0.3:
                break
            face(0.005, -0.5, 0.5, z, z + 0.03, 'mortar')
            zn = min(z + 0.55, WALK)
            if k % 2:                                                                          # perpends
                face(0.006, -0.015, 0.015, z + 0.03, zn, 'mortar')
            else:
                face(0.006, -0.5, -0.485, z + 0.03, zn, 'mortar')
                face(0.006, 0.485, 0.5, z + 0.03, zn, 'mortar')
        face(0.004, -0.5, 0.5, 0.8, 1.4, 'stoneD')                                            # plinth course
    m.bx(-0.36, 0.36, -0.5, 0.5, WALK, WALK + 0.14, 'stoneL', hull='noend')
    m.bx(-0.27, 0.27, -0.25, 0.25, WALK + 0.14, WALK + 1.1, 'stone', cull='b')
    m.bx(-0.3, 0.3, -0.28, 0.28, WALK + 1.1, WALK + 1.2, 'stoneL')
    cd.trail_detail(m)
    make('TrailWall', m, ao=ao)


def build_hatch(pal, ao):
    """Exit pad: a cellar trapdoor of iron-banded oak in a stone ring, teal lamps around it."""
    m = PM(pal)
    m.cy((0, 0, 0), 1.32, 1.26, 0.12, 'stoneD', seg=16, bevel=True)
    m.cy((0, 0, 0.12), 1.1, 1.1, 0.025, 'teal', seg=16, hull='none')
    m.bx(-0.85, 0.85, -0.85, 0.85, 0.125, 0.2, 'wood')
    for k in range(-3, 4):
        m.bx(k * 0.24 - 0.008, k * 0.24 + 0.008, -0.8, 0.8, 0.19, 0.206, 'woodD', hull='none', cull='b')
    for y in (-0.5, 0.5):
        m.bx(-0.86, 0.86, y - 0.07, y + 0.07, 0.19, 0.225, 'iron', hull='none', cull='b')
    m.cy((0.0, 0.0, 0.2), 0.16, 0.16, 0.035, 'iron', seg=10, hull='none')
    m.cy((0.0, 0.0, 0.235), 0.1, 0.1, 0.012, 'gold', seg=8, hull='none')
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        m.cy((math.cos(a) * 1.18, math.sin(a) * 1.18, 0.12), 0.06, 0.05, 0.07, 'amber', seg=6, hull='none')
    make('Hatch', m, bevel=0.015, ao=ao)


# ================================================================ props
def barrel(m, x, y, z, r=0.3, h=0.78, c='wood', lie=False):
    rot = (90, 0, 0) if lie else (0, 0, 0)
    if lie:
        m.cy((x, y + h / 2, z + r), r * 0.9, r * 0.9, h, c, seg=10, rot=rot)
        for t in (0.08, h - 0.13):
            m.cy((x, y + h / 2 - t, z + r), r * 0.93, r * 0.93, 0.05, 'iron', seg=10, rot=rot, hull='none')
        return
    m.cy((x, y, z), r * 0.88, r, h / 2, c, seg=8)
    m.cy((x, y, z + h / 2), r, r * 0.88, h / 2, c, seg=8)
    for t in (0.1, h - 0.15):
        rr = r * (0.9 + 0.1 * (1 - abs(t - h / 2) / (h / 2)))
        m.cy((x, y, z + t), rr + 0.012, rr + 0.012, 0.05, 'iron', seg=8, hull='none', caps=False)
    m.cy((x, y, z + h - 0.01), r * 0.8, r * 0.8, 0.02, 'woodL', seg=8, hull='none')


def build_barrels(pal, ao):
    m = PM(pal)
    barrel(m, -0.18, -0.12, 0.0)
    barrel(m, 0.24, 0.2, 0.0, r=0.24, h=0.62, c='woodL')
    obj = make('Barrels', m, ao=ao)
    col_box(obj, 0, -0.46, 0.46, -0.42, 0.44, 0, 0.8)
    m = PM(pal)
    barrel(m, -0.245, 0.0, 0.0, r=0.24, h=0.7)
    barrel(m, 0.245, 0.0, 0.0, r=0.24, h=0.66, c='woodL')
    m.bx(-0.48, 0.48, -0.3, 0.3, 0.71, 0.77, 'woodD')                                          # board across
    barrel(m, 0.0, 0.0, 0.77, r=0.24, h=0.6)
    obj = make('BarrelStack', m, ao=ao)
    col_box(obj, 0, -0.48, 0.48, -0.3, 0.3, 0, 1.36)


def crate(m, cx, cy, z, s, c='woodL'):
    m.bx(cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2, z, z + s, c)
    for sy in (-1, 1):
        y0, y1 = sorted((cy + sy * s / 2, cy + sy * (s / 2 + 0.006)))
        m.bx(cx - s / 2 + 0.03, cx + s / 2 - 0.03, y0, y1, z + 0.03, z + 0.09, 'wood', hull='none')
        m.bx(cx - s / 2 + 0.03, cx + s / 2 - 0.03, y0, y1, z + s - 0.09, z + s - 0.03, 'wood', hull='none')


def build_crates(pal, ao):
    m = PM(pal)
    crate(m, -0.2, -0.1, 0, 0.52)
    crate(m, 0.26, 0.18, 0, 0.42, 'wood')
    crate(m, -0.18, -0.08, 0.52, 0.4, 'wood')
    for a in ((-0.2, -0.1, 0, 0.52), (0.26, 0.18, 0, 0.42), (-0.18, -0.08, 0.52, 0.4)):
        cd.crate_detail(m, a[0], a[1], a[2], a[3])
    obj = make('Crates', m, bevel=0.012, ao=ao)
    col_box(obj, 0, -0.47, 0.47, -0.38, 0.4, 0, 0.92)
    m = PM(pal)                                                                               # grain sacks
    for (x, y, z, s) in ((-0.22, -0.12, 0, 1.0), (0.2, -0.05, 0, 0.95), (0.0, 0.22, 0, 0.9), (-0.02, -0.04, 0.42, 0.9)):
        m.sp((x, y, z + 0.24 * s), 0.27 * s, 'canvas' if z == 0 else 'rope', seg=(7, 4), scale=(1.0, 0.82, 0.95))
        m.cy((x, y, z + 0.47 * s), 0.07, 0.04, 0.12, 'rope', seg=5, hull='none')
    obj = make('Sacks', m, ao=ao)
    col_box(obj, 0, -0.47, 0.45, -0.38, 0.46, 0, 0.82)


def build_hay(pal, ao):
    m = PM(pal)                                                                               # square bale
    m.bx(-0.46, 0.46, -0.32, 0.32, 0, 0.5, 'hay')
    for x in (-0.22, 0.22):
        m.bx(x - 0.025, x + 0.025, -0.326, 0.326, -0.005, 0.506, 'rope', hull='none')
    for k in range(3):
        x = -0.3 + k * 0.3
        m.bx(x - 0.012, x + 0.012, -0.332, -0.32, 0.06, 0.44, 'hayD', hull='none', cull='ktblr')
    m.bx(-0.36, 0.2, -0.22, 0.26, 0.5, 0.84, 'hay')
    m.bx(-0.11, -0.06, -0.226, 0.266, 0.495, 0.846, 'rope', hull='none')
    obj = make('HayBale', m, ao=ao)
    col_box(obj, 0, -0.47, 0.47, -0.33, 0.33, 0, 0.84)
    m = PM(pal)                                                                               # 2 x 2 haystack
    m.cy((0, 0, 0), 0.92, 0.82, 0.9, 'hay', seg=10)
    m.cy((0, 0, 0.9), 0.82, 0.12, 1.0, 'hay', seg=10)
    m.cy((0, 0, 0.9), 0.836, 0.836, 0.08, 'hayD', seg=10, hull='none', caps=False)
    m.cy((0, 0, 1.85), 0.06, 0.02, 0.5, 'woodD', seg=5)
    for (x, y, r) in ((0.75, -0.55, 0.22), (-0.7, 0.5, 0.18)):
        m.sp((x, y, 0.08), r, 'hayD', seg=(6, 3), scale=(1, 1, 0.5), hull='none')
    m.bm_((0.55, -0.6, 0.0), (0.95, -0.2, 1.5), 0.045, 'woodL')                               # pitchfork
    for k in (-1, 0, 1):
        m.bm_((0.95 + k * 0.05, -0.2 - k * 0.05, 1.5), (1.0 + k * 0.05, -0.15 - k * 0.05, 1.75), 0.02, 'iron', hull='none')
    obj = make('HayStack', m, ao=ao)
    col_box(obj, 0, -0.85, 0.85, -0.85, 0.85, 0, 1.8)


def build_fence(pal, ao):
    """1 m of post-and-rail fence along X (training rings, pens)."""
    m = PM(pal)
    for x0, x1 in ((-0.5, -0.43), (0.43, 0.5)):
        m.bx(x0, x1, -0.07, 0.07, 0, 1.15, 'wood', hull='noside')
    for z in (0.42, 0.85):
        m.bx(-0.43, 0.43, -0.04, 0.04, z, z + 0.12, 'woodL')
    obj = make('Fence', m, ao=ao)
    col_box(obj, 0, -0.5, 0.5, -0.08, 0.08, 0, 1.1)


def build_dummy(pal, ao):
    """Training dummy: a post on a round foot, straw body tied with rope, sack head with a straw tuft, a round
    painted target on the chest. No crossbar and no crossed foot: nothing on it reads as a cross."""
    m = PM(pal)
    m.cy((0, 0, 0), 0.4, 0.36, 0.1, 'woodD', seg=10)
    m.cy((0, 0, 0.1), 0.06, 0.05, 1.05, 'wood', seg=6)
    m.cy((0, 0, 0.95), 0.2, 0.3, 0.7, 'hay', seg=8)
    for z in (1.08, 1.5):
        m.cy((0, 0, z), 0.3, 0.3, 0.04, 'rope', seg=8, hull='none', caps=False)
    m.sp((0, 0, 1.84), 0.17, 'canvas', seg=(7, 4))
    m.bx(-0.07, 0.07, -0.18, -0.15, 1.86, 1.9, 'ink', hull='none')
    m.cy((0, 0, 1.98), 0.09, 0.03, 0.14, 'hay', seg=6)
    m.cy((0, -0.24, 1.3), 0.19, 0.19, 0.04, 'bannerR', seg=10, rot=(90, 0, 0))
    m.cy((0, -0.27, 1.3), 0.08, 0.08, 0.02, 'gold', seg=8, rot=(90, 0, 0), hull='none')
    obj = make('Dummy', m, ao=ao)
    col_box(obj, 0, -0.28, 0.28, -0.28, 0.28, 0, 1.95)


def build_rack(pal, ao):
    """Spear tub: an oak tub with iron hoops, four spears standing in it and fanning out, a round shield leaning on
    its front. (It was a rack with rails; spears crossing rails read as crosses.) Same footprint and cover box."""
    m = PM(pal)
    m.cy((0, 0, 0), 0.3, 0.36, 0.62, 'wood', seg=8)
    for z in (0.12, 0.46):
        m.cy((0, 0, z), 0.34 + z * 0.1, 0.345 + z * 0.1, 0.06, 'iron', seg=8, hull='none', caps=False)
    for (x, y) in ((-0.13, -0.06), (0.13, -0.06), (-0.07, 0.1), (0.09, 0.09)):
        tx, ty = x * 2.4, y * 2.4
        m.bm_((x, y, 0.3), (tx, ty, 1.9), 0.035, 'woodD', hull='none')
        m.cy((tx, ty, 1.88), 0.045, 0.0, 0.24, 'ironL', seg=4, hull='none')
    m.cy((0.0, -0.42, 0.32), 0.3, 0.3, 0.05, 'bannerR', seg=10, rot=(80, 0, 0))
    m.cy((0.0, -0.45, 0.325), 0.11, 0.11, 0.06, 'gold', seg=8, rot=(80, 0, 0), hull='none')
    obj = make('Rack', m, ao=ao)
    col_box(obj, 0, -0.5, 0.5, -0.3, 0.3, 0, 1.4)


def build_target(pal, ao):
    """Archery butt: straw disc on a tripod, painted rings, arrows stuck in it."""
    m = PM(pal)
    for (x, y) in ((-0.38, 0.22), (0.38, 0.22), (0, -0.32)):
        m.bm_((x, y, 0), (x * 0.3, y * 0.3 + 0.1, 1.5), 0.06, 'wood')
    m.cy((0, -0.02, 1.15), 0.52, 0.52, 0.16, 'hay', seg=14, rot=(90, 0, 0))
    for k, (r, c) in enumerate(((0.44, 'canvas'), (0.33, 'bannerR'), (0.22, 'canvas'), (0.11, 'gold'))):
        m.cy((0, -0.17 - 0.005 * k, 1.15), r, r, 0.015, c, seg=14, rot=(90, 0, 0), hull='none')
    for (x, z, a) in ((0.1, 1.2, 10), (-0.18, 1.05, -15), (0.25, 0.95, 20)):
        m.bm_((x, -0.19, z), (x + math.sin(math.radians(a)) * 0.1, -0.62, z + 0.08), 0.022, 'woodL', hull='none')
        m.bx(x - 0.04 + math.sin(math.radians(a)) * 0.1, x + 0.04 + math.sin(math.radians(a)) * 0.1, -0.62, -0.52, z + 0.03, z + 0.12, 'bannerB', hull='none')
    obj = make('Target', m, ao=ao)
    col_box(obj, 0, -0.45, 0.45, -0.35, 0.3, 0, 1.6)


def build_brazier(pal, ao):
    """Iron fire basket on a stone plinth (lights the yard; reads as a lamp post)."""
    m = PM(pal)
    m.bx(-0.32, 0.32, -0.32, 0.32, 0, 0.5, 'stoneD', bevel=True)
    m.bx(-0.36, 0.36, -0.36, 0.36, 0.5, 0.58, 'stoneL')
    m.cy((0, 0, 0.58), 0.07, 0.07, 0.9, 'iron', seg=6)
    m.cy((0, 0, 1.48), 0.12, 0.34, 0.32, 'iron', seg=8)
    m.cy((0, 0, 1.79), 0.3, 0.3, 0.02, 'woodD', seg=8, hull='none')
    flame(m, 0, 0, 1.8, 1.4)
    flame(m, 0.13, 0.08, 1.835, 0.8)
    cd.brazier_detail(m)
    obj = make('Brazier', m, ao=ao)
    col_box(obj, 0, -0.33, 0.33, -0.33, 0.33, 0, 1.9)


def build_bannerpole(pal, ao):
    """Tall pole on a stone foot with a long banner (red or blue) and a gilded finial."""
    for name, c, c2 in (('BannerPoleR', 'bannerR', 'gold'), ('BannerPoleB', 'bannerB', 'canvas')):
        m = PM(pal)
        m.bx(-0.3, 0.3, -0.3, 0.3, 0, 0.35, 'stoneD', bevel=True)
        m.cy((0, 0, 0.35), 0.06, 0.05, 5.4, 'woodD', seg=6)
        m.sp((0, 0, 5.8), 0.1, 'gold', seg=(6, 4))
        m.cy((-0.02, 0, 5.3), 0.03, 0.03, 1.05, 'woodD', seg=5, rot=(0, 90, 0))
        m.bx(0.07, 0.95, -0.025, 0.025, 2.6, 5.28, c)
        poly_y(m, [(0.07, 2.6), (0.95, 2.6), (0.51, 2.1)], -0.025, 0.025, c)
        for sy in (-1, 1):
            y0, y1 = sorted((sy * 0.025, sy * 0.034))
            m.bx(0.12, 0.9, y0, y1, 4.95, 5.05, c2, hull='none')
            poly_y(m, [(0.51, 4.6), (0.75, 4.1), (0.51, 3.4), (0.27, 4.1)], y0, y1, c2, hull='none')
        cd.bannerpole_detail(m)
        obj = make(name, m, ao=ao)
        col_box(obj, 0, -0.3, 0.3, -0.3, 0.3, 0, 2.0)


def goods(m, kind, x0, x1, y, z):
    """A row of market goods on a counter top."""
    n = int((x1 - x0) / 0.24)
    for i in range(n):
        x = x0 + 0.12 + i * (x1 - x0 - 0.24) / max(1, n - 1)
        if kind == 'veg':
            m.sp((x, y, z + 0.1), 0.11, 'cabbage' if i % 3 else 'apple', seg=(6, 4), hull='full' if i % 2 else 'none')
        elif kind == 'bread':
            m.sp((x, y, z + 0.07), 0.12, 'bread', seg=(6, 3), scale=(1.0, 0.6, 0.6))
        elif kind == 'pots':
            m.cy((x, y, z), 0.08, 0.11, 0.2, 'pot' if i % 2 else 'cheese', seg=7)
        elif kind == 'cloth':
            m.bx(x - 0.1, x + 0.1, y - 0.14, y + 0.14, z, z + 0.08 + 0.03 * (i % 2), ('clothP', 'bannerB', 'clothG', 'canvas')[i % 4])


def build_stalls(pal, ao):
    """Market stall 3 x 2 (counter along -Y): timber posts, counter with goods and baskets, striped canvas roof
    sloping back, a bunting valance. Three liveries / wares."""
    for name, stripe, wares in (('Stall_A', 'bannerR', ('veg', 'bread')), ('Stall_B', 'bannerB', ('pots', 'cloth')), ('Stall_C', 'clothG', ('bread', 'veg'))):
        m = PM(pal)
        for x in (-1.4, 1.4):
            for y in (-0.85, 0.85):
                m.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, 2.45 if y < 0 else 2.1, 'wood')
        m.bx(-1.45, 1.45, -0.95, -0.35, 0.85, 0.95, 'woodL')                               # counter top
        m.bx(-1.4, 1.4, -0.9, -0.88, 0.1, 0.85, 'wood', hull='none', cull='k')             # counter front boards
        for k in range(6):
            x = -1.17 + k * 0.47
            m.bx(x - 0.01, x + 0.01, -0.906, -0.9, 0.12, 0.83, 'woodD', hull='none', cull='k')
        goods(m, wares[0], -1.35, -0.05, -0.65, 0.95)
        goods(m, wares[1], 0.1, 1.35, -0.65, 0.95)
        m.bx(-1.4, 1.4, 0.4, 0.8, 0.0, 0.7, 'woodD', cull='b')                               # back shelf
        for x in (-0.9, 0.0, 0.9):
            m.cy((x, 0.15, 0), 0.24, 0.3, 0.38, 'rope', seg=8)                                # baskets
            m.sp((x, 0.15, 0.38), 0.2, 'apple' if x < 0 else 'cabbage', seg=(6, 3), scale=(1, 1, 0.45), hull='none')
        # sloping striped roof (front high), as one folded profile
        prof = [(-1.05, 2.55), (1.05, 2.12), (1.05, 2.04), (-1.05, 2.47)]
        m.prism(prof, -1.6, 1.6, [stripe, 'canvas'] * 4)
        # scalloped valance at the front
        for k in range(8):
            x = -1.6 + 0.2 + k * 0.4
            poly_y(m, [(x - 0.2, 2.5), (x + 0.2, 2.5), (x, 2.26)], -1.075, -1.055, stripe if k % 2 else 'canvas', hull='none')
        cd.stall_detail(m)
        obj = make(name, m, ao=ao)
        col_box(obj, 0, -1.5, 1.5, -0.98, 0.9, 0, 1.0)
        col_box(obj, 1, -1.5, 1.5, -0.98, 0.9, 2.0, 2.6)


def wheel_x(m, x, y, r, w, spokes=6):
    """Cart wheel on the X axis at x (the wheel plane), wooden rim, hub, spokes."""
    m.cy((x - w / 2, y, r), r, r, w, 'woodD', seg=12, rot=(0, 90, 0))
    m.cy((x - 0.12, y, r), 0.09, 0.09, 0.24, 'iron', seg=6, rot=(0, 90, 0))
    sx = (x - w / 2 - 0.006) if x < 0 else (x + w / 2 + 0.006)
    for k in range(spokes):
        a = k * 2 * math.pi / spokes
        c, s_ = math.cos(a), math.sin(a)
        m.bm_((sx, y + c * 0.1, r + s_ * 0.1), (sx, y + c * r * 0.8, r + s_ * r * 0.8), 0.04, 'woodL', hull='none')


def build_carts(pal, ao):
    """Two-wheeled cart 2 x 3 (shafts toward -Y): a hay cart and a barrel cart."""
    for name, load in (('Cart_Hay', 'hay'), ('Cart_Barrels', 'barrels')):
        m = PM(pal)
        for sx in (-1, 1):
            wheel_x(m, sx * 0.86, 0.25, 0.52, 0.1)
        m.bx(-0.78, 0.78, -0.75, 1.3, 0.62, 0.74, 'woodL')                                 # bed
        m.bx(-0.12, 0.12, -0.8, 1.2, 0.5, 0.62, 'woodD', cull='b')                          # axle beam
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.74, sx * 0.8))
            m.bx(x0, x1, -0.75, 1.3, 0.74, 1.12, 'wood')                                   # side boards
            m.bm_((sx * 0.45, -0.75, 0.68), (sx * 0.35, -1.48, 0.55), 0.07, 'wood')         # shafts
        m.bx(-0.74, 0.74, 1.24, 1.3, 0.74, 1.08, 'wood', cull='b')
        m.bx(-0.6, 0.6, -1.0, -0.94, 0.0, 0.5, 'woodD')                                       # prop leg board
        if load == 'hay':
            m.bx(-0.72, 0.72, -0.7, 1.24, 0.74, 1.35, 'hay', bevel=True)
            m.sp((0.0, 0.25, 1.35), 0.72, 'hay', seg=(8, 4), scale=(1.0, 1.35, 0.42))
            for y in (-0.3, 0.7):
                m.bm_((-0.75, y, 1.3), (0.75, y, 1.3), 0.03, 'rope', hull='none')
        else:
            for (x, y) in ((-0.36, -0.35), (0.36, -0.35), (-0.36, 0.42), (0.36, 0.42)):
                barrel(m, x, y, 0.74, r=0.27, h=0.66, c='wood' if x < 0 else 'woodL')
            barrel(m, 0.0, 0.92, 0.74, r=0.2, h=0.5)
            m.bm_((-0.7, 0.03, 1.36), (0.7, 0.03, 1.36), 0.03, 'rope', hull='none')
        obj = make(name, m, ao=ao)
        col_box(obj, 0, -0.98, 0.98, -0.8, 1.32, 0, 1.4)
        col_box(obj, 1, -0.5, 0.5, -1.5, -0.8, 0, 0.75)


# ================================================================ landmarks
def build_well(pal, ao):
    """Well 3 x 3: round stone drum, water, two posts with a shingled roof, windlass, rope and bucket."""
    m = PM(pal)
    ring(m, 0.82, 1.15, 0.0, 0.85, 14, 'stone')
    ring(m, 0.78, 1.22, 0.85, 0.97, 14, 'stoneL')
    m.cy((0, 0, 0.0), 0.81, 0.81, 0.45, 'water', seg=14, hull='none')
    for k in range(7):                                                                         # stone courses
        m.parent = Matrix.Rotation(k * 2 * math.pi / 7, 4, 'Z')
        m.bx(-0.16, 0.16, -1.17, -1.1, 0.2 + (k % 2) * 0.3, 0.42 + (k % 2) * 0.3, 'stoneD', hull='none', cull='k')
    m.parent = Matrix.Identity(4)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.98, sx * 1.12))
        m.bx(x0, x1, -0.08, 0.08, 0.97, 2.55, 'wood')
    m.cy((-1.05, 0, 1.75), 0.08, 0.08, 2.1, 'woodL', seg=8, rot=(0, 90, 0))                  # windlass
    m.bm_((1.05, 0, 1.75), (1.38, 0, 1.75), 0.05, 'wood')
    m.bm_((1.36, 0.06, 1.78), (1.36, 0.06, 1.45), 0.05, 'wood')
    m.cy((0.0, 0, 1.1), 0.01, 0.01, 0.65, 'rope', seg=4, hull='none')
    m.cy((0.0, 0, 0.92), 0.17, 0.2, 0.26, 'woodL', seg=8)
    for sy in (-1, 1):                                                                         # gable roof
        m.prism([(0, 3.15), (sy * 1.0, 2.45), (sy * 1.0, 2.53), (0, 3.25)], -1.3, 1.3, ['slate'])
    m.bx(-1.3, 1.3, -0.07, 0.07, 2.42, 2.58, 'woodD')
    poly_y(m, [(-0.98, 2.58), (0.98, 2.58), (0.0, 3.12)], -0.06, 0.06, 'woodL')
    m.cy((0, 0, 0.0), 1.48, 1.42, 0.12, 'cobbleD', seg=14)
    cd.well_detail(m)
    obj = make('Landmark_Well', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -1.2, 1.2, -1.2, 1.2, 0, 1.0)
    col_box(obj, 1, -1.35, 1.35, -1.0, 1.0, 2.4, 3.2)


def build_tower(pal, ao):
    """Round drum tower 5 x 5 (stands against a curtain wall): battered foot, arrow slits, a door on both faces,
    corbelled crenellated top. Tower_B carries a conical slate roof and a pennant."""
    for name, roof in (('Tower_A', False), ('Tower_B', True)):
        m = PM(pal)
        R = 2.55
        m.cy((0, 0, 0), R + 0.3, R, 1.6, 'stoneD', seg=16)
        m.cy((0, 0, 1.6), R, R, 9.2, 'stone', seg=16, caps=False)
        for z in (3.2, 5.6, 8.0):
            m.cy((0, 0, z), R + 0.012, R + 0.012, 0.04, 'mortar', seg=16, caps=False, hull='none')
        for k in range(16):                                                                    # corbels
            a = (k + 0.5) * 2 * math.pi / 16
            m.parent = Matrix.Rotation(a, 4, 'Z')
            m.bx(R - 0.05, R + 0.32, -0.12, 0.12, 10.2, 10.75, 'stoneD', cull='l')
        m.parent = Matrix.Identity(4)
        m.cy((0, 0, 10.75), R + 0.4, R + 0.4, 0.9, 'stone', seg=16)
        m.cy((0, 0, 11.65), R + 0.46, R + 0.46, 0.12, 'stoneL', seg=16)
        for k in (0, 1):                                                                       # doors (one shows)
            m.parent = Matrix.Rotation(k * math.pi, 4, 'Z')
            for a in (-0.9, 0.9):                                                              # slits
                m.parent = Matrix.Rotation(k * math.pi + a, 4, 'Z')
                m.bx(-0.07, 0.07, -R - 0.02, -R + 0.1, 4.2, 5.5, 'ink', hull='none', cull='k')
                m.bx(-0.07, 0.07, -R - 0.02, -R + 0.1, 7.1, 8.2, 'ink', hull='none', cull='k')
            m.parent = Matrix.Rotation(k * math.pi, 4, 'Z')
            m.bx(-0.62, 0.62, -R - 0.36, -R + 0.3, 0, 2.6, 'stoneL', cull='kb')
            m.bx(-0.48, 0.48, -R - 0.39, -R + 0.3, 0, 2.3, 'woodD', hull='none', cull='kb')
            for z in (0.6, 1.6):
                m.bx(-0.51, 0.51, -R - 0.41, -R - 0.385, z, z + 0.08, 'iron', hull='none', cull='k')
            m.bx(-0.3, 0.3, -R - 0.12, -R + 0.1, 6.0, 7.0, 'glassD', hull='none', cull='k')    # window
            m.bx(-0.38, 0.38, -R - 0.2, -R + 0.1, 5.9, 6.0, 'stoneL', cull='k')
        m.parent = Matrix.Identity(4)
        if roof:
            m.cy((0, 0, 11.77), R + 0.25, 0.0, 6.2, 'slate', seg=16)
            for z in (13.0, 14.6):
                t = (z - 11.77) / 6.2
                rr = (R + 0.25) * (1 - t)
                m.cy((0, 0, z), rr + 0.02, rr - 0.1, 0.12, 'slateD', seg=16, caps=False, hull='none')
            m.cy((0, 0, 17.9), 0.04, 0.03, 1.5, 'woodD', seg=5)
            poly_y(m, [(0.03, 19.3), (1.2, 19.05), (0.03, 18.8)], -0.02, 0.02, 'bannerB')
        else:
            for k in range(10):
                a = k * 2 * math.pi / 10
                m.parent = Matrix.Rotation(a, 4, 'Z')
                m.bx(-0.38, 0.38, -R - 0.42, -R + 0.1, 11.77, 12.85, 'stone', cull='b')
                m.bx(-0.41, 0.41, -R - 0.45, -R + 0.13, 12.85, 12.95, 'stoneL')
            m.parent = Matrix.Identity(4)
            m.cy((0, 0, 11.77), 0.05, 0.04, 3.2, 'woodD', seg=5)
            poly_y(m, [(0.04, 14.8), (1.25, 14.5), (0.04, 14.2)], -0.02, 0.02, 'bannerR')
        cd.tower_detail(m, R, roof)
        obj = make(name, m, ao=ao)
        col_box(obj, 0, -2.3, 2.3, -2.3, 2.3, 0, 11.0)


def build_stairs(pal, ao):
    """Stone stair 2 x 7 up to the wall walk (along Y, rising toward +Y), solid masonry steps, stringers and a
    parapet on the open side: 'Stairs' has it on +X (stands against a west wall), 'StairsL' on -X."""
    for name, s in (('Stairs', 1), ('StairsL', -1)):
        m = PM(pal)
        # the wall side keeps 0.42 m clear of the curtain's plinth, corbels and parapet
        xw0, xw1 = sorted((-s * 0.58, s * 0.95))
        for k in range(14):
            y0 = -3.5 + k * 0.5
            m.bx(xw0, xw1, y0, y0 + 0.5, 0, 0.5 * (k + 1), 'stoneL' if k % 2 else 'stone', cull='b')
        for e in (-s * 0.58, s * 0.95):
            x0, x1 = sorted((e, e + (0.05 if e > 0 else -0.05)))
            m.prism([(-3.5, 0.0), (3.5, 0.0), (3.5, 7.0), (-3.5, 0.5)], x0, x1, ['stone'], hull='none')
        x0, x1 = sorted((s * 0.95, s * 1.08))
        m.prism([(-3.5, 0.5), (3.5, 7.0), (3.5, 7.9), (-3.5, 1.4)], x0, x1, ['stone'])          # parapet
        x0, x1 = sorted((s * 0.92, s * 1.11))
        m.prism([(-3.5, 1.4), (3.5, 7.9), (3.5, 8.02), (-3.5, 1.52)], x0, x1, ['stoneL'], hull='none')
        x0, x1 = sorted((s * 0.93, s * 1.12))
        m.bx(x0, x1, -3.6, -3.35, 0, 1.6, 'stoneL')                                              # newel
        flame(m, s * 1.02, -3.47, 1.6, 0.7)
        obj = make(name, m, ao=ao)
        x0, x1 = sorted((s * -0.64, s * 1.1))
        col_box(obj, 0, x0, x1, -3.5, 3.5, 0, 7.0)


def build_keep(pal, ao):
    """The keep, 12 x 10: battered plinth, three storeys of ashlar, pilaster buttresses, round-headed windows,
    corbelled parapet, four corner turrets, a forebuilding stair to a first-floor door (front = -Y), a long banner."""
    m = PM(pal)
    W, D = 5.4, 4.4          # half sizes of the body
    m.bx(-W - 0.4, W + 0.4, -D - 0.4, D + 0.4, 0, 1.4, 'stoneD', cull='b')
    m.bx(-W, W, -D, D, 1.4, 17.0, 'stone', cull='b')
    for (cx, cy, sx, sy) in ((W, D, 1, 1), (-W, D, -1, 1), (W, -D, 1, -1), (-W, -D, -1, -1)):   # corner turrets
        x0, x1 = sorted((cx - sx * 0.9, cx + sx * 0.4))
        y0, y1 = sorted((cy - sy * 0.9, cy + sy * 0.4))
        m.bx(x0, x1, y0, y1, 1.4, 20.2, 'stone', cull='b')
        m.bx(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 20.2, 20.4, 'stoneL')
        for (px, py) in ((x0 + 0.25, y0 + 0.25), (x1 - 0.25, y0 + 0.25), (x0 + 0.25, y1 - 0.25), (x1 - 0.25, y1 - 0.25)):
            m.bx(px - 0.22, px + 0.22, py - 0.22, py + 0.22, 20.4, 21.3, 'stone', cull='b')
        m.cy(((x0 + x1) / 2, (y0 + y1) / 2, 20.4), 0.42, 0.0, 2.2, 'slate', seg=4, rot=(0, 0, 45))
    for z in (5.0, 9.6):                                                                       # string courses
        m.bx(-W - 0.08, W + 0.08, -D - 0.08, D + 0.08, z, z + 0.16, 'stoneL', hull='none')
    for z in (3.2, 7.3, 12.0, 14.2):                                                           # mortar courses
        m.bx(-W - 0.006, W + 0.006, -D - 0.006, D + 0.006, z, z + 0.04, 'mortar', hull='none')
    # corbel table and parapet on the long sides, merlons
    for sy in (-1, 1):
        y0, y1 = sorted((sy * D, sy * (D + 0.35)))
        for k in range(9):
            x = -3.6 + k * 0.9
            m.bx(x - 0.12, x + 0.12, y0, y1, 15.8, 16.3, 'stoneD')
        m.bx(-W + 0.42, W - 0.42, *sorted((sy * (D - 0.2), sy * (D + 0.38))), 16.3, 17.3, 'stone', cull='')
        for k in range(5):
            x = -3.2 + k * 1.6
            yy0, yy1 = sorted((sy * (D - 0.1), sy * (D + 0.38)))
            m.bx(x - 0.42, x + 0.42, yy0, yy1, 17.3, 18.3, 'stone', cull='b')
            m.bx(x - 0.45, x + 0.45, yy0 - 0.03, yy1 + 0.03, 18.3, 18.4, 'stoneL')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * W, sx * (W + 0.35)))
        for k in range(6):
            y = -2.6 + k * 1.04
            m.bx(x0, x1, y - 0.12, y + 0.12, 15.8, 16.3, 'stoneD')
        m.bx(*sorted((sx * (W - 0.2), sx * (W + 0.38))), -D + 0.42, D - 0.42, 16.3, 17.3, 'stone')
        for k in range(3):
            y = -1.8 + k * 1.8
            xx0, xx1 = sorted((sx * (W - 0.1), sx * (W + 0.38)))
            m.bx(xx0, xx1, y - 0.42, y + 0.42, 17.3, 18.3, 'stone', cull='b')
            m.bx(xx0 - 0.03, xx1 + 0.03, y - 0.45, y + 0.45, 18.3, 18.4, 'stoneL')
    # windows on all four faces (round-headed, dark glass, stone surround)
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        half = W if k % 2 == 0 else D
        depth = D if k % 2 == 0 else W
        xs = (-3.2, 0.0, 3.2) if k % 2 == 0 else (-2.0, 2.0)
        for x in xs:
            for (z, big) in ((6.1, False), (10.6, True)):
                if k == 0 and x == 0.0 and not big:
                    continue                                                                   # the door bay
                w, h = (0.5, 2.0) if big else (0.36, 1.4)
                poly_y(m, [(x - w - 0.14, z - 0.1), (x + w + 0.14, z - 0.1), (x + w + 0.14, z + h)] +
                       [(x + math.cos(t * math.pi / 4) * (w + 0.14), z + h + math.sin(t * math.pi / 4) * (w + 0.14)) for t in range(1, 4)] +
                       [(x - w - 0.14, z + h)], -depth - 0.05, -depth + 0.02, 'stoneL')
                poly_y(m, [(x - w, z), (x + w, z), (x + w, z + h)] +
                       [(x + math.cos(t * math.pi / 4) * w, z + h + math.sin(t * math.pi / 4) * w) for t in range(1, 4)] +
                       [(x - w, z + h)], -depth - 0.07, -depth - 0.04, 'glassD', hull='none')
                m.bx(x - 0.03, x + 0.03, -depth - 0.08, -depth - 0.06, z + 0.03, z + h, 'stoneL', hull='none', cull='k')
        for x2 in ([-2.4, 2.4] if k % 2 == 0 else [0.0]):
            m.bx(x2 - 0.06, x2 + 0.06, -depth - 0.03, -depth + 0.02, 2.4, 3.6, 'ink', hull='none', cull='k')   # slits
        # pilaster buttresses between bays
        for x in ((-1.6, 1.6) if k % 2 == 0 else ()):
            m.bx(x - 0.32, x + 0.32, -depth - 0.25, -depth + 0.02, 1.4, 15.8, 'stone', cull='kb')
    m.parent = Matrix.Identity(4)
    # forebuilding: stair from the west rising east to a door at 4.2 m on the -Y face, with a landing
    yf0, yf1 = -D - 1.7, -D
    for k in range(9):
        x0 = -4.4 + k * 0.42
        z1 = 0.47 * (k + 1)
        m.bx(x0, x0 + 0.42, yf0 + 0.15, yf1, z1 - 0.47 if k else 0.0, z1, 'stoneL' if k % 2 else 'stone', cull='b')
    m.bx(-0.62, 1.33, yf0 + 0.15, yf1, 0.0, 4.23, 'stone', cull='b')                         # landing block
    poly_y(m, [(-4.4, 0.0), (1.3, 0.0), (1.3, 4.95), (-0.62, 4.95), (-4.4, 0.95)], yf0 + 0.01, yf0 + 0.15, 'stoneD')   # outer parapet
    m.bx(-0.75, 0.75, -D - 0.07, -D + 0.02, 4.23, 6.85, 'stoneL')                           # door surround
    poly_y(m, [(-0.55, 4.24), (0.55, 4.24), (0.55, 6.0)] + [(math.cos(t * math.pi / 6) * 0.55, 6.0 + math.sin(t * math.pi / 6) * 0.55) for t in range(1, 6)] + [(-0.55, 6.0)],
           -D - 0.1, -D - 0.06, 'woodD', hull='none')
    m.bx(-0.55, 0.55, -D - 0.115, -D - 0.1, 5.0, 5.08, 'iron', hull='none', cull='k')
    flame(m, -1.05, -D - 0.3, 5.6, 0.8)
    m.bm_((-1.05, -D + 0.01, 5.2), (-1.05, -D - 0.3, 5.45), 0.05, 'iron')
    m.cy((-1.05, -D - 0.3, 5.35), 0.08, 0.06, 0.26, 'iron', seg=6)
    # great banner over the door
    m.cy((-1.05, -D - 0.45, 14.8), 0.04, 0.04, 2.1, 'iron', seg=6, rot=(0, 90, 0))
    m.bx(-0.95, 0.95, -D - 0.47, -D - 0.42, 8.3, 14.78, 'bannerR')
    poly_y(m, [(-0.95, 8.3), (0.95, 8.3), (0.0, 7.4)], -D - 0.47, -D - 0.42, 'bannerR')
    poly_y(m, [(0.0, 13.6), (0.6, 12.2), (0.0, 10.4), (-0.6, 12.2)], -D - 0.485, -D - 0.469, 'gold', hull='none')
    poly_y(m, [(0.0, 12.9), (0.28, 12.2), (0.0, 11.2), (-0.28, 12.2)], -D - 0.495, -D - 0.484, 'bannerB', hull='none')
    m.bx(-0.97, 0.97, -D - 0.49, -D - 0.469, 14.2, 14.4, 'gold', hull='none')
    # roof: low slate pyramid behind the parapet and a flagpole
    m.cy((0, 0, 17.0), 6.3, 0.0, 3.0, 'slate', seg=4, rot=(0, 0, 45), caps=False)
    m.cy((0, 0, 19.6), 0.06, 0.04, 4.0, 'woodD', seg=5)
    poly_y(m, [(0.05, 23.5), (2.2, 23.0), (0.05, 22.4)], -0.02, 0.02, 'bannerB')
    cd.keep_detail(m, W, D)
    obj = make('Landmark_Keep', m, ao=ao)
    col_box(obj, 0, -W - 0.4, W + 0.4, -D - 0.4, D + 0.4, 0, 17.0)
    col_box(obj, 1, -4.45, 1.35, -D - 1.75, -D, 0, 4.7)


def build_trebuchet(pal, ao):
    """Trebuchet 4 x 8 (training-yard landmark), cocked: wheeled base frame, braced A-frame uprights, iron axle, the
    long arm with its tip down at the back (+Y) and the counterweight crate raised at the front, sling and shot."""
    m = PM(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.15, sx * 1.45))
        m.bx(x0, x1, -3.8, 3.8, 0.45, 0.8, 'woodD')                                            # rails
        wheel_x(m, sx * 1.62, -2.9, 0.5, 0.12)
        wheel_x(m, sx * 1.62, 2.9, 0.5, 0.12)
        for y0, y1, dx in ((-2.4, 0.0, -0.06), (2.4, 0.0, 0.06)):
            m.bm_((sx * 1.3 + dx, y0, 0.8), (sx * 1.3 + dx, y1, 5.2), 0.22, 'wood')            # uprights
        m.bm_((sx * 1.3, -2.0, 1.6), (sx * 1.3, 2.0, 1.6), 0.14, 'woodL')                      # tie beam
    for y in (-3.4, 0.0, 3.4):
        m.bx(-1.45, 1.45, y - 0.15, y + 0.15, 0.8, 1.05, 'wood')                                # cross beams
    m.cy((-1.55, 0, 5.2), 0.12, 0.12, 3.1, 'iron', seg=8, rot=(0, 90, 0))                       # axle
    tip, pivot, cw = (0, 3.75, 0.95), (0, 0, 5.2), (0, -1.45, 6.88)
    m.bm_(cw, tip, 0.26, 'woodL')                                                                  # the arm
    for t in (0.3, 0.62):
        p = [cw[i] + (tip[i] - cw[i]) * t for i in range(3)]
        m.bm_((-0.16, p[1], p[2]), (0.16, p[1], p[2]), 0.3, 'iron', hull='none')                 # iron bands
    m.bx(-0.75, 0.75, -2.15, -0.75, 4.2, 5.7, 'woodD')                                           # counterweight crate
    for z in (4.45, 5.4):
        m.bx(-0.77, 0.77, -2.17, -0.73, z, z + 0.1, 'iron', hull='none')
    m.bm_((-0.5, -1.45, 5.7), (-0.05, -1.45, 6.8), 0.08, 'iron')
    m.bm_((0.5, -1.45, 5.7), (0.05, -1.45, 6.8), 0.08, 'iron')
    m.bm_((0.02, 3.75, 0.95), (0.25, 3.0, 0.2), 0.04, 'rope', hull='none')                      # sling
    m.sp((0.3, 2.9, 0.22), 0.22, 'stoneD', seg=(8, 5))
    for (x, y) in ((-0.9, -3.75), (-0.5, -3.7), (-0.7, -3.35)):
        m.sp((x, y, 0.2), 0.2, 'stone', seg=(7, 4))                                              # shot pile
    m.sp((-0.7, -3.6, 0.52), 0.2, 'stoneD', seg=(7, 4))
    m.cy((0, 0, 5.32), 0.04, 0.03, 1.5, 'woodD', seg=5)
    poly_y(m, [(0.03, 6.75), (0.9, 6.55), (0.03, 6.35)], -0.02, 0.02, 'bannerR')
    obj = make('Landmark_Trebuchet', m, ao=ao)
    col_box(obj, 0, -1.75, 1.75, -3.8, 3.8, 0, 1.1)
    col_box(obj, 1, -1.5, 1.5, -2.5, 2.5, 1.1, 6.0)


# ================================================================ backdrop (outside the walls, fogged)
def build_backdrop(pal):
    m = PM(pal)                                     # outer rampart: 34 m of high wall with two towers and a stair
    m.bx(-17, 17, -2, 2, 0, 14, 'bdWall')
    for k in range(17):
        x = -16 + k * 2
        m.bx(x - 0.55, x + 0.55, -2.2, 0.5, 14.06, 15.4, 'bdWall')
    m.bx(-17.2, 17.2, -2.3, 2.2, 13.3, 14.06, 'bdStone')
    for x in (-11, 9):
        m.cy((x, -1.0, 0), 4.0, 3.8, 19.0, 'bdStone', seg=12)
        m.cy((x, -1.0, 19.0), 4.4, 4.4, 1.2, 'bdWall', seg=12)
        m.cy((x, -1.0, 20.2), 4.0, 0.0, 6.5, 'bdSlate', seg=12)
        for z in (8, 13):
            m.bx(x - 0.15, x + 0.15, -5.2, -4.4, z, z + 1.6, 'glassD', hull='none')
    for k in range(10):                             # stair climbing the face
        m.bx(-6 + k * 1.2, -4.8 + k * 1.2, -3.2, -2.0, 0, 1.3 * (k + 1), 'bdStone')
    make('Backdrop_Rampart', m)
    m = PM(pal)                                     # tall round tower with a slate cone and a pennant
    m.cy((0, 0, 0), 5.0, 4.5, 4.0, 'bdStone', seg=12)
    m.cy((0, 0, 4), 4.4, 4.2, 22.0, 'bdWall', seg=12)
    m.cy((0, 0, 26), 5.0, 5.0, 1.6, 'bdStone', seg=12)
    m.cy((0, 0, 27.6), 4.8, 0.0, 9.0, 'bdSlate', seg=12)
    m.cy((0, 0, 36.4), 0.12, 0.1, 3.0, 'woodD', seg=5, hull='none')
    poly_y(m, [(0.1, 39.3), (3.0, 38.7), (0.1, 38.1)], -0.05, 0.05, 'bannerR')
    for z in (9, 15, 21):
        m.bx(-0.3, 0.3, -4.6, -4.0, z, z + 2.0, 'glassD', hull='none')
    make('Backdrop_Tower', m)
    m = PM(pal)                                     # rolling hills with tree clumps
    rnd = random.Random(5)
    for (x, r, h) in ((-26, 22, 12), (0, 26, 16), (24, 20, 10)):
        m.sp((x, 0, 0), r, 'hill' if x else 'hillD', seg=(12, 5), scale=(1.0, 0.45, h / r))
    for k in range(9):
        x = -34 + k * 8.5 + rnd.uniform(-2, 2)
        z = 6 + rnd.uniform(0, 6)
        m.sp((x, -6, z), 2.6, 'leafD' if k % 2 else 'leaf', seg=(7, 4), scale=(1, 1, 1.1))
    make('Backdrop_Hills', m)
    m = PM(pal)                                     # village: houses with red and slate roofs and a church spire
    for k, (x, w, h, c) in enumerate(((-16, 7, 6, 'roofR'), (-8, 6, 7, 'bdSlate'), (-1, 8, 6, 'roofR'), (7, 6, 8, 'roofR'), (14, 7, 6, 'bdSlate'))):
        m.bx(x - w / 2, x + w / 2, -3, 3, 0, h, 'plaster')
        m.prism([(-3.4, h), (3.4, h), (0, h + 3.5)], x - w / 2 - 0.3, x + w / 2 + 0.3, [c])
        for j in range(2):
            m.bx(x - w / 2 + 1.2 + j * (w - 2.4) - 0.4, x - w / 2 + 1.2 + j * (w - 2.4) + 0.4, -3.15, -2.9, 2.5, 4.0, 'glassD', hull='none')
    m.bx(19, 23, -2, 2, 0, 14, 'bdWall')
    m.cy((21, 0, 14), 2.9, 0.0, 9, 'bdSlate', seg=4, rot=(0, 0, 45))
    make('Backdrop_Village', m)


# ================================================================ build
def build_kit_castle(ao):
    pal = Palette(FAM)
    build_walls(pal, ao)
    build_floor(pal)
    build_gate(pal, ao)
    build_shutter(pal)
    build_trail(pal, ao)
    build_hatch(pal, ao)
    build_barrels(pal, ao)
    build_crates(pal, ao)
    build_hay(pal, ao)
    build_fence(pal, ao)
    build_dummy(pal, ao)
    build_rack(pal, ao)
    build_target(pal, ao)
    build_brazier(pal, ao)
    build_bannerpole(pal, ao)
    build_stalls(pal, ao)
    build_carts(pal, ao)
    build_well(pal, ao)
    build_tower(pal, ao)
    build_stairs(pal, ao)
    build_keep(pal, ao)
    build_trebuchet(pal, ao)
    build_backdrop(pal)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_castle
