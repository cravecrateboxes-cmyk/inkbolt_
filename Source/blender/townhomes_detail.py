"""kit-townhomes modelled detail (tactical look plan Stage 11): the trims and fittings a painted suburban house really has.

Facades: corner boards, base board, belly band, window casings with head caps, sash stiles, sill aprons and shutters
with rails and hinge straps, door surrounds (plinth blocks, head caps, thresholds), kick plates, lever plates, hinges,
carriage-lamp backplates and mullions, gutters on hangers, downpipes on straps, utility meters, garage-door joints
and handles; porches: post bases and caps, rail caps, step nosings; street: fence post collars and brackets, lamp
rings and mullions, the mailbox latch, gatehouse sills and hip rolls, barrier base plates, gate hinges.

Palette: only cells that are not house-paint cells are used for new parts ('trim', 'trimD', 'iron', 'steel', 'chrome',
'stoneD') except the shutter rails, which use 'shut' so a repainted shutter keeps its frame. Same rules as every detail
pass: hull='none' (no outline shell), >= 3 mm proud, embedded 3 mm, horizontal runs inset 5 mm from the piece sides.
Nothing here changes a piece's origin, footprint, collision boxes or the parts already drawn: it only adds shapes.
Facade helpers work in the facade frame (m.parent = frame_front() etc.): the wall plane is y = 0, out is -Y.
"""
import math

from parking_base import fq, bq, lq, rq  # noqa: F401

EMB = 0.003
INS = 0.005


def fb(m, x0, x1, z0, z1, d0, d1, c, cull='', sides=False):
    """box d0..d1 proud of the facade plane (d0 may be -EMB: sunk into the wall). The kit's GLB is size-capped, so only
    the faces a player can see are kept: the front, and the top unless cull has 't'; sides=True keeps the end faces"""
    m.bx(x0, x1, -d1, -d0, z0, z1, c, hull='none', cull=cull + 'kb' + ('' if sides else 'lr'))


def bx(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


# ------------------------------------------------------------------------------------------------ openings
def window_detail(m, x0, x1, z0, z1, shutters=False, sill=True, arch=False, flowerbox=False):
    """a head cap over the casing and hinge straps on the shutters (facade frame)"""
    if not arch:
        fb(m, x0 - 0.12, x1 + 0.12, z1 + 0.09, z1 + 0.125, -EMB, 0.034, 'trim')
    if shutters:
        w = (x1 - x0) * 0.45
        for (a, b, inner) in ((x0 - 0.12 - w, x0 - 0.12, 1), (x1 + 0.12, x1 + 0.12 + w, -1)):
            ie = b if inner > 0 else a
            ha, hb = (ie - 0.16, ie - 0.01) if inner > 0 else (ie + 0.01, ie + 0.16)
            fb(m, ha, hb, z1 - 0.2, z1 - 0.16, 0.012, 0.032, 'iron', cull='t')


def door_detail(m, x0, x1, z0, z1, open_=False, arch=False, transom=True, hinges=True):
    """a head cap; closed doors also get a threshold, kick plate, lever plate and hinges (facade frame)"""
    if not arch:
        fb(m, x0 - 0.19, x1 + 0.19, z1 + 0.16, z1 + 0.2, -EMB, 0.044, 'trim')
    if open_:
        return
    fb(m, x0 + 0.06, x1 - 0.06, z0 + 0.04, z0 + 0.27, 0.0, 0.026, 'steel', cull='t')
    fb(m, x1 - 0.16, x1 - 0.08, z0 + 0.88, z0 + 1.14, 0.0, 0.026, 'chrome', cull='t')
    if hinges:
        zt = z1 - (0.4 if transom else 0.0) - (0.2 if arch else 0.0)
        for zz in (z0 + 0.25, zt - 0.4):
            fb(m, x0 + 0.005, x0 + 0.04, zz, zz + 0.1, 0.0, 0.02, 'iron', cull='t')


def lamp_detail(m, x, z):
    """a backplate and a mullion cross over the glass of a carriage lamp (facade frame)"""
    fb(m, x - 0.085, x + 0.085, z - 0.21, z + 0.21, -EMB, 0.012, 'iron', cull='t')
    fb(m, x - 0.007, x + 0.007, z - 0.09, z + 0.12, 0.218, 0.232, 'iron', cull='t')
    fb(m, x - 0.06, x + 0.06, z + 0.012, z + 0.026, 0.218, 0.236, 'iron', cull='t')


# ------------------------------------------------------------------------------------------------ facade bands
def siding_trim(m, x0, x1, eave, gf, uf, gaps):
    """3D corner boards, a base board (stopping at `gaps`, x ranges of the openings that reach the floor) and a belly
    band between the floors, over a lap-siding facade"""
    fb(m, x0 + INS, x0 + 0.145, gf + EMB, eave - EMB, -EMB, 0.025, 'trim', cull='t')
    fb(m, x1 - 0.145, x1 - INS, gf + EMB, eave - EMB, -EMB, 0.025, 'trim', cull='t')
    xs = [x0 + 0.145] + [v for g in gaps for v in g] + [x1 - 0.145]
    for a, b in zip(xs[0::2], xs[1::2]):
        if b - a > 0.1:
            fb(m, a, b, gf + 0.045, gf + 0.14, -EMB, 0.022, 'trim')
    fb(m, x0 + 0.145, x1 - 0.145, uf - 0.2, uf - 0.09, -EMB, 0.035, 'trim')


def brick_trim(m, x0, x1, gf, gaps):
    """a stone water table along the foot of a brick facade, stopping at the door gaps"""
    xs = [x0 + INS] + [v for g in gaps for v in g] + [x1 - INS]
    for a, b in zip(xs[0::2], xs[1::2]):
        if b - a > 0.1:
            fb(m, a, b, gf + 0.045, gf + 0.12, -EMB, 0.03, 'stoneD')


# ------------------------------------------------------------------------------------------------ eaves and services
def gutter_run(m, x0, x1, ya, za, side):
    """a gutter on the fascia at an eave: side -1 front (fascia outer face at ya - 0.04), +1 back (ya + 0.04); a
    hanger every 1.5 m (piece frame; only the outward face and the top are kept)"""
    yo = ya + side * 0.04 - side * EMB      # sunk into the fascia
    y1 = ya + side * 0.11
    a, b = (min(yo, y1), max(yo, y1))
    out = 'k' if side < 0 else 'f'
    bx(m, x0 + INS, x1 - INS, a, b, za - 0.04, za + 0.1, 'trimD', cull='blr' + out)
    n = max(2, int((x1 - x0) / 1.5))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        s0, s1 = (y1 - 0.003, y1 + 0.007) if side > 0 else (y1 - 0.007, y1 + 0.003)
        bx(m, x - 0.014, x + 0.014, s0, s1, za - 0.045, za + 0.105, 'steel', cull='tblr' + out)


def downpipe(m, x, z0, z1, jog=None):
    """a rectangular downpipe on two strap brackets (facade frame); jog: the gutter's outer depth, where an elbow
    runs back in to the pipe"""
    ztop = z1 - 0.07 + EMB if jog else z1
    fb(m, x - 0.035, x + 0.035, z0 + 0.1, ztop, 0.015, 0.085, 'trimD', cull='t', sides=True)
    fb(m, x - 0.039, x + 0.039, z0, z0 + 0.1, 0.015, 0.17, 'trimD', cull='', sides=True)     # shoe kicking out
    for z in (z0 + 0.5, z0 + 1.7):
        fb(m, x - 0.045, x + 0.045, z, z + 0.035, -EMB, 0.1, 'steel', cull='t')
    if jog:
        fb(m, x - 0.031, x + 0.031, z1 - 0.07, z1 + EMB, 0.015, jog - 0.01, 'trimD', cull='t', sides=True)


def meter(m, x, z):
    """an electric meter on its backplate with a conduit run up the wall (facade frame)"""
    fb(m, x - 0.15, x + 0.15, z - 0.2, z + 0.2, -EMB, 0.07, 'steel')
    fb(m, x - 0.09, x + 0.09, z - 0.09, z + 0.09, 0.07, 0.092, 'chrome', cull='t')
    fb(m, x - 0.018, x + 0.018, z + 0.2 - EMB, z + 0.95, 0.02, 0.055, 'steel', cull='t')


def hose_bib(m, x, z):
    fb(m, x - 0.05, x + 0.05, z - 0.05, z + 0.05, -EMB, 0.012, 'steel', cull='t')
    fb(m, x - 0.014, x + 0.014, z - 0.014, z + 0.014, 0.0, 0.1, 'steel', cull='t')


def garage_door_detail(m, g0, g1, zrows, handle_x, ztop):
    """sectional joints, side tracks and a pull handle over a painted garage door (facade frame, face at d 0.018-0.026)"""
    for z in zrows:
        fb(m, g0 + 0.005, g1 - 0.005, z - 0.006, z + 0.006, 0.0, 0.026, 'iron', cull='t')
    for (a, b) in ((g0 - 0.005, g0 + 0.03), (g1 - 0.03, g1 + 0.005)):
        fb(m, a, b, 0.0 + 0.004, ztop, 0.0, 0.03, 'iron', cull='t')
    fb(m, handle_x - 0.14, handle_x + 0.14, 1.0, 1.05, 0.036, 0.05, 'steel', cull='t')
    for dx in (-0.12, 0.12):
        fb(m, handle_x + dx - 0.012, handle_x + dx + 0.012, 0.985, 1.065, 0.0, 0.04, 'chrome', cull='t')


# ------------------------------------------------------------------------------------------------ porches (piece frame)
def porch_post(m, x, y, ztop, zbase):
    """a square plinth at the foot of a round post and a capital under the beam"""
    bx(m, x - 0.11, x + 0.11, y - 0.11, y + 0.11, zbase - EMB, zbase + 0.2, 'trim', cull='b')


def nosing(m, x0, x1, y_edge, ztop, side=-1, h=0.045, c='stoneD'):
    """a bullnose lip along the front edge of a step: side -1 = the step's face looks toward -Y"""
    y = y_edge
    a, b = (y - 0.03, y + EMB) if side < 0 else (y - EMB, y + 0.03)
    bx(m, x0 + INS, x1 - INS, a, b, ztop - h - 0.003, ztop - 0.004, c, cull='blrk')


def rail_cap(m, x0, x1, y, ztop, w=0.14, c='trim'):
    """a capping board on a porch rail's top bar (rail along x at y): front and top only"""
    bx(m, x0 + INS, x1 - INS, y - w / 2, y + w / 2, ztop - EMB, ztop + 0.028, c, cull='blrk')


def rail_cap_y(m, y0, y1, x, ztop, w=0.14, c='trim'):
    bx(m, x - w / 2, x + w / 2, y0, y1, ztop - EMB, ztop + 0.028, c, cull='bfk')


# ------------------------------------------------------------------------------------------------ street and site
def courses(m, hw, hd, zs, c='stoneD', t=0.012):
    """mortar joint lines round a square stone post (half sizes hw x hd), painted 4 mm proud"""
    for z in zs:
        fq(m, -hw + 0.01, hw - 0.01, -hd - 0.004, z - t, z + t, c)
        bq(m, -hw + 0.01, hw - 0.01, hd + 0.004, z - t, z + t, c)
        lq(m, -hw - 0.004, -hd + 0.01, hd - 0.01, z - t, z + t, c)
        rq(m, hw + 0.004, -hd + 0.01, hd - 0.01, z - t, z + t, c)


def skirt(m, x, y, hw, hd, h, c='stoneD', grow=0.025):
    """a plinth skirt round the foot of a square post"""
    bx(m, x - hw - grow, x + hw + grow, y - hd - grow, y + hd + grow, 0.0, h, c, cull='b')


def ring(m, x, y, z, r, h, c='steel', seg=8):
    m.cy((x, y, z), r, r, h, c, seg=seg, hull='none')


def bolt_plate(m, x, y, z, face, c='steel', s=0.028, out=0.009, cull=''):
    """a square bolt head on a face of a part; face '-y' '+y' '-x' '+x' '+z'"""
    h = s / 2
    x0, x1, y0, y1, z0, z1 = x - h, x + h, y - h, y + h, z - h, z + h
    if face == '-y':
        y0, y1 = y - out, y + EMB
    elif face == '+y':
        y0, y1 = y - EMB, y + out
    elif face == '-x':
        x0, x1 = x - out, x + EMB
    elif face == '+x':
        x0, x1 = x - EMB, x + out
    else:
        z0, z1 = z - EMB, z + out
    bx(m, x0, x1, y0, y1, z0, z1, c, cull=cull)
