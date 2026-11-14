"""kit-pelagic modelled detail (tactical look plan Stage 11): real offshore-platform fixings on the pieces the player
sees most. pel_base.make() calls apply(name, model) just before a piece is built; the table DETAIL maps a piece name to
its detail function (names, origins, footprints, _COL / _WCOL boxes, sockets and the palette are untouched).

Every part is hull='none' (no outline shell), stands at least 3 mm proud of what it sits on, starts E (3 mm) inside the
face behind it, horizontal runs stop 5 mm short of the piece sides. Only palette names the kit already has.
"""
import math

from ap_base import cyl_x, cyl_y

E = 0.003
STEELD, STEEL, NAVYD, DARK, YELLOW, YELLOWD, BLACK, WALLD = 'steelD', 'steel', 'navyD', 'dark', 'yellow', 'yellowD', 'black', 'wallD'


# ------------------------------------------------------------------------------------------------ primitives
def pb(m, a0, a1, z0, z1, p, d, c, ax='y', s=-1, cull=''):
    """box standing d proud of the face at plane p (axis ax, outward sign s), E inside it; a0..a1 run along the
    other horizontal axis"""
    if ax == 'y':
        lo, hi = (p - d, p + E) if s < 0 else (p - E, p + d)
        return m.bx(a0, a1, lo, hi, z0, z1, c, hull='none', cull=cull + ('k' if s < 0 else 'f'))
    lo, hi = (p - d, p + E) if s < 0 else (p - E, p + d)
    return m.bx(lo, hi, a0, a1, z0, z1, c, hull='none', cull=cull + ('r' if s < 0 else 'l'))


def bolt(m, a, z, p, ax='y', s=-1, c=STEELD, sz=0.026, d=0.010):
    pb(m, a - sz / 2, a + sz / 2, z - sz / 2, z + sz / 2, p, d, c, ax, s, cull='btlr' if ax == 'y' else 'btfk')


def bolts(m, a0, a1, z, p, n, ax='y', s=-1, c=STEELD, sz=0.026, d=0.010):
    for i in range(n):
        bolt(m, a0 + (a1 - a0) * (i + 0.5) / n, z, p, ax, s, c, sz, d)


def seam_v(m, a, z0, z1, p, c=STEELD, ax='y', s=-1, w=0.016, d=0.008):
    pb(m, a - w / 2, a + w / 2, z0, z1, p, d, c, ax, s, cull='btlr' if ax == 'y' else 'btfk')


def seam_h(m, a0, a1, z, p, c=STEELD, ax='y', s=-1, h=0.016, d=0.008):
    pb(m, a0 + 0.005, a1 - 0.005, z - h / 2, z + h / 2, p, d, c, ax, s, cull='')


def frame(m, a0, a1, z0, z1, p, c=NAVYD, ax='y', s=-1, depth=0.06, t=0.05, sill=True, low=True):
    """a frame standing out round an opening so the window reads with depth; a drip sill under it"""
    pb(m, a0 - t, a1 + t, z1, z1 + t, p, depth, c, ax, s)
    if low:
        pb(m, a0 - t, a1 + t, z0 - t, z0, p, depth, c, ax, s)
    pb(m, a0 - t, a0, z0 + 0.004, z1 - 0.004, p, depth, c, ax, s)
    pb(m, a1, a1 + t, z0 + 0.004, z1 - 0.004, p, depth, c, ax, s)
    if sill:
        pb(m, a0 - t - 0.02, a1 + t + 0.02, z0 - t - 0.034, z0 - t - 0.012, p, depth + 0.035, STEELD, ax, s)


def hinge(m, a, z, p, ax='y', s=-1, c=STEELD, hgt=0.12, w=0.05):
    """a hinge: leaf plate with a barrel"""
    pb(m, a - w / 2, a + w / 2, z - hgt / 2, z + hgt / 2, p, 0.012, c, ax, s)
    pb(m, a - 0.012, a + 0.012, z - hgt / 2 - 0.01, z + hgt / 2 + 0.01, p, 0.028, BLACK, ax, s)


def dog(m, a, z, p, ax='y', s=-1, c=STEELD):
    """a door dog: pivot boss with a lever"""
    pb(m, a - 0.045, a + 0.045, z - 0.014, z + 0.014, p, 0.022, c, ax, s)
    pb(m, a - 0.02, a + 0.02, z - 0.025, z + 0.025, p, 0.034, BLACK, ax, s)


def door_detail(m, x0, x1, z1, p, kick=0.22, dogs=(), hinges=(), ax='y', s=-1, jamb=True, ztop=None):
    """door furniture and frame for a door leaf x0..x1 (along the face) up to z1: kick plate, jambs and head, hinges, dogs"""
    pb(m, x0 + 0.02, x1 - 0.02, 0.004, kick, p, 0.014, STEELD, ax, s)
    bolts(m, x0 + 0.06, x1 - 0.06, kick * 0.5, p - s * 0.0, 4, ax, s, STEEL, 0.02, 0.020)
    if jamb:
        t = 0.05
        pb(m, x0 - t, x0 + 0.002, 0.004, z1 + t, p, 0.05, NAVYD, ax, s)
        pb(m, x1 - 0.002, x1 + t, 0.004, z1 + t, p, 0.05, NAVYD, ax, s)
        pb(m, x0 + 0.004, x1 - 0.004, z1 - 0.002, z1 + t, p, 0.05, NAVYD, ax, s)
    for (xa, za) in hinges:
        hinge(m, xa, za, p, ax, s)
    for (xa, za) in dogs:
        dog(m, xa, za, p, ax, s)


def pad_eye(m, x, y, z, c=STEELD):
    """a deck tie-down point: base plate and an eye lug with its dark hole"""
    m.bx(x - 0.07, x + 0.07, y - 0.06, y + 0.06, z, z + 0.014, c, hull='none', cull='b')
    m.bx(x - 0.05, x + 0.05, y - 0.012, y + 0.012, z + 0.014 - E, z + 0.085, c, hull='none', cull='b')
    m.bx(x - 0.02, x + 0.02, y - 0.0165, y - 0.0155, z + 0.04, z + 0.07, 'black', hull='none', cull='btlrk')


def rail_foot(m, x, y, z0):
    """base plate of a guard-rail stanchion"""
    m.bx(x - 0.075, x + 0.075, y - 0.075, y + 0.075, z0, z0 + 0.014, STEELD, hull='none', cull='b')


def clamp_x(m, x, y, z, r):
    """a pipe clamp (strap ring) round a pipe along X"""
    cyl_x(m, x - 0.018, x + 0.018, y, z, r + 0.012, STEELD, seg=8, hull='none')


def clamp_y(m, y, x, z, r):
    cyl_y(m, x, y - 0.018, y + 0.018, z, r + 0.012, STEELD, seg=8, hull='none')


# ------------------------------------------------------------------------------------------------ deck edge
def edge_detail(m):
    """scuppers, a pipe run with clamps and weld seams on the outboard fascia, a tie-down eye on the deck, slots in the kerb"""
    yf = 0.74
    for x in (-0.3, 0.3):    # drain scuppers: a dark slot in a steel surround
        pb(m, x - 0.13, x + 0.13, -0.5, -0.26, yf, 0.016, STEELD, 'y', 1)
        pb(m, x - 0.1, x + 0.1, -0.46, -0.3, yf + 0.016, 0.006, 'black', 'y', 1)
    for x in (-0.15, 0.15):
        seam_v(m, x, -1.55, -0.55, yf, STEELD, 'y', 1)
    bolts(m, -0.45, 0.45, -1.52, yf, 6, 'y', 1, STEEL, 0.02, 0.008)
    # a scupper in the coaming kerb
    for x in (-0.38, 0.38):
        pb(m, x - 0.07, x + 0.07, 0.03, 0.095, -0.47, 0.007, 'black', 'y', -1, cull='bt')
    pad_eye(m, 0.34, 0.62, 0.05)
    # bolts on the fascia's lower lip
    seam_h(m, -0.5, 0.5, -1.57, yf, STEELD, 'y', 1)


# ------------------------------------------------------------------------------------------------ blast fences
def fence_detail(m, h=3.6, post=False, brace=False, sign=False):
    """panel seams, rivet rows, a base channel with anchor bolts"""
    p = -0.423
    for x in (-0.25, 0.25):
        seam_v(m, x, 0.47, h - 0.15, p, STEELD, 'y', -1)
    for z in (0.6, h - 0.28):
        for i in range(9):
            x = -0.44 + i * 0.11
            if abs(abs(x) - 0.25) < 0.03 or (post and abs(x) < 0.14):
                continue
            bolt(m, x, z, p, 'y', -1, STEEL, 0.02, 0.008)
    # anchor plate on the back foot of the fence, bolted
    m.bx(-0.45, 0.45, -0.3 - E, -0.1, 0.0, 0.016, STEELD, hull='none', cull='b')
    for x in (-0.36, -0.12, 0.12, 0.36):
        m.bx(x - 0.022, x + 0.022, -0.26, -0.21, 0.016 - E, 0.04, STEEL, hull='none', cull='b')
    if brace:
        for x in (-0.1, 0.1):
            for y in (1.4, 1.7):
                m.bx(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.06 - E, 0.085, STEEL, hull='none', cull='b')


# ------------------------------------------------------------------------------------------------ ops block front
OPS_H = 7.6


def ops_detail(m, name):
    p = -0.45
    win_lo = name in ('Ops_Win',) or name.startswith('Ops_Sign_')
    if win_lo:
        frame(m, -0.4, 0.4, 0.9, 2.5, p, depth=0.05, t=0.04)
    if name in ('Ops_Win', 'Ops_Door', 'Ops_Vent') or name == 'Ops_End':
        if name == 'Ops_End':
            frame(m, -0.1, 0.4, 0.9, 2.5, p, depth=0.05, t=0.04, sill=False)
        else:
            frame(m, -0.4, 0.4, 4.4, 6.3, p, depth=0.05, t=0.04)
    if name.startswith('Ops_Sign_'):
        frame(m, -0.4, 0.4, 5.85, 6.9, p, depth=0.05, t=0.04)
    if name == 'Ops_End':
        frame(m, -0.1, 0.4, 4.4, 6.3, p, depth=0.05, t=0.04, sill=False)
    if name == 'Ops_Door':
        door_detail(m, -0.38, 0.38, 2.25, -0.5, kick=0.22, dogs=((0.27, 0.55), (0.27, 1.65)),
                    hinges=((-0.34, 0.35), (-0.34, 1.1), (-0.34, 1.85)), jamb=False)
        frame(m, -0.24, 0.24, 1.35, 1.95, -0.506, STEELD, depth=0.045, t=0.03, sill=False)
        bolts(m, -0.3, 0.3, 2.19, -0.503, 5, 'y', -1, STEEL, 0.02, 0.012)
    if name == 'Ops_Vent':
        frame(m, -0.4, 0.4, 0.5, 2.2, p, depth=0.05, t=0.04, sill=False)
        bolts(m, -0.43, 0.43, 0.43, p - 0.056, 6, 'y', -1, STEEL, 0.02, 0.008)
    if name == 'Ops_Plain':
        # a conduit run with clips, a junction box, a downpipe on the wall
        r = 0.022
        yc = p - r - 0.006
        cyl_x(m, -0.495, 0.495, yc, 3.0, r, 'black', seg=6, hull='none')
        for x in (-0.38, 0.0, 0.38):
            pb(m, x - 0.015, x + 0.015, 3.0 - r - 0.008, 3.0 + r + 0.008, p, 2 * r + 0.012, STEELD, 'y', -1)
        pb(m, 0.12, 0.38, 1.3, 1.62, p, 0.09, NAVYD, 'y', -1)
        pb(m, 0.15, 0.35, 1.33, 1.59, p - 0.09, 0.006, STEELD, 'y', -1)
        bolts(m, 0.17, 0.33, 1.36, p - 0.096, 3, 'y', -1, STEEL, 0.014, 0.006)
        m.cy((-0.38, yc, 0.4), 0.032, 0.032, 2.7, 'steelD', seg=6, hull='none')
        for z in (0.7, 1.6, 2.5):
            pb(m, -0.42, -0.34, z - 0.02, z + 0.02, p, 2 * 0.032 + 0.024, STEELD, 'y', -1)
    # cornice ledge under the roof band and a kick plate on the plinth (all module fronts)
    pb(m, -0.495, 0.495, 3.80, 3.835, p, 0.045, STEELD, 'y', -1)
    pb(m, -0.495, 0.495, 0.3, 0.325, p, 0.03, STEELD, 'y', -1)


# ------------------------------------------------------------------------------------------------ gate
def gate_detail(m):
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.55, s * 2.45))
        xc = (x0 + x1) / 2
        # base plate with anchor bolts, seams and a rivet row above the hazard band
        m.bx(x0 + 0.005, x1 - 0.005, -0.54, 0.54, 0.0, 0.03, STEELD, hull='none', cull='b')
        for (dx, dy) in ((-0.34, -0.46), (0.34, -0.46), (-0.34, 0.46), (0.34, 0.46)):
            m.bx(xc + dx - 0.025, xc + dx + 0.025, dy - 0.025, dy + 0.025, 0.03 - E, 0.07, STEEL, hull='none', cull='b')
        for sy in (-1, 1):
            pl = 0.5 * sy
            seam_v(m, xc, 1.1, 4.3, pl, STEELD, 'y', sy)
            for z in (1.15, 4.25):
                bolts(m, x0 + 0.08, x1 - 0.08, z, pl, 5, "y", sy, STEEL, 0.026, 0.014)
            seam_v(m, x0 + 0.06, 1.1, 4.3, pl, STEELD, 'y', sy)
            seam_v(m, x1 - 0.06, 1.1, 4.3, pl, STEELD, 'y', sy)


# ------------------------------------------------------------------------------------------------ hangars
def hangar_detail(m):
    # sliding-door gear on the south front: floor guide rail, overhead track with rollers, motor box and cable run
    m.bx(-9.595, 9.595, -10.04, -9.92, 0.0, 0.05, STEELD, hull='none', cull='b')
    for x in (-9.0, -6.0, -3.0, 0.0, 3.0, 6.0, 9.0):
        m.bx(x - 0.03, x + 0.03, -10.044, -10.036, 0.012, 0.038, STEEL, hull='none', cull='b')
    m.bx(-9.595, 9.595, -9.98, -9.82, 7.07, 7.203, STEELD, hull='none', cull='t')
    for x in (-9.4, -4.7, 0.0, 4.7, 9.4):
        m.bx(x - 0.05, x + 0.05, -10.0, -9.8, 6.96, 7.075, BLACK, hull='none', cull='t')
    # motor box on the header, a conduit down to the track, hazard-yellow hand wheel cover
    m.bx(10.1, 10.8, -10.28, -9.997, 7.55, 8.15, NAVYD, hull='none', cull='k')
    for i in range(4):
        z = 7.65 + i * 0.1
        m.bx(10.15, 10.75, -10.292, -10.28 + E, z, z + 0.04, BLACK, hull='none', cull='k')
    bolts(m, 10.17, 10.73, 7.58, -10.28, 4, 'y', -1, STEEL, 0.03, 0.012)
    m.cy((10.45, -10.06, 6.55), 0.03, 0.03, 1.02, 'black', seg=6, hull='none')
    for z in (6.8, 7.3):
        m.bx(10.42, 10.48, -10.092, -9.997, z - 0.02, z + 0.02, STEELD, hull='none', cull='k')
    # header: panel seams and rivet rows on the face below the lettering, a drip ledge on top
    m.bx(-11.555, 11.555, -10.045, -9.995, 9.52, 9.55, STEELD, hull='none', cull='k')
    for x in (-5.8, 0.0, 5.8):
        m.bx(x - 0.01, x + 0.01, -10.012, -9.997, 7.44, 7.65, STEELD, hull='none', cull='k')
    # the door-stack leaves: panel seams, a pull bar and a guide shoe at the foot
    for s in (-1, 1):
        for k in range(3):
            x0, x1 = sorted((s * (9.6 + k * 0.7), s * (9.6 + k * 0.7 + 0.82)))
            y0 = -10.0 + k * 0.24
            for z in (1.8, 3.6, 5.4):
                m.bx(x0 + 0.005, x1 - 0.005, y0 - 0.012, y0 + E, z - 0.02, z + 0.02, STEELD, hull='none', cull='k')
            xi = x0 + 0.09 if s > 0 else x1 - 0.09
            m.bx(xi - 0.02, xi + 0.02, y0 - 0.05, y0 + E, 0.9, 1.5, STEELD, hull='none', cull='k')
            m.bx(x0 + 0.005, x1 - 0.005, y0 - 0.03, y0 + E, 0.0, 0.1, STEELD, hull='none', cull='kb')
    # the outside walls: dado cap rails, a downpipe, a pipe run with clamps (east wall), man door furniture
    xo = 12.05
    m.bx(xo - E, xo + 0.03, -9.995, 10.045, 1.2, 1.24, STEELD, hull='none', cull='b')
    m.bx(-xo - 0.03, -xo + E, -9.995, 10.045, 1.2, 1.24, STEELD, hull='none', cull='b')
    m.bx(-11.595, 11.595, 10.05 - E, 10.08, 1.2, 1.24, STEELD, hull='none', cull='b')
    # downpipe on the east wall with brackets
    cx = xo + 0.075
    m.cy((cx, -9.7, 0.15), 0.055, 0.055, 9.0, STEEL, seg=8, hull='none')
    for z in (0.7, 2.5, 4.3, 6.1, 7.9):
        m.bx(xo - E, xo + 0.075 + 0.075, -9.7 - 0.07, -9.7 + 0.07, z - 0.02, z + 0.02, STEELD, hull='none', cull='')
    # pipe run along the east wall under the window band
    r = 0.045
    cyl_y(m, xo + r + 0.012, -9.3, 9.3, 3.2, r, 'steelD', seg=8, hull='none')
    for i in range(10):
        y = -8.4 + i * 1.87
        clamp_y(m, y, xo + r + 0.012, 3.2, r)
        m.bx(xo - E, xo + 2 * r + 0.012, y - 0.015, y + 0.015, 3.2 - 0.02, 3.2 + 0.02, STEELD, hull='none', cull='')
    # personnel door (east wall, y 3.0..4.1, z 0..2.2): frame, hinges, dogs, kick, rain hood
    xp = 12.058
    for (y0, y1, z0, z1) in ((2.93, 3.0, 0.0, 2.27), (4.1, 4.17, 0.0, 2.27), (3.004, 4.096, 2.2, 2.27)):
        m.bx(xp - 0.011, xp + 0.05, y0, y1, z0 + 0.004 if z0 == 0.0 else z0, z1, NAVYD, hull='none', cull='l')
    for z in (0.35, 1.1, 1.85):
        m.bx(xp, xp + 0.012 + E, 3.01, 3.09, z - 0.06, z + 0.06, STEELD, hull='none', cull='l')
    m.bx(xp, xp + 0.03, 3.86, 3.94, 1.0, 1.06, STEEL, hull='none', cull='l')
    m.bx(xp, xp + 0.022 + E, 3.99, 4.07, 0.55, 0.59, STEELD, hull='none', cull='l')
    m.bx(xp, xp + 0.022 + E, 3.99, 4.07, 1.65, 1.69, STEELD, hull='none', cull='l')
    m.bx(xp, xp + 0.012 + E, 3.03, 4.07, 0.004, 0.2, STEELD, hull='none', cull='lb')
    m.bx(xp - 0.01, xp + 0.25, 2.88, 4.22, 2.3, 2.34, STEELD, hull='none', cull='b')
    # safety board frame (NO SMOKING) on the east wall
    frame(m, -3.0, -1.4, 1.2, 2.2, 12.055, STEELD, ax='x', s=1, depth=0.03, t=0.03, sill=False)


# ------------------------------------------------------------------------------------------------ stairs
def stair_detail(m, x0, x1, y0, n, rise=0.2, run=0.5, z0=0.0, sides=(True, True)):
    """bolted stringers: a rivet at the mid of every second tread, tread grip bars, a landing kick"""
    L = n * run
    top = z0 + n * rise
    for i in range(1, n, 2):
        y = y0 + (i + 0.5) * run
        zu = z0 + 0.3 + (y - y0) * (top - z0 - 0.3) / (L - 0.25)
        zl = z0 + (y - y0 - 0.25) * (top - 0.3 - z0) / (L - 0.25)
        z = (zu + zl) / 2
        for side, x in ((0, x0), (1, x1)):
            if not sides[side]:
                continue
            xs = x - 0.04 if side == 0 else x + 0.04
            a, b = (xs - 0.007, xs + E) if side == 0 else (xs - E, xs + 0.007)
            m.bx(a, b, y - 0.014, y + 0.014, z - 0.014, z + 0.014, STEEL, hull='none', cull='btfk' + ('r' if side == 0 else 'l'))
    for i in range(n):
        ya = y0 + i * run
        z = z0 + (i + 1) * rise
        # grating bars under the nosing stripe: two dark grooves along the tread
        for yy in (ya + 0.2, ya + 0.3, ya + 0.4):
            m.bx(x0 + 0.1, x1 - 0.1, yy - 0.008, yy + 0.008, z + 0.003 - 0.001, z + 0.006, BLACK, hull='none', cull='b')


# ------------------------------------------------------------------------------------------------ island / tower2
def island_detail(m):
    G = 3.6
    # base block: door furniture on the ISLAND ACCESS door (x -0.9..0.3 at y -10), louvre door frame, ledge, kick
    p = -10.0
    door_detail(m, -0.9, 0.3, 2.15, p - 0.009 + 0.0, kick=0.22, dogs=((0.18, 0.6), (0.18, 1.7)),
                hinges=((-0.84, 0.35), (-0.84, 1.1), (-0.84, 1.85)), jamb=False)
    frame(m, -0.8, 0.2, 1.4, 1.95, -10.012, STEELD, depth=0.045, t=0.03, sill=False)
    for x0, x1, z1 in ((-0.9, 0.3, 2.15), (2.0, 3.6, 2.6)):
        pb(m, x0 - 0.05, x0 + 0.002, 0.004, z1 + 0.05, p, 0.045, NAVYD, 'y', -1)
        pb(m, x1 - 0.002, x1 + 0.05, 0.004, z1 + 0.05, p, 0.045, NAVYD, 'y', -1)
        pb(m, x0 + 0.004, x1 - 0.004, z1 - 0.002, z1 + 0.05, p, 0.045, NAVYD, 'y', -1)
    for z in (0.7, 1.7):
        dog(m, 3.44, z, p - 0.009, 'y', -1)
    for z in (0.5, 1.3, 2.1):
        hinge(m, 2.04, z, p - 0.009, 'y', -1)
    # cornice ledge, plinth kick plate and rivets round the base block
    pb(m, -4.995, 4.995, G - 0.07, G - 0.035, p, 0.06, STEELD, 'y', -1)
    pb(m, -9.995, 9.995, G - 0.07, G - 0.035, 5.0, 0.06, STEELD, 'x', 1)
    pb(m, -4.995, 4.995, 0.3, 0.325, p, 0.03, STEELD, 'y', -1)
    for x in (-4.0, -2.2, 1.0, 4.2):
        seam_v(m, x, 0.4, G - 0.1, p, STEELD, 'y', -1)
    for y in (-8.0, -3.0, 1.0, 5.0, 9.0):
        seam_v(m, y, 0.4, G - 0.1, 5.0, STEELD, 'x', 1)
    # the four portholes on the east face: a dogged ring
    for y in (-5.0, -1.0, 3.0, 7.0):
        yc = y + 1.4
        m.cy((5.0 - E, yc, 2.6), 0.23, 0.23, 0.03, STEELD, seg=8, rot=(0, 90, 0), hull='none')
        pts = [(5.033, yc + math.cos(a) * 0.17, 2.6 + math.sin(a) * 0.17) for a in [math.radians(22.5 + 45 * i) for i in range(8)]]
        from parking_base import poly
        poly(m, pts, 'glassD', (1, 0, 0))
        for k in range(4):
            a = math.radians(45 + 90 * k)
            m.bx(5.03, 5.045, yc + math.cos(a) * 0.205 - 0.015, yc + math.cos(a) * 0.205 + 0.015, 2.6 + math.sin(a) * 0.205 - 0.015, 2.6 + math.sin(a) * 0.205 + 0.015, 'black', hull='none', cull='l')
        # east doors (y +-0.5 around y, 0..2.2): frame jambs and a kick plate
        pb(m, y - 0.5, y + 0.5, 0.004, 0.2, 5.006, 0.014, STEELD, 'x', 1)
        pb(m, y - 0.56, y - 0.498, 0.0, 2.25, 5.006, 0.04, NAVYD, 'x', 1)
        pb(m, y + 0.498, y + 0.56, 0.0, 2.25, 5.006, 0.04, NAVYD, 'x', 1)
        pb(m, y - 0.496, y + 0.496, 2.198, 2.25, 5.006, 0.04, NAVYD, 'x', 1)
    # tower body: window frames with depth (south face y -7.2, east face x 2.2)
    for z0, z1 in ((4.5, 5.9), (7.9, 9.3)):
        xa = -1.0 if z0 < 6 else -2.7
        frame(m, xa, 1.9, z0, z1, -7.2, NAVYD, depth=0.055, t=0.045)
        frame(m, -6.9, 9.6, z0, z1, 2.2, NAVYD, ax='x', s=1, depth=0.055, t=0.045)
    # tower stringer bands every 3.5 m on the south face
    for z in (6.6, 10.5):
        pb(m, -2.995, 2.195, z - 0.02, z + 0.02, -7.2, 0.03, STEELD, 'y', -1)
        pb(m, -7.195, 9.995, z - 0.02, z + 0.02, 2.2, 0.03, STEELD, 'x', 1)
    # bolted fixing rows at the tower's foot
    bolts(m, -2.9, 2.1, G + 0.25, -7.2, 12, 'y', -1, STEEL, 0.03, 0.012)


def tower2_detail(m):
    G = 3.6
    p = -6.0
    door_detail(m, 0.2, 1.4, 2.15, p - 0.006, kick=0.22, dogs=((1.28, 0.6), (1.28, 1.7)),
                hinges=((0.26, 0.35), (0.26, 1.1), (0.26, 1.85)), jamb=False)
    frame(m, 0.3, 1.3, 1.4, 1.95, p - 0.009, STEELD, depth=0.045, t=0.03, sill=False)
    pb(m, 0.15, 0.202, 0.004, 2.2, p, 0.045, NAVYD, 'y', -1)
    pb(m, 1.398, 1.45, 0.004, 2.2, p, 0.045, NAVYD, 'y', -1)
    pb(m, 0.204, 1.396, 2.148, 2.2, p, 0.045, NAVYD, 'y', -1)
    frame(m, 2.0, 3.6, 1.0, 2.3, p - 0.006, NAVYD, depth=0.05, t=0.04, sill=True)
    pb(m, -3.995, 3.995, G - 0.07, G - 0.035, p, 0.06, STEELD, 'y', -1)
    pb(m, -3.995, 3.995, 0.3, 0.325, p, 0.03, STEELD, 'y', -1)
    for x in (-2.8, -1.2, 1.7, 3.8):
        seam_v(m, x, 0.4, G - 0.1, p, STEELD, 'y', -1)
    # shaft: window frames, door furniture, ledge bands
    p = 1.4
    frame(m, 0.8, 3.6, 7.0, 8.2, p, NAVYD, depth=0.055, t=0.045)
    frame(m, 1.8, 5.6, 7.0, 8.2, 4.0, NAVYD, ax='x', s=1, depth=0.055, t=0.045)
    door_detail(m, 1.6, 2.6, G + 2.1, p - 0.006, kick=0.22, dogs=((2.48, G + 0.6), (2.48, G + 1.6)),
                hinges=((1.66, G + 0.35), (1.66, G + 1.05), (1.66, G + 1.75)), jamb=False)
    pb(m, 1.55, 1.602, G + 0.004, G + 2.15, p, 0.045, NAVYD, 'y', -1)
    pb(m, 2.598, 2.65, G + 0.004, G + 2.15, p, 0.045, NAVYD, 'y', -1)
    pb(m, 1.604, 2.596, G + 2.098, G + 2.15, p, 0.045, NAVYD, 'y', -1)
    for z in (4.9, 10.2):
        pb(m, 0.405, 1.5, z - 0.02, z + 0.02, p, 0.03, STEELD, 'y', -1)
        pb(m, 2.7, 3.995, z - 0.02, z + 0.02, p, 0.03, STEELD, 'y', -1)
        pb(m, 1.405, 5.995, z - 0.02, z + 0.02, 4.0, 0.03, STEELD, 'x', 1)
    # a ladder up the shaft's south face between door and cab: stiles on stand-off brackets, rungs
    xl = 3.3
    for sx in (-0.2, 0.2):
        m.bx(xl + sx - 0.02, xl + sx + 0.02, p - 0.1, p + E, G + 2.4, 11.6, STEELD, hull='none', cull='kbt')
    for k in range(0, 17):
        z = G + 2.6 + k * 0.5
        m.bx(xl - 0.2, xl + 0.2, p - 0.092, p - 0.06, z - 0.014, z + 0.014, STEEL, hull='none', cull='k')
    for z in (G + 2.5, 7.4, 11.5):
        for sx in (-0.2, 0.2):
            m.bx(xl + sx - 0.03, xl + sx + 0.03, p - 0.135, p + E, z, z + 0.05, STEELD, hull='none', cull='k')


# ------------------------------------------------------------------------------------------------ props
def container_detail(m):
    W, L, H = 2.44, 6.06, 2.59
    hx, hy = W / 2, L / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * (hx - 0.162), sx * (hx + 0.012)))
            ya, yb = sorted((sy * (hy - 0.178), sy * (hy + 0.012)))
            m.bx(xa, xb, ya, yb, 0.0, 0.118, STEELD, hull='none', cull='b')
            m.bx(xa, xb, ya, yb, H - 0.118, H + 0.012, STEELD, hull='none', cull='b')
    # door end (y +L/2): cam keepers on the locking rods, hinges
    for x in (-0.6, 0.6):
        for z in (0.55, 1.3, 2.05):
            m.bx(x - 0.05, x + 0.05, hy - E, hy + 0.034, z - 0.03, z + 0.03, STEELD, hull='none', cull='f')
        m.bx(x - 0.07, x + 0.07, hy - E, hy + 0.012, 0.0, 0.05, STEELD, hull='none', cull='fb')
    for x in (-1.12, 1.12):
        for z in (0.5, 1.3, 2.1):
            m.bx(x - 0.04, x + 0.04, hy - E, hy + 0.032, z - 0.08, z + 0.08, STEELD, hull='none', cull='f')
    m.bx(-0.09, 0.09, hy - E, hy + 0.04, 1.15, 1.2, BLACK, hull='none', cull='f')
    # forklift pockets and a bottom rail on the sides
    for sx in (-1, 1):
        xp = sx * hx
        for y in (-0.95, 0.95):
            a, b = sorted((xp + sx * 0.006, xp + sx * 0.012))
            m.bx(a, b, y - 0.2, y + 0.2, 0.02, 0.12, BLACK, hull='none', cull='tbfk' + ('l' if sx > 0 else 'r'))


def fueltank_detail(m):
    R = 1.25
    zc = R + 0.55
    # hold-down straps over each saddle and weld rings between
    for y in (-2.2, 2.2):
        cyl_y(m, 0, y - 0.04, y + 0.04, zc, R + 0.03, STEELD, seg=14, hull='none')
    for y in (-1.1, 1.1):
        cyl_y(m, 0, y - 0.012, y + 0.012, zc, R + 0.012, STEEL, seg=14, hull='none')
    zt = 2 * R + 0.62
    # manway, vent stack, gauge post on the walkway
    m.cy((0.0, -1.0, zt), 0.3, 0.3, 0.07, STEEL, seg=10, hull='none')
    for k in range(6):
        a = k * math.pi / 3
        m.bx(math.cos(a) * 0.23 - 0.02, math.cos(a) * 0.23 + 0.02, -1.0 + math.sin(a) * 0.23 - 0.02, -1.0 + math.sin(a) * 0.23 + 0.02, zt + 0.07 - E, zt + 0.1, STEELD, hull='none', cull='b')
    m.cy((0.0, 1.3, zt), 0.05, 0.05, 0.5, STEELD, seg=6, hull='none')
    m.cy((0.0, 1.3, zt + 0.5), 0.1, 0.03, 0.08, STEEL, seg=8, hull='none')
    m.cy((-0.25, 0.2, zt), 0.04, 0.04, 0.22, 'fire', seg=6, hull='none')
    m.bx(-0.3, -0.2, 0.15, 0.25, zt + 0.22 - E, zt + 0.3, 'fire', hull='none', cull='b')
    # outlet flange and gate valve on the south dome
    cyl_y(m, 0, -4.02, -3.86, zc - 0.5 + 0.2, 0.17, STEEL, seg=8, hull='none')
    # tank end: a ground lug and level gauge on the east side
    # base: anchor bolts on the saddles' plates
    for y in (-2.2, 2.2):
        for sx in (-1, 1):
            m.bx(sx * 0.98 - 0.03, sx * 0.98 + 0.03, y - 0.25, y - 0.19, 0.0, 0.05, STEEL, hull='none', cull='b')
            m.bx(sx * 0.98 - 0.03, sx * 0.98 + 0.03, y + 0.19, y + 0.25, 0.0, 0.05, STEEL, hull='none', cull='b')


def cargolift_detail(m):
    for (x, y) in ((-3.3, -3.3), (3.3, -3.3), (-3.3, 3.3), (3.3, 3.3)):
        m.bx(x - 0.195, x + 0.195, y - 0.195, y + 0.195, 0.0, 0.04, STEELD, hull='none', cull='b')
        for (dx, dy) in ((-0.15, -0.15), (0.15, -0.15), (-0.15, 0.15), (0.15, 0.15)):
            m.bx(x + dx - 0.022, x + dx + 0.022, y + dy - 0.022, y + dy + 0.022, 0.04 - E, 0.075, STEEL, hull='none', cull='b')
        for z in (1.0, 2.2, 3.4):
            m.bx(x - 0.19, x + 0.19, y - 0.19, y + 0.19, z - 0.015, z + 0.015, STEELD, hull='none', cull='')
    # flush tie-down eyes in the platform
    for (x, y) in ((-2.2, -0.975), (2.2, -0.975), (-2.2, 0.965), (2.2, 0.965), (0.0, -1.945), (0.0, 1.935)):
        pad_eye(m, x, y, 0.011)
    # the control post: base plate, e-stop, conduit
    m.bx(-3.8, -3.4, -2.65, -2.15, 0.0, 0.03, STEELD, hull='none', cull='b')
    m.cy((-3.6, -2.4, 1.3), 0.04, 0.04, 0.05, 'beacon', seg=8, hull='none')
    m.cy((-3.6, -2.4, 1.35), 0.055, 0.055, 0.02, 'beacon', seg=8, hull='none')
    for x in (-3.72, -3.48):
        m.bx(x - 0.015, x + 0.015, -2.58, -2.52, 0.03 - E, 0.06, STEEL, hull='none', cull='b')


def tractor_detail(m):
    # headlights and bumper on the nose, fuel cap, side seams, wheel hub caps with lug nuts, tow hitch plate
    m.bx(-0.7, 0.7, -1.06, -0.997, 0.22 + 0.0, 0.3, STEELD, hull='none', cull='b')
    for x in (-0.55, 0.55):
        m.bx(x - 0.1, x + 0.1, -1.04, -0.997, 0.58, 0.74, DARK, hull='none', cull='k')
        m.bx(x - 0.07, x + 0.07, -1.046, -1.04 + E, 0.62, 0.7, 'lampW', hull='none', cull='k')
    m.cy((0.5, -0.3, 0.92), 0.06, 0.06, 0.025, STEELD, seg=8, hull='none')
    for s in (-1, 1):
        a, b = sorted((s * 0.75 - s * E, s * 0.75 + s * 0.008))
        for y in (0.15, 0.45):
            m.bx(a, b, y - 0.01, y + 0.01, 0.26, 0.76, YELLOWD, hull='none', cull='tbfk' + ('l' if s > 0 else 'r'))
        for (y) in (-0.6, 1.05):
            x = s * 0.72
            xo = x + s * 0.092
            for k in range(6):
                ang = k * math.pi / 3
                yy, zz = y + math.cos(ang) * 0.11, 0.24 + math.sin(ang) * 0.11
                a2, b2 = sorted((xo + s * 0.008, xo + s * 0.022))
                m.bx(a2, b2, yy - 0.012, yy + 0.012, zz - 0.012, zz + 0.012, BLACK, hull='none', cull='tbfk' + ('l' if s < 0 else 'r') + '')
    m.bx(-0.12, 0.12, -1.0 - 0.1, -1.0 + E, 0.3, 0.34, STEELD, hull='none', cull='k')


def jet_detail(m):
    """landing gear collars, torque links, hub caps, nozzle rings, pitot and the tail-hook plate"""
    for s in (-1, 1):
        xg = s * 1.55
        m.cy((xg, 1.6, 0.8), 0.08, 0.08, 0.1, STEELD, seg=6, hull='none')
        m.cy((xg, 1.6, 0.5), 0.075, 0.075, 0.05, YELLOW, seg=6, hull='none')
        m.bm_((xg, 1.6 - 0.05, 0.84), (xg, 1.6 - 0.05, 0.62), 0.03, STEELD, hull='none')
        # hub cap and lug nuts
        xo = xg + s * 0.131
        for k in range(6):
            ang = k * math.pi / 3
            yy, zz = 1.6 + math.cos(ang) * 0.14, 0.42 + math.sin(ang) * 0.14
            a2, b2 = sorted((xo + s * 0.012, xo + s * 0.03))
            m.bx(a2, b2, yy - 0.014, yy + 0.014, zz - 0.014, zz + 0.014, BLACK, hull='none', cull='tbfk' + ('l' if s < 0 else 'r'))
        x = s * 1.85
    # nose gear collar and a torque link, a taxi lamp
    m.cy((0.0, -5.0, 0.62), 0.07, 0.07, 0.07, STEELD, seg=6, hull='none')
    m.bm_((0.0, -5.06, 0.66), (0.0, -5.06, 0.45), 0.025, STEELD, hull='none')
    # tail hook point plate
    m.bx(-0.07, 0.07, 7.36, 7.44, 0.58, 0.64, BLACK, hull='none', cull='')


def pipe_detail(m, y0, y1):
    """flange rings and a hold-down strap on each pipe line"""
    for x in (-0.13, 0.13):
        for y in ((y0 + 0.05, y1 - 0.05) if y1 - y0 > 0.5 else (y0 + 0.05,)):
            cyl_y(m, x, y - 0.015, y + 0.015, 0.22, 0.103, STEELD, seg=8, hull='none')
        ym = (y0 + y1) / 2
        cyl_y(m, x, ym - 0.025, ym + 0.025, 0.22, 0.092, STEELD, seg=8, hull='none')


def fuelpoint_detail(m):
    p = -0.4
    m.bx(-0.795, 0.795, p - 0.03, p + E, 0.004, 0.12, STEELD, hull='none', cull='kb')
    bolts(m, -0.7, 0.7, 0.08, p - 0.03, 5, 'y', -1, STEEL, 0.022, 0.010)
    seam_v(m, 0.0, 0.15, 0.78, p, STEELD, 'y', -1)
    seam_v(m, 0.0, 1.38, 1.48, p, STEELD, 'y', -1)
    # door hinge and latch on the meter panel, reel flange bolts
    for z in (0.95, 1.2):
        hinge(m, -0.74, z, p - 0.006, 'y', -1, hgt=0.1)
    for k in range(6):
        ang = k * math.pi / 3
        x, z = 0.4 + math.cos(ang) * 0.28, 0.75 + math.sin(ang) * 0.28
        m.bx(x - 0.016, x + 0.016, -0.609, -0.597, z - 0.016, z + 0.016, STEELD, hull='none', cull='k')
    # nozzle holster


def trail_detail(m, name):
    """blast screen: bolts through the louvre rails, weld seam, base angle"""
    xf = 0.064
    for y in (-0.25, 0.25):
        pb(m, y - 0.01, y + 0.01, 0.31, TRAIL_H - 0.11, xf, 0.008, STEELD, 'x', 1)
    for z in (0.34, TRAIL_H - 0.16):
        for y in (-0.42, -0.08, 0.08, 0.42):
                bolt(m, y, z, xf, 'x', 1, STEEL, 0.02, 0.008)
    pb(m, -0.495, 0.495, 0.3, 0.33, xf, 0.035, STEELD, 'x', 1)


TRAIL_H = 2.6


def hatch_detail(m):
    # corner bolts on the hatch ring, hinge barrels and a lifting handle
    for (x, y) in ((-0.72, -0.72), (0.72, -0.72), (-0.72, 0.72), (0.72, 0.72)):
        m.bx(x - 0.035, x + 0.035, y - 0.035, y + 0.035, 0.18 - E, 0.205, STEEL, hull='none', cull='b')
    for y in (-0.6, 0.6):
        for x in (-0.5, 0.5):
            m.bx(x - 0.03, x + 0.03, y - 0.04, y + 0.04, 0.2 - E, 0.235, STEELD, hull='none', cull='b')
    for x in (-0.18, 0.18):
        m.bx(x - 0.02, x + 0.02, -0.09, 0.09, 0.26 - E, 0.3, STEELD, hull='none', cull='b')


DETAIL = {
    'Edge_A': edge_detail, 'Edge_B': edge_detail, 'Edge_Ring': edge_detail, 'Edge_Hose': edge_detail, 'Edge_Light': edge_detail,
    'Fence_A': lambda m: fence_detail(m, post=True, brace=True), 'Fence_B': fence_detail, 'Fence_Sign': fence_detail,
    'Fence_Light': fence_detail,
    'GateFrame': gate_detail,
    'Landmark_Hangar1': hangar_detail, 'Landmark_Hangar2': hangar_detail,
    'Landmark_Island': island_detail, 'Landmark_Tower2': tower2_detail,
    'Stair24': lambda m: stair_detail(m, -0.85, 0.85, -3.0, 12), 'Stair30': lambda m: stair_detail(m, -0.85, 0.85, -4.0, 15),
    'Container': container_detail, 'FuelTank': fueltank_detail, 'CargoLift': cargolift_detail, 'Tractor': tractor_detail,
    'Jet_Body': jet_detail, 'FuelPoint': fuelpoint_detail, 'Hatch': hatch_detail,
    'PipeFull': lambda m: pipe_detail(m, -0.5, 0.5), 'PipeHalf': lambda m: pipe_detail(m, -0.5, -0.2),
}
for _n in ('Ops_Win', 'Ops_Plain', 'Ops_Door', 'Ops_Vent', 'Ops_End'):
    DETAIL[_n] = (lambda n: lambda m: ops_detail(m, n))(_n)
for _k in range(14):
    DETAIL['Ops_Sign_%d' % _k] = (lambda n: lambda m: ops_detail(m, n))('Ops_Sign_%d' % _k)
for _i in range(3):
    for _w in ('A', 'B'):
        DETAIL['Fence_Deck%s_%d' % (_w, _i)] = (lambda i: lambda m: fence_detail(m, post=(i == 1)))(_i)
for _n in ('TrailWall', 'TrailWall_B', 'TrailWall_C', 'TrailWall_D'):
    DETAIL[_n] = (lambda n: lambda m: trail_detail(m, n))(_n)


def apply(name, m):
    fn = DETAIL.get(name)
    if fn:
        fn(m)
