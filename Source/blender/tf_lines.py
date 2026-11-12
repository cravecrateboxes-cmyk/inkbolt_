"""kit-toyfactory production floor: the assembly-line belts (a 1 m belt section along Blender X, feed / exit hoods,
cleats), the packing roller line, the toys and cartons that ride them, robot arms and benches along the lines, tote
racks, injection moulding machines, the pellet loft (dryers, pellet gaylords, sacks, the overhead feed pipes), paint
booths and drying racks, the three packaging machines (case packer, shrink tunnel, labeller), pack benches, andon
lights, parts carts, the plush stuffing machine, QC benches, finished-goods pallets, a stretch wrapper and a pallet
jack (see tf_base.py for conventions; belt items ride with their base on the belt top, B.BELT)."""
import math
import random

from tf_base import *  # noqa: F401,F403
import tf_base as B

BT = B.BELT


# ================================================================ belts
def belt_frame(m, x0=-0.5, x1=0.5, legs=True):
    """belt section between x0 and x1: blue side frames with a yellow edge strip, legs, the rubber belt (top at BT)"""
    for s in (-1, 1):
        a, b = sorted((s * 0.4, s * 0.48))
        m.bx(x0, x1, a, b, 0.66, 0.98, 'machB', hull='noside', cull='lr')
        (fq if s < 0 else bq)(m, x0, x1, s * 0.483, 0.9, 0.94, 'hazY')
    if legs:
        for s in (-1, 1):
            a, b = sorted((s * 0.34, s * 0.42))
            m.bx(-0.04, 0.04, a, b, 0.0, 0.66, 'steelD', hull='none', cull='bt')
    uq(m, x0, x1, -0.4, 0.4, BT, 'rubber')


def build_belts(pal, ao):
    m = new(pal); belt_frame(m)
    make('Belt', m, ao, cols=[cb(-0.5, -0.48, 0.0, 0.5, 0.48, 0.98)])
    # end hoods (local +X = downstream): a tunnel over the belt with a strip curtain on the open mouth, the drive motor
    # on the closed end (Feed: closed upstream; Exit: closed downstream), a photo-eye and a little lamp
    for kind in ('Feed', 'Exit'):
        m = new(pal)
        sx = -1 if kind == 'Feed' else 1
        L, W, Hh = 0.5, 0.5, 1.9
        z0 = 0.984
        for s in (-1, 1):
            y0, y1 = sorted((s * (W - 0.06), s * W))
            m.bx(-L, L, y0, y1, z0, Hh, 'machW', cull='b')
            for k in range(2):
                xa = -L + 0.14 + k * 0.5
                (fq if s < 0 else bq)(m, xa, xa + 0.16, s * (W + 0.003), 1.05, 1.2, 'hazY')
        m.bx(-L - 0.02, L + 0.02, -W - 0.03, W + 0.03, Hh, Hh + 0.08, 'machB')
        x0, x1 = sorted((sx * (L - 0.066), sx * (L - 0.006)))
        m.bx(x0, x1, -W + 0.06, W - 0.06, z0, Hh, 'machW', cull='b')
        m.bx(*sorted((sx * L, sx * (L + 0.14))), -0.22, 0.22, 0.56, 1.3, 'steelD')
        xm = -sx * (L - 0.04)
        for i in range(4):
            y = -W + 0.1 + (2 * W - 0.2) * (i + 0.5) / 4
            m.bx(xm - 0.008 - 0.004 * (i % 2), xm + 0.008 - 0.004 * (i % 2), y - 0.075, y + 0.075, BT + 0.06, Hh - 0.004, 'rubber', hull='none', cull='')
        fq(m, -0.22, 0.22, -W - 0.006, Hh - 0.42, Hh - 0.12, 'pWhite')
        text_front(m, 'IN' if kind == 'Feed' else 'OUT', 0.14, -W - 0.009, 0.0, Hh - 0.36, 'brandB')
        m.cy((0.0, 0.0, Hh + 0.08), 0.05, 0.05, 0.12, 'gD' if kind == 'Feed' else 'gA', seg=6)
        make('Belt_' + kind, m, ao, cols=[cb(-L, -W, 0.0, L, W, Hh + 0.08)])
    m = new(pal)
    m.bx(-0.025, 0.025, -0.38, 0.38, 0.0, 0.012, 'steel', hull='none', cull='b')
    make('Belt_Cleat', m, ao)
    # packing / sortation roller line (cartons): a 1 m section of chrome rollers (tops at the belt height) in yellow
    # side frames on legs
    m = new(pal)
    for s in (-1, 1):
        a, b = sorted((s * 0.38, s * 0.44))
        m.bx(-0.5, 0.5, a, b, 0.66, 0.98, 'hazY', hull='noside', cull='')
        a, b = sorted((s * 0.32, s * 0.38))
        m.bx(-0.03, 0.03, a, b, 0.0, 0.66, 'steelD', hull='none', cull='bt')
    m.bx(-0.03, 0.03, -0.32, 0.32, 0.2, 0.26, 'steelD', hull='none', cull='')
    for k in range(3):
        x = -0.333 + k * 0.333
        m.cy((x, -0.38, BT - 0.035), 0.035, 0.035, 0.76, 'chrome', seg=6, rot=(-90, 0, 0), caps=False, hull='none')
    m.bx(-0.5, 0.5, -0.38, 0.38, 0.74, 0.75, 'steelD', hull='none', cull='t')
    make('Rollers', m, ao, cols=[cb(-0.5, -0.44, 0.0, 0.5, 0.44, 0.98)])


# ================================================================ items riding the lines (origin = the belt top)
def build_items(pal, ao):
    """toys and cartons riding the lines -- light models (an instance draws its whole line's atlas)"""
    m = new(pal)   # a set of bricks: a 2x4 with a 2x2 on it (studs without outline)
    m.bx(-0.22, 0.22, -0.11, 0.11, 0.0, 0.14, 'gA', cull='b')
    m.bx(-0.2, 0.02, -0.1, 0.1, 0.14, 0.26, 'gB', cull='b')
    for k in range(2):
        m.cy((-0.15 + k * 0.11, 0.0, 0.26), 0.035, 0.035, 0.03, 'gB', seg=6, hull='none')
    for k in range(2):
        m.cy((0.08 + k * 0.1, 0.0, 0.14), 0.035, 0.035, 0.03, 'gA', seg=6, hull='none')
    make_item('Toy_Bricks', m, ao)
    m = new(pal)   # alphabet blocks: two wooden cubes with painted letters
    for (x, y, z, s, c, ch) in ((-0.12, 0.0, 0.0, 0.2, 'gA', 'A'), (0.13, 0.03, 0.0, 0.2, 'gB', 'B')):
        m.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z, z + s, 'cream', cull='b')
        fq(m, x - s * 0.4, x + s * 0.4, y - s / 2 - 0.003, z + s * 0.1, z + s * 0.9, c)
        text_front(m, ch, s * 0.6, y - s / 2 - 0.006, x, z + s * 0.2, 'pWhite')
    make_item('Toy_ABC', m, ao)
    m = new(pal)   # a rubber duck
    duck(m, 0.0, 0.0, 0.0, 0.34, deg=0)
    make_item('Toy_Duck', m, ao)
    m = new(pal)   # a wind-up robot (body and head outlined; limbs plain)
    with at(m, 0.0, 0.0, 0.0, 0.0, s=0.42):
        for sx in (-1, 1):
            m.bx(sx * 0.1 - 0.08, sx * 0.1 + 0.08, -0.12, 0.12, 0.0, 0.35, 'chrome', hull='none', cull='b')
            m.bx(sx * 0.3 - 0.06, sx * 0.3 + 0.06, -0.08, 0.08, 0.4, 0.75, 'chrome', hull='none')
        m.bx(-0.24, 0.24, -0.16, 0.16, 0.35, 0.85, 'gB')
        fq(m, -0.15, 0.15, -0.17, 0.5, 0.72, 'pWhite')
        m.bx(-0.17, 0.17, -0.14, 0.14, 0.88, 1.18, 'gB')
        fq(m, -0.12, 0.12, -0.15, 0.98, 1.06, 'black')
        m.bx(-0.12, 0.12, 0.25, 0.28, 0.54, 0.66, 'brass', hull='none', cull='')
    make_item('Toy_Robot', m, ao)
    m = new(pal); bear(m, 0.0, 0.0, 0.0, 0.38); make_item('Toy_Bear', m, ao)
    # cartons on the packing and sortation lines (printed toy boxes)
    for v, (c, art) in enumerate((('gA', 'gC'), ('gB', 'gC'), ('gD', 'gB'))):
        m = new(pal)
        carton(m, -0.26, 0.26, -0.2, 0.2, 0.0, 0.34, c, art=art)
        bq(m, -0.18, 0.18, 0.203, 0.08, 0.26, 'pWhite')
        make_item('Box_' + 'ABC'[v], m, ao)


# ================================================================ along the lines
def robot_arm(m, kind, reach=1.0):
    """an industrial robot arm on a pedestal, reaching toward -Y over the belt (gripper or nut runner)"""
    m.bx(-0.3, 0.3, -0.3, 0.3, 0.0, 0.7, 'machW', cull='b')
    fq(m, -0.2, 0.2, -0.303, 0.3, 0.42, 'hazY')
    m.cy((0, 0, 0.7), 0.24, 0.22, 0.2, 'pOrange', seg=8)
    # shoulder, upper arm up and over, elbow, forearm down toward the belt
    sh = Vector((0.0, 0.05, 1.0))
    el = Vector((0.0, -0.35, 2.15))
    wr = Vector((0.0, -reach, 1.98))
    m.bx(-0.18, 0.18, -0.12, 0.2, 0.9, 1.15, 'pOrange')
    m.bm_(tuple(sh), tuple(el), 0.18, 'pOrange')
    m.cy(tuple(el + Vector((-0.13, 0, 0))), 0.13, 0.13, 0.26, 'steelD', seg=6, rot=(0, 90, 0))
    m.bm_(tuple(el), tuple(wr), 0.13, 'pOrange')
    m.cy(tuple(sh + Vector((-0.2, 0, 0))), 0.15, 0.15, 0.4, 'steelD', seg=6, rot=(0, 90, 0))
    m.cy(tuple(wr + Vector((0, 0, -0.18))), 0.07, 0.07, 0.18, 'steelD', seg=6, hull='none')
    if kind == 'grip':
        m.bx(wr.x - 0.12, wr.x + 0.12, wr.y - 0.05, wr.y + 0.05, wr.z - 0.26, wr.z - 0.18, 'steel')
        for sx in (-1, 1):
            m.bx(wr.x + sx * 0.1 - 0.02, wr.x + sx * 0.1 + 0.02, wr.y - 0.04, wr.y + 0.04, wr.z - 0.45, wr.z - 0.26, 'chrome', hull='none', cull='')
    else:
        m.cy(tuple(wr + Vector((0, 0, -0.42))), 0.05, 0.03, 0.24, 'chrome', seg=6)
        m.cy(tuple(wr + Vector((0.12, 0, -0.18))), 0.02, 0.02, 0.3, 'black', seg=5, hull='none')


def build_line_props(pal, ao):
    for kind, name in (('grip', 'Arm'),):
        m = new(pal); robot_arm(m, kind)
        make(name, m, ao, cols=[cb(-0.36, -0.36, 0.0, 0.36, 0.36, 1.2)])
    # assembly bench [2, 1] (front -Y toward the belt): worktop, a parts-bin shelf over the back, a tool balancer,
    # a tablet screen (glow), a fixture with a half-built toy
    for v in range(1):
        rnd = random.Random(200 + v)
        m = new(pal)
        g = new(pal)
        m.bx(-0.95, 0.95, -0.4, 0.4, 0.86, 0.92, 'machW')
        for (x, y) in ((-0.88, -0.33), (0.88, -0.33), (-0.88, 0.33), (0.88, 0.33)):
            m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.86, 'steelD', hull='none', cull='bt')
        m.bx(-0.85, 0.85, -0.32, 0.32, 0.2, 0.23, 'steelD', hull='none', cull='')
        for sx in (-1, 1):
            m.bx(sx * 0.92 - 0.03, sx * 0.92 + 0.03, 0.3, 0.36, 0.92, 2.1, 'steelD', cull='')
        m.bx(-0.89, 0.89, 0.305, 0.355, 2.04, 2.09, 'steelD', cull='')
        for z in (1.5,):
            m.bx(-0.89, 0.89, 0.06, 0.3, z - 0.03, z, 'steel', hull='none', cull='')
            for k in range(4):
                x0 = -0.86 + k * 0.43
                c = rnd.choice(['gB', 'gA', 'gC', 'gD', 'pOrange'])
                m.bx(x0 + 0.01, x0 + 0.41, 0.08, 0.29, z, z + 0.2, c, cull='bk', hull='none')
        m.cy((0.5 if v else -0.5, 0.15, 2.1), 0.012, 0.012, 0.6, 'black', seg=4, hull='none', rot=(180, 0, 0))
        # tablet on an arm, a fixture with a toy, a bin of screws
        m.bx(0.45, 0.85, 0.16, 0.2, 1.0, 1.24, 'pBlack')
        fq(g, 0.47, 0.83, 0.157, 1.02, 1.22, rnd.choice(['scrB', 'scrG']))
        m.bx(-0.3, 0.1, -0.2, 0.15, 0.92, 1.0, 'steel')
        m.bx(-0.24, 0.04, -0.12, 0.08, 1.0, 1.22, 'gB')
        fq(m, -0.18, -0.02, -0.123, 1.06, 1.16, 'pWhite')
        m.bx(-0.18, -0.02, -0.1, 0.06, 1.22, 1.34, 'gB', hull='none')
        make('Bench_' + 'AB'[v], m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.4, 0.92), cb(-0.95, 0.04, 0.92, 0.95, 0.4, 2.1)])
        make_glow('Bench_' + 'AB'[v] + '_LED', g)
    # flow rack of parts totes [2, 1] (1.9 m): three sloped levels of coloured totes
    m = new(pal)
    rnd = random.Random(210)
    for sx in (-1, 1):
        for y in (-0.36, 0.36):
            m.bx(sx * 0.92 - 0.03, sx * 0.92 + 0.03, y - 0.03, y + 0.03, 0.0, 1.9, 'hazY', hull='full', cull='b')
    for k, z in enumerate((0.3, 0.85, 1.4)):
        m.bx(-0.92, 0.92, -0.38, 0.38, z - 0.04, z, 'steel', cull='')
        for j in range(4):
            x0 = -0.88 + j * 0.44
            c = rnd.choice(['gB', 'gA', 'gC', 'gD', 'pOrange', 'pTeal'])
            m.bx(x0 + 0.01, x0 + 0.42, -0.36, 0.36, z, z + 0.26, c, cull='b', hull='none')
            fq(m, x0 + 0.1, x0 + 0.32, -0.363, z + 0.08, z + 0.17, 'paper')
            uq(m, x0 + 0.04, x0 + 0.39, -0.32, 0.32, z + 0.2, rnd.choice(['pWhite', 'gC', 'pPink', 'steel']))
    make('Totes', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.4, 1.9)])
    # andon tower: a stack light on a post with a line counter (the lamps glow)
    m = new(pal)
    g = new(pal)
    m.bx(-0.2, 0.2, -0.2, 0.2, 0.0, 0.06, 'steelD', cull='b')
    m.cy((0, 0, 0.06), 0.04, 0.04, 2.26, 'steel', seg=6)
    m.bx(-0.3, 0.3, -0.1, 0.06, 1.5, 1.9, 'pBlack')
    fq(g, -0.26, 0.26, -0.103, 1.54, 1.86, 'screen')
    text_front(g, '1284', 0.2, -0.106, 0.0, 1.6, 'scrG', font='cond', maxw=0.46)
    for k, c in enumerate(('red', 'amber', 'exitG')):
        z = 2.36 + k * 0.16
        m.cy((0, 0, z), 0.08, 0.08, 0.14, 'chrome', seg=6)
        g.cy((0, 0, z + 0.01), 0.083, 0.083, 0.12, c, seg=6, caps=False)
    make('Andon', m, ao, cols=[cb(-0.2, -0.2, 0.0, 0.2, 0.2, 2.9)])
    make_glow('Andon_LED', g)
    # parts cart: a two-deck trolley of totes, a handle
    for v in range(1):
        rnd = random.Random(220 + v)
        m = new(pal)
        for (x, y) in ((-0.38, -0.3), (0.38, -0.3), (-0.38, 0.3), (0.38, 0.3)):
            m.cy((x, y, 0.0), 0.06, 0.06, 0.08, 'black', seg=6)
            m.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.08, 1.0, 'steel', hull='none', cull='bt')
        for z in (0.2, 0.62):
            m.bx(-0.42, 0.42, -0.34, 0.34, z, z + 0.03, 'machB', cull='')
            for j in range(2):
                x0 = -0.4 + j * 0.41
                m.bx(x0 + 0.01, x0 + 0.38, -0.3, 0.3, z + 0.03, z + 0.27, rnd.choice(['gA', 'gB', 'gC', 'gD']), cull='b', hull='none')
                uq(m, x0 + 0.04, x0 + 0.35, -0.26, 0.26, z + 0.22, rnd.choice(['pWhite', 'pPink', 'gC', 'pBrown']))
        m.bm_((-0.42, 0.34, 1.0), (0.42, 0.34, 1.0), 0.04, 'hazY')
        if v:
            bear(m, 0.0, 0.0, 1.0, 0.3, c='pPink')
        make('Cart_' + 'AB'[v], m, ao, cols=[cb(-0.44, -0.36, 0.0, 0.44, 0.36, 1.02)])
    # a stack of empty totes
    m = new(pal)
    for k in range(5):
        z = k * 0.22
        m.bx(-0.3, 0.3, -0.22, 0.22, z, z + 0.22, 'gB' if k % 2 else 'machB', cull='b' if k == 0 else '')
        fq(m, -0.1, 0.1, -0.223, z + 0.08, z + 0.14, 'black')
    make('ToteStack', m, ao, cols=[cb(-0.3, -0.22, 0.0, 0.3, 0.22, 1.1)])


# ================================================================ moulding: machines, pellets, the loft
def build_moulding(pal, ao):
    """[5, 2] injection moulding machine along X (front -Y = the operator side): base frame, the clamp unit (-X end:
    platens, tie bars, the sliding guard with windows) dropping parts down a chute into a bin, the injection unit (+X:
    barrel with heater bands, hopper with a vacuum loader, its pellet pipe rising to the overhead pipe run at 4.2 m),
    the control pendant with a screen (glow), warning stripes. Two colourways."""
    for v, body in enumerate(('machB',)):
        rnd = random.Random(300 + v)
        m = new(pal)
        g = new(pal)
        m.bx(-2.45, 2.2, -0.75, 0.75, 0.0, 0.9, body, cull='b')
        fq(m, -2.45, 2.2, -0.753, 0.0, 0.1, 'black')
        for k in range(5):
            x0 = -2.4 + k * 0.9
            fq(m, x0, x0 + 0.45, -0.753, 0.12, 0.2, 'hazY')
        # clamp unit guard: a machine-white housing with two windows, platens visible through them
        m.bx(-2.4, -0.2, -0.7, 0.7, 0.9, 2.25, 'machW')
        for x0 in (-2.2, -1.2):
            fq(m, x0, x0 + 0.85, -0.703, 1.15, 2.0, 'glass')
            fq(m, x0 + 0.08, x0 + 0.2, -0.706, 1.2, 1.95, 'glassL')
        m.bx(-2.4, -0.2, -0.72, 0.72, 2.25, 2.35, body)
        # tie-bar ends poking out of the platen at -X, the part chute and bin at the -X end
        for (y, z) in ((-0.45, 1.2), (0.45, 2.0)):
            m.cy((-2.4, y, z), 0.06, 0.06, 0.12, 'chrome', seg=6, rot=(0, -90, 0), hull='none')
        m.bx(-2.5, -2.05, -0.95, -0.74, 0.55, 0.86, 'steel', cull='')
        # injection unit: barrel with heater bands, nozzle shroud, motor housing, hopper and loader
        m.bx(-0.2, 2.2, -0.45, 0.45, 0.9, 1.2, 'steelD', cull='b')
        m.cy((-0.2, 0.0, 1.55), 0.22, 0.22, 2.0, 'chrome', seg=8, rot=(0, 90, 0))
        for k in range(3):
            m.cy((0.05 + k * 0.5, 0.0, 1.55), 0.25, 0.25, 0.2, 'red', seg=8, rot=(0, 90, 0), caps=False)
        m.bx(1.7, 2.3, -0.5, 0.5, 1.2, 2.0, body)
        fq(m, 1.75, 2.25, -0.503, 1.6, 1.9, 'hazY')
        text_front(m, '220T', 0.14, -0.506, 2.0, 1.66, 'black', font='cond', maxw=0.4)
        m.cy((1.2, 0.0, 1.75), 0.07, 0.07, 0.25, 'steel', seg=6)
        m.cy((1.2, 0.0, 2.0), 0.18, 0.34, 0.5, 'machW', seg=10)
        m.cy((1.2, 0.0, 2.5), 0.34, 0.3, 0.32, 'chrome', seg=10)
        m.cy((1.2, 0.0, 2.82), 0.3, 0.12, 0.14, 'steelD', seg=10)
        tube(m, (1.2, 0.0, 2.96), (1.2, 0.0, 4.2), 0.06, 'steel', seg=6)
        tube(m, (1.2, 0.07, 4.2), (1.2, 0.5, 4.2), 0.06, 'steel', seg=6)
        # control pendant on a swing arm at the front of the clamp guard, its screen glows
        m.bm_((-0.25, -0.72, 2.0), (-0.25, -1.0, 2.0), 0.05, 'steelD')
        m.bx(-0.5, 0.0, -1.08, -0.98, 1.5, 2.1, 'pBlack')
        fq(g, -0.46, -0.04, -1.083, 1.75, 2.06, rnd.choice(['scrB', 'scrC']))
        for k in range(4):
            fq(m, -0.44 + k * 0.1, -0.38 + k * 0.1, -1.083, 1.56, 1.62, ['gD', 'red', 'hazY', 'pWhite'][k])
        # the bin of fresh mouldings under the chute, cooling fan stub, oil cooler pipes at the back
        m.bx(-2.5, -1.6, -1.45, -0.75, 0.0, 0.55, 'gB' if v == 0 else 'gA', cull='b')
        uq(m, -2.46, -1.64, -1.41, -0.79, 0.5, rnd.choice(['gC', 'pPink', 'gD']))
        for k in range(3):
            x = -2.4 + k * 0.26
            m.bx(x, x + 0.08, -1.3 + (k % 3) * 0.12, -1.22 + (k % 3) * 0.12, 0.5, 0.58, rnd.choice(['gC', 'gA', 'pWhite']), hull='none', cull='b')
        tube(m, (-1.5, 0.76, 0.45), (1.5, 0.76, 0.45), 0.04, 'steelD', seg=5, hull='none')
        make('Mould', m, ao, cols=[cb(-2.45, -0.75, 0.0, 2.3, 0.75, 2.35), cb(1.0, -0.36, 2.35, 1.4, 0.36, 3.0),
                                            cb(-2.5, -1.45, 0.0, -1.6, -0.75, 0.58), cb(-0.5, -1.08, 1.5, 0.0, -0.75, 2.1)])
        make_glow('Mould_LED', g)
    # a gaylord of moulded parts: a cardboard bin, a heap of coloured parts in it
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    m.bx(-0.46, 0.46, -0.46, 0.46, 0.14, 1.0, 'cardD', cull='bt')
    fq(m, -0.44, 0.44, 0.44, 0.8, 1.0, 'card')
    bq(m, -0.44, 0.44, -0.44, 0.8, 1.0, 'cardL')
    rq(m, -0.44, -0.44, 0.44, 0.8, 1.0, 'card')
    lq(m, 0.44, -0.44, 0.44, 0.8, 1.0, 'cardL')
    uq(m, -0.44, 0.44, -0.44, 0.44, 0.84, 'gA')
    rnd = random.Random(320)
    for k in range(3):
        x, y = rnd.uniform(-0.34, 0.3), rnd.uniform(-0.34, 0.3)
        stud_brick(m, x, x + 0.12, y, y + 0.08, 0.84 + k * 0.005, 0.9 + k * 0.005, rnd.choice(['gA', 'gB', 'gC']), nx=2, ny=1, seg=5, hull='none')
    fq(m, -0.3, 0.3, -0.463, 0.5, 0.75, 'paper')
    text_front(m, 'PARTS 2X4', 0.07, -0.466, 0.0, 0.58, 'black', font='cond', maxw=0.5)
    make('Gay_Parts', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 1.0)])
    # a gaylord of pellets (the surface in the pellet colour, goods cell gA: repainted)
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    m.bx(-0.46, 0.46, -0.46, 0.46, 0.14, 1.1, 'card', cull='bt')
    for (f, y) in ((fq, 0.44), (bq, -0.44)):
        f(m, -0.44, 0.44, y, 0.95, 1.1, 'cardL')
    rq(m, -0.44, -0.44, 0.44, 0.95, 1.1, 'cardL')
    lq(m, 0.44, -0.44, 0.44, 0.95, 1.1, 'cardL')
    m.sp((0, 0, 0.95), 0.43, 'gA', seg=(8, 3), scale=(1.0, 1.0, 0.22), hull='none')
    # the pellet colour on a label each side, the supplier's blue band
    fq(m, -0.3, 0.3, -0.463, 0.5, 0.86, 'pWhite')
    fq(m, -0.2, 0.2, -0.466, 0.56, 0.8, 'gA')
    bq(m, -0.3, 0.3, 0.463, 0.5, 0.86, 'gA')
    lq(m, -0.463, -0.3, 0.3, 0.5, 0.86, 'gA')
    rq(m, 0.463, -0.3, 0.3, 0.5, 0.86, 'pWhite')
    for (f, v) in ((fq, -0.463), (bq, 0.463)):
        f(m, -0.46, 0.46, v, 0.25, 0.33, 'brandB')
    make('Pellets', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 1.1)])
    # a pallet of 25 kg pellet sacks, four courses in a brick bond
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    for k in range(4):
        z = 0.14 + k * 0.15
        if k % 2 == 0:
            for (a, b) in ((-0.46, -0.01), (0.01, 0.46)):
                m.bx(a, b, -0.46, 0.46, z, z + 0.145, 'pWhite', cull='b')
                fq(m, a + 0.06, b - 0.06, -0.463, z + 0.03, z + 0.11, 'gA')
                bq(m, a + 0.06, b - 0.06, 0.463, z + 0.03, z + 0.11, 'gA')
        else:
            for (c0, c1) in ((-0.46, -0.01), (0.01, 0.46)):
                m.bx(-0.46, 0.46, c0, c1, z, z + 0.145, 'pWhite', cull='b')
                lq(m, -0.463, c0 + 0.06, c1 - 0.06, z + 0.03, z + 0.11, 'gA')
                rq(m, 0.463, c0 + 0.06, c1 - 0.06, z + 0.03, z + 0.11, 'gA')
            fq(m, -0.3, 0.3, -0.463, z + 0.03, z + 0.11, 'gB')
    make('Sacks', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.74)])
    # pellet dryer / blender [2, 2] on the loft: a frame with a tall drying hopper, a gravimetric blender over a
    # side hopper, the dryer cabinet with a screen (glow), pipes
    m = new(pal)
    g = new(pal)
    for (x, y) in ((-0.8, -0.8), (0.1, -0.8), (-0.8, 0.1), (0.1, 0.1)):
        m.bx(x, x + 0.08, y, y + 0.08, 0.0, 1.1, 'steelD', hull='none', cull='bt')
    m.bx(-0.85, 0.23, -0.85, 0.23, 1.1, 1.18, 'steelD')
    m.cy((-0.31, -0.31, 1.18), 0.12, 0.42, 0.45, 'chrome', seg=8)
    m.cy((-0.31, -0.31, 1.63), 0.42, 0.42, 1.2, 'chrome', seg=8)
    m.cy((-0.31, -0.31, 2.83), 0.42, 0.16, 0.25, 'steel', seg=8)
    for z in (1.9, 2.5):
        m.cy((-0.31, -0.31, z), 0.425, 0.425, 0.05, 'machB', seg=8, caps=False, hull='none')
    m.bx(0.35, 0.9, -0.8, 0.85, 0.0, 1.5, 'machB', cull='b')
    fq(m, 0.4, 0.85, -0.803, 0.2, 1.3, 'machW')
    m.bx(0.45, 0.8, -0.86, -0.803, 1.0, 1.3, 'pBlack')
    fq(g, 0.47, 0.78, -0.863, 1.02, 1.28, 'scrC')
    m.cy((0.6, 0.4, 1.5), 0.22, 0.22, 0.6, 'chrome', seg=10)
    m.cy((0.6, 0.4, 2.1), 0.22, 0.08, 0.2, 'steel', seg=10)
    tube(m, (-0.31, -0.31, 3.08), (-0.31, 0.6, 3.6), 0.05, 'steel', seg=6)
    tube(m, (0.6, 0.4, 2.3), (0.6, 0.4, 3.0), 0.05, 'steel', seg=6)
    fq(m, -0.6, 0.0, -0.733, 2.1, 2.4, 'hazY')
    text_front(m, 'DRYER', 0.14, -0.736, -0.31, 2.18, 'black', maxw=0.5)
    make('Dryer', m, ao, cols=[cb(-0.85, -0.85, 0.0, 0.25, 0.25, 3.1), cb(0.35, -0.86, 0.0, 0.9, 0.85, 1.5), cb(0.38, 0.18, 1.5, 0.82, 0.62, 2.3)])
    make_glow('Dryer_LED', g)
    # overhead pellet feed pipes (1 m along X, hung from the run layer at 4.2 m: three pipes on a hanger)
    m = new(pal)
    for k, c in enumerate(('chrome', 'steel')):
        y = -0.12 + k * 0.24
        m.cy((-0.5, y, 0.0), 0.06, 0.06, 1.0, c, seg=6, rot=(0, 90, 0), caps=False, hull='none')
    m.bx(-0.02, 0.02, -0.28, 0.28, -0.08, -0.05, 'steelD', hull='none', cull='')
    m.bx(-0.015, 0.015, -0.015, 0.015, -0.05, H - 4.2, 'steelD', hull='none', cull='')
    make('Pipe', m, ao)


# ================================================================ paint shop
def build_paint(pal, ao):
    """[4, 4] paint booth open to the front (-Y): steel walls, the extraction filter wall at the back, a lit roof
    (glow), a turntable with a toy being sprayed by a robot (A) or a hanging conveyor of parts (B)"""
    for v in range(1):
        rnd = random.Random(400 + v)
        m = new(pal)
        g = new(pal)
        X, Y, Hh = 1.9, 1.9, 3.2
        m.bx(-X, X, Y - 0.1, Y, 0.0, Hh, 'machW', cull='b')
        for sx in (-1, 1):
            a, b = sorted((sx * X, sx * (X - 0.1)))
            m.bx(a, b, -Y, Y - 0.1, 0.0, Hh, 'machW', cull='b')
            # overspray stains inside the walls
            for k in range(3):
                z = rnd.uniform(0.6, 2.4)
                y0 = rnd.uniform(-1.4, 1.0)
                (rq if sx < 0 else lq)(m, sx * (X - 0.1) + (0.003 + 0.003 * k) * (1 if sx < 0 else -1), y0, y0 + 0.4, z, z + 0.25, rnd.choice(['pPink', 'gC', 'gB', 'pPurple']))
        m.bx(-X - 0.05, X + 0.05, -Y - 0.05, Y + 0.05, Hh, Hh + 0.3, 'pPurple')
        fq(m, -X - 0.05, X + 0.05, -Y - 0.053, Hh + 0.04, Hh + 0.26, 'pPurple')
        text_front(m, 'PAINT BOOTH', 0.18, -Y - 0.056, 0.0, Hh + 0.07, 'paper', maxw=2.8)
        # filter wall (grid of filter pads) on the back wall
        for i in range(4):
            for j in range(3):
                x0 = -1.6 + i * 0.82
                z0 = 0.4 + j * 0.85
                fq(m, x0, x0 + 0.76, Y - 0.103, z0, z0 + 0.78, 'cream')
        # lit roof panels, the floor grating
        dq(m, -X + 0.1, X - 0.1, -Y, Y - 0.1, Hh - 0.003, 'steel')
        for i in range(3):
            x0 = -1.5 + i * 1.05
            dq(g, x0, x0 + 0.9, -1.5, 1.4, Hh - 0.008, 'lightW')
        uq(m, -X + 0.1, X - 0.1, -Y + 0.05, Y - 0.1, 0.012, 'steelD')
        for k in range(6):
            y = -1.65 + k * 0.6
            uq(m, -X + 0.15, X - 0.15, y, y + 0.03, 0.016, 'steel')
        # the job: a turntable, the toy, the spray robot / a parts hanger rail
        if v == 0:
            m.cy((0.0, 0.2, 0.0), 0.7, 0.7, 0.3, 'steelD', seg=12)
            duck(m, 0.0, 0.2, 0.3, 1.5, c='gC', deg=-30)
            m.cy((1.25, 1.25, 0.0), 0.08, 0.08, 1.5, 'pOrange', seg=8)
            m.bm_((1.25, 1.25, 1.5), (0.55, 0.6, 1.35), 0.07, 'pOrange')
            m.cy((0.5, 0.55, 1.2), 0.04, 0.03, 0.18, 'chrome', seg=6)
            tube(m, (1.3, 1.4, 1.0), (1.3, 1.8, 2.8), 0.03, 'black', seg=5, hull='none')
        else:
            m.bx(-1.7, 1.7, -0.03, 0.03, 2.5, 2.56, 'steelD')
            for k in range(6):
                x = -1.4 + k * 0.56
                m.bx(x - 0.01, x + 0.01, -0.01, 0.01, 1.86 if k % 2 else 1.7, 2.5, 'steel', hull='none', cull='')
                c = rnd.choice(['gA', 'gB', 'gD', 'pPurple', 'pPink'])
                if k % 2:
                    tin_robot(m, x, 0.0, 1.05, 0.55, c=c)
                else:
                    m.bx(x - 0.2, x + 0.2, -0.04, 0.04, 1.3, 1.7, c)
            m.cy((-1.4, -1.0, 0.0), 0.25, 0.25, 0.9, 'gB', seg=10)
            m.cy((-1.4, -1.0, 0.9), 0.26, 0.26, 0.06, 'steel', seg=10)
            tube(m, (-1.4, -1.0, 0.96), (-0.8, -1.2, 1.4), 0.025, 'black', seg=5, hull='none')
            m.bx(-0.85, -0.7, -1.3, -1.12, 1.25, 1.45, 'steel')
        make('Booth', m, ao, cols=[cb(-X, Y - 0.1, 0.0, X, Y, Hh + 0.3), cb(-X, -Y, 0.0, -X + 0.1, Y, Hh + 0.3), cb(X - 0.1, -Y, 0.0, X, Y, Hh + 0.3),
                                            cb(-0.7, -0.5, 0.0, 0.7, 0.9, 1.4) if v == 0 else cb(-1.65, -1.3, 0.0, -1.15, -0.75, 1.0),
                                            cb(0.85, 0.85, 0.0, 1.55, 1.55, 1.2) if v == 0 else cb(-1.7, -0.25, 1.25, 1.7, 0.25, 2.56)])
        make_glow('Booth_LED', g)
    # drying rack [2, 1]: a wheeled rack with pegs of painted parts
    m = new(pal)
    rnd = random.Random(420)
    for sx in (-1, 1):
        m.bx(sx * 0.9 - 0.03, sx * 0.9 + 0.03, -0.3, 0.3, 0.08, 0.12, 'steelD', cull='')
        m.bx(sx * 0.9 - 0.03, sx * 0.9 + 0.03, -0.03, 0.03, 0.12, 1.9, 'steel', cull='b')
        for y in (-0.26, 0.26):
            m.cy((sx * 0.9, y, 0.0), 0.05, 0.05, 0.08, 'black', seg=6)
    for z in (0.55, 1.05, 1.55):
        m.bx(-0.9, 0.9, -0.025, 0.025, z, z + 0.04, 'steel', cull='')
        for k in range(3):
            x = -0.6 + k * 0.6
            c = rnd.choice(['gA', 'gB', 'gC', 'gD', 'pPink', 'pPurple'])
            m.bx(x - 0.1, x + 0.1, -0.08, 0.08, z - 0.26, z - 0.02, c, hull='none')
    make('DryRack', m, ao, cols=[cb(-0.95, -0.3, 0.0, 0.95, 0.3, 0.12), cb(-0.93, -0.04, 0.12, -0.87, 0.04, 1.9), cb(0.87, -0.04, 0.12, 0.93, 0.04, 1.9)] +
         [cb(-0.87, -0.08, z - 0.26, 0.87, 0.08, z + 0.04) for z in (0.55, 1.05, 1.55)])
    # paint drums: a pair of big cans with drips and lids (the colours from the goods cells)
    m = new(pal)
    for (x, y, c) in ((-0.2, -0.12, 'gA'), (0.22, 0.14, 'gB')):
        m.cy((x, y, 0.0), 0.2, 0.2, 0.42, 'chrome', seg=8)
        m.cy((x, y, 0.42), 0.205, 0.205, 0.03, c, seg=8)
        m.cy((x, y, 0.2), 0.203, 0.203, 0.14, c, seg=8, caps=False, hull='none')
    make('PaintCans', m, ao, cols=[cb(-0.42, -0.34, 0.0, 0.44, 0.36, 0.45)])


# ================================================================ packing
def infeed(m, x0, x1):
    """the machine's own belt section along X (same height as the line)"""
    m.bx(x0, x1, -0.4, 0.4, BT - 0.08, BT, 'rubber', hull='noside', cull='b')
    for s in (-1, 1):
        a, b = sorted((s * 0.4, s * 0.48))
        m.bx(x0, x1, a, b, 0.66, 0.98, 'machB', hull='noside', cull='')


def build_packing(pal, ao):
    """[6, 3] packaging machines along X (the line enters at -X on the belt centre line y = 0, front -Y): Boxer, a case
    packer (carton magazine, erected cartons, the guarded packing cell, a closed carton out); Shrink, a shrink-wrap
    tunnel (film unwind, L-sealer, the heat tunnel glowing orange behind strip curtains); Labeller (print-and-apply
    heads, label rolls, a scanner arch). Each with a touch screen (glow) and a stack light."""
    for kind in ('Boxer', 'Shrink', 'Labeller'):
        rnd = random.Random(hash(kind) % 1000)
        m = new(pal)
        g = new(pal)
        infeed(m, -2.8, 3.0)
        for (x, y) in ((-2.6, -0.3), (2.6, -0.3), (-2.6, 0.3), (2.6, 0.3), (0.0, -0.3), (0.0, 0.3)):
            m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, 0.66, 'steelD', hull='none', cull='bt')
        if kind == 'Boxer':
            # the guarded packing cell: a frame with polycarbonate panels over the belt
            m.bx(-1.6, 1.4, -0.95, 0.95, 0.0, 0.66, 'machW', cull='b')
            for (x, y) in ((-1.6, -0.95), (1.4, -0.95), (-1.6, 0.95), (1.4, 0.95)):
                m.bx(x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.66, 2.6, 'machB', cull='')
            m.bx(-1.65, 1.45, -1.0, 1.0, 2.6, 2.75, 'machB')
            fq(m, -1.55, 1.35, -1.0, 0.98, 2.55, 'glass')
            fq(m, -1.5, -1.3, -1.003, 1.05, 2.5, 'glassL')
            bq(m, -1.55, 1.35, 1.0, 0.98, 2.55, 'glass')
            # inside: a carton being filled (open flaps) and a pick head over it
            m.bx(-0.3, 0.3, -0.25, 0.25, BT, BT + 0.4, 'card', cull='bt')
            for (y0, y1) in ((-0.25, -0.24), (0.24, 0.25)):
                m.bx(-0.3, 0.3, y0 - 0.12 if y0 < 0 else y1, y0 if y0 < 0 else y1 + 0.12, BT + 0.4, BT + 0.41, 'cardL', hull='none', cull='')
            m.bx(-0.15, 0.15, -0.1, 0.1, 1.9, 2.6, 'steel')
            m.bx(-0.25, 0.25, -0.2, 0.2, 1.6, 1.9, 'chrome')
            # carton magazine (flat blanks) at the back, the outfeed with a closed carton, tape head
            m.bx(-2.6, -1.7, 0.5, 1.4, 0.0, 1.6, 'machW', cull='b')
            for k in range(6):
                z = 1.0 + k * 0.1
                m.bx(-2.55, -1.75, 0.55, 1.35, z, z + 0.08, 'card' if k % 2 else 'cardL', hull='none', cull='b' if k == 0 else '')
            carton(m, 1.8, 2.4, -0.25, 0.25, BT, BT + 0.42, 'card', art='gA')
            m.bx(1.95, 2.25, -0.3, 0.3, 1.5, 1.8, 'machB')
            m.bx(2.05, 2.15, -0.05, 0.05, 1.3, 1.5, 'brandR')
            panel_x = -2.2
        elif kind == 'Shrink':
            # film unwind, the L-sealer, the heat tunnel
            m.bx(-2.9, -2.1, 0.5, 1.2, 0.0, 1.2, 'machW', cull='b')
            m.cy((-2.5, 0.85, 1.2), 0.32, 0.32, 0.12, 'wrap', seg=12)
            m.cy((-2.5, 0.85, 1.32), 0.08, 0.08, 0.1, 'steel', seg=6)
            m.bx(-1.9, -0.9, -0.85, 0.85, 0.0, 0.66, 'machW', cull='b')
            m.bx(-1.9, -0.9, -0.6, 0.6, 1.4, 1.6, 'machB')
            for x in (-1.85, -0.95):
                m.bx(x - 0.05, x + 0.05, -0.6, -0.5, 0.98, 1.4, 'steel', cull='')
                m.bx(x - 0.05, x + 0.05, 0.5, 0.6, 0.98, 1.4, 'steel', cull='')
            m.bx(-0.6, 2.4, -0.85, 0.85, 0.0, 0.66, 'machW', cull='b')
            m.bx(-0.6, 2.4, -0.85, -0.5, 0.66, 1.9, 'brandR', cull='')
            m.bx(-0.6, 2.4, 0.5, 0.85, 0.66, 1.9, 'brandR', cull='')
            m.bx(-0.6, 2.4, -0.85, 0.85, 1.9, 2.1, 'brandR')
            fq(m, -0.4, 2.2, -0.853, 1.4, 1.75, 'pWhite')
            text_front(m, 'HEAT TUNNEL', 0.22, -0.856, 0.9, 1.46, 'brandR', maxw=2.4)
            for k in range(6):
                fq(m, -0.4 + k * 0.45, -0.1 + k * 0.45, -0.853, 0.8, 1.2, 'steelD')
            for xm in (-0.56, 2.36):
                for i in range(5):
                    y = -0.42 + i * 0.21
                    m.bx(xm - 0.01, xm + 0.01, y - 0.09, y + 0.09, BT + 0.04, 1.88, 'rubber', hull='none', cull='')
            uq(g, -0.5, 2.3, -0.48, 0.48, BT + 0.004, 'pOrange')
            bq(g, -0.5, 2.3, -0.497, BT + 0.1, 1.86, 'amber')
            # a wrapped pack of ducks coming out
            duck(m, 2.62, 0.0, BT, 0.24)
            m.bx(2.45, 2.85, -0.3, 0.3, BT, BT + 0.25, 'wrap', hull='none', cull='b')
            panel_x = -1.4
        else:
            # labeller: a portal frame over the belt, two print-and-apply heads, label rolls, a scanner arch
            for x in (-1.2, 1.2):
                for y in (-0.75, 0.75):
                    m.bx(x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.0, 2.4, 'machW', cull='b')
                m.bx(x - 0.08, x + 0.08, -0.8, 0.8, 2.4, 2.55, 'machB')
            m.bx(-1.3, 1.3, -0.8, 0.8, 2.55, 2.62, 'machB')
            for x in (-0.6, 0.5):
                m.bx(x - 0.25, x + 0.25, 0.25, 0.65, 1.0, 1.7, 'machW')
                m.cy((x, 0.45, 1.7), 0.18, 0.18, 0.1, 'pWhite', seg=8, rot=(90, 0, 0))
                m.cy((x, 0.62, 1.7), 0.06, 0.06, 0.08, 'steel', seg=6, rot=(90, 0, 0))
                m.bx(x - 0.12, x + 0.12, 0.05, 0.25, 1.32, 1.55, 'steelD')
                m.bx(x - 0.1, x + 0.1, 0.0, 0.05, 1.35, 1.52, 'pWhite', hull='none', cull='')
            m.bx(1.8, 1.9, -0.6, -0.5, 0.98, 2.0, 'steelD', cull='')
            m.bx(1.8, 1.9, 0.5, 0.6, 0.98, 2.0, 'steelD', cull='')
            m.bx(1.8, 1.9, -0.6, 0.6, 2.0, 2.1, 'steelD', cull='')
            fq(g, 1.81, 1.89, -0.6 - 0.003, 1.1, 1.9, 'red')
            for k in range(2):
                x0 = -1.0 + k * 1.4
                carton(m, x0, x0 + 0.55, -0.24, 0.24, BT, BT + 0.4, ['gB', 'gD'][k], art='pWhite')
            panel_x = -2.4
        # touch screen on a stand at the front, the stack light
        m.bm_((panel_x, -1.0, 0.0), (panel_x, -1.0, 1.4), 0.06, 'steelD')
        m.bx(panel_x - 0.3, panel_x + 0.3, -1.08, -0.95, 1.3, 1.75, 'pBlack')
        fq(g, panel_x - 0.27, panel_x + 0.27, -1.083, 1.33, 1.72, rnd.choice(['scrB', 'scrC']))
        text_front(g, kind.upper(), 0.07, -1.086, panel_x, 1.62, 'pWhite', font='cond', maxw=0.4)
        m.cy((2.75, 0.75, 0.0), 0.03, 0.03, 2.3, 'steel', seg=5)
        for k, c in enumerate(('red', 'amber', 'exitG')):
            m.cy((2.75, 0.75, 2.3 + k * 0.13), 0.07, 0.07, 0.12, 'chrome', seg=8)
            g.cy((2.75, 0.75, 2.31 + k * 0.13), 0.073, 0.073, 0.1, c, seg=8, caps=False)
        # the model name on a plate
        fq(m, -0.5, 0.5, -0.483, 0.7, 0.86, 'pWhite')
        text_front(m, {'Boxer': 'CASE PACKER', 'Shrink': 'SHRINK WRAP', 'Labeller': 'LABELLER'}[kind], 0.08, -0.486, 0.0, 0.74, 'brandB', font='cond', maxw=0.9)
        cols = [cb(-2.8, -0.48, 0.0, 3.0, 0.48, 0.98), cb(panel_x - 0.3, -1.08, 0.0, panel_x + 0.3, -0.95, 1.75), cb(2.7, 0.7, 0.0, 2.8, 0.8, 2.7)]
        if kind == 'Boxer':
            cols += [cb(-1.65, -1.0, 0.0, 1.45, 1.0, 2.75), cb(-2.6, 0.5, 0.0, -1.7, 1.4, 1.6), cb(1.8, -0.3, 0.98, 2.4, 0.3, 1.8)]
        elif kind == 'Shrink':
            cols += [cb(-2.9, 0.5, 0.0, -2.1, 1.2, 1.45), cb(-1.9, -0.85, 0.0, -0.9, 0.85, 1.6), cb(-0.6, -0.85, 0.0, 2.4, 0.85, 2.1)]
        else:
            cols += [cb(-1.3, -0.81, 0.0, 1.3, -0.69, 2.62), cb(-1.3, 0.69, 0.0, 1.3, 0.81, 2.62), cb(-1.3, -0.8, 2.4, 1.3, 0.8, 2.62),
                     cb(-0.85, 0.0, 1.3, 0.75, 0.65, 1.8), cb(1.8, -0.6, 0.98, 1.9, 0.6, 2.1)]
        make(kind, m, ao, cols=cols)
        make_glow(kind + '_LED', g)
    # manual pack bench [2, 1]: a carton being taped, a tape gun, a label printer, a scale, flat cartons under it
    m = new(pal)
    g = new(pal)
    m.bx(-0.95, 0.95, -0.4, 0.4, 0.86, 0.92, 'cream')
    for (x, y) in ((-0.88, -0.33), (0.88, -0.33), (-0.88, 0.33), (0.88, 0.33)):
        m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.86, 'steelD', hull='none', cull='bt')
    for k in range(4):
        m.bx(-0.85, 0.3, -0.3, 0.3, 0.1 + k * 0.03, 0.125 + k * 0.03, 'card' if k % 2 else 'cardL', hull='none', cull='b' if k == 0 else '')
    carton(m, -0.6, 0.0, -0.25, 0.25, 0.92, 1.3, 'card', art='gC')
    m.cy((0.2, -0.1, 0.92), 0.08, 0.08, 0.06, 'brandR', seg=8, rot=(90, 0, 0))
    m.bx(0.4, 0.8, 0.0, 0.32, 0.92, 1.15, 'machW')
    fq(g, 0.45, 0.62, -0.003, 1.0, 1.1, 'scrG')
    m.bx(0.42, 0.78, -0.32, -0.08, 0.92, 0.97, 'steel')
    for sx in (-1, 1):
        m.bx(sx * 0.92 - 0.03, sx * 0.92 + 0.03, 0.34, 0.4, 0.92, 1.9, 'steelD', cull='')
    m.bx(-0.89, 0.89, 0.345, 0.395, 1.84, 1.89, 'steelD', cull='')
    m.cy((-0.4, 0.37, 1.6), 0.18, 0.18, 0.08, 'cardL', seg=10, rot=(90, 0, 0))
    make('PackBench', m, ao, cols=[cb(-0.95, -0.4, 0.0, 0.95, 0.4, 1.3)])
    make_glow('PackBench_LED', g)
    # finished goods: pallets of printed toy cartons (three loads) and a pallet of flat cartons
    for v in range(3):
        rnd = random.Random(500 + v)
        m = new(pal)
        pallet(m, -0.48, 0.48, -0.48, 0.48)
        words = ['BLOKKO', 'QUACKERS', 'ROBO-PAL']
        nl = 3 if v != 1 else 2
        z = 0.14
        for k in range(nl):
            hh = rnd.uniform(0.34, 0.46)
            c = GOODS[(k + v) % 4]
            # one layer of four cartons: a block with the carton seams and the product panels painted on
            m.bx(-0.46, 0.46, -0.46, 0.46, z, z + hh - 0.004, c, cull='b')
            fq(m, -0.006, 0.006, -0.463, z, z + hh - 0.004, 'cardD')
            bq(m, -0.006, 0.006, 0.463, z, z + hh - 0.004, 'cardD')
            lq(m, -0.463, -0.006, 0.006, z, z + hh - 0.004, 'cardD')
            rq(m, 0.463, -0.006, 0.006, z, z + hh - 0.004, 'cardD')
            for xc in (-0.23, 0.23):
                fq(m, xc - 0.16, xc + 0.16, -0.466, z + hh * 0.15, z + hh * 0.6, 'pWhite')
                fq(m, xc - 0.08, xc + 0.08, -0.469, z + hh * 0.2, z + hh * 0.55, rnd.choice(['gC', 'gA', 'pPink', 'gB']))
            if k == nl - 1:
                uq(m, -0.006, 0.006, -0.46, 0.46, z + hh - 0.001, 'cardD')
            z += hh
        bq(m, -0.46, 0.46, 0.469, 0.4, z - 0.2, 'wrap')
        lq(m, -0.469, -0.46, 0.46, 0.4, z - 0.2, 'wrap')
        rq(m, 0.469, -0.46, 0.46, 0.4, z - 0.2, 'wrap')
        make('PalToys_' + 'ABC'[v], m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, z)])
    m = new(pal)
    pallet(m, -0.48, 0.48, -0.48, 0.48)
    m.bx(-0.46, 0.46, -0.44, 0.44, 0.14, 0.9, 'card', cull='b')
    for k in range(12):
        z = 0.18 + k * 0.06
        fq(m, -0.46, 0.46, -0.443, z, z + 0.01, 'cardD')
    uq(m, -0.4, 0.4, -0.4, 0.4, 0.903, 'cardL')
    fq(m, -0.2, 0.2, -0.446, 0.5, 0.7, 'pWhite')
    text_front(m, 'FLAT', 0.1, -0.449, 0.0, 0.55, 'brandB', maxw=0.35)
    make('PalFlat', m, ao, cols=[cb(-0.48, -0.48, 0.0, 0.48, 0.48, 0.9)])
    # stretch wrapper [2, 2]: turntable, mast with the film carriage, a pallet of cartons half wrapped
    m = new(pal)
    m.cy((0, 0, 0), 0.8, 0.8, 0.12, 'steelD', seg=12)
    ring(m, 0, 0, 0.123, 0.62, 0.72, 'hazY', seg=12)
    m.bx(-0.15, 0.15, 0.8, 0.98, 0.0, 2.4, 'brandB', cull='b')
    m.bx(-0.25, 0.25, 0.62, 0.8, 1.2, 1.5, 'steel')
    m.cy((0, 0.66, 1.0), 0.07, 0.07, 0.6, 'wrap', seg=8)
    m.bx(-0.3, 0.3, 0.75, 0.95, 0.0, 0.5, 'steelD', cull='b')
    pallet(m, -0.48, 0.48, -0.48, 0.48, 0.12)
    for (y0, y1) in ((-0.46, -0.005), (0.005, 0.46)):
        for (x0, x1) in ((-0.46, -0.005), (0.005, 0.46)):
            carton(m, x0, x1, y0, y1, 0.26, 0.7, 'gA' if x0 < 0 else 'gB', art='pWhite' if y0 < 0 else None)
            carton(m, x0, x1, y0, y1, 0.704, 1.14, 'gC' if x0 < 0 else 'gD', art='pWhite' if y0 < 0 else None)
    fq(m, -0.46, 0.46, -0.472, 0.3, 0.8, 'wrap')
    make('Wrapper', m, ao, cols=[cb(-0.8, -0.8, 0.0, 0.8, 0.8, 0.12), cb(-0.48, -0.48, 0.12, 0.48, 0.48, 1.14), cb(-0.3, 0.62, 0.0, 0.3, 0.98, 2.4)])
    # manual pallet jack (front -Y = the handle end)
    m = new(pal)
    for sx in (-1, 1):
        x = sx * 0.2
        m.bx(x - 0.08, x + 0.08, -0.15, 0.48, 0.0, 0.08, 'steelD', cull='b')
    m.bx(-0.3, 0.3, -0.35, -0.15, 0.0, 0.2, 'brandR', cull='b')
    m.cy((0, -0.3, 0.2), 0.07, 0.07, 0.35, 'steel', seg=8)
    m.bx(-0.06, 0.06, -0.5, -0.36, 0.0, 0.16, 'black')
    m.bm_((0, -0.3, 0.5), (0, -0.62, 1.15), 0.05, 'brandR')
    m.bx(-0.16, 0.16, -0.66, -0.58, 1.12, 1.2, 'black')
    make('PalletJack', m, ao, cols=[cb(-0.3, -0.5, 0.0, 0.3, 0.48, 0.2)])


# ================================================================ plush and QC
def build_plush(pal, ao):
    """[3, 3] plush stuffing machine (front -Y): the fluff drum with a window full of white fibre, the blower box,
    a stuffing nozzle over a table of empty bear skins (flat, faceless), sacks of fibre, a control box (glow)"""
    m = new(pal)
    g = new(pal)
    m.bx(-1.4, 0.2, 0.0, 1.4, 0.0, 0.3, 'steelD', cull='b')
    m.cy((-0.6, 0.7, 0.3), 0.7, 0.7, 1.7, 'pPink', seg=10)
    m.cy((-0.6, 0.7, 2.0), 0.72, 0.4, 0.3, 'pPink', seg=10)
    m.cy((-0.6, 0.7, 2.3), 0.25, 0.25, 0.3, 'steel', seg=10)
    fq(m, -1.0, -0.2, -0.003, 0.7, 1.7, 'pWhite')
    for k in range(3):
        x = -0.9 + k * 0.25
        fq(m, x, x + 0.14, -0.006, 0.8 + (k % 2) * 0.15, 1.4 + (k % 3) * 0.1, 'cream')
    m.bx(-1.05, -0.15, -0.03, 0.0, 0.66, 0.7, 'steel', hull='none', cull='')
    m.bx(-1.05, -0.15, -0.03, 0.0, 1.7, 1.74, 'steel', hull='none', cull='')
    m.bx(0.3, 1.2, 0.4, 1.3, 0.0, 1.1, 'machW', cull='b')
    fq(m, 0.4, 1.1, 0.397, 0.3, 0.9, 'steelD')
    tube(m, (-0.6, 0.7, 2.6), (0.0, -0.4, 2.5), 0.09, 'pWhite', seg=8)
    tube(m, (0.0, -0.4, 2.5), (0.0, -0.4, 1.3), 0.09, 'pWhite', seg=8)
    m.cy((0.0, -0.4, 1.12), 0.04, 0.1, 0.18, 'chrome', seg=8)
    # the stuffing table with empty skins and a stuffed bear
    m.bx(-1.3, 1.3, -1.4, -0.6, 0.84, 0.9, 'machW')
    for (x, y) in ((-1.22, -1.32), (1.22, -1.32), (-1.22, -0.68), (1.22, -0.68)):
        m.bx(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.84, 'steelD', hull='none', cull='bt')
    for k in range(2):
        x = -1.0 + k * 0.4
        uq(m, x - 0.12, x + 0.12, -1.2, -0.9, 0.903, 'pBrown' if k % 2 else 'pPink')
        disc(m, x, -0.88, 0.906, 0.1, 'pBrown' if k % 2 else 'pPink', seg=8)
    bear(m, 0.6, -1.0, 0.9, 0.5, c='pBrown')
    # sacks of fibre
    for (x, y) in ((0.75, 0.85),):
        m.sp((x, y, 1.35), 0.36, 'pWhite', seg=(6, 4), scale=(1.0, 0.9, 0.8))
    m.bx(0.1, 0.5, -0.45, -0.3, 1.0, 1.5, 'pBlack')
    fq(g, 0.13, 0.47, -0.453, 1.05, 1.45, 'scrG')
    m.bx(0.27, 0.33, -0.36, -0.3, 0.0, 1.0, 'steelD', hull='none', cull='b')
    text_side(m, 'FLUFF-O-MATIC', 0.16, -1.303, 0.7, 1.9, 'pWhite', 'x-', maxw=1.2)
    make('Stuffer', m, ao, cols=[cb(-1.32, 0.0, 0.0, 0.12, 1.4, 2.3), cb(0.3, 0.4, 0.0, 1.2, 1.3, 1.7), cb(-1.3, -1.4, 0.0, 1.3, -0.6, 1.35),
                                 cb(0.1, -0.45, 0.0, 0.5, -0.3, 1.5)])
    make_glow('Stuffer_LED', g)


def build_lines(pal, ao):
    build_belts(pal, ao)
    build_items(pal, ao)
    build_line_props(pal, ao)
    build_moulding(pal, ao)
    build_paint(pal, ao)
    build_packing(pal, ao)
    build_plush(pal, ao)
