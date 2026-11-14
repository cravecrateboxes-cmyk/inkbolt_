"""kit-techhq modelled detail (tactical look plan Stage 11): the finish and fittings of a glass tech headquarters,
added to the pieces the player sees most. Built on the kit_base detail helpers. Every part is ink=False, at least
3 mm proud, embedded 3 mm, horizontal runs stop 5 mm short of the piece's sides. Faces that look toward Blender -Y sit
at the plane y = yf in the current frame (k.push(0, 0, 180) for the back face, 90 / 270 for the +X / -X faces).
Palette names used are the kit's existing ones (steel, steelD, graphite, graphite2, black, oak, oak2, oakD, wallW)."""
import math

from kit_base import PROUD, EMBED, cap_trim, base_trim, bolt_row


def _lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ curtain wall
def window_fittings(k, kind, H, DECK):
    """skirting cap, glazing beads, slab-band nosings, head shadow trim, extra rail stand-offs with flanges; M: pressure
    cap and screws on the mullion reveal; B: bench joints and cushion piping"""
    if kind == 'A':
        k.bx(-0.495, 0.495, -0.516, -0.497, 0.098, 0.112, 'steel', ink=False)
    elif kind == 'M':
        for xa, xb in ((-0.495, -0.067), (0.067, 0.495)):      # the reveal's foot stands between
            k.bx(xa, xb, -0.516, -0.497, 0.098, 0.112, 'steel', ink=False)
    # glazing beads on the glass side of the four glass edges
    for za, zb in ((0.157, 0.187), (DECK - 0.51, DECK - 0.477), (DECK + 0.137, DECK + 0.167), (H - 0.59, H - 0.557)):
        k.bx(-0.495, 0.495, 0.03, 0.063, za, zb, 'steelD', ink=False)
    # slab band: nosing strips top and bottom; head bulkhead shadow trim
    k.bx(-0.495, 0.495, -0.512, -0.497, DECK + 0.06, DECK + 0.083, 'steel', ink=False)
    k.bx(-0.495, 0.495, -0.512, -0.497, DECK - 0.43, DECK - 0.405, 'steelD', ink=False)
    k.bx(-0.495, 0.495, -0.512, -0.497, H - 0.518, H - 0.497, 'steelD', ink=False)
    # extra stand-offs under the safety rails (the centre one is the original), with flange plates on the glass line
    for zr in (0.95, DECK + 0.95):
        for x in (-0.38, 0.38):
            k.bx(x - 0.015, x + 0.015, -0.383, 0.052, zr + 0.015, zr + 0.045, 'steelD', ink=False)
            k.bx(x - 0.035, x + 0.035, 0.045, 0.062, zr - 0.01, zr + 0.05, 'steel', ink=False)
    if kind == 'M':
        k.bx(-0.03, 0.03, -0.545, -0.527, 0.16, H - 0.56, 'steelD', ink=False)       # pressure cap on the reveal
        for i in range(8):
            z = 0.55 + i * 0.95
            k.bx(-0.012, 0.012, -0.549, -0.54, z - 0.012, z + 0.012, 'steel', ink=False)
    elif kind == 'B':
        for x in (-0.25, 0.25):                                                       # board joints on the bench front
            k.bx(x - 0.004, x + 0.004, -0.508, -0.497, 0.13, 0.41, 'oakD', ink=False)
        k.bx(-0.475, 0.475, -0.468, -0.457, 0.505, 0.518, 'wallW', ink=False)         # cushion piping, top front edge
        k.bx(-0.475, 0.475, -0.468, -0.457, 0.466, 0.478, 'wallW', ink=False)         # and bottom
        k.bx(-0.495, 0.495, -0.512, -0.497, 0.105, 0.12, 'steel', ink=False)         # toe kick cap under the oak


def glass_wall_fittings(k, door, H, DECK):
    """lab glass wall: cap strips on the slab band, a shadow line under the head, patch plates at the panel joint"""
    for deg in (0, 180):
        k.push(0, 0, deg)
        cap_trim(k, -0.5, 0.5, -0.5, DECK + 0.04, 'steel', h=0.03, d=0.012)
        base_trim(k, -0.5, 0.5, -0.5, 'steelD', h=0.03, d=0.012, z0=DECK - 0.42)
        k.bx(-0.495, 0.495, -0.132, -0.117, H - 0.403, H - 0.37, 'steelD', ink=False)
        if not door:
            for z in (0.25, 3.15, 4.3, 7.3):
                k.bx(-0.04, 0.04, -0.03, -0.009, z, z + 0.08, 'steel', ink=False)    # spider patch plates, both faces
        k.pop()
    if not door:
        for z in (0.25, 3.15, 4.3, 7.3):
            k.bx(-0.012, 0.012, -0.012, 0.012, z + 0.01, z + 0.07, 'steelD', ink=False)


# ------------------------------------------------------------------ balustrades
def rail_fittings(k, y0, y1):
    """glass clamps both sides at two heights, and a handrail collar"""
    n = 2 if (y1 - y0) < 0.6 else 3
    for i in range(n):
        y = _lerp(y0, y1, (i + 0.5) / n)
        for zc in (0.3, 0.72):
            if abs(y - (y0 + y1) / 2) < 0.1 and zc < 0.8 and i == n // 2 and n == 3:
                continue      # keep the glint streaks clear
            for s in (-1, 1):
                a, b = sorted((s * 0.009, s * 0.03))
                k.bx(a, b, y - 0.03, y + 0.03, zc, zc + 0.06, 'steel', ink=False)
        k.bx(-0.02, 0.02, y - 0.03, y + 0.03, 0.976, 0.983, 'steelD', ink=False)


def post_fittings(k):
    """base flange with a collar, a head collar under the oak cap"""
    k.bx(-0.062, 0.062, -0.062, 0.062, 0.004, 0.02, 'steelD', ink=False)
    k.bx(-0.056, 0.056, -0.056, 0.056, 0.02, 0.07, 'steel', ink=False)
    k.bx(-0.056, 0.056, -0.056, 0.056, 0.93, 0.97, 'steel', ink=False)


def column_fittings(k, h):
    """steel cap on the black plinth, a bumper band, a head shadow ring"""
    k.cyl(0, 0, 0.097, 0.318, 0.318, 0.017, 'steel', seg=12, ink=False)
    k.cyl(0, 0, 0.9, 0.306, 0.306, 0.06, 'steel', seg=12, ink=False, caps=False)
    k.cyl(0, 0, h - 0.1, 0.309, 0.309, 0.097, 'graphite2', seg=12, ink=False, caps=False)


def stair_fittings(k, STEPS, Y0S, Y1S, RUN, RISE, DECK):
    """grip insets and board joints on every tread, glass clamps on the balustrades"""
    for i in range(STEPS - 1):
        a, top = Y0S + i * RUN, (i + 1) * RISE
        k.bx(-1.2, 1.2, a - 0.008, a + 0.034, top - 0.003, top + 0.004, 'graphite2', ink=False)
        k.bx(-1.285, 1.285, a + RUN * 0.5 - 0.004, a + RUN * 0.5 + 0.004, top - 0.003, top + 0.004, 'oakD', ink=False)
    for sx in (-1, 1):
        gx = sx * 1.375
        for t in (0.08, 0.45, 0.8):
            y = Y0S + (Y1S - Y0S) * t
            zb = _lerp(0.3, DECK + 0.05, (y - (Y0S - 0.2)) / (Y1S - (Y0S - 0.2)))
            for s in (-1, 1):
                a, b = sorted((gx + s * 0.009, gx + s * 0.032))
                k.bx(a, b, y - 0.035, y + 0.035, zb + 0.09, zb + 0.16, 'steel', ink=False)


def bleacher_clamps(k, STEPS, Y0S, Y1S, DECK):
    """glass clamps along both balustrades of the bleacher"""
    for sx in (-1, 1):
        gx = sx * 4.89
        ys = [-4.5, 4.4] + [Y0S + (Y1S - Y0S) * t for t in (0.12, 0.45, 0.85)]
        for y in ys:
            if y < Y0S - 0.1:
                zb = 0.25
            elif y > Y1S:
                zb = DECK + 0.08
            else:
                zb = _lerp(0.25, DECK + 0.08, (y - (Y0S - 0.1)) / (Y1S - (Y0S - 0.1)))
            for s in (-1, 1):
                a, b = sorted((gx + s * 0.009, gx + s * 0.032))
                k.bx(a, b, y - 0.04, y + 0.04, zb + 0.15, zb + 0.22, 'steel', ink=False)


def tier_nosing(k, SX0, SX1, a, depth, top):
    """anti-slip nosing on the tier edge and two board joints along it"""
    k.bx(SX0 + 0.05, SX1 - 0.05, a + 0.012, a + 0.05, top - 0.003, top + 0.004, 'graphite2', ink=False)
    for f in (0.4, 0.7):
        y = a + depth * f
        k.bx(SX0 + 0.05, SX1 - 0.05, y - 0.004, y + 0.004, top - 0.003, top + 0.004, 'oakD', ink=False)


def cushion_piping(k, x0, x1, ya, top):
    k.bx(x0 + 0.02, x1 - 0.02, ya - 0.003, ya + 0.003, top + 0.06, top + 0.08, 'wallW', ink=False)


# ------------------------------------------------------------------ lobby trail walls (corridor toward +X)
def trail_fittings(k, kind, DECK):
    # glass clamps on the gallery rail (both faces) and a nosing on the ledge
    for y in (-0.25, 0.25):
        for zc in (DECK + 0.25, DECK + 0.7):
            k.bx(0.885, 0.903, y - 0.04, y + 0.04, zc, zc + 0.06, 'steel', ink=False)
            k.bx(0.927, 0.945, y - 0.04, y + 0.04, zc, zc + 0.06, 'steel', ink=False)
    k.bx(0.947, 0.962, -0.495, 0.495, DECK - 0.12, DECK - 0.01, 'steelD', ink=False)
    if kind in ('', 'End'):
        k.bx(0.247, 0.285, -0.495, 0.495, 0.097, 0.112, 'steel', ink=False)           # skirting cap
    if kind == 'Lift':
        for y0, y1 in ((-0.4, -0.012), (0.012, 0.4)):
            k.bx(0.327, 0.338, y0, y1, 0.105, 0.3, 'steelD', ink=False)                # kick plates
        k.bx(0.297, 0.335, -0.43, 0.43, 2.503, 2.56, 'steelD', ink=False)              # door head
        k.bx(0.297, 0.346, -0.325, 0.325, 2.857, 2.89, 'steel', ink=False)             # indicator bezel
        k.bx(0.297, 0.346, -0.325, 0.325, 2.59, 2.623, 'steel', ink=False)
        for y0, y1 in ((-0.322, -0.3), (0.3, 0.322)):
            k.bx(0.293, 0.343, y0, y1, 2.62, 2.86, 'steel', ink=False)
        k.bx(0.297, 0.31, 0.38, 0.495, 0.97, 1.33, 'steel', ink=False)                 # call-button plate
        for z, c in ((1.05, 'black'), (1.19, 'black')):
            k.bx(0.307, 0.32, 0.395, 0.425, z, z + 0.04, c, ink=False)
    elif kind == 'Plant':
        k.bx(0.447, 0.462, -0.495, 0.495, 0.3, 0.347, 'steel', ink=False)             # trough rim
    elif kind == 'Stair':
        for y0, y1 in ((-0.4, -0.012), (0.012, 0.4)):
            k.bx(0.327, 0.338, y0, y1, 0.105, 0.33, 'steelD', ink=False)               # kick plates
        for z in (0.35, 1.1, 1.85):
            k.bx(0.318, 0.338, -0.428, -0.4, z - 0.06, z + 0.06, 'steelD', ink=False)  # hinges
        k.bx(0.287, 0.298, -0.47, 0.47, 6.897, 6.93, 'steel', ink=False)               # directory frame
        k.bx(0.287, 0.298, -0.47, 0.47, 5.17, 5.203, 'steel', ink=False)
        for y0, y1 in ((-0.467, -0.447), (0.447, 0.467)):
            k.bx(0.284, 0.295, y0, y1, 5.203, 6.897, 'steel', ink=False)


def gate_frame_fittings(k):
    """steel edge guards on the inner post corners, trim lines under and over the lintel"""
    for s in (-1, 1):
        for f in (-1, 1):
            xa, xb = sorted((s * 1.505, s * 1.565))
            ya, yb = sorted((f * 0.597, f * 0.608))
            k.bx(xa, xb, ya, yb, 0.115, 1.4, 'steel', ink=False)
    for f in (-1, 1):
        ya, yb = sorted((f * 0.6, f * 0.612))
        k.bx(-2.095, 2.095, ya, yb, 3.404, 3.44, 'steel', ink=False)
        k.bx(-2.095, 2.095, ya, yb, 3.86, 3.896, 'steelD', ink=False)


def gate_side_fittings(k):
    k.bx(-0.49, 0.49, -0.572, -0.497, 3.597, 3.62, 'steel', ink=False)                  # cap on the oak lining


def inner_wall_fittings(k, kind, H):
    if kind in ('BoardA', 'BoardB', 'Graphic'):
        k.bx(-0.495, 0.495, -0.516, -0.497, 0.098, 0.112, 'steel', ink=False)          # skirting cap
    if kind == 'Oak':
        k.bx(-0.495, 0.495, -0.612, -0.527, H - 0.303, H - 0.28, 'steel', ink=False)   # head rail on the battens
    elif kind == 'Plant':
        k.bx(-0.495, 0.495, -0.652, -0.627, 0.34, 0.397, 'steel', ink=False)           # trough lip
    elif kind in ('BoardA', 'BoardB'):
        k.bx(-0.495, 0.495, -0.545, -0.527, 2.322, 2.345, 'steel', ink=False)           # board frame lip
        k.bx(-0.495, 0.495, -0.558, -0.497, 3.497, 3.512, 'steel', ink=False)          # felt band cap


# ------------------------------------------------------------------ glass pods and rooms
def glass_run_fittings(k, ax, fixed, a0, a1, h):
    """vertical silicone joints between glass panels, with patch plates on both faces; the joints dodge the glints"""
    L = a1 - a0
    n = max(1, int(math.ceil(L / 1.25)))
    mid = (a0 + a1) / 2
    for i in range(1, n):
        p = a0 + L * i / n
        if mid - 0.22 < p < mid + 0.5:
            p = mid - 0.3
        if ax == 'x':
            k.bx(p - 0.008, p + 0.008, fixed - 0.016, fixed + 0.016, 0.067, h - 0.077, 'steelD', ink=False)
            for s in (-1, 1):
                a, b = sorted((fixed + s * 0.013, fixed + s * 0.03))
                k.bx(p - 0.04, p + 0.04, a, b, 0.2, 0.28, 'steel', ink=False)
        else:
            k.bx(fixed - 0.016, fixed + 0.016, p - 0.008, p + 0.008, 0.067, h - 0.077, 'steelD', ink=False)
            for s in (-1, 1):
                a, b = sorted((fixed + s * 0.013, fixed + s * 0.03))
                k.bx(a, b, p - 0.04, p + 0.04, 0.2, 0.28, 'steel', ink=False)


def pod_fascia(k, G, Hp):
    for deg in (0, 90, 180, 270):
        k.push(0, 0, deg)
        cap_trim(k, -G - 0.1, G + 0.1, -G - 0.1, Hp + 0.18, 'steel', h=0.03, d=0.012)
        base_trim(k, -G - 0.1, G + 0.1, -G - 0.1, 'steelD', h=0.025, d=0.012, z0=Hp)
        k.pop()


# ------------------------------------------------------------------ desks
def desk_fittings(k, x0, x1, y0, y1, h):
    """edge banding, under-desk cable tray, a cable grommet, leg collars and glides"""
    k.bx(x0 + 0.005, x1 - 0.005, y0 - 0.008, y0 + 0.003, h - 0.027, h - 0.003, 'oak2', ink=False)
    k.bx(x0 + 0.005, x1 - 0.005, y1 - 0.003, y1 + 0.008, h - 0.027, h - 0.003, 'oak2', ink=False)
    k.bx(x0 - 0.008, x0 + 0.003, y0 + 0.005, y1 - 0.005, h - 0.024, h - 0.006, 'oak2', ink=False)
    k.bx(x1 - 0.003, x1 + 0.008, y0 + 0.005, y1 - 0.005, h - 0.024, h - 0.006, 'oak2', ink=False)
    near_div = y1 if abs(y1) < abs(y0) else y0
    sgn = -1 if near_div == y1 else 1            # the direction from the divider toward the player
    yc = near_div + sgn * 0.12
    ya, yb = sorted((yc - 0.04, yc + 0.04))
    k.bx(x0 + 0.3, x1 - 0.3, ya, yb, h - 0.075, h - 0.027, 'graphite', ink=False)       # cable tray
    gy = near_div + sgn * 0.16
    k.bx(x0 + 0.12, x0 + 0.18, gy - 0.03, gy + 0.03, h - 0.004, h + 0.004, 'black', ink=False)   # grommet
    ym = (y0 + y1) / 2
    for x in (x0 + 0.15, x1 - 0.15):
        k.bx(x - 0.047, x + 0.047, ym - 0.057, ym + 0.057, 0.004, 0.06, 'steelD', ink=False)
        for e in (y0 + 0.06, y1 - 0.06):
            a, b = sorted((e - 0.003 * (1 if e < ym else -1), e + 0.034 * (-1 if e > ym else 1)))
            k.bx(x - 0.033, x + 0.033, a, b, 0.004, 0.026, 'black', ink=False)


def arm_clamp(k):
    """desk clamp of a monitor arm (frame: the monitor's, z = desk top)"""
    k.bx(-0.045, 0.045, 0.08, 0.16, -0.003, 0.012, 'steelD', ink=False)
    k.bx(-0.02, 0.02, 0.103, 0.137, -0.047, -0.006, 'steelD', ink=False)
    k.bx(-0.045, 0.045, 0.08, 0.16, -0.05, -0.027, 'steelD', ink=False)


def divider_fittings(k):
    """cap and foot trims on the dev-desk divider, felt panel seams on both faces"""
    k.bx(-1.945, 1.945, -0.025, 0.025, 1.247, 1.26, 'steel', ink=False)
    k.bx(-1.945, 1.945, -0.027, 0.027, 0.004, 0.06, 'graphite', ink=False)
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.032, s * 0.044))
        for i in range(1, 4):
            x = -1.94 + 3.88 * i / 4
            k.bx(x - 0.007, x + 0.007, y0, y1, 0.906, 1.236, 'graphite2', ink=False)


# ------------------------------------------------------------------ landmarks
def logo_wall_fittings(k, Hw):
    base_trim(k, -7.0, 7.0, -0.35, 'steel', h=0.04, d=0.012, z0=0.2)
    for deg in (0, 180):
        k.push(0, 0, deg)
        cap_trim(k, -6.9, 6.9, -0.38, Hw + 0.12, 'steel', h=0.03, d=0.012)
        k.pop()
    # frame round the lettering plate (front)
    k.bx(-5.65, 5.65, -0.5, -0.417, 4.9, 4.96, 'graphite', ink=False)
    k.bx(-5.65, 5.65, -0.5, -0.417, 1.94, 2.0, 'graphite', ink=False)
    for xa, xb in ((-5.644, -5.6), (5.6, 5.644)):
        k.bx(xa, xb, -0.494, -0.42, 1.997, 4.903, 'graphite', ink=False)
    bolt_row(k, -5.5, 5.5, 2.1, -0.48, 12, 'steel', s=0.03)
    bolt_row(k, -5.5, 5.5, 4.8, -0.48, 12, 'steel', s=0.03)
    # frame round the LED wall (back)
    k.bx(-6.28, 6.28, 0.297, 0.375, 5.797, 5.86, 'graphite', ink=False)
    k.bx(-6.28, 6.28, 0.297, 0.375, 1.14, 1.203, 'graphite', ink=False)
    for xa, xb in ((-6.274, -6.2), (6.2, 6.274)):
        k.bx(xa, xb, 0.294, 0.371, 1.2, 5.8, 'graphite', ink=False)


def reception_fittings(k):
    k.bx(-2.15, 2.195, -0.612, -0.597, 1.04, 1.07, 'steelD', ink=False)               # reveal under the top
    for x in (-0.2, 0.2):                                                              # staff grommets
        k.bx(x - 0.03, x + 0.03, 0.27, 0.33, 0.747, 0.757, 'black', ink=False)
    k.bx(-1.995, 2.195, 0.697, 0.708, 0.726, 0.744, 'oak', ink=False)                 # edge banding, staff desk
    for x in (-1.85, 2.05):
        k.bx(x - 0.06, x + 0.06, 0.23, 0.67, 0.004, 0.035, 'graphite', ink=False)     # leg feet


# ------------------------------------------------------------------ planters
def planter_fittings(k, v):
    if v == 'A':
        k.cyl(0, 0, 0.655, 0.311, 0.311, 0.035, 'graphite2', seg=12, ink=False, caps=False)    # rim band
        k.cyl(0, 0, 0.004, 0.3415, 0.3415, 0.04, 'graphite', seg=12, ink=False)                  # foot ring
    else:
        k.bx(-0.385, 0.385, -0.385, 0.385, 0.004, 0.05, 'graphite', ink=False)                  # plinth
        k.bx(-0.385, 0.385, -0.385, 0.385, 0.54, 0.597, 'graphite2', ink=False)                 # rim band


def planter_tree_fittings(k):
    for deg in (0, 90, 180, 270):
        k.push(0, 0, deg)
        base_trim(k, -0.9, 0.9, -0.9, 'graphite', h=0.05, d=0.012)
        k.pop()
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * 0.885, sx * 0.915))
            ya, yb = sorted((sy * 0.885, sy * 0.915))
            k.bx(xa, xb, ya, yb, 0.06, 0.52, 'steel', ink=False)
