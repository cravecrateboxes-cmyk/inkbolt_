"""INKBOLT kit-pelagic structures: deck-edge railings with their safety nets, blast fences, the runway barricade, the
flight-operations block front, corners, the gate, trail, hatch, deck posts and rails, stairs, the island control
tower (landmark of the flight deck), the second tower (landmark of the hangar deck) and the two hangar shells.
Conventions: pel_base.py."""
import math

from pel_base import *  # noqa: F401,F403
from pel_base import new, make, text, steps, stair_visual, stair_side_cols, hazard, hazard_up, window_band, window_band_x, rot_cols
from kit_base import shutter_hull
import pel_detail as PD


# ================================================================ deck-edge railing (zone walls over the sea)
def edge_base(m, post=False, arm=False, net=True):
    # the coaming kerb on the inside face, the deck lip and the edge fascia outboard
    m.bx(-0.5, 0.5, -0.47, -0.36, 0.0, 0.14, 'yellow', hull='noside', cull='b')
    m.bx(-0.5, 0.5, 0.5, 0.74, -1.6, 0.05, 'navyD', hull='noside', cull='')
    uq(m, -0.5, 0.5, 0.52, 0.72, 0.053, 'deck2')
    # rails: a top rail and a mid rail (yellow / steel), the rope net between them and the kerb
    cyl_x(m, -0.5, 0.5, -0.415, 1.15, 0.035, 'yellow', seg=6, caps=False)
    cyl_x(m, -0.5, 0.5, -0.415, 0.64, 0.025, 'steel', seg=5, caps=False)
    if net:
        for x in (-0.375, -0.125, 0.125, 0.375):
            fq(m, x - 0.014, x + 0.014, -0.44, 0.14, 1.11, 'net')
        for z in (0.39, 0.88):
            fq(m, -0.5, 0.5, -0.444, z - 0.013, z + 0.013, 'net')
    if post:
        m.cy((0, -0.415, 0.14), 0.045, 0.045, 1.08, 'yellow', seg=6)
        m.cy((0, -0.415, 0.0), 0.07, 0.07, 0.17, 'steelD', seg=6, hull='none')
    # the outboard safety net: a frame sloping out and down from the deck lip, the net over it
    if net:
        cyl_x(m, -0.5, 0.5, 0.78, -0.42, 0.035, 'steelD', seg=5, caps=False)
        cyl_x(m, -0.5, 0.5, 2.15, -1.0, 0.035, 'steelD', seg=5, caps=False)
        n = (0.0, 0.4, 0.92)
        poly(m, [(-0.5, 0.8, -0.44), (0.5, 0.8, -0.44), (0.5, 2.13, -1.02), (-0.5, 2.13, -1.02)], 'netD', n)
        for t in (0.33, 0.66):
            y = 0.8 + 1.33 * t
            z = -0.44 - 0.58 * t
            poly(m, [(-0.5, y - 0.02, z + 0.012), (0.5, y - 0.02, z + 0.012), (0.5, y + 0.02, z - 0.005), (-0.5, y + 0.02, z - 0.005)], 'net', n)
        for x in (-0.25, 0.25):
            poly(m, [(x - 0.015, 0.8, -0.433), (x + 0.015, 0.8, -0.433), (x + 0.015, 2.13, -1.013), (x - 0.015, 2.13, -1.013)], 'net', n)
    if arm:
        m.bm_((0, 0.74, -1.3), (0, 2.15, -1.04), 0.06, 'steelD')


EDGE_COL = [cb(-0.5, -0.5, 0.0, 0.5, 0.5, EDGE_H)]


def build_edges(pal, ao):
    m = new(pal); edge_base(m, post=True, arm=True); make('Edge_A', m, ao)
    m = new(pal); edge_base(m); make('Edge_B', m, ao)
    # a lifebuoy on its holder
    m = new(pal); edge_base(m)
    m.bx(-0.06, 0.06, -0.47, -0.43, 0.3, 1.12, 'steelD', cull='b')
    m.cy((0, -0.47, 0.78), 0.3, 0.3, 0.08, 'orange', seg=12, rot=(90, 0, 0))
    vdisc(m, 0, -0.553, 0.78, 0.16, 'navyD', seg=10)
    for a in (0, 90, 180, 270):
        r = math.radians(a + 45)
        x, z = math.cos(r) * 0.23, 0.78 + math.sin(r) * 0.23
        poly(m, [(x - 0.05, -0.553, z - 0.05), (x + 0.05, -0.553, z - 0.05), (x + 0.05, -0.553, z + 0.05), (x - 0.05, -0.553, z + 0.05)], 'white', (0, -1, 0))
    make('Edge_Ring', m, ao)
    # a fire-hose cabinet on the rail
    m = new(pal); edge_base(m, post=True)
    m.bx(-0.3, 0.3, -0.5, -0.36, 0.18, 1.0, 'fire', cull='')
    fq(m, -0.24, 0.24, -0.503, 0.3, 0.86, 'redD')
    text(m, 'FIRE', 0, -0.506, 0.66, 0.11, 'white')
    text(m, 'HOSE', 0, -0.506, 0.48, 0.09, 'white')
    make('Edge_Hose', m, ao)
    # a deck-edge floodlight on a short post
    m = new(pal); edge_base(m)
    m.cy((0.3, -0.38, 0.0), 0.05, 0.05, 1.55, 'steelD', seg=6)
    m.bx(0.12, 0.48, -0.5, -0.3, 1.5, 1.72, 'dark', cull='')
    fq(m, 0.15, 0.45, -0.503, 1.53, 1.69, 'lampW')
    make('Edge_Light', m, ao)


def corner_post(m, sx, sy, tall=3.9):
    """the steel post where two walls meet: at the inside corner (sx, sy = signs toward the zone)"""
    x, y = sx * 0.415, sy * 0.415
    m.bx(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.0, tall, 'navyD', cull='b')
    m.bx(x - 0.17, x + 0.17, y - 0.17, y + 0.17, tall, tall + 0.08, 'yellow', cull='')
    hazard(m, x - 0.15, x + 0.15, y - 0.153, 0.0, 0.9, 3) if sy < 0 else hazard(m, x - 0.15, x + 0.15, y + 0.153, 0.0, 0.9, 3, face=1)


def build_corners(pal, ao):
    # (name, inside x sign, inside y sign, fascia sides)
    for name, sx, sy, fas in (('Corner_NW_W', 1, -1, 'W'), ('Corner_SW_W', 1, 1, 'W'), ('Corner_NE_E', -1, -1, 'E'), ('Corner_SE_E', -1, 1, 'E'),
                              ('Corner_NE', -1, -1, ''), ('Corner_SE', -1, 1, '')):
        m = new(pal)
        corner_post(m, sx, sy)
        if 'W' in fas:
            m.bx(-0.74, -0.5, -0.5, 0.5, -1.6, 0.05, 'navyD', hull='noend', cull='')
        if 'E' in fas:
            m.bx(0.5, 0.74, -0.5, 0.5, -1.6, 0.05, 'navyD', hull='noend', cull='')
        make(name, m, ao)


# ================================================================ blast fences (zone walls on the deck)
def fence_base(m, post=False, h=FENCE_H, brace=False):
    m.bx(-0.5, 0.5, -0.42, -0.3, 0.0, h, 'steel', hull='noside', cull='b')
    # louvre shadows, a yellow top edge, a hazard band at the foot
    for i in range(1, 12):
        z = 0.5 + i * (h - 0.7) / 12
        fq(m, -0.5, 0.5, -0.423, z, z + 0.05, 'steelD')
    fq(m, -0.5, 0.5, -0.423, h - 0.12, h, 'yellow')
    hazard(m, -0.5, 0.5, -0.423, 0.0, 0.45, 4)
    if post:   # an I-beam post on the face and a brace behind it
        m.bx(-0.11, 0.11, -0.52, -0.42, 0.0, h + 0.1, 'navyD', cull='b')
        m.bx(-0.11, 0.11, -0.3, -0.22, 0.0, h + 0.1, 'navyD', cull='b')
    if brace:
        m.bm_((0, -0.25, h - 0.6), (0, 1.5, 0.05), 0.1, 'navyD')
        m.bx(-0.15, 0.15, 1.35, 1.75, 0.0, 0.06, 'steelD', cull='b')


FENCE_COL = [cb(-0.5, -0.45, 0.0, 0.5, -0.25, FENCE_H)]


def build_fences(pal, ao):
    m = new(pal); fence_base(m, post=True, brace=True); make('Fence_A', m, ao, cols=FENCE_COL)
    m = new(pal); fence_base(m); make('Fence_B', m, ao, cols=FENCE_COL)
    m = new(pal); fence_base(m)
    m.bx(-0.44, 0.44, -0.47, -0.42, 1.45, 2.45, 'white', cull='')
    fq(m, -0.4, 0.4, -0.473, 2.12, 2.4, 'fire')
    text(m, 'DANGER', 0, -0.476, 2.18, 0.17, 'white')
    text(m, 'JET BLAST', 0, -0.476, 1.82, 0.17, 'black')
    text(m, 'KEEP CLEAR', 0, -0.476, 1.56, 0.13, 'fire')
    make('Fence_Sign', m, ao, cols=FENCE_COL)
    m = new(pal); fence_base(m)
    m.bx(-0.04, 0.04, -0.6, -0.42, FENCE_H - 0.3, FENCE_H - 0.22, 'steelD', cull='')
    m.bx(-0.2, 0.2, -0.78, -0.56, FENCE_H - 0.38, FENCE_H - 0.12, 'dark', cull='')
    fq(m, -0.17, 0.17, -0.783, FENCE_H - 0.35, FENCE_H - 0.15, 'lampW')
    make('Fence_Light', m, ao, cols=FENCE_COL)
    # the zone number board: big white figures on the fence (A = flight deck, B = hangar deck)
    for k, word in (('Fence_DeckA', 'DECK A'), ('Fence_DeckB', 'DECK B')):
        for i in range(3):
            m = new(pal); fence_base(m, post=(i == 1))
            m.bx(-0.5, 0.5, -0.45, -0.423, 1.2, 2.6, 'blueD', hull='noside', cull='bt')
            text(m, word, (1 - i) * 1.0, -0.455, 1.45, 0.9, 'white', clip=(-0.5 - (1 - i), 0.5 - (1 - i)))
            make('%s_%d' % (k, i), m, ao, cols=FENCE_COL)


# ================================================================ the runway barricade (zone 1 north wall over the runway)
def build_barricade(pal, ao):
    def net(m):
        for i in range(4):
            x = -0.375 + i * 0.25
            fq(m, x - 0.04, x + 0.04, -0.42, 0.1, 4.3, 'orange' if i % 2 else 'cream')
        for z in (1.45, 2.9):
            fq(m, -0.5, 0.5, -0.425, z - 0.04, z + 0.04, 'cream')
        cyl_x(m, -0.5, 0.5, -0.4, 4.36, 0.03, 'black', seg=5, caps=False)
        cyl_x(m, -0.5, 0.5, -0.4, 0.07, 0.03, 'black', seg=5, caps=False)
        uq(m, -0.5, 0.5, -0.47, -0.33, 0.012, 'yellow')
    col = [cb(-0.5, -0.46, 0.0, 0.5, -0.34, 4.4)]
    m = new(pal); net(m); make('Barricade_Net', m, ao, cols=col)
    m = new(pal)
    net(m)
    m.bx(-0.22, 0.22, -0.3, 0.25, 0.0, 4.75, 'yellow', cull='b')
    hazard(m, -0.22, 0.22, -0.303, 0.0, 4.6, 9)
    m.bx(-0.3, 0.3, 0.25, 0.95, 0.0, 0.8, 'navyD', cull='b')
    m.cy((0, 0.5, 0.8), 0.18, 0.18, 0.25, 'steelD', seg=8, rot=(0, 90, 0))
    m.bx(-0.26, 0.26, -0.34, 0.3, 4.75, 4.85, 'black', cull='')
    make('Barricade_Post', m, ao, cols=[cb(-0.5, -0.46, 0.0, 0.5, -0.34, 4.4), cb(-0.22, -0.34, 0.0, 0.22, 0.25, 4.75)])


# ================================================================ the flight-operations block front (zone 1 south wall)
def ops_base(m, upper=True):
    m.bx(-0.5, 0.5, -0.45, 0.5, 0.0, OPS_H - 0.3, 'wall', hull='noside', cull='k')
    fq(m, -0.5, 0.5, -0.453, 0.0, 0.3, 'wallD')
    fq(m, -0.5, 0.5, -0.453, 3.55, 3.8, 'wallD')
    fq(m, -0.5, -0.47, -0.453, 0.3, 3.55, 'wallD')
    fq(m, -0.5, -0.47, -0.453, 3.8, OPS_H - 0.3, 'wallD')
    m.bx(-0.5, 0.5, -0.55, 0.5, OPS_H - 0.3, OPS_H, 'wallL', hull='noside', cull='bk')
    if upper:
        window_band(m, -0.4, 0.4, -0.456, 4.4, 6.3, every=0.8)


OPS_COL = [cb(-0.5, -0.45, 0.0, 0.5, 0.5, OPS_H)]


def build_ops(pal, ao):
    m = new(pal); ops_base(m); window_band(m, -0.4, 0.4, -0.456, 0.9, 2.5, every=0.8); make('Ops_Win', m, ao, cols=OPS_COL)
    m = new(pal); ops_base(m, upper=False)
    fq(m, -0.12, 0.12, -0.456, 5.0, 5.9, 'wallD')
    make('Ops_Plain', m, ao, cols=OPS_COL)
    m = new(pal); ops_base(m)
    m.bx(-0.38, 0.38, -0.5, -0.45, 0.0, 2.25, 'navyD', cull='b')
    fq(m, -0.32, 0.32, -0.503, 0.0, 2.15, 'steelD')
    fq(m, -0.24, 0.24, -0.506, 1.35, 1.95, 'glassD')
    m.bx(0.18, 0.26, -0.53, -0.503, 1.0, 1.06, 'steel', hull='none', cull='k')
    m.bx(-0.5, 0.5, -0.9, -0.45, 2.45, 2.55, 'steelD', cull='k')
    make('Ops_Door', m, ao, cols=OPS_COL)
    m = new(pal); ops_base(m)
    fq(m, -0.4, 0.4, -0.456, 0.5, 2.2, 'steelD')
    for i in range(9):
        z = 0.6 + i * 0.18
        fq(m, -0.38, 0.38, -0.46, z, z + 0.07, 'dark')
    make('Ops_Vent', m, ao, cols=OPS_COL)
    # the sign band "PELAGIC AIRBASE  FLIGHT OPERATIONS" over 14 modules (module k reads from local -X to +X)
    word, n = 'PELAGIC AIRBASE  -  FLIGHT OPERATIONS', 14
    for k in range(n):
        m = new(pal); ops_base(m, upper=False)
        window_band(m, -0.4, 0.4, -0.456, 0.9, 2.5, every=0.8)
        m.bx(-0.5, 0.5, -0.5, -0.45, 4.25, 5.55, 'blueD', hull='noside', cull='bk')
        xc = (n / 2 - 0.5 - k)
        text(m, word, xc, -0.505, 4.55, 0.72, 'white', maxw=n - 0.8, clip=(-0.5 - xc, 0.5 - xc))
        window_band(m, -0.4, 0.4, -0.456, 5.85, 6.9, every=0.8, glints=False)
        make('Ops_Sign_%d' % k, m, ao, cols=OPS_COL)
    # the east end: a pilaster on local -X (yaw pi: world east), where the fence starts
    m = new(pal); ops_base(m)
    window_band(m, -0.1, 0.4, -0.456, 0.9, 2.5, every=0.5)
    m.bx(-0.53, -0.18, -0.62, 0.5, 0.0, OPS_H + 0.1, 'wallL', cull='bk')
    make('Ops_End', m, ao, cols=OPS_COL)
    # the south-west corner: the block's corner on the deck edge
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.45, 0.0, OPS_H - 0.3, 'wall', cull='b')
    m.bx(-0.55, 0.5, -0.55, 0.55, OPS_H - 0.3, OPS_H, 'wallL', cull='')
    m.bx(-0.74, -0.5, -0.5, 0.5, -1.6, 0.05, 'navyD', hull='noend', cull='')
    make('Ops_Corner', m, ao, cols=[cb(-0.5, -0.5, 0.0, 0.5, 0.45, OPS_H)])


# ================================================================ gate, trail, hatch
def build_gate(pal, ao):
    m = new(pal)
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.55, s * 2.45))
        m.bx(x0, x1, -0.5, 0.5, 0.0, 4.4, 'navy', cull='b')
        hazard(m, x0, x1, -0.503, 0.0, 1.0, 4)
        hazard(m, x0, x1, 0.503, 0.0, 1.0, 4, face=1)
        m.bx(x0 - 0.05, x1 + 0.05, -0.55, 0.55, 4.4, 4.55, 'steelD', cull='')
        m.cy((s * 2.0, 0, 4.55), 0.14, 0.14, 0.22, 'beacon', seg=8)
    m.bx(-1.55, 1.55, -0.42, 0.42, 3.3, 4.05, 'dark', cull='')
    fq(m, -1.5, 1.5, -0.423, 3.33, 3.38, 'yellow')
    bq(m, -1.5, 1.5, 0.423, 3.33, 3.38, 'yellow')
    text(m, 'PELAGIC AIRBASE', 0, -0.426, 3.5, 0.34, 'white', maxw=2.9)
    text(m, 'PELAGIC AIRBASE', 0, 0.426, 3.5, 0.34, 'white', face='y+', maxw=2.9)
    make('GateFrame', m, ao, cols=[cb(-2.5, -0.5, 0.0, -1.55, 0.5, 4.4), cb(1.55, -0.5, 0.0, 2.5, 0.5, 4.4)])
    m = new(pal)
    Hs = 3.05
    m.bx(-1.5, 1.5, -0.06, 0.06, 0.0, Hs, 'steel', hull='none', cull='')
    for i in range(1, 16):
        z = i * Hs / 16
        fq(m, -1.48, 1.48, -0.063, z - 0.02, z + 0.02, 'steelD')
        bq(m, -1.48, 1.48, 0.063, z - 0.02, z + 0.02, 'steelD')
    fq(m, -1.48, 1.48, -0.063, 0.0, 0.16, 'yellow')
    bq(m, -1.48, 1.48, 0.063, 0.0, 0.16, 'yellow')
    obj = make('GateShutter', m, False)
    shutter_hull(pal, obj)
    TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_trail(pal, ao):
    """1 m trail screen along Blender Y, its trail face +X, 2.6 m: a louvred blast screen; variants with a lamp,
    a fire extinguisher, a post"""
    for name, extra in (('TrailWall', None), ('TrailWall_B', 'lamp'), ('TrailWall_C', 'ext'), ('TrailWall_D', 'post')):
        m = new(pal)
        m.bx(-0.1, 0.06, -0.5, 0.5, 0.0, TRAIL_H, 'steel', hull='noend', cull='b')
        for i in range(1, 9):
            z = 0.45 + i * (TRAIL_H - 0.6) / 9
            m.bx(0.062, 0.064, -0.5, 0.5, z, z + 0.05, 'steelD', hull='none', cull='tbfkl')
        m.bx(0.062, 0.064, -0.5, 0.5, TRAIL_H - 0.1, TRAIL_H, 'yellow', hull='none', cull='tbfkl')
        m.bx(0.062, 0.064, -0.5, 0.5, 0.0, 0.3, 'black', hull='none', cull='tbfkl')
        if extra == 'lamp':
            m.bx(0.06, 0.26, -0.15, 0.15, 2.0, 2.2, 'dark', cull='')
            m.bx(0.12, 0.24, -0.12, 0.12, 1.995 - 0.003, 1.997, 'lampW', hull='none', cull='tfklr')
        elif extra == 'ext':
            m.bx(0.062, 0.1, -0.2, 0.2, 0.9, 1.5, 'fire', cull='')
            m.cy((0.2, 0.0, 0.3), 0.09, 0.09, 0.55, 'fire', seg=8)
            m.cy((0.2, 0.0, 0.85), 0.03, 0.03, 0.1, 'black', seg=6)
        elif extra == 'post':
            m.bx(0.062, 0.16, -0.12, 0.12, 0.0, TRAIL_H, 'navyD', cull='b')
        make(name, m, ao)
    # the exit hatch: a deck scuttle in a hazard border
    m = new(pal)
    m.bx(-1.3, 1.3, -1.3, 1.3, 0.0, 0.06, 'deck2', cull='b')
    hazard_up(m, -1.25, 1.25, -1.25, -1.0, 0.063, 10)
    hazard_up(m, -1.25, 1.25, 1.0, 1.25, 0.063, 10)
    hazard_up(m, -1.25, -1.0, -1.0, 1.0, 0.063, 8, along='y')
    hazard_up(m, 1.0, 1.25, -1.0, 1.0, 0.063, 8, along='y')
    m.bx(-0.85, 0.85, -0.85, 0.85, 0.06, 0.18, 'navyD', cull='b')
    for y in (-0.5, 0.5):
        m.bx(-0.8, 0.8, y - 0.04, y + 0.04, 0.18, 0.2, 'steelD', hull='none', cull='b')
    m.cy((0, 0, 0.18), 0.28, 0.28, 0.04, 'yellow', seg=12)
    m.cy((0, 0, 0.22), 0.05, 0.05, 0.1, 'steelD', seg=6)
    make('Hatch', m, ao)


# ================================================================ deck posts, rails, stairs
def build_decks(pal, ao):
    for name, top in (('DeckPost', HELI - 0.3), ('DeckPost3', MEZZ - 0.3)):
        m = new(pal)
        m.bx(-0.15, 0.15, -0.15, 0.15, 0.0, top, 'navyD', cull='b')
        m.bx(-0.22, 0.22, -0.22, 0.22, 0.0, 0.05, 'steelD', hull='none', cull='b')
        hazard(m, -0.15, 0.15, -0.153, 0.05, 1.2, 3)
        hazard(m, -0.15, 0.15, 0.153, 0.05, 1.2, 3, face=1)
        make(name, m, ao, cols=[cb(-0.15, -0.15, 0.0, 0.15, 0.15, top)])

    def rail(m, y0, y1):
        cyl_y(m, 0, y0, y1, 1.05, 0.035, 'yellow', seg=6, caps=False)
        cyl_y(m, 0, y0, y1, 0.55, 0.025, 'yellow', seg=5, caps=False)
        m.bx(-0.015, 0.015, y0, y1, 0.0, 0.12, 'yellowD', hull='none', cull='b')
    m = new(pal); rail(m, -0.5, 0.5); make('RailFull', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.5, 1.1)])
    m = new(pal); rail(m, -0.5, -0.04); make('RailHalf', m, ao, cols=[cb(-0.06, -0.5, 0.0, 0.06, 0.0, 1.1)])
    m = new(pal)
    m.cy((0, 0, 0), 0.045, 0.045, 1.1, 'yellow', seg=6)
    m.cy((0, 0, 1.1), 0.06, 0.03, 0.05, 'yellowD', seg=6, hull='none')
    make('RailPost', m, ao)
    # steel stairs [2, 6] to the 2.4 m deck and [2, 8] to the 3.0 m mezzanine, rising toward +Y
    for name, n, L in (('Stair24', 12, 6.0), ('Stair30', 15, 8.0)):
        m = new(pal)
        y0 = -L / 2
        top = stair_visual(m, -0.85, 0.85, y0, n)
        cols = []
        steps(cols, -0.84, 0.84, y0, n)
        if n * 0.5 < L:   # a landing at the top
            m.bx(-0.85, 0.85, y0 + n * 0.5, L / 2, top - 0.1, top, 'steel', cull='')
            cols.append(cb(-0.84, y0 + n * 0.5, 0.0, 0.84, L / 2, top, True))
        stair_side_cols(cols, -0.87, y0, n)
        stair_side_cols(cols, 0.87, y0, n)
        make(name, m, ao, cols=cols)


def stair_cols_rot(cols, local, deg, dx, dy):
    for (c, h, w) in rot_cols(local, deg):
        cols.append(((c[0] + dx, c[1] + dy, c[2]), h, w))


# ================================================================ the island control tower (zone 1 landmark) [10, 20]
def build_island(pal, ao):
    """Footprint x -5..5 (east = the runway side), y -10..10. A steel base block 3.6 m high whose roof is the gallery
    (south strip and east strip, 2.8 m wide, yellow rails), the stair up the west face rising south to a landing on
    the south-west corner; the tower body set back on the base (offices, window bands, phased-array panels, the big
    hull number 01 toward the runway); the flight-control cab and the mast with radars on top (IslandTop)."""
    m = new(pal)
    G = GALLERY
    # base block (an L: the full width at the south end for the landing)
    m.bx(-3.0, 5.0, -7.4, 10.0, 0.0, G, 'navy', cull='b')
    m.bx(-5.0, 5.0, -10.0, -7.4, 0.0, G, 'navy', cull='b')
    # base details: doors, portholes, a plinth, the gallery deck paint and kick plates
    fq(m, -5.0, 5.0, -10.003, 0.0, 0.3, 'dark')
    m.bx(5.0, 5.003, -10.0, 10.0, 0.0, 0.3, 'dark', hull='none', cull='tbfkl')
    fq(m, -0.9, 0.3, -10.006, 0.0, 2.15, 'navyD')
    fq(m, -0.8, 0.2, -10.009, 1.4, 1.95, 'glassD')
    text(m, 'ISLAND  ACCESS', -0.3, -10.006, 2.35, 0.2, 'white')
    fq(m, 2.0, 3.6, -10.006, 0.0, 2.6, 'steelD')
    for i in range(5):
        fq(m, 2.08, 3.52, -10.009, 0.2 + i * 0.5, 0.3 + i * 0.5, 'dark')
    for y in (-5.0, -1.0, 3.0, 7.0):
        m.bx(5.003, 5.006, y - 0.5, y + 0.5, 0.0, 2.2, 'navyD', hull='none', cull='tbfkl')
        xdisc(m, 5.004, y + 1.4, 2.6, 0.18, 'glassD', seg=8)
    m.bx(-3.003, -3.0, 2.2, 9.6, 0.0, 0.3, 'dark', hull='none', cull='tbfkr')
    for y in (4.0, 7.5):
        m.bx(-3.006, -3.004, y - 0.45, y + 0.45, 0.0, 2.1, 'navyD', hull='none', cull='tbfkr')
    # fire stations on the north part of the west face (open ground beside the stair foot)
    m.bx(-3.3, -3.0, 5.0, 5.7, 0.4, 1.4, 'fire', cull='')
    m.bx(-3.3, -3.0, 8.4, 9.1, 0.4, 1.4, 'fire', cull='')
    # gallery deck paint (non-skid) and a yellow edge
    uq(m, -5.0, 5.0, -10.0, -7.4, G + 0.003, 'deck')
    uq(m, 2.2, 5.0, -7.4, 10.0, G + 0.003, 'deck')
    uq(m, -2.95, 2.2, -7.4, -7.25, G + 0.003, 'yellow')
    # gallery rails: south edge, east edge, the north end of the east strip, the west side of the landing
    def rail_x(x0, x1, y):
        cyl_x(m, x0, x1, y, G + 1.05, 0.035, 'yellow', seg=6, caps=False)
        cyl_x(m, x0, x1, y, G + 0.55, 0.025, 'yellow', seg=5, caps=False)
        m.bx(x0, x1, y - 0.015, y + 0.015, G, G + 0.12, 'yellowD', hull='none', cull='b')
        x = x0
        while x <= x1 + 1e-6:
            m.cy((x, y, G), 0.04, 0.04, 1.11, 'yellow', seg=6)
            PD.rail_foot(m, x, y, G)
            x += (x1 - x0) / max(1, round((x1 - x0) / 2.0))

    def rail_y(x, y0, y1):
        cyl_y(m, x, y0, y1, G + 1.05, 0.035, 'yellow', seg=6, caps=False)
        cyl_y(m, x, y0, y1, G + 0.55, 0.025, 'yellow', seg=5, caps=False)
        m.bx(x - 0.015, x + 0.015, y0 + 0.02, y1 - 0.02, G, G + 0.12, 'yellowD', hull='none', cull='b')
        n = max(1, round((y1 - y0) / 2.0))
        for i in range(1, n):   # the corner posts belong to the rails along X
            m.cy((x, y0 + (y1 - y0) * i / n, G), 0.04, 0.04, 1.11, 'yellow', seg=6)
            PD.rail_foot(m, x, y0 + (y1 - y0) * i / n, G)
    rail_x(-4.92, 4.92, -9.92)
    rail_y(4.92, -9.92, 9.92)
    rail_x(2.25, 4.92, 9.92)
    rail_y(-4.92, -9.92, -7.45)
    # the stair up the west face: rises toward -Y (south) from y = +1.6 to the landing at y = -7.4
    m.push(-4.0, -2.9, 180)   # local frame: x flipped, +Y = Blender -Y; the stair runs local y -4.5 .. 4.5
    stair_visual(m, -0.95, 0.9, -4.5, 18, rails=(False, True))
    PD.stair_detail(m, -0.95, 0.9, -4.5, 18)
    # a solid side under the outer stringer (local +X is the outer side: the stair is closed underneath)
    m.prism([(-4.5, 0.0), (4.5, 0.0), (4.5, G - 0.3)], 0.86, 0.92, ['navyD'])
    m.pop()
    cols = []
    cols.append(cb(-3.0, -7.4, 0.0, 5.0, 10.0, G, True))
    cols.append(cb(-5.0, -10.0, 0.0, 5.0, -7.4, G, True))
    # a solid skin on the base block's face beside the stair: from a tread two steps below the gallery (exactly a
    # robot's step up) nobody steps sideways onto the block; at the top tread the gallery is one step up
    cols.append(cb(-3.0, -7.4, 0.0, -2.85, 1.6, G - 0.05))
    loc = []
    steps(loc, -0.9, 0.88, -4.5, 18)
    stair_side_cols(loc, 0.92, -4.5, 18)
    stair_cols_rot(cols, loc, 180, -4.0, -2.9)
    for c in ((-5.0, -10.0, -4.86, -7.4), (-5.0, -10.0, 5.0, -9.86), (4.86, -10.0, 5.0, 10.0), (2.2, 9.86, 5.0, 10.0)):
        cols.append(cb(c[0], c[1], G, c[2], c[3], G + 1.1))
    # the tower body (3.6 .. 14 m), set back from the gallery
    T0, T1 = G, 14.0
    m.bx(-3.0, 2.2, -7.2, 10.0, T0, T1 - 0.2, 'navy', cull='b')
    for z0, z1 in ((4.5, 5.9), (7.9, 9.3)):
        window_band(m, -1.0 if z0 < 6 else -2.7, 1.9, -7.203, z0, z1, every=0.9)
        window_band_x(m, -6.9, 9.6, 2.203, z0, z1, every=1.2, face=1)
    fq(m, -2.4, -1.2, -7.203, T0, T0 + 2.15, 'navyD')
    fq(m, -2.3, -1.3, -7.206, T0 + 1.3, T0 + 1.9, 'glassD')
    # phased-array panels (flat octagons) and the hull number toward the runway
    for (y, z) in ((-3.5, 11.9), (5.5, 11.9)):
        pts = [(2.206, y + math.cos(a) * 1.3, z + math.sin(a) * 1.3) for a in [math.radians(22.5 + 45 * i) for i in range(8)]]
        poly(m, pts, 'dark', (1, 0, 0))
        poly(m, [(p[0] + 0.004, (p[1] - y) * 0.82 + y, (p[2] - z) * 0.82 + z) for p in pts], 'navyD', (1, 0, 0))
    pts = [(-0.4 + math.cos(a) * 1.3, -7.206, 11.9 + math.sin(a) * 1.3) for a in [math.radians(22.5 + 45 * i) for i in range(8)]]
    poly(m, pts, 'dark', (0, -1, 0))
    text(m, '01', 0.8, 2.206, 9.6, 3.6, 'white', face='x+', font='display')
    m.bx(-3.1, 2.3, -7.3, 10.1, T1 - 0.2, T1, 'navyD', cull='')
    cols.append(cb(-3.0, -7.2, G, 2.2, 10.0, 17.4))
    make('Landmark_Island', m, ao, cols=cols)

    # ---- the top: the flight-control cab (14 .. 17.4 m, glazed on all sides, overhanging toward the runway and the
    # apron), the mast with its radars and antennas
    m = new(pal)
    C0, C1 = 14.0, 17.0
    m.bx(-3.0, 3.0, -7.8, 9.6, C0, C0 + 0.6, 'navy', cull='')
    m.bx(-3.0, 3.0, -7.8, 9.6, C1 - 0.4, C1, 'navy', cull='')
    m.bx(-2.6, 2.6, -7.4, 9.2, C0 + 0.6, C1 - 0.4, 'glassD', hull='none', cull='tb')
    for (x0, x1, y) in ((-2.6, 2.6, -7.405),):
        window_band(m, x0, x1, y, C0 + 0.6, C1 - 0.4, every=1.3)
    window_band_x(m, -7.4, 9.2, 2.605, C0 + 0.6, C1 - 0.4, every=1.4, face=1)
    window_band_x(m, -7.4, 9.2, -2.605, C0 + 0.6, C1 - 0.4, every=1.4, face=-1)
    m.bx(-3.2, 3.2, -8.0, 9.8, C1, C1 + 0.35, 'navyD', cull='')
    text(m, 'PELAGIC  AIRBASE', 0, -7.805, C0 + 0.12, 0.38, 'white')
    # the mast: a steel lattice on the cab roof, yards, radars, antennas, lights
    M0 = C1 + 0.35
    for (x, y) in ((-0.9, 0.4), (0.9, 0.4), (0.0, 1.9)):
        m.bm_((x, y, M0), (x * 0.35, 0.9 + (y - 0.9) * 0.35, M0 + 8.0), 0.12, 'steel')
    for k in range(4):
        z = M0 + 1.0 + k * 1.8
        f = 1 - (z - M0) / 8.0 * 0.65
        pa = [(-0.9 * f, 0.9 + (0.4 - 0.9) * f), (0.9 * f, 0.9 + (0.4 - 0.9) * f), (0.0, 0.9 + (1.9 - 0.9) * f)]
        for i in range(3):
            a, b = pa[i], pa[(i + 1) % 3]
            m.bm_((a[0], a[1], z), (b[0], b[1], z), 0.06, 'steel', hull='none')
    m.bx(-2.4, 2.4, 0.75, 1.05, M0 + 4.6, M0 + 4.8, 'steelD', cull='')
    for s in (-1, 1):
        m.cy((s * 2.2, 0.9, M0 + 4.8), 0.02, 0.02, 1.4, 'black', seg=4, hull='none')
    m.cy((0, 0.9, M0 + 8.0), 0.18, 0.18, 0.4, 'steelD', seg=8)
    m.bx(-1.6, 1.6, 0.7, 1.1, M0 + 8.4, M0 + 8.75, 'dark', cull='')   # the air-search radar bar
    m.cy((0, 0.9, M0 + 8.75), 0.03, 0.02, 3.0, 'black', seg=4, hull='none')
    m.cy((0, 0.9, M0 + 11.7), 0.1, 0.1, 0.15, 'beacon', seg=6, hull='none')
    m.sp((1.8, 4.5, M0 + 1.3), 1.1, 'wallL', seg=(10, 6))   # a radome on its own pedestal
    m.cy((1.8, 4.5, M0), 0.25, 0.25, 0.4, 'steelD', seg=8)
    m.bx(-2.0, -0.8, 5.5, 6.7, M0, M0 + 0.9, 'navyD', cull='b')   # air-con units, a cable tray
    m.bx(-2.0, 2.0, -6.5, -5.9, M0, M0 + 0.3, 'steelD', cull='b')
    m.cy((-1.6, -3.0, M0), 0.04, 0.03, 4.0, 'black', seg=4, hull='none')
    m.cy((1.6, -3.5, M0), 0.04, 0.03, 3.0, 'black', seg=4, hull='none')
    make('Landmark_IslandTop', m, ao)


# ================================================================ the second tower (zone 2 landmark) [8, 12]
def build_tower2(pal, ao):
    """Footprint x -4..4, y -6..6. A base block (x -2..4) 3.6 m high whose roof is the balcony, the stair up its west
    face rising south to the landing, the tower shaft on the north-east of the base, the approach-control cab at
    12 m, its antenna mast and windsock."""
    m = new(pal)
    G = GALLERY
    m.bx(-2.0, 4.0, -4.5, 6.0, 0.0, G, 'navy', cull='b')
    m.bx(-4.0, 4.0, -6.0, -4.5, 0.0, G, 'navy', cull='b')
    fq(m, -4.0, 4.0, -6.003, 0.0, 0.3, 'dark')
    fq(m, 0.2, 1.4, -6.006, 0.0, 2.15, 'navyD')
    fq(m, 0.3, 1.3, -6.009, 1.4, 1.95, 'glassD')
    window_band(m, 2.0, 3.6, -6.006, 1.0, 2.3, every=0.8)
    window_band_x(m, -4.0, 5.5, 4.003, 1.0, 2.3, every=1.0, face=1)
    text(m, 'APPROACH  CONTROL', 0.0, -6.006, 2.6, 0.24, 'white')
    uq(m, -4.0, 4.0, -6.0, -4.5, G + 0.003, 'deck')
    uq(m, -2.0, 0.4, -4.5, 6.0, G + 0.003, 'deck')
    uq(m, 0.4, 4.0, -4.5, 1.4, G + 0.003, 'deck')

    def rail_x(x0, x1, y):
        cyl_x(m, x0, x1, y, G + 1.05, 0.035, 'yellow', seg=6, caps=False)
        cyl_x(m, x0, x1, y, G + 0.55, 0.025, 'yellow', seg=5, caps=False)
        x = x0
        while x <= x1 + 1e-6:
            m.cy((x, y, G), 0.04, 0.04, 1.11, 'yellow', seg=6)
            PD.rail_foot(m, x, y, G)
            x += (x1 - x0) / max(1, round((x1 - x0) / 2.0))

    def rail_y(x, y0, y1):
        cyl_y(m, x, y0, y1, G + 1.05, 0.035, 'yellow', seg=6, caps=False)
        cyl_y(m, x, y0, y1, G + 0.55, 0.025, 'yellow', seg=5, caps=False)
        n = max(1, round((y1 - y0) / 2.0))
        for i in range(1, n):   # the corner posts belong to the rails along X
            m.cy((x, y0 + (y1 - y0) * i / n, G), 0.04, 0.04, 1.11, 'yellow', seg=6)
            PD.rail_foot(m, x, y0 + (y1 - y0) * i / n, G)
    rail_x(-3.92, 3.92, -5.92)
    rail_y(3.92, -5.92, 5.92)
    rail_x(-1.95, 0.4, 5.92)
    rail_y(-3.92, -5.92, -4.55)
    rail_y(-1.98, -4.4, 5.92)
    m.cy((-1.98, -4.4, G), 0.04, 0.04, 1.11, 'yellow', seg=6)
    PD.rail_foot(m, -1.98, -4.4, G)
    m.push(-3.0, 0.0, 180)
    stair_visual(m, -0.95, 0.9, -4.5, 18, rails=(False, True))
    PD.stair_detail(m, -0.95, 0.9, -4.5, 18)
    m.prism([(-4.5, 0.0), (4.5, 0.0), (4.5, G - 0.3)], 0.86, 0.92, ['navyD'])
    m.pop()
    # the balustrade along the balcony's west edge over the stair (the stair's inner rail): nobody steps sideways from
    # the stair onto the balcony, they go round by the landing (robots path the same way: the rail blocks those nav
    # cells, so the flow field and the physics agree)
    cols = [cb(-2.0, -4.5, 0.0, 4.0, 6.0, G, True), cb(-4.0, -6.0, 0.0, 4.0, -4.5, G, True), cb(-2.1, -4.4, 0.0, -1.92, 6.0, G + 1.1)]
    loc = []
    steps(loc, -0.9, 0.88, -4.5, 18)
    stair_side_cols(loc, 0.92, -4.5, 18)
    stair_cols_rot(cols, loc, 180, -3.0, 0.0)
    for c in ((-4.0, -6.0, -3.86, -4.5), (-4.0, -6.0, 4.0, -5.86), (3.86, -6.0, 4.0, 6.0), (-2.0, 5.86, 0.4, 6.0)):
        cols.append(cb(c[0], c[1], G, c[2], c[3], G + 1.1))
    # the shaft: x 0.4 .. 4.0, y 1.4 .. 6.0, 3.6 .. 12 m, a door onto the balcony, a ladder cage, cable trays
    m.bx(0.4, 4.0, 1.4, 6.0, G, 12.0, 'wall', cull='b')
    for z in (6.0, 9.0):
        fq(m, 0.4, 4.0, 1.397, z, z + 0.15, 'wallD')
    fq(m, 1.6, 2.6, 1.397, G, G + 2.1, 'navyD')
    fq(m, 1.7, 2.5, 1.394, G + 1.3, G + 1.85, 'glassD')
    window_band(m, 0.8, 3.6, 1.397, 7.0, 8.2, every=0.9)
    window_band_x(m, 1.8, 5.6, 4.003, 7.0, 8.2, every=0.9, face=1)
    cols.append(cb(0.4, 1.4, G, 4.0, 6.0, 12.0))
    # the cab: a glazed box overhanging the shaft, roof, mast, beacon, windsock
    m.bx(-0.4, 4.8, 0.6, 6.8, 12.0, 12.5, 'navyD', cull='')
    m.bx(-0.2, 4.6, 0.8, 6.6, 12.5, 14.6, 'glassD', hull='none', cull='tb')
    window_band(m, -0.2, 4.6, 0.797, 12.5, 14.6, every=1.2)
    window_band_x(m, 0.8, 6.6, 4.603, 12.5, 14.6, every=1.2, face=1)
    window_band_x(m, 0.8, 6.6, -0.203, 12.5, 14.6, every=1.2, face=-1)
    m.bx(-0.6, 5.0, 0.4, 7.0, 14.6, 15.0, 'navy', cull='')
    text(m, 'PELAGIC APPROACH', 2.2, 0.395, 12.12, 0.28, 'white', maxw=4.8)
    m.cy((3.6, 5.6, 15.0), 0.06, 0.04, 4.2, 'steel', seg=5)
    m.cy((3.6, 5.6, 19.2), 0.12, 0.12, 0.16, 'beacon', seg=6)
    m.cy((0.6, 1.5, 15.0), 0.05, 0.04, 2.6, 'steel', seg=5)
    m.cy((0.6, 1.5, 17.6), 0.18, 0.06, 0.9, 'orange', seg=6, rot=(0, 90, 0))
    m.bx(0.2, 1.6, 5.2, 6.4, 15.0, 15.5, 'steelD', cull='b')
    make('Landmark_Tower2', m, ao, cols=cols)


# ================================================================ the hangar shells (zone 2) [24, 20]
def hangar_walls(m, label):
    H = HANGAR_H
    # back wall and side walls, 5 cm proud of the footprint so the mezzanine slabs end inside them
    m.bx(-11.6, 11.6, 9.6, 10.05, 0.0, H + 0.6, 'corr', cull='b')
    for s in (-1, 1):
        x0, x1 = sorted((s * 11.6, s * 12.05))
        m.bx(x0, x1, -10.0, 10.05, 0.0, H + 0.6, 'corr', cull='b')
    # corrugation, a dark dado, the high window band, on both faces
    for i in range(40):
        x = -11.6 + (i + 0.5) * 23.2 / 40
        fq(m, x - 0.06, x + 0.06, 9.597, 1.2, H - 0.3, 'corrD')
        for (za, zb) in (((1.2, 6.3), (7.7, H - 0.3)) if abs(x) < 8.1 else ((1.2, H - 0.3),)):
            bq(m, x - 0.06, x + 0.06, 10.053, za, zb, 'corrD')
    fq(m, -11.6, 11.6, 9.597, 0.0, 1.2, 'steelD')
    bq(m, -11.6, 11.6, 10.053, 0.0, 1.2, 'steelD')
    for s in (-1, 1):
        xi, xo = s * 11.6, s * 12.05
        for i in range(32):
            y = -9.3 + (i + 0.5) * 18.6 / 32
            bands = ((1.2, 6.3), (7.7, H - 0.3)) if abs(y) < 6.1 else ((1.2, H - 0.3),)
            if s < 0:
                m.bx(xi + 0.002, xi + 0.004, y - 0.06, y + 0.06, 1.2, H - 0.3, 'corrD', hull='none', cull='tbfkl')
                for (za, zb) in bands:
                    m.bx(xo - 0.004, xo - 0.002, y - 0.06, y + 0.06, za, zb, 'corrD', hull='none', cull='tbfkr')
            else:
                m.bx(xi - 0.004, xi - 0.002, y - 0.06, y + 0.06, 1.2, H - 0.3, 'corrD', hull='none', cull='tbfkr')
                for (za, zb) in bands:
                    m.bx(xo + 0.002, xo + 0.004, y - 0.06, y + 0.06, za, zb, 'corrD', hull='none', cull='tbfkl')
        if s < 0:
            m.bx(xi + 0.002, xi + 0.004, -9.2, 9.6, 0.0, 1.2, 'steelD', hull='none', cull='tbfkl')
            m.bx(xo - 0.004, xo - 0.002, -10.0, 10.05, 0.0, 1.2, 'steelD', hull='none', cull='tbfkr')
        else:
            m.bx(xi - 0.004, xi - 0.002, -9.2, 9.6, 0.0, 1.2, 'steelD', hull='none', cull='tbfkr')
            m.bx(xo + 0.002, xo + 0.004, -10.0, 10.05, 0.0, 1.2, 'steelD', hull='none', cull='tbfkl')
        window_band_x(m, -6.0, 6.0, xo + s * 0.004, 6.4, 7.6, every=1.5, face=s)
    window_band(m, -8.0, 8.0, 10.056, 6.4, 7.6, every=1.6, face=1)
    # columns inside every 4 m (the back wall and the side walls)
    for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
        m.bx(x - 0.15, x + 0.15, 9.3, 9.6, 0.0, H - 0.6, 'steelD', cull='b')
    for s in (-1, 1):
        for y in (-6.0, -2.0, 2.0, 6.0):
            x0, x1 = sorted((s * 11.3, s * 11.6))
            m.bx(x0, x1, y - 0.15, y + 0.15, 0.0, H - 0.8, 'steelD', cull='b')
    # a personnel door and safety boards on the outside of the east side wall
    m.bx(12.055, 12.058, 3.0, 4.1, 0.0, 2.2, 'navyD', hull='none', cull='tbfkl')
    m.bx(12.055, 12.058, -3.0, -1.4, 1.2, 2.2, 'white', hull='none', cull='tbfkl')
    text(m, 'NO SMOKING', 12.061, -2.2, 1.85, 0.2, 'fire', face='x+')
    text(m, 'FOD CHECK', 12.061, -2.2, 1.45, 0.2, 'black', face='x+')
    # the door stacks: three corrugated leaves on each side of the opening, the header over it with the name
    for s in (-1, 1):
        for k in range(3):
            x0, x1 = sorted((s * (9.6 + k * 0.7), s * (9.6 + k * 0.7 + 0.82)))
            y0 = -10.0 + k * 0.24
            m.bx(x0, x1, y0, y0 + 0.2, 0.0, 7.2, 'corr' if k % 2 else 'corrD', cull='b')
            fq(m, x0 + 0.05, x1 - 0.05, y0 - 0.003, 0.0, 0.6, 'yellow')
    m.bx(-11.6, 11.6, -10.0, -9.3, 7.2, H + 0.6, 'corr', cull='')
    fq(m, -11.6, 11.6, -10.003, 7.2, 7.4, 'steelD')
    m.bx(-11.0, -6.0, -10.04, -10.0, 7.7, 9.3, 'blueD', hull='none', cull='k')
    text(m, label, -8.5, -10.045, 8.05, 0.95, 'white')
    text(m, 'PELAGIC AIRBASE', 4.5, -10.006, 8.15, 0.7, 'blueD')
    # the floor: epoxy, the aircraft bay outline, walkway lines
    uq(m, -11.6, 11.6, -9.3, 9.6, 0.008, 'epoxy')
    for x in (-8.6, 8.6):
        uq(m, x - 0.06, x + 0.06, -9.3, 9.3, 0.011, 'yellow')
    uq(m, -8.54, 8.54, -9.0, -8.88, 0.011, 'yellow')
    uq(m, -8.54, 8.54, 5.4, 5.52, 0.011, 'yellow')
    cols = [cb(-12.05, 9.6, 0.0, 12.05, 10.05, H), cb(-12.05, -10.0, 0.0, -11.6, 9.6, H), cb(11.6, -10.0, 0.0, 12.05, 9.6, H)]
    for s in (-1, 1):   # one box per door leaf (they step back toward the side walls)
        for k in range(3):
            x0, x1 = sorted((s * (9.6 + k * 0.7), s * (9.6 + k * 0.7 + 0.82)))
            y0 = -10.0 + k * 0.24
            cols.append(cb(x0, -10.0, 0.0, x1, y0 + 0.2, 7.2))
    for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
        cols.append(cb(x - 0.15, 9.3, 0.0, x + 0.15, 9.6, H - 0.6))
    for s in (-1, 1):
        for y in (-6.0, -2.0, 2.0, 6.0):
            x0, x1 = sorted((s * 11.3, s * 11.6))
            cols.append(cb(x0, y - 0.15, 0.0, x1, y + 0.15, H - 0.8))
    return cols


def build_hangars(pal, ao):
    for name, label in (('Landmark_Hangar1', 'HANGAR 1'), ('Landmark_Hangar2', 'HANGAR 2')):
        m = new(pal)
        cols = hangar_walls(m, label)
        make(name, m, ao, cols=cols)
    # the roof: the deck slab, four roof trusses, purlins, high-bay lamps
    m = new(pal)
    H = HANGAR_H
    m.bx(-12.25, 12.25, -10.3, 10.25, H + 0.6, H + 0.9, 'corrD', cull='')
    m.bx(-12.25, 12.25, -10.3, 10.25, H + 0.9, H + 1.1, 'steel', cull='b')
    dq(m, -11.6, 11.6, -9.3, 9.6, H + 0.597, 'corr')
    for y in (-6.0, -2.0, 2.0, 6.0):
        m.bm_((-11.5, y, H + 0.5), (11.5, y, H + 0.5), 0.16, 'steelD')
        m.bm_((-11.5, y, H - 0.6), (11.5, y, H - 0.6), 0.14, 'steelD')
        for i in range(6):
            xa = -11.6 + i * 23.2 / 6
            xb = xa + 23.2 / 6
            m.bm_((xa, y, H - 0.6), (xb, y, H + 0.5), 0.07, 'steel', hull='none')
            m.bm_((xb, y, H - 0.6), (xb, y, H + 0.5), 0.05, 'steel', hull='none')
        for x in (-6.0, 0.0, 6.0):
            m.cy((x, y, H - 1.3), 0.32, 0.12, 0.6, 'dark', seg=8)
            dq(m, x - 0.22, x + 0.22, y - 0.22, y + 0.22, H - 1.305, 'lampW')
            m.cy((x, y, H - 0.7), 0.012, 0.012, 0.1, 'black', seg=4, hull='none')
    for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
        m.bm_((x, -9.3, H + 0.5), (x, 9.6, H + 0.5), 0.12, 'steelD', hull='none')
    for x in (-6.0, 6.0):
        m.bx(x - 1.0, x + 1.0, -3.0, 3.0, H + 1.1, H + 1.5, 'navyD', cull='b')
    make('Landmark_HangarRoof', m, ao)


def build_struct(pal, ao):
    build_edges(pal, ao)
    build_corners(pal, ao)
    build_fences(pal, ao)
    build_barricade(pal, ao)
    build_ops(pal, ao)
    build_gate(pal, ao)
    build_trail(pal, ao)
    build_decks(pal, ao)
    build_island(pal, ao)
    build_tower2(pal, ao)
    build_hangars(pal, ao)
