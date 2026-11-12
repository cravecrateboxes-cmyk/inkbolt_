"""INKBOLT kit-airfield7 props: runway and taxiway edge lights, taxiway signs, the windsock, the floodlight mast, ground
equipment (chocks, tool chest, wheeled fire bottle, ground power unit), workshop gear (workbench, parts racks, lathe,
drill press, the engine on its transport dolly, tyre stacks), the picnic table, dry scrub. Conventions: af_base.py."""
import math

from af_base import *  # noqa: F401,F403
from af_base import new, make, text, hazard, plate, tyre_stack


def build_lights(pal, ao):
    for name, c in (('RwyLight', 'lamp'), ('TaxiLight', 'lampB'), ('EndLight', 'lampR')):
        m = new(pal)
        m.cy((0.0, 0.0, 0.0), 0.09, 0.07, 0.22, 'yellow', seg=6)
        m.cy((0.0, 0.0, 0.22), 0.08, 0.05, 0.1, c, seg=6)
        m.bx(-0.16, 0.16, -0.16, 0.16, 0.0, 0.03, 'concD', hull='none', cull='b')
        make(name, m, ao)


def build_signs(pal, ao):
    """[2, 1] taxiway signs on frangible legs: location (black / yellow), direction (yellow / black), mandatory
    runway-holding sign (red / white); both faces lettered"""
    for name, word, bg, fg in (('Sign_A', 'A  09-27', 'black', 'yellow'), ('Sign_B', 'B  A1', 'yellow', 'black'), ('Sign_Hold', '09-27', 'redD', 'white')):
        m = new(pal)
        m.bx(-0.95, 0.95, -0.18, 0.18, 0.35, 1.15, 'dark', cull='')
        fq(m, -0.9, 0.9, -0.183, 0.4, 1.1, bg)
        bq(m, -0.9, 0.9, 0.183, 0.4, 1.1, bg)
        text(m, word, 0.0, -0.186, 0.55, 0.42, fg, maxw=1.7)
        text(m, word, 0.0, 0.186, 0.55, 0.42, fg, face='y+', maxw=1.7)
        for x in (-0.7, 0.7):
            m.bx(x - 0.04, x + 0.04, -0.04, 0.04, 0.0, 0.35, 'steelD', cull='b')
            m.bx(x - 0.12, x + 0.12, -0.12, 0.12, 0.0, 0.05, 'concD', hull='none', cull='b')
        make(name, m, ao, cols=[cb(-0.95, -0.18, 0.35, 0.95, 0.18, 1.15)])


def build_windsock(pal, ao):
    """the windsock: a lattice-free steel mast with a ring frame and the orange / white sock blowing east (+X)"""
    m = new(pal)
    H = 5.4
    m.bx(-0.35, 0.35, -0.35, 0.35, 0.0, 0.15, 'concD', cull='b')
    m.cy((0.0, 0.0, 0.15), 0.07, 0.05, H - 0.15, 'white2', seg=6)
    for k in range(3):
        z = 1.2 + k * 1.4
        fq(m, -0.06, 0.06, -0.064, z, z + 0.5, 'redD')
    m.cy((0.0, 0.0, H), 0.06, 0.06, 0.1, 'steelD', seg=6)
    m.bm_((0.0, 0.0, H + 0.05), (0.35, 0.0, H + 0.05), 0.04, 'steelD')
    # the sock: five frustum bands along +X drooping slightly, alternating orange and white
    x, r, z = 0.35, 0.36, H + 0.05
    for k in range(5):
        L = 0.48
        r1 = r * 0.88
        z1 = z - 0.07
        m.cy((x, 0.0, z), r, r1, L, 'orange' if k % 2 == 0 else 'white2', seg=10, rot=(0, 90 + math.degrees(math.atan2(z - z1, L)), 0), caps=(k == 4))
        x += L
        r = r1
        z = z1
    m.cy((0.0, 0.0, H + 0.1), 0.1, 0.1, 0.12, 'lampR', seg=8)
    make('Windsock', m, ao, cols=[cb(-0.35, -0.35, 0.0, 0.35, 0.35, H)])


def build_mast(pal, ao):
    """a floodlight mast (8 m) with a twin head facing the piece's front (-Y)"""
    m = new(pal)
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.25, 'concD', cull='b')
    m.cy((0.0, 0.0, 0.25), 0.12, 0.08, 7.75, 'grey', seg=8)
    m.bx(-0.7, 0.7, -0.12, 0.12, 7.7, 7.85, 'steelD', cull='')
    for x in (-0.45, 0.45):
        m.bx(x - 0.23, x + 0.23, -0.42, -0.1, 7.45, 7.95, 'dark', cull='')
        fq(m, x - 0.21, x + 0.21, -0.423, 7.5, 7.9, 'lamp')
    m.bx(-0.2, 0.2, 0.12, 0.4, 1.0, 1.6, 'steelD', cull='')
    make('LightMast', m, ao, cols=[cb(-0.3, -0.3, 0.0, 0.3, 0.3, 0.25), cb(-0.13, -0.13, 0.25, 0.13, 0.4, 7.7)])


def build_ground(pal, ao):
    m = new(pal)
    for x in (-0.25, 0.25):
        wedge(m, x - 0.13, x + 0.13, -0.18, 0.18, 0.0, 0.2, 0.0, 0.2, 'yellow')
    m.bx(-0.13, 0.13, -0.02, 0.02, 0.08, 0.12, 'dark', hull='none', cull='')
    make('Chocks', m, ao, cols=[cb(-0.38, -0.18, 0.0, 0.38, 0.18, 0.2)])
    m = new(pal)
    m.bx(-0.45, 0.45, -0.3, 0.3, 0.12, 1.0, 'redD', cull='')
    for k in range(4):
        z = 0.25 + k * 0.2
        fq(m, -0.4, 0.4, -0.303, z, z + 0.12, 'fire')
        fq(m, -0.1, 0.1, -0.307, z + 0.04, z + 0.07, 'steel')
    m.bx(-0.47, 0.47, -0.32, 0.32, 1.0, 1.05, 'dark', cull='')
    for (x, y) in ((-0.38, -0.22), (0.38, -0.22), (-0.38, 0.22), (0.38, 0.22)):
        m.cy((x, y, 0.0), 0.06, 0.06, 0.12, 'black', seg=6)
    make('ToolChest', m, ao, cols=[cb(-0.47, -0.32, 0.0, 0.47, 0.32, 1.05)])
    # the wheeled fire bottle (a 50 kg extinguisher trolley)
    m = new(pal)
    m.cy((0.0, 0.0, 0.18), 0.22, 0.22, 0.85, 'fire', seg=10)
    m.sp((0.0, 0.0, 1.03), 0.22, 'fire', seg=(10, 5), scale=(1, 1, 0.5))
    m.cy((0.0, 0.0, 1.1), 0.05, 0.05, 0.15, 'black', seg=6)
    m.bm_((-0.25, 0.25, 0.3), (-0.25, 0.25, 1.15), 0.04, 'dark')
    m.bm_((0.25, 0.25, 0.3), (0.25, 0.25, 1.15), 0.04, 'dark')
    m.bm_((-0.3, 0.25, 1.16), (0.3, 0.25, 1.16), 0.055, 'dark')
    for x in (-0.28, 0.28):
        wheel(m, x, 0.1, 0.18, 0.18, 0.08, c='tire', hub='steel', seg=8)
    m.cy((0.0, -0.2, 0.5), 0.04, 0.04, 0.5, 'black', seg=5)
    make('FireBottle', m, ao, cols=[cb(-0.33, -0.26, 0.0, 0.33, 0.3, 1.2)])
    # ground power unit [2, 2]
    m = new(pal)
    m.bx(-0.65, 0.65, -0.85, 0.85, 0.35, 1.3, 'yellow', cull='')
    for k in range(5):
        y = -0.6 + k * 0.28
        rq(m, 0.653, y - 0.06, y + 0.06, 0.55, 1.15, 'yellowD')
    fq(m, -0.5, 0.5, -0.853, 0.6, 1.1, 'dark')
    text(m, '400 HZ', 0.0, -0.856, 0.75, 0.16, 'yellow', font='cond', maxw=0.9)
    hazard(m, -0.65, 0.65, -0.856, 0.36, 0.52, 6)
    m.bm_((0.0, -0.85, 0.5), (0.0, -1.0, 0.4), 0.06, 'dark')
    m.cy((-0.3, 0.86, 0.9), 0.22, 0.22, 0.12, 'black', seg=10, rot=(-90, 0, 0))
    for (x, y) in ((-0.55, -0.6), (0.55, -0.6), (-0.55, 0.6), (0.55, 0.6)):
        wheel(m, x, y, 0.22, 0.22, 0.12, c='tire', hub='steel', seg=8)
    make('GPU', m, ao, cols=[cb(-0.68, -1.0, 0.0, 0.68, 0.98, 1.3)])
    # tyre stacks
    m = new(pal)
    tyre_stack(m, -0.12, -0.1, 3)
    tyre_stack(m, 0.25, 0.22, 2, r=0.3, w=0.2)
    make('Tyres', m, ao, cols=[cb(-0.46, -0.45, 0.0, 0.47, 0.45, 0.72)])


def build_workshop(pal, ao):
    """[3, 1] workbench, [4, 1] parts racks A / B, [3, 1] lathe, the drill press, [2, 4] the engine on its dolly"""
    m = new(pal)
    m.bx(-1.45, 1.45, -0.42, 0.38, 0.86, 0.94, 'wood', cull='')
    for x in (-1.35, 1.35):
        for y in (-0.33, 0.3):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.86, 'steelD', hull='none', cull='b')
    m.bx(-1.3, -0.6, -0.35, 0.33, 0.1, 0.8, 'redD', cull='')
    for k in range(3):
        fq(m, -1.26, -0.64, -0.353, 0.2 + k * 0.2, 0.32 + k * 0.2, 'fire')
    m.bx(-1.45, 1.45, 0.38, 0.45, 0.94, 1.95, 'woodD', cull='')
    for k in range(7):
        x = -1.25 + k * 0.4
        fq(m, x, x + 0.05, 0.377, 1.15, 1.75, 'black' if k % 2 else 'steelD')
    m.bx(0.6, 0.9, -0.3, 0.0, 0.94, 1.12, 'blueD', cull='b')
    m.bx(0.68, 0.82, -0.36, 0.06, 1.12, 1.2, 'steelD', cull='')
    m.bx(-0.2, 0.3, -0.25, 0.1, 0.94, 1.05, 'khaki', cull='b')
    m.cy((1.25, 0.25, 0.94), 0.03, 0.03, 0.55, 'black', seg=5)
    m.cy((1.25, 0.08, 1.49), 0.09, 0.12, 0.12, 'yellow', seg=8)
    make('Workbench', m, ao, cols=[cb(-1.45, -0.42, 0.0, 1.45, 0.45, 0.94), cb(-1.45, 0.38, 0.94, 1.45, 0.45, 1.95)])
    for name, load in (('RackA', 'wheels'), ('RackB', 'boxes')):
        m = new(pal)
        for x in (-1.95, 1.95):
            for y in (-0.4, 0.4):
                m.bx(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 2.6, 'blue', cull='b')
        for z in (0.12, 0.95, 1.8):
            m.bx(-1.95, 1.95, -0.42, 0.42, z, z + 0.06, 'orange', cull='')
            if load == 'wheels':
                for k in range(4):
                    x = -1.5 + k * 1.0
                    m.cy((x, 0.0, z + 0.06), 0.36, 0.36, 0.22, 'tire', seg=10)
                    m.cy((x, 0.0, z + 0.284), 0.2, 0.2, 0.004, 'steel', seg=8, hull='none')
            else:
                for k in range(5):
                    x = -1.6 + k * 0.8
                    c = ('khaki', 'od', 'camoA', 'khakiD', 'od')[(k + int(z * 3)) % 5]
                    h = 0.42 + 0.12 * ((k + int(z * 7)) % 3)
                    m.bx(x - 0.33, x + 0.33, -0.36, 0.36, z + 0.06, z + 0.06 + h, c, cull='b')
                    fq(m, x - 0.18, x + 0.18, -0.363, z + 0.18, z + 0.3, 'white2')
        make(name, m, ao, cols=[cb(-2.0, -0.45, 0.0, 2.0, 0.45, 2.6)])
    # the lathe
    m = new(pal)
    m.bx(-1.3, 1.3, -0.3, 0.3, 0.0, 0.8, 'green', cull='b')
    m.bx(-1.4, 1.4, -0.35, 0.35, 0.8, 0.9, 'steelD', cull='')
    m.bx(-1.3, -0.7, -0.3, 0.3, 0.9, 1.45, 'green', cull='')
    m.bx(0.9, 1.25, -0.2, 0.2, 0.9, 1.25, 'green', cull='')
    cyl_x(m, -0.62, 0.9, 0.0, 1.17, 0.05, 'steel', seg=6)
    cyl_x(m, -0.7, -0.55, 0.0, 1.17, 0.15, 'steelD', seg=8)
    m.bx(-0.2, 0.15, -0.28, 0.2, 0.9, 1.08, 'steelD', cull='b')
    fq(m, -1.25, -0.75, -0.303, 1.0, 1.35, 'steelD')
    make('Lathe', m, ao, cols=[cb(-1.4, -0.35, 0.0, 1.4, 0.35, 1.45)])
    # the drill press
    m = new(pal)
    m.bx(-0.3, 0.3, -0.25, 0.3, 0.0, 0.08, 'green', cull='b')
    m.cy((0.0, 0.18, 0.08), 0.05, 0.05, 1.6, 'steel', seg=6)
    m.bx(-0.15, 0.15, -0.2, 0.25, 1.4, 1.8, 'green', cull='')
    m.cy((0.0, -0.08, 1.15), 0.02, 0.02, 0.25, 'steelD', seg=5)
    m.bx(-0.2, 0.2, -0.25, 0.15, 0.75, 0.8, 'steelD', cull='')
    make('DrillPress', m, ao, cols=[cb(-0.3, -0.25, 0.0, 0.3, 0.3, 1.8)])
    # a jet engine on its transport dolly (rails along Y)
    m = new(pal)
    for x in (-0.6, 0.6):
        m.bx(x - 0.06, x + 0.06, -1.9, 1.9, 0.25, 0.37, 'yellowD', cull='')
    for y in (-1.6, 1.6):
        m.bx(-0.7, 0.7, y - 0.06, y + 0.06, 0.27, 0.35, 'yellowD', cull='')
        for s in (-1, 1):
            m.bm_((s * 0.6, y, 0.37), (s * 0.3, y, 0.9), 0.07, 'yellowD')
    for (x, y) in ((-0.65, -1.7), (0.65, -1.7), (-0.65, 1.7), (0.65, 1.7)):
        m.cy((x, y, 0.0), 0.12, 0.12, 0.25, 'black', seg=8)
    cyl_y(m, 0.0, -1.5, 1.3, 1.25, 0.5, 'steel', seg=10)
    cyl_y(m, 0.0, -1.85, -1.5, 1.25, 0.6, 'steelD', seg=10, r1=0.55)
    vdisc(m, 0.0, -1.854, 1.25, 0.45, 'dark', seg=10)
    cyl_y(m, 0.0, 1.3, 1.85, 1.25, 0.48, 'rust', seg=10, r1=0.38)
    m.bx(0.4, 0.62, -1.0, 0.4, 1.0, 1.45, 'od', cull='')
    text(m, 'SERVICEABLE', -0.505, 0.0, 1.05, 0.12, 'green', face='x-', font='cond')
    make('EngineDolly', m, ao, cols=[cb(-0.75, -1.9, 0.0, 0.75, 1.9, 1.8)])


def build_misc(pal, ao):
    # the picnic table [2, 2] outside the barracks
    m = new(pal)
    m.bx(-0.9, 0.9, -0.38, 0.38, 0.72, 0.78, 'wood', cull='')
    for y in (-0.72, 0.72):
        m.bx(-0.9, 0.9, y - 0.14, y + 0.14, 0.42, 0.47, 'wood', cull='')
    for x in (-0.7, 0.7):
        m.bm_((x, -0.85, 0.0), (x, 0.0, 0.72), 0.06, 'woodD')
        m.bm_((x, 0.85, 0.0), (x, 0.0, 0.72), 0.05, 'woodD')
    make('Picnic', m, ao, cols=[cb(-0.9, -0.86, 0.0, 0.9, 0.86, 0.78)])
    # dry scrub clumps (low, collision-free) and a sand drift
    for name, n, c in (('Scrub_A', 5, 'scrub'), ('Scrub_B', 4, 'dry')):
        m = new(pal)
        for k in range(n):
            a = k * 2.4
            r = 0.12 + 0.18 * ((k * 7) % 5) / 4.0
            x, y = math.cos(a) * r * 1.4, math.sin(a) * r * 1.4
            h = 0.3 + 0.15 * ((k * 3) % 4)
            m.cy((x, y, 0.0), 0.22 + 0.06 * (k % 3), 0.04, h, c if k % 2 else ('scrubD' if c == 'scrub' else 'sandD'), seg=6)
        make(name, m, ao)


def build_marks(pal, ao):
    """the runway designation numbers (painted, 9 m tall; reading along +X, the tops toward +Y)"""
    for word in ('09', '27'):
        m = new(pal)
        text(m, word, 0.0, 0.0, 0.008, 9.0, 'white2', face='up', valign='m', maxw=9.0)
        make('Rwy' + word, m, False)


def build_props(pal, ao):
    build_lights(pal, ao)
    build_signs(pal, ao)
    build_windsock(pal, ao)
    build_mast(pal, ao)
    build_ground(pal, ao)
    build_workshop(pal, ao)
    build_misc(pal, ao)
    build_marks(pal, ao)
