"""kit-cargoship engine room: the six-cylinder two-stroke main engine (bedplate, frame box with crankcase doors,
cylinder block, cylinder covers and exhaust valves, exhaust and scavenge-air receivers, turbochargers, the uptake,
the turning wheel at the aft end), diesel generator sets, purifiers, pumps, starting-air bottles, the auxiliary boiler,
the engine control room behind glass, the workshop, the main switchboard, valve manifolds, a settling tank and the
propeller shaft line (static guards and bearings; the turning shaft is an overlay the theme spins).

The engine's front (Blender -Y, game south) is its free end; the aft end (+Y) couples to the shaft line."""
import math

from cargo_base import *  # noqa: F401,F403
import ib_text

NCYL, PITCH = 6, 3.4
CYL_Y = [-(NCYL - 1) / 2 * PITCH + k * PITCH for k in range(NCYL)]


def flange_tube(m, a, b, r, c, seg=8):
    tube(m, a, b, r, c, seg=seg)
    for p in (a, b):
        m.cy((p[0], p[1], p[2] - 0.03), r + 0.05, r + 0.05, 0.06, 'steelD', seg=seg, hull='none')


def build_main_engine(pal, ao):
    # ---- body: bedplate, frame box (A-frames and crankcase doors), cylinder block
    m = new(pal)
    m.bx(-2.6, 2.6, -11.0, 11.0, 0.0, 1.6, 'engGD', cull='b', bevel=True)
    for sx in (-1, 1):
        xf = sx * 2.603
        f = rq if sx > 0 else lq
        for k in range(6):
            y = -9.5 + k * 3.8
            f(m, xf, y - 0.15, y + 0.15, 0.25, 0.45, 'ink')
        f(m, xf, -11.0, 11.0, 1.42, 1.5, 'engG')
    m.bx(-2.2, 2.2, -10.5, 10.5, 1.6, 5.6, 'engG', bevel=True)
    for sx in (-1, 1):
        xf = sx * 2.203
        f = rq if sx > 0 else lq
        for y in CYL_Y:   # crankcase doors with relief valves, A-frame columns between them
            f(m, xf, y - 0.75, y + 0.75, 2.2, 4.4, 'engGD')
            f(m, xf + sx * 0.003, y - 0.6, y + 0.6, 2.35, 4.25, 'engG')
            m.cy((sx * 2.2, y, 3.3), 0.2, 0.2, 0.18, 'steelL', seg=6, rot=(0, sx * 90, 0), hull='none')
        for y in [CYL_Y[0] - PITCH / 2] + [yy + PITCH / 2 for yy in CYL_Y]:
            f(m, xf, y - 0.15, y + 0.15, 1.6, 5.6, 'engGD')
        f(m, xf + sx * 0.003, -10.5, 10.5, 5.3, 5.36, 'yel')
        ib_text.draw(m, 'KORVA 6K72', xf + sx * 0.003, 0.0, 4.65, 0.42, 'paper', face='x+' if sx > 0 else 'x-', font='display', maxw=4.0)
    m.bx(-1.9, 1.9, -10.2, 10.2, 5.6, 8.6, 'engG', bevel=True)
    for sx in (-1, 1):
        xf = sx * 1.903
        f = rq if sx > 0 else lq
        for y in CYL_Y:
            f(m, xf, y - 1.4, y + 1.4, 6.0, 8.2, 'engGD')
            f(m, xf + sx * 0.003, y - 1.3, y + 1.3, 6.1, 8.1, 'engG')
            m.cy((sx * 1.9, y + 0.8, 7.0), 0.12, 0.12, 0.3, 'fireR', seg=6, rot=(0, sx * 90, 0), hull='none')
    # front (free end): chain casing cover, local control stand
    fq(m, -2.0, 2.0, -10.503, 1.8, 5.3, 'engGD')
    fq(m, -1.6, 1.6, -10.506, 2.0, 5.1, 'engG')
    m.bx(-1.2, 1.2, -11.9, -11.1, 0.0, 1.5, 'supWD', bevel=True)
    m.bx(-1.15, 1.15, -12.0, -11.6, 1.5, 1.9, 'supWD')
    fq(m, -1.0, 1.0, -12.003, 1.55, 1.85, 'steelD')
    for k in range(5):
        fq(m, -0.86 + k * 0.4, -0.74 + k * 0.4, -12.006, 1.62, 1.78, 'paper' if k % 2 else 'amber')
    fq(m, -1.0, 1.0, -11.903, 0.6, 1.2, 'steelL')
    text_front(m, 'LOCAL CONTROL', 0.025, -11.906, 0.0, 0.83, 'ink')
    make('Landmark_Engine', m, ao, cols=[cb(-2.6, -11.0, 0, 2.6, 11.0, 1.6), cb(-2.2, -10.5, 1.6, 2.2, 10.5, 5.6),
                                          cb(-1.9, -10.2, 5.6, 1.9, 10.2, 8.6), cb(-1.2, -12.0, 0, 1.2, -11.0, 1.9)])
    # ---- top: cylinder covers, exhaust valves and actuators, the exhaust receiver, top gratings
    m = new(pal)
    for y in CYL_Y:
        m.cy((0, y, 8.6), 0.95, 0.9, 0.5, 'engGD', seg=10)
        m.cy((0, y, 9.1), 0.5, 0.5, 1.0, 'engG', seg=8)
        m.cy((0, y, 10.1), 0.36, 0.36, 0.35, 'steelL', seg=8, hull='none')
        m.bx(-0.25, 0.25, y - 0.25, y + 0.25, 10.45, 10.75, 'fireR', cull='b')
        tube(m, (0.45, y, 9.7), (2.3, y, 9.25), 0.28, 'galv', seg=8)
        m.bx(-1.75, -1.2, y - 0.5, y + 0.5, 8.6, 9.5, 'steelD', cull='b')   # hydraulic cylinder unit
    m.cy((3.0, -10.2, 9.0), 0.85, 0.85, 20.2, 'galv', seg=14, rot=(-90, 0, 0))
    for y in (-10.2, 10.0):
        m.cy((3.0, y - 0.06, 9.0), 0.9, 0.9, 0.12, 'steelD', seg=14, rot=(-90, 0, 0), hull='none')
    for k in range(3):
        m.cy((3.0, -6.0 + k * 6.0, 9.0), 0.87, 0.87, 0.08, 'steelL', seg=14, rot=(-90, 0, 0), hull='none', caps=False)
    for sx in (-1, 1):   # top gratings between the covers and the receivers, rails
        x0, x1 = sorted((sx * 1.9, sx * 2.3))
        m.bx(x0, x1, -10.1, 10.1, 8.5, 8.6, 'galv')
    rail_y(m, -2.3, -10.0, 10.0, 8.6, c='yel', post=2.0, toe=False)
    for sy in (-1, 1):   # end rails over the cylinder block
        rail_run(m, -1.9, 1.9, sy * 10.15, 8.6, c='yel', post=1.9, toe=False)
    make('Landmark_EngineTop', m, ao, cols=[cb(-1.0, -10.2, 8.6, 1.0, 10.2, 10.8), cb(2.15, -10.2, 8.15, 3.85, 10.2, 9.85)])
    # ---- aft and sides: turbochargers and the uptake, scavenge-air receiver and air coolers, turning wheel, ladders
    m = new(pal)
    m.cy((-2.75, -10.0, 4.0), 0.72, 0.72, 19.2, 'engGD', seg=12, rot=(-90, 0, 0))
    for y in CYL_Y:
        tube(m, (-2.2, y, 4.0), (-2.6, y, 4.0), 0.25, 'engG', seg=8)
    for y in (-9.4, 8.6):   # scavenge air coolers at the receiver ends
        m.bx(-4.3, -3.3, y - 0.9, y + 0.9, 2.9, 4.8, 'engG', bevel=True)
        for k in range(4):
            lq(m, -4.303, y - 0.75 + k * 0.45, y - 0.5 + k * 0.45, 3.1, 4.6, 'engGD')
        tube(m, (-3.2, y + 0.01, 4.0), (-3.36, y + 0.01, 4.0), 0.45, 'engGD', seg=10)
    for y in (6.0, 9.6):   # turbochargers on the exhaust side, over the aft cylinders
        m.cy((2.0, y, 10.4), 0.85, 0.85, 1.6, 'galv', seg=10, rot=(0, 90, 0))
        m.cy((3.6, y, 10.4), 0.95, 0.75, 0.9, 'steelL', seg=10, rot=(0, 90, 0))
        m.cy((4.5, y, 10.4), 0.78, 0.78, 0.04, 'steelD', seg=10, rot=(0, 90, 0), hull='none')
        m.cy((2.6, y, 11.25), 0.55, 0.55, 1.75, 'galv', seg=10)
        m.cy((2.6, y, 11.25), 0.58, 0.58, 0.1, 'steelD', seg=10, hull='none', caps=False)
        tube(m, (3.0, y, 9.85), (2.3, y, 9.85), 0.4, 'galv', seg=10)
        m.bx(1.2, 4.0, y - 0.75, y + 0.75, 8.6, 9.6, 'steelD')
    # turning wheel and turning gear at the aft end
    m.cy((0.0, 10.6, 1.45), 1.35, 1.35, 0.5, 'engGD', seg=16, rot=(-90, 0, 0))
    for k in range(8):
        a = k / 8 * 2 * math.pi
        m.bx(math.cos(a) * 1.3 - 0.06, math.cos(a) * 1.3 + 0.06, 11.103, 11.107, 1.45 + math.sin(a) * 1.3 - 0.06, 1.45 + math.sin(a) * 1.3 + 0.06, 'yel', hull='none')
    m.cy((0.0, 11.1, 1.4), 0.4, 0.4, 0.9, 'engG', seg=10, rot=(-90, 0, 0))
    m.bx(1.6, 2.4, 10.4, 11.4, 0.0, 1.3, 'engG', bevel=True)
    m.cy((2.0, 11.0, 1.3), 0.25, 0.25, 0.6, 'signB', seg=8)
    for sx in (-1, 1):   # ladders up the frame box, side platforms at the cylinder covers
        m.parent = Matrix.Translation((sx * 2.2, -6.8, 0.0)) @ Matrix.Rotation(math.radians(-90 * sx), 4, 'Z')
        ladder(m, 0.0, 0.0, 1.63, 8.55, c='yel', face=-1)
        m.parent = Matrix.Identity(4)
    make('Landmark_EngineAft', m, ao, cols=[cb(-3.47, -10.0, 3.28, -2.2, 9.2, 4.72), cb(-4.3, -10.3, 2.9, -3.3, -8.5, 4.8),
                                             cb(-4.3, 7.7, 2.9, -3.3, 9.5, 4.8), cb(-1.35, 10.35, 0.1, 1.35, 11.6, 2.8),
                                             cb(1.6, 10.4, 0, 2.4, 11.4, 1.6)])


def build_generators(pal, ao):
    """diesel generator set [4,9]: base frame, inline-six engine, turbo and silencer, alternator"""
    for name in ('Genset_A', 'Genset_B'):
        m = new(pal)
        m.bx(-1.4, 1.4, -4.3, 4.3, 0.0, 0.45, 'steelD', cull='b')
        m.bx(-0.9, 0.9, -4.0, 0.9, 0.45, 2.2, 'engG', bevel=True)
        for k in range(6):
            y = -3.6 + k * 0.75
            if name == 'Genset_B' and k == 2:   # one head off for overhaul, on a pallet beside it
                m.bx(-0.55, 0.55, y - 0.3, y + 0.3, 2.2, 2.25, 'oil', hull='none')
                continue
            m.bx(-0.6, 0.6, y - 0.32, y + 0.32, 2.2, 2.65, 'engGD', bevel=True)
            m.cy((0.0, y, 2.65), 0.12, 0.12, 0.12, 'steelL', seg=6, hull='none')
        for sx in (-1, 1):
            xf = sx * 0.903
            f = rq if sx > 0 else lq
            for k in range(6):
                y = -3.6 + k * 0.75
                f(m, xf, y - 0.25, y + 0.25, 0.8, 1.6, 'engGD')
        m.cy((1.05, -3.95, 2.3), 0.13, 0.13, 4.4, 'galv', seg=8, rot=(-90, 0, 0))
        m.cy((0.6, -4.5 + 0.3, 2.0), 0.45, 0.45, 0.7, 'galv', seg=10, rot=(-90, 0, 0))
        m.cy((0.6, -3.9, 2.7), 0.32, 0.32, 1.4, 'galv', seg=10)
        m.cy((0.6, -3.9, 4.1), 0.35, 0.35, 0.08, 'steelD', seg=10, hull='none')
        m.cy((0.0, 0.9, 1.5), 1.05, 1.05, 3.1, 'cNav', seg=14, rot=(-90, 0, 0))
        for y in (0.95, 3.95):
            m.cy((0.0, y - 0.05, 1.5), 1.08, 1.08, 0.1, 'steelD', seg=14, rot=(-90, 0, 0), hull='none', caps=False)
        m.bx(-0.6, 0.6, 1.6, 3.2, 2.5, 2.9, 'cNav', bevel=True)
        fq(m, -0.5, 0.5, -4.003, 0.7, 1.4, 'steelL')
        text_front(m, 'D/G', 0.05, -4.006, 0.0, 0.9, 'ink')
        make(name, m, ao, cols=[cb(-1.4, -4.3, 0, 1.4, 4.3, 0.45), cb(-1.0, -4.5, 0.45, 1.0, 4.0, 2.7), cb(-1.05, 0.9, 0.45, 1.05, 4.0, 2.9)])


def build_aux(pal, ao):
    # purifiers [2,2]: two disc-stack separators on a frame with their heaters and pipes
    m = new(pal)
    m.bx(-0.95, 0.95, -0.9, 0.9, 0.0, 0.2, 'steelD', cull='b')
    for x in (-0.45, 0.45):
        m.bx(x - 0.32, x + 0.32, -0.3, 0.34, 0.2, 0.75, 'engGD', bevel=True)
        m.cy((x, 0.02, 0.75), 0.36, 0.3, 0.55, 'engG', seg=12)
        m.cy((x, 0.02, 1.3), 0.25, 0.12, 0.25, 'steelL', seg=10)
        m.cy((x, 0.02, 1.55), 0.06, 0.06, 0.25, 'steelD', seg=6)
        tube(m, (x, 0.02, 1.7), (x, 0.7, 1.7), 0.05, 'rust', seg=6)
    m.cy((-0.95, 0.7, 1.7), 0.06, 0.06, 1.9, 'rust', seg=6, rot=(0, 90, 0))
    m.bx(-0.85, 0.85, 0.45, 0.85, 0.2, 1.0, 'steelL', bevel=True)
    fq(m, -0.6, 0.6, -0.903, 0.04, 0.17, 'yel')
    make('Purifiers', m, ao, cols=[cb(-0.85, -0.35, 0, 0.85, 0.85, 1.8)])
    # pumps [2,1]: two vertical centrifugal pumps with motors, pipes and valve handwheels
    m = new(pal)
    m.bx(-0.95, 0.95, -0.4, 0.4, 0.0, 0.15, 'steelD', cull='b')
    for x, c in ((-0.45, 'deckG'), (0.45, 'signB')):
        m.cy((x, 0, 0.15), 0.3, 0.3, 0.35, 'engGD', seg=10)
        m.cy((x, 0, 0.5), 0.18, 0.22, 0.3, 'engG', seg=10)
        m.cy((x, 0, 0.8), 0.26, 0.26, 0.55, 'engG', seg=10)
        m.cy((x, 0, 1.35), 0.2, 0.15, 0.1, 'engGD', seg=10)
        tube(m, (x, 0.0, 0.32), (x, 0.4, 0.32), 0.1, c, seg=8)
        tube(m, (x, 0.0, 0.32), (x, -0.4, 0.32), 0.1, c, seg=8)
        m.cy((x, -0.34, 0.45), 0.02, 0.02, 0.3, 'steelD', seg=6, hull='none')
        m.cy((x, -0.34, 0.75), 0.13, 0.13, 0.03, 'fireR', seg=8)
    make('Pumps', m, ao, cols=[cb(-0.8, -0.3, 0, 0.8, 0.3, 1.45)])
    # starting-air bottles [2,1]
    m = new(pal)
    for x in (-0.48, 0.48):
        m.cy((x, 0, 0.0), 0.32, 0.32, 0.2, 'steelD', seg=10)
        m.cy((x, 0, 0.2), 0.45, 0.45, 2.8, 'supWD', seg=12)
        m.sp((x, 0, 3.0), 0.45, 'supWD', seg=(12, 5), scale=(1, 1, 0.55))
        m.cy((x, 0, 1.0), 0.455, 0.455, 0.12, 'signB', seg=12, hull='none', caps=False)
        m.cy((x, 0, 3.2), 0.07, 0.07, 0.35, 'steelD', seg=6)
        m.cy((x, 0, 3.5), 0.14, 0.14, 0.03, 'fireR', seg=8)
        m.cy((x, -0.45, 1.6), 0.11, 0.11, 0.04, 'paper', seg=8, rot=(90, 0, 0), hull='none')
    tube(m, (-0.48, 0.0, 3.45), (0.48, 0.0, 3.45), 0.05, 'steelD')
    make('AirBottles', m, ao, cols=[cb(-0.93, -0.45, 0, 0.93, 0.45, 3.5)])
    # auxiliary boiler [3,3]: lagged shell, burner, gauge glass, a ladder, the uptake to the deckhead
    m = new(pal)
    m.cy((0, 0, 0), 1.3, 1.3, 0.3, 'steelD', seg=14)
    m.cy((0, 0, 0.3), 1.2, 1.2, 8.2, 'galv', seg=12, caps=False)
    for z in (2.5, 6.0):
        m.cy((0, 0, z), 1.205, 1.205, 0.06, 'steelL', seg=12, hull='none', caps=False)
    m.cy((0, 0, 8.5), 1.2, 0.5, 0.9, 'galv', seg=12)
    m.cy((0, 0, 9.4), 0.5, 0.5, 3.56, 'galv', seg=12)
    m.bx(-0.6, 0.6, -1.5, -1.1, 0.3, 1.6, 'fireR', bevel=True, cull='b')
    m.cy((0, -1.5, 0.95), 0.3, 0.3, 0.3, 'steelD', seg=10, rot=(90, 0, 0))
    m.bx(0.75, 0.85, -0.98, -0.88, 2.0, 3.0, 'glass')
    ib_text.draw(m, 'AUX BOILER', 0.0, -1.21, 4.4, 0.24, 'ink', face='y-', font='cond')
    m.parent = Matrix.Translation((-0.85, 0.85, 0.0)) @ Matrix.Rotation(math.radians(135), 4, 'Z')
    ladder(m, 0.0, 0.0, 0.32, 8.9, c='yel', face=1)
    m.parent = Matrix.Identity(4)
    make('Boiler', m, ao, cols=[cb(-1.2, -0.5, 0, 1.2, 0.5, 8.6), cb(-0.5, -1.2, 0, 0.5, 1.2, 8.6), cb(-0.85, -0.85, 0, 0.85, 0.85, 8.6), cb(-0.6, -1.5, 0.3, 0.6, -1.1, 1.6)])
    # settling tank [4,3]: a steel tank box, sight glass, manhole, ladder, label
    m = new(pal)
    m.bx(-1.9, 1.9, -1.3, 1.3, 0.0, 3.4, 'supWD', bevel=True, cull='b')
    for x in (-1.0, 0.0, 1.0):
        fq(m, x - 0.04, x + 0.04, -1.303, 0.0, 3.4, 'supG')
    m.bx(1.3, 1.4, -1.36, -1.3, 0.4, 3.0, 'glass')
    fq(m, -1.6, -0.2, -1.306, 2.2, 2.8, 'paper')
    text_front(m, 'H.F.O. SETTLING', 0.028, -1.309, -0.9, 2.42, 'ink')
    m.cy((0.5, -1.3, 1.0), 0.32, 0.32, 0.06, 'steelD', seg=10, rot=(90, 0, 0))
    m.cy((0.0, 0.0, 3.4), 0.12, 0.12, 0.6, 'rust', seg=6)
    m.parent = Matrix.Translation((-1.903, 0.5, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, 'Z')
    ladder(m, 0.0, 0.0, 0.0, 3.9, c='yel', face=-1)
    m.parent = Matrix.Identity(4)
    make('Tank', m, ao, cols=[cb(-1.9, -1.3, 0, 1.9, 1.3, 3.4)])
    # valve manifold [2,1]: a header with colour-coded valves on stands
    m = new(pal)
    tube(m, (-0.95, 0.0, 0.85), (0.95, 0.0, 0.85), 0.12, 'deckG', seg=8)
    for x in (-0.95, 0.95):
        m.bx(x - 0.05 if x < 0 else x - 0.1, x + 0.1 if x < 0 else x + 0.05, -0.1, 0.1, 0.0, 0.8, 'steelD')
    for k, c in enumerate(('fireR', 'yel', 'signB', 'exitG')):
        x = -0.66 + k * 0.44
        m.cy((x, 0, 0.85), 0.08, 0.08, 0.35, 'steelL', seg=6)
        m.cy((x, 0, 1.4), 0.14, 0.14, 0.03, c, seg=8)
        tube(m, (x, 0.0, 0.85), (x, 0.0, 0.1), 0.06, 'deckG', seg=6)
    make('Manifold', m, ao, cols=[cb(-0.95, -0.15, 0, 0.95, 0.15, 1.45)])
    # workshop bench [4,1]: bench with a vice, a drill press, a small lathe
    m = new(pal)
    m.bx(-1.95, -0.05, -0.38, 0.38, 0.85, 0.92, 'wood', bevel=True)
    for x in (-1.85, -0.15):
        for y in (-0.3, 0.3):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.85, 'steelD', hull='none')
    m.bx(-1.86, -0.14, -0.31, 0.31, 0.25, 0.3, 'steelD', hull='none')
    m.bx(-1.6, -1.3, -0.25, -0.05, 0.92, 1.1, 'signB')
    m.bx(-0.9, -0.5, -0.1, 0.25, 0.92, 1.0, 'fireR')
    m.cy((0.3, 0.1, 0.0), 0.15, 0.15, 1.5, 'steelD', seg=8)
    m.bx(0.2, 0.55, -0.2, 0.25, 1.3, 1.65, 'engG', bevel=True)
    m.bx(0.15, 0.6, -0.25, 0.25, 0.0, 0.06, 'steelD', cull='b')
    m.bx(0.85, 1.95, -0.3, 0.3, 0.0, 0.8, 'engGD', bevel=True)
    m.bx(0.85, 1.25, -0.25, 0.25, 0.8, 1.25, 'engG', bevel=True)
    m.cy((1.25, 0.0, 1.05), 0.06, 0.06, 0.6, 'steelL', seg=6, rot=(0, 90, 0))
    m.bx(1.6, 1.9, -0.2, 0.2, 0.8, 1.06, 'engG')
    make('Workshop', m, ao, cols=[cb(-1.95, -0.38, 0, -0.05, 0.38, 0.92), cb(0.15, -0.25, 0, 0.6, 0.25, 1.65), cb(0.85, -0.3, 0, 1.95, 0.3, 1.25)])
    # main switchboard [6,1]: cabinets with meters, breakers and a mimic line
    m = new(pal)
    m.bx(-2.95, 2.95, -0.35, 0.4, 0.0, 2.2, 'supWD', bevel=True, cull='b')
    for k in range(6):
        x = -2.5 + k * 1.0
        fq(m, x - 0.45, x + 0.45, -0.353, 0.15, 2.05, 'steelL')
        fq(m, x - 0.36, x + 0.36, -0.356, 1.65, 1.85, 'paper')
        fq(m, x - 0.3, x + 0.3, -0.356, 0.9, 1.3, 'steelD')
        fq(m, x - 0.2, x - 0.1, -0.359, 1.0, 1.2, 'exitG' if k % 2 else 'fireR')
    fq(m, -2.9, 2.9, -0.359, 1.5, 1.55, 'signB')
    fq(m, -1.5, 1.5, -0.353, 2.07, 2.18, 'paper')
    text_front(m, 'MAIN SWITCHBOARD', 0.018, -0.356, 0.0, 2.08, 'ink')
    make('Switchboard', m, ao, cols=[cb(-2.95, -0.35, 0, 2.95, 0.4, 2.2)])


def build_control_room(pal, ao):
    """engine control room [8,6] on the upper flat: windows along the front with consoles inside"""
    m = new(pal)
    W2, D2, Hr = 4.0, 3.0, 3.0
    # walls: back, sides, front sill and head with mullions (open panes: you see in)
    m.bx(-W2, W2, D2 - 0.15, D2, 0.0, Hr, 'supWD', cull='b')
    for sx in (-1, 1):
        a, b = sorted((sx * W2, sx * (W2 - 0.15)))
        m.bx(a, b, -D2, D2 - 0.15, 0.0, Hr, 'supWD', cull='b')
    m.bx(-W2 + 0.15, W2 - 0.15, -D2, -D2 + 0.15, 0.0, 1.0, 'supWD', cull='b')
    m.bx(-W2 + 0.15, W2 - 0.15, -D2, -D2 + 0.15, 2.5, Hr, 'supWD')
    for k in range(9):
        x = -W2 + 0.19 + k * (2 * W2 - 0.38) / 8
        m.bx(x - 0.04, x + 0.04, -D2, -D2 + 0.1, 1.0, 2.5, 'steelD')
    for k in range(8):   # glints across the panes
        x = -W2 + 0.4 + k * (2 * W2 - 0.3) / 8
        poly(m, [(x, -D2 + 0.05, 1.3), (x + 0.12, -D2 + 0.05, 1.3), (x + 0.42, -D2 + 0.05, 2.2), (x + 0.3, -D2 + 0.05, 2.2)], 'glass', (0, -1, 0))
    m.bx(-W2, W2, -D2, D2, Hr, Hr + 0.15, 'supWD')
    fq(m, -2.2, 2.2, -D2 - 0.003, 2.62, 2.9, 'signB')
    text_front(m, 'ENGINE CONTROL ROOM', 0.03, -D2 - 0.006, 0.0, 2.68, 'paper')
    # inside: floor, console desk with screens, chairs, an alarm panel and a mimic board on the back wall, lights
    uq(m, -W2 + 0.15, W2 - 0.15, -D2 + 0.15, D2 - 0.15, 0.03, 'steelL')
    m.bx(-3.2, 3.2, -1.6, -0.8, 0.0, 0.85, 'supG', bevel=True)
    for k in range(6):
        x = -2.7 + k * 1.08
        m.bx(x - 0.4, x + 0.4, -1.1, -1.0, 0.85, 1.4, 'ink')
        fq(m, x - 0.35, x + 0.35, -1.103, 0.9, 1.35, 'teal')
    for x in (-1.6, 0.4, 2.0):
        m.cy((x, -0.1, 0.0), 0.05, 0.05, 0.45, 'steelD', seg=6)
        m.bx(x - 0.25, x + 0.25, -0.35, 0.15, 0.45, 0.55, 'signB')
        m.bx(x - 0.25, x + 0.25, 0.1, 0.18, 0.55, 1.0, 'signB')
    fq(m, -3.6, 3.6, D2 - 0.153, 1.0, 2.4, 'steelL')
    for k in range(12):
        x = -3.3 + k * 0.6
        fq(m, x - 0.18, x + 0.18, D2 - 0.156, 1.9, 2.2, 'amber' if k % 3 == 0 else 'exitG')
    fq(m, -3.4, 3.4, D2 - 0.156, 1.4, 1.46, 'signB')
    fq(m, -3.4, -3.34, D2 - 0.159, 1.1, 1.46, 'signB')
    for x in (-2.0, 2.0):
        dq(m, x - 0.6, x + 0.6, -0.4, 0.4, Hr - 0.003, 'light')
    # side door with a porthole
    rq(m, W2 + 0.003, 0.3, 1.3, 0.0, 2.1, 'supG')
    m.cy((W2 + 0.006, 0.8, 1.6), 0.15, 0.15, 0.004, 'glassD', seg=10, rot=(0, 90, 0), hull='none')
    make('Landmark_ECR', m, ao, cols=[cb(-W2, -D2, 0, W2, D2, Hr + 0.15)])


def build_shaft(pal, ao):
    """shaft line cells [3,1] along Blender Y: guard rails on both sides (and an intermediate bearing); the turning
    shaft itself is ShaftSpin (an overlay mesh, axis along Y at z 1.4)"""
    for name in ('Shaft', 'ShaftBearing'):
        m = new(pal)
        for sx in (-1, 1):
            x = sx * 1.2
            m.bx(x - 0.03, x + 0.03, -0.5, 0.5, 1.75, 1.81, 'yel', hull='noend')
            m.bx(x - 0.02, x + 0.02, -0.5, 0.5, 0.9, 0.94, 'yel', hull='none')
            m.bx(x - 0.03, x + 0.03, -0.03, 0.03, 0.0, 1.75, 'yel', hull='none', cull='bt')
            m.bx(x - 0.01, x + 0.01, -0.5, 0.5, 0.0, 0.12, 'yel', hull='none')
        if name == 'ShaftBearing':
            m.bx(-0.55, 0.55, -0.35, 0.35, 0.0, 1.0, 'engGD', bevel=True, cull='b')
            m.cy((0.0, -0.3, 1.4), 0.5, 0.5, 0.6, 'engG', seg=12, rot=(-90, 0, 0))
            m.bx(-0.65, 0.65, -0.4, 0.4, 0.0, 0.1, 'steelD', cull='b')
            m.cy((0.4, 0.0, 1.85), 0.04, 0.04, 0.3, 'galv', seg=6)
        make(name, m, ao, cols=[cb(-1.24, -0.5, 0, 1.24, 0.5, 1.9)], side=0.45)
    m = new(pal)
    m.cy((0.0, -0.5, 1.4), 0.3, 0.3, 1.0, 'steelL', seg=10, rot=(-90, 0, 0), hull='noend', caps=False)
    m.cy((0.0, -0.1, 1.4), 0.305, 0.305, 0.2, 'yel', seg=10, rot=(-90, 0, 0), hull='none', caps=False)
    m.bx(-0.04, 0.04, -0.5, 0.5, 1.695, 1.705, 'fireR', hull='none')
    make('ShaftSpin', m, ao)
