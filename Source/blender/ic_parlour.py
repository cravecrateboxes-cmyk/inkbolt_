"""kit-icecream parlour (zone 1): the serving counters (glass-front dipping cabinets with 48 flavours in four sets,
counter ends, the till, the sundae / topping bar, the waffle-cone station, the milkshake bar and its stools), the back
bar against the menu wall (twin soft-serve machines, back counters, the ice cream cake freezer), queue belts, the
giant cone landmark, the seating (booths, bistro tables with heart-back chairs, sofas, the window bar), the kids'
corner (soft-play tower, a low crayon table, bean bags), planters, cone bins, the napkin station, the entrance
vestibule (glass and automatic doors) and the raised terrace (steps and rails). See ic_base.py for conventions."""
import math
import random

from ic_base import *  # noqa: F401,F403
import ic_base as B

# ---------------------------------------------------------------- the four flavour sets (two rows of six per cabinet)
# (front row: named on the glass rail; back row: colour chips on the step, named on a strip on the front) --
# two sets, 24 tubs each
FLAV = {
    'A': [('VANILLA', 'vanilla', None), ('STRAWBERRY', 'strawb', None), ('CHOC FUDGE', 'chocF', None),
          ('MINT CHIP', 'mintF', 'chocD'), ('PISTACHIO', 'pista', None), ('BLUEBERRY', 'blueb', None),
          ('', 'mango', None), ('', 'rasp', None), ('', 'cookie', 'chocD'), ('', 'caramel', 'wafD'), ('', 'grape', None),
          ('', 'bubble', 'cotton')],
    'B': [('COFFEE', 'coffee', None), ('KEY LIME', 'lime', None), ('PEACH', 'peach', None),
          ('COTTON CANDY', 'cotton', 'bubble'), ('LEMON ICE', 'lemon', None), ('CHERRY', 'cherry', None),
          ('', 'chocF', 'wallC'), ('', 'vanilla', 'rasp'), ('', 'mintF', 'chocF'), ('', 'caramel', 'chocD'), ('', 'lilac', None),
          ('', 'strawb', 'lemon')],
}
BACK = {'A': 'MANGO - RASPBERRY - COOKIES - SALT CARAMEL - GRAPE - BUBBLEGUM',
        'B': 'ROCKY ROAD - BERRY SWIRL - CHOC MINT - TOFFEE - LAVENDER - PINK LEMON'}


def glass_q(g, pts):
    """one additive glass face (the glow companion draws it both sides): a faint tint and two sheen streaks"""
    poly(g, pts, 'glassA', (0, -1, 0))
    streaks(g, pts, n=1, off=0.004)


def front_panel(m, x0, x1, y, z0, z1, c, trim='wallC'):
    """a counter front: enamel panel with a scalloped cream trim under the top and a chrome strip above the kick"""
    fq(m, x0, x1, y - 0.003, z1 - 0.1, z1 - 0.02, trim)
    scallops(m, x0, x1, y - 0.004, z1 - 0.1, 0.075, trim)
    fq(m, x0, x1, y - 0.003, z0, z0 + 0.03, 'chrome')


# ================================================================ counters
def build_dip(pal, ao):
    """[2, 2] dipping cabinet: an enamel body (wallP, repainted per copy), a curved glass hood over two rows of six
    tubs (the back row on a step), named tags on the glass rail, colour chips on the step, the back row's names on a
    strip along the front, a steel staff side with sliding doors and a scoop rack"""
    for key, flav in FLAV.items():
        m = new(pal)
        m.bx(-0.98, 0.98, -0.9, 0.55, 0.0, 0.12, 'chocD', cull='b')
        m.bx(-1.0, 1.0, -0.95, 0.55, 0.12, 0.92, 'wallP', cull='b')
        front_panel(m, -1.0, 1.0, -0.95, 0.12, 0.92, 'wallP')
        for k in range(6):
            fdisc(m, -0.75 + k * 0.3, -0.953, 0.66, 0.05, flav[6 + k][1], seg=8)
        fdisc(m, 0.0, -0.953, 0.36, 0.15, 'wallC', seg=8)
        poly(m, [(-0.06, -0.956, 0.38), (0.06, -0.956, 0.38), (0.0, -0.956, 0.25)], 'waf', (0, -1, 0))
        fdisc(m, 0.0, -0.959, 0.43, 0.065, flav[1][1], seg=8)
        for x in (-0.5, 0.5):   # staff side: sliding doors
            bq(m, x - 0.46, x + 0.46, 0.553, 0.2, 0.8, 'steel')
        m.bx(-1.0, 1.0, 0.3, 0.58, 0.92, 0.95, 'chrome', cull='b')
        for k in range(2):
            x = -0.4 + k * 0.8
            m.bm_((x, 0.38, 0.97), (x, 0.52, 0.97), 0.025, 'steelD', hull='none')
        m.bx(-0.98, 0.98, -0.4, 0.3, 0.92, 0.97, 'steel', cull='b')
        for row in range(2):
            y = -0.66 if row == 0 else -0.14
            zt = 0.94 if row == 0 else 0.99
            for k in range(6):
                name, c, mix = flav[row * 6 + k]
                x = -0.825 + k * 0.33
                tub(m, x, y, zt, 0.14, 0.1, c, mix=mix, scooped=(k + row) % 2 == 0)
                if row == 0:   # tag on the glass rail in front of the tub
                    m.bx(x - 0.15, x + 0.15, -0.9, -0.88, 0.92, 0.99, 'white', cull='bk', hull='none')
                    text_front(m, name, 0.032, -0.903, x, 0.945, 'chocD', font='cond', maxw=0.27)
                else:          # a colour chip on the step riser
                    fq(m, x - 0.1, x + 0.1, -0.403, 0.93, 0.962, c)
        # the hood: chrome end plates, chrome bars along the bends (the glass is the glow companion)
        Y = [(-0.95, 0.92), (-0.95, 1.1), (-0.8, 1.27), (-0.6, 1.36), (0.05, 1.38)]
        prof = Y + [(0.05, 0.92)]
        m.prism(prof, -1.0, -0.98, ['chrome'])
        m.prism(prof, 0.98, 1.0, ['chrome'])
        for (y, z) in (Y[1], Y[4]):
            m.bm_((-0.985, y, z), (0.985, y, z), 0.022, 'chrome', hull='none')
        m.bx(-0.98, 0.98, -0.97, -0.9, 0.9, 0.93, 'chrome')
        make('Dip_' + key, m, ao, cols=[cb(-1.0, -0.95, 0.0, 1.0, 0.58, 0.95), cb(-1.0, -0.95, 0.95, 1.0, 0.05, 1.38)])
    g = new(pal)
    for (a, b) in zip(Y[:-1], Y[1:]):
        glass_q(g, [(-0.975, a[0] + 0.004, a[1]), (0.975, a[0] + 0.004, a[1]), (0.975, b[0] + 0.004, b[1]), (-0.975, b[0] + 0.004, b[1])])
    poly(g, [(-0.8, -0.957, 0.96), (-0.68, -0.957, 0.96), (-0.6, -0.957, 1.08), (-0.72, -0.957, 1.08)], 'steelD', (0, -1, 0))
    make_glow('Dip_Glass', g)


def counter_body(m, x0, x1, en, top='woodL', zt=CT, back=0.55):
    """a counter: kick, enamel body to zt - 0.05 with the scalloped front, a wood top overhanging the front"""
    m.bx(x0 + 0.02, x1 - 0.02, -0.9, back, 0.0, 0.12, 'chocD', cull='b')
    m.bx(x0, x1, -0.95, back, 0.12, zt - 0.05, en, cull='b')
    front_panel(m, x0, x1, -0.95, 0.12, zt - 0.05, en)
    m.bx(x0, x1, -1.0, back + 0.03, zt - 0.05, zt, top, cull='b')
    bq(m, x0 + 0.05, x1 - 0.05, back + 0.003, 0.2, zt - 0.15, 'steel')


def build_counter_end(pal, ao):
    """[1, 2] counter end: a rounded enamel end with a cone dispenser tube and a napkin box on top (symmetric)"""
    m = new(pal)
    m.bx(-0.48, 0.48, -0.9, 0.55, 0.0, 0.12, 'chocD', cull='b')
    m.bx(-0.5, 0.5, -0.95, 0.55, 0.12, CT - 0.05, 'pinkD', cull='b')
    front_panel(m, -0.5, 0.5, -0.95, 0.12, CT - 0.05, 'pinkD')
    for x in (-0.503, 0.503):
        (lq if x < 0 else rq)(m, x, -0.95, 0.55, CT - 0.15, CT - 0.07, 'wallC')
        (lq if x < 0 else rq)(m, x, -0.95, 0.55, 0.12, 0.15, 'chrome')
    m.bx(-0.5, 0.5, -1.0, 0.58, CT - 0.05, CT, 'woodL', cull='b')
    # cone dispenser: a clear tube of stacked cones (cones painted on a cream tube) and a napkin box
    m.cy((0.0, -0.2, CT), 0.07, 0.07, 0.55, 'wallC', seg=8)
    for k in range(5):
        m.cy((0.0, -0.2, CT + 0.05 + k * 0.1), 0.075, 0.075, 0.05, 'waf', seg=8, hull='none')
    m.cy((0.0, -0.2, CT + 0.55), 0.09, 0.09, 0.04, 'pinkD', seg=8)
    m.bx(-0.16, 0.16, 0.12, 0.34, CT, CT + 0.14, 'chrome')
    uq(m, -0.1, 0.1, 0.18, 0.28, CT + 0.143, 'white')
    make('Ctr_End', m, ao, cols=[cb(-0.5, -1.0, 0.0, 0.5, 0.58, CT)])


def build_till(pal, ao):
    """[2, 2] the till counter: register screens (staff and customer side), card reader, tip jar, cup tower and an
    ORDER HERE sign on a pole"""
    m, g = new(pal), new(pal)
    counter_body(m, -1.0, 1.0, 'lilac')
    text_front(m, 'ORDER & PAY', 0.14, -0.957, 0.0, 0.5, 'white', maxw=1.2)
    # register: a base, the staff screen tilted toward +Y, a customer screen facing -Y
    m.bx(-0.35, 0.15, 0.0, 0.42, CT, CT + 0.12, 'black')
    m.bm_((-0.1, 0.18, CT + 0.12), (-0.1, 0.2, CT + 0.3), 0.04, 'steelD')
    m.bx(-0.32, 0.12, 0.17, 0.25, CT + 0.28, CT + 0.56, 'black')
    bq(g, -0.29, 0.09, 0.253, CT + 0.31, CT + 0.53, 'screen')
    bq(g, -0.27, -0.05, 0.256, CT + 0.45, CT + 0.51, 'neonB')
    bq(g, -0.02, 0.07, 0.256, CT + 0.33, CT + 0.42, 'exitG')
    m.bx(0.2, 0.42, -0.6, -0.5, CT, CT + 0.22, 'black')
    fq(g, 0.22, 0.4, -0.603, CT + 0.06, CT + 0.2, 'screen')
    text_front(g, '4.95', 0.07, -0.606, 0.31, CT + 0.1, 'lemon', font='cond')
    m.bx(-0.7, -0.5, -0.75, -0.6, CT, CT + 0.04, 'black')
    m.bx(-0.68, -0.52, -0.73, -0.62, CT + 0.04, CT + 0.15, 'steelD')
    # tip jar and a cup tower
    m.cy((0.65, -0.55, CT), 0.08, 0.09, 0.2, 'glass', seg=8)
    m.bx(0.6, 0.7, -0.64, -0.637, CT + 0.06, CT + 0.12, 'white', hull='none', cull='k')
    for k, (c, r) in enumerate((('pinkD', 0.07), ('mintD', 0.06), ('lemon', 0.05))):
        m.cy((0.55 + k * 0.15, 0.2, CT), r * 0.75, r, 0.32 - k * 0.06, c, seg=8)
    # ORDER HERE sign on a pole
    m.cy((-0.85, 0.3, CT), 0.02, 0.02, 1.0, 'chrome', seg=6)
    m.bx(-1.0, -0.58, 0.27, 0.33, CT + 0.95, CT + 1.25, 'cherry')
    text_front(m, 'ORDER', 0.11, 0.267, -0.79, CT + 1.13, 'white', maxw=0.38)
    text_front(m, 'HERE', 0.09, 0.267, -0.79, CT + 1.0, 'lemon', maxw=0.38)
    make('Till', m, ao, cols=[cb(-1.0, -1.0, 0.0, 1.0, 0.58, CT), cb(-0.4, -0.6, CT, 0.45, 0.45, CT + 0.56)])
    make_glow('Till_LED', g)


def topping_bin(m, x, y, c, kind, rnd):
    uq(m, x - 0.11, x + 0.11, y - 0.13, y + 0.13, 0.938, 'steel')
    uq(m, x - 0.095, x + 0.095, y - 0.115, y + 0.115, 0.941, c)
    if kind == 'dots':
        for k in range(6):
            cc = ('cherry', 'lemon', 'sky', 'mintD', 'lilac', 'orange')[(k + int(rnd.random() * 6)) % 6]
            px, py = x - 0.05 + (k % 3) * 0.05, y - 0.04 + (k // 3) * 0.08
            uq(m, px - 0.012, px + 0.012, py - 0.012, py + 0.012, 0.944, cc)


def build_sundae(pal, ao):
    """[3, 2] the sundae bar: twelve topping bins under a glass sneeze guard, three sauce pumps, whipped cream, a jar
    of cherries, bananas, a stack of sundae dishes, the SUNDAE BAR board"""
    m, g = new(pal), new(pal)
    rnd = random.Random(31)
    counter_body(m, -1.5, 1.5, 'mintD', zt=0.97)
    text_front(m, 'SUNDAES', 0.16, -0.957, 0.0, 0.42, 'white', maxw=2.4)
    TOP = [('wallC', 'dots'), ('chocD', 'flat'), ('woodL', 'flat'), ('cotton', 'balls'), ('cardL', 'flat'), ('white', 'balls'),
           ('cherry', 'balls'), ('rasp', 'flat'), ('lemon', 'dots'), ('choc', 'dots'), ('mintF', 'balls'), ('wafL', 'flat')]
    m.bx(-1.4, 1.4, -0.82, -0.18, 0.9, 0.935, 'steelD', cull='b')
    for i, (c, k) in enumerate(TOP):
        topping_bin(m, -1.25 + (i % 6) * 0.5, -0.65 + (i // 6) * 0.3, c, k, rnd)
    # sneeze guard: chrome posts, a sloped glass plane, the board on top
    for x in (-1.42, 0.0, 1.42):
        m.bm_((x, -0.3, 0.95), (x, -0.3, 1.55), 0.03, 'chrome', hull='none')
        m.bm_((x, -0.3, 1.5), (x, -0.85, 1.25), 0.018, 'chrome', hull='none')
    glass_q(g, [(-1.42, -0.3, 1.5), (1.42, -0.3, 1.5), (1.42, -0.85, 1.25), (-1.42, -0.85, 1.25)])
    m.bx(-0.75, 0.75, -0.34, -0.26, 1.55, 1.82, 'pinkD')
    text_front(m, 'SUNDAE BAR', 0.18, -0.343, 0.0, 1.6, 'white', maxw=1.35)
    # the staff half: sauce pumps, whipped cream, cherries, bananas, dishes
    for k, c in enumerate(('chocF', 'caramel', 'strawb')):
        x = -1.2 + k * 0.32
        m.cy((x, 0.15, 0.97), 0.09, 0.09, 0.26, c, seg=8)
        m.cy((x, 0.15, 1.23), 0.03, 0.03, 0.1, 'chrome', seg=6)
        m.bm_((x, 0.15, 1.33), (x, 0.03, 1.33), 0.025, 'chrome', hull='none')
    m.cy((-0.15, 0.2, 0.97), 0.06, 0.06, 0.3, 'chrome', seg=8)
    m.cy((-0.15, 0.2, 1.27), 0.03, 0.01, 0.08, 'white', seg=6)
    m.cy((0.2, 0.2, 0.97), 0.09, 0.08, 0.16, 'glass', seg=8)
    for k in range(4):
        m.bx(0.15 + (k % 2) * 0.06, 0.19 + (k % 2) * 0.06, 0.15 + (k // 2) * 0.06, 0.19 + (k // 2) * 0.06, 1.13, 1.17, 'cherry', hull='none', cull='b')
    for k in range(4):
        a = -0.6 + k * 0.4
        m.bm_((0.55 + math.cos(a) * 0.02, 0.15 + math.sin(a) * 0.12, 0.99 + k * 0.04), (0.75 + math.cos(a) * 0.05, 0.12 + math.sin(a) * 0.18, 1.02 + k * 0.04), 0.04, 'lemon')
    for k in range(2):
        m.cy((1.15, 0.2, 0.97 + k * 0.07), 0.05, 0.12, 0.06, 'glassL', seg=6)
    make('Sundae', m, ao, cols=[cb(-1.5, -1.0, 0.0, 1.5, 0.58, 0.97), cb(-1.45, -0.86, 0.97, 1.45, -0.26, 1.55)])
    make_glow('Sundae_Glass', g)


def cone_iron(m, x, y, open_):
    m.bx(x - 0.17, x + 0.17, y - 0.2, y + 0.18, CT, CT + 0.08, 'black')
    m.cy((x, y, CT + 0.08), 0.14, 0.14, 0.03, 'steelD', seg=8)
    uq(m, x - 0.09, x + 0.09, y - 0.02, y + 0.02, CT + 0.113, 'waf')
    if open_:   # the lid hinged up at the back
        m.cy((x, y + 0.13, CT + 0.24), 0.14, 0.14, 0.03, 'black', seg=8, rot=(80, 0, 0))
    else:
        m.cy((x, y, CT + 0.11), 0.14, 0.13, 0.04, 'black', seg=8)
        m.bm_((x, y - 0.14, CT + 0.13), (x, y - 0.32, CT + 0.14), 0.03, 'chocD')


def build_waffle(pal, ao):
    """[3, 2] the waffle-cone station: three cone irons (two open), a cone roller, a cone tree full of fresh cones,
    a batter jug, the FRESH WAFFLE CONES front"""
    m = new(pal)
    counter_body(m, -1.5, 1.5, 'lemon')
    # a waffle-grid panel on the front, the words over it
    fq(m, -1.2, 1.2, -0.954, 0.2, 0.62, 'waf')
    for k in range(9):
        x = -1.2 + (k + 0.5) * 2.4 / 9
        fq(m, x - 0.012, x + 0.012, -0.957, 0.2, 0.62, 'wafD')
    for k in range(3):
        z = 0.2 + (k + 1) * 0.42 / 4
        fq(m, -1.2, 1.2, -0.96, z - 0.012, z + 0.012, 'wafD')
    m.bx(-1.0, 1.0, -0.98, -0.955, 0.67, 0.84, 'chocD', cull='k')
    text_front(m, 'WAFFLE CONES', 0.11, -0.983, 0.0, 0.71, 'wafL', maxw=1.9)
    for k, x in enumerate((-0.95, 0.55)):
        cone_iron(m, x, 0.18, k == 0)
    m.bx(0.85, 1.3, 0.05, 0.35, CT, CT + 0.03, 'woodL')
    cone(m, 1.07, 0.2, CT + 0.03, CT + 0.26, 0.06, 'steel', seg=8, lip=False)
    # the cone tree (front middle): a rod with two tiers of rings, each holding cones
    m.cy((0.0, -0.45, CT), 0.12, 0.12, 0.03, 'chrome', seg=8)
    m.cy((0.0, -0.45, CT + 0.03), 0.015, 0.015, 0.42, 'chrome', seg=6)
    for t, (z, r, n) in enumerate(((CT + 0.34, 0.15, 5),)):
        m.cy((0.0, -0.45, z), r + 0.03, r + 0.03, 0.015, 'chrome', seg=10, caps=False, hull='none')
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * t) / n
            cone(m, math.cos(a) * r, -0.45 + math.sin(a) * r, z - 0.17, z + 0.03, 0.042, seg=6)
    # batter jug, a stack of finished cones
    m.cy((-1.0, -0.55, CT), 0.08, 0.07, 0.2, 'white', seg=8)
    uq(m, -1.07, -0.93, -0.62, -0.48, CT + 0.203, 'wafL')
    for k in range(3):
        cone(m, -0.55, -0.6, CT + 0.02 + k * 0.035, CT + 0.2 + k * 0.035, 0.045, seg=6)
    make('Waffle', m, ao, cols=[cb(-1.5, -1.0, 0.0, 1.5, 0.58, CT), cb(-0.2, -0.65, CT, 0.2, -0.25, CT + 0.45)])


def spindle(m, x, y):
    m.bx(x - 0.1, x + 0.1, y - 0.06, y + 0.14, CT, CT + 0.05, 'chrome')
    m.bx(x - 0.04, x + 0.04, y + 0.06, y + 0.14, CT + 0.05, CT + 0.5, 'pinkD')
    m.bx(x - 0.07, x + 0.07, y - 0.08, y + 0.15, CT + 0.45, CT + 0.6, 'pinkD')
    m.cy((x, y - 0.02, CT + 0.2), 0.008, 0.008, 0.26, 'chrome', seg=4, hull='none')
    m.cy((x, y - 0.02, CT + 0.05), 0.055, 0.065, 0.22, 'chrome', seg=8)


def build_shakebar(pal, ao):
    """[3, 2] the milkshake bar: a diner bar front (quilted steel, a pink stripe), a wood bar top overhanging the
    stools, three spindle mixers on the back edge, a display shake, a straw jar, steel cups"""
    m = new(pal)
    m.bx(-1.48, 1.48, -0.7, 0.55, 0.0, 0.12, 'chocD', cull='b')
    m.bx(-1.5, 1.5, -0.75, 0.55, 0.12, CT - 0.05, 'chrome', cull='b')
    for k in range(10):
        x = -1.5 + (k + 0.5) * 0.3
        poly(m, [(x - 0.13, -0.753, 0.55), (x, -0.753, 0.7), (x + 0.13, -0.753, 0.55), (x, -0.753, 0.4)], 'steel', (0, -1, 0))
    fq(m, -1.5, 1.5, -0.753, 0.78, 0.9, 'pinkD')
    fq(m, -1.5, 1.5, -0.753, 0.12, 0.16, 'steelD')
    m.bx(-1.5, 1.5, -1.0, 0.58, CT - 0.05, CT, 'woodL', cull='b')
    fq(m, -1.5, 1.5, -1.003, CT - 0.05, CT, 'pinkD')
    m.bx(-1.48, 1.48, -0.78, -0.75, 0.25, 0.3, 'chrome', cull='')   # foot rail
    for x in (-1.0, 0.0, 1.0):
        m.bx(x - 0.02, x + 0.02, -0.78, -0.753, 0.12, 0.25, 'chrome', hull='none', cull='k')
    for x in (-0.8, 0.2):
        spindle(m, x, 0.25)
    # display shake: tall glass with a pink shake, whipped cream, a cherry and a striped straw
    m.cy((1.15, -0.55, CT), 0.04, 0.04, 0.02, 'glassL', seg=8)
    m.cy((1.15, -0.55, CT + 0.02), 0.012, 0.012, 0.08, 'glassL', seg=6, hull='none')
    m.cy((1.15, -0.55, CT + 0.1), 0.045, 0.065, 0.18, 'strawb', seg=8)
    m.sp((1.15, -0.55, CT + 0.3), 0.06, 'white', seg=(6, 3), scale=(1, 1, 0.8))
    m.sp((1.15, -0.55, CT + 0.36), 0.02, 'cherry', seg=(6, 3), hull='none')
    m.bm_((1.17, -0.54, CT + 0.2), (1.22, -0.52, CT + 0.48), 0.012, 'cherry', hull='none')
    # straw jar and steel cups
    m.cy((-1.3, -0.6, CT), 0.06, 0.06, 0.16, 'glass', seg=8)
    for k in range(5):
        a = k * 1.25
        m.bm_((-1.3 + math.cos(a) * 0.02, -0.6 + math.sin(a) * 0.02, CT + 0.05), (-1.3 + math.cos(a) * 0.06, -0.6 + math.sin(a) * 0.06, CT + 0.36),
              0.01, ('cherry', 'sky', 'lemon', 'mintD', 'pinkD')[k], hull='none')
    for k in range(3):
        m.cy((1.25, 0.25 - k * 0.0, CT + k * 0.12), 0.06, 0.075, 0.13, 'chrome', seg=8)
    make('ShakeBar', m, ao, cols=[cb(-1.5, -1.0, 0.0, 1.5, 0.58, CT), cb(-1.15, 0.1, CT, 0.75, 0.45, CT + 0.6)])


def build_stool(pal, ao):
    """[1, 1] diner stool: chrome post on a round base, a foot ring, a seat (repainted per copy)"""
    m = new(pal)
    m.cy((0, 0, 0), 0.22, 0.2, 0.04, 'chrome', seg=8, hull='none')
    m.bx(-0.03, 0.03, -0.03, 0.03, 0.04, 0.7, 'chrome', hull='none', cull='tb')
    m.cy((0, 0, 0.29), 0.16, 0.16, 0.025, 'chrome', seg=8, caps=False, hull='none')
    m.cy((0, 0, 0.7), 0.2, 0.19, 0.1, 'lilac', seg=8)
    make('Stool', m, ao, cols=[cb(-0.2, -0.2, 0.0, 0.2, 0.2, 0.8)])


# ================================================================ the back bar (against the menu wall)
def back_cab(m, en='wallC', door='pinkD', top='woodL'):
    m.bx(-0.98, 0.98, -0.4, 0.45, 0.0, 0.1, 'chocD', cull='b')
    m.bx(-1.0, 1.0, -0.45, 0.45, 0.1, 0.88, en, cull='b')
    for x in (-0.5, 0.5):
        fq(m, x - 0.45, x + 0.45, -0.453, 0.16, 0.82, door)
        m.bx(x - 0.12, x + 0.12, -0.49, -0.453, 0.7, 0.73, 'chrome', cull='k')
    m.bx(-1.0, 1.0, -0.5, 0.45, 0.88, 0.93, top, cull='b')


def build_softserve(pal, ao):
    """[2, 1] twin-twist soft-serve machine on its cabinet (against the wall): three draw handles, the drip tray, a
    hopper lid, a giant soft-serve swirl on top as its sign; cone and cup dispensers beside it"""
    m, g = new(pal), new(pal)
    back_cab(m, 'steel', 'chrome', 'steel')
    m.bx(-0.48, 0.48, -0.38, 0.38, 0.93, 1.78, 'chrome')
    fq(m, -0.44, 0.44, -0.383, 1.35, 1.7, 'steel')
    for k, x in enumerate((-0.22, 0.0, 0.22)):
        m.bx(x - 0.05, x + 0.05, -0.47, -0.38, 1.18, 1.3, 'steelD')
        m.bm_((x, -0.45, 1.3), (x, -0.52, 1.5), 0.025, ('strawb', 'wallC', 'chocF')[k])
        m.cy((x, -0.43, 1.12), 0.025, 0.012, 0.06, 'steelD', seg=6, hull='none')
    m.bx(-0.4, 0.4, -0.5, -0.38, 0.93, 0.98, 'steelD')
    m.bx(-0.38, 0.38, -0.49, -0.39, 0.98, 0.985, 'black', hull='none', cull='b')
    fq(g, -0.12, 0.12, -0.386, 1.5, 1.62, 'screen')
    text_front(g, '-6C', 0.07, -0.389, 0.0, 1.52, 'neonB', font='cond')
    m.bx(-0.46, 0.46, -0.3, 0.3, 1.78, 1.84, 'steel')
    # the swirl sign: a cone with a three-turn twist (vanilla / strawberry) and a tip
    cone(m, 0.0, 0.0, 1.84, 2.25, 0.2, seg=8)
    for k, (r, c) in enumerate(((0.24, 'wallC'), (0.17, 'strawb'))):
        torus(m, 0.0, 0.0, 2.3 + k * 0.14, r - 0.05, 0.08, c, seg=8, sides=5, axis='z')
    m.cy((0.0, 0.0, 2.48), 0.1, 0.0, 0.2, 'wallC', seg=8)
    # cones and cups either side
    for x in (-0.78, 0.78):
        m.cy((x, 0.1, 0.93), 0.08, 0.08, 0.5, 'wallC', seg=8)
        m.cy((x, 0.1, 1.43), 0.1, 0.1, 0.03, 'pinkD', seg=8)
    make('SoftServe', m, ao, cols=[cb(-1.0, -0.5, 0.0, 1.0, 0.45, 0.93), cb(-0.5, -0.5, 0.93, 0.5, 0.38, 1.84)])
    make_glow('SoftServe_LED', g)


def build_backbar(pal, ao):
    """[2, 1] back counters: A cups and lids, a blender; B a sink with a dipper well and scoop rack; C a toppings fridge
    with a hot-fudge warmer, a whipped-cream dispenser, a fruit bowl"""
    # A
    m = new(pal); back_cab(m)
    for k, (c, r, h) in enumerate((('pinkD', 0.06, 0.42), ('mintD', 0.075, 0.34), ('sky', 0.1, 0.24))):
        m.cy((-0.8 + k * 0.24, 0.15, 0.93), r * 0.75, r, h, c, seg=6, hull='none')
    for k in range(3):
        m.cy((0.05 + k * 0.16, 0.2, 0.93), 0.07, 0.07, 0.12 + k * 0.04, 'white', seg=6, hull='none')
    m.bx(0.58, 0.82, 0.0, 0.3, 0.93, 1.05, 'black')
    m.cy((0.7, 0.15, 1.05), 0.08, 0.1, 0.26, 'glass', seg=8)
    m.cy((0.7, 0.15, 1.31), 0.1, 0.1, 0.03, 'black', seg=8)
    make('BackBar_A', m, ao, cols=[cb(-1.0, -0.5, 0.0, 1.0, 0.45, 0.93)])
    # B
    m = new(pal); back_cab(m, door='mintD')
    m.bx(-0.75, -0.05, -0.35, 0.3, 0.9, 0.935, 'chrome', cull='b')
    uq(m, -0.7, -0.1, -0.3, 0.25, 0.938, 'steelD')
    m.bm_((-0.4, 0.35, 0.93), (-0.4, 0.35, 1.25), 0.03, 'chrome')
    m.bm_((-0.4, 0.35, 1.25), (-0.4, 0.05, 1.25), 0.02, 'chrome')
    m.cy((0.35, 0.05, 0.93), 0.13, 0.13, 0.1, 'steel', seg=8)
    uq(m, 0.25, 0.45, -0.05, 0.15, 1.033, 'sky')
    for k in range(4):
        m.bm_((0.65 + k * 0.08, 0.25, 0.94), (0.65 + k * 0.08, 0.25, 1.1), 0.018, 'steelD', hull='none')
        m.sp((0.65 + k * 0.08, 0.25, 1.12), 0.03, 'chrome', seg=(6, 3), hull='none')
    m.bx(0.6, 0.95, -0.4, -0.2, 0.935, 0.95, 'white', hull='none')
    make('BackBar_B', m, ao, cols=[cb(-1.0, -0.5, 0.0, 1.0, 0.45, 0.93)])
    # C
    m = new(pal); back_cab(m, en='steel', door='chrome')
    for x in (-0.5, 0.5):
        fq(m, x - 0.3, x + 0.3, -0.456, 0.65, 0.7, 'sky')
    m.bx(-0.85, -0.45, -0.1, 0.3, 0.93, 1.13, 'steel')
    m.cy((-0.65, 0.1, 1.13), 0.12, 0.12, 0.02, 'chrome', seg=8)
    uq(m, -0.75, -0.55, 0.0, 0.2, 1.153, 'chocD')
    m.bx(-0.2, 0.1, 0.0, 0.32, 0.93, 1.45, 'chrome')
    m.bm_((-0.05, -0.02, 1.15), (-0.05, -0.12, 1.1), 0.03, 'steelD')
    m.cy((0.6, 0.1, 0.93), 0.18, 0.12, 0.1, 'wallC', seg=10)
    for k in range(3):
        a = k * 0.9
        m.bm_((0.5 + math.cos(a) * 0.05, 0.06 + math.sin(a) * 0.05, 1.05 + k * 0.035), (0.68 + math.cos(a) * 0.05, 0.14 + math.sin(a) * 0.05, 1.08 + k * 0.035), 0.04, 'lemon')
    make('BackBar_C', m, ao, cols=[cb(-1.0, -0.5, 0.0, 1.0, 0.45, 0.93), cb(-0.85, -0.12, 0.93, 0.1, 0.32, 1.45)])


def build_cakefreezer(pal, ao):
    """[2, 1] upright ice cream cake freezer (against the wall): two glass doors (glow companion), a lit back, four
    shelves of round cakes in frosting colours, the ICE CREAM CAKES header"""
    m, g = new(pal), new(pal)
    m.bx(-0.98, 0.98, -0.42, 0.45, 0.0, 2.15, 'white', cull='b')
    fq(m, -0.98, 0.98, -0.423, 0.0, 0.15, 'chocD')
    fq(m, -0.98, 0.98, -0.423, 1.92, 2.12, 'pinkD')
    text_front(m, 'ICE CREAM CAKES', 0.13, -0.426, 0.0, 1.96, 'white', maxw=1.7)
    for x in (-0.47, 0.47):
        m.bx(x - 0.45, x + 0.45, -0.46, -0.423, 0.18, 1.88, 'chrome', cull='k')
        m.bx((x - 0.38) if x > 0 else (x + 0.34), (x - 0.34) if x > 0 else (x + 0.38), -0.52, -0.46, 0.7, 1.4, 'chrome')
    rnd = random.Random(9)
    for s in range(3):
        z = 0.4 + s * 0.5
        m.bx(-0.9, 0.9, -0.35, 0.35, z - 0.02, z, 'chrome', hull='none', cull='')
        for k in range(3):
            x = -0.6 + k * 0.6
            c = rnd.choice(['strawb', 'chocF', 'wallC', 'mintF', 'cotton', 'lemon'])
            m.cy((x, -0.05, z), 0.2, 0.2, 0.18, c, seg=8, hull='none')
            m.cy((x, -0.05, z + 0.18), 0.17, 0.12, 0.05, 'white', seg=8, hull='none')
            m.bx(x - 0.03, x + 0.03, -0.08, -0.02, z + 0.23, z + 0.27, 'cherry', hull='none', cull='b')
    poly(g, [(-0.92, -0.462, 0.23), (-0.02, -0.462, 0.23), (-0.02, -0.462, 1.83), (-0.92, -0.462, 1.83)], 'glassA', (0, -1, 0))
    poly(g, [(0.02, -0.462, 0.23), (0.92, -0.462, 0.23), (0.92, -0.462, 1.83), (0.02, -0.462, 1.83)], 'glassA', (0, -1, 0))
    for x0 in (-0.92, 0.02):
        streaks(g, [(x0, -0.465, 0.23), (x0 + 0.9, -0.465, 0.23), (x0 + 0.9, -0.465, 1.83), (x0, -0.465, 1.83)], n=1, w=0.1)
    make('CakeFreezer', m, ao, cols=[cb(-0.98, -0.52, 0.0, 0.98, 0.45, 2.15)])
    make_glow('CakeFreezer_Glass', g)


def build_belts(pal, ao):
    """queue belts (links, modelled along Blender Y): chrome posts on round bases, a pink retractable belt"""
    def post(m):
        m.cy((0, 0, 0), 0.15, 0.15, 0.03, 'chrome', seg=8, hull='none')
        m.bx(-0.025, 0.025, -0.025, 0.025, 0.03, 0.93, 'chrome', hull='none', cull='b')
        m.cy((0, 0, 0.93), 0.04, 0.04, 0.05, 'pinkD', seg=6)
    m = new(pal); post(m)
    m.bx(-0.006, 0.006, -0.5, 0.5, 0.82, 0.88, 'pinkD', hull='none', cull='kf')
    make('BeltFull', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.5, 0.95)])
    m = new(pal)
    m.bx(-0.006, 0.006, -0.5, -0.03, 0.82, 0.88, 'pinkD', hull='none', cull='f')
    make('BeltHalf', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.0, 0.95)])
    m = new(pal); post(m)
    make('BeltPost', m, ao)


# ================================================================ landmark: the giant cone
def build_landmark(pal, ao):
    """[6, 6] the giant cone: a round plinth ringed by a cushioned bench, a fluted pedestal, a 2.6 m waffle cone with
    a painted criss-cross, a strawberry scoop with a chocolate drip, a mint scoop with sprinkles, a cherry; the
    SCOOPS & CREAM band round the pedestal (glow)"""
    m, g = new(pal), new(pal)
    m.cy((0, 0, 0), 2.7, 2.7, 0.12, 'chocD', seg=16, hull='none')
    m.cy((0, 0, 0.12), 2.6, 2.6, 0.3, 'wallP', seg=16)
    m.cy((0, 0, 0.42), 2.66, 2.66, 0.1, 'pinkD', seg=16)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        fdisc_x = 2.603
        x, y = math.cos(a) * fdisc_x, math.sin(a) * fdisc_x
        nrm = (math.cos(a), math.sin(a), 0)
        pts = []
        for i in range(10):
            t = 2 * math.pi * i / 10
            u, v = math.cos(t) * 0.09, math.sin(t) * 0.09
            pts.append((x - math.sin(a) * u, y + math.cos(a) * u, 0.27 + v))
        poly(m, pts, 'wallC', nrm)
    # the inner raised ring and the pedestal
    m.cy((0, 0, 0.52), 1.5, 1.4, 0.3, 'wallC', seg=20)
    m.cy((0, 0, 0.82), 1.45, 1.45, 0.04, 'waf', seg=20, hull='none')
    pillar(m, 0, 0, 0.82, 1.55, 0.55, ['wallM', 'mintD'], seg=16)
    m.cy((0, 0, 1.55), 0.65, 0.65, 0.12, 'waf', seg=12)
    # the band of lettering round the pedestal (four sides, glowing pink)
    for k in range(2):
        a = k * math.pi
        g.parent = Matrix.Rotation(a, 4, 'Z')
        ib_text.draw(g, 'SCOOPS', 0.0, -0.585, 1.06, 0.22, 'neonP', face='y-', font='display', maxw=0.6)
    g.parent = Matrix.Identity(4)
    # the cone
    m.cy((0, 0, 1.4), 0.0, 1.25, 2.6, 'waf', seg=12)
    for k in range(4):   # criss-cross lines on the cone (spirals both ways, painted strips)
        for sgn in (-1, 1):
            pts = []
            for i in range(4):
                t = i / 3
                z = 1.6 + t * 2.3
                r = (z - 1.4) / 2.6 * 1.25 + 0.006
                a = 2 * math.pi * k / 4 + sgn * t * 1.4
                pts.append((math.cos(a) * r, math.sin(a) * r, z))
            for i in range(3):
                a0, a1 = pts[i], pts[i + 1]
                m.bm_(a0, a1, 0.035, 'wafD', hull='none')
    m.cy((0, 0, 3.96), 1.32, 1.32, 0.14, 'wafL', seg=12)
    # scoops: strawberry with a chocolate drip, mint with sprinkles, a cherry
    m.sp((0, 0, 4.55), 1.25, 'strawb', seg=(12, 7), scale=(1, 1, 0.68))
    m.cy((0, 0, 4.12), 1.33, 1.28, 0.14, 'strawb', seg=12)
    torus(m, 0, 0, 4.86, 1.0, 0.13, 'chocF', seg=12, sides=5, axis='z')
    for k in range(7):
        a = 2 * math.pi * (k + 0.2) / 7
        r = 1.06
        L = 0.25 + 0.2 * ((k * 5) % 3)
        m.cy((math.cos(a) * r, math.sin(a) * r, 4.86 - L), 0.07, 0.1, L, 'chocF', seg=6, hull='none')
    m.sp((0, 0, 5.55), 0.95, 'mintF', seg=(12, 6), scale=(1, 1, 0.7))
    m.cy((0, 0, 5.12), 0.98, 0.95, 0.12, 'mintF', seg=12)
    rnd = random.Random(4)
    for k in range(14):
        a, b = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.15, 1.2)
        r = 0.95 * math.cos(b) + 0.01
        x, y, z = math.cos(a) * r, math.sin(a) * r, 5.55 + 0.7 * 0.95 * math.sin(b)
        c = ('cherry', 'lemon', 'sky', 'chocD', 'lilac', 'white')[k % 6]
        m.bm_((x, y, z), (x + 0.07 * math.cos(a + 1.4), y + 0.07 * math.sin(a + 1.4), z + 0.02), 0.035, c, hull='none')
    m.sp((0, 0, 6.38), 0.24, 'cherry', seg=(8, 5))
    m.bm_((0, 0, 6.58), (0.12, 0.05, 6.8), 0.03, 'leaf', hull='none')
    # collision inscribed in the round shapes (plinth, ring, pedestal, cone, scoops)
    make('Landmark_Cone', m, ao, cols=[
        cb(-2.5, -1.0, 0.0, 2.5, 1.0, 0.52), cb(-1.0, -2.5, 0.0, 1.0, 2.5, 0.52), cb(-1.8, -1.8, 0.0, 1.8, 1.8, 0.52),
        cb(-1.02, -1.02, 0.52, 1.02, 1.02, 0.82), cb(-0.4, -0.4, 0.82, 0.4, 0.4, 2.5), cb(-0.62, -0.62, 2.5, 0.62, 0.62, 3.3),
        cb(-0.85, -0.85, 3.3, 0.85, 0.85, 5.1), cb(-0.62, -0.62, 5.1, 0.62, 0.62, 6.0)])
    make_glow('Landmark_Cone_LED', g)


# ================================================================ seating
def build_booth(pal, ao):
    """[2, 3] diner booth: two high-backed benches facing across a laminate table (end to the wall), a napkin box and
    a sundae on the table; upholstery repainted per copy"""
    m = new(pal)
    for s in (-1, 1):
        y0, y1 = sorted((s * 1.45, s * 0.95))
        m.bx(-0.98, 0.98, y0 + 0.05, y1 - 0.05, 0.0, 0.4, 'chocD', cull='b')
        cushion(m, -0.98, 0.98, y0, y1, 0.4, 0.5, 'pinkD', 'wallP')
        b0, b1 = sorted((s * 1.48, s * 1.3))
        cushion(m, -0.98, 0.98, b0, b1, 0.5, 1.2, 'pinkD', 'wallP')
        m.bx(-1.0, 1.0, b0 - 0.0, b1, 1.2, 1.26, 'wafD', cull='b')
        for k in range(0):   # (no tufted channels)
            x = -0.75 + k * 0.5
            (fq if s > 0 else bq)(m, x - 0.015, x + 0.015, s * 1.3 - s * 0.003 if s > 0 else -1.3 + 0.003, 0.56, 1.14, 'wallP')
    m.bx(-0.9, 0.9, -0.4, 0.4, 0.71, 0.75, 'wallC')
    fq(m, -0.9, 0.9, -0.403, 0.71, 0.75, 'chrome')
    bq(m, -0.9, 0.9, 0.403, 0.71, 0.75, 'chrome')
    m.cy((0.0, 0.0, 0.0), 0.2, 0.2, 0.03, 'chrome', seg=8)
    m.cy((0.0, 0.0, 0.03), 0.04, 0.04, 0.68, 'chrome', seg=8)
    m.bx(-0.85, -0.68, -0.07, 0.07, 0.75, 0.88, 'chrome')
    uq(m, -0.83, -0.7, -0.05, 0.05, 0.883, 'white')
    m.cy((0.25, -0.1, 0.75), 0.08, 0.05, 0.12, 'glassL', seg=6, hull='none')
    m.sp((0.25, -0.1, 0.89), 0.07, 'strawb', seg=(6, 2), hull='none')
    make('Booth', m, ao, cols=[cb(-1.0, -1.48, 0.0, 1.0, -0.95, 0.5), cb(-1.0, -1.48, 0.5, 1.0, -1.3, 1.26),
                               cb(-1.0, 0.95, 0.0, 1.0, 1.48, 0.5), cb(-1.0, 1.3, 0.5, 1.0, 1.48, 1.26), cb(-0.9, -0.4, 0.0, 0.9, 0.4, 0.75)])


def heart_chair(m, x, y, yaw):
    """a bistro chair with a wire heart back, facing yaw (radians; 0 = facing -Y)"""
    old = m.parent
    m.parent = old @ Matrix.Translation((x, y, 0)) @ Matrix.Rotation(yaw, 4, 'Z')
    for (lx, ly) in ((-0.14, -0.14), (0.14, -0.14), (-0.14, 0.14), (0.14, 0.14)):
        m.bx(lx - 0.012, lx + 0.012, ly - 0.012, ly + 0.012, 0.0, 0.44, 'chrome', hull='none', cull='bt')
    m.cy((0, 0, 0.44), 0.19, 0.18, 0.07, 'lilac', seg=6)

    def hp(i, k):
        t = math.pi * 2 * i / 8
        hx = 16 * math.sin(t) ** 3
        hz = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        return hx * 0.011 * k, 0.8 + (hz + 4) * 0.011 * k - 0.044
    pts = [hp(i, 1.0) for i in range(8)]
    for (yy, nrm) in ((0.172, (0, -1, 0)), (0.188, (0, 1, 0))):
        poly(m, [(a, yy, b) for (a, b) in pts], 'chrome', nrm)
        poly(m, [(a * 0.7, yy + 0.003 * nrm[1], 0.8 + (b - 0.8) * 0.7) for (a, b) in pts], 'lilac', nrm)
    m.bx(-0.012, 0.012, 0.168, 0.192, 0.51, 0.62, 'chrome', hull='none', cull='tb')
    m.parent = old


def build_tables(pal, ao):
    """[2, 2] bistro sets: Table4 (a round marble-top pedestal table, four heart-back chairs), Table2 (a square table,
    two chairs, a banana split); chair seats repainted per copy"""
    m = new(pal)
    m.cy((0, 0, 0), 0.26, 0.24, 0.04, 'chrome', seg=8, hull='none')
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.04, 0.72, 'chrome', hull='none', cull='tb')
    m.cy((0, 0, 0.72), 0.45, 0.45, 0.04, 'wallC', seg=10)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        heart_chair(m, math.cos(a) * 0.68, math.sin(a) * 0.68, a - math.pi / 2 + math.pi)
    m.cy((0.1, 0.05, 0.76), 0.04, 0.05, 0.12, 'pinkD', seg=6, hull='none')
    m.sp((0.1, 0.05, 0.9), 0.05, 'mintF', seg=(6, 2), hull='none')
    make('Table4', m, ao, cols=[cb(-0.45, -0.45, 0.0, 0.45, 0.45, 0.76)] +
         [cb(math.cos(k * math.pi / 2 + math.pi / 4) * 0.68 - 0.2, math.sin(k * math.pi / 2 + math.pi / 4) * 0.68 - 0.2, 0.0,
             math.cos(k * math.pi / 2 + math.pi / 4) * 0.68 + 0.2, math.sin(k * math.pi / 2 + math.pi / 4) * 0.68 + 0.2, 0.52) for k in range(4)])
    m = new(pal)
    for (lx, ly) in ((-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)):
        m.bx(lx - 0.022, lx + 0.022, ly - 0.022, ly + 0.022, 0.0, 0.72, 'chrome', hull='none', cull='bt')
    m.bx(-0.36, 0.36, -0.36, 0.36, 0.72, 0.76, 'wallM')
    fq(m, -0.36, 0.36, -0.363, 0.72, 0.76, 'mintD')
    bq(m, -0.36, 0.36, 0.363, 0.72, 0.76, 'mintD')
    for s in (-1, 1):
        heart_chair(m, 0.0, s * 0.68, 0.0 if s > 0 else math.pi)
    # a banana split boat
    m.bx(-0.18, 0.18, -0.07, 0.07, 0.76, 0.8, 'glassL')
    for k, c in enumerate(('chocF', 'vanilla', 'strawb')):
        m.sp((-0.1 + k * 0.1, 0.0, 0.84), 0.05, c, seg=(6, 2), hull='none')
    for s in (-1, 1):
        m.bm_((-0.16, s * 0.05, 0.81), (0.16, s * 0.05, 0.81), 0.03, 'lemon', hull='none')
    make('Table2', m, ao, cols=[cb(-0.36, -0.36, 0.0, 0.36, 0.36, 0.76), cb(-0.2, -0.88, 0.0, 0.2, -0.48, 0.52), cb(-0.2, 0.48, 0.0, 0.2, 0.88, 0.52)])


def build_sofa(pal, ao):
    """[3, 1] a pastel lounge sofa (against a wall or a rail): rolled arms, three seat cushions, a scoop cushion"""
    m = new(pal)
    m.bx(-1.45, 1.45, -0.42, 0.42, 0.0, 0.12, 'chocD', cull='b')
    cushion(m, -1.25, 1.25, -0.05, 0.4, 0.12, 0.95, 'mintD', 'wallM')
    for k in range(3):
        x = -0.83 + k * 0.83
        cushion(m, x - 0.4, x + 0.4, -0.42, -0.05, 0.12, 0.45, 'mintD', 'wallM')
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.45, s * 1.25))
        m.bx(x0, x1, -0.45, 0.44, 0.12, 0.62, 'mintD', cull='b')
        cyl_y(m, (x0 + x1) / 2, -0.47, 0.43, 0.62, 0.12, 'mintD', seg=8)
    m.sp((-0.8, -0.05, 0.62), 0.16, 'strawb', seg=(6, 4), scale=(1, 0.6, 1))
    make('Sofa', m, ao, cols=[cb(-1.45, -0.47, 0.0, 1.45, 0.42, 0.45), cb(-1.45, -0.05, 0.45, 1.45, 0.42, 0.95)])


def build_windowbar(pal, ao):
    """[2, 1] window bar (against the shop window): a narrow ledge counter on brackets, two tall stools, a napkin box"""
    m = new(pal)
    m.bx(-1.0, 1.0, 0.0, 0.42, CT - 0.05, CT, 'woodL')
    fq(m, -1.0, 1.0, -0.003, CT - 0.05, CT, 'pinkD')
    for x in (-0.8, 0.8):
        m.bx(x - 0.03, x + 0.03, 0.3, 0.36, 0.0, CT - 0.05, 'chrome', cull='b')
        m.bm_((x, 0.33, 0.6), (x, 0.08, CT - 0.06), 0.03, 'chrome', hull='none')
    for x in (-0.5, 0.5):
        m.cy((x, -0.3, 0), 0.2, 0.18, 0.04, 'chrome', seg=8, hull='none')
        m.bx(x - 0.03, x + 0.03, -0.33, -0.27, 0.04, 0.74, 'chrome', hull='none', cull='tb')
        m.cy((x, -0.3, 0.74), 0.19, 0.18, 0.08, 'lilac', seg=8)
    m.bx(-0.08, 0.08, 0.15, 0.3, CT, CT + 0.12, 'chrome')
    make('WindowBar', m, ao, cols=[cb(-1.0, 0.0, 0.0, 1.0, 0.42, CT), cb(-0.7, -0.5, 0.0, -0.3, -0.1, 0.8), cb(0.3, -0.5, 0.0, 0.7, -0.1, 0.8)])


# ================================================================ kids' corner, small props
def build_kids(pal, ao):
    """[4, 4] soft-play tower: padded floor mats, foam blocks, a little tower on posts with a scoop-shaped roof, a net
    side, a slide down to the mats; [2, 2] a low crayon table with cube stools; [1, 1] bean bags"""
    m = new(pal)
    for i, c in enumerate(('cherry', 'sky', 'lemon', 'mintD')):
        x0, y0 = -1.95 + (i % 2) * 1.95, -1.95 + (i // 2) * 1.95
        m.bx(x0, x0 + 1.95, y0, y0 + 1.95, 0.0, 0.08, c, cull='b')
    # the tower (north-west quarter): four posts, a padded deck at 1.0, a scoop roof, a net and a slide
    for (x, y) in ((-1.8, 0.2), (-0.2, 0.2), (-1.8, 1.8), (-0.2, 1.8)):
        m.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.08, 2.3, 'pinkD', cull='b')
    m.bx(-1.86, -0.14, 0.14, 1.86, 0.9, 1.05, 'lemon')
    m.cy((-1.0, 1.0, 2.3), 1.0, 1.0, 0.08, 'waf', seg=10)
    m.sp((-1.0, 1.0, 2.38), 0.92, 'strawb', seg=(10, 5), scale=(1, 1, 0.55))
    m.sp((-1.0, 1.0, 2.9), 0.14, 'cherry', seg=(6, 3))
    for side, (a, b) in enumerate((((-1.8, 0.2), (-0.2, 0.2)), ((-1.8, 1.8), (-1.8, 0.2)))):
        for k in range(3):
            z = 1.2 + k * 0.28 + side * 0.06
            m.bm_((a[0], a[1], z), (b[0], b[1], z), 0.03, 'sky', hull='none')
        for k in range(3):
            t = (k + 0.5) / 3
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            m.bm_((x, y, 1.05), (x, y, 1.85), 0.022, 'sky', hull='none')
    m.prism([(0.3, 1.0), (0.3, 1.1), (1.95, 0.2), (1.95, 0.1)], -0.9, -0.3, ['mintD'])
    for x in (-0.92, -0.28):
        m.prism([(0.3, 1.1), (0.3, 1.25), (1.95, 0.35), (1.95, 0.2)], x - 0.04, x + 0.04, ['mintD'])
    # foam blocks (south half)
    for (x, y, s, c) in ((0.6, -1.2, 0.5, 'lemon'), (1.4, -1.35, 0.4, 'cherry'), (0.9, -0.5, 0.35, 'sky'), (1.55, -0.6, 0.45, 'lilac')):
        m.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, 0.08, 0.08 + s, c, cull='b')
    m.cy((0.6, -1.2, 0.58), 0.16, 0.16, 0.12, 'orange', seg=8)
    cone(m, -1.0, -1.0, 0.08, 0.7, 0.28, seg=8)
    m.sp((-1.0, -1.0, 0.82), 0.3, 'cotton', seg=(8, 4), scale=(1, 1, 0.8))
    make('Play', m, ao, cols=[cb(-1.88, 0.12, 0.0, -0.12, 1.88, 1.05), cb(-1.88, 0.12, 1.05, -0.12, 0.2, 1.9), cb(-1.88, 0.12, 1.05, -1.8, 1.88, 1.9),
                              cb(-1.88, 0.12, 1.9, -0.12, 1.88, 2.9), cb(-0.9, 0.3, 0.0, -0.3, 1.95, 0.6),
                              cb(0.35, -1.55, 0.0, 1.78, -0.33, 0.7), cb(-1.3, -1.3, 0.0, -0.7, -0.7, 1.1)])
    m = new(pal)
    m.bx(-0.65, 0.65, -0.45, 0.45, 0.42, 0.48, 'sky')
    for (x, y) in ((-0.58, -0.38), (0.58, -0.38), (-0.58, 0.38), (0.58, 0.38)):
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.42, 'lemon', cull='b')
    uq(m, -0.4, -0.05, -0.25, 0.1, 0.483, 'white')
    uq(m, 0.1, 0.45, -0.1, 0.25, 0.483, 'white')
    for k, c in enumerate(('cherry', 'mintD', 'lilac', 'orange')):
        m.bm_((-0.2 + k * 0.08, 0.25, 0.495), (-0.1 + k * 0.08, 0.3, 0.495), 0.02, c, hull='none')
    for (x, y, c) in ((-0.95, 0.0, 'cherry'), (0.95, 0.0, 'mintD'), (0.0, -0.75, 'lemon'), (0.0, 0.75, 'lilac')):
        m.bx(x - 0.17, x + 0.17, y - 0.17, y + 0.17, 0.0, 0.3, c, cull='b')
    make('KidTable', m, ao, cols=[cb(-0.65, -0.45, 0.0, 0.65, 0.45, 0.48)])
    m = new(pal)
    m.sp((0.0, 0.0, 0.2), 0.38, 'lilac', seg=(8, 4), scale=(1, 0.9, 0.62))
    m.sp((0.05, 0.12, 0.42), 0.22, 'lilac', seg=(6, 3), scale=(1, 0.8, 0.7))
    make('BeanBag', m, ao, cols=[cb(-0.36, -0.34, 0.0, 0.36, 0.34, 0.45)])


def build_cart(pal, ao):
    """[2, 1] a vintage ice cream pushcart (along X): a striped cooler box with two lids, big spoked wheels at the
    east end, a push handle at the west end, a striped umbrella on a pole, a SCOOPS board"""
    m = new(pal)
    m.bx(-0.75, 0.6, -0.36, 0.36, 0.35, 1.0, 'wallC', cull='b')
    stripes_front(m, -0.75, 0.6, -0.363, 0.42, 0.9, ['wallC', 'pinkD'], 9)
    bq(m, -0.75, 0.6, 0.363, 0.56, 0.76, 'pinkD')
    m.bx(-0.78, 0.63, -0.39, 0.39, 1.0, 1.06, 'chrome')
    for x in (-0.38, 0.22):
        m.cy((x, 0.0, 1.06), 0.17, 0.17, 0.04, 'chrome', seg=8)
        m.cy((x, 0.0, 1.1), 0.05, 0.05, 0.04, 'black', seg=6, hull='none')
    m.bx(-0.3, 0.3, -0.42, -0.363, 0.56, 0.78, 'cherry', cull='k')
    text_front(m, 'SCOOPS', 0.12, -0.423, 0.0, 0.61, 'white', maxw=0.5)
    for y in (-0.42, 0.42):   # wheels (east end) and a stand leg (west end)
        cyl_y(m, 0.62, y - 0.04 if y > 0 else y, y + 0.04 if y < 0 else y, 0.36, 0.34, 'chocD', seg=8)
        cyl_y(m, 0.62, y - 0.045 if y > 0 else y - 0.005, y + 0.045 if y < 0 else y + 0.005, 0.36, 0.08, 'chrome', seg=6)
    m.bx(-0.72, -0.66, -0.3, 0.3, 0.0, 0.35, 'chrome', cull='b')
    m.bm_((-0.75, 0.0, 0.95), (-0.98, 0.0, 1.15), 0.04, 'chrome', hull='none')
    m.bm_((-0.98, -0.3, 1.15), (-0.98, 0.3, 1.15), 0.045, 'chocD')
    m.cy((0.0, 0.0, 1.06), 0.022, 0.022, 1.3, 'chrome', seg=6)
    m.fan((0.0, 0.0, 2.15), 2.5, 0.85, 8, ['pinkD', 'wallC'])
    m.sp((0.0, 0.0, 2.5), 0.05, 'cherry', seg=(6, 3), hull='none')
    make('Cart', m, ao, cols=[cb(-0.78, -0.39, 0.0, 0.63, 0.39, 1.1), cb(0.58, -0.47, 0.0, 0.66, 0.47, 0.7)])


def build_planterbox(pal, ao):
    """[3, 1] a planter-box divider between table groups (along X): a pink-striped wooden trough, a clipped hedge with
    little flowers, low cover"""
    m = new(pal)
    m.bx(-1.45, 1.45, -0.32, 0.32, 0.0, 0.62, 'wallC', cull='b')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -1.45, 1.45, s * 0.323, 0.0, 0.1, 'wafD')
        (fq if s < 0 else bq)(m, -1.45, 1.45, s * 0.323, 0.42, 0.52, 'pinkD')
    for x in (-1.453, 1.453):
        (lq if x < 0 else rq)(m, x, -0.32, 0.32, 0.42, 0.52, 'pinkD')
    m.bx(-1.4, 1.4, -0.27, 0.27, 0.62, 1.12, 'leaf', cull='b')
    for k in range(7):
        x = -1.2 + k * 0.4
        c = ('cherry', 'lemon', 'white')[k % 3]
        uq(m, x - 0.04, x + 0.04, -0.12 + (k % 2) * 0.14, -0.04 + (k % 2) * 0.14, 1.123, c)
        fq(m, x + 0.08, x + 0.15, -0.273, 0.8 + (k % 3) * 0.09, 0.87 + (k % 3) * 0.09, c)
    make('PlanterBox', m, ao, cols=[cb(-1.45, -0.32, 0.0, 1.45, 0.32, 1.12)])


def build_small(pal, ao):
    """[1, 1] a topiary planter, a cone-shaped bin, the napkin / spoon station"""
    m = new(pal)
    m.cy((0, 0, 0), 0.3, 0.36, 0.6, 'pinkD', seg=8)
    m.cy((0, 0, 0.6), 0.38, 0.38, 0.06, 'wallC', seg=8, hull='none')
    disc(m, 0, 0, 0.664, 0.33, 'chocD', seg=8)
    m.bx(-0.03, 0.03, -0.03, 0.03, 0.66, 1.1, 'wood', hull='none', cull='tb')
    m.sp((0, 0, 1.45), 0.4, 'leaf', seg=(7, 4))
    for k in range(3):
        a = k * 2.1
        m.sp((math.cos(a) * 0.34, math.sin(a) * 0.34, 1.45 + (k % 2) * 0.15), 0.06, 'cherry' if k % 2 else 'white', seg=(6, 3), hull='none')
    make('Planter', m, ao, cols=[cb(-0.38, -0.38, 0.0, 0.38, 0.38, 1.85)])
    m = new(pal)   # bin: a big waffle cone with a vanilla-scoop lid and a THANK YOU flap
    m.cy((0, 0, 0), 0.2, 0.32, 0.95, 'waf', seg=10)
    for k in range(3):
        z = 0.2 + k * 0.28
        r = 0.2 + 0.12 * z / 0.95 + 0.004
        m.cy((0, 0, z), r, r, 0.02, 'wafD', seg=10, caps=False, hull='none')
    m.sp((0, 0, 0.95), 0.34, 'vanilla', seg=(8, 4), scale=(1, 1, 0.6))
    m.bx(-0.13, 0.13, -0.33, -0.3, 0.92, 1.06, 'chocD')
    text_front(m, 'THANK YOU', 0.04, -0.333, 0.0, 0.97, 'white', maxw=0.22)
    make('Bin', m, ao, cols=[cb(-0.32, -0.32, 0.0, 0.32, 0.32, 1.15)])
    m = new(pal)   # napkin / spoon station
    m.bx(-0.4, 0.4, -0.3, 0.3, 0.0, 0.08, 'chocD', cull='b')
    m.bx(-0.4, 0.4, -0.3, 0.3, 0.08, 0.95, 'wallC', cull='b')
    for s in (-1, 1):
        (fq if s < 0 else bq)(m, -0.36, 0.36, s * 0.303, 0.15, 0.85, 'mintD')
        (fq if s < 0 else bq)(m, -0.36, 0.36, s * 0.306, 0.62, 0.68, 'wallC')
    m.bx(-0.4, 0.4, -0.3, 0.3, 0.95, 1.0, 'woodL')
    m.bx(-0.3, -0.05, -0.12, 0.12, 1.0, 1.15, 'chrome')
    uq(m, -0.27, -0.08, -0.09, 0.09, 1.153, 'white')
    for k, c in enumerate(('pinkD', 'lemon', 'sky')):
        m.cy((0.08 + k * 0.1, 0.0, 1.0), 0.04, 0.04, 0.14, c, seg=8)
        for j in range(3):
            m.bm_((0.08 + k * 0.1 + (j - 1) * 0.012, 0.0, 1.1), (0.08 + k * 0.1 + (j - 1) * 0.02, 0.0, 1.22), 0.008, 'white', hull='none')
    make('Napkins', m, ao, cols=[cb(-0.4, -0.3, 0.0, 0.4, 0.3, 1.15)])


# ================================================================ entrance vestibule and the terrace
def build_vestibule(pal, ao):
    """vestibule glass (links, along Blender Y): a waffle-brown base and header, chrome mullions, glass (glow
    companion); automatic doors [4, 1] (span): leaves slid open, a WELCOME header"""
    VH = 3.2

    def glass(m, g, y0, y1):
        m.bx(-0.08, 0.08, y0, y1, 0.0, 0.3, 'wafD', hull='noend', cull='b')
        m.bx(-0.06, 0.06, y0, y1, VH - 0.25, VH, 'wafD', hull='noend')
        m.bx(-0.024, 0.024, y0, y1, 1.15, 1.2, 'chrome', hull='noend', cull='')
        poly(g, [(0.0, y0, 0.3), (0.0, y1, 0.3), (0.0, y1, VH - 0.25), (0.0, y0, VH - 0.25)], 'glassA', (1, 0, 0))
        if y1 - y0 > 0.6:
            streaks(g, [(0.004, y0, 0.3), (0.004, y1, 0.3), (0.004, y1, VH - 0.25), (0.004, y0, VH - 0.25)], n=1, w=0.08)
    m, g = new(pal), new(pal); glass(m, g, -0.5, 0.5)
    m.bx(-0.03, 0.03, -0.03, 0.03, 0.3, VH - 0.25, 'chrome', hull='none', cull='tb')
    make('VGlassFull', m, ao, cols=[cb(-0.08, -0.5, 0.0, 0.08, 0.5, VH)])
    make_glow('VGlassFull_G', g)
    m, g = new(pal), new(pal); glass(m, g, -0.5, -0.085)
    make('VGlassHalf', m, ao, cols=[cb(-0.08, -0.5, 0.0, 0.08, 0.0, VH)])
    make_glow('VGlassHalf_G', g)
    m = new(pal)
    m.bx(-0.085, 0.085, -0.085, 0.085, 0.0, VH + 0.02, 'chrome', cull='b')
    make('VGlassPost', m, ao)
    # doors [4, 1] along X: jambs, header box with WELCOME, two leaves slid behind the side glass
    m, g = new(pal), new(pal)
    for s in (-1, 1):
        a, b = sorted((s * 2.0, s * 1.88))
        m.bx(a, b, -0.12, 0.12, 0.0, VH, 'chrome', cull='b')
        x0, x1 = sorted((s * 1.85, s * 0.85))
        for (u0, u1) in ((x0, x0 + 0.05), (x1 - 0.05, x1)):
            m.bx(u0, u1, 0.13, 0.19, 0.02, 2.62, 'chrome', cull='b')
        m.bx(x0 + 0.05, x1 - 0.05, 0.135, 0.185, 2.57, 2.62, 'chrome', cull='lr')
        m.bx(x0 + 0.05, x1 - 0.05, 0.135, 0.185, 0.02, 0.1, 'chrome', cull='lr')
        poly(g, [(x0 + 0.05, 0.16, 0.1), (x1 - 0.05, 0.16, 0.1), (x1 - 0.05, 0.16, 2.57), (x0 + 0.05, 0.16, 2.57)], 'glassA', (0, -1, 0))
        streaks(g, [(x0 + 0.05, 0.157, 0.1), (x1 - 0.05, 0.157, 0.1), (x1 - 0.05, 0.157, 2.57), (x0 + 0.05, 0.157, 2.57)], n=1, w=0.08)
    m.bx(-1.88, 1.88, -0.2, 0.2, 2.62, VH, 'wafD')
    fq(m, -1.2, 1.2, -0.203, 2.7, 3.12, 'pinkD')
    text_front(m, 'WELCOME', 0.3, -0.206, 0.0, 2.76, 'white', maxw=2.2)
    bq(m, -1.2, 1.2, 0.203, 2.7, 3.12, 'pinkD')
    text_back(m, 'COME AGAIN', 0.26, 0.206, 0.0, 2.78, 'white', maxw=2.2)
    m.bx(-1.85, 1.85, -0.15, 0.15, 0.0, 0.02, 'steelD', hull='none', cull='b')
    make('VDoor', m, ao, cols=[cb(-2.0, -0.12, 0.0, -1.85, 0.2, VH), cb(1.85, -0.12, 0.0, 2.0, 0.2, VH)])
    make_glow('VDoor_G', g)


def build_terrace(pal, ao):
    """the raised terrace (deck slab at TER): steps [3, 3] rising toward Blender +Y (game north) and rails (links,
    along Blender Y): waffle-brown handrail, pink balusters, a kick board"""
    m = new(pal)
    n = 5
    run = 3.0 / (n + 1)
    cols = []
    for k in range(n):
        y0 = -1.5 + k * run
        top = (k + 1) * TER / (n + 1)
        m.bx(-1.42, 1.42, y0, 1.5 if k == n - 1 else y0 + run, top - 0.08, top, 'woodL', cull='blr')
        m.bx(-1.42, 1.42, y0, y0 + 0.04, 0.0, top - 0.08, 'pinkD', hull='none', cull='bklr')
        uq(m, -1.4, 1.4, y0 + 0.005, y0 + 0.05, top + 0.003, 'wafD')
        cols.append(cb(-1.5, y0, 0.0, 1.5, 1.5, top, True))
    for sx in (-1, 1):   # cheek walls either side
        a, b = sorted((sx * 1.5, sx * 1.42))
        prof = [(-1.5, 0.0), (1.5, 0.0), (1.5, TER), (-1.5 + n * run, TER), (-1.5, TER / (n + 1))]
        m.prism(prof, a, b, ['wafD'])
    make('Steps', m, ao, cols=cols)

    def rail(m, y0, y1):
        m.bx(-0.05, 0.05, y0, y1, 0.95, 1.02, 'wafD', hull='noend', cull='')
        m.bx(-0.02, 0.02, y0, y1, 0.0, 0.12, 'wafD', hull='none', cull='b')
        n = max(1, int(round((y1 - y0) / 0.33)))
        for k in range(n):
            y = y0 + (k + 0.5) * (y1 - y0) / n
            m.bx(-0.02, 0.02, y - 0.02, y + 0.02, 0.12, 0.95, 'pinkD', hull='none', cull='tb')
    m = new(pal); rail(m, -0.5, 0.5); make('TRailFull', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.5, 1.02)])
    m = new(pal); rail(m, -0.5, -0.05); make('TRailHalf', m, ao, cols=[cb(-0.05, -0.5, 0.0, 0.05, 0.0, 1.02)])
    m = new(pal)
    m.bx(-0.06, 0.06, -0.06, 0.06, 0.0, 1.1, 'wafD', cull='b')
    m.sp((0, 0, 1.14), 0.07, 'pinkD', seg=(6, 3))
    make('TRailPost', m, ao)


def build_parlour(pal, ao):
    build_dip(pal, ao)
    build_counter_end(pal, ao)
    build_till(pal, ao)
    build_sundae(pal, ao)
    build_waffle(pal, ao)
    build_shakebar(pal, ao)
    build_stool(pal, ao)
    build_softserve(pal, ao)
    build_backbar(pal, ao)
    build_cakefreezer(pal, ao)
    build_belts(pal, ao)
    build_landmark(pal, ao)
    build_booth(pal, ao)
    build_tables(pal, ao)
    build_sofa(pal, ao)
    build_windowbar(pal, ao)
    build_kids(pal, ao)
    build_small(pal, ao)
    build_planterbox(pal, ao)
    build_cart(pal, ao)
    build_vestibule(pal, ao)
    build_terrace(pal, ao)
