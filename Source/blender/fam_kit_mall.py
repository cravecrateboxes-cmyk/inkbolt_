"""INKBOLT asset family: kit-mall ("Galleria", a two-storey shopping mall).

Two-storey storefront wall modules (9.5 m: shop glass, sign band, mezzanine fascia, upper shops, cornice), glass
balcony rails (half modules the engine links into runs, corners and ends), escalators (stair-block collision, glass
balustrades), a glass elevator shaft and its cab (the engine moves the cab), a fountain, a round Guest Services desk,
planters, benches, kiosks, food-court tables, ad pillars, bins, display stands, skylights, gate, trail wall, hatch.

Conventions (src/game/zones.js): 1 cell = 1 m; origin = centre of the cell / footprint at floor level; Blender -Y =
game +Z = the piece's front. Decks stand at 4.5 m (slab 4.1-4.5); the ceiling is at 9.5 m.
"""
import math

import bpy  # noqa: F401
from mathutils import Vector  # noqa: F401

from ib_lib import *  # noqa: F401,F403
import ib_lib
from kit_util import finish as _finish, col_box, blob

FAM = 'kit-mall'
PFX = 'KIT_MALL_'
ib_lib.GLB[FAM] = 'fps-kit-mall.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    ('stone', '#E3D8C6'), ('stone2', '#CDBFA9'), ('cream', '#F7F0E4'), ('tile', '#EFE6D6'),
    ('glass', '#A8D8F0'), ('glass2', '#7FC0E6'), ('chrome', '#CBD3DC'), ('steel', '#8E98A6'),
    ('dark', '#3E3B47'), ('rose', '#F27D8E'), ('mint', '#62C9AE'), ('gold', '#F2BE48'),
    ('sky', '#6EA6EA'), ('violet', '#AA86E2'), ('orange', '#F59A4C'), ('wood', '#C99566'),
    ('wood2', '#A87A4E'), ('leaf', '#55AE6C'), ('leaf2', '#3F915A'), ('soil', '#7A5A44'),
    ('water', '#86D0EE'), ('light', '#FFF5CF'), ('sign', '#2F2B3B'), ('terra', '#DA845C'),
    ('display', '#FBE3C8'), ('skin', '#EDE6DA'), ('step', '#5A5866'), ('yellow', '#FFD84A'),
]
TRIS = {}
SHOPS = ['rose', 'mint', 'gold', 'sky', 'violet', 'orange']
H = 9.5          # wall / ceiling height
DECK = 4.5       # mezzanine floor


def new(pal):
    return Model(pal)


def finish(name, m, ao, bevel=0.0, hull_t=0.02, cols=None):
    return _finish(PFX, TRIS, name, m, ao, bevel, hull_t, cols)


# ================================================================ walls
def shop_front(m, color, door, z0, z1, y=-0.5):
    """one storey of shop front between z0 and z1 on the face plane y (front layer 0.1 deep)"""
    m.box((0, y + 0.05, z0 + 0.075), (1.0, 0.1, 0.15), 'dark', bevel=False)                  # kick plate
    m.box((-0.47, y + 0.05, (z0 + 0.15 + z1) / 2), (0.06, 0.1, z1 - z0 - 0.15), 'dark', bevel=False)   # mullion (one per bay)
    if door:
        for sx in (-1, 1):   # double glass door panels with chrome pulls, a dark transom above
            m.box((sx * 0.22, y + 0.08, (z0 + 0.15 + z1 - 0.7) / 2), (0.4, 0.03, z1 - z0 - 0.85), 'glass2', bevel=False)
            m.box((sx * 0.05, y + 0.04, z0 + 1.1), (0.03, 0.05, 0.5), 'chrome', bevel=False)
        m.box((0, y + 0.07, z1 - 0.35), (0.88, 0.06, 0.7), 'dark', bevel=False)
    else:
        m.box((0.03, y + 0.08, (z0 + 0.15 + z1) / 2), (0.94, 0.03, z1 - z0 - 0.15), 'glass', bevel=False)
    m.box((0, y + 0.05, z1 + 0.35), (1.0, 0.1, 0.7), color, bevel=False)                     # sign band


def build_walls(pal, ao):
    for c in SHOPS:
        for door in (False, True):
            m = new(pal)
            m.box((0, 0.05, H / 2), (1.0, 0.9, H), 'stone', bevel=False)
            shop_front(m, c, door, 0.0, 3.4)
            m.box((0, -0.45, 4.3), (1.0, 0.1, 0.38), 'cream', bevel=False)                     # mezzanine fascia (inside the deck slab)
            shop_front(m, c, False, 4.5, 7.6)
            m.box((0, -0.45, 8.65), (1.0, 0.1, 0.7), 'stone2', bevel=False)                   # cornice
            m.box((0, -0.45, 9.25), (1.0, 0.1, 0.5), 'cream', bevel=False)
            finish(('ShopDoor_' if door else 'Shop_') + c, m, ao)
    # pilaster between shop fronts; corner pillar; blank side wall with an ad frame
    m = new(pal)
    m.box((0, 0.05, H / 2), (1.0, 0.9, H), 'stone', bevel=False)
    m.box((0, -0.45, H / 2), (1.0, 0.1, H), 'stone2', bevel=False)
    m.box((0, -0.53, H / 2), (0.62, 0.06, H - 0.4), 'cream', bevel=False)
    for z in (0.25, 9.0):
        m.box((0, -0.57, z), (0.74, 0.02, 0.3), 'gold', bevel=False)
    finish('Pilaster', m, ao)
    m = new(pal)
    m.box((0, 0, H / 2), (1.0, 1.0, H), 'stone2', bevel=False)
    for z in (4.3, 8.65):
        m.box((0, 0, z), (1.06, 1.06, 0.3), 'cream', bevel=False)
    finish('Corner', m, ao)
    m = new(pal)
    m.box((0, 0.05, H / 2), (1.0, 0.9, H), 'stone', bevel=False)
    m.box((0, -0.45, 2.0), (1.0, 0.1, 4.0), 'stone2', bevel=False)
    m.box((0, -0.45, 4.3), (1.0, 0.1, 0.38), 'cream', bevel=False)
    m.box((0, -0.45, 6.9), (1.0, 0.1, 4.8), 'stone2', bevel=False)
    m.box((0, -0.52, 1.8), (0.8, 0.04, 2.2), 'sign', bevel=False)
    m.box((0, -0.545, 1.8), (0.66, 0.01, 2.0), 'light', bevel=False)
    m.box((0, -0.552, 2.2), (0.5, 0.01, 0.5), 'rose', bevel=False)
    finish('Blank', m, ao)


# ================================================================ circulation
def build_rail(pal, ao):
    """half rail module: from the cell centre to the +Z (game) edge = Blender -Y; posts at the centre"""
    m = new(pal)
    m.box((0, -0.275, 0.515), (0.03, 0.45, 1.03), 'glass', bevel=False)    # starts at the post (5 cm from the centre)
    m.box((0, -0.275, 1.06), (0.08, 0.45, 0.06), 'chrome', bevel=False)
    finish('Rail', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0, 1.1)])
    m = new(pal)
    m.box((0, 0, 0.515), (0.03, 1.0, 1.03), 'glass', bevel=False)
    m.box((0, 0, 1.06), (0.08, 1.0, 0.06), 'chrome', bevel=False)
    finish('RailFull', m, ao, cols=[col_box(-0.09, -0.5, 0, 0.09, 0.5, 1.1)])
    m = new(pal)
    m.box((0, 0, 0.56), (0.1, 0.1, 1.12), 'chrome', bevel=False)
    finish('RailPost', m, ao)


def build_escalator(pal, ao):
    """2 x 10 footprint rising toward +Y (game north): bottom landing, 14 steps of 0.3214 m, top landing at 4.5 m"""
    m = new(pal)
    n, y0, y1 = 14, -5.0 + 0.9, 5.0 - 1.0
    run, rise = (y1 - y0) / n, DECK / n
    cols = [col_box(-0.84, -5.0, 0, 0.84, y0, 0.05, True)]
    m.box((0, -5.0 + 0.45, 0.025), (1.68, 0.9, 0.05), 'steel', bevel=False)
    for k in range(n):
        a, top = y0 + k * run, (k + 1) * rise
        m.box((0, a + run / 2, top / 2), (1.66, run, top), 'step', bevel=False)
        m.box((0, a + 0.03, top + 0.004), (1.6, 0.04, 0.008), 'yellow', bevel=False)
        cols.append(col_box(-0.84, a, 0, 0.84, a + run, top, True))
    m.box((0, y1 + 0.5, DECK / 2), (1.68, 1.0, DECK), 'steel', bevel=False)
    cols.append(col_box(-0.84, y1, 0, 0.84, 5.0, DECK, True))
    # side cladding (solid under the balustrades) and glass balustrades with a handrail along the step line
    for sx in (-1, 1):
        x = sx * 0.92
        for k in range(n + 2):
            if k == 0:
                a, b, top = -5.0, y0, 0.05
            elif k == n + 1:
                a, b, top = y1, 5.0, DECK
            else:
                a, b, top = y0 + (k - 1) * run, y0 + k * run, k * rise
            m.box((x, (a + b) / 2, top / 2), (0.16, b - a, top), 'cream', bevel=False)
            m.box((x, (a + b) / 2, top + 0.5), (0.04, b - a, 1.0), 'glass', bevel=False)
            m.box((x, (a + b) / 2, top + 1.03), (0.12, b - a, 0.06), 'dark', bevel=False)
            cols.append(col_box(x - 0.08, a, 0, x + 0.08, b, top + 1.06))
    finish('Escalator', m, ao, cols=cols)


def build_elevator(pal, ao):
    """3 x 3 glass shaft, open toward -Y (game +Z / the piece's front), and the cab the engine moves"""
    m = new(pal)
    top = H - 0.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((sx * 1.42, sy * 1.42, top / 2), (0.16, 0.16, top), 'chrome', bevel=False)
    for sx in (-1, 1):   # side glass (game west / east) and back glass
        m.box((sx * 1.44, 0, top / 2), (0.04, 2.68, top), 'glass', bevel=False)
    m.box((0, 1.44, top / 2), (2.68, 0.04, top), 'glass', bevel=False)
    for z in (0.08, DECK - 0.2, DECK + 2.6, top - 0.17):
        for sx in (-1, 1):
            m.box((sx * 1.42, 0, z), (0.1, 2.72, 0.12), 'chrome', bevel=False)
        m.box((0, 1.42, z), (2.72, 0.1, 0.12), 'chrome', bevel=False)
    m.box((0, -1.42, top - 0.17), (2.72, 0.1, 0.3), 'chrome', bevel=False)   # front header
    m.box((0, -1.5, top - 0.5), (1.2, 0.04, 0.3), 'sign', bevel=False)
    m.box((0, -1.525, top - 0.5), (1.0, 0.01, 0.16), 'light', bevel=False)
    cols = [col_box(-1.5, 1.36, 0, 1.5, 1.5, top), col_box(-1.5, -1.5, 0, -1.36, 1.5, top), col_box(1.36, -1.5, 0, 1.5, 1.5, top)]
    finish('Landmark_ElevatorShaft', m, ao, cols=cols)
    m = new(pal)
    iw = 1.25
    m.box((0, 0, -0.07), (2.5, 2.5, 0.26), 'steel', bevel=False)       # floor top at 0.06
    m.box((0, 0, 0.065), (2.3, 2.3, 0.01), 'tile', bevel=False)
    for sx in (-1, 1):
        m.box((sx * 1.29, 0, 0.6), (0.04, 2.44, 1.08), 'glass2', bevel=False)
        m.box((sx * 1.29, 0, 1.15), (0.08, 2.48, 0.06), 'chrome', bevel=False)
        for sy in (-1, 1):
            m.box((sx * 1.29, sy * 1.29, 1.4), (0.12, 0.12, 2.68), 'chrome', bevel=False)
    m.box((0, 1.29, 0.6), (2.44, 0.04, 1.08), 'glass2', bevel=False)
    m.box((0, 1.29, 1.15), (2.48, 0.08, 0.06), 'chrome', bevel=False)
    m.box((0, 0, 2.78), (2.66, 2.66, 0.12), 'chrome', bevel=False)
    m.box((0, 0, 2.71), (1.2, 1.2, 0.02), 'light', bevel=False)
    finish('Elevator_Cab', m, ao)


# ================================================================ props
def build_props(pal, ao):
    # small planter (1 x 1) with a fern; big planter (2 x 2) with a ficus tree, canopy above head height
    m = new(pal)
    m.cyl((0, 0, 0), 0.42, 0.46, 0.65, 'terra', seg=8, bevel=False)
    m.cyl((0, 0, 0.65), 0.38, 0.38, 0.01, 'soil', seg=8, bevel=False)
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.3
        m.beam((math.cos(a) * 0.06, math.sin(a) * 0.06, 0.62), (math.cos(a) * 0.42, math.sin(a) * 0.42, 1.15), 0.09, 'leaf2' if i % 2 else 'leaf')
    blob(m, (0, 0, 1.05), 0.28, 'leaf', seg=(7, 5))
    finish('Planter', m, ao, cols=[col_box(-0.42, -0.42, 0, 0.42, 0.42, 1.1)])
    m = new(pal)
    m.box((0, 0, 0.35), (1.8, 1.8, 0.7), 'stone2')
    m.box((0, 0, 0.71), (1.6, 1.6, 0.03), 'soil', bevel=False)
    m.cyl((0, 0, 0.7), 0.12, 0.09, 2.6, 'wood2', seg=7, bevel=False)
    for k, (x, y, z, r) in enumerate(((0, 0, 3.6, 0.9), (0.5, 0.3, 3.3, 0.6), (-0.45, -0.3, 3.35, 0.65), (0.13, -0.53, 3.93, 0.55))):
        blob(m, (x, y, z), r, 'leaf' if r > 0.6 else 'leaf2', seg=(9 + k, 6 + k % 2))
    finish('BigPlanter', m, ao, bevel=0.02, cols=[col_box(-0.9, -0.9, 0, 0.9, 0.9, 0.7)])
    # bench 2 x 1 (wood slats on stone feet), front -Y
    m = new(pal)
    for sx in (-0.75, 0.75):
        m.box((sx, 0, 0.2), (0.2, 0.5, 0.4), 'stone2', bevel=False)
    m.box((0, 0, 0.44), (1.9, 0.5, 0.06), 'wood', bevel=False)
    m.box((0, 0.24, 0.75), (1.9, 0.06, 0.4), 'wood2', bevel=False)
    for sx in (-0.75, 0.75):
        m.box((sx, 0.2, 0.475), (0.1, 0.05, 0.15), 'stone2', bevel=False)
    finish('Bench', m, ao, cols=[col_box(-0.95, -0.27, 0, 0.95, 0.27, 0.47)])
    # bin and ad pillar
    m = new(pal)
    m.cyl((0, 0, 0), 0.26, 0.26, 0.85, 'steel', seg=8, bevel=False)
    m.cyl((0, 0, 0.85), 0.28, 0.24, 0.12, 'dark', seg=8, bevel=False)
    finish('Bin', m, ao, cols=[col_box(-0.28, -0.28, 0, 0.28, 0.28, 0.97)])
    m = new(pal)
    m.box((0, 0, 1.35), (0.7, 0.7, 2.7), 'sign')
    for k, (fx, fy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        c = SHOPS[k]
        m.box((fx * 0.355, fy * 0.355, 1.5), (0.5 if fy else 0.02, 0.02 if fy else 0.5, 1.7), 'light', bevel=False)
        m.box((fx * 0.37, fy * 0.37, 1.8), (0.36 if fy else 0.01, 0.01 if fy else 0.36, 0.6), c, bevel=False)
    m.box((0, 0, 2.75), (0.78, 0.78, 0.1), 'gold', bevel=False)
    finish('AdPillar', m, ao, bevel=0.02, cols=[col_box(-0.36, -0.36, 0, 0.36, 0.36, 2.8)])
    # kiosk 3 x 2: counter cart with a striped canopy on four posts (solid as a whole)
    for name, c in (('Kiosk_A', 'rose'), ('Kiosk_B', 'mint')):
        m = new(pal)
        m.box((0, 0, 0.5), (2.6, 1.4, 1.0), 'cream')
        m.box((0, 0, 1.03), (2.7, 1.5, 0.06), 'wood', bevel=False)
        m.box((0, -0.71, 0.5), (2.2, 0.02, 0.6), c, bevel=False)
        for sx in (-1.25, 1.25):
            for sy in (-0.65, 0.65):
                m.cyl((sx, sy, 1.06), 0.04, 0.04, 1.4, 'chrome', seg=6, bevel=False)
        for k in range(6):
            m.box((-1.35 + 0.225 + k * 0.45, 0, 2.52), (0.45, 1.6, 0.12), c if k % 2 else 'paper', bevel=False)
        for k in range(3):
            m.box((-0.8 + k * 0.8, 0.1, 1.2), (0.3, 0.3, 0.3), ['gold', 'sky', 'orange'][k], bevel=False)
        finish(name, m, ao, bevel=0.015, cols=[col_box(-1.4, -0.8, 0, 1.4, 0.8, 2.6)])
    # food court table (2 x 2) with four stools
    m = new(pal)
    m.cyl((0, 0, 0.03), 0.08, 0.08, 0.69, 'chrome', seg=8, bevel=False)
    m.cyl((0, 0, 0.72), 0.55, 0.55, 0.05, 'paper', seg=16)
    m.cyl((0, 0, 0), 0.3, 0.3, 0.03, 'chrome', seg=12, bevel=False)
    for i in range(4):
        a = i / 4 * 2 * math.pi + 0.785
        x, y = math.cos(a) * 0.78, math.sin(a) * 0.78
        m.cyl((x, y, 0), 0.04, 0.04, 0.44, 'chrome', seg=6, bevel=False)
        m.cyl((x, y, 0.44), 0.18, 0.18, 0.05, SHOPS[i], seg=10)
    m.box((0.15, 0.05, 0.79), (0.18, 0.12, 0.04), 'orange', bevel=False)
    finish('FoodTable', m, ao, bevel=0.01, cols=[col_box(-0.95, -0.95, 0, 0.95, 0.95, 0.77)])
    # display stand 2 x 1: low platform with two mannequins
    m = new(pal)
    m.box((0, 0, 0.12), (1.8, 0.8, 0.24), 'cream')
    for sx, c in ((-0.45, 'rose'), (0.45, 'sky')):
        m.cyl((sx, 0, 0.24), 0.05, 0.05, 0.75, 'chrome', seg=6, bevel=False)
        m.box((sx, 0, 1.25), (0.4, 0.24, 0.6), c, rot=(0, 0, 0))
        m.box((sx, 0, 0.85), (0.34, 0.2, 0.26), 'dark', bevel=False)
        m.sphere((sx, 0, 1.66), 0.13, 'skin')
    finish('Display', m, ao, bevel=0.015, cols=[col_box(-0.9, -0.4, 0, 0.9, 0.4, 1.85)])
    # skylight (hangs under the ceiling: origin at the ceiling plane), lit panel faces down
    m = new(pal)
    m.box((0, 0, -0.125), (2.8, 2.8, 0.24), 'cream', bevel=False)   # 5 mm under the ceiling plane (wall tops share it)
    m.box((0, 0, -0.25), (2.4, 2.4, 0.01), 'light', bevel=False)
    m.box((0, 0, -0.265), (0.06, 2.4, 0.02), 'chrome', bevel=False)
    m.box((0, 0, -0.275), (2.4, 0.06, 0.02), 'chrome', bevel=False)
    finish('Skylight', m, ao)


def build_fountain(pal, ao):
    m = new(pal)
    m.cyl((0, 0, 0), 1.85, 1.85, 0.55, 'stone2', seg=20)
    m.cyl((0, 0, 0.55), 1.86, 1.86, 0.07, 'cream', seg=20, bevel=False, caps=False)
    m.cyl((0, 0, 0.55), 1.6, 1.6, 0.03, 'water', seg=20, bevel=False)
    m.cyl((0, 0, 0.58), 0.35, 0.3, 1.02, 'stone', seg=12)
    m.cyl((0, 0, 1.6), 0.95, 0.75, 0.2, 'stone2', seg=16)
    m.cyl((0, 0, 1.8), 0.8, 0.8, 0.01, 'water', seg=16, bevel=False)
    m.cyl((0, 0, 1.81), 0.15, 0.12, 0.69, 'stone', seg=8)
    m.sphere((0, 0, 2.6), 0.22, 'gold')
    for i in range(8):
        a = i / 8 * 2 * math.pi
        m.beam((math.cos(a) * 0.2, math.sin(a) * 0.2, 2.45), (math.cos(a) * 0.75, math.sin(a) * 0.75, 1.85), 0.05, 'water')
    cols = [col_box(-1.6, -1.6, 0, 1.6, 1.6, 0.6), col_box(-0.95, -0.95, 0.6, 0.95, 0.95, 1.85)]
    finish('Landmark_Fountain', m, ao, bevel=0.02, cols=cols)


def build_guestdesk(pal, ao):
    """round Guest Services desk (4 x 4): ring counter, centre column with the sign drum"""
    m = new(pal)
    m.cyl((0, 0, 0), 1.75, 1.75, 1.05, 'wood', seg=20)
    m.cyl((0, 0, 1.05), 1.82, 1.82, 0.06, 'cream', seg=20)
    m.cyl((0, 0, 0.0), 1.77, 1.77, 0.12, 'dark', seg=20, bevel=False, caps=False)
    m.cyl((0, 0, 1.11), 0.45, 0.45, 2.3, 'cream', seg=14)
    m.cyl((0, 0, 3.0), 1.2, 1.2, 0.6, 'sign', seg=18)
    m.cyl((0, 0, 3.2), 1.215, 1.215, 0.2, 'gold', seg=18, bevel=False, caps=False)
    for i in range(4):
        a = i / 4 * 2 * math.pi
        m.box((math.cos(a) * 1.75, math.sin(a) * 1.75, 0.6), (0.5, 0.5, 0.36), 'paper', rot=(0, 0, math.degrees(a)), bevel=False)
        m.box((math.cos(a + 0.6) * 1.2, math.sin(a + 0.6) * 1.2, 1.25), (0.32, 0.22, 0.22), 'dark', rot=(0, 0, math.degrees(a)), bevel=False)
    finish('Landmark_GuestDesk', m, ao, bevel=0.02, cols=[col_box(-1.8, -1.8, 0, 1.8, 1.8, 1.11), col_box(-0.5, -0.5, 0, 0.5, 0.5, 3.6)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao, bw, ht):
    m = new(pal)
    for sx in (-1, 1):
        m.box((sx * 1.72, 0, 1.75), (0.56, 0.98, 3.5), 'stone2', bevel=False)
        m.box((sx * 1.72, 0, 0.12), (0.62, 1.02, 0.24), 'dark', bevel=False)
    m.box((0, 0, 3.75), (4.0, 0.98, 0.5), 'dark', bevel=False)
    m.box((0, 0, (4.0 + H) / 2), (3.0, 0.96, H - 4.0), 'stone', bevel=False)
    for fy in (-1, 1):
        for k in range(10):
            m.box((-1.5 + (k + 0.5) * 0.3, fy * 0.5, 3.75), (0.3, 0.02 + 0.004 * (k % 2), 0.3), 'amber' if k % 2 else 'ink', bevel=False)
        m.box((0, fy * 0.5, 5.6), (2.2, 0.03, 0.9), 'sign', bevel=False)
        m.box((0, fy * 0.515, 5.6), (1.8, 0.01, 0.5), 'teal', bevel=False)
    finish('GateFrame', m, ao, bevel=bw)
    m = new(pal)
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.55 + (i + 0.5) * (Hs - 0.55) / n
        m.box((0, 0, z), (3.0, 0.12, (Hs - 0.55) / n - 0.06), 'steel' if i % 2 else 'chrome', bevel=False)
    for k in range(8):
        m.box((-1.5 + (k + 0.5) * 3 / 8, 0, 0.27), (3 / 8, 0.14, 0.5), 'ink' if k % 2 else 'amber', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.16, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor wall, 1 m along Blender Y, 0.5 thick, full height; lit ad panels on the inner face (+X)
    m = new(pal)
    m.box((0, 0, H / 2), (0.5, 1.0, H), 'stone', bevel=False)
    m.box((0.27, 0, 0.1), (0.04, 1.0, 0.2), 'dark', bevel=False)
    m.box((0.27, 0, 4.3), (0.04, 1.0, 0.4), 'cream', bevel=False)
    m.box((0.27, 0, 8.65), (0.04, 1.0, 0.7), 'stone2', bevel=False)
    m.box((0.27, 0, 2.1), (0.03, 0.8, 1.6), 'light', bevel=False)
    finish('TrailWall', m, ao)
    m = new(pal)
    m.cyl((0, 0, 0), 1.25, 1.2, 0.12, 'chrome', seg=20)
    m.cyl((0, 0, 0.12), 0.95, 0.95, 0.02, 'teal', seg=20, bevel=False)
    for i in range(6):
        a = i / 6 * math.pi * 2
        m.cyl((math.cos(a) * 1.08, math.sin(a) * 1.08, 0.12), 0.07, 0.07, 0.05, 'amber', seg=6, bevel=False)
    finish('Hatch', m, ao, bevel=0.015)


def build_kit_mall(ao):
    pal = Palette(FAM)
    bw, ht = CFG[FAM]
    build_walls(pal, ao)
    build_rail(pal, ao)
    build_escalator(pal, ao)
    build_elevator(pal, ao)
    build_props(pal, ao)
    build_fountain(pal, ao)
    build_guestdesk(pal, ao)
    build_gate(pal, ao, bw, ht)
    print('kit-mall: %d pieces, %d triangles' % (len(TRIS), sum(TRIS.values())))
    for n in sorted(TRIS, key=lambda k: -TRIS[k])[:12]:
        print('  %-40s %6d' % (n, TRIS[n]))
    export(FAM)


FAMILY = 'kit-mall'
BUILD = build_kit_mall
