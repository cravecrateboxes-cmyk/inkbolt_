"""INKBOLT asset family: kit-city2 ('Downtown at Dusk').

A dense downtown at sunset, clearly not Small City's sunny two-storey main street nor the office skyline: 4-6 storey
brownstones, red-brick tenements hung with fire escapes, cream cast-iron lofts and lavender art-deco fronts, warm lit
windows, neon blade signs and sign bands over dark shop glass, an elevated railway on riveted green steel running
down the avenue (one span carries a stopped train), a subway entrance, a bronze statue on a granite plaza, yellow
cabs, box trucks, newsstands, hot-dog carts, steam stacks, billboards on steel legs. Beyond the walls: tenement
rows with water tanks and lit windows, dusk towers and a deco spire.

Conventions (shared with kit-smallcity / kit-castle; see ib_lib.py):
  * 1 cell = 1 m; a piece's origin is the centre of its cell / footprint at floor level
  * a facade module's face is its Blender -Y side; the theme sets wall.facing = 'open' so the engine turns it to the
    module's single open side; corners and notches get four-way symmetric corner piers
  * facade modules drop their outline shell on the +/-X faces ('noside') so a building reads as one facade;
    pilasters (building boundaries) and corners keep the full ink outline
  * every coplanar pair of faces is avoided by construction (check_zfight fails the build otherwise)
"""
import math
import random

import bpy  # must load before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector

from ib_lib import *  # noqa: F401,F403
import ib_lib
from fam_kit_smallcity import PM, post_hull, col_box, tile, grid_cells, slant, wheel
from fam_kit_castle import poly_y

FAM = 'kit-city2'
PRE = 'KIT_CITY2_'
ib_lib.GLB[FAM] = 'fps-kit-city2.glb'
ib_lib.CFG[FAM] = (0.02, 0.02)
ib_lib.PALETTES[FAM] = BASE + [
    # facades
    ('brown', '#8E5644'), ('brownL', '#A86C55'), ('brick', '#A2463A'), ('brickD', '#7E3530'),
    ('iron', '#E2D5BA'), ('ironD', '#C8B999'), ('deco', '#B6ABC6'), ('decoD', '#9286A8'),
    ('stone', '#D6C8AB'), ('trim', '#3B3346'), ('cornice', '#5B4C5E'), ('roof', '#4C4656'),
    # windows and shops
    ('lit', '#FFD27A'), ('litW', '#FFF0C2'), ('winD', '#3D4B6B'), ('curtain', '#E9875D'),
    ('shopG', '#2F2A3A'), ('neonP', '#FF4FA8'), ('neonC', '#45E6F2'), ('neonY', '#FFE45A'),
    ('neonG', '#7CF28A'), ('awnR', '#C2354A'), ('awnT', '#2C8A8A'), ('awnV', '#6B4FA0'),
    # street
    ('asphalt', '#4F4C5C'), ('walk', '#A99E99'), ('walkB', '#9D928E'), ('curb', '#857B79'),
    ('granite', '#BCB1AC'), ('graniteD', '#ADA29D'), ('paintW', '#EEEAE2'), ('paintY', '#F2C14A'),
    # steel, vehicles
    ('el', '#3F5E50'), ('elD', '#2D453A'), ('steel', '#7B8796'), ('silver', '#CBD1DA'),
    ('cab', '#F6C33B'), ('plum', '#6E3F70'), ('tealC', '#2F7A7E'), ('truck', '#ECE5D8'),
    ('tire', '#2A2830'), ('chrome', '#D3D8DF'),
    # props, nature, backdrop
    ('hydrant', '#D2453B'), ('mailB', '#2F4F8F'), ('newsG', '#3E7B4E'), ('bronze', '#A07A48'),
    ('bronzeD', '#735634'), ('leaf', '#5F9A57'), ('leafD', '#487A45'), ('trunk', '#6A4C3C'),
    ('steam', '#F3EFEA'), ('stack', '#F08A3A'), ('bdA', '#6E5C80'), ('bdB', '#8C6F7C'),
    ('bdC', '#514868'), ('wood', '#8A5E44'),
]
assert len(ib_lib.PALETTES[FAM]) <= 64, len(ib_lib.PALETTES[FAM])

HT = 0.02
G_H, U_H = 4.2, 3.2       # ground floor / upper floor heights
PAR = 0.9


def top_of(n):
    return G_H + (n - 1) * U_H


def make(name, m, bevel=0.0, hull=HT, ao=False):
    obj = build_object(PRE + name, m, bevel, hull, ao=ao)
    post_hull(obj, m.hmode)
    return obj


def F(d):
    return -0.5 - d


# facade materials: body, trim (sills / lintels), cornice, pier colour
MATS = {'B': ('brown', 'stone', 'cornice', 'brownL'), 'K': ('brick', 'stone', 'brickD', 'brickD'),
        'I': ('iron', 'ironD', 'ironD', 'ironD'), 'D': ('deco', 'stone', 'decoD', 'decoD')}
# building styles: (material, neon / awning colour, storeys). Mirrored by STY in src/data/themes/city2.js.
STYLES = [('B', 'neonP', 5), ('K', 'neonC', 6), ('I', 'neonY', 4), ('D', 'neonG', 6),
          ('K', 'neonP', 5), ('B', 'neonC', 4), ('I', 'neonP', 5), ('D', 'neonY', 5)]
AWN = {'neonP': 'awnR', 'neonC': 'awnT', 'neonY': 'awnV', 'neonG': 'awnT'}
ESC = ('B', 'K')          # materials that carry fire escapes


# ================================================================ facades
def flat(m, x0, x1, d, emb, z0, z1, color):
    """Hairline facade layer (frame, glass, blind, mullion): only its front face, no outline."""
    m.bx(x0, x1, F(d), -0.5 + emb, z0, z1, color, hull='none', cull='ktblr')


def ledge(m, x0, x1, d, z0, z1, color):
    """Sill / lintel: front and underside (and the top below eye height); ends and back are never seen."""
    m.bx(x0, x1, F(d), -0.5, z0, z1, color, hull='none', cull='klr' + ('t' if z1 > 5.0 else ''))


def window(m, mat, x0, x1, z0, z1, glass):
    body, trim, cor, pier = MATS[mat]
    flat(m, x0 - 0.04, x1 + 0.04, 0.02, 0.02, z0, z1, 'trim')                         # inked frame
    flat(m, x0, x1, 0.03, 0.03, z0 + 0.04, z1 - 0.04, glass)
    if glass == 'lit' and (x1 - x0) > 0.4:
        flat(m, x0 + 0.01, x1 - 0.01, 0.036, 0.036, z1 - 0.5, z1 - 0.06, 'curtain')        # half-drawn blind
    flat(m, (x0 + x1) / 2 - 0.02, (x0 + x1) / 2 + 0.02, 0.042, 0.042, z0 + 0.06, z1 - 0.06, 'trim')   # mullion
    ledge(m, x0 - 0.09, x1 + 0.09, 0.07, z0 - 0.1, z0, trim)                         # sill
    if mat == 'B':
        ledge(m, x0 - 0.1, x1 + 0.1, 0.08, z1, z1 + 0.28, trim)                      # heavy brownstone lintel
    elif mat == 'K':
        ledge(m, x0 - 0.06, x1 + 0.06, 0.04, z1, z1 + 0.16, 'brickD')                # soldier course
    elif mat == 'I':
        ledge(m, x0 - 0.05, x1 + 0.05, 0.05, z1, z1 + 0.12, 'ironD')


def floors(m, mat, n, seed, kind, zmin=0.0):
    """Upper floors of one module: windows (lit / dark by a seeded pattern) and per-material piers and bands."""
    rnd = random.Random(seed)
    body, trim, cor, pier = MATS[mat]
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        glass = 'lit' if rnd.random() < 0.42 else 'winD'
        if z0 < zmin:
            continue
        if mat == 'I':        # cast iron: wide window between half columns at the module edges
            for sx in (-1, 1):
                x0, x1 = sorted((sx * 0.5, sx * 0.4))
                m.bx(x0, x1, F(0.07), -0.5, z0, z0 + U_H, 'ironD', hull='none', cull='k')
            window(m, mat, -0.3, 0.3, z0 + 0.55, z0 + 2.65, glass)
        elif mat == 'D':      # deco: continuous piers, dark spandrels
            for sx in (-1, 1):
                x0, x1 = sorted((sx * 0.5, sx * 0.36))
                m.bx(x0, x1, F(0.1), -0.5, z0, z0 + U_H, 'stone' if k % 2 else 'deco', hull='none', cull='k')
            flat(m, -0.36, 0.36, 0.015, 0.0, z0 + 2.6, z0 + U_H, 'decoD')
            flat(m, -0.28, 0.28, 0.02, 0.02, z0 + 0.4, z0 + 2.5, 'trim')
            flat(m, -0.25, 0.25, 0.03, 0.03, z0 + 0.43, z0 + 2.47, glass)
            flat(m, -0.02, 0.02, 0.04, 0.04, z0 + 0.46, z0 + 2.44, 'trim')
        else:
            window(m, mat, -0.27, 0.27, z0 + 0.7, z0 + 2.5, glass)
        if mat == 'B' and k == 1:
            m.det(-0.5, 0.5, 0.05, 0.0, z0, z0 + 0.14, trim, hull='noside')     # first-floor band


def cornice(m, mat, n):
    body, trim, cor, pier = MATS[mat]
    T = top_of(n)
    if mat == 'B':        # bracketed metal cornice
        m.bx(-0.5, 0.5, F(0.32), -0.5, T, T + 0.5, cor, hull='noside', cull='k')
        for x in (-0.28, 0.22):
            m.bx(x - 0.06, x + 0.06, F(0.26), -0.5, T - 0.45, T, cor, hull='none', cull='kt')
        m.bx(-0.5, 0.5, F(0.34), -0.5, T + 0.5, T + 0.58, 'trim', hull='noside', cull='k')
    elif mat == 'K':
        m.det(-0.5, 0.5, 0.12, 0.0, T, T + 0.3, 'brickD', hull='noside')
        m.det(-0.5, 0.5, 0.06, 0.0, T - 0.35, T - 0.25, 'stone', hull='noside')
    elif mat == 'I':      # dentil cornice
        m.bx(-0.5, 0.5, F(0.26), -0.5, T + 0.1, T + 0.5, 'iron', hull='noside', cull='k')
        for x in (-0.375, -0.125, 0.125, 0.375):
            m.bx(x - 0.05, x + 0.05, F(0.18), -0.5, T - 0.05, T + 0.1, 'ironD', hull='none', cull='k')
    else:                 # deco: stepped crown
        m.det(-0.5, 0.5, 0.14, 0.0, T, T + 0.22, 'decoD', hull='noside')
        m.det(-0.5, 0.5, 0.08, 0.0, T + 0.22, T + 0.6, 'stone', hull='noside')


def body(m, mat, n, hull='noside', lip=0.04):
    b, trim, cor, pier = MATS[mat]
    T = top_of(n)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PAR, b, hull=hull, cull='bt')
    m.bx(-0.5, 0.5, F(lip), 0.5, T + PAR, T + PAR + 0.12, 'stone' if mat != 'D' else 'decoD', hull=hull, cull='b')   # coping


def shopfront(m, mat, shop, kind):
    """Ground floor: dark shop panel, sign band with neon, lit display window or door, a flat awning on some."""
    awn = AWN[shop]
    m.bx(-0.5, 0.5, F(0.025), -0.5, 0.06, G_H, 'shopG', hull='noside', cull='ktblr')
    m.bx(-0.5, 0.5, F(0.12), F(0.025), 3.25, 4.05, 'trim', hull='noside', cull='klr')               # sign band
    m.bx(-0.5, 0.5, F(0.14), F(0.025), 4.05, 4.2, MATS[mat][2], hull='noside', cull='klr')          # cap
    m.bx(-0.5, 0.5, F(0.04), F(0.025), 0.06, 0.36, 'trim', hull='noside', cull='kblr')                # kick plate
    if kind == 'win':
        flat(m, -0.43, 0.43, 0.045, 0.02, 0.36, 3.05, 'trim')
        flat(m, -0.4, 0.4, 0.055, 0.03, 0.42, 3.0, 'lit')
        flat(m, -0.42, 0.42, 0.062, 0.035, 2.35, 2.43, 'trim')                                          # transom bar
        flat(m, -0.33, -0.27, 0.06, 0.035, 0.9, 2.2, 'litW')                                            # shine
        for x0, x1 in ((-0.4, -0.1), (0.04, 0.32)):                                                     # neon letters
            m.bx(x0, x1, F(0.135), F(0.12) + 0.004, 3.5, 3.62, shop, hull='none', cull='ktblr')
        m.bx(-0.4, 0.4, F(0.135), F(0.12) + 0.004, 3.33, 3.37, shop, hull='none', cull='ktblr')
    elif kind == 'door':
        m.det(-0.36, 0.36, 0.045, 0.02, 0.0, 3.0, 'trim')
        m.det(-0.3, 0.3, 0.055, 0.03, 0.0, 2.35, 'wood')
        flat(m, -0.22, 0.22, 0.062, 0.035, 0.95, 2.15, 'lit')
        flat(m, -0.3, 0.3, 0.055, 0.03, 2.45, 2.92, 'litW')
        # neon blade sign on a bracket, both faces lit
        m.bx(-0.03, 0.03, -1.05, -0.49, 6.3, 6.36, 'trim', hull='none', cull='k')
        m.bx(-0.04, 0.04, -1.0, -0.62, 4.45, 6.3, 'trim')
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.04, sx * 0.052))
            for (z0, z1) in ((5.85, 6.15), (5.35, 5.7), (4.85, 5.2)):
                m.bx(x0, x1, -0.94, -0.68, z0, z1, shop, hull='none', cull='r' if sx < 0 else 'l')
    if kind in ('win', 'door') and mat in ('B', 'I'):   # flat awning, valance in the neon colour
        yb, yf = F(0.12), F(0.12) - 0.86       # stays inside the street cell: never meets a perpendicular awning
        m.prism([(yb, 3.2), (yf, 2.86), (yf, 2.7), (yb, 3.1)], -0.5, 0.5, [awn], skip=(3,))
        m.bx(-0.497, 0.497, yf - 0.012, yf, 2.72, 2.8, shop, hull='none', cull='k')
    if kind == 'pier':
        m.det(-0.12, 0.12, 0.09, 0.02, 0.36, 3.25, MATS[mat][3])                                        # iron column


def escape(m, n, part):
    """Fire escape on the upper floors: grating platform, railing, and (part 'A') a stair to the next floor up,
    (part 'B') the drop ladder under the first platform."""
    for k in range(1, n):
        z = G_H + (k - 1) * U_H
        z += 0.08
        m.bx(-0.5, 0.5, -1.38, -0.6, z - 0.06, z, 'trim', hull='none', cull='lr')              # platform
        m.bx(-0.42, 0.42, -0.6, -0.5, z - 0.05, z - 0.01, 'trim', hull='none', cull='klrt')    # wall angle
        m.bx(-0.5, 0.5, -1.4, -1.36, z + 0.9, z + 0.96, 'trim', hull='none', cull='lr')        # top rail
        m.bx(-0.5, 0.5, -1.4, -1.37, z + 0.42, z + 0.46, 'trim', hull='none', cull='lrt')      # mid rail
        for x in (-0.25, 0.25):
            m.bx(x - 0.015, x + 0.015, -1.395, -1.375, z, z + 0.9, 'trim', hull='none', cull='tb')
        if part == 'A' and k < n - 1:
            m.bm_((-0.4, -0.95, z), (0.4, -0.95, z + U_H - 0.06), 0.07, 'trim', hull='none')
            m.bm_((-0.4, -1.25, z), (0.4, -1.25, z + U_H - 0.06), 0.07, 'trim', hull='none')
        if part == 'A' and k == n - 1:                                                           # roof ladder
            m.bx(-0.2, -0.17, -0.67, -0.575, z, z + U_H + 0.9, 'trim', hull='none')
            m.bx(0.17, 0.2, -0.67, -0.575, z, z + U_H + 0.9, 'trim', hull='none')
    if part == 'B':
        z = G_H - 0.06
        for x in (-0.2, 0.2):
            m.bx(x - 0.02, x + 0.02, -1.3, -1.25, z - 1.4, z, 'trim', hull='none')
        for k in range(4):
            m.bx(-0.18, 0.18, -1.29, -1.265, z - 1.3 + k * 0.33, z - 1.27 + k * 0.33, 'trim', hull='none')


def build_facades(pal):
    for si, (mat, shop, n) in enumerate(STYLES):
        kinds = [('Win', 'win', 3), ('Win2', 'win', 17), ('Door', 'door', 5), ('Pier', 'pier', 9)]
        if mat in ESC:
            kinds += [('EscA', 'win', 23), ('EscB', 'pier', 29), ('EscC', 'win', 31)]
        for name, sk, seed in kinds:
            m = PM(pal)
            body(m, mat, n)
            shopfront(m, mat, shop, sk)
            floors(m, mat, n, seed * 7 + si, name)
            cornice(m, mat, n)
            if name.startswith('Esc'):
                escape(m, n, name[3])
            make('%s_%d' % (name, si), m)
        # the El runs into the facade through a dark portal (steel lintel, girder shadow)
        m = PM(pal)
        body(m, mat, n)
        m.det(-0.5, 0.5, 0.012, 0.0, 4.6, 8.4, 'ink', hull='noside')
        m.det(-0.5, 0.5, 0.18, 0.0, 8.4, 8.9, 'el', hull='noside')
        m.det(-0.5, 0.5, 0.025, 0.0, 0.06, 0.36, 'trim', hull='noside')
        floors(m, mat, n, 41 + si, 'Portal', zmin=9.0)
        cornice(m, mat, n)
        make('Portal_%d' % si, m)
    for mat, n in sorted({(st[0], st[2]) for st in STYLES}):
        pilaster(pal, mat, n)
        corner(pal, mat, n)
        m = PM(pal)
        body(m, mat, n, lip=0.0)          # inner corners: nothing proud, the perpendicular facade owns the corner
        m.det(-0.46, 0.46, 0.02, 0.0, 0.06, 0.38, 'trim', hull='noside')
        make('Blank_%s%d' % (mat, n), m)


def pilaster(pal, mat, n):
    b, trim, cor, pier = MATS[mat]
    T = top_of(n)
    m = PM(pal)
    body(m, mat, n, hull='full')
    m.bx(-0.44, 0.44, F(0.12), -0.49, 0.5, T + PAR + 0.3, pier, cull='kbt')
    m.bx(-0.47, 0.47, F(0.15), -0.49, 0, 0.5, 'trim', cull='kb')
    m.bx(-0.5, 0.5, F(0.2), -0.5, T - 0.1, T + 0.45, cor, cull='k')
    m.bx(-0.48, 0.48, F(0.15), 0.5, T + PAR + 0.3, T + PAR + 0.42, 'stone', cull='b')
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        m.det(-0.18, 0.18, 0.135, 0.02, z0 + 1.2, z0 + 1.8, 'stone', back=-0.48)
    return make('Pilaster_%s%d' % (mat, n), m)


def corner(pal, mat, n):
    b, trim, cor, pier = MATS[mat]
    T = top_of(n)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PAR, b, cull='bt')
    q = 0.535
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(min(sx * 0.38, sx * q), max(sx * 0.38, sx * q), min(sy * 0.38, sy * q), max(sy * 0.38, sy * q), 0.4, T, pier, cull='bt')
    m.bx(-0.56, 0.56, -0.56, 0.56, 0, 0.4, 'trim', cull='b')
    m.bx(-0.58, 0.58, -0.58, 0.58, 4.0, 4.26, cor)
    m.bx(-0.73, 0.73, -0.73, 0.73, T - 0.07, T + 0.4, cor, cull='t')
    m.bx(-0.565, 0.565, -0.565, 0.565, T + PAR + 0.02, T + PAR + 0.17, 'stone')
    return make('Corner_%s%d' % (mat, n), m)


# ================================================================ street surface
def build_floor(pal):
    for name, c, j in (('Walk', 'walk', 'curb'), ('WalkB', 'walkB', 'curb'), ('Plaza', 'granite', 'graniteD'), ('PlazaB', 'graniteD', 'curb')):
        m = PM(pal)
        tile(m, 0, 0, c, j)
        make(name, m, hull=0)
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.22, 0.22, 0.006, 0.014, 'paintW', hull='none')
    make('Zebra', m, hull=0)
    m = PM(pal)
    m.bx(-0.3, 0.3, -0.06, 0.06, 0.006, 0.013, 'paintW', hull='none')
    make('LaneW', m, hull=0)
    m = PM(pal)
    for sy in (-1, 1):
        m.bx(-0.5, 0.5, sy * 0.13 - 0.05, sy * 0.13 + 0.05, 0.006, 0.013, 'paintY', hull='none')
    make('LaneY', m, hull=0)
    m = PM(pal)
    m.cy((0, 0, 0.006), 0.36, 0.36, 0.012, 'steel', seg=14, hull='none')
    for k in range(4):
        m.bx(-0.26 + k * 0.15, -0.22 + k * 0.15, -0.24, 0.24, 0.01, 0.0215, 'trim', hull='none')
    make('Manhole', m, hull=0)


# ================================================================ gate, trail, hatch
GW = 2.96


def build_gate(pal, ao):
    """Gate building bridging the street: a riveted steel portal over the 3 m opening and four storeys of brick
    with lit windows above it (the same on both faces), cornice, water tank and a teal 'ZONE' neon bar, so the slot
    between the facades is closed right up to the rooflines."""
    m = PM(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.48, sx * GW))
        m.bx(x0, x1, -1.0, 1.0, 0, 20.6, 'brick', cull='b')                                     # piers / walls
    m.bx(-1.48, 1.48, -1.0, 1.0, 4.4, 20.6, 'brick', cull='')                                   # bridge block
    m.bx(-GW - 0.1, GW + 0.1, -1.08, 1.08, 20.6, 21.0, 'cornice')
    m.bx(-GW - 0.04, GW + 0.04, -1.03, 1.03, 21.0, 21.6, 'brick', cull='b')
    m.bx(-GW - 0.08, GW + 0.08, -1.06, 1.06, 21.6, 21.72, 'stone')
    for sy in (-1, 1):
        m.parent = Matrix.Rotation(0 if sy < 0 else math.pi, 4, 'Z')
        # steel portal: riveted girder lintel and posts
        m.bx(-1.75, 1.75, -1.12, -0.98, 3.2, 4.4, 'el')
        for x in (-1.6, 1.6):
            m.bx(x - 0.18, x + 0.18, -1.14, -0.98, 0, 3.2, 'el')
            m.bx(x - 0.22, x + 0.22, -1.17, -0.99, 0, 0.35, 'elD')
        for k in range(6):
            x = -1.5 + k * 0.6
            for z in (3.32, 4.28):
                m.bx(x - 0.03, x + 0.03, -1.135, -1.11, z - 0.03, z + 0.03, 'elD', hull='none', cull='k')
        m.bx(-1.3, 1.3, -1.135, -1.11, 3.62, 3.98, 'neonC', hull='none', cull='k')               # neon bar
        m.bx(-1.1, -0.6, -1.145, -1.13, 3.7, 3.9, 'ink', hull='none', cull='k')
        m.bx(-0.3, 0.3, -1.145, -1.13, 3.7, 3.9, 'ink', hull='none', cull='k')
        m.bx(0.6, 1.1, -1.145, -1.13, 3.7, 3.9, 'ink', hull='none', cull='k')
        # windows on four storeys over the street
        for k in range(4):
            z0 = 5.0 + k * 3.6
            for x in (-2.0, -0.7, 0.7, 2.0):
                glass = 'lit' if (k * 3 + int(x * 2) + (sy > 0)) % 3 == 0 else 'winD'
                m.bx(x - 0.36, x + 0.36, -1.03, -0.99, z0 + 0.5, z0 + 2.6, 'trim', hull='none', cull='ktblr')
                m.bx(x - 0.31, x + 0.31, -1.05, -1.02, z0 + 0.55, z0 + 2.55, glass, hull='none', cull='ktblr')
                m.bx(x - 0.42, x + 0.42, -1.1, -0.99, z0 + 0.38, z0 + 0.5, 'stone', hull='none', cull='klr')
                m.bx(x - 0.4, x + 0.4, -1.08, -0.99, z0 + 2.6, z0 + 2.8, 'stone', hull='none', cull='klr')
        for z in (4.6, 19.4):
            m.bx(-GW - 0.04, GW + 0.04, -1.06, -0.99, z, z + 0.2, 'stone', hull='none', cull='k')
        # amber caution lamps on the posts
        for x in (-1.6, 1.6):
            m.bx(x - 0.1, x + 0.1, -1.3, -1.14, 2.7, 2.95, 'amber', hull='none')
    m.parent = Matrix.Identity(4)
    # roof water tank
    for x in (-0.9, 0.9):
        for y in (-0.5, 0.5):
            m.bx(x - 0.07, x + 0.07, y - 0.07, y + 0.07, 21.72, 23.2, 'trim', hull='none')
    m.cy((0, 0, 23.2), 1.25, 1.25, 2.4, 'wood', seg=10)
    m.cy((0, 0, 25.6), 1.35, 0.1, 1.2, 'cornice', seg=10)
    m.bx(-1.505, 1.505, -0.12, 0.12, 3.06, 4.4, 'trim', hull='none', cull='t')                     # shutter box
    make('GateFrame', m, ao=ao)
    # roll-down steel grille with the hazard band at the foot
    m = PM(pal)
    H, slats = 3.05, 12
    for i in range(slats):
        z0 = 0.42 + i * (H - 0.42) / slats
        m.bx(-1.5, 1.5, -0.07, 0.07, z0, z0 + (H - 0.42) / slats - 0.03, 'steel' if i % 2 else 'silver', hull='none')
    for k in range(10):
        m.bx(-1.5 + k * 0.3, -1.2 + k * 0.3, -0.08, 0.08, 0.0, 0.4, 'ink' if k % 2 else 'amber', hull='none')
    sh = make('GateShutter', m, hull=0)
    m = PM(pal)
    m.bx(-1.5, 1.5, -0.08, 0.08, 0, H, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(sh, tmp)


TRAIL_H = 16.0


def build_trail(pal, ao):
    """Trail wall: 1 m of a brick alley between two blocks, 16 m high so the passages are closed canyons. It is
    repeated every metre, so it is dressed only with things that repeat in a real wall: brick courses, a stone plinth,
    stone floor bands and soldier courses, and one small window per metre on two upper floors (lit or dark by floor).
    Both faces alike (the hatch room turns some modules round)."""
    m = PM(pal)
    m.bx(-0.25, 0.25, -0.5, 0.5, 0.6, TRAIL_H, 'brick', hull='noend', cull='bt')
    m.bx(-0.3, 0.3, -0.5, 0.5, 0, 0.6, 'stone', hull='noend', cull='b')
    m.bx(-0.33, 0.33, -0.5, 0.5, TRAIL_H, TRAIL_H + 0.18, 'stone', hull='noend')
    for sx in (-1, 1):
        cl = 'r' if sx < 0 else 'l'

        def face(d0, d1, y0, y1, z0, z1, c):
            x0, x1 = sorted((sx * (0.25 + d0), sx * (0.25 + d1)))
            m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cl + 'tbfk')
        for k in range(26):                                                                    # brick courses
            z = 0.9 + k * 0.58
            if abs(z - 4.3) < 0.4 or abs(z - 10.7) < 0.4:
                continue
            face(0.0, 0.004, -0.5, 0.5, z, z + 0.03, 'brickD')
        for zb in (4.15, 10.55):                                                               # stone bands
            x0, x1 = sorted((sx * 0.25, sx * 0.3))
            m.bx(x0, x1, -0.5, 0.5, zb, zb + 0.3, 'stone', hull='none', cull=cl + 'fk')
        for k, (z0, lit) in enumerate(((7.0, sx < 0), (13.4, sx > 0))):                      # small windows
            face(0.0, 0.012, -0.24, 0.24, z0 - 0.2, z0, 'brickD')                              # soldier course
            face(0.0, 0.01, -0.2, 0.2, z0 - 1.5, z0 - 0.2, 'trim')
            face(0.0, 0.016, -0.17, 0.17, z0 - 1.47, z0 - 0.23, 'lit' if lit else 'winD')
            x0, x1 = sorted((sx * 0.25, sx * 0.3))
            m.bx(x0, x1, -0.24, 0.24, z0 - 1.62, z0 - 1.5, 'stone', hull='none', cull=cl)
    make('TrailWall', m, ao=ao)


def build_hatch(pal, ao):
    """Exit pad: a sidewalk cellar hatch (diamond-plate double doors in a steel frame), teal lamps around it."""
    m = PM(pal)
    m.cy((0, 0, 0), 1.3, 1.24, 0.1, 'walk', seg=20, bevel=True)
    m.cy((0, 0, 0.1), 1.08, 1.08, 0.025, 'teal', seg=20, hull='none')
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.105, 0.17, 'trim')
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.03, sy * 0.84))
        m.bx(-0.84, 0.84, y0, y1, 0.165, 0.185, 'steel', hull='none', cull='b')
        for k in range(5):
            for j in range(3):
                x = -0.6 + k * 0.3
                y = sy * (0.2 + j * 0.25)
                m.bx(x - 0.05, x + 0.05, y - 0.02, y + 0.02, 0.18, 0.192, 'silver', hull='none', cull='b')
    m.cy((0.0, -0.3, 0.185), 0.06, 0.06, 0.02, 'amber', seg=6, hull='none')
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        m.cy((math.cos(a) * 1.17, math.sin(a) * 1.17, 0.1), 0.06, 0.05, 0.06, 'amber', seg=6, hull='none')
    make('Hatch', m, bevel=0.015, ao=ao)


# ================================================================ vehicles (front = Blender -Y = game +Z)
def build_car(pal, name, bodyc, cab=False, ad=False, ao=False):
    """A long 70s-style sedan: low body, set-back greenhouse, chrome bumpers; the cab has a checker band and a lit
    roof sign (or a roof advertising box)."""
    m = PM(pal)
    for sx in (-1, 1):
        for y in (-1.25, 1.3):
            wheel(m, sx * 0.9, y, 0.33, 0.22, seg=8)
    m.bx(-0.87, 0.87, -1.95, 1.95, 0.3, 0.86, bodyc, bevel=True)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 1.9, sy * 2.0))
        m.bx(-0.86, 0.86, y0, y1, 0.28, 0.46, 'chrome')
    cabin = [(-0.62, 0.86), (-0.22, 1.36), (0.82, 1.36), (1.15, 0.86)]
    m.prism(cabin, -0.76, 0.76, [bodyc])
    m.prism([(-0.58, 0.89), (-0.21, 1.33), (0.8, 1.33), (1.11, 0.89)], -0.766, 0.766, ['ink'], hull='none')
    m.prism([(-0.55, 0.91), (-0.2, 1.31), (0.78, 1.31), (1.08, 0.91)], -0.772, 0.772, ['litW' if cab else 'winD'], hull='none')
    m.bx(-0.778, 0.778, 0.25, 0.37, 0.9, 1.34, bodyc, hull='none')
    for (p0, p1) in ((cabin[0], cabin[1]), (cabin[2], cabin[3])):
        m.prism(slant(p0, p1, 0.06, 0.94, -0.01, 0.006), -0.71, 0.71, ['ink'], hull='none')
        m.prism(slant(p0, p1, 0.12, 0.88, -0.004, 0.014), -0.66, 0.66, ['winD'], hull='none')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.48, sx * 0.78))
        m.bx(x0, x1, -1.985, -1.95, 0.6, 0.74, 'litW', hull='none', cull='k')
        m.bx(x0, x1, 1.95, 1.985, 0.6, 0.76, 'red', hull='none', cull='f')
        x0, x1 = sorted((sx * 0.866, sx * 0.874))
        m.bx(x0, x1, -0.5, -0.482, 0.34, 0.84, 'ink', hull='none', cull='l' if sx > 0 else 'r')
        m.bx(x0, x1, 0.4, 0.418, 0.34, 0.84, 'ink', hull='none', cull='l' if sx > 0 else 'r')
        x0, x1 = sorted((sx * 0.76, sx * 0.94))
        m.bx(x0, x1, -0.45, -0.34, 0.98, 1.08, bodyc)
    m.bx(-0.4, 0.4, -1.985, -1.95, 0.48, 0.6, 'trim', hull='none', cull='k')
    if cab:
        for sx in (-1, 1):                                                                         # checker band
            x0, x1 = sorted((sx * 0.871, sx * 0.88))
            for k in range(8):
                y = -1.3 + k * 0.3
                m.bx(x0, x1, y, y + 0.15, 0.62 + (0.07 if k % 2 else 0), 0.69 + (0.07 if k % 2 else 0), 'ink', hull='none')
        if ad:
            m.bx(-0.55, 0.55, 0.2, 0.45, 1.36, 1.76, 'trim')
            for sx in (-1, 1):
                x0, x1 = sorted((sx * 0.55, sx * 0.56))
                m.bx(x0, x1, 0.23, 0.42, 1.4, 1.72, 'neonP', hull='none')
            for sy in (-1, 1):
                y0, y1 = sorted((0.325 + sy * 0.125, 0.325 + sy * 0.135))
                m.bx(-0.52, 0.52, y0, y1, 1.4, 1.72, 'neonP', hull='none')
        else:
            m.bx(-0.24, 0.24, 0.2, 0.4, 1.36, 1.56, 'litW')
            m.bx(-0.245, 0.245, 0.195, 0.405, 1.44, 1.48, 'ink', hull='none')
    obj = make(name, m, bevel=0.025, ao=ao)
    col_box(obj, 0, -0.9, 0.9, -2.0, 2.0, 0, 0.86)
    col_box(obj, 1, -0.76, 0.76, -0.62, 1.15, 0.86, 1.36)


def build_truck(pal, ao):
    """Box truck 2 x 5: plum cab, cream box with a roll-up rear door, a teal stripe (no lettering)."""
    m = PM(pal)
    for sx in (-1, 1):
        for y in (-1.6, 1.55):
            wheel(m, sx * 0.97, y, 0.4, 0.26)
    m.bx(-0.95, 0.95, -2.45, -1.15, 0.35, 1.3, 'plum', cull='b')
    cab = [(-2.45, 1.3), (-2.15, 2.15), (-1.15, 2.15), (-1.15, 1.3)]
    m.prism(cab, -0.92, 0.92, ['plum'])
    m.prism(slant(cab[0], cab[1], 0.1, 0.92, -0.01, 0.006), -0.84, 0.84, ['ink'], hull='none')
    m.prism(slant(cab[0], cab[1], 0.15, 0.87, -0.004, 0.014), -0.78, 0.78, ['winD'], hull='none')
    m.prism([(-2.25, 1.35), (-2.08, 2.05), (-1.3, 2.05), (-1.3, 1.35)], -0.926, 0.926, ['ink'], hull='none')
    m.prism([(-2.21, 1.39), (-2.06, 2.01), (-1.34, 2.01), (-1.34, 1.39)], -0.932, 0.932, ['winD'], hull='none')
    m.bx(-1.0, 1.0, -1.15, 2.48, 0.42, 2.9, 'truck', bevel=True)
    for sx in (-1, 1):
        inner = 'l' if sx > 0 else 'r'
        x0, x1 = sorted((sx * 1.002, sx * 1.01))
        m.bx(x0, x1, -1.0, 2.35, 1.0, 1.25, 'tealC', hull='none', cull=inner)
        m.bx(x0, x1, -1.0, 2.35, 1.32, 1.38, 'neonP', hull='none', cull=inner)
        x0, x1 = sorted((sx * 0.5, sx * 0.8))
        m.bx(x0, x1, -2.485, -2.45, 0.8, 0.98, 'litW', hull='none')
        m.bx(x0, x1, 2.48, 2.51, 0.6, 0.9, 'red', hull='none')
        x0, x1 = sorted((sx * 0.8, sx * 1.02))
        m.bx(x0, x1, -1.95, -1.82, 1.6, 1.9, 'trim')
    for k in range(7):                                                                              # roll door slats
        z = 0.63 + k * 0.32
        m.bx(-0.85, 0.85, 2.48, 2.495, z, z + 0.06, 'silver', hull='none', cull='f')
    m.bx(-0.94, 0.94, -2.55, -2.42, 0.32, 0.52, 'chrome')
    m.bx(-0.94, 0.94, 2.44, 2.56, 0.3, 0.48, 'trim')
    obj = make('Truck', m, bevel=0.025, ao=ao)
    col_box(obj, 0, -0.96, 0.96, -2.5, -1.15, 0, 2.15)
    col_box(obj, 1, -1.0, 1.0, -1.15, 2.5, 0, 2.9)


# ================================================================ street furniture
def slab(m, cells, kind='walk'):
    c, j = ('walk', 'curb') if kind == 'walk' else ('granite', 'graniteD')
    for (cx, cy) in cells:
        tile(m, cx, cy, c, j)


def build_lamps(pal, ao):
    """'Lamp': cobra-head street light on a tapered pole (sidewalk); 'LampP': twin-globe plaza lamp (granite)."""
    m = PM(pal)
    slab(m, [(0, 0)])
    m.cy((0, 0, 0.05), 0.16, 0.13, 0.5, 'steel', seg=8)
    m.cy((0, 0, 0.55), 0.09, 0.06, 5.6, 'steel', seg=8)
    m.bm_((0, 0, 6.05), (0, -1.6, 6.5), 0.08, 'steel')
    m.bx(-0.2, 0.2, -2.05, -1.5, 6.32, 6.56, 'steel')
    m.bx(-0.16, 0.16, -2.0, -1.55, 6.28, 6.32, 'litW', hull='none')
    m.bx(-0.3, 0.3, 0.1, 0.13, 2.6, 3.3, 'awnV')                                                    # street banner
    m.bx(-0.28, 0.28, 0.13, 0.136, 2.85, 2.95, 'neonY', hull='none')
    obj = make('Lamp', m, ao=ao)
    col_box(obj, 0, -0.13, 0.13, -0.13, 0.13, 0, 5.0)
    m = PM(pal)
    slab(m, [(0, 0)], 'plaza')
    m.cy((0, 0, 0.05), 0.2, 0.16, 0.6, 'elD', seg=8)
    m.cy((0, 0, 0.65), 0.07, 0.07, 3.0, 'elD', seg=8)
    m.cy((0, 0, 3.65), 0.12, 0.08, 0.2, 'elD', seg=8)
    m.bx(-0.75, 0.75, -0.04, 0.04, 3.82, 3.9, 'elD')
    for sx in (-1, 1):
        m.cy((sx * 0.7, 0, 3.9), 0.07, 0.07, 0.1, 'elD', seg=6)
        m.sp((sx * 0.7, 0, 4.2), 0.24, 'litW', seg=(8, 5))
        m.cy((sx * 0.7, 0, 4.42), 0.05, 0.0, 0.12, 'elD', seg=5, hull='none')
    obj = make('LampP', m, ao=ao)
    col_box(obj, 0, -0.16, 0.16, -0.16, 0.16, 0, 4.4)


def build_tree(pal, ao):
    m = PM(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, 0.054, 'trim', hull='none', cull='b')
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.04, 0.058, 'trunk', hull='none', cull='b')
    m.cy((0, 0, 0.044), 0.11, 0.08, 2.8, 'trunk', seg=7)
    m.bm_((0, 0, 2.0), (-0.4, 0.2, 2.9), 0.08, 'trunk')
    m.sp((0, 0, 3.7), 1.25, 'leaf', seg=(8, 5), scale=(1, 1, 0.85))
    m.sp((-0.6, 0.35, 3.2), 0.85, 'leafD', seg=(7, 4))
    m.sp((0.55, -0.4, 3.35), 0.8, 'leafD', seg=(7, 4))
    for (x, y, z) in ((0.4, 0.5, 4.2), (-0.5, -0.4, 4.0)):
        m.sp((x, y, z), 0.12, 'neonY', seg=(5, 3), hull='none')                                   # fairy lights
    obj = make('StreetTree', m, ao=ao)
    col_box(obj, 0, -0.15, 0.15, -0.15, 0.15, 0, 2.6)


def build_furniture(pal, ao):
    m = PM(pal)                                                                                 # hydrant
    slab(m, [(0, 0)])
    m.cy((0, 0, 0.05), 0.17, 0.16, 0.07, 'hydrant', seg=10)
    m.cy((0, 0, 0.12), 0.12, 0.12, 0.46, 'hydrant', seg=10)
    m.cy((0, 0, 0.58), 0.15, 0.15, 0.06, 'hydrant', seg=10)
    m.cy((0, 0, 0.64), 0.14, 0.06, 0.15, 'hydrant', seg=10)
    for x in (0.11, -0.2):
        m.cy((x, 0, 0.42), 0.055, 0.055, 0.09, 'hydrant', seg=8, rot=(0, 90, 0))
    m.cy((0, -0.1, 0.38), 0.07, 0.07, 0.1, 'chrome', seg=8, rot=(90, 0, 0))
    obj = make('Hydrant', m, ao=ao)
    col_box(obj, 0, -0.18, 0.18, -0.18, 0.18, 0, 0.8)
    m = PM(pal)                                                                                 # mailbox
    slab(m, [(0, 0)])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.2, sx * 0.24))
        m.bx(x0, x1, -0.24, 0.24, 0.05, 0.3, 'trim')
    m.bx(-0.24, 0.24, -0.26, 0.26, 0.3, 1.0, 'mailB', bevel=True)
    m.cy((0, 0.255, 1.0), 0.24, 0.24, 0.51, 'mailB', seg=12, rot=(90, 0, 0))
    m.bx(-0.13, 0.13, -0.272, -0.25, 0.86, 0.91, 'ink', hull='none')
    m.bx(-0.1, 0.1, -0.268, -0.25, 0.5, 0.68, 'paper', hull='none')
    obj = make('Mailbox', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.25, 0.25, -0.27, 0.27, 0, 1.24)
    m = PM(pal)                                                                                 # newspaper boxes
    slab(m, [(0, 0)])
    for cx, c in ((-0.23, 'newsG'), (0.23, 'awnR')):
        m.bx(cx - 0.05, cx + 0.05, -0.05, 0.05, 0.05, 0.38, 'trim')
        m.bx(cx - 0.21, cx + 0.21, -0.19, 0.19, 0.38, 1.0, c, cull='t')
        m.bx(cx - 0.215, cx + 0.215, -0.195, 0.195, 1.0, 1.06, c)
        m.bx(cx - 0.17, cx + 0.17, -0.203, -0.177, 0.6, 0.92, 'ink', hull='none')
        m.bx(cx - 0.15, cx + 0.15, -0.21, -0.17, 0.62, 0.9, 'paper', hull='none')
        m.bx(cx - 0.12, cx + 0.12, -0.215, -0.165, 0.81, 0.85, 'ink', hull='none')
    obj = make('NewsBoxes', m, bevel=0.012, ao=ao)
    col_box(obj, 0, -0.45, 0.45, -0.21, 0.21, 0, 1.06)
    m = PM(pal)                                                                                 # wire litter basket
    slab(m, [(0, 0)])
    m.cy((0, 0, 0.05), 0.22, 0.28, 0.85, 'steel', seg=10, caps=False)
    for z in (0.3, 0.6):
        m.cy((0, 0, z), 0.255, 0.27, 0.04, 'trim', seg=10, hull='none', caps=False)
    m.cy((0, 0, 0.9), 0.3, 0.3, 0.05, 'trim', seg=10)
    m.cy((0, 0, 0.62), 0.24, 0.24, 0.3, 'paper', seg=8, hull='none')
    obj = make('TrashCan', m, ao=ao)
    col_box(obj, 0, -0.3, 0.3, -0.3, 0.3, 0, 0.95)


def build_junk(pal, ao):
    m = PM(pal)
    for (x, y, z, r, c) in ((-0.2, -0.12, 0.26, 0.3, 'ink'), (0.22, -0.05, 0.25, 0.28, 'trim'), (0.0, 0.2, 0.24, 0.27, 'ink'), (0.02, -0.02, 0.6, 0.24, 'trim')):
        m.sp((x, y, z), r, c, seg=(7, 4), scale=(1.0, 0.9, 0.95))
        m.cy((x, y, z + r * 0.9), 0.05, 0.02, 0.12, c, seg=5, hull='none')
    obj = make('TrashBags', m, ao=ao)
    col_box(obj, 0, -0.46, 0.46, -0.4, 0.45, 0, 0.85)
    m = PM(pal)
    for (x0, x1, y0, y1, z0, z1) in ((-0.44, 0.06, -0.38, 0.12, 0, 0.45), (0.1, 0.44, -0.3, 0.32, 0, 0.38), (-0.36, 0.02, -0.3, 0.08, 0.45, 0.78), (0.12, 0.4, -0.22, 0.2, 0.38, 0.6)):
        m.bx(x0, x1, y0, y1, z0, z1, 'stone')
        m.bx((x0 + x1) / 2 - 0.04, (x0 + x1) / 2 + 0.04, y0 - 0.004, y1 + 0.004, z1 - 0.06, z1 + 0.004, 'ironD', hull='none')
    obj = make('Boxes', m, bevel=0.01, ao=ao)
    col_box(obj, 0, -0.44, 0.44, -0.38, 0.32, 0, 0.78)
    m = PM(pal)                                                                                 # pallet stack
    for k in range(4):
        z = k * 0.15
        m.bx(-0.45, 0.45, -0.4, 0.4, z + 0.1, z + 0.14, 'wood')
        for x in (-0.38, 0.0, 0.38):
            m.bx(x - 0.05, x + 0.05, -0.4, 0.4, z, z + 0.1, 'wood' if k % 2 else 'trunk', hull='none')
    m.bx(-0.4, 0.3, -0.35, 0.35, 0.6, 0.95, 'stone')
    obj = make('Pallets', m, ao=ao)
    col_box(obj, 0, -0.45, 0.45, -0.4, 0.4, 0, 0.95)


def build_barriers(pal, ao):
    m = PM(pal)                                                                                 # sawhorse barricade
    for sx in (-1, 1):
        x = sx * 0.4
        m.bm_((x, -0.25, 0), (x, 0, 1.0), 0.05, 'paintW')
        m.bm_((x + 0.05, 0.25, 0), (x + 0.05, 0, 1.0), 0.05, 'paintW')
    m.prism([(-0.03, 0.62), (0.03, 0.62), (0.03, 0.92), (-0.03, 0.92)], -0.5, 0.5, ['stack', 'paintW', 'stack', 'paintW', 'stack'], hull='noside')
    m.cy((0.38, 0, 0.92), 0.07, 0.07, 0.14, 'amber', seg=6)
    obj = make('Sawhorse', m, ao=ao)
    col_box(obj, 0, -0.5, 0.5, -0.25, 0.25, 0, 1.0)
    m = PM(pal)
    jp = [(-0.3, 0), (0.3, 0), (0.3, 0.08), (0.12, 0.34), (0.08, 0.9), (-0.08, 0.9), (-0.12, 0.34), (-0.3, 0.08)]
    m.prism(jp, -0.49, 0.49, ['granite'])
    m.prism([(-0.103, 0.62), (0.103, 0.62), (0.0944, 0.74), (-0.0944, 0.74)], -0.495, 0.495, ['stack', 'paintW', 'stack', 'paintW'], hull='none')
    obj = make('Jersey', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.5, 0.5, -0.3, 0.3, 0, 0.9)


def build_steam(pal, ao):
    """Steam stack: an orange-and-white striped chimney over a manhole, puffing steam."""
    m = PM(pal)
    m.cy((0, 0, 0), 0.36, 0.36, 0.02, 'steel', seg=12, hull='none')
    for k in range(4):
        m.cy((0, 0, 0.02 + k * 0.38), 0.25 - k * 0.02, 0.23 - k * 0.02, 0.38, 'stack' if k % 2 == 0 else 'paintW', seg=10)
    for (x, y, z, r) in ((0.0, 0.0, 1.9, 0.3), (0.12, 0.1, 2.35, 0.38), (-0.08, -0.05, 2.85, 0.45), (0.15, 0.06, 3.3, 0.36)):
        m.sp((x, y, z), r, 'steam', seg=(7, 4))
    obj = make('SteamStack', m, ao=ao)
    col_box(obj, 0, -0.26, 0.26, -0.26, 0.26, 0, 1.6)


def build_bench(pal, ao):
    m = PM(pal)
    slab(m, [(-0.5, 0), (0.5, 0)], 'plaza')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.8, sx * 0.88))
        m.bx(x0, x1, -0.26, 0.2, 0.05, 0.42, 'elD')
        m.bx(x0, x1, 0.17, 0.25, 0.42, 0.95, 'elD')
        x0, x1 = sorted((sx * 0.79, sx * 0.89))
        m.bx(x0, x1, -0.28, 0.15, 0.62, 0.67, 'elD')
    for y in (-0.2, -0.06, 0.08):
        m.bx(-0.95, 0.95, y - 0.055, y + 0.055, 0.42, 0.47, 'wood')
    for z in (0.6, 0.78):
        m.bx(-0.95, 0.95, 0.12, 0.17, z, z + 0.12, 'wood')
    obj = make('Bench', m, ao=ao)
    col_box(obj, 0, -0.95, 0.95, -0.28, 0.26, 0, 0.95)


def build_newsstand(pal, ao):
    """Newsstand 2 x 3 on sidewalk paving: green kiosk, lit interior, magazine racks on the open front (-Y)."""
    m = PM(pal)
    slab(m, grid_cells(2, 3))
    m.bx(-0.95, 0.95, -1.2, 1.4, 0.05, 2.5, 'newsG', cull='b')
    m.bx(-0.85, 0.85, -1.21, -1.195, 1.0, 2.2, 'shopG', hull='none', cull='k')
    m.bx(-0.8, 0.8, -1.22, -1.2, 1.05, 2.15, 'lit', hull='none', cull='k')
    m.bx(-0.98, 0.98, -1.25, -1.2, 0.05, 0.95, 'newsG', cull='k')                                      # counter front
    m.bx(-1.0, 1.0, -1.45, -0.9, 0.95, 1.02, 'trim')                                                # counter top
    for k in range(6):                                                                              # papers on the counter
        x = -0.8 + k * 0.32
        m.bx(x - 0.13, x + 0.13, -1.4, -1.0, 1.02, 1.06 + 0.02 * (k % 2), 'paper' if k % 3 else 'neonY', hull='none')
    for row in range(3):                                                                            # magazines on the sides
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.95, sx * 0.97))
            for j in range(3):
                y = -0.9 + j * 0.45
                m.bx(x0, x1, y, y + 0.36, 0.7 + row * 0.5, 1.12 + row * 0.5, ('neonP', 'awnT', 'paintY', 'awnR')[(row + j) % 4], hull='none')
    m.bx(-1.15, 1.15, -1.6, 1.55, 2.5, 2.62, 'trim')                                                # roof
    m.prism([(-1.6, 2.62), (1.55, 2.62), (1.55, 2.68), (-1.6, 2.68)], -1.15, 1.15, ['newsG'], hull='none')
    m.bx(-1.0, 1.0, -1.62, -1.6, 2.2, 2.5, 'neonY', hull='none')                                    # header sign
    for x0, x1 in ((-0.8, -0.3), (-0.15, 0.25), (0.4, 0.8)):
        m.bx(x0, x1, -1.63, -1.62, 2.28, 2.42, 'ink', hull='none')
    obj = make('Newsstand', m, ao=ao)
    col_box(obj, 0, -1.0, 1.0, -1.45, 1.42, 0, 2.62)


def build_hotdog(pal, ao):
    m = PM(pal)
    slab(m, grid_cells(2, 2), 'plaza')
    m.bx(-0.65, 0.65, -0.35, 0.35, 0.4, 1.05, 'silver', bevel=True)
    m.bx(-0.68, 0.68, -0.38, 0.38, 1.05, 1.1, 'steel')
    m.bx(-0.55, 0.55, -0.36, -0.35, 0.5, 0.95, 'awnT', hull='none')
    m.bx(-0.4, 0.4, -0.368, -0.36, 0.65, 0.85, 'paintY', hull='none')
    for y in (0.42, -0.42):
        m.cy((-0.35, y, 0.33), 0.3, 0.3, 0.06, 'trim', seg=10, rot=(90, 0, 0))
    m.bm_((0.62, -0.3, 0.95), (0.95, -0.3, 1.05), 0.04, 'steel')
    m.bm_((0.62, 0.3, 0.95), (0.95, 0.3, 1.05), 0.04, 'steel')
    m.bm_((0.95, -0.345, 1.05), (0.95, 0.345, 1.05), 0.045, 'steel')
    m.cy((0, 0, 1.1), 0.03, 0.03, 1.4, 'steel', seg=6)
    m.fan((0, 0, 2.18), 2.62, 1.05, 8, ['paintY', 'awnT'])
    m.cy((0.3, 0.12, 1.1), 0.05, 0.05, 0.2, 'hydrant', seg=6)
    m.cy((0.42, 0.12, 1.1), 0.05, 0.05, 0.2, 'paintY', seg=6)
    obj = make('HotDog', m, bevel=0.015, ao=ao)
    col_box(obj, 0, -0.68, 0.98, -0.42, 0.42, 0, 1.1)


def build_billboard(pal, ao):
    """Billboard 6 x 2 on steel legs facing -Y: lattice legs, catwalk, lit panel with a cartoon soda ad (no words),
    gooseneck lamps."""
    m = PM(pal)
    for x in (-2.0, 2.0):
        m.bx(x - 0.15, x + 0.15, 0.3, 0.6, 0, 7.5, 'el')
        m.bx(x - 0.3, x + 0.3, 0.15, 0.75, 0, 0.3, 'elD')
        for k in range(3):
            z = 0.6 + k * 1.3
            m.bm_((x - 0.12, 0.45, z), (x + 0.12, 0.45, z + 1.2), 0.05, 'elD', hull='none')
    m.bx(-3.0, 3.0, 0.1, 0.4, 4.4, 7.6, 'trim')                                                     # panel back
    m.bx(-2.95, 2.95, 0.07, 0.1, 4.45, 7.55, 'neonY', hull='none', cull='k')                         # ad ground
    m.bx(-3.1, 3.1, -0.6, 0.45, 4.22, 4.3, 'elD')                                                    # catwalk
    m.bx(-3.1, 3.1, -0.62, -0.58, 4.3, 4.85, 'elD', hull='none')
    # the ad: a giant fizzing bottle and a sunburst
    m.cy((-1.2, 0.068, 6.0), 1.1, 1.1, 0.02, 'awnR', seg=14, rot=(90, 0, 0), hull='none')
    for k in range(8):
        a = k * math.pi / 4
        m.bx(-1.2 + math.cos(a) * 1.25 - 0.08, -1.2 + math.cos(a) * 1.25 + 0.08, 0.06, 0.07, 6.0 + math.sin(a) * 1.25 - 0.08, 6.0 + math.sin(a) * 1.25 + 0.08, 'awnR', hull='none', cull='k')
    poly_y(m, [(-1.55, 4.7), (-0.85, 4.7), (-0.85, 6.2), (-1.05, 6.6), (-1.05, 7.15), (-1.35, 7.15), (-1.35, 6.6), (-1.55, 6.2)], 0.035, 0.05, 'plum', hull='none')
    poly_y(m, [(-1.5, 5.3), (-0.9, 5.3), (-0.9, 5.8), (-1.5, 5.8)], 0.025, 0.036, 'paintW', hull='none')
    for (x, z, r) in ((0.5, 6.6, 0.35), (1.3, 5.6, 0.5), (2.2, 6.8, 0.3), (0.9, 5.0, 0.22), (2.1, 5.2, 0.28)):
        m.cy((x, 0.068, z), r, r, 0.02, 'neonC' if r > 0.3 else 'paintW', seg=10, rot=(90, 0, 0), hull='none')
    for x in (-2.0, 0.0, 2.0):                                                                       # lamps
        m.bm_((x, -0.55, 4.6), (x, -1.0, 4.9), 0.05, 'elD')
        m.bx(x - 0.2, x + 0.2, -1.15, -0.9, 4.85, 5.05, 'elD')
        m.bx(x - 0.15, x + 0.15, -1.1, -0.95, 5.05, 5.08, 'litW', hull='none')
    obj = make('Billboard', m, ao=ao)
    for i, x in enumerate((-2.0, 2.0)):
        col_box(obj, i, x - 0.3, x + 0.3, 0.15, 0.75, 0, 4.2)


# ================================================================ the El
EL_Z = 5.4       # underside of the girders


def el_deck(m, y0, y1, cols):
    """Elevated railway deck along Y from y0 to y1: two riveted plate girders, cross ties, rails, a lane line on
    the street below, columns with knee braces at the given y positions."""
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.35, sx * 1.6))
        m.bx(x0, x1, y0, y1, EL_Z, EL_Z + 1.1, 'el', hull='noend')
        x0, x1 = sorted((sx * 1.3, sx * 1.65))
        m.bx(x0, x1, y0, y1, EL_Z - 0.08, EL_Z, 'elD', hull='noend')
        m.bx(x0, x1, y0, y1, EL_Z + 1.1, EL_Z + 1.18, 'elD', hull='noend')
        xo = sx * 1.605
        x0, x1 = sorted((xo, xo + sx * 0.012))
        k = 0
        while y0 + 0.25 + k * 0.5 < y1:                                                          # stiffeners + rivets
            y = y0 + 0.25 + k * 0.5
            m.bx(x0, x1, y - 0.04, y + 0.04, EL_Z + 0.05, EL_Z + 1.05, 'elD', hull='none', cull='r' if sx < 0 else 'l')
            k += 1
    n = int(round((y1 - y0) / 0.6))
    for k in range(n):
        y = y0 + 0.3 + k * 0.6
        m.bx(-1.35, 1.35, y - 0.1, y + 0.1, EL_Z + 1.0, EL_Z + 1.12, 'wood', hull='none', cull='b')
    for x in (-0.72, 0.72):
        m.bx(x - 0.04, x + 0.04, y0, y1, EL_Z + 1.12, EL_Z + 1.24, 'steel', hull='noend')
    m.bx(-0.13, 0.13, y0, y1, 0.006, 0.013, 'paintY', hull='none')                                  # centre line below
    for y in cols:
        for sx in (-1, 1):
            x = sx * 1.47
            m.bx(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0, EL_Z - 0.08, 'el')
            m.bx(x - 0.26, x + 0.26, y - 0.26, y + 0.26, 0, 0.35, 'elD')
            m.bm_((x, y, EL_Z - 1.4), (x - sx * 0.95, y, EL_Z - 0.1), 0.1, 'el')
        m.bx(-1.3, 1.3, y - 0.12, y + 0.12, EL_Z - 0.6, EL_Z - 0.09, 'el')                         # cross girder


def build_el(pal, ao):
    m = PM(pal)
    el_deck(m, -3.0, 3.0, [-2.6])
    obj = make('El_A', m, ao=ao)
    for i, sx in enumerate((-1, 1)):
        col_box(obj, i, sx * 1.47 - 0.26, sx * 1.47 + 0.26, -2.86, -2.34, 0, EL_Z)
    # El_B: the same span with a signal mast and a cat-walk lamp
    m = PM(pal)
    el_deck(m, -3.0, 3.0, [-2.6])
    m.bx(1.62, 1.72, 0.9, 1.0, EL_Z + 1.18, EL_Z + 3.4, 'trim')
    m.bx(1.55, 1.85, 0.82, 0.98, EL_Z + 2.6, EL_Z + 3.35, 'trim')
    for z, c in ((EL_Z + 3.15, 'red'), (EL_Z + 2.85, 'neonG')):
        m.cy((1.7, 0.82, z), 0.08, 0.08, 0.03, c, seg=8, rot=(90, 0, 0), hull='none')
    obj = make('El_B', m, ao=ao)
    for i, sx in enumerate((-1, 1)):
        col_box(obj, i, sx * 1.47 - 0.26, sx * 1.47 + 0.26, -2.86, -2.34, 0, EL_Z)


def train_car(m, y0, y1):
    z0 = EL_Z + 1.3
    m.bx(-1.3, 1.3, y0, y1, z0 + 0.25, z0 + 3.0, 'silver', bevel=True)
    m.bx(-1.1, 1.1, y0 + 0.3, y1 - 0.3, z0, z0 + 0.25, 'trim')                                       # trucks / skirt
    m.bx(-1.15, 1.15, y0 + 0.1, y1 - 0.1, z0 + 3.0, z0 + 3.25, 'steel')                               # roof
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.3, sx * 1.315))
        cl = 'l' if sx > 0 else 'r'
        m.bx(x0, x1, y0 + 0.2, y1 - 0.2, z0 + 1.35, z0 + 2.25, 'lit', hull='none', cull=cl)          # window band
        x0, x1 = sorted((sx * 1.3, sx * 1.322))
        k = 0
        while y0 + 0.9 + k * 1.2 < y1 - 0.5:
            y = y0 + 0.9 + k * 1.2
            m.bx(x0, x1, y - 0.05, y + 0.05, z0 + 1.32, z0 + 2.28, 'trim', hull='none', cull=cl)     # pillars
            k += 1
        x0, x1 = sorted((sx * 1.3, sx * 1.318))
        m.bx(x0, x1, y0 + 0.1, y1 - 0.1, z0 + 0.95, z0 + 1.15, 'neonP', hull='none', cull=cl)        # stripe
        for yc in ((y0 * 2 + y1) / 3, (y0 + y1 * 2) / 3):
            x0, x1 = sorted((sx * 1.3, sx * 1.33))
            m.bx(x0, x1, yc - 0.45, yc + 0.45, z0 + 0.3, z0 + 2.45, 'steel', hull='none', cull=cl)  # doors
    for y, cl in ((y0, 'k'), (y1, 'f')):
        yy0, yy1 = sorted((y, y - 0.015 if y == y0 else y + 0.015))
        m.bx(-0.5, 0.5, yy0, yy1, z0 + 1.3, z0 + 2.4, 'litW', hull='none', cull=cl)


def build_eltrain(pal, ao):
    """A 12 m span (4 x 12) carrying a stopped two-car train: silver cars, lit window bands, pink stripe."""
    m = PM(pal)
    el_deck(m, -6.0, 6.0, [-5.6, 0.4])
    train_car(m, -5.85, -0.15)
    train_car(m, 0.15, 5.85)
    m.bx(-0.6, 0.6, -0.16, 0.16, EL_Z + 1.9, EL_Z + 4.0, 'trim')                                    # gangway
    obj = make('Landmark_ElTrain', m, ao=ao)
    i = 0
    for y in (-5.6, 0.4):
        for sx in (-1, 1):
            col_box(obj, i, sx * 1.47 - 0.26, sx * 1.47 + 0.26, y - 0.26, y + 0.26, 0, EL_Z)
            i += 1


# ================================================================ landmarks
def build_subway(pal, ao):
    """Subway entrance 3 x 5: a stair well (dark, steps fading down) inside green iron railings, open at the south
    (-Y) end, two green globe lamps on posts, an enamel sign panel (stripes and a roundel, no lettering)."""
    m = PM(pal)
    slab(m, grid_cells(3, 5))
    m.bx(-1.2, 1.2, -2.3, 2.3, 0.05, 0.062, 'ink', hull='none', cull='b')                            # the well
    for k in range(9):
        y = -2.1 + k * 0.48
        c = ('granite', 'graniteD', 'walkB', 'curb', 'trim', 'trim', 'shopG', 'shopG', 'ink')[k]
        m.bx(-1.15, 1.15, y, y + 0.05, 0.062, 0.07, c, hull='none', cull='b')                        # nosings
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.25, sx * 1.35))
        m.bx(x0, x1, -2.45, 2.45, 0.05, 0.35, 'el', cull='b')                                        # curb wall
        m.bx(x0, x1, -2.45, 2.45, 1.0, 1.08, 'el')                                                   # rail
        for k in range(9):
            y = -2.3 + k * 0.575
            m.bx(x0 + 0.03, x1 - 0.03, y - 0.02, y + 0.02, 0.35, 1.0, 'el', hull='none')
    m.bx(-1.25, 1.25, 2.35, 2.45, 0.05, 0.35, 'el')
    m.bx(-1.25, 1.25, 2.35, 2.45, 1.0, 1.08, 'el')
    for k in range(5):
        x = -1.0 + k * 0.5
        m.bx(x - 0.02, x + 0.02, 2.37, 2.43, 0.35, 1.0, 'el', hull='none')
    for sx in (-1, 1):                                                                                # globe lamps
        x = sx * 1.3
        m.cy((x, -2.4, 0.05), 0.09, 0.07, 2.6, 'el', seg=8)
        m.sp((x, -2.4, 2.85), 0.22, 'neonG', seg=(8, 5))
        m.cy((x, -2.4, 3.05), 0.05, 0.0, 0.15, 'el', seg=5, hull='none')
    m.bx(-1.2, 1.2, -2.42, -2.38, 1.9, 2.5, 'el')                                                     # sign panel
    m.bx(-1.15, 1.15, -2.44, -2.42, 1.95, 2.45, 'newsG', hull='none')
    m.bx(-1.15, 1.15, -2.45, -2.44, 2.12, 2.28, 'paper', hull='none')
    m.cy((-0.8, -2.452, 2.2), 0.17, 0.17, 0.01, 'awnR', seg=10, rot=(90, 0, 0), hull='none')
    obj = make('Landmark_Subway', m, ao=ao)
    col_box(obj, 0, -1.35, 1.35, -2.45, 2.45, 0, 1.1)


def build_statue(pal, ao):
    """Statue 4 x 4: stepped granite plinth with a bronze plaque, a bronze figure in a long coat raising a lantern
    (lit), four lamps on the plinth corners."""
    m = PM(pal)
    m.bx(-2.0, 2.0, -2.0, 2.0, 0, 0.3, 'graniteD', bevel=True)
    m.bx(-1.6, 1.6, -1.6, 1.6, 0.3, 0.65, 'granite', bevel=True, cull='b')
    m.bx(-1.0, 1.0, -1.0, 1.0, 0.65, 2.6, 'granite', cull='b')
    m.bx(-1.12, 1.12, -1.12, 1.12, 2.6, 2.85, 'graniteD')
    m.bx(-1.08, 1.08, -1.08, 1.08, 0.65, 0.85, 'graniteD', cull='b')
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        m.bx(-0.55, 0.55, -1.03, -0.99, 1.3, 2.1, 'bronzeD', hull='none', cull='k')
        m.bx(-0.45, 0.45, -1.04, -1.02, 1.5, 1.9, 'bronze', hull='none', cull='k')
        m.cy((1.6, -1.6, 0.3), 0.08, 0.06, 1.9, 'elD', seg=6)
        m.sp((1.6, -1.6, 2.35), 0.2, 'litW', seg=(8, 5))
    m.parent = Matrix.Identity(4)
    z = 2.85
    m.bx(-0.45, 0.45, -0.45, 0.45, z, z + 0.12, 'bronzeD')
    m.cy((0, 0, z + 0.12), 0.48, 0.3, 1.5, 'bronze', seg=10)                                           # coat
    m.cy((0, 0, z + 1.62), 0.32, 0.26, 0.55, 'bronze', seg=10)                                         # chest
    m.sp((0, 0, z + 2.4), 0.24, 'bronze', seg=(8, 6))                                                  # head
    m.cy((0, 0, z + 2.55), 0.3, 0.3, 0.04, 'bronzeD', seg=10)                                          # hat brim
    m.cy((0, 0, z + 2.59), 0.2, 0.18, 0.22, 'bronzeD', seg=10)
    m.bm_((0.22, 0, z + 2.05), (0.5, -0.1, z + 2.7), 0.13, 'bronze')                                  # raised arm
    m.bm_((0.5, -0.1, z + 2.7), (0.55, -0.15, z + 3.2), 0.11, 'bronze')
    m.bx(0.45, 0.65, -0.25, -0.05, z + 3.2, z + 3.25, 'bronzeD')
    m.bx(0.47, 0.63, -0.23, -0.07, z + 3.25, z + 3.55, 'lit')
    m.cy((0.55, -0.15, z + 3.55), 0.11, 0.0, 0.14, 'bronzeD', seg=4)
    m.bm_((-0.22, 0, z + 2.05), (-0.36, -0.15, z + 1.35), 0.12, 'bronze')                             # other arm + book
    m.bx(-0.5, -0.24, -0.3, -0.14, z + 1.2, z + 1.5, 'bronzeD')
    obj = make('Landmark_Statue', m, ao=ao)
    col_box(obj, 0, -2.0, 2.0, -2.0, 2.0, 0, 0.65)
    col_box(obj, 1, -1.12, 1.12, -1.12, 1.12, 0.65, 6.0)


# ================================================================ backdrop (beyond the walls, fogged, dusk)
def build_backdrop(pal):
    m = PM(pal)                                     # tenement row with water tanks and lit windows
    rnd = random.Random(3)
    for i, (c, h, w) in enumerate((('bdB', 22, 9), ('bdA', 26, 8), ('bdC', 20, 10), ('bdB', 28, 8))):
        x0 = -17.5 + sum(v[2] for v in (('bdB', 22, 9), ('bdA', 26, 8), ('bdC', 20, 10), ('bdB', 28, 8))[:i])
        m.bx(x0 + 0.02, x0 + w - 0.02, -5, 5, 0, h, c)
        m.bx(x0 - 0.08, x0 + w + 0.08, -5.25, 4.9, h, h + 0.6, 'cornice')
        for f in range(int((h - 3) / 3.2)):
            z = 3 + f * 3.2
            for k in range(int(w / 1.6)):
                x = x0 + 0.9 + k * 1.6
                if x + 0.4 > x0 + w:
                    break
                m.bx(x - 0.35, x + 0.35, -5.08, -4.95, z, z + 1.6, 'lit' if rnd.random() < 0.3 else 'winD', hull='none')
        if i % 2 == 0:
            tx = x0 + w / 2
            for (dx, dy) in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
                m.bx(tx + dx - 0.1, tx + dx + 0.1, dy - 0.1, dy + 0.1, h + 0.6, h + 2.2, 'trim', hull='none')
            m.cy((tx, 0, h + 2.2), 1.3, 1.3, 2.4, 'wood', seg=8)
            m.cy((tx, 0, h + 4.6), 1.4, 0.1, 1.2, 'cornice', seg=8)
    m.bx(-4, 2, -5.3, -5.05, 26.6, 30.6, 'trim')                                                     # roof billboard
    m.bx(-3.8, 1.8, -5.32, -5.3, 26.8, 30.4, 'neonP', hull='none')
    make('Backdrop_Block', m)
    m = PM(pal)                                     # dusk tower: setbacks, lit window grid, red beacon
    for (h, z0, z1, c) in ((8, 0, 34, 'bdA'), (6, 34.4, 48, 'bdC'), (4, 48.4, 56, 'bdA')):
        m.bx(-h, h, -h, h, z0, z1, c)
        m.bx(-h - 0.3, h + 0.3, -h - 0.3, h + 0.3, z1, z1 + 0.4, 'cornice')
        for k in range(h):
            x = -h + 1 + k * 2
            for fz in range(int((z1 - z0 - 2) / 3.4)):
                z = z0 + 1.5 + fz * 3.4
                lit = (k * 7 + fz * 3) % 5 == 0
                m.bx(x - 0.4, x + 0.4, -h - 0.06, -h + 0.06, z, z + 1.8, 'lit' if lit else 'winD', hull='none')
    m.cy((0, 0, 56.4), 0.15, 0.08, 6.0, 'trim', seg=5, hull='none')
    m.sp((0, 0, 62.5), 0.4, 'red', seg=(6, 4), hull='none')
    make('Backdrop_Tower', m)
    m = PM(pal)                                     # deco spire
    m.bx(-7, 7, -7, 7, 0, 40, 'bdB')
    for (h, z0, z1) in ((5.5, 40, 50), (4, 50, 58), (2.6, 58, 64)):
        m.bx(-h, h, -h, h, z0, z1, 'deco' if h != 4 else 'bdA')
    m.cy((0, 0, 64), 2.6 * math.sqrt(2), 0.0, 14, 'silver', seg=4, rot=(0, 0, 45))
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        for x in (-4.5, -1.5, 1.5, 4.5):
            m.bx(x - 0.4, x + 0.4, -7.06, -6.94, 2, 38, 'decoD', hull='none')
        for x in (-3.0, 0.0, 3.0):
            m.bx(x - 0.2, x + 0.2, -7.08, -6.96, 6, 36, 'lit' if x == 0 else 'winD', hull='none')
    m.parent = Matrix.Identity(4)
    make('Backdrop_Spire', m)


# ================================================================ build
def build_kit_city2(ao):
    pal = Palette(FAM)
    build_facades(pal)
    build_floor(pal)
    build_gate(pal, ao)
    build_trail(pal, ao)
    build_hatch(pal, ao)
    for name, c, cab, ad in (('Cab', 'cab', True, False), ('CabAd', 'cab', True, True), ('Sedan_Plum', 'plum', False, False), ('Sedan_Teal', 'tealC', False, False)):
        build_car(pal, name, c, cab, ad, ao)
    build_truck(pal, ao)
    build_lamps(pal, ao)
    build_tree(pal, ao)
    build_furniture(pal, ao)
    build_junk(pal, ao)
    build_barriers(pal, ao)
    build_steam(pal, ao)
    build_bench(pal, ao)
    build_newsstand(pal, ao)
    build_hotdog(pal, ao)
    build_billboard(pal, ao)
    build_el(pal, ao)
    build_eltrain(pal, ao)
    build_subway(pal, ao)
    build_statue(pal, ao)
    build_backdrop(pal)
    export(FAM)


FAMILY = FAM
BUILD = build_kit_city2
