"""kit-icecream creamery (zone 2, behind the STAFF ONLY door): batch freezers (churning machines), mix and ageing
tanks, blast freezers, the walk-in freezer (insulated panel walls, its door with a strip curtain, frosted shelving),
prep tables (mixing, cake decorating), a double sink, staff lockers, pallets of cone / cup / mix cartons, wrapped
carton stacks, cream cans, a pallet jack, a speed rack; the mezzanine (steel stair, rails, deck columns), party
tables and balloons, and the landmark PARTY ROOM on the deck (see ic_base.py)."""
import math
import random

from ic_base import *  # noqa: F401,F403
import ic_base as B


def legs(m, x0, x1, y0, y1, z1, c='steel', t=0.04):
    for (x, y) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        m.bx(x - t, x + t, y - t, y + t, 0.0, z1, c, cull='bt')


# ================================================================ production
def build_churn(pal, ao):
    """[2, 2] batch freezer (churning machine): a stainless cabinet on legs, the round barrel door with its spout,
    a hopper, a control panel (glow), a tub catching the ice cream on the shelf, a trolley of empty tubs beside it"""
    m, g = new(pal), new(pal)
    legs(m, -0.6, 0.6, -0.45, 0.5, 0.2)
    m.bx(-0.68, 0.68, -0.55, 0.6, 0.2, 1.7, 'chrome', cull='b')
    fq(m, -0.64, 0.64, -0.553, 0.25, 0.4, 'steel')
    # the barrel door: a disc on the front with a clamp handle, the spout chute below it
    m.cy((0.0, -0.55, 1.15), 0.34, 0.34, 0.06, 'steel', seg=10, rot=(90, 0, 0))
    m.cy((0.0, -0.61, 1.15), 0.26, 0.26, 0.03, 'glassL', seg=10, rot=(90, 0, 0))
    m.bm_((-0.3, -0.66, 1.15), (0.3, -0.66, 1.15), 0.04, 'steelD')
    m.bx(-0.1, 0.1, -0.8, -0.54, 0.8, 0.86, 'steel', cull='k')
    m.bx(-0.08, 0.08, -0.79, -0.73, 0.62, 0.8, 'steel', cull='t')
    m.cy((0.0, -0.77, 0.66), 0.06, 0.05, 0.08, 'strawb', seg=8, hull='none')
    # the shelf with the tub catching it
    m.bx(-0.4, 0.4, -0.85, -0.55, 0.42, 0.46, 'steel')
    m.cy((0.0, -0.72, 0.46), 0.14, 0.15, 0.18, 'white', seg=8)
    m.sp((0.0, -0.72, 0.63), 0.13, 'strawb', seg=(6, 3), scale=(1, 1, 0.5))
    # hopper and control panel
    m.cy((0.3, 0.2, 1.7), 0.12, 0.22, 0.3, 'steel', seg=8)
    m.cy((0.3, 0.2, 2.0), 0.23, 0.23, 0.03, 'steelD', seg=8, hull='none')
    m.bx(-0.6, -0.15, -0.6, -0.55, 1.45, 1.65, 'black', cull='k')
    fq(g, -0.56, -0.32, -0.603, 1.49, 1.61, 'screen')
    text_front(g, '-8.5', 0.06, -0.606, -0.44, 1.51, 'neonB', font='cond')
    for k, c in enumerate(('exitG', 'cherry', 'lemon')):
        fdisc(g, -0.25 + k * 0.035, -0.604, 1.55, 0.012, c, seg=6)
    text_front(m, 'CHURN-O-MATIC', 0.07, -0.553, 0.28, 1.6, 'steelD', font='cond', maxw=0.6)
    # a trolley of empty tubs beside it (east)
    m.bx(0.72, 0.98, -0.45, 0.35, 0.55, 0.58, 'steel')
    legs(m, 0.75, 0.95, -0.42, 0.32, 0.55, t=0.015)
    for k in range(2):
        m.cy((0.85, -0.22 + k * 0.4, 0.58), 0.1, 0.11, 0.3, 'white', seg=8)
    make('Churn', m, ao, cols=[cb(-0.68, -0.6, 0.0, 0.68, 0.6, 1.7), cb(-0.4, -0.85, 0.4, 0.4, -0.55, 0.86),
                               cb(0.72, -0.45, 0.0, 0.98, 0.35, 0.88), cb(0.08, 0.0, 1.7, 0.52, 0.42, 2.0)])
    make_glow('Churn_LED', g)


def build_tanks(pal, ao):
    """[2, 2] MixTank: a jacketed round vat on legs with a domed lid, a gauge, an outlet valve and a step stool;
    AgeTank: a taller ageing tank with an agitator motor on top and a level glass"""
    for name in ('MixTank', 'AgeTank'):
        m = new(pal)
        tall = name == 'AgeTank'
        r = 0.62 if tall else 0.72
        z0, z1 = 0.45, (2.45 if tall else 1.65)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            m.bx(math.cos(a) * r * 0.75 - 0.04, math.cos(a) * r * 0.75 + 0.04, math.sin(a) * r * 0.75 - 0.04,
                 math.sin(a) * r * 0.75 + 0.04, 0.0, z0 + 0.1, 'steel', cull='bt')
        m.cy((0, 0, z0 - 0.15), r * 0.5, r, 0.15, 'chrome', seg=10)
        m.cy((0, 0, z0), r, r, z1 - z0, 'chrome', seg=10)
        for z in (z0 + 0.2, z1 - 0.2):
            m.cy((0, 0, z), r + 0.02, r + 0.02, 0.05, 'steel', seg=10, caps=False, hull='none')
        m.cy((0, 0, z1), r, r * 0.25, 0.25, 'chrome', seg=10)
        # outlet pipe and valve to the front
        m.bm_((0.0, 0.0, z0 - 0.15), (0.0, -r - 0.15, 0.3), 0.08, 'steel')
        m.cy((0.0, -r - 0.17, 0.12), 0.07, 0.07, 0.2, 'steelD', seg=8)
        m.bm_((0.0, -r - 0.17, 0.33), (0.12, -r - 0.17, 0.33), 0.03, 'cherry')
        # gauge
        m.cy((r * 0.7, -r * 0.72, z1 - 0.45), 0.08, 0.08, 0.04, 'white', seg=8, rot=(90, 0, 45))
        if tall:
            m.bx(-0.12, 0.12, -0.12, 0.12, z1 + 0.25, z1 + 0.6, 'mintD')
            m.cy((0, 0, z1 + 0.6), 0.1, 0.1, 0.06, 'steelD', seg=8)
            m.bx(-r - 0.04, -r + 0.02, -0.03, 0.03, z0 + 0.2, z1 - 0.2, 'glassL', hull='none')
        else:   # a step stool
            m.bx(0.45, 0.85, -0.95, -0.7, 0.0, 0.35, 'hazY')
        cols = [cb(-r, -r, 0.0, r, r, z1 + 0.25), cb(-0.12, -r - 0.27, 0.0, 0.12, -r + 0.05, 0.4)]
        if tall:
            cols.append(cb(-0.12, -0.12, z1 + 0.25, 0.12, 0.12, z1 + 0.66))
        else:
            cols.append(cb(0.45, -0.95, 0.0, 0.85, -0.7, 0.35))
        make(name, m, ao, cols=cols)


def build_blastfreezer(pal, ao):
    """[3, 2] blast freezer (against the wall): a tall stainless cabinet with three doors, frost round the seals,
    the temperature readout (glow), a compressor box on top, a BLAST FREEZER plate"""
    m, g = new(pal), new(pal)
    m.bx(-1.48, 1.48, -0.75, 0.95, 0.0, 0.12, 'steelD', cull='b')
    m.bx(-1.5, 1.5, -0.8, 0.95, 0.12, 2.3, 'chrome', cull='b')
    for k in range(3):
        x = -1.0 + k * 1.0
        m.bx(x - 0.47, x + 0.47, -0.86, -0.8, 0.2, 2.15, 'steel', cull='k')
        fq(m, x - 0.47, x + 0.47, -0.863, 0.2, 0.27, 'frost')
        fq(m, x - 0.47, x - 0.4, -0.863, 0.27, 2.15, 'frost')
        m.bx(x + 0.3, x + 0.36, -0.95, -0.9, 0.8, 1.6, 'chrome')
        for j in range(2):
            m.bx(x + 0.31, x + 0.35, -0.9, -0.86, 0.85 + j * 0.68, 0.9 + j * 0.68, 'steelD', hull='none', cull='k')
    m.bx(-0.7, 0.7, -0.6, 0.6, 2.3, 2.75, 'steelD')
    for k in range(5):
        fq(m, -0.6 + k * 0.28, -0.48 + k * 0.28, -0.603, 2.38, 2.68, 'black')
    m.bx(-0.55, 0.55, -0.86, -0.8, 2.17, 2.28, 'black', cull='k')
    fq(g, -0.5, -0.1, -0.863, 2.19, 2.26, 'screen')
    text_front(g, '-35C', 0.05, -0.866, -0.3, 2.2, 'neonB', font='cond')
    text_front(m, 'BLAST FREEZER', 0.06, -0.863, 0.25, 2.2, 'white', font='cond', maxw=0.55)
    make('BlastFreezer', m, ao, cols=[cb(-1.5, -0.95, 0.0, 1.5, 0.95, 2.3), cb(-0.7, -0.6, 2.3, 0.7, 0.6, 2.75)])
    make_glow('BlastFreezer_LED', g)


# ================================================================ the walk-in freezer
def build_walkin(pal, ao):
    """insulated panel walls (links, along Blender Y, deck-underside high), the freezer door [3, 1] (span) swung open
    with a strip curtain tied back, frosted wire shelving [2, 1] (against a wall)"""
    def panel(m, y0, y1):
        m.bx(-0.1, 0.1, y0, y1, 0.0, UNDER, 'panel', hull='noend', cull='bt')
        for s in (-1, 1):
            x = s * 0.103
            (lq if s < 0 else rq)(m, x, y0, y1, 0.0, 0.18, 'steel')
            (lq if s < 0 else rq)(m, x, y0, y1, UNDER - 0.08, UNDER, 'steel')
            (lq if s < 0 else rq)(m, x, y0, y1, 0.18, 0.3, 'frost')
    m = new(pal); panel(m, -0.5, 0.5)
    for s in (-1, 1):
        (lq if s < 0 else rq)(m, s * 0.106, -0.01, 0.01, 0.3, UNDER - 0.08, 'steel')
    make('PanFull', m, ao, cols=[cb(-0.1, -0.5, 0.0, 0.1, 0.5, UNDER)])
    m = new(pal); panel(m, -0.5, -0.1); make('PanHalf', m, ao, cols=[cb(-0.1, -0.5, 0.0, 0.1, 0.0, UNDER)])
    m = new(pal)
    m.bx(-0.1, 0.1, -0.1, 0.1, 0.0, UNDER, 'panel', cull='bt')
    for (c, z0, z1) in (('steel', 0.0, 0.18), ('steel', UNDER - 0.08, UNDER)):
        fq(m, -0.1, 0.1, -0.103, z0, z1, c)
        bq(m, -0.1, 0.1, 0.103, z0, z1, c)
        lq(m, -0.103, -0.1, 0.1, z0, z1, c)
        rq(m, 0.103, -0.1, 0.1, z0, z1, c)
    make('PanPost', m, ao, cols=[cb(-0.1, -0.1, 0.0, 0.1, 0.1, UNDER)])
    # the door [3, 1] along X: panels either side of a 1.3 m opening, a heavy leaf swung open into the freezer (+Y)
    m, g = new(pal), new(pal)
    for (a, b) in ((-1.5, -0.65), (0.65, 1.5)):
        m.bx(a, b, -0.1, 0.1, 0.0, UNDER, 'panel', hull='noside', cull='bt')
        for s in (-1, 1):
            (fq if s < 0 else bq)(m, a, b, s * 0.103, 0.0, 0.18, 'steel')
            (fq if s < 0 else bq)(m, a, b, s * 0.103, UNDER - 0.08, UNDER, 'steel')
    m.bx(-0.65, 0.65, -0.1, 0.1, 2.35, UNDER, 'panel', cull='tlr')
    for x in (-0.65, 0.65):
        a, b = sorted((x, x - 0.08 if x > 0 else x + 0.08))
        m.bx(a, b, -0.14, 0.14, 0.0, 2.35, 'steel', cull='b')
    m.bx(-0.57, 0.57, -0.13, 0.13, 2.27, 2.35, 'steel', cull='lr')
    # the leaf, open at 90 degrees along the hinge side (+Y into the freezer), a big latch handle
    m.bx(0.5, 0.62, 0.14, 1.3, 0.02, 2.25, 'panel')
    m.bx(0.45, 0.5, 1.0, 1.15, 1.0, 1.15, 'steelD')
    # the strip curtain, tied back to both jambs (no collision)
    for s in (-1, 1):
        for k in range(4):
            x = s * (0.5 - k * 0.035)
            m.bx(x - 0.015, x + 0.015, -0.17 - k * 0.01, -0.15 - k * 0.01, 0.15, 2.25, 'glassL', hull='none', cull='tb')
    m.bx(-0.65, 0.65, -0.2, -0.14, 2.25, 2.35, 'steelD', cull='')
    # sign and readout
    m.bx(-0.75, 0.75, -0.14, -0.103, 2.55, 2.95, 'sky')
    text_front(m, 'WALK-IN FREEZER', 0.17, -0.143, 0.0, 2.65, 'white', maxw=1.4)
    m.bx(0.75, 1.05, -0.14, -0.103, 1.5, 1.7, 'black')
    fq(g, 0.78, 1.02, -0.143, 1.53, 1.67, 'screen')
    text_front(g, '-20', 0.08, -0.146, 0.9, 1.56, 'neonB', font='cond')
    make('FreezerDoor', m, ao, cols=[cb(-1.5, -0.14, 0.0, -0.57, 0.14, UNDER), cb(0.57, -0.14, 0.0, 1.5, 0.14, UNDER),
                                     cb(-0.65, -0.14, 2.27, 0.65, 0.14, UNDER), cb(0.45, 0.14, 0.0, 0.62, 1.3, 2.25)])
    make_glow('FreezerDoor_LED', g)
    # frosted wire shelving [2, 1] against a wall: shelves of tub rows and cartons
    m = new(pal)
    rnd = random.Random(12)
    for (x, y) in ((-0.95, -0.35), (0.95, -0.35), (-0.95, 0.4), (0.95, 0.4)):
        m.bx(x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0.0, 2.1, 'chrome', cull='b')
    for sh in range(4):
        z = 0.15 + sh * 0.6
        m.bx(-0.93, 0.93, -0.36, 0.41, z, z + 0.03, 'chrome', hull='none', cull='')
        uq(m, -0.9, 0.9, -0.33, 0.38, z + 0.033, 'frost')
        if sh == 3:
            continue
        x = -0.88
        while x < 0.6:
            w = rnd.choice((0.36, 0.5))
            if rnd.random() < 0.6:   # a row of tubs: one block, the lids painted on top
                c = rnd.choice(B.FLAVOURS[:16])
                m.bx(x, x + w, -0.3, 0.3, z + 0.03, z + 0.25, c, cull='b')
                uq(m, x + 0.02, x + w - 0.02, -0.28, 0.28, z + 0.253, 'white')
                fq(m, x + 0.03, x + w - 0.03, -0.303, z + 0.1, z + 0.17, 'white')
            else:
                m.bx(x, x + w, -0.3, 0.3, z + 0.03, z + 0.03 + rnd.uniform(0.25, 0.4), rnd.choice(('card', 'cardL', 'sky')), cull='b')
            x += w + 0.04
    make('FreezerShelf', m, ao, cols=[cb(-0.98, -0.38, 0.0, 0.98, 0.43, 2.1)])


# ================================================================ prep, sinks, lockers
def prep_table(m):
    legs(m, -1.4, 1.4, -0.85, 0.85, 0.86)
    m.bx(-1.45, 1.45, -0.9, 0.9, 0.86, 0.92, 'chrome', cull='b')
    m.bx(-1.4, 1.4, -0.85, 0.85, 0.2, 0.24, 'steel')
    fq(m, -1.45, 1.45, -0.903, 0.86, 0.92, 'steel')
    bq(m, -1.45, 1.45, 0.903, 0.86, 0.92, 'steel')


def build_prep(pal, ao):
    """[3, 2] prep tables (along X): A mixing -- a pink stand mixer, bowls, a cutting board of fruit, scoops, mix
    jugs on the undershelf; B cake decorating -- a turntable with a cake, piping bags, sprinkle jars, boxed cakes"""
    m = new(pal); prep_table(m)
    m.bx(-1.1, -0.7, -0.3, 0.15, 0.92, 1.0, 'pinkD')
    m.bx(-0.98, -0.82, 0.04, 0.12, 1.0, 1.4, 'pinkD', cull='bt')
    m.bx(-1.1, -0.65, -0.25, 0.15, 1.38, 1.55, 'pinkD')
    m.cy((-0.9, -0.14, 1.003), 0.13, 0.16, 0.2, 'chrome', seg=8)
    m.cy((-0.9, -0.14, 1.2), 0.012, 0.012, 0.18, 'steel', seg=4, hull='none')
    for k, (x, r) in enumerate(((-0.25, 0.22), (0.25, 0.17))):
        m.cy((x, 0.25, 0.92), r * 0.6, r, r * 0.65, 'chrome', seg=10)
        m.cy((x, 0.25, 0.92 + r * 0.55), r * 0.9, r * 0.9, 0.04, ('strawb', 'vanilla')[k], seg=10, hull='none')
    m.bx(0.5, 1.1, -0.6, -0.15, 0.92, 0.96, 'woodL')
    for k in range(4):
        x = 0.62 + k * 0.12
        m.bx(x - 0.04, x + 0.04, -0.4 - (k % 2) * 0.08, -0.32 - (k % 2) * 0.08, 0.96, 1.02, ('cherry', 'strawb', 'lemon', 'grape')[k], hull='none', cull='b')
    for k in range(3):
        m.bm_((0.0 + k * 0.08, -0.6, 0.935), (0.0 + k * 0.08, -0.35, 0.935), 0.02, 'steelD', hull='none')
    for k in range(2):
        m.cy((-0.7 + k * 1.4, 0.0, 0.24), 0.14, 0.12, 0.35, 'white', seg=8)
        m.cy((-0.7 + k * 1.4, 0.0, 0.59), 0.05, 0.05, 0.06, 'sky', seg=6)
    make('PrepTable_A', m, ao, cols=[cb(-1.45, -0.9, 0.0, 1.45, 0.9, 0.92), cb(-1.1, -0.3, 0.92, -0.65, 0.15, 1.55)])
    m = new(pal); prep_table(m)
    m.cy((-0.6, 0.0, 0.92), 0.06, 0.06, 0.12, 'steel', seg=6, hull='none')
    m.cy((-0.6, 0.0, 1.04), 0.26, 0.26, 0.03, 'chrome', seg=10)
    m.cy((-0.6, 0.0, 1.07), 0.22, 0.22, 0.2, 'chocF', seg=10)
    m.cy((-0.6, 0.0, 1.27), 0.2, 0.2, 0.03, 'wallC', seg=10, hull='none')
    scallop_r = 0.21
    torus(m, -0.6, 0.0, 1.28, scallop_r, 0.035, 'wallC', seg=10, sides=4, axis='z', hull='none')
    m.sp((-0.6, 0.0, 1.33), 0.045, 'cherry', seg=(6, 3))
    for k, c in enumerate(('strawb', 'mintF', 'lemon')):
        m.bm_((0.05 + k * 0.15, -0.55, 0.95), (0.18 + k * 0.15, -0.35, 0.95), 0.06, c)
    for k, c in enumerate(('cherry', 'sky')):
        m.cy((0.2 + k * 0.14, 0.4, 0.92), 0.05, 0.05, 0.14, c, seg=6)
        m.cy((0.2 + k * 0.14, 0.4, 1.06), 0.05, 0.05, 0.03, 'white', seg=6, hull='none')
    for k in range(3):   # boxed cakes on the undershelf
        x = -0.9 + k * 0.7
        m.bx(x - 0.25, x + 0.25, -0.3, 0.3, 0.24, 0.5, 'white', cull='b')
        fq(m, x - 0.25, x + 0.25, -0.303, 0.38, 0.44, 'pinkD')
    make('PrepTable_B', m, ao, cols=[cb(-1.45, -0.9, 0.0, 1.45, 0.9, 0.92), cb(-0.86, -0.26, 0.92, -0.34, 0.26, 1.33)])


def build_sink(pal, ao):
    """[2, 1] double sink (against the wall): two bowls, a gooseneck tap, a splash back, a drying rack of scoops"""
    m = new(pal)
    legs(m, -0.9, 0.9, -0.35, 0.35, 0.86)
    m.bx(-1.0, 1.0, -0.42, 0.42, 0.86, 0.92, 'chrome', cull='b')
    for x in (-0.45, 0.25):
        uq(m, x - 0.28, x + 0.28, -0.3, 0.25, 0.923, 'steelD')
    m.bx(-1.0, 1.0, 0.36, 0.45, 0.92, 1.3, 'chrome')
    m.bm_((-0.1, 0.32, 0.92), (-0.1, 0.32, 1.3), 0.04, 'chrome')
    m.bm_((-0.1, 0.32, 1.3), (-0.1, 0.05, 1.3), 0.032, 'chrome')
    m.bm_((-0.1, 0.05, 1.3), (-0.1, 0.05, 1.18), 0.024, 'chrome')
    m.bx(0.62, 0.95, -0.3, 0.3, 0.92, 0.95, 'steel')
    for k in range(4):
        m.bm_((0.66 + k * 0.08, -0.25, 0.96), (0.66 + k * 0.08, 0.2, 0.96), 0.02, 'steelD', hull='none')
    make('Sink', m, ao, cols=[cb(-1.0, -0.42, 0.0, 1.0, 0.45, 0.92), cb(-1.0, 0.36, 0.92, 1.0, 0.45, 1.3)])


def build_lockers(pal, ao):
    """[2, 1] staff lockers (against the wall): four tall doors in mint and pink, vents, name cards"""
    m = new(pal)
    m.bx(-0.98, 0.98, -0.25, 0.3, 0.0, 1.95, 'steel', cull='b')
    for k in range(4):
        x = -0.735 + k * 0.49
        c = 'wallM' if k % 2 else 'wallP'
        fq(m, x - 0.22, x + 0.22, -0.253, 0.12, 1.88, c)
        for j in range(3):
            fq(m, x - 0.12, x + 0.12, -0.256, 1.62 + j * 0.06, 1.64 + j * 0.06, 'steelD')
        fq(m, x - 0.08, x + 0.08, -0.256, 1.35, 1.43, 'white')
        m.bx(x + 0.14, x + 0.18, -0.29, -0.253, 0.9, 1.1, 'chrome', cull='k')
    make('Lockers', m, ao, cols=[cb(-0.98, -0.29, 0.0, 0.98, 0.3, 1.95)])


# ================================================================ cartons, pallets, small props
def pallet(m, x0, x1, y0, y1, z0=0.0):
    m.bx(x0, x1, y0, y1, z0 + 0.1, z0 + 0.14, 'wood', cull='')
    w = x1 - x0
    for k in range(3):
        a = x0 + 0.02 + k * (w - 0.14) / 2
        m.bx(a, a + 0.1, y0 + 0.02, y1 - 0.02, z0, z0 + 0.1, 'cardD', cull='bt', hull='none')
    for k in range(1, 5):
        a = x0 + k * w / 5
        uq(m, a - 0.006, a + 0.006, y0, y1, z0 + 0.143, 'cardD')


def carton(m, x0, x1, y0, y1, z0, z1, c, band=None, word=None, wc='chocD', cap=0.07, faces=(-1,)):
    m.bx(x0, x1, y0, y1, z0, z1, c, cull='b')
    uq(m, (x0 + x1) / 2 - 0.03, (x0 + x1) / 2 + 0.03, y0, y1, z1 + 0.003, 'cardL' if c != 'cardL' else 'card')
    for s in faces:
        y = y0 - 0.003 if s < 0 else y1 + 0.003
        if band:
            (fq if s < 0 else bq)(m, x0 + 0.02, x1 - 0.02, y, z0 + (z1 - z0) * 0.55, z0 + (z1 - z0) * 0.85, band)
        if word:
            (text_front if s < 0 else text_back)(m, word, cap, y + 0.003 * s, (x0 + x1) / 2, z0 + (z1 - z0) * 0.2, wc,
                                                 font='cond', maxw=(x1 - x0) * 0.85)


def column_of_cartons(m, x0, x1, y0, y1, z0, n, hgt, c, band=None, word=None, wc='chocD', cap=0.07, front=True):
    """a column of n cartons as one outlined block: painted seams between the cartons, a band and a word on the
    front (-Y) of each, tape over the top"""
    z1 = z0 + n * hgt
    m.bx(x0, x1, y0, y1, z0, z1, c, cull='b')
    uq(m, (x0 + x1) / 2 - 0.03, (x0 + x1) / 2 + 0.03, y0, y1, z1 + 0.003, 'cardL' if c != 'cardL' else 'card')
    for k in range(n):
        za = z0 + k * hgt
        if k:
            fq(m, x0, x1, y0 - 0.003, za - 0.006, za + 0.006, 'cardD')
            lq(m, x0 - 0.003, y0, y1, za - 0.006, za + 0.006, 'cardD')
            rq(m, x1 + 0.003, y0, y1, za - 0.006, za + 0.006, 'cardD')
        if front and band:
            fq(m, x0 + 0.03, x1 - 0.03, y0 - 0.003, za + hgt * 0.58, za + hgt * 0.82, band)
        if front and word and k == 0 and word[0] != '_':
            text_front(m, word, cap, y0 - 0.006, (x0 + x1) / 2, za + hgt * 0.2, wc, font='cond', maxw=(x1 - x0) * 0.85)
    return z1


def build_pallets(pal, ao):
    """[1, 1] pallets: waffle-cone cartons, cup / lid sleeves, cream-base cartons with a churn, an empty pallet stack;
    [2, 2] a tall shrink-wrapped stack of cone cartons; [1, 1] cream cans, a pallet jack, a speed rack"""
    m = new(pal); pallet(m, -0.47, 0.47, -0.47, 0.47)
    for i in range(2):
        column_of_cartons(m, -0.46 + i * 0.465, -0.005 + i * 0.465, -0.46, 0.46, 0.14, 3, 0.38, 'cardL', band='waf', word='CONES' if i == 0 else '_')
    make('Pal_Cones', m, ao, cols=[cb(-0.47, -0.47, 0.0, 0.47, 0.47, 1.28)])
    m = new(pal); pallet(m, -0.47, 0.47, -0.47, 0.47)
    for i in range(3):
        column_of_cartons(m, -0.46 + i * 0.31, -0.165 + i * 0.31, -0.46, 0.46, 0.14, 2, 0.48, 'white',
                          band='pinkD' if i != 1 else 'mintD', word='CUPS' if i == 1 else '_', wc='pinkD', cap=0.09)
    make('Pal_Cups', m, ao, cols=[cb(-0.47, -0.47, 0.0, 0.47, 0.47, 1.1)])
    m = new(pal); pallet(m, -0.47, 0.47, -0.47, 0.47)
    for i in range(2):
        column_of_cartons(m, -0.46 + i * 0.465, -0.005 + i * 0.465, -0.46, 0.46, 0.14, 2, 0.33, 'sky' if i else 'white',
                          band='white' if i else 'sky', word='CREAM' if i == 0 else '_')
    m.cy((0.0, 0.0, 0.8), 0.15, 0.15, 0.36, 'chrome', seg=8)
    m.cy((0.0, 0.0, 1.16), 0.11, 0.11, 0.06, 'steelD', seg=8)
    make('Pal_Mix', m, ao, cols=[cb(-0.47, -0.47, 0.0, 0.47, 0.47, 0.8), cb(-0.15, -0.15, 0.8, 0.15, 0.15, 1.22)])
    m = new(pal)
    for k in range(4):
        pallet(m, -0.47, 0.47, -0.47, 0.47, z0=k * 0.145)
    make('Pal_Empty', m, ao, cols=[cb(-0.47, -0.47, 0.0, 0.47, 0.47, 0.58)])
    m = new(pal)   # [2, 2] tall stack: two pallets of cartons, four columns each, wrap bands
    for (x0, x1) in ((-0.97, -0.02), (0.02, 0.97)):
        pallet(m, x0, x1, -0.95, 0.95)
        for j in range(2):
            xa = x0 + 0.01 + j * 0.47
            column_of_cartons(m, xa, xa + 0.455, -0.94, 0.94, 0.14, 4, 0.5, ('cardL', 'card')[j], band=('waf', 'pinkD')[j],
                              word=('CONES', '_')[j])
        for z in (0.5, 1.4):
            lq(m, x0 + 0.01 - 0.006, -0.94, 0.94, z, z + 0.3, 'glassL')
            rq(m, x1 - 0.01 + 0.006, -0.94, 0.94, z, z + 0.3, 'glassL')
    make('BoxStack', m, ao, cols=[cb(-0.97, -0.95, 0.0, 0.97, 0.95, 2.14)])
    m = new(pal)   # three cream cans
    for (x, y) in ((-0.18, -0.1), (0.18, 0.12)):
        m.cy((x, y, 0.0), 0.17, 0.17, 0.5, 'chrome', seg=8)
        m.cy((x, y, 0.5), 0.17, 0.09, 0.15, 'chrome', seg=8)
        m.cy((x, y, 0.65), 0.11, 0.11, 0.06, 'steel', seg=8)
        m.cy((x, y, 0.2), 0.175, 0.175, 0.04, 'sky', seg=8, caps=False, hull='none')
    make('Cans', m, ao, cols=[cb(-0.3, -0.22, 0.0, -0.06, 0.02, 0.72), cb(0.06, 0.0, 0.0, 0.3, 0.24, 0.72)])
    m = new(pal)   # pallet jack with a pink handle
    m.bx(-0.28, -0.12, -0.5, 0.3, 0.02, 0.09, 'pinkD')
    m.bx(0.12, 0.28, -0.5, 0.3, 0.02, 0.09, 'pinkD')
    m.bx(-0.3, 0.3, 0.3, 0.45, 0.0, 0.22, 'pinkD')
    m.bm_((0.0, 0.4, 0.22), (0.0, 0.48, 1.1), 0.05, 'black')
    m.bm_((-0.15, 0.48, 1.12), (0.15, 0.48, 1.12), 0.04, 'black')
    make('PalletJack', m, ao, cols=[cb(-0.3, -0.5, 0.0, 0.3, 0.48, 0.22)])
    m = new(pal)   # speed rack: a rolling sheet-pan rack of trays (cones, sandwiches, bars)
    for (x, y) in ((-0.3, -0.38), (0.3, -0.38), (-0.3, 0.38), (0.3, 0.38)):
        m.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.08, 1.75, 'chrome', cull='')
        m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.08, 'black', hull='none', cull='b')
    for k in range(5):
        z = 0.35 + k * 0.3
        m.bx(-0.28, 0.28, -0.36, 0.36, z, z + 0.02, 'steel', hull='none', cull='')
        c = ('waf', 'chocF', 'strawb', 'mintF', 'waf')[k]
        for j in range(2):
            y = -0.18 + j * 0.36
            m.bx(-0.24, 0.24, y - 0.14, y + 0.14, z + 0.02, z + 0.07, c, hull='none', cull='b')
    make('SpeedRack', m, ao, cols=[cb(-0.32, -0.4, 0.0, 0.32, 0.4, 1.75)])


# ================================================================ the filling line
def build_line(pal, ao):
    """[3, 1] a filling-line conveyor (along X): a steel bed on legs, a black belt, side guides, filled tubs riding on
    it (lids on); [2, 2] the filler: a stainless cabinet with a hopper and a nozzle reaching over the belt, a control
    panel (glow)"""
    for v, cols_ in (('A', ('strawb', 'mintF', 'chocF')), ('B', ('vanilla', 'mango', 'blueb'))):
        m = new(pal)
        for x in (-1.3, 1.3):
            legs(m, x - 0.08, x + 0.08, -0.22, 0.22, 0.78, t=0.025)
        m.bx(-1.5, 1.5, -0.3, 0.3, 0.78, 0.9, 'steel', hull='noside', cull='b')
        uq(m, -1.5, 1.5, -0.24, 0.24, 0.903, 'black')
        for s in (-1, 1):
            m.bx(-1.5, 1.5, s * 0.27 - 0.015, s * 0.27 + 0.015, 0.9, 1.0, 'chrome', hull='noside', cull='b')
        for k, c in enumerate(cols_):
            x = -1.0 + k * 1.0
            m.cy((x, 0.0, 0.906), 0.16, 0.18, 0.2, 'white', seg=8)
            m.cy((x, 0.0, 1.106), 0.185, 0.185, 0.03, c, seg=8, hull='none')
        make('Line_' + v, m, ao, cols=[cb(-1.5, -0.3, 0.0, 1.5, 0.3, 1.0)])
    m, g = new(pal), new(pal)
    legs(m, -0.7, 0.7, -0.3, 0.6, 0.25)
    m.bx(-0.8, 0.8, -0.4, 0.75, 0.25, 1.75, 'chrome', cull='b')
    m.cy((0.0, 0.2, 1.75), 0.25, 0.42, 0.45, 'steel', seg=10)
    m.cy((0.0, 0.2, 2.2), 0.43, 0.43, 0.04, 'steelD', seg=10, hull='none')
    m.bx(-0.62, -0.38, -1.2, -0.4, 1.3, 1.45, 'steel')
    for x in (-0.56, -0.44):
        m.cy((x, -1.1, 1.15), 0.025, 0.04, 0.15, 'steelD', seg=6, hull='none')
    m.bx(0.3, 0.75, -0.46, -0.4, 1.1, 1.55, 'black', cull='k')
    fq(g, 0.34, 0.71, -0.463, 1.3, 1.5, 'screen')
    text_front(g, 'FILL 5L', 0.05, -0.466, 0.525, 1.36, 'neonB', font='cond')
    for k, c in enumerate(('exitG', 'cherry')):
        fdisc(g, 0.42 + k * 0.1, -0.463, 1.18, 0.025, c, seg=6)
    text_front(m, 'TUB FILLER', 0.1, -0.403, -0.3, 1.5, 'steelD', font='cond', maxw=0.5)
    make('Filler', m, ao, cols=[cb(-0.8, -0.4, 0.0, 0.8, 0.75, 2.2), cb(-0.62, -1.2, 1.3, -0.38, -0.4, 1.45)])
    make_glow('Filler_LED', g)


# ================================================================ the mezzanine: stair, rails, columns
def build_mezzanine(pal, ao):
    """steel stair [2, 7] rising toward Blender +Y (game north) to the deck at DECK: 13 steps and a landing, pink
    stringers and handrails; guard rails (links, along Blender Y); deck columns"""
    m = new(pal)
    W, L, n, landing = 1.6, 7.0, 13, 0.55
    run = (L - landing) / n
    cols = []
    for k in range(n):
        y0 = -L / 2 + k * run
        y1 = y0 + run if k < n - 1 else L / 2
        top = (k + 1) * DECK / n
        m.bx(-W / 2, W / 2, y0, y1, top - 0.06, top, 'steel', hull='full', cull='')
        uq(m, -W / 2 + 0.03, W / 2 - 0.03, y0 + 0.005, y0 + 0.06, top + 0.003, 'hazY')
        cols.append(cb(-W / 2, y0, 0.0, W / 2, y1, top, True))
    for sx in (-1, 1):
        a, b = sorted((sx * W / 2, sx * (W / 2 + 0.08)))
        prof = [(-L / 2, 0.0), (-L / 2 + 0.25, 0.0), (L / 2 - landing, DECK - 0.35), (L / 2, DECK - 0.35), (L / 2, DECK), (L / 2 - landing - 0.1, DECK), (-L / 2, 0.3)]
        m.prism(prof, a, b, ['pinkD'])
        xr = sx * (W / 2 + 0.04)
        m.bm_((xr, -L / 2 + 0.1, 1.0), (xr, L / 2 - landing, DECK + 1.0), 0.05, 'chrome')
        m.bm_((xr, L / 2 - landing, DECK + 1.0), (xr, L / 2 - 0.05, DECK + 1.0), 0.042, 'chrome')
        for k in range(4):
            t = (k + 0.5) / 4
            yy = -L / 2 + 0.1 + t * (L - landing - 0.1)
            zz = 0.3 + t * (DECK - 0.3)
            m.bx(xr - 0.015, xr + 0.015, yy - 0.015, yy + 0.015, zz, zz + 0.95, 'chrome', hull='none', cull='b')
        for k in range(n + 1):
            y0 = -L / 2 + k * run
            y1 = L / 2 if k == n else y0 + run
            top = min(DECK, (k + 1) * DECK / n) + 1.0
            cols.append(cb(a, y0, 0.0, b, y1, top))
    make('Stair', m, ao, cols=cols)

    def rail(m, y0, y1):
        m.bx(-0.03, 0.03, y0, y1, 1.02, 1.08, 'pinkD', hull='noend', cull='')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'chrome', hull='noend', cull='')
        m.bx(-0.01, 0.01, y0, y1, 0.0, 0.14, 'pinkD', hull='none', cull='b')
    m = new(pal); rail(m, -0.5, 0.5); make('RailFull', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.5, 1.08)])
    m = new(pal); rail(m, -0.5, -0.035); make('RailHalf', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.0, 1.08)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.1, 'pinkD', cull='b')
    make('RailPost', m, ao)
    m = new(pal)
    m.bx(-0.1, 0.1, -0.1, 0.1, 0.0, UNDER, 'steelD', cull='bt')
    m.bx(-0.16, 0.16, -0.16, 0.16, UNDER - 0.04, UNDER, 'steelD', hull='none', cull='t')
    for (c, z0, z1) in (('hazY', 0.0, 0.4), ('black', 0.4, 0.5), ('hazY', 0.5, 0.9)):
        fq(m, -0.1, 0.1, -0.103, z0, z1, c)
        bq(m, -0.1, 0.1, 0.103, z0, z1, c)
        lq(m, -0.103, -0.1, 0.1, z0, z1, c)
        rq(m, 0.103, -0.1, 0.1, z0, z1, c)
    make('DeckColumn', m, ao, cols=[cb(-0.1, -0.1, 0.0, 0.1, 0.1, UNDER)])


# ================================================================ party: balloons, the PARTY ROOM landmark
def balloons(m, x, y, z0, n, rnd, top=1.9):
    m.cy((x, y, z0), 0.1, 0.1, 0.12, 'pinkD', seg=8)
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.12, 0.3)
        bx, by, bz = x + math.cos(a) * r, y + math.sin(a) * r, z0 + top + rnd.uniform(-0.25, 0.25)
        m.bm_((x + math.cos(a) * 0.06, y + math.sin(a) * 0.06, z0 + 0.12), (bx, by, bz - 0.2), 0.008, 'white', hull='none')
        m.sp((bx, by, bz), 0.17, ('cherry', 'sky', 'lemon', 'lilac', 'mintD', 'orange', 'pinkD')[k % 7], seg=(6, 4), scale=(1, 1, 1.18))


def build_party(pal, ao):
    """[1, 1] a balloon bunch on a weight; [8, 5] the PARTY ROOM on the mezzanine (faces south): pink walls with big
    windows and a wide doorway, bunting, the PARTY ROOM sign, a long party table with a giant sundae cake, chairs,
    balloons, a gift table; a flat roof"""
    rnd = random.Random(21)
    m = new(pal)
    balloons(m, 0.0, 0.0, 0.0, 4, rnd)
    make('Balloons', m, ao, cols=[cb(-0.12, -0.12, 0.0, 0.12, 0.12, 0.6)])
    m, g = new(pal), new(pal)
    X, Y, WH, T = 4.0, 2.5, 2.9, 0.15
    # floor finish (a pastel rug) on the deck
    uq(m, -3.6, 3.6, -2.1, 2.1, 0.004, 'lilac')
    uq(m, -3.3, 3.3, -1.8, 1.8, 0.007, 'cotton')
    # back and side walls: pink outside, cream inside, a waffle base
    m.bx(-X, X, Y - T, Y, 0.0, WH, 'wallP', cull='b')
    m.bx(-X, -X + T, -Y, Y - T, 0.0, WH, 'wallP', cull='bk')
    m.bx(X - T, X, -Y, Y - T, 0.0, WH, 'wallP', cull='bk')
    fq(m, -X + T, X - T, Y - T - 0.003, 0.0, WH, 'wallC')
    rq(m, -X + T + 0.003, -Y + T, Y - T, 0.0, WH, 'wallC')
    lq(m, X - T - 0.003, -Y + T, Y - T, 0.0, WH, 'wallC')
    bq(m, -X, X, Y + 0.003, 0.0, 0.15, 'wafD')
    lq(m, -X - 0.003, -Y, Y, 0.0, 0.15, 'wafD')
    rq(m, X + 0.003, -Y, Y, 0.0, 0.15, 'wafD')
    # front wall (y = -Y): sill walls, posts and a header round four big windows, a 2 m doorway in the middle
    m.bx(-X + T, -1.0, -Y, -Y + T, 0.0, 0.9, 'wallP', cull='bl')
    m.bx(1.0, X - T, -Y, -Y + T, 0.0, 0.9, 'wallP', cull='br')
    m.bx(-X + T, X - T, -Y, -Y + T, 2.3, WH, 'wallP', cull='lr')
    for x in (-2.5, -1.07, 1.07, 2.5):
        m.bx(x - 0.07, x + 0.07, -Y, -Y + T, 0.9, 2.3, 'wallP', cull='tb')
    for (x0, x1) in ((-X + T, -2.57), (-2.43, -1.14), (1.14, 2.43), (2.57, X - T)):
        m.bx(x0, x1, -Y - 0.05, -Y + T + 0.03, 0.87, 0.93, 'wafD', cull='lr')
        poly(g, [(x0, -Y + 0.07, 0.93), (x1, -Y + 0.07, 0.93), (x1, -Y + 0.07, 2.3), (x0, -Y + 0.07, 2.3)], 'glassA', (0, -1, 0))
        streaks(g, [(x0, -Y + 0.067, 0.93), (x1, -Y + 0.067, 0.93), (x1, -Y + 0.067, 2.3), (x0, -Y + 0.067, 2.3)], n=1, w=0.08)
    fq(m, -X, -1.0, -Y - 0.003, 0.0, 0.15, 'wafD')
    fq(m, 1.0, X, -Y - 0.003, 0.0, 0.15, 'wafD')
    # roof slab with a scalloped fascia and the PARTY ROOM sign
    m.bx(-X - 0.1, X + 0.1, -Y - 0.1, Y + 0.1, WH, WH + 0.2, 'wallC')
    scallops(m, -X - 0.1, X + 0.1, -Y - 0.103, WH + 0.0, 0.12, 'pinkD', n=20)
    m.bx(-1.8, 1.8, -Y - 0.18, -Y - 0.1, WH + 0.2, WH + 0.85, 'pinkD')
    text_front(m, 'PARTY ROOM', 0.44, -Y - 0.183, 0.0, WH + 0.3, 'white', maxw=3.2)
    # bunting across the front
    for k in range(14):
        x = -3.6 + k * 0.55
        z = 2.65 - 0.12 * math.sin(math.pi * ((k % 7) + 0.5) / 7)
        poly(m, [(x - 0.2, -Y - 0.02, z + 0.1), (x + 0.2, -Y - 0.02, z + 0.1), (x, -Y - 0.02, z - 0.22)],
             ('cherry', 'lemon', 'sky', 'mintD', 'lilac')[k % 5], (0, -1, 0))
    # inside: a long party table with a giant sundae cake, chairs both sides, a gift table, balloons
    m.bx(-1.8, 1.8, 0.5, 1.4, 0.72, 0.77, 'wallC')
    fq(m, -1.8, 1.8, 0.497, 0.45, 0.77, 'pinkD')
    scallops(m, -1.8, 1.8, 0.494, 0.45, 0.06, 'wallC', n=12)
    for x in (-1.7, 1.7):
        for y in (0.6, 1.3):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.72, 'chrome', cull='b')
    m.cy((0.0, 0.95, 0.77), 0.3, 0.3, 0.25, 'strawb', seg=10)
    m.cy((0.0, 0.95, 1.02), 0.22, 0.22, 0.2, 'vanilla', seg=10)
    m.sp((0.0, 0.95, 1.25), 0.15, 'chocF', seg=(6, 3))
    m.sp((0.0, 0.95, 1.42), 0.06, 'cherry', seg=(6, 3))
    for k in range(5):
        a = 2 * math.pi * k / 5
        m.cy((math.cos(a) * 0.16, 0.95 + math.sin(a) * 0.16, 1.22), 0.01, 0.01, 0.12, ('sky', 'lemon', 'cotton')[k % 3], seg=4, hull='none')
    for k in range(2):
        for s in (-1, 1):
            x = -0.6 + k * 1.2
            y = 0.95 + s * 0.75
            m.bx(x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.42, 0.47, ('sky', 'lemon', 'mintD', 'lilac')[k])
            for (lx, ly) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
                m.bx(x + lx - 0.02, x + lx + 0.02, y + ly - 0.02, y + ly + 0.02, 0.0, 0.42, 'chrome', cull='b', hull='none')
            yb = y + s * 0.18
            m.bx(x - 0.2, x + 0.2, yb - 0.025, yb + 0.025, 0.47, 0.9, ('sky', 'lemon', 'mintD', 'lilac')[k])
    m.bx(2.6, 3.7, 1.2, 2.2, 0.0, 0.75, 'mintD', cull='b')
    for k, (x, y, s, c) in enumerate(((2.85, 1.5, 0.3, 'cherry'), (3.3, 1.55, 0.36, 'sky'), (3.05, 1.95, 0.26, 'lemon'))):
        m.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, 0.75, 0.75 + s, c)
        uq(m, x - 0.03, x + 0.03, y - s / 2, y + s / 2, 0.753 + s, 'white')
    balloons(m, -3.4, 1.9, 0.0, 4, rnd, top=1.8)
    make('Landmark_Party', m, ao, cols=[
        cb(-X, Y - T, 0.0, X, Y, WH), cb(-X, -Y, 0.0, -X + T, Y, WH), cb(X - T, -Y, 0.0, X, Y, WH),
        cb(-X, -Y, 0.0, -1.0, -Y + T, WH), cb(1.0, -Y, 0.0, X, -Y + T, WH),
        cb(-1.0, -Y, 2.3, 1.0, -Y + T, WH),
        cb(-1.8, 0.5, 0.0, 1.8, 1.4, 0.77), cb(2.6, 1.2, 0.0, 3.7, 2.2, 0.75)])
    make_glow('Landmark_Party_Glass', g)


def build_kitchen(pal, ao):
    build_churn(pal, ao)
    build_tanks(pal, ao)
    build_blastfreezer(pal, ao)
    build_walkin(pal, ao)
    build_prep(pal, ao)
    build_sink(pal, ao)
    build_lockers(pal, ao)
    build_pallets(pal, ao)
    build_mezzanine(pal, ao)
    build_line(pal, ao)
    build_party(pal, ao)
