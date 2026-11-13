"""kit-datacenter data hall and room props: rack rows (compute, network, storage, AI / GPU; capped row ends) with
blinking LED companions, CRAC cooling units, clean-agent fire-suppression tanks, UPS cabinets, battery strings, a
power distribution unit, NOC desks with monitor companions, a meeting table, the armory locker, gear lockers, the mod
bench, structural columns, server boxes, a crash cart, a cable drum, an open floor tile, and the quantum core landmark
(see dc_base.py for conventions)."""
import math
import random

from dc_base import *  # noqa: F401,F403
import dc_base as B

RW = 0.584       # rack cabinet width (5 to a 3 m row piece)
RD = 0.48        # half depth
RH = 2.2         # cabinet height


def side_q(m, side, x0, x1, y, z0, z1, c):
    (fq if side < 0 else bq)(m, x0, x1, y, z0, z1, c)


# ================================================================ racks
def cabinet(m, cx, kind, rnd, led, blink):
    """one cabinet at x = cx; LED quads go to the `led` / `blink` lists (x0, x1, y, z0, z1, colour, side)"""
    a, b = cx - RW / 2 + 0.004, cx + RW / 2 - 0.004
    m.bx(a, b, -RD, RD, 0.0, RH, 'graph', cull='b')
    yf, yb = -RD - 0.003, RD + 0.003
    fq(m, a + 0.035, b - 0.035, yf, 0.1, RH - 0.1, 'black')                 # perforated door field
    m.bx(b - 0.06, b - 0.035, -RD - 0.04, -RD, 1.0, 1.35, 'chrome', hull='none')   # handle
    fq(m, a + 0.035, b - 0.035, yf, RH - 0.09, RH - 0.05, 'graphL')            # top label strip
    fq(m, a + 0.1, a + 0.22, yf - 0.003, RH - 0.085, RH - 0.055, 'paper')
    # door frame stiles with three hinge knuckles, plinth kick plate and top cap on the front; kick plate on the back
    dbx(m, a + 0.006, a + 0.033, -RD, 0.01, 0.1, RH - 0.1, 'graphL')
    dbx(m, b - 0.033, b - 0.006, -RD, 0.01, 0.1, RH - 0.1, 'graphL')
    for zh in (0.35, 1.1, 1.85):
        dbx(m, a + 0.012, a + 0.027, -RD, 0.016, zh - 0.04, zh + 0.04, 'steel')
    dbx(m, a + 0.004, b - 0.004, -RD, 0.014, 0.004, 0.09, 'graphD')
    dbx(m, a + 0.004, b - 0.004, -RD, 0.012, RH - 0.045, RH - 0.004, 'graphD')
    dbx(m, a + 0.004, b - 0.004, RD, 0.012, 0.004, 0.09, 'graphD', s=1)
    x0, x1 = a + 0.06, b - 0.08
    if kind == 'A':      # 2U compute servers
        z = 0.18
        while z < RH - 0.35:
            h = 0.13 if rnd.random() < 0.6 else 0.22
            fq(m, x0, x1, yf - 0.003, z, z + h - 0.014, 'graphL')
            led.append((x1 - 0.06, x1 - 0.04, yf - 0.009, z + 0.03, z + 0.05, 'ledG' if rnd.random() < 0.7 else 'ledB', -1))
            if rnd.random() < 0.35:
                blink.append((x1 - 0.14, x1 - 0.12, yf - 0.009, z + 0.03, z + 0.05, rnd.choice(['ledG', 'cabY', 'ledB']), -1))
            z += h
    elif kind == 'B':    # network: patch panels and switches with coloured cable loops
        z = 0.2
        k = 0
        while z < RH - 0.3:
            h = 0.06
            fq(m, x0, x1, yf - 0.003, z, z + h, 'black' if k % 3 else 'graphL')
            if k % 3:
                for i in range(5):
                    xx = x0 + 0.04 + i * (x1 - x0 - 0.06) / 5
                    fq(m, xx, xx + 0.025, yf - 0.006, z + 0.015, z + 0.045, rnd.choice(['cabB', 'cabY', 'cabR', 'cabG', 'cabP', 'paper']))
                if rnd.random() < 0.5:
                    blink.append((x1 - 0.05, x1 - 0.03, yf - 0.009, z + 0.02, z + 0.04, 'ledG', -1))
            else:
                led.append((x1 - 0.05, x1 - 0.03, yf - 0.009, z + 0.02, z + 0.04, 'cabY', -1))
            z += h + 0.03
            k += 1
        for s, col in ((-1, rnd.choice(['cabB', 'cabY'])), (1, rnd.choice(['cabR', 'cabG', 'cabP']))):
            xx = a + 0.05 if s < 0 else b - 0.11
            m.bx(xx, xx + 0.06, -RD - 0.06, -RD - 0.003, 0.25, RH - 0.3, col, hull='none', cull='k')
    elif kind == 'C':    # storage: a grid of drive trays
        for r in range(9):
            z = 0.25 + r * 0.2
            for c in range(3):
                xx = x0 + c * (x1 - x0) / 3
                fq(m, xx + 0.008, xx + (x1 - x0) / 3 - 0.008, yf - 0.003, z, z + 0.16, 'steelD')
                (blink if rnd.random() < 0.3 else led).append((xx + 0.02, xx + 0.04, yf - 0.009, z + 0.02, z + 0.035, 'ledG' if rnd.random() < 0.85 else 'cabY', -1))
    else:                # AI / GPU: big units with lit fan rings
        for r in range(3):
            z = 0.3 + r * 0.6
            fq(m, x0, x1, yf - 0.003, z, z + 0.52, 'graphD')
            for c in range(2):
                fx = x0 + 0.11 + c * 0.2
                poly(m, [(fx + math.cos(j / 8 * 2 * math.pi) * 0.09, yf - 0.006, z + 0.26 + math.sin(j / 8 * 2 * math.pi) * 0.09) for j in range(8)], 'black', (0, -1, 0))
                led.append((fx - 0.08, fx + 0.08, yf - 0.009, z + 0.44, z + 0.455, 'cyan', -1))
            led.append((x1 - 0.04, x1 - 0.02, yf - 0.009, z + 0.04, z + 0.46, 'teal', -1))
    # back: rear door, two vertical PDU strips, cable bundles
    bq(m, a + 0.035, b - 0.035, yb, 0.1, RH - 0.1, 'black')
    for xx in (a + 0.06, b - 0.1):
        bq(m, xx, xx + 0.04, yb + 0.003, 0.3, RH - 0.3, 'graphL')
        for k in range(6):
            (blink if rnd.random() < 0.25 else led).append((xx + 0.01, xx + 0.03, yb + 0.006, 0.45 + k * 0.25, 0.47 + k * 0.25, 'ledG', 1))
    for i, col in enumerate(rnd.sample(['cabB', 'cabK', 'cabY', 'cabR', 'cabB', 'cabK'], 3)):
        xx = cx - 0.12 + i * 0.09
        bq(m, xx, xx + 0.05, yb + 0.003, 0.4, RH - 0.15, col)


def end_panel(m, x, sx):
    a, b = sorted((x, x + sx * 0.04))
    m.bx(a, b, -RD - 0.02, RD + 0.02, 0.0, RH + 0.05, 'wallW', cull='b')
    xs = b + 0.002 if sx > 0 else a - 0.002
    face = 'x+' if sx > 0 else 'x-'
    m.bx(a - 0.003, b + 0.003, -RD - 0.023, RD + 0.023, 1.0, 1.08, 'teal', hull='none', cull='tb')
    m.bx(a - 0.003, b + 0.003, -RD - 0.023, RD + 0.023, 0.0, 0.12, 'graph', hull='none', cull='b')
    text_side(m, 'ROW', 0.13, xs + sx * 0.002, 0.0, 1.55, 'graph', face, maxw=0.8)
    text_side(m, 'HX', 0.08, xs + sx * 0.002, 0.0, 1.36, 'tealD', face, maxw=0.8)
    # end face: cap trim and two cover battens (frame turned so the end face looks toward local -Y)
    m.push(0, 0, 90 * sx)
    yf = -(b if sx > 0 else -a)
    w = RD + 0.02
    dbx(m, -w + 0.005, w - 0.005, yf, 0.008, RH - 0.02, RH + 0.046, 'graphL')
    for xb in (-0.44, 0.44):
        dbx(m, xb - 0.009, xb + 0.009, yf, 0.006, 0.14, RH - 0.04, 'wallL')
    m.pop()


def build_racks(pal, ao):
    kinds = {'A': 'AABAA', 'C': 'CCACC', 'D': 'DDBDD'}
    pieces = [('RackRow_' + k, v, None) for k, v in kinds.items()] + [('RackRow_EndL', 'ABAAC', -1), ('RackRow_EndR', 'CAABA', 1)]
    for name, seq, end in pieces:
        m = new(pal)
        rnd = random.Random(sum(ord(ch) * (i + 1) for i, ch in enumerate(name)))
        led, blink = [], []
        for i, k in enumerate(seq):
            cabinet(m, -1.168 + i * RW, k, rnd, led, blink)
        # fibre drops from the yellow tray overhead into two cabinet tops
        for i in (1, 3):
            x = -1.168 + i * RW
            m.bx(x - 0.04, x + 0.04, -0.04, 0.04, RH, 3.1, 'cabY')
        if end:
            end_panel(m, end * 1.46, end)
        make(name, m, ao, cols=[cb(-1.5, -RD, 0.0, 1.5, RD, RH)])
        for nm, lst in (('_LED', led), ('_Blink', blink)):
            g = new(pal)
            for (x0, x1, y, z0, z1, c, s) in lst:
                side_q(g, s, x0, x1, y, z0, z1, c)
            make_glow(name + nm, g)


# ================================================================ cooling, fire, power
def build_plant(pal, ao):
    # CRAC unit [3, 1]: cabinets with louvred fronts, a status display, a duct up into the ceiling plenum
    m = new(pal)
    m.bx(-1.46, 1.46, -0.42, 0.5, 0.0, 0.12, 'graph', cull='b')
    m.bx(-1.44, 1.44, -0.4, 0.5, 0.12, 2.4, 'wallW')
    for i in range(3):
        x0 = -1.4 + i * 0.95
        fq(m, x0, x0 + 0.88, -0.403, 0.25, 2.2, 'wallL')
        slats(m, x0 + 0.06, x0 + 0.82, -0.406, 0.4, 1.5, 10, 'wallG')
        m.bx(x0 + 0.78, x0 + 0.82, -0.44, -0.4, 1.65, 1.95, 'graph', hull='none')
    m.bx(-0.55, 0.15, -0.44, -0.4, 1.7, 2.1, 'graphD')
    text_front(m, 'HELIXA COOL', 0.06, -0.403, 0.95, 2.26, 'tealD', maxw=0.8)
    fq(m, -1.44, 1.44, -0.406, 2.3, 2.35, 'teal')
    m.bx(-1.2, 1.2, -0.25, 0.5, 2.4, H, 'steelL', cull='t')
    for z in (3.2, 4.4, 5.4):
        m.bx(-1.22, 1.22, -0.27, 0.5, z, z + 0.06, 'steel', hull='none', cull='k')
    make('Crac', m, ao, cols=[cb(-1.46, -0.42, 0.0, 1.46, 0.5, 2.4)])
    g = new(pal)
    fq(g, -0.5, 0.1, -0.443, 1.75, 2.05, 'screen')
    text_front(g, '18.5 C', 0.08, -0.446, -0.2, 1.88, 'scrC', font='display', maxw=0.5)
    for k in range(4):
        fq(g, -0.48 + k * 0.08, -0.43 + k * 0.08, -0.446, 1.78, 1.82, 'scrG')
    make_glow('Crac_LED', g)
    # clean-agent suppression tanks [2, 1] on a wall rack, a manifold, a red riser to the ceiling
    m = new(pal)
    m.bx(-0.98, 0.98, -0.4, 0.45, 0.0, 0.08, 'steelD', cull='b')
    for i in range(3):
        x = -0.6 + i * 0.6
        m.cy((x, 0.0, 0.08), 0.2, 0.2, 1.45, 'fireR', seg=8)
        m.sp((x, 0.0, 1.53), 0.2, 'fireR', seg=(8, 3), scale=(1, 1, 0.5))
        m.cy((x, 0.0, 1.6), 0.05, 0.05, 0.15, 'chrome', seg=6, hull='none')
        poly(m, [(x + math.cos(j / 6 * 2 * math.pi) * 0.06, -0.212, 1.0 + math.sin(j / 6 * 2 * math.pi) * 0.06) for j in range(6)], 'paper', (0, -1, 0))
        fq(m, x - 0.12, x + 0.12, -0.203, 0.5, 0.75, 'paper')
    m.bx(-0.98, 0.98, 0.25, 0.4, 0.9, 1.0, 'steelD')
    m.cy((-0.98, 0.0, 1.85), 0.06, 0.06, 1.96, 'fireR', seg=8, rot=(0, 90, 0))
    m.cy((0.85, 0.0, 1.85), 0.06, 0.06, H - 1.85, 'fireR', seg=8, caps=False)
    m.bx(-0.3, 0.3, 0.35, 0.45, 2.1, 2.5, 'hazY')
    text_front(m, 'CLEAN AGENT', 0.05, 0.347, 0.0, 2.3, 'black', maxw=0.55)
    make('Tanks', m, ao, cols=[cb(-0.98, -0.4, 0.0, 0.98, 0.45, 1.75)])
    # UPS cabinets [3, 1]
    m = new(pal)
    for i in range(3):
        x0 = -1.45 + i * 0.97
        m.bx(x0, x0 + 0.95, -0.4, 0.45, 0.0, 2.0, 'wallG')
        fq(m, x0 + 0.05, x0 + 0.9, -0.403, 0.1, 1.9, 'wallL')
        slats(m, x0 + 0.12, x0 + 0.83, -0.406, 0.2, 0.7, 6, 'joint')
        if i == 1:
            m.bx(x0 + 0.2, x0 + 0.75, -0.44, -0.4, 1.3, 1.7, 'graphD')
    text_front(m, 'UPS', 0.12, -0.406, -1.0, 1.55, 'graph')
    text_front(m, 'UPS', 0.12, -0.406, 0.94, 1.55, 'graph')
    make('Ups', m, ao, cols=[cb(-1.45, -0.4, 0.0, 1.46, 0.45, 2.0)])
    g = new(pal)
    fq(g, -0.28, 0.27, -0.443, 1.33, 1.67, 'screen')
    for k in range(5):
        fq(g, -0.25 + k * 0.1, -0.18 + k * 0.1, -0.446, 1.38, 1.38 + 0.05 + k * 0.04, 'scrG')
    for x in (-1.0, 0.94):
        fq(g, x - 0.2, x + 0.2, -0.406, 1.25, 1.3, 'scrG')
    make_glow('Ups_LED', g)
    # battery strings [3, 1]: open racks of black blocks with red / black terminals and orange interconnects
    m = new(pal)
    for x in (-1.45, -0.02, 1.41):
        m.bx(x, x + 0.04, -0.4, 0.4, 0.0, 2.0, 'steelD')
    for z in (0.08, 0.55, 1.02, 1.49):
        m.bx(-1.41, 1.41, -0.38, 0.38, z, z + 0.04, 'steelD', hull='noside')
        for (x0, x1) in ((-1.38, -0.05), (0.05, 1.38)):
            m.bx(x0, x1, -0.3, 0.3, z + 0.04, z + 0.34, 'black')
            for i in range(5):
                x = x0 + (i + 0.5) * (x1 - x0) / 5
                fq(m, x - 0.1, x + 0.1, -0.303, z + 0.1, z + 0.22, 'graphL')
                uq(m, x - 0.09, x - 0.05, -0.2, -0.16, z + 0.343, 'cabR')
                uq(m, x + 0.05, x + 0.09, -0.2, -0.16, z + 0.343, 'paper')
            m.bx(x0 + 0.05, x1 - 0.05, -0.19, -0.17, z + 0.345, z + 0.365, 'cabO', hull='none')
    make('Batteries', m, ao, cols=[cb(-1.45, -0.4, 0.0, 1.45, 0.4, 2.0)])
    # power distribution unit [2, 1]
    m = new(pal)
    m.bx(-0.95, 0.95, -0.42, 0.42, 0.0, 1.9, 'wallW')
    m.bx(-0.97, 0.97, -0.44, 0.44, 0.0, 0.1, 'graph', hull='none', cull='b')
    for i in range(2):
        x0 = -0.9 + i * 0.92
        fq(m, x0, x0 + 0.86, -0.423, 0.2, 1.75, 'wallL')
        for r in range(6):
            for c in range(5):
                xx = x0 + 0.1 + c * 0.14
                fq(m, xx, xx + 0.07, -0.426, 0.4 + r * 0.17, 0.5 + r * 0.17, 'graphD')
    fq(m, -0.95, 0.95, -0.426, 1.8, 1.86, 'cabO')
    text_front(m, 'PDU-4', 0.07, -0.426, 0.0, 1.5, 'graph')
    make('Pdu', m, ao, cols=[cb(-0.97, -0.44, 0.0, 0.97, 0.44, 1.9)])


# ================================================================ NOC, meeting room
def chair(m, x, y, deg, c='chair'):
    m.push(x, y, deg)
    m.bx(-0.22, 0.22, -0.03, 0.03, 0.0, 0.04, 'graphD', hull='none')
    m.bx(-0.03, 0.03, -0.03, 0.03, 0.04, 0.43, 'steelD', hull='none')
    m.bx(-0.24, 0.24, -0.22, 0.24, 0.43, 0.52, c)
    m.bx(-0.22, 0.22, 0.2, 0.28, 0.55, 1.05, c)
    m.pop()


def monitor(m, g, x, y, z, deg, w=0.56, h=0.34, content='scrB', rnd=None):
    """a monitor facing +Y at (x, y) (turned by deg); its screen goes on the glow model g"""
    for M_ in (m, g):
        M_.push(x, y, deg)
    m.bx(-w / 2, w / 2, -0.02, 0.02, z, z + h, 'black')
    m.bx(-0.03, 0.03, -0.03, 0.0, z - 0.12, z, 'graphD', hull='none')
    m.bx(-0.1, 0.1, -0.08, 0.06, z - 0.13, z - 0.11, 'graphD', hull='none')
    bq(g, -w / 2 + 0.015, w / 2 - 0.015, 0.024, z + 0.015, z + h - 0.015, 'screen')
    r = rnd or random.Random(1)
    for k in range(4):
        zz = z + 0.04 + k * (h - 0.08) / 4
        bq(g, -w / 2 + 0.04, -w / 2 + 0.04 + r.uniform(0.1, w - 0.12), 0.027, zz, zz + 0.025, r.choice(['scrC', 'scrG', 'scrB', 'scrO']))
    for M_ in (m, g):
        M_.pop()


def build_rooms(pal, ao):
    # NOC desk pod [4, 2]: a curved console in three segments facing -Y (toward the video wall), monitors toward the
    # operators (+Y), two chairs
    for name, seed in (('NocDesk', 3),):
        m, g = new(pal), new(pal)
        rnd = random.Random(seed)
        for k, (cx, cy, deg) in enumerate(((-1.3, 0.1, -18), (0.0, -0.1, 0), (1.3, 0.1, 18))):
            dz = 0.006 if k == 1 else 0.0
            m.push(cx, cy, deg)
            m.bx(-0.68, 0.68, -0.4, 0.35, 0.0, 0.72 - dz, 'graph')
            m.bx(-0.7, 0.7, -0.42, 0.45, 0.72 - dz, 0.77 + dz, 'wallW')
            fq(m, -0.68, 0.68, -0.403 - dz, 0.64, 0.68, 'cyan')
            m.bx(-0.25, 0.25, 0.1, 0.3, 0.77 + dz, 0.79 + dz, 'black', hull='none')
            dbx(m, -0.66, 0.66, -0.4, 0.014, 0.004, 0.1, 'graphD')            # plinth kick plate
            for xs in (-0.34, 0.34):                                           # modesty panel joints
                dbx(m, xs - 0.008, xs + 0.008, -0.4, 0.008, 0.12, 0.62, 'graphL')
            dbx(m, -0.695, 0.695, -0.42, 0.006, 0.735, 0.765, 'steelL')         # edge band round the worktop
            m.pop()
        for k, (cx, cy, deg) in enumerate(((-1.55, -0.08, -18), (-0.95, -0.2, -18), (-0.3, -0.22, 0), (0.3, -0.22, 0), (0.95, -0.2, 18), (1.55, -0.08, 18))):
            monitor(m, g, cx, cy, 0.95, deg, rnd=rnd)
        chair(m, -0.7, 0.75, 180 + 8)
        chair(m, 0.75, 0.72, 180 - 10)
        make(name, m, ao, cols=[cb(-2.0, -0.45, 0.0, 2.0, 0.55, 0.77)])
        make_glow(name + '_LED', g)
    # meeting table [4, 2]: a rounded oak table, six chairs, a speaker puck, two open laptops
    m, g = new(pal), new(pal)
    m.bx(-1.2, 1.2, -0.5, 0.5, 0.72, 0.77, 'wood')
    for sx in (-1, 1):
        m.cy((sx * 1.2, 0, 0.724), 0.5, 0.5, 0.042, 'wood', seg=12)
        m.bx(sx * 0.9 - 0.06, sx * 0.9 + 0.06, -0.3, 0.3, 0.0, 0.72, 'graph')
    m.cy((0, 0, 0.77), 0.1, 0.1, 0.03, 'graphD', seg=10)
    for (x, y, deg) in ((-0.6, -0.85, 0), (0.6, -0.85, 0), (-0.6, 0.85, 180), (0.6, 0.85, 180)):
        chair(m, x, y, deg)
    for (x, y, deg) in ((-0.8, -0.25, 0), (0.6, 0.25, 180)):
        m.push(x, y, deg)
        m.bx(-0.17, 0.17, -0.12, 0.12, 0.77, 0.79, 'steelL')
        m.bxr(0.0, 0.13, 0.9, 0.34, 0.015, 0.22, 'steelL', rot=(-12, 0, 0))
        m.pop()
    make('MeetTable', m, ao, cols=[cb(-1.7, -0.5, 0.0, 1.7, 0.5, 0.77)])


# ================================================================ armory, gear (loot mounts: see the theme's mounts)
def build_loot(pal, ao):
    # weapon locker [3, 1]: a graphite board with four cyan-lit gun slots (guns rest 3.5 cm in front, y = 0.415)
    m = new(pal)
    m.bx(-1.48, 1.48, 0.45, 0.5, 0.0, 2.4, 'graphD')
    m.bx(-1.5, 1.5, 0.3, 0.45, 0.0, 0.5, 'graph')
    m.bx(-1.5, 1.5, 0.3, 0.45, 2.3, 2.5, 'graph')
    fq(m, -1.46, 1.46, 0.297, 0.42, 0.48, 'hazY')
    for (x0, x1) in ((-1.42, -0.1), (0.1, 1.42)):
        for (z0, z1) in ((0.8, 1.32), (1.5, 2.02)):
            for (p, q, r0, r1) in ((x0, x1, z0, z0 + 0.03), (x0, x1, z1 - 0.03, z1), (x0, x0 + 0.03, z0 + 0.03, z1 - 0.03), (x1 - 0.03, x1, z0 + 0.03, z1 - 0.03)):
                m.bx(p, q, 0.44, 0.45, r0, r1, 'graph', hull='none')
            fq(m, x0 + 0.03, x1 - 0.03, 0.447, z0 + 0.03, z0 + 0.06, 'cyan')
    m.bx(-0.04, 0.04, 0.38, 0.45, 0.5, 2.3, 'graph')
    m.bx(-0.6, 0.6, 0.27, 0.3, 2.33, 2.47, 'teal', hull='none')
    text_front(m, 'ARMORY', 0.1, 0.267, 0.0, 2.35, 'paper', maxw=1.1)
    make('Armory', m, ao, cols=[cb(-1.5, 0.3, 0.0, 1.5, 0.5, 2.5)])
    # gear locker [2, 1]: open shelving behind a mesh door swung open, two items stand on the 1.16 m shelf
    m = new(pal)
    m.bx(-0.92, 0.92, 0.42, 0.5, 0.0, 2.2, 'graph')
    for sx in (-1, 1):
        a, b = sorted((sx * 0.98, sx * 0.92))
        m.bx(a, b, -0.06, 0.5, 0.0, 2.2, 'graph')
    m.bx(-0.92, 0.92, -0.02, 0.42, 1.1, 1.16, 'steelL')
    m.bx(-0.92, 0.92, -0.04, 0.42, 0.0, 0.3, 'graph')
    m.bx(-0.92, 0.92, -0.04, 0.42, 1.95, 2.2, 'graph')
    fq(m, -0.92, 0.92, -0.043, 2.0, 2.15, 'tealD')
    text_front(m, 'GEAR', 0.09, -0.046, 0.0, 2.03, 'paper')
    for x in (-0.6, 0.0, 0.6):
        m.bx(x - 0.15, x + 0.15, 0.0, 0.38, 0.3, 0.62, rnd_pick(x))
    make('GearLocker', m, ao, cols=[cb(-0.98, -0.06, 0.0, 0.98, 0.5, 2.2)])
    # mod bench [2, 1]: a white tech bench, attachments rest on the 0.926 m top (front edge y = -0.433)
    m = new(pal)
    m.bx(-0.98, 0.98, -0.42, 0.45, 0.86, 0.926, 'wallW')
    fq(m, -0.98, 0.98, -0.423, 0.87, 0.92, 'cyan')
    for sx in (-1, 1):
        m.bx(sx * 0.9 - 0.04, sx * 0.9 + 0.04, -0.4, 0.4, 0.0, 0.86, 'graph')
    m.bx(-0.86, 0.86, -0.38, 0.38, 0.2, 0.25, 'graph', hull='none')
    m.bx(-0.95, 0.95, 0.38, 0.45, 0.926, 1.7, 'graphD')
    for k in range(4):
        x = -0.75 + k * 0.5
        m.bx(x - 0.12, x + 0.12, 0.34, 0.38, 1.25, 1.55, rnd_pick(k))
    m.bx(-0.04, 0.04, 0.2, 0.3, 0.926, 1.3, 'steelD')
    m.bxr(0.0, 0.05, 1.33, 0.06, 0.4, 0.05, 'steelD', rot=(25, 0, 0))
    m.cy((0.0, -0.12, 1.22), 0.07, 0.05, 0.08, 'graph', seg=8)
    make('ModBench', m, ao, cols=[cb(-0.98, -0.45, 0.0, 0.98, 0.45, 0.926)])


def rnd_pick(k):
    return ['steelD', 'tealD', 'graphL', 'steel'][int(abs(k * 7 + 3)) % 4]


# ================================================================ small props
def build_props(pal, ao):
    # structural column [1, 1]
    m = new(pal)
    m.bx(-0.36, 0.36, -0.36, 0.36, 0.0, H, 'wallW', cull='bt')
    m.bx(-0.38, 0.38, -0.38, 0.38, 0.0, 0.2, 'graph', hull='none', cull='b')
    m.bx(-0.363, 0.363, -0.363, 0.363, 1.0, 1.08, 'teal', hull='none', cull='tb')
    m.bx(-0.37, 0.37, -0.37, 0.37, 5.3, H, 'graph', hull='none', cull='t')
    for deg in (0, 90, 180, 270):     # base plate bolts and a guard angle up each corner
        m.push(0, 0, deg)
        dbolts(m, (-0.3, -0.1, 0.1, 0.3), 0.1, -0.38, 'steelL', d=0.012, sz=0.03)
        m.bx(0.3, 0.366, -0.366, -0.3, 0.2, 1.2, 'steelD', hull='none', cull='b')
        m.pop()
    for s in (-1, 1):
        side_q(m, s, -0.2, 0.2, s * 0.363, 2.0, 2.3, 'graph')
        (text_front if s < 0 else text_back)(m, 'C-12', 0.12, s * 0.366, 0.0, 2.07, 'paper')
    make('Column', m, ao, cols=[cb(-0.36, -0.36, 0.0, 0.36, 0.36, H)])
    # server boxes on a pallet [1, 1] (and a taller stack)
    for name, n in (('Boxes', 2), ('Boxes_B', 3)):
        m = new(pal)
        m.bx(-0.45, 0.45, -0.45, 0.45, 0.0, 0.12, 'woodD')
        rnd = random.Random(n)
        z = 0.12
        for k in range(n):
            w, d, h = rnd.uniform(0.7, 0.85), rnd.uniform(0.55, 0.8), rnd.uniform(0.3, 0.42)
            dx, dy = rnd.uniform(-0.04, 0.04), rnd.uniform(-0.05, 0.05)
            m.bx(dx - w / 2, dx + w / 2, dy - d / 2, dy + d / 2, z, z + h, 'cardb')
            fq(m, dx - 0.15, dx + 0.15, dy - d / 2 - 0.003, z + 0.08, z + h - 0.08, 'paper')
            text_front(m, 'HELIXA', 0.04, dy - d / 2 - 0.006, dx, z + h / 2 - 0.02, 'tealD', maxw=0.26)
            uq(m, dx - w / 2, dx + w / 2, dy - 0.04, dy + 0.04, z + h + 0.003, 'tileD')
            z += h
        make(name, m, ao, cols=[cb(-0.45, -0.45, 0.0, 0.45, 0.45, z)])
    # crash cart [1, 1]: a trolley with a monitor, keyboard and a coil of cable
    m, g = new(pal), new(pal)
    m.bx(-0.32, 0.32, -0.25, 0.25, 0.85, 0.89, 'graph')
    m.bx(-0.32, 0.32, -0.25, 0.25, 0.25, 0.29, 'graph')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.29 - 0.02, sx * 0.29 + 0.02, sy * 0.22 - 0.02, sy * 0.22 + 0.02, 0.1, 0.85, 'steelD', hull='none')
            m.cy((sx * 0.27, sy * 0.2, 0.0), 0.05, 0.05, 0.1, 'black', seg=6, hull='none')
    m.bx(-0.2, 0.2, -0.2, 0.02, 0.89, 0.91, 'black', hull='none')
    monitor(m, g, 0.0, 0.12, 1.02, 180, w=0.42, h=0.28, rnd=random.Random(4))
    torus(m, 0.0, 0.0, 0.33, 0.14, 0.03, 'cabB', seg=10, sides=4, axis='z')
    make('CrashCart', m, ao, cols=[cb(-0.32, -0.25, 0.0, 0.32, 0.25, 0.91)])
    make_glow('CrashCart_LED', g)
    # cable drum [1, 1]
    m = new(pal)
    for sy in (-1, 1):
        m.cy((0, sy * 0.28, 0.42), 0.42, 0.42, 0.06, 'wood', seg=12, rot=(90, 0, 0))
    m.cy((0, -0.25, 0.42), 0.32, 0.32, 0.5, 'cabY', seg=12, rot=(-90, 0, 0))
    make('CableDrum', m, ao, cols=[cb(-0.42, -0.34, 0.0, 0.42, 0.34, 0.84)])
    # an open floor tile: the cable well under the raised floor, the lifted tile leaning on a cone, the suction lifter
    m = new(pal)
    uq(m, -0.3, 0.3, -0.3, 0.3, 0.009, 'black')
    for k, c in enumerate(('cabB', 'cabY', 'cabK')):
        uq(m, -0.3, 0.3, -0.2 + k * 0.15, -0.14 + k * 0.15, 0.012, c)
    m.bxr(0.36, 0.28, 0.3, 0.03, 0.6, 0.6, 'tile', rot=(0, -20, 0))
    for (x, y) in ((-0.38, -0.38), (0.38, -0.38)):
        m.cy((x, y, 0.0), 0.1, 0.02, 0.45, 'cabO', seg=8)
        m.bx(x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.0, 0.03, 'cabO', hull='none', cull='b')
        m.cy((x, y, 0.18), 0.07, 0.055, 0.08, 'paper', seg=8, hull='none')
    m.bx(-0.45, 0.45, -0.385, -0.375, 0.32, 0.36, 'hazY', hull='none')
    make('TileOpen', m, ao, cols=[cb(-0.5, -0.5, 0.0, 0.5, 0.5, 0.5)])


# ================================================================ quantum core (zone 2 landmark) [4, 4]
def build_quantum(pal, ao):
    m, g = new(pal), new(pal)
    m.cy((0, 0, 0.0), 1.9, 1.9, 0.25, 'graph', seg=16)
    ring(m, 0, 0, 0.253, 1.55, 1.7, 'cyan', seg=16)
    m.cy((0, 0, 0.25), 1.1, 1.1, 0.12, 'graphL', seg=12)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = sx * 1.05, sy * 1.05
        m.bx(x - 0.09, x + 0.09, y - 0.09, y + 0.09, 0.37, 4.6, 'steelL')
        m.bx(x - 0.093, x + 0.093, y - 0.093, y + 0.093, 1.4, 1.46, 'teal', hull='none', cull='tb')
    m.bx(-1.25, 1.25, -1.25, 1.25, 4.6, 4.9, 'graph')
    m.cy((0, 0, 4.9), 0.6, 0.6, 1.1, 'graphD', seg=12)                           # cryostat top, into the ceiling
    # the gold chandelier: five plates on rods, copper coax coils between them
    plates = [(4.4, 0.82), (3.6, 0.66), (2.8, 0.5), (2.0, 0.36)]
    for z, r in plates:
        m.cy((0, 0, z), r, r, 0.07, 'gold', seg=12)
        ring(g, 0, 0, z - 0.004, r * 0.55, r * 0.62, 'cyanL', seg=12, normal=(0, 0, -1))
    for k in range(4):
        a = k / 4 * 2 * math.pi
        for (z0, r0), (z1, r1) in zip(plates, plates[1:]):
            m.bm_((math.cos(a) * r1 * 0.85, math.sin(a) * r1 * 0.85, z1 + 0.07), (math.cos(a) * r1 * 0.85, math.sin(a) * r1 * 0.85, z0), 0.035, 'gold', hull='none')
    for (z0, r0), (z1, r1) in zip(plates, plates[1:]):
        m.cy((0, 0, z1 + 0.07), r1 * 0.3, r1 * 0.3, z0 - z1 - 0.07, 'copper', seg=8)
    m.cy((0, 0, 1.6), 0.18, 0.12, 0.4, 'gold', seg=8)                           # mixing chamber
    g.sp((0, 0, 1.42), 0.14, 'cyan', seg=(8, 5))
    # a waist-high safety rail round it with two warning plaques
    torus(m, 0, 0, 1.0, 1.82, 0.03, 'steelL', seg=16, sides=4, axis='z')
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        m.cy((math.cos(a) * 1.82, math.sin(a) * 1.82, 0.25), 0.03, 0.03, 0.73, 'steelL', seg=6)
    for s in (-1, 1):
        m.bx(-0.3, 0.3, s * 1.86 - 0.01, s * 1.86 + 0.01, 0.55, 0.85, 'hazY', hull='none')
    text_front(m, 'QC-1  -273 C', 0.07, -1.873, 0.0, 0.66, 'black', maxw=0.55)
    make('Landmark_Quantum', m, ao, cols=[cb(-1.9, -1.9, 0.0, 1.9, 1.9, 1.05), cb(-1.25, -1.25, 4.6, 1.25, 1.25, 6.0)])
    make_glow('Landmark_Quantum_LED', g)
