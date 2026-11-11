"""kit-cargoship cargo: ISO containers (40 ft 12.0 x 2.44 x 2.6 m, 20 ft 6.0 m long) in double stacks on the hatch
covers, reefers, a tank container, flat racks with a motor launch and with machinery, container cells with cell
guides for the hold, lashing bridges between the hatches, and project cargo in the hold (a transformer on skids,
cable drums, a pipe stack).

A box's colours are one of the four paint slots (CSLOT); a stack piece mixes them and the theme repaints the slots
per placed stack. Boxes stand along Blender Y (game north-south), doors at the +Y (north) end."""
import math

from cargo_base import *  # noqa: F401,F403
import ib_text

CW, CH = 2.44, 2.6


def box(m, x, y, z, L, slot, vis, door=1, reefer=False, brand=None):
    """one container centred on (x, y), base z, length L along Y. vis: set of faces seen ('l' -X side, 'r' +X side,
    't' top, 'n' +Y end, 's' -Y end). door: +1 doors on the +Y end, -1 on the -Y end."""
    c, cd = ('cWht', 'cWhtD') if reefer else CSLOT[slot]
    hx, hy = CW / 2, L / 2
    cull = 'b' + ''.join(k for k, f in (('l', 'l'), ('r', 'r'), ('t', 't'), ('k', 'n'), ('f', 's')) if f not in vis)
    m.bx(x - hx, x + hx, y - hy, y + hy, z, z + CH, c, cull=cull)
    for side, sx in (('l', -1), ('r', 1)):
        if side not in vis:
            continue
        xf = x + sx * (hx + 0.003)
        f = lq if sx < 0 else rq
        f(m, xf, y - hy, y + hy, z, z + 0.16, cd)
        f(m, xf, y - hy, y + hy, z + CH - 0.16, z + CH, cd)
        n = int(L / 1.45)
        for k in range(n):
            yy = y - hy + 0.5 + k * (L - 1.0) / max(1, n - 1)
            f(m, xf, yy - 0.11, yy + 0.11, z + 0.2, z + CH - 0.2, cd)
        for yy in (y - hy, y + hy - 0.16):
            f(m, xf, yy, yy + 0.16, z + 0.16, z + CH - 0.16, cd)
        if brand and L > 10:
            ib_text.draw(m, brand, x + sx * (hx + 0.008), y, z + 0.85, 0.9, 'paper', face='x+' if sx > 0 else 'x-', font='display', maxw=L * 0.6)
        if reefer:
            pass
    for end, sy in (('n', 1), ('s', -1)):
        if end not in vis:
            continue
        yf = y + sy * (hy + 0.003)
        f = bq if sy > 0 else fq
        f(m, x - hx, x + hx, yf, z, z + 0.16, cd)
        f(m, x - hx, x + hx, yf, z + CH - 0.22, z + CH, cd)
        for xx in (x - hx, x + hx - 0.16):
            f(m, xx, xx + 0.16, yf, z + 0.16, z + CH - 0.22, cd)
        if reefer and sy == -door:   # machinery end: grille, controller
            f(m, x - 0.95, x + 0.95, yf + sy * 0.003, z + 0.3, z + 1.5, 'steelD')
            for k in range(5):
                f(m, x - 0.9, x + 0.9, yf + sy * 0.006, z + 0.38 + k * 0.22, z + 0.46 + k * 0.22, 'ink')
            f(m, x + 0.3, x + 0.85, yf + sy * 0.003, z + 1.65, z + 2.2, 'galv')
            f(m, x + 0.4, x + 0.75, yf + sy * 0.006, z + 1.85, z + 2.05, 'teal')
        elif sy == door:   # door end: seam, locking bars, handles
            f(m, x - 0.02, x + 0.02, yf + sy * 0.003, z + 0.16, z + CH - 0.22, cd)
            for xx in (-0.85, -0.3, 0.3, 0.85):
                f(m, x + xx - 0.03, x + xx + 0.03, yf + sy * 0.003, z + 0.2, z + CH - 0.26, 'galv')
        else:
            for k in range(2):
                xx = x - 0.4 + k * 0.8
                f(m, xx - 0.1, xx + 0.1, yf + sy * 0.003, z + 0.2, z + CH - 0.26, cd)


def lashing(m, x, y, z, sy):
    """lashing rods crossed over a stack end (just off the end face at y), turnbuckles at their feet"""
    for sx in (-1, 1):
        a = (x + sx * 1.0, y + sy * 0.07, z + 0.06)
        b = (x - sx * 1.05, y + sy * 0.035, z + CH - 0.1)
        m.bm_(a, b, 0.03, 'galv', hull='none')
        m.bx(a[0] - 0.04, a[0] + 0.04, a[1] - 0.03, a[1] + 0.03, z, z + 0.3, 'yel', hull='none')


def stack(m, rows, L=12.0, vis_end=('n', 's'), seed=0, reefers=(), brands=(), lash=None, z0=0.0):
    """rows: [(x, tiers), ...] side by side; boxes of length L; slot colours mixed by position"""
    for ri, (x, n) in enumerate(rows):
        for t in range(n):
            vis = set(vis_end)
            left = [r for r in rows if abs(r[0] - (x - 2.5)) < 0.1]
            right = [r for r in rows if abs(r[0] - (x + 2.5)) < 0.1]
            if not left or left[0][1] <= t:
                vis.add('l')
            if not right or right[0][1] <= t:
                vis.add('r')
            if t == n - 1:
                vis.add('t')
            slot = (seed + ri * 3 + t * 5 + (t * ri)) % 4
            box(m, x, 0.0, z0 + t * CH, L, slot, vis, door=1 if (ri + t + seed) % 3 else -1,
                reefer=(ri, t) in reefers, brand=LINE if (ri, t) in brands else None)
    if lash is None:
        lash = L > 10
    if lash:
        for x, n in rows:
            for sy in (-1, 1):
                lashing(m, x, sy * (L / 2 + 0.003), z0, sy)


def stack_cols(rows, L=12.0):
    cols = []
    for x, n in rows:
        cols.append(cb(x - CW / 2 - 0.02, -L / 2 - 0.02, 0.0, x + CW / 2 + 0.02, L / 2 + 0.02, n * CH))
    return cols


DOUBLE = (-1.25, 1.25)


def build_stacks(pal, ao):
    # 40 ft double stacks on the hatch covers [5,12]: tiers, stepped tops, reefers, the line's own boxes
    specs = {
        'S40_1A': [(DOUBLE[0], 1), (DOUBLE[1], 1)],
        'S40_1R': [(DOUBLE[0], 1), (DOUBLE[1], 1)],
        'S40_2A': [(DOUBLE[0], 2), (DOUBLE[1], 2)],
        'S40_2B': [(DOUBLE[0], 2), (DOUBLE[1], 1)],
        'S40_3A': [(DOUBLE[0], 3), (DOUBLE[1], 3)],
        'S40_4A': [(DOUBLE[0], 4), (DOUBLE[1], 4)],
        'S40_4B': [(DOUBLE[0], 4), (DOUBLE[1], 3)],
    }
    extra = {'S40_1R': dict(reefers={(1, 0)}), 'S40_2A': dict(brands={(0, 0)}),
             'S40_3A': dict(brands={(1, 1)}), 'S40_4A': dict(reefers={(0, 3)}, brands={(1, 1)})}
    for i, (name, rows) in enumerate(specs.items()):
        m = new(pal)
        stack(m, rows, seed=i, **extra.get(name, {}))
        make(name, m, ao, cols=stack_cols(rows))
    # 20 ft double stacks [5,6]
    for i, (name, rows) in enumerate((('S20_1A', [(DOUBLE[0], 1), (DOUBLE[1], 1)]), ('S20_2A', [(DOUBLE[0], 2), (DOUBLE[1], 2)]),
                                      )):
        m = new(pal)
        stack(m, rows, L=6.0, seed=i + 2)
        make(name, m, ao, cols=stack_cols(rows, 6.0))
    # tank container [3,6]: a white tank in a 20 ft frame
    m = new(pal)
    L = 6.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * CW / 2 - (0.16 if sx > 0 else 0), sx * CW / 2 + (0.16 if sx < 0 else 0), sy * L / 2 - (0.16 if sy > 0 else 0),
                 sy * L / 2 + (0.16 if sy < 0 else 0), 0.0, CH, 'cOra', cull='b')
        for z in (0.0, CH - 0.16):
            m.bx(sx * CW / 2 - (0.12 if sx > 0 else 0), sx * CW / 2 + (0.12 if sx < 0 else 0), -L / 2 + 0.16, L / 2 - 0.16, z, z + 0.16, 'cOraD')
    for sy in (-1, 1):
        for z in (0.0, CH - 0.16):
            m.bx(-CW / 2 + 0.16, CW / 2 - 0.16, min(sy * L / 2, sy * (L / 2 - 0.12)), max(sy * L / 2, sy * (L / 2 - 0.12)), z, z + 0.16, 'cOraD')
    m.cy((0, -L / 2 + 0.4, CH / 2), 1.12, 1.12, L - 0.8, 'cWht', seg=14, rot=(-90, 0, 0))
    for sy in (-1, 1):
        m.sp((0, sy * (L / 2 - 0.4), CH / 2), 1.12, 'cWht', seg=(14, 6), scale=(1, 0.22, 1))
    for y in (-1.6, 0.0, 1.6):
        m.cy((0, y - 0.05, CH / 2), 1.135, 1.135, 0.1, 'cWhtD', seg=14, rot=(-90, 0, 0), hull='none')
    m.bx(-0.3, 0.3, -0.3, 0.3, CH - 0.05, CH + 0.08, 'steelD')
    ib_text.draw(m, 'NON-POTABLE', CW / 2 - 0.03, 0.0, 1.95, 0.22, 'fireR', face='x+', font='cond')
    make('Tank_20', m, ao, cols=[cb(-CW / 2 - 0.02, -L / 2, 0, CW / 2 + 0.02, L / 2, CH)])
    # flat racks [3,12]: end walls, a floor, and their cargo
    for name in ('Flat_Boat', 'Flat_Mach'):
        m = new(pal)
        L = 12.0
        m.bx(-CW / 2, CW / 2, -L / 2, L / 2, 0.0, 0.5, 'cRed', cull='b')
        fq(m, -CW / 2, CW / 2, -L / 2 - 0.003, 0.0, 0.5, 'cRedD')
        for sy in (-1, 1):
            y0, y1 = sorted((sy * L / 2, sy * (L / 2 - 0.3)))
            m.bx(-CW / 2, CW / 2, y0, y1, 0.5, CH, 'cRed', cull='b')
            for k in range(3):
                (fq if sy < 0 else bq)(m, -1.0 + k * 0.8, -0.8 + k * 0.8, sy * (L / 2 + 0.003), 0.6, CH - 0.1, 'cRedD')
        for sx in (-1, 1):
            for y in (-4.0, -1.5, 1.5, 4.0):
                m.bx(sx * CW / 2 - 0.05, sx * CW / 2 + 0.05, y - 0.06, y + 0.06, 0.5, 0.75, 'cRedD', hull='none')
        if name == 'Flat_Boat':   # a motor launch on cradles, under straps
            for y in (-3.0, 2.5):
                m.bx(-0.7, 0.7, y - 0.2, y + 0.2, 0.5, 1.0, 'wood', cull='b')
            prof = [(-4.9, 1.3), (-4.6, 0.85), (-2.0, 0.75), (4.3, 0.85), (4.9, 1.2), (5.0, 2.0), (-5.1, 2.0)]
            m.prism([(p[0], p[1]) for p in prof], -1.0, 1.0, ['paper'])
            m.bx(-1.03, 1.03, -5.0, 5.0, 1.75, 1.86, 'signB', hull='none')
            m.bx(-0.8, 0.8, -2.2, 1.2, 2.0, 2.9, 'paper', bevel=True)
            m.bx(-0.82, 0.82, -2.0, 1.0, 2.45, 2.75, 'glassD', hull='none')
            m.bx(-0.85, 0.85, -2.4, 1.4, 2.9, 3.0, 'signB')
            for y in (-3.5, 0.0, 3.3):
                m.bx(-1.08, 1.08, y - 0.06, y + 0.06, 0.75, 2.05, 'yel', hull='none')
            cols = [cb(-CW / 2, -L / 2, 0, CW / 2, L / 2, 0.5), cb(-CW / 2, -L / 2, 0.5, CW / 2, -L / 2 + 0.3, CH),
                    cb(-CW / 2, L / 2 - 0.3, 0.5, CW / 2, L / 2, CH), cb(-1.05, -5.1, 0.5, 1.05, 5.0, 3.0)]
        else:   # crated machinery and a diesel generator set under a tarp
            m.bx(-1.0, 1.0, -5.2, -1.4, 0.5, 2.3, 'wood', bevel=True, cull='b')
            for z in (0.9, 1.9):
                m.bx(-1.01, 1.01, -5.21, -1.39, z, z + 0.1, 'cBrnD', hull='none')
            ib_text.draw(m, 'THIS SIDE UP', -1.003, -3.3, 1.3, 0.22, 'ink', face='x-', font='cond')
            m.bx(-1.0, 1.0, -0.8, 5.2, 0.5, 2.1, 'signB', bevel=True, cull='b')
            m.bx(-1.02, 1.02, 0.6, 0.8, 0.5, 2.12, 'ink', hull='none', cull='b')
            m.bx(-1.02, 1.02, 3.4, 3.6, 0.5, 2.12, 'ink', hull='none', cull='b')
            cols = [cb(-CW / 2, -L / 2, 0, CW / 2, L / 2, 0.5), cb(-CW / 2, -L / 2, 0.5, CW / 2, -L / 2 + 0.3, CH),
                    cb(-CW / 2, L / 2 - 0.3, 0.5, CW / 2, L / 2, CH), cb(-1.0, -5.2, 0.5, 1.0, 5.2, 2.3)]
        make(name, m, ao, cols=cols)


# ================================================================ hold: container cells with cell guides [3,13]
def guide(m, x, y, sx, sy, z1=H - 0.01):
    """an angle-bar cell guide at a cell corner; the angle opens toward the cell (sx, sy point outward)"""
    a, b = sorted((x, x + sx * 0.18))
    c, d = sorted((y, y + sy * 0.03))
    m.bx(a, b, c, d, 0.0, z1, 'yel', cull='t')
    a2, b2 = sorted((x + sx * 0.15, x + sx * 0.18))
    c2, d2 = sorted((y, y - sy * 0.15))
    m.bx(a2, b2, c2, d2, 0.0, z1, 'yel', cull='t')


def build_cells(pal, ao):
    L = 12.0
    gx, gy = 1.3, 6.35
    for name, n, extra in (('Cell_0', 0, None), ('Cell_1', 1, None), ('Cell_2', 2, None), ('Cell_3', 3, None),
                           ('Cell_4', 4, None), ('Cell_Flat', 0, 'flat')):
        m = new(pal)
        for sx in (-1, 1):
            for sy in (-1, 1):
                guide(m, sx * gx, sy * gy, sx, sy)
        for sy in (-1, 1):   # cross ties between the guides at the cell ends
            for z in (WALK - 0.25, 2 * WALK - 0.25):
                m.bx(-gx + 0.18, gx - 0.18, sy * gy - 0.04, sy * gy + 0.04, z, z + 0.12, 'yelD')
        # container foot sockets on the tank top
        for sx in (-1, 1):
            for sy in (-1, 1):
                uq(m, sx * 1.05 - 0.12, sx * 1.05 + 0.12, sy * 5.85 - 0.08, sy * 5.85 + 0.08, 0.006, 'steelD')
        cols = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                a, b = sorted((sx * gx, sx * (gx + 0.18)))
                c, d = sorted((sy * gy, sy * (gy - 0.15)))
                cols.append(cb(a, c, 0, b, d, H - 0.01))
        for t in range(n):
            vis = {'l', 'r', 'n', 's'}
            if t == n - 1:
                vis.add('t')
            box(m, 0.0, 0.0, t * CH, L, (t * 3 + n) % 4, vis, door=1 if t % 2 else -1, reefer=(extra == 'reefer'),
                brand=LINE if (n >= 3 and t == 1) else None)
        if n:
            cols.append(cb(-CW / 2 - 0.02, -L / 2, 0, CW / 2 + 0.02, L / 2, n * CH))
        if extra == 'reefer':   # power cable from the reefer socket on the guide
            m.bm_((0.6, -6.0, 1.9), (1.2, -6.3, 4.8), 0.04, 'ink', hull='none')
            m.bx(1.12, 1.3, -6.42, -6.3, 4.6, 5.0, 'steelD')
        if extra == 'flat':   # a flat rack holding a yacht hull on cradles
            m.bx(-CW / 2, CW / 2, -L / 2, L / 2, 0.0, 0.5, 'cBlu', cull='b')
            for sy in (-1, 1):
                y0, y1 = sorted((sy * L / 2, sy * (L / 2 - 0.3)))
                m.bx(-CW / 2, CW / 2, y0, y1, 0.5, CH, 'cBlu', cull='b')
            for y in (-3.0, 2.5):
                m.bx(-0.75, 0.75, y - 0.2, y + 0.2, 0.5, 1.1, 'wood', cull='b')
            prof = [(-5.2, 1.7), (-4.8, 1.0), (-1.5, 0.85), (4.0, 1.0), (5.3, 1.9), (5.4, 2.4), (-5.4, 2.4)]
            m.prism(prof, -1.05, 1.05, ['cWht'])
            m.bx(-1.08, 1.08, -5.3, 5.3, 2.2, 2.3, 'cNav', hull='none')
            m.cy((0, 1.2, 2.4), 0.06, 0.06, 6.2, 'galv', seg=6)
            m.bx(-0.6, 0.6, -2.5, 0.8, 2.4, 3.0, 'cWht', bevel=True)
            m.bx(-0.62, 0.62, -2.3, 0.6, 2.6, 2.85, 'glassD', hull='none')
            cols += [cb(-CW / 2, -L / 2, 0, CW / 2, L / 2, 0.5), cb(-CW / 2, -L / 2, 0.5, CW / 2, -L / 2 + 0.3, CH),
                     cb(-CW / 2, L / 2 - 0.3, 0.5, CW / 2, L / 2, CH), cb(-1.1, -5.4, 0.5, 1.1, 5.4, 3.0)]
        make(name, m, ao, cols=cols)


# ================================================================ lashing bridges [6,2]
def build_lashing_bridges(pal, ao):
    for name in ('LB_A', 'LB_B'):
        m = new(pal)
        cols = []
        for x in (-1.5, 1.5):
            for y in (-0.8, 0.8):
                m.bx(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.0, 7.2, 'deckGL', cull='t')
                cols.append(cb(x - 0.13, y - 0.13, 0, x + 0.13, y + 0.13, 7.2))
            m.bm_((x, -0.8, 0.3), (x, 0.8, 4.0), 0.07, 'deckGL', hull='none')
        for z in (4.4, 7.0):   # platforms: grating floor, toe plates, rails both sides
            m.bx(-3.0, 3.0, -0.95, 0.95, z - 0.12, z, 'galv', hull='noside')
            dq(m, -3.0, 3.0, -0.95, 0.95, z - 0.123, 'steelD')
            for y in (-0.95, 0.95):
                rail_run(m, -3.0, 3.0, y, z, h=1.05, c='yel', post=2.0, toe=False)
            cols.append(cb(-3.0, -0.95, z - 0.12, 3.0, 0.95, z))
        m.bx(-3.0, 3.0, -0.1, 0.1, 4.0, 4.28, 'deckGL', hull='noside')
        m.bx(-3.0, 3.0, -0.1, 0.1, 6.6, 6.88, 'deckGL', hull='noside')
        if name == 'LB_B':   # ladder up to the platforms
            ladder(m, 0.0, -0.95, 0.0, 7.0 + 1.0, c='yel')
        elif name == 'LB_C':   # spare lashing rods hung on the rail, a gear box on the platform
            for k in range(7):
                x = -2.4 + k * 0.22
                m.bm_((x, -0.99, 4.45), (x + 0.15, -1.03, 6.8), 0.025, 'galv', hull='none')
            m.bx(1.0, 2.2, -0.6, 0.3, 4.4, 5.0, 'yelD', bevel=True)
            m.bx(1.05, 2.15, -0.55, 0.25, 5.0, 5.03, 'grime', hull='none')
        make(name, m, ao, cols=cols, side=2.95)


# ================================================================ hold project cargo
def build_project(pal, ao):
    # power transformer on steel skids [4,6], lashed with chains
    m = new(pal)
    for x in (-1.4, 1.4):
        m.bx(x - 0.2, x + 0.2, -2.9, 2.9, 0.0, 0.35, 'steelD', cull='b')
    m.bx(-1.6, 1.6, -2.4, 2.4, 0.35, 3.2, 'engGD', bevel=True)
    for sy in (-1, 1):   # radiator fins on both ends
        for k in range(8):
            x = -1.3 + k * 0.37
            y0, y1 = sorted((sy * 2.4, sy * 2.75))
            m.bx(x - 0.04, x + 0.04, y0, y1, 0.6, 2.8, 'engG', hull='none', cull='tb')
    for x in (-0.9, 0.0, 0.9):
        m.cy((x, 0.0, 3.2), 0.16, 0.12, 0.9, 'paper', seg=8)
        for k in range(2):
            m.cy((x, 0.0, 3.4 + k * 0.3), 0.2, 0.2, 0.06, 'cBrn', seg=8, hull='none')
    m.cy((1.0, -1.6, 3.2), 0.3, 0.3, 0.5, 'engG', seg=10)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bm_((sx * 1.6, sy * 2.2, 2.4), (sx * 1.95, sy * 2.85, 0.05), 0.04, 'steelD', hull='none')
    fq(m, -0.6, 0.6, -2.403, 1.6, 2.2, 'paper')
    text_front(m, 'HV', 0.08, -2.406, 0.0, 1.7, 'fireR')
    make('Transformer', m, ao, cols=[cb(-1.6, -2.4, 0, 1.6, 2.4, 3.2), cb(-1.6, -2.9, 0, 1.6, 2.9, 0.35)])
    # cable drums [2,2]: two big wooden reels on chocks
    m = new(pal)
    for x, r, ya, yb in ((-0.45, 0.8, -0.92, -0.12), (0.5, 0.62, 0.12, 0.86)):
        for y in (ya, yb):
            m.cy((x, y, r + 0.02), r, r, 0.12, 'wood', seg=14, rot=(-90, 0, 0))
        m.cy((x, ya + 0.12, r + 0.02), r * 0.7, r * 0.7, yb - ya - 0.12, 'ink', seg=12, rot=(-90, 0, 0))
        m.bx(x - 0.3, x + 0.3, ya - 0.04, yb + 0.16, 0.0, 0.1, 'wood', cull='b')
    make('CableDrums', m, ao, cols=[cb(-1.25, -0.96, 0, -0.1, -0.0, 1.62), cb(-0.12, 0.08, 0, 1.12, 0.98, 1.26)])
    # steel pipe stack on dunnage [3,6]
    m = new(pal)
    for y in (-2.2, 0.0, 2.2):
        m.bx(-1.3, 1.3, y - 0.12, y + 0.12, 0.0, 0.14, 'wood', cull='b')
    r = 0.32
    for row, (n, z) in enumerate(((4, 0.14 + r), (3, 0.14 + r + 0.56))):
        for k in range(n):
            x = (k - (n - 1) / 2) * 0.66
            m.cy((x, -2.9, z), r, r, 5.8, 'rust' if (k + row) % 2 else 'steel', seg=10, rot=(-90, 0, 0))
            m.cy((x, -2.9, z), r * 0.8, r * 0.8, 0.004, 'ink', seg=10, rot=(90, 0, 0), hull='none')
    for y in (-1.2, 1.2):
        m.bx(-1.35, 1.35, y - 0.04, y + 0.04, 0.12, 1.58, 'yel', hull='none')
    make('PipeStack', m, ao, cols=[cb(-1.3, -2.9, 0, 1.3, 2.9, 1.5)])
