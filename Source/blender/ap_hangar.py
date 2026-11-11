"""kit-airport hangar and apron: the Skylark Air twin-jet (an original design: a 33 m narrow-body with a low swept
wing, winglets, two underwing engines and a conventional tail; Skylark Air livery -- white with a sky-blue sweep,
a yellow fin with blue chevrons), its engine as a separate piece (on the pylon or on its transport stand), wing
jacks, ground support equipment (aircraft tug, baggage tractor and carts, fuel truck, stairs truck, belt loader,
ULD containers, ground power unit, towbar), a tool crib and an apron light mast (see ap_base.py for conventions).

The jet's frame (Blender): nose toward -Y (game +Z); fuselage axis at x = 0, centre 3.25 m up; wing root at
y = -2.2 .. 4.2; engines at x = +/-6.0, nacelle centre 1.2 m up, from y = -4.0 to 0.0 (an engine block [2, 4]
centred 2 m ahead of the plane's centre). Collision: the fuselage to 1.15 m above the floor (robots path round it),
the wing's upper surface as walkable steps (WCOL) so the work platforms lead onto it."""
import math

from ap_base import *  # noqa: F401,F403
import ap_base as B

R = 1.95          # fuselage radius
CZ = 3.25         # fuselage centre height
ENG_X, ENG_Z = 6.0, 1.2
RINGS = [(-16.5, 0.0, 2.9, 0.0, 0.0), (-16.1, 0.0, 2.95, 0.6, 0.55), (-15.2, 0.0, 3.05, 1.25, 1.15), (-14.0, 0.0, 3.15, 1.7, 1.62),
         (-12.4, 0.0, 3.23, 1.93, 1.9), (-10.0, 0.0, CZ, R, R), (7.0, 0.0, CZ, R, R), (9.8, 0.0, 3.45, 1.8, 1.72),
         (12.6, 0.0, 3.9, 1.3, 1.18), (15.0, 0.0, 4.35, 0.72, 0.62), (16.5, 0.0, 4.6, 0.25, 0.22)]
A0 = -math.pi / 12          # facets centred at 0, 30, 60 ... degrees: the side facets are vertical
APO = R * math.cos(math.pi / 12)


def wing_le(x):
    return -2.2 + (abs(x) - 1.6) / 13.9 * 7.2


def wing_te(x):
    return 4.2 + (abs(x) - 1.6) / 13.9 * 2.6


def wing_mid(x):
    return 1.95 + (abs(x) - 1.6) / 13.9 * 0.95


def wing_t(x):
    return 0.6 - (abs(x) - 1.6) / 13.9 * 0.45


def wing_top(x):
    return wing_mid(x) + wing_t(x) / 2


def facet_frame(m, ang):
    """m.parent for painting on the fuselage facet centred at angle ang (local +X = the facet's outward normal)"""
    return m.parent @ Matrix.Rotation(-ang, 4, 'Y')


def jet_body(pal, ao, name, maint=False):
    m = new(pal)

    def col(k, i, ang):
        if k <= 1:
            return 'belly'
        sn = math.sin(ang)
        if sn < -0.6:
            return 'belly'
        if sn < -0.2:
            return 'sky'
        return 'white'
    loft(m, RINGS, col, seg=12, a0=A0)
    # cockpit windows (on the 0 and 30 degree facets, both sides) -- painted on the facets near y = -13.5
    for side in (1, -1):
        for fa in (0.0, math.pi / 6):
            ang = fa if side > 0 else math.pi - fa
            M0 = m.parent
            m.parent = facet_frame(m, ang)
            # apothem of the facet near y = -13.4 (ring radius ~1.8)
            ap = 1.79 * math.cos(math.pi / 12) + 0.012
            for k in range(2):
                y0 = -13.9 + k * 0.45
                rq(m, ap, y0, y0 + 0.36, -0.24, 0.2, 'black')
            m.parent = M0
    # passenger windows on the vertical side facets, the doors, the title above the windows
    for side in (1, -1):
        x = side * (APO + 0.004)
        Q = rq if side > 0 else lq
        for k in range(22):
            y = -8.2 + k * 0.68
            Q(m, x, y, y + 0.24, CZ + 0.12, CZ + 0.42, 'navy')
        for (y0, y1) in ((-9.9, -9.0), (7.4, 8.2)) if side > 0 else ((-9.9, -9.0), (7.4, 8.2)):
            Q(m, x, y0, y1, CZ - 0.5, CZ + 0.5, 'belly')
        M0 = m.parent
        m.parent = facet_frame(m, math.pi / 6 if side > 0 else math.pi - math.pi / 6)
        ib_text.draw(m, 'SKYLARK AIR', APO + 0.012, -3.0 * side, -0.25, 0.55, 'sky', face='x+', font='display', maxw=9.0)
        m.parent = M0
    # wings (low, swept, with dihedral) and winglets, flap-track fairings, the pylons
    for s in (-1, 1):
        def pt(x, y, up):
            return (s * x, y, wing_mid(x) + (wing_t(x) / 2 if up else -wing_t(x) / 2))
        xr, xt = 1.6, 15.5
        v = [pt(xr, wing_le(xr), 0), pt(xr, wing_te(xr), 0), pt(xt, wing_te(xt), 0), pt(xt, wing_le(xt), 0),
             pt(xr, wing_le(xr), 1), pt(xr, wing_te(xr), 1), pt(xt, wing_te(xt), 1), pt(xt, wing_le(xt), 1)]
        f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        skin(m, (v, f), 'white')
        # winglet: a swept fin rising 1.6 m from the tip
        zt = wing_top(xt)
        wv = [(s * xt, wing_le(xt) + 0.3, zt - 0.05), (s * xt, wing_te(xt), zt - 0.05), (s * (xt + 0.35), wing_te(xt) + 0.5, zt + 1.6), (s * (xt + 0.35), wing_te(xt) - 0.3, zt + 1.6)]
        wv2 = [(a + s * 0.1, b, c) for (a, b, c) in wv]
        skin(m, (wv + wv2, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'sky')
        for xf in (4.0, 8.5, 12.0):
            yb = wing_te(xf) - 0.6
            m.bx(s * xf - 0.14, s * xf + 0.14, yb, yb + 1.3, wing_mid(xf) - wing_t(xf) / 2 - 0.22, wing_mid(xf) - wing_t(xf) / 2 + 0.02, 'belly', cull='t')
        # pylon: from the nacelle's top to under the wing (kept on both sides; the engine piece hangs under it)
        xe = s * ENG_X
        zb = wing_mid(ENG_X) - wing_t(ENG_X) / 2
        zt = wing_mid(ENG_X) + 0.05
        wedge(m, xe - 0.13, xe + 0.13, -3.2, wing_le(ENG_X) + 1.4, ENG_Z + 0.82, zt, ENG_Z + 0.82, zt, 'white')
        if maint and s > 0:   # the bare pylon of the removed engine: a yellow cover over its mounts
            m.bx(xe - 0.18, xe + 0.18, -2.4, -1.4, ENG_Z + 0.7, ENG_Z + 0.86, 'sun', hull='none', cull='t')
            chevrons(m, xe - 0.18, xe + 0.18, -2.403, ENG_Z + 0.7, ENG_Z + 0.86, 4)
    # tailplanes and the fin (Skylark yellow with blue chevrons)
    for s in (-1, 1):
        v = [(s * 0.9, 12.3, 4.35), (s * 0.9, 15.6, 4.35), (s * 6.0, 16.4, 4.85), (s * 6.0, 15.2, 4.85),
             (s * 0.9, 12.3, 4.65), (s * 0.9, 15.6, 4.65), (s * 6.0, 16.4, 4.95), (s * 6.0, 15.2, 4.95)]
        skin(m, (v, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'white')
    fin = [(10.5, 4.9), (16.4, 4.9), (16.7, 11.0), (14.6, 11.0)]
    v = [(-0.15, y, z) for (y, z) in fin] + [(0.15, y, z) for (y, z) in fin]
    skin(m, (v, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'sun')
    for s in (-1, 1):
        x = s * 0.153
        for k in range(3):
            z0 = 6.3 + k * 1.15
            # chevron stripes following the fin's sweep: parallelograms
            yl0 = 10.5 + (z0 - 4.9) / 6.1 * 4.1
            yl1 = 10.5 + (z0 + 0.5 - 4.9) / 6.1 * 4.1
            poly(m, [(x, yl0 + 0.4, z0), (x, yl0 + 2.6, z0), (x, yl1 + 2.6, z0 + 0.5), (x, yl1 + 0.4, z0 + 0.5)], 'sky', (s, 0, 0))
        poly(m, [(x, 14.55, 10.4), (x, 16.65, 10.4), (x, 16.7, 10.98), (x, 14.62, 10.98)], 'navy', (s, 0, 0))
    # landing gear: the nose leg (two wheels) and the main legs under the wing roots (two wheels each)
    m.cy((0.0, -12.5, 0.4), 0.08, 0.08, CZ - R - 0.4 + 0.1, 'chrome', seg=6)
    for x in (-0.25, 0.25):
        wheel(m, x, -12.5, 0.38, 0.38, 0.22, seg=8)
    m.bx(-0.3, 0.3, -12.75, -12.25, 1.25, 1.35, 'belly', hull='none')
    for s in (-1, 1):
        x = s * 2.9
        m.cy((x, 2.8, 0.55), 0.12, 0.12, 1.3, 'chrome', seg=6)
        for dx in (-0.32, 0.32):
            wheel(m, x + dx, 2.8, 0.55, 0.55, 0.3, seg=8)
        m.bx(x - 0.04, x + 0.04, 2.4, 3.2, 0.9, 1.75, 'white', hull='none', cull='')
    if maint:   # access panels off: dark openings under the belly and an avionics bay door
        for (y0, y1) in ((-6.0, -4.8), (5.0, 6.2)):
            dq(m, -0.6, 0.6, y0, y1, CZ - R + 0.06, 'black')
    # collision: fuselage to 1.15 m (robots path round it), tail, wings as walkable steps, gear, tailplanes
    # (inner boxes: each one inside the drawn shape, so no corner of a box stands in the air)
    cols = [cb(-R, -12.4, 1.15, R, 7.5, CZ + R), cb(-1.6, -14.0, 1.6, 1.6, -12.4, 4.7), cb(-1.15, -15.2, 1.95, 1.15, -14.0, 4.2),
            cb(-1.5, 7.5, 1.9, 1.5, 12.6, 5.2), cb(-0.8, 12.6, 3.5, 0.8, 14.5, 5.0), cb(-0.25, 14.5, 4.3, 0.25, 16.4, 4.85),
            cb(-0.4, -12.8, 0.0, 0.4, -12.2, 1.4)]
    for (za, zb) in ((4.9, 6.9), (6.9, 8.9), (8.9, 11.0)):
        cols.append(cb(-0.15, 10.5 + (zb - 4.9) / 6.1 * 4.1, za, 0.15, 16.4 + (za - 4.9) / 6.1 * 0.3, zb))
    for s in (-1, 1):
        cols.append(cb(s * 2.45, 2.45, 0.0, s * 3.35, 3.15, 1.9))
        for (xa, xb) in ((0.9, 2.6), (2.6, 4.3), (4.3, 6.0)):
            le = 12.3 + (xb - 0.9) / 5.1 * 2.9
            te = 15.6 + (xa - 0.9) / 5.1 * 0.8
            cols.append(cb(s * xa, le, 4.35, s * xb, te, 4.85))
        for k in range(11):
            x0, x1 = 2.0 + k, 3.0 + k
            xm = (x0 + x1) / 2
            a, b = wing_le(x1) + 0.25, wing_te(x0) - 0.25
            bot = wing_mid(xm) - wing_t(xm) / 2
            cols.append(cb(s * x0, a, 1.15 if bot < 1.75 else bot, s * x1, b, wing_top(xm) - 0.02, True))
    make(name, m, ao, cols=cols)


def engine(pal, ao):
    """the engine (nacelle centre at the origin, intake toward -Y, 4 m long): white cowl, a blue intake lip,
    the dark fan with a spinner, the exhaust cone"""
    m = new(pal)
    rings = [(-2.0, 0.0, 0.0, 0.86, 0.86), (-1.8, 0.0, 0.0, 0.92, 0.92), (0.4, 0.0, 0.0, 0.88, 0.88), (2.0, 0.0, 0.0, 0.62, 0.62)]
    loft(m, rings, lambda k, i, a: 'sky' if k == 0 else 'white', seg=12)
    vdisc(m, 0.0, -2.003, 0.0, 0.8, 'black', seg=12)
    m.cy((0.0, -1.98, 0.0), 0.26, 0.02, 0.45, 'chrome', seg=8, rot=(90, 0, 0), caps=False)
    m.cy((0.0, 2.0, 0.0), 0.4, 0.06, 0.7, 'steelD', seg=8, rot=(-90, 0, 0))
    make('Engine', m, ao, cols=[cb(-0.9, -2.0, -0.9, 0.9, 2.0, 0.9)])


def build_jet(pal, ao):
    jet_body(pal, ao, 'Jet_Body', maint=True)
    jet_body(pal, ao, 'Jet_Line')
    engine(pal, ao)
    # weapon-stand base: an aluminium flight case with black corners and a Skylark tag
    m = new(pal)
    m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.55, 'chrome')
    for x in (-0.45, 0.45):
        for y in (-0.35, 0.35):
            m.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.0, 0.58, 'black', hull='none')
    fq(m, -0.25, 0.25, -0.353, 0.3, 0.42, 'sky')
    make('Stand', m, ao, cols=[cb(-0.5, -0.4, 0.0, 0.5, 0.4, 0.58)])
    # engine transport stand [2, 4]: a yellow cradle on castors; the engine sits with its centre at ENG_Z
    m = new(pal)
    for x in (-0.75, 0.75):
        m.bx(x - 0.08, x + 0.08, -2.0, 2.0, 0.18, 0.32, 'sun')
        for y in (-1.8, 1.8):
            m.bx(x - 0.08, x + 0.08, y - 0.1, y + 0.1, 0.0, 0.18, 'black', hull='none', cull='b')
    for y in (-1.3, 1.3):
        m.bx(-0.67, 0.67, y - 0.08, y + 0.08, 0.2, 0.3, 'sun', hull='none')
        for x in (-0.45, 0.45):
            m.bm_((x, y, 0.32), (x * 0.9, y, ENG_Z - 0.82), 0.08, 'sun')
    m.bm_((0.0, -2.0, 0.25), (0.0, -2.9, 0.25), 0.06, 'sun')
    make('EngStand', m, ao, cols=[cb(-0.85, -2.0, 0.0, 0.85, 2.0, 0.5)])
    # tripod jack under the wing (its ram reaching up to the jacking point)
    m = new(pal)
    for i in range(3):
        a = i * 2 * math.pi / 3
        m.bm_((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.0), (0.0, 0.0, 0.9), 0.07, 'sun')
    m.cy((0.0, 0.0, 0.8), 0.1, 0.1, 0.4, 'sun', seg=6)
    m.cy((0.0, 0.0, 1.2), 0.05, 0.05, 1.12, 'chrome', seg=6, hull='none')
    m.cy((0.0, 0.0, 2.32), 0.09, 0.09, 0.05, 'steelD', seg=6, hull='none')
    make('Jack', m, ao, cols=[cb(-0.3, -0.3, 0.0, 0.3, 0.3, 1.2)])


# ================================================================ ground support equipment
def wheels4(m, xs, ys, r, w, c='tire'):
    for x in xs:
        for y in ys:
            wheel(m, x, y, r, r, w, c=c, seg=8)


def build_gse(pal, ao):
    # aircraft tug [2, 4] (front -Y): a low wide yellow body, a cab at the back with a roof on posts, a tow hitch
    m = new(pal)
    m.bx(-0.95, 0.95, -1.8, 1.8, 0.25, 0.95, 'tug')
    fq(m, -0.95, 0.95, -1.803, 0.4, 0.6, 'black')
    for k in range(4):
        fq(m, -0.8 + k * 0.45, -0.6 + k * 0.45, -1.806, 0.4, 0.6, 'sun')
    m.bx(-0.7, 0.7, 0.4, 1.6, 0.95, 1.35, 'black', cull='b')
    m.bx(-0.75, 0.75, 0.3, 1.7, 2.0, 2.08, 'tug')
    for x in (-0.7, 0.7):
        for y in (0.35, 1.65):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.95, 2.0, 'black', hull='none', cull='bt')
    m.bx(-0.2, 0.2, -2.0, -1.8, 0.4, 0.55, 'steelD', hull='none')
    m.cy((0.55, 1.2, 2.08), 0.08, 0.08, 0.12, 'orange', seg=6, hull='none')
    wheels4(m, (-0.85, 0.85), (-1.1, 1.1), 0.36, 0.3)
    make('Tug', m, ao, cols=[cb(-1.0, -1.85, 0.0, 1.0, 1.8, 1.35), cb(-0.75, 0.3, 1.35, 0.75, 1.7, 2.08)])
    # baggage tractor [2, 2]: a small yellow tractor with a seat and a roof
    m = new(pal)
    m.bx(-0.6, 0.6, -0.95, 0.3, 0.3, 0.95, 'tug')
    m.bx(-0.6, 0.6, 0.3, 0.95, 0.3, 0.6, 'tug')
    m.bx(-0.35, 0.35, 0.35, 0.8, 0.6, 0.72, 'black')
    m.bx(-0.35, 0.35, 0.75, 0.85, 0.72, 1.15, 'black')
    m.bx(-0.65, 0.65, -0.3, 1.0, 1.85, 1.92, 'tug')
    for x in (-0.6, 0.6):
        m.bx(x - 0.025, x + 0.025, 0.9, 0.95, 0.6, 1.85, 'black', hull='none', cull='bt')
        m.bx(x - 0.025, x + 0.025, -0.3, -0.25, 0.95, 1.85, 'black', hull='none', cull='bt')
    m.cy((-0.1, 0.05, 0.95), 0.03, 0.03, 0.3, 'black', seg=4, hull='none', rot=(30, 0, 0))
    wheels4(m, (-0.6, 0.6), (-0.6, 0.6), 0.28, 0.22)
    make('BagTractor', m, ao, cols=[cb(-0.7, -0.95, 0.0, 0.7, 0.95, 1.15), cb(-0.65, -0.3, 1.15, 0.65, 1.0, 1.92)])
    # baggage cart [2, 3]: a flatbed with side rails, a canopy, bags; the drawbar forward (-Y)
    m = new(pal)
    m.bx(-0.85, 0.85, -1.3, 1.3, 0.45, 0.55, 'steelD')
    for x in (-0.79, 0.79):
        m.bx(x - 0.03, x + 0.03, -1.24, 1.24, 0.55, 0.85, 'sky', hull='none', cull='')
    for x in (-0.85, 0.85):
        for y in (-1.27, 1.27):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.55, 1.75, 'steelD', hull='none', cull='bt')
    m.bx(-0.88, 0.88, -1.33, 1.33, 1.75, 1.82, 'sky')
    for (x0, x1, y0, y1, h, c) in ((-0.75, 0.0, -1.2, -0.45, 0.42, 'gA'), (0.05, 0.75, -1.2, -0.6, 0.3, 'navy'), (-0.75, -0.05, -0.35, 0.4, 0.36, 'gB'),
                                   (0.05, 0.72, -0.5, 0.35, 0.5, 'pPurple'), (-0.7, 0.7, 0.5, 1.2, 0.34, 'gD'), (-0.6, 0.2, 0.55, 1.1, 0.62, 'gC')):
        m.bx(x0, x1, y0, y1, 0.55 if h < 0.6 else 0.89, 0.55 + h if h < 0.6 else 1.2, c, cull='b')
    m.bm_((0.0, -1.3, 0.5), (0.0, -2.0, 0.3), 0.06, 'steelD')
    wheels4(m, (-0.7, 0.7), (-0.9, 0.9), 0.24, 0.16)
    make('BagCart', m, ao, cols=[cb(-0.88, -1.33, 0.0, 0.88, 1.33, 1.82)])
    # fuel truck [3, 7]: a cab forward (-Y), the tank (JET A-1), the hose reel and a platform at the back
    m = new(pal)
    m.bx(-1.2, 1.2, -3.4, -1.6, 0.6, 2.6, 'white')
    fq(m, -1.05, 1.05, -3.403, 1.7, 2.45, 'screen')
    glint(m, -0.8, -3.406, 1.75, 0.6, w=0.12, c='glass')
    fq(m, -1.2, 1.2, -3.403, 0.75, 0.95, 'red')
    m.bx(-1.2, 1.2, -1.6, 3.4, 0.55, 0.85, 'steelD')
    cyl_y(m, 0.0, -1.4, 2.6, 1.85, 1.1, 'white', seg=12)
    for s in (-1, 1):
        ib_text.draw(m, 'JET A-1', s * 1.11, 0.6, 1.62, 0.36, 'red', face='x+' if s > 0 else 'x-', font='display', maxw=2.4)
    m.bx(-0.9, 0.9, 2.6, 3.4, 0.85, 1.9, 'steel')
    cyl_x(m, -0.6, 0.6, 3.0, 2.25, 0.32, 'red', seg=8)
    wheels4(m, (-1.0, 1.0), (-2.6, 1.4, 2.6), 0.5, 0.36)
    make('FuelTruck', m, ao, cols=[cb(-1.2, -3.4, 0.0, 1.2, -1.6, 2.6), cb(-1.2, -1.6, 0.0, 1.2, 3.4, 2.95)])
    # passenger stairs truck [2, 6]: a cab forward (-Y) under the top platform (at DOCK, with a canopy), the stair
    # rising from the ground at the back (+Y) to the platform (walkable steps: climb it), side stringers and rails
    m = new(pal)
    m.bx(-0.95, 0.95, -3.0, -1.8, 0.55, 2.0, 'white')
    fq(m, -0.85, 0.85, -3.003, 1.3, 1.9, 'screen')
    fq(m, -0.95, 0.95, -3.003, 0.6, 0.8, 'sky')
    m.bx(-0.95, 0.95, -1.8, 2.6, 0.3, 0.45, 'steelD', cull='')
    cols = []
    n, yb, yt = 9, 3.0, -1.5
    run = (yb - yt) / n
    for k in range(n):
        y1 = yb - k * run
        top = (k + 1) * DOCK / n
        m.bx(-0.7, 0.7, y1 - run, y1, top - 0.06, top, 'steel', hull='full', cull='')
        cols.append(cb(-0.7, y1 - run, 0.0, 0.7, y1, top, True))
    m.bx(-0.72, 0.72, -3.0, -1.5, DOCK - 0.08, DOCK, 'steel', cull='')
    cols.append(cb(-0.8, -3.0, 0.0, 0.8, -1.5, DOCK, True))
    for s in (-1, 1):
        x = s * 0.78
        prof = [(3.0, 0.0), (2.6, 0.0), (-1.6, DOCK - 0.25), (-3.0, DOCK - 0.25), (-3.0, DOCK), (-1.6, DOCK), (3.0, 0.3)]
        m.prism(prof, x - 0.04, x + 0.04, ['sky'])
        m.bm_((x, 2.9, 1.0), (x, -1.6, DOCK + 1.0), 0.05, 'white')
        m.bm_((x, -1.6, DOCK + 1.0), (x, -2.95, DOCK + 1.0), 0.038, 'white')
        for k in range(5):
            ya, yb2 = 3.0 - k * 0.92, 3.0 - (k + 1) * 0.92
            cols.append(cb(x - 0.05, yb2, 0.0, x + 0.05, ya, min(DOCK, (k + 1) * 0.92 / 4.6 * DOCK) + 1.0))
        cols.append(cb(x - 0.05, -3.0, DOCK, x + 0.05, -1.6, DOCK + 1.05))
        m.bx(s * 0.8 - 0.025, s * 0.8 + 0.025, -2.98, -2.93, DOCK, DOCK + 2.1, 'white', hull='none', cull='bt')
    m.bm_((-0.78, -2.97, DOCK + 1.0), (0.78, -2.97, DOCK + 1.0), 0.038, 'white')
    cols.append(cb(-0.8, -3.05, DOCK, 0.8, -2.95, DOCK + 1.05))
    m.bx(-0.85, 0.85, -3.05, -1.5, DOCK + 2.1, DOCK + 2.18, 'sky')
    text_side(m, 'SKYLARK', 0.22, 0.823, 0.6, 1.2, 'paper', 'x+', maxw=1.5)
    text_side(m, 'SKYLARK', 0.22, -0.823, 0.6, 1.2, 'paper', 'x-', maxw=1.5)
    wheels4(m, (-1.0, 1.0), (-2.4, 1.9), 0.4, 0.28)
    make('StairTruck', m, ao, cols=cols)
    # belt loader [2, 6]: a low chassis with an inclined belt (to a hold door at 2.2 m), a driver's seat on the side
    m = new(pal)
    m.bx(-0.8, 0.8, -3.0, 3.0, 0.35, 0.7, 'tug')
    v = [(-0.45, 3.0, 0.75), (0.45, 3.0, 0.75), (0.45, -2.9, 2.25), (-0.45, -2.9, 2.25),
         (-0.45, 3.0, 0.9), (0.45, 3.0, 0.9), (0.45, -2.9, 2.4), (-0.45, -2.9, 2.4)]
    skin(m, (v, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'steel')
    poly(m, [(-0.4, 2.95, 0.905), (0.4, 2.95, 0.905), (0.4, -2.85, 2.405), (-0.4, -2.85, 2.405)], 'rubber', (0, 0.25, 1))
    for y in (-1.5, 0.5):
        m.bm_((0.0, y, 0.7), (0.0, y, 0.75 + (3.0 - y) / 5.9 * 1.5), 0.12, 'steelD')
    m.bx(0.55, 0.8, -1.0, -0.3, 0.7, 1.2, 'black')
    wheels4(m, (-0.7, 0.7), (-2.2, 2.2), 0.3, 0.25)
    make('BeltLoader', m, ao, cols=[cb(-0.8, -3.0, 0.0, 0.8, 3.0, 0.9), cb(-0.45, -2.9, 0.9, 0.45, 0.5, 2.4)])
    # ULD containers on a dolly [2, 2] (AKE shape: a sloped lower side), Skylark tag
    m = new(pal)
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.3, 0.42, 'steelD')
    wheels4(m, (-0.7, 0.7), (-0.6, 0.6), 0.15, 0.12)
    v = [(-0.75, -0.75, 0.42), (0.75, -0.75, 0.42), (0.75, 0.75, 0.42), (-0.4, 0.75, 0.42),
         (-0.75, -0.75, 2.0), (0.75, -0.75, 2.0), (0.75, 0.75, 2.0), (-0.75, 0.75, 1.0)]
    skin(m, (v, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]), 'chrome')
    fq(m, -0.6, 0.6, -0.753, 1.5, 1.8, 'sky')
    text_front(m, 'AKE 2081 SK', 0.12, -0.756, 0.0, 1.6, 'paper', maxw=1.0)
    for k in range(3):
        fq(m, -0.7, 0.7, -0.756, 0.6 + k * 0.28, 0.63 + k * 0.28, 'steel')
    make('ULD', m, ao, cols=[cb(-0.9, -0.9, 0.0, 0.9, 0.9, 2.0)])
    # ground power unit [2, 2] with its cable coiled on top
    m = new(pal)
    m.bx(-0.7, 0.7, -0.9, 0.9, 0.35, 1.4, 'sun')
    fq(m, -0.6, 0.6, -0.903, 0.6, 1.25, 'steelD')
    for k in range(5):
        fq(m, -0.55, 0.55, -0.906, 0.68 + k * 0.11, 0.72 + k * 0.11, 'black')
    m.cy((0.0, 0.3, 1.4), 0.4, 0.4, 0.14, 'black', seg=8)
    m.bm_((0.0, -0.9, 0.5), (0.0, -1.5, 0.3), 0.06, 'steelD')
    wheels4(m, (-0.65, 0.65), (-0.6, 0.6), 0.22, 0.14)
    make('GPU', m, ao, cols=[cb(-0.7, -0.9, 0.0, 0.7, 0.9, 1.54)])
    # towbar [1, 4] (lying on the apron)
    m = new(pal)
    m.bm_((-0.4, 1.7, 0.25), (0.0, -1.8, 0.25), 0.09, 'sun')
    m.bm_((0.4, 1.7, 0.25), (0.0, -1.8, 0.25), 0.09, 'sun')
    m.bx(-0.45, 0.45, 1.6, 1.8, 0.15, 0.35, 'steelD')
    for x in (-0.35, 0.35):
        m.cy((x - 0.04, 1.2, 0.15), 0.15, 0.15, 0.08, 'tire', seg=6, rot=(0, 90, 0), hull='none')
    make('Towbar', m, ao, cols=[cb(-0.45, 1.0, 0.0, 0.45, 1.8, 0.4), cb(-0.28, -0.3, 0.0, 0.28, 1.0, 0.35), cb(-0.12, -1.8, 0.0, 0.12, -0.3, 0.35)])


def build_shop(pal, ao):
    # tool crib [4, 3] (front -Y, back to a wall): a wire-mesh cage on a steel frame with a service hatch, shelves
    # of parts bins inside
    m = new(pal)
    for x in (-1.95, 1.95):
        for y in (-1.45, 1.45):
            m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 2.6, 'steelD', cull='b')
    m.bx(-1.95, 1.95, -1.45, 1.45, 2.56, 2.64, 'steelD', hull='none', cull='b')
    # mesh walls: painted grids on both faces of the front and sides
    def mesh_y(y, x0, x1, z0, z1, face):
        Q = fq if face < 0 else bq
        for k in range(int((x1 - x0) / 0.25) + 1):
            x = x0 + k * 0.25
            Q(m, x - 0.01, x + 0.01, y, z0, z1, 'steel')
        for k in range(int((z1 - z0) / 0.25) + 1):
            z = z0 + k * 0.25
            Q(m, x0, x1, y + face * 0.003, z - 0.01, z + 0.01, 'steel')

    def mesh_x(x, y0, y1, z0, z1, face):
        Q = rq if face > 0 else lq
        for k in range(int((y1 - y0) / 0.25) + 1):
            y = y0 + k * 0.25
            Q(m, x, y - 0.01, y + 0.01, z0, z1, 'steel')
        for k in range(int((z1 - z0) / 0.25) + 1):
            z = z0 + k * 0.25
            Q(m, x + face * 0.003, y0, y1, z - 0.01, z + 0.01, 'steel')
    mesh_y(-1.45, -1.9, -0.6, 0.1, 2.5, -1)
    mesh_y(-1.45, 0.6, 1.9, 0.1, 2.5, -1)
    mesh_y(-1.45, -0.6, 0.6, 1.3, 2.5, -1)
    for s in (-1, 1):
        mesh_x(s * 1.95, -1.4, 1.4, 0.1, 2.5, s)
    m.bx(-0.6, 0.6, -1.6, -1.3, 0.95, 1.05, 'steel')
    m.bx(-0.6, 0.6, -1.5, -1.4, 0.0, 0.95, 'steelD', cull='b')
    for z in (0.5, 1.2, 1.9):
        m.bx(-1.8, 1.8, 0.7, 1.35, z - 0.04, z, 'steelD', hull='none', cull='')
        for k in range(6):
            x = -1.5 + k * 0.6
            m.bx(x - 0.22, x + 0.22, 0.8, 1.25, z, z + 0.22, GOODS[(k + int(z * 3)) % 4], hull='none', cull='b')
    m.bx(-0.5, 0.5, -1.5, -1.45, 2.64, 2.95, 'navy', hull='none', cull='k')
    text_front(m, 'TOOL CRIB', 0.18, -1.503, 0.0, 2.72, 'paper', maxw=0.9)
    make('ToolCrib', m, ao, cols=[cb(-1.99, -1.6, 0.0, 1.99, 1.49, 2.64)])
    # apron light mast: a 12 m pole on a concrete foot with a lamp head (glow companion: the lamps)
    m = new(pal)
    g = new(pal)
    m.cy((0, 0, 0), 0.35, 0.35, 0.6, 'conc', seg=8)
    m.cy((0, 0, 0.6), 0.16, 0.1, 11.4, 'steel', seg=6, caps=False)
    m.bx(-1.0, 1.0, -0.12, 0.12, 12.0, 12.12, 'steelD')
    for x in (-0.65, 0.0, 0.65):
        m.bx(x - 0.25, x + 0.25, -0.3, 0.1, 11.7, 12.0, 'steelD')
        dq(g, x - 0.22, x + 0.22, -0.27, 0.07, 11.697, 'lightW')
    m.cy((0, 0, 0.6), 0.2, 0.2, 1.2, 'sun', seg=6, caps=False, hull='none')
    make('Mast', m, ao, cols=[cb(-0.35, -0.35, 0.0, 0.35, 0.35, 0.6), cb(-0.16, -0.16, 0.6, 0.16, 0.16, 12.0)])
    make_glow('Mast_LED', g)


def build_hangar(pal, ao):
    build_jet(pal, ao)
    build_gse(pal, ao)
    build_shop(pal, ao)
