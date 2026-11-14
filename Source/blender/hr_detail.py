"""kit-highrise modelled detail (tactical look plan Stage 11): fixings and trims on the unique, most-seen pieces.
The map sits over its triangle ceiling, so almost everything here is a flat quad drawn from the visible side only
(2 tris), 3 - 4 mm proud of the face it sits on, never coplanar with a neighbour; horizontal runs stop 5 mm short of
the piece sides. Nothing touches a glow part, a collision box, an origin or a footprint."""
import math


def sq(k, x, z, y, s, c, r=0.009):
    """a flat square fixing (screw head) centred at x, z on a -Y / +Y facing plane."""
    k.qy(x - r, x + r, z - r, z + r, y, s, c)


def sqz(k, x, y, z, c, r=0.012):
    k.qz(x - r, x + r, y - r, y + r, z, 1, c)


def door(k):
    """Lift / sliding door: centre seam of the two leaves (split round the glass slit), slit frame, kick plate edge,
    frame screws, a call plate with up / down buttons on the left leaf, a lip over the header."""
    yl = -0.581
    k.qy(-0.003, 0.003, 0.14, 0.99, yl, -1, 'graphite')
    k.qy(-0.003, 0.003, 2.11, 2.39, yl, -1, 'graphite')
    k.qy(-0.07, -0.064, 1.0, 2.1, yl, -1, 'steelDark')
    k.qy(0.064, 0.07, 1.0, 2.1, yl, -1, 'steelDark')
    k.qy(-0.3, 0.3, 0.125, 0.14, yl, -1, 'steel2')
    for z in (0.34, 1.2, 2.04):
        for x in (-0.44, 0.44):
            sq(k, x, z, -0.563, -1, 'steel2')
    k.qy(-0.37, -0.29, 1.0, 1.36, -0.584, -1, 'black')
    k.qy(-0.345, -0.315, 1.2, 1.3, -0.587, -1, 'cyan')
    k.qy(-0.345, -0.315, 1.05, 1.15, -0.587, -1, 'orange')
    k.qy(-0.48, 0.48, 2.5, 2.54, -0.563, -1, 'steel2')


def sign(k):
    """Sign plate: four corner screws and a steel edge strip."""
    for x in (-0.445, 0.445):
        for z in (2.95, 3.55):
            sq(k, x, z, -0.563, -1, 'steel2', r=0.008)
    k.qy(-0.44, 0.44, 2.905, 2.915, -0.563, -1, 'steel2')


def logo(k):
    """Emblem wall: four studs on the ring flange, a steel frame round the ZENITH plate with corner screws."""
    for a in (45, 135, 225, 315):
        x = 0.39 * math.cos(math.radians(a))
        z = 2.75 + 0.39 * math.sin(math.radians(a))
        sq(k, x, z, -0.558, -1, 'steel2', r=0.014)
    y = -0.5125
    k.qy(-0.472, 0.472, 2.25, 2.262, y, -1, 'steel2')
    k.qy(-0.472, 0.472, 1.938, 1.95, y, -1, 'steel2')
    k.qy(-0.472, -0.46, 1.95, 2.25, y, -1, 'steel2')
    k.qy(0.46, 0.472, 1.95, 2.25, y, -1, 'steel2')
    for x in (-0.485, 0.485):
        for z in (1.96, 2.24):
            sq(k, x, z, y, -1, 'steelDark', r=0.006)


def lock(k):
    """Bio lock: four corner screws on the black panel."""
    for x in (-0.18, 0.18):
        for z in (1.03, 1.72):
            sq(k, x, z, -0.563, -1, 'steel2', r=0.008)


def front_desk(k):
    """Reception counter: toe kick, stone panel seams, frame round the logo panel, edge strip, cable grommets."""
    y = -0.557
    k.qy(-2.895, 2.895, 0.004, 0.045, y, -1, 'graphite')
    for x in (-2.2, -1.5, 1.5, 2.2):
        k.qy(x - 0.006, x + 0.006, 0.12, 1.1, y, -1, 'stone2')
    k.qy(-0.918, 0.918, 1.015, 1.03, y, -1, 'steel2')
    k.qy(-0.918, 0.918, 0.27, 0.285, y, -1, 'steel2')
    k.qy(-0.918, -0.903, 0.285, 1.015, y, -1, 'steel2')
    k.qy(0.903, 0.918, 0.285, 1.015, y, -1, 'steel2')
    for x in (-0.84, 0.84):
        for z in (0.35, 0.95):
            sq(k, x, z, -0.556, -1, 'steel2', r=0.012)
    k.qy(-2.94, 2.94, 1.14, 1.16, -0.626, -1, 'steel2')
    for x in (-2.2, 0.0, 2.2):
        sqz(k, x, -0.3, 1.184, 'black', r=0.035)
        sqz(k, x, -0.3, 1.188, 'steelDark', r=0.02)


def hvac(k):
    """Rooftop unit: service-panel screws, panel seam, louvre frame, lid screws."""
    for f in (-1, 1):
        y = f * 0.953
        for x in (0.16, 1.24):
            for z in (0.36, 1.29):
                sq(k, x, z, f * 0.958, f, 'steelDark', r=0.014)
        k.qy(-0.006, 0.006, 0.2, 1.45, y, f, 'steelDark')
        k.qy(-1.34, -1.30, 0.32, 1.28, y, f, 'steelDark')
        k.qy(-0.10, -0.06, 0.32, 1.28, y, f, 'steelDark')
        k.qy(-1.30, -0.10, 1.25, 1.28, y, f, 'steelDark')
        k.qy(-1.30, -0.10, 0.32, 0.35, y, f, 'steelDark')
    for x in (-1.3, 1.3):
        for yy in (-0.85, 0.85, 0.0):
            sqz(k, x, yy, 1.509, 'steelDark')


def duct(k):
    """Duct section: a bolted flange at each joint."""
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.495, s * 0.455))
        k.bx(x0, x1, -0.318, 0.318, 0.185, 0.765, 'steelDark', ink=False)


def machine_room(k):
    """Lift machine room door: kick plate, hinges; louvre panel corner screws."""
    y = -2.0065
    k.qy(-0.45, 0.45, 0.025, 0.2, y, -1, 'steelDark')
    for z in (0.35, 1.15, 1.95):
        k.qy(-0.46, -0.40, z - 0.06, z + 0.06, y, -1, 'steelDark')
    for x0 in (-2.4, 1.2):
        for x in (x0 + 0.025, x0 + 1.075):
            for z in (1.63, 2.57):
                sq(k, x, z, -2.033, -1, 'steelDark', r=0.008)


def cooling_tower(k):
    """Corner posts up the casing, leg base plates with anchor bolts."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * 1.77, sx * 1.856))
            y0, y1 = sorted((sy * 1.77, sy * 1.856))
            k.bx(x0, x1, y0, y1, 1.006, 2.994, 'steelDark', ink=False)
            cx, cy = sx * 1.85, sy * 1.85
            k.qz(cx - 0.14, cx + 0.14, cy - 0.14, cy + 0.14, 0.012, 1, 'graphite')
            for dx in (-0.1, 0.1):
                for dy in (-0.1, 0.1):
                    sqz(k, cx + dx, cy + dy, 0.016, 'steel2', r=0.016)


def mast(k):
    """Antenna mast: base plates and anchor bolts under the four legs."""
    s = 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * s * 1.2, sy * s * 1.2
            k.qz(cx - 0.1, cx + 0.1, cy - 0.1, cy + 0.1, 0.354, 1, 'graphite')
            for dx in (-0.07, 0.07):
                for dy in (-0.07, 0.07):
                    sqz(k, cx + dx, cy + dy, 0.358, 'steel2', r=0.012)


def hatch(k):
    """Roof hatch: lid corner bolts, hinge plates, a hasp."""
    for x in (-0.27, 0.27):
        for y in (-0.27, 0.27):
            sqz(k, x, y, 0.508, 'steelDark', r=0.016)
    for x in (-0.2, 0.2):
        k.qz(x - 0.05, x + 0.05, 0.2, 0.3, 0.512, 1, 'steelDark')
    k.qz(-0.04, 0.04, -0.3, -0.2, 0.512, 1, 'steelDark')


def bulk_door(k):
    """Plant-room door in the bulk wall: kick plate, hinges, handle."""
    y = -0.5565
    k.qy(-0.34, 0.34, 0.025, 0.2, y, -1, 'steelDark')
    for z in (0.4, 1.1, 1.85):
        k.qy(-0.355, -0.31, z - 0.05, z + 0.05, y, -1, 'steelDark')
    k.qy(0.27, 0.33, 0.98, 1.0, y, -1, 'black')


def server_rack(k):
    """Rack door: a handle bar and a label plate."""
    k.qy(0.386, 0.402, 0.9, 1.3, -0.456, -1, 'steel2')
    k.qy(-0.3, -0.12, 2.09, 2.12, -0.459, -1, 'frost')


def gantry(k):
    """BMU: bolts along the roof rails (both sides of the top rail)."""
    n = 10
    for x in (-1.4, 1.4):
        for i in range(n):
            y = -2.7 + i * 5.4 / (n - 1)
            for dx in (-0.07, 0.07):
                sqz(k, x + dx, y, 0.124, 'steel2', r=0.013)
