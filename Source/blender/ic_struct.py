"""kit-icecream structure: wall modules (parlour: mint wainscot, waffle dado rail, pink pinstripe wall, chocolate-drip
band, cream upper wall and waffle cornice; creamery: white subway tile with a mint band, painted block above) and
their wall art (menu boards, the SCOOPS & CREAM script logo run, shop windows, posters, the kids' mural, fire point,
fire exit, notice board, electrical panel, hand-wash sign, extractor louvre, a closed dock door), corner posts, the gate
(STAFF ONLY roller door), the staff-corridor trail walls, the exit hatch, ceiling bays (coffers with scalloped pendant
lamps; kitchen T-bar grid with light panels and ducts), floor tiles and marks, and columns (see ic_base.py)."""
import math
import random

from ic_base import *  # noqa: F401,F403
import ic_base as B
import ic_detail as D


# ================================================================ walls
def wall_parlour(m, z0=0.0, seed=0, x0=-0.5, x1=0.5):
    """front face (y = -0.5) from z0 up: skirting, mint bead-board wainscot, waffle dado rail, pink wall with cream
    pinstripes, a chocolate drip band, cream upper wall, waffle cornice"""
    if z0 < 0.12:
        fq(m, x0, x1, -0.503, 0.0, 0.12, 'chocD')
    if z0 < 1.1:
        fq(m, x0, x1, -0.5, max(z0, 0.12), 1.1, 'wallM')
        for x in [x0 + 0.25 + 0.5 * k for k in range(int(round((x1 - x0) * 2)))]:
            fq(m, x - 0.008, x + 0.008, -0.503, max(z0, 0.12), 1.1, 'mintD')
        fq(m, x0, x1, -0.503, 1.1, 1.21, 'waf')
        fq(m, x0, x1, -0.506, 1.1, 1.125, 'wafD')
    fq(m, x0, x1, -0.5, max(z0, 1.21), 4.7, 'wallP')
    for x in [x0 + 0.25 + 0.5 * k for k in range(int(round((x1 - x0) * 2)))]:
        fq(m, x - 0.04, x + 0.04, -0.503, max(z0, 1.21), 4.45, 'wallC')
    fq(m, x0, x1, -0.5, 4.7, 6.78, 'wallC')
    drip_band(m, x0, x1, -0.503, 4.74, 'choc', n=int(round((x1 - x0) * 2)), depth=0.22, seed=seed)
    fq(m, x0, x1, -0.503, 6.78, H, 'wafD')
    D.parlour_finish(m, x0, x1, z0)


def wall_kitchen(m, z0=0.0, x0=-0.5, x1=0.5):
    """creamery: quarry cove base, white subway tile to 2.4 m with a mint band, steel cap, painted block above"""
    if z0 < 0.15:
        fq(m, x0, x1, -0.503, 0.0, 0.15, 'quarryD')
    if z0 < 2.4:
        fq(m, x0, x1, -0.5, max(z0, 0.15), 2.4, 'tileW')
        for k in range(1, 8):
            z = 0.15 + k * 0.3
            if z > z0 and abs(z - 1.5) > 0.12:
                fq(m, x0, x1, -0.503, z - 0.006, z + 0.006, 'panel')
        if z0 < 1.42:
            fq(m, x0, x1, -0.503, 1.44, 1.56, 'mintD')
        fq(m, x0, x1, -0.503, 2.4, 2.48, 'steel')
    fq(m, x0, x1, -0.5, max(z0, 2.48), H, 'wallC')
    fq(m, x0, x1, -0.503, 6.4, 6.52, 'pinkD')
    D.kitchen_finish(m, x0, x1, z0)


def ext_point(m, x=0.0, wall=wall_parlour):
    """fire point: red extinguisher on a bracket under a FIRE sign"""
    m.bx(x - 0.14, x + 0.14, -0.56, -0.503, 1.62, 1.98, 'cherry', cull='k')
    text_front(m, 'FIRE', 0.12, -0.563, x, 1.73, 'white')
    m.cy((x, -0.63, 0.45), 0.1, 0.1, 0.56, 'red', seg=8)
    m.cy((x, -0.63, 1.01), 0.04, 0.04, 0.08, 'black', seg=6, hull='none')
    m.bm_((x + 0.04, -0.63, 1.06), (x + 0.12, -0.63, 0.98), 0.03, 'black', hull='none')
    m.bx(x - 0.12, x + 0.12, -0.53, -0.503, 0.6, 0.9, 'steelD', cull='k')


def build_walls(pal, ao):
    m = new(pal); wall_parlour(m); D.socket_plate(m, 0.3, 0.45); D.light_switch(m, -0.3, 1.45); make('WP', m, ao)
    m = new(pal); wall_kitchen(m); D.socket_plate(m, 0.3, 1.1); D.light_switch(m, -0.3, 1.3); make('WK', m, ao)
    # corner posts: the finish on all four sides
    for S in ('P', 'K'):
        m = new(pal)
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, 'wallC', cull='bt')
        bands = ((('chocD', 0.0, 0.12), ('wallM', 0.12, 1.1), ('waf', 1.1, 1.21), ('wallP', 1.21, 4.68), ('choc', 4.68, 4.74),
                  ('wafD', 6.78, H)) if S == 'P' else
                 (('quarryD', 0.0, 0.15), ('tileW', 0.15, 2.4), ('mintD', 1.44, 1.56), ('steel', 2.4, 2.48), ('pinkD', 6.4, 6.52)))
        for (c, z0, z1) in bands:
            d = 0.506 if c in ('mintD',) else 0.503
            fq(m, -0.5, 0.5, -d, z0, z1, c)
            bq(m, -0.5, 0.5, d, z0, z1, c)
            lq(m, -d, -0.5, 0.5, z0, z1, c)
            rq(m, d, -0.5, 0.5, z0, z1, c)
        make('Corner' + S, m, ao)
    m = new(pal); wall_parlour(m); ext_point(m); make('WP_Fire', m, ao)
    m = new(pal); wall_kitchen(m); ext_point(m); make('WK_Fire', m, ao)
    # fire exits (a steel door in the wall plane, push bar, a glowing EXIT box)
    for S, fn in (('P', wall_parlour), ('K', wall_kitchen)):
        m = new(pal); fn(m, z0=2.3)
        if S == 'P':
            fq(m, -0.5, -0.46, -0.5, 0.0, 2.3, 'wallM'); fq(m, 0.46, 0.5, -0.5, 0.0, 2.3, 'wallM')
        else:
            fq(m, -0.5, -0.46, -0.5, 0.0, 2.3, 'tileW'); fq(m, 0.46, 0.5, -0.5, 0.0, 2.3, 'tileW')
        m.bx(-0.46, 0.46, -0.56, -0.5, 0.0, 2.3, 'steelD', cull='kb')
        fq(m, -0.4, 0.4, -0.563, 0.04, 2.22, 'mintD' if S == 'P' else 'steel')
        m.bx(-0.34, 0.34, -0.64, -0.563, 1.0, 1.08, 'chrome')
        fq(m, -0.38, 0.38, -0.566, 1.45, 1.75, 'cherry')
        text_front(m, 'EMERGENCY EXIT', 0.08, -0.569, 0.0, 1.55, 'white', font='cond', maxw=0.7)
        D.exit_door_finish(m)
        m.bx(-0.3, 0.3, -0.62, -0.503, 2.45, 2.75, 'white', cull='k')
        make('W%s_Exit' % S, m, ao)
    g = new(pal)
    fq(g, -0.27, 0.27, -0.623, 2.48, 2.72, 'exitG')
    text_front(g, 'EXIT', 0.16, -0.626, 0.0, 2.52, 'white')
    make_glow('W_Exit_LED', g)
    build_menus(pal, ao)
    build_logo(pal, ao)
    build_windows(pal, ao)
    build_posters(pal, ao)
    build_kitchen_art(pal, ao)


def menu_frame(m, z0, z1):
    m.bx(-0.48, 0.48, -0.56, -0.503, z0, z1, 'wafD', cull='k')
    fq(m, -0.44, 0.44, -0.563, z0 + 0.04, z1 - 0.04, 'screen')
    D.menu_frame_detail(m, z0, z1)


MENUS = {
    'A': ('SCOOPS', 'pinkD', (('ONE SCOOP', '3.50'), ('TWO SCOOPS', '5.50'))),
    'B': ('CONES', 'waf', (('WAFFLE CONE', '+1.25'), ('CHOC DIPPED', '+1.75'))),
    'C': ('SUNDAES', 'cherry', (('HOT FUDGE', '6.95'), ('BANANA BOAT', '8.50'))),
}


def build_menus(pal, ao):
    """menu boards (one per module, 2.9 - 4.5 m): a coloured header, four items with prices, a drawn treat"""
    for key, (head, hc, items) in MENUS.items():
        m = new(pal); wall_parlour(m, seed=3)
        menu_frame(m, 2.85, 4.5)
        fq(m, -0.44, 0.44, -0.566, 4.12, 4.46, hc)
        text_front(m, head, 0.24, -0.569, 0.0, 4.17, 'white', maxw=0.8)
        for k, (item, price) in enumerate(items):
            z = 3.78 - k * 0.3
            text_front(m, item, 0.1, -0.566, -0.4, z, 'wallC', font='cond', align='l', maxw=0.56)
            text_front(m, price, 0.1, -0.566, 0.4, z, 'lemon', font='cond', align='r', maxw=0.24)
        # the treat (a cone with a scoop, painted) under the list
        poly(m, [(-0.08, -0.566, 3.0), (0.08, -0.566, 3.0), (0.0, -0.566, 2.88)], 'waf', (0, -1, 0))
        fdisc(m, 0.0, -0.569, 3.07, 0.085, {'A': 'strawb', 'B': 'vanilla', 'C': 'chocF'}[key], seg=10)
        make('WP_Menu' + key, m, ao)


def build_logo(pal, ao):
    """the SCOOPS & CREAM logo across ten modules high on the wall (script lettering with a chocolate shadow, a
    waffle underline): each module draws its slice of the word"""
    for k in range(10):
        m = new(pal); wall_parlour(m, seed=k)
        ib_text.draw(m, 'Scoops & Cream', 4.5 - k, -0.509, 5.35, 1.15, 'pinkD', face='y-', font='script', maxw=9.2,
                     clip=(k - 5.0, k - 4.0))
        fq(m, -0.5, 0.5, -0.506, 4.88, 4.96, 'waf')
        make('WP_Logo%d' % k, m, ao)


def window(m, kind):
    """a shop window (0.85 - 3.4 m): waffle-brown frame, a mullion, sill; the pane is the glow companion"""
    wall_parlour(m, z0=3.4)
    fq(m, -0.5, 0.5, -0.5, 0.0, 0.12, 'chocD')
    fq(m, -0.5, 0.5, -0.5, 0.12, 0.85, 'wallM')
    m.bx(-0.5, 0.5, -0.62, -0.45, 0.8, 0.88, 'waf', hull='noside')
    m.bx(-0.5, 0.5, -0.56, -0.45, 3.36, 3.44, 'wafD', hull='noside', cull='t')
    for x in (-0.5, 0.5):
        m.bx(x - 0.04 if x > 0 else x, x if x > 0 else x + 0.04, -0.56, -0.45, 0.88, 3.36, 'wafD', hull='none', cull='tb')
    m.bx(-0.025, 0.025, -0.54, -0.45, 0.88, 3.36, 'wafD', hull='none', cull='tbk')
    m.bx(-0.46, 0.46, -0.535, -0.455, 2.66, 2.71, 'wafD', hull='none', cull='lrk')
    D.window_finish(m)
    if kind == 'B':   # a window decal: a big painted cone with two scoops
        poly(m, [(0.12, -0.476, 1.25), (0.38, -0.476, 1.25), (0.25, -0.476, 0.98)], 'waf', (0, -1, 0))
        fdisc(m, 0.25, -0.48, 1.37, 0.14, 'strawb', seg=10)
        fdisc(m, 0.25, -0.484, 1.58, 0.12, 'mintF', seg=10)
    if kind == 'C':   # an OPEN sign hung in the window (its tubes glow)
        m.bx(-0.36, 0.36, -0.53, -0.51, 1.95, 2.35, 'black', cull='k')
        m.bm_((-0.2, -0.52, 2.35), (-0.16, -0.52, 2.66), 0.008, 'steelD', hull='none')
        m.bm_((0.2, -0.52, 2.35), (0.16, -0.52, 2.66), 0.008, 'steelD', hull='none')


def build_windows(pal, ao):
    for kind in 'AB':
        m = new(pal); window(m, kind); make('WP_Win' + kind, m, ao)
    g = new(pal)   # the pane: bright daylight through the glass, a sheen streak
    fq(g, -0.475, 0.475, -0.47, 0.88, 3.36, 'glassL')
    fq(g, -0.3, -0.18, -0.473, 1.2, 3.0, 'white')
    make_glow('WP_Win_LED', g)


def build_posters(pal, ao):
    # framed posters: a sundae, a cone, a shake (each painted layer 3 mm in front of the one under it)
    for key, word, treat in (('A', 'SUNDAE FUNDAY', 'sundae'), ('B', 'GET THE SCOOP', 'cone')):
        m = new(pal); wall_parlour(m, seed=7)
        m.bx(-0.4, 0.4, -0.55, -0.503, 1.6, 2.7, 'wafD', cull='k')
        bg = {'A': 'lemon', 'B': 'sky', 'C': 'lilac'}[key]
        fq(m, -0.35, 0.35, -0.553, 1.65, 2.65, bg)
        text_front(m, word, 0.085, -0.556, 0.0, 1.72, 'chocD', maxw=0.62)
        y = [-0.556]

        def L():
            y[0] -= 0.003
            return y[0]
        if treat == 'cone':
            poly(m, [(-0.12, L(), 2.1), (0.12, y[0], 2.1), (0.0, y[0], 1.86)], 'waf', (0, -1, 0))
            fdisc(m, 0.0, L(), 2.2, 0.13, 'strawb', seg=10)
            fdisc(m, 0.0, L(), 2.4, 0.11, 'vanilla', seg=10)
            fdisc(m, 0.0, L(), 2.53, 0.035, 'cherry', seg=8)
        elif treat == 'sundae':
            yy = L()
            poly(m, [(-0.2, yy, 2.15), (0.2, yy, 2.15), (0.07, yy, 1.98), (-0.07, yy, 1.98)], 'glassL', (0, -1, 0))
            fq(m, -0.03, 0.03, yy, 1.88, 1.98, 'glassL')
            for k, c in enumerate(('chocF', 'strawb', 'vanilla')):
                fdisc(m, -0.1 + k * 0.1, L(), 2.22, 0.09, c, seg=10)
            fdisc(m, 0.0, L(), 2.38, 0.08, 'white', seg=10)
            fdisc(m, 0.0, L(), 2.5, 0.035, 'cherry', seg=8)
        else:
            yy = L()
            poly(m, [(-0.13, yy, 2.4), (0.13, yy, 2.4), (0.09, yy, 1.88), (-0.09, yy, 1.88)], 'strawb', (0, -1, 0))
            fdisc(m, 0.0, L(), 2.42, 0.12, 'white', seg=10)
            m.bx(0.03, 0.06, L() - 0.006, y[0], 2.45, 2.62, 'pinkD', hull='none', cull='k')
        make('WP_Poster' + key, m, ao)
    # the kids' corner mural on the wainscot and the pink: a rainbow, clouds, a smiling cone
    for key in 'AB':
        m = new(pal); wall_parlour(m, seed=11)
        if key == 'A':
            for k, c in enumerate(('cherry', 'orange', 'lemon', 'mintD', 'sky', 'lilac')):
                r0, r1 = 0.4 - k * 0.06, 0.46 - k * 0.06
                yy = -0.506
                pts = [(math.cos(math.pi * i / 10) * r1, yy, 1.3 + math.sin(math.pi * i / 10) * r1) for i in range(11)]
                pts += [(math.cos(math.pi * i / 10) * r0, yy, 1.3 + math.sin(math.pi * i / 10) * r0) for i in range(10, -1, -1)]
                for i in range(10):
                    poly(m, [pts[i], pts[i + 1], pts[21 - i - 1], pts[21 - i]], c, (0, -1, 0))
            for (cx, cz) in ((-0.28, 1.32), (0.28, 1.32)):
                fdisc(m, cx, -0.509, cz, 0.12, 'white', seg=10)
                fdisc(m, cx + 0.08 * (1 if cx > 0 else -1), -0.512, cz + 0.06, 0.09, 'white', seg=10)
        else:
            poly(m, [(-0.16, -0.506, 2.0), (0.16, -0.506, 2.0), (0.0, -0.506, 1.5)], 'waf', (0, -1, 0))
            fdisc(m, 0.0, -0.509, 2.13, 0.19, 'cotton', seg=12)
            fdisc(m, -0.06, -0.512, 2.17, 0.025, 'chocD', seg=6)
            fdisc(m, 0.06, -0.512, 2.17, 0.025, 'chocD', seg=6)
            fq(m, -0.05, 0.05, -0.515, 2.06, 2.08, 'chocD')
            text_front(m, 'KIDS CLUB', 0.12, -0.506, 0.0, 2.45, 'pinkD', maxw=0.8)
            for k in range(5):
                fdisc(m, -0.38 + k * 0.19, -0.506, 0.75 - (k % 2) * 0.2, 0.05, ('lemon', 'sky', 'cherry', 'lilac', 'orange')[k], seg=8)
        make('WP_Mural' + key, m, ao)


def build_kitchen_art(pal, ao):
    m = new(pal); wall_kitchen(m)   # food-safety notice board
    m.bx(-0.42, 0.42, -0.55, -0.503, 1.35, 2.15, 'wood', cull='k')
    fq(m, -0.38, 0.38, -0.553, 1.39, 2.11, 'cardL')
    for k, (x, z, c) in enumerate(((-0.25, 1.85, 'white'), (0.05, 1.8, 'lemon'), (0.25, 1.55, 'white'), (-0.2, 1.5, 'sky'))):
        fq(m, x - 0.11, x + 0.11, -0.556 - 0.003 * k, z - 0.12, z + 0.14, c)
    text_front(m, 'CLEAN AS YOU GO', 0.06, -0.556, 0.0, 2.0, 'chocD', font='cond', maxw=0.7)
    make('WK_Board', m, ao)
    m = new(pal); wall_kitchen(m)   # electrical panel and conduit
    m.bx(-0.32, 0.32, -0.66, -0.503, 1.0, 2.0, 'steelD', cull='k')
    fq(m, -0.28, 0.28, -0.663, 1.04, 1.96, 'steel')
    m.bx(0.2, 0.24, -0.69, -0.663, 1.45, 1.6, 'black')
    fq(m, -0.12, 0.12, -0.666, 1.75, 1.85, 'hazY')
    m.bx(-0.05, 0.05, -0.58, -0.503, 2.0, H, 'steel', cull='kt')
    make('WK_Panel', m, ao)
    m = new(pal); wall_kitchen(m)   # hand-wash sign over a paper-towel dispenser
    m.bx(-0.3, 0.3, -0.53, -0.503, 1.75, 2.15, 'white', cull='k')
    fq(m, -0.27, 0.27, -0.533, 2.02, 2.12, 'sky')
    text_front(m, 'WASH HANDS', 0.07, -0.536, 0.0, 1.85, 'chocD', font='cond', maxw=0.5)
    m.bx(-0.16, 0.16, -0.64, -0.503, 1.15, 1.55, 'chrome', cull='k')
    fq(m, -0.1, 0.1, -0.643, 1.15, 1.2, 'white')
    make('WK_Wash', m, ao)
    m = new(pal); wall_kitchen(m)   # extractor louvre high on the wall
    m.bx(-0.45, 0.45, -0.6, -0.503, 4.6, 5.5, 'steel', cull='k')
    for k in range(6):
        z = 4.68 + k * 0.13
        m.prism([(-0.6, z), (-0.64, z + 0.02), (-0.6, z + 0.08)], -0.42, 0.42, ['steelD'], hull='none')
    make('WK_Vent', m, ao)
    m = new(pal); wall_kitchen(m)   # food-safety sign: HAIRNETS ON
    m.bx(-0.36, 0.36, -0.53, -0.503, 1.65, 2.25, 'sky', cull='k')
    fq(m, -0.32, 0.32, -0.533, 1.69, 2.21, 'white')
    fdisc(m, 0.0, -0.536, 2.04, 0.11, 'sky', seg=10)
    fq(m, -0.06, 0.06, -0.539, 2.0, 2.08, 'white')
    text_front(m, 'HAIRNETS ON', 0.075, -0.536, 0.0, 1.76, 'chocD', font='cond', maxw=0.56)
    make('WK_Safety', m, ao)
    m = new(pal); wall_kitchen(m)   # a wall clock and the churn schedule whiteboard
    m.cy((0.0, -0.503, 3.1), 0.22, 0.22, 0.05, 'pinkD', seg=12, rot=(90, 0, 0))
    fdisc(m, 0.0, -0.556, 3.1, 0.18, 'white', seg=12)
    m.bx(-0.008, 0.008, -0.562, -0.559, 3.1, 3.24, 'black', hull='none', cull='k')
    m.bx(0.0, 0.1, -0.565, -0.562, 3.09, 3.11, 'black', hull='none', cull='k')
    m.bx(-0.45, 0.45, -0.53, -0.503, 1.35, 2.1, 'chrome', cull='k')
    fq(m, -0.42, 0.42, -0.533, 1.38, 2.07, 'white')
    text_front(m, 'CHURN TODAY', 0.07, -0.536, 0.0, 1.94, 'pinkD', font='cond', maxw=0.7)
    for k in range(3):
        fq(m, -0.36, 0.1 + 0.1 * k, -0.536, 1.5 + k * 0.12, 1.53 + k * 0.12, ('sky', 'mintD', 'chocF')[k])
    make('WK_Clock', m, ao)
    # closed dock door (3 m bay; the centre module draws it, the cells either side are '_')
    m = new(pal)
    wall_kitchen(m, z0=3.7, x0=-1.5, x1=1.5)
    fq(m, -1.5, -1.3, -0.5, 0.0, 3.7, 'hazY')
    fq(m, 1.3, 1.5, -0.5, 0.0, 3.7, 'hazY')
    for k in range(14):
        z = 0.1 + k * 0.24
        m.bx(-1.3, 1.3, -0.56, -0.5, z, z + 0.2, 'steel' if k % 2 else 'chrome', hull='none', cull='kblr')
    m.bx(-1.32, 1.32, -0.6, -0.5, 3.45, 3.7, 'steelD', cull='k')
    m.bx(-1.3, 1.3, -0.58, -0.5, 0.0, 0.1, 'black', cull='kb')
    fq(m, -0.6, 0.6, -0.563, 1.7, 2.05, 'cherry')
    text_front(m, 'DELIVERIES', 0.2, -0.566, 0.0, 1.77, 'white', maxw=1.1)
    m.bx(-1.5, 1.5, -0.65, -0.5, 0.0, 0.08, 'black', hull='none', cull='kb')
    make('WK_Dock', m, ao)


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.49, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'steel', cull='b')
        for fy in (-1, 1):
            (fq if fy < 0 else bq)(m, a + 0.06, b - 0.06, fy * 0.623, 0.12, 1.0, 'chrome')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.75, 'steelD')
    # wall over the doors: the parlour finish in front, the kitchen tile at the back
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.75, H, 'wallC', cull='t')
    fq(m, -2.48, 2.48, -0.453, 3.75, 4.7, 'wallP')
    drip_band(m, -2.48, 2.48, -0.456, 4.74, 'choc', n=18, depth=0.22, seed=5)
    bq(m, -2.48, 2.48, 0.453, 6.4, 6.52, 'pinkD')
    # front: STAFF ONLY board under a scoop sign; back: THANK YOU, COME AGAIN
    m.bx(-1.45, 1.45, -0.62, -0.45, 3.95, 4.55, 'pinkD')
    text_front(m, 'STAFF ONLY', 0.4, -0.623, 0.0, 4.05, 'white', maxw=2.6)
    m.bx(-1.2, 1.2, 0.45, 0.6, 4.0, 4.7, 'mintD')
    text_back(m, 'Scoops & Cream', 0.34, 0.603, 0.0, 4.2, 'white', font='script', maxw=2.2)
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    g = new(pal)
    fq(g, -0.45, 0.45, -0.623, 4.75, 5.1, 'exitG')
    text_front(g, 'EXIT', 0.24, -0.626, 0.0, 4.81, 'white')
    make_glow('GateFrame_LED', g)
    # roller door: pink and cream slats, a chocolate bottom bar, the warning words
    m = new(pal)
    Hs, n = 3.05, 12
    for i in range(n):
        z = 0.2 + (i + 0.5) * (Hs - 0.2) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.2) / n - 0.02), 'wallP' if i % 2 else 'wallC', bevel=False)
    m.box((0, 0, 0.1), (3.0, 0.12, 0.2), 'chocD', bevel=False)
    m.box((0, -0.06, 1.85), (2.0, 0.01, 0.4), 'pinkD', bevel=False)
    text_front(m, 'STAFF ONLY', 0.26, -0.069, 0.0, 1.92, 'white', maxw=1.8)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # staff corridor walls (1 m along Blender Y, inner face +X): tile dado, mint band, cream above, a bump rail
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'wallC', hull='noend', cull='t')
        rq(m, 0.253, -0.5, 0.5, 0.0, 0.15, 'quarryD')
        rq(m, 0.253, -0.5, 0.5, 0.15, 1.6, 'tileW')
        rq(m, 0.256, -0.5, 0.5, 1.0, 1.1, 'mintD')
        m.bx(0.25, 0.32, -0.5, 0.5, 0.75, 0.88, 'chrome', hull='noend', cull='')
        rq(m, 0.253, -0.5, 0.5, 5.6, 5.72, 'pinkD')
        if name == 'TrailWall_B':   # a wall light
            m.bx(0.25, 0.38, -0.22, 0.22, 2.6, 2.82, 'chrome')
            rq(m, 0.383, -0.19, 0.19, 2.62, 2.8, 'lightW')
        elif name == 'TrailWall_C':   # the staff rota board and a coat hook
            m.bx(0.253, 0.27, -0.32, 0.32, 1.65, 2.25, 'white', cull='l')
            rq(m, 0.273, -0.28, 0.28, 2.1, 2.2, 'pinkD')
            text_side(m, 'STAFF ROTA', 0.08, 0.276, 0.0, 1.95, 'chocD', 'x+', font='cond', maxw=0.5)
            m.bm_((0.27, 0.42, 1.75), (0.36, 0.42, 1.8), 0.03, 'chrome', hull='none')
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=20)
    ring(m, 0, 0, 0.103, 0.95, 1.12, 'pinkD', seg=20)
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ ceiling bays (hang from z = 0 = the ceiling at H)
def pendant(m, g, x, y, drop, shade):
    """a pendant lamp: cord, a cone shade, the bulb (glow)"""
    m.bx(x - 0.008, x + 0.008, y - 0.008, y + 0.008, -drop + 0.3, -0.005, 'black', hull='none', cull='tb')
    m.cy((x, y, -drop), 0.34, 0.06, 0.32, shade, seg=8)
    g.cy((x, y, -drop + 0.02), 0.31, 0.31, 0.004, 'lightW', seg=8)


def coffer(m, panel):
    """a coffer bay: waffle-brown beams on its -X and -Y edges (the next bay draws the others), a pastel panel"""
    m.bx(-2.1, -1.9, -2.1, 1.9, -0.32, -0.003, 'wafD', hull='none', cull='tkf')
    m.bx(-1.9, 1.9, -2.1, -1.9, -0.32, -0.003, 'wafD', hull='none', cull='tlr')
    dq(m, -1.6, 1.7, -1.6, 1.7, -0.008, panel)
    for (a, b) in ((-1.6, 1.7),):
        dq(m, a, b, -1.75, -1.6, -0.01, 'waf')
        dq(m, a, b, 1.7, 1.85, -0.01, 'waf')
        dq(m, -1.75, -1.6, a, b, -0.01, 'waf')
        dq(m, 1.7, 1.85, a, b, -0.01, 'waf')


def build_ceiling(pal, ao):
    for v, panel, shade, lamp in (('A', 'wallP', 'pinkD', True), ('B', 'wallM', None, False), ('D', 'sky', None, False)):
        m, g = new(pal), new(pal)
        coffer(m, panel)
        if lamp:
            pendant(m, g, 0.05, 0.05, 2.2, shade)
        make('Ceil_' + v, m, ao)
        if lamp:
            make_glow('Ceil_%s_LED' % v, g)
    # kitchen: T-bar grid with a light panel, a duct run along X
    for v in ('K', 'KD'):
        m, g = new(pal), new(pal)
        m.bx(-2.02, -1.98, -2.0, 2.0, -0.06, -0.003, 'steel', hull='none', cull='tkf')
        m.bx(-1.98, 2.0, -2.02, -1.98, -0.054, -0.003, 'steel', hull='none', cull='tlr')
        m.bx(-0.7, 0.7, -0.5, 0.5, -0.1, -0.003, 'chrome', hull='none', cull='t')
        dq(g, -0.65, 0.65, -0.45, 0.45, -0.103, 'lightW')
        if v == 'KD':   # a round supply duct on two hangers
            cyl_x(m, -2.0, 2.0, 1.2, -0.75, 0.3, 'steel', seg=8, caps=False, hull='noside')
            for x in (-1.0, 1.0):
                m.bx(x - 0.04, x + 0.04, 1.16, 1.24, -0.45, -0.003, 'steelD', hull='none', cull='t')
        make('Ceil_' + v, m, ao)
        make_glow('Ceil_%s_LED' % v, g)


# ================================================================ floor tiles and marks (layer 0.01)
def build_floors(pal, ao):
    m = new(pal)   # a pink checker square (the cream floor shows between, the grout lines round it)
    uq(m, -0.49, 0.49, -0.49, 0.49, 0.002, 'wallP')
    make('F_Chk', m, ao)
    m = new(pal)   # chocolate checker square (behind the counters)
    uq(m, -0.49, 0.49, -0.49, 0.49, 0.002, 'choc')
    make('F_ChkD', m, ao)
    m = new(pal)   # a yellow walkway line through the cell (rotate: run; the creamery floor is the zone's own paint)
    uq(m, -0.5, 0.5, -0.06, 0.06, 0.005, 'hazY')
    make('F_Line', m, ao)
    m = new(pal)   # a floor drain
    disc(m, 0, 0, 0.005, 0.17, 'steelD', seg=8)
    for k in range(-2, 3):
        uq(m, -0.11, 0.11, k * 0.05 - 0.012, k * 0.05 + 0.012, 0.008, 'black')
    make('F_Drain', m, ao)
    m = new(pal)   # entrance mat [3, 2]
    uq(m, -1.45, 1.45, -0.95, 0.95, 0.004, 'chocD')
    uq(m, -1.35, 1.35, -0.85, 0.85, 0.007, 'pinkD')
    text_up(m, 'Hello Sweetie', 0.42, 0.01, 0.0, 0.0, 'wallC', font='script', maxw=2.4, flip=True)
    make('F_Mat', m, ao)


# ================================================================ columns
def build_columns(pal, ao):
    m = new(pal)   # parlour: a candy-striped column with a waffle base and capital
    m.cy((0, 0, 0), 0.36, 0.36, 0.3, 'wafD', seg=12)
    pillar(m, 0, 0, 0.3, H - 0.55, 0.28, ['wallC', 'pinkD'], seg=10)
    m.cy((0, 0, H - 0.55), 0.3, 0.42, 0.35, 'waf', seg=12)
    m.cy((0, 0, H - 0.2), 0.44, 0.44, 0.2, 'wafD', seg=12, caps=False)
    make('Column', m, ao, cols=[cb(-0.36, -0.36, 0, 0.36, 0.36, 0.3), cb(-0.28, -0.28, 0.3, 0.28, 0.28, H)])
    m = new(pal)   # creamery: a square column clad in steel to 2 m, a yellow / black guard
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, H, 'wallC', cull='bt')
    for (c, z0, z1) in (('steel', 0.0, 2.0), ('hazY', 0.1, 0.4), ('black', 0.4, 0.55), ('hazY', 0.55, 0.85)):
        d = 0.303 if c == 'steel' else 0.306
        fq(m, -0.3, 0.3, -d, z0, z1, c)
        bq(m, -0.3, 0.3, d, z0, z1, c)
        lq(m, -d, -0.3, 0.3, z0, z1, c)
        rq(m, d, -0.3, 0.3, z0, z1, c)
    make('ColumnK', m, ao, cols=[cb(-0.3, -0.3, 0, 0.3, 0.3, H)])
