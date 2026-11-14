"""kit-coalmine modelled detail (tactical look plan Stage 11): real-mine fixings on the pieces the player sees most.
Built on the kit_base detail helpers; every part is ink=False, at least 3 mm proud, embedded 3 mm, and horizontal
runs stop 5 mm short of the piece sides. Faces looking toward Blender -Y are drawn at y = yf in the current frame
(k.push(0, 0, 180) for the +Y face, 90 / 270 for +X / -X, as in mt_detail.py)."""
from kit_base import PROUD, EMBED, bolt_row, rivet_strip, junction_box, sign_plate, window_frame_depth

STEEL, STEEL_D, BOLT = 'steel2', 'steelDark', 'steel'


def face_plate(k, x0, x1, z0, z1, yf, c=STEEL_D, bc=BOLT, d=0.008, nx=2, m=0.03, s=0.022):
    """A bolted plate on a -Y face: 8 mm proud, a bolt row along its top and bottom edge."""
    k.bx(x0, x1, yf - d, yf + EMBED, z0, z1, c, ink=False)
    if bc:
        for z in (z0 + m, z1 - m):
            bolt_row(k, x0 + 0.01, x1 - 0.01, z, yf - d, nx, bc, s=s)


def collar(k, x0, x1, y0, y1, z0, z1, c=STEEL_D):
    """A strap wrapped round a post, 3 mm proud on every side."""
    k.bx(x0 - 0.003, x1 + 0.003, y0 - 0.003, y1 + 0.003, z0, z1, c, ink=False)


def sign_frame(k, xh, z0, z1, yf, c=STEEL_D, bc=BOLT, w=0.028, d=0.012):
    """Angle frame wrapped round a board (half width xh, z0..z1) whose face is at yf, with corner bolts."""
    k.bx(-xh - 0.003, -xh + w, yf - d, yf + EMBED, z0 - 0.003, z1 + 0.003, c, ink=False)
    k.bx(xh - w, xh + 0.003, yf - d, yf + EMBED, z0 - 0.003, z1 + 0.003, c, ink=False)
    k.bx(-xh + w, xh - w, yf - d - 0.001, yf + EMBED, z0 - 0.003, z0 + w, c, ink=False)
    k.bx(-xh + w, xh - w, yf - d - 0.001, yf + EMBED, z1 - w, z1 + 0.003, c, ink=False)
    for sx in (-1, 1):
        for z in (z0 + w * 0.5, z1 - w * 0.5):
            x = sx * (xh - w * 0.5 + 0.0015)
            k.bx(x - 0.009, x + 0.009, yf - d - 0.008, yf - d + EMBED, z - 0.009, z + 0.009, bc, ink=False)


# ------------------------------------------------------------------ cables and lamps
def cable_hook(k, z, y):
    """Clamp round the sagging power cable and a rock-bolt plate on the end of its hook arm."""
    k.bx(-0.026, 0.026, y - 0.026, y + 0.04, z - 0.125, z - 0.062, STEEL_D, ink=False)
    k.bx(-0.05, 0.05, y + 0.215, y + 0.235, z - 0.16, z - 0.03, STEEL, ink=False)


def lamp_bracket(k):
    """Rock_Lamp*: strap collar, bolted end plate and a clipped lamp cable along the timber bracket (bracket
    x +-0.07, y -0.95..-0.2, z 3.25..3.39; the lantern stays where it is)."""
    collar(k, -0.07, 0.07, -0.62, -0.56, 3.247, 3.393)
    face_plate(k, -0.06, 0.06, 3.27, 3.37, -0.95, nx=2, m=0.025, s=0.02)
    k.bx(-0.014, 0.014, -0.9, -0.3, 3.387, 3.414, 'cable', ink=False)
    for y in (-0.46, -0.76):
        k.bx(-0.03, 0.03, y - 0.02, y + 0.02, 3.38, 3.425, STEEL_D, ink=False)


def prop_detail(k):
    """Rock_Prop: strap collars with bolts, a bolted head plate, wedges under the cap, a foot anchor, chalk tally."""
    for z in (0.9, 2.3):
        collar(k, -0.13, 0.13, -0.8, -0.54, z, z + 0.07)
        bolt_row(k, -0.09, 0.09, z + 0.035, -0.803, 2, BOLT, s=0.022)
    face_plate(k, -0.16, 0.16, 4.03, 4.25, -0.86, nx=3, m=0.03)
    for s in (-1, 1):
        k.bxr(s * 0.17, -0.67, 3.945, 0.07, 0.2, 0.1, 'timberEnd', rot=(0, -s * 30, 0), ink=False)
    bolt_row(k, -0.14, 0.14, 0.06, -0.84, 2, BOLT, s=0.03)
    for i in range(4):
        x = -0.09 + i * 0.045
        k.qy(x - 0.006, x + 0.006, 3.1, 3.35, -0.805, -1, 'chalk')


def sign_detail(k):
    """Rock_Sign: angle frame with corner bolts and washers on the pins (board x +-0.42, z 2.0..2.8, face y -0.62)."""
    sign_frame(k, 0.42, 2.0, 2.8, -0.62)
    for x in (-0.36, 0.36):
        k.bx(x - 0.03, x + 0.03, -0.665, -0.655, 2.63, 2.71, STEEL, ink=False)


# ------------------------------------------------------------------ timber sets, posts, crib
def set_detail(k, x_half, cap_z, lamp, post=0.15, y_half=0.17):
    """Drift timber set: flitch plates on the cap over the posts, post collars with bolts, stone footings, a
    junction box with a clipped conduit on one post, a hazard sign on the other, a lamp arm on the lamp sets."""
    for s in (-1, 1):
        x0, x1 = sorted((s * (x_half - post), s * (x_half + post)))
        collar(k, x0, x1, -post + 0.01, post - 0.01, 1.1, 1.17)
        k.bx(x0 - 0.03, x1 + 0.03, -y_half, y_half, 0.0, 0.1, 'rock2', ink=False)
    for deg in (0, 180):
        k.push(0, 0, deg)
        for s in (-1, 1):
            x0, x1 = sorted((s * (x_half - 0.25), s * (x_half + 0.25)))
            face_plate(k, x0, x1, cap_z + 0.04, cap_z + 0.3, -y_half, nx=3, m=0.03)
            a, b = sorted((s * (x_half - post), s * (x_half + post)))
            bolt_row(k, a + 0.03, b - 0.03, 1.135, -post + 0.007, 3, BOLT, s=0.022)
        k.pop()
    xj = x_half
    junction_box(k, xj, 1.9, -post + 0.01, STEEL_D, STEEL, w=0.2, h=0.24, d=0.07)
    k.bx(xj - 0.013, xj + 0.013, -post + 0.01 - 0.03, -post + 0.01, 2.02 + 0.0, cap_z - 0.04, STEEL, ink=False)
    for z in (2.35, 2.95, 3.55):
        k.bx(xj - 0.03, xj + 0.03, -post + 0.01 - 0.04, -post + 0.01 + EMBED, z, z + 0.03, STEEL_D, ink=False)
    sign_plate(k, -x_half, 1.7, -post + 0.01, 0.2, 0.26, 'hazard', 'ink', bar=0.35)
    if lamp:   # the lantern hangs at x -1.2, y -0.25: give it an arm and a bolted flange on the cap
        k.bx(-1.225, -1.175, -0.27, -0.16, cap_z - 0.02, cap_z + 0.005, STEEL_D, ink=False)
        face_plate(k, -1.26, -1.14, cap_z - 0.015, cap_z + 0.25, -y_half, nx=2, m=0.03)


def trail_post(k, y_mid, roof):
    """TrailWall timber set: collars with bolts on the post, a bolted plate on the cap end."""
    for z in (0.9, 2.2):
        collar(k, -0.1, 0.1, -0.42, -0.24, z, z + 0.07)
        bolt_row(k, -0.07, 0.07, z + 0.035, -0.423, 2, BOLT, s=0.022)
    face_plate(k, -0.09, 0.09, roof - 0.29, roof - 0.09, y_mid, nx=2, m=0.03)
    k.bx(-0.13, 0.13, -0.48, -0.36, 0.0, 0.05, 'rock2', ink=False)


def crib_detail(k, ceil):
    """Crib post collars and bolted header plates."""
    collar(k, -0.28, 0.28, -0.28, 0.28, 5.0, 5.07)
    collar(k, -0.28, 0.28, -0.28, 0.28, ceil - 1.1, ceil - 1.03)
    for a in (0, 90, 180, 270):
        k.push(0, 0, a)
        bolt_row(k, -0.2, 0.2, 5.035, -0.283, 3, BOLT, s=0.022)
        bolt_row(k, -0.2, 0.2, ceil - 1.065, -0.283, 3, BOLT, s=0.022)
        k.pop()
    for a in (0, 180):
        k.push(0, 0, a)
        for xa, xb in ((-0.82, -0.46), (0.46, 0.82)):
            face_plate(k, xa, xb, ceil - 0.36, ceil - 0.06, -0.33, nx=2, m=0.03)
        k.pop()


def roof_jack_detail(k, ceil):
    """Roof jack: anchor bolts on the base plate, locking lugs on the collar, hose fittings, a gauge, a bolted
    cleat plate on the timber header."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(sx * 0.22 - 0.025, sx * 0.22 + 0.025, sy * 0.22 - 0.025, sy * 0.22 + 0.025, 0.12 - EMBED, 0.145, STEEL, ink=False)
    for a in (0, 90, 180, 270):
        k.push(0, 0, a)
        k.bx(-0.03, 0.03, -0.215, -0.19, 2.995, 3.085, STEEL_D, ink=False)   # lugs round the collar
        k.pop()
    for z in (0.95, 2.6):
        k.bx(-0.045, 0.045, -0.255, -0.16, z, z + 0.07, STEEL_D, ink=False)    # hose fittings
    k.cyl(0.0, 0.15, 1.5, 0.045, 0.045, 0.05, STEEL_D, seg=8, ink=False, rot=(-90, 0, 0))
    k.cyl(0.0, 0.199, 1.5, 0.035, 0.035, 0.009, 'chalk', seg=8, ink=False, rot=(-90, 0, 0))
    for a in (0, 180):
        k.push(0, 0, a)
        face_plate(k, -0.3, 0.3, ceil - 0.31, ceil + 0.05, -0.2, nx=3, m=0.03)
        k.pop()


# ------------------------------------------------------------------ posts, portal, hatch, shack
def gate_detail(k):
    """GateFrame: bolts on the post bands, flitch plates on the cap, sign frames, steel shoes."""
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.5, s * 2.05))
        k.bx(x0 - 0.03, x1 + 0.03, -0.64, 0.64, 0.0, 0.08, STEEL_D, ink=False)
    for f in (-1, 1):
        k.push(0, 0, 180 if f > 0 else 0)
        for s in (-1, 1):
            x0, x1 = sorted((s * 1.5, s * 2.05))
            for z in (0.33, 2.63):
                bolt_row(k, x0 + 0.07, x1 - 0.07, z, -0.63, 3, BOLT, s=0.024)
            face_plate(k, x0, x1, 3.36, 3.79, -0.62, nx=3, m=0.04, s=0.026)
        sign_frame(k, 0.8, 4.3, 4.95, -0.66)
        k.pop()


def lamp_post_detail(k):
    """LanternPost: strap collars with bolts, a junction box and a clipped cable up the post and under the arm."""
    for z in (0.7, 1.5):
        collar(k, -0.09, 0.09, -0.09, 0.09, z, z + 0.06)
        bolt_row(k, -0.05, 0.05, z + 0.03, -0.093, 2, BOLT, s=0.02)
    face_plate(k, -0.06, 0.06, 2.77, 2.88, -0.7, nx=2, m=0.02, s=0.02)
    k.push(0, 0, 180)
    junction_box(k, 0.0, 0.62, -0.09, STEEL_D, STEEL, w=0.14, h=0.2, d=0.06)
    k.pop()
    k.bx(-0.012, 0.012, 0.087, 0.108, 0.75, 2.752, 'cable', ink=False)
    k.bx(-0.008, 0.008, -0.6, 0.098, 2.727, 2.746, 'cable', ink=False)
    for z in (1.1, 1.7, 2.3):
        k.bx(-0.03, 0.03, 0.082, 0.112, z, z + 0.03, STEEL_D, ink=False)
    k.bx(-0.03, 0.03, -0.41, -0.37, 2.72, 2.755, STEEL_D, ink=False)


def work_light_detail(k):
    """WorkLight: guard bars over the lamp, a collar where the legs meet, foot pads."""
    import math
    for a in (0, 120, 240):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.bx(ca * 0.42 - 0.06, ca * 0.42 + 0.06, sa * 0.42 - 0.06, sa * 0.42 + 0.06, 0.004, 0.02, STEEL_D, ink=False)
    k.bx(-0.07, 0.07, -0.07, 0.07, 1.62, 1.76, 'mach2', ink=False)
    k.push(0, 0, 0, 2.2)
    n = (0.0, 0.9063, -0.4226)       # the slab's normal after its -25 degree turn
    u = (0.0, 0.4226, 0.9063)        # and its up axis
    c = (0.0, -0.17 - 0.008 * n[1], -0.005 - 0.008 * n[2])
    for x in (-0.12, -0.04, 0.04, 0.12):
        k.bxr(x, c[1], c[2], 0.012, 0.012, 0.22, STEEL_D, rot=(-25, 0, 0), ink=False)
    ch = (0.0, -0.17 - 0.0125 * n[1], -0.005 - 0.0125 * n[2])
    for t in (-0.08, 0.0, 0.08):
        k.bxr(0.0, ch[1] + t * u[1], ch[2] + t * u[2], 0.32, 0.014, 0.014, STEEL_D, rot=(-25, 0, 0), ink=False)
    k.pop()


def hatch_detail(k):
    """Lift cage: rivets along the floor and roof edge, a capacity plate."""
    rivet_strip(k, -0.7, 0.7, 0.09, -0.62, BOLT, every=0.2, s=0.02)
    sign_plate(k, 0.0, 2.675, -0.68, 0.3, 0.09, 'chalk', 'ink', bar=0.3)


def shack_detail(k, y0):
    """Shack: strap hinges with bolts on the door, a timber surround on the lit window."""
    yf = y0 - 0.06
    for z in (0.3, 1.7):
        k.bx(-1.445, -1.05, yf - 0.01, yf + EMBED, z, z + 0.07, STEEL_D, ink=False)
        bolt_row(k, -1.4, -1.1, z + 0.035, yf - 0.01, 3, BOLT, s=0.026)
    window_frame_depth(k, 0.28, 1.42, 1.08, 1.82, yf, 'timber', depth=0.03, t=0.05)


# ------------------------------------------------------------------ conveyor and cart
def conveyor_detail(k):
    """Belt conveyor: carrying and return idler rollers with brackets, bolts and splice plates on the stringers,
    base plates with anchor bolts under the legs."""
    k.cyl(0.0, -0.40, 0.89, 0.04, 0.04, 0.80, STEEL_D, seg=8, ink=False, rot=(-90, 0, 0))
    k.cyl(0.0, -0.39, 0.40, 0.035, 0.035, 0.78, STEEL_D, seg=8, ink=False, rot=(-90, 0, 0))
    for s in (-1, 1):
        ys = sorted((s * 0.385, s * 0.425))
        k.bx(-0.03, 0.03, ys[0], ys[1], 0.84, 0.94, STEEL_D, ink=False)
        k.bx(-0.025, 0.025, ys[0], ys[1], 0.36, 0.83, STEEL_D, ink=False)
    for deg in (0, 180):
        k.push(0, 0, deg)
        for xa, xb in ((-0.495, -0.37), (0.37, 0.495)):
            face_plate(k, xa, xb, 0.85, 0.95, -0.47, c=STEEL, bc=BOLT, nx=2, m=0.025, s=0.02)
        bolt_row(k, -0.3, 0.3, 0.9, -0.47, 3, BOLT, s=0.022)
        k.pop()
    for x in (-0.3, 0.3):
        for s in (-1, 1):
            ya, yb = sorted((s * 0.35, s * 0.48))
            k.bx(x - 0.07, x + 0.07, ya, yb, 0.004, 0.016, STEEL_D, ink=False)
            yc = s * 0.415
            for sx in (-1, 1):
                k.bx(x + sx * 0.057 - 0.01, x + sx * 0.057 + 0.01, yc - 0.01, yc + 0.01, 0.013, 0.028, BOLT, ink=False)


def cart_detail(k):
    """Ore cart: rivets on the sill and rim, hub caps on the wheels."""
    for deg in (90, 270):
        k.push(0, 0, deg)
        rivet_strip(k, -0.66, 0.66, 0.35, -0.42, BOLT, every=0.24, s=0.018)
        rivet_strip(k, -0.8, 0.8, 1.235, -0.58, BOLT, every=0.24, s=0.018)
        k.pop()
    for deg in (0, 180):
        k.push(0, 0, deg)
        rivet_strip(k, -0.5, 0.5, 1.235, -0.86, BOLT, every=0.24, s=0.018)
        k.pop()
    for sy in (-1, 1):
        k.cyl(-0.315, sy * 0.48, 0.3, 0.06, 0.06, 0.02, STEEL_D, seg=6, ink=False, rot=(0, 90, 0))
        k.cyl(0.37, sy * 0.48, 0.3, 0.06, 0.06, 0.02, STEEL_D, seg=6, ink=False, rot=(0, 90, 0))


# ------------------------------------------------------------------ track
def track_detail(k, xs, y, gauge, sleeper_top, x0, x1):
    """Tie plates and two spikes per rail on each sleeper, fishplates on the rail webs at both ends."""
    for x in xs:
        for s in (-1, 1):
            yc = y + s * gauge / 2
            k.bx(x - 0.05, x + 0.05, yc - 0.05, yc + 0.05, sleeper_top - EMBED, sleeper_top + 0.005, STEEL_D, ink=False)
            for d in (-1, 1):
                ys = yc + d * 0.0245
                k.bx(x - 0.007, x + 0.007, ys - 0.007, ys + 0.007, sleeper_top + 0.003, sleeper_top + 0.026, BOLT, ink=False)
    for s in (-1, 1):
        yc = y + s * gauge / 2
        for xa, xb in ((x0 + 0.005, x0 + 0.14), (x1 - 0.14, x1 - 0.005)):
            for d in (-1, 1):
                ya, yb = sorted((yc + d * 0.017, yc + d * 0.026))
                k.bx(xa, xb, ya, yb, sleeper_top + 0.013, sleeper_top + 0.046, STEEL, ink=False)
