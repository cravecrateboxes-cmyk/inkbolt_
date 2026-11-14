"""kit-megastore modelled detail (tactical look plan Stage 11): what a real warehouse club shows up close.

Racking: upright slot perforations, rack-protector guards, capacity plates, beam-to-upright connectors. Checkouts:
side kick plates and panel seams, belt edge rails, a scanner bezel. Walls: cladding laps, a rub rail, a cap trim, a
conduit run, fire-exit door frame / hinges / kick plate / push-bar brackets, strapped extinguishers. Columns: splice
plates and a base cap. Hanging signs: edge trims and hanger plates. Cart corral: post base plates with anchor bolts.

Rules (KIT-BRIEF): every part is hull='none' (no outline shell), at least 3 mm proud of what it sits on, embedded
3 mm, horizontal runs stop 5 mm short of the piece sides. Nothing here changes a piece's origin, footprint, collision
boxes or the parts already drawn: it only adds shapes. Called from the builders in ms_struct / ms_racks / ms_dept."""
from ms_base import *  # noqa: F401,F403

E = 0.003


def _cull(s, z0, z1):
    return ('k' if s < 0 else 'f') + ('b' if z0 < 0.01 else '') + ('t' if z1 > 5.0 else '')


def dbx(m, x0, x1, yf, d, z0, z1, c, s=-1):
    """box d proud of a face at y = yf (s -1: face looks toward -Y, s +1: toward +Y), sunk E into it"""
    y0, y1 = (yf - d, yf + E) if s < 0 else (yf - E, yf + d)
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=_cull(s, z0, z1))


def dbx_x(m, xf, y0, y1, z0, z1, d, c, s=1):
    """box d proud of a face at x = xf (s +1: face looks toward +X, s -1: toward -X)"""
    a, b = (xf - E, xf + d) if s > 0 else (xf - d, xf + E)
    return m.bx(a, b, y0, y1, z0, z1, c, hull='none', cull=('l' if s > 0 else 'r') + ('b' if z0 < 0.01 else ''))


def paint(m, x0, x1, yf, z0, z1, c, s=-1):
    (fq if s < 0 else bq)(m, x0, x1, yf + s * 0.003, z0, z1, c)


# ================================================================ racking
def rack_detail(m, Ht, frames, beams, bx0, bx1):
    """frames: [(x, guarded)] upright x positions (post spans x..x+0.08); beams: [(z_lo, z_hi)] front step beams"""
    for s in (-1, 1):
        yf = s * 1.0
        for x, has_guard in frames:
            z = 0.5   # slotted upright: a column of dark slots (painted) from above the guard to near the top
            while z + 0.05 < Ht - 0.1:
                if not (Ht > 6 and 2.25 < z < 2.65):   # the stockroom bays carry a location tag there
                    paint(m, x + 0.025, x + 0.055, yf, z, z + 0.05, 'navy', s)
                z += 0.12
            if not has_guard:   # rack protector: a yellow steel guard with two black bands
                dbx(m, x + 0.005, x + 0.075, yf, 0.016, 0.004, 0.4, 'hazY', s)
                for z0 in (0.1, 0.26):
                    paint(m, x + 0.005, x + 0.075, yf + s * 0.016, z0, z0 + 0.06, 'black', s)
            zc = 1.3 if Ht < 6 else 1.2   # capacity plate on the upright
            dbx(m, x + 0.003, x + 0.077, yf, 0.007, zc, zc + 0.2, 'paper', s)
            paint(m, x + 0.012, x + 0.068, yf + s * 0.007, zc + 0.13, zc + 0.18, 'brandR', s)
            paint(m, x + 0.012, x + 0.068, yf + s * 0.007, zc + 0.04, zc + 0.1, 'black', s)
        for (z0, z1) in beams:   # beam connectors: a bolted steel clip over each beam end
            h = z1 - z0
            za, zb = z0 + h * 0.1, z1 - h * 0.1
            dbx(m, bx0 + 0.005, bx0 + 0.085, yf, 0.007, za, zb, 'steelD', s)
            dbx(m, bx1 - 0.085, bx1 - 0.005, yf, 0.007, za, zb, 'steelD', s)


# ================================================================ checkout
def checkout_detail(m):
    for xf, s in ((-0.05, 1), (-0.95, -1)):   # counter sides: kick plates, panel seams
        dbx_x(m, xf, -1.595, 2.295, 0.004, 0.1, 0.008, 'steelD', s)
        for y in (-0.7, 0.2, 1.1, 1.7):
            dbx_x(m, xf, y - 0.007, y + 0.007, 0.11, 0.84, 0.008, 'rackG', s)
    dbx(m, -0.945, -0.055, -2.45, 0.008, 0.004, 0.1, 'steelD')   # bagging shelf end kick plate
    for x0, x1 in ((-0.89, -0.855), (-0.145, -0.11)):   # belt edge rails and the end stop
        m.bx(x0, x1, -0.195, 2.195, 0.86, 0.9, 'chrome', hull='none', cull='b')
    m.bx(-0.855, -0.145, 2.16, 2.195, 0.86, 0.9, 'chrome', hull='none', cull='b')
    m.bx(-0.72, -0.28, -1.2, -0.72, 0.86, 0.88, 'steelD', hull='none', cull='b')   # scanner bezel and window
    m.bx(-0.64, -0.36, -1.12, -0.8, 0.86, 0.886, 'black', hull='none', cull='b')
    m.bx(-0.5, -0.46, -1.12, -0.8, 0.886, 0.89, 'scrC', hull='none', cull='b')


# ================================================================ walls
def sales_wall(m, lower=True, upper=True):
    if lower:   # rub rail with two bolt heads, grey skirting above the painted plinth
        dbx(m, -0.495, 0.495, -0.5, 0.012, 0.86, 0.98, 'steel')
        for x in (-0.3, 0.3):
            dbx(m, x - 0.015, x + 0.015, -0.512, 0.008, 0.9, 0.94, 'steelD')
        dbx(m, -0.495, 0.495, -0.5, 0.012, 0.145, 0.2, 'grey')
    if upper:   # cladding laps every 1.2 m and a cap trim under the roof deck
        for z in (5.4, 6.6, 7.8, 9.0):
            dbx(m, -0.495, 0.495, -0.5, 0.009, z, z + 0.035, 'corrD')
        dbx(m, -0.495, 0.495, -0.5, 0.02, 9.86, 9.996, 'steel')


def stock_wall(m, conduit=False):
    for z in (6.0, 7.2, 8.4):
        dbx(m, -0.495, 0.495, -0.5, 0.009, z, z + 0.035, 'corrD')
    dbx(m, -0.495, 0.495, -0.5, 0.02, 9.86, 9.996, 'steelD')
    if conduit:   # a conduit run at 3.3 m with clips and a drop to a junction box
        m.cy((-0.495, -0.532, 3.3), 0.022, 0.022, 0.99, 'steelD', seg=6, rot=(0, 90, 0), hull='none')
        for x in (-0.3, 0.1, 0.4):
            dbx(m, x - 0.015, x + 0.015, -0.5, 0.058, 3.272, 3.328, 'steel')
        m.cy((0.3, -0.532, 1.1), 0.02, 0.02, 2.2, 'steelD', seg=6, hull='none')
        dbx(m, 0.2, 0.4, -0.5, 0.09, 0.9, 1.1, 'steel')
        dbx(m, 0.22, 0.38, -0.59, 0.006, 0.92, 1.08, 'steelD')


def exit_door_detail(m):
    """frame, hinges, kick plate and push-bar brackets for the fire exit (door leaf y -0.56..-0.503, x +-0.48)"""
    dbx(m, -0.495, -0.48, -0.5, 0.075, 0.0, 2.34, 'steel')
    dbx(m, 0.48, 0.495, -0.5, 0.075, 0.0, 2.34, 'steel')
    dbx(m, -0.48, 0.48, -0.5, 0.075, 2.3, 2.345, 'steel')
    dbx(m, -0.41, 0.41, -0.56, 0.012, 0.03, 0.28, 'steelD')
    for z in (0.3, 1.15, 2.0):
        dbx(m, -0.465, -0.435, -0.56, 0.012, z, z + 0.1, 'chrome')
    for x in (-0.37, 0.33):
        dbx(m, x, x + 0.04, -0.563, 0.05, 0.97, 1.11, 'steelD')


def extinguisher_straps(m, x=0.0):
    for z in (0.63, 0.88):
        m.cy((x, -0.62, z), 0.104, 0.104, 0.03, 'black', seg=8, hull='none')


# ================================================================ columns
def column_detail(m):
    m.cy((0, 0, 1.197), 0.3, 0.3, 0.02, 'steelD', seg=12, hull='none')   # cap over the guard
    for z in (4.0, 6.5):   # bolted splice plates on the front and back flanges
        for yf, s in ((-0.16, -1), (0.16, 1)):
            dbx(m, -0.13, 0.13, yf, 0.012, z, z + 0.5, 'steelD', s)
            for dx in (-0.09, 0.09):
                for dz in (0.08, 0.42):
                    dbx(m, dx - 0.012, dx + 0.012, yf + s * 0.012, 0.008, z + dz - 0.012, z + dz + 0.012, 'steel', s)
    dbx(m, -0.1, 0.1, -0.16, 0.007, 1.5, 1.7, 'paper')   # column number plate
    paint(m, -0.07, 0.07, -0.167, 1.56, 1.64, 'brand')


# ================================================================ hanging signs
def sign_frame(m, hw, th, z0, z1, xhang):
    """steel edge trims along the bottom and top of a hanging board (x +-hw, y +-th..) and a hanger plate at each rod"""
    for s in (-1, 1):
        ya, yb = sorted((s * (th - 0.003), s * (th + 0.008)))
        m.bx(-hw + 0.005, hw - 0.005, ya, yb, z0 - 0.003, z0 + 0.03, 'steelD', hull='none', cull='')
        m.bx(-hw + 0.005, hw - 0.005, ya, yb, z1 - 0.03, z1 + 0.003, 'steelD', hull='none', cull='')
    for x in xhang:
        m.bx(x - 0.05, x + 0.05, -0.078, 0.078, z1 - 0.003, z1 + 0.03, 'steelD', hull='none', cull='')


# ================================================================ cart corral
def corral_detail(m):
    for sy in (-1, 1):
        ya, yb = (-0.445, -0.33) if sy < 0 else (0.33, 0.445)
        yy = ya + 0.02 if sy < 0 else yb - 0.02
        for x in (-1.9, 0.0, 1.9):
            m.bx(x - 0.045, x + 0.045, ya, yb, 0.0, 0.012, 'steelD', hull='none', cull='b')
            for dx in (-0.025, 0.025):
                m.bx(x + dx - 0.012, x + dx + 0.012, yy - 0.012, yy + 0.012, 0.009, 0.03, 'steel', hull='none', cull='b')
