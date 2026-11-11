"""kit-cargoship backdrop pieces (placed by the theme's backdrop.build, outside the play area):
  Backdrop_Deckhouse  the accommodation tower on top of the superstructure's full-width base (origin: the base top,
                      13 m up, on the ship's centre line, at the tower's front plane; the base's front edge is 3 m
                      forward of it): five decks of cabins, the wheelhouse with raked windows, bridge wings out to the
                      ship's sides, the radar mast with two scanners, the ship's name on the bridge front
  Backdrop_Funnel     the funnel aft of the tower in the line's colours
  Backdrop_Forecastle the bow forward of the forecastle bulkhead (origin: the main deck at the zone's south edge, the
                      bow toward Blender -Y): forecastle deck, breakwater, windlasses and anchor chains, the foremast,
                      a jack staff, the flared and raked hull of the bow down to the waterline
  Backdrop_Feeder     a small feeder container ship far out at sea
  Gull, Sea_Glint, Foam_Fleck: instanced and animated by the theme"""
import math

from cargo_base import *  # noqa: F401,F403
import ib_text

SEA = -13.0   # waterline below the main deck


def build_deckhouse(pal, ao):
    m = new(pal)
    W2, D, DH, N = 15.0, 16.0, 2.9, 5
    top = N * DH
    m.bx(-W2, W2, 0.0, D, 0.0, top, 'supW', cull='b')
    for k in range(1, N):   # deck ledges round the tower
        z = k * DH
        m.bx(-W2 - 0.12, W2 + 0.12, -0.12, D + 0.12, z - 0.1, z, 'supWD', hull='full')
    for k in range(N):
        z = k * DH + 0.9
        for i in range(12):   # front windows
            x = -W2 + 1.25 + i * 2.5
            fq(m, x - 0.6, x + 0.6, -0.003, z, z + 1.2, 'glassD')
        for sx in (-1, 1):
            for i in range(4):
                y = 2.0 + i * 4.0
                (rq if sx > 0 else lq)(m, sx * (W2 + 0.003), y - 0.6, y + 0.6, z, z + 1.2, 'glassD')
    # wheelhouse with raked windows, wings out to the ship's sides
    zb = top
    m.bx(-13.0, 13.0, 1.0, 10.0, zb, zb + 3.3, 'supW')
    prof = [(1.0, zb + 1.1), (0.4, zb + 2.9), (1.0, zb + 3.3), (1.3, zb + 1.1)]
    m.prism(prof, -12.98, 12.98, ['glassD'])
    for k in range(14):
        x = -13.0 + k * 26.0 / 13
        m.bx(x - 0.06, x + 0.06, 0.36, 0.5, zb + 1.1, zb + 2.95, 'supW', hull='none', cull='tbk')
    m.bx(-13.2, 13.2, 0.2, 10.2, zb + 3.3, zb + 3.55, 'supWD')
    for sx in (-1, 1):
        a, b = sorted((sx * 13.0, sx * 25.2))
        s0, s1 = sorted((sx * W2, sx * 25.2))
        m.bx(s0, s1, 1.0, 6.0, zb - 0.25, zb, 'supWD')
        m.bx(a, b, 1.0, 1.2, zb, zb + 1.2, 'supW')
        m.bx(a, b, 5.8, 6.0, zb, zb + 1.2, 'supW')
        e0, e1 = sorted((sx * 25.0, sx * 25.2))
        m.bx(e0, e1, 1.2, 5.8, zb, zb + 1.2, 'supW')
        fq(m, a, b, 0.997, zb + 0.4, zb + 0.5, 'supWD')
        # brackets under the wing
        for x in (sx * 18.0, sx * 22.5):
            m.bm_((x, 3.5, zb - 0.25), (sx * (abs(x) - 3.0), 3.5, zb - 3.6), 0.25, 'supWD')
        m.bx(sx * 24.4 - 0.3, sx * 24.4 + 0.3, 1.6, 2.4, zb + 1.2, zb + 1.6, 'steelD')
    ib_text.draw(m, 'HALCYON VEGA', 0.0, 0.997, zb + 0.15, 0.8, 'cTel', face='y-', font='display', maxw=14)
    # radar mast, scanners, lights, horn, whip aerials
    zt = zb + 3.55
    m.bx(-0.6, 0.6, 5.0, 6.2, zt, zt + 7.0, 'supW')
    m.bx(-4.5, 4.5, 5.2, 6.0, zt + 5.5, zt + 5.8, 'supW')
    for x, h in ((-3.5, 0.0), (3.5, 0.0)):
        m.cy((x, 5.6, zt + 5.8), 0.25, 0.25, 0.4, 'steelD', seg=6)
        m.bx(x - 1.9, x + 1.9, 5.45, 5.75, zt + 6.2, zt + 6.45, 'paper')
    m.cy((0, 5.6, zt + 7.0), 0.15, 0.05, 3.0, 'steelD', seg=6)
    for x in (-4.4, 4.4):
        m.cy((x, 5.6, zt + 5.8), 0.12, 0.12, 0.25, 'fireR' if x < 0 else 'exitG', seg=6)
    for x in (-9.0, -6.0, 8.0):
        m.cy((x, 8.0, zt), 0.03, 0.02, 5.0, 'steelD', seg=4, hull='none')
    m.cy((1.5, 4.8, zt + 2.0), 0.2, 0.4, 0.9, 'supWD', seg=8, rot=(90, 0, 0))
    # guard rail along the base's front edge (3 m ahead of the tower) and the open deck there
    rail_run(m, -25.2, 25.2, -2.85, 0.0, h=1.05, c='supW', post=3.0, toe=False)
    make('Backdrop_Deckhouse', m, ao)


def build_funnel(pal, ao):
    m = new(pal)
    R, X = 2.6, 2.8
    H2 = 22.0
    m.bx(-X, X, -R, R, 0.0, H2, 'hullR', cull='btlr')
    for sx in (-1, 1):
        m.cy((sx * X, 0, 0.0), R, R, H2, 'hullR', seg=12, caps=False)
    for z0, z1, c in ((11.0, 16.5, 'cTel'), (19.5, H2, 'ink')):
        m.bx(-X, X, -R - 0.03, R + 0.03, z0, z1, c, hull='none', cull='tblr')
        for sx in (-1, 1):
            m.cy((sx * X, 0, z0), R + 0.03, R + 0.03, z1 - z0, c, seg=12, hull='none', caps=False)
    for fy in (-1, 1):   # the line's emblem: a white ring with an H in it
        y = fy * (R + 0.06)
        m.cy((0, y, 13.75), 2.0, 2.0, 0.02, 'paper', seg=16, rot=(90 * fy, 0, 0), hull='none')
        m.cy((0, y + fy * 0.02, 13.75), 1.6, 1.6, 0.02, 'cTel', seg=16, rot=(90 * fy, 0, 0), hull='none')
        (text_front if fy < 0 else text_back)(m, 'H', 0.42, y + fy * 0.045, 0.0, 12.7, 'paper')
    for x in (-1.6, 0.0, 1.6):
        m.cy((x, 0.4, H2), 0.5, 0.5, 1.4, 'steelD', seg=8)
    make('Backdrop_Funnel', m, ao)


def build_forecastle(pal, ao):
    m = new(pal)
    zd = FC + 0.12
    # deck-edge outline (y, half-width at the deck, half-width at the waterline, the bulwark top's sheer)
    pts = [(0.0, 25.5, 25.5, 1.25), (-10.0, 25.2, 24.0, 1.3), (-20.0, 22.5, 18.0, 1.45), (-30.0, 16.5, 9.5, 1.7),
           (-38.0, 8.5, 2.5, 2.0), (-43.0, 1.2, 0.3, 2.3)]
    stem = (-44.5, -39.5)   # stem at the deck / at the waterline (raked)
    # deck: fan of quads over the outline
    for i in range(len(pts) - 1):
        (y0, w0, _, _), (y1, w1, _, _) = pts[i], pts[i + 1]
        poly(m, [(-w0, y0, zd), (w0, y0, zd), (w1, y1, zd), (-w1, y1, zd)], 'deckG', (0, 0, 1))
    poly(m, [(-pts[-1][1], pts[-1][0], zd), (pts[-1][1], pts[-1][0], zd), (0.0, stem[0], zd)], 'deckG', (0, 0, 1))
    # bulwark (inner face, cap) and hull side (red to the boot top, black boot top to the waterline)
    side = pts + [(stem[0], 0.0, 0.0, 2.4)]
    for sx in (-1, 1):
        for i in range(len(side) - 1):
            (y0, w0, l0, s0), (y1, w1, l1, s1) = side[i], side[i + 1]
            yl0 = y0 if i < len(side) - 2 else y0
            yl1 = y1 if i < len(side) - 2 else stem[1]
            t0, t1 = zd + s0, zd + s1
            i0, i1 = max(w0 - 0.25, 0.0), max(w1 - 0.25, 0.0)
            poly(m, [(sx * i0, y0, zd), (sx * i1, y1, zd), (sx * i1, y1, t1), (sx * i0, y0, t0)], 'supWD', (-sx, 0, 0))
            poly(m, [(sx * i0, y0, t0), (sx * i1, y1, t1), (sx * w1, y1, t1), (sx * w0, y0, t0)], 'deckGD', (0, 0, 1))
            zb = SEA + 2.0
            f = lambda w, l, t: l + (w - l) * (zb - SEA) / (t - SEA)
            poly(m, [(sx * w0, y0, t0), (sx * w1, y1, t1), (sx * f(w1, l1, t1), y1 + (yl1 - y1) * 0.08, zb), (sx * f(w0, l0, t0), y0 + (yl0 - y0) * 0.08, zb)], 'hullR', (sx, 0, 0))
            poly(m, [(sx * f(w0, l0, t0), y0 + (yl0 - y0) * 0.08, zb), (sx * f(w1, l1, t1), y1 + (yl1 - y1) * 0.08, zb), (sx * l1, yl1, SEA), (sx * l0, yl0, SEA)], 'ink', (sx, 0, 0))
    # breakwater: a V of stiffened plate across the forecastle, its point forward
    for sx in (-1, 1):
        a = math.atan2(4.0, 22.0) * sx
        at(m, sx * 11.0, -7.0, zd, math.degrees(-a))
        hb = 3.3 + (0.03 if sx > 0 else 0.0)
        m.bx(-11.05, 11.2, -0.1, 0.1, 0.0, hb, 'supW', cull='b')
        for k in range(5):
            x = -9.0 + k * 4.5
            m.prism([(0.1, 0.0), (0.7, 0.0), (0.1, 3.1)], x - 0.05, x + 0.05, ['supWD'])
        m.bx(-11.05, 11.2, -0.14, 0.14, hb, hb + 0.1, 'supWD')
        at(m)
    # windlasses, anchor chains to the hawse pipes, bitts, mushroom vents
    for sx in (-1, 1):
        x = sx * 4.5
        m.bx(x - 1.6, x + 1.6, -27.0, -24.5, zd, zd + 0.4, 'steelD')
        m.cy((x - 1.2, -25.7, zd + 1.3), 0.9, 0.9, 2.4, 'engG', seg=12, rot=(0, 90, 0))
        m.cy((x - sx * 0.1, -25.7, zd + 1.3), 1.0, 1.0, 0.25, 'fireR', seg=12, rot=(0, 90, 0))
        hx = sx * 13.5
        m.bm_((x, -26.6, zd + 0.5), (hx, -36.0, zd + 0.1), 0.3, 'ink')
        m.cy((hx, -36.0, zd), 0.55, 0.55, 0.3, 'steelD', seg=10)
        m.bx(sx * 18.5 - 0.6, sx * 18.5 + 0.6, -14.25, -13.75, zd, zd + 0.7, 'ink')
        m.cy((sx * 8.0, -16.0, zd), 0.2, 0.2, 1.0, 'supWD', seg=8)
        m.cy((sx * 8.0, -16.0, zd + 1.0), 0.4, 0.1, 0.3, 'supWD', seg=8)
    # foremast: a tapered post with a lookout platform, lights and a radar reflector; jack staff at the stem
    m.cy((0, -31.0, zd), 0.55, 0.35, 15.0, 'supW', seg=10)
    m.bx(-1.4, 1.4, -32.4, -29.6, zd + 9.0, zd + 9.15, 'supWD')
    rail_run(m, -1.4, 1.4, -32.4, zd + 9.15, h=0.9, c='supW', post=0.7, toe=False)
    m.bx(-1.8, 1.8, -31.15, -30.85, zd + 12.0, zd + 12.2, 'supW')
    for x, c in ((-1.7, 'fireR'), (1.7, 'exitG'), (0.0, 'light')):
        m.cy((x, -31.0, zd + 12.2 if x else zd + 15.0), 0.12, 0.12, 0.3, c, seg=6)
    m.cy((0, -43.0, zd + 2.3), 0.06, 0.04, 4.0, 'supW', seg=6)
    make('Backdrop_Forecastle', m, ao)


def build_small(pal, ao):
    # a feeder container ship far out at sea (origin: its waterline amidships, bow toward -Y)
    m = new(pal)
    m.bx(-6.0, 6.0, -22.0, 26.0, 0.0, 5.0, 'cNav', cull='b')
    m.prism([(-22.0, 0.0), (-30.0, 6.0), (-22.0, 6.0)], -6.0, 6.0, ['cNav'])
    cols = ['cRed', 'cBlu', 'cGrn', 'cOra', 'cGry', 'cYel', 'cTel', 'cMar']
    for i in range(6):
        y = -18.0 + i * 6.5
        h = 2.6 * (2 + (i * 7) % 3)
        m.bx(-5.4, 5.4, y, y + 6.0, 5.0, 5.0 + h, cols[i % len(cols)], cull='b')
    m.bx(-5.5, 5.5, 20.1, 26.0, 5.0, 16.0, 'supW', cull='b')
    fq(m, -5.0, 5.0, 19.997, 13.5, 15.0, 'glassD')
    m.bx(-1.2, 1.2, 23.0, 25.0, 16.0, 20.0, 'hullR')
    make('Backdrop_Feeder', m, ao)
    # gull: body, M-shaped wings, tail
    m = new(pal)
    m.sp((0, 0, 0), 0.18, 'paper', seg=(6, 4), scale=(0.7, 2.0, 0.7))
    m.sp((0, -0.38, 0.05), 0.09, 'paper', seg=(6, 4))
    m.cy((0, -0.48, 0.04), 0.03, 0.0, 0.1, 'yel', seg=4, rot=(90, 0, 0), hull='none')
    for sx in (-1, 1):
        poly(m, [(sx * 0.1, -0.12, 0.05), (sx * 0.55, -0.15, 0.22), (sx * 0.62, 0.08, 0.2), (sx * 0.1, 0.12, 0.05)], 'supWD', (0, 0, 1))
        poly(m, [(sx * 0.55, -0.15, 0.22), (sx * 1.15, -0.02, 0.05), (sx * 1.1, 0.12, 0.03), (sx * 0.62, 0.08, 0.2)], 'supWD', (0, 0, 1))
        poly(m, [(sx * 1.15, -0.02, 0.05), (sx * 1.35, 0.06, 0.0), (sx * 1.1, 0.12, 0.03)], 'ink', (0, 0, 1))
        poly(m, [(sx * 0.1, -0.12, 0.049), (sx * 0.55, -0.15, 0.219), (sx * 0.62, 0.08, 0.199), (sx * 0.1, 0.12, 0.049)], 'paper', (0, 0, -1))
        poly(m, [(sx * 0.55, -0.15, 0.219), (sx * 1.15, -0.02, 0.049), (sx * 1.1, 0.12, 0.029), (sx * 0.62, 0.08, 0.199)], 'paper', (0, 0, -1))
    poly(m, [(-0.1, 0.3, 0.02), (0.1, 0.3, 0.02), (0.14, 0.55, 0.0), (-0.14, 0.55, 0.0)], 'paper', (0, 0, 1))
    make('Gull', m, ao)
    # sea glint (a shimmer dash) and a foam fleck: flat, no outline
    m = new(pal)
    poly(m, [(-0.9, -0.05, 0.0), (0.9, -0.05, 0.0), (0.9, 0.05, 0.0), (-0.9, 0.05, 0.0)], 'white', (0, 0, 1))
    make('Sea_Glint', m, ao)
    m = new(pal)
    disc(m, 0.0, 0.0, 0.0, 0.5, 'white', seg=7, jag=[1.0, 0.7, 1.15, 0.8, 1.05, 0.65, 0.95], sx=2.2, sy=1.0)
    make('Foam_Fleck', m, ao)
