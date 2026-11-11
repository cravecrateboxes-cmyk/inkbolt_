"""kit-megastore structure: wall modules (sales floor: painted block with the BULKBARN band and corrugated cladding;
stockroom: bare block with a steel bump rail) and their wall art (fire point, sprinkler riser, fire exit door, banner,
reach-in cooler doors, walk-in cooler door, TV wall, dock doors with a trailer backed in, a closed dock door, a notice
board), corner posts, the gate (EMPLOYEES ONLY doors with a roll-up shutter), the back-corridor walls with their drop
ceiling, the exit hatch, roof bays (open-web joists, girders, high-bay lamps, skylights), hanging aisle and department
signs, floor marks and steel columns (see ms_base.py for conventions)."""
import math
import random

from ms_base import *  # noqa: F401,F403
import ms_base as B


# ================================================================ walls
def wall_sales(m):
    """front face (y = -0.5): block wall to 3.6 m, the BULKBARN blue / red band, corrugated cladding above"""
    fq(m, -0.5, 0.5, -0.5, 0.0, 3.6, 'wallW')
    fq(m, -0.5, 0.5, -0.503, 0.0, 0.14, 'concD')
    for k in range(1, 5):
        z = 0.14 + k * 0.8
        fq(m, -0.5, 0.5, -0.503, z - 0.008, z + 0.008, 'joint')
    fq(m, -0.5, 0.5, -0.5, 3.6, 4.15, 'brand')
    fq(m, -0.5, 0.5, -0.503, 4.0, 4.06, 'paper')
    fq(m, -0.5, 0.5, -0.5, 4.15, 4.27, 'brandR')
    fq(m, -0.5, 0.5, -0.5, 4.27, H, 'corr')
    for k in range(2):
        x = -0.25 + k * 0.5
        fq(m, x - 0.04, x + 0.04, -0.503, 4.27, H, 'corrD')


def wall_upper(m, z0):
    """the sales wall face from z0 up (a module with something cut into its lower part)"""
    if z0 < 3.6:
        fq(m, -0.5, 0.5, -0.5, z0, 3.6, 'wallW')
    fq(m, -0.5, 0.5, -0.5, 3.6, 4.15, 'brand')
    fq(m, -0.5, 0.5, -0.503, 4.0, 4.06, 'paper')
    fq(m, -0.5, 0.5, -0.5, 4.15, 4.27, 'brandR')
    fq(m, -0.5, 0.5, -0.5, 4.27, H, 'corr')
    for k in range(4):
        x = -0.5 + 0.125 + k * 0.25
        fq(m, x - 0.03, x + 0.03, -0.503, 4.27, H, 'corrD')


def wall_stock(m):
    """stockroom: grey-painted block to 2.4 m, bare block to 4.8 m, cladding above; a yellow steel bump rail"""
    fq(m, -0.5, 0.5, -0.5, 0.0, 2.4, 'wallL')
    fq(m, -0.5, 0.5, -0.5, 2.4, 4.8, 'wallW')
    for k in range(1, 12):
        z = k * 0.4
        if k != 6:
            fq(m, -0.5, 0.5, -0.503, z - 0.008, z + 0.008, 'joint')
    fq(m, -0.5, 0.5, -0.503, 2.38, 2.44, 'steelD')
    fq(m, -0.5, 0.5, -0.5, 4.8, H, 'corr')
    for k in range(4):
        x = -0.5 + 0.125 + k * 0.25
        fq(m, x - 0.03, x + 0.03, -0.503, 4.8, H, 'corrD')
    # bump rail on stand-offs (pallets and forklifts hit the rail, not the wall)
    m.prism([(-0.53, 0.42), (-0.6, 0.42), (-0.6, 0.6), (-0.53, 0.63)], -0.5, 0.5, ['hazY'], hull='noside', skip=(0,))
    for x in (-0.25, 0.25):
        m.bx(x - 0.04, x + 0.04, -0.53, -0.503, 0.47, 0.57, 'steelD', cull='k')


def ext_point(m, x=0.0):
    """fire point: red extinguisher on a bracket, a pull station and a sign above"""
    m.bx(x - 0.13, x + 0.13, -0.56, -0.503, 1.55, 1.95, 'brandR', cull='k')
    text_front(m, 'FIRE', 0.1, -0.563, x, 1.68, 'paper', font='display')
    m.cy((x, -0.62, 0.5), 0.1, 0.1, 0.55, 'brandR', seg=8)
    m.cy((x, -0.62, 1.05), 0.035, 0.035, 0.08, 'black', seg=6, hull='none')
    m.bx(x - 0.12, x + 0.12, -0.53, -0.503, 0.6, 0.9, 'steelD', cull='k')
    m.bx(x + 0.22, x + 0.34, -0.55, -0.503, 1.1, 1.26, 'brandR', cull='k')


def build_walls(pal, ao):
    for S, fn in (('S', wall_sales), ('K', wall_stock)):
        m = new(pal); fn(m); make('W' + S, m, ao)
        # corner post: the finish on all four sides
        m = new(pal)
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'wallW' if S == 'S' else 'wallL', cull='bt')
        bands = (('brand', 3.6, 4.15), ('brandR', 4.15, 4.27), ('corr', 4.27, H)) if S == 'S' else (('wallW', 2.4, 4.8), ('corr', 4.8, H))
        for (c, z0, z1) in (('concD', 0.0, 0.14),) + bands:
            fq(m, -0.5, 0.5, -0.503, z0, z1, c)
            bq(m, -0.5, 0.5, 0.503, z0, z1, c)
            lq(m, -0.503, -0.5, 0.5, z0, z1, c)
            rq(m, 0.503, -0.5, 0.5, z0, z1, c)
        make('Corner' + S, m, ao)
        # fire point
        m = new(pal); fn(m); ext_point(m); make('W' + S + '_Fire', m, ao)
    # sales floor art --------------------------------------------------------------
    # sprinkler riser with the fire-department valve and a red sign
    m = new(pal); wall_sales(m)
    m.cy((0.0, -0.62, 0.0), 0.07, 0.07, H, 'brandR', seg=8, caps=False)
    m.cy((0.0, -0.62, 1.2), 0.11, 0.11, 0.22, 'brandR', seg=8)
    m.bm_((0.0, -0.62, 1.31), (0.0, -0.82, 1.31), 0.07, 'chrome')
    m.bx(-0.2, 0.2, -0.53, -0.503, 2.0, 2.3, 'brandR', cull='k')
    text_front(m, 'RISER', 0.12, -0.533, 0.0, 2.09, 'paper')
    make('WS_Riser', m, ao)
    # fire exit door (painted steel door in the wall plane, push bar, running-exit sign that glows)
    m = new(pal); wall_sales(m)
    m.bx(-0.48, 0.48, -0.56, -0.503, 0.0, 2.3, 'steelD', cull='kb')
    fq(m, -0.42, 0.42, -0.563, 0.02, 2.22, 'steel')
    m.bx(-0.36, 0.36, -0.64, -0.563, 1.0, 1.08, 'chrome')
    fq(m, -0.4, 0.4, -0.566, 1.5, 1.8, 'brandR')
    text_front(m, 'ALARM WILL SOUND', 0.07, -0.569, 0.0, 1.6, 'paper', font='cond', maxw=0.72)
    m.bx(-0.3, 0.3, -0.62, -0.503, 2.45, 2.75, 'paper', cull='k')
    make('WS_Exit', m, ao)
    m = new(pal)
    fq(m, -0.27, 0.27, -0.623, 2.48, 2.72, 'exitG')
    text_front(m, 'EXIT', 0.16, -0.626, 0.0, 2.52, 'paper')
    make_glow('WS_Exit_LED', m)
    # banner (BULKBARN savings), two variants
    for v, (word, c) in enumerate((('BULK', 'brand'), ('SAVE', 'brandR'))):
        m = new(pal); wall_sales(m)
        m.bx(-0.42, 0.42, -0.53, -0.503, 4.6, 8.6, c, cull='k')
        fq(m, -0.36, 0.36, -0.533, 4.8, 5.2, 'hazY')
        for k, ch in enumerate(word):
            text_front(m, ch, 0.62, -0.533, 0.0, 7.75 - k * 0.72, 'paper')
        m.bm_((-0.46, -0.56, 8.65), (0.46, -0.56, 8.65), 0.05, 'steelD')
        make('WS_Banner' + 'AB'[v], m, ao)
    # the BULKBARN logo across eight modules high on the cladding (each module draws its slice of the word)
    for k in range(8):
        m = new(pal); wall_sales(m)
        ib_text.draw(m, 'BULKBARN', 3.5 - k, -0.506, 5.3, 2.8, 'brandR', face='y-', font='display', maxw=7.4,
                     clip=(k - 4.0, k - 3.0), shadow='brand', shadow_off=(0.05, -0.05))
        make('WS_Logo%d' % k, m, ao)
    # reach-in cooler doors: a glass door into a lit case (0.85 m deep, inside the wall cell) with stocked shelves
    for v, kind in enumerate(('Dairy', 'Drinks')):
        rnd = random.Random(40 + v)
        m = new(pal)
        wall_upper(m, 2.85)
        # case surround: kick base and header (the case is cut into the wall face below 2.85 m)
        m.bx(-0.5, 0.5, -0.58, -0.5, 0.0, 0.25, 'black', hull='noside', cull='bk')
        m.bx(-0.5, 0.5, -0.58, -0.5, 2.25, 2.85, 'pWhite', hull='noside', cull='k')
        fq(m, -0.5, 0.5, -0.583, 2.45, 2.62, 'brand')
        text_front(m, 'DAIRY' if v == 0 else 'DRINKS', 0.12, -0.586, 0.0, 2.48, 'paper', maxw=0.8)
        # case interior seen through the door: back liner, side liners, floor, ceiling, shelves
        fq(m, -0.46, 0.46, 0.35, 0.25, 2.25, 'cool')
        rq(m, -0.46, -0.5, 0.35, 0.25, 2.25, 'chrome')
        lq(m, 0.46, -0.5, 0.35, 0.25, 2.25, 'chrome')
        uq(m, -0.46, 0.46, -0.5, 0.35, 0.25, 'grey')
        dq(m, -0.46, 0.46, -0.5, 0.35, 2.25, 'cool')
        for z in (0.32, 0.92, 1.52):
            m.bx(-0.455, 0.455, -0.45, 0.33, z - 0.02, z, 'chrome', hull='none', cull='')
            # stock: jugs / cartons (dairy) or bottles and cans (drinks) -- two facings a shelf, painted labels
            cols = ['pWhite', 'gB', 'pWhite', 'pSky'] if v == 0 else GOODS + ['pOrange']
            xs = (-0.43, rnd.uniform(-0.1, 0.1), 0.43)
            for k in range(2):
                a, b = xs[k] + 0.006, xs[k + 1] - 0.006
                hgt = rnd.uniform(0.3, 0.46)
                c = rnd.choice(cols)
                m.bx(a, b, -0.4, 0.28, z + 0.004, z + 0.004 + hgt, c, hull='none', cull='bk')
                n = int((b - a) / (0.12 if v == 0 else 0.09))
                lab = 'paper' if c != 'pWhite' else rnd.choice(['gB', 'gA'])
                for j in range(n):
                    xa = a + (b - a) * (j + 0.2) / n
                    xb = a + (b - a) * (j + 0.8) / n
                    fq(m, xa, xb, -0.403, z + hgt * 0.35, z + hgt * 0.62, lab)
        # door: jambs, rails, glints on the glass, handle
        m.bx(-0.5, -0.46, -0.6, -0.5, 0.25, 2.25, 'black', cull='bt')
        m.bx(0.46, 0.5, -0.6, -0.5, 0.25, 2.25, 'black', cull='bt')
        m.bx(-0.46, 0.46, -0.6, -0.56, 0.25, 0.32, 'black', cull='')
        m.bx(-0.46, 0.46, -0.6, -0.56, 2.18, 2.25, 'black', cull='')
        for (x0, z0) in ((-0.32, 1.45), (0.0, 0.55)):
            poly(m, [(x0, -0.585, z0), (x0 + 0.08, -0.585, z0), (x0 + 0.26, -0.585, z0 + 0.3), (x0 + 0.18, -0.585, z0 + 0.3)], 'glassL', (0, -1, 0))
        m.bx(0.34, 0.38, -0.66, -0.6, 0.8, 1.7, 'chrome')
        make('WC_' + kind, m, ao)
    # the cases' light: a strip down each door jamb inside the case (unlit glow)
    m = new(pal)
    rq(m, -0.457, -0.48, 0.3, 0.35, 2.15, 'cool')
    lq(m, 0.457, -0.48, 0.3, 0.35, 2.15, 'cool')
    dq(m, -0.4, 0.4, -0.45, 0.3, 2.246, 'paper')
    make_glow('WC_Glow', m)
    # walk-in cooler door: insulated stainless leaf, strip curtain behind a porthole, a thermometer sign
    m = new(pal); wall_sales(m)
    m.bx(-0.5, 0.5, -0.6, -0.5, 0.0, 2.6, 'chrome', hull='noside', cull='bk')
    fq(m, -0.4, 0.4, -0.603, 0.06, 2.3, 'rackG')
    m.bx(-0.42, 0.42, -0.62, -0.603, 0.06, 0.4, 'steel', cull='k')
    fq(m, -0.16, 0.16, -0.606, 1.45, 1.8, 'glass')
    for k in range(4):
        fq(m, -0.15 + k * 0.08, -0.12 + k * 0.08, -0.609, 1.47, 1.78, 'glassL')
    m.bx(-0.36, -0.3, -0.7, -0.603, 1.0, 1.25, 'steelD')
    m.bx(0.3, 0.38, -0.66, -0.603, 1.2, 1.4, 'black')
    m.bx(-0.3, 0.3, -0.63, -0.6, 2.32, 2.55, 'brand', cull='k')
    text_front(m, 'WALK-IN 2 C', 0.11, -0.633, 0.0, 2.38, 'paper', maxw=0.56)
    make('WC_WalkIn', m, ao)
    # TV wall: slatwall with TVs of mixed sizes (two variants), screens glow (companion)
    for v in range(2):
        rnd = random.Random(70 + v)
        m = new(pal); wall_sales(m)
        m.bx(-0.5, 0.5, -0.54, -0.5, 0.0, 3.55, 'pBlack', hull='noside', cull='k')
        for z in (0.6, 1.2, 1.8, 2.4, 3.0):
            fq(m, -0.5, 0.5, -0.543, z, z + 0.012, 'grey')
        g = new(pal)
        rows = ((0.75, 0.55), (1.45, 0.62), (2.25, 0.72)) if v == 0 else ((0.7, 0.66), (1.55, 0.5), (2.2, 0.82))
        for (z0, hgt) in rows:
            w = min(0.94, hgt * 16 / 9 * rnd.uniform(0.55, 0.7))
            x0 = rnd.uniform(-0.47, 0.47 - w)
            m.bx(x0, x0 + w, -0.6, -0.543, z0, z0 + hgt, 'black', cull='k')
            fq(g, x0 + 0.02, x0 + w - 0.02, -0.603, z0 + 0.02, z0 + hgt - 0.02, rnd.choice(['scrB', 'scrC', 'scrO', 'screen']))
            # a picture: horizon band and a sun disc (sports, nature, cartoons)
            fq(g, x0 + 0.02, x0 + w - 0.02, -0.606, z0 + 0.02, z0 + hgt * 0.4, rnd.choice(['leaf', 'scrB', 'gC', 'pPurple']))
            disc_c = rnd.choice(['paper', 'gC', 'pPink'])
            poly(g, [(x0 + w * 0.7 + math.cos(a / 6 * math.pi) * hgt * 0.12, -0.609, z0 + hgt * 0.68 + math.sin(a / 6 * math.pi) * hgt * 0.12) for a in range(12)], disc_c, (0, -1, 0))
            m.bx(x0 + w * 0.4, x0 + w * 0.6, -0.56, -0.543, z0 - 0.06, z0, 'grey', cull='k')
        make('WE_TV' + 'AB'[v], m, ao)
        make_glow('WE_TV' + 'AB'[v] + '_LED', g)
    # stockroom art ----------------------------------------------------------------
    # notice board + time clock
    m = new(pal); wall_stock(m)
    m.bx(-0.45, 0.45, -0.54, -0.503, 1.2, 2.0, 'woodD', cull='k')
    fq(m, -0.41, 0.41, -0.543, 1.24, 1.96, 'cardL')
    rnd = random.Random(9)
    for (x, z, w, hh, c) in ((-0.3, 1.7, 0.2, 0.22, 'paper'), (-0.02, 1.62, 0.24, 0.3, 'pWhite'), (0.24, 1.72, 0.14, 0.18, 'gC'), (-0.25, 1.3, 0.26, 0.3, 'brand'), (0.15, 1.3, 0.22, 0.26, 'paper')):
        fq(m, x - w / 2, x + w / 2, -0.546, z, z + hh, c)
    text_front(m, 'SAFETY FIRST', 0.08, -0.549, 0.0, 1.88, 'brandR', font='cond', maxw=0.7)
    text_front(m, '312 DAYS', 0.07, -0.549, -0.25, 1.36, 'paper', font='cond', maxw=0.24)
    make('WK_Board', m, ao)
    # electrical panel with conduits
    m = new(pal); wall_stock(m)
    m.bx(-0.35, 0.35, -0.68, -0.503, 1.1, 2.4, 'steel', cull='k')
    fq(m, -0.32, 0.32, -0.683, 1.14, 2.36, 'rackG')
    m.bx(-0.3, -0.02, -0.7, -0.683, 1.9, 2.2, 'hazY', cull='k')
    text_front(m, 'DANGER 480V', 0.06, -0.703, -0.16, 2.02, 'black', font='cond', maxw=0.26)
    for x in (-0.24, 0.0, 0.24):
        m.cy((x, -0.58, 2.4), 0.03, 0.03, H - 2.4, 'steelD', seg=6, caps=False, hull='none')
    make('WK_Panel', m, ao)
    # dock doors (centre cell of a 3-cell bay; the theme leaves the side cells empty): 3 m door, dock shelter pads,
    # bumpers, a light and a leveler plate on the floor in front; behind: a trailer backed in, or a closed door
    for kind in ('Dock', 'DockShut'):
        build_dock(pal, ao, kind)


def stock_face_3(m, z_open):
    """a 3 m stockroom wall face with a door opening 2.8 x z_open in the middle"""
    for (a, b) in ((-1.5, -1.4), (1.4, 1.5)):
        fq(m, a, b, -0.5, 0.0, 4.8, 'wallL')
    fq(m, -1.4, 1.4, -0.5, z_open, 4.8, 'wallL')
    fq(m, -1.5, 1.5, -0.5, 4.8, H, 'corr')
    for k in range(12):
        x = -1.5 + 0.125 + k * 0.25
        fq(m, x - 0.03, x + 0.03, -0.503, 4.8, H, 'corrD')


def build_dock(pal, ao, kind):
    rnd = random.Random(5 if kind == 'Dock' else 6)
    m = new(pal)
    Z = 3.2
    stock_face_3(m, Z)
    # shelter: black foam pads round the opening, a yellow-striped header
    m.bx(-1.75, -1.4, -0.85, -0.5, 0.0, Z + 0.35, 'black', cull='k')
    m.bx(1.4, 1.75, -0.85, -0.5, 0.0, Z + 0.35, 'black', cull='k')
    m.bx(-1.4, 1.4, -0.85, -0.5, Z, Z + 0.35, 'black', cull='k')
    for k in range(7):
        x0 = -1.4 + k * 0.4
        fq(m, x0, x0 + 0.2, -0.853, Z + 0.05, Z + 0.3, 'hazY')
    for sx in (-1, 1):   # bumpers
        x = sx * 1.1
        m.bx(x - 0.13, x + 0.13, -0.66, -0.5, 0.15, 0.55, 'black', cull='k')
    # dock light on a swing arm, the bay number
    m.bx(-1.72, -1.58, -0.93, -0.85, 2.0, 2.2, 'steelD', cull='k')
    m.bm_((-1.65, -0.93, 2.1), (-1.65, -1.2, 2.25), 0.04, 'steelD')
    m.cy((-1.65, -1.2, 2.2), 0.09, 0.12, 0.16, 'hazY', seg=8)
    m.bx(-0.45, 0.45, -0.53, -0.5, 4.0, 4.6, 'brand', hull='none', cull='k')
    # leveler plate on the floor in front (diamond plate, yellow lip)
    uq(m, -1.25, 1.25, -2.4, -0.5, 0.016, 'steel')
    for k in range(10):
        y = -2.35 + k * 0.17
        uq(m, -1.2, 1.2, y, y + 0.03, 0.019, 'rackG')
    uq(m, -1.25, 1.25, -0.66, -0.5, 0.022, 'hazY')
    if kind == 'Dock':
        # the opening: the trailer's rear frame fills it, the box goes back 4.2 m (beyond the wall: nobody sees round it)
        y0, y1 = -0.5, 3.8
        m.bx(-1.4, -1.25, y0, y1, 0.0, Z, 'steelD', cull='bt')
        m.bx(1.25, 1.4, y0, y1, 0.0, Z, 'steelD', cull='bt')
        m.bx(-1.25, 1.25, y0, y1, Z - 0.22, Z, 'steelD', cull='t')
        m.bx(-1.25, 1.25, y0, y1, 0.0, 0.12, 'woodD', cull='b')        # trailer floor at the dock floor height
        rq(m, -1.247, y0 + 0.2, y1, 0.12, Z - 0.22, 'pWhite')
        lq(m, 1.247, y0 + 0.2, y1, 0.12, Z - 0.22, 'pWhite')
        fq(m, -1.25, 1.25, y1 - 0.003, 0.12, Z - 0.22, 'wallL')
        for k in range(1, 7):
            y = y0 + k * 0.6
            rq(m, -1.243, y - 0.02, y + 0.02, 0.12, Z - 0.22, 'rackG')
            lq(m, 1.243, y - 0.02, y + 0.02, 0.12, Z - 0.22, 'rackG')
        # dock safety barrier across the opening (nobody walks off the dock edge): posts and two striped bars
        for sx in (-1, 1):
            m.bx(sx * 1.36 - 0.04, sx * 1.36 + 0.04, -0.62, -0.54, 0.0, 1.15, 'hazY', cull='b')
        for z in (0.5, 1.02):
            m.bx(-1.32, 1.32, -0.6, -0.56, z, z + 0.08, 'hazY', cull='lr')
            for k in range(7):
                x0 = -1.28 + k * 0.38
                fq(m, x0, x0 + 0.18, -0.603, z + 0.005, z + 0.075, 'black')
        # load: a wall of mixed cartons at the back, two wrapped pallets nearer, one half unloaded
        stack(m, rnd, -1.2, 1.2, 2.6, 3.7, 0.12, 2.8, ['card', 'cardD', 'cardL', 'gA', 'gB'], face=-1, nx=5, maxh=0.7)
        pallet(m, -1.15, -0.05, 1.2, 2.3, 0.12)
        load(m, -1.12, -0.08, 1.23, 2.27, 0.26, 1.85, 'gC', face=(-1,))
        pallet(m, 0.05, 1.15, 1.2, 2.3, 0.12)
        load(m, 0.08, 1.12, 1.23, 2.27, 0.26, 1.2, 'card', face=(-1,))
    else:
        # closed roll-up door: ribbed panel in the opening, handle, warning stencil
        fq(m, -1.4, 1.4, -0.45, 0.0, Z, 'rackG')
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
    make('WK_' + kind, m, ao)


# ================================================================ gate, corridor, hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.49, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'steelD', cull='b')
        for fy in (-1, 1):   # hazard chevrons on the jamb faces (forklift traffic)
            for k in range(6):
                z0 = 0.1 + k * 0.32
                (fq if fy < 0 else bq)(m, a + 0.05, b - 0.05, fy * 0.623, z0, z0 + 0.16, 'hazY')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.75, 'steelD')
    # wall over the doors: the store's finishes on the sales side (front) and the stockroom's at the back
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.75, H, 'wallW', cull='t')
    fq(m, -2.48, 2.48, -0.453, 3.75, 4.15, 'brand')
    fq(m, -2.48, 2.48, -0.453, 4.15, 4.27, 'brandR')
    fq(m, -2.48, 2.48, -0.453, 4.27, H, 'corr')
    bq(m, -2.48, 2.48, 0.453, 4.8, H, 'corr')
    # front: EMPLOYEES ONLY board; back: a green EXIT box
    m.bx(-1.55, 1.55, -0.62, -0.45, 4.5, 5.4, 'brandR')
    text_front(m, 'EMPLOYEES ONLY', 0.5, -0.623, 0.0, 4.72, 'paper', maxw=2.9)
    m.bx(-0.55, 0.55, 0.45, 0.62, 3.95, 4.4, 'paper')
    m.bx(-1.0, 1.0, 0.45, 0.6, 5.0, 5.8, 'brand')
    text_back(m, 'BULKBARN', 0.4, 0.603, 0.0, 5.2, 'paper', maxw=1.8)
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    g = new(pal)
    bq(g, -0.45, 0.45, 0.623, 4.0, 4.35, 'exitG')
    text_back(g, 'EXIT', 0.24, 0.626, 0.0, 4.06, 'paper')
    make_glow('GateFrame_LED', g)
    # roll-up shutter: ribbed galvanised slats, a yellow-black bottom bar, the warning words
    m = new(pal)
    Hs, n = 3.05, 12
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.02), 'rackG' if i % 2 else 'chrome', bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'black' if k % 2 else 'hazY', bevel=False)
    m.box((0, -0.06, 1.95), (2.2, 0.01, 0.42), 'brandR', bevel=False)
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
    # back corridor walls (1 m along Blender Y, inner face +X): block, bump rail, a 3.6 m drop ceiling to the corridor
    # centre line (2.25 m from the wall's centre: the two sides' tiles meet edge to edge)
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'wallL', hull='noend', cull='t')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.14, 'concD')
        rq(m, 0.253, -0.5, 0.5, 1.6, 3.6, 'wallW')
        m.bx(0.25, 0.33, -0.5, 0.5, 0.85, 1.0, 'brand', hull='noend', cull='')
        rq(m, 0.253, -0.5, 0.5, 6.0, 6.12, 'brand')
        m.bx(0.25, 0.31, -0.5, 0.5, 4.2, 4.26, 'steelD', hull='none', cull='')   # conduit tray
        if name == 'TrailWall_B':   # wall pack light
            m.bx(0.25, 0.4, -0.25, 0.25, 3.2, 3.45, 'grey')
            rq(m, 0.403, -0.22, 0.22, 3.22, 3.43, 'lightW')
        elif name == 'TrailWall_C':   # a staff notice and a hand-sanitiser station
            m.bx(0.253, 0.27, -0.32, 0.32, 1.35, 2.05, 'paper', cull='l')
            rq(m, 0.273, -0.28, 0.28, 1.88, 2.0, 'brand')
            text_side(m, 'CLOCK IN', 0.1, 0.276, 0.0, 1.62, 'brand', 'x+', font='cond', maxw=0.5)
            m.bx(0.253, 0.36, 0.36, 0.48, 1.0, 1.3, 'pWhite', cull='l')
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=20)
    ring(m, 0, 0, 0.103, 0.95, 1.12, 'hazY', seg=20)
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ roof bays (hang from z = 0 = the roof deck at 10 m)
def joist(m, y, x0, x1, depth=0.75):
    """open-web steel joist along X at y: top chord, bottom chord, a zigzag web (painted both sides)"""
    m.bx(x0, x1, y - 0.06, y + 0.06, -0.1, -0.012, 'joist', hull='none', cull='t')
    m.bx(x0, x1, y - 0.045, y + 0.045, -depth, -depth + 0.07, 'joist', hull='none', cull='lr')
    n = int(round((x1 - x0) / 0.8))
    pts = []
    for k in range(n + 1):
        pts.append((x0 + 0.05 + (x1 - x0 - 0.1) * k / n, -0.1 if k % 2 == 0 else -depth + 0.07))
    for s in (-1, 1):
        L, R = [], []
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            dx, dz = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dz) or 1.0
            nx, nz = -dz / d * 0.025, dx / d * 0.025
            L.append((p[0] + nx, y + s * 0.012, p[1] + nz))
            R.append((p[0] - nx, y + s * 0.012, p[1] - nz))
        poly(m, L + R[::-1], 'joist', (0, s, 0))


def lamp(m, g, x, y, drop=0.9):
    """high-bay pendant: rod, driver box, an aluminium reflector bell; the lens glows (companion g)"""
    m.bx(x - 0.015, x + 0.015, y - 0.015, y + 0.015, -drop + 0.3, -0.012, 'steelD', hull='none', cull='t')
    m.cy((x, y, -drop - 0.12), 0.34, 0.12, 0.27, 'chrome', seg=8, caps=False)
    disc(g, x, y, -drop - 0.115, 0.31, 'lightW', seg=8)


def build_roof(pal, ao):
    """[4, 4] roof bays: a joist along the bay (local X) every 4 m; variants with a high-bay lamp, a skylight, a
    girder across the bay (Y) and a girder with a lamp"""
    for v in ('J', 'L', 'S', 'G', 'GL'):
        m = new(pal)
        g = new(pal) if v in ('L', 'S', 'GL') else None
        joist(m, 0.0, -2.0, 2.0)
        # deck ribs (the roof deck's flutes) painted under the roof plane
        if 'G' in v:   # girder: a deeper truss across the joists
            m.bx(-0.09, 0.09, -2.0, 2.0, -0.13, -0.012, 'joist', hull='noend', cull='t')
            m.bx(-0.08, 0.08, -2.0, 2.0, -1.0, -0.88, 'joist', hull='noend')
            for s in (-1, 1):
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
            lamp(m, g, 1.0, 1.0)
        if v == 'S':   # skylight: a 2 x 2 m dome in a curb, the panel glows
            m.bx(-1.1, 1.1, 0.9, 1.1, -0.18, -0.012, 'pWhite', hull='none', cull='t')
            m.bx(-1.1, 1.1, -1.1, -0.9, -0.18, -0.012, 'pWhite', hull='none', cull='t')
            m.bx(-1.1, -0.9, -0.9, 0.9, -0.18, -0.012, 'pWhite', hull='none', cull='t')
            m.bx(0.9, 1.1, -0.9, 0.9, -0.18, -0.012, 'pWhite', hull='none', cull='t')
            dq(m, -0.9, 0.9, -0.9, 0.9, -0.01, 'cool')
            dq(g, -0.88, 0.88, -0.88, 0.88, -0.014, 'cool')
            dq(g, -0.88, -0.2, 0.1, 0.88, -0.018, 'paper')
        make('Roof_' + v, m, ao)
        if g:
            make_glow('Roof_' + v + '_LED', g)


def build_signs(pal, ao):
    """hanging signs (from the roof plane): aisle number boards over the rack aisles, department boards, stockroom
    area boards. Both faces carry the words; the board hangs from two rods to 6.6 - 7.6 m."""
    AISLES = [('1', 'PAPER'), ('2', 'CLEANING'), ('3', 'SNACKS'), ('4', 'COFFEE'), ('5', 'CANNED'),
              ('6', 'DRINKS'), ('7', 'HARDWARE')]
    for num, words in AISLES:
        m = new(pal)
        z0, z1 = -3.4, -2.5
        m.bx(-1.3, 1.3, -0.05, 0.05, z0, z1, 'brand')
        m.bx(-1.3, -0.55, -0.065, 0.065, z0, z1, 'hazY', hull='none', cull='tblr')
        for x in (-1.0, 1.0):
            m.bx(x - 0.012, x + 0.012, -0.012, 0.012, z1, -0.012, 'steelD', hull='none', cull='t')
        for s in (-1, 1):
            yy = s * 0.068
            (text_front if s < 0 else text_back)(m, num, 0.58, yy, -0.92, z0 + 0.16, 'navy', maxw=0.62)
            (text_front if s < 0 else text_back)(m, words, 0.32, s * 0.053, 0.38, z0 + 0.3, 'paper', maxw=1.7)
            (text_front if s < 0 else text_back)(m, 'AISLE', 0.12, s * 0.053, 0.38, z0 + 0.13, 'hazY', font='cond', maxw=0.6)
        make('Aisle_' + num, m, ao)
    DEPTS = [('Produce', 'PRODUCE', 'leaf'), ('Tech', 'ELECTRONICS', 'navy'), ('Apparel', 'APPAREL', 'pPink'),
             ('Frozen', 'FROZEN', 'pSky'), ('Receiving', 'RECEIVING', 'hazY'), ('Staging', 'STAGING', 'hazY')]
    for key, word, c in DEPTS:
        m = new(pal)
        z0, z1 = -3.5, -2.6
        m.bx(-2.4, 2.4, -0.06, 0.06, z0, z1, c)
        dark = c in ('hazY', 'pSky')
        fg = 'black' if dark else 'paper'
        for s in (-1, 1):
            (fq if s < 0 else bq)(m, -2.4, 2.4, s * 0.063, z0 + 0.05, z0 + 0.12, 'paper' if dark else 'hazY')
            (text_front if s < 0 else text_back)(m, word, 0.5, s * 0.063, 0.0, z0 + 0.22, fg, maxw=4.4)
        for x in (-2.0, 2.0):
            m.bx(x - 0.012, x + 0.012, -0.012, 0.012, z1, -0.012, 'steelD', hull='none', cull='t')
        make('Dept_' + key, m, ao)


# ================================================================ floor marks (layer 0.01) and columns
def build_floors(pal, ao):
    m = new(pal)   # a yellow aisle line (1 m, along Blender X: the run placer turns it to its line of cells)
    uq(m, -0.5, 0.5, -0.05, 0.05, 0.004, 'hazY')
    make('F_Line', m, ao)
    m = new(pal)   # pedestrian walkway: green with white chevrons
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.004, 'exitG')
    for k in range(2):
        y0 = -0.4 + k * 0.5
        poly(m, [(-0.3, y0, 0.007), (0.0, y0 + 0.25, 0.007), (0.3, y0, 0.007), (0.3, y0 + 0.12, 0.007), (0.0, y0 + 0.37, 0.007), (-0.3, y0 + 0.12, 0.007)], 'paper', (0, 0, 1))
    make('F_Walk', m, ao)
    m = new(pal)   # hatched keep-clear cell (diagonal stripes)
    for k in range(3):
        x0 = -0.5 + k * 0.3
        poly(m, [(x0, -0.5, 0.004), (x0 + 0.12, -0.5, 0.004), (x0 + 0.22, 0.5, 0.004), (x0 + 0.1, 0.5, 0.004)], 'hazY', (0, 0, 1))
    make('F_Hatch', m, ao)
    m = new(pal)   # entrance mat [3, 2]
    uq(m, -1.45, 1.45, -0.95, 0.95, 0.004, 'black')
    for k in range(9):
        x = -1.3 + k * 0.325
        uq(m, x - 0.03, x + 0.03, -0.85, 0.85, 0.007, 'grey')
    text_up(m, 'BULKBARN', 0.36, 0.011, 0.0, 0.0, 'paper', maxw=2.4)
    make('F_Mat', m, ao)
    # steel column: a W-section 10 m tall with a yellow concrete-filled guard round its foot
    m = new(pal)
    m.bx(-0.16, 0.16, -0.02, 0.02, 0.0, H, 'rackB', cull='bt')
    m.bx(-0.16, 0.16, -0.16, -0.13, 0.0, H, 'rackB', cull='bt')
    m.bx(-0.16, 0.16, 0.13, 0.16, 0.0, H, 'rackB', cull='bt')
    m.cy((0, 0, 0), 0.34, 0.34, 1.2, 'hazY', seg=12)
    for z in (0.35, 0.8):
        m.cy((0, 0, z), 0.343, 0.343, 0.12, 'black', seg=12, caps=False, hull='none')
    make('Column', m, ao, cols=[cb(-0.35, -0.35, 0, 0.35, 0.35, 1.2), cb(-0.17, -0.17, 1.2, 0.17, 0.17, H)])
