"""kit-datacenter structure: wall modules in four finishes (data hall, NOC, lab, secure rooms) with their wall art,
corner posts, the breakable doors (security door, vault door, glass door, cage gate: frame + leaf + two damage stages +
what is left after it bursts), glass and cage partitions, the gate portal, shutter, corridor walls and exit hatch,
ceiling fittings and floor finishes (see dc_base.py for conventions)."""
import math
import random

from dc_base import *  # noqa: F401,F403
import dc_base as B


def strip(m, pts, w, y, c, s=-1):
    """a polyline (x, z) painted as ONE polygon w wide on a plane y facing -Y (s -1) or +Y (s 1)"""
    L, R = [], []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / n * w / 2, dx / n * w / 2
        L.append((p[0] + nx, y, p[1] + nz))
        R.append((p[0] - nx, y, p[1] - nz))
    poly(m, L + R[::-1], c, (0, s, 0))


def spots(rnd, n, x0, x1, z0, z1, gap, tries=200):
    """up to n random points in a rectangle at least `gap` apart"""
    out = []
    for _ in range(tries):
        if len(out) >= n:
            break
        p = (rnd.uniform(x0, x1), rnd.uniform(z0, z1))
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= gap for q in out):
            out.append(p)
    return out


def face_q(m, side, x0, x1, y, z0, z1, c):
    """a painted quad on a -Y (side -1) or +Y (side 1) plane"""
    (fq if side < 0 else bq)(m, x0, x1, y, z0, z1, c)


# ================================================================ walls
def wall_hall(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'wallW')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'wallL')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.16, 'graph')
    fq(m, -0.5, 0.5, -0.506, 1.0, 1.08, 'teal')
    fq(m, -0.5, 0.5, -0.506, 1.08, 1.1, 'tealD')
    fq(m, -0.5, -0.492, -0.503, 0.16, 5.3, 'joint')
    for z in (2.6, 4.1):
        fq(m, -0.5, 0.5, -0.506, z, z + 0.014, 'joint')
    fq(m, -0.5, 0.5, -0.509, 5.3, H, 'graph')


def wall_noc(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'graph')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'graphL')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.16, 'graphD')
    for z0, z1 in ((0.3, 2.15), (2.32, 4.9)):
        fq(m, -0.46, 0.46, -0.503, z0, z1, 'graphL')
    fq(m, -0.5, 0.5, -0.503, 2.2, 2.26, 'cyan')
    fq(m, -0.5, 0.5, -0.509, 5.3, H, 'graphD')


def wall_lab(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'wallW')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'wallL')
    fq(m, -0.5, 0.5, -0.509, 0.0, 0.12, 'graph')
    fq(m, -0.5, 0.5, -0.503, 0.86, 0.9, 'cyan')
    fq(m, -0.5, -0.494, -0.503, 0.9, 4.3, 'cyanL')
    fq(m, -0.5, 0.5, -0.503, 4.3, H, 'wallL')
    fq(m, -0.5, 0.5, -0.506, 4.3, 4.34, 'cyan')
    fq(m, -0.5, 0.5, -0.509, 5.6, H, 'graph')


def wall_room(m):
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'wallG')
    bq(m, -0.5, 0.5, 0.5, 0.0, H, 'wallG')
    for k in range(1, 9):
        fq(m, -0.5, 0.5, -0.503, 0.3 + k * 0.4, 0.31 + k * 0.4, 'joint')
    fq(m, -0.5, -0.49, -0.506, 0.3, 3.5, 'joint')
    chevrons(m, -0.5, 0.5, -0.503, 0.0, 0.3, 4)
    fq(m, -0.5, 0.5, -0.503, 3.6, 3.7, 'graph')
    fq(m, -0.5, 0.5, -0.509, 5.4, H, 'graph')


STYLES = {'H': wall_hall, 'N': wall_noc, 'L': wall_lab, 'R': wall_room}


def grille(m, x0, x1, z0, z1, c='graph', slat='graphD'):
    m.bx(x0, x1, -0.56, -0.5, z0, z1, c, cull='k')
    slats(m, x0 + 0.05, x1 - 0.05, -0.563, z0 + 0.05, z1 - 0.05, 8, slat)


def screen_frame(m, x0, x1, z0, z1, c='graphD', d=0.07, hull='full'):
    m.bx(x0, x1, -0.5 - d, -0.5, z0, z1, c, hull=hull, cull='k')


def video_content(m, seed, x0, x1, rows):
    """screens of the NOC video wall (glow companion): maps, graphs, bars, status tiles"""
    r = random.Random(seed)
    y = -0.582
    for (z0, z1) in rows:
        fq(m, x0, x1, y, z0, z1, 'screen')
        kind = r.choice(['graph', 'bars', 'map', 'tiles', 'graph'])
        yy = y - 0.003
        if kind == 'graph':
            pts = [(x0 + 0.05 + (x1 - x0 - 0.1) * i / 9, z0 + 0.15 + r.uniform(0.1, 0.7) * (z1 - z0 - 0.3)) for i in range(10)]
            strip(m, pts, 0.024, yy, r.choice(['scrC', 'scrG']))
            fq(m, x0 + 0.05, x1 - 0.05, yy, z0 + 0.1, z0 + 0.11, 'scrB')
        elif kind == 'bars':
            n = 7
            w = (x1 - x0 - 0.12) / n
            for i in range(n):
                h = r.uniform(0.15, 0.85) * (z1 - z0 - 0.2)
                fq(m, x0 + 0.06 + i * w + 0.015, x0 + 0.06 + (i + 1) * w - 0.015, yy, z0 + 0.1, z0 + 0.1 + h, r.choice(['scrC', 'scrO', 'scrG', 'scrP']))
        elif kind == 'map':
            for (cx, cz) in spots(r, 9, x0 + 0.1, x1 - 0.1, z0 + 0.12, z1 - 0.12, 0.2):
                poly(m, [(cx - 0.08, yy, cz - 0.04), (cx + 0.07, yy, cz - 0.06), (cx + 0.09, yy, cz + 0.05), (cx - 0.05, yy, cz + 0.07)], 'scrB', (0, -1, 0))
                fq(m, cx - 0.012, cx + 0.012, yy - 0.003, cz - 0.012, cz + 0.012, r.choice(['scrO', 'scrC', 'scrG']))
        else:
            for i in range(4):
                for k in range(2):
                    a, b = x0 + 0.05 + i * (x1 - x0 - 0.1) / 4, x0 + 0.05 + (i + 1) * (x1 - x0 - 0.1) / 4 - 0.03
                    c0, c1 = z0 + 0.06 + k * (z1 - z0 - 0.12) / 2, z0 + 0.06 + (k + 1) * (z1 - z0 - 0.12) / 2 - 0.03
                    fq(m, a, b, yy, c0, c1, r.choice(['scrG', 'scrG', 'scrG', 'scrO', 'scrB']))


def build_walls(pal, ao):
    for S, fn in STYLES.items():
        m = new(pal)
        fn(m)
        make('W' + S, m, ao)
        # corner post: the style's finish on all four sides
        m = new(pal)
        body = {'H': 'wallW', 'N': 'graph', 'L': 'wallW', 'R': 'wallG'}[S]
        trim = {'H': 'graph', 'N': 'graphD', 'L': 'graph', 'R': 'graph'}[S]
        m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, H, body, cull='b')
        # bands painted round the post (proud boxes would meet the wall modules' own trims in one plane)
        acc = {'H': ('teal', 1.0, 1.08), 'N': ('cyan', 2.2, 2.26), 'L': ('cyan', 0.86, 0.9), 'R': ('hazY', 0.3, 0.38)}[S]
        for (c, z0, z1) in ((trim, 0.0, 0.16), (trim, 5.3 if S != 'L' else 5.6, H), acc):
            # one quad a side, each exactly the post's width, so neighbouring posts' bands only meet edge to edge
            fq(m, -0.5, 0.5, -0.503, z0, z1, c)
            bq(m, -0.5, 0.5, 0.503, z0, z1, c)
            lq(m, -0.503, -0.5, 0.5, z0, z1, c)
            rq(m, 0.503, -0.5, 0.5, z0, z1, c)
        make('Corner' + S, m, ao)
    # ---- data hall art
    m = new(pal); wall_hall(m); grille(m, -0.42, 0.42, 3.3, 4.2); make('WH_Grille', m, ao)
    m = new(pal); wall_hall(m)
    m.bx(-0.36, -0.04, -0.6, -0.5, 1.35, 1.75, 'fireR', cull='k')            # fire alarm panel
    fq(m, -0.32, -0.08, -0.603, 1.55, 1.7, 'screen')
    leds(m, -0.32, -0.08, -0.603, 1.45, 4, ['ledG', 'ledG', 'hazY', 'ledG'])
    text_front(m, 'FIRE', 0.05, -0.603, -0.2, 1.38, 'paper')
    m.cy((0.22, -0.62, 0.12), 0.09, 0.09, 0.5, 'fireR', seg=8)              # extinguisher on a bracket
    m.cy((0.22, -0.62, 0.62), 0.05, 0.03, 0.08, 'black', seg=6, hull='none')
    m.bx(0.19, 0.25, -0.53, -0.5, 0.25, 0.55, 'steelD', hull='none')
    fq(m, 0.12, 0.32, -0.503, 0.75, 0.95, 'fireR')
    make('WH_Panel', m, ao)
    for code, sub in (('A1', 'DATA HALL'), ('B2', 'DATA HALL'), ('C3', 'R&D WING')):
        m = new(pal); wall_hall(m)
        m.bx(-0.42, 0.42, -0.56, -0.5, 2.9, 4.0, 'teal', cull='k')
        fq(m, -0.4, 0.4, -0.563, 3.72, 3.98, 'tealD')
        text_front(m, sub, 0.12, -0.566, 0.0, 3.78, 'paper', maxw=0.74)
        text_front(m, code, 0.52, -0.566, 0.0, 3.06, 'paper', font='display', maxw=0.74)
        make('WH_Sign' + code[0], m, ao)
    m = new(pal); wall_hall(m)                                                # emergency power off + phone
    m.bx(-0.3, 0.05, -0.58, -0.5, 1.3, 1.7, 'hazY', cull='k')
    m.cy((-0.125, -0.58, 1.5), 0.07, 0.07, 0.06, 'fireR', seg=10, rot=(90, 0, 0))
    text_front(m, 'EPO', 0.06, -0.583, -0.125, 1.33, 'black')
    m.bx(0.18, 0.36, -0.57, -0.5, 1.2, 1.55, 'graph', cull='k')
    m.bx(0.2, 0.34, -0.61, -0.57, 1.3, 1.5, 'graphD', hull='none', cull='k')
    make('WH_Epo', m, ao)
    m = new(pal); wall_hall(m)                                                # cable riser conduits
    for x in (-0.25, 0.0, 0.25):
        m.cy((x, -0.62, 0.16), 0.06, 0.06, 5.14, 'steelL', seg=8, caps=False)
        for z in (1.2, 2.8, 4.4):
            m.bx(x - 0.08, x + 0.08, -0.7, -0.5, z, z + 0.05, 'steelD', hull='none')
    make('WH_Riser', m, ao)
    # ---- NOC: the video wall (left end / middle / right end; screens are the glow companion) and world clocks
    rows = ((1.25, 2.27), (2.31, 3.33), (3.37, 4.39))
    for part in ('L', 'M', 'R'):
        m = new(pal); wall_noc(m)
        x0 = -0.42 if part == 'L' else -0.5
        x1 = 0.42 if part == 'R' else 0.5
        m.bx(x0, x1, -0.58, -0.5, 1.15, 1.25, 'graphD', hull='noside' if part == 'M' else 'full', cull='k')
        m.bx(x0, x1, -0.58, -0.5, 4.39, 4.5, 'graphD', hull='noside' if part == 'M' else 'full', cull='k')
        for (z0, z1) in rows[:-1]:
            fq(m, x0, x1, -0.583, z1, z1 + 0.04, 'black')
        if part != 'M':
            xe = x0 if part == 'L' else x1 - 0.08
            m.bx(xe, xe + 0.08, -0.58, -0.5, 1.25, 4.39, 'graphD', cull='k')
            m.bx(xe - 0.02, xe + 0.1, -0.64, -0.5, 0.4, 1.0, 'black', cull='k')      # speaker column
        make('WN_Video' + part, m, ao)
        g = new(pal)
        a = x0 + (0.08 if part == 'L' else 0.0)
        b = x1 - (0.08 if part == 'R' else 0.0)
        video_content(g, {'L': 3, 'M': 7, 'R': 11}[part], a + 0.005, b - 0.005, rows)
        make_glow('WN_Video' + part + '_LED', g)
    m = new(pal); wall_noc(m)
    for i, (city, t) in enumerate((('NYC', '04:12'), ('LON', '09:12'), ('TKY', '18:12'))):
        x = -0.32 + i * 0.32
        m.bx(x - 0.14, x + 0.14, -0.56, -0.5, 3.6, 3.86, 'black', cull='k')
        text_front(m, city, 0.05, -0.563, x, 3.9, 'cyanL')
    make('WN_Clock', m, ao)
    g = new(pal)
    for i, t in enumerate(('04:12', '09:12', '18:12')):
        x = -0.32 + i * 0.32
        text_front(g, t, 0.11, -0.565, x, 3.66, 'scrO', font='display', maxw=0.25)
    make_glow('WN_Clock_LED', g)
    # ---- lab art
    m = new(pal); wall_lab(m)
    screen_frame(m, -0.46, 0.46, 1.4, 2.9, 'graph', 0.06)
    make('WL_Screen', m, ao)
    g = new(pal)                                                              # a robot blueprint on blue
    y = -0.563
    fq(g, -0.43, 0.43, y, 1.43, 2.87, 'scrB')
    yy = y - 0.003
    for (a, b, c0, c1) in ((-0.1, 0.1, 2.45, 2.7), (-0.16, 0.16, 1.95, 2.42), (-0.24, -0.18, 1.98, 2.36), (0.18, 0.24, 1.98, 2.36),
                           (-0.13, -0.05, 1.5, 1.92), (0.05, 0.13, 1.5, 1.92)):
        for (p, q, r0, r1) in ((a, b, c0, c0 + 0.012), (a, b, c1 - 0.012, c1), (a, a + 0.012, c0 + 0.012, c1 - 0.012), (b - 0.012, b, c0 + 0.012, c1 - 0.012)):
            fq(g, p, q, yy, r0, r1, 'cyanL')
    fq(g, -0.06, 0.06, yy, 2.55, 2.6, 'scrC')
    for k in range(5):
        fq(g, 0.26, 0.4, yy, 2.6 - k * 0.1, 2.62 - k * 0.1, 'cyanL')
    text_front(g, 'MK-IX', 0.05, yy, -0.3, 2.72, 'scrC')
    make_glow('WL_Screen_LED', g)
    m = new(pal); wall_lab(m)                                                 # HELIXA logo: a double helix
    m.bx(-0.45, 0.45, -0.54, -0.5, 2.0, 3.4, 'graph', cull='k')
    for k in range(10):
        z = 2.2 + k * 0.105
        for ph, c in ((0.0, 'cyan'), (math.pi, 'teal')):
            x = math.sin(k * 0.55 + ph) * 0.11 - 0.3
            fq(m, x - 0.025, x + 0.025, -0.543 if ph == 0.0 else -0.546, z, z + 0.05, c)
    text_front(m, 'HELIXA', 0.14, -0.543, 0.12, 2.68, 'paper', maxw=0.48)
    text_front(m, 'ADVANCED SYSTEMS', 0.035, -0.543, 0.12, 2.55, 'cyanL', maxw=0.48)
    make('WL_Logo', m, ao)
    m = new(pal); wall_lab(m)                                                 # observation window (comic glass)
    m.bx(-0.5, 0.5, -0.56, -0.5, 1.0, 1.08, 'graph', hull='noside', cull='k')
    m.bx(-0.5, 0.5, -0.56, -0.5, 2.5, 2.58, 'graph', hull='noside', cull='k')
    fq(m, -0.5, 0.5, -0.506, 1.08, 2.5, 'glassD')
    fq(m, -0.5, 0.5, -0.509, 1.12, 2.46, 'glass')
    poly(m, [(-0.3, -0.512, 1.2), (-0.18, -0.512, 1.2), (0.1, -0.512, 2.38), (-0.02, -0.512, 2.38)], 'glassL', (0, -1, 0))
    poly(m, [(-0.08, -0.512, 1.2), (-0.03, -0.512, 1.2), (0.25, -0.512, 2.38), (0.2, -0.512, 2.38)], 'glassL', (0, -1, 0))
    make('WL_Window', m, ao)
    # ---- secure rooms art
    m = new(pal); wall_room(m)
    m.bx(-0.32, 0.32, -0.53, -0.5, 1.5, 2.1, 'hazY', cull='k')
    poly(m, [(-0.27, -0.533, 1.98), (-0.12, -0.533, 1.98), (-0.195, -0.533, 1.84)], 'black', (0, -1, 0))
    text_front(m, 'DANGER', 0.07, -0.533, 0.07, 1.92, 'black', maxw=0.32)
    text_front(m, 'HIGH VOLTAGE', 0.05, -0.533, 0.0, 1.6, 'black', maxw=0.56)
    make('WR_Sign', m, ao)
    m = new(pal); wall_room(m)                                                # breaker panel
    m.bx(-0.38, 0.38, -0.62, -0.5, 1.0, 2.3, 'steelL', cull='k')
    fq(m, -0.34, 0.34, -0.623, 1.05, 2.25, 'steel')
    for k in range(5):
        for i in range(6):
            x = -0.27 + i * 0.108
            fq(m, x - 0.03, x + 0.03, -0.626, 1.2 + k * 0.2, 1.3 + k * 0.2, 'graphD')
    fq(m, -0.1, 0.1, -0.626, 2.12, 2.2, 'paper')
    make('WR_Panel', m, ao)
    m = new(pal); wall_room(m); grille(m, -0.4, 0.4, 3.9, 4.8, 'steel', 'steelD'); make('WR_Vent', m, ao)


# ================================================================ breakable doors
# frame: [3, 2] (security, vault: x +/-1.5, through a 2-cell wall y +/-1) or [3, 1] (glass, cage: in a partition line);
# opening 2.4 m x 2.7 m; leaf pieces <Leaf>_Leaf / _Leaf_D1 / _Leaf_D2 / _Broken stand in the frame's own transform
def door_frame_2(m, body, trim, sign, sign_c, jamb='graph'):
    for sx in (-1, 1):
        a, b = sorted((sx * 1.2, sx * 1.5))
        m.bx(a, b, -1.0, 1.0, 0.0, DH, jamb, cull='b' + ('l' if sx < 0 else 'r'))
        for sy in (-1, 1):     # casing on both faces and the hazard foot of the reveal
            c0, c1 = sorted((sy * 1.0, sy * 1.045))
            m.bx(a, b, c0, c1, 0.0, DH + 0.15, trim, hull='full', cull='b' + ('l' if sx < 0 else 'r'))
    for sy in (-1, 1):
        c0, c1 = sorted((sy * 1.0, sy * 1.045))
        m.bx(-1.2, 1.2, c0, c1, DH, DH + 0.15, trim, hull='full')
    # header wall up to the ceiling, a graphite soffit
    m.bx(-1.5, 1.5, -1.0, 1.0, DH, H, body, hull='noside', cull='t')
    dq(m, -1.2, 1.2, -1.0, 1.0, DH - 0.003, 'graph')
    for sy in (-1, 1):
        face_q(m, sy, -1.5, 1.5, sy * 1.003, 5.3, H, 'graph')
        face_q(m, sy, -1.5, 1.5, sy * 1.003, 1.0 + 3.0, 4.012, 'joint')
    # reveal soffit and inner jamb faces: hazard bands at the foot
    for sx in (-1, 1):
        for k in range(5):
            y0 = -0.95 + k * 0.38
            if sx < 0:
                rq(m, -1.197, y0, y0 + 0.19, 0.0, 0.3, 'hazY')
            else:
                lq(m, 1.197, y0, y0 + 0.19, 0.0, 0.3, 'hazY')
    # sign plates over the opening on both faces, a card reader beside it
    for sy in (-1, 1):
        y = sy * 1.045
        c0, c1 = sorted((y, y + sy * 0.04))
        m.bx(-0.75, 0.75, c0, c1, 3.1, 3.55, sign_c, cull='k' if sy < 0 else 'f')
        if sy < 0:
            text_front(m, sign, 0.2, y - 0.043, 0.0, 3.2, 'paper', maxw=1.35)
        else:
            text_back(m, sign, 0.2, y + 0.043, 0.0, 3.2, 'paper', maxw=1.35)
        c0, c1 = sorted((y, y + sy * 0.05))
        m.bx(1.25, 1.42, c0, c1, 1.2, 1.48, 'graphD')
        face_q(m, sy, 1.29, 1.38, y + sy * 0.053, 1.38, 1.44, 'ledG')


def sec_leaf(m, dmg, rnd, x0=-1.2, x1=1.2, t=0.07):
    """two steel leaves meeting at x = 0; dmg 0 / 1 / 2. Face layers (3 mm apart): panels, overlays, glass, damage"""
    for i, (a, b) in enumerate(((x0, -0.004), (0.004, x1))):
        rot = 0.0
        if dmg == 1 and i == 1:
            rot = 2.5
        if dmg == 2:
            rot = -6.0 if i == 0 else 9.0
        torn = dmg == 2 and i == 0
        cx = (a + b) / 2
        m.push(cx, 0, rot)
        hw = (b - a) / 2
        if torn:   # the left leaf's inner top corner folded back
            m.bx(-hw, hw, -t, t, 0.01, 1.85, 'graph')
            m.bx(-hw, 0.0, -t, t, 1.85, DH - 0.01, 'graph')
            m.bxr(hw * 0.45, 0.16, 2.2, hw * 0.95, 0.06, 0.8, 'graphL', rot=(-35, 0, 8))
        else:
            m.bx(-hw, hw, -t, t, 0.01, DH - 0.01, 'graph')
        for s in (-1, 1):
            y = s * (t + 0.003)
            face_q(m, s, -hw + 0.08, hw - 0.08, y, 0.4, 1.3, 'graphL')
            face_q(m, s, -hw + 0.08, (-0.02 if torn else hw - 0.08), y, 1.4, 1.83 if torn else 2.55, 'graphL')
            face_q(m, s, -hw + 0.04, hw - 0.04, y, 0.05, 0.32, 'steel')
            yo = y + s * 0.003
            if not torn:
                face_q(m, s, -0.16, 0.16, yo, 1.62, 2.18, 'glassD')
                face_q(m, s, -0.13, 0.13, yo + s * 0.003, 1.65, 2.15, 'glass')
            c0, c1 = sorted((s * t, s * (t + 0.06)))
            m.bx(-hw + 0.12, hw - 0.12, c0, c1, 1.0, 1.06, 'chrome', hull='none')
            if i == 0:
                (text_front if s < 0 else text_back)(m, 'AUTHORIZED', 0.08, yo, 0.0, 0.7, 'hazY', font='cond', maxw=hw * 1.5)
            chevrons(m, -hw + 0.04, hw - 0.04, yo, 0.08, 0.28, 6, back=s > 0)
            if dmg:
                damage_marks(m, rnd, -hw + 0.05, hw - 0.05, 0.36, 1.8 if torn else 2.5, yo + s * 0.006, s, dmg)
        m.pop()
    if dmg == 2:     # a torn cable hanging out of the gap
        m.cy((0.0, 0.0, 1.6), 0.02, 0.02, 0.9, 'cabK', seg=5, rot=(0, 18, 0), hull='none')


def damage_marks(m, rnd, x0, x1, z0, z1, y, s, dmg, metal=True):
    """dents (dark crumpled patches with a bright scraped edge) and bullet holes on a leaf face, from plane y out
    (layers 3 mm apart; marks of one layer never overlap)"""
    n = 2 if dmg == 1 else 4
    r0 = 0.1 if dmg == 1 else 0.14
    for (cx, cz) in spots(rnd, n, x0 + 0.18, x1 - 0.18, z0 + 0.2, z1 - 0.2, 2.4 * r0 + 0.02):
        pts = []
        for j in range(6):
            a = j / 6 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
            pts.append((cx + math.cos(a) * r0 * rnd.uniform(0.75, 1.15), y, cz + math.sin(a) * r0 * rnd.uniform(0.75, 1.15)))
        poly(m, pts, 'steelL' if metal else 'glassL', (0, s, 0))
        poly(m, [(p[0] * 0.7 + cx * 0.3, y + s * 0.003, p[2] * 0.7 + cz * 0.3) for p in pts], 'graphD' if metal else 'glassD', (0, s, 0))
    for (cx, cz) in spots(rnd, 4 if dmg == 1 else 7, x0, x1, z0 + 0.05, z1 - 0.05, 0.09):
        r = rnd.uniform(0.02, 0.035)
        poly(m, [(cx + math.cos(j / 6 * 2 * math.pi) * r, y + s * 0.006, cz + math.sin(j / 6 * 2 * math.pi) * r) for j in range(6)], 'black', (0, s, 0))
    if dmg == 2:
        for (cx, cz) in spots(rnd, 2, x0 + 0.2, x1 - 0.2, z0 + 0.5, z1 - 0.4, 0.35):   # glowing torn holes
            pts = []
            for j in range(7):
                a = j / 7 * 2 * math.pi
                rr = rnd.uniform(0.07, 0.13)
                pts.append((cx + math.cos(a) * rr, y + s * 0.009, cz + math.sin(a) * rr))
            poly(m, pts, 'cabO', (0, s, 0))
            poly(m, [(p[0] * 0.6 + cx * 0.4, y + s * 0.012, p[2] * 0.6 + cz * 0.4) for p in pts], 'black', (0, s, 0))


def glass_cracks(m, rnd, x0, x1, z0, z1, y, s, n, big=False):
    """star cracks on a glass face: white zigzag spokes round an impact point (one polygon per spoke; each crack on
    its own layer, 6 mm apart)"""
    x0, x1 = x0 + 0.02, x1 - 0.02
    for k, (cx, cz) in enumerate(spots(rnd, n, x0 + 0.2, x1 - 0.2, z0 + 0.4, z1 - 0.4, 0.5)):
        yy = y + s * 0.0045 * k
        spokes = 7 if big else 5
        for j in range(spokes):
            a = j / spokes * 2 * math.pi + rnd.uniform(-0.2, 0.2)
            L = rnd.uniform(0.25, 0.6) * (1.6 if big else 1.0)
            pts = [(cx + math.cos(a) * 0.045, cz + math.sin(a) * 0.045)]
            for seg in range(3):
                aa = a + rnd.uniform(-0.3, 0.3)
                px, pz = pts[-1]
                pts.append((max(x0, min(x1, px + math.cos(aa) * L / 3)), max(z0 + 0.03, min(z1 - 0.03, pz + math.sin(aa) * L / 3))))
            strip(m, pts, 0.014, yy, 'paper', s)
        poly(m, [(cx + math.cos(j / 6 * 2 * math.pi) * 0.035, yy + s * 0.003, cz + math.sin(j / 6 * 2 * math.pi) * 0.035) for j in range(6)], 'paper', (0, s, 0))


def leaf_cols(t, x=1.2):
    return [cb(-x, -t, 0.0, x, t, DH)]


def build_doors(pal, ao):
    # ---- security door frames (sign variants share one leaf) and the leaf states
    for name, sign, sc in (('SecDoor', 'RESTRICTED', 'graph'), ('SecDoorUPS', 'UPS / POWER', 'fireR')):
        m = new(pal)
        door_frame_2(m, 'wallW', 'graphD', sign, sc)
        make(name, m, ao, cols=[cb(-1.5, -1.0, 0.0, -1.2, 1.0, DH), cb(1.2, -1.0, 0.0, 1.5, 1.0, DH)])
    for st, dmg in (('_Leaf', 0), ('_Leaf_D1', 1), ('_Leaf_D2', 2)):
        m = new(pal)
        sec_leaf(m, dmg, random.Random(5 + dmg))
        make('SecDoor' + st, m, ao, cols=leaf_cols(0.07) if dmg == 0 else None)
    m = new(pal)                     # what is left: stubs on the hinges, a leaf down in the reveal, a hanging cable
    rnd = random.Random(9)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.2, sx * 1.08))
        m.bx(a, b, -0.07, 0.07, 1.7, DH - 0.02, 'graph')
        m.bxr(sx * 1.0, -0.05, 1.55, 0.36, 0.05, 0.42, 'graphL', rot=(0, sx * 28, sx * 20))
        m.bx(a, b, -0.07, 0.07, 0.0, 0.42, 'graph')
    m.push(-0.15, -0.35, 9)
    m.bx(-0.6, 0.55, -0.55, 0.55, 0.0, 0.05, 'graph')
    uq(m, -0.5, 0.45, -0.45, 0.45, 0.053, 'graphL')
    uq(m, -0.5, 0.45, -0.5, -0.36, 0.056, 'hazY')
    m.pop()
    for k, (x, y) in enumerate(spots(rnd, 6, -1.0, 1.0, 0.65, 0.9, 0.2)):
        m.bx(x - 0.07, x + 0.07, y - 0.05, y + 0.05, 0.0, 0.02 + k * 0.004, rnd.choice(['graph', 'steel', 'graphL']), hull='none', cull='b')
    m.cy((0.3, 0.0, DH - 0.9), 0.02, 0.02, 0.9, 'cabK', seg=5, hull='none', caps=False)
    m.cy((0.38, 0.0, DH - 0.6), 0.02, 0.02, 0.6, 'cabR', seg=5, hull='none', caps=False)
    make('SecDoor_Broken', m, ao)

    # ---- vault door: massive bolted frame, a thick slab with a locking wheel
    m = new(pal)
    door_frame_2(m, 'wallG', 'steelD', 'VAULT 07', 'graphD', jamb='steelD')
    for sx in (-1, 1):
        for k in range(5):
            z = 0.35 + k * 0.5
            x = sx * 1.197
            for y in (0.3, -0.3):
                poly(m, [(x - sx * 0.001, y + math.cos(j / 6 * 2 * math.pi) * 0.05, z + math.sin(j / 6 * 2 * math.pi) * 0.05) for j in range(6)], 'black', (-sx, 0, 0))
    make('VaultDoor', m, ao, cols=[cb(-1.5, -1.0, 0.0, -1.2, 1.0, DH), cb(1.2, -1.0, 0.0, 1.5, 1.0, DH)])

    def vault_slab(m, dmg, rnd):
        t = 0.24
        m.bx(-1.19, 1.19, -t, t, 0.01, DH - 0.01, 'steel', bevel=False)
        for s in (-1, 1):
            y = s * (t + 0.003)
            face_q(m, s, -1.1, 1.1, y, 0.1, DH - 0.1, 'steelL')
            for zz in (0.18, DH - 0.18):     # rivet bands
                face_q(m, s, -1.0, 1.0, y + s * 0.003, zz - 0.02, zz + 0.02, 'steelD')
            # locking wheel on a hub
            c0 = s * t
            m.cy((0, c0, 1.35), 0.17, 0.17, 0.2, 'graph', seg=10, rot=(90 if s < 0 else -90, 0, 0))
            torus(m, 0, s * (t + 0.14), 1.35, 0.42, 0.04, 'chrome', seg=10, sides=4, axis='y')
            for k in range(4):
                a = k / 4 * 2 * math.pi + math.pi / 4
                m.beam((math.cos(a) * 0.16, s * (t + 0.14), 1.35 + math.sin(a) * 0.16), (math.cos(a) * 0.39, s * (t + 0.14), 1.35 + math.sin(a) * 0.39), 0.035, 'chrome')
            # bolt housings left and right
            for sx in (-1, 1):
                c1, c2 = sorted((s * t, s * (t + 0.06)))
                m.bx(sx * 0.95 - 0.08, sx * 0.95 + 0.08, c1, c2, 0.6, 2.1, 'steelD')
            (text_front if s < 0 else text_back)(m, 'HELIXA', 0.12, y + s * 0.003, 0.0, 2.15, 'graphD')
            if dmg:
                damage_marks(m, rnd, -1.05, 1.05, 0.3, 2.45, y + s * 0.006, s, dmg)
        if dmg == 2:
            m.bxr(0.75, -0.3, 2.35, 0.7, 0.06, 0.4, 'steelL', rot=(25, 0, -15))
    for st, dmg in (('_Leaf', 0), ('_Leaf_D1', 1), ('_Leaf_D2', 2)):
        m = new(pal)
        if dmg == 2:
            m.push(0.04, 0.0, 2.0)
        vault_slab(m, dmg, random.Random(31 + dmg))
        if dmg == 2:
            m.pop()
        make('VaultDoor' + st, m, ao, cols=leaf_cols(0.24) if dmg == 0 else None)
    # blown: the slab tipped back against the west jamb, bolts sheared, a wheel off on the floor
    m = new(pal)
    rnd = random.Random(33)
    m.push(-0.88, 0.1, 0)
    m.bxr(0.0, 0.0, 1.1, 0.48, 1.6, 2.2, 'steel', rot=(0, -14, 0))
    m.pop()
    torus(m, 0.45, -0.55, 0.05, 0.42, 0.04, 'chrome', seg=14, sides=5, axis='z')
    m.bx(1.05, 1.2, -0.25, 0.25, 0.0, DH - 0.02, 'steelD')
    for k, (x, y) in enumerate(spots(rnd, 5, -0.2, 1.0, -0.8, 0.8, 0.2)):
        m.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.0, 0.03 + k * 0.004, 'steelL', hull='none', cull='b')
    make('VaultDoor_Broken', m, ao, cols=[cb(-1.2, -0.9, 0.0, -0.66, 1.0, 2.25)])

    # ---- glass door: frosted double leaves in a partition line ([3, 1])
    def glass_frame(m, sign):
        for sx in (-1, 1):
            a, b = sorted((sx * 1.2, sx * 1.5))
            m.bx(a, b, -0.09, 0.09, 0.0, DH, 'steelL', cull='b')
        m.bx(-1.5, 1.5, -0.09, 0.09, DH, DH + 0.12, 'steelL')
        m.bx(-1.5, 1.5, -0.08, 0.08, DH + 0.12, H, 'wallW', hull='noside', cull='t')
        for s in (-1, 1):
            face_q(m, s, -1.5, 1.5, s * 0.083, 5.3, H, 'graph')
            c0, c1 = sorted((s * 0.083, s * 0.11))
            m.bx(-0.6, 0.6, c0, c1, 3.0, 3.3, 'graph', cull='k' if s < 0 else 'f')
            if s < 0:
                text_front(m, sign, 0.13, -0.113, 0.0, 3.08, 'cyanL', maxw=1.1)
            else:
                text_back(m, sign, 0.13, 0.113, 0.0, 3.08, 'cyanL', maxw=1.1)
    for name, sign in (('GlassDoor', 'MEETING 2B'), ('GlassDoorLab', 'PROTOTYPING')):
        m = new(pal)
        glass_frame(m, sign)
        make(name, m, ao, cols=[cb(-1.5, -0.09, 0.0, -1.2, 0.09, DH + 0.12), cb(1.2, -0.09, 0.0, 1.5, 0.09, DH + 0.12)])

    def glass_leaves(m, dmg, rnd):
        for (a, b) in ((-1.2, -0.004), (0.004, 1.2)):
            m.bx(a, b, -0.03, 0.03, 0.0, 0.12, 'steelL')
            m.bx(a, b, -0.03, 0.03, DH - 0.1, DH - 0.01, 'steelL')
            m.bx(a, a + 0.05, -0.03, 0.03, 0.12, DH - 0.1, 'steelL')
            m.bx(b - 0.05, b, -0.03, 0.03, 0.12, DH - 0.1, 'steelL')
            for s in (-1, 1):
                face_q(m, s, a + 0.05, b - 0.05, s * 0.015, 0.12, DH - 0.1, 'glass')
                face_q(m, s, a + 0.05, b - 0.05, s * 0.018, 1.0, 1.5, 'frost')
                for k in range(5):
                    x = a + 0.15 + k * (b - a - 0.3) / 4
                    face_q(m, s, x - 0.02, x + 0.02, s * 0.021, 1.2, 1.3, 'cyanL')
                poly(m, [(a + 0.2, s * 0.019, 1.7), (a + 0.32, s * 0.019, 1.7), (a + 0.62, s * 0.019, 2.5), (a + 0.5, s * 0.019, 2.5)], 'glassL', (0, s, 0))
                if dmg:
                    glass_cracks(m, rnd, a + 0.05, b - 0.05, 0.12, DH - 0.1, s * 0.024, s, 1 if dmg == 1 else 2, big=dmg == 2)
            m.bx(b - 0.3 if a < 0 else a + 0.06, b - 0.06 if a < 0 else a + 0.3, -0.07, 0.07, 1.0, 1.04, 'chrome', hull='none')
        # the inner glass sheet (seen edge-on through the frame) as one thin slab
        m.bx(-1.15, 1.15, -0.012, 0.012, 0.12, DH - 0.1, 'glassD', hull='none', cull='tb')
    for st, dmg in (('_Leaf', 0), ('_Leaf_D1', 1), ('_Leaf_D2', 2)):
        m = new(pal)
        glass_leaves(m, dmg, random.Random(41 + dmg))
        make('GlassDoor' + st, m, ao, cols=[cb(-1.2, -0.03, 0.0, 1.2, 0.03, DH)] if dmg == 0 else None)
    m = new(pal)                     # rails and a jagged fringe of glass left in the frames, shards on the floor
    rnd = random.Random(47)
    for (a, b) in ((-1.2, -0.004), (0.004, 1.2)):
        m.bx(a, b, -0.03, 0.03, 0.0, 0.12, 'steelL')
        m.bx(a, a + 0.05, -0.03, 0.03, 0.12, DH - 0.1, 'steelL')
        m.bx(b - 0.05, b, -0.03, 0.03, 0.12, DH - 0.1, 'steelL')
        m.bx(a, b, -0.03, 0.03, DH - 0.1, DH - 0.01, 'steelL')
        for s in (-1, 1):
            for (za, zb, up) in ((0.12, 0.45, 1), (DH - 0.45, DH - 0.1, -1)):
                xs = [a + 0.05 + (b - a - 0.1) * k / 6 for k in range(7)]
                base = za if up > 0 else zb
                for k in range(6):
                    tip = base + up * rnd.uniform(0.08, 0.32)
                    poly(m, [(xs[k], s * 0.015, base), (xs[k + 1], s * 0.015, base), ((xs[k] + xs[k + 1]) / 2 + rnd.uniform(-0.05, 0.05), s * 0.015, tip)], 'glass', (0, s, 0))
    for (x, y) in spots(rnd, 14, -1.3, 1.3, -0.45, 0.45, 0.2):
        r = rnd.uniform(0.04, 0.09)
        a0 = rnd.uniform(0, 3)
        poly(m, [(x + math.cos(a0 + j * 2.1) * r, y + math.sin(a0 + j * 2.1) * r, 0.012) for j in range(3)], rnd.choice(['glass', 'glassL']), (0, 0, 1))
    make('GlassDoor_Broken', m, ao)

    # ---- cage gate: welded mesh leaves in a cage run ([3, 1])
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.36, sx * 1.5))
        m.bx(a, b, -0.07, 0.07, 0.0, 3.0, 'graph', cull='b')
    m.bx(-1.36, 1.36, -0.06, 0.06, 2.86, 3.0, 'graph')
    for s in (-1, 1):
        c0, c1 = sorted((s * 0.07, s * 0.1))
        m.bx(-0.4, 0.4, c0, c1, 2.88, 2.98, 'hazY', hull='none', cull='k' if s < 0 else 'f')
    text_front(m, 'CAGE', 0.06, -0.103, 0.0, 2.9, 'black')
    text_back(m, 'CAGE', 0.06, 0.103, 0.0, 2.9, 'black')
    make('CageGate', m, ao, cols=[cb(-1.5, -0.07, 0.0, -1.36, 0.07, 3.0), cb(1.36, -0.07, 0.0, 1.5, 0.07, 3.0)])

    def mesh_leaf(m, a, b, z0, z1, rot=0.0, cx=None, holes=()):
        cx = (a + b) / 2 if cx is None else cx
        hw = (b - a) / 2
        m.push(cx, 0, rot)
        for (p, q, r0, r1) in ((-hw + 0.05, hw - 0.05, z0, z0 + 0.05), (-hw + 0.05, hw - 0.05, z1 - 0.05, z1), (-hw, -hw + 0.05, z0, z1), (hw - 0.05, hw, z0, z1),
                               (-hw + 0.05, hw - 0.05, (z0 + z1) / 2 - 0.025, (z0 + z1) / 2 + 0.025)):
            m.bx(p, q, -0.025, 0.025, r0, r1, 'graph')
        n = int((2 * hw - 0.1) / 0.18)
        for i in range(1, n):
            x = -hw + 0.05 + i * (2 * hw - 0.1) / n
            if any(abs(x - hx) < hr for (hx, hz, hr) in holes):
                continue
            fq(m, x - 0.008, x + 0.008, -0.008, z0 + 0.05, z1 - 0.05, 'mesh')
            bq(m, x - 0.008, x + 0.008, 0.008, z0 + 0.05, z1 - 0.05, 'mesh')
        k = int((z1 - z0 - 0.1) / 0.18)
        for i in range(1, k):
            z = z0 + 0.05 + i * (z1 - z0 - 0.1) / k
            if any(abs(z - hz) < hr for (hx, hz, hr) in holes):
                continue
            fq(m, -hw + 0.05, hw - 0.05, -0.004, z - 0.008, z + 0.008, 'mesh')
            bq(m, -hw + 0.05, hw - 0.05, 0.004, z - 0.008, z + 0.008, 'mesh')
        m.pop()
    for st, dmg in (('_Leaf', 0), ('_Leaf_D1', 1), ('_Leaf_D2', 2)):
        m = new(pal)
        if dmg == 0:
            mesh_leaf(m, -1.34, -0.01, 0.03, 2.8)
            mesh_leaf(m, 0.01, 1.34, 0.03, 2.8)
        elif dmg == 1:
            mesh_leaf(m, -1.34, -0.01, 0.03, 2.8, holes=((-0.3, 1.2, 0.12),))
            mesh_leaf(m, 0.01, 1.34, 0.03, 2.8, rot=3.0)
        else:
            mesh_leaf(m, -1.34, -0.01, 0.06, 2.8, rot=-7.0, holes=((-0.4, 1.0, 0.2), (-0.2, 1.8, 0.15)))
            mesh_leaf(m, 0.01, 1.34, 0.12, 2.7, rot=10.0, holes=((0.3, 1.4, 0.22),))
        # padlock hasp on the meeting stiles
        m.bx(-0.075, 0.075, -0.06, 0.06, 1.25, 1.4, 'steelL' if dmg < 2 else 'steelD')
        m.bx(-0.04, 0.04, -0.1, -0.06, 1.12, 1.25, 'hazY')
        make('CageGate' + st, m, ao, cols=[cb(-1.36, -0.03, 0.0, 1.36, 0.03, 2.8)] if dmg == 0 else None)
    m = new(pal)                     # one leaf torn off and lying flat, the other bent open on its hinge
    m.push(1.36, 0.0, -70)
    mesh_leaf(m, -1.33, 0.0, 0.05, 2.75)
    m.pop()
    # the torn leaf flat on the floor (a mesh panel 4 cm high)
    for i in range(9):
        x = -1.25 + i * 0.15
        m.bx(x - 0.008, x + 0.008, -0.93, 0.33, 0.0, 0.016, 'mesh', hull='none', cull='b')
    for k in range(9):
        y = -0.9 + k * 0.15
        m.bx(-1.25, -0.05, y - 0.008, y + 0.008, 0.016, 0.032, 'mesh', hull='none', cull='b')
    for (p, q, r0, r1) in ((-1.25, -0.05, -0.98, -0.93), (-1.25, -0.05, 0.33, 0.38), (-1.3, -1.25, -0.98, 0.38), (-0.05, 0.0, -0.98, 0.38)):
        m.bx(p, q, r0, r1, 0.0, 0.045, 'graph', cull='b')
    make('CageGate_Broken', m, ao, cols=[cb(1.3, -1.36, 0.0, 1.5, 0.08, 2.75)])


# ================================================================ partitions (linked runs like rails)
def build_partitions(pal, ao):
    # glass: 0 - 2.7 frosted-band glass between aluminium mullions, a white bulkhead from 2.85 to the ceiling
    def glass_part(m, a, b, post_l, post_r):
        m.bx(a, b, -0.06, 0.06, 0.0, 0.1, 'steelL', hull='noside')
        m.bx(a, b, -0.06, 0.06, DH, DH + 0.12, 'steelL', hull='noside')
        m.bx(a, b, -0.07, 0.07, DH + 0.12, H, 'wallW', hull='noside', cull='t')
        for s in (-1, 1):
            face_q(m, s, a, b, s * 0.073, 5.3, H, 'graph')
            face_q(m, s, a, b, s * 0.012, 0.1, DH, 'glass')
            face_q(m, s, a, b, s * 0.015, 1.05, 1.45, 'frost')
            face_q(m, s, a, b, s * 0.018, 1.22, 1.27, 'cyanL')
        m.bx(a, b, -0.009, 0.009, 0.1, DH, 'glassD', hull='none', cull='tb')
    m = new(pal); glass_part(m, -0.5, 0.5, 0, 0)
    for s in (-1, 1):
        poly(m, [(-0.3, s * 0.016, 1.7), (-0.18, s * 0.016, 1.7), (0.12, s * 0.016, 2.55), (0.0, s * 0.016, 2.55)], 'glassL', (0, s, 0))
    make('GlassFull', m, ao, cols=[cb(-0.5, -0.07, 0.0, 0.5, 0.07, H)])
    m = new(pal); glass_part(m, 0.08, 0.5, 0, 0)
    make('GlassHalf', m, ao, cols=[cb(0.0, -0.07, 0.0, 0.5, 0.07, H)])
    m = new(pal)
    m.bx(-0.08, 0.08, -0.08, 0.08, 0.0, DH + 0.14, 'steelL')
    make('GlassPost', m, ao)
    # cage: welded mesh panels between square posts, 3 m tall with a top rail (colocation cages)
    def cage_part(m, a, b):
        for (p, q, r0, r1) in ((a, b, 0.03, 0.08), (a, b, 2.92, 3.0), (a, b, 1.48, 1.53)):
            m.bx(p, q, -0.025, 0.025, r0, r1, 'graph', hull='noside')
        n = int(round((b - a) / 0.18))
        for i in range(n):
            x = a + (i + 0.5) * (b - a) / n
            fq(m, x - 0.008, x + 0.008, -0.008, 0.08, 2.92, 'mesh')
            bq(m, x - 0.008, x + 0.008, 0.008, 0.08, 2.92, 'mesh')
        for k in range(1, 12):
            z = 0.08 + k * 2.84 / 12
            fq(m, a, b, -0.004, z - 0.008, z + 0.008, 'mesh')
            bq(m, a, b, 0.004, z - 0.008, z + 0.008, 'mesh')
    m = new(pal); cage_part(m, -0.5, 0.5)
    make('CageFull', m, ao, cols=[cb(-0.5, -0.04, 0.0, 0.5, 0.04, 3.0)])
    m = new(pal); cage_part(m, 0.05, 0.5)
    make('CageHalf', m, ao, cols=[cb(0.0, -0.04, 0.0, 0.5, 0.04, 3.0)])
    m = new(pal)
    m.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 3.02, 'graph')
    make('CagePost', m, ao, cols=[cb(-0.05, -0.05, 0.0, 0.05, 0.05, 3.02)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.5, sx * 1.86))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'graph', cull='b')
        for fy in (-1, 1):
            face_q(m, fy, a + 0.08, b - 0.08, fy * 0.623, 0.3, 3.0, 'cyan')
    m.bx(-1.86, 1.86, -0.62, 0.62, 3.3, 3.8, 'graphD')
    for fy in (-1, 1):
        face_q(m, fy, -1.8, 1.8, fy * 0.623, 3.45, 3.52, 'cyan')
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.8, H, 'wallW', cull='t')
    for fy in (-1, 1):
        y = fy * 0.45
        face_q(m, fy, -2.48, 2.48, fy * 0.453, 5.3, H, 'graph')
        c0, c1 = sorted((y, y + fy * 0.06))
        m.bx(-1.3, 1.3, c0, c1, 4.1, 5.0, 'teal')
        yy = y + fy * 0.063
        if fy < 0:
            text_front(m, 'HELIXA', 0.42, yy, 0.0, 4.3, 'paper', font='display', maxw=2.3)
        else:
            text_back(m, 'HELIXA', 0.42, yy, 0.0, 4.3, 'paper', font='display', maxw=2.3)
    make('GateFrame', m, ao, cols=[cb(-1.86, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.86, 0.62, 3.3)])
    m = new(pal)
    Hs, n = 3.05, 10
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.03), 'steelL' if i % 2 else 'wallW', bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'graphD' if k % 2 else 'hazY', bevel=False)
    m.box((0, -0.06, 1.7), (2.9, 0.02, 0.06), 'cyan', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor walls (1 m along Blender Y, inner face +X)
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'wallW', hull='noend', cull='t')
        m.bx(0.25, 0.29, -0.5, 0.5, 0.0, 0.16, 'graph', hull='noend', cull='b')
        rq(m, 0.253, -0.5, 0.5, 1.0, 1.08, 'teal')
        rq(m, 0.253, -0.5, 0.5, 2.6, 2.614, 'joint')
        m.bx(0.25, 0.3, -0.5, 0.5, 5.3, H, 'graph', hull='noend', cull='t')
        if name == 'TrailWall_B':   # wall light
            m.bx(0.25, 0.32, -0.3, 0.3, 2.9, 3.0, 'graph')
            rq(m, 0.323, -0.28, 0.28, 2.91, 2.99, 'glow')
        elif name == 'TrailWall_C':   # chevrons pointing on (+Y)
            for k in range(2):
                y0 = -0.35 + k * 0.4
                pts = [(y0, 1.3), (y0 + 0.14, 1.3), (y0 + 0.3, 1.5), (y0 + 0.14, 1.7), (y0, 1.7), (y0 + 0.16, 1.5)]
                poly(m, [(0.256, p[0], p[1]) for p in pts[:3] + [pts[5]]], 'cyan', (1, 0, 0))
                poly(m, [(0.256, p[0], p[1]) for p in [pts[5], pts[2], pts[3], pts[4]]], 'cyan', (1, 0, 0))
        make(name, m, ao)
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'graph', seg=20)
    ring(m, 0, 0, 0.103, 0.95, 1.12, 'cyan', seg=20)
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ ceiling fittings (hang from z = 0 = the ceiling)
def build_ceiling(pal, ao):
    # yellow fibre runner tray at 3.1 m above the floor (2.9 under the ceiling), on two drop rods
    m = new(pal)
    z0 = -(H - 3.1)
    m.bx(-0.5, 0.5, -0.15, 0.15, z0, z0 + 0.03, 'cabY', hull='noside', cull='lr')
    for s in (-1, 1):
        c0, c1 = sorted((s * 0.17, s * 0.15))
        m.bx(-0.5, 0.5, c0, c1, z0, z0 + 0.12, 'cabY', hull='noside', cull='lr')
    m.bx(-0.012, 0.012, 0.188, 0.212, z0 - 0.03, 0.0, 'steelD', hull='none', cull='tb')
    m.bx(-0.02, 0.02, -0.2, 0.188, z0 - 0.03, z0, 'steelD', hull='none', cull='l')
    make('Tray', m, ao)
    # steel ladder tray at 3.7 m with bundled black / blue cables
    m = new(pal)
    z0 = -(H - 3.7)
    for s in (-1, 1):
        c0, c1 = sorted((s * 0.3, s * 0.27))
        m.bx(-0.5, 0.5, c0, c1, z0, z0 + 0.1, 'steel', hull='noside', cull='lr')
    m.bx(-0.02, 0.02, -0.27, 0.27, z0, z0 + 0.025, 'steel', hull='none', cull='kf')
    m.bx(-0.5, 0.5, -0.24, 0.02, z0 + 0.025, z0 + 0.11, 'cabK', hull='noside', cull='lrb')
    m.bx(-0.5, 0.5, 0.04, 0.2, z0 + 0.025, z0 + 0.09, 'cabB', hull='noside', cull='lrb')
    m.bx(-0.012, 0.012, 0.302, 0.326, z0, 0.0, 'steelD', hull='none', cull='tb')
    make('Ladder', m, ao)
    # linear LED light on the ceiling (glow companion: its lens)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.06, 0.06, -0.09, 0.0, 'graphD', hull='noside')
    make('LightL', m, ao)
    g = new(pal)
    dq(g, -0.5, 0.5, -0.045, 0.045, -0.093, 'glow')
    make_glow('LightL_LED', g)
    # red sprinkler main at 5.4 m with a drop head every metre
    m = new(pal)
    z0 = -(H - 5.4)
    m.cy((-0.5, 0.25, z0), 0.045, 0.045, 1.0, 'fireR', seg=8, rot=(0, 90, 0), caps=False)
    m.cy((0.0, 0.25, z0 - 0.25), 0.015, 0.015, 0.25, 'chrome', seg=5, hull='none', caps=False)
    m.cy((0.0, 0.25, z0 - 0.3), 0.04, 0.02, 0.05, 'chrome', seg=6, hull='none')
    make('Pipe', m, ao)
    # busbar trunking with orange tap-off boxes at 3.4 m
    m = new(pal)
    z0 = -(H - 3.4)
    m.bx(-0.5, 0.5, -0.1, 0.1, z0, z0 + 0.16, 'steelL', hull='noside')
    fq(m, -0.5, 0.5, -0.103, z0 + 0.06, z0 + 0.1, 'cabO')
    m.bx(-0.15, 0.15, -0.12, 0.12, z0 - 0.3, z0, 'cabO')
    m.cy((0.0, 0.0, z0 - 0.3 - 0.25), 0.03, 0.03, 0.25, 'black', seg=5, hull='none')
    m.bx(-0.012, 0.012, -0.012, 0.012, z0 + 0.16, 0.0, 'steelD', hull='none')
    make('Busway', m, ao)
    # smoke detector and CCTV dome
    m = new(pal)
    m.cy((0, 0, -0.06), 0.09, 0.08, 0.06, 'wallW', seg=10)
    m.cy((0.25, 0.0, -0.12), 0.08, 0.09, 0.08, 'graph', seg=10)
    m.sp((0.25, 0.0, -0.12), 0.07, 'black', seg=(8, 4))
    make('Sensors', m, ao)
    # lab ceiling: a light panel in a white baffle (lab ceiling grid) -- glow companion lens
    m = new(pal)
    m.bx(-0.48, 0.48, -0.48, 0.48, -0.05, 0.0, 'wallW', hull='noside')
    make('LabPanel', m, ao)
    g = new(pal)
    dq(g, -0.4, 0.4, -0.4, 0.4, -0.053, 'glow')
    make_glow('LabPanel_LED', g)


# ================================================================ floor finishes (flat, no collision)
def build_floors(pal, ao):
    # cold aisle: perforated raised-floor tile
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'tile')
    for i in range(3):
        for k in range(3):
            x, y = -0.3 + i * 0.3, -0.3 + k * 0.3
            uq(m, x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.011, 'perf')
    make('Floor_Perf', m, ao)
    # hot aisle: darker tiles with a seam
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'tileD')
    make('Floor_Hot', m, ao)
    # lab: white epoxy with a cyan inlay line (along X)
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'wallL')
    make('Floor_Lab', m, ao)
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'wallL')
    uq(m, -0.5, 0.5, -0.04, 0.04, 0.011, 'cyan')
    make('Floor_LabLine', m, ao)
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'carpet')
    make('Floor_Carpet', m, ao)
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'graphL')
    make('Floor_Dark', m, ao)
    m = new(pal)             # secure rooms: grey anti-static tiles with dark seams
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'wallG')
    uq(m, -0.5, -0.47, -0.5, 0.5, 0.011, 'joint')
    uq(m, -0.47, 0.5, -0.5, -0.47, 0.011, 'joint')
    make('Floor_Secure', m, ao)
    m = new(pal)             # secure room hazard edge
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'tileD')
    for k in range(4):
        uq(m, -0.5 + k * 0.25, -0.375 + k * 0.25, -0.5, 0.5, 0.011, 'hazY' if k % 2 == 0 else 'graphD')
    make('Floor_Hazard', m, ao)
    m = new(pal)             # walkway line (data hall main aisle)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.008, 'tile')
    uq(m, -0.5, 0.5, -0.06, 0.06, 0.011, 'teal')
    make('Floor_Line', m, ao)
    # the HELIXA floor emblem [4, 4] (lobby / lab centre)
    m = new(pal)
    disc(m, 0, 0, 0.009, 1.9, 'graph', seg=24)
    ring(m, 0, 0, 0.012, 1.6, 1.75, 'cyan', seg=24)
    for k in range(18):
        a = k * 0.35
        for ph, c in ((0.0, 'cyan'), (math.pi, 'teal')):
            x = math.sin(a + ph) * 0.35
            y = -1.1 + k * 0.13
            uq(m, x - 0.05, x + 0.05, y - 0.04, y + 0.04, 0.012 if ph == 0.0 else 0.015, c)
    make('Floor_Emblem', m, ao)
