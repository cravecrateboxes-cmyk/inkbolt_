"""kit-arctic zone 1 props: the trench (snowcat, fuel tank, drums, crates, a cargo sledge, antenna masts and a weather
mast poking out of drifts, a buried hut's roof, the buried module with its walkable roof, a generator skid, snow banks,
route flags, the collapsed radar dome) and the station's upper modules (mess tables, chairs, the galley, pantry, bunks,
lockers, desks, the dead terminal, the radio rack, the map table, boot-room benches and parka racks, ice breaking in,
the shaft winch, supply boxes, filing cabinets). See arc_base.py for conventions."""
import math

from arc_base import *  # noqa: F401,F403
import arc_base as B


def drum(m, x, y, z=0.0, c='blueP', lying=False, deg=0.0, r=0.23, h=0.82):
    if lying:
        m.cy((x - h / 2, y, z + r), r, r, h, c, seg=8, rot=(0, 90, deg))
        return
    m.cy((x, y, z), r, r, h, c, seg=8)
    m.cy((x, y, z + h), r * 0.75, r * 0.86, 0.05, 'snowW', seg=7, hull='none')


def wheel_disc(m, x, y, z, r, c='steelD', s=1):
    m.cy((x, y, z), r, r, 0.004, c, seg=8, rot=(0, s * 90, 0), hull='none')


def build_trench(pal, ao):
    # ---- snowcat [4, 6]: tracked carrier, orange cab, plough blade (front -Y), cargo deck behind
    m = new(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.15, sx * 1.9))
        m.prism([(-2.4, 0.3), (-2.05, 0.0), (2.05, 0.0), (2.4, 0.3), (2.2, 0.9), (-2.2, 0.9)], x0, x1, ['black'])
        xo = sx * 1.904
        for k in range(5):
            m.cy((xo, -1.8 + k * 0.9, 0.45), 0.3, 0.3, 0.004, 'steelD', seg=8, rot=(0, 90, 0), hull='none')
        lump(m, RND(300 + sx), sx * 1.6, 0.4, 0.5, 1.6, 0.55, 0.0, 'snowL', n=6, top=2)
    m.bx(-1.15, 1.15, -2.3, 2.1, 0.55, 1.45, 'orangeD')
    m.bx(-1.05, 1.05, -1.7, 0.5, 1.45, 2.75, 'orange')
    fq(m, -0.95, 0.95, -1.703, 1.75, 2.6, 'glassD')
    fq(m, -0.03, 0.03, -1.706, 1.75, 2.6, 'orange')
    for sx in (-1, 1):
        x = sx * 1.053
        poly(m, [(x, -1.6, 1.75), (x, -0.1, 1.75), (x, -0.1, 2.6), (x, -1.6, 2.6)], 'glassD', (sx, 0, 0))
    frost_spots(m, RND(301), -0.9, 0.9, 1.8, 2.55, -1.709, 5)
    m.bx(-0.9, 0.9, -0.6, 0.3, 2.75, 2.88, 'steelK')
    for sx in (-1, 1):
        m.cy((sx * 0.6, -0.62, 2.81), 0.08, 0.08, 0.05, 'yel', seg=6, rot=(90, 0, 0))
    lump(m, RND(302), 0.1, -0.5, 0.9, 0.9, 0.3, 2.88, 'snowW', n=7, top=3)
    for sx in (-1, 1):   # headlamps
        m.cy((sx * 0.75, -2.3, 1.2), 0.11, 0.11, 0.06, 'lampC', seg=8, rot=(90, 0, 0))
    m.prism([(-2.95, 0.05), (-2.6, 0.05), (-2.55, 1.1), (-2.8, 1.15)], -2.0, 2.0, ['steelL'])
    m.bx(-0.9, 0.9, -2.6, -2.3, 0.5, 0.65, 'steelK')
    for sx in (-1, 1):   # the cargo bed's side rails
        m.bx(sx * 1.1 - 0.05, sx * 1.1 + 0.05, 0.55, 2.1, 1.45, 1.85, 'steelD', cull='b')
    m.bx(-1.05, 1.05, 2.0, 2.1, 1.45, 1.85, 'steelD', cull='b')
    m.bx(-0.75, 0.3, 0.8, 1.8, 1.45, 2.3, 'cardb')
    drum(m, 0.7, 1.55, 1.45, 'blueP')
    text_side(m, 'KOLVANE 3', 0.16, 1.153, 0.0, 1.0, 'paper', 'x+', maxw=1.6)
    text_side(m, 'KOLVANE 3', 0.16, -1.153, 0.0, 1.0, 'paper', 'x-', maxw=1.6)
    make('Snowcat', m, ao, cols=[cb(-1.9, -2.4, 0, -1.15, 2.4, 0.9), cb(1.15, -2.4, 0, 1.9, 2.4, 0.9), cb(-1.15, -2.3, 0, 1.15, 2.4, 1.85),
                                 cb(-1.05, -1.7, 1.85, 1.05, 0.5, 2.75), cb(-2.0, -2.95, 0, 2.0, -2.55, 1.1)])
    # ---- fuel tank on a sledge [3, 6]
    m = new(pal)
    for sx in (-1, 1):
        m.bx(sx * 0.95 - 0.1, sx * 0.95 + 0.1, -2.8, 2.8, 0.0, 0.18, 'steelK')
        m.prism([(-2.95, 0.05), (-2.8, 0.0), (-2.75, 0.18), (-2.95, 0.3)], sx * 0.95 - 0.09, sx * 0.95 + 0.09, ['steelK'])
    for y in (-1.8, 0.0, 1.8):
        m.bx(-1.1, 1.1, y - 0.12, y + 0.12, 0.18, 0.55, 'steelD')
    m.cy((0, -2.5, 1.25), 1.0, 1.0, 5.0, 'steelL', seg=12, rot=(-90, 0, 0))
    for y in (-1.5, 1.5):
        m.cy((0, y - 0.05, 1.25), 1.005, 1.005, 0.1, 'orange', seg=12, rot=(-90, 0, 0), hull='none', caps=False)
    text_side(m, 'POLAR DIESEL', 0.28, 1.0, 0.0, 1.05, 'black', 'x+', maxw=2.6)
    text_side(m, 'POLAR DIESEL', 0.28, -1.0, 0.0, 1.05, 'black', 'x-', maxw=2.6)
    m.cy((0, -0.6, 2.25), 0.18, 0.18, 0.2, 'steelD', seg=8)
    lump(m, RND(310), 0.0, 0.6, 0.7, 1.6, 0.25, 2.18, 'snowW', n=7, top=2)
    m.cy((0, -2.55, 1.25), 0.25, 0.25, 0.06, 'black', seg=8, rot=(90, 0, 0), hull='none')
    make('FuelTank', m, ao, cols=[cb(-1.0, -2.6, 0, 1.0, 2.6, 2.25)])
    # ---- drums, crates
    m = new(pal); drum(m, -0.24, -0.2, c='blueP'); drum(m, 0.24, -0.2, c='orange'); drum(m, 0.0, 0.23, c='redE')
    make('Drums_A', m, ao, cols=[cb(-0.47, -0.43, 0, 0.47, 0.46, 0.87)])
    m = new(pal); drum(m, -0.24, 0.25, c='orange'); drum(m, 0.24, 0.25, c='blueP'); drum(m, 0.0, -0.25, c='blueP', lying=True)
    make('Drums_B', m, ao, cols=[cb(-0.47, -0.48, 0, 0.47, 0.48, 0.87)])
    for v, c in (('Crate_A', 'wood'), ('Crate_B', 'steelL')):
        m = new(pal)
        m.bx(-0.44, 0.44, -0.44, 0.44, 0.0, 0.9, c)
        if v == 'Crate_A':
            for z in (0.12, 0.78):
                fq(m, -0.44, 0.44, -0.443, z, z + 0.08, 'woodD'); bq(m, -0.44, 0.44, 0.443, z, z + 0.08, 'woodD')
            text_front(m, 'K-7', 0.18, -0.446, 0.0, 0.36, 'black')
        else:
            for x in (-0.3, 0.3):
                fq(m, x - 0.03, x + 0.03, -0.443, 0.05, 0.85, 'steel')
            fq(m, -0.15, 0.15, -0.446, 0.6, 0.7, 'orange')
        uq(m, -0.4, 0.3, -0.35, 0.4, 0.903, 'snowW')
        make(v, m, ao, cols=[cb(-0.44, -0.44, 0, 0.44, 0.44, 0.9)])
    m = new(pal)
    m.bx(-0.36, 0.36, -0.3, 0.3, 0.0, 0.5, 'cardb'); uq(m, -0.3, 0.2, -0.25, 0.2, 0.503, 'snowW')
    make('Crate_Lid', m, ao, cols=[cb(-0.36, -0.3, 0, 0.36, 0.3, 0.5)])
    # ---- cargo sledge [2, 4]
    m = new(pal)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.7, sx * 0.82))
        m.prism([(-1.9, 0.3), (-1.75, 0.02), (1.9, 0.02), (1.9, 0.1), (-1.6, 0.12)], x0, x1, ['woodD'])
        for y in (-1.2, 0.0, 1.2):
            m.bx(x0 + 0.01, x1 - 0.01, y - 0.04, y + 0.04, 0.1, 0.4, 'woodD', hull='none')
    m.bx(-0.85, 0.85, -1.6, 1.8, 0.4, 0.47, 'wood')
    for i, (y, c) in enumerate(((-1.0, 'steelL'), (0.0, 'wood'), (1.0, 'cardb'))):
        m.bx(-0.55, 0.55, y - 0.42, y + 0.42, 0.47, 1.1 - i * 0.1, c)
    m.prism([(-1.5, 0.47), (-1.5, 1.15), (1.5, 1.0), (1.5, 0.47)], -0.62, 0.62, ['orangeD'], skip=(3,))
    for y in (-0.5, 0.5):
        m.bx(-0.64, 0.64, y - 0.02, y + 0.02, 1.0, 1.18, 'yel', hull='none')
    lump(m, RND(320), 0.0, 0.3, 0.55, 1.0, 0.2, 1.08, 'snowW', n=7, top=2)
    m.bm_((0.0, -1.9, 0.25), (0.0, -2.2, 0.35), 0.05, 'steelD')
    make('Sled', m, ao, cols=[cb(-0.82, -1.9, 0, 0.82, 1.9, 1.2)])
    # ---- antenna masts in their drifts [2, 2]: a square lattice tower in red / white sections, a dish; B: snapped
    for v, top, lean in (('Mast_A', 7.6, 0.0), ('Mast_B', 4.4, 14.0)):
        m = new(pal)
        rnd = RND(330 + int(top))
        lump(m, rnd, 0.0, 0.0, 0.95, 0.9, 0.9, 0.0, 'snowS', n=8, top=3)
        old = m.parent
        m.parent = old @ Matrix.Rotation(math.radians(lean), 4, 'X')
        w = 0.28
        n = int(top / 1.2)
        for k in range(n):
            z0, z1 = 0.3 + k * (top - 0.3) / n, 0.3 + (k + 1) * (top - 0.3) / n
            c = 'orange' if k % 2 else 'panelW'
            for sx in (-1, 1):
                for sy in (-1, 1):
                    m.bx(sx * w - 0.045, sx * w + 0.045, sy * w - 0.045, sy * w + 0.045, z0, z1 - 0.004, c, cull='bt' if k else 't')
            m.bx(-w, w, -w - 0.02, -w + 0.02, z1 - 0.06, z1 - 0.02, 'steelK', hull='none')
            for (a0, a1) in (((-w, -w - 0.06), (w, -w - 0.06)),):
                m.bm_((a0[0], a0[1], z0 + 0.05), (a1[0], a1[1], z1 - 0.08), 0.02, 'steelK', hull='none')
            m.bm_((-w - 0.06, -w, z0 + 0.05), (-w - 0.06, w, z1 - 0.08), 0.02, 'steelK', hull='none')
        if lean:   # the snapped top: torn leg ends, a dish lying in the snow
            for sx in (-1, 1):
                m.bxr(sx * w, w, top + 0.15, 0.09, 0.09, 0.35, 'orange', rot=(25, sx * 15, 0))
        else:
            m.cy((0.0, -0.32, top - 1.4), 0.6, 0.18, 0.28, 'panelW', seg=10, rot=(70, 0, 0))
            m.cy((0, 0, top), 0.04, 0.04, 1.6, 'steelK', seg=5)
            m.cy((0, 0, top + 1.6), 0.08, 0.08, 0.08, 'redE', seg=6)
            hullp(m, [(-w, -w - 0.05, top * 0.62), (w, -w - 0.05, top * 0.62), (0.0, -w - 0.12, top * 0.66)], 'frost', hull='none')
        m.parent = old
        if lean:
            m.cy((0.55, -0.6, 0.25), 0.45, 0.12, 0.2, 'panelW', seg=10, rot=(20, -60, 0))
        make(v, m, ao, cols=[cb(-0.85, -0.8, 0, 0.85, 0.8, 0.8), cb(-0.4, -0.4, 0.8, 0.4, 0.4, 2.5)])
    # ---- weather mast (1 cell): anemometer, vane, a small solar panel, its drift
    m = new(pal)
    lump(m, RND(340), 0.0, 0.0, 0.42, 0.42, 0.45, 0.0, 'snowS', n=6, top=2)
    m.cy((0, 0, 0), 0.05, 0.04, 4.0, 'steelL', seg=6)
    m.bx(-0.6, 0.6, -0.03, 0.03, 3.6, 3.66, 'steelD')
    for k in range(3):
        a = k * 2.094
        m.bm_((0.55, 0, 3.75), (0.55 + math.cos(a) * 0.2, math.sin(a) * 0.2, 3.75), 0.012, 'steelK', hull='none')
        m.cy((0.55 + math.cos(a) * 0.22, math.sin(a) * 0.22, 3.7), 0.05, 0.05, 0.08, 'steelK', seg=6)
    m.bxr(-0.55, 0.0, 3.78, 0.4, 0.02, 0.12, 'orange', rot=(0, 0, 20))
    m.bxr(0.0, -0.18, 2.4, 0.5, 0.03, 0.36, 'scr', rot=(-35, 0, 0))
    m.bx(-0.12, 0.12, -0.1, 0.05, 1.3, 1.65, 'panelW')
    make('WeatherMast', m, ao, cols=[cb(-0.35, -0.35, 0, 0.35, 0.35, 0.45), cb(-0.1, -0.1, 0.45, 0.1, 0.1, 2.0)])
    # ---- route flag (1 cell)
    m = new(pal)
    m.cy((0, 0, 0), 0.025, 0.02, 2.0, 'black', seg=5)
    m.prism([(0.0, 1.55), (0.0, 1.95), (0.45, 1.8)], -0.005, 0.005, ['orange'], hull='none')
    lump(m, RND(345), 0.05, 0.0, 0.18, 0.15, 0.18, 0.0, 'snowW', n=5, top=1, hull='none')
    make('Flag', m, ao, cols=[cb(-0.06, -0.06, 0, 0.06, 0.06, 2.0)])
    # ---- snow banks [2, 2]
    for v in ('Snowbank_A', 'Snowbank_B'):
        m = new(pal)
        rnd = RND(350 + len(v) + (v[-1] == 'B') * 7)
        lump(m, rnd, -0.1, 0.0, 0.92, 0.85, 1.25 if v[-1] == 'A' else 0.95, 0.0, 'snowS', n=8, top=3)
        lump(m, rnd, 0.35, 0.3, 0.55, 0.55, 1.5 if v[-1] == 'A' else 1.2, 0.0, 'snowW', n=6, top=2)
        make(v, m, ao, cols=[cb(-0.85, -0.75, 0, 0.85, 0.8, 1.1)])
    # ---- buried hut [6, 4]: a gable roof out of the drift, its chimney, a window under the eave
    m = new(pal)
    rnd = RND(360)
    for s in (-1, 1):
        y0, y1 = sorted((0.0, s * 1.9))
        poly(m, [(-2.7, 0.0, 2.6), (2.7, 0.0, 2.6), (2.7, s * 1.9, 1.3), (-2.7, s * 1.9, 1.3)], 'steelD', (0, s, 1))
        poly(m, [(-2.7, s * 1.9, 1.3), (2.7, s * 1.9, 1.3), (2.7, s * 1.9, 1.16), (-2.7, s * 1.9, 1.16)], 'steelK', (0, s, 0))
        for k in range(10):
            x = -2.55 + k * 0.567
            poly(m, [(x, s * 0.05, 2.58 + 0.008), (x + 0.06, s * 0.05, 2.58 + 0.008), (x + 0.06, s * 1.85, 1.33 + 0.008), (x, s * 1.85, 1.33 + 0.008)], 'steel', (0, s, 1))
        poly(m, [(-2.6, s * 0.1, 2.56 + 0.02), (1.8, s * 0.1, 2.56 + 0.02), (2.2, s * 1.4, 1.75 + 0.02), (-2.3, s * 1.6, 1.62 + 0.02)], 'snowW', (0, s, 1))
    for sx in (-1, 1):
        x = sx * 2.7
        poly(m, [(x, -1.9, 1.3), (x, 1.9, 1.3), (x, 0.0, 2.6)], 'wood', (sx, 0, 0))
        poly(m, [(x + sx * 0.003, -1.9, 1.16), (x + sx * 0.003, 1.9, 1.16), (x + sx * 0.003, 1.9, 1.3), (x + sx * 0.003, -1.9, 1.3)], 'woodD', (sx, 0, 0))
    poly(m, [(2.703, -0.4, 1.4), (2.703, 0.4, 1.4), (2.703, 0.4, 1.9), (2.703, -0.4, 1.9)], 'glassD', (1, 0, 0))
    m.bx(-2.7, 2.7, -1.9, 1.9, 0.0, 1.16, 'woodD', cull='tb')
    for (x, y, rx, ry, h) in ((-1.5, -2.0, 1.6, 0.9, 1.5), (1.4, -2.0, 1.5, 0.8, 1.4), (-1.4, 2.0, 1.7, 0.9, 1.6), (1.5, 2.0, 1.4, 0.85, 1.35),
                              (-2.85, 0.0, 0.7, 1.9, 1.1), (2.85, -1.2, 0.6, 0.9, 1.0)):
        lump(m, rnd, x, y, rx, ry, h, 0.0, 'snowS', n=7, top=3)
    m.cy((1.2, 0.6, 1.9), 0.12, 0.12, 1.3, 'black', seg=8)
    m.cy((1.2, 0.6, 3.2), 0.2, 0.2, 0.08, 'steelK', seg=8)
    icicles(m, rnd, -2.6, 2.6, -1.92, 1.16, 7, 0.45)
    make('BuriedHut', m, ao, cols=[cb(-2.8, -1.95, 0, 2.8, 1.95, 1.4), cb(-2.7, -1.0, 1.4, 2.7, 1.0, 2.3)])
    # ---- buried module [8, 3]: an old container lab buried to its roof; the roof (2.2 m) is walkable
    m = new(pal)
    rnd = RND(370)
    m.bx(-3.7, 3.7, -1.25, 1.25, 0.0, ROOF - 0.15, 'panelW', cull='b')
    for k in range(13):
        x = -3.5 + k * 0.58
        fq(m, x, x + 0.06, -1.253, 0.0, ROOF - 0.18, 'panelG'); bq(m, x, x + 0.06, 1.253, 0.0, ROOF - 0.18, 'panelG')
    fq(m, -3.7, 3.7, -1.256, 1.3, 1.4, 'orange')
    for x in (-2.0, 0.8):
        fq(m, x - 0.4, x + 0.4, -1.256, 0.6, 1.2, 'glassD')
    text_front(m, 'LAB 2 - 1987', 0.18, -1.259, 2.2, 1.6, 'panelK', maxw=2.0)
    m.bx(-3.75, 3.75, -1.3, 1.3, ROOF - 0.15, ROOF, 'panelG')
    for (x, y, r) in ((-2.4, 0.2, 0.9), (1.2, -0.3, 1.1), (3.0, 0.5, 0.6)):
        disc(m, x, y, ROOF + 0.004, r, 'snowW', seg=8, sy=0.8)
    m.bx(-1.0, -0.4, 0.3, 0.9, ROOF, ROOF + 0.55, 'steelL')
    fq(m, -0.95, -0.45, 0.297, ROOF + 0.1, ROOF + 0.45, 'steelD')
    m.cy((2.4, 0.8, ROOF), 0.04, 0.04, 2.0, 'steelK', seg=5)
    for (x, y, rx, ry, h) in ((-2.5, -1.35, 1.3, 0.25, 1.3), (0.4, -1.35, 1.6, 0.22, 1.0), (2.6, 1.35, 1.2, 0.25, 1.5), (-1.2, 1.35, 1.6, 0.25, 1.2)):
        lump(m, rnd, x, y, rx, ry, h, 0.0, 'snowL', n=7, top=2)
    make('BuriedModule', m, ao, cols=[cb(-3.75, -1.3, 0, 3.75, 1.3, ROOF, True)])
    # ---- generator skid [3, 2]
    m = new(pal)
    m.bx(-1.4, 1.4, -0.8, 0.8, 0.0, 0.2, 'steelK')
    m.bx(-1.3, 1.3, -0.7, 0.7, 0.2, 1.6, 'steelL')
    for k in range(6):
        fq(m, -1.1 + k * 0.38, -0.85 + k * 0.38, -0.703, 0.6, 1.3, 'steelD')
    fq(m, -1.3, 1.3, -0.703, 0.3, 0.42, 'orange'); bq(m, -1.3, 1.3, 0.703, 0.3, 0.42, 'orange')
    m.cy((0.9, 0.3, 1.6), 0.09, 0.09, 0.8, 'steelK', seg=8)
    m.cy((0.9, 0.3, 2.4), 0.12, 0.12, 0.05, 'black', seg=8, hull='none')
    text_front(m, 'GEN 1', 0.16, -0.706, -0.4, 1.38, 'black')
    lump(m, RND(380), -0.2, 0.0, 1.1, 0.6, 0.22, 1.6, 'snowW', n=7, top=2)
    make('Genset_S', m, ao, cols=[cb(-1.4, -0.8, 0, 1.4, 0.8, 1.6)])


def radome(pal, ao):
    """the collapsed radar dome [8, 8]: its equipment shelter, half the geodesic shell still up, the rest fallen in on
    the shelter roof and the snow, the antenna dish tilted out of the hole"""
    m = new(pal)
    rnd = RND(400)
    S, HZ = 2.8, 2.6
    m.bx(-S, S, -S, S, 0.0, HZ, 'panelW', cull='b')
    for (pl, at, sgn) in (('y', -S, -1), ('y', S, 1), ('x', -S, -1), ('x', S, 1)):
        for z0, z1, c in ((0.0, 0.35, 'panelK'), (1.95, 2.1, 'orange')):
            pts = [(-S, z0), (S, z0), (S, z1), (-S, z1)]
            poly(m, [(u, at + sgn * 0.003, v) if pl == 'y' else (at + sgn * 0.003, u, v) for (u, v) in pts], c, (0, sgn, 0) if pl == 'y' else (sgn, 0, 0))
    fq(m, -0.5, 0.5, -S - 0.006, 0.36, 1.94, 'steelD')
    text_front(m, 'RADAR 1', 0.3, -S - 0.006, 1.5, 2.2, 'panelK')
    R, CZ = 3.3, HZ
    lat = [0.0, 0.42, 0.85, 1.2]
    N = 10
    def pt(i, j, k=1.0):
        a = j / N * 2 * math.pi
        e = lat[i]
        r = R * math.cos(e) * k
        return (math.cos(a) * r, math.sin(a) * r, CZ + R * math.sin(e) * k)
    for i in range(3):
        for j in range(N):
            a = (j + 0.5) / N * 2 * math.pi
            broken = math.cos(a - 4.4) > 0.1 and i < 3   # the south-east half fell in
            q = [pt(i, j), pt(i, j + 1), pt(i + 1, j + 1), pt(i + 1, j)]
            if not broken:
                poly(m, q, 'panelW' if (i + j) % 2 else 'snowW', tuple(sum(p[k] for p in q) / 4 - (0, 0, CZ)[k] for k in range(3)))
                q2 = [(p[0] * 0.985, p[1] * 0.985, CZ + (p[2] - CZ) * 0.985) for p in q[::-1]]
                poly(m, q2, 'panelG', tuple(-(sum(p[k] for p in q) / 4 - (0, 0, CZ)[k]) for k in range(3)))
            elif rnd.random() < 0.55:   # fallen panels: tilted on the roof or the snow
                cx, cy = math.cos(a) * rnd.uniform(1.0, 2.2), math.sin(a) * rnd.uniform(1.0, 2.2)
                m.bxr(cx, cy, HZ + 0.15 + i * 0.08, 1.2, 1.0, 0.04, 'panelW', rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), math.degrees(a)))
    def strut(a, b):   # shortened at both ends so struts never overlap at the nodes
        d = [b[k] - a[k] for k in range(3)]
        L = math.sqrt(sum(v * v for v in d)) or 1.0
        e = 0.035 / L
        m.bm_(tuple(a[k] + d[k] * e for k in range(3)), tuple(b[k] - d[k] * e for k in range(3)), 0.05, 'steelL')
    for i in range(4):   # the frame: struts round the standing half
        for j in range(N):
            a = (j + 0.5) / N * 2 * math.pi
            if math.cos(a - 4.4) > 0.1:
                continue
            if i < 3:
                strut(pt(i, j, 1.006), pt(i + 1, j, 1.006))
            strut(pt(i, j, 1.006), pt(i, j + 1, 1.006))
    for (x, y, deg) in ((3.4, -1.0, 30), (2.6, 3.2, -60), (-0.6, -3.4, 75)):
        m.bxr(x, y, 0.08, 1.1, 0.9, 0.04, 'panelW', rot=(8, 6, deg))
    m.cy((0.3, 0.3, HZ - 0.05), 0.25, 0.25, 1.05, 'steelD', seg=8)
    m.cy((0.6, -0.2, HZ + 1.0), 1.6, 0.3, 0.45, 'panelW', seg=12, rot=(-35, 25, 0))
    m.bm_((0.6, -0.2, HZ + 1.2), (1.1, -1.1, HZ + 2.3), 0.05, 'steelK')
    for (x, y, rx, ry, h) in ((-3.1, 1.5, 0.9, 1.8, 1.4), (3.2, 0.8, 0.8, 1.3, 1.0), (0.5, 3.2, 1.6, 0.7, 1.2)):
        lump(m, rnd, x, y, rx, ry, h, 0.0, 'snowL', n=7, top=3)
    lump(m, rnd, -0.8, 0.8, 1.6, 1.4, 0.7, HZ - 0.03, 'snowW', n=7, top=3)
    make('Landmark_Radome', m, ao, cols=[cb(-S, -S, 0, S, S, HZ)])


# ---------------------------------------------------------------- station interior
def chair(m, x, y, deg=0.0, down=False):
    old = m.parent
    m.parent = old @ Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')
    if down:   # on its back
        m.bx(-0.22, 0.22, -0.2, 0.22, 0.0, 0.05, 'chair')
        m.bx(-0.22, 0.22, 0.22, 0.27, 0.0, 0.45, 'chair')
        for sx in (-1, 1):
            m.bm_((sx * 0.2, -0.18, 0.02), (sx * 0.2, -0.18, 0.45), 0.03, 'steelK', hull='none')
            m.bm_((sx * 0.2, 0.2, 0.02), (sx * 0.2, 0.2, 0.45), 0.03, 'steelK', hull='none')
    else:
        m.bx(-0.22, 0.22, -0.22, 0.22, 0.43, 0.48, 'chair')
        m.bx(-0.22, 0.22, 0.2, 0.25, 0.48, 0.9, 'chair')
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.bm_((sx * 0.19, sy * 0.19, 0.0), (sx * 0.19, sy * 0.19, 0.43), 0.03, 'steelK', hull='none')
    m.parent = old


def plates(m, rnd, x0, x1, y0, y1, z, n):
    for k in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        disc(m, x, y, z + 0.004 + k * 0.003, 0.11, 'paper', seg=8)
        if k % 2:
            m.cy((x + 0.15, y, z), 0.04, 0.04, 0.09, rnd.choice(['orange', 'blueP', 'paper']), seg=6)


def build_station(pal, ao):
    # ---- mess table [4, 2] (benches fixed to it)
    for v in ('A', 'B'):
        m = new(pal)
        rnd = RND(500 + ord(v))
        m.bx(-1.8, 1.8, -0.42, 0.42, 0.72, 0.77, 'tileW')
        for sx in (-1, 1):
            m.bx(sx * 1.6 - 0.05, sx * 1.6 + 0.05, -0.3, 0.3, 0.0, 0.72, 'steelK')
            m.bx(sx * 1.6 - 0.035, sx * 1.6 + 0.035, -0.85, 0.85, 0.05, 0.12, 'steelK', hull='none')
        for sy in (-1, 1):
            if v == 'B' and sy > 0:   # torn off its mounts, lying on its side
                m.bxr(0.3, 0.8, 0.18, 3.0, 0.06, 0.32, 'wood', rot=(70, 0, 4))
                continue
            m.bx(-1.7, 1.7, sy * 0.8 - 0.16, sy * 0.8 + 0.16, 0.42, 0.47, 'wood')
            for sx in (-1, 1):
                m.bx(sx * 1.5 - 0.04, sx * 1.5 + 0.04, sy * 0.8 - 0.04, sy * 0.8 + 0.04, 0.0, 0.42, 'steelK', hull='none')
        plates(m, rnd, -1.5, 1.5, -0.3, 0.3, 0.77, 5)
        if v == 'B':
            m.bxr(0.9, -0.1, 0.8, 0.45, 0.32, 0.02, 'steelL', rot=(0, 12, 30))
            for k in range(3):
                disc(m, -0.6 + k * 0.5, -0.9, 0.02 + k * 0.003, 0.1, 'paper', seg=7)
        make('MessTable_' + v, m, ao, cols=[cb(-1.8, -0.42, 0, 1.8, 0.42, 0.77), cb(-1.7, -0.96, 0, 1.7, -0.64, 0.47)] + ([] if v == 'B' else [cb(-1.7, 0.64, 0, 1.7, 0.96, 0.47)]))
    for v, down in (('Chair_Up', False), ('Chair_Down', True)):
        m = new(pal); chair(m, 0.0, 0.0, 15.0, down); make(v, m, ao, cols=[cb(-0.28, -0.28, 0, 0.28, 0.28, 0.48)])
    # ---- galley [4, 1] (back to the wall, +Y)
    m = new(pal)
    rnd = RND(510)
    m.bx(-2.0, 2.0, -0.3, 0.5, 0.0, 0.88, 'steelL')
    m.bx(-2.02, 2.02, -0.34, 0.5, 0.88, 0.93, 'steel')
    for k in range(6):
        fq(m, -1.95 + k * 0.66, -1.35 + k * 0.66, -0.303, 0.1, 0.8, 'steel')
    m.bx(-1.6, -0.4, -0.25, 0.4, 0.93, 0.97, 'black')
    for (x, y) in ((-1.3, -0.05), (-0.7, -0.05), (-1.3, 0.25), (-0.7, 0.25)):
        disc(m, x, y, 0.974, 0.11, 'steelK', seg=8)
    m.cy((-1.3, -0.05, 0.97), 0.16, 0.16, 0.2, 'steelD', seg=8)
    m.cy((-0.7, 0.25, 0.97), 0.14, 0.12, 0.14, 'orangeD', seg=8)
    uq(m, 0.4, 1.2, -0.2, 0.35, 0.934, 'steelD')
    m.cy((0.8, 0.42, 0.93), 0.02, 0.02, 0.3, 'steelL', seg=6)
    m.bx(-2.0, 2.0, 0.15, 0.5, 1.5, 2.25, 'panelW', cull='k')
    for k in range(4):
        fq(m, -1.95 + k * 1.0, -1.1 + k * 1.0, 0.147, 1.55, 2.2, 'panelG')
    m.prism([(0.5, 1.6), (-0.3, 1.75), (-0.3, 1.9), (0.5, 2.2)], -1.7, -0.3, ['steelL'], skip=(3,))
    icicles(m, rnd, -1.65, -0.35, -0.3, 1.75, 5, 0.35)
    plates(m, rnd, 1.3, 1.9, -0.2, 0.3, 0.93, 3)
    make('Galley', m, ao, cols=[cb(-2.02, -0.34, 0, 2.02, 0.5, 0.93)])
    # ---- pantry shelving [2, 1]
    m = new(pal)
    rnd = RND(520)
    for sx in (-1, 1):
        m.bx(sx * 0.9 - 0.03, sx * 0.9 + 0.03, 0.05, 0.5, 0.0, 2.0, 'steelD', cull='k')
    for z in (0.15, 0.7, 1.25, 1.8):
        m.bx(-0.87, 0.87, 0.05, 0.5, z, z + 0.03, 'steelL', cull='k')
        x = -0.8
        while x < 0.7:
            w = rnd.uniform(0.12, 0.3)
            h = rnd.uniform(0.15, 0.35)
            if rnd.random() < 0.8:
                m.bx(x, x + w, 0.1, 0.44, z + 0.03, z + 0.03 + h, rnd.choice(['cardb', 'redE', 'blueP', 'paper', 'orange', 'green']), hull='full' if w > 0.2 else 'none')
            x += w + 0.04
    make('Pantry', m, ao, cols=[cb(-0.93, 0.05, 0, 0.93, 0.5, 2.0)])
    # ---- bunks [2, 1]: a double bunk along the wall, ladder, rumpled blankets
    for v in ('A', 'B'):
        m = new(pal)
        rnd = RND(530 + ord(v))
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.bx(sx * 0.95 - 0.03, sx * 0.95 + 0.03, sy * 0.42 - 0.03, sy * 0.42 + 0.03, 0.0, 1.95, 'steelD')
        for z in (0.3, 1.35):
            m.bx(-0.95, 0.95, -0.42, 0.42, z, z + 0.06, 'steelK')
            m.bx(-0.9, 0.9, -0.38, 0.38, z + 0.06, z + 0.2, 'mattress')
            lump(m, rnd, rnd.uniform(-0.2, 0.3), 0.0, 0.62, 0.36, 0.15, z + 0.185, 'fabric' if (v == 'A') == (z < 1) else 'fabricR', n=6, top=2)
            m.bx(-0.88, -0.55, -0.3, 0.3, z + 0.2, z + 0.3, 'paper')
        m.bx(-0.95, 0.95, -0.44, -0.4, 1.55, 1.75, 'steelD', hull='none')
        for z in (0.5, 0.8, 1.1):
            m.bx(0.6, 0.85, -0.47, -0.44, z, z + 0.03, 'steelL', hull='none')
        if v == 'B':   # the top blanket slid off onto the floor
            lump(m, rnd, 0.2, -0.65, 0.5, 0.25, 0.12, 0.0, 'fabricR', n=6, top=2, hull='none')
        make('Bunk_' + v, m, ao, cols=[cb(-0.98, -0.45, 0, 0.98, 0.45, 1.95)])
    # ---- locker (1 cell, back on +Y)
    for v in ('A', 'B'):
        m = new(pal)
        m.bx(-0.3, 0.3, 0.0, 0.48, 0.0, 1.9, 'panelB')
        if v == 'A':
            for k in range(4):
                fq(m, -0.24, 0.24, -0.003, 1.6 + k * 0.05, 1.62 + k * 0.05, 'panelK')
            fq(m, 0.18, 0.22, -0.003, 0.9, 1.1, 'steelD')
        else:   # door hanging open, a parka inside
            fq(m, -0.27, 0.27, -0.003, 0.05, 1.85, 'panelK')
            m.bxr(-0.336, -0.285, 0.95, 0.54, 0.03, 1.8, 'panelB', rot=(0, 0, -100))   # hinged at the left edge, swung wide (stays in its cell)
            lump(m, RND(541), 0.0, 0.2, 0.22, 0.14, 0.9, 0.8, 'orange', n=6, top=2)
        make('Locker_' + v, m, ao, cols=[cb(-0.3, 0.0, 0, 0.3, 0.48, 1.9)])
    # ---- desk [2, 1] and the dead terminal [2, 1] (back on +Y)
    def desk(m, rnd):
        m.bx(-0.95, 0.95, -0.3, 0.45, 0.72, 0.76, 'wood')
        m.bx(0.45, 0.92, -0.25, 0.42, 0.0, 0.72, 'panelG')
        for k in range(3):
            fq(m, 0.5, 0.87, -0.253, 0.08 + k * 0.22, 0.26 + k * 0.22, 'panelB')
        m.bx(-0.92, -0.86, -0.25, 0.42, 0.0, 0.72, 'panelG')
        for k in range(4):
            x, y = rnd.uniform(-0.6, 0.3), rnd.uniform(-0.2, 0.3)
            poly(m, [(x - 0.1, y - 0.14, 0.764 + k * 0.003), (x + 0.1, y - 0.14, 0.764 + k * 0.003), (x + 0.1, y + 0.14, 0.764 + k * 0.003), (x - 0.1, y + 0.14, 0.764 + k * 0.003)], 'paper', (0, 0, 1))
        chair(m, -0.2, -0.75 + 0.36, 200.0)
    m = new(pal); rnd = RND(550); desk(m, rnd)
    m.cy((0.7, 0.25, 0.76), 0.08, 0.08, 0.03, 'steelK', seg=6)
    m.bm_((0.7, 0.25, 0.79), (0.6, 0.15, 1.15), 0.025, 'steelK')
    m.cy((0.55, 0.1, 1.08), 0.12, 0.06, 0.1, 'orange', seg=6, rot=(30, 0, 0))
    m.cy((0.3, -0.1, 0.76), 0.04, 0.04, 0.1, 'blueP', seg=6)
    make('Desk', m, ao, cols=[cb(-0.95, -0.3, 0, 0.95, 0.45, 0.76)])
    m = new(pal); rnd = RND(551); desk(m, rnd)
    m.bx(-0.4, 0.3, -0.05, 0.42, 0.76, 1.32, 'paperY')
    fq(m, -0.32, 0.22, -0.053, 0.84, 1.24, 'scrDead')
    m.bx(-0.45, 0.25, -0.28, -0.08, 0.76, 0.8, 'paperY')
    m.bx(0.45, 0.9, 0.0, 0.42, 0.76, 0.98, 'panelG')
    poly(m, [(0.5, -0.2, 0.765), (0.85, -0.2, 0.765), (0.85, 0.0, 0.98), (0.5, 0.0, 0.98)], 'paper', (0, -1, 1))
    make('Terminal', m, ao, cols=[cb(-0.95, -0.3, 0, 0.95, 0.45, 0.76)])
    g = new(pal)
    text_front(g, 'LINK LOST', 0.05, -0.056, -0.05, 1.12, 'scrG', font='display', maxw=0.45)
    fq(g, -0.28, -0.22, -0.056, 0.92, 0.96, 'scrG')
    make_glow('Terminal_LED', g)
    # ---- radio rack [2, 1]
    m = new(pal)
    m.bx(-0.95, 0.95, -0.3, 0.45, 0.72, 0.76, 'steelL')
    for x in (-0.55, 0.45):
        m.bx(x - 0.38, x + 0.38, 0.0, 0.45, 0.76, 1.9, 'steelK', cull='kb')
        for k in range(3):
            z = 0.9 + k * 0.33
            fq(m, x - 0.33, x + 0.33, -0.003, z, z + 0.26, 'steelD')
            for i in range(3):
                fq(m, x - 0.24 + i * 0.2, x - 0.16 + i * 0.2, -0.006, z + 0.09, z + 0.17, 'paper' if i != 1 else 'orange')
    m.bx(-0.95, 0.95, -0.3, 0.42, 0.0, 0.72, 'steelD', cull='t')
    m.cy((0.0, -0.1, 0.76), 0.06, 0.06, 0.04, 'black', seg=6)
    m.bm_((0.0, -0.1, 0.8), (0.12, -0.2, 0.95), 0.03, 'black', hull='none')
    text_front(m, 'HF RADIO', 0.08, -0.303, -0.5, 0.5, 'paper')
    frost_spots(m, RND(560), -0.9, 0.85, 1.3, 1.85, -0.009, 4)
    make('RadioRack', m, ao, cols=[cb(-0.95, -0.3, 0, 0.95, 0.45, 1.9)])
    # ---- map table [3, 2]
    m = new(pal)
    rnd = RND(570)
    m.bx(-1.4, 1.4, -0.8, 0.8, 0.85, 0.9, 'woodD')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 1.3 - 0.04, sx * 1.3 + 0.04, sy * 0.7 - 0.04, sy * 0.7 + 0.04, 0.0, 0.85, 'woodD')
    uq(m, -1.25, 1.25, -0.65, 0.65, 0.903, 'iceL')
    for k in range(5):   # the ice dome on the map: nested contour bands, the biggest first
        r = 0.55 - k * 0.1
        poly(m, [(0.2 + math.cos(a / 9 * 6.283) * r * 1.6, -0.05 + math.sin(a / 9 * 6.283) * r, 0.906 + k * 0.003) for a in range(9)],
             ['iceM', 'ice', 'iceM', 'ice', 'iceD'][k], (0, 0, 1))
    m.cy((0.2, -0.05, 0.9), 0.03, 0.03, 0.08, 'redE', seg=5)

    text_up(m, 'K-7', 0.06, 0.925, 0.2, 0.0, 'redE')
    for k in range(3):
        x, y = rnd.uniform(-1.1, -0.5), rnd.uniform(-0.5, 0.5)
        poly(m, [(x - 0.1, y - 0.14, 0.93 + k * 0.003), (x + 0.1, y - 0.14, 0.93 + k * 0.003), (x + 0.1, y + 0.14, 0.93 + k * 0.003), (x - 0.1, y + 0.14, 0.93 + k * 0.003)], 'paper', (0, 0, 1))
    chair(m, 1.0, 1.15 - 0.3, 160.0, down=True)
    make('MapTable', m, ao, cols=[cb(-1.4, -0.8, 0, 1.4, 0.8, 0.9)])
    # ---- boot room: bench [2, 1], parka rack [2, 1]
    m = new(pal)
    m.bx(-0.95, 0.95, -0.2, 0.2, 0.42, 0.47, 'wood')
    for sx in (-1, 1):
        m.bx(sx * 0.85 - 0.04, sx * 0.85 + 0.04, -0.18, 0.18, 0.0, 0.42, 'woodD')
    for (x, y, c) in ((-0.5, -0.35, 'black'), (-0.3, -0.35, 'black'), (0.4, 0.3, 'redE'), (0.6, 0.32, 'redE')):
        m.bx(x - 0.07, x + 0.07, y - 0.14, y + 0.14, 0.0, 0.22, c)
    make('Bench', m, ao, cols=[cb(-0.95, -0.2, 0, 0.95, 0.2, 0.47)])
    m = new(pal)
    m.bx(-0.95, 0.95, 0.42, 0.48, 1.4, 1.75, 'wood', cull='k')
    for i, x in enumerate((-0.6, 0.0, 0.6)):
        m.bm_((x, 0.42, 1.6), (x, 0.3, 1.66), 0.03, 'steelD', hull='none')
        lump(m, RND(580 + i), x, 0.25, 0.25, 0.15, 1.05, 0.5, ['orange', 'redE', 'orange'][i], n=6, top=2)
        m.bx(x - 0.07, x + 0.07, 0.05, 0.35, 0.0, 0.25, 'black')
        m.bx(x + 0.08, x + 0.22, 0.05, 0.35, 0.0, 0.25, 'black')
    make('ParkaRack', m, ao, cols=[cb(-0.85, 0.05, 0, 0.85, 0.48, 1.6)])
    # ---- the ice breaking in [2, 2] (against a wall, +Y): glacier ice burst through the panels
    m = new(pal)
    rnd = RND(590)
    lump(m, rnd, 0.0, 0.5, 0.95, 0.5, 3.0, 0.0, 'iceM', n=8, top=3)
    lump(m, rnd, -0.35, -0.1, 0.6, 0.45, 1.7, 0.0, 'ice', n=7, top=2)
    lump(m, rnd, 0.45, -0.2, 0.45, 0.4, 1.1, 0.0, 'iceL', n=6, top=2)
    for (x, y, z, rx, rz) in ((-0.8, 0.3, 1.2, 25, 60), (0.85, 0.4, 2.0, -20, -50), (0.3, -0.7, 0.05, 80, 20)):
        m.bxr(x, y, z, 0.5, 0.03, 0.7, 'panelW', rot=(rx, 0, rz))
    for k in range(3):
        x, y = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.8, -0.4)
        lump(m, rnd, x, y, 0.15, 0.12, 0.15, 0.0, 'iceL', n=5, top=1, hull='none')
    make('IceIntrusion', m, ao, cols=[cb(-0.95, -0.55, 0, 0.95, 1.0, 2.2)])
    # ---- the shaft winch [4, 3] (its cable runs north to the shaft door)
    m = new(pal)
    m.bx(-1.9, 1.9, -1.2, 1.2, 0.0, 0.25, 'steelK')
    for sx in (-1, 1):
        m.bx(sx * 1.4 - 0.12, sx * 1.4 + 0.12, -0.5, 0.5, 0.25, 1.4, 'orangeD')
    m.cy((-1.28, 0.0, 1.0), 0.75, 0.75, 2.56, 'steelD', seg=12, rot=(0, 90, 0))
    for k in range(7):
        m.cy((-1.0 + k * 0.33, 0.0, 1.0), 0.76, 0.76, 0.06, 'black', seg=12, rot=(0, 90, 0), hull='none', caps=False)
    m.bx(1.55, 1.9, -1.0, 0.2, 0.25, 1.3, 'blueP')
    m.cy((1.72, -0.4, 1.3), 0.25, 0.25, 0.15, 'steelK', seg=8)
    m.bm_((0.0, 0.7, 1.6), (0.0, 1.5, 3.4), 0.05, 'black')
    m.bx(-1.8, -1.2, -1.15, -0.85, 0.25, 1.3, 'yel')
    fq(m, -1.75, -1.25, -1.153, 0.9, 1.2, 'black')
    lump(m, RND(600), 0.0, 0.0, 1.2, 0.5, 0.15, 1.72, 'frost', n=6, top=2, hull='none')
    make('Winch', m, ao, cols=[cb(-1.9, -1.2, 0, 1.9, 1.2, 0.25), cb(-1.55, -0.78, 0.25, 1.55, 0.78, 1.75), cb(1.55, -1.0, 0.25, 1.9, 0.2, 1.3), cb(-1.8, -1.15, 0.25, -1.2, -0.85, 1.3)])
    # ---- supply boxes, filing cabinet (1 cell)
    for v in ('Boxes_A', 'Boxes_B'):
        m = new(pal)
        rnd = RND(610 + len(v) * (2 if v[-1] == 'B' else 1))
        z = 0.0
        for k in range(3 if v[-1] == 'A' else 2):
            w, d, h = rnd.uniform(0.35, 0.44), rnd.uniform(0.3, 0.42), rnd.uniform(0.3, 0.4)
            ox, oy = rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)
            m.bx(ox - w, ox + w, oy - d, oy + d, z, z + h, 'cardb')
            fq(m, ox - w * 0.5, ox + w * 0.5, oy - d - 0.003, z + h * 0.3, z + h * 0.6, 'paper')
            z += h
        make(v, m, ao, cols=[cb(-0.45, -0.45, 0, 0.45, 0.45, z)])
    m = new(pal)
    m.bx(-0.25, 0.25, -0.1, 0.48, 0.0, 1.35, 'panelG')
    for k in range(4):
        fq(m, -0.22, 0.22, -0.103, 0.05 + k * 0.33, 0.33 + k * 0.33, 'panelB')
    m.bx(-0.22, 0.22, -0.45, -0.1, 0.72, 0.98, 'panelB')
    for k in range(3):
        poly(m, [(-0.18 + k * 0.05, -0.42, 0.985 + k * 0.004), (0.12 + k * 0.05, -0.42, 0.985 + k * 0.004), (0.12, -0.15, 0.985 + k * 0.004), (-0.18, -0.15, 0.985 + k * 0.004)], 'paper', (0, 0, 1))
    make('FileCab', m, ao, cols=[cb(-0.25, -0.45, 0, 0.25, 0.48, 1.35)])


def build(pal, ao):
    build_trench(pal, ao)
    radome(pal, ao)
    build_station(pal, ao)
