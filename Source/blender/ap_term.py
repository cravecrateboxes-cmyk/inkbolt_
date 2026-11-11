"""kit-airport terminal fit-out: check-in islands (a run with a moving bag belt), self check-in kiosks, the
departures board, the information desk, belt barriers, baggage trolleys; the automated security checkpoint (glass
screens, e-gates, X-ray lanes with moving trays, body-scanner portals, walk-through sensor arches, rising bollards,
roller shutters, the supervisor podium, repack benches, ceiling camera domes and sensor gantries); airside gate
seating, gate podiums, charging pillars, flight-information pylons; duty free (gondolas, the perfume island, the
cash desk, a chocolate pyramid, wall shelving); the Skylark lounge (bar, club chairs, sofas, buffet, reception, the
glass door); the cafe; hanging signs (see ap_base.py for conventions)."""
import math
import random

from ap_base import *  # noqa: F401,F403
import ap_base as B


def legs(m, x0, x1, y0, y1, h, c='chrome', t=0.04):
    for x in (x0, x1 - t):
        for y in (y0, y1 - t):
            m.bx(x, x + t, y, y + t, 0.0, h, c, hull='none', cull='b')


def screen_y(m, g, x0, x1, y, z0, z1, face=-1, frame='black'):
    """a flat screen: a dark bezel box in the model, the lit face in the glow companion g"""
    a, b = sorted((y, y + 0.05 * -face))
    m.bx(x0, x1, a, b, z0, z1, frame, cull='')
    (fq if face < 0 else bq)(g, x0 + 0.03, x1 - 0.03, y + 0.003 * face if face < 0 else b + 0.003, z0 + 0.03, z1 - 0.03, 'scrB')


# ================================================================ check-in
def build_checkin(pal, ao):
    """an island run [3, 6] along Blender X: desks on both faces (y = -3 / +3), weigh belts, the collector belt along
    y = 0 at 0.62 m (a moving line: bags), agent chairs. gA = the airline's counter colour, gB its accent (repainted
    per airline symbol)."""
    BELT = 0.62

    def side(m, s, g):
        """one face of a segment: desk at x -1.5..0.05, weigh belt x 0.05..1.5 (s = -1: the -Y face)"""
        y0 = s * 3.0
        yi = s * 2.25
        a, b = sorted((y0, yi))
        m.bx(-1.5, 0.05, a, b, 0.0, 1.0, 'gA', hull='noside', cull='b')
        m.bx(-1.5, 0.05, min(a, b) - 0.02, max(a, b) + 0.02, 1.0, 1.06, 'wallW', hull='noside')
        Q = fq if s < 0 else bq
        Q(m, -1.5, 0.05, y0 + s * 0.003, 0.12, 0.3, 'gB')
        Q(m, -1.45, 0.0, y0 + s * 0.003, 0.0, 0.1, 'black')
        # the scale: a low belt in a steel frame, the bag tag printer
        a2, b2 = sorted((y0, s * 1.2))
        m.bx(0.05, 1.5, a2, b2, 0.0, 0.42, 'steel', hull='noside', cull='b')
        uq(m, 0.12, 1.43, min(a2, b2) + 0.06, max(a2, b2) - 0.06, 0.423, 'rubber')
        Q(m, 0.05, 1.5, y0 + s * 0.003, 0.3, 0.38, 'gB')
        # monitor on the desk facing the agent, its back to the customer
        m.bx(-0.95, -0.35, s * 2.5 - 0.03, s * 2.5 + 0.03, 1.06, 1.45, 'black', cull='')
        (bq if s < 0 else fq)(g, -0.92, -0.38, s * 2.465, 1.09, 1.42, 'scrB')
        # agent's chair
        yc = s * 1.75
        m.cy((-0.6, yc, 0.0), 0.04, 0.04, 0.5, 'steelD', seg=6, hull='none')
        m.bx(-0.85, -0.35, yc - 0.25, yc + 0.25, 0.5, 0.6, 'black')
        a3, b3 = sorted((yc - s * 0.2, yc - s * 0.27))
        m.bx(-0.85, -0.35, a3, b3, 0.6, 1.05, 'black')

    def belt(m, x0, x1):
        m.bx(x0, x1, -0.55, 0.55, 0.0, BELT - 0.04, 'steelD', hull='noside', cull='b')
        uq(m, x0, x1, -0.45, 0.45, BELT, 'rubber')
        for s in (-1, 1):
            m.bx(x0, x1, s * 0.5 - 0.05, s * 0.5 + 0.05, BELT - 0.04, BELT + 0.12, 'chrome', hull='noside', cull='b')
    for key in ('Mid', 'End', 'Hood'):
        m = new(pal)
        g = new(pal)
        for s in (-1, 1):
            side(m, s, g)
        belt(m, -1.15 if key == 'End' else -1.5, 0.4 if key == 'Hood' else 1.5)
        cols = [cb(-1.5, -3.0, 0.0, 1.5, -2.25, 1.06), cb(-1.5, 2.25, 0.0, 1.5, 3.0, 1.06), cb(0.05, -2.25, 0.0, 1.5, -1.2, 0.42),
                cb(0.05, 1.2, 0.0, 1.5, 2.25, 0.42), cb(-1.5, -0.55, 0.0, 1.5, 0.55, BELT + 0.12)]
        if key == 'End':   # the island's head: a lightbox totem with the airline's colours and CHECK-IN
            m.bx(-1.45, -1.15, -1.0, 1.0, 0.0, 3.2, 'gA', cull='b')
            lq(m, -1.453, -0.9, 0.9, 2.2, 3.1, 'wallW')
            fq(m, -1.42, -1.18, -1.003, 2.3, 3.0, 'gB')
            bq(m, -1.42, -1.18, 1.003, 2.3, 3.0, 'gB')
            text_side(m, 'CHECK-IN', 0.26, -1.456, 0.0, 2.5, 'navy', 'x-', maxw=1.7)
            cols.append(cb(-1.45, -1.0, 0.0, -1.15, 1.0, 3.2))
        if key == 'Hood':   # the belt runs into a hood (the bags drop to the baggage hall below)
            m.bx(0.4, 1.5, -0.7, 0.7, 0.0, 1.5, 'steel', cull='b')
            m.bx(0.38, 0.42, -0.5, 0.5, BELT, 1.3, 'black', hull='none', cull='b')
            for k in range(5):
                lq(m, 0.377, -0.45 + k * 0.2, -0.3 + k * 0.2, BELT + 0.05, 1.25, 'rubber')
            fq(m, 0.5, 1.4, -0.703, 1.1, 1.4, 'sun')
            text_front(m, 'BAGGAGE', 0.14, -0.706, 0.95, 1.18, 'black', font='cond', maxw=0.8)
            bq(m, 0.5, 1.4, 0.703, 1.1, 1.4, 'sun')
            text_back(m, 'BAGGAGE', 0.14, 0.706, 0.95, 1.18, 'black', font='cond', maxw=0.8)
            cols.append(cb(0.4, -0.7, 0.0, 1.5, 0.7, 1.5))
        make('Isl_' + key, m, ao, cols=cols)
        make_glow('Isl_' + key + '_LED', g)
    # bags on the belts (moving-line items; lying flat, front along +X): hard shells and a soft duffel
    for key, c, l, w, h in (('A', 'gB', 0.62, 0.42, 0.24), ('B', 'gA', 0.5, 0.36, 0.22), ('C', 'navy', 0.7, 0.4, 0.26), ('D', 'pPurple', 0.46, 0.34, 0.2)):
        m = new(pal)
        m.bx(-l / 2, l / 2, -w / 2, w / 2, 0.0, h, c, cull='b')
        m.bx(-0.1, 0.1, -0.03, 0.03, h, h + 0.04, 'black', hull='none', cull='b')
        uq(m, -l / 2 + 0.06, -l / 2 + 0.14, -w / 2 + 0.04, w / 2 - 0.04, h + 0.003, 'paper')
        make('Bag_' + key, m, ao)
    # self check-in kiosk (a white pedestal with a tilted screen)
    m = new(pal)
    g = new(pal)
    m.bx(-0.28, 0.28, -0.2, 0.2, 0.0, 1.05, 'wallW', cull='b')
    m.bx(-0.3, 0.3, -0.24, 0.24, 0.0, 0.08, 'steelD', hull='none', cull='b')
    wedge(m, -0.3, 0.3, -0.32, 0.22, 1.05, 1.2, 1.05, 1.6, 'wallW')
    fq(m, -0.28, 0.28, -0.203, 0.6, 0.66, 'sky')
    poly(g, [(-0.24, -0.3, 1.22), (0.24, -0.3, 1.22), (0.24, 0.16, 1.55), (-0.24, 0.16, 1.55)], 'scrB', (0, -0.6, 0.8))
    m.bx(-0.12, 0.12, -0.21, -0.2, 0.3, 0.38, 'black', hull='none', cull='k')
    make('Kiosk', m, ao, cols=[cb(-0.3, -0.32, 0.0, 0.3, 0.24, 1.6)])
    make_glow('Kiosk_LED', g)
    # the departures board [10, 2]: a double-sided flight board on two legs, lit rows (glow companion)
    m = new(pal)
    g = new(pal)
    for x in (-4.3, 4.3):
        m.bx(x - 0.18, x + 0.18, -0.3, 0.3, 0.0, 2.8, 'steelD', cull='b')
        m.bx(x - 0.3, x + 0.3, -0.45, 0.45, 0.0, 0.12, 'stoneD', hull='none', cull='b')
    m.bx(-4.6, 4.6, -0.3, 0.3, 2.8, 6.4, 'black')
    for s in (-1, 1):
        Q = fq if s < 0 else bq
        T = text_front if s < 0 else text_back
        y = s * 0.303
        Q(m, -4.5, 4.5, y, 5.75, 6.3, 'sun')
        T(m, 'DEPARTURES', 0.42, s * 0.306, 2.2 * s, 5.82, 'black', maxw=4.0)
        T(m, 'SKYLARK AIR  -  MERIDIAN', 0.18, s * 0.306, -2.0 * s, 5.93, 'black', font='cond', maxw=3.8)
        for r in range(9):
            z = 5.45 - r * 0.3
            for (u0, u1, c) in ((-4.4, -3.6, 'sun'), (-3.5, -1.0, 'paper'), (-0.9, 0.2, 'paper'), (0.3, 1.0, 'sun'), (1.1, 2.4, 'paper'),
                                (2.5, 4.4, ('scrG', 'scrG', 'sun', 'scrG', 'scrR', 'scrG', 'sun', 'scrG', 'scrG')[r])):
                x0, x1 = (u0, u1) if s < 0 else (-u1, -u0)
                Q(g, x0, x1, s * 0.306, z - 0.09, z + 0.09, c)
    make('Board', m, ao, cols=[cb(-4.5, -0.3, 0.0, -4.1, 0.3, 2.8), cb(4.1, -0.3, 0.0, 4.5, 0.3, 2.8)])
    make_glow('Board_LED', g)
    # information desk [4, 2]: a curved front in panels, a timber top, the blue i sign
    m = new(pal)
    n = 6
    for i in range(n):
        a0, a1 = math.pi * i / n, math.pi * (i + 1) / n
        p0 = (math.cos(a0) * 1.9, -0.3 - math.sin(a0) * 0.65)
        p1 = (math.cos(a1) * 1.9, -0.3 - math.sin(a1) * 0.65)
        slab(m, [(p0[0], p0[1]), (p1[0], p1[1]), (p1[0] * 0.8, p1[1] * 0.6 + 0.3), (p0[0] * 0.8, p0[1] * 0.6 + 0.3)], 0.0, 1.05, 'wallW', hull='noside')
    slab(m, [(1.95, -0.3), (1.0, -1.0), (-1.0, -1.0), (-1.95, -0.3), (-1.95, 0.9), (1.95, 0.9)], 1.05, 1.12, 'wood')
    m.bx(-1.9, 1.9, 0.5, 0.9, 0.0, 1.05, 'wallL', cull='b')
    m.cy((0.0, 0.7, 1.12), 0.04, 0.04, 1.5, 'steelD', seg=6, hull='none')
    m.bx(-0.45, 0.45, 0.65, 0.75, 2.4, 3.0, 'sky')
    text_front(m, 'i', 0.42, 0.647, -0.18, 2.5, 'paper')
    text_front(m, 'INFO', 0.16, 0.647, 0.18, 2.62, 'paper', maxw=0.4)
    text_back(m, 'INFORMATION', 0.12, 0.753, 0.0, 2.65, 'paper', maxw=0.8)
    make('InfoDesk', m, ao, cols=[cb(-1.2, -0.85, 0.0, 1.2, 0.9, 1.12), cb(-1.95, -0.55, 0.0, -1.2, 0.9, 1.12), cb(1.2, -0.55, 0.0, 1.95, 0.9, 1.12)])
    # belt barrier (stanchions + retractable belt; modelled along Blender Y, the run placer links half modules)
    def tape(m, y0, y1):
        m.bx(-0.02, 0.02, y0, y1, 0.86, 0.94, 'navy', hull='none', cull='')
    m = new(pal); tape(m, -0.5, 0.5); make('BeltFull', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.5, 0.95)])
    m = new(pal); tape(m, -0.5, -0.04); make('BeltHalf', m, ao, cols=[cb(-0.04, -0.5, 0.0, 0.04, 0.0, 0.95)])
    m = new(pal)
    m.cy((0, 0, 0), 0.17, 0.17, 0.03, 'steelD', seg=6, hull='none')
    m.cy((0, 0, 0.03), 0.04, 0.04, 0.95, 'chrome', seg=6)
    make('BeltPost', m, ao, cols=[cb(-0.17, -0.17, 0.0, 0.17, 0.17, 1.0)])
    # bench [4, 1] (Blender X along it): timber slats on two steel legs, backless (seen from both sides)
    m = new(pal)
    for x in (-1.5, 1.5):
        m.bx(x - 0.05, x + 0.05, -0.22, 0.22, 0.0, 0.42, 'steelD', cull='b')
    m.bx(-1.95, 1.95, -0.25, 0.25, 0.42, 0.48, 'wood', hull='noside')
    for k in range(1, 5):
        uq(m, -1.95, 1.95, -0.25 + k * 0.1 - 0.008, -0.25 + k * 0.1 + 0.008, 0.483, 'woodD')
    make('Bench', m, ao, cols=[cb(-1.95, -0.25, 0.0, 1.95, 0.25, 0.48)])
    # baggage trolley (front -Y: the handle at +Y), with a suitcase on some
    for key in ('', 'B'):
        m = new(pal)
        m.bx(-0.28, 0.28, -0.45, 0.4, 0.2, 0.24, 'chrome', hull='none')
        for x in (-0.25, 0.25):
            m.bm_((x, 0.36, 0.24), (x, 0.5, 1.0), 0.03, 'chrome')
            for y in (-0.38, 0.32):
                m.cy((x - 0.02, y, 0.08), 0.08, 0.08, 0.04, 'tire', seg=6, rot=(0, 90, 0), hull='none')
        m.bx(-0.3, 0.3, 0.47, 0.53, 0.97, 1.03, 'gA', hull='none')
        m.bx(-0.26, 0.26, -0.47, -0.43, 0.24, 0.55, 'chrome', hull='none', cull='')
        if key == 'B':
            m.bx(-0.24, 0.24, -0.42, 0.34, 0.24, 0.5, 'gB', cull='b')
            m.bx(-0.2, 0.18, -0.36, 0.18, 0.5, 0.68, 'navy', cull='b')
        make('Trolley' + key, m, ao, cols=[cb(-0.3, -0.45, 0.0, 0.3, 0.5, 0.7 if key else 0.55)])


# ================================================================ security
def build_security(pal, ao):
    H3 = 2.8

    # glass screen (modelled along Blender Y): base channel, top rail, open glazing with a frosted band and glints
    def glass(m, y0, y1):
        m.bx(-0.05, 0.05, y0, y1, 0.0, 0.1, 'steelD', hull='noend', cull='b')
        m.bx(-0.04, 0.04, y0, y1, H3 - 0.07, H3, 'steelD', hull='noend', cull='')
        for s in (-1, 1):
            x = s * 0.02
            (lq if s < 0 else rq)(m, x, y0, y1, 1.1, 1.3, 'glassL')
            (lq if s < 0 else rq)(m, x, y0, y1, 1.36, 1.4, 'sky')
            if y1 - y0 > 0.6:
                poly(m, [(x, -0.25, 1.7), (x, -0.1, 1.7), (x, 0.25, 2.3), (x, 0.1, 2.3)], 'glassL', (s, 0, 0))
    m = new(pal); glass(m, -0.5, 0.5); make('GlassFull', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.5, H3)])
    m = new(pal); glass(m, -0.5, -0.07); make('GlassHalf', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.0, H3)])
    m = new(pal)
    m.bx(-0.07, 0.07, -0.07, 0.07, 0.0, H3 + 0.02, 'steelD', cull='b')
    make('GlassPost', m, ao, cols=[cb(-0.07, -0.07, 0.0, 0.07, 0.07, H3)])
    # automated e-gates [3, 2] (Blender X across: three cabinets, two lanes of 1.3 m; the open flaps folded into the
    # cabinets; passengers walk along Y): a boarding-pass reader and a camera mast on each; glow: arrows / readers
    m = new(pal)
    g = new(pal)
    for x in (-1.37, 0.0, 1.37):
        m.bx(x - 0.11, x + 0.11, -0.95, 0.95, 0.0, 1.0, 'wallW', cull='b')
        m.bx(x - 0.12, x + 0.12, -0.97, 0.97, 1.0, 1.05, 'steelD', hull='none')
        for s in (-1, 1):
            if (x < 1.0 and s > 0) or (x > -1.0 and s < 0):
                (rq if s > 0 else lq)(m, x + s * 0.113, -0.9, 0.9, 0.55, 0.62, 'sky')
                m.bx(x + s * 0.11, x + s * 0.2, -0.05, 0.25, 0.75, 1.0, 'glass', hull='none', cull='')
        m.bx(x - 0.03, x + 0.03, 0.75, 0.81, 1.05, 1.7, 'steelD', hull='none', cull='b')
        m.bx(x - 0.08, x + 0.08, 0.7, 0.86, 1.7, 1.86, 'black')
        fq(g, x - 0.06, x + 0.06, -0.973, 0.82, 0.96, 'scrG')
        uq(g, x - 0.08, x + 0.08, -0.85, -0.6, 1.053, 'scrB')
        fq(g, x - 0.04, x + 0.04, 0.697, 1.74, 1.82, 'scrR')
    make('EGate', m, ao, cols=[cb(x - 0.12, -0.97, 0.0, x + 0.12, 0.97, 1.05) for x in (-1.37, 0.0, 1.37)])
    make_glow('EGate_LED', g)
    # X-ray lane [3, 2] x 3 (a run along Blender X; the trays ride a moving line at 0.86 m along local +X)
    BY = 0.86

    def rollers(m, x0, x1, y0=-0.45, y1=0.45, z0=0.0):
        m.bx(x0, x1, y0, y1, z0, BY - 0.05, 'steel', hull='noside', cull='b' if z0 == 0.0 else '')
        uq(m, x0, x1, y0 + 0.04, y1 - 0.04, BY, 'rubber')
        for s in (-1, 1):
            m.bx(x0, x1, (y1 if s > 0 else y0) - 0.04, (y1 if s > 0 else y0) + 0.04, BY - 0.05, BY + 0.06, 'chrome', hull='noside', cull='b')
    # In: the divest bench (wider: trays slide off a stack), the tray return under it, a screen with instructions
    m = new(pal)
    g = new(pal)
    rollers(m, -1.5, 1.5, -0.45, 0.85, z0=0.45)
    m.bx(-1.45, 1.45, -0.4, 0.8, 0.12, 0.18, 'steelD', hull='none', cull='')
    for x in (-1.42, 1.38):
        for y in (-0.42, 0.78):
            m.bx(x, x + 0.04, y, y + 0.04, 0.0, 0.45, 'steelD', hull='none', cull='bt')
    for k in range(4):
        x = -1.0 + k * 0.62
        m.bx(x - 0.28, x + 0.28, -0.2, 0.6, 0.18, 0.3, 'belly', hull='none', cull='b')
    for k in range(4):
        m.bx(-1.4, -1.0, 0.25, 0.8, BY + k * 0.06, BY + k * 0.06 + 0.05, 'steel' if k % 2 else 'belly', hull='none', cull='b')
    m.cy((0.6, 0.75, BY), 0.03, 0.03, 0.9, 'steelD', seg=6, hull='none')
    screen_y(m, g, 0.25, 0.95, 0.74, BY + 0.9, BY + 1.35, face=-1)
    make('Xr_In', m, ao, cols=[cb(-1.5, -0.45, 0.0, 1.5, 0.85, BY + 0.06)])
    make_glow('Xr_In_LED', g)
    # Tunnel: the X-ray machine with lead curtains, the operator's desk and screens on the +Y side
    m = new(pal)
    g = new(pal)
    rollers(m, -1.5, 1.5)
    m.bx(-1.1, 1.1, -0.6, 0.6, 0.0, BY - 0.06, 'wallW', hull='noside', cull='b')
    m.bx(-1.1, 1.1, -0.6, 0.6, BY + 0.62, 1.75, 'wallW', cull='')
    m.bx(-1.1, 1.1, -0.6, -0.45, BY - 0.05, BY + 0.62, 'wallW', hull='noside', cull='')
    m.bx(-1.1, 1.1, 0.45, 0.6, BY - 0.05, BY + 0.62, 'wallW', hull='noside', cull='')
    fq(m, -1.1, 1.1, -0.603, 1.45, 1.55, 'sky')
    bq(m, -1.1, 1.1, 0.603, 1.45, 1.55, 'sky')
    for s in (-1, 1):
        x = s * 1.1
        for k in range(5):
            yy = -0.4 + k * 0.18
            (rq if s > 0 else lq)(m, x + s * 0.003, yy, yy + 0.15, BY + 0.06, BY + 0.6, 'rubber')
    text_front(m, 'CT-9 SCAN', 0.16, -0.606, 0.0, 1.2, 'navy', font='cond', maxw=1.2)
    m.bx(-0.2, 0.6, 0.6, 1.0, 0.0, 0.85, 'steelD', cull='b')
    screen_y(m, g, -0.15, 0.5, 0.95, 0.9, 1.35, face=1)
    make('Xr_Tunnel', m, ao, cols=[cb(-1.5, -0.6, 0.0, 1.5, 0.6, 1.75), cb(-0.2, 0.6, 0.0, 0.6, 1.0, 1.0)])
    make_glow('Xr_Tunnel_LED', g)
    # Out: exit rollers, the reject belt branching to a search table, a recycling bin for trays
    m = new(pal)
    rollers(m, -1.5, 1.5)
    m.bx(0.0, 1.5, 0.5, 0.95, 0.0, BY - 0.02, 'steel', hull='noside', cull='b')
    uq(m, 0.05, 1.45, 0.55, 0.9, BY - 0.017, 'wallL')
    m.bx(-1.3, -0.7, 0.55, 0.95, 0.0, 0.5, 'navy', cull='b')
    uq(m, -1.25, -0.75, 0.6, 0.9, 0.503, 'black')
    make('Xr_Out', m, ao, cols=[cb(-1.5, -0.45, 0.0, 1.5, 0.45, BY + 0.06), cb(0.0, 0.45, 0.0, 1.5, 0.95, BY), cb(-1.3, 0.45, 0.0, -0.7, 0.95, 0.5)])
    # trays (moving-line items): a grey tray with a bag, one with a laptop and shoes, an empty one
    for key in ('A', 'B', 'C'):
        m = new(pal)
        m.bx(-0.3, 0.3, -0.24, 0.24, 0.0, 0.1, 'belly', cull='b')
        uq(m, -0.26, 0.26, -0.2, 0.2, 0.103, 'steel')
        if key == 'A':
            m.bx(-0.22, 0.2, -0.17, 0.15, 0.1, 0.32, 'gA', cull='b')
            m.bx(-0.06, 0.06, -0.02, 0.02, 0.32, 0.36, 'black', hull='none', cull='b')
        elif key == 'B':
            m.bx(-0.24, 0.06, -0.18, 0.12, 0.1, 0.13, 'black', cull='b')
            m.bx(0.1, 0.24, -0.18, 0.02, 0.1, 0.18, 'leather', cull='b')
            m.bx(0.1, 0.24, 0.04, 0.2, 0.1, 0.18, 'leather', cull='b')
        make('Tray_' + key, m, ao)
    # body-scanner portal [2, 2]: a round booth of two curved glass halves on a white plinth, scanning arms inside,
    # a lit ring on its crown; open toward -Y and +Y (walk-through)
    m = new(pal)
    g = new(pal)
    m.cy((0, 0, 0), 0.95, 0.95, 0.08, 'steelD', seg=16)
    m.cy((0, 0, 2.25), 0.95, 0.9, 0.3, 'wallW', seg=16)
    for s in (-1, 1):
        for i in range(4):
            a0 = math.radians(25 + i * 32.5)
            a1 = math.radians(25 + (i + 1) * 32.5)
            p0 = (s * math.sin(a0) * 0.92, -math.cos(a0) * 0.92)
            p1 = (s * math.sin(a1) * 0.92, -math.cos(a1) * 0.92)
            slab(m, [p0, p1, (p1[0] * 0.92, p1[1] * 0.92), (p0[0] * 0.92, p0[1] * 0.92)], 0.08, 2.25, 'wallW' if i in (0, 3) else 'glassL', hull='full' if i in (0, 3) else 'none')
        m.bx(s * 0.8 - 0.06, s * 0.8 + 0.06, -0.12, 0.12, 0.08, 2.25, 'sky', cull='bt')
    m.bx(-0.5, 0.5, -0.04, 0.04, 2.0, 2.25, 'steel', hull='none', cull='t')
    ring(g, 0, 0, 2.553, 0.5, 0.85, 'scrB', seg=16)
    for s in (-1, 1):
        (rq if s < 0 else lq)(g, s * 0.735, -0.1, 0.1, 0.4, 2.0, 'scrG')
    make('Scanner', m, ao, cols=[cb(s * 0.7, -0.5, 0.0, s * 0.93, 0.5, 2.25) for s in (-1, 1)] + [cb(-0.9, -0.4, 2.25, 0.9, 0.4, 2.55)])
    make_glow('Scanner_LED', g)
    # walk-through sensor arch [1, 2] (passengers walk along Y through it): two posts and a header with LED bars
    m = new(pal)
    g = new(pal)
    for x in (-0.48, 0.48):
        m.bx(x - 0.1, x + 0.1, -0.35, 0.35, 0.0, 2.2, 'chrome', cull='b')
    m.bx(-0.58, 0.58, -0.35, 0.35, 2.2, 2.4, 'chrome')
    fq(m, -0.58, 0.58, -0.353, 2.24, 2.36, 'navy')
    for x in (-0.48, 0.48):
        (rq if x < 0 else lq)(g, x + (0.103 if x < 0 else -0.103), -0.25, 0.25, 0.3, 2.0, 'scrG')
    for s in (-1, 1):
        (fq if s < 0 else bq)(g, -0.3, 0.3, s * 0.356, 2.27, 2.33, 'scrG')
    make('Arch', m, ao, cols=[cb(-0.58, -0.35, 0.0, -0.38, 0.35, 2.4), cb(0.38, -0.35, 0.0, 0.58, 0.35, 2.4)])
    make_glow('Arch_LED', g)
    # rising bollard (a steel post with a lit red ring) and the security shutters (rolled up; one half down)
    m = new(pal)
    g = new(pal)
    m.cy((0, 0, 0), 0.24, 0.24, 0.03, 'steelD', seg=10, hull='none')
    m.cy((0, 0, 0.03), 0.14, 0.14, 0.9, 'chrome', seg=8)
    g.cy((0, 0, 0.75), 0.144, 0.144, 0.06, 'scrR', seg=8, caps=False, hull='none')
    make('Bollard', m, ao, cols=[cb(-0.15, -0.15, 0.0, 0.15, 0.15, 0.93)])
    make_glow('Bollard_LED', g)
    for key in ('Up', 'Half'):
        m = new(pal)
        g = new(pal)
        for x in (-1.43, 1.43):
            m.bx(x - 0.06, x + 0.06, -0.08, 0.08, 0.0, 3.0, 'steelD', cull='b')
        m.bx(-1.55, 1.55, -0.25, 0.25, 3.0, 3.5, 'steel')
        fq(m, -1.55, 1.55, -0.253, 3.05, 3.15, 'sun')
        bq(m, -1.55, 1.55, 0.253, 3.05, 3.15, 'sun')
        cols = [cb(-1.49, -0.08, 0.0, -1.37, 0.08, 3.0), cb(1.37, -0.08, 0.0, 1.49, 0.08, 3.0)]
        if key == 'Half':   # lowered to 1.0 m: slats, a hazard bottom bar (you can shoot and crawl under it)
            for i in range(8):
                z = 1.15 + i * 0.235
                m.bx(-1.39, 1.39, -0.04, 0.04, z, z + 0.22, 'chrome' if i % 2 else 'steel', hull='noside')
            m.bx(-1.39, 1.39, -0.05, 0.05, 1.0, 1.15, 'sun', hull='noside')
            for k in range(6):
                fq(m, -1.35 + k * 0.48, -1.15 + k * 0.48, -0.053, 1.0, 1.15, 'black')
            cols.append(cb(-1.39, -0.05, 1.0, 1.39, 0.05, 3.0))
        fq(g, -0.2, 0.2, -0.256, 3.25, 3.4, 'scrR' if key == 'Half' else 'scrG')
        bq(g, -0.2, 0.2, 0.256, 3.25, 3.4, 'scrR' if key == 'Half' else 'scrG')
        make('Shutter' + key, m, ao, cols=cols)
        make_glow('Shutter' + key + '_LED', g)
    # supervisor podium: a raised desk with screens
    m = new(pal)
    g = new(pal)
    m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 1.15, 'navy', cull='b')
    m.bx(-0.5, 0.5, -0.4, 0.4, 1.15, 1.2, 'wallW')
    fq(m, -0.45, 0.45, -0.353, 0.9, 1.0, 'sky')
    text_front(m, 'SECURITY', 0.1, -0.356, 0.0, 0.5, 'paper', maxw=0.7)
    for x in (-0.22, 0.22):
        m.bx(x - 0.2, x + 0.2, 0.1, 0.16, 1.2, 1.5, 'black', cull='')
        fq(g, x - 0.17, x + 0.17, 0.097, 1.23, 1.47, 'scrB')
    make('Podium', m, ao, cols=[cb(-0.5, -0.4, 0.0, 0.5, 0.4, 1.2)])
    make_glow('Podium_LED', g)
    # repack bench [4, 1]
    m = new(pal)
    m.bx(-1.95, 1.95, -0.35, 0.35, 0.82, 0.88, 'steel')
    m.bx(-1.71, 1.71, -0.27, 0.27, 0.2, 0.25, 'steelD', hull='none', cull='')
    for x in (-1.75, 1.75):
        m.bx(x - 0.04, x + 0.04, -0.3, 0.3, 0.0, 0.82, 'steelD', cull='b')
    m.bx(-1.2, -0.7, -0.24, 0.2, 0.88, 0.98, 'belly', cull='b')
    make('Repack', m, ao, cols=[cb(-1.95, -0.35, 0.0, 1.95, 0.35, 0.88)])
    # ceiling camera dome (hangs from the 14 m ceiling on a drop rod) and the sensor gantry [2, 8] (a truss across a
    # lane at 5 m: lidar heads, cameras, status bars) -- both hang from z = 0
    m = new(pal)
    g = new(pal)
    m.cy((0, 0, -3.0), 0.02, 0.02, 3.0, 'steelD', seg=4, hull='none', caps=False)
    m.cy((0, 0, -3.12), 0.22, 0.22, 0.12, 'wallW', seg=8)
    m.sp((0, 0, -3.12), 0.18, 'black', seg=(8, 4), scale=(1, 1, 0.8))
    g.cy((0, 0, -3.1), 0.225, 0.225, 0.03, 'scrR', seg=8, caps=False, hull='none')
    make('Cam', m, ao)
    make_glow('Cam_LED', g)
    m = new(pal)
    g = new(pal)
    for x in (-0.4, 0.4):
        m.bx(x - 0.015, x + 0.015, -3.9, -3.87, -8.6, -0.01, 'steelD', hull='none', cull='tb')
        m.bx(x - 0.015, x + 0.015, 3.87, 3.9, -8.6, -0.01, 'steelD', hull='none', cull='tb')
    m.bx(-0.45, 0.45, -3.95, 3.95, -9.0, -8.6, 'wallW', hull='full')
    for k in range(4):
        y = -3.0 + k * 2.0
        m.bx(-0.16, 0.16, y - 0.16, y + 0.16, -9.3, -9.0, 'black')
        m.cy((0.0, y, -9.4), 0.12, 0.12, 0.1, 'steelD', seg=8)
        dq(g, -0.12, 0.12, y - 0.12, y + 0.12, -9.303, 'scrB')
    for s in (-1, 1):
        (lq if s < 0 else rq)(g, s * 0.453, -3.8, 3.8, -8.84, -8.76, 'scrG')
    make('Gantry', m, ao)
    make_glow('Gantry_LED', g)


# ================================================================ airside: gates, seating
def build_gates(pal, ao):
    # seat row [4, 1] (Blender X along the row, seats face -Y): four fabric seats with armrests on a chrome beam
    m = new(pal)
    for x in (-1.6, 1.6):
        m.bx(x - 0.04, x + 0.04, -0.25, 0.25, 0.0, 0.38, 'chrome', hull='none', cull='b')
    m.bx(-1.95, 1.95, -0.3, 0.2, 0.38, 0.46, 'fab', hull='noside')
    wedge(m, -1.95, 1.95, 0.18, 0.28, 0.46, 1.0, 0.46, 1.05, 'fab', hull='noside')
    for k in range(4):
        x = -1.5 + k * 1.0
        uq(m, x - 0.4, x + 0.4, -0.26, 0.16, 0.463, 'fabD')
    for k in range(5):
        x = max(-1.92, min(1.92, -2.0 + k * 1.0))
        m.bx(x - 0.03, x + 0.03, -0.28, 0.14, 0.466, 0.68, 'black', hull='none', cull='b')
    make('Seats', m, ao, cols=[cb(-1.95, -0.32, 0.0, 1.95, 0.3, 0.5), cb(-1.95, 0.15, 0.0, 1.95, 0.3, 1.05)])
    # gate podium [3, 1] (front -Y: the passenger side): a curved counter, two screens, a boarding-pass reader
    m = new(pal)
    g = new(pal)
    m.bx(-1.4, 1.4, -0.3, 0.35, 0.0, 1.05, 'wallW', cull='b')
    m.bx(-1.45, 1.45, -0.4, 0.4, 1.05, 1.1, 'wood')
    fq(m, -1.4, 1.4, -0.303, 0.75, 0.85, 'sky')
    for x in (-0.6, 0.6):
        m.bx(x - 0.3, x + 0.3, 0.1, 0.16, 1.1, 1.45, 'black', cull='')
        bq(g, x - 0.27, x + 0.27, 0.163, 1.13, 1.42, 'scrB')
    m.cy((1.2, -0.2, 1.1), 0.02, 0.02, 0.15, 'steelD', seg=4, hull='none')
    m.bx(1.1, 1.3, -0.3, -0.1, 1.25, 1.33, 'black')
    m.bx(-1.3, 1.3, 0.4, 0.5, 0.0, 2.6, 'sky', cull='b')
    fq(g, -1.2, 1.2, 0.397, 1.8, 2.5, 'screen')
    text_front(g, 'BOARDING', 0.22, 0.394, 0.0, 2.2, 'sun', maxw=1.6)
    text_front(g, 'SKYLARK AIR', 0.13, 0.394, 0.0, 1.95, 'paper', maxw=1.4)
    make('GatePod', m, ao, cols=[cb(-1.45, -0.4, 0.0, 1.45, 0.5, 1.1), cb(-1.3, 0.4, 0.0, 1.3, 0.5, 2.6)])
    make_glow('GatePod_LED', g)
    # charging pillar and a flight-information pylon (two screens back to back on a post)
    m = new(pal)
    g = new(pal)
    m.bx(-0.18, 0.18, -0.18, 0.18, 0.0, 1.1, 'wallW', cull='b')
    m.bx(-0.2, 0.2, -0.2, 0.2, 1.1, 1.16, 'sky')
    for s in (-1, 1):
        Q = fq if s < 0 else bq
        Q(m, -0.12, 0.12, s * 0.183, 0.7, 0.95, 'black')
        Q(g, -0.08, 0.08, s * 0.186, 0.98, 1.05, 'scrG')
        (lq if s < 0 else rq)(m, s * 0.183, -0.12, 0.12, 0.7, 0.95, 'black')
    make('Charge', m, ao, cols=[cb(-0.2, -0.2, 0.0, 0.2, 0.2, 1.16)])
    make_glow('Charge_LED', g)
    m = new(pal)
    g = new(pal)
    m.bx(-0.08, 0.08, -0.08, 0.08, 0.0, 1.6, 'steelD', cull='b')
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.05, 'steelD', hull='none', cull='b')
    m.bx(-0.45, 0.45, -0.1, 0.1, 1.6, 2.9, 'black')
    for s in (-1, 1):
        Q = fq if s < 0 else bq
        Q(g, -0.4, 0.4, s * 0.103, 1.65, 2.85, 'screen')
        for r in range(6):
            z = 2.7 - r * 0.18
            for (u0, u1, c) in ((-0.36, -0.2, 'sun'), (-0.16, 0.2, 'paper'), (0.24, 0.36, ('scrG', 'scrG', 'sun', 'scrR', 'scrG', 'scrG')[r])):
                x0, x1 = (u0, u1) if s < 0 else (-u1, -u0)
                Q(g, x0, x1, s * 0.106, z - 0.05, z + 0.05, c)
    make('FIDS', m, ao, cols=[cb(-0.45, -0.1, 0.0, 0.45, 0.1, 2.9)])
    make_glow('FIDS_LED', g)


# ================================================================ duty free and the cafe
def build_shops(pal, ao):
    rnd = random.Random(7)
    # gondola [3, 1] (Blender X along it): three shelves of goods on both faces, a lit header (goods cells repainted)
    m = new(pal)
    m.bx(-1.45, 1.45, -0.08, 0.08, 0.0, 1.6, 'wallW', cull='b')
    m.bx(-1.5, 1.5, -0.45, 0.45, 0.0, 0.12, 'steelD', cull='b')
    for s in (-1, 1):
        for z in (0.5, 0.95, 1.4):
            a, b = sorted((s * 0.08, s * 0.42))
            m.bx(-1.45, 1.45, a, b, z - 0.03, z, 'wallL', hull='none', cull='')
            c0 = GOODS[(int(z * 10) + (s > 0)) % 4]
            m.bx(-1.4, 1.4, s * 0.1, s * 0.34, z, z + 0.26, c0, cull='b', hull='noside')
            for k in range(3):
                x = -0.95 + k * 0.95
                c = GOODS[(k + int(z * 10) + (s > 0) + 1) % 4]
                (fq if s < 0 else bq)(m, x - 0.4, x + 0.4, s * 0.343, z + 0.02, z + 0.24, c)
    m.bx(-1.5, 1.5, -0.1, 0.1, 1.6, 1.9, 'navy')
    for s in (-1, 1):
        (text_front if s < 0 else text_back)(m, 'DUTY FREE', 0.18, s * 0.103, 0.0, 1.66, 'sun', maxw=2.0)
    make('Gondola', m, ao, cols=[cb(-1.5, -0.45, 0.0, 1.5, 0.45, 1.9)])
    # wall shelving [3, 1] (back to a wall at +Y): liquor and perfume, lit shelves
    m = new(pal)
    m.bx(-1.5, 1.5, 0.1, 0.5, 0.0, 2.4, 'woodD', cull='b')
    for z in (0.6, 1.1, 1.6):
        m.bx(-1.45, 1.45, -0.3, 0.1, z - 0.03, z, 'glassL', hull='none', cull='')
        for k in range(9):
            x = -1.3 + k * 0.32
            c = GOODS[(k + int(z * 7)) % 4]
            fq(m, x - 0.06, x + 0.06, 0.097, z, z + (0.3 if k % 3 else 0.22), c)
    m.bx(-1.5, 1.5, -0.35, 0.1, 0.0, 0.5, 'woodD', cull='b')
    m.bx(-1.5, 1.5, -0.3, 0.1, 2.2, 2.4, 'wood', hull='noside')
    make('Shelf', m, ao, cols=[cb(-1.5, -0.35, 0.0, 1.5, 0.5, 2.4)])
    # perfume island [2, 2]: a glass-topped counter, testers, a mirror column
    m = new(pal)
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.85, 'wallW', cull='b')
    m.bx(-0.95, 0.95, -0.95, 0.95, 0.85, 0.9, 'glass', hull='full')
    for k in range(8):
        a = k * math.pi / 4
        x, y = math.cos(a) * 0.6, math.sin(a) * 0.6
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.9, 1.06, GOODS[k % 4], hull='none', cull='b')
    m.cy((0, 0, 0.9), 0.18, 0.18, 1.5, 'chrome', seg=6)
    m.cy((0, 0, 2.4), 0.32, 0.32, 0.12, 'pPink', seg=8)
    make('Perfume', m, ao, cols=[cb(-0.95, -0.95, 0.0, 0.95, 0.95, 0.9), cb(-0.2, -0.2, 0.9, 0.2, 0.2, 2.5)])
    # cash desk [3, 2]: a white desk with the till and bag shelf, front -Y
    m = new(pal)
    g = new(pal)
    m.bx(-1.45, 1.45, -0.6, 0.2, 0.0, 1.0, 'wallW', cull='b')
    m.bx(-1.5, 1.5, -0.65, 0.25, 1.0, 1.05, 'wood')
    fq(m, -1.45, 1.45, -0.603, 0.2, 0.3, 'navy')
    for x in (-0.6, 0.6):
        m.bx(x - 0.18, x + 0.18, -0.25, -0.05, 1.05, 1.12, 'black', hull='none')
        m.bx(x - 0.2, x + 0.2, 0.0, 0.05, 1.12, 1.4, 'black', cull='')
        bq(g, x - 0.17, x + 0.17, 0.053, 1.15, 1.37, 'scrB')
    m.bx(-1.4, 1.4, 0.5, 0.9, 0.0, 0.9, 'wood', cull='b')
    make('CashDesk', m, ao, cols=[cb(-1.5, -0.65, 0.0, 1.5, 0.25, 1.05), cb(-1.4, 0.5, 0.0, 1.4, 0.9, 0.9)])
    make_glow('CashDesk_LED', g)
    # chocolate pyramid [2, 2]: stepped boxes on a round plinth
    m = new(pal)
    m.cy((0, 0, 0), 0.92, 0.92, 0.3, 'navy', seg=12)
    for k, r in enumerate((0.75, 0.55, 0.35)):
        z = 0.3 + k * 0.3
        m.bx(-r, r, -r, r, z, z + 0.3, ('gA', 'gC', 'gB')[k], cull='b')
        fq(m, -r * 0.5, r * 0.5, -r - 0.003, z + 0.1, z + 0.2, 'paper')
    m.bx(-0.15, 0.15, -0.15, 0.15, 1.2, 1.5, 'sun', cull='b')
    make('Choc', m, ao, cols=[cb(-0.92, -0.92, 0.0, 0.92, 0.92, 0.6), cb(-0.55, -0.55, 0.6, 0.55, 0.55, 1.2)])
    # the cafe [4, 2] (on the mezzanine): a timber counter with an espresso machine, a menu board, pastry case
    m = new(pal)
    g = new(pal)
    m.bx(-1.95, 1.95, -0.6, 0.1, 0.0, 1.05, 'wood', cull='b')
    m.bx(-2.0, 2.0, -0.65, 0.15, 1.05, 1.1, 'wallW')
    fq(m, -1.95, 1.95, -0.603, 0.1, 0.2, 'black')
    m.bx(-1.4, -0.6, -0.35, 0.0, 1.1, 1.55, 'chrome')
    fq(m, -1.35, -0.65, -0.353, 1.35, 1.48, 'red')
    m.bx(0.3, 1.6, -0.55, 0.0, 1.1, 1.45, 'glass', hull='full')
    for k in range(4):
        m.bx(0.4 + k * 0.3, 0.6 + k * 0.3, -0.45, -0.15, 1.12, 1.22, ('leather', 'cream', 'sun', 'leather')[k], hull='none', cull='b')
    m.bx(-1.95, 1.95, 0.6, 0.9, 0.0, 2.6, 'woodD', cull='b')
    fq(m, -1.95, 1.95, 0.597, 1.0, 1.05, 'wood')
    fq(g, -1.8, 1.8, 0.594, 1.7, 2.5, 'screen')
    text_front(g, 'SKYBEAN', 0.36, 0.591, -0.6, 2.05, 'sun', maxw=2.0)
    text_front(g, 'COFFEE', 0.16, 0.591, -0.6, 1.82, 'paper', maxw=1.2)
    for r in range(4):
        fq(g, 0.6, 1.6, 0.591, 2.3 - r * 0.15, 2.36 - r * 0.15, 'paper')
    make('Cafe', m, ao, cols=[cb(-2.0, -0.65, 0.0, 2.0, 0.15, 1.1), cb(-1.95, 0.6, 0.0, 1.95, 0.9, 2.6)])
    make_glow('Cafe_LED', g)
    # cafe table with two chairs [2, 2]
    m = new(pal)
    m.cy((0, 0, 0), 0.25, 0.25, 0.03, 'steelD', seg=8, hull='none')
    m.cy((0, 0, 0.03), 0.04, 0.04, 0.7, 'chrome', seg=6, hull='none')
    m.cy((0, 0, 0.73), 0.4, 0.4, 0.04, 'wallW', seg=10)
    for s in (-1, 1):
        y = s * 0.68
        m.bx(-0.2, 0.2, y - 0.2, y + 0.2, 0.44, 0.48, 'wood')
        yb = y + s * 0.2
        a, b = sorted((yb, yb + s * 0.04))
        m.bx(-0.2, 0.2, a, b, 0.48, 0.85, 'wood', hull='none', cull='')
        for x in (-0.17, 0.17):
            for yy in (y - 0.17, y + 0.17):
                m.bx(x - 0.015, x + 0.015, yy - 0.015, yy + 0.015, 0.0, 0.44, 'black', hull='none', cull='b')
    make('CafeTable', m, ao, cols=[cb(-0.4, -0.4, 0.0, 0.4, 0.4, 0.77), cb(-0.2, 0.48, 0.0, 0.2, 0.92, 0.6), cb(-0.2, -0.92, 0.0, 0.2, -0.48, 0.6)])


# ================================================================ the Skylark lounge
def build_lounge(pal, ao):
    # the bar [6, 2] (front -Y): a curved timber counter, a brass foot rail, stools, the lit back bar (glow) at +Y
    m = new(pal)
    g = new(pal)
    m.bx(-2.8, 2.8, -0.5, 0.1, 0.0, 1.08, 'woodD', cull='b')
    m.bx(-2.85, 2.85, -0.6, 0.15, 1.08, 1.13, 'cream')
    m.bx(-2.75, 2.75, -0.68, -0.64, 0.18, 0.22, 'brass', hull='none')
    for k in range(5):
        x = -2.2 + k * 1.1
        m.cy((x, -0.95, 0.0), 0.04, 0.04, 0.75, 'brass', seg=4, hull='none', caps=False)
        m.cy((x, -0.95, 0.75), 0.2, 0.2, 0.08, 'leather', seg=6)
    m.bx(-2.9, 2.9, 0.6, 0.95, 0.0, 2.8, 'woodD', cull='b')
    for z in (1.2, 1.6, 2.0):
        m.bx(-2.8, 2.8, 0.4, 0.6, z - 0.03, z, 'glassL', hull='none', cull='')
        for k in range(12):
            x = -2.6 + k * 0.47
            fq(m, x - 0.05, x + 0.05, 0.597, z, z + (0.28 if k % 3 else 0.2), GOODS[(k + int(z * 5)) % 4])
    for z in (1.2, 1.6, 2.0):
        fq(g, -2.8, 2.8, 0.594, z + 0.02, z + 0.06, 'lightW')
    m.bx(-2.9, 2.9, 0.3, 0.95, 2.8, 3.05, 'wood')
    fq(m, -2.9, 2.9, 0.297, 2.85, 3.0, 'navy')
    text_front(m, 'THE AERIE BAR', 0.13, 0.294, 0.0, 2.87, 'brass', maxw=2.0)
    make('Bar', m, ao, cols=[cb(-2.85, -0.6, 0.0, 2.85, 0.15, 1.13), cb(-2.9, 0.4, 0.0, 2.9, 0.95, 3.05)])
    make_glow('Bar_LED', g)
    # club chairs with a side table [2, 2]: two leather armchairs angled to the table (front -Y)
    m = new(pal)
    for s in (-1, 1):
        x = s * 0.54
        M0 = m.parent
        m.parent = M0 @ Matrix.Translation((x, 0.1, 0)) @ Matrix.Rotation(math.radians(-s * 15), 4, 'Z')
        m.bx(-0.36, 0.36, -0.32, 0.32, 0.08, 0.42, 'leather')
        m.bx(-0.36, 0.36, 0.2, 0.34, 0.42, 0.85, 'leather')
        for sx in (-1, 1):
            m.bx(sx * 0.29, sx * 0.39, -0.3, 0.2, 0.42, 0.62, 'leather')
        m.bx(-0.27, 0.27, -0.28, 0.18, 0.42, 0.5, 'cream')
        m.parent = M0
    m.cy((0, -0.65, 0), 0.22, 0.22, 0.5, 'woodD', seg=8)
    m.cy((0, -0.65, 0.5), 0.26, 0.26, 0.04, 'brass', seg=8)
    make('Club', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.55, 0.85), cb(-0.26, -0.92, 0.0, 0.26, -0.4, 0.54)])
    # sofa [3, 1] (front -Y)
    m = new(pal)
    m.bx(-1.45, 1.45, -0.42, 0.42, 0.08, 0.42, 'fabD')
    m.bx(-1.45, 1.45, 0.2, 0.42, 0.42, 0.9, 'fabD')
    for x in (-1.32, 1.32):
        m.bx(x - 0.13, x + 0.13, -0.42, 0.2, 0.42, 0.66, 'fabD')
    for x in (-0.6, 0.6):
        m.bx(x - 0.55, x + 0.55, -0.38, 0.2, 0.42, 0.52, 'fab')
    for x in (-1.3, 1.3):
        m.cy((x, 0.0, 0.0), 0.04, 0.04, 0.08, 'brass', seg=4, hull='none')
    make('Sofa', m, ao, cols=[cb(-1.45, -0.42, 0.0, 1.45, 0.42, 0.66), cb(-1.45, 0.2, 0.0, 1.45, 0.42, 0.9)])
    # buffet [4, 1] (front -Y): a stone counter, chafing dishes under a sneeze guard, a fruit bowl
    m = new(pal)
    m.bx(-1.95, 1.95, -0.4, 0.4, 0.0, 0.9, 'stone', cull='b')
    m.bx(-2.0, 2.0, -0.45, 0.45, 0.9, 0.95, 'wallW')
    for k in range(4):
        x = -1.45 + k * 0.95
        m.bx(x - 0.35, x + 0.35, -0.25, 0.25, 0.95, 1.08, 'chrome')
        uq(m, x - 0.3, x + 0.3, -0.2, 0.2, 1.083, ('sun', 'leather', 'leaf', 'cream')[k])
    m.bx(-1.9, 1.9, -0.3, 0.3, 1.45, 1.48, 'glassL', hull='none', cull='')
    for x in (-1.85, 1.85):
        m.bx(x - 0.02, x + 0.02, -0.02, 0.02, 0.95, 1.45, 'chrome', hull='none', cull='b')
    make('Buffet', m, ao, cols=[cb(-2.0, -0.45, 0.0, 2.0, 0.45, 1.1)])
    # reception desk [3, 1] (front -Y) with the lounge name on the wall panel behind
    m = new(pal)
    m.bx(-1.4, 1.4, -0.35, 0.3, 0.0, 1.05, 'navy', cull='b')
    m.bx(-1.45, 1.45, -0.4, 0.35, 1.05, 1.1, 'brass')
    fq(m, -1.3, 1.3, -0.353, 0.45, 0.62, 'brass')
    text_front(m, 'SKYLARK LOUNGE', 0.12, -0.356, 0.0, 0.48, 'navy', maxw=2.4)
    m.bx(-0.3, 0.3, 0.0, 0.2, 1.1, 1.4, 'black', cull='')
    make('LoungeDesk', m, ao, cols=[cb(-1.45, -0.4, 0.0, 1.45, 0.35, 1.1)])
    # the lounge's glass door [2, 1] (orient 'span': local X along the glass line): a frameless pair standing open
    m = new(pal)
    m.bx(-1.0, 1.0, -0.06, 0.06, 2.6, 2.8, 'steelD', hull='noside')
    for x in (-0.97, 0.97):
        m.bx(x - 0.03, x + 0.03, -0.05, 0.05, 0.0, 2.6, 'steelD', cull='b')
    for s in (-1, 1):
        x = s * 0.9
        m.bx(x - 0.01, x + 0.01, -0.85, -0.05, 0.05, 2.5, 'glass', hull='none', cull='')
        m.bx(x - 0.04 * s - 0.02, x - 0.04 * s + 0.02, -0.7, -0.62, 0.9, 1.4, 'brass', hull='none', cull='')
    text_front(m, 'SKYLARK LOUNGE', 0.12, -0.063, 0.0, 2.64, 'brass', maxw=1.6)
    make('LoungeDoor', m, ao, cols=[cb(-1.0, -0.06, 2.6, 1.0, 0.06, 2.8), cb(-1.0, -0.06, 0.0, -0.94, 0.06, 2.6), cb(0.94, -0.06, 0.0, 1.0, 0.06, 2.6)])


# ================================================================ hanging signs (from z = 0 = the 14 m ceiling)
def hang(m, w, z0, z1, c, rods=True):
    m.bx(-w / 2, w / 2, -0.07, 0.07, z0, z1, c)
    if rods:
        for x in (-w / 2 + 0.3, w / 2 - 0.3):
            m.bx(x - 0.012, x + 0.012, -0.012, 0.012, z1, -0.012, 'steelD', hull='none', cull='tb')


def build_signs(pal, ao):
    """wayfinding boards (black with yellow, the airport style) and airline boards over the check-in islands; both
    faces lettered; they hang 9.4 - 10.3 m down (bottom at 3.7 - 4.6 m)"""
    WAY = [('Gates', 'GATES A1-A3  LOUNGE', None), ('Security', 'SECURITY', None),
           ('CheckIn', 'CHECK-IN', None), ('Exit', 'TO HANGAR 2', None)]
    for key, w1, w2 in WAY:
        m = new(pal)
        z0, z1 = -10.3, -9.4
        hang(m, 4.6, z0, z1, 'black')
        for s in (-1, 1):
            T = text_front if s < 0 else text_back
            T(m, w1, 0.5, s * 0.073, 0.0, z0 + 0.2, 'sun', maxw=4.2)
        make('Sg_' + key, m, ao)
    AIR = [('Sky', 'SKYLARK AIR', 'sky', 'sun'), ('Vale', 'AEROVALE', 'coral', 'paper'), ('North', 'NORTHSTAR', 'navy', 'skyL'),
           ('Coral', 'CORAL JET', 'sun', 'navy')]
    for key, word, bg, fg in AIR:
        m = new(pal)
        z0, z1 = -9.6, -8.8
        hang(m, 5.4, z0, z1, bg)
        for s in (-1, 1):
            (text_front if s < 0 else text_back)(m, word, 0.5, s * 0.073, 0.0, z0 + 0.15, fg, maxw=5.0)
        make('Sg_' + key, m, ao)
    for k in range(1, 4):
        m = new(pal)
        z0, z1 = -9.9, -9.1
        hang(m, 1.6, z0, z1, 'black')
        for s in (-1, 1):
            (text_front if s < 0 else text_back)(m, 'A%d' % k, 0.6, s * 0.073, 0.0, z0 + 0.1, 'sun', maxw=1.3)
        make('Sg_A%d' % k, m, ao)
    m = new(pal)   # duty free fascia
    z0, z1 = -10.6, -9.6
    hang(m, 8.0, z0, z1, 'navy')
    for s in (-1, 1):
        (text_front if s < 0 else text_back)(m, 'MERIDIAN DUTY FREE', 0.55, s * 0.073, 0.0, z0 + 0.22, 'sun', maxw=7.4)
    make('Sg_DF', m, ao)


def build_term(pal, ao):
    build_checkin(pal, ao)
    build_security(pal, ao)
    build_gates(pal, ao)
    build_shops(pal, ao)
    build_lounge(pal, ao)
    build_signs(pal, ao)
