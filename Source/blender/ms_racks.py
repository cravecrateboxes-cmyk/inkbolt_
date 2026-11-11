"""kit-megastore racking and stock: sales-floor pallet racks (double-sided [3, 2] bays, 5.6 m: two shelves of goods
under two pallet levels), stockroom racks (9 m, five pallet levels), gondola endcaps, floor pallets (water, paper,
TVs, wrapped mixed loads, sacks, a low drop, empty pallet stacks), cardboard bales and gaylords.

Rack bays run along Blender X (the placer's run direction), their shelf faces at Y = -1 and +1 (the aisles). Every
bay draws the upright frame at its -X end only; the run's last piece (`EndR`) also draws the one at +X, so neighbouring
bays never stack two frames in one place. Goods use the gA - gD cells (repainted per placed copy by the theme)."""
import math
import random

from ms_base import *  # noqa: F401,F403
import ms_base as B

PROD = GOODS + ['card', 'cardL', 'pWhite']


def frame(m, x, s, Ht, end=False):
    """one upright frame at x (from x to x + 0.08) on the side s (-1 front aisle, 1 back aisle): two posts, and on an
    end frame the diagonal bracing between them and a yellow column guard"""
    for (y0, y1, hl) in ((0.92, 1.0, 'full'), (0.06, 0.14, 'none')):
        a, b = sorted((s * y0, s * y1))
        m.bx(x, x + 0.08, a, b, 0.0, Ht, 'rackB', cull='bt', hull=hl)
    if end:
        xm = x + 0.04
        k = 0
        z = 0.3
        while z + 1.3 < Ht:
            ya, yb = (s * 0.14, s * 0.92) if k % 2 == 0 else (s * 0.92, s * 0.14)
            xk = xm + (0.004 if k % 2 else -0.004)
            m.bm_((xk, ya, z), (xk, yb, z + 1.3), 0.03, 'rackB', hull='none')
            z += 1.3
            k += 1
        a, b = sorted((s * 0.86, s * 1.08))
        g0, g1 = (x - 0.03, x + 0.16) if x < 0 else (x - 0.08, x + 0.11)
        m.bx(g0, g1, a, b, 0.0, 0.45, 'hazY', cull='b')


def beam(m, x0, x1, s, z, c='rackO'):
    """a front step beam with location tags"""
    a, b = sorted((s * 0.9, s * 1.0))
    m.bx(x0, x1, a, b, z - 0.12, z, c, cull='lrb' if z - 0.12 <= 0.001 else 'lr')
    xt = x0 + (x1 - x0) * 0.3
    (fq if s < 0 else bq)(m, xt - 0.08, xt + 0.08, s * 1.003, z - 0.1, z - 0.03, 'paper')


def bay_slots(m, rnd, s, x0, x1, z, Hmax, colors, empty=0.12):
    """one pallet level of one side: two pallet slots from x0 to x1 -- a wrapped load or a carton stack each,
    sometimes an empty slot (the wire deck shows)"""
    w = (x1 - x0)
    slots = ((x0 + 0.05, x0 + w / 2 - 0.03), (x0 + w / 2 + 0.03, x1 - 0.05))
    yi, yo = sorted((s * 0.1, s * 1.02))
    for (a, b) in slots:
        if rnd.random() < empty:
            continue
        # pallet: one block with the two dark fork gaps painted on its aisle face
        m.bx(a, b, yi, yo, z, z + 0.14, 'wood', cull='b', hull='none')
        for f in (0.22, 0.62):
            xa = a + (b - a) * f
            (fq if s < 0 else bq)(m, xa, xa + (b - a) * 0.16, s * 1.023, z + 0.012, z + 0.1, 'woodD')
        hgt = rnd.uniform(0.6, 1.0) * (Hmax - 0.16)
        ya, yb = yi + 0.03, yo - 0.03
        c = rnd.choice(colors)
        z0, z1 = z + 0.14, z + 0.14 + hgt
        if rnd.random() < 0.75:   # shrink-wrapped load
            m.bx(a + 0.02, b - 0.02, ya, yb, z0, z1, c, cull='bk' if s < 0 else 'bf')
            yf = s * 0.993
            (fq if s < 0 else bq)(m, a + 0.02, b - 0.02, yf, z0 + hgt * 0.55, z0 + hgt * 0.78, 'wrap')
            uq(m, a + 0.06, b - 0.06, ya + 0.05, yb - 0.05, z1 + 0.003, 'wrap')
        else:                       # cartons: two columns of different heights, tape on top
            xm = (a + b) / 2 + rnd.uniform(-0.15, 0.15)
            for (p, q, f) in ((a + 0.02, xm - 0.01, 1.0), (xm + 0.01, b - 0.02, rnd.uniform(0.55, 0.9))):
                top = z0 + hgt * f
                cc = rnd.choice(['card', 'cardD', 'cardL', c])
                m.bx(p, q, ya, yb, z0, top, cc, cull='bk' if s < 0 else 'bf')
                xmid = (p + q) / 2
                uq(m, xmid - 0.04, xmid + 0.04, ya, yb, top + 0.003, 'cardD' if cc != 'cardD' else 'cardL')
                (fq if s < 0 else bq)(m, p + 0.08, q - 0.08, s * 0.993, z0 + (top - z0) * 0.55, z0 + (top - z0) * 0.8, rnd.choice(['paper', 'gA', 'gB']))


def sales_bay(pal, ao, name, seed, kinds, end=None):
    """[3, 2] sales rack bay, 5.6 m: two shelves of goods 0.12 - 1.92 m, pallet levels on beams at 2.07 and 3.87 m"""
    rnd = random.Random(seed)
    m = new(pal)
    Ht = 5.6
    xb = 1.42 if end == 'R' else 1.5
    for s in (-1, 1):
        frame(m, -1.5, s, Ht, end=(end == 'L'))
        if end == 'R':
            frame(m, 1.42, s, Ht, end=True)
        beam(m, -1.42, xb, s, 0.12, 'rackO')
        a2, b2 = sorted((s * 0.9, s * 1.0))
        m.bx(-1.42, xb, a2, b2, 0.95, 1.03, 'rackG', cull='lr')
        a, b = sorted((s * 0.08, s * 0.9))
        uq(m, -1.42, xb, a, b, 1.0, 'wire')
        for k in range(2):
            xt = -0.9 + k * 1.6
            (fq if s < 0 else bq)(m, xt - 0.07, xt + 0.07, s * 1.003, 0.96, 1.02, rnd.choice(['paper', 'paper', 'hazY']))
        for z in (2.07, 3.87):
            beam(m, -1.42, xb, s, z)
            dq(m, -1.42, xb, a, b, z - 0.03, 'wire')
        kind = kinds[0 if s < 0 else 1]
        yi, yo = sorted((s * 0.08, s * 0.97))
        cols, nb = {'grocery': (GOODS + ['card'], 2), 'paper': (['pWhite', 'pWhite', 'gA', 'gB'], 2),
                    'bottles': (['pSky', 'gB', 'pWhite', 'gA'], 2), 'bulk': (['cardL', 'gC', 'gD', 'pWhite'], 2)}[kind]
        shelf_row(m, rnd, -1.4, xb - 0.03, yi, yo, 0.125, 0.94, cols, face=s, nb=nb)
        shelf_row(m, rnd, -1.4, xb - 0.03, yi, yo, 1.035, 1.93, cols, face=s, nb=nb)
        bay_slots(m, rnd, s, -1.42, xb, 2.07, 1.72, PROD)
        bay_slots(m, rnd, s, -1.42, xb, 3.87, 1.6, PROD)
    make(name, m, ao, cols=[cb(-1.5, -1.02, 0.0, 1.5, 1.02, Ht)])


def tall_bay(pal, ao, name, seed, end=None):
    """[3, 2] stockroom rack bay, 8.6 m: pallets on the floor and on four beam levels (1.75 / 3.5 / 5.25 / 7.0 m)"""
    rnd = random.Random(seed)
    m = new(pal)
    Ht = 8.6
    xb = 1.42 if end == 'R' else 1.5
    for s in (-1, 1):
        frame(m, -1.5, s, Ht, end=(end == 'L'))
        if end == 'R':
            frame(m, 1.42, s, Ht, end=True)
        bay_slots(m, rnd, s, -1.42, xb, 0.0, 1.6, PROD, empty=0.05)
        a, b = sorted((s * 0.08, s * 0.9))
        for z in (1.75, 3.5, 5.25, 7.0):
            beam(m, -1.42, xb, s, z)
            dq(m, -1.42, xb, a, b, z - 0.03, 'wire')
            bay_slots(m, rnd, s, -1.42, xb, z, 1.5, PROD, empty=0.25)
        (fq if s < 0 else bq)(m, -1.5, -1.42, s * 1.003, 2.3, 2.6, 'paper')
    make(name, m, ao, cols=[cb(-1.5, -1.02, 0.0, 1.5, 1.02, Ht)])


def build_racks(pal, ao):
    sales_bay(pal, ao, 'Rack_A', 11, ('grocery', 'paper'))
    sales_bay(pal, ao, 'Rack_B', 12, ('bottles', 'bulk'))
    sales_bay(pal, ao, 'Rack_EndL', 15, ('paper', 'grocery'), end='L')
    sales_bay(pal, ao, 'Rack_EndR', 16, ('bulk', 'bottles'), end='R')
    tall_bay(pal, ao, 'Tall_A', 21)
    tall_bay(pal, ao, 'Tall_B', 27)
    tall_bay(pal, ao, 'Tall_EndL', 24, end='L')
    tall_bay(pal, ao, 'Tall_EndR', 25, end='R')


# ================================================================ endcaps [2, 1] (front -Y), floor pallets [1, 1]
def build_endcaps(pal, ao):
    for v, (word, c) in enumerate((('HOT BUY', 'brandR'), ('SAVE 30%', 'hazY'))):
        rnd = random.Random(30 + v)
        m = new(pal)
        m.bx(-0.98, 0.98, -0.45, 0.45, 0.0, 0.14, 'grey', cull='b')
        m.bx(-0.98, 0.98, 0.3, 0.45, 0.14, 1.75, 'pWhite', cull='b')
        for sx in (-1, 1):
            a, b = sorted((sx * 0.98, sx * 0.94))
            m.bx(a, b, -0.45, 0.3, 0.14, 1.5, 'grey', cull='b')
        for z in (0.14, 0.72, 1.24):
            if z > 0.2:
                m.bx(-0.94, 0.94, -0.42, 0.3, z, z + 0.03, 'chrome', hull='none', cull='b')
            shelf_row(m, rnd, -0.92, 0.92, -0.4, 0.27, z + 0.033, z + (0.513 if z < 1.2 else 0.45), PROD, face=-1, nb=2)
        m.bx(-0.9, 0.9, 0.3, 0.38, 1.75, 2.15, c, cull='b')
        text_front(m, word, 0.26, 0.297, 0.0, 1.82, 'black' if c == 'hazY' else 'paper', maxw=1.6)
        make('Endcap_' + 'AB'[v], m, ao, cols=[cb(-0.98, -0.45, 0.0, 0.98, 0.45, 1.75)])


def pallet_piece(pal, ao, name, fn, h):
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    fn(m)
    make(name, m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, h)])


def build_pallets(pal, ao):
    def water(m):   # four layers of 24-packs, each tray wrapped
        for k in range(4):
            z = 0.14 + k * 0.28
            for (a, b) in ((-0.46, -0.01), (0.01, 0.46)):
                for (c0, c1) in ((-0.46, -0.01), (0.01, 0.46)):
                    m.bx(a, b, c0, c1, z, z + 0.27, 'pSky', cull='b')
            for sy in (-1, 1):
                (fq if sy < 0 else bq)(m, -0.46, 0.46, sy * 0.463, z + 0.1, z + 0.17, 'gB')
            lq(m, -0.463, -0.46, 0.46, z + 0.1, z + 0.17, 'gB')
            rq(m, 0.463, -0.46, 0.46, z + 0.1, z + 0.17, 'gB')
    pallet_piece(pal, ao, 'Pal_Water', water, 1.26)

    def paper(m):   # giant bath tissue packs, 2 x 2, two high
        for k in range(2):
            z = 0.14 + k * 0.7
            for (a, b) in ((-0.46, -0.01), (0.01, 0.46)):
                for (c0, c1) in ((-0.46, -0.01), (0.01, 0.46)):
                    m.bx(a, b, c0, c1, z, z + 0.68, 'pWhite', cull='b')
            for sy in (-1, 1):
                (fq if sy < 0 else bq)(m, -0.46, 0.46, sy * 0.463, z + 0.38, z + 0.5, 'gA')
            if k == 1:
                uq(m, -0.4, 0.4, -0.4, 0.4, z + 0.683, 'gA')
    pallet_piece(pal, ao, 'Pal_Paper', paper, 1.54)

    def tvs(m):   # boxed TVs standing on edge
        for k, (w, hgt) in enumerate(((0.16, 1.15), (0.14, 0.95), (0.13, 0.8))):
            y0 = -0.46 + k * 0.31
            m.bx(-0.46, 0.46, y0, y0 + w, 0.14, 0.14 + hgt, 'pBlack', cull='b')
            fq(m, -0.4, 0.4, y0 - 0.003, 0.14 + hgt * 0.25, 0.14 + hgt * 0.85, 'gB')
            fq(m, -0.36, 0.1, y0 - 0.006, 0.14 + hgt * 0.32, 0.14 + hgt * 0.42, 'paper')
    pallet_piece(pal, ao, 'Pal_TV', tvs, 1.29)

    def mixed(m):
        load(m, -0.46, 0.46, -0.46, 0.46, 0.14, 0.95, 'gC')
        case(m, -0.4, 0.05, -0.38, 0.1, 0.95, 1.3, 'card', tape='cardD')
        case(m, 0.08, 0.42, -0.2, 0.36, 0.95, 1.15, 'cardL', tape='cardD')
    pallet_piece(pal, ao, 'Pal_Mixed', mixed, 1.3)

    def low(m):
        case(m, -0.44, 0.0, -0.42, 0.4, 0.14, 0.5, 'gA', tape='cardD', label='paper')
        case(m, 0.04, 0.44, -0.3, 0.2, 0.14, 0.42, 'card', tape='cardD')
    pallet_piece(pal, ao, 'Pal_Low', low, 0.5)

    def bags(m):   # sacks of rice / flour: plump slabs in a brick bond, five courses
        for k in range(5):
            z = 0.14 + k * 0.16
            if k % 2 == 0:
                for (a, b) in ((-0.46, -0.01), (0.01, 0.46)):
                    m.bx(a, b, -0.46, 0.46, z, z + 0.155, 'cardL' if k % 4 else 'pWhite', cull='b')
                    fq(m, a + 0.08, b - 0.08, -0.463, z + 0.04, z + 0.11, 'gD')
            else:
                for (c0, c1) in ((-0.46, -0.01), (0.01, 0.46)):
                    m.bx(-0.46, 0.46, c0, c1, z, z + 0.155, 'pWhite' if k % 4 == 1 else 'cardL', cull='b')
                fq(m, -0.3, 0.3, -0.463, z + 0.04, z + 0.11, 'gA')
    pallet_piece(pal, ao, 'Pal_Bags', bags, 0.94)

    m = new(pal)   # a stack of empty pallets
    for k in range(4):
        pallet(m, -0.48, 0.48, -0.48, 0.48, k * 0.142)
    make('Pal_Empty', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.57)])


def build_bales(pal, ao):
    """baled cardboard: compressed layers (striped sides in card colours with flecks of print), wire ties"""
    for name, n in (('Bale_1', 1), ('Bale_2', 2)):
        rnd = random.Random(60 + n)
        m = new(pal)
        for k in range(n):
            z0, z1 = k * 0.8, k * 0.8 + 0.78
            m.bx(-0.46, 0.46, -0.44, 0.44, z0, z1, 'card', cull='b' if k == 0 else '')
            for j in range(6):
                za = z0 + 0.06 + j * 0.12
                c = rnd.choice(['cardD', 'cardL', 'cardD', 'gA', 'gB', 'pWhite'])
                fq(m, -0.46, 0.46, -0.443, za, za + 0.05, c)
                bq(m, -0.46, 0.46, 0.443, za + 0.03, za + 0.07, rnd.choice(['cardD', 'cardL']))
                lq(m, -0.463, -0.44, 0.44, za + 0.02, za + 0.06, rnd.choice(['cardD', 'cardL']))
                rq(m, 0.463, -0.44, 0.44, za, za + 0.05, rnd.choice(['cardD', 'cardL', 'gC']))
            for x in (-0.25, 0.0, 0.25):
                fq(m, x - 0.008, x + 0.008, -0.446, z0, z1, 'steelD')
                uq(m, x - 0.008, x + 0.008, -0.44, 0.44, z1 + 0.003, 'steelD')
        make(name, m, ao, cols=[cb(-0.46, -0.44, 0.0, 0.46, 0.44, n * 0.8)])
    m = new(pal)   # gaylord: a big cardboard bin on a pallet, loose flattened cartons inside
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    m.bx(-0.46, 0.46, -0.46, 0.46, 0.14, 1.05, 'cardD', cull='bt')
    # inner walls seen over the rim (painted faces pointing into the bin), the loose cardboard level inside
    fq(m, -0.44, 0.44, 0.44, 0.8, 1.05, 'card')
    bq(m, -0.44, 0.44, -0.44, 0.8, 1.05, 'cardL')
    rq(m, -0.44, -0.44, 0.44, 0.8, 1.05, 'card')
    lq(m, 0.44, -0.44, 0.44, 0.8, 1.05, 'cardL')
    uq(m, -0.44, 0.44, -0.44, 0.44, 0.8, 'cardD')
    case(m, -0.3, 0.1, -0.2, 0.25, 0.8, 0.98, 'cardL')
    fq(m, -0.3, 0.3, -0.463, 0.5, 0.75, 'paper')
    text_front(m, 'CARDBOARD ONLY', 0.06, -0.466, 0.0, 0.58, 'black', font='cond', maxw=0.55)
    make('Gaylord', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 1.05)])
