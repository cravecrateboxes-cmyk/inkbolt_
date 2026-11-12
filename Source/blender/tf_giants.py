"""kit-toyfactory showpiece workshop: the oversized toys built for a toy-fair parade (cover and landmarks) -- the
landmark wind-up robot ROBO-PAL MAX (9 m, on a display plinth), the giant rocking horse, the giant spinning top (its
plinth; the top itself spins: a conveyor-path item), giant building bricks (2 x 2 and 2 x 4, stacked), alphabet
blocks, a scaffold tower and giant paint pots (see tf_base.py for conventions)."""
import math
import random

from tf_base import *  # noqa: F401,F403
import tf_base as B


# ================================================================ the landmark: ROBO-PAL MAX [6, 6]
def build_robot(pal, ao):
    m = new(pal)
    g = new(pal)
    # display plinth (0.45 m) with a yellow edge and the name plaque at the front
    m.bx(-2.9, 2.9, -2.9, 2.9, 0.0, 0.45, 'brandB', cull='b')
    fq(m, -2.9, 2.9, -2.903, 0.33, 0.42, 'hazY')
    bq(m, -2.9, 2.9, 2.903, 0.33, 0.42, 'hazY')
    lq(m, -2.903, -2.9, 2.9, 0.33, 0.42, 'hazY')
    rq(m, 2.903, -2.9, 2.9, 0.33, 0.42, 'hazY')
    uq(m, -2.6, 2.6, -2.6, 2.6, 0.453, 'machB')
    m.bx(-1.3, 1.3, -3.05, -2.9, 0.06, 0.4, 'brass', cull='b')
    text_front(m, 'ROBO-PAL MAX', 0.2, -3.053, 0.0, 0.14, 'black', maxw=2.4)
    Z = 0.45
    c, trim = 'gB', 'chrome'
    # legs: square tin legs with a red knee band, big flat feet
    for sx in (-1, 1):
        x = sx * 0.75
        m.bx(x - 0.55, x + 0.55, -1.1, 0.7, Z, Z + 0.45, 'pBlack', cull='b')
        m.bx(x - 0.45, x + 0.45, -0.45, 0.45, Z + 0.45, Z + 3.2, trim)
        fq(m, x - 0.45, x + 0.45, -0.453, Z + 1.6, Z + 1.9, 'gA')
        for k in range(2):
            z = Z + 2.3 + k * 0.4
            fq(m, x - 0.45, x + 0.45, -0.453, z, z + 0.04, 'steel')
    # body: the tin torso with rivets, a chest dial panel, a hatch
    z0, z1 = Z + 3.2, Z + 6.2
    m.bx(-1.5, 1.5, -1.0, 1.0, z0, z1, c)
    m.bx(-1.55, 1.55, -1.05, 1.05, z0 - 0.15, z0 + 0.1, 'gA')
    m.bx(-1.55, 1.55, -1.05, 1.05, z1 - 0.1, z1 + 0.12, 'gA')
    fq(m, -1.0, 1.0, -1.003, z0 + 0.6, z1 - 0.5, 'pWhite')
    for k, col in enumerate(('gA', 'gC', 'gD', 'pOrange')):
        x = -0.68 + k * 0.45
        disc_pts = [(x + 0.16 * math.cos(a / 4 * math.pi), -1.006, z0 + 1.9 + 0.16 * math.sin(a / 4 * math.pi)) for a in range(8)]
        poly(m, disc_pts, col, (0, -1, 0))
    for k in range(5):
        fq(m, -0.8 + k * 0.34, -0.6 + k * 0.34, -1.006, z0 + 0.85, z0 + 1.35, 'navy')
    for k in range(6):
        fq(g, -0.84 + k * 0.3, -0.66 + k * 0.3, -1.009, z0 + 0.95 + (k % 3) * 0.1, z0 + 1.25, ['scrG', 'scrC', 'amber'][k % 3])
    text_front(m, 'TOPSY', 0.34, -1.006, 0.0, z1 - 0.42, 'brandR', maxw=1.6)
    # the wind-up key on the back
    m.cy((0, 1.0, z0 + 1.8), 0.12, 0.12, 0.6, 'brass', seg=8, rot=(-90, 0, 0))
    m.bx(-0.06, 0.06, 1.55, 1.7, z0 + 1.0, z0 + 2.6, 'brass')
    m.sp((0, 1.62, z0 + 2.75), 0.32, 'brass', seg=(8, 5), scale=(0.3, 1.0, 1.0))
    m.sp((0, 1.62, z0 + 0.85), 0.32, 'brass', seg=(8, 5), scale=(0.3, 1.0, 1.0))
    # arms: shoulder balls, tube arms bent forward, claw hands (one holding a giant brick)
    for sx in (-1, 1):
        x = sx * 1.85
        m.sp((x, 0.0, z1 - 0.45), 0.42, 'gA', seg=(8, 5))
        m.bx(x - 0.28, x + 0.28, -0.28, 0.28, z1 - 2.1, z1 - 0.45, trim)
        m.bx(x - 0.3, x + 0.3, -1.6, 0.3, z1 - 2.4, z1 - 1.8, trim)
        for k in range(3):
            fq(m, x - 0.28, x + 0.28, -0.283, z1 - 1.0 - k * 0.3, z1 - 0.96 - k * 0.3, 'steel')
        for sy in (-1, 1):
            m.bx(x - 0.32 + (0.44 if sy > 0 else 0.0), x - 0.12 + (0.44 if sy > 0 else 0.0), -2.1, -1.6, z1 - 2.5, z1 - 1.75, 'pBlack')
    stud_brick(m, 1.25, 2.45, -2.4, -1.65, z1 - 2.15, z1 - 1.55, 'gC', nx=2, ny=1, seg=10)
    # neck and head: a box head with a visor screen (glow), round ear dials, antenna with a ball
    m.bx(-0.4, 0.4, -0.4, 0.4, z1 + 0.12, z1 + 0.5, 'steel')
    h0, h1 = z1 + 0.5, z1 + 2.3
    m.bx(-1.15, 1.15, -0.95, 0.95, h0, h1, c)
    m.bx(-1.2, 1.2, -1.0, 1.0, h1 - 0.12, h1 + 0.04, 'gA')
    fq(m, -0.85, 0.85, -0.953, h0 + 0.6, h0 + 1.3, 'black')
    fq(g, -0.78, 0.78, -0.956, h0 + 0.7, h0 + 1.2, 'scrC')
    for k in range(6):
        fq(m, -0.6 + k * 0.24, -0.5 + k * 0.24, -0.953, h0 + 0.2, h0 + 0.42, trim)
    for sx in (-1, 1):
        m.cy((sx * 1.15, 0.0, h0 + 1.0), 0.32, 0.32, 0.18, 'gC', seg=8, rot=(0, 90 * sx, 0))
    m.cy((0, 0, h1 + 0.04), 0.05, 0.05, 0.9, trim, seg=6)
    m.sp((0, 0, h1 + 1.05), 0.2, 'red', seg=(8, 6))
    g.sp((0, 0, h1 + 1.05), 0.21, 'red', seg=(8, 6))
    make('Landmark_Robot', m, ao, cols=[
        cb(-2.9, -2.9, 0.0, 2.9, 2.9, 0.45), cb(-1.3, -3.05, 0.0, 1.3, -2.9, 0.4),
        cb(-1.3, -1.1, Z, -0.2, 0.7, Z + 0.45), cb(0.2, -1.1, Z, 1.3, 0.7, Z + 0.45),
        cb(-1.2, -0.48, Z + 0.45, -0.3, 0.48, Z + 3.2), cb(0.3, -0.48, Z + 0.45, 1.2, 0.48, Z + 3.2),
        cb(-1.55, -1.05, z0 - 0.15, 1.55, 1.05, z1 + 0.5), cb(-0.2, 1.05, z0 + 0.5, 0.2, 1.7, z0 + 3.1),
        cb(-2.15, -0.42, z1 - 2.1, -1.55, 0.42, z1), cb(1.55, -0.42, z1 - 2.1, 2.15, 0.42, z1),
        cb(-2.15, -2.1, z1 - 2.5, -1.55, -0.42, z1 - 1.75), cb(1.55, -2.1, z1 - 2.5, 2.15, -0.42, z1 - 1.75),
        cb(1.25, -2.4, z1 - 2.15, 2.45, -1.65, z1 - 1.55),
        cb(-1.2, -1.0, h0, 1.2, 1.0, h1 + 0.04)])
    make_glow('Landmark_Robot_LED', g)


# ================================================================ the giant rocking horse [6, 3] (along X, head at +X)
def build_horse(pal, ao):
    m = new(pal)
    # rockers: two curved runners (bow segments), a footboard between them
    R, n = 9.0, 10
    pts = []
    for i in range(n + 1):
        x = (-1.0 + 2.0 * i / n) * 2.85
        pts.append((x, R - math.sqrt(R * R - x * x)))
    prof = pts + [(x, z + 0.3) for (x, z) in reversed(pts)]
    swap = Matrix(((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))   # profile in (X, Z), extruded along Y
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.75, sy * 1.0))
        old = m.parent
        m.parent = old @ swap
        m.prism(prof, y0, y1, ['brandR'])
        m.parent = old
    for x in (-1.6, 0.0, 1.6):
        z = R - math.sqrt(R * R - x * x)
        m.bx(x - 0.2, x + 0.2, -0.75, 0.75, z + 0.08, z + 0.24, 'brass')
    # stand posts from the rockers to the belly
    for x in (-1.3, 1.3):
        for sy in (-1, 1):
            m.bx(x - 0.12, x + 0.12, sy * 0.62 - 0.12, sy * 0.62 + 0.12, 0.25, 1.75, 'pWhite')
    # body: a round-ended barrel, the saddle with a blanket, stirrups
    m.cy((-1.9, 0.0, 2.3), 0.72, 0.72, 3.6, 'pWhite', seg=10, rot=(0, 90, 0), caps=False)
    m.sp((-1.9, 0.0, 2.3), 0.72, 'pWhite', seg=(10, 5), scale=(0.6, 1.0, 1.0))
    m.sp((1.7, 0.0, 2.3), 0.72, 'pWhite', seg=(10, 5), scale=(0.6, 1.0, 1.0))
    # dapples (spots on the flanks)
    rnd = random.Random(611)
    for sy in (-1, 1):
        for k in range(4):
            x = -1.4 + k * 0.85 + rnd.uniform(-0.1, 0.1)
            z = 2.2 + rnd.uniform(-0.25, 0.25)
            pts = [(x + 0.13 * math.cos(a / 4 * math.pi), sy * 0.728, z + 0.13 * math.sin(a / 4 * math.pi)) for a in range(8)]
            poly(m, pts, 'gC' if k % 2 else 'pSky', (0, sy, 0))
    m.bx(-0.8, 0.5, -0.78, 0.78, 2.7, 3.08, 'gA')
    m.bx(-0.95, 0.65, -0.82, 0.82, 2.55, 2.72, 'gB')
    m.bx(-0.8, -0.5, -0.4, 0.4, 3.08, 3.3, 'gA')
    for sy in (-1, 1):
        m.bx(-0.2, -0.1, sy * 0.85 - 0.02, sy * 0.85 + 0.02, 1.6, 2.6, 'black', hull='none', cull='')
        m.bx(-0.3, 0.0, sy * 0.85 - 0.08, sy * 0.85 + 0.08, 1.5, 1.6, 'brass')
    # neck and head (blocky toy head), ears, the yarn mane, handle pegs, the bridle
    with at(m, 2.0, 0.0, 2.6, 0.0, ry=-35):
        m.bx(-0.35, 0.35, -0.42, 0.42, 0.0, 1.6, 'pWhite')
    m.bx(2.3, 3.4, -0.45, 0.45, 3.5, 4.2, 'pWhite')
    m.bx(3.0, 3.6, -0.4, 0.4, 3.35, 3.8, 'pWhite')
    fq(m, 3.0, 3.6, -0.403, 3.42, 3.55, 'pPink')
    bq(m, 3.0, 3.6, 0.403, 3.42, 3.55, 'pPink')
    for sy in (-1, 1):
        m.bx(2.45, 2.65, sy * 0.3 - 0.08, sy * 0.3 + 0.08, 4.2, 4.6, 'pWhite')
        m.cy((2.75, sy * 0.44, 3.85), 0.05, 0.05, 0.4, 'brass', seg=6, rot=(-90 * sy, 0, 0))
        m.sp((2.75, sy * 0.88, 3.85), 0.1, 'gA', seg=(6, 4))
    m.bx(3.2, 3.25, -0.42, 0.42, 3.4, 4.0, 'gB', hull='none', cull='')
    for k in range(5):
        x = 1.75 + k * 0.28
        z = 3.1 + k * 0.22
        w = 0.12 + 0.012 * (k % 2)
        m.bx(x - 0.12, x + 0.12, -w, w, z, z + 0.42, 'gC' if k % 2 else 'pOrange')
    # tail
    for k in range(3):
        w = 0.12 + 0.012 * (k % 2)
        m.bx(-2.75 - k * 0.12, -2.55 - k * 0.12, -w, w, 2.0 - k * 0.25, 2.5 - k * 0.2, 'gC' if k % 2 else 'pOrange')
    make('Horse', m, ao, cols=[cb(-2.85, -1.0, 0.0, 2.85, -0.72, 0.6), cb(-2.85, 0.72, 0.0, 2.85, 1.0, 0.6)] + [cb(x - 0.2, -0.75, 0.0, x + 0.2, 0.75, 0.4) for x in (-1.6, 0.0, 1.6)] + [cb(-2.3, -0.45, 1.6, 2.1, 0.45, 3.1), cb(-2.3, -0.72, 1.9, 2.1, 0.72, 2.75),
                               cb(-1.42, -0.74, 0.6, -1.18, -0.5, 1.55), cb(1.18, -0.74, 0.6, 1.42, -0.5, 1.55),
                               cb(-1.42, 0.5, 0.6, -1.18, 0.74, 1.55), cb(1.18, 0.5, 0.6, 1.42, 0.74, 1.55),
                               cb(1.7, -0.5, 3.0, 3.6, 0.5, 4.3), cb(-3.1, -0.15, 1.2, -2.5, 0.15, 2.5)])


# ================================================================ the giant spinning top: plinth [3, 3] + the top
def build_top(pal, ao):
    m = new(pal)
    m.cy((0, 0, 0), 1.45, 1.45, 0.16, 'machW', seg=20)
    ring(m, 0, 0, 0.163, 1.1, 1.38, 'brandR', seg=20)
    ring(m, 0, 0, 0.163, 0.5, 0.62, 'hazY', seg=16)
    m.bx(-0.7, 0.7, -1.6, -1.45, 0.02, 0.32, 'brass', cull='b')
    text_front(m, 'WHIRLY GIGA-TOP', 0.12, -1.603, 0.0, 0.11, 'black', maxw=1.3)
    make('TopBase', m, ao, cols=[cb(-1.45, -1.45, 0.0, 1.45, 1.45, 0.16), cb(-0.95, -0.95, 0.16, 0.95, 0.95, 2.5)])
    # the top (origin = its tip on the plinth; spins about Z): striped cone body, a rim, the handle knob
    m = new(pal)
    seg = 12
    m.cy((0, 0, 0.0), 0.06, 1.0, 0.8, 'gA', seg=seg)
    m.cy((0, 0, 0.8), 1.0, 1.05, 0.22, 'hazY', seg=seg)
    m.cy((0, 0, 1.02), 1.05, 0.6, 0.6, 'gB', seg=seg)
    m.cy((0, 0, 1.62), 0.6, 0.18, 0.3, 'pWhite', seg=seg)
    m.cy((0, 0, 1.92), 0.1, 0.1, 0.5, 'gD', seg=8)
    m.sp((0, 0, 2.45), 0.16, 'gA', seg=(8, 5))
    # painted swirl: coloured panels round the rim band
    for k in range(6):
        a0 = k * 2 * math.pi / 6
        a1 = a0 + math.pi / 6
        pts = [(math.cos(a0) * 1.055, math.sin(a0) * 1.055, 0.84), (math.cos(a1) * 1.055, math.sin(a1) * 1.055, 0.84),
               (math.cos(a1) * 1.055, math.sin(a1) * 1.055, 0.98), (math.cos(a0) * 1.055, math.sin(a0) * 1.055, 0.98)]
        poly(m, pts, ['gA', 'gB', 'gD', 'pPurple'][k % 4], ((math.cos(a0) + math.cos(a1)) / 2, (math.sin(a0) + math.sin(a1)) / 2, 0))
    make('Top_Spin', m, ao)


# ================================================================ giant bricks and blocks
def build_blocks(pal, ao):
    # giant bricks (the goods cell gA, repainted per copy): 2 x 2 (1.2 m), the same with a 2 x 2 stacked offset,
    # a 2 x 4 brick [4, 2], a 2 x 4 with a 2 x 2 on top
    m = new(pal)
    stud_brick(m, -0.98, 0.98, -0.98, 0.98, 0.0, 1.2, 'gA', nx=2, ny=2, seg=8, stud=0.32, sh=0.2)
    make('Brick_A', m, ao, cols=[cb(-0.98, -0.98, 0.0, 0.98, 0.98, 1.2)])
    m = new(pal)
    stud_brick(m, -1.98, 1.98, -0.98, 0.98, 0.0, 1.2, 'gA', nx=4, ny=2, seg=8, stud=0.32, sh=0.2)
    make('Brick_Long', m, ao, cols=[cb(-1.98, -0.98, 0.0, 1.98, 0.98, 1.2)])
    # alphabet blocks: 0.96 m wooden cubes, a coloured panel with a letter on each side; one, or two stacked (the
    # top one turned 20 degrees)
    LET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    def abc(m, z0, deg, k0, s=0.96):
        h = s / 2
        cols = ['gA', 'gB', 'gC', 'gD']
        with at(m, 0.0, 0.0, z0, deg):
            m.bx(-h, h, -h, h, 0.0, s, 'cream', cull='b' if z0 == 0 else '')
            for i, (f, nrm) in enumerate(((fq, -1), (bq, 1))):
                y = nrm * (h + 0.003)
                f(m, -h + 0.08, h - 0.08, y, 0.08, s - 0.08, cols[(k0 + i) % 4])
                (text_front if nrm < 0 else text_back)(m, LET[(k0 + i) % 8], 0.56, nrm * (h + 0.006), 0.0, 0.2, 'pWhite')
            lq(m, -h - 0.003, -h + 0.08, h - 0.08, 0.08, s - 0.08, cols[(k0 + 2) % 4])
            rq(m, h + 0.003, -h + 0.08, h - 0.08, 0.08, s - 0.08, cols[(k0 + 3) % 4])
            text_side(m, LET[(k0 + 2) % 8], 0.56, -h - 0.006, 0.0, 0.2, 'pWhite', 'x-')
            text_side(m, LET[(k0 + 3) % 8], 0.56, h + 0.006, 0.0, 0.2, 'pWhite', 'x+')
            uq(m, -h + 0.08, h - 0.08, -h + 0.08, h - 0.08, s + 0.003, cols[(k0 + 1) % 4])
    m = new(pal); abc(m, 0.0, 0.0, 0); make('ABC_1', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.96)])
    m = new(pal); abc(m, 0.0, 0.0, 4); abc(m, 0.96, 20.0, 2, s=0.8)
    make('ABC_2', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.96), cb(-0.48, -0.48, 0.96, 0.48, 0.48, 1.76)])
    # scaffold tower [2, 2]: two lifts of tube frames, plank decks, a ladder, toe boards
    m = new(pal)
    for (x, y) in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)):
        m.cy((x, y, 0.0), 0.03, 0.03, 4.0, 'steel', seg=5)
        m.bx(x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.0, 0.03, 'steelD', hull='none', cull='b')
    for z in (1.0, 2.0, 3.0, 4.0):
        for (a, b, dz) in (((-0.9, -0.9), (0.9, -0.9), 0.0), ((-0.9, 0.9), (0.9, 0.9), 0.0), ((-0.9, -0.9), (-0.9, 0.9), 0.09), ((0.9, -0.9), (0.9, 0.9), 0.09)):
            m.bm_((a[0], a[1], z - dz), (b[0], b[1], z - dz), 0.07, 'steel' if z % 2 else 'hazY')
    for z in (2.0, 4.0):
        m.bx(-0.88, 0.88, -0.88, 0.88, z + 0.03, z + 0.07, 'wood')
        for k in range(1, 4):
            y0 = -0.88 + k * 0.44
            uq(m, -0.88, 0.88, y0 - 0.008, y0 + 0.008, z + 0.073, 'woodD')
        m.bx(-0.88, 0.88, -0.92, -0.88, z + 0.07, z + 0.22, 'hazY', hull='none', cull='')
    m.bm_((0.9, -0.9, 0.5), (-0.9, -0.9, 1.9), 0.04, 'steel')
    m.bm_((0.9, 0.9, 2.5), (-0.9, 0.9, 3.9), 0.04, 'steel')
    for k in range(8):
        z = 0.3 + k * 0.45
        m.bx(-0.68, -0.42, 0.925, 0.945, z, z + 0.04, 'steelD', hull='none', cull='')
    for x in (-0.7, -0.4):
        m.bx(x - 0.02, x + 0.02, 0.915, 0.955, 0.0, 4.2, 'steelD', hull='none', cull='')
    make('Scaffold', m, ao, cols=[cb(-0.93, -0.93, 0.0, -0.87, -0.87, 4.0), cb(0.87, -0.93, 0.0, 0.93, -0.87, 4.0), cb(-0.93, 0.87, 0.0, -0.87, 0.93, 4.0),
                                  cb(0.87, 0.87, 0.0, 0.93, 0.93, 4.0), cb(-0.9, -0.9, 1.95, 0.9, 0.9, 2.07), cb(-0.9, -0.9, 3.95, 0.9, 0.9, 4.07),
                                  cb(-0.92, -0.92, 0.0, 0.92, -0.86, 1.05)])
    # giant paint pots: a 1.1 m tin with a drip down its side and a lid leaning on it, a brush
    m = new(pal)
    m.cy((0, 0, 0), 0.45, 0.45, 1.05, 'chrome', seg=10)
    m.cy((0, 0, 1.05), 0.47, 0.47, 0.05, 'steelD', seg=10)
    disc(m, 0, 0, 1.103, 0.42, 'gA', seg=10)
    m.cy((0, 0, 0.35), 0.453, 0.453, 0.45, 'gA', seg=10, caps=False, hull='none')
    for k in range(3):
        a = -1.9 + k * 0.4
        x, y = math.cos(a) * 0.455, math.sin(a) * 0.455
        m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.55 - k * 0.12, 1.06, 'gA', hull='none', cull='')
    with at(m, 0.0, -0.0, 0.0, 0.0):
        m.bm_((0.15, 0.05, 1.1), (0.55, 0.3, 2.0), 0.08, 'woodD')
        m.bx(0.05, 0.25, -0.05, 0.15, 0.95, 1.12, 'gA')
    make('PaintPot', m, ao, cols=[cb(-0.47, -0.47, 0.0, 0.47, 0.47, 1.1)])


def build_giants(pal, ao):
    build_robot(pal, ao)
    build_horse(pal, ao)
    build_top(pal, ao)
    build_blocks(pal, ao)
