"""kit-toyfactory structure: wall modules in two finishes (production hall: cream block, the TOPSY red / blue band,
white cladding, a ribbon of translucent clerestory panels; warehouse: grey block, a yellow bump rail, insulated panels
with the blue stripe) and their wall art (fire point, fire exit, electrical panel, safety board, the TOPSY TOYWORKS
logo over eight modules, toy banners, the carton chute through the wall, dock doors with a trailer backed in or shut),
corner posts, the gate, the trail walls, the exit hatch, the weapon stand, roof bays (open-web joists, girders,
high-bay lamps, skylights), hanging line / department / aisle boards, floor marks and steel columns (see tf_base.py)."""
import math
import random

from tf_base import *  # noqa: F401,F403
import tf_base as B
import tf_detail as D
from ms_struct import lamp, ext_point


# ================================================================ wall finishes (front face y = -0.5)
WIN0, WIN1 = 8.4, 10.2      # clerestory ribbon (production) / translucent band (warehouse) heights


def wall_prod(m, z0=0.0, x0=-0.5, x1=0.5, detail=True, plain=False):
    """production hall: skirting, cream block to 2.6 m, the red / blue band, white cladding with a rib a metre, the
    clerestory's sill and head flashings and mullion (its panes are the glow companion WinP), cladding to the roof"""
    if z0 < 0.14:
        fq(m, x0, x1, -0.503, 0.0, 0.14, 'concD')
    if z0 < 2.6:
        fq(m, x0, x1, -0.5, max(z0, 0.0), 2.6, 'wallC')
        if z0 < 1.3:
            fq(m, x0, x1, -0.503, 1.32, 1.34, 'joint')
    fq(m, x0, x1, -0.5, max(z0, 2.6), 3.0, 'brandR')
    fq(m, x0, x1, -0.5, max(z0, 3.0), 3.14, 'brandB')
    fq(m, x0, x1, -0.5, max(z0, 3.14), WIN0, 'clad')
    fq(m, x0, x1, -0.5, WIN1, H, 'clad')
    for k in range(int(round(x1 - x0))):
        x = x0 + 0.5 + k
        fq(m, x - 0.04, x + 0.04, -0.503, max(z0, 3.14), WIN0 - 0.12, 'cladD')
        fq(m, x - 0.02, x + 0.02, -0.512, WIN0, WIN1, 'steelD')
    fq(m, x0, x1, -0.503, WIN0 - 0.12, WIN0, 'steelD')
    fq(m, x0, x1, -0.503, WIN1, WIN1 + 0.1, 'steelD')
    if detail and z0 == 0.0 and x0 == -0.5 and x1 == 0.5:
        D.wall_detail(m, 'P', plain)


def win_prod(g, x0=-0.5, x1=0.5):
    fq(g, x0, x1, -0.506, WIN0, WIN1, 'glassL')
    for k in range(int(round(x1 - x0))):
        x = x0 + k + 0.5
        fq(g, x - 0.34, x - 0.26, -0.509, WIN0 + 0.2, WIN1 - 0.2, 'cool')


def wall_ware(m, z0=0.0, x0=-0.5, x1=0.5, rail=True, detail=True, plain=False):
    """warehouse: grey painted block to 2.4 m with a yellow bump rail, insulated panels, the blue / red stripe, a
    translucent daylight band (glow companion WinK)"""
    if z0 < 0.14:
        fq(m, x0, x1, -0.503, 0.0, 0.14, 'concD')
    if z0 < 2.4:
        fq(m, x0, x1, -0.5, max(z0, 0.0), 2.4, 'wallG')
        if z0 < 1.2:
            fq(m, x0, x1, -0.503, 1.19, 1.21, 'joint')
    fq(m, x0, x1, -0.5, max(z0, 2.4), 5.8, 'clad')
    fq(m, x0, x1, -0.5, max(z0, 5.8), 6.2, 'brandB')
    fq(m, x0, x1, -0.5, max(z0, 6.2), 6.34, 'brandR')
    fq(m, x0, x1, -0.5, max(z0, 6.34), WIN1 - 0.6, 'clad')
    fq(m, x0, x1, -0.5, WIN1 + 0.4, H, 'clad')
    if z0 < 4.2:
        fq(m, x0, x1, -0.503, 4.19, 4.21, 'cladD')
    fq(m, x0, x1, -0.503, WIN1 - 0.7, WIN1 - 0.6, 'steelD')
    fq(m, x0, x1, -0.503, WIN1 + 0.4, WIN1 + 0.5, 'steelD')
    if rail and z0 < 0.4:
        m.bx(x0, x1 - 0.1, -0.6, -0.5, 0.42, 0.62, 'hazY', cull='kb')
    if detail and z0 == 0.0 and x0 == -0.5 and x1 == 0.5:
        D.wall_detail(m, 'K', plain)


def win_ware(g, x0=-0.5, x1=0.5):
    fq(g, x0, x1, -0.506, WIN1 - 0.6, WIN1 + 0.4, 'glassL')


FIN = {'P': (wall_prod, win_prod, 'wallC'), 'K': (wall_ware, win_ware, 'wallG')}


def pilaster(m, S):
    """a steel I-column standing proud of the wall (every 6 m)"""
    c = 'machB' if S == 'P' else 'rackB'
    m.bx(-0.18, 0.18, -0.566, -0.5, 0.0, H, c, cull='btk', hull='none')
    m.bx(-0.03, 0.03, -0.76, -0.566, 0.0, H, c, cull='btkf', hull='none')
    m.bx(-0.18, 0.18, -0.82, -0.76, 0.0, H, c, cull='bt')
    m.bx(-0.24, 0.24, -0.86, -0.5, 0.0, 1.0, 'hazY', cull='bk')
    for z in (0.3, 0.7):
        fq(m, -0.24, 0.24, -0.863, z, z + 0.12, 'black')
    D.pilaster_detail(m)


def build_walls(pal, ao):
    for S in ('P', 'K'):
        fn, wfn, base = FIN[S]
        logo = S == 'P'
        m = new(pal); fn(m, plain=True); make('W' + S, m, ao)
        m = new(pal); fn(m); pilaster(m, S); make('W' + S + '_Col', m, ao)
        g = new(pal); wfn(g); make_glow('Win' + S, g)
        # corner post: the finish on all four sides (no windows)
        m = new(pal)
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, base, cull='bt')
        bands = (('brandR', 2.6, 3.0), ('brandB', 3.0, 3.14), ('clad', 3.14, H)) if S == 'P' else (('clad', 2.4, 5.8), ('brandB', 5.8, 6.2), ('brandR', 6.2, 6.34), ('clad', 6.34, H))
        for (c, z0, z1) in (('concD', 0.0, 0.14),) + bands:
            fq(m, -0.5, 0.5, -0.503, z0, z1, c)
            bq(m, -0.5, 0.5, 0.503, z0, z1, c)
            lq(m, -0.503, -0.5, 0.5, z0, z1, c)
            rq(m, 0.503, -0.5, 0.5, z0, z1, c)
        D.corner_guards(m)
        make('Corner' + S, m, ao)
        # fire point
        m = new(pal); fn(m); ext_point(m); D.fire_extras(m); make('W' + S + '_Fire', m, ao)
        # fire exit door: painted steel leaf in the wall plane, push bar, the running-man sign glows
        m = new(pal); fn(m, plain='door')
        m.bx(-0.48, 0.48, -0.56, -0.503, 0.0, 2.3, 'steelD', cull='kb')
        fq(m, -0.42, 0.42, -0.563, 0.02, 2.22, 'steel')
        m.bx(-0.36, 0.36, -0.64, -0.563, 1.0, 1.08, 'chrome')
        fq(m, -0.4, 0.4, -0.566, 1.5, 1.8, 'brandR')
        D.exit_detail(m)
        m.bx(-0.3, 0.3, -0.62, -0.503, 2.45, 2.75, 'paper', cull='k')
        make('W' + S + '_Exit', m, ao)
        # electrical panel with conduits up the wall
        m = new(pal); fn(m)
        m.bx(-0.35, 0.35, -0.68, -0.503, 1.1, 2.4, 'steel', cull='k')
        fq(m, -0.32, 0.32, -0.683, 1.14, 2.36, 'chrome')
        m.bx(-0.3, -0.02, -0.7, -0.683, 1.9, 2.2, 'hazY', cull='k')
        text_front(m, 'DANGER 480V', 0.06, -0.703, -0.16, 2.02, 'black', font='cond', maxw=0.26)
        for x in (-0.24, 0.0, 0.24):
            m.cy((x, -0.58, 2.4), 0.03, 0.03, WIN0 - 2.5, 'steelD', seg=6, caps=True, hull='none')
        D.panel_detail(m)
        make('W' + S + '_Panel', m, ao)
        # safety board: days without an accident, a notice sheet, the hard-hat rule
        m = new(pal); fn(m)
        m.bx(-0.46, 0.46, -0.54, -0.503, 1.1, 2.1, 'brandB', cull='k')
        fq(m, -0.42, 0.42, -0.543, 1.68, 2.06, 'pWhite')
        text_front(m, 'DAYS SAFE', 0.09, -0.546, 0.0, 1.9, 'brandB', font='cond', maxw=0.7)
        text_front(m, '128', 0.14, -0.546, 0.0, 1.72, 'brandR', maxw=0.5)
        for (x, z, w, hh, c) in ((-0.24, 1.18, 0.34, 0.42, 'paper'), (0.2, 1.18, 0.3, 0.2, 'hazY'), (0.2, 1.42, 0.3, 0.2, 'gD')):
            fq(m, x - w / 2, x + w / 2, -0.546, z, z + hh, c)
        make('W' + S + '_Board', m, ao)
        # the TOPSY TOYWORKS logo across eight modules high on the cladding (each module draws its slice)
        for k in range(8 if logo else 0):
            m = new(pal); fn(m)
            ib_text.draw(m, 'TOPSY TOYWORKS', 3.5 - k, -0.506, 4.6, 2.2, 'brandR', face='y-', font='display', maxw=7.5,
                         clip=(k - 4.0, k - 3.0), shadow='brandB', shadow_off=(0.05, -0.06))
            make('W' + S + '_Logo%d' % k, m, ao)
    # production banners: a long vertical banner with a toy picture and a slogan word
    for v, (word, c, pic) in enumerate((('PLAY', 'brandB', 'duck'), ('JOY', 'brandR', 'bear'))):
        m = new(pal); wall_prod(m)
        m.bx(-0.44, 0.44, -0.53, -0.503, 3.5, 8.1, c, cull='k')
        fq(m, -0.38, 0.38, -0.533, 6.3, 7.9, 'pWhite')
        if pic == 'duck':
            poly(m, [(-0.24 + 0.24 * math.cos(a / 8 * math.pi), -0.536, 6.78 + 0.2 * math.sin(a / 8 * math.pi)) for a in range(16)], 'gC', (0, -1, 0))
            poly(m, [(0.1 + 0.13 * math.cos(a / 6 * math.pi), -0.539, 7.2 + 0.13 * math.sin(a / 6 * math.pi)) for a in range(12)], 'gC', (0, -1, 0))
            fq(m, 0.2, 0.32, -0.542, 7.14, 7.2, 'pOrange')
        else:
            poly(m, [(0.24 * math.cos(a / 8 * math.pi), -0.536, 6.75 + 0.26 * math.sin(a / 8 * math.pi)) for a in range(16)], 'pBrown', (0, -1, 0))
            poly(m, [(0.17 * math.cos(a / 8 * math.pi), -0.539, 7.3 + 0.17 * math.sin(a / 8 * math.pi)) for a in range(16)], 'pBrown', (0, -1, 0))
            for sx in (-1, 1):
                poly(m, [(sx * 0.14 + 0.07 * math.cos(a / 4 * math.pi), -0.536, 7.48 + 0.07 * math.sin(a / 4 * math.pi)) for a in range(8)], 'pBrown', (0, -1, 0))
        for kk, ch in enumerate(word):
            text_front(m, ch, 0.5, -0.536, 0.0, 5.6 - kk * 0.62, 'pWhite')
        m.bm_((-0.48, -0.56, 8.15), (0.48, -0.56, 8.15), 0.05, 'steelD')
        make('WP_Ban' + 'AB'[v], m, ao)
    # the carton chute through the wall (the packing belt leaves the hall / the warehouse belt comes in): a framed
    # opening with a strip curtain at belt height, a TO / FROM board above
    for S, word in (('P', 'TO WAREHOUSE'), ('K', 'FROM PRODUCTION')):
        fn = FIN[S][0]
        m = new(pal); fn(m, 1.9)
        fq(m, -0.5, -0.42, -0.5, 0.0, 1.9, FIN[S][2])
        fq(m, 0.42, 0.5, -0.5, 0.0, 1.9, FIN[S][2])
        fq(m, -0.42, 0.42, -0.5, 0.0, 0.62, FIN[S][2])
        m.bx(-0.5, -0.42, -0.6, -0.5, 0.62, 1.9, 'hazY', cull='k', hull='noside')
        m.bx(0.42, 0.5, -0.6, -0.5, 0.62, 1.9, 'hazY', cull='k', hull='noside')
        m.bx(-0.5, 0.5, -0.6, -0.5, 1.9, 2.0, 'hazY', cull='k', hull='noside')
        bq(m, -0.42, 0.42, 0.3, 0.62, 1.9, 'black')
        for i in range(6):
            x = -0.36 + i * 0.144
            m.bx(x - 0.055, x + 0.055, -0.53, -0.51, 1.0, 1.88, 'rubber', hull='none', cull='')
        m.bx(-0.48, 0.48, -0.56, -0.503, 2.2, 2.6, 'brandB', cull='k')
        text_front(m, word, 0.16, -0.563, 0.0, 2.32, 'paper', maxw=0.86)
        make('W' + S + '_Chute', m, ao)
    for kind in ('Dock', 'DockShut'):
        build_dock(pal, ao, kind)


def ware_face_3(m, z_open):
    """a 3 m warehouse wall face with a door opening 2.8 x z_open in the middle (no bump rail across the opening)"""
    for (a, b) in ((-1.5, -1.4), (1.4, 1.5)):
        wall_ware(m, 0.0, a, b, rail=False)
    wall_ware(m, z_open, -1.4, 1.4, rail=False)


def build_dock(pal, ao, kind):
    rnd = random.Random(15 if kind == 'Dock' else 16)
    m = new(pal)
    Z = 3.2
    ware_face_3(m, Z)
    # shelter: black foam pads round the opening, a yellow-striped header, bumpers, a dock light, the bay number
    m.bx(-1.75, -1.4, -0.85, -0.5, 0.0, Z + 0.35, 'black', cull='k')
    m.bx(1.4, 1.75, -0.85, -0.5, 0.0, Z + 0.35, 'black', cull='k')
    m.bx(-1.4, 1.4, -0.85, -0.5, Z, Z + 0.35, 'black', cull='k')
    for k in range(7):
        x0 = -1.4 + k * 0.4
        fq(m, x0, x0 + 0.2, -0.853, Z + 0.05, Z + 0.3, 'hazY')
    for sx in (-1, 1):
        x = sx * 1.1
        m.bx(x - 0.13, x + 0.13, -0.66, -0.5, 0.15, 0.55, 'black', cull='k')
    m.bx(-1.72, -1.58, -0.93, -0.85, 2.0, 2.2, 'steelD', cull='k')
    m.bm_((-1.65, -0.93, 2.1), (-1.65, -1.2, 2.25), 0.04, 'steelD')
    m.cy((-1.65, -1.2, 2.2), 0.09, 0.12, 0.16, 'hazY', seg=8)
    m.bx(-0.5, 0.5, -0.53, -0.503, 4.0, 4.7, 'brandB', hull='none', cull='k')
    # leveler plate on the floor in front (diamond plate, a yellow lip)
    uq(m, -1.25, 1.25, -2.4, -0.5, 0.016, 'steel')
    for k in range(10):
        y = -2.35 + k * 0.17
        uq(m, -1.2, 1.2, y, y + 0.03, 0.019, 'chrome')
    uq(m, -1.25, 1.25, -0.66, -0.5, 0.022, 'hazY')
    if kind == 'Dock':
        # the trailer's rear frame fills the opening, its box goes back 4.3 m (beyond the wall); TOPSY on the doors
        y0, y1 = -0.5, 3.8
        m.bx(-1.4, -1.25, y0, y1, 0.0, Z, 'pWhite', cull='bt')
        m.bx(1.25, 1.4, y0, y1, 0.0, Z, 'pWhite', cull='bt')
        m.bx(-1.25, 1.25, y0, y1, Z - 0.22, Z, 'steelD', cull='t')
        m.bx(-1.25, 1.25, y0, y1, 0.0, 0.12, 'woodD', cull='b')
        rq(m, -1.247, y0 + 0.2, y1, 0.12, Z - 0.22, 'pWhite')
        lq(m, 1.247, y0 + 0.2, y1, 0.12, Z - 0.22, 'pWhite')
        fq(m, -1.25, 1.25, y1 - 0.003, 0.12, Z - 0.22, 'wallG')
        for k in range(1, 7):
            y = y0 + k * 0.6
            rq(m, -1.243, y - 0.02, y + 0.02, 0.12, Z - 0.22, 'chrome')
            lq(m, 1.243, y - 0.02, y + 0.02, 0.12, Z - 0.22, 'chrome')
        # the swung-open trailer doors against the shelter pads' sides, the TOPSY logo on them
        for sx in (-1, 1):
            a, b = sorted((sx * 1.76, sx * 1.8))
            m.bx(a, b, -1.95, -0.86, 0.15, Z - 0.1, 'pWhite', cull='')
            text_side(m, 'TOPSY', 0.22, sx * 1.803, -1.4, 1.6, 'brandR', 'x+' if sx > 0 else 'x-', maxw=0.95)
        # dock safety barrier across the opening: posts and two striped bars
        for sx in (-1, 1):
            m.bx(sx * 1.36 - 0.04, sx * 1.36 + 0.04, -0.62, -0.54, 0.0, 1.15, 'hazY', cull='b')
        for z in (0.5, 1.02):
            m.bx(-1.32, 1.32, -0.6, -0.56, z, z + 0.08, 'hazY', cull='lr')
            for k in range(7):
                x0 = -1.28 + k * 0.38
                fq(m, x0, x0 + 0.18, -0.603, z + 0.005, z + 0.075, 'black')
        # the load: printed toy cartons at the back, two pallets nearer, one half unloaded
        for k in range(2):
            x0 = -1.2 + k * 1.2
            hh = rnd.uniform(1.6, 2.6)
            carton(m, x0 + 0.01, x0 + 1.19, 2.7, 3.7, 0.12, 0.12 + hh * 0.5, rnd.choice(GOODS), art=rnd.choice(['gC', 'pPink', 'gA']))
            carton(m, x0 + 0.03, x0 + 1.17, 2.75, 3.7, 0.12 + hh * 0.5, 0.12 + hh, rnd.choice(GOODS + ['card']))
        pallet(m, -1.15, -0.05, 1.2, 2.3, 0.12)
        load(m, -1.12, -0.08, 1.23, 2.27, 0.26, 1.85, 'gB', face=(-1,))
        pallet(m, 0.05, 1.15, 1.2, 2.3, 0.12)
        carton(m, 0.1, 0.6, 1.25, 2.25, 0.26, 0.85, 'gA', art='gC')
        carton(m, 0.62, 1.1, 1.25, 2.25, 0.26, 0.7, 'gD', art='pWhite')
        cols = [cb(-1.75, -0.85, 0.0, -1.4, -0.5, Z + 0.35), cb(1.4, -0.85, 0.0, 1.75, -0.5, Z + 0.35),
                cb(-1.4, -0.64, 0.0, 1.4, -0.5, 1.15), cb(-1.8, -1.95, 0.0, -1.75, -0.85, Z), cb(1.75, -1.95, 0.0, 1.8, -0.85, Z)]
    else:
        # closed roll-up door: ribbed panel in the opening, a handle, the warning stencil
        fq(m, -1.4, 1.4, -0.45, 0.0, Z, 'chrome')
        for k in range(16):
            z = 0.1 + k * 0.2
            fq(m, -1.4, 1.4, -0.453, z, z + 0.03, 'steel')
        fq(m, -1.4, 1.4, -0.456, 0.0, 0.12, 'black')
        m.bx(-0.15, 0.15, -0.52, -0.456, 0.9, 0.98, 'steelD')
        fq(m, -0.7, 0.7, -0.459, 1.8, 2.15, 'hazY')
        text_front(m, 'KEEP CLEAR', 0.2, -0.462, 0.0, 1.88, 'black', font='display', maxw=1.3)
        rq(m, -1.4, -0.5, -0.45, 0.0, Z, 'steelD')
        lq(m, 1.4, -0.5, -0.45, 0.0, Z, 'steelD')
        dq(m, -1.4, 1.4, -0.5, -0.45, Z, 'steelD')
        cols = [cb(-1.75, -0.85, 0.0, -1.4, -0.5, Z + 0.35), cb(1.4, -0.85, 0.0, 1.75, -0.5, Z + 0.35), cb(-1.4, -0.5, 0.0, 1.4, -0.45, Z)]
    make('WK_' + kind, m, ao, cols=cols + [cb(-1.5, -0.5, 0.0, 1.5, 0.5, H)])
    if kind == 'Dock':
        g = new(pal); win_ware(g, -1.5, 1.5); make_glow('WinK3', g)


# ================================================================ gate, trail walls, hatch, stand
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.49, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'steelD', cull='b')
        for fy in (-1, 1):
            for k in range(6):
                z0 = 0.1 + k * 0.32
                (fq if fy < 0 else bq)(m, a + 0.05, b - 0.05, fy * 0.623, z0, z0 + 0.16, 'hazY')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.75, 'steelD')
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.75, H, 'clad', cull='t')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -2.48, 2.48, s * 0.453, 3.75, 4.05, 'brandR')
        (fq if s < 0 else bq)(m, -2.48, 2.48, s * 0.453, 4.05, 4.17, 'brandB')
    # boards: TOPSY TOYWORKS / a ring of toy colours (front), SAFETY FIRST (back)
    m.bx(-1.7, 1.7, -0.64, -0.45, 4.5, 5.5, 'brandB')
    text_front(m, 'TOPSY TOYWORKS', 0.44, -0.643, 0.0, 4.78, 'paper', maxw=3.1)
    for k, c in enumerate(('gA', 'gC', 'gD', 'gB', 'pPurple')):
        x = -1.2 + k * 0.6
        fq(m, x - 0.22, x + 0.22, -0.643, 4.58, 4.68, c)
    m.bx(-1.2, 1.2, 0.45, 0.62, 4.6, 5.3, 'hazY')
    text_back(m, 'SAFETY FIRST', 0.3, 0.623, 0.0, 4.82, 'black', maxw=2.1)
    m.bx(-0.55, 0.55, 0.45, 0.62, 3.95, 4.4, 'paper')
    D.gate_detail(m)
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    g = new(pal)
    bq(g, -0.45, 0.45, 0.623, 4.0, 4.35, 'exitG')
    text_back(g, 'EXIT', 0.24, 0.626, 0.0, 4.06, 'paper')
    make_glow('GateFrame_LED', g)
    # roll-up shutter: slats in the toy colours, a yellow-black bottom bar
    m = new(pal)
    Hs, n = 3.05, 12
    cols = ['gA', 'gC', 'gB', 'gD']
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.02), 'chrome' if i % 2 else cols[(i // 2) % 4], bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'black' if k % 2 else 'hazY', bevel=False)
    m.box((0, -0.06, 1.95), (2.2, 0.01, 0.42), 'brandR', bevel=False)
    text_front(m, 'STAFF ONLY', 0.26, -0.069, 0.0, 1.83, 'paper', maxw=2.0)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor walls between the hall and the warehouse (1 m along Blender Y, inner face +X)
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'wallC', hull='noend', cull='t')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.14, 'concD')
        rq(m, 0.253, -0.5, 0.5, 2.6, 3.0, 'brandR')
        rq(m, 0.253, -0.5, 0.5, 3.0, 3.14, 'brandB')
        rq(m, 0.253, -0.5, 0.5, 3.14, H, 'clad')
        m.bx(0.25, 0.33, -0.5, 0.5, 0.85, 1.0, 'hazY', hull='noend', cull='')
        m.bx(0.25, 0.31, -0.5, 0.5, 4.2, 4.26, 'steelD', hull='none', cull='')
        if name == 'TrailWall_B':
            m.bx(0.25, 0.4, -0.25, 0.25, 3.3, 3.55, 'grey')
            rq(m, 0.403, -0.22, 0.22, 3.32, 3.53, 'lightW')
        elif name == 'TrailWall_C':
            m.bx(0.253, 0.27, -0.32, 0.32, 1.35, 2.05, 'paper', cull='l')
            rq(m, 0.273, -0.28, 0.28, 1.88, 2.0, 'brandB')
            text_side(m, 'WASH HANDS', 0.08, 0.276, 0.0, 1.62, 'brandB', 'x+', font='cond', maxw=0.5)
            m.bx(0.253, 0.36, 0.36, 0.48, 1.0, 1.3, 'pWhite', cull='l')
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=20)
    ring(m, 0, 0, 0.103, 0.95, 1.12, 'hazY', seg=20)
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)
    # the weapon stand's base: a toy crate on a pallet
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    carton(m, -0.44, 0.44, -0.4, 0.4, 0.14, 0.52, 'gB', word='TOPSY', art='gC')
    make('Stand', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.52)])


# ================================================================ roof bays (hang from z = 0 = the roof deck)
def joist(m, y, x0, x1, depth=0.75):
    """open-web steel joist along X at y: top chord, bottom chord, a zigzag web (one panel a 1.33 m, painted both
    sides)"""
    m.bx(x0, x1, y - 0.06, y + 0.06, -0.1, -0.012, 'joist', hull='none', cull='t')
    m.bx(x0, x1, y - 0.045, y + 0.045, -depth, -depth + 0.07, 'joist', hull='none', cull='lr')
    n = 3
    pts = [(x0 + 0.05 + (x1 - x0 - 0.1) * k / n, -0.1 if k % 2 == 0 else -depth + 0.07) for k in range(n + 1)]
    for s in (-1, 1):
        L, R = [], []
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            dx, dz = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dz) or 1.0
            nx, nz = -dz / d * 0.03, dx / d * 0.03
            L.append((p[0] + nx, y + s * 0.012, p[1] + nz))
            R.append((p[0] - nx, y + s * 0.012, p[1] - nz))
        poly(m, L + R[::-1], 'joist', (0, s, 0))


def build_roof(pal, ao):
    """[4, 4] roof bays: a joist along the bay (local X) every 4 m; variants with a high-bay lamp, a skylight, a
    girder across the bay (Y) and a girder with a lamp"""
    for v in ('J', 'L', 'S', 'G', 'GL'):
        m = new(pal)
        g = new(pal) if v in ('L', 'S', 'GL') else None
        joist(m, 0.0, -2.0, 2.0)
        if 'G' in v:
            m.bx(-0.09, 0.09, -2.0, 2.0, -0.13, -0.012, 'joist', hull='none', cull='t')
            m.bx(-0.08, 0.08, -2.0, 2.0, -1.0, -0.88, 'joist', hull='none', cull='t')
            for s in (1,):
                pts = [(-1.94 + k * 0.485, -0.13 if k % 2 == 0 else -0.88) for k in range(9)]
                L, R = [], []
                for i, p in enumerate(pts):
                    a = pts[max(0, i - 1)]
                    b = pts[min(len(pts) - 1, i + 1)]
                    dy, dz = b[0] - a[0], b[1] - a[1]
                    d = math.hypot(dy, dz) or 1.0
                    ny, nz = -dz / d * 0.035, dy / d * 0.035
                    L.append((s * 0.02, p[0] + ny, p[1] + nz))
                    R.append((s * 0.02, p[0] - ny, p[1] - nz))
                poly(m, L + R[::-1], 'joist', (s, 0, 0))
        if 'L' in v:
            lamp(m, g, 1.0, 1.0, drop=1.2)
        if v == 'S':
            for (x0, x1, y0, y1) in ((-1.1, 1.1, 0.9, 1.1), (-1.1, 1.1, -1.1, -0.9), (-1.1, -0.9, -0.9, 0.9), (0.9, 1.1, -0.9, 0.9)):
                m.bx(x0, x1, y0, y1, -0.18, -0.012, 'pWhite', hull='none', cull='t')
            dq(m, -0.9, 0.9, -0.9, 0.9, -0.01, 'cool')
            dq(g, -0.88, 0.88, -0.88, 0.88, -0.014, 'cool')
            dq(g, -0.88, -0.2, 0.1, 0.88, -0.018, 'paper')
        make('Roof_' + v, m, ao)
        if g:
            make_glow('Roof_' + v + '_LED', g)


def board(pal, ao, name, word, c, sub=None, w=2.4, fg='paper', band='hazY', pic=None):
    """a hanging board (from the roof plane) with the word on both faces, two rods, a coloured band"""
    m = new(pal)
    z0, z1 = -6.1, -5.1
    m.bx(-w, w, -0.06, 0.06, z0, z1, c)
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -w, w, s * 0.063, z0 + 0.05, z0 + 0.13, band)
        xt = 0.35 if pic else 0.0
        (text_front if s < 0 else text_back)(m, word, 0.46 if not sub else 0.42, s * 0.063, xt * s, z0 + (0.42 if sub else 0.24), fg, maxw=2 * w - (1.3 if pic else 0.4))
        if sub:
            (text_front if s < 0 else text_back)(m, sub, 0.17, s * 0.063, xt * s, z0 + 0.18, band, font='cond', maxw=2 * w - 1.4)
        if pic:
            xp = -(w - 0.55) * s
            poly(m, [(xp + 0.36 * math.cos(a / 8 * math.pi), s * 0.066, z0 + 0.55 + 0.36 * math.sin(a / 8 * math.pi)) for a in range(16)], pic, (0, s, 0))
    for x in (-w + 0.4, w - 0.4):
        m.bx(x - 0.012, x + 0.012, -0.012, 0.012, z1, -0.012, 'steelD', hull='none', cull='t')
    D.sign_frame(m, w, 0.06, z0, z1, (-w + 0.4, w - 0.4))
    make(name, m, ao)


def build_signs(pal, ao):
    LINES = [('A', 'BLOCKS', 'gA'), ('B', 'DUCKS', 'gC'), ('C', 'ROBOTS', 'gB')]
    for k, words, c in LINES:
        board(pal, ao, 'Line_' + k, 'LINE ' + k, 'brandB', sub=words, w=2.4, pic=c)
    DEPTS = [('Moulding', 'MOULDING', 'machB', 'paper', 'hazY'), ('Paint', 'PAINT SHOP', 'pPurple', 'paper', 'hazY'),
             ('Packing', 'PACKING', 'brandR', 'paper', 'hazY'), ('Workshop', 'SHOWPIECES', 'hazY', 'black', 'brandR'),
             ('Loft', 'PELLET LOFT', 'machG', 'paper', 'hazY'), ('Shipping', 'SHIPPING', 'brandR', 'paper', 'hazY'),
             ('Pick', 'PICK + PACK', 'brandB', 'paper', 'hazY'), ('Plush', 'PLUSH', 'pPink', 'paper', 'brandB')]
    for key, word, c, fg, band in DEPTS:
        board(pal, ao, 'Dept_' + key, word, c, w=2.6, fg=fg, band=band)
    AISLES = [('1', 'BLOCKS', 'gA'), ('2', 'PLUSH', 'pPink'), ('3', 'DUCKS', 'gC'), ('4', 'ROBOTS', 'gB'), ('5', 'TOPS', 'gD'),
              ('6', 'HORSES', 'pOrange')]
    for num, words, c in AISLES:
        m = new(pal)
        z0, z1 = -5.4, -4.5
        m.bx(-1.3, 1.3, -0.05, 0.05, z0, z1, 'brandB')
        m.bx(-1.3, -0.55, -0.065, 0.065, z0, z1, c, hull='none', cull='tblr')
        for x in (-1.0, 1.0):
            m.bx(x - 0.012, x + 0.012, -0.012, 0.012, z1, -0.012, 'steelD', hull='none', cull='t')
        for s in (-1, 1):
            (text_front if s < 0 else text_back)(m, num, 0.58, s * 0.068, -0.92 * (1 if s < 0 else -1), z0 + 0.16, 'paper', maxw=0.62)
            (text_front if s < 0 else text_back)(m, words, 0.34, s * 0.053, 0.38 * (1 if s < 0 else -1), z0 + 0.25, 'paper', maxw=1.7)
        D.sign_frame(m, 1.3, 0.05, z0, z1, (-1.0, 1.0))
        make('Aisle_' + num, m, ao)


# ================================================================ floor marks (layer 0.01) and columns
def build_floors(pal, ao):
    m = new(pal)   # a yellow aisle line (1 m along Blender X: the run placer turns it to its line of cells)
    uq(m, -0.5, 0.5, -0.05, 0.05, 0.004, 'hazY')
    make('F_Line', m, ao)
    m = new(pal)   # pedestrian walkway: green with white chevrons
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.004, 'exitG')
    for k in range(2):
        y0 = -0.4 + k * 0.5
        poly(m, [(-0.3, y0, 0.007), (0.0, y0 + 0.25, 0.007), (0.3, y0, 0.007), (0.3, y0 + 0.12, 0.007), (0.0, y0 + 0.37, 0.007), (-0.3, y0 + 0.12, 0.007)], 'paper', (0, 0, 1))
    make('F_Walk', m, ao)
    m = new(pal)   # hatched keep-clear cell
    for k in range(3):
        x0 = -0.5 + k * 0.3
        poly(m, [(x0, -0.5, 0.004), (x0 + 0.12, -0.5, 0.004), (x0 + 0.22, 0.5, 0.004), (x0 + 0.1, 0.5, 0.004)], 'hazY', (0, 0, 1))
    make('F_Hatch', m, ao)
    m = new(pal)   # a play-mat square of the showpiece workshop (red / blue / yellow / green quarters)
    for (x0, x1, y0, y1, c) in ((-0.5, 0.0, -0.5, 0.0, 'gA'), (0.0, 0.5, -0.5, 0.0, 'gB'), (-0.5, 0.0, 0.0, 0.5, 'gC'), (0.0, 0.5, 0.0, 0.5, 'gD')):
        uq(m, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, 0.006, c)
    make('F_Mat', m, ao)
    # steel column: a W-section to the roof with a yellow concrete-filled guard round its foot
    m = new(pal)
    m.bx(-0.16, 0.16, -0.02, 0.02, 0.0, H, 'machB', cull='bt')
    m.bx(-0.16, 0.16, -0.16, -0.13, 0.0, H, 'machB', cull='bt')
    m.bx(-0.16, 0.16, 0.13, 0.16, 0.0, H, 'machB', cull='bt')
    m.cy((0, 0, 0), 0.34, 0.34, 1.2, 'hazY', seg=12)
    for z in (0.35, 0.8):
        m.cy((0, 0, z), 0.343, 0.343, 0.12, 'black', seg=12, caps=False, hull='none')
    D.column_detail(m)
    make('Column', m, ao, cols=[cb(-0.35, -0.35, 0, 0.35, 0.35, 1.2), cb(-0.17, -0.17, 1.2, 0.17, 0.17, H)])


def build_struct(pal, ao):
    build_walls(pal, ao)
    build_gate(pal, ao)
    build_roof(pal, ao)
    build_signs(pal, ao)
    build_floors(pal, ao)
