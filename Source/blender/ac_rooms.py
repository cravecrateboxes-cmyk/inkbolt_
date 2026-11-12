"""kit-academy rooms: classroom, computer lab, art room, science lab, robotics lab, office, lounge, corridor, cafeteria
and library furniture (see ac_base.py for the conventions: the front of a piece is Blender -Y)."""
import math
import random

from ac_base import *  # noqa: F401,F403


def desk_top(k, x0, x1, y0, y1, z, c='woodL', edge='steelD', t=0.03):
    k.bx(x0, x1, y0, y1, z - t, z, c)
    k.bx(x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, z - t - 0.025, z - t, edge, ink=False, cull='t')


def monitor(k, g, x, y, deg=0, w=0.5, z=0.75):
    """a flat screen on a foot, the screen facing -Y before the turn; g: the glow companion (screen)"""
    for kk in ([k] + ([g] if g else [])):
        kk.push(x, y, deg)
    k.bx(-0.08, 0.08, -0.06, 0.06, z, z + 0.015, 'black', ink=False)
    k.bx(-0.02, 0.02, 0.0, 0.03, z + 0.015, z + 0.12, 'black', ink=False)
    k.bx(-w / 2, w / 2, -0.03, 0.0, z + 0.1, z + 0.1 + w * 0.6, 'black')
    if g:
        g.fq(-w / 2 + 0.02, w / 2 - 0.02, -0.033, z + 0.12, z + 0.08 + w * 0.6, 'screen')
        g.fq(-w / 2 + 0.05, w / 2 - 0.12, -0.036, z + 0.18 + w * 0.3, z + 0.21 + w * 0.3, 'scrB')
        g.fq(-w / 2 + 0.05, w / 2 - 0.2, -0.036, z + 0.14 + w * 0.3, z + 0.16 + w * 0.3, 'paper')
    for kk in ([k] + ([g] if g else [])):
        kk.pop()


def office_chair(k, x, y, deg, c='navy'):
    k.push(x, y, deg)
    k.cyl(0, 0, 0.06, 0.03, 0.03, 0.36, 'black', seg=4, ink=False, caps=False)
    k.cyl(0, 0, 0.0, 0.3, 0.26, 0.06, 'black', seg=5, ink=False)
    k.bx(-0.24, 0.24, -0.24, 0.22, 0.42, 0.5, c)
    k.bx(-0.22, 0.22, 0.2, 0.27, 0.55, 1.0, c)
    k.pop()


# ================================================================ classroom
def build_classroom(k, ao):
    # student desk (1 cell): the student faces Blender +Y (game north before the turn); the chair on the -Y side
    k.begin()
    for x in (-0.29, 0.26):
        k.bx(x, x + 0.03, -0.02, 0.36, 0.0, 0.69, 'steelD', ink=False, cull='bt')
    k.bx(-0.31, 0.31, -0.04, 0.38, 0.69, 0.72, 'woodL')
    k.bx(-0.12, 0.08, 0.1, 0.3, 0.72, 0.745, 'chA', ink=False, cull='b')
    k.chair(0.0, -0.3, 180, 'chB')
    k.col(-0.32, 0.32, -0.52, 0.39, 0.0, 0.76)
    k.finish('Desk', ao=ao)
    # teacher desk [2, 1]: modesty panel on the front (-Y, the class), pedestal drawers, the chair behind (+Y)
    k.begin()
    desk_top(k, -0.8, 0.8, -0.38, 0.38, 0.76, 'wood', 'woodD')
    k.bx(-0.78, -0.3, -0.36, 0.36, 0.0, 0.7, 'woodD', cull='b')
    for z in (0.12, 0.34, 0.56):
        k.bq(-0.74, -0.34, 0.363, z, z + 0.16, 'wood')
        k.bq(-0.6, -0.48, 0.366, z + 0.12, z + 0.14, 'chrome')
    k.bx(0.74, 0.78, -0.36, 0.36, 0.0, 0.7, 'woodD', ink=False, cull='b')
    k.bx(-0.3, 0.74, -0.36, -0.33, 0.25, 0.7, 'woodD', cull='b')
    monitor(k, None, 0.35, 0.05, 180, 0.42, 0.76)
    k.bx(-0.55, -0.25, -0.2, 0.05, 0.76, 0.82, 'chD')
    k.bx(-0.53, -0.27, -0.19, 0.04, 0.82, 0.86, 'chA')
    k.sph(0.05, -0.15, 0.81, 0.05, 'chD', seg=(6, 4))
    k.cyl(-0.05, 0.15, 0.76, 0.04, 0.04, 0.1, 'paper', seg=6)
    office_chair(k, 0.2, 0.62, 180, 'navy')
    k.col(-0.8, 0.8, -0.38, 0.38, 0.0, 0.8)
    k.col(-0.05, 0.45, 0.38, 0.88, 0.0, 1.0)
    k.finish('TeacherDesk', ao=ao)
    # low bookcase [2, 1] against a wall (its back at +Y), books, a globe on top
    k.begin()
    rnd = random.Random(3)
    # an open case: sides, a back, three boards; the books stand on the boards
    for x0, x1 in ((-0.95, -0.91), (0.91, 0.95)):
        k.bx(x0, x1, -0.17, 0.17, 0.0, 1.05, 'wood', cull='b')
    k.bx(-0.91, 0.91, 0.13, 0.17, 0.0, 1.05, 'woodD', cull='b')
    for z0, z1 in ((0.0, 0.08), (0.5, 0.55), (1.0, 1.05)):
        k.bx(-0.91, 0.91, -0.17, 0.13, z0, z1, 'wood', cull='b' if z0 == 0 else '')
    for z in (0.08, 0.55):
        k.book_row(rnd, -0.88, 0.88, -0.14, 0.12, z, (0.2, 0.33))
    k.cyl(0.55, 0.0, 1.05, 0.08, 0.06, 0.08, 'woodD', seg=6)
    k.sph(0.55, 0.0, 1.3, 0.17, 'sky', seg=(8, 5))
    k.poly([(0.55 + math.cos(i / 6 * 6.283) * 0.1, -0.168, 1.3 + math.sin(i / 6 * 6.283) * 0.08) for i in range(6)], 'grass', (0, -1, 0))
    k.bx(-0.6, -0.1, -0.12, 0.12, 1.05, 1.1, 'chC')
    k.col(-0.95, 0.95, -0.17, 0.17, 0.0, 1.1)
    k.finish('Bookcase', ao=ao)
    # group table [2, 2]: a square table for four (chairs on every side, repainted per copy)
    k.begin()
    k.legs4(-0.55, 0.55, -0.55, 0.55, 0.7, 'steelD', ink=False)
    desk_top(k, -0.58, 0.58, -0.58, 0.58, 0.73)
    for i, (x, y, d) in enumerate(((0, -0.8, 0), (0.8, 0, 90), (0, 0.8, 180), (-0.8, 0, 270))):
        k.chair(x, y, d, 'chA')
        k.bx(-0.15 + x * 0.45, 0.15 + x * 0.45, -0.1 + y * 0.45, 0.12 + y * 0.45, 0.73, 0.75, ['paper', 'chE', 'skyL', 'paper'][i], ink=False)
    k.col(-0.6, 0.6, -0.6, 0.6, 0.0, 0.76)
    for (x, y) in ((0, -0.8), (0.8, 0), (0, 0.8), (-0.8, 0)):
        k.col(x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0.0, 0.5)
    k.finish('GroupTable', ao=ao)
    # computer desk [2, 1] against a wall: two monitors facing the room side (-Y), keyboards, two chairs
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.legs4(-0.9, 0.9, -0.3, 0.33, 0.7, 'steelD', ink=False)
    desk_top(k, -0.92, 0.92, -0.35, 0.35, 0.74, 'lam')
    for x in (-0.45, 0.45):
        monitor(k, g, x, 0.12, 0, 0.5, 0.74)
        k.bx(x - 0.2, x + 0.2, -0.25, -0.1, 0.74, 0.76, 'black', ink=False)
        k.chair(x, -0.62, 0, 'chA')
        k.bx(x + 0.25, x + 0.33, 0.0, 0.3, 0.0, 0.42, 'black')
    k.col(-0.92, 0.92, -0.35, 0.35, 0.0, 1.1)
    k.finish('CompDesk', ao=ao)
    g.finish('CompDesk_Glow')
    # computer island [2, 2]: two desks back to back, four screens
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.legs4(-0.85, 0.85, -0.38, 0.38, 0.7, 'steelD', ink=False)
    desk_top(k, -0.88, 0.88, -0.4, 0.4, 0.74, 'lam')
    k.bx(-0.86, 0.86, -0.02, 0.02, 0.74, 1.05, 'slate')
    for x in (-0.43, 0.43):
        for s in (-1, 1):
            monitor(k, g, x, s * 0.12, 0 if s > 0 else 180, 0.42, 0.74)
            k.chair(x, s * -0.7, 0 if s > 0 else 180, 'chA')
    k.col(-0.88, 0.88, -0.4, 0.4, 0.0, 1.1)
    k.finish('CompIsland', ao=ao)
    g.finish('CompIsland_Glow')


# ================================================================ art room
def build_art(k, ao):
    # big art table [2, 2] with four stools, paint splats, jars of brushes, a roll of paper
    k.begin()
    rnd = random.Random(5)
    k.legs4(-0.75, 0.75, -0.48, 0.48, 0.74, 'woodD')
    desk_top(k, -0.8, 0.8, -0.52, 0.52, 0.78, 'lam', 'wood')
    for q in range(6):
        x, y, r = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.35, 0.35), rnd.uniform(0.04, 0.09)
        k.disc(x, y, 0.783 + 0.003 * q, r, rnd.choice(['chA', 'chB', 'chC', 'chD', 'chE', 'chF']), n=7)
    for (x, y, c) in ((-0.3, 0.1, 'chD'), (0.35, -0.2, 'chA')):
        k.cyl(x, y, 0.78, 0.05, 0.05, 0.12, 'glassL', seg=8)
        k.cyl(x, y, 0.9, 0.006, 0.006, 0.12, c, seg=4, ink=False, caps=False)
    k.cyl(0.0, 0.3, 0.78, 0.05, 0.05, 0.6, 'paper', seg=8, rot=(0, 90, 0))
    for (x, y) in ((-0.45, -0.75), (0.45, -0.75), (-0.45, 0.75), (0.45, 0.75)):
        k.stool(x, y, 0.62, 'steelD', 'wood')
    k.col(-0.8, 0.8, -0.52, 0.52, 0.0, 0.8)
    k.finish('ArtTable', ao=ao)
    # easel (1 cell): an A-frame with a painting
    k.begin()
    rnd = random.Random(8)
    for s in (-1, 1):
        k.beam((s * 0.3, -0.12, 0.0), (s * 0.08, 0.0, 1.7), 0.04, 'wood')
    k.beam((0.0, 0.35, 0.0), (0.0, 0.02, 1.55), 0.035, 'wood')
    k.bx(-0.32, 0.32, -0.16, -0.08, 0.72, 0.76, 'wood')
    k.bx(-0.3, 0.3, -0.12, -0.09, 0.76, 1.46, 'paper')
    k.fq(-0.28, 0.28, -0.123, 0.78, 1.0, 'grass')
    k.fq(-0.28, 0.28, -0.123, 1.0, 1.44, 'sky')
    k.poly([(0.1 + math.cos(i / 8 * 6.283) * 0.08, -0.126, 1.28 + math.sin(i / 8 * 6.283) * 0.08) for i in range(8)], 'foodY', (0, -1, 0))
    k.poly([(-0.25, -0.126, 1.0), (-0.05, -0.126, 1.25), (0.15, -0.126, 1.0)], 'leafD', (0, -1, 0))
    k.col(-0.32, 0.32, -0.2, 0.36, 0.0, 1.5)
    k.finish('Easel', ao=ao)
    # sink counter [3, 1] against a wall: cabinets, a double sink, shelves of paint pots above
    k.begin()
    rnd = random.Random(9)
    k.bx(-1.45, 1.45, -0.3, 0.3, 0.0, 0.86, 'wood', cull='b')
    for i in range(5):
        x = -1.4 + i * 0.57
        k.fq(x, x + 0.52, -0.303, 0.1, 0.8, 'woodL')
        k.fq(x + 0.4, x + 0.46, -0.306, 0.6, 0.7, 'chrome')
    k.bx(-1.48, 1.48, -0.34, 0.3, 0.86, 0.9, 'lam')
    for x in (-0.45, 0.25):
        k.uq(x - 0.25, x + 0.25, -0.22, 0.12, 0.903, 'steel')
        k.uq(x - 0.2, x + 0.2, -0.18, 0.08, 0.906, 'steelD')
        k.beam((x, 0.2, 0.9), (x, 0.2, 1.2), 0.03, 'chrome', ink=False)
        k.beam((x, 0.2, 1.2), (x, 0.05, 1.12), 0.018, 'chrome', ink=False)
    k.bx(-1.4, 1.4, 0.12, 0.3, 1.6, 1.64, 'wood')
    x = -1.3
    while x < 1.25:
        c = rnd.choice(['chA', 'chB', 'chC', 'chD', 'chE', 'chF'])
        k.cyl(x, 0.2, 1.64, 0.06, 0.06, 0.12, c, seg=7)
        x += rnd.uniform(0.16, 0.24)
    k.col(-1.48, 1.48, -0.34, 0.3, 0.0, 0.92)
    k.finish('SinkCounter', ao=ao)


# ================================================================ science labs
def build_lab(k, ao):
    # lab bench [4, 2]: black epoxy top over cabinets, a raised service spine with gas taps, two sinks, six stools
    k.begin()
    k.bx(-1.75, 1.75, -0.6, 0.6, 0.0, 0.85, 'slate', cull='b')
    for s in (-1, 1):
        for i in range(4):
            x = -1.7 + i * 0.86
            k.qy(x, x + 0.8, 0.1, 0.78, s * 0.603, s, 'steel')
        k.qy(-1.75, 1.75, 0.0, 0.1, s * 0.603, s, 'black')
    k.bx(-1.8, 1.8, -0.68, 0.68, 0.85, 0.9, 'black')
    k.bx(-1.6, 1.6, -0.08, 0.08, 0.9, 1.12, 'steelD')
    for x in (-0.8, 0.8):
        for s in (-1, 1):
            k.cyl(x, s * 0.09, 1.02, 0.025, 0.025, 0.05, 'gold', seg=4, rot=(s * 90, 0, 0))
    for x in (-1.45, 1.45):
        k.uq(x - 0.22, x + 0.22, -0.3, 0.3, 0.903, 'steelD')
        k.beam((x, 0.0, 1.12), (x, 0.0, 1.38), 0.03, 'chrome', ink=False)
        k.beam((x, 0.0, 1.38), (x, -0.18, 1.3), 0.018, 'chrome', ink=False)
    for (x, y, c) in ((-0.8, -0.35, 'chC'), (0.1, 0.38, 'chA'), (0.9, -0.3, 'chE')):
        k.cyl(x, y, 0.9, 0.05, 0.05, 0.1, c, seg=6)
    k.cyl(-0.1, -0.4, 0.9, 0.03, 0.08, 0.18, 'glassL', seg=6)
    for x in (-0.9, 0.9):
        for s in (-1, 1):
            k.stool(x, s * 0.92, 0.68)
    k.col(-1.8, 1.8, -0.68, 0.68, 0.0, 1.12)
    k.finish('LabBench', ao=ao)
    # fume hood [2, 1] against a wall: base cabinet, the hood with a lit interior behind a glass sash, the duct up
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.bx(-0.9, 0.9, -0.38, 0.4, 0.0, 0.85, 'steel', cull='b')
    for i in range(3):
        x = -0.86 + i * 0.58
        k.fq(x, x + 0.54, -0.383, 0.08, 0.8, 'chrome')
    k.bx(-0.92, 0.92, -0.42, 0.4, 0.85, 0.9, 'black')
    k.bx(-0.9, -0.78, -0.38, 0.4, 0.9, 2.0, 'steel')
    k.bx(0.78, 0.9, -0.38, 0.4, 0.9, 2.0, 'steel')
    k.bx(-0.9, 0.9, -0.38, 0.4, 2.0, 2.45, 'steel')
    k.fq(-0.6, 0.6, -0.383, 2.12, 2.32, 'chE')
    k.text('FUME HOOD', 0.0, -0.386, 2.16, 0.12, 'black', font='display')
    k.bx(-0.78, 0.78, -0.36, -0.32, 1.45, 1.5, 'chrome')
    k.bx(-0.78, 0.78, 0.34, 0.4, 0.9, 2.0, 'steelD', ink=False)
    k.bx(-0.3, 0.3, -0.1, 0.3, 2.45, CEIL - 0.004, 'steel', cull='t')
    for (x, c) in ((-0.4, 'chD'), (0.1, 'chC'), (0.45, 'glassL')):
        k.cyl(x, 0.05, 0.9, 0.05, 0.05, 0.16, c, seg=8)
    g.fq(-0.76, 0.76, -0.35, 0.92, 1.98, 'navy')
    g.fq(-0.7, -0.5, -0.353, 1.1, 1.9, 'steelD')
    k.col(-0.92, 0.92, -0.42, 0.4, 0.0, 2.45)
    k.finish('FumeHood', ao=ao)
    g.finish('FumeHood_Glass')
    # skeleton model on its rolling stand (an anatomy teaching model)
    k.begin()
    k.cyl(0, 0, 0.0, 0.32, 0.32, 0.05, 'steelD', seg=10)
    for a in range(5):
        ang = a * 2 * math.pi / 5
        k.cyl(math.cos(ang) * 0.28, math.sin(ang) * 0.28, 0.0, 0.035, 0.035, 0.03, 'black', seg=5, ink=False)
    k.cyl(0, 0.12, 0.05, 0.018, 0.018, 1.75, 'steel', seg=5, ink=False, caps=False)
    k.beam((0, 0.12, 1.78), (0, 0.0, 1.78), 0.025, 'steel', ink=False)
    B = 'bone'
    k.sph(0, 0.0, 1.65, 0.11, B, seg=(8, 6), scale=(0.85, 1.0, 1.1))
    k.bx(-0.06, 0.06, -0.12, -0.02, 1.5, 1.56, B)
    for (x, z) in ((-0.035, 1.66), (0.035, 1.66)):
        k.poly([(x + math.cos(i / 6 * 6.283) * 0.022, -0.104, z + math.sin(i / 6 * 6.283) * 0.026) for i in range(6)], 'black', (0, -1, 0))
    k.cyl(0, 0.03, 0.88, 0.022, 0.022, 0.62, B, seg=5)
    for i in range(5):
        z = 1.42 - i * 0.075
        k.cyl(0, 0.0, z, 0.15 - i * 0.008, 0.15 - i * 0.008, 0.025, B, seg=10, caps=False, rot=(0, 0, 0))
    k.bx(-0.16, 0.16, -0.06, 0.06, 0.82, 0.94, B)
    for s in (-1, 1):
        k.sph(s * 0.18, 0.0, 1.45, 0.04, B, seg=(5, 4))
        k.beam((s * 0.19, 0.0, 1.44), (s * 0.22, -0.02, 1.15), 0.03, B)
        k.beam((s * 0.22, -0.02, 1.15), (s * 0.23, -0.1, 0.9), 0.025, B)
        k.bx(s * 0.23 - 0.03, s * 0.23 + 0.03, -0.14, -0.08, 0.8, 0.9, B)
        k.beam((s * 0.1, 0.0, 0.84), (s * 0.11, 0.0, 0.46), 0.04, B)
        k.beam((s * 0.11, 0.0, 0.46), (s * 0.11, 0.02, 0.1), 0.035, B)
        k.bx(s * 0.11 - 0.035, s * 0.11 + 0.035, -0.08, 0.04, 0.05, 0.09, B)
    k.col(-0.32, 0.32, -0.32, 0.32, 0.0, 1.8)
    k.finish('Skeleton', ao=ao)
    # chemical cabinet [2, 1] against a wall: glass doors over bottles, a yellow flammables cabinet below
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    rnd = random.Random(14)
    k.bx(-0.9, 0.9, -0.25, 0.25, 0.0, 0.9, 'foodY', cull='b')
    k.fq(-0.86, -0.02, -0.253, 0.08, 0.84, 'gold')
    k.fq(0.02, 0.86, -0.253, 0.08, 0.84, 'gold')
    k.fq(-0.5, 0.5, -0.256, 0.55, 0.72, 'chD')
    k.text('FLAMMABLE', 0.0, -0.259, 0.58, 0.1, 'paper', font='display', maxw=0.9)
    k.bx(-0.9, 0.9, 0.2, 0.25, 0.9, 2.16, 'wood', cull='')
    k.bx(-0.9, -0.86, -0.22, 0.2, 0.9, 2.16, 'wood')
    k.bx(0.86, 0.9, -0.22, 0.2, 0.9, 2.16, 'wood')
    k.bx(-0.9, 0.9, -0.22, 0.25, 2.16, 2.2, 'wood')
    k.bx(-0.02, 0.02, -0.22, -0.18, 0.9, 2.16, 'woodD', ink=False)
    for z in (0.95, 1.38, 1.8):
        x = -0.8
        while x < 0.75:
            c = rnd.choice(['chD', 'chC', 'chA', 'glassL', 'woodD', 'chB'])
            h = rnd.uniform(0.15, 0.3)
            k.cyl(x, -0.08, z, 0.045, 0.045, h, c, seg=5)
            x += rnd.uniform(0.15, 0.22)
        k.bx(-0.86, 0.86, -0.18, 0.2, z - 0.02, z, 'woodL', ink=False)
    g.fq(-0.86, -0.02, -0.21, 0.92, 2.16, 'navy')
    g.fq(0.02, 0.86, -0.21, 0.92, 2.16, 'navy')
    k.col(-0.9, 0.9, -0.25, 0.25, 0.0, 2.2)
    k.finish('ChemCab', ao=ao)
    g.finish('ChemCab_Glass')
    # demo bench [4, 1]: the teacher's bench (students on the front, -Y): a sink, a burner, a microscope, test tubes
    k.begin()
    k.bx(-1.8, 1.8, -0.35, 0.35, 0.0, 0.88, 'slate', cull='b')
    k.fq(-1.7, 1.7, -0.353, 0.1, 0.8, 'steel')
    k.fq(-0.9, 0.9, -0.356, 0.4, 0.62, 'paper')
    k.text('SCIENCE', 0.0, -0.359, 0.44, 0.16, 'slate', font='display')
    k.bx(-1.85, 1.85, -0.4, 0.4, 0.88, 0.93, 'black')
    k.uq(1.0, 1.5, -0.2, 0.2, 0.933, 'steelD')
    k.beam((1.25, 0.25, 0.93), (1.25, 0.25, 1.25), 0.03, 'chrome', ink=False)
    k.beam((1.25, 0.25, 1.25), (1.25, 0.05, 1.15), 0.018, 'chrome', ink=False)
    k.cyl(-1.2, 0.0, 0.93, 0.06, 0.04, 0.08, 'steelD', seg=8)
    k.cyl(-1.2, 0.0, 1.01, 0.015, 0.015, 0.12, 'steel', seg=5, ink=False)
    k.bx(-0.3, 0.1, -0.1, 0.1, 0.93, 0.95, 'black')
    k.cyl(-0.1, 0.05, 0.95, 0.02, 0.02, 0.25, 'black', seg=6, ink=False)
    k.cyl(-0.1, -0.03, 1.15, 0.04, 0.03, 0.12, 'black', seg=6, rot=(30, 0, 0))
    k.bx(0.3, 0.75, -0.08, 0.08, 0.93, 1.0, 'woodD')
    for i in range(5):
        x = 0.36 + i * 0.085
        k.cyl(x, 0.0, 0.96, 0.02, 0.02, 0.16, ['chD', 'chC', 'chA', 'chE', 'chF'][i], seg=6)
    k.col(-1.85, 1.85, -0.4, 0.4, 0.0, 1.0)
    k.finish('DemoBench', ao=ao)


# ================================================================ robotics lab
def build_robotics(k, ao):
    # workbench [3, 2]: a half-built robot arm on a turntable, a laptop, parts bins, a tool chest, stools
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.legs4(-1.3, 1.3, -0.6, 0.6, 0.86, 'steelD', t=0.05)
    k.bx(-1.25, 1.25, -0.55, 0.55, 0.2, 0.24, 'steelD', ink=False)
    desk_top(k, -1.35, 1.35, -0.65, 0.65, 0.9, 'woodL', 'steelD', 0.05)
    k.cyl(-0.4, 0.05, 0.9, 0.22, 0.22, 0.06, 'steelD', seg=12)
    k.cyl(-0.4, 0.05, 0.96, 0.08, 0.08, 0.2, 'chB', seg=8)
    k.beam((-0.4, 0.05, 1.16), (-0.2, 0.15, 1.55), 0.09, 'chE')
    k.sph(-0.2, 0.15, 1.55, 0.07, 'steelD', seg=(6, 4))
    k.beam((-0.2, 0.15, 1.55), (0.15, 0.1, 1.42), 0.07, 'chE')
    k.bx(0.12, 0.24, 0.04, 0.16, 1.32, 1.46, 'steelD')
    for s in (-1, 1):
        k.bx(0.2, 0.32, 0.1 + s * 0.04 - 0.012, 0.1 + s * 0.04 + 0.012, 1.3, 1.36, 'steel', ink=False)
    k.bx(0.55, 0.95, -0.3, -0.02, 0.9, 0.92, 'black')
    k.bx(0.55, 0.95, -0.02, 0.01, 0.92, 1.18, 'black')
    g.fq(0.58, 0.92, -0.023, 0.95, 1.15, 'scrB')
    g.fq(0.6, 0.8, -0.026, 1.05, 1.07, 'paper')
    k.bx(-1.25, -0.6, 0.35, 0.6, 0.9, 1.0, 'chA', cull='b')
    for i, c in enumerate(('chD', 'chE', 'chC')):
        k.fq(-1.22 + i * 0.21, -1.05 + i * 0.21, 0.347, 0.92, 0.98, c)
    k.bx(0.88, 1.22, 0.18, 0.52, 0.24, 0.84, 'chD')
    for z in (0.34, 0.5, 0.66):
        k.fq(0.91, 1.19, 0.177, z, z + 0.12, 'chrome')
    for (x, y) in ((-0.6, -0.95), (0.6, -0.95)):
        k.stool(x, y, 0.66)
    k.col(-1.35, 1.35, -0.65, 0.65, 0.0, 1.0)
    k.finish('RoboBench', ao=ao)
    g.finish('RoboBench_Glow')


# ================================================================ office, lounge, corridors
def build_office(k, ao):
    # reception counter [6, 2]: the visitors' ledge on the front (-Y), desks and screens on the staff side
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.bx(-2.8, 2.8, -0.45, -0.15, 0.0, 1.1, 'wood', cull='b')
    k.fq(-2.75, 2.75, -0.453, 0.08, 1.0, 'woodL')
    for i in range(6):
        x = -2.5 + i * 1.0
        k.fq(x - 0.02, x + 0.02, -0.456, 0.08, 1.0, 'woodD')
    k.bx(-2.85, 2.85, -0.6, -0.1, 1.1, 1.15, 'lam')
    k.bx(-2.8, 2.8, -0.15, 0.6, 0.72, 0.76, 'lam')
    k.bx(-2.8, -2.7, -0.15, 0.6, 0.0, 0.72, 'wood', ink=False, cull='b')
    k.bx(2.7, 2.8, -0.15, 0.6, 0.0, 0.72, 'wood', ink=False, cull='b')
    for x in (-1.6, 0.4, 2.0):
        monitor(k, g, x, 0.25, 180, 0.46, 0.76)
        office_chair(k, x + 0.1, 0.95, 180, 'slate')
    k.bx(-0.8, -0.4, -0.5, -0.2, 1.15, 1.2, 'paper')
    k.cyl(-2.3, -0.35, 1.15, 0.05, 0.04, 0.14, 'chA', seg=6)
    k.bx(1.0, 1.4, -0.5, -0.3, 1.15, 1.35, 'navy')
    k.fq(1.03, 1.37, -0.503, 1.18, 1.32, 'paper')
    k.text('SIGN IN', 1.2, -0.506, 1.22, 0.06, 'navy', font='display')
    k.col(-2.85, 2.85, -0.6, 0.6, 0.0, 1.2)
    k.finish('Reception', ao=ao)
    g.finish('Reception_Glow')
    # office desk [2, 1] (flip): a monitor, papers, the chair on the +Y side
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    desk_top(k, -0.85, 0.85, -0.38, 0.38, 0.75, 'wood', 'woodD')
    k.bx(-0.83, -0.4, -0.36, 0.36, 0.0, 0.69, 'woodD', cull='b')
    k.bx(0.79, 0.83, -0.36, 0.36, 0.0, 0.69, 'woodD', ink=False, cull='b')
    k.bx(-0.4, 0.79, -0.36, -0.33, 0.25, 0.69, 'woodD', ink=False, cull='b')
    monitor(k, g, 0.1, -0.15, 180, 0.48, 0.75)
    k.bx(-0.2, 0.25, 0.05, 0.2, 0.75, 0.77, 'black', ink=False)
    k.bx(-0.7, -0.4, -0.25, 0.1, 0.75, 0.82, 'paper')
    k.cyl(0.6, 0.1, 0.75, 0.04, 0.04, 0.1, 'chD', seg=6)
    office_chair(k, 0.1, 0.62, 180)
    k.col(-0.85, 0.85, -0.38, 0.38, 0.0, 0.8)
    k.col(-0.15, 0.35, 0.38, 0.88, 0.0, 1.0)
    k.finish('OfficeDesk', ao=ao)
    g.finish('OfficeDesk_Glow')
    # file cabinet (1 cell, front -Y)
    k.begin()
    k.bx(-0.24, 0.24, -0.3, 0.3, 0.0, 1.32, 'steel', cull='b')
    for i in range(4):
        z = 0.06 + i * 0.32
        k.fq(-0.21, 0.21, -0.303, z, z + 0.28, 'chrome')
        k.fq(-0.08, 0.08, -0.306, z + 0.2, z + 0.24, 'steelD')
        k.fq(-0.05, 0.05, -0.306, z + 0.1, z + 0.15, 'paper')
    k.bx(-0.15, 0.1, -0.1, 0.15, 1.32, 1.4, 'chE')
    k.col(-0.24, 0.24, -0.3, 0.3, 0.0, 1.4)
    k.finish('FileCab', ao=ao)
    # copier (1 cell, front -Y)
    k.begin()
    k.bx(-0.4, 0.4, -0.32, 0.32, 0.0, 0.85, 'chrome', cull='b')
    for z in (0.08, 0.32, 0.56):
        k.fq(-0.36, 0.36, -0.323, z, z + 0.2, 'steel')
        k.fq(-0.1, 0.1, -0.326, z + 0.14, z + 0.17, 'steelD')
    k.bx(-0.42, 0.42, -0.34, 0.32, 0.85, 1.05, 'paper')
    k.bx(-0.38, 0.38, -0.3, 0.3, 1.05, 1.1, 'steelD')
    k.bx(0.2, 0.38, -0.42, -0.34, 0.9, 1.0, 'steelD')
    k.bx(0.42, 0.62, -0.2, 0.2, 0.86, 0.9, 'steel')
    k.uq(0.44, 0.6, -0.18, 0.18, 0.903, 'paper')
    k.col(-0.42, 0.62, -0.42, 0.32, 0.0, 1.1)
    k.finish('Copier', ao=ao)
    # sofa [2, 1] against a wall (its back at +Y)
    k.begin()
    k.bx(-0.95, 0.95, -0.4, 0.3, 0.0, 0.42, 'slate', cull='b')
    k.bx(-0.95, 0.95, 0.12, 0.38, 0.42, 0.88, 'slate')
    for s in (-1, 1):
        a, b = sorted((s * 0.95, s * 0.78))
        k.bx(a, b, -0.4, 0.12, 0.42, 0.62, 'slate')
    for x in (-0.39, 0.39):
        k.bx(x - 0.38, x + 0.38, -0.38, 0.12, 0.42, 0.52, 'mat')
    k.bx(-0.7, -0.35, 0.02, 0.14, 0.52, 0.8, 'gold')
    k.col(-0.95, 0.95, -0.4, 0.38, 0.0, 0.88)
    k.finish('Sofa', ao=ao)
    # kitchenette [3, 1] against a wall: base cabinets, a sink, the microwave, the coffee maker, a fridge
    k.begin()
    k.bx(-1.5, 0.75, -0.3, 0.3, 0.0, 0.88, 'woodL', cull='b')
    for i in range(4):
        x = -1.45 + i * 0.55
        k.fq(x, x + 0.5, -0.303, 0.1, 0.8, 'wood')
    k.bx(-1.52, 0.77, -0.33, 0.3, 0.88, 0.92, 'lam')
    k.uq(-0.9, -0.5, -0.2, 0.15, 0.923, 'steel')
    k.beam((-0.7, 0.22, 0.92), (-0.7, 0.22, 1.2), 0.03, 'chrome', ink=False)
    k.bx(-0.2, 0.3, -0.18, 0.25, 0.92, 1.2, 'black')
    k.fq(-0.17, 0.12, -0.183, 0.97, 1.16, 'screen')
    k.bx(0.4, 0.62, -0.1, 0.2, 0.92, 1.25, 'chD')
    k.cyl(0.51, -0.05, 0.94, 0.06, 0.06, 0.1, 'glassL', seg=8)
    k.bx(0.8, 1.45, -0.32, 0.32, 0.0, 1.75, 'chrome', cull='b')
    k.fq(0.8, 1.45, -0.323, 1.12, 1.14, 'steelD')
    k.bx(0.84, 0.88, -0.38, -0.323, 1.2, 1.55, 'steelD')
    k.bx(-1.45, 0.75, 0.15, 0.32, 1.45, 2.1, 'woodL')
    k.col(-1.52, 0.77, -0.33, 0.3, 0.0, 0.92)
    k.col(0.8, 1.45, -0.38, 0.32, 0.0, 1.75)
    k.finish('Kitchenette', ao=ao)
    # lounge table [2, 2]: a round table, three chairs
    k.begin()
    k.cyl(0, 0, 0.0, 0.3, 0.3, 0.03, 'steelD', seg=10)
    k.cyl(0, 0, 0.03, 0.04, 0.04, 0.68, 'steelD', seg=6, ink=False, caps=False)
    k.cyl(0, 0, 0.71, 0.55, 0.55, 0.04, 'woodL', seg=16)
    for i in range(3):
        a = i * 2 * math.pi / 3 + 0.4
        k.chair(math.cos(a) * 0.72, math.sin(a) * 0.72, math.degrees(a) + 90, 'chA')
    k.cyl(0.1, -0.1, 0.75, 0.04, 0.04, 0.09, 'paper', seg=6)
    k.col(-0.56, 0.56, -0.56, 0.56, 0.0, 0.76)
    k.finish('LoungeTable', ao=ao)
    # bins (1 cell): trash and recycling side by side
    k.begin()
    for (x, c, lid) in ((-0.2, 'steelD', 'black'), (0.2, 'chA', 'chA')):
        k.cyl(x, 0, 0.0, 0.17, 0.19, 0.78, c, seg=8)
        k.cyl(x, 0, 0.78, 0.2, 0.2, 0.05, lid, seg=8)
    k.poly([(0.2 + math.cos(i / 3 * 6.283 + 1.57) * 0.07, -0.183 - 0.008, 0.5 + math.sin(i / 3 * 6.283 + 1.57) * 0.07) for i in range(3)], 'paper', (0, -1, 0))
    k.col(-0.4, 0.4, -0.2, 0.2, 0.0, 0.83)
    k.finish('Bins', ao=ao)
    # bench [2, 1]: slatted wood on steel legs (corridors, the locker room, the courtyard)
    k.begin()
    for i in range(3):
        y = -0.18 + i * 0.13
        k.bx(-0.95, 0.95, y, y + 0.1, 0.42, 0.46, 'wood')
    for x in (-0.75, 0.75):
        k.bx(x - 0.03, x + 0.03, -0.2, 0.2, 0.04, 0.42, 'steelD', cull='b')
        k.bx(x - 0.05, x + 0.05, -0.22, 0.22, 0.0, 0.04, 'steelD', ink=False)
    k.col(-0.95, 0.95, -0.2, 0.2, 0.0, 0.46)
    k.finish('Bench', ao=ao)
    # potted plant (1 cell)
    k.begin()
    k.cyl(0, 0, 0.0, 0.22, 0.27, 0.5, 'woodD', seg=10)
    k.disc(0, 0, 0.495, 0.25, 'bark', n=10)
    for (x, y, z, r, c) in ((0, 0, 0.95, 0.32, 'leaf'), (0.1, 0.06, 1.22, 0.24, 'leafD')):
        k.sph(x, y, z, r, c, seg=(7, 4))
    k.cyl(0, 0, 0.5, 0.03, 0.03, 0.45, 'bark', seg=5, ink=False, caps=False)
    k.col(-0.27, 0.27, -0.27, 0.27, 0.0, 1.3)
    k.finish('Plant', ao=ao)
    # banner stand (1 cell): a roll-up banner, front -Y
    k.begin()
    k.bx(-0.42, 0.42, -0.12, 0.12, 0.0, 0.1, 'steelD')
    k.bx(-0.4, 0.4, -0.02, 0.0, 0.1, 2.0, 'slate')
    k.fq(-0.36, 0.36, -0.023, 1.6, 1.9, 'gold')
    k.text('WELCOME', 0.0, -0.026, 1.66, 0.16, 'navy', font='display', maxw=0.66)
    k.text('CHALKSTONE', 0.0, -0.023, 1.2, 0.14, 'paper', font='display', maxw=0.7)
    k.text('ACADEMY', 0.0, -0.023, 1.0, 0.14, 'gold', font='display', maxw=0.7)
    k.fq(-0.3, 0.3, -0.023, 0.3, 0.8, 'skyL')
    k.text('EST 1962', 0.0, -0.026, 0.45, 0.1, 'navy', font='cond')
    k.col(-0.42, 0.42, -0.12, 0.12, 0.0, 2.0)
    k.finish('BannerStand', ao=ao)
    # weapon stand: a wooden book cart
    k.begin()
    rnd = random.Random(2)
    k.bx(-0.45, 0.45, -0.25, 0.25, 0.1, 0.7, 'wood', cull='b')
    k.fq(-0.42, 0.42, -0.253, 0.14, 0.4, 'woodD')
    k.book_row(rnd, -0.4, 0.4, -0.3, -0.05, 0.42, (0.16, 0.24))
    for (x, y) in ((-0.38, -0.2), (0.38, -0.2), (-0.38, 0.2), (0.38, 0.2)):
        k.sph(x, y, 0.05, 0.05, 'black', seg=(6, 4))
    k.finish('Stand', ao=ao)


# ================================================================ cafeteria
def build_cafeteria(k, ao):
    # the serving line [10, 3] (landmark), back to the wall (+Y): steam table with sneeze guard, tray rail, food
    # pans, the cashier stand at the -X end, the staff aisle behind closed at both ends, a back counter, a LUNCH board
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    rnd = random.Random(21)
    W = 5.0
    yF0, yF1 = -1.05, -0.2           # the steam counter
    k.bx(-4.2, W - 0.05, yF0, yF1, 0.0, 0.88, 'steel', cull='b')
    for i in range(9):
        x = -4.15 + i * 1.02
        k.fq(x, x + 0.95, yF0 - 0.003, 0.1, 0.8, 'chrome')
    k.bx(-4.25, W - 0.05, yF0 - 0.05, yF1, 0.88, 0.92, 'chrome')
    for x in range(8):
        xa = -3.9 + x * 1.06
        for j in range(2):
            ya = yF0 + 0.12 + j * 0.36
            k.uq(xa, xa + 0.48, ya, ya + 0.3, 0.923, 'steelD')
            k.uq(xa + 0.04, xa + 0.44, ya + 0.04, ya + 0.26, 0.926, rnd.choice(['food', 'foodY', 'chB', 'leaf', 'paper', 'woodD']))
            k.uq(xa + 0.54, xa + 0.98, ya + 0.04, ya + 0.26, 0.926, rnd.choice(['food', 'foodY', 'chB', 'leaf', 'paper', 'woodD'])) if xa + 0.98 < W - 0.1 else None
    # sneeze guard: posts and a glass canopy (glass = companion)
    for x in (-4.1, -2.0, 0.1, 2.2, 4.3):
        k.bx(x - 0.02, x + 0.02, yF0 + 0.25, yF0 + 0.29, 0.92, 1.42, 'chrome', ink=False)
    k.bx(-4.12, 4.32, yF0 + 0.05, yF0 + 0.35, 1.42, 1.45, 'chrome', ink=False)
    g.uq(-4.1, 4.3, yF0 + 0.06, yF0 + 0.34, 1.455, 'navy')
    g.fq(-4.1, 4.3, yF0 + 0.25, 1.0, 1.4, 'navy')
    # the tray rail (tubes on brackets along the front)
    k.bx(-4.25, W - 0.05, yF0 - 0.38, yF0 - 0.05, 0.86, 0.9, 'chrome')
    for x in (-4.0, -1.5, 1.0, 3.5):
        k.bx(x - 0.02, x + 0.02, yF0 - 0.2, yF0 - 0.05, 0.6, 0.86, 'chrome', ink=False)
    for i in range(3):
        x = -2.5 + i * 0.4
        k.bx(x, x + 0.36, yF0 - 0.36, yF0 - 0.06, 0.9, 0.92, ['chD', 'chA', 'chC'][i], ink=False)
    # the cashier stand at the west end
    k.bx(-W + 0.05, -4.25, -1.25, -0.2, 0.0, 1.0, 'slate', cull='b')
    k.bx(-W + 0.02, -4.22, -1.28, -0.17, 1.0, 1.04, 'lam')
    k.bx(-4.85, -4.45, -0.85, -0.45, 1.04, 1.24, 'black')
    g.fq(-4.82, -4.48, -0.853, 1.08, 1.2, 'scrB')
    # the end returns, the back counter with dish racks, the staff aisle between
    k.bx(W - 0.25, W - 0.05, -0.2, 1.48, 0.0, 0.92, 'steel')
    k.bx(-W + 0.05, -W + 0.25, -0.2, 1.48, 0.0, 0.92, 'steel')
    k.bx(-W + 0.25, W - 0.25, 0.95, 1.48, 0.0, 0.92, 'steel', cull='b')
    k.fq(-W + 0.25, W - 0.25, 0.947, 0.1, 0.84, 'chrome')
    for i in range(6):
        x = -4.0 + i * 1.5
        k.bx(x, x + 0.5, 1.05, 1.4, 0.92, 1.12, rnd.choice(['steelD', 'chrome', 'chA']))
    # the LUNCH board hanging over the line
    k.bx(-1.6, 1.6, -0.75, -0.65, 2.6, 3.2, 'navy')
    k.text('LUNCH LINE', 0.0, -0.753, 2.75, 0.32, 'gold', font='display', maxw=3.0)
    for x in (-1.4, 1.4):
        k.bx(x - 0.01, x + 0.01, -0.71, -0.69, 3.2, CEIL + 4.0 - 0.01, 'steelD', ink=False, cull='t')
    k.col(-W, W, yF0 - 0.38, yF1, 0.0, 0.95)
    k.col(-W, -W + 0.25, -0.2, 1.48, 0.0, 0.95)
    k.col(W - 0.25, W, -0.2, 1.48, 0.0, 0.95)
    k.col(-W + 0.25, W - 0.25, 0.95, 1.48, 0.0, 0.95)
    k.finish('Landmark_Serving', ao=ao)
    g.finish('Landmark_Serving_Glow')
    # cafeteria table [6, 2] (along X): the classic fold-up table with its benches, trays and milk cartons
    k.begin()
    rnd = random.Random(23)
    k.bx(-2.6, 2.6, -0.4, 0.4, 0.71, 0.75, 'lam')
    k.bx(-2.55, 2.55, -0.36, 0.36, 0.68, 0.71, 'steelD', ink=False, cull='t')
    for x in (-1.8, 0.0, 1.8):
        k.bx(x - 0.04, x + 0.04, -0.8, 0.8, 0.0, 0.06, 'steelD', ink=False)
        k.bx(x - 0.03, x + 0.03, -0.05, 0.05, 0.06, 0.68, 'steelD', ink=False)
        for s in (-1, 1):
            k.bx(x - 0.03, x + 0.03, s * 0.66 - 0.03, s * 0.66 + 0.03, 0.06, 0.42, 'steelD', ink=False)
    for s in (-1, 1):
        k.bx(-2.5, 2.5, s * 0.66 - 0.15, s * 0.66 + 0.15, 0.42, 0.46, 'chA')
    for i in range(2):
        x = -1.6 + i * 2.2 + rnd.uniform(-0.3, 0.3)
        s = (-1, 1)[i]
        k.bx(x, x + 0.42, -0.36 if s < 0 else 0.1, -0.1 if s < 0 else 0.36, 0.75, 0.77, rnd.choice(['chE', 'chB', 'mat']), ink=False)
        k.bx(x + 0.28, x + 0.36, (-0.3 if s < 0 else 0.16), (-0.22 if s < 0 else 0.24), 0.77, 0.89, 'paper')
    k.col(-2.6, 2.6, -0.4, 0.4, 0.0, 0.77)
    k.col(-2.5, 2.5, -0.81, -0.51, 0.0, 0.46)
    k.col(-2.5, 2.5, 0.51, 0.81, 0.0, 0.46)
    k.finish('CafTable', ao=ao)
    # vending machines (1 cell, front -Y): snacks behind glass, cold drinks; the fronts glow
    for v, (name, c, word) in enumerate((('Vend_A', 'chD', 'SNAKLY'), ('Vend_B', 'chA', 'FIZZBO'))):
        k.begin()
        g = AKit(k.pal, k.prefix, k.hull_t).begin()
        rnd = random.Random(30 + v)
        k.bx(-0.44, 0.44, -0.38, 0.4, 0.0, 1.85, c, cull='b')
        k.bx(-0.44, 0.44, -0.4, -0.38, 0.0, 0.12, 'black', ink=False)
        k.bx(0.2, 0.4, -0.41, -0.38, 0.95, 1.4, 'black', ink=False)
        k.bx(-0.36, 0.14, -0.41, -0.38, 0.16, 0.36, 'black', ink=False)
        if v == 0:
            for j in range(5):
                z = 0.6 + j * 0.24
                for i in range(4):
                    x = -0.36 + i * 0.13
                    g.fq(x, x + 0.1, -0.387, z, z + 0.15, rnd.choice(['foodY', 'chB', 'chC', 'chD', 'paper']))
            g.fq(-0.38, 0.16, -0.384, 0.5, 1.75, 'skyL')
        else:
            g.fq(-0.38, 0.16, -0.384, 0.5, 1.75, 'chA')
            for j in range(3):
                g.fq(-0.32, 0.1, -0.387, 0.75 + j * 0.35, 0.95 + j * 0.35, ['paper', 'chD', 'foodY'][j])
        g.fq(-0.4, 0.4, -0.384, 1.76, 1.82, 'lightW')
        g.fq(0.24, 0.36, -0.413, 1.3, 1.36, 'exitG')
        k.col(-0.44, 0.44, -0.41, 0.4, 0.0, 1.85)
        k.finish(name, ao=ao)
        g.finish(name + '_Glow')
    # tray return [3, 1] against a wall: a counter with the dish window, trash and recycling bins
    k.begin()
    k.bx(-1.45, 1.45, -0.35, 0.35, 0.0, 0.9, 'steel', cull='b')
    k.fq(-1.4, 1.4, -0.353, 0.1, 0.84, 'chrome')
    k.bx(-1.5, 1.5, -0.4, 0.35, 0.9, 0.94, 'chrome')
    k.bx(-0.9, 0.9, 0.0, 0.35, 0.94, 1.9, 'steelD', cull='')
    k.fq(-0.8, 0.8, -0.003, 1.0, 1.8, 'black')
    k.bx(-0.9, 0.9, -0.15, 0.35, 1.9, 2.0, 'steel')
    k.fq(-0.6, 0.6, -0.153, 1.92, 1.98, 'gold')
    for (x, c) in ((-1.2, 'steelD'), (1.2, 'chA')):
        k.cyl(x, -0.6, 0.0, 0.2, 0.22, 0.85, c, seg=10)
    k.col(-1.5, 1.5, -0.4, 0.35, 0.0, 1.0)
    k.col(-1.42, -0.98, -0.82, -0.38, 0.0, 0.85)
    k.col(0.98, 1.42, -0.82, -0.38, 0.0, 0.85)
    k.finish('TrayReturn', ao=ao)
    # milk cooler (1 cell): stainless chest with a glass lid
    k.begin()
    k.bx(-0.45, 0.45, -0.32, 0.32, 0.0, 0.9, 'chrome', cull='b')
    k.fq(-0.4, 0.4, -0.323, 0.1, 0.8, 'steel')
    k.fq(-0.3, 0.3, -0.326, 0.55, 0.7, 'paper')
    k.text('MILK', 0.0, -0.329, 0.58, 0.1, 'chA', font='display')
    k.uq(-0.4, 0.4, -0.27, 0.27, 0.903, 'glass')
    for i in range(4):
        k.uq(-0.36 + i * 0.19, -0.2 + i * 0.19, -0.2, 0.2, 0.906, ['paper', 'chA', 'paper', 'chD'][i])
    k.col(-0.45, 0.45, -0.32, 0.32, 0.0, 0.9)
    k.finish('MilkCooler', ao=ao)


# ================================================================ library (on the mezzanine deck)
def build_library(k, ao):
    # double-sided book stack [3, 1]
    k.begin()
    rnd = random.Random(41)
    # an open double-sided stack: end panels, a centre back, five boards; books on both faces
    for x0, x1 in ((-1.45, -1.4), (1.4, 1.45)):
        k.bx(x0, x1, -0.3, 0.3, 0.0, 1.75, 'wood', cull='b')
    k.bx(-1.39, 1.39, -0.02, 0.02, 0.0, 1.75, 'woodD', cull='b')
    for j in range(4):
        z0 = 0.0 if j == 0 else 0.04 + j * 0.42
        k.bx(-1.4, 1.4, -0.3, 0.3, z0, z0 + (0.08 if j == 0 else 0.04), 'wood', cull='b' if j == 0 else '')
    for j in range(4):
        z = 0.08 + j * 0.42
        k.book_row(rnd, -1.38, 1.38, -0.27, -0.02, z)
        k.book_row(rnd, -1.38, 1.38, 0.02, 0.27, z, face=1)
    k.bx(-1.48, 1.48, -0.33, 0.33, 1.75, 1.8, 'woodD')
    k.col(-1.48, 1.48, -0.33, 0.33, 0.0, 1.8)
    k.finish('Shelf', ao=ao)
    # reading table [2, 2]: four chairs, two green lamps
    k.begin()
    k.legs4(-0.75, 0.75, -0.45, 0.45, 0.72, 'woodD', t=0.06)
    desk_top(k, -0.8, 0.8, -0.5, 0.5, 0.76, 'wood', 'woodD')
    for x in (-0.4, 0.4):
        for s in (-1, 1):
            k.chair(x, s * 0.72, 0 if s < 0 else 180, 'chA')
    for x in (-0.45, 0.45):
        k.cyl(x, 0.0, 0.76, 0.06, 0.06, 0.02, 'gold', seg=6)
        k.cyl(x, 0.0, 0.78, 0.01, 0.01, 0.25, 'gold', seg=4, ink=False, caps=False)
        k.bx(x - 0.15, x + 0.15, -0.06, 0.06, 1.0, 1.08, 'leafD')
    k.bx(-0.2, 0.05, -0.2, 0.05, 0.76, 0.8, 'chD')
    k.col(-0.8, 0.8, -0.5, 0.5, 0.0, 0.8)
    for x in (-0.4, 0.4):
        for s in (-1, 1):
            k.col(x - 0.22, x + 0.22, s * 0.72 - 0.22, s * 0.72 + 0.22, 0.0, 0.5)
    k.finish('ReadTable', ao=ao)
    # circulation desk [4, 2]: the librarian's counter (front -Y), a return slot, a screen, a cart of returns
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.bx(-1.8, 1.8, -0.7, -0.3, 0.0, 1.05, 'wood', cull='b')
    k.fq(-1.75, 1.75, -0.703, 0.08, 0.98, 'woodL')
    k.fq(-1.2, 1.2, -0.706, 0.6, 0.85, 'slate')
    k.text('CHECKOUT', 0.0, -0.709, 0.65, 0.16, 'gold', font='display')
    k.bx(-1.85, 1.85, -0.78, -0.25, 1.05, 1.09, 'woodD')
    k.bx(-1.8, -1.4, -0.3, 0.7, 0.0, 1.05, 'wood', cull='b')
    k.bx(-1.4, 1.8, -0.3, 0.6, 0.72, 0.76, 'lam')
    monitor(k, g, 0.3, 0.0, 180, 0.46, 0.76)
    office_chair(k, 0.3, 0.75, 180)
    k.bx(0.9, 1.5, 0.1, 0.5, 0.76, 0.98, 'chB')
    k.col(-1.85, 1.85, -0.78, -0.25, 0.0, 1.09)
    k.col(-1.8, -1.4, -0.3, 0.7, 0.0, 1.05)
    k.col(-1.4, 1.8, -0.3, 0.6, 0.0, 0.98)
    k.finish('LibDesk', ao=ao)
    g.finish('LibDesk_Glow')


def build_rooms(k, ao):
    build_classroom(k, ao)
    build_art(k, ao)
    build_lab(k, ao)
    build_robotics(k, ao)
    build_office(k, ao)
    build_cafeteria(k, ao)
    build_library(k, ao)
