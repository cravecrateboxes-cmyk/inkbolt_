"""kit-airport structure: wall modules (terminal: stone cladding under white composite panels, with wall art --
lightbox ads, flight-information screens, restrooms, staff doors, wayfinding, fire points, the MERIDIAN logo; the
glass curtain wall with entrance doors and the jet-bridge door; the concrete cores by the gates; the hangar lining
with columns, panels and the MERIDIAN AERO logo; the hangar front wall (two-sided) and its door pockets; the apron
blast fence (two-sided); the ground-operations building), corner posts, the gate, the service corridor (trail)
walls, the exit hatch, ceiling lights, hangar roof trusses and the door header, terminal ceiling features, decks
(glass and scaffold rails, columns, posts), stairs and escalators, floor marks (see ap_base.py for conventions)."""
import math
import random

from ap_base import *  # noqa: F401,F403
import ap_base as B
import ap_detail as D


# ================================================================ terminal walls (front face y = -0.5)
def wall_term(m, z0=0.0, z1=H):
    """pale stone cladding to 3 m, a timber band, white composite panels above with reveals, a light cove"""
    if z0 < 0.15:
        fq(m, -0.5, 0.5, -0.5, 0.0, 0.15, 'stoneD')
    if z0 < 3.0:
        fq(m, -0.5, 0.5, -0.5, max(0.15, z0), 3.0, 'stone')
        for z in (1.1, 2.05):
            if z > z0:
                fq(m, -0.5, 0.5, -0.503, z - 0.008, z + 0.008, 'stoneD')
        fq(m, -0.008, 0.008, -0.506, max(0.15, z0), 3.0, 'stoneD')
    if z1 > 3.3:
        fq(m, -0.5, 0.5, -0.5, max(3.0, z0), 3.3, 'wood')
        fq(m, -0.5, 0.5, -0.503, 3.24, 3.27, 'woodD')
        fq(m, -0.5, 0.5, -0.5, max(3.3, z0), min(z1, 13.5), 'wallW')
        for z in (5.9, 8.5, 11.1):
            fq(m, -0.5, 0.5, -0.503, z - 0.01, z + 0.01, 'joint')
        fq(m, -0.01, 0.01, -0.506, max(3.3, z0), 13.5, 'joint')
        fq(m, -0.5, 0.5, -0.5, 13.5, H, 'ceil')
    D.wall_fit(m, z0, z1)


def core(m):
    """the concrete cores by the gates: board-formed concrete with tie holes"""
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'conc')
    for z in (1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4, 9.6, 10.8, 12.0, 13.2):
        fq(m, -0.5, 0.5, -0.503, z - 0.006, z + 0.006, 'concD')
    for z in (0.6, 3.0, 5.4, 7.8, 10.2, 12.6):
        vdisc(m, 0.0, -0.503, z, 0.025, 'concD', seg=6)


def curtain(m, kind='A', z0=0.0):
    """1 m of the glass curtain wall: an upstand, the glass line 15 cm behind the face (open glazing: glints only),
    transoms, a head; kind 'M' adds the 3 m bay's mullion and a fin outside"""
    yg = -0.35
    if z0 < 0.3:
        m.bx(-0.5, 0.5, -0.5, -0.28, 0.0, 0.3, 'wallL', hull='noside', cull='b')
        fq(m, -0.5, 0.5, -0.503, 0.0, 0.08, 'black')
    for (za, zb) in ((3.4, 3.48), (7.0, 7.08), (10.6, 10.68)):
        if za >= z0:
            m.bx(-0.5, 0.5, yg - 0.04, yg + 0.04, za, zb, 'mull', hull='noside', cull='')
    m.bx(-0.5, 0.5, -0.5, -0.25, 13.55, H, 'wallW', hull='noside', cull='t')
    if kind == 'M':
        m.bx(-0.05, 0.05, yg - 0.07, yg + 0.05, max(0.3, z0), 13.55, 'mull', cull='bt')
        m.bx(-0.035, 0.035, yg + 0.05, yg + 0.55, 0.3, 13.55, 'chrome', cull='bt')
    elif kind == 'A':
        glint(m, -0.32, yg, max(0.9, z0 + 0.6), 1.1)
        glint(m, -0.2, yg, 7.6, 1.4)
    else:
        glint(m, 0.0, yg, 4.0, 1.6)
        glint(m, -0.25, yg, 11.0, 1.2)
    D.curtain_fit(m, kind, z0)


def ext_point(m, x=0.0):
    """fire point: a red extinguisher in a recessed cabinet and a sign above"""
    m.bx(x - 0.18, x + 0.18, -0.53, -0.503, 0.35, 1.3, 'red', cull='k')
    fq(m, x - 0.13, x + 0.13, -0.533, 0.45, 1.15, 'glassL')
    m.cy((x, -0.6, 0.48), 0.09, 0.09, 0.5, 'red', seg=8)
    m.bx(x - 0.15, x + 0.15, -0.53, -0.503, 1.55, 1.8, 'red', cull='k')
    text_front(m, 'FIRE', 0.14, -0.533, x, 1.6, 'paper')


def build_walls(pal, ao):
    m = new(pal); wall_term(m); make('WT', m, ao)
    m = new(pal); wall_term(m); ext_point(m); make('WT_Fire', m, ao)
    # corner post: cladding on all four sides
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'wallW', cull='bt')
    for (c, z0, z1) in (('stoneD', 0.0, 0.15), ('stone', 0.15, 3.0), ('wood', 3.0, 3.3), ('ceil', 13.5, H)):
        fq(m, -0.5, 0.5, -0.503, z0, z1, c); bq(m, -0.5, 0.5, 0.503, z0, z1, c)
        lq(m, -0.503, -0.5, 0.5, z0, z1, c); rq(m, 0.503, -0.5, 0.5, z0, z1, c)
    D.corner_post_fit(m)
    make('CornerT', m, ao)
    m = new(pal); core(m); D.core_fit(m); make('WC', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'conc', cull='bt')
    make('CornerC', m, ao)
    # lightbox ads (1 m wide, 2.4 m tall, lit: glow companions) for made-up brands
    ADS = [('A', 'NIMBUS', 'WATCHES', 'navy', 'sun'), ('B', 'AURORA', 'TRAVEL', 'coral', 'paper'), ('C', 'KESTREL', 'HEADPHONES', 'black', 'scrB'),
           ('D', 'SKYLARK', 'FLY MORE', 'sky', 'sun')]
    for key, w1, w2, bg, fg in ADS:
        m = new(pal); wall_term(m)
        m.bx(-0.45, 0.45, -0.62, -0.503, 0.55, 3.0, 'steelD', cull='k')
        D.lightbox_frame(m)
        make('WT_Ad' + key, m, ao)
        g = new(pal)
        fq(g, -0.4, 0.4, -0.623, 0.6, 2.95, bg)
        text_front(g, w1, 0.2, -0.626, 0.0, 2.2, fg, maxw=0.72)
        text_front(g, w2, 0.09, -0.626, 0.0, 2.0, 'paper', font='cond', maxw=0.7)
        if key == 'A':
            vdisc(g, 0.0, -0.629, 1.35, 0.22, 'chrome', seg=12)
            vdisc(g, 0.0, -0.632, 1.35, 0.17, 'paper', seg=12)
            fq(g, -0.008, 0.008, -0.635, 1.35, 1.5, 'black'); fq(g, 0.0, 0.1, -0.638, 1.342, 1.358, 'black')
        elif key == 'B':
            for i in range(3):
                poly(g, [(-0.3 + i * 0.12, -0.628, 0.8), (-0.18 + i * 0.12, -0.628, 0.8), (0.1 + i * 0.12, -0.628, 1.7), (-0.02 + i * 0.12, -0.628, 1.7)], ('sun', 'paper', 'skyL')[i], (0, -1, 0))
        elif key == 'C':
            fq(g, -0.14, 0.14, -0.628, 1.6, 1.67, 'scrB')
            for s in (-1, 1):
                fq(g, s * 0.2 - 0.06, s * 0.2 + 0.06, -0.628, 1.05, 1.58, 'scrB')
        else:
            poly(g, [(-0.3, -0.628, 0.9), (0.3, -0.628, 1.3), (0.28, -0.628, 1.4), (-0.32, -0.628, 1.0)], 'paper', (0, -1, 0))
            poly(g, [(-0.05, -0.631, 1.1), (0.15, -0.631, 1.25), (-0.15, -0.631, 1.55), (-0.2, -0.631, 1.45)], 'skyL', (0, -1, 0))
        make_glow('WT_Ad' + key + '_LED', g)
    # flight information screens: three portrait screens on a dark panel (glow companion: the screens)
    m = new(pal); wall_term(m)
    m.bx(-0.48, 0.48, -0.6, -0.503, 1.6, 3.6, 'black', cull='k')
    fq(m, -0.48, 0.48, -0.603, 3.32, 3.56, 'sun')
    text_front(m, 'DEPARTURES', 0.15, -0.606, 0.0, 3.37, 'black', maxw=0.85)
    D.fids_frame(m)
    make('WT_FIDS', m, ao)
    g = new(pal)
    for k in range(3):
        x = -0.32 + k * 0.32
        fq(g, x - 0.14, x + 0.14, -0.606, 1.7, 3.25, 'screen')
        for r in range(9):
            z = 3.15 - r * 0.16
            fq(g, x - 0.12, x - 0.03, -0.609, z - 0.03, z + 0.03, 'sun')
            fq(g, x - 0.01, x + 0.08, -0.609, z - 0.03, z + 0.03, 'paper')
            fq(g, x + 0.09, x + 0.12, -0.609, z - 0.03, z + 0.03, ('scrG', 'scrG', 'sun', 'scrG', 'scrR', 'scrG', 'scrG', 'sun', 'scrG')[(r + k * 4) % 9])
    make_glow('WT_FIDS_LED', g)
    # restrooms: a dark doorway with a privacy screen behind it and a blue sign above
    m = new(pal); wall_term(m, z0=2.4)
    fq(m, -0.5, 0.5, -0.5, 0.0, 0.15, 'stoneD')
    m.bx(-0.5, -0.38, -0.5, 0.3, 0.15, 2.4, 'stone', cull='b')
    m.bx(0.38, 0.5, -0.5, 0.3, 0.15, 2.4, 'stone', cull='b')
    bq(m, -0.38, 0.38, 0.3, 0.0, 2.4, 'mull')
    dq(m, -0.38, 0.38, -0.5, 0.3, 2.4, 'black')
    m.bx(-0.45, 0.45, -0.58, -0.5, 2.5, 2.9, 'sky', cull='k')
    text_front(m, 'RESTROOMS', 0.15, -0.583, 0.0, 2.6, 'paper', maxw=0.8)
    make('WT_WC', m, ao)
    # staff door: a grey steel leaf with a kick plate and a keypad
    m = new(pal); wall_term(m)
    m.bx(-0.46, 0.46, -0.56, -0.503, 0.0, 2.3, 'steelD', cull='kb')
    fq(m, -0.4, 0.4, -0.563, 0.02, 2.24, 'wallL')
    fq(m, -0.4, 0.4, -0.566, 0.05, 0.3, 'chrome')
    m.bx(0.24, 0.32, -0.6, -0.563, 1.0, 1.06, 'chrome', hull='none', cull='k')
    m.bx(0.5 - 0.02, 0.5, -0.6, -0.5, 1.3, 1.5, 'black', hull='none', cull='k')
    fq(m, -0.3, 0.3, -0.566, 1.5, 1.72, 'red')
    text_front(m, 'STAFF ONLY', 0.12, -0.569, 0.0, 1.55, 'paper', maxw=0.55)
    D.staff_door_fit(m)
    make('WT_Door', m, ao)
    # wayfinding: a black sign with yellow lettering and an arrow (two versions)
    for key, word, arrow in (('A', 'GATES  A1-A6', 1), ('B', 'CHECK-IN', -1)):
        m = new(pal); wall_term(m)
        m.bx(-0.5, 0.5, -0.56, -0.503, 4.0, 4.7, 'black', hull='noside', cull='k')
        text_front(m, word, 0.32, -0.563, -0.08 * arrow, 4.17, 'sun', maxw=0.72)
        x = 0.4 * arrow
        poly(m, [(x - 0.06 * arrow, -0.564, 4.2), (x + 0.04 * arrow, -0.564, 4.35), (x - 0.06 * arrow, -0.564, 4.5)], 'sun', (0, -1, 0))
        D.sign_frame(m)
        make('WT_Way' + key, m, ao)
    # ---- the curtain wall
    for kind in ('A', 'B', 'M'):
        m = new(pal); curtain(m, kind); make('WG' if kind == 'A' else 'WG_' + kind, m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, -0.2, 0.0, 0.3, 'wallL', cull='b')
    m.bx(-0.12, 0.12, -0.47, -0.23, 0.3, H, 'mull', cull='b')
    D.corner_glass_fit(m)
    make('CornerG', m, ao)
    # entrance doors in the curtain wall: an automatic sliding pair per module under a lit header
    m = new(pal); curtain(m, 'M', z0=3.0)
    yg = -0.35
    for x in (-0.47, 0.47):
        m.bx(x - 0.03, x + 0.03, yg - 0.06, yg + 0.06, 0.0, 2.7, 'mull', cull='b')
    m.bx(-0.5, 0.5, -0.56, yg + 0.06, 2.7, 3.05, 'mull', hull='noside', cull='')
    for x0, x1 in ((-0.44, -0.02), (0.02, 0.44)):
        for (za, zb) in ((0.0, 0.08), (2.62, 2.7)):
            m.bx(x0, x1, yg - 0.025, yg + 0.025, za, zb, 'chrome', hull='none', cull='')
        for xx in (x0, x1 - 0.03):
            m.bx(xx, xx + 0.03, yg - 0.025, yg + 0.025, 0.08, 2.62, 'chrome', hull='none', cull='')
    glint(m, -0.3, yg - 0.03, 0.8, 1.0)
    fq(m, -0.4, 0.4, -0.563, 2.78, 2.98, 'scrG')
    m.bx(-0.5, 0.5, -0.12, 0.5, -0.01, 0.0, 'conc', hull='none', cull='bfklr')
    D.entrance_fit(m)
    make('WG_Door', m, ao)
    g = new(pal)
    fq(g, -0.4, 0.4, -0.566, 2.78, 2.98, 'scrG')
    text_front(g, 'ENTRANCE', 0.13, -0.569, 0.0, 2.82, 'paper', maxw=0.7)
    make_glow('WG_Door_LED', g)
    # the jet-bridge door: a dark portal in the glazing with a closed glass door, the gate number and a status light
    m = new(pal); curtain(m, 'M', z0=3.2)
    m.bx(-0.5, 0.5, -0.56, 0.5, 2.5, 3.4, 'mull', hull='noside', cull='')
    for x in (-0.47, 0.47):
        m.bx(x - 0.03, x + 0.03, -0.56, 0.5, 0.0, 2.5, 'mull', cull='b')
    bq(m, -0.44, 0.44, 0.3, 0.0, 2.5, 'steelD')
    m.bx(-0.44, 0.44, -0.4, -0.36, 0.0, 2.5, 'glass', hull='none', cull='')
    glint(m, -0.3, -0.403, 0.6, 1.2)
    m.bx(0.3, 0.36, -0.44, -0.4, 1.0, 1.15, 'chrome', hull='none', cull='k')
    m.bx(-0.5, 0.5, -0.5, 0.5, -0.01, 0.0, 'stoneD', hull='none', cull='bfklr')
    D.bridge_fit(m)
    make('WG_Bridge', m, ao)
    g = new(pal)
    fq(g, -0.4, 0.4, -0.563, 2.6, 3.3, 'screen')
    text_front(g, 'A3', 0.42, -0.566, -0.12, 2.75, 'sun')
    fq(g, 0.18, 0.34, -0.566, 2.8, 3.1, 'scrG')
    make_glow('WG_Bridge_LED', g)


# ================================================================ hangar, apron and ops walls
def lining(m, face=-1, z0=0.0):
    """the hangar lining on the face at y = 0.5 * face: a concrete plinth, corrugated steel, girts, a translucent
    clerestory band, the eave"""
    Q = fq if face < 0 else bq
    y = 0.5 * face
    d = 0.003 * face
    if z0 < 1.2:
        Q(m, -0.5, 0.5, y, z0, 1.2, 'conc')
        Q(m, -0.5, 0.5, y + d, 1.12, 1.2, 'sun')
    Q(m, -0.5, 0.5, y, max(1.2, z0), 10.0, 'corr')
    for k in range(4):
        x = -0.375 + k * 0.25
        Q(m, x - 0.035, x + 0.035, y + d, max(1.2, z0), 10.0, 'corrD')
    for z in (4.6, 8.0):
        if z > z0:
            Q(m, -0.5, 0.5, y + 2 * d, z - 0.07, z + 0.07, 'steelD')
    Q(m, -0.5, 0.5, y, 10.0, 12.2, 'glassL')
    for x in (-0.25, 0.25):
        Q(m, x - 0.015, x + 0.015, y + d, 10.0, 12.2, 'corrD')
    Q(m, -0.5, 0.5, y, 12.2, H, 'steelD')


def outer(m, face=-1):
    """the hangar's outside cladding (on the apron): navy plinth band, light corrugated steel, a dark eave"""
    Q = fq if face < 0 else bq
    y = 0.5 * face
    d = 0.003 * face
    Q(m, -0.5, 0.5, y, 0.0, 1.0, 'concD')
    Q(m, -0.5, 0.5, y, 1.0, 12.8, 'corr')
    for k in range(4):
        x = -0.375 + k * 0.25
        Q(m, x - 0.04, x + 0.04, y + d, 1.0, 12.8, 'corrD')
    Q(m, -0.5, 0.5, y, 12.8, H, 'navy')
    Q(m, -0.5, 0.5, y + d, 12.8, 12.9, 'coral')


def fence(m):
    """the apron blast fence: a 4.8 m wall of slatted deflector panels leaning back on a steel frame (two-sided)"""
    for k in range(4):
        z0 = 0.35 + k * 1.1
        a, b = -0.5 + k * 0.08, -0.25 + k * 0.08
        wedge_slat(m, z0, z0 + 1.04, a, b)
    m.bx(-0.5, 0.5, -0.5, 0.2, 0.0, 0.35, 'conc', hull='noside', cull='b')
    fq(m, -0.5, 0.5, -0.503, 0.05, 0.3, 'sun')
    for k in range(3):
        x = -0.45 + k * 0.4
        poly(m, [(x, -0.506, 0.05), (x + 0.14, -0.506, 0.05), (x + 0.39, -0.506, 0.3), (x + 0.25, -0.506, 0.3)], 'black', (0, -1, 0))
    # the frame behind: a raking strut and a post per module
    m.bm_((0.0, 0.2, 0.35), (0.0, -0.18, 4.75), 0.07, 'steelD')
    m.bm_((0.0, 0.45, 0.35), (0.0, -0.05, 2.6), 0.06, 'steelD')
    m.bx(-0.04, 0.04, 0.2, 0.5, 0.0, 0.35, 'conc', hull='none', cull='b')


def wedge_slat(m, z0, z1, a, b):
    """one deflector slat across the module, its face toward -Y, tilted back"""
    v = [(-0.5, a, z0), (0.5, a, z0), (0.5, a + 0.06, z0), (-0.5, a + 0.06, z0),
         (-0.5, b, z1), (0.5, b, z1), (0.5, b + 0.06, z1), (-0.5, b + 0.06, z1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    skin(m, (v, f), 'corr', hull='noside')


def ops(m, z0=0.0):
    """the ground-operations building facing the apron: a dark glazed ground floor, two ribbon-window floors
    (layers: wall -0.500, glass -0.503, transoms -0.506, mullions -0.509, glints -0.512)"""
    fq(m, -0.5, 0.5, -0.5, 0.0, 0.4, 'concD')
    fq(m, -0.5, 0.5, -0.5, 0.4, 3.6, 'screen')
    fq(m, -0.5, 0.5, -0.506, 2.5, 2.56, 'mull')
    fq(m, -0.03, 0.03, -0.509, 0.4, 3.6, 'mull')
    glint(m, -0.42, -0.512, 0.8, 1.2, w=0.1, c='glass')
    fq(m, -0.5, 0.5, -0.5, 3.6, 4.4, 'navy')
    fq(m, -0.5, 0.5, -0.5, 4.4, 13.2, 'conc')
    for (za, zb) in ((5.6, 7.6), (9.2, 11.2)):
        fq(m, -0.5, 0.5, -0.503, za, zb, 'glass')
        fq(m, -0.5, 0.5, -0.506, za, za + 0.08, 'mull')
        fq(m, -0.03, 0.03, -0.509, za + 0.08, zb, 'mull')
        glint(m, -0.4, -0.512, za + 0.3, 1.2, w=0.1, c='glassL')
    fq(m, -0.5, 0.5, -0.5, 13.2, H, 'navy')
    fq(m, -0.5, 0.5, -0.503, 13.2, 13.28, 'coral')


def build_hangar_walls(pal, ao):
    m = new(pal); lining(m); make('WH', m, ao)
    # a steel column (I-section, sky-blue) standing proud of the lining every 6 m, with a yellow foot guard
    m = new(pal); lining(m)
    m.bx(-0.2, 0.2, -0.56, -0.503, 1.0, H, 'sky', cull='btk')
    m.bx(-0.04, 0.04, -0.86, -0.56, 1.0, H, 'sky', cull='btk')
    m.bx(-0.2, 0.2, -0.92, -0.86, 1.0, H, 'sky', cull='bt')
    m.bx(-0.26, 0.26, -0.98, -0.503, 0.0, 1.0, 'sun', cull='bk')
    for z in (0.25, 0.65):
        fq(m, -0.26, 0.26, -0.983, z, z + 0.15, 'black')
    make('WH_Col', m, ao, cols=[cb(-0.27, -0.99, 0.0, 0.27, -0.5, H)])
    m = new(pal); lining(m); ext_point(m); make('WH_Fire', m, ao)
    # an air / power drop: a hose reel, a yellow electrical panel, a red stop button
    m = new(pal); lining(m)
    m.bx(-0.42, 0.0, -0.75, -0.503, 1.2, 2.2, 'sun', cull='k')
    fq(m, -0.38, -0.04, -0.753, 1.9, 2.1, 'black')
    text_front(m, '400 HZ', 0.1, -0.756, -0.21, 1.94, 'sun')
    vdisc(m, -0.21, -0.757, 1.55, 0.06, 'red', seg=8)
    cyl_y(m, 0.25, -0.82, -0.503, 1.6, 0.26, 'red', seg=10)
    vdisc(m, 0.25, -0.823, 1.6, 0.12, 'black', seg=10)
    make('WH_Panel', m, ao)
    # safety board
    m = new(pal); lining(m)
    m.bx(-0.48, 0.48, -0.56, -0.503, 1.4, 2.6, 'paper', cull='k')
    fq(m, -0.48, 0.48, -0.563, 2.3, 2.6, 'scrG')
    text_front(m, 'SAFETY FIRST', 0.17, -0.566, 0.0, 2.36, 'paper', maxw=0.85)
    for r in range(4):
        fq(m, -0.4, 0.4 - 0.15 * (r % 2), -0.563, 2.12 - r * 0.17, 2.16 - r * 0.17, 'steelD')
    fq(m, -0.4, 0.4, -0.563, 1.47, 1.55, 'sun')
    make('WH_Board', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'corr', cull='bt')
    for (c, z0, z1) in (('conc', 0.0, 1.2), ('steelD', 12.2, H)):
        fq(m, -0.5, 0.5, -0.503, z0, z1, c); bq(m, -0.5, 0.5, 0.503, z0, z1, c)
        lq(m, -0.503, -0.5, 0.5, z0, z1, c); rq(m, 0.503, -0.5, 0.5, z0, z1, c)
    make('CornerH', m, ao)
    # front wall (two-sided: the apron outside (-Y), the lining inside (+Y))
    m = new(pal); outer(m, -1); lining(m, 1); make('WF', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'corr', cull='bt')
    for (c, z0, z1) in (('concD', 0.0, 1.0), ('navy', 12.8, H)):
        fq(m, -0.5, 0.5, -0.503, z0, z1, c); bq(m, -0.5, 0.5, 0.503, z0, z1, c)
        lq(m, -0.503, -0.5, 0.5, z0, z1, c); rq(m, 0.503, -0.5, 0.5, z0, z1, c)
    make('CornerF', m, ao)
    # door pockets: the slid-back hangar door leaves (panel seams, a rubber seal, the door number), both faces
    for v in range(2):
        m = new(pal)
        for s in (-1, 1):
            Q = fq if s < 0 else bq
            y = 0.5 * s
            Q(m, -0.5, 0.5, y, 0.0, 12.8, 'corrD' if v else 'corr')
            for z in (3.2, 6.4, 9.6):
                Q(m, -0.5, 0.38 if v else 0.5, y + 0.003 * s, z - 0.03, z + 0.03, 'steelD')
            Q(m, -0.5, 0.5, y, 12.8, H, 'navy')
            if v:
                Q(m, 0.38, 0.5, y + 0.003 * s, 0.25, 12.8, 'black')
            Q(m, -0.5, 0.5, y + 0.003 * s, 0.0, 0.25, 'sun')
        make('WF_Door' + 'AB'[v], m, ao)
    # apron blast fence and its corner
    m = new(pal); fence(m); make('WA', m, ao)
    m = new(pal); fence(m)
    m.bx(-0.45, 0.45, -0.58, -0.52, 1.3, 2.2, 'red', hull='noside', cull='k')
    text_front(m, 'DANGER', 0.22, -0.583, 0.0, 1.85, 'paper', maxw=0.8)
    text_front(m, 'JET BLAST', 0.18, -0.583, 0.0, 1.45, 'paper', maxw=0.8)
    make('WA_Sign', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, 4.9, 'conc', cull='b')
    m.bx(-0.52, 0.52, -0.52, 0.52, 4.9, 5.05, 'steelD', cull='b')
    make('CornerA', m, ao)
    # ground operations building
    m = new(pal); ops(m); make('WO', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'conc', cull='bt')
    for (c, z0, z1) in (('navy', 3.6, 4.4), ('navy', 13.2, H)):
        fq(m, -0.5, 0.5, -0.503, z0, z1, c); bq(m, -0.5, 0.5, 0.503, z0, z1, c)
        lq(m, -0.503, -0.5, 0.5, z0, z1, c); rq(m, 0.503, -0.5, 0.5, z0, z1, c)
    make('CornerO', m, ao)

    # wall logos: flat lettering pieces laid over plain wall modules (a prefab over the wall cells, letters 12 mm
    # in front of the wall plane at local y = -0.5)
    m = new(pal)
    ib_text.draw(m, 'MERIDIAN', 0.0, -0.512, 7.0, 2.6, 'navy', face='y-', font='display', maxw=7.6, shadow='coral', shadow_off=(0.04, -0.04))
    ib_text.draw(m, 'INTERNATIONAL  AIRPORT', 0.0, -0.512, 6.15, 0.55, 'coral', face='y-', font='cond', maxw=7.6)
    make('Logo_T', m, ao)
    m = new(pal)
    ib_text.draw(m, 'MERIDIAN AERO', 0.0, -0.512, 5.0, 2.4, 'navy', face='y-', font='display', maxw=11.4)
    ib_text.draw(m, 'MAINTENANCE  -  HANGAR 2', 0.0, -0.512, 4.0, 0.62, 'coral', face='y-', font='cond', maxw=8.0)
    make('Logo_H', m, ao)
    m = new(pal)
    ib_text.draw(m, 'GROUND OPERATIONS', 0.0, -0.515, 12.0, 0.95, 'paper', face='y-', font='display', maxw=9.2)
    make('Logo_O', m, ao)

# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.49, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'steelD', cull='b')
        for fy in (-1, 1):
            for k in range(6):
                z0 = 0.1 + k * 0.32
                (fq if fy < 0 else bq)(m, a + 0.05, b - 0.05, fy * 0.623, z0, z0 + 0.16, 'sun')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.75, 'steelD')
    # the concrete core over the doors, both faces, with a wayfinding sign each side
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.75, H, 'conc', cull='t')
    for s in (-1, 1):
        Q = fq if s < 0 else bq
        for z in (4.8, 6.0, 7.2, 8.4, 9.6, 10.8, 12.0, 13.2):
            Q(m, -2.48, 2.48, s * 0.453, z - 0.006, z + 0.006, 'concD')
        ya, yb = sorted((s * 0.45, s * 0.6))
        m.bx(-1.7, 1.7, ya, yb, 4.2, 4.9, 'black', cull='k' if s < 0 else 'f')
        (text_front if s < 0 else text_back)(m, 'SERVICE CORRIDOR', 0.34, s * 0.603, 0.2 * s, 4.37, 'sun', maxw=2.5)
        ax = 1.36 * -s
        poly(m, [(ax, s * 0.604, 4.38), (ax - 0.16 * s, s * 0.604, 4.55), (ax, s * 0.604, 4.72)], 'sun', (0, s, 0))
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    g = new(pal)
    for s in (-1, 1):
        (fq if s < 0 else bq)(g, -0.45, 0.45, s * 0.623, 3.42, 3.66, 'scrG')
        (text_front if s < 0 else text_back)(g, 'EXIT', 0.17, s * 0.626, 0.0, 3.46, 'paper')
    make_glow('GateFrame_LED', g)
    # roll-up shutter
    m = new(pal)
    Hs, n = 3.05, 12
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.02), 'steel' if i % 2 else 'chrome', bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'black' if k % 2 else 'sun', bevel=False)
    m.box((0, -0.06, 1.95), (2.2, 0.01, 0.42), 'red', bevel=False)
    text_front(m, 'AUTHORIZED ONLY', 0.26, -0.069, 0.0, 1.83, 'paper', maxw=2.0)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # service corridor walls (1 m along Blender Y, inner face +X): painted block, a buffer rail, a drop ceiling
    # to the corridor centre line at 3.6 m (2.25 m from the wall's centre)
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'wallL', hull='noend', cull='t')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.14, 'concD')
        rq(m, 0.253, -0.5, 0.5, 1.4, DROP, 'wallW')
        rq(m, 0.253, -0.5, 0.5, 1.33, 1.4, 'sky')
        m.bx(0.25, 0.33, -0.5, 0.5, 0.8, 0.95, 'navy', hull='noend', cull='')
        m.bx(0.25, 2.25, -0.5, 0.5, DROP, DROP + 0.06, 'ceil', hull='none', cull='tlrfk')
        if name == 'TrailWall_B':   # a light panel under the drop ceiling
            m.bx(1.2, 1.8, -0.3, 0.3, DROP - 0.008, DROP, 'lightW', hull='none', cull='tlrfk')
        elif name == 'TrailWall_C':   # airside notice and a wall phone
            m.bx(0.253, 0.27, -0.34, 0.34, 1.5, 2.2, 'paper', cull='l')
            rq(m, 0.273, -0.3, 0.3, 2.02, 2.15, 'red')
            text_side(m, 'AIRSIDE', 0.1, 0.276, 0.0, 2.04, 'paper', 'x+', font='cond', maxw=0.5)
            text_side(m, 'ID AT ALL TIMES', 0.06, 0.276, 0.0, 1.85, 'black', 'x+', font='cond', maxw=0.55)
            m.bx(0.253, 0.36, 0.38, 0.47, 1.2, 1.45, 'sun', cull='l')
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=14)
    ring(m, 0, 0, 0.103, 0.95, 1.12, 'sun', seg=14)
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ ceilings and roofs (hang from z = 0 = the 14 m plane)
def truss_x(m, y, x0, x1, depth=1.6, n=8, c='steelD'):
    """a steel truss along X at y hanging from the roof plane: chords and a zigzag web"""
    m.bx(x0, x1, y - 0.1, y + 0.1, -0.22, -0.02, c, hull='noside', cull='t')
    m.bx(x0, x1, y - 0.09, y + 0.09, -depth - 0.18, -depth, c, hull='noside', cull='')
    w = (x1 - x0) / n
    for k in range(n):
        a = x0 + k * w
        m.bm_((a + 0.05, y, -0.2), (a + w / 2, y, -depth), 0.07, c, hull='none')
        m.bm_((a + w / 2, y + 0.012, -depth), (a + w - 0.05, y + 0.012, -0.2), 0.07, c, hull='none')


def build_roof(pal, ao):
    # terminal ceiling light: a round downlight ring (glow companion: the lens)
    m = new(pal)
    m.cy((0, 0, -0.18), 0.5, 0.55, 0.18, 'wallW', seg=8, caps=False)
    make('CeilLight', m, ao)
    g = new(pal)
    pts = [(math.cos(2 * math.pi * i / 8) * 0.46, math.sin(2 * math.pi * i / 8) * 0.46, -0.17) for i in range(8)]
    poly(g, pts, 'lightW', (0, 0, -1))
    make_glow('CeilLight_LED', g)
    # skylight strip [8, 2] (Blender X along its length): a glazed slot in the ceiling with white coffers either side
    m = new(pal)
    dq(m, -4.0, 4.0, -0.7, 0.7, -0.004, 'skyL')
    for k in range(-3, 4):
        m.bx(k * 1.0 - 0.04, k * 1.0 + 0.04, -0.7, 0.7, -0.35, -0.01, 'wallW', hull='none', cull='t')
    for s in (-1, 1):
        m.bx(-4.0, 4.0, s * 0.7 - 0.06, s * 0.7 + 0.06, -0.9, -0.01, 'wallW', hull='noside', cull='t')
    make('Sky_Strip', m, ao)
    # timber baffles [4, 4]: five slats hanging 0.5 - 1.1 m under the ceiling
    m = new(pal)
    for k in range(5):
        y = -1.6 + k * 0.8
        m.bx(-1.95, 1.95, y - 0.05, y + 0.05, -1.1, -0.5, 'wood', hull='noside')
        m.bx(-0.01, 0.01, y - 0.01, y + 0.01, -0.5, -0.01, 'steelD', hull='none', cull='tb')
    make('Baffle', m, ao)
    # hangar roof truss bay [24, 4] (along X): a truss at the bay's centre line, purlins, the roof deck seen from below
    for v in ('', 'L', 'S'):
        m = new(pal)
        dq(m, -12.0, 12.0, -2.0, 2.0, -0.003, 'corr')
        for k in range(-11, 12, 2):
            dq(m, k - 0.04, k + 0.04, -2.0, 2.0, -0.006, 'corrD')
        truss_x(m, 0.0, -11.95, 11.95, depth=1.8, n=8)
        for y in (-1.0, 1.0):
            m.bx(-11.95, 11.95, y - 0.05, y + 0.05, -0.18, -0.006, 'steel', hull='none', cull='t')
        if v == 'L':   # two high-bay lamps on drop rods
            for x in (-6.0, 6.0):
                m.bx(x - 0.015, x + 0.015, 0.985, 1.015, -2.0, -0.18, 'steelD', hull='none', cull='tb')
                m.cy((x, 1.0, -2.6), 0.48, 0.18, 0.6, 'steelD', seg=10, caps=False)
        if v == 'S':
            for x in (-7.0, 5.0):
                dq(m, x - 1.0, x + 1.0, -1.6, 1.6, -0.009, 'glassL')
        make('Roof_H' + v, m, ao)
        if v == 'L':
            g = new(pal)
            for x in (-6.0, 6.0):
                pts = [(x + math.cos(2 * math.pi * i / 10) * 0.42, 1.0 + math.sin(2 * math.pi * i / 10) * 0.42, -2.6) for i in range(10)]
                poly(g, pts, 'lightW', (0, 0, -1))
            make_glow('Roof_HL_LED', g)
    # the door header over the 36 m opening, in three [12, 1] pieces: a deep fascia, the door track below it;
    # the apron face (-Y) carries MERIDIAN AERO, the hangar face (+Y) the lining
    for i, key in enumerate(('A', 'B', 'C')):
        m = new(pal)
        xa, xb = (-5.95, 6.0) if key == 'A' else (-6.0, 5.95) if key == 'C' else (-6.0, 6.0)
        m.bx(xa, xb, -0.5, 0.5, -2.6, -0.0, 'corr', hull='noside', cull='t')
        fq(m, -6.0, 6.0, -0.503, -0.55, -0.0, 'navy')
        fq(m, -6.0, 6.0, -0.506, -0.62, -0.55, 'coral')
        bq(m, -6.0, 6.0, 0.503, -0.4, 0.0, 'steelD')
        m.bx(-6.0, 6.0, -0.2, 0.2, -2.85, -2.6, 'steelD', hull='noside', cull='')
        fq(m, -6.0, 6.0, -0.503, -2.6, -2.45, 'sun')
        if key == 'B':
            text_front(m, 'MERIDIAN AERO', 1.1, -0.506, 0.0, -1.95, 'navy', maxw=10.0)
        else:
            text_front(m, 'HANGAR' if key == 'A' else 'MRO', 0.9, -0.506, 0.0, -1.85, 'navy', maxw=6.0)
        make('Hdr_' + key, m, ao)


# ================================================================ decks, rails, stairs, escalators
def build_decks(pal, ao):
    # glass balustrade (modelled along Blender Y; the run placer links half modules): a steel cap rail, a base
    # channel and open glazing with glints
    def grail(m, y0, y1):
        m.bx(-0.04, 0.04, y0, y1, 1.05, 1.1, 'chrome', hull='noend', cull='')
        m.bx(-0.05, 0.05, y0, y1, 0.0, 0.12, 'steelD', hull='noend', cull='b')
        if y1 - y0 > 0.6:
            for s in (-1, 1):
                pts = [(s * 0.01, -0.2, 0.3), (s * 0.01, -0.05, 0.3), (s * 0.01, 0.2, 0.85), (s * 0.01, 0.05, 0.85)]
                poly(m, pts, 'glassL', (s, 0, 0))
    m = new(pal); grail(m, -0.5, 0.5); make('GRailFull', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.5, 1.1)])
    m = new(pal); grail(m, -0.5, -0.07); make('GRailHalf', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.0, 1.1)])
    m = new(pal)
    m.bx(-0.04, 0.04, -0.04, 0.04, 0.0, 1.12, 'chrome', cull='b')
    D.railpost_fit(m, 0.04, 1.12)
    make('GRailPost', m, ao)

    # scaffold guard rail (hangar work platforms): yellow top / mid rails and a toe board
    def yrail(m, y0, y1):
        m.bx(-0.03, 0.03, y0, y1, 1.02, 1.08, 'sun', hull='noend', cull='')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'sun', hull='noend', cull='')
        m.bx(-0.012, 0.012, y0, y1, 0.0, 0.14, 'sun', hull='none', cull='b')
    m = new(pal); yrail(m, -0.5, 0.5); make('YRailFull', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.5, 1.08)])
    m = new(pal); yrail(m, -0.5, -0.045); make('YRailHalf', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.0, 1.08)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.1, 'sun', cull='b')
    D.railpost_fit(m, 0.035, 1.1, capc='black')
    make('YRailPost', m, ao)
    # terminal deck column (white, round) and the hangar platform posts (yellow square tube, one per platform level)
    m = new(pal)
    m.cy((0, 0, 0), 0.22, 0.22, DECK - 0.4, 'wallW', seg=8, caps=False)
    m.cy((0, 0, 0), 0.26, 0.26, 0.12, 'steelD', seg=8, hull='none')
    D.deckcol_fit(m, DECK - 0.4)
    make('DeckCol', m, ao, cols=[cb(-0.22, -0.22, 0, 0.22, 0.22, DECK - 0.4)])
    for key, top in (('Post', DOCK - 0.4), ('Post2', 2 * DOCK - 0.4)):
        m = new(pal)
        m.bx(-0.06, 0.06, -0.06, 0.06, 0.0, top, 'sun', cull='')
        m.bx(-0.14, 0.14, -0.14, 0.14, 0.0, 0.02, 'steelD', hull='none', cull='b')
        make(key, m, ao, cols=[cb(-0.07, -0.07, 0, 0.07, 0.07, top)])

    # stairs: steps as walkable blocks (WCOL) rising toward Blender +Y (game north), rails both sides
    def stair(name, L, rise, n, landing, tread, stringer, rail, cols_side=True, glassy=False):
        m = new(pal)
        W = 1.6
        run = (L - landing) / n
        cols = []
        for k in range(n):
            y0 = -L / 2 + k * run
            y1 = y0 + run if k < n - 1 else L / 2
            top = (k + 1) * rise / n
            m.bx(-W / 2, W / 2, y0, y1, top - 0.08, top, tread, cull='')
            uq(m, -W / 2 + 0.03, W / 2 - 0.03, y0 + 0.005, y0 + 0.06, top + 0.003, 'sun' if not glassy else 'steelD')
            cols.append(cb(-W / 2, y0, 0.0, W / 2, y1, top, True))
        for sx in (-1, 1):
            a, b = sorted((sx * W / 2, sx * (W / 2 + 0.1)))
            prof = [(-L / 2, 0.0), (-L / 2 + 0.3, 0.0), (L / 2 - landing, rise - 0.4), (L / 2, rise - 0.4), (L / 2, rise), (L / 2 - landing - 0.1, rise), (-L / 2, 0.35)]
            m.prism(prof, a, b, [stringer])
            xr = sx * (W / 2 + 0.05)
            if glassy:
                pa = [(xr, -L / 2 + 0.3, 0.35), (xr, L / 2 - landing, rise + 0.05), (xr, L / 2 - landing, rise + 1.0), (xr, -L / 2 + 0.3, 1.25)]
                for s in (-1, 1):
                    q = [(x + s * 0.004, y, z) for (x, y, z) in pa]
                    poly(m, [q[0], q[1], (q[1][0], q[1][1], q[1][2] + 0.35), (q[0][0], q[0][1], q[0][2] + 0.35)], 'glassL', (s, 0, 0))
            m.bm_((xr, -L / 2 + 0.1, 1.05), (xr, L / 2 - landing, rise + 1.05), 0.06, rail)
            m.bm_((xr, L / 2 - landing, rise + 1.05), (xr, L / 2 - 0.05, rise + 1.05), 0.05, rail)
            if not glassy:
                for k in range(4):
                    t = (k + 0.5) / 4
                    yy = -L / 2 + 0.1 + t * (L - landing - 0.1)
                    zz = 0.35 + t * (rise - 0.35)
                    m.bx(xr - 0.015, xr + 0.015, yy - 0.015, yy + 0.015, zz, zz + 0.95, rail, hull='none', cull='b')
            if cols_side:
                for k in range(n + 1):
                    y0 = -L / 2 + k * run
                    y1 = L / 2 if k == n else y0 + run
                    top = min(rise, (k + 1) * rise / n) + 1.05
                    cols.append(cb(a, y0, 0.0, b, y1, top))
        return m, cols
    m, cols = stair('Stair', 9.0, DECK, 17, 0.5, 'stone', 'wallW', 'chrome', glassy=True)
    make('Stair', m, ao, cols=cols)
    m, cols = stair('Scaf', 6.0, DOCK, 11, 0.5, 'steel', 'sun', 'sun')
    make('Scaf', m, ao, cols=cols)
    # escalator [2, 9]: a steel truss with glass balustrades and black handrails, grooved steps (walkable), comb plates
    m = new(pal)
    W, L, n, land = 1.6, 9.0, 13, 1.2
    run = (L - 2 * land) / n
    cols = []
    m.bx(-W / 2 + 0.13, W / 2 - 0.13, -L / 2, -L / 2 + land, 0.0, 0.08, 'chrome', cull='b')
    cols.append(cb(-W / 2, -L / 2, 0.0, W / 2, -L / 2 + land, 0.08, True))
    for k in range(n):
        y0 = -L / 2 + land + k * run
        top = 0.08 + (k + 1) * (DECK - 0.08) / n
        m.bx(-W / 2 + 0.13, W / 2 - 0.13, y0, y0 + run, top - 0.1, top, 'steelD', cull='')
        uq(m, -W / 2 + 0.14, W / 2 - 0.14, y0 + 0.005, y0 + 0.05, top + 0.003, 'sun')
        cols.append(cb(-W / 2, y0, 0.0, W / 2, y0 + run, top, True))
    m.bx(-W / 2 + 0.13, W / 2 - 0.13, L / 2 - land, L / 2, DECK - 0.08, DECK, 'chrome', cull='')
    cols.append(cb(-W / 2, L / 2 - land, 0.0, W / 2, L / 2, DECK, True))
    for sx in (-1, 1):
        a, b = sorted((sx * (W / 2 - 0.12), sx * W / 2))
        prof = [(-L / 2 + land - 0.3, 0.08), (L / 2 - land, DECK - 0.5), (L / 2 - 0.02, DECK - 0.5), (L / 2 - 0.02, DECK + 0.12), (L / 2 - land, DECK + 0.12), (-L / 2 + land, 0.6), (-L / 2 + land - 0.3, 0.6)]
        m.prism(prof, a, b, ['steel'])
        xr = sx * (W / 2 - 0.06)
        pa = [(xr, -L / 2 + land - 0.4, 0.6), (xr, L / 2 - land + 0.2, DECK + 0.1), (xr, L / 2 - land + 0.2, DECK + 0.95), (xr, -L / 2 + land - 0.4, 1.45)]
        for s in (-1, 1):
            q = [(x + s * 0.004, y, z) for (x, y, z) in pa]
            poly(m, [q[0], q[1], (q[1][0], q[1][1], q[1][2] + 0.3), (q[0][0], q[0][1], q[0][2] + 0.3)], 'glassL', (s, 0, 0))
        m.bm_((xr, -L / 2 + land - 0.55, 1.05), (xr, L / 2 - land + 0.2, DECK + 1.05), 0.07, 'black')
        m.bm_((xr, L / 2 - land + 0.2, DECK + 1.05), (xr, L / 2 - 0.4, DECK + 1.05), 0.06, 'black')
        m.bx(xr - 0.02, xr + 0.02, -L / 2 + land - 0.6, -L / 2 + land - 0.4, 0.08, 1.05, 'steel', hull='none', cull='b')
        for k in range(n + 2):
            y0 = -L / 2 + land - 0.6 + k * (L - 2 * land + 0.8) / (n + 2)
            y1 = y0 + (L - 2 * land + 0.8) / (n + 2)
            top = min(DECK, max(0.0, (y1 - (-L / 2 + land)) / (L - 2 * land)) * DECK) + 1.1
            cols.append(cb(a, max(-L / 2, y0), 0.0, b, min(L / 2, y1), top))
    # underside panel (the truss seen from below)
    v = [(-W / 2, -L / 2 + land, 0.08), (W / 2, -L / 2 + land, 0.08), (W / 2, L / 2 - land, DECK - 0.5), (-W / 2, L / 2 - land, DECK - 0.5)]
    poly(m, v, 'steelD', (0, 0.4, -1))
    make('Escalator', m, ao, cols=cols)


# ================================================================ floor marks (layer 0.01)
def build_floors(pal, ao):
    m = new(pal)   # yellow line (1 m along Blender X; the run placer turns it to its cells)
    uq(m, -0.5, 0.5, -0.075, 0.075, 0.004, 'sun')
    make('F_Line', m, ao)
    m = new(pal)   # taxi lead-in line: yellow with black edges
    uq(m, -0.5, 0.5, -0.16, 0.16, 0.004, 'black')
    uq(m, -0.5, 0.5, -0.1, 0.1, 0.007, 'sun')
    make('F_Taxi', m, ao)
    m = new(pal)   # hatched keep-clear cell
    for k in range(3):
        x0 = -0.5 + k * 0.3
        poly(m, [(x0, -0.5, 0.004), (x0 + 0.12, -0.5, 0.004), (x0 + 0.22, 0.5, 0.004), (x0 + 0.1, 0.5, 0.004)], 'sun', (0, 0, 1))
    make('F_Hatch', m, ao)
    m = new(pal)   # red hatched no-go cell (equipment restraint area edge)
    for k in range(3):
        x0 = -0.5 + k * 0.3
        poly(m, [(x0, -0.5, 0.004), (x0 + 0.12, -0.5, 0.004), (x0 + 0.22, 0.5, 0.004), (x0 + 0.1, 0.5, 0.004)], 'red', (0, 0, 1))
    make('F_Red', m, ao)
    m = new(pal)   # terrazzo band (1 m along Blender X): dark stone between two brass strips
    uq(m, -0.5, 0.5, -0.4, 0.4, 0.004, 'stoneD')
    for y in (-0.33, 0.33):
        uq(m, -0.5, 0.5, y - 0.02, y + 0.02, 0.008, 'brass')
    make('F_Band', m, ao)
    m = new(pal)   # entrance mat [3, 2]
    uq(m, -1.45, 1.45, -0.95, 0.95, 0.004, 'black')
    for k in range(9):
        x = -1.3 + k * 0.325
        uq(m, x - 0.03, x + 0.03, -0.85, 0.85, 0.007, 'steelD')
    text_up(m, 'MERIDIAN', 0.36, 0.011, 0.0, 0.0, 'paper', maxw=2.4)
    make('F_Mat', m, ao)
    m = new(pal)   # lounge carpet [4, 4] with a border
    uq(m, -2.0, 2.0, -2.0, 2.0, 0.004, 'carpet')
    for k in range(-1, 2):
        uq(m, k * 1.333 - 0.02, k * 1.333 + 0.02, -2.0, 2.0, 0.007, 'fabD')
    make('F_Carpet', m, ao)
    m = new(pal)   # duty-free gloss tile [4, 4]
    uq(m, -2.0, 2.0, -2.0, 2.0, 0.004, 'wallW')
    for k in (-1.0, 0.0, 1.0):
        uq(m, k - 0.012, k + 0.012, -2.0, 2.0, 0.007, 'joint')
        uq(m, -2.0, 2.0, k - 0.012, k + 0.012, 0.010, 'joint')
    make('F_Tile', m, ao)
    m = new(pal)   # security hall vinyl [4, 4]: blue-grey with a lane stripe
    uq(m, -2.0, 2.0, -2.0, 2.0, 0.004, 'fab')
    uq(m, -2.0, 2.0, -0.04, 0.04, 0.007, 'skyL')
    make('F_Vinyl', m, ao)
    m = new(pal)   # hangar epoxy [4, 4]
    uq(m, -2.0, 2.0, -2.0, 2.0, 0.004, 'epoxy')
    uq(m, -2.0, 2.0, 1.985, 2.0, 0.007, 'corrD')
    uq(m, 1.985, 2.0, -2.0, 1.985, 0.007, 'corrD')
    make('F_Epoxy', m, ao)
    m = new(pal)   # aircraft stand marks: a red stop bar with white letters ("STOP")
    uq(m, -1.5, 1.5, -0.25, 0.25, 0.004, 'red')
    text_up(m, 'STOP', 0.28, 0.008, 0.0, 0.0, 'paper', maxw=1.2)
    make('F_Stop', m, ao)
    m = new(pal)   # stand number painted on the apron [3, 2]
    uq(m, -1.4, 1.4, -0.9, 0.9, 0.004, 'black')
    text_up(m, 'H2', 1.1, 0.008, 0.0, 0.0, 'sun', maxw=2.2)
    make('F_Stand', m, ao)
    # columns: the terminal's tree columns (a white trunk branching into four struts to the 14 m ceiling)
    m = new(pal)
    m.cy((0, 0, 0), 0.42, 0.42, 0.15, 'stoneD', seg=8)
    m.cy((0, 0, 0.15), 0.32, 0.36, 8.5, 'wallW', seg=8, caps=False)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        m.bm_((0.0, 0.0, 8.4), (math.cos(a) * 3.0, math.sin(a) * 3.0, H - 0.05), 0.26, 'wallW')
        m.cy((math.cos(a) * 3.0, math.sin(a) * 3.0, H - 0.12), 0.3, 0.36, 0.12, 'chrome', seg=6, hull='none')
    D.column_fit(m)
    make('Column', m, ao, cols=[cb(-0.38, -0.38, 0, 0.38, 0.38, 8.6)])
