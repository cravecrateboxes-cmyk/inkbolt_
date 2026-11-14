"""kit-toyfactory modelled detail (tactical look plan Stage 11): the fixings a real, tidy toy plant shows up close.

Walls: a kick rail above the skirting, cladding laps, clerestory sill / head / mullion depth, a cap trim, conduit and a
junction box on the plain module; pilasters and columns: stiffeners, splice plates, cap plates; corner posts: yellow
corner guards; belts and rollers: leg foot plates with anchor bolts, side access panels with screws, a lower rail;
hoods: access panels, toe kick, motor cooling fins; benches: edge bands, drawers, foot plates; tote rack, andon, gate
frame, fire exit (frame, hinges, kick plate, closer), fire point straps, tall racks (base plates, beam clips, capacity
plates, protectors), hanging boards (edge trims, hanger plates).

Rules (KIT-BRIEF): every part is hull='none' (no outline shell), at least 3 mm proud, embedded 3 mm, horizontal runs
stop 5 mm short of the piece sides. Nothing here changes a piece's origin, footprint or collision boxes: it only adds."""
from tf_base import *  # noqa: F401,F403

E = 0.003
ST, STD = 'steel', 'steelD'


def dbx(m, x0, x1, yf, d, z0, z1, c, s=-1, cull=None):
    """box d proud of a face at y = yf (s -1: face looks toward -Y, s +1: toward +Y), sunk E into it"""
    y0, y1 = (yf - d, yf + E) if s < 0 else (yf - E, yf + d)
    if cull is None:
        cull = ('k' if s < 0 else 'f') + ('b' if z0 < 0.01 else '')
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def screw(m, x, z, yf, d, c=STD, sz=0.02):
    """a screw head on a -Y face at yf that carries a plate d proud (d = 0: on the face itself)"""
    m.bx(x - sz / 2, x + sz / 2, yf - d - 0.005, yf - d + E, z - sz / 2, z + sz / 2, c, hull='none', cull='k')


def access_panel(m, x0, x1, z0, z1, yf, c='machW', d=0.008, handle=True):
    dbx(m, x0, x1, yf, d, z0, z1, c)
    for x in (x0 + 0.03, x1 - 0.03):
        for z in (z0 + 0.03, z1 - 0.03):
            screw(m, x, z, yf, d)
    if handle:
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        m.bx(xm - 0.03, xm + 0.03, yf - d - 0.014, yf - d + E, zm - 0.012, zm + 0.012, STD, hull='none', cull='k')


def junction(m, x, z, yf, w=0.18, h=0.2, d=0.08, c=ST, lid=STD):
    dbx(m, x - w / 2, x + w / 2, yf, d, z - h / 2, z + h / 2, c)
    m.bx(x - w / 2 + 0.02, x + w / 2 - 0.02, yf - d - 0.006, yf - d + 0.001, z - h / 2 + 0.02, z + h / 2 - 0.02, lid, hull='none', cull='k')


def conduit(m, x0, x1, z, yf, clips=(), c=STD, cc=ST, r=0.02):
    m.cy((x0, yf - 0.032, z), r, r, x1 - x0, c, seg=6, rot=(0, 90, 0), hull='none')
    for x in clips:
        dbx(m, x - 0.015, x + 0.015, yf, 0.058, z - 0.028, z + 0.028, cc)


def foot_bolt(m, x, y, z0=0.013):
    m.bx(x - 0.011, x + 0.011, y - 0.011, y + 0.011, z0, z0 + 0.023, ST, hull='none', cull='b')


def foot_plate(m, x, y, hx=0.06, hy=0.06, bolts=True, c=STD):
    m.bx(x - hx, x + hx, y - hy, y + hy, 0.004, 0.016, c, hull='none', cull='b')
    if bolts:
        for dx in (-1, 1):
            foot_bolt(m, x + dx * (hx - 0.022), y)


# ================================================================ walls
def wall_detail(m, S, plain=False):
    """a full 1 m wall module (x -0.5..0.5, front y = -0.5)"""
    x0, x1 = -0.495, 0.495
    if plain != 'door':
        dbx(m, x0, x1, -0.5, 0.012, 0.15, 0.23, ST)                       # kick rail above the skirting
    dbx(m, x0, x1, -0.5, 0.02, 11.88, 11.996, ST)                          # cap trim under the roof deck
    if S == 'P':
        for z in (4.2, 7.5):
            dbx(m, x0, x1, -0.5, 0.009, z, z + 0.03, 'cladD')              # cladding laps
        dbx(m, x0, x1, -0.5, 0.05, 8.30, 8.40, ST, cull='k')               # clerestory sill and head
        dbx(m, x0, x1, -0.5, 0.05, 10.2, 10.28, ST, cull='k')
        dbx(m, -0.02, 0.02, -0.5, 0.03, 8.4, 10.2, STD, cull='k')          # mullion with depth
        cz = 3.4
    else:
        for z in (3.3, 4.7, 7.3, 8.5):
            dbx(m, x0, x1, -0.5, 0.009, z, z + 0.03, 'cladD')
        dbx(m, x0, x1, -0.5, 0.05, 9.50, 9.60, ST, cull='k')
        dbx(m, x0, x1, -0.5, 0.05, 10.6, 10.68, ST, cull='k')
        cz = 3.0
    if plain is True:   # a conduit run with a drop to a junction box
        conduit(m, -0.495, 0.495, cz, -0.5, clips=(-0.3, 0.1, 0.4))
        m.cy((-0.21, -0.532, 1.7), 0.02, 0.02, cz - 1.7, STD, seg=6, hull='none')
        junction(m, -0.21, 1.6, -0.5, w=0.2, h=0.2, d=0.09)


def pilaster_detail(m):
    """steel I-pilaster standing proud of the wall: web stiffeners, a splice plate with bolts, a cap plate"""
    for z in (1.6, 4.5, 7.5, 10.5):
        for sx in (-1, 1):
            a, b = sorted((sx * 0.033, sx * 0.17))
            m.bx(a, b, -0.765, -0.561, z, z + 0.03, ST, hull='none', cull='')
    dbx(m, -0.13, 0.13, -0.82, 0.012, 6.0, 6.6, ST)
    for x in (-0.09, 0.09):
        for z in (6.07, 6.53):
            screw(m, x, z, -0.82, 0.012, STD, sz=0.024)
    m.bx(-0.2, 0.2, -0.84, -0.497, 11.9, 11.99, ST, hull='none', cull='b')


def corner_guards(m):
    """four yellow angle guards on the vertical edges of a corner post"""
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa = sorted((sx * 0.497, sx * 0.513))
            ya = sorted((sy * 0.44, sy * 0.513))
            m.bx(xa[0], xa[1], ya[0], ya[1], 0.15, 1.3, 'hazY', hull='none', cull='b')
            xb = sorted((sx * 0.44, sx * 0.497))
            yb = sorted((sy * 0.497, sy * 0.513))
            m.bx(xb[0], xb[1], yb[0], yb[1], 0.15, 1.3, 'hazY', hull='none', cull='b')


def exit_detail(m):
    """fire exit: frame, hinges, kick plate, door closer (leaf y -0.56..-0.503, x +-0.48)"""
    for sx in (-1, 1):
        a, b = sorted((sx * 0.495, sx * 0.472))
        m.bx(a, b, -0.57, -0.497, 0.0, 2.34, STD, hull='none', cull='bk')
    m.bx(-0.485, 0.485, -0.575, -0.497, 2.296, 2.345, STD, hull='none', cull='k')
    dbx(m, -0.41, 0.41, -0.56, 0.012, 0.03, 0.28, STD)
    for z in (0.3, 1.15, 2.0):
        dbx(m, -0.47, -0.43, -0.56, 0.014, z, z + 0.1, 'chrome')
    dbx(m, 0.1, 0.4, -0.56, 0.04, 2.2, 2.26, STD)
    dbx(m, 0.09, 0.13, -0.56, 0.06, 2.19, 2.32, STD)


def fire_extras(m, x=0.0):
    for z in (0.63, 0.88):
        m.cy((x, -0.62, z), 0.104, 0.104, 0.03, 'black', seg=8, hull='none')


def panel_detail(m):
    for z in (1.12, 2.38):
        for x in (-0.3, 0.3):
            screw(m, x, z, -0.68, 0.0, STD, sz=0.026)
    dbx(m, 0.2, 0.26, -0.68, 0.03, 1.5, 1.75, STD)


# ================================================================ columns
def column_detail(m):
    """Column: guard cap, splice plates with bolts front and back, top cap plate"""
    m.cy((0, 0, 1.197), 0.352, 0.352, 0.03, STD, seg=12, hull='none')
    for yf, s in ((-0.16, -1), (0.16, 1)):
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            dbx(m, -0.12, 0.12, -0.16, 0.012, 5.0, 5.6, ST)
            for x in (-0.08, 0.08):
                for z in (5.07, 5.53):
                    screw(m, x, z, -0.16, 0.012, STD, sz=0.024)
    m.bx(-0.2, 0.2, -0.2, 0.2, 11.9, 11.996, ST, hull='none', cull='b')


def deck_column_detail(m):
    """mezzanine deck column: a base plate with anchor bolts"""
    foot_plate(m, 0.0, 0.0, 0.17, 0.17, bolts=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot_bolt(m, sx * 0.14, sy * 0.14)


# ================================================================ belts, hoods, rollers
def belt_detail(m):
    for s in (-1, 1):
        foot_plate(m, 0.0, s * 0.38, 0.08, 0.08)
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            dbx(m, -0.495, 0.495, -0.48, 0.012, 0.655, 0.70, STD)           # lower flange
            access_panel(m, -0.27, 0.27, 0.72, 0.86, -0.48)


def rollers_detail(m):
    for s in (-1, 1):
        foot_plate(m, 0.0, s * 0.35, 0.07, 0.07)
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            dbx(m, -0.495, 0.495, -0.44, 0.01, 0.655, 0.69, STD)
            for x in (-0.35, 0.0, 0.35):
                screw(m, x, 0.82, -0.44, 0.0, STD, sz=0.022)               # fixing screws along the frame


def hood_detail(m, kind):
    sx = -1 if kind == 'Feed' else 1
    for s in (-1, 1):
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            dbx(m, -0.495, 0.495, -0.5, 0.012, 0.988, 1.03, STD)           # toe kick
            if s < 0:
                access_panel(m, 0.27, 0.46, 1.3, 1.8, -0.5)
            else:
                access_panel(m, -0.35, 0.35, 1.25, 1.8, -0.5)
    for s2 in (-1, 1):                                                      # motor cooling fins
        ya, yb = sorted((s2 * 0.217, s2 * 0.232))
        a, b = sorted((sx * 0.53, sx * 0.62))
        for z in (0.66, 0.78, 0.9, 1.02, 1.14):
            m.bx(a, b, ya, yb, z, z + 0.03, ST, hull='none', cull='')
    a, b = sorted((sx * 0.54, sx * 0.6))
    m.bx(a, b, -0.07, 0.07, 1.297, 1.37, STD, hull='none', cull='b')       # terminal box on the motor


# ================================================================ benches
def bench_detail(m, drawer_x=(0.3, 0.84)):
    for (y0, y1) in ((-0.408, -0.397), (0.397, 0.408)):
        m.bx(-0.945, 0.945, y0, y1, 0.864, 0.916, ST, hull='none', cull='')   # edge bands front and back
    for (x0, x1) in ((-0.958, -0.947), (0.947, 0.958)):
        m.bx(x0, x1, -0.395, 0.395, 0.864, 0.916, ST, hull='none', cull='')
    for (x, y) in ((-0.88, -0.33), (0.88, -0.33), (-0.88, 0.33), (0.88, 0.33)):
        foot_plate(m, x, y, 0.06, 0.06, bolts=False)
    x0, x1 = drawer_x                                                       # a drawer unit hung under the worktop
    m.bx(x0, x1, -0.31, 0.31, 0.62, 0.863, 'machW', hull='none', cull='t')
    dbx(m, x0 + 0.04, x1 - 0.04, -0.31, 0.012, 0.74, 0.76, 'chrome')
    dbx(m, x0 + 0.02, x1 - 0.02, -0.31, 0.006, 0.66, 0.70, STD)


def totes_detail(m):
    for sx in (-1, 1):
        for y in (-0.36, 0.36):
            foot_plate(m, sx * 0.92, y, 0.07, 0.07, bolts=False)
    for s in (-1, 1):
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            for z in (0.3, 0.85, 1.4):
                for x in (-0.8, -0.27, 0.27, 0.8):
                    screw(m, x, z - 0.02, -0.38, 0.0, STD, sz=0.022)


def andon_detail(m):
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot_bolt(m, sx * 0.15, sy * 0.15, 0.057)
    m.cy((0, 0, 0.057), 0.065, 0.065, 0.05, STD, seg=8, hull='none')


# ================================================================ gate frame
def gate_detail(m):
    for sx in (-1, 1):
        a, b = sorted((sx * 1.47, sx * 1.88))
        m.bx(a, b, -0.65, 0.65, 0.004, 0.04, ST, hull='none', cull='b')
        for x in (1.55, 1.8):
            for sy in (-1, 1):
                foot_bolt(m, sx * x, sy * 0.636, 0.037)
    for s in (-1, 1):
        with at(m, 0, 0, 0, 0 if s < 0 else 180):
            junction(m, -1.7, 3.52, -0.62, w=0.3, h=0.3, d=0.09)
            conduit(m, -1.55, -0.85, 3.52, -0.65, clips=(-1.4, -1.1))


# ================================================================ racks and boards
def rack_detail(m, end):
    """Tall racks: base plate, rack protector, capacity plates, beam end clips (both aisles, x not mirrored)"""
    ups = [-1.5] + ([1.42] if end == 'R' else [])
    xr = 1.42 if end == 'R' else 1.5
    for s in (-1, 1):
        yf = s * 1.0
        for x in ups:
            xa, xb = x + 0.005, x + 0.075
            dbx(m, xa, xb, yf, 0.008, 1.0, 1.2, 'paper', s)                    # capacity plate on the upright
            a, b = sorted((yf + s * 0.0075, yf + s * 0.0115))
            m.bx(xa + 0.01, xb - 0.01, a, b, 1.12, 1.18, 'brandR', hull='none', cull='f' if s > 0 else 'k')
        if end != 'L':                                                         # plate and protector on the plain upright
            a, b = sorted((s * 0.9, s * 1.04))
            m.bx(-1.49, -1.39, a, b, 0.004, 0.016, STD, hull='none', cull='b')
            dbx(m, -1.495, -1.425, yf, 0.014, 0.004, 0.4, 'hazY', s)
        for z in (1.9, 3.8, 5.7, 7.6):
            for xa, xb in ((-1.415, -1.34), (xr - 0.075, xr - 0.005)):
                dbx(m, xa, xb, yf, 0.007, z - 0.1, z - 0.02, STD, s)           # beam end clips


def sign_frame(m, hw, th, z0, z1, xhang):
    """steel edge trims along the bottom and top of a hanging board and a hanger plate at each rod"""
    for s in (-1, 1):
        ya, yb = sorted((s * (th - 0.003), s * (th + 0.008)))
        m.bx(-hw + 0.005, hw - 0.005, ya, yb, z0 - 0.003, z0 + 0.03, STD, hull='none', cull='')
        m.bx(-hw + 0.005, hw - 0.005, ya, yb, z1 - 0.03, z1 + 0.003, STD, hull='none', cull='')
    for x in xhang:
        m.bx(x - 0.05, x + 0.05, -0.078, 0.078, z1 - 0.003, z1 + 0.03, STD, hull='none', cull='')
