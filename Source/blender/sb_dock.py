"""kit-seabase docking and service level: the moon pool landmark (curb, rails, the deep water base; the submersible
DSV TRIDENT in its cradle; the portal gantry with its hoist), winches, umbilical spools, the work ROV on its stand,
dive lockers, scuba tank racks, the dive gear table, benches, hard cases and crate stacks, the subsea cargo basket,
tool carts, gas bottles, pumps, manifolds, the HP air receiver, ballast tanks, compressors, battery racks, electrical
cabinets, flood barriers (stop logs, sandbags), floor pipe runs, the decompression chamber, the column and the dock
control cabin on the gallery deck (see sb_base.py for conventions)."""
import math
import random

from sb_base import *  # noqa: F401,F403
import sb_base as B
import sb_detail as SD


def rboxes(m, boxes, c, hull='full'):
    for b in boxes:
        m.bx(*b, c, hull=hull)


# ================================================================ moon pool landmark [12, 10]
PX, PY = 4.0, 3.0       # pool opening half sizes (the water cells of the theme's '&' code)
CW, CH = 0.3, 0.5       # curb width, height


def build_moonpool(pal, ao):
    m = new(pal)
    ox, oy = PX + CW, PY + CW
    # curb: north / south bars full length, east / west between them
    for sy in (-1, 1):
        a, b = sorted((sy * PY, sy * oy))
        m.bx(-ox, ox, a, b, 0.0, CH, 'steelD', cull='b')
        hazard_up(m, -ox, ox, a, b, CH + 0.003, 16)
    for sx in (-1, 1):
        a, b = sorted((sx * PX, sx * ox))
        m.bx(a, b, -PY, PY, 0.0, CH, 'steelD', cull='b')
        hazard_up(m, a, b, -PY, PY, CH + 0.003, 12, along='y')
    # the pool: a dark water base and a stained waterline on the inner curb faces
    uq(m, -PX, PX, -PY, PY, 0.02, 'deep')
    for sy in (-1, 1):
        (bq if sy < 0 else fq)(m, -PX, PX, sy * (PY - 0.003), 0.1, 0.24, 'tealD')
    for sx in (-1, 1):
        (rq if sx < 0 else lq)(m, sx * (PX - 0.003), -PY, PY, 0.1, 0.24, 'tealD')
    # rails: stanchions round the curb, two rails per side (a gap with a chain on the west side)
    rh = 1.15
    for sy in (-1, 1):
        y = sy * (oy - 0.12)
        for i in range(9):
            x = -ox + 0.15 + i * (2 * ox - 0.3) / 8
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, CH, rh, 'hazY', hull='none' if i % 2 else 'full')
        m.tube([(-ox + 0.15, y, rh), (ox - 0.15, y, rh)], 0.035, 'hazY', seg=6)
        m.tube([(-ox + 0.15, y, 0.85), (ox - 0.15, y, 0.85)], 0.025, 'hazY', seg=5, hull='none')
    for sx in (-1, 1):
        x = sx * (ox - 0.12)
        for i in range(1, 6):
            y = -oy + 0.15 + i * (2 * oy - 0.3) / 6
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, CH, rh, 'hazY', hull='none')
        if sx > 0:
            m.tube([(x, -oy + 0.15, rh), (x, oy - 0.15, rh)], 0.035, 'hazY', seg=6)
            m.tube([(x, -oy + 0.15, 0.85), (x, oy - 0.15, 0.85)], 0.025, 'hazY', seg=5, hull='none')
        else:
            m.tube([(x, -oy + 0.15, rh), (x, -1.0, rh)], 0.035, 'hazY', seg=6)
            m.tube([(x, 1.0, rh), (x, oy - 0.15, rh)], 0.035, 'hazY', seg=6)
            m.tube([(x, -1.0, rh - 0.05), (x, -0.5, rh - 0.3), (x, 0.0, rh - 0.36), (x, 0.5, rh - 0.3), (x, 1.0, rh - 0.05)], 0.02, 'fireR', seg=4, hull='none')
            m.bx(x - 0.02, x + 0.02, -0.15, 0.15, rh - 0.6, rh - 0.4, 'hazY')
    # deck plate round the pool: a raised checker-plate apron is painted on the floor layer by the theme; here the
    # launch-control pedestal on the south-east corner
    m.bx(4.6, 5.3, 3.6, 4.3, 0.0, 1.05, 'steelD', cull='b')
    m.bxr(4.95, 3.85, 1.12, 0.76, 0.42, 0.06, 'rib', rot=(-25, 0, 0))
    for k, c in enumerate(('scrG', 'fireR', 'hazY', 'scrG')):
        fq(m, 4.7 + k * 0.14, 4.8 + k * 0.14, 3.597, 0.85, 0.95, c)
    text_front(m, 'LARS', 0.12, -0.003 + 3.6, 4.95, 0.62, 'hazY')
    cols = []
    for sy in (-1, 1):
        a, b = sorted((sy * PY, sy * oy))
        cols.append(cb(-ox, a, 0.0, ox, b, rh))
    for sx in (-1, 1):
        a, b = sorted((sx * PX, sx * ox))
        cols.append(cb(a, -PY, 0.0, b, PY, rh))
    cols.append(cb(-PX, -PY, 0.0, PX, PY, 2.4))
    cols.append(cb(4.6, 3.6, 0.0, 5.3, 4.3, 1.15))
    SD.moonpool(m, PX, PY, CW, CH)
    make('Landmark_MoonPool', m, ao, cols=cols)
    g = new(pal)
    for k, c in enumerate(('scrG', 'fireR', 'hazY', 'scrG')):
        fq(g, 4.7 + k * 0.14, 4.8 + k * 0.14, 3.594, 0.85, 0.95, c)
    make_glow('Landmark_MoonPool_LED', g)

    # ---- the submersible DSV TRIDENT (long axis on X, bow +X), floating in the pool, hull bottom under the water
    m = new(pal)
    zc = 0.75
    m.cy((-1.7, 0, zc), 0.95, 0.95, 3.2, 'subY', seg=12, rot=(0, 90, 0), caps=False)
    m.sp((-1.7, 0, zc), 0.95, 'subY', seg=(12, 6), scale=(0.7, 1, 1))
    m.sp((1.5, 0, zc), 0.92, 'glassE', seg=(12, 6), scale=(0.75, 1, 1))
    m.cy((1.42, 0, zc), 0.97, 0.97, 0.16, 'steelD', seg=12, rot=(0, 90, 0), caps=False)
    # sail / fairing with the hatch, lights, the name on both sides
    m.bx(-1.3, 0.6, -0.42, 0.42, zc + 0.7, zc + 1.45, 'subY')
    m.cy((-0.6, 0, zc + 1.45), 0.32, 0.3, 0.12, 'steelL', seg=10)
    wheel(m, -0.6, 0.0, zc + 1.62, 0.18, 'hazK', axis='z')
    for sy in (-1, 1):
        (fq if sy < 0 else bq)(m, -1.25, 0.55, sy * 0.423, zc + 0.78, zc + 0.86, 'hazK')
        (text_front if sy < 0 else text_back)(m, 'TRIDENT', 0.3, sy * 0.426, -0.35, zc + 0.95, 'hazK', maxw=1.7)
        m.cy((0.95, sy * 0.75, zc + 0.75), 0.11, 0.13, 0.22, 'steelD', seg=8, rot=(0, 90, 0))
        # stern thrusters in ducts
        m.cy((-3.0, sy * 1.15, zc + 0.15), 0.32, 0.32, 0.55, 'rib', seg=10, rot=(0, 90, 0), caps=False)
        m.bx(-2.85, -2.55, sy * 0.85 - 0.06, sy * 0.85 + 0.06, zc + 0.1, zc + 0.2, 'rib', hull='none')
        # manipulator arm folded under the bow
        m.bm_((1.35, sy * 0.55, zc - 0.35), (1.95, sy * 0.6, zc - 0.05), 0.09, 'steelL')
        m.bm_((1.95, sy * 0.6, zc - 0.05), (1.75, sy * 0.45, zc + 0.3), 0.07, 'steelL')
    m.cy((-3.2, 0, zc + 0.6), 0.25, 0.25, 0.45, 'rib', seg=8, caps=False)
    m.bx(-3.35, -2.6, -0.04, 0.04, zc + 0.2, zc + 1.2, 'subY')          # tail fin
    # lift frame and slings to the hook
    for sx in (-1, 1):
        x = -0.35 + sx * 1.1
        m.bm_((x, -0.5, zc + 1.45), (-0.35, 0.0, 3.7), 0.025, 'cable', hull='none')
        m.bm_((x, 0.5, zc + 1.45), (-0.35, 0.0, 3.7), 0.025, 'cable', hull='none')
        m.bx(x - 0.06, x + 0.06, -0.55, 0.55, zc + 1.4, zc + 1.5, 'steelD')
    make('MoonPool_Sub', m, ao)
    g = new(pal)
    for sy in (-1, 1):
        g.cy((1.173, sy * 0.75, zc + 0.75), 0.09, 0.09, 0.004, 'lamp', seg=8, rot=(0, 90, 0))
    make_glow('MoonPool_Sub_LED', g)

    # ---- the portal gantry over the pool with a trolley, hoist block and hook
    m = new(pal)
    LX, LY, TOP = 5.45, 4.0, 5.6
    for sx in (-1, 1):
        x = sx * LX
        for sy in (-1, 1):
            m.bx(x - 0.18, x + 0.18, sy * LY - 0.18, sy * LY + 0.18, 0.0, 0.08, 'steelD', hull='none')
            m.bm_((x, sy * LY, 0.05), (x, sy * 0.5, TOP - 0.3), 0.2, 'hazY')
        m.bx(x - 0.22, x + 0.22, -0.8, 0.8, TOP - 0.45, TOP, 'hazY')
        m.bm_((x, -2.0, 1.4), (x, 2.0, 1.4), 0.12, 'hazY')
    m.bx(-LX - 0.2, LX + 0.2, -0.3, 0.3, TOP, TOP + 0.55, 'hazY')
    for sy in (-1, 1):
        (fq if sy < 0 else bq)(m, -4.0, 4.0, sy * 0.303, TOP + 0.12, TOP + 0.43, 'hazK')
        (text_front if sy < 0 else text_back)(m, 'SWL 12 T', 0.22, sy * 0.306, 0.0, TOP + 0.15, 'hazY', maxw=3.0)
    m.bx(-0.85, 0.15, -0.5, 0.5, TOP - 0.55, TOP, 'orange')
    m.bm_((-0.35, 0.0, TOP - 0.55), (-0.35, 0.0, 4.05), 0.03, 'cable', hull='none')
    m.bx(-0.6, -0.1, -0.2, 0.2, 3.7, 4.05, 'hazY')
    m.bm_((-0.35, 0.0, 3.7), (-0.35, 0.0, 3.45), 0.06, 'steelD', hull='none')
    for sx in (-1, 1):   # floodlights under the beam aimed at the pool
        m.bxr(sx * 3.0, 0.0, TOP - 0.15, 0.4, 0.3, 0.25, 'steelD', rot=(0, sx * 20, 0))
    make('MoonPool_Crane', m, ao, cols=[cb(sx * LX - 0.2, sy * LY - 0.2, 0.0, sx * LX + 0.2, sy * LY + 0.2, 2.2) for sx in (-1, 1) for sy in (-1, 1)])
    g = new(pal)
    for sx in (-1, 1):
        g.bxr(sx * 3.0, 0.0, TOP - 0.29, 0.3, 0.2, 0.01, 'lamp', rot=(0, sx * 20, 0))
    make_glow('MoonPool_Crane_LED', g)


# ================================================================ dock gear
def build_dockgear(pal, ao):
    # winch [2, 2]: drum along X with wound cable, motor and gearbox on a skid, yellow frame
    m = new(pal)
    m.bx(-0.95, 0.95, -0.8, 0.8, 0.0, 0.14, 'steelD', cull='b')
    for sx in (-1, 1):
        m.bx(sx * 0.62 - 0.06, sx * 0.62 + 0.06, -0.55, 0.55, 0.14, 1.25, 'hazY', cull='b')
    m.cy((-0.5, 0.0, 0.9), 0.36, 0.36, 1.0, 'cable', seg=10, rot=(0, 90, 0), caps=False)
    for x in (-0.56, 0.5):
        m.cy((x, 0.0, 0.9), 0.5, 0.5, 0.06, 'steelD', seg=10, rot=(0, 90, 0))
    m.cy((0.68, -0.25, 0.42), 0.26, 0.26, 0.3, 'tealD', seg=8, rot=(0, 90, 0))
    m.bx(0.69, 0.92, -0.5, 0.05, 0.14, 0.75, 'steelL', cull='b')
    m.bm_((-0.3, -0.35, 1.25), (-0.3, -1.0, 2.6), 0.04, 'cable', hull='none')
    fq(m, -0.4, 0.4, -0.803, 0.02, 0.12, 'hazY')
    SD.winch(m)
    make('Winch', m, ao, cols=[cb(-0.95, -0.8, 0.0, 0.95, 0.8, 1.4)])
    # umbilical spool [2, 2]: a big reel between A-frames
    m = new(pal)
    m.bx(-0.95, 0.95, -0.9, 0.9, 0.0, 0.1, 'steelD', cull='b')
    for sx in (-1, 1):
        x = sx * 0.62
        m.cy((x - 0.04, 0.0, 1.0), 0.88, 0.88, 0.08, 'steel', seg=12, rot=(0, 90, 0))
        m.bm_((sx * 0.8, -0.6, 0.1), (sx * 0.8, 0.0, 1.0), 0.09, 'hazY')
        m.bm_((sx * 0.8, 0.6, 0.1), (sx * 0.8, 0.0, 1.0), 0.078, 'hazY')
    m.cy((-0.58, 0.0, 1.0), 0.66, 0.66, 1.16, 'subY', seg=12, rot=(0, 90, 0), caps=False)
    for k in range(3):
        x = -0.38 + k * 0.38
        m.cy((x, 0.0, 1.0), 0.672, 0.672, 0.05, 'hazK', seg=12, rot=(0, 90, 0), caps=False, hull='none')
    m.cy((-0.9, 0.0, 1.0), 0.1, 0.1, 1.8, 'steelD', seg=6, rot=(0, 90, 0))
    make('Spool', m, ao, cols=[cb(-0.95, -0.9, 0.0, 0.95, 0.9, 1.9)])
    # work-class ROV on its stand [2, 2]: frame, buoyancy block, thrusters, cameras, a manipulator
    m = new(pal)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.7 - 0.05, sx * 0.7 + 0.05, sy * 0.55 - 0.05, sy * 0.55 + 0.05, 0.0, 0.55, 'steelD', hull='none')
    m.bx(-0.85, 0.85, -0.65, 0.65, 0.55, 0.65, 'steelD')
    for sy in (-1, 1):
        m.bx(-0.8, 0.8, sy * 0.55 - 0.05, sy * 0.55 + 0.05, 0.65, 1.35, 'rib', hull='none')
    m.bx(-0.78, 0.78, -0.5, 0.5, 0.65, 1.0, 'steelL')
    m.bx(-0.85, 0.85, -0.62, 0.62, 1.35, 1.85, 'subY')
    fq(m, -0.6, 0.6, -0.623, 1.45, 1.75, 'hazK')
    text_front(m, 'ROV-3', 0.2, -0.626, 0.0, 1.5, 'subY')
    for sx in (-1, 1):
        m.cy((sx * 0.6, -0.68, 0.82), 0.15, 0.15, 0.3, 'rib', seg=8, rot=(90, 0, 0), caps=False)
        m.cy((sx * 0.6, 0.38, 0.82), 0.15, 0.15, 0.3, 'rib', seg=8, rot=(-90, 0, 0), caps=False)
    m.cy((0.0, -0.55, 0.8), 0.1, 0.1, 0.18, 'chrome', seg=8, rot=(90, 0, 0))
    m.bm_((0.35, -0.6, 0.75), (0.55, -0.95, 0.55), 0.06, 'steelL')
    m.bm_((0.55, -0.95, 0.55), (0.45, -1.0, 0.3), 0.05, 'steelL')
    make('ROV', m, ao, cols=[cb(-0.88, -0.68, 0.0, 0.88, 0.68, 1.85)])
    g = new(pal)
    for sx in (-1, 1):
        fq(g, sx * 0.3 - 0.07, sx * 0.3 + 0.07, -0.523, 0.7, 0.82, 'lamp')
    make_glow('ROV_LED', g)
    # subsea cargo basket [2, 2]: an open steel cage with cases and a coiled line inside
    m = new(pal)
    m.bx(-0.9, 0.9, -0.9, 0.9, 0.0, 0.08, 'steelD', cull='b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.86 - 0.04, sx * 0.86 + 0.04, sy * 0.86 - 0.04, sy * 0.86 + 0.04, 0.08, 1.0, 'hazY')
    for sy in (-1, 1):
        m.bx(-0.82, 0.82, sy * 0.86 - 0.03, sy * 0.86 + 0.03, 0.96, 1.02, 'hazY', hull='none')
        m.bx(-0.82, 0.82, sy * 0.86 - 0.02, sy * 0.86 + 0.02, 0.5, 0.54, 'hazY', hull='none')
    for sx in (-1, 1):
        m.bx(sx * 0.86 - 0.03, sx * 0.86 + 0.03, -0.82, 0.82, 0.96, 1.02, 'hazY', hull='none')
    m.bx(-0.7, 0.05, -0.7, -0.05, 0.08, 0.55, 'crate')
    m.bx(-0.65, 0.0, 0.05, 0.65, 0.08, 0.4, 'crateO')
    m.cy((0.42, 0.2, 0.08), 0.3, 0.3, 0.22, 'subY', seg=10)
    m.cy((0.42, 0.2, 0.09), 0.14, 0.14, 0.215, 'steelD', seg=8, hull='none')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bm_((sx * 0.86, sy * 0.86, 1.0), (0.0, 0.0, 1.9), 0.02, 'cable', hull='none')
    make('Basket', m, ao, cols=[cb(-0.9, -0.9, 0.0, 0.9, 0.9, 1.02)])
    # hard cases / drums (1 cell), a stack of cases on a pallet [2, 2]
    for name, (c, h, latch) in (('Crate_A', ('crate', 0.62, 'hazY')), ('Crate_B', ('crateO', 0.5, 'hazK'))):
        m = new(pal)
        m.bx(-0.42, 0.42, -0.32, 0.32, 0.0, h, c, cull='b')
        for sy in (-1, 1):
            (fq if sy < 0 else bq)(m, -0.42, 0.42, sy * 0.323, h - 0.12, h - 0.09, 'rib')
            for x in (-0.24, 0.24):
                (fq if sy < 0 else bq)(m, x - 0.05, x + 0.05, sy * 0.323, h - 0.2, h - 0.13, latch)
        uq(m, -0.3, 0.3, -0.06, 0.06, h + 0.003, 'rib')
        make(name, m, ao, cols=[cb(-0.42, -0.32, 0.0, 0.42, 0.32, h)])
    m = new(pal)
    m.cy((0, 0, 0), 0.3, 0.3, 0.9, 'tealD', seg=10)
    for z in (0.28, 0.62):
        m.cy((0, 0, z), 0.31, 0.31, 0.04, 'steelD', seg=10, caps=False, hull='none')
    disc(m, 0, 0, 0.903, 0.24, 'steelD', seg=10)
    fq(m, -0.15, 0.15, -0.303, 0.4, 0.55, 'hazY')
    make('Crate_C', m, ao, cols=[cb(-0.3, -0.3, 0.0, 0.3, 0.3, 0.9)])
    m = new(pal)
    m.bx(-0.95, 0.95, -0.95, 0.95, 0.0, 0.14, 'steelD', cull='b')
    rnd = random.Random(4)
    for (x0, x1, y0, y1, z0, z1, c) in ((-0.9, 0.0, -0.9, 0.05, 0.14, 0.8, 'crate'), (0.05, 0.9, -0.9, -0.1, 0.14, 0.66, 'crateO'),
                                         (-0.9, -0.05, 0.1, 0.9, 0.14, 0.62, 'crateO'), (0.0, 0.9, -0.05, 0.9, 0.14, 0.88, 'crate'),
                                         (-0.8, 0.0, -0.8, 0.0, 0.8, 1.3, 'crateO'), (0.1, 0.8, 0.05, 0.75, 0.88, 1.4, 'crate')):
        m.bx(x0, x1, y0, y1, z0, z1, c)
        fq(m, x0 + 0.08, x1 - 0.08, y0 - 0.003, z1 - 0.12, z1 - 0.08, 'rib')
    make('CrateStack', m, ao, cols=[cb(-0.95, -0.95, 0.0, 0.95, 0.95, 1.4)])
    # tool cart (1 cell)
    m = new(pal)
    m.bx(-0.4, 0.4, -0.26, 0.26, 0.12, 0.92, 'fireR')
    for k in range(4):
        z = 0.2 + k * 0.17
        fq(m, -0.36, 0.36, -0.263, z + 0.12, z + 0.135, 'rib')
        fq(m, -0.1, 0.1, -0.266, z + 0.06, z + 0.09, 'chrome')
    m.bx(-0.42, 0.42, -0.28, 0.28, 0.92, 0.96, 'rib')
    m.bx(0.4, 0.44, -0.2, 0.2, 0.7, 0.98, 'chrome', hull='none')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cy((sx * 0.32, sy * 0.18, 0.0), 0.06, 0.06, 0.12, 'rubber', seg=6, hull='none')
    m.bx(-0.2, 0.15, -0.15, 0.1, 0.96, 1.06, 'hazY')
    make('Cart', m, ao, cols=[cb(-0.44, -0.28, 0.0, 0.44, 0.28, 1.0)])
    # gas bottles chained to a bracket (1 cell)
    m = new(pal)
    for k, (x, y, c) in enumerate(((-0.22, 0.12, 'tealD'), (0.05, 0.18, 'hazY'), (0.28, 0.05, 'tealD'))):
        m.cy((x, y, 0.0), 0.12, 0.12, 1.35, c, seg=6)
        m.sp((x, y, 1.35), 0.12, c, seg=(6, 2), scale=(1, 1, 0.6))
        m.cy((x, y, 1.4), 0.03, 0.03, 0.12, 'chrome', seg=5, hull='none')
    m.bx(-0.4, 0.45, 0.32, 0.38, 0.9, 1.0, 'rib', hull='none')
    m.tube([(-0.38, 0.3, 0.95), (-0.2, -0.02, 0.95), (0.1, 0.03, 0.95), (0.42, -0.08, 0.95), (0.43, 0.3, 0.95)], 0.012, 'chrome', seg=4, hull='none', caps=False)
    make('Cylinders', m, ao, cols=[cb(-0.36, -0.1, 0.0, 0.42, 0.32, 1.45)])
    # column (1 cell): a boxed steel column with a yellow foot
    m = new(pal)
    m.bx(-0.25, 0.25, -0.25, 0.25, 0.0, H, 'steelD', cull='b')
    for (c, z0, z1) in (('hazY', 0.0, 0.5), ('hazK', 0.5, 0.6), ('hazY', 0.6, 1.0)):
        fq(m, -0.25, 0.25, -0.253, z0, z1, c)
        bq(m, -0.25, 0.25, 0.253, z0, z1, c)
        lq(m, -0.253, -0.25, 0.25, z0, z1, c)
        rq(m, 0.253, -0.25, 0.25, z0, z1, c)
    make('Column', m, ao, cols=[cb(-0.25, -0.25, 0.0, 0.25, 0.25, H)])


# ================================================================ dive lockers and gear
def helmet(m, x, y, z, c='subY'):
    m.sp((x, y, z + 0.17), 0.17, c, seg=(6, 4))
    m.cy((x, y - 0.12, z + 0.17), 0.08, 0.08, 0.06, 'glassE', seg=6, rot=(90, 0, 0))
    m.cy((x, y, z), 0.15, 0.15, 0.05, 'steelD', seg=6, hull='none')


def build_dive(pal, ao):
    # dive locker [2, 1] (back to the wall at +Y): two open bays with a helmet, a tank, fins and a coiled hose
    m = new(pal)
    m.bx(-0.89, 0.89, 0.1, 0.45, 0.0, 2.2, 'steelD', cull='bk')
    for sx in (-1, 1):
        a_, b_ = sorted((sx * 0.89, sx * 0.95))
        m.bx(a_, b_, -0.4, 0.45, 0.0, 2.28, 'steel', cull='b')
    m.bx(-0.03, 0.03, -0.4, 0.1, 0.12, 2.2, 'steel')
    m.bx(-0.89, 0.89, -0.4, 0.45, 2.2, 2.28, 'steel')
    m.bx(-0.89, 0.89, -0.4, 0.1, 0.0, 0.12, 'steel', cull='b')
    for x0 in (-0.89, 0.03):
        m.bx(x0, x0 + 0.86, -0.38, 0.1, 1.5, 1.54, 'steelL', hull='none')
        helmet(m, x0 + 0.43, -0.12, 1.54, 'subY' if x0 < 0 else 'orange')
        m.cy((x0 + 0.25, 0.0, 0.12), 0.11, 0.11, 0.7, 'hazY' if x0 < 0 else 'tealD', seg=6)
        m.bxr(x0 + 0.62, -0.05, 0.42, 0.18, 0.04, 0.6, 'rubber', rot=(8, 0, 0))
        m.cy((x0 + 0.6, 0.06, 1.05), 0.14, 0.14, 0.08, 'cable', seg=6, rot=(90, 0, 0))
        m.bx(x0 + 0.1, x0 + 0.76, -0.4, -0.37, 2.0, 2.12, 'paper', hull='none')
    SD.dive_locker(m)
    make('DiveLocker', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.45, 2.28)])
    # scuba tank rack [2, 1]: six bottles strapped in a frame
    m = new(pal)
    m.bx(-0.95, 0.95, -0.3, 0.4, 0.0, 0.1, 'steelD', cull='b')
    m.bx(-0.95, 0.95, 0.3, 0.4, 0.1, 1.5, 'steelD', cull='k')
    for k in range(6):
        x = -0.78 + k * 0.31
        c = ('hazY', 'tealD', 'hazY', 'paper', 'tealD', 'hazY')[k]
        m.cy((x, 0.08, 0.1), 0.12, 0.12, 1.05, c, seg=6)
        m.sp((x, 0.08, 1.15), 0.12, c, seg=(6, 2), scale=(1, 1, 0.55))
        m.cy((x, 0.08, 1.2), 0.035, 0.035, 0.1, 'chrome', seg=5, hull='none')
    for z in (0.45, 0.95):
        m.bx(-0.95, 0.95, -0.07, -0.03, z, z + 0.06, 'rubber', hull='none')
    SD.tank_rack(m)
    make('TankRack', m, ao, cols=[cb(-0.95, -0.06, 0.0, 0.95, 0.4, 1.5)])
    # dive gear table [2, 1]: helmets, regulators, a hose coil and a toolbox
    m = new(pal)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 0.85 - 0.03, sx * 0.85 + 0.03, sy * 0.38 - 0.03, sy * 0.38 + 0.03, 0.0, 0.86, 'steelD', hull='none')
    m.bx(-0.95, 0.95, -0.45, 0.45, 0.86, 0.92, 'steelL')
    m.bx(-0.95, 0.95, -0.45, 0.45, 0.25, 0.28, 'steelD', hull='none')
    helmet(m, -0.55, 0.0, 0.92)
    helmet(m, 0.1, 0.12, 0.92, 'orange')
    m.cy((0.6, -0.17, 0.92), 0.22, 0.22, 0.08, 'subY', seg=10)
    m.bx(0.35, 0.8, 0.1, 0.38, 0.92, 1.12, 'fireR')
    m.bx(-0.6, 0.6, -0.3, 0.3, 0.28, 0.5, 'crate')
    make('GearTable', m, ao, cols=[cb(-0.95, -0.45, 0.0, 0.95, 0.45, 1.3)])
    # bench [2, 1]
    m = new(pal)
    for sx in (-1, 1):
        m.bx(sx * 0.8 - 0.04, sx * 0.8 + 0.04, -0.15, 0.15, 0.0, 0.42, 'steelD', hull='none')
    m.bx(-0.95, 0.95, -0.22, 0.22, 0.42, 0.48, 'steelL')
    uq(m, -0.9, 0.9, -0.18, 0.18, 0.483, 'fabric')
    make('Bench', m, ao, cols=[cb(-0.95, -0.22, 0.0, 0.95, 0.22, 0.48)])


# ================================================================ machinery
def build_machinery(pal, ao):
    # centrifugal pump set [3, 2]: skid, volute, motor with fins, coupling guard, flanged pipes
    m = new(pal)
    m.bx(-1.45, 1.45, -0.85, 0.85, 0.0, 0.2, 'steelD', cull='b')
    hazard(m, -1.45, 1.45, -0.853, 0.03, 0.17, 12)
    m.cy((-0.75, 0.25, 0.85), 0.62, 0.62, 0.5, 'tealD', seg=12, rot=(90, 0, 0))
    m.cy((-0.75, -0.25, 0.85), 0.28, 0.28, 0.12, 'tealM', seg=10, rot=(90, 0, 0))
    m.bx(-1.1, -0.4, -0.3, 0.3, 0.2, 0.3, 'tealD')
    m.cy((-0.2, 0.0, 0.85), 0.18, 0.18, 0.5, 'hazY', seg=8, rot=(0, 90, 0))
    m.cy((0.3, 0.0, 0.85), 0.45, 0.45, 1.05, 'steel', seg=12, rot=(0, 90, 0))
    for k in range(5):
        m.cy((0.4 + k * 0.2, 0.0, 0.85), 0.47, 0.47, 0.04, 'steelD', seg=12, rot=(0, 90, 0), caps=False, hull='none')
    m.bx(0.4, 1.2, -0.35, 0.35, 0.2, 0.45, 'steelD')
    m.bx(0.55, 0.85, -0.25, 0.25, 1.3, 1.5, 'steelD')
    m.tube([(-0.75, 0.25, 1.47), (-0.75, 0.25, 2.4), (-0.75, 0.8, 2.75)], 0.16, 'tealD', seg=8, caps=False)
    m.cy((-0.75, 0.25, 1.45), 0.24, 0.24, 0.07, 'steelD', seg=8)
    m.tube([(-1.37, 0.25, 0.85), (-1.45, 0.25, 0.85)], 0.2, 'steelD', seg=8)
    wheel(m, -0.75, -0.3, 2.0, 0.17, 'fireR')
    m.bm_((-0.75, -0.05, 2.0), (-0.75, 0.15, 2.0), 0.04, 'steelD', hull='none')
    make('Pump', m, ao, cols=[cb(-1.45, -0.85, 0.0, 1.45, 0.85, 0.2), cb(-1.4, -0.4, 0.2, 1.3, 0.9, 1.5), cb(-1.0, -0.15, 1.5, -0.5, 0.95, 2.9)])
    # manifold [4, 1] (back to the wall): two headers with valves and gauges, risers up the wall
    m = new(pal)
    for (z, r, c) in ((0.8, 0.13, 'tealD'), (1.75, 0.11, 'hazY')):
        m.cy((-1.95, 0.05, z), r, r, 3.9, c, seg=8, rot=(0, 90, 0))
        for x in (-1.2, 0.0, 1.2):
            m.cy((x - 0.08, 0.05, z), r + 0.04, r + 0.04, 0.16, 'steelD', seg=8, rot=(0, 90, 0), caps=False, hull='none')
    for x in (-1.5, 0.6):
        m.cy((x, 0.05, 0.8), 0.13, 0.13, 3.7, 'tealD', seg=8, caps=False)
    for x in (-0.6, 1.5):
        m.cy((x, 0.05, 1.75), 0.11, 0.11, 2.75, 'hazY', seg=8, caps=False)
    for x in (-0.6, 0.6):
        m.cy((x, 0.05, 0.94), 0.06, 0.06, 0.25, 'steelD', seg=6, hull='none')
        wheel(m, x, -0.15, 1.25, 0.15, 'fireR')
    m.bx(-1.9, -1.1, 0.32, 0.42, 1.95, 2.6, 'steelL')
    gauge(m, -1.7, 0.32, 2.3)
    gauge(m, -1.3, 0.32, 2.3)
    for x in (-1.9, 1.9):
        m.bx(x - 0.04, x + 0.04, 0.1, 0.45, 0.0, 2.2, 'steelD', hull='none')
    make('Manifold', m, ao, cols=[cb(-1.95, -0.12, 0.0, 1.95, 0.45, 2.2)])
    # HP air receiver [2, 2]: a vertical vessel on legs
    m = new(pal)
    for k in range(3):
        a = k / 3 * 2 * math.pi + 0.5
        m.bx(math.cos(a) * 0.6 - 0.05, math.cos(a) * 0.6 + 0.05, math.sin(a) * 0.6 - 0.05, math.sin(a) * 0.6 + 0.05, 0.0, 0.6, 'steelD', hull='none')
    m.cy((0, 0, 0.5), 0.75, 0.75, 2.2, 'steelL', seg=12)
    m.sp((0, 0, 2.7), 0.75, 'steelL', seg=(12, 4), scale=(1, 1, 0.45))
    m.sp((0, 0, 0.5), 0.75, 'steelL', seg=(12, 4), scale=(1, 1, 0.3))
    m.bx(-0.45, 0.45, -0.763, -0.7, 1.4, 1.9, 'tealD', hull='none')
    text_front(m, 'HP AIR', 0.17, -0.766, 0.0, 1.55, 'panelL', maxw=0.8)
    gauge(m, 0.0, -0.75, 2.2, 0.09)
    m.cy((0, 0, 3.0), 0.08, 0.08, 0.6, 'steelD', seg=6)
    make('Tank', m, ao, cols=[cb(-0.75, -0.75, 0.0, 0.75, 0.75, 3.1)])
    # ballast tank [6, 3]: a horizontal vessel on two saddles, valves and a nameplate
    m = new(pal)
    for x in (-1.8, 1.8):
        m.bx(x - 0.3, x + 0.3, -1.1, 1.1, 0.0, 0.7, 'steelD', cull='b')
    m.cy((-2.4, 0, 1.55), 1.3, 1.3, 4.8, 'tealD', seg=14, rot=(0, 90, 0), caps=False)
    for sx in (-1, 1):
        m.sp((sx * 2.4, 0, 1.55), 1.3, 'tealD', seg=(14, 5), scale=(0.35, 1, 1))
        m.cy((sx * 1.2 - 0.1, 0, 1.55), 1.33, 1.33, 0.2, 'steelD', seg=14, rot=(0, 90, 0), caps=False, hull='none')
    for x in (-1.5, 0.3):
        m.cy((x, 0, 2.8), 0.14, 0.14, 0.5, 'steelD', seg=8)
        wheel(m, x, 0.0, 3.35, 0.2, 'hazY', axis='z')
    m.bx(-0.9, 0.9, -1.33, -1.25, 1.2, 1.9, 'hazY', hull='none')
    text_front(m, 'BALLAST', 0.3, -1.333, 0.0, 1.32, 'hazK', maxw=1.7)
    m.tube([(2.95, 0, 1.0), (3.0, 0, 0.3), (3.0, 0, 0.0)], 0.13, 'tealD', seg=8, caps=False)
    make('BallastTank', m, ao, cols=[cb(-2.4, -1.3, 0.0, 2.4, 1.3, 2.85), cb(-2.78, -0.85, 0.0, -2.4, 0.85, 2.4), cb(2.4, -0.85, 0.0, 2.78, 0.85, 2.4)])
    # compressor [2, 2]: a skid unit with a fan grille and an after-cooler
    m = new(pal)
    m.bx(-0.95, 0.95, -0.9, 0.9, 0.0, 0.12, 'steelD', cull='b')
    m.bx(-0.85, 0.85, -0.8, 0.5, 0.12, 1.5, 'steel')
    for k in range(6):
        z = 0.35 + k * 0.17
        fq(m, -0.75, 0.15, -0.803, z, z + 0.08, 'rib')
    fq(m, 0.3, 0.75, -0.803, 0.95, 1.35, 'hazY')
    text_front(m, 'AIR', 0.14, -0.806, 0.525, 1.05, 'hazK')
    m.cy((0.0, 0.5, 0.9), 0.4, 0.4, 0.35, 'rib', seg=10, rot=(-90, 0, 0), caps=False)
    m.tube([(0.6, 0.0, 1.5), (0.6, 0.0, 2.1), (0.6, 0.7, 2.1), (0.6, 0.85, 1.6)], 0.07, 'copper', seg=6, caps=False)
    make('Compressor', m, ao, cols=[cb(-0.95, -0.9, 0.0, 0.95, 0.85, 1.5)])
    # battery rack [3, 2] (stands free): two faces of battery trays with status LEDs (companion)
    m = new(pal)
    m.bx(-1.45, 1.45, -0.6, 0.6, 0.0, 2.1, 'steelB', cull='b')
    for sy in (-1, 1):
        y = sy * 0.603
        for k in range(4):
            z = 0.2 + k * 0.48
            (fq if sy < 0 else bq)(m, -1.35, 1.35, y, z, z + 0.04, 'rib')
            for i in range(6):
                x = -1.25 + i * 0.45
                (fq if sy < 0 else bq)(m, x, x + 0.36, y, z + 0.08, z + 0.36, 'steelD')
        (fq if sy < 0 else bq)(m, -0.5, 0.5, y, 2.04, 2.1, 'hazY')
    m.bx(-1.45, 1.45, -0.65, 0.65, 2.1, 2.2, 'rib')
    make('BatteryRack', m, ao, cols=[cb(-1.45, -0.65, 0.0, 1.45, 0.65, 2.2)])
    g = new(pal)
    for sy in (-1, 1):
        y = sy * 0.609
        for k in range(4):
            z = 0.2 + k * 0.48 + 0.3
            for i in range(6):
                x = -1.25 + i * 0.45 + 0.28
                (fq if sy < 0 else bq)(g, x, x + 0.04, y, z, z + 0.03, 'scrG' if (i + k) % 5 else 'scrO')
    make_glow('BatteryRack_LED', g)
    # electrical cabinet [2, 1] (back to the wall)
    m = new(pal)
    m.bx(-0.95, 0.95, -0.3, 0.45, 0.0, 2.1, 'steelB', cull='bk')
    for x0 in (-0.92, 0.02):
        fq(m, x0, x0 + 0.9, -0.303, 0.1, 2.0, 'steel')
        fq(m, x0 + 0.78, x0 + 0.82, -0.306, 0.9, 1.2, 'rubber')
    fq(m, -0.9, -0.1, -0.306, 1.45, 1.85, 'screen')
    m.bx(0.2, 0.7, -0.33, -0.3, 1.5, 1.9, 'hazY', hull='none')
    poly(m, [(0.45, -0.334, 1.85), (0.3, -0.334, 1.6), (0.6, -0.334, 1.6)], 'hazK', (0, -1, 0))
    make('Cabinet', m, ao, cols=[cb(-0.95, -0.3, 0.0, 0.95, 0.45, 2.1)])
    g = new(pal)
    for k in range(6):
        fq(g, -0.85 + k * 0.12, -0.78 + k * 0.12, -0.309, 1.62, 1.68, 'scrG' if k % 3 else 'scrO')
    fq(g, -0.85, -0.15, -0.309, 1.75, 1.8, 'scrC')
    make_glow('Cabinet_LED', g)
    # decompression chamber [5, 3] (back to the wall): a horizontal vessel with a door, porthole and panel
    m = new(pal)
    for x in (-1.5, 1.2):
        m.bx(x - 0.3, x + 0.3, -0.8, 0.8, 0.0, 0.5, 'steelD', cull='b')
    m.cy((-2.0, 0.1, 1.45), 1.0, 1.0, 3.6, 'panelL', seg=14, rot=(0, 90, 0), caps=False)
    m.sp((1.6, 0.1, 1.45), 1.0, 'panelL', seg=(14, 4), scale=(0.3, 1, 1))
    m.cy((-2.0, 0.1, 1.45), 1.05, 1.05, 0.2, 'steelD', seg=14, rot=(0, 90, 0))
    m.cy((-2.2, 0.1, 1.45), 0.75, 0.75, 0.2, 'steel', seg=14, rot=(0, 90, 0))
    for k in range(3):
        x = -1.0 + k * 0.9
        m.cy((x, -0.82, 1.7), 0.16, 0.16, 0.12, 'steelD', seg=10, rot=(90, 0, 0))
    m.bx(-1.3, 1.2, -0.95, -0.85, 0.9, 1.0, 'tealM', hull='none')
    text_front(m, 'DECO 1', 0.22, -0.953, 0.0, 0.62, 'tealD')
    m.bx(1.75, 2.4, -0.5, 0.5, 0.0, 1.6, 'steelB')
    fq(m, 1.82, 2.33, -0.503, 0.9, 1.45, 'steelL')
    gauge(m, 1.95, -0.503, 1.25, 0.08)
    gauge(m, 2.2, -0.503, 1.25, 0.08)
    make('DecoChamber', m, ao, cols=[cb(-2.4, -0.95, 0.0, 1.9, 1.1, 2.5), cb(1.75, -0.5, 0.0, 2.4, 0.5, 1.6)])
    g = new(pal)
    for k in range(3):
        x = -1.0 + k * 0.9
        g.cy((x, -0.95, 1.7), 0.12, 0.12, 0.004, 'lampC', seg=10, rot=(90, 0, 0))
    make_glow('DecoChamber_LED', g)


# ================================================================ flood barriers, pipe runs (cells, run along X)
def build_barriers(pal, ao):
    # steel stop-log barrier: posts at the module ends (half), boards between, yellow tops
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 0.5, sx * 0.44))
        m.bx(a, b, -0.12, 0.12, 0.0, 1.2, 'steelD', hull='noside')
    for k in range(4):
        z = k * 0.27
        m.bx(-0.44, 0.44, -0.07, 0.07, z, z + 0.25, 'steel' if k % 2 else 'steelL', hull='none')
    m.bx(-0.44, 0.44, -0.08, 0.08, 1.06, 1.12, 'hazY')
    fq(m, -0.3, 0.3, -0.073, 0.6, 0.72, 'hazK')
    m.bxr(0.0, -0.32, 0.45, 0.06, 0.06, 0.95, 'steelD', rot=(-28, 0, 0))
    make('Barrier_A', m, ao, cols=[cb(-0.5, -0.12, 0.0, 0.5, 0.12, 1.12)])
    # sandbag wall: three courses of canvas bags
    m = new(pal)
    rnd = random.Random(8)
    for k in range(3):
        for i in range(2 if k < 2 else 1):
            x = -0.25 + i * 0.5 if k < 2 else 0.0
            m.sp((x, 0.0, 0.16 + k * 0.27), 0.28, 'canvas' if (i + k) % 2 else 'canvasD', seg=(6, 3), scale=(0.95, 0.75, 0.5))
    make('Barrier_B', m, ao, cols=[cb(-0.5, -0.22, 0.0, 0.5, 0.22, 0.85)])
    # floor pipe run: three pipes on low saddles
    m = new(pal)
    for (y, z, r, c) in ((-0.28, 0.32, 0.12, 'tealD'), (0.0, 0.32, 0.1, 'hazY'), (0.28, 0.32, 0.14, 'steelL')):
        m.cy((-0.5, y, z), r, r, 1.0, c, seg=6, rot=(0, 90, 0), caps=False, hull='noside')
    m.bx(-0.06, 0.06, -0.45, 0.45, 0.0, 0.2, 'steelD', hull='none')
    m.bx(-0.04, 0.04, -0.45, 0.45, 0.44, 0.48, 'steelD', hull='none')
    make('PipeRun', m, ao, cols=[cb(-0.5, -0.43, 0.0, 0.5, 0.43, 0.48)])


# ================================================================ dock control cabin [6, 4] (on the gallery deck)
def build_cabin(pal, ao):
    m = new(pal)
    W2, D2, CHt = 3.0, 2.0, 2.7
    # back and side walls; the front (-Y) is a window band with a doorway in the middle
    m.bx(-W2, W2, D2 - 0.17, D2 - 0.07, 0.0, CHt, 'steelB', cull='bk')
    for sx in (-1, 1):
        a, b = sorted((sx * W2, sx * (W2 - 0.1)))
        m.bx(a, b, -D2, D2 - 0.17, 0.0, 1.0, 'steelB')
        m.bx(a, b, -D2, D2 - 0.17, 2.3, CHt, 'steelB', hull='noend')
        for y in (-D2, 0.0, D2 - 0.27):
            m.bx(a, b, y, y + 0.1, 1.0, 2.3, 'rib', hull='none')
    for x0, x1 in ((-W2 + 0.1, -0.6), (0.6, W2 - 0.1)):
        m.bx(x0, x1, -D2, -D2 + 0.1, 0.0, 1.0, 'steelB')
        for x in (x0, (x0 + x1) / 2 - 0.05, x1 - 0.1):
            m.bx(x, x + 0.1, -D2, -D2 + 0.1, 1.0, 2.3, 'rib', hull='none')
    m.bx(-W2 + 0.1, W2 - 0.1, -D2, -D2 + 0.1, 2.3, CHt, 'steelB')
    fq(m, -1.8, 1.8, -D2 - 0.003, 2.36, 2.62, 'tealD')
    text_front(m, 'DOCK CONTROL', 0.2, -D2 - 0.006, 0.0, 2.4, 'panelL', maxw=3.4)
    m.bx(-W2 - 0.1, W2 + 0.1, -D2 - 0.1, D2 - 0.03, CHt, CHt + 0.15, 'rib')
    # console along the front windows, two chairs, a chart table
    m.bx(-2.8, -0.8, -1.85, -1.25, 0.0, 0.85, 'steelD')
    m.bx(0.8, 2.8, -1.85, -1.25, 0.0, 0.85, 'steelD')
    for x in (-1.8, 1.8):
        m.bxr(x, -1.55, 0.92, 1.8, 0.5, 0.06, 'rib', rot=(18, 0, 0))
        m.cy((x, -0.7, 0.0), 0.05, 0.05, 0.45, 'steelD', seg=6, hull='none')
        m.bx(x - 0.25, x + 0.25, -0.95, -0.45, 0.45, 0.55, 'fabric')
        m.bx(x - 0.25, x + 0.25, -0.5, -0.42, 0.55, 1.05, 'fabric')
    m.bx(-1.0, 1.0, 0.6, 1.6, 0.0, 0.9, 'steelB')
    uq(m, -0.9, 0.9, 0.7, 1.5, 0.903, 'screen')
    make('DockCabin', m, ao, cols=[cb(-W2, D2 - 0.17, 0.0, W2, D2, CHt), cb(-W2, -D2, 0.0, -W2 + 0.1, D2, CHt), cb(W2 - 0.1, -D2, 0.0, W2, D2, CHt),
                                   cb(-W2, -D2, 0.0, -0.6, -D2 + 0.1, CHt), cb(0.6, -D2, 0.0, W2, -D2 + 0.1, CHt),
                                   cb(-2.8, -1.9, 0.0, -0.8, -1.25, 1.0), cb(0.8, -1.9, 0.0, 2.8, -1.25, 1.0), cb(-1.0, 0.6, 0.0, 1.0, 1.6, 0.9)])
    g = new(pal)
    for x in (-1.8, 1.8):
        g.bxr(x, -1.55, 0.955, 1.6, 0.4, 0.004, 'scrC', rot=(18, 0, 0))
    uq(g, -0.85, 0.85, 0.75, 1.45, 0.906, 'scrG')
    make_glow('DockCabin_LED', g)
    g = new(pal)
    for x0, x1 in ((-W2, -0.6), (0.6, W2)):
        poly(g, [(x0, -D2 + 0.05, 1.0), (x1, -D2 + 0.05, 1.0), (x1, -D2 + 0.05, 2.3), (x0, -D2 + 0.05, 2.3)], 'glassT', (0, -1, 0))
    for sx in (-1, 1):
        x = sx * (W2 - 0.05)
        poly(g, [(x, -D2, 1.0), (x, D2 - 0.17, 1.0), (x, D2 - 0.17, 2.3), (x, -D2, 2.3)], 'glassT', (sx, 0, 0))
    make_glow('DockCabin_Glass', g)


def build_dock(pal, ao):
    build_moonpool(pal, ao)
    build_dockgear(pal, ao)
    build_dive(pal, ao)
    build_machinery(pal, ao)
    build_barriers(pal, ao)
    build_cabin(pal, ao)
