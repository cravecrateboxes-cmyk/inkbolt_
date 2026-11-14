"""kit-city2 modelled detail (tactical look plan Stage 11): the street-level fittings a player sees up close.

Brownstone / tenement / loft / deco facades: shop-window frames with depth, sills and shutter boxes, kick-plate
screws, basement grilles, doors with surrounds, raised panels, sash bars, pulls, kick plates, sconces and (brownstone
and tenement) a two-step stoop with railings and spear finials, drainpipes on stand-off straps, meter boxes and
conduit, louvres, window sash rails, sill corbels and keystones, dentil and corbel courses, fire-escape braces and
balusters. The elevated railway: rivet rows, splice plates, column base plates with nuts, built-up column ribs and
gusset plates. Street props: lamp and hydrant fittings, newsboxes, mailbox, bench, bins, steam stack, subway railings,
newsstand trim, billboard bolts, cellar-hatch hardware.

Same rules as the other kits' detail passes: every part is hull='none' (no outline shell), stands at least 3 mm proud
and sinks 3 mm into what it sits on; the facade plane is y = -0.5 (F(d) = d proud of it). Nothing here changes a
piece's origin, footprint, collision boxes or the parts already drawn: it only adds shapes.
"""
import math

from mathutils import Matrix

EMB = 0.003
G_H, U_H = 4.2, 3.2
EL_Z = 5.4


def F(d):
    return -0.5 - d


def D(m, x0, x1, d, z0, z1, c, d0=0.022, cull='k'):
    """facade fitting: front face d proud of the facade plane, back sunk EMB into a host whose face is d0 proud"""
    m.bx(x0, x1, F(d), F(d0) + EMB, z0, z1, c, hull='none', cull=cull)


def B(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def bolt(m, x, z, d, c='chrome', s=0.024, d0=0.022):
    D(m, x - s / 2, x + s / 2, d, z - s / 2, z + s / 2, c, d0)


# ================================================================ pipes
def pipe_strap(m, x, z, dfront, r, c='trim'):
    cy = F(dfront - r)
    D(m, x - r - 0.008, x + r + 0.008, dfront + 0.008, z - 0.015, z + 0.015, c, d0=dfront - 2 * r + 0.004, cull='ktb')
    D(m, x - 0.012, x + 0.012, dfront - 2 * r + 0.008, z - 0.015, z + 0.015, c, d0=0.0)


def vpipe(m, x, z0, z1, dfront, r, straps, c='cornice', sc='trim', hopper=True):
    """a drainpipe (front dfront proud) on stand-off straps, with a shoe at the foot and a hopper head"""
    m.cy((x, F(dfront - r), z0), r, r, z1 - z0, c, seg=8, hull='none', caps=False)
    for z in straps:
        pipe_strap(m, x, z, dfront, r, sc)
    D(m, x - r - 0.01, x + r + 0.01, dfront + 0.03, z0, z0 + 0.12, sc, d0=0.0, cull='kt')            # shoe
    if hopper:
        D(m, x - 0.06, x + 0.06, dfront + 0.04, z1 - 0.14, z1, sc, d0=0.0, cull='kt')                   # hopper head
        D(m, x - 0.075, x + 0.075, dfront + 0.05, z1, z1 + 0.04, sc, d0=0.0, cull='kb')


# ================================================================ ground floor
def kick_screws(m, xs):
    for x in xs:
        bolt(m, x, 0.31, 0.047, d0=0.04, s=0.022)


def band_bolts(m):
    for x in (-0.462, 0.462):
        bolt(m, x, 3.65, 0.127, d0=0.117, s=0.026)


def grille(m, x, z, w, h, d=0.062, d0=0.04):
    """a cast grille set into the kick plate: frame, dark void, bars"""
    t = 0.022
    D(m, x - w / 2, x + w / 2, d, z - h / 2, z - h / 2 + t, 'elD', d0)
    D(m, x - w / 2, x + w / 2, d, z + h / 2 - t, z + h / 2, 'elD', d0)
    D(m, x - w / 2, x - w / 2 + t, d, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, 'elD', d0)
    D(m, x + w / 2 - t, x + w / 2, d, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, 'elD', d0)
    D(m, x - w / 2 + t, x + w / 2 - t, d - 0.01, z - h / 2 + t, z + h / 2 - t, 'ink', d0, cull='ktblr')
    n = max(3, int((w - 2 * t) / 0.05))
    for i in range(n):
        xx = x - w / 2 + t + (w - 2 * t) * (i + 0.5) / n
        D(m, xx - 0.007, xx + 0.007, d - 0.002, z - h / 2 + t + 0.003, z + h / 2 - t - 0.003, 'steel', d0, cull='ktb')


def win_ground(m, mat):
    kick_screws(m, (-0.46, -0.2, 0.2, 0.46))
    band_bolts(m)
    for sx in (-1, 1):                                                              # frame jambs, depth
        x0, x1 = sorted((sx * 0.40, sx * 0.44))
        D(m, x0, x1, 0.088, 0.357, 3.0, 'trim', cull='ktb')
    D(m, -0.44, 0.44, 0.088, 3.0, 3.07, 'trim', cull='kt')                         # head
    D(m, -0.455, 0.455, 0.112, 0.357, 0.42, 'stone', cull='kb')                      # sill
    D(m, -0.45, 0.45, 0.078, 3.09, 3.23, 'steel', cull='ktb')                       # roller shutter box
    D(m, -0.42, -0.3, 0.083, 3.12, 3.2, 'ink', d0=0.075, cull='ktb')                # its slot
    grille(m, 0.25, 0.2, 0.26, 0.18)                                                # basement grille in the kick plate


def stoop(m):
    """two shallow steps with a railing each side: posts, sloped handrail, balusters, spear finials"""
    D(m, -0.42, 0.42, 0.30, 0.0, 0.09, 'graniteD', d0=0.02, cull='kb')            # lower step
    D(m, -0.40, 0.40, 0.17, 0.0, 0.17, 'granite', d0=0.02, cull='kb')             # upper step
    for sx in (-1, 1):
        x = sx * 0.455
        xa, xb = x - 0.013, x + 0.013
        # newel posts at the foot (tall) and against the wall
        B(m, xa - 0.007, xb + 0.007, F(0.29), F(0.25), 0.08, 0.92, 'elD', cull='b')
        B(m, xa - 0.007, xb + 0.007, F(0.075), F(0.035), 0.16, 1.02, 'elD', cull='b')
        # handrail from the foot post to the wall post
        m.bm_((x, F(0.27), 0.93), (x, F(0.055), 1.0), 0.026, 'elD', hull='none')
        for dd in (0.2, 0.12):                                                  # balusters
            z0 = 0.16 if dd < 0.17 else 0.08
            zt = 0.93 + (0.27 - dd) / 0.215 * 0.07
            B(m, x - 0.006, x + 0.006, F(dd) - 0.006, F(dd) + 0.006, z0 - 0.003, zt, 'elD', cull='tb')
        for dd, zt in ((0.27, 0.93), (0.055, 1.02)):                                    # spear finials
            m.cy((x, F(dd), zt + 0.02), 0.026, 0.0, 0.1, 'elD', seg=4, hull='none')


def door_ground(m, mat):
    kick_screws(m, (-0.47, 0.47))
    band_bolts(m)
    for sx in (-1, 1):                                                              # stone surround, depth
        x0, x1 = sorted((sx * 0.36, sx * 0.435))
        D(m, x0, x1, 0.088, 0.0, 3.0, 'stone', cull='kb')
    D(m, -0.445, 0.445, 0.104, 3.0, 3.13, 'stone', cull='kb')                       # lintel
    D(m, -0.07, 0.07, 0.118, 3.0, 3.2, 'ironD', d0=0.1, cull='kb')                  # keystone
    # raised panels below the glazing
    for a, b in ((-0.25, -0.03), (0.03, 0.25)):
        D(m, a, b, 0.064, 0.5, 0.88, 'trunk', d0=0.05, cull='k')
    # glazing bars on the lit panel
    for a, b, z0, z1 in ((-0.23, 0.23, 2.15, 2.18), (-0.23, 0.23, 0.92, 0.95)):
        D(m, a, b, 0.07, z0, z1, 'trim', d0=0.055, cull='k')
    D(m, -0.23, -0.2, 0.07, 0.95, 2.15, 'trim', d0=0.055, cull='k')
    D(m, 0.2, 0.23, 0.07, 0.95, 2.15, 'trim', d0=0.055, cull='k')
    D(m, -0.012, 0.012, 0.078, 0.95, 2.15, 'trim', d0=0.055, cull='k')
    D(m, -0.2, 0.2, 0.074, 1.54, 1.57, 'trim', d0=0.055, cull='k')
    # kick plate, pull, lock, hinges
    D(m, -0.27, 0.27, 0.07, 0.19, 0.42, 'bronze', d0=0.05, cull='kb')
    for z in (1.04, 1.30):                                                           # pull handle on stand-offs
        D(m, 0.262, 0.278, 0.092, z - 0.012, z + 0.012, 'chrome', d0=0.05)
    D(m, 0.265, 0.275, 0.104, 1.0, 1.34, 'chrome', d0=0.09)
    D(m, 0.225, 0.265, 0.082, 1.44, 1.5, 'bronze', d0=0.05)                         # lock plate
    D(m, 0.238, 0.252, 0.086, 1.455, 1.485, 'ink', d0=0.08)
    for z in (0.4, 2.0):
        D(m, -0.318, -0.282, 0.074, z - 0.06, z + 0.06, 'bronzeD', d0=0.05)          # hinge leaves
    # intercom plate and a wall lantern either side
    D(m, 0.442, 0.492, 0.05, 1.15, 1.35, 'bronze')
    D(m, 0.457, 0.477, 0.057, 1.27, 1.31, 'litW', d0=0.05)
    D(m, 0.457, 0.477, 0.057, 1.19, 1.23, 'ink', d0=0.05)
    D(m, -0.49, -0.448, 0.05, 2.0, 2.34, 'bronzeD')
    D(m, -0.485, -0.455, 0.1, 2.06, 2.28, 'litW', d0=0.046)
    D(m, -0.486, -0.452, 0.108, 2.28, 2.31, 'bronzeD', d0=0.05)
    if mat in ('B', 'K'):
        stoop(m)
    else:
        D(m, -0.43, 0.43, 0.115, 0.0, 0.055, 'stone', d0=0.02, cull='kb')           # plain threshold


def pier_ground(m, mat, n, name):
    kick_screws(m, (-0.46, 0.46))
    band_bolts(m)
    grille(m, -0.26, 0.2, 0.28, 0.18)
    # meter box with a lid, hasp and a conduit going up
    D(m, -0.46, -0.2, 0.1, 0.61, 0.95, 'steel', cull='kb')
    D(m, -0.44, -0.22, 0.108, 0.63, 0.93, 'silver', d0=0.099, cull='kb')
    D(m, -0.28, -0.24, 0.118, 0.77, 0.81, 'chrome', d0=0.107)
    m.cy((-0.42, F(0.04), 0.95), 0.016, 0.016, 1.1, 'steel', seg=6, hull='none', caps=False)
    for z in (1.3, 1.9):
        D(m, -0.44, -0.4, 0.052, z - 0.012, z + 0.012, 'trim')
    # louvred vent beside the column
    vx, vz, vw, vh = 0.28, 1.6, 0.2, 0.3
    t = 0.022
    D(m, vx - vw / 2, vx + vw / 2, 0.038, vz - vh / 2, vz - vh / 2 + t, 'elD')
    D(m, vx - vw / 2, vx + vw / 2, 0.038, vz + vh / 2 - t, vz + vh / 2, 'elD')
    D(m, vx - vw / 2, vx - vw / 2 + t, 0.038, vz - vh / 2 + t + 0.003, vz + vh / 2 - t - 0.003, 'elD')
    D(m, vx + vw / 2 - t, vx + vw / 2, 0.038, vz - vh / 2 + t + 0.003, vz + vh / 2 - t - 0.003, 'elD')
    D(m, vx - vw / 2 + t, vx + vw / 2 - t, 0.029, vz - vh / 2 + t, vz + vh / 2 - t, 'ink', cull='ktblr')
    for i in range(4):
        zz = vz - vh / 2 + t + (vh - 2 * t) * (i + 0.5) / 4
        D(m, vx - vw / 2 + t - 0.005, vx + vw / 2 - t + 0.005, 0.034, zz - 0.007, zz + 0.007, 'silver', d0=0.02, cull='kb')
    if name == 'Pier':     # the downpipe runs the full height of the building, in front of the sign band
        T = G_H + (n - 1) * U_H
        straps = [0.45, 1.8] + [4.6 + k * 2.6 for k in range(int((T - 0.7 - 4.6) / 2.6) + 1)]
        vpipe(m, 0.43, 0.05, T - 0.4, 0.22, 0.04, straps)
    else:                  # escape modules: a short run to the sign band
        vpipe(m, 0.43, 0.05, 3.22, 0.11, 0.04, (0.45, 1.5, 2.55), hopper=False)
        D(m, 0.385, 0.475, 0.12, 3.17, 3.25, 'trim', d0=0.05, cull='kt')


def ground_detail(m, mat, kind, name, n):
    if kind == 'win':
        win_ground(m, mat)
    elif kind == 'door':
        door_ground(m, mat)
    elif kind == 'pier':
        pier_ground(m, mat, n, name)


# ================================================================ upper floors
def window_detail(m, mat, x0, x1, z0, z1):
    zm = (z0 + z1) / 2
    D(m, x0, x1, 0.05, zm - 0.015, zm + 0.015, 'trim', d0=0.03, cull='kt')            # sash meeting rail
    if mat == 'B':
        for xc in (x0 + 0.02, x1 - 0.02):                                           # stepped corbels under the sill
            D(m, xc - 0.03, xc + 0.03, 0.062, z0 - 0.2, z0 - 0.097, 'stone', d0=0.0, cull='kt')
            D(m, xc - 0.025, xc + 0.025, 0.044, z0 - 0.28, z0 - 0.2, 'stone', d0=0.0, cull='kt')
        xc = (x0 + x1) / 2
        D(m, xc - 0.045, xc + 0.045, 0.096, z1 + 0.04, z1 + 0.28, 'brownL', d0=0.075, cull='kt')   # keystone


def deco_detail(m, z0):
    D(m, -0.25, 0.25, 0.05, z0 + 1.43, z0 + 1.46, 'trim', d0=0.03, cull='kt')
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.3, sx * 0.34))
        D(m, x0, x1, 0.03, z0 + 2.62, z0 + 3.1, 'stone', d0=0.014, cull='ktb')


def cornice_detail(m, mat, n):
    T = G_H + (n - 1) * U_H
    if mat == 'B':
        for i in range(8):
            x = -0.4375 + i * 0.125
            if abs(x + 0.28) < 0.11 or abs(x - 0.22) < 0.11:
                continue
            D(m, x - 0.035, x + 0.035, 0.09, T - 0.12, T + 0.003, 'cornice', d0=0.0, cull='kt')
    elif mat == 'K':
        for i in range(7):
            x = -0.42 + i * 0.14
            D(m, x - 0.035, x + 0.035, 0.095, T - 0.12, T + 0.003, 'brick', d0=0.0, cull='kt')


def escape_detail(m, n, part):
    for k in range(1, n):
        z = G_H + (k - 1) * U_H + 0.08
        for x in (-0.375, 0.0, 0.375):                                      # more balusters
            B(m, x - 0.007, x + 0.007, -1.392, -1.378, z - 0.003, z + 0.9, 'trim', cull='tb')
        for y in (-0.8, -1.2):                                                # grating cross bars
            B(m, -0.495, 0.495, y - 0.015, y + 0.015, z - 0.003, z + 0.012, 'trim', cull='b')
        for sx in (-1, 1):                                                            # wall brackets
            m.bm_((sx * 0.4, -0.52, z - 0.95), (sx * 0.4, -1.3, z - 0.09), 0.04, 'trim', hull='none')


def portal_detail(m, mat):
    for z in (8.5, 8.78):                                                           # rivet rows on the El lintel
        for i in range(8):
            x = -0.4375 + i * 0.125
            D(m, x - 0.014, x + 0.014, 0.193, z - 0.014, z + 0.014, 'elD', d0=0.177, cull='kt')


def pilaster_detail(m, n):
    T = G_H + (n - 1) * U_H
    straps = [0.5, 1.8] + [4.6 + k * 2.6 for k in range(int((T - 0.8 - 4.6) / 2.6) + 1)]
    vpipe(m, -0.3, 0.1, T - 0.5, 0.24, 0.04, straps)


# ================================================================ the El
def rivet(m, x, y, z, sx, c='elD', s=0.034, p=0.008):
    x0, x1 = sorted((x - sx * EMB, x + sx * p))
    m.bx(x0, x1, y - s / 2, y + s / 2, z - s / 2, z + s / 2, c, hull='none', cull='l' if sx > 0 else 'r')


def rivet_under(m, x, y, z, c='elD', s=0.034, p=0.008):
    m.bx(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z - p, z + EMB, c, hull='none', cull='t')


def gusset(m, cx, y, sx, c='elD'):
    """a triangular plate in the corner between the column, the cross girder and the knee brace"""
    pts = [(sx * 1.285, EL_Z - 0.597), (sx * 1.285, EL_Z - 1.12), (sx * 0.90, EL_Z - 0.597)]
    m.parent = Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    m.prism([(-gx, gz) for gx, gz in pts], -0.008, 0.008, [c], hull='none')
    m.parent = Matrix.Identity(4)


def el_detail(m, y0, y1, cols):
    splices = []
    s = y0 + 3.0
    while s < y1 - 1.0:
        splices.append(s)
        s += 3.0
    for sx in (-1, 1):
        xo = sx * 1.6
        k = 0
        while y0 + 0.5 + k * 0.5 < y1 - 0.2:
            y = y0 + 0.5 + k * 0.5
            k += 1
            if any(abs(y - sp) < 0.25 for sp in splices):
                continue
            for z in (EL_Z + 0.13, EL_Z + 0.97):
                rivet(m, xo, y, z, sx)
            rivet_under(m, sx * 1.47, y, EL_Z - 0.08)
        for sp in splices:                                                       # splice plate, riveted
            x0, x1 = sorted((xo - sx * EMB, xo + sx * 0.012))
            m.bx(x0, x1, sp - 0.17, sp + 0.17, EL_Z + 0.06, EL_Z + 1.04, 'elD', hull='none', cull='l' if sx > 0 else 'r')
            for dy in (-0.09, 0.09):
                for z in (0.2, 0.42, 0.64, 0.86):
                    rivet(m, xo + sx * 0.012, sp + dy, EL_Z + z, sx, c='el', s=0.03, p=0.007)
    for y in cols:
        for sx in (-1, 1):
            cx = sx * 1.47
            B(m, cx - 0.3, cx + 0.3, y - 0.3, y + 0.3, 0.0, 0.075, 'graniteD', cull='b')       # grout pad
            for ax in (-0.215, 0.215):                                                 # anchor nuts
                for ay in (-0.215, 0.215):
                    B(m, cx + ax - 0.025, cx + ax + 0.025, y + ay - 0.025, y + ay + 0.025, 0.347, 0.395, 'elD', cull='b')
            zt = EL_Z - 0.12
            for a in (-0.09, 0.09):                                                    # built-up column ribs
                xs = cx + sx * 0.18
                xa, xb = sorted((xs - sx * EMB, xs + sx * 0.014))
                B(m, xa, xb, y + a - 0.015, y + a + 0.015, 0.42, zt, 'elD', cull='tb')
                for sy in (-1, 1):
                    ys = y + sy * 0.18
                    ya, yb = sorted((ys - sy * EMB, ys + sy * 0.014))
                    B(m, cx + a - 0.015, cx + a + 0.015, ya, yb, 0.42, zt, 'elD', cull='tb')
            gusset(m, cx, y, sx)


# ================================================================ street props (model frame, walk slab top at z = 0.05)
def nut(m, x, y, z, s=0.036, h=0.03, c='elD'):
    B(m, x - s / 2, x + s / 2, y - s / 2, y + s / 2, z - EMB, z + h, c, cull='b')


def base_plate(m, r, t=0.028, c='elD', bolts=True, bs=0.034):
    """square base plate under a pole, with four anchor nuts at the corners"""
    B(m, -r, r, -r, r, 0.047, 0.047 + t, c, cull='b')
    if bolts:
        k = r - 0.032
        for sx in (-1, 1):
            for sy in (-1, 1):
                nut(m, sx * k, sy * k, 0.047 + t, bs)


def lamp_detail(m):
    base_plate(m, 0.2)
    m.cy((0, 0, 0.547), 0.105, 0.1, 0.045, 'elD', seg=8, hull='none', caps=False)           # collar over the base cone
    B(m, -0.05, 0.05, -0.115, -0.077, 0.85, 1.2, 'elD', cull='k')                           # hand-hole cover
    for z in (0.88, 1.17):
        for sx in (-1, 1):
            B(m, sx * 0.035 - 0.009, sx * 0.035 + 0.009, -0.122, -0.113, z - 0.009, z + 0.009, 'chrome', cull='k')
    m.cy((0, 0, 5.9), 0.075, 0.075, 0.05, 'elD', seg=8, hull='none', caps=False)
    m.cy((0, -1.75, 6.553), 0.035, 0.035, 0.06, 'steel', seg=6, hull='none')                 # photocell
    for z in (2.557, 3.297):                                                                 # banner arms
        B(m, -0.33, 0.33, 0.07, 0.135, z, z + 0.046, 'elD', cull='k')


def lampp_detail(m):
    base_plate(m, 0.25)
    m.cy((0, 0, 0.647), 0.1, 0.09, 0.05, 'elD', seg=8, hull='none', caps=False)
    for z in (1.5, 2.6):
        m.cy((0, 0, z), 0.088, 0.088, 0.05, 'elD', seg=8, hull='none', caps=False)
    for sx in (-1, 1):                                                                       # scroll braces under the arm
        m.bm_((sx * 0.07, 0, 3.4), (sx * 0.5, 0, 3.822), 0.035, 'elD', hull='none')
    m.cy((0, 0, 3.897), 0.06, 0.0, 0.26, 'elD', seg=6, hull='none')                          # finial


def hydrant_detail(m):
    for a in range(0, 360, 60):                                                              # flange bolts
        x, y = math.cos(math.radians(a)) * 0.145, math.sin(math.radians(a)) * 0.145
        nut(m, x, y, 0.12, 0.034, 0.022, 'chrome')
    B(m, -0.03, 0.03, -0.03, 0.03, 0.787, 0.83, 'chrome', cull='b')                         # operating nut
    for x0 in (0.2, -0.238):                                                                 # nozzle caps
        m.cy((x0, 0, 0.42), 0.068, 0.068, 0.038, 'hydrant', seg=8, rot=(0, 90, 0), hull='none')
    m.cy((0, -0.2, 0.38), 0.078, 0.078, 0.038, 'hydrant', seg=8, rot=(90, 0, 0), hull='none')   # pumper cap


def mailbox_detail(m):
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.185, sx * 0.255))
        B(m, x0, x1, -0.27, 0.27, 0.047, 0.07, 'elD', cull='b')                              # foot plates
        nut(m, sx * 0.22, -0.2, 0.07, 0.03)
        nut(m, sx * 0.22, 0.2, 0.07, 0.03)
    B(m, -0.235, 0.235, -0.266, -0.257, 0.455, 0.47, 'trim', cull='k')                        # door seam
    B(m, -0.1, 0.1, -0.29, -0.258, 0.725, 0.755, 'chrome', cull='k')                         # pull lever
    B(m, 0.14, 0.2, -0.272, -0.257, 0.37, 0.42, 'steel', cull='k')                           # lock plate


def newsbox_detail(m):
    for cx in (-0.23, 0.23):
        B(m, cx - 0.1, cx + 0.1, -0.12, 0.12, 0.047, 0.07, 'elD', cull='b')                  # foot plate
        for sx in (-1, 1):
            nut(m, cx + sx * 0.075, -0.08, 0.07, 0.028)
        B(m, cx - 0.07, cx + 0.07, -0.205, -0.19, 0.44, 0.56, 'steel', cull='k')            # coin plate
        B(m, cx - 0.012, cx + 0.012, -0.212, -0.205, 0.5, 0.54, 'ink', cull='k')
        B(m, cx - 0.1, cx + 0.1, -0.23, -0.19, 0.4, 0.42, 'chrome', cull='k')               # pull handle


def trashcan_detail(m):
    m.cy((0, 0, 0.047), 0.27, 0.27, 0.025, 'elD', seg=10, hull='none', caps=False)           # base ring
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        r0, r1 = 0.225, 0.283
        m.bm_((math.cos(a) * r0, math.sin(a) * r0, 0.07), (math.cos(a) * r1, math.sin(a) * r1, 0.88), 0.016, 'trim', hull='none')


def bench_detail(m):
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.76, sx * 0.92))
        B(m, x0, x1, -0.3, 0.27, 0.047, 0.07, 'elD', cull='b')                               # foot plates
        for y in (-0.22, 0.19):
            nut(m, sx * 0.84, y, 0.07, 0.03)
    for y in (-0.2, -0.06, 0.08):                                                            # seat screws
        for sx in (-1, 1):
            B(m, sx * 0.84 - 0.012, sx * 0.84 + 0.012, y - 0.012, y + 0.012, 0.467, 0.473, 'chrome', cull='b')


def steam_detail(m):
    for k in range(1, 4):
        z = 0.02 + k * 0.38
        m.cy((0, 0, z - 0.015), 0.23 - 0.02 * k + 0.014, 0.23 - 0.02 * k + 0.014, 0.03, 'steel', seg=10, hull='none', caps=False)
    m.cy((0, 0, 0.017), 0.31, 0.3, 0.04, 'silver', seg=10, hull='none')                       # base flange
    for a in range(0, 360, 60):
        nut(m, math.cos(math.radians(a)) * 0.28, math.sin(math.radians(a)) * 0.28, 0.057, 0.032, 0.02, 'steel')


def newsstand_detail(m):
    B(m, -0.95, 0.95, -1.262, -1.247, 0.1, 0.22, 'trim', cull='k')                           # counter kick plate
    for x in (-0.85, -0.45, 0.0, 0.45, 0.85):
        B(m, x - 0.012, x + 0.012, -1.268, -1.259, 0.155, 0.18, 'chrome', cull='k')
    B(m, -0.995, 0.995, -1.462, -1.447, 0.96, 1.01, 'silver', cull='k')                      # counter edge strip
    for sx in (-1, 1):                                                                       # window frame
        x0, x1 = sorted((sx * 0.85, sx * 0.9))
        B(m, x0, x1, -1.238, -1.197, 1.02, 2.2, 'trim', cull='b')
    B(m, -0.9, 0.9, -1.238, -1.197, 2.2, 2.26, 'trim', cull='b')
    m.cy((-1.13, -1.63, 2.57), 0.035, 0.035, 2.26, 'steel', seg=6, rot=(0, 90, 0), hull='none')   # front gutter


def billboard_detail(m):
    for x in (-2.0, 2.0):
        B(m, x - 0.34, x + 0.34, 0.14, 0.76, 0.0, 0.06, 'graniteD', cull='b')
        for sx in (-1, 1):
            for yy in (0.2, 0.7):
                nut(m, x + sx * 0.25, yy, 0.3, 0.05, 0.04)
        for sx in (-1, 1):
            m.bm_((x + sx * 0.08, 0.45, 3.3), (x + sx * 0.08, -0.55, 4.22), 0.05, 'elD', hull='none')


def subway_detail(m):
    for sx in (-1, 1):
        xc = sx * 1.3
        for k in (0, 4, 8):                                                                  # rail posts with spear finials
            y = -2.3 + k * 0.575
            B(m, xc - 0.055, xc + 0.055, y - 0.05, y + 0.05, 0.35, 1.1, 'elD', cull='b')
            m.cy((xc, y, 1.097), 0.05, 0.0, 0.14, 'elD', seg=4, hull='none')
        for k in (2, 6):
            y = -2.3 + k * 0.575
            m.cy((xc, y, 1.077), 0.04, 0.0, 0.1, 'elD', seg=4, hull='none')
    for sx in (-1, 1):                                                                       # lamp post feet
        x = sx * 1.3
        B(m, x - 0.15, x + 0.15, -2.55, -2.25, 0.047, 0.075, 'elD', cull='b')
        for ax in (-1, 1):
            for ay in (-1, 1):
                nut(m, x + ax * 0.115, -2.4 + ay * 0.115, 0.075, 0.032)
        m.cy((x, -2.4, 1.3), 0.11, 0.11, 0.04, 'elD', seg=8, hull='none', caps=False)
    for sx in (-1, 1):                                                                       # sign panel bolts
        for z in (1.925, 2.475):
            B(m, sx * 1.175 - 0.012, sx * 1.175 + 0.012, -2.428, -2.417, z - 0.012, z + 0.012, 'chrome', cull='k')


def hatch_detail(m):
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.62, sy * 0.825))
        B(m, -0.5, -0.38, y0, y1, 0.182, 0.194, 'elD', cull='b')                             # hinge straps
        B(m, 0.38, 0.5, y0, y1, 0.182, 0.194, 'elD', cull='b')
        B(m, -0.14, 0.14, sy * 0.1 - 0.012, sy * 0.1 + 0.012, 0.19, 0.215, 'chrome', cull='b')   # pull bar
    B(m, -0.05, 0.05, -0.07, 0.07, 0.182, 0.2, 'elD', cull='b')                              # hasp
    for sx in (-1, 1):
        for sy in (-1, 1):
            nut(m, sx * 0.83, sy * 0.83, 0.17, 0.05, 0.03)
