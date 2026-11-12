"""kit-toyfactory warehouse: tall pallet racks full of printed toy cartons ([3, 2] bays, 9.6 m, five pallet levels),
the dispatch mezzanine (steel stair, guard rails, deck columns), the landmark dispatch office on the deck with the
giant TOPSY mascot bear on its roof, pick + pack stations, the forklift charging station, the returns cage and a
showpiece shipping crate (see tf_base.py for conventions). Rack bays run along Blender X with their pallet faces at
Y = -1 / +1 (the aisles); every bay draws the upright frame at its -X end only, the run's last piece (`EndR`) also at
+X. Goods use the gA - gD cells (repainted per placed copy by the theme)."""
import math
import random

from tf_base import *  # noqa: F401,F403
import tf_base as B
from ms_racks import beam

LEVELS = (1.9, 3.8, 5.7, 7.6)
HT = 9.6


def frame(m, x, s, Ht, end=False):
    """one upright frame at x (from x to x + 0.08) on the side s (-1 front aisle, 1 back aisle): two posts, and on an
    end frame the diagonal bracing between them (every 2.4 m) and a yellow column guard"""
    for (y0, y1, hl) in ((0.92, 1.0, 'full'), (0.06, 0.14, 'none')):
        a, b = sorted((s * y0, s * y1))
        m.bx(x, x + 0.08, a, b, 0.0, Ht, 'rackB', cull='bt', hull=hl)
    if end:
        xm, k, z = x + 0.04, 0, 0.3
        while z + 2.4 < Ht:
            ya, yb = (s * 0.14, s * 0.92) if k % 2 == 0 else (s * 0.92, s * 0.14)
            m.bm_((xm + (0.004 if k % 2 else -0.004), ya, z), (xm + (0.004 if k % 2 else -0.004), yb, z + 2.4), 0.03, 'rackB', hull='none')
            z += 2.4
            k += 1
        a, b = sorted((s * 0.86, s * 1.08))
        g0, g1 = (x - 0.03, x + 0.16) if x < 0 else (x - 0.08, x + 0.11)
        m.bx(g0, g1, a, b, 0.0, 0.45, 'hazY', cull='b')


def slot(m, rnd, s, a, b, z, hmax):
    """one pallet position of one side, from a to b along X at beam height z: a pallet and a load of printed toy
    cartons (one block with painted carton seams and the product panel), sometimes empty"""
    yi, yo = sorted((s * 0.1, s * 1.02))
    m.bx(a, b, yi, yo, z, z + 0.14, 'wood', cull='bkt' if s < 0 else 'bft', hull='none')
    face = fq if s < 0 else bq
    face(m, a + (b - a) * 0.2, b - (b - a) * 0.2, s * 1.023, z + 0.012, z + 0.1, 'woodD')
    hgt = rnd.uniform(0.7, 1.0) * hmax
    c = rnd.choice(GOODS)
    z0, z1 = z + 0.14, z + 0.14 + hgt
    ya, yb = yi + 0.02, yo - 0.02
    m.bx(a + 0.02, b - 0.02, ya, yb, z0, z1, c, cull='bk' if s < 0 else 'bf', hull='full' if z < 5 else 'none')
    yf = s * 1.003
    nr = 1
    zz = z0 + hgt * 0.55
    face(m, a + 0.02, b - 0.02, yf, zz - 0.01, zz + 0.01, 'cardD')
    pw = (b - a) * 0.2
    for xc in ((a + b) / 2,):
        za = z0 + hgt * (0.12 if nr == 1 else 0.06)
        face(m, xc - pw, xc + pw, s * 1.009, za, za + min(0.36, hgt * 0.32), 'pWhite')
        face(m, xc - pw * 0.55, xc + pw * 0.55, s * 1.012, za + 0.05, za + min(0.31, hgt * 0.32) - 0.05, rnd.choice(['gA', 'gC', 'gB', 'pPink', 'gD']))


def tall_bay(pal, ao, name, seed, end=None):
    rnd = random.Random(seed)
    m = new(pal)
    xb = 1.42 if end == 'R' else 1.5
    for s in (-1, 1):
        frame(m, -1.5, s, HT, end=(end == 'L'))
        if end == 'R':
            frame(m, 1.42, s, HT, end=True)
        w = xb - (-1.42)
        slots = ((-1.42 + 0.05, -1.42 + w / 2 - 0.03), (-1.42 + w / 2 + 0.03, xb - 0.05))
        for (a, b) in slots:
            slot(m, rnd, s, a, b, 0.0, 1.55)
        a2, b2 = sorted((s * 0.08, s * 0.9))
        for li, z in enumerate(LEVELS):
            beam(m, -1.42, xb, s, z)
            dq(m, -1.42, xb, a2, b2, z - 0.03, 'wire')
            for (a, b) in slots:
                if rnd.random() < (0.12 if li < 3 else 0.3):
                    continue
                slot(m, rnd, s, a, b, z, 1.5 if li < 3 else 1.6)
        (fq if s < 0 else bq)(m, -1.5, -1.42, s * 1.003, 2.3, 2.6, 'paper')
    make(name, m, ao, cols=[cb(-1.5, -1.02, 0.0, 1.5, 1.02, HT)])


def build_racks(pal, ao):
    tall_bay(pal, ao, 'Tall_A', 721)
    tall_bay(pal, ao, 'Tall_EndL', 724, end='L')
    tall_bay(pal, ao, 'Tall_EndR', 725, end='R')


# ================================================================ mezzanine: stair, rails, columns
def build_mezzanine(pal, ao):
    # steel stair [2, 7] rising toward Blender +Y (game north) to the deck at 3.5 m: 13 steps and a top landing
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
        m.prism(prof, a, b, ['brandB'])
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
    # guard rail (modelled along Blender Y; the link placer joins half modules): top / mid rails and a kick plate
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


# ================================================================ landmark: the dispatch office on the deck [8, 5]
def build_office(pal, ao):
    """a site-built office box on the deck ("@layer 3.5" grid): block walls 2.9 m, a ribbon of open windows over the
    deck front (-Y), a doorway at the east end of the front, desks with monitors and a plan table inside, a flat roof
    with the DISPATCH fascia -- and the giant TOPSY mascot (a faceless plush bear, 3.6 m sitting) on the roof"""
    m = new(pal)
    g = new(pal)
    Hh, t = 2.9, 0.15
    X0, X1, Y0, Y1 = -3.9, 3.9, -2.4, 2.4
    m.bx(X0, X1, Y1 - t, Y1, 0.0, Hh, 'wallC', cull='b')
    m.bx(X0, X0 + t, Y0, Y1 - t, 0.0, Hh, 'wallC', cull='b')
    m.bx(X1 - t, X1, Y0, Y1 - t, 0.0, Hh, 'wallC', cull='b')
    m.bx(X0 + t, 2.2, Y0, Y0 + t, 0.0, 1.0, 'wallC', cull='b')
    m.bx(X0 + t, X1 - t, Y0, Y0 + t, 2.1, Hh, 'wallC')
    for x in (-2.6, -1.3, 0.0, 1.1):
        m.bx(x - 0.05, x + 0.05, Y0 + 0.02, Y0 + t - 0.02, 1.0, 2.1, 'steelD', cull='bt')
    m.bx(2.2, 2.3, Y0, Y0 + t, 0.0, 2.1, 'steelD', cull='bt')
    m.bx(X0 + t, 2.2, Y0 - 0.06, Y0, 0.96, 1.02, 'steelD')
    m.bx(3.69, 3.74, Y0 + t, Y0 + 1.1, 0.0, 2.05, 'brandR')
    fq(m, X0 + t, 2.2, Y0 - 0.003, 0.0, 0.14, 'concD')
    # roof slab, the fascia sign
    m.bx(X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1, Hh, Hh + 0.25, 'steelD')
    m.bx(-3.0, 3.0, Y0 - 0.2, Y0 - 0.1, Hh + 0.1, Hh + 0.75, 'brandB')
    text_front(m, 'DISPATCH OFFICE', 0.36, Y0 - 0.203, 0.0, Hh + 0.24, 'paper', maxw=5.4)
    # inside: two desks with monitors and chairs, the plan table with a pick list, filing cabinets, a whiteboard
    for x in (-2.5, -0.4):
        m.bx(x - 0.75, x + 0.75, Y1 - 0.9, Y1 - t - 0.02, 0.72, 0.76, 'cream')
        m.bx(x - 0.7, x - 0.62, Y1 - 0.85, Y1 - t - 0.05, 0.0, 0.72, 'grey', hull='none', cull='b')
        m.bx(x + 0.62, x + 0.7, Y1 - 0.85, Y1 - t - 0.05, 0.0, 0.72, 'grey', hull='none', cull='b')
        m.bx(x - 0.3, x + 0.3, Y1 - 0.45, Y1 - 0.4, 0.8, 1.15, 'pBlack')
        fq(g, x - 0.27, x + 0.27, Y1 - 0.453, 0.83, 1.12, 'scrB')
        m.bx(x - 0.04, x + 0.04, Y1 - 0.42, Y1 - 0.36, 0.76, 0.8, 'pBlack', hull='none')
    m.bx(1.2, 2.6, -0.5, 0.5, 0.88, 0.92, 'cream')
    m.bx(1.25, 1.35, -0.45, 0.45, 0.0, 0.88, 'grey', hull='none', cull='b')
    m.bx(2.45, 2.55, -0.45, 0.45, 0.0, 0.88, 'grey', hull='none', cull='b')
    uq(m, 1.35, 2.3, -0.35, 0.3, 0.923, 'paper')
    uq(m, 1.5, 2.0, -0.2, 0.1, 0.926, 'brandB')
    m.bx(X1 - t - 0.5, X1 - t, 0.4, 1.4, 0.0, 1.35, 'steel', cull='b')
    m.bx(X0 + t, X0 + t + 0.03, -1.2, 0.8, 1.1, 2.0, 'pWhite', cull='l')
    for k in range(4):
        rq(m, X0 + t + 0.033, -1.0 + k * 0.4, -0.75 + k * 0.4, 1.3 + (k % 2) * 0.25, 1.36 + (k % 2) * 0.25, ['brandR', 'brandB', 'gD', 'pBlack'][k])
    rq(m, X1 + 0.003, -1.6, 1.6, 1.4, 2.4, 'brandR')
    text_side(m, 'TOPSY', 0.6, X1 + 0.006, 0.0, 1.6, 'paper', 'x+', maxw=2.9)
    # the mascot: a giant faceless plush bear sitting on the roof (a red bow tie), waving a pennant
    Z = Hh + 0.25
    bear(m, -1.2, 0.6, Z, 2.6, c='pBrown', paw='cream', lod=1)
    m.bx(-1.75, -0.65, -0.36, -0.12, Z + 2.85, Z + 3.25, 'brandR')
    m.bx(-1.33, -1.07, -0.42, -0.14, Z + 2.9, Z + 3.2, 'brandR')
    m.cy((-2.25, 0.4, Z + 1.4), 0.04, 0.04, 2.6, 'steel', seg=6)
    poly(m, [(-2.25, 0.4, Z + 4.0), (-2.25, 0.4, Z + 3.4), (-3.3, 0.4, Z + 3.7)], 'hazY', (0, -1, 0))
    poly(m, [(-2.25, 0.4, Z + 4.0), (-3.3, 0.4, Z + 3.7), (-2.25, 0.4, Z + 3.4)], 'hazY', (0, 1, 0))
    # roof sign on a frame at the east end
    for x in (0.6, 3.4):
        m.bx(x - 0.05, x + 0.05, 1.0, 1.1, Z, Z + 1.0, 'steelD', hull='none', cull='b')
    m.bx(0.4, 3.6, 0.95, 1.1, Z + 1.0, Z + 2.2, 'hazY')
    text_front(m, 'TOYS', 0.75, 0.947, 2.0, Z + 1.2, 'brandR', maxw=2.9)
    make('Landmark_Office', m, ao, cols=[
        cb(X0, Y1 - t, 0.0, X1, Y1, Hh), cb(X0, Y0, 0.0, X0 + t, Y1 - t, Hh), cb(X1 - t, Y0, 0.0, X1, Y1 - t, Hh),
        cb(X0 + t, Y0 - 0.06, 0.0, 2.3, Y0 + t, 1.02), cb(X0 + t, Y0, 2.1, X1 - t, Y0 + t, Hh),
        cb(3.69, Y0 + t, 0.0, 3.74, Y0 + 1.1, 2.05),
        cb(X0 - 0.1, Y0 - 0.1, Hh, X1 + 0.1, Y1 + 0.1, Hh + 0.25),
        cb(-3.25, Y1 - 0.9, 0.0, 0.35, Y1 - t, 0.76), cb(1.2, -0.5, 0.0, 2.6, 0.5, 0.92), cb(X1 - t - 0.5, 0.4, 0.0, X1 - t, 1.4, 1.35)])
    make_glow('Landmark_Office_LED', g)


# ================================================================ pick + pack, charging, returns, the crate
def build_floor_props(pal, ao):
    # pick + pack station [2, 2] (front -Y): a packing table with a monitor, scanner, label printer and scale, a
    # roll of brown paper, a carton being packed with a toy, a tote rack behind
    for v in range(1):
        rnd = random.Random(800 + v)
        m = new(pal)
        g = new(pal)
        m.bx(-0.95, 0.95, -0.7, 0.2, 0.86, 0.92, 'cream')
        for (x, y) in ((-0.88, -0.63), (0.88, -0.63), (-0.88, 0.13), (0.88, 0.13)):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.86, 'steelD', hull='none', cull='bt')
        m.bx(-0.84, 0.84, -0.6, 0.1, 0.25, 0.28, 'steelD', hull='none', cull='')
        for k in range(3):
            m.bx(-0.8, 0.2, -0.56, 0.06, 0.28 + k * 0.03, 0.305 + k * 0.03, 'card' if k % 2 else 'cardL', hull='none', cull='b' if k == 0 else '')
        m.bm_((0.6, 0.14, 0.92), (0.6, 0.14, 1.35), 0.04, 'steelD')
        m.bx(0.3, 0.9, 0.05, 0.12, 1.2, 1.55, 'pBlack')
        fq(g, 0.33, 0.87, 0.047, 1.23, 1.52, 'scrB' if v else 'scrG')
        m.bx(-0.85, -0.45, -0.1, 0.18, 0.92, 1.12, 'machW')
        fq(m, -0.8, -0.5, -0.103, 1.0, 1.05, 'pBlack')
        carton(m, -0.3, 0.25, -0.55, -0.1, 0.92, 1.25, 'card', art=None)
        if v:
            duck(m, 0.0, -0.32, 1.25, 0.3)
        else:
            tin_robot(m, -0.02, -0.32, 1.25, 0.3, c='gA')
        m.cy((0.55, -0.4, 0.92), 0.12, 0.12, 0.04, 'steel', seg=10)
        m.cy((-0.92, -0.25, 1.045), 0.12, 0.12, 0.6, 'cardL', seg=10, rot=(0, 90, 0))
        # tote rack behind the table (the back row of cells)
        for sx in (-1, 1):
            m.bx(sx * 0.92 - 0.03, sx * 0.92 + 0.03, 0.62, 0.68, 0.0, 1.8, 'hazY', cull='b')
        for z in (0.55, 1.3):
            m.bx(-0.92, 0.92, 0.35, 0.95, z - 0.03, z, 'steel', cull='')
            for j in range(4):
                x0 = -0.88 + j * 0.44
                m.bx(x0 + 0.01, x0 + 0.42, 0.38, 0.92, z, z + 0.24, rnd.choice(['gB', 'gA', 'gC', 'gD', 'pTeal']), cull='bk', hull='none')
                fq(m, x0 + 0.1, x0 + 0.3, 0.377, z + 0.07, z + 0.15, 'paper')
        make('PackStation_' + 'AB'[v], m, ao, cols=[cb(-0.95, -0.7, 0.0, 0.95, 0.2, 0.92), cb(-0.95, 0.35, 0.0, 0.95, 0.95, 1.8), cb(0.3, 0.05, 0.92, 0.9, 0.12, 1.55)])
        make_glow('PackStation_' + 'AB'[v] + '_LED', g)
    # forklift charging station [2, 1] (against the wall, front -Y): two charger cabinets with screens (glow),
    # cables coiled on hooks, a spare battery on a stand, the yellow floor box
    m = new(pal)
    g = new(pal)
    for x in (-0.5, 0.5):
        m.bx(x - 0.32, x + 0.32, -0.1, 0.4, 0.6, 1.6, 'machW', cull='')
        m.bx(x - 0.36, x + 0.36, -0.14, 0.4, 1.6, 1.66, 'steelD')
        fq(m, x - 0.26, x + 0.26, -0.103, 0.7, 1.2, 'steel')
        m.bx(x - 0.15, x + 0.15, -0.16, -0.1, 1.28, 1.5, 'pBlack')
        fq(g, x - 0.13, x + 0.13, -0.163, 1.3, 1.48, 'scrG')
        m.bx(x - 0.03, x + 0.03, 0.34, 0.4, 0.0, 0.6, 'steelD', hull='none', cull='b')
        tube(m, (x + 0.2, -0.12, 0.8), (x + 0.25, -0.35, 0.3), 0.03, 'black', seg=5, hull='none')
        m.bx(x + 0.15, x + 0.35, -0.45, -0.25, 0.0, 0.3, 'brandR', cull='b')
    m.bx(-0.95, 0.95, 0.1, 0.4, 1.75, 2.1, 'brandB', cull='')
    text_front(m, 'FORKLIFT CHARGING', 0.13, 0.097, 0.0, 1.85, 'paper', maxw=1.7)
    make('Charger', m, ao, cols=[cb(-0.85, -0.16, 0.0, 0.85, 0.4, 1.66), cb(-0.4, -0.45, 0.0, 0.9, -0.25, 0.3)])
    make_glow('Charger_LED', g)
    # returns cage [2, 2]: a wire-mesh cage (posts, mesh panels painted as a grid, an open door), damaged cartons
    # and a loose bear inside, the RETURNS sign
    m = new(pal)
    rnd = random.Random(830)
    X = 0.95
    for (x, y) in ((-X, -X), (X, -X), (-X, X), (X, X)):
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 2.2, 'steelD', cull='b')
    def mesh_x(y, x0, x1, s):
        f = fq if s < 0 else bq
        for k in range(int((x1 - x0) / 0.36) + 1):
            x = x0 + k * 0.36
            f(m, x - 0.006, x + 0.006, y, 0.05, 2.15, 'steel')
        for k in range(7):
            z = 0.05 + k * 0.35
            f(m, x0, x1, y + s * 0.003, z - 0.006, z + 0.006, 'steel')
    def mesh_y(x, y0, y1, s):
        f = lq if s < 0 else rq
        for k in range(int((y1 - y0) / 0.36) + 1):
            y = y0 + k * 0.36
            f(m, x, y - 0.006, y + 0.006, 0.05, 2.15, 'steel')
        for k in range(7):
            z = 0.05 + k * 0.35
            f(m, x + s * 0.003, y0, y1, z - 0.006, z + 0.006, 'steel')
    mesh_x(-X - 0.004, -X + 0.04, X - 0.04, -1)
    mesh_x(-X + 0.004, -X + 0.04, X - 0.04, 1)
    mesh_x(X - 0.004, -X + 0.04, X - 0.04, -1)
    mesh_x(X + 0.004, -X + 0.04, X - 0.04, 1)
    mesh_y(-X - 0.004, -X + 0.04, X - 0.04, -1)
    mesh_y(-X + 0.004, -X + 0.04, X - 0.04, 1)
    mesh_y(X - 0.004, -X + 0.04, X - 0.04, -1)
    mesh_y(X + 0.004, -X + 0.04, X - 0.04, 1)
    m.bx(-X, X, -X, X, 2.2, 2.24, 'steelD', cull='')
    for (x, y, c, hh) in ((-0.5, 0.4, 'gB', 0.5), (0.3, 0.45, 'card', 0.42)):
        z0 = 0.0 if c != 'gA' else 0.42
        carton(m, x - 0.25, x + 0.25, y - 0.22, y + 0.22, z0, z0 + hh, c, art='pWhite')
    m.bx(-0.7, 0.7, -X - 0.08, -X - 0.04, 1.6, 2.0, 'brandR', cull='')
    text_front(m, 'RETURNS', 0.24, -X - 0.083, 0.0, 1.68, 'paper', maxw=1.3)
    make('Cage', m, ao, cols=[cb(-X - 0.04, -X - 0.04, 0.0, X + 0.04, X + 0.04, 2.24)])


def build_store(pal, ao):
    build_racks(pal, ao)
    build_mezzanine(pal, ao)
    build_office(pal, ao)
    build_floor_props(pal, ao)
