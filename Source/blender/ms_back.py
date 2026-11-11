"""kit-megastore stockroom: pallet jack, vertical baler, stretch wrapper, the break room (table, vending machines,
lockers, kitchenette, block partitions and a door), the mezzanine (steel stair, guard rails, deck columns) and the
landmark receiving office standing on it (see ms_base.py for conventions)."""
import math
import random

from ms_base import *  # noqa: F401,F403
import ms_base as B
from ms_dept import rbox

UNDER = DECK - 0.4     # deck underside (the engine's deck slab is 0.4 thick)


def build_jack(pal, ao):
    """manual pallet jack: two forks, the pump body with its wheel, the tiller handle (front -Y = the handle end)"""
    m = new(pal)
    for sx in (-1, 1):
        x = sx * 0.2
        m.bx(x - 0.08, x + 0.08, -0.15, 0.48, 0.0, 0.08, 'steelD', cull='b')
    m.bx(-0.3, 0.3, -0.35, -0.15, 0.0, 0.2, 'brandR', cull='b')
    m.cy((0, -0.3, 0.2), 0.07, 0.07, 0.35, 'steel', seg=8)
    m.bx(-0.06, 0.06, -0.5, -0.36, 0.0, 0.16, 'black')
    m.bm_((0, -0.3, 0.5), (0, -0.62, 1.15), 0.05, 'brandR')
    m.bx(-0.16, 0.16, -0.66, -0.58, 1.12, 1.2, 'black')
    make('PalletJack', m, ao, cols=[cb(-0.3, -0.5, 0.0, 0.3, 0.48, 0.2)])


def build_baler(pal, ao):
    """[2, 2] vertical cardboard baler against the wall: chamber with a gated loading door, the ram housing,
    hydraulic power pack, control box with a red stop button, hazard stripes, a bale tie rack"""
    m = new(pal)
    m.bx(-0.9, 0.9, -0.55, 0.85, 0.0, 2.0, 'brand', cull='b')
    m.bx(-0.8, 0.8, -0.6, 0.85, 2.0, 3.3, 'steelD', cull='b')
    m.bx(-0.95, 0.95, -0.7, 0.9, 3.3, 3.45, 'steelD')
    # loading door: frame, mesh window, hazard bar
    m.bx(-0.75, 0.75, -0.62, -0.55, 0.2, 1.75, 'rackG', cull='k')
    fq(m, -0.62, 0.62, -0.623, 0.85, 1.6, 'black')
    for k in range(8):
        x = -0.6 + k * 0.17
        fq(m, x, x + 0.025, -0.626, 0.87, 1.58, 'steel')
    for k in range(6):
        x0 = -0.72 + k * 0.25
        fq(m, x0, x0 + 0.12, -0.623, 0.3, 0.45, 'hazY')
    m.bx(-0.5, 0.5, -0.7, -0.62, 1.66, 1.72, 'chrome')
    # control box and stop button, side power pack
    m.bx(0.92, 1.0, -0.3, 0.1, 1.2, 1.7, 'pWhite', cull='l')
    m.cy((1.0, -0.1, 1.45), 0.05, 0.05, 0.05, 'brandR', seg=8, rot=(0, math.pi / 2, 0))
    m.bx(-0.95, -0.9, -0.4, 0.6, 0.0, 0.9, 'steel', cull='rb')
    fq(m, -0.6, 0.6, -0.603, 2.6, 3.0, 'hazY')
    text_front(m, 'BALER', 0.3, -0.606, 0.0, 2.64, 'black', maxw=1.0)
    make('Baler', m, ao, cols=[cb(-0.95, -0.7, 0.0, 1.0, 0.9, 3.45)])


def build_wrapper(pal, ao):
    """[2, 2] stretch wrapper: turntable, mast with the film carriage, a pallet load half wrapped on the table"""
    m = new(pal)
    m.cy((0, 0, 0), 0.8, 0.8, 0.12, 'steelD', seg=12)
    ring(m, 0, 0, 0.123, 0.62, 0.72, 'hazY', seg=12)
    m.bx(-0.15, 0.15, 0.8, 0.98, 0.0, 2.4, 'brand', cull='b')
    m.bx(-0.25, 0.25, 0.62, 0.8, 1.2, 1.5, 'steel')
    m.cy((0, 0.66, 1.0), 0.07, 0.07, 0.6, 'wrap', seg=8)
    m.bx(-0.3, 0.3, 0.75, 0.95, 0.0, 0.5, 'steelD', cull='b')
    pallet(m, -0.48, 0.48, -0.48, 0.48, 0.12)
    load(m, -0.46, 0.46, -0.46, 0.46, 0.26, 1.5, 'card', bands=1)
    case(m, -0.3, 0.2, -0.3, 0.25, 1.5, 1.75, 'cardL', tape='cardD')
    make('Wrapper', m, ao, cols=[cb(-0.8, -0.8, 0.0, 0.8, 0.8, 0.12), cb(-0.48, -0.48, 0.12, 0.48, 0.48, 1.75), cb(-0.3, 0.62, 0.0, 0.3, 0.98, 2.4)])


# ================================================================ break room (under the mezzanine deck)
def build_breakroom(pal, ao):
    m = new(pal)   # table [2, 2] with four stools
    m.bx(-0.6, 0.6, -0.6, 0.6, 0.72, 0.76, 'woodL')
    m.cy((0, 0, 0), 0.25, 0.25, 0.04, 'steelD', seg=8, hull='none')
    m.bx(-0.04, 0.04, -0.04, 0.04, 0.04, 0.72, 'steelD', hull='none', cull='bt')
    for (x, y) in ((-0.8, 0.0), (0.8, 0.0), (0.0, -0.8), (0.0, 0.8)):
        m.bx(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.42, 0.47, 'brand')
        m.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 0.42, 'steelD', hull='none', cull='bt')
    m.bx(0.15, 0.3, -0.1, 0.05, 0.76, 0.88, 'pWhite')
    m.cy((-0.2, 0.15, 0.76), 0.05, 0.04, 0.11, 'brandR', seg=6)
    make('BreakTable', m, ao, cols=[cb(-0.6, -0.6, 0.0, 0.6, 0.6, 0.76), cb(-0.98, -0.2, 0.0, -0.62, 0.2, 0.47), cb(0.62, -0.2, 0.0, 0.98, 0.2, 0.47),
                                    cb(-0.2, -0.98, 0.0, 0.2, -0.62, 0.47), cb(-0.2, 0.62, 0.0, 0.2, 0.98, 0.47)])
    # vending machines [1, 1] (against the wall): snacks (navy) and drinks (red); the window glows
    for v, (body, name) in enumerate((('navy', 'Vending'), ('brandR', 'Vending_B'))):
        rnd = random.Random(80 + v)
        m = new(pal)
        g = new(pal)
        m.bx(-0.46, 0.46, -0.38, 0.4, 0.0, 1.85, body, cull='b')
        fq(m, -0.4, 0.15, -0.383, 0.55, 1.75, 'black')
        fq(m, 0.2, 0.4, -0.383, 1.1, 1.6, 'grey')
        for k in range(6):
            fq(m, 0.23 + (k % 2) * 0.08, 0.29 + (k % 2) * 0.08, -0.386, 1.2 + (k // 2) * 0.12, 1.26 + (k // 2) * 0.12, 'paper')
        fq(m, -0.35, 0.1, -0.383, 0.15, 0.35, 'black')
        fq(g, -0.38, 0.13, -0.386, 0.57, 1.73, 'cool')
        for r in range(5):
            z = 0.62 + r * 0.22
            x = -0.36
            while x < 0.08:
                w = 0.07 if v else rnd.uniform(0.05, 0.1)
                fq(g, x, x + w - 0.012, -0.389, z, z + (0.14 if v else rnd.uniform(0.08, 0.15)), rnd.choice(GOODS + ['pOrange', 'pPink']))
                x += w
        text_front(m, 'SNACKS' if v == 0 else 'DRINKS', 0.09, -0.386, 0.31, 1.66, 'paper', maxw=0.26)
        make(name, m, ao, cols=[cb(-0.46, -0.38, 0.0, 0.46, 0.4, 1.85)])
        make_glow(name + '_LED', g)
    m = new(pal)   # lockers [2, 1]: four tall doors with vents and number plates
    m.bx(-0.98, 0.98, -0.25, 0.3, 0.0, 1.95, 'steelD', cull='b')
    for k in range(4):
        x0 = -0.96 + k * 0.48
        fq(m, x0 + 0.02, x0 + 0.46, -0.253, 0.08, 1.9, ['rackB', 'brand', 'rackB', 'brand'][k])
        for j in range(3):
            fq(m, x0 + 0.12, x0 + 0.36, -0.256, 1.6 + j * 0.06, 1.62 + j * 0.06, 'navy')
        fq(m, x0 + 0.36, x0 + 0.4, -0.256, 0.9, 1.05, 'chrome')
        fq(m, x0 + 0.16, x0 + 0.3, -0.256, 1.4, 1.48, 'paper')
    make('Lockers', m, ao, cols=[cb(-0.98, -0.25, 0.0, 0.98, 0.3, 1.95)])
    m = new(pal)   # kitchenette [3, 1]: counter, sink, microwave, coffee maker, a fridge
    m.bx(-1.45, 0.75, -0.3, 0.32, 0.0, 0.88, 'pWhite', cull='b')
    m.bx(-1.48, 0.78, -0.33, 0.32, 0.88, 0.92, 'woodL')
    for k in range(4):
        x = -1.2 + k * 0.52
        fq(m, x, x + 0.48, -0.303, 0.1, 0.8, 'mint' if k % 2 else 'cream')
        fq(m, x + 0.2, x + 0.28, -0.306, 0.7, 0.74, 'chrome')
    uq(m, -0.8, -0.3, -0.2, 0.2, 0.923, 'steel')
    m.bx(-0.58, -0.52, 0.22, 0.28, 0.92, 1.2, 'chrome', hull='none')
    m.bx(-0.2, 0.32, -0.15, 0.3, 0.92, 1.2, 'pBlack')
    fq(m, -0.16, 0.12, -0.153, 0.96, 1.16, 'screen')
    m.bx(0.45, 0.65, -0.05, 0.25, 0.92, 1.25, 'brandR')
    m.bx(0.8, 1.45, -0.32, 0.32, 0.0, 1.8, 'chrome', cull='b')
    fq(m, 0.8, 1.45, -0.323, 1.15, 1.17, 'steelD')
    m.bx(0.85, 0.9, -0.38, -0.323, 1.25, 1.6, 'steelD')
    m.bx(-1.45, 0.75, 0.15, 0.32, 1.45, 2.1, 'cream', cull='')
    make('Kitchen', m, ao, cols=[cb(-1.48, -0.33, 0.0, 0.78, 0.32, 0.92), cb(0.8, -0.38, 0.0, 1.45, 0.32, 1.8)])
    # block partitions (1 cell thick, deck underside high; modelled along Blender Y), and a door [3, 1]
    def part(m, y0, y1):
        m.bx(-0.1, 0.1, y0, y1, 0.0, UNDER, 'wallW', hull='noend', cull='bt')
        for s in (-1, 1):
            x = s * 0.103
            (lq if s < 0 else rq)(m, x, y0, y1, 0.0, 0.14, 'concD')
            (lq if s < 0 else rq)(m, x, y0, y1, 1.0, 1.08, 'brand')
            for k in range(1, 7):
                z = 0.14 + k * 0.4
                if abs(z - 1.04) > 0.1:
                    (lq if s < 0 else rq)(m, x, y0, y1, z - 0.008, z + 0.008, 'joint')
    m = new(pal); part(m, -0.5, 0.5); make('PartFull', m, ao, cols=[cb(-0.1, -0.5, 0.0, 0.1, 0.5, UNDER)])
    m = new(pal); part(m, -0.5, -0.1); make('PartHalf', m, ao, cols=[cb(-0.1, -0.5, 0.0, 0.1, 0.0, UNDER)])
    m = new(pal)
    m.bx(-0.1, 0.1, -0.1, 0.1, 0.0, UNDER, 'wallW', cull='bt')
    for (c, z0, z1) in (('concD', 0.0, 0.14), ('brand', 1.0, 1.08)):
        fq(m, -0.1, 0.1, -0.103, z0, z1, c)
        bq(m, -0.1, 0.1, 0.103, z0, z1, c)
        lq(m, -0.103, -0.1, 0.1, z0, z1, c)
        rq(m, 0.103, -0.1, 0.1, z0, z1, c)
    make('PartPost', m, ao, cols=[cb(-0.1, -0.1, 0.0, 0.1, 0.1, UNDER)])
    m = new(pal)   # break-room door [3, 1] (along X): wall either side of a 1.2 m opening, the leaf swung open inward
    for (a, b) in ((-1.5, -0.6), (0.6, 1.5)):
        m.bx(a, b, -0.1, 0.1, 0.0, UNDER, 'wallW', hull='noside', cull='bt')
        for s in (-1, 1):
            (fq if s < 0 else bq)(m, a, b, s * 0.103, 0.0, 0.14, 'concD')
            (fq if s < 0 else bq)(m, a, b, s * 0.103, 1.0, 1.08, 'brand')
    m.bx(-0.6, 0.6, -0.1, 0.1, 2.2, UNDER, 'wallW', cull='t')
    m.bx(-0.6, -0.56, -0.12, 0.12, 0.0, 2.14, 'steelD', cull='b')
    m.bx(0.56, 0.6, -0.12, 0.12, 0.0, 2.14, 'steelD', cull='b')
    m.bx(-0.6, 0.6, -0.12, 0.12, 2.14, 2.2, 'steelD', cull='t')
    m.bx(0.58, 0.62, 0.12, 1.25, 0.0, 2.15, 'brand')   # the open leaf, swung against the room side
    m.bx(-0.7, 0.7, -0.14, -0.103, 2.4, 2.75, 'paper', cull='k')
    text_front(m, 'BREAK ROOM', 0.2, -0.143, 0.0, 2.48, 'brand', maxw=1.3)
    make('BreakDoor', m, ao, cols=[cb(-1.5, -0.1, 0.0, -0.6, 0.1, UNDER), cb(0.6, -0.1, 0.0, 1.5, 0.1, UNDER), cb(0.58, 0.1, 0.0, 0.62, 1.25, 2.15)])


# ================================================================ mezzanine: stair, rails, columns
def build_mezzanine(pal, ao):
    # steel stair [2, 7] rising toward Blender +Y (game north) to the deck at 3.5 m: 13 steps and a top landing,
    # yellow stringers and handrails; collision: walkable stair blocks, rails along both sides
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
        m.prism(prof, a, b, ['hazY'])
        xr = sx * (W / 2 + 0.04)
        m.bm_((xr, -L / 2 + 0.1, 1.0), (xr, L / 2 - landing, DECK + 1.0), 0.05, 'hazY')
        m.bm_((xr, L / 2 - landing, DECK + 1.0), (xr, L / 2 - 0.05, DECK + 1.0), 0.042, 'hazY')
        for k in range(4):
            t = (k + 0.5) / 4
            yy = -L / 2 + 0.1 + t * (L - landing - 0.1)
            zz = 0.3 + t * (DECK - 0.3)
            m.bx(xr - 0.015, xr + 0.015, yy - 0.015, yy + 0.015, zz, zz + 0.95, 'hazY', hull='none', cull='b')
        for k in range(n + 1):
            y0 = -L / 2 + k * run
            y1 = L / 2 if k == n else y0 + run
            top = min(DECK, (k + 1) * DECK / n) + 1.0
            cols.append(cb(a, y0, 0.0, b, y1, top))
    make('Stair', m, ao, cols=cols)
    # guard rail (modelled along Blender Y; the run placer links half modules): top / mid rails and a kick plate
    def rail(m, y0, y1):
        m.bx(-0.03, 0.03, y0, y1, 1.02, 1.08, 'hazY', hull='noend', cull='')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'hazY', hull='noend', cull='')
        m.bx(-0.01, 0.01, y0, y1, 0.0, 0.12, 'hazY', hull='none', cull='b')
    m = new(pal); rail(m, -0.5, 0.5); make('RailFull', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.5, 1.08)])
    m = new(pal); rail(m, -0.5, -0.035); make('RailHalf', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.0, 1.08)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.1, 'hazY', cull='b')
    make('RailPost', m, ao)
    m = new(pal)   # deck column (floor to the deck underside)
    m.bx(-0.1, 0.1, -0.1, 0.1, 0.0, UNDER, 'steelD', cull='bt')
    m.bx(-0.16, 0.16, -0.16, 0.16, UNDER - 0.04, UNDER, 'steelD', hull='none', cull='t')
    for (c, z0, z1) in (('hazY', 0.0, 0.4), ('black', 0.4, 0.5), ('hazY', 0.5, 0.9)):
        fq(m, -0.1, 0.1, -0.103, z0, z1, c)
        bq(m, -0.1, 0.1, 0.103, z0, z1, c)
        lq(m, -0.103, -0.1, 0.1, z0, z1, c)
        rq(m, 0.103, -0.1, 0.1, z0, z1, c)
    make('DeckColumn', m, ao, cols=[cb(-0.1, -0.1, 0.0, 0.1, 0.1, UNDER)])


# ================================================================ landmark: the receiving office on the mezzanine [8, 5]
def build_office(pal, ao):
    """a site-built office box on the deck (placed on the "@layer 3.5" grid): block walls 2.9 m with a ribbon of open
    windows over the deck front (-Y), a doorway at the east end of the front, desks with monitors and a plan table
    inside, a flat roof slab with the RECEIVING OFFICE fascia and the BULKBARN logo"""
    m = new(pal)
    g = new(pal)
    Hh, t = 2.9, 0.15
    X0, X1, Y0, Y1 = -3.9, 3.9, -2.4, 2.4
    # back and side walls (outside faces painted with a band)
    m.bx(X0, X1, Y1 - t, Y1, 0.0, Hh, 'wallW', cull='b')
    m.bx(X0, X0 + t, Y0, Y1 - t, 0.0, Hh, 'wallW', cull='b')
    m.bx(X1 - t, X1, Y0, Y1 - t, 0.0, Hh, 'wallW', cull='b')
    # front wall: sill wall to 1.0 m, lintel from 2.1 m, mullions; a 1.4 m doorway at the east end (x 2.3 .. 3.75)
    m.bx(X0 + t, 2.2, Y0, Y0 + t, 0.0, 1.0, 'wallW', cull='b')
    m.bx(X0 + t, X1 - t, Y0, Y0 + t, 2.1, Hh, 'wallW')
    for x in (-2.6, -1.3, 0.0, 1.1):
        m.bx(x - 0.05, x + 0.05, Y0 + 0.02, Y0 + t - 0.02, 1.0, 2.1, 'steelD', cull='bt')
    m.bx(2.2, 2.3, Y0, Y0 + t, 0.0, 2.1, 'steelD', cull='bt')
    m.bx(X0 + t, 2.2, Y0 - 0.06, Y0, 0.96, 1.02, 'steelD')
    m.bx(3.69, 3.74, Y0 + t, Y0 + 1.1, 0.0, 2.05, 'brand')   # the door, open inward against the east wall
    fq(m, X0 + t, 2.2, Y0 - 0.003, 0.0, 0.14, 'concD')
    # roof slab and fascia sign
    m.bx(X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1, Hh, Hh + 0.25, 'steelD')
    m.bx(-2.6, 2.6, Y0 - 0.2, Y0 - 0.1, Hh + 0.1, Hh + 0.75, 'brand')
    text_front(m, 'RECEIVING OFFICE', 0.36, Y0 - 0.203, 0.0, Hh + 0.24, 'paper', maxw=5.0)
    # inside: two desks with monitors and chairs, a plan table, filing cabinets, a whiteboard
    for x in (-2.5, -0.4):
        m.bx(x - 0.75, x + 0.75, Y1 - 0.9, Y1 - t - 0.02, 0.72, 0.76, 'woodL')
        m.bx(x - 0.7, x - 0.62, Y1 - 0.85, Y1 - t - 0.05, 0.0, 0.72, 'grey', hull='none', cull='b')
        m.bx(x + 0.62, x + 0.7, Y1 - 0.85, Y1 - t - 0.05, 0.0, 0.72, 'grey', hull='none', cull='b')
        m.bx(x - 0.3, x + 0.3, Y1 - 0.45, Y1 - 0.4, 0.8, 1.15, 'pBlack')
        fq(g, x - 0.27, x + 0.27, Y1 - 0.453, 0.83, 1.12, 'scrB')
        m.bx(x - 0.04, x + 0.04, Y1 - 0.42, Y1 - 0.36, 0.76, 0.8, 'pBlack', hull='none')
        m.bx(x - 0.22, x + 0.22, Y1 - 1.4, Y1 - 1.0, 0.42, 0.48, 'pBlack')
        m.bx(x - 0.22, x + 0.22, Y1 - 1.04, Y1 - 0.98, 0.48, 0.95, 'pBlack')
        m.bx(x - 0.03, x + 0.03, Y1 - 1.23, Y1 - 1.17, 0.0, 0.42, 'steelD', hull='none', cull='b')
    m.bx(1.2, 2.6, -0.5, 0.5, 0.88, 0.92, 'woodL')
    m.bx(1.25, 1.35, -0.45, 0.45, 0.0, 0.88, 'grey', hull='none', cull='b')
    m.bx(2.45, 2.55, -0.45, 0.45, 0.0, 0.88, 'grey', hull='none', cull='b')
    uq(m, 1.35, 2.3, -0.35, 0.3, 0.923, 'paper')
    uq(m, 1.5, 2.0, -0.2, 0.1, 0.926, 'brand')
    m.bx(X1 - t - 0.5, X1 - t, 0.4, 1.4, 0.0, 1.35, 'steel', cull='b')
    for k in range(3):
        lq(m, X1 - t - 0.503, 0.45, 1.35, 0.15 + k * 0.42, 0.5 + k * 0.42, 'rackG')
    m.bx(X0 + t, X0 + t + 0.03, -1.2, 0.8, 1.1, 2.0, 'pWhite', cull='l')
    for k in range(4):
        rq(m, X0 + t + 0.033, -1.0 + k * 0.4, -0.75 + k * 0.4, 1.3 + (k % 2) * 0.25, 1.36 + (k % 2) * 0.25, ['brandR', 'brand', 'leaf', 'pBlack'][k])
    # outside: BULKBARN logo on the east wall, a fire extinguisher by the door
    rq(m, X1 + 0.003, -1.5, 1.5, 1.6, 2.4, 'brand')
    text_side(m, 'BULKBARN', 0.42, X1 + 0.006, 0.0, 1.75, 'paper', 'x+', maxw=2.8)
    make('Landmark_Office', m, ao, cols=[
        cb(X0, Y1 - t, 0.0, X1, Y1, Hh), cb(X0, Y0, 0.0, X0 + t, Y1 - t, Hh), cb(X1 - t, Y0, 0.0, X1, Y1 - t, Hh),
        cb(X0 + t, Y0 - 0.06, 0.0, 2.3, Y0 + t, 1.02), cb(X0 + t, Y0, 2.1, X1 - t, Y0 + t, Hh),
        cb(3.69, Y0 + t, 0.0, 3.74, Y0 + 1.1, 2.05),
        cb(X0 - 0.1, Y0 - 0.1, Hh, X1 + 0.1, Y1 + 0.1, Hh + 0.25),
        cb(-3.25, Y1 - 0.9, 0.0, 0.35, Y1 - t, 0.76), cb(1.2, -0.5, 0.0, 2.6, 0.5, 0.92), cb(X1 - t - 0.5, 0.4, 0.0, X1 - t, 1.4, 1.35)])
    make_glow('Landmark_Office_LED', g)


def build_back(pal, ao):
    build_jack(pal, ao)
    build_baler(pal, ao)
    build_wrapper(pal, ao)
    build_breakroom(pal, ao)
    build_mezzanine(pal, ao)
    build_office(pal, ao)
