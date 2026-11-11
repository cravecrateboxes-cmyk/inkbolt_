"""kit-townhomes street pieces: paving and lawn tiles, road paint, fences and walls (theme `links` runs modelled along
Blender Y: <Name> is the half module from the cell centre toward -Y, <Name>Full a straight 1 m module, <Name>Post the
joint), the planted median and cul-de-sac island, street furniture, trees, yard props, the zone gate, the garden-wall
trail, the exit hatch and the low-poly backdrop (town-house rows, tree clumps).
"""
import math
import random

from townhomes_base import *  # noqa: F401,F403
from fam_kit_city2 import GW  # noqa: F401  (gate opening half width, shared with the other street kits)


# ================================================================ floors (no collision)
def build_floor(pal, ao):
    # sidewalk slabs keep their curb sides; lawns, driveways, the pool deck and mulch are top faces only (3 - 4 cm up,
    # no sides: the edge is too low to read and the zones stay light)
    for name, c, j in (('Walk', 'walk', 'curb'), ('WalkB', 'walkB', 'curb')):
        m = new(pal)
        tile(m, 0, 0, c, j, h=0.06)
        make(name, m, ao, hull=0)
    for name, c, h in (('Lawn', 'grass', 0.03), ('LawnB', 'grassD', 0.03), ('Drive', 'walk', 0.025), ('Deck', 'stuP', 0.04), ('Mulch', 'woodD', 0.035)):
        m = new(pal)
        uq(m, -0.5, 0.5, -0.5, 0.5, h, c)
        if name == 'Drive':
            uq(m, -0.5, 0.5, 0.47, 0.5, h + 0.004, 'curb')
        if name == 'Deck':
            uq(m, 0.47, 0.5, -0.5, 0.5, h + 0.004, 'stoneD')
        if name == 'Mulch':
            for (x, y, c2) in ((-0.25, -0.2, 'tileR'), (0.2, 0.25, 'shingle')):
                uq(m, x - 0.08, x + 0.08, y - 0.06, y + 0.06, h + 0.004, c2)
        make(name, m, ao, hull=0)
    # stepping-stone path across a lawn cell
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.03, 'grass')
    for (y, x) in ((-0.28, -0.04), (0.24, 0.05)):
        uq(m, x - 0.3, x + 0.3, y - 0.2, y + 0.2, 0.034, 'stone')
    make('Path', m, ao, hull=0)
    # flower bed: mulch with low flowers and a stone edge
    m = new(pal)
    uq(m, -0.5, 0.5, -0.5, 0.5, 0.04, 'woodD')
    for (x, y, c) in ((-0.25, -0.22, 'flower'), (0.22, 0.25, 'doorY')):
        m.sp((x, y, 0.04), 0.2, 'leaf', seg=(5, 2), scale=(1, 1, 0.6), hull='none')
        uq(m, x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.17, c)
    make('Bed', m, ao, hull=0)
    # road paint
    m = new(pal)
    for sy in (-1, 1):
        m.bx(-0.5, 0.5, sy * 0.1 - 0.04, sy * 0.1 + 0.04, 0.004, 0.011, 'lineY', hull='none', cull='b')
    make('LaneY', m, ao, hull=0)
    m = new(pal)
    m.bx(-0.3, 0.3, -0.05, 0.05, 0.004, 0.011, 'lineW', hull='none', cull='b')
    make('LaneW', m, ao, hull=0)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.15, 0.15, 0.004, 0.011, 'lineW', hull='none', cull='b')
    make('StopLine', m, ao, hull=0)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.2, 0.2, 0.004, 0.011, 'lineW', hull='none', cull='b')
    make('Zebra', m, ao, hull=0)
    m = new(pal)
    m.cy((0, 0, 0.004), 0.34, 0.34, 0.01, 'steel', seg=10, hull='none')
    for k in range(4):
        m.bx(-0.24 + k * 0.14, -0.2 + k * 0.14, -0.22, 0.22, 0.014, 0.018, 'iron', hull='none', cull='b')
    make('Manhole', m, ao, hull=0)
    # parking stall line (along Blender Y) with a car stop
    m = new(pal)
    m.bx(-0.05, 0.05, -0.5, 0.5, 0.004, 0.011, 'lineW', hull='none', cull='b')
    make('StallLine', m, ao, hull=0)
    # a speed hump across the lane (along X): yellow chevrons, low enough to step over
    m = new(pal)
    m.prism([(-0.4, 0.0), (0.4, 0.0), (0.15, 0.08), (-0.15, 0.08)], -0.5, 0.5, ['curb'], hull='none', skip=(0,))
    for x in (-0.25, 0.25):
        poly(m, [(x - 0.12, -0.15, 0.084), (x + 0.12, -0.15, 0.084), (x + 0.12, 0.15, 0.084), (x - 0.12, 0.15, 0.084)], 'lineY', (0, 0, 1))
    make('Hump', m, ao, hull=0)


# ================================================================ fences and walls (links along Blender Y)
def run_pieces(pal, ao, name, draw, post, h, w=0.1, post_w=None):
    for (suffix, y0, y1) in (('', -0.5, -0.05), ('Full', -0.5, 0.5)):   # a half module stops short of the post
        m = new(pal)
        draw(m, y0, y1)
        make(name + suffix, m, ao, cols=[box(-w / 2, y0, 0.0, w / 2, y1, h)])
    m = new(pal)
    pw = post(m)
    make(name + 'Post', m, ao, cols=[box(-pw, -pw, 0.0, pw, pw, h + 0.1)])


def build_fences(pal, ao):
    # white picket fence (1.0 m): rails, pointed pickets
    def picket(m, y0, y1):
        for z in (0.25, 0.75):
            m.bx(-0.02, 0.02, y0, y1, z, z + 0.07, 'trim', hull='none')
        n = int(round((y1 - y0) / 0.125))
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            m.bx(0.02, 0.04, y - 0.035, y + 0.035, 0.05, 0.92, 'trim', hull='none', cull='tbfk')
            for xx in (0.02, 0.04):
                poly(m, [(xx, y - 0.035, 0.92), (xx, y + 0.035, 0.92), (xx, y, 1.0)], 'trim', (1 if xx > 0.03 else -1, 0, 0))

    def picket_post(m):
        m.bx(-0.06, 0.06, -0.06, 0.06, 0.0, 1.05, 'trim')
        m.fan((0, 0, 1.05), 1.15, 0.085, 4, ['trim'], rot=math.pi / 4)
        return 0.07
    run_pieces(pal, ao, 'Picket', picket, picket_post, 1.0, w=0.1)

    # wrought iron on a stone plinth (1.8 m)
    def iron(m, y0, y1):
        m.bx(-0.16, 0.16, y0, y1, 0.0, 0.4, 'stone', hull='full', cull='bfk')
        m.bx(-0.19, 0.19, y0, y1, 0.4, 0.48, 'stoneD', hull='full', cull='fk')
        for z in (0.6, 1.65):
            m.bx(-0.02, 0.02, y0, y1, z, z + 0.04, 'iron', hull='full')
        n = int(round((y1 - y0) / 0.14))
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            m.bx(-0.014, 0.014, y - 0.014, y + 0.014, 0.48, 1.8, 'iron', hull='none', cull='tbfk')
            for xx in (-0.014, 0.014):
                poly(m, [(xx, y - 0.03, 1.8), (xx, y + 0.03, 1.8), (xx, y, 1.9)], 'iron', (1 if xx > 0 else -1, 0, 0))

    def iron_post(m):
        m.bx(-0.26, 0.26, -0.26, 0.26, 0.0, 1.9, 'stone', cull='b')
        m.bx(-0.3, 0.3, -0.3, 0.3, 1.9, 2.04, 'stoneD')
        m.fan((0, 0, 2.04), 2.2, 0.26, 4, ['stoneD'], rot=math.pi / 4)
        return 0.3
    run_pieces(pal, ao, 'Iron', iron, iron_post, 1.88, w=0.38)

    # the community wall: coursed stone to 1.0 m, a coping, iron railing on top to 2.3 m
    def wall(m, y0, y1):
        m.bx(-0.22, 0.22, y0, y1, 0.0, 1.0, 'stone', hull='full', cull='bfk')
        for sx in (-1, 1):
            (rq if sx > 0 else lq)(m, sx * 0.224, y0, y1, 0.488, 0.512, 'stoneD')
        m.bx(-0.26, 0.26, y0, y1, 1.0, 1.1, 'stoneD', hull='full', cull='fk')
        for z in (1.25, 2.15):
            m.bx(-0.02, 0.02, y0, y1, z, z + 0.04, 'iron', hull='none', cull='fk')
        n = int(round((y1 - y0) / 0.2))
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            m.bx(-0.014, 0.014, y - 0.014, y + 0.014, 1.1, 2.3, 'iron', hull='none', cull='tbfk')

    def wall_pier(m):
        m.bx(-0.32, 0.32, -0.32, 0.32, 0.0, 2.3, 'stone', cull='b')
        m.bx(-0.37, 0.37, -0.37, 0.37, 2.3, 2.44, 'stoneD')
        m.bx(-0.1, 0.1, -0.1, 0.1, 2.44, 2.5, 'iron')
        m.bx(-0.13, 0.13, -0.13, 0.13, 2.5, 2.84, 'glassL')
        m.fan((0, 0, 2.84), 3.02, 0.2, 4, ['iron'], rot=math.pi / 4)
        return 0.37
    run_pieces(pal, ao, 'Wall', wall, wall_pier, 2.3, w=0.52)

    # clipped boxwood hedge (1.1 m)
    def hedge(m, y0, y1):
        m.bx(-0.4, 0.4, y0, y1, 0.0, 1.05, 'leafD', hull='full', cull='bfk')
        m.bx(-0.36, 0.36, y0, y1, 1.05, 1.12, 'leaf', hull='none', cull='bfk')
        for (x, y, z) in ((-0.404, (y0 + y1) / 2 - 0.1, 0.6), (0.404, (y0 + y1) / 2 + 0.12, 0.4)):
            (lq if x < 0 else rq)(m, x, y - 0.12, y + 0.12, z, z + 0.18, 'leaf')

    def hedge_post(m):
        m.bx(-0.43, 0.43, -0.43, 0.43, 0.0, 1.08, 'leafD', cull='b')
        m.sp((0, 0, 1.03), 0.4, 'leaf', seg=(6, 3), scale=(1, 1, 0.45), hull='none')
        return 0.43
    run_pieces(pal, ao, 'Hedge', hedge, hedge_post, 1.12, w=0.8)


# ================================================================ planted median and cul-de-sac island
def build_planters(pal, ao):
    """Median [2, 6]: a raised curb bed down the boulevard: lawn, clipped shrubs, flowers, an ornamental tree and an
    up-light; Island [6, 6]: the round planted island in a cul-de-sac turnaround, a shade tree in the middle"""
    m = new(pal)
    cols = []
    m.bx(-1.42, 1.42, -2.92, 2.92, 0.0, 0.16, 'curb', cull='b')
    uq(m, -1.32, 1.32, -2.82, 2.82, 0.164, 'grass')
    for y in (-1.9, 1.9):
        shrub(m, 0.0, y, 0.42, z=0.16)
        solid_ = box(-0.42, y - 0.42, 0.16, 0.42, y + 0.42, 0.85)
        cols.append(solid_)
    flowers(m, -1.1, 1.1, -0.9, 0.9, 0.168, n=8)
    flowers(m, -1.1, 1.1, -2.7, -2.5, 0.168, n=3)
    m.cy((0, 0, 0.16), 0.09, 0.07, 1.6, 'trunk', seg=6)
    m.sp((0, 0, 2.4), 1.0, 'flower', seg=(7, 4), scale=(1, 1, 0.8))
    m.sp((0.35, 0.2, 2.1), 0.55, 'stuP', seg=(6, 3))
    m.sp((-0.3, -0.25, 2.7), 0.5, 'flower', seg=(6, 3))
    cols.append(box(-0.1, -0.1, 0.16, 0.1, 0.1, 1.8))
    cols.append(wbox(-1.42, -2.92, 0.0, 1.42, 2.92, 0.16))
    make('Median', m, ao, cols=cols)
    m = new(pal)
    cols = []
    n = 12
    m.cy((0, 0, 0), 2.9, 2.9, 0.16, 'curb', seg=n)
    m.cy((0, 0, 0.16), 2.75, 2.75, 0.01, 'grass', seg=n, hull='none')
    for i in range(4):
        a = i / 4 * math.pi * 2 + math.pi / 4
        m.sp((math.cos(a) * 1.9, math.sin(a) * 1.9, 0.42), 0.4, 'leafD', seg=(6, 3), scale=(1, 1, 0.75))
    flowers(m, -1.2, 1.2, -1.2, 1.2, 0.174, n=8)
    tree_round(m, 0, 0, h=6.0, r=2.0, trunk=0.17)
    for (x0, y0, x1, y1) in ((-2.05, -2.05, 2.05, 2.05),):
        cols.append(wbox(x0, y0, 0.0, x1, y1, 0.16))
    cols += [wbox(-2.9, -1.2, 0.0, -2.05, 1.2, 0.16), wbox(2.05, -1.2, 0.0, 2.9, 1.2, 0.16),
             wbox(-1.2, -2.9, 0.0, 1.2, -2.05, 0.16), wbox(-1.2, 2.05, 0.0, 1.2, 2.9, 0.16)]
    cols.append(box(-0.18, -0.18, 0.16, 0.18, 0.18, 3.2))
    for i in range(4):
        a = i / 4 * math.pi * 2 + math.pi / 4
        x, y = math.cos(a) * 1.9, math.sin(a) * 1.9
        cols.append(box(x - 0.33, y - 0.33, 0.16, x + 0.33, y + 0.33, 0.7))
    make('Island', m, ao, cols=cols)


# ================================================================ street furniture and yard props
def build_furniture(pal, ao):
    # colonial post lantern (3.4 m)
    m = new(pal)
    m.cy((0, 0, 0), 0.13, 0.11, 0.35, 'iron', seg=5)
    m.cy((0, 0, 0.35), 0.06, 0.05, 2.75, 'iron', seg=5, hull='none')
    m.bx(-0.16, 0.16, -0.16, 0.16, 3.1, 3.16, 'iron')
    m.cy((0, 0, 3.16), 0.15, 0.2, 0.42, 'glassL', seg=5)
    m.fan((0, 0, 3.58), 3.82, 0.24, 5, ['iron'])
    m.cy((0, 0, 3.82), 0.03, 0.01, 0.1, 'iron', seg=4, hull='none')
    make('Lamp', m, ao, cols=[box(-0.13, -0.13, 0.0, 0.13, 0.13, 2.4)])
    # fire hydrant
    m = new(pal)
    m.cy((0, 0, 0), 0.16, 0.16, 0.08, 'red', seg=8)
    m.cy((0, 0, 0.08), 0.12, 0.12, 0.48, 'red', seg=8)
    m.cy((0, 0, 0.56), 0.14, 0.05, 0.14, 'trim', seg=8)
    for sx in (-1, 1):
        m.cy((sx * 0.12, 0, 0.4), 0.045, 0.045, 0.08, 'trim', seg=6, rot=(0, sx * 90, 0))
    make('Hydrant', m, ao, cols=[box(-0.17, -0.17, 0.0, 0.17, 0.17, 0.7)])
    # a house mailbox on a post (curbside), flag up
    m = new(pal)
    m.bx(-0.05, 0.05, -0.05, 0.05, 0.0, 1.0, 'trim')
    m.bx(-0.12, 0.12, -0.28, 0.24, 1.0, 1.18, 'iron')
    m.cy((0, -0.27, 1.18), 0.12, 0.12, 0.5, 'iron', seg=8, rot=(-90, 0, 0))
    m.bx(0.12, 0.14, 0.05, 0.1, 1.15, 1.4, 'red', hull='none')
    m.bx(0.12, 0.14, 0.1, 0.22, 1.33, 1.4, 'red', hull='none')
    make('PostBox', m, ao, cols=[box(-0.12, -0.3, 0.0, 0.12, 0.26, 1.32)])
    # street-name sign over a stop sign
    for (name, w1, w2) in (('StreetSign', 'LARKSPUR LN', 'MEADOW CT'),):
        m = new(pal)
        m.cy((0, 0, 0), 0.035, 0.035, 2.95, 'steel', seg=5, hull='none')
        m.bx(-0.75, 0.75, -0.02, 0.02, 2.6, 2.82, 'doorG')
        txt(m, w1, 0.0, -0.024, 2.71, 0.13, 'trim', font='display', maxw=1.35)
        txt(m, w1, 0.0, 0.024, 2.71, 0.13, 'trim', face='y+', font='display', maxw=1.35)
        m.bx(-0.02, 0.02, -0.75, 0.75, 2.84, 3.06, 'doorG')
        txt(m, w2, -0.024, 0.0, 2.95, 0.13, 'trim', face='x-', font='display', maxw=1.35)
        txt(m, w2, 0.024, 0.0, 2.95, 0.13, 'trim', face='x+', font='display', maxw=1.35)
        pts = [(math.cos(math.pi / 8 + i * math.pi / 4) * 0.33, -0.05, 2.05 + math.sin(math.pi / 8 + i * math.pi / 4) * 0.33) for i in range(8)]
        poly(m, pts, 'trim', (0, -1, 0))
        pts = [(math.cos(math.pi / 8 + i * math.pi / 4) * 0.3, -0.054, 2.05 + math.sin(math.pi / 8 + i * math.pi / 4) * 0.3) for i in range(8)]
        poly(m, pts, 'red', (0, -1, 0))
        pts = [(math.cos(math.pi / 8 + i * math.pi / 4) * 0.33, -0.046, 2.05 + math.sin(math.pi / 8 + i * math.pi / 4) * 0.33) for i in range(8)]
        poly(m, pts, 'steel', (0, 1, 0))
        txt(m, 'STOP', 0.0, -0.058, 2.05, 0.15, 'trim', font='display', maxw=0.44)
        make(name, m, ao, cols=[box(-0.05, -0.05, 0.0, 0.05, 0.05, 2.5)])
    # speed limit / kids-at-play signs (text only)
    m = new(pal)
    m.cy((0, 0, 0), 0.035, 0.035, 2.5, 'steel', seg=5, hull='none')
    m.bx(-0.3, 0.3, -0.06, -0.035, 1.75, 2.5, 'trim')
    txt(m, 'SPEED', 0.0, -0.064, 2.38, 0.09, 'iron', font='display', maxw=0.5)
    txt(m, 'LIMIT', 0.0, -0.064, 2.26, 0.09, 'iron', font='display', maxw=0.5)
    txt(m, '15', 0.0, -0.064, 1.98, 0.3, 'iron', font='display', maxw=0.5)
    make('SpeedSign', m, ao, cols=[box(-0.05, -0.07, 0.0, 0.05, 0.05, 2.5)])
    m = new(pal)
    m.cy((0, 0, 0), 0.035, 0.035, 2.4, 'steel', seg=5, hull='none')
    poly(m, [(0.0, -0.06, 1.55), (0.42, -0.06, 1.97), (0.0, -0.06, 2.39), (-0.42, -0.06, 1.97)], 'lineY', (0, -1, 0))
    poly(m, [(0.0, -0.056, 1.55), (0.42, -0.056, 1.97), (0.0, -0.056, 2.39), (-0.42, -0.056, 1.97)], 'steel', (0, 1, 0))
    txt(m, 'SLOW', 0.0, -0.064, 2.06, 0.11, 'iron', font='display', maxw=0.4)
    txt(m, 'KIDS AT PLAY', 0.0, -0.064, 1.88, 0.06, 'iron', font='display', maxw=0.46)
    make('KidsSign', m, ao, cols=[box(-0.05, -0.07, 0.0, 0.05, 0.05, 2.4)])
    # park bench [2, 1]
    m = new(pal)
    for x in (-0.85, 0.85):
        m.bx(x - 0.04, x + 0.04, -0.25, 0.25, 0.0, 0.45, 'iron')
        m.bx(x - 0.04, x + 0.04, 0.18, 0.26, 0.45, 0.88, 'iron')
    for k in range(3):
        m.bx(-0.95, 0.95, -0.24 + k * 0.15, -0.12 + k * 0.15, 0.42, 0.47, 'wood', hull='none')
    for k in range(2):
        m.bx(-0.95, 0.95, 0.22, 0.27, 0.56 + k * 0.17, 0.68 + k * 0.17, 'wood', hull='none')
    make('Bench', m, ao, cols=[box(-0.95, -0.25, 0.0, 0.95, 0.27, 0.88)])
    # park litter bin
    m = new(pal)
    m.cy((0, 0, 0), 0.25, 0.25, 0.85, 'doorG', seg=8)
    m.cy((0, 0, 0.85), 0.29, 0.27, 0.12, 'iron', seg=8)
    make('TrashCan', m, ao, cols=[box(-0.27, -0.27, 0.0, 0.27, 0.27, 0.97)])
    # green pad-mount transformer
    m = new(pal)
    m.bx(-0.55, 0.55, -0.47, 0.47, 0.0, 0.12, 'walkB')
    m.bx(-0.48, 0.48, -0.42, 0.42, 0.12, 1.15, 'leafD')
    fq(m, -0.3, 0.3, -0.424, 0.7, 0.95, 'lineY')
    txt(m, 'DANGER', 0.0, -0.428, 0.825, 0.07, 'iron', font='display', maxw=0.5)
    make('Transformer', m, ao, cols=[box(-0.55, -0.47, 0.0, 0.55, 0.47, 1.15)])
    # AC condenser by a back wall
    m = new(pal)
    m.bx(-0.4, 0.4, -0.4, 0.4, 0.0, 0.08, 'walkB', cull='b')
    m.bx(-0.36, 0.36, -0.36, 0.36, 0.08, 0.82, 'steel')
    m.cy((0, 0, 0.82), 0.28, 0.28, 0.02, 'iron', seg=10, hull='none')
    for k in range(5):
        z = 0.18 + k * 0.12
        fq(m, -0.32, 0.32, -0.364, z, z + 0.05, 'iron')
    make('ACUnit', m, ao, cols=[box(-0.4, -0.4, 0.0, 0.4, 0.4, 0.84)])
    # kettle grill
    m = new(pal)
    for k in range(3):
        a = k * 2 * math.pi / 3
        m.bm_((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.0), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.6), 0.03, 'iron', hull='none')
    m.sp((0, 0, 0.75), 0.3, 'iron', seg=(8, 5), scale=(1, 1, 0.75))
    m.cy((0, 0, 0.95), 0.03, 0.03, 0.06, 'trim', seg=4, hull='none')
    make('Grill', m, ao, cols=[box(-0.3, -0.3, 0.0, 0.3, 0.3, 1.0)])
    # stone urn planter
    m = new(pal)
    m.cy((0, 0, 0), 0.22, 0.16, 0.25, 'stone', seg=8)
    m.cy((0, 0, 0.25), 0.18, 0.36, 0.42, 'stone', seg=8)
    m.cy((0, 0, 0.67), 0.38, 0.38, 0.05, 'stoneD', seg=8)
    m.sp((0, 0, 0.78), 0.34, 'leaf', seg=(7, 4), scale=(1, 1, 0.6))
    flowers(m, -0.2, 0.2, -0.2, 0.2, 0.98, n=4)
    make('Urn', m, ao, cols=[box(-0.38, -0.38, 0.0, 0.38, 0.38, 0.95)])
    # basketball hoop on a pole (backboard facing -Y)
    m = new(pal)
    m.bx(-0.3, 0.3, 0.1, 0.5, 0.0, 0.12, 'iron')
    m.cy((0, 0.3, 0.12), 0.06, 0.06, 2.9, 'iron', seg=6)
    m.bm_((0, 0.3, 2.9), (0, -0.3, 3.05), 0.07, 'iron')
    m.bx(-0.6, 0.6, -0.36, -0.3, 2.75, 3.45, 'trim')
    fq(m, -0.2, 0.2, -0.364, 2.95, 3.2, 'red')
    fq(m, -0.16, 0.16, -0.368, 2.99, 3.16, 'trim')
    m.cy((0, -0.58, 3.0), 0.23, 0.23, 0.025, 'orange', seg=10, hull='none')
    make('Hoop', m, ao, cols=[box(-0.08, 0.2, 0.0, 0.08, 0.4, 3.0)])
    # recycling carts (blue and green)
    m = new(pal)
    for (x, c) in ((-0.33, 'fabric'), (0.33, 'doorG')):
        m.bx(x - 0.3, x + 0.3, -0.35, 0.35, 0.05, 1.05, c)
        m.bx(x - 0.32, x + 0.32, -0.39, 0.37, 1.05, 1.12, c)
        m.cy((x - 0.24, 0.3, 0.1), 0.1, 0.1, 0.06, 'iron', seg=6, rot=(0, 90, 0))
        m.cy((x + 0.18, 0.3, 0.1), 0.1, 0.1, 0.06, 'iron', seg=6, rot=(0, 90, 0))
    make('Carts', m, ao, cols=[box(-0.65, -0.39, 0.0, 0.65, 0.37, 1.12)])
    # kid's bike lying on a lawn, a wagon
    m = new(pal)
    for x in (-0.38, 0.38):
        m.cy((x, 0.0, 0.0), 0.24, 0.24, 0.04, 'iron', seg=10, hull='none')
        m.cy((x, 0.0, 0.04), 0.16, 0.16, 0.005, 'steel', seg=8, hull='none')
    m.bm_((-0.38, 0.0, 0.07), (0.1, 0.0, 0.07), 0.04, 'flower', hull='none')
    m.bm_((0.1, -0.06, 0.075), (0.38, 0.0, 0.075), 0.034, 'flower', hull='none')
    m.bx(0.25, 0.32, -0.3, 0.3, 0.1, 0.13, 'chrome', hull='none')
    make('KidBike', m, ao, cols=[box(-0.6, -0.3, 0.0, 0.6, 0.3, 0.12)])
    # garden hose reel by a wall
    m = new(pal)
    m.bx(-0.25, 0.25, -0.15, 0.15, 0.0, 0.06, 'doorG', hull='none', cull='b')
    for x in (-0.2, 0.2):
        m.bx(x - 0.03, x + 0.03, -0.12, 0.12, 0.06, 0.6, 'doorG', hull='none')
    m.cy((-0.17, 0.0, 0.42), 0.2, 0.2, 0.34, 'doorG', seg=10, rot=(0, 90, 0))
    make('HoseReel', m, ao, cols=[box(-0.25, -0.2, 0.0, 0.25, 0.2, 0.62)])


def build_trees(pal, ao):
    """Tree (a round street maple, 6 m), TreeB (a narrow columnar hornbeam), TreeC (an ornamental cherry in pink
    blossom), Shrub (a single clipped shrub), Shrubs (a foundation planting of three)"""
    m = new(pal)
    tree_round(m, 0, 0, h=6.2, r=2.0, trunk=0.16)
    make('Tree', m, ao, cols=[box(-0.17, -0.17, 0.0, 0.17, 0.17, 3.2)])
    m = new(pal)
    m.cy((0, 0, 0), 0.13, 0.1, 1.5, 'trunk', seg=6)
    m.sp((0, 0, 3.3), 0.95, 'leafD', seg=(7, 5), scale=(1, 1, 2.3))
    m.sp((0.25, -0.2, 2.5), 0.6, 'leaf', seg=(6, 4), scale=(1, 1, 1.6))
    make('TreeB', m, ao, cols=[box(-0.14, -0.14, 0.0, 0.14, 0.14, 2.0)])
    m = new(pal)
    tree_round(m, 0, 0, h=4.4, r=1.6, trunk=0.12, c='flower', c2='stuP')
    make('TreeC', m, ao, cols=[box(-0.13, -0.13, 0.0, 0.13, 0.13, 2.4)])
    m = new(pal)
    shrub(m, 0, 0, 0.42)
    make('Shrub', m, ao, cols=[box(-0.42, -0.42, 0.0, 0.42, 0.42, 0.7)])
    m = new(pal)
    for (x, r, c) in ((-0.32, 0.34, 'leafD'), (0.3, 0.3, 'leaf'), (0.0, 0.26, 'leafD')):
        m.sp((x, 0.05 if x else -0.18, r * 0.75), r, c, seg=(7, 4), scale=(1, 1, 0.85))
    make('Shrubs', m, ao, cols=[box(-0.66, -0.44, 0.0, 0.6, 0.38, 0.6)])


# ================================================================ zone gate, trail, hatch
TRAIL_H = 3.2


def build_gate(pal, ao):
    """GateFrame: a garden-wall gateway between zones: brick piers with stone caps and lanterns either side of the
    3 m opening, an iron arch over it with the THE COMMONS plate (alike on both faces); GateShutter: a pair of
    wrought-iron leaves (one mesh, rolls up when the zone is cleared)"""
    m = new(pal)
    H = TRAIL_H + 0.5
    for sx in (-1, 1):
        x0, x1 = srt(sx * 1.5, sx * GW)
        m.bx(x0, x1, -0.55, 0.55, 0.0, H, 'brk', cull='b')
        m.bx(x0 - 0.08, x1 + 0.08, -0.63, 0.63, H, H + 0.16, 'stone')
        xc = sx * (GW + 1.5) / 2
        m.bx(xc - 0.12, xc + 0.12, -0.12, 0.12, H + 0.16, H + 0.22, 'iron')
        m.bx(xc - 0.16, xc + 0.16, -0.16, 0.16, H + 0.22, H + 0.62, 'glassL')
        m.fan((xc, 0, H + 0.62), H + 0.85, 0.24, 4, ['iron'], rot=math.pi / 4)
    m.bx(-1.5, 1.5, -0.08, 0.08, 3.06, 3.24, 'iron')
    for k in range(6):
        a0, a1 = math.pi * k / 6, math.pi * (k + 1) / 6
        m.bm_((math.cos(a0) * 1.48, 0.0, 3.24 + math.sin(a0) * 0.55), (math.cos(a1) * 1.48, 0.0, 3.24 + math.sin(a1) * 0.55), 0.07 if k % 2 else 0.06, 'iron', hull='none')
    m.bx(-0.75, 0.75, -0.06, 0.06, 3.35, 3.7, 'trim')
    txt(m, 'THE COMMONS', 0.0, -0.064, 3.525, 0.2, 'iron', font='display', maxw=1.35)
    txt(m, 'THE COMMONS', 0.0, 0.064, 3.525, 0.2, 'iron', face='y+', font='display', maxw=1.35)
    make('GateFrame', m, ao, cols=[box(-GW, -0.55, 0.0, -1.5, 0.55, H + 0.16), box(1.5, -0.55, 0.0, GW, 0.55, H + 0.16)])
    m = new(pal)
    Hs = 3.05
    for z in (0.12, 1.1, Hs - 0.12):
        m.bx(-1.5, 1.5, -0.04, 0.04, z, z + 0.08, 'iron', hull='none')
    m.bx(-0.03, 0.03, -0.05, 0.05, 0.0, Hs, 'iron', hull='none')
    for i in range(20):
        x = -1.43 + i * 0.15
        if abs(x) < 0.05:
            continue
        m.bx(x - 0.016, x + 0.016, -0.016, 0.016, 0.05, Hs - 0.05, 'iron', hull='none', cull='tb')
    for sx in (-1, 1):
        m.cy((sx * 0.75, -0.02, 0.62), 0.24, 0.24, 0.04, 'lineY', seg=8, rot=(90, 0, 0), hull='none')
    sh = make('GateShutter', m, ao, hull=0)
    m = new(pal)
    m.bx(-1.5, 1.5, -0.05, 0.05, 0, Hs, 'HULL')
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(sh, tmp)


def build_perimeter(pal, ao):
    """the zone edge ('#' modules, 1 m, front = -Y = the open side): Perim (coursed stone to 1 m, a coping, an iron
    railing to 2.3 m), Perim_Hedge (a clipped 2.3 m hedge), Perim_Pier (a stone pier for corners)"""
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, -0.05, 0.0, 1.0, 'stone', hull='noside', cull='bklr')
    fq(m, -0.5, 0.5, -0.504, 0.49, 0.51, 'stoneD')
    m.bx(-0.5, 0.5, -0.5, 0.0, 1.0, 1.1, 'stoneD', hull='noside', cull='blr')
    for z in (1.25, 2.15):
        fq(m, -0.5, 0.5, -0.32, z, z + 0.04, 'iron')
    for i in range(4):
        x = -0.5 + (i + 0.5) / 4
        fq(m, x - 0.016, x + 0.016, -0.316, 1.1, 2.3, 'iron')
    make('Perim', m, ao)
    # the same over two cells (the cell and its neighbour on local +X): the chooser pairs straight wall cells
    m = new(pal)
    m.bx(-0.5, 1.5, -0.5, -0.05, 0.0, 1.0, 'stone', hull='noside', cull='bklr')
    fq(m, -0.5, 1.5, -0.504, 0.49, 0.51, 'stoneD')
    m.bx(-0.5, 1.5, -0.5, 0.0, 1.0, 1.1, 'stoneD', hull='noside', cull='blr')
    for z in (1.25, 2.15):
        fq(m, -0.5, 1.5, -0.32, z, z + 0.04, 'iron')
    for i in range(8):
        x = -0.5 + (i + 0.5) / 4
        fq(m, x - 0.016, x + 0.016, -0.316, 1.1, 2.3, 'iron')
    make('Perim2', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.3, 0.0, 2.3, 'leafD', hull='noside', cull='blrk')
    for (x, z, w, h) in ((-0.25, 0.6, 0.3, 0.4), (0.2, 1.5, 0.35, 0.35), (-0.1, 1.95, 0.25, 0.2)):
        fq(m, x - w / 2, x + w / 2, -0.504, z, z + h, 'leaf')
    m.bx(-0.5, 0.5, -0.46, 0.26, 2.3, 2.36, 'leaf', hull='none', cull='b')
    make('Perim_Hedge', m, ao)
    m = new(pal)
    m.bx(-0.5, 0.5, -0.5, 0.5, 0.0, 2.6, 'stone', cull='b')
    m.bx(-0.56, 0.56, -0.56, 0.56, 2.6, 2.74, 'stoneD')
    m.sp((0, 0, 2.92), 0.2, 'stoneD', seg=(6, 4))
    make('Perim_Pier', m, ao)


def build_trail(pal, ao):
    """garden-wall footpath between the zones (1 m slice along Blender Y, both faces alike): a brick wall on a stone
    plinth with a stone coping; variants with ivy and with a lantern on a bracket"""
    for name, extra in (('TrailWall', None), ('TrailWall_B', 'ivy'), ('TrailWall_C', 'lamp')):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.45, TRAIL_H, 'brkB', hull='noend', cull='bt')
        m.bx(-0.3, 0.3, -0.5, 0.5, 0.0, 0.45, 'stone', hull='noend', cull='b')
        m.bx(-0.33, 0.33, -0.5, 0.5, TRAIL_H, TRAIL_H + 0.14, 'stoneD', hull='noend')
        for sx in (-1, 1):
            cl = 'r' if sx < 0 else 'l'
            for k in (2, 5, 8):
                z = 0.45 + k * 0.3
                a, b = srt(sx * 0.25, sx * 0.254)
                m.bx(a, b, -0.5, 0.5, z - 0.012, z + 0.012, 'mortar', hull='none', cull=cl + 'tbfk')
            if extra == 'ivy':
                for j, (y, z0, z1) in enumerate(((-0.3, 1.2, 3.1), (0.15, 0.6, 2.8), (0.38, 1.6, 3.1))):
                    a, b = srt(sx * (0.258 + 0.005 * j), sx * (0.262 + 0.005 * j))
                    m.bx(a, b, y - 0.16, y + 0.16, z0, z1, 'leafD', hull='none', cull=cl + 'tbfk')
                    m.sp((sx * 0.3, y, z1), 0.2, 'leaf', seg=(5, 3), scale=(0.4, 1, 1), hull='none')
            elif extra == 'lamp':
                x = sx * 0.25
                a, b = srt(x, x + sx * 0.06)
                m.bx(a, b, -0.06, 0.06, 2.1, 2.3, 'iron', hull='none')
                a, b = srt(x + sx * 0.06, x + sx * 0.3)
                m.bx(a, b, -0.1, 0.1, 2.15, 2.45, 'glassL', hull='full')
                m.bx(a - 0.02, b + 0.02, -0.12, 0.12, 2.45, 2.5, 'iron', hull='none')
        make(name, m, ao)


def build_hatch(pal, ao):
    """Exit pad: a round utility vault lid in a paved ring, teal marker lights"""
    m = new(pal)
    m.cy((0, 0, 0), 1.3, 1.24, 0.1, 'walk', seg=10)
    m.cy((0, 0, 0.1), 1.08, 1.08, 0.025, 'teal', seg=10, hull='none')
    m.cy((0, 0, 0.105), 0.85, 0.85, 0.06, 'steel', seg=10)
    for k in range(3):
        m.bx(-0.5 + k * 0.4, -0.4 + k * 0.4, -0.5, 0.5, 0.165, 0.175, 'iron', hull='none', cull='b')
    for i in range(6):
        a = i / 6 * math.pi * 2 + math.pi / 6
        m.cy((math.cos(a) * 1.17, math.sin(a) * 1.17, 0.1), 0.06, 0.05, 0.06, 'amber', seg=6, hull='none')
    make('Hatch', m, ao, bevel=0.015)


# ================================================================ backdrop (low poly)
def build_backdrop(pal, ao):
    """Backdrop_Row: a row of six town houses beyond the walls (gables, flat tops, front gables in four colours) with
    window bands; Backdrop_Trees: a clump of round trees; Backdrop_Hill: a long wooded rise with a water tower"""
    m = new(pal)
    x = -18.0
    rnd = random.Random(3)
    for k, (c, h, roof) in enumerate((('sidB', 7, 'g'), ('brkT', 9, 'f'), ('stuW', 7, 'y'), ('sidY', 7, 'g'), ('brk', 9, 'f'), ('sidP', 7, 'y'))):
        w = 6.0
        m.bx(x + 0.02, x + w - 0.02, -5, 5, 0, h, c)
        if roof == 'g':
            m.prism([(-5.3, h), (5.3, h), (0.0, h + 2.6)], x + 0.03, x + w - 0.03, ['shingle'], hull='full')
        elif roof == 'y':
            m.prism([(-2.97, h), (2.97, h), (0.0, h + 2.3)], -5.3, 4.97, ['tileR'], hull='full', mat=Matrix.Translation((x + w / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
        else:
            m.bx(x - 0.05, x + w + 0.05, -5.2, 5.0, h, h + 0.35, 'trim')
        for f in range(2 if h < 8 else 3):
            z = 1.0 + f * 2.8
            fq(m, x + 0.8, x + w - 0.8, -5.004, z, z + 1.4, 'glassD' if rnd.random() < 0.3 else 'glass')
        x += w
    make('Backdrop_Row', m, ao)
    m = new(pal)
    for (dx, dy, h, r, c) in ((-4, 0, 7, 2.6, 'leaf'), (0, 1.5, 9, 3.2, 'leafD'), (4, -0.5, 7.5, 2.8, 'leaf'), (1.5, -2, 6, 2.2, 'grassD')):
        m.cy((dx, dy, 0), 0.25, 0.2, h * 0.55, 'trunk', seg=4, hull='none')
        m.sp((dx, dy, h * 0.7), r, c, seg=(6, 3))
    make('Backdrop_Trees', m, ao)
    m = new(pal)
    m.sp((0, 0, -6), 30, 'grassD', seg=(10, 4), scale=(1, 0.35, 0.45))
    for (dx, h) in ((-12, 7), (-4, 8), (6, 7)):
        m.sp((dx, -4, 6 + h * 0.5), 3.5, 'leafD', seg=(6, 3))
    m.cy((14, 0, 2), 0.4, 0.4, 14, 'steel', seg=5)
    m.cy((14, 0, 16), 3.2, 3.2, 3.5, 'trim', seg=8)
    m.fan((14, 0, 19.5), 21, 3.3, 8, ['steel'])
    make('Backdrop_Hill', m, ao)


def build_street(pal, ao):
    build_floor(pal, ao)
    build_fences(pal, ao)
    build_planters(pal, ao)
    build_furniture(pal, ao)
    build_trees(pal, ao)
    build_gate(pal, ao)
    build_perimeter(pal, ao)
    build_trail(pal, ao)
    build_hatch(pal, ao)
    build_backdrop(pal, ao)
