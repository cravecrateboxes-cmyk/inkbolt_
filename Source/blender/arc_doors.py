"""kit-arctic openings and fittings: door frames (station front door, interior doors, the lab doors, the breaches the ice
made, the breakable vault door with its damage stages), the gate portal and shutter, the shaft walls of the trail, the
exit hatch, stairs (snow steps onto the buried module, steel stairs to the catwalks), catwalk rails, ceiling tiles and
fittings, the cave ceiling's hanging ice and lamps, and the flat floor finishes (see arc_base.py)."""
import math

from arc_base import *  # noqa: F401,F403
import arc_base as B
import arc_struct as S

OW = 1.2   # half the door opening width


def casing(m, y, s, c='orange', z1=DH, w=0.1):
    """door casing round an opening on the plane y (facing s * Y)"""
    f = fq if s < 0 else bq
    for sx in (-1, 1):
        a, b = sorted((sx * OW, sx * (OW + w)))
        f(m, a, b, y, 0.0, z1 + w, c)
    f(m, -OW, OW, y, z1, z1 + w, c)


def jambs(m, d, c='steelL', z1=DH, top=None):
    """the reveal of an opening through a wall d deep (y from -d to d): jamb blocks and the head"""
    for sx in (-1, 1):
        a, b = sorted((sx * OW, sx * 1.5))
        m.bx(a, b, -d + 0.01, d - 0.01, 0.0, z1, c, cull='b')
    m.bx(-1.5, 1.5, -d + 0.01, d - 0.01, z1, top or (z1 + 0.25), c, cull='')


def door_cols(d):
    return [cb(-1.5, -d, 0.0, -OW, d, DH), cb(OW, -d, 0.0, 1.5, d, DH)]


def ext_upper(m, y, rnd):
    """facade above a door on the trench side (plane y, facing -Y): panels, eave, firn overburden"""
    fq(m, -1.5, 1.5, y, DH + 0.1, 3.9, 'panelW')
    m.bx(-1.5, 1.5, y - 0.28, y, 3.86, 4.12, 'orangeD', hull='noside', cull='k')
    m.bx(-1.5, 1.5, y - 0.32, y, 4.12, 4.22, 'snowW', hull='noside', cull='k')
    S.strata(m, S.FIRN, S.BULGE['A'], at=y, u0=-1.5, u1=1.5, zmin=4.22)
    m.bx(-1.5, 1.5, y - 0.09, y, 6.9, 7.0, 'firn', hull='noside', cull='k')
    m.bx(-1.5, 1.5, y - 0.11, y, 7.0, 7.05, 'snowW', hull='noside', cull='k')
    m.prism([(y, 11.35), (y - 0.12, 11.42), (y - 0.3, 11.7), (y - 0.24, 12.0), (y, 12.0)], -1.5, 1.5, ['snowW'], hull='noside', skip=(4,))


def cave_upper(m, y, s, z0):
    """glacier ice above an opening on the plane y facing s * Y"""
    S.strata(m, S.CAVE, S.BULGE['B'], at=y, s=s, u0=-1.5, u1=1.5, zmin=z0)


def int_upper(m, y, s, z1, fill='panelW', band='panelG'):
    f = fq if s < 0 else bq
    f(m, -1.5, 1.5, y, DH + 0.1, z1, fill)
    f(m, -1.5, 1.5, y + s * 0.003, z1 - 0.12, z1, band)


def build_doors(pal, ao):
    # station front door [3, 2]: trench side (front, -Y) and the boot room side
    m = new(pal)
    jambs(m, 1.0, 'steelD')
    casing(m, -1.003, -1, 'orange')
    ext_upper(m, -1.0, RND(201))
    fq(m, -1.5, -OW - 0.1, -1.0, 0.0, DH + 0.1, 'panelW'); fq(m, OW + 0.1, 1.5, -1.0, 0.0, DH + 0.1, 'panelW')
    m.bx(-0.9, 0.9, -1.12, -1.0, DH + 0.25, DH + 0.6, 'orange', cull='k')
    text_front(m, 'AIRLOCK 1', 0.2, -1.123, 0.0, DH + 0.32, 'black', maxw=1.6)
    m.cy((1.35, -1.0, 2.0), 0.08, 0.08, 0.1, 'redE', seg=8, rot=(90, 0, 0))
    icicles(m, RND(202), -1.25, 1.25, -1.06, DH, 8, 0.4)
    casing(m, 1.003, 1, 'panelK', z1=DH)
    int_upper(m, 1.0, 1, CS)
    bq(m, -1.5, -OW - 0.1, 1.0, 0.0, DH + 0.1, 'panelW'); bq(m, OW + 0.1, 1.5, 1.0, 0.0, DH + 0.1, 'panelW')
    uq(m, -OW, OW, -1.0, 1.0, 0.012, 'steelD')
    for k in range(6):
        uq(m, -OW + 0.1, OW - 0.1, -0.9 + k * 0.32, -0.9 + k * 0.32 + 0.1, 0.016, 'black')
    make('DoorX', m, ao, cols=door_cols(1.0))
    # interior door [3, 1]: casings both sides, a number plate
    m = new(pal)
    jambs(m, 0.5, 'panelG')
    for s in (-1, 1):
        y = s * 0.503
        casing(m, y, s, 'panelK')
        int_upper(m, s * 0.5, s, CS)
        (fq if s < 0 else bq)(m, -1.5, -OW - 0.1, s * 0.5, 0.0, DH + 0.1, 'panelW')
        (fq if s < 0 else bq)(m, OW + 0.1, 1.5, s * 0.5, 0.0, DH + 0.1, 'panelW')
    make('DoorI', m, ao, cols=door_cols(0.5))
    # lab door [3, 2]: cave side (front): an insulated steel portal in the module's skin; lab side (back)
    for name, upper in (('DoorL', True),):
        m = new(pal)
        jambs(m, 1.0, 'steelL')
        fq(m, -1.5, 1.5, -1.0, DH + 0.1, 4.6, 'panelG')
        fq(m, -1.5, -OW - 0.1, -1.0, 0.0, DH + 0.1, 'panelG'); fq(m, OW + 0.1, 1.5, -1.0, 0.0, DH + 0.1, 'panelG')
        casing(m, -1.003, -1, 'orange', w=0.14)
        m.bx(-1.5, 1.5, -1.12, -1.0, 4.45, 4.62, 'steelD', hull='noside', cull='k')
        cave_upper(m, -1.0, -1, 4.62)
        m.bx(1.32, 1.46, -1.08, -1.0, 1.2, 1.5, 'black', cull='k')
        fq(m, 1.34, 1.44, -1.083, 1.38, 1.46, 'redE')
        S.chevrons(m, -1.5, 1.5, -1.006, 4.1, 4.3, 10, ca='yel')
        casing(m, 1.003, 1, 'steelK')
        int_upper(m, 1.0, 1, CL)
        bq(m, -1.5, -OW - 0.1, 1.0, 0.0, DH + 0.1, 'panelW'); bq(m, OW + 0.1, 1.5, 1.0, 0.0, DH + 0.1, 'panelW')
        frost_spots(m, RND(211), -1.45, 1.45, 3.0, 4.3, -1.009, 6)
        make(name, m, ao, cols=door_cols(1.0))
    # breaches [3, 2]: the wall torn open, bent panels and ice round a jagged hole
    for name in ('Breach', 'BreachIce'):
        m = new(pal)
        rnd = RND(220 if name == 'Breach' else 230)
        for sx in (-1, 1):
            a, b = sorted((sx * OW, sx * 1.5))
            m.bx(a, b, -0.99, 0.99, 0.0, DH, 'steelK', cull='bt')
            for k in range(3):   # torn panel ends sticking into the hole
                z = 0.4 + k * 0.8 + rnd.uniform(0, 0.3)
                m.bxr(sx * (OW - 0.12), rnd.uniform(-0.6, 0.6), z, 0.28, 0.04, 0.5, 'panelB' if name == 'Breach' else 'panelG', rot=(rnd.uniform(-30, 30), 0, sx * 25))
        m.bx(-1.5, 1.5, -0.99, 0.99, DH, DH + 0.3, 'iceD', cull='')
        for k in range(5):   # the ice that did it, hanging in the top of the hole
            x = -1.0 + k * 0.5
            hullp(m, [(x - 0.25, -0.9, DH), (x + 0.25, -0.9, DH), (x + 0.25, 0.9, DH), (x - 0.25, 0.9, DH),
                      (x + rnd.uniform(-0.1, 0.1), rnd.uniform(-0.5, 0.5), DH - rnd.uniform(0.25, 0.55))], 'iceM' if k % 2 else 'ice')
        for sx in (-1, 1):   # ice heaped against the jambs (inside the jamb collision)
            lump(m, rnd, sx * 1.36, -0.3, 0.22, 0.6, 1.6, 0.0, 'iceM', n=6, top=2)
        lump(m, rnd, 0.0, 0.0, 1.05, 0.95, 0.12, 0.0, 'snowL', n=8, top=3, hull='none', flat_top=True)
        if name == 'Breach':   # trench side: the facade over the hole; mess side
            ext_upper(m, -1.0, rnd)
            for sx in (-1, 1):
                fq(m, *sorted((sx * 1.5, sx * OW)), -1.0, 0.0, DH, 'panelW')
                bq(m, *sorted((sx * 1.5, sx * OW)), 1.0, 0.0, DH, 'panelW')
            int_upper(m, 1.0, 1, CS, 'panelW')
            lump(m, rnd, -0.5, -1.4, 0.7, 0.45, 0.7, 0.0, 'snowW', n=7)
        else:   # lab side (front) and the cavern side (back)
            int_upper(m, -1.0, -1, CL, 'panelW')
            for sx in (-1, 1):
                fq(m, *sorted((sx * 1.5, sx * OW)), -1.0, 0.0, DH, 'panelW')
                bq(m, *sorted((sx * 1.5, sx * OW)), 1.0, 0.0, DH, 'iceD')
            cave_upper(m, 1.0, 1, DH + 0.3)
        make(name, m, ao, cols=door_cols(1.0))
    # vault door [3, 2]: frame (front: the hall, the lab skin; back: the vault), the leaf, two damage stages, the wreck
    m = new(pal)
    jambs(m, 1.0, 'steelD')
    fq(m, -1.5, 1.5, -1.0, DH + 0.1, 4.6, 'panelG')
    fq(m, -1.5, -OW - 0.1, -1.0, 0.0, DH + 0.1, 'panelG'); fq(m, OW + 0.1, 1.5, -1.0, 0.0, DH + 0.1, 'panelG')
    casing(m, -1.003, -1, 'steelK', w=0.16)
    m.bx(-1.5, 1.5, -1.12, -1.0, 4.45, 4.62, 'steelD', hull='noside', cull='k')
    cave_upper(m, -1.0, -1, 4.62)
    m.bx(-1.0, 1.0, -1.1, -1.0, 3.05, 3.5, 'yel', cull='k')
    text_front(m, 'VAULT 3', 0.26, -1.103, 0.0, 3.13, 'black', maxw=1.8)
    casing(m, 1.003, 1, 'steelK')
    int_upper(m, 1.0, 1, CL)
    bq(m, -1.5, -OW - 0.1, 1.0, 0.0, DH + 0.1, 'panelW'); bq(m, OW + 0.1, 1.5, 1.0, 0.0, DH + 0.1, 'panelW')
    make('VaultDoor', m, ao, cols=door_cols(1.0))

    def leaf(m, dmg, rnd):
        m.bx(-OW, OW, -0.75, -0.45, 0.0, DH, 'steelL')
        for z in (0.5, 1.35, 2.2):
            m.bx(-OW + 0.08, OW - 0.08, -0.79, -0.75, z, z + 0.08, 'steel', hull='none', cull='k')
        tube(m, (0.0, -0.72, 1.35), (0.0, -0.95, 1.35), 0.05, 'steelD', seg=6)
        S.chevrons(m, -OW + 0.05, OW - 0.05, -0.753, 0.05, 0.3, 8, ca='yel')
        for ang, yy in ((0, -0.955), (90, -0.985)):   # the locking wheel's spokes
            m.bxr(0.0, yy, 1.35, 0.7, 0.02, 0.05, 'orange', rot=(0, ang, 0))
        frost_spots(m, rnd, -OW + 0.05, OW - 0.05, 0.4, DH - 0.1, -0.753, 6)
        if dmg:
            for j in range(4 * dmg):
                x, z = rnd.uniform(-1.0, 1.0), rnd.uniform(0.3, 2.4)
                r = rnd.uniform(0.06, 0.14) * (1 + dmg * 0.4)
                poly(m, [(x + math.cos(i / 6 * 6.283) * r * rnd.uniform(0.6, 1), -0.756 - j * 0.003, z + math.sin(i / 6 * 6.283) * r * rnd.uniform(0.6, 1)) for i in range(6)], 'steelD' if dmg < 2 else 'black', (0, -1, 0))
    for st, dmg in (('_Leaf', 0), ('_Leaf_D1', 1), ('_Leaf_D2', 2)):
        m = new(pal); leaf(m, dmg, RND(240 + dmg))
        make('VaultDoor' + st, m, ao, cols=[cb(-OW, -0.8, 0.0, OW, -0.4, DH)])
    m = new(pal)   # the burst leaf: a slab torn off its hinge, leaning in the opening, shards
    m.bxr(-0.85, -0.25, 0.8, 0.5, 0.3, 1.7, 'steelL', rot=(0, 18, 12))
    m.bxr(0.7, -0.6, 0.12, 1.0, 0.6, 0.06, 'steelD', rot=(0, 4, 30))
    make('VaultDoor_Broken', m, ao, cols=[cb(-1.2, -0.45, 0.0, -0.55, 0.0, 1.6)])


def build_gate(pal, ao):
    m = new(pal)
    for sx in (-1, 1):
        a, b = sorted((sx * 1.5, sx * 2.5))
        m.bx(a, b, -0.6, 0.6, 0.0, 3.44, 'steelD', cull='b')
    m.bx(-2.5, 2.5, -0.6, 0.6, 3.44, 4.1, 'steelD', cull='')
    for fy in (-1, 1):
        y = fy * 0.6
        f = fq if fy < 0 else bq
        for sx in (-1, 1):
            a, b = sorted((sx * 1.5, sx * 2.5))
            for k in range(6):
                f(m, a + 0.1, b - 0.1, y + fy * 0.003, 0.2 + k * 0.5, 0.45 + k * 0.5, 'orange' if k % 2 == 0 else 'black')
            m.bx(min(sx * 1.5, sx * 1.64), max(sx * 1.5, sx * 1.64), min(y, y + fy * 0.12), max(y, y + fy * 0.12), 0.0, 3.3, 'orangeD', cull='b')
        m.bx(-1.64, 1.64, min(y, y + fy * 0.12), max(y, y + fy * 0.12), 3.3, 3.44, 'orangeD')
        f(m, -1.3, 1.3, y + fy * 0.003, 3.55, 3.98, 'yel')
        (text_front if fy < 0 else text_back)(m, 'SHAFT K-7', 0.28, y + fy * 0.006, 0.0, 3.62, 'black', maxw=2.3)
        for sx in (-1, 1):
            m.cy((sx * 2.1, y, 3.75), 0.12, 0.12, 0.09, 'redE', seg=8, rot=(fy * -90, 0, 0))
        S.strata(m, S.CAVE, S.BULGE['C'], at=y, s=fy, u0=-2.5, u1=2.5, zmin=4.1)
        m.bx(-2.5, 2.5, min(y, y + fy * 0.1), max(y, y + fy * 0.1), 7.3, 7.4, 'iceL', hull='noside')
    make('GateFrame', m, ao, cols=[cb(-2.5, -0.6, 0, -1.5, 0.6, 3.44), cb(1.5, -0.6, 0, 2.5, 0.6, 3.44)], side=2.45)
    # the shutter: an insulated steel door leaf, frost and a hazard foot
    m = new(pal)
    Hs = 3.05
    m.box((0, 0, Hs / 2), (3.0, 0.12, Hs), 'steelL', bevel=False)
    for fy in (-1, 1):
        f = fq if fy < 0 else bq
        for z in (0.6, 1.5, 2.4):
            m.box((0, fy * 0.075, z), (2.9, 0.03, 0.07), 'steel', bevel=False)
        for k in range(10):
            f(m, -1.5 + k * 0.3, -1.2 + k * 0.3, fy * 0.063, 0.02, 0.24, 'orange' if k % 2 else 'black')
        frost_spots(m, RND(260 + fy), -1.45, 1.45, 1.6, 3.0, fy * 0.066, 5, face=fy)
    build_object(PFX + 'GateShutter', m, 0, 0.0)
    shutter = bpy.data.objects[PFX + 'GateShutter']
    strip_hull(shutter)
    m = new(pal)
    m.box((0, 0, Hs / 2), (3.0, 0.14, Hs), 'HULL', bevel=False)
    tmp = build_object('tmp_shutter_hull', m, 0, 0.02)
    hull_only(tmp)
    join_into(shutter, tmp)
    B.TRIS[PFX + 'GateShutter'] = sum(len(p.vertices) - 2 for p in shutter.data.polygons)
    # the shaft K-7 descent (trail): 1 m of wall along Blender Y, inner face +X; ice strata, steel ribs, depth marks
    for v in ('TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D', 'TrailWall_End'):
        m = new(pal)
        m.bx(-0.25, 0.25, -0.5, 0.5, 0.0, H, 'iceD', hull='noend', cull='t')
        S.strata(m, S.CAVE if v != 'TrailWall_C' else S.FIRN, S.BULGE['0'], plane='x', at=0.253, s=1, u0=-0.5, u1=0.5)
        rq(m, 0.256, -0.5, 0.5, 0.0, 0.3, 'steelK')
        if v == 'TrailWall_B':   # a steel arch rib and a lamp
            m.bx(0.25, 0.4, -0.12, 0.12, 0.0, H, 'steelD', hull='noend')
            m.bx(0.4, 0.55, -0.2, 0.2, 3.3, 3.55, 'steelK')
            rq(m, 0.553, -0.16, 0.16, 3.33, 3.52, 'lamp')
        elif v == 'TrailWall_C':   # cable tray and a pipe running down the shaft
            m.bx(0.25, 0.45, -0.5, 0.5, 2.9, 2.95, 'galv', hull='noend')
            tube(m, (0.36, -0.5, 1.4), (0.36, 0.5, 1.4), 0.08, 'orangeD', seg=8, hull='none')
        elif v == 'TrailWall_D':   # a depth plate
            rq(m, 0.256, -0.4, 0.4, 2.0, 2.6, 'orange')
            text_side(m, '-40 M', 0.3, 0.259, 0.0, 2.13, 'black', 'x+', maxw=0.7)
        make(v, m, ao, side=0.45)
    # the exit: a floor hatch down to the deep lift, ice round its coaming
    m = new(pal)
    m.cy((0, 0, 0), 1.25, 1.2, 0.12, 'steelD', seg=16)
    m.cy((0, 0, 0.12), 0.95, 0.95, 0.06, 'steel', seg=16)
    for i in range(16):
        a0, a1 = i / 16 * 2 * math.pi, (i + 1) / 16 * 2 * math.pi
        poly(m, [(math.cos(a0) * 0.98, math.sin(a0) * 0.98, 0.123), (math.cos(a0) * 1.15, math.sin(a0) * 1.15, 0.123),
                 (math.cos(a1) * 1.15, math.sin(a1) * 1.15, 0.123), (math.cos(a1) * 0.98, math.sin(a1) * 0.98, 0.123)], 'orange' if i % 2 else 'black', (0, 0, 1))
    m.bx(-0.3, 0.3, 0.9, 1.1, 0.0, 0.26, 'steelD')
    text_up(m, 'DEEP LIFT', 0.12, 0.183, 0.0, 0.0, 'paper')
    make('Hatch', m, ao, bevel=0.015)


def build_stair(pal, ao, name, W, L, rise, n, landing, snow=False):
    """a stair rising toward +Y: treads, stringers, handrails (steel) or packed snow steps with a rope (snow).
    Collision: walkable step blocks, solid to the stair's base (the nav grid)"""
    m = new(pal)
    run = (L - landing) / n
    cols = []
    rnd = RND(len(name))
    for k in range(n):
        y0 = -L / 2 + k * run
        y1 = y0 + run if k < n - 1 else L / 2
        top = (k + 1) * rise / n
        if snow:
            m.bx(-W / 2 + 0.05, W / 2 - 0.05, y0, L / 2, top - rise / n, top, 'snowL' if k % 2 else 'snowW', hull='full' if k == n - 1 else 'none', cull='b')
            uq(m, -W / 2 + 0.1, W / 2 - 0.1, y0 + 0.01, y0 + 0.08, top + 0.003, 'snowS')
        else:
            m.bx(-W / 2 + 0.08, W / 2 - 0.08, y0, y1 if k == n - 1 else y0 + run + 0.02, top - 0.05, top, 'galv', hull='none', cull='blr')
            uq(m, -W / 2 + 0.1, W / 2 - 0.1, y0 + 0.01, y0 + 0.07, top + 0.003, 'orange')
        cols.append(cb(-W / 2, y0 - (0.03 if k else 0.0), 0.0, W / 2, y1, top, True))   # overlapping a little: a nav-cell centre on a step edge stands on one
    yt = L / 2 - landing
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (W / 2 - 0.08), sx * W / 2))
        if snow:
            for k in range(3):   # marker stakes and a rope
                y = -L / 2 + 0.2 + k * (L - 0.4) / 2
                z = min(rise, (y + L / 2) / (L - landing) * rise)
                m.cy((sx * (W / 2 - 0.12), y, z), 0.03, 0.03, 1.0, 'orange', seg=5)
            m.bm_((sx * (W / 2 - 0.12), -L / 2 + 0.2, 0.95), (sx * (W / 2 - 0.12), L / 2 - 0.2, rise + 0.95), 0.025, 'yel', hull='none')
            continue
        prof = [(-L / 2, 0.0), (L / 2, 0.0), (L / 2, rise + 0.02), (L / 2 - landing, rise + 0.02), (-L / 2, 0.3)]
        m.prism(prof, x0, x1, ['steelD'], skip=(0,))
        xr = sx * (W / 2 - 0.04)
        m.bm_((xr, -L / 2 + 0.1, rise / n + 0.95), (xr, yt, rise + 0.95), 0.05, 'orange')
        m.bm_((xr, yt + 0.04, rise + 0.95), (xr, L / 2 - 0.03, rise + 0.95), 0.05, 'orange')
        m.bm_((xr, -L / 2 + 0.2, rise / n + 0.5), (xr, yt, rise + 0.5), 0.03, 'orange')
        for k in range(0, n + 1, 3):
            y = min(-L / 2 + (k + 0.5) * run, yt)
            z = min(rise, (k + 1) * rise / n)
            m.bx(xr - 0.018, xr + 0.018, y - 0.018, y + 0.018, z, z + 0.92, 'orange', hull='none', cull='bt')
        m.bx(xr - 0.018, xr + 0.018, L / 2 - 0.07, L / 2 - 0.035, rise, rise + 0.92, 'orange', hull='none', cull='bt')
    if not snow:
        m.bx(-W / 2 + 0.08, W / 2 - 0.08, L / 2 - 0.04, L / 2, 0.0, rise - 0.05, 'steelD', cull='b')
    make(name, m, ao, cols=cols)


def build_stairs(pal, ao):
    build_stair(pal, ao, 'StairSnow', 2.6, 4.0, ROOF, 7, 0.4, snow=True)
    build_stair(pal, ao, 'Stair45', 2.6, 8.0, WALK, 13, 0.8)   # runs over 0.5 m: no two nav cells (0.5 m) a step apart by more than one
    build_stair(pal, ao, 'Stair70', 2.6, 6.0, HIGH - WALK, 9, 0.6)


def build_rails(pal, ao):
    """catwalk edge rail: half module from the cell centre toward -Y, a full module, a post"""
    def rail(m, y0, y1):
        m.bx(-0.02, 0.02, y0, y1, 0.0, 0.14, 'orange', hull='noend', cull='b')
        m.bx(-0.03, 0.03, y0, y1, 1.0, 1.06, 'orange', hull='noend')
        m.bx(-0.02, 0.02, y0, y1, 0.52, 0.56, 'orange', hull='none')
    m = new(pal)
    rail(m, -0.5, -0.03)
    make('Rail', m, ao, cols=[cb(-0.06, -0.5, 0, 0.06, 0.0, 1.06)])
    m = new(pal)
    rail(m, -0.5, 0.5)
    m.bx(-0.025, 0.025, -0.025, 0.025, 0.14, 1.0, 'orange', hull='none')
    make('RailFull', m, ao, cols=[cb(-0.06, -0.5, 0, 0.06, 0.5, 1.06)])
    m = new(pal)
    m.bx(-0.035, 0.035, -0.035, 0.035, 0.0, 1.08, 'orange', cull='b')
    make('RailPost', m, ao)


def build_ceiling(pal, ao):
    """ceiling tiles hanging from their origin (the 3.7 m station / 4.4 m lab ceiling); each holds a thin box so
    flyers keep under it"""
    COL = [cb(-0.5, -0.5, 0.0, 0.5, 0.5, 0.1)]

    def tile(m, c='tileW'):
        dq(m, -0.5, 0.5, -0.5, 0.5, 0.0, c)
        dq(m, -0.5, -0.488, -0.5, 0.5, -0.003, 'panelG')
        dq(m, -0.488, 0.5, -0.5, -0.488, -0.003, 'panelG')
    m = new(pal); dq(m, -0.5, 0.5, -0.5, 0.5, 0.0, 'tileW')   # the plain tiles: one quad (the zone holds thousands),
    make('Ceil_A', m, ao, cols=COL)                          # laid in a checker of two tones
    m = new(pal); dq(m, -0.5, 0.5, -0.5, 0.5, 0.0, 'panelW')
    make('Ceil_B', m, ao, cols=COL)
    for name in ('Ceil_Light', 'Ceil_LightOn'):
        m = new(pal); tile(m)
        m.bx(-0.45, 0.45, -0.14, 0.14, -0.09, -0.003, 'panelW', cull='t')
        dq(m, -0.4, 0.4, -0.1, 0.1, -0.093, 'lampC' if name == 'Ceil_LightOn' else 'steelL')
        if name == 'Ceil_Light':
            icicles(m, RND(271), -0.4, 0.4, 0.0, -0.09, 4, 0.25)
        make(name, m, ao, cols=COL)
    g = new(pal); dq(g, -0.4, 0.4, -0.1, 0.1, -0.096, 'lamp'); make_glow('Ceil_LightOn_LED', g)
    m = new(pal)   # a fallen tile: the dark void above, the panel hanging by a corner, wires, icicles
    dq(m, -0.5, 0.5, -0.5, -0.3, 0.0, 'tileW'); dq(m, -0.5, 0.5, 0.3, 0.5, 0.0, 'tileW')
    dq(m, -0.5, -0.3, -0.3, 0.3, 0.0, 'tileW'); dq(m, 0.3, 0.5, -0.3, 0.3, 0.0, 'tileW')
    dq(m, -0.3, 0.3, -0.3, 0.3, 0.35, 'black')
    m.bx(-0.3, 0.3, -0.3, -0.29, 0.0, 0.35, 'steelK', hull='none', cull='f')
    m.bx(-0.3, 0.3, 0.29, 0.3, 0.0, 0.35, 'steelK', hull='none', cull='k')
    m.bx(-0.3, -0.29, -0.29, 0.29, 0.0, 0.35, 'steelK', hull='none', cull='l')
    m.bx(0.29, 0.3, -0.29, 0.29, 0.0, 0.35, 'steelK', hull='none', cull='r')
    m.bxr(0.12, 0.05, -0.32, 0.58, 0.58, 0.02, 'tileW', rot=(55, 10, 0), hull='none')
    m.bm_((-0.1, 0.1, 0.2), (0.0, 0.2, -0.5), 0.012, 'black', hull='none')
    m.bm_((0.1, -0.1, 0.2), (0.15, -0.05, -0.65), 0.012, 'redE', hull='none')
    icicles(m, RND(272), -0.45, 0.45, 0.4, -0.003, 2, 0.4)
    make('Ceil_Broken', m, ao, cols=COL)
    m = new(pal); tile(m)   # return-air vent with a frost beard
    m.bx(-0.3, 0.3, -0.3, 0.3, -0.04, -0.003, 'steelL', cull='t')
    for k in range(5):
        dq(m, -0.26, 0.26, -0.26 + k * 0.11, -0.22 + k * 0.11, -0.043, 'steelD')
    make('Ceil_Vent', m, ao, cols=COL)
    # ---- the cave ceiling (12 m): hanging ice, icicle clusters, a work lamp on a cable
    for v, k in (('IceHang_A', 1), ('IceHang_B', 2)):
        m = new(pal)
        rnd = RND(280 + k)
        for i in range(4):
            x, y = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8)
            L = rnd.uniform(1.2, 2.8)
            r = rnd.uniform(0.35, 0.65)
            hullp(m, [(x + math.cos(a / 6 * 6.283) * r, y + math.sin(a / 6 * 6.283) * r, i * 0.004) for a in range(6)]
                  + [(x + math.cos(a / 5 * 6.283 + 0.4) * r * 0.5, y + math.sin(a / 5 * 6.283 + 0.4) * r * 0.5, -L * 0.55) for a in range(5)]
                  + [(x + rnd.uniform(-0.1, 0.1), y + rnd.uniform(-0.1, 0.1), -L)], 'iceL' if i % 2 else 'frost')
        icicles(m, rnd, -1.3, 1.3, 1.2, 0.03, 5, 0.9)
        make(v, m, ao)
    m = new(pal)
    rnd = RND(285)
    for i in range(6):
        x, y = rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4)
        L = rnd.uniform(0.5, 1.6)
        zt = i * 0.004
        hullp(m, [(x - 0.07, y - 0.07, zt), (x + 0.07, y - 0.07, zt), (x + 0.07, y + 0.07, zt), (x - 0.07, y + 0.07, zt), (x, y, -L)], 'iceL')
    make('Icicles', m, ao)
    m = new(pal); g = new(pal)
    m.bx(-0.01, 0.01, -0.01, 0.01, -3.2, 0.0, 'black', hull='none')
    m.cy((0, 0, -3.5), 0.22, 0.08, 0.3, 'steelK', seg=8)
    dq(m, -0.15, 0.15, -0.15, 0.15, -3.504, 'lampC')
    dq(g, -0.15, 0.15, -0.15, 0.15, -3.507, 'lamp')
    make('CaveLamp', m, ao); make_glow('CaveLamp_LED', g)


def build_floors(pal, ao):
    """flat floor finishes on "@layer 0.01" (top face at the origin)"""
    def base(m, c, seam='vinylD'):
        uq(m, -0.5, 0.5, -0.5, 0.5, 0.0, c)
        if seam:
            uq(m, -0.5, -0.49, -0.5, 0.5, 0.003, seam)
            uq(m, -0.49, 0.5, -0.5, -0.49, 0.003, seam)
    m = new(pal); base(m, 'vinyl', None); make('Fl_Vinyl', m, ao)
    m = new(pal)
    for i in range(2):
        for k in range(2):
            uq(m, -0.5 + i * 0.5, i * 0.5, -0.5 + k * 0.5, k * 0.5, 0.0, 'tileW' if (i + k) % 2 else 'tileB')
    make('Fl_Mess', m, ao)
    m = new(pal); base(m, 'fabric', None); make('Fl_Carpet', m, ao)
    m = new(pal); base(m, 'tileW', None); make('Fl_Lab', m, ao)
    m = new(pal); base(m, 'steel', None)
    uq(m, -0.5, -0.47, -0.5, 0.5, 0.003, 'steelD')
    make('Fl_Plate', m, ao)
    m = new(pal); base(m, 'black', None)
    for k in range(6):
        uq(m, -0.48, 0.48, -0.47 + k * 0.16, -0.39 + k * 0.16, 0.003, 'galv')
    make('Fl_Grate', m, ao)
    for name, rs in (('Fl_Snow', 291), ('Fl_Papers', 292)):
        m = new(pal); base(m, 'vinyl')
        rnd = RND(rs)
        if name == 'Fl_Snow':
            disc(m, rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0.006, 0.46, 'snowL', seg=9, jag=[1.0, 0.8, 0.95, 0.75, 1.0, 0.85, 0.9, 0.7, 1.0])
            disc(m, 0.1, -0.05, 0.009, 0.28, 'snowW', seg=7, jag=[1.0, 0.8, 0.9, 0.7, 1.0, 0.85, 0.75])
        else:
            for i in range(5):
                x, y, a = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 3.14)
                c, s_ = math.cos(a), math.sin(a)
                pts = [(x + c * dx - s_ * dy, y + s_ * dx + c * dy, 0.004 + i * 0.003) for dx, dy in ((-0.1, -0.14), (0.1, -0.14), (0.1, 0.14), (-0.1, 0.14))]
                poly(m, pts, 'paper' if i % 2 else 'paperY', (0, 0, 1))
        make(name, m, ao)
    m = new(pal); base(m, 'steelD', None)
    for k in range(4):
        poly(m, [(-0.5 + k * 0.25, 0.3, 0.003), (-0.375 + k * 0.25, 0.3, 0.003), (-0.25 + k * 0.25, 0.5, 0.003), (-0.375 + k * 0.25, 0.5, 0.003)], 'yel', (0, 0, 1))
    make('Fl_Hazard', m, ao)
    m = new(pal); uq(m, -0.5, 0.5, -0.5, 0.5, 0.0, 'ice')
    for (a, b) in (((-0.4, -0.3), (0.1, 0.2)), ((0.1, 0.2), (0.45, 0.05)), ((0.1, 0.2), (0.0, 0.48))):
        poly(m, [(a[0], a[1], 0.003), (b[0], b[1], 0.003), (b[0] + 0.012, b[1] + 0.012, 0.003), (a[0] + 0.012, a[1] + 0.012, 0.003)], 'iceL', (0, 0, 1))
    make('Fl_Ice', m, ao)
