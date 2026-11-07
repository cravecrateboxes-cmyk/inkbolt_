"""INKBOLT asset family: kit-police ("Strike Team HQ", a police / special-forces base).

Painted-block walls (navy wainscot, gold stripe, notice boards, interior windows), weapon wall racks (3 m pegboard:
six gun mounts the game fills with real, pickable guns of a rolled rarity), workbenches (two mod mounts), gear shelves
(two item mounts), the mod and gear meshes themselves (extended / speed mag, suppressor, compensator, long barrel,
red dot, laser, grip; vest, med kit, ammo box), lockers, sandbag barricades, ammo crates, desks, a briefing table,
a SWAT van, holding cells, a firing range (booths, targets), ceiling lights, gate, corridor wall, hatch.

Mount points are listed in src/data/themes/police.js in game prefab-local coordinates (x, height, z): a rack's guns
hang 0.28 m in front of the pegboard (Blender y = -z_game).
"""
import math

import bpy  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_util import finish as _finish, col_box

FAM = 'kit-police'
PFX = 'KIT_POLICE_'
ib_lib.GLB[FAM] = 'fps-kit-police.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    ('navy', '#2F4B7C'), ('navy2', '#253D66'), ('wall', '#BFCCDD'), ('wall2', '#A9B9CF'),
    ('concrete', '#C9C5BD'), ('concrete2', '#B1ACA3'), ('steel', '#8F9AA9'), ('steel2', '#6E7988'),
    ('olive', '#6F7B4A'), ('olive2', '#59643B'), ('sand', '#CDB680'), ('gold', '#E8B83A'),
    ('blue', '#3C7CF0'), ('peg', '#C9A97A'), ('wood', '#B98A5E'), ('black', '#2A2A31'),
    ('glass', '#A2D5EE'), ('target', '#F3EEE2'), ('orange', '#F08A3C'), ('green', '#4FA86A'),
    ('cork', '#C7955E'), ('light', '#FFF6D6'), ('rubber', '#3A3940'), ('yellow', '#F7D23E'),
]
TRIS = {}
H = 4.0


def new(pal):
    return Model(pal)


def finish(name, m, ao, bevel=0.0, hull_t=0.02, cols=None):
    return _finish(PFX, TRIS, name, m, ao, bevel, hull_t, cols)


# ================================================================ walls (front = -Y, 0.1 m front layer inside the cell)
def wall_base(m):
    m.box((0, 0.05, H / 2), (1.0, 0.9, H), 'concrete', bevel=False)
    m.box((0, -0.45, 0.55), (1.0, 0.1, 1.1), 'navy', bevel=False)
    m.box((0, -0.45, 1.15), (1.0, 0.1, 0.1), 'gold', bevel=False)
    m.box((0, -0.45, 2.6), (1.0, 0.1, 2.8), 'wall', bevel=False)


def build_walls(pal, ao):
    m = new(pal); wall_base(m); finish('Wall_A', m, ao)
    m = new(pal); wall_base(m)
    m.box((0, -0.52, 2.35), (0.72, 0.04, 0.95), 'cork', bevel=False)          # notice board with pinned sheets
    for k, (x, z, c) in enumerate(((-0.18, 2.5, 'target'), (0.17, 2.2, 'paper'), (0.05, 2.62, 'yellow'))):
        m.box((x, -0.543 - 0.003 * k, z), (0.24, 0.006, 0.3), c, bevel=False)
    finish('Wall_Board', m, ao)
    m = new(pal); wall_base(m)
    m.box((0, -0.52, 2.5), (0.7, 0.04, 0.7), 'navy2', bevel=False)          # badge plaque: gold disc, navy core
    m.cyl((0, -0.54, 2.5), 0.25, 0.25, 0.02, 'gold', seg=10, rot=(90, 0, 0), bevel=False)
    m.cyl((0, -0.56, 2.5), 0.12, 0.12, 0.01, 'navy', seg=10, rot=(90, 0, 0), bevel=False)
    finish('Wall_Badge', m, ao)
    m = new(pal)
    m.box((0, 0.05, H / 2), (1.0, 0.9, H), 'concrete', bevel=False)
    m.box((0, -0.45, 0.55), (1.0, 0.1, 1.1), 'navy', bevel=False)
    m.box((0, -0.45, 1.15), (1.0, 0.1, 0.1), 'gold', bevel=False)
    m.box((0, -0.45, 1.3), (1.0, 0.1, 0.2), 'wall', bevel=False)
    m.box((-0.46, -0.45, 2.15), (0.08, 0.1, 1.5), 'steel2', bevel=False)
    m.box((0.04, -0.43, 2.15), (0.92, 0.03, 1.5), 'glass', bevel=False)
    m.box((0, -0.45, 3.45), (1.0, 0.1, 1.1), 'wall', bevel=False)
    finish('Wall_Window', m, ao)
    m = new(pal)
    m.box((0, 0, H / 2), (1.0, 1.0, H), 'concrete2', bevel=False)
    m.box((0, 0, 0.54), (1.04, 1.04, 1.08), 'navy2', bevel=False)
    finish('Corner', m, ao)


# ================================================================ armory furniture (mount pieces)
def build_rack(pal, ao):
    """3 x 1 weapon wall rack: pegboard 1 cm off the wall (+Y), guns hang at x = -0.7, 0.7 and heights 1.55 / 0.95"""
    m = new(pal)
    m.box((0, 0.45, 1.2), (2.88, 0.08, 2.0), 'peg', bevel=False)
    m.box((0, 0.435, 2.25), (3.0, 0.11, 0.1), 'steel2', bevel=False)
    m.box((0, 0.435, 0.15), (3.0, 0.11, 0.1), 'steel2', bevel=False)
    for sx in (-1.47, 1.47):
        m.box((sx, 0.435, 1.2), (0.06, 0.11, 2.0), 'steel2', bevel=False)
    for x in (-0.7, 0.7):
        for z in (1.55, 0.95):
            for px in (-0.3, 0.3):
                m.box((x + px, 0.38, z - 0.04), (0.05, 0.06, 0.05), 'black', bevel=False)   # studs behind the gun
            m.box((x, 0.405, z - 0.2), (0.4, 0.01, 0.07), 'paper', bevel=False)              # label strip
    m.box((0, 0.405, 2.0), (1.2, 0.01, 0.16), 'navy', bevel=False)
    finish('WeaponRack', m, ao, cols=[col_box(-1.5, 0.2, 0, 1.5, 0.5, 2.3)])


def build_bench(pal, ao):
    """2 x 1 workbench: mods lie on the top at x = +-0.55 (height 0.9)"""
    m = new(pal)
    m.box((0, 0, 0.87), (1.9, 0.86, 0.06), 'wood', bevel=False)
    for sx in (-0.88, 0.88):
        for sy in (-0.36, 0.36):
            m.box((sx, sy, 0.42), (0.06, 0.06, 0.84), 'steel2', bevel=False)
    m.box((0, 0, 0.25), (1.7, 0.66, 0.04), 'steel', bevel=False)
    m.box((0, 0.3, 0.97), (0.16, 0.14, 0.14), 'blue', bevel=False)            # vice
    m.box((0, 0.28, 1.06), (0.2, 0.06, 0.04), 'steel2', bevel=False)
    finish('Workbench', m, ao, cols=[col_box(-0.95, -0.43, 0, 0.95, 0.43, 0.9)])


def build_shelf(pal, ao):
    """2 x 1 gear shelf against the wall: items stand on the middle shelf (height 1.03) at x = +-0.5"""
    m = new(pal)
    for sx in (-0.97, 0.97):
        for sy in (-0.02, 0.46):
            m.box((sx, sy, 1.0), (0.05, 0.05, 2.0), 'steel2', bevel=False)
    for z in (0.35, 1.0, 1.65):
        m.box((0, 0.22, z), (1.88, 0.52, 0.03), 'steel', bevel=False)
    m.box((0, 0.48, 1.0), (1.86, 0.02, 1.96), 'steel2', bevel=False)
    for k, (x, c) in enumerate(((-0.6, 'olive'), (-0.1, 'olive2'), (0.4, 'navy'))):   # stored boxes, bottom / top shelves
        m.box((x, 0.25, 0.53), (0.4, 0.4, 0.33), c, bevel=False)
        m.box((x + 0.12, 0.25, 1.81), (0.36, 0.38, 0.29), ['sand', 'olive', 'black'][k], bevel=False)
    finish('GearShelf', m, ao, cols=[col_box(-1.0, -0.05, 0, 1.0, 0.5, 2.0)])


def build_mods(pal, ao):
    """mods and gear rest on their origin (bottom centre), long axis along X, about 0.3-0.45 m"""
    m = new(pal)
    m.box((0, 0, 0.03), (0.34, 0.12, 0.06), 'black', bevel=False)
    m.box((0.02, 0, 0.09), (0.3, 0.1, 0.06), 'steel2', bevel=False)
    m.box((-0.145, 0, 0.095), (0.04, 0.11, 0.06), 'orange', bevel=False)
    finish('Mod_extmag', m, ao)
    m = new(pal)
    m.box((0, 0, 0.04), (0.2, 0.11, 0.08), 'black', bevel=False)
    m.box((0.12, 0, 0.04), (0.04, 0.06, 0.05), 'orange', bevel=False)
    finish('Mod_speedmag', m, ao)
    m = new(pal)
    m.cyl((-0.17, 0, 0.06), 0.06, 0.06, 0.34, 'black', seg=10, rot=(0, 90, 0), bevel=False)
    m.cyl((-0.2, 0, 0.06), 0.045, 0.045, 0.03, 'steel', seg=10, rot=(0, 90, 0), bevel=False)
    finish('Mod_suppressor', m, ao)
    m = new(pal)
    m.cyl((-0.1, 0, 0.05), 0.05, 0.05, 0.2, 'steel2', seg=8, rot=(0, 90, 0), bevel=False)
    for k in (-0.04, 0.03):
        m.box((k, 0, 0.1), (0.03, 0.04, 0.012), 'black', bevel=False)
    finish('Mod_compensator', m, ao)
    m = new(pal)
    m.cyl((-0.22, 0, 0.035), 0.035, 0.035, 0.44, 'steel2', seg=8, rot=(0, 90, 0), bevel=False)
    m.cyl((0.22, 0, 0.035), 0.045, 0.045, 0.04, 'black', seg=8, rot=(0, 90, 0), bevel=False)
    finish('Mod_longbarrel', m, ao)
    m = new(pal)
    m.box((0, 0, 0.025), (0.16, 0.08, 0.05), 'black', bevel=False)
    m.box((0, 0, 0.1), (0.12, 0.09, 0.1), 'steel2', bevel=False)
    m.box((-0.0625, 0, 0.1), (0.005, 0.06, 0.06), 'red', bevel=False)
    finish('Mod_reddot', m, ao)
    m = new(pal)
    m.box((0, 0, 0.04), (0.18, 0.08, 0.08), 'olive2', bevel=False)
    m.cyl((-0.11, 0, 0.05), 0.02, 0.02, 0.03, 'red', seg=8, rot=(0, 90, 0), bevel=False)
    finish('Mod_laser', m, ao)
    m = new(pal)
    m.box((0, 0, 0.02), (0.14, 0.06, 0.04), 'black', bevel=False)
    m.box((0, 0, 0.13), (0.06, 0.07, 0.18), 'rubber', bevel=False)
    finish('Mod_grip', m, ao)
    m = new(pal)   # vest standing upright, front toward -Y
    m.box((0, 0, 0.22), (0.4, 0.12, 0.44), 'navy', bevel=False)
    for sx in (-0.13, 0.13):
        m.box((sx, 0, 0.47), (0.1, 0.11, 0.06), 'navy2', bevel=False)
    m.box((0, -0.065, 0.3), (0.28, 0.01, 0.08), 'paper', bevel=False)
    for k in range(3):
        m.box((-0.12 + k * 0.12, -0.07, 0.12), (0.09, 0.03, 0.1), 'navy2', bevel=False)
    finish('Item_vest', m, ao)
    m = new(pal)
    m.box((0, 0, 0.11), (0.34, 0.14, 0.22), 'white', bevel=False)
    m.box((0, -0.072, 0.11), (0.12, 0.004, 0.04), 'red', bevel=False)
    m.box((0, -0.072, 0.15), (0.04, 0.004, 0.04), 'red', bevel=False)
    m.box((0, -0.072, 0.07), (0.04, 0.004, 0.04), 'red', bevel=False)
    m.box((0, 0, 0.235), (0.12, 0.04, 0.03), 'steel2', bevel=False)
    finish('Item_medkit', m, ao)
    m = new(pal)
    m.box((0, 0, 0.12), (0.32, 0.16, 0.24), 'olive', bevel=False)
    m.box((0, 0, 0.255), (0.3, 0.14, 0.03), 'olive2', bevel=False)
    m.box((0, 0, 0.29), (0.14, 0.03, 0.04), 'black', bevel=False)
    m.box((0, -0.0815, 0.12), (0.16, 0.003, 0.06), 'yellow', bevel=False)
    finish('Item_ammobox', m, ao)


# ================================================================ other props
def build_props(pal, ao):
    m = new(pal)   # locker, front -Y
    m.box((0, 0.1, 1.0), (0.9, 0.7, 2.0), 'steel', bevel=False)
    m.box((0, -0.26, 1.0), (0.004 + 0.02, 0.02, 1.9), 'black', bevel=False)
    for sx in (-0.22, 0.22):
        m.box((sx, -0.255, 1.65), (0.3, 0.01, 0.2), 'steel2', bevel=False)
        m.box((sx + (0.11 if sx < 0 else -0.11), -0.265, 1.05), (0.03, 0.02, 0.12), 'black', bevel=False)
    finish('Locker', m, ao, cols=[col_box(-0.45, -0.25, 0, 0.45, 0.45, 2.0)])
    m = new(pal)   # sandbags, one run module (wall along X): two bags, one long bag, two bags
    for row, (z, n) in enumerate(((0.16, 2), (0.46, 1), (0.76, 2))):
        d = 0.6 - row * 0.08
        for k in range(n):
            x = 0.0 if n == 1 else -0.25 + k * 0.5
            m.box((x, 0, z), (0.96 if n == 1 else 0.48, d, 0.28), 'sand' if (row + k) % 2 else 'olive', bevel=False)
    finish('Sandbags', m, ao, bevel=0.0, cols=[col_box(-0.5, -0.3, 0, 0.5, 0.3, 0.92)])
    m = new(pal)   # ammo crate
    m.box((0, 0, 0.36), (0.9, 0.7, 0.72), 'olive', bevel=False)
    m.box((0, -0.355, 0.4), (0.5, 0.01, 0.16), 'yellow', bevel=False)
    m.box((0, 0, 0.735), (0.92, 0.72, 0.03), 'olive2', bevel=False)
    finish('Crate', m, ao, cols=[col_box(-0.46, -0.36, 0, 0.46, 0.36, 0.75)])
    m = new(pal)   # desk 2 x 1 with monitor
    m.box((0, 0, 0.74), (1.9, 0.8, 0.05), 'wood', bevel=False)
    for sx in (-0.9, 0.9):
        m.box((sx, 0, 0.36), (0.06, 0.76, 0.72), 'steel2', bevel=False)
    m.box((0.3, 0.15, 1.05), (0.55, 0.05, 0.36), 'black', bevel=False)
    m.box((0.3, 0.121, 1.05), (0.49, 0.004, 0.3), 'blue', bevel=False)
    m.box((0.3, 0.2, 0.85), (0.08, 0.06, 0.16), 'black', bevel=False)
    m.box((-0.2, -0.15, 0.775), (0.5, 0.18, 0.02), 'black', bevel=False)
    finish('Desk', m, ao, cols=[col_box(-0.95, -0.4, 0, 0.95, 0.4, 1.23)])
    m = new(pal)   # briefing table 4 x 2 with chairs
    m.box((0, 0, 0.76), (3.6, 1.4, 0.06), 'wood', bevel=False)
    for sx in (-1.6, 1.6):
        m.box((sx, 0, 0.37), (0.12, 1.1, 0.74), 'steel2', bevel=False)
    for k in range(4):
        for sy in (-1, 1):
            x = -1.2 + k * 0.8
            m.box((x, sy * 0.88, 0.45), (0.42, 0.38, 0.06), 'navy', bevel=False)
            m.box((x, sy * 1.05, 0.72), (0.4, 0.05, 0.5), 'navy2', bevel=False)
            m.box((x, sy * 0.88, 0.21), (0.06, 0.06, 0.42), 'steel2', bevel=False)
    m.box((0, 0, 0.8), (1.0, 0.6, 0.02), 'paper', bevel=False)
    finish('BriefTable', m, ao, cols=[col_box(-1.85, -1.0, 0, 1.85, 1.0, 0.82)])
    m = new(pal)   # potted plant
    m.cyl((0, 0, 0), 0.3, 0.26, 0.5, 'concrete2', seg=8, bevel=False)
    m.sphere((0, 0, 0.9), 0.36, 'green', seg=(8, 6))
    m.cyl((0, 0, 0.5), 0.04, 0.04, 0.3, 'wood', seg=5, bevel=False)
    finish('Plant', m, ao, cols=[col_box(-0.32, -0.32, 0, 0.32, 0.32, 1.2)])
    m = new(pal)   # filing cabinet, front -Y
    m.box((0, 0.1, 0.7), (0.6, 0.7, 1.4), 'steel', bevel=False)
    for k in range(3):
        m.box((0, -0.255, 0.3 + k * 0.42), (0.5, 0.01, 0.34), 'steel2', bevel=False)
        m.box((0, -0.265, 0.4 + k * 0.42), (0.16, 0.02, 0.03), 'black', bevel=False)
    finish('Cabinet', m, ao, cols=[col_box(-0.3, -0.25, 0, 0.3, 0.45, 1.4)])
    m = new(pal)   # firing-range booth partition (run module) and paper target on a stand
    m.box((0, 0, 0.75), (1.0, 0.08, 1.5), 'steel', bevel=False)
    m.box((0, 0, 1.53), (1.0, 0.12, 0.06), 'black', bevel=False)
    finish('Booth', m, ao, cols=[col_box(-0.5, -0.06, 0, 0.5, 0.06, 1.56)])
    m = new(pal)
    m.box((0, 0, 0.6), (0.06, 0.06, 1.2), 'black', bevel=False)
    m.box((0, 0, 0.03), (0.4, 0.3, 0.06), 'steel2', bevel=False)
    m.box((0, -0.04, 1.5), (0.5, 0.01, 0.7), 'target', bevel=False)
    m.box((0, -0.048, 1.62), (0.18, 0.006, 0.18), 'black', bevel=False)
    m.box((0, -0.048, 1.32), (0.28, 0.006, 0.28), 'black', bevel=False)
    m.box((0, -0.052, 1.32), (0.1, 0.004, 0.1), 'red', bevel=False)
    finish('Target', m, ao, cols=[col_box(-0.26, -0.15, 0, 0.26, 0.15, 1.85)])
    m = new(pal)   # ceiling light (origin on the ceiling plane)
    m.box((0, 0, -0.045), (1.2, 0.5, 0.08), 'steel', bevel=False)    # 5 mm under the ceiling plane (wall tops share it)
    m.box((0, 0, -0.09), (1.1, 0.4, 0.01), 'light', bevel=False)
    finish('CeilLight', m, ao)
    m = new(pal)   # floor emblem 4 x 4 (flat, on top of the floor lines)
    m.cyl((0, 0, 0), 1.7, 1.7, 0.02, 'navy', seg=24, bevel=False)
    m.cyl((0, 0, 0.02), 1.45, 1.45, 0.006, 'gold', seg=24, bevel=False)
    m.cyl((0, 0, 0.026), 1.3, 1.3, 0.006, 'navy2', seg=24, bevel=False)
    for i in range(5):   # star arms, each 3 mm above the last
        a = math.pi / 2 + i * 2 * math.pi / 5
        m.box((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.035 + 0.003 * i), (1.1, 0.22, 0.003), 'gold', rot=(0, 0, math.degrees(a)), bevel=False)
    finish('Emblem', m, ao, hull_t=0.0)


def build_landmarks(pal, ao):
    m = new(pal)   # SWAT van 3 x 6, nose toward -Y
    m.box((0, 0.3, 1.45), (2.3, 4.6, 1.9), 'navy', bevel=False)
    m.box((0, -2.35, 1.01), (2.2, 1.1, 0.98), 'navy', bevel=False)
    m.box((0, -2.0, 1.85), (2.1, 0.5, 0.7), 'glass', bevel=False, rot=(-30, 0, 0))
    m.box((0, -2.92, 0.75), (2.0, 0.04, 0.4), 'black', bevel=False)
    for sx in (-1.152, 1.152):
        m.box((sx, 0.6, 1.45), (0.004, 2.6, 0.5), 'paper', bevel=False)
        m.box((sx, -1.2, 1.75), (0.004, 0.8, 0.5), 'glass', bevel=False)
    for sx in (-1.33, 1.03):   # cylinders extend +X from their base: left wheels start further out
        for sy in (-2.0, 1.7):
            m.cyl((sx, sy, 0.42), 0.42, 0.42, 0.3, 'rubber', seg=12, rot=(0, 90, 0), bevel=False)
    m.box((0, -0.2, 2.47), (1.4, 0.3, 0.14), 'black', bevel=False)
    m.box((-0.4, -0.2, 2.58), (0.5, 0.26, 0.1), 'blue', bevel=False)
    m.box((0.4, -0.2, 2.58), (0.5, 0.26, 0.1), 'red', bevel=False)
    finish('Landmark_Van', m, ao, cols=[col_box(-1.34, -2.95, 0, 1.34, 2.6, 2.5)])
    m = new(pal)   # holding cell 4 x 3: bars along the front (-Y), solid back and sides, bench inside
    m.box((0, 1.44, 1.45), (3.8, 0.1, 2.9), 'concrete', bevel=False)
    for sx in (-1.95, 1.95):
        m.box((sx, 0, 1.5), (0.1, 2.8, 3.0), 'concrete', bevel=False)
    m.box((0, 0, 2.95), (3.8, 2.8, 0.1), 'concrete2', bevel=False)
    for k in range(17):
        m.cyl((-1.8 + k * 0.225, -1.4, 0), 0.025, 0.025, 2.9, 'steel2', seg=6, bevel=False)
    m.box((0, -1.4, 1.2), (3.8, 0.06, 0.06), 'steel2', bevel=False)
    m.box((0, 1.15, 0.45), (2.6, 0.5, 0.08), 'wood', bevel=False)
    m.box((0, -1.47, 2.6), (0.8, 0.02, 0.22), 'gold', bevel=False)
    finish('Landmark_Cells', m, ao, cols=[col_box(-2.0, -1.45, 0, 2.0, 1.5, 3.0)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao, bw, ht):
    m = new(pal)
    for sx in (-1, 1):
        m.box((sx * 1.72, 0, 1.75), (0.56, 0.98, 3.5), 'steel2', bevel=False)
    m.box((0, 0, 3.745), (4.0, 0.98, 0.49), 'black', bevel=False)   # top 1 cm under the 4 m wall tops beside it
    for fy in (-1, 1):
        for k in range(10):
            m.box((-1.5 + (k + 0.5) * 0.3, fy * 0.5, 3.745), (0.3, 0.02 + 0.004 * (k % 2), 0.3), 'yellow' if k % 2 else 'ink', bevel=False)
    finish('GateFrame', m, ao, bevel=bw)
    m = new(pal)
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.55 + (i + 0.5) * (Hs - 0.55) / n
        m.box((0, 0, z), (3.0, 0.12, (Hs - 0.55) / n - 0.06), 'steel' if i % 2 else 'steel2', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.14, 0.5), 'ink' if k % 2 else 'yellow', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.16, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    m = new(pal)   # corridor wall: 1 m along Y, inner face +X
    m.box((0, 0, H / 2), (0.5, 1.0, H), 'concrete', bevel=False)
    m.box((0.27, 0, 0.55), (0.04, 1.0, 1.1), 'navy', bevel=False)
    m.box((0.27, 0, 1.15), (0.04, 1.0, 0.1), 'gold', bevel=False)
    finish('TrailWall', m, ao)
    m = new(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'steel2', seg=20)
    m.cyl((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, bevel=False)
    finish('Hatch', m, ao, bevel=0.015)


def build_kit_police(ao):
    pal = Palette(FAM)
    bw, ht = CFG[FAM]
    build_walls(pal, ao)
    build_rack(pal, ao)
    build_bench(pal, ao)
    build_shelf(pal, ao)
    build_mods(pal, ao)
    build_props(pal, ao)
    build_landmarks(pal, ao)
    build_gate(pal, ao, bw, ht)
    print('kit-police: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:10]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-police'
BUILD = build_kit_police
