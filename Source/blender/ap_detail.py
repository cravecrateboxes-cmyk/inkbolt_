"""kit-airport modelled detail (tactical look plan Stage 11): the finish of a clean modern terminal and its apron kit.

Walls: skirting caps, panel-joint fixings, reveal trims, curtain-wall pressure caps and transom caps, frames round the
signs and lightboxes, a door frame with hinges. Check-in: kick plates, desk seams and edge bands, bag-tag printer
bezels, weigh-belt guards and roller ends, collector-belt cleats, rail bumpers and bolts. Seating, benches, kiosk, board,
posts and stanchions: foot plates and bolts. Columns: base collars and anchor nuts, guard band, joint rings. Jet
bridge, apron vehicles: wheel hubs, hazard bands, rivet rows, panel seams, hydraulic lines, handles.

Rules (KIT-BRIEF): every part is hull='none' (no outline shell), stands >= 3 mm proud of what it sits on and sinks 3 mm
into it, horizontal runs stop 5 mm short of a module's sides. Nothing here changes a piece's origin, footprint,
collision boxes or the parts already drawn: it only adds shapes."""
import math

E = 0.003          # sink into the face behind
HOLD = 0.495       # horizontal runs stop 5 mm short of a module side


def P(m, x0, x1, y0, y1, z0, z1, c, cull=''):
    return m.bx(x0, x1, y0, y1, z0, z1, c, hull='none', cull=cull)


def fz(m, x0, x1, z0, z1, yf, d, c, s=-1, cull=''):
    """a box d proud of a face at y = yf that looks toward s (-1: -Y, +1: +Y), sunk E into it"""
    cull += 'k' if s < 0 else 'f'
    if z0 < 0.01:
        cull += 'b'
    if s < 0:
        return P(m, x0, x1, yf - d, yf + E, z0, z1, c, cull)
    return P(m, x0, x1, yf - E, yf + d, z0, z1, c, cull)


def fx(m, y0, y1, z0, z1, xf, d, c, s=1, cull=''):
    """the same on a face at x = xf looking toward s (+1: +X, -1: -X)"""
    cull += 'l' if s > 0 else 'r'
    if z0 < 0.01:
        cull += 'b'
    if s > 0:
        return P(m, xf - E, xf + d, y0, y1, z0, z1, c, cull)
    return P(m, xf - d, xf + E, y0, y1, z0, z1, c, cull)


def bolts_y(m, xs, z, yf, c, s=-1, sz=0.022, d=0.008):
    for x in xs:
        fz(m, x - sz / 2, x + sz / 2, z - sz / 2, z + sz / 2, yf, d, c, s)


def bolts_x(m, ys, z, xf, c, s=1, sz=0.022, d=0.008):
    for y in ys:
        fx(m, y - sz / 2, y + sz / 2, z - sz / 2, z + sz / 2, xf, d, c, s)


def frame_y(m, x0, x1, z0, z1, yf, c, s=-1, t=0.015, d=0.012):
    """a frame of four strips standing OUTSIDE the rectangle (x0..x1, z0..z1) on a face at y = yf"""
    fz(m, x0 - t, x1 + t, z0 - t, z0, yf, d, c, s)
    fz(m, x0 - t, x1 + t, z1, z1 + t, yf, d, c, s)
    fz(m, x0 - t, x0, z0, z1, yf, d, c, s)
    fz(m, x1, x1 + t, z0, z1, yf, d, c, s)


def ring_z(m, x, y, z0, z1, r, c, seg):
    return m.cy((x, y, z0), r, r, z1 - z0, c, seg=seg, hull='none')


# ------------------------------------------------------------------------------------------------ terminal walls
def wall_fit(m, z0=0.0, z1=14.0):
    """skirting cap over the stone plinth, a reveal trim over the timber band, panel-joint fixings, a cove shadow trim"""
    if z0 < 0.15:
        fz(m, -HOLD, HOLD, 0.15, 0.18, -0.5, 0.012, 'steel')
    if z1 > 3.3:
        fz(m, -HOLD, HOLD, 3.3, 3.34, -0.5, 0.012, 'steelD')
        for z in (5.9, 8.5, 11.1):
            bolts_y(m, (-0.25, 0.25), z + 0.06, -0.5, 'steel', sz=0.02)
        fz(m, -HOLD, HOLD, 13.455, 13.5, -0.5, 0.01, 'joint')


def sign_frame(m, kind='way'):
    """frames on the wayfinding sign (x +-0.5, z 4.0 - 4.7, face y = -0.56)"""
    fz(m, -HOLD, HOLD, 4.006, 4.03, -0.56, 0.012, 'chrome')
    fz(m, -HOLD, HOLD, 4.67, 4.694, -0.56, 0.012, 'chrome')
    fz(m, -HOLD, -0.47, 4.03, 4.67, -0.56, 0.012, 'chrome')
    fz(m, 0.47, HOLD, 4.03, 4.67, -0.56, 0.012, 'chrome')


def lightbox_frame(m):
    """bezel round a lightbox ad: box x +-0.45, z 0.55 - 3.0, face y = -0.62, lit area x +-0.4, z 0.6 - 2.95"""
    fz(m, -0.447, 0.447, 0.558, 0.597, -0.62, 0.012, 'chrome')
    fz(m, -0.447, 0.447, 2.953, 2.992, -0.62, 0.012, 'chrome')
    fz(m, -0.447, -0.41, 0.597, 2.953, -0.62, 0.012, 'chrome')
    fz(m, 0.41, 0.447, 0.597, 2.953, -0.62, 0.012, 'chrome')


def fids_frame(m):
    """a steel wrap round the flight-information panel (x +-0.48, z 1.6 - 3.6, face y = -0.6)"""
    fz(m, -HOLD, HOLD, 1.585, 1.603, -0.6, 0.012, 'chrome')
    fz(m, -HOLD, HOLD, 3.597, 3.615, -0.6, 0.012, 'chrome')
    fz(m, -HOLD, -0.477, 1.603, 3.597, -0.6, 0.012, 'chrome')
    fz(m, 0.477, HOLD, 1.603, 3.597, -0.6, 0.012, 'chrome')


def staff_door_fit(m):
    """door frame and three hinges on the grey leaf (x +-0.46, z 0 - 2.3, face y = -0.56)"""
    fz(m, -0.485, 0.485, 2.3, 2.34, -0.56, 0.012, 'steel')
    fz(m, -0.485, -0.46, 0.004, 2.3, -0.56, 0.012, 'steel')
    fz(m, 0.46, 0.485, 0.004, 2.3, -0.56, 0.012, 'steel')
    for z in (0.3, 1.1, 1.9):
        fz(m, -0.45, -0.415, z - 0.06, z + 0.06, -0.56, 0.014, 'chrome')


def corner_post_fit(m):
    """stainless corner guards and a skirting cap round the four-sided corner post"""
    for sy in (-1, 1):
        fz(m, -HOLD, HOLD, 0.15, 0.18, sy * 0.5, 0.012, 'steel', sy)
    for sx in (-1, 1):
        fx(m, -HOLD, HOLD, 0.15, 0.18, sx * 0.5, 0.012, 'steel', sx)
    for sx in (-1, 1):
        for sy in (-1, 1):
            a, b = sorted((sx * 0.44, sx * 0.495))
            fz(m, a, b, 0.19, 2.95, sy * 0.5, 0.012, 'steel', sy)
            a, b = sorted((sy * 0.44, sy * 0.495))
            fx(m, a, b, 0.19, 2.95, sx * 0.5, 0.012, 'steel', sx)


def core_fit(m):
    fz(m, -HOLD, HOLD, 0.004, 0.1, -0.5, 0.012, 'steelD')
    fz(m, -HOLD, HOLD, 13.4, 13.5, -0.5, 0.01, 'concD')


# ------------------------------------------------------------------------------------------------ curtain wall
def curtain_fit(m, kind, z0=0.0):
    """coping and skirting on the upstand, transom caps, head flashing; kind M: a pressure cap with screws on the mullion"""
    yg = -0.35
    if z0 < 0.3:
        P(m, -HOLD, HOLD, -0.508, -0.46, 0.297, 0.314, 'steel', 'k')
        fz(m, -HOLD, HOLD, 0.085, 0.1, -0.5, 0.012, 'steel')
    for (za, zb) in ((3.4, 3.48), (7.0, 7.08), (10.6, 10.68)):
        if za >= z0:
            fz(m, -HOLD, HOLD, za + 0.012, zb - 0.012, yg - 0.04, 0.012, 'steel')
    fz(m, -HOLD, HOLD, 13.56, 13.6, -0.5, 0.012, 'steelD')
    if kind == 'M':
        zc = 0.31 if z0 < 0.3 else z0 + 0.35
        P(m, -0.03, 0.03, -0.436, -0.417, zc, 13.45, 'steel', 'k')
        z = zc + 0.4
        while z < 13.3:
            if not any(za - 0.05 < z < zb + 0.05 for (za, zb) in ((3.4, 3.48), (7.0, 7.08), (10.6, 10.68))):
                P(m, -0.011, 0.011, -0.444, -0.433, z - 0.011, z + 0.011, 'chrome', 'k')
            z += 1.2


def corner_glass_fit(m):
    P(m, -HOLD, HOLD, -0.508, -0.46, 0.297, 0.314, 'steel', 'k')
    P(m, -0.07, 0.07, -0.486, -0.467, 0.31, 13.9, 'steel', 'k')


def entrance_fit(m):
    """sensor bar over the sliding doors, a trim strip under the header, a frame round the lit strip"""
    P(m, -0.1, 0.1, -0.572, -0.557, 3.0, 3.045, 'black', 'k')
    fz(m, -HOLD, HOLD, 2.71, 2.76, -0.56, 0.01, 'steel')
    frame_y(m, -0.4, 0.4, 2.78, 2.98, -0.56, 'chrome', t=0.015)


def bridge_fit(m):
    """frame round the gate display, trim strip on the header"""
    fz(m, -HOLD, HOLD, 2.52, 2.57, -0.56, 0.01, 'steel')
    frame_y(m, -0.4, 0.4, 2.6, 3.3, -0.56, 'chrome', t=0.015)


# ------------------------------------------------------------------------------------------------ check-in
def desk_side(m, s):
    """one desk face (s = -1: y = -3, s = +1: y = +3): kick plate, seams, edge band, bag-tag printer, weigh-belt guards"""
    y0 = 3.0 * s
    fz(m, -1.43, -0.02, 0.004, 0.1, y0, 0.012, 'steel', s)
    for x in (-1.05, -0.45):
        fz(m, x - 0.006, x + 0.006, 0.3, 0.995, y0, 0.008, 'steelD', s)
    fz(m, -HOLD - 0.0, 0.045, 1.012, 1.048, y0 + 0.02 * s, 0.01, 'chrome', s)
    # bag-tag printer on the desk top, bezel toward the agent
    P(m, -1.4, -1.1, s * 2.38, s * 2.68, 1.057, 1.13, 'steelD')
    yi = s * 2.38
    P(m, -1.37, -1.13, yi + s * E, yi - s * 0.008, 1.07, 1.115, 'black')
    P(m, -1.3, -1.2, yi - s * 0.004, yi - s * 0.05, 1.09, 1.094, 'paper')
    # weigh belt: side guards, roller ends, kick plate and bolts
    for a, b in ((2.94, 2.99), (1.205, 1.255)):
        P(m, 0.07, 1.48, s * a, s * b, 0.417, 0.47, 'steelD', 'b')
    for x, r in ((0.09, 0.03), (1.465, 0.025)):
        m.cy((x, min(s * 1.26, s * 2.94), 0.425), r, r, 1.68, 'steel', seg=6, rot=(-90, 0, 0), hull='none')
    fz(m, 0.07, 1.48, 0.004, 0.08, y0, 0.01, 'steelD', s)
    bolts_y(m, (0.25, 0.55, 0.85, 1.15), 0.04, y0 + s * 0.01, 'chrome', s, sz=0.02)


def belt_fit(m, x0, x1, belt):
    """collector belt: rail bumpers and bolts, cleats on the rubber, roller ends at an open end"""
    for s in (-1, 1):
        P(m, x0 + 0.005, x1 - 0.005, s * 0.475, s * 0.525, belt + 0.117, belt + 0.132, 'black', 'b')
        x = x0 + 0.3
        while x < x1 - 0.2:
            P(m, x - 0.011, x + 0.011, s * 0.453, s * 0.442, belt + 0.05, belt + 0.072, 'chrome')
            x += 0.55
    x = x0 + 0.25
    while x < x1 - 0.15:
        P(m, x - 0.012, x + 0.012, -0.43, 0.43, belt - 0.003, belt + 0.006, 'black', 'b')
        x += 0.3
    for x, open_end in ((x0 + 0.04, x0 < -1.4), (x1 - 0.04, x1 > 1.4)):
        if open_end:
            m.cy((x, -0.43, belt), 0.03, 0.03, 0.86, 'steel', seg=6, rot=(-90, 0, 0), hull='none')


def island_end_fit(m):
    """the lightbox totem: a plinth round three faces and a coping"""
    fz(m, -1.44, -1.16, 0.004, 0.1, -1.0, 0.012, 'steelD', -1)
    fz(m, -1.44, -1.16, 0.004, 0.1, 1.0, 0.012, 'steelD', 1)
    fx(m, -0.995, 0.995, 0.004, 0.1, -1.45, 0.012, 'steelD', -1)
    P(m, -1.46, -1.14, -1.01, 1.01, 3.197, 3.215, 'steel', 'b')


def island_hood_fit(m):
    """the bag hood: plinth, cap trim, seams and a rivet row on both long faces"""
    for s in (-1, 1):
        yf = s * 0.7
        fz(m, 0.405, 1.495, 0.004, 0.1, yf, 0.012, 'steelD', s)
        fz(m, 0.405, 1.495, 1.43, 1.496, yf, 0.018, 'steelD', s)
        fz(m, 0.944, 0.956, 0.1, 1.08, yf, 0.008, 'steelD', s)
        bolts_y(m, [0.5 + 0.18 * i for i in range(6)], 1.02, yf, 'chrome', s, sz=0.02)


def kiosk_fit(m):
    """anchor bolts on the base plate, a bezel round the ticket slot, a panel seam"""
    for x in (-0.25, 0.25):
        for y in (-0.22, 0.22):
            P(m, x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.077, 0.1, 'chrome', 'b')
    P(m, -0.14, 0.14, -0.214, -0.197, 0.38, 0.395, 'steel', 'k')
    P(m, -0.14, 0.14, -0.214, -0.197, 0.285, 0.3, 'steel', 'k')
    P(m, -0.14, -0.12, -0.214, -0.197, 0.3, 0.38, 'steel', 'k')
    P(m, 0.12, 0.14, -0.214, -0.197, 0.3, 0.38, 'steel', 'k')
    P(m, -0.275, 0.275, -0.212, -0.197, 0.848, 0.862, 'joint', 'k')


def board_fit(m):
    """departures board: anchor bolts on the base plates, flashing under and over the panel"""
    for x in (-4.3, 4.3):
        for dx in (-0.22, 0.22):
            for y in (-0.37, 0.37):
                P(m, x + dx - 0.02, x + dx + 0.02, y - 0.02, y + 0.02, 0.117, 0.145, 'steel', 'b')
    P(m, -4.595, 4.595, -0.31, 0.31, 6.397, 6.42, 'steelD')
    P(m, -4.595, 4.595, -0.31, 0.31, 2.78, 2.803, 'steelD', 'b')


def seats_fit(m):
    """gate seating: foot plates with bolts, beam bolts at the legs, rubber caps on the armrests"""
    for x in (-1.6, 1.6):
        P(m, x - 0.09, x + 0.09, -0.27, 0.27, 0.0, 0.02, 'steelD', 'b')
        for dx in (-0.065, 0.065):
            for y in (-0.2, 0.2):
                P(m, x + dx - 0.0125, x + dx + 0.0125, y - 0.0125, y + 0.0125, 0.017, 0.032, 'chrome', 'b')
    bolts_y(m, (-1.65, -1.55, 1.55, 1.65), 0.42, -0.3, 'chrome', sz=0.025)
    for k in range(5):
        x = max(-1.92, min(1.92, -2.0 + k * 1.0))
        P(m, x - 0.04, x + 0.04, -0.285, 0.145, 0.676, 0.694, 'steelD', 'b')


def bench_fit(m):
    for x in (-1.5, 1.5):
        P(m, x - 0.09, x + 0.09, -0.24, 0.24, 0.0, 0.015, 'steelD', 'b')
        for dx in (-0.07, 0.07):
            for y in (-0.19, 0.19):
                P(m, x + dx - 0.0125, x + dx + 0.0125, y - 0.0125, y + 0.0125, 0.012, 0.03, 'chrome', 'b')
    P(m, -1.45, 1.45, -0.03, 0.03, 0.36, 0.423, 'steelD', 'b')


def beltpost_fit(m):
    m.cy((0, 0, 0.975), 0.06, 0.06, 0.025, 'chrome', seg=6, hull='none')
    m.cy((0, 0, 0.2), 0.055, 0.055, 0.06, 'steelD', seg=6, hull='none')
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        x, y = math.cos(a) * 0.11, math.sin(a) * 0.11
        P(m, x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.027, 0.05, 'chrome', 'b')


def gatepod_fit(m):
    fz(m, -1.395, 1.395, 0.004, 0.1, -0.3, 0.012, 'steel')
    fz(m, -1.445, 1.445, 1.06, 1.09, -0.4, 0.01, 'chrome')
    for x in (-0.7, 0.7):
        fz(m, x - 0.006, x + 0.006, 0.1, 1.04, -0.3, 0.008, 'steelD')
    frame_y(m, -1.2, 1.2, 1.8, 2.5, 0.4, 'chrome', s=-1, t=0.015)


def charge_fit(m):
    P(m, -0.192, 0.192, -0.192, 0.192, 0.0, 0.08, 'steelD', 'b')


def railpost_fit(m, half, top, c='steelD', capc='steel'):
    """base plate with four bolts and a cap on a square rail post"""
    pl = half + 0.03
    P(m, -pl, pl, -pl, pl, 0.0, 0.012, c, 'b')
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (half + 0.0155), sy * (half + 0.0155)
            P(m, x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0.009, 0.026, 'chrome', 'b')
    P(m, -half - 0.006, half + 0.006, -half - 0.006, half + 0.006, top - 0.008, top + 0.006, capc)


def deckcol_fit(m, top):
    for a in range(4):
        x, y = math.cos(a * math.pi / 2) * 0.24, math.sin(a * math.pi / 2) * 0.24
        P(m, x - 0.0125, x + 0.0125, y - 0.0125, y + 0.0125, 0.117, 0.145, 'chrome', 'b')
    ring_z(m, 0, 0, top - 0.2, top - 0.1, 0.236, 'steel', 8)


def column_fit(m):
    """the tree column: stainless collar over the plinth with anchor nuts, a bump rail, joint rings, a branch collar"""
    ring_z(m, 0, 0, 0.152, 0.30, 0.336, 'steel', 8)
    ring_z(m, 0, 0, 1.05, 1.2, 0.34, 'steel', 8)
    for z in (4.0, 6.5):
        ring_z(m, 0, 0, z, z + 0.02, 0.35, 'joint', 8)
    ring_z(m, 0, 0, 8.2, 8.32, 0.373, 'steelD', 8)
    for a in range(8):
        x, y = math.cos(a * math.pi / 4) * 0.385, math.sin(a * math.pi / 4) * 0.385
        P(m, x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.147, 0.185, 'chrome')


# ------------------------------------------------------------------------------------------------ jet bridge and apron
def hub(m, x, y, r, w):
    """a raised wheel hub: a rim ring and a boss on the outer face"""
    s = 1 if x >= 0 else -1
    xo = x + s * w / 2
    for (rr, a, b, c, sg) in ((r * 0.46, -0.004, 0.008, 'steelD', 8), (r * 0.2, 0.004, 0.016, 'chrome', 6)):
        xa, xb = (xo + s * a, xo + s * b)
        m.cy((min(xa, xb), y, r), rr, rr, abs(xb - xa), c, seg=sg, rot=(0, 90, 0), hull='none')


def tunnel_fit(m):
    """jet-bridge tunnel section (stretched along X by the theme): long strips only"""
    for s in (-1, 1):
        yf = s * 1.4
        fz(m, 0.005, 0.995, 0.004, 0.12, yf, 0.014, 'rubber', s)
        fz(m, 0.005, 0.995, 0.97, 1.0, yf, 0.012, 'chrome', s)
        fz(m, 0.005, 0.995, 1.7, 1.73, yf, 0.012, 'chrome', s)
        fz(m, 0.005, 0.995, 2.6, 2.68, yf, 0.02, 'steel', s)
    for y in (-0.5, 0.5):
        P(m, 0.005, 0.995, y - 0.02, y + 0.02, 2.698, 2.714, 'steel', 'b')


def cab_fit(m):
    """jet-bridge cab: window frames, panel seam, hazard band, rivet rows, bumper stripes"""
    for s in (-1, 1):
        yf = s * 1.6
        fz(m, -1.04, 0.64, 0.96, 1.0, yf, 0.014, 'chrome', s)
        fz(m, -1.04, 0.64, 1.9, 1.94, yf, 0.014, 'chrome', s)
        fz(m, -1.04, -1.0, 1.0, 1.9, yf, 0.014, 'chrome', s)
        fz(m, 0.6, 0.64, 1.0, 1.9, yf, 0.014, 'chrome', s)
        fz(m, -1.15, 0.95, 0.004, 0.18, yf, 0.012, 'sun', s)
        fz(m, 0.79, 0.81, 0.2, 2.75, yf, 0.008, 'steel', s)
        for z in (0.5, 2.5):
            bolts_y(m, [-1.1 + 0.3 * i for i in range(8)], z, yf, 'steel', s, sz=0.016, d=0.006)
    for i in range(7):
        y = -1.2 + i * 0.4
        P(m, 1.744, 1.753, y - 0.075, y + 0.075, -0.1, -0.03, 'black', 'b')


def drive_fit(m, GY):
    for y in (-0.6, 0.6):
        s = -1 if y < 0 else 1
        yc = y + s * (0.15 + 0.032)
        m.cy((0.07, yc, GY + 0.85), 0.035, 0.035, -1.36 - (GY + 0.85), 'chrome', seg=6, hull='none')
        P(m, -0.155, 0.155, y - 0.155, y + 0.155, -2.55, -2.4, 'sun', 'b')
    for s in (-1, 1):
        fz(m, -0.495, 0.495, GY + 0.58, GY + 0.66, s * 1.2, 0.012, 'sun', s)
    for y in (-0.9, 0.9):
        for sx in (-1, 1):
            xo = sx * 0.22
            m.cy((min(xo - sx * 0.004, xo + sx * 0.012), y, GY + 0.35), 0.16, 0.16, 0.016, 'steelD', seg=8, rot=(0, 90, 0), hull='none')
            m.cy((min(xo + sx * 0.008, xo + sx * 0.024), y, GY + 0.35), 0.07, 0.07, 0.016, 'chrome', seg=6, rot=(0, 90, 0), hull='none')


def rotunda_fit(m, GY):
    ring_z(m, 1.6, 0.0, -0.12, 0.0, 1.615, 'rubber', 10)
    ring_z(m, 1.6, 0.0, 1.45, 1.5, 1.615, 'steel', 10)
    ring_z(m, 1.6, 0.0, 2.86, 2.92, 1.715, 'steelD', 10)
    ring_z(m, 0.0, 0.0, GY, GY + 0.05, 0.62, 'steelD', 8)
    ring_z(m, 0.0, 0.0, -2.5, -2.4, 0.515, 'sun', 8)


# ------------------------------------------------------------------------------------------------ apron vehicles
def tug_fit(m):
    for s in (-1, 1):
        fx(m, -1.75, 1.75, 0.27, 0.35, s * 0.95, 0.012, 'black', s)
        fx(m, -1.7, 1.7, 0.78, 0.8, s * 0.95, 0.008, 'steelD', s)
        bolts_x(m, [-1.6 + 0.4 * i for i in range(9)], 0.72, s * 0.95, 'steelD', s, sz=0.02)
    P(m, -0.9, 0.9, -1.84, -1.797, 0.27, 0.38, 'black', 'k')


def tractor_fit(m):
    for s in (-1, 1):
        fx(m, -0.9, 0.25, 0.32, 0.4, s * 0.6, 0.012, 'black', s)
        bolts_x(m, [-0.8 + 0.3 * i for i in range(4)], 0.88, s * 0.6, 'steelD', s, sz=0.02)
    P(m, -0.55, 0.55, -0.98, -0.947, 0.32, 0.4, 'black', 'k')


def cart_fit(m):
    for s in (-1, 1):
        fx(m, -1.2, 1.2, 0.46, 0.54, s * 0.85, 0.012, 'sun', s)
        bolts_x(m, [-1.1 + 0.275 * i for i in range(9)], 0.5, s * 0.85, 'chrome', s, sz=0.02, d=0.016)
        P(m, s * 0.79 - 0.045, s * 0.79 + 0.045, -1.245, 1.245, 0.847, 0.862, 'steelD', 'b')
        fz(m, -0.875, 0.875, 1.76, 1.8, s * 1.33, 0.012, 'steelD', s)
    for y in (-0.8, 0.0, 0.8):
        P(m, -0.87, 0.87, y - 0.02, y + 0.02, 1.818, 1.836, 'steelD', 'b')


def fuel_fit(m):
    for y in (-1.25, -0.8, 2.15, 2.5):
        m.cy((0.0, y, 1.85), 1.115, 1.115, 0.06, 'steelD', seg=12, rot=(-90, 0, 0), hull='none')
    m.cy((0.0, 0.5, 2.94), 0.28, 0.28, 0.1, 'steelD', seg=8, hull='none')
    m.cy((0.0, 0.5, 3.03), 0.2, 0.2, 0.04, 'steel', seg=8, hull='none')
    for xa in (-0.62, 0.597):
        m.cy((xa, 3.0, 2.25), 0.38, 0.38, 0.023, 'steelD', seg=8, rot=(0, 90, 0), hull='none')
    P(m, -1.15, 1.15, -3.44, -3.397, 0.62, 0.74, 'black', 'k')


def stairtruck_fit(m, DOCK):
    for s in (-1, 1):
        x = s * 0.82
        for i in range(8):
            y = 2.4 - i * 0.55
            zl = (2.6 - y) / 4.2 * (DOCK - 0.25)
            zu = 0.3 + (3.0 - y) / 4.6 * (DOCK - 0.3)
            z = (zl + zu) / 2
            fx(m, y - 0.015, y + 0.015, z - 0.015, z + 0.015, x, 0.011, 'steelD', s)
        fx(m, -2.95, -1.85, 0.7, 0.72, s * 0.95, 0.008, 'steelD', s)
        fx(m, -2.41, -2.39, 0.74, 1.95, s * 0.95, 0.008, 'steelD', s)
        fx(m, -2.95, -1.85, 0.6, 0.68, s * 0.95, 0.012, 'black', s)
    for sy in (-1, 1):
        fz(m, -0.845, 0.845, DOCK + 2.12, DOCK + 2.16, -1.5 if sy > 0 else -3.05, 0.012, 'steelD', sy)


def loader_fit(m):
    for s in (-1, 1):
        fx(m, -2.95, 2.95, 0.36, 0.44, s * 0.8, 0.012, 'black', s)
        bolts_x(m, [-2.7 + 0.45 * i for i in range(13)], 0.6, s * 0.8, 'steelD', s, sz=0.02)
        m.bm_((s * 0.46, 2.95, 0.93), (s * 0.46, -2.85, 2.43), 0.04, 'steelD', hull='none')
        m.bm_((s * 0.3, 1.0, 0.7), (s * 0.3, -0.9, 1.74), 0.05, 'chrome', hull='none')
    m.cy((-0.43, -2.92, 2.36), 0.07, 0.07, 0.86, 'steelD', seg=6, rot=(0, 90, 0), hull='none')


def uld_fit(m):
    for s in (-1, 1):
        fz(m, -0.895, 0.895, 0.31, 0.41, s * 0.9, 0.012, 'sun', s)
    for x in (-0.82, 0.82):
        for y in (-0.82, 0.82):
            P(m, x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.417, 0.46, 'black', 'b')
    for x in (-0.67, 0.67):
        fz(m, x - 0.015, x + 0.015, 0.46, 1.95, -0.75, 0.012, 'steel', -1)


def gpu_fit(m):
    frame_y(m, -0.6, 0.6, 0.6, 1.25, -0.9, 'steel', s=-1, t=0.04, d=0.014)
    for s in (-1, 1):
        xf = s * 0.7
        for y in (-0.25, 0.25):
            fx(m, y - 0.018, y + 0.018, 1.052, 1.088, xf, 0.032, 'black', s)
        fx(m, -0.3, 0.3, 1.04, 1.1, xf + s * 0.032, 0.02, 'black', s)
        for k in range(5):
            z = 0.62 + k * 0.11
            fx(m, -0.4, 0.4, z, z + 0.04, xf, 0.01, 'black', s)
