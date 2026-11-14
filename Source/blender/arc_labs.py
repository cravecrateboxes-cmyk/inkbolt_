"""kit-arctic zone 2 props: the drill-core archive (core-tube racks with end panels, logging tables, core boxes), the
cryo lab (sample tanks, dewars, ultra-low freezers, benches, a glove box), the generator hall (gensets, the boiler,
pipe runs, the day tank, switchboard, pumps), the vault's loot (weapon locker, gear locker), ice pillars and spikes,
and the landmark: an ancient ring machine half swallowed by the ice wall of the cavern the drill broke into.
See arc_base.py for conventions."""
import math

from arc_base import *  # noqa: F401,F403
import arc_base as B
import arc_detail as AD


def ring_y(m, x, y, z, r, c, seg=8, w=0.012, face=-1):
    """a thin painted ring (circle outline) on a -Y facing plane"""
    for i in range(seg):
        a0, a1 = i / seg * 2 * math.pi, (i + 1) / seg * 2 * math.pi
        poly(m, [(x + math.cos(a0) * r, y, z + math.sin(a0) * r), (x + math.cos(a1) * r, y, z + math.sin(a1) * r),
                 (x + math.cos(a1) * (r - w), y, z + math.sin(a1) * (r - w)), (x + math.cos(a0) * (r - w), y, z + math.sin(a0) * (r - w))], c, (0, face, 0))


def build_archive(pal, ao):
    # ---- core-tube rack [3, 1]: four shelves, rows of core tubes both sides, labels; end panels cap a run
    def rack(m, end):
        for x in (-1.45, 0.0, 1.45):
            m.bx(x - 0.04, x + 0.04, -0.47, 0.47, 0.0, 2.4, 'steelD')
        for z in (0.1, 0.68, 1.26, 1.84):
            m.bx(-1.5, 1.5, -0.45, 0.45, z, z + 0.04, 'galv', hull='noside')
            for s in (-1, 1):
                m.cy((-1.41, s * 0.25, z + 0.04 + 0.17), 0.17, 0.17, 2.82, 'tube' if (z > 1) else 'coreB', seg=6, rot=(0, 90, 0), caps=False, hull='noside')
                (fq if s < 0 else bq)(m, -1.4, 1.4, s * 0.453, z - 0.06, z, 'steelK')
                for i in range(6):
                    xx = -1.3 + i * 0.5
                    (fq if s < 0 else bq)(m, xx, xx + 0.14, s * 0.456, z - 0.05, z - 0.01, 'paper')
        if end:   # the end panel: a solid steel side with the section sign
            x = -1.5 if end == 'L' else 1.5
            sx = -1 if end == 'L' else 1
            m.bx(min(x, x + sx * 0.06), max(x, x + sx * 0.06), -0.48, 0.48, 0.0, 2.45, 'blueP')
            xs = x + sx * 0.063
            poly(m, [(xs, -0.35, 1.7), (xs, 0.35, 1.7), (xs, 0.35, 2.2), (xs, -0.35, 2.2)], 'paper', (sx, 0, 0))
            text_side(m, 'CORES', 0.14, xs + sx * 0.003, 0.0, 1.85, 'blueP', 'x-' if sx < 0 else 'x+')
    for v, end in (('CoreRack_A', None), ('CoreRack_EndL', 'L'), ('CoreRack_EndR', 'R')):
        m = new(pal); rack(m, end); AD.rack(m, end)
        x0 = -1.56 if end == 'L' else -1.5
        x1 = 1.56 if end == 'R' else 1.5
        make(v, m, ao, cols=[cb(x0, -0.46, 0, x1, 0.46, 2.45)])
    # ---- logging table [3, 2]: a core in its half tray, lamps, the measuring rule; B: the band saw
    for v in ('A', 'B'):
        m = new(pal)
        m.bx(-1.4, 1.4, -0.7, 0.7, 0.86, 0.92, 'steelL')
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.bx(sx * 1.3 - 0.04, sx * 1.3 + 0.04, sy * 0.6 - 0.04, sy * 0.6 + 0.04, 0.0, 0.86, 'steelD')
        m.bx(-1.2, 1.2, -0.1, 0.18, 0.92, 0.97, 'steelD')
        m.cy((-1.1, 0.04, 1.03), 0.08, 0.08, 2.2, 'core', seg=8, rot=(0, 90, 0))
        for k in range(6):
            uq(m, -1.1 + k * 0.4, -1.08 + k * 0.4, -0.25, -0.12, 0.923, 'black')
        if v == 'A':
            m.bm_((0.9, 0.5, 0.92), (0.7, 0.3, 1.5), 0.03, 'steelK')
            m.cy((0.6, 0.2, 1.42), 0.15, 0.06, 0.16, 'blueP', seg=8)
            for k in range(3):
                uq(m, -0.9 + k * 0.25, -0.7 + k * 0.25, 0.3, 0.55, 0.923 + k * 0.003, 'paper')
        else:
            m.bx(0.3, 1.2, 0.2, 0.62, 0.92, 1.9, 'steelL')
            m.bx(0.35, 1.15, 0.0, 0.2, 1.5, 1.9, 'steelL')
            m.bx(0.68, 0.72, 0.03, 0.17, 0.95, 1.5, 'steelD', hull='none')
            fq(m, 0.32, 0.6, 0.197, 1.7, 1.85, 'orange')
            m.bx(-0.4, 0.2, 0.2, 0.6, 0.92, 1.2, 'coreB')
        make('CoreTable_' + v, m, ao, cols=[cb(-1.4, -0.7, 0, 1.4, 0.7, 0.92)] + ([cb(0.3, 0.0, 0.92, 1.2, 0.62, 1.9)] if v == 'B' else []))
    # ---- core shipping boxes (1 cell)
    m = new(pal)
    for k, (x, y, w) in enumerate(((0.0, -0.18, 0.42), (0.02, 0.2, 0.4))):
        m.bx(x - w, x + w, y - 0.17, y + 0.17, 0.0, 0.3, 'blueP')
        fq(m, x - w * 0.6, x + w * 0.6, y - 0.173, 0.08, 0.22, 'paper')
    m.bx(-0.4, 0.4, -0.35, 0.35, 0.3, 0.6, 'steelL')
    fq(m, -0.2, 0.2, -0.353, 0.38, 0.52, 'orange')
    uq(m, -0.35, 0.2, -0.3, 0.25, 0.603, 'frost')
    make('CoreBoxes', m, ao, cols=[cb(-0.42, -0.36, 0, 0.42, 0.37, 0.6)])


def build_cryo(pal, ao):
    # ---- sample tank [2, 2]: a big LN2 dewar, lid, control box with its display (glow), frost, hose
    m = new(pal); g = new(pal)
    m.cy((0, 0.05, 0), 0.78, 0.78, 1.3, 'steelL', seg=12)
    m.cy((0, 0.05, 1.3), 0.7, 0.62, 0.12, 'steel', seg=12)
    m.cy((0, 0.05, 1.42), 0.18, 0.18, 0.1, 'steelD', seg=8)
    m.cy((0, 0.05, 0.25), 0.785, 0.785, 0.08, 'blueP', seg=12, hull='none', caps=False)
    m.bx(-0.3, 0.3, -0.92, -0.72, 0.6, 1.1, 'panelW')
    fq(m, -0.24, 0.24, -0.923, 0.8, 1.04, 'scr')
    text_front(g, '-196 C', 0.07, -0.926, 0.0, 0.88, 'glowC', maxw=0.4)
    fq(g, -0.2, -0.12, -0.926, 0.97, 1.01, 'scrG')
    make_glow('CryoTank_LED', g)
    tube(m, (0.6, -0.4, 0.5), (0.85, -0.85, 0.05), 0.04, 'black', seg=6, hull='none')
    for k in range(5):
        a = k * 1.3 + 0.4
        hullp(m, [(math.cos(a) * 0.79, 0.05 + math.sin(a) * 0.79, 0.0), (math.cos(a + 0.25) * 0.79, 0.05 + math.sin(a + 0.25) * 0.79, 0.0),
                  (math.cos(a + 0.12) * 0.8, 0.05 + math.sin(a + 0.12) * 0.8, 0.35 + k * 0.08)], 'frost', hull='none')
    make('CryoTank', m, ao, cols=[cb(-0.78, -0.73, 0, 0.78, 0.83, 1.42), cb(-0.3, -0.92, 0.6, 0.3, -0.72, 1.1)])
    # ---- dewars on a trolley (1 cell)
    m = new(pal)
    m.bx(-0.42, 0.42, -0.3, 0.3, 0.12, 0.16, 'steelK')
    for (x, y) in ((-0.42, -0.3), (0.42, -0.3), (-0.42, 0.3), (0.42, 0.3)):
        m.cy((x * 0.9, y * 0.9, 0.0), 0.05, 0.05, 0.12, 'black', seg=6, hull='none')
    for x, h in ((-0.2, 0.75), (0.2, 0.6)):
        m.cy((x, 0.0, 0.16), 0.18, 0.18, h, 'steelL', seg=8)
        m.cy((x, 0.0, 0.16 + h), 0.07, 0.07, 0.12, 'blueP', seg=6)
    m.bm_((0.42, 0.0, 0.16), (0.48, 0.0, 1.0), 0.03, 'steelK')
    make('Dewars', m, ao, cols=[cb(-0.42, -0.3, 0, 0.42, 0.3, 0.9)])
    # ---- ultra-low freezers [2, 1] (back on +Y): two upright units, frosted doors, status displays (glow)
    m = new(pal); g = new(pal)
    for x in (-0.47, 0.47):
        m.bx(x - 0.45, x + 0.45, -0.38, 0.48, 0.0, 1.95, 'panelW', cull='k')
        fq(m, x - 0.4, x + 0.4, -0.383, 0.15, 1.55, 'panelG')
        m.bx(x + 0.3, x + 0.36, -0.44, -0.383, 0.7, 1.2, 'steelD', hull='none')
        fq(m, x - 0.3, x + 0.1, -0.383, 1.65, 1.85, 'scrDead')
        fq(g, x - 0.28, x - 0.02, -0.386, 1.7, 1.8, 'scrG' if x < 0 else 'glowC')
        frost_spots(m, RND(700 + int(x * 10)), x - 0.38, x + 0.38, 0.2, 1.5, -0.386, 6)
    text_front(m, '-80 C', 0.08, -0.386, -0.47, 1.58, 'blueP')
    make('Freezer', m, ao, cols=[cb(-0.92, -0.38, 0, 0.92, 0.48, 1.95)])
    make_glow('Freezer_LED', g)
    # ---- lab bench [3, 1] (an island, both sides): reagent shelf, microscope, sample racks
    m = new(pal)
    rnd = RND(710)
    m.bx(-1.45, 1.45, -0.45, 0.45, 0.86, 0.92, 'panelW')
    m.bx(-1.4, 1.4, -0.4, 0.4, 0.0, 0.86, 'panelG', cull='t')
    for s in (-1, 1):
        for k in range(4):
            (fq if s < 0 else bq)(m, -1.3 + k * 0.68, -0.72 + k * 0.68, s * 0.403, 0.1, 0.78, 'panelB')
    for x in (-1.3, 1.3):
        m.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0.92, 1.8, 'steelD')
    m.bx(-1.35, 1.35, -0.15, 0.15, 1.5, 1.54, 'galv')
    for i in range(8):
        x = -1.2 + i * 0.32
        m.cy((x, 0.0, 1.54), 0.05, 0.05, rnd.uniform(0.12, 0.24), rnd.choice(['glass', 'blueP', 'orange', 'glassD']), seg=6)
    m.bx(-0.9, -0.6, -0.35, -0.1, 0.92, 0.98, 'black')
    m.bm_((-0.75, -0.2, 0.98), (-0.75, -0.25, 1.35), 0.06, 'black')
    m.cy((-0.75, -0.33, 1.15), 0.035, 0.035, 0.2, 'steelL', seg=6)
    for x in (0.3, 0.8):
        m.bx(x - 0.18, x + 0.18, 0.1, 0.32, 0.92, 1.0, 'blueP')
        for i in range(4):
            m.cy((x - 0.12 + i * 0.08, 0.21, 1.0), 0.022, 0.022, 0.1, 'iceL', seg=5, hull='none')
    make('LabBench', m, ao, cols=[cb(-1.45, -0.45, 0, 1.45, 0.45, 0.92)])
    # ---- glove box [3, 1] (back on +Y)
    m = new(pal)
    m.bx(-1.4, 1.4, -0.35, 0.48, 0.0, 0.9, 'steelL', cull='k')
    m.prism([(-0.35, 0.9), (0.48, 0.9), (0.48, 1.9), (0.1, 1.9), (-0.35, 1.25)], -1.3, 1.3, ['steelD'], skip=(0,))
    poly(m, [(-1.25, -0.355, 0.95), (1.25, -0.355, 0.95), (1.25, 0.08, 1.85), (-1.25, 0.08, 1.85)], 'glassD', (0, -1, 0.5))
    for x in (-0.55, 0.55):
        m.cy((x, -0.15, 1.2), 0.12, 0.12, 0.02, 'black', seg=8, rot=(-64, 0, 0), hull='none')
    fq(m, -1.3, 1.3, -0.353, 0.7, 0.8, 'orange')
    text_front(m, 'INERT ATMOSPHERE', 0.06, -0.356, -0.6, 0.72, 'black', maxw=1.2)
    make('GloveBox', m, ao, cols=[cb(-1.4, -0.35, 0, 1.4, 0.48, 1.9)])


def build_power(pal, ao):
    # ---- genset [4, 6]: engine block on a skid, alternator, radiator, an exhaust stack
    m = new(pal)
    m.bx(-1.8, 1.8, -2.8, 2.8, 0.0, 0.3, 'steelK')
    m.bx(-1.1, 1.1, -1.6, 1.4, 0.3, 1.9, 'blueP')
    for k in range(6):
        y = -1.4 + k * 0.48
        m.cy((1.1, y, 1.5), 0.13, 0.13, 0.12, 'steelD', seg=6, rot=(0, 90, 0))
        m.cy((-1.1, y, 1.5), 0.13, 0.13, 0.12, 'steelD', seg=6, rot=(0, -90, 0))
    m.bx(-0.9, 0.9, -1.5, 1.3, 1.9, 2.15, 'steelD')
    m.cy((0.0, 1.4, 1.1), 0.75, 0.75, 1.2, 'steelL', seg=10, rot=(-90, 0, 0))
    m.bx(-1.2, 1.2, -2.6, -1.6, 0.3, 2.3, 'steelD')
    for k in range(8):
        fq(m, -1.1, 1.1, -2.603, 0.45 + k * 0.22, 0.55 + k * 0.22, 'black')
    m.cy((0.6, -0.5, 2.15), 0.16, 0.16, 2.6, 'steel', seg=8)
    m.cy((0.6, -0.5, 4.75), 0.2, 0.2, 0.1, 'black', seg=8, hull='none')
    m.bx(-1.6, -1.2, 1.0, 2.6, 0.3, 1.8, 'steelL')
    lq(m, -1.603, 1.2, 2.4, 1.2, 1.65, 'steelD')
    text_side(m, 'GEN 2', 0.3, -1.103, -0.2, 0.9, 'paper', 'x-', maxw=1.5)
    text_side(m, 'GEN 2', 0.3, 1.103, -0.2, 0.9, 'paper', 'x+', maxw=1.5)
    for k in range(3):
        hullp(m, [(-1.0 + k * 0.8, -1.6, 2.15), (-0.6 + k * 0.8, -1.6, 2.15), (-0.8 + k * 0.8, -1.4, 2.4)], 'frost', hull='none')
    AD.gen_set(m)
    make('GenSet', m, ao, cols=[cb(-1.8, -2.8, 0, 1.8, 2.8, 0.3), cb(-1.2, -2.6, 0.3, 1.2, 2.1, 2.15), cb(-1.6, 1.0, 0.3, -1.2, 2.6, 1.8)])
    # ---- boiler [4, 4]: vertical fire-tube boiler, burner, insulation bands, pipes up into the ice
    m = new(pal)
    m.bx(-1.8, 1.8, -1.8, 1.8, 0.0, 0.25, 'steelK')
    m.cy((0, 0.2, 0.24), 1.3, 1.3, 3.61, 'redE', seg=12)
    for z in (0.9, 1.9, 2.9):
        m.cy((0, 0.2, z), 1.31, 1.31, 0.1, 'steelL', seg=12, hull='none', caps=False)
    m.cy((0, 0.2, 3.85), 1.25, 0.5, 0.5, 'steelD', seg=12)
    m.cy((0, 0.2, 4.35), 0.32, 0.32, 3.0, 'steel', seg=8)
    m.bx(-0.55, 0.55, -1.75, -0.95, 0.25, 1.3, 'steelL', cull='b')
    m.cy((0, -1.75, 0.8), 0.25, 0.25, 0.06, 'black', seg=8, rot=(90, 0, 0))
    tube(m, (1.1, -0.5, 2.6), (1.7, -1.2, 2.6), 0.14, 'steelL', seg=8)
    tube(m, (1.7, -1.2, 2.6), (1.7, -1.2, 5.8), 0.14, 'steelL', seg=8)
    m.cy((-1.0, -1.0, 2.4), 0.18, 0.18, 0.06, 'paper', seg=8, rot=(90, 0, 30), hull='none')
    AD.boiler(m)
    make('Boiler', m, ao, cols=[cb(-1.8, -1.8, 0, 1.8, 1.8, 0.25), cb(-1.2, -1.0, 0.25, 1.2, 1.4, 3.6), cb(-0.55, -1.75, 0.25, 0.55, -0.95, 1.3)])
    # ---- pipe run (1 cell, along X): two big insulated pipes on a stand
    m = new(pal)
    m.bx(-0.06, 0.06, -0.4, 0.4, 0.0, 0.85, 'steelD')
    m.bx(-0.08, 0.08, -0.45, 0.45, 0.85, 0.9, 'steelK')
    for y, c in ((-0.22, 'steelL'), (0.22, 'orangeD')):
        m.cy((-0.5, y, 1.08), 0.18, 0.18, 1.0, c, seg=8, rot=(0, 90, 0), caps=False, hull='noside')
        m.cy((-0.5 + 0.45, y, 1.08), 0.19, 0.19, 0.1, 'steel', seg=8, rot=(0, 90, 0), caps=False, hull='none')
    make('PipeRun', m, ao, cols=[cb(-0.5, -0.42, 0, 0.5, 0.42, 1.27)])
    # ---- day tank [3, 2]
    m = new(pal)
    m.bx(-1.4, 1.4, -0.85, 0.85, 0.0, 0.3, 'steelK')
    m.bx(-1.3, 1.3, -0.75, 0.75, 0.3, 1.6, 'yel')
    fq(m, -1.3, 1.3, -0.753, 1.2, 1.32, 'black')
    text_front(m, 'DAY TANK', 0.22, -0.756, 0.0, 0.7, 'black', maxw=1.8)
    m.cy((0.9, 0.3, 1.6), 0.1, 0.1, 0.3, 'steelD', seg=6)
    uq(m, -1.2, 0.5, -0.6, 0.6, 1.603, 'frost')
    AD.day_tank(m)
    make('DayTank', m, ao, cols=[cb(-1.4, -0.85, 0, 1.4, 0.85, 1.6)])
    # ---- switchboard [4, 1] (back on +Y)
    m = new(pal)
    rnd = RND(720)
    m.bx(-1.95, 1.95, -0.2, 0.48, 0.0, 2.2, 'steelL', cull='k')
    for k in range(4):
        x = -1.45 + k * 0.97
        fq(m, x - 0.42, x + 0.42, -0.203, 0.15, 2.05, 'panelG')
        for i in range(3):
            fq(m, x - 0.28 + i * 0.2, x - 0.16 + i * 0.2, -0.206, 1.6, 1.72, 'paper')
        m.bx(x + 0.25, x + 0.31, -0.26, -0.2, 0.9, 1.2, 'black', hull='none')
        fq(m, x - 0.3, x + 0.1, -0.206, 0.4, 0.55, 'orange' if k % 2 else 'yel')
    frost_spots(m, rnd, -1.9, 1.9, 1.8, 2.15, -0.209, 6)
    AD.switchboard(m)
    make('Switchboard', m, ao, cols=[cb(-1.95, -0.2, 0, 1.95, 0.48, 2.2)])
    # ---- pump [2, 1]
    m = new(pal)
    m.bx(-0.95, 0.95, -0.4, 0.4, 0.0, 0.2, 'steelK')
    m.cy((-0.7, 0.0, 0.55), 0.3, 0.3, 0.9, 'blueP', seg=10, rot=(0, 90, 0))
    m.cy((0.35, 0.0, 0.2), 0.32, 0.32, 0.5, 'steelD', seg=10)
    tube(m, (0.35, 0.0, 0.7), (0.35, 0.0, 1.3), 0.11, 'steelL', seg=8)
    tube(m, (0.67, 0.0, 0.45), (0.95, 0.0, 0.45), 0.11, 'steelL', seg=8)
    make('Pump', m, ao, cols=[cb(-0.95, -0.4, 0, 0.95, 0.4, 0.85)])


def build_vault(pal, ao):
    # weapon locker [3, 1]: four gun slots (guns rest 3.5 cm in front of the board, y = 0.415), lit by a dead tube
    m = new(pal)
    m.bx(-1.48, 1.48, 0.45, 0.5, 0.0, 2.4, 'steelK')
    m.bx(-1.5, 1.5, 0.3, 0.45, 0.0, 0.5, 'steelD')
    m.bx(-1.5, 1.5, 0.3, 0.45, 2.3, 2.5, 'steelD')
    fq(m, -1.46, 1.46, 0.297, 0.42, 0.48, 'orange')
    for (x0, x1) in ((-1.42, -0.1), (0.1, 1.42)):
        for (z0, z1) in ((0.8, 1.32), (1.5, 2.02)):
            for (p, q, r0, r1) in ((x0, x1, z0, z0 + 0.03), (x0, x1, z1 - 0.03, z1), (x0, x0 + 0.03, z0 + 0.03, z1 - 0.03), (x1 - 0.03, x1, z0 + 0.03, z1 - 0.03)):
                m.bx(p, q, 0.44, 0.45, r0, r1, 'steelD', hull='none')
            fq(m, x0 + 0.03, x1 - 0.03, 0.447, z0 + 0.03, z0 + 0.06, 'orange')
    m.bx(-0.04, 0.04, 0.38, 0.45, 0.5, 2.3, 'steelD')
    text_front(m, 'SECURITY', 0.1, 0.297, 0.0, 2.35, 'orange', maxw=1.1)
    make('Armory', m, ao, cols=[cb(-1.5, 0.3, 0.0, 1.5, 0.5, 2.5)])
    # gear locker [2, 1]: open shelving, two items stand on the 1.16 m shelf
    m = new(pal)
    m.bx(-0.92, 0.92, 0.42, 0.5, 0.0, 2.2, 'steelK')
    for sx in (-1, 1):
        a, b = sorted((sx * 0.98, sx * 0.92))
        m.bx(a, b, -0.06, 0.5, 0.0, 2.2, 'steelD')
    m.bx(-0.92, 0.92, -0.02, 0.42, 1.1, 1.16, 'steelL')
    m.bx(-0.92, 0.92, -0.04, 0.42, 0.0, 0.3, 'steelD')
    m.bx(-0.92, 0.92, -0.04, 0.42, 1.95, 2.2, 'steelD')
    fq(m, -0.92, 0.92, -0.043, 2.0, 2.15, 'blueP')
    text_front(m, 'GEAR', 0.09, -0.046, 0.0, 2.03, 'paper')
    for i, x in enumerate((-0.6, 0.0, 0.6)):
        m.bx(x - 0.15, x + 0.15, 0.0, 0.38, 0.3, 0.62, ['orange', 'steelL', 'blueP'][i])
    make('GearLocker', m, ao, cols=[cb(-0.98, -0.06, 0.0, 0.98, 0.5, 2.2)])


def build_ice(pal, ao):
    # ---- ice pillar [2, 2]: a column of glacier ice floor to ceiling (12 m)
    m = new(pal)
    rnd = RND(730)
    z = 0.0
    for k, (r0, r1, h) in enumerate(((0.95, 0.72, 4.2), (0.72, 0.66, 4.0), (0.66, 0.95, 3.8))):   # a waisted column
        pts = [(math.cos(a / 8 * 6.283 + k) * r0 * rnd.uniform(0.9, 1.0), math.sin(a / 8 * 6.283 + k) * r0 * 0.9 * rnd.uniform(0.9, 1.0), z) for a in range(8)]
        pts += [(math.cos(a / 8 * 6.283 + k + 0.3) * r1 * rnd.uniform(0.9, 1.0), math.sin(a / 8 * 6.283 + k + 0.3) * r1 * 0.9 * rnd.uniform(0.9, 1.0), z + h + 0.05) for a in range(8)]
        hullp(m, pts, ['ice', 'iceM', 'iceL'][k])
        z += h
    make('IcePillar', m, ao, cols=[cb(-0.75, -0.7, 0, 0.75, 0.7, 2.4)])
    # ---- ice spike (1 cell): a short cone of floor ice, cover
    m = new(pal)
    rnd = RND(731)
    lump(m, rnd, 0.0, 0.0, 0.45, 0.42, 1.25, 0.0, 'ice', n=6, top=1)
    lump(m, rnd, 0.2, -0.2, 0.22, 0.2, 0.6, 0.0, 'iceL', n=5, top=1)
    make('IceSpike', m, ao, cols=[cb(-0.38, -0.36, 0, 0.38, 0.36, 1.0)])


def build_relic(pal, ao):
    """[14, 6], against the cavern's north wall (+Y): a colossal segmented ring standing on a stepped plinth, a dark
    recessed disc inside it scored with glyph rings (glow companion, pulsing), two leaning pylons, all of it half
    swallowed by glacier ice"""
    m = new(pal); g = new(pal)
    rnd = RND(740)
    for k, (w, d, h) in enumerate(((6.6, 2.9, 0.35), (5.8, 2.5, 0.7), (5.0, 2.1, 1.05))):
        m.bx(-w, w, 2.9 - d * 2 + (0.1 if k else 0.0), 2.95, h - 0.35, h, 'relD' if k % 2 else 'relK', hull='full', cull='b')
    CX, CY, CZ, R1, R0 = 0.0, 2.1, 5.9, 4.9, 3.7
    N = 16
    for i in range(N):
        a0 = (i + 0.06) / N * 2 * math.pi
        a1 = (i + 0.94) / N * 2 * math.pi
        if math.sin((a0 + a1) / 2) < -0.82:
            continue   # the bottom segments are under the plinth
        pts = []
        for a in (a0, a1):
            for r in (R0, R1):
                for y in (CY - 0.55, CY + 0.5):
                    pts.append((CX + math.cos(a) * r, y, CZ + math.sin(a) * r))
        hullp(m, pts, 'relK' if i % 2 else 'relD')
        am = (a0 + a1) / 2
        u = (-math.sin(am), math.cos(am))
        rc = (R0 + R1) / 2
        x, z = CX + math.cos(am) * rc, CZ + math.sin(am) * rc
        for (du, dr, c) in ((0.0, 0.0, 'relM'), (0.0, 0.3, 'relM')):
            hw = 0.38 if dr == 0 else 0.2
            pp = [(x + u[0] * s1 * hw + math.cos(am) * (dr + s2 * 0.18), CY - 0.556 - dr * 0.01, z + u[1] * s1 * hw + math.sin(am) * (dr + s2 * 0.18)) for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            poly(m, pp, c, (0, -1, 0))
        pp = [(x + u[0] * s1 * 0.12 + math.cos(am) * (-0.35 + s2 * 0.06), CY - 0.562, z + u[1] * s1 * 0.12 + math.sin(am) * (-0.35 + s2 * 0.06)) for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        poly(g, pp, 'relG', (0, -1, 0))
    # the dark disc inside the ring and its glyph rings
    pts = [(CX + math.cos(a / 16 * 6.283) * R0, CY + 0.3, CZ + math.sin(a / 16 * 6.283) * R0) for a in range(16)]
    poly(m, pts, 'relK', (0, -1, 0))
    for r in (3.2, 2.3, 1.4):
        ring_y(g, CX, CY + 0.297, CZ, r, 'relG', seg=16, w=0.06)
    m.cy((CX, CY + 0.3, CZ), 0.8, 0.55, 0.6, 'relM', seg=10, rot=(90, 0, 0))
    poly(g, [(CX + math.cos(a / 10 * 6.283) * 0.42, CY - 0.304, CZ + math.sin(a / 10 * 6.283) * 0.42) for a in range(10)], 'relG', (0, -1, 0))
    # two pylons leaning in, frozen at their feet
    for sx in (-1, 1):
        x = sx * 6.0
        m.bxr(x, 1.6, 3.2, 0.9, 0.9, 6.4, 'relD', rot=(0, sx * -8, 0))
        poly(m, [(x - sx * 0.25 - 0.15, 1.144, 3.0), (x - sx * 0.25 + 0.15, 1.144, 3.0), (x - sx * 0.1 + 0.15, 1.144, 5.2), (x - sx * 0.1 - 0.15, 1.144, 5.2)], 'relM', (0, -1, 0))
        poly(g, [(x - sx * 0.2 - 0.05, 1.141, 3.4), (x - sx * 0.2 + 0.05, 1.141, 3.4), (x - sx * 0.15 + 0.05, 1.141, 4.8), (x - sx * 0.15 - 0.05, 1.141, 4.8)], 'relG', (0, -1, 0))
    # the ice that holds it: heaped over the right side, the left foot, the plinth front
    for (x, y, rx, ry, h, z0, c) in ((5.2, 1.4, 2.0, 1.6, 7.5, 0.0, 'iceM'), (6.4, 0.9, 0.9, 1.2, 4.0, 0.0, 'ice'), (3.8, 2.4, 1.4, 0.7, 10.5, 1.0, 'iceD'),
                                     (-5.6, 1.3, 1.5, 1.6, 4.2, 0.0, 'iceM'), (-4.2, 2.4, 1.2, 0.6, 8.0, 1.0, 'iceD'), (-1.5, -2.3, 1.6, 0.6, 0.8, 0.0, 'iceL'),
                                     (1.8, -2.4, 1.3, 0.5, 1.1, 0.0, 'ice'), (0.6, 2.6, 2.6, 0.4, 2.2, 9.6, 'iceM')):
        lump(m, rnd, x, y, rx, ry, h, z0, c, n=7, top=3)
    icicles(m, rnd, -3.5, 3.5, CY - 0.6, CZ + R1 - 0.3, 9, 1.2, 'iceL')
    make('Landmark_Relic', m, ao, cols=[cb(-6.6, -2.9, 0, 6.6, 2.95, 0.35), cb(-5.8, -2.0, 0.35, 5.8, 2.95, 0.7), cb(-5.0, -1.2, 0.7, 5.0, 2.95, 1.05),
                                        cb(4.0, -0.6, 0, 7.0, 3.0, 3.5), cb(-7.0, -0.2, 0, -4.3, 3.0, 3.0)])
    make_glow('Landmark_Relic_LED', g)


def build(pal, ao):
    build_archive(pal, ao)
    build_cryo(pal, ao)
    build_power(pal, ao)
    build_vault(pal, ao)
    build_ice(pal, ao)
    build_relic(pal, ao)
