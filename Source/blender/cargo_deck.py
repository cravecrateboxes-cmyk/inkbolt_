"""kit-cargoship main-deck equipment: the deck crane (pedestal, house, luffing jib), mooring winches, double bitts,
mushroom vents, a hold ventilator, a foam monitor, a lashing-gear cage, rope coils, oil drums, a raised manhole, and
lifeboat / rescue-boat davits whose boats hang outboard over the ship's side (Blender -X)."""
import math

from cargo_base import *  # noqa: F401,F403
import ib_text
import cargo_detail as D


def octo(m, x, y, z, r, h, c, seg=8, hull='full'):
    m.cy((x, y, z), r, r, h, c, seg=seg, hull=hull)


# ================================================================ deck crane [4,4]
def build_crane(pal, ao):
    m = new(pal)
    octo(m, 0, 0, 0, 1.55, 6.0, 'supWD', seg=8)
    m.cy((0, 0, 0), 1.75, 1.75, 0.25, 'deckGD', seg=8)
    m.cy((0, 0, 6.0), 1.8, 1.8, 0.45, 'steelD', seg=12)
    ladder(m, 0.0, -1.43, 0.25, 6.0, c='yel')
    fq(m, -0.35, 0.35, -1.435, 0.25, 2.0, 'supG')
    # slewing house: machinery room, operator cab with windows, A-frame for the luffing wires
    m.bx(-1.7, 1.7, -1.4, 2.1, 6.45, 9.4, 'yel', bevel=True)
    m.bx(-1.72, 1.72, -1.42, 2.12, 7.3, 7.4, 'ink', hull='none')
    for sx in (-1, 1):
        for k in range(3):
            xf = sx * 1.703
            (rq if sx > 0 else lq)(m, xf, 0.0 + k * 0.6, 0.4 + k * 0.6, 7.8, 8.9, 'steelD')
    m.bx(-1.7, -0.5, -2.3, -1.4, 6.45, 8.9, 'yel', bevel=True)
    fq(m, -1.62, -0.58, -2.303, 7.5, 8.6, 'glassD')
    fq(m, -1.62, -1.1, -2.306, 8.15, 8.6, 'glass')
    m.bx(-1.75, -0.45, -2.35, -1.35, 8.9, 9.0, 'ink')
    for sx in (-1, 1):
        m.bm_((sx * 1.2, 1.8, 9.4), (sx * 0.4, 0.4, 12.6), 0.22, 'yel')
        m.bm_((sx * 1.2, -0.6, 9.4), (sx * 0.4, 0.4, 12.6), 0.22, 'yel')
    m.bx(-0.6, 0.6, 0.2, 0.6, 12.5, 12.8, 'yel')
    m.cy((0.0, 0.4, 12.8), 0.18, 0.18, 0.3, 'fireR', seg=8)
    m.bx(-0.5, 0.5, 2.1, 2.5, 7.0, 8.6, 'steelD')   # counterweight / winch housing
    hazard(m, -0.5, 0.5, 2.503, 7.0, 7.4, 4, back=True)
    make('Landmark_Crane', m, ao, cols=[cb(-1.55, -0.65, 0, 1.55, 0.65, 6.0), cb(-0.65, -1.55, 0, 0.65, 1.55, 6.0)])
    # luffing jib: tapered box girder from the heel (y -1.6, z 8.2) up toward -Y at 56 degrees, hook block on its wire
    m = new(pal)
    a = math.radians(56)
    Lj = 21.0
    heel = Vector((0.0, -1.6, 8.2))
    d = Vector((0.0, -math.cos(a), math.sin(a)))
    up = Vector((0.0, math.sin(a), math.cos(a)))
    tip = heel + d * Lj
    for sx in (-1, 1):   # two chords per side, lacing between them
        for su in (-1, 1):
            w0, w1 = 0.55, 0.22
            p0 = heel + Vector((sx * w0, 0, 0)) + up * su * 0.45
            p1 = tip + Vector((sx * w1, 0, 0)) + up * su * 0.18
            m.bm_(tuple(p0), tuple(p1), 0.16, 'yel')
        for k in range(8):
            t0, t1 = k / 8.0, (k + 1) / 8.0
            q0 = heel + d * (Lj * t0) + Vector((sx * (0.55 - 0.33 * t0), 0, 0)) + up * (0.45 - 0.27 * t0)
            q1 = heel + d * (Lj * t1) + Vector((sx * (0.55 - 0.33 * t1), 0, 0)) - up * (0.45 - 0.27 * t1)
            m.bm_(tuple(q0), tuple(q1), 0.07, 'yel', hull='none')
    m.bx(-0.3, 0.3, tip.y - 0.4, tip.y + 0.4, tip.z - 0.3, tip.z + 0.3, 'ink')
    m.cy((0.0, tip.y, tip.z - 0.3), 0.3, 0.3, 0.15, 'fireR', seg=8, rot=(0, 90, 0))
    # luffing wires to the A-frame top, hoist wire down to the hook block
    m.bm_((0.25, 0.4, 12.7), (0.2, tip.y + 0.2, tip.z + 0.25), 0.04, 'ink', hull='none')
    m.bm_((-0.25, 0.4, 12.7), (-0.2, tip.y + 0.2, tip.z + 0.25), 0.04, 'ink', hull='none')
    hz = 15.2
    m.bm_((0.08, tip.y, tip.z - 0.3), (0.08, tip.y, hz + 0.9), 0.035, 'ink', hull='none')
    m.bm_((-0.08, tip.y, tip.z - 0.3), (-0.08, tip.y, hz + 0.9), 0.035, 'ink', hull='none')
    m.bx(-0.35, 0.35, tip.y - 0.25, tip.y + 0.25, hz, hz + 0.9, 'yel', bevel=True)
    hazard(m, -0.35, 0.35, tip.y - 0.253, hz + 0.3, hz + 0.6, 4)
    m.cy((0.0, tip.y, hz - 0.5), 0.08, 0.16, 0.5, 'steelD', seg=8)
    make('Landmark_CraneJib', m, ao)


# ================================================================ mooring and deck fittings
def build_mooring(pal, ao):
    # mooring winch [4,3]: base frame, split rope drum, warping head, gearbox, motor, brake bands
    for name, rope in (('Winch_A', True), ('Winch_B', False)):
        m = new(pal)
        m.bx(-1.9, 1.9, -1.2, 1.2, 0.0, 0.3, 'steelD', cull='b')
        zc = 1.0
        for x in (-1.3, 0.55):   # bearing pedestals
            m.bx(x - 0.15, x + 0.15, -0.5, 0.5, 0.3, zc, 'engGD')
        m.cy((-1.15, 0, zc), 0.78, 0.78, 0.12, 'engG', seg=14, rot=(0, 90, 0))
        m.cy((0.3, 0, zc), 0.78, 0.78, 0.12, 'engG', seg=14, rot=(0, 90, 0))
        m.cy((-1.03, 0, zc), 0.48, 0.48, 1.33, 'rope' if rope else 'steelL', seg=14, rot=(0, 90, 0))
        if rope:   # rope wraps: darker bands
            for k in range(5):
                m.cy((-0.95 + k * 0.25, 0, zc), 0.485, 0.485, 0.06, 'yelD', seg=14, rot=(0, 90, 0), hull='none', caps=False)
            m.bm_((0.0, -0.45, zc - 0.05), (0.2, -1.25, 0.31), 0.12, 'rope')
        m.cy((-1.9, 0, zc), 0.3, 0.38, 0.45, 'steelL', seg=10, rot=(0, -90, 0))
        m.bx(0.7, 1.4, -0.55, 0.55, 0.3, 1.45, 'engGD', bevel=True)
        m.cy((1.4, 0, 0.95), 0.36, 0.36, 0.45, 'engG', seg=10, rot=(0, 90, 0))
        m.cy((1.85, 0, 0.95), 0.2, 0.2, 0.05, 'steelD', seg=8, rot=(0, 90, 0))
        for x in (-1.25, 0.18):   # brake bands and handwheels
            m.cy((x, 0, zc), 0.8, 0.8, 0.05, 'fireR', seg=14, rot=(0, 90, 0), hull='none', caps=False)
        m.cy((0.2, -0.95, 1.5), 0.03, 0.03, 0.25, 'steelD', seg=6)
        m.cy((0.2, -0.95, 1.75), 0.22, 0.22, 0.04, 'fireR', seg=10)
        D.winch_detail(m)
        make(name, m, ao, cols=[cb(-2.0, -0.8, 0, 1.9, 0.8, 1.8), cb(-1.9, -1.2, 0, 1.9, 1.2, 0.3)])
    # double bitts [2,1]
    m = new(pal)
    m.bx(-0.9, 0.9, -0.35, 0.35, 0.0, 0.08, 'deckGD', cull='b')
    for x in (-0.48, 0.48):
        m.cy((x, 0, 0.08), 0.22, 0.22, 0.6, 'ink', seg=12)
        m.cy((x, 0, 0.68), 0.28, 0.28, 0.08, 'ink', seg=12)
        m.cy((x, 0, 0.5), 0.223, 0.223, 0.08, 'paper', seg=12, hull='none', caps=False)
    m.bx(-0.48, 0.48, -0.06, 0.06, 0.25, 0.35, 'ink')
    D.bitts_detail(m)
    make('Bitts', m, ao, cols=[cb(-0.75, -0.28, 0, 0.75, 0.28, 0.76)])
    # rope coil 1x1: a flaked-down mooring line on a grating
    m = new(pal)
    m.bx(-0.48, 0.48, -0.48, 0.48, 0.0, 0.08, 'galv', cull='b')
    for k in range(4):
        m.cy((0, 0, 0.08 + k * 0.1), 0.44 - k * 0.02, 0.44 - k * 0.02, 0.1, 'rope' if k % 2 == 0 else 'yelD', seg=12, caps=k == 3)
    m.cy((0, 0, 0.481), 0.2, 0.2, 0.004, 'ink', seg=10, hull='none')
    make('RopeCoil', m, ao, cols=[cb(-0.44, -0.44, 0, 0.44, 0.44, 0.48)])
    # oil drums 1x1
    m = new(pal)
    for x, y, c, h in ((-0.24, -0.2, 'signB', 0.88), (0.245, -0.2, 'fireR', 0.86), (0.0, 0.225, 'signB', 0.9)):
        m.cy((x, y, 0), 0.23, 0.23, h, c, seg=10)
        for z in (0.29, 0.59):
            m.cy((x, y, z), 0.233, 0.233, 0.03, 'steelD', seg=10, hull='none', caps=False)
        m.cy((x + 0.1, y, h), 0.04, 0.04, 0.02, 'steelD', seg=6)
    make('Drums', m, ao, cols=[cb(-0.45, -0.42, 0, 0.47, 0.48, 0.9)])
    # mushroom vent 1x1
    m = new(pal)
    m.cy((0, 0, 0), 0.3, 0.3, 0.12, 'deckGD', seg=10)
    m.cy((0, 0, 0.12), 0.16, 0.16, 0.85, 'supWD', seg=10)
    m.cy((0, 0, 0.97), 0.36, 0.08, 0.3, 'supWD', seg=10)
    m.cy((0, 0, 0.92), 0.362, 0.362, 0.05, 'steelD', seg=10, hull='none', caps=False)
    make('MushroomVent', m, ao, cols=[cb(-0.18, -0.18, 0, 0.18, 0.18, 1.25)])
    # hold ventilator [2,2]: louvred fan housing with a hood and a stencilled number
    m = new(pal)
    m.bx(-0.8, 0.8, -0.8, 0.8, 0.0, 2.1, 'supWD', bevel=True, cull='b')
    for fy in (-1, 1):
        f = fq if fy < 0 else bq
        for k in range(6):
            f(m, -0.65, 0.65, fy * 0.803, 0.4 + k * 0.2, 0.48 + k * 0.2, 'steelD')
    ib_text.draw(m, 'HOLD VENT', 0.803, 0.0, 1.75, 0.16, 'ink', face='x+', font='cond')
    ib_text.draw(m, 'HOLD VENT', -0.803, 0.0, 1.75, 0.16, 'ink', face='x-', font='cond')
    m.bx(-0.95, 0.95, -0.95, 0.95, 2.1, 2.25, 'supWD')
    m.cy((0, 0, 2.25), 0.45, 0.45, 0.4, 'steelL', seg=10)
    m.cy((0, 0, 2.65), 0.3, 0.3, 0.05, 'steelD', seg=10)
    make('HoldVent', m, ao, cols=[cb(-0.8, -0.8, 0, 0.8, 0.8, 2.25)])
    # foam monitor 1x1: red pedestal and nozzle
    m = new(pal)
    m.cy((0, 0, 0), 0.25, 0.25, 0.1, 'steelD', seg=8)
    m.cy((0, 0, 0.1), 0.1, 0.1, 1.05, 'fireR', seg=8)
    m.sp((0, 0, 1.18), 0.15, 'fireR', seg=(8, 5))
    m.bm_((0, 0.05, 1.2), (0, -0.65, 1.45), 0.11, 'fireR')
    m.cy((0, -0.65, 1.45), 0.08, 0.13, 0.25, 'steelL', seg=8, rot=(-70, 0, 0))
    m.bm_((0.12, 0.2, 1.2), (0.12, 0.45, 0.95), 0.03, 'steelD', hull='none')
    make('FoamMonitor', m, ao, cols=[cb(-0.2, -0.2, 0, 0.2, 0.2, 1.3)])
    # lashing-gear cage [3,2]
    m = new(pal)
    m.bx(-1.4, 1.4, -0.9, 0.9, 0.0, 0.12, 'yelD', cull='b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.bx(sx * 1.4 - (0.06 if sx > 0 else 0), sx * 1.4 + (0.06 if sx < 0 else 0), sy * 0.9 - (0.06 if sy > 0 else 0),
                 sy * 0.9 + (0.06 if sy < 0 else 0), 0.12, 1.5, 'yelD')
    m.bx(-1.4, 1.4, -0.9, 0.9, 1.5, 1.58, 'yelD')
    for fy in (-1, 1):
        for k in range(8):
            x = -1.12 + k * 0.32
            m.bx(x - 0.015, x + 0.015, fy * 0.9 - 0.015, fy * 0.9 + 0.015, 0.12, 1.5, 'steelD', hull='none', cull='tb')
    for fx in (-1, 1):
        for k in range(4):
            y = -0.54 + k * 0.36
            m.bx(fx * 1.4 - 0.015, fx * 1.4 + 0.015, y - 0.015, y + 0.015, 0.12, 1.5, 'steelD', hull='none', cull='tb')
    for k in range(6):   # twistlocks piled inside
        x, y = -0.9 + (k % 3) * 0.75, -0.35 + (k // 3) * 0.6
        m.bx(x - 0.22, x + 0.22, y - 0.16, y + 0.16, 0.12, 0.42 + (k % 3) * 0.1, 'steel' if k % 2 else 'galv', hull='none', cull='b')
    for k in range(6):
        m.bm_((-1.2 + k * 0.4, -0.7, 0.2), (-1.0 + k * 0.4, 0.6, 1.3), 0.03, 'galv', hull='none')
    make('LashCage', m, ao, cols=[cb(-1.4, -0.9, 0, 1.4, 0.9, 1.58)])
    # raised manhole 1x1: coaming, hinged lid, butterfly nuts
    m = new(pal)
    m.bx(-0.4, 0.4, -0.4, 0.4, 0.0, 0.45, 'deckGD', bevel=True, cull='b')
    m.cy((0, 0, 0.45), 0.36, 0.36, 0.06, 'deckG', seg=12)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        m.cy((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.51), 0.03, 0.03, 0.06, 'steelD', seg=6, hull='none')
    m.bx(-0.12, 0.12, 0.38, 0.45, 0.3, 0.5, 'steelD', hull='none')
    make('Manhole', m, ao, cols=[cb(-0.4, -0.4, 0, 0.4, 0.4, 0.51)])


# ================================================================ lifeboat davits [3,8]
def boat(m, x, y, z, L, W, enclosed=True):
    """boat along Blender Y centred on (x, y), keel at z"""
    old = m.parent
    m.parent = old @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    hw = W / 2
    hull = [(-hw * 0.55, 0.0), (hw * 0.55, 0.0), (hw, 0.55), (hw, 1.0), (-hw, 1.0), (-hw, 0.55)]
    m.prism(hull, -L / 2 + 1.0, L / 2 - 1.0, ['paper'])
    m.prism([(hw + 0.004, 0.88), (hw + 0.004, 0.98), (-hw - 0.004, 0.98), (-hw - 0.004, 0.88)], -L / 2 + 1.01, L / 2 - 1.01, ['orange'], hull='none')
    if enclosed:
        top = [(-hw, 1.0), (hw, 1.0), (hw * 0.85, 1.75), (hw * 0.4, 2.05), (-hw * 0.4, 2.05), (-hw * 0.85, 1.75)]
        m.prism(top, -L / 2 + 1.02, L / 2 - 1.02, ['orange'])
        for k in range(5):   # windows
            xx = -L / 2 + 1.6 + k * (L - 3.2) / 4
            m.bx(xx - 0.18, xx + 0.18, -hw * 0.9 - 0.02, hw * 0.9 + 0.02, 1.35, 1.6, 'ink', hull='none')
        m.cy((L / 2 - 2.0, 0, 2.05), 0.35, 0.35, 0.3, 'orange', seg=10)
    m.parent = old
    for sy in (-1, 1):   # bow and stern caps
        m.sp((x, y + sy * (L / 2 - 1.0), z + 1.0 if enclosed else z + 0.6), 1.0, 'orange' if enclosed else 'paper',
             seg=(10, 6), scale=(hw, 1.0, 1.0 if enclosed else 0.6))


def build_davits(pal, ao):
    # gravity davit with an enclosed lifeboat hanging outboard (-X); its frames stand in the walkway (x 0 .. 1.4)
    m = new(pal)
    bx_, bz = -4.3, 2.1
    for y in (-2.6, 2.6):
        m.bx(0.0, 1.4, y - 0.35, y + 0.35, 0.0, 0.3, 'deckGD', cull='b')
        m.bm_((1.1, y, 0.3), (0.2, y, 4.6), 0.3, 'supWD')
        m.bm_((0.2, y, 4.6), (bx_ + 0.2, y, 5.9), 0.26, 'supWD')
        m.bm_((0.9, y, 0.3), (0.3, y, 2.4), 0.18, 'supWD')
        m.cy((bx_ + 0.2, y - 0.15, 5.75), 0.18, 0.18, 0.3, 'steelD', seg=8, rot=(-90, 0, 0))
        m.bm_((bx_ + 0.2, y, 5.6), (bx_ + 0.2, y, bz + 2.1), 0.04, 'ink', hull='none')
    m.cy((0.9, -1.6, 0.3), 0.3, 0.3, 0.5, 'steelD', seg=10, rot=(-90, 0, 0))
    boat(m, bx_, 0.0, bz, 7.6, 2.8, enclosed=True)
    ib_text.draw(m, 'HALCYON VEGA 1', bx_ + 1.404, 0.0, bz + 0.62, 0.16, 'ink', face='x+', font='cond')
    make('Davit_Lifeboat', m, ao, cols=[cb(0.0, -2.95, 0, 1.4, -2.25, 2.6), cb(0.0, 2.25, 0, 1.4, 2.95, 2.6)])
    # rescue boat on a single slewing davit
    m = new(pal)
    m.cy((0.6, 1.8, 0.0), 0.4, 0.4, 0.3, 'deckGD', seg=10)
    m.cy((0.6, 1.8, 0.3), 0.25, 0.22, 3.6, 'supWD', seg=10)
    m.bm_((0.6, 1.8, 3.7), (-3.6, 0.2, 5.2), 0.24, 'supWD')
    m.bx(0.3, 0.9, 1.0, 1.5, 0.3, 1.1, 'engGD', bevel=True)
    m.bm_((-3.6, 0.2, 5.0), (-3.6, 0.2, 3.6), 0.04, 'ink', hull='none')
    boat(m, -3.6, 0.0, 2.6, 5.2, 2.0, enclosed=False)
    m.bx(-4.0, -3.2, -0.4, 0.2, 3.2, 3.9, 'steelL', bevel=True)
    for k in range(3):
        m.bx(-4.4 + k * 0.4, -4.1 + k * 0.4, 1.0, 1.4, 3.15, 3.45, 'orange', hull='none')
    make('Davit_Rescue', m, ao, cols=[cb(0.2, 1.4, 0, 1.0, 2.2, 3.9)])
