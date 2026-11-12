"""kit-academy gymnasium and courtyard: pulled-out bleachers (walkable tiers), the stage, hoops hung from the roof,
mats, ball carts, gear shelves, the snack bar and the ticket table; the big tree in its raised seat-wall bed
(landmark), planters, picnic tables, bike racks, the covered walkway, the flagpole, lamp posts, the outdoor classroom
tiers, street trees in grates, and the backdrop tree clusters (see ac_base.py for the conventions)."""
import math
import random

from ac_base import *  # noqa: F401,F403

STEP_R, STEP_D = 0.16, 0.28     # bleacher steps: rise per depth (at most two a 0.5 m nav cell: 0.32 m)


def stepped(k, x0, x1, y_front, n, rise, depth, cA, cB, side='steelD', top_c=None):
    """n walkable steps rising toward +Y from y_front; closed end panels to the floor; returns the top height"""
    for j in range(n):
        top = (j + 1) * rise
        a = y_front + j * depth
        b = a + depth
        k.bx(x0, x1, a, b, top - rise, top, cA if j % 2 == 0 else cB, cull='bk' if j < n - 1 else 'b')
        if j > 0:
            k.lq(x0, a, b, 0.0, top - rise, side)
            k.rq(x1, a, b, 0.0, top - rise, side)
        k.wcol(x0, x1, a, b, 0.0, top)
    return n * rise


# ================================================================ gym
def build_gym(k, ao):
    # bleachers [8, 5]: 12 steps (seat boards and foot boards in turn), a rail along the top, closed ends
    k.begin()
    top = stepped(k, -3.98, 3.98, -2.45, 15, STEP_R, STEP_D, 'woodL', 'steel')
    yb = -2.45 + 15 * STEP_D
    k.bx(-3.98, 3.98, yb, 2.5, top - 0.2, top, 'steel', cull='b')
    k.lq(-3.98, yb, 2.5, 0.0, top - 0.2, 'steelD')
    k.rq(3.98, yb, 2.5, 0.0, top - 0.2, 'steelD')
    k.wcol(-3.98, 3.98, yb, 2.5, 0.0, top)
    for j in range(0, 15, 2):
        a = -2.45 + j * STEP_D
        k.fq(-3.98, 3.98, a - 0.003, (j + 1) * STEP_R - 0.06, (j + 1) * STEP_R - 0.02, 'wood')
    k.bx(-3.98, 3.98, 2.42, 2.48, top + 0.95, top + 1.0, 'slate')
    for x in (-3.9, -1.3, 1.3, 3.9):
        k.bx(x - 0.03, x + 0.03, 2.42, 2.48, top, top + 0.95, 'slate', ink=False)
    k.col(-3.98, 3.98, 2.4, 2.5, top, top + 1.0)
    k.finish('Bleacher', ao=ao)
    # the stage [14, 6] (front -Y): a 1 m platform 4.5 m deep with steps down to the floor near both ends, the proscenium,
    # curtains, a valance with the school name, a lectern and chairs from the spring concert
    k.begin()
    rnd = random.Random(51)
    H, yF = 1.0, -1.5
    k.bx(-6.95, 6.95, yF, 2.98, 0.0, H, 'woodD', cull='bk')
    k.uq(-6.9, 6.9, yF + 0.05, 2.9, H + 0.003, 'wood')
    for i in range(6):
        x = -5.4 + i * 2.15
        k.fq(x, x + 1.7, yF - 0.003, 0.15, 0.8, 'wood')
        k.fq(x + 0.75, x + 0.95, yF - 0.006, 0.4, 0.46, 'chrome')
    k.wcol(-6.95, 6.95, yF, 2.98, 0.0, H)
    for s in (-1, 1):
        xa, xb = sorted((s * 5.9, s * 4.4))
        for j in range(6):
            tt = (j + 1) * H / 6
            a = -3.0 + j * 0.25
            k.bx(xa, xb, a, a + 0.25, tt - H / 6, tt, 'woodL' if j % 2 else 'wood', cull='bk')
            k.wcol(xa, xb, a, a + 0.25, 0.0, tt)
        xr = s * 5.95
        k.beam((xr, -2.95, 1.0), (xr, yF - 0.05, 1.95), 0.05, 'slate')
        k.col(min(xr - 0.05, xr + 0.05), max(xr - 0.05, xr + 0.05), -3.0, yF, 0.0, 2.0)
        k.cyl(xr, -2.95, 0.0, 0.025, 0.025, 1.0, 'slate', seg=5, ink=False, caps=False)
        # proscenium pillar and the side curtain (leg)
        xa, xb = sorted((s * 6.95, s * 6.55))
        k.bx(xa, xb, yF, yF + 0.4, H, 6.3, 'wallC', cull='b')
        k.col(xa, xb, yF, yF + 0.4, H, 6.3)
        for f in range(2):
            xx = s * (6.45 - f * 0.22)
            k.bx(xx - 0.11, xx + 0.11, yF + 0.5 + (f % 2) * 0.06, yF + 0.62 + (f % 2) * 0.06, H, 5.9, 'curtain')
    k.bx(-6.95, 6.95, yF, yF + 0.4, 6.3, 6.9, 'wallC')
    k.bx(-6.55, 6.55, yF + 0.42, yF + 0.5, 5.2, 6.3, 'curtain')
    ib_text.draw(k, 'CHALKSTONE ACADEMY', 0.0, yF - 0.004, 6.42, 0.36, 'slate', face='y-', font='serif', maxw=9.0)
    for i in range(13):
        x = -6.0 + i * 1.0
        k.bx(x - 0.5, x + 0.5, 2.55 + (i % 2) * 0.08, 2.7 + (i % 2) * 0.08, H, 6.0, 'curtain')
    k.bx(-0.3, 0.3, 0.0, 0.45, H, H + 1.15, 'woodD')
    k.bx(-0.36, 0.36, -0.08, 0.5, H + 1.15, H + 1.2, 'wood')
    k.cyl(0.0, -0.05, H + 1.2, 0.01, 0.01, 0.25, 'black', seg=4, ink=False, rot=(25, 0, 0))
    k.col(-0.3, 0.3, 0.0, 0.45, H, H + 1.2)
    for i in range(5):
        x = -4.5 + i * 1.0
        k.chair(x, 1.6, 0, 'navy')
    k.bx(3.2, 4.8, 1.0, 1.9, H, H + 1.0, 'black')
    k.bx(3.15, 4.85, 0.95, 1.95, H + 1.0, H + 1.06, 'black')
    k.fq(3.3, 4.7, 0.997, H + 0.75, H + 0.95, 'paper')
    k.col(3.15, 4.85, 0.95, 1.95, H, H + 1.06)
    k.finish('Stage', ao=ao)
    # basketball hoop [2, 1] hung from the 8 m roof: the frame, a glass backboard 1.2 m in from the baseline, the
    # rim and the net (front -Y: the court)
    k.begin()
    yB = -1.2
    for x in (-0.6, 0.6):
        k.bx(x - 0.04, x + 0.04, yB + 0.08, yB + 0.16, 3.9, WALL_H - 0.004, 'steelD', cull='t')
    k.beam((0.0, yB + 0.12, 4.5), (0.0, 0.5, WALL_H - 0.02), 0.07, 'steelD')
    k.bx(-0.62, 0.62, yB + 0.07, yB + 0.17, 4.5, 4.58, 'steelD')
    k.bx(-0.9, 0.9, yB - 0.03, yB + 0.03, 2.9, 3.95, 'glassL')
    k.fq(-0.86, 0.86, yB - 0.033, 3.88, 3.92, 'paper')
    k.fq(-0.86, -0.82, yB - 0.033, 2.98, 3.88, 'paper')
    k.fq(0.82, 0.86, yB - 0.033, 2.98, 3.88, 'paper')
    k.fq(-0.86, 0.86, yB - 0.033, 2.94, 2.98, 'paper')
    k.fq(-0.3, 0.3, yB - 0.036, 3.1, 3.5, 'chD')
    k.fq(-0.26, 0.26, yB - 0.039, 3.14, 3.46, 'glassL')
    yr = yB - 0.38
    for i in range(12):
        a, b = i / 12 * 2 * math.pi, (i + 1) / 12 * 2 * math.pi
        k.beam((math.cos(a) * 0.23, yr + math.sin(a) * 0.23, 3.05), (math.cos(b) * 0.23, yr + math.sin(b) * 0.23, 3.05), 0.025, 'chB')
    k.bx(-0.06, 0.06, yr + 0.2, yB - 0.03, 3.0, 3.06, 'chB')
    k.cyl(0.0, yr, 2.62, 0.14, 0.22, 0.42, 'paper', seg=10, ink=False, caps=False)
    k.finish('Hoop', ao=ao)
    # folded gym mats [2, 1] (a stack of three)
    k.begin()
    for j in range(3):
        z = j * 0.2
        k.bx(-0.9 + j * 0.03, 0.9 - j * 0.04, -0.42, 0.42, z, z + 0.19, 'mat')
        for x in (-0.3, 0.3):
            k.fq(x - 0.006, x + 0.006, -0.423, z + 0.02, z + 0.17, 'navy')
    k.col(-0.9, 0.9, -0.42, 0.42, 0.0, 0.6)
    k.finish('Mats', ao=ao)
    # ball cart (1 cell): a wire cart of basketballs
    k.begin()
    k.bx(-0.38, 0.38, -0.25, 0.25, 0.25, 0.3, 'steelD', ink=False)
    for x in (-0.36, 0.36):
        for y in (-0.23, 0.23):
            k.bx(x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.06, 0.93, 'steel', ink=False)
            k.sph(x, y, 0.04, 0.04, 'black', seg=(5, 3))
    for z in (0.62, 0.95):
        k.bx(-0.38, 0.38, -0.25, -0.22, z - 0.02, z, 'steel', ink=False)
        k.bx(-0.38, 0.38, 0.22, 0.25, z - 0.02, z, 'steel', ink=False)
    for (x, y, z) in ((-0.2, -0.05, 0.42), (0.2, 0.05, 0.42), (0.0, 0.0, 0.66)):
        k.sph(x, y, z, 0.12, 'chB', seg=(7, 4))
    k.col(-0.38, 0.38, -0.25, 0.25, 0.0, 0.95)
    k.finish('BallCart', ao=ao)
    # gear shelf [2, 1] against a wall: steel shelves of balls, cones, a bin of bibs
    k.begin()
    for x in (-0.9, 0.9):
        for y in (-0.25, 0.25):
            k.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 1.9, 'steelD', ink=False, cull='b')
    for z in (0.3, 1.0, 1.7):
        k.bx(-0.88, 0.88, -0.27, 0.27, z, z + 0.03, 'steel')
    for (x, c, r) in ((-0.6, 'paper', 0.11), (-0.3, 'chB', 0.12), (0.0, 'paper', 0.11), (0.35, 'foodY', 0.11), (0.65, 'chB', 0.12)):
        k.sph(x, 0.0, 1.03 + r, r, c, seg=(7, 5))
    for x in (-0.6, -0.35, -0.1):
        k.cyl(x, 0.0, 0.33, 0.1, 0.02, 0.25, 'chB', seg=8)
    k.bx(0.15, 0.8, -0.22, 0.22, 0.33, 0.7, 'chA')
    k.bx(-0.7, 0.4, -0.2, 0.2, 1.73, 1.95, 'chC')
    k.col(-0.92, 0.92, -0.27, 0.27, 0.0, 1.95)
    k.finish('GearShelf', ao=ao)
    # snack bar [6, 2] against a wall: the counter, the SNACK SHACK board, a popcorn machine, a drinks cooler
    k.begin()
    g = AKit(k.pal, k.prefix, k.hull_t).begin()
    k.bx(-2.9, 2.9, -0.95, -0.35, 0.0, 1.05, 'slate', cull='b')
    for i in range(5):
        x = -2.8 + i * 1.14
        k.fq(x, x + 1.06, -0.953, 0.1, 0.95, 'navy')
    k.fq(-1.4, 1.4, -0.956, 0.45, 0.75, 'gold')
    k.text('COMETS', 0.0, -0.959, 0.5, 0.22, 'navy', font='display')
    k.bx(-2.95, 2.95, -1.05, -0.3, 1.05, 1.1, 'lam')
    k.bx(-2.9, -2.4, -0.35, 0.95, 0.0, 1.05, 'slate', cull='b')
    k.bx(-1.7, -1.0, -0.75, -0.4, 1.1, 1.75, 'chD')
    g.fq(-1.65, -1.05, -0.753, 1.2, 1.65, 'foodY')
    k.bx(0.6, 1.1, -0.75, -0.45, 1.1, 1.3, 'black')
    g.fq(0.64, 1.06, -0.753, 1.14, 1.26, 'scrB')
    k.bx(1.6, 2.6, 0.3, 0.95, 0.0, 1.9, 'chrome', cull='b')
    g.fq(1.66, 2.54, 0.297, 0.2, 1.8, 'glassL')
    k.bx(-2.4, 1.5, 0.55, 0.95, 0.0, 0.9, 'steel', cull='b')
    k.bx(-2.6, 2.6, 0.85, 0.95, 2.3, 3.2, 'navy')
    k.text('SNACK SHACK', 0.0, 0.847, 2.5, 0.48, 'gold', font='display', maxw=4.8)
    k.col(-2.95, 2.95, -1.05, -0.3, 0.0, 1.1)
    k.col(-2.9, -2.4, -0.3, 0.95, 0.0, 1.05)
    k.col(1.6, 2.6, 0.3, 0.95, 0.0, 1.9)
    k.col(-2.4, 1.5, 0.55, 0.95, 0.0, 0.9)
    k.finish('SnackBar', ao=ao)
    g.finish('SnackBar_Glow')
    # ticket table [2, 1]: a folding table with a cash box, a roll of tickets, a sign; the chair behind (+Y)
    k.begin()
    k.legs4(-0.85, 0.85, -0.35, 0.35, 0.71, 'steelD', t=0.03, ink=False)
    k.bx(-0.88, 0.88, -0.38, 0.38, 0.71, 0.74, 'lam')
    k.fq(-0.86, 0.86, -0.383, 0.4, 0.71, 'slate')
    k.bx(-0.3, 0.1, -0.15, 0.15, 0.74, 0.86, 'steelD')
    k.cyl(0.4, 0.0, 0.74, 0.07, 0.07, 0.06, 'chD', seg=8)
    k.bx(-0.7, -0.4, -0.2, -0.17, 0.74, 1.0, 'paper')
    k.text('TICKETS', -0.55, -0.203, 0.85, 0.06, 'chD', font='display')
    k.chair(0.0, 0.62, 180, 'navy')
    k.col(-0.88, 0.88, -0.38, 0.38, 0.0, 0.86)
    k.finish('TicketTable', ao=ao)


# ================================================================ courtyard
def crown(k, rnd, x, y, z, r, n=5, c1='leaf', c2='leafD', seg=(8, 5)):
    k.sph(x, y, z, r, c1, seg=seg, scale=(1.0, 1.0, 0.82))
    for i in range(n):
        a = i / n * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        rr = r * rnd.uniform(0.5, 0.68)
        k.sph(x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62, z + rnd.uniform(-0.2, 0.35) * r, rr, c2 if i % 2 else c1, seg=(6, 4), scale=(1.0, 1.0, 0.85))


def build_courtyard(k, ao):
    # the big tree [9, 9] (landmark): an old oak in a raised round bed with a brick seat wall and a stone cap
    k.begin()
    rnd = random.Random(61)
    R0, R1, Hw = 3.85, 3.45, 0.45
    k.cyl(0, 0, 0.0, R0, R0, Hw - 0.06, 'brick', seg=32, caps=False)
    k.cyl(0, 0, Hw - 0.06, R0 + 0.06, R0 + 0.06, 0.06, 'stone', seg=32, caps=False)
    k.ring(0, 0, Hw, R1 - 0.02, R0 + 0.06, 'stone', seg=32)
    k.disc(0, 0, Hw - 0.04, R1 - 0.02, 'bark', n=32)
    for i in range(10):
        a = i / 10 * 2 * math.pi + 0.2
        k.poly([(math.cos(a) * 1.4 + math.cos(a + t / 5 * 6.283) * 0.35, math.sin(a) * 1.4 + math.sin(a + t / 5 * 6.283) * 0.35, Hw - 0.035) for t in range(5)], 'grass2', (0, 0, 1))
    k.cyl(0, 0, Hw - 0.05, 0.75, 0.55, 0.6, 'bark', seg=10)
    k.cyl(0, 0, Hw + 0.5, 0.55, 0.38, 3.6, 'bark', seg=10)
    limbs = [((0.0, 0.0, 3.8), (2.6, 0.6, 6.2)), ((0.0, 0.0, 4.0), (-2.2, 1.6, 6.6)), ((0.0, 0.0, 3.6), (-0.6, -2.6, 6.0)),
             ((0.0, 0.0, 4.2), (1.0, 2.4, 7.2)), ((0.0, 0.0, 4.4), (0.2, -0.4, 8.2))]
    for a, b in limbs:
        k.tube(a, b, 0.3, 0.16, 'bark', seg=7)
    for (x, y, z, r) in ((2.7, 0.7, 7.1, 2.4), (-2.4, 1.7, 7.4, 2.5), (-0.6, -2.7, 6.9, 2.3), (1.1, 2.6, 8.0, 2.2), (0.2, -0.3, 9.0, 2.8)):
        crown(k, rnd, x, y, z, r, n=4)
    # roots at the foot, benches built into the seat wall are the courtyard benches (separate pieces)
    for i in range(5):
        a = i / 5 * 2 * math.pi + 0.5
        k.tube((math.cos(a) * 0.4, math.sin(a) * 0.4, Hw + 0.15), (math.cos(a) * 1.2, math.sin(a) * 1.2, Hw - 0.04), 0.18, 0.06, 'bark', seg=5)
    k.col(-0.9, 0.9, -0.9, 0.9, 0.0, 4.5)
    for i in range(12):
        a, b = i / 12 * 2 * math.pi, (i + 1) / 12 * 2 * math.pi
        xm, ym = math.cos((a + b) / 2) * (R0 - 0.2), math.sin((a + b) / 2) * (R0 - 0.2)
    # the bed (raised soil to the cap) is solid: the player stands on its rim and soil like on any cover top
    k.col(-2.7, 2.7, -2.7, 2.7, 0.0, Hw)
    for (x0, x1, y0, y1) in ((-3.85, -2.7, -1.7, 1.7), (2.7, 3.85, -1.7, 1.7), (-1.7, 1.7, -3.85, -2.7), (-1.7, 1.7, 2.7, 3.85),
                             (-3.4, -2.7, -2.5, -1.7), (2.7, 3.4, -2.5, -1.7), (-3.4, -2.7, 1.7, 2.5), (2.7, 3.4, 1.7, 2.5),
                             (-2.5, -1.7, -3.4, -2.7), (1.7, 2.5, -3.4, -2.7), (-2.5, -1.7, 2.7, 3.4), (1.7, 2.5, 2.7, 3.4)):
        k.col(x0, x1, y0, y1, 0.0, Hw)
    k.finish('Landmark_Tree', ao=ao)
    # planter [4, 2]: a raised brick bed with a stone cap, shrubs and flowers (the school garden beds too)
    for v in range(2):
        k.begin()
        rnd = random.Random(70 + v)
        k.bx(-1.9, 1.9, -0.9, 0.9, 0.0, 0.52, 'brick', cull='b')
        k.bx(-1.95, 1.95, -0.95, 0.95, 0.52, 0.6, 'stone', cull='')
        k.uq(-1.78, 1.78, -0.78, 0.78, 0.603, 'bark')
        if v == 0:
            for i in range(4):
                x = -1.35 + i * 0.9
                k.sph(x + rnd.uniform(-0.1, 0.1), rnd.uniform(-0.15, 0.15), 0.85, rnd.uniform(0.42, 0.55), 'leafD' if i % 2 else 'leaf', seg=(8, 5))
        else:
            for j in range(3):
                y = -0.5 + j * 0.5
                k.sph(0.0, y, 0.7, 0.2, ['leaf', 'grass', 'leafD'][j], seg=(8, 3), scale=(8.0, 1.0, 1.0))
                k.sph(-1.0 + j * 0.8, y + 0.05, 0.84, 0.09, ['chD', 'foodY', 'chF'][j], seg=(5, 3))
        k.col(-1.95, 1.95, -0.95, 0.95, 0.0, 0.6)
        k.finish('Planter' + 'AB'[v], ao=ao)
    # picnic table [2, 2]: A-frame legs, two attached benches
    k.begin()
    for i in range(4):
        y = -0.36 + i * 0.18 + 0.01
        k.bx(-0.95, 0.95, y, y + 0.16, 0.72, 0.76, 'wood')
    for s in (-1, 1):
        for i in range(2):
            y = s * (0.62 + i * 0.14)
            k.bx(-0.95, 0.95, min(y, y + s * 0.12), max(y, y + s * 0.12), 0.42, 0.46, 'wood')
        for x in (-0.7, 0.7):
            k.beam((x, s * 0.85, 0.0), (x, s * 0.1, 0.72), 0.07, 'woodD')
    for x in (-0.7, 0.7):
        k.bx(x - 0.04, x + 0.04, -0.9, 0.9, 0.38, 0.42, 'woodD')
    k.col(-0.95, 0.95, -0.37, 0.37, 0.0, 0.76)
    k.col(-0.95, 0.95, -0.92, -0.6, 0.0, 0.46)
    k.col(-0.95, 0.95, 0.6, 0.92, 0.0, 0.46)
    k.finish('Picnic', ao=ao)
    # bike rack [4, 1] against a wall (its back at +Y): five steel loops, two bikes parked nose out (their rear
    # wheels clear of the wall, the front wheels over the paving in front)
    k.begin()
    for i in range(5):
        x = -1.6 + i * 0.8
        k.beam((x, 0.02, 0.0), (x, 0.02, 0.8), 0.05, 'steel')
        k.beam((x, 0.42, 0.0), (x, 0.42, 0.8), 0.05, 'steel')
        k.beam((x, -0.01, 0.8), (x, 0.45, 0.8), 0.062, 'steel')
        k.col(x - 0.04, x + 0.04, -0.01, 0.45, 0.0, 0.83)
    for (x, c) in ((-1.2, 'chA'), (0.4, 'chD')):
        for y in (0.1, -1.0):
            k.push(x, y, 0, 0.34)
            k.cyl(-0.025, 0, 0, 0.34, 0.34, 0.05, 'black', seg=10, rot=(0, 90, 0))
            k.pop()
        k.beam((x, 0.1, 0.34), (x, -0.45, 0.62), 0.04, c)
        k.beam((x, -0.43, 0.6), (x, -1.0, 0.34), 0.032, c)
        k.beam((x, -0.51, 0.34), (x, -0.47, 0.6), 0.05, c)
        k.beam((x, -0.05, 0.95), (x, -0.13, 0.66), 0.024, 'steelD')
        k.bx(x - 0.06, x + 0.06, -0.1, 0.06, 0.95, 0.98, 'black')
        k.bx(x - 0.3, x + 0.3, -0.98, -0.92, 0.95, 0.98, 'black')
        k.beam((x, -0.95, 0.64), (x, -0.95, 0.95), 0.018, 'steelD')
        k.col(x - 0.05, x + 0.05, -1.34, 0.45, 0.0, 1.0)
    k.finish('BikeRack', ao=ao)
    # the covered walkway [2, 4] (run along X): a flat steel canopy 3 m up on posts, fascia, gutters, lights
    def canopy(k, posts, ledger_s=False, ledger_n=False, ext=0.0):
        x0, x1 = -1.0 - ext, 1.0
        k.bx(x0, x1, -2.0, 2.0, 3.0, 3.08, 'steelD', cull='')
        k.dq(x0, x1, -1.9, 1.9, 2.997, 'trimW')
        for s in (-1, 1):
            a, b = sorted((s * 2.0, s * 2.12))
            k.bx(x0, x1, a, b, 2.88, 3.2, 'slate')
        k.bx(x0 + 0.02, x1 - 0.02, -0.06, 0.06, 2.8, 3.0, 'slate', ink=False)
        if posts:
            for s in (-1, 1):
                y = s * 1.75
                k.cyl(0.92, y, 0.0, 0.07, 0.07, 3.0, 'slate', seg=6, caps=False)
                k.cyl(0.92, y, 0.0, 0.13, 0.13, 0.1, 'stoneD', seg=6, ink=False)
                k.col(0.84, 1.0, y - 0.08, y + 0.08, 0.0, 3.0)
        if ledger_s:
            k.bx(x0, x0 + 0.12, -2.0, 2.0, 2.7, 2.99, 'slate')
        if ledger_n:
            k.bx(x1 - 0.12, x1, -2.0, 2.0, 2.7, 2.99, 'slate')
        k.col(x0, x1, -2.12, 2.12, 2.88, 3.2)
    k.begin(); canopy(k, True, ledger_s=True, ext=1.0); k.finish('Canopy_S', ao=ao)
    k.begin(); canopy(k, True); k.finish('Canopy_M', ao=ao)
    k.begin(); canopy(k, False, ledger_n=True); k.finish('Canopy_N', ao=ao)
    k.begin()
    k.poly([(-0.3, -0.06, 2.795), (0.3, -0.06, 2.795), (0.3, 0.06, 2.795), (-0.3, 0.06, 2.795)], 'lightW', (0, 0, -1))
    k.finish('Canopy_Glow')
    # flagpole [2, 2]: a stone plinth with a plaque, the pole, the school flag
    k.begin()
    k.bx(-0.8, 0.8, -0.8, 0.8, 0.0, 0.4, 'stone', cull='b')
    k.bx(-0.85, 0.85, -0.85, 0.85, 0.4, 0.46, 'stoneD')
    k.fq(-0.35, 0.35, -0.803, 0.1, 0.32, 'gold')
    k.text('EST 1962', 0.0, -0.806, 0.16, 0.1, 'brick2', font='serif')
    k.cyl(0, 0, 0.46, 0.08, 0.05, 9.5, 'chrome', seg=8)
    k.sph(0, 0, 10.0, 0.1, 'gold', seg=(6, 4))
    for s in (-1, 1):
        k.qy(0.06, 1.9, 8.6, 9.8, s * 0.004, s, 'slate')
        k.qy(0.6, 1.36, 8.85, 9.55, s * 0.007, s, 'gold')
    k.col(-0.85, 0.85, -0.85, 0.85, 0.0, 0.46)
    k.col(-0.08, 0.08, -0.08, 0.08, 0.46, 4.0)
    k.finish('Flagpole', ao=ao)
    # lamp post (1 cell): a lantern on a slate pole
    k.begin()
    k.cyl(0, 0, 0.0, 0.14, 0.12, 0.4, 'slate', seg=8)
    k.cyl(0, 0, 0.4, 0.05, 0.05, 3.3, 'slate', seg=6, caps=False)
    k.cyl(0, 0, 3.7, 0.22, 0.16, 0.45, 'black', seg=6, caps=False)
    k.cyl(0, 0, 4.15, 0.26, 0.05, 0.18, 'slate', seg=6)
    k.col(-0.14, 0.14, -0.14, 0.14, 0.0, 3.7)
    k.finish('LampPost', ao=ao)
    k.begin()
    k.cyl(0, 0, 3.72, 0.2, 0.15, 0.42, 'lightW', seg=6, caps=False)
    k.finish('LampPost_Glow')
    # outdoor classroom tiers [10, 4] (front -Y): six concrete steps, wooden seat boards on every other one
    k.begin()
    top = stepped(k, -4.95, 4.95, -1.95, 6, 0.2, 0.62, 'conc', 'conc', side='concD')
    for j in range(1, 6, 2):
        a = -1.95 + j * 0.62
        k.bx(-4.8, 4.8, a + 0.08, a + 0.5, (j + 1) * 0.2, (j + 1) * 0.2 + 0.04, 'wood')
    k.bx(-4.95, 4.95, -1.95 + 6 * 0.62, 2.0, 0.0, top, 'concD', cull='b')
    k.wcol(-4.95, 4.95, -1.95 + 6 * 0.62, 2.0, 0.0, top)
    k.finish('Tiers', ao=ao)
    # a street tree in a grate [2, 2]
    k.begin()
    rnd = random.Random(80)
    k.uq(-0.8, 0.8, -0.8, 0.8, 0.005, 'steelD')
    for i in range(6):
        k.uq(-0.7, 0.7, -0.6 + i * 0.24, -0.56 + i * 0.24, 0.008, 'black')
    k.cyl(0, 0, 0.0, 0.18, 0.12, 3.2, 'bark', seg=8)
    k.tube((0, 0, 2.6), (0.6, 0.3, 3.6), 0.1, 0.06, 'bark', seg=5)
    crown(k, rnd, 0.1, 0.0, 4.4, 1.6, n=4)
    k.col(-0.2, 0.2, -0.2, 0.2, 0.0, 3.0)
    k.finish('TreeGrate', ao=ao)
    # backdrop tree clusters (rings of the level-wide backdrop: big, low-poly, outlined)
    for v in range(2):
        k.begin()
        rnd = random.Random(90 + v)
        for i in range(3):
            x, y = (i - 1) * 4.5 + rnd.uniform(-1, 1), rnd.uniform(-2, 2)
            h = rnd.uniform(5.0, 7.0)
            k.cyl(x, y, 0.0, 0.5, 0.35, h, 'bark', seg=6, caps=False)
            r = rnd.uniform(3.6, 4.6)
            k.sph(x, y, h + r * 0.6, r, 'leafD' if (i + v) % 2 else 'leaf', seg=(6, 4), scale=(1.0, 1.0, 0.9))
            k.sph(x + r * 0.5, y, h + r * 1.1, r * 0.6, 'leaf', seg=(5, 3))
        k.finish('Backdrop_Trees' + 'AB'[v])


def build_gym_yard(k, ao):
    build_gym(k, ao)
    build_courtyard(k, ao)
