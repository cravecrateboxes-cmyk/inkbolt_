"""kit-parking structure: wall modules per level and storey, corner posts, gate piers, columns, deck-edge rails,
ramps and stairs, the gate portal, shutter, corridor walls and the exit hatch (see parking_base.py for conventions)."""
import math

from parking_base import *  # noqa: F401,F403
import parking_base as B


def inset(prof, d):
    """convex (y, z) polygon moved d inward (edges offset toward the centroid, corners re-intersected)"""
    n = len(prof)
    cy = sum(p[0] for p in prof) / n
    cz = sum(p[1] for p in prof) / n
    lines = []
    for i in range(n):
        a, b = prof[i], prof[(i + 1) % n]
        dy, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dy, dz)
        ny, nz = -dz / L, dy / L
        if (cy - a[0]) * ny + (cz - a[1]) * nz < 0:
            ny, nz = -ny, -nz
        lines.append(((a[0] + ny * d, a[1] + nz * d), (dy, dz)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            out.append(p2)
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


# ================================================================ walls
def span(trim):
    """x extent of a module's proud details: full, or stopping 0.32 m short of the corner on its -X (L) / +X (R) end
    (the corner post covers the rest, so the two walls' details never meet in the corner square)"""
    return (-0.18, 0.5) if trim == 'L' else (-0.5, 0.18) if trim == 'R' else (-0.5, 0.5)


def kerb(m, z0, z1=None, trim=None):
    """yellow / black wheel kerb along the wall foot (or the deck line)"""
    z1 = z0 + 0.2 if z1 is None else z1
    x0, x1 = span(trim)
    m.bx(x0, x1, -0.6, -0.5, z0, z1, 'lineY', hull='noside', cull='k' + ('b' if z0 < 0.01 else ''))
    for i in (0, 2):
        a, b = max(x0, -0.5 + i * 0.25), min(x1, -0.25 + i * 0.25)
        if b - a > 0.01:
            fq(m, a, b, -0.603, z0, z1, 'ink')


def wall_lo(m, c, cl, dado=True, trim=None):
    x0, x1 = span(trim)
    fq(m, -0.5, 0.5, -0.5, 0.0, DECK, 'conc')
    if dado:
        fq(m, -0.5, 0.5, -0.503, 0.3, 1.4, c)
        fq(m, -0.5, 0.5, -0.503, 1.48, 1.58, cl)
    fq(m, -0.5, 0.5, -0.503, 2.45, 2.48, 'concW')
    m.bx(x0, x1, -0.58, -0.5, 3.25, 3.57, 'concL', hull='noside', cull='k')


def wall_up(m, c, cl, trim=None):
    x0, x1 = span(trim)
    fq(m, -0.5, 0.5, -0.5, DECK, H, 'conc')
    kerb(m, DECK, DECK + 0.18, trim)
    fq(m, -0.5, 0.5, -0.503, 3.9, 5.0, c)
    fq(m, -0.5, 0.5, -0.503, 5.08, 5.18, cl)
    fq(m, -0.5, 0.5, -0.503, 6.0, 6.03, 'concW')
    m.bx(x0, x1, -0.7, -0.5, 6.72, H, 'concL', hull='noside', cull='kt')


def wall_arrow(m, z, c='paper'):
    """white arrow pointing +X painted over the colour band (centre height z)"""
    y = -0.506
    fq(m, -0.4, 0.1, y, z - 0.13, z + 0.13, c)
    poly(m, [(0.1, y - 0.002, z - 0.3), (0.42, y - 0.002, z), (0.1, y - 0.002, z + 0.3)], c, (0, -1, 0))


def wall_pier(m, c, cl, z0, z1, ext=True):
    m.bx(-0.36, 0.36, -0.78, -0.5, z0, z1, 'concL', cull='k' + ('b' if z0 < 0.01 else ''))
    m.bx(-0.365, 0.365, -0.785, -0.5, z0 + 0.3, z0 + 1.4, c, hull='none', cull='kbt')
    m.bx(-0.365, 0.365, -0.785, -0.5, z0 + 1.48, z0 + 1.58, cl, hull='none', cull='kbt')
    if ext:   # fire extinguisher on a bracket
        m.cy((0, -0.88, z0 + 0.55), 0.085, 0.085, 0.42, 'pipeR', seg=8)
        m.cy((0, -0.88, z0 + 0.97), 0.05, 0.03, 0.08, 'ink', seg=6, hull='none')
        m.bx(-0.03, 0.03, -0.8, -0.785, z0 + 0.62, z0 + 0.9, 'steelD', hull='none')


def build_walls(pal, ao):
    for L, (c, cl) in LEVELS.items():
        # ---- lower storey (0 - 3.6)
        for v in ('Plain', 'Num', 'Arrow', 'Pipe', 'Pier', 'Door', 'Lift', 'Dock'):
            m = new(pal)
            wall_lo(m, c, cl, dado=v not in ('Door', 'Lift'))
            if v not in ('Door', 'Lift'):
                kerb(m, 0.0)
            if v == 'Num':
                fq(m, -0.46, 0.46, -0.503, 1.72, 2.36, 'concL')
                text_front(m, L, 0.1, -0.506, 0.0, 1.79, c)
            elif v == 'Arrow':
                wall_arrow(m, 0.85)
                fq(m, -0.44, 0.44, -0.503, 1.75, 2.1, 'exitG')
                text_front(m, 'EXIT', 0.045, -0.506, 0.0, 1.81, 'paper')
            elif v == 'Pipe':
                m.cy((0.32, -0.64, 0.0), 0.07, 0.07, DECK, 'pipeB', seg=8, caps=False)
                for z in (1.9, 3.0):
                    m.bx(0.22, 0.42, -0.72, -0.5, z, z + 0.06, 'steelD', hull='none')
                m.bx(-0.44, 0.06, -0.74, -0.5, 0.85, 1.75, 'pipeR', cull='k')
                m.cy((-0.19, -0.74, 1.3), 0.3, 0.3, 0.006, 'ink', seg=12, rot=(90, 0, 0), hull='none')
                m.cy((-0.19, -0.746, 1.3), 0.22, 0.22, 0.006, 'pipeR', seg=12, rot=(90, 0, 0), hull='none')
                m.cy((-0.19, -0.752, 1.3), 0.07, 0.07, 0.006, 'chrome', seg=8, rot=(90, 0, 0), hull='none')
                fq(m, -0.4, 0.02, -0.743, 1.6, 1.7, 'paper')
            elif v == 'Pier':
                wall_pier(m, c, cl, 0.0, 3.54)
            elif v == 'Door':   # stairwell fire door with a running-man exit sign
                for x0, x1 in ((-0.5, -0.43), (0.43, 0.5)):
                    m.bx(x0, x1, -0.58, -0.5, 0.0, 2.3, 'steelD', hull='noside', cull='kb')
                m.bx(-0.43, 0.43, -0.58, -0.5, 2.22, 2.3, 'steelD', hull='none', cull='k')
                fq(m, -0.43, 0.43, -0.503, 0.0, 2.22, 'signB')
                fq(m, -0.15, 0.15, -0.506, 1.35, 1.9, 'glass')
                m.bx(-0.33, 0.33, -0.6, -0.506, 1.0, 1.07, 'chrome', hull='none')
                fq(m, -0.5, 0.5, -0.503, 2.32, 2.42, cl)
                m.bx(-0.3, 0.3, -0.64, -0.5, 2.48, 2.78, 'exitG', cull='k')
                text_front(m, 'EXIT', 0.033, -0.643, 0.11, 2.55, 'paper')
                fq(m, -0.27, -0.17, -0.643, 2.52, 2.74, 'paper')
                fq(m, -0.5, 0.5, -0.503, 2.95, 3.05, c)
            elif v == 'Lift':   # lift doors, floor indicator
                for x0, x1 in ((-0.5, -0.43), (0.43, 0.5)):
                    m.bx(x0, x1, -0.6, -0.5, 0.0, 2.45, 'steelD', hull='noside', cull='kb')
                m.bx(-0.43, 0.43, -0.6, -0.5, 2.35, 2.45, 'steelD', hull='none', cull='k')
                fq(m, -0.43, 0.43, -0.503, 0.0, 2.35, 'chrome')
                fq(m, -0.006, 0.006, -0.506, 0.0, 2.35, 'steelD')
                fq(m, -0.43, -0.012, -0.506, 1.0, 1.06, 'galv')
                fq(m, 0.012, 0.43, -0.506, 1.0, 1.06, 'galv')
                m.bx(-0.22, 0.22, -0.6, -0.5, 2.55, 2.8, 'ink', cull='k')
                text_front(m, L, 0.04, -0.603, 0.0, 2.58, 'litA')
                fq(m, -0.5, 0.5, -0.503, 2.95, 3.05, c)
            elif v == 'Dock':   # roller shutter over the dock (dock top 1.2 m)
                fq(m, -0.5, 0.5, -0.506, 1.62, 3.2, 'galv')
                for k in range(8):
                    fq(m, -0.5, 0.5, -0.509, 1.72 + k * 0.19, 1.75 + k * 0.19, 'steel')
                fq(m, -0.5, 0.5, -0.509, 1.62, 1.7, 'ink')
                m.bx(-0.496, 0.496, -0.78, -0.5, 3.18, 3.5, 'galv', hull='noside', cull='k')
            make('Lo_%s_%s' % (L, v), m, ao)
        # ---- upper storey (3.6 - 7.0)
        for v in ('Plain', 'Num', 'Arrow', 'Pipe', 'Pier'):
            m = new(pal)
            wall_up(m, c, cl)
            if v == 'Num':
                fq(m, -0.46, 0.46, -0.503, 5.32, 5.96, 'concL')
                text_front(m, L, 0.1, -0.506, 0.0, 5.39, c)
            elif v == 'Arrow':
                wall_arrow(m, 4.45)
                fq(m, -0.44, 0.44, -0.503, 5.35, 5.7, 'exitG')
                text_front(m, 'EXIT', 0.045, -0.506, 0.0, 5.41, 'paper')
            elif v == 'Pipe':
                m.cy((0.32, -0.64, DECK + 0.18), 0.07, 0.07, H - DECK - 0.18, 'pipeB', seg=8, caps=False)
                m.cy((-0.25, -0.64, DECK + 0.18), 0.06, 0.06, H - DECK - 0.18, 'pipeR', seg=8, caps=False)
                m.cy((-0.25, -0.64, 4.6), 0.1, 0.1, 0.18, 'pipeR', seg=8)
                m.bx(-0.33, -0.17, -0.84, -0.74, 4.65, 4.73, 'chrome', hull='none')
                for z in (4.2, 5.6, 6.4):
                    m.bx(-0.35, 0.42, -0.72, -0.5, z, z + 0.06, 'steelD', hull='none')
            elif v == 'Pier':
                wall_pier(m, c, cl, DECK + 0.18, 6.72, ext=False)
            make('Up_%s_%s' % (L, v), m, ao)
    # beside the split-level platform (1.8 m, solid): the kerb and the colour band sit over the platform
    for L, (c, cl) in LEVELS.items():
        m = new(pal)
        wall_lo(m, c, cl, dado=False)
        kerb(m, 1.8, 1.98)
        fq(m, -0.5, 0.5, -0.506, 2.05, 2.95, c)
        fq(m, -0.5, 0.5, -0.506, 3.02, 3.1, cl)
        make('Lo_%s_Split' % L, m, ao)
    # beside a corner: plain modules whose proud details stop short of the corner post (EndL: post on the -X side)
    for L, (c, cl) in LEVELS.items():
        for t in ('L', 'R'):
            m = new(pal)
            wall_lo(m, c, cl, trim=t)
            kerb(m, 0.0, trim=t)
            make('Lo_%s_End%s' % (L, t), m, ao)
            m = new(pal)
            wall_up(m, c, cl, trim=t)
            make('Up_%s_End%s' % (L, t), m, ao)
    # corner posts (fill the notch where two walls meet): hazard bands, full height
    for name, sx, sy in (('NW', 1, -1), ('NE', -1, -1), ('SW', 1, 1), ('SE', -1, 1)):
        m = new(pal)
        x0, x1 = sorted((sx * 0.496, sx * 0.8))
        y0, y1 = sorted((sy * 0.496, sy * 0.8))
        m.bx(x0, x1, y0, y1, 0.0, H, 'concL', cull='bt')
        for z0 in (0.0, DECK):
            for k in range(4):
                m.bx(x0 - 0.004, x1 + 0.004, y0 - 0.004, y1 + 0.004, z0 + 0.2 + k * 0.3, z0 + 0.35 + k * 0.3, 'lineY' if k % 2 else 'ink', hull='none', cull='tb')
        make('Corner_' + name, m, ao)
    # beside a gate: a full-height pier with hazard bands and a parking sign pointing down a level
    m = new(pal)
    fq(m, -0.5, 0.5, -0.5, 0.0, H, 'conc')
    m.bx(-0.42, 0.42, -0.72, -0.5, 0.0, H, 'concL', cull='kbt')
    for k in range(6):
        fq(m, -0.42, 0.42, -0.723, 0.2 + k * 0.3, 0.35 + k * 0.3, 'lineY' if k % 2 else 'ink')
    fq(m, -0.36, 0.36, -0.723, 3.0, 5.6, 'signB')
    text_front(m, 'P', 0.12, -0.726, 0.0, 4.6, 'paper')
    poly(m, [(-0.25, -0.726, 4.3), (0.25, -0.726, 4.3), (0.0, -0.726, 3.75)], 'paper', (0, -1, 0))
    fq(m, -0.06, 0.06, -0.726, 4.3, 4.5, 'paper')
    make('GateSide', m, ao)


# ================================================================ columns, rails
CODES = ['A1', 'A4', 'C2', 'D7']


def column(m, h, code):
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, h, 'conc', cull='tb')
    m.bx(-0.305, 0.305, -0.305, 0.305, 0.0, 1.2, 'lvB', hull='none', cull='tb')
    m.bx(-0.305, 0.305, -0.305, 0.305, 1.28, 1.36, 'lvBL', hull='none', cull='tb')
    for sx in (-1, 1):   # yellow corner guards
        for sy in (-1, 1):
            x0, x1 = sorted((sx * 0.26, sx * 0.315))
            y0, y1 = sorted((sy * 0.26, sy * 0.315))
            m.bx(x0, x1, y0, y1, 0.0, 0.9, 'lineY', hull='none', cull='b')
    # code plaques front and back, a P sign on the sides
    m.bx(-0.2, 0.2, -0.32, 0.32, 1.62, 2.02, 'paper', hull='none')
    text_front(m, code, 0.05, -0.323, 0.0, 1.695, 'ink')
    text_back(m, code, 0.05, 0.323, 0.0, 1.695, 'ink')
    m.bx(-0.32, 0.32, -0.16, 0.16, 2.2, 2.52, 'signB', hull='none')
    for (a, b, c0, c1) in word_rects('P', 0.05, 0.0, 2.235):
        rq(m, 0.325, a, b, c0, c1, 'paper')
        lq(m, -0.325, -b, -a, c0, c1, 'paper')
    m.bx(-0.32, 0.32, -0.32, 0.32, h - 0.25, h - 0.18, 'lvB', hull='none')


def build_columns(pal, ao):
    for name, h in (('Col_Lo', UNDER), ('Col_Hi', H - DECK), ('Col_Full', H)):
        for k, code in enumerate(CODES):
            m = new(pal)
            column(m, h, code)
            make('%s_%d' % (name, k), m, ao, cols=[cb(-0.3, -0.3, 0, 0.3, 0.3, h)])


def build_rails(pal, ao):
    """deck-edge barrier: concrete upstand with hazard paint, galvanised posts, yellow top rail (half module from the
    cell centre toward Blender -Y, a full module, a post)"""
    def rail(m, y0, y1):
        m.bx(-0.1, 0.1, y0, y1, 0.0, 0.35, 'concL', hull='noend', cull='b')
        n = max(1, int(round((y1 - y0) / 0.25)))
        for i in range(0, n, 2):
            a, b = y0 + i * (y1 - y0) / n, y0 + (i + 1) * (y1 - y0) / n
            lq(m, -0.103, a, b, 0.05, 0.3, 'lineY')
            rq(m, 0.103, a, b, 0.05, 0.3, 'lineY')
        m.bx(-0.035, 0.035, y0, y1, 1.0, 1.08, 'lineY', hull='noend')
        m.bx(-0.02, 0.02, y0, y1, 0.66, 0.71, 'galv', hull='none')
    m = new(pal)
    rail(m, -0.5, -0.1)
    make('Rail', m, ao, cols=[cb(-0.1, -0.5, 0, 0.1, 0.0, 1.1)])
    m = new(pal)
    rail(m, -0.5, 0.5)
    m.bx(-0.03, 0.03, -0.03, 0.03, 0.35, 1.0, 'galv', hull='none')
    make('RailFull', m, ao, cols=[cb(-0.1, -0.5, 0, 0.1, 0.5, 1.1)])
    m = new(pal)   # junction / end post: upstand block, galvanised post, a cap that meets the top rails
    m.bx(-0.1, 0.1, -0.1, 0.1, 0.0, 0.35, 'concL', cull='b')
    m.bx(-0.04, 0.04, -0.04, 0.04, 0.35, 1.0, 'galv')
    m.bx(-0.1, 0.1, -0.1, 0.1, 1.0, 1.1, 'lineY')
    make('RailPost', m, ao)


# ================================================================ ramps and stairs
def build_ramp(pal, ao, name, L, rise, lane, curb):
    """straight car ramp rising toward +Y: a concrete wedge (lane) between kerbs, guard rails both sides.
    Collision: walkable stair blocks (rises of ~0.12 m; the visual slope runs through their middles), kerb + rail walls."""
    m = new(pal)
    W = lane / 2 + curb
    s = lambda y: rise * (y + L / 2) / L
    slope_n = (0, -rise, L)
    m.prism([(-L / 2, 0.0), (L / 2, 0.0), (L / 2, rise)], -lane / 2, lane / 2, ['conc'], skip=(0,))
    for sx in (-1, 1):
        a, b = sorted((sx * lane / 2, sx * W))
        m.prism([(-L / 2, 0.0), (L / 2, 0.0), (L / 2, rise + 0.22), (-L / 2, 0.22)], a, b, ['concL'], skip=(0,))
        xo = sx * (W + 0.003)
        # level band along the side wall (recoloured per level), hazard blocks at the foot
        ya = -L / 2 + 0.75 / rise * L
        pts = [(ya, 0.05), (L / 2, rise - 0.55), (L / 2, rise - 0.12), (ya, s(ya) - 0.12)]
        poly(m, [(xo, p[0], p[1]) for p in pts], 'lvB', (sx, 0, 0))
        for k in range(6):
            y0 = -L / 2 + 0.05 + k * 0.3
            if y0 + 0.15 < ya - 0.1:
                poly(m, [(xo, y0, 0.02), (xo, y0 + 0.15, 0.02), (xo, y0 + 0.15, s(y0 + 0.15) + 0.18), (xo, y0, s(y0) + 0.18)], 'lineY', (sx, 0, 0))
        # kerb-top stripe and the guard rail (posts every 2 m, two rails along the slope)
        xc = sx * (lane / 2 + curb / 2)
        poly(m, [(xc - 0.06, -L / 2, 0.226), (xc + 0.06, -L / 2, 0.226), (xc + 0.06, L / 2, rise + 0.226), (xc - 0.06, L / 2, rise + 0.226)], 'lineY', slope_n)
        n = max(1, int(L // 2))
        for k in range(n + 1):
            y = -L / 2 + 0.3 + k * (L - 0.6) / n
            m.bx(xc - 0.04, xc + 0.04, y - 0.04, y + 0.04, s(y) + 0.2, s(y) + 1.12, 'galv', cull='b')
        for dz, c, t in ((1.1, 'lineY', 0.07), (0.7, 'galv', 0.05)):
            m.bm_((xc, -L / 2 + 0.22, s(-L / 2 + 0.22) + dz), (xc, L / 2 - 0.05, s(L / 2 - 0.05) + dz), t, c)

    def slope_quad(x0, x1, y0, y1, off, c):
        poly(m, [(x0, y0, s(y0) + off), (x1, y0, s(y0) + off), (x1, y1, s(y1) + off), (x0, y1, s(y1) + off)], c, slope_n)
    # lane paint on the slope: anti-skid grooves, a yellow nose at the foot, centre dashes, up / down arrows
    for k in range(1, int(L / 0.5)):
        y = -L / 2 + k * 0.5
        slope_quad(-lane / 2, lane / 2, y - 0.03, y + 0.03, 0.004, 'concW')
    slope_quad(-lane / 2, lane / 2, -L / 2 + 0.02, -L / 2 + 0.22, 0.004, 'lineY')
    if lane >= 3.5:
        for k in range(int(L / 2)):
            y = -L / 2 + 0.8 + k * 2.0
            if y + 1.0 < L / 2:
                slope_quad(-0.06, 0.06, y, y + 1.0, 0.009, 'lineY')
        for sx, dirn in ((-1, 1), (1, -1)):
            xc = sx * lane / 4
            tail, tip = -dirn * 1.1, dirn * 1.1
            head = tip - dirn * 0.6
            ys = sorted((tail, head))
            slope_quad(xc - 0.13, xc + 0.13, ys[0], ys[1], 0.009, 'paper')
            poly(m, [(xc - 0.38, head, s(head) + 0.009), (xc + 0.38, head, s(head) + 0.009), (xc, tip, s(tip) + 0.009)], 'paper', slope_n)
    n = max(2, int(round(L / 0.533)))
    run = L / n
    cols = []
    for k in range(n):
        y0 = -L / 2 + k * run
        top = rise if k == n - 1 else rise * (k + 0.5) / n
        cols.append(cb(-lane / 2, y0, 0.0, lane / 2, y0 + run, top, True))
    nseg = max(1, int(round(L / 2)))
    for sx in (-1, 1):
        a, b = sorted((sx * lane / 2, sx * W))
        for k in range(nseg):
            y0, y1 = -L / 2 + k * L / nseg, -L / 2 + (k + 1) * L / nseg
            cols.append(cb(a, y0, 0.0, b, y1, s(y1) + 1.12))
    make(name, m, ao, cols=cols)


def build_stair(pal, ao, name, W, L, rise, n, wall=0.15, landing=0.0):
    """concrete stair flight rising toward +Y (a landing at the top), yellow nosings, parapet walls with a level band
    and handrails. Collision: walkable stair blocks, parapet walls following the flight."""
    m = new(pal)
    run = (L - landing) / n
    cols = []
    for k in range(n):
        y0 = -L / 2 + k * run
        y1 = y0 + run if k < n - 1 else L / 2
        top = (k + 1) * rise / n
        m.bx(-W / 2, W / 2, y0, y1, 0.0, top, 'concL', cull='b' + ('k' if k < n - 1 else ''))
        uq(m, -W / 2 + 0.03, W / 2 - 0.03, y0 + 0.005, y0 + 0.07, top + 0.003, 'lineY')
        cols.append(cb(-W / 2, y0, 0.0, W / 2, y1, top, True))
    yt = L / 2 - landing - run   # start of the top step
    for sx in (-1, 1):
        a, b = sorted((sx * W / 2, sx * (W / 2 + wall)))
        prof = [(-L / 2, 0.0), (L / 2, 0.0), (L / 2, rise + 1.0), (yt, rise + 1.0), (-L / 2 + run, rise / n + 1.0), (-L / 2, rise / n + 1.0)]
        m.prism(prof, a, b, ['conc'], skip=(0,))
        xo = sx * (W / 2 + wall + 0.003)
        y0b = -L / 2 + run
        if yt - y0b > 0.5:
            poly(m, [(xo, y0b, rise / n + 0.25), (xo, yt, rise + 0.25), (xo, yt, rise + 0.6), (xo, y0b, rise / n + 0.6)], 'lvB', (sx, 0, 0))
        xi = sx * (W / 2 - 0.06)
        m.bm_((xi, -L / 2 + 0.2, rise / n + 0.9), (xi, yt, rise + 0.9), 0.05, 'lineY')
        if landing > 0:
            m.bm_((xi, yt + 0.03, rise + 0.9), (xi, L / 2 - 0.05, rise + 0.9), 0.044, 'lineY')
        for k in range(n + 1):
            y0 = -L / 2 + k * run
            y1 = L / 2 if k == n else y0 + run
            top = min(rise, (k + 1) * rise / n) + 1.0
            cols.append(cb(a, y0, 0.0, b, y1, top))
    make(name, m, ao, cols=cols)


def build_circulation(pal, ao):
    build_ramp(pal, ao, 'Ramp', 16.0, DECK, 4.0, 0.5)
    build_ramp(pal, ao, 'RampHalf', 8.0, DECK / 2, 4.0, 0.5)
    build_ramp(pal, ao, 'DockRamp', 6.0, 1.2, 2.0, 0.5)
    build_stair(pal, ao, 'Stair', 2.4, 8.0, DECK, 12, landing=0.8)
    build_stair(pal, ao, 'DockStep', 1.7, 3.0, 1.2, 4)


# ================================================================ gate, corridor, hatch
def build_gate(pal, ao):
    """concrete portal: hazard-banded piers, a yellow lintel with chevrons, wall up to the ceiling with a blue P sign and
    a down arrow on both faces (closes the corridor end: |x| <= 2.5, full height)"""
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.5, sx * 1.82))
        m.bx(a, b, -0.62, 0.62, 0.0, 3.3, 'concL', cull='b')
        for fy in (-1, 1):
            for k in range(4):
                (fq if fy < 0 else bq)(m, a, b, fy * 0.623, 0.25 + k * 0.4, 0.45 + k * 0.4, 'lineY')
    m.bx(-1.82, 1.82, -0.62, 0.62, 3.3, 3.9, 'lineY')
    for fy in (-1, 1):
        for k in range(0, 9, 2):
            (fq if fy < 0 else bq)(m, -1.8 + k * 0.4, -1.8 + (k + 1) * 0.4, fy * 0.623, 3.36, 3.84, 'ink')
    m.bx(-2.48, 2.48, -0.45, 0.45, 3.9, H, 'conc', cull='t')
    for fy in (-1, 1):
        y = fy * 0.45
        m.bx(-1.0, 1.0, min(y, y + fy * 0.1), max(y, y + fy * 0.1), 4.3, 6.1, 'signB')
        yy = fy * 0.553
        f = fq if fy < 0 else bq
        f(m, -0.85, 0.85, yy, 4.42, 5.98, 'paper')
        f(m, -0.78, 0.78, yy + fy * 0.003, 4.49, 5.91, 'signB')
        if fy < 0:
            text_front(m, 'P', 0.13, yy - 0.006, -0.35, 5.0, 'paper')
        else:
            text_back(m, 'P', 0.13, yy + 0.006, -0.35, 5.0, 'paper')
        poly(m, [(0.2, yy + fy * 0.006, 5.45), (0.65, yy + fy * 0.006, 5.45), (0.425, yy + fy * 0.006, 4.75)], 'lineY', (0, fy, 0))
        m.bx(-2.48, 2.48, min(y, y + fy * 0.06), max(y, y + fy * 0.06), 6.65, 6.85, 'concL', hull='noside')
    make('GateFrame', m, ao, cols=[cb(-1.82, -0.62, 0, -1.5, 0.62, 3.3), cb(1.5, -0.62, 0, 1.82, 0.62, 3.3)])
    m = new(pal)
    Hs, n = 3.05, 12
    for i in range(n):
        z = 0.3 + (i + 0.5) * (Hs - 0.3) / n
        m.box((0, 0, z), (3.0, 0.1, (Hs - 0.3) / n - 0.03), 'galv' if i % 2 else 'steel', bevel=False)
    for k in range(10):
        m.box((-1.5 + (k + 0.5) * 0.3, 0, 0.15), (0.3, 0.12, 0.3), 'ink' if k % 2 else 'lineY', bevel=False)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, 3.05 / 2), (3.0, 0.14, 3.05), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # corridor walls (the ramp tunnel between levels): 1 m along Blender Y, inner face +X
    for name in ('TrailWall', 'TrailWall_B', 'TrailWall_C'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'conc', hull='noend', cull='t')
        m.bx(0.25, 0.33, -0.5, 0.5, 0.0, 0.2, 'lineY', hull='noend', cull='b')
        rq(m, 0.333, -0.5, -0.25, 0.0, 0.2, 'ink')
        rq(m, 0.333, 0.0, 0.25, 0.0, 0.2, 'ink')
        rq(m, 0.253, -0.5, 0.5, 0.35, 1.3, 'signB')
        rq(m, 0.253, -0.5, 0.5, 1.38, 1.46, 'lvBL')
        rq(m, 0.253, -0.5, 0.5, 2.6, 2.63, 'concW')
        m.bx(0.25, 0.4, -0.5, 0.5, 6.7, H, 'concL', hull='noend', cull='t')
        if name == 'TrailWall_B':   # bulkhead lamp
            m.bx(0.25, 0.36, -0.2, 0.2, 2.75, 3.05, 'steelD')
            rq(m, 0.363, -0.16, 0.16, 2.79, 3.01, 'light')
        elif name == 'TrailWall_C':   # chevron pointing on (+Y)
            for k in range(2):
                y0 = -0.35 + k * 0.4
                pts = [(y0, 0.55), (y0 + 0.18, 0.55), (y0 + 0.38, 0.825), (y0 + 0.18, 1.1), (y0, 1.1), (y0 + 0.2, 0.825)]
                poly(m, [(0.256, p[0], p[1]) for p in pts[:3] + [pts[5]]], 'paper', (1, 0, 0))
                poly(m, [(0.256, p[0], p[1]) for p in [pts[5], pts[2], pts[3], pts[4]]], 'paper', (1, 0, 0))
        make(name, m, ao)
    # exit hatch: round steel plate with a yellow hazard ring
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.1, 'steelD', seg=20)
    for i in range(20):
        a0, a1 = i / 20 * 2 * math.pi, (i + 1) / 20 * 2 * math.pi
        poly(m, [(math.cos(a0) * 0.95, math.sin(a0) * 0.95, 0.103), (math.cos(a0) * 1.12, math.sin(a0) * 1.12, 0.103),
                 (math.cos(a1) * 1.12, math.sin(a1) * 1.12, 0.103), (math.cos(a1) * 0.95, math.sin(a1) * 0.95, 0.103)], 'lineY' if i % 2 else 'ink', (0, 0, 1))
    for k in range(-3, 4):
        uq(m, -0.6, 0.6, k * 0.2 - 0.03, k * 0.2 + 0.03, 0.106, 'steel')
    make('Hatch', m, ao, bevel=0.015)
