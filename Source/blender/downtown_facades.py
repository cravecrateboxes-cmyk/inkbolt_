"""kit-downtown facades, street surface, gate, trail, hatch and backdrop.

Facade modules are 1 m wide, front = Blender -Y. Five building styles (mirrored by STY in src/data/themes/downtown.js):
  L  limestone bank / office: rusticated ground floor, tall windows with keystones, heavy dentil cornice (5 storeys)
  T  tan brick commercial: punched windows with stone sills and soldier courses, brick cornice (6 storeys)
  G  glass curtain wall: storey-high glazing between dark mullions, grey spandrels, metal coping (8 storeys)
  D  teal terracotta deco: continuous piers, dark spandrels, a stepped crown (7 storeys)
  C  60s concrete: ribbon windows between deep concrete bands, sun fins (5 storeys)
Kinds per style (<Kind>_<style index>): Win (a closed shop: shutter half down, sign band), Lobby (office entrance with
a canopy), Pier (solid ground floor with a plaque), Board (plywood over the shop window, upper windows taped), Nest (a
sniper nest on a low balcony: sandbags, a rifle, camo netting), ShopWin / ShopOpen (a walk-in shop's display window /
open front: the shop room piece adds its own sign, awning and window lettering), plus Pilaster_<s>, Corner_<s> and
Blank_<s> (inner corners, beside gates).
"""
import math
import random

from mathutils import Matrix

from downtown_base import *  # noqa: F401,F403
import downtown_detail as DD
from fam_kit_city2 import GW  # noqa: F401  (gate opening half width, shared with the other street kits)

PAR = 0.9
MATS = {   # body, trim, cornice, pier, sign band
    'L': ('lime', 'limeD', 'limeD', 'limeD', 'navy'),
    'T': ('brickT', 'lime', 'brickTD', 'brickTD', 'woodD'),
    'G': ('concF', 'mull', 'mull', 'concF', 'mull'),
    'D': ('terra', 'lime', 'terraD', 'terraD', 'terraD'),
    'C': ('conc', 'concF', 'concF', 'concF', 'pipeR'),
}
STYLES = [('L', 5), ('T', 6), ('G', 8), ('D', 7), ('C', 5)]
KINDS = ['Win', 'Lobby', 'Pier', 'Board', 'Nest', 'ShopWin', 'ShopOpen']
NEST = 'LTC'      # styles with sniper-nest balconies (not the glass and deco towers)
BOARD = 'LTC'     # styles with boarded-up shops (the towers' ground floors are lobbies and closed shops)


def flat(m, x0, x1, d, z0, z1, c):
    """hairline facade layer d proud of the front plane: only its front face"""
    m.bx(x0, x1, F(d), F(d) + 0.002, z0, z1, c, hull='none', cull='ktblr')


def ledge(m, x0, x1, d, z0, z1, c, top=False):
    m.bx(x0, x1, F(d), -0.5 + 0.01, z0, z1, c, hull='none', cull='klr' + ('' if top else ('t' if z1 > 5.0 else '')))


# ---------------------------------------------------------------- upper floors
def gcol(glass):
    return {'broken': 'ink', 'tape': 'glass'}.get(glass, glass)


def window(m, mat, x0, x1, z0, z1, glass, rnd):
    body, trim, cor, pier, band = MATS[mat]
    flat(m, x0 - 0.04, x1 + 0.04, 0.012, z0, z1, 'mull')
    flat(m, x0, x1, 0.02, z0 + 0.04, z1 - 0.04, gcol(glass))
    if glass == 'glass':
        if rnd.random() < 0.45:   # blind half down
            flat(m, x0, x1, 0.026, z1 - 0.04 - (z1 - z0) * rnd.choice((0.25, 0.4)), z1 - 0.04, 'cream')
        else:                     # a glint
            poly(m, [(x0 + 0.05, F(0.026), z0 + 0.3), (x0 + 0.13, F(0.026), z0 + 0.3), (x0 + 0.3, F(0.026), z0 + 0.8), (x0 + 0.22, F(0.026), z0 + 0.8)], 'glassL', (0, -1, 0))
    elif glass == 'broken':       # shot out: dark hole with jagged glass round it
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        for (a, b, c) in (((x0, z1 - 0.05), (cx, z1 - 0.05), (x0 + 0.06, cz)), ((x1, z0 + 0.05), (x1, cz + 0.2), (cx + 0.05, z0 + 0.05))):
            poly(m, [(a[0], F(0.026), a[1]), (b[0], F(0.026), b[1]), (c[0], F(0.026), c[1])], 'glass', (0, -1, 0))
    elif glass == 'tape':         # taped X against blast
        for sgn in (-1, 1):
            xa, xb = (x0 + 0.03, x1 - 0.03) if sgn > 0 else (x1 - 0.03, x0 + 0.03)
            d = 0.026 if sgn > 0 else 0.03
            poly(m, [(xa - 0.025, F(d), z0 + 0.08), (xa + 0.025, F(d), z0 + 0.08), (xb + 0.025, F(d), z1 - 0.08), (xb - 0.025, F(d), z1 - 0.08)], 'cream', (0, -1, 0))
    if mat in ('L', 'T'):
        ledge(m, x0 - 0.08, x1 + 0.08, 0.06, z0 - 0.1, z0, trim)                       # sill
    if mat == 'L':
        ledge(m, x0 - 0.06, x1 + 0.06, 0.05, z1, z1 + 0.18, trim)                       # lintel
        if z1 < 12:
            ledge(m, -0.06, 0.06, 0.07, z1 - 0.02, z1 + 0.22, 'lime')                   # keystone
    elif mat == 'T':
        ledge(m, x0 - 0.05, x1 + 0.05, 0.03, z1, z1 + 0.14, 'brickTD')                  # soldier course


def floors(m, mat, n, seed, kind):
    rnd = random.Random(seed)
    body, trim, cor, pier, band = MATS[mat]
    for k in range(1, n):
        z0 = G_H + (k - 1) * U_H
        r = rnd.random()
        glass = 'mull' if r < 0.22 else 'broken' if r < 0.3 else 'glass'
        if kind == 'Board' and k <= 2:
            glass = 'tape'
        if kind == 'Nest' and k == 1:
            nest_floor(m, mat, z0)
            continue
        if mat == 'G':        # curtain wall: glass between mullions, spandrel band
            flat(m, -0.5, 0.5, 0.004, z0, z0 + 0.75, 'concF' if k % 2 else 'steel')
            flat(m, -0.5, 0.5, 0.008, z0 + 0.75, z0 + U_H, 'signB' if glass == 'mull' else gcol(glass))
            if glass == 'glass':
                poly(m, [(-0.4, F(0.012), z0 + 1.0), (-0.3, F(0.012), z0 + 1.0), (-0.05, F(0.012), z0 + 2.4), (-0.15, F(0.012), z0 + 2.4)], 'glassL', (0, -1, 0))
            m.bx(-0.5, -0.46, F(0.08), -0.5, z0, z0 + U_H, 'mull', hull='none', cull='k')
            m.bx(-0.5, 0.5, F(0.05), -0.5, z0 + 0.72, z0 + 0.78, 'mull', hull='none', cull='klr')
        elif mat == 'D':      # deco: piers at the module edges, dark spandrels
            for sx in (-1, 1):
                a, b = sorted((sx * 0.5, sx * 0.34))
                m.bx(a, b, F(0.1), -0.5, z0, z0 + U_H, 'terra' if k % 2 else 'lime', hull='none', cull='k')
            flat(m, -0.34, 0.34, 0.004, z0 + 2.6, z0 + U_H, 'terraD')
            window(m, mat, -0.26, 0.26, z0 + 0.35, z0 + 2.5, glass, rnd)
        elif mat == 'C':      # ribbon windows between concrete bands, a sun fin
            flat(m, -0.5, 0.5, 0.01, z0 + 0.9, z0 + 2.5, 'mull')
            flat(m, -0.5, 0.5, 0.016, z0 + 0.94, z0 + 2.46, glass if glass in ('glass', 'mull') else 'glass')
            if glass == 'broken':
                flat(m, -0.2, 0.3, 0.02, z0 + 1.1, z0 + 2.2, 'ink')
            m.bx(-0.5, 0.5, F(0.16), -0.5, z0 + 2.5, z0 + 2.75, 'concF', hull='none', cull='klr')
            m.bx(0.42, 0.5, F(0.32), -0.5, z0 + 0.9, z0 + 2.5, 'concF', hull='none', cull='k')
        else:
            window(m, mat, -0.27, 0.27, z0 + 0.65, z0 + 2.65, glass, rnd)
        if mat == 'L' and k == 1:
            ledge(m, -0.5, 0.5, 0.06, z0 - 0.02, z0 + 0.14, 'limeD')                       # first-floor band
        if mat == 'T' and k == n - 1:
            ledge(m, -0.5, 0.5, 0.04, z0 - 0.15, z0 - 0.05, 'lime')


def nest_floor(m, mat, z0):
    """sniper nest: a 1.1 m balcony at the first floor, sandbagged round, a rifle across the bags, camo net over it,
    the door behind it dark"""
    body, trim, cor, pier, band = MATS[mat]
    flat(m, -0.32, 0.32, 0.01, z0, z0 + 2.4, 'mull')
    flat(m, -0.28, 0.28, 0.016, z0 + 0.04, z0 + 2.36, 'ink')
    m.bx(-0.5, 0.5, -1.62, -0.5, z0 - 0.16, z0, trim, cull='k')                              # slab
    for x in (-0.38, 0.38):                                                                   # brackets
        m.prism([(-0.5, z0 - 0.16), (-1.3, z0 - 0.16), (-0.5, z0 - 0.75)], x - 0.05, x + 0.05, [trim], hull='none')
    P0 = m.parent
    m.parent = P0 @ Matrix.Translation((0, 0, z0))
    sandbag_row(m, -0.48, 0.48, -1.42, 0.0, 0.3, 0.26, k0=0, top=False)
    sandbag_row(m, -0.42, 0.42, -1.42, 0.26, 0.28, 0.24, k0=1)
    for x in (-0.38, 0.38):                                                                   # side bags
        m.bx(x - 0.1, x + 0.1, -1.25, -0.7, 0.0, 0.36, 'sandD' if x < 0 else 'sand')
    m.bm_((0.1, -0.85, 0.56), (-0.05, -1.9, 0.52), 0.04, 'ink')                              # rifle barrel over the bags
    m.bx(0.06, 0.2, -1.0, -0.72, 0.47, 0.6, 'woodD')                                         # stock
    m.bx(0.02, 0.24, -1.05, -0.7, 0.0, 0.47, 'olive')                                        # on an ammo box
    m.cy((0.02, -1.15, 0.6), 0.035, 0.035, 0.22, 'ink', seg=6, rot=(90, 0, 0), hull='none')  # scope
    # camo net draped from the wall over the balcony
    m.prism([(-0.5, 2.3), (-1.65, 1.5), (-1.7, 1.38), (-0.5, 2.12)], -0.5, 0.5, ['olive'], hull='full')
    for x in (-0.3, 0.05, 0.36):
        m.bx(x - 0.07, x + 0.07, -1.69, -1.6, 1.0 + (x * 3 % 0.4), 1.42, 'olive', hull='none')
    m.parent = P0


def cornice(m, mat, n):
    T = top_of(n)
    body, trim, cor, pier, band = MATS[mat]
    if mat == 'L':        # dentils under a heavy cornice
        m.bx(-0.5, 0.5, F(0.34), -0.5, T + 0.12, T + 0.55, cor, hull='noside', cull='k')
        for x in (-0.375, -0.125, 0.125, 0.375):
            m.bx(x - 0.05, x + 0.05, F(0.22), -0.5, T - 0.04, T + 0.12, 'lime', hull='none', cull='k')
        m.bx(-0.5, 0.5, F(0.12), -0.5, T - 0.35, T - 0.22, cor, hull='none', cull='klrt')
    elif mat == 'T':
        m.bx(-0.5, 0.5, F(0.14), -0.5, T, T + 0.32, 'brickTD', hull='noside', cull='k')
        m.bx(-0.5, 0.5, F(0.08), -0.5, T - 0.42, T - 0.3, 'lime', hull='none', cull='klrt')
    elif mat == 'G':
        m.bx(-0.5, 0.5, F(0.1), -0.5, T, T + 0.3, 'steel', hull='noside', cull='k')
    elif mat == 'D':      # stepped crown
        m.bx(-0.5, 0.5, F(0.14), -0.5, T, T + 0.22, 'terraD', hull='noside', cull='k')
        m.bx(-0.5, 0.5, F(0.07), -0.5, T + 0.22, T + 0.62, 'lime', hull='noside', cull='k')
        m.bx(-0.12, 0.12, F(0.1), -0.5, T + 0.62, T + 1.1, 'terra', hull='none', cull='k')
    else:
        m.bx(-0.5, 0.5, F(0.22), -0.5, T, T + 0.4, 'concF', hull='noside', cull='k')


def body(m, mat, n, z0=0.0, hull='noside', lip=0.04, bottom=False):
    b = MATS[mat][0]
    T = top_of(n)
    m.bx(-0.5, 0.5, -0.5, 0.5, z0, T + PAR, b, hull=hull, cull='t' if bottom else 'bt')
    m.bx(-0.5, 0.5, F(lip), 0.5, T + PAR, T + PAR + 0.12, 'conc' if mat != 'L' else 'limeD', hull=hull, cull='b')   # coping


# ---------------------------------------------------------------- ground floors
def plinth(m, mat):
    m.bx(-0.5, 0.5, F(0.04), -0.49, 0.0, 0.32, 'limeD' if mat in ('L', 'D') else 'mull', hull='noside', cull='kblr')


def sign_band(m, mat, z0=3.3, z1=4.15):
    body, trim, cor, pier, band = MATS[mat]
    m.bx(-0.5, 0.5, F(0.1), -0.5, z0, z1, band, hull='noside', cull='klr')
    m.bx(-0.5, 0.5, F(0.13), -0.5, z1, z1 + 0.1, cor, hull='noside', cull='klr')


def rustic(m, mat, z0, z1):
    """rusticated stone: dark joint lines every 0.45 m"""
    z = z0 + 0.45
    while z < z1 - 0.1:
        flat(m, -0.5, 0.5, 0.004, z, z + 0.03, 'limeD')
        z += 0.45


def ground(m, mat, kind, si):
    body, trim, cor, pier, band = MATS[mat]
    if kind in ('Win', 'Nest', 'Board'):
        plinth(m, mat)
        flat(m, -0.46, 0.46, 0.012, 0.32, 3.2, 'mull')
        if kind == 'Board':   # plywood boards screwed over the window, a sprayed X
            m.bx(-0.47, 0.45, F(0.06), F(0.016), 0.36, 1.75, 'wood', hull='none', cull='k')
            m.bx(-0.44, 0.47, F(0.06), F(0.016), 1.8, 3.15, 'wood', hull='none', cull='k')
            flat(m, -0.47, 0.45, 0.064, 1.2, 1.24, 'woodD')
            for sgn in (-1, 1):
                d = 0.068 if sgn > 0 else 0.072
                poly(m, [(-0.36 * sgn - 0.04, F(d), 0.6), (-0.36 * sgn + 0.04, F(d), 0.6), (0.36 * sgn + 0.04, F(d), 2.9), (0.36 * sgn - 0.04, F(d), 2.9)], 'pipeR', (0, -1, 0))
        else:                 # shutter half down over dark glass
            flat(m, -0.44, 0.44, 0.018, 0.36, 3.16, 'interior')
            poly(m, [(-0.36, F(0.022), 0.5), (-0.28, F(0.022), 0.5), (-0.12, F(0.022), 1.4), (-0.2, F(0.022), 1.4)], 'glassL', (0, -1, 0))
            zt = 1.55 + (si % 3) * 0.3
            flat(m, -0.46, 0.46, 0.024, zt, 3.18, 'galv')
            z = zt + 0.12
            while z < 3.1:
                flat(m, -0.46, 0.46, 0.028, z, z + 0.02, 'steel')
                z += 0.16
            m.bx(-0.46, 0.46, F(0.06), F(0.012), 3.12, 3.28, 'steelD', hull='none', cull='klr')   # shutter box
        sign_band(m, mat)
        if mat in ('T', 'C') and kind == 'Win':   # striped fabric awning
            c1, c2 = ('pipeR', 'cream') if mat == 'T' else ('pTeal', 'cream')
            m.prism([(F(0.12), 3.28), (F(0.12) - 0.8, 3.04), (F(0.12) - 0.8, 2.9), (F(0.12), 3.18)], -0.5, 0.5, [c1, c2, c1, c2], hull='none', skip=(3,))
            m.bx(-0.5, 0.5, F(0.12) - 0.812, F(0.12) - 0.8, 2.74, 2.91, c1, hull='none', cull='k')
    elif kind == 'Lobby':
        for sx in (-1, 1):
            a, b = sorted((sx * 0.5, sx * 0.43))
            m.bx(a, b, F(0.04), -0.49, 0.0, 0.32, 'limeD' if mat in ('L', 'D') else 'mull', hull='none', cull='kb' + ('r' if sx > 0 else 'l'))
        flat(m, -0.5, 0.5, 0.01, 0.32, 3.1, trim)
        flat(m, -0.42, 0.42, 0.016, 0.02, 2.5, 'mull')
        flat(m, -0.38, -0.02, 0.022, 0.06, 2.42, 'glass')
        flat(m, 0.02, 0.38, 0.022, 0.06, 2.42, 'glass')
        flat(m, -0.08, -0.04, 0.026, 0.9, 1.4, 'chrome')
        flat(m, 0.04, 0.08, 0.026, 0.9, 1.4, 'chrome')
        flat(m, -0.42, 0.42, 0.016, 2.56, 3.0, 'glassL')
        m.bx(-0.5, 0.5, -1.55, -0.5, 3.18, 3.34, 'mull', hull='full', cull='k')                # canopy
        flat(m, -0.4, 0.4, 1.055, 3.2, 3.32, 'chrome')
        m.bx(-0.16, 0.16, F(0.03), -0.5, 3.45, 3.75, 'bronze', hull='none', cull='k')           # street number
        txt(m, str(100 + si * 14), 0.0, F(0.034), 3.6, 0.2, 'cream', font='display', maxw=0.28)
        if mat == 'L':
            rustic(m, mat, 3.34, G_H - 0.2)
    elif kind == 'Pier':
        plinth(m, mat)
        if mat == 'L':
            rustic(m, mat, 0.32, G_H - 0.2)
        flat(m, -0.18, 0.18, 0.01, 1.3, 1.75, 'bronze')
        flat(m, -0.14, 0.14, 0.014, 1.36, 1.69, 'limeD')
        flat(m, -0.3, 0.3, 0.008, 2.2, 2.9, 'paper')                                            # notice
        for k in range(4):
            flat(m, -0.24, 0.24 - 0.08 * (k % 2), 0.012, 2.72 - k * 0.12, 2.76 - k * 0.12, 'ink' if k else 'pipeR')
    elif kind == 'ShopWin':   # walk-in shop display window (the room behind draws the inside)
        m.bx(-0.5, 0.5, F(0.04), -0.49, 0.0, 0.45, 'mull', hull='noside', cull='kblr')
        flat(m, -0.5, 0.5, 0.006, 0.45, 3.3, 'mull')
        flat(m, -0.46, 0.46, 0.012, 0.5, 2.6, 'glass')
        flat(m, -0.46, 0.46, 0.012, 2.66, 3.24, 'glassL')
        poly(m, [(-0.3, F(0.016), 0.7), (-0.2, F(0.016), 0.7), (0.05, F(0.016), 2.2), (-0.05, F(0.016), 2.2)], 'glassL', (0, -1, 0))
    if kind == 'ShopOpen':
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, 0.012, 'mull', hull='none', cull='b')                  # threshold
        m.bx(-0.5, 0.5, -0.5, -0.38, DOOR_H - 0.12, DOOR_H, 'mull', hull='none', cull='tklr')


def build_facades(pal, ao):
    for si, (mat, n) in enumerate(STYLES):
        for ki, kind in enumerate(KINDS):
            if (kind == 'Nest' and mat not in NEST) or (kind == 'Board' and mat not in BOARD):
                continue
            m = new(pal)
            body(m, mat, n, z0=DOOR_H if kind == 'ShopOpen' else 0.0, bottom=kind == 'ShopOpen')
            ground(m, mat, kind, si * 7 + ki)
            if kind in DD.FACADE_DETAIL:
                DD.FACADE_DETAIL[kind](m, mat, si * 7 + ki)
            if mat == 'L' and kind in ('Win', 'Board', 'Nest'):
                rustic(m, mat, 4.25, G_H - 0.05)
            floors(m, mat, n, si * 31 + ki * 7, kind)
            cornice(m, mat, n)
            make('%s_%d' % (kind, si), m, ao)
        pilaster(pal, mat, n, si, ao)
        corner(pal, mat, n, si, ao)
        m = new(pal)
        body(m, mat, n, lip=0.0)          # inner corners and gate sides: nothing proud, the neighbours own the corner
        make('Blank_%d' % si, m, ao)


def pilaster(pal, mat, n, si, ao):
    body_c, trim, cor, pier, band = MATS[mat]
    T = top_of(n)
    m = new(pal)
    body(m, mat, n, hull='full')
    m.bx(-0.44, 0.44, F(0.14), -0.49, 0.35, T + PAR + 0.25, pier, cull='kbt')
    m.bx(-0.47, 0.47, F(0.17), -0.49, 0.0, 0.35, 'mull' if mat in ('G', 'C', 'T') else 'limeD', cull='kb')
    m.bx(-0.5, 0.5, F(0.22), -0.5, T - 0.1, T + 0.4, cor, cull='k')
    m.bx(-0.48, 0.48, F(0.17), 0.5, T + PAR + 0.25, T + PAR + 0.37, 'conc', cull='b')
    if mat == 'L':
        rustic_p = 0.32 + 0.45
        while rustic_p < G_H:
            m.bx(-0.445, 0.445, F(0.144), F(0.14) + 0.01, rustic_p, rustic_p + 0.03, 'lime', hull='none', cull='ktblr')
            rustic_p += 0.45
    make('Pilaster_%d' % si, m, ao)


def corner(pal, mat, n, si, ao):
    body_c, trim, cor, pier, band = MATS[mat]
    T = top_of(n)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0, T + PAR, body_c, cull='bt')
    q = 0.575        # proud of the modules either side by amounts none of their details use (no coplanar faces)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(min(sx * 0.36, sx * q), max(sx * 0.36, sx * q), min(sy * 0.36, sy * q), max(sy * 0.36, sy * q), 0.37, T, pier, cull='bt')
    m.bx(-0.595, 0.595, -0.595, 0.595, 0, 0.37, 'mull' if mat in ('G', 'C', 'T') else 'limeD', cull='b')
    m.bx(-0.725, 0.725, -0.725, 0.725, T - 0.07, T + 0.43, cor, cull='')
    m.bx(-0.585, 0.585, -0.585, 0.585, T + PAR + 0.03, T + PAR + 0.17, 'conc')
    make('Corner_%d' % si, m, ao)


# ================================================================ street surface
def build_floor(pal, ao):
    for name, c, j in (('Walk', 'walk', 'curb'), ('WalkB', 'walkB', 'curb'), ('Plaza', 'cream', 'limeD'), ('PlazaB', 'lime', 'limeD')):
        m = new(pal)
        tile(m, 0, 0, c, j)
        make(name, m, ao, hull=0)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.22, 0.22, 0.006, 0.014, 'pWhite', hull='none', cull='b')
    make('Zebra', m, ao, hull=0)
    m = new(pal)
    m.bx(-0.3, 0.3, -0.06, 0.06, 0.006, 0.013, 'pWhite', hull='none', cull='b')
    make('LaneW', m, ao, hull=0)
    m = new(pal)
    for sy in (-1, 1):
        m.bx(-0.5, 0.5, sy * 0.13 - 0.05, sy * 0.13 + 0.05, 0.006, 0.013, 'lineY', hull='none', cull='b')
    make('LaneY', m, ao, hull=0)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.06, 0.06, 0.006, 0.013, 'pWhite', hull='none', cull='b')
    make('StopLine', m, ao, hull=0)
    m = new(pal)
    m.cy((0, 0, 0.006), 0.36, 0.36, 0.012, 'steel', seg=12, hull='none')
    for k in range(4):
        m.bx(-0.26 + k * 0.15, -0.22 + k * 0.15, -0.24, 0.24, 0.018, 0.0215, 'steelD', hull='none', cull='b')
    make('Manhole', m, ao, hull=0)
    # scorch mark (a burst of soot) and scattered rubble / brass
    m = new(pal)
    disc(m, 0, 0, 0.007, 0.48, 'burnt', seg=10, jag=[1.0, 0.7, 1.15, 0.8, 1.05, 0.62, 1.1, 0.85, 0.95, 0.7])
    disc(m, 0.05, -0.04, 0.011, 0.22, 'ink', seg=7, jag=[1.0, 0.6, 1.2, 0.8, 0.9, 0.7, 1.1])
    make('Scorch', m, ao, hull=0)
    m = new(pal)
    rnd = random.Random(5)
    for i in range(7):
        x, y = rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4)
        s = rnd.uniform(0.05, 0.12)
        m.bx(x - s, x + s, y - s * 0.8, y + s * 0.8, 0.0, s * 0.9, rnd.choice(('conc', 'limeD', 'brickT', 'concF')), hull='none', cull='b')
    for i in range(5):
        x, y = rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4)
        m.cy((x, y, 0.0), 0.012, 0.012, 0.05, 'pYellow', seg=5, rot=(90, 0, rnd.uniform(0, 180)), hull='none')
    make('Rubble', m, ao, hull=0)
    # tram rails (one cell, along Blender Y)
    m = new(pal)
    for x in (-0.72, 0.72):
        m.bx(x - 0.05, x + 0.05, -0.5, 0.5, 0.004, 0.02, 'steel', hull='none', cull='b')
        m.bx(x - 0.013, x + 0.013, -0.5, 0.5, 0.02, 0.024, 'chrome', hull='none', cull='b')
    make('Rails', m, ao, hull=0)


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    """Checkpoint gate building bridging the street: a sandbagged steel portal over the 3 m opening, four storeys of
    brick above it (the same on both faces), a red-and-white 'CHECKPOINT' board and amber lamps."""
    m = new(pal)
    H = 19.0
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.48, sx * GW))
        m.bx(x0, x1, -1.0, 1.0, 0, H, 'brickT', cull='b')
    m.bx(-1.48, 1.48, -1.0, 1.0, 4.4, H, 'brickT', cull='')
    m.bx(-GW - 0.1, GW + 0.1, -1.08, 1.08, H, H + 0.4, 'brickTD')
    m.bx(-GW - 0.06, GW + 0.06, -1.04, 1.04, H + 0.4, H + 0.55, 'conc')
    for sy in (-1, 1):
        m.parent = Matrix.Rotation(0 if sy < 0 else math.pi, 4, 'Z')
        m.bx(-1.75, 1.75, -1.14, -0.98, 3.2, 4.4, 'steelD')
        for x in (-1.6, 1.6):
            m.bx(x - 0.18, x + 0.18, -1.16, -0.98, 0, 3.2, 'steelD')
        for k in range(7):
            x = -1.5 + k * 0.5
            fq(m, x, x + 0.25, -1.145, 3.6, 3.98, 'pipeR' if k % 2 else 'pWhite')
        fq(m, -1.25, 1.25, -1.15, 3.62, 3.96, 'pWhite')
        txt(m, 'CHECKPOINT', 0.0, -1.153, 3.79, 0.22, 'pipeR', font='display', maxw=2.3)
        for k in range(3):
            z0 = 5.6 + k * 4.4
            for x in (-2.0, -0.7, 0.7, 2.0):
                g = 'tape' if k == 0 else ('mull' if (k + int(x * 2)) % 3 == 0 else 'glass')
                fq(m, x - 0.36, x + 0.36, -1.012, z0 + 0.5, z0 + 2.5, 'mull')
                fq(m, x - 0.31, x + 0.31, -1.02, z0 + 0.55, z0 + 2.45, 'glass' if g == 'tape' else g)
                if g == 'tape':
                    for sgn in (-1, 1):
                        yy = -1.025 if sgn > 0 else -1.029
                        poly(m, [(x - 0.28 * sgn - 0.03, yy, z0 + 0.6), (x - 0.28 * sgn + 0.03, yy, z0 + 0.6), (x + 0.28 * sgn + 0.03, yy, z0 + 2.4), (x + 0.28 * sgn - 0.03, yy, z0 + 2.4)], 'cream', (0, -1, 0))
                m.bx(x - 0.42, x + 0.42, -1.1, -0.99, z0 + 0.38, z0 + 0.5, 'lime', hull='none', cull='klr')
        for x in (-1.6, 1.6):
            m.bx(x - 0.1, x + 0.1, -1.32, -1.16, 2.7, 2.95, 'litA', hull='none')
        # sandbag walls in front of both piers
        P0 = m.parent
        for x0 in (-GW + 0.05, 1.85):
            m.parent = P0 @ Matrix.Translation((0, -1.45, 0))
            sandbag_wall(m, x0, x0 + 1.05, 0.0, rows=4)
        m.parent = P0
    m.parent = Matrix.Identity(4)
    m.bx(-1.505, 1.505, -0.12, 0.12, 3.06, 4.4, 'mull', hull='none', cull='t')
    make('GateFrame', m, ao, bevel=0.015, cols=[box(-GW, -1.7, 0, -1.48, -1.0, 0.8), box(1.48, -1.7, 0, GW, -1.0, 0.8),
                                                   box(-GW, 1.0, 0, -1.48, 1.7, 0.8), box(1.48, 1.0, 0, GW, 1.7, 0.8)])
    m = new(pal)
    Hs, slats = 3.05, 12
    for i in range(slats):
        z0 = 0.42 + i * (Hs - 0.42) / slats
        m.bx(-1.5, 1.5, -0.07, 0.07, z0, z0 + (Hs - 0.42) / slats - 0.03, 'steel' if i % 2 else 'galv', hull='none')
    for k in range(10):
        m.bx(-1.5 + k * 0.3, -1.2 + k * 0.3, -0.08, 0.08, 0.0, 0.4, 'ink' if k % 2 else 'lineY', hull='none')
    sh = make('GateShutter', m, ao, hull=0)
    m = new(pal)
    m.bx(-1.5, 1.5, -0.08, 0.08, 0, Hs, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(sh, tmp)


TRAIL_H = 16.0


def build_trail(pal, ao):
    """Alley wall (1 m slice, both faces alike): tan brick, a concrete plinth, stone bands, small windows on two upper
    floors; variants with a downpipe and with an iron fire-escape ladder."""
    for name, extra in (('TrailWall', None), ('TrailWall_B', 'pipe'), ('TrailWall_C', 'vent')):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.6, TRAIL_H, 'brickT', hull='noend', cull='bt')
        m.bx(-0.3, 0.3, -0.5, 0.5, 0, 0.6, 'conc', hull='noend', cull='b')
        m.bx(-0.33, 0.33, -0.5, 0.5, TRAIL_H, TRAIL_H + 0.18, 'conc', hull='noend')
        for sx in (-1, 1):
            cl = 'r' if sx < 0 else 'l'

            def face(d0, d1, y0, y1, z0, z1, c):
                x0, x1 = sorted((sx * (0.25 + d0), sx * (0.25 + d1)))
                m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cl + 'tbfk')
            for zb in (4.4, 10.8):
                x0, x1 = sorted((sx * 0.25, sx * 0.3))
                m.bx(x0, x1, -0.5, 0.5, zb, zb + 0.3, 'lime', hull='none', cull=cl + 'fk')
            for k in range(14):
                z = 1.0 + k * 1.05
                if abs(z - 4.55) < 0.5 or abs(z - 10.95) < 0.5:
                    continue
                face(0.0, 0.004, -0.5, 0.5, z, z + 0.03, 'brickTD')
            for (z0, lit) in ((7.4, sx < 0), (13.6, sx > 0)):
                face(0.0, 0.01, -0.2, 0.2, z0 - 1.5, z0 - 0.2, 'mull')
                face(0.0, 0.016, -0.17, 0.17, z0 - 1.47, z0 - 0.23, 'glass' if lit else 'interior')
            if extra == 'pipe':
                x = sx * 0.33
                m.cy((x, 0.3, 0.0), 0.06, 0.06, TRAIL_H, 'steelD', seg=6, hull='none')
            elif extra == 'vent':
                face(0.0, 0.08, -0.3, 0.3, 2.4, 2.9, 'galv')
                for k in range(3):
                    face(0.08, 0.09, -0.26, 0.26, 2.48 + k * 0.14, 2.52 + k * 0.14, 'steelD')
        make(name, m, ao)


def build_hatch(pal, ao):
    """Exit pad: a sidewalk cellar hatch (diamond-plate doors), teal lamps round it."""
    m = new(pal)
    m.cy((0, 0, 0), 1.3, 1.24, 0.1, 'walk', seg=10)
    m.cy((0, 0, 0.1), 1.08, 1.08, 0.025, 'teal', seg=10, hull='none')
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.105, 0.17, 'steelD')
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.03, sy * 0.84))
        m.bx(-0.84, 0.84, y0, y1, 0.165, 0.185, 'steel', hull='none', cull='b')
        for k in range(4):
            x = -0.55 + k * 0.36
            m.bx(x - 0.06, x + 0.06, sy * 0.45 - 0.03, sy * 0.45 + 0.03, 0.185, 0.195, 'galv', hull='none', cull='b')
    for i in range(8):
        a = i / 8 * math.pi * 2 + math.pi / 8
        m.cy((math.cos(a) * 1.17, math.sin(a) * 1.17, 0.1), 0.06, 0.05, 0.06, 'litA', seg=6, hull='none')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ backdrop
def build_backdrop(pal, ao):
    """daylight skyline beyond the walls: an office block row, a glass tower, a limestone deco spire"""
    m = new(pal)
    rnd = random.Random(8)
    x0 = -18.0
    for (c, h, w) in (('lime', 24, 9), ('brickT', 30, 8), ('concF', 22, 10), ('terra', 28, 9)):
        m.bx(x0 + 0.02, x0 + w - 0.02, -5, 5, 0, h, c)
        m.bx(x0 - 0.08, x0 + w + 0.08, -5.25, 4.9, h, h + 0.6, 'roof')
        for f in range(int((h - 3) / 3.4)):
            z = 3 + f * 3.4
            for k in range(int(w / 2.0)):
                x = x0 + 1.0 + k * 2.0
                if x + 0.4 > x0 + w:
                    break
                fq(m, x - 0.4, x + 0.4, -5.08, z, z + 1.8, 'glass' if rnd.random() < 0.7 else 'mull')
        x0 += w
    m.bx(-6, 0, -5.3, -5.05, 31.0, 34.5, 'mull')
    m.bx(-5.8, -0.2, -5.32, -5.3, 31.2, 34.3, 'cream', hull='none')
    make('Backdrop_Block', m, ao)
    m = new(pal)
    for (h, z0, z1, c) in ((8, 0, 40, 'concF'), (6, 40.4, 56, 'glass'), (4, 56.4, 62, 'concF')):
        m.bx(-h, h, -h, h, z0, z1, c)
        m.bx(-h - 0.3, h + 0.3, -h - 0.3, h + 0.3, z1, z1 + 0.4, 'mull')
        for k in range(h):
            x = -h + 1 + k * 2
            m.bx(x - 0.1, x + 0.1, -h - 0.06, -h + 0.06, z0, z1, 'mull', hull='none', cull='ktblr')
        for fz in range(int((z1 - z0) / 3.4)):
            m.bx(-h, h, -h - 0.07, -h + 0.06, z0 + fz * 3.4, z0 + fz * 3.4 + 0.5, 'steel', hull='none', cull='ktblr')
    m.cy((0, 0, 62.4), 0.15, 0.08, 6.0, 'steelD', seg=5, hull='none')
    m.sp((0, 0, 68.5), 0.4, 'red', seg=(6, 4), hull='none')
    make('Backdrop_Tower', m, ao)
    m = new(pal)
    m.bx(-7, 7, -7, 7, 0, 42, 'lime')
    for (h, z0, z1) in ((5.5, 42, 52), (4, 52, 60), (2.6, 60, 66)):
        m.bx(-h, h, -h, h, z0, z1, 'limeD' if h == 4 else 'lime')
    m.cy((0, 0, 66), 2.6 * math.sqrt(2), 0.0, 14, 'terra', seg=4, rot=(0, 0, 45))
    for k in range(4):
        m.parent = Matrix.Rotation(k * math.pi / 2, 4, 'Z')
        for x in (-4.5, -1.5, 1.5, 4.5):
            fq(m, x - 0.4, x + 0.4, -7.06, 2, 40, 'limeD')
        for x in (-3.0, 0.0, 3.0):
            fq(m, x - 0.2, x + 0.2, -7.09, 6, 38, 'glass')
    m.parent = Matrix.Identity(4)
    make('Backdrop_Spire', m, ao)
