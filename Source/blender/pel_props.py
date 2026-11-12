"""INKBOLT kit-pelagic props: the jet blast deflector, arresting wires, the helipad markings, deck gear (chocks, tool
chests, extinguishers, fire stations, gas bottles, ammo crates, drums, cargo pallets, floodlights, the ground power
unit), maintenance gear (engine stand, work stand, hoist, bench, shelving), the cargo lift, containers, fuel tanks,
the bund kerb and the fuel lines. Conventions: pel_base.py."""
import math

from pel_base import *  # noqa: F401,F403
from pel_base import new, make, text, hazard, hazard_up


# ================================================================ flight deck gear
def build_jbd(pal, ao):
    """jet blast deflector [8, 2], raised: four water-cooled panels hinged on the +Y edge, leaning back to -Y as they
    rise (the jet stands to the +Y side, its tail toward the deflector); a closed housing behind them"""
    m = new(pal)
    H, YH, YT = 2.6, 0.9, -0.9
    # the panels: one solid wedge (panel face, back plate, sides), the cooling grid painted on the face
    v = [(-4.0, YT, 0.0), (4.0, YT, 0.0), (4.0, YH, 0.0), (-4.0, YH, 0.0), (-4.0, YT, H), (4.0, YT, H), (4.0, YT + 0.12, H), (-4.0, YT + 0.12, H)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    skin(m, (v, f), lambda fc: 'steel' if fc.normal.y > 0.3 else 'navyD')
    # cooling grid on the sloped face: lines along X and the panel joints
    L = math.hypot(H, YH - YT - 0.12)
    n = (0, H / L, (YH - YT - 0.12) / L)

    def on_face(t, x):   # point on the sloped face at fraction t up its height, lifted 4 mm along the normal
        y = YH + (YT + 0.12 - YH) * t
        z = H * t
        return (x, y + n[1] * 0.004, z + n[2] * 0.004)
    for k in range(1, 9):
        t = k / 9
        a, b = on_face(t - 0.012, -3.95), on_face(t + 0.012, 3.95)
        poly(m, [a, (b[0], a[1], a[2]), b, (a[0], b[1], b[2])], 'steelD', n)
    for x in (-2.0, 0.0, 2.0):
        a, b = on_face(0.0, x - 0.03), on_face(1.0, x + 0.03)
        poly(m, [(a[0], a[1] + 0.003 * n[1], a[2] + 0.003 * n[2]), (b[0], a[1] + 0.003 * n[1], a[2] + 0.003 * n[2]),
                 (b[0], b[1] + 0.003 * n[1], b[2] + 0.003 * n[2]), (a[0], b[1] + 0.003 * n[1], b[2] + 0.003 * n[2])], 'dark', n)
    # hinge line, hazard paint along the foot, the hydraulic rams on the back
    m.bx(-4.05, 4.05, YH - 0.05, YH + 0.12, 0.0, 0.12, 'yellow', cull='b')
    for x in (-3.0, -1.0, 1.0, 3.0):
        m.bm_((x, YT - 0.6, 0.05), (x, YT + 0.05, 1.6), 0.14, 'steelD')
        m.bx(x - 0.2, x + 0.2, YT - 0.85, YT - 0.45, 0.0, 0.1, 'steelD', cull='b')
    fq(m, -4.0, 4.0, YT - 0.003, 0.0, 0.5, 'yellow')
    for i in range(8):
        x0 = -4.0 + i * 1.0
        poly(m, [(x0, YT - 0.006, 0.0), (x0 + 0.5, YT - 0.006, 0.0), (x0 + 0.75, YT - 0.006, 0.5), (x0 + 0.25, YT - 0.006, 0.5)], 'black', (0, -1, 0))
    yl = lambda z: YH + (YT + 0.12 - YH) * (z / H)
    make('JBD', m, ao, cols=[cb(-4.0, YT, 0.0, 4.0, yl(0.2) + 0.02, 1.3), cb(-4.0, YT, 1.3, 4.0, yl(1.3) + 0.02, H)])


def build_wires(pal, ao):
    """arresting wire across the runway (rotate 'run': along X), a steel cable lifted on bow-spring supports"""
    for name, sup in (('Wire_A', True), ('Wire_B', False)):
        m = new(pal)
        cyl_x(m, -0.5, 0.5, 0.0, 0.1, 0.022, 'black', seg=5, caps=False)
        uq(m, -0.5, 0.5, -0.08, 0.08, 0.006, 'deck2')
        if sup:
            for x in (-0.25, 0.25):
                m.bx(x - 0.02, x + 0.02, -0.03, 0.03, 0.0, 0.09, 'steelD', hull='none', cull='b')
            m.bx(-0.3, 0.3, -0.05, 0.05, 0.004, 0.02, 'yellow', hull='none', cull='b')
        make(name, m, ao)
    # the deck sheave housing at each end of a wire (flush steel box)
    m = new(pal)
    m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.08, 'steelD', cull='b')
    m.cy((0, 0, 0.08), 0.22, 0.22, 0.04, 'dark', seg=10)
    make('WireEnd', m, ao)


def build_helipad(pal, ao):
    """helipad markings [16, 16] for the 2.4 m dock deck: a dark landing square, the white perimeter, the yellow
    touchdown ring, the H, the name; green edge lights round it"""
    m = new(pal)
    uq(m, -7.6, 7.6, -7.6, 7.6, 0.006, 'deck2')
    for (x0, x1, y0, y1) in ((-7.4, 7.4, -7.4, -7.15), (-7.4, 7.4, 7.15, 7.4), (-7.4, -7.15, -7.15, 7.15), (7.15, 7.4, -7.15, 7.15)):
        uq(m, x0, x1, y0, y1, 0.009, 'white')
    N = 24
    for i in range(N):
        a0, a1 = i / N * 2 * math.pi, (i + 1) / N * 2 * math.pi
        pts = [(math.cos(a) * r, math.sin(a) * r, 0.009) for (a, r) in ((a0, 4.2), (a1, 4.2), (a1, 4.8), (a0, 4.8))]
        poly(m, pts, 'yellow', (0, 0, 1))
    for (x0, x1, y0, y1) in ((-1.7, -1.0, -2.4, 2.4), (1.0, 1.7, -2.4, 2.4), (-1.0, 1.0, -0.33, 0.33)):
        uq(m, x0, x1, y0, y1, 0.012, 'white')
    text(m, 'PB 21', 0.0, -5.9, 0.012, 0.9, 'white', face='up', valign='m')
    for i in range(20):
        t = i / 20 * 4
        side, f = int(t), t - int(t)
        x, y = [(-7.8 + 15.6 * f, -7.8), (7.8, -7.8 + 15.6 * f), (7.8 - 15.6 * f, 7.8), (-7.8, 7.8 - 15.6 * f)][side]
        m.cy((x, y, 0.0), 0.09, 0.07, 0.1, 'lgreen', seg=5, hull='none')
    make('Helipad', m, ao)


# ================================================================ small deck gear
def build_small(pal, ao):
    m = new(pal)   # wheel chocks on their chain, a yellow pair
    for x in (-0.25, 0.25):
        m.prism([(-0.25, 0.0), (0.25, 0.0), (0.12, 0.16), (-0.12, 0.16)], x - 0.12, x + 0.12, ['yellow'])
    m.bm_((-0.13, 0.0, 0.05), (0.13, 0.0, 0.05), 0.03, 'steelD')
    m.bx(-0.35, 0.35, 0.35, 0.42, 0.0, 0.04, 'black', hull='none', cull='b')
    make('Chocks', m, ao, cols=[cb(-0.37, -0.25, 0.0, 0.37, 0.25, 0.16)])
    m = new(pal)   # rolling tool chest (red)
    m.bx(-0.45, 0.45, -0.3, 0.3, 0.12, 1.0, 'fire', cull='b')
    for k in range(5):
        z = 0.22 + k * 0.15
        fq(m, -0.42, 0.42, -0.303, z, z + 0.11, 'redD')
        fq(m, -0.15, 0.15, -0.306, z + 0.07, z + 0.09, 'steel')
    m.bx(-0.47, 0.47, -0.32, 0.32, 1.0, 1.06, 'dark', cull='')
    for (x, y) in ((-0.38, -0.22), (0.38, -0.22), (-0.38, 0.22), (0.38, 0.22)):
        m.cy((x, y, 0.0), 0.06, 0.06, 0.12, 'black', seg=6)
    m.bm_((-0.5, 0.31, 0.9), (0.5, 0.31, 0.9), 0.03, 'steel')
    make('ToolChest', m, ao, cols=[cb(-0.47, -0.32, 0.0, 0.47, 0.32, 1.06)])
    m = new(pal)   # wheeled fire extinguisher (a big red bottle on a trolley)
    m.cy((0, 0.05, 0.12), 0.24, 0.24, 1.0, 'fire', seg=8)
    m.cy((0, 0.05, 1.12), 0.24, 0.08, 0.12, 'fire', seg=8, caps=False)
    m.cy((0, 0.05, 1.22), 0.05, 0.05, 0.12, 'black', seg=6)
    fq(m, -0.12, 0.12, -0.195, 0.5, 0.75, 'white')
    for s in (-1, 1):
        wheel(m, s * 0.3, 0.1, 0.16, 0.16, 0.07, c='tire', hub='steel', seg=8)
    m.bm_((-0.3, 0.3, 0.16), (0.0, 0.32, 1.1), 0.035, 'steelD')
    make('Extinguisher', m, ao, cols=[cb(-0.32, -0.2, 0.0, 0.32, 0.32, 1.25)])
    m = new(pal)   # fire station: a red hose-reel cabinet on legs, foam can, sign
    m.bx(-0.45, 0.45, -0.25, 0.25, 0.5, 1.6, 'fire', cull='')
    for x in (-0.38, 0.38):
        m.bx(x - 0.04, x + 0.04, -0.2, 0.2, 0.0, 0.5, 'steelD', cull='b')
    m.cy((0, -0.25, 1.05), 0.36, 0.36, 0.06, 'redD', seg=12, rot=(90, 0, 0))
    m.cy((0, -0.31, 1.05), 0.12, 0.12, 0.03, 'steel', seg=8, rot=(90, 0, 0))
    m.bx(-0.45, 0.45, -0.27, -0.25, 1.62, 1.95, 'white', cull='')
    text(m, 'FIRE STATION', 0, -0.273, 1.7, 0.12, 'fire', maxw=0.82)
    m.cy((0.3, 0.3, 0.0), 0.15, 0.15, 0.45, 'yellow', seg=8)
    make('FireStation', m, ao, cols=[cb(-0.45, -0.25, 0.5, 0.45, 0.25, 1.95), cb(-0.42, -0.2, 0.0, 0.42, 0.2, 0.5), cb(0.15, 0.15, 0.0, 0.45, 0.45, 0.45)])
    m = new(pal)   # gas bottles in a rack (nitrogen grey, oxygen green)
    m.bx(-0.45, 0.45, -0.35, 0.35, 0.0, 0.06, 'steelD', cull='b')
    for i, (x, y) in enumerate(((-0.25, -0.15), (0.0, -0.15), (0.25, -0.15), (-0.12, 0.15), (0.13, 0.15))):
        c = 'green' if i % 2 else 'dark'
        m.cy((x, y, 0.06), 0.11, 0.11, 1.2, c, seg=6)
        m.cy((x, y, 1.26), 0.11, 0.04, 0.1, c, seg=6, caps=False)
        m.cy((x, y, 1.36), 0.035, 0.035, 0.1, 'brass', seg=4, hull='none')
    m.bm_((-0.45, -0.3, 0.9), (0.45, -0.3, 0.9), 0.04, 'yellow')
    for x in (-0.45, 0.45):
        m.bx(x - 0.025, x + 0.025, -0.33, -0.27, 0.06, 1.0, 'yellow', cull='b')
    make('Gas', m, ao, cols=[cb(-0.45, -0.33, 0.0, 0.45, 0.28, 1.4)])
    m = new(pal)   # ammo crates stacked (olive, stencils)
    for (x0, x1, y0, y1, z0, z1) in ((-0.45, 0.45, -0.3, 0.3, 0.0, 0.42), (-0.4, 0.42, -0.28, 0.3, 0.42, 0.84), (-0.3, 0.32, -0.25, 0.25, 0.84, 1.18)):
        m.bx(x0, x1, y0, y1, z0, z1, 'olive', cull='b')
        fq(m, x0 + 0.05, x1 - 0.05, y0 - 0.003, z0 + 0.06, z0 + 0.1, 'oliveD')
        fq(m, (x0 + x1) / 2 - 0.15, (x0 + x1) / 2 + 0.15, y0 - 0.003, z0 + 0.16, z0 + 0.28, 'yellow')
    make('Crates', m, ao, cols=[cb(-0.45, -0.3, 0.0, 0.45, 0.3, 0.84), cb(-0.3, -0.25, 0.84, 0.32, 0.25, 1.18)])
    m = new(pal)   # three drums on a pallet
    m.bx(-0.48, 0.48, -0.48, 0.48, 0.0, 0.12, 'wood', cull='b')
    for (x, y, c) in ((-0.22, -0.2, 'blue'), (0.22, -0.2, 'blue'), (0.0, 0.22, 'fire')):
        m.cy((x, y, 0.12), 0.21, 0.21, 0.86, c, seg=8)
        for z in (0.42, 0.72):
            m.cy((x, y, 0.12 + z - 0.02), 0.215, 0.215, 0.03, 'dark', seg=8, caps=False, hull='none')
    make('Drums', m, ao, cols=[cb(-0.42, -0.4, 0.0, 0.42, 0.42, 0.98)])
    m = new(pal)   # a cargo pallet: shrink-wrapped boxes with a cargo strap
    m.bx(-0.48, 0.48, -0.48, 0.48, 0.0, 0.13, 'wood', cull='b')
    m.bx(-0.45, 0.45, -0.45, 0.45, 0.13, 1.2, 'cream', cull='b')
    for z in (0.5, 0.88):
        fq(m, -0.45, 0.45, -0.453, z - 0.004, z + 0.004, 'wallD')
    m.bx(-0.06, 0.06, -0.46, 0.46, 0.13, 1.21, 'orange', hull='none', cull='b')
    make('Pallet', m, ao, cols=[cb(-0.46, -0.46, 0.0, 0.46, 0.46, 1.2)])
    m = new(pal)   # deck floodlight mast
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.2, 'steelD', cull='b')
    m.cy((0, 0, 0.2), 0.12, 0.08, 7.0, 'navyD', seg=8)
    m.bx(-0.7, 0.7, -0.08, 0.08, 7.0, 7.12, 'steelD', cull='')
    for x in (-0.5, 0.5):
        m.bx(x - 0.22, x + 0.22, -0.4, -0.08, 6.8, 7.12, 'dark', cull='')
        dq(m, x - 0.18, x + 0.18, -0.36, -0.12, 6.797, 'lampW')
    m.cy((0, 0, 7.12), 0.06, 0.06, 0.12, 'beacon', seg=6)
    hazard(m, -0.3, 0.3, -0.303, 0.0, 0.2, 3)
    make('Floodlight', m, ao, cols=[cb(-0.3, -0.3, 0.0, 0.3, 0.3, 0.2), cb(-0.12, -0.12, 0.2, 0.12, 0.12, 7.0)])
    m = new(pal)   # ground power unit / air start cart [2, 2]
    m.bx(-0.6, 0.6, -0.8, 0.8, 0.3, 1.25, 'yellow', cull='b')
    m.bx(-0.62, 0.62, -0.82, 0.82, 1.25, 1.32, 'yellowD', cull='')
    for k in range(6):
        y = -0.6 + k * 0.24
        m.bx(0.6, 0.603, y, y + 0.12, 0.6, 1.1, 'dark', hull='none', cull='tbfkl')
    fq(m, -0.4, 0.4, -0.803, 0.7, 1.1, 'dark')
    fq(m, -0.32, -0.05, -0.806, 0.85, 1.0, 'screen')
    for (x, y) in ((-0.5, -0.6), (0.5, -0.6), (-0.5, 0.6), (0.5, 0.6)):
        wheel(m, x, y, 0.2, 0.2, 0.12, c='tire', hub='steelD', seg=8)
    m.bm_((0, -0.8, 0.5), (0, -1.25, 0.3), 0.05, 'steelD')
    m.cy((-0.6, 0.2, 0.75), 0.24, 0.24, 0.1, 'black', seg=10, rot=(0, -90, 0))
    xdisc(m, -0.703, 0.2, 0.75, 0.1, 'yellow', seg=8, face=-1)
    text(m, 'GPU 2', 0, -0.803 - 0.003, 0.45, 0.14, 'black')
    make('GPU', m, ao, cols=[cb(-0.62, -0.82, 0.0, 0.62, 0.82, 1.32)])


# ================================================================ maintenance gear (hangars)
def build_maint(pal, ao):
    m = new(pal)   # engine stand [2, 5]: a turbofan on a wheeled cradle
    m.bx(-0.7, 0.7, -2.3, 2.3, 0.25, 0.35, 'yellow', cull='')
    for (x, y) in ((-0.6, -2.1), (0.6, -2.1), (-0.6, 2.1), (0.6, 2.1)):
        wheel(m, x, y, 0.18, 0.18, 0.1, c='tire', hub='steel', seg=8)
    for y in (-1.3, 1.3):
        m.bx(-0.55, 0.55, y - 0.08, y + 0.08, 0.35, 0.75, 'yellow', cull='b')
    cyl_y(m, 0, -2.1, 1.8, 1.25, 0.5, 'steel', seg=12)
    cyl_y(m, 0, 1.8, 2.3, 1.25, 0.44, 'steelD', seg=12, r1=0.36)
    vdisc(m, 0, -2.103, 1.25, 0.42, 'dark', seg=12, face=-1)
    m.cy((0, -2.103, 1.25), 0.14, 0.03, 0.25, 'steelD', seg=8, rot=(90, 0, 0))
    for y in (-0.6, 0.4):
        cyl_y(m, 0, y, y + 0.12, 1.25, 0.53, 'brass', seg=12)
    make('EngineStand', m, ao, cols=[cb(-0.55, -2.15, 0.0, 0.55, 2.3, 1.78)])
    m = new(pal)   # maintenance work stand [2, 3]: steps up to a railed platform at 1.8 m
    P = 1.8
    m.bx(-0.75, 0.75, 0.2, 1.4, P - 0.08, P, 'steel', cull='')
    for (x, y) in ((-0.7, 0.25), (0.7, 0.25), (-0.7, 1.35), (0.7, 1.35)):
        m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.12, P - 0.08, 'yellow', cull='b')
        wheel(m, x, y, 0.1, 0.1, 0.06, c='tire', hub='steel', seg=6)
    for k in range(6):
        z = (k + 1) * P / 7
        y = -1.4 + k * 0.27
        m.bx(-0.55, 0.55, y, y + 0.25, z - 0.04, z, 'steel', cull='')
    for s in (-1, 1):
        m.bm_((s * 0.58, -1.45, 0.1), (s * 0.58, 0.2, P), 0.06, 'yellow')
        m.bm_((s * 0.62, -1.45, 1.0), (s * 0.62, 0.2, P + 1.0), 0.045, 'yellow')
        m.bm_((s * 0.76, 0.2, P + 1.0), (s * 0.76, 1.4, P + 1.0), 0.045, 'yellow')
        m.bm_((s * 0.76, 1.37, P), (s * 0.76, 1.37, P + 0.98), 0.034, 'yellow')
    m.bm_((-0.74, 1.4, P + 1.0), (0.74, 1.4, P + 1.0), 0.04, 'yellow')
    make('WorkStand', m, ao, cols=[cb(-0.76, 0.2, 0.0, 0.76, 1.42, P), cb(-0.6, -1.45, 0.0, 0.6, 0.2, 0.9)])
    m = new(pal)   # A-frame gantry hoist [3, 2] with its chain block
    for s in (-1, 1):
        x = s * 1.3
        m.bm_((x, -0.8, 0.0), (x, 0.0, 3.4), 0.12, 'yellow')
        m.bm_((x, 0.8, 0.0), (x, 0.0, 3.4), 0.1, 'yellow')
        m.bx(x - 0.15, x + 0.15, -0.95, 0.95, 0.0, 0.12, 'yellowD', cull='b')
        for y in (-0.85, 0.85):
            wheel(m, x, y, 0.1, 0.1, 0.08, c='tire', hub='steel', seg=6)
    m.bx(-1.45, 1.45, -0.1, 0.1, 3.4, 3.62, 'yellow', cull='')
    m.bx(-0.15, 0.15, -0.14, 0.14, 2.95, 3.4, 'dark', cull='')
    m.cy((0.0, 0.0, 1.6), 0.015, 0.015, 1.35, 'black', seg=4, hull='none')
    m.bx(-0.06, 0.06, -0.04, 0.04, 1.4, 1.6, 'fire', cull='')
    make('Hoist', m, ao, cols=[cb(-1.45, -0.95, 0.0, -1.15, 0.95, 1.6), cb(1.15, -0.95, 0.0, 1.45, 0.95, 1.6)])
    m = new(pal)   # workbench [2, 1] (back to +Y): a steel top, a vise, a pegboard with tools
    m.bx(-0.95, 0.95, -0.35, 0.35, 0.85, 0.92, 'wood', cull='')
    for x in (-0.88, 0.88):
        m.bx(x - 0.04, x + 0.04, -0.3, 0.3, 0.0, 0.85, 'steelD', cull='b')
    m.bx(-0.84, 0.84, -0.26, 0.26, 0.2, 0.26, 'steelD', cull='')
    m.bx(-0.95, 0.95, 0.35, 0.42, 0.92, 1.9, 'cream', cull='b')
    for i, x in enumerate((-0.7, -0.45, -0.2, 0.1, 0.4, 0.7)):
        fq(m, x - 0.04, x + 0.04, 0.347, 1.2 + (i % 2) * 0.15, 1.6, 'fire' if i % 3 == 0 else 'dark')
    m.bx(0.55, 0.8, -0.3, -0.1, 0.92, 1.08, 'blue', cull='b')
    m.bx(-0.6, -0.3, -0.2, 0.1, 0.92, 1.0, 'dark', cull='b')
    make('Bench', m, ao, cols=[cb(-0.95, -0.35, 0.0, 0.95, 0.42, 0.92), cb(-0.95, 0.35, 0.92, 0.95, 0.42, 1.9)])
    m = new(pal)   # parts shelving [3, 1] (back to +Y): four shelves of bins and boxes
    for x in (-1.45, 1.45):
        m.bx(x - 0.04, x + 0.04, -0.3, 0.3, 0.0, 2.2, 'blueD', cull='b')
    for k in range(4):
        z = 0.15 + k * 0.6
        m.bx(-1.41, 1.41, -0.28, 0.28, z, z + 0.04, 'steel', cull='')
        for j in range(5):
            x = -1.2 + j * 0.6
            c = ('cont4', 'blue', 'cream', 'fire', 'olive')[(j + k) % 5]
            m.bx(x - 0.24, x + 0.24, -0.25, 0.25, z + 0.04, z + 0.3 + 0.05 * ((j * 3 + k) % 3), c, cull='b')
    make('Shelf', m, ao, cols=[cb(-1.49, -0.3, 0.0, 1.49, 0.3, 2.2)])


# ================================================================ cargo lift, containers, fuel
def build_cargo(pal, ao):
    m = new(pal)   # cargo lift [7, 7]: the flush platform with its hazard border, corner guide posts, chains, control post
    uq(m, -3.4, 3.4, -3.4, 3.4, 0.006, 'steel')
    for i in range(1, 7):
        uq(m, -3.1, 3.1, -3.4 + i * 0.97 - 0.02, -3.4 + i * 0.97 + 0.02, 0.009, 'steelD')
    hazard_up(m, -3.4, 3.4, -3.4, -3.1, 0.011, 16)
    hazard_up(m, -3.4, 3.4, 3.1, 3.4, 0.011, 16)
    hazard_up(m, -3.4, -3.1, -3.1, 3.1, 0.011, 14, along='y')
    hazard_up(m, 3.1, 3.4, -3.1, 3.1, 0.011, 14, along='y')
    for (x, y) in ((-3.3, -3.3), (3.3, -3.3), (-3.3, 3.3), (3.3, 3.3)):
        m.bx(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.0, 4.2, 'yellow', cull='b')
        m.bx(x - 0.24, x + 0.24, y - 0.24, y + 0.24, 4.2, 4.5, 'dark', cull='')
        m.cy((x, y, 4.5), 0.08, 0.08, 0.1, 'beacon', seg=6)
    for (a, b) in (((-3.3, 3.3), (3.3, 3.3)), ((3.3, -3.3), (3.3, 3.3))):
        n = 6
        for k in range(n):
            p0 = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            p1 = (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)
            m.bm_((p0[0], p0[1], 0.95), ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.85), 0.034, 'fire', hull='none')
            m.bm_(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.85), (p1[0], p1[1], 0.95), 0.024, 'fire', hull='none')
    m.bx(-3.75, -3.45, -2.6, -2.2, 0.0, 1.15, 'navyD', cull='b')
    m.bx(-3.78, -3.42, -2.65, -2.15, 1.15, 1.3, 'dark', cull='')
    for i, c in enumerate(('lgreen', 'beacon', 'yellow')):
        m.bx(-3.45, -3.447, -2.55 + i * 0.13, -2.45 + i * 0.13, 0.9, 1.0, c, hull='none', cull='tbfkl')
    cols = [cb(x - 0.18, y - 0.18, 0.0, x + 0.18, y + 0.18, 4.2) for (x, y) in ((-3.3, -3.3), (3.3, -3.3), (-3.3, 3.3), (3.3, 3.3))]
    cols.append(cb(-3.75, -2.6, 0.0, -3.45, -2.2, 1.3))
    make('CargoLift', m, ao, cols=cols)
    m = new(pal)   # ISO 20 ft container [3, 6] (along Y), corrugated sides, doors at +Y
    W, L, H = 2.44, 6.06, 2.59
    m.bx(-W / 2, W / 2, -L / 2, L / 2, 0.0, H, 'cont1', cull='b')
    for s in (-1, 1):
        x = s * (W / 2 + 0.003)
        for k in range(16):
            y = -L / 2 + 0.25 + k * (L - 0.5) / 15
            m.bx(*sorted((x, x + s * 0.002)), y - 0.06, y + 0.06, 0.12, H - 0.12, 'navyD', hull='none', cull='tbfk' + ('l' if s > 0 else 'r'))
    for x in (-0.6, 0.6):
        bq(m, x - 0.04, x + 0.04, L / 2 + 0.003, 0.1, H - 0.1, 'dark')
    bq(m, -0.03, 0.03, L / 2 + 0.006, 0.1, H - 0.1, 'dark')
    text(m, 'TRITON', 0.0, -L / 2 - 0.003, 1.3, 0.4, 'white')
    make('Container', m, ao, cols=[cb(-W / 2, -L / 2, 0.0, W / 2, L / 2, H)])
    m = new(pal)   # horizontal fuel tank [3, 8] on two saddles, a ladder, a walkway on top, the JP sign
    R, L = 1.25, 7.2
    cyl_y(m, 0, -L / 2, L / 2, R + 0.55, R, 'wallL', seg=14)
    for s in (-1, 1):
        m.cy((0, s * L / 2, R + 0.55), R, R * 0.4, 0.3, 'wallL', seg=14, rot=(-90 * s, 0, 0))
    text(m, 'AVIATION FUEL', R + 0.02, 0.0, 1.6, 0.36, 'fire', face='x+')
    for y in (-2.2, 2.2):
        m.bx(-1.1, 1.1, y - 0.3, y + 0.3, 0.0, 0.9, 'conc', cull='b')
    cyl_y(m, 0, -0.2, 0.2, R + 0.55, R + 0.02, 'fire', seg=14, caps=False)
    m.bx(-0.4, 0.4, -L / 2 + 0.6, L / 2 - 0.6, 2 * R + 0.55, 2 * R + 0.62, 'steelD', cull='')
    for k in range(6):
        z = 0.3 + k * 0.45
        m.bx(1.31, 1.39, L / 2 - 1.18, L / 2 - 0.82, z - 0.02, z + 0.02, 'yellow', cull='')
    for y in (L / 2 - 1.2, L / 2 - 0.8):
        m.bx(1.29, 1.41, y - 0.03, y + 0.03, 0.0, 2 * R + 0.6, 'yellow', cull='b')
    make('FuelTank', m, ao, cols=[cb(-1.1, -L / 2 - 0.3, 0.0, 1.1, L / 2 + 0.3, 2 * R + 0.55), cb(1.25, L / 2 - 1.25, 0.0, 1.42, L / 2 - 0.75, 2 * R + 0.6)])
    # bund kerb and fuel lines (links: modelled along Blender Y, the half from the origin toward -Y)
    m = new(pal); m.bx(-0.15, 0.15, -0.5, 0.5, 0.0, 0.45, 'conc', hull='noend', cull='b'); uq(m, -0.15, 0.15, -0.5, 0.5, 0.453, 'yellow'); make('BundFull', m, ao, cols=[cb(-0.15, -0.5, 0.0, 0.15, 0.5, 0.45)])
    m = new(pal); m.bx(-0.15, 0.15, -0.5, -0.15, 0.0, 0.45, 'conc', hull='noend', cull='b'); uq(m, -0.15, 0.15, -0.5, -0.15, 0.453, 'yellow'); make('BundHalf', m, ao, cols=[cb(-0.15, -0.5, 0.0, 0.15, 0.0, 0.45)])
    m = new(pal); m.bx(-0.17, 0.17, -0.17, 0.17, 0.0, 0.5, 'conc', cull='b'); make('BundPost', m, ao)

    def pipes(m, y0, y1):
        for x in (-0.13, 0.13):
            cyl_y(m, x, y0, y1, 0.22, 0.08, 'yellow' if x < 0 else 'steel', seg=6, caps=False)
        for y in ((y0 + y1) / 2,):
            m.bx(-0.28, 0.28, y - 0.06, y + 0.06, 0.0, 0.13, 'dark', cull='b')
    m = new(pal); pipes(m, -0.5, 0.5); make('PipeFull', m, ao, cols=[cb(-0.24, -0.5, 0.0, 0.24, 0.5, 0.3, True)])
    m = new(pal); pipes(m, -0.5, -0.2); make('PipeHalf', m, ao, cols=[cb(-0.24, -0.5, 0.0, 0.24, 0.0, 0.3, True)])
    m = new(pal)
    m.bx(-0.26, 0.26, -0.26, 0.26, 0.0, 0.36, 'steelD', cull='b')
    m.cy((0, 0, 0.36), 0.12, 0.12, 0.1, 'fire', seg=8)
    m.cy((0, 0, 0.46), 0.18, 0.18, 0.03, 'fire', seg=10)
    make('PipePost', m, ao, cols=[cb(-0.26, -0.26, 0.0, 0.26, 0.26, 0.36, True)])
    m = new(pal)   # fuel point [2, 2]: a refuelling cabinet with meter, hose reel and nozzle, the sign
    m.bx(-0.8, 0.8, -0.4, 0.5, 0.0, 1.5, 'wallL', cull='b')
    m.bx(-0.82, 0.82, -0.42, 0.52, 1.5, 1.6, 'fire', cull='')
    fq(m, -0.7, -0.1, -0.403, 0.8, 1.35, 'dark')
    fq(m, -0.62, -0.18, -0.406, 1.0, 1.25, 'screen')
    m.cy((0.4, -0.4, 0.75), 0.42, 0.42, 0.2, 'black', seg=12, rot=(90, 0, 0))
    m.cy((0.4, -0.6, 0.75), 0.15, 0.15, 0.03, 'steel', seg=8, rot=(90, 0, 0))
    m.bx(-0.75, -0.55, -0.48, -0.4, 0.4, 0.7, 'steelD', cull='')
    m.bx(-0.6, 0.6, 0.0, 0.1, 1.6, 2.2, 'white', cull='')
    text(m, 'FUEL 3', 0.0, -0.003, 1.72, 0.32, 'fire')
    make('FuelPoint', m, ao, cols=[cb(-0.82, -0.42, 0.0, 0.82, 0.52, 1.6)])


def build_rwynum(pal, ao):
    m = new(pal)   # the runway designator, painted on the deck (read from the south)
    text(m, '36', 0.0, 0.0, 0.016, 7.0, 'white', face='up', valign='m')
    make('RwyNum', m, ao)


def build_props(pal, ao):
    build_rwynum(pal, ao)
    build_jbd(pal, ao)
    build_wires(pal, ao)
    build_helipad(pal, ao)
    build_small(pal, ao)
    build_maint(pal, ao)
    build_cargo(pal, ao)
