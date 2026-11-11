"""INKBOLT asset family: kit-highrise (Zenith Command: the Zenith Tactical Response Unit's HQ on the top floors of a
skyscraper, and the roofs round it; campaign level 25, the final level).

Built off the office / spire kits (fam_kit_office.Kit through fam_kit_spire.SKit: outlined + flat shapes, z-fight
check, collision empties, walkable boxes): office furniture helpers (chairs, monitors, plants) and the spire's skyline
towers are reused with this family's palette, which keeps their colour names.

Look: high-tech and cold: dark slate and gunmetal, white stone in the lobby, cyan LED lines, lit glass gun cases,
biometric locks, video walls; outside a pale blue haze over the city 240 m down. On the roof: grey membrane, gravel,
galvanised plant (HVAC units with fans, cooling towers), a wooden water tank on stilts, a concrete lift machine room,
an antenna mast, solar arrays, skylights and the window-cleaning gantry.

Conventions (src/data/themes/highrise.js, src/game/zones.js, src/game/rooftops.js):
  * 1 m = 1 ASCII cell; a piece's origin is the centre of its cell / footprint at floor level; Blender Z-up.
  * One-sided pieces face Blender -Y (game +Z, the room). Interior walls are 4.5 m tall full-cell blocks (two cells
    thick in the plans) with their detail on the -Y face; the curtain wall is open glazing (mullions, glints) so the
    city shows through.
  * Armory mounts keep the Strike Team HQ contract (see highrise.js): the gun wall's board face at y = 0.45 (guns'
    backs at 0.415), workbench mats at 0.926 (x +-0.48, y -0.18), shelf at 1.16 (x +-0.5, y 0.22); the island gun
    case's board faces at y = +-0.04 (guns' backs 3.5 cm off them).
  * Roof edges (rooftops.js): a parapet / kerb module stands on its cell's -Y edge... no: on the cell's game +Z edge,
    i.e. Blender y in [-0.5, -0.5 + t] with the outer face on y = -0.5; the L / R variants stop 0.3 m short of their
    -X / +X end (where an east / west edge meets a north / south one).
  * Planks run along local X, centred, bottom at z = 0, top at 0.08, 1.5 m wide. Fans spin about their origin (the
    theme places them at the HVAC / cooling tower fan height).
"""
import math

import bpy  # noqa: F401  (must load before bmesh/mathutils)
import bmesh
from mathutils import Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
import ib_text
import fam_kit_office as O
import fam_kit_spire as SP

FAM = 'kit-highrise'
PFX = 'KIT_HIGHRISE_'
ib_lib.GLB[FAM] = 'fps-kit-highrise.glb'
ib_lib.CFG[FAM] = (0.012, 0.014)
HULL_T = ib_lib.CFG[FAM][1]
H = 4.5          # wall / ceiling height
srt = O.srt

ib_lib.PALETTES[FAM] = BASE + [
    # office / spire names (furniture, skyline) re-tinted cold
    ('mullion', '#23272E'), ('graphite', '#2F343C'), ('graphite2', '#4A515C'), ('steel', '#B7C0CB'),
    ('steel2', '#8D97A4'), ('steelDark', '#646D79'), ('glow', '#E8F8FF'), ('screen', '#66C8F0'),
    ('screen2', '#1B3550'), ('black', '#1C1F25'), ('chair', '#2E333B'), ('chairMesh', '#48505C'),
    ('leaf', '#4FA866'), ('leaf2', '#317F4C'), ('pot', '#E6E8EA'), ('soil', '#5A4636'),
    ('trunk', '#7A5A40'), ('glint', '#F2FBFF'), ('stone', '#DADDE0'), ('stone2', '#B9BEC4'),
    ('gold', '#F2C14E'),
    ('twGlass', '#8FB3D1'), ('twDark', '#4D6178'), ('twSand', '#D8C4A2'), ('twWhite', '#E7E4DE'),
    ('twWin', '#5A6E86'), ('twGreen', '#9CC7BE'),
    # Zenith Command
    ('slate', '#3A4350'), ('slate2', '#2C333D'), ('panel', '#4F5A68'), ('cyan', '#36D1E0'), ('cyanD', '#1E8C9C'),
    ('blue', '#3F7BEA'), ('walnut', '#6E4A33'), ('walnut2', '#4E3424'), ('carpet', '#3A4A63'), ('carpet2', '#33425A'),
    ('rubber', '#4A525E'), ('rubber2', '#414852'), ('tile', '#6C7581'), ('tile2', '#5F6773'), ('olive', '#66724C'),
    ('orange', '#F08A2E'), ('yellow', '#F4C531'), ('green', '#47C27A'), ('frost', '#DCE8F0'), ('holo', '#7FF0FF'),
    # roof
    ('membrane', '#8C9198'), ('gravel', '#A99C86'), ('concrete', '#A4A7AA'), ('concrete2', '#868A8F'),
    ('wood', '#B98A55'), ('wood2', '#8E6538'), ('solar', '#26365A'), ('galv', '#C3C9CF'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])


class HKit(SP.SKit):
    """The spire's kit with this family's prefix."""

    def finish(self, name, bevel=0.0, ao=False):
        old = SP.PFX
        SP.PFX = PFX
        try:
            return SP.SKit.finish(self, name, bevel, ao)
        finally:
            SP.PFX = old


def glint_y(k, x, y, z0, h, s=-1, w=0.07):
    for (dx, ww) in ((0.0, w), (0.16, w * 0.45)):
        a = x + dx
        k.poly([(a, y, z0), (a + ww, y, z0), (a + ww + h * 0.45, y, z0 + h), (a + h * 0.45, y, z0 + h)], 'glint', (0, s, 0))


def text(k, s, x, y, z, cap, c, face='y-', font='display', maxw=None, align='c', valign='b'):
    ib_text.draw(k, s, x, y, z, cap, c, face=face, font=font, maxw=maxw, align=align, valign=valign)


def star(k, cx, y, cz, r, c, face=-1, inner=0.42, a0=math.pi / 2):
    """five-point star painted on a wall plane at y (normal face * Y)"""
    P = [((r if i % 2 == 0 else r * inner) * math.cos(a0 + i * math.pi / 5), (r if i % 2 == 0 else r * inner) * math.sin(a0 + i * math.pi / 5)) for i in range(10)]
    for i in range(10):   # fan of triangles round the centre (one flat shape per triangle keeps the poly convex)
        j = (i + 1) % 10
        k.poly([(cx, y, cz), (cx + P[i][0], y, cz + P[i][1]), (cx + P[j][0], y, cz + P[j][1])], c, (0, face, 0))


def star_up(k, cx, cy, z, r, c, inner=0.42):
    P = [((r if i % 2 == 0 else r * inner) * math.cos(math.pi / 2 + i * math.pi / 5), (r if i % 2 == 0 else r * inner) * math.sin(math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    for i in range(10):
        j = (i + 1) % 10
        k.poly([(cx, cy, z), (cx + P[i][0], cy + P[i][1], z), (cx + P[j][0], cy + P[j][1], z)], c, (0, 0, 1))


# ================================================================ interior walls (room toward -Y)
# style: block colour, skirting, (z0, z1, colour) face bands drawn as flat quads 3 mm proud, LED line height
STY = {
    'L': ('stone', 'graphite', [(0.15, 1.0, 'stone2')], 3.95),
    'B': ('slate2', 'walnut2', [(0.15, 1.05, 'walnut'), (1.12, 4.2, 'carpet')], 4.25),
    'A': ('slate', 'black', [(0.12, 1.2, 'slate2'), (1.27, 4.2, 'panel')], 1.22),
    'S': ('black', 'graphite', [(0.12, 0.85, 'graphite'), (0.95, 4.2, 'graphite2')], 0.9),
    'O': ('graphite', 'black', [(0.15, 4.15, 'screen2')], 4.22),
}
LED = {'L': 'cyan', 'B': 'blue', 'A': 'cyan', 'S': 'orange', 'O': 'cyan'}


def wall_base(k, S, lamp=False):
    base, skirt, bands, led = STY[S]
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, base)
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.12, skirt, ink=False)
    for (z0, z1, c) in bands:
        k.qy(-0.47, 0.47, z0, z1, -0.503, -1, c)
    if S == 'B':      # acoustic panel joints
        k.qy(-0.012, 0.012, 1.12, 4.2, -0.506, -1, 'carpet2')
    if S == 'S':      # padded squares
        for z in (1.75, 2.6, 3.45):
            k.qy(-0.47, 0.47, z - 0.015, z + 0.015, -0.506, -1, 'black')
        k.qy(-0.015, 0.015, 0.95, 4.2, -0.509, -1, 'black')
    if S == 'A':
        k.qy(-0.012, 0.012, 1.27, 4.2, -0.506, -1, 'slate2')
    if S == 'O':
        for z in (1.4, 2.8):
            k.qy(-0.47, 0.47, z - 0.006, z + 0.006, -0.506, -1, 'cyanD')
    k.bx(-0.5, 0.5, -0.53, -0.5, H - 0.25, H, 'graphite2' if S != 'L' else 'graphite', ink=False)   # cornice / shadow gap
    k.qy(-0.5, 0.5, led - 0.02, led + 0.02, -0.509, -1, LED[S])
    if lamp:          # wall washer: a slim vertical light bar
        k.bx(-0.06, 0.06, -0.58, -0.49, 1.6, 3.4, 'graphite')
        k.qy(-0.035, 0.035, 1.65, 3.35, -0.583, -1, 'glow')


def corner(k, S):
    k.begin()
    base, skirt, _, led = STY[S]
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, base)
    return k


def door(k, S):
    """a closed sliding door with a glass slit and a bio panel, in a gunmetal frame (the wall bands round it)"""
    k.begin()
    wall_base(k, S)
    k.bx(-0.48, 0.48, -0.56, -0.49, 0, 2.5, 'graphite')
    k.bx(-0.4, 0.4, -0.575, -0.56, 0.02, 2.4, 'steel2')
    k.qy(-0.07, 0.07, 1.0, 2.1, -0.578, -1, 'frost')
    k.qy(-0.4, 0.4, 0.02, 0.12, -0.578, -1, 'steelDark')
    k.bx(0.24, 0.34, -0.6, -0.575, 1.05, 1.3, 'black', ink=False)
    k.qy(0.26, 0.32, 1.18, 1.26, -0.603, -1, 'green')
    k.qy(0.26, 0.32, 1.08, 1.14, -0.603, -1, LED[S])
    k.qy(-0.48, 0.48, 2.42, 2.47, -0.563, -1, LED[S])
    return k


SIGNS = {'L': ('ZENITH', 'LIFTS · LEVEL 61'), 'B': ('BRIEFING', 'THEATRE 2'), 'A': ('ARMORY', 'AUTHORISED ONLY'),
         'S': ('SIM BAY', 'LIVE FIRE · EARS ON'), 'O': ('OPERATIONS', 'LEVEL 62')}


def sign(k, S):
    k.begin()
    wall_base(k, S)
    a, b = SIGNS[S]
    k.bx(-0.46, 0.46, -0.56, -0.49, 2.9, 3.6, 'black')
    k.qy(-0.43, 0.43, 3.55, 3.57, -0.563, -1, LED[S])
    text(k, a, 0, -0.563, 3.15, 0.26, 'white', maxw=0.84)
    text(k, b, 0, -0.563, 2.98, 0.08, LED[S], font='cond', maxw=0.84)
    return k


def logo(k, S):
    """the unit's emblem: a star in a ring, ZENITH under it"""
    k.begin()
    wall_base(k, S)
    y = -0.56
    k.cyl(0, -0.53, 2.75, 0.42, 0.42, 0.05, 'graphite', seg=16, rot=(90, 0, 0))
    k.cyl(0, -0.584, 2.75, 0.36, 0.36, 0.004, LED[S] if S != 'L' else 'cyan', seg=16, rot=(90, 0, 0), ink=False)
    k.cyl(0, -0.592, 2.75, 0.32, 0.32, 0.004, 'black', seg=16, rot=(90, 0, 0), ink=False)
    star(k, 0, -0.6, 2.75, 0.27, 'white')
    k.qy(-0.46, 0.46, 1.95, 2.25, -0.5095, -1, 'black')
    text(k, 'ZENITH', 0, -0.513, 2.0, 0.2, 'white', maxw=0.8)
    return k


def lock(k, S):
    """biometric lock: palm plate and an eye scanner on a black panel"""
    k.begin()
    wall_base(k, S)
    k.bx(-0.2, 0.2, -0.56, -0.49, 1.0, 1.75, 'black')
    k.qy(-0.14, 0.14, 1.08, 1.42, -0.563, -1, 'screen2')
    for i in range(5):
        x = -0.1 + i * 0.05
        k.qy(x - 0.012, x + 0.012, 1.18, 1.36 - abs(i - 2) * 0.03, -0.566, -1, LED[S])
    k.cyl(0, -0.56, 1.6, 0.06, 0.06, 0.03, 'graphite', seg=10, rot=(90, 0, 0))
    k.cyl(0, -0.591, 1.6, 0.035, 0.035, 0.004, 'red', seg=10, rot=(90, 0, 0), ink=False)
    k.qy(-0.16, 0.16, 1.47, 1.5, -0.563, -1, 'green')
    return k


def screen_run(k, S, part):
    """video wall over three modules (L / M / R): black bezel band, dark tiles with charts, a ticker"""
    k.begin()
    wall_base(k, S)
    x0 = -0.44 if part == 'L' else -0.5
    x1 = 0.44 if part == 'R' else 0.5
    k.bx(x0, x1, -0.57, -0.5, 1.2, 3.9, 'black')
    for (z0, z1) in ((1.25, 2.55), (2.6, 3.85)):
        k.qy(x0 + 0.03, x1 - 0.03, z0, z1, -0.573, -1, 'screen2')
    seed = {'L': 1, 'M': 4, 'C': 5, 'R': 7}[part] + {'B': 0, 'S': 2, 'O': 5}[S]
    if S == 'S':      # projection: a street scene with a target silhouette
        k.qy(x0 + 0.03, x1 - 0.03, 1.25, 1.6, -0.576, -1, 'graphite2')
        for i in range(3):
            xx = -0.35 + i * 0.32 + (seed % 3) * 0.04
            k.qy(xx, xx + 0.18, 1.6, 2.2 + ((i + seed) % 3) * 0.4, -0.576, -1, 'twDark')
        if part == 'C':
            k.qy(-0.12, 0.12, 1.6, 2.5, -0.579, -1, 'orange')
            k.cyl(0, -0.58, 2.66, 0.11, 0.11, 0.004, 'orange', seg=8, rot=(90, 0, 0), ink=False)
            k.qy(-0.3, 0.3, 2.04, 2.07, -0.582, -1, 'red')
            k.qy(-0.015, 0.015, 1.75, 2.35, -0.585, -1, 'red')
    else:
        for i in range(6):
            xx = -0.42 + i * 0.14
            if xx < x0 + 0.04 or xx + 0.08 > x1 - 0.04:
                continue
            hh = 0.15 + 0.12 * ((i * 3 + seed) % 6)
            k.qy(xx, xx + 0.08, 1.35, 1.35 + hh, -0.576, -1, 'cyan' if (i + seed) % 3 else 'green')
        if S == 'O' and part == 'C':  # a city map patch
            k.qy(x0 + 0.08, x1 - 0.08, 2.7, 3.75, -0.576, -1, 'twDark')
            for j in range(4):
                k.qy(x0 + 0.08, x1 - 0.08, 2.85 + j * 0.25, 2.87 + j * 0.25, -0.579, -1, 'screen')
            k.qy(-0.06 + (seed % 3) * 0.1, 0.0 + (seed % 3) * 0.1, 3.1, 3.16, -0.582, -1, 'red')
        else:         # briefing: slide frame with a title bar
            k.qy(x0 + 0.06, x1 - 0.06, 3.55, 3.75, -0.576, -1, 'blue')
            k.qy(x0 + 0.1, x1 - 0.1, 2.75, 3.4, -0.576, -1, 'twDark')
            if part == 'C':
                text(k, 'OPERATION SKYFALL', 0, -0.579, 3.6, 0.1, 'white', font='cond', maxw=0.9)
                star(k, 0, -0.579, 3.07, 0.22, 'gold')
    return k


def city_map(k):
    k.begin()
    wall_base(k, 'O')
    k.bx(-0.46, 0.46, -0.57, -0.49, 1.2, 3.6, 'black')
    k.qy(-0.43, 0.43, 1.25, 3.55, -0.573, -1, 'screen2')
    for i in range(5):
        k.qy(-0.43, 0.43, 1.4 + i * 0.45, 1.43 + i * 0.45, -0.576, -1, 'cyanD')
        k.qy(-0.4 + i * 0.2, -0.37 + i * 0.2, 1.25, 3.55, -0.579, -1, 'cyanD')
    for (x, z) in ((-0.2, 2.1), (0.15, 2.8), (0.3, 1.6)):
        k.qy(x - 0.04, x + 0.04, z - 0.04, z + 0.04, -0.582, -1, 'red')
    k.qy(-0.05, 0.05, 2.45, 2.55, -0.582, -1, 'green')
    return k


def build_walls(k, ao):
    for S in STY:
        k.begin(); wall_base(k, S); k.finish('W' + S, ao=ao)
        k.begin(); wall_base(k, S, lamp=True); k.finish('W%s_Lamp' % S, ao=ao)
        corner(k, S).finish('Corner' + S, ao=ao)
        door(k, S).finish('W%s_Door' % S, ao=ao)
    for S in 'LBASO':
        sign(k, S).finish('W%s_Sign' % S, ao=ao)
    logo(k, 'L').finish('WL_Logo', ao=ao)
    logo(k, 'A').finish('WA_Logo', ao=ao)
    lock(k, 'L').finish('WL_Lock', ao=ao)
    lock(k, 'A').finish('WA_Lock', ao=ao)
    for S in 'BSO':
        for part in 'LMCR':
            screen_run(k, S, part).finish('W%s_Screen%s' % (S, part), ao=ao)
    # the lobby's single screen
    k.begin()
    wall_base(k, 'L')
    k.bx(-0.46, 0.46, -0.57, -0.49, 1.6, 3.2, 'black')
    k.qy(-0.43, 0.43, 1.64, 3.16, -0.573, -1, 'screen2')
    star(k, -0.2, -0.576, 2.75, 0.16, 'white')
    text(k, 'WELCOME', 0.12, -0.576, 2.65, 0.11, 'cyan', font='cond', maxw=0.4)
    k.qy(-0.38, 0.38, 1.85, 1.88, -0.576, -1, 'cyan')
    k.qy(-0.38, 0.1, 2.0, 2.03, -0.576, -1, 'steel2')
    k.finish('WL_Screen', ao=ao)
    city_map(k).finish('WO_Map', ao=ao)


# ================================================================ curtain wall (open glazing), cores, gate sides
def win(k, kind, rot=0):
    """floor-to-ceiling glazing bay: mullion (left edge), sill kick, guard rail, ceiling bulkhead, slab edge outside"""
    k.begin(rot)
    k.bx(-0.5, -0.44, -0.5, -0.34, 0, H, 'mullion')
    k.bx(-0.5, -0.44, -0.34, -0.2, 0.03, H, 'graphite')
    k.bx(-0.44, 0.5, -0.5, -0.34, 0, 0.12, 'graphite', ink=False)
    k.bx(-0.44, 0.5, -0.47, -0.41, 0.95, 1.0, 'mullion', ink=False)
    k.bx(-0.44, 0.5, -0.5, 0.42, H - 0.45, H, 'stone2')
    k.qz(-0.44, 0.5, -0.46, -0.38, H - 0.453, -1, 'cyan')
    k.bx(-0.5, 0.5, -0.34, 0.9, -0.6, 0.03, 'stone2')
    k.bx(-0.5, 0.5, 0.84, 0.9, 0.03, 0.15, 'mullion', ink=False)
    if kind == 'B':
        glint_y(k, -0.25, -0.35, 1.3, 1.1)
    if kind == 'C':   # a blind half down
        k.bx(-0.42, 0.48, -0.46, -0.43, 2.4, H - 0.45, 'graphite2', ink=False)
        k.bx(-0.43, 0.49, -0.47, -0.42, 2.37, 2.43, 'black', ink=False)
    return k


def win_col(k):
    k.begin()
    k.bx(-0.495, 0.495, -0.5, 0.42, 0, H, 'stone')
    k.bx(-0.495, 0.495, 0.42, 0.45, 0.03, H, 'mullion', ink=False)
    k.bx(-0.5, 0.5, -0.513, -0.497, 0, 0.12, 'graphite', ink=False)
    k.qy(-0.03, 0.03, 0.12, H - 0.2, -0.503, -1, 'cyan')
    k.bx(-0.5, 0.5, -0.34, 0.9, -0.6, 0.03, 'stone2')
    k.bx(-0.5, 0.5, 0.84, 0.9, 0.03, 0.15, 'mullion', ink=False)
    return k


def win_corner(k, rot):
    """building corner (canonical: outside toward Blender -X and +Y)"""
    k.begin(rot)
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'mullion')
    k.bx(-0.9, 0.5, 0.5, 0.9, -0.6, 0.03, 'stone2')
    k.bx(-0.9, -0.5, -0.5, 0.5, -0.6, 0.03, 'stone2')
    return k


def core(k):
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'stone2')
    return k


def gate_side(k):
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H, 'graphite')
    k.bx(-0.5, 0.5, -0.515, -0.5, 0, 0.12, 'black', ink=False)
    k.qy(-0.03, 0.03, 0.12, 3.6, -0.503, -1, 'cyan')
    k.qy(-0.45, 0.45, 3.9, 3.94, -0.503, -1, 'cyan')
    return k


# ---- the roof zone's walls: the HQ tower's facade (south) and the stair penthouse (north); full-cell blocks
TH = 8.0


def tower_glass(k):
    k.begin()
    k.bx(-0.5, 0.5, -0.4, 0.5, 0, TH, 'mullion')
    for (z0, z1) in ((0.2, 3.9), (4.3, 7.6)):
        k.qy(-0.43, 0.43, z0, z1, -0.403, -1, 'screen2')
        glint_y(k, -0.3, -0.406, z0 + 0.6, 1.4)
    k.bx(-0.5, 0.5, -0.5, -0.4, 3.9, 4.3, 'stone2')
    k.bx(-0.5, 0.5, -0.5, -0.4, 0, 0.2, 'stone2')
    k.bx(-0.5, 0.5, -0.5, -0.4, 7.6, TH, 'stone2')
    k.bx(-0.06, 0.06, -0.48, -0.4, 0.2, 3.9, 'graphite2', ink=False)
    k.bx(-0.06, 0.06, -0.48, -0.4, 4.3, 7.6, 'graphite2', ink=False)
    return k


def tower_gate_head(k):
    """over the 3 m entry gate in the HQ facade (roof zone): the facade continues from the gate frame's top (4.5 m)
    to the coping, with the unit's name over the door"""
    k.begin()
    k.bx(-1.5, 1.5, -0.4, 0.5, H, TH, 'mullion')
    k.qy(-1.45, 1.45, 4.85, 7.6, -0.403, -1, 'screen2')
    glint_y(k, -1.0, -0.406, 5.4, 1.4)
    glint_y(k, 0.6, -0.406, 5.1, 1.6)
    k.bx(-1.5, 1.5, -0.5, -0.4, H, 4.85, 'stone2')
    k.bx(-1.5, 1.5, -0.5, -0.4, 7.6, TH, 'stone2')
    k.bx(-1.3, 1.3, -0.56, -0.5, 5.5, 6.3, 'black')
    text(k, 'ZENITH HQ', 0, -0.563, 5.65, 0.5, 'white', maxw=2.3)
    k.qy(-1.25, 1.25, 6.18, 6.22, -0.563, -1, 'cyan')
    return k


def tower_pier(k):
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, TH + 0.3, 'stone2')
    k.qy(-0.03, 0.03, 0.3, TH, -0.503, -1, 'cyan')
    return k


def bulk(k, kind):
    k.begin()
    k.bx(-0.5, 0.5, -0.5, 0.5, 0, H - 0.25, 'concrete')
    k.bx(-0.53, 0.53, -0.53, 0.53, H - 0.25, H, 'concrete2')
    k.qy(-0.5, 0.5, 1.5, 1.52, -0.503, -1, 'concrete2')
    k.qy(-0.5, 0.5, 3.0, 3.02, -0.503, -1, 'concrete2')
    if kind == 'Louvre':
        k.bx(-0.4, 0.4, -0.56, -0.5, 1.9, 3.2, 'galv')
        for i in range(7):
            z = 2.0 + i * 0.17
            k.bx(-0.38, 0.38, -0.6, -0.56, z, z + 0.06, 'steel2', ink=False)
    elif kind == 'Door':
        k.bx(-0.42, 0.42, -0.55, -0.5, 0, 2.3, 'steelDark')
        k.qy(-0.36, 0.36, 0.02, 2.2, -0.553, -1, 'steel2')
        k.qy(-0.25, 0.25, 1.75, 1.95, -0.556, -1, 'yellow')
    elif kind == 'Plain':
        k.qy(0.15, 0.2, 0.0, 3.0, -0.506, -1, 'concrete2')   # rain streak
    return k


# ================================================================ gate, bridge, ceiling, hatch, stand
def gate_frame(k):
    """blast-door portal for the 3 m zone gates (both faces alike): graphite posts with cyan strips, a lit header"""
    k.begin()
    for s in (-1, 1):
        x0, x1 = srt(s * 1.495, s * 2.1)
        k.bx(x0, x1, -0.56, 0.56, 0, 3.5, 'graphite')
        lx0, lx1 = srt(s * 1.6, s * 1.68)
        for f in (-1, 1):
            y0, y1 = srt(f * 0.56, f * 0.59)
            k.bx(lx0, lx1, y0, y1, 0.3, 3.2, 'cyan', ink=False)
            k.bx(x0 + 0.02, x1 - 0.02, y0, y1, 0, 0.14, 'yellow', ink=False)
        cx = s * 1.9
        for f in (-1, 1):
            y0, y1 = srt(f * 0.59, f * 0.64)
            k.bx(cx - 0.07, cx + 0.07, y0, y1, 1.1, 1.36, 'black', ink=False)
    k.bx(-2.1, 2.1, -0.56, 0.56, 3.5, H - 0.005, 'graphite2')
    for f in (-1, 1):
        y = f * 0.563
        k.qy(-1.4, 1.4, 3.66, 3.7, y, f, 'cyan')
        text(k, 'ZENITH', 0, y, 3.82, 0.36, 'white', face='y-' if f < 0 else 'y+', maxw=2.2)
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
        k.bx(x0, x0 + 3 / 8, -0.07, 0.07, 0, 0.45, 'ink' if j % 2 else 'yellow', ink=False)
    return k


def trail_wall(k, kind=''):
    """sky-bridge side, 1 m along Blender Y, corridor toward +X: steel upstand, mullion, header, open glazing with
    glints, a handrail; half the deck and roof slabs and an edge girder"""
    k.begin()
    k.bx(-0.25, 0.25, -0.5, 0.5, 0, 0.25, 'stone2')
    k.bx(-0.08, 0.08, -0.5, -0.43, 0.25, H - 0.4, 'stone2')
    k.bx(-0.25, 0.25, -0.5, 0.5, H - 0.4, H, 'stone2')
    k.bx(0.16, 0.21, -0.5, 0.5, 0.98, 1.03, 'steel', ink=False)
    k.bx(0.12, 0.16, -0.47, -0.43, 0.96, 1.0, 'steelDark', ink=False)
    k.qz(0.0, 0.25, -0.5, 0.5, H - 0.403, -1, 'cyan')
    for s in (-1, 1):
        x = s * 0.03
        k.poly([(x, -0.25, 1.4), (x, -0.18, 1.4), (x, 0.12, 2.2), (x, 0.05, 2.2)], 'glint', (s, 0, 0))
    k.bx(-0.25, 2.25, -0.5, 0.5, -0.55, -0.004, 'stone2')
    k.bx(-0.32, -0.25, -0.5, 0.5, -1.1, 0.25, 'stone2')
    k.bx(-0.25, 2.25, -0.5, 0.5, H + 0.02, H + 0.36, 'stone')
    k.bx(-0.32, -0.25, -0.5, 0.5, H - 0.4, H + 0.42, 'stone2')
    if kind == 'Sign':
        k.bx(0.08, 0.13, -0.47, -0.05, 2.0, 2.6, 'black')
        k.poly([(0.133, -0.4, 2.3), (0.133, -0.25, 2.45), (0.133, -0.25, 2.15)], 'cyan', (1, 0, 0))
        k.qx(-0.24, -0.08, 2.27, 2.33, 0.133, 1, 'cyan')
        k.qx(-0.42, -0.1, 2.08, 2.12, 0.133, 1, 'white')
    elif kind == 'Plant':
        k.bx(0.08, 0.16, -0.42, 0.42, 1.25, 3.4, 'graphite')
        k.qx(-0.38, 0.38, 1.29, 3.36, 0.163, 1, 'leaf2')
        for i, (y, z, h) in enumerate(((-0.3, 1.35, 0.5), (-0.05, 1.6, 0.7), (0.22, 1.4, 0.45), (-0.2, 2.3, 0.6), (0.15, 2.2, 0.8), (-0.1, 2.9, 0.4))):
            k.qx(y - 0.1, y + 0.1, z, z + h, 0.166 + 0.003 * (i % 3), 1, 'leaf')
    return k


def ceil_light(k):
    k.begin()
    k.bx(-0.07, 0.07, -1.1, 1.1, -0.09, -0.004, 'stone', ink=False)
    k.qz(-0.05, 0.05, -1.05, 1.05, -0.093, -1, 'glow')
    return k


def hatch(k):
    """exit: the express-lift pod, a round pad with chevrons inside a ribbed glass capsule"""
    k.begin()
    k.cyl(0, 0, 0, 1.25, 1.25, 0.06, 'steel2', seg=20)
    k.cyl(0, 0, 0.06, 1.0, 1.0, 0.012, 'graphite', seg=20, ink=False)
    for i in range(3):
        y = -0.6 + i * 0.45
        k.poly([(-0.55, y, 0.075), (0, y + 0.32, 0.075), (0, y + 0.46, 0.075), (-0.55, y + 0.14, 0.075)], 'cyan', (0, 0, 1))
        k.poly([(0, y + 0.32, 0.076), (0.55, y, 0.076), (0.55, y + 0.14, 0.076), (0, y + 0.46, 0.076)], 'cyan', (0, 0, 1))
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        if abs(math.sin(a) + 1) < 0.5:
            continue
        ca, sa = math.cos(a), math.sin(a)
        pts = [(1.22, 0.06), (1.24, 1.2), (1.18, 2.1), (0.95, 2.75), (0.55, 3.1)]
        for j in range(len(pts) - 1):
            k.beam((ca * pts[j][0], sa * pts[j][0], pts[j][1]), (ca * pts[j + 1][0], sa * pts[j + 1][0], pts[j + 1][1]), 0.07, 'steel')
    k.cyl(0, 0, 3.05, 0.6, 0.2, 0.3, 'steel', seg=12)
    k.cyl(0, 0, 3.0, 0.5, 0.5, 0.05, 'glow', seg=12, ink=False)
    return k


def stand(k):
    k.begin()
    k.bx(-0.45, 0.45, -0.42, 0.42, 0, 0.9, 'graphite')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0.9, 0.96, 'steel')
    k.qy(-0.4, 0.4, 0.12, 0.16, -0.423, -1, 'cyan')
    k.bx(-0.47, 0.47, -0.44, 0.44, 0, 0.1, 'black', ink=False)
    k.col(-0.47, 0.47, -0.44, 0.44, 0, 0.96)
    return k


# ================================================================ floors and ceiling fittings (flat)
def floors(k):
    def tile(name, c, g, gw=0.025, extra=None):
        k.begin()
        k.qz(-0.5, 0.5, -0.5, 0.5, 0, 1, c)
        for (x0, x1, y0, y1) in ((-0.5, 0.5, -0.5, -0.5 + gw), (-0.5, -0.5 + gw, -0.5 + gw, 0.5)):
            k.qz(x0, x1, y0, y1, 0.003, 1, g)
        if extra:
            extra()
        k.finish(name)
    tile('Floor_StoneA', 'stone2', 'steel2')
    tile('Floor_StoneB', 'stone', 'steel2')
    tile('Floor_Border', 'graphite2', 'graphite', extra=lambda: k.qz(-0.5, 0.5, -0.03, 0.03, 0.006, 1, 'cyanD'))
    tile('Floor_Carpet', 'carpet', 'carpet2', gw=0.02, extra=lambda: k.qz(-0.3, 0.3, -0.3, 0.3, 0.006, 1, 'carpet2'))
    tile('Floor_Rubber', 'rubber', 'rubber2', gw=0.03,
         extra=lambda: [k.qz(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.006, 1, 'rubber2') for x in (-0.25, 0.25) for y in (-0.25, 0.25)])
    tile('Floor_Sim', 'graphite', 'black', gw=0.02, extra=lambda: k.qz(-0.5, 0.5, 0.2, 0.22, 0.006, 1, 'graphite2'))
    tile('Floor_Ops', 'tile', 'tile2', gw=0.03, extra=lambda: k.qz(0.3, 0.42, 0.3, 0.42, 0.006, 1, 'tile2'))
    tile('Floor_Mat', 'black', 'graphite', gw=0.04, extra=lambda: [k.qz(-0.4, 0.4, y - 0.02, y + 0.02, 0.006, 1, 'graphite2') for y in (-0.3, -0.1, 0.1, 0.3)])
    tile('Floor_Paver', 'concrete', 'concrete2', gw=0.04)
    # hazard stripes, the firing line, the cyan guide line
    k.begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, 0, 1, 'yellow')
    for (a, b) in ((-0.5, -0.3), (-0.1, 0.1), (0.3, 0.5)):
        k.qz(a, b, -0.5, 0.5, 0.003, 1, 'black')
    k.finish('Floor_Hazard')
    k.begin()
    k.qz(-0.5, 0.5, -0.5, 0.5, 0, 1, 'graphite')
    k.qz(-0.5, 0.5, -0.06, 0.06, 0.003, 1, 'orange')
    k.finish('Floor_FireLine')
    k.begin()
    k.qz(-0.5, 0.5, -0.04, 0.04, 0, 1, 'cyan')
    k.finish('Floor_Guide')
    # the unit's star inlay [4,4]
    k.begin()
    n = 24
    for (r, c, zz) in ((1.9, 'graphite', 0.0), (1.75, 'cyan', 0.003), (1.68, 'black', 0.006)):
        for i in range(n):
            a0, a1 = i / n * math.pi * 2, (i + 1) / n * math.pi * 2
            k.poly([(0, 0, zz), (r * math.cos(a0), r * math.sin(a0), zz), (r * math.cos(a1), r * math.sin(a1), zz)], c, (0, 0, 1))
    star_up(k, 0, 0, 0.009, 1.35, 'white')
    k.finish('Emblem')


def ceiling(k):
    k.begin()   # linear LED along X, 1 cell
    k.bx(-0.5, 0.5, -0.06, 0.06, -0.08, -0.004, 'graphite2', ink=False)
    k.qz(-0.5, 0.5, -0.04, 0.04, -0.083, -1, 'glow')
    k.finish('Ceil_Line')
    k.begin()
    k.cyl(0, 0, -0.06, 0.14, 0.14, 0.056, 'graphite2', seg=10, ink=False)
    k.cyl(0, 0, -0.063, 0.1, 0.1, 0.002, 'glow', seg=10, ink=False)
    k.finish('Ceil_Down')
    k.begin()   # steel beam along X
    k.bx(-0.5, 0.5, -0.14, 0.14, -0.5, -0.42, 'graphite2', ink=False)
    k.bx(-0.5, 0.5, -0.03, 0.03, -0.42, -0.08, 'graphite2', ink=False)
    k.bx(-0.5, 0.5, -0.14, 0.14, -0.08, -0.004, 'graphite2', ink=False)
    k.finish('Beam')
    k.begin()
    k.bx(-0.14, 0.14, -0.14, 0.14, -0.52, -0.004, 'graphite', ink=False)
    k.finish('BeamX')
    k.begin()   # round duct along X with hangers
    k.cyl(-0.5, 0, -0.62, 0.22, 0.22, 1.0, 'galv', seg=10, rot=(0, 90, 0), caps=False)
    k.bx(-0.02, 0.02, -0.02, 0.02, -0.4, -0.004, 'steelDark', ink=False)
    k.finish('Duct')
    k.begin()
    k.bx(-0.5, 0.5, -0.2, 0.2, -0.32, -0.3, 'steel2', ink=False)
    k.bx(-0.5, 0.5, -0.2, -0.18, -0.3, -0.24, 'steel2', ink=False)
    k.bx(-0.5, 0.5, 0.18, 0.2, -0.3, -0.24, 'steel2', ink=False)
    for (y, c) in ((-0.1, 'blue'), (0.0, 'yellow'), (0.1, 'black')):
        k.bx(-0.5, 0.5, y - 0.03, y + 0.03, -0.3, -0.26, c, ink=False)
    k.bx(-0.01, 0.01, -0.21, -0.19, -0.27, -0.004, 'steelDark', ink=False)
    k.bx(-0.01, 0.01, 0.19, 0.21, -0.27, -0.004, 'steelDark', ink=False)
    k.finish('Ceil_Tray')
    k.begin()   # doorway lintel over a two-cell wall (along X)
    k.bx(-0.5, 0.5, -0.5, 0.5, -1.2, -0.004, 'graphite2')
    k.qy(-0.5, 0.5, -1.15, -1.12, -0.503, -1, 'cyan')
    k.qy(-0.5, 0.5, -1.15, -1.12, 0.503, 1, 'cyan')
    k.finish('Lintel')


# ================================================================ furniture helpers
def led_frame(k, x0, x1, z0, z1, y, c='cyan', w=0.014):
    k.qy(x0, x1, z0, z0 + w, y, -1, c)
    k.qy(x0, x1, z1 - w, z1, y, -1, c)
    k.qy(x0, x0 + w, z0 + w, z1 - w, y, -1, c)
    k.qy(x1 - w, x1, z0 + w, z1 - w, y, -1, c)


SLOT_X = (-0.72, 0.72)
SLOT_Z = (1.05, 1.75)


def weapon_rack(k):
    """3 x 1 gun wall: gunmetal frame, slate board with four LED-framed slots (2 x 2), labels, a drawer cabinet and
    a lit header. Board face y = 0.45; guns hang with their backs at y = 0.415 (game z = -0.415)."""
    k.begin()
    for sx in (-1, 1):
        x0, x1 = srt(sx * 1.42, sx * 1.5)
        k.bx(x0, x1, 0.32, 0.5, 0.0, 2.2, 'graphite')
    k.bx(-0.03, 0.03, 0.36, 0.45, 0.62, 2.2, 'graphite')
    k.bx(-1.42, 1.42, 0.45, 0.5, 0.62, 2.2, 'slate2')
    for x in SLOT_X:
        for z in SLOT_Z:
            k.qy(x - 0.66, x + 0.66, z - 0.33, z + 0.3, 0.447, -1, 'slate')
            led_frame(k, x - 0.66, x + 0.66, z - 0.33, z + 0.3, 0.444)
            k.qy(x - 0.22, x + 0.22, z - 0.31, z - 0.21, 0.441, -1, 'black')
            k.qy(x - 0.18, x - 0.02, z - 0.28, z - 0.26, 0.438, -1, 'white')
            for px in (-0.3, 0.3):
                k.bx(x + px - 0.012, x + px + 0.012, 0.42, 0.447, z - 0.072, z - 0.048, 'steel', ink=False)
    k.bx(-1.5, 1.5, 0.32, 0.5, 2.2, 2.5, 'graphite2')
    k.qy(-1.4, 1.4, 2.27, 2.43, 0.317, -1, 'black')
    text(k, 'ZENITH ARMORY', -0.55, 0.314, 2.3, 0.1, 'cyan', font='cond', maxw=1.2)
    k.qy(0.6, 1.3, 2.33, 2.36, 0.314, -1, 'cyan')
    k.bx(-1.415, 1.415, 0.05, 0.45, 0.06, 0.62, 'graphite2')
    k.bx(-1.4, 1.4, 0.08, 0.45, 0.0, 0.06, 'black', ink=False)
    for x in SLOT_X:
        for i in range(3):
            z0 = 0.09 + i * 0.175
            k.qy(x - 0.64, x + 0.64, z0, z0 + 0.155, 0.047, -1, 'slate')
            k.qy(x - 0.18, x + 0.18, z0 + 0.1, z0 + 0.12, 0.044, -1, 'cyan' if i == 0 else 'steel')
    k.col(-1.5, 1.5, 0.0, 0.5, 0, 2.6)
    return k


def gun_case(k):
    """2 x 2 island gun case: plinth, a central slate board (faces at y = +-0.04) with two LED-framed slots a side,
    frosted glass ends, a lit canopy. Guns hang 3.5 cm off the board faces (mounts in highrise.js)."""
    k.begin()
    k.bx(-0.95, 0.95, -0.7, 0.7, 0, 0.5, 'graphite')
    k.bx(-0.97, 0.97, -0.72, 0.72, 0, 0.06, 'black', ink=False)
    for f in (-1, 1):
        k.qy(-0.8, 0.8, 0.2, 0.4, f * 0.703, f, 'slate')
        k.qy(-0.8, 0.8, 0.44, 0.46, f * 0.703, f, 'cyan')
    k.bx(-0.9, 0.9, -0.04, 0.04, 0.5, 2.15, 'slate2')
    for f in (-1, 1):
        y = f * 0.043
        for z in (1.0, 1.66):
            k.qy(-0.62, 0.62, z - 0.24, z + 0.26, y, f, 'slate')
            for (a, b, c0, d0) in ((-0.62, 0.62, z - 0.24, z - 0.226), (-0.62, 0.62, z + 0.246, z + 0.26), (-0.62, -0.606, z - 0.226, z + 0.246), (0.606, 0.62, z - 0.226, z + 0.246)):
                k.poly([(a, f * 0.046, c0), (b, f * 0.046, c0), (b, f * 0.046, d0), (a, f * 0.046, d0)], 'cyan', (0, f, 0))
            k.poly([(-0.2, f * 0.049, z - 0.22), (0.2, f * 0.049, z - 0.22), (0.2, f * 0.049, z - 0.17), (-0.2, f * 0.049, z - 0.17)], 'black', (0, f, 0))
    for sx in (-1, 1):
        x0, x1 = srt(sx * 0.9, sx * 0.96)
        for sy in (-1, 1):
            y0, y1 = srt(sy * 0.64, sy * 0.7)
            k.bx(x0, x1, y0, y1, 0.5, 2.2, 'graphite')
            k.qy(x0 + 0.015, x1 - 0.015, 0.6, 2.1, sy * 0.703, sy, 'cyan')
        k.bx(x0, x1, -0.64, 0.64, 0.5, 0.56, 'graphite', ink=False)
    k.bx(-0.97, 0.97, -0.72, 0.72, 2.2, 2.32, 'graphite')
    k.qz(-0.85, 0.85, -0.6, 0.6, 2.197, -1, 'glow')
    k.qy(-0.9, 0.9, 2.24, 2.28, -0.723, -1, 'cyan')
    k.qy(-0.9, 0.9, 2.24, 2.28, 0.723, 1, 'cyan')
    k.col(-0.97, 0.97, -0.72, 0.72, 0, 0.5)
    k.col(-0.95, 0.95, -0.06, 0.06, 0.5, 2.32)
    return k


def workbench(k):
    """2 x 1 bench: steel top at 0.92, grey mats (top 0.926) under the two mod mounts at x = +-0.48, y = -0.18; a
    tool riser on the back half with a holo lamp"""
    k.begin()
    k.bx(-0.95, 0.95, -0.42, 0.42, 0.86, 0.92, 'steel')
    k.qy(-0.95, 0.95, 0.87, 0.91, -0.423, -1, 'cyan')
    for sx in (-0.88, 0.88):
        for sy in (-0.36, 0.36):
            k.bx(sx - 0.03, sx + 0.03, sy - 0.03, sy + 0.03, 0.0, 0.86, 'graphite')
    k.bx(-0.85, 0.85, -0.33, 0.33, 0.18, 0.22, 'graphite2')
    k.bx(0.3, 0.85, -0.3, 0.3, 0.45, 0.86, 'slate')
    for i in range(2):
        k.qy(0.34, 0.81, 0.49 + i * 0.18, 0.64 + i * 0.18, -0.303, -1, 'slate2')
        k.qy(0.5, 0.65, 0.6 + i * 0.18, 0.62 + i * 0.18, -0.306, -1, 'steel')
    for sx in (-1, 1):
        k.bx(sx * 0.45 - 0.14, sx * 0.45 + 0.14, -0.1, 0.1, 0.22, 0.4, 'olive') if sx < 0 else None
    for x in (-0.48, 0.48):
        k.qz(x - 0.26, x + 0.26, -0.38, 0.02, 0.926, 1, 'graphite2')
    for sx in (-0.82, 0.82):
        k.bx(sx - 0.02, sx + 0.02, 0.36, 0.4, 0.92, 1.5, 'graphite')
    k.bx(-0.85, 0.85, 0.2, 0.42, 1.42, 1.46, 'graphite2')
    k.bx(-0.85, 0.85, 0.4, 0.42, 0.92, 1.42, 'slate2')
    for i in range(6):
        x = -0.7 + i * 0.13
        k.bx(x - 0.02, x + 0.02, 0.37, 0.4, 1.1, 1.35 - (i % 2) * 0.08, ('steel', 'yellow', 'steel', 'red', 'steel', 'blue')[i], ink=False)
    k.bx(0.2, 0.55, 0.24, 0.38, 1.46, 1.56, 'orange')
    k.bx(-0.07, 0.07, 0.22, 0.38, 0.926, 1.0, 'graphite')
    k.cyl(0.0, 0.3, 1.0, 0.012, 0.012, 0.3, 'steel', seg=6, ink=False)
    k.bx(-0.12, 0.12, -0.02, 0.3, 1.3, 1.34, 'graphite')
    k.qz(-0.1, 0.1, 0.0, 0.28, 1.297, -1, 'holo')
    k.col(-0.97, 0.97, -0.44, 0.44, 0, 0.926)
    k.col(-0.86, 0.86, 0.18, 0.43, 0.926, 1.56)
    return k


SHELF_TOP = 1.16


def gear_shelf(k):
    """2 x 1 gear shelving, back to the wall: items stand on the 1.16 shelf at x = +-0.5, y = 0.22"""
    k.begin()
    for sx in (-0.95, 0.95):
        for sy in (0.0, 0.46):
            k.bx(sx - 0.025, sx + 0.025, sy - 0.025, sy + 0.025, 0.0, 2.2, 'graphite')
    for top in (0.24, 0.7, SHELF_TOP, 1.64, 2.12):
        k.bx(-0.925, 0.925, -0.02, 0.48, top - 0.04, top, 'graphite2')
        k.qy(-0.925, 0.925, top - 0.035, top - 0.01, -0.023, -1, 'cyan' if top == SHELF_TOP else 'steelDark')
    k.bx(-0.925, 0.925, 0.48, 0.49, 0.24, 2.08, 'slate2')
    for i, x in enumerate((-0.45, 0.45)):
        k.bx(x - 0.36, x + 0.36, 0.04, 0.44, 0.24, 0.56, 'black' if i else 'graphite')
        k.qy(x - 0.12, x + 0.12, 0.34, 0.44, 0.037, -1, 'yellow')
    for i, x in enumerate((-0.62, -0.25, 0.12)):
        k.sph(x, 0.22, 0.85, 0.15, ('black', 'twDark', 'graphite')[i], seg=(8, 4), scale=(1, 1.1, 0.85))
    k.bx(0.42, 0.86, 0.06, 0.42, 0.7, 0.98, 'olive')
    for i, (x, w, h, c) in enumerate(((-0.6, 0.5, 0.3, 'black'), (-0.02, 0.44, 0.24, 'graphite'), (0.5, 0.56, 0.36, 'olive'))):
        k.bx(x - w / 2, x + w / 2, 0.06, 0.42, 1.64, 1.64 + h, c)
    k.col(-1.0, 1.0, -0.03, 0.5, 0, 2.2)
    return k


def exo_stand(k):
    """an exo-suit on its charging stand (faces -Y): a frame, armoured legs, torso, arms, a helmet"""
    k.begin()
    k.bx(-0.45, 0.45, -0.4, 0.4, 0, 0.1, 'graphite')
    k.qz(-0.38, 0.38, -0.33, 0.33, 0.104, 1, 'cyanD')
    k.bx(-0.06, 0.06, 0.29, 0.36, 0.1, 2.2, 'graphite')
    k.bx(-0.3, 0.3, 0.26, 0.38, 2.15, 2.3, 'graphite')
    for sx in (-1, 1):
        x = sx * 0.13
        k.bx(x - 0.08, x + 0.08, -0.1, 0.1, 0.1, 0.5, 'black')
        k.bx(x - 0.09, x + 0.09, -0.12, 0.1, 0.5, 0.95, 'slate')
        k.bx(x - 0.07, x + 0.07, -0.14, -0.12, 0.6, 0.85, 'cyan', ink=False)
        k.bx(x - 0.04, x + 0.04, -0.07, 0.25, 0.4, 0.46, 'steelDark', ink=False)
    k.bx(-0.24, 0.24, -0.16, 0.16, 0.95, 1.55, 'slate')
    k.bx(-0.2, 0.2, -0.2, -0.16, 1.1, 1.45, 'graphite2')
    k.qy(-0.06, 0.06, 1.25, 1.37, -0.203, -1, 'cyan')
    for sx in (-1, 1):
        x0, x1 = srt(sx * 0.24, sx * 0.36)
        k.bx(x0, x1, -0.1, 0.1, 1.15, 1.55, 'slate')
        k.bx(x0 + 0.01, x1 - 0.01, -0.08, 0.08, 0.75, 1.15, 'black')
    k.bx(-0.11, 0.11, -0.12, 0.12, 1.6, 1.86, 'graphite2')
    k.qy(-0.09, 0.09, 1.7, 1.78, -0.123, -1, 'holo')
    k.col(-0.45, 0.45, -0.4, 0.4, 0, 0.1)
    k.col(-0.36, 0.36, -0.2, 0.38, 0.1, 2.0)
    return k


def locker(k, v):
    k.begin()
    k.bx(-0.45, 0.45, -0.3, 0.45, 0, 2.3, 'graphite2')
    k.bx(-0.47, 0.47, -0.32, 0.47, 2.3, 2.38, 'graphite')
    k.qy(-0.43, -0.01, 0.06, 2.24, -0.303, -1, 'slate')
    k.qy(0.01, 0.43, 0.06, 2.24, -0.303, -1, 'slate' if v == 'A' else 'panel')
    for x in (-0.22, 0.22):
        k.qy(x - 0.1, x + 0.1, 1.85, 1.88, -0.306, -1, 'black')
        k.qy(x - 0.03, x + 0.03, 1.2, 1.26, -0.306, -1, 'green' if (x > 0) == (v == 'A') else 'red')
        k.qy(x - 0.12, x + 0.12, 0.2, 0.22, -0.306, -1, 'black')
    k.qy(-0.43, 0.43, 2.18, 2.2, -0.306, -1, 'cyan')
    k.col(-0.47, 0.47, -0.32, 0.47, 0, 2.38)
    return k


def cases(k, v):
    k.begin()
    if v == 'A':
        k.bx(-0.42, 0.42, -0.32, 0.32, 0, 0.36, 'black')
        k.bx(-0.36, 0.38, -0.26, 0.28, 0.36, 0.68, 'graphite')
        for (y, z) in ((-0.323, 0.18), (-0.263, 0.52)):
            k.qy(-0.1, 0.1, z - 0.02, z + 0.02, y, -1, 'yellow')
        k.bx(-0.12, 0.12, -0.05, 0.05, 0.68, 0.7, 'steelDark', ink=False)
    else:
        k.bx(-0.45, 0.45, -0.18, 0.18, 0, 0.3, 'graphite2')
        k.bx(-0.45, 0.45, -0.38, -0.2, 0, 0.3, 'black')
        k.bx(-0.4, 0.4, -0.3, 0.3, 0.3, 0.6, 'slate')
        k.qy(-0.3, 0.3, 0.44, 0.47, -0.303, -1, 'cyan')
    k.col(-0.45, 0.45, -0.38, 0.32, 0, 0.7)
    return k


def ammo_crate(k):
    k.begin()
    k.bx(-0.45, 0.45, -0.32, 0.32, 0, 0.42, 'olive')
    k.bx(-0.47, 0.47, -0.34, 0.34, 0.42, 0.48, 'olive')
    text(k, '5.56 · 900', 0, -0.323, 0.15, 0.09, 'yellow', font='cond', maxw=0.6)
    for sx in (-0.2, 0.2):
        k.bx(sx - 0.15, sx + 0.15, -0.12, 0.12, 0.48, 0.68, 'olive')
        k.bx(sx - 0.04, sx + 0.04, -0.02, 0.02, 0.68, 0.71, 'black', ink=False)
    k.col(-0.47, 0.47, -0.34, 0.34, 0, 0.7)
    return k


def ops_console(k):
    """4 x 1 wall console: desk with five screens, a big status screen over it, two chairs"""
    k.begin()
    k.bx(-1.95, 1.95, -0.1, 0.48, 0, 0.74, 'graphite2')
    k.bx(-1.98, 1.98, -0.42, 0.5, 0.74, 0.78, 'graphite')
    k.qy(-1.98, 1.98, 0.745, 0.775, -0.423, -1, 'cyan')
    for i in range(5):
        x = -1.6 + i * 0.8
        O.monitor(k, x, 0.2, 0, 0.78, 'screen' if i % 2 else 'green')
    k.bx(-1.6, 1.6, 0.42, 0.5, 1.4, 2.6, 'black')
    k.qy(-1.55, 1.55, 1.45, 2.55, 0.417, -1, 'screen2')
    for i in range(8):
        x = -1.4 + i * 0.36
        k.qy(x, x + 0.2, 1.6, 1.7 + 0.1 * ((i * 5) % 7), 0.414, -1, 'cyan' if i % 3 else 'orange')
    text(k, 'SECTOR STATUS', -0.9, 0.414, 2.3, 0.12, 'white', font='cond', maxw=1.2)
    for x in (-1.0, 1.0):
        O.task_chair(k, x, -0.7, 0)
    O.keyboard(k, -1.0, -0.15, 0, 0.78)
    O.keyboard(k, 1.0, -0.15, 0, 0.78)
    k.col(-1.98, 1.98, -0.42, 0.5, 0, 0.78)
    k.col(-1.6, 1.6, 0.4, 0.5, 0.78, 2.6)
    return k


def ops_desk(k):
    """4 x 2 desk pair back to back: a monitor wall down the middle, chairs both sides"""
    k.begin()
    for f in (-1, 1):
        y0, y1 = srt(f * 0.05, f * 0.8)
        k.bx(-1.9, 1.9, y0, y1, 0.72, 0.76, 'graphite')
        k.bx(-1.85, 1.85, *srt(f * 0.05, f * 0.15), 0, 0.72, 'graphite2')
        for sx in (-1.82, 1.82):
            k.bx(sx - 0.04, sx + 0.04, *srt(f * 0.7, f * 0.78), 0, 0.72, 'black', ink=False)
        k.qy(-1.9, 1.9, 0.725, 0.755, f * 0.803, f, 'cyan')
        for x in (-1.2, 0.0, 1.2):
            O.monitor(k, x, f * 0.18, 0 if f < 0 else 180, 0.76, 'screen')
            O.keyboard(k, x, f * 0.5, 0 if f < 0 else 180, 0.76)
        for x in (-0.9, 0.9):
            O.task_chair(k, x, f * 1.2, 0 if f < 0 else 180)
    k.bx(-1.9, 1.9, -0.05, 0.05, 0.76, 1.3, 'graphite2')
    k.col(-1.9, 1.9, -0.8, 0.8, 0, 0.76)
    k.col(-1.9, 1.9, -0.05, 0.05, 0.76, 1.3)
    return k


def seat_row(k):
    """4 x 2 theatre seat row on a riser, facing north (Blender +Y): four seats with tablet arms, a back panel"""
    k.begin()
    k.bx(-2.0, 2.0, -1.0, 1.0, 0, 0.15, 'carpet2')
    k.bx(-2.0, 2.0, -1.0, -0.92, 0.15, 0.78, 'carpet2')
    k.bx(-2.02, 2.02, -1.02, -0.9, 0.78, 0.84, 'walnut')
    k.qy(-2.0, 2.0, 0.22, 0.25, -1.003, -1, 'cyan')
    for i in range(4):
        x = -1.5 + i
        k.bx(x - 0.26, x + 0.26, -0.55, 0.05, 0.42, 0.52, 'carpet')
        k.bx(x - 0.26, x + 0.26, -0.75, -0.6, 0.45, 1.1, 'carpet')
        k.bx(x - 0.04, x + 0.04, -0.3, -0.2, 0.15, 0.42, 'graphite', ink=False)
        k.bx(x + 0.3, x + 0.36, -0.6, 0.0, 0.15, 0.68, 'graphite')
        k.bx(x + 0.18, x + 0.48, -0.05, 0.2, 0.68, 0.71, 'walnut2')
    k.bx(-1.86, -1.8, -0.6, 0.0, 0.15, 0.68, 'graphite')
    k.col(-2.0, 2.0, -1.0, 1.0, 0, 0.15)
    k.col(-2.0, 2.0, -1.0, 0.2, 0.15, 0.84)
    return k


def lectern(k):
    k.begin()
    k.bx(-0.32, 0.32, -0.22, 0.22, 0, 1.0, 'graphite2')
    k.prism_y([(-0.3, 1.0), (0.3, 1.0), (0.3, 1.14), (-0.3, 1.2)], -0.36, 0.36, 'graphite')
    k.qy(-0.25, 0.25, 0.5, 0.75, 0.223, 1, 'black')
    star(k, 0, 0.226, 0.62, 0.09, 'white', face=1)
    k.qy(-0.3, 0.3, 0.92, 0.95, 0.223, 1, 'cyan')
    k.col(-0.36, 0.36, -0.3, 0.3, 0, 1.2)
    return k


def bench(k):
    k.begin()
    k.bx(-0.95, 0.95, -0.22, 0.22, 0.42, 0.48, 'walnut')
    for sx in (-0.75, 0.75):
        k.bx(sx - 0.04, sx + 0.04, -0.2, 0.2, 0, 0.42, 'graphite')
    k.bx(-0.95, 0.95, -0.15, 0.15, 0.06, 0.08, 'graphite', ink=False)
    k.col(-0.95, 0.95, -0.22, 0.22, 0, 0.48)
    return k


def vending(k, v):
    k.begin()
    if v == 'A':
        k.bx(-0.45, 0.45, -0.38, 0.4, 0, 1.95, 'graphite')
        k.qy(-0.38, 0.2, 0.55, 1.8, -0.383, -1, 'screen2')
        for i in range(4):
            for j in range(3):
                k.qy(-0.34 + j * 0.18, -0.22 + j * 0.18, 0.7 + i * 0.27, 0.82 + i * 0.27, -0.386, -1, ('orange', 'cyan', 'green', 'red')[(i + j) % 4])
        k.qy(0.25, 0.4, 1.2, 1.5, -0.383, -1, 'black')
        k.qy(-0.38, 0.4, 0.15, 0.4, -0.383, -1, 'black')
        k.qy(-0.42, 0.42, 1.84, 1.9, -0.383, -1, 'cyan')
    else:
        k.bx(-0.2, 0.2, -0.2, 0.2, 0, 1.0, 'stone')
        k.cyl(0, 0, 1.0, 0.16, 0.16, 0.4, 'frost', seg=10)
        k.qy(-0.06, 0.06, 0.7, 0.76, -0.203, -1, 'blue')
        k.qy(-0.06, 0.06, 0.6, 0.66, -0.203, -1, 'red')
    k.col(-0.45, 0.45, -0.4, 0.4, 0, 1.95)
    return k


def front_desk(k):
    """6 x 2 reception counter (faces south, Blender -Y): stone front with the star, a cyan light line, monitors"""
    k.begin()
    k.bx(-2.9, 2.9, -0.55, -0.15, 0, 1.12, 'stone')
    k.bx(-2.95, 2.95, -0.62, 0.0, 1.12, 1.18, 'graphite')
    k.qy(-2.9, 2.9, 0.05, 0.1, -0.553, -1, 'cyan')
    k.bx(-2.9, 2.9, -0.15, 0.6, 0, 0.74, 'graphite2')
    k.bx(-2.9, 2.9, -0.15, 0.62, 0.74, 0.78, 'graphite')
    for sx in (-1, 1):
        x0, x1 = srt(sx * 2.6, sx * 2.9)
        k.bx(x0, x1, 0.0, 0.62, 0.78, 1.12, 'stone')
    k.qy(-0.9, 0.9, 0.3, 1.0, -0.553, -1, 'black')
    star(k, -0.55, -0.556, 0.65, 0.22, 'white')
    text(k, 'ZENITH', 0.2, -0.556, 0.55, 0.22, 'white', maxw=1.0)
    for x in (-1.6, -0.5, 0.6, 1.7):
        O.monitor(k, x, 0.15, 180, 0.78, 'screen')
    for x in (-1.1, 1.1):
        O.task_chair(k, x, 0.95, 180)
    k.col(-2.95, 2.95, -0.62, 0.62, 0, 1.18)
    return k


def bio_gate(k):
    """security speed-gate cabinet, 1 m along X: steel body, glass flap, scanner"""
    k.begin()
    k.bx(-0.5, 0.5, -0.14, 0.14, 0, 0.98, 'graphite2')
    k.bx(-0.5, 0.5, -0.16, 0.16, 0.98, 1.03, 'graphite')
    for f in (-1, 1):
        k.qy(-0.46, 0.46, 0.88, 0.9, f * 0.143, f, 'cyan')
    k.bx(-0.38, 0.38, -0.012, 0.012, 1.03, 1.55, 'frost')
    k.bx(0.39, 0.49, -0.08, 0.08, 1.03, 1.06, 'black', ink=False)
    k.qz(0.41, 0.47, -0.06, 0.06, 1.064, 1, 'green')
    k.col(-0.5, 0.5, -0.16, 0.16, 0, 1.05)
    return k


def sim_booth(k):
    """3 x 2 simulator booth, counter to the north (Blender +Y): padded side panels, a counter with a terminal"""
    k.begin()
    for sx in (-1, 1):
        x0, x1 = srt(sx * 1.42, sx * 1.5)
        k.bx(x0, x1, -0.9, 0.95, 0, 2.1, 'graphite')
        k.qx(-0.85, 0.9, 0.3, 1.9, sx * 1.42 - sx * 0.003, -sx, 'graphite2')
        k.qx(-0.85, 0.9, 1.95, 1.98, sx * 1.42 - sx * 0.003, -sx, 'orange')
    k.bx(-1.42, 1.42, 0.55, 0.95, 0, 1.05, 'graphite2')
    k.bx(-1.42, 1.42, 0.5, 0.95, 1.05, 1.1, 'black')
    k.qy(-1.42, 1.42, 0.95, 1.0, 0.497, -1, 'orange')
    k.bx(0.6, 1.1, 0.7, 0.85, 1.1, 1.45, 'black')
    k.qy(0.63, 1.07, 1.14, 1.42, 0.697, -1, 'screen')
    k.qz(-1.38, 1.38, -0.88, 0.5, 0.004, 1, 'black')
    text(k, 'LANE', -0.6, 0.497, 0.6, 0.18, 'white', face='y-', font='display', maxw=0.6)
    k.col(-1.5, -1.42, -0.9, 0.95, 0, 2.1)
    k.col(1.42, 1.5, -0.9, 0.95, 0, 2.1)
    k.col(-1.42, 1.42, 0.5, 0.95, 0, 1.1)
    return k


def holo_target(k):
    k.begin()
    k.cyl(0, 0, 0, 0.35, 0.38, 0.1, 'graphite', seg=10)
    k.cyl(0, 0, 0.1, 0.28, 0.28, 0.006, 'holo', seg=10, ink=False)
    # a robot silhouette in hologram light (flat, both faces)
    for f in (-1, 1):
        y = f * 0.004
        k.poly([(-0.18, y, 0.2), (0.18, y, 0.2), (0.22, y, 1.1), (-0.22, y, 1.1)], 'holo', (0, f, 0))
        k.poly([(-0.13, y, 1.15), (0.13, y, 1.15), (0.13, y, 1.42), (-0.13, y, 1.42)], 'holo', (0, f, 0))
        k.poly([(-0.32, y, 0.55), (-0.24, y, 0.55), (-0.24, y, 1.05), (-0.32, y, 1.0)], 'holo', (0, f, 0))
        k.poly([(0.24, y, 0.55), (0.32, y, 0.55), (0.32, y, 1.0), (0.24, y, 1.05)], 'holo', (0, f, 0))
        k.poly([(-0.04, y * 2, 1.25), (0.04, y * 2, 1.25), (0.04, y * 2, 1.33), (-0.04, y * 2, 1.33)], 'red', (0, f, 0))
    k.col(-0.36, 0.36, -0.36, 0.36, 0, 0.1)
    k.col(-0.22, 0.22, -0.06, 0.06, 0.1, 1.42)
    return k


def drone(k, x, y, z):
    """a parked quadcopter drone (body, four rotor rings, a camera)"""
    k.bx(x - 0.22, x + 0.22, y - 0.22, y + 0.22, z, z + 0.16, 'graphite')
    k.bx(x - 0.16, x + 0.16, y - 0.16, y + 0.16, z + 0.16, z + 0.22, 'slate')
    k.qz(x - 0.1, x + 0.1, y - 0.03, y + 0.03, z + 0.225, 1, 'cyan')
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ax, ay = x + dx * 0.42, y + dy * 0.42
        k.beam((x + dx * 0.15, y + dy * 0.15, z + 0.1), (ax, ay, z + 0.12), 0.04, 'graphite2', ink=False)
        k.cyl(ax, ay, z + 0.1, 0.2, 0.2, 0.05, 'black', seg=10)
        k.qz(ax - 0.17, ax + 0.17, ay - 0.015, ay + 0.015, z + 0.155, 1, 'steel2')
    k.sph(x, y - 0.22, z + 0.06, 0.07, 'black', seg=(6, 4))
    k.qy(x - 0.03, x + 0.03, z + 0.03, z + 0.09, y - 0.293, -1, 'red')


def drone_cradle(k, v):
    """2 x 2 charging cradle: a pad with hazard edge, guide posts, a charging arm; A holds a drone"""
    k.begin()
    k.bx(-0.95, 0.95, -0.95, 0.95, 0, 0.12, 'graphite2')
    k.qz(-0.85, 0.85, -0.85, 0.85, 0.124, 1, 'black')
    k.cyl(0, 0, 0.127, 0.6, 0.6, 0.004, 'cyan', seg=16, ink=False)
    k.cyl(0, 0, 0.134, 0.55, 0.55, 0.004, 'black', seg=16, ink=False)
    for (a, b) in ((-0.85, -0.6), (0.6, 0.85)):
        k.qz(a, b, -0.85, -0.75, 0.127, 1, 'yellow')
    for (sx, sy) in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
        k.bx(sx - 0.05, sx + 0.05, sy - 0.05, sy + 0.05, 0.12, 0.6, 'graphite')
        k.bx(sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.6, 0.64, 'cyan', ink=False)
    k.bx(0.6, 0.8, 0.6, 0.8, 0.12, 1.3, 'graphite')
    k.beam((0.7, 0.7, 1.25), (0.25, 0.25, 0.65), 0.06, 'graphite2')
    k.bx(0.6, 0.8, 0.58, 0.6, 0.9, 1.15, 'black', ink=False)
    k.qy(0.63, 0.77, 1.0, 1.1, 0.577, -1, 'green' if v == 'A' else 'orange')
    if v == 'A':
        drone(k, 0, 0, 0.142)
    else:
        k.bx(-0.3, 0.3, -0.2, 0.2, 0.12, 0.3, 'olive')
        k.bx(-0.25, 0.25, -0.15, 0.15, 0.3, 0.33, 'black', ink=False)
    k.col(-0.95, 0.95, -0.95, 0.95, 0, 0.13)
    k.col(0.6, 0.8, 0.6, 0.8, 0.13, 1.3)
    if v == 'A':
        k.col(-0.62, 0.62, -0.62, 0.62, 0.13, 0.4)
    else:
        k.col(-0.3, 0.3, -0.2, 0.2, 0.13, 0.33)
    return k


def vault(k):
    """6 x 2 vault entrance set into a two-cell wall (front -Y toward the hall): a steel frame block with a round-
    topped opening 2.6 m wide, the 3 m round door swung open on its hinge toward the hall (-Y), bolts, wheel"""
    k.begin()
    D = 1.0     # half the wall's thickness
    W2 = 1.3    # half the opening
    R = 1.3     # top arch radius (centre at 2.4)
    zc = 2.4
    for sx in (-1, 1):
        x0, x1 = srt(sx * W2, sx * 3.0)
        k.bx(x0, x1, -D, D, 0, H, 'graphite2')
    k.bx(-W2, W2, -D, D, zc + R, H, 'graphite2')
    # the arch: wedges between the opening and the lintel block
    n = 8
    for i in range(n):
        a0, a1 = i / n * math.pi, (i + 1) / n * math.pi
        p0 = (W2 * math.cos(a0), zc + R * math.sin(a0))
        p1 = (W2 * math.cos(a1), zc + R * math.sin(a1))
        top0 = (p0[0], zc + R)
        top1 = (p1[0], zc + R)
        k.prism([p0, p1, top1, top0][::-1] if p1[0] < p0[0] else [p0, p1, top1, top0], -D, D, 'graphite2')
    # the ring frame on the hall face: a thick steel ring
    for i in range(16):
        a0, a1 = i / 16 * math.pi * 2, (i + 1) / 16 * math.pi * 2
        r0, r1 = 1.62, 1.9
        pts = [(r0 * math.cos(a0), zc - 0.4 + r0 * math.sin(a0)), (r1 * math.cos(a0), zc - 0.4 + r1 * math.sin(a0)),
               (r1 * math.cos(a1), zc - 0.4 + r1 * math.sin(a1)), (r0 * math.cos(a1), zc - 0.4 + r0 * math.sin(a1))]
        if min(p[1] for p in pts) < 0.0:
            continue
        k.prism(pts, -D - 0.12, -D, 'steel2')
    k.qy(-3.0, 3.0, 4.0, 4.06, -D - 0.003, -1, 'cyan')
    text(k, 'VAULT 01', -2.15, -D - 0.003, 3.55, 0.28, 'white', maxw=1.4)
    k.qy(1.6, 2.7, 3.55, 3.85, -D - 0.003, -1, 'yellow')
    text(k, 'TIME LOCK', 2.15, -D - 0.006, 3.62, 0.14, 'ink', font='cond', maxw=1.0)
    # the door: a 3.2 m disc, 0.6 thick, open 95 degrees about a hinge at x = +1.9 on the hall face
    hx, hy = 1.95, -D - 0.1
    k.push(hx, hy, 95)
    k.cyl(-1.65, 0.3, zc - 0.4, 1.6, 1.6, 0.6, 'steel', seg=20, rot=(90, 0, 0))   # axis along -Y in the door frame
    k.cyl(-1.65, -0.3, zc - 0.4, 1.25, 1.25, 0.08, 'steel2', seg=20, rot=(90, 0, 0))
    k.cyl(-1.65, 0.38, zc - 0.4, 1.3, 1.3, 0.08, 'steel2', seg=20, rot=(90, 0, 0))
    for i in range(12):   # locking bolts round the rim
        a = i / 12 * math.pi * 2
        k.bx(-1.65 + 1.52 * math.cos(a) - 0.06, -1.65 + 1.52 * math.cos(a) + 0.06, -0.36, 0.36, zc - 0.4 + 1.52 * math.sin(a) - 0.06, zc - 0.4 + 1.52 * math.sin(a) + 0.06, 'galv', ink=False)
    k.cyl(-1.65, -0.38, zc - 0.4, 0.12, 0.12, 0.2, 'graphite', seg=8, rot=(90, 0, 0))
    for i in range(3):    # the wheel spokes
        a = i / 3 * math.pi
        k.beam((-1.65 - 0.6 * math.cos(a), -0.5 - 0.012 * i, zc - 0.4 - 0.6 * math.sin(a)), (-1.65 + 0.6 * math.cos(a), -0.5 - 0.012 * i, zc - 0.4 + 0.6 * math.sin(a)), 0.06, 'yellow')
    k.pop()
    k.bx(hx - 0.15, hx + 0.15, hy - 0.2, hy + 0.05, 0.6, 4.0, 'graphite')   # hinge post
    # collision: the wall either side and over the opening, the open door
    k.col(-3.0, -W2, -D, D, 0, H)
    k.col(W2, 3.0, -D, D, 0, H)
    k.col(-W2, W2, -D, D, zc + 0.6, H)
    # the open door (local frame turned -95 degrees about the hinge): an axis box along -Y from the hinge
    k.col(hx - 0.35, hx + 0.35, hy - 3.35, hy + 0.05, 0, 4.0)
    return k


def holo_table(k):
    """4 x 4 holo table: a round table with a glowing top, a hologram of the city towers over it and a light ring"""
    k.begin()
    k.cyl(0, 0, 0, 1.5, 1.6, 0.75, 'graphite', seg=20)
    k.cyl(0, 0, 0.75, 1.65, 1.65, 0.12, 'graphite2', seg=20)
    k.cyl(0, 0, 0.87, 1.45, 1.45, 0.003, 'screen2', seg=20, ink=False)
    k.cyl(0, 0, 0.876, 1.25, 1.25, 0.003, 'cyanD', seg=20, ink=False)
    k.cyl(0, 0, 0.882, 1.15, 1.15, 0.003, 'screen2', seg=20, ink=False)
    for i in range(20):
        a = i / 20 * math.pi * 2
        k.qz(1.5 * math.cos(a) - 0.04, 1.5 * math.cos(a) + 0.04, 1.5 * math.sin(a) - 0.04, 1.5 * math.sin(a) + 0.04, 0.876, 1, 'cyan')
    # the hologram: towers (flat outline-free boxes in holo light), the HQ in the middle with a red marker
    towers = ((0, 0, 0.18, 1.2), (-0.5, 0.3, 0.14, 0.7), (0.45, -0.35, 0.16, 0.85), (0.3, 0.5, 0.12, 0.5), (-0.4, -0.5, 0.13, 0.6),
              (0.7, 0.2, 0.1, 0.4), (-0.75, -0.1, 0.11, 0.45), (0.05, -0.75, 0.1, 0.35))
    for (x, y, r, h) in towers:
        k.bx(x - r, x + r, y - r, y + r, 0.95, 0.95 + h, 'holo', ink=False)
    k.bx(-0.03, 0.03, -0.03, 0.03, 2.15, 2.6, 'red', ink=False)
    k.cyl(0, 0, 0.92, 1.0, 1.0, 0.01, 'holo', seg=20, ink=False)
    k.cyl(0, 0, 4.1, 1.1, 1.1, 0.4, 'graphite2', seg=16)          # projector ring under the ceiling
    k.cyl(0, 0, 4.09, 0.9, 0.9, 0.01, 'glow', seg=16, ink=False)
    for i, a in enumerate((0.4, 2.0, 3.6, 5.2)):
        O.side_chair(k, math.cos(a) * 1.95, math.sin(a) * 1.95, math.degrees(a) + 90)
    k.col(-1.6, 1.6, -0.66, 0.66, 0, 0.87)
    k.col(-0.66, 0.66, -1.6, -0.66, 0, 0.87)
    k.col(-0.66, 0.66, 0.66, 1.6, 0, 0.87)
    k.col(-1.2, 1.2, -1.2, -0.66, 0, 0.87)
    k.col(-1.2, 1.2, 0.66, 1.2, 0, 0.87)
    return k


def server_rack(k):
    k.begin()
    k.bx(-0.42, 0.42, -0.45, 0.45, 0, 2.2, 'black')
    k.qy(-0.38, 0.38, 0.08, 2.12, -0.453, -1, 'graphite')
    for i in range(14):
        z = 0.15 + i * 0.14
        k.qy(-0.34, 0.34, z, z + 0.09, -0.456, -1, 'graphite2')
        for j in range(3):
            if (i * 7 + j * 3) % 5 == 0:
                continue
            x = -0.3 + j * 0.06
            k.qy(x, x + 0.025, z + 0.03, z + 0.06, -0.459, -1, ('cyan', 'green', 'blue', 'orange')[(i + j) % 4])
    k.qy(-0.42, 0.42, 2.14, 2.17, -0.453, -1, 'cyan')
    k.col(-0.42, 0.42, -0.45, 0.45, 0, 2.2)
    return k


def column(k):
    k.begin()
    k.bx(-0.4, 0.4, -0.4, 0.4, 0, H, 'stone')
    k.bx(-0.42, 0.42, -0.42, 0.42, 0, 0.15, 'graphite', ink=False)
    for (y, s) in ((-0.403, -1), (0.403, 1)):
        k.qy(-0.025, 0.025, 0.15, H - 0.3, y, s, 'cyan')
    for (x, s) in ((-0.403, -1), (0.403, 1)):
        k.qx(-0.025, 0.025, 0.15, H - 0.3, x, s, 'cyan')
    k.col(-0.42, 0.42, -0.42, 0.42, 0, H)
    return k


def coffee(k):
    """2 x 1 coffee point against the wall: cabinet, counter, an espresso machine, cups, a menu screen"""
    k.begin()
    k.bx(-0.95, 0.95, -0.2, 0.5, 0, 0.88, 'graphite2')
    k.bx(-0.97, 0.97, -0.25, 0.5, 0.88, 0.92, 'stone')
    for x in (-0.48, 0.48):
        k.qy(x - 0.44, x + 0.44, 0.08, 0.8, -0.203, -1, 'slate')
    k.bx(-0.6, -0.1, 0.0, 0.4, 0.92, 1.38, 'steel')
    k.bx(-0.58, -0.12, -0.02, 0.0, 1.05, 1.3, 'black', ink=False)
    for i in range(4):
        k.cyl(0.15 + i * 0.13, 0.15, 0.92, 0.04, 0.045, 0.1, 'white', seg=6, ink=False)
    k.bx(-0.7, 0.7, 0.45, 0.5, 1.5, 2.2, 'black')
    k.qy(-0.66, 0.66, 1.54, 2.16, 0.447, -1, 'screen2')
    text(k, 'FUEL', 0, 0.444, 1.9, 0.18, 'orange', maxw=1.0)
    k.col(-0.97, 0.97, -0.25, 0.5, 0, 1.4)
    return k


# ================================================================ the roof
def parapet(k, cut, kerb=False):
    """roof edge module on the cell's -Y edge: a 1.1 m parapet (concrete, steel coping) or a 0.3 m kerb with hazard
    paint; cut 'L' / 'R': stops 0.3 m short of its -X / +X end"""
    k.begin()
    t = 0.25 if kerb else 0.3
    h = 0.3 if kerb else 1.1
    x0 = -0.5 + (0.3 if 'L' in cut else 0.0)
    x1 = 0.5 - (0.3 if 'R' in cut else 0.0)
    y0, y1 = -0.5, -0.5 + t
    if kerb:
        k.bx(x0, x1, y0, y1, -0.02, h, 'steelDark')
        n = int(round((x1 - x0) / 0.25))
        for i in range(n):
            a = x0 + i * (x1 - x0) / n
            k.qz(a, a + (x1 - x0) / n, y0 + 0.02, y1 - 0.02, h + 0.004, 1, 'yellow' if i % 2 else 'black')
            k.qy(a, a + (x1 - x0) / n, 0.04, h - 0.04, y1 + 0.003, 1, 'black' if i % 2 else 'yellow')
    else:
        k.bx(x0, x1, y0, y1, -0.02, h - 0.08, 'concrete')
        k.bx(x0, x1, y0 - 0.04, y1 + 0.04, h - 0.08, h, 'galv')
        k.qy(x0, x1, 0.0, 0.12, y1 + 0.003, 1, 'concrete2')
    return k


def plank(k, L):
    """scaffold planks: three boards banded together, 1.5 m wide, running along local X (centred), top at 0.08"""
    k.begin()
    for i, y in enumerate((-0.5, 0.0, 0.5)):
        c = ('wood', 'wood2', 'wood')[i]
        k.bx(-L / 2 + 0.02 * i, L / 2 - 0.03 * (2 - i), y - 0.235, y + 0.235, 0, 0.075, c)
        for j in range(int(L / 1.5)):   # grain lines and knots
            x = -L / 2 + 0.6 + j * 1.5 + 0.2 * i
            k.qz(x, x + 0.5, y - 0.08 + 0.05 * i, y - 0.065 + 0.05 * i, 0.078, 1, 'wood2' if c == 'wood' else 'wood')
    for x in (-L / 2 + 0.15, L / 2 - 0.15, 0.0):
        k.bx(x - 0.05, x + 0.05, -0.75, 0.75, 0.0, 0.082, 'galv')
    text(k, 'ZTR', -L / 4, 0.0, 0.081, 0.2, 'white', face='up', font='display', valign='m')
    return k


def fan(k, r, n, c='steelDark'):
    """horizontal fan blades round a hub, origin at the hub centre (spun about Z by the theme)"""
    k.begin()
    k.cyl(0, 0, -0.06, r * 0.18, r * 0.18, 0.17, 'graphite', seg=10)
    for i in range(n):
        a = i / n * math.pi * 2
        ca, sa = math.cos(a), math.sin(a)
        w0, w1 = r * 0.12, r * 0.22
        pts = [(ca * r * 0.15 - sa * w0, sa * r * 0.15 + ca * w0), (ca * r * 0.95 - sa * w1, sa * r * 0.95 + ca * w1),
               (ca * r * 0.98 + sa * w1 * 0.3, sa * r * 0.98 - ca * w1 * 0.3), (ca * r * 0.15 + sa * w0 * 0.4, sa * r * 0.15 - ca * w0 * 0.4)]
        z0 = 0.005 * i
        a3 = [k.m.bm.verts.new(k.m.parent @ Vector((x, y, z0))) for (x, y) in pts]
        b3 = [k.m.bm.verts.new(k.m.parent @ Vector((x, y, z0 + 0.03 + 0.03 * (j % 2)))) for j, (x, y) in enumerate(pts)]
        fs = [k.m.bm.faces.new(a3), k.m.bm.faces.new(b3)]
        for q in range(4):
            fs.append(k.m.bm.faces.new((a3[q], a3[(q + 1) % 4], b3[(q + 1) % 4], b3[q])))
        bmesh.ops.recalc_face_normals(k.m.bm, faces=fs)
        k.m._finish(a3 + b3, c, False)
    return k


def hvac(k):
    """3 x 2 rooftop unit: galvanised casing with louvres, a fan shroud on top (fan at 1.62, spun by the theme),
    guard bars, service panels, pipework"""
    k.begin()
    k.bx(-1.45, 1.45, -0.95, 0.95, 0.15, 1.5, 'galv')
    k.bx(-1.5, 1.5, -1.0, 1.0, 0, 0.15, 'steelDark')
    for f in (-1, 1):
        for i in range(8):
            z = 0.35 + i * 0.12
            k.qy(-1.3, -0.1, z, z + 0.05, f * 0.953, f, 'steelDark')
        k.qy(0.1, 1.3, 0.3, 1.35, f * 0.953, f, 'steel2')
        k.qy(1.1, 1.2, 0.8, 0.95, f * 0.956, f, 'black')
        k.qy(0.15, 0.9, 1.15, 1.25, f * 0.956, f, 'yellow')
    k.qz(-1.4, 1.4, -0.9, 0.9, 1.505, 1, 'steel2')
    k.cyl(0, 0, 1.5, 0.82, 0.82, 0.25, 'steel', seg=16, caps=False)
    k.cyl(0, 0, 1.509, 0.78, 0.78, 0.003, 'black', seg=16, ink=False)
    for i in range(5):
        x = -0.6 + i * 0.3
        k.bx(x - 0.015, x + 0.015, -0.8, 0.8, 1.74, 1.77, 'graphite', ink=False)
    k.bx(-0.8, 0.8, -0.015, 0.015, 1.77, 1.8, 'graphite', ink=False)
    k.cyl(1.5, 0.5, 0.3, 0.07, 0.07, 0.8, 'galv', seg=6, rot=(0, 90, 0))
    k.cyl(1.5, -0.4, 0.5, 0.05, 0.05, 0.8, 'orange', seg=6, rot=(0, 90, 0))
    k.col(-1.5, 1.5, -1.0, 1.0, 0, 1.75)
    return k


def cooling_tower(k):
    """4 x 4 cooling tower: louvred box on legs, fan stack on top (fan at 3.32), a ladder"""
    k.begin()
    for (sx, sy) in ((-1.85, -1.85), (1.85, -1.85), (-1.85, 1.85), (1.85, 1.85)):
        k.bx(sx - 0.08, sx + 0.08, sy - 0.08, sy + 0.08, 0, 0.6, 'steelDark')
    k.bx(-1.9, 1.9, -1.9, 1.9, 0.6, 1.0, 'steelDark')
    k.bx(-1.85, 1.85, -1.85, 1.85, 1.0, 3.0, 'galv')
    for f in (-1, 1):
        for i in range(9):
            z = 1.15 + i * 0.2
            k.qy(-1.7, 1.7, z, z + 0.09, f * 1.853, f, 'steel2')
            k.qx(-1.7, 1.7, z, z + 0.09, f * 1.853, f, 'steel2')
    k.bx(-1.9, 1.9, -1.9, 1.9, 3.0, 3.1, 'steelDark')
    k.cyl(0, 0, 3.1, 1.72, 1.72, 0.5, 'galv', seg=20, caps=False)
    k.cyl(0, 0, 3.104, 1.68, 1.68, 0.003, 'black', seg=20, ink=False)
    for i in range(7):
        x = -1.5 + i * 0.5
        k.bx(x - 0.02, x + 0.02, -1.6, 1.6, 3.58, 3.62, 'graphite', ink=False)
    text(k, 'CT-2', 0, -1.856, 2.55, 0.3, 'ink', font='display')
    for i in range(10):   # ladder up the front
        z = 0.7 + i * 0.28
        k.bx(1.2, 1.6, -2.05, -2.0, z, z + 0.03, 'yellow', ink=False)
    for x in (1.2, 1.6):
        k.bx(x - 0.02, x + 0.02, -2.06, -1.9, 0.0, 3.6, 'yellow', ink=False)
    k.col(-1.9, 1.9, -2.06, 1.9, 0, 3.6)
    return k


def water_tank(k):
    """3 x 3 wooden water tank on a steel stand: hoops, a cone roof, a ladder"""
    k.begin()
    for (sx, sy) in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
        k.bx(sx - 0.09, sx + 0.09, sy - 0.09, sy + 0.09, 0, 1.9, 'graphite2')
    k.beam((-1.0, -1.0, 0.2), (1.0, -1.0, 1.7), 0.05, 'graphite2', ink=False)
    k.beam((1.0, 1.0, 0.2), (-1.0, 1.0, 1.7), 0.05, 'graphite2', ink=False)
    k.bx(-1.3, 1.3, -1.3, 1.3, 1.9, 2.05, 'graphite')
    k.cyl(0, 0, 2.05, 1.32, 1.32, 2.4, 'wood2', seg=14)
    for z in (2.35, 3.0, 3.65, 4.2):
        k.cyl(0, 0, z, 1.345, 1.345, 0.06, 'graphite', seg=14, ink=False)
    k.cyl(0, 0, 4.45, 1.42, 0.12, 0.85, 'wood', seg=14)
    for i in range(12):
        z = 0.3 + i * 0.32
        k.bx(-0.25, 0.25, -1.62, -1.58, z, z + 0.03, 'steel2', ink=False)
    for x in (-0.25, 0.25):
        k.bx(x - 0.02, x + 0.02, -1.64, -1.5, 0.0, 4.4, 'steel2', ink=False)
    for (sx, sy) in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
        k.col(sx - 0.1, sx + 0.1, sy - 0.1, sy + 0.1, 0, 1.9)
    k.col(-0.95, 0.95, -0.95, 0.95, 1.9, 5.2)
    k.col(-1.3, -0.95, -0.55, 0.55, 1.9, 5.2)
    k.col(0.95, 1.3, -0.55, 0.55, 1.9, 5.2)
    k.col(-0.55, 0.55, -1.3, -0.95, 1.9, 5.2)
    k.col(-0.55, 0.55, 0.95, 1.3, 1.9, 5.2)
    return k


def machine_room(k):
    """6 x 4 lift machine room: concrete box, steel door, louvres, a split AC unit, warning signs, roof plant"""
    k.begin()
    k.bx(-2.95, 2.95, -1.95, 1.95, 0, 3.2, 'concrete')
    k.bx(-3.0, 3.0, -2.0, 2.0, 3.2, 3.42, 'concrete2')
    for z in (1.0, 2.0):
        k.qy(-2.95, 2.95, z, z + 0.015, -1.953, -1, 'concrete2')
        k.qy(-2.95, 2.95, z, z + 0.015, 1.953, 1, 'concrete2')
    k.bx(-0.55, 0.55, -2.0, -1.95, 0, 2.3, 'steelDark')
    k.qy(-0.47, 0.47, 0.02, 2.22, -2.003, -1, 'steel2')
    k.qy(0.28, 0.38, 1.0, 1.06, -2.006, -1, 'black')
    k.qy(-0.3, 0.3, 1.7, 2.05, -2.006, -1, 'yellow')
    text(k, 'LIFT MOTOR ROOM', 0, -2.009, 1.82, 0.08, 'ink', font='cond', maxw=0.55)
    for x0 in (-2.4, 1.2):
        k.bx(x0, x0 + 1.1, -2.03, -1.95, 1.6, 2.6, 'galv')
        for i in range(6):
            k.bx(x0 + 0.05, x0 + 1.05, -2.07, -2.03, 1.7 + i * 0.15, 1.75 + i * 0.15, 'steel2', ink=False)
    k.bx(3.0, 3.55, -1.0, 0.8, 0.4, 1.4, 'galv')
    for i in range(4):
        k.qx(-0.9, 0.7, 0.55 + i * 0.2, 0.62 + i * 0.2, 3.553, 1, 'steelDark')
    k.cyl(3.2, 0.9, 0.6, 0.04, 0.04, 2.5, 'steel2', seg=6, ink=False)
    k.bx(-2.0, -0.6, 0.0, 1.4, 3.42, 4.0, 'galv')
    k.bx(1.0, 2.4, -1.2, 0.2, 3.42, 3.8, 'steelDark')
    k.cyl(1.7, -0.5, 3.8, 0.35, 0.35, 0.12, 'steel2', seg=10)
    k.col(-3.0, 3.0, -2.07, 2.0, 0, 3.42)
    k.col(3.0, 3.55, -1.0, 0.8, 0, 1.4)
    return k


def mast(k):
    """2 x 2 antenna mast: a lattice tower on a plinth, dishes and a whip, a red beacon"""
    k.begin()
    k.bx(-0.9, 0.9, -0.9, 0.9, 0, 0.35, 'concrete')
    s = 0.35
    for (sx, sy) in ((-s, -s), (s, -s), (-s, s), (s, s)):
        k.beam((sx * 1.2, sy * 1.2, 0.35), (sx * 0.5, sy * 0.5, 9.0), 0.06, 'galv')
    for i in range(9):
        z = 0.8 + i * 0.95
        f = 1.2 - 0.7 * (z - 0.35) / 8.65
        a = s * f
        for j, (p, q) in enumerate((((-a, -a), (a, -a)), ((a, -a), (a, a)), ((a, a), (-a, a)), ((-a, a), (-a, -a)))):
            k.beam((p[0], p[1], z + 0.04 * j), (q[0], q[1], z + 0.04 * j), 0.03, 'galv', ink=False)
    for (z, yaw, r) in ((5.2, 0.0, 0.45), (6.8, 2.2, 0.35)):
        dx, dy = math.cos(yaw) * 0.45, math.sin(yaw) * 0.45
        k.push(dx, dy, math.degrees(yaw) + 90, z=z)
        k.cyl(0, 0, 0, r, r * 0.4, 0.18, 'white', seg=12, rot=(90, 0, 0))
        k.pop()
    k.bx(-0.25, -0.2, -0.05, 0.05, 4.0, 5.2, 'white')
    k.cyl(0, 0, 9.0, 0.04, 0.02, 2.4, 'galv', seg=6, ink=False)
    k.sph(0, 0, 11.45, 0.12, 'red', seg=(6, 4))
    k.col(-0.9, 0.9, -0.9, 0.9, 0, 1.2)
    return k


def gantry(k):
    """4 x 6 window-cleaning gantry (BMU) on its roof track: two rails along Y, a wheeled carriage, a turret and a long
    jib out over the edge (local -X, beyond the footprint) with the cleaning cradle hanging off it"""
    k.begin()
    for x in (-1.4, 1.4):
        k.bx(x - 0.1, x + 0.1, -2.95, 2.95, 0, 0.12, 'steelDark')
        k.bx(x - 0.04, x + 0.04, -2.95, 2.95, 0.12, 0.2, 'galv', ink=False)
    k.bx(-1.7, 1.7, -1.3, 1.3, 0.35, 1.6, 'yellow')
    for (x, y) in ((-1.4, -1.0), (1.4, -1.0), (-1.4, 1.0), (1.4, 1.0)):
        k.cyl(x, y, 0.28, 0.2, 0.2, 0.18, 'black', seg=10, rot=(0, 90, 0))
    for f in (-1, 1):
        k.qy(-1.5, 1.5, 0.5, 0.6, f * 1.303, f, 'black')
        text(k, 'SKYWASH BMU-3', 0, f * 1.303, 0.95, 0.18, 'ink', face='y-' if f < 0 else 'y+', font='cond', maxw=2.4)
    k.cyl(0, 0, 1.6, 0.75, 0.75, 1.9, 'yellow', seg=12)
    k.bx(-0.6, 0.6, -0.55, 0.55, 3.5, 4.4, 'graphite')
    k.qy(-0.5, 0.5, 3.7, 4.2, -0.553, -1, 'screen2')
    # the jib (along local -X, 9 m out), a counter-jib, ties to a mast
    k.bx(-9.5, 1.8, -0.22, 0.22, 4.4, 4.8, 'yellow')
    k.bx(1.0, 2.3, -0.5, 0.5, 4.0, 4.4, 'graphite2')
    k.bx(-0.12, 0.12, -0.12, 0.12, 4.8, 6.6, 'yellow')
    k.beam((0, 0, 6.6), (-9.3, 0, 4.85), 0.04, 'graphite', ink=False)
    k.beam((0, 0.05, 6.6), (2.1, 0.05, 4.85), 0.04, 'graphite', ink=False)
    for x in (-8.0, -5.5, -3.0):
        k.bx(x - 0.04, x + 0.04, -0.24, 0.24, 4.3, 4.4, 'graphite', ink=False)
    # the cradle hanging off the jib end on four cables
    for (cx, cy) in ((-9.9, -0.9), (-9.9, 0.9), (-8.6, -0.9), (-8.6, 0.9)):
        k.bx(cx - 0.012, cx + 0.012, cy - 0.012, cy + 0.012, 2.1, 4.4, 'black', ink=False)
    k.bx(-10.0, -8.5, -1.0, 1.0, 1.6, 1.7, 'graphite2')
    k.bx(-10.0, -8.5, -1.0, -0.95, 1.7, 2.6, 'yellow')
    k.bx(-10.0, -8.5, 0.95, 1.0, 1.7, 2.6, 'yellow')
    k.bx(-10.0, -9.95, -0.95, 0.95, 1.7, 2.6, 'yellow')
    k.bx(-8.55, -8.5, -0.95, 0.95, 1.7, 2.6, 'yellow')
    k.bx(-9.6, -9.2, -0.4, 0.3, 1.7, 2.1, 'slate')
    k.col(-1.7, 1.7, -1.3, 1.3, 0, 1.6)
    k.col(-0.75, 0.75, -0.75, 0.75, 1.6, 3.5)
    return k


def skylight(k):
    """3 x 2 skylight: a curb with a glazed ridge roof (dark glass, glints, mullions, a ridge bar)"""
    k.begin()
    k.bx(-1.45, 1.45, -0.95, 0.95, 0, 0.45, 'concrete2')
    k.bx(-1.48, 1.48, -0.98, 0.98, 0.45, 0.52, 'galv')
    k.prism_y([(-0.9, 0.52), (0.9, 0.52), (0.0, 1.2)], -1.36, 1.36, 'screen2')
    for x in (-1.39, -0.7, 0.0, 0.7, 1.39):
        x0, x1 = x - 0.03, x + 0.03
        zf = lambda y: 0.52 + (0.9 - abs(y)) * 0.68 / 0.9
        for sg in (-1, 1):
            ya, yb = sg * 0.9, sg * 0.06
            k.prism_y([(ya, zf(ya) - 0.03), (yb, zf(yb) - 0.03), (yb, zf(yb) + 0.03), (ya, zf(ya) + 0.03)], x0, x1, 'galv', ink=False)
    k.bx(-1.44, 1.44, -0.08, 0.08, 1.14, 1.28, 'galv')
    k.col(-1.48, 1.48, -0.98, 0.98, 0, 1.26)
    return k


def solar(k):
    """4 x 2 solar array: two tilted panels on frames"""
    k.begin()
    for x in (-1.0, 1.0):
        for y in (-0.7, 0.7):
            k.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0, 0.5 + (0.7 - y) * 0.45, 'galv')
    for x0 in (-1.9, 0.0):
        k.prism_y([(-0.85, 1.2), (0.85, 0.42), (0.85, 0.5), (-0.85, 1.28)], x0 + 0.02, x0 + 1.88, 'solar')
    for i in range(1, 8):
        x = -1.9 + i * 3.8 / 8
        a = (x - 0.01, x + 0.01)
        k.poly([(a[0], -0.85, 1.285), (a[1], -0.85, 1.285), (a[1], 0.85, 0.505), (a[0], 0.85, 0.505)], 'steel2', (0, 0.4, 1))
    k.col(-1.9, 1.9, -0.9, -0.3, 0, 1.05)
    k.col(-1.9, 1.9, -0.3, 0.3, 0, 0.8)
    k.col(-1.9, 1.9, 0.3, 0.9, 0, 0.55)
    return k


def vent(k, v):
    k.begin()
    if v == 'A':   # mushroom extract fan
        k.bx(-0.32, 0.32, -0.32, 0.32, 0, 0.2, 'concrete2')
        k.cyl(0, 0, 0.2, 0.22, 0.22, 0.45, 'galv', seg=10)
        k.cyl(0, 0, 0.65, 0.42, 0.12, 0.25, 'galv', seg=10)
    else:          # gooseneck
        k.bx(-0.3, 0.3, -0.3, 0.3, 0, 0.18, 'concrete2')
        k.cyl(0, 0, 0.18, 0.13, 0.13, 0.7, 'galv', seg=8)
        k.cyl(0, 0, 0.88, 0.13, 0.13, 0.26, 'galv', seg=8, rot=(0, 90, 0))
        k.cyl(0.26, 0, 0.88, 0.13, 0.13, 0.26, 'galv', seg=8, rot=(0, 145, 0))
    k.col(-0.35, 0.35, -0.35, 0.35, 0, 0.9)
    return k


def roof_duct(k):
    """1 m of rectangular duct on supports, along X"""
    k.begin()
    k.bx(-0.5, 0.5, -0.3, 0.3, 0.2, 0.75, 'galv')
    k.qy(-0.5, 0.5, 0.45, 0.47, -0.303, -1, 'steel2')
    k.qy(-0.5, 0.5, 0.45, 0.47, 0.303, 1, 'steel2')
    k.bx(-0.04, 0.04, -0.34, 0.34, 0.0, 0.2, 'steelDark')
    k.bx(-0.06, 0.06, -0.32, 0.32, 0.75, 0.78, 'steelDark', ink=False)
    k.col(-0.5, 0.5, -0.34, 0.34, 0, 0.78)
    return k


def plank_stack(k):
    """spare planks: a stack on bearers and two leaning on a crate (faces -Y)"""
    k.begin()
    for x in (-0.3, 0.3):
        k.bx(x - 0.05, x + 0.05, -0.45, 0.45, 0, 0.1, 'wood2')
    for i in range(4):
        k.bx(-0.48 + 0.01 * (i % 2), 0.48 - 0.01 * ((i + 1) % 2), -0.42, 0.42, 0.1 + i * 0.08, 0.17 + i * 0.08, 'wood' if i % 2 else 'wood2')
    k.bx(-0.35, 0.35, 0.05, 0.4, 0.42, 0.9, 'olive')
    for i, x in enumerate((-0.25, 0.15)):
        k.push(x, 0.0, 0, z=0.42)
        k.prism_y([(-0.05, 0.0), (0.03, 0.0), (0.38, 1.6), (0.3, 1.6)], -0.12, 0.12, 'wood' if i else 'wood2')
        k.pop()
    k.col(-0.48, 0.48, -0.45, 0.45, 0, 0.9)
    return k


def roof_hatch(k):
    k.begin()
    k.bx(-0.45, 0.45, -0.45, 0.45, 0, 0.42, 'concrete2')
    k.bx(-0.48, 0.48, -0.48, 0.48, 0.42, 0.5, 'galv')
    k.qz(-0.3, 0.3, -0.3, 0.3, 0.504, 1, 'steel2')
    k.qz(-0.3, 0.3, -0.03, 0.03, 0.508, 1, 'yellow')
    for x in (-0.25, 0.25):
        k.beam((x, 0.45, 0.42), (x, 0.55, 1.4), 0.03, 'yellow', ink=False)
    k.beam((-0.25, 0.55, 1.4), (0.25, 0.55, 1.4), 0.03, 'yellow', ink=False)
    k.col(-0.48, 0.48, -0.48, 0.48, 0, 0.5)
    return k


# ================================================================ build
CORNERS = (('NW', 0), ('NE', -90), ('SE', 180), ('SW', 90))


def build_kit_highrise(ao):
    pal = Palette(FAM)
    k = HKit(pal)
    build_walls(k, ao)
    for kind in ('A', 'B', 'C'):
        win(k, kind).finish('Win_%s' % kind)
    win_col(k).finish('WinCol', ao=ao)
    for tag, rot in CORNERS:
        win_corner(k, rot).finish('WinCorner_%s' % tag)
    core(k).finish('Core', ao=ao)
    gate_side(k).finish('GateSide', ao=ao)
    tower_glass(k).finish('Tower_Glass', ao=ao)
    tower_pier(k).finish('Tower_Pier', ao=ao)
    tower_gate_head(k).finish('Tower_GateHead', ao=ao)
    for kind in ('Plain', 'Louvre', 'Door', 'Corner'):
        bulk(k, kind).finish('Bulk_%s' % kind, ao=ao)
    gate_frame(k).finish('GateFrame', ao=ao)
    shutter = gate_shutter(k).finish('GateShutter')
    m = Model(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    trail_wall(k).finish('TrailWall', ao=ao)
    trail_wall(k, 'Sign').finish('TrailWall_Sign', ao=ao)
    trail_wall(k, 'Plant').finish('TrailWall_Plant', ao=ao)
    ceil_light(k).finish('CeilLight')
    hatch(k).finish('Hatch', ao=ao)
    stand(k).finish('Stand', ao=ao)
    floors(k)
    ceiling(k)
    # armory
    weapon_rack(k).finish('WeaponRack', ao=ao)
    gun_case(k).finish('GunCase', ao=ao)
    workbench(k).finish('Workbench', ao=ao)
    gear_shelf(k).finish('GearShelf', ao=ao)
    exo_stand(k).finish('ExoStand', ao=ao)
    locker(k, 'A').finish('Locker', ao=ao)
    locker(k, 'B').finish('Locker_B', ao=ao)
    cases(k, 'A').finish('Cases', ao=ao)
    cases(k, 'B').finish('Cases_B', ao=ao)
    ammo_crate(k).finish('AmmoCrate', ao=ao)
    # rooms
    ops_console(k).finish('OpsConsole', ao=ao)
    ops_desk(k).finish('OpsDesk', ao=ao)
    seat_row(k).finish('SeatRow', ao=ao)
    lectern(k).finish('Lectern', ao=ao)
    for kind, nm in (('fig', 'Plant'), ('snake', 'Plant_B')):
        O.plant(k, kind).finish(nm, ao=ao)
    bench(k).finish('Bench', ao=ao)
    vending(k, 'A').finish('Vending', ao=ao)
    vending(k, 'B').finish('Cooler', ao=ao)
    front_desk(k).finish('FrontDesk', ao=ao)
    bio_gate(k).finish('BioGate', ao=ao)
    sim_booth(k).finish('SimBooth', ao=ao)
    holo_target(k).finish('HoloTarget', ao=ao)
    drone_cradle(k, 'A').finish('DroneCradle', ao=ao)
    drone_cradle(k, 'B').finish('DroneCradle_B', ao=ao)
    vault(k).finish('Landmark_Vault', ao=ao)
    holo_table(k).finish('Landmark_Holo', ao=ao)
    server_rack(k).finish('ServerRack', ao=ao)
    column(k).finish('Column', ao=ao)
    coffee(k).finish('Coffee', ao=ao)
    # roof
    for cut in ('', 'L', 'R', 'LR'):
        parapet(k, cut).finish('Parapet' + cut, ao=ao)
        parapet(k, cut, kerb=True).finish('Kerb' + cut, ao=ao)
    plank(k, 6).finish('Plank_6')
    plank(k, 8).finish('Plank_8')
    fan(k, 0.74, 5).finish('Fan_HVAC')
    fan(k, 1.62, 7).finish('Fan_Tower')
    hvac(k).finish('HVAC', ao=ao)
    cooling_tower(k).finish('CoolingTower', ao=ao)
    water_tank(k).finish('WaterTank', ao=ao)
    machine_room(k).finish('MachineRoom', ao=ao)
    mast(k).finish('Mast', ao=ao)
    gantry(k).finish('Landmark_Gantry', ao=ao)
    skylight(k).finish('Skylight', ao=ao)
    solar(k).finish('Solar', ao=ao)
    vent(k, 'A').finish('Vent', ao=ao)
    vent(k, 'B').finish('Vent_B', ao=ao)
    roof_duct(k).finish('RoofDuct', ao=ao)
    plank_stack(k).finish('PlankStack', ao=ao)
    roof_hatch(k).finish('RoofHatch', ao=ao)
    # skyline (the spire's tower styles, this theme's table)
    rows, base = read_skyline()
    for name in sorted(rows):
        SP.backdrop(k, rows, name, base).finish(name)
    total = 0
    for n in sorted(k.tris):
        total += k.tris[n]
    for n in sorted(k.tris, key=lambda q: -k.tris[q])[:14]:
        print('%-40s %6d tris' % (n, k.tris[n]))
    print('kit-highrise: %d pieces, %d tris (one of each)' % (len(k.tris), total))
    export(FAM)


def read_skyline():
    import json
    import os
    import re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'data', 'themes', 'highrise.js'), encoding='utf-8').read()
    m = re.search(r'/\*SKYLINE-BEGIN\*/(.*?)/\*SKYLINE-END\*/', src, re.S)
    txt = re.sub(r"'", '"', m.group(1))
    txt = re.sub(r'(\w+)\s*:', r'"\1":', txt)
    base = float(re.search(r'var BASE = (-?[\d.]+)', src).group(1))
    return json.loads(txt), base


FAMILY = 'kit-highrise'
BUILD = build_kit_highrise
